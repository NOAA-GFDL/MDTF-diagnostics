; This file is part of the MJO_prop_amp module of the MDTF code package (see LICENSE.txt)


load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

wk_dir = getenv("WK_DIR")
OBS_DATA = getenv("OBS_DATA")
; model skill score names (MJO propagtion, specific humidity,
;                          MJO amplitude, convect. timescale)
ss_name = (/"prop","shum","amp","tc"/)

; model output files
fn_pr  = wk_dir+"/model/netCDF/model_pr.nc"
fn_prw = wk_dir+"/model/netCDF/model_prw.nc"
fn_hus = wk_dir+"/model/netCDF/model_hus_900_650_avg.nc"

; season of interest (use first 3 letters only 
; in the format: Jan, Feb, Mar,..., Dec) 
month0_str = "Nov"
monthf_str = "Apr"

; Lanczos temporal filtering
ta = 100   ; upper cutoff period [days] 
tb =  20   ; lower cutoff period [days]
nwt = 31   ; number of Lanczos weights; 

; number of lags (in days) for Hovmoller plots
nlag = 20

; lats to average over and lon boundaries for Hovmoller plots
lats_hov = -15
latn_hov =  15
lonw_hov =  50
lone_hov = 180

; domain for winter mean low-level moisture pattern
lats_map = -30
latn_map =  30
lonw_map =  30
lone_map = 210

;--------------------EDIT HERE ONLY-------------------------;
; Constants 
One   = 1.
Two   = 2.
Kilo  = 1000.
pi    = 4d*atan(One)
g     = 9.81     ; gravity
rho_w = Kilo ; water density

; longer names of variables
fname_pr  = "precipitation"
fname_prw = "precipitable water"
fname_hus = "specific humidity"

; read netcdf file for precipiation
print_clock("Processing Model " +fname_pr)
fin = addfile(fn_pr,"r") 
; read precip array from file
pr = fin->pr(:,{lats_hov:latn_hov},{lonw_hov:lone_hov})
pr = pr*86400.
;printMinMax(dim_avg_n_Wrap(pr,0),0)
; type for all non-int vars - either float or double
precision = typeof(pr)

; read time array (for selection of season)
dname=getvardims(pr)
tname=dname(0)
latname=dname(1)
lonname=dname(2)
time  = fin->$tname$
; read number of elements lon vector 
lon = fin->$lonname$({lonw_hov:lone_hov})
nx_p = dimsizes(lon)
delete(fn_pr)
delete(fin)

; read netcdf file for precipiation
print_clock("Processing Model " +fname_prw)
fin = addfile(fn_prw,"r")
; read precip array from file
prw = fin->prw(:,{lats_hov:latn_hov},{lonw_hov:lone_hov})
delete(fn_prw)
delete(fin)
;printMinMax(dim_avg_n_Wrap(prw,0),0)


;***********************************************************
; Step 1: Remove seasonal cycle and nharm harmonics using 
; clmDayTLL, smthClmDayTLL, and calcDayAnomTLL
;***********************************************************
; number of harmonics for smoothed annual cycle
   nharm = 6

; concatenate time to yearmonthday using cd_calendar
; and then to yeardayofyear using yyyymmdd_to_yyyyddd
   yyyyddd = yyyymmdd_to_yyyyddd(cd_calendar(time,-2))

; average over all years - annual cycle
   pr_annual = clmDayTLL(pr,yyyyddd)
; smooth annual cycle
   pr_smth = smthClmDayTLL(pr_annual,nharm) 
; remove smooth annual cycle 
   pr = calcDayAnomTLL(pr,yyyyddd,pr_smth)
   delete([/pr_annual,pr_smth/])
   ;printVarSummary(pr)

; average over all years - annual cycle
   prw_annual = clmDayTLL(prw,yyyyddd)
; smooth annual cycle
   prw_smth = smthClmDayTLL(prw_annual,3) 
; remove smooth annual cycle 
   prw = calcDayAnomTLL(prw,yyyyddd,prw_smth)
   delete([/yyyyddd,prw_annual,prw_smth/])
   ;printVarSummary(prw)

;***********************************************************
; Step 2: Compute bandpass filter using Lanczos filter and 
; wgt_runave_n_Wrap
;***********************************************************	
dt  = 1.    ; time step [days]
fca = dt/ta ; low frequency cutoff
fcb = dt/tb ; high frequency cutoff

; initialize weights
wgt = new((/nwt/),precision)
; calculate weights
   do jj=1,nwt
      ang2 = Two*pi*fcb*jj
      ang1 = Two*pi*fca*jj
      ang  = (pi*jj)/(nwt*One)
      term = (sin(ang2)-sin(ang1))/(pi*jj)
      sigma = sin(ang)/ang
      if precision .eq. "float"
      wgt(jj-1) = doubletofloat(term*sigma)
      else
      wgt(jj-1) = term*sigma
      end if
   end do

