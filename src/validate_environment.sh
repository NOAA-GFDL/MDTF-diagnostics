#! /usr/bin/env bash
# Script that determines whether POD's requested (non-data) dependencies are 
# present in the current environment. This is called in a subprocess by the 
# run() method of EnvironmentManager. Exit normally if everything is found, 
# otherwise exit with code 1 which aborts the subprocess. 
# It's hacky to do this in a shell script, but didn't want to assume the 
# current environment has python, etc.
set -Eeuo pipefail

verbose=false

while getopts "vp:a:b:c:z:" opt; do
    case $opt in
        v) # verbose mode: print successfully found dependencies
            verbose=true
        ;;
        p) # look for command-line program
            if command -v ${OPTARG} > /dev/null 2>&1; then
                if [ "$verbose" = true ]; then
                    echo "Found program ${OPTARG}."
                fi
                continue
            else
                echo "Fatal error: couldn't find program ${OPTARG}."
                exit 1
            fi
        ;;
        z) # look for environment variable
            if [ ! -z ${OPTARG} ]; then
                if [ "$verbose" = true ]; then
                    # echo "Environment variable ${OPTARG} is defined."
                    true
                fi
                continue
            else
                echo "Fatal error: Environment variable ${OPTARG} undefined."
                exit 1
            fi
        ;;
        a) # look for python module
           # also can't figure out how to disable pip's python2.7 warning
            if pip list --disable-pip-version-check \
                | awk -v p="${OPTARG}" 'tolower($0) ~ tolower(p) {rc = 1}; END { exit !rc }'; then
                if [ "$verbose" = true ]; then
                    echo "Found python module ${OPTARG}."
                fi
                continue
            else
                echo "Fatal error: couldn't find python module ${OPTARG}."
                exit 1
            fi
        ;;
        b) # look for NCL script
            if [ ! -z "$NCARG_ROOT" ] && [ -d "$NCARG_ROOT/lib/ncarg/nclscripts" ]; then
                if find $NCARG_ROOT/lib/ncarg/nclscripts -name ${OPTARG}.ncl -exec true {} +; then
                    if [ "$verbose" = true ]; then
                        echo "Found ${OPTARG}.ncl in $NCARG_ROOT/lib/ncarg/nclscripts."
                    fi
                    continue
                else
                    echo "Fatal error: couldn't find NCL script ${OPTARG}."
                    exit 1
                fi
            else
                echo "Fatal error: Couldn't find NCL installation directory."
                exit 1
            fi
        ;;
        c) #look for R package
            if Rscript -e 'cat(c(.libPaths(), installed.packages()[,1]), sep = "\n")' \
                | awk -v p="${OPTARG}" 'tolower($0) ~ tolower(p) {rc = 1}; END { exit !rc }'; then
                if [ "$verbose" = true ]; then
                    echo "Found R package ${OPTARG}."
                fi
                continue
            else
                echo "Fatal error: couldn't find R package ${OPTARG}."
                exit 1
            fi
        ;;
        :) echo "Warning: validate_environment called with 0 arguments." >&2
           exit 0
        ;;
        \?) echo "Invalid option -$OPTARG" >&2
        ;;
    esac
done
shift $((OPTIND -1))
exit 0