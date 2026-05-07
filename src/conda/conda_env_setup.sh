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
    echo "   -cr, --conda_root    root path to anaconda or miniconda directory"
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
# parse aruments manually
_MDTF_CONDA_ROOT=""
_CONDA_ENV_ROOT=""
make_envs="true"
env_glob=""
while (( "$#" )); do
    case "$1" in
         # call the help function
        -h | --help)
            display_help
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

    # install envs with mamba (https://github.com/mamba-org/mamba) for
    # performance reasons; need to find mamba executable, or install it if not
    # present
    _INSTALL_EXE=$( command -v mamba ) || true
    mamba_temp="false"
    if [[ ! -x "$_INSTALL_EXE" ]]; then
        echo "Couldn't find mamba executable; installing in temp environment."
        mamba_temp="true"
        conda create --force -qy -n _MDTF_install_temp
        conda install -qy mamba -n _MDTF_install_temp -c conda-forge
        # still no idea why this works but "conda activate" doesn't
        conda activate _MDTF_install_temp
        _INSTALL_EXE=$( command -v mamba ) || true
    fi
    if [[ ! -x "$_INSTALL_EXE" ]]; then
        echo "Mamba installation failed."
        exit 1
    fi

    # create all envs in a loop
    "$_INSTALL_EXE" clean -qi
    for env_file in "${script_dir}/"${env_glob}; do
        [ -e "$env_file" ] || continue # catch the case where nothing matches
        # get env name from reading "name:" attribute of yaml file
        env_name=$( sed -n "s/^[[:space:]]*name:[[:space:]]*\([[:alnum:]_\-]*\)[[:space:]]*/\1/p" "$env_file" )
        if [ -z "$_CONDA_ENV_ROOT" ]; then
            # need to set manually, otherwise mamba will install in a subdir
            # of its env's directory
            conda_prefix="${_CONDA_ROOT}/envs/${env_name}"
        else
            conda_prefix="${_CONDA_ENV_ROOT}/${env_name}"
        fi
	echo "$conda_prefix"
	if [ -d "$conda_prefix" ]; then
		# remove conda env of same name
		echo "Removing previous conda env ${env_name}..."
		conda remove -q -y -n "$env_name" --all
		echo "... previous env ${env_name} removed."
	fi
        echo "Creating conda env ${env_name} in ${conda_prefix}..."
        "$_INSTALL_EXE" env create -qy -p "$conda_prefix" -f "$env_file"
        echo "... conda env ${env_name} created."
    done
    "$_INSTALL_EXE" clean -aqy

    if [ "$mamba_temp" = "true" ]; then
        # delete the temp env we used for the install
        conda deactivate
        conda env remove -y -n _MDTF_install_temp
    fi
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
