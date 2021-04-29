;;*******************************************************
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

;; select the  cmin, cmax, cint
   cmin = (/  -2.8,  -2.4, -22.5, -18,  -12 /) ; min(datain)
   cmax = (/   2.8,   2.4,  22.5,  18,   12 /) ; max(datain)
   cint = (/   0.4,   0.4,  2.5,    2,    2 /)
   ccenter = 0


   variables2 = (/ "pr" , "sw", "lw", "hfls", "hfss" /)
   variables = (/ "PR" , "SW", "LW", "LHF", "SHF" /)
   varinames = (/ "PRECIP" , "SW~B~net~N", "LW~B~net~N", "LHF", "SHF" /)
   varunits =  (/ "[mm/day]/[deg. C]", "[W/m2]/[deg. C]", "[W/m2]/[deg. C]", "[W/m2]/[deg. C]", "[W/m2]/[deg. C]"  /)


;;  read  in the data 

      obsdir  = getenv("OBS_DATA") +"/DATA/"
      outdir2   = getenv("ENSO_MSE_WKDIR")+"/obs/"  
      outdir   = getenv("ENSO_MSE_WKDIR_COMPOSITE")+"/obs/"  ; set in ENSO_MSE.py
      varcode  = getenv("POD_HOME")
      model =  " "   ;;;;   leave blank for observations  getenv( "CASENAME")

      parameter_name = varcode + "/shared/parameters.txt"

      nameclima = obsdir +  "/netCDF/"
      namein  = obsdir + "/netCDF/"  

       nameout2 = outdir2 + "/PS/regression" 

      maintitle = "NINO3.4 SST on "

      season = "XXX"
      undef2 = 1.1E+20

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(12), 3," ")

       xlon1 = 0
       xlon2 = 360
       xcenter  = (xlon1 + xlon2)/2

;;;   read in various variables then  plot 
;;   
    do iv = 0, 4

    variable = variables(iv) ;;;;    
    variable2 = variables2(iv)
    units2 = varunits(iv)

     colormap = "BlueWhiteOrangeRed" 
;;  the title 

   namein1 = namein + "/REGRESS_" + variable2 + ".nc"  

   nameout12 = nameout2 + "_" + variable 

     fin1 = addfile( namein1, "r")

     lon = fin1->lon
     lat = fin1->lat

     xmax = dimsizes( lon)
     ymax = dimsizes( lat)
     dims = (/  ymax, xmax /)

     dims = (/  ymax, xmax /)
     datain1 =  new(  dims, "float")
     datain1@_FillValue = undef2
     datain1 = fin1->$variable2$

    datain1@units = " "
    datain1@long_name = " "

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

;  symMinMaxPlt ( datain1, clevs, False,res)  
 res@cnMinLevelValF        = cmin(iv)
 res@cnMaxLevelValF        = cmax(iv)
 res@cnLevelSpacingF       = cint(iv)

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
      dx2 = 0.8
      label2 = maintitle + " " +  varinames(iv)
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 =  "(" + season + ")"
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

     label4 = "Months/Season= " +  season +   " units:" + units2
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)

	plot = gsn_csm_contour_map(wks, datain1, res)

  end do  ;  over variables
end
