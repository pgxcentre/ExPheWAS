"""
Database models to store the results of ExPheWas analysis.
"""

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import select
from sqlalchemy.orm import column_property, relationship, deferred
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

    outcome_id = Column(String, primary_key=True)
    analysis_type = Column(AnalysisEnum, primary_key=True)

    # This could be a code from Hierarchy (e.g. ATC codes).
    gene_set_id = Column(String, primary_key=True)
    hierarchy_id = Column(String, nullable=True)

    set_size = Column(Integer, nullable=True)
    enrichment_score = Column(Float, nullable=True)

    p = Column(Float, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            [outcome_id, analysis_type],
            ["outcomes.id", "outcomes.analysis_type"]
        ),
    )

    def get_data_dict(self):
        return {
            "p": self.p,
            "set_size": self.set_size,
            "enrichment_score": self.enrichment_score,
        }


class EnrichmentContingency(Base):
    __tablename__ = "enrichment_contingency"

    outcome_id = Column(String, primary_key=True)
    analysis_type = Column(AnalysisEnum, primary_key=True)

    # This could be a code from Hierarchy (e.g. ATC codes).
    gene_set_id = Column(String, primary_key=True)

    hierarchy_id = Column(String, nullable=True)

    n00 = Column(Integer, nullable=False)
    n01 = Column(Integer, nullable=False)
    n10 = Column(Integer, nullable=False)
    n11 = Column(Integer, nullable=False)

    p = Column(Float, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            [outcome_id, analysis_type],
            ["outcomes.id", "outcomes.analysis_type"]
        ),
    )

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

    def __repr__(self):
        return "<{}: '{}' ({}) - {}>".format(
            self.__class__.__name__,
            self.id,
            self.analysis_type,
            self.label
        )


class BinaryOutcome(Outcome):
    __tablename__ = "binary_outcomes"

    id = Column(String, primary_key=True)
    analysis_type = Column(AnalysisEnum, primary_key=True)

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
    analysis_type = Column(AnalysisEnum, primary_key=True)

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

    outcome_id = Column(String, primary_key=True)
    analysis_type = Column(AnalysisEnum, primary_key=True)

    static_nlog10p = Column(Float)

    def model_fit_df(self):
        return pd.DataFrame(self.model_fit)

    @declarative_base
    def model_fit(cls):
        return deferred(Column(JSON))

    @declared_attr
    def gene(cls):
        return Column(String, ForeignKey("genes.ensembl_id"), primary_key=True)

    @declared_attr
    def gene_obj(cls):
        return relationship("Gene")

    @declared_attr
    def outcome_obj(cls):
        return relationship("Outcome", lazy="joined")

    def p(self):
        return None

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                [cls.outcome_id, cls.analysis_type],
                ["outcomes.id", "outcomes.analysis_type"]
            ),
        )

    def to_object(self):
        """Serialize using only primitive types (e.g. to json dump)."""
        return {
            "gene": self.gene,
            "analysis_subset": self.analysis_subset,
            "nlog10p": self.static_nlog10p,
            "outcome_id": self.outcome_id,
            "outcome_label": self.outcome_obj.label,
            "analysis_type": self.analysis_type
        }

    def __repr__(self):
        try:
            p = self.p()
            p = "{:.2g}".format(p)
        except:
            p = "?"

        return "<{} - {}:{} / {}; p={}>".format(
            self.__class__.__name__,
            self.analysis_type,
            self.outcome_id,
            self.gene,
            p
        )


