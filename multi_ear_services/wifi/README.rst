*************************************
Multi-EAR services - Wi-Fi 
*************************************

The Multi-EAR automatically connects to known wireless networks in range on boot.
If no known network is in range the Multi-EAR creates it's own wireless network with ``ssid=$HOSTNAME`` and ``passphrase=multi-ear``.

Checkout _raspberryconnect for the original `autohotspot` script!

.. _raspberryconnect: https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/158-raspberry-pi-auto-wifi-hotspot-switch-direct-connection

The Wi-Fi hotspot systemd .service is triggered on boot or when a new Wi-Fi network is added in the ctrl interface using `append_wpa_supplicant`.

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
