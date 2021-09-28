from flask import Flask, render_template
from sys import version
import os
import subprocess
import socket
import configparser
import json
import argparse

app = Flask(__name__)


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

def _parse_config(config_path: str, **kwargs):
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


def _systemd_status(service: str):
    """Get the systemd status of a single service.
    """
    if service not in _services:
        return dict(
            success=False,
            service=service,
            response='Service not part of listed Multi-EAR services.',
        )
    else:
        return dict(
            success=False,
            service=service,
            response=rpopen(['/usr/bin/systemctl', 'status', service]),
        )


def _systemd_status_all():
    """Get the systemd status of all services.
    """
    status = dict()
    for s in _services:
        status[s] = _systemd_status(s)
    return status
    

@app.context_processor
def inject_stage_and_region():
    hostapd = ('' if app.debug else '/') + 'etc/hostapd/hostapd.conf'
    print(hostapd)
    return dict(
        hostname=socket.gethostname(),
        version=version,
        wireless_access_point=True,
        services=services,
        hostapd=dict(_parse_config(hostapd)['default']),
    )


@app.route("/")
# @app.route("/index")
def index():
    return render_template('base.html.jinja')


# all api relalted stuff
def rpopen(*args, **kwargs):
    """Wraps subprocess.Popen in a catch error statement. 
    """

    # subprocess command
    try:
        p = subprocess.Popen(*args, **kwargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return {
            "success": False,
            "returncode": None,
            "stdout": None,
            "stderr": None,
        }

    # wait for process to finish; this also sets the returncode variable inside 'p'
    stdout, stderr = p.communicate()

    # construct return dict
    result = {
        "success": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": "<br>".join(stdout.decode("utf-8").split("\n")),
        "stderr": "<br>".join(stderr.decode("utf-8").split("\n")),
    }

    return result


@app.route("/_tab/<tab>")
def load_tab(tab="home"):
    try:
        html = render_template(f"tabs/{tab}.html.jinja")
    except FileNotFoundError:
        html = None
    resp = {
        "succes": True if html else False,
        "tab": tab,
        "html": html,
    }
    return json.dumps(resp, indent=4)
 

@app.route("/_status/<service>")
def api_status(service=""):
    res = rpopen(['/usr/bin/systemctl', 'status', service])
    res["service"] = service
    res["status"] = service.contains("active")
    return json.dumps(resp, indent=4)


@app.route("/_status_list")
def api_status_all():
    # res = rpopen(['/usr/bin/systemctl', 'status', service])
    # res["service"] = service
    # res["status"] = service.contains("active")
    return json.dumps(services, indent=4)


@app.route("/_switch_wifi_mode")
def switch_wifi_mode():
    res = rpopen(['ping', '-c', '4', 'www.google.com'])
    return json.dumps(res, indent=4)


def main():
    parser = argparse.ArgumentParser(
        prog='multi-ear-ctrl',
        description=('Multi-EAR CTRL web service.'),
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Enable debug mode (auto re-loaded resources).'
    )
    args = parser.parse_args()
    app.run(debug=args.debug)

if __name__ == "__main__":
    main()
