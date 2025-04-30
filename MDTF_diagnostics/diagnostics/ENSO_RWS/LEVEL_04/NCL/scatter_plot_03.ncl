;; 
;  RR vs adiv 
;
; This file still has to be loaded manually
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin

  prefix =  getenv("OBS_DATA") + "/SCATTER/"

   datadir  =  getenv("ENSO_RWS_WKDIR") + "/model/netCDF/ELNINO/"
   datadir2  =  getenv("ENSO_RWS_WKDIR") + "/model/netCDF/"
   outputdir =  getenv("ENSO_RWS_WKDIR") + "/model/PS"

    case = "CASE_03"
    nameout = "scatter_03"
    prefix1 = prefix + "/" + case

     wks_type = "eps"

     mindex =  12
     msize  =  0.025 ;; 
     mcolor =  (/ "red" /)
     mthick = 10
     mlabel = "NEW MODEL"

;;---Tickmark resources
    xmin  =  0.0
    xmax  =  1.5
    dxx   =  0.2

    ymin  =  -4
    ymax  =  14
    dyy   =   2

    xlabel = "Positive precip anomalies [110:F34:0:F:E-140:F34:0:F:E; 22:F34:0:F:-32:F34:0:F:N] [mm/day]"
     ix = 0
     ff1 = 1.

     eqn1 = ":F18:-:F8:n:S::F0:':N::B::F8:c:N::F34:WQ:N::F8:x:N::H-8::V20::F21:-:N:"
     xe1 = 0.06
     ye1 = 0.29

     ylabel = ":F:[100:F34:0:F:E-140:F34:0:F:E; 22:F34:0:F:-32:F34:0:F:N] [10:S:-11:N:s:S:-2:N:]"
     iy = 1
     ff2 = 1.E+11

    undef2 = -9999.
    tt0 = 0 
;;;;;;;;;;;;  RR positive anomaly 
    lon1 = 110.
    lon2 = 140.
    lat1 = 22.
    lat2 = 32.
    nameinX =  datadir + "/" + "pr.nc"
    nameinX2 =  datadir2 + "/" + "pr.nc"
;;   RWS term 2
    lon11 = 150.
    lon22 = 360. - 160.
    lat11 = 25.
    lat22 = 40.
    plevel22 = 200.
    nameinU =  datadir + "/" + "ua.nc"
    nameinV =  datadir + "/" + "va.nc"
    nameinU2 =  datadir2 + "/" + "ua.nc"
    nameinV2 =  datadir2 + "/" + "va.nc"   ;; climatologies
;; calculate RR+ and  RWS term 2,  need climatology too
 
     f = addfile( nameinX, "r")
     lon = f->lon
     lat = f->lat
     pra = f->pr
     delete( f)
     f = addfile( nameinX2, "r")
     lon = f->lon
     lat = f->lat
     prc = f->pr
     delete( f)
     rr = 24.*60.*60. ;;;  convert to mm/day
     pra = (pra - prc) * rr
;;;   make it  only positive
     pra = where( pra .ge. 0., pra, pra@_FillValue)
;;     make it area average lon1, lon2, lat1, lat2
     xx = wgt_areaave_Wrap(pra(tt0,  {lat1:lat2}, {lon1:lon2}),1.0,1.0,0)
;;;  RW2 term 2
     omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.
   
     fu = addfile( nameinU, "r")
     fv = addfile( nameinV, "r")
     lon = fu->lon
     lat = fu->lat
     plev1 = fu->lev
     xdim1 = dimsizes( lon)
     ydim1 = dimsizes( lat)
     zdim1 = dimsizes( plev1)
     ua = fu->ua
     va = fv->va
     delete( [/ fu, fv /])
     fu = addfile( nameinU2, "r")
     fv = addfile( nameinV2, "r")
     uc = fu->ua
     vc = fv->va
