; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"    
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"    
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/diagnostics_cam.ncl"    

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

  
;******************** MAIN **********************************
begin
routine_name = "mjo_lat_lat_lon.ncl"
vars = (/"pr","u850"/)
casename = getenv("CASENAME")

file_dir = getenv("WK_DIR")+"/model/netCDF/"
filename_pr = file_dir+casename+".pr.day.anom.nc"
filename_u850 = file_dir+casename+".u850.day.anom.nc"

nameSeason = (/"winter","summer","annual"/)


                           ; Must include period of mutual overlap
;  twStrt = 19961001        ; include enough temporal buffer for filter
;  twLast = 20051231        ; at least 100 days on each side of season

 ;cwStrt = 20001101        ; correlation window for specified season 
 ;cwLast = 20010531       

;  pName  = "data"          ; name of variable on precipitation file
;  dirp   = "/Users/shea/Data/AMWG/"
;  filp   = "pregpcp19962008.daily.nc"     ; last date w data 20080430

;  uName  = "U_anom"        ; name of variable on U-anomaly file
;  diru   = "/Users/shea/Data/AMWG/"
;  filu   = "uwnd.day.850.anomalies.1980-12005.nc"

;  nameSeason = (/ "winter", "summer", "annual" /)

  nameRegion = "IO"        ; Indian Ocean base region
  latS_IO    = -10.
  latN_IO    =   5. 
  lonL_IO    =  75.
  lonR_IO    = 100. 

  latS_globe = -30.        ; global subset  [Fig 6]
  latN_globe =  30. 

  latn       =  10.        ; lat band for (lag,lon) Fig 5
  lats       = -10.

  lonl       =  80.        ; lon band for (lag,lat) Fig 6
  lonr       = 100.

  pltName    = casename+".MJO.lag.lat.lon"       ; output plot name         
  pltType    = "ps"       ; x11, ps, eps, pdf, png 
  pltDir     = getenv("WK_DIR")+"/model/PS/"       ; output plot directory

;************************************************
; create Lanczos BandPass Filter
;************************************************
  ihp    = 2                          ; bpf=>band pass filter
  nWgt   = 201
  sigma  = 1.0                        ; Lanczos sigma
  fca    = 1./100.                    ; MJO clivar
  fcb    = 1./20.
  wgt    = filwgts_lanczos (nWgt, ihp, fca, fcb, sigma )

;************************************************************
; PRECIPITATION:
;     time indices corresponding to the desired time window
;     Read user specified period
;************************************************************

;  f      = addfile(dirp+filp, "r")  
  f      = addfile(filename_pr,"r")
;  date_p = cd_calendar(f->time, -2)   ; entire file
;  iStrt  = ind(date_p.eq.twStrt)      ; desired dates
;  iLast  = ind(date_p.eq.twLast)
;  delete(date_p)
                                      ; P(time,lat,lon)
;  if (getfilevartypes(f,pName) .eq. "short") then
;      P  = short2flt( f->$pName$(iStrt:iLast,{latS_globe:latN_globe},:)) 
;  else
;      P  = f->$pName$(iStrt:iLast,{latS_globe:latN_globe},:) 
;  end if

  pr = f->$vars(0)$(:,{latS_globe:latN_globe},:) 

;  printVarSummary( pr )
;  printMinMax(pr, True)

  time_pr = pr&time                     ; clarity
  date_pr = cd_calendar(time_pr, -2 )   ; yyyymmdd
  
  wypr   = f->lat({latS_IO:latN_IO})  
  wypr   = cos(0.017459*wypr)         ; spatial wgt

  t_utc = cd_calendar(time_pr,2)
  twStrt = min(t_utc(:))
  twLast = max(t_utc(:))
  
;************************************************************
; U 850 ANOMALIES:
;     time indices corresponding to the desired time window
;     Read user specified period
;************************************************************

;  f      = addfile(diru+filu, "r")  
  f      = addfile(filename_u850,"r")
;  date_u2 = cd_calendar(f->time, -2)     ; entire file
;  iStrt  = ind(date_u.eq.twStrt)        ; desired dates
;  iLast  = ind(date_u.eq.twLast)
;  delete(date_u)
                                        ; U(time,lat,lon)
;  if (getfilevartypes(f,uName) .eq. "short") then
;      U  = short2flt( f->$uName$(iStrt:iLast,{latS_globe:latN_globe},:)) 
;  else
;      U  = f->$uName$(iStrt:iLast,{latS_globe:latN_globe},:) 
;  end if

  u850 = f->$vars(1)$(:,{latS_globe:latN_globe},:) 

