#!/bin/csh -f

# variables set by frepp
set in_data_dir
set out_dir
set descriptor
set yr1
set yr2
set databegyr
set dataendyr
set datachunk
set staticfile
set fremodule
set freanalysismodule

# actually run

module load python/2.7.12
set REPO_DIR=/home/tsj/mdtf/MDTF-diagnostics

mkdir -p "${REPO_DIR}/envs/venv"
python -m pip install --user virtualenv
python -m virtualenv "${REPO_DIR}/envs/venv/base"
source "${REPO_DIR}/envs/venv/base/bin/activate"
pip install subprocess32 pyyaml

python "${REPO_DIR}/src/mdtf.py" config_frepp.yml >&! "${REPO_DIR}/frepp_run.log"
