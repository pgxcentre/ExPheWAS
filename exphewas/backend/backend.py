"""
Flask-based application for ExPheWAS.
"""

import os
import random
from collections import defaultdict

from sqlalchemy.orm.exc import NoResultFound
from flask import Blueprint, render_template, abort, url_for, request, redirect

from . import api
from .cache import Cache
from ..version import exphewas_version
from ..db import models
from ..db.engine import Session
from ..db.utils import ANALYSIS_SUBSETS


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
    """Browser and DB versions."""
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
    """Home route."""
    return render_template("index.html", page_title="Home")


@backend.route("/api_docs")
def get_api_docs():
    """API documentation."""
    # Infer api root
    api_root = url_for("api_blueprint.get_metadata", _external=True)
    api_root = "/".join(api_root.split("/")[:-1])

    return render_template(
        "api_docs.html",
        page_title="API Documentation",
        full_api_url=api_root
    )


@backend.route("/browser_docs")
def get_browser_docs():
    """Browser documentation"""
    return render_template(
        "browser_docs.html",
        page_title="Browser Documentation",
    )


@backend.route("/outcome")
def get_outcomes():
    """Outcomes (phenotypes) (list) page."""
    return render_template("outcome_list.html", page_title="Phenotypes")


@backend.route("/outcome/random")
def get_random_outcome():
    """Random outcome (phenotype)."""
    outcomes = Session().query(models.Outcome).all()
    outcome = random.choice(outcomes)

    # Pick an analysis subset with data.
    subsets = ANALYSIS_SUBSETS.copy()
    random.shuffle(subsets)
    for subset in subsets:
        # Check if current subset has data.
        Result = models.RESULTS_CLASS_MAP[subset][outcome.analysis_type]
        res = Session.query(Result).filter_by(outcome_iid=outcome.iid).first()
        if res is None:
            continue

        return redirect(url_for(
            "backend_blueprint.get_outcome",
            id=outcome.id,
            analysis_subset=subset,
            analysis_type=outcome.analysis_type
        ))


@backend.route("/outcome/<id>")
def get_outcome(id):
    """Specific outcome (phenotype)."""
    try:
        outcome_dict = api.get_outcome(id)
    except api.RessourceNotFoundError:
        abort(404)

    # Checks if there are enrichment results for this outcome
    enrichment_result = Session.query(models.EnrichmentContingency)\
        .filter_by(hierarchy_id="ATC", outcome_iid=outcome_dict["iid"])\
        .first()

    has_atc = enrichment_result is not None

    title = "Outcome '{}' - {}".format(id, outcome_dict["label"])
    analysis_subset = request.args.get("analysis_subset", "BOTH")
    if analysis_subset == "FEMALE_ONLY":
        title += " (Female only)"
    elif analysis_subset == "MALE_ONLY":
        title += " (Male only)"

    available_subsets = list(filter(
        lambda o: (
            o["id"] == id and
            o["analysis_type"] == outcome_dict["analysis_type"]
        ),
        Cache().get("outcomes")
    ))
    assert len(available_subsets) == 1
    available_subsets = available_subsets[0]["available_subsets"]

    return render_template(
        "outcome.html",
        page_title=title,
        has_atc_enrichment=has_atc,
        available_subsets=list(available_subsets),
        analysis_subset=analysis_subset,
        **outcome_dict,
    )


@backend.route("/gene")
def get_genes():
    """Gene (list) page."""
    return render_template("gene_list.html", page_title="Genes")


@backend.route("/cisMR")
def cis_mr():
    """cis-MR page."""
    return render_template("cis_mr.html", page_title="cisMR")


@backend.route("/gene/random")
def get_random_gene():
    """Random gene page."""
    ensgs = Session().query(models.Gene.ensembl_id).all()
    ensg = random.choice(ensgs)[0]

    subset = random.choice(ANALYSIS_SUBSETS)
    return redirect(url_for(
        "backend_blueprint.get_gene",
        ensg=ensg,
        analysis_subset=subset
    ))


@backend.route("/gene/<ensg>")
def get_gene(ensg):
    """Specific gene page."""
    try:
        gene_info = api.get_gene_by_ensembl_id(ensg)
    except api.RessourceNotFoundError:
        abort(404)

    # Adding the cross references
    xrefs = defaultdict(list)
    db_names = {}
    for xref in api.get_gene_xrefs(ensg):
        db_names[xref["db_id"]] = xref["db_description"]
        xrefs[xref["db_id"]].append(xref["external_id"])

    # Checking if there are any GTEx data
    has_gtex = len(api.get_gene_gtex(ensg)) > 0

    title = "Gene '{}' - {}".format(gene_info["ensembl_id"], gene_info["name"])
    analysis_subset = request.args.get("analysis_subset", "BOTH")
    if analysis_subset == "FEMALE_ONLY":
        title += " (Female only)"
    elif analysis_subset == "MALE_ONLY":
        title += " (Male only)"

    return render_template(
        "gene.html",
        page_title=title,
        **gene_info,
        analysis_subset=analysis_subset,
        xrefs=xrefs,
        has_gtex=has_gtex,
        db_full_names=db_names,
        db_urls=EXTERNAL_DB_URL,
        external_dbs=EXTERNAL_DB_TO_SHOW,
        max_n_pcs=os.environ.get("EXPHEWAS_MAX_N_PCS", 40),
    )
