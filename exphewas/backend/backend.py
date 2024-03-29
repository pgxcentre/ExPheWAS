"""
Flask-based application for ExPheWAS.
"""

import os
from collections import defaultdict

from sqlalchemy.orm.exc import NoResultFound
from flask import Blueprint, render_template, abort, url_for

from . import api
from ..version import exphewas_version
from ..db import models
from ..db.engine import Session


backend = Blueprint(
    "backend_blueprint",
    __name__,
    static_url_path="/backend_static/",
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)

EXTERNAL_DB_URL = {
    "WikiGene": "https://www.wikigenes.org/e/gene/e/{id}.html",
    "MIM_GENE": "https://omim.org/entry/{id}",
    "MIM_MORBID": "https://omim.org/entry/{id}",
    "our_uniprot": "https://www.uniprot.org/uniprot/{id}",
    "HGNC": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:{id}",
}

EXTERNAL_DB_TO_SHOW = ("HGNC", "WikiGene", "MIM_GENE", "MIM_MORBID",
                       "our_uniprot")

@backend.context_processor
def inject_db_metadata():
    metadata = {
        "exphewas_version": exphewas_version,
        "db": {}
    }

    try:
        metadata["db"] = Session.query(models.Metadata).one().metadata_dict()
    except NoResultFound:
        pass

    return {"meta": metadata}


@backend.route("/")
def get_index():
    return render_template("index.html", page_title="Home")


@backend.route("/docs")
def get_docs():
    # Infer api root
    api_root = url_for("api_blueprint.get_metadata", _external=True)
    api_root = "/".join(api_root.split("/")[:-1])

    return render_template(
        "docs.html",
        page_title="Documentation",
        full_api_url=api_root
    )


@backend.route("/outcome")
def get_outcomes():
    return render_template("outcome_list.html", page_title="Phenotypes")


@backend.route("/outcome/<id>")
def get_outcome(id):
    try:
        outcome_data = api.get_outcome(id)
    except api.RessourceNotFoundError as exception:
        abort(404)

    # Checks if there are enrichment results for this outcome
    enrichment_result = Session.query(models.Enrichment)\
        .filter_by(hierarchy_id="ATC")\
        .filter_by(outcome_id=id)\
        .first()

    has_atc = enrichment_result is not None

    return render_template(
        "outcome.html",
        page_title=f"Outcome {id}",
        has_atc_enrichment=has_atc,
        **outcome_data,
    )


@backend.route("/gene")
def get_genes():
    return render_template("gene_list.html", page_title="Genes")


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
