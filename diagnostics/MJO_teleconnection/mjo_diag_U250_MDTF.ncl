; This file is part of the MJO_teleconnection module of the MDTF code package (see LICENSE.txt)

;------------------------------------------------------------------------------------
;CMIP 250mb zonal wind
; Written By Stehnaie Handerson
; Edited By Bohar Singh 
; Department of atmpspheric Sceince Colorado State University Fort Collins
;------------------------------------------------------------------------------------

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin
print("--------------------------------------------------------------------------")
print("              ** Calculating 250-hPa Zonal Wind RMS Error **              ")
print("--------------------------------------------------------------------------")
;-- scalars and constants --
yrs = ispan(1979,2016,1)
dim_yrs = dimsizes(yrs)-1   	  ;number of DJF seasons
dim_mo = tointeger(dim_yrs * 3.)

   ymdStrt = tointeger(getenv("strtdy"))                         ; start yyyymmdd
   ymdLast = tointeger(getenv("lastdy")) 
   yrStrt  = ymdStrt/10000
   yrLast  = ymdLast/10000
   
   print("starting year"+yrStrt)
   print("Last year"+yrLast)
g   = 9.81              ;- Gravity acceleration [m/s^2]
;-----Model------
Model= getenv("CASENAME")

;-----------------------------------------------------------------------------------------
;-- read in reanalysis values of monthly zonal wind --
;-----------------------------------------------------------------------------------------
print("Reading DJF mean ERA-I(1979-2016) zonal wind data .....")

;All pressure level data files are in one netcdf, DJF months only

;---------------------------------------------------------------------------------
;--directory for output files--
;---------------------------------------------------------------------------------
dirobs  = getenv("OBS_DATA")+"/"         ;Output data directory
diro    = getenv("WK_DIR")+"/model/netCDF/" 
filobsU = "ERAi.1979_2016.DJF.mean.nc"
filu250   = getenv("u250_file")                   ; input file

print("Output data path :" + diro)
print("Input data file for Observed U250 :" + filobsU)
print("Input data file for"+Model+ "U250 :" + filu250)
print("--------------------------------------------------------------------------")
u250var = getenv("u250_var")
;-----------------------------------------------------------------------------------------
;                 -- read in reanalysis values of monthly zonal wind --
;-----------------------------------------------------------------------------------------

  a = addfile(dirobs+filobsU,"r")   ;(lat,lon), 
  lat = a->lat       ;flip latitudes so that they go S -> N
  lon = a->lon      ;must flip data longitudes (original -180 to 180)
 
 Ut = a->U   ;zonal wind        [m/s]
 Ut@_FillValue=-999

;-- calculate DJF mean --
print("calculating DJF mean")
U = Ut  ;lat, lon
U@_FillValue=-999

;clean up
delete(Ut)
print("Done")
print("--------------------------------------------------------------------------")

;dirf = "./"
;-----------------------------------------------------------------------------------------
;                   -- read in model values of monthly zonal wind --
;-----------------------------------------------------------------------------------------
print("Reading Model 250hPa zonal wind data")

 b =addfile(filu250,"r")   ;(time,lat,lon), 

;--- read in time ---
   temp_time = b->time

   calend = temp_time@calendar
   ymd     = cd_calendar(temp_time, -2)            ; yyyymmdd

    iStrt   = ind(ymd.eq.ymdStrt)              ; index start
    iLast   = ind(ymd.eq.ymdLast)              ; index last 

    Ut  = tofloat(b->$u250var$(iStrt:iLast,:,:))	 	;type: double orig.
 Ut@_FillValue=-999


 lat2 = tofloat(b->lat)		;type: double orig.  -90 to 90
 lon2 = tofloat(b->lon)		;0-360


;--- read in time ---
 time = b->time(iStrt:iLast)
 
