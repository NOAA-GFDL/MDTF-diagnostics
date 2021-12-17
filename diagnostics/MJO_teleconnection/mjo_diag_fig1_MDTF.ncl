; This file is part of the MJO_teleconnection module of the MDTF code package (see LICENSE.txt)

;-------------------------------------------------------------------------------------
;Precip and geopotential height pentad lagged MJO composites
;
;January 2, 2015, updated for CMIP5 models July 13, 2015
;Updated directories for CSU Feb 6, 2016
;Written by Stephanie Henderson
;Modiefied By Bohar Singh for MDTF Jan 11 2018 
;-------------------------------------------------------------------------------------

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

err = NhlGetErrorObjectId()
  setvalues err
    "errLevel" : "Fatal"          ; only report Fatal errors
  end setvalues

print("-----------------------------------------------------------------------------------")
print("   Plotting  phase composites for precipitation and geopotential height all phases")
print("-----------------------------------------------------------------------------------")

 Modeln = getenv("CASENAME") 
 phase = ispan(1,8,1) 
 pentad = 0               ;index of pentad desired 
 sig = False              ;difference of means test for Z250 btwn GCMs and reanalysis

;--------------------------------------- Participating model names ---------------------------------------|

  Model_long = (/"ERA_GPCP",Modeln,"bcc_csm1_1","CNRM_CM5","GFDL_CM3","MIROC5","MRI_CGCM3","NorESM1_M"/)
  Model = (/"ERA/GPCP",Modeln,"BCC-CSM1.1","CNRM-CM5","GFDL-CM3","MIROC5","MRI-CGCM3", "NorESM1-M"/)

;---------------------------------------------------------------------------------------------------------|
;                                    Input and output data directories
;---------------------------------------------------------------------------------------------------------|
dirobs   = getenv("OBS_DATA")+"/" 
dirm     = getenv("WK_DIR")+"/model/netCDF/"
dirfig   = getenv("WK_DIR")+"/model/PS/"


print("precipitation and geopotential height composites are read in")

 
do pn = 0,dimsizes(phase)-1
  ;print("phase: " + phase(pn)) 

 do m = 0,dimsizes(Model)-1
 ;  print("Model: " + Model(m))

;-------------------------------------------------------------------------------------------------------------
;                                  |------directory for output files-------|
;-------------------------------------------------------------------------------------------------------------
if(Model(m) .ne. "ERA/GPCP")

;--read in data--

   if(Model(m) .ne. Modeln)
       a = addfile(dirobs + "PR_composites_"+Model_long(m)+".nc","r")    	   ;read in precip (4 pentads)
       geop_composites_Pt = a->geop_composites_P(0,pn,:,:)     ;4,8,lat,lon
   else
       a = addfile(dirm + "PR_composites_"+Model_long(m)+".nc","r") 
       geop_composites_Pt = a->pr_composites(0,pn,:,:)     ;4,8,lat,lon
   end if 
else

  a = addfile(dirobs + "GPCP_composites.nc","r")  ;4 pentads
  geop_composites_Pt = a->geop_composites_P(0,pn,:,:)

end if

  lon_p = a->lon  
  lat_p = a->lat   ;only goes 30S to 30N  

;add geopotential height data
if(Model(m) .ne. "ERA/GPCP")

   if(Model(m) .ne. Modeln)
      b = addfile(dirobs + "geop_compositesP_hgt250_"+Model_long(m)+".nc","r") 
    else 
    b = addfile(dirm + "geop_compositesP_hgt250_"+Model_long(m)+".nc","r") 
   end if

else
  b = addfile(dirobs + "geop_compositesP_hgt250.nc","r")
end if
  geop_composites = b->geop_composites(pentad,pn,:,:)
 

  lon = tofloat(b->lon)
  lat = tofloat(b->lat)

 if(Model(m) .eq. "ERA/GPCP")
   geop_composites_obs = geop_composites
   lat_obs = lat
   lon_obs = lon   
 end if 

  lon = tofloat(b->lon)  
  lat = tofloat(b->lat)  

nlonn=dimsizes(lon)
nlatn=dimsizes(lat)

lat =latGlobeFo(nlatn, "lat", "latitude", "degrees_north")
lon =lonGlobeFo(nlonn, "lon", "longitude", "degrees_east")

  lon = tofloat(b->lon)  
  lat = tofloat(b->lat)  


