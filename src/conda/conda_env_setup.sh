#!/usr/bin/env bash
# Driver script to create Anaconda environments for MDTF.
# Require bash due to lingering conda compatibility issues.

set -Eeo pipefail
# Enable extended globbing, see
# https://www.gnu.org/software/bash/manual/bashref.html#Pattern-Matching
shopt -s extglob 

# get directory this script is located in
script_dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
# relative paths resolved relative to repo directory, which is grandparent
repo_dir=$( cd "${script_dir}/../.." ; pwd -P )

pushd "$PWD" > /dev/null
# parse aruments manually
_MDTF_CONDA_ROOT=""
_CONDA_ENV_ROOT=""
env_glob=""
while (( "$#" )); do
    case "$1" in
        -a|--all)
            env_glob="env_*.yml"  # install all envs
            shift 1
            ;;
        -e|--env)
            # specify one env by name
            env_glob="env_${2}.yml" 
            if [[ ! -f "${script_dir}/${env_glob}" ]]; then
                echo "ERROR: ${script_dir}/${env_glob} not found."
                exit 1
            fi
            shift 2
            ;;
        --dev-only)
            # dev and base only (for Travis CI/ auto testing)
            env_glob="env_@(base|dev).yml" 
            shift 1
            ;;
        -d|--env_dir)
            # specify install destination; resolve path first
            cd "$repo_dir"
            if [[ ! -d "$2" ]]; then
                echo "Creating directory $2"
                mkdir -p "$2"
            fi
            cd "$2"
            export _CONDA_ENV_ROOT="$PWD"
            shift 2
            ;;
        -c|--conda_root)
            # manually specify path to conda installation; resolve path first
            cd "$repo_dir"
            if [[ ! -d "$2" ]]; then
                echo "ERROR: can't find conda dir $2"
                exit 1
            fi
            cd "$2"
            export _MDTF_CONDA_ROOT="$PWD"
            shift 2
            ;;
        -?*)
            echo "$0: Unknown option (ignored): $1\n" >&2
            shift 1
            ;;
        *) # Default case: No more options, so break out of the loop.
            break
    esac
done
popd > /dev/null   # restore CWD

# setup conda in non-interactive shell
if [[ -z "$_MDTF_CONDA_ROOT" ]]; then
    set -- # clear cmd line
    source "${script_dir}/conda_init.sh"
else
    # pass conda installation dir to setup script
    source "${script_dir}/conda_init.sh" "$_MDTF_CONDA_ROOT"
fi
if [[ -z "$_CONDA_ENV_ROOT" ]]; then
    # not set, create conda env without --prefix
    echo "Installing envs into system Anaconda"
else
    # set, create and change conda envs using --prefix
    echo "Installing envs into $_CONDA_ENV_ROOT"
    echo "To use envs interactively, run conda config --append envs_dirs $_CONDA_ENV_ROOT"
fi

for env_file in "${script_dir}/"${env_glob}; do
    [[ -e "$env_file" ]] || continue # catch the case where nothing matches
    # get env name from reading "name:" attribute of yaml file 
    env_name=$( sed -n "s/^[[:space:]]*name:[[:space:]]*\([[:alnum:]_\-]*\)[[:space:]]*/\1/p" "$env_file" )
    if [[ -z "$_CONDA_ENV_ROOT" ]]; then
        echo "Creating conda env ${env_name}"
        "$CONDA_EXE" env create --force -q -f="$env_file"
    else
        conda_prefix="${_CONDA_ENV_ROOT}/${env_name}"
        echo "Creating conda env ${env_name} in ${conda_prefix}"
        "$CONDA_EXE" env create --force -q -p="$conda_prefix" -f="$env_file"
    fi
done
