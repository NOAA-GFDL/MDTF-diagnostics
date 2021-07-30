; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

; FILE: daily_netcdf.ncl
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/utils.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

undef("debug_print")
procedure debug_print(string_to_print,routine_name,debug_flag)
begin

  if ( debug_flag ) then
    print(routine_name+": "+string_to_print)
  end if
end ; procedure debug_print


begin
; read daily output files from CAM2 and process the data
; each daily file has 30 days of data
; eg. U200(time,lat,lon)

debug = False
routine_name = "daily_netcdf"
debug_print("Starting...",routine_name,debug)
casename = getenv("CASENAME")
datadir = getenv("DATADIR")
level = getenv("lev_coord")
wk_dir = getenv("WK_DIR")+"/model/netCDF/"


file_u200 = getenv("U200_FILE")
file_v200 = getenv("V200_FILE")
file_u850 = getenv("U850_FILE")
file_rlut = getenv("RLUT_FILE")
file_pr = getenv("PR_FILE")

print("daily_netcdf.ncl reading "+file_pr+" for time coordinates.")
print("   Assuming without checking that all have same time coordinates!")
f = addfile(file_pr,"r")

yr1 = stringtointeger(getenv("FIRSTYR"))
yr2 = stringtointeger(getenv("LASTYR"))

lat_coord = getenv("lat_coord")
lon_coord = getenv("lon_coord")
time_coord = getenv("time_coord")
time = f->$time_coord$
gw = get_gw(f,-40,40) 

if ( time@units.eq."julian day") then  ; set so cd_calendar can convert it
  time@units = "days since -4713-01-01 00:00:00" ;
  time@calendar = "julian"
end if ; time@units julian

;time_array = cd_calendar(time,0) ; separated YYYY,MM,DD,HH dim
time_all = cd_calendar(time,-3)  ; YYYYMMDDHH

i1 = 0
nd = dimsizes(time_all)
i2 = nd(0) - 1
debug_print("Time range in file: "+time_all(0)+" -"+time_all(i2),routine_name,debug)

  ; in hours to match cd_calendar/ut_calendar output YYYYMMDDHH
  ; uses 18 hrs for endtime since 6-hourly is the most high res we expect
  ; should still work for daily, just finds YYYY123100
  start_time = yr1*1000000+101*100
  end_time = yr2*1000000+1231*100+18
  debug_print("Time range requested: "+start_time+" "+end_time,routine_name,debug)
  tol = 24  ; 24 hours tolerance allows for different time resolutions
  do i=0,dimsizes(time_all)-1
;     debug_print("examining times "+i+" "+time_all(i),routine_name,debug)
     if( abs(time_all(i)-start_time).lt.tol) then
        i1 = i
        debug_print("Found start_time "+time_all(i)+" "+end_time,routine_name,debug)
     end if
     if( abs(time_all(i)-end_time).lt.tol) then
        i2 = i
        debug_print("Found end_time "+time_all(i)+" "+end_time,routine_name,debug)
     end if
  end do 
  delete(f)
  print("Time range indices: "+i1+" "+time_all(i1)+" - "+i2+" "+time_all(i2))
;  print("Time range indices: "+i1+" "+time_array(i1,:)+" - "+i2+" "+time_array(i2,:))


date = time_all(i1:i2)
print("Using date range:")
printMinMax(date,0)
ndays = dimsizes(date)


;
; Make sure date array is monotonic
;
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

; DRB: used to do pr, rlut separately. Folding them into the loop instead.
; **here first just use read_model_file for pr here, then put into var loop below
; precipitation rate (pr)
print("daily_netcdf.ncl reading "+file_pr+" for making precip file!")

delete_existing = False  ;True = overwrite, False = don't overwrite

