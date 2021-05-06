#!/usr/bin/env python


import os
import pickle
import gzip
import argparse

import pandas as pd
import numpy as np
import geneparse.utils
import sklearn.decomposition



def main():
    args = parse_args()

    reader = geneparse.parsers[args.genotypes_format](
        args.genotypes,
        **geneparse.utils.parse_kwargs(args.genotypes_kwargs)
    )

    chrom, _pos = args.region.split(":")
    start, end = [int(i) for i in _pos.split("-")]
    genotypes = extract_genotypes_in_region(reader, chrom, start, end)

    n_samples, n_snps = genotypes.shape
    print(
        "Extracted genotypes for {} variants and {} samples from region {}"
        "".format(n_snps, n_samples, args.region)
    )

    # Do the PCA.
    pca = sklearn.decomposition.PCA(
        n_components=args.explain_variance,
        svd_solver="full"
    )

    pcs = pca.fit_transform(genotypes)

    print(
        "Selected {} components explaining {:.0%} of the variance."
        "".format(pca.n_components_, np.sum(pca.explained_variance_ratio_))
    )

    # Save the PCs
    df = pd.DataFrame(
        pcs,
        index=reader.get_samples(),
        columns=["XPC{}".format(i + 1) for i in range(pcs.shape[1])]
    )

    df.to_csv(args.output + "_pcs.csv.gzip", compression="gzip",
              index_label="sample_id")

    # Save the PCA object.
    with gzip.open(args.output + "_pca.pkl.gz", "wb") as f:
        pickle.dump(pca, f)


def _get_maf(g):
    return g.genotypes, g.maf()

def extract_genotypes_in_region(reader, chrom, start, end):
    genotypes = []
    for g in reader.get_variants_in_region(chrom, start, end):
        maf = g.maf()

        if np.isnan(maf) or maf < 0.01:
            continue

        # Normalize the genotypes
        g = geneparse.utils.normalize_genotypes(g)

        # Set missing to 0 (expected genotype after normalization).
        g[np.isnan(g)] = 0

        genotypes.append(g)

    return np.vstack(genotypes).T


def parse_args():
    parser = argparse.ArgumentParser()

    # Add --genotypes --genotypes-format
    geneparse.utils.add_arguments_to_parser(parser)

    parser.add_argument(
        "--explain-variance",
        help="Keep the number of PCs so that this amount of variance is "
             "explained (default: %(default)s)",
        default=0.95,
        type=float
    )

    parser.add_argument(
        "--region",
        help="The genomic region (e.g. a gene) to convert to a vector. "
             "Should be expressed as chr:start-end (e.g. 3:1234-4567).",
        required=True
    )

    parser.add_argument(
        "--output", "-o",
        help="Prefix for output file (default: %(default)s).",
        default="gene2vec"
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