; weight of center point
w0 = 2.*(fcb-fca)

pts = nwt*2+1

; full set of weights
wgt_full = new((/pts/),precision)
wgt_full(:nwt-1) = wgt(::-1)
wgt_full(nwt)    = w0
wgt_full(nwt+1:) = wgt

; apply weights to precipitation (data becomes filtered over chosen freq)
pr = wgt_runave_n_Wrap(pr,wgt_full,0,0) ; sub-period
;printVarSummary(pr)
;printMinMax(pr,0)

; apply weights to precipitable water (data becomes filtered over chosen freq)
prw = wgt_runave_n_Wrap(prw,wgt_full,0,0) 
;printVarSummary(prw)
;printMinMax(prw,0)

;***********************************************************
; Step 3: Focus on a season using cd_calendar and ind
;***********************************************************
; make a long vector with years and months for each time 
t3d = cd_calendar(time,0)
lyr  = t3d(:,0)
lmon = t3d(:,1)
delete(t3d)

; find starting and ending years
yr0 = min(lyr)
yrf = max(lyr)

; convert month string to int
month_str_short = (/"Jan","Feb","Mar","Apr","May","Jun","Jul",\
                   "Aug","Sep","Oct","Nov","Dec"/)

; find the indices associated with month strings
mn0 = ind(month_str_short.eq.month0_str)+1
mnf = ind(month_str_short.eq.monthf_str)+1

; the begining and end of the data are excluded
id_seas = ind( (lyr.ge.yr0.and.lyr.lt.yrf.and.lmon.ge.mn0) \
            .or. (lyr.gt.yr0.and.lyr.le.yrf.and.lmon.le.mnf) )
delete([/lyr,lmon,time/])
;printVarSummary(id_seas)

;***********************************************************
; Step 4: Take averages over an Indian Ocean box and a West
; Pacific box using dim_avg_n_Wrap
;***********************************************************

; create daily lag vector
lag = ispan(-nlag,nlag,1)
lag!0 = "lag"
lag&lag = lag
lag@units = "days" 
nl = dimsizes(lag)

; average data over an area box over Indian Ocean
prbox_io  = dim_avg_n_Wrap(pr(id_seas,{-5:5},{75:85}),(/1,2/))
prwbox_io = dim_avg_n_Wrap(prw(id_seas,{-5:5},{75:85}),(/1,2/))
;printVarSummary(prbox_io)

; average data over an area box over West Pacific
prbox_wp = dim_avg_n_Wrap(pr(id_seas,{-5:5},{145:155}),(/1,2/))

;***********************************************************
; Step 5: Take seasonal and vertical average for specific humidity  
;***********************************************************

; read netcdf file for specific humidity
fin = addfile(fn_hus,"r") 

; read number of elements in lat and lon for specific humidity array
ny_q = dimsizes(fin->$latname$({lats_map:latn_map}))
nx_q = dimsizes(fin->$lonname$({lonw_map:lone_map}))

; initialize arrays for Indian Ocean and West Pacific lag regressions, 
; as well as specific humidity maps
   f_io  = new((/nx_p,nl/),precision)
   f_wp  = new((/nx_p,nl/),precision)
   hus   = new((/ny_q,nx_q/),precision)
   prw_io = new((/1/),precision)
   pr_io = new((/1/),precision)
   tconv = new((/1/),precision)
   MJO_amp = new((/1/),precision)

; read specific humidity array and take seasonal and vertical average
hus(:,:) = dim_avg_n_Wrap(fin->hus(id_seas, \
             {lats_map:latn_map},{lonw_map:lone_map}),0)*Kilo
hus!0 = "lat"
hus!1 = "lon"
hus&lat=fin->$latname$({lats_map:latn_map})
hus&lon=fin->$lonname$({lonw_map:lone_map})
printVarSummary(hus)
;printMinMax(hus,0)

;***********************************************************
; Step 6: Compute lag regressions using regCoef_n
;***********************************************************

; compute MJO amplitude 
MJO_amp = avg(dim_stddev_n_Wrap(pr(id_seas,{-5:5},{75:85}),0))
print("Model MJO amplitude = "+sprintf("%5.2f",MJO_amp))

stdprbox_io=dim_stddev_n_Wrap(prbox_io(:),0)
stdprbox_wp=dim_stddev_n_Wrap(prbox_wp(:),0)

do jj = 0,nl-1
ll = jj-nlag ; lags go from -nlag/2 to +nlag/2
f1 = pr(id_seas+ll,:,:)
; regress prcp onto base time series and normalize by prcp0
f_io(:,jj)  = dim_avg_n_Wrap(regCoef_n(prbox_io,f1,0,0)*stdprbox_io,0)
f_wp(:,jj)  = dim_avg_n_Wrap(regCoef_n(prbox_wp,f1,0,0)*stdprbox_wp,0)
end do

