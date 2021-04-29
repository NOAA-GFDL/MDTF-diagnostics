;---------------------------------------------------------------------
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
;
; This file still has to be loaded manually
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin
      varcode = getenv("POD_HOME")

      wkdir = getenv("ENSO_MSE_WKDIR")

      prefix = wkdir + "/SCATTER/netCDF/"
 
;;---Tickmark resources
    dxx = (/  50., 50. /)
    dyy = (/  10., 10. /)
    xmin     =  (/ 0.,  0. /)
    xmax     =  (/ 180.,  200. /)
    ymin    =  (/ -25.,  -50. /)
    ymax    =  (/ 20.,   10. /)
    xlabel = "Precipitation [W/m~S~2~N~]"
;;;----------------------------------------------------------------------
;----------------------------------------------------------------------
;;  read in the data based on the region .. 
  
;;  columns -   rows = xdim, columns - ydim 
;;   xdim is the number of lines = models 
;;     ydim is the number of columns = variables 

    season = "DJF"
    mode = "El Nino"

;;;   the season  and mode pre-defined  -  only 2 predefined domain to consider 

    region = (/ "Central Pacific", "Eastern Pacific" /)

    nameout = (/ "central_elnino_01",  "eastern_elnino_01" /)
    namein1 = (/ "central_pacific_MSE_terms.txt", "eastern_pacific_MSE_terms.txt" /)
    namein2 = (/ "central_pacific_MSE_terms_NEW_MODEL.txt", "eastern_pacific_MSE_terms_NEW_MODEL.txt" /)  ;; NEW MODEL data 

   xdim = 37 
   ydim = 6

;; read in the models:
;;     namemodel = varcode +  "/SCATTER/list-models-historical-obs"
     namemodel = prefix + "list-models-historical-obs"
     models = readAsciiTable ( namemodel, 1, "string", 0)
     models2 = new ( (/ xdim+1 /), "string" )
     models2(0:xdim-1) = models(0:xdim-1, 0)
     models2(xdim) = "NEW MODEL"
;; 

   do ibox = 0, 1

    maintitle = region(ibox) +  " "  + " "  + mode + " (" + season + ")"

    namein11 = prefix + namein1(ibox) 
    datain1 = asciiread(namein11,(/xdim, ydim/),"float")
    undef2 = 1.1E+20
    datain1@_FillValue =  undef2
;;;  read the new model 
    namein22 = prefix + namein2(ibox)
    datain2 = asciiread(namein22,(/1, ydim/),"float")
    datain2@_FillValue =  undef2
;;;   fill dataX and dataY 
    dataX = new ( (/ xdim+1 /), float, datain1@_FillValue)
    dataY = new ( (/ xdim+1 /), float, datain1@_FillValue)
    dataX(0:xdim-1) = datain1(0:xdim-1, 0)
    dataX(xdim) = datain2(0, 0)
    dataY(0:xdim-1) = datain1(0:xdim-1, 1)
    dataY(xdim) = datain2(0, 1)

;;   printMinMax (dataX, False)
;;   printMinMax (dataY, False)
   
;----------------------------------------------------------------------
; Open a PNG file and define the color table
;----------------------------------------------------------------------
;;  colors  = (/"white","black","dodgerblue2","firebrick","forestgreen",\
;              "dodgerblue2","darkorange2","forestgreen","deeppink2",\
;              "darkorange2","purple"/)
;;  colors for the markers 
   colors1  = (/ 2,  3,   2,   3,   2,   3,  4,   2,  3,  4,  \ ;;   10
                 8,  2,   2,   3,   2,   2,  3,   4,  2,  3, \ ;;   20
                 4,  8,   2,   2,   2,   3,  4,   2,  3,  2, \  ;;; 30 
                 3,  4,   1,  14,   1,   14,  \                 ;; 36
                14,  6,  14,  14, 14 /)                  ;;; ERA +  NEW_MODEL 
                                                                        ;; 36 + 5 =  41

   markers1 =   (/16,  16,  1,  1,  2,  4,  5,  6,  6,  6,  \  ;; 10
                   6,   7,  8,  8,  9, 10, 10, 10, 11, 11,  \ ;;; 20
                   11, 11, 12, 13, 14, 14, 14, 15, 15,  0,  \ ;; 30 
                    0,  0,  0,  0,  1,  2,  \  ;;  36     
                    4, 12,  7,  5, 16/)               ;;      ERA + NEW_MODEL


    markersizes = (/ 0.02,  0.02, 0.02, 0.02, 0.02, 0.03, 0.03, 0.02, 0.03, 0.02, \ ;; 10 
                     0.02,  0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.03, 0.02, 0.02, \ ;; 20
                     0.02,  0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.03, 0.02,  \ ;; 30
                     0.02,  0.02, 0.02, 0.02,  0.02, 0.02,  \   ;; 36
                     0.03,  0.03, 0.03, 0.03,  0.03/)        ;;; ERA + NEW_MODEL


     markerthick =  (/   3., 3., 3., 3., 3., 10., 10.,  3., 10., 3., \  ;;  10
                         3., 3., 3., 3., 3.,  3.,  3., 10.,  3., 3., \ ;;; 20 
                         3., 3., 3., 3., 3.,  3.,  3.,  3., 10., 3.,  \ ;; 30
                         3., 3., 3., 3., 3., 3.,  \  ! 36
                        10., 10., 6.,  6., 6./)      ;; ERA + NEW_MODEL



