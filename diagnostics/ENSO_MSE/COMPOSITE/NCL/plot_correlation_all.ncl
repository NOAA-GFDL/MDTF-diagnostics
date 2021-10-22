;;*******************************************************
;*******************************************************
;

begin 

;; select the  cmin, cmax, cint
   cmin = -1.0 ;; 
   cmax =  1.0 ;; 
   cint = 0.1
   ccenter = 0
   clevs = 20

   variables2 = (/ "PR" , "SW", "LW", "LHF", "SHF" /)
   variables = (/  "pr" , "sw", "lw", "hfls", "hfss" /)
   varinames = (/ "PRECIP" , "SW~B~net~N", "LW~B~net~N", "LHF", "SHF" /)

;;  read  in the data 
     varcode  = getenv("POD_HOME")
     outdir  = getenv("ENSO_MSE_WKDIR")+"/model/"
     outdir2  = getenv("ENSO_MSE_WKDIR_COMPOSITE") +"/model"     
     model    = getenv( "CASENAME")


      parameter_name = varcode + "/shared/parameters.txt"
      nameclima = outdir2 +  "/netCDF/"

        namein  = outdir2 + "/netCDF/"  
        nameout = outdir +  "/PS/correlation" 

       maintitle = "NINO3.4 SST vs "  

      undef2 = 1.1E+20

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(10), 3," ")

       tt0 = 0 
       xlon1 = 0
       xlon2 = 360
       xcenter  = (xlon1 + xlon2)/2

;;;   read in various variables then  plot 
;;   
    do iv = 0, 4

    variable = variables(iv) ;;;;    
    variable2 = variables2(iv) 
     colormap = "BlueWhiteOrangeRed" ;;   "BlWhRe"  ;;   "BlRe"
;;  the title 

   namein1 = namein + "/CORR_" + variable + ".nc"  ;;  str_concat( string)
   nameout12 = nameout + "_" + variable2
;;   read in the data
      fin = addfile( namein1, "r")
	
      lat = fin->lat
      lon = fin->lon
      xmax = dimsizes( lon)
      ymax = dimsizes( lat)
      dims = (/  ymax, xmax /)

      datain = fin->$variable$

      datain@units = " "
      datain@long_name = " "

;;  


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
      txres2@txFuncCode    = "~"

     xs1 = 0.1
     ys1 = 0.18
     dy2 = 0.0
     dx2 = 0.3

     label4 = "Months/Season= " +  season +  " Model: " + model + " " 

;;;;;;;;;;  
     gsn_text_ndc (wks, label4, xs1, ys1, txres2)
;;;;;    

	plot = gsn_csm_contour_map(wks, datain, res)


  end do  ;  over variables
end
