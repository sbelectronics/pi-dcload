sudo raspi-config
   enable spi and i2d

sudo apt-get update
sudo apt-get -y install python-smbus i2c-tools python-pip

mkdir python-spi
cd python-spi
wget https://raw.github.com/doceme/py-spidev/master/setup.py
wget https://raw.github.com/doceme/py-spidev/master/spidev_module.c
echo > README.md
echo > CHANGELOG.md
sudo python setup.py install

# On Pi-Zero-W increase the i2c speed
sudo emacs /boot/config.txt
    dtparam=i2c1=on
    dtparam=i2c1_baudrate=400000


# DO NOT DO
sudo pip install adafruit-ads1x15

fix bug in adafruit library:
 sudo emacs /usr/local/lib/python2.7/dist-packages/Adafruit_PureIO/smbus.py
        cmdstring = create_string_buffer(len(cmd))
        for i, val in enumerate(cmd):
      -    cmdstring[i] = val
      +    cmdstring[i] = chr(val)