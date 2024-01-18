#!/bin/bash

# These bytes enable certain features when sent to the hidraw device
# It does work without all the 0 padding, but wireshark will complain about misformed packets
CHATMIX_ENABLE="06490100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
SONAR_ICON_ENABLE="068d0100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

# Look in dmesg to get this. It should be the one related to input4
HIDRAWDEV=/dev/hidraw2

# Send data to enable features
printf $CHATMIX_ENABLE | xxd -r -p - | tee $HIDRAWDEV
printf $SONAR_ICON_ENABLE | xxd -r -p - | tee $HIDRAWDEV

# Example ids, you can get these with `lsusb`
BUS=1
DEVICE=2

# Read events
usbhid-dump -s $BUS:$DEVICE -f -e stream