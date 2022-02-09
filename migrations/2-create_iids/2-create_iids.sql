-- Changes in *outcomes*
-- Change the primary key to the new serial id.
begin;
alter table outcomes drop constraint outcomes_pkey cascade;
alter table outcomes add column iid serial primary key;

-- Still enforce the uniqueness and index for id, analysis_type.
create unique index outcomes_id_type_idx on outcomes (id, analysis_type);

-- Restore relationships with new field.
-- enrichment
create table enrichment_new as
select
    o.iid as outcome_iid,
    e.gene_set_id,
    e.hierarchy_id,
    e.set_size,
    e.enrichment_score,
    e.p float8,
    e.analysis_subset
from
    enrichment e
    inner join outcomes o
        on e.outcome_id = o.id and e.analysis_type = o.analysis_type;

drop table enrichment;
alter table enrichment_new rename to enrichment;

alter table enrichment add primary key
    (outcome_iid, analysis_subset, gene_set_id);

alter table enrichment add constraint enrichment_outcome_id_fkey
    foreign key (outcome_iid) references outcomes(iid);

-- enrichment_contingency
create table enrichment_contingency_new as
select
    o.iid as outcome_iid,
    e.gene_set_id,
    e.hierarchy_id,
    e.n00,
    e.n01,
    e.n10,
    e.n11,
    e.p,
    e.analysis_subset
from
    enrichment_contingency e
    inner join outcomes o
        on e.outcome_id = o.id and e.analysis_type = o.analysis_type;

drop table enrichment_contingency;
alter table enrichment_contingency_new rename to enrichment_contingency;

alter table enrichment_contingency
    add primary key (outcome_iid, analysis_subset, gene_set_id);

alter table enrichment_contingency
    add constraint enrichment_contingency_outcome_iid_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- Changes in *genes*
-- Change the primary key to the new serial id.
begin;
alter table genes drop constraint genes_pkey cascade;
alter table genes add column iid serial primary key;

-- Still enforce the uniqueness and index for ensembl id.
create unique index genes_id_idx on genes (ensembl_id);

-- Restore relationships with new field.
-- xrefs
create table xrefs_new as
select
    g.iid as gene_iid,
    xrefs.external_db_id,
    xrefs.external_id
from
    xrefs inner join genes g on xrefs.ensembl_id = g.ensembl_id;

drop table xrefs;
alter table xrefs_new rename to xrefs;

alter table xrefs add primary key (gene_iid, external_db_id, external_id);

alter table xrefs add constraint xrefs_gene_iid_fkey
    foreign key (gene_iid) references genes(iid);

alter table xrefs add constraint xrefs_external_db_id_fkey
    foreign key (external_db_id) references external_db(id);

-- gene_n_pcs
create table gene_n_pcs_new as
select
    g.iid as gene_iid,
    pc.n_pcs_95,
    pc.n_variants,
    pc.pct_explained
from
    gene_n_pcs pc
    inner join genes g on pc.ensembl_id = g.ensembl_id;

drop table gene_n_pcs;
alter table gene_n_pcs_new rename to gene_n_pcs;

alter table gene_n_pcs add primary key (gene_iid, n_pcs_95);
alter table gene_n_pcs add constraint gene_n_pcs_gene_iid_fkey
    foreign key (gene_iid) references genes(iid);
commit;

-- *All results tables and model fits*
-- results (results_both_phecodes)
begin;
create table results_both_phecodes_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_phecodes r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'PHECODES') o
        on r.outcome_id = o.id;

drop table results_both_phecodes;
alter table results_both_phecodes_new rename to results_both_phecodes;

alter table results_both_phecodes drop column gene;
alter table results_both_phecodes drop column outcome_id;

alter table results_both_phecodes add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes
    add constraint results_both_phecodes_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes
    add constraint results_both_phecodes_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_both_phecodes)
begin;
create table results_both_phecodes_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_phecodes_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'PHECODES') o
        on r.outcome_id = o.id;

drop table results_both_phecodes_model_fit;
alter table results_both_phecodes_model_fit_new
    rename to results_both_phecodes_model_fit;
alter table results_both_phecodes_model_fit drop column outcome_id;
alter table results_both_phecodes_model_fit drop column gene;

alter table results_both_phecodes_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_model_fit
    add constraint results_both_phecodes_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_model_fit
    add constraint results_both_phecodes_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_female_phecodes)
begin;
create table results_female_phecodes_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_phecodes r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'PHECODES') o
        on r.outcome_id = o.id;

