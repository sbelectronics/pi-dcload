sudo raspi-config
   enable spi and i2d

sudo apt-get update
sudo apt-get -y install python-smbus i2c-tools python-pip

# install spidev
mkdir python-spi
cd python-spi
wget https://raw.github.com/doceme/py-spidev/master/setup.py
wget https://raw.github.com/doceme/py-spidev/master/spidev_module.c
echo > README.md
echo > CHANGELOG.md
sudo python setup.py install

# install django
sudo pip install Django==1.7

# On Pi-Zero-W increase the i2c speed
sudo emacs /boot/config.txt
    dtparam=i2c1=on
    dtparam=i2c1_baudrate=400000

# Add to crontab for auto startup
@reboot bash /home/pi/dcload/start_django.sh &> /dev/null

# Avoid writing to the sd-card
sudo emacs /etc/fstab
  tmpfs    /tmp            tmpfs    defaults,noatime,nosuid,size=100m    0 0
  tmpfs    /var/tmp        tmpfs    defaults,noatime,nosuid,size=30m    0 0
  tmpfs    /var/log        tmpfs    defaults,noatime,nosuid,mode=0755,size=100m    0 0
  tmpfs    /var/run        tmpfs    defaults,noatime,nosuid,mode=0755,size=2m    0 0
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo update-rc.d dphys-swapfile remove


# DO NOT DO
sudo pip install adafruit-ads1x15

fix bug in adafruit library:
 sudo emacs /usr/local/lib/python2.7/dist-packages/Adafruit_PureIO/smbus.py
        cmdstring = create_string_buffer(len(cmd))
        for i, val in enumerate(cmd):
      -    cmdstring[i] = val
      +    cmdstring[i] = chr(val)