; compute convective time scale
pr_io = avg(regCoef_n(prbox_io,pr(id_seas,{-5:5},{75:85}),0,0))
prw_io = avg(regCoef_n(prbox_io,prw(id_seas,{-5:5},{75:85}),0,0))
tconv = prw_io/pr_io
print("Model convective time scale = " +sprintf("%5.2f",tconv))

; clean up for efficiency
delete([/id_seas,pr,prw,f1,prbox_io,prbox_wp,prwbox_io/])

; assign metadata to precip
f_io!0 = "lon"
f_io!1 = "lag"
f_io&lon = lon 
f_io&lag = lag
copy_VarMeta(f_io,f_wp)

; just to make sure the type is correct
precision = typeof(f_io)

; create one array for Hovmoller
prcp = new((/nl,nx_p,4/),precision)
prcp(:,:,0) = f_io(lag|:,lon|:)
prcp(:,:,1) = f_wp(lag|:,lon|:)

prcp_io = new((/nl,1,nx_p/),precision)
prcp_wp = new((/nl,1,nx_p/),precision)
prcp_io(:,0,:)=prcp(:,:,0)
prcp_wp(:,0,:)=prcp(:,:,1)
prcp_io!0="time"
prcp_io!1="lat"
prcp_io!2="lon"
prcp_wp!0="time"
prcp_wp!1="lat"
prcp_wp!2="lon"
prcp_io&time=f_io&lag 
prcp_io&lon=f_io&lon
prcp_io&lat=0.
prcp_wp&time=f_io&lag 
prcp_wp&lon=f_io&lon
prcp_wp&lat=0.
prcp_io&lat@units = "degrees_north"
prcp_io&lon@units = "degrees_east"
prcp_io&time@units = "days since 0000-01-21 00:00:00"
prcp_wp&lat@units = "degrees_north"
prcp_wp&lon@units = "degrees_east"
prcp_wp&time@units = "days since 0000-01-21 00:00:00"

system("rm -f "+wk_dir+"/model/netCDF/model_hovmoller.nc")
fout = addfile(wk_dir+"/model/netCDF/model_hovmoller.nc","c")            
fAtt               = True            ; assign file attributes
fAtt@title         = "Hovmoller Diagram of Rainfall associated with the MJO"
fAtt@source_file   =  ""
fAtt@Conventions   = "None"
fAtt@creation_date = systemfunc ("date")
fileattdef( fout, fAtt )
filedimdef(fout,"time",-1,True)
prcp_io&time@calendar="leap"
prcp_wp&time@calendar="leap"
fout->prcp_io = prcp_io
fout->prcp_wp = prcp_wp
delete([/f_io,f_wp/])
delete([/prcp_io,prcp_wp,fout/])

husm   = new((/1,ny_q,nx_q/),precision)
husm (0,:,:)=hus(:,:)
husm!0="time"
husm!1="lat"
husm!2="lon"
husm&time=1
husm&lon=hus&lon
husm&lat=hus&lat
husm&lat@units = "degrees_north"
husm&lon@units = "degrees_east"
husm&time@units = "days since 0000-01-11 00:00:00"

system("rm -f "+wk_dir+"/model/netCDF/model_hus_900_650_mean.nc")
fout = addfile(wk_dir+"/model/netCDF/model_hus_900_650_mean.nc","c")
fAtt               = True            ; assign file attributes
fAtt@title         = "Winter mean (Nov-Apr) 900-650hPa specific humidity"
fAtt@source_file   =  ""
fAtt@Conventions   = "None"
fAtt@creation_date = systemfunc ("date")
fileattdef( fout, fAtt )
filedimdef(fout,"time",-1,True)
husm&time@calendar="leap"
fout->hus = husm
;delete([/husm,fout/])

;***********************************************************
; Step 7: Compute pattern correlation for precip and 
; specific humidity   
;***********************************************************
; make Hovmoller one-dimensional for pattern correlation
fin = addfile(OBS_DATA+"/obs_hovmoller.nc","r")            
if precision .eq. "float"
prcp(:,:,2)=doubletofloat(fin->prcp_io(:,0,:))
prcp(:,:,3)=doubletofloat(fin->prcp_wp(:,0,:))
else
prcp(:,:,2)=fin->prcp_io(:,0,:)
prcp(:,:,3)=fin->prcp_wp(:,0,:)
end if
prcp_rs = reshape(prcp,(/nx_p*nl,4/))
; compute correlation for Indian Ocean and West Pacific precip
pc_io = escorc(prcp_rs(:,0),prcp_rs(:,2))
pc_wp = escorc(prcp_rs(:,1),prcp_rs(:,3))
; average two correlations
pc_pr = (pc_io + pc_wp)/Two
print("Model MJO propagation skill score = "+sprintf("%5.2f",pc_pr))
delete([/pc_io,pc_wp,fin/])