drop table results_female_phecodes;
alter table results_female_phecodes_new rename to results_female_phecodes;

alter table results_female_phecodes drop column gene;
alter table results_female_phecodes drop column outcome_id;

alter table results_female_phecodes add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes
    add constraint results_female_phecodes_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes
    add constraint results_female_phecodes_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_female_phecodes)
begin;
create table results_female_phecodes_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_phecodes_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'PHECODES') o
        on r.outcome_id = o.id;

drop table results_female_phecodes_model_fit;
alter table results_female_phecodes_model_fit_new
    rename to results_female_phecodes_model_fit;
alter table results_female_phecodes_model_fit drop column outcome_id;
alter table results_female_phecodes_model_fit drop column gene;

alter table results_female_phecodes_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_model_fit
    add constraint results_female_phecodes_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_model_fit
    add constraint results_female_phecodes_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_male_phecodes)
begin;
create table results_male_phecodes_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_phecodes r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'PHECODES') o
        on r.outcome_id = o.id;

drop table results_male_phecodes;
alter table results_male_phecodes_new rename to results_male_phecodes;

alter table results_male_phecodes drop column gene;
alter table results_male_phecodes drop column outcome_id;

alter table results_male_phecodes add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes
    add constraint results_male_phecodes_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes
    add constraint results_male_phecodes_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_male_phecodes)
begin;
create table results_male_phecodes_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_phecodes_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'PHECODES') o
        on r.outcome_id = o.id;

drop table results_male_phecodes_model_fit;
alter table results_male_phecodes_model_fit_new
    rename to results_male_phecodes_model_fit;
alter table results_male_phecodes_model_fit drop column outcome_id;
alter table results_male_phecodes_model_fit drop column gene;

alter table results_male_phecodes_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_model_fit
    add constraint results_male_phecodes_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_model_fit
    add constraint results_male_phecodes_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_both_continuous_variables)
begin;
create table results_both_continuous_variables_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_continuous_variables r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CONTINUOUS_VARIABLE') o
        on r.outcome_id = o.id;

drop table results_both_continuous_variables;
alter table results_both_continuous_variables_new rename to results_both_continuous_variables;

alter table results_both_continuous_variables drop column gene;
alter table results_both_continuous_variables drop column outcome_id;

alter table results_both_continuous_variables add primary key (outcome_iid, gene_iid);

alter table results_both_continuous_variables
    add constraint results_both_continuous_variables_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_continuous_variables
    add constraint results_both_continuous_variables_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_both_continuous_variables)
begin;
create table results_both_continuous_variables_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_continuous_variables_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CONTINUOUS_VARIABLE') o
        on r.outcome_id = o.id;

drop table results_both_continuous_variables_model_fit;
alter table results_both_continuous_variables_model_fit_new
    rename to results_both_continuous_variables_model_fit;
alter table results_both_continuous_variables_model_fit drop column outcome_id;
alter table results_both_continuous_variables_model_fit drop column gene;

alter table results_both_continuous_variables_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_both_continuous_variables_model_fit
    add constraint results_both_continuous_variables_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_continuous_variables_model_fit
    add constraint results_both_continuous_variables_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_female_continuous_variables)
begin;
create table results_female_continuous_variables_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_continuous_variables r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CONTINUOUS_VARIABLE') o
        on r.outcome_id = o.id;

drop table results_female_continuous_variables;
alter table results_female_continuous_variables_new rename to results_female_continuous_variables;

alter table results_female_continuous_variables drop column gene;
alter table results_female_continuous_variables drop column outcome_id;

alter table results_female_continuous_variables add primary key (outcome_iid, gene_iid);

alter table results_female_continuous_variables
    add constraint results_female_continuous_variables_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_continuous_variables
    add constraint results_female_continuous_variables_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_female_continuous_variables)
begin;
create table results_female_continuous_variables_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_continuous_variables_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CONTINUOUS_VARIABLE') o
        on r.outcome_id = o.id;

drop table results_female_continuous_variables_model_fit;
alter table results_female_continuous_variables_model_fit_new
    rename to results_female_continuous_variables_model_fit;
alter table results_female_continuous_variables_model_fit drop column outcome_id;
alter table results_female_continuous_variables_model_fit drop column gene;

alter table results_female_continuous_variables_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_female_continuous_variables_model_fit
    add constraint results_female_continuous_variables_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_continuous_variables_model_fit
    add constraint results_female_continuous_variables_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_male_continuous_variables)
