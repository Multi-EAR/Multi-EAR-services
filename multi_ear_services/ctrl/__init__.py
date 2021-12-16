# absolute imports
import os
import socket
import hashlib
from flask import Flask, Response, jsonify, request, render_template
from flask_cors import CORS
from influxdb_client import InfluxDBClient

# relative imports
try:
    from ..version import version
except ModuleNotFoundError:
    version = '[VERSION-NOT-FOUND]'
from . import utils
from ..util import DataSelect, is_raspberry_pi, parse_config


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # set cross-origin resource sharing
    CORS(app, resources=r'/api/*')

    # check if host is a Raspberry Pi
    is_rpi = is_raspberry_pi()

    # open influx connection
    db_client = InfluxDBClient(url="http://127.0.0.1:8086",
                               token="ear:listener", org="-")

    # set hostname and referers
    hostname = socket.gethostname()
    referers = ("http://127.0.0.1", f"http://{hostname.lower()}")

    # hostapd config
    etc = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '../../etc') if app.debug else '/etc'
    hostapd = parse_config(os.path.join(etc, 'hostapd', 'hostapd.conf'))

    # wifi secret
    wifi_secret = hashlib.sha256(
        bytes(os.environ.get('MULTI_EAR_WIFI_SECRET') or 'albatross', 'utf-8')
    ).hexdigest()

    # prepare template globals
    context_globals = dict(
        hostname=hostname.replace('.local',''),
        version=version,
        services=utils.services,
        hostapd=dict(hostapd.items('DEFAULT')),
    )

    # inject template globals
    @app.context_processor
    def inject_stage_and_region():
        return context_globals

    # quick check for an internal request
    def is_internal_referer():
        if 'Referer' not in request.headers:
            return False
        return any(r in request.headers['Referer'] for r in referers)

    # routes
    @app.route("/", methods=['GET'])
    def index():
        return render_template('base.html.jinja')

    @app.route("/_tab/<tab>", methods=['GET'])
    def load_tab(tab="home"):

        if not is_internal_referer():
            return "Invalid request", 400

        try:
            html = render_template(f"tabs/{tab}.html.jinja")
        except FileNotFoundError:
            return f"Tab {tab} not found", 404
        except Exception as e:
            return f"Server Error: {e}", 500

        resp = {
            "succes": True,
            "tab": tab,
            "html": html,
        }
        return jsonify(resp), 200

    @app.route("/_systemd_status", methods=['GET'])
    def systemd_status():

        if not is_rpi:
            return "I'm not Raspberry Pi", 418

        service = request.args.get('service') or '*'
        if service == '*': 
            resp = utils.systemd_status_all()
        else:
            resp = utils.systemd_status(service)

        return jsonify(resp), 200

    @app.route("/_append_wpa_supplicant", methods=['POST'])
    def append_wpa_supplicant():

        if not is_internal_referer():
            return "Invalid request", 403

        if not is_rpi:
            return "I'm not Raspberry Pi", 418

        secret = request.args.get('secret')
        if secret != wifi_secret:
            return "Secret invalid", 403

        ssid = request.args.get('ssid')
        passphrase = request.args.get('passphrase')
        if not (ssid and passphrase):
            return "Invalid ssid and/or passphrase arguments", 400
        
        resp = utils.wlan_ssid_passphrase(ssid, passphrase)

        return jsonify(resp), 200

    @app.route("/_autohotspot", methods=['POST'])
    def autohotspot():

        if not is_internal_referer():
            return "Invalid request", 403

        if not is_rpi:
            return "I'm not Raspberry Pi", 418

        secret = request.args.get('secret')
        if secret != wifi_secret:
            return "Secret invalid", 403
        
        resp = utils.wlan_autohotspot()

        return jsonify(resp), 200


    @app.route("/api/dataselect/health", methods=['GET'])
    def api_dataselect_health():
        return repr(db_client.health()), 200

    @app.route("/api/dataselect/query", methods=['GET', 'POST'])
    def api_dataselect_query():
        ds = DataSelect(
            db_client,
            starttime=(request.args.get('starttime') or
                       request.args.get('start') or
                       request.args.get('s')),
            endtime=(request.args.get('endtime') or
                     request.args.get('end') or
                     request.args.get('e')),
            database=(request.args.get('database') or
                      request.args.get('db') or
                      request.args.get('d')),
            measurement=request.args.get('measurement') or request.args.get('m'),
            field=request.args.get('field') or request.args.get('f'),
            format=request.args.get('format') or request.args.get('_f'),
            nodata=request.args.get('nodata') or request.args.get('_n'),
        )
        return ds.response()

    return app
