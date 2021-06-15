"""
Flask-based API specific for datatables.
"""


from flask import Blueprint, jsonify, request

from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.postgresql import array
from sqlalchemy import or_

from datatables import DataTable

from ..db import models
from ..db.engine import Session


dt_api = Blueprint("dt_api_blueprint", __name__)


_gene_cache = None
def get_genes_with_results():
    global _gene_cache

    if _gene_cache is None:
        session = Session()

        cont = session.query(models.ContinuousVariableResult.gene)
        bin = session.query(models.BinaryVariableResult.gene)

        _gene_cache = [tu[0] for tu in cont.union(bin).all()]

    return _gene_cache
get_genes_with_results()  # Preload cache


# Datatables serverprocessing endpoints.
@dt_api.route("/gene")
def dt_gene():
    session = Session()

    q = session.query(models.Gene)\
        .filter(models.Gene.ensembl_id.in_(get_genes_with_results()))

    table = DataTable(
        request.args,
        models.Gene,
        q,
        [ # columns
            "ensembl_id",
            "name",
            "description",
            "biotype",
            "chrom",
            "start",
            "end",
            "positive_strand"
        ]
    )

    table.searchable(perform_search)

    return table.json()


def perform_search(queryset, user_input):
    return queryset.filter(
        or_(
            models.Gene.ensembl_id.ilike(f"{user_input}%".lower()),
            models.Gene.name.ilike(f"{user_input}%".lower()),
            models.Gene.description.ilike(f"%{user_input}%".lower()),
        )
    )
