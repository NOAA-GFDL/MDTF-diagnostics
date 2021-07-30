; This file is part of the Wheeler_Kiladis module of the MDTF code package (see LICENSE.txt)
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/diagnostics_cam.ncl"
load "$POD_HOME/getVarSlice.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

;==================================================================
; Function to fix contour levels according to variable name
; The variable name's used here are the CESM variables as used in diagnostics_cam.ncl
; This routine should be called by an interface that translates to them
; OLR options: "FLUT" ,"OLR", "olr"
; Zonal wind at pressure levels: "U200","U850" 
; Total precipitation "PRECT"
; Vertical velocity at 500 mb" OMEGA500"
undef("set_contours_by_varname")
procedure set_contours_by_varname(varname,opt)
begin


     nCn = 15
     routine_name = "set_contours_by_varname"
  if (varname.eq."PRECT") then
    debug_print("Fixing contour levels for "+varname+" (translated name)",routine_name,opt@debug)
    ; unequal, but that's what's in the code
    opt@Fig_1  = (/-18.2,-18.0,-17.8,-17.6,-17.5,-17.4,-17.3 \ ; unequal
                       ,-17.2,-17.1,-17.0,-16.9,-16.8,-16.7,-16.6,-16.5/)
    opt@Fig_2 = (/-18.2,-18.0,-17.8,-17.6,-17.5,-17.4,-17.3 \   
                       ,-17.2,-17.1,-17.0,-16.9,-16.8,-16.7,-16.6,-16.5/)
    opt@Fig_3a = (/0.6,0.7 ,0.8,0.9 ,1.0,1.1,1.15,1.2,1.25 \
                       ,1.3,1.35,1.4,1.45,1.5,1.6/)
    opt@Fig_3b = (/.6,.7,.8,.9,1.,1.1,1.15,1.2,1.25,1.3,1.35,1.4,1.45,1.5,1.6/)
  end if; PRECT

   if (varname .eq. "FLUT") then
    debug_print("Fixing contour levels for "+varname+" (translated name)",routine_name,opt@debug)
       opt@Fig_1  = (/-1.2,-1.1,-1.0,-0.8,-0.6,-0.4,-0.2     \ ; unequal
                       , 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.1,1.2/)
       opt@Fig_2 = (/-1.2,-1.1,-1.0,-0.8,-0.6,-0.4,-0.2 \     ; unequal 15
                       , 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.1,1.2/)
       opt@Fig_3a = fspan(0.3, 1.7, nCn)
       opt@Fig_3b = (/.3,.4,.5,.6,.7,.8,.9,1.,1.1,1.2,1.4,1.7,2.,2.4,2.8/)
   end if
   if (varname .eq. "U200") then
    debug_print("Fixing contour levels for "+varname+" (translated name)",routine_name,opt@debug)
       opt@Fig_1  = fspan(-3.3, 0.9, nCn)
       opt@Fig_2 = fspan(-3.3, 0.9, nCn)
       opt@Fig_3a = fspan(0.4, 1.8, nCn)
       opt@Fig_3b = (/.4,.6,.8,1.,1.2,1.3,1.4,1.5,1.6,1.7,1.8,2.,2.2,2.4,2.6/)
   end if
   if (varname .eq. "U850") then
    debug_print("Fixing contour levels for "+varname+" (translated name)",routine_name,opt@debug)
       opt@Fig_1  = fspan(-3.25, 0.25, nCn)
       opt@Fig_2 = fspan(-3.25, 0.25, nCn)
       opt@Fig_3a = fspan(0.4, 1.8, nCn)
       opt@Fig_3b = (/.4,.6,.8,1.,1.2,1.3,1.4,1.5,1.6,1.7,1.8,2.,2.2,2.4,2.6/)
   end if
   if (varname .eq. "OMEGA500") then
     debug_print("Fixing contour levels for "+varname+" (translated name)",routine_name,opt@debug)
       opt@Fig_1  = fspan(-5.9, -4.5, nCn)
       opt@Fig_2 = fspan(-5.9,-4.5, nCn)
       opt@Fig_3a = (/0.6,0.7,0.8,0.9,1.0,1.1,1.15,1.2,1.25 \
                       ,1.3,1.35,1.4,1.45,1.5,1.6/)
       opt@Fig_3b = (/.6,.7,.8,.9,1.,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2./)
   end if

  if (.not.isatt(opt,"Fig_1")) then
    debug_print("WARNING: set_contours_by_varname called but varname "+varname+" not found",routine_name,opt@debug)
  else
    if (isatt(opt,"debug")) then
      if (opt@debug) then
        debug_print("Contour levels set by (translated) varname "+varname,routine_name,opt@debug)