;; make anomalies 
     ua = ua - uc
     va = va - vc 

     do k = 0, zdim1 - 1
     if( plev1(k) .eq. plevel22)
     kk1 = k
     end if
     end do
    
      term2 = ua  ;; 
      sinlat = sin( lat * pi/180.)
      fcoriol = 2.* omega * sinlat
    
      cvort2 =  uv2vr_cfd(uc, vc, lat, lon, 3)
      cvort = cvort2
       do j = 0, ydim1 - 1
       cvort(:,:,j, :) =  tofloat( fcoriol(j))  + cvort2(:,:,j,:)
       end do

     cvort_grad =  grad_latlon_cfd( cvort, lat, lon, True, False)
   
     cvortx = tofloat(cvort_grad[1])
     cvorty = tofloat(cvort_grad[0])

     adiv = ua
     adiv = uv2dv_cfd (ua, va, lat, lon, 3)
;;;  fill in adiv and cdiv
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill( adiv, gtype, guess, nscan, eps, relc, opt)

    aUVdiv = dv2uvF_Wrap (adiv)
;;  mask the undefined   0 = zonal  1 = meridional
    aUVdiv(0, :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), aUVdiv(0, :, :, :, :), ua@_FillValue)
    aUVdiv(1, :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), aUVdiv(1, :, :, :, :), ua@_FillValue)

    term2(:, :, :, :) = -1.*( aUVdiv(0, :, :, :, :) * cvortx(:, :, :, :) +  aUVdiv(1, :, :, :, :) * cvorty(:, :, :, :))

      yy = ff2 * wgt_areaave_Wrap ( term2(0, kk1, {lat11:lat22}, {lon11:lon22}),1.0,1.0,0)
 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;   custom markers
    mstring5 = (/ "5", "5", "5", "5", "5", "5", "5", "5", "5", "5", \
                   "5", "5", "5"  /)
    mstring6 = (/ "6", "6", "6", "6", "6", "6", "6", "6", "6", "6", \
                   "6", "6", "6" /)

    fontnum  = 30
    xoffset = 0
    yoffset = 0
    ratio = 1
    size  = 1
    angle = 0

;;   collect CMIP5 CMIP6 and OBS data :
   maintitle = " AMIP5/6 "
   season = "DJF"
   mode = "El Nino"

    namein1 = prefix1 +  "/" + "scatter_data_AMIP5.txt"
    namein2 = prefix1 +  "/" + "scatter_data_AMIP6.txt"
    namein3 = prefix1 + "/" + "scatter_data_OBS.txt"
    list1 = prefix + "/" + "list-amip5.txt"
    list2 = prefix + "/" + "list-amip6.txt"
    list3 = prefix + "/" + "list-OBS.txt"

;;;----------------------------------------------------------------------
;----------------------------------------------------------------------
;;  read in the data based on the region .. 
;;  columns -   rows = xdim, columns - ydim 
;;   xdim is the number of lines = models 
;;     ydim is the number of columns = variables   - reads in 3 files:
   xdim1 = 12
   ydim1 = 2
   datain1 = asciiread(namein1,(/xdim1, ydim1/),"float") 
   model1 =   readAsciiTable ( list1, 1, "string", 0)
 
   xdim2 =  12;
   ydim2 =  2
   datain2 = asciiread(namein2,(/xdim2, ydim2/),"float")
   model2 = readAsciiTable ( list2, 1, "string", 0)

   xdim3 = 5
   ydim3 = 2
   datain3 = asciiread(namein3,(/xdim3, ydim3/),"float")
   model3 =  readAsciiTable ( list3, 1, "string", 0)
    datain1@_FillValue = undef2
    datain2@_FillValue = undef2
    datain3@_FillValue = undef2

;;  the order of datain is the order of variables  SST first , RR second
;;  loop over integrals  
;;; also combine dataX and dataY
    xdim = xdim1 + xdim2 + xdim3
    ydim = ydim1
    datain  = new ( (/xdim, ydim/), typeof(datain1)  )
    ix1 = 0
    ix2 = xdim1 -1
    datain(ix1:ix2, :) = datain1(ix1:ix2, :)
    ix1 = ix2 + 1
    ix2 = ix1 + xdim2 -1
    datain(ix1:ix2,  :) = datain2(0:xdim2-1,  :)
    ix1 = ix2 + 1 ;  xdim2
    ix2 = ix1 + xdim3 -1
    datain(ix1:ix2,  :) = datain3(0:xdim3-1,  :)
    datain@_FillValue = undef2


   iyy = iy
   ixx = ix
   dataX1 = ff1 * datain1( :, ixx)
   dataY1 = ff2 * datain1( :, iyy)

   dataX2 = ff1 * datain2(:, ixx)
   dataY2 = ff2 * datain2(:, iyy)

   dataX3 = ff1 * datain3(:, ixx)
   dataY3 = ff2 * datain3(:, iyy)
  
   dataX = ff1 * datain(:, ixx)
   dataY = ff2 * datain(:, iyy)
   
   
