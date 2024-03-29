;---------------------------------------------------------------------
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
    ymin    =  (/ 0.,  0. /)
    ymax    =  (/ 40.,   50. /)
    xlabel = "Precipitation [W/m~S~2~N~]"
    ylabel = "F~B~rad~N~ [W/m~S~2~N~]"
;;;----------------------------------------------------------------------
;;  columns -   rows = xdim, columns - ydim 
;;   xdim is the number of lines = models 
;;   ydim is the number of columns = variables 

   season = "DJF"
   mode = "El Nino"

    region = (/ "Central Pacific", "Eastern Pacific" /)

    nameout = (/ "central_elnino_02",  "eastern_elnino_02" /)
    namein1  = (/ "central_pacific_MSE_terms.txt", "eastern_pacific_MSE_terms.txt" /)
    namein2 = (/ "central_pacific_MSE_terms_NEW_MODEL.txt", "eastern_pacific_MSE_terms_NEW_MODEL.txt" /)  ;; NEW MODEL data

   xdim = 37
   ydim = 6

;; read in the models:
     namemodel = prefix + "list-models-historical-obs"
     models = readAsciiTable ( namemodel, 1, "string", 0)
     models2 = new ( (/ xdim+1 /), "string" )
     models2(0:xdim-1) = models(0:xdim-1, 0)
     models2(xdim) = "NEW MODEL"

;;  the order of datain is the order of variables  SST first , RR second

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
    dataY(0:xdim-1) = datain1(0:xdim-1, 2)
    dataY(xdim) = datain2(0, 2)

;----------------------------------------------------------------------
; Open a PNG file and define the color table
;----------------------------------------------------------------------
;;  colors for the markers 

  colors1  = (/ 2,  3,   2,   3,   2,   3,  4,   2,  3,  4,  \ ;;   10
                 8,  2,   2,   3,   2,   2,  3,   4,  2,  3, \ ;;   20
                 4,  8,   2,   2,   2,   3,  4,   2,  3,  2, \  ;;; 30
                 3,  4,   1,  14,   1,   14,  \                 ;; 36
                14,  6,  14,  14, 14 /)                  ;;; ERA +  NEW_MODEL

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


     markerthick =  (/   3., 3., 3., 3., 3., 10., 10.,  3., 10., 3., \  ;;  
                         3., 3., 3., 3., 3.,  3.,  3., 10.,  3., 3., \ ;;; 
                         3., 3., 3., 3., 3.,  3.,  3.,  3., 10., 3.,  \ ;; 
                         3., 3., 3., 3., 3., 3.,  \  ! 36
                        10., 10., 6.,  6., 6./)      ;; ERA + NEW_MODEL


   wks_type = "eps"
   nameout2 = wkdir +  "/model/PS/" + nameout(ibox)
   wks = gsn_open_wks( wks_type, nameout2)

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
;************************************************

   res1 = True
   res1@tiMainFont = "helvetica"
   res1@txFont   = "helvetica"
   res1@txFuncCode    = "~"

   res1@tmXBMode         =  "Explicit" ;; 
   res1@tmYLMode         =  "Explicit" ;; 
   res1@tmXBTickSpacingF =  dxx(ibox)
   res1@tmYLTickSpacingF =  dyy(ibox) 
   res1@trXMinF           = xmin(ibox)
   res1@trXMaxF           = xmax(ibox)
   res1@trYMinF           = ymin(ibox)
   res1@trYMaxF           = ymax(ibox)

  res1@gsnDraw            = False       ; 
  res1@gsnFrame           = False       ; 
;;;
  res1@vpXF              = 0.18 ;; 
  res1@vpYF              = 0.8  ;; 
  res1@vpWidthF          = 0.53 ;;
  res1@vpHeightF         = 0.53 ;; 

;---Title resources
  res1@txFont   = "helvetica"
  res1@tiMainString       = maintitle
  res1@tiMainFontHeightF  = 0.02
;;;; X label
    txres3 = True
    txres3@txFuncCode    = "~"
    txres3@txFont   = "helvetica"
    txres3@txFontHeightF = 0.025
    gsn_text_ndc(wks, xlabel, 0.45, 0.17, txres3)

    txres4 = True
    txres4@txFuncCode    = "~"
    txres4@txFont   = "helvetica"
    txres4@txAngleF  = 90.
    txres4@txFontHeightF = 0.025
    gsn_text_ndc(wks, ylabel, 0.08, 0.54, txres4)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

   res1@tiMainFontHeightF  = 0.02
 
  res1@tmLabelAutoStride = True

  res1@xyMarkLineMode     = "Markers"
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

;;  bold selected markers = models
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
