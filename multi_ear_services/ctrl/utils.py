# absolute imports
import os
from subprocess import Popen, PIPE


services = ['multi-ear-ctrl.service',
            #  'multi-ear-data.service',
            #  'multi-ear-data.timer',
            #  'multi-ear-lora.service',
            #  'multi-ear-lora.timer',
            'multi-ear-uart.service',
            'multi-ear-wifi.service',
            #  'multi-ear-wifi.timer',
            'nginx.service',
            'influxdb.service',
            'telegraf.service',
            'grafana-server.service',
            'dnsmasq.service',
            'hostapd.service']


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
        r = _popen(['/usr/bin/systemctl', 'status', service])
        if r['stdout'] and 'Active: ' in r['stdout']:
            status = r['stdout'].split('<br>')[2].split('Active: ')[1]
            if 'since' in status:
                status = status.split(' since ')[0]
        else:
            status = None
        return dict(
            service=service,
            status=status,
            **r,
        )


def systemd_status_all():
    """Get the systemd status of all services.
    """
    status = dict()
    for s in services:
        status[s] = systemd_status(s)
    return status


def wlan_ssid_passphrase(ssid: str, passphrase: str):
    """Add Wi-Fi ssid and passphrase to wpa_supplicant and connect.
    """
    return _popen(['/home/tud/.py37/bin/append_wpa_supplicant',
                   ssid, passphrase])


def wlan_autohotspot():
    """Run autohotspot.
    """
    return _popen(['/usr/bin/sudo', '/usr/bin/systemctl',
                   'start', 'multi-ear-wifi'])


def _popen(*args, **kwargs):

    """Wraps Popen and Popen.communicate() in a catch error statement and
    returns a serialized dictionary object for jsonify.
    """
    def _resp(**kwargs):
        r = {
            'success': False,
            'returncode': None,
            'stdout': None,
            'stderr': None,
            **kwargs,
        }
        return r

    try:
        p = Popen(*args, **kwargs, stdout=PIPE, stderr=PIPE)
    except OSError:
        return _resp()

    try:
        # wait for process to finish;
        # this also sets the returncode variable inside 'p'
        stdout, stderr = p.communicate()

        # construct return dict
        r = _resp(
            success=p.returncode == 0,
            returncode=p.returncode,
            stdout="<br>".join(stdout.decode("utf-8").split("\n")),
            stderr="<br>".join(stderr.decode("utf-8").split("\n")),
        )
    except OSError as e:
        r = _resp(returncode=e.errno, stderr=e.strerror)
    except Exception:
        r = _resp()

    return r
