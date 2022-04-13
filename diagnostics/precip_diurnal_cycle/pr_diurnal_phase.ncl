; This file is part of the precip_diurnal_cycle module of the MDTF code package (see LICENSE.txt)

; This routine is meant to read in CAM (an time resolution from 1hr to 3 or 6? hrs) data
; calculate the magnitude of the diurnal and semi0diyrnal cycle and phase
; and plot Evans diagram of the results. Plus plots diurnal variancee explained and mean precip.  

; RBN - Dec 2010 - Always process one month at a time and can process both obs. and model.
; Should also run on CGD and DASG machines

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/calc_utils.ncl"
load "$POD_HOME/evans_plot.ncl"

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

begin
; Set variables for two runs.


  date_off = getenv("date_int_offset")
  date_offset = stringtointeger(date_off) ; 1 for native CESM, 0 for GFDL & CMIP

  setfileoption("nc", "SuppressClose", False)

  var_name = getenv("pr_var")
  

;  seasons =(/"01","02","03","04","05","06","07","08","09","10","11","12","JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ","DJF","ANN","WIN","SUM"/)

  seasons = (/"DJF","JJA","MAM","SON","ANN"/)  
  phase_only = False ; Set true iff not amplitude color saturation is required.
  
;  ps_dir = "/datalocal/haystack/cchen/dcycle/"
  ps_dir = getenv("WK_DIR")+"/model/PS/"
  firstyr = stringtoint(getenv("FIRSTYR"))
  lastyr = stringtoint(getenv("LASTYR"))
  print(firstyr)
  print(lastyr)
;;;;; For model only   ;;;;;
  model_fstruc = 0 ; Model file structure; 0 = single files; 1 = many files.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Multiple model/obs. specification ;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

  run_names = getenv("CASENAME")
  run_titles = getenv("CASENAME")
  obs = (/False/)   ; True-obs, False-model. (TRMM-3B42-3HRLY assumed for obs. in separate monthly files.)
;  mrun_years = (/2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010/)
   mrun_years = ispan(firstyr,lastyr,1)
   print(mrun_years)
;  orun_years = (/2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010/)


;  dir_root = "/datalocal/haystack/cchen/dcycle/3hrly/" ; TRIMM data
  rsub_dir = "/" ;Directory name between run_name dir and data, set = "" iff no directory in between.
;  hchan = getenv("fincl") ; ;e.g., h1,h2,h3

; Default name of region
  region_plot = "50N50S"

; Domain range - will alter plot positions iff not (-50-50; 0-360.) 
  
  lat_s = -50.
  lat_n = 50.
  lon_w = 0. ; Specify as -180->180
  lon_e = 360.

;;;

  usa_plot = False

;  if (usa_plot) then
    region_plot =  "USA"
    lat_s_2 = 25.
    lat_n_2 = 50.
    lon_w_2 = -130+360 ; Specify as -180->180
    lon_e_2 = -70.+360
;  end if

  nharm = 1 ; 3 diurnal harmonics

; Loop runs
  nruns = dimsizes(run_names)

  ps_name0 = run_names(0)
  do irun=1,nruns-1
    ps_name0 = ps_name0+"."+run_names(irun)
  end do

;  ps_name = ps_name0+"_"+var_name+"."+region_plot+".dc."

