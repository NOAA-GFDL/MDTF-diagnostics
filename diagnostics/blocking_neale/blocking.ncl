load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl" 
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$POD_HOME/blocking_funcs.ncl"
load "$POD_HOME/blocking_digested.ncl"
;=========================================
; - RBN 11MAR14 -
; Reads in daily Z500mb and constructs various indices and plots of blocking.
; Analyzes many ensemble members and plots the mean and spread or std
; Can accomodate data of different resolutions.
; - DRBC Feb 2021
; separate some analysis and plotting functions into blocking_funcs
; make controllable by env vars
; - DRBC May 2023: Add multi-run capability
begin 

lstd = False     ; Plot standard dev lines (otherwise plot min/max which is UNTESTED).


opts = True
set_digested(opts) ; translates env vars to opts@read_digested,write_digested
                   ; this is used by all_cases to set file names

all_cases = blocking_get_all_case_info(opts) 
printVarSummary(all_cases)
; opts = data structure to hold all case information of length number of files
; case_names,case_type,file_names,@years_run0, years_run1 = start and stop years corresponding to above



obs_inds = get_obs_inds(all_cases@case_names)

nlines = all_cases@nobs+all_cases@nens ; nobs + nens (model)

;;;;;;;;;;;;;;;; Settings ;;;;;;;;;;;;;;;;;;;;

nstd = 1 ; Number of st .devs. +/- to plot (of ensembles)


; Settings structure holds phi_n,phi_0,phi_s,ghgn_thresh,ghgs_thresh
settings = True
settings = get_blocking_settings()


;Plot settings


plot = set_plotting_info(all_cases,settings) ;plot(nfiles) for panel
plot_t = new(all_cases@nfiles,graphic)



pan_t = get_plot_settings_t(all_cases) ; hovmueller
pan_m = get_plot_settings_m(all_cases) ; line -plot


; sets attributes of all_cases that are used by subsequent  functions
; adds attrs: line_types, nens, nobs, nlines
file_opts = True

; Regional subset of data to read in
latn_in = 85. 
lats_in = 20.
lone_in = 360.
lonw_in = 0.

; Loop seasons. (Currenly only tested with one season, ANN)

do ip=0,settings@nperiods-1

  period_name = settings@period_names(ip)

; Loop cases

do ifile=0,all_cases@nfiles-1
   if (isdefined(file_opts)) then
     delete(file_opts)
   end if

   file_opts = True

   print("--- Opening "+all_cases@case_names(ifile)+" (: "+all_cases@file_names(ifile))
   file_opts = extract_file_opts(all_cases,ifile)
   ; Add additional settings
   file_opts@period_name = period_name  ; set above
   file_opts@latn_in = latn_in 
   file_opts@lats_in = lats_in
   file_opts@lone_in = lone_in
   file_opts@lonw_in = lonw_in
   
   ; Check for global read digested settings (MDTF case restricted to only undigested)
   if (opts@MDTF_BLOCKING_READ_DIGESTED.and.(file_opts@case_type.ne."MDTF")) then  ; read in block_time
     print("Opening digested file")
     f_dig = open_digested(file_opts)

     time_ymd = blocking_readtime(f_dig,file_opts)  ; time_ymd(idays)
               ; also returns as attributes @time(idays) , @idays (for var indexing)

     idays    = file_opts@idays     ; only used for writing out ?     
     ndays = dimsizes(idays)     
     time = time_ymd&time


     block_time = f_dig->$var_name$(idays,:) ; set in blocking_digested, needs  ; better var name!

     lon = f_dig->lon
     nlons = dimsizes(lon)

   else  ; opts@MDTF_BLOCKING_READ_DIGESTED = False
     print("Opening un-digested file")
     var_in_p = blocking_readfile_orig(file_opts)           ; Data actually read here
             ;file_opts in:  year0,year1,period_name,filename,var_name,lat/lon limits
             ;file_opts out: time_ymd, idays,time

     time_ymd = file_opts@time_ymd  ; used in analysis

     idays    = file_opts@idays     ; only used for writing out ?
     time     = file_opts@time      ; only used for writing out ?
     ndays = dimsizes(idays)     

     lon = file_opts@lon
     lat = file_opts@lat
     
     nlons = dimsizes(lon)
     lon@long_name = "longitude"

     ; Now do the blocking analysis

     ; Set arrays
     ghgs = new((/settings@ndels,nlons/),float)
     ghgn = new((/settings@ndels,nlons/),float)
     
     block_time = new((/ndays,nlons/),integer)
     block_time!0 = "time"
     block_time!1 = "lon"

     block_time&time = time ; already idays dimension
     block_time&lon = lon

     
     block_time@long_name = "Blocking index (0=no; 1=yes)"
     
     block_time = (/0/)
     
     do iday=0,ndays-1 ; loop days of period
       lblock = False
       
