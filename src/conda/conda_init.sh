#!/usr/bin/env bash

# This is a workaround to permit switching conda environments in a 
# non-interactive shell.
# The script is what's placed in ~/.bashrc by 'conda init bash'; 
# this doesn't get sourced by bash in non-interactive mode so we have to 
# do it manually. See https://github.com/conda/conda/issues/7980 .

# NOTE this has only been tested with conda 4.7.10 and later; I know earlier 
# versions had things in different places.

# parse aruments manually
_TEMP_CONDA_ROOT=""
_TEMP_CONDA_EXE=""
_v=1
while (( "$#" )); do
    case "$1" in
        -v)
            _v=2 # verbose output for debugging
            shift 1
            ;;
        -q)
            _v=0 # suppress output
            shift 1
            ;;
        ?*)
            # Assume nonempty input is user-specified CONDA_ROOT
            if [ ! -d "$1" ]; then
                echo "ERROR: \"$1\" not a directory" 1>&2
                exit 1
            fi
            _TEMP_CONDA_ROOT="$1"
            shift 1
            ;;
        *) # Default case: No more options, so break out of the loop.
            break
    esac
done

# if we got _TEMP_CONDA_ROOT from command line, see if that works
if [ -d "$_TEMP_CONDA_ROOT" ]; then
    # let command line value override pre-existing _CONDA_ROOT, in case user
    # is specifying personal vs. site installation of conda
    if [[ $_v -eq 2 && -d "$_CONDA_ROOT" ]]; then
        echo "WARNING: overriding ${_CONDA_ROOT} with ${_TEMP_CONDA_ROOT}" 1>&2
    fi
    _CONDA_ROOT="$_TEMP_CONDA_ROOT"
    if [[ $_v -eq 2 && -x "$CONDA_EXE" ]]; then
        echo "WARNING: user supplied CONDA_ROOT so unsetting existing CONDA_EXE" 1>&2
    fi
    CONDA_EXE=""
    if [ $_v -eq 2 ]; then echo "CONDA_ROOT set from command line"; fi
fi
# if not, maybe we were run from an interactive shell and inherited the info
if [ ! -d "$_CONDA_ROOT" ]; then
    if [ -x "$CONDA_EXE" ]; then
        if [ $_v -eq 2 ]; then echo "CONDA_EXE set from environment"; fi
        _TEMP_CONDA_ROOT="$( "$CONDA_EXE" info --base 2> /dev/null )"
    else
        _TEMP_CONDA_ROOT="$( conda info --base 2> /dev/null )"
    fi
    if [ -d "$_TEMP_CONDA_ROOT" ]; then
        _CONDA_ROOT="$_TEMP_CONDA_ROOT"
        if [ $_v -eq 2 ]; then echo "CONDA_ROOT set from environment"; fi
    fi
fi
# if not, run user's shell in interactive mode. Subshell output could have 
# arbitrary text output in it, since user's init scripts may be setting prompt
# and generating output in any number of ways. We try to extract the paths by 
# delimiting them with (hopefully uncommon) vertical tab characters (\v) and 
# using awk to extract whatever text is found between those two field separators.
if [ ! -d "$_CONDA_ROOT" ]; then
    if [ $_v -eq 2 ]; then echo "Setting conda from $SHELL -i"; fi
    _TEMP_CONDA_ROOT=$( "$SHELL" -i -c "_temp=\$( conda info --base ) && echo \"\v\${_temp}\v\"" | awk 'BEGIN { FS = "\v" } ; { print $2 }' )
    if [ $_v -eq 2 ]; then echo "Received CONDA_ROOT=\"${_TEMP_CONDA_ROOT}\""; fi
    if [[ -d "$_TEMP_CONDA_ROOT" ]]; then
        _CONDA_ROOT="$_TEMP_CONDA_ROOT"
        if [ $_v -eq 2 ]; then echo "Found CONDA_ROOT"; fi
    fi
    _TEMP_CONDA_EXE="$( "$SHELL" -i -c "echo \"\v\${CONDA_EXE}\v\"" | awk 'BEGIN { FS = "\v" } ; { print $2 }' )"
    if [ $_v -eq 2 ]; then echo "Received CONDA_EXE=\"${_TEMP_CONDA_EXE}\""; fi
    if [[ ! -x "$CONDA_EXE" && -x "$_TEMP_CONDA_EXE" ]]; then
        CONDA_EXE="$_TEMP_CONDA_EXE"
        if [ $_v -eq 2 ]; then echo "Found CONDA_EXE"; fi
    fi
fi
# found root but not exe
if [[ -d "$_CONDA_ROOT" && ! -x "$CONDA_EXE" ]]; then
    if [ $_v -eq 2 ]; then echo "Looking for conda executable in ${_CONDA_ROOT}"; fi
    if [ -x "${_CONDA_ROOT}/bin/conda" ]; then
        CONDA_EXE="${_CONDA_ROOT}/bin/conda"
        if [ $_v -eq 2 ]; then echo "Found CONDA_EXE"; fi
    elif [ -x "${_CONDA_ROOT}/condabin/conda" ]; then
        CONDA_EXE="${_CONDA_ROOT}/condabin/conda"
        if [ $_v -eq 2 ]; then echo "Found CONDA_EXE"; fi
    fi
fi
# found exe but not root
if [[ -x "$CONDA_EXE" && ! -d "$_CONDA_ROOT" ]]; then
    if [ $_v -eq 2 ]; then echo "Running $CONDA_EXE to find conda root"; fi
    _TEMP_CONDA_ROOT="$( "$CONDA_EXE" info --base 2> /dev/null )"
    if [ -d "$_TEMP_CONDA_ROOT" ]; then
        _CONDA_ROOT="$_TEMP_CONDA_ROOT"
        if [ $_v -eq 2 ]; then echo "Found CONDA_ROOT"; fi
    fi
fi

if [[ -x "$CONDA_EXE" && -d "$_CONDA_ROOT" ]]; then
    if [ $_v -ne 0 ]; then
        # Conda env manager reads this output
        echo "_CONDA_EXE=${CONDA_EXE}"
        echo "_CONDA_ROOT=${_CONDA_ROOT}"
    fi
    # in case these weren't exported already
    export _CONDA_ROOT="$_CONDA_ROOT"
    export CONDA_EXE="$CONDA_EXE"
else
    if [ ! -d "$_CONDA_ROOT" ]; then
        echo "ERROR: search for conda base dir failed (${_CONDA_ROOT})" 1>&2
    fi
    if [ ! -x "$CONDA_EXE" ]; then
        echo "ERROR: search for conda executable failed (${CONDA_EXE})" 1>&2
    fi
    exit 1
fi

# workaround for $PATH being set incorrectly
# https://github.com/conda/conda/issues/9392#issuecomment-617345019
unset CONDA_SHLVL
# finally run conda's init script
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

