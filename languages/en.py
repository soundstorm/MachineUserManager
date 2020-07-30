# -*- coding: utf-8 -*-

'''
Variable names that will be replaced:
{NAME}              Username
{CARD_HEX}          Short hexadecimal representation of card UID
{CARD_DEC}          Long decimal representation of card UID
{CREDIT_REMAINING}  Remaining credit of card
{TIME_REMAINING}    Remaining time (if currently logged in just credit / PRICE_MINUTE, otherwise (credit - PRICE_ONCE) / PRICE_MINUTE)
{PRICE_ONCE}        Price for starting a session
{PRICE_MINUTE}      Price per minute logged in (not respecing actual usage time, just the time "blocking" the machine)}

Text will be padded by whitespaces on the right and cropped to 20 chars
'''


TEMPLATE = [
	#01234567890123456789
	'',
	'',
	'',
	''
]

MACHINE_OFF = [
	#01234567890123456789
	'',
	'  Turn on machine',
	'     to login.',
	''
]

MACHINE_READY = [
	#01234567890123456789
	'Hold tag/card close',
	'  to the reader to',
	'       login.',
	''
]

# HAS COUNTDONW
CARD_UNAUTHORIZED = [
	#01234567890123456789
	' This card is not',
	' authorized to use',
	'   this machine.',
	'',
]

# HAS COUNTDONW
CARD_UNKNOWN = [
	#01234567890123456789
	'  This tag is not',
	'     registred.',
	'{CARD_HEX}',
	''
]

# HAS COUNTDONW
CREDIT_TOO_LOW = [
	#01234567890123456789
	'{NAME}',
	'Credit: {CREDIT_REMAINING}',
	'Credit too low.',
	'Please recharge.'
]

LOGIN = [
	#01234567890123456789
	'{NAME}',
	'Credit: {CREDIT_REMAINING}',
	'Once {PRICE_ONCE}+{PRICE_MINUTE}/Min',
	'Green: Yes / Red: No'
]

LOGGED_IN = [
	#01234567890123456789
	'Unlocked by:',
	'{NAME}',
	'Remaining time:',
	'{TIME_REMAINING} Min'
]