;----------------------------------------------------------------------
; Open a PNG file and define the color table
;----------------------------------------------------------------------

    colors1 = (/  "black", "saddlebrown", "blue", "green", "plum2", "red", \
             "orange", "hotpink",  "cadetblue2", "purple",  "darkseagreen3", "grey50" /)


    markers1 =   (/  1,   1,  1,  1,  1,  \
                     1,   1,  1,  1,  1,  \
                     1,   1, 1 /)


     markersizes1 = (/ 0.01, 0.01, 0.015, 0.01, 0.01, 0.015,  \
                      0.01, 0.01, 0.01, 0.01, 0.01, 0.01 /)

     markerthick1 = (/ 5, 5, 7, 5, 5, 7, 5, 5, 5, \
                      5, 5, 5 /)

     markersizes11 = (/  0.01, 0.01, 0.01, 0.01, 0.01, 0.01,  \
                      0.01, 0.01, 0.01, 0.01, 0.01, 0.01 /)

     markerthick11 = (/ 5, 5, 5, 5, 5, 5, 5, 5, 5, \
                      5, 5, 5 /)

;;;;  

   markers3 = (/  4,  5, 6, 7, 8 /)
    colors3 = (/ "black",  "black", "black",  "black", "black" /) ;; 
   markersizes3 = (/ 0.025, 0.025, 0.025, 0.025, 0.025  /)
   markerthick3 = (/ 10, 10, 10, 10, 10  /)

   markersizesR = (/ 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015,  \
                    0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015,  \
                    0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015,  \
                    0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015,  \
                    0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015,  \
                    0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, \
                    0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, \
                    0.015, 0.015/)

   markerthickR = (/ 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,  \
                    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,  \
                    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,  \
                    5, 5 /)

;;  colors for the markers 

  nameout2 =  outputdir + "/" +   nameout
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

;    amaxy = maxy + dy
;    aminy = miny - dy
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
; This illustrates one approach. Overlays could also be used.
;************************************************

   res1 = True

   res1@txFuncCode       = ":"
   res1@tiMainFuncCode   = ":"
   res1@tiXAxisFuncCode  = ":"
   res1@tiYAxisFuncCode  = ":"
   res1@tmXBMode         = "Manual"
   res1@tmYLMode         = "Manual"
   res1@tmXBTickSpacingF =  dxx
   res1@tmYLTickSpacingF =  dyy
   res1@trXMinF           = xmin
   res1@trXMaxF           = xmax
   res1@trYMinF           = ymin
   res1@trYMaxF           = ymax

   res1@tmYLFormat = "0@;*.2f" ;;

  res1@gsnDraw            = False       ; Don't draw plot
  res1@gsnFrame           = False       ; Don't advance frame
;;;
  res1@vpXF              = 0.14 ;; 
  res1@vpYF              = 0.82
  res1@vpWidthF          = 0.55 ;; 
  res1@vpHeightF         = 0.55

;---Title resources
  res1@tiMainString       = maintitle + " " +  mode +  " " + season
  res1@tiXAxisString      =  xlabel
  res1@tiYAxisString      =  ylabel 
  res1@tiMainFontHeightF  =  0.02
  res1@tiXAxisFontHeightF = 0.015
  res1@tiYAxisFontHeightF = 0.015

  res1@tmLabelAutoStride = True
