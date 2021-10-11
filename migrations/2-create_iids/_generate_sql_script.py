#!/usr/bin/env python

import exphewas.db.models

from jinja2 import Template


RESULTS_TABLES = [
    (i.__tablename__, i.analysis_type)
    for i in exphewas.db.models.RESULTS_CLASSES
]


with open("migration_template_jinja2.jsql", "rt") as f:
    sql_template = f.read()

with open("2-create_iids.sql", "wt") as f:
    f.write(Template(sql_template).render(result_tables=RESULTS_TABLES))