if(Model(m) .ne. "ERA/GPCP")
  if(Model(m) .ne. Modeln)
  c = addfile(dirobs + "tstatP_hgt250_"+Model_long(m)+".nc","r") 
  else   
  c = addfile(dirm + "tstatP_hgt250_"+Model_long(m)+".nc","r") 
  end if 
else
  c = addfile(dirobs + "tstatP_hgt250.nc","r") 
end if

  tstat = c->tstat_hgt(pentad,pn,:,:)
  ;tstat = dim_avg_n(tstatt,0)
  ;delete(tstatt)
  delete(c) 

 tstat!0   = "lat"    
 tstat!1   = "lon"
 tstat&lat = lat      
 tstat&lon = lon   

tstat@_FillValue = -999
geop_composites_Pt@_FillValue = -999
geop_composites@_FillValue = -999

;expand precip to full globe

    latS   = -30.
    latN   =  30.  



if(Model(m) .ne. "ERA/GPCP")
 geop_composites_P = new((/dimsizes(geop_composites)/),typeof(geop_composites_Pt))
 geop_composites_P!0   = "lat"    
 geop_composites_P&lat = lat    

;print("Var Summary for geop_composites_P")
;printVarSummary(geop_composites_Pt)
;print("Var Summary for geop_composites_P")
;printVarSummary(geop_composites_P)


; This section is to write precipitation only between 30N-30S 

 geop_composites_P = geop_composites_Pt@_FillValue
 if(Model(m) .ne. Modeln)
 geop_composites_P({latS:latN},:) = geop_composites_Pt
 else
 geop_composites_P({latS:latN},:) = geop_composites_Pt({latS:latN},:)
 end if  
 geop_composites_P!0   = "lat"    
 geop_composites_P!1   = "lon" 
 geop_composites_P&lat = lat      
 geop_composites_P&lon = lon
else
 geop_composites_P = geop_composites_Pt
 geop_composites_P!0   = "lat_p"    
 geop_composites_P!1   = "lon_p"
 geop_composites_P&lat_p = lat_p      
 geop_composites_P&lon_p = lon_p
end if

geop_composites_P@_FillValue = -999
delete(geop_composites_Pt)

delete(latS)
delete(latN)
latN = 15

tstat({:latN},:) = tstat@_FillValue

delete(latN)
latN = -35

geop_composites!0   = "lat"    
geop_composites!1   = "lon"
geop_composites&lat = lat      
geop_composites&lon = lon

if(m .gt. 0)
 geop_composites_CMIP5 = geop_composites
end if

geop_composites({:latN},:) = geop_composites@_FillValue

geop_composites!0   = "lat"    
geop_composites!1   = "lon"
geop_composites&lat = lat      
geop_composites&lon = lon

delete(latN)
delete(a)

;print("make plot")


;print("phase: " + phase(pn) )


if(m .eq. 0)  
if(sig .eq. False .or. phase(pn) .ne. 3)
  wks = gsn_open_wks("eps" ,dirfig + "precip_hgtP_" + phase(pn)+"_Pentad"+pentad)
else
 ;difference of mean plot
 wks = gsn_open_wks("eps" ,dirf + "precip_hgtP_p3_diffofmeans")
end if

   gsn_define_colormap(wks,"ViBlGrWhYeOrRe")   
   gsn_reverse_colormap(wks) 

 res = True
 res@gsnDraw          = False
 res@gsnFrame         = False 
 res@gsnAddCyclic = True
 res@mpPerimOn         = False  
 res@mpFillOn               = False
 res@mpGeophysicalLineThicknessF = 1.3
 res@mpGeophysicalLineColor = "steelblue4" ;"grey30"

 ;res@mpGridAndLimbOn   = True              ; turn on lat/lon lines
 ;res@mpGridLatSpacingF = 30.
 ;res@mpProjection      = "Robinson"       ; choose projection
 res@mpCenterLonF      = 210.             ; choose center lon
 ;res@mpGridLineColor =  "steelblue4"

