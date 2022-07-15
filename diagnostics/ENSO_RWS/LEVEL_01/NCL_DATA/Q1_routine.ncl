;;  ncl code to calculate anomaly of r vertically integrated Q1 heating 
;;   calculates el nino/la nina composites + climatology
;;   the anomaly is the difference 


begin

   indir   = getenv("ENSO_RWS_WKDIR") + "/model/netCDF" 


      mode = (/ "ELNINO", "LANINA" /) 
;     3 D vars
       zgv  = "zg" ;; 
       uav  = "ua" ;;;  
       vav  = "va" ;;;  
       tav  = "ta" ;;   
       dTv  =  "dT"
       wapv = "wap" ;;;   

       levx  = "lev" ;;  
       lonx  = "lon" ;; 
       latx  = "lat" ;;
       timex = "time" ;; 

   gg = 9.81
   cp = 1004. 
;;;  climatology first
 
;;  hgt    
     namein = indir + "/"  + zgv + ".nc"
 
     f1 = addfile( namein, "r")
     hgt = f1->$zgv$
     time = f1->$timex$
     plev = f1->$levx$
     lat = f1->$latx$
     lon = f1->$lonx$
     delete(f1)
;;;   u
     namein = indir + "/"  + uav + ".nc"
     f1 = addfile( namein, "r")
     ua = f1->$uav$
     delete(f1)

     namein = indir + "/"  + vav + ".nc"
     f1 = addfile( namein, "r")
     va = f1->$vav$
     delete(f1)

     namein = indir + "/"  + tav + ".nc"
     f1 = addfile( namein, "r")
     ta = f1->$tav$
     delete(f1)

     namein = indir + "/"  + wapv + ".nc"
     f1 = addfile( namein, "r")
     wap = f1->$wapv$
     delete(f1)

     namein = indir + "/"  + dTv + ".nc"
     f1 = addfile( namein, "r")
     dtemp = f1->$dTv$
     delete(f1)
