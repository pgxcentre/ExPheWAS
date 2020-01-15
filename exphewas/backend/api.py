"""
Flask-based REST API for the results of the ExPheWAS analysis.
"""

import json
import functools
from os import path

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from flask import Blueprint, jsonify, request

from ..db import models
from ..db.engine import Session
from ..db.utils import mod_to_dict

from .r_bindings import R


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
        "label": outcome.label,
        "analysis_type": outcome.analysis_type,
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
        outcome = Session.query(models.Outcome).filter_by(id=id).one()
    except NoResultFound:
        raise RessourceNotFoundError(f"Could not find outcome '{id}'.")

    variance_pct = request.args.get("variance_pct", 95)

    Result = None
    if isinstance(outcome, models.BinaryOutcome):
        Result = models.BinaryVariableResult
    elif isinstance(outcome, models.ContinuousOutcome):
        Result = models.ContinuousVariableResult

    results = Session\
        .query(Result)\
        .filter_by(outcome_id=id, variance_pct=variance_pct)\
        .options(joinedload("gene_obj"))\
        .options(joinedload("outcome_obj"))\
        .options(joinedload("gene_variance_obj"))\
        .all()

    return [
        {
            "gene": r.gene,
            "analysis_type": r.outcome_obj.analysis_type,
            "outcome_id": r.outcome_id,
            "outcome_label": r.outcome_obj.label,
            "variance_pct": r.variance_pct,
            "p": r.p,
            "gene_name": r.gene_obj.name,
            "n_components": r.gene_variance_obj.n_components
        }
        for r in results
    ]


@make_api("/gene")
def get_genes():
    json_fn = path.join(path.dirname(__file__), "static", "genes.json")
    with open(json_fn) as genes:
        res = json.loads(genes.read())

    return res


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
    variance_pct = request.args.get("variance_pct", 95)

    try:
        gene, gene_variance = Session.query(
            models.Gene,
            models.GeneVariance,
        )\
        .filter(models.Gene.ensembl_id == ensg)\
        .filter(models.Gene.ensembl_id == models.GeneVariance.ensembl_id)\
        .filter(models.GeneVariance.variance_pct == variance_pct)\
        .one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    # Add the Uniprot xref.
    results = mod_to_dict(gene)
    results.update(mod_to_dict(gene_variance))
    results.update({"uniprot_ids": gene.uniprot_ids})

    return results


@make_api("/gene/<ensg>/results")
def get_gene_results(ensg):
    try:
        Session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    variance_pct = request.args.get("variance_pct", 95)

    # Find all results.
    fields = ("gene", "analysis_type", "outcome_id", "outcome_label",
              "variance_pct", "p", "gof_meas", "gene_name", "n_components")

    result_models = (
        {
            "model": models.BinaryVariableResult,
            "gof_meas": models.BinaryVariableResult.deviance,
        },
        {
            "model": models.ContinuousVariableResult,
            "gof_meas": models.ContinuousVariableResult.sum_of_sq,
        },
    )

    binary_results, continuous_results = [
        Session.query(
            result_info["model"].gene,
            models.Outcome.analysis_type,
            result_info["model"].outcome_id,
            models.Outcome.label,
            result_info["model"].variance_pct,
            result_info["model"].p,
            result_info["gof_meas"],
            models.Gene.name,
            models.GeneVariance.n_components,
        )
        .filter(models.Outcome.id == result_info["model"].outcome_id)
        .filter(models.Gene.ensembl_id == result_info["model"].gene)
        .filter(models.GeneVariance.ensembl_id == models.Gene.ensembl_id)
        .filter(models.GeneVariance.variance_pct == result_info["model"].variance_pct)
        .filter(result_info["model"].variance_pct == variance_pct)
        .filter_by(gene=ensg)
        for result_info in result_models
    ]

    results = binary_results.union(continuous_results).all()

    results = [dict(zip(fields, i)) for i in results]

    return results


@api.route("/qvalue", methods=["POST"])
def qvalue():
    try:
        p = json.loads(request.data)
    except Exception as e:
        return jsonify({"error": str(e)})

    # Load rpy2.
    try:
        r = R()
        return jsonify(r.qvalue(p))
    except Exception as e:
        return jsonify({"error": str(e)})
