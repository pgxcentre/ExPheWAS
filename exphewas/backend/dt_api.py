"""
Flask-based API specific for datatables.
"""


from flask import Blueprint, jsonify, request

from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.postgresql import array
from sqlalchemy import or_

from datatables import DataTable

from .cache import Cache

from ..db import models
from ..db.engine import Session


dt_api = Blueprint("dt_api_blueprint", __name__)


# Datatables serverprocessing endpoints.
@dt_api.route("/gene")
def dt_gene():
    session = Session()

    # genes_with_results = Cache().get("genes_with_results")
    # q = session.query(models.Gene)\
    #     .filter(models.Gene.ensembl_id.in_(genes_with_results))
    q = session.query(models.Gene)

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
