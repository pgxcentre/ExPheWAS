"""
Flask-based REST API for the results of the ExPheWAS analysis.
"""

import functools

from sqlalchemy.orm.exc import NoResultFound
from flask import Blueprint, jsonify

from ..db import models
from ..db.engine import Session
from ..db.utils import mod_to_dict


api = Blueprint("api_blueprint", __name__, url_prefix="/api")


class make_api(object):
    def __init__(self, rule, handler=None):
        self.rule = rule
        self.handler = handler

    @staticmethod
    def _default_api_call_handler(f, *args, **kwargs):
        try:
            results = f(*args, **kwargs)
        except RessourceNotFoundError as exception:
            return resource_not_found(exception.message)

        return jsonify(results)

    def __call__(self, f):
        if self.handler is None:
            handler = self._default_api_call_handler
        else:
            handler = self.handler

        api.add_url_rule(
            self.rule,
            f.__name__,
            functools.partial(handler, f=f)
        )

        return f


class RessourceNotFoundError(Exception):
    def __init__(self, message):
        self.message = message


@api.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@make_api("/outcome")
def get_outcomes():
    res = Session.query(models.Outcome).all()

    return [{"id": i.id, "label": i.label} for i in res]


@make_api("/outcome/<id>")
def get_outcome(id):
    try:
        outcome = Session.query(models.Outcome).filter_by(id=id).one()
    except NoResultFound:
        raise RessourceNotFoundError(f"Could not find outcome '{id}'.")

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

    return d


@make_api("/outcome/<id>/results")
def get_outcome_results(id):
    try:
        Session.query(models.Outcome).filter_by(id=id).one()
    except NoResultFound:
        raise RessourceNotFoundError(f"Could not find outcome '{id}'.")

    # Find all results.
    fields = ("id", "gene", "analysis", "outcome_id", "outcome_label",
              "variance_pct", "p", "gene_name")

    results = Session\
        .query(
            models.Result.id,
            models.Result.gene,
            models.Result.analysis,
            models.Result.outcome_id,
            models.Outcome.label,
            models.Result.variance_pct,
            models.Result.p,
            models.Gene.name,
        )\
        .filter(models.Outcome.id == models.Result.outcome_id)\
        .filter(models.Result.gene == models.Gene.ensembl_id)\
        .filter_by(outcome_id=id)\
        .all()

    results = [dict(zip(fields, i)) for i in results]

    return results


@make_api("/gene/name/<name>")
def get_gene_by_name(name):
    try:
        gene = Session.query(models.Gene).filter_by(name=name).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by name) '{name}'."
        )

    # Add the Uniprot xref.
    d = mod_to_dict(gene)
    d.update({"uniprot_id": gene.uniprot_ids})

    return d


@make_api("/gene/ensembl/<ensg>")
def get_gene_by_ensembl_id(ensg):
    try:
        gene = Session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    # Add the Uniprot xref.
    d = mod_to_dict(gene)
    d.update({"uniprot_id": gene.uniprot_ids})

    return d


@make_api("/gene/<ensg>/results")
def get_gene_results(ensg):
    try:
        Session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    # Find all results.
    fields = ("id", "gene", "analysis", "outcome_id", "outcome_label",
              "variance_pct", "p", "gene_name")

    results = Session\
        .query(
            models.Result.id,
            models.Result.gene,
            models.Result.analysis,
            models.Result.outcome_id,
            models.Outcome.label,
            models.Result.variance_pct,
            models.Result.p,
            models.Gene.name,
        )\
        .filter(models.Outcome.id == models.Result.outcome_id)\
        .filter(models.Gene.ensembl_id == models.Result.gene)\
        .filter_by(gene=ensg)\
        .all()

    results = [dict(zip(fields, i)) for i in results]

    return results
