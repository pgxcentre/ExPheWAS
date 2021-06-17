"""
Flask-based REST API for the results of the ExPheWAS analysis.
"""

import json
import itertools
import functools
from os import path

import numpy as np

from sqlalchemy import distinct, and_
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import joinedload, undefer
from sqlalchemy.sql.expression import func, null

from flask import Blueprint, jsonify, request, current_app

from ..db import models
from ..db.tree import tree_from_hierarchy_id
from ..db.engine import Session
from ..db.utils import mod_to_dict
from ..utils import (
    load_gtex_median_tpm, load_gtex_statistics, qvalue, one_sample_ivw_mr
)



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
        except AmbiguousIdentifierError as exception:
            return bad_request(exception.message)

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


class cached(object):
    """Simple decorator to cache functions."""
    def __init__(self, f):
        self.f = f
        self.__name__ = f.__name__
        self.clear_cache()

    def clear_cache(self):
        self.cache = None

    def __call__(self):
        if self.cache is None:
            self.cache = self.f()
        return self.cache


def _get_outcome(session, id, analysis_type=None):
    filters = {"id": id}

    if analysis_type is not None:
        filters["analysis_type"] = analysis_type

    elif "analysis_type" in request.args:
        filters["analysis_type"] = request.args["analysis_type"]

    try:
        return session.query(models.Outcome).filter_by(**filters).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find outcome '{id}'."
        )
    except MultipleResultsFound:
        raise AmbiguousIdentifierError(
            f"There are multiple outcomes with id='{id}'. Specifying an "
            "analysis_type parameter guarantees uniqueness."
        )


class RessourceNotFoundError(Exception):
    def __init__(self, message):
        self.message = message


class AmbiguousIdentifierError(Exception):
    def __init__(self, message):
        self.message = message


@api.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@api.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400


@make_api("/metadata")
def get_metadata():
    try:
        return Session.query(models.Metadata).one().metadata_dict()
    except NoResultFound:
        return {
            "version": "unknown",
            "date": "",
            "comments": "The version has not been set in the results database."
        }


@make_api("/outcome")
@cached
def get_outcomes():
    session = Session()

    u = models.all_results_union(session).subquery()

    subq = session.query(
        u.c.outcome_id,
        u.c.analysis_type,
        func.array_agg(u.c.analysis_subset).label("available_subsets")
    ).group_by(
        u.c.outcome_id,
        u.c.analysis_type
    ).subquery()

    results = session.query(models.Outcome, subq.c.available_subsets)\
        .join(subq, and_(
            models.Outcome.id==subq.c.outcome_id,
            models.Outcome.analysis_type==subq.c.analysis_type
        ))

    return [
        {
            "id": o.id,
            "type": o.type,
            "analysis_type": o.analysis_type,
            "label": o.label,
            "available_subsets": availables,
        } for o, availables in results
    ]


@make_api("/outcome/<id>")
def get_outcome(id):
    session = Session()
    outcome = _get_outcome(session, id)
    analysis_subset = request.args.get("analysis_subset")

    out = {
        "id": outcome.id,
        "analysis_type": outcome.analysis_type,
        "analysis_subset": analysis_subset,
        "label": outcome.label,
        "type": outcome.type,
    }

    # Get appropriate result class.
    # We need to also look at analysis subset so that the reported ns are
    # correct.
    if isinstance(outcome, models.ContinuousOutcome):
        # Get mean n.
        q = session.query(
            func.avg(models.ContinuousVariableResult.n)
        ).filter_by(
            outcome_id=outcome.id,
            analysis_type=outcome.analysis_type,
            analysis_subset=analysis_subset
        )

        out["n_avg"] = int(q.one()[0])

    else:
        res = session.query(
            func.avg(models.BinaryVariableResult.n_cases),
            func.avg(models.BinaryVariableResult.n_controls),
            func.avg(models.BinaryVariableResult.n_excluded_from_controls)
        ).filter_by(
            outcome_id=outcome.id,
            analysis_type=outcome.analysis_type,
            analysis_subset=analysis_subset
        ).one()

        res = [int(i) if i else 0 for i in res]
        (
            out["n_cases_avg"],
            out["n_controls_avg"],
            out["n_excluded_from_controls_avg"]
        ) = res

    return out


def _query_outcome_results(outcome, analysis_subset="BOTH",
                           preload_model=False):
    session = Session()

    Result = None
    if isinstance(outcome, models.BinaryOutcome):
        Result = models.BinaryVariableResult
    elif isinstance(outcome, models.ContinuousOutcome):
        Result = models.ContinuousVariableResult

    query = session.query(Result)\
        .filter_by(
            outcome_id=outcome.id,
            analysis_type=outcome.analysis_type,
            analysis_subset=analysis_subset
        )

    if preload_model:
        query.options(undefer("model_fit"))

    return query


