;;;;  to read grads  file  and get the climatology and anomaly divergent wind
;;;;    and the vorticity   ERA-INTERIM only 
;;;     

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

begin

  modes = (/ "ELNINO", "LANINA" /)
  title_mode = (/ "El Nino",  "La Nina" /)

  varcode = getenv("POD_HOME")
  dirname1  =   getenv("ENSO_RWS_WKDIR")
  obsname  =   getenv("OBS_DATA") + "/DATA/"
 
  model2 = getenv( "CASENAME")
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
     parameter_name = varcode + "/shared/parameters.txt"
;;;   global map
      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2
      ylat1 = -90.
      ylat2 =  90.
     data  = asciiread(parameter_name,-1,"string")
     season = str_get_field(data(7), 3," ")

    outname =  "RR_adiv_aUVdiv"
    variname = "Anomaly RR and Divergent Wind"

;;  variables 
   variable1 = "ua"
   variable2 = "va" 
   variable3 = "pr" 
   ff = 24.*60.*60.  ;; conversion to mm/day 
;; levels to plot 
   plevel1 = (/  200.  /)
   nlevels1 = dimsizes( plevel1) 

    tt0 = 0
    kk0 = 0
    kk = 0

    omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.

    ff4 = 1.E+06   ;;  adiv
    unit =  (/ "[mm/day]",  "[x10~S~-06~N~s~S~-1~N~]",  "[m s~S~-1~N~]"/) 

    title2 = (/ "Colors rainfall",  "contours anomaly divergence ",   \
             "vectors anomaly divergent wind" /) 

;;;;  legends 
     xs10 = 0.08
     ys10 = 0.84
     dx2 = 0.65

     xs110 = 0.05 ;;  
     ys110 = 0.15 ;;  
     dxs1 = 0. ;;  
     dys1 = -0.03

;;  need to set for each pressure level   here now only top is relevant 

   levels1 = (/  -8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8 /)

;;;  anomaly divergence 
   levels4 =   (/1, 2, 3, 4, 5 /) 
   cmin4 = -4 ;; 
   cmax4 =  4 ;; 
   cint4 =  1.

;;  hatching :
    levels44 = (/ -3., -2., -1. /)
    patterns = (/ 16, 16, 6, -1  /) 
    scales   =  (/ 0.6, 0.7, 0.8, 1 /)  ;;; 

;;; vector parameters 
    divmag = 2.
    veclength =  0.025 ;;;   
    vmin = 0.4  ;;  min vector to plot
    thinvector = 0.02 ;;  
    vthick = 4 ;; 
    vcolor =  "black" ;; 
    ahead =  0.005

;; loop over El Nino/La Nina  and MODEL/OBS

   do icase = 1, 2
   if( icase .eq. 1) ;;  model
     dirname  =  dirname1 + "/model"
     outdir   =  dirname1 + "/model"
     model =  model2   ;;
    end if

  if( icase .eq. 2) ;;; OBS
     dirname = obsname
     outdir  = dirname1  + "/obs"
     model = " "
    end if

     wks_type = "eps" ;; 
;;;  clima  winds  first 
    namein1 =  dirname +  "/netCDF/"  + variable1 + ".nc"
    namein2 =  dirname +  "/netCDF/"  + variable2 + ".nc"
    namein3 =  dirname +  "/netCDF/"  + variable3 + ".nc"

    f1 = addfile( namein1, "r")
    uuc = f1->$variable1$
    f2 = addfile( namein2, "r")
    vvc = f2->$variable2$
    f3 = addfile( namein3, "r")
    rrc = f3->$variable3$
  
    plev1 = f1->lev
    lon = f1->lon
    lat = f1->lat
    time = f1->time
    xdim1 = dimsizes( lon)
    ydim1 = dimsizes( lat)
    zdim1 = dimsizes( plev1)
    tdim1 = dimsizes( time)
 
    delete( [/ f1, f2, f3 /])
