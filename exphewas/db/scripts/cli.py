import argparse
import datetime
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

from . import (import_ensembl, import_results, import_n_pcs, import_external,
               metadata)


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
    session = Session()

    # Getting the unique variance for each gene
    results_binary = session.query(
        models.BinaryVariableResult.gene,
        models.BinaryVariableResult.variance_pct,
    ).distinct()

    results_continuous = session.query(
        models.ContinuousVariableResult.gene,
        models.ContinuousVariableResult.variance_pct,
    ).distinct()

    # Deleting the current content (gene)
    session.query(models.AvailableGeneResult).delete(synchronize_session=False)

    # Pushing data to the database (gene)
    entries = []
    for ensembl_id, variance in results_binary.union(results_continuous).all():
        entries.append(models.AvailableGeneResult(
            ensembl_id=ensembl_id, variance_pct=variance,
        ))

    session = Session()
    session.add_all(entries)

    session.commit()
    print("Added {} available gene results.".format(len(entries)))

    # Getting the unique variance for each outcome
    results_binary = session.query(
        models.BinaryVariableResult.outcome_id,
        models.BinaryVariableResult.variance_pct,
    ).distinct()

    results_continuous = session.query(
        models.ContinuousVariableResult.outcome_id,
        models.ContinuousVariableResult.variance_pct,
    ).distinct()

    # Deleting the current content (outcome)
    session.query(models.AvailableOutcomeResult).delete(
        synchronize_session=False,
    )

    # Pushing data to the database (outcome)
    entries = []
    for outcome_id, variance in results_binary.union(results_continuous).all():
        entries.append(models.AvailableOutcomeResult(
            outcome_id=outcome_id, variance_pct=variance,
        ))

    session = Session()
    session.add_all(entries)

    session.commit()
    print("Added {} available outcome results.".format(len(entries)))


class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def import_chembl(args):
    chembl = pd.read_csv(args.filename)

    chembl = chembl[["who_name", "level1", "level2", "level3", "level4",
                     "level5", "action_type", "accession"]].drop_duplicates()

    db_dicts_targets = set()
    db_dicts_uniprots = []
    for _, row in chembl.iterrows():

        d = hashabledict(
            who_name = row["who_name"],
            atc1 = row["level1"],
            atc2 = row["level2"],
            atc3 = row["level3"],
            atc4 = row["level4"],
            atc5 = row["level5"],
        )

        if d not in db_dicts_targets:
            db_dicts_targets.add(d)

        d = {
            "target_atc5": row["level5"],
            "uniprot": row["accession"],
            "action_type": row["action_type"],
        }
        db_dicts_uniprots.append(d)

    Session().bulk_insert_mappings(models.ChEMBLDrug, db_dicts_targets)
    Session().commit()
    Session().bulk_insert_mappings(models.TargetToUniprot, db_dicts_uniprots)
    Session().commit()

    print("Added {} ChEMBL drug target entries.".format(len(db_dicts_targets)))


def import_hierarchies(args):
    session = Session()

    if os.path.isfile(args.directory_root):
        # Import single file.
        filenames = [args.directory_root]

    else:
        # Import all hierarchies in path.
        path = os.path.join(args.directory_root, "hierarchy_*")
        filenames = glob.glob(path)

    if len(filenames) == 0:
        raise RuntimeError("Could not find hierarchies to import.")

    for filename in filenames:
        cur = pd.read_csv(filename, dtype=str)
        hierarchies = []

        for _, row in cur.iterrows():
            if pd.isna(row.parent):
                parent = models.Hierarchy.DEFAULT_PARENT
            else:
                parent = row.parent

            desc = row["description"]
            desc = None if pd.isnull(desc) else desc

            hierarchies.append(
                models.Hierarchy(
                    id=row["id"],
                    code=row["code"],
                    parent=parent,
                    description=desc
                )
            )

        tree = tree_from_hierarchies(hierarchies, keep_hierarchy=True)

        # We use depth first traversal of the tree to set the insertion order.
        # The instance to the Hierarchy is held in the _data field when
        # creating the tree to allow this.
        hierarchies = []
        for _, n in tree.iter_depth_first():
            hierarchies.append(n._data)

        session.bulk_save_objects(hierarchies)
        session.commit()

        print("Added {} hierarchical entries from '{}'."
              "".format(len(hierarchies), filename))


def import_enrichment(args):
    results = pd.read_csv(args.filename)

    # Insert the data.
    db_dicts = []
    for _, row in results.iterrows():
        d = {
            "outcome_id": row["outcome"],
            "gene_set_id": row["pathway"],
            "hierarchy_id": "ATC",
            "set_size": row["size"],
            "enrichment_score": row["NES"],
            "p": row["pval"],
        }

        db_dicts.append(d)

    Session().bulk_insert_mappings(models.Enrichment, db_dicts)
    Session().commit()

    print("Added {} enrichment analysis results.".format(len(db_dicts)))


