import argparse
import csv
import functools


from ..engine import ENGINE, Session
from ..models import Base, ANALYSIS_TYPES
from .. import models

from . import import_ensembl, import_results, import_n_pcs


def create():
    Base.metadata.create_all(ENGINE)


def delete_results():
    session = Session()

    session.query(models.ContinuousVariableResult)\
        .delete(synchronize_session=False)

    session.query(models.BinaryVariableResult)\
        .delete(synchronize_session=False)

    session.commit()


def find_missing_results():
    session = Session()

    missing_genes = {}

    for analysis_type in ANALYSIS_TYPES:
        # Get all outcomes for this analysis.
        outcomes = session.query(models.Outcome.id)\
            .filter_by(analysis_type=analysis_type)\
            .subquery()

        # Get genes with results.
        if analysis_type == "CONTINUOUS_VARIABLE":
            Result = models.ContinuousVariableResult
        else:
            Result = models.BinaryVariableResult

        genes_with_results = session.query(Result.gene)\
            .filter(Result.outcome_id.in_(outcomes))

        # Get all genes except ones with results or the ones that were not
        # analyzed.
        # We query GeneVariance instead of Gene to limit ourselves to the
        # genes that were not excluded.
        # The genes that were excluded had no common variants to derive the
        # principal components.
        missing_genes[analysis_type] = {i[0] for i in 
            session.query(models.GeneVariance.ensembl_id)\
                .except_(genes_with_results)\
                .all()
        }

    all_genes = functools.reduce(
        lambda x, y: x | y, missing_genes.values(), set()
    )

    with open("missing_results.csv", "w") as f:
        writer = csv.writer(f)

        writer.writerow(["gene"] + ANALYSIS_TYPES + ["n_missing_analyses"])

        for gene in all_genes:
            row = [gene, ]

            for analysis_type in ANALYSIS_TYPES:
                row.append(int(gene in missing_genes[analysis_type]))

            row.append(sum(row[1:]))

            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    # Command to create the database.
    subparsers.add_parser("create")

    # Command to delete all results.
    subparsers.add_parser("delete-results")

    # Command to import ensembl data (from a GTF).
    parser_import_ensembl = subparsers.add_parser("import-ensembl")
    parser_import_ensembl.add_argument("filename",
                                       help="Path to the Ensembl GTF file.")

    # Command to import the Ensembl to Uniprot cross-references.
    parser_import_uniprot_xref = subparsers.add_parser("import-uniprot-xref")
    parser_import_uniprot_xref.add_argument(
        "filename", help="Path to the Ensembl to Uniprot xref file."
    )

    # Command to import the number of PCs for a gene.
    parser_import_n_pcs = subparsers.add_parser("import-n-pcs")
    parser_import_n_pcs.add_argument(
        "filename",
        help=("The file containing the number of PCs per gene for various "
              "percentages of variance explained.")
    )

    # Command to import the results.
    parser_import_results = subparsers.add_parser("import-results")
    parser_import_results.add_argument(
        "filename",
        help="Path to the results file."
    )

    parser_import_results.add_argument(
        "--gene",
        help="Ensembl ID of the gene.",
        required=True
    )

    parser_import_results.add_argument(
        "--analysis",
        help="Type of analysis.",
        choices=ANALYSIS_TYPES,
        required=True
    )

    parser_import_results.add_argument(
        "--pct-variance",
        help="Percentage of the variance explained by the PCs.",
        default=95
    )

    # Command to list the missing analyses per gene.
    subparsers.add_parser("find-missing-results")

    # Dispatch the command.
    args = parser.parse_args()
    if args.command == "create":
        return create()

    elif args.command == "delete-results":
        return delete_results()

    elif args.command == "find-missing-results":
        return find_missing_results()

    elif args.command == "import-ensembl":
        return import_ensembl.main(args)

    elif args.command == "import-uniprot-xref":
        return import_ensembl.import_uniprot_xref(args)

    elif args.command == "import-n-pcs":
        return import_n_pcs.main(args)

    elif args.command == "import-results":
        return import_results.main(args)
