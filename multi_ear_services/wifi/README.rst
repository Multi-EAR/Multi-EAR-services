*************************************
Multi-EAR services - Wi-Fi 
*************************************

The Multi-EAR automatically connects to known wireless networks in range.
If no known network is in range the Multi-EAR creates it's own wireless network with ``ssid=$HOSTNAME`` and ``passphrase=multi-ear``.

Checkout _raspberryconnect!

.. _raspberryconnect: https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/158-raspberry-pi-auto-wifi-hotspot-switch-direct-connection

The Wi-Fi hotspot systemd .service is triggered via a .timer unit.


Service
=======

https://www.man7.org/linux/man-pages/man5/systemd.service.5.html

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


Timer
=====

https://www.man7.org/linux/man-pages/man5/systemd.timer.5.html

:Timer:
    multi-ear-wifi.timer
:OnActiveSec:
    5min
:OnUnitActiveSec:
    5min
