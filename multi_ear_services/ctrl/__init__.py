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


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

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

    # template globals
    @app.context_processor
    def inject_stage_and_region():
        hostapd = ('' if app.debug else '/') + 'etc/hostapd/hostapd.conf'
        return dict(
            hostname=socket.gethostname(),
            version=version,
            wireless_access_point=utils.is_wap_enabled(),
            services=utils.services,
            hostapd=dict(utils.parse_config(hostapd)['default']),
        )

    # routes
    @app.route("/")
    def index():
        return render_template('base.html.jinja')

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
        return jsonify(resp)

    @app.route("/_systemd_status", methods=['GET'])
    def systemd_status():
        service = request.args.get('service') or '*'
        if service == '*': 
            res = utils.systemd_status_all()
        else:
            res = utils.systemd_status(service)
        return jsonify(res)

    @app.route("/_wlan_access_point", methods=['POST'])
    def wlan_access_point():
        action = request.args.get('action')
        if action == 'status':
            res = utils.status_wap()
        elif action in ('on', 'enable', 'true'):
            res = utils.enable_wap()
        elif action in ('off', 'disable', 'false'):
            res = utils.disable_wap()
        else:
            res = None
        return jsonify(res)

    @app.route("/_wpa_supplicant", methods=['POST'])
    def wpa_supplicant():
        ssid = request.args.get('ssid')
        passphrase = request.args.get('passphrase')
        if ssid and passphrase:
            res = utils.wlan_ssid_passphrase(ssid, passphrase)
        else:
            res = None
        return jsonify(res)

    return app
