# DCLoad Controller
# Scott Baker, http://www.smbaker.com
#
# This implements the main control loop and the VFD/LCD user interface
# for the pi-powered dc load.

import argparse
import ConfigParser
import os
import smbus
import spidev
import sys
import threading
import time
from dcload import DCLoad, DEFAULT_ADCADDR, DEFAULT_DACGAIN, DEFAULT_ADCGAIN
from dcload import DEFAULT_SENSE_OHMS
from smbpi.vfdcontrol import VFDController, trimpad
from smbpi.ioexpand import MCP23017
from smbpi.ds1820 import DS1820

DEFAULT_VTRIM = 1.0
DEFAULT_ATRIM = 1.0
DEFAULT_CONFIG_FILE = "/etc/dcload.conf"

# either 20x4 or 16x2 depending on the module
DEFAULT_DISPLAY = "20x4"
DEFAULT_NOCURSOR = True


class DCLoad_Control(DCLoad):
    def __init__(self,
                 bus,
                 spi,
                 adcAddr=DEFAULT_ADCADDR,
                 dacGain=DEFAULT_DACGAIN,
                 adcGain=DEFAULT_ADCGAIN,
                 senseOhms=DEFAULT_SENSE_OHMS,
                 display_kind=DEFAULT_DISPLAY,
                 display_nocursor=DEFAULT_NOCURSOR,
                 atrim=DEFAULT_ATRIM,
                 vtrim=DEFAULT_VTRIM):
        DCLoad.__init__(self, bus, spi, adcAddr, dacGain, adcGain, senseOhms)

        self.display = VFDController(MCP23017(bus, 0x20),
                                     four_line=(display_kind == "20x4"))
        self.display.setDisplay(True, False, False)
        self.display_kind = display_kind
        self.display_nocursor = display_nocursor

        self.ds = DS1820()

        self.vtrim = vtrim
        self.atrim = atrim
        self.temperature = 0.0
        self.desired_ma = 0
        self.actual_ma = 0
        self.actual_volts = 0
        self.cursor_x = 3
        self.last_line = ["", "", "", ""]
        self.update_count = 0

        self.new_desired_ma = None

        self.display.set_color(0)

    def start(self):
        self.start_thread()

    def update_display_16x2(self):
        # turn off cursor
        self.display.setDisplay(True, False, False)

        line1 = "A:%6.3f >%6.3f" % (self.desired_ma/1000.0, self.actual_ma/1000.0)

        line2 = "V:%6.3f W:%5.3f" % (self.actual_volts, self.actual_watts)

        self.display.setPosition(0, 0)
        self.display.writeStr(trimpad(line1, 16))

        self.display.setPosition(0, 1)
        self.display.writeStr(trimpad(line2, 16))

        # turn on cursor
        if self.cursor_x == 0:
            self.display.setPosition(3, 0)
        else:
            self.display.setPosition(4+self.cursor_x, 0)
        self.display.setDisplay(True, True, False)

    def writeLineDelta(self, y, line):
        if self.last_line[y] == line:
            return
        
        ll = self.last_line[y]
        i = 0
        first_diff = None
        last_diff = None
        while i < len(line):
            same = (i < len(ll)) and (line[i] == ll[i])
            if (not same) and (first_diff is None):
                first_diff = i
            if not same:
                last_diff = i
            i = i + 1

        if first_diff is None:
            return

        self.display.setDisplayCached(True, False, False)
        self.display.setPosition(first_diff, y)
        self.display.writeStr(line[first_diff:(last_diff+1)])

        self.last_line[y] = line

    def update_display_20x4(self):
        # calculate cursor offset taking decimal point into consideration
        if self.cursor_x == 0:
            cursor_offs = 6
        else:
            cursor_offs = 7 + self.cursor_x

        line1 = "Set: %6.3f A %6.1f C" % (self.desired_ma/1000.0, self.temperature)
        line2 = "Act: %6.3f A" % (self.actual_ma/1000.0)
        line3 = "Vol: %6.3f V" % self.actual_volts
        line4 = "Pow: %6.3f W" % self.actual_watts

        # The VFD supports a blink, but the problem I found is that with blink
        # enabled, occasional cursors will be visible in non-cursor positions as
        # the display is updated. So I chose to emulate blink myself.
        if self.display_nocursor:
            if self.update_count % 2 == 1:
                line1 = line1[:cursor_offs] + chr(0xFF) + line1[(cursor_offs+1):]

        self.writeLineDelta(0, trimpad(line1, 20))
        self.writeLineDelta(1, trimpad(line2, 20))
        self.writeLineDelta(2, trimpad(line3, 20))
        self.writeLineDelta(3, trimpad(line4, 20))

        self.display.setPosition(cursor_offs, 0)
        self.display.setDisplayCached(True, not self.display_nocursor, False)

        self.update_count = self.update_count + 1

    def update_display(self):
        if self.display_kind == "20x4":
            self.update_display_20x4()
        else:
            self.update_display_16x2()

    def get_mult(self):
        if self.cursor_x == 3:
            return 1
        elif self.cursor_x == 2:
            return 10
        elif self.cursor_x == 1:
            return 100
        else:
            return 1000

    def control_poll(self):
        self.actual_ma = self.GetActualMilliamps() * self.atrim
        self.actual_volts = self.GetActualVolts() * self.vtrim
        self.actual_watts = float(self.actual_volts) * float(self.actual_ma) / 1000.0

        if self.display.poller.get_button1_event():
            self.cursor_x = max(0, self.cursor_x-1)

        if self.display.poller.get_button3_event():
            self.cursor_x = min(3, self.cursor_x+1)

        delta = self.display.poller.get_delta()
        if delta != 0:
            mult = self.get_mult()
            self.new_desired_ma = min(10000, max(0, float(self.desired_ma) + delta * mult))

        if self.new_desired_ma is not None:
            self.desired_ma = self.new_desired_ma
            self.SetDesiredMilliamps(self.desired_ma)
            self.new_desired_ma = None

        self.update_display()

    def temperature_poll(self):
        self.temperature = self.ds.measure_first_device()

    def start_thread(self):
        self.poll_thread = DCLoad_Thread(self)
        self.poll_thread.start()

        self.temperature_thread = Temperature_Thread(self)
        self.temperature_thread.start()

    def set_new_desired_ma(self, ma):
        self.new_desired_ma = ma


