#!/bin/tcsh -f
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

## parse paths and check access
# if ( ! -w "$WK_DIR" ) then
# 	echo "${USER} doesn't have write access to ${WK_DIR}"
#	exit 1
# endif
# if ( ! -w "$out_dir" ) then
# 	echo "${USER} doesn't have write access to ${out_dir}"
# 	exit 1
# endif

# counts in the following depend on in_data_dir being terminated with a '/'
set last_char=`echo "$in_data_dir" | rev | cut -c -1`
if ( "$last_char" != "/" ) then
    set in_data_dir="${in_data_dir}/"
endif
set PP_DIR=`cd ${in_data_dir}/../../../.. ; pwd`
# chunk frequency = 2nd directory from the end
set CHUNK_FREQ=`echo "$in_data_dir" | rev | cut -d/ -f2 | rev`
# data frequency = 3rd directory from the end
set DATA_FREQ=`echo "$in_data_dir" | rev | cut -d/ -f3 | rev`
# component = 5th directory from the end
set COMPONENT=`echo "$in_data_dir" | rev | cut -d/ -f5 | rev`
set cmpt_args=( '--component' "$COMPONENT" '--data_freq' "$DATA_FREQ" '--chunk_freq' "$CHUNK_FREQ" )
set flags=()

## parse command line arguments
# NB analysis doesn't have getopts
# reference: https://github.com/blackberry/GetOpt/blob/master/getopt-parse.tcsh
set temp=(`getopt -s tcsh -o Y:Z: --long save_nc,yr1:,yr2: -- $argu:q`)
if ($? != 0) then 
    echo "Command line parse error 1" >/dev/stderr
    exit 1
endif

eval set argv=\($temp:q\) # argv needed for shift etc. to work
while (1)
    switch($1:q)
    case --save_nc:
        set flags = ( '--save_nc' ) ; shift 
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
( module list -t ) |& cat # log modules being used

## clean up tmpdir
wipetmp

## Clean output subdirectory
set mdtf_dir="MDTF_${descriptor}_${yr1}_${yr2}"
if ( -d "${out_dir}/${mdtf_dir}" ) then
    # may be mounted read-only though...
    echo "${out_dir}/${mdtf_dir} already exists; deleting"
    rm -rf "${out_dir}/${mdtf_dir}"
endif

## run the command (unbuffered output)
echo 'script start'
/usr/bin/env python -u "${REPO_DIR}/src/mdtf_gfdl.py" \
--frepp --ignore-component \
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
$cmpt_args:q \
$flags:q
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
# if ( ! -w "$OUTPUT_HTML_DIR" ) then
#    echo "${USER} doesn't have write access to ${OUTPUT_HTML_DIR}"
#    exit 0
# endif

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
