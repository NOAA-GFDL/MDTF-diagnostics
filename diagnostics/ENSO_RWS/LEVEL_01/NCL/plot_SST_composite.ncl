;;   plot the ElNino/LaNina composite anomalies 
;;    SST in this case 


begin

   cmin = (/ -3.2, -3.2 /)

   cmax = (/  3.2 , 3.2 /)

   cint = (/ 0.4,  0.4  /)

   modes = (/ "ELNINO", "LANINA" /)

   variable =  "ts" 
   variname = "Skin Temperature" 

   varunit =  "[~F34~0~F~C]" ;;;   "[deg. C]"

   title_mode = (/ "El Nino",  "La Nina" /)

  varcode = getenv("POD_HOME")

    dirname1  =  getenv("ENSO_RWS_WKDIR")
    obsname   =  getenv("OBS_DATA") + "/DATA/"

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
     tt0 = 0 
     colormap = "BlueWhiteOrangeRed" 

   do icase = 1, 2 

  if( icase .eq. 1) ;;  model
   dirname  =  dirname1 + "/model"
   outdir   =  dirname1 + "/model"
     model =   getenv( "CASENAME")
    end if

  if( icase .eq. 2) ;;; OBS
   dirname = obsname
   outdir  = dirname1  + "/obs"
      model = " " ;; 
    end if

  
    do n = 0, 1
        mode  =  modes(n)
        namein  = dirname  + "/netCDF/"  + mode
        nameout = outdir  + "/PS/"
 
      namein1 = dirname + "/netCDF/" + mode + "/" + variable + ".nc" 
      namein2 =  dirname +  "/netCDF/"  + variable + ".nc"
;;    read in the variables 
      f1 = addfile( namein1, "r") 
      sst1 = f1->$variable$
      f2 = addfile( namein2, "r")
      sst2 = f2->$variable$
      delete( f1) 
      delete( f2) 
    sst = sst1
    sst = sst1 - sst2 
    sst@units = " "
    sst@long_name = " "

   nameout2 =  nameout + variable + "_" + mode 
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
 res@cnLevelSelectionMode  = "ManualLevels"

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = False

 res@cnMinLevelValF        = cmin(n)
 res@cnMaxLevelValF        = cmax(n)
 res@cnLevelSpacingF       = cint(n)

 res@gsnMaximize         = True

   txres1 = True
   txres1@txFontColor =  "black"
   txres1@txFont   = "helvetica"
   txres1@txFontHeightF = 0.025
   txres1@txJust        = "CenterLeft"
   txres1@txFuncCode    = "~"

      label2 = variname
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
     plot = gsn_csm_contour_map(wks, sst(tt0,:,:), res)

     end do 
 
   delete ([/ sst, sst1, sst2 /])
 end do

end
