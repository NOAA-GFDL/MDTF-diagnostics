;;;     

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

begin

;; levels to plot   only 200 mb now 
 
  varcode   =  getenv("POD_HOME")
  dirname1  =  getenv("ENSO_RWS_WKDIR")
  obsname   =  getenv("OBS_DATA") + "/DATA/"
   model2   =  getenv( "CASENAME")  

  modes = (/ "ELNINO", "LANINA" /)

   variable1 =  "ua"
   variable2 =  "va"

   variname = "RWS term"

   outname = (/ "term_0001", "term_0002", "term_0003", "term_0004", "term_0012", "term_0034", "term_1234" /)

   plevel1 = (/  200.  /)
   nlevels = dimsizes( plevel1)

   title_mode =  (/ "El Nino",  "La Nina" /)

    ff = 1.E+11
    varunit = "[x10~S~-11~N~s~S~-2~N~]"

   termlabel = (/ "01", "02", "03", "04", "01+02", "03+04", "01+02+03+04" /)
  
;;;  
  levels1 = (/ -30, -27, -24, -21, -18, -15, -12, -9, -6,  6, 9, 12, 15, 18, 21, 24, 27, 30 /)
  levels2 = (/ -10, -9, -8, -7, -6, -5, -4, -3, -2, -1,  1, 2, 3, 4, 5, 6, 7, 8, 9, 10 /) 

  levels3 =  levels2
  levels4 =  levels2

  levels5 =  levels1

  levels6 =  (/ -20, -18, -16, -14, -12, -10, -8, -6, -4,  4, 6, 8, 10, 12, 14, 16, 18, 20 /)
  levels7 =  levels1

   colormap = "hotcold_18lev"

      parameter_name = varcode + "/shared/parameters.txt"
;;;   global map
      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(7), 3," ")
 
     xs1 = 0.08
     ys1 = 0.84
     dy2 = 0.0
     dx2 = 0.65

     xs4 = 0.08
     ys4 = 0.14
  

    omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.

   do icase = 1, 2

   if( icase .eq. 1) ;;  model
     dirname  =  dirname1 + "/model"
     outdir   =  dirname1 + "/model"
     model = model2  ;;;  getenv( "CASENAME") ;;; 
    end if

  if( icase .eq. 2) ;;; OBS
      dirname = obsname
      outdir  = dirname1  + "/obs"
      model = " " ;;   observations - leave it blank 
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
    ydim = dimsizes( lat)
    zdim = dimsizes( plev1)

    delete( f1)
    delete( f2)

;;;  anomalies    loop over elnino/lanina modes

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
;;;  fill in adiv and cdiv
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


    avort   =  ua
    cvort2  =  uuc
    avort   = uv2vrF_Wrap (ua, va)   ;; 
    cvort2  = uv2vrF_Wrap (uuc, vvc) ;;    
    
    sinlat = sin( lat * pi/180.)
    fcoriol = 2.* omega * sinlat

    coslat =  cos(lat * pi/180.)
    beta = 2.* omega * coslat/rearth

     cvort = cvort2
     do j = 0, ydim - 1
     cvort(:, :, j, :) =  ( tofloat(fcoriol(j))  + cvort2(:, :, j, :) )
     end do
 
     avortx = uu1
     avorty = uu1
     cvortx = uu1
     cvorty = uu1

;;;;   anomaly vorticity and climatolog vorticity gradients 
     
       gradsf (avort,  avortx, avorty)
       gradsf (cvort,  cvortx, cvorty)

     adiv = uu1
     cdiv = uuc
     adiv = uv2dvF_Wrap( ua, va) ;;  
     cdiv = uv2dvF_Wrap( uuc, vvc) ;;  
   
     aUVdiv = dv2uvF_Wrap (adiv)  
     cUVdiv = dv2uvF_Wrap (cdiv) 
;;  mask the undefined   0 = zonal  1 = meridional 
    aUVdiv(0, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), aUVdiv(0, :, :, :, :), uu1@_FillValue)     
    aUVdiv(1, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), aUVdiv(1, :, :, :, :), uu1@_FillValue) 

   cUVdiv(0, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), cUVdiv(0, :, :, :, :), uu1@_FillValue)  
   cUVdiv(1, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), cUVdiv(1, :, :, :, :), uu1@_FillValue) 
    adiv(  :, :, :, :) = where( .not.ismissing( ua(:, :, :, :)), adiv(  :, :, :, :), ua@_FillValue)
    cdiv(  :, :, :, :) = where( .not.ismissing(uuc(:, :, :, :)), cdiv(  :, :, :, :), uuc@_FillValue)
    
    avortx(:, :, :, :) =  where( .not.ismissing( ua(:, :, :, :)), avortx(:, :, :, :),ua@_FillValue)
    avorty(:, :, :, :) =  where( .not.ismissing( ua(:, :, :, :)), avorty(:, :, :, :),ua@_FillValue)
    cvortx(:, :, :, :) =  where( .not.ismissing(uuc(:, :, :, :)), cvortx(:, :, :, :),ua@_FillValue)
    cvorty(:, :, :, :) =  where( .not.ismissing(uuc(:, :, :, :)), cvorty(:, :, :, :),ua@_FillValue)
   

;;;   term1 = cvort (clima abs vorticity) *  div ( UVdivanom)
      term1 = uu1
      term1 = -1.*( cvort * adiv)
