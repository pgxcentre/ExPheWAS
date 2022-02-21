"""Loads the different blueprints and creates the Flask application."""


import os
from binascii import hexlify

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from .. import __version__

from .config import URL_ROOT, STATIC_FOLDER
from .api import api as api_blueprint
from .cache import create_or_load_startup_caches
from .backend import backend as backend_blueprint
from .backend import inject_db_metadata
from .dt_api import dt_api as dt_api_blueprint

from ..db.engine import Session


# Build the cache if needed.
create_or_load_startup_caches()


app = Flask(
    __name__,
    static_url_path=URL_ROOT.rstrip("/") + "/dist",
    static_folder=STATIC_FOLDER,
)

app.config["SECRET_KEY"] = hexlify(os.urandom(24))
app.config["EXPHEWAS_VERSION"] = __version__

CORS(app)


# Adding the blueprints
app.register_blueprint(api_blueprint, url_prefix=URL_ROOT.rstrip("/") + "/api")
app.register_blueprint(backend_blueprint, url_prefix=URL_ROOT)
app.register_blueprint(dt_api_blueprint,
                       url_prefix=URL_ROOT.rstrip("/") + "/dt")

@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()


@app.errorhandler(404)
def page_not_found(error):
    """Handles page not found error."""
    if request.path.startswith("/api/"):
        return jsonify({
            "error": 404,
            "message": "The requested API endpoint was not found on the "
                       "server.",

        }), 404

    return render_template(
        "404.html", page_title="Page not found", **inject_db_metadata(),
    ), 404
