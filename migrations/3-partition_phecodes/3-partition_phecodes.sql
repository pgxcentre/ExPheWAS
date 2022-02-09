begin;

-- Create the master table for results_both_phecodes
alter table results_both_phecodes rename to results_both_phecodes_old;

create table results_both_phecodes
    (like results_both_phecodes_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_both_phecodes

-- Q1
drop table if exists results_both_phecodes_q1;
create table results_both_phecodes_q1
    as (
        select * from results_both_phecodes_old
        where outcome_iid < 290
    );

alter table results_both_phecodes_q1
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q1
    add constraint results_both_phecodes_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q1
    add constraint results_both_phecodes_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q1 for values from (MINVALUE) to (290);

-- Q2
drop table if exists results_both_phecodes_q2;
create table results_both_phecodes_q2
    as (
        select * from results_both_phecodes_old
        where 290 <= outcome_iid and outcome_iid < 462
    );

alter table results_both_phecodes_q2
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q2
    add constraint results_both_phecodes_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q2
    add constraint results_both_phecodes_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q2 for values from (290) to (462);

-- Q3
drop table if exists results_both_phecodes_q3;
create table results_both_phecodes_q3
    as (
        select * from results_both_phecodes_old
        where 462 <= outcome_iid and outcome_iid < 632
    );

alter table results_both_phecodes_q3
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q3
    add constraint results_both_phecodes_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q3
    add constraint results_both_phecodes_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q3 for values from (462) to (632);

-- Q4
drop table if exists results_both_phecodes_q4;
create table results_both_phecodes_q4
    as (
        select * from results_both_phecodes_old
        where 632 <= outcome_iid and outcome_iid < 797
    );

alter table results_both_phecodes_q4
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q4
    add constraint results_both_phecodes_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q4
    add constraint results_both_phecodes_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q4 for values from (632) to (797);

-- Q5
drop table if exists results_both_phecodes_q5;
create table results_both_phecodes_q5
    as (
        select * from results_both_phecodes_old
        where 797 <= outcome_iid and outcome_iid < 963
    );

alter table results_both_phecodes_q5
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q5
    add constraint results_both_phecodes_q5_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q5
    add constraint results_both_phecodes_q5_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q5 for values from (797) to (963);

-- Q6
drop table if exists results_both_phecodes_q6;
create table results_both_phecodes_q6
    as (
        select * from results_both_phecodes_old
        where 963 <= outcome_iid and outcome_iid < 1091
    );

alter table results_both_phecodes_q6
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q6
    add constraint results_both_phecodes_q6_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q6
    add constraint results_both_phecodes_q6_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q6 for values from (963) to (1091);

-- Q7
drop table if exists results_both_phecodes_q7;
create table results_both_phecodes_q7
    as (
        select * from results_both_phecodes_old
        where 1091 <= outcome_iid and outcome_iid < 1260
    );

alter table results_both_phecodes_q7
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q7
    add constraint results_both_phecodes_q7_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q7
    add constraint results_both_phecodes_q7_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q7 for values from (1091) to (1260);

-- Q8
drop table if exists results_both_phecodes_q8;
create table results_both_phecodes_q8
    as (
        select * from results_both_phecodes_old
        where 1260 <= outcome_iid and outcome_iid < 1430
    );

alter table results_both_phecodes_q8
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q8
    add constraint results_both_phecodes_q8_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q8
    add constraint results_both_phecodes_q8_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q8 for values from (1260) to (1430);

-- Q9
drop table if exists results_both_phecodes_q9;
create table results_both_phecodes_q9
    as (
        select * from results_both_phecodes_old
        where 1430 <= outcome_iid and outcome_iid < 1602
    );

alter table results_both_phecodes_q9
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q9
    add constraint results_both_phecodes_q9_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q9
    add constraint results_both_phecodes_q9_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q9 for values from (1430) to (1602);

-- Q10
drop table if exists results_both_phecodes_q10;
create table results_both_phecodes_q10
    as (
        select * from results_both_phecodes_old
        where 1602 <= outcome_iid
    );

alter table results_both_phecodes_q10
    add primary key (outcome_iid, gene_iid);

alter table results_both_phecodes_q10
    add constraint results_both_phecodes_q10_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_phecodes_q10
    add constraint results_both_phecodes_q10_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_phecodes
    attach partition results_both_phecodes_q10 for values from (1602) to (MAXVALUE);

drop table results_both_phecodes_old;

end;
begin;

-- Create the master table for results_female_phecodes
alter table results_female_phecodes rename to results_female_phecodes_old;

create table results_female_phecodes
    (like results_female_phecodes_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_female_phecodes

-- Q1
drop table if exists results_female_phecodes_q1;
create table results_female_phecodes_q1
    as (
        select * from results_female_phecodes_old
        where outcome_iid < 293
    );

alter table results_female_phecodes_q1
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q1
    add constraint results_female_phecodes_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q1
    add constraint results_female_phecodes_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q1 for values from (MINVALUE) to (293);

-- Q2
drop table if exists results_female_phecodes_q2;
create table results_female_phecodes_q2
    as (
        select * from results_female_phecodes_old
        where 293 <= outcome_iid and outcome_iid < 464
    );

alter table results_female_phecodes_q2
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q2
    add constraint results_female_phecodes_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q2
    add constraint results_female_phecodes_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q2 for values from (293) to (464);

-- Q3
drop table if exists results_female_phecodes_q3;
create table results_female_phecodes_q3
    as (
        select * from results_female_phecodes_old
        where 464 <= outcome_iid and outcome_iid < 635
    );

alter table results_female_phecodes_q3
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q3
    add constraint results_female_phecodes_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q3
    add constraint results_female_phecodes_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q3 for values from (464) to (635);

-- Q4
drop table if exists results_female_phecodes_q4;
create table results_female_phecodes_q4
    as (
        select * from results_female_phecodes_old
        where 635 <= outcome_iid and outcome_iid < 807
    );

alter table results_female_phecodes_q4
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q4
    add constraint results_female_phecodes_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q4
    add constraint results_female_phecodes_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q4 for values from (635) to (807);

-- Q5
drop table if exists results_female_phecodes_q5;
create table results_female_phecodes_q5
    as (
        select * from results_female_phecodes_old
        where 807 <= outcome_iid and outcome_iid < 979
    );

alter table results_female_phecodes_q5
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q5
    add constraint results_female_phecodes_q5_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q5
    add constraint results_female_phecodes_q5_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q5 for values from (807) to (979);

-- Q6
drop table if exists results_female_phecodes_q6;
create table results_female_phecodes_q6
    as (
        select * from results_female_phecodes_old
        where 979 <= outcome_iid and outcome_iid < 1142
    );

alter table results_female_phecodes_q6
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q6
    add constraint results_female_phecodes_q6_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q6
    add constraint results_female_phecodes_q6_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q6 for values from (979) to (1142);

-- Q7
drop table if exists results_female_phecodes_q7;
create table results_female_phecodes_q7
    as (
        select * from results_female_phecodes_old
        where 1142 <= outcome_iid and outcome_iid < 1275
    );

alter table results_female_phecodes_q7
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q7
    add constraint results_female_phecodes_q7_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q7
    add constraint results_female_phecodes_q7_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q7 for values from (1142) to (1275);

-- Q8
drop table if exists results_female_phecodes_q8;
create table results_female_phecodes_q8
    as (
        select * from results_female_phecodes_old
        where 1275 <= outcome_iid and outcome_iid < 1443
    );

alter table results_female_phecodes_q8
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q8
    add constraint results_female_phecodes_q8_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q8
    add constraint results_female_phecodes_q8_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q8 for values from (1275) to (1443);

-- Q9
drop table if exists results_female_phecodes_q9;
create table results_female_phecodes_q9
    as (
        select * from results_female_phecodes_old
        where 1443 <= outcome_iid and outcome_iid < 1613
    );

alter table results_female_phecodes_q9
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q9
    add constraint results_female_phecodes_q9_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q9
    add constraint results_female_phecodes_q9_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q9 for values from (1443) to (1613);

-- Q10
drop table if exists results_female_phecodes_q10;
create table results_female_phecodes_q10
    as (
        select * from results_female_phecodes_old
        where 1613 <= outcome_iid
    );

alter table results_female_phecodes_q10
    add primary key (outcome_iid, gene_iid);

alter table results_female_phecodes_q10
    add constraint results_female_phecodes_q10_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_phecodes_q10
    add constraint results_female_phecodes_q10_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_phecodes
    attach partition results_female_phecodes_q10 for values from (1613) to (MAXVALUE);

drop table results_female_phecodes_old;

end;
begin;

-- Create the master table for results_male_phecodes
alter table results_male_phecodes rename to results_male_phecodes_old;

create table results_male_phecodes
    (like results_male_phecodes_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_male_phecodes

-- Q1
drop table if exists results_male_phecodes_q1;
create table results_male_phecodes_q1
    as (
        select * from results_male_phecodes_old
        where outcome_iid < 286
    );

alter table results_male_phecodes_q1
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q1
    add constraint results_male_phecodes_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q1
    add constraint results_male_phecodes_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q1 for values from (MINVALUE) to (286);

-- Q2
drop table if exists results_male_phecodes_q2;
create table results_male_phecodes_q2
    as (
        select * from results_male_phecodes_old
        where 286 <= outcome_iid and outcome_iid < 460
    );

alter table results_male_phecodes_q2
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q2
    add constraint results_male_phecodes_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q2
    add constraint results_male_phecodes_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q2 for values from (286) to (460);

-- Q3
drop table if exists results_male_phecodes_q3;
create table results_male_phecodes_q3
    as (
        select * from results_male_phecodes_old
        where 460 <= outcome_iid and outcome_iid < 642
    );

alter table results_male_phecodes_q3
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q3
    add constraint results_male_phecodes_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q3
    add constraint results_male_phecodes_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q3 for values from (460) to (642);

-- Q4
drop table if exists results_male_phecodes_q4;
create table results_male_phecodes_q4
    as (
        select * from results_male_phecodes_old
        where 642 <= outcome_iid and outcome_iid < 803
    );

alter table results_male_phecodes_q4
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q4
    add constraint results_male_phecodes_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q4
    add constraint results_male_phecodes_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q4 for values from (642) to (803);

-- Q5
drop table if exists results_male_phecodes_q5;
create table results_male_phecodes_q5
    as (
        select * from results_male_phecodes_old
        where 803 <= outcome_iid and outcome_iid < 972
    );

alter table results_male_phecodes_q5
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q5
    add constraint results_male_phecodes_q5_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q5
    add constraint results_male_phecodes_q5_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q5 for values from (803) to (972);

-- Q6
drop table if exists results_male_phecodes_q6;
create table results_male_phecodes_q6
    as (
        select * from results_male_phecodes_old
        where 972 <= outcome_iid and outcome_iid < 1135
    );

alter table results_male_phecodes_q6
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q6
    add constraint results_male_phecodes_q6_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q6
    add constraint results_male_phecodes_q6_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q6 for values from (972) to (1135);

-- Q7
drop table if exists results_male_phecodes_q7;
create table results_male_phecodes_q7
    as (
        select * from results_male_phecodes_old
        where 1135 <= outcome_iid and outcome_iid < 1260
    );

alter table results_male_phecodes_q7
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q7
    add constraint results_male_phecodes_q7_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q7
    add constraint results_male_phecodes_q7_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q7 for values from (1135) to (1260);

-- Q8
drop table if exists results_male_phecodes_q8;
create table results_male_phecodes_q8
    as (
        select * from results_male_phecodes_old
        where 1260 <= outcome_iid and outcome_iid < 1438
    );

alter table results_male_phecodes_q8
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q8
    add constraint results_male_phecodes_q8_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q8
    add constraint results_male_phecodes_q8_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q8 for values from (1260) to (1438);

-- Q9
drop table if exists results_male_phecodes_q9;
create table results_male_phecodes_q9
    as (
        select * from results_male_phecodes_old
        where 1438 <= outcome_iid and outcome_iid < 1612
    );

alter table results_male_phecodes_q9
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q9
    add constraint results_male_phecodes_q9_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q9
    add constraint results_male_phecodes_q9_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q9 for values from (1438) to (1612);

-- Q10
drop table if exists results_male_phecodes_q10;
create table results_male_phecodes_q10
    as (
        select * from results_male_phecodes_old
        where 1612 <= outcome_iid
    );

alter table results_male_phecodes_q10
    add primary key (outcome_iid, gene_iid);

alter table results_male_phecodes_q10
    add constraint results_male_phecodes_q10_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_phecodes_q10
    add constraint results_male_phecodes_q10_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_phecodes
    attach partition results_male_phecodes_q10 for values from (1612) to (MAXVALUE);

drop table results_male_phecodes_old;

end;
begin;

-- Create the master table for results_both_continuous_variables
alter table results_both_continuous_variables rename to results_both_continuous_variables_old;

create table results_both_continuous_variables
    (like results_both_continuous_variables_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_both_continuous_variables

-- Q1
drop table if exists results_both_continuous_variables_q1;
create table results_both_continuous_variables_q1
    as (
        select * from results_both_continuous_variables_old
        where outcome_iid < 22
    );

alter table results_both_continuous_variables_q1
    add primary key (outcome_iid, gene_iid);

alter table results_both_continuous_variables_q1
    add constraint results_both_continuous_variables_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_continuous_variables_q1
    add constraint results_both_continuous_variables_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_continuous_variables
    attach partition results_both_continuous_variables_q1 for values from (MINVALUE) to (22);

-- Q2
drop table if exists results_both_continuous_variables_q2;
create table results_both_continuous_variables_q2
    as (
        select * from results_both_continuous_variables_old
        where 22 <= outcome_iid and outcome_iid < 60
    );

alter table results_both_continuous_variables_q2
    add primary key (outcome_iid, gene_iid);

alter table results_both_continuous_variables_q2
    add constraint results_both_continuous_variables_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_continuous_variables_q2
    add constraint results_both_continuous_variables_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_continuous_variables
    attach partition results_both_continuous_variables_q2 for values from (22) to (60);

-- Q3
drop table if exists results_both_continuous_variables_q3;
create table results_both_continuous_variables_q3
    as (
        select * from results_both_continuous_variables_old
        where 60 <= outcome_iid and outcome_iid < 98
    );

alter table results_both_continuous_variables_q3
    add primary key (outcome_iid, gene_iid);

alter table results_both_continuous_variables_q3
    add constraint results_both_continuous_variables_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_continuous_variables_q3
    add constraint results_both_continuous_variables_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_continuous_variables
    attach partition results_both_continuous_variables_q3 for values from (60) to (98);

-- Q4
drop table if exists results_both_continuous_variables_q4;
create table results_both_continuous_variables_q4
    as (
        select * from results_both_continuous_variables_old
        where 98 <= outcome_iid
    );

alter table results_both_continuous_variables_q4
    add primary key (outcome_iid, gene_iid);

alter table results_both_continuous_variables_q4
    add constraint results_both_continuous_variables_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_continuous_variables_q4
    add constraint results_both_continuous_variables_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_continuous_variables
    attach partition results_both_continuous_variables_q4 for values from (98) to (MAXVALUE);

drop table results_both_continuous_variables_old;

end;
begin;

-- Create the master table for results_female_continuous_variables
alter table results_female_continuous_variables rename to results_female_continuous_variables_old;

create table results_female_continuous_variables
    (like results_female_continuous_variables_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_female_continuous_variables

-- Q1
drop table if exists results_female_continuous_variables_q1;
create table results_female_continuous_variables_q1
    as (
        select * from results_female_continuous_variables_old
        where outcome_iid < 22
    );

alter table results_female_continuous_variables_q1
    add primary key (outcome_iid, gene_iid);

alter table results_female_continuous_variables_q1
    add constraint results_female_continuous_variables_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_continuous_variables_q1
    add constraint results_female_continuous_variables_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_continuous_variables
    attach partition results_female_continuous_variables_q1 for values from (MINVALUE) to (22);

-- Q2
drop table if exists results_female_continuous_variables_q2;
create table results_female_continuous_variables_q2
    as (
        select * from results_female_continuous_variables_old
        where 22 <= outcome_iid and outcome_iid < 60
    );

alter table results_female_continuous_variables_q2
    add primary key (outcome_iid, gene_iid);

alter table results_female_continuous_variables_q2
    add constraint results_female_continuous_variables_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_continuous_variables_q2
    add constraint results_female_continuous_variables_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_continuous_variables
    attach partition results_female_continuous_variables_q2 for values from (22) to (60);

-- Q3
drop table if exists results_female_continuous_variables_q3;
create table results_female_continuous_variables_q3
    as (
        select * from results_female_continuous_variables_old
        where 60 <= outcome_iid and outcome_iid < 98
    );

alter table results_female_continuous_variables_q3
    add primary key (outcome_iid, gene_iid);

alter table results_female_continuous_variables_q3
    add constraint results_female_continuous_variables_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_continuous_variables_q3
    add constraint results_female_continuous_variables_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_continuous_variables
    attach partition results_female_continuous_variables_q3 for values from (60) to (98);

-- Q4
drop table if exists results_female_continuous_variables_q4;
create table results_female_continuous_variables_q4
    as (
        select * from results_female_continuous_variables_old
        where 98 <= outcome_iid
    );

alter table results_female_continuous_variables_q4
    add primary key (outcome_iid, gene_iid);

alter table results_female_continuous_variables_q4
    add constraint results_female_continuous_variables_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_continuous_variables_q4
    add constraint results_female_continuous_variables_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_continuous_variables
    attach partition results_female_continuous_variables_q4 for values from (98) to (MAXVALUE);

drop table results_female_continuous_variables_old;

end;
begin;

-- Create the master table for results_male_continuous_variables
alter table results_male_continuous_variables rename to results_male_continuous_variables_old;

create table results_male_continuous_variables
    (like results_male_continuous_variables_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_male_continuous_variables

-- Q1
drop table if exists results_male_continuous_variables_q1;
create table results_male_continuous_variables_q1
    as (
        select * from results_male_continuous_variables_old
        where outcome_iid < 22
    );

alter table results_male_continuous_variables_q1
    add primary key (outcome_iid, gene_iid);

alter table results_male_continuous_variables_q1
    add constraint results_male_continuous_variables_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_continuous_variables_q1
    add constraint results_male_continuous_variables_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_continuous_variables
    attach partition results_male_continuous_variables_q1 for values from (MINVALUE) to (22);

-- Q2
drop table if exists results_male_continuous_variables_q2;
create table results_male_continuous_variables_q2
    as (
        select * from results_male_continuous_variables_old
        where 22 <= outcome_iid and outcome_iid < 60
    );

alter table results_male_continuous_variables_q2
    add primary key (outcome_iid, gene_iid);

alter table results_male_continuous_variables_q2
    add constraint results_male_continuous_variables_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_continuous_variables_q2
    add constraint results_male_continuous_variables_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_continuous_variables
    attach partition results_male_continuous_variables_q2 for values from (22) to (60);

-- Q3
drop table if exists results_male_continuous_variables_q3;
create table results_male_continuous_variables_q3
    as (
        select * from results_male_continuous_variables_old
        where 60 <= outcome_iid and outcome_iid < 98
    );

alter table results_male_continuous_variables_q3
    add primary key (outcome_iid, gene_iid);

alter table results_male_continuous_variables_q3
    add constraint results_male_continuous_variables_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_continuous_variables_q3
    add constraint results_male_continuous_variables_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_continuous_variables
    attach partition results_male_continuous_variables_q3 for values from (60) to (98);

-- Q4
drop table if exists results_male_continuous_variables_q4;
create table results_male_continuous_variables_q4
    as (
        select * from results_male_continuous_variables_old
        where 98 <= outcome_iid
    );

alter table results_male_continuous_variables_q4
    add primary key (outcome_iid, gene_iid);

alter table results_male_continuous_variables_q4
    add constraint results_male_continuous_variables_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_continuous_variables_q4
    add constraint results_male_continuous_variables_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_continuous_variables
    attach partition results_male_continuous_variables_q4 for values from (98) to (MAXVALUE);

drop table results_male_continuous_variables_old;

end;
begin;

-- Create the master table for results_both_self_reported
alter table results_both_self_reported rename to results_both_self_reported_old;

create table results_both_self_reported
    (like results_both_self_reported_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_both_self_reported

-- Q1
drop table if exists results_both_self_reported_q1;
create table results_both_self_reported_q1
    as (
        select * from results_both_self_reported_old
        where outcome_iid < 372
    );

alter table results_both_self_reported_q1
    add primary key (outcome_iid, gene_iid);

alter table results_both_self_reported_q1
    add constraint results_both_self_reported_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_self_reported_q1
    add constraint results_both_self_reported_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_self_reported
    attach partition results_both_self_reported_q1 for values from (MINVALUE) to (372);

-- Q2
drop table if exists results_both_self_reported_q2;
create table results_both_self_reported_q2
    as (
        select * from results_both_self_reported_old
        where 372 <= outcome_iid and outcome_iid < 750
    );

alter table results_both_self_reported_q2
    add primary key (outcome_iid, gene_iid);

alter table results_both_self_reported_q2
    add constraint results_both_self_reported_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_self_reported_q2
    add constraint results_both_self_reported_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_self_reported
    attach partition results_both_self_reported_q2 for values from (372) to (750);

-- Q3
drop table if exists results_both_self_reported_q3;
create table results_both_self_reported_q3
    as (
        select * from results_both_self_reported_old
        where 750 <= outcome_iid and outcome_iid < 1129
    );

alter table results_both_self_reported_q3
    add primary key (outcome_iid, gene_iid);

alter table results_both_self_reported_q3
    add constraint results_both_self_reported_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_self_reported_q3
    add constraint results_both_self_reported_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_self_reported
    attach partition results_both_self_reported_q3 for values from (750) to (1129);

-- Q4
drop table if exists results_both_self_reported_q4;
create table results_both_self_reported_q4
    as (
        select * from results_both_self_reported_old
        where 1129 <= outcome_iid
    );

alter table results_both_self_reported_q4
    add primary key (outcome_iid, gene_iid);

alter table results_both_self_reported_q4
    add constraint results_both_self_reported_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_self_reported_q4
    add constraint results_both_self_reported_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_self_reported
    attach partition results_both_self_reported_q4 for values from (1129) to (MAXVALUE);

drop table results_both_self_reported_old;

end;
begin;

-- Create the master table for results_female_self_reported
alter table results_female_self_reported rename to results_female_self_reported_old;

create table results_female_self_reported
    (like results_female_self_reported_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_female_self_reported

-- Q1
drop table if exists results_female_self_reported_q1;
create table results_female_self_reported_q1
    as (
        select * from results_female_self_reported_old
        where outcome_iid < 365
    );

alter table results_female_self_reported_q1
    add primary key (outcome_iid, gene_iid);

alter table results_female_self_reported_q1
    add constraint results_female_self_reported_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_self_reported_q1
    add constraint results_female_self_reported_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_self_reported
    attach partition results_female_self_reported_q1 for values from (MINVALUE) to (365);

-- Q2
drop table if exists results_female_self_reported_q2;
create table results_female_self_reported_q2
    as (
        select * from results_female_self_reported_old
        where 365 <= outcome_iid and outcome_iid < 738
    );

alter table results_female_self_reported_q2
    add primary key (outcome_iid, gene_iid);

alter table results_female_self_reported_q2
    add constraint results_female_self_reported_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_self_reported_q2
    add constraint results_female_self_reported_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_self_reported
    attach partition results_female_self_reported_q2 for values from (365) to (738);

-- Q3
drop table if exists results_female_self_reported_q3;
create table results_female_self_reported_q3
    as (
        select * from results_female_self_reported_old
        where 738 <= outcome_iid and outcome_iid < 1126
    );

alter table results_female_self_reported_q3
    add primary key (outcome_iid, gene_iid);

alter table results_female_self_reported_q3
    add constraint results_female_self_reported_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_self_reported_q3
    add constraint results_female_self_reported_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_self_reported
    attach partition results_female_self_reported_q3 for values from (738) to (1126);

-- Q4
drop table if exists results_female_self_reported_q4;
create table results_female_self_reported_q4
    as (
        select * from results_female_self_reported_old
        where 1126 <= outcome_iid
    );

alter table results_female_self_reported_q4
    add primary key (outcome_iid, gene_iid);

alter table results_female_self_reported_q4
    add constraint results_female_self_reported_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_self_reported_q4
    add constraint results_female_self_reported_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_self_reported
    attach partition results_female_self_reported_q4 for values from (1126) to (MAXVALUE);

drop table results_female_self_reported_old;

end;
begin;

-- Create the master table for results_male_self_reported
alter table results_male_self_reported rename to results_male_self_reported_old;

create table results_male_self_reported
    (like results_male_self_reported_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_male_self_reported

-- Q1
drop table if exists results_male_self_reported_q1;
create table results_male_self_reported_q1
    as (
        select * from results_male_self_reported_old
        where outcome_iid < 371
    );

alter table results_male_self_reported_q1
    add primary key (outcome_iid, gene_iid);

alter table results_male_self_reported_q1
    add constraint results_male_self_reported_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_self_reported_q1
    add constraint results_male_self_reported_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_self_reported
    attach partition results_male_self_reported_q1 for values from (MINVALUE) to (371);

-- Q2
drop table if exists results_male_self_reported_q2;
create table results_male_self_reported_q2
    as (
        select * from results_male_self_reported_old
        where 371 <= outcome_iid and outcome_iid < 742
    );

alter table results_male_self_reported_q2
    add primary key (outcome_iid, gene_iid);

alter table results_male_self_reported_q2
    add constraint results_male_self_reported_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_self_reported_q2
    add constraint results_male_self_reported_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_self_reported
    attach partition results_male_self_reported_q2 for values from (371) to (742);

-- Q3
drop table if exists results_male_self_reported_q3;
create table results_male_self_reported_q3
    as (
        select * from results_male_self_reported_old
        where 742 <= outcome_iid and outcome_iid < 1124
    );

alter table results_male_self_reported_q3
    add primary key (outcome_iid, gene_iid);

alter table results_male_self_reported_q3
    add constraint results_male_self_reported_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_self_reported_q3
    add constraint results_male_self_reported_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_self_reported
    attach partition results_male_self_reported_q3 for values from (742) to (1124);

-- Q4
drop table if exists results_male_self_reported_q4;
create table results_male_self_reported_q4
    as (
        select * from results_male_self_reported_old
        where 1124 <= outcome_iid
    );

alter table results_male_self_reported_q4
    add primary key (outcome_iid, gene_iid);

alter table results_male_self_reported_q4
    add constraint results_male_self_reported_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_self_reported_q4
    add constraint results_male_self_reported_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_self_reported
    attach partition results_male_self_reported_q4 for values from (1124) to (MAXVALUE);

drop table results_male_self_reported_old;

end;
begin;

-- Create the master table for results_both_cv_endpoints
alter table results_both_cv_endpoints rename to results_both_cv_endpoints_old;

create table results_both_cv_endpoints
    (like results_both_cv_endpoints_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_both_cv_endpoints

-- Q1
drop table if exists results_both_cv_endpoints_q1;
create table results_both_cv_endpoints_q1
    as (
        select * from results_both_cv_endpoints_old
        where outcome_iid < 579
    );

alter table results_both_cv_endpoints_q1
    add primary key (outcome_iid, gene_iid);

alter table results_both_cv_endpoints_q1
    add constraint results_both_cv_endpoints_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_cv_endpoints_q1
    add constraint results_both_cv_endpoints_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_cv_endpoints
    attach partition results_both_cv_endpoints_q1 for values from (MINVALUE) to (579);

-- Q2
drop table if exists results_both_cv_endpoints_q2;
create table results_both_cv_endpoints_q2
    as (
        select * from results_both_cv_endpoints_old
        where 579 <= outcome_iid and outcome_iid < 948
    );

alter table results_both_cv_endpoints_q2
    add primary key (outcome_iid, gene_iid);

alter table results_both_cv_endpoints_q2
    add constraint results_both_cv_endpoints_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_cv_endpoints_q2
    add constraint results_both_cv_endpoints_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_cv_endpoints
    attach partition results_both_cv_endpoints_q2 for values from (579) to (948);

-- Q3
drop table if exists results_both_cv_endpoints_q3;
create table results_both_cv_endpoints_q3
    as (
        select * from results_both_cv_endpoints_old
        where 948 <= outcome_iid and outcome_iid < 1319
    );

alter table results_both_cv_endpoints_q3
    add primary key (outcome_iid, gene_iid);

alter table results_both_cv_endpoints_q3
    add constraint results_both_cv_endpoints_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_cv_endpoints_q3
    add constraint results_both_cv_endpoints_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_cv_endpoints
    attach partition results_both_cv_endpoints_q3 for values from (948) to (1319);

-- Q4
drop table if exists results_both_cv_endpoints_q4;
create table results_both_cv_endpoints_q4
    as (
        select * from results_both_cv_endpoints_old
        where 1319 <= outcome_iid
    );

alter table results_both_cv_endpoints_q4
    add primary key (outcome_iid, gene_iid);

alter table results_both_cv_endpoints_q4
    add constraint results_both_cv_endpoints_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_both_cv_endpoints_q4
    add constraint results_both_cv_endpoints_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_both_cv_endpoints
    attach partition results_both_cv_endpoints_q4 for values from (1319) to (MAXVALUE);

drop table results_both_cv_endpoints_old;

end;
begin;

-- Create the master table for results_female_cv_endpoints
alter table results_female_cv_endpoints rename to results_female_cv_endpoints_old;

create table results_female_cv_endpoints
    (like results_female_cv_endpoints_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_female_cv_endpoints

-- Q1
drop table if exists results_female_cv_endpoints_q1;
create table results_female_cv_endpoints_q1
    as (
        select * from results_female_cv_endpoints_old
        where outcome_iid < 579
    );

alter table results_female_cv_endpoints_q1
    add primary key (outcome_iid, gene_iid);

alter table results_female_cv_endpoints_q1
    add constraint results_female_cv_endpoints_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_cv_endpoints_q1
    add constraint results_female_cv_endpoints_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_cv_endpoints
    attach partition results_female_cv_endpoints_q1 for values from (MINVALUE) to (579);

-- Q2
drop table if exists results_female_cv_endpoints_q2;
create table results_female_cv_endpoints_q2
    as (
        select * from results_female_cv_endpoints_old
        where 579 <= outcome_iid and outcome_iid < 948
    );

alter table results_female_cv_endpoints_q2
    add primary key (outcome_iid, gene_iid);

alter table results_female_cv_endpoints_q2
    add constraint results_female_cv_endpoints_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_cv_endpoints_q2
    add constraint results_female_cv_endpoints_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_cv_endpoints
    attach partition results_female_cv_endpoints_q2 for values from (579) to (948);

-- Q3
drop table if exists results_female_cv_endpoints_q3;
create table results_female_cv_endpoints_q3
    as (
        select * from results_female_cv_endpoints_old
        where 948 <= outcome_iid and outcome_iid < 1319
    );

alter table results_female_cv_endpoints_q3
    add primary key (outcome_iid, gene_iid);

alter table results_female_cv_endpoints_q3
    add constraint results_female_cv_endpoints_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_cv_endpoints_q3
    add constraint results_female_cv_endpoints_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_cv_endpoints
    attach partition results_female_cv_endpoints_q3 for values from (948) to (1319);

-- Q4
drop table if exists results_female_cv_endpoints_q4;
create table results_female_cv_endpoints_q4
    as (
        select * from results_female_cv_endpoints_old
        where 1319 <= outcome_iid
    );

alter table results_female_cv_endpoints_q4
    add primary key (outcome_iid, gene_iid);

alter table results_female_cv_endpoints_q4
    add constraint results_female_cv_endpoints_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_female_cv_endpoints_q4
    add constraint results_female_cv_endpoints_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_female_cv_endpoints
    attach partition results_female_cv_endpoints_q4 for values from (1319) to (MAXVALUE);

drop table results_female_cv_endpoints_old;

end;
begin;

-- Create the master table for results_male_cv_endpoints
alter table results_male_cv_endpoints rename to results_male_cv_endpoints_old;

create table results_male_cv_endpoints
    (like results_male_cv_endpoints_old including constraints)
    partition by range (outcome_iid);

-- Partitions based on quartiles for results_male_cv_endpoints

-- Q1
drop table if exists results_male_cv_endpoints_q1;
create table results_male_cv_endpoints_q1
    as (
        select * from results_male_cv_endpoints_old
        where outcome_iid < 579
    );

alter table results_male_cv_endpoints_q1
    add primary key (outcome_iid, gene_iid);

alter table results_male_cv_endpoints_q1
    add constraint results_male_cv_endpoints_q1_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_cv_endpoints_q1
    add constraint results_male_cv_endpoints_q1_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_cv_endpoints
    attach partition results_male_cv_endpoints_q1 for values from (MINVALUE) to (579);

-- Q2
drop table if exists results_male_cv_endpoints_q2;
create table results_male_cv_endpoints_q2
    as (
        select * from results_male_cv_endpoints_old
        where 579 <= outcome_iid and outcome_iid < 948
    );

alter table results_male_cv_endpoints_q2
    add primary key (outcome_iid, gene_iid);

alter table results_male_cv_endpoints_q2
    add constraint results_male_cv_endpoints_q2_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_cv_endpoints_q2
    add constraint results_male_cv_endpoints_q2_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_cv_endpoints
    attach partition results_male_cv_endpoints_q2 for values from (579) to (948);

-- Q3
drop table if exists results_male_cv_endpoints_q3;
create table results_male_cv_endpoints_q3
    as (
        select * from results_male_cv_endpoints_old
        where 948 <= outcome_iid and outcome_iid < 1319
    );

alter table results_male_cv_endpoints_q3
    add primary key (outcome_iid, gene_iid);

alter table results_male_cv_endpoints_q3
    add constraint results_male_cv_endpoints_q3_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_cv_endpoints_q3
    add constraint results_male_cv_endpoints_q3_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_cv_endpoints
    attach partition results_male_cv_endpoints_q3 for values from (948) to (1319);

-- Q4
drop table if exists results_male_cv_endpoints_q4;
create table results_male_cv_endpoints_q4
    as (
        select * from results_male_cv_endpoints_old
        where 1319 <= outcome_iid
    );

alter table results_male_cv_endpoints_q4
    add primary key (outcome_iid, gene_iid);

alter table results_male_cv_endpoints_q4
    add constraint results_male_cv_endpoints_q4_gene_fkey
    foreign key (gene_iid) references genes(iid);

alter table results_male_cv_endpoints_q4
    add constraint results_male_cv_endpoints_q4_outcome_fkey
    foreign key (outcome_iid) references outcomes(iid);

alter table results_male_cv_endpoints
    attach partition results_male_cv_endpoints_q4 for values from (1319) to (MAXVALUE);

drop table results_male_cv_endpoints_old;

end;
