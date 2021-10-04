*************************************
Multi-EAR Services
*************************************

Multi-EAR system services for Raspberry Pi OS LITE (32-bit).


Installation
============

Install the Multi-EAR services on a [deployed](https://github.com/Multi-EAR/Multi-EAR-deploy) Raspberry Pi.
Make sure that the Raspberry Pi is connected to a wireless network with internet connection.

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


Multi-EAR services
==================

- **ctrl** : local web service to control and monitor the device
- **data** : data transmission to the central database
- **lora** : remote monitoring of the device
- **uart** : continuous data readout, buffering and local storage
- **wifi** : enable/disable wireless access point mode


Multi-EAR services are installed in a Python3 virtual environment ``(py37)``.

Activate the Python3 virtual environment

.. code-block:: console

    source /home/tud/.py37/bin/activate


Multi-EAR services are controlled and monitored via systemd system services.

Check the status of a service

.. code-block:: console

    sudo systemctl status multi-ear-uart

Log files are generated per services in ``/var/log/multi-ear/`` and can be filtered in ``journalctl``.
Check the ``multi-ear-uart`` system logs

.. code-block:: console

    journalctl -u multi-ear-uart.service --since yesterday --until now


multi-ear-uart
--------------
Data collection and storage on the device.
Sensorboard serial readout via UART with data storage in a local InfluxDB database.

You can manually start the sensorboard serial readout for testing purposes.

.. code-block:: console
 
    multi-ear-uart

Make sure that the systemd service is stopped as only one serial connection to the sensorboard is possible.

.. code-block:: console

    sudo systemctl stop multi-ear-uart


multi-ear-ctrl
--------------
Simplified control, monitoring, documentation and data visualization via a web browser.

The web-service is started automatically via the ``multi-ear-ctrl.service`` in ``/etc/systemd/system`` via a ``uwsgi`` socket handled via ``nginx`` on the default http port 80.

You can also manually start the web-service on `http://127.0.0.1:5000`_.

First check if the Flask environment variables are set correctly.

.. code-block:: console

    echo $FLASK_APP  # should be multi_ear_services.ctrl
    echo $FLASK_ENV  # should be production (default) or development

If not set in ``.bashrc`` or incorrect

.. code-block:: console

    export FLASK_ENV=development
    export FLASK_APP=multi_ear_services.ctrl

Start the web-service

.. code-block:: console

    flask run


multi-ear-wifi
--------------

Simply switch between wireless access point mode (hotspot) or regular client mode to connect to an existing wireless network controlled via a bash script.

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

The wireless access point mode can be controlled via the web-service (see multi-ear-ctrl) and ca be enabled by connecting GPIO-7_ with ground.

.. _GPIO-7: https://pinout.xyz/pinout/pin26_gpio7


multi-ear-lora
--------------

Remote monitoring of the Multi-EAR device via LoRa.


multi-ear-data
--------------

Data transmission of the Multi-EAR to a central database.
