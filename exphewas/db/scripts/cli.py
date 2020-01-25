import argparse
import csv
import glob
import os
import functools
from collections import defaultdict

import pandas as pd

from ..engine import ENGINE, Session
from ..models import Base, ANALYSIS_TYPES
from .. import models
from ..tree import tree_from_hierarchies

from . import import_ensembl, import_results, import_n_pcs, import_external


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


def populate_available_results():
    # First, we get the distinct gene/variance values
    session = Session()

    # Getting the variance
    results_binary = session.query(
        models.BinaryVariableResult.gene,
        models.BinaryVariableResult.variance_pct,
    ).distinct()

    results_continuous = session.query(
        models.ContinuousVariableResult.gene,
        models.ContinuousVariableResult.variance_pct,
    ).distinct()

    # Deleting the current content
    session.query(models.AvailableGeneResult).delete(synchronize_session=False)

    # Pushing data to the database
    entries = []
    for ensembl_id, variance in results_binary.union(results_continuous).all():
        entries.append(models.AvailableGeneResult(
            ensembl_id=ensembl_id, variance_pct=variance,
        ))

    session = Session()
    session.add_all(entries)

    session.commit()
    print("Added {} available results.".format(len(entries)))


def import_hierarchies(args):
    session = Session()

    path = os.path.join(args.directory_root, "hierarchy_*")
    for filename in glob.glob(path):
        cur = pd.read_csv(filename, dtype=str)
        hierarchies = []

        for _, row in cur.iterrows():
            if pd.isna(row.parent):
                parent = None
            else:
                parent = row.parent

            hierarchies.append(
                models.Hierarchy(
                    id=row["id"],
                    code=row["code"],
                    parent=parent,
                    description=row["description"]
                )
            )

        tree = tree_from_hierarchies(hierarchies)

        # We use depth first traversal of the tree to set the insertion order.
        # The instance to the Hierarchy is held in the _data field when
        # creating the tree to allow this.
        hierarchies = [n._data for _, n in tree.iter_depth_first()]

        session.bulk_save_objects(hierarchies)
        session.commit()

        print("Added {} hierarchical entries from '{}'."
              "".format(len(hierarchies), filename))


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    # Command to create the database.
    subparsers.add_parser("create")

    # Command to delete all results.
    subparsers.add_parser("delete-results")

    # Command to populate the available results for each gene
    subparsers.add_parser("populate-available-results")

    # Command to load all hierarchical data.
    parser_import_hierarchies = subparsers.add_parser("import-hierarchies")
    parser_import_hierarchies.add_argument(
        "directory_root",
        help="Root directory from which to find hierarchy files. All files "
             "in this directory prefixed with 'hierarchy_' will then be "
             "imported. The expected format is a CSV file with: id, code, "
             "parent and description."
    )

    # Command to import ensembl data (from a GTF).
    parser_import_ensembl = subparsers.add_parser("import-ensembl")
    parser_import_ensembl.add_argument(
        "filename", help="Path to the Ensembl GTF file.",
    )
    parser_import_ensembl.add_argument(
        "--description", help="Optional description for each gene (CSV)",
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

    parser_import_external = subparsers.add_parser("import-external")
    parser_import_external.add_argument(
        "--external-db", help="The external databases", required=True,
    )
    parser_import_external.add_argument(
        "--xrefs", help="The external references", required=True,
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

    elif args.command == "populate-available-results":
        return populate_available_results()

    elif args.command == "import-ensembl":
        return import_ensembl.main(args)

    elif args.command == "import-n-pcs":
        return import_n_pcs.main(args)

    elif args.command == "import-results":
        return import_results.main(args)

    elif args.command == "import-hierarchies":
        return import_hierarchies(args)

    elif args.command == "import-external":
        return import_external.main(args)
