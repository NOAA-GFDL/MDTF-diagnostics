;;;*******************************************************
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

;;  read  in the data from  NetCDF directory : 

      vardata  = getenv("DATADIR")  ; model data
      outdata =  getenv("ENSO_MSE_WKDIR_COMPOSITE")
      case =  getenv( "CASENAME")
      codedata = getenv ("POD_HOME")  ;; not used

      iy1 = getenv("FIRSTYR")
      iy2 = getenv("LASTYR")

       Varname1 = getenv("rsus_var") ;;  "rsus"
       Varname2 = getenv("rsds_var") ;;  "rsds"
       Varname3 = getenv("rsdt_var") ;;  "rsdt"
       Varname4 = getenv("rsut_var") ;;  "rsut"
       
       Varname5 = getenv("rlus_var") ;;  "rlus"
       Varname6 = getenv("rlds_var") ;;  "rlds"
       Varname7 = getenv("rlut_var") ;;  "rlut"


        undef2 = 1.1E+20

       namein0 = vardata + "/mon/" +  case + "."
       nameout = outdata + "/model/netCDF/DATA/"


       Varout1 =  "SW"
	Varout2 =  "LW" 

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

       setfileoption("nc", "Format",  "NetCDF4")  ;   "NetCDF4Classic"

;;      the time attribute here :
       time = fin1->time

       time2 = calendar_decode2 ( time ,  -5)

       dlat = fin1->lat
       lat2 =  tofloat ( dlat)

       dlon = fin1->lon
       lon2 =  tofloat ( dlon)

;;        tdate = fin->date

       ntim  = dimsizes(time)      ; get dimension sizes
       nlat  = dimsizes(lat2)
       nlon  = dimsizes(lon2)
       dimNames2 = (/"time",  "lat", "lon"/)
       dimSizes2 = (/ 1 ,    nlat,  nlon /)
       dimUnlim2 = (/ True , False, False/)

;;;  as in the case of 3D and 2D plain variables go step by step within the year range iy1-iy2

       do it = 0, ntim - 1

       year = time2(it,0)
       month = time2(it,1)

       if( ( year .ge. iy1 ) .and. ( year .le. iy2 )) then

       Vin1 = fin1->$Varname1$(it, :,:)
       Vin2 = fin2->$Varname2$(it, :,:)
       Vin3 = fin3->$Varname3$(it, :,:)
       Vin4 = fin4->$Varname4$(it, :,:)
 
       Vin5 = fin5->$Varname5$(it, :,:)
       Vin6 = fin6->$Varname6$(it, :,:)
       Vin7 = fin7->$Varname7$(it, :,:)

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

	 LW1D      = ndtooned (LWin )
        indices = ind(ismissing(LW1D))
        if( .not.ismissing( indices(0) ))  then
        LW1D( indices ) = undef2
        end if
        LWout = onedtond( LW1D, dimsizes( LWin))
        LWout@_FillValue = undef2
        delete( indices) 
;;;  output to file
        yearchar =  sprinti("%0.4i", year)
        monthchar =  sprinti("%0.2i", month)
        fileout  = nameout + yearchar + "/" + Varout1 + "_" + yearchar + "-" +  \
                         monthchar + ".grd"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fbindirwrite(fileout , SWout )
	 print ("fileout: "+fileout) 
 
        fileout  = nameout + yearchar + "/" + Varout2 + "_" + yearchar + "-" +  \
                         monthchar + ".grd"
       n = systemfunc( " rm " +  fileout + " 2> /dev/null")
       fbindirwrite(fileout , LWout )
        print("fileout: "+fileout ) 
        print( "   "  ) 

	delete( LWout)
       delete( SWout) 
       delete( LW1D)
       delete( SW1D)
       delete( LWin)
       delete( SWin)


       end if   ;;  in in the year range
       end do   ;;; over all input timesteps 

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
end
