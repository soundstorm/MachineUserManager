#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from pn532pi import Pn532I2c, Pn532, pn532
from RPLCD import i2c
import time
import RPi.GPIO as GPIO
from math import ceil
from importlib import import_module
from mqtt_notify import MqttNotify
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
db_connector.db_connector.configure(
	host     = DB_HOST,
	user     = DB_USER,
	password = DB_PASSWORD,
	database = DB_DATABASE,
	machine  = MACHINE_NAME
)

pni2c = Pn532I2c(1)
nfc = Pn532(pni2c)
nfc.begin()
nfc.setPassiveActivationRetries(0xFF)
nfc.SAMConfig()

GPIO.setmode(GPIO.BCM)

lcd = i2c.CharLCD('PCF8574', 0x27, port=1, charmap='A00', cols=20, rows=4)

notify = None
try:
	notify = MqttNotify(host=MQTT_HOST, username=MQTT_USERNAME, password=MQTT_PASSWORD, name=MQTT_DEVICE, manufacturer=MQTT_MFC, model=MQTT_MODEL)
except NameError:
	logging.info('MQTT_HOST not defined, not setting up MQTT notifier.')

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
price_once = 0
price_minute = 0
time_remaining = 0
credit = 0
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

def set_red_led(state : bool):
	try:
		GPIO.output(LED_R, state != INVERT_LEDS)
	except NameError:
		logging.info('No pin defined for LED_R or INVERT_LEDS not set')
	except Exception as e:
		logging.exception('Error while setting pin LED_R')

def set_yellow_led(state):
	try:
		GPIO.output(LED_Y, state != INVERT_LEDS)
	except NameError:
		logging.info('No pin defined for LED_Y or INVERT_LEDS not set')
	except Exception as e:
		logging.exception('Error while setting pin LED_Y')

def set_green_led(state : bool):
	try:
		GPIO.output(LED_G, state != INVERT_LEDS)
	except NameError:
		logging.info('No pin defined for LED_G or INVERT_LEDS not set')
	except Exception:
		logging.exception('Error while setting pin LED_G')

def set_button_leds(confirm : bool, cancel : bool):
	try:
		GPIO.output(LED_CONFIRM, confirm != INVERT_BUTTON_LEDS)
	except NameError:
		logging.info('No pin defined for LED_CONFIRM or INVERT_BUTTON_LED not set')
	except Exception:
		logging.exception('Error while setting pin LED_CONFIRM')
	try:
		GPIO.output(LED_CANCEL, cancel != INVERT_BUTTON_LEDS)
	except NameError:
		logging.info('No pin defined for LED_CANCEL or INVERT_BUTTON_LED not set')
	except Exception:
		logging.exception('Error while setting pin LED_CANCEL')

def set_alarm(state : bool):
	try:
		GPIO.output(ALARM, state != INVERT_ALARM)
	except NameError:
		logging.info('No pin defined for ALARM or INVERT_ALARM not set')
	except Exception:
		logging.exception('Error while setting pin ALARM')

def set_protection(state : bool):
	GPIO.output(MACHINE_PROT, state == INVERT_PROT)
	# Don't fetch error here to avoid failing silently

def read_tag():
	success, uid_stream = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
	tag_uid = 0
	if success:
		for i in uid_stream:
			tag_uid <<= 8
			tag_uid += i
		return tag_uid
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

def countdown(t):
	for i in range(t):
		lcd.cursor_pos = (3, 19)
		lcd.write_string(str(5 - i))
		time.sleep(1)

def display_text(arr):
	i = 0
	padding = ' '*20
	for line in arr:
		lcd.cursor_pos = (i, 0)
		lcd.write_string((line.format(
			NAME             = username,
			CARD_HEX         = "{:08x}".format(uid).upper(),
			CARD_DEC         = uid,
			CREDIT_REMAINING = credit,
			TIME_REMAINING   = time_remaining,
			PRICE_ONCE       = price_once if (int(price_once) != price_once) else int(price_once),
			PRICE_MINUTE     = price_minute if (int(price_minute) != price_minute) else int(price_minute)
		) + padding)[:20])
		i += 1
		if i == 4: # Limit to display lines
			break
	for n in range(i, 4):
		lcd.cursor_pos = (n, 0)
		lcd.write_string(padding) # Clear not defined lines

