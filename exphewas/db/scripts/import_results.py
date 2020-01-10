import sqlalchemy.orm.exc
import pandas as pd
import numpy as np

from ..engine import Session
from ..models import (
    ContinuousOutcome, BinaryOutcome,
    ContinuousVariableResult, BinaryVariableResult
)


def main(args):
    session = Session()

    df = pd.read_csv(args.filename, dtype={"outcome_id": str})

    if "sum_of_sq" in df.columns:
        create_object = _process_continuous_result
        result_class = ContinuousVariableResult

    elif "deviance" in  df.columns:
        create_object = _process_binary_result
        result_class = BinaryVariableResult

    else:
        raise ValueError("Could not infer analysis type.")

    # For every line:
    # 1. Get or create Outcome.
    # 2. Create Result.
    objects = []
    for i, row in df.iterrows():
        objects.append(create_object(row, args, session))

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


def _process_continuous_result(row, args, session):
    # Get or create outcome.
    try:
        outcome = session.query(ContinuousOutcome)\
            .filter_by(id=row.outcome_id).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = ContinuousOutcome(
            id = row.outcome_id,
            label = row.outcome_label,
            analysis_type = args.analysis,
        )

        session.add(outcome)

    return dict(
        gene = args.gene,
        variance_pct = args.pct_variance,
        outcome_id = outcome.id,
        p = row.p,

        rss_base = row.rss_base,
        rss_augmented = row.rss_augmented,
        sum_of_sq = row.sum_of_sq,
        F_stat = row.F_stat
    )


def _process_binary_result(row, args, session):
    # Get or create outcome.
    try:
        outcome = session.query(BinaryOutcome)\
            .filter_by(id=row.outcome_id).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = BinaryOutcome(
            id = row.outcome_id,
            label = row.outcome_label,
            analysis_type = args.analysis,
            n_cases = row.n_cases,
            n_controls = row.n_controls,
            n_excluded_from_controls = row.n_excl_from_ctrls
        )

        session.add(outcome)

    return dict(
        gene = args.gene,
        variance_pct = args.pct_variance,
        outcome_id = outcome.id,
        p = row.p,

        resid_deviance_base = row.resid_deviance_base,
        resid_deviance_augmented = row.resid_deviance_augmented,
        deviance = row.deviance
    )
