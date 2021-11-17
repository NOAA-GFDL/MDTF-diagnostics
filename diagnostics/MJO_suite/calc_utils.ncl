; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;                                      ;;;
;;;  Utility routines for NCL output     ;;;
;;;                                      ;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
;load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

;; Local variables for alll plot routines ;;

pwks = "ps"        ; Output format (ps,X11,png,gif)
_FillValue = -999  ; Missing value for FLOAT variables.


;;Routine bins input data into a number of bins.

function data_bin (invar:float,dbin:float,bin_first:float,nbins:integer) 

begin


; Construct bin arrays.

bin_last = bin_first+nbins*dbin
bin_low = fspan(bin_first,bin_last-dbin,nbins)
bin_high = bin_low+dbin
bin_out = new(nbins,"integer")
bin_out = 0

; Change array to 1-D array and find dimension

var1d = ndtooned(invar)
nd = dimsizes(var1d)


do id = 0,nd(0)-1
  do ibin = 0, nbins-1
    if (var1d(id).ge.bin_low(ibin).and.var1d(id).lt.bin_high(ibin)) then
      bin_out(ibin) = bin_out(ibin)+1
      break
    end if
  end do
end do

bin_out!0 = "bin_cen"
bin_out&bin_cen = 0.5*(bin_low+bin_high)

return(bin_out)

end


function dcycle_calc(invar:float,ptrin:file,ptri:file)
;;;;  Calculate mean diurnal cycle.

;; It's a little convoluted because the SCAM nc file does not contain anyy
;; absolute timing info - only relative info. Have to get starting Z time
;; from iop file

begin

  spd = 86400 ; Seconds per day

  lon  = doubletofloat_Wrap(ptrin->lon) 
  tsec_iop = ptri->tsec                     ; Info that has to come from IOP file.
  dt = tsec_iop(1)-tsec_iop(0) 

  ndims      = dimsizes(invar)
  nt         = ndims(0)                     ; In Variable time levels.
  np         = ndims(1)                     ; In variable pressure levels 
  ntspd      = spd/dt                       ; Time steps per day
  dc_weight  = new(ntspd,"float")           ; Number of samples for each itspd 
  dc_utime   = new(ntspd,"float")           ; Unadjusted diurnal cycle time 
  dc_atime   = new(ntspd+2,"float")         ; Adjusted diurnal cycle time (for t=0, local time and plotting) 
  dc_uvar    = new((/ntspd,np/),"float")    ; Unadjusted diurnal cycle 
  dc_avar    = new((/ntspd+2,np/),"float")  ; Adjusted diurnal cycle (for t=0, local time and plotting)      
  itspd      = 0                            ; tspd counter (0->ntspd-1)

; Create unadjusted diurnal cycle.

  dc_weight  = 0.
  dc_uvar    = 0.

  do it = 0, nt-1
    do ip = 0, np-1
      dc_uvar(itspd,ip) = dc_uvar(itspd,ip)+ invar(it,ip) ; Accumulate variable for this itspd
    end do
    dc_weight(itspd) = dc_weight(itspd)+1.           ; Increment weighting for this itspd
    itspd=itspd+1
    if (itspd .eq. ntspd) then 
      itspd=0
    end if
  end do
 
  do ip = 0, np-1
    dc_uvar(:,ip) = dc_uvar(:,ip)/dc_weight(:)  ; Re-scale according to weighting (incomplete days)
  end do  

