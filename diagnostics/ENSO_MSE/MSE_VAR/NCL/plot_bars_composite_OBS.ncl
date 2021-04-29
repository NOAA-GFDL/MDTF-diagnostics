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

begin 
      
      ff = 2.6E+06
      factor  = 1./ff
;;;; 
     dyy = 0.4
;;  read  in the data from MSE_VAR
	
	modes =  (/ "ELNINO" , "LANINA" /)
       title_modes = (/ "El Nino", "La Nina" /)

      composite_dir_data  = getenv("ENSO_MSE_WKDIR_COMPOSITE")+"/obs/netCDF/DATA/"
      varcode  = getenv("POD_HOME")
      model =  "  " ;   leave  blank for OBS 

      parameter_name = varcode + "/shared/parameters.txt"
      season = "XXX"

      lon1 = -9999.
      lon2 = -9999.
      lat1 = -9999.
      lat2 = -9999.
      undef2 = 1.1E+20

       data  = asciiread(parameter_name,-1,"string")
       season = str_get_field(data(12), 3," ")

      domain = (/ "Central Pacific", "Eastern Pacific" /)
      tlabels = (/ "MSE~B~vert. advect.~N", "M~B~adv~N",  "T~B~adv~N" , "SW~B~net~N", \ 
                    "LW~B~net~N", "THF~B~net~N" /)
;      tlabels = (/ "MSE:B:vert. advect.:N", "M:B:adv:N",  "T:B:adv:N" , "SW:B:net:N", \
;                    "LW:B:net:N", "THF:B:net:N" /)


      do n = 0, 1
	mode =  modes(n) ;;
	
       namein1 =  getenv("ENSO_MSE_WKDIR_MSE_VAR")+"/obs/netCDF/" +  mode +  "/MSE_variance_C.out"
       namein2 =  getenv("ENSO_MSE_WKDIR_MSE_VAR")+"/obs/netCDF/" +  mode +  "/MSE_variance_E.out"

       
;;       nameout = getenv("ENSO_MSE_WKDIR_MSE_VAR")+"/obs/PS/MSE_VAR_comp_" + mode
         nameout = getenv("ENSO_MSE_WKDIR")+"/obs/PS/MSE_VAR_comp_" + mode
;;;      maintitle = "MSE variance budget " + title_modes(n)
;;;  construct the main title based on model, season and region
;;;       maintitle2 = maintitle + " " + season

       ydim = 8
       dims = ( [ydim] ) 
       datain1  = fbindirread (namein1, 0, dims , "float")
       datain1(0) = factor * datain1(0)

        data2       = new( (/  ydim-2 /), float) 
        data2(0)    =  datain1(1)/datain1(0)     ;;  omse
        data2(1)    =  datain1(2)/datain1(0)     ;;  moist adv. 
        data2(2)    =  datain1(3)/datain1(0)     ;;  temp adv.
        data2(3)    =  datain1(4)/datain1(0)      ;;   SW
        data2(4)    =  datain1(5)/datain1(0)      ;;   Lw  
        data2(5)    = (datain1(6)+datain1(7))/datain1(0) ;; THF

	 datain2  = fbindirread (namein2, 0, dims , "float")
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
	
;;    print (datain)
;;    print( data2)


;======================================================================================	
;;   wks_type = "png"
;;   wks_type@wkWidth = 1000
;;   wks_type@wkHeight = 1000
   wks_type = "eps"
   wks = gsn_open_wks( wks_type, nameout)
   wks_type@wkOrientation = "portrait" 

;;   wks = gsn_open_wks ("X11", "scatter")
   gsn_define_colormap(wks, "grads_default")


;;; controling paramters
     width=  0.25 ;   width of the bars 
     nxl =  ydim - 2
     xl1 = 0.72 + 0.25
     xl2 = nxl - 1 + xl1
     ndim1 = 0 
     ndim2 = ydim -2 -1 ; dimensions to display 

     sres = True
     sres@tmYLMode   = "Automatic" ;;; "Automatic" ;;   "Manual"
     sres@vpWidthF = 0.8 ;;  0.9
     sres@vpHeightF = 0.5
     sres@vpXF = 0.10
     sres@vpYF = 0.8

     sres@trXMinF = 0
     sres@trXMaxF = ydim - 1
     sres@trYMinF = ymin2 ;;; ymin2(n)
     sres@trYMaxF = ymax2 ;;; ymax2(n)
     sres@gsnDraw = True
     sres@gsnFrame = False
;;;    manual labels 
;;      sres@tmYLMode          = "Manual"
;;      sres@tmYLTickEndF      = sres@trYMaxF
;;      sres@tmYLTickStartF    = sres@trYMinF

     sres@gsnXYBarChart = True
     sres@gsnYRefLine           = 0. ; reference line  
     sres@gsnPaperOrientation = "portrait"
;;     sres@gsnMaximize      = True      

      sres@tmXBValues = ispan( 1, ydim-2, 1 )

     sres@gsnXYBarChartBarWidth = width           ; change bar widths

     sres@tmXBMode          =   "Explicit"         ; explicit labels

     sres@txFuncCode    = "~"
     sres@tmXBLabelFuncCode  = "~"

     sres@tmXBLabels = tlabels ;
     sres@tmXBLabelFontHeightF = 0.018
     sres@tmXTLabelFontHeightF = 0.018   ;; 0.0205
     sres@tmYLLabelFontHeightF = 0.015   ;;  0.0225
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
     xlb1 = 0.60 ;;   0.74
     ylb1 = 0.8 ;;; 0.35
     nbox = 2
     lbres                    = True          ; labelbar only resources
     lbres@txFuncCode    = "~"
     lbres@vpWidthF           = 0.25           ; labelbar width
     lbres@vpHeightF          = 0.12           ; labelbar height
     lbres@lbBoxMajorExtentF  = 0.35          ; puts space between color boxes
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
      ys1 = 0.85
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

      label1 =  "Months/Season= " + season +  "   " +   model 
;;     new_label1 = str_concat(label1)
     xs1 = 0.1
     ys1 = 0.15
     dy2 = 0.0
     dx2 = 0.3
     gsn_text_ndc (wks, label1, xs1, ys1, txres2)

;;; add the text of scaling
     label2 = "relative units"
     xs1 = 0.8
     ys1 = ys1 ;;  0.05
;;;     gsn_text_ndc (wks, label2, xs1, ys1, txres2)

;;;
   
     frame(wks)      

      end do
end
