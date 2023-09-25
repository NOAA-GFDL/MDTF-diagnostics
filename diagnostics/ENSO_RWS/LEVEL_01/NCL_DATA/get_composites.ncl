;;; to get the seasonal DJF timeseries of SST for ENSO selection

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin

      varcode = getenv ("POD_HOME")
      vardata  = getenv("DATADIR")                   ; model input
      outdir  = getenv("ENSO_RWS_WKDIR") + "/model" ; envvar set in ENSO_MSE.py
      case =  getenv( "CASENAME")
      codedata = getenv ("POD_HOME")

      iy1 = toint( ( getenv("FIRSTYR")) )
      iy2 = toint( (  getenv("LASTYR")) )


      Vars3 = (/ "zg", "ua", "va", "ta", "wap" /)
      ivar3 = dimsizes( Vars3)
      unit3 = (/ "m", "m/s", "m/s", "K", "kg/kg", "Pa/s" /) 
      standardname3 = (/ "geopotential_height", "eastward_wind", "northward_wind", \
                     "air_temperature" ,  "lagrangian_tendency_of_air_pressure" /)

      Vars2 = (/ "pr", "ts" /)
      ivar2 = dimsizes( Vars2)
      unit2 = (/ "kg/m2/s" , "K" /)
      standardname2 = (/ "precipitation_flux", "surface_temperature" /) 

      id3   = 1; 
      id2   = 1; 
      iddT =  1; 

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

;;; collect the sigma in Nino3.4 
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
;;         print( iy + " " + it1 + " " + it2 + " " +  xanom2 )
       if( xanom2 .ge.  (sigma34*sigma2) ) 	
;;         print( iy + " " + it1 + " " + xanom2 )
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
;;;   define the climatology and the
      clima = clmMonTLLL ( datain)

;;  define monthly anomaly
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

       fileout  =  nameclima + "/" + Varname +  ".nc"
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

       filedimdef(fout1, dimNames, dimSizes, dimUnlim)

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

        filedimdef(fout2, dimNames, dimSizes, dimUnlim)

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
      delete( [/ dimNames, dimSizes, dimUnlim /])
      delete( [/ lat,lon, plev, time0, time2 /])

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

       fileout  =  nameclima + "/" + Varname +  ".nc"
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

       filedimdef(fout1, dimNames, dimSizes, dimUnlim)

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

        filedimdef(fout2, dimNames, dimSizes, dimUnlim)

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
    delete( [/ dimNames, dimSizes, dimUnlim /])
   end if

;;;;;; ; added  dT/dt  clima and ELNINO/LANINA data  already have the elnino lanina years
    if( iddT .eq. 1) 

      Varname = "ta"
      Varname2 = "dT"
      standardname = "dT/dt"
      unit = "K/s"     

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
;;        print( tdim + " " + zdim + " " +  ydim + " " + xdim )

       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   zdim,  ydim,  xdim /)
       dimUnlim = (/ True , False, False, False/)

        ta  = fin->$Varname$
        time_seconds = cd_convert( time0, "seconds since 1950-01-01 00:00" )
        dta = tofloat( center_finite_diff_n( ta, time_seconds, False, 0,  0)) 
        
;;;   get the dta seasonal climatology:
;;;   define the climatology and the anomaly for 24month development
      clima = clmMonTLLL ( dta)
;;  define monthly anomaly
;;;  anom = calcMonAnomTLLL ( dta, clima)

       clima2 = new( dimSizes, "float")
       clima2 =  0.
       clima2@_FillValue = ta@_FillValue
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
        ss2 =  where( ss2 .gt. 0., ss2, ta@_FillValue)
        clima2 = where( .not. ismissing(ss2), clima2/ss2, ta@_FillValue)

;;;  write out    seasonal  climatology
       timeout = new( 1, typeof(time0) )
       timeout(0)  = time0(0)
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"
       timeout@_FillValue = ta@_FillValue

       fileout  =  nameclima + "/" + Varname2 +  ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       lon!0 = "lon"
       lon@units = "degrees_east"
       lon@_FillValue = ta@_FillValue
       lon@long_name = "longitude"

       lat!0 = "lat"
       lat@units = "degrees_north"
       lat@long_name = "latitude"
       lat@_FillValue = ta@_FillValue

       plev!0 = "lev"
       plev@units  = "mb"
       plev@long_name = "pressure levels "
       plev@_FillValue = ta@_FillValue

