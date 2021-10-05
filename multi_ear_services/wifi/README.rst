*************************************
multi-ear-wifi
*************************************

Wireless access point mode control with trigger via GPIO pin 7.
Simply switch between wireless access point mode (hotspot) or regular client mode to connect to an existing wireless network.

.. code-block:: console

    multi-ear-wifi --switch

Type ``multi-ear-wifi --help`` for the usage

.. code-block:: console

    Multi-EAR Wi-Fi access point mode control.
    Usage: multi-ear-wifi [options] <action>

    Actions:
      --status       Returns if wireless access point mode is enabled.
      --on           Enable wireless access point mode (host mode).
      --off          Disable wireless access point mode (client mode).
      --switch       Switch between wireless access point mode.

    Options:
      --help, -h     Print help.
      --version, -v  Print version.

The wireless access point mode can be controlled via the web service (see `multi-ear-ctrl`) and can be enabled by connecting GPIO-7_ with ground.

.. _GPIO-7: https://pinout.xyz/pinout/pin26_gpio7

GPIO pin monitoring is obtained via ``gpio-watch``

:Service:
    multi-ear-wifi.service
:ExecStart:
    /home/tud/.py37/bin/gpio-watch -v -e rising 7
:Restart:
    on-fail
:SyslogIdentifier:
    multi-ear-wifi
:Log:
    /var/log/multi-ear/wifi.log

The executed script for GPIO-7 is

.. code-block:: console

    multi-ear-wifi --enable
