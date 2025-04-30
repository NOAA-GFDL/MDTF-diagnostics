;;; to get the seasonal DJF timeseries of SST for ENSO selection

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin

      varcode = getenv ("POD_HOME")
      vardata  = getenv("DATADIR")                     ; model input
      outdir  = getenv("ENSO_MSE_WKDIR_COMPOSITE") + "/model/" ; envvar set in ENSO_MSE.py
      case =  getenv( "CASENAME")
      codedata = getenv ("POD_HOME")

      iy1 = toint( ( getenv("FIRSTYR")) )
      iy2 = toint( (  getenv("LASTYR")) )

      Vars3 = (/ "zg", "ua", "va", "ta", "hus", "wap" /)
      ivar3 = dimsizes( Vars3)
      unit3 = (/ "m", "m/s", "m/s", "K", "kg/kg", "Pa/s" /) 
      standardname3 = (/ "geopotential_height", "eastward_wind", "northward_wind", \
                     "air_temperature" ,  "specific_humidity", "lagrangian_tendency_of_air_pressure" /)

      Vars2 = (/ "pr", "ts", "hfss", "hfls" /)
      ivar2 = dimsizes( Vars2)
      unit2 = (/ "kg/m2/s" , "K",  "W/m2", "W/m2" /)
      standardname2 = (/ "precipitation_flux", "surface_temperature",   \
                 "surface_upward_sensible_heat_flux", "surface_upward_latent_heat_flux" /)

;;;  radiation 
      VarsLW = (/ "rlds", "rlus", "rlut" /)
      ivarLW = dimsizes( VarsLW) 
      VarsSW = (/ "rsds", "rsdt", "rsus", "rsut" /)
      ivarSW = dimsizes( VarsSW) 
       
      unitRAD =  "W/m2"
      standardnameSW = "net_shortwave_flux"
      standardnameLW = "net_longwave_flux" 

;;;  correlation + regression
      VarsC = (/ "pr", "sw", "lw",  "hfss", "hfls" /)
      ivarC = dimsizes( VarsC)
      unitR = (/ "kg/m2/s/K" , "W/m2/K",  "W/m2/K", "W/m2/K", "W/m2/K" /)

      standardnameC = (/ "precipitation_flux_sst_correlation",   \
                         "net_shortwave_flux_sst_correlation",   \
                         "net_longwave_flux_sst_correlation",   \
                         "surface_upward_sensible_heat_flux_sst_correlation", \
                         "surface_upward_latent_heat_flux_sst_correlation" /)
      standardnameR  =  (/ "precipitation_flux_sst_regression",   \
                         "net_shortwave_flux_sst_regression",   \
                         "net_longwave_flux_sst_regression",   \
                         "surface_upward_sensible_heat_flux_sst_regression", \
                         "surface_upward_latent_heat_flux_sst_regression" /)
	

      id3   = 1; 
      id2   = 1; 
      idrad = 1; 
      idcor = 1;
;; radiation separate 

    print( "started " +  systemfunc ("date") ) 

;;  get the monthly clima and  anomaly of SST
    namein1   = vardata +  "/mon/"
    nameout   =  outdir + "/netCDF/"
    nameclima =  outdir + "/netCDF/"
  
    Varname = "ts"
    namein = namein1 + case + "." + Varname + ".mon.nc"
    fin = addfile( namein, "r")

      lat = fin->lat
      lon = fin->lon
      time0 = fin->time
      time0@calendar  ="standard"
      time2 = calendar_decode2( time0 ,  -5)
      ts = fin->$Varname$

      tdim  = dimsizes( time0)      
;;   read parameter.txt to get the seasons 
       parameter_name = varcode + "/shared/parameters.txt"
       line = asciiread(parameter_name,-1,"string")
      
       xdum = str_get_field(line(0), 3," ")
       lon1 =  stringtofloat( xdum)
       xdum = str_get_field(line(1), 3," ")
       lon2 =  stringtofloat( xdum)
       xdum = str_get_field(line(2), 3," ")
       lat1 =  stringtofloat( xdum)
       xdum = str_get_field(line(3), 3," ")
       lat2 =  stringtofloat( xdum)
       xdum = str_get_field(line(4), 3," ")
       sigma34 =  stringtofloat( xdum)
       xdum = str_get_field(line(5), 3," ")
       im1  = stringtointeger( xdum)
       xdum = str_get_field(line(6), 3," ")
       im2  = stringtointeger( xdum)
;;;  parameters defined 
;;;  define monthly climatology 
     clima = clmMonTLL ( ts) 
;;  define monthly anomaly
     anom = calcMonAnomTLL ( ts, clima)
     anom_sst = anom
;;output 
;;; collect the sigma in Nino3.4 
;;      anom = anom
      anom_sst2 =  wgt_areaave_Wrap(  anom(:, {lat1:lat2},  {lon1:lon2}), 1., 1., 0)

      sigma2 = 0.
      ss = 0.
	do it = 0, tdim - 1
        im  = time2(it, 1)
        if(  (im .ge. im1) .or. (im .le. im2) )
         sigma2 = sigma2 +  anom_sst2(it) * anom_sst2(it)
         ss = ss + 1.
        end if
      end do

      if( ss .gt. 0.) 
       sigma2 =  sqrt(sigma2/ss)
       else
       sigma2 = ts@_FillValue
      end if

;;	print( sigma2 + " ")
;;;  make the anomaly seasonal  average im1:im2 
;;;   select the elnino/lanina years 
      itd = im2 - im1 
      if( im2 .lt. im1) 
       itd = im2 +12 - im1
      end if 

     tdim2 = iy2 - iy1 + 1
     iyelnino = new(  tdim2, "integer") 
     iyelnino@_FillValue = -9999
     iyelnino = -9999
     iylanina = iyelnino

     ii1 = 0
     ii2 = 0
     do iy = iy1, iy2-1

        it1 = (iy - iy1) * 12 + im1 - 1
        it2 = it1 + itd
        xanom = wgt_areaave_Wrap( anom(it1:it2, {lat1:lat2},  {lon1:lon2}), 1., 1., 0)
       
        xanom2 = dim_avg_n_Wrap(xanom,0)

       if( xanom2 .ge.  (sigma34*sigma2) ) 	
        iyelnino(ii1) = iy
        ii1 = ii1 + 1
       end if
       if( xanom2 .le. (-sigma34*sigma2) )
         iylanina(ii2) = iy
         ii2 = ii2 + 1
       end if
     end do        
     itmax1 = ii1
     itmax2 = ii2
