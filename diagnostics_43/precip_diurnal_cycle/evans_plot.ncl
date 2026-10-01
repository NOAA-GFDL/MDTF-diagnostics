; This file is part of the precip_diurnal_cycle module of the MDTF code package (see LICENSE.txt)

;
; This series of "Evans" plots were created by Jason Evans, a
; senior research fellow at the Climate Change Research Center,
; University of New South Wales, Sydney, Australia.
;
; This is the generic template for creating color wheel map plots (with
; or without wind vectors)
;
; gsn_code.ncl, gsn_csm.ncl and contributed.ncl must be loaded first
; by the main calling program.
;

undef("evans_plot_color_map")
undef("add_color_wheel")
undef("add_ep_label_bar")
undef("evans_plot_map")
undef("evans_plot_vector_map")

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

;**********************************************************************;
; Function : evans_plot_color_map
;		nHues: integer
;		nSats: integer
;               hueoffset : float
;               minval : float
;
; This function determines the color to use with with an Evans plot
;
;**********************************************************************;

function evans_plot_color_map(nHues:numeric,nSats:numeric,hueoffset:numeric, \
                               minval:numeric)

local hue,sat,val,i

begin
 hue = new(nHues*nSats,float)
 sat = hue
 val = hue
 
 do i = 0,nHues-1
   if (nSats.gt.5) then
     sat((i+1)*nSats-4:(i+1)*nSats-1) = fspan(1.,1.,4)     ; set saturation to 1.
     sat(i*nSats:(i+1)*nSats-4) = fspan(0.,1.,nSats-3)     ; set saturation to range from 0. to 1.
   else
     sat(i*nSats:(i+1)*nSats-1) = fspan(0.,1.,nSats)	; set saturation to range from 0. to 1.
   end if
 end do
 do i = 0,nSats*(nHues-1),nSats
   hue(i:i+nSats-1) = 360.*i/(nHues*nSats)     ; Set hue to range from 0 to 360
 end do
 do i = 0,nHues-1
   if (nSats.gt.5) then
     val((i+1)*nSats-4:(i+1)*nSats-1) = fspan(1.,0.6,4)         ; value range 1.0 to 0.5
     val((i*nSats):(i+1)*nSats-4) = fspan(minval,1.,nSats-3)         ; value range minval to 1.0.
   else
     val((i*nSats):(i+1)*nSats-1) = fspan(minval,1.,nSats)         ; value range minval to 1.0.
   end if
 end do

 ;add hueoffset
 hue = hue + hueoffset
 do i = 0,nHues*nSats-1
   if (hue(i).gt.360) then
     hue(i) = hue(i) - 360.
   end if
 end do

 cmap  = new((/(nHues*nSats)+2,3/),float)   

 cmap(0,:)    = (/1.,1.,1./)   ; Set the background to white.
 cmap(1,:)    = (/0.,0.,0./)   ; Set the foreground to black.

 cmap(2:,:) = hsv2rgb(hue,sat,val) ; Generate smooth range of RGB values.
 
 return(cmap)
 
end


;**********************************************************************;
; Procedure : add_color_wheel
;		wks: workstation object
;		nHues: numeric
;		nSats: numeric
;		title: string
;		huelabel: numeric
;		satlevels: numeric
;               scale : numeric
;               cx : numeric
;               cy : numeric
;               perim : logical
;
; This function draws an actual colorwheel in the top right hand corner
; of the plot. It also adds labels for the colors and a magnitude vector 
; for the saturation values.
; 
;**********************************************************************;

procedure add_color_wheel(wks:graphic,nHues:numeric,nSats:numeric, \
				title:string,huelabel:numeric,satlevels:numeric, \
				scale:numeric,cx:numeric,cy:numeric, \
				perim:logical)

local i,pi,x,y,cx,cy,ploy_res,text_res,rinc,hue,ihue,\
	theta1,theta2,rlen,isat,xndc,yndc,xline,yline,ex,ey,cmap

