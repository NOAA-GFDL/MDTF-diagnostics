#!/usr/bin/env bash
# Driver script to create all Anaconda environments for MDTF.
# Require bash due to lingering conda compatibility issues.

set -Eeo pipefail
# Enable extended globbing, see
# https://www.gnu.org/software/bash/manual/bashref.html#Pattern-Matching
shopt -s extglob 

# get directory this script is located in
src_dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
parent_dir="$( dirname "$src_dir" )"

source "${src_dir}/conda_init.sh"

# determine if conda_env_root is defined in conda.yml settings
conda_root=$( conda info --root )

conda_env_root=$( sed -n "s/^[[:space:]]*\"conda_env_root\"[[:space:]]*:[[:space:]]*\"\(.*\)\",.*/\1/p" "${src_dir}/mdtf_settings.json" )
if [[ -z "$conda_env_root" ]]; then
    # not set, create conda env without --prefix
    use_prefix=false
    export _CONDA_ENV_ROOT="${conda_root}/envs" # true in default install only! Will need to fix
    echo "Installing into system Anaconda at $_CONDA_ENV_ROOT"
else
    # set, create and change conda envs using --prefix
    use_prefix=true
    pushd $PWD > /dev/null
    cd "${parent_dir}" # config paths are relative to repo root
    if [[ ! -d "$conda_env_root" ]]; then
        echo "Creating directory $conda_env_root"
        mkdir -p "$conda_env_root"
    fi
    cd "$conda_env_root"
    export _CONDA_ENV_ROOT=$( pwd -P )
    popd > /dev/null
    echo "Installing into $_CONDA_ENV_ROOT"
    echo "To use envs interactively, run conda config --append envs_dirs $_CONDA_ENV_ROOT"
fi

# check for --develop flag manually
env_glob="conda_env_!(dev).yml" # default is to install all envs except dev
while :; do
    case $1 in
        --develop)
            echo 'Installing developer and runtime environments.'
            env_glob="conda_env_*.yml"
            break
            ;;
        --develop-only)
            echo 'Installing only developer and base environments.'
            env_glob="conda_env_@(base|dev).yml"
            break
            ;;
        -?*)
            echo "$0: Unknown option (ignored): $1\n" >&2
            ;;
        *) # Default case: No more options, so break out of the loop.
            break
    esac
    shift
done

for env_file in "${src_dir}/"${env_glob}; do
    echo "$env_file"
    [[ -e "$env_file" ]] || continue # catch the case where nothing matches
    env_name=$( sed -n "s/^[[:space:]]*name:[[:space:]]*\([[:alnum:]_\-]*\)[[:space:]]*/\1/p" "$env_file" )
    if [[ "$use_prefix" = true ]]; then
        conda_prefix="${_CONDA_ENV_ROOT}/${env_name}"
        echo "Creating conda env ${env_name} in ${conda_prefix}"
        conda env create --force -q -p="$conda_prefix" -f="$env_file"
    else
        echo "Creating conda env ${env_name}"
        conda env create --force -q -f="$env_file"
    fi
done