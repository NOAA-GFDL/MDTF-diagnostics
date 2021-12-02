;;;****************************************************

load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin 


   cmin = (/  (/  -3.2,   -8,   -60,   -40,  -32,  -8,  -60 /) ,  \
              (/  -3.2,  -3.6, -50,   -32,  -28,  -7,  -50 /) /)

   cmax = (/  (/ 3.2,   8,     60,   40,     32,   8,   60 /) ,  \
              (/ 3.2,   3.6,  50,    32,     28,   7,   50 /)  /)

   cint = (/  (/ 0.4,   1,    10,    5,     4,    1,  10 /),  \
              (/ 0.4,   0.4,  10,    4,     4,    1,  10 /)  /)


   modes = (/ "ELNINO", "LANINA" /) 

   variable_out = (/ "TS" , "SW", "LW", "LHF", "SHF", "PR", "FRAD"   /)

   variables = (/ "ts" , "sw", "lw", "hfls", "hfss", "pr", "frad"   /)

   varinames = (/ "SST" , "SW~B~net~N", "LW~B~net~N", "LHF", "SHF", "PRECIP", "F~B~rad~N" /)

   varunits =  (/ "[deg. C]", "[W/m2]", "[W/m2]", "[W/m2]", "[W/m2]", "[mm/day]",  "[W/m2]" /)

   title_mode = (/ "El Nino",  "La Nina" /)

      outdir  = getenv("ENSO_MSE_WKDIR") + "/model"
      outdir2  = getenv("ENSO_MSE_WKDIR_COMPOSITE") +"/model" ; envvar set in ENSO_MSE.py
      varcode  = getenv("POD_HOME")
      model = getenv( "CASENAME")


      parameter_name = varcode + "/shared/parameters.txt"

      nameclima = outdir2 +  "/netCDF/"

      tt0 = 0 
      xlon1 = 0
      xlon2 = 360
      xcenter  = (xlon1 + xlon2)/2

;;;  construct the main title based on model, season and region
      season = "XXX"

      lon1 = -9999.
      lon2 = -9999.
      lat1 = -9999.
      lat2 = -9999.
      undef2 = 1.1E+20

       data  = asciiread(parameter_name,-1,"string")

       season = str_get_field(data(10), 3," ")

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

   do n =  0, 1
   mode  =  modes(n) 

   do iv =  0,  6
    ff = 1.
    if( iv  .eq. 5) then
       ff = 24. * 60. * 60.
    end if 
;;  read  in the data from 

	namein  = outdir2 + "/netCDF/"  + mode
	nameout = outdir + "/PS/composite_"  + mode

;;;   read in various variables then  plot 
;;    
     variable = variables(iv) ;;;;  
     units = varunits(iv) ;;;  

     colormap = "BlueWhiteOrangeRed" ;; 
     if( iv .eq. 5 ) then
	 colormap =  "precip4_diff_19lev"
     end if
;;  the title 
   nameout12 = nameout + "_" + variable_out(iv)

   if( iv .le. 5) 
   namein1 = namein + "/" + variable + ".nc"  ;;  
   namein2 = nameclima +  variable + "_clim.nc"  ;;


     fin1 = addfile( namein1, "r")
     fin2 = addfile( namein2, "r")

      lat = fin1->lat
      lon = fin1->lon
      time0 = fin1->time
      time2 = calendar_decode2( time0 ,  -5)
      datain1 = fin1->$variable$
      datain2 = fin2->$variable$
;;   read in the data
;;  make the anomaly for plotting
    
     datain =  datain1
     datain = ff *( datain1  - datain2) 
     delete( [/ fin1, fin2 /])
    end if 

    if( iv .eq. 6)   ;;  net Frad
     variable = variables(1)
     namein1 = namein + "/" + variable + ".nc"  ;;
     namein2 = nameclima +  variable + "_clim.nc"  ;;

     fin1  = addfile( namein1, "r")
     fin2  = addfile( namein2, "r")
     lat = fin1->lat
      lon = fin1->lon
      time0 = fin1->time
      time2 = calendar_decode2( time0 ,  -5)
      datain1 = fin1->$variable$
      datain2 = fin2->$variable$
     delete( [/ fin1, fin2 /])

     variable = variables(2)
     namein1 = namein + "/"  + variable + ".nc"  ;;
     namein2 = nameclima +  variable + "_clim.nc"  ;;
     fin1 = addfile( namein1, "r")
     fin2 = addfile( namein2, "r")
      datain11 = fin1->$variable$
      datain22 = fin2->$variable$
;;  make the anomaly for plotting
    
     datain =  datain1
     datain = ff *( datain1  - datain2 +  datain11  - datain22)
  
    delete( [/ fin1, fin2 /])
    end if 
    
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
 res@cnLevelSelectionMode  = "ManualLevels"

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = False

 res@cnMinLevelValF        = cmin(n, iv)
 res@cnMaxLevelValF        = cmax(n, iv)
 res@cnLevelSpacingF       = cint(n, iv) 

 res@gsnMaximize         = True

;;  title 
  res@tiMainFontHeightF = 0.025
  res@tiMainFont = "helvetica"

;;;  title separate as two texts on the top
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

;;  legend - variable mode and season

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
       label4 = "  Months/Season= " + season + " Model: " + model + "  units:" +  units
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)

	plot = gsn_csm_contour_map(wks, datain(tt0,:,:), res)
   print( "finished " + iv + " " + variable)  
  end do  ;  over variables

  end do  ;  over modes
end
