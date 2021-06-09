#!/usr/bin/env bash

# Bash script used to import blocks of results into the exPheWAS database.
# This script assumes the directory structure used for the main analysis.

if [ "$#" -lt 2 ]; then
    echo "Usage: import_block.sh block_path_tar sex_subset [n_cpus]"
    exit 1
fi


tar_file=$1
sex_subset=$2  # BOTH, FEMALE_ONLY, MALE_ONLY
n_cpus=${3:-0}

if [ "$n_cpus" -eq "0" ]; then
    n_cpus=$(nproc --all)
fi
echo "Importing block using ${n_cpus} CPUs"


block=$(basename $tar_file | sed 's/.tar//')

if [ -d $block ]; then
    echo "Directory ${block} already exists and would be overwritten by extraction."
    exit 1
fi

tar -xf $tar_file

genes=$(ls -1 $block | grep results | cut -f 2 -d_ | sort | uniq | head -n 4)


import_gene() {
    block=$1
    sex_subset=$2
    gene=$3
    cont_or_bin=$4

    path="${block}/results_${gene}_${cont_or_bin}"

    exphewas-db \
        import-results \
        --sex-subset $sex_subset \
        $path
}
export -f import_gene

parallel -j $n_cpus \
    import_gene $block $sex_subset \
    ::: $genes \
    ::: continuous binary

rm -r $block
