#!/usr/bin/env bash
# Driver script to create Anaconda environments for MDTF.
# Require bash due to lingering conda compatibility issues.

set -Eeo pipefail
# Enable extended globbing, see
# https://www.gnu.org/software/bash/manual/bashref.html#Pattern-Matching
shopt -s extglob
#########################
# The command line help
# Everything is stackoverflow: https://stackoverflow.com/questions/5474732/how-can-i-add-a-help-method-to-a-shell-script
#########################
display_help() {
    echo "Usage: ./src/conda/conda_env_setup [option 1, ... option n]" >&2
    echo ""
    echo "   -a, --all    build all conda environments in src/conda with 'env' prefix"
    echo "   -e, --env [base | python3_base | R_base | NCL_base]    build specific environment defined in src/conda/env_[name]_base.yml "
    echo "   -mr, --micromamba_root    root path to micromamba directory"
    echo "   --micromamba_exe    full path to micromamba executable on your system"
    echo "   -d, --env_dir    directory path where conda environments will be installed"
    echo "   --wrapper_only   do not change conda enviroments; only build the mdtf wrapper"
    echo ""
    # echo some stuff here for the -a or --add-options
    exit 1
}

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
# parse arguments manually
_MDTF_CONDA_ROOT=""
_MDTF_MICROMAMBA_ROOT=""
_MDTF_MICROMAMBA_EXE=""
_CONDA_ENV_ROOT=""
make_envs="true"
env_glob=""
while (( "$#" )); do
    case "$1" in
        -h | --help)
          display_help # call the help function
          exit 0
          ;;
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
            echo "$_CONDA_ENV_ROOT"
            shift 2
            ;;
         -mr|--micromamba_root)
            # manually specify path to micromamba installation; resolve path first
            cd "$repo_dir"
            if [ ! -d "$2" ]; then
                echo "ERROR: can't find micromamba directory $2"
                exit 1
            fi
            cd "$2"
            export _MDTF_MICROMAMBA_ROOT="$PWD"
            shift 2
            ;;
        --micromamba_exe)
            # path to micromamba executable
            if [ ! -x "$2" ]; then
                echo "ERROR: can't find micromamba executable $2"
                exit 1
            fi
            export _MDTF_MICROMAMBA_EXE="$2"
            shift 2
            ;;
        --wrapper-only)
            # Don't change conda envs; only update wrapper shell script
            echo "Updating wrapper script and leaving envs unchanged."
            make_envs="false"
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

# setup conda for non-interactive shell
# NB: 'conda' isn't an executable; it's created as a shell alias. This is why we
# invoke it as 'conda' below, instead of the absolute path in $CONDA_EXE.
if [[ -z "$_MDTF_MICROMAMBA_ROOT" ]]; then
    set -- # clear cmd line
    echo "calling micromamba_init.sh"
    . "${script_dir}/micromamba_init.sh" -v
elif [ -n "$_MDTF_MICROMAMBA_ROOT" ]; then
    if [ -n "$_MDTF_MICROMAMBA_EXE" ]; then
       # pass micromamba installation dir and executable path to setup script
       echo "calling micromamba_init.sh on $_MDTF_MICROMAMBA_ROOT and $_MDTF_MICROMAMBA_EXE"
       . "${script_dir}/micromamba_init.sh" -v --micromamba_root "$_MDTF_MICROMAMBA_ROOT" --micromamba_exe "$_MDTF_MICROMAMBA_EXE"
    else
       . "${script_dir}/micromamba_init.sh" -v --micromamba_root "$_MDTF_MICROMAMBA_ROOT"
    fi
fi

echo "MICROMAMBA_ROOT is $_CONDA_ROOT"
echo "MICROMAMBA_EXE is $CONDA_EXE"

if [ "$make_envs" = "true" ]; then
    if [ -z "$_CONDA_ENV_ROOT" ]; then
        # not set, create conda env without --prefix
        echo "Installing envs into system Anaconda"
    else
        # set, create and change conda envs using --prefix
        echo "Installing envs into $_CONDA_ENV_ROOT"
        echo "To use envs interactively, run \"conda config --append envs_dirs $_CONDA_ENV_ROOT\""
    fi

    if [ -n "$_MDTF_MICROMAMBA_ROOT" ]; then
         _INSTALL_EXE=$( command -v micromamba ) || true
        if [[ -z "$_INSTALL_EXE" ]]; then
            echo "Error: micromamba not found."
            exit 1
        fi
    fi

    # create all envs in a loop
    "$_INSTALL_EXE" clean -qi
    for env_file in "${script_dir}/"${env_glob}; do
        [ -e "$env_file" ] || continue # catch the case where nothing matches
        # get env name from reading "name:" attribute of yaml file
        env_name=$( sed -n "s/^[[:space:]]*name:[[:space:]]*\([[:alnum:]_\-]*\)[[:space:]]*/\1/p" "$env_file" )
        if [ -n "$_CONDA_ENV_ROOT" ]; then
            conda_prefix="${_CONDA_ENV_ROOT}/${env_name}"
        else
            conda_prefix="${_MDTF_MICROMAMBA_ROOT}/envs/${env_name}"
        fi

        echo "Creating conda env ${env_name} in ${conda_prefix}..."
        "$_INSTALL_EXE" create -q -y -p "$conda_prefix" -f "$env_file"
        echo "... conda env ${env_name} created."
    done
    "$_INSTALL_EXE" clean -aqy
fi

# create script wrapper to activate base environment
echo "creating mdtf wrapper"
_CONDA_WRAPPER="${repo_dir}/mdtf"
if [ -e "$_CONDA_WRAPPER" ]; then
    rm -f "$_CONDA_WRAPPER"
fi
echo '#!/usr/bin/env bash' > "$_CONDA_WRAPPER"
echo "# This wrapper script is generated by conda_env_setup.sh." >> "$_CONDA_WRAPPER"
echo "_mdtf=\"${repo_dir}\"" >> "$_CONDA_WRAPPER"

if [ -n "$_MDTF_MICROMAMBA_EXE" ]; then
   echo "source \"\${_mdtf}/src/conda/micromamba_init.sh\" -q --micromamba_root \"${_CONDA_ROOT}\" --micromamba_exe \"${_MDTF_MICROMAMBA_EXE}\"" >> "$_CONDA_WRAPPER"
else
   echo "source \"\${_mdtf}/src/conda/micromamba_init.sh\" -q --micromamba_root \"${_CONDA_ROOT}\"" >> "$_CONDA_WRAPPER"
fi

echo "micromamba activate _MDTF_base" >> "$_CONDA_WRAPPER"

echo "\"\${_mdtf}/mdtf_framework.py\" \"\$@\"" >> "$_CONDA_WRAPPER"
echo "exit \$?" >> "$_CONDA_WRAPPER"
chmod +x "$_CONDA_WRAPPER"
echo "Created MDTF wrapper script at ${_CONDA_WRAPPER}"
