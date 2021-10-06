; This file is part of the MJO_teleconnection module of the MDTF code package (see LICENSE.txt)

;-------------------------------------------------------------------------------------
;Composites of geopotential height for CMIP5 models
;
;Time range: January 1950 - December 2005 
;
;February 14, 2014, updated for CMIP5 models July 13, 2015
;Written by Stephanie Henderson
;-------------------------------------------------------------------------------------

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl" 

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin

;lag desired for geopotential height plots

  lag = ispan(0,19,1)
 Mean = False  ;True only for variance calculation for difference of means test
print("--------------------------------------------------------------------------")  
Sig = True   ;significance testing?
print("Sig: " + Sig)
 
Model = getenv("CASENAME")

print("Model: " + Model)

old_model = True
;-------------------------------------------------------------------------------------
   ymdStrt = tointeger(getenv("strtdy"))                         ; start yyyymmdd
   ymdLast = tointeger(getenv("lastdy")) 
   yrStrt  = ymdStrt/10000
   yrLast  = ymdLast/10000
;-------------------------------------------------------------------------------------
;--directory for output files--
dirobs   = getenv("OBS_DATA")+"/"                      ;Obs input directory
diro     = getenv("WK_DIR")+"/model/netCDF/"        ;Output data directory
filz250  = getenv("z250_file")                                              ; input file
tfile    = "t_table_data.txt"
print("Output data path :" + diro)
print("Input data file for Z250 :" + filz250)
print("t-statistics data table is read from:"+diro+tfile)


z250var = getenv("z250_var")


print("--------------------------------------------------------------------------")
n = new((/dimsizes(lag),8/),float)
tdata = asciiread(dirobs+tfile,(/101,2/),"float")
t_crit = tdata(1:,0)
dof    = tdata(:,1)
print("data table for t stat is read in ")
;------------------read in geopotential height data --------------------


    a = addfile(filz250 , "r")
  ;  print(a)
;--- read in time ---
   temp_time = a->time
   calend = temp_time@calendar
   ymd     = cd_calendar(temp_time, -2)            ; yyyymmdd
;   print(calend)

    iStrt   = ind(ymd.eq.ymdStrt)              ; index start
    iLast   = ind(ymd.eq.ymdLast)              ; index last 
   
    zgt = a->$z250var$(iStrt:iLast,:,:)     ;time,lat,lon
    zgt@_FillValue = -999

    lon = tofloat(a->lon)
    lat = tofloat(a->lat)

 ; print(lon)
 ; print(lat)
 
   

   if(temp_time@calendar .ne. "360_day") ; Check if model have 360 day calender 
   utc_date = cd_calendar((a->time(iStrt:iLast)), 0)
   ;print(utc_date)

   yeart   = tointeger(utc_date(:,0))
   montht  = tointeger(utc_date(:,1))
   dayst   = tointeger(utc_date(:,2))

   ;clean up
   delete(utc_date)
   end if 

;  print(yeart(iStrt))
;  print(yeart(iLast))
  print("Total days: " + dimsizes(yeart))  ;Total days indata set 

  year = yeart
  month = montht
  days = dayst


  delete(yeart)
  delete(montht)
  delete(dayst)

  year@calendar = calend
  doy = day_of_year(year,month,days)
  time = tointeger(year * 1000.) + doy

  print("First doy: " + min(time) + "  last doy: " + max(time))

  H_all = zgt(:,:,:)
  H_all@_FillValue = -999

  delete(zgt)

;--remove daily seasonal cycle and long term mean--
print("remove seasonal cycle")

H_all!0 = "time"
H_all!1 = "lat"
H_all!2 = "lon"

H_all@_FillValue=-999

if(Mean .eq. False)
;calculate raw climatology then smooth it
rawclim = clmDayTLL(H_all,time)
smoothclim = smthClmDayTLL(rawclim,2)

H_anom = calcDayAnomTLL(H_all,time,smoothclim)
H_anom@_FillValue=-999

;clean up
delete(H_all)
delete(smoothclim)
delete(rawclim)

H_all = H_anom
delete(H_anom)
end if

;-- isolate DJF and remove leap days (if any) --
  
