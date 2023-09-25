; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

;***********************************************************
; Generate life cycle composites based upon daily phase space
; If the MJO_INDEX is < 1.0 it is not included
;***********************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"  
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"  
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

  routine_name = "mjo_life_cycle"
   casename = getenv("CASENAME")
   file_dir = getenv("WK_DIR")+"/model/netCDF/"

   latS    = -20
   latN    =  20

;   ymdStrt = 19950101                         ; start yyyymmdd
;   ymdLast = 19991231                         ; last  

;   yrStrt  = ymdStrt/10000
;   yrLast  = ymdLast/10000

   pltSubTitle = "Anomalous: OLR, U850, V850"

   pltDir  = getenv("WK_DIR")+"/model/PS/"                           ; plot directory
   pltType = "ps"  
   pltName = casename+".MJO.life.cycle"                      ; yrStrt+"_"+yrLast
  
;   diri    = "/Users/shea/Data/AMWG/"         ; input directory   

   filo    = file_dir+casename+".rlut.day.anom.nc"
   filu    = file_dir+casename+".u850.day.anom.nc"
   filv    = file_dir+casename+".v850.day.anom.nc"

;************************************************
; create BandPass Filter
;************************************************
  ihp      = 2                             ; bpf=>band pass filter
  nWgt     = 201
  sigma    = 1.0                           ; Lanczos sigma
  fca      = 1./100.
  fcb      = 1./20.
  wgt      = filwgts_lanczos (nWgt, ihp, fca, fcb, sigma )

;***********************************************************
; Find the indicies (subscripts) corresponding to the start/end times
;***********************************************************

   f       = addfile (filu , "r")                         
   TIME    = f->time                          ; days since ...
   YMD     = cd_calendar(TIME, -2)            ; entire (time,6)

   ymdStrt = min(YMD(:))
   ymdLast = max(YMD(:))
   yrStrt  = ymdStrt/10000
   yrLast  = ymdLast/10000
   
;   iStrt   = ind(YMD.eq.ymdStrt)              ; index start
;   iLast   = ind(YMD.eq.ymdLast)              ; index last 
   delete(TIME)
   delete(YMD )

   time    = f->time             ; days since ...
   u       = f->u850(:,{latS:latN},:) 
;***********************************************************
; Read anomalies frpm other fields
;***********************************************************
   f       = addfile (filv , "r")                         
   v       = f->v850(:,{latS:latN},:)

   f       = addfile (filo , "r")                         
   x       = f->rlut(:,{latS:latN},:) 

   dimx    = dimsizes( x )
   ntim    = dimx(0)
   nlat    = dimx(1)
   mlon    = dimx(2)
;************************************************
; Apply the band pass filter to the original anomalies
;************************************************
  x   = wgt_runave_leftdim (x, wgt, 0)
  u   = wgt_runave_leftdim (u, wgt, 0)
  v   = wgt_runave_leftdim (v, wgt, 0)

;***********************************************************
; Open PC components file created in 'mjo_14.ncl'
;***********************************************************
;  diri    = "/Users/shea/ncld/AMWG/"         ; input directory   
  fMJO    = file_dir+"MJO_PC_INDEX.nc"                ; created in mjo_14.ncl
  f       = addfile (fMJO, "r")

;***********************************************************
; Find the indices corresponding to the start/end times
;***********************************************************
;  TIME    = f->time                          ; days since ...
;  YMD     = cd_calendar(TIME, -2)            ; entire (time,6)

;  iStrt   = ind(YMD.eq.ymdStrt)              ; index start
;  iLast   = ind(YMD.eq.ymdLast)              ; index last 
;  delete(TIME)
;  delete(YMD )

;***********************************************************
; Read the data for the desired period
;***********************************************************
  pc1     = f->PC1
  pc2     = f->PC2
  mjo_indx= f->MJO_INDEX

  time    = f->time
  ymdhms  = cd_calendar(time, 0)

  imon    = floattoint( ymdhms(:,1) )   ; convenience
  iday    = floattoint( ymdhms(:,2) )   ; subscripts must be integer

;***********************************************************
; Place each array into an appropriate array
;***********************************************************
  nPhase      = 8
  angBnd      = new( (/2,nPhase/), "float")
  angBnd(0,:) = fspan(  0,315,nPhase)
  angBnd(1,:) = fspan( 45,360,nPhase)

  r2d         = 180./(4.*atan(1.0))

  do pc_sign_flip = 1,2
    if (pc_sign_flip.eq.2) then  ; 1 = v1, 2 = v2 
      pc1     = pc1*-1.0
      file_tail = ".v2"  ; this script just produces both figures, user
                        ; needs to choose
    else
      file_tail = ""
    end if ; pc_sign_flip
  ang         = atan2(pc2,pc1)*r2d     ; phase space 
  nn          = ind(ang.lt.0)
  ang(nn)     = ang(nn) + 360          ; make 0 to 360

  nDays       = new (nPhase, "integer")
  pLabel      = "P"+ispan(1,nPhase,1)+": "

