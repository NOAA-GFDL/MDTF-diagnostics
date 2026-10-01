; This file is part of the Wheeler_Kiladis module of the MDTF code package (see LICENSE.txt)
setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))


;==================================================================
;                     USER INTERFACE 
;                   MAIN DRIVER SCRIPT
;==================================================================

; This file is part of the Wheeler_Kiladis module of the MDTF code package (see LICENSE.txt)
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/debug_plots.ncl" 

time_i = 10
undef("replace_missing_with_zeros")
function replace_missing_with_zeros( x,array_missing,debug_flag )
begin
  routine_name = "replace_missing_with_zeros"
  debug_print("Into ",routine_name,debug_flag)
  map_flag = True
    x_fixed = where(array_missing,0.,x)
    copy_VarMeta(x,x_fixed)
    if (debug_flag) then
      one_plot(x(time_i,:,:),"removed_missing_zeros_before",map_flag,debug_flag)
      one_plot(x_fixed(time_i,:,:),"removed_missing_zeros_after",map_flag,debug_flag)
      diff_plot(x(time_i,:,:),x_fixed(time_i,:,:),"removed_missing_zeros_diff",debug_flag)
    end if
    return x_fixed
end ;replace_missing_with_zeros


undef("replace_missing_with_zonal_avg")
function replace_missing_with_zonal_avg( x, array_missing, debug_flag )
begin
  routine_name = "replace_missing_with_zonal_avg"
  debug_print("Into replace_missing_with_zonal_avg",routine_name,debug_flag)

dim_i = 2 ; this is the dimension to average
    xavg = dim_avg_n(x, dim_i)  ; zonal avg (time,lon)
    debug_print("XAVG at time "+time_i+" "+xavg(time_i,:),routine_name,debug_flag)

    xavg_conformed = conform(x,xavg,(/0,1/))   ; conform to x 
    copy_VarMeta(x,xavg_conformed)
    if ( debug_flag ) then
      map_flag = False
      one_plot(xavg_conformed(time_i,:,:),"removed_missing_zonal_before",map_flag,debug_flag)
;     one_plot(x(time_i,:,:),"removed_missing_zonal_before",map_flag,debug_flag)
;     one_plot(x_fixed(time_i,:,:),"removed_missing_zonal_after",map_flag,debug_flag)
;     diff_plot(x(time_i,:,:),x_fixed(time_i,:,:),"removed_missing_zonal_diff",debug_flag)
    end if

  ; where (condition is true, use this, else use this)
    x_fixed = where(array_missing,xavg_conformed,x)
    if ( debug_flag ) then
      one_plot(x_fixed(time_i,:,:),"removed_missing_zonal_after",map_flag,debug_flag)
      diff_plot(x(time_i,:,:),x_fixed(time_i,:,:),"removed_missing_zonal_diff",debug_flag)

    end if
    copy_VarMeta(x,x_fixed)
  return x_fixed
end  ;         replace_missing_with_zonal_avg


undef("replace_missing_values")
procedure replace_missing_values( x, debug_flag )
begin
;ex nmsg = num(ismissing(x))   ; count number of missing
;ex igood = ind(.not.ismissing(x))

  routine_name = "replace_missing_values"
  array_missing = ismissing(x)
  debug_print("started.",routine_name,debug_flag)
;  one_plot(x(0,:,:),"x_raster",debug_flag)

  if (x@name.eq.getenv("pr_var")) then
    debug_print("Replacing "+x@name+" missing values with zeros",routine_name,debug_flag)
;save
    x_new = replace_missing_with_zeros( x,array_missing,debug_flag )
;    x_new = replace_missing_with_zonal_avg( x,array_missing )

  else
    debug_print("Replacing "+x@name+" missing values zonal average",routine_name,debug_flag)
    x_new = replace_missing_with_zonal_avg( x,array_missing,debug_flag )
  end if

;  delete(x)
  x = x_new  ;returned updated in argument list

end ; replace_missing_values


undef("check_lon")
procedure check_lon(f,latS,latN,lonL,lonR,lon_diff,debug_flag)
begin


  fname = "check_lon"
  filedims = getfiledims(f)
  debug_print("matched lon? "+str_match(filedims,"lon"),fname,debug_flag)
  lon = f->lon
  debug_print("File lon range "+min(lon)+" "+max(lon)+", script asks for  "+lonL+" "+lonR,\
               fname,debug_flag)

; shift limits to match what's in the file, in order to read it in
; set the flag in order to change back, and change lon itself
  if (min(lon).lt.0) then 
    lon_diff = 360. - max(lon)  ; difference from expected, serves as a flag when non-zero
    lonL = lonL - lon_diff
    lonR = lonR - lon_diff
    debug_print("Lon diff: "+lon_diff+" results in adjusted lon limits:"+lonL+" "+lonR,fname,debug_flag)
  end if

