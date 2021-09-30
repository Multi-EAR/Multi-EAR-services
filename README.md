# Multi-EAR-Software

Multi-EAR software install on a deployed Raspberry Pi OS LITE (32-bit).

## Install
Make sure that the Raspberry Pi is connected to a wireless network with internet connection.

Run the bash script install the Multi-EAR software.
```
bash install.sh
```

Type `bash install.sh --help` for the usage.
```
Multi-EAR software install on a deployed Raspberry Pi OS LITE (32-bit).
Usage: install.sh [options] <install_step>

Install step:
  all            Perform all of the following steps (default).
  packages       Install all required packages via apt.
  etc            Sync /etc for all packages.
  config         Configure all packages (make sure /etc is synced).
  python3        Create the Python3 virtual environment (py37) in /home/tud/.py37.
  gpio-watch     Install gpio-watch in /home/tud/.py37.
  multi-ear      Install and enable the Multi-EAR software in /home/tud/.py37.

Options:
  --help, -h     Print help.
  --version, -v  Print version.
```

