# Multi-EAR-Software

Software setup of the Raspberry Pi.

## Install

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
  multi_ear      Install and enable the Multi-EAR modules and services.

Options:
  --help, -h     Print help.
  --version, -v  Print version.
```