def import_enrichment_contingency(args):
    session = Session()

    results = pd.read_csv(args.filename)

    expected_cols = {"outcome_id", "gene_set_id", "n00", "n01", "n10", "n11",
                     "p"}

    missing = expected_cols - set(results.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")


    # If there is a hierarchy_id, test that it exists.
    if args.hierarchy_id:
        try:
            session\
                .query(models.Hierarchy)\
                .filter_by(id=args.hierarchy_id)\
                .limit(1)\
                .one()

        except Exception as e:
            print(e)
            print(f"Could not find hierarchy id '{args.hierarchy_id}'")
            return

    # Insert the data.
    db_dicts = []
    for _, row in results.iterrows():
        d = {
            "outcome_id": row.outcome_id,
            "gene_set_id": row.gene_set_id,
            "n00": row.n00,
            "n01": row.n01,
            "n10": row.n10,
            "n11": row.n11,
            "p": row.p,
        }

        if args.hierarchy_id:
            d["hierarchy_id"] = args.hierarchy_id

        db_dicts.append(d)

    session.bulk_insert_mappings(models.EnrichmentContingency, db_dicts)
    session.commit()

    print("Added {} enrichment analysis results.".format(len(db_dicts)))


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    # Command to create the database.
    subparsers.add_parser("create")

    # Command to delete all results.
    subparsers.add_parser("delete-results")

    # Command to set or view the data freeze version and metadata.
    parser_metadata = subparsers.add_parser("metadata")
    parser_metadata.add_argument(
        "--view",
        action="store_true",
        help="Prints the current database metadata instead of creating or "
             "updating it."
    )

    parser_metadata.add_argument(
        "--version", "-v",
        type=str,
        help="Set the version (e.g. 0.1)."
    )

    parser_metadata.add_argument(
        "--comments",
        type=str,
        help="Set extra description or comments."
    )

    parser_metadata.add_argument(
        "--date",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
        help="Set the recorded data creation date."
    )

    # Command to populate the available results for each gene
    subparsers.add_parser("populate-available-results")

    # Command to load all hierarchical data.
    parser_import_hierarchies = subparsers.add_parser("import-hierarchies")
    parser_import_hierarchies.add_argument(
        "directory_root",
        help="Root directory from which to find hierarchy files. All files "
             "in this directory prefixed with 'hierarchy_' will then be "
             "imported. The expected format is a CSV file with: id, code, "
             "parent and description. Alternatively, a single file can be "
             "provided."
    )

    # Command to import results from enrichment analyses based on contigency
    # table.
    parser_import_enrichment_c = subparsers.add_parser(
        "import-enrichment-contingency"
    )
    parser_import_enrichment_c.add_argument(
        "filename",
        help="Filename to the results of the form outcome_id, gene_set_id, "
             "n00, n01, n10, n11 and p. Column names will be enforced."
    )
    parser_import_enrichment_c.add_argument(
        "--hierarchy-id",
        help="If the gene_set_ids correspond to codes in the hierarchy table, "
             "this argument can be used to specify the code.",
        default=None
    )

    # Command to import results from enrichment analyses.
    parser_import_enrichment = subparsers.add_parser(
        "import-enrichment"
    )
    parser_import_enrichment.add_argument(
        "filename",
        help="Filename to the results of GSEA analysis."
    )

    # Command to import ensembl data (from a GTF).
    parser_import_ensembl = subparsers.add_parser("import-ensembl")
    parser_import_ensembl.add_argument(
        "filename", help="Path to the Ensembl GTF file.",
    )
    parser_import_ensembl.add_argument(
        "--description", help="Optional description for each gene (CSV)",
    )

    # Command to import ChEMBL drug target data.
    parser_import_chembl = subparsers.add_parser(
        "import-chembl-targets"
    )
    parser_import_chembl.add_argument(
        "filename",
        help="Filename formatted ChEMBL data."
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

    elif args.command == "metadata":
        return metadata.main(args)

    elif args.command == "find-missing-results":
        return find_missing_results()

    elif args.command == "populate-available-results":
        return populate_available_results()

    elif args.command == "import-ensembl":
        return import_ensembl.main(args)

    elif args.command == "import-chembl-targets":
        return import_chembl(args)

    elif args.command == "import-n-pcs":
        return import_n_pcs.main(args)

    elif args.command == "import-results":
        return import_results.main(args)

    elif args.command == "import-hierarchies":
        return import_hierarchies(args)

    elif args.command == "import-enrichment-contingency":
        return import_enrichment_contingency(args)

    elif args.command == "import-enrichment":
        return import_enrichment(args)

    elif args.command == "import-external":
        return import_external.main(args)
