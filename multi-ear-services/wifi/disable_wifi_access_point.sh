#!/bin/bash

echo "$0"

# stop and disable the access point services
sudo systemctl daemon-reload
sudo systemctl disable hostapd
sudo systemctl stop hostapd
sudo systemctl disable dnsmasq
sudo systemctl stop dnsmasq

# link to enable
sudo ln -sf /opt/multi-ear-services/enable_wifi_access_point.sh switch_wifi_access_point_mode

exit 0