;------------------------------------------------------------
; PLOTS
;------------------------------------------------------------
  

  

  res                      = True         
  res@gsnDraw              = False        ; don't draw yet
  res@gsnFrame             = False        ; don't advance frame yet
  res@gsnSpreadColors      = True         ; spread out color table
 
  res@mpFillOn             = False        ; turn off map fill
  res@mpMinLatF            = latS         ; zoom in on map
  res@mpMaxLatF            = latN
  res@mpCenterLonF         = 210.
  res@cnFillOn             = True         ; turn on color fill
  res@cnLinesOn            = False        ; True is default
  res@cnLineLabelsOn       = False        ; True is default
  res@lbLabelBarOn         = False        ; turn off individual lb's
  res@gsnScalarContour     = True         ; contour 3rd array 
  res@gsnMajorLatSpacing   = 15
  res@gsnMajorLonSpacing   = 60
  res@tmXBLabelFontHeightF = 0.01
  res@tmYLLabelFontHeightF = 0.01

                                          ; common contours 
 ;mnmxint = nice_mnmxintvl( min(x) , max(x), 16, False)
  res@cnLevelSelectionMode = "ManualLevels"
  res@cnMinLevelValF       =  -40         ; -100; mnmxint(0)
  res@cnMaxLevelValF       =   40         ;   80; mnmxint(1)
  res@cnLevelSpacingF      =    5         ;   20; mnmxint(2)
;print(res)

  res@vcMinDistanceF            = 0.01            ; thin the vector density
  res@vcRefMagnitudeF           = 2.0             ; define vector ref mag
  res@vcRefLengthF              = 0.025           ; define length of vec ref
  res@vcRefAnnoOrthogonalPosF   = -1.0            ; move ref vector
  res@vcRefAnnoArrowLineColor   = "black"         ; change ref vector color
  res@vcRefAnnoArrowUseVecColor = False           ; don't use vec color for ref
  res@vcRefAnnoFontHeightF = 0.01
                                          ; panel plot only resources
  resP                     = True         ; modify the panel plot
  resP@gsnMaximize         = True         ; large format
  resP@gsnPanelLabelBar    = True         ; add common colorbar
  resP@lbLabelAutoStride   = True         ; auto stride on labels
  resP@lbLabelFontHeightF  = 0.01
  resP@gsnPanelBottom      = 0.05         ; add some space at bottom
  resP@pmLabelBarWidthF    = 0.8          ; label bar width
  resP@pmLabelBarHeightF   = 0.05
  resP@gsnPanelFigureStringsFontHeightF = 0.0125  ; bit larger than default
 ;resP@pmLabelBarOrthogonalPosF = 0.015   ; move labelbar up a bit

  txres                  = True             
  txres@txFontHeightF    = 0.01
;  txid = gsn_create_text(wks, pltSubTitle, txres)

  amres                  = True 
 ;amres@amParallelPosF   =  0.575  
  amres@amOrthogonalPosF =  0.75  
  amres@amJust           = "CenterCenter"
 ;amres@amResizeNotify   = True

;*******************************************
; Loop over each phase
;*******************************************
 res@gsnLeftString   = ""
 res@gsnRightString  = ""
 do nSeason=1,2

    if (nSeason.eq.1) then
        resP@txString  = yrStrt+"-"+yrLast+": May to Oct"
        pltPath = pltDir+pltName+".summer"+file_tail
    else
        resP@txString  = yrStrt+"-"+yrLast+": Nov to Apr"
        pltPath = pltDir+pltName+".winter"+file_tail
    end if
    print(routine_name+" writing figure "+pltPath)

  wks  = gsn_open_wks(pltType,pltPath)
  gsn_define_colormap(wks,"ViBlGrWhYeOrRe") 
  plot = new(nPhase,graphic)  
  txid = gsn_create_text(wks, pltSubTitle, txres)

  do n=0,nPhase-1
     if (nSeason.eq.1) then
         nt = ind(mjo_indx.gt.1.0    .and.                     \
                 (imon.ge.5          .and. imon.le.10).and.    \
                  ang.ge.angBnd(0,n) .and. ang.lt.angBnd(1,n))
     else
         nt = ind(mjo_indx.gt.1.0    .and.                     \
                 (imon.ge.11         .or.  imon.le. 4).and.    \
                  ang.ge.angBnd(0,n) .and. ang.lt.angBnd(1,n))
     end if
     if (.not.all(ismissing(nt))) then
         xAvg = dim_avg_Wrap( x(lat|:,lon|:,time|nt) )
         uAvg = dim_avg_Wrap( u(lat|:,lon|:,time|nt) )
         vAvg = dim_avg_Wrap( v(lat|:,lon|:,time|nt) )
         nDays(n) = dimsizes(nt)
         ; Don't know why these get lost!
         xAvg&lon@units = x&lon@units
         uAvg&lon@units = x&lon@units
         vAvg&lon@units = x&lon@units
         xAvg&lat@units = x&lat@units
         uAvg&lat@units = x&lat@units
         vAvg&lat@units = x&lat@units

         res@tmXBLabelsOn         = False    ; do not draw lon labels
         res@tmXBOn               = False    ;             lon tickmarks
         if (n.eq.(nPhase-1)) then           ; 
             res@tmXBLabelsOn     = True     ; draw lon labels
             res@tmXBOn           = True     ;          tickmarks
         end if
         plot(n) = gsn_csm_vector_scalar_map_ce(wks,uAvg,vAvg,xAvg,res)
     end if
     delete(nt)                  ; will change next iteration
  end do ; n=0,nPhase-1

;;ann3  = gsn_add_annotation(plot(0), txid, amres)
  resP@gsnPanelFigureStrings= pLabel+nDays
  gsn_panel(wks,plot,(/nPhase,1/),resP)     ; now draw as one plot
 end do ; nSeason=1,2 

end do ; pc_sign_flip = 1,2

; system("gv "+pltPath+"."+pltType)
end
