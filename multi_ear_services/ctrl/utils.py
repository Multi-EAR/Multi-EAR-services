# absolute imports
import subprocess
import configparser


services = ['multi-ear-ctrl',
            'multi-ear-data',
            'multi-ear-lora',
            'multi-ear-uart',
            'multi-ear-wifi',
            'influxdb',
            'grafana',
            'telegraph',
            'hostapd',
            'dnsmasq']


def parse_config(config_path: str, **kwargs):
    """
    """
    config = configparser.ConfigParser(**kwargs)
    try:
        config.read(config_path)
    except configparser.MissingSectionHeaderError:
        with open(config_path, 'r') as f:
            config_string = '[default]\n' + f.read()
            config = configparser.ConfigParser()
            config.read_string(config_string)
    return config


def systemd_status(service: str):
    """Get the systemd status of a single service.
    """
    if service not in services:
        return dict(
            success=False,
            service=service,
            stderr='Service not part of listed Multi-EAR services.',
        )
    else:
        return dict(
            service=service,
            **rpopen(['/usr/bin/systemctl', 'status', service]),
        )


def systemd_status_all():
    """Get the systemd status of all services.
    """
    status = dict()
    for s in services:
        status[s] = systemd_status(s)
    return status


def rpopen(*args, **kwargs):
    """Wraps subprocess.Popen in a catch error statement.
    """

    # subprocess command
    try:
        p = subprocess.Popen(
            *args, **kwargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError:
        return {
            "success": False,
            "returncode": None,
            "stdout": None,
            "stderr": None,
        }

    # wait for process to finish;
    # this also sets the returncode variable inside 'p'
    stdout, stderr = p.communicate()

    # construct return dict
    r = dict(
        success=p.returncode == 0,
        returncode=p.returncode,
        stdout="<br>".join(stdout.decode("utf-8").split("\n")),
        stderr="<br>".join(stderr.decode("utf-8").split("\n")),
    )

    return r
