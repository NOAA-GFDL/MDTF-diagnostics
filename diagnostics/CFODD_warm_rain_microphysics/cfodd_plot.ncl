;************************************************
; plot cfodd from statistics.
;************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"   
;
;************************************************
begin

rgb = getenv("RGB")
variab_dir = getenv("variab_dir")
casename = getenv("CASENAME")
 
f = addfile (variab_dir+"/CFODD_warm_rain_microphysics/model/netCDF/"+casename+".CFODD_ocean.nc","r")
cfodd=f->cfodd
count=f->count

count_sum=dim_sum(count)
count_5_20=sum(count_sum(1:3))
pct_5_10=count_sum(1)/count_5_20*100.
pct_10_15=count_sum(2)/count_5_20*100.
pct_15_20=count_sum(3)/count_5_20*100.

wks  = gsn_open_wks("ps",variab_dir+"/CFODD_warm_rain_microphysics/model/PS/"+casename+".CFODD_ocean") 
gsn_define_colormap(wks,"NCV_jet")

res  = True
res@gsnDraw=False
res@gsnFrame=False
res@trXMinF = -30
res@trXMaxF = 20
res@trYMinF = 0
res@trYMaxF = 60
res@trYReverse = True
res@gsnSpreadColors=True

res@cnLinesOn = False
res@cnFillOn = True
res@cnLevelSelectionMode  = "ExplicitLevels"
res@cnLevels = fspan(1,10,10)

res@lbLabelBarOn = False
res@cnLineLabelsOn = False
res@cnInfoLabelOn = False
res@tmXBLabelFontHeightF=0.028
res@tmYLLabelFontHeightF=0.028
res@tiXAxisFontHeightF = 0.035
res@tiYAxisFontHeightF = 0.035

plot=new((/3/),"graphic")
res@gsnLeftStringFontHeightF=0.035
res@gsnRightStringFontHeightF=0.035
res@gsnLeftStringOrthogonalPosF = 0.02
res@gsnRightStringOrthogonalPosF = 0.02
res@tmXTOn=False
res@tmYROn=False
res@tmXBMinorOn=False
res@tmYLMinorOn=False
res@gsnLeftString = "Re=5-10 ~F33~m~F21~m"
res@gsnRightString = sprintf("%4.1f",pct_5_10)+" %"
res@tiYAxisString = "Cloud Optical Depth"
res@tiXAxisString = " "
plot(0) = gsn_csm_contour (wks,cfodd(1,:,:), res)
res@gsnLeftStringOrthogonalPosF = 0.04
res@gsnRightStringOrthogonalPosF = 0.04
res@gsnLeftString = "Re=10-15 ~F33~m~F21~m"
res@gsnRightString = sprintf("%4.1f",pct_10_15)+" %"
res@tiYAxisString = " "
res@tiXAxisString = "Radar Reflectivity (dBZ)"
plot(1) = gsn_csm_contour (wks,cfodd(2,:,:), res)
res@gsnLeftStringOrthogonalPosF = 0.04
res@gsnRightStringOrthogonalPosF = 0.04
res@gsnLeftString = "Re=15-20 ~F33~m~F21~m"
res@gsnRightString = sprintf("%4.1f",pct_15_20)+" %"
res@tiXAxisString = " "
res@tiYAxisString = " "
plot(2) = gsn_csm_contour (wks,cfodd(3,:,:), res)

respn=True
respn@gsnPanelLabelBar = True
respn@lbAutoManage          = False
respn@lbBoxLinesOn     = False
respn@pmLabelBarWidthF = 0.08
respn@pmLabelBarHeightF = 0.225
respn@lbOrientation = "Vertical"
respn@lbLabelStride = 1
respn@lbLabelFontHeightF = 0.012
respn@pmLabelBarParallelPosF = 0.012
respn@txString = casename+" CFODD over ocean"
respn@txFontHeightF = 0.025
respn@gsnPanelXWhiteSpacePercent = 5.0
respn@gsnPanelYWhiteSpacePercent = 5.0

gsn_panel(wks, plot(0:2), (/1,3/),respn)
end
