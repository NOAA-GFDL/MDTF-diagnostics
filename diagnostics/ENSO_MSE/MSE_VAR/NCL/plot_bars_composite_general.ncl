;;;*******************************************************
;
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin 

     ff = 2.6E+06
     factor  = 1./ff
;;;   get in the general  custom selectable domain lat/lons

;;      composite_dir_data  = getenv("ENSO_MSE_WKDIR_COMPOSITE")+"/model/netCDF/DATA/"

       slon1 = tofloat( getenv("slon1"))
       slon2 = tofloat( getenv("slon2"))
       slat1 = tofloat( getenv("slat1"))
       slat2 = tofloat( getenv("slat2"))

       varcode  = getenv("POD_HOME")
       vardata  = getenv("ENSO_MSE_WKDIR_MSE_VAR")
       outdir   = getenv("ENSO_MSE_WKDIR")
     
       model = getenv( "CASENAME")

;;       varcode = "/export/oat/hafner/gyoji7/VARIOUS/HANA/MSE_SRC/PYTHON/MDTF_2021-07-06/diagnostics/ENSO_MSE/"
;;      vardata = "/export/oat/hafner/gyoji7/VARIOUS/HANA/MSE_SRC/PYTHON/MDTF_2021-07-06/wkdir/MDTF_CESM2_1950_2005.v1/ENSO_MSE/MSE_VAR/"
;;      outdir = "/export/oat/hafner/gyoji7/VARIOUS/HANA/MSE_SRC/PYTHON/MDTF_2021-07-06/wkdir/MDTF_CESM2_1950_2005.v1/ENSO_MSE/"
;;      model = "CESM2"
 
      slon1 = 160.
      slon2 = 200.
      slat1 = -10.
      slat2 =   5.

      Varname = "output"

      parameter_name = varcode + "/shared/parameters.txt"
      datamode = "Anomaly"
       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(10), 3," ")

;;  read  in the data from MSE_VAR
	
	modes =  (/ "ELNINO" , "LANINA" /)
       title_modes = (/ "El Nino", "La Nina" /)

      tlabels = (/ "MSE~B~vert. advect.~N", "M~B~adv~N",  "T~B~adv~N" , "SW~B~net~N", \
                   "LW~B~net~N", "THF~B~net~N" /)

      do n = 0, 1
	mode =  modes(n) ;;
	
       namein1 =   vardata + "/model/netCDF/" +  mode +  "/MSE_variance_general.nc"

       nameout = outdir + "/model/PS/MSE_VAR_comp_general_" + mode

;;;  construct the main title based on model, season and region
       fin1 = addfile(   namein1, "r")
       datain = fin1->$Varname$
       ydim = dimsizes( datain)

       datain(0) = factor * datain(0) 

        data2       = new( (/  ydim-2 /), float) 
        data2(0)    =  datain(1)/datain(0)     ;;  omse
        data2(1)    =  datain(2)/datain(0)     ;;  moist adv. 
        data2(2)    =  datain(3)/datain(0)     ;;  temp adv.
        data2(3)    =  datain(4)/datain(0)      ;;   SW
        data2(4)    =  datain(5)/datain(0)      ;;   Lw  
        data2(5)    = (datain(6)+datain(7))/datain(0) ;; THF

;======================================================================================	
   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout)
   wks_type@wkOrientation = "portrait" ;; "landscape"

   gsn_define_colormap(wks, "grads_default")

;;; controling paramters
     width=  0.25 ;   width of the bars 
     nxl =  ydim - 2
     xl1 = 0.72 + 0.25
     xl2 = nxl - 1 + xl1
     ndim1 = 0 
     ndim2 = ydim -2 -1 ; dimensions to display 

     sres = True
     sres@tmYLMode   = "Automatic" ;;  
     sres@vpWidthF = 0.8 ;; 
     sres@vpHeightF = 0.5
     sres@vpXF = 0.10 ;; 
     sres@vpYF = 0.8

     sres@trXMinF = 0
     sres@trXMaxF = ydim - 1
     sres@gsnFrame = False

     sres@gsnXYBarChart = True
     sres@gsnYRefLine           = 0. ; reference line  
     sres@gsnPaperOrientation = "portrait"

      sres@tmXBValues = ispan( 1, ydim-2, 1 )

     sres@gsnXYBarChartBarWidth = width           ; change bar widths

     sres@tmXBMode          =   "Explicit"         ; explicit labels
   
     sres@txFuncCode    = "~"
     sres@tmXBLabelFuncCode  = "~"
     sres@tmXBLabels = tlabels ;
     sres@tmXBLabelFontHeightF = 0.018 ;; 
     sres@tmXTLabelFontHeightF = 0.018 ;;  
     sres@tmYLLabelFontHeightF = 0.015   ;; 
     sres@tiMainFontHeightF = 0.025
     sres@tiMainFont = "helvetica"