begin
   ;add perimeter
   poly_res = True
   if (perim) then
     poly_res@gsFillColor = 0.
     poly_res@gsEdgesOn = True
     xndc = new(5,float)
     yndc = xndc
     xndc(0) = cx - 0.155*scale
     xndc(1) = xndc(0)
     xndc(2) = cx + 0.155*scale
     xndc(3) = xndc(2)
     xndc(4) = xndc(0)
     yndc(0) = cy - 0.19*scale
     yndc(1) = cy + 0.16*scale
     yndc(2) = yndc(1)
     yndc(3) = yndc(0)
     yndc(4) = yndc(0)
     
     gsn_polygon_ndc(wks,xndc,yndc,poly_res)
     delete(xndc)
     delete(yndc)
     delete(poly_res)     
   end if
   
   

 pi = acos(-1)
 
 cmap = gsn_retrieve_colormap(wks)
 
  x = new(4,float)
  y = new(4,float)
  
  
; Create variables to hold resource lists.
;
  poly_res = True
  text_res = True
  text_res@txFont = "helvetica"
  text_res@txFontHeightF = 0.025*scale

;
;  Loop on the values.
;
  rinc = 2 * pi/nHues
;
;  Loop on the hues.
;
    do ihue = 0,nHues-1
      theta1 = (ihue -.5) * rinc
      theta2 = (ihue +.5) * rinc
      x(0) = 0.0
      x(3) = 0.0
      y(0) = 0.0
      y(3) = 0.0
;
;  Loop on the saturation values.
;
      do isat = 1,nSats,1
        poly_res@gsFillColor = cmap((ihue*nSats)+isat+1,:)
        rlen = ((1.*isat)/(1.*nSats*3))*scale
;        x(1) = cos(theta1) * rlen
;        y(1) = sin(theta1) * rlen
;        x(2) = cos(theta2) * rlen
;        y(2) = sin(theta2) * rlen
        x(1) = sin(theta1) * rlen
        y(1) = cos(theta1) * rlen
        x(2) = sin(theta2) * rlen
        y(2) = cos(theta2) * rlen
        xndc = (cx-0.5)+((x + 1.4)/2.8)
        yndc = (cy-0.5)+((y + 1.4)/2.8)
        gsn_polygon_ndc(wks,xndc,yndc,poly_res)
        x(0) = x(1)
        x(3) = x(2)
        y(0) = y(1)
        y(3) = y(2)
	
	      ;get location of magnitude vector
      if (ihue.eq.0.and.isat.eq.nSats-1) then
        ex = ((((xndc(2)+xndc(1))/2)-cx)*(1-(1/nSats)))+cx
	ey = ((((yndc(2)+yndc(1))/2)-cy)*(1-(1/nSats)))+cy
      end if

      end do
      
      ;draw time stamps
      if (fabs(round(huelabel(ihue),0)-huelabel(ihue)).lt.0.1) then
        xline = (/(xndc(2)+xndc(1))/2,((((xndc(2)+xndc(1))/2)-cx)*1.1)+cx/)
        yline = (/(yndc(2)+yndc(1))/2,((((yndc(2)+yndc(1))/2)-cy)*1.1)+cy/)
        gsn_polyline_ndc(wks,xline,yline,False)
        gsn_text_ndc(wks,sprintf("%3.0f",huelabel(ihue)),2.*xline(1)-xline(0),2.*yline(1)-yline(0),text_res)
      end if
      
    end do

    ;ex and ey must be float so change them if they are double
    if (isdouble(ex)) then
      exd = ex
      delete(ex)
      ex = doubletofloat(exd)
      delete(exd)
    end if
    if (isdouble(ey)) then
      eyd = ey
      delete(ey)
      ey = doubletofloat(eyd)
      delete(eyd)
    end if


    ;draw magnitude vector (need to use the wmlabs stuff)
    wmsetp("ezf",-1)
    wmsetp("awc",1) ;arrow color
    wmsetp("aoc",1) ;outline color
    wmsetp("ard",90.) ;arrow direction
    wmsetp("ars",sqrt((ex-cx)^2 + (ey-cy)^2))  ;arrow length
    wmlabs(wks,ex,ey,"arrow")
    ;gsn_polyline_ndc(wks,(/cx,ex/),(/cy,ey/),False)
    text_res@txFontHeightF = 0.02*scale
    gsn_text_ndc(wks,min(satlevels),cx-(ey-cy)*0.25,cy-(ex-cx)*0.25,text_res)
    gsn_text_ndc(wks,max(satlevels),ex-(ey-cy)*0.25,ey-(ex-cx)*0.25,text_res)
 
 
   ;add title for color wheel
   text_res@txFontHeightF = 0.02*scale
   gsn_text_ndc(wks,title,cx,cy-0.17*scale,text_res)
   
   
 end



