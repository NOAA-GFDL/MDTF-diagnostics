#!/usr/bin/env bash
# Driver script to create all Anaconda environments for MDTF.
# Require bash due to lingering conda compatibility issues.

set -Eeo pipefail

# get directory this script is located in
script_dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

source "${script_dir}/conda_init.sh"

# determine if conda_env_root is defined in conda.yml settings
conda_root=$( conda info --root )
conda_env_root=$( sed -n "s/^[[:space:]]*conda_env_root:[[:space:]]*'\(.*\)'.*/\1/p" "${script_dir}/config.yml" )
if [ -z "$conda_env_root" ]; then
    # not set, create conda env without --prefix
    use_prefix=false
    export _CONDA_ENV_ROOT="${conda_root}/envs" # true in default install only! Will need to fix
    echo "Installing into system Anaconda at $_CONDA_ENV_ROOT"
else
    # set, create and change conda envs using --prefix
    use_prefix=true
    pushd $PWD > /dev/null
    cd "${script_dir}" # config paths are relative to script location
    if [ ! -d "$conda_env_root" ]; then
        echo "Creating directory $conda_env_root"
        mkdir "$conda_env_root"
    fi
    cd "$conda_env_root"
    export _CONDA_ENV_ROOT=$( pwd -P )
    popd > /dev/null
    echo "Installing into $_CONDA_ENV_ROOT"
    echo "To use envs interactively, run conda config --append envs_dirs $_CONDA_ENV_ROOT"
fi

for env_file in "${script_dir}"/conda_env_*.yml; do
    [ -e "$env_file" ] || continue # catch the case where nothing matches
    env_name=$( sed -n "s/^[[:space:]]*name:[[:space:]]*\([[:alnum:]_\-]*\)[[:space:]]*/\1/p" "$env_file" )
    if [ "$use_prefix" = true ]; then
        conda_prefix="${_CONDA_ENV_ROOT}/${env_name}"
        echo "Creating conda env ${env_name} in ${conda_prefix}"
        conda env create --force -q -p="$conda_prefix" -f="$env_file"
    else
        echo "Creating conda env ${env_name}"
        conda env create --force -q -f="$env_file"
    fi
done