#! /usr/bin/env bash
set -Eeuo pipefail

while getopts "p:a:b:c:z:" opt; do
    case $opt in
        p) # look for command-line program
            if command -v ${OPTARG} > /dev/null 2>&1; then
                continue
            else
                echo "Fatal error: couldn't find program ${OPTARG}."
                exit 1
            fi
        ;;
        z) # look for environment variable
            if [ -z ${OPTARG} ]; then
                continue
            else
                echo "Fatal error: Environment variable ${OPTARG} undefined."
                exit 1
            fi
        ;;
        a) # look for python module
           # tail -n necessary to avoid getting broken pipe errors?
           # also can't figure out how to disable pip's python2.7 warning
            if pip list --no-color --disable-pip-version-check | tail -n +1 | grep -qF ${OPTARG}; then
                continue
            else
                echo "Fatal error: couldn't find python module ${OPTARG}."
                exit 1
            fi
        ;;
        b) # look for NCL script
            if [ -z "$NCARG_ROOT" && -d "$NCARG_ROOT/lib/ncarg/nclscripts" ]; then
                if find $NCARG_ROOT/lib/ncarg/nclscripts -name ${OPTARG}; then
                    continue
                else
                    echo "Fatal error: couldn't find NCL script ${OPTARG}."
                    exit 1
            else
                echo "Fatal error: Couldn't find NCL installation directory."
                exit 1
            fi
        ;;
        c) #look for R package
            if Rscript -e 'cat(c(.libPaths(), installed.packages()[,1]), sep = "\n")' | grep -qF ${OPTARG}; then
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