;  ps_name1 = var_name+".50N50S.dc."
;  ps_name2 = var_name+".USA.dc."
ps_name = ps_name0+"_pr."+region_plot+".dc."

  ps_name1 = "pr.50N50S.dc."
  ps_name2 = "pr.USA.dc."
    
    nseas = dimsizes(seasons)
    
    do iseas=0,nseas-1
      
      season = seasons(iseas)
      
      
      if (season.eq."ANN") then
        months = (/"01","02","03","04","05","06","07","08","09","10","11","12"/)
        mwt = (/31,28,31,30,31,30,31,31,30,31,30,31/)
        stitle = "Annual"
      end if
      if (season.eq."SUM") then ; MJO Summer = May-October
        months = (/"05","06","07","08","09","10"/)
        mwt = (/31,30,31,31,30,31/)
        stitle = "NH Summer (May-Oct)"
      end if
      if (season.eq."WIN") then ; MJO Winter = November-April
        months = (/"01","02","03","04","11","12"/)
        mwt = (/31,28,31,30,30,31/)
        stitle = "NH Winter (Nov-Mar)"
      end if
      
      if (season.eq."JFM") then ; MJO Winter = November-April
        months = (/"01","02","03"/)
        mwt = (/31,28,31/)
        stitle = "JFM"
      end if
      if (season.eq."FMA") then ; MJO Winter = November-April
        months = (/"02","03","04"/)
        mwt = (/28,31,30/)
        stitle = "FMA"
      end if
      if (season.eq."MAM") then ; MJO Winter = November-April
        months = (/"03","04","05"/)
        mwt = (/31,30,31/)
        stitle = "MAM"
      end if
      if (season.eq."AMJ") then ; MJO Winter = November-April
        months = (/"04","05","06"/)
        mwt = (/30,31,30/)
        stitle = "AMJ"
      end if
      if (season.eq."MJJ") then ; MJO Winter = November-April
        months = (/"05","06","07"/)
        mwt = (/31,30,31/)
        stitle = "MJJ"
      end if
      if (season.eq."JJA") then ; MJO Winter = November-April
        months = (/"06","07","08"/)
        mwt = (/30,31,31/)
        stitle = "JJA"
      end if
      if (season.eq."JAS") then ; MJO Winter = November-April
        months = (/"07","08","09"/)
        mwt = (/31,31,30/)
        stitle = "JAS"
      end if
      if (season.eq."ASO") then ; MJO Winter = November-April
        months = (/"08","09","10"/)
        mwt = (/31,30,31/)
        stitle = "ASO"
      end if
      if (season.eq."SON") then ; MJO Winter = November-April
        months = (/"09","10","11"/)
        mwt = (/30,31,30/)
        stitle = "SON"
      end if
      if (season.eq."OND") then ; MJO Winter = November-April
        months = (/"10","11","12"/)
        mwt = (/31,30,31/)
        stitle = "OND"
      end if
      if (season.eq."NDJ") then ; MJO Winter = November-April
        months = (/"11","12","01"/)
        mwt = (/30,31,31/)
        stitle = "NDJ"
      end if
      if (season.eq."DJF") then ; MJO Winter = November-April
        months = (/"12","01","02"/)
        mwt = (/31,31,28/)
        stitle = "DJF"
      end if
      
      
      mon_name = (/"JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"/)
      
      if (.not.isdefined("months")) then
        months = season
        mwto = (/31.,28,31,30,31,30,31,31,30,31,30,31/)
        mwt = mwto(stringtointeger(season)-1)
        season = mon_name(stringtointeger(season)-1)
        stitle = season
      end if
      
      print("*** Season =  "+stitle+" ***")
      
; Postscript
      
      tphase = ""
      if (phase_only) then
        tphase = "_phase-only"
      end if
      
      
;      if (max(mrun_years).eq.min(mrun_years)) then
       
;        wks = gsn_open_wks("ps",ps_dir+ps_name+sprinti("%0.4i",min(mrun_years))+"."+season+tphase)
;      else
;        wks = gsn_open_wks("ps",ps_dir+ps_name+sprinti("%0.4i",min(mrun_years))+"-"+sprinti("%0.4i",max(mrun_years))+"."+season+tphase)
;      end if
;      print(ps_dir+ps_name+sprinti("%0.4i",min(mrun_years))+"."+season+tphase)
            
       wks1 = gsn_open_wks("ps",ps_dir+"/"+ps_name1+season)
       wks2 = gsn_open_wks("ps",ps_dir+"/"+ps_name2+season)

      nmonths = dimsizes(months)
      nyears = dimsizes(mrun_years)
;      print(nyears)
;      plot = new(3,graphic)
      plot1 = new(3,graphic)
      plot2 = new(3,graphic)

;;;;
; Graphics
      
; Phase and mag.
      resdc = True
      resdc@gsnFrame = False
      resdc@gsnDraw  = False
      
      resdc@mpOutlineDrawOrder     = "PostDraw"  ; force map tp be drawn 1st 
;  resdc@mpGridLineDashPattern  = 2           ; lat/lon lines as dashed
;  resdc@mpPerimOn              = True
      resdc@mpPerimDrawOrder       = "PostDraw"
      resdc@mpOutlineOn            = True
;  resdc@mpGeophysicalLineThicknessF = 0.5
      
      resdc@epCyclic = True ; is the hue variable cyclic? [True]
