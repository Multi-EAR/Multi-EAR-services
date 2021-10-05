*************************************
Multi-EAR Services
*************************************

Multi-EAR system services for Raspberry Pi OS LITE (32-bit).


Installation
============

Install the Multi-EAR services on a deployed_ Raspberry Pi.
Make sure that the Raspberry Pi is connected to a wireless network with internet connection.

.. _deployed: https://github.com/Multi-EAR/Multi-EAR-deploy

Run the bash script to install and configure the Multi-EAR software and services.

.. code-block:: console

    bash install.sh

The device is now ready for Multi-EAR'ing.

Type ``bash install.sh --help`` for the usage.

.. code-block:: console

    Multi-EAR system services install on a deployed Raspberry Pi OS LITE (32-bit).
    Usage: install.sh [options] <install_step>

    Install step:
      all            Perform all of the following steps (default).
      packages       Install all required packages via apt.
      config         Configure all packages (make sure /etc is synced).
      python3        Create the Python3 virtual environment (py37) in /home/tud/.py37.
      multi-ear      Install and enable the Multi-EAR software in /home/tud/.py37.

    Options:
      --help, -h     Print help.
      --version, -v  Print version.

Usage
=====

Multi-EAR services are installed in a Python3 virtual environment ``(py37)``.

Activate the Python3 virtual environment

.. code-block:: console

    source /home/tud/.py37/bin/activate


Multi-EAR services
==================

- ``multi-ear-ctrl`` : local web service to control and monitor the device
- ``multi-ear-data`` : data transfer to the central database
- ``multi-ear-lora`` : remote monitoring of the device via LoRaWAN
- ``multi-ear-uart`` : sensorboard serial readout and local data storage
- ``multi-ear-wifi`` : wireless access point mode control with trigger via GPIO pin 7


Multi-EAR services are controlled and monitored via systemd system services.

Check the status of a service

.. code-block:: console

    sudo systemctl status multi-ear-uart

Log files are generated per services in ``/var/log/multi-ear/`` and can be filtered in ``journalctl``.
Check the ``multi-ear-uart`` system logs

.. code-block:: console

    journalctl -u multi-ear-uart.service --since yesterday --until now
