from sqlalchemy.orm.exc import NoResultFound
from ..engine import Session
from ..models import Metadata


def main(args):
    session = Session()

    # Check if there is already a metadata.
    try:
        cur = session.query(Metadata).one()
    except NoResultFound:
        # We need to create all fields.
        cur = None

    if args.view:
        if cur is None:
            print("There is no metadata for the results database.")
        else:
            print(cur)

        return

    kwargs = {}
    if cur is not None:
        kwargs.update(cur.metadata_dict())

    for field in ("version", "date", "comments"):
        if getattr(args, field) is not None:
            kwargs[field] = getattr(args, field)

    new = Metadata(**kwargs)

    # Delete the old metadata.
    if cur is not None:
        session.delete(cur)

    session.add(new)
    session.commit()
    print("New metadata has been set.")
    print(new)


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
