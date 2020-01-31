#!/usr/bin/env python

"""
Compute the enrichment of all ATC codes and all outcomes.
"""

import itertools
import multiprocessing

import pandas as pd
import scipy.stats

import exphewas.db.tree as tree
from exphewas.db.models import *
from exphewas.db.engine import Session
from exphewas.backend.r_bindings import R as R_


R = R_()


def get_uniprot_to_ensembl_xref():
    # -1 is the id for the Uniprot to Ensembl mapping
    query = select([XRefs.external_id, XRefs.ensembl_id])\
        .where(XRefs.external_db_id == -1)

    return {k: v for k, v in Session().execute(query)}


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
            ensg = uniprot_to_ensembl.get(t)
            
            if ensg is None:
                print(f"Could not find Ensembl ID for '{t}' (ignoring).")
                continue
                
            m.append((atc.code, ensg))

    # This is a relationship table (long format)
    df = pd.DataFrame(m, columns=["atc", "target"])

    # Pivot into a binary matrix of drug target gene x ATC
    df["x"] = 1
    df = pd.pivot_table(df, columns=["atc"], index=["target"], values="x",
                        fill_value=0)

    return df


def compute_fisher_exact_test(args):
    data, atc = args

    contingency = pd.crosstab(
        data["q"] <= 0.01,
        data[atc]
    )

    if contingency.shape != (2, 2):
        print(f"Weird contingency for {atc} (skipping)")
        return

    or_, p = scipy.stats.fisher_exact(contingency)

    return (atc, or_, p)


def main():
    # Get drug target data (prepared from ChEMBL)
    chembl = pd.read_csv("../data/chembl/chembl.csv.gz")

    uniprot_to_ensembl = get_uniprot_to_ensembl_xref()

    atc_tree = tree.tree_from_hierarchy_id("ATC")

    # Create a binary matrix of genes x ATC of membership.
    atc_targets = create_atc_targets(chembl, atc_tree, uniprot_to_ensembl)

    outcome_ids = [i for i, in Session().query(Outcome.id).distinct()]

    out = []

    for outcome_id in outcome_ids:
        results = get_results(outcome_id)

        cur = results.join(atc_targets, how="outer")
        cur = cur.fillna(0)

        pool = multiprocessing.Pool(7)
        cur_results = pool.map(
            compute_fisher_exact_test,
            zip(
                itertools.cycle([cur]),
                atc_targets.columns
            )
        )

        out.extend(
            [(outcome_id, *i) for i in cur_results if i is not None]
        )

    out = pd.DataFrame(out, columns=["outcome_id", "atc", "OR", "p"])
    out.to_csv("atc_enrichment.csv")


if __name__ == "__main__":
    main()
