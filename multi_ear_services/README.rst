*************************************
Multi-EAR services 
*************************************

Multi-EAR system services for the host Raspberry Pi OS LITE (32-bit) with sensorboard.

Installation
============

Installation of the Python module is included in the ``multi-ear-services.sh`` script.
Manual installation of the Python module via ``pip``

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
============

- ``multi-ear-ctrl`` : local web service to access and monitor the device and data
- ``multi-ear-lora`` : remote monitoring of the device via LoRaWAN
- ``multi-ear-sync`` : data transfer to the central database
- ``multi-ear-uart`` : sensorboard serial readout with local data storage and broadcast via websockets

Scripts
=======

- ``autohotspot`` : automatically generates an wlan hotspot when no a valid ssid is in range
- ``append_wpa_supplicant`` : append a new network with encrypted PSK to wpa_supplicants
