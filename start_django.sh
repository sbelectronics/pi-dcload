#! /bin/bash
cd /home/pi/dcload
nohup python ./web_server.py > /tmp/dcload.out 2> /tmp/dcload.err & 
