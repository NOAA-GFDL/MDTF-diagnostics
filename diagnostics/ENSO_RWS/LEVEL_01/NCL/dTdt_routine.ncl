;;***************************************************
;
;*******************************************************
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin 

;;  read  in the data from  NetCDF directory one year + months im1 , im2
;;      to process dT/dt data from ta 
 vardata  = getenv("DATADIR")                   ; model input
     
 outdir  = getenv("ENSO_RWS_WKDIR") + "/model" ; envvar set in ENSO_MSE.py
 case = getenv( "CASENAME")

  iy1 =  toint( ( getenv("FIRSTYR")) )
  iy2 =  toint( (  getenv("LASTYR")) )

;;;    selected variables    import from system defined vars. 
;;     3D  vars only TA
    tav =  "ta" ;;;   getenv("ta_var")

;;       coordinate vars
      levx  = "lev" ;;  getenv("lev_coord")
      lonx  = "lon" ;;  getenv("lon_coord")
      latx  = "lat" ;;;   getenv("lat_coord")
      timex = "time" ;;;   getenv("time_coord")

;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

       namein1   = vardata +  "/mon/"
       nameout   =  outdir + "/netCDF/DATA/"
       nameclima =  outdir + "/netCDF/CLIMA/"
;;;;   
;;   3D ta
       Varname  =  tav
       Varname2 = "dT"
       Varout   =  "dT" 
;;;;;;;;;;;;   
 
       undef2 = 1.1E+20
;; 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;      
   print( " Started preprocessing dT/dt " )

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

;;        tdate = fin->date

       ntim = dimsizes( time0)      ; get dimension sizes
       nlev = dimsizes( plevels)
       nlat = dimsizes( lat2)
       nlon = dimsizes( lon2)
       dimNames2 = (/"time", "lev",  "lat", "lon"/)
       dimSizes2 = (/ 1 ,  nlev,  nlat,  nlon /)
       dimUnlim2 = (/ True ,  False,False, False/)
       dimSizes22 = (/ 12 , nlev,  nlat,  nlon /)
;;;  define clima arrays
        clima = new( dimSizes22, "float")
        clima =  0.
        clima@_FillValue = undef2
        ss2 = new(  dimSizes22, "float")
        ss2@_FillValue = undef2
        ss2 = 0.

;;       
        ta = fin->$Varname$
        time_seconds = cd_convert( time0, "seconds since 1950-01-01 00:00" )
        dta = center_finite_diff_n( ta, time_seconds, False, 0,  0)
;;       convert time to seconds 
      
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
       Vin2(it2, :, :, :)  = tofloat( dta(it, :, :, :))  ;;;;   fin->$Varname$(it:it, :, :)

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
       
;;;;;;;;;;  fill clima - the same dims as Vout
     clima =  where( .not. ismissing(Vout2), clima + Vout2, clima )
     ss2   =  where( .not. ismissing(Vout2),  ss2 + 1., ss2)
 
        Vout2!3 ="lon"
        Vout2!2 ="lat"
        Vout2!1 ="lev"
        Vout2!0 ="time"
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

	plevels!0 = "lev"
       plevels@units  = "mb"
       plevels@long_name = "pressure levels "
       plevels@_FillValue = undef2


       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes
;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
       filedimdef(fout, dimNames2, dimSizes2, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lev"  , typeof(plevels),   (/"lev"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varname2, typeof(Vout2),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lev"  , plevels)
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varname2, Vout2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lev    = (/plevels/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varname2$  = (/Vout2/)

        end do   ;;    over all  years in the data
      

       fileout  = nameclima + "/" + Varout + "_clim" + ".nc"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fout = addfile( fileout ,"c")
       setfileoption(fout,"DefineMode",True)
    
;       lon2!0 = "lon"
;       lon2@units = "degrees_east"
;       lon2@_FillValue = undef2
;       lon2@long_name = "longitude"

;       lat2!0 = "lat"
;       lat2@units = "degrees_north"
;       lat2@long_name = "latitude"
;       lat2@_FillValue = undef2


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
       filevardef(fout, "lev"  , typeof(plevels),   (/"lev"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varname2, typeof(clima),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lev"  , plevels)
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varname2, clima)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lev    = (/plevels/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varname2$  = (/clima/)

      delete( fout)
      delete( time0)
      delete( time2)
      delete( timeout)
      delete( fin)
      delete( ss2)
      delete( clima)

;;;;;;;;;;;;;;;; END of calculations
end
 