;;;;   print diagnostic messages
       if( itmax1 .le. 0) 
       print("WARNING: The number of  El Nino events is :" + itmax1 ) 
       print("At least 1 event is needed for calculation ")
       print("and at least 2 events for sucessfull completion")
       print("Please, extend the time span of your Model data")
       end if 
  
       if( itmax1 .eq. 1)
       print("WARNING: The number of  El Nino events is : " + itmax1)
       print("At least 2 events are needed for successful  calculations ")
       print("The code will run just with 1 event, but with limited results")
       print("You may  extend the time span of your Model data")
       end if 

       if( itmax1 .gt. 1) 
       print ("The number of  El Nino events is : "  + itmax1)
       print ("The code will proceed  with this number of El Nino events")
       end if 

       if( itmax2 .le. 0) 
       print("WARNING: The number of  La Nina events is : "  + itmax2 )
       print("At least 1 event is needed for calculation ")
       print("and at least 2 events for sucessfull completion")
       print("Please, extend the time span of your Model data")
       end if 
  
       if( itmax2 .eq. 1)
       print("WARNING: The number of  La Nina events is : "  + itmax2)
       print("At least 2 events are needed for successful  calculations ")
       print("The code will run just with 1 event, but with limited results")
       print("You may  extend the time span of your Model data")
       end if

       if( itmax2 .gt. 1) 
       print("The number of  El Nino events is : " + itmax2)
       print("The code will proceed  with this number of La Nina events")
       end if 
  
;;;  proceed to get the composites El Nino/La Nina  for all variables 3D and 2D 
;;  
     delete( [/lat,lon, time0, time2, anom, clima, fin/])

      if( id3 .eq. 1)        

      do iv = 0, ivar3 - 1
       Varname = Vars3(iv) 
       namein = namein1 + case + "." + Varname + ".mon.nc"
       fin = addfile( namein, "r")
	lat = fin->lat
       lon = fin->lon
       plev = fin->lev
       time0 = fin->time
       time0@calendar  ="standard"
       time2 = calendar_decode2( time0 ,  -5)

       tdim = dimsizes(time0)     ; get dimension sizes
       zdim = dimsizes(plev)
       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      datain = fin->$Varname$
;;;   define the climatology and the anomaly for 24month development
      clima = clmMonTLLL ( datain)
      anom = calcMonAnomTLLL ( datain, clima)

       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   zdim,  ydim,  xdim /)
       dimUnlim = (/ True , False, False, False/)

       clima2 = new( dimSizes, "float")
       clima2 =  0.
       clima2@_FillValue = datain@_FillValue
       ss2 = clima2

;; seasonal average 		 
      itd = im2 - im1
      if( im2 .lt. im1)
       itd = im2 +12 - im1
      end if
	do it = im1, im1 + itd
         it2 = it
         if( it2 .gt. 12) 
         it2 = it2 - 12
	  end if
         it2  = it2 - 1
         
        clima2(0, :, :, :) =  where( .not. ismissing(clima(it2, :, :, :)), clima2(0, :, :, :) + clima(it2, :, :, :), clima2(0, :, :, :) )
         ss2(0, :, :, :)  =  where( .not. ismissing( clima(it2, :, :, :)),  ss2(0, :, :, :) + 1., ss2(0, :, :, :))
       end do   
;;; average 
        ss2 =  where( ss2 .gt. 0., ss2, datain@_FillValue) 
        clima2 = where( .not. ismissing(ss2), clima2/ss2, datain@_FillValue)         
;;;  write out    seasonal  climatology
       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

       fileout  =  nameclima + "/" + Varname + "_" + "clim.nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       lon!0 = "lon"
       lon@units = "degrees_east"
       lon@_FillValue = datain@_FillValue
       lon@long_name = "longitude"

       lat!0 = "lat"
       lat@units = "degrees_north"
       lat@long_name = "latitude"
       lat@_FillValue = datain@_FillValue

       plev!0 = "lev"
       plev@units  = "mb"
       plev@long_name = "pressure levels "
       plev@_FillValue = datain@_FillValue

;; define units and standard name 
       clima2@standard_name = standardname3(iv) 
       clima2@units = unit3(iv) 

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  Varname, typeof(clima2),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, Varname, clima2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lev    = (/plev/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname$  = (/clima2/)

       delete( [/ fout, timeout, clima2, ss2 /] )
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;     next  24 month evolution composite
       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1,   zdim,  ydim,  xdim /)
       dimUnlim = (/ True , False, False, False/)
       dimSizes24 = (/ 24,   zdim,  ydim,  xdim /)

	elnino24 = new( dimSizes24, "float")
       elnino24 = 0.
	elnino24@_FillValue = datain@_FillValue
       ss2 =  elnino24
       lanina24 = elnino24
       ss22 =  elnino24
  
       do it = 0 ,itmax1 - 1
         it1 = (iyelnino(it) - iy1) * 12 
         it2 = it1 + 23
       elnino24(0:23, :, :, :) =  where( .not. ismissing( anom(it1:it2, :, :, :)), elnino24(0:23, :, :, :) + anom(it1:it2, :, :, :), elnino24(0:23, :, :, :) )
         ss2(0:23, :, :, :)  =  where( .not. ismissing( anom(it1:it2, :, :, :)),  ss2(0:23, :, :, :) + 1.,  ss2(0:23, :, :, :) ) 
       end do 
	
	do it = 0 ,itmax2 - 1
           it1 = (iylanina(it) - iy1) * 12
           it2 = it1 + 23
       lanina24(0:23, :, :, :) =  where( .not. ismissing( anom(it1:it2, :, :, :)), lanina24(0:23, :, :, :) + anom(it1:it2, :, :, :), lanina24(0:23, :, :, :) )
         ss22(0:23, :, :, :)  =  where( .not. ismissing( anom(it1:it2, :, :, :)),  ss22(0:23, :, :, :) + 1.,  ss22(0:23, :, :, :) ) 
       end do
      
	 ss2 =  where( ss2 .gt. 0., ss2, datain@_FillValue)
       elnino24 = where( .not. ismissing(ss2), elnino24/ss2, datain@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datain@_FillValue)
       lanina24 = where( .not. ismissing(ss22), lanina24/ss22, datain@_FillValue)
       
