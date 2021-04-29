;;;*******************************************************
;
;
;*******************************************************
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
; load "$POD_HOME/shared/gsnColorRange.ncl"

begin 


   cmin = (/  -2.8,  -2.4, -22.5, -18,  -12 /) ; min(datain)
   cmax = (/   2.8,   2.4,  22.5,  18,   12 /) ; max(datain)
   cint = (/   0.4,   0.4,  2.5,    2,    2 /)
   ccenter = 0
  

   variables = (/ "PR" , "SW", "LW", "LHF", "SHF" /)
   varinames = (/ "PRECIP" , "SW~B~net~N", "LW~B~net~N", "LHF", "SHF" /)
   varunits =  (/ "[mm/day]/[deg. C]", "[W/m2]/[deg. C]", "[W/m2]/[deg. C]", "[W/m2]/[deg. C]", "[W/m2]/[deg. C]"  /)


;;  read  in the data from 

      varcode  = getenv("POD_HOME")
      outdir  = getenv("ENSO_MSE_WKDIR_COMPOSITE") +"/model/" ; envvar set in ENSO_MSE.py
      outdir2 = getenv("ENSO_MSE_WKDIR") +"/model/"
      model = getenv( "CASENAME")

      parameter_name = varcode + "/shared/parameters.txt"
      name_dimensions =  outdir + "/netCDF/DATA/xyz_dimensions.txt"
      name_lon = outdir + "/netCDF/DATA/longitude.out"
      name_lat = outdir + "/netCDF/DATA/latitude.out"
      name_plevs = outdir + "/netCDF/DATA/plevels.out"

      namein = outdir + "/netCDF/"  
      nameout = outdir2 +  "/PS/regression" 
	 
      maintitle = "NINO3.4 SST on "

      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2

;;;  construct the main title based on model, season and region
      season = "XXX"
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
     do iv = 0, 4
     variable = variables(iv) ;;;;    
     units = varunits(iv)

     colormap = "BlueWhiteOrangeRed" ;;   "BlWhRe"  ;;   "BlRe"
;;  the title 

     namein1 = namein + "/REGRESS_" + variable + ".grd"  ;;  str_concat( string)
     nameout12 = nameout + "_" + variable

 
;;   read in the data
     dims = (/  ymax, xmax /)
     datain1 =  new(  dims, "float")
     datain1@_FillValue = undef2
     datain1  = fbindirread (namein1, 0, dims , "float")


;;  make the anomaly for plotting
       datain1!0="lat"
 	datain1!1="lon"
	datain1&lat = lat
	datain1&lon = lon 

   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout12)
   gsn_define_colormap(wks,  colormap)

 res = True

  res@mpMinLonF              =  xlon1 
  res@mpMaxLonF              =  xlon2
  res@mpCenterLonF           = xcenter     ; This is necessary to get the correct map
  res@txFuncCode    = "~"

 res@cnFillOn              = True
 res@cnFillMode            = "AreaFill"
 res@cnLinesOn             = False
 res@cnLevelSelectionMode  = "ManualLevels"

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = False

  res@cnMinLevelValF        = cmin(iv)
  res@cnMaxLevelValF        = cmax(iv)
  res@cnLevelSpacingF       = cint(iv)

 res@gsnMaximize         = True

;;  title 
  res@tiMainFontHeightF = 0.025
  res@tiMainFont = "helvetica"

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
      dx2 = 0.8
      label2 = maintitle + " " +  varinames(iv)
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 =  "(" + season + ")"
      xs1 = xs1 + dx2
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

;;;;;;;;;;;;;;;;;;;;;;
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
     label4 = "Months/Season= " +  season +  " Model: " + model + " units:" + units
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)

	plot = gsn_csm_contour_map(wks, datain1, res)


  end do  ;  over variables
end