DJF = ind((month .le. 2 .or. month .eq. 12) .and. (.not.(month .eq. 2 .and. days .eq. 29) ))
 
block_doyDJF = time(DJF)
print("Total days: " + dimsizes(DJF))  ;20440
; print(year(DJF) + "  " + month(DJF) + "  " + days(DJF))
 print("First doy: " + min(block_doyDJF) + "  last doy: " + max(block_doyDJF))

 
H_DJF = H_all(DJF,:,:)

  delete(time)
  delete(year)
  delete(month)
  delete(days)
  delete(doy)

H_DJF@_FillValue=-999
delete(H_all)

time = ispan(1,dimsizes(DJF),1)
;delete(DJF)

H_DJF!0 = "time" 
H_DJF!1 = "lat"
H_DJF!2 = "lon"

;-----------------------Add MJO data-------------------------
print("--------------------------------------------------------------------------")
print("Reading in RMM indices data")

; Data is ordered in terms on phase, not date
; MJO index (RMM1 and RMM2)
;1979 - present


MJO  = readAsciiTable(diro+Model +"_RMMs.txt",5,"float",1)
MJO@_FillValue=-999

;print(dimsizes(MJO))


;time    RMM1    RMM2    phase    amplitude
   date=tointeger(MJO(:,0))        ;date (yyyydoy) 
   RMMot=MJO(:,1)      		   ;RMM1
   RMMtt=MJO(:,2)       	   ;RMM2
   phaset=tointeger(MJO(:,3))      ;phase

;--isolate DJF--
yyyymmdd = yyyyddd_to_yyyymmdd(date)
year = tointeger(floor(date/1000.))  ;
year_all = tointeger(year * 10000.)  ;yyyy000
month = tointeger(floor((yyyymmdd - year_all)/100.))
day = tointeger(yyyymmdd - year_all - (month * 100.))


;print(yyyymmdd(DJF))

;print("DJF dimsizes = " + dimsizes(DJF))  ;5040

 ;clean up
 delete(year)
 delete(year_all) 
 delete(month)
 delete(day)
 delete(yyyymmdd) 

;-- isolate DJF in unlagged terms --
  MJO_yrdoyn = date(DJF)
;print(max(MJO_yrdoyn) + "   " + min(MJO_yrdoyn))

do lg = 0,dimsizes(lag)-1
;;print("Lag: " + lag(lg))

;lag all phases (forward lag)
ab_lag = abs(lag(lg))

Ldoy = dimsizes(date) - ab_lag

RMMo = new((/dimsizes(date)/),float)
RMMt = new((/dimsizes(date)/),float)
phase = new((/dimsizes(date)/),float)

if(lag(lg) .gt. 0)
  RMMo(lag(lg):) = RMMot(:Ldoy-1)	;ex: actual doy = 2010200 has lag 6 phase and RMMS of 2010194.
  RMMo(:lag(lg)-1) = RMMot(Ldoy:)
  RMMt(lag(lg):) = RMMtt(:Ldoy-1)		
  RMMt(:lag(lg)-1) = RMMtt(Ldoy:)
  phase(lag(lg):) = phaset(:Ldoy-1)		
  phase(:lag(lg)-1) = phaset(Ldoy:)  
end if
if(lag(lg) .lt. 0)
  RMMo(Ldoy:) = RMMot(:ab_lag-1)	;ex: actual doy = 2010200 has lag 6 phase and RMMS of 2010194.
  RMMo(:Ldoy-1) = RMMot(ab_lag:)
  RMMt(Ldoy:) = RMMtt(:ab_lag-1)		
  RMMt(:Ldoy-1) = RMMtt(ab_lag:)
  phase(Ldoy:) = phaset(:ab_lag-1)		
  phase(:Ldoy-1) = phaset(ab_lag:)  
end if
if(lag(lg) .eq. 0)
  RMMo = RMMot
  RMMt= RMMtt	
  phase = phaset	
end if

delete(Ldoy)
delete(ab_lag)

amplitude=(RMMo^2. + RMMt^2.)^0.5

;--isolate DJF in all variables--
 phase_DJFn = phase(DJF)
 amp = amplitude(DJF)

delete(phase)
delete(amplitude)
delete(RMMo)
delete(RMMt)