; Adjust for local time, t=0
 
  tod_iop = tsec_iop(0)         ; Start time of day (tod) (seconds) from iop file.
  dc_utime = 0.                 ; Unadjusted time dimension.
  dc_atime = 0.                 ; Adjusted time dimension.
  tzone_iop = spd*lon/360.      ; Local time zone offset (seconds) from 00Z.
  toffset = tod_iop + tzone_iop ; Total offset time for DC.
  it_first = 0                  ; Location of itspd which is first local time point.
  
  if (isfilevar(ptrin, "time")) then ; Need to remove one timestep from model due to inics. on file.
    if (ptrin->time@long_name .eq. "elapsed model time") then
      toffset = toffset + dt
    end if
  end if

  if (toffset .gt. int2flt(spd)) then ; Total offset may be more than one day so - spd
    toffset = toffset-int2flt(spd)
  end if

  if (toffset .gt. 0.) then     ; Need to minus spd to get the +/- local 00 time split
    dc_utime = -int2flt(spd) 
  end if


  do itspd = 0, ntspd-1 
    dc_utime(itspd) =  dc_utime(itspd) + int2flt(spd*itspd)/int2flt(ntspd) + toffset 
    if (itspd.gt.0) then
      if (dc_utime(itspd)*dc_utime(itspd-1).le.0.) then
        it_first = itspd 
      end if
    end if
  end do

  dc_atime(1:ntspd-it_first)        = dc_utime(it_first:ntspd-1)
  dc_atime(ntspd-it_first+1:ntspd)  = int2flt(spd) + dc_utime(0:it_first-1) ; First values are always negative
  dc_atime(ntspd+1)                 = dc_atime(1)  + int2flt(spd)  ; Cyclic grid points for plotting.
  dc_atime(0)                       = dc_atime(ntspd)  - int2flt(spd)

  dc_avar(1:ntspd-it_first,:)       = dc_uvar(it_first:ntspd-1,:)
  dc_avar(ntspd-it_first+1:ntspd,:) = dc_uvar(0:it_first-1,:)
  dc_avar(ntspd+1,:)                = dc_avar(1,:)    ; Cyclic grid points for plotting.
  dc_avar(0,:)                      = dc_avar(ntspd,:)    ; Cyclic grid points for plotting.

 
  dc_avar!0 = "time"                  ; Attach time attribute
  dc_avar&time = dc_atime/3600.       ; Make it hours
  dc_avar&time@units = "hours"
  dc_avar&time@long_name = "Local hour" 

  if (np.gt.1) then
    dc_avar!1 = "lev"                 ; Attach lev attribute
    dc_avar&lev = invar&lev          
    dc_avar&lev@units = "hPa"
    dc_avar&lev@long_name = "Pressure (mb)"
  end if

  return (dc_avar)

end






function dcycle_calc_cam(invar:float)
;;;;  Calculate mean diurnal cycle from CAM hourly output of a 2-D variable.

begin

  spd = 86400 ; Seconds per day

  ndims      = dimsizes(invar)
  nlon       = ndims(2)                   ; In Variable time levels.
  nlat       = ndims(1)                   ; In variable pressure levels 
  ntime      = ndims(0)

  time_ut    = cd_calendar(invar&time, 0)
; Following construct is to grab dtstep(hours) and checks to see iff it crosses days my finding the minimum of
; the first two timesteps.
  dt_days    = min((/fabs((time_ut(1,3)-time_ut(0,3))/24.),fabs((time_ut(2,3)-time_ut(1,3))/24.)/)) 

  ntspd      = round(1./dt_days,3)                ; Time steps per day (has to be integer value)
  dc_uvar    = new((/ntspd,nlat,nlon/),"float")   ; Unadjusted diurnal cycle 

  itspd      = 0                                  ; tspd counter (0->ntspd-1)

  print( "*dcycle_calc_cam - 1/3* - Calculating time info ("+ntspd+" time-steps per day)")

; Create unadjusted diurnal cycle.

  time_24hr = fspan(0.,24.-dt_days*24.,ntspd)

  dc_uvar!0 = "time"
  dc_uvar&time = time_24hr       ; Make it hours
  dc_uvar&time@units = "local hour"
  dc_uvar&time@long_name = "Local hour"

  dc_uvar!1 = "lat"
  dc_uvar&lat = invar&lat
  
  dc_uvar!2 = "lon"
  dc_uvar&lon = invar&lon

  dc_weight = dc_uvar
  dc_weight = 0.
  dc_uvar = 0.
  
  print( "*dcycle_calc_cam - 2/3* - Creating unadjusted diurnal cycle, with missing and incomplete day weighting")

; Weighting for missing data and time-steps for each itspd=0,ntspd-1 array value

  do it = 0, ntime-1
    dc_uvar(itspd,:,:)   = where(ismissing(invar(it,:,:)),dc_uvar(itspd,:,:),dc_uvar(itspd,:,:)+invar(it,:,:))
    dc_weight(itspd,:,:) = where(ismissing(invar(it,:,:)),dc_weight(itspd,:,:),dc_weight(itspd,:,:)+1.)
    itspd=itspd+1
    if (itspd .eq. ntspd) then 
      itspd=0
    end if
  end do

  print( "*dcycle_calc_cam - 3/3* - Apply correct weighting to diurnal cycle for incomplete days")

