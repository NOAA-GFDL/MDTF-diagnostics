;*******************************************************
;
;   to regrid the original NetCDF files to pre-defined 
;            binaries +  climatologies
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

	 iy1 = getenv("FIRSTYR")
        iy2 = getenv("LASTYR")

 
;;;           need this file just  in a case it is on hybrid levels 
	plevels_name  =  codedata + "/shared/plevs.txt"

	namein1 = vardata + "/mon/" +  case + "."

	nameout = outdir + "/netCDF/DATA/" 
      
;;   read in all parameters including the new plevels 

;;;    selected variables    import from system defined vars. 
;; 	3 D vars 
       zg  = getenv("zg_var")
       ua  = getenv("ua_var")
       va  = getenv("va_var")
       ta  = getenv("ta_var")
       hus = getenv("qa_var")       
       wap = getenv("omega_var")
;;  	2D  vars
       pr = getenv("pr_var")
       ts = getenv("ts_var")
       pr_conversion = getenv("pr_conversion_factor")
	hfss = getenv("hfss_var")       
	hfls = getenv("hfls_var") 
	
;;       coordinate vars 
       lev  = getenv("lev_coord")
       lon  = getenv("lon_var")
       lat  = getenv("lat_var")
       time = getenv("time_var")
	
       hyam = getenv("hyam_var")
       hybm = getenv("hybm_var")

;;;;   
;;     	 Varnamesin3   = (/ "zg", "ua", "va", "ta", "hus", "wap" /)
            Varnamesin3   = (/ zg, ua, va, ta, hus, wap /)

	Varnamesout3  = (/ "Z", "U", "V", "T", "Q", "OMG" /)
 	ivar3 = dimsizes( Varnamesin3)

;;;;	print( Varnamesin3 )

;;  2 D fluxes 
;;        Varnamesin2   = (/ "pr",  "hfss", "hfls", "ts"/)
       Varnamesin2   = (/ pr,  hfss, hfls, ts/)
       Varnamesout2  = (/ "PR",  "SHF" , "LHF" , "TS" /)
       ivar2 = dimsizes( Varnamesin2)
       ivar32 = ivar3 + ivar2 
;;;;;;;;;;;;   
 
       undef2 = 1.1E+20
	
;; 
;;;   get the 3D dimensions from the actual NetCDF data 
	ivar = 0
       Varname =   Varnamesin3(ivar)
        namein = namein1 + Varname + ".mon.nc"
        fin = addfile( namein, "r")
        setfileoption("nc", "Format",  "NetCDF4")  ;   "NetCDF4Classic"

;;;      check if the data are on hybrid levels - if  hyam and hybm define
         ihyam = 0
         ihybm = 0
        if (isfilevar(fin, hyam)) then
         hyam4 = fin->$hyam$
         hyam2 = tofloat(hyam4)
         ihyam = 1
        end if
        if (isfilevar(fin, hybm)) then
         hybm4 = fin->$hybm$
         hybm2 = tofloat(hybm4)
         ihybm = 1
        end if
;;;;   
       
      if( (ihyam .eq. 1) .and. (ihybm .eq. 1)) then
         print ( "data on  hybrid levels will be converted to pressure levels ")
         pdata  = asciiread(plevels_name,-1,"string")
         plevels = stringtofloat( pdata)
         pnew = plevels
         else
           ; not on hybrid levels
           lev_unit_conversion = 1.0
           i = str_index_of_substr(lev, "plev", 1) 
           ; allows for eg "plev19" as in CMIP, but should compare units instead
           if (i.eq.0) then
             print ("found plev axis, assuming hPa")
             lev_unit_conversion = 0.01
           else
             print ("Assuming levels in Pa")
           end if
           dlev = fin->$lev$
           plevels = lev_unit_conversion * tofloat ( dlev)
	end if 
;;;;  get the dimensions and write out 
       dlat = fin->$lat$
       lat2 =  tofloat ( dlat)
 
       dlon = fin->$lon$
       lon2 =  tofloat ( dlon)

       time0 = fin->$time$
       time2 = calendar_decode2 ( time0 ,  -5)
       ntim  = dimsizes(time0)     ; get dimension sizes
       nlev  = dimsizes(plevels)
       nlat  = dimsizes(lat2)
       nlon  = dimsizes(lon2)

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
        if( d3var .eq. 1)  then
         do ivar =  0,   ivar3 - 1

         Varname =  Varnamesin3(ivar)
         Varout = Varnamesout3(ivar)
	   ivv1 = ivar + 1
;;;;   print( " Started preprocessing variable : " + Varname + "  " +  ivv1 + "/" + ivar32 )

        namein = namein1 + Varname + ".mon.nc"
        print("namein: "+ namein)           
        fin = addfile( namein, "r")
        setfileoption("nc", "Format",  "NetCDF4")  ;   "NetCDF4Classic"

