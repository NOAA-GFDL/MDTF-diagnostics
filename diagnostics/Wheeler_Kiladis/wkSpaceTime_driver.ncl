; This file is part of the Wheeler_Kiladis module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/diagnostics_cam.ncl"
load "$POD_HOME/getVarSlice.ncl"

;==================================================================
;                     USER INTERFACE 
;                   MAIN DRIVER SCRIPT
;==================================================================
begin
;-------------------------------------------------------------------
; Get Info from Environment variables
;-------------------------------------------------------------------

print("In wkSpaceTime_driver")
  diri = getenv("DATADIR")+"/day/"
  case = getenv("CASENAME")
  varName = getenv("MVAR")
  print("varName:" +varName)
  print("diri:" +diri)
  print("case:" +case)
;  spd = 4
;  spd = stringtointeger(getenv("SPD"))
  latBound = 15
;  latBound = stringtointeger(getenv("LATBND"))
  tstride = 1
;  tstride = stringtointeger(getenv("TSTRIDE"))
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

  opt      = True
  opt@debug= True
 ;opt@pltType = "eps"
 ;opt@pltColorMap = "amwg"

;-------------------------------------------------------------------
; Get subset (time,level, lat, or lon) of variable
;-------------------------------------------------------------------

  lonL    = 0        ; -180
  lonR    = 360      ;  180
  level    = -999    ; only used for 4D [set -999 otherwise]

; Read in files from file list created by script

  fili = diri+getenv("file_WK")

  latN    = latBound
  latS    =-latBound ; make symmetric about the equator

  yr1 = stringtointeger(getenv("FIRSTYR"))
  yr2 = stringtointeger(getenv("LASTYR"))
  f=addfile(fili,"r")
  time_coord = getenv("time_coord")
  time = f->$time_coord$
  time_all = cd_calendar(f->$time_coord$,-3)
  i1 = 0
  i2 = dimsizes(time_all)-1
  start_time = yr1*1000000+101*100
  end_time = yr2*1000000+1231*100+18
  do i=0,dimsizes(time_all)-1
     if( time_all(i).eq.start_time )then
        i1 = i
     end if
     if( time_all(i).eq.end_time )then
        i2 = i
     end if
  end do 
  delete(f)

  spd = tointeger(1.0/(time(1)-time(0)))

; get subset of variable

  x=getVarSlice( fili, varName, level, latS, latN, lonL, lonR, tstride, i1, i2)

  if(varName.eq.getenv("pr_var")) then
    conversion_factor = tofloat(getenv("pr_conversion_factor"))
    x = x*conversion_factor*0.001
  end if
;-------------------------------------------------------------------
; make sure that "x" has full days of data and update spd to reflect
; any user specified stride for time
;-------------------------------------------------------------------
  dsizes_x = dimsizes(x)
  ntim     = dsizes_x(0)

  new_spd   = spd/tstride ; SPD *actual* "samples per day" 

  if ((ntim%new_spd).eq.0) then
     wkSpaceTime (x, diro, case, varName,latBound, \
                  new_spd, nDayWin, nDaySkip, opt  )
  else
     nExtra = ntim%new_spd
     NTIM = ntim - nExtra
     wkSpaceTime (x(:NTIM-1,:,:), diro, case, varName,latBound, \
                  new_spd, nDayWin, nDaySkip, opt  )
  end if

end
