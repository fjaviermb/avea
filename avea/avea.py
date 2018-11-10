"""
Module that controls an Elgato Avea bulb

The lib allows you to :
    - scan the bluetooth neighborhood and find nearby Avea bulbs
    - set the color and brightness of a bulb
    - get the current name, color and brightness of a bulb

Creator : Corentin Farque @Hereath
Creation date : 2017-02-04
License : MIT
Source : https://github.com/Hereath/avea
"""

# Imports
import time

# Imports
import bluepy  # for bluetooth transmission


class Bulb:
    """The class that represents an Avea bulb

    An Bulb object describe a real world Avea bulb,
    with a BLE connector used to communicate and
    the associated address
    """
    def __init__(self, address):
        """ Create a new Bulb object that represents a real Avea bulb

        - Set the object's address
        - Create a modified bluepy.btle.Peripheral object (see AveaPeripheral)
        - Add a delegate for notifications
        - Send the "enable bit" for notification
        """
        self.addr = address
        self.name = None
        self.red = None
        self.blue = None
        self.green = None
        self.brightness = None
        self.white = None
        self.bulb = AveaPeripheral(self.addr)
        self.bulb.withDelegate(AveaDelegate(self))
        self.subscribe_to_notification()

    def subscribe_to_notification(self):
        """Subscribe to the bulbs notifications"""

        self.bulb.writeCharacteristic(41, "0100")

    # IDEA: request the bulb's state afterward to check if it's applied
    # IDEA: make the method RGB compliant (0 to 255 instead of 0-4095)
    def set_color(self, white, red, green, blue):
        """Send the specified color to the bulb"""

        self.bulb.writeCharacteristic(40, compute_color(check_bounds(white),
                                                        check_bounds(red),
                                                        check_bounds(green),
                                                        check_bounds(blue)))

    def set_brightness(self, brightness):
        """Send the specified brightness to the bulb"""

        self.bulb.writeCharacteristic(40, compute_brightness(check_bounds(brightness)))

    # TODO : Reverse engineer how to select and send moods requests
    # what Elgato's app is calling 'ambiances'
    def set_mood(self, mood):
        """
        Set the bulb to a predefined mood
        # TODO: needs a more complete list of moods
        """
        pass

    def get_brightness(self):
        """Retrieve and return the current brightness of the bulb"""

        print("sending the request")
        self.bulb.writeCharacteristic(40, "57")
        self.bulb.waitForNotifications(1.0)

    def get_color(self):
        """Retrieve and return the current color of the bulb

        A .5s sleep is here to accomodate for the bulb's response time :
        If get_color() is called directly after set_color(), the bulb
        won't reply with the new values
        """
        time.sleep(0.5)
        self.bulb.writeCharacteristic(40, "35")
        self.bulb.waitForNotifications(1.0)

    def get_name(self):
        """Get the name of the bulb"""

        print("Retrieving bulb's name..")
        self.bulb.writeCharacteristic(40, "58")
        self.bulb.waitForNotifications(1.0)

    def set_name(self, name):
        """Set the name of the bulb"""

        byteName = name.encode("utf-8")
        command = "58"+byteName.hex()
        self.bulb.writeCharacteristic(40,command)


    def process_notification(self, data):
        """Method called when a notification is send from the bulb

        It is processed here rather than in the handleNotification() function,
        because the latter is not a method of the Bulb class.
        """
        cmd = data[:1]
        values = data[1:]
        cmd = int(cmd.hex())

        # Convert the brightness value
        if cmd is 57:
            self.brightness = int.from_bytes(values, 'little')

        # Convert the color values
        elif cmd is 35:
            hex = values.hex()
            self.red = int.from_bytes(bytes.fromhex(hex[-4:]), "little") ^ int(0x3000)
            self.green = int.from_bytes(bytes.fromhex(hex[-8:-4]), "little") ^ int(0x2000)
            self.blue = int.from_bytes(bytes.fromhex(hex[-12:-8]), "little") ^ int(0x1000)
            self.white = int.from_bytes(bytes.fromhex(hex[-16:-12]), "little")

        # Convert the name
        elif cmd is 58:
            self.name = values.decode("utf-8")


def discover_avea_bulbs():
    """Scanning feature

    Scan the BLE neighborhood for an Avea bulb
    and add its address to the config file
    This method requires the script to be launched as root
    """
    bulb_list = []
    from bluepy.btle import Scanner, DefaultDelegate

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


def compute_brightness(brightness):
    """Return the hex code for the specified brightness"""

    value = hex(int(brightness))[2:]
    value = value.zfill(4)
    value = value[2:] + value[:2]
    return "57" + value


def compute_color(w=2000, r=0, g=0, b=0):
    """Return the hex code for the specified colors"""

    color = "35"
    fading = "1101"
    unknow = "0a00"
    white = (int(w) | int(0x8000)).to_bytes(2, byteorder='little').hex()
    red = (int(r) | int(0x3000)).to_bytes(2, byteorder='little').hex()
    green = (int(g) | int(0x2000)).to_bytes(2, byteorder='little').hex()
    blue = (int(b) | int(0x1000)).to_bytes(2, byteorder='little').hex()

    return color + fading + unknow + white + red + green + blue


def check_bounds(value):
    """Check if the given value is out-of-bounds (0 to 4095)

    If so, correct it and return the inbounds value
    This is required for the payload to be properly understood by the bulb
    """
    try:
        if int(value) > 4095:
            return 4095

        elif int(value) < 0:
            return 0
        else:
            return value
    except ValueError:
        print("Value was not a number, returned default value of 0")
        return 0


class AveaDelegate(bluepy.btle.DefaultDelegate):
    """Overwrite of Bluepy's DefaultDelegate class

    It adds a bulb object that refers to the Bulb.bulb object which
    called this delegate.
    It is used to call the bulb.process_notification() function
    """
    def __init__(self, bulbObject):
        self.bulb = bulbObject

    def handleNotification(self, cHandle, data):
        """Async function called when a device sends a notification.

        It's just passing the data to process_notification(),
        which is linked to the emitting bulb (via self.bulb).
        """
        self.bulb.process_notification(data)


class AveaPeripheral(bluepy.btle.Peripheral):
    """Overwrite of the Bluepy 'Peripheral' class.

    It overwrites only the default writeCharacteristic() method
    """
    def writeCharacteristic(self, handle, val, withResponse=False):
        """Overwrite of the writeCharacteristic method

        By default it only allows strings as input
        As we craft our own paylod, we need to bypass this behavior
        and send hex values directly
        """
        cmd = "wrr" if withResponse else "wr"
        self._writeCmd("%s %X %s\n" % (cmd, handle, val))
        return self._getResp('wr')


# Example code on how to use it
if __name__ == '__main__':
    # get nearby bulbs in a list
    nearbyBulbs = discover_avea_bulbs()

    # Or create a bulb if you know its address
    myBulb = Bulb("xx:xx:xx:xx:xx:xx")

    # for each bulb
    for bulb in nearbyBulbs:
        bulb.get_name()
        print(bulb.name)

        bulb.set_brightness(2000)  # ranges from 0 to 4095
        bulb.set_color(0, 4095, 0, 0)  # in order : white, red, green, blue
