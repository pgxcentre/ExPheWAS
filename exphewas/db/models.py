"""
Database models to store the results of ExPheWas analysis.
"""

from collections import defaultdict
from itertools import product

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import literal, union
from sqlalchemy.orm import relationship, foreign, joinedload, undefer
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Enum, Float, Boolean,
    ForeignKeyConstraint, Date, JSON, and_, cast
)

import scipy.stats
import numpy as np
import pandas as pd

from .engine import Session
from .utils import (
    ANALYSIS_SUBSETS, ANALYSIS_TYPES, _get_table_name, _get_class_name
)


AnalysisEnum = Enum(*ANALYSIS_TYPES, name="enum_analysis_type")
SexSubsetEnum = Enum(*ANALYSIS_SUBSETS,
                     name="enum_sex_subset")
BiotypeEnum = Enum("lincRNA", "protein_coding", name="enum_biotype")


Base = declarative_base()


# These will be filled dynamically.
RESULTS_CLASSES = []
RESULTS_CLASS_MAP = defaultdict(dict)
MODEL_FIT_CLASSES = []
MODEL_FIT_CLASS_MAP = defaultdict(dict)


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


class EnrichmentContingency(Base):
    __tablename__ = "enrichment_contingency"

    outcome_id = Column(String, primary_key=True)
    analysis_type = Column(AnalysisEnum, primary_key=True)
    analysis_subset = Column(SexSubsetEnum, primary_key=True)

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

    def __repr__(self):
        return "<{}: '{}' ({}) - {}>".format(
            self.__class__.__name__,
            self.id,
            self.analysis_type,
            self.label
        )

    def is_continuous(self):
        return self.analysis_type == "CONTINUOUS_VARIABLE"

    def is_binary(self):
        return not self.is_continuous()

    def query_results(self, *args, **kwargs):
        return self.query_outcome_results(self, *args, **kwargs)

    @staticmethod
    def query_outcome_results(outcome, analysis_subset="BOTH",
                              preload_model=False):
        """Build a sqlalchemy query to get results for a given outcome."""
        session = Session()

        result_class_map = RESULTS_CLASS_MAP[analysis_subset]

        Result = None
        if outcome.is_binary():
            Result = result_class_map[outcome.analysis_type]
        elif outcome.is_continuous():
            Result = result_class_map["CONTINUOUS_VARIABLE"]

        query = session.query(Result)\
            .filter_by(
                outcome_id=outcome.id,
                analysis_type=outcome.analysis_type,
            )

        if preload_model:
            query.options(undefer("model_fit"))

        query.options(joinedload(Result.outcome_obj))
        query.options(joinedload(Result.gene_obj))

        return query


class ModelFitMixin(object):
    outcome_id = Column(String, primary_key=True)

    @declared_attr
    def gene(cls):
        return Column(String, ForeignKey("genes.ensembl_id"), primary_key=True)

    def model_fit_df(self):
        return pd.DataFrame(self.model_fit)

    @declared_attr
    def model_fit(cls):
        return Column(JSON)


class ResultMixin(object):
    static_nlog10p = Column(Float)

    # This is not a FK because the pair of (outcome_id, analysis_type) forms
    # the key, but analysis type is not stored in the DB for performance
    # reasons.
    # Also note that analysis_type is defined by subclasses.
    # There is no formal relationship between subclasses of ResultMixin and
    # Outcome, but we do provide utilities to join with outcomes.
    outcome_id = Column(String, primary_key=True)

    @declared_attr
    def gene(cls):
        return Column(String, ForeignKey("genes.ensembl_id"), primary_key=True)

    @declared_attr
    def gene_obj(cls):
        # TODO back_populates
        return relationship("Gene", lazy="joined")

    @declared_attr
    def outcome_obj(cls):
        return relationship(
            "Outcome",
            lazy="joined",
            primaryjoin=lambda: and_(
                foreign(cls.outcome_id) == Outcome.id,
                cls.analysis_type == Outcome.analysis_type
            )
        )

    @declared_attr
    def model_fit(cls):
        return relationship(
            cls.model_fit_cls,
            primaryjoin=lambda: and_(
                foreign(cls.outcome_id) == cls.model_fit_cls.outcome_id,
                foreign(cls.gene) == cls.model_fit_cls.gene
            ),
            viewonly=True
        )

    def p(self):
        return None

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

    def to_object(self):
        """Serialize using only primitive types (e.g. to json dump)."""
        return {
            "gene": self.gene,
            "nlog10p": self.static_nlog10p,
            "outcome_id": self.outcome_id,
            "outcome_label": self.outcome_obj.label,
            "analysis_type": self.analysis_type,
            "analysis_subset": self.analysis_subset,
        }