; Zero weights at alll itspds occur for missing data regions, but we cannot divide by 0 so set to 

  print(" -Weight range =  "+min(dc_weight)+" to "+max(dc_weight))
  
  dc_weight = where(dc_weight.ne.0,dc_weight,dc_weight@_FillValue)
  dc_uvar = dc_uvar/dc_weight

  print("*Composite diurnal cycle complete")

  return (dc_uvar)

end


function dcycle_calc_trmm(invar:float)
;;;;  Calculate mean diurnal cycle from CAM hourly output of a 2-D variable.

begin

  spd = 86400 ; Seconds per day

  ndims      = dimsizes(invar)
  nlon       = ndims(2)                   ; In Variable time levels.
  nlat       = ndims(1)                   ; In variable pressure levels 
  ntime      = ndims(0)
  dt_days    = doubletofloat(invar&time(1)-invar&time(0))
  ntspd      = round(1./dt_days,3)                ; Time steps per day (has to be integer value)
  time_gmt   = new(ntspd,"float")                 ; GMT/Z time with offset for start time of data 


  dc_weight  = new((/ntspd,nlat,nlon/),"float")    ; Number of samples for each itspd (some missing values for TRMM)
  dc_uvar    = new((/ntspd,nlat,nlon/),"float")   ; Unadjusted diurnal cycle 
  dc_avar    = new((/ntspd,nlat,nlon/),"float")   ; Adjusted diurnal cycle (for t=0, local time and plotting)      
  itspd      = 0                                  ; tspd counter (0->ntspd-1)

; Create unadjusted diurnal cycle.

  dc_weight  = 0.
  dc_uvar    = 0.
  dc_avar = 0.

  time_24hr = fspan(0.,24.-dt_days*24.,ntspd)

  dc_avar!0 = "time"
  dc_avar&time = time_24hr       ; Make it hours
  dc_avar&time@units = "local hour"
  dc_avar&time@long_name = "Local hour"

  dc_avar!1 = "lat"
  dc_avar&lat = invar&lat
  
  dc_avar!2 = "lon"
  dc_avar&lon = invar&lon
  
  dc_uvar = dc_avar

  dc_weight!1 = "lat"
  dc_weight&lat = invar&lat
  
  dc_weight!2 = "lon"
  dc_weight&lon = invar&lon

  print( "*dcycle_calc_trmm - 1/4* - Creating unadjusted diurnal cycle")

  invar = where(invar.lt.0.,0.,invar)
  do it = 0, ntime-1
;    print(it+" "+ntime)

; Maskk out missing value regions for summ and weight.
    dc_uvar(itspd,:,:)   = where(ismissing(invar(it,:,:)),dc_uvar(itspd,:,:),dc_uvar(itspd,:,:)+invar(it,:,:))
    dc_weight(itspd,:,:) = where(ismissing(invar(it,:,:)),dc_weight(itspd,:,:),dc_weight(itspd,:,:)+1.)
    itspd=itspd+1
    if (itspd .eq. ntspd) then 
      itspd=0
    end if
  end do
   


  print( "*dcycle_calc_trmm - 2/4* - Apply correct weighting to diurnal cycle")

  dc_weight =  where(dc_weight.eq.0.,dc_weight@_FillValue,dc_weight) ; Change zero values to prevent/0 problem
  dc_uvar = dc_uvar/dc_weight   ; Re-scale according to weighting

