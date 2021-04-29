;;;*******************************************************
;
;
; Concepts illustrated:
;   - Drawing multiple bar charts on a page
;   - Drawing three custom legends outside a bar chart
;   - Using bar charts to draw standard deviations for four timeseries
;*******************************************************
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
;;load "$POD_HOME/shared/gsnColorRange.ncl"

begin 

;;  read  in the data from MSE
        varcode = getenv("POD_HOME")
        outdir  =  getenv("ENSO_MSE_WKDIR") +"/model/"

        composite_dir  = getenv("ENSO_MSE_WKDIR_COMPOSITE") +"/model/"
        mse_dir  = getenv("ENSO_MSE_WKDIR_MSE") +"/model/"
        model = getenv( "CASENAME")


       parameter_name = varcode + "/shared/parameters.txt"
       name_dimensions =  composite_dir + "netCDF/DATA/xyz_dimensions.txt"
       name_lon = composite_dir + "netCDF/DATA/longitude.out"
       name_lat = composite_dir + "netCDF/DATA/latitude.out"
       name_plevs = composite_dir + "netCDF/DATA/plevels.out"

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
;;   varinames = (/ "moisture advection", "moist divergence", "MSE vert. advect.", "temp. advection", "MSE" /)
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
	
       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(12), 3," ")

;;;   read the lat/lon and dimensions from external files - in DATA
       dataxyz  = asciiread(name_dimensions,-1,"string")
       xdum  = str_get_field(dataxyz(0), 1," ")
       xmax =  stringtointeger( xdum)
       ydum  = str_get_field(dataxyz(1), 1," ")
       ymax =  stringtointeger( ydum)
       zdum  = str_get_field(dataxyz(2), 1," ")
       zmax =  stringtointeger( zdum)

;;;  read in the lon/lat plevs here !!
       lon = fbindirread (name_lon, 0, (/ xmax /) , "float")
       lat = fbindirread (name_lat, 0, (/ ymax /) , "float")
       lon@units = "degrees_east"
       lon@long_name = "lon"
       lat@units = "degrees_north"
       lat@long_name = "lat"

;;;   read in various variables then  plot 
;;    
      do  n = 0, 1
      mode  = modes(n)  ;;; 

       namein  = mse_dir +  "/netCDF/" + mode

       nameout = outdir +  "/PS/" + mode ;;;   mse_dir +  "/PS/" + mode

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
	 
     colormap = "BlueWhiteOrangeRed" ;;   "BlWhRe"  ;;   "BlRe"
;;  the title 
;;    maintitle2 = maintitle + " " + season  +  " " + varinames(iv)
    namein1 = namein + "/MSE_" + variable + ".out"  ;;  str_concat( string)
    namein2 = nameclima+ "/MSE_" + variable + "_clim.out"  ;;; str_concat( string)


   nameout12 = nameout + "_" + variable
;   print( namein1) 
;   print( namein2 ) 
;;   read in the data
     dims = (/ zmax+1,  ymax, xmax /)
     dims2 = (/ ymax, xmax /)

     datain1 =  new(  dims2, "float")
     datain2 =  new(  dims2, "float")
     datain1@_FillValue = undef2
     datain2@_FillValue = undef2
     datain1  = fbindirread (namein1, 0, dims2 , "float")
     datain2  = fbindirread (namein2, 0, dims2 , "float")

;;     print( datain1)

;;  make the anomaly for plotting
    datain =  new(  dims2, "float")
    datain@_FillValue = undef2

       datain!0="lat"
 	datain!1="lon"
	datain&lat = lat
	datain&lon = lon 

       datain = datain1( :, :)  - datain2( :, :) 
       do j = 0, ymax -1
         do i = 0, xmax - 1
          if( (.not.ismissing(datain(j,i)) ) .and. (datain(j, i) .le.  -6.0E+07) ) then
	      datain(j, i) =  undef2
          end if      
	  end do 
	end do
       
;;  gsn_range = gsnColorRange(cmin, cmax, cint, ccenter, 97, 49)

;;   wks_type = "png"
;;   wks_type@wkWidth = 1000
;;   wks_type@wkHeight = 1000
   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout12)
   gsn_define_colormap(wks,  colormap)

 res = True
;;   res@gsnMaximize  = True                        ; maximize plot in frame

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
; res@gsnSpreadColors     = True
; res@gsnSpreadColorStart = gsn_range@ColorStart
; res@gsnSpreadColorEnd   = gsn_range@ColorEnd
; res@lbLabelStride       = 2

;;  title 
  res@tiMainFontHeightF = 0.025
  res@tiMainFont = "helvetica"
;;  res@tiMainString =  maintitle2

;;   gsn_define_colormap(wks,  colormap)
;;   plot = gsn_csm_contour_map(wks, datain, res)

;;  legend - variable mode and season
;;  legend title
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
;;     label2 = (/ datamode, " ",  "Months/Season= ", season, " Model: ", model, "  ", variable, " " , units2 /)
;;     new_label2 = str_concat(label2)
     label4 =  "Months/Season= " +  season +  " Model: " + model + " units:" + units2
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)
;;;;;    

	plot = gsn_csm_contour_map(wks, datain, res)

;;  frame(wks)      
  end do 
  end do 
end