;;;;  output 
       timeout = new( 24, typeof(time0) )
       timeout(0:23)  = time0(0:23)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

;; define units and standard name
       elnino24@standard_name = standardname3(iv)
       elnino24@units = unit3(iv) 
	lanina24@standard_name = standardname3(iv)
       lanina24@units = unit3(iv)


       fileout1  = nameout + "/24MONTH_ELNINO/" + Varname + ".nc"
       fileout2  = nameout + "/24MONTH_LANINA/" + Varname + ".nc"
	
       print("fileout =  "  +  fileout1 + " " + fileout2)

       n = systemfunc( " rm " +  fileout1 + " 2> /dev/null")
       n = systemfunc( " rm " +  fileout2 + " 2> /dev/null")

       fout1 = addfile( fileout1 ,"c")
       setfileoption(fout1,"DefineMode",True)
       fout2 = addfile( fileout2 ,"c")
       setfileoption(fout2,"DefineMode",True)

	filedimdef(fout1, dimNames, dimSizes24, dimUnlim)

       filevardef(fout1, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout1, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout1, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout1, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout1,  Varname, typeof(elnino24),  dimNames )

       filevarattdef(fout1, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout1, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout1, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout1, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout1, Varname, elnino24)

       setfileoption(fout1,"DefineMode",False)
       fout1->time   = (/timeout/)
       fout1->lev    = (/plev/)
       fout1->lat    = (/lat/)
       fout1->lon    = (/lon/)
       fout1->$Varname$  = (/elnino24/)

	filedimdef(fout2, dimNames, dimSizes24, dimUnlim)

       filevardef(fout2, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout2, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout2, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout2, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout2,  Varname, typeof(lanina24),  dimNames )

       filevarattdef(fout2, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout2, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout2, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout2, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout2, Varname, lanina24)

       setfileoption(fout1,"DefineMode",False)
       fout2->time   = (/timeout/)
       fout2->lev    = (/plev/)
       fout2->lat    = (/lat/)
       fout2->lon    = (/lon/)
       fout2->$Varname$  = (/lanina24/)

       delete( [/fout1, fout2, timeout,  elnino24, lanina24, ss2, ss22 /] )

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;  lastly the seasonal composite 
       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   zdim,  ydim,  xdim /)
       dimUnlim = (/ True , False, False, False/)

       elnino = new( dimSizes, "float")
       elnino = 0.
       elnino@_FillValue = datain@_FillValue
       ss2 =  elnino
       lanina = elnino
       ss22 =  elnino

        do itt = 0 ,itmax1 - 1
         it1 = (iyelnino(itt) - iy1) * 12  + im1 - 1
         it2 = it1 + itd
       do it = it1, it2
       elnino(0, :, :, :) =  where( .not. ismissing( datain(it, :, :, :)), elnino(0, :, :, :) + datain(it, :, :, :), elnino(0, :, :, :) )
         ss2(0, :, :, :)  =  where( .not. ismissing( datain(it, :, :, :)),  ss2(0, :, :, :) + 1.,  ss2(0, :, :, :) )
       end do
       end do 

       do itt = 0 ,itmax2 - 1
           it1 = (iylanina(itt) - iy1) * 12 + im1 - 1
           it2 = it1 + itd
        do it = it1, it2
       lanina(0, :, :, :) =  where( .not. ismissing( datain(it, :, :, :)), lanina(0, :, :, :) + datain(it, :, :, :), lanina(0, :, :, :) )
         ss22(0:, :, :, :)  =  where( .not. ismissing( datain(it, :, :, :)),  ss22(0, :, :, :) + 1.,  ss22(0, :, :, :) )
       end do
       end do 

        ss2 =  where( ss2 .gt. 0., ss2, datain@_FillValue)
       elnino = where( .not. ismissing(ss2), elnino/ss2, datain@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datain@_FillValue)
       lanina = where( .not. ismissing(ss22), lanina/ss22, datain@_FillValue)

;;;  write out to external  netCDF files  
      timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

;; define units and standard name
       elnino@standard_name = standardname3(iv)
       elnino@units = unit3(iv)
       lanina@standard_name = standardname3(iv)
       lanina@units = unit3(iv)

       fileout1  = nameout + "/ELNINO/" + Varname + ".nc"
       fileout2  = nameout + "/LANINA/" + Varname + ".nc"

       n = systemfunc( " rm " +  fileout1 + " 2> /dev/null")
       n = systemfunc( " rm " +  fileout2 + " 2> /dev/null")

       fout1 = addfile( fileout1 ,"c")
       setfileoption(fout1,"DefineMode",True)
       fout2 = addfile( fileout2 ,"c")
       setfileoption(fout2,"DefineMode",True)

       filedimdef(fout1, dimNames, dimSizes24, dimUnlim)

       filevardef(fout1, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout1, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout1, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout1, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout1,  Varname, typeof(elnino),  dimNames )

       filevarattdef(fout1, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout1, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout1, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout1, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout1, Varname, elnino)

       setfileoption(fout1,"DefineMode",False)
       fout1->time   = (/timeout/)
       fout1->lev    = (/plev/)
       fout1->lat    = (/lat/)
       fout1->lon    = (/lon/)
       fout1->$Varname$  = (/elnino/)

        filedimdef(fout2, dimNames, dimSizes24, dimUnlim)

       filevardef(fout2, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout2, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout2, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout2, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout2,  Varname, typeof(lanina),  dimNames )

       filevarattdef(fout2, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout2, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout2, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout2, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout2, Varname, lanina)

       setfileoption(fout1,"DefineMode",False)
       fout2->time   = (/timeout/)
       fout2->lev    = (/plev/)
       fout2->lat    = (/lat/)
       fout2->lon    = (/lon/)
       fout2->$Varname$  = (/lanina/)

       delete( [/fout1, fout2, timeout,  elnino, lanina, ss2, ss22 /] )

       delete( [/ fin, datain,  anom, clima /])

      print( " finished variable "  + Varname + " "  +  systemfunc ("date") )

      end do   ;; over 3D variables a
      delete( [/ dimNames, dimSizes, dimUnlim, dimSizes24 /])
      delete( [/lat,lon, plev, time0, time2 /])

      end if 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;   2D Variables 
 
      if( id2 .eq. 1 ) 
      do iv = 0, ivar2 - 1
       Varname = Vars2(iv)
     
       namein = namein1 + case + "." + Varname + ".mon.nc"
       fin = addfile( namein, "r")
       lat = fin->lat
       lon = fin->lon
       time0 = fin->time
       time0@calendar  ="standard"
       time2 = calendar_decode2( time0 ,  -5)

       tdim = dimsizes(time0)     ; get dimension sizes
       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      datain = fin->$Varname$