;separate phases
MJOst=ind(amp .ge. 1.0)   ;stronger:   

   MJO_yrdoy=MJO_yrdoyn(MJOst)   ;strong days
   phase_DJF=phase_DJFn(MJOst)   		 ;lagged phase (phase of current + lag days)

;print("strong days: " + dimsizes(MJOst))
delete(phase_DJFn)
delete(amp)
delete(MJOst)

;--Separate per phase--
phase1 = ind(phase_DJF .eq. 1)
phase2 = ind(phase_DJF .eq. 2)
phase3 = ind(phase_DJF .eq. 3)
phase4 = ind(phase_DJF .eq. 4)
phase5 = ind(phase_DJF .eq. 5)
phase6 = ind(phase_DJF .eq. 6)
phase7 = ind(phase_DJF .eq. 7)
phase8 = ind(phase_DJF .eq. 8)

;print("Phase 1 days = " + dimsizes(phase1))
;print("Phase 2 days = " + dimsizes(phase2))
;print("Phase 3 days = " + dimsizes(phase3))
;print("Phase 4 days = " + dimsizes(phase4))
;print("Phase 5 days = " + dimsizes(phase5))
;print("Phase 6 days = " + dimsizes(phase6))
;print("Phase 7 days = " + dimsizes(phase7))
;print("Phase 8 days = " + dimsizes(phase8))

yydoy_phase1 = MJO_yrdoy(phase1)
yydoy_phase2 = MJO_yrdoy(phase2)
yydoy_phase3 = MJO_yrdoy(phase3)
yydoy_phase4 = MJO_yrdoy(phase4)
yydoy_phase5 = MJO_yrdoy(phase5)
yydoy_phase6 = MJO_yrdoy(phase6)
yydoy_phase7 = MJO_yrdoy(phase7)
yydoy_phase8 = MJO_yrdoy(phase8)

delete(phase1)
delete(phase2)
delete(phase3)
delete(phase4)
delete(phase5)
delete(phase6)
delete(phase7)
delete(phase8)

delete(phase_DJF)
delete(MJO_yrdoy)


;-- composite geopotential height data by MJO events --

block_phase1 = new((/dimsizes(block_doyDJF)/),float)  
block_phase1 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase1(i)=num(yydoy_phase1 .eq. block_doyDJF(i))       ;relative to geopotential height
 end do
 
 kphase1 = floattointeger(sum(block_phase1))     ;1214
; print("MJO days phase 1 = " + kphase1)

block_phase2 = new((/dimsizes(block_doyDJF)/),float)  
block_phase2 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase2(i)=num(yydoy_phase2 .eq. block_doyDJF(i))   
 end do

 kphase2 = floattointeger(sum(block_phase2))     ;1214
; print("MJO days phase 2 = " + kphase2)


block_phase3 = new((/dimsizes(block_doyDJF)/),float)  
block_phase3 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase3(i)=num(yydoy_phase3 .eq. block_doyDJF(i))   
 end do

 kphase3 = floattointeger(sum(block_phase3))     ;1214
; print("MJO days phase 3 = " + kphase3)


block_phase4 = new((/dimsizes(block_doyDJF)/),float)  
block_phase4 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase4(i)=num(yydoy_phase4 .eq. block_doyDJF(i))    
 end do

 kphase4 = floattointeger(sum(block_phase4))     ;1214
; print("MJO days phase 4 = " + kphase4)


block_phase5 = new((/dimsizes(block_doyDJF)/),float)  
block_phase5 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase5(i)=num(yydoy_phase5 .eq. block_doyDJF(i))    
 end do

 kphase5 = floattointeger(sum(block_phase5))     ;1214
; print("MJO days phase 5 = " + kphase5)


block_phase6 = new((/dimsizes(block_doyDJF)/),float)  
block_phase6 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase6(i)=num(yydoy_phase6 .eq. block_doyDJF(i))    
 end do

 kphase6 = floattointeger(sum(block_phase6))     ;1214
; print("MJO days phase 6 = " + kphase6)


