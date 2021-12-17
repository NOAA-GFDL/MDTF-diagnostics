;; 
;  RR vs adiv 
;
; This file still has to be loaded manually
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin

  prefix =  getenv("OBS_DATA") + "/SCATTER_05/"

   datadir  =  getenv("ENSO_RWS_WKDIR") + "/model/netCDF/ELNINO/"
   datadir2  =  getenv("ENSO_RWS_WKDIR") + "/model/netCDF/"
   outputdir =  getenv("ENSO_RWS_WKDIR") + "/model/PS"

    case = "CASE_08"
    nameout = "scatter_08"

    prefix1 = prefix + "/" + case

     wks_type = "eps"

     mindex =  12
     msize  =  0.025 ;; 
     mcolor =  (/ "red" /)
     mthick = 10
     mlabel = "NEW MODEL"

;;---Tickmark resources
    xmin  =  -20 ;;
    xmax  =   50;; 
    dxx   =   10 ;; 

    ymin  = 0.0 ;;  
    ymax  = 4.0 ;;   
    dyy   = 0.4 ;; 

    ylabel = "PNA standardized index "
     iy = 1
     ff2 = 1.

    xlabel = "Beta* zero ''longitude'' with respect to dateline"
     ix = 0
     ff1 = 1

;;  XX  betastar ZERO line extend from 180E 
    zero_limit = 0.   
    lon180 = 180.
    lon1 = lon180 - 40.
    lon2 = lon180 +  40. 

    lat1 = 40.
    lat2 = 60.
    plevel2 = 200.
    nameinU =  datadir + "/" + "ua.nc"
    nameinV =  datadir + "/" + "va.nc"
    nameinU2 =  datadir2 + "/" + "ua.nc"
    nameinV2 =  datadir2 + "/" + "va.nc"   ;; climatologies
;;;;  calculate the betastar at 200 mb
    omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.
    ff22 = 1E+11
    undef2 = -9999.

     fu = addfile( nameinU, "r")
     fv = addfile( nameinV, "r")
     lon = fu->lon
     lat = fu->lat
     plev1 = fu->lev
     time = fu->time

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
    uc!0 = "time"
    uc!1 = "lev"
    uc!2 = "lat"
    uc!3 = "lon"
;; make anomalies
     ua = ua - uc
     va = va - vc
    do k = 0, zdim1 - 1
     if( plev1(k) .eq. plevel2)
     kk1 = k
     end if
     end do
;;; calculate the betastar 
    betastar = uc
    avort  = ua
    cvort2  = uc
    avort  =  uv2vr_cfd(ua, va, lat, lon, 3) ;;
    cvort2 =  uv2vr_cfd(uc, vc, lat, lon, 3) ;;

    sinlat = sin( lat * pi/180.)
    fcoriol = 2.* omega * sinlat

    coslat =  cos(lat * pi/180.)
    beta = 2.* omega * coslat/rearth
    
      do j = 1, ydim1-2                      ; loop over each latitude
      dlat = 0.5 * (lat(j+1)-lat(j-1))
      dY = rearth * dlat * pi/180.  ; constant at this latitude
      Uc2 = (uc(:,:,j+1,:) - 2.*uc(:,:,j,:) + uc(:,:,j-1,:))/(dY*dY)
      betastar(:,:, j, :) =  (  tofloat( beta(j))  - tofloat( Uc2) )
      end do
      betastar = ff22 * betastar
;;;  smoothing
   nscan = 500             ; usually *much* fewer
   eps   = 0.001            ; variable depended
   gtype =  True           ; "gendat" does not generate cyclic fields
   guess =  1               ; use zonal means
   relc  = 0.6              ; standard relaxation coef
   opt   = 0
   poisson_grid_fill( betastar, gtype, guess, nscan, eps, relc, opt)
