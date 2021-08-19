
function isfilevar_TF(fin,var_name)
; strictly returns True (it is a file var) or False (it is not)
; ncl provided isfilevar either returns True or returns a missing value(!)
begin
  
     temp = isfilevar(fin,var_name)
     if ( ismissing(temp) ) then
       return False
     else
       return temp
     end if


end

; ------------------------------------------------------
function string_to_logical(args:string)
begin
; modified from ncl_talk. 
; returns True for any form of true, False for any form of False
; Otherwise returns missing
  cargs=str_lower(args)
  nstrs=dimsizes(args)
  largs=new(nstrs,logical)

  func_name = "string_to_logical"
  do i = 0,nstrs-1
    if any( (/"true","false"/) .eq. cargs(i))
      largs(i)=cargs(i) .eq."true"   ;drb not sure how this works but it does
    end if
    if (cargs(i).eq.0 ) then
      largs(i) = False
    end if
    if (cargs(i).eq.1 ) then
      largs(i) = True
    end if
  end do
;  print(func_name+" returning largs "+largs)
  return(largs)

end


; ------------------------------------------------------

function set_from_env_logical(name_in) ;could put quit on failure here
; check envvars, opts_in attributes, changes strings to logical if nec.
begin

  func_name = "set_from_env_logical"
;  print(func_name+" looking for "+name_in)

  found_good_setting = False
  setting = getenv(name_in)

  if (ismissing(setting)) then  ; if not in envs, check opts
;    print("WARNING: "+func_name+" did not find an envvar of name "+name_in)
   return setting ; string of type missing
  else
;    print(func_name+" found envvar "+name_in+" = "+setting)
  end if  ; if (ismissing(setting)) 


   setting_log = string_to_logical(setting)

   if ( ismissing(setting_log)) then
      print("ERROR: setting for envvar "+name_in+" must be True or  False")
      print("       instead of "+setting)
      delete(setting)
      return setting ; missing
    else
      return  setting_log
    end if

end ; set_from_env_logical


; -------- Main ----------------------------------------------

; set_from_env_logical("MDTF_DEBUG") ; switches to fewer ens members instead of 5
debug = set_from_env_logical("MDTF_DEBUG")
if ( ismissing(debug)) then
  delete(debug) ; because above sets it as string type (annoyingly!)
  debug = False; use full ensembles
end if



compare_long_years = False  
; False = user input dates control obs/ensembles
; True  = 1979-1999 used for obs/ensembles regardless of user input

; parameters that will be known by anyone loading this
all_colors = (/"blue","red","green","purple","orange","magenta","cyan"/)
verbose = 1
   ; 0= no response (not implemented), 1 = minimal, 2 = dani's preference, 3 = debug 



; ------------------------------------------------------
; Only works when run as main, unfortunately
; Copied from MJO_suite debug_print(string_to_print,routine_name,debug_flag)
procedure print_if_verbose_gt(threshold,what_to_print)
begin
  if ( verbose.gt.threshold ) then
;    print(routine_name+": "+what_to_print)
    print("func_blocking: "+what_to_print)
  end if

end ; procedure print_if_verbose_gt
        
; ------------------------------------------------------
procedure printVarSummary_if_verbose_gt(threshold,var)
begin
	if ( verbose.gt.threshold ) then
	   printVarSummary(var)
	end if
end


; ------------------------------------------------------

function extract_file_opts(all_cases,ifile)
begin
  func_name = "extract_file_opts"
;  print(func_name+" starting")
   file_opts = True	; just contains info for one file
   file_opts@file_name = all_cases@file_names(ifile)  ;file_names (with paths)
   file_opts@case_name = all_cases@case_names(ifile)  ;Ensemble name/legend label
   file_opts@var_name  = all_cases@var_names(ifile)
   file_opts@year0     = all_cases@years_run0(ifile)    ; set in case_info
   file_opts@year1     = all_cases@years_run1(ifile)

;   print(func_name+" "+file_opts@year0+" - "+file_opts@year1 )

   return file_opts
end ; function extract_file_opts(all_cases,index)

; ------------------------------------------------------
function extract_days(period_name)
; USAGE mnths = extract_days(period_name)
begin

   if (period_name.eq."DJF") then
     mnths_loc = (/1,2,12/)
   end if
   if (period_name.eq."MAM") then
     mnths_loc = (/3,4,5/)
   end if
   if (period_name.eq."JJA") then
     mnths_loc = (/6,7,8/)
   end if
   if (period_name.eq."SON") then
     mnths_loc = (/9,10,11/)
   end if
   if (period_name.eq."ANN") then
     mnths_loc = (/1,2,3,4,5,6,7,8,9,10,11,12/)
   end if

   return mnths_loc
end

; ------------------------------------------------------
procedure check_time_range(year0,year1,time_y_in)
begin
  func_name = "check_time_range"

  if (year0.lt.min(time_y_in)) then
    print("WARNING: user requested start year "+year0+" precedes data start year "+min(time_y_in))
    print("         proceeding with whatever is found")
  end if

  if (year1.gt.max(time_y_in)) then
    print("WARNING: user requested end year "+year1+" is after data end year "+max(time_y_in))
    print("         proceeding with whatever is found")
  end if
end
; ------------------------------------------------------
function find_required_days(year0,year1,period_name,time_ymd)
; USAGE idays = find_required_days(year0,year1,period_name,time_ymd)

begin
  func_name = "find_required_days"
;  print("starting "+func_name)
   mnths = extract_days(period_name)
; Time breakout of all data.
   time_y_in = time_ymd(:,0)
   time_m_in = time_ymd(:,1)
   time_d_in = time_ymd(:,2)

   ntime = dimsizes(time_y_in)

; Available data.
   print("Time range in file  : "+time_y_in(0)+" "+time_m_in(0)+" "+time_d_in(0)+" - "+time_y_in(ntime-1)+" "+time_m_in(ntime-1)+" "+time_d_in(ntime-1))

; Find required days of whole input data period.
   check_time_range(year0,year1,time_y_in)
   if (period_name.eq."ANN") then
     idays = ind(time_y_in.ge.year0.and.time_y_in.le.year1)
   else
     idays = ind((time_y_in.ge.year0.and.time_y_in.le.year1).and.(time_m_in.eq.mnths(0).or.time_m_in.eq.mnths(1).or.time_m_in.eq.mnths(2)))  
   end if

   ndays = dimsizes(idays)	
   ; Selected dates
   print("Requested time range: "+time_y_in(idays(0))+" "+time_m_in(idays(0))+" "+time_d_in(idays(0))+" - "+time_y_in(idays(ndays-1))+" "+time_m_in(idays(ndays-1))+" "+time_d_in(idays(ndays-1)))

   return idays

end
; ------------------------------------------------------
function blocking_check_var_units(var_in,var_name)
begin


     func_name = "blocking_check_var_units"
     if ( debug ) then
       print(func_name+" received var "+var_name)
