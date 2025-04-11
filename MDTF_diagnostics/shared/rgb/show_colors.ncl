; This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

;************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"   
;************************************************
begin
; replace amwg.rgb with your own rgb file
 wks = gsn_open_wks("x11","rgb")            
 cmap = RGBtoCmap("amwg_reverse.rgb")
 gsn_define_colormap(wks,cmap)       
 gsn_draw_colormap(wks)             
end
