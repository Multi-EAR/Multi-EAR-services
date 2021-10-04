*************************************
multi-ear-uart
*************************************

Sensorboard serial readout via UART with data storage in a local InfluxDB database.

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

You can manually start the sensorboard serial readout script for testing purposes.

.. code-block:: console
 
    multi-ear-uart

Make sure that the systemd service is stopped as only one serial connection to the sensorboard is possible.

.. code-block:: console

    sudo systemctl stop multi-ear-uart
