"""
Database models to store the results of ExPheWas analysis.
"""

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import select
from sqlalchemy.orm import column_property, relationship
from sqlalchemy import (
    Table, Column, Integer, String, MetaData, ForeignKey, Enum, Float,
    Boolean, Sequence, UniqueConstraint, ForeignKeyConstraint, create_engine,
    and_, PrimaryKeyConstraint, Date, JSON
)

import scipy.stats
import numpy as np
import pandas as pd

from .engine import ENGINE, Session


ANALYSIS_TYPES = [
    "PHECODES", "CONTINUOUS_VARIABLE", "SELF_REPORTED", "CV_ENDPOINTS"
]


AnalysisEnum = Enum(*ANALYSIS_TYPES, name="enum_analysis_type")
SexSubsetEnum = Enum("BOTH", "FEMALE_ONLY", "MALE_ONLY",
                     name="enum_sex_subset")


Base = declarative_base()


class Metadata(Base):
    __tablename__ = "meta"

    version = Column(String, primary_key=True)
    date = Column(Date)
    comments = Column(String)

    def metadata_dict(self):
        return {
            "version": self.version,
            "date": self.date,
            "comments": self.comments,
        }

    def __repr__(self):
        return f"<Metadata v{self.version} - {self.date} // {self.comments}>"


class Enrichment(Base):
    __tablename__ = "enrichment"

    outcome_id = Column(String, ForeignKey("outcomes.id"), primary_key=True)

    # This could be a code from Hierarchy (e.g. ATC codes).
    gene_set_id = Column(String, primary_key=True)
    hierarchy_id = Column(String, nullable=True)

    set_size = Column(Integer, nullable=True)
    enrichment_score = Column(Float, nullable=True)

    p = Column(Float, nullable=False)

    def get_data_dict(self):
        return {
            "p": self.p,
            "set_size": self.set_size,
            "enrichment_score": self.enrichment_score,
        }


class EnrichmentContingency(Base):
    __tablename__ = "enrichment_contingency"

    outcome_id = Column(String, ForeignKey("outcomes.id"), primary_key=True)

    # This could be a code from Hierarchy (e.g. ATC codes).
    gene_set_id = Column(String, primary_key=True)

    hierarchy_id = Column(String, nullable=True)

    n00 = Column(Integer, nullable=False)
    n01 = Column(Integer, nullable=False)
    n10 = Column(Integer, nullable=False)
    n11 = Column(Integer, nullable=False)

    p = Column(Float, nullable=False)

    def get_data_dict(self):
        return {
            "p": self.p,
            "n00": self.n00,
            "n01": self.n01,
            "n10": self.n10,
            "n11": self.n11,
        }


class Hierarchy(Base):
    __tablename__ = "hierarchy"

    DEFAULT_PARENT = "_ROOT_"

    # A textual ID for the hierarchy (e.g. ICD10, UKB_SELF_REPORT)
    id = Column(String, primary_key=True)

    code = Column(String, primary_key=True)
    parent = Column(
        String,
        server_default=DEFAULT_PARENT,
        default=DEFAULT_PARENT,
        primary_key=True
    )

    description = Column(String)


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(String, primary_key=True)
    analysis_type = Column(AnalysisEnum, primary_key=True)
    label = Column(String, nullable=False)
    type = Column(String)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "outcomes"
    }


class BinaryOutcome(Outcome):
    __tablename__ = "binary_outcomes"

    id = Column(String, primary_key=True)
    analysis_type = Column(String, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            [id, analysis_type],
            ["outcomes.id", "outcomes.analysis_type"]
        ),
    )

    __mapper_args__ = {
        "polymorphic_identity": "binary_outcomes"
    }


class ContinuousOutcome(Outcome):
    __tablename__ = "continuous_outcomes"

    id = Column(String, primary_key=True)
    analysis_type = Column(String, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            [id, analysis_type],
            ["outcomes.id", "outcomes.analysis_type"]
        ),
    )

    __mapper_args__ = {
        "polymorphic_identity": "continuous_outcomes"
    }


class ResultMixin(object):
    analysis_subset = Column(SexSubsetEnum, primary_key=True)
    model_fit = Column(JSON)

    outcome_id = Column(String, primary_key=True)
    analysis_type = Column(String, primary_key=True)

    def model_fit_df(self):
        return pd.DataFrame(self.model_fit)

    @declared_attr
    def gene(cls):
        return Column(String, ForeignKey("genes.ensembl_id"), primary_key=True)

    @declared_attr
    def gene_obj(cls):
        return relationship("Gene")

    @declared_attr
    def outcome_obj(cls):
        return relationship("Outcome")

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                [cls.outcome_id, cls.analysis_type],
                ["outcomes.id", "outcomes.analysis_type"]
            ),
        )

    def p(self):
        return None

    def __repr__(self):
        return "<{} - {}:{} / {}; p={:.2g}>".format(
            self.__class__.__name__,
            self.analysis_type,
            self.outcome_id,
            self.gene,
            self.p()
        )


