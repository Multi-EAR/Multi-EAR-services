from flask import Flask, render_template
from sys import version
import os
import subprocess
import socket
import json

app = Flask(__name__)

services = {
    'multi-ear-ctrl': {
        'name': 'Multi-EAR-CTRL',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'multi-ear-data': {
        'name': 'Multi-EAR-DATA',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'multi-ear-lora': {
        'name': 'Multi-EAR-LORA',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'multi-ear-uart': {
        'name': 'Multi-EAR-UART',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'multi-ear-wifi': {
        'name': 'Multi-EAR-WIFI',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'influxdb': {
        'name': 'InfluxDB',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'grafana': {
        'name': 'Grafana',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'telegraph': {
        'name': 'Telegraph',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'hostapd': {
        'name': 'hostapd',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
    'dnsmasq': {
        'name': 'dnsmasq',
        'info': '',
        'status': 'active (running)',
        'version': '0.0',
        'response': '...',
    },
}

@app.context_processor
def inject_stage_and_region():
    globs = dict(
        hostname=socket.gethostname(),
        version=version, services=services,
        wifi_hotspot_mode=True,
    )
    return globs


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


if __name__ == "__main__":
    app.run(debug=True)
