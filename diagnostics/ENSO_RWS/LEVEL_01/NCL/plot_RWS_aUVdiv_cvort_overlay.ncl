;;;;  to read grads  file  and get the climatology and anomaly divergent wind
;;;       overlay RWS 1+2+3+4  200mb divegrent wind anomaly +  absolute vorticity t

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

begin

   modes = (/ "ELNINO", "LANINA" /)
   title_mode = (/ "El Nino",  "La Nina" /)

  varcode = getenv("POD_HOME")
  dirname1  =   getenv("ENSO_RWS_WKDIR")
  obsname  =   getenv("OBS_DATA") + "/DATA/"

  model2 = getenv( "CASENAME")
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; levels to plot 
   plevel1 = (/  200.  /)
   nlevels1 = dimsizes( plevel1) 

     parameter_name = varcode + "/shared/parameters.txt"
;;;   global map
      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2
      ylat1 = -90.
      ylat2 =  90.
     data  = asciiread(parameter_name,-1,"string")
     season = str_get_field(data(7), 3," ")

    outname =  "RWS_aUVdiv_absvort"    
    variname = "RWS terms, Abs. Vort. and Anom Div. Wind"

;;  variables
   variable1 = "ua"
   variable2 = "va"

    tt0 = 0
    kk = 0

    omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.

    ff1 = 1.E+11   ;;  RWS 1+2+3+4
    ff4 = 1E+05    ;; absolute vorticity 
    unit =  (/ "[x10~S~-11~N~s~S~-2~N~]",  "[x10~S~-05~N~s~S~-1~N~]",  "[m s~S~-1~N~]"/) 

    title2 = (/ "Colors RWS terms 1+2+3+4",  "contours absolute vorticity climatology",   \
             "vectors anomaly divergent wind" /) 
     
;;;;  legends
     xs10 = 0.08
     ys10 = 0.84
     dx2 = 0.65

     xs110 = 0.05 ;;  0.82
     ys110 = 0.15 ;;  0.78
     dxs1 = 0. ;;   0.3
     dys1 = -0.03

     colormap = "hotcold_18lev"

;;  levels1  =  RWS terms 
   levels1 = (/ -30,  -27,  -24, -21, -18, -15, -12, -9, -6,  6, 9, 12, 15, 18, 21, 24, 27, 30 /)
    
;;;   absolute corticity
  
   cmin4 = -16 ;; 
   cmax4 =  16 ;; 
   cint4 =   2.

;;; vector parameters     vcLineArrowThicknessF 
    divmag = 2.
    veclength =  0.025 ;;; 
    thinvector = 0.02 ;;  
    vmin = 0.4
    vthick = 4 ;;   
    vcolor = "black"  ;; 
    ahead = 0.005

     wks_type = "eps" ;;

;; loop over El Nino/La Nina  and MODEL/OBS

   do icase = 1, 2
   if( icase .eq. 1) ;;  model
     dirname  =  dirname1 + "/model"
     outdir   =  dirname1 + "/model"
     model =  model2   ;;;   
    end if

   if( icase .eq. 2) ;;; OBS
      dirname = obsname
      outdir  = dirname1  + "/obs"
      model = " "
    end if

;;;  clima  winds  first
    namein1 =  dirname +  "/netCDF/"  + variable1 + ".nc"
    namein2 =  dirname +  "/netCDF/"  + variable2 + ".nc"

    f1 = addfile( namein1, "r")
    uuc = f1->$variable1$
    f2 = addfile( namein2, "r")
    vvc = f2->$variable2$

    plev1 = f1->lev
    lon = f1->lon
    lat = f1->lat
    time = f1->time
    xdim1 = dimsizes( lon)
    ydim1 = dimsizes( lat)
    zdim1 = dimsizes( plev1)
    tdim1 = dimsizes( time)

    delete( [/ f1, f2 /])
   