;;;   define the climatology and the anomaly for 24month development
      clima = clmMonTLL ( datain)
;;  define monthly anomaly 
      anom = calcMonAnomTLL ( datain, clima)
       dimNames = (/"time",  "lat", "lon"/)
       dimSizes = (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ True , False, False/)
       
       clima2 = new( dimSizes, "float")
       clima2 =  0.
       clima2@_FillValue = datain@_FillValue
       ss2 = clima2
;; seasonal average
      itd = im2 - im1
      if( im2 .lt. im1)
       itd = im2 +12 - im1
      end if
       do it = im1, im1 + itd
         it2 = it
         if( it2 .gt. 12)
         it2 = it2 - 12
         end if
         it2  = it2 - 1

        clima2(0, :, :) =  where( .not. ismissing(clima(it2, :, :)), clima2(0,:, :) + clima(it2, :, :), clima2(0, :, :) )
         ss2(0, :, :)  =  where( .not. ismissing( clima(it2, :, :)),  ss2(0, :, :) + 1., ss2(0, :, :))
       end do
;;; average
        ss2 =  where( ss2 .gt. 0., ss2, datain@_FillValue)
        clima2 = where( .not. ismissing(ss2), clima2/ss2, datain@_FillValue)
;;;  write out    seasonal  climatology
       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

;; define units and standard name
       clima2@standard_name = standardname2(iv)
       clima2@units = unit2(iv)

       fileout  =  nameclima + "/" + Varname + "_" + "clim.nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)
       
       lon!0 = "lon"
       lon@units = "degrees_east"
       lon@_FillValue = datain@_FillValue
       lon@long_name = "longitude"

       lat!0 = "lat"
       lat@units = "degrees_north"
       lat@long_name = "latitude"
       lat@_FillValue = datain@_FillValue

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  Varname, typeof(clima2),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, Varname, clima2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname$  = (/clima2/)

       delete( [/ fout, timeout, clima2, ss2 /] )
       
;;     next  24 month evolution composite
       dimNames = (/"time", "lat", "lon"/)
       dimSizes = (/ 1 ,  ydim,  xdim /)
       dimUnlim = (/ True ,  False, False/)
       dimSizes24 = (/ 24,  ydim,  xdim /)

       elnino24 = new( dimSizes24, "float")
       elnino24 = 0.
       elnino24@_FillValue = datain@_FillValue
       ss2 =  elnino24
       lanina24 = elnino24
       ss22 =  elnino24

       do it = 0 ,itmax1 - 1
         it1 = (iyelnino(it) - iy1) * 12
         it2 = it1 + 23
       elnino24(0:23, :, :) =  where( .not. ismissing( anom(it1:it2, :, :)), elnino24(0:23, :, :) + anom(it1:it2,  :, :), elnino24(0:23, :, :) )
         ss2(0:23, :, :)  =  where( .not. ismissing( anom(it1:it2, :, :)),  ss2(0:23, :, :) + 1.,  ss2(0:23, :, :) )
       end do

       do it = 0 ,itmax2 - 1
           it1 = (iylanina(it) - iy1) * 12
           it2 = it1 + 23
       lanina24(0:23, :, :) =  where( .not. ismissing( anom(it1:it2, :, :)), lanina24(0:23, :, :) + anom(it1:it2, :, :), lanina24(0:23, :, :) )
         ss22(0:23, :, :)  =  where( .not. ismissing( anom(it1:it2, :, :)),  ss22(0:23, :, :) + 1.,  ss22(0:23, :, :) )
       end do

        ss2 =  where( ss2 .gt. 0., ss2, datain@_FillValue)
       elnino24 = where( .not. ismissing(ss2), elnino24/ss2, datain@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datain@_FillValue)
       lanina24 = where( .not. ismissing(ss22), lanina24/ss22, datain@_FillValue)

;;;;  output
       timeout = new( 24, typeof(time0) )
       timeout(0:23)  = time0(0:23)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;; define units and standard name
       elnino24@standard_name = standardname2(iv)
       elnino24@units = unit2(iv)
       lanina24@standard_name = standardname2(iv)
       lanina24@units = unit2(iv)

       fileout1  = nameout + "/24MONTH_ELNINO/" + Varname + ".nc"
       fileout2  = nameout + "/24MONTH_LANINA/" + Varname + ".nc"

       n = systemfunc( " rm " +  fileout1 + " 2> /dev/null")
       n = systemfunc( " rm " +  fileout2 + " 2> /dev/null")

       fout1 = addfile( fileout1 ,"c")
       setfileoption(fout1,"DefineMode",True)
       fout2 = addfile( fileout2 ,"c")
       setfileoption(fout2,"DefineMode",True)

       filedimdef(fout1, dimNames, dimSizes24, dimUnlim)

       filevardef(fout1, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout1, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout1, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout1,  Varname, typeof(elnino24),  dimNames )

       filevarattdef(fout1, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout1, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout1, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout1, Varname, elnino24)

       setfileoption(fout1,"DefineMode",False)
       fout1->time   = (/timeout/)
       fout1->lat    = (/lat/)
       fout1->lon    = (/lon/)
       fout1->$Varname$  = (/elnino24/)

       filedimdef(fout2, dimNames, dimSizes24, dimUnlim)

       filevardef(fout2, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout2, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout2, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout2,  Varname, typeof(lanina24),  dimNames )

       filevarattdef(fout2, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout2, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout2, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout2, Varname, lanina24)

      setfileoption(fout1,"DefineMode",False)
       fout2->time   = (/timeout/)
       fout2->lat    = (/lat/)
       fout2->lon    = (/lon/)
       fout2->$Varname$  = (/lanina24/)

       delete( [/fout1, fout2, timeout,  elnino24, lanina24, ss2, ss22 /] )
       
