import csv
import gzip

from ..engine import Session
from ..models import Gene


def parse_line(line):
    """Parse a GTF line into a Gene instance."""
    line = line.strip().split("\t")
    chrom, _, _, start, end, _, strand, _, meta = line

    meta = meta.strip(";").split(";")
    meta = dict([i.strip().replace('"', "").split(" ") for i in meta])

    ensembl_id = meta["gene_id"]

    if len(chrom) > 2:
        raise ValueError("Contig unsupported.")

    # By default, genes have no results
    return Gene(
        ensembl_id=ensembl_id,
        name=meta.get("gene_name"),
        chrom=chrom,
        start=int(start),
        end=int(end),
        positive_strand=(strand == "+"),
        biotype=meta.get("gene_biotype"),
        has_results=False,
    )


def get_reader(fn):
    if fn.endswith(".gz"):
        reader = gzip.open
    else:
        reader = open

    return reader


def parse_header(li):
    return {name: i for i, name in enumerate(li)}


def get_descriptions(fn):
    if fn is None:
        return None

    reader = get_reader(fn)
    out = {}

    with reader(fn, "rt") as f:
        csv_reader = csv.reader(f)
        header = parse_header(next(csv_reader))

        for row in csv_reader:
            ensembl_id = row[header["ensembl_id"]]
            description = row[header["description"]]

            if description == "":
                continue

            out[ensembl_id] = description

    return out


def get_genes_to_keep(filename):
    if filename is None:
        return None

    reader = get_reader(filename)
    with reader(filename, "rt") as f:
        csv_reader = csv.reader(f)
        header = parse_header(next(csv_reader))
        keep = {li[header["ensembl_id"]] for li in csv_reader}

    return keep


def main(args):
    keep = get_genes_to_keep(args.included_genes)
    descriptions = get_descriptions(args.description)

    filename = args.filename

    if filename.endswith(".gz"):
        reader = gzip.open

    else:
        reader = open

    genes = []
    with reader(filename, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue

            try:
                gene = parse_line(line)

                if descriptions is not None:
                    desc = descriptions.get(gene.ensembl_id)

                    if desc:
                        gene.description = desc

                if keep is None or gene.ensembl_id in keep:
                    genes.append(gene)

            except ValueError:
                pass

    session = Session()
    session.add_all(genes)

    session.commit()
    print("Added {} genes to the database.".format(len(genes)))
