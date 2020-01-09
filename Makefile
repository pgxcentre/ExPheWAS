# export EXPHEWAS_DATABASE_URL to configure the database.
# e.g. export EXPHEWAS_DATABASE_URL=postgresql+psycopg2://user:pwd@localhost/mydatabase

.PHONY: database
database: create ensembl uniprot_xref n_pcs


.PHONY: create
create:
	exphewas-db create


.PHONY: ensembl
ensembl:
	exphewas-db import-ensembl data/ensembl/human_protein_coding_genes.gtf.gz


.PHONY: uniprot_xref
uniprot_xref:
	exphewas-db import-uniprot-xref data/uniprot/uniprot_ensembl_human_mapping.txt.gz


.PHONY: n_pcs
n_pcs:
	exphewas-db import-n-pcs data/exphewas/n_components_all.csv.gz


.PHONY: clear_results
clear_results:
	exphewas-db delete-results


.PHONY: serve
serve:
	FLASK_ENV=development FLASK_APP=exphewas.server flask run --port 5001