;;;    
     sres@gsnXYBarChartColors = (/"blue"/)
     xl1 = xl1  ;
     xl2 = xl2  ; 
     nxl =  nxl ; 
     plot1 = gsn_csm_xy(wks,fspan(xl1, xl2, nxl), data2(ndim1:ndim2),sres)	
;;;; 
     xlb1 = 0.72
     ylb1 = 0.35
     nbox = 1
     lbres                    = True          ; labelbar only resources
     lbres@vpWidthF           = 0.25           ; labelbar width
     lbres@vpHeightF          = 0.12           ; labelbar height
     lbres@lbBoxMajorExtentF  = 0.35 ;;        ; puts space between color boxes
     lbres@lbMonoFillPattern  = True          ; Solid fill pattern
     lbres@lbLabelFontHeightF = 0.015         ; font height. default is small
     lbres@lbLabelJust        = "CenterLeft"  ; left justify labels
     lbres@lbPerimOn          = False
     lbres@lgPerimColor      = "white"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;  title separate as two texts on the top
      txres1 = True
      txres1@txFontColor =  "black"
      txres1@txFont   = "helvetica"
      txres1@txFontHeightF = 0.025
      txres1@txJust        = "CenterLeft"
      txres1@txFuncCode    = "~"
      xs1 = 0.08
      ys1 = 0.85 ;; 
      dy2 = 0.0
      dx2 = 0.65
      label2 = "MSE variance    User Selected Domain"
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

      label2 = title_modes(n) + "  (" + season + ")"
      xs1 = xs1 + dx2
      gsn_text_ndc (wks, label2, xs1, ys1, txres1)

;;;   to write the summary - model season  etc. 

      txres2 = True
      txres2@txFuncCode    = "~"
      txres2@txFontColor =  "black"
      txres2@txFont   = "helvetica"
      txres2@txFontHeightF = 0.016
      txres2@txJust        = "CenterLeft"

     label1 = "Months/Season= " + season +  "   Model:" +   model
     xs1 = 0.1
     ys1 = 0.12
     dy2 = 0.0
     dx2 = 0.3
     gsn_text_ndc (wks, label1, xs1, ys1, txres2)

;;;
;;    the domain is the next
     txres2@txFontHeightF = 0.016
      dy2 = -0.03

    if ( (slat1 .lt. 0.) .and. (slat2 .gt. 0.) )  then
    sslat1 = -slat1
   region2 = slon1 + "~F34~0~F~E " + slon2 + "~F34~0~F~E  " + sslat1 + "~F34~0~F~S " + slat2 + "~F34~0~F~N"
    end if
    if ( (slat1 .lt. 0.) .and. (slat2 .lt. 0.) )  then
    sslat1 = -slat1
    sslat2 = -slat2
    region2 = slon1 + "~F34~0~F~E " + slon2 + "~F34~0~F~E  " + sslat1 + "~F34~0~F~S " + sslat2 + "~F34~0~F~S"
    end if
     if ( (slat1 .ge. 0.) .and. (slat2 .ge. 0.) )  then
   region2 = slon1 + "~F34~0~F~E " + slon2 + "~F34~0~F~E  " + slat1 + "~F34~0~F~N " + slat2 + "~F34~0~F`N"
    end if

      label4 = "User Selected Domain = " + region2

       xs4 = xs1 
       ys4 = ys1 + dy2
       gsn_text_ndc (wks, label4, xs4, ys4, txres2)
 
     frame(wks)      

     delete( data2 )
      end do
end