;;;;  lastly the seasonal composite
       dimNames = (/"time",  "lat", "lon"/)
       dimSizes = (/ 1 ,    ydim,  xdim /)
       dimUnlim = (/ True , False, False/)

       elnino = new( dimSizes, "float")
       elnino = 0.
       elnino@_FillValue = datain@_FillValue
       ss2 =  elnino
       lanina = elnino
       ss22 =  elnino

        do itt = 0 ,itmax1 - 1
         it1 = (iyelnino(itt) - iy1) * 12  + im1 - 1
         it2 = it1 + itd
       do it = it1, it2
       elnino(0, :, :) =  where( .not. ismissing( datain(it, :, :)), elnino(0, :, :) + datain(it, :, :), elnino(0, :, :) )
         ss2(0, :, :)  =  where( .not. ismissing( datain(it, :, :)),  ss2(0, :, :) + 1.,  ss2(0, :, :) )
       end do
       end do

       do itt = 0 ,itmax2 - 1
           it1 = (iylanina(itt) - iy1) * 12 + im1 - 1
           it2 = it1 + itd
        do it = it1, it2
       lanina(0, :, :) =  where( .not. ismissing( datain(it, :, :)), lanina(0, :, :) + datain(it, :, :), lanina(0, :, :) )
         ss22(0:, :, :)  =  where( .not. ismissing( datain(it, :, :)),  ss22(0, :, :) + 1.,  ss22(0, :, :) )
       end do
       end do

        ss2 =  where( ss2 .gt. 0., ss2, datain@_FillValue)
       elnino = where( .not. ismissing(ss2), elnino/ss2, datain@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datain@_FillValue)
       lanina = where( .not. ismissing(ss22), lanina/ss22, datain@_FillValue)

;;;  write out to external  netCDF files
       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;; define units and standard name
       elnino@standard_name = standardname2(iv)
       elnino@units = unit2(iv)
       lanina@standard_name = standardname2(iv)
       lanina@units = unit2(iv)

       fileout1  = nameout + "/ELNINO/" + Varname + ".nc"
       fileout2  = nameout + "/LANINA/" + Varname + ".nc"

       n = systemfunc( " rm " +  fileout1 + " 2> /dev/null")
       n = systemfunc( " rm " +  fileout2 + " 2> /dev/null")

       fout1 = addfile( fileout1 ,"c")
       setfileoption(fout1,"DefineMode",True)
       fout2 = addfile( fileout2 ,"c")
       setfileoption(fout2,"DefineMode",True)

       filedimdef(fout1, dimNames, dimSizes24, dimUnlim)

       filevardef(fout1, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout1, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout1, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout1,  Varname, typeof(elnino),  dimNames )
        
       filevarattdef(fout1, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout1, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout1, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout1, Varname, elnino)

       setfileoption(fout1,"DefineMode",False)
       fout1->time   = (/timeout/)
       fout1->lat    = (/lat/)
       fout1->lon    = (/lon/)
       fout1->$Varname$  = (/elnino/)

        filedimdef(fout2, dimNames, dimSizes24, dimUnlim)

       filevardef(fout2, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout2, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout2, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout2,  Varname, typeof(lanina),  dimNames )

       filevarattdef(fout2, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout2, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout2, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout2, Varname, lanina)

       setfileoption(fout1,"DefineMode",False)
       fout2->time   = (/timeout/)
       fout2->lat    = (/lat/)
       fout2->lon    = (/lon/)
       fout2->$Varname$  = (/lanina/)

       delete( [/fout1, fout2, timeout,  elnino, lanina, ss2, ss22 /] )

       delete( [/ fin, datain,   anom, clima /])

      print( " finished variable "  + Varname + " "  +  systemfunc ("date") )
      
   end do ;; over 2D variables 
    delete( [/ dimNames, dimSizes, dimUnlim, dimSizes24 /])
   end if


;;; last is the radiation 
;;    make the net SW and LW first 
 
      if( idrad .eq. 1) 
       Varname = VarsLW(0)
       namein11 = namein1 + case + "." + Varname + ".mon.nc"
       fin1 = addfile( namein11, "r")
       datain1 = fin1->$Varname$
       Varname = VarsLW(1)
       namein22 = namein1 + case + "." + Varname + ".mon.nc"
       fin2 = addfile( namein22, "r")
       datain2 = fin2->$Varname$
       Varname = VarsLW(2)
       namein33 = namein1 + case + "." + Varname + ".mon.nc"
       fin3 = addfile( namein33, "r")
       datain3 = fin3->$Varname$
       datainLW = datain2
       datainLW = datain2 - datain1 - datain3 
       delete( [/ fin1, fin2, fin3, datain1, datain2, datain3 /] )
;;;  similar for SW 
       Varname = VarsSW(0)
       namein11 = namein1 + case + "." + Varname + ".mon.nc"
       fin1 = addfile( namein11, "r")
       datain1 = fin1->$Varname$
       Varname = VarsSW(1)
       namein22 = namein1 + case + "." + Varname + ".mon.nc"
       fin2 = addfile( namein22, "r")
       datain2 = fin2->$Varname$
       Varname = VarsSW(2)
       namein33 = namein1 + case + "." + Varname + ".mon.nc"
       fin3 = addfile( namein33, "r")
       datain3 = fin3->$Varname$
       Varname = VarsSW(3)
       namein44 = namein1 + case + "." + Varname + ".mon.nc"
       fin4 = addfile( namein44, "r")
       datain4 = fin4->$Varname$
       datainSW = datain2
	datainSW = datain2 - datain1 + datain3 - datain4

       lat = fin1->lat
       lon = fin1->lon
       time0 = fin1->time
       time0@calendar  ="standard"
       time2 = calendar_decode2( time0 ,  -5)

       tdim = dimsizes(time0)     ; get dimension sizes
       ydim = dimsizes(lat)
       xdim = dimsizes(lon)
