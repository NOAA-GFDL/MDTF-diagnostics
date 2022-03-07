; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

; FILE: daily_anom.ncl
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/calc_utils.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

routine_name = "daily_anom"
casename = getenv("CASENAME")
time_coord = getenv("time_coord")
lat_coord = getenv("lat_coord")
lon_coord = getenv("lon_coord")

file_dir = getenv("WK_DIR")+"/model/netCDF/"
datadir = getenv("DATADIR")
yr1 = stringtointeger(getenv("FIRSTYR"))
yr2 = stringtointeger(getenv("LASTYR"))
start_date = yr1*10000+201
end_date = (yr2+1)*10000+101

delete_existing = False  ;True = overwrite, False = don't overwrite
if ( delete_existing ) then
  print("WARNING: daily_anom.ncl deleting existing anom files")
  system("ls "+file_dir+"/*anom*.nc")
end if

var_names = (/ "pr","rlut","u200","u850","v200","v850" /)

do i=0,dimsizes(var_names)-1

  var_name = var_names(i)
  print(routine_name+" starting variable "+var_name)

  file_in   = file_dir +"/"+casename+"."+var_name+".day.nc"
  file_out  = file_dir +"/"+casename+"."+var_name+".day.anom.nc"

  if( isfilepresent(file_out) .and. (.not.delete_existing)) then
    print(file_out+" already exists. To force recalculation, set daily_anom.ncl delete_existing = True")

  else

    if( isfilepresent(file_out) .and. (delete_existing)) then
      print(file_out+" already exists. Overwriting since delete_existing = "+delete_existing)
      system("rm "+file_out)
    end if
 
    if( isfilepresent(file_in) ) then
    	print("reading "+file_in)
	f = addfile(file_in,"r")
	time = f->$time_coord$
	date = cd_calendar(time,-2)

	gw = f->gw
	invar = f->$var_name$($time_coord$|:,$lat_coord$|:,$lon_coord$|:)

	var = compute_daily_anom(invar)
	var!0 = "time"
	var!1 = "lat"
	var!2 = "lon"
	var&time = time
	var&lat = f->$lat_coord$
	var&lon = f->$lon_coord$

        ; this was already done in daily_netcdf
        if (var_name.eq."pr") then
          var = (/var*1000.0*86400.0/) ; mm/day
          var@units = "mm/day"
        end if

	print("writing "+file_out)
	fo = addfile(file_out,"c")

	fo->gw = gw
	fo->date = date
	fo->$var_name$ = var

	delete(f)
	delete(fo)
	delete(invar)
	delete(var)
 
      else
        print("ERROR: missing file that should have been made by daily_netcdf.ncl "+file_in)
      end if ; if( isfilepresent(file_in)
    end if ; isfilepresent(wkdir+ ... anom ...
    
  end do

end
