"""Loads the different blueprints and creates the Flask application."""


import os
from os import path
from binascii import hexlify

from flask import Flask
from flask_cors import CORS

from werkzeug.wsgi import DispatcherMiddleware

from .api import api as api_blueprint
from .backend import backend as backend_blueprint

from ..db.engine import Session


URL_ROOT = os.environ.get("EXPHEWAS_URL_ROOT", "/")


app = Flask(
    __name__,
    static_url_path=URL_ROOT.rstrip("/") + "/dist",
    static_folder=path.join(
        path.dirname(__file__), "..", "..", "frontend", "dist",
    ),
)

app.config["SECRET_KEY"] = hexlify(os.urandom(24))

CORS(app)


# Adding the blueprints
app.register_blueprint(api_blueprint, url_prefix=URL_ROOT.rstrip("/") + "/api")
app.register_blueprint(backend_blueprint, url_prefix=URL_ROOT)


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()
