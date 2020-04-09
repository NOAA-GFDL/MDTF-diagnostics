; This file is part of the MJO_suite module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

undef("mjo_wavenum_freq_season_plot_panel")
procedure mjo_wavenum_freq_season_plot_panel (wf[*][*],seaName[1]:string\
                     ,pltDir[1]:string, pltType[1]:string         \
                     ,pltName[1]:string, opt[1]:logical,wks:graphic,plot:graphic)
begin 
  pltPath= pltDir+"/"+pltName+"."+seaName
 
  if (pltType.eq."png") then
      pltTypeLocal = "eps"
  else
      pltTypeLocal = pltType
  end if

;  wks  = gsn_open_wks(pltTypeLocal, pltPath)  
  if (opt .and. isatt(opt,"colorTable") .or. isatt(opt,"pltColorTable")) then
      if (isatt(opt,"colorTable")) then
          gsn_define_colormap(wks,opt@colorTable) 
      else
          gsn_define_colormap(wks,opt@pltColorTable) 
      end if
  else
     gsn_define_colormap(wks,"precip2_17lev") 
  end if

  res = opt
  res@gsnFrame            = False
  res@gsnDraw             = False
  res@cnFillOn            = True          ; turn on color
  res@lbLabelBarOn        = False
  res@cnInfoLabelOn       = False
;;No longer needed in V6.1.0 and later
;;res@gsnSpreadColors     = True          ; use full range of colormap
;;res@lbLabelAutoStride   = True
  
  if (isatt(opt,"tiMainString") .and. opt@tiMainString.ne."") then
      res@tiMainString    = opt@tiMainString
    else if (seaName.ne."") then
             res@tiMainString    = str_upper(seaName)
    end if
  end if
  if (isatt(opt,"gsnLeftString")) then
      res@gsnLeftString   = opt@gsnLeftString
  end if
  if (isatt(opt,"gsnCenterString")) then
      res@gsnCenterString = opt@gsnCenterString
  end if
  if (isatt(opt,"gsnRightString")) then
      res@gsnRightString  = opt@gsnRightString
  end if
  if (isatt(opt,"cnLinesOn")) then
      res@cnLinesOn    = opt@cnLinesOn
      if (.not.res@cnLinesOn) then
          res@cnLineLabelsOn = False
      end if
  end if
  if (isatt(opt,"cnLevelSelectionMode")) then
      res@cnLevelSelectionMode  = opt@cnLevelSelectionMode
  end if
  if (isatt(opt,"cnLevelSelectionMode")) then
      res@cnLevelSelectionMode  = opt@cnLevelSelectionMode
  end if
  if (isatt(opt,"cnMinLevelValF")) then
      res@cnMinLevelValF  = opt@cnMinLevelValF
  end if
  if (isatt(opt,"cnMaxLevelValF")) then
      res@cnMaxLevelValF  = opt@cnMaxLevelValF
  end if
  if (isatt(opt,"cnLevelSpacingF")) then
      res@cnLevelSpacingF  = opt@cnLevelSpacingF
  end if
  if (isatt(opt,"cnLevels")) then
      res@cnLevels  = opt@cnLevels
  end if
  if (isatt(opt,"cnLevels")) then
      res@cnLevels  = opt@cnLevels
  end if
  if (isatt(opt,"lbOrientation")) then
      res@lbOrientation = opt@lbOrientation
  end if
  
  NW = 6
  if (isatt(opt,"maxWavePlot")) then     ; wave [Y] axis
      NW  = opt@maxWavePlot
  end if

  fMin = -0.05  
  fMax =  0.05
  
  if (isatt(opt,"minFreqPlot")) then
      fMin  = opt@minFreqPlot
  end if 
  if (isatt(opt,"maxFreqPlot")) then
      fMax  = opt@maxFreqPlot
  end if
  
 ;res@trXMinF = fMin
 ;res@trXMaxF = fMax  
 
  WORK  = wf({0:NW},{fMin:fMax}) 
  
  if (opt .and. isatt(opt,"smth9") .and. opt@smth9) then
      WORK = smth9(WORK, 0.50,  0.25, False)
  end if

  izero = ind(WORK&freq .eq. 0.0)
  WORK(:,izero) = min(WORK)       ; 0th freq

  if (isatt(opt,"label_freq") .and. .not.opt@label_freq) then
      delete(WORK&freq@long_name)
  end if
  
  plot = gsn_csm_contour(wks, WORK , res)

  resp                  = True                      ; polyline mods desired
 ;resp@gsLineThicknessF = 2.0                       ; thickness of lines
  resp@gsLineDashPattern= 11

  tres       =  True
  tres@txFontHeightF = 0.0175
                                                    ; orig code rename
  if (opt .and. (isatt(opt,"dayLine") .or. isatt(opt,"dayLines"))) then
      if (opt .and. (isatt(opt,"dayLines"))) then
          day = min(opt@dayLines)
      else
          day = min(opt@dayLine)
      end if
  else
       day = 30         ; default 
  end if
  fline = 1./day

 ;resp@gsLineLabelString= day+"d"                   ; adds a line label string
