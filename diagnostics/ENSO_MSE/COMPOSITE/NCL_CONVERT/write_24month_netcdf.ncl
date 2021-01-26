;;;   to convert binary to easy netcdf for 24 month ENSO evolution 
;;;; 

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"

begin

     outdir  = getenv("ENSO_MSE_WKDIR_COMPOSITE") +"/model" ; envvar set in ENSO_MSE.py,
                                ;processed output from other scripts in this package
     varcode = getenv ("POD_HOME")


;;;  read in the dimensions first 
        modes = (/ "ELNINO", "LANINA" /)
   ivar3 = 6 
    variables3 = (/ "zg" , "ua", "va", "ta", "hus", "wap"   /)
    varnames3 = (/ "zg", "ua", "va",  "ta", "hus", "wap" /)
    varunits3 =  (/ "[m]", "[m/s]", "[m/s]", "[deg. C]", "[g/g]", "[Pa/s]" /)
    long_name3 = (/ "geopotential height", "zonal wind component", "meridional wind component",   "temperature", "specific humidity", "vertical velocity" /)

  ivar2 = 6
    variables2 = (/ "ts" , "sw", "lw", "hfls", "hfss", "pr" /)
    varnames2 = (/ "ts" , "sw", "lw", "hfls",  "hfss" , "pr" /)
    varunits2 =  (/ "[deg. C]", "[W/m2]", "[W/m2]", "[W/m2]", "[W/m2]", "[kg/m2/sec]" /)
    long_name2 = (/ "skin surface temperature ", "net shortwave radiation", "net longwave radiation",  "latent heat flux ", "sensible heat flux", "precipitation " /) 

     mode = (/ "ELNINO", "LANINA" /)

      parameter_name = varcode + "/shared/parameters.txt"
      name_dimensions = outdir  + "/netCDF/DATA/xyz_dimensions.txt"
      name_lon = outdir + "/netCDF/DATA/longitude.out"
      name_lat = outdir + "/netCDF/DATA/latitude.out"
      name_plevs = outdir + "/netCDF/DATA/plevels.out"


;;;;  read in the parameter data lon/lat/plevs 
       dataxyz  = asciiread(name_dimensions,-1,"string")
       xdum  = str_get_field(dataxyz(0), 1," ")
       xmax =  stringtointeger( xdum)
       ydum  = str_get_field(dataxyz(1), 1," ")
       ymax =  stringtointeger( ydum)
       zdum  = str_get_field(dataxyz(2), 1," ")
       zmax =  stringtointeger( zdum)
       undef2 = 1.1E+20 
;;;  read in the lon/lat plevs here !!
      t24 = 24 
      dims3 = (/ t24, zmax, ymax, xmax /)
      dims2 = (/ t24, ymax, xmax /)
       lon = new( xmax, "float")
       lat = new( ymax, "float")
       lev = new( zmax, "float")
	lon@units = "degrees_east"
       lon@_FillValue = undef2
       lon@long_name = "longitude"

       lat@units = "degrees_north"
       lat@long_name = "latitude"
       lat@_FillValue = undef2

       lev@units  = "mb"
       lev@long_name = "pressure levels "
       lev@_FillValue = undef2
 

       lon = fbindirread (name_lon, 0, (/ xmax /) , "float")
       lat = fbindirread (name_lat, 0, (/ ymax /) , "float")
       lev = fbindirread (name_plevs, 0, (/ zmax /) , "float")

      time = new( t24, "float" )
      time = (/ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 , 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23 /)

       time@units  = "months since 0001-01-01"
       time@long_name = "24 month evolution month, year 0 and year +1 "
       time@_FillValue = -9999

;;;;;   3D variables 
       dimNames3 = (/"time", "lev",  "lat", "lon" /)
       dimSizes3 = (/ -1   ,  zmax,  ymax, xmax /)
       dimUnlim3 = (/ True , False, False, False/)
        
        datain3 =  new(  dims3, "float")
        datain3!3="lon"
        datain3!2="lat"
        datain3!1="lev"
        datain3!0="time"

        datain3&lon = lon
        datain3&lat = lat
        datain3&lev = lev
        datain3&time = time

        datain3@_FillValue =  undef2