;; define units and standard name
       clima2@standard_name = standardname
       clima2@units = unit

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
       filevardef(fout,  Varname2, typeof(clima2),  dimNames )

       filevarattdef(fout, "time" , timeout)                ; copy time attributes
       filevarattdef(fout, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout, Varname2, clima2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lev    = (/plev/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname2$  = (/clima2/)

       delete( [/ fout, clima2, ss2 /] )
        
;;;;;;;;;;;;;;;;;;;   
;;;;;;   ELNINO anomaly composite

       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   zdim,  ydim,  xdim /)
       dimUnlim = (/ True , False, False, False/)

       elnino = new( dimSizes, "float")
       elnino = 0.
       elnino@_FillValue = ta@_FillValue
       ss2 =  elnino
       lanina = elnino
       ss22 =  elnino

        do itt = 0 ,itmax1 - 1
         it1 = (iyelnino(itt) - iy1) * 12  + im1 - 1
         it2 = it1 + itd
       do it = it1, it2
       elnino(0, :, :, :) =  where( .not. ismissing( dta(it, :, :, :)), elnino(0, :, :, :) + dta(it, :, :, :), elnino(0, :, :, :) )
         ss2(0, :, :, :)  =  where( .not. ismissing( dta(it, :, :, :)),  ss2(0, :, :, :) + 1.,  ss2(0, :, :, :) )
       end do
       end do

       do itt = 0 ,itmax2 - 1
           it1 = (iylanina(itt) - iy1) * 12 + im1 - 1
           it2 = it1 + itd
        do it = it1, it2
       lanina(0, :, :, :) =  where( .not. ismissing( dta(it, :, :, :)), lanina(0, :, :, :) + dta(it, :, :, :), lanina(0, :, :, :) )
         ss22(0:, :, :, :)  =  where( .not. ismissing( dta(it, :, :, :)),  ss22(0, :, :, :) + 1.,  ss22(0, :, :, :) )
       end do
       end do

        ss2 =  where( ss2 .gt. 0., ss2, ta@_FillValue)
       elnino = where( .not. ismissing(ss2), elnino/ss2, ta@_FillValue)
        ss22 =  where( ss22 .gt. 0., ss22, ta@_FillValue)
       lanina = where( .not. ismissing(ss22), lanina/ss22, ta@_FillValue)
;;  output 
;; define units and standard name
       elnino@standard_name = standardname
       elnino@units = unit
       lanina@standard_name = standardname
       lanina@units = unit

       fileout1  = nameout + "/ELNINO/" + Varname2 + ".nc"
       fileout2  = nameout + "/LANINA/" + Varname2 + ".nc"
    
       n = systemfunc( " rm " +  fileout1 + " 2> /dev/null")
       n = systemfunc( " rm " +  fileout2 + " 2> /dev/null")
 
       fout1 = addfile( fileout1 ,"c")
       setfileoption(fout1,"DefineMode",True)
       fout2 = addfile( fileout2 ,"c")
       setfileoption(fout2,"DefineMode",True)

       filedimdef(fout1, dimNames, dimSizes, dimUnlim)

       filevardef(fout1, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout1, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout1, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout1, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout1,  Varname2, typeof(elnino),  dimNames )

       filevarattdef(fout1, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout1, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout1, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout1, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout1, Varname2, elnino)

       setfileoption(fout1,"DefineMode",False)
       fout1->time   = (/timeout/)
       fout1->lev    = (/plev/)
       fout1->lat    = (/lat/)
       fout1->lon    = (/lon/)
       fout1->$Varname2$  = (/elnino/)

       filedimdef(fout2, dimNames, dimSizes, dimUnlim)

       filevardef(fout2, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout2, "lev"  , typeof(plev),   (/"lev"/) )
       filevardef(fout2, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout2, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout2,  Varname2, typeof(lanina),  dimNames )

       filevarattdef(fout2, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout2, "lev"  , plev)                   ; copy lev attributes
       filevarattdef(fout2, "lat"  , lat)                    ; copy lat attributes
       filevarattdef(fout2, "lon"  , lon)                    ; copy lon attributes
       filevarattdef(fout2, Varname2, lanina)

       setfileoption(fout1,"DefineMode",False)
       fout2->time   = (/timeout/)
       fout2->lev    = (/plev/)
       fout2->lat    = (/lat/)
       fout2->lon    = (/lon/)
       fout2->$Varname2$  = (/lanina/)

      print( " finished variable "  + Varname2 + " "  +  systemfunc ("date") )

    end if 


end 
