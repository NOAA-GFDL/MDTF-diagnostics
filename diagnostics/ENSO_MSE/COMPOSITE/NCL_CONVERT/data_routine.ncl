;;***************************************************
;
;*******************************************************
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin

;;  read  in the data from  NetCDF directory :  one month at the time
;;     to avoid loading too much into memory
      vardata  = getenv("DATADIR")                   ; model input
      outdir  = getenv("ENSO_MSE_WKDIR_COMPOSITE") + "/model" ; envvar set in ENSO_MSE.py
      case =  getenv( "CASENAME")
      codedata = getenv ("POD_HOME")

      iy1 = toint( ( getenv("FIRSTYR")) )
      iy2 = toint( (  getenv("LASTYR")) )

;;;    selected variables    import from system defined vars.
;;     3 D vars
       zgv  = "zg" ;;  getenv("zg_var")
       uav  = "ua" ;;  getenv("ua_var")
       vav  = "va" ;;  getenv("va_var")
       tav  = "ta" ;;  getenv("ta_var")
       husv = "hus" ;;  "qa" ;;  getenv("qa_var")
       wapv = "wap" ;;  getenv("omega_var")

;;     2D  vars
       prv = "pr" ;;  getenv("pr_var")
       tsv = "ts" ;;  getenv("ts_var")
       pr_conversionv =  1. ;;; "pr_conversion_factor" ;;  getenv("pr_conversion_factor")
       hfssv = "hfss" ;;  getenv("hfss_var")
       hflsv = "hfls" ;;  getenv("hfls_var")

;;       coordinate vars
       levx  = "lev" ;;  getenv("lev_coord")
       lonx  = "lon" ;;  getenv("lon_var")
       latx  = "lat" ;;  getenv("lat_var")
       timex = "time" ;; getenv("time_var")

       hyamx = getenv("hyam_var")
       hybmx = getenv("hybm_var")

	levx = "lev"
       lonx = "lon"
       latx = "lat"
       timex = "time"
       hyamx = "hyam"
       hybmx = "hybm"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;           need this file just  in a case it is on hybrid levels
       plevels_name  =  codedata + "/shared/plevs.txt"

       namein1   = vardata +  "/mon/"
       nameout   =  outdir + "/netCDF/DATA/"
       nameclima =  outdir + "/netCDF/CLIMA/"
;;;;
       Varnamesin3   = (/ zgv, uav, vav, tav, husv, wapv /)

	Varnamesout3  = (/ "zg", "ua", "va", "ta", "hus", "wap" /)
 	ivar3 = dimsizes( Varnamesin3)

;;  2 D fluxes
;;        Varnamesin2   = (/ "pr",  "hfss", "hfls", "ts"/)
       Varnamesin2   = (/ prv,  hfssv, hflsv, tsv /)
       Varnamesout2  = (/ "pr",  "hfss" , "hfls" , "ts" /)
       ivar2 = dimsizes( Varnamesin2)
       ivar32 = ivar3 + ivar2
;;;;;;;;;;;;

       undef2 = 1.1E+20
;;
;;;   get the 3D dimensions from the actual NetCDF data
	ivar = 0
       Varname =   Varnamesin3(ivar)
        namein = namein1 + case +"." + Varname + ".mon.nc"
        ;print( namein + " " )

        fin = addfile( namein, "r")
        setfileoption("nc", "Format",  "Classic")  ;   "NetCDF4Classic"

;;;      check if the data are on hybrid levels - if  hyam and hybm define
         ihyam = 0
         ihybm = 0
        if (isfilevar(fin, hyamx)) then
         hyam4 = fin->$hyamx$
         hyam2 = tofloat(hyam4)
         ihyam = 1
        end if
        if (isfilevar(fin, hybmx)) then
         hybm4 = fin->$hybmx$
         hybm2 = tofloat(hybm4)
         ihybm = 1
        end if
;;;;
     if( (ihyam .eq. 1) .and. (ihybm .eq. 1)) then
         print ( "data on  hybrid levels will be converted to pressure levels ")
         print ( "trying to read from "+plevels_name)
         pdata  = asciiread(plevels_name,-1,"string")
         plevels = stringtofloat( pdata)
         pnew = plevels
         else
           if (isfilevar(fin, "lev")) then
           dlev = fin->lev
           plevels =   tofloat ( dlev)
           end if

           if (isfilevar(fin, "plev")) then
           dlev = fin->plev
           plevels =  0.01 * tofloat ( dlev)
           end if

       end if
