;;***************************************************
;*******************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin 

;;  read  in the data from  NetCDF directory one year + months im1 , im2
;;     to avoid loading too much into memory 
    vardata  = getenv("DATADIR")                   ; model input
    outdir  =  getenv("ENSO_RWS_WKDIR") + "/model" ; envvar set in ENSO_MSE.py
    case    =  getenv( "CASENAME")

      iy1 =  toint( ( getenv("FIRSTYR")) )
      iy2 =  toint( (  getenv("LASTYR")) )

;;;    selected variables    import from system defined vars.
;;     3 D vars
       zgv  = "zg" ;; 
       uav  = "ua" ;;  
       vav  = "va" ;; 
       tav  = "ta" ;; 
       wapv = "wap" ;; 

;;     2D  vars
       prv =  "pr" ;;; 
       tsv =  "ts" ;;;   
       pr_conversionv =  1. ;;;  

;;       coordinate vars
       levx  = "lev" ;;; 
       lonx  = "lon" ;;; 
       latx  = "lat" ;;;  
       timex = "time" ;;;  

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;           need this file just  in a case it is on hybrid levels

       namein1   = vardata +  "/mon/"
       nameout   =  outdir + "/netCDF/DATA/"
       nameclima =  outdir + "/netCDF/CLIMA/"
;;;;   
       Varnamesin3   = (/ zgv, uav, vav, tav, wapv /)

	Varnamesout3  = (/ "zg", "ua", "va", "ta", "wap" /)
 	ivar3 = dimsizes( Varnamesin3)

;;  2 D fluxes 
       Varnamesin2   = (/ prv,  tsv /)
       Varnamesout2  = (/ "pr", "ts" /)
       ivar2 = dimsizes( Varnamesin2)
       ivar32 = ivar3 + ivar2 
;;;;;;;;;;;;   
 
       undef2 = 1.1E+20
;; 
;;;   get the 3D dimensions from the actual NetCDF data 
	ivar = 0
       Varname =   Varnamesin3(ivar)
        namein = namein1 + case +"." + Varname + ".mon.nc"

        fin = addfile( namein, "r")
        setfileoption("nc", "Format",  "Classic")  ;   "NetCDF4Classic"

;;;;  get the dimensions and write out 
       dlat = fin->$latx$
       lat2 =  tofloat ( dlat)
 
       dlon = fin->$lonx$
       lon2 =  tofloat ( dlon)

       time0 = fin->$timex$
       time2 = calendar_decode2 ( time0 ,  -5)
	
        if (isfilevar(fin, "lev")) then
        dlev = fin->lev
        end if

        if (isfilevar(fin, "plev")) then
        dlev = fin->plev
        end if

;;     convert to mb
        ff = 1.
        if(  dlev@units .eq. "Pa")
        ff = 0.01
        end if
	 plevels = ff * tofloat ( dlev)

       ntim  = dimsizes(time0)     ; get dimension sizes
       nlev  = dimsizes(plevels)
       nlat  = dimsizes(lat2)
       nlon  = dimsizes(lon2)

       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   nlev,  nlat,  nlon /)
       dimUnlim = (/ True , False, False, False/)
       dimSizes12 = (/ 12 ,   nlev,  nlat,  nlon /)

        clima = new( dimSizes12, "float")
        clima =  0.
        clima@_FillValue = undef2
        ss3 = new(  dimSizes12, "float")
        ss3@_FillValue = undef2
        ss3 = 0.

        delete( fin)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;     READ DATA IN  here 

	d3var = 1
       d2var = 1
        if( d3var .eq. 1)  then

         do ivar =  0,   ivar3 - 1

         Varname =  Varnamesin3(ivar)
         Varout = Varnamesout3(ivar)
	   ivv1 = ivar + 1
    print( " Started preprocessing variable : " + Varname + "  " +  ivv1 + "/" + ivar32 )

        namein = namein1 + case +"." + Varname + ".mon.nc"
        fin = addfile( namein, "r")
        setfileoption("nc", "Format",  "Classic")  ;   "NetCDF4Classic"

;;   the time attribute here :
       time0 = fin->$timex$
       
       time2 = calendar_decode2 ( time0 ,  -5)

       if (isfilevar(fin, "lev")) then
         dlev = fin->lev
        end if

       if (isfilevar(fin, "plev")) then
        dlev = fin->plev
       end if

;;     convert to mb
        ff = 1.
        if(  dlev@units .eq. "Pa")
        ff = 0.01
        end if
        lev2 = ff * tofloat ( dlev)

        dlat = fin->$latx$
 	 lat2 =  tofloat ( dlat)
 
       dlon = fin->$lonx$
	lon2 =  tofloat ( dlon)

