
var_name = "block_time"  ; this could be sent in, obviously!



; ------------------------------------------------------
function set_file_opts_out(file_opts_in)
begin

  file_opts_out = file_opts_in  ; copy everything
  
  dir_out = set_from_env("MDTF_BLOCKING_WRITE_DIGESTED_DIR",False)     ; directory to write into
  strs = str_split(file_opts_in@file_name, "/")  ; separate strings of path by "/"

  file_name_digested = strs(dimsizes(strs)-1)    ; file name is last string

  dir_one_up = strs(dimsizes(strs)-2)  ;add obs names to their file names
  if ((dir_one_up.eq."ERAI").or.(dir_one_up.eq."MERRA")) then  
    file_name_digested = dir_one_up+"."+file_name_digested
  end if
  file_opts_out@file_name_digested = dir_out+"/"+file_name_digested

  return file_opts_out
end

; ------------------------------------------------------
procedure write_digested(var,file_opts_in)
begin

;  Doesn't need to be general, just make it work!
;  Dimensions and sizes:[time | 1825] x [lon | 288]
;Coordinates: 
;            time: [13870..15694]
;            lon: [   0..358.75]
; Attributes:
; long_name :Blocking index (0=no; 1=yes)


  env_var_name = "MDTF_BLOCKING_WRITE_DIGESTED"
  env_settings = True
  env_settings@type_logical = env_var_name
  write_digested_flag = set_from_env(env_var_name,env_settings)
  if ( write_digested_flag ) then
    file_opts_out = set_file_opts_out(file_opts_in)

    time     = var&time
    lon = var&lon

    ; Create file
    file_out = file_opts_out@file_name_digested
    system("/bin/rm -f " + file_out)    ; remove if exists !DRB tie to settings flags
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
  else ;   write_digested_flag = False
    print("DEBUG: Not writing digested")
  end if  


end

; ------------------------------------------------------
function open_digested(file_opts)
begin

    fin = addfile(file_opts@file_name_digested,"r")
    return fin
end



; ------------------------------------------------------
function decide_to_use_digested(file_opts)
begin


   read_digested_flag = set_from_env_logical("MDTF_BLOCKING_READ_DIGESTED")
   if ( ismissing(read_digested_flag)) then ; default
     read_digested_flag = False; use full ensembles
   end if

   print("Read Digested Flag = "+read_digested_flag)

   if (read_digested_flag) then     ; see if there is one for this case

     file_opts = set_file_opts_out(file_opts)
     test = isfilepresent(file_opts@file_name_digested)
     if (test ) then
       return True
     else ;
       print("WARNING: read_digested = True but expected file not found for this case")
       print(file_opts@file_name_digested)
       print("         Attempting to read the raw file...")
       return False ; no attribute found with name
     end if
   else
     return False
   end if ;(read_digested_flag) then     ; see if there is one for this case

end



