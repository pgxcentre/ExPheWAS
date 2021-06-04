"""Utility functions."""


from os import path
import gzip
import json
import csv

import pandas as pd
import numpy as np
import scipy.stats
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


def load_variable_labels():
    """Load the label for UKBPheWAS IDs."""
    fn = "variable_labels.csv.gz"
    fn = resource_filename(__name__, path.join("db", "scripts", "data", fn))

    labels = {}
    with gzip.open(fn, "rt") as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # skip header.

        for row in csv_reader:
            analysis_type, variable_id, label = row
            labels[(analysis_type, variable_id)] = label

    return labels


def load_ukbphewas_model(filename, as_dict=False, fit_df=True):
    """Load the full model fit as serialized by UKBPheWAS.

    It's one phenotype per row. Every row is a valid JSON.

    """
    models = []
    with gzip.open(filename, "rt") as f:
        for line in f:
            model = json.loads(line)
            model["variable_id"] = str(model["variable_id"])
            if fit_df:
                fit = model.pop("model_fit")
                fit = pd.DataFrame(fit)
                model["model_fit"] = fit

            models.append(model)

    if as_dict:
        return {
            (i["analysis_type"], i["variable_id"]): i["model_fit"]
            for i in models
        }
    else:
        return models


def one_sample_pca_ivw(x_model, y_model, ci=None):
    """Compute the IVW estimate of the effect of X on Y using PCs as IVs.

    CI needs to be an alpha level.

    """
    def _prep_df(df, label):
        term_column = "term" if "term" in df.columns else "variable"
        cols = [term_column, "beta", "se"]

        # Keep only PCs and the relevant columns.
        df = df.loc[df[term_column].str.startswith("XPC"), cols].copy()
        df = df.set_index(term_column)
        df.columns = [f"{label}_beta", f"{label}_se"]
        return df

    x = _prep_df(x_model["model_fit"], "x")
    y = _prep_df(y_model["model_fit"], "y")
    df = pd.concat((x, y), axis=1)

    # The IVW weight is only valid under relevance, but if we filter out PCs
    # with a null effect, then we're subject to Winner's curse.
    precisions = df["y_se"] ** -2
    ivw_denum = np.sum(df["x_beta"] ** 2 * precisions)
    ivw = (
        np.sum(df["x_beta"] * df["y_beta"] * precisions) /
        ivw_denum
    )

    # We use the first order approximation as in Burgess 2013 (Genetic Epi.)
    # for now.
    se = np.sqrt(1 / ivw_denum)

    out = {
        "ivw_beta": ivw,
        "ivw_se": se
    }

    if ci:
        z = scipy.stats.norm.ppf(ci / 2)
        ci = str(int(ci * 100))
        out[f"lower_ci{ci}"] = ivw + z * se
        out[f"upper_ci{ci}"] = ivw - z * se

    return out


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
