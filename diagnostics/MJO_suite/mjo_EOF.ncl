; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

;***********************************************************
; Generate conventional EOFs using 20-100 day filtered data
;***********************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"  
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"  
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin
; ===========================================================
; input data
;============================================================
routine_name = "mjo_EOF.ncl"
vars = (/"pr","rlut","u200","u850","v200","v850"/)

casename = getenv("CASENAME")

file_dir = getenv("WK_DIR")+"/model/netCDF/"
filename_pr = file_dir+casename+".pr.day.anom.nc"
filename_rlut = file_dir+casename+".rlut.day.anom.nc"
filename_u200 = file_dir+casename+".u200.day.anom.nc"
filename_u850 = file_dir+casename+".u850.day.anom.nc"
filename_v200 = file_dir+casename+".v200.day.anom.nc"
filename_v850 = file_dir+casename+".v850.day.anom.nc"

seasons_name = (/"winter","summer"/)


   neof    =  4

   latS    = -30
   latN    =  30

;   ymdStrt = 19950101                         ; start yyyymmdd
;   ymdLast = 19991231                         ; last  

;   yrStrt  = ymdStrt/10000
;   yrLast  = ymdLast/10000

   pltDir  = getenv("WK_DIR")+"/model/PS/"             ; plot directory
   pltType = "ps"
;   pltName = "mjoclivar"                      ; yrStrt+"_"+yrLast
  
;   diri    = "/Users/shea/Data/AMWG/"         ; input directory   

  ;fili    = "olr.day.anomalies.1980-2005.nc"
  ;vName   = "OLR_anom"

;   plev    = 850                              ; 850 or 200 hPa
;   fili    = "uwnd.day."+plev+".anomalies.1980-2005.nc"
;   vName   = "U_anom"

;***********************************************
; calculate Guassian weight
;***********************************************
file_list = (/filename_pr,filename_rlut,filename_u200,filename_u850,filename_v200,filename_v850/)
f = addfiles(file_list,"r")

gw0 = f[0]->gw


;************************************************
; create BandPass Filter
;************************************************
  ihp      = 2                             ; bpf=>band pass filter
  nWgt     = 201
  sigma    = 1.0                           ; Lanczos sigma
  fca      = 1./100.
  fcb      = 1./20.
  wgt      = filwgts_lanczos (nWgt, ihp, fca, fcb, sigma )

;***********************************************************
; Find the indicies (subscripts) corresponding to the start/end times
;***********************************************************

;   f       = addfile (diri+fili , "r")                         
;   TIME    = f->time                          ; days since ...
;   YMD     = cd_calendar(TIME, -2)            ; entire (time,6)

;   iStrt   = ind(YMD.eq.ymdStrt)              ; index start
;   iLast   = ind(YMD.eq.ymdLast)              ; index last 
;   delete(TIME)
;   delete(YMD )


do ivars = 0,dimsizes(vars)-1
  
  vName = vars(ivars)
  print("Starting "+vName)
;***********************************************************
; Read anomalies
;***********************************************************
;   X       = f->$vName$(iStrt:iLast,{latS:latN},:) ; U_anom_sm
   X = f[ivars]->$vars(ivars)$(:,{latS:latN},:)
;   printVarSummary(X)
;   printMinMax(X, True)

;   time    = f->time(iStrt:iLast)             ; days since ...
   time    = f[ivars]->time
   t_utc = cd_calendar(time,0)

   yrStrt = min(t_utc(:,0))
   yrLast = max(t_utc(:,0))

   lon = X&lon
   lat = X&lat
   gw = gw0({latS:latN})
   mlon = dimsizes(lon)
   nlat = dimsizes(lat)

;   dimX    = dimsizes( X )
;   ntim    = dimX(0)
;   nlat    = dimX(1)
;   mlon    = dimX(2)

;************************************************
; Apply the band pass filter to the original anomalies
;************************************************
  x   = wgt_runave_Wrap (X(lat|:, lon|:, time|:), wgt, 0)

