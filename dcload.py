from smbpi.mcp4821 import MCP4821
from smbpi.ads1115 import ADS1115, MUX_AIN0_AIN3, MUX_AIN1_AIN3, PGA_4V, MODE_CONT, DATA_32, COMP_MODE_TRAD, COMP_POL_LOW, COMP_NON_LAT, COMP_QUE_DISABLE
import smbus
import spidev
import sys
import time

DEFAULT_DACGAIN = 1
DEFAULT_ADCGAIN = 1
DEFAULT_ADCADDR = 0x48
DEFAULT_SENSE_OHMS = 0.1


class DCLoad:
    def __init__(self,
                 bus,
                 spi,
                 adcAddr=DEFAULT_ADCADDR,
                 dacGain=DEFAULT_DACGAIN,
                 adcGain=DEFAULT_ADCGAIN,
                 senseOhms=DEFAULT_SENSE_OHMS):
        self.bus = bus
        self.spi = spi
        self.adcAddr = adcAddr
        self.dacGain = dacGain
        self.adcGain = adcGain
        self.adcResolution = 32767   # 16-bit, positive half
        self.adcVRef = 4096          # in millivolts
        self.adcDiv1 = 75000.0
        self.adcDiv2 = 1000.0
        self.adcOffs = 0  # 55
        self.loadResistor = senseOhms

        self.dac = MCP4821(spi, gain=self.dacGain)
        self.adc = ADS1115(bus, self.adcAddr)

    def SetDesiredMilliamps(self, ma):
        self.dac.SetVoltage(float(ma) * float(self.loadResistor) / 1000.0)

    def GetActualMilliamps(self):
        # Note: We use differential mode, because the GND between the vreg and the
        # ADC may have some voltage drop. 
        self.adc.write_config(MUX_AIN0_AIN3 | PGA_4V | MODE_CONT | DATA_32 | COMP_MODE_TRAD | COMP_POL_LOW | COMP_NON_LAT | COMP_QUE_DISABLE)
        self.adc.wait_samp()
        self.adc.wait_samp()

        v = self.adc.read_conversion()
        millivolts = float(v) * float(self.adcVRef) / float(self.adcResolution) + self.adcOffs

        return millivolts/float(self.loadResistor)

    def GetActualVolts(self):
        # Note: We use differential mode, because the GND between the vreg and the
        # ADC may have some voltage drop. 
        self.adc.write_config(MUX_AIN1_AIN3 | PGA_4V | MODE_CONT | DATA_32 | COMP_MODE_TRAD | COMP_POL_LOW | COMP_NON_LAT | COMP_QUE_DISABLE)
        self.adc.wait_samp()
        self.adc.wait_samp()

        v = self.adc.read_conversion()
        millivolts = float(v) * float(self.adcVRef) / float(self.adcResolution) + self.adcOffs

        return millivolts * (self.adcDiv1 + self.adcDiv2) / (self.adcDiv2) / 1000.0


def main():
    if len(sys.argv)<=1:
        print >> sys.stderr, "Please specify milliamps as command-line arg"
        sys.exit(-1)

    desired_ma = float(sys.argv[1])

    bus = smbus.SMBus(1)
    spi = spidev.SpiDev()
    dcload = DCLoad(bus, spi)

    dcload.SetDesiredMilliamps(desired_ma)
    while True:
        actual_ma = dcload.GetActualMilliamps()
        actual_volts = dcload.GetActualVolts()
        print "Desired_ma=%0.4f, Actual_ma=%0.4f, actual_volts=%0.4f        \n" % (desired_ma, actual_ma, actual_volts),
        time.sleep(0.1)


if __name__ == "__main__":
    main()