block_phase7 = new((/dimsizes(block_doyDJF)/),float)  
block_phase7 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase7(i)=num(yydoy_phase7 .eq. block_doyDJF(i))    
 end do

 kphase7 = floattointeger(sum(block_phase7))     ;1214
; print("MJO days phase 7 = " + kphase7)


block_phase8 = new((/dimsizes(block_doyDJF)/),float)  
block_phase8 = 0                     ;initialize to 0

 do i = 0,dimsizes(block_doyDJF)-1     
   block_phase8(i)=num(yydoy_phase8 .eq. block_doyDJF(i))    
 end do

 kphase8 = floattointeger(sum(block_phase8))     ;1214
; print("MJO days phase 8 = " + kphase8)
; print("max " + max(block_phase1))
; print(min(block_phase1))

delete(yydoy_phase1)
delete(yydoy_phase2)
delete(yydoy_phase3)
delete(yydoy_phase4)
delete(yydoy_phase5)
delete(yydoy_phase6)
delete(yydoy_phase7)
delete(yydoy_phase8)

;find indices of blocked days per MJO phase (relative to blocking index)
phase1_blockedin = ind(block_phase1 .gt. 0)
phase2_blockedin = ind(block_phase2 .gt. 0)
phase3_blockedin = ind(block_phase3 .gt. 0)
phase4_blockedin = ind(block_phase4 .gt. 0)
phase5_blockedin = ind(block_phase5 .gt. 0)
phase6_blockedin = ind(block_phase6 .gt. 0)
phase7_blockedin = ind(block_phase7 .gt. 0)
phase8_blockedin = ind(block_phase8 .gt. 0)

phase1_hgt = H_DJF(phase1_blockedin,:,:)     ;time,lon
phase2_hgt = H_DJF(phase2_blockedin,:,:)     
phase3_hgt = H_DJF(phase3_blockedin,:,:)     
phase4_hgt = H_DJF(phase4_blockedin,:,:)    
phase5_hgt = H_DJF(phase5_blockedin,:,:)   
phase6_hgt = H_DJF(phase6_blockedin,:,:)    
phase7_hgt = H_DJF(phase7_blockedin,:,:)    
phase8_hgt = H_DJF(phase8_blockedin,:,:)   

delete(block_phase1)
delete(block_phase2)
delete(block_phase3)
delete(block_phase4)
delete(block_phase5)
delete(block_phase6)
delete(block_phase7)
delete(block_phase8)

delete(phase1_blockedin)
delete(phase2_blockedin)
delete(phase3_blockedin)
delete(phase4_blockedin)
delete(phase5_blockedin)
delete(phase6_blockedin)
delete(phase7_blockedin)
delete(phase8_blockedin)  



;--generate composites--
dim_lon = dimsizes(lon)
dim_lat = dimsizes(lat)

nlonn=dim_lon
nlatn=dim_lat

lon = tofloat(a->lon)
lat = tofloat(a->lat)

if(lg .eq. 0)

  geop_composites_PSIt = new((/dimsizes(lag),8,dim_lat,dim_lon/),typeof(phase1_hgt))
  

  if(Sig .eq. True)
    tstat_hgtt = new((/dimsizes(lag),8,dim_lat,dim_lon/),typeof(phase1_hgt))
  end if

end if

geop_composites_PSIt(lg,0,:,:) = dim_avg_n(phase1_hgt,0)
geop_composites_PSIt(lg,1,:,:) = dim_avg_n(phase2_hgt,0)
geop_composites_PSIt(lg,2,:,:) = dim_avg_n(phase3_hgt,0)
geop_composites_PSIt(lg,3,:,:) = dim_avg_n(phase4_hgt,0)
geop_composites_PSIt(lg,4,:,:) = dim_avg_n(phase5_hgt,0)
geop_composites_PSIt(lg,5,:,:) = dim_avg_n(phase6_hgt,0)
geop_composites_PSIt(lg,6,:,:) = dim_avg_n(phase7_hgt,0)
geop_composites_PSIt(lg,7,:,:) = dim_avg_n(phase8_hgt,0)

geop_composites_PSIt@_FillValue = -999

;--test null hypothesis that anomalies are not significantly different from zero--
print("significance testing")

  MJO_daysn = 5.
  