while True:
	lock_machine()
	set_alarm(0)
	set_button_leds(False, False)
	if notify is not None:
		notify.setLoggedIn(False)
		notify.setRemaining(0)
	if not machine_is_on:
		if notify is not None:
			notify.setPower(False)
			notify.setState(False)
		lcd.backlight_enabled = False
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
		if notify is not None:
			notify.setPower(True)
	while machine_is_on and not session_active and not OVERRIDE:
		display_text(lang.MACHINE_READY)
		lcd.backlight_enabled = True
		read_uid = None
		while machine_is_on and read_uid == None:
			read_uid = read_tag()
		if read_uid is None or not machine_is_on:
			break
		uid = read_uid
		try:
			callbacks.card_scan(uid)
		except NameError:
			logging.debug('No callback defined for event card_scan')
		except TypeError:
			logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
		session = db_connector.db_connector(uid)
		username, credit = session.get_user_info()
		authorized = session.is_authorized()
		try:
			job_is_running = GPIO.input(MACHINE_STATE) != INVERT_STATE
		except NameError:
			job_is_running = False # No pin for machine state defined, always assume no job is active
		if notify is not None:
			notify.setState(job_is_running)
		if username is None:
			logging.info('Card %d is unknown', uid)
			try:
				callbacks.card_unknown(uid)
			except NameError:
				logging.debug('No callback defined for event card_unknown')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
			display_text(lang.CARD_UNKNOWN)
			countdown(TIMEOUT_SEC)
		elif not authorized:
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
			price_once, price_minute = session.get_rate()
			if session.can_create_session():
				display_text(lang.LOGIN)
				# Reset button states
				do_cancel = False
				do_confirm = False
				set_button_leds(True, True)
				while machine_is_on:
					if do_cancel:
						logging.debug('Login was cancelled')
						break
					elif do_confirm:
						set_button_leds(False, True)
						if session.create_session():
							try:
								callbacks.user_login(uid, username)
							except NameError:
								logging.debug('No callback defined for event user_login')
							except TypeError:
								logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
							if notify is not None:
								notify.setLoggedIn(True)
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
	time_remaining = -1
	while (session_active or OVERRIDE) and machine_is_on:
		if not OVERRIDE:
			rem = session.get_remaining_time()
			if time_remaining != rem:
				if notify is not None:
					notify.setRemaining(rem)
				time_remaining = rem
				display_text(lang.LOGGED_IN)
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
		elif time_remaining == -1:
			time_remaining = 999
			if notify is not None:
				notify.setRemaining(time_remaining)
			display_text(lang.LOGGED_IN)
		set_yellow_led(job_active & ((time.time() % 2) < 1))

		if not session.extend_session():
			logging.debug('Could not extend session')
			session.end_session()
			lock_machine()
			try:
				if job_active:
					callbacks.credit_runout_interrupt(uid, username, time.time() - job_started)
				else:
					callbacks.credit_runout(uid, username)
			except NameError:
				logging.debug('No callback defined for event credit_runout or credit_runout_interrupt')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
		elif not machine_is_on:
			logging.debug('Logout due to turning off the machine')
			session.end_session()
			lock_machine()
			try:
				callbacks.machine_turn_off()
			except NameError:
				logging.debug('No callback defined for event machine_turn_off')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
		elif do_cancel and not OVERRIDE:
			logging.debug('Manual logout triggered')
			session.end_session()
			lock_machine()
			try:
				callbacks.user_logout(uid, username)
			except NameError:
				logging.debug('No callback defined for event user_logout')
			except TypeError:
				logging.exception('Your callback may be malformed or outdated as probably the parameters mismatch')
		elif job_active != job_is_running:
			if notify is not None:
				notify.setState(job_is_running)
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
	lock_machine()