;  resdc@epSatLabel = (/0,2,5,10/) ; to label the saturations [sat_data@units]
;  resdc@epExplicitSatLevels {float[resdc]} ; user set saturation levels
 ; resdc@epMaxSatLevel = 9 ; maxx saturation level
 ; resdc@epMinSatLevel = 1 ; minn saturation level
; Set values for each harmonic

; Color maps for saturation.
; As a guide there will be 8 saturation levels per hue.

      maxsatlevel = (/5, 5.,  3.,   2.25 /)
      minsatlevel = (/0.5, 0.5,  0.33, 0.25 /)
      maxhuelevel = (/23, 11.5, 7.66, 5.75 /)
      huespacing =  (/1., 0.5,  0.33, 0.25 /)


                                ; resdc@epSatLevelSpacing = 1 ; saturation level spacing
;  resdc@epExplicitHueLevels {float[resdc]} ; user set hue levels
; resdc@epMaxHueLevel = 23 ; maxx hue level
      resdc@epMinHueLevel = 0 ; minn hue level
;  resdc@epHueLevelSpacing = 1 ; hue level spacing
      resdc@epHueOffset = 180. ; make the first hue this many degrees around the color wheel from red (0-360) [0.]
      resdc@epMinIntensity = 1 ; minimum intensity to use (0-1) [0.8]
      resdc@epColorWheelScale = 0.41 ; change the size of the color wheel by multiplying by this scale factor [1.]
      resdc@epColorWheelCenterX = 0.925 ; center X of color wheel in ndc [0.85]
      resdc@epColorWheelCenterY = 0.937 ; center Y of color wheel in ndc [0.85]
      resdc@epColorWheelPerimOn = False ; draw a box around the color wheel? [False] 
      resdc@mpMinLatF = lat_s
      resdc@mpMaxLatF = lat_n
      
      resdc_title = " phase (color, hours) and magnitude (hue, mm/day)"

; Variancee explained

      resv = True
      resv@gsnFrame = False
      resv@gsnDraw  = False
      
      resv@mpMinLatF = lat_s
      resv@mpMaxLatF = lat_n
      
      resv@cnInfoLabelOn        = False
      resv@tiMainString = "Diurnal variance explained (%)"
      
      
      resv@cnFillOn            = True               ; turn on color fill
      resv@lbLabelBarOn        = True
      resv@mpFillOn            = True     ; turn off grey continents
      resv@cnLinesOn           = False
      resv@cnRasterModeOn = True
      
      resv@lbOrientation       = "Vertical"
      resv@lbBoxMinorExtentF = 0.15
      resv@lbLabelStride = 2
      resv@lbAutoManage        = False
      resv@lbBoxMinorExtentF   = 0.06
      resv@lbLabelFontHeightF  = 0.01
      resv@lbLeftMarginF       = -0.7
      resv@lbRightMarginF      = 0.001
      resv@lbLabelPosition     = "Right"
      resv@lbLabelOffsetF = 0.02
      
      
      
      resv@cnLevelSelectionMode = "ExplicitLevels"
      resv@cnFillColors        = (/0,13,15,16,34,36,197,200,178,169,144,148,150,135,138,127,139,130,95,97,76,80/)
      resv@cnLevels            = (/0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100/)
;  resv@cnFillColors        = (/0,15,34,197,178,144,150,138,139,95,76/)
;  resv@cnLevels            = (/0,10,20,30,40,50,60,70,80,90,100/)
; Mean

      res = True
      res@gsnFrame = False
      res@gsnDraw  = False
      
      res@mpMinLatF = lat_s
      res@mpMaxLatF = lat_n
      
      
      res@cnInfoLabelOn        = False
      res@tiMainString = "Mean precipitation (mm/day)"
      
      res@cnFillOn            = True               ; turn on color fill
      res@lbLabelBarOn        = True
      res@mpFillOn            = True     ; turn off grey continents
      res@cnLinesOn           = False
      res@cnRasterModeOn = True
      
      res@lbOrientation       = "Vertical"
      res@lbBoxMinorExtentF = 0.15
      res@lbAutoManage        = False
      res@lbBoxMinorExtentF   = 0.06
      res@lbLabelFontHeightF  = 0.01
      res@lbLeftMarginF       = -0.7
      res@lbRightMarginF      = 0.0001
      res@lbLabelOffsetF = 0.02
      res@lbLabelStride = 2
  

      res@cnLevelSelectionMode = "ExplicitLevels"
      res@cnFillColors        = (/0,13,15,16,34,36,197,200,178,169,144,148,150,135,138,127,139,130,95,97,76,80/)
      res@cnLevels            = (/0,0.5,1.,1.5,2.,3.,4,5.,6.,7,8,9,10,12,14,16,18.,20,25,30,40/)
