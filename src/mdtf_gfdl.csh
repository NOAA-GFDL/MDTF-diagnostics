#!/bin/csh -f

source /home/gfdl/init/csh.cshrc

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
if (! $?MODULESHOME) then       
	echo "\$MODULESHOME is undefined"
	exit 1
else
	if ("$MODULESHOME" == "")  then
		echo "\$MODULESHOME is empty"
		exit 1
	else 
		source $MODULESHOME/init/csh
		# should probably 'module purge'
		if ( `where module` == "" ) then
			echo "Still can't load modules"
			exit 1
		endif
  	endif
endif

set mods="python/2.7.12"
module load $mods	

set REPO_DIR=/home/tsj/mdtf/MDTF-diagnostics

./src/validate_environment.sh -v -a subprocess32 -a pyyaml
if ( $status != 0 ) then
	echo 'Installing required modules'
	mkdir -p "${REPO_DIR}/envs/venv"
	python -m pip install --user virtualenv
	python -m virtualenv "${REPO_DIR}/envs/venv/base"
	source "${REPO_DIR}/envs/venv/base/bin/activate"
	pip install --user subprocess32 pyyaml
else
	echo 'Found required modules'
endif

echo 'script start'
python "${REPO_DIR}/src/mdtf.py" "${REPO_DIR}/src/frepp_config.yml"
# python "${REPO_DIR}/src/mdtf.py" "${REPO_DIR}/src/frepp_config.yml" >&! "${REPO_DIR}/frepp_run.log"
echo 'script exit'
