;;;;  to read grads  file  and get the climatology and anomaly divergent wind
;;;;    and the vorticity   ERA-INTERIM only 
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

    outname =  "RWS_betastar"
    variname = "RWS terms and Beta* "

;;  variables
   variable1 = "ua"
   variable2 = "va"

    tt0 = 0
    kk = 0

    omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.

    ff1 = 1.E+11   ;;  RWS 1+2+3+4
    
    unit =  (/ "[x10~S~-11~N~m~S~-1~N~s~S~-1~N~]",  "[x10~S~-11~N~s~S~-2~N~]"/) 

    title2 = (/ "Shading RWS terms 1+2+3+4",  "colors beta star " /)
 
;;;;  legends
     xs10 = 0.08
     ys10 = 0.84
     dx2 = 0.65

     xs110 = 0.05 ;;  
     ys110 = 0.19 ;;
     dxs1 = 0. ;; 
     dys1 = -0.03

     colormap = "precip2_17lev"
;;  need to set for each pressure level   here now only top is relevant 

;;  levels1  =  RWS terms 
    levels1 = (/  -6, 6 /)
    patterns =  (/ 2, -1, 16 /)  ; 
    scales = (/ 1, 1, 1 /) ;;;  

;;;     betastar
   levels4 = (/ -1.,  0., 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13, 14, 15, 16 /)

    wks_type = "eps" ;; 
;;;  time dimensions for seasonal averaging 

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

    sinlat = sin( tofloat(lat) * pi/180.)
    fcoriol = 2.* omega * sinlat

    coslat =  cos( tofloat(lat) * pi/180.)
    beta = 2.* omega * coslat/rearth

     cvort = cvort2
     do j = 0, ydim1 - 1
     cvort(:, :, j, :) =  ( fcoriol(j)  + cvort2(:, :, j, :) )
     end do

;;;  get the gradient of avort,  and cvort - avortgr  cvortgr
     avortx = uu1
     avorty = uu1
     cvortx = uu1
     cvorty = uu1
    
     gradsf (avort,  avortx, avorty)
     gradsf (cvort,  cvortx, cvorty)

;;  divergent wind from divergence 
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

;;  add betastar =  beta +  d2uclima/dy2
      betastar = uuc
      Uc2 = uuc

      do j = 1, ydim1-2                      ; loop over each latitude
      dlat = 0.5 * tofloat((lat(j+1)-lat(j-1)) )
      dY = rearth * dlat * pi/180.  ; constant at this latitude
      Uc2(:, :, j, :) = (uuc(:,:,j+1,:) - 2.*uuc(:,:,j,:) + uuc(:,:,j-1,:))/(dY*dY)
      betastar(:,:, j, :) =  ( beta(j)  -  Uc2(:, :, j, :) )
      end do

   betastar = ff1 * betastar
   betastar@long_name = " " ;;  "Beta star"
   betastar@units =" " ;; 

;;; RWS terms : 1
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
      txres2@txFontHeightF = 0.018 ;;
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
      if( icase .eq. 1)
      gsn_text_ndc (wks, "Model: " + model2, xs11, ys11, txres2)
      end if
;;   betastar 
    res@cnLevelSelectionMode = "ExplicitLevels" ;;;
    res@cnLevels    =   levels4
    cmap = read_colormap_file( colormap) 

     i = 0
    cmap( i, 0) = 150./255.
    cmap (i,1) = 150./255.
    cmap (i,2) = 150./255.
    cmap (i,3) = 1
    i = 1
    cmap( i, 0) = 200./255.
    cmap (i,1) = 200./255.
    cmap (i,2) = 200./255.
    cmap (i,3) = 1

    res@cnFillPalette = cmap ( (/  0, 1,  2,  3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17 /), :)
    

     res@lbAutoManage          = False             ; we control label bar
     res@pmLabelBarDisplayMode = "Always"          ; turns on label bar
     res@lbOrientation         = "Horizontal"      ; ncl default is vertical
     res@pmLabelBarSide        = "Bottom"          ; default is right
     res@lbLabelStride         = 1                 ; skip every other label
     res@pmLabelBarWidthF      = 0.8               ; default is shorter
     res@pmLabelBarHeightF     = 0.1               ; default is taller
     res@lbLabelFontHeightF    = .014              ; default is HUGE
     res@lbPerimOn             = False
     res@pmLabelBarOrthogonalPosF = 0.15

    plot1 = gsn_csm_contour_map(wks,  betastar(tt0, kk, :,:), res)
   
   delete( res@mpMinLatF)
   delete( res@mpMaxLatF)
   delete( res@mpMinLonF)
   delete( res@mpMaxLonF)
   delete( res@mpCenterLonF)

;;  RWS 1+2+3+4    i = 1    
    res2                  = True
    res2@gsnFrame         = False               ; don't advance frame
    res2@gsnDraw          = False
    res2@gsnMaximize  = True

    res2@cnLevelSelectionMode = "ExplicitLevels"
    res2@cnLevels    =   levels1 
     
   res2@cnInfoLabelOn   = False                ; turn off info label box
   res2@cnLineLabelsOn  = False                ; no lables on line
   res2@cnFillOn        = True                 ; fill contour intervals
   res2@cnLinesOn        =  True ;; 

   res2@cnMonoFillColor = True                 ; default color is fground [black]
   res2@cnMonoFillPattern = False              ; want multiple patterns 
   res2@cnMonoFillScale   = False              ; want patterns w/ diff densities

   res2@cnFillPatterns    = patterns ;; 
   res2@cnFillScales  = scales  ;;; 

    res2@lbAutoManage          =  False 
    res2@pmLabelBarDisplayMode =  "Never" ;;      ; turns on label bar
    res2@lbOrientation         = "Horizontal"      ; ncl default is vertical
    res2@pmLabelBarSide        = "Bottom"          ; default is right
    res2@lbLabelStride         = 1                 ; skip every other label
    res2@pmLabelBarWidthF      = 0.17               ; default is shorter
    res2@pmLabelBarHeightF     = 0.1               ; default is taller
    res2@lbLabelFontHeightF    = 0.01              ; default is HUGE
    res2@lbPerimOn             = False

     plot2 = gsn_csm_contour(wks,  termx(tt0, kk, :, :), res2)


     overlay( plot1, plot2)

    draw( plot1)
   frame(wks)

    delete( res2 )

 end do  ;;  over ELNINO/LANINA

  delete( res)

  delete( [/  lon, lat, plev1, time,  ydim1, zdim1, ua, va, uu1, vv1, uuc, vvc, Uc2, dlat /])

  delete( [/ cUVdiv, aUVdiv,  adiv, cdiv, avortx, avorty, cvortx,  cvorty, sinlat, fcoriol, coslat, beta, betastar, cvort2, cvort, avort /])
  delete( [/ term1, term2, term3, term4, termx /])


  end do ;;  over  MODEL/OBS

end