;;  wks = gsn_open_wks ("ps","scatter")
;;   wks_type = "png"
;;   wks_type@wkWidth = 1000
;;   wks_type@wkHeight = 1000 
   wks_type = "eps"
;;     nameout2 = wkdir + "/SCATTER/PS/" + nameout(ibox)
   nameout2 = wkdir +  "/model/PS/" + nameout(ibox)
   wks = gsn_open_wks( wks_type, nameout2)

;;   wks = gsn_open_wks ("X11", "scatter")
    gsn_define_colormap(wks, "grads_default")

;----------------------------------------------------------------------
; Set some plot resources
;----------------------------------------------------------------------
;---Some calculations to get min/max for Y axis.
  dx = 5
  dy = 5
  miny = min(dataY) 
  maxy = max(dataY) 
  minx = min(dataX) - dx 
  maxx = max(dataX) + dx

    amaxy = maxy + dy
    aminy = miny - dy
;----------------------------------------------------------------------
;----------------------------------------------------------------------
; Draw time stamp first, then the plot.
;----------------------------------------------------------------------
;  infoTimeStamp(wks,0.005,"")
;;;;;; ***********  regression line  
   
   rc =   regline ( dataX, dataY)
   
;************************************************
; create an array to hold both the original data
; and the calculated regression line   
;     ---------
;     y = mx+b 
;     m is the slope:       rc      returned from regline
;     b is the y intercept: rc@yave attribute of rc returned from regline
;************************************************
   pltarry   = new ( (/2/), typeof(dataX), dataX@_FillValue)
   xx1       = new ( (/2/), typeof(dataX), dataX@_FillValue)
   xx1(0) =  minx
   xx1(1) =  maxx
   pltarry(:) = rc*(xx1-rc@xave) + rc@yave          ; use solid line

   rc = regline_stats( dataX, dataY)

;************************************************
; plotting parameters
; This illustrates one approach. Overlays could also be used.
;************************************************

   res1 = True
   res1@tiMainFont = "helvetica"
   res1@txFont   = "helvetica"
   res1@txFuncCode    = "~"

   res1@tmXBMode         =  "Explicit" ;; "Manual"
   res1@tmYLMode         =  "Explicit" ;;  "Manual"
   res1@tmXBTickSpacingF =  dxx(ibox)
   res1@tmYLTickSpacingF =  dyy(ibox) 
   res1@trXMinF           = xmin(ibox)
   res1@trXMaxF           = xmax(ibox)
   res1@trYMinF           = ymin(ibox)
   res1@trYMaxF           = ymax(ibox)

  res1@gsnDraw            = False       ; Don't draw plot
  res1@gsnFrame           = False       ; Don't advance frame
;;;
  res1@vpXF              = 0.18 ;; 0.14
  res1@vpYF              = 0.8  ;; 0.82
  res1@vpWidthF          = 0.53 ;; 0.55
  res1@vpHeightF         = 0.53 ;; 0.55

;---Title resources
  res1@txFont   = "helvetica"
  res1@tiMainString       = maintitle
;;  res1@tiXAxisString      =  xlabel
 ;; res1@tiYAxisString      =  ylabel
  res1@tiMainFontHeightF  = 0.02
;;;; X label
    txres3 = True
    txres3@txFuncCode    = "~"
    txres3@txFont   = "helvetica"
    txres3@txFontHeightF = 0.025
    gsn_text_ndc(wks, xlabel, 0.45, 0.17, txres3)