end; check_lon

undef("getVarSlice")
function getVarSlice( fili[*], varName:string, level, latS, latN, lonL,lonR, tstride:integer, i1:integer, i2:integer, debug_flag)
begin


  routine_name = "getVarSlice"

  debug_print("started routine",routine_name,debug_flag)
    nfil = dimsizes(fili)
    f    = addfile (fili(0), "r")

    ; If lon dimension is -180:180, change lonL,lonR to reflect that
    lon_diff = 0.  ; if changed, gives the change that was made
    check_lon(f,latS,latN,lonL,lonR,lon_diff,debug_flag)

    combine_precs=False

    if (.not.isfilevar(f,varName)) then
       if (varName .eq. "PRECT") then
          if (isfilevar(f,"PRECC").and.isfilevar(f,"PRECL")) then
             combine_precs=True
             debug_print("getVarSlice: PRECT is being computed from PRECC and PRECL",routine_name,debug_flag)
          else
             debug_print("getVarSlice: PRECT,PRECC, and/or PRECL are not variables in file "+fili(0),routine_name,debug_flag)
          end if
       else
          print("getVarSlice: "+varName+" is not a variable in file "+fili(0))
          exit
       end if
    end if
    if (combine_precs) then
       rank = dimsizes( filevardimsizes(f,"PRECC") )
    else
       rank = dimsizes( filevardimsizes(f,varName) )
    end if 

    if (rank.ne.3) then
        print("getVarSlice: only 3D supported: rank="+rank+"D. 3D data should have been supplied by the MDTF preprocessor.")
        exit
    end if

; The following tmpx variables are a workaround for a bug in the stride
; argument when using addfiles.

    if (nfil.eq.1) then                    ; SINGLE FILE    
       if (rank.eq.3) then
           if (combine_precs) then
              tmpp  = f->PRECC(i1:i2,{latS:latN},{lonL:lonR})
              precc  = tmpp(::tstride,:,:)
              tmpp  = f->PRECL(i1:i2,{latS:latN},{lonL:lonR})
              precl  = tmpp(::tstride,:,:)
              x  = precc
              x  = (/precc+precl/)
              delete(tmpp)
              delete(precc)
              delete(precl)
           else
;TRMM             tmpx  = f->$varName$(i1:i2,{lonL:lonR},{latS:latN})
;This is really slow, and since I've disabled non-one tsride, I'm taking it out
;             tmpx  = f->$varName$(i1:i2,{latS:latN},{lonL:lonR})
;             x  = tmpx(::tstride,:,:)
;             delete(tmpx)
;save
             x  = f->$varName$(i1:i2,{latS:latN},{lonL:lonR})
             x@name = "PRECT"  ;try to get same contour ints
           end if
       end if
    else      ; multiple files
         debug_print("getVarSlice multipled files",routine_name,debug_flag)
                             ; MULTIPLE FILES
       if (combine_precs) then
          dNam   = getfilevardims(f,"PRECC")
       else
          dNam   = getfilevardims(f,varName)
       end if
 
       setfileoption("nc","SuppressClose",False)
 
       flist  = addfiles( fili, "r")
                                              ; make TIME  [tedious]
;
;       TIME           = flist[:]->$dNam(0)$(::tstride)   ; values
       tmpt            = flist[:]->$dNam(0)$(i1:i2)
       TIME           = tmpt(::tstride)
       delete(tmpt)
       if (isfilevaratt(flist[0],  dNam(0) ,  "units") ) then  
           TIME@units = flist[0]->$dNam(0)$@units   ; assign units attribute
       end if
       if (isfilevarcoord( flist[0], dNam(0), dNam(0) ) ) then
           TIME!0     = dNam(0)          ; name the dimension
           TIME&$dNam(0)$ = TIME         ; assign values [coord]
       end if

       if (rank.eq.3) then
         debug_print("getVarSlice rank.eq.3",routine_name,debug_flag)
          if (combine_precs) then
             tmpp   = flist[:]->PRECC(i1:i2,{latS:latN},{lonL:lonR})
             precc   = tmpp(::tstride,:,:)
             tmpp   = flist[:]->PRECL(i1:i2,{latS:latN},{lonL:lonR})
             precl   = tmpp(::tstride,:,:)
             x  = precc
             x  = (/precc+precl/)
             delete(tmpp)
             delete(precc)
             delete(precl)
          else
             tmpx   = flist[:]->$varName$(i1:i2,{latS:latN},{lonL:lonR})
             x   = tmpx(::tstride,:,:)
             delete(tmpx)
          end if
 
          x!0 = dNam(0)
          x!1 = dNam(1)
          x!2 = dNam(2)
 
       end if

    ; NOT required but create meta data
       dNamx  = getvardims(x)            
     
       x&$dNamx(0)$ = TIME      ; assign coordinates
       x&$dNamx(1)$ = flist[0]->$dNamx(1)$({latS:latN})
       x&$dNamx(2)$ = flist[0]->$dNamx(2)$({lonL:lonR})
       if (isfilevaratt( flist[0], varName, "long_name")) then
           if (combine_precs) then
              x@long_name = "total precipitation"
           else
              x@long_name = flist[0]->$varName$@long_name
           end if
       end if
       if (isfilevaratt( flist[0], varName, "units"    )) then  
           if (combine_precs) then
              x@units = flist[0]->PRECC@units
           else
              x@units = flist[0]->$varName$@units
          end if     
       end if     
    end if