; Adjust for local time, t=0
; Check start times from time coordinate.

   print( "*dcycle_calc_trmm - 3/4* - Adjust for local timing")

  if (invar&time@units.eq."days since 00Z 01 Jan 1998" .or. invar&time@units.eq."days since 1997-01-01 00:00:0.0") then
    print(invar&time@units)
    print("Recognized TRMM time info...")
  else
    if (invar&time@units.eq."days since 1977-01-01 00:00:00" .or. invar&time@units.eq."days since 0000-01-01 00:00:00" \
      .or.  invar&time@units.eq."days since 0001-01-01 00:00:00") then
      print(invar&time@units)
      print("Recognized CAM/CCSM time info...")
    else
      print(invar&time@units)
      print("Unrecognized time info ... exiting")
    exit
    end if
  end if

  t_zstart = doubletofloat(invar&time(0)-int2dble(doubletoint(invar&time(0))))     ; Start time of day (Z) (seconds) from input file.
  it_first = 0                  ; Location of itspd which is first local time point.
  time_gmt = t_zstart*ntspd+fspan(0.,1.-dt_days,ntspd) ; Z time based on first time.

; Loop over each longitude for the time offset.


  print( "*dcycle_calc_trmm - 4/4* - Adjust for local timing")

  do ilon=0,nlon-1

    time_lon = doubletofloat(invar&lon(ilon)/360.)      ; Local time zone offset (seconds) from 00Z.
    do itime=0,ntspd-1
      time_loc = time_gmt(itime)-t_zstart-time_lon ; Local time after adjustments.
      if (time_loc .lt. 0.) then
        time_loc = time_loc+1.
      end if
      if (time_loc .gt. 1.) then
        time_loc = time_loc-1.
      end if
      dc_avar(lon|ilon,lat|:,time|itime) = linint1 (time_gmt,dc_uvar(lon|ilon,lat|:,time|:), True, time_loc, 0) 
      if (ilon.eq.140) then
;        print("time= "+itime+" "+time_loc)
;        print("uvar = "+dc_uvar(:,43,140))
;        print("avar = "+dc_avar(itime,43,140))        
        
      end if 
    end do
  end do


 
  return (dc_avar)

end



function compute_daily_anom(invar:float)
begin

time_coord = getenv("time_coord")
lon_coord = getenv("lon_coord")
lat_coord = getenv("lat_coord")

time = invar&$time_coord$
time@calendar = "noleap"
t_utc = cd_calendar(time,0)
nt = dimsizes(time)

lon = invar&$lon_coord$
nlon = dimsizes(lon)
lat = invar&$lat_coord$
nlat = dimsizes(lat)

var_clim = new((/12,31,nlat,nlon/),"float")
weight_clim = new((/12,31/),"float")

max_day = new((/12/),"integer")
max_day = (/31,28,31,30,31,30,31,31,30,31,30,31/)

; calculate climatology

var_clim = 0.
weight_clim = 0.
do n = 0,nt-1
   var_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1,:,:)=var_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1,:,:)+invar(n,:,:)
   weight_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1) = weight_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1)+1.
end do

do month = 0,11
do day = 0,max_day(month)-1
   var_clim(month,day,:,:) = var_clim(month,day,:,:)/weight_clim(month,day)
;   var_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1,:,:) = var_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1,:,:)/weight_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1)
end do
end do


var_anom = invar
var_anom = 0.
do n=0,nt-1
     var_anom(n,:,:) = invar(n,:,:) - var_clim(tointeger(t_utc(n,1))-1,tointeger(t_utc(n,2))-1,:,:)
end do

return(var_anom)

end































procedure multi_plot_ts(rnames:string,mplot:string,munits:string,mscale:float,cmin:float,cmax:float,cgap:float,acmin:float,acmax:float,acgap:float,vsmooth:integer,plot_name:string,ptrt:file,ptrc:file,iplot:string,iscale:float,ptri:file)
; Plot multi level postscript files.
; First full fields (+optional iop field)
; Difference from between runs (+optional difference with iop)

begin

; Check variable is present.

; Test
  if (num(getfilevarnames(ptrt).eq.mplot).eq.0) then   ; If test does not exist then exit.
    print ("-- ERROR: "+mplot+" not found in nc test file - plot will not be produced")
    return
  else
    vart  = ptrt->$mplot$
  end if 

; Control.  
  if (num(getfilevarnames(ptrc).eq.mplot).eq.0) then   ; BUT iff control does not exist thenn fill with MISSING #s.
    print ("-- ERROR: "+mplot+" not found in nc ctrl file - filling with MISSING #s")  
    varc = vart
    varc = (/_FillValue/)
  else
    varc  = ptrc->$mplot$
  end if 
 
