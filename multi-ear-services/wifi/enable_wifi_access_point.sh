#!/bin/bash

echo "$0"

# stop and disable the access point services
sudo systemctl daemon-reload
sudo systemctl enable hostapd
sudo systemctl start hostapd
sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq

# link to disable
sudo ln -sf /opt/multi-ear-services/disable_wifi_access_point.sh switch_wifi_access_point_mode

exit 0