print("MJO average # of days: " + MJO_daysn)
 n(lg,0) = kphase1/MJO_daysn
 n(lg,1) = kphase2/MJO_daysn
 n(lg,2) = kphase3/MJO_daysn
 n(lg,3) = kphase4/MJO_daysn
 n(lg,4) = kphase5/MJO_daysn
 n(lg,5) = kphase6/MJO_daysn
 n(lg,6) = kphase7/MJO_daysn
 n(lg,7) = kphase8/MJO_daysn

print(n(lg,:))

;clean up
delete(kphase1)
delete(kphase2)
delete(kphase3)
delete(kphase4)
delete(kphase5)
delete(kphase6)
delete(kphase7)
delete(kphase8)


if(Sig .eq. True)

siglvl = new((/8/),float)    ;(from t-table; t-value must exceed this to be significant at 95% level, two-tail test)

  do  i= 0,7
   if (round(n(lg,i),0).le. 100)
     jj= tointeger(round(n(lg,i),0))
     siglvl(i) = t_crit(jj)
   else
    siglvl(i) = 1.96
   end if
  end do




stddv = new((/8,dimsizes(lat),dimsizes(lon)/),typeof(phase1_hgt))
stddv(0,:,:) = dim_stddev_n(phase1_hgt,0)
stddv(1,:,:) = dim_stddev_n(phase2_hgt,0)
stddv(2,:,:) = dim_stddev_n(phase3_hgt,0)
stddv(3,:,:) = dim_stddev_n(phase4_hgt,0)
stddv(4,:,:) = dim_stddev_n(phase5_hgt,0)
stddv(5,:,:) = dim_stddev_n(phase6_hgt,0)
stddv(6,:,:) = dim_stddev_n(phase7_hgt,0)
stddv(7,:,:) = dim_stddev_n(phase8_hgt,0)

stddv@_FillValue = -999

tstat = new((/dimsizes(stddv)/),typeof(phase1_hgt))
do i = 0,7
  tstat(i,:,:) = abs(sqrt(n(lg,i)-1.)) * abs(geop_composites_PSIt(lg,i,:,:)/stddv(i,:,:))
end do

tstat@_FillValue = -999
delete(stddv)

do i = 0,7
 do j=0, dimsizes(lat)-1
  do k=0, dimsizes(lon)-1
  if(.not.ismissing(tstat(i,j,k)))
   if (tstat(i,j,k) .gt. siglvl(i)) 
      tstat(i,j,k) = 1
   else 
      tstat(i,j,k) = 0 
   end if
   ;if(lat(j) .le. 15 .and. lat(j) .ge. -15)
   ;   tstat(i,j,k) = 0
   ;end if
 else
      tstat(i,j,k) = 0
 end if
   end do
 end do
end do

tstat_hgtt(lg,:,:,:) = tstat
tstat_hgtt@_FillValue = -999

delete(tstat)
delete(siglvl)
end if

delete(phase1_hgt)
delete(phase2_hgt)
delete(phase3_hgt)
delete(phase4_hgt)
delete(phase5_hgt)
delete(phase6_hgt)
delete(phase7_hgt)
delete(phase8_hgt)

end do

print("")
geop_composites_hgt = geop_composites_PSIt
geop_composites_hgt@_FillValue = -999

phase = ispan(1,8,1)

geop_composites_hgt!0   = "lag"
geop_composites_hgt!1   = "phase"
geop_composites_hgt!2   = "lat"    
geop_composites_hgt!3   = "lon"
geop_composites_hgt&lag = lag
geop_composites_hgt&phase = phase
geop_composites_hgt&lat = lat      
geop_composites_hgt&lon = lon


;write out a 3D netcdf file
print("Writing NetCDF files")

;  system("rm -f geop_compositesDly_hgt_"+Model_long+".nc")
;  ncdf = addfile("geop_compositesDly_hgt_"+Model_long+".nc" , "c")

;make time and unlimited dimension
; filedimdef(ncdf, "lag", -1, True)

;output variables directly
; ncdf->geop_composites_hgt = geop_composites_hgt

;clean up
;delete(ncdf)
delete(geop_composites_hgt)


