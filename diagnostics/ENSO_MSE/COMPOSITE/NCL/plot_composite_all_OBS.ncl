;;;****************************************************
;
;
;*******************************************************
;
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
;load "$POD_HOME/shared/gsnColorRange.ncl"

begin 

;; select the  cmin, cmax, cint
;;;    need the two rows El Nino/La Nina 
   cmin = (/  (/  -3.2,   -8,   -60,   -40,  -32,  -8,  -60 /) ,  \
              (/  -3.2,  -3.6, -50,   -32,  -28,  -7,  -50 /) /)

   cmax = (/  (/ 3.2,   8,     60,   40,     32,   8,   60 /) ,  \
              (/ 3.2,   3.6,  50,    32,     28,   7,   50 /)  /)

   cint = (/  (/ 0.4,   1,    10,    5,     4,    1,  10 /),  \
              (/ 0.4,   0.4,  10,    4,     4,    1,  10 /)  /)

   modes = (/ "ELNINO", "LANINA" /) 

   variname2 = (/ "TS", "SW", "LW", "LHF",  "SHF",  "PR", "FRAD" /) 
   variables = (/ "ts" , "sw", "lw", "hfls", "hfss", "pr", "frad"   /)
   varinames = (/ "SST" , "SW~B~net~N", "LW~B~net~N", "LHF", "SHF", "PRECIP", "F~B~rad~N" /)

   varunits =  (/ "[deg. C]", "[W/m2]", "[W/m2]", "[W/m2]", "[W/m2]", "[mm/day]",  "[W/m2]" /)

   title_mode = (/ "El Nino",  "La Nina" /)

      outdir2 =  getenv("ENSO_MSE_WKDIR") +"/obs/" 

      obsdir  = getenv("OBS_DATA") +"/DATA/"  ; envvar set in ENSO_MSE.py
      outdir =  getenv("ENSO_MSE_WKDIR_COMPOSITE") +"/obs/" 
      varcode  = getenv("POD_HOME")
      

      model =  " "   ;;;;   leave blank for observations  getenv( "CASENAME")

      parameter_name = varcode + "/shared/parameters.txt"
      nameclima = obsdir +  "/netCDF/"

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

        season = str_get_field(data(12), 3," ")

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

   do n = 0, 1
   mode  =  modes(n) 

   do iv = 0, 6
    ff = 1.
    if( iv  .eq. 5) then
       ff = 24. * 60. * 60.
    end if 
;;  read  in the data from 

	namein  = obsdir + "/netCDF/"  + mode
	nameout = outdir2 + "/PS/composite_"  + mode

;;      maintitle = "Composite " + title_mode(n)  + " " + varinames(iv)
;;;   read in various variables then  plot 
;;    
     variable = variables(iv) ;;;;  
     units = varunits(iv) ;;;  

     colormap = "BlueWhiteOrangeRed" ;;   "BlWhRe"  ;;   "BlRe"
     if( iv .eq. 5 ) then
	 colormap =  "precip4_diff_19lev"
     end if
;;  the title 

   namein1 = namein + "/" + variable + ".nc"  ;;  str_concat( string)
   namein2 = nameclima +  variable + "_clim.nc"  ;;; str_concat( string)

   nameout12 = nameout + "_" + variname2(iv)
;    print( namein1) 
;   print( namein2 ) 
;;   read in the data and dimensions lon/lat

     fin1 = addfile( namein1, "r")
     fin2 = addfile( namein2, "r")

     lon = fin1->lon
     lat = fin1->lat

     xmax = dimsizes( lon)
     ymax = dimsizes( lat)
     dims = (/  ymax, xmax /)

     datain1 =  new(  dims, "float")
     datain2 =  new(  dims, "float")
     datain1@_FillValue = undef2
     datain2@_FillValue = undef2
     datain1 = fin1->$variables(iv)$
     datain2 = fin2->$variables(iv)$

;;  make the anomaly for plotting
     
     datain =  new(  dims, "float")
     datain@_FillValue = undef2

     datain!0="lat"
     datain!1="lon"
     datain&lat = lat
     datain&lon = lon
     
    datain = ff *( datain1  - datain2) 
     

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

 res@cnMinLevelValF       = cmin( n, iv)
 res@cnMaxLevelValF       = cmax( n, iv)
 res@cnLevelSpacingF      = cint( n, iv)

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
    label4 = "  Months/Season= " + season + "  " +  "units:" +  units

     gsn_text_ndc (wks, label4, xs1, ys1, txres2)
;;;;;    
	plot = gsn_csm_contour_map(wks, datain, res)

;;  frame(wks)      
   
  end do  ;  over variables

  end do  ;  over modes
end
