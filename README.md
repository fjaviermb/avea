# Control of an Elgato Avea bulb using Python

![](https://img.shields.io/badge/python_flavor-3.x-brightgreen.svg?style=for-the-badge)
![Travis (.org)](https://img.shields.io/travis/Hereath/avea.svg?style=for-the-badge)
![PyPI](https://img.shields.io/pypi/v/avea.svg?style=for-the-badge)

The [Avea bulb from Elgato](https://www.amazon.co.uk/Elgato-Avea-Dynamic-Light-Android-Smartphone/dp/B00O4EZ11Q) is a light bulb that connects to an iPhone or Android app via Bluetooth.

This project aim to control it using a Bluetooth 4.0 compatible device and some Python magic.

Tested on Raspberry Pi 3 and Zero W (with integrated bluetooth)

## TL;DR

```bash
# install pip3 and bluepy's dependancy libglib2
sudo apt-get install python3-pip libglib2.0-dev

pip3 install avea
```


## Library usage

Below is a quick how-to of the various methods of the library.

**Important : To use the scan feature of bluepy (the discover_avea_bulbs() function of the module), the script needs to be launched as root (or sudo -E)**

```python
import avea # Important !

# get nearby bulbs in a list, then retrieve the name of all bulbs
# Using this method requires root privileges
nearbyBulbs = avea.discover_avea_bulbs()
for bulb in nearbyBulbs:
    bulb.get_name()
    print(bulb.name)

# Or create a bulb if you know its address
myBulb = Bulb("xx:xx:xx:xx:xx:xx")

# Setter
myBulb.set_brightness(2000)  # ranges from 0 to 4095
myBulb.set_color(0,4095,0,0)  # in order : white, red, green, blue
myBulb.set_name("bedroom")

# Getter
print(myBulb.get_name())  # Query the name of the bulb
theName = myBulb.get_color() # Query the current color
theBrightness = myBulb.get_brightness() # query the current brightness level

# You can also access the values of the bulb without querying using the object variables
print(myBulb.brightness)
print(myBulb.white)
```

That's it. Pretty simple.

Check the explanation below for some more informations, or check the source !

## Reverse engineering of the bulb

I've used the informations given by [Marmelatze](https://github.com/Marmelatze/avea_bulb) as well as some reverse engineering using a `btsnoop_hci.log` file and Wireshark.

Below is a pretty thorough explanation of the BLE communication and the python implementation to communicate with the bulb.

As BLE communication is quite complicated, you might want to skip all of this if you just want to use the library. But it's quite interesting.


## Communication protocol

### Intro

To communicate the bulb uses Bluetooth 4.0 "BLE", which provide some interesting features for communications, to learn more about it go [here](https://learn.adafruit.com/introduction-to-bluetooth-low-energy/gatt).

To sum up, the bulb emits a set of `services` which have `characteristics`. We use the latter to communicate to the device.

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


## Python implementation
To compute the correct values for each color, I created the following conversion (here showing for white) :

```python
white = (int(w) | int(0x8000)).to_bytes(2, byteorder='little').hex()
```

## Bluepy writeCharacteristic() overwrite
By default, the btle.Peripheral() object of bluepy only allows to send UTF-8 encoded strings, which are internally converted to hexadecimal. As we craft our own hexadecimal payload, we need to bypass this behavior. A child class of Peripheral() is created and overwrites the writeCharacteristic() method, as follows :

```python
class AveaPeripheral(bluepy.btle.Peripheral):
    def writeCharacteristic(self, handle, val, withResponse=True):
        cmd = "wrr" if withResponse else "wr"
        self._writeCmd("%s %X %s\n" % (cmd, handle, val))
        return self._getResp('wr')
```

## Working with notifications using Bluepy
To reply to our packets, the bulb is using BLE notifications, and some setup is required to be able to receive these notifications with bluepy.

To subscribe to the bulb's notifications, we must send a "0100" to the BLE handle which is just after the one used for communication. As we use handle 0x0028 (40 for bluepy) to communicate, we will send the notification payload to the handle 0x0029 (so 41 for bluepy)

```python
self.bulb.writeCharacteristic(41, "0100")
```
After that, we will receive notifications from the bulb.

## TODO

- Add the possibility to launch ambiances (which are mood-based scenes built in the bulb itslef) from the script.
