#!/usr/bin/env python

"""
Compute the enrichment of all ATC codes and all outcomes.
"""

import sys
import csv
import itertools
import functools
import collections
import multiprocessing

import pandas as pd
import numpy as np
import scipy.stats

import exphewas.db.tree as tree
from exphewas.db.models import *
from exphewas.db.engine import Session
from exphewas.backend.r_bindings import R as R_


Q_THRESHOLD = 0.05
R = R_()


def uniprot_list_to_ensembl(li, xrefs=None):
    if xrefs is None:
        xrefs = get_uniprot_to_ensembl_xref()

    ensgs = []
    for uniprot in li:
        matches = xrefs.get(uniprot)
        if matches is None:
            continue

        ensgs.extend(matches)

    return ensgs


def get_uniprot_to_ensembl_xref():
    # -1 is the id for the Uniprot to Ensembl mapping
    query = select([XRefs.external_id, XRefs.ensembl_id])\
        .where(XRefs.external_db_id == -1)

    uniprot_to_ensembl = collections.defaultdict(list)
    for uniprot, ensg in Session().execute(query):
        uniprot_to_ensembl[uniprot].append(ensg)

    return uniprot_to_ensembl


def get_results(outcome_id):
    # Check if binary or continuous.
    outcome = Session()\
        .query(Outcome)\
        .filter_by(id=outcome_id)\
        .one()

    if outcome.analysis_type == "CONTINUOUS_VARIABLE":
        results_model = ContinuousVariableResult

    else:
        results_model = BinaryVariableResult

    df = pd.DataFrame(
        Session()\
        .query(
            getattr(results_model, "gene"),
            getattr(results_model, "p")
        )\
        .filter_by(outcome_id=outcome_id)\
        .filter_by(variance_pct=95)\
        .order_by(getattr(results_model, "p"))\
        .all(),
        columns=["gene", "p"]
    )

    # Add Q value
    df["q"] = R.qvalue(df["p"].values)

    df = df.set_index("gene", verify_integrity=True)

    return df


def create_atc_targets(chembl, atc_tree, uniprot_to_ensembl):
    m = []
    for i, atc in atc_tree.iter_depth_first():
        level_codes = getattr(chembl, f"level{i}")

        targets_uniprot = chembl.loc[
            level_codes == atc.code,
            "accession"
        ].drop_duplicates()

        # We skip classes with few known targets because it's not
        # useful for enrichment.
        if len(targets_uniprot) <= 1:
            # No known targets for this class.
            continue

        # Convert targets to Ensembl.
        for t in targets_uniprot:
            # ensg is a list of ensembl ids matching the uniprot accession.
            # or None
            ensgs = uniprot_to_ensembl.get(t)

            if ensg is None:
                print(f"Could not find Ensembl ID for '{t}' (ignoring).")
                continue

            for ensg in ensg:
                m.append((atc.code, ensg))

    # This is a relationship table (long format)
    df = pd.DataFrame(m, columns=["atc", "target"])

    # Pivot into a binary matrix of drug target gene x ATC
    df["x"] = 1
    df = pd.pivot_table(df, columns=["atc"], index=["target"], values="x",
                        fill_value=0)

    return df


def compute_fisher_exact_test(data, atc):

    # Calculate the contingency table manually to easily serialize.
    sig = data["q"] <= Q_THRESHOLD
    target = data[atc].astype(bool)

    nsig = ~sig
    ntarget = ~target

    # Assume the following matrix for indexing:
    #
    # +===================+==========+==============+
    # |                   | ATC code | Not ATC code |
    # |-------------------+----------+--------------|
    # | Phenotype Assoc.  | n00      | n01          |
    # | Not associated    | n10      | n11          |
    # +-------------------+----------+--------------+

    n00 = (sig & target).sum()
    n01 = (sig & ntarget).sum()
    n10 = (nsig & target).sum()
    n11 = (nsig & ntarget).sum()

    # If there are no genes associated with both the ATC code and the phenotype
    # (n00) we take a shortcut.
    if n00 == 0:
        return (n00, n01, n10, n11, np.nan, 1)

    or_, p = scipy.stats.fisher_exact([[n00, n01], [n10, n11]])

    return (n00, n01, n10, n11, or_, p)


def _worker(atc, atc_targets, results):
    atc_cols = atc_targets.columns

    cur = results.join(atc_targets, how="outer")
    cur.loc[:, atc_cols] = cur.loc[:, atc_cols].fillna(0)

    return (atc, *compute_fisher_exact_test(cur, atc))


def main(n_cpus=None):
    if n_cpus is None:
        n_cpus = multiprocessing.cpu_count() - 1

    # Get drug target data (prepared from ChEMBL)
    chembl = pd.read_csv("../data/chembl/chembl.csv.gz")

    uniprot_to_ensembl = get_uniprot_to_ensembl_xref()

    atc_tree = tree.tree_from_hierarchy_id("ATC")

    # Create a binary matrix of genes x ATC of membership.
    atc_targets = create_atc_targets(chembl, atc_tree, uniprot_to_ensembl)
    atc_targets.to_csv("atc_to_drug_targets.csv")

    atc_cols = atc_targets.columns

    outcome_ids = [i for i, in Session().query(Outcome.id).distinct()]

    pool = multiprocessing.Pool(n_cpus)

    with open("atc_enrichment.csv", "wt") as f:
        out = csv.writer(f)
        out.writerow(["outcome_id", "atc", "n00", "n01", "n10", "n11", "OR",
                      "p"])

        for outcome_id in outcome_ids:
            results = get_results(outcome_id)

            if (results["q"] > Q_THRESHOLD).all():
                # There are no associated genes with this outcome.
                print(f"No significant genes associated with {outcome_id} "
                       "(ignoring).")
                continue

            cur = pool.map(
                functools.partial(_worker,
                                  atc_targets=atc_targets, results=results),
                atc_targets.columns
            )

            for res in cur:
                out.writerow([outcome_id, *res])

    pool.close()


if __name__ == "__main__":
    try:
        n_cpus = int(sys.argv[1])
    except:
        n_cpus = None

    main(n_cpus)
