;;;*******************************************************
;
;
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin 
 
   ff = 2.6E+06
   factor  = 1./ff

      dyy = 0.4
;;  read  in the data from MSE_VAR
	
	modes =  (/ "ELNINO" , "LANINA" /)
       title_modes = (/ "El Nino", "La Nina" /)

       varcode  = getenv("POD_HOME")
       vardata  = getenv("ENSO_MSE_WKDIR_MSE_VAR")
       outdir   = getenv("ENSO_MSE_WKDIR")

       model = getenv( "CASENAME")

;       varcode = "/export/oat/hafner/gyoji7/VARIOUS/HANA/MSE_SRC/PYTHON/MDTF_2021-07-06/diagnostics/ENSO_MSE/"
;      vardata = "/export/oat/hafner/gyoji7/VARIOUS/HANA/MSE_SRC/PYTHON/MDTF_2021-07-06/wkdir/MDTF_CESM2_1950_2005.v1/ENSO_MSE/MSE_VAR/"
;      outdir = "/export/oat/hafner/gyoji7/VARIOUS/HANA/MSE_SRC/PYTHON/MDTF_2021-07-06/wkdir/MDTF_CESM2_1950_2005.v1/ENSO_MSE/"
;      model = "CESM2"

      Varname = "output"

      parameter_name = varcode + "/shared/parameters.txt"

	season = "XXX"

      undef2 = 1.1E+20

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(10), 3," ")

      domain = (/ "Central Pacific", "Eastern Pacific" /)
      tlabels = (/ "MSE~B~vert. advect.~N", "M~B~adv~N",  "T~B~adv~N" , "SW~B~net~N", \ 
                    "LW~B~net~N", "THF~B~net~N" /)

      do n = 0, 1
	mode =  modes(n) ;;
	
       namein1 =   vardata + "/model/netCDF/" +  mode +  "/MSE_variance_C.nc"
       namein2 =   vardata + "/model/netCDF/" +  mode +  "/MSE_variance_E.nc"

      nameout = outdir + "/model/PS/MSE_VAR_comp_" + mode
;;;     read in the data from netCDF files

       fin1 = addfile(   namein1, "r")
       datain1 = fin1->$Varname$ 
       ydim = dimsizes( datain1)  

       datain1(0) =  factor * datain1(0)

        data2       = new( (/  ydim-2 /), float) 
        data2(0)    =  datain1(1)/datain1(0)     ;;  omse
        data2(1)    =  datain1(2)/datain1(0)     ;;  moist adv. 
        data2(2)    =  datain1(3)/datain1(0)     ;;  temp adv.
        data2(3)    =  datain1(4)/datain1(0)      ;;   SW
        data2(4)    =  datain1(5)/datain1(0)      ;;   Lw  
        data2(5)    =  (datain1(6)+datain1(7))/datain1(0) ;; THF

        fin2 = addfile(   namein2, "r")
        datain2 = fin2->$Varname$ 

        datain2(0) = factor * datain2(0) 

        data22       = new( (/  ydim-2 /), float) 
        data22(0)    =  datain2(1)/datain2(0)     ;;  omse
        data22(1)    =  datain2(2)/datain2(0)     ;;  moist adv.
        data22(2)    =  datain2(3)/datain2(0)     ;;  temp adv.
        data22(3)    =  datain2(4)/datain2(0)      ;;   SW
        data22(4)    =  datain2(5)/datain2(0)      ;;   Lw
        data22(5)    = (datain2(6)+datain2(7))/datain2(0) ;; THF

;;     find the data2 and data22   max/min  for plotting
     
       ymin2 =  9999.
	ymax2 = -9999.
	do i =  0, 5 
	  xx =  max( data2(i))
         if( xx .ge. ymax2)  then
          ymax2 = xx
         end if 
	  yy =  min( data2(i))
         if( yy .le. ymin2)  then
          ymin2 = yy
         end if
	end do
	 do i =  0, 5 
         xx=  max( data22(i))
         if( xx .ge. ymax2)  then
          ymax2 = xx
         end if 
         yy =  min( data22(i))
         if( yy .le. ymin2)  then
          ymin2 = yy
         end if
       end do
        ymax2 = ymax2 + 4.*dyy
        ymin2 = ymin2 - dyy

