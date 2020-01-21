"""
Flask-based API specific for datatables.
"""


from flask import Blueprint, jsonify, request

from datatables import ColumnDT, DataTables

from ..db import models
from ..db.engine import Session


dt_api = Blueprint("dt_api_blueprint", __name__)


# Datatables serverprocessing endpoints.
@dt_api.route("/gene")
def dt_gene():
    columns = [
        ColumnDT(models.Gene.ensembl_id),
        ColumnDT(models.Gene.name),
        ColumnDT(models.Gene.chrom),
        ColumnDT(models.Gene.start),
        ColumnDT(models.Gene.end),
        ColumnDT(models.Gene.positive_strand),
    ]

    query = Session.query()\
        .select_from(models.Gene)

    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)

    return jsonify(row_table.output_result())
