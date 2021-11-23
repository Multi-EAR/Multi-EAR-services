*************************************
Multi-EAR Services
*************************************

Multi-EAR system services and configuration for a deployed Raspberry Pi OS LITE (32-bit).


Installation
============

Install the Multi-EAR services on a deployed_ Raspberry Pi.
Make sure that the Raspberry Pi is connected to a wireless network with internet connection.

.. _deployed: https://github.com/Multi-EAR/Multi-EAR-deploy

Run the bash script to install and configure the Multi-EAR software and services.

.. code-block:: console

    bash multi-ear-services.sh install

The device is now ready for Multi-EAR'ing.

Type ``bash multi-ear-services.sh --help`` for the usage.

.. code-block:: console

    Multi-EAR Services setup on a deployed Raspberry Pi OS LITE (32-bit).
    Usage:
      multi-ear-services.sh [options] <action>
    Actions:
      install        Full installation of the Multi-Ear services:
                      * install Python3, dnsmasq, hostapd, nginx, influxdb, telegraf, grafana
                      * configure system services
                      * create Python3 virtual environment py37 in ~/.py37
                      * install and activate the Multi-EAR services
      check          Verify the installed Multi-EAR services and dependencies.
      update         Update the existing Multi-EAR services and dependencies.
      uninstall      Remove the installed Multi-EAR services, data, configurations and
                     the Python3 virtual environment.
    Options:
      --help, -h     Print help.
      --version, -v  Print version.

    multi-ear-services.sh only works on a Raspberry Pi platform.
    Environment variables $MULTI_EAR_ID and $MULTI_EAR_UUID should be defined in ~/.bashrc.

Usage
=====

Multi-EAR services are installed in a Python3 virtual environment ``(py37)``.

Activate the Python3 virtual environment

.. code-block:: console

    source ~/.py37/bin/activate


Services
========

- ``multi-ear-ctrl`` : local web service to access and monitor the device and data
- ``multi-ear-uart`` : sensorboard serial readout with local data storage and broadcast via websockets
- ``multi-ear-wifi`` : automatically generates a Wi-Fi hotspot when no known SSID is in range

Multi-EAR services are controlled and monitored via systemd_ system services.

.. _systemd: https://wiki.archlinux.org/title/Systemd#Using_units

Check the status of a service

.. code-block:: console

    systemctl status multi-ear-uart.service

Log files are generated per services in ``/var/log/multi-ear/`` and can be filtered in ``journalctl``.
Check the ``multi-ear-uart`` system logs

.. code-block:: console

    journalctl -u multi-ear-uart.service --since yesterday --until now

Licensing
=========

The source code for Multi-EAR-services is licensed under MIT that can be found under the LICENSE file.

This repository includes third-party software stored inside the lib directory. The code in this folder may be constrained by additional licenses and should be treated as such. The distribution of third-party software through this repository is warranted because of scientific reproducibility that cannot be guaranteed through a dynamic CDN.

Multi-EAR.org © 2021. All rights reserved.
