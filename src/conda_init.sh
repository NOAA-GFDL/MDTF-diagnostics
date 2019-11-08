#!/usr/bin/env bash
# This is a workaround to permit switching conda environments in a 
# non-interactive shell.
# The script is what's placed in ~/.bashrc by 'conda init bash'; 
# this doesn't get sourced by bash in non-interactive mode so we have to 
# do it manually.

# NOTE this has only been tested with conda 4.7.10 and later; I know earlier 
# versions had things in different places.

# Try to determine where conda is
if [[ $# -eq 1 ]]; then
    _MDTF_CONDA_ROOT="$1"
else
    if [[ -z "$_CONDA_ROOT" ]]; then
        _MDTF_CONDA_ROOT="$_CONDA_ROOT"
    else
        if [[ -z "$CONDA_EXE" ]]; then
            _MDTF_CONDA_ROOT="$( cd "$(dirname "$CONDA_EXE")/.."; pwd -P )"
        else
            if [[ -n "$( command -v conda)" ]]; then
                _MDTF_CONDA_ROOT="$(conda info --root)"
            else
                echo "Conda not found on \$PATH, sourcing .bashrc"
                if [[ -f $HOME/.bashrc ]]; then
                    source $HOME/.bashrc
                fi
                if [[ -n "$( command -v conda)" ]]; then
                    _MDTF_CONDA_ROOT="$(conda info --root)"
                else
                    echo "Conda still not found; aborting"
                    exit 1
                fi
            fi
        fi
    fi
fi
export _CONDA_ROOT="$_MDTF_CONDA_ROOT"
export CONDA_EXE="${_CONDA_ROOT}/bin/conda"
export _CONDA_EXE="$CONDA_EXE"
echo "Found conda at $CONDA_EXE"

__conda_setup="$($CONDA_EXE 'shell.bash' 'hook' 2> /dev/null)"
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

