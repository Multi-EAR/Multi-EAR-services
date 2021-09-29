#!/bin/bash

echo "$0"

sudo systemctl disable hostapd
sudo systemctl stop hostapd
sudo systemctl disable dnsmasq
sudo systemctl stop dnsmasq

exit 0
