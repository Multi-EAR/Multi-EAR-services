#!/bin/bash

echo "$0"

sudo systemctl daemon-reload
sudo systemctl enable hostapd
sudo systemctl start hostapd
sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq

exit 0