;;;   search for the zero line extend 
     beta2 = betastar(0, kk1,  {lat1:lat2}, {lon1:lon2})
     dsizes_beta2 = dimsizes( beta2)
      xdim2 = dsizes_beta2(1) 
      ydim2 = dsizes_beta2(0)
      beta2!0 = "lat"
      beta2!1 = "lon"
        lon22 = lon( {lon1:lon2})
        lat22 = lat( {lat1:lat2}) 
      beta2@lat = lat22 ;;   lat( {lat1:lat2}) 
      beta2@lon = lon22 ;;   lon( {lon1:lon2}) 

     beta22 =  beta2

     do j = 0, ydim2 - 1
     do i = 0, xdim2 - 1
      if( lon22(i) .gt. 180.) 
         beta22(j,i)=  beta22@_FillValue
      end if 
     end do 
     end do 

     beta1D      = ndtooned( beta22)      

     bmask = new( dimsizes( beta2), "float") 
     bmask = 0.

     indices  = ind_resolve( minind(beta1D), dsizes_beta2) 

     ii = indices(0,1)
     jj = indices(0,0)

     min_beta2 = min( beta22)
   
;; calculate if the minimum is below 0.
      xx = undef2
      ijdims = dimsizes( beta1D)
;;      print( ijdims + " " )
     
      iindex = new( (/ ijdims /), "integer")
      jindex = new( (/ ijdims /), "integer")
      iindex = 0
      jindex = 0

      kk2 = 0 
      iindex( kk2) = ii
      jindex( kk2) = jj
       bmask(jj , ii) = 1.
;;      print( kk2 + " " + iindex( kk2)  + " " + jindex( kk2)  )

     if( min_beta2 .le. zero_limit)  ;; then calculate the 

	xx_lon = -9999.

      do n = 0, ijdims - 1	 
      
       k1 = kk2 
      do k = 0, kk2
        
        ii =  iindex( k)
        i1 = ii - 1
	 if ( i1 .lt. 0) 
	 i1 = 0 
        end if 
        i2 = ii + 1
        if ( i2 .ge. xdim2) 
        i2 =  xdim2 - 1
        end if 
        jj = jindex( k) 
        j1 = jj - 1
        if ( j1 .lt. 0)
        j1 = 0
        end if
        j2 = jj + 1
        if ( j2 .ge. ydim2)
        j2 =  ydim2 - 1
        end if
         do j = j1, j2
         do i = i1, i2
          if( (beta2(j,i) .le. zero_limit) .and. (beta2(jj,ii) .le. zero_limit) .and. \
	       (bmask(j,i) .lt. 0.5)  ) 
            k1 = k1 + 1
            iindex( k1) = i
            jindex( k1) = j 
            bmask(j,i) = 1.
	        if( lon22( i) .gt. xx_lon) 
	          xx_lon = tofloat(lon22( i))
               end if  
           end if 
          end do 
          end do 
      end do  ;; over all collected indexes 
       kk2 = k1 
     end do 
     xx = xx_lon - 180.
    end if  ;;  if minimum below zero_limit
   
;; quick plot 
;;;   YY PNA index 
    namein2 = datadir2 + "PNA.txt"
    yy2  =  asciiread(namein2, -1,"float")
    ydims = dimsizes( yy2)
    yy = yy2(0)

;;   custom markers
   maintitle = " NCAR "
   season = "DJF"
   mode = "El Nino"

    namein1 = prefix1 +  "/" + "scatter_data_CASE_08.txt"
    namein3 = prefix1 + "/" + "scatter_data_OBS.txt"
    list1 = prefix + "/" + "list-all.txt"
    list3 = prefix + "/" + "list-OBS.txt"

   namein11 = prefix1 +  "/" + "beta_ext_CASE_08.txt"
   namein33 = prefix1 +  "/" + "beta_ext_REANAL.txt"

;;;----------------------------------------------------------------------
;----------------------------------------------------------------------
;;  read in the data based on the region .. 
;;  columns -   rows = xdim, columns - ydim 
;;   xdim is the number of lines = models 
;;     ydim is the number of columns = variables   - reads in 3 files:
   xdim1 = 18
   ydim1 = 2
   datain1 = asciiread(namein1,(/xdim1/),"float") 
   model1 =   readAsciiTable ( list1, 1, "string", 0)
 
   xdim3 = 5
   ydim3 = 2
   datain3 = asciiread(namein3,(/xdim3/),"float")
   model3 =  readAsciiTable ( list3, 1, "string", 0)
    datain1@_FillValue = undef2
    datain3@_FillValue = undef2
