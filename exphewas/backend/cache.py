"""
Disk-based caching for ExPheWas.
"""

import os
import json

from sqlalchemy.sql.expression import func
from sqlalchemy import and_

from .config import CACHE_DIR
from ..db import models
from ..db.engine import Session


def path_to(name):
    return os.path.join(CACHE_DIR, name)


class Cache(object):
    def __init__(self):
        print(f"Using '{CACHE_DIR}' as data cache.")

    def put(self, name, data):
        with open(path_to(name), "w") as f:
            json.dump(data, f)

    def get(self, name):
        with open(path_to(name), "r") as f:
            return json.load(f)

    def has(self, name):
        try:
            with open(path_to(name), "r"):
                return True
        except:
            return False

    def clear(self):
        for filename in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, filename))
        print("Cache cleared.")


# Create the data caches.
def create_or_load_startup_caches():
    cache = Cache()
    session = Session()

    if not cache.has("genes_with_results"):
        print("Creating cache for genes")
        cache_gene_with_results(cache, session)

    if not cache.has("outcomes"):
        print("Creating cache for outcomes")
        cache_outcomes(cache, session)


def cache_outcomes(cache, session):
    q = models.all_results_union(session).subquery()

    results = session.query(
        models.Outcome,
        func.array_agg(
            q.c.analysis_subset
        ).label("available_subsets"))\
        .filter(
            models.Outcome.id==q.c.outcome_id,
            models.Outcome.analysis_type==q.c.analysis_type
        )\
        .group_by(
            models.Outcome.id,
            models.Outcome.analysis_type
        )

    results = [
        {
            "id": o.id,
            "type": "binary_outcomes" if o.is_binary() else "continuous_outcomes",
            "analysis_type": o.analysis_type,
            "label": o.label,
            "available_subsets": availables,
        } for o, availables in results
    ]

    cache.put("outcomes", results)


def cache_gene_with_results(cache, session):
    all_genes = session.query(models.RESULTS_CLASSES[0].gene)
    for result_obj in models.RESULTS_CLASSES[1:]:
        all_genes = all_genes.union(session.query(result_obj.gene))
    cache.put("genes_with_results", [tu[0] for tu in all_genes.all()])
