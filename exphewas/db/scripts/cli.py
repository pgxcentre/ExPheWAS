import argparse
import csv
import functools
from collections import defaultdict


from ..engine import ENGINE, Session
from ..models import Base, ANALYSIS_TYPES
from .. import models

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


def create_icd10_hierarchy():
    session = Session()

    # Getting the ICD10 blocks
    icd10_blocks = _generate_icd10_blocks([
        result[0] for result in
        session.query(models.Outcome.id)
            .filter_by(analysis_type="ICD10_BLOCK").all()
    ])

    # Creating the chapters
    chapters = defaultdict(list)
    for block in icd10_blocks:
        chapters[block.chapter].append(block)

    # Getting the ICD10 3 character codes
    icd10_3char = [
        result[0] for result in
        session.query(models.Outcome.id)
            .filter_by(analysis_type="ICD10_3CHAR").all()
    ]

    # Generating what will be added
    hierarchy = [
        models.OutcomeHierarchy(id=str(icd10_block), parent=None)
        for icd10_block in icd10_blocks
    ]

    # Adding the 3 character codes
    for code in icd10_3char:
        parent = _get_icd10_parent(code, chapters)
        if parent is not None:
            parent = str(parent)
        hierarchy.append(models.OutcomeHierarchy(id=code, parent=parent))

    session.add_all(hierarchy)
    session.commit()


def _get_icd10_parent(code, chapters):
    chapter = code[0]
    blocks = chapters[chapter]
    for block in blocks:
        if code in block:
            return block


def _generate_icd10_blocks(blocks):
    class ICD10Block(object):
        def __init__(self, block):
            self.chapter = block[0]
            start, stop = block.split("-")
            self.start = int(start[1:])
            self.stop = int(stop[1:])

        def __repr__(self):
            return "<ICD10BLock: {}>".format(self.__str__())

        def __str__(self):
            return "{chapter}{start:02d}-{chapter}{stop:02d}".format(
                chapter=self.chapter, start=self.start, stop=self.stop,
            )

        def __contains__(self, icd10_3char):
            """Checks if an ICD10 3 character code is in the block."""
            chapter = icd10_3char[0]
            section = int(icd10_3char[1:])

            return (
                (chapter == self.chapter) and
                (self.start <= section <= self.stop)
            )

    return [ICD10Block(block) for block in blocks]


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

    # Command to create the outcome hierarchy
    subparsers.add_parser("create-icd10-hierarchy")

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

    elif args.command == "create-icd10-hierarchy":
        return create_icd10_hierarchy()

    elif args.command == "import-external":
        return import_external.main(args)