; Calculate block for alll longitudes.
       var_phi_n = (/var_in_p(iday,{settings@phi_n},:)/)
       var_phi_0 = (/var_in_p(iday,{settings@phi_0},:)/)
       var_phi_s = (/var_in_p(iday,{settings@phi_s},:)/)
       
       do idel=0,settings@ndels-1
         ghgs(idel,:) = (var_phi_0(idel,:)-var_phi_s(idel,:))/(settings@phi_0(idel)-settings@phi_s(idel))
         ghgn(idel,:) = (var_phi_n(idel,:)-var_phi_0(idel,:))/(settings@phi_n(idel)-settings@phi_0(idel))
         block_time(iday,:) = where((ghgs(idel,:).gt.settings@ghgs_thresh).and.(ghgn(idel,:).lt.settings@ghgn_thresh).or.(block_time(iday,:).eq.1),1,0)
       end do
                                ; L300 
     end do ; day loop
     
     ; If instructed, write out a file containing this information to
     ;  shortcut this processing next time.

     write_digested(block_time,file_opts)
     
     delete([/var_in_p,var_phi_n,var_phi_0,var_phi_s/])

     delete([/ghgs,ghgn,lat/])

 end if ; opts@MDTF_BLOCKING_READ_DIGESTED


;Initialize plotting arrays
   if (ifile.eq.0) then
     lons_plot = get_lons_plot()
     nlons_plot = dimsizes(lons_plot)
     block_freq_p = new((/all_cases@nfiles,nlons_plot/),float)
     block_freq_p!1 = "lon"
     block_freq_p&lon = lons_plot
     block_freq_p = (/0./)
   end if

; Block frequency
   block_days = new(nlons,integer)
   block_std = new(nlons,float)
   block_days = (/0/)

   block_std = (/0./)

   years = ispan(file_opts@year0,file_opts@year1,1)
   nyears = dimsizes(years)    
   year_avgs = new(nyears,float)


     time_y = time_ymd(:,0) 
     time_m = time_ymd(:,1)
     time_d = time_ymd(:,2)
     time_y@long_name = "Time (year)"
     time_m@long_name = "Time (month)"
     time_d@long_name = "Time (day of month)"
     time_y!0 = "time"
     time_m!0 = "time"
     time_d!0 = "time"
     time_y&time =  time(:) 
     time_m&time =  time(:)
     time_d&time =  time(:)
     
     delete(time)
     delete(time_ymd)
     delete(idays)

     case_years_used = True ; will get opts @min, @max
; Annual variance calculation (sum block per year per lon)
   do ilon=0,nlons-1
      do iyr=0,nyears-1
        idyrs = ind(time_y.eq.years(iyr))
        if (any(.not.ismissing(idyrs))) then
          year_avgs(iyr) = sum(tofloat(block_time(idyrs,ilon)))
          set_case_years(case_years_used,years(iyr)) ; records min/max for figure title
        else
          if (ilon.eq.0 ) then
            print("WARNING: no data found for year "+years(iyr))
          end if
        end if ; ismissing(idyrs)
        delete(idyrs)
      end do ; iyr

      block_days(ilon) = sum(block_time(:,ilon))  ; For the entire range)
      block_std(ilon)  = dim_stddev_Wrap(year_avgs)


  end do ; ilon
  file_opts@year_range =   " ("+case_years_used@min+\
                            "-"+case_years_used@max+")"


; Need to intepolate here iff not the base longitude resolution
  block_freq = 100.*tofloat(block_days)/ndays


  if (nlons.ne.nlons_plot) then
    block_freq_p(ifile,:) = linint1_Wrap(lon,block_freq,True,lons_plot,0)
  else
    block_freq_p(ifile,:) = (/block_freq/) ; For plotting (days->freq)
  end if

  print(" Sanity check: block freq range "+min(block_freq_p(ifile,:))+"-"+max(block_freq_p(ifile,:)))

