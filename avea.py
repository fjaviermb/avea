# Creator : Corentin Farque @Hereath
# Date : 2017-02-04

#
#  Imports
#
import bluepy
import ConfigParser
import argparse
import os.path

#
# Vars
#
old_values = {}  # Dict for old values
arg_values = {}  # Dict for arguments values
new_values = {}  # Dict for computed values
config = ConfigParser.ConfigParser()  # Config Parser object
configFile = "/home/pi/.avea.conf" # Config file path

#
# ArgParse configuration
#
parser = argparse.ArgumentParser(description='Control your Elgato Avea bulb using Python ! ')
parser.add_argument('-r', '--red', help='Set the red value of the bulb (0-4095)', required=False)
parser.add_argument('-g', '--green', help='Set the green value of the bulb (0-4095)', required=False)
parser.add_argument('-b', '--blue', help='Set the blue value of the bulb (0-4095)', required=False)
parser.add_argument('-w', '--white', help='Set the white value of the bulb (0-4095)', required=False)
parser.add_argument('-l', '--light', help='Set the brightness of the bulb (0-4095)', required=False)
parser.add_argument('-m', '--mood', help='Set a predefined mood', required=False)



#
# Class Peripheral. Used to overwrite the default writeCharacteristic() method that only allows strings as input
#
class SuperPeripheral(bluepy.btle.Peripheral):
    def writeCharacteristic(self, handle, val, withResponse=False):
        cmd = "wrr" if withResponse else "wr"
        self._writeCmd("%s %X %s\n" % (cmd, handle, val))
        return self._getResp('wr')

#
# Functions
#

# Check if the config file exists, else create and fill it
def check_config_file():
    if not os.path.isfile(configFile):
        config.add_section('Avea')
        config.set('Avea', 'Address', '78:A5:04:8E:9E:57')
        config.set('Avea', 'light', '2000')
        config.set('Avea', 'white', '2000')
        config.set('Avea', 'red', '2000')
        config.set('Avea', 'green', '2000')
        config.set('Avea', 'blue', '2000')
        with open(configFile, 'wb') as configfile:
            config.write(configfile)


# Updates the new values to the config file
def update_values():
    for each in new_values:
        if new_values[each]:
            config.set('Avea', each, new_values[each])
    with open(configFile, 'wb') as configfile:
        config.write(configfile)


# Check each value for out-of-boudnaries (0 to 4095) and correct them
def check_values_boundaries():
    for each in new_values:
        if new_values[each]:
            # More than 4095
            if int(new_values[each]) > 4095:
                new_values[each] = '4095'

            # Less than 0
            if int(new_values[each]) < 0:
                new_values[each] = '0'


# Return the hex code for the specified colors
def color():
    global new_values
    w = new_values["white"]
    r = new_values["red"]
    g = new_values["green"]
    b = new_values["blue"]

    color = "35"
    fading = "1101"
    unknow = "0a00"
    white = hex(int(w) | int(0x8000))[2:].zfill(4)[2:] + hex(int(w) | int(0x8000))[2:].zfill(4)[:2]
    red = hex(int(r) | int(0x3000))[2:].zfill(4)[2:] + hex(int(r) | int(0x3000))[2:].zfill(4)[:2]
    green = hex(int(g) | int(0x2000))[2:].zfill(4)[2:] + hex(int(g) | int(0x2000))[2:].zfill(4)[:2]
    blue = hex(int(b) | int(0x1000))[2:].zfill(4)[2:] + hex(int(b) | int(0x1000))[2:].zfill(4)[:2]

    return color + fading + unknow + white + red + green + blue


# Return the hex code for the specified brightness
def light():
    global new_values
    brightness = new_values["light"]
    value = hex(int(brightness))[2:]
    value = value.zfill(4)
    value = value[2:] + value[:2]
    return "57" + value


#
# Actual code
#
if __name__ == '__main__':

    # Check for config file
    check_config_file()

    # Get old values from config file
    config.read(configFile)
    addr = config.get('Avea', 'Address')
    for each in ["light", "white", "red", "green", "blue"]:
        old_values[each] = config.get('Avea', each)

    # Get arguments values
    arg_values = vars(parser.parse_args())

    # Check if mood is set
    if arg_values["mood"]:
        mood = arg_values["mood"]
        if "red" in mood:
            new_values = {'blue': '0', 'light': '4095', 'white': '0', 'green': '0', 'red': '4095'}
        if "blue" in mood:
            new_values = {'blue': '4095', 'light': '4095', 'white': '0', 'green': '0', 'red': '0'}
        if "green" in mood:
            new_values = {'blue': '0', 'light': '4095', 'white': '0', 'green': '4095', 'red': '0'}
        if "white" in mood:
            new_values = {'blue': '0', 'light': '4095', 'white': '4095', 'green': '0', 'red': '0'}
        if "sleep" in mood:
            new_values = {'blue': '0', 'light': '10', 'white': '0', 'green': '0', 'red': '4095'}
    else:
        # Else check args values
        for each in ["light", "white", "red", "green", "blue"]:
            if arg_values[each]:  # Does the value is set ?

                # Check for sign
                if "+" in arg_values[each] or "-" in arg_values[each]:
                    new_values[each] = str(int(old_values[each]) + int(arg_values[each]))  # Add old values with arg one

                # Absolute value
                else:
                    new_values[each] = arg_values[each]
            else:
                new_values[each] = old_values[each]

    check_values_boundaries()

    # Connect to the bulb
    bulb = SuperPeripheral(addr)

    # Send the values
    bulb.writeCharacteristic(40, color())
    bulb.writeCharacteristic(40, light())

    # Update values
    update_values()
