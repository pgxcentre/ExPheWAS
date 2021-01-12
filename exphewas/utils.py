"""Utility functions."""


from os import path

import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline

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


def _pi_0(ps, l=0.5):
    return np.sum(ps > l) / (ps.shape[0] * (1 - l))


def qvalue(ps):
    # Implementation of qvalue as described in Storey, Tibshirani (2003) PNAS
    # https://www.pnas.org/content/pnas/100/16/9440.full.pdf
    idx = np.argsort(ps)
    ps = ps[idx]
    m = ps.shape[0]

    # Same range as original in paper.
    l = np.arange(0.01, 0.96, 0.01)
    pi0s = np.empty(l.shape[0])

    # Calculate pi hat for different values of lambda.
    for i, cur_l in enumerate(l):
        pi0s[i] = _pi_0(ps, cur_l)

    # Fit spline.
    spline = UnivariateSpline(x=l, y=pi0s, k=3)

    # Predicted pi0 when lambda -> 1
    pi0 = spline(1)

    qs = np.empty(m, dtype=float)
    qs[-1] = pi0 * ps[-1]

    for i in reversed(range(m - 1)):
        qs[i] = np.minimum(
            pi0 * m * ps[i] / (i + 1),
            qs[i + 1]
        )

    return qs[np.argsort(idx)]