;  fill undefined
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill(    ua, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill(    va, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill(    ta, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill(   wap, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( dtemp, gtype, guess, nscan, eps, relc, opt)

;;;    
;;;;    convert  temperatures in K to potential temp. 
      dtemp@units = "K"
      ta@units = "K"
      theta  = ta
      dtheta = ta
      theta =  pot_temp( tofloat(plev)*100., ta, 1, False)  ; 
      dtheta = pot_temp( tofloat(plev)*100., dtemp, 1, False)   

;;   calculate the horizontal advection of theta
      gridType = 1
      long_name = "horizontal advection of potential temperature"
      units     = "K" ;; 
      opt_adv  = 0 
      theta_adv = advect_variable(ua, va, theta, gridType, long_name, units, opt_adv)

;; fill back the missing 
      ta =   where( .not.ismissing( hgt), ta, hgt@_FillValue)
      theta = where( .not.ismissing( hgt), theta, hgt@_FillValue)
      dtheta =   where( .not.ismissing( hgt), dtheta, hgt@_FillValue) 
      theta_adv =  where( .not.ismissing( hgt),  theta_adv, hgt@_FillValue) 

;;    next is vertical advection of theta
      theta_omg = wap * center_finite_diff_n( theta, tofloat(plev*100.), False, 0, 1)
;;  sum up and integrate in vertical 
    q1 = ta
    q1 = (ta/theta)*( dtheta + theta_adv + theta_omg) 

    rr = 1.
    dplev =  tofloat( center_finite_diff ( plev*100., rr,False,0)) 

    nlevs = dimsizes( dplev) 
    do k = 0, nlevs-1
     q1(:,k,:,:) = -q1(:,k,:,:) * dplev(k)/gg
    end do 

    q1clima = cp *  dim_sum_n(q1,1)
;;  attach lon lat to q1clima
       q1clima!2="lon"
       q1clima!1="lat"
       q1clima!0="time"

       q1clima&lat = lat
       q1clima&lon = lon
       q1clima&time = time
       q1clima@_FillValue = hgt@_FillValue
       q1clima@unit = "[W/m2]"  
       Varname2 = "q1"

;;     just in a case output q1clima to the file 
      nameout = indir + "/" + "q1.nc"
      n = systemfunc( " rm " +  nameout + " 2> /dev/null")
      fout = addfile( nameout,"c")
      setfileoption(fout,"DefineMode",True)
  
       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes
       
       dimSizes = dimsizes( q1clima) 
       dimUnlim2 = (/ True, False, False/)
       dimNames2 = (/"time", "lat", "lon"/)

       filedimdef(fout, dimNames2, dimSizes, dimUnlim2)
       filevardef(fout, "time" , typeof(time), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  Varname2, typeof(q1clima),  dimNames2 )

       filevarattdef(fout, "time" , time)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                     ; copy lon attributes
       filevarattdef(fout, Varname2, q1clima)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/time/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname2$  = (/q1clima/)
       delete( fout)  

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;  
;;;   now loop over El Nino/La Nina cases and output q1elnino/ q1lanina
    Varname2 = "q1"
    do imode = 0, 1 
     indir2 = indir + "/"  +  mode(imode) 
     namein = indir2 +  "/" +  zgv + ".nc"

     f1 = addfile( namein, "r")
     hgt = f1->$zgv$
     time = f1->$timex$
     plev = f1->$levx$
     lat = f1->$latx$
     lon = f1->$lonx$
     delete(f1)
;;;   u
     namein = indir2 + "/"  + uav + ".nc"
     f1 = addfile( namein, "r")
     ua = f1->$uav$
     delete(f1)

     namein = indir2 + "/"  + vav + ".nc"
     f1 = addfile( namein, "r")
     va = f1->$vav$
     delete(f1)

     namein = indir2 + "/"  + tav + ".nc"
     f1 = addfile( namein, "r")
     ta = f1->$tav$
     delete(f1)

     namein = indir2 + "/"  + wapv + ".nc"
     f1 = addfile( namein, "r")
     wap = f1->$wapv$
     delete(f1)

     namein = indir2 + "/"  + dTv + ".nc"
     f1 = addfile( namein, "r")
     dtemp = f1->$dTv$
     delete(f1)

;  fill undefined
  nscan = 500             ; usually *much* fewer
  eps   = 0.001            ; variable depended
  gtype =  True           ; "gendat" does not generate cyclic fields
  guess =  1               ; use zonal means
  relc  = 0.6              ; standard relaxation coef
  opt   = 0
  poisson_grid_fill(    ua, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill(    va, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill(    ta, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill(   wap, gtype, guess, nscan, eps, relc, opt)
  poisson_grid_fill( dtemp, gtype, guess, nscan, eps, relc, opt)

;;;;    convert  temperatures in K to potential temp.
      theta = ta
      dtheta = ta
      theta =  pot_temp( tofloat(plev)*100., ta, 1, False)  ; dim=0
      dtheta = pot_temp( tofloat(plev)*100., dtemp, 1, False)

;;   calculate the horizontal advection of theta
      gridType = 1
      long_name = "horizontal advection of potential temperature"
      units     =   "K/s"
      opt_adv  = 0
      theta_adv = advect_variable(ua, va, theta, gridType, long_name, units, opt_adv)

;; fill back the missing
      ta =   where( .not.ismissing( hgt), ta, hgt@_FillValue)
      theta = where( .not.ismissing( hgt), theta, hgt@_FillValue)
      dtheta =   where( .not.ismissing( hgt), dtheta, hgt@_FillValue)
      theta_adv =  where( .not.ismissing( hgt),  theta_adv, hgt@_FillValue)

;;    next is vertical advection of theta
      theta_omg = wap * center_finite_diff_n( theta, tofloat(plev*100.), False, 0, 1)

;;  sum up and integrate in vertical
    q1 = ta
    q1 = (ta/theta)*( dtheta + theta_adv + theta_omg)

;;   fill back missing 
     q1 =  where( .not.ismissing( hgt), q1, hgt@_FillValue) 

    rr = 1.
    dplev =  tofloat( center_finite_diff ( plev*100., rr,False,0) )

    nlevs = dimsizes( dplev)
    do k = 0, nlevs-1
     q1(:,k,:,:) = -q1(:,k,:,:) * dplev(k)/gg
    end do

    qq1 = cp *  dim_sum_n(q1,1)
;;  attach lon lat to q1
       qq1!2="lon"
       qq1!1="lat"
       qq1!0="time"

       qq1&lat = lat
       qq1&lon = lon
       qq1&time = time
       qq1@_FillValue = hgt@_FillValue
       qq1@unit = "[W/m2]"
;;     just in a case output q1clima to the file
      nameout = indir + "/" + mode(imode) +  "/q1.nc"
      n = systemfunc( " rm " +  nameout + " 2> /dev/null")
      fout = addfile( nameout,"c")
      setfileoption(fout,"DefineMode",True)
 
       fAtt               = True            ; assign file attributes
       fAtt@title         = "NCL created netcdf"
       fAtt@source_file   =  "original-file.nc"
       fAtt@Conventions   = "None"
       fAtt@creation_date = systemfunc ("date")
       fileattdef( fout, fAtt )            ; copy file attributes

       dimSizes = dimsizes( qq1)
       dimUnlim2 = (/ True, False, False/)
       dimNames2 = (/"time", "lat", "lon"/)

       filedimdef(fout, dimNames2, dimSizes, dimUnlim2)
       filevardef(fout, "time" , typeof(time), (/"time"/) )
       filevardef(fout, "lat"  , typeof(lat),   (/"lat"/) )
       filevardef(fout, "lon"  , typeof(lon),   (/"lon"/) )
       filevardef(fout,  Varname2, typeof(qq1),  dimNames2 )

       filevarattdef(fout, "time" , time)                  ; copy time attributes
       filevarattdef(fout, "lat"  , lat)                     ; copy lat attributes
       filevarattdef(fout, "lon"  , lon)                     ; copy lon attributes
       filevarattdef(fout, Varname2, qq1)

       setfileoption(fout,"DefineMode",False)
       fout->time   = (/time/)
       fout->lat    = (/lat/)
       fout->lon    = (/lon/)
       fout->$Varname2$  = (/qq1/)
       delete( fout) 
    end do  

end