;        print("  Fig 1  = "+opt@Fig_1)
;        print("  Fig 2  = "+opt@Fig_2)
;        print("  Fig 3a = "+opt@Fig_3a)
;        print("  Fig 3b = "+opt@Fig_3b)
      end if ;opt@debug
    end if   ;isatt(opt@debug)
  end if ; (.not.isatt(opt,"Fig_1") then

end  ;procedure set_contours_by_varname


;==================================================================
;                     USER INTERFACE 
;                   MAIN DRIVER SCRIPT
;==================================================================
begin
;-------------------------------------------------------------------
; Get Info from Environment variables
;-------------------------------------------------------------------
  
  
  debug = False     ;ideally this gets set for verbose >1 from mdtf 
  routine_name = "wkSpaceTime_driver.ncl"
  debug_print("Started ",routine_name,debug)

  diri = getenv("DATADIR")+"/day/"
  case = getenv("CASENAME")
  varName = getenv("MVAR")
  print("varName:" +varName)
  print("diri:" +diri)
  print("case:" +case)

  latBound = 15
;  latBound = stringtointeger(getenv("LATBND"))

  diro     = getenv("WK_DIR")+"/model/PS/"     ; output dir: location of plots
  print ("writing to "+diro)
;-------------------------------------------------------------------
; spectral input params for wkSpaceTime
;-------------------------------------------------------------------

  nDayWin  = 96      ; Wheeler-Kiladis [WK] temporal window length (days)
  nDaySkip = -65     ; time (days) between temporal windows [segments]

;-------------------------------------------------------------------
; Plotting Options for wkSpaceTime
;-------------------------------------------------------------------
; DRB: move this up to the interface level (maybe... all going to be
; replaced by python anyway?)

  fix_clevs = True
  if (.not.isvar("opt"))then
    opt = True
  end if
  if ( debug ) then
    opt@debug= True
  else
    opt@debug= False
  end if

  if ( fix_clevs ) then
    if (.not.isvar("opt"))then
      opt = True
    end if

    debug_print("DEBUG: wk comparing varname "+varName+" to "+ \
       getenv("pr_var") +" "+\
       getenv("rlut_var") +" "+\
       getenv("u200_var") +" "+\
       getenv("u850_var") +" "+\
       getenv("omega500_var"),\
       routine_name,\
       debug)

    if (varName.eq.getenv("pr_var")) then
      set_contours_by_varname("PRECT",opt)
    end if
    if (varName.eq.getenv("rlut_var")) then
      set_contours_by_varname("FLUT",opt)
    end if
    if (varName.eq.getenv("u200_var")) then
      set_contours_by_varname("U200",opt)
    end if
    if (varName.eq.getenv("u850_var")) then
      set_contours_by_varname("U850",opt)
    end if
    if (varName.eq.getenv("omega500_var")) then
      set_contours_by_varname("OMEGA500",opt)
    end if
  end if ; fix_clevs

  if ( debug ) then
    opt@debug = True
  end if

;-------------------------------------------------------------------
; Get subset (time,level, lat, or lon) of variable
;-------------------------------------------------------------------

  lonL    = 0.        ; -180
  lonR    = 360.      ;  180
  level    = -999    ; only used for 4D set -999 otherwise]

; Read in files from file list created by script

  fili = getenv("file_WK")

  latN    = latBound
  latS    =-latBound ; make symmetric about the equator

  yr1 = stringtointeger(getenv("FIRSTYR"))
  yr2 = stringtointeger(getenv("LASTYR"))
  f=addfile(fili,"r")

  ; DRB: should move all the time/calendar stuff to a function
  time_coord = getenv("time_coord")
  time = f->$time_coord$
  
  if ( time@units.eq."julian day") then  ; set so cd_calendar can convert it
    time@units = "days since -4713-01-01 00:00:00" ;
    time@calendar = "julian"
  end if ; time@units julian

  ; Overkill but different parts of the code use each of these
  time_array = cd_calendar(time,0) ; separated YYYY,MM,DD,HH dims
  time_all = cd_calendar(time,-3)  ; YYYYMMDDHH
  
  i1 = 0
  nd = dimsizes(time_array)
  i2 = nd(0) - 1
  debug_print("Time range in file: "+time_all(0)+" - "+time_all(i2),routine_name,debug)

;  print("Time range in file: "+time_array(0,:)+" - "+time_array(i2,:))

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
;  print("Time range indices: "+i1+" "+time_all(i1)+" - "+i2+" "+time_all(i2))
;  print("Time range indices: "+i1+" "+time_array(i1,:)+" - "+i2+" "+time_array(i2,:))

  spd = calculate_samples_per_day(time_array,debug)    ; samples per day
  tstride = 1  ; Use all indices
  x=getVarSlice( fili, varName, level, latS, latN, lonL, lonR, tstride, i1, i2,debug)

  if (typeof(x).eq."short") then
    debug_print ("Converting short to float",routine_name,debug)
    y = short2flt(x)
    delete(x)
    x = y
    delete(y)
  end if
;-------------------------------------------------------------------
; make sure that "x" has full days of data and update spd to reflect
; any user specified stride for time
;-------------------------------------------------------------------
  dsizes_x = dimsizes(x)
  ntim     = dsizes_x(0)

 
  if ((ntim%spd).eq.0) then
     y = x
   else  ; cut off extra time-samples
     nExtra = ntim%new_spd
     debug_print("Cutting off extra time samples ( ntim "+ntim+" % spd "+spd+" = "+nExtra+")",routine_name,debug)
     NTIM = ntim - nExtra
     y = x(:NTIM-1,:,:)
   end if


; Dimensions and sizes:   [time | 1187] x [lat | 30] x [lon | 360]
;save   one_plot(y(0,:,:),case,True,debug)
   ts_plot(y,"into_wkspacetime",debug)
   ; Analysis and (unfortunately) figures
   wkSpaceTime (y, diro, case, varName,latBound, \
                spd, nDayWin, nDaySkip, opt) 

   print("Completed Wheeler-Kiladis Code")


end
