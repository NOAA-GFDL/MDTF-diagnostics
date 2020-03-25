; This file is part of the MJO_suite module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

; FILE: daily_netcdf.ncl
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/utils.ncl"

begin
; read daily output files from CAM2 and process the data
; each daily file has 30 days of data
; eg. U200(time,lat,lon)

print("Starting...")
casename = getenv("CASENAME")
datadir = getenv("DATADIR")
level = getenv("lev_coord")
file_dir = getenv("WK_DIR")+"/model/netCDF/"
pr_conversion_factor = stringtofloat(getenv("pr_conversion_factor"))

file_u200 = datadir+"/day/"+casename+"."+getenv("u200_var")+".day.nc"
file_v200 = datadir+"/day/"+casename+"."+getenv("v200_var")+".day.nc"
file_u850 = datadir+"/day/"+casename+"."+getenv("u850_var")+".day.nc"
file_rlut = datadir+"/day/"+casename+"."+getenv("rlut_var")+".day.nc"
file_pr = datadir+"/day/"+casename+"."+getenv("pr_var")+".day.nc"

print("daily_netcdf.ncl reading "+file_pr+" for coordinates")
f = addfile(file_pr,"r")
lat_coord = getenv("lat_coord")
lat = f->$lat_coord$
nlat = dimsizes(lat)
lon_coord = getenv("lon_coord")
lon = f->$lon_coord$
nlon = dimsizes(lon)
if(isfilevar(f,"gw")) then
   gw = f->gw
else
   slat = new((/nlat+1/),"double")
   gw = new((/nlat/),"double")
   gw!0 = "lat"
   gw&lat = lat
   if( lat(0).lt.lat(1) ) then
       slat(0) = -90.d0        
       slat(nlat) = 90.d0
   else
       slat(0) = 90.d0  
       slat(nlat) = -90.d0
   end if

   do i=1,nlat-1
       slat(i) = (lat(i-1)+lat(i))/2.d0
   end do

   pi = 4.d0*atan(1.d0)
   do i=0,nlat-1
      gw(i) = abs(sin(slat(i+1)/180.d0*pi)-sin(slat(i)/180.d0*pi))
   end do
   delete(slat)
end if

gwEq = gw({-40:40})


yr1 = stringtointeger(getenv("FIRSTYR"))
yr2 = stringtointeger(getenv("LASTYR"))

time_coord = getenv("time_coord")
time_all = f->$time_coord$
date_all = ut_calendar(time_all,-2)
date_all!0 = "time"
date_all&time = time_all
date_all@units = "YYYYMMDD"
year_all = date_all/10000

start_date = yr1*10000+101
start_date = yr1*10000+101
if( time_all@calendar.eq."360_day") then
    end_date = yr2*10000+1230
else
    end_date = yr2*10000+1231
end if

i1 = 0
i2 = 0


do i=0,dimsizes(date_all)-1
   if( date_all(i).eq.start_date ) then
       i1 = i
   end if
   if( date_all(i).eq.end_date ) then
       i2 = i
   end if
end do

date = date_all(i1:i2)
print(date(0:9))
ndays = dimsizes(date)
time = ispan(0,ndays-1,1)

;
; Make sure date array looks right
;	This used to check that there were n*30 dates
;	because it required 30 timesamples per file
;	that is no longer a requirement, so now it just
;	checks for monotonicity.

if (  isMonotonic(date) .ne. 1 ) then 
   print("ERROR: daily_netcdf.ncl finds dates not monotonic increasing")
   ; find the bad value(s) for stdout
   do n = 1, ndays-1      
      nd = n-1
      if ( date(n) .lt. date(nd) ) then
      	 print("record "+nd +" date "+date(nd))
	 print("record "+n  +" date "+date(n))
      end if
   end do
   exit  ; exit on error
end if

time_coord = getenv("time_coord")
lat_coord = getenv("lat_coord")
lon_coord = getenv("lon_coord")



; precipitation rate (pr)
print("daily_netcdf.ncl reading "+file_pr+" for making precip file!")
if( isfilepresent(file_pr) ) then

    f_pr = addfile(file_pr,"r")
    pr_var = getenv("pr_var")