;  gsn_polyline(wks,plot,(/fline,fline/),(/ 0.,NW/), resp)      
;  gsn_text(wks,plot, (day+"d"),fline+0.005,0.93*NW,tres)

                                                    ; orig code rename
  if (opt .and. (isatt(opt,"dayLine") .or. isatt(opt,"dayLines"))) then
      if (opt .and. (isatt(opt,"dayLines"))) then
          day = max(opt@dayLines)
      else
          day = max(opt@dayLine)
      end if
  else
       day = 80  
  end if
  fline = 1./day

 ;resp@gsLineLabelString= day+"d"                    ; adds a line label string
;  gsn_polyline(wks,plot,(/fline,fline/),(/ 0.,NW/), resp)      
;  gsn_text(wks,plot, (day+"d"),fline+0.005,0.93*NW,tres)

;  frame(wks)
  
  if (pltType.eq."png") then
      if (isatt(opt,"pltConvert")) then 
          pltConvert = opt@pltConvert    ; convert options
      else
          pltConvert = " "               ; default
      end if
      
      system("convert "+pltConvert+" "+pltPath+".eps "+pltPath+".png")
      system("rm -f "+pltPath+".eps")
  end if
  
  if (pltType.eq."x11" .and. isatt(opt,"debug") .and. opt@debug) then 
      
      res@gsnCenterString = "wf"
      plot = gsn_csm_contour(wks, wf, res)
      
      res@gsnCenterString = "wf({-5:5},{-0.075:0.075})"
      plot = gsn_csm_contour(wks, wf({-5:5},{-0.075:0.075}), res)
  end if  
end  

undef("mjo_xcor_lag_ovly_panel_here")
procedure mjo_xcor_lag_ovly_panel_here( \
                   ccr_a[*][*]:numeric, ccr_b[*][*]:numeric \
                  ,ccr_c[*][*]:numeric, ccr_d[*][*]:numeric \
                  ,pltType[1]:string, pltDir[1]:string      \
                  ,pltName[1]:string, opt[1]:logical        \
                  ,wks1:graphic,wks2:graphic,plot[2]:graphic)
local pltPath, pltTypeLocal, res1, res2, CCR1, CCR2 \
    , plt1, plt2, resP, plot1, plot2
begin

  pltPath = pltDir+"/"+pltName

  if (pltType.eq."png") then
      pltTypeLocal = "eps"
  else
      pltTypeLocal = pltType
  end if

;  wks  = gsn_open_wks(pltTypeLocal,pltPath)  
  if (opt .and. isatt(opt,"colorTable") .or. isatt(opt,"pltColorTable")) then
      if (isatt(opt,"colorTable")) then
          gsn_define_colormap(wks,opt@colorTable) 
      else
          gsn_define_colormap(wks,opt@pltColorTable) 
      end if
  else
     gsn_define_colormap(wks1,"BlWhRe") 
     gsn_define_colormap(wks2,"BlWhRe") 
  end if

  res1                      = True          ; color precip     
  res1@gsnDraw              = False
  res1@gsnFrame             = False
  res1@gsnMaximize          = True 
;  res1@gsnPaperOrientation  = "portrait"

  res1@cnFillOn             = True          ; turn on color
  res1@cnLinesOn            = False