;  printVarSummary( u850 )
;  printMinMax(u850, True)

  time_u850 = u850&time                     ; clarity
  date_u850 = cd_calendar(time_u850 , -2 )  ; yyyymmdd

  wyu850    = f->lat({latS_IO:latN_IO})
  wyu850   = cos(0.017459*wyu850)          ; MJO Clivar says cos(lat) wgting


;************************************************
; make sure dates agree
;************************************************

  
  if (.not.all(date_pr.eq.date_u850)) then
      print("date mismatch: exit")
      exit
  end if
  
;************************************************
; Create wgted area average of the base IO precip series  (time)
; Really, no need to area weight here .... area is very small.
;************************************************

  PIO    = wgt_areaave_Wrap(pr(:,{latS_IO:latN_IO},{lonL_IO:lonR_IO}), wypr, 1., 0)
  PIO    = dtrend (PIO, False)                                   ; rmv overall trend
  PIO    = wgt_runave_leftdim( PIO, wgt, 0 )                     ; apply filter
 
;************************************************
; Create LAT average of the global Precip and U series  (time,lon)
; Really, no need to area weight here
;************************************************

  pr_timeLon   = dim_avg_Wrap(pr( time|:,lon|:,{lat|lats:latn}) )  ; (time,lon)
  pr_timeLon   = dtrend_leftdim (pr_timeLon, False)                ; rmv overall trend
  pr_timeLon   = wgt_runave_leftdim( pr_timeLon, wgt, 0 )          ; apply filter

  u850_timeLon   = dim_avg_Wrap(u850( time|:,lon|:,{lat|lats:latn}) )  ; (time,lon)
  u850_timeLon   = dtrend_leftdim (u850_timeLon, False)                ; rmv overall trend
  u850_timeLon   = wgt_runave_leftdim( u850_timeLon, wgt, 0 )

;************************************************
; Create LON average of the global Precip and U series  (time,lat)
; Really, no need to area weight here
;************************************************

  pr_timeLat   = dim_avg_Wrap(pr( time|:,lat|:,{lon|lonl:lonr}) )  ; (time,lat)
  pr_timeLat   = dtrend_leftdim (pr_timeLat, False)                ; rmv overall trend
  pr_timeLat   = wgt_runave_leftdim( pr_timeLat, wgt, 0 )          ; apply filter

  u850_timeLat   = dim_avg_Wrap(u850( time|:,lat|:,{lon|lonl:lonr}) )  ; (time,lat)
  u850_timeLat   = dtrend_leftdim (u850_timeLat, False)                ; rmv overall trend
  u850_timeLat   = wgt_runave_leftdim( u850_timeLat, wgt, 0 )

;*************************************************************************
; Calculate/Plot the mean seasonal cross-correlations at +/- 'mxlag' lags
;*************************************************************************
  optXcor   = False
  mxlag     = 25
  nSeason   = dimsizes(nameSeason)

  optPlot                  = True
  optPlot@gsnLeftString    = "precip (color)"    
  optPlot@gsnRightString   = "U (lines)"  
  optPlot@smth9            = 0.25                ; local spatial smoothing

  timePeriod               =  twStrt+"-"+twLast  ; panel title 
  
  do ns=0,nSeason-1                              ; loop over each season
     rpr_timelon = mjo_xcor_lag (PIO, pr_timeLon, date_pr, mxlag, nameSeason(ns), optXcor)
     ru850_timelon = mjo_xcor_lag (PIO, u850_timeLon, date_u850, mxlag, nameSeason(ns), optXcor)
     
     rpr_timelat = mjo_xcor_lag (PIO, pr_timeLat, date_pr, mxlag, nameSeason(ns), optXcor)
     ru850_timelat = mjo_xcor_lag (PIO, u850_timeLat, date_u850, mxlag, nameSeason(ns), optXcor)

     optPlot@txString      = nameSeason(ns)+": "+timePeriod
     pltNameSeason = pltName+"."+nameSeason(ns)
     mjo_xcor_lag_ovly_panel(rpr_timelon, ru850_timelon, rpr_timelat, ru850_timelat \
                            ,pltType, pltDir, pltNameSeason, optPlot)

     print(routine_name+" wrote "+pltDir+"/"+pltNameSeason+"."+pltType) ;lag.lat.lon.summer.ps
                            
  end do
end