pr = f_pr->$pr_var$($time_coord$|i1:i2,{$lat_coord$|-40:40},$lon_coord$|:)
pr = (/pr*pr_conversion_factor*0.001/)            ; m/s
pr@units = "m/s"
;prEq = pr($time_coord$ | :,{$lat_coord$ | -40 : 40 }, {$lon_coord$ | : })

print("writing "+file_dir+casename+".pr.day.nc")
fo = addfile(file_dir+casename+".pr.day.nc","c")
fo->gw = gwEq
fo->date = date
fo->pr = pr

else

print("daily pr file does not exist for MJO diagnostics")

end if

;---------------------- moved up for speedier debugging -------------------

; To Do: 
; - incorporate the varname/file name setting into a function instead of repeating
; looks like procedures can modify arguments (intent inout) so just do that
; - make function work w/o optional arguments
; - make this a loop over the variable names
; - maybe make read and write separate functions with the coordinate subsetting done here

delete_existing = False  ;overwrite

plevs = (/850,200/)       ;this package expects new files to be written with these names
var_names = (/"u","v"/)
source = (/datadir+"/day/"+casename+"."+getenv("u200_var")+".day.nc",datadir+"/day/"+casename+"."+getenv("v200_var")+".day.nc"/)

do i=0,dimsizes(plevs)-1
   plev = plevs(i)
   do j=0,dimsizes(var_names)-1
;      var_name_3d_model = getenv((var_names(j)+"_var")                           ; as read from history files (3D field)
      var_name_3d_model = getenv(var_names(j)+"_var")                           ; as read from history files (3D field
      print(" var_name_3d_model "+var_name_3d_model)

      print(" looking for "+var_names(j)+tostring(plev)+"_var")
      var_name_plev_model = getenv((var_names(j))+tostring(plev)+"_var")  ; as read from history files (pressure slice)
      print(" var_name_plev_model "+var_name_plev_model)

      var_name_plev_package = var_names(j)+tostring(plev)      ; new file name & varname in file
      print(" var_name_plev_package "+var_name_plev_package)
    ;   LEV = tostring(plevs(i)*100)+"." 
    ;   src = source(j)
    ;   temp_file = datadir+"/day/"+var_name_plev_package+".temp.nc"
    ;   dst = datadir+"/day/"+casename+"."+var_name_plev_package+".day.nc"
    ;   ; extract level
    ;   nco_call = "ncks --no_tmp_fl -O -d "+level+","+LEV+","+LEV+"  "+src+" "+temp_file
    ;   print(nco_call)
    ;   system(nco_call)
    ;   ; flatten to 3D
    ;   nco_call = "ncwa --no_tmp_fl -O -a "+level+" -d "+level+",0,0 "+temp_file+" "+dst
    ;   print(nco_call)
    ;   system(nco_call)

      dst = datadir+"/day/"+casename+"."+var_name_plev_model+".day.nc"
      file_out = file_dir+casename+"."+var_name_plev_package+".day.nc"
      file_in_3d =  datadir+"/day/"+casename+"."+var_name_3d_model+".day.nc"
      file_in_ps =  datadir+"/day/"+casename+".PS.day.nc"  ;drbdbg needs a getenv

      read_model_file (var_name_plev_model, dst,\
      		      var_name_plev_package,file_out,\
		      delete_existing, \
      		      i1,i2,time_coord,lat_coord,lon_coord,gwEq,date,\  ; better moved to another function for slicing
		      var_name_3d_model,plev,file_in_3d,file_in_ps)  ; optional args for pressure interp
    end do
end do


; outgoing longwave radiation (rlut)

print("daily_netcdf.ncl reading "+file_rlut)
if( isfilepresent(file_rlut) ) then

f_rlut = addfile(file_rlut,"r")
rlut_var = getenv("rlut_var")

rlut = f_rlut->$rlut_var$($time_coord$|i1:i2,{$lat_coord$|-40:40},$lon_coord$|:)

print("writing "+file_dir+casename+".rlut.day.nc")
fo = addfile(file_dir+casename+".rlut.day.nc","c")
fo->gw = gwEq
fo->date = date
fo->rlut = rlut

else

print("daily rlut file does not exist for MJO diagnostics")

end if




end
