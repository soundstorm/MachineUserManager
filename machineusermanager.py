#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from pn532.api import PN532
import lcdlib
import time
import RPi.GPIO as GPIO
from math import ceil
from importlib import import_module
import callbacks
try:
	import user_callbacks as callbacks
except ImportError:
	logging.info('No user_callbacks available, using defaults')

from config import *
try:
	from user_config import *
except ImportError:
	logging.info('No user_config available, using defaults')

lang = import_module('languages.{}'.format(UI_LANGUAGE))
db_connector = import_module('dbconnectors.db_{}'.format(DB_TYPE))
db = db_connector.db_connector(
	host     = DB_HOST,
	user     = DB_USER,
	password = DB_PASSWORD,
	database = DB_DATABASE,
	machine  = MACHINE_NAME
)

nfc = PN532()
nfc.setup()

GPIO.setmode(GPIO.BCM)

lcd = lcdlib.lcd(LCD_ADDR, 4, 20)

do_cancel      = False
do_confirm     = False
job_is_running = False
machine_is_on  = False

# Interrupt functions
def INT_cancel(channel):
	global do_cancel
	do_cancel = True

def INT_confirm(channel):
	global do_confirm
	do_confirm = True

def INT_state(channel):
	global job_is_running
	job_is_running = GPIO.input(channel) != INVERT_STATE

def INT_on(channel):
	global machine_is_on
	machine_is_on = GPIO.input(channel) != INVERT_POWER


# SETUP GPIOS
logging.debug('Setting up GPIOs')
GPIO.setwarnings(False) # May yield warnings on restart otherwise
GPIO.setup(MACHINE_PROT, GPIO.OUT)
try:
	GPIO.setup(LED_R, GPIO.OUT)
except NameError:
	logging.info('No GPIO defined for LED_R')
try:
	GPIO.setup(LED_Y, GPIO.OUT)
except:
	logging.info('No GPIO defined for LED_Y')
try:
	GPIO.setup(LED_G, GPIO.OUT)
except NameError:
	logging.info('No GPIO defined for LED_G')
try:
	GPIO.setup(ALARM, GPIO.OUT)
except NameError:
	logging.info('No GPIO defined for ALARM')
try:
	GPIO.setup(MACHINE_STATE, GPIO.IN, GPIO.PUD_UP)
except NameError:
	logging.info('No GPIO defined for MACHINE_STATE')
try:
	GPIO.setup(MACHINE_ON, GPIO.IN, GPIO.PUD_UP)
except NameError:
	logging.info('No GPIO defined for MACHINE_ON')
