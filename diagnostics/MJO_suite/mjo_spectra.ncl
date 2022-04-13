; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"    
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"    
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/diagnostics_cam.ncl"    
load "$POD_HOME/my_cam_diags.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

;++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
begin
routine_name = "mjo_spectra.ncl"
vars = (/"pr","rlut","u200","u850","v200","v850"/)

casename = getenv("CASENAME")

file_dir = getenv("WK_DIR")+"/model/netCDF/"
filename_pr = file_dir+casename+".pr.day.anom.nc"
filename_rlut = file_dir+casename+".rlut.day.anom.nc"
filename_u200 = file_dir+casename+".u200.day.anom.nc"
filename_u850 = file_dir+casename+".u850.day.anom.nc"
filename_v200 = file_dir+casename+".v200.day.anom.nc"
filename_v850 = file_dir+casename+".v850.day.anom.nc"

  nameSeason = (/"winter" , "summer"/)

;  twStrt = 19800101        
;  twLast = 20051231

  latS   = -10.
  latN   =  10.

;  diri   = "/Users/shea/Data/AMWG/"

  vName  = "U_anom"        ; name of variable on the file
;  fili   = "uwnd.day.850.anomalies.1980-2005.nc"
;  f      = addfile(diri+fili, "r")  

  pltDir  = getenv("WK_DIR")+"/model/PS"
  pltType = "ps"
  

file_list = (/filename_pr,filename_rlut,filename_u200,filename_u850,filename_v200,filename_v850/)
f = addfiles(file_list,"r")

plot = new(1,graphic)
dum = new((/1,3/),graphic)

pan = True
pan@gsnMaximize = True
pan@gsnPanelLabelBar    = True 
pan@gsnPanelFigureStrings = casename
pan@amJust = "TopLeft"
pan@gsnPanelFigureStringsFontHeightF = 0.015

pan@lbOrientation = "Horizontal"
pan@lbTitlePosition = "Top"
pan@lbTitleFontHeightF = "0.01"
pan@lbLabelFontHeightF = 0.01
pan@pmLabelBarWidthF      = 0.5               
pan@pmLabelBarHeightF     = 0.12              

resp                  = True                      ; polyline mods desired
resp@gsLineThicknessF = 2.0                       ; thickness of lines
resp@gsLineDashPattern= 11


do ivars = 0,dimsizes(vars)-1

 pltName = casename+".MJO.wave.freq."+vars(ivars)
 

;************************************************************
; time indices corresponding to the desired time window
;************************************************************

  date  = cd_calendar(f[ivars]->time, -2)   ; entire file
  twStrt = min(date)
  twLast = max(date)
;  iStrt = ind(date.eq.twStrt)        ; desired dates
;  iLast = ind(date.eq.twLast)
  delete(date)

;************************************************************
; Read user specified period
;************************************************************

;  if (getfilevartypes(f,vName) .eq. "short") then
;      X = short2flt( f->$vName$(iStrt:iLast,{latS:latN},:) ) ; all data in window
;  else
;      X = f->$vName$(iStrt:iLast,{latS:latN},:) 
;  end if
  X = f[ivars]->$vars(ivars)$(:,{latS:latN},:)
;  printVarSummary( X )
;  printMinMax(X, True)

  time  = X&time                     ; clarity
  date  = cd_calendar( time , -2 )   ; yyyymmdd

;************************************************************
; MJO Clivar says to average the data over latitude and
; use the averaged to compute spectra,. Technically, not correct.
; No areal weighting  for -10 to 10
;************************************************************

  x = dim_avg_Wrap( X(time|:,lon|:,lat|:) )    ; (time,lon)
  
;************************************************************
; calculate and plot the spectra
;************************************************************
  optWavFrq     = False
  optPlot       = True
  optPlot@cnLinesOn    = False
;  optPlot@smth9 = False
 ;optPlot@debug = True

  res       = True
  res@cnLinesOn    = True

  if( vars(ivars).eq."pr" ) 
   res@cnLevelSelectionMode  = "ExplicitLevels"
   res@cnLevels              = 0.1*(/0.04,0.08,0.12,0.16,0.2,0.24,0.28,0.32,0.36,0.4,0.44,0.48/)
   vunits = "(mm/day)"
  end if  
  if( vars(ivars).eq."u850" )
   res@cnLevelSelectionMode  = "ExplicitLevels"
   res@cnLevels              = 0.1*(/0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0/)
   vunits = "(m/s)"
  end if
  if( vars(ivars).eq."v850" )
   res@cnLevelSelectionMode  = "ExplicitLevels"
   res@cnLevels              = 0.001*(/0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.25,2.5,2.75,3.0,3.25,3.5,3.75,4.0/)
    vunits = "(m/s)"
  end if
  if( vars(ivars).eq."u200" )
   res@cnLevelSelectionMode  = "ExplicitLevels"
   res@cnLevels              = 0.01*(/4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68/)
   vunits = "(m/s)"
  end if
  if( vars(ivars).eq."v200" )
   res@cnLevelSelectionMode  = "ExplicitLevels"
   res@cnLevels              = 0.001*(/4,8,12,16,20,24,28,32,36,40,48/)
    vunits = "(m/s)"
  end if
  if( vars(ivars).eq."rlut" )
   res@cnLevelSelectionMode  = "ExplicitLevels"
   res@cnLevels              = 10.*(/0.02,0.04,0.06,0.08,0.1,0.12,0.14,0.16,0.18,0.2,0.22,0.24,0.26/)
   vunits = "(W/m~S~2~N~)"
  end if

  pan@lbTitleString = vunits
  res@tmXBMode   = "Explicit"
  res@tmXBValues = 1./(/-5,-10,-20,-30,-90,90,30,20,10,5/)     ; choose first 13 timesteps
  res@tmXBLabels = (/"5d","10d","20d","30d","90d","90d","30d","20d","10d","5d"/)
 
;  print (" *** Plotting ***")
  res@gsnLeftString = ""
  res@gsnRightString = ""
  res@gsnCenterString = ""

  do ns=0,dimsizes(nameSeason)-1
     wf      = mjo_wavenum_freq_season (x, date,nameSeason(ns), optWavFrq)  
     optPlot@tiMainString = nameSeason(ns)+": "+twStrt+"-"+twLast
;     mjo_wavenum_freq_season_plot (wf, nameSeason(ns), pltDir, pltType, pltName, optPlot) 
     wks = gsn_open_wks(pltType, pltDir+"/"+pltName+"."+nameSeason(ns)) 
     
     mjo_wavenum_freq_season_plot_panel (wf, nameSeason(ns), pltDir, pltType, pltName, res, wks, plot)
     dum(0,0)=gsn_add_polyline(wks,plot,1./(/30.,30./),(/0.,6./),resp)      
     dum(0,1)=gsn_add_polyline(wks,plot,1./(/90.,90./),(/0.,6./),resp) 
     dum(0,2)=gsn_add_polyline(wks,plot,     (/0.,0./),(/0.,6./),True) 

     pan@txString = vars(ivars)+":"+twStrt+" to "+twLast
     gsn_panel(wks,plot,(/1,1/),pan)
     
     print(routine_name+ " wrote "+ pltDir+"/"+pltName+"."+nameSeason(ns)+"."+pltType)
  end do

  delete(res@cnLevels)
end do ; vars
  
end