; Stuff always needed

  file_out = plot_name+mplot

  print (mplot+" in "+file_out)

  wks = gsn_open_wks(pwks,file_out)
  gsn_define_colormap(wks,"amwg")  ; choose a colormap

 
  vart&time = vart&time/24. ; Scale for days rather than hours.
  varc&time = varc&time/24. 

  vartp = mscale*vart(:,:,0,0)
  varcp = mscale*varc(:,:,0,0)

  mtime = ptrt->time

; Panel resources

  pan = True
  pan@gsnMaximize = True  
  pan@gsnPaperOrientation = "Portrait"
  pan@gsnPaperMargin = 0.
  pan@gsnPanelYWhiteSpacePercent = 2
  pan@txString=vart@long_name

; Individual plot resources

  res = True
  res@gsnDraw                = False    
  res@gsnFrame               = False


  res@lbBoxMinorExtentF     = 0.15    
  res@lbOrientation         = "Vertical" 
  res@lbLabelsOn            = True
  res@lbLabelFontHeightF    = 0.02                                                
  res@lbLabelAutoStride     = True
  res@tiXAxisFontHeightF    = 0.02
  res@tiXAxisString         = "Days since "+ptrt->nbdate
  res@tiYAxisFontHeightF    = 0.02
  res@tiYAxisString         = "Pressure (mb)"
   
;  res@tmXBMinorOn           = False
  res@tmYLMinorOn           = False
  res@tmXTMinorOn           = False
  res@tmYRMinorOn           = False
  res@tmXTOn                = False

  res@gsnRightString        = munits 
  res@gsnLeftString         = mplot
  res@gsnStringFontHeightF  = 0.02
  res@gsnCenterStringFontHeightF  = 0.03

  res@cnFillOn             = True          ; turn on color
  
  res@gsnSpreadColors      = True          ; use full range of colormap
  res@cnLevelSelectionMode = "ManualLevels" 
  res@cnLevelSpacingF      = cgap
  res@cnMinLevelValF       = cmin
  res@cnMaxLevelValF       = cmax 
  res@vpWidthF             = 0.95          ; change aspect ratio of plot
  res@vpHeightF            = 0.33
  res@trYReverse           = True      

  vartp!0 = "time"  ;Reconstruct meta data as the time dimension has changed.
  vartp!1 = "lev"
  
  vartp&time = mtime
  vartp&lev  = vart&lev
  vartp&lev@units = "hPa"
  vartp&lev@long_name = "Pressure Levels"
  copy_VarMeta(vartp,varcp)

; Final plotting and thenn obs.

  cnplot = new(3,"graphic")

  res@gsnCenterString = rnames(0)
  
  cnplot(0)  = gsn_csm_pres_hgt(wks,vartp({lev|100:1000},time|:),res) 
  
  res@gsnCenterString = rnames(1)
  cnplot(1)  = gsn_csm_pres_hgt(wks,varcp({lev|100:1000},time|:),res) 
  
; Stuff to add if iop data available to plot.

  if (iplot .ne. "x") then
    if (num(getfilevarnames(ptri).eq.iplot).eq.0) then
      print ("  -- ERROR: "+iplot+" not found in nc input file - only model fields will be plotted")      
    else
      vari = ptri->$iplot$
      vari&time = mtime          ; Add the time coordinate in seconds.
      vari&lev  = vari&lev*0.01  ; Re-scale plev coordinate and change units.
      vari&lev@units = "hPa"  
      
      varip = iscale*vari(:,:,0,0)
      copy_VarMeta(vari,varip)
      
      res@gsnCenterString = rnames(2)
      cnplot(2) =  gsn_csm_pres_hgt(wks,varip({lev|100:1000},time|:),res)
    end if
  end if

  gsn_panel(wks,cnplot,(/3,1/),pan)   

;;;; 
;;;; Difference plots now
;;;;

; Stuff always needed

  file_out = plot_name+mplot+"-diff"

  print (mplot+"diffs. in "+file_out)

; Changed resources for diffs.

  wks = gsn_open_wks(pwks,file_out)
  gsn_define_colormap(wks,"amwg")  ; choose a colormap

  res@cnLevelSpacingF      = acgap
  res@cnMinLevelValF       = acmin
  res@cnMaxLevelValF       = acmax 

  vartp_diff = vartp-varcp
  copy_VarMeta(vartp,vartp_diff)
  
  res@gsnCenterString = rnames(0)+" minus "+ rnames(1)
  cnplot(0)  = gsn_csm_pres_hgt(wks,vartp_diff({lev|100:1000},time|:),res) 

