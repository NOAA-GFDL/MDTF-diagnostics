; This file is part of the EOF_500hPa module of the MDTF code package (see LICENSE.txt)

; FILE: eof_npacific.ncl
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin
yr1 = getenv("FIRSTYR")
yr2 = getenv("LASTYR")
rgb = getenv("RGB")
wk_dir = getenv("WK_DIR")
casename = getenv("CASENAME")

firstyr = stringtointeger(yr1)
lastyr = stringtointeger(yr2)
nyrs = lastyr-firstyr

; get pointer to netcdf file  
 f = addfile (wk_dir+"/model/netCDF/"+casename+".Z500.ANOMS.nc","r") 
 z500 = f->Z500_ANOM   ; year,lat,lon

 lat = f->lat
 lat1 = lat({20:80})
 nlat1 = dimsizes(lat1)

 lon = f->lon
 lon1 = lon({120:270})
 nlon1 = dimsizes(lon1)

 anom = new((/nyrs,nlat1,nlon1/),float)
 anom!0 = "year"
 anom&year = ispan(firstyr+1,lastyr,1)
 anom!1 = "lat"
 anom&lat = lat1
 anom!2 = "lon"
 anom&lon = lon1
 anom  = (/z500(:,{20:80},{120:270})/) 

; compute eofs of covariance matrix
 evectors = new((/2,nlat1,nlon1/),float)
 evectors!0 = "eigenvector"
 evectors&eigenvector = ispan(1,2,1) 
 evectors!1 = "lat"
 evectors&lat = lat1
 evectors!2 = "lon"
 evectors&lon = lon1


nyr = ""
nyr = lastyr - firstyr 
optEOF = True  ; makes available some options, see http://www.ncl.ucar.edu/Document/Functions/Built-in/eofunc.shtml

;
; eofcov won't work in NCL > 5.0.0, so switching to eofunc,
; which returns the same eigenvectors but sometimes with the wrong
; sign. So, if the values are negative, multiply by -1 to maintain
; compatibility.  bundy 11/13/08
;

 evec = eofunc(anom(lat|:,lon|:,year|:),2,optEOF)
 printVarSummary(evec)

 if ( min(evec) .lt. 0 ) then
    print("WARNING: changing sign of eofs because of negative evec (see above)")
    evec = evec * -1  
 end if  


; evec = eofcov(anom(lat|:,lon|:,year|:),2)
 evectors(0,:,:) = (/evec(0,:,:)*sqrt(evec@eval(0))/)
 evectors(1,:,:) = (/evec(1,:,:)*sqrt(evec@eval(1))/)

;************ plots of EOFs *******************

 wks = gsn_open_wks ("ps",wk_dir+"/model/PS/"+casename+".npac.eof1")
   
; define colormap
 cmap = RGBtoCmap(rgb+"/blueyellowred.rgb")
 gsn_define_colormap (wks,cmap) 

; resources for the plot of annual means
   res=True
   res@gsnMaximize = True
   res@gsnPaperOrientation = "portrait"
   res@gsnAddCyclic = False
   res@gsnTickMarksOn = False
   res@mpLimitMode = "LatLon"
   res@mpMinLatF = 20.0 
   res@mpMaxLatF = 80.0
   res@mpCenterLatF = 50.0
   res@mpMinLonF = 120.0
   res@mpMaxLonF = 270.0
   res@mpCenterLonF = 195.0
   res@mpShapeMode = "FreeAspect"
   res@vpWidthF = 0.6
   res@vpHeightF = 0.4
   res@mpFillOn = False
   res@mpPerimOn = True 
   res@mpGridAndLimbOn = False
   res@txFontHeightF = 0.015

; contour resources
   res@cnFillOn = True 
   res@cnLinesOn = False
   res@cnLineLabelsOn = False
   res@cnInfoLabelOn = False
   res@cnLevelSelectionMode = "ExplicitLevels"

   res@lbTitleString = "meters"
   res@lbTitleFontHeightF = 0.015
   res@lbLabelFontHeightF = 0.015
   res@lbBoxMinorExtentF = 0.18
   res@tiMainString = casename+" DJFM 500 mb Geopotential Height Anomalies"
   res@tiMainFontHeightF = 0.018
; EOF 1
   res@cnLevels = (/-55,-45,-35,-25,-15,-10,-5,0,5,10,15,25,35,45,55/)
   res@gsnLeftString="EOF 1"
   res@gsnRightString=sprintf("%4.1f",evec@pcvar(0))+" %"
   plot = gsn_csm_contour_map_ce (wks,evectors(0,:,:),res) 
   
end