;;  the Y axis separate  as an equation
;;   -< v * delq >`
   txres4 = True
   txres4@txFuncCode    = "~"
;;   txres4@txFont   = "helvetica"

  xx4 = 0.08
  yy4 = 0.45 
 
;; - minus
  txres4@txAngleF  = 90.
  txres4@txFontHeightF =  0.020 ;;;  0.025
  gsn_text_ndc(wks, "~F22~-", xx4, yy4, txres4)
 
;;  left paranth
  dyy4 = 0.013
  yy4 = yy4 + dyy4
  gsn_text_ndc(wks, "~F34~a", xx4, yy4, txres4)
  
;;;  V
  dyy4 = 0.018
  yy4 = yy4 + dyy4
  gsn_text_ndc(wks, "~F25~V", xx4, yy4, txres4)
 
;;;  dot  
  dyy4 = 0.018
  yy4 = yy4 + dyy4
  gsn_text_ndc(wks, "~F18~.", xx4, yy4, txres4)

;;; 
;;  del   q 
  dyy4 = 0.02
  yy4 = yy4 + dyy4
  gsn_text_ndc(wks, "~F34~Q", xx4, yy4, txres4)

  dyy4 = 0.02
  yy4 = yy4 + dyy4
;;  gsn_text_ndc(wks, "~F25~q", xx4, yy4, txres4)
  gsn_text_ndc(wks, "~F14~q", xx4, yy4, txres4)
 
  dyy4 = 0.02
  yy4 = yy4 + dyy4
  gsn_text_ndc(wks, "~F34~q", xx4, yy4, txres4)

;;; prime
  dxx4 = -0.01
  dyy4 = 0.01
  yy4 = yy4 + dyy4
  xx4 = xx4 + dxx4
  gsn_text_ndc(wks, "~F18~c", xx4, yy4, txres4)

;;;  unit
  txres4@txFont   = "helvetica"
  dyy4 = 0.06
  dxx4 = 0.01
  yy4 = yy4 + dyy4
  xx4 = xx4 + dxx4
  gsn_text_ndc(wks,"[W/m~S~2~N~]", xx4, yy4, txres4)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

   res1@tiMainFontHeightF  = 0.02
;---Resources for X/Y axes.
;  res1@trYMinF            =  aminy               ; min value on y-axis
;  res1@trYMaxF            =  amaxy               ; max value on y-axis
;  res1@trXMinF            =  minx                  ; min value on x-axis
;  res1@trXMaxF            =  maxx                  ; max value on x-axis
 
  res1@tmLabelAutoStride = True
;--XY marker resources
  res1@xyMarkLineMode     = "Markers"
;;  res1@xyMarkerSizeF      = 0.02
;;  res1@xyMarkerThicknessF = 3.
  res1@xyMonoMarkerColor  = False          ; Allow different colors for markers
  res1@xyMarkerSizes            = markersizes(:)
  res1@xyMarkerThicknesses      = markerthick(:)

  res1@xyMarkerColors     = colors1(:)     ; It's okay to list more than
                                          ; you need here
  res1@xyMarkers          =  markers1(:)

;---Title resources
  res1@tiMainString       = maintitle
  res1@tiMainFontHeightF  = 0.03
  plot1 = gsn_csm_xy (wks,transpose((/dataX,dataX/)), \
                         transpose((/dataY,dataY/)),res1)
   draw(plot1)

;; for the line  of regressed variables 
    
   res1@xyMarkLineMode      = "Lines"
   res1@xyLineColors        = "red"  ; choose which have markers
;;   res1@xyMarkerSizeF       = 0.005  ; Marker size (default 0.01)
   res1@xyDashPatterns      = 0                ; solid line 
   res1@xyLineThicknesses   = 4                 ; 

   plot2  = gsn_csm_xy (wks, xx1,pltarry,res1)           ; create plot
   draw(plot2)
;----------------------------------------------------------------------
; Draw some markers and text. based on external file :
;----------------------------------------------------------------------
  labels2  = models2 

  mkres               = True         ; Marker resources
  txres               = True         ; Text resources
  txres@txFontHeightF = 0.01
  txres@txJust        = "CenterLeft"
  txres@txAngleF  = 0.

  xpos2 = 0.75
  xpos3 = xpos2 + 0.03

  ypos2 = 0.90
  dyy2 = 0.018
  do i = 0, xdim
      ypos2 = ypos2 - dyy2
      txres@txFontThicknessF = 1.
      txres@txFontColor =  colors1(i)
      txres@txFont   = "helvetica"
      txres@txFontHeightF = 0.01
     mkres@gsMarkerColor =  colors1(i)
     mkres@gsMarkerThicknessF = 3.5
     mkres@gsMarkerSizeF      = 0.012
     mkres@gsMarkerIndex      = markers1(i)
     fheight  = 0.016
     fthick = 6.
     mthick = 6.

;;  bold selected markers = models2
     if( (i .eq. 5) .or. (i .eq. 6) .or. (i .eq. 8) .or.  (i .eq. 17) .or.  \
         (i .eq. 28) .or. (i .ge. xdim-1) )  then
       txres@txFontHeightF = fheight
       txres@txFont   = "helvetica-bold"
       txres@txFontThicknessF = fthick
       mkres@gsMarkerThicknessF = mthick
     end if

     gsn_polymarker_ndc(wks,             xpos2, ypos2, mkres)
     gsn_text_ndc      (wks,labels2(i),xpos3, ypos2, txres)
  end do

;;;  the correlations
     correlation  =  sprintf("%9.3f", rc@bstd(1))
     regression   =  sprintf("%9.3f", rc@b(1))
;;  print the correlation and regression values
      txres2 = True
      txres2@txFontColor =  "red"
      txres2@txFont   = "helvetica"
      txres2@txFontHeightF = 0.013
      txres@txJust        = "CenterLeft"

     label1 = (/"Regression=", " ", regression/)
     new_label1 = str_concat(label1)
     xs1 = 0.595 ;;; 0.75
     ys1 = 0.31 ;;;  0.18
     dy2 = -0.022
     gsn_text_ndc (wks, new_label1, xs1, ys1, txres2)

     label2 = (/"Correlation="," ", correlation/)
     new_label2 = str_concat(label2)
     xs2 = xs1
     ys2 = ys1 + dy2
      gsn_text_ndc (wks, new_label2, xs2, ys2, txres2)

  frame(wks)    ; Now advance the frame.

   end do  ;;;;  over boxes 
end