;  res@cnFillColors        = (/0,15,34,197,178,144,150,138,139,95,76/)
;  res@cnLevels            = (/0,1.,2.4,6.8,10,15,20.,25,40/)


 
; USA focus?

;      if (usa_plot) then

        res2 = res
        resv2 = resv
        resdc2 = resdc

        res2@mpOutlineBoundarySets = "GeophysicalAndUSStates"
        resv2@mpOutlineBoundarySets = "GeophysicalAndUSStates"
        resdc2@mpOutlineBoundarySets = "GeophysicalAndUSStates"
        res2@gsnAddCyclic = False
        res2@mpMinLonF = lon_w_2
        res2@mpMaxLonF = lon_e_2
        res2@mpMinLatF = lat_s_2
        res2@mpMaxLatF = lat_n_2
        resv2@gsnAddCyclic = False
        resv2@mpMinLonF = lon_w_2
        resv2@mpMaxLonF = lon_e_2
        resv2@mpMinLatF = lat_s_2
        resv2@mpMaxLatF = lat_n_2
        resdc2@gsnAddCyclic = False
        resdc2@mpMinLonF = lon_w_2
        resdc2@mpMaxLonF = lon_e_2
        resdc2@mpMinLatF = lat_s_2
        resdc2@mpMaxLatF = lat_n_2
        
        maxsatlevel2 = (/5, 5.,  3.,   2.25 /)
        minsatlevel2 = (/0.1, 0.1,  0.33, 0.25 /)
        maxhuelevel2 = (/23, 11.5, 7.66, 5.75 /)
        huespacing2 =  (/1., 0.5,  0.33, 0.25 /)
        
;      end if



; Panel

      pan = True
      pan@gsnMaximize = True
;  pan@gsnPanelYWhiteSpacePercent = 5.
      pan@gsnPanelTop = 0.9
      
      pan@gsnPaperOrientation = "Landscape"
      pan@txString =  "Diurnal Cycle"
      pan@txString = ""

      do irun=0,nruns-1

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; Derived variables.
        vscale = 1.0
        
        run_name = run_names(irun)
        run_title = run_titles(irun)
        if (obs(irun)) then ; ********* TRMM ************
          print("** OBSERVED DATA")
          run_name = "3B42"
          vscale = 24. ; For MSS data.
          lon_w = lon_w-180. ; Specify -180.->180 range for TRMM
          llon_e = lon_e-180.
;          dir_root = "/datalocal/haystack/cchen/dcycle/3hrly/"
          run_years = orun_years
        else  ; ************* CAM/CCSM ***********
          print("** model output")
;          if  (any(var_name.eq.(/"PRECT","PRECC","PRECL","PRECSH"/))) then
            vscale = 86400.0
;          end if
          run_years = mrun_years
        end if
        
;; Loop for different periods.
        
        print("***** Run Name =  "+run_name+" ***")
        if (dimsizes(mrun_years).eq.1) then
          print("***** Year = "+ sprinti("%0.4i",run_years)) 
        else
          print("***** Years = "+ sprinti("%0.4i",min(run_years))+" to "+ sprinti("%0.4i",max(run_years)))
        end if
        
;;;;
; Get data.
  
; Pre-calculate weighting data.

      wgt_tot = sum(mwt)*nyears
      
      do iyear=0,nyears-1
        
        srun_year = sprinti("%0.4i",run_years(iyear)) ; String version for current year (needed when years are <1000)
        print("")
        print ("*** Year = "+srun_year)
        do imonth=0,nmonths-1
          
          if (obs(irun).and.months(imonth).eq."02".and.any(run_years(iyear).eq.(/"1976","1980","1984","1988","1992","1996","2000","2004","2008"/))) ; leap year feb in obs?
            wgt_mon = mwt(imonth)+1 ; Add 1 day to month weighting
            wgt_tot = wgt_tot+1 ; Add 1 day to total weighting 
            leap_feb = " (leap year)"
          else
            wgt_mon = mwt(imonth)
            leap_feb = ""
          end if
          
          print("")
          print ("*** Month/year = "+mon_name(toint(months(imonth))-1)+" ("+srun_year+") : Weight = "+wgt_mon+" days "+leap_feb)
          
          print("** Checking data")
          
          if (obs(irun)) then
