;;;*******************************************************
;
;   to regrid the original NetCDF files to pre-defined 
;            data +  climatologies  as netCDF
;*******************************************************
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin 

;;  read  in the data from  NetCDF directory : 

      obsdata  = getenv("OBS_DATA")  ; model data
      outdir =  getenv("ENSO_MSE_WKDIR_COMPOSITE") + "/obs"
      case =  "ERA-INTERIM"  ;;;
      codedata = getenv ("POD_HOME")  ;; not used

       Varname1 = "rsus" ;;  getenv("rsus_var") ;;  "rsus"
       Varname2 = "rsds" ;;  getenv("rsds_var") ;;  "rsds"
       Varname3 = "rsdt" ;;  getenv("rsdt_var") ;;  "rsdt"
       Varname4 = "rsut" ;;  getenv("rsut_var") ;;  "rsut"

       Varname5 = "rlus" ;; getenv("rlus_var") ;;  "rlus"
       Varname6 = "rlds" ;;  getenv("rlds_var") ;;  "rlds"
       Varname7 = "rlut" ;;  getenv("rlut_var") ;;  "rlut"

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;;    years set by the data - here read from external file 
        nameyear =   outdir +  "/netCDF/DATA/years.txt"
        iy12 = asciiread(nameyear,(/2/),"integer")
        iy1 = iy12(0)
        iy2 = iy12(1)
;;	print( iy1 +  " " + iy2)
        undef2 = 1.1E+20

       namein0 = obsdata +  "/DATA/mon/" +  case + "."
       nameout = outdir +  "/netCDF/DATA/"
       nameclima = outdir + "/netCDF/CLIMA/"

       Varout1 =  "sw"
	Varout2 =  "lw" 

       namein1 = namein0 + Varname1 + ".mon.nc"
       namein2 = namein0 + Varname2 + ".mon.nc"
       namein3 = namein0 + Varname3 + ".mon.nc"
       namein4 = namein0 + Varname4 + ".mon.nc"
     
       namein5 = namein0 + Varname5 + ".mon.nc"
       namein6 = namein0 + Varname6 + ".mon.nc"
       namein7 = namein0 + Varname7 + ".mon.nc"

       fin1 = addfile( namein1, "r")
       fin2 = addfile( namein2, "r")
       fin3 = addfile( namein3, "r")
       fin4 = addfile( namein4, "r")
  
       fin5 = addfile( namein5, "r")
       fin6 = addfile( namein6, "r")
       fin7 = addfile( namein7, "r")

       setfileoption("nc", "Format",  "Classic")  ;   "NetCDF4Classic"

;;      the time attribute here :
       time0 = fin1->time
       time2 = calendar_decode2 ( time0 ,  -5)

       dlat = fin1->lat
       lat2 =  tofloat ( dlat)

       dlon = fin1->lon
       lon2 =  tofloat ( dlon)

;;        tdate = fin->date

       ntim  = dimsizes(time0)      ; get dimension sizes
       nlat  = dimsizes(lat2)
       nlon  = dimsizes(lon2)
       dimNames2 = (/"time",  "lat", "lon"/)
       dimSizes2 = (/ 1 ,    nlat,  nlon /)
       dimUnlim2 = (/ True , False, False/)

       dimSizes22 = (/ 12,    nlat,  nlon /)
;;;  define clima arrays
        climasw = new( dimSizes22, "float")
        climasw =  0.
        climasw@_FillValue = undef2
        sssw2 = new(  dimSizes22, "float")
        sssw2@_FillValue = undef2
        sssw2 = 0.
	 climalw = new( dimSizes22, "float")
        climalw =  0.
        climalw@_FillValue = undef2
        sslw2 = new(  dimSizes22, "float")
        sslw2@_FillValue = undef2
        sslw2 = 0.

;;;  as in the case of 3D and 2D plain variables go step by step within the year range iy1-iy2
;;;    make the annual files each with 12 months 

	do year = iy1, iy2

       Vin1 = new(  dimSizes22, "float")
       Vin2 = new(  dimSizes22, "float")
       Vin3 = new(  dimSizes22, "float")
       Vin4 = new(  dimSizes22, "float")
       Vin5 = new(  dimSizes22, "float")
       Vin6 = new(  dimSizes22, "float")
       Vin7 = new(  dimSizes22, "float")
   

	SW2 = new(  dimSizes2, "float")
       LW2 = new(  dimSizes2, "float")
       timeout = new( 12, typeof(time0) )
       copy_VarAtts (time0, timeout)
       timeout@calendar = "standard"

       do it = 0, ntim - 1

       year22 = time2(it,0)
       month = time2(it,1)

       if(  year22 .eq. year)  then
       it2 = month - 1

       Vin1(it2, :,:) = fin1->$Varname1$(it, :,:)
       Vin2(it2, :,:) = fin2->$Varname2$(it, :,:)
       Vin3(it2, :,:) = fin3->$Varname3$(it, :,:)
       Vin4(it2, :,:) = fin4->$Varname4$(it, :,:)
 
       Vin5(it2, :,:) = fin5->$Varname5$(it, :,:)
       Vin6(it2, :,:) = fin6->$Varname6$(it, :,:)
       Vin7(it2, :,:) = fin7->$Varname7$(it, :,:)
       timeout(it2)  = time0(it)

	end if
	 end do   ;;  over all time steps in the file
	 timeout@calendar = "standard"