;;;;  get the dimensions and write out
       dlat = fin->$latx$
       lat2 =  tofloat ( dlat)

       dlon = fin->$lonx$
       lon2 =  tofloat ( dlon)

       time0 = fin->$timex$
       time2 = calendar_decode2 ( time0 ,  -5)


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

       nameout2 = nameout + "longitude.out"
       n = systemfunc( " rm " +  nameout2 + " 2> /dev/null")
       fbindirwrite (nameout2, lon2)

       nameout2 = nameout + "latitude.out"
       n = systemfunc( " rm " +  nameout2 + " 2> /dev/null")
       fbindirwrite (nameout2, lat2)

        nameout2 = nameout + "plevels.out"
       n = systemfunc( " rm " +  nameout2 + " 2> /dev/null")
        fbindirwrite (nameout2, plevels)
;;;   last the  dimensions in external file
       nameout2 = nameout + "xyz_dimensions.txt"
       n = systemfunc( " rm " +  nameout2 + " 2> /dev/null")
       xyz = (/ nlon, nlat, nlev /)
       asciiwrite ( nameout2 , xyz)
       delete( fin)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;     READ DATA IN  here
;;;     get the input files from  mon/ERA-INTERIM.nc
;;;     filesin = systemfunc("ls " + namein + "*012*02.nc")
;;       loop over variables  3D first

	d3var = 1
       d2var = 1
        if( d3var .eq. 1)  then

         do ivar =  0,   ivar3 - 1

         Varname =  Varnamesin3(ivar)
         Varout = Varnamesout3(ivar)
	   ivv1 = ivar + 1
    print( " Started preprocessing variable : " + Varname + "  " +  ivv1 + "/" + ivar32 )

        namein = namein1 + case +"." + Varname + ".mon.nc"
        ; print("namein: "+ namein)
        fin = addfile( namein, "r")
        setfileoption("nc", "Format",  "Classic")  ;   "NetCDF4Classic"

;;;     check if the data are on hybrid levels - if  hyam and hybm define
         ihyam = 0
         ihybm = 0
	 if (isfilevar(fin, hyamx)) then
         hyam4 = fin->$hyamx$
         hyam2 = tofloat(hyam4)
         ihyam = 1
        end if

	 if (isfilevar(fin, hybmx)) then
         hybm4 = fin->$hybmx$
         hybm2 = tofloat(hybm4)
         ihybm = 1
        end if
;;;;    PS, 1, P0mb
       if( isfilevar( fin, "P0")) then
        P0mb = 0.01*fin->P0
	 else
        P0mb = 1000.
       end if
       if( isfilevar( fin, "PS")) then
         PS = fin->PS
       else   ;;;   to read from external file
         nameinps = namein1 +  "PS" + ".mon.nc"
           if (fileexists(nameinps)) then
            finps = addfile( nameinps, "r")
            PS = finps->PS
            delete(finps)
           end if
       end if
;;         vNames = getfilevarnames (fin)
;;   the time attribute here :
       time0 = fin->$timex$

       time2 = calendar_decode2 ( time0 ,  -5)

       if (isfilevar(fin, "lev")) then
         dlev = fin->lev
         lev2 =   tofloat ( dlev)
        end if

       if (isfilevar(fin, "plev")) then
        dlev = fin->plev
        lev2 =  0.01 * tofloat ( dlev)
       end if

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
	if( (ihyam .eq. 1) .and. (ihybm .eq. 1)) then
         print ( " hybrid levels are converted to p-levels ")
        Vinter = vinth2p( Vin, hyam2, hybm2, pnew, PS, 1, P0mb, 1, False)
        Vinter1D      = ndtooned ( Vinter)
	 indices = ind(ismissing(Vinter1D))
          if( .not.ismissing( indices(0) ))  then
          Vinter1D( indices ) = undef2
	   end if
          Vout = onedtond( Vinter1D, dimsizes( Vinter))
          Vout@_FillValue = undef2
          delete( Vinter)
;;;       if on pressure levels  just  interplotate
       else
        Vinter1D      = ndtooned ( Vin)
        indices = ind(ismissing(Vinter1D))
        if( .not.ismissing( indices(0) ))  then
        Vinter1D( indices ) = undef2
        end if
        Vout = onedtond( Vinter1D, dimsizes( Vin))
        Vout@_FillValue = undef2
       end if   ;;;   if  hybrid or not ...

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

;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
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

;;   print( yearchar )
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

;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
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
;;;; the same for 2D but no vertical or hybrid  interpolations
      if( d2var .eq. 1) then

      do ivar = 0, ivar2 - 1
;;
;;        print( ivar)
;;        dimsize4 = (/ ymax, xmax /)
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
	  ff = tofloat( pr_conversionv)
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
;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
            filedimdef(fout, dimNames2, dimSizes2, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       ;filevardef(fout,  Varname, typeof(Vout2),  dimNames2 )
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
;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
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

;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
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

