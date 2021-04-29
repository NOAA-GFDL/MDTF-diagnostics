;;;*******************************************************
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
   cmin = -1.0 ;; -1.2 ; min(datain)
   cmax =  1.0 ;;  1.2 ; max(datain)
   cint = 0.1
   ccenter = 0
   clevs = 20

   variables2 = (/ "PR" , "SW", "LW", "LHF", "SHF" /)
   variables = (/ "pr",  "sw", "lw", "hfls", "hfss" /)
   varinames = (/ "PRECIP" , "SW~B~net~N", "LW~B~net~N", "LHF", "SHF" /)

;;  read  in the data 

      obsdir  = getenv("OBS_DATA") +"/DATA/"
      outdir2   = getenv("ENSO_MSE_WKDIR")+"/obs/"
      outdir   = getenv("ENSO_MSE_WKDIR_COMPOSITE")+"/obs/"  ; set in ENSO_MSE.py
      varcode  = getenv("POD_HOME")
      model =  " "   ;;;;   leave blank for observations  getenv( "CASENAME")

      parameter_name = varcode + "/shared/parameters.txt"

      nameclima = obsdir +  "/netCDF/"
      namein  = obsdir + "/netCDF/"  

       nameout = outdir2 + "/PS/correlation" 

       maintitle = "NINO3.4 SST vs "  

      season = "XXX"
      undef2 = 1.1E+20

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(12), 3," ")

       xlon1 = 0
       xlon2 = 360
       xcenter  = (xlon1 + xlon2)/2

;;   
    do iv = 0, 4

    variable = variables(iv) ;;;;    

     colormap = "BlueWhiteOrangeRed" 
;;  the title 

   namein1 = namein + "/CORR_" + variable + ".nc"  

   nameout12 = nameout + "_" + variables2(iv) 
;;   read in the data
     fin1 = addfile( namein1, "r")

     lon = fin1->lon
     lat = fin1->lat

     xmax = dimsizes( lon)
     ymax = dimsizes( lat)
     dims = (/  ymax, xmax /)

     dims = (/  ymax, xmax /)
     datain1 =  new(  dims, "float")
     datain1@_FillValue = undef2
     datain1 = fin1->$variable$

    datain1@units = " "
    datain1@long_name = " "

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
 res@cnLevelSelectionMode  = "ManualLevels"

  res@cnFillOn             = True                  ; turn on color fill
  res@cnLinesOn            = False

 res@cnMinLevelValF        = cmin
 res@cnMaxLevelValF        = cmax
 res@cnLevelSpacingF       = cint

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

     xs1 = 0.1
     ys1 = 0.18
     dy2 = 0.0
     dx2 = 0.3

     label4 = "Months/Season= " +  season 

     gsn_text_ndc (wks, label4, xs1, ys1, txres2)
;;;;;    

	plot = gsn_csm_contour_map(wks, datain1, res)

;;  frame(wks)      

  end do  ;  over variables
end
