#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
General configuration for Machine User Management System

THIS IS THE DEFAULTS FILE!

Please copy the needed variables to a new file called
user_config.py
This makes upgrading to newer versions easy by simply calling git pull.
'''

# DATABASE
DB_TYPE       = 'mysql'
DB_HOST       = 'localhost'
DB_USER       = 'machine'
DB_PASSWORD   = 'password'
DB_DATABASE   = 'machines'

MACHINE_NAME  = 'lasercutter' # must be in your database
# you can use any kind of identifier

# Language Config
UI_LANGUAGE   = 'en'

# Pricing
PRICE_ONCE         = 1.00
PRICE_MINUTE       = 0.15
LOW_CREDIT_MINUTES = 15
OVERRIDE           = False

# Hardware

LCD_ADDR    = 0x27 # PCF8574 Expander
TIMEOUT_SEC = 5    # Warning/Error timeout on display

# Invert on = active low
INVERT_BUTTONS = True
INVERT_LEDS    = False
INVERT_ALARM   = False
INVERT_STATE   = False
INVERT_POWER   = True
INVERT_PROT    = False

# State pin might trigger before power on is off
# This will lead to false callbacks when turning machine off while logged in 
STATE_DEBOUNCE_TIME = 1.0

# Pin definitions

#       3V3   =    #  1
#       SDA   =  2 #  3
#       SCL   =  3 #  5
#     1Wire   =  4 #  7
#       GND   =    #  9
#LED_R        = 17 # 11  # Optional, use user_config.py to define the pin
#LED_Y        = 27 # 13  # Optional, use user_config.py to define the pin
#LED_G        = 22 # 15  # Optional, use user_config.py to define the pin
#       3V3   =    # 17
#      MOSI   =    # 19
#      MISO   =    # 21
#       SCK   =    # 23
#       GND   =    # 25
#     ID_SD   =    # 27
BTN_CONFIRM   = 5  # 29
BTN_CANCEL    = 6  # 31
#ALARM        = 13 # 33  # Optional, use user_config.py to define the pin
#             = 19 # 35
#             = 26 # 37
#       GND   =    # 39

#        5V   =    #  2
#        5V   =    #  4
#       GND   =    #  6
#        TX   = 14 #  8
#        RX   = 15 # 10
#MACHINE_ON   = 18 # 12  # Optional, use user_config.py to define the pin
#       GND   =    # 14
#MACHINE_STATE= 23 # 16  # Optional, use user_config.py to define the pin
MACHINE_PROT  = 24 # 18
#       GND   =    # 20
#             = 25 # 22
#   SPI_CE0   =  8 # 24
#   SPI_CE1   =  7 # 26
#     ID_SC   =    # 28
#       GND   =    # 30
#             = 12 # 32
#       GND   =    # 34
#             = 16 # 36
#             = 20 # 38
#             = 21 # 40