;======================================================================================	
   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout)
   wks_type@wkOrientation = "portrait"

   gsn_define_colormap(wks, "grads_default")


;;; controling paramters
     width=  0.25 ;   width of the bars 
     nxl =  ydim - 2
     xl1 = 0.72 + 0.25
     xl2 = nxl - 1 + xl1
     ndim1 = 0 
     ndim2 = ydim -2 -1 ; dimensions to display 

     sres = True
     sres@tmYLMode   = "Automatic" ;;; 
     sres@vpWidthF = 0.8 ;; 
     sres@vpHeightF = 0.5
     sres@vpXF = 0.10 ;; 
     sres@vpYF = 0.8

     sres@trXMinF = 0
     sres@trXMaxF = ydim - 1
     sres@trYMinF = ymin2 ;;;
     sres@trYMaxF = ymax2 ;;;
     sres@gsnDraw = True
     sres@gsnFrame = False

     sres@gsnXYBarChart = True
     sres@gsnYRefLine      = 0. ; reference line  
     sres@gsnPaperOrientation = "portrait" 

     sres@tmXBValues = ispan( 1, ydim-2, 1 )

     sres@gsnXYBarChartBarWidth = width           ; change bar widths

     sres@tmXBMode      =   "Explicit"         ; explicit labels
     sres@txFuncCode = "~"
     sres@tmXBLabelFuncCode  = "~"

     sres@tmXBLabels = tlabels ;
     sres@tmXBLabelFontHeightF = 0.018  ;;  
     sres@tmXTLabelFontHeightF = 0.018  ;;  
     sres@tmYLLabelFontHeightF = 0.015  ;;
     sres@tiMainFontHeightF = 0.025
     sres@tiMainFont = "helvetica"
     sres@gsnRightString = ""

;;;    Central 
     sres@gsnXYBarChartColors = (/"red"/)
     xl1 = xl1  ;
     xl2 = xl2  ; 
     nxl =  nxl ; 
     plot1 = gsn_csm_xy(wks,fspan(xl1, xl2, nxl), data2(ndim1:ndim2),sres)	

;;;;  Eastern 
     sres@gsnXYBarChartColors = (/"blue"/)
     xl1 = xl1  + width;
     xl2 = xl2  + width ;
     nxl =  nxl ;
     plot1 = gsn_csm_xy(wks,fspan(xl1, xl2, nxl), data22(ndim1:ndim2),sres)

;;;; 
     xlb1 = 0.60 ;;
     ylb1 = 0.8 ;; 
     nbox = 2
     lbres                    = True          ; labelbar only resources
     lbres@txFuncCode    = "~"
     lbres@vpWidthF           = 0.25           ; labelbar width
     lbres@vpHeightF          = 0.12           ; labelbar height
     lbres@lbBoxMajorExtentF  = 0.35 ;;        ; puts space between color boxes
     lbres@lbMonoFillPattern  = True          ; Solid fill pattern
     lbres@lbLabelFontHeightF = 0.015         ; font height. default is small
     lbres@lbLabelJust        = "CenterLeft"  ; left justify labels
     lbres@lbPerimOn          = False
     lbres@lgPerimColor      = "white"
     lbres@lbFillColors       = (/"red" , "blue" /)
     labels = domain    ;;;
     gsn_labelbar_ndc(wks, nbox, labels, xlb1, ylb1, lbres)    ; draw right labelbar column

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;  title separate as two texts on the top
      txres1 = True
      txres1@txFontColor =  "black"
      txres1@txFont   = "helvetica"
      txres1@txFontHeightF = 0.025
      txres1@txJust        = "CenterLeft"
      txres1@txFuncCode    = "~"
      xs1 = 0.08
      ys1 = 0.85 ;;  0.95 ;;  0.90
      dy2 = 0.0
      dx2 = 0.65
      label2 = "MSE variance"
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

      label1 =  "Months/Season= " + season +  "   Model:" +   model 
     xs1 = 0.1
     ys1 = 0.15 ;;  
     dy2 = 0.0
     dx2 = 0.3
     gsn_text_ndc (wks, label1, xs1, ys1, txres2)

;;;
    label2 = "relative units"
     xs1 = 0.8
     ys1 = ys1 ;; 0.05

;;;
   
     frame(wks)      

     delete([/ data22, data2 /])

      end do
end
