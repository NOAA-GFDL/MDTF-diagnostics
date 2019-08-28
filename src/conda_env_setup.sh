#!/usr/bin/env bash
# Driver script to create all Anaconda environments for MDTF.
# Require bash due to lingering conda compatibility issues.

set -Eeo pipefail

# get directory this script is located in
script_dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

source "${script_dir}/conda_init.sh"

for env_file in "${script_dir}"/conda_env_*.yml; do
    [ -e "$env_file" ] || continue # catch the case where nothing matches
    echo "Creating conda env from ${env_file}"
    conda env create --force -q -f "$env_file"
done