;            infiles = systemfunc("ls -1 "+dir_root+run_name+"."+srun_year+months(imonth)+".3hr.nc")
            tpert = 0.
          else
            if (model_fstruc.eq.0) then
; 0 = Single file containing data.
;           infiles =  getenv("file_path")+"/"+getenv("CASENAME")+"."+getenv("PRECT_var")+".3hr.nc"
           infiles = getenv("PR_FILE")
;              infiles = systemfunc("ls -1 "+dir_root+run_name+"/"+rsub_dir+run_name+".cam2.h"+hchan+"."+srun_year+"."+var_name+".nc") ; Single file.
;           infiles = systemfunc("ls -1 "+dir_root+run_name+"/"+rsub_dir++run_name+".cam2.h"+hchan+".{"+ym1+","+srun_year+"}-??-??-?????.nc") ; this year+ previous year.
            end if      
; 1 = many files with single or multiple time points.
; Bit tricky with the file structure 1 include a month before this month to capture required dat period, doo special things for Dec and Jan
;     
            if (model_fstruc.eq.1) then
              if (months(imonth).eq."01") then
                mm1 =  tostring(12)  ; December and year minus 1
                ym1 =  sprinti("%0.4i",run_years(iyear)-1)
;                infiles = systemfunc("ls -1 "+dir_root+run_name+"/"+rsub_dir+run_name+".cam2.h"+hchan+".{"+ym1+"-"+mm1+","+srun_year+"-"+months(imonth)+"}-??-*")
;                infiles = systemfunc("ls -1 "+dir_root+run_name+".PRECC.{"+ym1+mm1+","+srun_year+months(imonth)+"}*.nc") ; SE infiles.
;                infilesl = systemfunc("ls -1 "+dir_root+run_name+".PRECL.{"+ym1+mm1+","+srun_year+months(imonth)+"}*.nc") ; SE infiles.
              else
                mm1 =  sprinti("%0.2i",(/toint(months(imonth))-1/)) ; Month minus 1
                mm2 =  sprinti("%0.2i",(/toint(months(imonth))-2/)) ; Month minus 1
                mp1 =  sprinti("%0.2i",(/toint(months(imonth))+1/)) ; 
;                infiles = systemfunc("ls -1 "+dir_root+run_name+"/"+rsub_dir+run_name+".cam2.h"+hchan+"."+srun_year+"-{"+mm1+","+months(imonth)+"}-??-*")

;                 infiles = systemfunc("ls -1 "+dir_root+run_name+".PRECC."+srun_year+"{"+mm2+","+mm1+","+months(imonth)+","+mp1+"}*.nc") ; SE infiles.
;                infilesl = systemfunc("ls -1 "+dir_root+run_name+".PRECL."+srun_year+"{"+mm2+","+mm1+","+months(imonth)+","+mp1+"}*.nc") ; SE infiles.
                print(infiles)


              end if
            end if
            
            tpert = 0.00001 ; Some temporary fix for incorrect cd_calendar functionality (rounding)
            
          end if
          
          inptr = addfiles(infiles,"r") 
;          print(infiles)    
;          inptrl = addfiles(infilesl,"r")   

; Some time checking for this month.
; - Does it start and stop on the right hour and day?
; - Are alll the samples there? 
   
;Read in available times
          time = inptr[:]->time
          time = time+tpert ; Add pert for model analysis (temporary) 
          time@calendar = "noleap" ; Calendar meta data correction 

; YYYYMMDDHH format.
        if(obs(irun)) then
          date =  inptr[:]->date
          datesec = inptr[:]->datesec
          t_utc = date*100 + datesec/3600
          delete(date)
          delete(datesec)
         else
          t_utc = cd_calendar(time,-3)
         end if
 
; Requested start time and index in data
          if (date_offset.eq.0) then
            ; CMIP / GFDL date index
            tstart = toint(run_years(iyear))*1000000+toint(months(imonth))*10000+(1*101) 
          else if (date_offset.eq.1) then
            ; CESM native date index
            tstart = toint(run_years(iyear))*1000000+toint(months(imonth))*10000+(1*100) 
          end if
          end if
          print(tstart)

