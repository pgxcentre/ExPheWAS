import argparse


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


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    # Command to create the database.
    parser_create = subparsers.add_parser("create")

    # Command to delete all results.
    parser_delete_results = subparsers.add_parser("delete-results")

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

    # Dispatch the command.
    args = parser.parse_args()
    if args.command == "create":
        return create()

    elif args.command == "delete-results":
        return delete_results()

    elif args.command == "import-ensembl":
        return import_ensembl.main(args)

    elif args.command == "import-uniprot-xref":
        return import_ensembl.import_uniprot_xref(args)

    elif args.command == "import-n-pcs":
        return import_n_pcs.main(args)

    elif args.command == "import-results":
        return import_results.main(args)