proj = False

 if(proj .eq. True)
  res@mpProjection      = "Orthographic"       ; choose projection
  res@mpCenterLonF      = -200.             ; choose center lon
  res@mpCenterLatF      = 25.               ; choose center lat
 else

 res@mpLimitMode = "LatLon"
 res@mpMinLatF = -20
 res@mpMaxLatF = 80
 res@mpMinLonF         = -295. 
 res@mpMaxLonF         = -60. ;-110.
 res@mpCenterLonF  = -200

 ;res@mpShapeMode = "FreeAspect"
  res@vpWidthF  = 0.7    
  res@vpHeightF  = 0.4

 res@tmXBLabelFontHeightF = 0.015    
 res@tmYLLabelFontHeightF = 0.015   

 res@tmXTOn         = False 
 res@tmYROn         = False 
 res@tmXBMinorOn = False
 res@tmYLMinorOn = False
 ;res@tmXBLabelsOn         = False              ; do not draw bottom labels
 ;res@tmXBOn               = False              ; no bottom tickmarks

  res@tmYLMode   = "Explicit"                                                
  res@tmYLValues = (/-15,0,15,30,45,60,75/)                           
  res@tmYLLabels = (/"15~S~o~N~S","0~S~o~N~","15~S~o~N~N","30~S~o~N~N","45~S~o~N~N","60~S~o~N~N","75~S~o~N~N"/)

  res@tmXBMode   = "Explicit"                                                
  res@tmXBValues = (/-270,-225,-180,-135, -90,-45, 0/)                           
  res@tmXBLabels = (/"90~S~o~N~E","135~S~o~N~E","180~S~o~N~","135~S~o~N~W","90~S~o~N~W","45~S~o~N~W","0~S~o~N~"/)

 end if


res2 = res
res2@cnFillOn          = False                  ; color fill
res2@cnLinesOn         = True
res2@cnLineDrawOrder      = "PostDraw"
 res2@cnLineThicknessF = 1.3
 res2@cnLineLabelsOn  = False
 ;res2@cnLineLabelDensityF      = 2.0
 ;res2@cnLineLabelInterval= 2.0
 ;res2@cnLineLabelFontHeightF = 0.008   
 ;res2@cnLineLabelFontThicknessF = 0.6
 res2@gsnContourNegLineDashPattern = 1       ; sets negative contours to dash pattern 1
 res2@gsnContourZeroLineThicknessF = 0
 res2@cnLevelSelectionMode  = "ManualLevels" ; set manual contour levels
 res2@cnMinLevelValF        = -100       ; set min contour level
 res2@cnMaxLevelValF        =  100
 res2@cnLevelSpacingF       =  10 ; set contour interval
 res2@cnInfoLabelOn = False  
 
res3            = res
res3 = True
res3@cnLineDrawOrder      = "PreDraw"
res3@lbLabelBarOn        = False 
res3@cnFillOn          = True                  ; color fill
res3@cnInfoLabelOn = False 
res3@cnLineLabelsOn  = False
;res3@cnLevelSpacingF   = 3.                    ; interval spacing
res3@cnLinesOn         = False
res3@gsnSpreadColors     = True                ; use full colormap
res3@cnLevelSelectionMode  = "ManualLevels" ; set manual contour levels
res3@cnMinLevelValF        = -9        ; set min contour level
res3@cnMaxLevelValF        =  9
res3@cnLevelSpacingF       =  1 ; set contour interval
    
  ; res5=res
  res5 = True
   res5@gsnAddCyclic = True
   res5@cnMonoFillPattern = False
   res5@cnFillMode      = "AreaFill"
   res5@cnFillColors  = (/"grey35","grey35"/)
   res5@cnFillOn        = True
   res5@cnLinesOn       = False
   res5@cnLevelSpacingF = 0.5
   res5@cnLineLabelsOn  = False
   res5@cnMinLevelValF = 0.1
   res5@cnMaxLevelValF = 0.1
   res5@cnFillDrawOrder     = "PostDraw"

   res5@cnMonoFillPattern    = False            ; want multiple patterns 
   res5@cnFillPatterns = (/-1,17/)
   res5@cnMonoFillScale      = False            ; want different densities 
   res5@cnFillScales         = (/2.0,0.5/) ; the densities (decreasing will make more dense, default: 1.0)

   res5@cnFillDotSizeF = 0.002    ;increasing will made dots bigger (default: 0)
   res5@cnInfoLabelOn  = False    ; Turn off info label