;;      tdate = fin->date

       ntim  = dimsizes(time0)	; get dimension sizes
 	nlev  = dimsizes(lev2)
 	nlat  = dimsizes(lat2)
 	nlon  = dimsizes(lon2)

       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   nlev,  nlat,  nlon /)
 	dimUnlim = (/ True , False, False, False/)
       dimSizes12 = (/ 12 ,   nlev,  nlat,  nlon /)

        clima = new( dimSizes12, "float")
        clima =  0.
        clima@_FillValue = undef2
        ss3 = new(  dimSizes12, "float")
        ss3@_FillValue = undef2
        ss3 = 0.

;;;;;;   loop over all years and write out if selected 

      do year = iy1, iy2

       Vin = new(  dimSizes12, "float")
        timeout = new( 12, typeof(time0) )
        copy_VarAtts (time0, timeout)
        timeout@calendar = "standard"

      do it = 0, ntim - 1
         year22 = time2(it,0)
         month = time2(it,1)

       if(  year22 .eq. year)  then
        it2 = month - 1
       Vin(it2, :, :,:)  = fin->$Varname$(it:it,:, :, :)
       timeout(it2)  = time0(it)
       end if
       end do   ;;  over all time steps in the file
	timeout@calendar = "standard"
;;     convert Vin to  select model levels   if on hybrid levels
        Vinter1D      = ndtooned ( Vin)
        indices = ind(ismissing(Vinter1D))
        if( .not.ismissing( indices(0) ))  then
        Vinter1D( indices ) = undef2
        end if    
        Vout = onedtond( Vinter1D, dimsizes( Vin))
        Vout@_FillValue = undef2

;;;;;;;;;;  fill clima - the same dims as Vout
    clima =  where( .not. ismissing(Vout), clima + Vout, clima )
    ss3   =  where( .not. ismissing(Vout),  ss3 + 1., ss3)
  
        Vout!3="lon"
        Vout!2="lat"
        Vout!1="lev"
        Vout!0="time"
        Vout@_FillValue = undef2

;;;  output the data to a file based on year  and month
       yearchar =  sprinti("%0.4i", year)
       fileout  = nameout + yearchar + "/" + Varout + "_" + yearchar + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)
   
       lon2!0 = "lon"
       lon2@units = "degrees_east"
       lon2@_FillValue = undef2
       lon2@long_name = "longitude"

       lat2!0 = "lat"
       lat2@units = "degrees_north"
       lat2@long_name = "latitude"
       lat2@_FillValue = undef2

       lev2!0 = "lev"
       lev2@units  = "mb"
       lev2@long_name = "pressure levels "
       lev2@_FillValue = undef2

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

;;;;;;;;;;;;;;;;; define all attributes here   
      filedimdef(fout, dimNames, dimSizes, dimUnlim)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lev"  , typeof(lev2),   (/"lev"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout, typeof(Vout),  dimNames )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lev"  , lev2)                     ; copy lev attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout, Vout)

      setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lev    = (/lev2/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout$  = (/Vout/)

      delete( indices)
      delete( Vin)
      delete( Vout)
      delete( Vinter1D)
      
      end do   ;;    over all  years in the data

;;;;  average clima and output too
       ss3 =  where( ss3 .gt. 0.,  ss3 ,  ss3@_FillValue )
       clima = clima/ss3
;;;   define attributes    and nameout
       fileout  = nameclima + "/" + Varout + "_clim" + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)
       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

