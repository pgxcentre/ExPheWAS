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

    return Gene(
        ensembl_id=ensembl_id,
        name=meta.get("gene_name"),
        chrom=chrom,
        start=int(start),
        end=int(end),
        positive_strand=(strand == "+")
    )


def add_description(fn):
    if fn.endswith(".gz"):
        reader = gzip.open
    else:
        reader = open

    session = Session()

    with reader(fn, "rt") as f:
        csv_reader = csv.reader(f)

        header = None
        for row in csv_reader:
            if header is None:
                header = {name: i for i, name in enumerate(row)}
                continue

            ensembl_id = row[header["ensembl_id"]]
            description = row[header["description"]]

            if description == "":
                description = None

            # Updating the entries
            session.query(Gene)\
                .filter(Gene.ensembl_id == ensembl_id)\
                .update({"description": description})

    session.commit()


def main(args):
#    filename = args.filename
#
#    if filename.endswith(".gz"):
#        reader = gzip.open
#
#    else:
#        reader = open
#
#    genes = []
#    with reader(filename, "rt") as f:
#        for line in f:
#            try:
#                genes.append(parse_line(line))
#            except ValueError:
#                pass
#
#    session = Session()
#    session.add_all(genes)
#
#    session.commit()
#    print("Added {} genes to the database.".format(len(genes)))

    # Checking if we have a description
    if args.description is not None:
        add_description(args.description)