;   print(time@calendar)
 

 if(time@calendar .ne. "360_day")  ;Check if calender is not 360 days
  utc_date = cd_calendar((b->time(iStrt:iLast)), 0)
  year   = tointeger(utc_date(:,0))
  month  = tointeger(utc_date(:,1))
  days   = tointeger(utc_date(:,2))
  ;clean up
;  delete(utc_date)
 end if


delete(b)
delete(time)

;-- Isolate DJF days -- Excluding 29 feb, Jan, Feb of first year and Dec. of last year
print("Isolating DJF days -- Excluding 29 feb, Jan, Feb of first year and Dec. of last year")


    DJF_days = ind((month .le. 2 .or. month .eq. 12) .and. (.not.(month .eq. 2 .and. days .eq. 29) .and. (.not.(year .eq. year(0) .and. month .le. 2)) .and. (.not.(year .eq. max(year) .and. month .eq. 12))))

  print("Total DJF days: " + dimsizes(DJF_days))  ;3*30

;debug  date_str =  sprinti("%0.4i", year(DJF_days)) +  sprinti("%0.2i",month(DJF_days)) +sprinti("%0.2i ", days(DJF_days))
 ; print(date_str)


Ua = Ut(DJF_days,:,:)
Ua@_FillValue = -999

;get dimensions
 dim_lat = dimsizes(lat2)
 dim_lon = dimsizes(lon2)

print("latitude dimension: " + dim_lat)
print("longitude dimension: " + dim_lon)

;clean up
delete(DJF_days)
delete(Ut)
delete(year)
delete(month)

;-- calculate DJF mean --
print("Calculating  DJF mean of Model data")
    
    U_CMIP5t = dim_avg_n(Ua,0)
    U_CMIP5t@_FillValue=-999
    delete(Ua)
 
print("Done")
print("--------------------------------------------------------------------------")
 U_CMIP5t!0 = "lat2"
 U_CMIP5t!1 = "lon2"
 U_CMIP5t&lat2 = lat2
 U_CMIP5t&lon2 = lon2

;-- interpolate to reference resolution --
print("Interpoling to reference resolution --")

 
;  lat =latGlobeFo(dimsizes(lat), "lat", "latitude", "degrees_north")
;  lon =lonGlobeFo(dimsizes(lon), "lon", "longitude", "degrees_east")

   U_CMIP5 = new((/dimsizes(lat),dimsizes(lon)/),typeof(U_CMIP5t))
   U_diff = new((/dimsizes(lat),dimsizes(lon)/),typeof(U_CMIP5t)) 

   U_CMIP5 = linint2 (lon2,lat2,U_CMIP5t,True,lon,lat, 0)
   U_CMIP5@_FillValue = -999
print("Done")
print("Calculating Diffrenerce between model and observations")
   U_diff(:,:) = U_CMIP5(:,:) - U
   U_diff@_FillValue = -999
print("Done")
delete(U_CMIP5t)
delete(lon2)
delete(lat2)

;--generate plot--

  U_CMIP5!0   = "lat" 
  U_CMIP5!1   = "lon" 
  U_CMIP5&lat = lat      
  U_CMIP5&lon = lon

  U_diff!0   = "lat" 
  U_diff!1   = "lon" 
  U_diff&lat = lat      
  U_diff&lon = lon

  U!0   = "lat" 
  U!1   = "lon" 
  U&lat = lat      
  U&lon = lon

;Getting index ovet the North Pacific region for U250 RMSE calculation
; Domain (15N-60N,110E-120W)

 ind_lat = ind(lat .ge. 15 .and. lat .lt. 60)
 ind_lon = ind(lon .le. 250 .and. lon.ge. 120)
;print(ind_lon)

 U_modt = U_CMIP5(ind_lat,ind_lon)
 U_obst = U(ind_lat,ind_lon)
 latnew = lat(ind_lat)
; print(latnew)
 U_mean = dim_avg_n(U_modt,1)