;;;   anomaly second  either El Nino/La Nina
    do n = 0, 1
     mode  =  modes(n)
     namein  = dirname  + "/netCDF/"  + mode
     nameout = outdir  + "/PS/"

      namein1 = dirname + "/netCDF/" + mode + "/" + variable1 + ".nc"
      namein2 = dirname + "/netCDF/" + mode + "/" + variable2 + ".nc"

    f1 = addfile( namein1, "r")
    uu1 = f1->$variable1$
    f2 = addfile( namein2, "r")
    vv1 = f2->$variable2$

      delete( [/ f1, f2 /])
;;;  define anomalies
    ua = uu1
    ua = uu1 - uuc
    va = vv1
    va = vv1 - vvc
  
    mm2 = 1
    wrf_smooth_2d(uu1,mm2)
    wrf_smooth_2d(vv1,mm2)
    wrf_smooth_2d(uuc,mm2)
    wrf_smooth_2d(vvc,mm2)

   ua@long_name = ""
   ua@units = " "
   va@long_name = ""
   va@units = " "

;;;  fill in ua uuc
  nscan =  500             ; 
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill( ua, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( va, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( uuc, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( vvc, gtype, guess, nscan, eps, relc, opt)

;;;;;;;;;;;;  calculations 

   avort   =  ua
    cvort2  =  uuc
    avort   = uv2vrF_Wrap (ua, va)   ;;
    cvort2  = uv2vrF_Wrap (uuc, vvc) ;;
   
    sinlat = sin( lat * pi/180.)
    fcoriol = 2.* omega * sinlat

    coslat =  cos(lat * pi/180.)
    beta = 2.* omega * coslat/rearth

     cvort = cvort2
     do j = 0, ydim1 - 1
     cvort(:, :, j, :) =  ( tofloat(fcoriol(j))  + cvort2(:, :, j, :) )
     end do

     avortx = uu1
     avorty = uu1
     cvortx = uu1
     cvorty = uu1
     
     gradsf (avort,  avortx, avorty)
     gradsf (cvort,  cvortx, cvorty)

;;  divergent wind from divergence    uv2dvG_Wrap
     adiv = uu1
     cdiv = uuc
     adiv = uv2dvF_Wrap( ua, va) ;;  
     cdiv = uv2dvF_Wrap( uuc, vvc) ;; 

     aUVdiv = dv2uvF_Wrap (adiv)
     cUVdiv = dv2uvF_Wrap (cdiv)

     adiv@units = " "
     adiv@long_name = " " ;; 

     aUVdiv(0, :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), aUVdiv(0, :, :, :, :), ua@_FillValue)
    aUVdiv(1, :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), aUVdiv(1, :, :, :, :), ua@_FillValue)

    cUVdiv(0, :, :, :, :) = where( .not.ismissing(uuc(:, :, :, :)), cUVdiv(0, :, :, :, :), uu1@_FillValue)
    cUVdiv(1, :, :, :, :) = where( .not.ismissing(uuc(:, :, :, :)), cUVdiv(1, :, :, :, :), uu1@_FillValue)

    adiv(  :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), adiv(  :, :, :, :), ua@_FillValue)
    cdiv(  :, :, :, :) = where( .not.ismissing(uuc(:, :, :, :)), cdiv(  :, :, :, :), uuc@_FillValue)

   avortx(:, :, :, :) =  where( .not.ismissing(ua(:, :, :, :)), avortx(:, :, :, :),ua@_FillValue)
   avorty(:, :, :, :) =  where( .not.ismissing(ua(:, :, :, :)), avorty(:, :, :, :),ua@_FillValue)
   cvortx(:, :, :, :) =  where( .not.ismissing(uuc(:, :, :, :)), cvortx(:, :, :, :),ua@_FillValue)
   cvorty(:, :, :, :) =  where( .not.ismissing(uuc(:, :, :, :)), cvorty(:, :, :, :),ua@_FillValue)

   aUVdiv@long_name = ""
   aUVdiv@units = " "
   cUVdiv@long_name = ""
   cUVdiv@units = " "
