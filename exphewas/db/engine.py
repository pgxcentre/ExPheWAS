import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


DEBUG = os.environ.get("EXPHEWAS_DEBUG", False)


ENGINE = create_engine("sqlite:///gene_phewas.db", echo=DEBUG)


Session = sessionmaker(bind=ENGINE)
