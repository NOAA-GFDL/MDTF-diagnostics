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
set script_path

## set paths to site installation
set REPO_DIR="/home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics"
set OBS_DATA_DIR="/home/oar.gfdl.mdtf/mdtf/inputdata/obs_data"
# output is always written to $out_dir; set a path below to GCP a copy of output
# for purposes of serving from a website
set WEBSITE_OUTPUT_DIR=""
set INPUT_DIR="${TMPDIR}/inputdata"
set WK_DIR="${TMPDIR}/wkdir"
set MDTF_ENV_JSONC="/net/${USER}"/mdtf/MDTF-diagnostics/sites/NOAA_GFDL/gfdl_ppan.jsonc

## clean up tmpdir
wipetmp

## activate the base conda environment
echo "mdtf_ppan.csh: conda activate"
source "${REPO_DIR}/src/conda/conda_init.sh" -q "/home/oar.gfdl.mdtf/miniconda3"
conda activate "/home/oar.gfdl.mdtf/miniconda3/envs/_MDTF_base"
## run the command
./home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics/mdtf -f ${MDTF_ENV_JSONC} -v