;************************************************
; remove means of band pass series: *not* necessary 
;************************************************
  x   =dim_rmvmean( x )
  
;************************************************
; two seasons, Nov to Apr & May to Oct
;************************************************
  count = new((/2/),"integer")
  count = 0
  do n=0,dimsizes(time)-1
     if( (t_utc(n,1).ge.5).and.(t_utc(n,1).le.10) ) then
     	 count(1) = count(1)+1
     else
         count(0) = count(0)+1
     end if
  end do

  time0 = new((/count(0)/),"double")
  time1 = new((/count(1)/),"double")

if ( dimsizes(time) .gt. 1000 ) then
  time_warning = dimsizes(time)+" time samples, may take a while. Check "+pltDir
else
  time_warning = " no time warning, nt "+dimsizes(time)
end if
  
do season = 0,1

pltName = casename+".MJO.EOF."+vars(ivars)+"."+seasons_name(season)
print("Computing "+vars(ivars)+", "+seasons_name(season)+". "+time_warning) 
x_season = new((/count(season),nlat,mlon/),"float")
x_season!0 = "time"
x_season!1 = "lat"
x_season!2 = "lon"
x_season&lat = lat
x_season&lon = lon

if( season.eq.0 ) then
index = 0
do n=0,dimsizes(time)-1
 if( (t_utc(n,1).le.4).or.(t_utc(n,1).ge.11) ) then
  time0(index) = time(n)
  x_season(index,:,:) = x(time|n,lat|:,lon|:)
  index = index+1
 end if
end do
x_season&time = time0
else
index = 0
do n=0,dimsizes(time)-1
 if( (t_utc(n,1).ge.5).and.(t_utc(n,1).le.10) ) then
  time1(index) = time(n)
  x_season(index,:,:) = x(time|n,lat|:,lon|:)
  index = index+1
 end if
end do
x_season&time = time1
end if

;************************************************
; Compute EOFs; no need to areal weight (15S to 15N)
;************************************************

;  eof    = eofunc_Wrap(x, neof, False)
;  eof_ts = eofunc_ts_Wrap(x,eof,False)

  x_season_w = x_season(lat|:,lon|:,time|:)*conform(x_season(lat|:,lon|:,time|:),gw,0)
  x_season_w!0 = "lat"
  x_season_w!1 = "lon"
  x_season_w!2 = "time"
  x_season_w&lat = lat
  x_season_w&lon = lon
  if(season.eq.0) then
  x_season_w&time = time0
  else
  x_season_w&time = time1
  end if
  eof    = eofunc_Wrap(x_season_w, neof, False)
  eof_ts = eofunc_ts_Wrap(x_season_w,eof,False)

  delete(x_season)
  delete(x_season_w)

;  printVarSummary( eof )
;  printVarSummary( eof_ts )

;------------------------------------------------------------
; PLOTS
;------------------------------------------------------------
  if (pltType.eq."png") then
      pltTypeLocal = "eps"
  else
      pltTypeLocal = pltType
  end if

;  print(pltDir)
;  print(pltName)
  pltPath = pltDir+pltName


  wks = gsn_open_wks(pltTypeLocal,pltPath)
  gsn_define_colormap(wks,"BlwhRe") 
  plot = new(neof,graphic)                ; create graphic array
                                          ; only needed if paneling
; EOF patterns

  res                      = True         
  res@gsnDraw              = False        ; don't draw yet
  res@gsnFrame             = False        ; don't advance frame yet
  res@gsnSpreadColors      = True         ; spread out color table
  res@gsnStringFontHeightF = 0.015         ; make larger than default
 
  res@mpFillOn             = False        ; turn off map fill
  res@mpMinLatF            = latS         ; zoom in on map
  res@mpMaxLatF            = latN
  res@mpCenterLonF         = 180.
  res@cnFillOn             = True         ; turn on color fill
  res@cnLinesOn            = False        ; True is default
  res@cnLineLabelsOn       = False        ; True is default
  res@lbLabelBarOn         = False        ; turn off individual lb's
                                          ; set symmetric plot min/max
  symMinMaxPlt(eof,  8, False, res)       ; contributed.ncl