if( isfilepresent(file_pr) ) then

  var_name = getenv("pr_var")
  var_name_out = "pr"
  file_in = file_pr
  file_out = wk_dir+casename+"."+var_name_out+".day.nc"
  var_name_3d_model = "not provided"
  file_in_3d = "not provided"
  file_in_ps = "not provided"
  plev = 0

  interp_opts = True  ; store this field as base resolution no matter what
  interp_opts@interp_to_var_name = var_name_out
  read_model_file (var_name, file_in,\
      		      var_name_out,file_out,\
		      delete_existing, \
      		      i1,i2,time_coord,lat_coord,lon_coord,date,\  ; better moved to another function for slicing
                      interp_opts,\
		      var_name_3d_model,plev,file_in_3d,file_in_ps)  ; optional args for pressure interp

else

  print("ERROR: daily pr input file does not exist for MJO diagnostics")
  

end if

;---------------------- moved up for speedier debugging -------------------

; To Do: 
; - incorporate the varname/file name setting into a function instead of repeating
; looks like procedures can modify arguments (intent inout) so just do that
; - make function work w/o optional arguments
; - make this a loop over the variable names
; - maybe make read and write separate functions with the coordinate subsetting done here


plevs = (/850,200/)       ;this package expects new files to be written with these names
var_names = (/"u","v"/)
do i=0,dimsizes(plevs)-1
   plev = plevs(i)
   do j=0,dimsizes(var_names)-1
      var_name_3d_model = getenv(var_names(j)+"_var")                           ; as read from history files (3D field
;      print(" var_name_3d_model "+var_name_3d_model)

;      print(" looking for "+var_names(j)+tostring(plev)+"_var")
      var_name_plev_model = getenv((var_names(j))+tostring(plev)+"_var")  ; as read from history files (pressure slice)
;      print(" var_name_plev_model "+var_name_plev_model)

      var_name_plev_package = var_names(j)+tostring(plev)      ; new file name & varname in file
;      print(" var_name_plev_package "+var_name_plev_package)

      ; DRB: TO DO: move this into read_model_file and only use in the
      ;      case that PS file isn't found. Also change hard-coded PS var
      ;      name and require PS file if level files aren't found

      file_in = datadir+"/day/"+casename+"."+var_name_plev_model+".day.nc"
      file_out = wk_dir+casename+"."+var_name_plev_package+".day.nc"
      ; All files supplied to POD are 3D slices; PS not part of varlist request
      file_in_3d =  datadir+"/day/"+casename+"."+var_name_3d_model+".day.nc"
      file_in_ps =  datadir+"/day/"+casename+".PS.day.nc"  ;drbdbg needs a getenv

      read_model_file (var_name_plev_model, file_in,\
      		      var_name_plev_package,file_out,\
		      delete_existing, \
      		      i1,i2,time_coord,lat_coord,lon_coord,date,\  ; better moved to another function for slicing
                      interp_opts,\
		      var_name_3d_model,plev,file_in_3d,file_in_ps)  ; optional args for pressure interp
;   print("After read_model_file "+var_name_plev_model)                     

    end do
end do


; outgoing longwave radiation (rlut)

print("daily_netcdf.ncl reading "+file_rlut)
if( isfilepresent(file_rlut) ) then
  
    var_name = getenv("rlut_var")
    var_name_out = "rlut"
    file_in = file_rlut
    file_out = wk_dir+casename+"."+var_name_out+".day.nc"
    var_name_3d_model = "not provided"
    file_in_3d = "not provided"
    file_in_ps = "not provided"
    plev = 0
    
    read_model_file (var_name, file_in,\
                     var_name_out,file_out,\
                     delete_existing, \
                     i1,i2,time_coord,lat_coord,lon_coord,date,\  ; better moved to another function for slicing
                     interp_opts,\
                     var_name_3d_model,plev,file_in_3d,file_in_ps)  ; optional args for pressure interp
;   print("After read_model_file "+var_name)                     
    
  
else ; file already exists

  print("daily rlut file does not exist for MJO diagnostics")

end if


end