class DCLoad_Thread(threading.Thread):
    def __init__(self, load):
        threading.Thread.__init__(self)
        self.load = load
        self.daemon = True
        self.stopping = False

    def run(self):
        while not self.stopping:
            self.load.control_poll()
            time.sleep(0.1)


class Temperature_Thread(threading.Thread):
    def __init__(self, load):
        threading.Thread.__init__(self)
        self.load = load
        self.daemon = True
        self.stopping = False

    def run(self):
        while not self.stopping:
            self.load.temperature_poll()
            time.sleep(1)


def parse_args():
    defaults = {"sense_ohms": DEFAULT_SENSE_OHMS,
                "atrim": DEFAULT_ATRIM,
                "vtrim": DEFAULT_VTRIM}

    # Get the config file argument

    conf_parser = argparse.ArgumentParser(add_help=False)
    _help = 'Config file name (default: %s)' % DEFAULT_CONFIG_FILE
    conf_parser.add_argument(
        '-c', '--conf_file', dest='conf_file',
        default=DEFAULT_CONFIG_FILE,
        type=str,
        help=_help)
    args, remaining_argv = conf_parser.parse_known_args()

    # Load the config file

    if args.conf_file:
        if not os.path.exists(args.conf_file):
            print >> sys.stderr, "Config file", args.conf_file, "does not exist. Not reading config."
        else:
            config = ConfigParser.SafeConfigParser()
            config.read(args.conf_file)
            defaults.update(dict(config.items("defaults")))

    # Parse the rest of the args

    parser = argparse.ArgumentParser(parents=[conf_parser])

    _help = 'Sense resistor ohms (default: %0.1f)' % DEFAULT_SENSE_OHMS
    parser.add_argument(
        '-s', '--sense', dest='sense_ohms',
        default=defaults["sense_ohms"],
        type=float,
        help=_help)

    _help = 'Amp Trim (default: %0.1f)' % DEFAULT_ATRIM
    parser.add_argument(
        '-a', '--atrim', dest='atrim',
        default=defaults["atrim"],
        type=float,
        help=_help)

    _help = 'Volt Trim (default: %0.1f)' % DEFAULT_VTRIM
    parser.add_argument(
        '-t', '--vtrim', dest='vtrim',
        default=defaults["vtrim"],
        type=float,
        help=_help)

    args = parser.parse_args()

    return args


def startup():
    global glo_dcload

    args = parse_args()

    bus = smbus.SMBus(1)
    spi = spidev.SpiDev()

    print "Setup: vtrim=%0.3f, atrim=%0.3f, sense_ohms=%0.1f" % (args.vtrim, args.atrim, args.sense_ohms)

    glo_dcload = DCLoad_Control(bus, spi, vtrim=args.vtrim, atrim=args.atrim, 
                                senseOhms=args.sense_ohms)
    glo_dcload.start()


def main():
    startup()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