husobs = new((/ny_q,nx_q/),precision)
husobs!0 = "lat"
husobs!1 = "lon"
fin = addfile(OBS_DATA+"/obs_hus_900_650_mean.nc","r")            
if precision .eq. "float"
husobs(:,:)=doubletofloat(fin->hus(0,:,:))
else
husobs(:,:)=fin->hus(0,:,:)
end if
husobs&lon=fin->hus&lon
husobs&lat=fin->hus&lat
ny_q = dimsizes(hus({-20:20},0))
nx_q = dimsizes(hus(0,{90:135}))
; make specific humidity one-dimensional for pattern correlation
q_rs1 = reshape(hus({-20:20},{90:135}),(/ny_q*nx_q/))
q_rs2 = reshape(husobs({-20:20},{90:135}),(/ny_q*nx_q/))
; compute correlation for specific humidity
pc_q = escorc(q_rs1(:),q_rs2(:))
print("Model Winter mean moisture pattern skill score = "+sprintf("%5.2f",pc_q))
delete([/husobs,q_rs1,q_rs2,fin/])

;***********************************************************
; Step 8: Load model scores for MJO propagation, moisture
; pattern, MJO amplitude, convective time scale and compute
; linear regression metrics for scatterplots
;***********************************************************

; scores for all models from the MJOTF/GASS GCMs
nmod = 24
prop_ss = new((/nmod+1/),precision)
shum_ss = new((/nmod+1/),precision)
amp     = new((/nmod+1/),precision)
tau     = new((/nmod+1/),precision)

;model       01  03a  04+   05  07-  10+  11-   16   21  22-   24  27-  31a 31b+  31c   34   35   36   37   40  43-   44   45
amp     =(/2.96,3.72,5.87,3.80,2.61,5.53,6.08,3.97,2.65,3.05,6.11,6.36,3.56,3.87,3.33,2.79,9.25,2.99,3.49,4.62,3.92,2.79,2.99,0.00,0.00/)
prop_ss =(/0.66,0.86,0.90,0.63,0.53,0.83,0.47,0.69,0.67,0.58,0.59,0.58,0.76,0.88,0.77,0.48,0.62,0.74,0.90,0.69,0.55,0.76,0.79,0.00,0.00/)
shum_ss =(/0.95,0.94,0.96,0.93,0.90,0.96,0.86,0.92,0.92,0.91,0.94,0.88,0.88,0.96,0.95,0.87,0.89,0.96,0.97,0.95,0.91,0.91,0.97,0.00,0.00/)
tau     =(/0.86,0.79,0.61,1.47,1.07,0.62,0.89,0.81,0.96,0.93,0.57,0.53,1.11,1.04,1.05,0.96,0.33,0.87,0.93,0.80,0.48,1.09,0.84,0.00,0.00/)

; add scores for this model
prop_ss(nmod-1) = pc_pr
shum_ss(nmod-1) = pc_q
amp(nmod-1)     = MJO_amp
tau(nmod-1)      = tconv

; add scores for observations
prop_ss(nmod) = 1
shum_ss(nmod) = 1
amp(nmod)     = 4.67
tau(nmod)     = 0.79

; compute regression cofficient and least squares regression
; line for MJO propagation vs. moisture pattern scatterplot
rc = regline(shum_ss,prop_ss)
reg1 = rc*(shum_ss-rc@xave) + rc@yave
; compute regression cofficient and least squares regression
; line for MJO amplitude vs. convective time scale
rc = regline(tau,amp)
reg2 = rc*(tau-rc@xave) + rc@yave


;***********************************************************
; Step 7: Create plot
;***********************************************************

; figure type (ps, pdf, eps, tif)
   figtype = "ps"
;   figtype@wkWidth = 2500
;   figtype@wkHeight = 2500 

; plot resources (always set to true)
   res = True
   
;--------------------Hovmoller plots------------------------

