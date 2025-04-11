;;;;   to get the MSE variance and covariance  data for plotting   
;;;   
  
 
begin

      varcode = getenv ("POD_HOME")
      vardata  = getenv("OBS_DATA")  + "/DATA/"           ; model input
      outdir  = getenv("ENSO_MSE_WKDIR_MSE_VAR") + "/obs" ; envvar set in ENSO_MSE.py
      case =  getenv( "CASENAME")

     mode = (/ "ELNINO", "LANINA" /)

;; custom lon lat:  slon1, slon2, slat1, slat2
       slon1 = tofloat( getenv("slon1"))
       slon2 = tofloat( getenv("slon2"))
       slat1 = tofloat( getenv("slat1"))
       slat2 = tofloat( getenv("slat2"))

;;; get the two pre-determined longitudes/latitudes of Central and Eastern Pacific 

   lon1 = (/ 160., 220., -9999. /)
   lon2 = (/ 200., 280., -9999. /)

   lat1 = (/ -10., -5., -9999. /)
   lat2 = (/   5.,  5., -9999. /)

   lon1(2) = slon1
   lon2(2) = slon2
   lat1(2) = slat1
   lat2(2) = slat2
  

    vvar1 = (/ "hfss", "hfls", "sw", "lw" /)
    vvar2 = (/ "mse",  "madv", "tadv",  "omse" /)

     tt0 = 0 
    nameout = (/ "MSE_variance_C.nc", "MSE_variance_E.nc", "MSE_variance_general.nc" /)

;;    MSE_madv.out  MSE_mdiv.out  MSE_mse.out  MSE_omse.out  MSE_tadv.out
;;;   read in the input data - full  + clima to make anomalies
     do n = 0, 1

     mmode = mode(n) 
     iv = 0 

     Varname = vvar2(iv) 
     namein = vardata +  "/netCDF/"  +  mmode + "/MSE_" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/MSE_"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      mse  = vvar 
      mse  = vvar - clima 
      delete([/ fin1, fin2 /])
;;   define  all other variables ..   MADV
     iv = 1  
     Varname = vvar2(iv)
     namein = vardata +  "/netCDF/"  +  mmode + "/MSE_" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/MSE_"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      madv  = vvar
      madv  = vvar - clima
      delete([/ fin1, fin2 /])
;;;;   TADV
      iv = 2
     Varname = vvar2(iv)
     namein = vardata +  "/netCDF/"  +  mmode + "/MSE_" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/MSE_"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      tadv  = vvar
      tadv  = vvar - clima
      delete([/ fin1, fin2 /])
;;;;;;;;;;;;;;;     omse
     iv = 3
     Varname = vvar2(iv)
     namein = vardata +  "/netCDF/"  +  mmode + "/MSE_" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/MSE_"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      omse  = vvar
      omse  = vvar - clima
      delete([/ fin1, fin2 /])

;;;;;;;;;;;;;;  COMPOSITES SHF 
      iv = 0 
      Varname = vvar1(iv)

     namein = vardata +  "/netCDF/"  +  mmode + "/" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      shf  = vvar
      shf  = vvar - clima
      delete([/ fin1, fin2 /])
;;;;;;;;;;;;;;  COMPOSITES LHF
     iv = 1
      Varname = vvar1(iv)
      namein = vardata +  "/netCDF/"  +  mmode + "/" + Varname + ".nc"
      nameclima = vardata +  "/netCDF/"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      lhf  = vvar
      lhf  = vvar - clima
      delete([/ fin1, fin2 /])
;;;; ;   SW
     iv = 2
      Varname = vvar1(iv)
     namein = vardata +  "/netCDF/"  +  mmode + "/" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      sw  = vvar
      sw  = vvar - clima
      delete([/ fin1, fin2 /])
;;;; ;   LW
      iv = 3
      Varname = vvar1(iv)

     namein = vardata +  "/netCDF/"  +  mmode + "/" + Varname + ".nc"
     nameclima = vardata +  "/netCDF/"  + Varname + "_clim.nc"

     fin1 = addfile(   namein, "r")
     fin2 = addfile( nameclima, "r")

     lat = (fin1->lat)
     lon = (fin1->lon)

       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      vvar     = fin1->$Varname$
      clima    = fin2->$Varname$

      lw  = vvar
      lw  = vvar - clima
      delete([/ fin1, fin2 /])
;;;;;  calculate the variances and covariances then average over select domains C. E. or custom 
     mse0 = mse
     mse0 = mse * mse
 
     madv0 = madv
     madv0 = madv * mse
    
     tadv0 = tadv
     tadv0 = tadv * mse
         
     omse0 = omse
     omse0 = omse * mse

     shf0 = shf 
     shf0 = shf * mse

     lhf0 = lhf 
     lhf0 = lhf * mse

     sw0 = sw
     sw0 = sw * mse

     lw0 = lw
     lw0 = lw * mse
;;;   define output variable
    ydim8 = 8
    output = new( (/  ydim8 /), float)
    output@standard_name = "covariance"
    output@_FillValue = mse@_FillValue   
    output@units = " " 

     
     dimNames = (/ "xdim"  /) ;;  
     dimSizes = (/ ydim8 /) ;;  
     dimUnlim = (/ False /) ;;   

    do i = 0, 2
     output(0) = wgt_areaave_Wrap( mse0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(1) = wgt_areaave_Wrap( omse0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(2) = wgt_areaave_Wrap( madv0(tt0,  {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(3) = wgt_areaave_Wrap( tadv0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(4) = wgt_areaave_Wrap( sw0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(5) = wgt_areaave_Wrap( lw0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(6) = wgt_areaave_Wrap( shf0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
     output(7) = wgt_areaave_Wrap( lhf0(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)


      fileout = outdir +  "/netCDF/"  +  mmode + "/" +  nameout(i)  ;;;  "MSE_variance_C.out"

       kk = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes
 
       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "output", typeof(output),  dimNames )
 
       filevarattdef(fout, "output", output)

       setfileoption(fout,"DefineMode",False)
       fout->output = (/output/)
;;   
   
    end do ;;; over domains 

    end do 
      
end
