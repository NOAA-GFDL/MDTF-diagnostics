;;;   read in and process Elnino/Lanina data etc.

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin

;;  constant 
   cp = 1004 ;; 
   lh = 2.5E+06 ;; latent heat of evaporation
   gg = 9.81

     varcode = getenv ("POD_HOME")
     vardata  = getenv("ENSO_MSE_WKDIR_COMPOSITE")  + "/model/" ;;                  ; model input
     outdir2  = getenv("ENSO_MSE_WKDIR_MSE") + "/model/" ; envvar set in ENSO_MSE.py
     case =  getenv( "CASENAME")

     iy1 = toint( ( getenv("FIRSTYR")) )
     iy2 = toint( (  getenv("LASTYR")) )

     nameout = outdir2 + "netCDF/"
;;;  input variables 
      Vars3 = (/ "zg", "ua", "va", "ta", "hus", "wap" /)
      ivar3 = dimsizes( Vars3)
      unit3 = (/ "m", "m/s", "m/s", "K", "kg/kg", "Pa/s" /)

;;;  output variables
      Varsout = (/ "madv", "mdiv", "mse", "omse", "tadv" /)
      unitout = (/ "W/m2", "W/m2",  "J/m2", "W/m2", "W/m2" /)
      standardname = (/ "moisture_advection" , "moisture_divergence", \
                        "moist_static_energy", "vertical_advection_of_moist_static_energy", \
                        "temperature_advection " /)

;;;  read in all Vars3 as ELNINO/LANINA and climatology 
;;  zg:  
    i = 0
    Varname = Vars3(i)
    namein1 = vardata +    "/netCDF/ELNINO/" + Varname + ".nc"
    namein2 = vardata +    "/netCDF/LANINA/" + Varname + ".nc"
    nameclima = vardata +    "/netCDF/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin2 = addfile( namein2, "r")
    fin3 = addfile( nameclima, "r")

      lat = (fin1->lat)
      lon = (fin1->lon)
      plev =(fin1->lev)
      time0 = fin1->time
      time2 = calendar_decode2( time0 ,  -5)

       tdim = dimsizes(time0)     ; get dimension sizes
       zdim = dimsizes(plev)
       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

    zg1     = fin1->$Varname$
    zg2     = fin2->$Varname$
    zg_clim = fin3->$Varname$

    dplev =  100. *  tofloat( center_finite_diff_n (plev, 1, False, 0, 0) )  ;;; convert to Pa
    
    delete( [/ fin1, fin2, fin3 /])
;;;   U             
     i = 1
    Varname = Vars3(i)
    namein1 = vardata +    "/netCDF/ELNINO/" + Varname + ".nc"
    namein2 = vardata +    "/netCDF/LANINA/" + Varname + ".nc"
    nameclima = vardata +    "/netCDF/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin2 = addfile( namein2, "r")
    fin3 = addfile( nameclima, "r")

    uu1     = fin1->$Varname$
    uu2     = fin2->$Varname$
    uu_clim = fin3->$Varname$
    delete( [/ fin1, fin2, fin3 /])
;;; ;V 
    i = 2
    Varname = Vars3(i)
    namein1 = vardata +    "/netCDF/ELNINO/" + Varname + ".nc"
    namein2 = vardata +    "/netCDF/LANINA/" + Varname + ".nc"
    nameclima = vardata +    "/netCDF/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin2 = addfile( namein2, "r")
    fin3 = addfile( nameclima, "r")

    vv1     = fin1->$Varname$
    vv2     = fin2->$Varname$
    vv_clim = fin3->$Varname$
    delete( [/ fin1, fin2, fin3 /])