;;;     check if the data are on hybrid levels - if  hyam and hybm define
         ihyam = 0
         ihybm = 0
	 if (isfilevar(fin, hyam)) then
         hyam4 = fin->$hyam$
         hyam2 = tofloat(hyam4)
         ihyam = 1
        end if

	 if (isfilevar(fin, hybm)) then
         hybm4 = fin->$hybm$
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
       time0 = fin->$time$
       
       time2 = calendar_decode2 ( time0 ,  -5)

         dlev = fin->$lev$
         lev2 = lev_unit_conversion * tofloat ( dlev)

       dlat = fin->$lat$
 	lat2 =  tofloat ( dlat)
 
       dlon = fin->$lon$
	lon2 =  tofloat ( dlon)

;;        tdate = fin->date

       ntim  = dimsizes(time0)	; get dimension sizes
 	nlev  = dimsizes(lev2)
 	nlat  = dimsizes(lat2)
 	nlon  = dimsizes(lon2)

       dimNames = (/"time", "lev", "lat", "lon"/)
       dimSizes = (/ 1 ,   nlev,  nlat,  nlon /)
 	dimUnlim = (/ True , False, False, False/)

;;;;;;   loop over all years and write out if selected 
      do it = 0, ntim - 1 
       year = time2(it,0)
       month = time2(it,1)
  
       if( ( year .ge. iy1 ) .and. ( year .le. iy2 )) then

       Vin  = fin->$Varname$(it,:, :, :) 
	
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

;;;  output the data to a file based on year  and month 
        yearchar =  sprinti("%0.4i", year)
        monthchar =  sprinti("%0.2i", month)
 
       n =  systemfunc( " mkdir " + nameout + yearchar  + " 2> /dev/null")
       fileout  = nameout + yearchar + "/" + Varout + "_" + yearchar + "-" +  \
                         monthchar + ".grd"
      ;;   print("fileout: "+fileout )
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fbindirwrite(fileout , Vout )
      ;;  print( yearchar )

      delete( indices)
      delete( Vin)
      delete( Vout) 
      delete( Vinter1D)

      end if   ;;;   if in time slot 

      end do   ;;    over all time steps 
      
      delete( fin) 
      end do  ;;;;  over 3 D variables
      end if  ;;;  it 3D var extraction 
;;;;;;;;;;;;;;;; END 3D calculations 
     
;;;;;;;;;;;
;;;; the same for 2D but no vertical or hybrid  interpolations

      do ivar = 0, ivar2 - 1
;;      
;;        print( ivar)
;;        dimsize4 = (/ ymax, xmax /)
       Varname = Varnamesin2(ivar)
       Varout = Varnamesout2(ivar)
       ivv1 = ivar3 + ivar + 1
;;;  print( " Started preprocessing variable : " + Varname + "  " +  ivv1 + "/" + ivar32 )

       namein = namein1 + Varname + ".mon.nc"
       fin = addfile( namein, "r")
       setfileoption("nc", "Format",  "NetCDF4")  ;   "NetCDF4Classic"

       ;;   the time attribute here :

       time20 = fin->$time$
       time22 = calendar_decode2 ( time20 ,  -5)

       dlat = fin->$lat$
       lat2 =  tofloat ( dlat)

       dlon = fin->$lon$
       lon2 =  tofloat ( dlon)

;;        tdate = fin->date
;;	 conversion - needed for PR
	ff = 1.
       if( Varname .eq. pr) then
	  ff = tofloat(pr_conversion)
       end if 

       ntim  = dimsizes(time20)      ; get dimension sizes
       nlat  = dimsizes(lat2)
       nlon  = dimsizes(lon2)
       dimNames2 = (/"time",  "lat", "lon"/)
       dimSizes2 = (/ 1 ,    nlat,  nlon /)
       dimUnlim2 = (/ True , False, False/)
;;;       loop over times and select only prescribed years 
       do it = 0, ntim - 1
       year = time22(it,0)
       month = time22(it,1)

       if( ( year .ge. iy1 ) .and. ( year .le. iy2 )) then

       Vin2  = fin->$Varname$(it, :, :)
      
       Vout20 = ff * Vin2
       Vinter = ndtooned ( Vout20)
       indices2 = ind( ismissing(  Vinter) )
       if( .not.ismissing( indices2(0)))  then
       Vinter( indices2 ) = undef2
       end if
       Vout20 = onedtond( Vinter, dimsizes( Vin2))
       Vout20@_FillValue = undef2

;;;;   write out to the file :  
       yearchar =  sprinti("%0.4i", year)
       monthchar =  sprinti("%0.2i", month)

       fileout  = nameout + yearchar + "/" + Varout + "_" + yearchar + "-" +  \
                         monthchar + ".grd"
       print("fileout: "+fileout)
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fbindirwrite(fileout , Vout20 )
	 
       delete( indices2)
       delete( Vinter)
       delete( Vin2) 
       delete( Vout20)
    
       end if  ;;  if in the year selection 
       end do   ;;; over all time steps 
       delete( fin) 
       end do ;;   over all 2D  variables 

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

end