; Plots of individual cases with time axes
; ndoys = 365 always (remove extra day in obs for simplicity)
; Only plot hov iff ANN period.
  
  if (period_name.eq."ANN") then
    ndoys = 365
    if (time_m(0).ne.1.and.time_d(0).ne.1) then
      print("First data point is not Jan 1; stopping...")
      exit
    end if
    
    block_freq_yr = new((/ndoys,nlons/),float)
    block_freq_yr!0 = "doy"
    block_freq_yr!1 = "lon"
    block_freq_yr&doy = ispan(1,365,1)
    block_freq_yr&lon = lon

    idoy = 0
    do it=0,ndoys-1
      if (time_m(idoy).eq.2.and.time_d(idoy).eq.29) then ; Skip Feb 29 for ease.
        idoy=idoy+1
      end if
      ids = ind(time_m.eq.time_m(idoy).and.time_d.eq.time_d(idoy))
      ndays_av = tofloat(dimsizes(ids))

      if (ndays_av.eq.1) then
        block_sum = tofloat(block_time(ids,:))
      else
        block_sum = dim_sum_n(tofloat(block_time(ids,:)),0)
      end if

      block_freq_yr(it,:) = 100.*block_sum/tofloat(ndays_av)

      delete(ids)
      delete(block_sum)
      idoy=idoy+1
    end do

    do ismth = 1,20
      block_freq_yr = smth9_Wrap(block_freq_yr, 0.50,  0.50, True) 
    end do

    ; get the file indices for this ensemble/group or individual
    this_ens_name = get_ens_name_or_obs_name(all_cases@case_names(ifile))
    ens_file_inds = get_file_indices_from_ens_name_group_obs(this_ens_name,all_cases@case_names)

    ; if this is the first file in the ensemble, create the panel graphics object
    if (ifile.eq.min(ens_file_inds)) then  
      res_t = True  ;output from get_plot_*
      wks_ens_page = get_plot_anncycle_ensname(this_ens_name,all_cases,settings,res_t)
    end if

    res_t@tiMainString = file_opts@case_name +file_opts@year_range


    ; draw the Hovmueller figure (individual panels for each file)
    plot_t(ifile) = gsn_csm_hov(wks_ens_page, lonPivot(block_freq_yr,270.), res_t) 

    ; if this is the last file in the ens, draw and write the panel plot of
    ; all ensemble Hov figures
    if (ifile.eq.max(ens_file_inds)) then 
      panel_layout = get_panel_layout(dimsizes(ens_file_inds))
      gsn_panel(wks_ens_page,plot_t(ens_file_inds),panel_layout,pan_t)
      delete(ens_file_inds)  
      delete(wks_ens_page)
      delete(res_t)
      delete(panel_layout)
    end if

    delete([/block_freq_yr/])
       
  end if

; Further analysis for synoptic blocking (continuous days)

  bsum_pac = 0
  bsum_atl = 0
  bdays_pac = 0
; L400

; Variance plots
  bmean_std = new((/3,nlons/),float)
  bmean_std!1 = "lon"
  bmean_std&lon = lon

  bmean_std(0,:) = (/block_freq+block_std/)
  bmean_std(1,:) = (/block_freq/)
  bmean_std(2,:) = (/block_freq-block_std/)
 
  bmean_v = lonPivot(bmean_std,270.)

; Delete stuff for next case

  delete([/time_y,time_m,time_d,lon,block_time,block_days,block_std,years,bmean_std,bmean_v,block_freq,year_avgs/])
  delete(case_years_used)

end do ; ifile Period/Year loop

; Plot zonal distribution of mean blocking frequency.

block_freq_pp = lonPivot(block_freq_p,270.) ; Flip lon for plotting


; Construct plot of means for each ensemble and std or range.

plot_stds = new(all_cases@nens,"graphic")


block_freq_aves = new((/nlines,nlons_plot/),float)
block_freq_min = new((/nlines,nlons_plot/),float)
block_freq_max = block_freq_min


if ( .not.any(ismissing(obs_inds))) then
  inds_obs_plot = ispan(0,all_cases@nobs-1,1)

  block_freq_aves(inds_obs_plot,:)  = block_freq_p(obs_inds,:)    ; Copy observations (ERAI+MERRA) direct.
  block_freq_min (inds_obs_plot,:)  = block_freq_p(obs_inds,:)     ; to mean, minn and maxx.
  block_freq_max (inds_obs_plot,:)  = block_freq_p(obs_inds,:)   
else
  print("WARNING: running without obs might not produce figures, only digested data")
