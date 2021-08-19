#!/usr/bin/tcsh -f
# Note look at save file for some settings
# /project/amp/bundy/mdtf/MDTF_v3.0beta.OBS_WK.20210225/MDTF_30L_cam5301_FAMIP_1990_1994/config_save.json
# and the blocking/settings.jsonc file for others
#set echo verbose
set test = 0   # 1 - calls test.ncl, where test flags need to be set
               # 0 - calls blocking.ncl

#case info
setenv CASENAME 30L_cam5301_FAMIP
#unsetenv CASENAME   # to skip an mdtf case, eg digest data
setenv  FIRSTYR 1990
setenv  LASTYR  1994

setenv  zg500_var zg500

#i/o   - code writes figures to $WK_DIR/obs/PS, $WK_DIR/model/PS
setenv  WK_DIR /project/amp/bundy/mdtf/MDTF_v3.0beta.OBS_WK.20210225/MDTF_30L_cam5301_FAMIP_1990_1994/blocking_neale/
setenv  MODEL_DATA_PATH $WK_DIR/day/${CASENAME}.$zg500_var.day.nc  # Where the framework writes the input model data
setenv  OBS_DATA    /project/amp/bundy/mdtf/inputdata/obs_data/blocking




#settings
setenv  MDTF_BLOCKING_READ_DIGESTED  True
setenv  MDTF_BLOCKING_WRITE_DIGESTED False
setenv  MDTF_BLOCKING_WRITE_DIGESTED_DIR /project/amp/bundy/mdtf/inputdata/obs_data/blocking_neale/digested
setenv  path_variable MODEL_DATA_PATH

#setenv  standard_name geopotential_height_500mb 
setenv POD_HOME /home/bundy/mdtf/MDTF-diagnostics-blocking/diagnostics/blocking_neale
setenv MDTF_BLOCKING_OBS  True  # No figures produced without obs, but it works for writing digested data
setenv MDTF_BLOCKING_CAM3 False
setenv MDTF_BLOCKING_CAM4 False
setenv MDTF_BLOCKING_CAM5 True
setenv MDTF_DEBUG         False #True reduces size of ensemble number

if ( $test ) then
    ncl $POD_HOME/test.ncl
else
    ncl $POD_HOME/blocking.ncl

#    echo "exiting early"
#    exit 
    set out_stat = $status
    echo " ----------------------------------------------"
    echo "Finished blocking.ncl with status $out_stat." # Output should be in $WK_DIR/*/PS"
    
    if ( $out_stat == 0 ) then
    set webdir = mdtf_figures/blocking/test
    set webaddress = "https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/$webdir"
    set webdir = ~/$webdir
    if ( ! -d $webdir ) mkdir -p $webdir

    foreach dir ( model obs )
	echo "--- $dir "
	set ps_dir = $WK_DIR/$dir/PS
	set list = `ls $ps_dir/*.ps`
	echo $list
    #    echo "converting $list"
	foreach file ( $list )  #just the file name, doesn't have path
	    convert $file $webdir/$file:t:r.png
	    if ( $status == 0 ) then
		echo $webaddress/$file:t:r.png
	    else
		echo "failed to convert/copy $ps_dir/$file to $webdir/$file:r.png"
	    endif
	end 
    end 
    endif # $out_stat == 0
endif #test






