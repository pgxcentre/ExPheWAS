"""
Flask-based application for ExPheWAS.
"""

from flask import Blueprint, render_template, abort

from . import api


backend = Blueprint("backend_blueprint", __name__)


@backend.route("/outcome")
def get_outcomes():
    return render_template("outcome_list.html")


@backend.route("/outcome/<id>")
def get_outcome(id):
    try:
        outcome_data = api.get_outcome(id)
    except api.RessourceNotFoundError as exception:
        abort(404)
    return render_template("outcome.html", **outcome_data)


@backend.route("/gene")
def get_genes():
    return render_template("gene_list.html")


@backend.route("/gene/<ensg>")
def get_gene(ensg):
    try:
        gene_info = api.get_gene_by_ensembl_id(ensg)
    except api.RessourceNotFoundError as exception:
        abort(404)
    return render_template("gene.html", **gene_info)
