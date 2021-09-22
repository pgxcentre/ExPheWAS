"""Import data into the database."""

import re
import os

import sqlalchemy.orm.exc
import pandas as pd
import numpy as np

from ..engine import Session
from ..models import (
    Gene, Outcome, ContinuousResult, BinaryResult, get_results_class,
    get_model_fit_class,
)
from ...utils import load_ukbphewas_model, load_variable_labels
from ..utils import ANALYSIS_TYPES, ANALYSIS_SUBSETS


PREFIX_PAT = re.compile(
    r"results_(?P<ensg>ENSG[0-9]+)_(?P<type>binary|continuous)"
)


# import-results prefix --sex-subset
def main(args):
    labels = load_variable_labels()
    basename = os.path.basename(args.prefix)
    match = re.match(PREFIX_PAT, basename)

    if match is None:
        raise ValueError(
            f"Unrecognized prefix: '{basename}'. The expected "
            f"pattern is 'results_ENSG_binary' (or continuous)."
        )

    match = match.groupdict()

    gene = match["ensg"]
    variable_type = match["type"]

    # Get n_pcs
    session = Session()
    n_pcs = session.query(Gene).filter_by(ensembl_id=gene).one().n_pcs

    # By default, analysis kept only 40 PCs
    n_pcs = min(n_pcs, args.max_n_pcs)

    # Check that we can find the model and summary files.
    model = f"{args.prefix}_model.json.gz"
    summary = f"{args.prefix}_summary.csv.gz"
    check_files_exist(model, summary)

    if variable_type == "continuous":
        create_object = _process_continuous_result

    elif variable_type == "binary":
        create_object = _process_binary_result

    df = pd.read_csv(summary, dtype={"variable_id": str})
    models = load_ukbphewas_model(model, as_dict=True, fit_df=False)

    # For every line:
    # 1. Get or create Outcome.
    # 2. Create Result.
    objects = {
        a_type: {a_subset: [] for a_subset in ANALYSIS_SUBSETS}
        for a_type in ANALYSIS_TYPES
    }

    model_fit_objects = {
        a_type: {a_subset: [] for a_subset in ANALYSIS_SUBSETS}
        for a_type in ANALYSIS_TYPES
    }

    for _, row in df.iterrows():
        if np.isnan(row["p"]):
            continue

        # Get the model object.
        o = create_object(row, gene, variable_type, args.sex_subset,
                          args.min_n_cases, labels, session)

        if o is not None:
            # Pre-compute the p-value
            result_class = get_results_class(
                row.analysis_type, o["analysis_subset"]
            )
            o["static_nlog10p"] = _compute_nlog10p(
                result_class, o, n_pcs,
            )
            objects[row.analysis_type][o["analysis_subset"]].append(o)

            # Adding the model fit
            model_fit_objects[row.analysis_type][o["analysis_subset"]].append(
                dict(
                    outcome_id=o["outcome_id"],
                    gene=gene,
                    model_fit=models[(row["analysis_type"], row["variable_id"])],
                )
            )

    session.commit()

    # Bulk insert.
    for analysis_type in ANALYSIS_TYPES:
        for sex_subset in ANALYSIS_SUBSETS:
            # The results
            to_insert = objects[analysis_type][sex_subset]
            result_class = get_results_class(analysis_type, sex_subset)
            session.bulk_insert_mappings(result_class, to_insert)

            # The model fits
            to_insert = model_fit_objects[analysis_type][sex_subset]
            model_fit_class = get_model_fit_class(analysis_type, sex_subset)
            session.bulk_insert_mappings(model_fit_class, to_insert)

    session.commit()


def _compute_nlog10p(result_class, o, n_pcs):
    if issubclass(result_class, ContinuousResult):
        return ContinuousResult.nlog10p_primitive(
            o["rss_base"], o["rss_augmented"], o["n"],
            o["n_params_base"], o["n_params_augmented"]
        )

    elif issubclass(result_class, BinaryResult):
        return BinaryResult.nlog10p_primitive(
            o["deviance_base"], o["deviance_augmented"],
            n_pcs
        )

    else:
        raise ValueError(result_class)


def check_files_exist(*args):
    for filename in args:
        with open(filename, "rb"):
            pass


def check_sex_subset(row, args_sex_subset):
    # Scenarios:
    # 1. The args_sex_subset variable is FEMALE_ONLY which means it's one of
    #    the sex stratified analyses. In this case, we ignore cases where
    #    row.sex_subset != "BOTH" because they will be included in the
    #    unstratified analyses. Otherwise, we return the analysis level
    #    subgroup.
    # 2. The args_sex_subset variable is BOTH in this case we use the value
    #    from row.sex_subset.
    if args_sex_subset != "BOTH":
        if row["sex_subset"] != "BOTH":
            # The phenotype is already sex-stratified.
            raise SkipRow()

        return args_sex_subset

    # The analysis is not sex-stratified, but the phenotype may be.
    return row["sex_subset"]


class SkipRow(Exception):
    pass


def _process_continuous_result(row, gene, variable_type, args_sex_subset,
                               _min_n_cases, labels, session):
    # Get or create outcome.
    try:
        outcome = session.query(Outcome)\
            .filter_by(id=row.variable_id,
                       analysis_type=row.analysis_type).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = Outcome(
            id=row.variable_id,
            label=labels[(row.analysis_type, row.variable_id)],
            analysis_type=row.analysis_type,
        )

        session.add(outcome)

    return dict(
        gene=gene,
        outcome_id=outcome.id,
        analysis_type=row.analysis_type,
        analysis_subset=args_sex_subset,

        n=row.n_samples,
        rss_base=row.rss_base,
        rss_augmented=row.rss_augmented,
        n_params_base=row.n_params_base,
        n_params_augmented=row.n_params_aug,
    )


def _process_binary_result(row, gene, variable_type, args_sex_subset,
                           min_n_cases, labels, session):
    if row.n_cases < min_n_cases:
        return None

    # Get or create outcome.
    try:
        outcome = session.query(Outcome)\
            .filter_by(id=row.variable_id,
                       analysis_type=row.analysis_type).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = Outcome(
            id=row.variable_id,
            label=labels[(row.analysis_type, row.variable_id.lstrip("0"))],
            analysis_type=row.analysis_type,
        )

        session.add(outcome)

    try:
        sex_subset = check_sex_subset(row, args_sex_subset)
    except SkipRow:
        return None

    return dict(
        gene=gene,
        outcome_id=outcome.id,
        analysis_type=row.analysis_type,
        analysis_subset=sex_subset,

        n_cases=row.n_cases,
        n_controls=row.n_controls,
        n_excluded_from_controls=row.n_excluded_from_controls,

        deviance_base=row.deviance_base,
        deviance_augmented=row.deviance_augmented,
    )
