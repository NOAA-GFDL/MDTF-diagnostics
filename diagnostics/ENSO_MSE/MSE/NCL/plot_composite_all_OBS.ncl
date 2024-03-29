;;;*******************************************************
;

begin 

;;  read  in the data from  inputdata  obs_data  - predigested 
        varcode  = getenv("POD_HOME")
        obs_dir  = getenv("OBS_DATA") +"/DATA/"
        mse_dir =  getenv("ENSO_MSE_WKDIR_MSE") +"/obs/"
        outdir =  getenv("ENSO_MSE_WKDIR") +"/obs/"

     model = "  "  ;; leave blank for OBS

     parameter_name = varcode + "/shared/parameters.txt"
     nameclima = obs_dir  +  "/netCDF/"


;; select the  cmin, cmax, cint
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
      undef2 = 1.1E+20
	
       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(10), 3," ")

;;;  
;;;   read in various variables then  plot 
;;    
      do  n = 0, 1
      mode  = modes(n)  ;;; 

       namein  = obs_dir +  "/netCDF/" + mode
       nameout = outdir  +  "/PS/" + mode ;;;;  mse_dir +  "/PS/" + mode
       maintitle = "Composite " + title_mode(n)

     do iv = 0, 4
      variable = variables(iv) ;; "madv" 
      units2 =  units(iv) ;;   "[W/m2]"

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
    namein1 = namein + "/MSE_" + variable + ".nc"  ;;  
    namein2 = nameclima + "/MSE_" + variable + "_clim.nc"  ;;; 

    nameout12 = nameout + "_" + variable

;;   read in the data
;;;;  read in data and dimensions lon/lat  etc
     
     fin1 = addfile( namein1, "r")
     fin2 = addfile( namein2, "r")

     lon = fin1->lon
     lat = fin1->lat 
     
     xmax = dimsizes( lon)
     ymax = dimsizes( lat)
     
     dims2 = (/ ymax, xmax /)

     datain1 =  new(  dims2, "float")
     datain2 =  new(  dims2, "float")
     datain1@_FillValue = undef2
     datain2@_FillValue = undef2
     datain1 = fin1->$variables(iv)$
     datain2 = fin2->$variables(iv)$

;;  make the anomaly for plotting
    datain =  new(  dims2, "float")
    datain@_FillValue = undef2

       datain!0="lat"
 	datain!1="lon"
	datain&lat = lat
	datain&lon = lon 

       datain = datain1  - datain2
       do j = 0, ymax -1
         do i = 0, xmax - 1
          if( (.not.ismissing(datain(j,i)) ) .and. (datain(j, i) .le.  -6.0E+07) ) then
	      datain(j, i) =  undef2
          end if      
	  end do 
	end do
       
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
     label4 =  "Months/Season= " +  season +  "  " + model + " units:" + units2
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)
;;;;;    

	plot = gsn_csm_contour_map(wks, datain, res)

  end do 
  end do 
end