;replace with  check_missing_values function
    if (isatt(x,"_FillValue")) then
       nMsg = num(ismissing(x))
       if (nMsg.gt.0) then
         nvals = num(x)
         npcnt = nMsg/nvals
         print("WARNING: missing values found, their replacement functions ")
         print("         do not provide great results.")
         debug_flag_save = debug_flag
         debug_flag = True
         debug_print("Processing to fill missing values in with field average",routine_name,debug_flag)
         debug_print("found   "+nMsg+" missing values ("+npcnt+"% of "+nvals+" total values )",routine_name,debug_flag)
         x@name = varName
         replace_missing_values(x,debug_flag ) 
         nMsg = num(ismissing(x))
         debug_print("UPDATE: "+nMsg+" missing values ("+npcnt+"% of "+nvals+" total values )",routine_name,debug_flag)         
         debug_flag = debug_flag_save
       end if
       delete(x@_FillValue)     ; avoid warning messages from fft
   end if

   debug_print("lon_diff L325 "+lon_diff,routine_name,debug_flag)
   if ( lon_diff .gt. 0 ) then

    ; x(lon=-180:180) y(lon=0,360)
    y = x
    copy_VarMeta(x,y)

     min_lon_x = min(x&lon)
     max_lon_x = max(x&lon)
     debug_print("OLD lon "+min(x&lon)+" "+max(x&lon),routine_name,debug_flag)
     debug_print("Lon limits old "+lonL+" "+lonR,routine_name,debug_flag)
     lonL = lonL + lon_diff  ; sent back as they came in
     lonR = lonR + lon_diff
     debug_print("Lon limits new "+lonL+" "+lonR,routine_name,debug_flag)
; DRB replace with n/2-1 and such

     nlon = dimsizes(x&lon)
     nlon_m1 = nlon - 1
     nlon_div2 = nlon / 2
     nlon_div2_p1 = nlon_div2 + 1
     nlon_div2_m1 = nlon_div2 - 1
     debug_print("Swapping lon regions ind 0:"+nlon_div2_m1+" with "+nlon_div2+":"+nlon_m1,routine_name,debug_flag)

     if ( False ) then 
       print("first assignment ")
       printVarSummary(y(:,:,:nlon_div2_m1))
       printVarSummary(x(:,:,nlon_div2:))
       print("second assignment ")
       printVarSummary(y(:,:,nlon_div2:))
       printVarSummary(x(:,:,0:nlon_div2_m1))
     end if
     y(:,:,:nlon_div2_m1) = x(:,:,nlon_div2:)
     y(:,:,nlon_div2:) = x(:,:,0:nlon_div2_m1)
;works     y(:,:,0:179) = x(:,:,180:359)
;works     y(:,:,180:359) = x(:,:,0:179)

     debug_print("NEW1 lon "+min(y&lon)+" "+max(y&lon),routine_name,debug_flag)
     y&lon = x&lon +lon_diff  ; add on what was missing

     debug_print("NEW2 lon "+min(y&lon)+" "+max(y&lon),routine_name,debug_flag)

    map_flag = False
    one_plot(x(5,:,:),"lon_before",map_flag,debug_flag)
    one_plot(y(5,:,:),"lon_after",map_flag,debug_flag)
    map_flag = True
    one_plot(x(5,:,:),"lon_before",map_flag,debug_flag)
    one_plot(y(5,:,:),"lon_after",map_flag,debug_flag)
;             x  = f->$varName$(i1:i2,{latS:latN},{lonL:lonR})
;       if (rank.eq.3) then
;             tmpp   = flist[:]->PRECC(i1:i2,{latS:latN},{lonL:lonR})    

    delete(x)
    x = y

   end if ;change lon flag


   return(x)

end
