# Multi-EAR Services

Multi-EAR system services for Raspberry Pi OS LITE (32-bit).

## Installation
Install the Multi-EAR services on a [deployed](https://github.com/Multi-EAR/Multi-EAR-deploy) Raspberry Pi.
Make sure that the Raspberry Pi is connected to a wireless network with internet connection.

Run the bash script to install and configure the Multi-EAR software and services.
```
bash install.sh
```
The device is now ready for Multi-EAR'ing.


Type `bash install.sh --help` for the usage.
```
Multi-EAR software install on a deployed Raspberry Pi OS LITE (32-bit).
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
```

## Getting started

The Multi-EAR services provide:
- multi-ear-uart: data collection and storage on the device.
- multi-ear-ctrl: simplified control, monitoring, documentation and data visualization via a web browser.
- multi-ear-wifi: enable wireless access point mode by connecting [GPIO-7](https://pinout.xyz/pinout/pin26_gpio7) with ground.
- multi-ear-lora: remote monitoring of the device via LoRa.
- multi-ear-data: data transmission to a central database.
