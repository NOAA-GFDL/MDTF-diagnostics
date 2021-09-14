;;   plot the ElNino/LaNina composite anomalies 


begin

   mode = "CLIMA"

   variable =  "ua"
 
   variname = "Zonal Wind" 

   outname = "U_wind"

   plevel2 = (/ 200  /)
   nlevels2 = dimsizes( plevel2)
   
;;  
   varunit = (/ "[m s~S~-1~N~]" /)
;;   contour levels  one for each p-level
     cmin = -10.
     cmax =  75.
     cint =   5

   levels = (/ -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75 /)

   cmin2 = 0.
   cmax2 = 1000
   cint2 = 1000


   title_mode =  "Climatology" 

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

     colormap = "precip2_17lev" ;;    "WhiteBlueGreenYellowRed"

   do icase = 1, 2

   if( icase .eq. 1) ;;  model
   dirname  =  dirname1 + "/model"
   outdir   =  dirname1 + "/model"
     model = getenv( "CASENAME") ;;;  "CESM2" ;;  getenv( "CASENAME")
    end if

  if( icase .eq. 2) ;;; OBS
   dirname = obsname
   outdir  = dirname1  + "/obs"
      model = " " ;;  OBS = blank
    end if

    namein1 =  dirname +  "/netCDF/"  + variable + ".nc"
    f1 = addfile( namein1, "r")
    uuc = f1->$variable$

    plev1 = f1->lev
    lon = f1->lon
    lat = f1->lat
    time = f1->time
    zdim = dimsizes( plev1) 

    delete( f1)


     namein  = dirname  + "/netCDF/"  + mode
     nameout = outdir  + "/PS/"

    uuc@units = " "
    uuc@long_name = " "

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

  res@gsnFrame             = False               ; don't advance frame
  res@gsnDraw              = False

  res@mpMinLonF              =  xlon1
  res@mpMaxLonF              =  xlon2
  res@mpCenterLonF           = xcenter     ; This is necessary to get the correct map


 res@cnFillOn              = True
 res@cnFillMode            = "AreaFill"
 res@cnLinesOn             = False
 res@cnLevelSelectionMode  = "ManualLevels " ;;  "ExplicitLevels" 

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
     label4 = "  Months/Season= " + season + "                       units:" +  varunit
     end if
     gsn_text_ndc (wks, label4, xs4, ys4, txres2)
  

      cmap = read_colormap_file(colormap)

    cmap( 17, 0) = 90./255.
    cmap (17,1) = 0.
    cmap (17,2) = 0.
    cmap (17,3) = 1

    i = 0
    cmap( i, 0) = 150./255.
    cmap (i,1) = 150./255.
    cmap (i,2) = 150./255.
    cmap (i,3) = 1
    i = 1
    cmap( i, 0) = 180./255.
    cmap (i,1) = 180./255.
    cmap (i,2) = 180./255.
    cmap (i,3) = 1
     i = 2
    cmap( i, 0) = 200./255.
    cmap (i,1) = 200./255.
    cmap (i,2) = 200./255.
    cmap (i,3) = 1

    i = 8
    cmap(i,0) = 164./255. ;; 184./255.
    cmap(i,1) = 215./255. ;;; 235./255.
    cmap(i,2) = 200./255. ;;;  220./255.
    cmap(i,3) = 1
 
     cmap(:, 3) = 0.75

     res@cnFillPalette =  cmap( (/0, 1, 2,  3, 4, 5, 6, 7, 8,  10, 11, 12,13, 14, 15, 16, 17 /), :)

     res@cnMinLevelValF       = cmin                ; set min contour level
     res@cnMaxLevelValF       = cmax                ; set max contour level
     res@cnLevelSpacingF      = cint 
      
     plot1 = gsn_csm_contour_map(wks, uuc(0, kk, :, :),res)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

    res2 = True
    res2@gsnMaximize          = True                ; maximize pot in frame
    res2@gsnFrame             = False               ; don't advance frame
    res2@gsnDraw              = False

;;     delete(uuc@long_name)

    res2@cnLineThicknessF =   1;;    4 ;;   linethick
    res2@cnLineLabelInterval        = 1             ; default = 2
    res2@cnLineLabelPlacementMode   = "constant"
    res2@cnLineLabelFontHeightF = 0.008 ;;  0.015
    res2@cnLineLabelFontThicknessF  = 1.
    res2@gsnContourZeroLineThicknessF  = 5
    res2@cnInfoLabelOn = False
    res2@cnLineLabelsOn   =  False

    res2@cnLevelSelectionMode = "ManualLevels"   ;

   res2@cnFillOn = False
   res2@cnLinesOn   = True
   res2@cnMinLevelValF  = cmin2                  ; set the minimum contour level
   res2@cnMaxLevelValF  = cmax2                  ; set the maximum contour level
   res2@cnLevelSpacingF = cint2

   plot2 = gsn_csm_contour(wks,  uuc(0, kk, :,:), res2)

   overlay( plot1, plot2)
 
   draw( plot1)
   frame(wks)

    end if  
    end do  ;;; over pressure levels 
 
  delete( [/  lon, lat, plev1, time,  zdim, uuc /])
 end do 
end
