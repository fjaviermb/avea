# Creator : Corentin Farque @Hereath
# Creation date : 2017-02-04
# License : MIT
# Source : https://github.com/Hereath/avea
#
# Description : Script that takes control of a given Elgato Avea bulb.
# Dependancies : sudo pip3 install bluepy


#  Imports
import bluepy  # for bluetooth transmission
import configparser  # for config file management
import argparse  # for sys arg parsing
import os  # for file handling

# TODO: Definition of moods to be used in setMood()


class Bulb():
    """
    The class that represents an Avea bulb using its MAC address
    """
    def __init__(self,address):
        """
        Set the object's address
        And create a modified bluepy.btle.Peripheral object,
        see the SuperPeripheral class below for an explanation
        """
        self.addr = address
        self.bulb = SuperPeripheral(self.addr)

    def computeBrightness(self,brightness):
        """
        Return the hex code for the specified brightness
        """
        value = hex(int(brightness))[2:]
        value = value.zfill(4)
        value = value[2:] + value[:2]
        return "57" + value

    def computeColor(self,w=2000,r=0,g=0,b=0):
        """
        Return the hex code for the specified colors
        """
        color = "35"
        fading = "1101"
        unknow = "0a00"
        white = hex(int(w) | int(0x8000))[2:].zfill(4)[2:] + hex(int(w) | int(0x8000))[2:].zfill(4)[:2]
        red = hex(int(r) | int(0x3000))[2:].zfill(4)[2:] + hex(int(r) | int(0x3000))[2:].zfill(4)[:2]
        green = hex(int(g) | int(0x2000))[2:].zfill(4)[2:] + hex(int(g) | int(0x2000))[2:].zfill(4)[:2]
        blue = hex(int(b) | int(0x1000))[2:].zfill(4)[2:] + hex(int(b) | int(0x1000))[2:].zfill(4)[:2]

        return color + fading + unknow + white + red + green + blue

    def setColor(self, white,red,green,blue):
        """
        Wraper for computeColor()
        """
        self.bulb.writeCharacteristic(40, self.computeColor(check_boundaries(white),check_boundaries(red),check_boundaries(green),check_boundaries(blue)))

    def setBrightness(self,brightness):
        """
        Wraper for computeBrightness()
        """
        self.bulb.writeCharacteristic(40, self.computeBrightness(check_boundaries(brightness)))

    # TODO
    def setMood(self,mood):
        """
        Set the bulb to a predefined mood
        # TODO: needs a more complete list of moods
        """
        pass

    # TODO
    def getBrightness(self):
        """
        Retrieve and return the current brightness of the bulb
        """
        pass

    # TODO
    def getColor(self):
        """
        Retrieve and return the current color of the bulb
        """
        pass

def discoverAveaBulbs():
    """
    Scan the BLE neighborhood for an Avea bulb
    and add its address to the config file
    This method requires the script to be launched as root
    """
    bulb_list = []
    from bluepy.btle import Scanner, DefaultDelegate, Peripheral
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(6.0)
    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if "Avea" in value:
                print("Found bulb with address " + str(dev.addr)+" !")
                bulb_list.append(Bulb(dev.addr))
    return bulb_list


def check_boundaries(value):
    """
    Check if the given value is out-of-bounds (0 to 4095)
    If so, correct it and return the inbounds value
    This is required for the payload to be properly understood by the bulb
    """
    if int(value) > 4095:
        return 4095

    elif int(value) < 0:
        return 0
    else:
        return value


class SuperPeripheral(bluepy.btle.Peripheral):
    """
    Overwrite of the Bluepy 'Peripheral' class.
    It overwrites the default writeCharacteristic() method,
    which by default only allows strings as input
    As we craft our own paylod, we need to bypass this behavior
    """
    def writeCharacteristic(self, handle, val, withResponse=False):
        cmd = "wrr" if withResponse else "wr"
        self._writeCmd("%s %X %s\n" % (cmd, handle, val))
        return self._getResp('wr')


# Example code on how to use it
if __name__ == '__main__':
    # get nearby bulbs in a list
    nearbyBulbs = discoverAveaBulbs();

    # for each bulb, set medium brightness and a red color
    for bulb in nearbyBulbs:
        bulb.setBrightness(2000) # ranges from 0 to 4095
        bulb.setColor(0,4095,0,0) # in order : white, red, green, blue
