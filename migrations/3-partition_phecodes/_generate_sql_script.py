#!/usr/bin/env python

import itertools

from exphewas.db.models import RESULTS_CLASS_MAP, RESULTS_CLASSES
from exphewas.db.engine import Session

import numpy as np
from jinja2 import Template


PHECODES_CLASSES = set()
for analysis_subgroup, d in RESULTS_CLASS_MAP.items():
    for analysis_type, cls in d.items():
        if analysis_type == "PHECODES":
            PHECODES_CLASSES.add(cls)


def pairwise(iterable):
    """Shim for itertools.pairwise (new in python 3.10)."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


pairwise = getattr(itertools, "pairwise", pairwise)


with open("create_partition_template.jsql", "rt") as f:
    SQL_TEMPLATE = f.read()


with open("3-partition_phecodes.sql", "wt") as f:
    for Result in RESULTS_CLASSES:
        ids = Session().query(
            getattr(Result, "outcome_iid")
        ).distinct()
        ids = np.array([id[0] for id in ids])

        if Result in PHECODES_CLASSES:
            # Deciles for phecodes because it is large.
            bounds = np.round(
                np.percentile(ids, [10, 20, 30, 40, 50, 60, 70, 80, 90])
            ).astype(int)
        else:
            # Quartiles is enough for most.
            bounds = np.round(np.percentile(ids, [25, 50, 75])).astype(int)

        bounds = pairwise(itertools.chain(
            ["MINVALUE"], bounds, ["MAXVALUE"]
        ))

        bounds = [(i + 1, l, r) for i, (l, r) in enumerate(bounds)]

        sql = Template(SQL_TEMPLATE).render(
            table=Result.__tablename__,
            bounds=bounds
        )

        f.write(sql)
        f.write("\n")
