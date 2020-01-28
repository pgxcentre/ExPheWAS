"""Utility functions."""


from os import path

import pandas as pd

from pkg_resources import resource_filename


__all__ = ["load_gtex_median_tpm", "load_gtex_statistics"]


def load_gtex_median_tpm():
    """Loads the GTEx data in a DataFrame"""
    fn = "GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz"
    fn = resource_filename(__name__, path.join("backend", "data", fn))

    # Skipping the first two lines
    df = pd.read_csv(fn, sep="\t", skiprows=2)

    # Getting rid of the '_PARY' genes (because they are duplicates)
    df = df.loc[~df.Name.str.endswith("_PAR_Y"), :]

    # Removing the versions
    df["gene"] = df.Name.str.split(".", expand=True)[0]
    df = df.set_index("gene", verify_integrity=True)

    return df.drop(columns=["Name", "Description"])


def load_gtex_statistics():
    """Loads the GTEx statistics (number of sample per tissue type)."""
    fn = "GTEx_Current_Release.csv.gz"
    fn = resource_filename(__name__, path.join("backend", "data", fn))

    # Reading with pandas because it's simpler
    df = pd.read_csv(fn).set_index("Tissue", verify_integrity=True)

    return dict(df["# RNASeq Samples"].iteritems())