GPIO.setup(BTN_CONFIRM, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(BTN_CANCEL, GPIO.IN, GPIO.PUD_UP)

logging.debug('Configuring interrupt routines')

GPIO.add_event_detect(
	BTN_CONFIRM,
	GPIO.FALLING if INVERT_BUTTONS else GPIO.RISING,
	callback=INT_confirm,
	bouncetime=300
)
GPIO.add_event_detect(
	BTN_CANCEL,
	GPIO.FALLING if INVERT_BUTTONS else GPIO.RISING,
	callback=INT_cancel,
	bouncetime=300
)

try:
	GPIO.add_event_detect(MACHINE_STATE, GPIO.BOTH, callback=INT_state, bouncetime=300)
except NameError:
	logging.info('No GPIO defined for MACHINE_STATE, not setting up interrupt')
try:
	GPIO.add_event_detect(MACHINE_ON, GPIO.BOTH, callback=INT_on, bouncetime=300)
except NameError:
	logging.info('No GPIO defined for MACHINE_ON, not setting up interrupt')

# Initial state
try:
	job_is_running = GPIO.input(MACHINE_STATE) != INVERT_STATE
except NameError:
	job_is_running = False # No pin for machine state defined, always assume no job is active
try:
	machine_is_on = GPIO.input(MACHINE_ON) != INVERT_POWER
except NameError:
	machine_is_on = True # No pin for machine power defined, always assume machine is on

uid = 0
credit = 0
time_remaining = 0
username = 'OVERRRIDE'
job_started = 0
last_state_change = 0
job_active = False
warning_sent = False
try:
	if OVERRIDE:
		logging.info('Override mode active')
except NameError:
	OVERRIDE = False

session_active = OVERRIDE
session_start = 0
session_valid_until = 0 # Time when session needs to be renewed/revaluated

def set_red_led(state):
	try:
		GPIO.output(LED_R, state != INVERT_LEDS)
	except NameError:
		logging.info('No pin defined for LED_R or INVERT_LEDs not set')
	except Exception as e:
		logging.exception('Error while setting pin LED_R')

def set_yellow_led(state):
	try:
		GPIO.output(LED_Y, state != INVERT_LEDS)
	except NameError:
		logging.info('No pin defined for LED_Y or INVERT_LEDs not set')
	except Exception as e:
		logging.exception('Error while setting pin LED_Y')

def set_green_led(state):
	try:
		GPIO.output(LED_G, state != INVERT_LEDS)
	except NameError:
		logging.info('No pin defined for LED_G or INVERT_LEDs not set')
	except Exception:
		logging.exception('Error while setting pin LED_G')

def set_alarm(state):
	try:
		GPIO.output(ALARM, state != INVERT_ALARM)
	except NameError:
		logging.info('No pin defined for ALARM or INVERT_ALARM not set')
	except Exception:
		logging.exception('Error while setting pin ALARM')

def set_protection(state):
	GPIO.output(MACHINE_PROT, state == INVERT_PROT)
	# Don't fetch error here to avoid failing silently

def prepare_reading_tag():
	nfc.in_list_passive_target() #prepare reading on modified pn532 lib

def read_tag():
	id_tuple = nfc.read()
	if id_tuple is not None:
		tag_uid = 0
		# Only bytes 5-9 are the really unique part
		# Generate int from tuple/list
		for i in id_tuple[5:9]:
			tag_uid <<= 8
			tag_uid += i
		return uid
	return None

def unlock_machine():
	global session_active, warning_sent
	session_active = True
	set_protection(0)
	set_red_led(0)
	set_green_led(1)
	warning_sent = False

def lock_machine():
	global session_active
	session_active = False
	set_protection(1)
	set_red_led(1)
	set_green_led(0)
	set_yellow_led(0)

def get_user_info():
	global username, credit
	try:
		username, credit = db.get_user_info(uid)
		return True
	except ValueError:
		logging.debug('No user found for uid %d', uid)

def check_card():
	global uid
	# First check if card is only alias
	alias_id = db.get_alias(uid)
	if alias_id is not None:
		logging.debug('Replacing aliased uid %d with main uid %d', uid, alias_id)
		uid = alias_id # Replace current card uid by main uid
	if not get_user_info():
		return -1
	return db.is_authorized(uid)

def can_afford():
	return credit > PRICE_ONCE + PRICE_MINUTE

def login():
	global session_start, session_valid_until
	if db.change_card_value(uid, -PRICE_ONCE - PRICE_MINUTE):
		# Update successful so the user had enough credit to login and book at least one minute
		session_start = int(time.time())
		db.create_session(uid, session_start, -PRICE_ONCE - PRICE_MINUTE)
		session_valid_until = time.time() + 60
		return True
	return False

def logout():
	db.end_session(uid, session_start, int(time.time()))
	lock_machine()

def revalidate():
	global uid, session_start
	if db.change_card_value(uid, -PRICE_MINUTE):
		# Update successful so the user had enough credit to extend session
		db.update_session(uid, session_start, -PRICE_MINUTE)
		return True
	return False

def countdown(t):
	for i in range(t):
		lcd.display_string(str(5 - i), 3, 19)
		time.sleep(1)

def calculate_time_remaining():
	global time_remaining, credit, session_active
	if get_user_info():
		if PRICE_MINUTE == 0:
			time_remaining = 999
		else:
			time_remaining = ceil((credit - (1 - session_active) * PRICE_ONCE) / PRICE_MINUTE)
	else:
		time_remaining = 0
	return time_remaining

def display_text(arr):
	i = 0
	padding = '                    '
	for line in arr:
		lcd.display_string((line.format(
			NAME             = username,
			CARD_HEX         = "{:08x}".format(uid).upper(),
			CARD_DEC         = uid,
			CREDIT_REMAINING = credit,
			TIME_REMAINING   = time_remaining,
			PRICE_ONCE       = PRICE_ONCE if (int(PRICE_ONCE) != PRICE_ONCE) else int(PRICE_ONCE),
			PRICE_MINUTE     = PRICE_MINUTE if (int(PRICE_MINUTE) != PRICE_MINUTE) else int(PRICE_MINUTE)
		) + padding)[:20], i, 0)
		i += 1
		if i == 4: # Limit to display lines
			break
	for n in range(i, 4):
		lcd.display_string(padding, n, 0) # Clear not defined lines

while True:
	lock_machine()
	set_alarm(0)
	if not machine_is_on:
		lcd.backlight_off()
		lcd.clear()
		display_text(lang.MACHINE_OFF)
		while not machine_is_on:
			time.sleep(.5)
		logging.info('Machine switched on')
		try:
			callbacks.machine_turn_on()
		except NameError:
			logging.debug('No callback defined for event machine_turn_on')
		except TypeError:
			logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
	while machine_is_on and not session_active and not OVERRIDE:
		display_text(lang.MACHINE_READY)
		lcd.backlight_on()
		prepare_reading_tag()
		read_uid = None
		while machine_is_on and read_uid == 0:
			read_uid = read_tag()
		if read_uid is None:
			break
		try:
			callbacks.card_scan(uid)
		except NameError:
			logging.debug('No callback defined for event card_scan')
		except TypeError:
			logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
		r = check_card()
		if r < 0:
			logging.info('Card %d is unknown', uid)
			try:
				callbacks.card_unknown(uid)
			except NameError:
				logging.debug('No callback defined for event card_unknown')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
			display_text(lang.CARD_UNKNOWN)
			countdown(TIMEOUT_SEC)
		elif r == 0:
			logging.info('Card %d is unauthorized to use this machine', uid)
			try:
				callbacks.card_unauthorized(uid, username)
			except NameError:
				logging.debug('No callback defined for event card_unauthorized')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
			display_text(lang.CARD_UNAUTHORIZED)
			countdown(TIMEOUT_SEC)
		else:
			try:
				callbacks.card_authorized(uid, username)
			except NameError:
				logging.debug('No callback defined for event card_authorized')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
			calculate_time_remaining()
			if can_afford():
				display_text(lang.LOGIN)
				# Reset button states
				do_cancel = False
				do_confirm = False
				while machine_is_on:
					if do_cancel:
						logging.debug('Login was cancelled')
						break
					elif do_confirm:
						if login():
							try:
								callbacks.user_login(uid, username)
							except NameError:
								logging.debug('No callback defined for event user_login')
							except TypeError:
								logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
							if job_is_running:
								if job_started == 0:
									job_started = time.time()
								if job_active: # still set from last session
									try:
										callbacks.job_resume(uid, username)
									except NameError:
										logging.debug('No callback defined for event job_resume')
									except TypeError:
										logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
							else:
								job_active = False
							logging.info('Machine is unlocked by %d', uid)
							unlock_machine()
							last_state_change = time.time()
							break
						else:
							try:
								callbacks.user_login_failed(uid, username)
							except NameError:
								logging.debug('No callback defined for event user_login_failed')
							except TypeError:
								logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
							break
							display_text(lang.LOGIN_FAILED)
							countdown(TIMEOUT_SEC)
					time.sleep(.3)
			else:
				logging.info('Credit of %d is too low to use machine', uid)
				try:
					callbacks.credit_too_low(uid, username)
				except NameError:
					logging.debug('No callback defined for event credit_too_low')
				except TypeError:
					logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
				display_text(lang.CREDIT_TOO_LOW)
				countdown(TIMEOUT_SEC)

	# Reset button state to not logout user immediately again after potentially successful login
	do_cancel = False
	if OVERRIDE and machine_is_on:
		unlock_machine()
	while (session_active or OVERRIDE) and machine_is_on:
		calculate_time_remaining() # update variables
		display_text(lang.LOGGED_IN)
		while ((session_valid_until >= time.time()) and session_active) or OVERRIDE:
			if not OVERRIDE:
				if   time_remaining < 2:
					set_alarm(1)
				elif time_remaining <= 10:
					set_alarm(time.time() % 10 < 1)
				else:
					set_alarm(0)
				set_red_led((time_remaining < 10) & ((time.time() % 2) < 1))
				if time_remaining < LOW_CREDIT_MINUTES:
					if not warning_sent:
						try:
							callbacks.credit_low_warning(uid, username)
						except NameError:
							logging.debug('No callback defined for event credit_low_warning')
						except TypeError:
							logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
						warning_sent = True
				else:
					warning_sent = False
			set_yellow_led(job_active & ((time.time() % 2) < 1))

			if not machine_is_on:
				logging.debug('Logout due to turning off the machine')
				logout()
				try:
					callbacks.machine_turn_off()
				except NameError:
					logging.debug('No callback defined for event machine_turn_off')
				except TypeError:
					logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
			elif do_cancel and not OVERRIDE:
				logging.debug('Manual logout triggered')
				logout()
				try:
					callbacks.user_logout(uid, username)
				except NameError:
					logging.debug('No callback defined for event user_logout')
				except TypeError:
					logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
			elif job_active != job_is_running:
				# Manual debouncing as the state signal may trigger when switching the machine off
				if last_state_change + STATE_DEBOUNCE_TIME < time.time():
					if not job_active:
						logging.debug('Job started')
						job_started = time.time()
						try:
							callbacks.job_start(uid, username)
						except NameError:
							logging.debug('No callback defined for event job_start')
						except TypeError:
							logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
					else:
						logging.debug('Job ended')
						try:
							callbacks.job_end(uid, username, time.time() - job_started)
						except NameError:
							logging.debug('No callback defined for event job_end')
						except TypeError:
							logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
					job_active = not job_active
					last_state_change = time.time()
			else:
				last_state_change = time.time() #reset debounce timer
				time.sleep(.3) # Reduce CPU load by fewer executions

		if session_active and session_valid_until < time.time():
			# user is still logged in (not logged out/machine off) but 1 minute is over
			if revalidate(): # try to extend session
				session_valid_until += 60  # extend by one minute
				logging.debug('Session extended sucessfully')
			else: # probably not enough credit
				logging.debug('Could not extend session')
				logout()
				try:
					if job_active:
						callbacks.credit_runout_interrupt(uid, username, time.time() - job_started)
					else:
						callbacks.credit_runout(uid, username)
				except NameError:
					logging.debug('No callback defined for event credit_runout or credit_runout_interrupt')
				except TypeError:
					logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
	lock_machine()