;;No longer needed in V6.1.0 and later
;;res1@gsnSpreadColors      = True          ; use full range of colormap
  res1@cnLevelSelectionMode = "ManualLevels"; set manual contour levels
  res1@cnMinLevelValF       = -1.0          ; set min contour level
  res1@cnMaxLevelValF       =  1.0          ; set max contour level
  res1@cnLevelSpacingF      =  0.1          ; set contour spacing

  res1@cnLabelBarEndLabelsOn= True
  res1@cnLabelBarEndStyle   = "ExcludeOuterBoxes"
  res1@cnInfoLabelOn        = False

  res1@lbLabelBarOn         = False           ; turn off individual cb's

  res1@vpWidthF             = 0.4           ; change aspect ratio of plot
  res1@vpHeightF            = 0.3

 ;res1@gsnMajorLatSpacing   = 10            ; change maj lat tm spacing

  res1@tiYAxisString        = "lag (days)"
  if (isatt(opt,"tiMainString")) then
      res1@tiMainString     = opt@tiMainString
  end if
  if (isatt(opt,"gsnLeftString")) then
      res1@gsnLeftString    = opt@gsnLeftString
  end if
  if (isatt(opt,"gsnCenterString")) then
      res1@gsnCenterString  = opt@gsnCenterString
  end if
  if (isatt(opt,"gsnRightString")) then
      res1@gsnRightString   = opt@gsnRightString
  end if

;************************************************
; resource list for second data array
;************************************************
  res2                      = True              ; U
  res2@gsnDraw              = False
  res2@gsnFrame             = False
  res2@cnLevelSelectionMode = "ManualLevels"    ; set manual contour levels
  res2@cnMinLevelValF       = -1.0
  res2@cnMaxLevelValF       =  1.0
  res2@cnLevelSpacingF      =  0.1
  res2@cnLineLabelsOn       = True
  res2@gsnContourZeroLineThicknessF = 0. 	; Eliminate 0 line
  res2@gsnContourNegLineDashPattern = 1 	; negative contours dash pattern
 ;res2@cnLineThicknessF     = 2.                ; line thickness
  res2@cnInfoLabelOn        = False

;  plot                      = new( 2, "graphic")

  do np=0,1
     if (np.eq.0) then
         CCR1 = ccr_a             ; possible smooth and delete of attribute
         CCR2 = ccr_b
     else
         CCR1 = ccr_c             ; possible smooth and delete of attribute
         CCR2 = ccr_d
     end if
    
     if (opt .and. isatt(opt,"smth9") .and. abs(opt@smth9).eq.0.25) then
         CCR1 = smth9(CCR1, 0.50, opt@smth9, False)
         CCR2 = smth9(CCR2, 0.50, opt@smth9, False)
     end if
     delete(CCR1@long_name)
     if (np.eq.0) then
       plot1 = gsn_csm_contour(wks1,CCR1,res1)       ; contour the variable
       
       delete(CCR2@long_name)
       plot2 = gsn_csm_contour(wks1,CCR2,res2)       ; contour the variable
     else
       plot1 = gsn_csm_contour(wks2,CCR1,res1)       ; contour the variable
       
       delete(CCR2@long_name)
       plot2 = gsn_csm_contour(wks2,CCR2,res2)      
     end if
   
     overlay(plot1, plot2)
     plot(np) = plot1

     delete(CCR1)                                 ; size may change
     delete(CCR2)
  end do

  resP                      = True                ; panel
  resP@lbLabelAutoStride    = True
  resP@gsnPanelLabelBar     = True                ; add common colorbar
 ;resP@lbLabelFontHeightF   = 0.007               ; make labels smaller
  if (isatt(opt,"txString")) then
      resP@txString = opt@txString
  end if
;  gsn_panel(wks,plot,(/2,1/),resP)                ; now draw as one plot

  if (pltType.eq."png") then
      if (isatt(opt,"pltConvert")) then 
          pltConvert = opt@pltConvert    ; convert options
      else
          pltConvert = " "               ; default
      end if
      system("convert "+pltConvert+" "+pltPath+".eps "+pltPath+".png")
      system("rm -f "+pltPath+".eps")
  end if
end
;***********************************************************
