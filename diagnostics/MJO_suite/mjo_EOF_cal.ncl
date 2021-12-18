; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

;***********************************************************
; Combined EOFs
;***********************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"  
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"  
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

  routine_name = "mjo_EOF_cal.ncl"
   casename = getenv("CASENAME")
   file_dir = getenv("WK_DIR")+"/model/netCDF/"

   neof    =  2

   latS    = -20
   latN    =  20

;   ymdStrt = 19950101                         ; start yyyymmdd
;   ymdLast = 19991231                         ; last  

;   yrStrt  = ymdStrt/10000
;   yrLast  = ymdLast/10000

   pltDir  = getenv("WK_DIR")+"/model/PS/"                             ; plot directory
   pltType = "ps"  
   pltName = "mjoclivar"                      ; yrStrt+"_"+yrLast
  
;   diri    = "/Users/shea/Data/AMWG/"         ; input directory   

   filolr     = file_dir+casename+".rlut.day.anom.nc"
   filu850    = file_dir+casename+".u850.day.anom.nc"
   filu200    = file_dir+casename+".u200.day.anom.nc"

;************************************************
; create BandPass Filter
;************************************************
  ihp      = 2                             ; bpf=>band pass filter
  nWgt     = 201
  sigma    = 1.0                           ; Lanczos sigma
  fca      = 1./100.
  fcb      = 1./20.
  wgt      = filwgts_lanczos (nWgt, ihp, fca, fcb, sigma )

;***********************************************************
; Find the indices corresponding to the start/end times
;***********************************************************
   f       = addfile (filolr , "r")                         
   TIME    = f->time                          ; days since ...
   YMD     = cd_calendar(TIME, -2)            ; entire (time,6)

   ymdStrt = min(YMD(:))
   ymdLast = max(YMD(:))
   yrStrt  = ymdStrt/10000
   yrLast  = ymdLast/10000
  
;   iStrt   = ind(YMD.eq.ymdStrt)              ; index start
;   iLast   = ind(YMD.eq.ymdLast)              ; index last 
   delete(TIME)
   delete(YMD )

;***********************************************************
; Read anomalies
;***********************************************************
   work    = f->rlut(:,{latS:latN},:) 
   OLR    = dim_avg_Wrap(work(time|:,lon|:,lat|:))

   f       = addfile (filu850 , "r")                         
   work    = f->u850(:,{latS:latN},:) 
   U850    = dim_avg_Wrap(work(time|:,lon|:,lat|:))

   f       = addfile (filu200 , "r")                         
   work    = f->u200(:,{latS:latN},:) 
   U200    = dim_avg_Wrap(work(time|:,lon|:,lat|:))  ; (time,lon)

   dimw    = dimsizes( work )
   ntim    = dimw(0)
   nlat    = dimw(1)
   mlon    = dimw(2)
   delete(work)

   lon     = f->lon                                           
   time    = f->time             ; days since ...
   date    = cd_calendar(time, -2)            ; yyyymmdd

;************************************************
; Apply the band pass filter to the original anomalies
;************************************************
  rlut  = wgt_runave_Wrap ( OLR(lon|:, time|:), wgt, 0)
  u850  = wgt_runave_Wrap (U850(lon|:, time|:), wgt, 0)
  u200  = wgt_runave_Wrap (U200(lon|:, time|:), wgt, 0)

;************************************************
; remove means of band pass series: *not* necessary 
;************************************************
  rlut   = dim_rmvmean(rlut)                   ; (lon,time)
  u850  = dim_rmvmean(u850)
  u200  = dim_rmvmean(u200)

;************************************************
; Compute the temporal variance
;************************************************
  var_rlut = dim_variance_Wrap(rlut)          ; (lon)
  var_u850 = dim_variance_Wrap(u850)
  var_u200 = dim_variance_Wrap(u200)

;************************************************
; Compute the zonal mean of the temporal variance
;************************************************
  zavg_var_rlut = dim_avg_Wrap( var_rlut)     
  zavg_var_u850 = dim_avg_Wrap( var_u850)
  zavg_var_u200 = dim_avg_Wrap( var_u200)

;************************************************
; Normalize by sqrt(avg_var*)
;************************************************
  rlut  = rlut/sqrt(zavg_var_rlut)          ; (lon,time)
  u850  = u850/sqrt(zavg_var_u850)
  u200  = u200/sqrt(zavg_var_u200)

;************************************************
; Combine the normalized data into one variable
;************************************************
  cdata     = new ( (/3*mlon,ntim/), typeof(rlut), getFillValue(rlut))
  do ml=0,mlon-1
     cdata(ml       ,:) = (/ rlut(ml,:) /)
     cdata(ml+  mlon,:) = (/ u850(ml,:) /)
     cdata(ml+2*mlon,:) = (/ u200(ml,:) /)
  end do

  cdata!0 = "lon"
  cdata!1 = "time"

;************************************************
; Compute Combined EOF
;************************************************
  eof_cdata    = eofunc_Wrap(cdata   , neof, False)      ; (neof,3*mlon)
  eof_ts_cdata = eofunc_ts_Wrap(cdata,eof_cdata,False)   ; (neof,time)

