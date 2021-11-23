*************************************
Multi-EAR services - UART
*************************************

Sensorboard serial readout via UART with data storage in a local InfluxDB database
and broadcast via websockets.

Service
=======

:Service:
    multi-ear-uart.service
:ExecStart:
    /home/tud/.py37/bin/multi-ear-uart
:Restart:
    always
:SyslogIdentifier:
    multi-ear-uart
:Log:
    /var/log/multi-ear/uart.log

Usage
=====

Command line
------------

You can manually start the sensorboard serial readout script for testing purposes.

.. code-block:: console
 
    multi-ear-uart

Make sure that the systemd service is stopped as only one serial connection to the sensorboard is possible over UART.

.. code-block:: console

    sudo systemctl status multi-ear-uart

Stop the service.

.. code-block:: console

    sudo systemctl stop multi-ear-uart

Python
------

.. code-block:: python3

    from multi_ear_services.uart import serial_readout
    serial_readout()
