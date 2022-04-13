load "$POD_HOME/panel_two_sets.ncl" 
setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

undef("debug_print")
procedure debug_print(string_to_print,routine_name,debug_flag)
begin

  if ( debug_flag ) then
    print(routine_name+": "+string_to_print)
  end if
end ; procedure debug_print

undef ("calculate_samples_per_day")
function calculate_samples_per_day(time,debug_flag)
begin

  funcname = "calculate_samples_per_day"

  hour   = time(:,3)
  hour_diff = hour(1) - hour(0)

  if ( hour_diff .eq. 0 ) then
    spd = 1 ;  1 sample per day (no hour difference)
  else
    spd = tointeger(24/hour_diff)
  end if

  debug_print("Calculated samples per day "+spd+" from hour_diff "+hour_diff+" (hour0= "+hour(0)+" ,hour1= "+hour(1)+")",funcname,debug_flag)


  return spd
end

undef("one_plot")
procedure one_plot(var,file_name,map_flag,debug_flag)
begin

  funcname = "one_plot"
  if (.not.map_flag) then  
    file_name = file_name+"_nomap"
  end if
  debug_print("one_plot, map_flag = "+map_flag+", writing figure: "+file_name,funcname,debug_flag)


  dir_out  = getenv("WK_DIR")+"/model/PS/debug/"       ; output dir: should be working directory
  system("mkdir -p "+dir_out)
  file_out = dir_out+"/"+file_name
  wks  = gsn_open_wks("png",file_out)         ; send graphics to PNG file
  debug_print("DEBUG one_plot writing figure "+file_out+".png",funcname,debug_flag)
  res                     = True

; you can have the contour lines on in raster mode, but their thickness
; actually make the plot look like is was contoured normally.

  res@cnFillOn         = True               ; color Fill 
  res@cnFillMode       = "RasterFill"       ; Raster Mode
  res@cnLinesOn        =  False             ; Turn off contour lines
;================================
; these three resources make the continents look nice. The first two
; make them color, and the later adds continental outlines when
; raster mode is used.

; this overwrites the data with continents ?!!
;  res@cnLineDrawOrder  = "Predraw"          ; Draw lines and filled
;  res@cnFillDrawOrder  = "Predraw"          ; areas before map gets set
;=================================
;  res@cnLevelSelectionMode = "ManualLevels" ; set manual contour levels
;  res@cnMinLevelValF   = -2.0               ; set min contour level
;  res@cnMaxLevelValF   =  0.0               ; set max contour level
;  res@cnLevelSpacingF  =  0.5               ; set contour spacing

  res@mpCenterLonF     = 180                ; set map center at 180
;  res@mpLandFillColor  = "light yellow"     ; choose color of continents.
                                            ; must be in colormap  

  res@gsnCenterString  = file_name   ; add center string
  res@gsnRightString   = ""            ; add right string

;  res@cnFillPalette = (/"magenta","blue","orange","green","yellow","red"/) 

    res@gsnZonalMean    = True                    ; put zonal on side
    if ( map_flag ) then
      plot = gsn_csm_contour_map_ce(wks,var, res) ; create plot
    else
      plot = gsn_csm_contour(wks,var, res) ; create plot
    end if
end ; one_plot


undef("diff_plot")
procedure diff_plot(var0,var1,file_name,debug_flag)
begin

  funcname = "diff_plot"
;  debug_print(" into diff_plot "+file_name,funcname,debug_flag)

;---Calculate difference
    diff                    = var1           ; trick to create array with    coordinate info
    diff                    = var1 - var0     ; over write values with    differences
    diff@long_name          =  "difference"
    debug_print("========================================",funcname,debug_flag)
;    printVarSummary(diff)   
    debug_print(" min="+min(diff)+"   max="+max(diff),funcname,debug_flag)

;---Plot
    dir_out  = getenv("WK_DIR")+"/model/PS/debug/"       ; output dir
    system("mkdir -p "+dir_out)
    file_out = dir_out+"/diff_"+file_name
    wks  = gsn_open_wks("png",file_out)         ; send graphics to PNG file
    debug_print("DEBUG diff_plot writing figure "+file_out+".png",funcname,debug_flag)
    res                     = True
    res@gsnDraw             = False
    res@gsnFrame            = False
    res@mpFillOn            = False            ; no need   
;    res@cnLevelSelectionMode= "ManualLevels"   ; manual set levels
;    res@cnMinLevelValF      = -3.0
;    res@cnMaxLevelValF      = 27.0
;    res@cnLevelSpacingF     = 1.5              ; 20 contour levels        
    res@cnFillOn            = True             ; color fill plot
;    res@cnFillPalette       = "BlAqGrYeOrRe"
    res@cnLinesOn           = False
    res@cnLineLabelsOn      = False
    res@cnInfoLabelOn       = False

; unforrtunately these don't work
;    res@trYMin = min(var1&lat)
;    res@trYMax = max(var1&lat)