;--XY marker resources

  res1@xyMarkLineMode     = "Markers"
  res1@xyMonoMarkerColor  = False ;;;;    ; Allow different colors for markers
  res1@xyMarkerSizes       = markersizes1(:)
  res1@xyMarkerColors      = colors1(:)
  res1@xyMarkerThicknesses = markerthick1(:)
  res1@xyMarkers     = NhlNewMarker(wks, mstring5, fontnum, xoffset, yoffset, ratio, size, angle)

  plot1 = gsn_csm_xy (wks,transpose((/dataX1,dataX1/)), \
                         transpose((/dataY1,dataY1/)),res1)

  delete( res1@xyMarkers )
  delete( res1@xyMarkerSizes)
  delete( res1@xyMarkerThicknesses)

  res1@xyMarkerSizes       = markersizes1(:)
  res1@xyMarkerThicknesses = markerthick1(:)
  res1@xyMarkerColors    = colors1(:)
  res1@xyMarkers     = NhlNewMarker(wks, mstring6, fontnum, xoffset, yoffset, ratio, size, angle)
  plot2 = gsn_csm_xy (wks,transpose((/dataX2,dataX2/)), \
                         transpose((/dataY2,dataY2/)),res1)

  delete( res1@xyMarkerSizes )
  delete( res1@xyMarkerColors )
  delete( res1@xyMarkerThicknesses )
  delete( res1@xyMarkers )
  
  res1@xyMarkerSizes       = markersizesR(:)
  res1@xyMarkerThicknesses = markerthickR(:)
  res1@xyMarkerColors    = colors3(:)
  res1@xyMarkers         = markers3(:)
  plot3 = gsn_csm_xy (wks,transpose((/dataX3,dataX3/)), \
                         transpose((/dataY3,dataY3/)),res1)
    
;;;;;;;;;;;;;;;;;;;;;;;;;;;
 ;;; added  eqn1
      txres2 = True
      txres2@txFuncCode       = ":"
      txres2@txFontColor =  "black"
      txres2@txFont   = "times-roman" ;;;
      txres2@txFontThicknessF = 2.
      txres2@txAngleF  = 90
      txres2@txFontHeightF = 0.016 ;;  
      txres2@txJust        = "CenterLeft"

     xs1 = 0.1  ;; 
     ys1 = 0.14  ;;
     dy2 = -0.022
     gsn_text_ndc (wks, eqn1, xe1, ye1, txres2)
     delete( txres2 )

   draw( plot1)
   draw( plot2)
   draw( plot3)

;;;;;;;;;;;;;
   res1@xyMarkLineMode      = "Lines"
   res1@xyLineColors        = "red"  ; choose which have markers
   res1@xyDashPatterns      = 0                ; solid line
   res1@xyLineThicknesses   = 4

;;;;;;;;;;; added list of models on side :
   labels1  = model1
   mkres               = True         ; Marker resources
   txres               = True         ; Text resources
   txres@txJust        = "CenterLeft"
   txres@txAngleF  = 0.
   txres@txFuncCode       = ":"
   txres@txFontColor =  "black"
   txres@txFont   = "times-bold" ;;; 
   txres@txFontHeightF =  0.015 ;;  
   xpos1 = 0.7 ;; 
   xpos2 = xpos1 + 0.03
   ypos1 = 0.85 ;; 

   gsn_text_ndc (wks, "AMIP5", xpos2, ypos1, txres)     
   dyy3 =  0.02 ;
   ypos2 = ypos1 - dyy3
;;   loop over model1 
   txres@txFont   = "times-roman" ;;; "helvetica"
   txres@txFontHeightF =  0.013 
   do i = 0, xdim1-1
      ypos2 = ypos2 - dyy3
      txres@txFontThicknessF = 1.
      txres@txFontColor =  colors1(i)
      txres@txFont   =  "times-roman" ;;;;
      mkres@gsMarkerColor =  colors1(i)
      mkres@gsMarkerThicknessF = 3.5
      mkres@gsMarkerSizeF      = 0.015 ;; 
      mkres@gsMarkerIndex      = markers1(i)
      
     gsn_text_ndc      (wks, labels1(i,0), xpos2, ypos2, txres)
  end do

;;;;;; repeat for AMIP6 
   delete( mkres)
   delete( txres) 
   labels2  = model2
   mkres               = True         ; Marker resources
   txres               = True         ; Text resources
   txres@txFontHeightF = 0.015
   txres@txJust        = "CenterLeft"
   txres@txAngleF  = 0.
   txres@txFuncCode       = ":"
   txres@txFontColor =  "black"
   txres@txFont   = "times-bold" ;;; "helvetica"
   xpos1 = xpos1 ;;  
   xpos2 = xpos1 + 0.03
   ypos1 = ypos2 - 0.05 ;;
   gsn_text_ndc (wks, "AMIP6", xpos2, ypos1, txres)

   ypos2 = ypos1 - dyy3