;calculate RMS error
 print("Calculating RMS error")
   clat = cos(0.01745329*latnew)


   rmsU1 = wgt_arearmse(U_modt,U_obst, clat, 1.0, 0)


delete(clat)

print("U250 zonal wind RMSE over (15N-60N,110E-120W): "+Model + "    " + rmsU1)

;---------------------------------------------------
; RMSE calculation over 
; Finding the Latitudinal maxima of jets
;---------------------------------------------------
  lat_maxt = ind(U_mean(:) .eq. (max(U_mean(:))))
  
;  print(Model + "  " + latnew(lat_maxt))

  lat_min = latnew(lat_maxt) - 5.
  lat_maxim = latnew(lat_maxt) + 5.

  lat_max = ind(latnew .ge. lat_min .and. latnew .le. lat_maxim)


  U_mod = new((/dimsizes(lat_max),dimsizes(ind_lon)/),typeof(U_CMIP5))
  lat_new = new((/dimsizes(lat_max)/),float) 

  
 lat_new = latnew(lat_max)
  U_mod(:,:) = U_modt(lat_max,:)

  delete(lat_max)
  delete(lat_min)
  delete(lat_maxim)
  delete(lat_maxt)


   U_mean_obs = dim_avg_n(U_obst,1)
   lat_maxobst = ind(U_mean_obs .eq. max(U_mean_obs))

  lat_min = latnew(lat_maxobst) - 5.
  lat_maxim = latnew(lat_maxobst) + 5.

  lat_maxobs = ind(latnew .ge. lat_min .and. latnew .le. lat_maxim)


  U_obs = U_obst(lat_maxobs,:)

;calculate RMS error
print("RMS error")

; rmsU = new((/dimsizes(Model)/),typeof(U_CMIP5))

   clat = cos(0.01745329*lat_new)
   rmsU = wgt_arearmse(U_mod,U_obs, clat, 1.0, 0)
;   printVarSummary(rmsU)
  delete(clat)
 


print("U250 Zonal wind RMSE aroud Jet maxima at Model between (15N-60N,110E-120W)" + "    " + rmsU)
print("RMSE calculation for model: " + Model + " is completed")


print("--------------------------------------------------------------------------")
print("Reading zonal wind RMS error data for CMIP5 Models")
print("Data Path: "+ dirobs )
print("RMS error data file for CMIP5 Models: "+"U250_RMS_jetext and U250_RMS ")
;-- read in zonal wind RMS error data --
 RMS_U_jet = asciiread(dirobs+"U250_RMS_jetext",(/-1/),"float") ;basic state zonal wind corr
 RMS_U = asciiread(dirobs+"U250_RMS",(/-1/),"float")

;print(RMS_U_jet)
;print(RMS_U)

;Adding New model RMSE values to CMIP5 RMSE array

print("Adding New model RMSE values to CMIP5 RMSE array")

   RMS_U_Jetnew = new((/dimsizes(RMS_U_jet)+1/),typeof(U_CMIP5))
   RMS_Unew = new((/dimsizes(RMS_U)+1/),typeof(U_CMIP5))

   RMS_U_Jetnew(0:9) = RMS_U_jet
   RMS_U_Jetnew(10)  = rmsU

   RMS_Unew(0:9) = RMS_U
   RMS_Unew(10)  = rmsU1

;print(RMS_Unew)


asciiwrite (diro+"/U250_RMS_jetext_updated" ,RMS_U_Jetnew)
asciiwrite (diro+"U250_RMS_updated" ,RMS_Unew)


print("Ascii file for U250-hPa  RMSE are updated with new model's U250-hPa RMSE values")
print("Updated RMSE files are now saved at: " +diro)
print("Updated RMSE ascii files are: "+ "U250_RMS_jetext and U250_RMS_updated ")
print("Process of U250-hPa RMSE caclulation is completed now")
print("--------------------------------------------------------------------------")
end