;    res@lbLabelBarOn        = False            ; turn off individual label    bars
;
; Formatting the labelbar strings helps make the two sets of labelbars
; match better. Even though the labelbar is turned off, it is internally
;  still generated.
;
;    res@lbLabelStrings      = sprintf("%4.1f",ispan(-30,370,15)*0.1)

    plot = new(2,graphic)    
    
    res@gsnLeftString       = "";  field name
    res@gsnRightString      = ""; unnits

    res@gsnCenterString     = "New"
    plot(0) = gsn_csm_contour_map(wks,var1,res)

    res@gsnCenterString     = "Old"
    plot(1) = gsn_csm_contour_map(wks,var0,res)
    
 ;   res@cnMinLevelValF      = -4.
 ;   res@cnMaxLevelValF      =  4.
 ;   res@cnLevelSpacingF     =  1.
 ;   res@cnFillPalette       = "BlueWhiteOrangeRed"    ; select a color map with white in the middle
    res@gsnCenterString     = "Difference: Top - Bottom"

;---Formatting the labelbar strings helps make the two sets of labelbars   match better
;    res@lbLabelStrings      := sprintf("%4.1f",ispan(-4,4,1))
    plot2 = gsn_csm_contour_map(wks, diff ,res)
    
;---Panel the two sets of plots. Note no special resources need to be set.
    pres1 = True
    pres2 = True
    pres  = True
    pres@lbLabelBarOn        = False            ; turn off communcal label bar
    panel_two_sets(wks,plot,plot2,(/2,1/),(/1,1/),pres1,pres2,pres)
end ; diff_plot

undef("ts_plot")
procedure ts_plot(var,file_name,debug_flag)
begin
; Expected to be a 3D field time, lat, lon
; Try a zonal avg time vs 2 lon.
; Eventually, could plot 5 different lons, and/or a raster 2d of time vs lon
;---To plot multiple lines, you must put them into a mulidimensional array.

  funcname = "ts_plot"
;  printVarSummary(var)  ; [time | 2922] x [lat | 30] x [lon | 360]

  zavg = dim_avg_n_Wrap(var,1)
;  printVarSummary(zavg)  ; [time | 2922] x  [lon | 360]

  lons = (/30,120,150,180,300/)
  debug_print("lons "+lons,funcname,debug_flag)
  nlons = dimsizes(lons)

;  data      = new((/nlons,dimsizes(var&time)/),float)
 

  dir_out  = getenv("WK_DIR")+"/model/PS/debug/"       ; output dir
  system("mkdir -p "+dir_out)
  file_out = dir_out+"/ts_"+file_name
  wks  = gsn_open_wks("png",file_out)         ; send graphics to PNG file
  debug_print("DEBUG ts_plot writing figure "+file_out+".png",funcname,debug_flag)

;---Set plotting parameters

  plot = new(nlons,graphic)                          ; create a plot array

                                ; within each panel
  res                   = True                      ; plot mods desired
    
                                ; for panel plot, wait to draw
  res@gsnDraw             = False            ; don't draw
  res@gsnFrame            = False            ; don't advance frame
; Similiar resources are xyLineThicknessF and xyLineColor,
; which will affect all lines in the array.
;
; res@xyLineThicknesses = (/  1.0,   2.0/)          ; make second line thicker
  res@xyLineColors      = (/"blue"/)          ; change line color


  res@vpWidthF    = 0.8      ; Make plots wider than 
  res@vpHeightF   = 0.2      ; they are high.

  res@tmYUseLeft           = False   ; Make right axis independent of left
  res@tmYLOn               = False   ; Turn off left tickmarks
  res@tmYROn               = True    ; Turn on right tickmarks
  res@tmXTOn               = False   ; Turn off top tickmarks
  res@tmYLLabelsOn         = False   ; Turn off left labels
  res@tmYRLabelsOn         = True    ; Turn on right labels
  res@tmYRMinorOn          = False   ; Turn off minor ticks on Y axis
  res@tmYRLabelFontHeightF = 0.015   ; Increase font height
  res@tmYRLabelDeltaF      = 2.0     ; Increase space b/w ticks and labels
  res@tmYRLabelJust        = "CenterRight"   ; right-justify labels

  maxdata = max(zavg)
  mindata = min(zavg)
  res@trYMinF = mindata
  res@trYMaxF = maxdata

  do i=0,nlons-1
  
;    debug_print("DEBUG starting "+i+" lon "+lons(i),funcname,debug_flag)
    data = zavg(:,{lons(i)})

    res@tiYAxisString      = "lon "+lons(i)       ; add title

    plot(i)  = gsn_csm_xy (wks,data&time,data,res) ; create plot

  end do
;************************************************
; create panel
;************************************************
  resP                  = True                   ; modify the panel plot
;  resP@gsnFrame         = True                  ; don't advance panel plot
;  resP@gsnDraw           = True            ; don't draw
  resP@gsnMaximize    = True                ; maximize plots
  resP@gsnPanelMainString = file_name +" zonal avg at longitudes"     ; set main title
;  resP@gsnPanelBottom   = 0.05                   ; add space at bottom
;  resP@gsnPanelFigureStrings= "longitude:" + lons
;  resP@amJust   = "TopLeft"
  gsn_panel(wks,plot,(/nlons,1/),resP)               ; now draw as one plot

 


end ; procedure ts_plot(var,figure_name)