; Some interpolation between grids now needed (iop to model grid)
; Only if obs exist.

  if (iplot .ne. "x") then
    if (num(getfilevarnames(ptri).eq.iplot).eq.0) then
      if (iplot .ne. "x") then
        print ("  -- ERROR: "+iplot+" not found in nc input file - only model fields will be plotted")
      end if
    else
      varip_mlevs = int2p(varip&lev,varip,vartp&lev,-1)
      copy_VarMeta(vartp,varip_mlevs)
      
      vartp_mobs = vartp-varip_mlevs
      varcp_mobs = varcp-varip_mlevs
      copy_VarMeta(vartp,vartp_mobs)
      copy_VarMeta(vartp,varcp_mobs)
      
      res@gsnCenterString = rnames(0)+" minus "+ rnames(2)
      cnplot(1)  = gsn_csm_pres_hgt(wks,vartp_mobs({lev|100:1000},time|:),res) 
      res@gsnCenterString = rnames(1)+" minus "+ rnames(2)
      cnplot(2) =  gsn_csm_pres_hgt(wks,varcp_mobs({lev|100:1000},time|:),res)
    
    end if
  end if
  
  gsn_panel(wks,cnplot,(/3,1/),pan)

end






procedure single_plot_dc(rnames:string,mplot:string,munits:string,mscale:float,vmin:float,vmax:float,vsmooth:integer,plot_name:string,ptrt:file,ptrc:file,iplot:string,iscale:float,ptri:file)

; Plot single level postscript files.

begin

; Test
  if (num(getfilevarnames(ptrt).eq.mplot).eq.0) then   ; If test does not exist then exit.
    print ("-- ERROR: "+mplot+" not found in nc test file - plot will not be produced")
    return
  else
    vart  = ptrt->$mplot$
  end if 

; Control.  
  if (num(getfilevarnames(ptrc).eq.mplot).eq.0) then   ; BUT if control doesnot's exist then fill with MISSING #s.
    print ("-- ERROR: "+mplot+" not found in nc ctrl file - filling with MISSING #s")  
    varc = vart
    varc = (/_FillValue/)
  else
    varc  = ptrc->$mplot$
  end if  

; Stuff always needed
  file_out = plot_name+mplot
  print (mplot+" in "+file_out)

  wks = gsn_open_wks(pwks,file_out)

; Make arrays 2D for dcycle_calc routine.
  
  dvart = dimsizes(vart)

  vartp = new((/dvart(0),1/),"float")
  varcp = new((/dvart(0),1/),"float")
  
  vartp(:,0) = mscale*vart(:,0,0)
  varcp(:,0) = mscale*varc(:,0,0)

; Panel resources

  pan = True
  pan@gsnMaximize = True  
  pan@gsnPaperOrientation = "Portrait"
  pan@gsnPaperMargin = 0.
  pan@gsnPanelYWhiteSpacePercent = 2

; Plot resources
  
  res = True  
  res@gsnDraw                = False    
  res@gsnFrame               = False   
  res@gsnMaximize            = True
  res@gsnPaperOrientation    = "Portrait"
  res@tiMainString           = vart@long_name
  res@xyLineColors           = (/"Red","Blue","Black"/)
  res@xyDashPatterns         = (/0,1,0/)
  res@xyLineThicknesses      = (/3,3,3/)
  res@trYMinF                = vmin
  res@trYMaxF                = vmax
  res@trXMinF                = 0
  res@trXMaxF                = 24
  res@pmLegendDisplayMode    = "Always"
  res@pmLegendSide           = "Bottom" 
  res@pmLegendWidthF         = 0.4                ; Change width and
  res@pmLegendHeightF        = 0.1                ; height of legend.  
  res@lgLabelsOn             = True                   ; no default lables
  res@lgPerimOn              = False  
  res@xyExplicitLegendLabels = rnames

  if (vmin .gt. vmax) then  ; Reverse the axis to give a better sense of top and bottom of column.
    res@trYReverse = True
    res@trYMinF                = vmax
    res@trYMaxF                = vmin
  end if

  res@vpWidthF               = 0.95          ; change aspect ratio of plot
  res@vpHeightF              = 0.33
  
  if (mscale .ne. 1.) then 
    res@tiYAxisString = munits 
  else
    res@tiYAxisString = vart@units
  end if