class ContinuousVariableResult(Base, ResultMixin):
    __tablename__ = "results_continuous_variables"

    n = Column(Integer, nullable=False)

    rss_base = Column(Float)
    rss_augmented = Column(Float)
    n_params_base = Column(Integer)
    n_params_augmented = Column(Integer)

    def f_stat(self):
        rss1 = self.rss_base
        rss2 = self.rss_augmented
        n = self.n
        p1 = self.n_params_base
        p2 = self.n_params_augmented

        return (rss1 - rss2) / (p2 - p1) * ((n - p2) / rss2)

    def p(self):
        return scipy.stats.f.sf(
            self.f_stat(),
            self.n_params_augmented - self.n_params_base,
            self.n - self.n_params_augmented
        )

    def nlog10p(self):
        return scipy.stats.f.logsf(
            self.f_stat(),
            self.n_params_augmented - self.n_params_base,
            self.n - self.n_params_augmented
        ) / -np.log(10)


class BinaryVariableResult(Base, ResultMixin):
    __tablename__ = "results_binary_variables"

    n_cases = Column(Integer)
    n_controls = Column(Integer)
    n_excluded_from_controls = Column(Integer, default=0)

    deviance_base = Column(Float)
    deviance_augmented = Column(Float)

    def p(self):
        # Get the number of PCs (difference in number of parameters).
        return scipy.stats.chi2.sf(
            self.deviance_base - self.deviance_augmented,
            df=self.gene_obj.n_pcs
        )

    def nlog10p(self):
        return scipy.stats.chi2.logsf(
            self.deviance_base - self.deviance_augmented,
            df=self.gene_obj.n_pcs
        ) / -np.log(10)


class Gene(Base):
    __tablename__ = "genes"

    ensembl_id = Column(String, primary_key=True)
    name = Column(String)

    chrom = Column(String(2))
    start = Column(Integer)
    end = Column(Integer)
    positive_strand = Column(Boolean)
    description = Column(String)

    n_pcs_obj = relationship("GeneNPcs", uselist=False, back_populates="gene")

    @property
    def n_pcs(self):
        return self.n_pcs_obj.n_pcs_95

    def __repr__(self):
        return "<Gene: {} - {}:{}-{} ({})>".format(
            self.ensembl_id,
            self.chrom, self.start, self.end,
            "+" if self.positive_strand else "-"
        )


class GeneNPcs(Base):
    __tablename__ = "gene_n_pcs"

    ensembl_id = Column(String, ForeignKey("genes.ensembl_id"),
                        primary_key=True)
    n_pcs_95 = Column(Integer, primary_key=True)
    n_variants = Column(Integer)
    pct_explained = Column(Float)

    gene = relationship("Gene", back_populates="n_pcs_obj")


class ExternalDB(Base):
    __tablename__ = "external_db"

    id = Column(Integer, primary_key=True)
    db_name = Column(String, nullable=False)
    db_display_name = Column(String, nullable=False)


class XRefs(Base):
    __tablename__ = "xrefs"

    ensembl_id = Column(String, ForeignKey("genes.ensembl_id"),
                        primary_key=True)
    external_db_id = Column(Integer, ForeignKey("external_db.id"),
                            primary_key=True)
    external_id = Column(String, nullable=False, primary_key=True)


class ChEMBLDrug(Base):
    # TODO Check if 24 or 25 was used and update table name so that we can
    # update this.

    __tablename__ = "chembl_drugs"

    who_name = Column(String)
    atc1 = Column(String(1))
    atc2 = Column(String(3))
    atc3 = Column(String(4))
    atc4 = Column(String(5))
    atc5 = Column(String(7), primary_key=True)

    uniprot_ids = relationship("TargetToUniprot")

    target_genes = relationship(
        "Gene",
        secondary="join(TargetToUniprot, XRefs, "
                  "    and_(TargetToUniprot.uniprot == XRefs.external_id, "
                  "         XRefs.external_db_id == -1))",
        primaryjoin=(
            "ChEMBLDrug.atc5 == TargetToUniprot.target_atc5"
        ),
        secondaryjoin=(
            "XRefs.ensembl_id == Gene.ensembl_id"
        )
    )


    def __repr__(self):
        return f"<Drug '{self.who_name}' {self.atc5}>"


class TargetToUniprot(Base):
    __tablename__ = "target_uniprot"

    target_atc5 = Column(String, ForeignKey("chembl_drugs.atc5"),
                    primary_key=True)
    uniprot = Column(String, primary_key=True)

    action_type = Column(String)

    # genes = relationship(
    #     "Gene",
    #     secondary=XRefs.__table__,
    #     primaryjoin=(
    #         "and_(XRefs.external_db_id == -1, "
    #         "XRefs.external_id == TargetToUniprot.uniprot)"
    #     ),
    #     secondaryjoin=(
    #         "XRefs.ensembl_id == Gene.ensembl_id"
    #     )
    # )
