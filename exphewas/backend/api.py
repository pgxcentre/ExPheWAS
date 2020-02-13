"""
Flask-based REST API for the results of the ExPheWAS analysis.
"""

import json
import itertools
import functools
from os import path

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func, null

from flask import Blueprint, jsonify, request

from ..db import models
from ..db.tree import tree_from_hierarchy_id
from ..db.engine import Session
from ..db.utils import mod_to_dict
from ..utils import load_gtex_median_tpm, load_gtex_statistics

from .r_bindings import R


try:
    R_instance = R()

except:
    R_instance = None


api = Blueprint("api_blueprint", __name__)


# Loading GTEx data
GTEX_MEDIAN_TPM = load_gtex_median_tpm()
GTEX_STATS = load_gtex_statistics()


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
    subquery = Session.query(
        models.AvailableOutcomeResult.outcome_id,
        func.array_agg(models.AvailableOutcomeResult.variance_pct)\
            .label("available_variances"),
    ).group_by(models.AvailableOutcomeResult.outcome_id).subquery()

    results = Session.query(models.Outcome, subquery)\
        .join(subquery, isouter=True).all()

    return [
        {
            "id": outcome.id,
            "label": outcome.label,
            "analysis_type": outcome.analysis_type,
            "available_variances": available_variances,
        } for outcome, outcome_id, available_variances in results
    ]


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

    # Get the corresponding Q-values.
    if R_instance is not None:
        qs = R_instance.qvalue([r.p for r in results])
    else:
        qs = itertools.cycle([None])

    return [
        {
            "gene": r.gene,
            "analysis_type": r.outcome_obj.analysis_type,
            "outcome_id": r.outcome_id,
            "outcome_label": r.outcome_obj.label,
            "variance_pct": r.variance_pct,
            "p": r.p,
            "q": q,
            "bonf": r.p * len(results),
            "gene_name": r.gene_obj.name,
            "n_components": r.gene_variance_obj.n_components
        }
        for q, r in zip(qs, results)
    ]


@make_api("/gene")
def get_genes():
    from_db = request.args.get("from_db", False)

    if not from_db:
        json_fn = path.join(path.dirname(__file__), "static", "genes.json")
        with open(json_fn) as genes:
            res = json.loads(genes.read())

    else:
        genes = Session.query(models.Gene).all()
        res = [mod_to_dict(gene) for gene in genes]

    return res


