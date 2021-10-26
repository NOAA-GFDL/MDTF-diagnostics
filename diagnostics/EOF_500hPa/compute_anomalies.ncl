; This file is part of the EOF_500hPa module of the MDTF code package (see LICENSE.txt)

; FILE: anomalies.ncl

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
begin

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

wk_dir = getenv("WK_DIR")
casename = getenv("CASENAME")
yr1 = getenv("FIRSTYR")
yr2 = getenv("LASTYR")
date_off = getenv("date_int_offset")
use_hybrid_sigma = (getenv("USE_HYBRID_SIGMA").eq."1")

firstyr = stringtointeger(yr1)
lastyr = stringtointeger(yr2)
date_offset = stringtointeger(date_off) ; 1 for native CESM, 0 for GFDL & CMIP
nyrs = lastyr-firstyr+1
nmons = nyrs*12

time_coord = getenv("time_coord")
lat_coord = getenv("lat_coord")
lon_coord = getenv("lon_coord")
lev_coord = getenv("lev_coord")
file_path = getenv("DATADIR")

; Z500 
if( fileexists(wk_dir+"/model/netCDF/"+casename+".Z500.ANOMS.nc") ) then

print(wk_dir+"/"+casename+".Z500.ANOMS.nc exists!!")

else

; TSJ edit 2021-01-12
if (use_hybrid_sigma) then
   hyam_var = "hyam" ;getenv("hyam_var")
   hybm_var = "hybm" ;getenv("hybm_var")
   zg_var = getenv("zg_hybrid_sigma_var")
   ps_var = getenv("ps_var")
   f_zg = addfile(getenv("ZG_HYBRID_SIGMA_FILE"),"r")
   f_ps = addfile(getenv("PS_FILE"),"r")
else
   zg_var = getenv("zg_var")
   f_zg = addfile(getenv("ZG_FILE"),"r")
end if
; end TSJ edit

time = f_zg->$time_coord$
lat = f_zg->$lat_coord$
lon = f_zg->$lon_coord$
nlat = dimsizes(lat)
nlon = dimsizes(lon)

slat = new((/nlat+1/),"double")
gw = new((/nlat/),"double")
gw!0 = lat_coord
gw&$lat_coord$ = lat
slat(0) = -90.d0
slat(nlat) = 90.d0
do i=1,nlat-1
 slat(i) = (lat(i-1)+lat(i))/2.d0
end do
pi = 4.d0*atan(1.d0)
do i=0,nlat-1
 gw(i) = sin(slat(i+1)/180.d0*pi)-sin(slat(i)/180.d0*pi)
end do

time_all = f_zg->$time_coord$
if (date_offset.eq.0) then
   ; CMIP / GFDL date index, use YYYYMM
   date_all = cd_calendar(time_all,-1)
   year_all = date_all/100
   start_date = firstyr*100+1
   end_date = (lastyr)*100+12
else if (date_offset.eq.1) then
   ; CESM native date index, use YYYYMMDD
   date_all = cd_calendar(time_all,-2)
   year_all = date_all/10000
   start_date = firstyr*10000+201
   end_date = (lastyr+1)*10000+101
end if
end if
; in either case, above only used to set following indices
do i=0,dimsizes(date_all)-1
   if( date_all(i).eq.start_date ) then
      i1 = i
   end if
   if( date_all(i).eq.end_date ) then
      i2 = i
   end if
end do

win_anom = new ((/nyrs-1,nlat,nlon/),"float")
win_anom!0 = "year"
win_anom&year = ispan(firstyr+1,lastyr,1) 
win_anom!1 = lat_coord
win_anom&$lat_coord$ = lat
win_anom!2 = lon_coord
win_anom&$lon_coord$ = lon
win_anom@long_name = "Winter (DJFM) 500mb height anomaly"
win_anom@units = "meters"

; TSJ edit 2021-01-12: temporary hack to extract 500 mb level of f_zg (z500)
if (use_hybrid_sigma) then
   ; hybrid sigma level extraction
   hyam = f_zg->$hyam_var$
   hybm = f_zg->$hybm_var$
   z = f_zg->$zg_var$($time_coord$|i1:i2,$lev_coord$|:,$lat_coord$|:,$lon_coord$|:)
   ps = f_ps->$ps_var$($time_coord$|i1:i2,$lat_coord$|:,$lon_coord$|:)
   z500_4D = vinth2p(z,hyam,hybm,500.,ps,2,1000.,1,False) ; (time,plev,lat,lon)
   ; level dimension is now degenerate (length 1), so drop it to get 3D data
   z500_dims = dimsizes(z500_4D)
   z500 = reshape(z500_4D, (/z500_dims(0), z500_dims(2), z500_dims(3)/))
   delete (z)
   delete (z500_4D)
   delete (ps)
else
   rank = dimsizes( filevardimsizes(f_zg,zg_var) )
   if (rank.ne.3 .or. rank.gt.4) then
      print("getVarSlice: only 3D supported: rank="+rank+"D")
      exit
   end if
   ; 3D data; assume we got 500 hPa level
    z500 = f_zg->$zg_var$($time_coord$|i1:i2,$lat_coord$|:,$lon_coord$|:)
end if
; end TSJ edit

anom = (/rmMonAnnCycTLL(z500(:,:,:))/)
delete (z500)
n = 11
do yr = firstyr+1,lastyr
  win_anom(yr-firstyr-1,:,:) = (/(anom(n,:,:)+anom(n+1,:,:)+anom(n+2,:,:)+anom(n+3,:,:))/4./)
  n = n + 12
end do
fo = addfile(wk_dir+"/model/netCDF/"+casename+".Z500.ANOMS.nc","c")
fo->Z500_ANOM = win_anom
fo->gw = gw

if (use_hybrid_sigma) then
   delete(f_ps)
end if
delete(f_zg)
delete(win_anom)

end if


end
