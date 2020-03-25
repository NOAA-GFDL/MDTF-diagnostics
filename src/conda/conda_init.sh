#!/usr/bin/env bash

# This is a workaround to permit switching conda environments in a 
# non-interactive shell.
# The script is what's placed in ~/.bashrc by 'conda init bash'; 
# this doesn't get sourced by bash in non-interactive mode so we have to 
# do it manually.

# NOTE this has only been tested with conda 4.7.10 and later; I know earlier 
# versions had things in different places.

# Try to determine where conda is
function find_conda {
    _MDTF_CONDA_ROOT="$( conda info --base 2> /dev/null )"
    if [[ $? -ne 0 || -z "$_MDTF_CONDA_ROOT" ]]; then
        # see if env vars tell us anything
        if [[ -n "$CONDA_EXE" ]]; then
            _MDTF_CONDA_ROOT="$( cd "$(dirname "$CONDA_EXE")/.."; pwd -P )"
        elif [[ -n "$_CONDA_ROOT" ]]; then
            _MDTF_CONDA_ROOT="$_CONDA_ROOT"
        else
            _MDTF_CONDA_ROOT="" # failure
        fi
    fi
}

_MDTF_CONDA_ROOT=""
if [[ $# -eq 1 ]]; then
    _MDTF_CONDA_ROOT="$1"  # passed the path to use on command line
fi
if [[ -z "$_MDTF_CONDA_ROOT" ]]; then
    find_conda
fi
if [[ -z "$_MDTF_CONDA_ROOT" ]]; then
    echo "conda not found, sourcing ~/.bashrc"
    if [[ -f "$HOME/.bashrc" ]]; then
        source "$HOME/.bashrc"
    fi
    find_conda
fi
if [[ -z "$_MDTF_CONDA_ROOT" ]]; then
    echo "ERROR: still can't find conda"
fi
export _CONDA_ROOT="$_MDTF_CONDA_ROOT"
export CONDA_EXE="${_CONDA_ROOT}/bin/conda"
export _CONDA_EXE="$CONDA_EXE"
if [[ -x "$CONDA_EXE" ]]; then
    echo "_CONDA_EXE=${CONDA_EXE}"
    echo "_CONDA_ROOT=${_CONDA_ROOT}"
else
    echo "ERROR: no conda executable at $CONDA_EXE"
    exit 1
fi

# assume we've found conda, now run Anaconda's init script
__conda_setup="$( $CONDA_EXE 'shell.bash' 'hook' 2> /dev/null )"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "${_CONDA_ROOT}/etc/profile.d/conda.sh" ]; then
        . "${_CONDA_ROOT}/etc/profile.d/conda.sh"
    else
        export PATH="${_CONDA_ROOT}/bin:$PATH"
    fi
fi
unset __conda_setup