; Stuff to add if iop data available to plot.

  plot = new(3,"graphic")

; A bit of minipulation for a 2d dcycle_calc routine.
  







  vartp_dc = dcycle_calc(vartp,ptrt,ptri)  ; Calculate model diurnal cycles.
  varcp_dc = dcycle_calc(varcp,ptrc,ptri)
  
  if (iplot .eq. "x") then
    plot(0) = gsn_csm_xy(wks,vartp_dc&time,(/vartp_dc(:,0),varcp_dc(:,0)/),res)
  else
    if (num(getfilevarnames(ptri).eq.iplot).eq.0) then
      print ("  -- ERROR: "+iplot+" not found in nc input file - only model fields will be plotted")
      plot(0) = gsn_csm_xy(wks,vartp_dc&time,(/vartp_dc(:,0),varcp_dc(:,0)/),res)
    else
      vari = ptri->$iplot$
      dvari = dimsizes(vari)
      varip = new((/dvari(0),1/),"float")
      varip(:,0) = iscale*vari(:,0,0)
      copy_VarMeta(vari,varip)
      varip_dc = dcycle_calc(varip,ptri,ptri) ; Calculate observational diurnal cycle
      plot(0) = gsn_csm_xy(wks,varip_dc&time,(/vartp_dc(:,0),varcp_dc(:,0),varip_dc(:,0)/),res)    
    end if
  end if

; Panel it like the contour plots to give the same size

  gsn_panel(wks,plot,(/3,1/),pan)   

end













procedure multi_plot_dc(rnames:string,mplot:string,munits:string,mscale:float,cmin:float,cmax:float,cgap:float,acmin:float,acmax:float,acgap:float,vsmooth:integer,plot_name:string,ptrt:file,ptrc:file,iplot:string,iscale:float,ptri:file)

; Plot multi level diurnal cycle postscript files.
; First full fields (+optional iop field)
; Second full fields minnus daily mean (+optional iop field).

begin

; Test
  if (num(getfilevarnames(ptrt).eq.mplot).eq.0) then   ; If test does not exist then exit.
    print ("-- ERROR: "+mplot+" not found in nc test file - plot will not be produced")
    return
  else
    vart  = ptrt->$mplot$
  end if 

; Control.  
  if (num(getfilevarnames(ptrc).eq.mplot).eq.0) then   ; BUT if control doesnot's exist then fill with MISSING #s.
    print ("-- ERROR: "+mplot+" not found in nc ctrl file - filling with MISSING #s")  
    varc = vart
    varc = (/_FillValue/)
  else
    varc  = ptrc->$mplot$
  end if  


; Full fields 
  file_out = plot_name+mplot
  print (mplot+" in "+file_out)
  wks = gsn_open_wks(pwks,file_out)
  gsn_define_colormap(wks,"amwg")  ; choose a colormap

; Anomalous fields  
  file_out = plot_name+mplot+"-anom"
  print (mplot+" anoms. in "+file_out)
  awks = gsn_open_wks(pwks,file_out)
  gsn_define_colormap(awks,"amwg")  ; choose a colormap

; Extract variables

  vartp = mscale*vart(:,:,0,0)
  varcp = mscale*varc(:,:,0,0)

  copy_VarCoords_2(vart,vartp)
  copy_VarCoords_2(varc,varcp) 

; Panel resources

  pan = True
  pan@gsnMaximize = True  
  pan@gsnPaperOrientation = "Portrait"
  pan@gsnPaperMargin = 0.
  pan@gsnPanelYWhiteSpacePercent = 2
  pan@txString=vart@long_name+" - Diurnal Cycle"

; Individual plot resources

  res = True
  res@gsnDraw                = False    
  res@gsnFrame               = False   
  
  res@lbBoxMinorExtentF     = 0.15    
  res@lbOrientation         = "Vertical" 
  res@lbLabelsOn            = True
  res@lbLabelFontHeightF    = 0.02                                                
  res@lbLabelAutoStride     = True
  res@tiXAxisFontHeightF    = 0.02
  res@tiYAxisFontHeightF    = 0.02
  res@tiYAxisString         = "Pressure (mb)"
   
