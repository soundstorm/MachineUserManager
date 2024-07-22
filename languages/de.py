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
	'Maschine einschalten',
	'um sich Einzuloggen.',
	''
]

MACHINE_READY = [
	#01234567890123456789
	' Karte/Anhänger an',
	'den Leser halten zum',
	'     Einloggen',
	''
]

# HAS COUNTDONW
CARD_UNAUTHORIZED = [
	#01234567890123456789
	'Die Karte ist nicht',
	'für die Nutzung der',
	'  Maschine freige-',
	'     schaltet.',
]

# HAS COUNTDONW
CARD_UNKNOWN = [
	#01234567890123456789
	'Die Karte ist nicht',
	'im System hinterlegt',
	'{CARD_HEX}',
	''
]

# HAS COUNTDONW
CREDIT_TOO_LOW = [
	#01234567890123456789
	'{NAME}',
	'Guthaben: {CREDIT_REMAINING}',
	'Guthaben zu gering.',
	'Bitte aufladen.'
]

LOGIN = [
	#01234567890123456789
	'{NAME}',
	'Guthaben: {CREDIT_REMAINING}',
	'Einmalig {PRICE_ONCE}+{PRICE_MINUTE}/Min',
	'Grün: Ja / Rot: Nein'
]

LOGGED_IN = [
	#01234567890123456789
	'Freigeschaltet von:',
	'{NAME}',
	'Verbleibende Zeit:',
	'{TIME_REMAINING} Min'
]

DB_UNAVAILABLE = [
	#01234567890123456789
	'Datenbank derzeit',
	'nicht verfügbar.',
	'Später erneut',
	'versuchen.'
]