; panel plot only resources
  resP                     = True         ; modify the panel plot
  resP@gsnMaximize         = True         ; large format
  resP@gsnPaperOrientation = "portrait" 
  resP@gsnPanelLabelBar    = True         ; add common colorbar
  resP@lbLabelAutoStride   = True         ; auto stride on labels
  resP@lbLabelFontHeightF  = 0.01

  txString            = vName+": "+yrStrt+"-"+yrLast+" "+seasons_name(season)
;  if (isvar("plev")) then
;      txString = txString+": "+plev+" hPa"
;  end if

;*******************************************
; first plot
;*******************************************
  do n=0,neof-1
     res@gsnLeftString   = "EOF "+(n+1)
     if (n.eq.0) then
         res@gsnCenterString = txString
     else
         res@gsnCenterString = ""
     end if
     res@gsnRightString  = sprintf("%5.1f", eof@pcvar(n)) +"%"
     plot(n)=gsn_csm_contour_map_ce(wks,eof(n,:,:),res)
  end do
  gsn_panel(wks,plot,(/neof,1/),resP)     ; now draw as one plot

;*******************************************
; second plot
;*******************************************
  rts           = True
  rts@gsnDraw   = False       ; don't draw yet
  rts@gsnFrame  = False       ; don't advance frame yet
  rts@gsnScale  = True        ; force text scaling               

; these four resources allow the user to stretch the plot size, and
; decide exactly where on the page to draw it.

  rts@vpHeightF = 0.40        ; Changes the aspect ratio
  rts@vpWidthF  = 0.85
  rts@vpXF      = 0.10        ; change start locations
  rts@vpYF      = 0.75        ; the plot

  rts@gsnYRefLine           = 0.              ; reference line   
 ;rts@gsnXYBarChart         = True            ; create bar chart 
  rts@gsnAboveYRefLineColor = "red"           ; above ref line fill red
  rts@gsnBelowYRefLineColor = "blue"          ; below ref line fill blue

; panel plot only resources
  rtsP                     = True             ; modify the panel plot
  rtsP@gsnMaximize         = True             ; large format
  rtsP@txString            = txString

; create individual plots

  if(season.eq.0) then
  ;yyyymmdd= cd_calendar(time0, -2)
  yrfrac = cd_calendar(time0, 4)
  else
  ;yyyymmdd= cd_calendar(time1, -2)
  yrfrac = cd_calendar(time1, 4)
  end if
  ;yrfrac  = yyyymmdd_to_yyyyfrac(yyyymmdd, 0.0) ; yyyymmdd_to_yyyyfrac assumes gregorian year
  if (isatt(yrfrac, "long_name")) then
    delete(yrfrac@long_name)
  end if

  nGrd    = nlat*mlon 
  eof_ts  = eof_ts/nGrd
  rts@tiYAxisString = x@units  

  do n=0,neof-1
     rts@gsnLeftString  = "EOF "+(n+1)
     rts@gsnRightString = sprintf("%5.1f", eof@pcvar(n)) +"%"
     work = wgt_runave_Wrap(eof_ts(n,:),121, 1)
     plot(n) = gsn_csm_xy (wks,yrfrac,   work    ,rts)
    ;plot(n) = gsn_csm_xy (wks,yrfrac,eof_ts(n,:),rts)
  end do
  gsn_panel(wks,plot,(/neof,1/),rtsP)     ; now draw as one plot

   if (pltType.eq."png") then
       if (.not.isvar("pltConvert")) then
           pltConvert = " "               ; default
       end if
       system("convert "+pltConvert+" "+pltPath+".eps "+pltPath+".png")
       system("convert "+pltConvert+" "+pltPath+".eps "+pltPath+".png")
       system("rm -f "+pltPath+".eps")
   end if

delete(pltName)
delete(eof)
delete(eof_ts)
delete(work)
; delete(yyyymmdd)
delete(yrfrac)

print(routine_name+" wrote "+pltPath)
end do ; season loop
end do ; variable loop

end
