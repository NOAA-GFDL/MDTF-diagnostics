;;;;  to read grads  file  and get the climatology and anomaly divergent wind
;;;;    and the vorticity   ERA-INTERIM only 
;;;       overlay Hgt anomaly  Vanom contour  no ZERO !! 

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

     outname = "HGTanom_Vanom"
     variname = "Anomaly Height and Meridional Wind" 

     variable1 = "zg"
     variable2 = "va"
 
;; levels to plot 
   plevel1 = (/  200.  /)
   nlevels1 = dimsizes( plevel1) 


    tt0 = 0
    kk = 0

    omega = 7.292E-05
    pi = 3.142
    rearth = 6378000.

    unit =  (/ "[m]", "[m s~S~-1~N~]"/) 

    title2 = (/ "Colors height anomaly",  "Contours meridional wind anomaly" /)

;;;;  legends
     xs10 = 0.08
     ys10 = 0.84
     dx2 = 0.65

     xs110 = 0.05 ;;  
     ys110 = 0.15 ;;  
     dxs1 = 0. ;;  
     dys1 = -0.03

;;  need to set for each pressure level   here now only top is relevant 
    cmin = -100
    cmax = 100
    cint = 20
;;;   vanomaly levels for contours
   levels4 = (/ -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6 /)

   colormap =  "hotcold_18lev"

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

    wks_type = "eps" ;; "ps" ;;; "png"
;;;  time dimensions for seasonal averaging 

    namein1 =  dirname +  "/netCDF/"  + variable1 + ".nc"
    namein2 =  dirname +  "/netCDF/"  + variable2 + ".nc"

    f1 = addfile( namein1, "r")
    hgtc = f1->$variable1$
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

;;  read  anomaly U wind  and V 
    do n = 0, 1

     mode  =  modes(n)
     namein  = dirname  + "/netCDF/"  + mode
     nameout = outdir  + "/PS/"

      namein1 = dirname + "/netCDF/" + mode + "/" + variable1 + ".nc"
      namein2 = dirname + "/netCDF/" + mode + "/" + variable2 + ".nc"

    f1 = addfile( namein1, "r")
    hgt1 = f1->$variable1$
    f2 = addfile( namein2, "r")
    vv1 = f2->$variable2$

     mm2 = 1
     wrf_smooth_2d(hgt1,mm2)
     wrf_smooth_2d(vv1,mm2)

     delete( [/ f1, f2 /])

    hgta = hgt1
    hgta = hgt1 - hgtc
    va = vv1
    va = vv1 - vvc

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

   hgta@long_name = " "
   va@long_name = " ";
   hgta@units = " "
   va@units = " ";; 


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

    res@gsnMaximize  = True 

    res@cnFillOn             = True               ; turn on color fill
    res@cnLinesOn           =   False ;; 

      txres1 = True
      txres1@txFuncCode    = ":"
      txres1@txFontColor =  "black"
      txres1@txFont   =  "helvetica"
      txres1@txFontHeightF = 0.025 ;;  
      txres1@txJust        = "CenterLeft"
      txres1@txFuncCode    = "~"

      xs1 = xs10
      ys1 = ys10
      label2 = variname
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 =  title_mode(n) + "  (" + season + ")"
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
      if( icase .eq. 1) 
      gsn_text_ndc (wks, "Model: " + model2, xs11, ys11, txres2)
      end if 
;;  Hgt anomaly    i = 1    
    res@cnLevelSelectionMode = "ManualLevels" ;; "ExplicitLevels"
     cmap = read_colormap_file( colormap)
     res@cnFillPalette = cmap
     res@cnMinLevelValF       = cmin              ; set min contour level
     res@cnMaxLevelValF       = cmax              ; set max contour level
     res@cnLevelSpacingF      = cint

     plot1 = gsn_csm_contour_map(wks,  hgta(tt0, kk, :, :), res)
    
     delete(cmap)
   delete( res@mpMinLatF)
   delete( res@mpMaxLatF)
   delete( res@mpMinLonF)   
   delete( res@mpMaxLonF)   
   delete( res@mpCenterLonF)

;;;;  V anomaly  in contours 
   i = 2
   res@cnLevelSelectionMode =  "ExplicitLevels" ;;
   res@cnLinesOn           =  True
   res@cnFillOn            = False 
   res@cnLevels            =   levels4
;;;   contour lines 
    res@pmLabelBarDisplayMode = "NoCreate"

    res@cnLineThicknessF =   3 ;;  
    res@cnLineLabelInterval       =  2 ;; 
    res@cnLineLabelPlacementMode   = "constant"
    res@cnLineLabelFontHeightF = 0.009 ;;
    res@cnLineLabelFontThicknessF  = 1.
    res@cnInfoLabelOn = False
    res@cnLineLabelsOn   =  True ;;;   False
    res@gsnContourNegLineDashPattern  = 7
    res@gsnContourZeroLineThicknessF  = 5

   plot2 = gsn_csm_contour(wks,   va(tt0, kk,:,:),res)
    
     overlay( plot1, plot2)

    draw( plot1)
   frame(wks)

   end do  ;;  over ELNINO/LANINA

  delete ([/lon, lat, plev1, time,  zdim1, hgt1, hgtc, hgta, vv1, vvc, va, res /])
 
 end do ;;  over  MODEL/OBS

end