;**********************************************************************;
; Procedure : add_ep_label_bar
;		wks: workstation object
;		nHues: numeric
;		nSats: numeric
;		hue_units: string
;		hue_levels: numeric
;		sat_units: string
;		sat_levels: numeric
;
; This function draws a label bar in the plot. 
; It also adds labels for the colors and a magnitude vector 
; for the saturation values.
; 
;**********************************************************************;

procedure add_ep_label_bar(wks:graphic,nHues:numeric,nSats:numeric, \
				hue_units:string,hue_levels:numeric, \
				sat_units:string,sat_levels:numeric)

local i,xmin,xmax,ymin,ymax,ploy_res,text_res,hue,ihue,\
	theta1,theta2,rlen,isat,xndc,yndc,xline,yline,ex,ey,cmap, \
	xstep,ystep

begin
 
 cmap = gsn_retrieve_colormap(wks)
 
  xndc = new(4,float)
  yndc = new(4,float)
  
  xmin = 0.2
  xmax = 0.85
  ymin = 0.15
  ymax = 0.2

  
; Create variables to hold resource lists.
;
  poly_res = True
  
  text_res = True
   text_res@txFont = "helvetica"
   text_res@txFontHeightF = 0.018

  
;
;  Loop on the values.
;
  xstep = (xmax-xmin)/nHues
  ystep = (ymax-ymin)/nSats
;
;  Loop on the hues.
;
    do ihue = 0,nHues-1
      xndc(0) = xmin + xstep*ihue
      xndc(1) = xndc(0)
      xndc(2) = xmin + xstep*(ihue+1)
      xndc(3) = xndc(2)
;
;  Loop on the saturation values.
;
      do isat = 0,nSats-1
        poly_res@gsFillColor = cmap((ihue*nSats)+isat+2,:)
        yndc(0) = ymin + ystep*isat 
        yndc(1) = ymin + ystep*(isat+1)
        yndc(2) = yndc(1)
        yndc(3) = yndc(0)
        gsn_polygon_ndc(wks,xndc,yndc,poly_res)
      end do
      
      ;draw hue stamps
      if (ihue.gt.0) then
        xline = (/xndc(0),xndc(0)/)
        yline = (/ymax,ymin-0.01/)
        gsn_polyline_ndc(wks,xline,yline,False)
        gsn_text_ndc(wks,sprintf("%3.0f",hue_levels(ihue-1)),xline(0),yline(1)-0.02,text_res)
      end if
      
    end do


    ;draw magnitude vector (need to use the wmlabs stuff)
    wmsetp("ezf",-1)
    wmsetp("awc",1) ;arrow color
    wmsetp("aoc",1) ;outline color
    wmsetp("ard",90.)  ;arrow direction
    wmsetp("ars",ystep*(nSats-2))   ;arrow length
    wmlabs(wks,xmin-0.02,ymax-ystep,"arrow")
    ;gsn_polyline_ndc(wks,(/cx,ex/),(/cy,ey/),False)
    text_res@txFontHeightF = 0.015
    gsn_text_ndc(wks,min(sat_levels),xmin-0.05,ymin+ystep,text_res)
    gsn_text_ndc(wks,max(sat_levels),xmin-0.05,ymax-ystep,text_res)
 
    ;draw box around the label bar
    delete(poly_res@gsFillColor)
    poly_res@gsFillColor = -1
    poly_res@gsEdgesOn = True
    gsn_polygon_ndc(wks,(/xmin,xmin,xmax,xmax,xmin/),(/ymin,ymax,ymax,ymin,ymin/),poly_res)
 
   ;add units
    text_res@txFontHeightF = 0.02

   gsn_text_ndc(wks,hue_units,(xmax+xmin)/2.,ymin-0.06,text_res)
   gsn_text_ndc(wks,sat_units,xmin-0.1,(ymax+ymin)/2.,text_res)
   
 end



