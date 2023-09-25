;;;     

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

begin

;; levels to plot 
   plevel2 = (/  200.  /)
   nlevels2 = dimsizes( plevel2) 

   mode = "CLIMA"

   variable1 =  "ua"
   variable2 =  "va"

   variname = "Beta star"

   outname = "betastar"

   title_mode = " "

    ff = 1.E+11   ;;   for beta star
    varunit = (/ "[x10~S~-11~N~m~S~-1~N~s~S~-1~N~]" /)

  levels1 = (/ -1.,  0., 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13, 14, 15, 16 /)
  levels0 = (/ 0. /)

    colormap = "precip2_17lev" ;;   "WhiteBlueGreenYellowRed"

     varcode = getenv("POD_HOME")
     dirname1  =   getenv("ENSO_RWS_WKDIR")
     obsname  = getenv("OBS_DATA") + "/DATA/"

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
     model = getenv( "CASENAME")  ;;  "CESM2" ;;  getenv( "CASENAME")
    end if

  if( icase .eq. 2) ;;; OBS
      dirname = obsname
      outdir  = dirname1  + "/obs"
      model = " " ;;   OBS leave it blank
    end if

    namein1 =  dirname +  "/netCDF/"  + variable1 + ".nc"
    namein2 =  dirname +  "/netCDF/"  + variable2 + ".nc"
    f1 = addfile( namein1, "r")
    uuc = f1->$variable1$
    f2 = addfile( namein2, "r")
    vvc = f2->$variable2$

    plev1 = f1->lev
    lon   = f1->lon
    lat   = f1->lat
    time  = f1->time
    ydim  = dimsizes( lat)
    zdim  = dimsizes( plev1)

    delete( f1)
    delete( f2)

   mm2 = 1
   wrf_smooth_2d(uuc,mm2)
   wrf_smooth_2d(vvc,mm2)


    nameout = outdir  + "/PS/"
;;  calculate beta star before plotting :
       betastar = uuc
       Uc2 = uuc

       sinlat = sin( tofloat(lat) * pi/180.)
       fcoriol = 2.* omega * sinlat

       coslat =  cos( tofloat(lat) * pi/180.)
       beta = 2.* omega * coslat/rearth

   do j = 1, ydim-2                      ; loop over each latitude
    dlat = 0.5 * tofloat((lat(j+1)-lat(j-1)) )
    dY = rearth * dlat * pi/180. 
    Uc2(:, :, j, :) = (uuc(:, :, j+1, :) - 2.*uuc(:, :, j, :) + uuc(:, :, j-1, :))/(dY*dY)
    betastar(:, :, j, :) =  (  beta(j)  -  Uc2(:, :, j, :) )
   end do

    betastar = ff * betastar
    betastar@units = " "
    betastar@long_name = " "

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
  res@cnLinesOn            = True ;;  
  res@cnLineThicknessF     = 0.1
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

      label2 = variname  + " level " +  pressure + " mb"
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 = title_mode + "  (" + season + ")"
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

     res@cnLevels    =   levels1
     cmap = read_colormap_file( colormap)
   
    i = 0
    gx = 150.
    cmap( i, 0) = gx/255.
    cmap (i,1) = gx/255.
    cmap (i,2) = gx/255.
    cmap (i,3) = 1

    i = 1
    gx = 200.
    cmap( i, 0) = gx/255.
    cmap (i,1) = gx/255.
    cmap (i,2) = gx/255.
    cmap (i,3) = 1

    res@cnFillPalette = cmap ( (/  0, 1,  2,  3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17 /), :)

    plot1 = gsn_csm_contour_map(wks,  betastar(0, kk, :, :), res)

  sres                      = True              ; set up a second resource list
  sres@gsnDraw              = False             ; do not draw the plot
  sres@gsnFrame             = False             ; do not advance the frame
  sres@cnLevelSelectionMode = "ExplicitLevels" ;; "ManualLevels" ;;;  "ExplicitLevels"  ; use explicit levels
  sres@cnLevels             =  levels0    ; set the contour levels

  sres@cnInfoLabelOn   = False                ; turn off info label box
  sres@cnLineLabelsOn  = False                ; no lables on line
  sres@cnFillOn        =  False
  sres@cnLineThicknessF =   10 
  sres@cnLineLabelInterval       =  2 ;; 
  sres@cnLineLabelPlacementMode   = "constant"

  sres@gsnContourNegLineDashPattern = 1
  sres@gsnContourZeroLineThicknessF = 2
  sres@cnInfoLabelOn = False
  sres@cnLineLabelsOn = False
  sres@cnLineLabelFormat  =  "f" ;; "0@;*.3f"

  betastar@long_name = " "

  plot2 = gsn_csm_contour(wks,  betastar(0, kk, :,:), sres)

  overlay(plot1,plot2)          ; overlay the U-wind plot on the temperature plot
  draw(plot1)                   ; draw the temperature plot (with the U-wind plot overlaid)
  frame(wks)

   end if   ;;  if on pressure levels
  
   end do ;;  over pressure levels 

 delete ([/lon, lat, plev1, time,  zdim, uuc, vvc,  betastar, Uc2, dY, dlat, beta, coslat,  fcoriol, sinlat/])
  end do 
 

end
