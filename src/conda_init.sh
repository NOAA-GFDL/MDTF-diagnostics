#!/usr/bin/env bash
# This is a workaround to permit switching conda environments in a 
# non-interactive shell.
# The script is what's placed in ~/.bashrc by 'conda init bash'; 
# this doesn't get sourced by bash in non-interactive mode so we have to 
# do it manually.

# NOTE this has only been tested with conda 4.7.10 and later; I know earlier 
# versions had things in different places.

if [ ! -n "$( command -v conda)" ]; then
    echo "Conda not found on \$PATH, sourcing .bashrc"
    if [ -f $HOME/.bashrc ]; then
        source $HOME/.bashrc
    fi
fi
if [ ! -n "$( command -v conda)" ]; then
    echo "Conda still not found; aborting"
    exit 1
fi
export _CONDA_ROOT=$(conda info --root)

__conda_path="$_CONDA_ROOT"'/bin/conda'
echo "$__conda_path"
__conda_setup="$($__conda_path 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$_CONDA_ROOT/etc/profile.d/conda.sh" ]; then
        . "$_CONDA_ROOT/etc/profile.d/conda.sh"
    else
        export PATH="$_CONDA_ROOT/bin:$PATH"
    fi
fi
unset __conda_setup

