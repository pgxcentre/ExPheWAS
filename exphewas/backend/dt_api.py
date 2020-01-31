"""
Flask-based API specific for datatables.
"""


from flask import Blueprint, jsonify, request

from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.postgresql import array

from datatables import ColumnDT, DataTables

from ..db import models
from ..db.engine import Session


dt_api = Blueprint("dt_api_blueprint", __name__)


# Datatables serverprocessing endpoints.
@dt_api.route("/gene")
def dt_gene():
    columns = [
        ColumnDT(models.Gene.ensembl_id),                               # 0
        ColumnDT("available_variances", global_search=False),           # 1
        ColumnDT(models.Gene.name),                                     # 2
        ColumnDT(models.Gene.description),                              # 3
        ColumnDT(models.Gene.chrom, global_search=False),               # 4
        ColumnDT(models.Gene.start, global_search=False),               # 5
        ColumnDT(models.Gene.end, global_search=False),                 # 6
        ColumnDT(models.Gene.positive_strand, global_search=False),     # 7
    ]

    subquery = Session.query(
        models.AvailableGeneResult.ensembl_id,
        func.array_agg(array([
            models.AvailableGeneResult.variance_pct,
            models.GeneVariance.n_components,
        ])).label("available_variances"),
    ).filter(
        models.GeneVariance.ensembl_id == models.AvailableGeneResult.ensembl_id
    ).filter(
        models.GeneVariance.variance_pct == models.AvailableGeneResult.variance_pct
    ).group_by(models.AvailableGeneResult.ensembl_id).subquery()

    query = Session.query()\
        .select_from(models.Gene)\
        .join(subquery, isouter=True)

    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)

    return jsonify(row_table.output_result())
