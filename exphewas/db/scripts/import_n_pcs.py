import gzip

from ..engine import ENGINE, Session
from ..models import GeneVariance, ensembl_uniprot


def parse_line(line):
    """Parse a line into many GeneVariance objects.

    Returns a list.

    """
    line = line.strip().split(",")

    ensg = line.pop(0)
    n_85, n_90, n_95, n_99 = [int(i) for i in line]

    return [
        GeneVariance(ensg, 85, n_85),
        GeneVariance(ensg, 90, n_90),
        GeneVariance(ensg, 95, n_95),
        GeneVariance(ensg, 99, n_99),
    ]


def main(args):
    filename = args.filename

    if filename.endswith(".gz"):
        reader = gzip.open

    else:
        reader = open

    objects = []
    with reader(filename, "rt") as f:
        assert next(f) == ("ensg,n_components_85,n_components_90,"
                           "n_components_95,n_components_99\n")

        for line in f:
            objects.extend(parse_line(line))

    session = Session()
    session.add_all(objects)

    session.commit()
    print("Added {} objects to the database.".format(len(objects)))