;**********************************************************************;
; Function : evans_plot_map
;		wks: workstation object
;		hue_data: 2D color data
;		sat_data: 2D saturation data
;		resources: optional resources
;
; This function creates a color/saturation raster map on the workstation
; "wks". "hue_data" is the 2D data to be mapped as color. "sat_data" is
; the data to be mapped as saturation. "resources" is a list of resources 
;
; Note that several resources apply specifically to this type of plot.
;
; epCyclic {logical} : is the hue variable cyclic? default is [True]
;
; epHueLabel {string} : [hue_data@units]
; epSatLabel {string} : [sat_data@units]
;
; epExplicitSatLevels {float[*]} : user set saturation levels
; epMaxSatLevel {float} : max saturation level
; epMinSatLevel {float} : min saturation level
; epSatLevelSpacing {float} : saturation level spacing
;
; epExplicitHueLevels {float[*]} : user set hue levels
; epMaxHueLevel {float} : max hue level
; epMinHueLevel {float} : min hue level
; epHueLevelSpacing {float} : hue level spacing
;
; epHueOffset {float} : make the first hue this many degrees around the
;                        color wheel from red (0-360) [0.]
; epMinIntensity {float} : minimum intensity to use (0-1) [0.8]
;
; epColorWheelScale {float} : change the size of the color wheel by
;                              multiplying by this scale factor [1.]
; epColorWheelCenterX {float} : center X of color wheel in ndc [0.85]
; epColorWheelCenterY {float} : center Y of color wheel in ndc [0.85]
; epColorWheelPerimOn {logical} : draw a box around the color wheel? [False]
;
;
; It uses gsn_csm_contour_map to plot so all the relevant resources also
; apply.
;
; 
;*************************************************************************;

function evans_plot_map(wks:graphic,hue_data[*][*]:numeric,\
				sat_data[*][*],resources:logical)
				
local i,dsize,mnmxint,nSats,minsat,maxsat,nHues,minhue,maxhue, \
      nHues,vmin,vmax,vstep,hue_data1d,sat_data1d,thishue,res, \
      	huelevels,satlevels,colunits,satunits,hueinds,satinds, \
	plotinds,plotvar1d,plotvar,plot_obj,dnames,huename,satname, \
	HueCyclic,satspace,dvar,hueoffset,minV,huemidlevels, \
	cwScale,cwX,cwY,cwPerim,framenow

