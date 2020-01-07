"""
Flask-based REST API for the results of the ExPheWAS analysis.
"""

import json

from sqlalchemy.orm.exc import NoResultFound
from flask import Flask, jsonify, abort
from flask_cors import CORS

from ..db import models
from ..db.engine import Session
from ..db.utils import mod_to_dict


app = Flask(__name__)

CORS(app)


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@app.route("/api/outcome")
def get_outcomes():
    res = Session.query(models.Outcome).all()

    return jsonify([{"id": i.id, "label": i.label} for i in res])


@app.route("/api/outcome/<id>")
def get_outcome(id):
    try:
        outcome = Session.query(models.Outcome).filter_by(id=id).one()
    except NoResultFound:
        return resource_not_found(f"Could not find outcome '{id}'.")

    # Extract shared fields.
    d = {
        "id": outcome.id,
        "label": outcome.label
    }

    if isinstance(outcome, models.BinaryOutcome):
        d.update({
            "type": "binary",
            "n_cases": outcome.n_cases,
            "n_controls": outcome.n_controls,
            "n_excluded_from_controls": outcome.n_excluded_from_controls,
        })

    elif isinstance(outcome, models.ContinuousOutcome):
        d.update({
            "type": "continuous",
            "n": outcome.n,
        })

    return jsonify(d)


@app.route("/api/outcome/<id>/results")
def get_outcome_results(id):
    try:
        gene = Session.query(models.Outcome).filter_by(id=id).one()
    except NoResultFound:
        return resource_not_found(
            f"Could not find outcome '{id}'."
        )

    # Find all results.
    fields = ("id", "gene", "analysis", "outcome_id", "outcome_label",
              "variance_pct", "p")

    results = Session\
        .query(
            models.Result.id,
            models.Result.gene,
            models.Result.analysis,
            models.Result.outcome_id,
            models.Outcome.label,
            models.Result.variance_pct,
            models.Result.p,
        )\
        .filter(models.Outcome.id==models.Result.outcome_id)\
        .filter_by(outcome_id=id)\
        .all()

    results = [dict(zip(fields, i)) for i in results]

    return jsonify(results)


@app.route("/api/gene/name/<name>")
def get_gene_by_name(name):
    try:
        gene = Session.query(models.Gene).filter_by(name=name).one()
    except NoResultFound:
        return resource_not_found(f"Could not find gene (by name) '{name}'.")

    # Add the Uniprot xref.
    d = mod_to_dict(gene)
    d.update({"uniprot_id": gene.uniprot_ids})

    return jsonify(d)


@app.route("/api/gene/ensembl/<ensg>")
def get_gene_by_ensembl_id(ensg):
    try:
        gene = Session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        return resource_not_found(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    # Add the Uniprot xref.
    d = mod_to_dict(gene)
    d.update({"uniprot_id": gene.uniprot_ids})

    return jsonify(d)


@app.route("/api/gene/<ensg>/results")
def get_gene_results(ensg):
    try:
        gene = Session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        return resource_not_found(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    # Find all results.
    fields = ("id", "gene", "analysis", "outcome_id", "outcome_label",
              "variance_pct", "p")

    results = Session\
        .query(
            models.Result.id,
            models.Result.gene,
            models.Result.analysis,
            models.Result.outcome_id,
            models.Outcome.label,
            models.Result.variance_pct,
            models.Result.p,
        )\
        .filter(models.Outcome.id==models.Result.outcome_id)\
        .filter_by(gene=ensg)\
        .all()

    results = [dict(zip(fields, i)) for i in results]

    return jsonify(results)


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()
