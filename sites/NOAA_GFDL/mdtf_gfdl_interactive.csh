#!/bin/tcsh -f
#SBATCH --job-name=MDTF-diags
#SBATCH --time=05:00:00
#SBATCH --ntasks=1
#SBATCH --chdir=/home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/MDTF-diagnostics
#SBATCH -o /home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/MDTF-diagnostics/%x.o%j
#SBATCH --constraint=bigmem
# ref: https://wiki.gfdl.noaa.gov/index.php/Moab-to-Slurm_Conversion
# Note: increase timeout for long runs

# ------------------------------------------------------------------------------
# Wrapper script to call the MDTF Diagnostics package interactively from PPAN.
# ------------------------------------------------------------------------------

## set paths
set REPO_DIR=/home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/MDTF-diagnostics
set OBS_DATA_DIR=/home/Oar.Gfdl.Mdteam/DET/analysis/mdtf/obs_data
set INPUT_DIR=${TMPDIR}/inputdata
set WK_DIR=${TMPDIR}/wkdir
set out_dir=${HOME}

## parse command line arguments
# NB analysis doesn't have getopts
# reference: https://github.com/blackberry/GetOpt/blob/master/getopt-parse.tcsh
set temp=(`getopt -s tcsh -o E:O:Y:Z: --long save_nc,test_mode,out_dir:,descriptor:,yr1:,yr2: -- $argv:q`)
if ($? != 0) then 
    echo "Command line parse error 1" >/dev/stderr
    exit 1
endif
set flags=()

eval set argv=\($temp:q\) # argv needed for shift etc. to work
while (1)
    switch($1:q)
    case -E:
    case --experiment:
        set descriptor="$2:q" ; shift ; shift
        breaksw;
    case -O:
    case --out_dir:
        set out_dir="$2:q" ; shift ; shift
        breaksw;
    case --save_nc:
        set flags = ( $flags:q '--save_nc' ) ; shift 
        breaksw;
    case --test_mode:
        set flags = ( $flags:q '--test_mode' ) ; shift 
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

# foreach el ($argv:q) created problems for some tcsh-versions (at least
# 6.02). So we use another shift-loop here:
while ($#argv > 0)
	set PP_DIR="$1:q"
	shift
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
( module list -t ) |& cat # log modules being used

## clean up tmpdir
wipetmp

## fetch obs data from local source
echo 'Fetching observational data'
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

## run the command (unbuffered output)
echo 'script start'
/usr/bin/env python -u "${REPO_DIR}/src/mdtf.py" \
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
$flags:q
echo 'script exit'

echo "Complete -- Exiting"
exit 0
## 
