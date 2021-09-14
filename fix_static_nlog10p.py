#!/usr/bin/env python
"""Fixes static_nlog10p values for genes with more than 40 PCs."""


import argparse
import logging
import sys
from os import path

from exphewas.db import models
from exphewas.db.engine import Session
from exphewas.db.utils import ANALYSIS_TYPES, ANALYSIS_SUBSETS


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(path.basename(sys.argv[0]))


def main() -> None:  # pylint: disable=missing-docstring
    args = parse_args()

    session = Session()

    # The genes with more than X PCs
    genes = session.query(models.Gene)\
        .join(models.GeneNPcs)\
        .filter(models.GeneNPcs.n_pcs_95 > args.max_n_pcs)\
        .all()

    # Fixing for each gene
    for gene in genes:
        logger.info("Processing %s", gene.ensembl_id)
        assert gene.n_pcs > 40
        fix_gene(gene, session)
        session.commit()
        break


def fix_gene(gene, session):
    """Fixe the gene."""
    for analysis_type in ANALYSIS_TYPES:
        if analysis_type == "CONTINUOUS_VARIABLE":
            # No need to modify, as the nlog10p computation doesn't take into
            # effect the number of PCs
            continue

        logger.info("\t%s", analysis_type)

        for analysis_subset in ANALYSIS_SUBSETS:
            logger.info("\t\t%s", analysis_subset)

            obj = models.get_results_class(analysis_type, analysis_subset)

            results = session.query(obj).filter_by(gene=gene.ensembl_id).all()

            for result in results:
                nlog10p = compute_nlog10p(obj, result, min(gene.n_pcs, 40))
                result.static_nlog10p = nlog10p


def compute_nlog10p(result_class, result, n_pcs):
    """Compute -log10(p) according if it's continuous or binary."""
    assert issubclass(result_class, models.BinaryResult)
    return models.BinaryResult.nlog10p_primitive(
        result.deviance_base, result.deviance_augmented, n_pcs,
    )


def parse_args() -> argparse.Namespace:
    """Parses the arguments and function."""
    parser = argparse.ArgumentParser(
        description="Fixes static_nlog10p values for genes with more than 40 "
                    "PCs (a user defined value while computing the results "
                    "with UKBPheWAS).",
    )

    parser.add_argument(
        "--max-n-pcs", default=40, type=int,
        help="Maximum number of PCs which were used for the analysis "
             "[%(default)s].",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
