; This file is part of the MJO_teleconnection module of the MDTF code package (see LICENSE.txt)

;-------------------------------------------------------------------------------------
;Calculate pattern correlations 
;Written by Stephanie Henderson
;-------------------------------------------------------------------------------------

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

;-- Domain --
    Domain = "Pacific"
   
print("------------------------------------------------------------------------------------")
print("** Calculating teleconnection patttern correlation of all MJO phase for Z250-hPa ** ")
print("------------------------------------------------------------------------------------")

   print("Domain: " + Domain)
   Model = getenv("CASENAME") 
   print("Dataset: " + Model)


;---------------------------------------------------------------------------------
;--directory for output files--
;---------------------------------------------------------------------------------
     print("Reading Geopotential height data for model : "+Model)
     
     diri   = getenv("WK_DIR")+"/model/netCDF/"
     dirobs = getenv("OBS_DATA")+"/"  
     filgeom    = "geop_compositesP_hgt250_"+Model+".nc"
     filgeobs    = "geop_compositesP_hgt250.nc"
     print("Input data path (rean.)  :" + dirobs)
     print("Input data path (Model) :" + diri)
     print("Input data file observation geop composite :" + filgeom)
     print("Input data file model geop composite :" + filgeom)
;---------------------------------------------------------------------------------

;--read in model data--
    a = addfile(diri + filgeom,"r")    
    geop_composites_CMIP5 = a->geop_composites   ;[lag,phase,lat,lon]
    lat2 = a->lat
    lon2 = a->lon 

;-- read in reanalysis data --
    print("Reading Geopotential height data for reanalysis")
    
    b = addfile(dirobs + filgeobs ,"r")    	   ;read in datasets
    geop_composites = b->geop_composites
    lat = b->lat
    lon = b->lon
    ;print(lat)
   
    print("data reading is completed")
print("------------------------------------------------------------------------------------")
    geop_composites_CMIP5@_FillValue = -999
    geop_composites@_FillValue = -999


;- interpolate to reanalysis resolution --
    print("interpolate")

   geop_int = linint2 (lon2,lat2,geop_composites_CMIP5,True,lon,lat, 0)
;  var_CMIP5t = linint2 (lon2,lat2,var_CMIP5tt,True,lon,lat, 0)

   delete(geop_composites_CMIP5)
   delete(lat2)
   delete(lon2)
   print("interpolation done")
print("------------------------------------------------------------------------------------")
;-- isolate domain --
   print("isolating Pacific domain")

   if(Domain .eq. "Pacific")
    ind_lon = ind(lon .le. 300 .and. lon.ge. 130)
;   ind_lon = ind(lon .le. 230 .and. lon.ge. 60)
   geop_hgt = geop_int(:,:,:,ind_lon)
   geop_obs = geop_composites(:,:,:,ind_lon)
   lonnew = lon(ind_lon)

   delete(geop_int)
   delete(geop_composites)
   delete(lon)

   geop_int = geop_hgt
   geop_composites = geop_obs
   lon = lonnew

   delete(geop_obs)
   delete(geop_hgt)
   delete(lonnew)
   end if


   ind_lat = ind(lat .ge. 15 .and. lat .le. 79.5)
   hgt_obs = geop_composites(:,:,ind_lat,:)
   hgt = geop_int(:,:,ind_lat,:)

   latnew = lat(ind_lat)
   delete(lat)
   lat = latnew
   delete(latnew)
   delete(geop_composites)
   delete(geop_int)
   delete(ind_lat)
   delete(ind_lon)

   ; printVarSummary(hgt)
   print("done") 

print("------------------------------------------------------------------------------------")
;-- calculate the cross-correlation between the patterns --
    print("calculate the cross-correlation between the patterns")

    clat = cos(0.01745329*lat)        ; cos(lat) weight
    ccr = pattern_cor(hgt, hgt_obs, clat, 0)

    ;print(dimsizes(ccr))
    ;print(max(ccr))
    ;print(min(ccr))
    delete(hgt)
    delete(hgt_obs)
    delete(clat)


    phase = ispan(1,8,1)
    lag = (/1,2,3,4/)

;do i=0,dimsizes(phase)-1
; do j=0,3
;  print("phase: " + phase(i) + "  pentad: " + lag(j) + "  corr:" + ccr(j,i))
; end do
;end do



     ccr_all1 = new((/dimsizes(Model),dimsizes(phase)/),typeof(ccr))
    ;printVarSummary(ccr_all1)
    ;print(ccr(0,:))
     ccr_all1 = ccr(0,:)   ;pentad 0 only

     ccr_all = tofloat(ccr_all1) ; CMIP5 model are saved as float and ccr_all1 as double

   ; printVarSummary(ccr_all)
    print("done")
;--write ascii file--
     print("writing correlation values into an ascii file")
     
    
     print("Output path: "+ dirobs)
     
     if(Domain .eq. "Pacific")
     opt=True 
     opt@fout = diri + "corrMJO_Pac_250mb_"+Model         
     write_matrix(ccr,"8f10.4",opt)
     delete(opt)
     end if
     
     print("output file : " + "corrMJO_Pac_250mb_"+Model)

     delete(ccr)
     delete(a)
     delete(lat)
     delete(lon)


print("----------------------------------------------------------------------------------")
print("Reading phase pattern correlation data for CMIP5 Models")
;-----------------------------------------------------------------------------------------
    
    Z250_crr = new((/11,8/),float)
;    printVarSummary(Z250_crr)

  
    crrt = asciiread(dirobs+"ccr_Z250comp_CMIP5",(/10,8/),"float")
  ;  print(crrt)
    
   Z250_crr(0:9,:) =crrt(:,:)
   Z250_crr(10,:) = ccr_all
   delete(crrt)
;  print(Z250_crr)

;-----------------------------------------------------------------------------------------
        print("Adding New model pattern Corr. values to CMIP5 Pattern Corr. array")
;-----------------------------------------------------------------------------------------

     opt=True
     opt@fout = diri+"ccr_Z250comp_CMIP5_updated"
     write_matrix(Z250_crr,"8f10.4",opt)
     delete(opt)


print("Ascii file for pattern correlation is updated with new model's Pat. Corr.  values")
print("saving upadated pat. corr. ascii file at :"+ diri)
print("saving upadated pat. corr. file name :"+ "ccr_Z250comp_CMIP5_updated")
print("Process of Pattern correlation calculation is completed now")
print("----------------------------------------------------------------------------------")
print("----------------------------------------------------------------------------------")


end