begin;
create table results_male_continuous_variables_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_continuous_variables r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CONTINUOUS_VARIABLE') o
        on r.outcome_id = o.id;

drop table results_male_continuous_variables;
alter table results_male_continuous_variables_new rename to results_male_continuous_variables;

alter table results_male_continuous_variables drop column gene;
alter table results_male_continuous_variables drop column outcome_id;

alter table results_male_continuous_variables add primary key (outcome_iid, gene_iid);

alter table results_male_continuous_variables
    add constraint results_male_continuous_variables_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_continuous_variables
    add constraint results_male_continuous_variables_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_male_continuous_variables)
begin;
create table results_male_continuous_variables_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_continuous_variables_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CONTINUOUS_VARIABLE') o
        on r.outcome_id = o.id;

drop table results_male_continuous_variables_model_fit;
alter table results_male_continuous_variables_model_fit_new
    rename to results_male_continuous_variables_model_fit;
alter table results_male_continuous_variables_model_fit drop column outcome_id;
alter table results_male_continuous_variables_model_fit drop column gene;

alter table results_male_continuous_variables_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_male_continuous_variables_model_fit
    add constraint results_male_continuous_variables_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_continuous_variables_model_fit
    add constraint results_male_continuous_variables_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_both_self_reported)
begin;
create table results_both_self_reported_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_self_reported r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'SELF_REPORTED') o
        on r.outcome_id = o.id;

drop table results_both_self_reported;
alter table results_both_self_reported_new rename to results_both_self_reported;

alter table results_both_self_reported drop column gene;
alter table results_both_self_reported drop column outcome_id;

alter table results_both_self_reported add primary key (outcome_iid, gene_iid);

alter table results_both_self_reported
    add constraint results_both_self_reported_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_self_reported
    add constraint results_both_self_reported_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_both_self_reported)
begin;
create table results_both_self_reported_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_self_reported_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'SELF_REPORTED') o
        on r.outcome_id = o.id;

drop table results_both_self_reported_model_fit;
alter table results_both_self_reported_model_fit_new
    rename to results_both_self_reported_model_fit;
alter table results_both_self_reported_model_fit drop column outcome_id;
alter table results_both_self_reported_model_fit drop column gene;

alter table results_both_self_reported_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_both_self_reported_model_fit
    add constraint results_both_self_reported_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_self_reported_model_fit
    add constraint results_both_self_reported_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_female_self_reported)
begin;
create table results_female_self_reported_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_self_reported r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'SELF_REPORTED') o
        on r.outcome_id = o.id;

drop table results_female_self_reported;
alter table results_female_self_reported_new rename to results_female_self_reported;

alter table results_female_self_reported drop column gene;
alter table results_female_self_reported drop column outcome_id;

alter table results_female_self_reported add primary key (outcome_iid, gene_iid);

alter table results_female_self_reported
    add constraint results_female_self_reported_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_self_reported
    add constraint results_female_self_reported_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_female_self_reported)
begin;
create table results_female_self_reported_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_self_reported_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'SELF_REPORTED') o
        on r.outcome_id = o.id;

drop table results_female_self_reported_model_fit;
alter table results_female_self_reported_model_fit_new
    rename to results_female_self_reported_model_fit;
alter table results_female_self_reported_model_fit drop column outcome_id;
alter table results_female_self_reported_model_fit drop column gene;

alter table results_female_self_reported_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_female_self_reported_model_fit
    add constraint results_female_self_reported_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_self_reported_model_fit
    add constraint results_female_self_reported_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_male_self_reported)
begin;
create table results_male_self_reported_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_self_reported r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'SELF_REPORTED') o
        on r.outcome_id = o.id;

drop table results_male_self_reported;
alter table results_male_self_reported_new rename to results_male_self_reported;

alter table results_male_self_reported drop column gene;
alter table results_male_self_reported drop column outcome_id;

alter table results_male_self_reported add primary key (outcome_iid, gene_iid);

alter table results_male_self_reported
    add constraint results_male_self_reported_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_self_reported
    add constraint results_male_self_reported_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_male_self_reported)
begin;
create table results_male_self_reported_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_self_reported_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'SELF_REPORTED') o
        on r.outcome_id = o.id;

drop table results_male_self_reported_model_fit;
alter table results_male_self_reported_model_fit_new
    rename to results_male_self_reported_model_fit;
alter table results_male_self_reported_model_fit drop column outcome_id;
alter table results_male_self_reported_model_fit drop column gene;

