#!/usr/bin/python
# -*- coding: utf-8 -*-

import smbus
from time import sleep

# I2C-Bus Port (raspberry default = 1)
I2C_PORT = 1

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

# control bits
LCD_EN = 0b00000100 # Enable bit
LCD_RS = 0b00000001 # Register select bit

class lcd:

# initializes objects and lcd
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, addr, rows=4, cols=16):
        self.addr = addr             # set device address
        if rows <= 4:                # set rows
            self.rows = rows
        else:
            self.rows = 4
        self.cols = cols             # set columns
        self.backlight_state = 'on'  # state of backlight ('on', 'off')
        self.display_state = 'on'    # state of display ('on', 'off')
        self.backlight_value = LCD_BACKLIGHT
        self.cursor_state = 'hide'   # state of cursor ('hide', 'on', 'blink')
        self.row_state = 0           # actual cursor position
        self.col_state = 0
        self.bus = smbus.SMBus(I2C_PORT)
        self.lcd_write_cmd(0x03)
        self.lcd_write_cmd(0x03)
        self.lcd_write_cmd(0x03)
        self.lcd_write_cmd(0x02)
        sleep(0.1)

        self.lcd_write_cmd(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        self.lcd_write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.lcd_write_cmd(LCD_CLEARDISPLAY)
        self.lcd_write_cmd(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        sleep(0.2)


# Low level functions
# ~~~~~~~~~~~~~~~~~~~

# Write a single i2c command (low level function)
    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd | self.backlight_value)
        sleep(0.0002)

# clocks EN to latch command (low level function)
    def lcd_strobe(self, data):
        self.write_cmd(data | LCD_EN)
        sleep(.0005)
        self.write_cmd(data & ~LCD_EN)
        sleep(.0002)

# Write a nibble to the I2C bus (low level function)
    def lcd_write_four_bits(self, data):
        self.write_cmd(data)
        self.lcd_strobe(data)

# write command to lcd (low level function)
    def lcd_write_cmd(self, cmd):
        self.lcd_write_four_bits((cmd & 0xF0))
        self.lcd_write_four_bits(((cmd << 4) & 0xF0))

# write data to lcd (low level function)
    def lcd_write_data(self, cmd):
        self.lcd_write_four_bits(LCD_RS | (cmd & 0xF0))
        self.lcd_write_four_bits(LCD_RS | ((cmd << 4) & 0xF0))


# LCD functions
# ~~~~~~~~~~~~~

# put string at cursor position
    def write_string(self, string):
        self.col_state = self.col_state + len(string)
        for char in string:
            self.lcd_write_data(ord(char))

# put string at position given by row and col
    def display_string(self, string, row, col):
        if row >= self.rows:
            row = self.rows - 1
        self.row_state = row
        self.col_state = col + len(string)
        row_offsets = [0x00, 0x40, self.cols, 0x40 + self.cols]
        self.lcd_write_cmd(LCD_SETDDRAMADDR | (row_offsets[row] + col))
        string = string.replace('ä', '\xE1').replace('Ä', '\xE1')
        string = string.replace('ö', '\xEF').replace('Ö', '\xEF')
        string = string.replace('ü', '\xF5').replace('Ü', '\xF5')
        string = string.replace('ß', '\xE2')
        for char in string:
            self.lcd_write_data(ord(char))

# set cursor position
    def set_cursor(self, row, col):
        if row >= self.rows:
            row = self.rows - 1
        row_offsets = [0x00, 0x40, self.cols, 0x40 + self.cols]
        self.row_state = row
        self.col_state = col
        self.lcd_write_cmd(LCD_SETDDRAMADDR | (col + row_offsets[row]))

# set cursor on
    def cursor_on(self):
        self.cursor_state = 'on'
        self.lcd_write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSORON)
        sleep(.05)

# set cursor blinking
    def cursor_blink(self):
        self.cursor_state = 'blink'
        self.lcd_write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_BLINKON)
        sleep(.05)

# set cursor off
    def cursor_off(self):
        self.cursor_state = 'off'
        self.lcd_write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF)
        sleep(.05)

# set to home
    def home(self):
        self.row_state = 0
        self.col_state = 0
        self.lcd_write_cmd(LCD_RETURNHOME)
        #sleep(1)

# clear lcd and set to home
    def clear(self):
        self.row_state = 0
        self.col_state = 0
        self.lcd_write_cmd(LCD_CLEARDISPLAY)
        self.lcd_write_cmd(LCD_RETURNHOME)
        #sleep(1)

# Move display left one position
    def move_left(self):
        self.col_state = self.col_state - 1
        self.lcd_write_cmd(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVELEFT)

# Move display right one position
    def move_right(self):
        self.col_state = self.col_state + 1
        self.lcd_write_cmd(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVERIGHT)

# Switch display on
    def display_on(self):
        self.display_state = 'on'
        self.lcd_write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYON)

# Switch display off
    def display_off(self):
        self.display_state = 'off'
        self.lcd_write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYOFF)

# Switch backlight on
    def backlight_on(self):
        self.backlight_state = 'on'
        self.backlight_value = LCD_BACKLIGHT
        self.write_cmd(0)

# Switch backlight off
    def backlight_off(self):
        self.backlight_state = 'off'
        self.backlight_value = LCD_NOBACKLIGHT
        self.write_cmd(0)

# Fill one of the first 8 CGRAM locations with custom characters.
# The location parameter must be between 0 and 7 and pattern must
# provide an array of 8 bytes containing the pattern.
    def create_char(self, location, pattern):
        # only position 0..7 are allowed
        location &= 0x7
        self.lcd_write_cmd(LCD_SETCGRAMADDR | (location << 3))
        for i in range(8):
            self.lcd_write_data(pattern[i])

# Get backlight status
    def get_backlight(self):
        return self.backlight_state

# Get display status
    def get_display(self):
        return self.display_state

# Get cursor status
    def get_cursor(self):
        return self.cursor_state

# Get cursor row position
    def get_row_pos(self):
       return self.row_state

# Get cursor column position
    def get_col_pos(self):
       return self.col_state