; contours for Hovmoller
cmax_p = 2.1
cmin_p = -cmax_p
nlev_p =  14

   res@cnLevelSelectionMode = "ManualLevels"         ; manually set the contour levels
   res@cnMinLevelValF       = cmin_p                 ; set the minimum contour level
   res@cnMaxLevelValF       = cmax_p                 ; set the maximum contour level
   res@cnLevelSpacingF      = (cmax_p-cmin_p)/nlev_p ; set the interval between contours

   res@cnLineLabelsOn       = False                  ; turn on/off contour line labels
   res@cnFillOn             = True                   ; turn on/off contour fill 
   res@cnLinesOn            = True                   ; turn on/off contour lines 
   res@cnInfoLabelOn        = False                  ; turn on/off contour information label
   res@gsnContourNegLineDashPattern = 1              ; make negative values dashed
   res@gsnContourZeroLineThicknessF = 0.             ; make zero line disappear
   
   vpw = 0.60    ; width
   aratio = 0.45 ; try to keep the height/width aspect ratio to close to 0.5
   res@vpWidthF             = vpw                    
   res@vpHeightF            = aratio*vpw

   ; x and y tickmark label font height
   lbfh = 0.013
   res@tmXBLabelFontHeightF = lbfh 
   res@tmYLLabelFontHeightF = lbfh 

   ; for panel plots
   res@gsnDraw  = False                              ; don't draw plots yet
   res@gsnFrame = False                              ; don't advance frame yet

   ; create new longitude labels
   ; I prefer to be in control of these labels, but you can choose not to do this
   ; just set res@tmXBMode = "Automatic" or delete the line altogether
   lon_plt = ispan(20,230,10)
   lon_plt_str = tostring(lon_plt)
   iE = ind(lon_plt.lt.180)
   iW = ind(lon_plt.gt.180)
   i0 = ind(lon_plt.eq.180)
   lon_plt_str(i0) = lon_plt_str(i0)+"~S~o~N~"
   lon_plt_str(iE) = lon_plt_str(iE)+"~S~o~N~E"
   lon_plt_str(iW) = lon_plt_str(iW)+"~S~o~N~W"
   lon_plt_str(iW) = ispan(170,130,10)+"~S~o~N~W"
   
   res@tmXBMode          = "Explicit"                ; explicit labels
   res@tmXBValues        = lon_plt(::2)              ; location of labels 
   res@tmXBLabels        = lon_plt_str(::2)          ; labels themselves
   res@tmXBMinorValues   = lon_plt                   ; location of labels 
   ; remove this for now, can be added later
   ;res@tiYAxisString     = "lag (day)" 

   ; Create a blue to red colormap from colorbrewer2.org
   blrd = (/ (/49,54,149/),   (/69,117,180/),\
             (/116,173,209/), (/171,217,233/), (/224,243,248/), (/255,255,255/), \
             (/254,224,144/), (/253,174,97/),  (/244,109,67/),  (/215,48,39/),\
             (/165,0,38/)/)

   nlevi = dimsizes(blrd(:,0))  ; number of levels from colorbrewer

   cm = todouble(blrd)/256d                          ; Convert to RGB values.
   ;gsn_define_colormap(wks1,cm)                      ; Set the color map.

; initial levels
   xi = fspan(0,nlevi-1,nlevi)

; intepolate levels and choose whether you want white near zero or not
   xo = fspan(0,nlevi-1,nlev_p+1)

; do the linear interpolation
   cms = linint1_n_Wrap(xi,cm,False,xo,0,0)
   res@cnFillPalette = cms                        ; set the contour color map

   res@lbOrientation      = "horizontal"          ; labelbar orientation
   res@pmLabelBarParallelPosF   =  0.55           ; move labelbar up/down
   res@pmLabelBarOrthogonalPosF = -0.01           ; move labelbar sideways
   res@pmLabelBarWidthF   = 0.6                   ; thin or widen labelbar
   res@pmLabelBarHeightF   = 0.05                  ; thin or widen labelbar
   res@lbTitleString      = "mm d~S~-1"           ; precip units string
   res@lbTitlePosition    = "Right"
   res@lbTitleDirection   = "Across"
   res@lbTitleFontHeightF = lbfh 
   res@lbLabelFontHeightF = lbfh 

   wks1a = gsn_open_wks(figtype, wk_dir+"/model/PS/fig1b")
   plot   = new(1,graphic)                     ; create a plot array for all panels
   ;plotxy = new(4,graphic)                    ; optional 5 m/s line, can be done later
   do jj=0,0
      res@gsnLeftString  = ""                  ; left title
      res@lbLabelBarOn   = True                 ; whether or not to have a labelbar
      res@tmXBLabelsOn   = True                 ; turn on/off x axis labels
      res@tmYLLabelsOn   = True                 ; turn on/off y axis labels
      ; finally, plot hovmoller diagram!
      plot(jj) = gsn_csm_hov(wks1a,prcp(:,:,0),res)

      ; add text with correlation cofficient
      txres               = True
      txres@txFontHeightF = lbfh                      ; Set the font height
      txres@txPerimOn     = True
      txres@txBackgroundFillColor = "white"
      xx = 192.
      yy =  16.
   end do

; create panel plot
   resP = True                         ; modify the panel plot
   resP@gsnMaximize     = False        ; maximize the panel plot size
   resP@gsnPanelRowSpec = True         ; specify the number of plots per row
   resP@txString     = ""           ; add a title
   gsn_panel(wks1a,plot,(/2,2/),False) ; now draw as one plot
   delete([/wks1a,plot/])

   wks1c = gsn_open_wks(figtype, wk_dir+"/model/PS/fig1d")
   plot   = new(1,graphic)                     ; create a plot array for all panels
      res@gsnLeftString  = ""                  ; left title
      res@lbLabelBarOn   = True                 ; whether or not to have a labelbar
      res@tmXBLabelsOn   = True                 ; turn on/off x axis labels
      res@tmYLLabelsOn   = True                 ; turn on/off y axis labels
      ; finally, plot hovmoller diagram!
      plot(0) = gsn_csm_hov(wks1c,prcp(:,:,1),res)

      ; add text with correlation cofficient
      txres               = True
      txres@txFontHeightF = lbfh                      ; Set the font height
      txres@txPerimOn     = True
      txres@txBackgroundFillColor = "white"
      xx = 192.
      yy =  16.