;  res@tmXBMinorOn           = False
  res@tmYLMinorOn           = False
  res@tmXTMinorOn           = False
  res@tmYRMinorOn           = False
  res@tmXTOn                = False
  res@tmXBMode              = "Manual"
  res@tmXBPrecision         = 2
  res@tmXBTickStartF        = 0
  res@tmXBTickEndF          = 24
  res@tmXBTickSpacingF      = 4

  res@gsnRightString        = munits 
  res@gsnLeftString         = mplot
  res@gsnStringFontHeightF  = 0.02
  res@gsnCenterStringFontHeightF  = 0.03

  res@cnFillOn             = True          ; turn on color
  
  res@gsnSpreadColors      = True          ; use full range of colormap
  res@cnLevelSelectionMode = "ManualLevels" 
  res@cnLevelSpacingF      = cgap
  res@cnMinLevelValF       = cmin
  res@cnMaxLevelValF       = cmax 
  res@vpWidthF             = 0.95          ; change aspect ratio of plot
  res@vpHeightF            = 0.33
  res@trYReverse           = True  


; Add a starting value onto model output for exact comparison with obs.
; Plotting with anomaly plotting and then optional obs.

  cnplot  = new(3,"graphic")
  acnplot = new(3,"graphic")

  ares = res
  ares@cnLevelSpacingF      = acgap
  ares@cnMinLevelValF       = acmin
  ares@cnMaxLevelValF       = acmax 

; Calculate DC

  vartp_dc  = dcycle_calc(vartp,ptrt,ptri)
  varcp_dc  = dcycle_calc(varcp,ptrc,ptri)
 
; Plot full model fields

  res@gsnCenterString = rnames(0)
  cnplot(0)  = gsn_csm_pres_hgt(wks,vartp_dc({lev|100:1000},{time|-1:24}),res) 
  
  res@gsnCenterString = rnames(1)
  cnplot(1)  = gsn_csm_pres_hgt(wks,varcp_dc({lev|100:1000},{time|-1:25}),res) 

; Plot anomolous fields   
  vartp_dc(lev|:,time|:) = dim_rmvmean_Wrap(vartp_dc(lev|:,time|:))
  varcp_dc(lev|:,time|:) = dim_rmvmean_Wrap(varcp_dc(lev|:,time|:))

  ares@gsnCenterString = rnames(0)
  acnplot(0)  = gsn_csm_pres_hgt(awks,vartp_dc({lev|100:1000},{time|-1:25}),ares) 
  
  ares@gsnCenterString = rnames(1)
  acnplot(1)  = gsn_csm_pres_hgt(awks,varcp_dc({lev|100:1000},{time|-1:25}),ares) 


; Stuff to add if iop data available to plot.

  if (iplot .ne. "x") then
    if (num(getfilevarnames(ptri).eq.iplot).eq.0) then
      print ("  -- ERROR: "+iplot+" not found in nc input file - only model fields will be plotted")
    else
      vari = ptri->$iplot$
      varip = iscale*vari(:,:,0,0)
      copy_VarCoords_2(vari,varip)  ; Retain coordinates for plotting.
      varip&lev  = varip&lev*0.01     ; Scale for hPa 

      varip_dc =  dcycle_calc(varip,ptri,ptri)
      res@gsnCenterString = rnames(2)
      cnplot(2) =  gsn_csm_pres_hgt(wks,varip_dc({lev|100:1000},{time|-1:25}),res)
      varip_dc(lev|:,time|:) = dim_rmvmean_Wrap(varip_dc(lev|:,time|:))
      ares@gsnCenterString = rnames(2)
      acnplot(2) =  gsn_csm_pres_hgt(awks,varip_dc({lev|100:1000},{time|-1:25}),ares)
    end if
  end if

  apan = pan
  apan@txString=vart@long_name+" - Anom. Diurnal Cycle"

  gsn_panel(wks, cnplot, (/3,1/),pan)   
  gsn_panel(awks,acnplot,(/3,1/),pan)

end



