;       printVarSummary(var_in)
       printMinMax(var_in,False)
     end if
     ; convert from Geopotential to geopotential height 
    if (.not.isatt(var_in,"units")) then
       found_guess = False

       ; perhaps use MDTF var codes here
       mystr = ": units attribute missing from "+var_name
       if ((var_name.eq."z500").or.(var_name.eq."Z500")) then
	  var_in@units = "m2/s2"
	  var_in@units = "m"
       	  print("WARNING"+mystr+". Assuming "+var_in@units+"based on var_name")
	  found_guess = True
       end if	  
       if ((var_name.eq."h500").or.(var_name.eq."H500")) then
       	  print("WARNING"+mystr+". Assuming m based on var_name")
	  var_in@units = "m"
	  found_guess = True
       end if	  
       if ( found_guess.eq.False ) then
       	  print("ERROR"+mystr+". No guess for units available for var_name (L152 blocking_func:blocking_readvar)")
	  exit
       end if
    end if  ;    if (.not.isatt(var_in,"units")) then

    if ( var_in@units.eq."-" ).or.( var_in@units.eq."m2s-2" ).or.( var_in@units.eq."m2/s2" ) then
     	print("Converting variable from geopotential ("+var_in@units+") to meters")
        var_out = var_in/9.80665
	var_out@units = "m"
	copy_VarMeta(var_in,var_out)
     else
        print("Variable units ("+var_in@units+") do not need conversion ")
	var_out = var_in
	copy_VarMeta(var_in,var_out)
     end if	

;     print(func_name+" returning")
     printVarSummary_if_verbose_gt(1,var_out)

     return var_out
end; blocking_check_var_units

; ------------------------------------------------------

function blocking_readvar(fin,opts)
begin; blocking_readvar
; USAGE var = blocking_readvar(fin,opts)
; required opts input = var_name
;
; Reads the variable from the file, then checks for and deals with special cases:
;    - reconstitues 'short' variables types 
;    - creates time var from julian day       

     func_name = "blocking_readvar"
     var_name = opts@var_name
;     print(func_name +" received "+var_name)

;just use the main one!     verbose = get_possible_attr(opts,"verbose",0)

;    assume for now that the attibutes are present
;     print(fin)
     var_0 = fin->$var_name$(opts@idays,{opts@lats_in:opts@latn_in},{opts@lonw_in:opts@lone_in})

     if (typeof(var_0).eq."short") then   ;drb make this a function
     	print("Converting variable from type short to float")
	var_1 = short2flt(var_0)
	copy_VarMeta(var_0,var_1)
        delete(var_0)
        var_0 = var_1
	copy_VarMeta(var_1,var_0)
	delete(var_1)
     else
        if (verbose.gt.1) then
;	   print("variable type ("+typeof(var_0)+") does not need conversion ")
	end if	   
     end if	

     var = blocking_check_var_units(var_0,var_name)

;     print(func_name+" returning")
     printVarSummary_if_verbose_gt(1,var)

     return var
end; blocking_readvar


; ------------------------------------------------------

function blocking_readtime(fin,opts)
begin; blocking_readtime
; USAGE time_ymd = blocking_readtime(fin,opts)
; Reads time from file, using year0,year1 limits
; if opts@period_name is set, calculates idays and returns as an attribute
; creates time_ymd appropriatly (using jul2greg or cd_calendar functions)
     func_name = "blocking_readtime"
;     print(func_name +" starting")

     if (isfilevar_TF(fin,"time_ymd")) then ; this is what we want, read it directly!     

       time_ymd = fin->time_ymd
       
       time = fin->time ; used later in code, could get rid of
     else ; read in time and calculate time_ymd

       time = fin->time

       if ((time@units .eq. "julian day").or.(time@units .eq. "Julian Day")) then  ;drb stronger to strmatch case-insensitive julian 
;         print(func_name+" converting time from "+time@units+" to time_ymd")
         time_ymd = jul2greg(time)	
       else  
;       print(func_name+" attempting to use cd_calendar to convert time from "+time@units+" to time_ymd")
         time@calendar = "noleap"     
         time_ymd = cd_calendar(time,0)     
         
         if (ismissing(any(time_ymd))) then
           print("ERROR: "+func_name+" failed to use cd_calendar to conver time from "+time@units+" to time_ymd")
           exit 
         end if ; ismissing(any(time_ymd))) then
       end if ; time@units

       time_ymd!0 = "time"
       time_ymd&time = time
     end if ; isfilevar time_ymd
     
     idays = find_required_days(opts@year0,opts@year1,opts@period_name,time_ymd)
     opts@idays = idays

     time_ymd_new = time_ymd(idays,:)
     time_ymd_new&time = time(idays)

     opts@time = time(idays)  ; send updated

     return time_ymd_new
end; blocking_readtime

; ------------------------------------------------------
function blocking_readfile_orig (opts)
; USAGE var =  block_readfile(opts)
; required input opts: file_name, var_name, year0, year1, period_name
;                      lonw_in,lone_in,lats_in,latn_in
; RETURNS  var[], var@time_ymd, var@idays, var@time


begin ;  blocking_readfile_orig
     func_name = "blocking_readfile_orig"

;     print(func_name +" opening "+opts@file_name+" to read time and "+opts@var_name)
     fin = addfile(opts@file_name,"r")

     opts@lon = fin->lon({opts@lonw_in:opts@lone_in})
     opts@lat = fin->lat({opts@lats_in:opts@latn_in})

     time_ymd = blocking_readtime(fin,opts)  ; time_ymd(idays), also sets  opts@idays, opts@time
     opts@time_ymd = time_ymd

     var = blocking_readvar(fin,opts)
     ; var and time_ymd are only dim idays; update actual idays


     printMinMax(var,False)

     delete(fin)

      return var  ; everything else should be in opts, which is returned as an updated value
	       
end ;  blocking_readfile_orig
; ------------------------------------------------------
function add_this_case_to_runlist(filelist,runlist)
; adds the file_names associated with this case/ensemble to the runlist
; returns runlist
begin
end
; ------------------------------------------------------

function get_input_opts(func_name,opts_in)
begin
  if ( opts_in ) then
    opts = opts_in
  else
    opts = True
  end if
  if ( (isatt(opts_in,"test")).or.(isatt(opts_in,"debug")) )  then