;;;;    2D variables 
       dimNames2 = (/"time", "lat", "lon" /)
       dimSizes2 = (/ -1   ,  ymax, xmax /)
       dimUnlim2 = (/ True ,  False, False/)

        datain2 =  new(  dims2, "float")
        datain2!2="lon"
        datain2!1="lat"
        datain2!0="time"

        datain2&lon = lon
        datain2&lat = lat
        datain2&time = time
        datain2@_FillValue =  undef2

;; predefine file attributes

      do n = 0, 1  ;;;  loop over El Nino/La Nina 
      do iv = 0,  ivar3 - 1
      namein  = outdir + "/netCDF/24MONTH_" +  mode(n) +  "/BIN/" + variables3(iv) + ".grd"
      nameout = outdir + "/netCDF/24MONTH_" +  mode(n) +  "/" + varnames3(iv) + ".nc"
;;;  read in the data 

       datain3@units     = varunits3(iv)
       datain3@long_name = long_name3(iv)

       datain3  = fbindirread (namein, 0, dims3 , "float")
;;  set the dimensions and units 
;===================================================================
; create global attributes of the file
;===================================================================
     system("/bin/rm -f " + nameout)
     fout =  addfile( nameout, "c" )
     setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
	fAtt@title         = "24 month evolution of " + mode(n) + "  year 0 developing and year 1 decaying phase" 
;;; 	fAtt@Conventions   = "None"   
	fAtt@creation_date = systemfunc ("date")        
	fileattdef( fout, fAtt ) 
;;;;;;;;;;;;;;;;; define all attributes here 

	filedimdef(fout, dimNames3, dimSizes3, dimUnlim3)

       filevardef(fout, "time" , typeof(time),  (/"time"/) ) 
       filevardef(fout, "lev"  , typeof(lev),   (/"lev"/) )                     
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )                       
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  varnames3(iv), typeof(datain3),  dimNames3 )   

       filevarattdef(fout,"time" ,time)                    ; copy time attributes
       filevarattdef(fout,"lev"  ,lev)                     ; copy lev attributes
       filevarattdef(fout,"lat"  ,lat)                     ; copy lat attributes
       filevarattdef(fout,"lon"  ,lon)                     ; copy lon attributes
       filevarattdef(fout, varnames3(iv), datain3)               

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/time/)     
       fout->lev    = (/lev/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/) 
       fout->$varnames3(iv)$  = (/datain3/)
       delete( fout) 
       
      end do  ;;  over 3D variables 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;  similar for the 2 D variables 
 

    do iv = 0, ivar2 - 1
      namein = outdir + "/netCDF/24MONTH_" +  mode(n) +  "/BIN/" + variables2(iv) + ".grd"
      nameout = outdir + "/netCDF/24MONTH_" +  mode(n) +  "/" + varnames2(iv) + ".nc"
;;;  read in the data

       datain2@units     = varunits2(iv)
       datain2@long_name = long_name2(iv)

;;  set the dimensions and units
;===================================================================
; create global attributes of the file
;===================================================================
     system("/bin/rm -f " + nameout)
     fout =  addfile( nameout, "c" )
     setfileoption(fout,"DefineMode",True)

       fAtt               = True            ; assign file attributes
       fAtt@title         = "24 month evolution of " + mode(n) + "  year 0 developing and year 1 decaying phase"
;;;    fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )
;;;;;;;;;;;;;;;;; define all attributes here

       filedimdef(fout, dimNames2, dimSizes2, dimUnlim2)

       filevardef(fout, "time" , typeof(time),  (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  varnames2(iv), typeof(datain2),  dimNames2 )

       filevarattdef(fout,"time" ,time)                    ; copy time attributes
       filevarattdef(fout,"lat"  ,lat)                     ; copy lat attributes
       filevarattdef(fout,"lon"  ,lon)                     ; copy lon attributes
       filevarattdef(fout, varnames2(iv), datain2)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/time/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$varnames2(iv)$  = (/datain2/)
       delete( fout)

      end do  ;;  over 2D variables
    
     end do   ;;  over 2 modes
end

