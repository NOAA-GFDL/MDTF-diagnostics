; This file is part of the MJO_teleconnection module of the MDTF code package (see LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin
print("--------------------------------------------------------------------")
print("                ploting of MJO teleconnection diagnosis figures")
print("--------------------------------------------------------------------")
Domain = "Pacific"
Modeln = getenv("CASENAME") 
phase_av = True  ;average all phases?

EP = False  ;if eastward power desired instead of E/W ratio
pentad = 0
;-----Model------

     Model_long = (/"GPCP","bcc_csm1_1","CanESM2","CNRM_CM5","GFDL_CM3","GFDL_ESM2G","GFDL_ESM2M","IPSL_CM5A_MR","MIROC5","MRI_CGCM3","NorESM1_M", Modeln/)  ;11 (10 CMIP5 models  and your model) and obs

     Model = (/"ERA-I","BCC-CSM1.1","CanESM2","CNRM-CM5","GFDL-CM3","GFDL-ESM2G", "GFDL-ESM2M","IPSL-CM5A-MR","MIROC5","MRI-CGCM3","NorESM1-M", Modeln/)

     model_good = ind(Model .ne. "ERA-I" .and. Model .ne. "CanESM2" .and. Model .ne. "GFDL-ESM2G" .and. Model .ne. "GFDL-ESM2M" .and. Model .ne. "IPSL-CM5A-MR")
   

     Model_new=Modeln
     
    model_good = model_good - 1

;---------------------------------------------------------------------------------------------------------|
;                                    Input and output data directories
;---------------------------------------------------------------------------------------------------------|
dirobs   = getenv("OBS_DATA")+"/" 
dirm     = getenv("WK_DIR")+"/model/netCDF/"
dirfig   = getenv("WK_DIR")+"/model/PS/"
;==============================================================================================
print("read in pattern correlation data")
;----------------------------------------------------------------------------------------------
     
     crr = asciiread(dirm+"ccr_Z250comp_CMIP5_updated",(/11,8/),"float") ;precip corr (10 models)
     crr_temp=dim_avg_n(crr,1)
     crr_M = new((/dimsizes(Model)/),typeof(crr))
     crr_M(0) = 1.0
     crr_M(1:11) =crr_temp
;     print(crr_M)
;==============================================================================================
 print("read in E/W ratio  data")
;----------------------------------------------------------------------------------------------
      EWR = asciiread(dirm+"EWratio_wf_CMIP5_updated",(/-1/),"float") ;precip corr (10 models)
      RMS_U_M = new((/dimsizes(model_good)+1/),typeof(EWR))
;      print(EWR)

;==============================================================================================
print("read in zonal wind RMS error data                           ")
;----------------------------------------------------------------------------------------------
     RMS_U_jet = asciiread(dirm+"U250_RMS_jetext_updated",(/-1/),"float") ;basic state zonal wind corr 
     RMS_U = asciiread(dirm+ "U250_RMS_updated",(/-1/),"float")   

     ;print(model_good)
     ;print(RMS_U)
;     print(RMS_U_jet)

     RMS_U_M = new((/dimsizes(model_good)+1/),typeof(RMS_U))
     RMS_U_M(0) = 0.0
     RMS_U_M(1:) = RMS_U(model_good)

     RMS_U_jet_M = new((/dimsizes(model_good)+1/),typeof(RMS_U))
     RMS_U_jet_M(0) = 0.0
     RMS_U_jet_M(1:) = RMS_U_jet(model_good)
;     print(RMS_U_jet_M)


;-- Make E/W ratio vs teleconnection plot plot -
 
 ;colors  = (/"white","black","grey59","palevioletred1","deepskyblue2","aquamarine4","maroon2","red3","darkorange","blue","darkgreen","purple"/)



          wks   = gsn_open_wks ("eps",dirfig +"wvEWR_MJOav_250mb" + Domain + "_updated") 
          avdataP = crr_M
          avdataT = EWR  ;E/W ratio
         ;print(avdataP)
         ;print(avdataT)

          acr = esccr(avdataP(1:),avdataT(1:),0)
         ;print(acr)

    gsn_define_colormap(wks,"wgne15")
;----------------------------------------------------------------------
; Set some plot resources
;----------------------------------------------------------------------
  res                    = True

  res@gsnDraw            = False       ; Don't draw plot
  res@gsnFrame           = False       ; Don't advance frame

; 
; where plot goes.
;
  res@vpXF              = 0.2
  res@vpYF              = 0.85
  res@vpWidthF          = 0.5
  res@vpHeightF         = 0.5

;---Some calculations to get min/max for Y axis.
  miny = min(avdataP) 
  maxy = max(avdataP) 
  minx = min(avdataT) 
  maxx = max(avdataT) 

  amaxy = maxy - abs(miny)
  amaxy = amaxy / 2.
;print(amaxy)
  amaxy = amaxy + 1.0
  
  aminy = maxy - abs(miny)
  aminy = aminy / 2.
;print(aminy)
  aminy = aminy - 1.0

;---Resources for X/Y axes.
; if(phase_av .eq. False)
;  res@trYMinF            =  aminy               ; min value on y-axis
;  res@trYMaxF            =  amaxy               ; max value on y-axis
; else
;  res@trYMinF            =  0.24             
;  res@trYMaxF            =  1.02
; end if
 
;---Resources for X/Y axes.
  res@trYMinF            =  0.1             
  res@trYMaxF            =  0.81

if(EP .eq. False)
  res@trXMinF            =  min(avdataT) - 0.28 ;0.02                 ; min value on x-axis
  res@trXMaxF            =  max(avdataT) + 0.28;0.05                    ; max value on x-axis
else
  res@trXMinF            =  0                 ; min value on x-axis
  res@trXMaxF            =  0.6
end if

  res@tmXBLabelFontHeightF = 0.013
  res@tmYLLabelFontHeightF = 0.013
  res@tmXTOn = False ; Turn off tickmarks and labels 
  res@tmYROn = False 
  res@txFontHeightF   = 0.01 

;---XY marker resources
  res@xyMarkLineMode     = "Markers"
  res@xyMarkerSizeF      = 0.014
  res@xyMarkerThicknessF = 3.
  ;res@xyMonoMarkerColor  = False          ; Allow different colors for markers

colModel = (/2,3,2,4,7,8,11,13,14,15,16,18/)
Markind  = (/16,16,4,16,16,4,4,4,16,16,16,16/)


   colors         = new ((/dimsizes(Model)/),"string")
   marki          = new ((/dimsizes(Model)/),"string")
   colors (0) = "black"
   marki (0)  = "black"

   colors (1:) = colModel(1:)
   marki(1:) = Markind(1:)
\
  res@xyMarkerColors     = colors     ; It's okay to list more than
                    
  res@xyMarkers          = (/16,16,4,16,16,4,4,4,16,16,16,16/)
  
;---Tickmark resources
  ;res@tmXBMode         = "Manual"
 ; res@tmYLMode         = "Manual"
  ;res@tmXBTickSpacingF = 1.
 ; res@tmYLTickStartF = 0.3
 ; res@tmYLTickSpacingF = 0.1

    
       res@tiXAxisString      = "MJO E/W ratio"
      
   

  res@tiYAxisString      = "MJO teleconnections pattern correlation"
  res@tiMainFontHeightF  = 0.015
  res@tiYAxisFontHeightF = 0.0135
  res@tiXAxisFontHeightF = 0.0135

 

 obs_line = fspan(0,1,dimsizes(avdataP))
 EWR_line = new((/dimsizes(obs_line)/),typeof(EWR))
 EWR_line = EWR(0)

 resline                  = True           ; polyline mods desired
 resline@gsnDraw            = False       ; Don't draw plot
 resline@gsnFrame           = False  
 resline@xyLineThicknessF      = 1.5   
 resline@xyDashPatterns    = 1 

 
  
  res@xyMarkerSizeF = 0.025
  plot = gsn_csm_xy (wks,transpose((/avdataT,avdataT/)),transpose((/avdataP,avdataP/)),res)
  plot_ov = gsn_csm_xy (wks,EWR_line,obs_line,resline)
     overlay(plot,plot_ov)

 


  draw(plot)
 delete(plot_ov)

;----------------------------------------------------------------------
; Draw some individual labelbars.
;----------------------------------------------------------------------

  labels1  = Model(1:)
  colors1  = colors(1:)

;with new model label
  markers1 = (/4,2,6,7,5,9,3,8,12,14,16/)
  xpos2    = (/0.09, 0.23,  0.35, 0.47, 0.59, 0.75/)
  xpos22   = (/0.12, 0.265,  0.38, 0.52, 0.65/)

;without ERA-I
;  markers1 = (/4,2,6,7,5,9,3,8,12,14 16/)
;  xpos2    = (/ 0.135,  0.27, 0.38, 0.51, 0.63/)
;  xpos22   = (/0.12, 0.265,  0.42, 0.52, 0.65/)

  xpos3    = xpos2 + 0.015
  xpos4    = xpos22 + 0.015

  mkres               = True         ; Marker resources
  mkres2               = True         ; Marker resources
  txres               = True         ; Text resources
  txres@txFontHeightF = 0.012
  txres@txJust        = "CenterLeft"
;
; Each labelbar has just one label. This allows you to more
; easily control where the label goes.
; 

 do i = 0,dimsizes(Model)-2
   if(i .lt. dimsizes(xpos2))
     mkres@gsMarkerColor     = colors(i+1)
     mkres@gsMarkerThicknessF = 3.5
     mkres@gsMarkerSizeF      = 0.015
     mkres@gsMarkerIndex      = marki(i+1)

     gsn_polymarker_ndc(wks,           xpos2(i),0.23,mkres)
     gsn_text_ndc      (wks,labels1(i),xpos3(i),0.23,txres)

     l = 0
    else
     mkres2@gsMarkerColor     = colors(i+1)
     mkres2@gsMarkerThicknessF = 3.5
     mkres2@gsMarkerSizeF      = 0.015
     mkres2@gsMarkerIndex      = marki(i+1)
     
     gsn_polymarker_ndc(wks,           xpos22(l),0.2,mkres2)
     gsn_text_ndc      (wks,labels1(i),xpos4(l),0.2,txres)
     l= l + 1
   end if
  end do

;----------------------------------------------------------------------
; Draw some markers and text.
;----------------------------------------------------------------------


  frame(wks)    ; Now advance the frame.


delete(wks)
delete(plot)
delete(res)
delete(avdataT)
delete(acr)
delete(avdataP)



print("250hPa zonal mean wind error plot")
print("--------------------------------------------------------------------")

mod_goodall = new((/dimsizes(model_good)+1/),integer)
mod_goodall(0) = 0
mod_goodall(1:) = model_good + 1
;print(mod_goodall)

avdataP = crr_M(mod_goodall)
;print(dimsizes(avdataP))
;print(dimsizes(RMS_U_M))
;print(avdataP)
;print("make BS metric plot")

   avdataT = new((/2,dimsizes(RMS_U_M)/),typeof(RMS_U_M))
   avdataT(0,:) = RMS_U_M
   avdataT(1,:) = RMS_U_jet_M

 acr = esccr(avdataP(1:),avdataT(0,1:),0)
 acr2 = esccr(avdataP(1:),avdataT(1,1:),0)
 ;print(acr + "   " + acr2)


 ;t-statistic
 ;print("t-statistic")

 n = dimsizes(avdataP(1:))    ;-1 to exclude reanalysis
; print(n)
 tstat = acr * sqrt(n-2.)/sqrt(1.-acr^2.)
 ;print(tstat)



;-- make plot of BS metrics --
   wks   = gsn_open_wks ("eps",dirfig +"BSmetric_goodMJO_250mbU" + "_" + Domain + "_pentad"+pentad) 

    gsn_define_colormap(wks,"wgne15")
;----------------------------------------------------------------------
; Set some plot resources
;----------------------------------------------------------------------
  res                    = True

  res@gsnDraw            = False       ; Don't draw plot
  res@gsnFrame           = False       ; Don't advance frame

; 
; where plot goes.
;
  res@vpXF              = 0.2
  res@vpYF              = 0.85
  res@vpWidthF          = 0.5
  res@vpHeightF         = 0.5

;---Resources for X/Y axes.
  ;res@trYMinF            =  0.29             
  ;res@trYMaxF            =  0.81

  res@trYMinF            =  min(avdataP) - 0.05           
  res@trYMaxF            =  max(avdataP(1:))+0.05

  res@trXMinF            =  0.0 ;min(avdataT) - 0.28 ;0.02                 ; min value on x-axis
  res@trXMaxF            =  max(avdataT) + 1.5;0.05

  res@tmXBLabelFontHeightF = 0.013
  res@tmYLLabelFontHeightF = 0.013
  res@tmXTOn = False ; Turn off tickmarks and labels 
  res@tmYROn = False 
  res@txFontHeightF   = 0.01 

;---XY marker resources
  res@xyMarkLineMode     = "Markers"
  res@xyMarkerSizeF      = 0.025
  res@xyMarkerThicknessF = 3.
  ;res@xyMonoMarkerColor  = False          ; Allow different colors for markers

delete(colModel)
delete(colors)


colModel = (/3,2,4,7,8,11,13,14,15,16,18/)

   colors         = new ((/dimsizes(model_good)+1/),"string")
   ;print(colModel(model_good))

   colors (0) = "black"
   colors (1:) = colModel(model_good)

  res@xyMarkerColors     = colors     ; It's okay to list more than
                                          ; you need here
;---Title resources
  res@tiXAxisString      = "U250 RMS Error"


  res@tiYAxisString      = "MJO teleconnections pattern correlation"
  res@tiMainFontHeightF  = 0.015
  res@tiYAxisFontHeightF = 0.0135
  res@tiXAxisFontHeightF = 0.0135



;GPCP","bcc_csm1_1","CanESM2","CNRM_CM5","GFDL_CM3","GFDL_ESM2G","GFDL_ESM2M","IPSL_CM5A_MR"
;print(avdataT)
;print(avdataP)

  res@xyMarkers  = (/2,2,2,2,2,2,2,2/)    
  plot_o = gsn_csm_xy (wks,transpose((/avdataT(0,:),avdataT(0,:)/)), \
                         transpose((/avdataP,avdataP/)),res)

  res@xyMarkers  = (/16,16,16,16,16,16,16,16/)  
  plot = gsn_csm_xy(wks,transpose((/avdataT(1,:),avdataT(1,:)/)), \
                         transpose((/avdataP,avdataP/)),res)

       overlay(plot,plot_o)

  draw(plot)

;----------------------------------------------------------------------
; Draw some individual labelbars.
;----------------------------------------------------------------------
;delete(colors1)


  labels2  = labels1(model_good)
  colors2  = colors1(model_good)
  

  markers2 = (/4,2,6,7,5,9,3/)
  xposs2    = (/0.09, 0.23,  0.35, 0.47, 0.57, 0.70, 0.82/)
  xposs3    = xposs2 + 0.015


  mkres               = True         ; Marker resources
  mkres2               = True         ; Marker resources
  txres               = True         ; Text resources
  txres@txFontHeightF = 0.012
  txres@txJust        = "CenterLeft"
;
; Each labelbar has just one label. This allows you to more
; easily control where the label goes.
; 
do i = 0,dimsizes( labels2)-1
     mkres@gsMarkerColor     = colors2(i)
     mkres@gsMarkerThicknessF = 3.5
     mkres@gsMarkerSizeF      = 0.020
     mkres@gsMarkerIndex      = 16
     gsn_polymarker_ndc(wks,           xposs2(i),0.23,mkres)
     gsn_text_ndc      (wks,labels2(i),xposs3(i),0.23,txres)
  end do
;----------------------------------------------------------------------
; Draw some markers and text.
;----------------------------------------------------------------------


  frame(wks)    ; Now advance the frame.

print("ploting of figures are done")


end
