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
    "our_uniprot": "https://www.uniprot.org/uniprot/{id}",
    "HGNC": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:{id}",
}

EXTERNAL_DB_TO_SHOW = ("HGNC", "WikiGene", "MIM_GENE", "MIM_MORBID", "our_uniprot")


@backend.route("/outcome")
def get_outcomes():
    return render_template("outcome_list.html", page_title="outcomes")


@backend.route("/outcome/<id>")
def get_outcome(id):
    try:
        outcome_data = api.get_outcome(id)
    except api.RessourceNotFoundError as exception:
        abort(404)
    return render_template(
        "outcome.html",
        page_title=f"outcome {id}",
        **outcome_data,
    )


@backend.route("/gene")
def get_genes():
    return render_template("gene_list.html", page_title="genes")


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

    # Adding the available variance results
    available_variance = api.get_gene_available_variance(ensg)
    available_variance = available_variance["available_variance"]

    # Checking if there are any GTEx data
    has_gtex = len(api.get_gene_gtex(ensg)) > 0

    return render_template(
        "gene.html",
        page_title=f"{ensg} | {gene_info['variance_pct']}%",
        **gene_info,
        available_variance=available_variance,
        xrefs=xrefs,
        has_gtex=has_gtex,
        db_full_names=db_names,
        db_urls=EXTERNAL_DB_URL,
        external_dbs=EXTERNAL_DB_TO_SHOW,
    )
