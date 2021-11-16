# absolute imports
import os
import socket
from flask import Flask, jsonify, request, render_template

# relative imports
try:
    from ..version import version
except ModuleNotFoundError:
    version = '[VERSION-NOT-FOUND]'
from . import utils
from ..util import is_raspberry_pi, parse_config, DataSelect


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

    # check if host is a Raspberry Pi
    is_rpi = is_raspberry_pi()

    # template globals
    @app.context_processor
    def inject_stage_and_region():
        etc = os.path.dirname(os.path.abspath(__file__)) + '/../../etc' if app.debug else '/etc'
        hostapd = parse_config(etc + '/hostapd/hostapd.conf')
        return dict(
            hostname=socket.gethostname().replace('.local',''),
            version=version,
            services=utils.services,
            hostapd=dict(hostapd.items('DEFAULT')),
        )

    #
    def is_internal_request():
        return ('Referer' in request.headers and
                'http://127.0.0.1' in request.headers['Referer'])

    # routes
    @app.route("/", methods=['GET'])
    def index():
        return render_template('base.html.jinja')

    @app.route("/_tab/<tab>", methods=['GET'])
    def load_tab(tab="home"):
        if not is_internal_request():
            return "Invalid request", 400
        try:
            html = render_template(f"tabs/{tab}.html.jinja")
        except FileNotFoundError:
            html = None
        res = {
            "succes": True if html else False,
            "tab": tab,
            "html": html,
        }
        return jsonify(res)

    @app.route("/_systemd_status", methods=['GET'])
    def systemd_status():
        service = request.args.get('service') or '*'
        if is_rpi:
            if is_rpi and service == '*': 
                res = utils.systemd_status_all()
            else:
                res = utils.systemd_status(service)
        else:
             res = None
        return jsonify(res)

    @app.route("/_append_wpa_supplicant", methods=['POST'])
    def append_wpa_supplicant():
        if not is_internal_request():
            return "Invalid request", 400
        ssid = request.args.get('ssid')
        passphrase = request.args.get('passphrase')
        if is_rpi and ssid and passphrase:
            res = utils.wlan_ssid_passphrase(ssid, passphrase)
        else:
            res = None
        return jsonify(res)

    @app.route("/_autohotspot", methods=['POST'])
    def autohotspot():
        if not is_internal_request():
            return "Invalid request", 400
        command = request.args.get('action')
        if is_rpi and command == 'start':
            res = utils.wlan_autohotspot()
        else:
            res = None
        return jsonify(res)

    @app.route("/api/dataselect", methods=['GET'])
    def api_dataselect():
        data = DataSelect(
            starttime=request.args.get('start') or request.args.get('starttime'),
            endtime=request.args.get('end') or request.args.get('endtime'),
            channel=request.args.get('chan') or request.args.get('channel'),
            format=request.args.get('format'),
            nodata=request.args.get('nodata'),
        )

        return jsonify(str(data))

    return app
