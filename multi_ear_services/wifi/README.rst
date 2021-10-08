*************************************
Multi-EAR services - Wifi 
*************************************

The Multi-EAR automatilly connects to known wireless networks if they are in range.
If no known network is in range the Multi-EAR simply creates it's own wireless network with ``ssid=$HOSTNAME`` and ``passphrase=multi-ear``.


Checkout _raspberryconnect!

.. _raspberryconnect: https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/157-raspberry-pi-auto-wifi-hotspot-switch-internet


Service
=======

:Service:
    multi-ear-wifi.service
:Type:
    oneshot
:RemainAfterExit:
    yes
:ExecStart:
    /home/tud/.py37/bin/autohotspot
:Restart:
    on-fail
:SyslogIdentifier:
    multi-ear-wifi
:Log:
    /var/log/multi-ear/wifi.log