;;;;  T 
   i = 3
    Varname = Vars3(i)
    namein1 = vardata +    "/netCDF/ELNINO/" + Varname + ".nc"
    namein2 = vardata +    "/netCDF/LANINA/" + Varname + ".nc"
    nameclima = vardata +    "/netCDF/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin2 = addfile( namein2, "r")
    fin3 = addfile( nameclima, "r")

    ta1     = fin1->$Varname$
    ta2     = fin2->$Varname$
    ta_clim = fin3->$Varname$
    delete( [/ fin1, fin2, fin3 /])
;;     hus: 
    i = 4
    Varname = Vars3(i)
    namein1 = vardata +    "/netCDF/ELNINO/" + Varname + ".nc"
    namein2 = vardata +    "/netCDF/LANINA/" + Varname + ".nc"
    nameclima = vardata +    "/netCDF/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin2 = addfile( namein2, "r")
    fin3 = addfile( nameclima, "r")

    hus1     = fin1->$Varname$
    hus2     = fin2->$Varname$
    hus_clim = fin3->$Varname$
    delete( [/ fin1, fin2, fin3 /])
;;;;;  omega = wap  
    i = 5
    Varname = Vars3(i)
    namein1 = vardata +    "/netCDF/ELNINO/" + Varname + ".nc"
    namein2 = vardata +    "/netCDF/LANINA/" + Varname + ".nc"
    nameclima = vardata +    "/netCDF/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin2 = addfile( namein2, "r")
    fin3 = addfile( nameclima, "r")

    wap1     = fin1->$Varname$
    wap2     = fin2->$Varname$
    wap_clim = fin3->$Varname$
    delete( [/ fin1, fin2, fin3 /])

