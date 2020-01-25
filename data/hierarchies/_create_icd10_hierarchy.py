#!/usr/bin/env python

"""
Merge manually generated ICD10 files with the UK Biobank data coding to
generate the final outcome hierarchy.
"""


import functools


import pandas as pd


def _find_parent_coding(row, icd10_ukb):
    if row.parent_id == 0:
        return None

    else:
        match = icd10_ukb.loc[icd10_ukb.node_id == row.parent_id, "coding"]
        assert len(match) == 1
        return match.values[0]


def icd10_hierarchy():
    icd10_ukb = pd.read_csv("ukb_codings/coding19.tsv.gz", sep="\t")

    # We sort the UKB by code length so that the nodes without dependencies get
    # created first.
    c = icd10_ukb.coding.str.startswith("Chapter")
    b = icd10_ukb.coding.str.startswith("Block")
    o = ~(c|b)

    icd10_ukb = pd.concat((
        icd10_ukb.loc[c, :],
        icd10_ukb.loc[b, :],
        icd10_ukb.loc[o, :].sort_values("coding")
    ))

    # Remove Chapter and Block
    icd10_ukb.coding = icd10_ukb.coding.str.replace("Chapter ", "")
    icd10_ukb.coding = icd10_ukb.coding.str.replace("Block ", "")

    icd10_ukb["parent_coding"] = icd10_ukb.apply(
        functools.partial(_find_parent_coding, icd10_ukb=icd10_ukb),
        axis=1
    )

    icd10_ukb["id"] = "ICD10"
    icd10_ukb = icd10_ukb[["id", "coding", "parent_coding", "meaning"]]
    icd10_ukb.columns = ["id", "code", "parent", "description"]

    icd10_ukb.to_csv("hierarchy_icd10.csv.gz", compression="gzip", index=False)


def self_reported_hierarchy():
    sr = pd.read_csv("ukb_codings/coding6.tsv.gz", sep="\t")

    # The node IDs are used as outcome IDs so we can ignore the coding field.
    sr["id"] = "SELF_REPORTED_DISEASES"

    sr = sr[["id", "node_id", "parent_id", "meaning"]]

    # Format parent IDs.
    sr.parent_id = sr.apply(
        lambda row: str(row.parent_id) if row.parent_id != 0 else "",
        axis=1
    )

    sr.columns = ["id", "code", "parent", "description"]


    sr.to_csv("hierarchy_self_reported.csv.gz", compression="gzip", index=False)


def main():
    icd10_hierarchy()
    self_reported_hierarchy()


if __name__ == "__main__":
    main()
