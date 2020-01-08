"""
Flask-based application for ExPheWAS.
"""

from flask import Blueprint, render_template

from . import api


server = Blueprint("server_blueprint", __name__)


@server.route("/outcome")
def get_outcomes():
    return render_template("outcome_list.html")


@server.route("/outcome/<id>")
def get_outcome(id):
    outcome_data = api.get_outcome(id)
    return render_template("outcome.html", **outcome_data)
