*************************************
multi_ear_services 
*************************************

Multi-EAR system services for the host Raspberry Pi OS LITE (32-bit) with sensorboard.


Installation
============

Installation of the Python module is included in the ``install.sh`` script.
Manual installation of the Python module

.. code-block:: console

    pip install .

Make sure the Raspberry Pi is deployed with pre-installed packages and the configured Python3 virtual environment ``(py37)``.

Python module
==================

Import the python module

.. code-block:: python3

    import multi_ear_services


Versioning is obtained via git.

.. code-block:: python3

    print(multi_ear_services.__version__)


Entry-points
==================

- ``multi-ear-ctrl`` : local web service to control and monitor the device
- ``multi-ear-data`` : data transfer to the central database
- ``multi-ear-lora`` : remote monitoring of the device via LoRaWAN
- ``multi-ear-uart`` : sensorboard serial readout and local data storage


Scripts
==================

- ``multi-ear-wifi`` : wireless access point mode control with trigger via GPIO pin 7