;;;;    seasonal clima
       climaLW = clmMonTLL ( datainLW)
       anomLW = calcMonAnomTLL ( datainLW, climaLW)
       climaSW = clmMonTLL ( datainSW)
       anomSW = calcMonAnomTLL ( datainSW, climaSW)

       dimNames = (/"time",  "lat", "lon"/)
       dimSizes = (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ True , False, False/)

       climaLW2 = new( dimSizes, "float")
       climaLW2 =  0.
       climaLW2@_FillValue = datainLW@_FillValue
       ssLW2 = climaLW2
       climaSW2 = new( dimSizes, "float")
       climaSW2 =  0.
       climaSW2@_FillValue = datainSW@_FillValue
       ssSW2 = climaSW2

; seasonal average
      itd = im2 - im1
      if( im2 .lt. im1)
       itd = im2 +12 - im1
      end if
       do it = im1, im1 + itd
         it2 = it
         if( it2 .gt. 12)
         it2 = it2 - 12
         end if
         it2  = it2 - 1

       climaLW2(0, :, :) =  where( .not. ismissing(climaLW(it2, :, :)), climaLW2(0,:, :) + climaLW(it2, :, :), climaLW2(0, :, :) )
         ssLW2(0, :, :)  =  where( .not. ismissing( climaLW(it2, :, :)),  ssLW2(0, :, :) + 1., ssLW2(0, :, :))

       climaSW2(0, :, :) =  where( .not. ismissing(climaSW(it2, :, :)), climaSW2(0,:, :) + climaSW(it2, :, :), climaSW2(0, :, :) )
         ssSW2(0, :, :)  =  where( .not. ismissing( climaSW(it2, :, :)),  ssSW2(0, :, :) + 1., ssSW2(0, :, :))

       end do
;;; average
        ssLW2 =  where( ssLW2 .gt. 0., ssLW2, datainLW@_FillValue)
        climaLW2 = where( .not. ismissing(ssLW2), climaLW2/ssLW2, datainLW@_FillValue)
        ssSW2 =  where( ssSW2 .gt. 0., ssSW2, datainSW@_FillValue)
        climaSW2 = where( .not. ismissing(ssSW2), climaSW2/ssSW2, datainSW@_FillValue)

;;;  write out    seasonal  climatology
       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"        

       climaLW2@standard_name = standardnameLW

       VarnameLW = "lw"
       climaLW2@units = unitRAD
       climaLW2@standard_name = standardnameLW

       fileout  =  nameclima + "/" + VarnameLW + "_clim.nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       lon!0 = "lon"
       lon@units = "degrees_east"
       lon@_FillValue = datainLW@_FillValue
       lon@long_name = "longitude"

       lat!0 = "lat"
       lat@units = "degrees_north"
       lat@long_name = "latitude"
       lat@_FillValue = datainLW@_FillValue

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameLW, typeof(climaLW2),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameLW, climaLW2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameLW$  = (/climaLW2/)
       delete( fout)  
;;;  the same for SW
       climaSW2@standard_name = standardnameSW

       VarnameSW = "sw"
       climaSW2@standard_name = standardnameSW
       climaSW2@units = unitRAD

       fileout  =  nameclima + "/" + VarnameSW + "_clim.nc"
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
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameSW, typeof(climaSW2),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameSW, climaSW2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameSW$  = (/climaSW2/)
       delete( [/ fout, timeout, climaLW2, ssLW2, climaSW2, ssSW2 /] )

;;;;;;;;;;;;;;;;;;;;;;;;;   24 month Elnino/Lanina evolution composite
       dimNames = (/"time", "lat", "lon"/)
       dimSizes = (/  1,  ydim,  xdim /)
       dimUnlim = (/ True ,  False, False/)
       dimSizes24 = (/ 24,  ydim,  xdim /)

       elnino24 = new( dimSizes24, "float")
       elnino24 = 0.
       elnino24@_FillValue = datainLW@_FillValue
       ss2 =  elnino24
       lanina24 = elnino24
       ss22 =  elnino24

       do it = 0 ,itmax1 - 1
         it1 = (iyelnino(it) - iy1) * 12
         it2 = it1 + 23
       elnino24(0:23, :, :) =  where( .not. ismissing( anomLW(it1:it2, :, :)), elnino24(0:23, :, :) + anomLW(it1:it2,  :, :), elnino24(0:23, :, :) )
         ss2(0:23, :, :)  =  where( .not. ismissing( anomLW(it1:it2, :, :)),  ss2(0:23, :, :) + 1.,  ss2(0:23, :, :) )
       end do

       do it = 0 ,itmax2 - 1
           it1 = (iylanina(it) - iy1) * 12
           it2 = it1 + 23
       lanina24(0:23, :, :) =  where( .not. ismissing( anomLW(it1:it2, :, :)), lanina24(0:23, :, :) + anomLW(it1:it2, :, :), lanina24(0:23, :, :) )
         ss22(0:23, :, :)  =  where( .not. ismissing( anomLW(it1:it2, :, :)),  ss22(0:23, :, :) + 1.,  ss22(0:23, :, :) )
       end do

        ss2 =  where( ss2 .gt. 0., ss2, datainLW@_FillValue)
       elnino24 = where( .not. ismissing(ss2), elnino24/ss2, datainLW@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datainLW@_FillValue)
       lanina24 = where( .not. ismissing(ss22), lanina24/ss22, datainLW@_FillValue)
       
        elninoLW24  = elnino24
        laninaLW24  = lanina24
        delete( [/ elnino24, lanina24 /])
