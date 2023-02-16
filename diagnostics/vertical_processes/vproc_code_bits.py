'''
	Code bits that I haven't used but might still come in useful
'''


# Squeeze plots together
#    fig.tight_layout(pad=4)
    
    
    
    
    
#    sst_date =  [CalendarDateTime(item, '365_day') for item in sst_ts.time]
#    print(sst_date)
    
#    print(sst_ts.time)
#    ax.set_xticks(iticks)
#    ax.set_xticklabels(tdate_day[iticks].values)
    
    
#    time_stride = mdates.MonthLocator(interval = 12)  ;  myFmt = mdates.DateFormatter('%Y') ##### EVRY YEAR
    
#    mp.gcf().autofmt_xdate() # Diagonal xtick labels.
#    print(time_stride)
#    ax.xaxis.set_major_formatter(myFmt)
#    ax.xaxis.set_major_locator(time_stride)
#    ax.set_xlim(yr0, yr1)

#    sst_yr = sst_ts.time.dt.strftime("%Y") 
    

       
    
#    ax.xaxis.set_major_locator(mdates.MonthLocator(12))
#    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
#    ax.xaxis.set_minor_locator(MultipleLocator(12))
#    ax.tick_params(which='minor', length=7)
    
	
	



#    data_files = xr.open_mfdataset(files_glade,parallel=True,chunks={"time": 100,"latitude": 10, "longitude": 10}) ; HANGS!!    
#    data_files = xr.open_mfdataset(files_glade,parallel=True,chunks={"time": 100}open_)  ; 2.52mins (ERA5: 1979-1990)
#     data_files = xr.open_mfdataset(files_glade,parallel=True,chunks={"time": 12}) ; 3.15 

#    data_files.time.attrs['calendar'] = 'noleap'
#    print(data_files.time)
#    data_files.time.decode_cf
#    print('hi2')
    
    
#    print(data_files)
    
#    time_int = data_files['time'].values.astype(int) # Convert to string for datetime conversion.
#    print(time_int)
#    print([str(time_ii) for time_ii in time_int])
#    time_dtime = [dt.datetime.strptime(str(time_ii), '%J') for time_ii in time_int]
#    print(time_dtime)
    
## STANDARDIZE COORDS/DIMS ##
#    time_dtime = pd.to_datetime(time_str,'%Y%j') 
#    print(time_dtime)



## USUAL WAY ##    
    
#    var_in_seas = var_df.loc[var_cam]['vscale']*var_in[imon_seas,:,:,:].mean(dim=['time']) 
#    var_in_nino = var_df.loc[var_cam]['vscale']*var_in[inino_seas,:,:,:].mean(dim=['time']) 
#    var_in_nina = var_df.loc[var_cam]['vscale']*var_in[inina_seas,:,:,:].mean(dim=['time']) 













    # Poor man's modifcation for lens1 ts
    #    if case_type[icase] == 'lens1' :
    #            month_nums = month_nums-1 # Set back 1 month
    #            month_nums[month_nums ==-1] = 12 # Set -1 months back to 12
    #    mon_obj = dt.datetime.strptime(mon_nums, "%m")

	
	
	
	
	
	
	
	
	
	
	
	
	

    # Seasonal selection for ninos 

    #    lnino_seas = np.isin(hmonths[inino_mons],seas_mons) # Logical for season months in all months
    #    inino_seas= inino_mons[np.argwhere(lnino_seas)[:,0]] # Indices of origin nino_mons that match the season
    #    inino_seas = np.argwhere(lnino_seas)[:,0] # Indices of origin nino_mons that match the season


    #    lnina_seas = np.isin(hmonths[inina_mons],seas_mons) # Logical for season months in all months
    #    inina_seas= inina_mons[np.argwhere(lnina_seas)[:,0]] # Indices of origin nino_mons that match the season
    #    inina_seas= np.argwhere(lnina_seas)[:,0] # Indices of origin nino_mons that match the season   

#        var_in = var_in.loc[:,:,reg_s:reg_n,reg_w:reg_e] # Limit the levels

    #  
     
		
		
		
		
		
		
		
		
		
		
		
		
		   ''' SUBSET SEASON MONTHS '''
    
#    print(files_ptr[var_name].dt)     
#    date_after_month = date.today()+ relativedelta(months=1)
#    print ('Today: ',date.today().strftime('%d/%m/%Y'))
#    print ('After Month:', dt.strftime('%d/%m/%Y'))

#    dt_index = files_ptr.indexes['time'].to_datetimeindex()
#    print(dt.date.today())
#    print(dt_index.month)
#    print(relativedelta(months=-1))
#    print(dt.date.today()+relativedelta(months=-10))

#    print(dt_index+relativedelta(months=+1))

#    print(dt_index.month)
    
    
#    time = files_ptr.time 
#    print(dt_index)
#    files_ptr['time'] = dt_index 
    
#    hmonths = files_ptr.time.dt.strftime("%b")
 
#    print(files_ptr.time.time)
#    print(pd.to_datetime(files_ptr.time))
    

    
	
	
	
	
	
	
	
	
	
	
#	 Construct required history file month-year array

#    hist_myr = np.array([".cam.h0.%d-%02d.nc"%(y, m) for y in range(yr0,yr1+1) for m in range(1,12+1)])
#    num_h0 = hist_myr.size
  

#    hfile_var = get_files_tseries(run_type,case_type,True) # Grab SST files










#%matplotlib inline
#ds.config.set({"array.slicing.split_large_chunks": True})