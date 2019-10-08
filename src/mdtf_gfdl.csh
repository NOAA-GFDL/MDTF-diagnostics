#!/bin/csh -f
#SBATCH --job-name=MDTF-diags
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --chdir=/home/tsj/mdtf/MDTF-diagnostics
#SBATCH -o /home/tsj/mdtf/MDTF-diagnostics/%x.o%j
#SBATCH --constraint=bigmem

## -v PYTHONHOME="/home/Oar.Gfdl.Mdteam/anaconda2/envs/ILAMB-2.2"
# ref: https://wiki.gfdl.noaa.gov/index.php/Moab-to-Slurm_Conversion

#source /home/gfdl/init/csh.cshrc

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

set mods="python/2.7.12 gcp/2.3"
module load $mods	

echo $TMPDIR

mkdir -p ${TMPDIR}/inputdata
mkdir -p ${TMPDIR}/inputdata/model
gcp -v -r gfdl:/home/tsj/mdtf/obs_data/ gfdl:${TMPDIR}/inputdata/obs_data/

set REPO_DIR=/home/tsj/mdtf/MDTF-diagnostics

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

echo 'script start'
python "${REPO_DIR}/src/mdtf.py" "${REPO_DIR}/src/frepp_config.yml"
# python "${REPO_DIR}/src/mdtf.py" "${REPO_DIR}/src/frepp_config.yml" >&! "${REPO_DIR}/frepp_run.log"
echo 'script exit'
