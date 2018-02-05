# Control of an Elgato Avea bulb using a Raspberry Pi & Python

Tested with a Raspberry Pi 3 (with integrated bluetooth)

Thanks to [Marmelatze](https://github.com/Marmelatze/avea_bulb) for the POC which made this possible


## Communication protocol

### Intro

To communicate the bulb uses Bluetooth 4.0 "BLE"

This provide some interesting features for communications, to learn more go [here](https://learn.adafruit.com/introduction-to-bluetooth-low-energy/gatt)

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

The brightness is also an Int value between 0 and 4095, sent as a big-endian 4-bytes hex value


## Example

Let say we want the bulb to be pink at 75% brightness : 

75% brightness is roughly 3072 : 

Int | 4-bytes Hexadecimal | **Big-endian hex** 
---|---|---
2048 |0x0C00| **0x00C0**

The brightness command will be 0x570080

Pink is 100% red, 100% blue, no green. (We assume that the white value is also 0.)

#### Calculate the final values

Variables | Int Values | Hexadecimal values | Bitwise XOR | big-endian
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

To compute the correct values for each color, I created the following (here showing only for white) : 

w is the input value for the white color

```python
white = hex(int(w) | int(0x8000))[2:].zfill(4)[2:] + hex(int(w) | int(0x8000))[2:].zfill(4)[:2]
```


# Dependancies

Needs bluepy for the BLE connection to the bulb. To install : 

```bash
sudo apt-get install python-pip libglib2.0-dev
sudo pip install bluepy
```