; create panel plot
   resP = True                         ; modify the panel plot
   resP@gsnMaximize     = False        ; maximize the panel plot size
   resP@gsnPanelRowSpec = True         ; specify the number of plots per row
   resP@txString     = ""           ; add a title
   gsn_panel(wks1c,plot,(/2,2/),False) ; now draw as one plot
   delete([/wks1c,plot/])

   delete([/cm,cms,xi,xo/])

;-----------------Specific Humidity plots-------------------

; contours for specific humidity maps
cmax_q = 10.5
cmin_q =  2.5
nlev_q =   16

   res@cnLevelSelectionMode = "ManualLevels"         ; manually set the contour levels
   res@cnMinLevelValF       = cmin_q                 ; set the minimum contour level
   res@cnMaxLevelValF       = cmax_q                 ; set the maximum contour level
   res@cnLevelSpacingF      = (cmax_q-cmin_q)/nlev_q ; set the interval between contours
   res@cnLinesOn            = False                  ; turn on/off contour lines

   ; only show lats and lons of interest
   res@mpMinLatF    = lats_map                       
   res@mpMaxLatF    = latn_map
   res@mpMinLonF    = lonw_map
   res@mpMaxLonF    = lone_map
   res@mpCenterLonF = 180
   res@gsnAddCyclic = False

   res@mpShapeMode = "FreeAspect"                    ; turn on/off control of aspect ratio
                                                     ; this is simply to control width of maps
                                                     ; so that they are equal with Hovmollers
   ; keep aspect ratio consistent with lat and lon
   aratio = abs(tofloat(latn_map-lats_map)/tofloat(lone_map-lonw_map))
   res@vpHeightF           = vpw*aratio              

   ; Create a white to green to blue colormap (from colorbrewer2.org, now NCL has something 
   ; built in, but I prefer to do it myself)  
   grbl = (/ (/255,255,255/), (/247,252,240/), (/224,243,219/), \
             (/204,235,197/), (/168,221,181/), (/123,204,196/), (/78,179,211/), \
             (/43,140,190/),  (/8,104,172/),   (/8,64,129/)/)
   nlevi = dimsizes(grbl(:,0)) ; number of levels from colorbrewer

   cm = todouble(grbl)/256d                          ; Convert to RGB values.

   ; initial levels
   xi = fspan(0,nlevi-1,nlevi)
   ; final levels
   xo = fspan(0,nlevi-1,nlev_q+2)
   ; do the interpolation
   cms = linint1_n_Wrap(xi,cm,False,xo,0,0)
   delete(res@cnFillPalette) ; required for reset of color map
   res@cnFillPalette = cms                           ; set the contour color map

   res@pmLabelBarOrthogonalPosF = 0.2
   res@lbTitleString       = "g kg~S~-1"             ; specific humidity units string

   wks2a = gsn_open_wks(figtype, wk_dir+"/model/PS/fig2b")
   plot   = new(1,graphic)                     ; create a plot array for all panels
	jj=0
      res@lbLabelBarOn   = True
      res@tmXBLabelsOn   = True
      res@tmYLLabelsOn   = True
      ; finally, plot the specific humidity map!
      plot(jj) = gsn_csm_contour_map(wks2a,hus(:,:),res)

      ; add text with correlation cofficient
      txres               = True                            
      txres@txFontHeightF = lbfh                      ; Set the font height
      xx = 192.
      yy =  22.

; create panel plot
   resP = True                         ; modify the panel plot
   resP@gsnMaximize     = False        ; maximize the panel plot size
   resP@gsnPanelRowSpec = True         ; specify the number of plots per row

   resP@txString     = ""           ; add a title

   gsn_panel(wks2a,plot,(/2,2/),False) ; now draw as one plot
   delete([/wks2a,plot,res/])

;----Scatter plots MJO propagation vs moisture pattern---
   wks3 = gsn_open_wks(figtype, wk_dir+"/model/PS/fig3")

; create new colors from ColorBrewer2.org (credit: Cynthia Brewer)
;  black     = todouble((/0,0,0/))/256d
   black     = todouble((/195,195,195/))/256d
;  new_green = todouble((/77,175,74/))/256d
   new_green = todouble((/255,0,0/))/256d
;  new_purp  = todouble((/152,78,163/))/256d
   new_purp  = todouble((/0,0,255/))/256d