;;; RWS terms : 
      term1 = uu1
      term1 = -1.*( cvort * adiv)

      term2 = term1
      term2(:, :, :, :) = -1.*( aUVdiv(0, :, :, :, :) * cvortx(:, :, :, :) +  aUVdiv(1, :, :, :, :) * cvorty(:, :, :, :))

      term3 =  term1
      term3 = -1.*( avort * cdiv)

      term4 =  term1
      term4(:, :, :, :) = -1.*( cUVdiv(0, :, :, :, :) * avortx(:, :, :, :) +  cUVdiv(1, :, :, :, :) * avorty(:, :, :, :))

   term1 = ff1 * term1
   term2 = ff1 * term2
   term3 = ff1 * term3
   term4 = ff1 * term4
   termx = term1
   termx =  (term1 + term2 + term3 + term4)
   termx@long_name = " "
   termx@units =  " "
;;;;;;   PLOTTING 

    kk = 0
    nn = 0
    do k = 0, zdim1 - 1
    if( plevel1(nn) .eq. plev1(k))
    kk = k
    end if
   end do

   pressure =  tostring_with_format( plev1(kk), "%3.0f" )

   nameout2 =  nameout + outname + "_" + mode + "_" + pressure ;;

   wks = gsn_open_wks( wks_type, nameout2)
    res              = True
    res@gsnFrame             = False               ; don't advance frame
    res@gsnDraw              = False

    res@tiMainFont  = 21
    res@mpMinLatF   =  ylat1 ;;
    res@mpMaxLatF   =  ylat2 ;;
    res@mpMinLonF   =  xlon1
    res@mpMaxLonF   =  xlon2
    res@mpCenterLonF =  xcenter
    res@mpGeophysicalLineThicknessF = 3

     res@lbAutoManage          = False             ; we control label bar
     res@pmLabelBarDisplayMode = "Always"          ; turns on label bar
     res@lbOrientation         = "Horizontal"      ; ncl default is vertical
     res@pmLabelBarSide        = "Bottom"          ; default is right
     res@lbLabelStride         = 1                 ; skip every other label
     res@pmLabelBarWidthF      =  0.80               ; default is shorter
     res@pmLabelBarHeightF     = 0.1               ; default is taller
     res@lbLabelFontHeightF    = .014              ; default is HUGE
     res@lbPerimOn             = False
     res@pmLabelBarOrthogonalPosF = 0.2


    res@gsnMaximize  = True 
    res@cnFillOn             = True               ; turn on color fill
    res@cnLinesOn           =   False ;; 

     txres1 = True
     txres1@txFontColor =  "black"
     txres1@txFont   = "helvetica"
     txres1@txFontHeightF =  0.022 ;;  
     txres1@txJust        = "CenterLeft"
     txres1@txFuncCode    = "~"

      xs1 = xs10
      ys1 = ys10
      label2 = variname
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 = title_mode(n) + "  (" + season + ")"
      xs1 = xs1 + dx2
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      txres2 = True
      txres2@txFontColor =  "black"
      txres2@txFont   = "helvetica"
      txres2@txFontHeightF = 0.02 ;; 
      txres2@txJust        = "CenterLeft"
      txres2@txFuncCode    = "~"

;;     add units
      xs11 = xs110
      ys11 = ys110
      i = 0
      gsn_text_ndc (wks, title2(i) + " " + unit(i), xs11, ys11, txres2)
      xs11 = xs11 + dxs1
      ys11 = ys11 + dys1
      i = i + 1
      gsn_text_ndc (wks, title2(i) + " " + unit(i), xs11, ys11, txres2)
      xs11 = xs11 + dxs1
      ys11 = ys11 + dys1
      i = i + 1
      gsn_text_ndc (wks, title2(i) + " " + unit(i), xs11, ys11, txres2)
      xs11 = xs11 + dxs1
      ys11 = ys11 + dys1
      i = i + 1
      if( icase .eq. 1)
      gsn_text_ndc (wks, "Model: " + model2, xs11, ys11, txres2)
      end if


