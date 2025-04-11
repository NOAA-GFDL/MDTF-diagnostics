;;;*******************************************************
;
;
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin 

;;  read  in the data from MSE
        varcode = getenv("POD_HOME")
        outdir  =  getenv("ENSO_MSE_WKDIR") +"/model/"
        mse_dir  = getenv("ENSO_MSE_WKDIR_MSE") +"/model/"
        model = getenv( "CASENAME")

     nameclima = mse_dir + "netCDF/"


   ccenter = 0
   clevs = 20

;;    set the levels  :

   cmins1 = (/ -70., -240., -160., -160.,  -5E+07 /)
   cmaxs1 = (/  70.,  240.,  160.,  160.,   5E+07 /)
   cints1 = (/  10.,   40.,   20.,   20.,   1E+07 /)

   cmins2 = (/ -70., -200., -100., -120.,  -4E+07 /)
   cmaxs2 = (/  70.,  200.,  100.,  120.,   4E+07 /)
   cints2 = (/  10.,   40.,   20.,   20.,   1E+07 /)


   modes = (/ "ELNINO", "LANINA" /)

   variables = (/ "madv",  "mdiv", "omse", "tadv",  "mse" /)
   varinames = (/ "M~B~adv~N", "M~B~div~N", "MSE~B~vert. advect.~N", "T~B~adv~N" , "MSE" /)

   units = (/ "[W/m2]", "[W/m2]", "[W/m2]", "[W/m2]",  "[J/m2]" /)

   title_mode = (/ "El Nino",  "La Nina" /)

      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2

;;;  construct the main title based on model, season and region
      season = "XXX"
      datamode = "Anomaly"
      lon1 = -9999.
      lon2 = -9999.
      lat1 = -9999.
      lat2 = -9999.
      undef2 = 1.1E+20
	
      parameter_name = varcode + "/shared/parameters.txt"
      data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(10), 3," ")

;;;   read in various variables then  plot 
;;    
      do  n = 0, 1
      mode  = modes(n)  ;;; 

       namein  = mse_dir +  "/netCDF/" + mode

       nameout = outdir +  "/PS/" + mode ;;; 

       maintitle = "Composite " + title_mode(n)

     do iv = 0, 4
      variable = variables(iv) ;; 
      units2 =  units(iv) ;;  

      if( n .eq. 0) then
	 cmins = cmins1(iv) 
        cmaxs = cmaxs1(iv)
        cints = cints1(iv)
      end if 
      if( n .eq. 1) then
        cmins = cmins2(iv)
        cmaxs = cmaxs2(iv)
        cints = cints2(iv)
      end if
	 
     colormap = "BlueWhiteOrangeRed" ;;  
;;  the title 
    namein1 = namein    + "/MSE_" + variable + ".nc"  ;;  
    namein2 = nameclima + "/MSE_" + variable + ".nc"  ;;;

   nameout12 = nameout + "_" + variable
;;   read in the data
     fin1 = addfile( namein1, "r")
     fin2 = addfile( namein2, "r")

      lat   = fin1->lat
      lon   = fin1->lon

      ydim = dimsizes(lat)
      xdim = dimsizes(lon)
 
      datain1  = fin1->$variable$
      datain2  = fin2->$variable$
      delete( [/ fin1, fin2  /])
;;  make the anomaly for plotting
    datain = datain1
    datain = datain1  - datain2 
    datain =  where( (datain .gt.  -6.0E+07), datain,  datain@_FillValue) 

   datain@units = " "
   datain@long_name = " "

   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout12)
   gsn_define_colormap(wks,  colormap)

 res = True

  res@mpMinLonF              =  xlon1 
  res@mpMaxLonF              =  xlon2
  res@mpCenterLonF           = xcenter     ; This is necessary to get the correct map


 res@cnFillOn              = True
 res@cnFillMode            = "AreaFill"
 res@cnLinesOn             = False
 res@cnLevelSelectionMode  = "ManualLevels" ;;;  "AutomaticLevels" ;;  "ManualLevels"

  res@cnFillOn             = True                  ; turn on color fill
  res@cnFillPalette        = colormap        ; set color map
  res@cnLinesOn            = False

  symMinMaxPlt ( datain, clevs, False,res)  
  res@cnMinLevelValF        = cmins
  res@cnMaxLevelValF        = cmaxs
  res@cnLevelSpacingF       = cints

 res@gsnMaximize         = True

;;  title 
  res@tiMainFontHeightF = 0.025
  res@tiMainFont = "helvetica"

;;  legend - variable mode and season
      txres1 = True
      txres1@txFontColor =  "black"
      txres1@txFont   = "helvetica"
      txres1@txFontHeightF = 0.025
      txres1@txJust        = "CenterLeft"
      txres1@txFuncCode    = "~"
      xs1 = 0.08
      ys1 = 0.84
      dy2 = 0.0
      dx2 = 0.65
      label2 = varinames(iv)
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 = title_mode(n) + "  (" + season + ")"
      xs1 = xs1 + dx2
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

;;;;;;;;;;;;

      txres2 = True
      txres2@txFontColor =  "black"
      txres2@txFont   = "helvetica"
      txres2@txFontHeightF = 0.016
      txres2@txJust        = "CenterLeft"
      txres2@txFuncCode    = "~"

     xs1 = 0.1
     ys1 = 0.18
     dy2 = 0.0
     dx2 = 0.3
     label4 =  "Months/Season= " +  season +  " Model: " + model + " units:" + units2
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)
;;;;;    

	plot = gsn_csm_contour_map(wks, datain, res)

  
  end do 
  end do 
end