;- generate pentads
; print("generate pentads")

  ntJump  = 5                     ; average over 5 days		
  NTIM=dimsizes(lag)              ; 25 days, 5 pentads

  geop_composites = geop_composites_PSIt(::ntJump,:,:,:)     ; ;lag,phase,lat,lon [5,8,121,240]
;  print(dimsizes(geop_composites))
  
    ntStrt  = 0
    ntLast  = ntJump-1
    do nt=0,NTIM-1,ntJump           
       geop_composites(nt/ntJump,:,:,:) = (/dim_avg_n(geop_composites_PSIt(ntStrt:ntLast,:,:,:), 0) /)   ; (/.../) ignore meta
       ntStrt  = ntStrt+ntJump
       ntLast  = ntLast+ntJump
    end do
 geop_composites@_FillValue = -999

if(Sig .eq. False)
  delete(lag)

dt = NTIM/ntJump
lag = ispan(-1,dt-2,1)  ;5 lags

print(dimsizes(lag))
end if

  ;clean up
  delete(geop_composites_PSIt)
  delete(ntStrt)
  delete(ntLast)
  delete(NTIM)
  delete(ntJump)

; print("generate tstat pentads")
if(Sig .eq. True)
  ntJump  = 5                     ; average over 5 days		
  NTIM=dimsizes(lag)              ; 25 days, 5 pentads

  tstat_hgt = tstat_hgtt(::ntJump,:,:,:)     ; ;lag,phase,lat,lon
;  print(dimsizes(tstat_hgt))
  
    ntStrt  = 0
    ntLast  = ntJump-1
    do nt=0,NTIM-1,ntJump           
       tstat_hgt(nt/ntJump,:,:,:) = (/dim_avg_n(tstat_hgtt(ntStrt:ntLast,:,:,:), 0) /)   ; (/.../) ignore meta
       ntStrt  = ntStrt+ntJump
       ntLast  = ntLast+ntJump
    end do
 tstat_hgt@_FillValue = -999

  delete(lag)

dt = NTIM/ntJump
lag = ispan(-1,dt-2,1)  ;5 lags

;print(dimsizes(lag))
  ;clean up
  delete(tstat_hgtt)
  delete(ntStrt)
  delete(ntLast)
  delete(NTIM)
  delete(ntJump)
  delete(dt)
end if

geop_composites!0   = "lag"
geop_composites!1   = "phase"
geop_composites!2   = "lat"    
geop_composites!3   = "lon"
geop_composites&lag = lag
geop_composites&phase = phase
geop_composites&lat = lat      
geop_composites&lon = lon


;write out a 3D netcdf file
print("Writing NetCDF file for composite of geopotential height for each phase")

  system("rm -f " + diro + "geop_compositesP_hgt250_"+Model+".nc")
  ncdf = addfile(diro + "geop_compositesP_hgt250_"+Model+".nc" , "c")

;make time and unlimited dimension
 filedimdef(ncdf, "lag", -1, True)

;output variables directly
 ncdf->geop_composites = geop_composites

;clean up
delete(ncdf)
delete(geop_composites)

 

if(Sig .eq. True)
tstat_hgt!0   = "lag"
tstat_hgt!1   = "phase"
tstat_hgt!2   = "lat"    
tstat_hgt!3   = "lon"
tstat_hgt&lag = lag
tstat_hgt&phase = phase
tstat_hgt&lat = lat      
tstat_hgt&lon = lon


;write out a 3D netcdf file
print("Writing NetCDF file for t-statistic values")

  system("rm -f " + diro + "tstatP_hgt250_"+Model+".nc")
  ncdf = addfile(diro + "tstatP_hgt250_"+Model+".nc" , "c")

;make time and unlimited dimension
 filedimdef(ncdf, "lag", -1, True)

;output variables directly
 ncdf->tstat_hgt = tstat_hgt
print("Composite of geopotential height at 250-hPa are genreted now ")
print("Data is saved as netcdf format at:"+diro)
print("In following files:")
print("geop_compositesP_hgt250_"+Model+".nc")
print("tstatP_hgt250_"+Model+".nc")
print("--------------------------------------------------------------------------")
;clean up
delete(ncdf)
delete(tstat_hgt)
end if


end
