"""
Database models to store the results of exPheWAS analysis.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select
from sqlalchemy.orm import column_property
from sqlalchemy import (
    Table, Column, Integer, String, MetaData, ForeignKey, Enum, Float,
    Boolean, Sequence, UniqueConstraint, ForeignKeyConstraint, create_engine
)

from .engine import ENGINE


ANALYSIS_TYPES = [
    "ICD10_3CHAR", "ICD10_BLOCK", "ICD10_RAW", "CONTINUOUS_VARIABLE",
    "SELF_REPORTED", "CV_ENDPOINTS"
]


AnalysisEnum = Enum(*ANALYSIS_TYPES, name="enum_analysis_type")


Base = declarative_base()


# Unmapped tables
ensembl_uniprot = Table(
    "ensembl_uniprot", Base.metadata,
    Column("ensembl_id", ForeignKey("genes.ensembl_id"), primary_key=True),
    Column("uniprot_id", String, primary_key=True)
)


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)

    analysis_type = Column(AnalysisEnum, nullable=False)

    type = Column(String(20))

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "outcomes"
    }


class BinaryOutcome(Outcome):
    __tablename__ = "binary_outcomes"

    id = Column(String, ForeignKey("outcomes.id"), primary_key=True)

    n_cases = Column(Integer)
    n_controls = Column(Integer)
    n_excluded_from_controls = Column(Integer, default=0)

    __mapper_args__ = {
        "polymorphic_identity": "binary_outcomes"
    }


class ContinuousOutcome(Outcome):
    __tablename__ = "continuous_outcomes"

    id = Column(String, ForeignKey("outcomes.id"), primary_key=True)

    n = Column(Integer)

    __mapper_args__ = {
        "polymorphic_identity": "continuous_outcomes"
    }


class ContinuousVariableResult(Base):
    __tablename__ = "results_continuous_variables"

    gene = Column(String, primary_key=True)
    variance_pct = Column(Integer, primary_key=True)
    outcome_id = Column(String, primary_key=True)

    p = Column(Float, nullable=False)
    rss_base = Column(Float)
    rss_augmented = Column(Float)
    sum_of_sq = Column(Float)
    F_stat = Column(Float)


class BinaryVariableResult(Base):
    __tablename__ = "results_binary_variables"

    gene = Column(String, primary_key=True)
    variance_pct = Column(Integer, primary_key=True)
    outcome_id = Column(String, primary_key=True)

    p = Column(Float, nullable=False)
    resid_deviance_base = Column(Float)
    resid_deviance_augmented = Column(Float)
    deviance = Column(Float)


class GeneVariance(Base):
    __tablename__ = "gene_variance"

    ensembl_id = Column(
        String, ForeignKey("genes.ensembl_id"), primary_key=True
    )
    variance_pct = Column(Integer, primary_key=True)
    n_components = Column(Integer, nullable=False)

    def __init__(self, ensg, variance_pct, n_components):
        self.ensembl_id = ensg
        self.variance_pct = variance_pct
        self.n_components = n_components


class Gene(Base):
    __tablename__ = "genes"

    ensembl_id = Column(String, primary_key=True)
    name = Column(String)

    chrom = Column(String(2))
    start = Column(Integer)
    end = Column(Integer)
    positive_strand = Column(Boolean)

    # An alternative to this is to use a regular property and to 
    # use object_session(self) to execute arbitrary queries.
    uniprot_ids = column_property(
        select([ensembl_uniprot.c.uniprot_id])\
            .where(ensembl_uniprot.c.ensembl_id == ensembl_id)
    )

    def __repr__(self):
        return "<Gene: {} - {}:{}-{} ({})>".format(
            self.ensembl_id,
            self.chrom, self.start, self.end,
            "+" if self.positive_strand else "-"
        )
