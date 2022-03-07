;;   plot the ElNino/LaNina composite anomalies 
;;   stream function composite anomalies at 500 and 200 mb 


begin

   modes = (/ "ELNINO", "LANINA" /)

   variable =  "zg"
 
   variname = "Geopotential Height" 

   outname = "height"

   plevel2 = (/ 200,  500  /)
   nlevels2 = dimsizes( plevel2)

   varunit = (/ "[m]" /)

;;   contour levels  one for each p-level

   levels2 = (/ (/ -100, -80, -60, -40, -20,  0, 20, 40, 60, 80, 100 /), \
                (/  -50, -40, -30, -20, -10,  0, 10, 20, 30, 40, 50 /) /)
   cmin =  (/ -100, -60 /)
   cmax =  (/  100,  60 /)
   cint =  (/   20,  10 /) 

   title_mode = (/ "El Nino",  "La Nina" /)

   varcode =  getenv("POD_HOME")

  dirname1  =  getenv("ENSO_RWS_WKDIR")
  obsname  =   getenv("OBS_DATA") + "/DATA/"

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

   do  icase = 1, 2
    if( icase .eq. 1) ;; model 
      dirname =  dirname1 + "/model"
       outdir =  dirname1 + "/model"
       model =   getenv( "CASENAME")
    end if 
    if( icase .eq. 2) ;; OBS
      dirname =  obsname 
      outdir =  dirname1 + "/obs"
      model = " " 
    end if

    namein1 =  dirname +  "/netCDF/"  + variable + ".nc"

    f1 = addfile( namein1, "r")
    hgtc = f1->$variable$

    plev1 = f1->lev
    lon = f1->lon
    lat = f1->lat
    time = f1->time
    zdim = dimsizes( plev1) 

    delete( f1)


    do n = 0, 1
        mode  =  modes(n)
        namein  = dirname  + "/netCDF/"  + mode
        nameout = outdir  + "/PS/"
 
      namein1 = dirname + "/netCDF/" + mode + "/" + variable + ".nc" 
;;    read in the variables 
      f1 = addfile( namein1, "r") 
      hgt = f1->$variable$

      delete( f1) 
;;; anomalies 
    hgta = hgt
    hgta = hgt - hgtc

    hgta@units = " "
    hgta@long_name = " "

    mm2 = 1
    wrf_smooth_2d(hgta, mm2)
;;;  loop over levels  select the index kk corresponding to plev(nlev) 

   do nlev = 0, nlevels2 - 1

   kk = -9 
   nlev2 = nlev
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
 res@cnLevelSelectionMode  =  "ManualLevels" ;; "ExplicitLevels" 

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = True ;;  
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
     gsn_text_ndc (wks, label4, xs4, ys4, txres2)
  
     cmap = read_colormap_file(colormap)
     res@cnFillPalette = cmap
     res@cnMinLevelValF       = cmin(nlev2)                ; set min contour level
     res@cnMaxLevelValF       = cmax(nlev2)              ; set max contour level
     res@cnLevelSpacingF      = cint(nlev2)

     plot = gsn_csm_contour_map(wks, hgta(0, kk,:,:),res)
  
     end if 
    end do  ;;; over pressure levels 
 
   end do   ;; over modes

   delete ([/ hgtc,  hgt, hgta, lon, lat, plev1, time,  zdim/])

  end do  ;;  
end  
