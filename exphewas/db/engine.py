import sys
import os

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine


# Set the DEBUG variable.
dbg = os.environ.get("EXPHEWAS_DEBUG", "false")
if dbg.lower() in ("true", "1"):
    DEBUG = True
else:
    DEBUG = False
del dbg


# Get the database connection URL as described here:
# https://docs.sqlalchemy.org/en/13/core/engines.html
#
# For exemple, to use postgres as the backend, define the following
# environment variable:
# EXPHEWAS_DATABASE_URL=postgresql+psycopg2://user:pwd@localhost/mydatabase
#
# By default, this will use a file-based sqlite database.
EXPHEWAS_DATABASE_URL = os.environ.get(
    "EXPHEWAS_DATABASE_URL", "sqlite:///gene_phewas.db"
)


if DEBUG:
    print(f"[DEBUG] Creating engine with url {EXPHEWAS_DATABASE_URL}",
          file=sys.stderr)

ENGINE = create_engine(EXPHEWAS_DATABASE_URL, echo=DEBUG, pool_pre_ping=True)


Session = scoped_session(sessionmaker(bind=ENGINE))