; Do this in order to create an 2D array of multiple 
; colors in scatterplot
   color_list = new((/nmod+1/),"string")
   color_list = new((/nmod+1/),"string")
   color_list         = "black"
   color_list(nmod)   = "green"
   color_list(nmod-1) = "purple"
   
; for plot resources
unique_colors_new = (/black,new_green,new_purp/)
; for loop below
   unique_colors     = (/color_list(0),color_list(nmod), \
                        color_list(nmod-1)/)
   ncolors           = dimsizes(unique_colors)

   ; 2D array with multiple colors for scatterplot
   y2d = new((/ncolors,nmod+1/),precision)      
   x2d = new((/ncolors,nmod+1/),precision)
   do i=0,ncolors-1
      ii  = ind(color_list.eq.unique_colors(i))
      nii = dimsizes(ii)
      y2d(i,:nii-1) = prop_ss(ii)
      x2d(i,:nii-1) = shum_ss(ii)
      delete(ii)
    end do

   res                    = True       ; resources for scatterplots                 
   res@xyMarkLineMode     = "Markers"     
   ; all scatterplot markers are circles except observations and model of interest
   mks = new((/3,3/),integer)
   mks = 16
   mks(:,1) = 16
   mks(:,2) = 16
   res@xyMarkers = mks       
   ; marker sizes are larger for observations and model of
   ; interest 
   sizes = new((/3,3/),double)
   sizes = 0.01
   sizes(:,1) = 0.015
   sizes(:,2) = 0.015
   res@xyMarkerSizes       = sizes        
   res@xyMarkerColors      = unique_colors_new
   res@gsnFrame            = False                   ; don't advance frame yet
   res@gsnDraw             = False                   ; don't draw plot

   res2                    = True                    ; resources for regression line               
   res2@xyDashPatterns     = 0                       ; solid line 
   res2@xyLineThicknesses  = 2                      
   res2@xyLineColor        = "grey"                  
   res2@gsnFrame           = False                   ; don't advance frame yet
   res2@gsnDraw            = False                   ; don't draw plot

; abscissa and ordinate limits for MJO propagation skill vs. moisture pattern skill
scat1_xmin =  0.8
scat1_xmax =  1.05
scat1_ymin =  0.4
scat1_ymax =  1.05

; scatterplot correlation text location and font height
corfh = 0.01
xx1 =  .5
yy1 =  .9

; abscissa and ordinate limits for MJO amplitude vs. convective time scale
scat2_xmin =  0.3
scat2_xmax =  1.8
scat2_ymin =  2.0
scat2_ymax =  7.0

; scatterplot correlation text location
xx2 = -1.5
yy2 =  7.5

   ; width of scatterplots
   vpw = .65*vpw
   aratio = .65
   res2@vpWidthF                = vpw                    
   res2@vpHeightF               = aratio*vpw
   res2@tmXBMajorOutwardLengthF = 0.0                ; draw tickmarks inward
   res2@tmXBMinorOutwardLengthF = 0.0                ; draw minor ticks inward
   res2@tmYLMajorOutwardLengthF = 0.0                ; draw tickmarks inward
   res2@tmYLMinorOutwardLengthF = 0.0                ; draw minor ticks inward
   res2@trXMaxF                 = scat1_xmax  
   res2@trXMinF                 = scat1_xmin
   res2@trYMaxF                 = scat1_ymax
   res2@trYMinF                 = scat1_ymin

   ; abscissa and ordinate titles
   res2@tiXAxisString  = "Moisture pattern skill"
   res2@tiYAxisString  = "MJO propagation skill"

   plot   = new(1,graphic)                     ; create a plot array for all panels
   plot1 = gsn_csm_xy (wks3,x2d,y2d,res)             ; create plot
   plot(0) = gsn_csm_xy (wks3,shum_ss,reg1,res2)     ; create plot

   delete(txres)
   ; add text with correlation cofficient
   txres               = True                            
   txres@txFontHeightF = corfh                      ; Set the font height
   tx1 = gsn_add_text(wks3,plot(0),"cor.="+sprintf("%4.2f", escorc(shum_ss,prop_ss)),xx1,yy1,txres)
   overlay(plot(0),plot1)
   delete(plot1)

; create panel plot
   resP = True                         ; modify the panel plot

   resP@gsnMaximize     = False        ; maximize the panel plot size
   resP@gsnPanelRowSpec = True         ; specify the number of plots per row

   resP@txString     = ""           ; add a title

   gsn_panel(wks3,plot,(/2,2/),False) ; now draw as one plot
   delete([/wks3,plot,res/])

;-------Scatter plots MJO amplitude vs convective timescale-------
   wks4 = gsn_open_wks(figtype, wk_dir+"/model/PS/fig4")

   ; create new colors from ColorBrewer2.org 
   ; (credit: Cynthia Brewer)
;  black     = todouble((/0,0,0/))/256d
   black     = todouble((/195,195,195/))/256d