; TSJ edit 2021-01-12: This step no longer necessary with the replacement of 
; ut_calendar by cd_calendar. See 
; https://www.ncl.ucar.edu/Document/Functions/Built-in/cd_calendar.shtml ,
; in particulare Example 5.
;
; ; Adjust for ut_calendar problems in cam/climo runs as the first year is usually 0000 and
; ; ut_calendar changes this to 0001 !! So adjust tstart forward by 1 year.
;           if (time@units.eq."days since 0000-01-01 00:00:00") then
;             tstart = tstart + 1000000
;             print("- Adjusting start date for CAM standalone runs which begin 0000 and ut_calendar switches in to 0001")
;           end if

         ; print(t_utc)
         ; print(tstart)
; Where in alll of input data is tstart?
          itm0 = ind(t_utc.eq.tstart)
          if (ismissing(itm0)) then
            print("*** Requested start date does not exist in available data - exiting ...")
            exit
          end if
; dt for the first timestep
          dtime = where(t_utc(itm0+1)-t_utc(itm0).gt.24,t_utc(itm0+1)-t_utc(itm0)-100+24,t_utc(itm0+1)-t_utc(itm0)); Convoluted but corrects for incrementing day and resetting hour.  
          
; Can now determine stop time given dt
          tstop = tstart+toint(wgt_mon-1)*100+(24-toint(dtime))
          itm1 = ind(t_utc.eq.tstop)
          
; Check constant dt across requested month
          do it=itm0+2,itm1,1 
            dtimei =  where(t_utc(it)-t_utc(it-1).gt.24,t_utc(it)-t_utc(it-1)-100+24,t_utc(it)-t_utc(it-1)) ; Convoluted but corrects for incrementing day and resetting hour.
            if (dtime.ne.dtimei) then
              print("**** Timestep not constant through timeseries - exiting...")
              exit
            end if          
          end do
          
          print("- Data time resolution is a constant "+dtime+" hours")
          
          print("- Input time range = "+min(t_utc)+" to "+max(t_utc))
          print("- Requested  range = "+tstart+" to "+tstop)
          
          if (tstart.lt.min(t_utc).or.tstop.gt.max(t_utc)) then
            print("Predicted data range not available in input data - exiting...")
            exit
          else
            print("- Correct time range is available: "+tstart+" to "+tstop)
            itime0 =  ind(t_utc.eq.tstart)
            itime1 =  ind(t_utc.eq.tstop)
            print("- Data istart-istop-ntime indices = "+itime0+" "+itime1+" "+(/dimsizes(time)/))
          end if
          
          print("** Grabbing data")
          
          if (obs(irun)) then
            invar = inptr[:]->precip(itime0:itime1,{lat_s:lat_n},{lon_w:lon_e})
            vscale = 24.
          else


    ;        precc = inptr[:]->PRECC(itime0:itime1,{lat_s:lat_n},{lon_w:lon_e})


     ;       precl = inptrl[:]->PRECL(itime0:itime1,{lat_s:lat_n},{lon_w:lon_e})
     ;       invar = precl
     ;       invar = (/precl+precc/)
     ;       delete(precc)
     ;       delete(precl)
            invar = inptr[:]->$var_name$(itime0:itime1,{lat_s:lat_n},{lon_w:lon_e})
            if (.not.isdefined("invar")) then
              invar = inptr[:]->$var_name$(itime0:itime1,{lat_s:lat_n},{lon_w:lon_e}) 
            end if
          end if
          invar&time@calendar = "noleap"

                                ; Other dimension information.
          if (.not.isdefined("lat")) then
            lon = invar&lon
            lat = invar&lat
            nlon = dimsizes(lon)
            nlat = dimsizes(lat)
          end if
          
; Record whether this is a time_averaged or instantaneous output
; as it requires adjustment later.   
          
          hour_tave_cent = 0.
          if (isatt(invar,"cell_method").or.isatt(invar,"cell_methods")) then
            if (isatt(invar,"cell_method")) then
              vcell_method = invar@cell_method
            else
              vcell_method = invar@cell_methods
            end if
    ;        if (vcell_method.eq."time: mean") then
              tinst = False
              hour_tave_cent = tofloat(dtime)/2
              print("-Time averaged data - Requires time-centering adjustment of -"+tofloat(dtime)/2+" hours")
     ;       else
     ;         print("*Unknown/incompatible averaging method. Exiting...")
     ;         exit
     ;       end if
          else
            print("-Instantaneous data - Requires no time-centering adjustment")
            tinst = True
          end if
          
          invar = (/invar*vscale/) ; Scale for mm/day
          
          delete(t_utc)
          
          print("** Done data grab!")
          
     
