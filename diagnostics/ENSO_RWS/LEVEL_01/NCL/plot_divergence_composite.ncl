;;   plot the ElNino/LaNina composite anomalies 
;;   stream function composite anomalies at 500 and 200 mb  both model + OBS


begin

   modes = (/ "ELNINO", "LANINA" /)

   variable1 =  "ua"
   variable2 =  "va"
 
   variname = "Divergence" 

   outname = "divergence"

   plevel2 = (/ 200,  500  /)
   nlevels2 = dimsizes( plevel2)
   
;;  
    levels4 = (/ (/ -5., -4.5, -4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, \
                     0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0 /) ,  \
              (/ -2.50, -2.25, -2.00, -1.75, -1.50, -1.25, -1.00, -0.75, -0.50, -0.25, \
                 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50 /) /)
    
   ff4 = 1E+06 
   varunit = (/ "[x10~S~-06~N~s~S~-1~N~]" /)

;;   contour levels  one for each p-level

   title_mode = (/ "El Nino",  "La Nina" /)

    varcode =  getenv("POD_HOME")

   dirname1  =  getenv("ENSO_RWS_WKDIR")
   obsname  =   getenv("OBS_DATA") + "/DATA/"
   varcode =  getenv("POD_HOME")

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
     dx2 = 0.65

     xs4 = 0.08
     ys4 = 0.14

     colormap = "temp_diff_18lev"  ;;  "hotcold_18lev"

   do  icase = 1, 2

   if( icase .eq. 1) ;;  model
      dirname  =  dirname1 + "/model"
      outdir   =  dirname1 + "/model"
      model =  getenv( "CASENAME")
    end if

  if( icase .eq. 2) ;;; OBS
      dirname = obsname   
      outdir  = dirname1  + "/obs"
      model = " " ;;  
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

     mm2 = 1
     wrf_smooth_2d(ua,mm2)
     wrf_smooth_2d(va,mm2)
     wrf_smooth_2d(uuc,mm2)
     wrf_smooth_2d(vvc,mm2)

;;  divergence 
    adiv = uu1
    adiv = uv2dvF_Wrap( ua, va) ;;  
    adiv = ff4 * adiv

;;  mask the undefined
   adiv(:, :, :, :) =  where( .not.ismissing(uu1(:, :, :, :)),  adiv(:, :, :, :), uu1@_FillValue)

    adiv@units = " "
    adiv@long_name = " "

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


 res@cnFillOn              = True
 res@cnFillMode            = "AreaFill"
 res@cnLinesOn             = False
 res@cnLevelSelectionMode  = "ExplicitLevels" 

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = False
;;  the color bar 
  res@lbAutoManage          = False             ; we control label bar
  res@pmLabelBarDisplayMode = "Always"          ; turns on label bar
  res@lbOrientation         = "Horizontal"      ; ncl default is vertical
  res@pmLabelBarSide        = "Bottom"          ; default is right
  res@lbLabelStride         = 1                ; skip every other label
  res@pmLabelBarWidthF      = 0.85 ;;           ; default is shorter
  res@pmLabelBarHeightF     = 0.15               ; default is taller
  res@lbLabelFontHeightF    = 0.012              ; default is HUGE
  res@lbPerimOn             = False       


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
      txres2@txFontHeightF = 0.02 ;; 
      txres2@txJust        = "CenterLeft"
      txres2@txFuncCode    = "~"

     label4 = "  Months/Season= " + season + " Model: " + model + "  units:" +  varunit
     if( icase .eq. 2) 
     label4 = "  Months/Season= " + season + "                        units:" +  varunit
     end if
     gsn_text_ndc (wks, label4, xs4, ys4, txres2)
  
    res@cnLevels    =   levels4(nlev,:)

    cmap = read_colormap_file(colormap)
    res@cnFillPalette = cmap ( (/0, 1, 2, 3, 4, 5, 6, 7,   9,  11, 12, 13, 14, 15, 16, 17, 18  /), :)
     plot = gsn_csm_contour_map(wks, adiv(0, kk,:,:),res)
 
    end if  
    end do  ;;; over pressure levels 

   end do   ;; over modes Elnino/Lanina

   delete ([/uuc, vvc, uu1, vv1, ua, va, adiv, lon, lat, plev1, time,  zdim/])

   end do  ;;  over model/OBS
end