;  new_green = todouble((/77,175,74/))/256d
   new_green = todouble((/255,0,0/))/256d
;  new_purp  = todouble((/152,78,163/))/256d
   new_purp  = todouble((/0,0,255/))/256d

   ; Do this in order to create an 2D array of multiple 
   ; colors in scatterplot
   color_list = new((/nmod+1/),"string")
   color_list = new((/nmod+1/),"string")
   color_list         = "black"
   color_list(nmod)   = "green"
   color_list(nmod-1) = "purple"
   
   ; for plot resources
   unique_colors_new = (/black,new_green,new_purp/)
   ; for loop below
   unique_colors     = (/color_list(0),color_list(nmod), \
                        color_list(nmod-1)/)
   ncolors           = dimsizes(unique_colors)

   ; 2D array with multiple colors for scatterplot
   y2d = new((/ncolors,nmod+1/),precision)      
   x2d = new((/ncolors,nmod+1/),precision)
   do i=0,ncolors-1
      ii  = ind(color_list.eq.unique_colors(i))
      nii = dimsizes(ii)

      y2d(i,:nii-1) = prop_ss(ii)
      x2d(i,:nii-1) = shum_ss(ii)
      delete(ii)
    end do

   res                    = True       ; resources for scatterplots                 
   res@xyMarkLineMode     = "Markers"     
   ; all scatterplot markers are circles except observations
   ; and model of interest
   mks = new((/3,3/),integer)
   mks = 16
   mks(:,1) = 16
   mks(:,2) = 16
   res@xyMarkers = mks       
   ; marker sizes are larger for observations and model of
   ; interest 
   sizes = new((/3,3/),double)
   sizes = 0.01
   sizes(:,1) = 0.015
   sizes(:,2) = 0.015
   res@xyMarkerSizes       = sizes        
   res@xyMarkerColors      = unique_colors_new
   res@gsnFrame            = False                   ; don't advance frame yet
   res@gsnDraw             = False                   ; don't draw plot

   res2                    = True                    ; resources for regression line               
   res2@xyDashPatterns     = 0                       ; solid line 
   res2@xyLineThicknesses  = 2                      
   res2@xyLineColor        = "grey"                  
   res2@gsnFrame           = False                   ; don't advance frame yet
   res2@gsnDraw            = False                   ; don't draw plot

   ; width of scatterplots
   vpw = .65*vpw
   aratio = .65
   res2@vpWidthF                = vpw                    
   res2@vpHeightF               = aratio*vpw
   res2@tmXBMajorOutwardLengthF = 0.0                ; draw tickmarks inward
   res2@tmXBMinorOutwardLengthF = 0.0                ; draw minor ticks inward
   res2@tmYLMajorOutwardLengthF = 0.0                ; draw tickmarks inward
   res2@tmYLMinorOutwardLengthF = 0.0                ; draw minor ticks inward
   res2@trXMaxF                 = scat1_xmax  
   res2@trXMinF                 = scat1_xmin
   res2@trYMaxF                 = scat1_ymax
   res2@trYMinF                 = scat1_ymin

   plot   = new(1,graphic)                     ; create a plot array for all panels
   ; abscissa and ordinate titles
   res2@tiXAxisString  = "Convective time scale (days)"
   res2@tiYAxisString  = "MJO amplitude (mm day~S~-1~N~)"

   color_list         = "black"
   color_list(nmod)   = "green"
   color_list(nmod-1) = "purple"
   do i=0,ncolors-1
      ii  = ind(color_list.eq.unique_colors(i))
      nii = dimsizes(ii)

      y2d(i,:nii-1) = amp(ii)
      x2d(i,:nii-1) = tau(ii)
      delete(ii)
   end do
   
   res2@trXMaxF                 = scat2_xmax
   res2@trXMinF                 = scat2_xmin
   res2@trYMaxF                 = scat2_ymax
   res2@trYMinF                 = scat2_ymin

   plot1 = gsn_csm_xy (wks4,x2d,y2d,res)        ; create plot
   plot(0) = gsn_csm_xy (wks4,tau,reg2,res2)     ; create plot

   ; add text with correlation cofficient
   txres               = True                            
   txres@txFontHeightF = corfh                      ; Set the font height
   tx1 = gsn_add_text(wks4,plot(0),"cor.="+sprintf("%4.2f", escorc(amp,tau)),xx2,yy2,txres)
   overlay(plot(0),plot1)

; create panel plot
   resP = True                         ; modify the panel plot

   resP@gsnMaximize     = False        ; maximize the panel plot size
   resP@gsnPanelRowSpec = True         ; specify the number of plots per row

   resP@txString     = ""           ; add a title

   gsn_panel(wks4,plot,(/2,2/),False) ; now draw as one plot
   delete([/wks4,plot/])

system("cp "+OBS_DATA+"/*.nc "+wk_dir+"/obs/netCDF")

print_clock("Finishing program")
end
