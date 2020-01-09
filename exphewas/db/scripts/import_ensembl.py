import gzip

from ..engine import ENGINE, Session
from ..models import Gene, ensembl_uniprot


def parse_line(line):
    """Parse a GTF line into a Gene instance."""
    line = line.strip().split("\t")
    chrom, source, type_, start, end, _, strand, _, meta = line

    meta = meta.strip(";").split(";")
    meta = dict([i.strip().replace('"', "").split(" ") for i in meta])

    ensembl_id = meta["gene_id"]

    if len(chrom) > 2:
        raise ValueError("Contig unsupported.")

    return Gene(
        ensembl_id=ensembl_id,
        name=meta.get("gene_name"),
        chrom = chrom,
        start = int(start),
        end = int(end),
        positive_strand = (strand == "+")
    )


def import_uniprot_xref(args):
    """Import the mappings of uniprot to ensembl IDs."""
    filename = args.filename
    mappings = []
    with gzip.open(filename, "rt") as f:
        for line in f:
            line = line.strip()

            uniprot, _, ensembl = line.split()
            mappings.append({"ensembl_id": ensembl, "uniprot_id": uniprot})

    con = ENGINE.connect()
    con.execute(ensembl_uniprot.insert(), mappings)


def main(args):
    filename = args.filename

    if filename.endswith(".gz"):
        reader = gzip.open

    else:
        reader = open

    genes = []
    with reader(filename, "rt") as f:
        for line in f:
            try:
                genes.append(parse_line(line))
            except ValueError:
                pass

    session = Session()
    session.add_all(genes)

    session.commit()
    print("Added {} genes to the database.".format(len(genes)))