;    print("func_name+" get_input_opts: ")
;    printVarSummary(opts)
  end if

  return opts
end


;**here
; ------------------------------------------------------
function check_if_setting_is_type_logical(name_in,opts_in)
begin 

  func_name = "check_if_setting_is_type_logical"
  if (isatt(opts_in,"type_logical")) then
    if ( any( opts_in@type_logical .eq. name_in)) then
;      print(func_name+" found "+name_in+" in type_logical string "+opts_in@type_logical)
      return True
    else
;      print(func_name+" did not find "+name_in+" in type_logical string "+opts_in@type_logical)
    end if
  else
;    print(func_name+" did not find opts_in@type_logical attritute")
;    printVarSummary(opts_in@type_logical)
  end if
  return False

end


; ------------------------------------------------------
function check_if_setting_is_type_integer(name_in,opts_in)
begin 

  func_name = "check_if_setting_is_type_integer"
  if (isatt(opts_in,"type_integer")) then
    if ( any( opts_in@type_integer .eq. name_in)) then
      print("       converting "+name_in+" to integer ")
      return True
    else
;      print(func_name+" did not find "+name_in+" in type_integer string "+opts_in@type_integer)
    end if
  else
;    print(func_name+" did not find opts_in@type_integer attritute")
;    printVarSummary(opts_in@type_integer)
  end if
  return False

end
; ------------------------------------------------------
function ones_1d_int(n)
begin
  new_array = new(n,integer)
  new_array(:) = 1
  return new_array
end

; ------------------------------------------------------

function set_from_env(name_in,opts_in)
; check envvars, opts_in attributes, changes strings to logical if nec.
begin

  func_name = "set_from_env"
;  print(func_name+" looking for "+name_in)

  opts = get_input_opts(func_name,opts_in)
  
  found_good_setting = False
  setting = getenv(name_in)

  if (ismissing(setting)) then  ; if not in envs, check opts
    if (isatt(opts,name_in)) then
      setting = opts@$name_in$
      ;print(name_in+" = "+setting+" (found in opts)")
    end if ; if (isatt(opts,name_in)) 
  else
      ;print(name_in+" = "+setting+" (found in envvars)") 
  end if ; if (ismissing(setting)) 

  ; These should be separated and modularized.

  ; If it is supposed to be logical, convert/check
  if ( check_if_setting_is_type_logical(name_in,opts)) then
;    print("trying to convert input to logical for setting "+name_in+" = "+setting)
    setting_log = string_to_logical(setting)
;    print("setting_log "+setting_log)
    if ( ismissing(setting_log)) then
      print("ERROR: setting for env var "+name_in+" must be True or  False")
      exit
    else
      delete(setting)
      setting = setting_log
    end if
  end if ; if (isatt(opts,"type_logical"))

  
  if ( check_if_setting_is_type_integer(name_in,opts)) then
; DRB: using tointerger(set_from_env("VAR")) instead
;    print("trying to convert input to integer for setting "+name_in+" = "+setting)
    setting_int = stringtointeger(setting)
;    print("setting_int "+setting_int)
    if ( ismissing(setting_int)) then
      print("ERROR: error converting env var "+name_in+" to integer")
      exit
    else
      delete(setting)
      setting = setting_int
    end if
  end if ; if (isatt(opts,"type_integer"))


  ; If it is still missing, try for default
  if (ismissing(setting)) then
    if (isatt(opts,"default")) then
      setting = opts@default
    end if
  end if

  if (ismissing(setting)) then 
    print("WARNING: "+func_name+" did not find a value for env/opt "+name_in)
  end if

  return setting   ; might be missing


end ; set_from_env

; ------------------------------


function get_path_obs(opts)
begin
  return set_from_env("OBS_DATA",opts)
end

; ------------------------------------------------------
function get_blocking_settings()    
begin

; 1. Blocking index (D'Andrea et al., 1998)
  lat0 = 60.
  latn = 78.85
  lats = 41.25

; Latitude widths of the blocking regions
  deltas = (/-3.75,0,3.75/)
  settings = True
  settings@ndels = dimsizes(deltas)

;Block latitudes
  settings@phi_n = latn+deltas 
  settings@phi_0 = lat0+deltas
  settings@phi_s = lats+deltas

  settings@ghgn_thresh = -5.
  settings@ghgs_thresh = 0.

  settings@period_names = (/"ANN"/)  
  settings@nperiods = dimsizes(settings@period_names)


 return settings

end


; ------------------------------------------------------
function get_lons_plot()
; Longitudes to interpolate to for the figure
; DRB TODO
; this file is a static variable? But why not use one of the existing grids
; instead of something else entirely? 
begin
  obs_dir = get_path_obs(True)
  flons = addfile(obs_dir+"/cami_1987-01-01_0.9x1.25_L26_c060703.nc","r")
  lons_plot = flons->lon
  delete(flons)
  return lons_plot
end
; -------------------------------------------------------

procedure append_case_info(case_info,file_names,case_names,var_names,years_run0,years_run1,lcolors)
begin
  
  func_name = "append_case_info"

  if (.not.isatt(case_info,"file_names")) then    ; First time through
;    print(" "+func_name+" Creating new case_info data structure")
    case_info@file_names = file_names
    case_info@case_names = case_names
    case_info@var_names  = var_names
    case_info@years_run0 = years_run0
    case_info@years_run1 = years_run1
    case_info@plot_colors = lcolors
  else  ; Every subsequent call
;    print(" "+func_name+" adding case_info on to data structure")

    case_info_copy = case_info ; save existing array

    ; need to delete all the arrays because they are the wrong length
    ; eg: delete_VarAtts(x,(/"pineapple","peach","banana"/))
    atts_to_delete = (/"file_names","case_names","var_names","years_run0","years_run1","plot_colors"/)
    delete_VarAtts(case_info, atts_to_delete) ; delete only array attributes

    ; now put in the new, longer ones
    case_info@file_names = array_append_record(file_names,case_info_copy@file_names ,0)
    case_info@case_names = array_append_record(case_names,case_info_copy@case_names,0)
    case_info@var_names  = array_append_record(var_names ,case_info_copy@var_names,0)
    case_info@years_run0 = array_append_record(years_run0,case_info_copy@years_run0,0)
    case_info@years_run1 = array_append_record(years_run1,case_info_copy@years_run1,0)
    case_info@plot_colors= array_append_record(lcolors   ,case_info_copy@plot_colors,0)
    delete(case_info_copy)

  end if
; print(func_name+" returning case_info:")
;  print(case_info@file_names)
;  printVarSummary(case_info)


end ; append_case_info

; -- get light color ----------------------------------------------------
function get_light_color(color_in)  
; returns a light version of several colors, for shading the ensemble spread
begin

  
  func_name = "get_light_color"
;  print(func_name+" knows all_colors? "+all_colors)

  default = "LightGray"  
  light_color_name = default
  if (color_in.eq."blue") then
    light_color_name = "LightBlue"
  end if
  if (color_in.eq."red") then
    light_color_name = "LightPink"
  end if
  if (color_in.eq."green") then
    light_color_name = "palegreen1"
  end if
  if (color_in.eq."purple") then
    light_color_name = "plum1"
  end if
  if (color_in.eq."orange") then
    light_color_name = "lightsalmon"
  end if
  if (color_in.eq."magenta") then
    light_color_name = "PaleVioletRed1"
  end if
  if (color_in.eq."cyan") then
    light_color_name = "LightCyan"
  end if
  if (light_color_name.eq.default) then
    print("WARNING: "+func_name+" using "+default+" because no setting  found for "+color_in)
  end if

  return light_color_name
end 

; --  ----------------------------------------------------
function get_light_colors_array(color_array)
begin 
  n = dimsizes(color_array)
  light_colors = new(n,string)

  do i=0,n-1
    light_colors(i) = get_light_color(color_array(i))
  end do

  return light_colors
  
end 
; -- get new color ----------------------------------------------------
function get_new_color(icolor)  ; unused
begin

  func_name = "get_new_color"
; Doesn't seem to be a default; might run out for large numbers of cases
  if (icolor.gt.dimsizes(all_colors)) then
    print("ERROR: number of colors available in "+func_name+" too small for number of cases")
    exit 
  end if
  
  return  all_colors(i)   ;works up to 16



return
end


; ------------------------------------------------------
procedure check_required_file(file_names_in)
; full path 
; currently only takes on name, should expand to run over an array
begin

  nfiles =  dimsizes(file_names_in)
  if ( nfiles.eq.1 ) then  ; make array even for singular
    file_names_array = (/file_names_in/)
  else
    file_names_array = file_names_in
  end if
  do i=0,nfiles-1
    file_name = file_names_array(i)
    if ( .not. fileexists(file_name)) then
      print("ERROR: Missing file "+file_name)
      exit
    else
      print("  ...found file "+file_name)
    end if
  end do

end


; ------------------------------------------------------
procedure get_run_info_mdtf(case_info,opts)
; This is for a single case. For ensembles ideas, see cam5 etc
begin

  func_name = "get_run_info_mdtf"

  ; settings in mdtf input jsonc file or opts in testing function below
  case_names = set_from_env("CASENAME",opts) ; provided by MDTF
  print("--- Adding "+case_names)

  years_run0 = tointeger(set_from_env("FIRSTYR",opts))
  years_run1 = tointeger(set_from_env("LASTYR",opts))

  ; We name this envvar in this POD's settings.jsonc file MODEL_DATA_PATH
  model_data_env_var = "MODEL_DATA_PATH"
  model_data_path = set_from_env(model_data_env_var,opts)
   if (ismissing(model_data_path)) then
    print("ERROR: missing env var "+model_data_env_var)
    exit
  end if
  print("DRBDBG got model_data_path "+model_data_path)

  var_names = set_from_env("zg500_var",opts)  
              ;zg500_var decided in settings.jsonc file,
              ;actual variable name for input model determined in data/fieldlist_$model.jsonc

;  file_names = model_data_path  + "/"+case_names+"."+var_names+".day.nc"
  file_names = model_data_path  


  lcolors = "magenta"

  check_required_file(file_names)
        
  ; add this to other case info
  append_case_info(case_info,file_names,case_names,var_names,\
                   years_run0,years_run1,lcolors)

end


; ------------------------------------------------------
function get_run_info_cam5(case_info,opts)
begin

  func_name = "get_run_info_cam5"
  ; === CAM5.3 ===

  run_info = True ; return structure      
  run_info@run_name  = "30L_cam5301_FAMIP"
  run_info@case_name = "CAM5"
  run_info@var_name  = "Z500"
  run_info@obs_data  = False  ; does this matter anymore?
  run_info@file_path = opts@path_cam_ensembles
  run_info@line_colors = "blue"  
  nruns = 5
  run_info@nruns =  nruns

  file_names  = new(nruns,"string")
  do ile=0,nruns-1
    file_names(ile)  = run_info@run_name+ "/"+\
                       run_info@run_name+"."+sprinti("%0.3i",ile+1)+\
                       "_dmeans_ts_"+run_info@var_name+".nc"
  end do
  run_info@file_names = file_names
  return run_info

end ; get_run_info_cam5(case_info)

; --------------------------
function get_run_info_cam4(case_info,opts)
begin
  ; === CAM4 ===
  run_info = True ; return structure      
  run_info@run_name  = "f40.1979_amip.track1.1deg"
  run_info@case_name = "CAM4"
  run_info@var_name = "Z500"
  run_info@obs_data = False  ; does this matter anymore?
  run_info@file_path = opts@path_cam_ensembles
  run_info@line_colors = "red"  
  nruns = 5
  run_info@nruns =  nruns

  file_names  = new(nruns,"string")
  do ile=0,nruns-1
    file_names(ile)  = run_info@run_name+ "/"+\
                       run_info@run_name+"."+sprinti("%0.3i",ile+1)+\
                       "_dmeans_ts_"+run_info@var_name+".nc"
  end do
  run_info@file_names = file_names
  return run_info

end ; get_run_info_cam4(case_info)

; --------------------------
function get_run_info_cam3(case_info,opts)
; concise setting of file names, variable names specific to CAM3 
; w/o array overhead (where possible)
begin
  
  run_info = True ; return structure      
  run_info@run_name  = "eul128x256_d67iamip"
  run_info@case_name = "CAM3"
  run_info@var_name = "Z500"
  run_info@obs_data = False  ; does this matter anymore?
  run_info@file_path = opts@path_cam_ensembles
  run_info@line_colors = "green"  

  nruns = 5 ; reduced (by calling func) if file setting debug 
  run_info@nruns = nruns   ; short form used below, keep it!

  ; Annoying file_names for CCSM3 are different from later ones
  file_names  = new(nruns,"string")

  do ile=0,nruns-1
      file_names(ile)  = run_info@run_name+"/"+\
                                run_info@run_name+sprinti(".ES%0.2i",ile+1)+\
                                "_dmeans_ts_"+run_info@var_name+".nc"
  end do

  run_info@file_names = file_names

  return run_info

end ; get_run_info_cam3

; --------------------------
procedure get_run_info_cam_ensemble(case_info,opts,case_type) 
;USAGE eg get_run_info_cam_ensemble(case_info,opts,"CAM3")

begin

  func_name = "get_run_info_cam_ensemble"

  case_found = False
  if ( case_type .eq. "CAM3") then
    run_info  = get_run_info_cam3(case_info,opts) ; only passing opt  for path
    case_found = True
  end if
  if ( case_type .eq. "CAM4") then
    run_info  = get_run_info_cam4(case_info,opts) ; only passing opt  for path
    case_found = True
  end if
  if ( case_type .eq. "CAM5") then
    run_info  = get_run_info_cam5(case_info,opts) ; only passing opt  for path
    case_found = True
  end if
  if ( .not. case_found ) then
    print("ERROR: "+func_name+" case type "+case_type+" not found.")
    exit
  end if

        ; this can probabaly go straight into append_ call below
        nruns = run_info@nruns
        case_name = run_info@case_name
        var_name = run_info@var_name
        if ( debug ) then  ; cut any ens > 2 to 2
          nruns = min((/nruns,2/))
          print("Debug set in blocking_funcs, cutting NENS to 2")
        end if

	case_names  = new(nruns,"string")
        case_names  = run_info@case_name

	obs_data    = new(nruns,"logical")
        obs_data    = run_info@obs_data

	var_names   = new(nruns,"string")
        var_names   = run_info@var_name

	line_colors =  new(nruns,"string")
        line_colors = run_info@line_colors

	years_run0 = new(nruns,"integer")
	years_run1 = new(nruns,"integer")

        if ( compare_long_years ) then
          years_run0(:) = 1979 
          years_run1(:) = 1999
        else 
          years_run0(:) = tointeger(set_from_env("FIRSTYR",opts))
          years_run1(:) = tointeger(set_from_env("LASTYR",opts))
        end if

        ; file_names needs to be reduced in size if using debug-sized ensemble
        file_names = run_info@file_names(0:nruns-1)


        ; Add the path
        file_names_path = run_info@file_path +"/"+  file_names

        check_required_file(file_names_path)

        append_case_info(case_info,file_names_path,case_names,var_names,\
                                 years_run0,years_run1,line_colors)

end ; get_run_info_cam_ensemble(case_info)

; -------------------------------------------------------
function get_obs_names()
;if adding obs, check hard-coded file_names_o in get_run_info_obs
begin
  return (/"ERAI","MERRA"/) 
end

; -------------------------------------------------------
function get_obs_inds(case_names)
begin
  obs_names = get_obs_names()
  nobs = dimsizes(obs_names)
  obs_inds = new(nobs,integer)
  do i =0, nobs-1
    obs_inds(i) = ind(case_names.eq.obs_names(i))
  end do

  return obs_inds
end
; -------------------------------------------
procedure get_run_info_obs(case_info,opts)
begin
	; Construct final arrays.
  

	case_names_o = get_obs_names()  ; default ERAI, MERRA
        print("  ...Adding case "+case_names_o)

        ; Store for the subsquent processing which treats obs different
        ; from others
        case_info@obs_names = case_names_o
        case_info@nobs = dimsizes(case_names_o)

        path_obs = opts@path_obs
        file_names_o  = path_obs + "/"+(/case_names_o(0)+"/z500.day.mean.nc",\
		                    case_names_o(1)+"/H500.day.nc"/)
        var_names_o =  (/"z500","H500"/)

        if ( compare_long_years ) then
          years_run0 = 1979
          years_run1 = 1999
        else
          years_run0 = tointeger(set_from_env("FIRSTYR",opts))
          years_run1 = tointeger(set_from_env("LASTYR",opts))
        end if

	years_run0_o = (/years_run0,years_run0/)
	years_run1_o = (/years_run1,years_run1/)
;        print("obs years_run0 "+years_run0_o)
;        print("obs years_run1 "+years_run1_o)

        
	obs_data_o   = (/True,True/)
        plot_colors = (/"black","black"/)

        check_required_file(file_names_o)

        append_case_info(case_info,file_names_o,case_names_o,var_names_o,\
                                  years_run0_o,years_run1_o,plot_colors)

end ; get_run_info(case_info)


; ------------------------------------------------------
procedure add_case_info(case_name,case_info,opts_in)
; case_info (in) is a string of the case name
; This function adds attributes to case_info that hold all the information
; it calls obs,cam3,cam4,cam5 or mdtf depending on the name
; 
; type (in) is a string that indicates types
;      comparisons   : "obs", "model_cam3", "model_cam4", "model_cam5"
;      OR model types: "model_in_case", "model_in_ensemble"
begin

  func_name = "add_case_info"

  opts = get_input_opts(func_name,opts_in)
  ; This is used by the CAM versions as well as actual OBS, so set here
  path_obs   = get_path_obs(opts)
  opts@path_obs = path_obs
  opts@path_cam_ensembles = path_obs+"/CAM_ensembles"

  opts@read_digested  = set_from_env("MDTF_BLOCKING_READ_DIGESTED",opts)
  opts@write_digested = set_from_env("MDTF_BLOCKING_WRITE_DIGESTED",opts)

  case_name_found = False ; not used
  if ( case_name.eq."MDTF_BLOCKING_CAM5") then
    case_name_found = True
    get_run_info_cam_ensemble(case_info,opts,"CAM5")
  end if
  if ( case_name.eq."MDTF_BLOCKING_CAM4") then
    case_name_found = True
    get_run_info_cam_ensemble(case_info,opts,"CAM4")
  end if
  if ( case_name.eq."MDTF_BLOCKING_CAM3") then
    case_name_found = True
    get_run_info_cam_ensemble(case_info,opts,"CAM3")
  end if
  if ( case_name.eq."MDTF_BLOCKING_OBS") then
    case_name_found = True
    get_run_info_obs(case_info,opts)
  end if
  if ( case_name.eq."MDTF_CASE") then
    get_run_info_mdtf(case_info,opts)
  end if


end ; function add_case

; ------------------------------------------------------
function get_ensemble_names(case_names)
; This searches through all the case names and extracts the unique ensemble names
begin

  func_name = "get_ensemble_names"
  ncases = dimsizes(case_names)
  do i = 0,ncases - 1
    if (isvar("case_name")) then
      delete(case_name)
    end if
    case_name = case_names(i)

;    print("Searching for ensemble for case "+i+" "+case_name)
;function str_match (string_array   : string,  sub_string [1] : string   )
    if ( i.eq.0 ) then
      ensemble_names = (/ case_name /)
    else
      if any( ensemble_names .eq. case_name) then
;        print("found repeat "+case_name)
      else
        if any( get_obs_names .eq. case_name ) then
        else
;          print("found new "+case_name)
          copy_ensemble_names = ensemble_names  
          delete(ensemble_names)
          ensemble_names = array_append_record(case_name,copy_ensemble_names,0)
          delete(copy_ensemble_names)
        end if ; obs_names
      end if ; ensemble names
    end if ; i eq 0
  end do ; i 

;  print(func_name+" returning: ")
;  print(ensemble_names)

  return ensemble_names
end ; function get_ensemble_names

; ------------------------------------------------------
function get_ensemble_sizes(ensemble_names,case_names)
begin
  nens = dimsizes(ensemble_names)
  ne_size = new(nens,integer)
  do i = 0,nens - 1
    ne_name = ensemble_names(i)
    ne_size(i) = num(case_names.eq.ne_name)
;    print("Found "+ne_size(i)+" cases for ensemble "+ensemble_names(i))
  end do
  return ne_size
end ; function get_ensemble_sizes


; ------------------------------------------------------
function get_file_indices_from_ens_name(ens_name,case_names)
begin
  func_name = "get_file_indices_from_ens_name"

  return ind(case_names.eq.ens_name)

end


; ------------------------------------------------------
function get_file_indices_from_ens_name_group_obs(ens_name,case_names)
begin
  func_name = "get_file_indices_from_ens_name_group_obs"

  if (any( get_obs_names() .eq. ens_name ).or.(ens_name.eq."OBS")) then
    return get_obs_inds(case_names)
  else
    return get_file_indices_from_ens_name(ens_name,case_names)
  end if
end

; ------------------------------------------------------
function get_file_indices_from_ensemble(it1,iens,nobs,ne_size)  ; DEPRACATE?
begin

  func_name = "get_file_indices_from_ensemble"

    iarr = nobs+iens
    ; find index in array
    if (iens.eq.0) then  ; first time through
      it0 = nobs
    else                ; increment
      it0 = it1+1
    end if
    it1 = it0+ne_size(iens)-1

;    print(func_name+" returning iens "+iens+" it0 "+it0+" it1 "+it1+" iarr "+iarr)
    out = True
    out@iarr = iarr
    out@it0 = it0
    out@it1 = it1
    return out

end ; function get_file_indices_from_ensemble(iens,nobs,ne_size)

; ------------------------------------------------------
function get_yearstring_by_ensnames(ensemble_names,all_cases)
begin

  func_name = "get_yearstring_by_ensnames"
  nens = dimsizes(ensemble_names)
  yearstring = new(nens,string)
  do iens=0,nens-1
    ens_file_inds = get_file_indices_from_ens_name(ensemble_names(iens),all_cases@case_names)
    yearstring(iens) = all_cases@years_run0(ens_file_inds(0))+"-"+all_cases@years_run1(ens_file_inds(0))
;    print("Ensemble "+iens+" "+ensemble_names(iens)+" "+yearstring)
    delete(ens_file_inds); different sized each time
  end do

  return yearstring

end


; ------------------------------------------------------
function get_nfilestring_by_ensnames(ensemble_names,all_cases)
begin

  func_name = "get_nfilestring_by_ensnames"
  nens = dimsizes(ensemble_names)
  nfilestring = new(nens,string)
  do iens=0,nens-1
    ens_file_inds = get_file_indices_from_ens_name(ensemble_names(iens),all_cases@case_names)
    nfiles = dimsizes(ens_file_inds)
    if ( nfiles .gt. 1 ) then
      nfilestring(iens) = "("+nfiles+" members)"
    else
      nfilestring(iens) = ""
    end if
;    print("Ensemble "+iens+" "+ensemble_names(iens)+" "+nfilestring)
    delete(ens_file_inds); different sized each time
  end do

  return nfilestring

end

; ------------------------------------------------------
function blocking_get_all_case_info(opts_in)
; USAGE
; all_cases = blocking_get_all_case_info
; all_cases is an array of STRINGS (that match env vars, ie. BLOCKING_CAM5)
; each case = all_cases(i) has attributes (each dimension nfiles)
;   case@case_names = short names/ensemble name/label for plot
;   case@file_names = array of strings, all run names (obs + expanded ensembles)
;   case@years_run0, years_run1 = start and stop years corresponding to above
begin

	func_name = "blocking_get_all_case_info"
        opts = get_input_opts(func_name,opts_in)

        ;Defaults of comparsions: models & obs
        ; don't change these, to turn off, set matching envvars False in calling program
        default_cases = (/"MDTF_BLOCKING_OBS","MDTF_BLOCKING_CAM5","MDTF_BLOCKING_CAM4","MDTF_BLOCKING_CAM3"/)
        opts@type_logical = default_cases  ; these will fail on non-logical input

        ; Check envvar settings, if found will change default
        ; Could avoid the double line, even make it a loop, if have a
        ; general type and use the env var as the type
        ncases_init = dimsizes(default_cases)

        case_info = True
        do icase = 0,ncases_init - 1
          case_name = default_cases(icase)
          if ( set_from_env(case_name,opts) ) then  ; check  env/opts/defaults to decide to do this case
            print("--- Adding   "+case_name)
            add_case_info(case_name,case_info,opts) ; load file names, var names, etc
          else
            print("--- Skipping "+case_name)
          end if
        end do ; i
          
        ; Input models (single or ensembles)
        if (.not.ismissing(set_from_env("CASENAME",opts))) then
          ncases_in = 1  ;for now
          do icase = 0,ncases_in - 1
            add_case_info("MDTF_CASE",case_info,opts) ; load file names, var names, etc
          end do
        else
            print("--- Skipping MDTF input (no CASENAME env var found) ")
        end if

        
          
        if (verbose.gt.1) then
          print(func_name+" returning file_names : "+case_info@file_names)
          print(          "           years_run0: "+case_info@years_run0)
          print(          "           var_names  : "+case_info@var_names)
        end if	
        case_info@nfiles = dimsizes(case_info@file_names)

        ; Glean ensemble names and sizes, and obs_names from all_cases
        ensemble_names = get_ensemble_names(case_info@case_names) 
        nens = dimsizes(ensemble_names)    ; number of ensembles/case groups (not incl obs)
        ; ne_size(nens): number of files/cases per ensemble
        ne_size = get_ensemble_sizes(ensemble_names,case_info@case_names)  

        ; save info as attributes for subsequent functions
        case_info@ensemble_names = ensemble_names
        case_info@nens = nens

        if (isatt(case_info,"obs_names")) then
          ; This is the flag that will be used throughout
          case_info@nobs = dimsizes(case_info@obs_names)
        else
          case_info@nobs = 0
        end if
        

        
        return case_info

end ; blocking_get_all_case_info


; ------------------------------------------------------
function get_attr_from_func(opts_in,attr_name)  
begin     
  func_name = "get_attr_from_func"
  print(func_name+": received attr_name "+attr_name)
  attr_value = _FillValue
  if (attr_name.eq."obs_names")
    attr_value = get_obs_names()
  end if
  if (attr_name.eq."ensemble_names")
    attr_value = get_ensemble_names(opts_in)  ; better be all_cases!
  end if
  return attr_value
end

; ------------------------------------------------------
function get_possible_attr(opts_in,attr_name)    ; doesn't work to call the funcs
begin
	func_name = "get_possible_attr"

        attr_in_opts =  opts_in@$attr_name$
        print("attr_in_ops "+attr_in_opts)

        if ( any(isvar(attr_in_opts)) ) then 
     	   if (isatt(opts_in,attr_name)) then
	      print(func_name+" found attribute with name"+attr_name+" and value "+opts_in@$attr_name$)
	      attr_value = opts_in@$attr_name$
	   else
	      print(func_name+" did not find attribute with name "+attr_name+" from following opts")
              print("Checking functions to set it")
              attr_value = get_attr_from_function(opts_in,attr_name)
              print("After function check "+attr_name)
	   end if	      
         else
           attr_value = attr_in_opts ; return missing
         end if

;         print(func_name+" returning "+attr_value)
	return attr_value

end


; ------------------------------------------------------
function get_possible_attr_defunct(opts_in,attr_name,attr_default)  
begin
; split into two: one is_var_with_attr that does the checking if it's an attribute, call this for idays
; then if it is an attribute, set it, or return the default

	func_name = "get_possible_attr_defunct"
        printVarSummary_if_verbose_gt(2,opts_in)
    	if ( isvar("opts_in")) then
     	   if (isatt(opts_in,attr_name)) then
	      print(func_name+" found attribute with name"+attr_name+" and value "+opts_in@$attr_name$)
	      return opts_in@$attr_name$
	   else
	      print(func_name+" did not find attribute with name "+attr_name+" from following opts")
	      printVarSummary_if_verbose_gt(2,opts_in)
	   end if	      
        else
           print(func_name+" did not find opts_in")
	end if
	return attr_default

end


; ------------------------------------------------------
function get_line_color_by_casename(casename,all_cases)
begin
  
  func_name = "get_line_color_by_casename"

 i = ind(casename.eq.all_cases@case_names)
 if (.not.any(ismissing(i))) then
   ; found
   if ( dimsizes(i).gt.1 ) then
     j = i(0)
     delete(i)
     i = j
     delete(j)
   end if
 else
   print("ERROR: "+func_name+ " did not find casename "+casename )
   print("       within available all_cases@case_names: ")
   print(" "+all_cases@case_names)
   exit
 end if

;  print(func_name+" input casename "+casename+" found color  "+all_cases@plot_colors(i) )

  return all_cases@plot_colors(i)

end
; ------------------------------------------------------
function get_line_colors(line_names,all_cases)
begin

 func_name = "get_line_colors"

 nlines = dimsizes(line_names)
 my_colors = new(nlines,string)

 do i = 0,nlines-1
   my_colors(i) = get_line_color_by_casename(line_names(i),all_cases)
 end do

 return my_colors
end

; ------------------------------------------------------
function get_panel_layout(npanels)
begin

  func_name = "get_panel_layout"

  if ( npanels .gt. 3 ) then
    sqrt_n = sqrt(npanels)
    sqrt_N = ceil(sqrt_n)

    return_val = (/sqrt_N,sqrt_N/)
  else
    return_val = (/npanels,1/)
  end if

  return tointeger(return_val)
end

; ------------------------------------------------------
function get_plot_settings_ann_cycle(wks_t,all_cases)
begin

  func_name = "get_plot_settings_ann_cycle"
  res_t = True
  res_t@gsnDraw = False
  res_t@gsnFrame = False
  
  res_t@tmXBMode = "Explicit"
  res_t@tmXBLabelFontHeightF = 0.012
  res_t@tmXBValues = (/-90.,-60.,-30.,0.,30.,60,90,120,150,180,210,240,270/)
  res_t@tmXBLabels = (/"90~F34~0~F~W","60~F34~0~F~W","30~F34~0~F~W","0~F34~0~F~","30~F34~0~F~E","60~F34~0~F~E","90~F34~0~F~E","120~F34~0~F~E","150~F34~0~F~E","180~F34~0~F~E","210~F34~0~F~E","240~F34~0~F~E","270~F34~0~F~E"/)
  res_t@tmYLMode = "Explicit"
  res_t@tmYLLabelFontHeightF = 0.02
  res_t@tmYLValues = -15.5+(/31,59,90,120,151,181,212,243,273,304,334,364/)
  res_t@tmYLLabels = (/"JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"/)
  
  res_t@cnFillOn             = True                
  res_t@cnLinesOn            = True           
  res_t@lbLabelBarOn         = False        
  res_t@cnInfoLabelOn        = False  
  

  res_t@cnLevelSelectionMode = "ExplicitLevels"
  res_t@cnFillColors  = (/-1,-1,20,20,12,12,12,12,12,12,12/)   ;hard-coded to 2 obs first
  res_t@cnLevels = (/5.,10,15,20,25,30,35,40,45,50/)
;  print("WARNING: "+func_name+" is still hard-coding contour fill colors")
  
  return res_t

end ; function get_plot_settings_ann_cycle(wks_t,all_cases)

; ------------------------------------------------------
function get_plot_settings_season(wks,all_cases)
begin

  gsn_define_colormap(wks,"rainbow")

  res = True
  res@xyLineColors = all_cases@line_colors 
  
  res@tmXBMode = "Explicit"
  res@tmXBLabelFontHeightF = 0.008
  res@trYMinF  = 0.                   
  res@trYMaxF  = 24.               
  res@trXMinF  = -90.                   
  res@trXMaxF  = 270.0   
  
  res@tiXAxisString    = "Longitude"        
  res@tiYAxisString    = "Blocking frequency (%)"
  res@tmYLLabelFontHeightF = 0.008
  
; L100
  res@tmXBValues = (/-90.,-60.,-30.,0.,30.,60,90,120,150,180,210,240,270/)
  res@tmXBLabels = (/"90~F34~0~F~W","60~F34~0~F~W","30~F34~0~F~W","0~F34~0~F~","30~F34~0~F~E","60~F34~0~F~E","90~F34~0~F~E","120~F34~0~F~E","150~F34~0~F~E","180~F34~0~F~E","210~F34~0~F~E","240~F34~0~F~E","270~F34~0~F~E"/)
  
  res@xyMonoLineThickness = True
  res@xyLineThicknessF = 5
  res@xyDashPatterns = all_cases@line_types
  
  
return res
end ; function get_plot_settings_season(wks,all_cases)

; ------------------------------------------------------
function get_plot_settings_panel(res,all_cases)
begin

res_m = True
res_m@gsnDraw = False
res_m@gsnFrame = False

res_m@gsnMaximize = True

res_m@gsnDraw            = False                   ; don't draw
res_m@gsnFrame           = False                   ; don't advance frame
res_m@xyMonoLineColor    = False             ; want colored lines

res_m@vpWidthF         = 0.9                      ; set width and height
res_m@vpHeightF        = 0.75

res_m@tiXAxisString    = res@tiXAxisString    
res_m@tiYAxisString    = res@tiYAxisString    


res_m@tmXBMode = "Explicit"
res_m@tmXBLabelFontHeightF = 0.017
res_m@trYMinF  = 0.                   
res_m@trYMaxF  = 24.               
res_m@trXMinF  = -90.                   
res_m@trXMaxF  = 270.0   

res_m@tmXBValues =  res@tmXBValues 
res_m@tmXBLabels =  res@tmXBLabels 

; need to meerge this with legend
res_m@xyLineColors       = res@xyLineColors
res_m@xyLineThicknessF  = res@xyLineThicknessF
res_m@xyDashPatterns	 = res@xyDashPatterns

  return res_m
end


; ------------------------------------------------------
procedure set_legend(all_cases)
begin

  func_name = "set_legend"

; all_cases needs to have attributes: ensemble_names, obs_names

  nens = all_cases@nens
  if ( nens .gt. 0 ) then
    ensemble_names = all_cases@ensemble_names
  else
    ensemble_names = ""
  end if

  nobs = all_cases@nobs
  if ( nobs .gt. 0 ) then
    obs_names      = all_cases@obs_names
  else
    obs_names = ""
  end if


;not yet written  ens_dates     = get_ensemble_dates(all_cases)
  nlines = nobs + nens

  legend_names = new(nlines,string)  ; These need to match case_names in all_cases
  if ( nobs.gt.0 ) then
    legend_names(0:nobs-1)      = obs_names      ; (/"  ERAI","  MERRA",
  end if
  if ( nens.gt.0 ) then
    legend_names(nobs:nlines-1) = ensemble_names ;   "CAM5","  CAM4","  CAM3", MDTF_case/) ;
  end if
; 16 line types  https://www.ncl.ucar.edu/Document/Graphics/Images/dashpatterns.png
; 0 = solid, 1 = dotted, 2= dash, 3 + ? 
; previous did all solid
  line_types  = ones_1d_int(nlines) - 1 ; zeros

  ; Only have MDTF_case (last ens) as solid
  do i=1,nobs-1  ; obs1 solid (0), obs2 dash (1)
    line_types(i) = i   
  end do
  do i=nobs,nlines-2  ; all but last one are different, starting with dot
    line_types(i) = i-nobs+1
  end do

  line_colors = get_line_colors(legend_names,all_cases)

  ; Add start and end years to each case, according to its ensemble
  ; call after get_line_colors call because it uses legend_names
  yearstring = get_yearstring_by_ensnames(legend_names,all_cases)
  nfilestring = get_nfilestring_by_ensnames(legend_names,all_cases)
  legend_names = legend_names + " "+yearstring + " "+nfilestring

  ; reverse the order...because that's what works. 
  ; yep, I should write a ispan_reverse_order function to do this
  temp = ispan(0,nlines-1,1)   
  item_order = temp(::-1)
  delete(temp)

; store for future functions
  all_cases@nlines = nlines
  all_cases@nobs   = nobs
  all_cases@nens   = nens

  all_cases@legend_names = legend_names
  all_cases@line_colors  = line_colors  ; length nlines
  all_cases@line_types   = line_types
  all_cases@item_order   = item_order

;  print(func_name+" "+all_cases@legend_names+" "+all_cases@line_colors)



end
; ------------------------------------------------------
function get_ens_name_or_obs_name(name)
begin
    if ( any(name.eq.get_obs_names())) then
      return "OBS"
    else
      return name
    end if
end



; ------------------------------------------------------
function get_plot_anncycle_ensname(name,all_cases,settings,res_t)
begin
  func_name = "get_plot_annycle_ensname"

  if (any(settings@period_names.eq.(/"ANN"/))) then 
    
  if (any( get_obs_names().eq.name ).or.(name.eq."OBS")) then
      print(func_name+" found obs")
      path_out = settings@path_out_obs 
    else
      iens = name
      print(func_name+" found model ens "+iens)
      path_out = settings@path_out_model
    end if

    full_name = path_out +"/"+settings@figure_name_anncycle+"."+name
    print("Writing figure: "+full_name)

    wks_t = gsn_open_wks(settings@figure_type, full_name)
    gsn_define_colormap(wks_t,"gsdtol")      ; choose
    res_t = get_plot_settings_ann_cycle(wks_t,all_cases)  

  end if

  return wks_t

end ; get_plot_anncycle


; ------------------------------------------------------
function get_plot_season(all_cases,settings,res)  ; res is returned too
begin
  func_name = "get_plot_season"

; Plot mean lon plot (line plot)
  full_path = settings@figure_name_season
  print(func_name+" "+full_path)
  wks = gsn_open_wks(settings@figure_type, full_path)
  res = get_plot_settings_season(wks,all_cases)  


  return wks
end ; get_plot_season

; ------------------------------------------------------
function set_plotting_info(all_cases,settings)
begin
  func_name = "set_plotting_info"
  
  ; plot_array will store the figures
  ; but also have attributes of all the wks, res etc.
  plot_array = new(all_cases@nfiles,"graphic")


  set_legend(all_cases)  ; adds information to attributes of all_cases

  nfiles = dimsizes(all_cases@file_names)

; Documentation says WK_DIR but MDTF uses DATADIR (?)
  path_out        = set_from_env("WK_DIR",False)

; These are hard-coded into mdtf/src/output_manger.py:convert_pod_figures
  path_out_model  = path_out +"/model/PS/"  ; will get season, + model block_freq
  path_out_obs    = path_out +"/obs/PS/"    ; will get obs + ens block_freq
  figure_type = "ps"
  figure_name_season = path_out_model+"block_freq_season"    
;  figure_name_season = "block_freq_season"    

  figure_name_anncycle = "block_freq_anncycle"  ; path added at plot write time for wks_t2

  print("Writing figures to: "+path_out_model)
  print("Writing figures to: "+path_out_obs)
  settings@path_out_model = path_out_model
  settings@path_out_obs = path_out_obs
  settings@figure_type = figure_type
  settings@figure_name_season = figure_name_season
  settings@figure_name_anncycle = figure_name_anncycle

  ; this is the array that is returned from this
  plot_array = new(nfiles,graphic)
  return plot_array

end ; function set_plotting_info(all_cases)

; ------------------------------------------------------
 function get_plot_settings_t(all_cases)
begin
; Panel settings
  pan_t = True
  pan_t@gsnMaximize = True
  pan_t@txString = "Blocking frequency Hovmueller"
                  ; "("+min(all_cases@years_run0)+"-"+max(all_cases@years_run1)+")"
                  ; Above now included for each panel
  pan_t@gsnPaperOrientation = "Portrait"
  return pan_t
end

; ------------------------------------------------------
function get_plot_settings_m(all_cases)
begin
; Graphics
  pan_m = True
  pan_m@gsnFrame = False
  pan_m@gsnMaximize = True
  pan_m@gsnPaperOrientation = "Portrait"

  return pan_m

end 

; ------------------------------------------------------
function get_legend(wks_in,all_cases)
; must call after set_plotting_info for required all_cases attributes:
; legend_names, line_colors, line_types
begin
  
  func_name = "get_legend"

legend0 = create "Legend" legendClass wks_in
"lgTitleString"            : ""
"lgTitleFontHeightF"        : 0.02
"vpXF"                     : 0.05                  ; orientation on page
"vpYF"                     : 1.05
"vpWidthF"                 : 0.25                     ; width
"vpHeightF"                : 0.15                     ; height
"lgPerimOn"                : False                  ; no perimeter
"lgItemCount"              : all_cases@nlines                   ; how many
"lgLabelStrings"           : all_cases@legend_names
"lgLabelsOn"               : True                   ; no default lables
"lgMonoDashIndex"          : False
"lgMonoLineThickness"      : True
"lgLineThicknessF"         : 5
"lgDashIndexes"            : all_cases@line_types
"lgLabelFontHeightF"       : 0.015                  ; font height
"lgLineColors"             : all_cases@line_colors
"lgMonoLineLabelFontColor" : False                    ; one label color
"lgItemOrder"              : all_cases@item_order
"lgAutoManage"             : False
"lgLabelJust"              : "CenterLeft"
end create

return legend0

end ; function get_legend(

; ------------------------------------------------------
procedure set_case_years(case_years_used,year_in)
; returns  case_years_used@min
;          case_years_used@max

begin

  func_name = "set_case_years"
  if (isatt(case_years_used,"min")) then
    case_years_used@min = min((/case_years_used@min,year_in/))
  else
    case_years_used@min = year_in
  end if

  if (isatt(case_years_used,"max")) then
    case_years_used@max = max((/case_years_used@max,year_in/))
  else
    case_years_used@max = year_in
  end if


end ; function set_case_years
