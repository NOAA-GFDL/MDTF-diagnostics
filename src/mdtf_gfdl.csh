#!/usr/bin/env tcsh -f
#SBATCH --job-name=MDTF-diags
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --chdir=/home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/MDTF-diagnostics
#SBATCH -o /home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/MDTF-diagnostics/%x.o%j
#SBATCH --constraint=bigmem
# ref: https://wiki.gfdl.noaa.gov/index.php/Moab-to-Slurm_Conversion

# ------------------------------------------------------------------------------
# Wrapper script to call the MDTF Diagnostics package from the FRE pipeline.
# ------------------------------------------------------------------------------

# variables set by frepp
set argu
set mode
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
set script_path

## set paths
set REPO_DIR=/home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/MDTF-diagnostics
set OBS_DATA_DIR=/home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/obs_data
# output always written to $out_dir; unset below to skip copy/linking to 
# MDteam experiment directory.
set OUTPUT_HTML_DIR=/home/Oar.Gfdl.Mdteam/internal_html/mdtf_output
set INPUT_DIR=${TMPDIR}/inputdata
set WK_DIR=${TMPDIR}/wkdir

# End of user-configurable paramters
# ----------------------------------------------------

## parse command line arguments

set PP_DIR=`cd ${in_data_dir}/../../../.. ; pwd`
# component = 5th directory from the end
set COMPONENT=`echo "$in_data_dir" | rev | cut -d/ -f5 | rev`
# chunk frequency = 2nd directory from the end
set CHUNK_FREQ=`echo "$in_data_dir" | rev | cut -d/ -f2 | rev`
set cmpt_args = ( '--component' "$COMPONENT" '--chunk_freq' "$CHUNK_FREQ" )

# NB analysis doesn't have getopts
# reference: https://github.com/blackberry/GetOpt/blob/master/getopt-parse.tcsh
set temp=(`getopt -s tcsh -o IY:Z: --long ignore-component,yr1:,yr2: -- $argv:q`)
if ($? != 0) then 
	echo "Command line parse error 1" >/dev/stderr
	exit 1
endif

eval set argv=\($temp:q\)
while (1)
	switch($1:q)
	case -I:
	case --ignore-component:
		set cmpt_args = ( '--ignore-component' ) ; shift 
		breaksw;
	case -Y:
	case --yr1:
		set yr1="$2:q" ; shift ; shift
		breaksw
	case -Z:
	case --yr2:
		set yr2="$2:q" ; shift ; shift
		breaksw
	case --:
		shift
		break
	default:
		echo "Command line parse error 2" ; exit 1
	endsw
end
# trim leading zeros
set yr1 = `echo ${yr1} | sed 's/^0*//g'`
set yr2 = `echo ${yr2} | sed 's/^0*//g'`


## configure env modules
if ( ! $?MODULESHOME ) then       
	echo "\$MODULESHOME is undefined"
	exit 1
else
	if ( "$MODULESHOME" == "" )  then
		echo "\$MODULESHOME is empty"
		exit 1
	else 
		source $MODULESHOME/init/tcsh
		# should probably 'module purge'
		if ( `where module` == "" ) then
			echo "Still can't load modules"
			exit 1
		endif
  	endif
endif

# modules may load other modules of different versions as dependencies,
# so if any version of a version-unspecified module is already loaded skip it
foreach mod ( 'gcp' 'python/2.7.12' 'perlbrew' )
	# () needed for csh quoting, also remember `module` only writes to stderr
	( module list -t ) |& grep -qiF "$mod"
	if ( $status != 0 ) then
		module load $mod
	endif
end	

## clean up tmpdir
wipetmp

## fetch obs data from local source
mkdir -p "${INPUT_DIR}"
mkdir -p "${WK_DIR}"
mkdir "${INPUT_DIR}/model"
gcp -v -r "gfdl:${OBS_DATA_DIR}/" "gfdl:${INPUT_DIR}/obs_data/"

## make sure we have python dependencies
${REPO_DIR}/src/validate_environment.sh -v -a subprocess32 -a pyyaml
if ( $status != 0 ) then
	echo 'Installing required modules'
	mkdir -p "${REPO_DIR}/envs/venv"
	python -m pip install --user virtualenv
	python -m virtualenv "${REPO_DIR}/envs/venv/base"
	source "${REPO_DIR}/envs/venv/base/bin/activate"
	# pip --user redundant/not valid in a virtualenv
	pip install --disable-pip-version-check subprocess32 pyyaml
else
	echo 'Found required modules'
endif

## Clean output subdirectory
set mdtf_dir="MDTF_${descriptor}_${yr1}_${yr2}"
if ( -d "${out_dir}/${mdtf_dir}" ) then
	echo "${out_dir}/${mdtf_dir} already exists; deleting"
	rm -rf "${out_dir}/${mdtf_dir}"
endif

## run the command
echo 'script start'
"${REPO_DIR}/src/mdtf.py" --frepp \
--MODEL_DATA_ROOT "${INPUT_DIR}/model" \
--OBS_DATA_ROOT "${INPUT_DIR}/obs_data" \
--WORKING_DIR "$WK_DIR" \
--OUTPUT_DIR "$out_dir" \
--data_manager "GfdlPP" \
--environment_manager "GfdlVirtualenv" \
--CASENAME "$descriptor" \
--CASE_ROOT_DIR "$PP_DIR" \
--FIRSTYR $yr1 \
--LASTYR $yr2 \
$cmpt_args:q
echo 'script exit'

## copy/link output files, if requested
if ( ! $?OUTPUT_HTML_DIR ) then       
	echo "Complete -- Exiting"
	exit 0
endif
if ( "$OUTPUT_HTML_DIR" == "" ) then
	echo "Complete -- Exiting"
	exit 0
endif
if ( -w "$OUTPUT_HTML_DIR" ) then
	echo "${USER} doesn't have write access to ${OUTPUT_HTML_DIR}"
	exit 0
endif

echo "Configuring data for experiments website"

set shaOut = `perl -e "use Digest::SHA qw(sha1_hex); print sha1_hex('${out_dir}');"`
set mdteamDir = "${OUTPUT_HTML_DIR}/${shaOut}"	

if ( ! -d ${mdteamDir} ) then
	mkdir -p "${mdteamDir}"
	echo "Symlinking ${out_dir}/${mdtf_dir} to ${mdteamDir}/mdtf"
	ln -s "${out_dir}/${mdtf_dir}" "${mdteamDir}/mdtf"
else
	echo "Gcp'ing ${out_dir}/${mdtf_dir}/ to ${mdteamDir}/mdtf/"
	gcp -v -r "gfdl:${out_dir}/${mdtf_dir}/" "gfdl:${mdteamDir}/mdtf/"
endif

echo "Complete -- Exiting"
exit 0
## 