;;; added the betastat longitude extension
   xdim1 = 18
   datain11 = asciiread(namein11,(/xdim1/),"float")

   xdim3 = 5
   datain33 = asciiread(namein33,(/xdim3/),"float")

   datain11@_FillValue = undef2
   datain33@_FillValue = undef2


;;  the order of datain is the order of variables  SST first , RR second
;;  loop over integrals  
;;; also combine dataX and dataY
    xdim = xdim1 +  xdim3
    ydim = ydim1
    datain  = new ( (/xdim, ydim/), typeof(datain1)  )
    ix1 = 0
    ix2 = xdim1 -1
    datain(ix1:ix2, 0) = datain1(0:xdim1-1)
    datain(ix1:ix2, 1) = datain11(0:xdim1-1)

    ix1 = ix2 + 1 ;  
    ix2 = ix1 + xdim3 -1
    datain(ix1:ix2,  0) = datain3(0:xdim3-1)
    datain(ix1:ix2,  1) = datain33(0:xdim3-1)

;;;;;;;;;;;;;;;;;;;;;;;   
   iyy = iy
   ixx = ix

   dataX1 = ff1 * datain11(:)
   dataY1 = ff2 * datain1(:)

   dataX3 = ff1 * datain33(:)
   dataY3 = ff2 * datain3(:)
 
   dataX = ff1 * datain(:, ixx)
   dataY = ff2 * datain(:, iyy)

;----------------------------------------------------------------------
; Open a PNG file and define the color table
;----------------------------------------------------------------------
;;;  markers first

  colors1 =    (/   3,  2,  3,  2,  4, \
                    3,  4,  2,  2,  2, \
                    4,  2,  2,  3,  4,   \
                    3,      2,  4,  1,  1,   \
                    14, 1,  1,  1,  1 /)

   markers1 =     (/  16,   1,   1,   2,  5,  \
                      6,   7,   7 ,  8,  9,  \
                     10,   13, 14,  11, 14,  \
                     15,       15,  15,   0,  1,  \
                      4,    2,  9,   8,  7  /)


    markersizes1 = (/ 0.02,  0.02,  0.02,  0.02,  0.02, \
                     0.02,  0.02,  0.02,  0.02,  0.02, \
                     0.02,  0.02,  0.02,  0.03,  0.02, \
                     0.02,         0.023,  0.023,  0.02,  0.02, \
                     0.03,  0.02,  0.02,  0.02, 0.02 /)

   markerthick1 =  (/   3.,  3.,  3.,   3.,  3., \
                        3.,  3.,  3.,   3.,  3., \
                        3.,  3.,  3.,   3.,  3., \
                        3.,       10.,  10.,   3.,  3., \
                       10.,  3.,  3.,   3.,  3 /)
;;;;  
   markers3 = (/  4,  5, 6, 7, 8 /)
   colors3 = (/ "black",  "black", "black",  "black", "black" /) ;;
   markersizes3 = (/ 0.015, 0.015, 0.015, 0.015, 0.015 /)
   markerthick3 = (/ 5, 5, 5, 5, 5 /)

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

;----------------------------------------------------------------------
;----------------------------------------------------------------------
; Draw time stamp first, then the plot.
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

   res1@xyMonoDashPattern = True                 ; make all curves solid
   res1@xyLineThicknessF  = 1.0
   res1@gsnXRefLineDashPatterns  = 1
   res1@gsnXRefLineColors = "black"  ;;   
   res1@gsnXRefLine       = (/ 0., 10./)

   res1@tmYLFormat = "0@;*.2f" ;; 

  res1@gsnDraw            = False       ; Don't draw plot
  res1@gsnFrame           = False       ; Don't advance frame
;;;
  res1@vpXF              = 0.14 ;; 
  res1@vpYF              = 0.82
  res1@vpWidthF          = 0.55 ;; 
  res1@vpHeightF         = 0.55

