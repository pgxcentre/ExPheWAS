"""Loads the different blueprints and creates the Flask application."""


from os import path

from flask import Flask, jsonify
from flask_cors import CORS

from .api import api as api_blueprint
from .server import server as server_blueprint

from ..db.engine import Session


app = Flask(
    __name__,
    static_folder=path.join(
        path.dirname(__file__), "..", "..", "frontend", "dist",
    ),
)
CORS(app)


# Adding the blueprints
app.register_blueprint(api_blueprint)
app.register_blueprint(server_blueprint)


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()
