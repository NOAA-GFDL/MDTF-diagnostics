;;   plot the ElNino/LaNina composite anomalies 
;; 

begin
   
      varcode = getenv("POD_HOME")
     dirname1  =  getenv("ENSO_RWS_WKDIR")
     obsname  =  getenv("OBS_DATA") + "/DATA/"

   modes = (/ "ELNINO", "LANINA" /)

   variable1 =  "ua"
   variable2 =  "va"
 
   variname = "Divergent Wind" 

   outname = "divergent_wind"

   plevel2 = (/ 200,  500  /)
   nlevels2 = dimsizes( plevel2)
   
;;  vector parameters 
    divmag =  (/ 2., 1. /)
     veclength =  0.05  ;;
     thinvector = 0.02 ;;

     thick_vector =  3. ;;

     height_ref = 3
     thick_ref = 5
    
   varunit = (/ "[m s~S~-1~N~]" /)

;;   contour levels  one for each p-level

   title_mode = (/ "El Nino",  "La Nina" /)

    varcode = getenv("POD_HOME")

      parameter_name = varcode + "/shared/parameters.txt"
;;;   global map 
      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2
      ylat1 = -90.
      ylat2 = 90.
       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(7), 3," ")
;;;  legend 
     xs1 = 0.08
     ys1 = 0.84
     dy2 = 0.0
     dx2 = 0.65

     xs4 = 0.08
     ys4 = 0.14

     colormap ="hotcold_18lev"

  do icase = 1, 2 

   if( icase .eq. 1) ;;  model
   dirname  =  dirname1 + "/model"
   outdir   =  dirname1 + "/model"
   model =  getenv( "CASENAME")
   end if

  if( icase .eq. 2) ;;; OBS
   dirname = obsname
   outdir  = dirname1  + "/obs"
    model = " " 
    end if    

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
    zdim = dimsizes( plev1) 

    delete( f1)
    delete( f2)


    do n = 0, 1
        mode  =  modes(n)
        namein  = dirname  + "/netCDF/"  + mode
        nameout = outdir  + "/PS/"
 
      namein1 = dirname + "/netCDF/" + mode + "/" + variable1 + ".nc" 
      namein2 = dirname + "/netCDF/" + mode + "/" + variable2 + ".nc"
;;    read in the variables 
      f1 = addfile( namein1, "r") 
      uu1 = f1->$variable1$
      f2 = addfile( namein2, "r")
      vv1 = f2->$variable2$

      delete( f1) 
      delete( f2) 
;;; anomalies 
    ua = uu1
    ua = uu1 - uuc
    va = vv1
    va = vv1 - vvc

     mm2 = 1
      wrf_smooth_2d(ua,mm2)
      wrf_smooth_2d(va,mm2)
      wrf_smooth_2d(uuc,mm2)
      wrf_smooth_2d(vvc,mm2)

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


;;  divergence 
    adiv = uu1
    adiv =  uv2dvF_Wrap( ua, va) ;; uv2dv_cfd (ua,va, lat, lon, 3)  
 
;;  fill undefined 
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill( adiv, gtype, guess, nscan, eps, relc, opt)
    
    aUVdiv = dv2uvF_Wrap (adiv) 
    aUVdiv(0, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), aUVdiv(0, :, :, :, :), uu1@_FillValue)
    aUVdiv(1, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), aUVdiv(1, :, :, :, :), uu1@_FillValue)

    aUVdiv@units = " "
    aUVdiv@long_name = " "

;;;  loop over levels  select the index kk corresponding to plev(nlev) 

    do nlev = 0, nlevels2 - 1
    kk = -9 
   do k = 0, zdim - 1
    if( plev1(k) .eq. plevel2(nlev)) 
    kk = k
    end if
   end do

   if( kk .gt. -1) 
   pressure =  tostring_with_format( plev1(kk), "%3.0f" )

   nameout2 =  nameout + outname + "_" + mode + "_" + pressure 

   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout2)
   gsn_define_colormap(wks,  colormap)
      
 res = True

  res@mpMinLonF              =  xlon1
  res@mpMaxLonF              =  xlon2
  res@mpCenterLonF           = xcenter     ; This is necessary to get the correct map
  res@mpMinLatF   =  ylat1 ;; 
  res@mpMaxLatF   =  ylat2 ;;

 res@gsnMaximize         = True
 res@mpGeophysicalLineThicknessF = 2

   txres1 = True
   txres1@txFontColor =  "black"
   txres1@txFont   = "helvetica"
   txres1@txFontHeightF = 0.025
   txres1@txJust        = "CenterLeft"
   txres1@txFuncCode    = "~"

      label2 = variname  + " level " +  pressure + " mb"
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 = title_mode(n) + "  (" + season + ")"
      xs11 = xs1 + dx2
      gsn_text_ndc (wks, label2, xs11, ys1, txres1)

      txres2 = True
      txres2@txFontColor =  "black"
      txres2@txFont   = "helvetica"
      txres2@txFontHeightF = 0.02 ;;  0.016
      txres2@txJust        = "CenterLeft"
      txres2@txFuncCode    = "~"

     label4 = "  Months/Season= " + season + " Model: " + model + "  units:" +  varunit
     if( icase .eq. 2) 
     label4 = "  Months/Season= " + season + "                       units:" +  varunit
     end if 
     gsn_text_ndc (wks, label4, xs4, ys4, txres2)
  
   res@vcRefMagnitudeF =  divmag(nlev)  ;;             ; make vectors larger
   res@vcRefLengthF    =  veclength ;; 0.050                 ; reference vector length
   res@vcGlyphStyle    = "CurlyVector"         ; turn on curly vectors
   res@vcMinDistanceF  =  thinvector ;;  0.012                 ; thin the vectors
   res@vcLineArrowThicknessF  = thick_vector
   res@vcLabelFontHeightF =  height_ref  
   res@vcRefAnnoFontThicknessF  = thick_ref
  
   plot= gsn_csm_vector_map(wks, aUVdiv(0, 0, kk, :, :), aUVdiv(1, 0, kk,:,:), res)

   end if 
   end do  ;;; over pressure levels 

  end do  ; elnino/lanina

  delete ([/lon, lat, plev1, time,  zdim, uuc, vvc, uu1, vv1, ua, va, adiv,  aUVdiv/])

  end do ;; model + OBS
end
