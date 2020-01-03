;;;*******************************************************
;
;   to  regridded data to make monthly climatologies 
;          output binaries as is the input
;*******************************************************
; These files are loaded by default in NCL V6.2.0 and newer
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
; load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"

begin 

;;  read  in the data from   regridded binaried 

  
      outdir  = getenv("ENSO_MSE_WKDIR_COMPOSITE")+"/model/"  ; set in ENSO_MSE.py
      case =  getenv( "CASENAME")
      codedata = getenv ("POD_HOME") ;; [not used]
        iy11 =  getenv("FIRSTYR")
        iy22 =  getenv("LASTYR") 


       dimension_name =  outdir+"/netCDF/DATA/xyz_dimensions.txt"
       
	namein = outdir + "netCDF/DATA/"

	nameout = outdir + "netCDF/CLIMA/" 

;;;    selected variables
	Varnamesin3   = (/ "Z", "U", "V", "T", "Q","OMG" /)
 	ivar3 = dimsizes( Varnamesin3)

	Varnamesin2   = (/ "SW", "LW", "SHF", "LHF", "TS", "PR" /)
       ivar2 = dimsizes( Varnamesin3)
;; 
	ivar32 = ivar3 + ivar2 

       undef2 = 1.1E+20
	
;;;  read in the dimensions 
       data  = asciiread(dimension_name,-1,"string")
        xmax = stringtointeger(str_get_field(data(0), 1," "))
        ymax = stringtointeger(str_get_field(data(1), 1," "))
        zmax = stringtointeger(str_get_field(data(2), 1," "))
          
	  t12 = 12
	  im1 = 1
	  im2 = 12
       
        iy1 = tointeger(iy11)
	 iy2 = tointeger(iy22)

	 tmax = (iy2 - iy1 + 1)* 12

	 dims3 = (/ zmax, ymax, xmax /)
        dim3_names =  (/ "lev",  "lat",  "lon" /) 

        i3D = 1
         if( i3D .eq. 1) 
         do ivar =  0, ivar3 - 1
	    clima = new( (/ t12, zmax, ymax, xmax /), "float")
           clima@_FillValue = undef2

           datain3  = new(  dims3, "float")
	    datain3!0 = "lon"
	    datain3!1 = "lat"
	    datain3!2 = "lev"
           datain3@_FillValue = undef2
	    ss3 = new(  dims3, "float")
           ss3@_FillValue = undef2
           ss3 = 0.

           datain  = new(  dims3, "float")
           datain!0 = "lon"
           datain!1 = "lat"
           datain!2 = "lev"
           datain@_FillValue = undef2
           
	   Varname = Varnamesin3(ivar)
;;;         fill in  clima for averaging 
         
         ivv1 = ivar + 1
	  ;;;  print( " Started climatology of  variable : " + Varname + "  " +  ivv1 + "/" + ivar32 )    
          do im = im1, im2

	    datain3 = 0.
           ss3 = 0.
           do iy = iy1, iy2
	     yearchar =  sprinti("%0.4i", iy)
            monthchar =  sprinti("%0.2i", im)
            filein = namein +  yearchar + "/" +  Varname + "_" + yearchar + "-" +  \
                         monthchar + ".grd"
           if( fileexists(filein) )
 	    datain  = fbindirread (filein, 0, dims3 , "float")             
           datain3 =  where( .not. ismissing(datain), datain3 +  datain, datain3)
           ss3 =  where( .not. ismissing(datain),  ss3 + 1., ss3)
           end if 
   	   end do  ;   over  years 
;;;  average a given month  and fill clima variable 
         ss3 =  where( ss3 .gt. 0.,  ss3 ,  ss3@_FillValue )
         datain3 = datain3/ss3
          it = im - 1
          clima( it, :, :, :) = datain3(:, :, :)
      end do  ;  over all months  
;;;;  write  out a;;  clima data          
	 fileout = nameout +  Varname + "_clim.grd"
	 n = systemfunc( " rm " +  fileout + " 2> /dev/null")
         print("ENSO_MSE/COMPOSITE/clima_routine.ncl writing "+fileout)
       fbindirwrite(fileout , clima)
       delete(clima) 
       delete( datain3) 
	end do  ;;; over input 3D variables 
;;	 print(  " 3D var done " )
        delete( datain) 
	 end if 

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;   the same for 2D variables 

	 dims2 = (/  ymax, xmax /)

        do ivar = 0, ivar2 - 1
         Varname = Varnamesin2(ivar)
        clima2 = new((/  t12, ymax, xmax /), "float")
        clima2@_FillValue = undef2

         datain2  = new((/ ymax, xmax /), "float")
         datain2@_FillValue = undef2
         datain2!0 = "lon"
         datain2!1 = "lat"
         datain2 = 0.

         ss2  = new((/ ymax, xmax /), "float")
         ss2@_FillValue = undef2
         ss2!0 = "lon"
         ss2!1 = "lat"
         ss2 = 0.

          datain  = new(  dims2, "float")
          datain!0 = "lon"
          datain!1 = "lat"
          datain@_FillValue = undef2


        do im = im1, im2
 
        datain2 = 0.
        ss2 = 0.
;;;        ivv1 = ivar3 +  ivar + 1
;;;   print( " Started climatology of  variable : " + Varname + "  " +  ivv1 + "/" + ivar32 ) 
 
	   do iy = iy1, iy2
           yearchar =  sprinti("%0.4i", iy)
           monthchar =  sprinti("%0.2i", im)
           filein = namein +  yearchar + "/" +  Varname + "_" + yearchar + "-" +  \
                         monthchar + ".grd"
           if( fileexists(filein) )
            datain  = fbindirread (filein, 0, dims2 , "float")
            datain2 =  where(.not. ismissing(datain),  datain2 +  datain, datain2)
            ss2 =  where(.not. ismissing(datain),  ss2 + 1, ss2)
	    end if 
         end do  ;  over all years
;;;  make climatology
        ss2 =  where( ss2 .gt. 0.,  ss2 ,  ss2@_FillValue )
        datain2 = datain2/ss2
          it = im - 1
          clima2( it, :, :) = datain2( :, :)
         end do  ;  over all months

	 fileout = nameout +  Varname + "_clim.grd"
        n = systemfunc( " rm " +  fileout + " 2> /dev/null")
        fbindirwrite(fileout , clima2)
        delete( clima2)
        delete( datain2) 
      end do   ;; over variables
        delete( datain)
 end  
