#!/bin/csh -f
#SBATCH --job-name=MDTF-diags
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --chdir=/home/tsj/mdtf/MDTF-diagnostics
#SBATCH -o /home/tsj/mdtf/MDTF-diagnostics/%x.o%j
#SBATCH --constraint=bigmem

# ref: https://wiki.gfdl.noaa.gov/index.php/Moab-to-Slurm_Conversion

# variables set by frepp
set in_data_dir
set out_dir
set descriptor
set yr1
set yr2
set WORKDIR
set databegyr
set dataendyr
set datachunk
set staticfile
set fremodule

## set paths
set REPO_DIR=/home/tsj/mdtf/MDTF-diagnostics
set INPUT_DIR=${TMPDIR}/inputdata
set WK_DIR=${TMPDIR}/wkdir
set PP_DIR=`cd ${in_data_dir}/../../../.. ; pwd`

## configure env modules
if ( ! $?MODULESHOME ) then       
	echo "\$MODULESHOME is undefined"
	exit 1
else
	if ( "$MODULESHOME" == "" )  then
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

set mods="python/2.7.12 gcp/2.3"
module load $mods	

## fetch obs data from local source
mkdir -p "${INPUT_DIR}"
mkdir -p "${WK_DIR}"
mkdir "${INPUT_DIR}/model"
gcp -v -r gfdl:/home/tsj/mdtf/obs_data/ gfdl:${INPUT_DIR}/obs_data/

## make sure we have python dependencies
${REPO_DIR}/src/validate_environment.sh -v -a subprocess32 -a pyyaml
if ( $status != 0 ) then
	echo 'Installing required modules'
	mkdir -p "${REPO_DIR}/envs/venv"
	python -m pip install --user virtualenv
	python -m virtualenv "${REPO_DIR}/envs/venv/base"
	source "${REPO_DIR}/envs/venv/base/bin/activate"
	pip install --disable-pip-version-check --user subprocess32 pyyaml
else
	echo 'Found required modules'
endif

## run the command!
echo 'script start'
"${REPO_DIR}/src/mdtf.py" --frepp \
--environment_manager "GfdlVirtualenv" \
--MODEL_DATA_ROOT "${INPUT_DIR}/model" \
--OBS_DATA_ROOT "${INPUT_DIR}/obs_data" \
--WORKING_DIR "$WK_DIR" \
--OUTPUT_DIR "$out_dir" \
--data_manager "GfdlPP" \
--CASENAME "$descriptor" \
--CASE_ROOT_DIR "$PP_DIR" \
--FIRSTYR $yr1 \
--LASTYR $yr2
echo 'script exit'
