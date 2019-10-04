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
set mods="python/2.7.12"
if ( `where module` != "" ) then
	module load $mods
else
	echo 'Module command not found'
	/usr/local/Modules/$MODULE_VERSION/bin/modulecmd tcsh load $mods
endif	

set REPO_DIR=/home/tsj/mdtf/MDTF-diagnostics

./src/validate_environment.sh -a subprocess32 -a pyyaml
if ( $status != 0 ) then
	echo 'Installing required modules'
	mkdir -p "${REPO_DIR}/envs/venv"
	python -m pip install --user virtualenv
	python -m virtualenv "${REPO_DIR}/envs/venv/base"
	source "${REPO_DIR}/envs/venv/base/bin/activate"
	pip install subprocess32 pyyaml
else
	echo 'Found required modules'
endif

echo 'script start'
python "${REPO_DIR}/src/mdtf.py" "${REPO_DIR}/src/config_frepp.yml" >&! "${REPO_DIR}/frepp_run.log"
echo 'script exit'
