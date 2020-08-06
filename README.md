# MachineUserManager
NFC based User/Credit Management for machines like Lasercutters, CNCs, etc. in workshops by using a Raspberry Pi.

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.me/mittwoch)

![Login](https://github.com/soundstorm/MachineUserManager/raw/master/images/loggedin.jpg)

## Use-Case
If you're running an open workshop or makerspace, you may want to control access to sensitive machines like e.g. Lasercutters, CNC or similar.
On one hand to reduce wrong and potentially harmful usage by people who don't know how to use the machine.
And on the other hand to generate revenue or compensate the investments simply based on usage.

If you just want to use the program for access control, just set the cost to zero and you're good to go.

Security would be rated basic to medium, as one may fake the UID of a Mifare Card or at least for Ruida machines disable the machine protection completely.
If you want to be sure, that the machine cannot be used, add a sufficient relay, which unpowers the whole machine (may be hard to resume interrupted jobs if used with credit).
I placed the Pi in the control cabinet of my Ruida Laser, which I locked up with a simple lock (which can be jiggled open, so just basic security as said).
But in a semi-trusted area it works very well.

## Features
- Callbacks: Simply define callbacks on certain events to notify an user that credit is low, send pictures to chat when an job is done, update usage state on website...
  Currently my setup sends messages to our Rocket.Chat; using an IP-Cam I can fetch images of the finished job via ffmpeg.
- Simple installation: Just a few components needed to get ready.
- Cheap: The components you need are not that expensive.
  Even the cards for each user are just a few cents, if they don't have a compatible one already.
- Flexibility: This is a full rewrite of my former application, so to get things right, I designed it to be as flexible as possible (or at least currently needed).
  Translations, databases, all interchangable.
- Multimachine, single user management: By using a central database for management and running the applications on multiple devices (Pis) you can control multiple machines.
- Upgradeability: The nice thing about open source - just improve the application to fit your needs.

## Requirements
- Raspberry Pi (any generation will do, zero is be cost effective, but if mounted internally WiFi may be bad, so consider using an OTG-LAN-Adapter)
- Optocouplers, Resistors, Capacitors (depending on Machine; I used PC817, 1k and 100nF-10uF on a 24V machine)
- Relay (depending on your setup)
- PN532 Breakout (switched to I2C Mode)
- 2004 LCD with PCF8574 Breakout
- Two buttons
- Cables
- Lights, Piezo alarm (optional)
- Network-Switch (optional, used the original external RJ45 Jack, plugged the end into the switch and cabled the Lasercutter, Pi and IP-Cam into it)

## Interfacing
The best way to interact with your machine is to use optocouplers or if neccessary relays.
Additionally I recommend debouncing all inputs (buttons too if the cables run close to power lines or are long) with a series resistor and capacitor at the input.

If you don't want to use an optional pin, simply do not define it (all other variables need to be defined).

The pinout in `config.py` is based on my PCB which already has optocouplers builtin.
If you want a different pin setup, simply create a file `user_config.py` where you set the pins (and database, etc.) accordingly.

### Outputs
#### LEDs (optional)
![LED Tower](https://github.com/soundstorm/MachineUserManager/raw/master/images/ledtower.jpg)

`LED_R` / `LED_Y` / `LED_G` can be connected to either simple LEDs or to 12V/24V/... signal light towers/... (with proper optocouplers/MOSFETs/relays). Use `INVERT_LEDs` to make them active low.

#### Alarm (optional)
Connect `ALARM` pin to an active piezo (partly included in signal light towers). Use `INVERT_ALARM` to make it active low.

#### Protection (machine enable)
`MACHINE_PROT` is used to interrupt the machine/prevent usage. This can be connected to protective door switches (GRBL, Ruida) in series with the switch itself.

Example for Ruida Lasercutters:

```
                               __
DR_PROT ______/ ______________/  ↘︎_______ GND
        Door switch (NO)   Optocoupler
```
### Inputs

#### Buttons (interrupt)
`BTN_CONFIRM` and `BTN_CANCEL` are used to confirm login or logout (directly connected to GPIOs). You may want to use R/C decoupling:

```
GND –o–––––/ ––––[ 1kΩ ]––––o– GPIO
      \  Button            /
       `–––––––––| 1uF |––´
```
Button behaviour should be inverted with `INVERT_BUTTONS` if using NO-Switches.

#### Power state (optional, interrupt)
The power supply (12V/24V/...) of the machine can be connected via an optocoupler (with RC like above) to `MACHINE_ON` pin. Use `INVERT_POWER` to trigger on low.

```
                   ________
                  |        |
VIN –––[ x Ω ]–o––|.      ,|–––––– GPIO
               |  | \    / |
              ___ |  _ |/  |
              1uF |  ⊻⇘|   |
              ___ |  | |\  |
               |  | /    ↘︎ |
Supply GND ––––o––|´      `|–––––– Pi GND
                  |________|
```
(Resistor value: (VIN - VLED) / ILED)

#### Working state (optional, interrupt)
Connect `MACHINE_STATE` to an output of the controller where it signals the processing of an job. For Ruida machines this is simply labled `STATE`. For CNCs like grbl you may use the spindle output with more debounce duration (as the spindle may stop and start during a job multiple times).

Use optocoupler as in power state; if using AC as input pay attention! Use an optocoupler like SFH6206-3 and a proper resistor tolerant up to 400V. Don't use capacitors in AC setups.

### LCD
The software currently only supports **2004 LCD**s with **PCF8574** I2C backpacks.
Connect SDA/SCL accordingly (you may want to strip the [472] pull up resistors on the data lines to prevent 5V signals).
The address set can be configured with `LCD_ADDR`.
Defaults to `0x27` when all `Ax` pins are left open.
The modified library is based on a [netzmafia Library](http://www.netzmafia.de/skripten/hardware/RasPi/Projekt-LCD/index.html).

### NFC Reader
I had mixed results with RC522 readers, so I switched to the somewhat more expensive **PN532**, which offers I2C.
Some people say, that I2C is not reliable on the Raspberry Pi - so far all worked good/better than the previous SPI solution.
*Some* breakoutboards offer voltage regulators, so you *can* wire it up to 5V.
The library used (slightly modified; no blocking call) is from [hoanhan101](https://github.com/hoanhan101/pn532).
As the pinout of the PCF8574 and PN532 breakouts are the same, I crimped a 10p flat wire to 5x2 IDCs (2x4 would be enough, but had none) and daisychained them.
I connected all unused wires to GND to improve shielding inside of the Lasercutter (side by side with 230V etc).

## Configuration
All above parameters are also in `config.py`.
Please create your configuration as `user_config.py` to apply your changes.
As stated: if you just want basic access control and charge nothing for the usage, simply set `PRICE_ONCE` and `PRICE_MINUTE` to 0. You can also remove the prices from `languages/xx.py` (or better create a file `languages/own.py` and set `GUI_LANGUAGE = 'own'`.

`PRICE_ONCE` is charged when starting a session.
On power loss (when `MACHINE_ON` goes off, triggered by emergency stop/...) the session ends automatically and the user needs to log in again.
You can also only set `PRICE_ONCE` to reflect a price for using the machine but by setting `PRICE_MINUTE` to zero for unlimited time once logged in.

The default database creation can be found in `dbscripts/`

## Callbacks
You can define your callbacks in `user_callbacks.py`.
You're responsible to fetch exception within your callback, as the application only handles `NameError` if some callbacks are not defined or `TypeError` when using wrong parameter count.
The file comes with prewritten functions, ready to use.
If you need extra functions (e.g. for posting to your used chat solution), just add them right to the file.