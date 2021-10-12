# absolute imports
import os
import subprocess
import configparser


services = ['multi-ear-ctrl.service',
            #  'multi-ear-data.service',
            #  'multi-ear-data.timer',
            #  'multi-ear-lora.service',
            #  'multi-ear-lora.timer',
            'multi-ear-uart.service',
            'multi-ear-wifi.service',
            'multi-ear-wifi.timer',
            'nginx.service',
            'influxdb.service',
            'grafana.service',
            'telegraph.service',
            'dnsmasq.service',
            'hostapd.service']


def is_raspberry_pi():
    """Checks if the device is a Rasperry Pi
    """
    if not os.path.exists('/proc/device-tree/model'):
        return False
    with open('/proc/device-tree/model') as f:
        model = f.read()
    return model.startswith('Raspberry Pi')


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
        response = rpopen(['/usr/bin/systemctl', 'status', service])
        if response['stdout'] and 'Active: ' in response['stdout']:
            status = response['stdout'].split('<br>')[2].split('Active: ')[1]
            if 'since' in status:
                status = status.split(' since ')[0]
        else:
            status = None
        return dict(
            service=service,
            status=status,
            **response,
        )


def systemd_status_all():
    """Get the systemd status of all services.
    """
    status = dict()
    for s in services:
        status[s] = systemd_status(s)
    return status


def wlan_ssid_passphrase(ssid: str, passphrase: str, method=None):
    """Add Wi-Fi ssid and passphrase and connect without rebooting.
    """
    if method == 'raspi-config':
        # Forces direct connection
        return rpopen(['/usr/bin/sudo', '/usr/bin/raspi-config', 'nonint',
                       'do_wifi_ssid_passphrase', ssid, passphrase])
    else:
        return rpopen(['/usr/bin/wpa_passphrase', ssid, passphrase, '|',
                       '/usr/bin/sed', '3d;2i\        scan_ssid=1', '|',
                       '/usr/bin/sed', '1i\\', '|',
                       '/usr/bin/sudo', '/usr/bin/tee', '-a',
                       '/etc/wpa_supplicant/wpa_supplicant.conf'])


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
