import re
import os

import sqlalchemy.orm.exc
import pandas as pd
import numpy as np

from ..engine import Session
from ..models import (
    ContinuousOutcome, BinaryOutcome,
    ContinuousVariableResult, BinaryVariableResult
)
from ...utils import load_ukbphewas_model, load_variable_labels


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
             "pattern is 'results_ENSG_binary' (or continuous)."
        )

    match = match.groupdict()

    gene = match["ensg"]
    variable_type = match["type"]

    # Check that we can find the model and summary files.
    model = f"{args.prefix}_model.json.gz"
    summary = f"{args.prefix}_summary.csv.gz"
    check_files_exist(model, summary)

    if variable_type == "continuous":
        create_object = _process_continuous_result
        result_class = ContinuousVariableResult

    elif variable_type == "binary":
        create_object = _process_binary_result
        result_class = BinaryVariableResult

    session = Session()

    df = pd.read_csv(summary, dtype={"variable_id": str})
    models = load_ukbphewas_model(model, as_dict=True, fit_df=False)

    # For every line:
    # 1. Get or create Outcome.
    # 2. Create Result.
    objects = []
    for i, row in df.iterrows():
        # Get the model object.
        model_fit = models[(row["analysis_type"], row["variable_id"])]
        o = create_object(row, gene, variable_type, args.sex_subset, model_fit,
                          labels, session)

        if o is not None:
            objects.append(o)

    session.commit()

    # Bulk insert.
    n = len(objects)
    chunk_size = 10000
    for chunk in range(0, n, chunk_size):
        session.bulk_insert_mappings(
            result_class,
            objects[chunk:chunk+chunk_size]
        )

    session.commit()


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
    if args_sex_subset != "BOTH" and row["sex_subset"] != "BOTH":
        if row["sex_subset"] != "BOTH":
            # The phenotype is already sex-stratified.
            raise SkipRow()
        return args_sex_subset

    # The analysis is not sex-stratified, but the phenotype may be.
    return row["sex_subset"]


class SkipRow(Exception):
    pass


def _process_continuous_result(row, gene, variable_type, args_sex_subset,
                               model_fit, labels, session):
    # Get or create outcome.
    try:
        outcome = session.query(ContinuousOutcome)\
            .filter_by(id=row.variable_id,
                       analysis_type=row.analysis_type).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = ContinuousOutcome(
            id = row.variable_id,
            label = labels[(row.analysis_type, row.variable_id)],
            analysis_type = row.analysis_type,
            n = row.n_samples
        )

        session.add(outcome)

    # Sanity check that the number of samples is constant across analyses.
    # This is important given the current implementation of the test statistic.
    assert row.n_samples == outcome.n

    return dict(
        gene = gene,
        outcome_id = outcome.id,
        analysis_type = row.analysis_type,
        analysis_subset = args_sex_subset,
        model_fit = model_fit,

        rss_base = row.rss_base,
        rss_augmented = row.rss_augmented,
        n_params_base = row.n_params_base,
        n_params_augmented = row.n_params_aug,
    )


def _process_binary_result(row, gene, variable_type, args_sex_subset,
                           model_fit, labels, session):
    # Get or create outcome.
    try:
        outcome = session.query(BinaryOutcome)\
            .filter_by(id=row.variable_id,
                       analysis_type=row.analysis_type).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = BinaryOutcome(
            id = row.variable_id,
            label = labels[(row.analysis_type, row.variable_id.lstrip("0"))],
            analysis_type = row.analysis_type,
            n_cases = row.n_cases,
            n_controls = row.n_controls,
            n_excluded_from_controls = row.n_excluded_from_controls
        )

        session.add(outcome)

    try:
        sex_subset = check_sex_subset(row, args_sex_subset)
    except SkipRow:
        return None

    return dict(
        gene = gene,
        outcome_id = outcome.id,
        analysis_type = row.analysis_type,
        analysis_subset = sex_subset,
        model_fit = model_fit,

        deviance_base = row.deviance_base,
        deviance_augmented = row.deviance_augmented,
    )