@make_api("/outcome/<id>/results")
def get_outcome_results(id):
    session = Session()
    outcome = _get_outcome(session, id)
    analysis_subset = request.args.get("analysis_subset", "BOTH")

    results = _query_outcome_results(outcome, analysis_subset)\
        .options(joinedload("gene_obj"))\
        .options(joinedload("outcome_obj"))\
        .all()

    if len(results) == 0:
        raise NoResultFound(f"Could not find results for outcome '{id}'.")

    # Get the corresponding Q-values.
    nlog10ps = np.fromiter(
        (r.static_nlog10p for r in results),
        dtype=np.float, count=len(results)
    )

    # We clamp everything at 10^-500
    nlog10ps[~np.isfinite(nlog10ps) | (nlog10ps >= 500)] = 500

    ps = 10 ** -nlog10ps
    qs = qvalue(ps)

    return [
        {
            "gene": r.gene,
            "analysis_type": r.analysis_type,
            "outcome_id": r.outcome_id,
            "outcome_label": r.outcome_obj.label,
            "nlog10p": nlog10p,
            "p": p,
            "bonf": p * len(results),
            "q": q,
            "gene_name": r.gene_obj.name,
            "n_components": r.gene_obj.n_pcs
        }
        for nlog10p, q, p, r in zip(nlog10ps, qs, ps, results)
    ]


@make_api("/gene")
def get_genes():
    from_db = request.args.get("from_db", False)

    if not from_db:
        json_fn = path.join(path.dirname(__file__), "static", "genes.json")
        with open(json_fn) as genes:
            return json.loads(genes.read())

    else:
        genes = Session.query(models.Gene).all()
        return [mod_to_dict(gene) for gene in genes]


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
    try:
        gene = Session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    # Creating the final results.
    results = mod_to_dict(gene)
    results["n_pcs"] = gene.n_pcs

    return results


@make_api("/gene/<ensg>/results")
def get_gene_results(ensg):
    session = Session()
    try:
        session.query(models.Gene).filter_by(ensembl_id=ensg).one()
    except NoResultFound:
        raise RessourceNotFoundError(
            f"Could not find gene (by Ensembl ID) '{ensg}'."
        )

    analysis_subset = request.args.get("analysis_subset", "BOTH")

    # Outcome.
    res_cont = session.query(models.ContinuousVariableResult)\
        .filter_by(
            gene=ensg,
            analysis_subset=analysis_subset
        ).all()

    res_bin = session.query(models.BinaryVariableResult)\
        .filter_by(
            gene=ensg,
            analysis_subset=analysis_subset
        ).all()

    results = []
    nlog10ps = []
    for res in itertools.chain(res_cont, res_bin):
        results.append(res.to_object())
        nlog10ps.append(res.static_nlog10p)

    if len(results) == 0:
        raise RessourceNotFoundError(f"No results for gene '{ensg}'.")

    # Get the corresponding Q-values.
    nlog10ps = np.array(nlog10ps)
    ps = 10 ** -nlog10ps

    # We clamp everything at 10^-500
    nlog10ps[~np.isfinite(nlog10ps) | (nlog10ps >= 500)] = 500

    bonf_ps = ps * ps.shape[0]
    qs = qvalue(ps)

    for i in range(len(results)):
        results[i]["nlog10p"] = nlog10ps[i]
        results[i]["p"] = ps[i]
        results[i]["bonf"] = bonf_ps[i]
        results[i]["q"] = qs[i]

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


@make_api("/cisMR")
def cis_mendelian_randomization():
    """Performs cis-MR using the IVW estimator and the PCs as IVs."""
    gene = request.args["ensembl_id"]
    analysis_subset = request.args.get("analysis_subset", "BOTH")

    exposure_id = request.args.get("exposure_id", None)
    exposure_type = request.args.get("exposure_type", None)

    outcome_id = request.args.get("outcome_id", None)
    outcome_type = request.args.get("outcome_type", None)

    session = Session()
    exposure = _get_outcome(session, exposure_id, exposure_type)
    outcome = _get_outcome(session, outcome_id, outcome_type)

    not_found = []
    try:
        exposure_result = _query_outcome_results(
            exposure,
            analysis_subset,
            preload_model=True
        ).filter_by(gene=gene).one()
    except NoResultFound:
        not_found.append(
            f"'{exposure_type} - {exposure.label} ({exposure_id})'"
        )

    try:
        outcome_result = _query_outcome_results(
            outcome,
            analysis_subset,
            preload_model=True
        ).filter_by(gene=gene).one()
    except NoResultFound:
        not_found.append(f"'{outcome_type} - {outcome.label} ({outcome_id})'")

    if not_found:
        raise RessourceNotFoundError(
            "Could not find results for the following outcome(s): {} in "
            "subset {}."
            "".format(", ".join(not_found), analysis_subset)
        )

    mr_results = one_sample_ivw_mr(
        exposure_result.model_fit_df(),
        outcome_result.model_fit_df(),
        alpha=0.05
    )

    mr_results["outcome_is_binary"] = not (
        outcome_type == "CONTINUOUS_VARIABLE"
    )

    mr_results["exposure_nlog10p"] = exposure_result.static_nlog10p
    if not np.isfinite(mr_results["exposure_nlog10p"]):
        mr_results["exposure_nlog10p"] = 500

    return mr_results


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
