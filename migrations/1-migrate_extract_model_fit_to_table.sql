create table if not exists public.results_both_continuous_variables_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_both_continuous_variables_model_fit_pkey primary key (outcome_id, gene),
    constraint results_both_continuous_variables_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_both_continuous_variables_model_fit;
    
begin;
    insert into public.results_both_continuous_variables_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_both_continuous_variables;

    alter table public.results_both_continuous_variables drop column model_fit;
commit;
    
create table if not exists public.results_female_continuous_variables_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_female_continuous_variables_model_fit_pkey primary key (outcome_id, gene),
    constraint results_female_continuous_variables_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_female_continuous_variables_model_fit;
    
begin;
    insert into public.results_female_continuous_variables_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_female_continuous_variables;

    alter table public.results_female_continuous_variables drop column model_fit;
commit;
    
create table if not exists public.results_male_continuous_variables_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_male_continuous_variables_model_fit_pkey primary key (outcome_id, gene),
    constraint results_male_continuous_variables_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_male_continuous_variables_model_fit;
    
begin;
    insert into public.results_male_continuous_variables_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_male_continuous_variables;

    alter table public.results_male_continuous_variables drop column model_fit;
commit;
    
create table if not exists public.results_both_phecodes_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_both_phecodes_model_fit_pkey primary key (outcome_id, gene),
    constraint results_both_phecodes_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_both_phecodes_model_fit;
    
begin;
    insert into public.results_both_phecodes_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_both_phecodes;

    alter table public.results_both_phecodes drop column model_fit;
commit;
    
create table if not exists public.results_female_phecodes_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_female_phecodes_model_fit_pkey primary key (outcome_id, gene),
    constraint results_female_phecodes_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_female_phecodes_model_fit;
    
begin;
    insert into public.results_female_phecodes_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_female_phecodes;

    alter table public.results_female_phecodes drop column model_fit;
commit;
    
create table if not exists public.results_male_phecodes_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_male_phecodes_model_fit_pkey primary key (outcome_id, gene),
    constraint results_male_phecodes_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_male_phecodes_model_fit;
    
begin;
    insert into public.results_male_phecodes_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_male_phecodes;

    alter table public.results_male_phecodes drop column model_fit;
commit;
    
create table if not exists public.results_both_self_reported_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_both_self_reported_model_fit_pkey primary key (outcome_id, gene),
    constraint results_both_self_reported_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_both_self_reported_model_fit;
    
begin;
    insert into public.results_both_self_reported_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_both_self_reported;

    alter table public.results_both_self_reported drop column model_fit;
commit;
    
create table if not exists public.results_female_self_reported_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_female_self_reported_model_fit_pkey primary key (outcome_id, gene),
    constraint results_female_self_reported_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_female_self_reported_model_fit;
    
begin;
    insert into public.results_female_self_reported_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_female_self_reported;

    alter table public.results_female_self_reported drop column model_fit;
commit;
    
create table if not exists public.results_male_self_reported_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_male_self_reported_model_fit_pkey primary key (outcome_id, gene),
    constraint results_male_self_reported_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_male_self_reported_model_fit;
    
begin;
    insert into public.results_male_self_reported_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_male_self_reported;

    alter table public.results_male_self_reported drop column model_fit;
commit;
    
create table if not exists public.results_both_cv_endpoints_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_both_cv_endpoints_model_fit_pkey primary key (outcome_id, gene),
    constraint results_both_cv_endpoints_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_both_cv_endpoints_model_fit;
    
begin;
    insert into public.results_both_cv_endpoints_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_both_cv_endpoints;

    alter table public.results_both_cv_endpoints drop column model_fit;
commit;
    
create table if not exists public.results_female_cv_endpoints_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_female_cv_endpoints_model_fit_pkey primary key (outcome_id, gene),
    constraint results_female_cv_endpoints_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_female_cv_endpoints_model_fit;
    
begin;
    insert into public.results_female_cv_endpoints_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_female_cv_endpoints;

    alter table public.results_female_cv_endpoints drop column model_fit;
commit;
    
create table if not exists public.results_male_cv_endpoints_model_fit (
    outcome_id text not null,
    gene text not null,
    model_fit json not null,
    constraint results_male_cv_endpoints_model_fit_pkey primary key (outcome_id, gene),
    constraint results_male_cv_endpoints_model_fit_gene_fkey foreign key (gene) references public.genes(ensembl_id)
);
truncate public.results_male_cv_endpoints_model_fit;
    
begin;
    insert into public.results_male_cv_endpoints_model_fit (outcome_id, gene, model_fit)
    select outcome_id, gene, model_fit from public.results_male_cv_endpoints;

    alter table public.results_male_cv_endpoints drop column model_fit;
commit;
    
