#!/usr/bin/env bash
# Deploys an ExPheWAS instance to a server.

set -eo pipefail

usage="$(basename "$0") BACKEND FRONTEND DESTINATION PYTHON_VENV_PREFIX"

create_python_venv() {
    # Creates a python environment and install newest versions of pip,
    # setuptools and wheel
    local venv_dir=$1

    python3 -m venv "$venv_dir"
    . "$venv_dir"/bin/activate

    pip install -U pip setuptools wheel
    deactivate
}

install_frontend() {
    # Cleans the directory, and extract the frontend
    local archive_name=$1
    local destination=$2

    rm -rf "$destination"/dist
    tar -C "$destination" -xf "$archive_name"
}

install_backend() {
    # Cleans the python virtual environment, and install the backend
    local package=$1
    local python_venv=$2

    source "$python_venv"/bin/activate

    if grep exphewas > /dev/null < <(pip list); then
        pip uninstall -y exphewas
    fi

    pip install "$package"
}

main() {
    local backend=$1
    local frontend=$2
    local destination=$3
    local python_venv_prefix=$4

    # Checking options and arguments
    if [[ -z "$backend" || -z "$frontend" || -z "$destination" || -z "$python_venv_prefix" ]]; then
        echo "$usage" >&2
        exit 1
    fi

    # Checking the backend
    if [[ ! -f "$backend" ]]; then
        echo "$backend: no such file" >&2
        exit 1
    fi

    # Checking the frontend
    if [[ ! -f "$frontend" ]]; then
        echo "$frontend: no such file" >&2
        exit 1
    fi

    # Retrieving the backend version
    local backend_version
    backend_version="v$(echo "$backend" | grep -o -E "[0-9]+\.[0-9]+\.[0-9]+" | cut -d. -f1)"

    # Checking if we have a python virtual environment directory
    local python_venv="$python_venv_prefix"-"$backend_version"
    if [[ ! -f "$python_venv"/bin/activate ]]; then
        create_python_venv "$python_venv"
    fi

    # Creating the output directory, if it doesn't exists
    if [[ ! -d "$destination"/"$backend_version" ]]; then
        mkdir -p "$destination"/"$backend_version"
    fi

    # Installing the frontend
    install_frontend "$frontend" "$destination"/"$backend_version"

    # Installing the backend
    install_backend "$backend" "$python_venv"
}

main "$@"
