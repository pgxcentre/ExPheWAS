#!/usr/bin/env bash

# Bash script used to import blocks of results into the exPheWAS database.
# This script assumes the directory structure used for the main analysis.

if [ "$#" -ne 2 ]; then
    echo "Usage: import_block.sh block_path variance_explained"
    exit 1
fi


root=$1
export pct_var=$2


# Remove trailing slash if needed.
root=$(echo $root | sed 's-/$--')


import_file() {
    path=$1

    # Infer metadata from path.
    filename=$(basename $path)

    gene=$(echo $filename | cut -d_ -f 2)

    analysis=$(echo $filename | cut -d_ -f 3- | sed 's/.csv//')

    case $analysis in
        cv_endpoints)
            analysis_val=CV_ENDPOINTS
            ;;
        icd10_blocks)
            analysis_val=ICD10_BLOCK
            ;;
        linear)
            analysis_val=CONTINUOUS_VARIABLE
            ;;
        icd10_three_chars)
            analysis_val=ICD10_3CHAR
            ;;
        icd10_raw)
            analysis_val=ICD10_RAW
            ;;
        self_reported_diseases)
            analysis_val=SELF_REPORTED
            ;;
        *)
            echo "Invalid analysis type: $analysis"
            exit 1
    esac


    exphewas-db \
        import-results \
        --gene $gene \
        --analysis $analysis_val \
        --pct-variance $pct_var \
        $path

}
export -f import_file

find $root -type f -name 'phewas_*' -print0 | xargs -0 -n 1 -I% bash -c 'import_file "%"'