;  print("==============")
;  printVarSummary(eof_cdata)
;  printMinMax(eof_cdata, True)

;  print("==============")
;  printVarSummary(eof_ts_cdata)
;  printMinMax(eof_ts_cdata, True)

;************************************************
; For clarity, explicitly extract each variable 
;************************************************

  nvar = 3  ; "rlut", "u850", "u200"

  ceof = new( (/nvar,neof,mlon/), typeof(cdata), getFillValue(cdata))

  do n=0,neof-1
     ceof(0,n,:) = eof_cdata(n,0:mlon-1)      ; olr
     ceof(1,n,:) = eof_cdata(n,mlon:2*mlon-1) ; u850
     ceof(2,n,:) = eof_cdata(n,2*mlon:)       ; u200
  end do

  ceof_ts = new( (/nvar,neof,ntim/), typeof(cdata), getFillValue(cdata))


  ceof!0 = "nvar"
  ceof!1 = "neof"

  ceof_ts(0,:,:) = eofunc_ts_Wrap(rlut,ceof(0,:,:),False)   ; (neof,time)
  ceof_ts(1,:,:) = eofunc_ts_Wrap(u850,ceof(1,:,:),False)   ; (neof,time)
  ceof_ts(2,:,:) = eofunc_ts_Wrap(u200,ceof(2,:,:),False)   ; (neof,time)

;************************************************
; Compute cross correlation of each variable's EOF time series at zero-lag
;************************************************
  r_rlut_u850  = escorc(ceof_ts(0,:,:) , ceof_ts(1,:,:))
  r_rlut_u200  = escorc(ceof_ts(0,:,:) , ceof_ts(2,:,:) )
  r_u850_u200 = escorc(ceof_ts(1,:,:) , ceof_ts(2,:,:) )

;  print("==============")
  do n=0,neof-1
     print("neof="+n \
          +"  r_rlut_u850=" +sprintf("%4.3f",r_rlut_u850(n))  \
          +"  r_rlut_u200=" +sprintf("%4.3f",r_rlut_u200(n))  \
          +"  r_u850_u200="+sprintf("%4.3f",r_u850_u200(n)) )
  end do
;  print("==============")

;************************************************
; Compute cross correlation of the multivariate EOF; EOF 1 vs EOF 2
;************************************************

  mxlag     = 25
  rlag_01   = esccr(eof_ts_cdata(0,:),eof_ts_cdata(1,:), mxlag)   ; (N,mxlag+1)
  rlag_10   = esccr(eof_ts_cdata(1,:),eof_ts_cdata(0,:), mxlag)   ; (N,mxlag+1)
  ccr_12    = new ( (/2*mxlag+1/), float)    

  ccr_12(mxlag:)    = rlag_10(0:mxlag)   
  ccr_12(0:mxlag)   = rlag_01(::-1)       ; reverse order

;************************************************
; Normalize the multivariate EOF 1&2 component time series
; Compute (PC1^2+PC2^2): values > 1 indicate "strong" periods
;************************************************
  eof_ts_cdata(0,:) = eof_ts_cdata(0,:)/stddev(eof_ts_cdata(0,:))
  eof_ts_cdata(1,:) = eof_ts_cdata(1,:)/stddev(eof_ts_cdata(1,:))

  mjo_ts_index      = eof_ts_cdata(0,:)^2 + eof_ts_cdata(1,:)^2 
  mjo_ts_index_smt  = runave(mjo_ts_index, 91, 0) ; 91-day running mean

  nGood   = num(.not.ismissing(mjo_ts_index))     ; # non-missing
  nStrong = num(mjo_ts_index .ge. 1.0)
  print("nGood="+nGood+"   nStrong="+nStrong+"   nOther="+(nGood-nStrong))

;************************************************
; Write PC results to netCDF for use in another example.
;************************************************
  mjo_ts_index!0    = "time"
  mjo_ts_index&time = time 
  mjo_ts_index@long_name = "MJO PC INDEX" 
  mjo_ts_index@info      = "(PC1^2 + PC2^2)" 

  PC1  = eof_ts_cdata(0,:)
  PC1!0= "time"
  PC1&time      =  time
  PC1@long_name = "PC1"
  PC1@info      = "PC1/stddev(PC1)"

  PC2  = eof_ts_cdata(1,:)
  PC2!0= "time"
  PC2&time      =  time
  PC2@long_name = "PC2"
  PC2@info      = "PC2/stddev(PC2)"

;  diro = "./"
  filo = file_dir+"MJO_PC_INDEX.nc"
  system("rm -f "+filo)   ; remove any pre-existing file
  ncdf = addfile(filo,"c")     ; open output netCDF file
                                    ; make time an UNLIMITED dimension 
  filedimdef(ncdf,"time",-1,True)   ; recommended  for most applications
                                    ; output variables directly
  ncdf->MJO_INDEX = mjo_ts_index    
  ncdf->PC1       = PC1     
  ncdf->PC2       = PC2     
  print(routine_name+" wrote "+filo)

end