;;;;
; Diurnal cycle (should come back with composite diurnal cycle only now)
      
          print("** Compositing diurnal cycle for this data...")
          
          dcycle_month =  dcycle_calc_cam(invar)  
          
; Need to chekc and deal with missing data + create weighting array.
          
          dcycle_mwgt = dcycle_month
          dcycle_mwgt = (/dcycle_month*0.+wgt_mon/)
      

     ; Iff anyy single missing data in a composite diurnal cycle in a whole month thenn set alll to zero.

          if (any(ismissing(dcycle_month))) then
            
            do ilat=0,nlat-1
              do ilon=0,nlon-1
                if (any(ismissing((dcycle_month(:,ilat,ilon))))) then
                  dcycle_month(:,ilat,ilon) = 0.
                  dcycle_mwgt(:,ilat,ilon) = 0.
                end if
              end do
            end do
          else
            print(" -No missing data for this time period.")
          end if 
      


; Iff first set of data assign to summed arrays otherwise pass to array with weight.

          if (iyear.eq.0.and.imonth.eq.0) then        
            dcycle =  dcycle_month
            dcycle = (/dcycle_month*dcycle_mwgt/)
            dcycle_mwgt_sum = dcycle_mwgt
          else        
            dcycle = (/dcycle_month*dcycle_mwgt+dcycle/)
            dcycle_mwgt_sum = dcycle_mwgt+dcycle_mwgt_sum
          end if
          
          
          delete(dcycle_month)
          delete(dcycle_mwgt)
          
; Clean up for this set of data
          
          delete(infiles)
;          delete(infilesl)
          delete(inptr)
          delete(invar)
          delete(time)
          
        end do ; month
      end do ; year
      
      print("")
      
;; Rescale by summ of weights
; Have to change zeros to ismissingg as division will fail, thenn change back again for the ftransform
      
      dcycle_mwgt_sum = where(dcycle_mwgt_sum.ne.0,dcycle_mwgt_sum,dcycle_mwgt_sum@_FillValue)
      dcycle = (/dcycle/dcycle_mwgt_sum/)
      dcycle =  where(ismissing(dcycle),0.,dcycle)
      
      
; Calculate 3 harmonics at each grid point.
; Phase is in hours from 0Z

      ntspd = dimsizes(dcycle&time)
      
      dc_harm = fourier_info (dcycle(lat|:,lon|:,time|:),nharm,24/ntspd)
      dc_harm!0 = "cat"
      dc_harm!1 = "lat"
      dc_harm!2 = "lon"
      dc_harm!3 = "harmonic"
      
      dc_harm&lat = dcycle&lat
      dc_harm&lon = dcycle&lon
      
      dc_harm@_FillValue = dcycle@_FillValue
 
; Adjust for local time, t=0
; Check start times from time coordinate.

      print( "** Adjust for local timing")

; Loop over each longitude for the time offset.
; Calculate adjusted phase maxx in hours.

      harm_ph = (/1.,2.,3.,4./) ; Number of cycles per day for each harmonic
      
      do ilon=0,nlon-1
        hour_lon = doubletofloat(24.*lon(ilon)/360.)      ; Local time zone offset (hours) from 00Z.
        hour_offset = hour_lon-hour_tave_cent ; Full offset with start time and for time_averaged time cetneraing
; Loop over harmonics for offset for long and time
        do iharm=0,nharm-1 
          hhoffm = 24./harm_ph(iharm) ; Phase offset maxx (cyclic)
          dc_o = dc_harm(1,:,ilon,iharm)+hour_offset ; Offset
          do while(min(dc_o).lt.0.or.max(dc_o).gt.hhoffm)
            dc_o = where(dc_o.gt.hhoffm, dc_o-hhoffm, dc_o) ; Rescale to < hhoffm?
            dc_o = where(dc_o.lt.0., dc_o+hhoffm, dc_o) ; Rescale to > 0?
          end do
          dc_harm(1,:,ilon,iharm) = (/dc_o/)
        end do
      end do
      