;---Title resources
  res1@tiMainString       = maintitle + " " + mode + " " + season
  res1@tiXAxisString      =  xlabel
  res1@tiYAxisString      =  ylabel 
  res1@tiMainFontHeightF  =  0.02
  res1@tiXAxisFontHeightF = 0.015
  res1@tiYAxisFontHeightF = 0.015

  res1@tmLabelAutoStride = True
;--XY marker resources

  res1@xyMarkLineMode      = "Markers"
  res1@xyMonoMarkerColor   = False ;;;; Allow different colors for markers
  res1@xyMarkerSizes       = markersizes1(:)
  res1@xyMarkerColors      = colors1(:)
  res1@xyMarkerThicknesses = markerthick1(:)

  res1@xyMarkers           =  markers1(:)
  plot1 = gsn_csm_xy (wks,transpose((/dataX1,dataX1/)), \
                         transpose((/dataY1,dataY1/)),res1)
  delete( res1@xyMarkerColors )
  delete( res1@xyMarkers )
  delete( res1@xyMarkerSizes)
  delete( res1@xyMarkerThicknesses)

  res1@xyMarkerSizes       = markersizes3(:)
  res1@xyMarkerThicknesses = markerthick3(:)
  res1@xyMarkerColors    = colors3(:)
  res1@xyMarkers         = markers3(:)
  plot3 = gsn_csm_xy (wks,transpose((/dataX3,dataX3/)), \
                         transpose((/dataY3,dataY3/)),res1)
    
;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; added legend 
      txres2 = True
      txres2@txFuncCode       = ":"
      txres2@txFontColor =  "black"
      txres2@txFont   = "times-roman" ;;; 
      txres2@txFontHeightF =  0.013  ;;;
      txres2@txJust        = "CenterLeft"

     xs1 = 0.1  ;;
     ys1 = 0.14  ;; 
     dy2 = -0.022
    
   draw( plot1)
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
   xpos1 = 0.75 ;;
   xpos2 = xpos1 + 0.03
   ypos1 = 0.85

   dyy3 =  0.026
   ypos2 = ypos1
;;   loop over model1 
     txres@txFont   = "times-roman" ;;;
   txres@txFontHeightF =  0.013
   do i = 0, xdim1-1
      ypos2 = ypos2 - dyy3
      txres@txFontThicknessF = 1.
      txres@txFontColor =  colors1(i)
      txres@txFont   =  "times-roman" ;;;
      mkres@gsMarkerColor =  colors1(i)
      mkres@gsMarkerThicknessF = 3.5
      mkres@gsMarkerSizeF      = 0.015 ;;
      mkres@gsMarkerIndex      = markers1(i)
      if( (i .eq. (xdim1 -2)) .or. (i .eq. (xdim1 -1)) )
        txres@txFontHeightF = 0.015
        mkres@gsMarkerThicknessF =  10
        mkres@gsMarkerSizeF      =  0.017
      end if

      gsn_polymarker_ndc(wks,  xpos1, ypos2, mkres)
     gsn_text_ndc      (wks, labels1(i,0), xpos2, ypos2, txres)
  end do

   delete( txres@txFontColor)
   delete( mkres@gsMarkerColor)
   delete( mkres@gsMarkerIndex)

;;;;;;;; observations are the last 
    labels3  = model3
    ypos2 = ypos2  - dyy3
    do i =  0, xdim3-1
      ypos2 = ypos2 - dyy3
      txres@txFontThicknessF = 1.
      txres@txFontColor =  colors3(i)
      txres@txFont   =  "times-roman"
      mkres@gsMarkerColor =  colors3(i)
      mkres@gsMarkerThicknessF = 3.5
      mkres@gsMarkerSizeF      = 0.015 ;;
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
;----------------------------------------------------------------------
;;;;;;;;;;;;;;;;;;;;;
   correlation  =  sprintf("%9.3f", rc@bstd(1))
   regression   =  sprintf("%9.3f", rc@b(1))
;;  print the correlation and regression values
      txres2 = True
      txres2@txFontColor =  "red"
      txres2@txFont   = "times-roman" ;;; "helvetica"
      txres2@txFontHeightF =  0.013  ;;;0.016
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
