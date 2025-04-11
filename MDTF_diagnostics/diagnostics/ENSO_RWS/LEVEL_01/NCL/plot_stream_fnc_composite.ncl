;;   plot the ElNino/LaNina composite anomalies 
;;   stream function composite anomalies at 500 and 200 mb 

begin

   modes = (/ "ELNINO", "LANINA" /)

   variable1 =  "ua"
   variable2 =  "va"
 
   variname = "Stream Function" 

   outname = "streamfunction"

   plevel2 = (/ 200,  500  /)
   nlevels2 = dimsizes( plevel2)
   

   ff6 = 1.E-06
   varunit = (/ "[x10~S~+06~N~m~S~2~N~s~S~-1~N~]" /)

;;   contour levels  one for each p-level
   
   levels2 = (/ (/ -20,  -18, -16, -14, -12, -10, -8, -6, -4, -2, 0, 2, 3, 4, 6, 8, 10, 12, \
                   14, 16, 18, 20 /) ,                  \
              (/ -20,  -18, -16, -14, -12, -10, -8, -6, -4, -2, 0, 2, 3, 4, 6, 8, 10, 12, \
                 14, 16, 18, 20 /)  /)   

   cmin = (/ -20, -10 /)
   cmax = (/  20,  10 /)
   cint = (/   2,   1 /)

   title_mode = (/ "El Nino",  "La Nina" /)

     varcode = getenv("POD_HOME")

     dirname1  =  getenv("ENSO_RWS_WKDIR")
     obsname  =  getenv("OBS_DATA") + "/DATA/"

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

;;  stream function index 0,  velocity potential index 1
;;  fill undefined
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill( ua, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( va, gtype, guess, nscan, eps, relc, opt)


    asfvp  = uv2sfvpF (ua,va)
;;  mask undefined
    asfvp(0, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), asfvp(0, :, :, :, :), uu1@_FillValue)
    asfvp(1, :, :, :, :) = where( .not.ismissing(uu1(:, :, :, :)), asfvp(1, :, :, :, :), uu1@_FillValue)
    
    asfvp = ff6 * asfvp

   asfvp!1 = "time"
   asfvp!2 = "lev"
   asfvp!3 = "lat"
   asfvp!4 = "lon"

   asfvp@time = "time"
   asfvp@lev = "plev"
   asfvp@lat = "lat"
   asfvp@lon = "lon"

   asfvp&time = time
   asfvp&lev = plev1
   asfvp&lat = lat
   asfvp&lon = lon

    asfvp@units = " "
    asfvp@long_name = " "

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
 res@cnLevelSelectionMode  =  "ManualLevels" ;;; "ExplicitLevels" 

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = True ;;  False
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
  
   cmap = read_colormap_file(colormap)
   res@cnFillPalette = cmap
   res@cnMinLevelValF       = cmin(nlev)                ; set min contour level
   res@cnMaxLevelValF       = cmax(nlev)                ; set max contour level
   res@cnLevelSpacingF      = cint(nlev)               ; set contour spacing


     plot = gsn_csm_contour_map(wks, asfvp(0, 0, kk,:,:),res)
 
   end if  
    end do  ;;; over pressure levels 

   end do 

   delete ([/lon, lat, plev1, time,  zdim, uuc, vvc, uu1, vv1, ua, va, asfvp /])
 end do 
end