@make_api("/gene/name/<name>")
def get_gene_by_name(name):
    try:
        gene = Session.query(models.Gene).filter_by(name=name).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by name) '{name}'."
        )

    return mod_to_dict(gene)


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

    # Creating the final results.
    results = mod_to_dict(gene)
    results.update(mod_to_dict(gene_variance))

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
              "variance_pct", "p", "gof_meas", "gene_name", "n_components",
              "test_statistic")

    result_models = (
        {
            "model": models.BinaryVariableResult,
            "gof_meas": models.BinaryVariableResult.deviance,
            "test_statistic": null(),
        },
        {
            "model": models.ContinuousVariableResult,
            "gof_meas": models.ContinuousVariableResult.sum_of_sq,
            "test_statistic": models.ContinuousVariableResult.F_stat,
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
            result_info["test_statistic"],
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

    # Get the corresponding Q-values.
    if R_instance is not None:
        qs = R_instance.qvalue([r["p"] for r in results])
    else:
        qs = None

    for i in range(len(results)):
        results[i]["q"] = None if qs is None else qs[i]
        results[i]["bonf"] = results[i]["p"] * len(results)

    return results


@make_api("/gene/<ensg>/xrefs")
def get_gene_xrefs(ensg):
    results = Session.query(models.XRefs, models.ExternalDB)\
        .filter(models.XRefs.external_db_id == models.ExternalDB.id)\
        .filter_by(ensembl_id=ensg)\
        .all()

    return [
        {
            "gene": xref.ensembl_id,
            "db_id": external_db.db_name,
            "db_description": external_db.db_display_name,
            "external_id": xref.external_id,
        }
        for xref, external_db in results
    ]


@make_api("/gene/<ensg>/available_variance")
def get_gene_available_variance(ensg):
    results = Session.query(
        models.AvailableGeneResult.ensembl_id,
        func.array_agg(models.AvailableGeneResult.variance_pct)
            .label("available_variances"),
    ).filter_by(ensembl_id=ensg)\
        .group_by(models.AvailableGeneResult.ensembl_id).one()

    return {"ensembl_id": results[0], "available_variance": results[1]}


@make_api("/outcome/<id>/available_variance")
def get_outcome_available_variance(id):
    results = Session.query(
        models.AvailableOutcomeResult.outcome_id,
        func.array_agg(models.AvailableOutcomeResult.variance_pct)
            .label("available_variances"),
    ).filter_by(outcome_id=id)\
        .group_by(models.AvailableOutcomeResult.outcome_id).one()

    return {"outcome_id": results[0], "available_variance": results[1]}


@make_api("/gene/<ensg>/gtex")
def get_gene_gtex(ensg):
    if ensg not in GTEX_MEDIAN_TPM.index:
        return []

    gtex_data = [
        {"tissue": tissue, "value": value, "nb_samples": GTEX_STATS[tissue]}
        for tissue, value in GTEX_MEDIAN_TPM.loc[ensg, :].iteritems()
    ]
    return gtex_data


@make_api("/outcome/venn")
def get_outcome_venn():
    # Getting the genes
    outcomes = request.args.get("outcomes", "").split(";")

    # Getting the p value threshold
    q_threshold = float(request.args.get("q", 0.05))

    # Getting the genes for each of the outcomes
    outcome_genes = []
    for outcome in outcomes:
        genes = {
            data["gene"] for data in get_outcome_results(outcome)
            if data["q"] < q_threshold
        }
        outcome_genes.append(genes)

    return [
        {
            "sets": [outcomes[0]],
            "size": len(outcome_genes[0] - outcome_genes[1]),
        },
        {
            "sets": [outcomes[1]],
            "size": len(outcome_genes[1] - outcome_genes[0])
        },
        {
            "sets": [outcomes],
            "size": len(outcome_genes[1] & outcome_genes[0]),
        },
    ]


@make_api("/tree/<id>")
def get_tree(id):
    root = tree_from_hierarchy_id(id)
    if len(root.children) == 0:
        raise RessourceNotFoundError(f"{id}: not a valid hierarchy")

    tree = root.to_primitive()
    tree["code"] = id

    return tree


@make_api("/enrichment/atc/fgsea/<outcome_id>")
def get_enrichment_atc_fgsea_for_outcome(outcome_id):
    return get_enrichment_for_outcome(outcome_id, models.Enrichment)


@make_api("/enrichment/atc/contingency/<outcome_id>")
def get_enrichment_atc_contingency_for_outcome(outcome_id):
    return get_enrichment_for_outcome(outcome_id, models.EnrichmentContingency)


def get_enrichment_for_outcome(outcome_id, enr_model):
    atc_tree = tree_from_hierarchy_id("ATC")

    # We will make a dict representation of the ATC tree to update the data
    # easily.
    atc_dict = {n.code: n for _, n in atc_tree.iter_depth_first()}

    results = Session.query(enr_model)\
        .filter_by(hierarchy_id="ATC")\
        .filter_by(outcome_id=outcome_id)\
        .all()

    for enrichment_result in results:
        n = atc_dict[enrichment_result.gene_set_id]
        n._data = enrichment_result.get_data_dict()
        n._data["min_p_children"] = None

    stack = []
    for _, node in atc_tree.iter_depth_first():
        # Set the minimum p-value in subtree.
        stack.append(node)

    while stack:
        cur = stack.pop()

        if cur._data is None:
            cur._data = {"p": None, "min_p_children": None}

        ps = [i._data["min_p_children"] for i in cur.children]
        ps.append(cur._data["p"])

        # Remove Nones
        ps = [i for i in ps if i is not None]

        if len(ps) == 0:
            # If there are no data for this node and all its children.
            cur_min = None

        else:
            cur_min = min(ps)

        cur._data["min_p_children"] = cur_min

    tree = atc_tree.to_primitive()
    tree["code"] = "ATC"

    return tree
