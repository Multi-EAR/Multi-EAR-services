# Multi-EAR

The Multi-EAR is a mobile low-cost multidisciplinary sensor platform for scientific monitoring of the earth and atmosphere. The low-cost platform uses digital Micro­electromechanical Systems (MEMS) sensors embedded on a Printed Circuit Board (PCB). The Multi-EAR extends the INFRA-EAR, a sensor platform for monitoring geophysical parameters designed to fit a Wandering Albatross.

## Installation
Install the Multi-EAR software on a deployed Raspberry Pi OS LITE (32-bit).
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

The Multi-EAR software contains all essential modules and services: data collection and storage, web-services for documentation and data visualization and services for remote monitoring and data transmission.

## Local Web-Serices

Browse to the devive IPv4 address for the local web-services (`192.168.128.1` in Wi-Fi access point mode).

# Documentation #sensors

# Data visualization #dashboard

# Simplified Wi-Fi control #wifi

Enable Wi-Fi access point mode (via the web-service to let the device broadcast it's own network.
The network SSID name shall be the device name with WPA2 passphrase `multi-ear`.
The device IPv4 address shall be `192.168.128.1`.
Wireless access point mode can also be enabled by connecting [GPIO 7 #PIN-26](https://pinout.xyz/pinout/pin26_gpio7) with ground #PIN-25.

When Wi-Fi access point mode is disabled the device will automatilly connect to known wireless networks.
Enter the name and passphrase to add a network to the Raspberry Pi's `wpa_supplicant` list.

# Multi-EAR service monitoring #status

Monitoring of the Multi-EAR related services