begin

 res = get_resources(resources)
 
 dsize = dimsizes(hue_data)
 dnames = getvardims(hue_data)


 ;if dimensions weren't named then name them
 if (ismissing(dnames(0))) then
   dnames(0) = "lat"
   hue_data!0 = "lat"
   sat_data!0 = "lat"
 end if
 if (ismissing(dnames(1))) then
   dnames(1) = "lon"
   hue_data!1 = "lon"
   sat_data!1 = "lon"
 end if

 ;are the color and saturation datasets named?
 if (isatt(hue_data,"long_name")) then
   huename = hue_data@long_name
 else
   huename = ""
 end if
 if (isatt(sat_data,"long_name")) then
   satname = sat_data@long_name
 else
   satname = ""
 end if
 
 ;do they have units?
 if (isatt(res,"epHueLabel")) then
   hueunits = res@epHueLabel
   delete(res@epHueLabel)
 else
   if (isatt(hue_data,"units")) then
     hueunits = hue_data@units
   else
     hueunits = ""
   end if
 end if
 if (isatt(res,"epSatLabel")) then
   satunits = res@epSatLabel
   delete(res@epSatLabel)
 else
   if (isatt(sat_data,"units")) then
     satunits = sat_data@units
   else
     satunits = ""
   end if
 end if

 ;is there a hue offset?
 if (isatt(res,"epHueOffset")) then
   hueoffset = res@epHueOffset
   delete(res@epHueOffset)
 else
   hueoffset = 0.
 end if
 
 ;is there a minimum intensity
 if (isatt(res,"epMinIntensity")) then
   minV = res@epMinIntensity
   delete(res@epMinIntensity)
 else
   minV = 0.8
 end if
 
 if (isatt(res,"epColorWheelScale")) then
   cwScale = res@epColorWheelScale
   delete(res@epColorWheelScale)
 else
   cwScale = 1.
 end if
 
 if (isatt(res,"epColorWheelCenterX")) then
   cwX = res@epColorWheelCenterX
   delete(res@epColorWheelCenterX)
 else
   cwX = 0.85
 end if
 
 if (isatt(res,"epColorWheelCenterY")) then
   cwY = res@epColorWheelCenterY
   delete(res@epColorWheelCenterY)
 else
   cwY = 0.85
 end if
 
 if (isatt(res,"epColorWheelPerimOn")) then
   cwPerim = res@epColorWheelPerimOn
   delete(res@epColorWheelPerimOn)
 else
   cwPerim = False
 end if
 
 
 
 
 ;Initialize
 res@lbLabelBarOn = False
 res@cnRasterModeOn = True
 res@cnMissingValFillColor = 0
 res@gsnMaximize = False
 res@gsnSpreadColors = False
 res@cnInfoLabelOn = False
 res@cnLinesOn = False
 res@cnLineLabelsOn = False
 

 if (.not.isatt(res,"epCyclic")) then
   HueCyclic = True
 else
   HueCyclic = res@epCyclic
   delete(res@epCyclic)
 end if
 
 if (HueCyclic) then
   res@vpXF = 0.1
   res@vpYF = 0.6
 end if

 
 ;set saturation values
 if (isatt(res,"epExplicitSatLevels")) then
   nSats = dimsizes(res@epExplicitSatLevels) + 1
   satlevels = res@epExplicitSatLevels
   delete(res@epExplicitSatLevels)
   
 else
 
   if (isatt(res,"epMinSatLevel").AND.isatt(res,"epMaxSatLevel").AND. \
       isatt(res,"epSatLevelSpacing")) then
     nSats = round(((res@epMaxSatLevel-res@epMinSatLevel)/res@epSatLevelSpacing),3) + 2
     
     satlevels = fspan(res@epMinSatLevel,res@epMaxSatLevel,nSats-1)
     
     delete(res@epMinSatLevel)
     delete(res@epMaxSatLevel)
     delete(res@epSatLevelSpacing)
   
   else
     
     if (isatt(res,"epMinSatLevel")) then
       minsat = res@epMinSatLevel 
       delete(res@epMinSatLevel)
     else
       minsat = min(sat_data)
     end if

     if (isatt(res,"epMaxSatLevel")) then
       maxsat = res@epMaxSatLevel
       delete(res@epMaxSatLevel)
     else
       maxsat = max(sat_data)
     end if
     
     if (isatt(res,"epSatLevelSpacing")) then
       nSats = round(((maxsat-minsat)/res@epSatLevelSpacing),3) + 2
       delete(res@epSatLevelSpacing)
     else
       nSats = 8
     end if
  
     mnmxint = nice_mnmxintvl(minsat,maxsat,nSats,False)
   
     nSats = round(((mnmxint(1) - mnmxint(0))/mnmxint(2)),3) + 2

     satlevels = fspan(mnmxint(0),mnmxint(1),nSats-1)

     delete(mnmxint)
     
   end if
 end if


 ;set hue values
 if (isatt(res,"epExplicitHueLevels")) then
   nHues = dimsizes(res@epExplicitHueLevels)
   huelevels = res@epExplicitHueLevels
   delete(res@epExplicitHueLevels)
   
 else
 
    if (isatt(res,"epMinHueLevel").AND.isatt(res,"epMaxHueLevel").AND. \
       isatt(res,"epHueLevelSpacing")) then
     nHues = round(((res@epMaxHueLevel-res@epMinHueLevel)/res@epHueLevelSpacing),3) + 1
     
     huelevels = fspan(res@epMinHueLevel,res@epMaxHueLevel,nHues)
     
     delete(res@epMinHueLevel)
     delete(res@epMaxHueLevel)
     delete(res@epHueLevelSpacing)
   
   else

     if (isatt(res,"epMinHueLevel")) then
       minhue = res@epMinHueLevel
       delete(res@epMinHueLevel)
     else
       minhue = min(hue_data)
     end if

     if (isatt(res,"epMaxHueLevel")) then
       maxhue = res@epMaxHueLevel
       delete(res@epMaxHueLevel)
     else
       maxhue = max(hue_data)
     end if
     
     if (isatt(res,"epHueLevelSpacing")) then
       nHues = round(((maxhue-minhue)/res@epHueLevelSpacing),3)+2
       delete(res@epHueLevelSpacing)
     else
       nHues = 8
     end if
 
     mnmxint = nice_mnmxintvl(minhue,maxhue,nHues,False)
   
     nHues = round(((mnmxint(1) - mnmxint(0))/mnmxint(2)),3) + 1
   
     huelevels = fspan(mnmxint(0),mnmxint(1),nHues)

   end if
 end if
 

 if (HueCyclic) then
   huemidlevels = huelevels
   delete(huelevels)
   huelevels = (huemidlevels(:nHues-2)+huemidlevels(1:))/2.
 else
   nHues = nHues + 1
 end if
   				
			
			
				
 ;create HSV colormap
 cmap = evans_plot_color_map(nHues,nSats,hueoffset,minV)
 gsn_define_colormap(wks,cmap)
 
