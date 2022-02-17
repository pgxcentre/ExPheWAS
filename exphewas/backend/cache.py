"""
Disk-based caching for ExPheWas.
"""

import os
import json
import sys

from sqlalchemy.sql.expression import func

from .config import CACHE_DIR
from ..db import models
from ..db.engine import Session


def path_to(name):
    """Return the path to a given cache file."""
    return os.path.join(CACHE_DIR, name)


class Cache(object):
    """Cache object."""
    # pylint: disable=missing-function-docstring
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
    """Create or load the startup cache (outcome)."""
    cache = Cache()
    session = Session()

    if not cache.has("outcomes"):
        print("Creating cache for outcomes")
        cache_outcomes(cache, session)


def cache_outcomes(cache, session):
    """Cache outcomes with results."""
    q = models.all_results_union(session).subquery()

    results = session.query(
        models.Outcome,
        func.array_agg(
            q.c.analysis_subset
        ).label("available_subsets"))\
        .filter(
            models.Outcome.iid == q.c.outcome_iid,
            models.Outcome.analysis_type == q.c.analysis_type
        )\
        .group_by(
            models.Outcome.iid,
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


def cache_gene_with_results():
    """Cache genes with results (setting `has_results` to True)."""
    print("Finding genes with results", file=sys.stderr)
    session = Session()

    # Retrieving all the genes with results
    all_genes = session.query(models.RESULTS_CLASSES[0].gene_iid)
    for result_obj in models.RESULTS_CLASSES[1:]:
        all_genes = all_genes.union(session.query(result_obj.gene_iid))

    # Setting has_results to true for these genes
    for gene in all_genes.all():
        gene_obj = session.query(models.Gene)\
            .filter(models.Gene.iid == gene[0])\
            .one()
        gene_obj.has_results = True

    session.commit()


def clear_cache_gene_with_results():
    """Clear cache genes with results (setting `has_results` to False)."""
    print("Clearing genes with results", file=sys.stderr)
    session = Session()

    # Resetting the cache
    genes = session.query(models.Gene)
    for gene in genes.all():
        gene.has_results = False
    session.commit()
