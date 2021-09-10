 #!/opt/py37/bin/python3

from flask import Flask, render_template
from sys import version
import os

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello uWSGI from python version: <br>" + version


@app.route("/status")
def status():
    output = os.popen('/usr/bin/systemctl status multi-ear-uart').read().strip()
    output = "<br>".join(output.split("\n"))
    return "service multi-ear-uart status: <br><br>" + output


if __name__ == "__main__":
    app.run()

# application = app