;;  the same for SW
       
       elnino24 = new( dimSizes24, "float")
       elnino24 = 0.
       elnino24@_FillValue = datainSW@_FillValue
       ss2 =   elnino24
       lanina24 = elnino24
       ss22 =  elnino24

       do it = 0 ,itmax1 - 1
         it1 = (iyelnino(it) - iy1) * 12
         it2 = it1 + 23
       elnino24(0:23, :, :) =  where( .not. ismissing( anomSW(it1:it2, :, :)), elnino24(0:23, :, :) + anomSW(it1:it2,  :, :), elnino24(0:23, :, :) )
         ss2(0:23, :, :)  =  where( .not. ismissing( anomSW(it1:it2, :, :)),  ss2(0:23, :, :) + 1.,  ss2(0:23, :, :) )
       end do

       do it = 0 ,itmax2 - 1
           it1 = (iylanina(it) - iy1) * 12
           it2 = it1 + 23
       lanina24(0:23, :, :) =  where( .not. ismissing( anomSW(it1:it2, :, :)), lanina24(0:23, :, :) + anomSW(it1:it2, :, :), lanina24(0:23, :, :) )
         ss22(0:23, :, :)  =  where( .not. ismissing( anomSW(it1:it2, :, :)),  ss22(0:23, :, :) + 1.,  ss22(0:23, :, :) )
       end do

        ss2 =  where( ss2 .gt. 0., ss2, datainSW@_FillValue)
       elnino24 = where( .not. ismissing(ss2), elnino24/ss2, datainSW@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datainSW@_FillValue)
       lanina24 = where( .not. ismissing(ss22), lanina24/ss22, datainSW@_FillValue)

       elninoSW24 = elnino24
       laninaSW24 = lanina24

;;;;  output 
       timeout = new( 24, typeof(time0) )
       timeout(0:23)  = time0(0:23)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

       elninoLW24@standard_name = standardnameLW
       laninaLW24@standard_name = standardnameLW

       VarnameLW = "lw"
       elninoLW24@units = unitRAD
       laninaLW24@units = unitRAD

       fileout  = nameout + "/24MONTH_ELNINO/" + VarnameLW + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes24, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameLW, typeof(elninoLW24),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameLW, elninoLW24)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameLW$  = (/elninoLW24/)
       delete( fout) 
     
       fileout  = nameout + "/24MONTH_LANINA/" + VarnameLW + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes24, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameLW, typeof(laninaLW24),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameLW, laninaLW24)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameLW$  = (/laninaLW24/)
       delete( fout) 
;;;  the same for SW:  
       elninoSW24@standard_name = standardnameSW
       laninaSW24@standard_name = standardnameSW

       VarnameSW = "sw"
       elninoSW24@units = unitRAD
       laninaSW24@units = unitRAD

       fileout  = nameout + "/24MONTH_ELNINO/" + VarnameSW + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes24, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameSW, typeof(elninoSW24),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameSW, elninoSW24)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameSW$  = (/elninoSW24/)
       delete( fout) 

       fileout  = nameout + "/24MONTH_LANINA/" + VarnameSW + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       filedimdef(fout, dimNames, dimSizes24, dimUnlim)
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameSW, typeof(laninaSW24),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameSW, laninaSW24)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameSW$  = (/laninaSW24/)

       delete( [/ fout, timeout,  elninoLW24, laninaLW24, ss2, ss22 /] )
       delete( [/ elninoSW24, laninaSW24  /] )

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;   seasonal composite     
       dimNames = (/"time",  "lat", "lon"/)
       dimSizes = (/ 1 ,    ydim,  xdim /)
       dimUnlim = (/ True , False, False/)

       elnino = new( dimSizes, "float")
       elnino = 0.
       elnino@_FillValue = datainLW@_FillValue
       ss2 =  elnino
       lanina = elnino
       ss22 =  elnino

        do itt = 0 ,itmax1 - 1
         it1 = (iyelnino(itt) - iy1) * 12  + im1 - 1
         it2 = it1 + itd
       do it = it1, it2
       elnino(0, :, :) =  where( .not. ismissing( datainLW(it, :, :)), elnino(0, :, :) + datainLW(it, :, :), elnino(0, :, :) )
         ss2(0, :, :)  =  where( .not. ismissing( datainLW(it, :, :)),  ss2(0, :, :) + 1.,  ss2(0, :, :) )
       end do
       end do

       do itt = 0 ,itmax2 - 1
           it1 = (iylanina(itt) - iy1) * 12 + im1 - 1
           it2 = it1 + itd
        do it = it1, it2
       lanina(0, :, :) =  where( .not. ismissing( datainLW(it, :, :)), lanina(0, :, :) + datainLW(it, :, :), lanina(0, :, :) )
         ss22(0:, :, :)  =  where( .not. ismissing( datainLW(it, :, :)),  ss22(0, :, :) + 1.,  ss22(0, :, :) )
       end do
       end do

        ss2 =  where( ss2 .gt. 0., ss2, datainLW@_FillValue)
       elnino = where( .not. ismissing(ss2), elnino/ss2, datainLW@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datainLW@_FillValue)
       lanina = where( .not. ismissing(ss22), lanina/ss22, datainLW@_FillValue)
       
        elninoLW = elnino  
        laninaLW = lanina
;;;  the same for SW
       elnino = new( dimSizes, "float")
       elnino = 0.
       elnino@_FillValue = datainLW@_FillValue
       ss2 =  elnino
       lanina = elnino
       ss22 =  elnino

        do itt = 0 ,itmax1 - 1
         it1 = (iyelnino(itt) - iy1) * 12  + im1 - 1
         it2 = it1 + itd
       do it = it1, it2
       elnino(0, :, :) =  where( .not. ismissing( datainSW(it, :, :)), elnino(0, :, :) + datainSW(it, :, :), elnino(0, :, :) )
         ss2(0, :, :)  =  where( .not. ismissing( datainSW(it, :, :)),  ss2(0, :, :) + 1.,  ss2(0, :, :) )
       end do
       end do

       do itt = 0 ,itmax2 - 1
           it1 = (iylanina(itt) - iy1) * 12 + im1 - 1
           it2 = it1 + itd
        do it = it1, it2
       lanina(0, :, :) =  where( .not. ismissing( datainSW(it, :, :)), lanina(0, :, :) + datainSW(it, :, :), lanina(0, :, :) )
         ss22(0:, :, :)  =  where( .not. ismissing( datainSW(it, :, :)),  ss22(0, :, :) + 1.,  ss22(0, :, :) )
       end do
       end do

        ss2 =  where( ss2 .gt. 0., ss2, datainLW@_FillValue)
       elnino = where( .not. ismissing(ss2), elnino/ss2, datainSW@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, datainLW@_FillValue)
       lanina = where( .not. ismissing(ss22), lanina/ss22, datainSW@_FillValue)
       
        elninoSW = elnino
        laninaSW = lanina
