#!/bin/csh -f
#--------------------------------------
#PBS -N mdtf_frepp_driver
#PBS -l size=1
#PBS -l walltime=60:00:00
#PBS -r y
#PBS -j oe
#PBS -o
#PBS -q batch
#--------------------------------------

# clean up tmpdir
wipetmp

# fields set by frepp
set argu
set descriptor
set in_data_dir
set out_dir
set WORKDIR
set mode
set yr1
set yr2
set databegyr
set dataendyr
set datachunk
set staticfile
set script_path
set fremodule 
set mode = "GFDL"

if (-d ${out_dir}/mdtf) then
  echo "Output directory already exists, removing"
  rm -fr ${out_dir}/mdtf
endif

set ppdir = `echo ${in_data_dir} | sed 's|\(.*pp\).*|\1|'`

/home/oar.gfdl.mdtf/run-MDTF/run-MDTF.sh -i ${ppdir} -o ${out_dir}/mdtf -s $yr1 -e $yr2

