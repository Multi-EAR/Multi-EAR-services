# absolute imports
import subprocess
import configparser


services = ['multi-ear-ctrl',
            #  'multi-ear-data',
            #  'multi-ear-lora',
            'multi-ear-uart',
            'multi-ear-wifi',
            'influxdb',
            'grafana',
            'telegraph',
            'nginx',
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


def is_wap_enabled():
    """Returns True if wireless access point mode is enabled.
    """
    response = status_wap()
    if not response['success'] or response['stdout'] is None:
        return
    return response['stdout'].lower() == 'true'


def status_wap():
    """Returns True if wireless access point mode is enabled.
    """
    return rpopen(['/home/tud/.py37/bin/multi-ear-wifi', '--status'])


def enable_wap():
    """Enable wireless access point mode.
    """
    return rpopen(['/home/tud/.py37/bin/multi-ear-wifi', '--on'])


def disable_wap():
    """Disable wireless access point mode.
    """
    return rpopen(['/home/tud/.py37/bin/multi-ear-wifi', '--off'])


def wlan_ssid_passphrase(ssid: str, passphrase: str, method='raspi-config'):
    """Add Wi-Fi ssid and passphrase and connect without rebooting.
    """
    # disable_wap()
    if method == 'raspi-config':
        return rpopen(['/usr/bin/sudo', '/usr/bin/raspi-config', 'nonint',
                       'do_wifi_ssid_passphrase', ssid, passphrase])
    else:
        return rpopen([
            '/usr/bin/wpa_passphrase', ssid, passphrase, '|',
            '/usr/bin/sed', '3d', '|', '/usr/bin/sudo', '/usr/bin/tee',
            '-a', '/etc/wpa_supplicant/wpa_supplicant.conf'
        ])


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
