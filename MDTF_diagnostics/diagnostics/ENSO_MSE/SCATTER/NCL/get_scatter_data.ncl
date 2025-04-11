;;;   to get the data for SCATTER plots  all are  anomalies 

begin


  varcode = getenv ("POD_HOME")
  vardata  = getenv("ENSO_MSE_WKDIR_COMPOSITE") + "/model/netCDF/"             ; model input
  vardata2 = getenv("ENSO_MSE_WKDIR_MSE") + "/model/netCDF/"
  outdir2  = getenv("ENSO_MSE_WKDIR") + "/SCATTER/netCDF/"    ; envvar set in ENSO_MSE.py

;;;  domains  Central and Eastern Pacific
   lon1 = (/ 160., 220. /)
   lon2 = (/ 200., 280. /)

   lat1 = (/ -10., -5. /)
   lat2 = (/   5.,  5. /)


   prfactor = 2.5E+06

   variable = (/ "pr", "madv", "sw", "lw", "omse", "hfls", "hfss" /)
   tt0 = 0 

   nameout = (/ "central_pacific_MSE_terms_NEW_MODEL" ,  "eastern_pacific_MSE_terms_NEW_MODEL" /)
;;;; PR
   iv = 0
    Varname = variable(iv)
    namein1   = vardata + "/ELNINO/" +  Varname + ".nc"
    nameclima = vardata + "/" + Varname  + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin3 = addfile( nameclima, "r")

    pr1     = fin1->$Varname$
    pr_clim = fin3->$Varname$

    pr1 = prfactor* (pr1 - pr_clim)

;;    MADV
    iv = 1
    Varname = variable(iv)
    namein1   = vardata2 + "/ELNINO/MSE_" + Varname + ".nc"
    nameclima = vardata2 + "/MSE_" + Varname  + ".nc"

    fin1 = addfile( namein1, "r")
    fin3 = addfile( nameclima, "r")
    
    madv1     = fin1->$Varname$
    madv_clim = fin3->$Varname$
    
    madv1 =  madv1 - madv_clim
;;;;   FRAD
 
    namein1   = vardata + "/ELNINO/sw.nc"
    nameclima1 = vardata + "/sw_clim.nc"

    namein2   = vardata + "/ELNINO/lw.nc"
    nameclima2 = vardata + "/lw_clim.nc"


    fin1 = addfile( namein1, "r")
    fin3 = addfile( nameclima1, "r")

    fin11 = addfile( namein2, "r")
    fin33 = addfile( nameclima2, "r")

     sw1      = fin1->sw
     sw_clim1 = fin3->sw
     lw1      = fin11->lw
     lw_clim1 = fin33->lw

     frad1 = lw1
     frad1 = (lw1 - lw_clim1) + (sw1 - sw_clim1)
;;;;;  OMSE
    iv = 4
    Varname = variable(iv)
    namein1   = vardata2 + "/ELNINO/MSE_" + Varname  + ".nc"
    nameclima = vardata2 + "/MSE_" + Varname  + ".nc"

    fin1 = addfile( namein1, "r")
    fin3 = addfile( nameclima, "r")

    omse1     = fin1->$Varname$
    omse_clim = fin3->$Varname$
   
    omse1 =  omse1 - omse_clim
   
;;;    LHF 
    iv = 5
    Varname = variable(iv)
    namein1   = vardata + "/ELNINO/" + Varname  + ".nc"
    nameclima = vardata + "/" + Varname + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin3 = addfile( nameclima, "r")

    lhf1     = fin1->$Varname$
    lhf_clim = fin3->$Varname$

    lhf1 =  (lhf1 - lhf_clim)
;;;  SHF 
    iv = 6
    Varname = variable(iv)
    namein1   = vardata + "/ELNINO/" + Varname  + ".nc"
    nameclima = vardata + "/" + Varname  + "_clim.nc"

    fin1 = addfile( namein1, "r")
    fin3 = addfile( nameclima, "r")

    shf1     = fin1->$Varname$
    shf_clim = fin3->$Varname$

    shf1 =  (shf1 - shf_clim)

;;;;   make the area averages :   loop over two domains
  do i = 0, 1     
   pr2   = wgt_areaave_Wrap(  pr1(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0) 
   madv2 = wgt_areaave_Wrap( madv1( {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
   frad2 = wgt_areaave_Wrap( frad1(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
   omse2 = wgt_areaave_Wrap( omse1( {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
   lhf2  = wgt_areaave_Wrap( lhf1(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)
   shf2  = wgt_areaave_Wrap( shf1(tt0, {lat1(i):lat2(i)},  {lon1(i):lon2(i)}), 1., 1., 0)

;;  output as ascii :
   
   nameout2 = outdir2 + "/" + nameout(i) + ".txt" 

    line = sprintf("%12.2f",pr2) +  " " + \
           sprintf("%12.2f",madv2) +  " " + \
           sprintf("%12.2f",frad2) +  " " + \
           sprintf("%12.2f",omse2) +  " " + \
           sprintf("%12.2f",lhf2) +  " " + \
           sprintf("%12.2f",shf2) 

    asciiwrite( nameout2, line)

   delete([/ pr2, madv2, frad2, omse2, lhf2, shf2, line /]) 
 end do 

end