;;;;;;;;;;;;;;;;; define all attributes here    
       filedimdef(fout, dimNames, dimSizes, dimUnlim)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lev"  , typeof(lev2),   (/"lev"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout, typeof(clima),  dimNames )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lev"  , lev2)                     ; copy lev attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout, clima)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lev    = (/lev2/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout$  = (/clima/)
;;;; 
      delete( fout)
      delete( time0)
      delete( time2)
      delete( timeout)

      delete( ss3)
      delete( clima)

      delete( fin)

      end do  ;;;;  over 3 D variables
      end if  ;;;  if 3D var extraction
;;;;;;;;;;;;;;;; END 3D calculations

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;; the same for 2D but 
      if( d2var .eq. 1) then

      do ivar = 0, ivar2 - 1
;;      
       Varname = Varnamesin2(ivar)
       Varout = Varnamesout2(ivar)
       ivv1 = ivar3 + ivar + 1
   print( " Started preprocessing variable : " + Varname + "  " +  ivv1 + "/" + ivar32 )

       namein = namein1 + case +"." + Varname + ".mon.nc"

       fin = addfile( namein, "r")
       setfileoption("nc", "Format",  "Classic")  ;   "NetCDF4Classic"

;;   the time attribute here :

       time0 = fin->$timex$
       time2 = calendar_decode2 ( time0 ,  -5)

       dlat = fin->$latx$
       lat2 =  tofloat ( dlat)

       dlon = fin->$lonx$
       lon2 =  tofloat ( dlon)

;;        tdate = fin->date
;;	 conversion - needed for PR
	ff = 1.
       if( Varname .eq. prv) then
	  ff = tofloat(pr_conversionv)
       end if 

       ntim  = dimsizes(time0)      ; get dimension sizes
       nlat  = dimsizes(lat2)
       nlon  = dimsizes(lon2)
       dimNames2 = (/"time",  "lat", "lon"/)
       dimSizes2 = (/ 1 ,    nlat,  nlon /)
       dimUnlim2 = (/ True , False, False/)
       dimSizes22 = (/ 12 ,  nlat,  nlon /)
;;;  define clima arrays
        clima = new( dimSizes22, "float")
        clima =  0.
        clima@_FillValue = undef2
        ss2 = new(  dimSizes22, "float")
        ss2@_FillValue = undef2
        ss2 = 0.

;;;       loop over times and select only prescribed years 
       do year = iy1, iy2

        Vin2 = new(  dimSizes22, "float")
        timeout = new( 12, typeof(time0) )
        copy_VarAtts (time0, timeout)

        do it = 0, ntim - 1
         year22 = time2(it,0)
         month  = time2(it,1)

       if(  year22 .eq. year)  then

       it2 = month - 1
       Vin2(it2, :,:)  = fin->$Varname$(it:it, :, :)
       timeout(it2)  = time0(it)

       end if
       end do   ;;  over all time steps in the file
	timeout@calendar = "standard"
;;;;;;;;;;;;;;;;
	 Vinter1D      = ndtooned ( Vin2)
        indices = ind(ismissing(Vinter1D))
        if( .not.ismissing( indices(0) ))  then
        Vinter1D( indices ) = undef2
        end if
        Vout2 = onedtond( Vinter1D, dimsizes( Vin2))
        Vout2@_FillValue = undef2
	 delete( indices)
        delete( Vinter1D)
        Vout2 = ff * Vout2
       
;;;;;;;;;;  fill clima - the same dims as Vout
     clima =  where( .not. ismissing(Vout2), clima + Vout2, clima )
     ss2   =  where( .not. ismissing(Vout2),  ss2 + 1., ss2)
 
        Vout2!2="lon"
        Vout2!1="lat"
        Vout2!0="time"
        Vout2@_FillValue = undef2
;;;  output the data to a file based on year  and month
        yearchar =  sprinti("%0.4i", year)

         fileout  = nameout + yearchar + "/" + Varout + "_" + yearchar + ".nc"
          n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)

       lon2!0 = "lon"
       lon2@units = "degrees_east"
       lon2@_FillValue = undef2
       lon2@long_name = "longitude"

       lat2!0 = "lat"
       lat2@units = "degrees_north"
       lat2@long_name = "latitude"
       lat2@_FillValue = undef2


       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes
;;;;;;;;;;;;;;;;; define all attributes here    
            filedimdef(fout, dimNames2, dimSizes2, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout, typeof(Vout2),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout, Vout2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout$  = (/Vout2/)

        end do   ;;    over all  years in the data
      

       fileout  = nameclima + "/" + Varout + "_clim" + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)
    
       lon2!0 = "lon"
       lon2@units = "degrees_east"
       lon2@_FillValue = undef2
       lon2@long_name = "longitude"

       lat2!0 = "lat"
       lat2@units = "degrees_north"
       lat2@long_name = "latitude"
       lat2@_FillValue = undef2

       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes
;;;;;;;;;;;;;;;;; define all attributes here    
;;;;  average clima and output too
      ss2 =  where( ss2 .gt. 0.,  ss2 ,  ss2@_FillValue )
       clima = clima/ss2
;;;   define attributes    and nameout
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)
       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

;;;;;;;;;;;;;;;;; define all attributes here   
         filedimdef(fout, dimNames2, dimSizes2, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout, typeof(clima),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout, clima)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout$  = (/clima/)

      delete( fout)
      delete( time0)
      delete( time2)
      delete( timeout)
      delete( fin)
      delete( ss2)
      delete( clima)

      end do  ;;;;  over 2 D variables
      end if  ;;;  if 2D var extraction
;;;;;;;;;;;;;;;; END 2D calculations
end
 
