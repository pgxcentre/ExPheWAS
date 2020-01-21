# export EXPHEWAS_DATABASE_URL to configure the database.
# e.g. export EXPHEWAS_DATABASE_URL=postgresql+psycopg2://user:pwd@localhost/mydatabase

.PHONY: database
database: create ensembl uniprot_xref n_pcs hierarchy external_db populate_available_results


.PHONY: create
create:
	exphewas-db create


.PHONY: ensembl
ensembl:
	exphewas-db import-ensembl data/ensembl/human_protein_coding_genes.gtf.gz


.PHONY: uniprot_xref
uniprot_xref:
	exphewas-db import-external --external-db data/uniprot/external_db.our.csv.gz --xrefs data/uniprot/ensembl_xrefs.our.csv.gz


.PHONY: n_pcs
n_pcs:
	exphewas-db import-n-pcs data/exphewas/n_components_all.csv.gz


.PHONY: hierarchy
hierarchy:
	exphewas-db create-icd10-hierarchy


.PHONY: external_db
external_db:
	exphewas-db import-external --external-db data/ensembl/external_db.csv.gz --xrefs data/ensembl/ensembl_xrefs.csv.gz


.PHONY: populate_available_results
populate_available_results:
	exphewas-db populate-available-results


.PHONY: clear_results
clear_results:
	exphewas-db delete-results


.PHONY: serve_dev
serve_dev:
	FLASK_ENV=development FLASK_APP=exphewas.backend flask run --port 5001


.PHONY: serve
serve:
	FLASK_APP=exphewas.backend flask run --port 5001
