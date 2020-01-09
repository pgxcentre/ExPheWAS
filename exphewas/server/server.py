"""
Flask-based application for ExPheWAS.
"""

from flask import Blueprint, render_template, abort

from . import api


server = Blueprint("server_blueprint", __name__)


@server.route("/outcome")
def get_outcomes():
    return render_template("outcome_list.html")


@server.route("/outcome/<id>")
def get_outcome(id):
    try:
        outcome_data = api.get_outcome(id)
    except api.RessourceNotFoundError as exception:
        abort(404)
    return render_template("outcome.html", **outcome_data)
