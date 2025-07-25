
var_name = "block_time"  ; this could be sent in, obviously!



function set_file_name_write_digested(file_opts_in)
; Only used to WRITE_DIGESTED; 
; READ_DIGESTED filename set through blocking_funcs.ncl set_and_check_file
; Set the file name and direction for the digested file
; based off the information in the undigested file name
begin


  file_opts_out = file_opts_in  ; copy everything
  path_out        = set_from_env("WORK_DIR",False)                    ; wkdir
  dir_out = set_from_env("MDTF_BLOCKING_WRITE_DIGESTED_DIR",False)  ; write directory

  strs = str_split(file_opts_in@file_name, "/")  ; separate strings of path by "/"

  file_name_digested = strs(dimsizes(strs)-1)    ; file name is last string


  dir_one_up = strs(dimsizes(strs)-2)  ;add obs names to their file names
  if ((dir_one_up.eq."ERAI").or.(dir_one_up.eq."MERRA")) then  
    file_name_digested = dir_one_up+"."+file_name_digested
  end if

  path_plus_dir = path_out+"/"+dir_out
  file_opts_out@file_name_digested = path_plus_dir+"/"+file_name_digested

  print("Making directory to write digested files: "+path_plus_dir)
  system("mkdir -p "+path_plus_dir)


  return file_opts_out
end

; ------------------------------------------------------
procedure write_digested(var,file_opts_in)
begin

; Coordinates:  time, lon
; long_name :Blocking index (0=no; 1=yes)


  env_var_name = "MDTF_BLOCKING_WRITE_DIGESTED"
  env_settings = True
  env_settings@type_logical = env_var_name
  write_digested_flag = set_from_env(env_var_name,env_settings)
  if ( write_digested_flag ) then
    file_opts_out = set_file_name_write_digested(file_opts_in)

    time     = var&time
    lon = var&lon

    ; Create file
    file_out = file_opts_out@file_name_digested
    system("/bin/rm -f " + file_out)    ; remove if exists 
    fout  = addfile (file_out, "c")  ; open output file
    setfileoption(fout,"DefineMode",True)

    ; Create global attributes of the file
    fAtt               = file_opts_out
    delete_VarAtts(fAtt,(/"lon","lat","time","idays","time_ymd"/))
    fAtt@history = "Created by blocking_digested.ncl:write_digested() "
    fAtt@creation_date = systemfunc ("date")        
    fileattdef( fout, fAtt )            ; copy file attributes    

    ; Define dimensions on file
    dimNames = (/"time","lon","ncalendar"/)
    ntim  = dimsizes(time)                 ; get dimension sizes  
    nlon  = dimsizes(lon)      

    time_ymd = file_opts_in@time_ymd
    dims_time_ymd = dimsizes(time_ymd)
    print("write_digested "+dims_time_ymd)
    ncalendar = dims_time_ymd(1)

    dimSizes = (/ -1   , nlon, ncalendar /) 
    dimUnlim = (/ True , False, False/)   
    filedimdef(fout,dimNames,dimSizes,dimUnlim)



    time_ymd!0 = "time"
    time_ymd&time = time
    time_ymd!1 = "ncalendar"

    ; Define the  dimensionality of the variables to be written out
    filevardef(fout, "time" ,typeof(time),getvardims(time)) 
    filevardef(fout, "time_ymd" ,typeof(time_ymd),getvardims(time_ymd)) 
    filevardef(fout, "lon"  ,typeof(lon),getvardims(lon)) 
    filevardef(fout, var_name  ,typeof(var),getvardims(var)) 

    ; All attributes associated with each variable will be copied.
    filevarattdef(fout,var_name,var)


    ; explicitly exit file definition mode. **NOT REQUIRED**
    setfileoption(fout,"DefineMode",False)

    fout->time   = (/time/)     
    fout->lon    = (/lon/) 
    fout->$var_name$      = (/var/)

    fout->time_ymd = time_ymd
    print("Wrote digested file "+file_out)
    print("(if the file is not present after the run, set 'save_nc: true' in input to MDTF)")
  end if  


end

; ------------------------------------------------------
function open_digested(file_opts)
; File name set in blocking_funcs.ncl:set_and_check_file_names
; whether digested or undigested
begin

    fin = addfile(file_opts@file_name,"r")
    return fin
end


; ------------------------------------------------------
procedure set_digested(opts)
; copies env vars to opts: READ_DIGESTED, WRITE_DIGESTED
begin

   read_digested_flag = set_from_env_logical("MDTF_BLOCKING_READ_DIGESTED",opts)
   if ( ismissing(read_digested_flag)) then ; default
     read_digested_flag = False; use full ensembles
   end if
 
   write_digested_flag = set_from_env_logical("MDTF_BLOCKING_WRITE_DIGESTED",opts)
   if ( ismissing(write_digested_flag)) then ; default
     write_digested_flag = False; use full ensembles
   end if

   print("Read  Digested = "+read_digested_flag)
   print("Write Digested = "+write_digested_flag)

   if ( read_digested_flag .and. write_digested_flag ) then
     print("ERROR: MDTF_BLOCKING_WRITE_DIGESTED = True requires MDTF_BLOCKING_READ_DIGESTED = False")
     exit
   end if
end