alter table results_male_self_reported_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_male_self_reported_model_fit
    add constraint results_male_self_reported_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_self_reported_model_fit
    add constraint results_male_self_reported_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_both_cv_endpoints)
begin;
create table results_both_cv_endpoints_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_cv_endpoints r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CV_ENDPOINTS') o
        on r.outcome_id = o.id;

drop table results_both_cv_endpoints;
alter table results_both_cv_endpoints_new rename to results_both_cv_endpoints;

alter table results_both_cv_endpoints drop column gene;
alter table results_both_cv_endpoints drop column outcome_id;

alter table results_both_cv_endpoints add primary key (outcome_iid, gene_iid);

alter table results_both_cv_endpoints
    add constraint results_both_cv_endpoints_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_cv_endpoints
    add constraint results_both_cv_endpoints_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_both_cv_endpoints)
begin;
create table results_both_cv_endpoints_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_both_cv_endpoints_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CV_ENDPOINTS') o
        on r.outcome_id = o.id;

drop table results_both_cv_endpoints_model_fit;
alter table results_both_cv_endpoints_model_fit_new
    rename to results_both_cv_endpoints_model_fit;
alter table results_both_cv_endpoints_model_fit drop column outcome_id;
alter table results_both_cv_endpoints_model_fit drop column gene;

alter table results_both_cv_endpoints_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_both_cv_endpoints_model_fit
    add constraint results_both_cv_endpoints_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_cv_endpoints_model_fit
    add constraint results_both_cv_endpoints_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_female_cv_endpoints)
begin;
create table results_female_cv_endpoints_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_cv_endpoints r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CV_ENDPOINTS') o
        on r.outcome_id = o.id;

drop table results_female_cv_endpoints;
alter table results_female_cv_endpoints_new rename to results_female_cv_endpoints;

alter table results_female_cv_endpoints drop column gene;
alter table results_female_cv_endpoints drop column outcome_id;

alter table results_female_cv_endpoints add primary key (outcome_iid, gene_iid);

alter table results_female_cv_endpoints
    add constraint results_female_cv_endpoints_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_cv_endpoints
    add constraint results_female_cv_endpoints_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_female_cv_endpoints)
begin;
create table results_female_cv_endpoints_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_female_cv_endpoints_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CV_ENDPOINTS') o
        on r.outcome_id = o.id;

drop table results_female_cv_endpoints_model_fit;
alter table results_female_cv_endpoints_model_fit_new
    rename to results_female_cv_endpoints_model_fit;
alter table results_female_cv_endpoints_model_fit drop column outcome_id;
alter table results_female_cv_endpoints_model_fit drop column gene;

alter table results_female_cv_endpoints_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_female_cv_endpoints_model_fit
    add constraint results_female_cv_endpoints_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_cv_endpoints_model_fit
    add constraint results_female_cv_endpoints_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;


-- results (results_male_cv_endpoints)
begin;
create table results_male_cv_endpoints_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_cv_endpoints r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CV_ENDPOINTS') o
        on r.outcome_id = o.id;

drop table results_male_cv_endpoints;
alter table results_male_cv_endpoints_new rename to results_male_cv_endpoints;

alter table results_male_cv_endpoints drop column gene;
alter table results_male_cv_endpoints drop column outcome_id;

alter table results_male_cv_endpoints add primary key (outcome_iid, gene_iid);

alter table results_male_cv_endpoints
    add constraint results_male_cv_endpoints_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_cv_endpoints
    add constraint results_male_cv_endpoints_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);
commit;

-- model fit (results_male_cv_endpoints)
begin;
create table results_male_cv_endpoints_model_fit_new as
select
    o.iid as outcome_iid,
    g.iid as gene_iid,
    r.*
from
    results_male_cv_endpoints_model_fit r
    inner join
    genes g on r.gene = g.ensembl_id
    inner join
    (select * from outcomes where analysis_type = 'CV_ENDPOINTS') o
        on r.outcome_id = o.id;

drop table results_male_cv_endpoints_model_fit;
alter table results_male_cv_endpoints_model_fit_new
    rename to results_male_cv_endpoints_model_fit;
alter table results_male_cv_endpoints_model_fit drop column outcome_id;
alter table results_male_cv_endpoints_model_fit drop column gene;

alter table results_male_cv_endpoints_model_fit
    add primary key (outcome_iid, gene_iid);

alter table results_male_cv_endpoints_model_fit
    add constraint results_male_cv_endpoints_model_fit_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_cv_endpoints_model_fit
    add constraint results_male_cv_endpoints_model_fit_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

commit;

