; This file is part of the MJO_suite module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

; FILE: daily_anom.ncl
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/calc_utils.ncl"

begin

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


file_pr = casename+".pr.day.nc"
file_rlut = casename+".rlut.day.nc"
file_u200 = casename+".u200.day.nc"
file_u850 = casename+".u850.day.nc"
file_v200 = casename+".v200.day.nc"
file_v850 = casename+".v850.day.nc"

;file_LANDFRAC = casename+"."+getenv("landfrac_var")+".nc"
;landfrac_var = getenv("landfrac_var")


; pr

if( isfilepresent(file_dir+casename+".pr.daily.anom.nc") ) then
    print(file_dir+casename+".pr.daily.anom.nc already exists!!")

else
    print("trying to create "+file_dir+casename+".pr.daily.anom.nc")
    if( isfilepresent(file_dir+file_pr) ) then
    	print("reading "+file_dir+file_pr)
	f = addfile(file_dir+file_pr,"r")
	time = f->$time_coord$
	date = cd_calendar(time,-2)

	print(getfilevarnames(f))

	gw = f->gw
	invar = f->pr($time_coord$|:,$lat_coord$|:,$lon_coord$|:)

	var = compute_daily_anom(invar)
	var!0 = "time"
	var!1 = "lat"
	var!2 = "lon"
	var&time = time
	var&lat = f->$lat_coord$
	var&lon = f->$lon_coord$

	var = (/var*1000.0*86400.0/) ; mm/day
	var@units = "mm/day"

	print("writing "+file_dir+casename+".pr.day.anom.nc")
	fo = addfile(file_dir+casename+".pr.day.anom.nc","c")

	fo->gw = gw
	fo->date = date
	fo->pr = var

	delete(f)
	delete(fo)
	delete(invar)
	delete(var)
 
    else
	print("ERROR: missing daily_netcdf.ncl created file "+file_dir+file_pr)
    end if ; if( isfilepresent(file_dir+file_pr) ) then
end if ; isfilepresent(wkdir+ ... anom ...


; U200
if( isfilepresent(file_dir+casename+".u200.day.anom.nc") ) then

print(file_dir+casename+".u200.day.anom.nc already exists")

else

if( isfilepresent(file_dir+file_u200) ) then

f = addfile(file_dir+file_u200,"r")
time = f->$time_coord$
date = cd_calendar(time,-2)


invar = f->u200($time_coord$|:,$lat_coord$|:,$lon_coord$|:)
    
var = compute_daily_anom(invar)
var!0 = "time"
var!1 = "lat"
var!2 = "lon"
var&time = time
var&lat = f->$lat_coord$
var&lon = f->$lon_coord$

print("writing "+file_dir+casename+".u200.day.anom.nc")
fo = addfile(file_dir+casename+".u200.day.anom.nc","c")

fo->gw = gw
fo->date = date
fo->u200 = var

delete(f)
delete(fo)
delete(invar)
delete(var)

end if
end if

; u850
if( isfilepresent(file_dir+casename+".u850.daily.anom.nc") ) then

print(file_dir+casename+".u850.daily.anom.nc exists!")

else

print(get_script_name()+"Creating "+file_dir+casename+".u850.daily.anom.nc")
if( isfilepresent(file_dir+file_u850) ) then

print("reading "+file_u850)
f = addfile(file_dir+file_u850,"r")
time = f->$time_coord$
date = cd_calendar(time,-2)


invar = f->u850($time_coord$|:,$lat_coord$|:,$lon_coord$|:)
    
var = compute_daily_anom(invar)
var!0 = "time"
var!1 = "lat"
var!2 = "lon"
var&time = time
var&lat = f->$lat_coord$
var&lon = f->$lon_coord$

print("writing "+file_dir+casename+".u850.day.anom.nc")
fo = addfile(file_dir+casename+".u850.day.anom.nc","c")

fo->gw = gw
fo->date = date
fo->u850 = var

delete(f)
delete(fo)
delete(invar)
delete(var)

end if
end if

; v200
if( isfilepresent(file_dir+casename+".v200.day.anom.nc") ) then

print(file_dir+casename+".v200.day.anom.nc already exists")

else

if( isfilepresent(file_dir+file_v200) ) then
    print(get_script_name()+"Creating "+file_dir+casename+".v200.daily.anom.nc")
    print("reading "+file_v200)
    f = addfile(file_dir+file_v200,"r")
    time = f->$time_coord$
    date = cd_calendar(time,-2)

    invar = f->v200($time_coord$|:,$lat_coord$|:,$lon_coord$|:)
    
    var = compute_daily_anom(invar)
    var!0 = "time"
    var!1 = "lat"
    var!2 = "lon"
    var&time = time
    var&lat = f->$lat_coord$
    var&lon = f->$lon_coord$

    print("writing "+file_dir+casename+".v200.day.anom.nc")
    fo = addfile(file_dir+casename+".v200.day.anom.nc","c")

    fo->gw = gw
    fo->date = date
    fo->v200 = var

    delete(f)
    delete(fo)
    delete(invar)
    delete(var)

else
    print("UH oh: file doens't exist: "+file_dir+file_v200)

end if
end if

; v850
if( isfilepresent(file_dir+casename+".v850.day.anom.nc") ) then

print(file_dir+casename+".v850.day.anom.nc already exists!!")

else

if( isfilepresent(file_dir+file_v850) ) then
print(get_script_name()+"Creating "+file_dir+casename+".v850.daily.anom.nc")
print("reading "+file_v850)
f = addfile(file_dir+file_v850,"r")
time = f->$time_coord$
date = cd_calendar(time,-2)

invar = f->v850($time_coord$|:,$lat_coord$|:,$lon_coord$|:)
    
var = compute_daily_anom(invar)
var!0 = "time"
var!1 = "lat"
var!2 = "lon"
var&time = time
var&lat = f->$lat_coord$
var&lon = f->$lon_coord$

print("writing "+file_dir+casename+".v850.day.anom.nc")
fo = addfile(file_dir+casename+".v850.day.anom.nc","c")

fo->gw = gw
fo->date = date
fo->v850 = var

delete(f)
delete(fo)
delete(invar)
delete(var)



end if
end if

; rlut
if( isfilepresent(file_dir+casename+".rlut.day.anom.nc") ) then

print(file_dir+casename+".rlut.day.anom.nc exists!!")

else

if( isfilepresent(file_dir+file_rlut) ) then

print("reading "+file_rlut)
f = addfile(file_dir+file_rlut,"r")
time = f->$time_coord$
date = cd_calendar(time,-2)

invar = f->rlut($time_coord$|:,$lat_coord$|:,$lon_coord$|:)
    
var = compute_daily_anom(invar)
var!0 = "time"
var!1 = "lat"
var!2 = "lon"
var&time = time
var&lat = f->$lat_coord$
var&lon = f->$lon_coord$

print("writing "+file_dir+casename+".rlut.day.anom.nc")
fo = addfile(file_dir+casename+".rlut.day.anom.nc","c")

fo->gw = gw
fo->date = date
fo->rlut = var

delete(f)
delete(fo)
delete(invar)
delete(var)



end if
end if



end
