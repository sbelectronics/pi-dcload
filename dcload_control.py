import smbus
import spidev
import threading
import time
from dcload import DCLoad, DEFAULT_ADCADDR, DEFAULT_DACGAIN, DEFAULT_ADCGAIN
from smbpi.vfdcontrol import VFDController, trimpad
from smbpi.ioexpand import MCP23017


class DCLoad_Control(DCLoad):
    def __init__(self,
                 bus,
                 spi,
                 adcAddr=DEFAULT_ADCADDR,
                 dacGain=DEFAULT_DACGAIN,
                 adcGain=DEFAULT_ADCGAIN):
        DCLoad.__init__(self, bus, spi, adcAddr, dacGain, adcGain)

        self.display = VFDController(MCP23017(bus, 0x20))
        self.display.setDisplay(True, False, False)

        self.desired_ma = 0
        self.cursor_x = 3

        self.new_desired_ma = None

    def start(self):
        self.start_thread()

    def update_display(self, actual_ma, actual_volts):
        # turn off cursor
        self.display.setDisplay(True, False, False)

        line1 = "A:%6.3f >%6.3f" % (self.desired_ma/1000.0, actual_ma/1000.0)

        watts = float(actual_volts) * float(actual_ma) / 1000.0

        line2 = "V:%6.3f W:%5.3f" % (actual_volts, watts)

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
        actual_ma = self.GetActualMilliamps()
        actual_volts = self.GetActualVolts()

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

        self.update_display(actual_ma, actual_volts)

    def start_thread(self):
        self.poll_thread = DCLoad_Thread(self)
        self.poll_thread.start()


class DCLoad_Thread(threading.Thread):
    def __init__(self, load):
        threading.Thread.__init__(self)
        self.load = load
        self.daemon = True
        self.stopping = False

    def run(self):
        while not self.stopping:
            self.load.control_poll()
            time.sleep(0.01)


def main():
    bus = smbus.SMBus(1)
    spi = spidev.SpiDev()

    load = DCLoad_Control(bus, spi)
    load.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
