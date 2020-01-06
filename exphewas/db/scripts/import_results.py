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

    df = pd.read_csv(args.filename)

    if "sum_of_sq" in df.columns:
        create_object = _process_continuous_result

    elif "deviance" in  df.columns:
        create_object = _process_binary_result

    else:
        raise ValueError("Could not infer analysis type.")

    # For every line:
    # 1. Get or create Outcome.
    # 2. Create Result.
    objects = []
    for i, row in df.iterrows():
        objects.append(create_object(row, args, session))

    session.add_all(objects)
    session.commit()


def _process_continuous_result(row, args, session):
    # Get or create outcome.
    try:
        outcome = session.query(ContinuousOutcome)\
            .filter_by(id=row.outcome_id).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = ContinuousOutcome(
            id = row.outcome_id,
            label = row.outcome_label
        )

        session.add(outcome)

    result = ContinuousVariableResult(
        gene = args.gene,
        variance_pct = args.pct_variance,
        analysis = args.analysis,
        outcome_id = outcome.id,
        p = row.p,

        rss_base = row.rss_base,
        rss_augmented = row.rss_augmented,
        sum_of_sq = row.sum_of_sq,
        F_stat = row.F_stat
    )

    return result


def _process_binary_result(row, args, session):
    # Get or create outcome.
    try:
        outcome = session.query(BinaryOutcome)\
            .filter_by(id=row.outcome_id).one()

    except sqlalchemy.orm.exc.NoResultFound:
        outcome = BinaryOutcome(
            id = row.outcome_id,
            label = row.outcome_label,
            n_cases = row.n_cases,
            n_controls = row.n_controls,
            n_excluded_from_controls = row.n_excl_from_ctrls
        )

        session.add(outcome)

    result = BinaryVariableResult(
        gene = args.gene,
        variance_pct = args.pct_variance,
        analysis = args.analysis,
        outcome_id = outcome.id,
        p = row.p,

        resid_deviance_base = row.resid_deviance_base,
        resid_deviance_augmented = row.resid_deviance_augmented,
        deviance = row.deviance
    )

    return result
