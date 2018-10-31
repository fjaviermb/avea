# Control of an Elgato Avea bulb using Python


![](https://img.shields.io/badge/python_flavor-3.x-brightgreen.svg?style=for-the-badge)

The [Avea bulb from Elgato](https://www.amazon.co.uk/Elgato-Avea-Dynamic-Light-Android-Smartphone/dp/B00O4EZ11Q) is a light bulb that connects to an iPhone or Android app via Bluetooth.

This project aim to control it using a Bluetooth 4.0 compatible device and some Python magic.

Tested with a Raspberry Pi 3 and a Raspbery Pi Zero W (with integrated bluetooth)

## Reverse engineering of the bulb

I've used the informations given by [Marmelatze](https://github.com/Marmelatze/avea_bulb).

## Communication protocol

### Intro

To communicate the bulb uses Bluetooth 4.0 "BLE"

This provide some interesting features for communications, to learn more about it go [here](https://learn.adafruit.com/introduction-to-bluetooth-low-energy/gatt). To sum up, the bulb emits a set of `services` which have `characteristics`. We transmit to the latter to communicate.

The bulb uses the service `f815e810456c6761746f4d756e696368` and the associated characteristic `f815e811456c6761746f4d756e696368` to send and receive informations about its state (color, name and brightness)

### Commands and payload explanation

The first bytes of transmission is the command. A few commands are available :

Value | Command
--- | ---
0x35 | set / get bulb color
0x57 | set / get bulb brightness
0x58 | set / get bulb name

### Color command

For the color command, the transmission payload is as follows :

Command | Fading time | Useless byte | White value | Red value | Green value | Blue value
---|---|---|---|---|---|---

Each value of the payload is a 4 hexadecimal value. (The actual values are integers between 0 and 4095)

For each color, a prefix in the hexadecimal value is needed :

Color | prefix
---|---
White| 0x8000
Red | 0x3000
Green | 0x2000
Blue | 0X1000

The values are formatted in **big-endian** format :

Int | 4-bytes Hexadecimal | Big-endian hex
---|---|---
4095 | 0x0fff| **0xff0f**

### Brightness command

The brightness is also an Int value between 0 and 4095, sent as a big-endian 4-bytes hex value. The transmission looks like this :

Command | Brightness value |
---|---
0x57 | 0xff00

## Example

Let say we want the bulb to be pink at 75% brightness :

### Brightness
75% brightness is roughly 3072 (out of the maximum 4095):

Int | 4-bytes Hexadecimal | **Big-endian hex**
---|---|---
3072 |0x0C00| **0x000C**

The brightness command will be `0x57000C`

#### Calculate the color values
Pink is 100% red, 100% blue, no green. (We assume that the white value is also 0.) For each color, we convert the int value to hexadecimal, then we apply the prefix, then we convert to big-endian :

Variables | Int Values | Hexadecimal values | Bitwise XOR | Big-endian values
---|---|---|---|---
White| 0| 0x0000| 0x8000| 0x0080
Red | 4095| 0x0fff| 0x3fff| 0xff3f
Green | 0 | 0x0000| 0x2000 | 0x0020
Blue | 4095| 0x0fff | 0x1fff| 0xff1f


The final byte sequence for a pink bulb will be :

Command | Fading time | Useless byte | White value | Red value | Green value | Blue value
---|---|---|---|---|---|---
`0x35`|`1101`| `0000`| `0080`|`ff3f`|`0020`|`ff1f`

# Python implementation
To compute the correct values for each color, I created the following conversion (here showing for white) :

```python
white = hex(int(w) | int(0x8000))[2:].zfill(4)[2:] + hex(int(w) | int(0x8000))[2:].zfill(4)[:2]
```

# Bluepy writeCharacteristic() overwrite
By default, the btle.Peripheral() object of bluepy only allows to send UTF-8 encoded strings, which are internally converted to hexadecimal, like this :

```python
self._writeCmd("%s %X %s\n" % (cmd, handle, binascii.b2a_hex(val).decode('utf-8')))
```

As we craft our own hexadecimal payload, we need to bypass this behavior. A child class of Peripheral() is created and overwrites the writeCharacteristic() method, as follows :

```python
class SuperPeripheral(bluepy.btle.Peripheral):
    def writeCharacteristic(self, handle, val, withResponse=False):
        cmd = "wrr" if withResponse else "wr"
        self._writeCmd("%s %X %s\n" % (cmd, handle, val))
        return self._getResp('wr')
```

# Usage

First, do `sudo python3 avea.py -s`.

This will scan the Bluetooth neighborhood for an Avea Bulb, and create the config file accordingly.

You can now use simply `python3 avea.py` to control it, see below for arguments.

## Scan

A scan feature is available via `avea.py -s`. Note that you will need to have root privileges. This will report the MAC address of the Avea bulb.


## Control of the bulb

To get some help from the script itself : `python3 avea.py -h`

An argument is available for each color:

* red, `-r`,
* green, `-g`
* blue, `-b`,
* white, `-w`,
* as well as light, `-l`


For each color/light parameter, both absolute (from 0 to 4096) and relative values are accepted :

`python3 avea.py -r 2000` will set the red value to 2000
`python3 avea.py -w +1000` will add 1000 to the current white value

The script also supports predefined moods, called with `-m` :

* `sleep` is a very subtle red light
* `red` ,`blue`,`green`,`white` are color specific moods

# TODO

- Add the possibility to launch ambiances (which are mood-based scenes built in the bulb itslef) from the script.
- Query the bulb for its current state



# Dependancies
Needs bluepy for the BLE connection to the bulb. To install :

```bash
sudo apt-get install python3-pip libglib2.0-dev
sudo pip3 install bluepy
```