; Magnitude + phase
      
      print("** Creating magnitude and phase arrays for plotting...")
      
;;;;
; Plot tmean,  phase (hue) and magnitude (saturation),and variancee explained
      
      dcycle_plot = new((/nlat,nlon/),float)
      
      dcycle_plot!0 = "lat"
      dcycle_plot&lat = lat
      dcycle_plot!1 = "lon"
      dcycle_plot&lon = lon
      
      dcycle_plot(lat|:,lon|:) = dim_avg_Wrap(dcycle(lat|:,lon|:,time|:)) 
      dcycle_plot = where(ismissing(dcycle_mwgt_sum(0,:,:)),dcycle_mwgt_sum@_FillValue,dcycle_plot)
      
      harm_title = (/"Diurnal","Semi-diurnal","Third-diurnal","Quarter-diurnal"/)
      
      print("")
      do iharm=0,nharm-1   
        
        print("Plotting figs. for harmonic - "+iharm)
        
        print("-Magnitude and phase...") 
        dc_mag = dc_harm(0,:,:,iharm)
        dc_phase = dc_harm(1,:,:,iharm)
        dc_var = dc_harm(2,:,:,iharm)
        
        dc_mag = where(ismissing(dcycle_plot),dcycle_mwgt_sum@_FillValue,dc_mag)
        dc_phase = where(ismissing(dcycle_plot),dcycle_mwgt_sum@_FillValue,dc_phase)
        dc_var = where(ismissing(dcycle_plot),dcycle_mwgt_sum@_FillValue,dc_var)
        
        resdc@tiMainString = run_title

; Adjust wheel contours+labels for semi-diurnal and higher harmonics.
       
        if (phase_only) then
          resdc@epMaxSatLevel = 0.001
          resdc@epMinSatLevel = 0.
        else
          resdc@epMaxSatLevel = maxsatlevel(iharm)
          resdc@epMinSatLevel = minsatlevel(iharm)
          resdc2@epMaxSatLevel = maxsatlevel2(iharm)
          resdc2@epMinSatLevel = minsatlevel2(iharm)
        end if
        
        resdc@epSatLevelSpacing = (resdc@epMaxSatLevel-resdc@epMinSatLevel)/8.
        resdc@epMaxHueLevel     = maxhuelevel(iharm)
        resdc@epHueLevelSpacing = huespacing(iharm)
        resdc2@epSatLevelSpacing = (resdc2@epMaxSatLevel-resdc2@epMinSatLevel)/8.
        resdc2@epMaxHueLevel     = maxhuelevel2(iharm)
        resdc2@epHueLevelSpacing = huespacing2(iharm)         

;        plot(irun) = evans_plot_map(wks,dc_phase,dc_mag,resdc)   
        plot1(irun) = evans_plot_map(wks1,dc_phase,dc_mag,resdc)   
       
        print("-% of diurnal variance explained")     
       
;        plot(1) = gsn_csm_contour_map_ce(wks,dc_harm(2,:,:,iharm),resv)
        plot1(1) = gsn_csm_contour_map_ce(wks1,dc_harm(2,:,:,iharm),resv)       

        print("-Mean precip")
       
;        plot(2) = gsn_csm_contour_map_ce(wks,dcycle_plot,res)
        plot1(2) = gsn_csm_contour_map_ce(wks1,dcycle_plot,res)    
        

; USA plot
        plot2(irun) = evans_plot_map(wks2,dc_phase,dc_mag,resdc2)
        plot2(1) = gsn_csm_contour_map_ce(wks2,dc_harm(2,:,:,iharm),resv2)
        plot2(2) = gsn_csm_contour_map_ce(wks2,dcycle_plot,res2)        

      end do ; harmonic loop

      delete([/lon,lat,dcycle,dc_mag,dc_phase,dc_harm,dc_var,dcycle_plot,dc_o,dcycle_mwgt_sum/])
      
    end do ; Run loop


;    gsn_panel(wks,plot,(/3,1/),pan)

    gsn_panel(wks1,plot1,(/3,1/),pan)
    gsn_panel(wks2,plot2,(/3,1/),pan)

;    delete(plot)
    delete(plot1)
    delete(plot2)

    delete(months)
    delete(mwt)
    print("*** "+stitle+" Done!")  

    
  end do ; Season loop

  print (" ++++++++ ALL DONE ++++++++ ")



end
