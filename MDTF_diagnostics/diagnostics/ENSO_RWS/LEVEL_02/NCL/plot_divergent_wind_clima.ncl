;;   plot the ElNino/LaNina composite anomalies 
;; 


begin

   mode =  "CLIMA"

   variable1 =  "ua"
   variable2 =  "va"
 
   variname = "Divergent Wind" 

   outname = "divergent_wind"

   plevel2 = (/ 200,  500  /)
   nlevels2 = dimsizes( plevel2)
   
;;  vector parameters 
     divmag = (/ 5, 2 /) ;;;   (/ 2., 1. /)
     veclength =  0.05  ;; 0.1 ;; 0.05
     thinvector = 0.02 ;; 0.12

     thick_vector =  3. ;; 2.

     height_ref = 3
     thick_ref = 5
    
   varunit = (/ "[m s~S~-1~N~]" /)

;;   contour levels  one for each p-level

   title_mode = "Climatology"

     varcode  = getenv("POD_HOME")
     dirname1 = getenv("ENSO_RWS_WKDIR")
     obsname  = getenv("OBS_DATA") + "/DATA/"

      parameter_name = varcode + "/shared/parameters.txt"
;;;   global map 
      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(7), 3," ")
;;;  legend 
     xs1 = 0.08
     ys1 = 0.84
     dy2 = 0.0
     dx2 = 0.6

     xs4 = 0.08
     ys4 = 0.14

     colormap ="hotcold_18lev"

   do icase = 1, 2

   if( icase .eq. 1) ;;  model
   dirname  =  dirname1 + "/model"
   outdir   =  dirname1 + "/model"
     model = getenv( "CASENAME") ;;  "CESM2" ;;  getenv( "CASENAME")
    end if

  if( icase .eq. 2) ;;; OBS
   dirname = obsname
   outdir  = dirname1  + "/obs"
      model = " " ;;   OBS = blank 
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


    nameout = outdir  + "/PS/"
;;   fill in missing 
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill( uuc, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( vvc, gtype, guess, nscan, eps, relc, opt)

  cdiv = uuc
  cdiv = uv2dvF_Wrap(uuc,vvc) 

   cUVdiv = dv2uvF_Wrap (cdiv) 
;;  maskout missing again 
   cUVdiv(0, :, :, :, :) = where( .not.ismissing(uuc(:, :, :, :)), cUVdiv(0, :, :, :, :), uuc@_FillValue)
    cUVdiv(1, :, :, :, :) = where( .not.ismissing(uuc(:, :, :, :)), cUVdiv(1, :, :, :, :), uuc@_FillValue)

    cUVdiv@units = " "
    cUVdiv@long_name = " "

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

      label2 = title_mode + "  (" + season + ")"
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
     label4 = "  Months/Season= " 
     end if
     gsn_text_ndc (wks, label4, xs4, ys4, txres2)
  
   res@vcRefMagnitudeF =  divmag(nlev)  ;;             ; make vectors larger
   res@vcRefLengthF    =  veclength ;; 0.050                 ; reference vector length
   res@vcGlyphStyle    = "CurlyVector"         ; turn on curly vectors
   res@vcMinDistanceF  =  thinvector ;;  0.012                 ; thin the vectors
   res@vcLineArrowThicknessF  = thick_vector
   res@vcLabelFontHeightF =  height_ref  
   res@vcRefAnnoFontThicknessF  = thick_ref
  
   plot= gsn_csm_vector_map(wks, cUVdiv(0, 0, kk, :, :), cUVdiv(1, 0, kk,:,:), res)

   end if 
   end do  ;;; over pressure levels 

  delete( [/ lon, lat, plev1, time,  zdim, uuc, vvc, cdiv, cUVdiv /])
end do 

end
