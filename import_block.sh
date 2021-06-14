#!/usr/bin/env bash

# Bash script used to import blocks of results into the exPheWAS database.
# This script assumes the directory structure used for the main analysis.

if [ "$#" -lt 2 ]; then
    echo "Usage: import_block.sh block_path_tar sex_subset"
    exit 1
fi


tar_file=$1
sex_subset=$2  # BOTH, FEMALE_ONLY, MALE_ONLY


block=$(basename $tar_file | sed 's/.tar//')

if [ -d $block ]; then
    echo "Directory ${block} already exists and would be overwritten by extraction."
    exit 1
fi

tar -xf $tar_file

genes=$(ls -1 $block | grep results | cut -f 2 -d_ | sort | uniq)

echo "Importing ${tar_file} (${sex_subset})"

import_gene() {
    block=$1
    sex_subset=$2
    gene=$3

    path="${block}/results_${gene}"

    time exphewas-db \
        import-results \
        --sex-subset $sex_subset \
        ${path}_continuous &

    time exphewas-db \
        import-results \
        --sex-subset $sex_subset \
        --min-n-cases 100 \
        ${path}_binary

    wait
}
export -f import_gene

# for gene in $genes; do
#     import_gene $block $sex_subset $gene
# done
parallel -j 4 \
    import_gene $block $sex_subset \
    ::: $genes

rm -r $block