;gsn_draw_colormap(wks)
 
 

  
 ;want to convert data to a single layer with values representing the
 ;colormap location of each point
 plotvar = hue_data
 plotvar = plotvar@_FillValue
 plotvar1d = ndtooned(plotvar)
 thishue = new(dimsizes(plotvar1d),logical)
 

 hue_data1d = ndtooned(hue_data)
 sat_data1d = ndtooned(sat_data)
 
 
 ;for the first hue
 hueinds = ind(hue_data1d.lt.huelevels(0))
 if (any(.not.ismissing(hueinds))) then
   thishue(hueinds) = True
 end if
   
 if (any(thishue)) then
     
   ;for the first sat  
   satinds = ind(sat_data1d.lt.satlevels(0).AND.thishue)   
   if (any(.not.ismissing(satinds))) then    
     plotvar1d(satinds) = 0.5
   end if
   delete(satinds)
   
   ;for the middle sats
   do i = 1,nSats-2
     satinds = ind(sat_data1d.ge.satlevels(i-1).AND.sat_data1d.lt.satlevels(i) \
		   .AND.thishue)
     if (any(.not.ismissing(satinds))) then
       plotvar1d(satinds) = 0.5 + i
     end if
     delete(satinds)
   end do	   
       
   ;for last sat
   satinds = ind(sat_data1d.ge.satlevels(nSats-2).AND.thishue)
   if (any(.not.ismissing(satinds))) then
     plotvar1d(satinds) = 0.5 + nSats-1
   end if
   delete(satinds)
   
 end if
 delete(hueinds)
 thishue = False
 
 ;for the middle hues
 do j = 1,nHues-2
   hueinds = ind(hue_data1d.ge.huelevels(j-1).AND.hue_data1d.lt.huelevels(j))
   if (any(.not.ismissing(hueinds))) then
     thishue(hueinds) = True
   end if
   
   if (any(thishue)) then
     
     ;for the first sat  
     satinds = ind(sat_data1d.lt.satlevels(0).AND.thishue)
     if (any(.not.ismissing(satinds))) then      
       plotvar1d(satinds) = 0.5 + j*nSats 
     end if
     delete(satinds)
     
     ;for the middle sats
     do i = 1,nSats-2
       satinds = ind(sat_data1d.ge.satlevels(i-1).AND.sat_data1d.lt.satlevels(i) \
		   .AND.thishue)
		
       if (any(.not.ismissing(satinds))) then		   
         plotvar1d(satinds) = 0.5 + j*nSats + i 
       end if
       delete(satinds)
     end do	   
       
     ;for last sat
     satinds = ind(sat_data1d.ge.satlevels(nSats-2).AND.thishue)
     if (any(.not.ismissing(satinds))) then
       plotvar1d(satinds) = 0.5 + j*nSats + nSats-1 
     end if
     delete(satinds)
        
   end if
   delete(hueinds)
   thishue = False
 end do  		  
       
 ;for the last hue
 hueinds = ind(hue_data1d.ge.huelevels(nHues-2))
 if (any(.not.ismissing(hueinds))) then
   thishue(hueinds) = True
 end if
 
 if (any(thishue)) then
     
   ;for the first sat  
   satinds = ind(sat_data1d.lt.satlevels(0).AND.thishue)
   if (any(.not.ismissing(satinds))) then      
     plotvar1d(satinds) = 0.5 + (nHues-1)*nSats
   end if
   delete(satinds)
   
   ;for the middle sats
   do i = 1,nSats-2
     satinds = ind(sat_data1d.ge.satlevels(i-1).AND.sat_data1d.lt.satlevels(i) \
		   .AND.thishue)
     if (any(.not.ismissing(satinds))) then
       plotvar1d(satinds) = 0.5 +(nHues-1)*nSats + i
     end if
     delete(satinds)
   end do	   
       
   ;for last sat
   satinds = ind(sat_data1d.ge.satlevels(nSats-2).AND.thishue)
   if (any(.not.ismissing(satinds))) then
     plotvar1d(satinds) = 0.5 + (nHues-1)*nSats + nSats-1
   end if
   delete(satinds)
   
 end if
 delete(hueinds)
 
 
 
 plotvar = onedtond(plotvar1d,dimsizes(plotvar))
 
 copy_VarMeta(hue_data,plotvar)
 if (isatt(plotvar,"units")) then
   delete(plotvar@units)
 end if
 
 if (isatt(res,"gsnFrame")) then
   framenow = res@gsnFrame
 else
   framenow = True
 end if
 
 res@gsnFrame = False
 res@gsnDraw = False

 res@cnLevelSelectionMode = "ManualLevels"
 res@cnMinLevelValF = 1.
 res@cnMaxLevelValF = (nSats*nHues) - 1.
 res@cnLevelSpacingF = 1.
 
 
 plot_obj = gsn_csm_contour_map(wks,plotvar,res)
 
 
 
 ;add the color wheel or label bar
 if (HueCyclic) then
   add_color_wheel(wks,nHues,nSats,hueunits,huemidlevels,satlevels,cwScale, \
                     cwX,cwY,cwPerim)
 else
   add_ep_label_bar(wks,nHues,nSats,hueunits,huelevels,satunits,satlevels)
 end if
 
 if (framenow) then
   frame(wks)
 end if

 
 return(plot_obj)

end

				
				