; Create a panel of plots with 3 rows and 1 columns.
  pres                  = True         ; Set panel resources.
  pres@gsnPaperOrientation = "portrait"
  pres@gsnMaximize      = True         ; Maximize plots in panel.
  pres@gsnPanelYWhiteSpacePercent = 3
  pres@gsnPanelXWhiteSpacePercent = 1.5 ;0.0000001
  pres@gsnPanelLabelBar = False        ; Turn on panel labelbar.
  ;pres@lbLabelFontHeightF  = 0.01
  pres@gsnPanelBottom      = 0.092

  ;pres@pmLabelBarOrthogonalPosF = -0.015

 ; pres@pmLabelBarWidthF = 0.7
 ; pres@pmLabelBarParallelPosF =0.07;5   ;moves it right or left
  ;pres@lbTitleOn        =  True                ; turn on title
 ; pres@lbTitleString    = "[m]"                ; title string
  ;pres@lbTitlePosition  = "Right"              ; title position
  ;pres@lbTitleFontHeightF= .013                ; make title smaller
  ;pres@lbTitleDirection = "Across"             ; title direction
  ;pres@lbTitleOffsetF = 0.005
  ;pres@lbTitleJust = "CenterLeft"

 plot= new((/dimsizes(Model)/),graphic)
 plot_ov = new((/dimsizes(Model)/),graphic)

end if


     if(m .eq. (dimsizes(Model)-1))
       res3@lbLabelBarOn        = True 
       res3@lbLabelFontHeightF  = 0.017           ; label bar font height 
       res3@pmLabelBarOrthogonalPosF = 0.12
       res3@pmLabelBarWidthF = 1.5
       res3@tmXBLabelsOn         = True              ; do not draw bottom labels
       res3@tmXBOn               = True              ; no bottom tickmarks

       res3@pmLabelBarParallelPosF =0.08  ;moves it right or left
       res3@lbTitleOn        =  True                ; turn on title
       res3@lbTitleString    = "[mm/day]"                ; title string
       res3@lbTitlePosition  = "Right"              ; title position
       res3@lbTitleFontHeightF= 0.021                ; make title smaller
       res3@lbTitleDirection = "Across"             ; title direction
  ;pres@lbTitleOffsetF = 0.005
       res3@lbTitleJust = "CenterLeft"

     end if

    res2@gsnLeftString =  Model(m) + "     MJO phase " + phase(pn)  
    res2@gsnLeftStringOrthogonalPosF=.03
    res2@txFontHeightF   = 0.016


;if(m .eq. 0 .or. sig .eq. False .or. phase(pn) .ne. 3)
  ac = count_unique_values(tstat)
 if (ac .eq. 1) 
   res5@cnConstFLabelFontHeightF = 0.0 ; removing constant field warning from plot if any
   plot(m)  = gsn_csm_contour_map_overlay(wks,geop_composites,tstat,res2,res5)
   print("Warning: Phase composite is statistically insignificant for "+"phase: " + phase(pn)+"  at 95% significance level ")
   print("Please include more data for conclusive result")
else
   plot(m)  = gsn_csm_contour_map_overlay(wks,geop_composites,tstat,res2,res5)
   
end if
  plot_ov(m)  = gsn_csm_contour(wks,geop_composites_P,res3)
   plot(m) = ColorNegDashZeroPosContour(plot(m),"blue3","red","red2")

   overlay(plot((m)),plot_ov((m)))

 delete(geop_composites)
 delete(tstat)
 delete(geop_composites_P)
 delete(lon_p)
 delete(lat_p)
 delete(lon)
 delete(lat)
 delete(nlonn)
 delete(nlatn)
; delete(diri)
 delete(b)

if(m .ne. 0)
  delete(geop_composites_CMIP5)
end if
if(m .ne. 0 .and. sig .eq. True .and. phase(pn) .eq. 3)
 delete(tstat_dom)
end if

 end do

    gsn_panel(wks,plot, (/4,2/), pres)

   ;draw(plot)
   ;frame(wks)

delete(plot)
delete(plot_ov)
delete(res2)
delete(res3)
delete(res5)
delete(wks)

end do
print("Figures for precipitation and geopotential height composites are now saved ")
print("at:" + dirfig)
print("-----------------------------------------------------------------------------------")
end
