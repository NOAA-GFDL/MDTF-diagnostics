#!/bin/tcsh -f
#SBATCH --job-name=MDTF-diags
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --chdir=/home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics
#SBATCH -o /home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics/%x.o%j
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
set conv = GFDL
set model = "modelname"

# Please enter the POD lists below. This gets filled in to the MDTF input json automatically if using frepp

#pod_list contains list of all PODS in the framework for reference. Please edit the pod_list as needed for your simulation.
set pod_list = '"Wheeler_Kiladis","EOF_500hPa","convective_transition_diag","MJO_suite","MJO_teleconnection","MJO_prop_amp","precip_diurnal_cycle","SM_ET_coupling"'

set script_path

## set paths to site installation
set CONDA_ROOT="/home/oar.gfdl.mdtf/miniconda3"
set REPO_DIR="/home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics"

#YOUR mdtf-frepp template jsonc should be in ${TEMPLATE_DIR}/sites/NOAA_GFDL/mdtf_frepp_template.jsonc

set TEMPLATE_DIR = $REPO_DIR

set OBS_DATA_DIR="/home/oar.gfdl.mdtf/mdtf/inputdata/obs_data"
# output is always written to $out_dir; set a path below to GCP a copy of output
# for purposes of serving from a website
set WEBSITE_OUTPUT_DIR=""
set INPUT_DIR="${TMPDIR}/inputdata"
set WK_DIR="${TMPDIR}/wkdir"

# End of user-configurable paramters
# ----------------------------------------------------

echo "mdtf_gfdl.csh: script start"
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

# parse command line arguments manually because getopt doesn't let us pass
# through unrecognized arguments.
set frepp_flag=( '--frepp' ) # multi-run/incremental mode, enabled by default
set passed_args=()
while ($#argv > 0)
    switch($1:q)
    # arguments we need to recognize and handle in this script
    case --run_once:
        # disable multi-run/incremental mode -- should set this flag if this
        # script only called once in an XML
        set frepp_flag=()
        breaksw
    case --component_only:
        set passed_args=( $passed_args:q '--component' "$COMPONENT" '--chunk_freq' "$CHUNK_FREQ" )
        shift
        breaksw
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
    # pass through everything else
    default:
	    if ("$1:q" =~ -*) then
			set passed_args=( $passed_args:q $1:q )     # flag
	    else
			set passed_args=( $passed_args:q \"$1:q\" ) # quote arg
		endif
		if ($#argv > 0) then
			shift
		else
			break
		endif
		breaksw
    endsw
end
# trim leading zeros
set yr1 = `echo ${yr1} | sed 's/\([[:space:]0]*\)\([0-9].*\)/\2/g'`
set yr2 = `echo ${yr2} | sed 's/\([[:space:]0]*\)\([0-9].*\)/\2/g'`

## configure env modules
if ( ! $?MODULESHOME ) then
    echo "mdtf_gfdl.csh: \$MODULESHOME is undefined"
    exit 1
else
    if ( "$MODULESHOME" == "" )  then
        echo "mdtf_gfdl.csh: \$MODULESHOME is empty"
        exit 1
    else
        source $MODULESHOME/init/tcsh
        # should probably 'module purge'
        if ( `where module` == "" ) then
            echo "mdtf_gfdl.csh: Still can't load modules"
            exit 1
        endif
    endif
endif

# modules may load other modules of different versions as dependencies,
# so if any version of a version-unspecified module is already loaded skip it
foreach mod ( 'gcp' 'perlbrew' )
    # () needed for csh quoting, also remember `module` only writes to stderr
    ( module list -t ) |& grep -qiF "$mod"
    if ( $status != 0 ) then
        module load $mod
    endif
end
( module list -t ) |& cat # log modules being used

## clean up tmpdir
wipetmp

## run the command
echo "mdtf_gfdl.csh: conda activate"
source /home/oar.gfdl.mdtf/miniconda3/etc/profile.d/conda.csh
conda activate _MDTF_base

echo "mdtf_gfdl.csh: MDTF start"

###### workaround to create input json based on a template json and the frepp template variables ####
set template_jsonc = ${TEMPLATE_DIR}/sites/NOAA_GFDL/mdtf_frepp_template.jsonc

gcp -cd $template_jsonc $WK_DIR/
echo "A copy of the input json can be found in outputdir as well ${out_dir}/" #TODO move under corresponding exp directory


set input_jsonc = ${WK_DIR}/mdtf_frepp_template.jsonc

sed -i 's/CASENAME1/'${descriptor}'/g' $input_jsonc
sed -i 's/MODEL1/'${model}'/g' $input_jsonc
sed -i 's|PPDIR1|'{$PP_DIR}'|' $input_jsonc
sed -i 's/FIRSTYR1/'${yr1}'/g' $input_jsonc
sed -i 's/LASTYR1/'${yr2}'/g' $input_jsonc
sed -i 's|OUTPUTDIR1|'${out_dir}'|' $input_jsonc
sed -i 's/CONVENTION1/'${conv}'/g' $input_jsonc
sed -i 's/POD_LIST/'${pod_list}'/g' $input_jsonc

echo "Filled in input settings json and using this for the MDTF run $input_jsonc"

gcp -cd $input_jsonc ${out_dir}/

if (! -d $in_data_dir) then
  echo "QUIT if in_data_dir is not valid"
endif

if (! -d $PP_DIR) then
  echo "QUIT if PP_DIR is not valid"
endif
echo "Running ${REPO_DIR}/mdtf_framework.py -f ${input_jsonc} --site NOAA_GFDL -v "
${REPO_DIR}/mdtf_framework.py -f ${input_jsonc} --site NOAA_GFDL -v


##workaround ends
pkg_status=$?
echo "mdtf_gfdl.csh: MDTF finish; exit={$pkg_status}"

# ----------------------------------------------------
# copy/link output files to website directory, if requested

if ( ! $?WEBSITE_OUTPUT_DIR ) then
    exit $pkg_status
else if ( "$WEBSITE_OUTPUT_DIR" == "" )
    exit $pkg_status
endif

# test for write access -- don't trust -w test
# OK, but what about gcp read-only?
( touch ${WEBSITE_OUTPUT_DIR}/test && rm -f ${WEBSITE_OUTPUT_DIR}/test ) >& /dev/null
if ($? == 0) then
    echo "mdtf_gfdl.csh: configuring data for experiments website"

    set shaOut = `perl -e "use Digest::SHA qw(sha1_hex); print sha1_hex('${out_dir}');"`
    set WEB_COPY_DIR="${WEBSITE_OUTPUT_DIR}/${shaOut}"
    if ( ! -d ${WEB_COPY_DIR} ) then
        mkdir -p "${WEB_COPY_DIR}"
        echo "mdtf_gfdl.csh: Symlinking ${out_dir}/${mdtf_dir} to ${WEB_COPY_DIR}/mdtf"
        ln -s "${out_dir}/${mdtf_dir}" "${WEB_COPY_DIR}/mdtf"
    else
        echo "mdtf_gfdl.csh: Gcp'ing ${out_dir}/${mdtf_dir}/ to ${WEB_COPY_DIR}/mdtf/"
        gcp -v -r -cd "gfdl:${out_dir}/${mdtf_dir}/" "gfdl:${WEB_COPY_DIR}/mdtf/"
    endif
    echo "mdtf_gfdl.csh: copied data for experiments website"
    exit $pkg_status
else
   echo "mdtf_gfdl.csh: ${USER} doesn't have write access to ${WEBSITE_OUTPUT_DIR}"
   exit 1
endif
