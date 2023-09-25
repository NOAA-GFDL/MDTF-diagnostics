; This file is part of the MJO_prop_amp module of the MDTF code package (see LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

print_clock("Starting model data inteperation")

wk_dir = getenv("WK_DIR")
pr_name  = getenv("pr_var")
prw_name = getenv("prw_var")
hus_name = getenv("hus_var")
pres_level_name = getenv("lev_coord")
file_pr = getenv("file_pr")
file_prw = getenv("file_prw")
file_hus = getenv("file_hus")

print_clock("Precipitation ...")
print("   Opening file_pr = "+file_pr)
filein_pr = addfile(file_pr,"r")

newlon = fspan(0.,357.5,144)
newlat = fspan(-60.,60,49) 
newlat@units = "degrees_north"
newlon@units = "degrees_east" 

newpr = linint2(filein_pr->$pr_name$&lon,filein_pr->$pr_name$&lat,filein_pr->$pr_name$,True,newlon,newlat,0)
newpr!0="time"
newpr!1="lat"
newpr!2="lon"
newpr&time=filein_pr->$pr_name$&time
newpr&lat=newlat
newpr&lon=newlon

newtime=newpr&time
ntim = dimsizes(newpr&time)
do i=0,ntim-1
newtime(i)=i
end do
newpr&time=newtime

newpr2 = calculate_daily_values (newpr, "avg", 0, False)  
newtime2=newpr2&time

print("Writing "+wk_dir+"/model/netCDF/model_pr.nc")
system("rm -f "+wk_dir+"/model/netCDF/model_pr.nc")
fout = addfile(wk_dir+"/model/netCDF/model_pr.nc","c") 
print("wrote "+wk_dir+"/model/netCDF/model_pr.nc")
fAtt               = True            ; assign file attributes
fAtt@title         = "Interpolated rainfall"
fAtt@source_file   = file_pr
fAtt@Conventions   = "None"
fAtt@creation_date = systemfunc ("date")
fileattdef(fout, fAtt )
print("set atts on "+wk_dir+"/model/netCDF/model_pr.nc")
filedimdef(fout,"time",-1,True)
newpr2&time@calendar="noleap"
fout->pr = newpr2

print_clock("Precipitatable water ...")
print("   Opening file_prw "+file_prw)
filein_prw = addfile(file_prw,"r")

newprw = linint2(filein_prw->$prw_name$&lon,filein_prw->$prw_name$&lat,filein_prw->$prw_name$,True,newlon,newlat,0)
newprw!0="time"
newprw!1="lat"
newprw!2="lon"
newprw&time=filein_prw->$prw_name$&time
newprw&lat=newlat
newprw&lon=newlon

newtime=newprw&time
ntim = dimsizes(newprw&time)
do i=0,ntim-1
newtime(i)=i
end do
newprw&time=newtime

newprw2 = calculate_daily_values (newprw, "avg", 0, False)
newtime2=newprw2&time

print("Writing "+ wk_dir+"/model/netCDF/model_prw.nc")
system("rm -f "+wk_dir+"/model/netCDF/model_prw.nc")
fout = addfile(wk_dir+"/model/netCDF/model_prw.nc","c")
print("wrote "+wk_dir+"/model/netCDF/model_prw.nc")
fAtt               = True            ; assign file attributes
fAtt@title         = "Interpolated rainfall"
fAtt@source_file   = file_prw
fAtt@Conventions   = "None"
fAtt@creation_date = systemfunc ("date")
fileattdef(fout, fAtt )
print("wrote atts to "+wk_dir+"/model/netCDF/model_prw.nc")
filedimdef(fout,"time",-1,True)
newprw2&time@calendar="noleap"
fout->prw = newprw2

print_clock("Specific humidity ...")
print("   Opening file_hus "+file_hus)
filein_hus = addfile(file_hus,"r")

time = filein_hus->time 
lev = filein_hus->$pres_level_name$
lon = filein_hus->lon 
lat = filein_hus->lat 
ntim = dimsizes(time)
nlev = dimsizes(lev)
nlat = dimsizes(lat)
nlon = dimsizes(lon)

husm=new((/ntim,dimsizes(newlat),dimsizes(newlon)/),typeof(filein_hus->$hus_name$(1,:,:,:)))
xxm=new((/dimsizes(lat),dimsizes(lon)/),typeof(filein_hus->$hus_name$(1,1,:,:)))
xxm!0="lat"
xxm!1="lon"
xxm&lat=lat
xxm&lon=lon

do itim=0,ntim-1
hus= filein_hus->$hus_name$(itim,:,:,:)
poisson_grid_fill(hus,True,1,1000,1e-2,0.6,0)

ps = hus(1,:,:)*0+100000.       ; surface pressure "Pa"
;opt = (/ 1, 650, 900 /)
opt = (/ 1, 60000, 92500 /)
;xxm = wgt_vert_avg_beta(lev,hus,ps,0,opt)
xxm = wgt_vert_avg_beta(lev,hus,ps,1,opt)
husm(itim,:,:)= linint2_Wrap(lon,lat,xxm,True,newlon,newlat,0)
end do

husm!0="time"
husm!1="lat"
husm!2="lon"
husm&time=time
husm&lat=newlat
husm&lon=newlon

print("Writing "+wk_dir+"/model/netCDF/model_hus_900_650_avg.nc")
system("rm -f "+wk_dir+"/model/netCDF/model_hus_900_650_avg.nc")
fout = addfile(wk_dir+"/model/netCDF/model_hus_900_650_avg.nc","c")
fAtt               = True            ; assign file attributes
fAtt@title         = "Interpolated model 900-650hPa averaged specific humidity"
fAtt@source_file   = file_hus
fAtt@Conventions   = "None"
fAtt@creation_date = systemfunc ("date")
fileattdef( fout, fAtt )
filedimdef(fout,"time",-1,True)
husm&time@calendar="noleap"
fout->hus = husm

print_clock("Finishing model data interpolation")
end