class ContinuousVariableResult(Base, ResultMixin):
    __tablename__ = "results_continuous_variables"

    n = Column(Integer, nullable=False)

    rss_base = Column(Float)
    rss_augmented = Column(Float)
    n_params_base = Column(Integer)
    n_params_augmented = Column(Integer)

    discriminator = Column("type", String(50))
    __mapper_args__ = {"polymorphic_on": discriminator}

    def to_object(self):
        o = super().to_object()
        keys = ["n", "rss_base", "rss_augmented",
                "n_params_base", "n_params_augmented"]
        o.update({k: getattr(self, k) for k in keys})
        return o

    @staticmethod
    def f_stat_primitive(rss_base, rss_augmented, n, n_params_base,
                         n_params_augmented):
        rss1 = rss_base
        rss2 = rss_augmented
        p1 = n_params_base
        p2 = n_params_augmented

        return (rss1 - rss2) / (p2 - p1) * ((n - p2) / rss2)

    def f_stat(self):
        return self.f_stat_static(
            self.rss_base, self.rss_augmented,
            self.n,
            self.n_params_base, self.n_params_augmented
        )

    def p(self):
        return scipy.stats.f.sf(
            self.f_stat(),
            self.n_params_augmented - self.n_params_base,
            self.n - self.n_params_augmented
        )

    @classmethod
    def nlog10p_primitive(cls, rss_base, rss_augmented, n, n_params_base,
                          n_params_augmented):
        f = cls.f_stat_primitive(rss_base, rss_augmented, n, n_params_base,
                                 n_params_augmented)

        return scipy.stats.f.logsf(
            f,
            n_params_augmented - n_params_base,
            n - n_params_augmented
        ) / -np.log(10)


    def nlog10p(self):
        return self.nlog10p_primitive(
            self.rss_base, self.rss_augmented,
            self.n,
            self.n_params_base, self.n_params_augmented
        )


class BinaryVariableResult(Base, ResultMixin):
    __tablename__ = "results_binary_variables"

    n_cases = Column(Integer)
    n_controls = Column(Integer)
    n_excluded_from_controls = Column(Integer, default=0)

    deviance_base = Column(Float)
    deviance_augmented = Column(Float)

    discriminator = Column("type", String(50))
    __mapper_args__ = {"polymorphic_on": discriminator}

    def to_object(self):
        o = super().to_object()
        keys = ["n_cases", "n_controls", "n_excluded_from_controls",
                "deviance_base", "deviance_augmented"]
        o.update({k: getattr(self, k) for k in keys})
        return o

    def p(self):
        # Get the number of PCs (difference in number of parameters).
        return scipy.stats.chi2.sf(
            self.deviance_base - self.deviance_augmented,
            df=self.gene_obj.n_pcs
        )

    @staticmethod
    def nlog10p_primitive(deviance_base, deviance_augmented, n_pcs):
        return scipy.stats.chi2.logsf(
            deviance_base - deviance_augmented,
            df=n_pcs
        ) / -np.log(10)

    def nlog10p(self):
        return self.nlog10p_primitive(
            self.deviance_base, self.deviance_augmented,
            self.gene_obj.n_pcs
        )


def all_results_union(session, cols=None):
    """Returns a sqlalchemy query unioning the binary and continuous results.

    By default, this only uses outcome_id, analysis_type and analysis_subset.

    """
    if cols is None:
        cols = ["outcome_id", "analysis_type", "analysis_subset"]

    bin_fields = [getattr(BinaryVariableResult, i).label(i) for i in cols]
    con_fields = [getattr(ContinuousVariableResult, i).label(i) for i in cols]

    return session.query(*bin_fields).union(
        session.query(*con_fields)
    )


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
        ),
        viewonly=True
    )


    def __repr__(self):
        return f"<Drug '{self.who_name}' {self.atc5}>"


class TargetToUniprot(Base):
    __tablename__ = "target_uniprot"

    target_atc5 = Column(String, ForeignKey("chembl_drugs.atc5"),
                         primary_key=True)
    uniprot = Column(String, primary_key=True)

    action_type = Column(String)

    genes = relationship(
        "Gene",
        secondary=XRefs.__table__,
        primaryjoin=(
            "and_(XRefs.external_db_id == -1, "
            "XRefs.external_id == TargetToUniprot.uniprot)"
        ),
        secondaryjoin=(
            "XRefs.ensembl_id == Gene.ensembl_id"
        ),
        viewonly=True
    )
