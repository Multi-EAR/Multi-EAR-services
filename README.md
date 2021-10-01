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

## Multi-EAR services
Multi-EAR services are installed in a Python3 virtual environment `(py37)` and are enabled via systemd system services.

Activate the virtual environment
```
source /home/tud/.py37/bin/activate
```

Check the status of the service, e.g.,
```
sudo systemctl status multi-ear-uart
```

Log files are generated per services in `/var/log/multi-ear/` and can be filtered in `journalctl` via .

### multi-ear-uart
Data collection and storage on the device.
Sensorboard serial readout via UART and storage in a local InfluxDB database.

## multi-ear-ctrl
Simplified control, monitoring, documentation and data visualization via a web browser.

## multi-ear-wifi
Simply switch between wireless access point mode (hotspot) or regular client mode to connect to an existing wireless network controlled via a bash script.
```
multi-ear-wifi --switch
```

Type `multi-ear-wifi --help` for the usage.
```
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
```

Wireless access point mode can be controlled via the web-service (see multi-ear-ctrl). 
Wireless access point mode can also be enabled by connecting [GPIO-7](https://pinout.xyz/pinout/pin26_gpio7) with ground.

## multi-ear-lora
Remote monitoring of the device via LoRa.

## Multi-ear-data
Data transmission to a central database.
