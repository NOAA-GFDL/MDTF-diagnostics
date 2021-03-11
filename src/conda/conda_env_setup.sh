#!/usr/bin/env bash
# Driver script to create Anaconda environments for MDTF.
# Require bash due to lingering conda compatibility issues.

set -Eeo pipefail
# Enable extended globbing, see
# https://www.gnu.org/software/bash/manual/bashref.html#Pattern-Matching
shopt -s extglob 

# get directory this script is located in, resolving any 
# symlinks/aliases (https://stackoverflow.com/a/246128)
_source="${BASH_SOURCE[0]}"
while [ -h "$_source" ]; do # resolve $_source until the file is no longer a symlink
    script_dir="$( cd -P "$( dirname "$_source" )" >/dev/null 2>&1 && pwd )"
    _source="$( readlink "$_source" )"
    # if $_source was a relative symlink, we need to resolve it relative to the 
    # path where the symlink file was located
    [[ $_source != /* ]] && _source="$script_dir/$_source" 
done
script_dir="$( cd -P "$( dirname "$_source" )" >/dev/null 2>&1 && pwd )"

# relative paths resolved relative to repo directory, which is grandparent 
# of dir this script is in
repo_dir="$( cd -P "$script_dir" >/dev/null 2>&1 && cd ../../ && pwd )"

pushd "$PWD" > /dev/null
# parse aruments manually
_MDTF_CONDA_ROOT=""
_CONDA_ENV_ROOT=""
make_envs="true"
use_mamba="false"
env_glob=""
while (( "$#" )); do
    case "$1" in
        -a|--all)
            # install all envs except dev environment
            env_glob="env_!(dev).yml"
            shift 1
            ;;
        -e|--env)
            # specify one env by name
            env_glob="env_${2}.yml" 
            if [ ! -f "${script_dir}/${env_glob}" ]; then
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
        --all-dev)
            # all envs, including dev
            env_glob="env_*.yml"
            shift 1
            ;;
        -d|--env_dir)
            # specify install destination; resolve path first
            cd "$repo_dir"
            if [ ! -d "$2" ]; then
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
            if [ ! -d "$2" ]; then
                echo "ERROR: can't find conda dir $2"
                exit 1
            fi
            cd "$2"
            export _MDTF_CONDA_ROOT="$PWD"
            shift 2
            ;;
        --wrapper-only)
            # Don't change conda envs; only update wrapper shell script
            echo "Updating wrapper script and leaving envs unchanged."
            make_envs="false"
            shift 1
            ;;
        --mamba)
            # Install envs with mamba package manager 
            # (https://github.com/mamba-org/mamba), assumed to be on $PATH
            echo "Using `mamba` instead of `conda` for installation."
            use_mamba="true"
            shift 1
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
if [ -z "$_MDTF_CONDA_ROOT" ]; then
    set -- # clear cmd line
    . "${script_dir}/conda_init.sh" -v
else
    # pass conda installation dir to setup script
    . "${script_dir}/conda_init.sh" -v "$_MDTF_CONDA_ROOT"
fi

if [ "$make_envs" = "true" ]; then
    if [ -z "$_CONDA_ENV_ROOT" ]; then
        # not set, create conda env without --prefix
        echo "Installing envs into system Anaconda"
    else
        # set, create and change conda envs using --prefix
        echo "Installing envs into $_CONDA_ENV_ROOT"
        echo "To use envs interactively, run \"conda config --append envs_dirs $_CONDA_ENV_ROOT\""
    fi

    if [ "$use_mamba" = "true" ]; then
        # install envs with mamba; need to find mamba executable
        _INSTALL_EXE=$( command -v mamba )
        if [[ ! -x "$_INSTALL_EXE" ]]; then
            echo "Couldn't find mamba executable."
            exit 1 # could also fall back to using conda
        fi
    else
        # use conda for install (& dependency resolution)
        _INSTALL_EXE="$CONDA_EXE"
    fi

    # create all envs in a loop
    "$_INSTALL_EXE" clean -i
    for env_file in "${script_dir}/"${env_glob}; do
        [ -e "$env_file" ] || continue # catch the case where nothing matches
        # get env name from reading "name:" attribute of yaml file 
        env_name=$( sed -n "s/^[[:space:]]*name:[[:space:]]*\([[:alnum:]_\-]*\)[[:space:]]*/\1/p" "$env_file" )
        if [ -z "$_CONDA_ENV_ROOT" ]; then
            echo "Creating conda env ${env_name}..."
            "$_INSTALL_EXE" env create --force -q -f="$env_file"
        else
            conda_prefix="${_CONDA_ENV_ROOT}/${env_name}"
            echo "Creating conda env ${env_name} in ${conda_prefix}..."
            "$_INSTALL_EXE" env create --force -q -p="$conda_prefix" -f="$env_file"
        fi
        echo "... conda env ${env_name} created."
    done
    "$_INSTALL_EXE" clean -ay
fi

# create script wrapper to activate base environment
_CONDA_WRAPPER="${repo_dir}/mdtf"
if [ -e "$_CONDA_WRAPPER" ]; then
    rm -f "$_CONDA_WRAPPER"
fi
echo '#!/usr/bin/env bash' > "$_CONDA_WRAPPER"
echo "# This wrapper script is generated by conda_env_setup.sh." >> "$_CONDA_WRAPPER"
echo "_mdtf=\"${repo_dir}\"" >> "$_CONDA_WRAPPER"
echo "source \"\${_mdtf}/src/conda/conda_init.sh\" -q \"${_CONDA_ROOT}\"" >> "$_CONDA_WRAPPER"
if [ -z "$_CONDA_ENV_ROOT" ]; then
    echo "conda activate _MDTF_base" >> "$_CONDA_WRAPPER"
else
    echo "conda activate ${_CONDA_ENV_ROOT}/_MDTF_base" >> "$_CONDA_WRAPPER"
fi
echo "\"\${_mdtf}/mdtf_framework.py\" \"\$@\"" >> "$_CONDA_WRAPPER"
echo "exit \$?" >> "$_CONDA_WRAPPER"
chmod +x "$_CONDA_WRAPPER"
echo "Created MDTF wrapper script at ${_CONDA_WRAPPER}"
