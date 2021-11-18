; This file is part of the MJO_teleconnection module of the MDTF code package (see LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"    
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"    
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/diagnostics_cam.ncl"    
   
setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

;++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
;This scripts calculates wave frequeency specra fo a given models precipitation
;Written by : Sptephnaie Handerson
;Edited By Bohar Singh Atomospheric science CSU Fort Collins
; Module MJO Teleconnection diagnostic MDTF 
;++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
begin

  Model = getenv("CASENAME")
  latS   = -10.
  latN   =  10.
print("----------------------------------------------------------------------------------")
print("** Calculating Ratio of the eastward and westward moving power of precipitation ** ")
print("----------------------------------------------------------------------------------")

   ratio_wf = new((/dimsizes(Model)/),"float")
   east_pw = new((/dimsizes(Model)/),"float")  ;east power (in case I want it later)

   print("Dataset: " + Model)
;---------------------------------------------------------------------------------
   ymdStrt = tointeger(getenv("strtdy"))                         ; start yyyymmdd
   ymdLast = tointeger(getenv("lastdy")) 
   yrStrt  = ymdStrt/10000
   yrLast  = ymdLast/10000


;---------------------------------------------------------------------------------
;                           Reading input data in 
;---------------------------------------------------------------------------------
  print("Reading daily precipitation data") 
  pName     = getenv("pr_var")           ; mm/day
  dirobs    = getenv("OBS_DATA")+"/"
  diro      = getenv("WK_DIR")+"/model/netCDF/"
  filp      = getenv("prec_file")    
  filewcmip ="EWratio_wf_CMIP5"
     print("Input data file observation geop composite :" + filp)
   
     print("Input data path (Observations EWR) :" + dirobs)
     print("Input data file CMIP5 models EWR :"   + filewcmip)


print("Done")
print("----------------------------------------------------------------------------------")
;************************************************************
; PRECIPITATION:
;     time indices corresponding to the desired time window
;     Read user specified period
;************************************************************

  f  = addfile(filp, "r")  
  temp_time = f->time
  
   calend = temp_time@calendar
   ymd     = cd_calendar(temp_time, -2)            ; yyyymmdd

    iStrt   = ind(ymd.eq.ymdStrt)              ; index start
    iLast   = ind(ymd.eq.ymdLast)              ; index last 

  date_p = cd_calendar(f->time(iStrt:iLast), -2)   ; entire file
  lon = f->lon
                                     
  if (getfilevartypes(f,pName) .eq. "short") then
      P  = short2flt( f->$pName$(iStrt:iLast,{latS:latN},:)) 
  else
      P  = f->$pName$(iStrt:iLast,{latS:latN},:) 
  end if
  
; if(m .gt. 0)
    print("convert kg m-2 s-1 flux to mm/day rate")
    P = P * 86400.0
; end if

   P@_FillValue = -999.0  

  delete(date_p)
  time_p = P&time                     ; clarity
  date_p = cd_calendar(time_p, -2 )   ; yyyymmdd
  lat = f->lat({latS:latN})

;-- remove seasonal cycle --
print("removing  seasonal cycle")

   P!0 = "time_p"
   P!1 = "lat"
   P!2 = "lon"
   P@_FillValue=-999.0

   yyyyddd  = yyyymmdd_to_yyyyddd(date_p)
   ;yyyymmdd_to_yyyyddd is deprecated but unsure why this workaround doesn't work
   ;yyyyddd_double = cd_calendar(time_p, 4)
   ;yyyy = floor(yyyyddd_double)
   ;ddd = floor(365.0*(yyyyddd_double - yyyy)) + 1.0 ; runs from 1 to 365
   ;yyyyddd = toint(1000.0*yyyy + ddd)
   if (isatt(time_p,"calendar")) then           ; default is gregorian
      yyyyddd@calendar = time_p@calendar  
   end if
   print("CALENDAR DEBUG")
   printMinMax(yyyyddd, 0)

;calculate raw climatology then smooth it
print("calculating raw and  smooth climatology ....")
   print("DEBUG: "+num(ismissing(P))+" missing vals in pr")
   rawclim = clmDayTLL(P,yyyyddd)
   print("DEBUG: "+num(ismissing(rawclim))+" missing vals in rawclim")
   printVarSummary(P)
   printVarSummary(rawclim)
   smoothclim = smthClmDayTLL(rawclim,2)
   print("DEBUG: "+num(ismissing(smoothclim))+" missing vals in smoothclim")

   P_anom = calcDayAnomTLL(P,yyyyddd,smoothclim)
   P_anom@_FillValue=-999

   delete(P)
   P = P_anom
   delete(P_anom)
   delete(rawclim)
   delete(smoothclim)
   delete(yyyyddd)

;  printVarSummary( P )
;   printMinMax(P, True)

print("Done")
print("----------------------------------------------------------------------------------")
;************************************************************
; MJO Clivar says to average the data over latitude and
; use the averaged to compute spectra. 
; No areal weighting  for -10 to 10
;************************************************************

  x1 = dim_avg_n_Wrap( P, 1 )                   ; (time,lon) ; v5.1.1 onward
  x  =  tofloat(x1)  
  delete(P)
  delete(x1)

   x!0 = "time_p"
   x!1 = "lon"
   x@_FillValue=-999
;printVarSummary(x)
;************************************************************
; calculate and plot the OLR spectra
;************************************************************
  pltDir = "./"
  pltType    = "eps"       ; x11, ps, eps, pdf, png
  pltName    = "mjo_wvn_freq_" + Model       ; output plot name
  
  optWavFrq     = True
  optWavFrq@dayLines = (/30,60/)

  optPlot       = True
  optPlot@maxWavePlot = 8
  optPlot@gsnLeftString    = Model    
  optPlot@cnLevelSelectionMode  = "ManualLevels" ; set manual contour levels
  optPlot@cnMinLevelValF        = 0.004       ; set min contour level
  optPlot@cnMaxLevelValF        = 0.044
  optPlot@cnLevelSpacingF       = 0.004  ; set contour interval

  optPlot@cnLinesOn    = False

  nameSeason = (/"winter"/)
  
  do ns=0,dimsizes(nameSeason)-1
     wf      = mjo_wavenum_freq_season (x, date_p,nameSeason(ns), optWavFrq)    ; (wavenumber,frequency)
     ;optPlot@tiMainString = nameSeason(ns)+": "+twStrt+"-"+twLast
     mjo_wavenum_freq_season_plot (wf, nameSeason(ns), pltDir, pltType, pltName, optPlot) 
  end do



;  printVarSummary(wf)

;nDay = 180
;freq      = fspan(-1*nDay/2,nDay/2,nDay+1)/nDay
;print(freq)


 min_wvn = 1
 max_wvn = 3
 min_freq = 1./60.   ;0.016
 max_freq = 1./30.   ;0.033
 min_fre = max_freq * -1.
 max_fre = min_freq * -1.

;-- isolate region for average --
;3 wavenumbers, 4 frequencies

east_wf = wf({min_wvn:max_wvn},{min_freq:max_freq})  ;eastward power
west_wf = wf({min_wvn:max_wvn},{min_fre:max_fre})  ;westward power

east_pw = sum(east_wf)
ratio_wf = sum(east_wf)/sum(west_wf)

print(Model + ":(Eastward power/Westward power) and Eastward power:  ")
print("E/W: " + ratio_wf + "    east power: " + sum(east_wf))

delete(x)
delete(time_p)
delete(date_p)
delete(wf)
delete(optPlot)
delete(optWavFrq)
delete(east_wf)
delete(west_wf)

print("----------------------------------------------------------------------------------")
print("Reading E/W ratio  data for CMIP5 Models")
;-- read in zonal wind RMS error data --
   
   EWR = asciiread(dirobs+filewcmip,(/-1/),"float") ;precip corr (9 models)
;   print(EWR)

;Adding New model RMSE values to CMIP5 RMSE array

print("Adding New model E/W ratio  values to CMIP5 E/W ratio array")

   EWRnew = new((/dimsizes(EWR)+1/),typeof(EWR))

   EWRnew(0:10) = EWR
   EWRnew(11)  = ratio_wf
;   print(EWRnew)
 
;output E/W ratio
asciiwrite (diro + "EWratio_wf_CMIP5_updated" , EWRnew)

print("Ascii file for E/W ratio is updated with new model's precip E/W ratio values")
print("Now saved at: " +diro+ "EWratio_wf_CMIP5_updated")
print("Process of E/W ratio calculation is completed now")
print("----------------------------------------------------------------------------------")
print("----------------------------------------------------------------------------------")

end