;;;;  write out 
       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
;; define units and standard name
       elninoLW@standard_name = standardnameLW
       laninaLW@standard_name = standardnameLW

       VarnameLW = "lw"
       elninoLW@units = unitRAD
       laninaLW@units = unitRAD

       fileout  = nameout + "/ELNINO/" + VarnameLW + ".nc"
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
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameLW, typeof(elninoLW),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameLW, elninoLW)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameLW$  = (/elninoLW/)
       delete( fout) 
;; the same for lanina
       fileout  = nameout + "/LANINA/" + VarnameLW + ".nc"
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
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameLW, typeof(laninaLW),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameLW, laninaLW)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameLW$  = (/laninaLW/)
       delete( fout)
;;;;;;;;;;;;;  repeat for SW 
       VarnameSW = "sw"
       elninoSW@units = unitRAD
       laninaSW@units = unitRAD

       fileout  = nameout + "/ELNINO/" + VarnameSW + ".nc"
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
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameSW, typeof(elninoSW),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameSW, elninoSW)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameSW$  = (/elninoSW/)
       delete( fout) 
 
      fileout  = nameout + "/LANINA/" + VarnameSW + ".nc"
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
       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  VarnameSW, typeof(laninaSW),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, VarnameSW, laninaSW)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$VarnameSW$  = (/laninaSW/)
  
      print( "finished radiation " +  systemfunc ("date") )
      delete( fout ) 
      delete( [/  dimNames, dimSizes, dimUnlim, dimSizes24, elnino, lanina /])
     end if 

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;   added  regression  
    if( idcor .eq. 1) 
;;  collect the El Nino anom_sst data first    itmax1  iyelnino
      dims1 = dimsizes( anom_sst) 

       lat   = (/anom_sst&lat/)
       lon   = (/anom_sst&lon/)
       time0 = (/anom_sst&time/)
       time0@calendar  ="standard"
       time2 = calendar_decode2( time0 ,  -5)

       tdim = dimsizes(time0)     ; get dimension sizes
       ydim = dimsizes(lat)
       xdim = dimsizes(lon)

      elnino_sst = new( tdim, "float")
      elnino_sst = anom_sst@_FillValue

       itd = im2 - im1
      if( im2 .lt. im1)
       itd = im2 + 12 - im1
      end if

      anom_sst2 =  wgt_areaave_Wrap(  anom_sst(:, {lat1:lat2},  {lon1:lon2}), 1., 1., 0)

       it3 = 0
       do it = 0 ,tdim - 1
        im  = time2(it, 1)
         if( im .eq. im1) 
         it1 = it
         it2 = it + itd
         if( it2 .gt. tdim-1)
           it2 = tdim-1
         end if
         do itt = it1, it2
         elnino_sst(it3) =  anom_sst2(itt) ;; dim_avg_n_Wrap(xanomx,0)
         it3 = it3 + 1
        end do 
        end if
      end do
     
;;;  correlations and regressions with select variables
      do iv = 0, ivarC - 1
       Varname = VarsC(iv)

       ff = 1.
       if( iv .eq. 0) 
       ff = 24.*60.*60.
       end if  

       if( (iv .le. 0)  .or. (iv .ge. 3) )
       namein = namein1 + case + "." + Varname + ".mon.nc"
       fin = addfile( namein, "r")

      datain = fin->$Varname$
      end if

      if (iv .eq. 1)  
         datain = datainSW
      end if
      if (iv .eq. 2) 
        datain  = datainLW 
      end if
;;;   define the climatology 
      clima = clmMonTLL ( datain)
;;  define monthly anomaly
       anom = calcMonAnomTLL ( datain, clima)

       dimNames = (/ "lat", "lon"/) ;;  (/"time",  "lat", "lon"/)
       dimSizes = (/ ydim,  xdim /) ;;  (/ 1 ,   ydim,  xdim /)
       dimUnlim = (/ False, False/) ;;   (/ True , False, False/)

       elnino = anom
       elnino = anom_sst@_FillValue

	 it3 = 0
       do it = 0 ,tdim - 1
        im  = time2(it, 1)
         if( im .eq. im1) 
         it1 = it
         it2 = it + itd
         if( it2 .gt. tdim-1)
           it2 = tdim-1
         end if
         do itt = it1, it2
         elnino(it3,:,:) =  anom(itt,:,:) ;; dim_avg_n_Wrap(xanomx,0)
         it3 = it3 + 1
        end do 
        end if
      end do
       it3 = it3 - 1
;;;       printVarSummary( corr)
;;       
         yy =  elnino(lat|:,lon|:,time|:)
         corr  = escorc(elnino_sst(0:it3-1), yy(:,:,0:it3-1)) 

       reg =  ff * regCoef( elnino_sst(0:it3-1), yy(:,:,0:it3-1))

        copy_VarCoords(elnino(0,:,:), reg)
        copy_VarCoords(elnino(0,:,:), corr)
        corr@standard_name = standardnameC(iv)
        reg@standard_name = standardnameR(iv)
        reg@units  = unitR(iv) 
;;;   write output   

       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

       fileout  = nameout + "/CORR_" + Varname + ".nc"
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
       filevardef(fout,  Varname, typeof(corr),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, Varname, corr)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname$  = (/corr/)

;;;;   the same for regression
       fileout  = nameout + "/REGRESS_" + Varname + ".nc"
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
       filevardef(fout,  Varname, typeof(reg),  dimNames )

       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, Varname, reg)

       setfileoption(fout,"DefineMode",False)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname$  = (/reg/)
;;;        print(iv + "  " + fileout + " " )  
      delete(  [/ reg, corr /])
      end do ;;; over input variables 
     print( " finished correlations and regressions "  +  systemfunc ("date") )
    end if      

end 
