;;;  to calculate PNA indexes needed for plotting : Hgt anomalies + sigma at 500mb

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/calendar_decode2.ncl"


begin

;; for testing 

   vardata =  getenv("DATADIR")   ;;     
   model  =  getenv( "CASENAME")

;;;  DJF seasonal anomalies output LEVEL_01
   dirname1  =  getenv("ENSO_RWS_WKDIR") + "/model/"
   obsname   =  getenv("OBS_DATA") + "/DATA/"

;;  4 centers of PNA index calculation

  tt1 = 2
  tt2 = 10   ;;  exclude March -Nov data 

  xlon1 = (/ 180., 180., 235., 270. /)
  xlon2 = (/ 220., 220., 255., 290. /)
  ylat1 = (/  15.,  40.,  45.,  25. /)
  ylat2 = (/  25.,  50.,  60.,  35. /)

 plev500 = 500.  ;; select pressure level 

  iy1 =  toint( ( getenv("FIRSTYR")) )
  iy2 =  toint( (  getenv("LASTYR")) )
  zgv  =  "zg" ;;  getenv("zg_var")
    levx  = "lev" ;;   getenv("lev_coord")
    lonx  = "lon" ;;  getenv("lon_coord")
    latx  = "lat" ;;  getenv("lat_coord")
    timex = "time" ;;   getenv("time_coord")

    namein   = vardata +  "/mon/"  + model +"." + zgv + ".mon.nc"
    fin = addfile( namein, "r")
;;;  select 500mb level for PNA index calculation
;;;;  get the dimensions and write out
       dlat = fin->$latx$
       lat2 =  tofloat (dlat)

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

;;   convert to mb 
       ff = 1.
        if(  dlev@units .eq. "Pa")
        ff = 0.01
;;         print( dlev@units +  " " )
        end if
	 plevels = tofloat ( dlev)
        plevels = ff * tofloat ( dlev)
        zdim1 = dimsizes( plevels)      
;;   find the index kk5 for  500mb
      kk5 = 0 
    do k = 0, zdim1 - 1
     if( plevels(k) .eq. plev500) 
	kk5 = k 
     end if
    end do 

;; get the 500 mb level data
  
   z500 =  rm_single_dims( fin->$zgv$(:,kk5:kk5, :, :) ) 
   delete( fin) 
;;;  calculate monthly  sigmas only as the composite anomalies are from output data LEVEL_01
;;;   make it DJF mean     [t,y,x]
    z500Sg = stdMonTLL (z500)
    z500Sg( tt1:tt2, :, : ) =  z500Sg@_FillValue ;; mask March - November values 

    z500SgDJF =  dim_avg_n_Wrap(z500Sg, 0)
    delete( z500)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
;;;;  anomalies here :
   namecomp =  dirname1 +   "/netCDF/ELNINO/"  + zgv + ".nc"
   nameclima =  dirname1 +   "/netCDF/"  +  zgv + ".nc"
;;  read and make anomalies at 500 mb  all composites DJF  already 
  fin = addfile( namecomp, "r")
  z500 =  rm_single_dims( fin->$zgv$(:,kk5:kk5, :, :) ) 
  delete( fin) 
  fin = addfile( nameclima, "r")
  z500Clm =  rm_single_dims( fin->$zgv$(:,kk5:kk5, :, :) )
  delete( fin) 
;;; make if anomaly
  z500a = z500
  z500a = z500 - z500Clm

;; define the 4 centers of PNA index 
   pna = new( (/ 5 /), "float")
   i = 0
   pna1  =  wgt_areaave_Wrap(     z500a( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0) 
   pna11 =  wgt_areaave_Wrap( z500SgDJF( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna1 = pna1/pna11

   i = 1
   pna2  =  wgt_areaave_Wrap(     z500a( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna22 =  wgt_areaave_Wrap( z500SgDJF( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna2 = pna2/pna22

   i = 2
   pna3  =  wgt_areaave_Wrap(     z500a( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna33 =  wgt_areaave_Wrap( z500SgDJF( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna3 = pna3/pna33

   i = 3
   pna4  =  wgt_areaave_Wrap(     z500a( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna44 =  wgt_areaave_Wrap( z500SgDJF( {ylat1(i):ylat2(i)}, {xlon1(i):xlon2(i)}),1.0,1.0,0)
   pna4 = pna4/pna44

   pna(0) = pna1 - pna2 + pna3 - pna4
   pna(1) = pna1
   pna(2) = pna2
   pna(3) = pna3
   pna(4) = pna4
;;  print out to output file in LEVEL_04  
    nameout =  dirname1 +   "/netCDF/PNA.txt" 

    system( " rm  " +  nameout )
    asciiwrite ( nameout, pna)
    
end