class ContinuousResult(ResultMixin):
    n = Column(Integer, nullable=False)

    rss_base = Column(Float)
    rss_augmented = Column(Float)
    n_params_base = Column(Integer)
    n_params_augmented = Column(Integer)

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
        return self.f_stat_primitive(
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


class BinaryResult(ResultMixin):
    n_cases = Column(Integer)
    n_controls = Column(Integer)
    n_excluded_from_controls = Column(Integer, default=0)

    deviance_base = Column(Float)
    deviance_augmented = Column(Float)

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


class Gene(Base):
    __tablename__ = "genes"

    ensembl_id = Column(String, primary_key=True)
    name = Column(String)

    chrom = Column(String(2))
    start = Column(Integer)
    end = Column(Integer)
    positive_strand = Column(Boolean)
    description = Column(String)
    biotype = Column(BiotypeEnum)
    has_results = Column(Boolean)

    n_pcs_obj = relationship(
        "GeneNPcs", uselist=False, back_populates="gene",
        lazy="joined"
    )

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


def dynamically_create_results_classes():
    """Dynamically create results classes."""
    for analysis_type, analysis_subset in product(ANALYSIS_TYPES,
                                                  ANALYSIS_SUBSETS):
        class_name = _get_class_name(analysis_subset, analysis_type)
        table_name = _get_table_name(analysis_subset, analysis_type)

        model_fit_class_name = f"{class_name}ModelFit"
        model_fit_table_name = f"{table_name}_model_fit"

        if analysis_type == "CONTINUOUS_VARIABLE":
            parent_class = ContinuousResult
        else:
            parent_class = BinaryResult

        # Create model fit class.
        fit_cls = type(
            model_fit_class_name,
            (ModelFitMixin, Base),
            {
                "__tablename__": model_fit_table_name
            }
        )
        globals()[class_name] = fit_cls

        # Create results class.
        cls = type(
            class_name,
            (parent_class, Base),
            {
                "__tablename__": table_name,
                "analysis_subset": analysis_subset,
                "analysis_type": analysis_type,
                "model_fit_cls": fit_cls
            }
        )

        # The result classes
        globals()[class_name] = cls
        RESULTS_CLASSES.append(cls)
        RESULTS_CLASS_MAP[analysis_subset][analysis_type] = cls

        # The model fit classes
        globals()[model_fit_class_name] = fit_cls
        MODEL_FIT_CLASSES.append(fit_cls)
        MODEL_FIT_CLASS_MAP[analysis_subset][analysis_type] = fit_cls


dynamically_create_results_classes()


def get_results_class(analysis_type, analysis_subset="BOTH"):
    """Returns the result class."""
    return RESULTS_CLASS_MAP[analysis_subset][analysis_type]


def get_model_fit_class(analysis_type, analysis_subset="BOTH"):
    """Returns the model fit class."""
    return MODEL_FIT_CLASS_MAP[analysis_subset][analysis_type]


def all_results_union(session, cols=None):
    """Returns a sqlalchemy query unioning the binary and continuous results.

    By default, this only uses outcome_id, analysis_type and analysis_subset.
    Note that analysis subset always get added to the list of columns.

    """
    if cols is None:
        cols = ["outcome_id"]

    # Making sure analysis_subset isn't in the list
    cols = [
        col for col in cols if col not in {"analysis_subset", "analysis_type"}
    ]

    # The list of queries
    queries = []

    # The binary and continuous variables
    for analysis_subset, d in RESULTS_CLASS_MAP.items():
        for analysis_type, cls in d.items():
            queries.append(session.query(
                *[getattr(cls, col).label(col) for col in cols],
                cast(literal(analysis_type).label("analysis_type"), AnalysisEnum),
                cast(literal(analysis_subset).label("analysis_subset"), SexSubsetEnum),
            ).distinct())

    return union(*queries)
