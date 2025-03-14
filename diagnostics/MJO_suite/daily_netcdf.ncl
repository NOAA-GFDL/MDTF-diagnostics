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

undef("check_date_format")
function check_date_format(date_in,date_type,routine_name,debug)
begin
  if (date_in.lt.1.e4) then  ; input just YYYY, need to add MMDDHH
    if (date_type.eq."start") then  
      date_suffix = 101*100
    else if (date_type.eq."end") then  
      date_suffix = 1231*10
      else 
        print("ERROR: "+routine_name+" No date_type given to function check_date_format")
      end if
    end if
    
    debug_print("Incoming "+date_type+" date YYYY format: "+date_in,routine_name,debug)
    date_out = date_in*1000000+ date_suffix
    debug_print("Corrected "+date_type+" date to:"+date_out,routine_name,debug)

  else
    if (date_in .lt. 100000000) ; YYYYMMDD
      debug_print("Incoming "+date_type+" date YYYYMMDD format: "+date_in,routine_name,debug)
      date_out = date_in*100 ;; HH = 00
      debug_print("Corrected "+date_type+" date to:"+date_out,routine_name,debug)
    else
      debug_print("Found start date format YYYYMMDDHH: "+yr,routine_name,debug)
      date_out = date_in
    end if ; YYYYMMDD
  end if ; YYYY

  return date_out
end ; function check_date_format

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
wk_dir = getenv("WORK_DIR")+"/model/"

file_u200 = getenv("U200_FILE")
file_v200 = getenv("V200_FILE")
file_u850 = getenv("U850_FILE")
file_rlut = getenv("RLUT_FILE")
file_pr = getenv("PR_FILE")

print("daily_netcdf.ncl reading "+file_pr+" for time coordinates.")
print("   Assuming without checking that all have same time coordinates!")
f = addfile(file_pr,"r")

yr1 = stringtointeger(getenv("startdate"))
yr2 = stringtointeger(getenv("enddate"))

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

; Check if date came in as YYYYMMDD or YYYY (historic)
start_time = check_date_format(yr1,"start",routine_name,debug)
end_time   = check_date_format(yr2,"end",routine_name,debug)

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

; First just use read_model_file for pr here, then put into var loop below
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
      file_var_name = str_upper(var_names(j))+tostring(plev)+"_FILE"
      ;file_in = datadir+"/day/"+casename+"."+var_name_plev_model+".day.nc"
      file_in = getenv(file_var_name)
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
