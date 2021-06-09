import gzip

from ..engine import ENGINE, Session
from ..models import XRefs, ExternalDB, Gene


def import_external_databases(fn):
    if fn.endswith(".gz"):
        reader = gzip.open
    else:
        reader = open

    entries = []

    with reader(fn, "rt") as f:
        header = None
        for line in f:
            row = line.rstrip("\n").split(",")

            if header is None:
                header = {name: i for i, name in enumerate(row)}
                continue

            db_id = int(row[header["external_db_id"]])
            db_name = row[header["db_name"]]
            db_display_name = row[header["db_display_name"]].strip('"')

            entries.append(ExternalDB(
                id=db_id,
                db_name=db_name,
                db_display_name=db_display_name,
            ))

    session = Session()
    session.add_all(entries)

    session.commit()
    print("Added {} external databases.".format(len(entries)))


def import_xrefs(fn):
    if fn.endswith(".gz"):
        reader = gzip.open
    else:
        reader = open

    entries = []

    # Get genes that are in the DB.
    session = Session()
    ref_genes = set((tu[0] for tu in session.query(Gene.ensembl_id)))

    with reader(fn, "rt") as f:
        header = None
        for line in f:
            row = line.rstrip("\n").split(",")

            if header is None:
                header = {name: i for i, name in enumerate(row)}
                continue

            ensembl_id = row[header["ensembl_id"]]
            external_db_id = int(row[header["external_db_id"]])
            external_id = row[header["external_id"]]

            if ensembl_id not in ref_genes:
                continue

            entries.append(XRefs(
                ensembl_id=ensembl_id,
                external_db_id=external_db_id,
                external_id=external_id,
            ))

    session.add_all(entries)

    session.commit()
    print("Added {} cross references".format(len(entries)))


def main(args):
    # Pushing the external databases
    import_external_databases(args.external_db)

    # Pushing the actual cross references
    import_xrefs(args.xrefs)