;;;   anomaly seconds  either El Nino/La Nina
    do n = 0, 1
     mode  =  modes(n)
     namein  = dirname  + "/netCDF/"  + mode
     nameout = outdir  + "/PS/"

      namein1 = dirname + "/netCDF/" + mode + "/" + variable1 + ".nc"
      namein2 = dirname + "/netCDF/" + mode + "/" + variable2 + ".nc"
      namein3 = dirname + "/netCDF/" + mode + "/" + variable3 + ".nc"

    f1 = addfile( namein1, "r")
    uu1 = f1->$variable1$
    f2 = addfile( namein2, "r")
    vv1 = f2->$variable2$
    f3 = addfile( namein3, "r")
    rr1 = f3->$variable3$

     mm2 = 1
      wrf_smooth_2d(uu1,mm2)
      wrf_smooth_2d(vv1,mm2)
      wrf_smooth_2d(uuc,mm2)
      wrf_smooth_2d(vvc,mm2)

     delete( [/ f1, f2, f3 /])
;;;  define anomalies    
    ua = uu1
    ua = uu1 - uuc
    va = vv1
    va = vv1 - vvc
    rra = rr1
    rra = ff* ( rr1 - rrc )
   
;;;  fill in ua uuc
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill( ua, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( va, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( uuc, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( vvc, gtype, guess, nscan, eps, relc, opt)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;  divergent wind from divergence    
     adiv = ua
     adiv = uv2dvF_Wrap( ua, va) ;;  
   
    aUVdiv = dv2uvF_Wrap (adiv)
    aUVdiv(0, :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), aUVdiv(0, :, :, :, :), ua@_FillValue)
    aUVdiv(1, :, :, :, :) = where( .not.ismissing(ua(:, :, :, :)), aUVdiv(1, :, :, :, :), ua@_FillValue)

    ua@units = " "
    ua@long_name = " "
    va@units = " "
    va@long_name = " "
    rra@units = " "
    rra@long_name = " "
    adiv@units = " "
    adiv@long_name = " "
    aUVdiv@units = " "
    aUVdiv@long_name = " "

;;;;;;;;;;;;;;;;;;
;;;;;;   PLOTTING 

    kk = 0
    nn = 0
    do k = 0, zdim1 - 1
    if( plevel1(nn) .eq. plev1(k))
    kk = k
    end if
   end do

   pressure =  tostring_with_format( plev1(kk), "%3.0f" )

   nameout2 = nameout + outname + "_" + mode + "_" + pressure ;;  

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
    txres1@txFontHeightF = 0.025
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

;;  RR anomaly  
     res@cnLevelSelectionMode = "ExplicitLevels"
     res@cnLevels    =   levels1 
     cmap = read_colormap_file("precip4_diff_19lev")
     gsn_define_colormap(wks,"precip4_diff_19lev")
     plot1 = gsn_csm_contour_map(wks,  rra(tt0,  :, :), res)
 
   delete(cmap)
   delete( res@cnLevels)
   delete( res@mpMinLatF)
   delete( res@mpMaxLatF)
   delete( res@mpMinLonF)   
   delete( res@mpMaxLonF)   
   delete( res@mpCenterLonF)
;;;;  anomaly divergence  in contours 
   res@cnLevelSelectionMode = "ExplicitLevels" ;;
   res@cnLinesOn           =  True
   res@cnFillOn            = False 
   res@cnLevels    =   levels4    ;;;
;;;   contour lines 
    res@cnLineThicknessF =  1 ;;  
    res@cnLineLabelInterval       =   1       
    res@cnLineLabelPlacementMode   = "Computed" 
    res@cnLineLabelFontHeightF = 0.008 ;; 
    res@cnLineLabelFontThicknessF  = 1.
    res@cnInfoLabelOn = False
    res@cnLineLabelsOn   =  True ;;;   
    res@gsnContourNegLineDashPattern  =  7 
    res@cnLineLabelFormat    =  "0@;*.2f"
    res@gsnContourZeroLineThicknessF  = 0

     res@cnMonoLineColor = True
     res@cnLineColor = "gray40" ;; 

    adiv = ff4 * adiv 
    plot2 = gsn_csm_contour(wks,  adiv(tt0, kk, :, :), res)

    delete( res@cnLevels )

    res2 =  True

   res2@gsnFrame             = False               ; don't advance frame
   res2@gsnDraw              = False

   res2@gsnMaximize  = True

     res2@lbAutoManage          =  False
     res2@pmLabelBarDisplayMode = "ForceAlways" ;;
     res2@lbOrientation         = "Vertical";;  
     res2@pmLabelBarSide        = "Right";;  
     res2@lbLabelStride         = 1                ; skip every other label
     res2@pmLabelBarWidthF      = 0.               ; default is shorter
     res2@pmLabelBarHeightF     = 0.               ; default is taller
     res2@lbLabelFontHeightF    = 0.0000001        ; default is HUGE
     res2@lbPerimOn             = False
     res2@pmLabelBarOrthogonalPosF = 1 ;; 

    res2@cnLevelSelectionMode = "ExplicitLevels"
    res2@cnLevels   =   levels44
;;;   contour lines
    res2@cnLineThicknessF =   2 ;; 
    res2@cnLineLabelInterval       =   1   ;;        
    res2@cnLineLabelPlacementMode   = "Computed" ;;; 
    res2@cnLineLabelFontHeightF = 0.008 ;;  
    res2@cnLineLabelFontThicknessF  = 1.
    res2@cnInfoLabelOn = False
    res2@cnLineLabelsOn   =  True ;;;   
    res2@gsnContourNegLineDashPattern  =  7 ;
    res2@cnLineLabelFormat    =  "0@;*.2f"
    res2@gsnContourZeroLineThicknessF  = 0

    res2@cnMonoLineColor = True
    res2@cnLineColor = "black"

   res2@cnLineColor     = "black"
   res2@cnFillOn        = True                 ; fill contour intervals
   res2@cnLinesOn       =  True 
   res2@cnMonoFillColor = True 

   res2@cnMonoFillPattern = False              ; want multiple patterns
   res2@cnMonoFillScale   = False 

   res2@cnFillPatterns  = patterns ;;
   res2@cnFillScales    = scales 
   
    plot22 = gsn_csm_contour(wks, adiv(tt0, kk, :, :), res2)

   delete( res2) 
;;;   anomaly divergent winds 
  res3                  = True
  res3@gsnFrame         = False               ; don't advance frame
  res3@gsnDraw          = False

  res3@gsnMaximize  = True

  res3@vcRefAnnoOn  = True
  res3@vcMinAnnoSide = "Bottom"

  res3@vcMonoLineArrowColor  = True
  res3@vcRefMagnitudeF =  divmag    ;; make vectors larger
  res3@vcRefLengthF    =  veclength ;;  reference vector length
  res3@vcGlyphStyle    = "LineArrow" ;;; turn on curly vectors
  res3@vcMinDistanceF  =  thinvector ;;  thin the vectors
  res3@vcLineArrowThicknessF  = vthick 
  
  res3@vcMinMagnitudeF  = vmin 

  res3@vcLineArrowColor  = vcolor   

  res3@vcLineArrowHeadMinSizeF = ahead
  res3@vcLineArrowHeadMaxSizeF =  ahead   

  plot3 = gsn_csm_vector(wks, aUVdiv(0, tt0, kk, :, :), aUVdiv(1,tt0, kk, :, :), res3)

    overlay( plot1, plot2)
    overlay( plot1, plot22)
    overlay( plot1, plot3)

    draw( plot1)
   frame(wks)
  delete( res3 ) 
  end do  ;;  over ELNINO/LANINA 

 delete ([/lon, lat, plev1, time,  zdim1, uuc, vvc, rrc, uu1, vv1, rr1, rra, ua, va, adiv, aUVdiv/])
 
end do ;;  over  MODEL/OBS

end