;;  RWS 1+2+3+4    i = 1    
    res@cnLevelSelectionMode = "ExplicitLevels"
     res@cnLevels    =   levels1 
     cmap = read_colormap_file( colormap )
     res@cnFillPalette = cmap
    
     plot1 = gsn_csm_contour_map(wks,  termx(tt0, kk, :, :), res)
  
   delete(cmap)
   delete( res@cnLevels)
   delete( res@mpMinLatF)
   delete( res@mpMaxLatF)
   delete( res@mpMinLonF)   
   delete( res@mpMaxLonF)   
   delete( res@mpCenterLonF)
   delete( res@lbAutoManage)
   delete( res@lbPerimOn)
   delete( res@lbLabelFontHeightF)
   delete( res@lbLabelStride)
   delete( res@mpGeophysicalLineThicknessF)
;;;;  absolute vorticity  in contours 
   i = 2
   res@cnLevelSelectionMode = "ManualLevels" ;;; 
   res@cnLinesOn           =  True
   res@cnFillOn            =  False 
   res@cnMinLevelValF      =  cmin4
   res@cnMaxLevelValF      =  cmax4
   res@cnLevelSpacingF     =   cint4
   res@pmLabelBarDisplayMode = "NoCreate"

    res@cnLineThicknessF =  1 ;;  
    res@cnLineLabelInterval       =  2 ;;
    res@cnLineLabelPlacementMode   = "constant"
    res@cnLineLabelFontHeightF = 0.009 ;; 
    res@cnLineLabelFontThicknessF  = 1.
    res@cnInfoLabelOn = False
    res@cnLineLabelsOn   =  True ;;;   
    res@gsnContourNegLineDashPattern  = 7
    res@gsnContourZeroLineThicknessF  = 5 ;; 

    cvort@units = " "
    cvort@long_name = " "
    cvort = ff4 *  cvort
    plot2 = gsn_csm_contour(wks,   cvort(tt0, kk,:,:),res)
    
;;;   anomaly divergent winds 
   i = 3
  res3                 = True
  res3@gsnFrame             = False               ; don't advance frame
  res3@gsnDraw              = False

  res3@gsnMaximize  = True

  res3@vcMonoLineArrowColor  = True
  res3@vcRefMagnitudeF =  divmag    ;;  make vectors larger
  res3@vcRefLengthF    =  veclength ;;  reference vector length
  res3@vcGlyphStyle    =  "LineArrow" ;; turn on curly vectors
  res3@vcMinDistanceF  =  thinvector ;;; thin the vectors
  res3@vcLineArrowThicknessF  = vthick   
  res3@vcLineArrowColor  = vcolor
  res3@vcRefAnnoArrowLineColor  = "black"

  res3@vcMinMagnitudeF  = vmin

  res3@vcLineArrowHeadMinSizeF = ahead
  res3@vcLineArrowHeadMaxSizeF =  ahead

  res3@vcRefAnnoArrowUseVecColor = False   

  plot3 = gsn_csm_vector(wks, aUVdiv(0, tt0, kk, :, :), aUVdiv(1, tt0, kk,:,:), res3)

    overlay( plot1, plot3)
    overlay( plot1, plot2)

    draw( plot1)
   frame(wks)

   delete( res3 )
  end do  ;;  over ELNINO/LANINA

  delete( res) 
 
   delete( [/  lon, lat, plev1, time,  ydim1, zdim1, ua, va, uu1, vv1, uuc, vvc /])

   delete( [/ cUVdiv, aUVdiv,  adiv, cdiv, avortx, avorty, cvortx,  cvorty, sinlat, fcoriol, coslat, beta, cvort2, cvort, avort /])
 delete( [/ term1, term2, term3, term4, termx /])


  end do ;;  over  MODEL/OBS

end