;;;;;;;;  calculations are done here 
;; TADV    = vertical integral ELNINO/LANINA + CLIMA  output   MSE_madv.nc
    iv = 4
    cyclic = True
    gridType  = 1
    opt_adv   = 0   ; return only the advected variable 
    long_name = "advection of temperature"
    units     = "K/s"    
 
    ff = 1./( 6378388. * 0.0174533  )
    tadv11 =  ta1
    dtdx = ff * tofloat( center_finite_diff_n (ta1, lon,  True, 0, 3) ) 
    dtdy = ff * tofloat( center_finite_diff_n (ta1, lat, False, 0, 2) )   
    do j=0,ydim-1                      ; loop over each latitude
      dtdx(:,:,j,:) =  dtdx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     tadv11 = -cp  * ( uu1 * dtdx + vv1 * dtdy) 
     
    tadv22 =  ta2
    dtdx = ff * tofloat( center_finite_diff_n (ta2, lon,  True, 0, 3) )
    dtdy = ff * tofloat( center_finite_diff_n (ta2, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dtdx(:,:,j,:) =  dtdx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     tadv22 = -cp  * ( uu2 * dtdx + vv2 * dtdy)
   
    tadv_clim1 = ta_clim
    dtdx = ff * tofloat( center_finite_diff_n (ta_clim, lon,  True, 0, 3) )
    dtdy = ff * tofloat( center_finite_diff_n (ta_clim, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dtdx(:,:,j,:) =  dtdx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     tadv_clim1 = -cp * ( uu_clim * dtdx + vv_clim * dtdy)
;;;  make vertical integral : 
   
   do k = 0, zdim - 1
   tadv11(:, k, :,:) =  dplev(k) * tadv11(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   tadv22(:, k, :,:) =  dplev(k) * tadv22(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   tadv_clim1(:, k, :,:) =  dplev(k) * tadv_clim1(:, k, :,:) 
   end do 

   tadv1     = dim_sum_n_Wrap( tadv11 , 1)
   tadv2     = dim_sum_n_Wrap( tadv22 , 1)
   tadv_clim = dim_sum_n_Wrap( tadv_clim1 , 1)
   tadv1     = -tadv1/gg
   tadv2     = -tadv2/gg
   tadv_clim =  -tadv_clim/gg

;;;; output as netCDF 

       dimNames = (/ "lat", "lon"/) ;;  (/"time",  "lat", "lon"/)
       dimSizes = (/ ydim,  xdim /) ;;  (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ False, False/) ;;   (/ True , False, False/)


       copy_VarCoords( ta1(:,0,:,:), tadv1)
       tadv1@standard_name = standardname(iv)
       tadv1@units  = unitout(iv)

       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;;;   ELNINO       
       fileout  = nameout + "/ELNINO/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "tadv", typeof(tadv1),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "tadv", tadv1)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->tadv  = (/tadv1/)
       delete( fout)      
;;    LANINA 
       fileout  = nameout + "/LANINA/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "tadv", typeof(tadv2),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "tadv", tadv2)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->tadv  = (/tadv2/)
       delete( fout)
;;;   CLIMA 
      fileout  = nameout + "/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "tadv", typeof(tadv_clim),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "tadv", tadv_clim)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->tadv  = (/tadv_clim/)
       delete( fout)

;;;;;;;;;;;;;;;;;;;;;    moisture advection   - similar 
;; MADV    = vertical integral ELNINO/LANINA + CLIMA  output   MSE_madv.nc
    iv = 0
    cyclic = True
    gridType  = 1
    opt_adv   = 0   ; return only the advected variable
    long_name = "advection of moisture"
    units     = "K/s"

    ff = 1./( 6378388. * 0.0174533  )
    madv11 =  hus1
    dqdx = ff * tofloat( center_finite_diff_n (hus1, lon,  True, 0, 3) )
    dqdy = ff * tofloat( center_finite_diff_n (hus1, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dqdx(:,:,j,:) =  dqdx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     madv11 = -lh  * ( uu1 * dqdx + vv1 * dqdy)
   
    madv22 =  hus2
    dqdx = ff * tofloat( center_finite_diff_n (hus2, lon,  True, 0, 3) )
    dqdy = ff * tofloat( center_finite_diff_n (hus2, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dqdx(:,:,j,:) =  dqdx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     madv22 = -lh  * ( uu2 * dqdx + vv2 * dqdy)

    madv_clim1 = hus_clim
    dqdx = ff * tofloat( center_finite_diff_n (hus_clim, lon,  True, 0, 3) )
    dqdy = ff * tofloat( center_finite_diff_n (hus_clim, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dqdx(:,:,j,:) =  dqdx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     madv_clim1 = -lh * ( uu_clim * dqdx + vv_clim * dqdy)
;;;  make vertical integral :
   do k = 0, zdim - 1
   madv11(:, k, :,:) =  dplev(k) * madv11(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   madv22(:, k, :,:) =  dplev(k) * madv22(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   madv_clim1(:, k, :,:) =  dplev(k) * madv_clim1(:, k, :,:)
   end do

   madv1     = dim_sum_n_Wrap( madv11 , 1)
   madv2     = dim_sum_n_Wrap( madv22 , 1)
   madv_clim = dim_sum_n_Wrap( madv_clim1 , 1)
   madv1     = -madv1/gg
   madv2     = -madv2/gg
   madv_clim = -madv_clim/gg

;;;; output as netCDF

       dimNames = (/ "lat", "lon"/) ;;  (/"time",  "lat", "lon"/)
       dimSizes = (/ ydim,  xdim /) ;;  (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ False, False/) ;;   (/ True , False, False/)


       copy_VarCoords( hus1(:,0,:,:), madv1)
       tadv1@standard_name = standardname(iv)
       tadv1@units  = unitout(iv)

       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;;;   ELNINO
       fileout  = nameout + "/ELNINO/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "madv", typeof(madv1),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "madv", madv1)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->madv  = (/madv1/)
       delete( fout)
;;    LANINA
       fileout  = nameout + "/LANINA/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "madv", typeof(madv2),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "madv", madv2)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->madv  = (/madv2/)
       delete( fout)
;;;   CLIMA
      fileout  = nameout + "/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "madv", typeof(madv_clim),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "madv", madv_clim)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->madv  = (/madv_clim/)
       delete( fout)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;    MDIV  moisture divergence :
       iv = 1
    cyclic = True
    gridType  = 1
    opt_adv   = 0   ; return only the advected variable
    long_name = "moisture divergence "
    units     = "K/s"

    ff = 1./( 6378388. * 0.0174533  )
    mdiv11 =  hus1
    dudx = ff * tofloat( center_finite_diff_n (uu1, lon,  True, 0, 3) )
    dvdy = ff * tofloat( center_finite_diff_n (vv1, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dudx(:,:,j,:) =  dudx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     mdiv11 = lh  * hus1 * ( dudx +  dvdy)

    mdiv22 =  hus2
    dudx = ff * tofloat( center_finite_diff_n (uu2, lon,  True, 0, 3) )
    dvdy = ff * tofloat( center_finite_diff_n (vv2, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dudx(:,:,j,:) =  dudx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     mdiv22 = lh  * hus2 * ( dudx + dvdy)

    mdiv_clim1 = hus_clim
    dudx = ff * tofloat( center_finite_diff_n (uu_clim, lon,  True, 0, 3) )
    dvdy = ff * tofloat( center_finite_diff_n (vv_clim, lat, False, 0, 2) )
    do j=0,ydim-1                      ; loop over each latitude
      dudx(:,:,j,:) =  dudx(:,:,j,:)/cos(0.0174533* tofloat(lat(j)) )
    end do
     mdiv_clim1 = lh * hus_clim * ( dudx +  dvdy)
;;;  make vertical integral :
   do k = 0, zdim - 1
   mdiv11(:, k, :,:)     =  dplev(k) * mdiv11(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   mdiv22(:, k, :,:)     =  dplev(k) * mdiv22(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   mdiv_clim1(:, k, :,:) =  dplev(k) * mdiv_clim1(:, k, :,:)
   end do

   mdiv1     = dim_sum_n_Wrap( mdiv11 , 1)
   mdiv2     = dim_sum_n_Wrap( mdiv22 , 1)
   mdiv_clim = dim_sum_n_Wrap( mdiv_clim1 , 1)
   mdiv1     = -mdiv1/gg
   mdiv2     = -mdiv2/gg
   mdiv_clim = -mdiv_clim/gg      
;;;; output as netCDF

       dimNames = (/ "lat", "lon"/) ;;  (/"time",  "lat", "lon"/)
       dimSizes = (/ ydim,  xdim /) ;;  (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ False, False/) ;;   (/ True , False, False/)


       copy_VarCoords( hus1(:,0,:,:), mdiv1)
       tadv1@standard_name = standardname(iv)
       tadv1@units  = unitout(iv)

       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;;;   ELNINO
       fileout  = nameout + "/ELNINO/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "mdiv", typeof(mdiv1),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "mdiv", mdiv1)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->mdiv  = (/mdiv1/)
       delete( fout)
;;    LANINA
      fileout  = nameout + "/LANINA/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "mdiv", typeof(mdiv2),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "mdiv", mdiv2)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->mdiv  = (/mdiv2/)
       delete( fout)
;;;   CLIMA
       fileout  = nameout + "/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "mdiv", typeof(mdiv_clim),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "mdiv", mdiv_clim)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->mdiv  = (/mdiv_clim/)
       delete( fout)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;    MSE -  just vertical integral  first - will be used for vertical advection of MSE
    iv = 2
    cyclic = True
    gridType  = 1
    opt_adv   = 0   ; return only the advected variable
    long_name = "moist static energy"
    units     = "J/kg"

    mse11 =  hus1
    mse11 = cp * ta1 + lh * hus1 + gg * zg1
    mse22 =  hus2
    mse22 = cp * ta2 + lh * hus2 + gg * zg2
    mse_clim1 =  hus_clim
    mse_clim1 = cp * ta_clim + lh * hus_clim + gg * zg_clim

;;;  make vertical integral :
   do k = 0, zdim - 1
   mse11(:, k, :,:)     =  dplev(k) * mse11(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   mse22(:, k, :,:)     =  dplev(k) * mse22(:, k, :,:) ;;;   -dim_sum_n( dplev * madv11 , 2)/gg
   mse_clim1(:, k, :,:) =  dplev(k) * mse_clim1(:, k, :,:)
   end do

   mse1     = dim_sum_n_Wrap( mse11 , 1)
   mse2     = dim_sum_n_Wrap( mse22 , 1)
   mse_clim = dim_sum_n_Wrap( mse_clim1 , 1)
   mse1     = -mse1/gg
   mse2     = -mse2/gg
   mse_clim = -mse_clim/gg

;;;; output as netCDF

       dimNames = (/ "lat", "lon"/) ;;  (/"time",  "lat", "lon"/)
       dimSizes = (/ ydim,  xdim /) ;;  (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ False, False/) ;;   (/ True , False, False/)

       copy_VarCoords( hus1(:,0,:,:), mse1)
       tadv1@standard_name = standardname(iv)
       tadv1@units  = unitout(iv)

       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;;;   ELNINO
       fileout  = nameout + "/ELNINO/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "mse", typeof(mse1),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "mse", mse1)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->mse  = (/mse1/)
       delete( fout)
;;    LANINA
      fileout  = nameout + "/LANINA/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "mse", typeof(mse2),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "mse", mse2)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->mse  = (/mse2/)
       delete( fout)
;;;   CLIMA
       fileout  = nameout + "/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "mse", typeof(mse_clim),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "mse", mse_clim)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->mse  = (/mse_clim/)
       delete( fout)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; OMSE  vertical integral of vertical MSE advection 
     iv = 3
    cyclic = True
    gridType  = 1
    opt_adv   = 0   ; return only the advected variable
    long_name = "moist static energy vertical advection "
    units     = "W/m2"

    mse11 =  hus1
    mse11 = cp * ta1 + lh * hus1 + gg * zg1
    mse22 =  hus2
    mse22 = cp * ta2 + lh * hus2 + gg * zg2
    mse_clim1 =  hus_clim
    mse_clim1 = cp * ta_clim + lh * hus_clim + gg * zg_clim

    omse11 =  mse11 
    omse11 = wap1 * tofloat( center_finite_diff_n (mse11, 1,  False, 0, 1) )
    omse22 =  mse22
    omse22 =  wap2 *  tofloat( center_finite_diff_n (mse22, 1,  False, 0, 1) )
    omse_clim1 = mse_clim1
    omse_clim1 = wap_clim *  tofloat( center_finite_diff_n (mse_clim1, 1,  False, 0, 1) )
    
;;;  make vertical integral :
   omse1     = dim_sum_n_Wrap( omse11 , 1)/gg
   omse2     = dim_sum_n_Wrap( omse22 , 1)/gg
   omse_clim = dim_sum_n_Wrap( omse_clim1 , 1)/gg
;;;; output as netCDF

       dimNames = (/ "lat", "lon"/) ;;  (/"time",  "lat", "lon"/)
       dimSizes = (/ ydim,  xdim /) ;;  (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ False, False/) ;;   (/ True , False, False/)

       copy_VarCoords( hus1(:,0,:,:), omse1)
       tadv1@standard_name = standardname(iv)
       tadv1@units  = unitout(iv)

       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;;;   ELNINO
       fileout  = nameout + "/ELNINO/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "omse", typeof(omse1),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "omse", omse1)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->omse  = (/omse1/)
       delete( fout)
;;    LANINA
      fileout  = nameout + "/LANINA/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "omse", typeof(omse2),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "omse", omse2)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->omse  = (/omse2/)
       delete( fout)
 
;;;   CLIMA
       fileout  = nameout + "/MSE_" + Varsout(iv) + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  "omse", typeof(omse_clim),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, "omse", omse_clim)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->omse  = (/omse_clim/)
       delete( fout)

end
