"""
Flask-based application for ExPheWAS.
"""

from collections import defaultdict

from flask import Blueprint, render_template, abort

from . import api


backend = Blueprint("backend_blueprint", __name__)

EXTERNAL_DB_URL = {
    "WikiGene": "https://www.wikigenes.org/e/gene/e/{id}.html",
    "MIM_GENE": "https://omim.org/entry/{id}",
    "MIM_MORBID": "https://omim.org/entry/{id}",
}

EXTERNAL_DB_TO_SHOW = ("WikiGene", "MIM_GENE", "MIM_MORBID")


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

    # Adding the cross references
    xrefs = defaultdict(list)
    db_names = {}
    for xref in api.get_gene_xrefs(ensg):
        db_names[xref["db_id"]] = xref["db_description"]
        xrefs[xref["db_id"]].append(xref["external_id"])

    return render_template("gene.html", **gene_info, xrefs=xrefs,
                           db_names=db_names, db_urls=EXTERNAL_DB_URL,
                           external_dbs=EXTERNAL_DB_TO_SHOW)