end if

; Loop over ensemble sets (may be of member size 1)
do iens=0,all_cases@nens-1

                                ; indices in the data array
  ens_file_inds = get_file_indices_from_ens_name(all_cases@ensemble_names(iens),all_cases@case_names)
  nfiles_in_ens = dimsizes(ens_file_inds)

  
;; Averages
  plot_inds = all_cases@nobs+iens  ; indices in the plotting array

  if (nfiles_in_ens.eq.1) then
    block_freq_aves(plot_inds,:) = block_freq_p(ens_file_inds,:)  ;  otherwise it averages over time
                                ; leave min/max alone here and they won't be plotted (?!)
    block_freq_aves(plot_inds,:)  = block_freq_p(ens_file_inds,:) ; Copy direct, no mean/max/min plotted
    block_freq_min (plot_inds,:)  = block_freq_p(ens_file_inds,:)     
    block_freq_max (plot_inds,:)  = block_freq_p(ens_file_inds,:)   
  else
    block_freq_aves(plot_inds,:) = dim_avg_n(block_freq_p(ens_file_inds,:),0)

; Standard deviation or range.
    if (lstd) then ; True/False flag at top of script (Calculate std at each longitude.)
      std = dim_stddev_n_Wrap(block_freq_p(ens_file_inds,:),0)
      block_freq_min(plot_inds,:) = block_freq_aves(plot_inds,:)-nstd*std
      block_freq_max(plot_inds,:) = block_freq_aves(plot_inds,:)+nstd*std
      delete(std)
    else ; Plot range at each longitude
      block_freq_min(plot_inds,:) = dim_min_n(block_freq_p(ens_file_inds,:),0)
      block_freq_max(plot_inds,:) = dim_max_n(block_freq_p(ens_file_inds,:),0)
    end if
  end if ; nfiles_in_ens


  delete(ens_file_inds)
end do ; ens sets


; Pivot variables for plotting. (Flip lon for some reason?)
block_freq_aves_p = lonPivot(block_freq_aves,270.) ; Flip lon for plotting
block_freq_min_p  = lonPivot(block_freq_min,270.) ; Flip lon for plotting
block_freq_max_p  = lonPivot(block_freq_max,270.) ; Flip lon for plotting

; Set plotting attributes that would be a pain to put all in the function
res = True   ;will be filled in by get_plot_* through arg list
wks   = get_plot_season(all_cases,settings,res) ; returns all properties in 'res' structure
res@tiMainString = period_name

res_m = get_plot_settings_panel(res,all_cases)
res_m@tiMainString  = res@tiMainString   
res_mm = res_m
res_mm@xyLineColors(inds_obs_plot) = -1*ones_1d_int(all_cases@nobs)   ;turns off lines, we're just doing shading?
res_mm@gsnXYFillOpacities = 0.3*ones_1d_int(nlines)

plot(ip) = gsn_csm_xy (wks,block_freq_aves_p&lon,block_freq_aves_p,res_m) ; Lines of aves. 


; Standard deviations
fcolors = get_light_colors_array(all_cases@line_colors(all_cases@nobs:nlines-1))  ;not obs
do iens=0,all_cases@nens-1
  plot_inds = all_cases@nobs+iens
  res_mm@gsnXYFillColors = fcolors(iens)   ; should grab shading color by ens name

; Plot minn/maxx/mean lines
  
  plot_stds(iens) = gsn_csm_xy(wks,block_freq_aves_p&lon,(/block_freq_min_p(plot_inds,:),block_freq_max_p(plot_inds,:)/),res_mm)

  ; Combine lines plots (ip) with standard deviation shading
  overlay(plot(ip),plot_stds(iens))

end do ; ensembles

print("Finished plotting all ensembles ")

delete([/res_mm@xyLineColors(0:1),res_mm@gsnXYFillOpacities,res_mm@gsnXYFillOpacities/])
delete([/block_freq_p,block_freq_pp,block_freq_min,block_freq_max,block_freq_min_p,block_freq_max_p,block_freq_aves,block_freq_aves_p,block_freq_p/])

end do ; Periods/seasons

; Panel draw.
print("Writing seasons plot (lines). Ignore warning about more plots than panels:")


; Panel plot because of the multiple lines
; generates warning: you have more plots than you have panels
gsn_panel(wks,plot,(/1,settings@nperiods/),pan_m)
legend1 = get_legend(wks,all_cases)
draw(legend1)
frame(wks)



end