;;;   term2 = aUVdiv * cvortxy( gradient )
      term2 = term1
      term2(:, :, :, :) = -1.*( aUVdiv(0, :, :, :, :) * cvortx(:, :, :, :) +  aUVdiv(1, :, :, :, :) * cvorty(:, :, :, :))

;;;   term3 =  avort( * div( UVdivclim)
      term3 =  term1 
      term3 = -1.*( avort * cdiv)
;;;   term4 =  UVdivclim  *  grad( avortxy)
      term4 =  term1 
      term4(:, :, :, :) = -1.*( cUVdiv(0, :, :, :, :) * avortx(:, :, :, :) +  cUVdiv(1, :, :, :, :) * avorty(:, :, :, :))


  term1 = ff * term1
  term2 = ff * term2
  term3 = ff * term3
  term4 = ff * term4
  term5 =  term1 
  term5 =  (term1 + term2) 
  term6 =  term1 
  term6 =  (term3 + term4)    
  term7 =  term1 
  term7 =  (term1 + term2 + term3 + term4) 

;;;;;;   plotting 

    kk = 0
    nn = 0 
   do nn = 0, nlevels-1
   
   do k = 0, zdim - 1
    if( plevel1(nn) .eq. plev1(k))
    kk = k
    end if
   end do 

   pressure =  tostring_with_format( tointeger(plev1(kk)), "%3.3d")  ;;;  
;;   loop over the 7 variables 
   do ivar = 0, 6 

   invar = tostring_with_format( ivar+1, "%2.2d")

   nameout2 =  nameout + outname(ivar) +  "_" + mode + "_" + pressure

   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout2)

    gsn_define_colormap(wks,  colormap)

   res = True

  res@mpMinLonF              =  xlon1
  res@mpMaxLonF              =  xlon2
  res@mpCenterLonF           = xcenter     ; This is necessary to get the correct map


  res@cnFillOn              = True
  res@cnFillMode            = "AreaFill"
  res@cnLinesOn             =  False
  res@cnLevelSelectionMode  = "ExplicitLevels"

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = False
;;  the color bar
  res@lbAutoManage          = False             ; we control label bar
  res@pmLabelBarDisplayMode = "Always"          ; turns on label bar
  res@lbOrientation         = "Horizontal"      ; ncl default is vertical
  res@pmLabelBarSide        = "Bottom"          ; default is right
  res@lbLabelStride         = 1                ; skip every other label
  res@pmLabelBarWidthF      = 0.8               ; default is shorter
  res@pmLabelBarHeightF     = 0.15               ; default is taller
  res@lbLabelFontHeightF    = 0.012              ; default is HUGE
  res@lbPerimOn             = False


 res@gsnMaximize         = True
 res@mpGeophysicalLineThicknessF = 2

  res@gsnDraw      =  False                   ; do not draw the plot
  res@gsnFrame     =  False

   txres1 = True
   txres1@txFontColor =  "black"
   txres1@txFont   = "helvetica"
   txres1@txFontHeightF = 0.025
   txres1@txJust        = "CenterLeft"
   txres1@txFuncCode    = "~"

      label2 = variname + " " + termlabel(ivar) + " "   + " level " +  pressure + " mb"
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 = title_mode(n) + "  (" + season + ")"
      xs11 = xs1 + dx2
      gsn_text_ndc (wks, label2, xs11, ys1, txres1)

      txres2 = True
      txres2@txFontColor =  "black"
      txres2@txFont   = "helvetica"
      txres2@txFontHeightF = 0.02 ;; 
      txres2@txJust        = "CenterLeft"
      txres2@txFuncCode    = "~"

     label4 = "  Months/Season= " + season + " Model: " + model + "  units:" +  varunit
     if( icase .eq. 2)
     label4 = "  Months/Season= " + season + "                       units:" +  varunit
     end if

     gsn_text_ndc (wks, label4, xs4, ys4, txres2)
      iv = ivar
      if( iv .eq. 0) 
        levelss = levels1
	 termx = term1 
      end if     
      if( iv .eq. 1)
        levelss = levels2
        termx = term2
      end if
      if( iv .eq. 2)
        levelss = levels3
        termx = term3
      end if
      if( iv .eq. 3)
        levelss = levels4
        termx = term4
      end if
      if( iv .eq. 4)
        levelss = levels5
        termx = term5
      end if
      if( iv .eq. 5)
        levelss = levels6
        termx = term6
      end if
      if( iv .eq. 6)
        levelss = levels7
        termx = term7
      end if
      termx@units     = " "
      termx@long_name = " "

     res@cnLevels    =   levelss
     cmap = read_colormap_file(colormap)
     res@cnFillPalette = cmap    
     plot = gsn_csm_contour_map(wks, termx(0, kk, :, :), res)

     draw( plot)   
    frame(wks)

     delete( res@cnLevels)
     delete(  levelss)    
    
    end do ;;   over all terms 1, 2, 3... 7

   end do ;;  over all  pressure levels   in plevel1 0, nlevels -1

  end do ;;  over elnino/lanina modes  

 delete( [/  lon, lat, plev1, time,  ydim, zdim, ua, va, uu1, vv1, uuc, vvc /])
 delete( [/ cUVdiv, aUVdiv,  adiv, cdiv, avortx, avorty, cvortx,  cvorty, sinlat, fcoriol, coslat, beta, cvort2, cvort, avort /])
 delete( [/ term1, term2, term3, term4, term5, term6, term7, termx /])

end do 

end