;;   loop over model2
   txres@txFont   = "times-roman" ;;; "helvetica"
   txres@txFontHeightF =  0.013 
   do i = 0, xdim2-1
      ypos2 = ypos2 - dyy3
      txres@txFontThicknessF = 1.
      txres@txFontColor =  colors1(i)
      txres@txFont   =  "times-roman" ;;;;"helvetica"
      mkres@gsMarkerColor =  colors1(i)
      mkres@gsMarkerThicknessF = 3.5
      mkres@gsMarkerSizeF      = 0.012
      mkres@gsMarkerIndex      = markers1(i)

     gsn_text_ndc      (wks,labels2(i,0),xpos2, ypos2, txres)
  end do

;;;;;;;; observations are the last 
   delete( mkres)
   delete( txres)
   labels3  = model3
   mkres               = True         ; Marker resources
   txres               = True         ; Text resources
   txres@txFontHeightF = 0.01
   txres@txJust        = "CenterLeft"
   txres@txAngleF  = 0.
   txres@txFuncCode       = ":"
   txres@txFontColor =  "black"
   txres@txFont   = "times-roman" ;;; 
   txres@txFontHeightF =  0.013
   xpos1 = xpos2 ;;  
   xpos2 = xpos1 + 0.03 
   ypos1 = ypos2 - 0.05 ;; 
   dyy3 = 0.03 ;;  
   ypos2 = ypos1 ;;  

;;   loop over model3
   do i = 0, xdim3-1
      ypos2 = ypos2 - dyy3
      txres@txFontThicknessF = 1.
      txres@txFontColor =  colors3(i)
      txres@txFont   =  "times-roman" ;;;;
      mkres@gsMarkerColor =  colors3(i)
      mkres@gsMarkerThicknessF = 10. ;;  
      mkres@gsMarkerSizeF      =  0.015 ;; 
      mkres@gsMarkerIndex      = markers3(i)

      gsn_polymarker_ndc(wks,  xpos1, ypos2, mkres)
     gsn_text_ndc      (wks, labels3(i,0), xpos2, ypos2, txres)
  end do

;;;;;;;;;  add the new model  here !!  xx yy coordinates
   pres = True
   pres@gsMarkerIndex =  mindex           ; choose circle as polymarker
   pres@gsMarkerSizeF =  msize          ; select size to avoid streaking
   pres@gsMarkerColor =  mcolor
   pres@gsMarkerThicknessF = mthick

   gsn_polymarker(wks, plot1, xx, yy, pres)

     xpos1 = xpos1 ;;
     xpos2 = xpos1 + 0.03
     ypos2 = ypos2 - dyy3
     ypos2 = ypos2 - dyy3
     txres@txFontThicknessF = 1.
     txres@txFontColor =  mcolor
      txres@txFont   =  "times-roman" ;;;;
      mkres@gsMarkerColor = mcolor
      mkres@gsMarkerThicknessF = 10. ;;
      mkres@gsMarkerSizeF      = msize
      mkres@gsMarkerIndex      =  mindex
      gsn_text_ndc      (wks, mlabel, xpos2, ypos2, txres)
      gsn_polymarker_ndc(wks,  xpos1, ypos2, mkres)


;;;;;;;;;;;;;;;;;;;;;
   correlation  =  sprintf("%9.3f", rc@bstd(1))
   regression   =  sprintf("%9.3f", rc@b(1))
;;  print the correlation and regression values
      txres2 = True
      txres2@txFontColor =  "red"
      txres2@txFont   = "times-roman" ;;; 
      txres2@txFontHeightF =  0.013  ;;;
      txres@txJust        = "CenterLeft"

     label1 = (/"Regression=", " ", regression/)
     new_label1 = str_concat(label1)
     xs1 = 0.45 ;;  
     ys1 = 0.31 ;;;
     dy2 = -0.022

     label2 = (/"Correlation="," ", correlation/)
     new_label2 = str_concat(label2)
     xs2 = xs1
     ys2 = ys1 + dy2


  frame(wks)    ; Now advance the frame.
;;;   print max min levels 
   min_p = min( dataX)
   max_p = max( dataX)
   min_y = min( dataY)
   max_y = max( dataY)

end