;;;  make the net first then remap 
       SWin  = (  Vin1 - Vin2 + Vin3 - Vin4)
       LWin  = (  Vin5 - Vin6 - Vin7  )
	copy_VarMeta ( Vin1, SWin)
	copy_VarMeta ( Vin5, LWin)
;;;      redefine the missing values
        SW1D      = ndtooned (SWin )
        indices = ind(ismissing(SW1D))
        if( .not.ismissing( indices(0) ))  then
        SW1D( indices ) = undef2
        end if
        SWout = onedtond( SW1D, dimsizes( SWin))
        SWout@_FillValue = undef2
	 delete( indices) 
	 delete( SW1D)

	 LW1D      = ndtooned (LWin )
        indices = ind(ismissing(LW1D))
        if( .not.ismissing( indices(0) ))  then
        LW1D( indices ) = undef2
        end if
        LWout = onedtond( LW1D, dimsizes( LWin))
        LWout@_FillValue = undef2
        delete( indices) 
        delete( LW1D)
;;;;    fill clima arrays 
        climasw =  where( .not. ismissing(SWout), climasw + SWout, climasw )
        sssw2   =  where( .not. ismissing(SWout),  sssw2 + 1., sssw2)
        climalw =  where( .not. ismissing(LWout), climalw + LWout, climalw )
        sslw2   =  where( .not. ismissing(LWout),  sslw2 + 1., sslw2)

;;;  output to file
        yearchar =  sprinti("%0.4i", year)

        fileout  = nameout + yearchar + "/" + Varout1 + "_" + yearchar + ".nc"

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
       filedimdef(fout, dimNames2, dimSizes22, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout1, typeof(SWout),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout1, SWout)

      setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout1$  = (/SWout/)
       delete( fout)
;;;;; second file 
        fileout  = nameout + yearchar + "/" + Varout2 + "_" + yearchar + ".nc"

        n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")

       setfileoption(fout,"DefineMode",True)
       fileattdef( fout, fAtt )            ; copy file attributes

;;;;;;;;;;;;;;;;; define all attributes here     filevardef( ncf, "gw", "float", "lat" )
       filedimdef(fout, dimNames2, dimSizes22, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout2, typeof(LWout),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout2, LWout)

      setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout2$  = (/LWout/)
       delete( fout)
;;;;;
;;;       print( "finished " +  yearchar )
      delete( SWout)
      delete( LWout)

      end do   ;;    over all  years in the data

;;;;  average clima and output too
       sssw2 =  where( sssw2 .gt. 0.,  sssw2 ,  sssw2@_FillValue )
       climasw = climasw/sssw2
       sslw2 =  where( sslw2 .gt. 0.,  sslw2 ,  sslw2@_FillValue )
       climalw = climalw/sslw2
        
       fileout  = nameclima + "/" + Varout1 + "_clim" + ".nc"
	 n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")

       setfileoption(fout,"DefineMode",True)
       fileattdef( fout, fAtt )            ; copy file attributes
	filedimdef(fout, dimNames2, dimSizes22, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout1, typeof(climasw),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout1, climasw)

      setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout1$  = (/climasw/)
       delete( fout)
;;;;  second file 
       fileout  = nameclima + "/" + Varout2 + "_clim" + ".nc"
        n = systemfunc( " rm " +  fileout + " 2> /dev/null")

       fout = addfile( fileout ,"c")

       setfileoption(fout,"DefineMode",True)
       fileattdef( fout, fAtt )            ; copy file attributes
       filedimdef(fout, dimNames2, dimSizes22, dimUnlim2)

       filevardef(fout, "time" , typeof(timeout), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat2),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon2),   (/"lon"/) )
       filevardef(fout,  Varout2, typeof(climalw),  dimNames2 )

       filevarattdef(fout, "time" , timeout)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat2)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon2)                     ; copy lon attributes
       filevarattdef(fout, Varout2, climalw)

      setfileoption(fout,"DefineMode",False)
       fout->time   = (/timeout/)
       fout->lat    = (/lat2/)
       fout->lon    = (/lon2/)
       fout->$Varout2$  = (/climalw/)
       delete( fout)

 end 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
