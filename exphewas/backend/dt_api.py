"""
Flask-based API specific for datatables.
"""


from flask import Blueprint, request

from sqlalchemy import or_

from datatables import DataTable

from ..db import models
from ..db.engine import Session


dt_api = Blueprint("dt_api_blueprint", __name__)


@dt_api.route("/gene")
def dt_gene():
    """Datatables serverprocessing endpoints for genes."""
    with_results_only = request.args.get("only_with_results", False)

    session = Session()

    q = session.query(models.Gene)

    if with_results_only:
        q = q.filter(models.Gene.has_results.is_(True))

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
            "positive_strand",
            "has_results",
        ]
    )

    table.searchable(perform_search)
    table.searchable_column(column_search)

    return table.json()


def column_search(column, queryset, user_input):
    """Search a particular column."""
    search_string = f"{user_input}%".lower()
    if column is not models.Gene.name:
        search_string = "%" + search_string

    return queryset.filter(column.ilike(search_string))


def perform_search(queryset, user_input):
    """Performs a global search."""
    return queryset.filter(
        or_(
            models.Gene.ensembl_id.ilike(f"{user_input}%".lower()),
            models.Gene.name.ilike(f"{user_input}%".lower()),
            models.Gene.description.ilike(f"%{user_input}%".lower()),
        )
    )
