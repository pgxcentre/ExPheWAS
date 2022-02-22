# export EXPHEWAS_DATABASE_URL to configure the database.
# e.g. export EXPHEWAS_DATABASE_URL=postgresql+psycopg2://user:pwd@localhost/mydatabase
host ?= 127.0.0.1

.PHONY: database
database: create ensembl uniprot_xref hierarchies external_db n_pcs


.PHONY: create
create:
	exphewas-db create


.PHONY: ensembl
ensembl:
	exphewas-db import-ensembl data/ensembl/Homo_sapiens.GRCh37.87.protein_coding_lincRNA.gtf.gz \
	   --description data/ensembl/gene_description.csv.gz \
	   --included-genes data/exphewas/pca_metadata.csv.gz


.PHONY: uniprot_xref
uniprot_xref:
	exphewas-db import-external --external-db data/uniprot/external_db.our.csv.gz --xrefs data/uniprot/ensembl_xrefs.our.csv.gz


.PHONY: n_pcs
n_pcs:
	exphewas-db import-n-pcs data/exphewas/pca_metadata.csv.gz


.PHONY: external_db
external_db:
	exphewas-db import-external --external-db data/ensembl/external_db.csv.gz --xrefs data/ensembl/ensembl_xrefs.csv.gz


.PHONY: hierarchies
hierarchies:
	exphewas-db import-hierarchies data/hierarchies


.PHONY: clear_results
clear_results:
	exphewas-db delete-results


.PHONY: ipython
ipython:
	ipython -i .ipython_startup


.PHONY: serve_dev
serve_dev:
	FLASK_ENV=development FLASK_APP=exphewas.backend flask run --port 5001 --host '$(host)'


.PHONY: serve
serve:
	FLASK_APP=exphewas.backend flask run --port 5001

.PHONY: clear_cache
clear_cache:
	python -c 'from exphewas.backend.cache import clear_cache_gene_with_results; clear_cache_gene_with_results()'
	python -c 'import exphewas.backend.cache; exphewas.backend.cache.Cache().clear()'

.PHONY: cache
cache:
	python -c 'import exphewas.backend.cache; exphewas.backend.cache.create_or_load_startup_caches()'
	python -c 'from exphewas.backend.cache import cache_gene_with_results; cache_gene_with_results()'
