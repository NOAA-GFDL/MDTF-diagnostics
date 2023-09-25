; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

; FILE: mjo.ncl

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin
; read daily output files from CAM2 and process the u200 data
; each daily file has 30 days of data
; U200(time,lat,lon)

routine_name = "mjo.ncl"
pod_home = getenv("POD_HOME")
casename = getenv("CASENAME")
file_dir = getenv("WK_DIR")+"/model/netCDF/"
yr1 = getenv("FIRSTYR")
yr2 = getenv("LASTYR")
time_coord = getenv("time_coord")

firstyr = stringtointeger(yr1)
lastyr = stringtointeger(yr2)
ndays = (lastyr-firstyr+1)*365  ; noleap years in model

f = addfile(file_dir+casename+".u200.day.nc","r")
gw = f->gw
date = f->date
maxdays = dimsizes(date)
if (ndays .gt. maxdays) then
  ndays = maxdays
end if
u200 = f->u200(0:ndays-1,{-10:10},:) 
; yrfrac = yyyymmdd2yyyyFrac(date(0:ndays-1),0) ; second arg is an offset
; yrfrac = yyyymmdd_to_yyyyfrac(date(0:ndays-1), 0.0) ; second arg is an offset
yrfrac_time = f->$time_coord$
yrfrac = cd_calendar(yrfrac_time(0:ndays-1), 4)
yrfrac!0 = "date as fraction of year"

; compute weighted area ave of U200 over tropics
data = new(ndays,"float")
data!0 = "u200"
data = wgt_areaave(u200,gw({-10:10}),1.,0)

; read the 20-100 day filter weights
weights = asciiread(pod_home+"/bp_filter_20-100",-1,"float")
nwgts = dimsizes(weights)

; filter the U200 data
filtered = wgt_runave(data,weights,0)
filtered!0 = "filtered_u200"
nfil = dimsizes(filtered)

; 101-day running variance 
var_fil = new(nfil,float)
var_fil!0 = "variance"
var_str = new(nfil,string)
do n = 50,nfil-51
  if (all(.not.ismissing(filtered(n-50:n+50)))) then
    var_fil(n) = variance(filtered(n-50:n+50)) 
    var_str(n) = sprintf("%9.4f",data(n))+" "+var_fil(n)
  end if
end do

; MAKE PLOTS
psplot = getenv("WK_DIR")+"/model/PS/"+casename+".MJO"
wks = gsn_open_wks("ps",psplot)
plot = new(3,graphic)
res = True
res@gsnFrame = False
res@gsnDraw = False
res@gsnYRefLine = 0.0
res@tmXBMode = "Explicit"
res@tmXBLabels = ispan(firstyr,lastyr+1,2) 
res@tmXBValues = ispan(firstyr,lastyr+1,2)
res@tmXBMinorValues = ispan(firstyr,lastyr+1,1)
res@tmYLLabelFontHeightF = 0.015
res@tmXBLabelFontHeightF = 0.015
res@tiYAxisFontHeightF = 0.018
res@tiXAxisFontHeightF = 0.018
res@tiYAxisString = "U (m/s)"
res@tiXAxisString = "Year"
res@tiMainFontHeightF = 0.018
res@vpXF = 0.10
res@vpWidthF = 0.85
res@vpHeightF = 0.30
res@trXMinF = firstyr
res@trXMaxF = lastyr+1

if ( False ) then
  print("DEBUG yrfrac")
  print(getvardims(yrfrac)+": "+dimsizes(yrfrac))
  print("DEBUG data")
  print(getvardims(data)+": "+dimsizes(data))
  print("DEBUG filtered")
  print(getvardims(filtered)+": "+dimsizes(filtered))
  print("DEBUG var_fil")
  print(getvardims(var_fil)+": "+dimsizes(var_fil))
end if

; First Plot
res@gsnCenterString = casename+" Mean of Daily 200 mb Zonal Wind (10S-10N)" 
res@trYMaxF = 15.0
res@trYMinF = -15.0
plot(0) = gsn_csm_xy(wks,yrfrac,data,res)

; Second Plot
res@gsnCenterString = "Band-pass Filtered for 20-100 Day Periods" 
res@trYMaxF = 6.0
res@trYMinF = -6.0
res@xyLineColor = "blue"
plot(1) = gsn_csm_xy(wks,yrfrac,filtered,res)

; Third Plot
res@gsnCenterString = "101-day Running Variance of Band-pass Filtered Data"
res@trYMaxF = 12.0
res@trYMinF = 0.0
res@tiYAxisString = "variance (m~S~2~N~/s~S~2~N~)"
res@xyLineColor = "red"
plot(2) = gsn_csm_xy(wks,yrfrac,var_fil,res)

pan = True
pan@gsnMaximize = True
pan@gsnPaperOrientation = "portrait"
pan@gsnPanelYWhiteSpacePercent = 2.0
gsn_panel(wks,plot,(/3,1/),pan)

print(routine_name+" wrote "+psplot+".ps")
end
