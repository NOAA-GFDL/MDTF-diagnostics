
pres_arr=850;

for nyear=1996:2004%1981:2005

  syear=num2str(nyear)
  display('loading p on levels')
  if 1
    set_gfdl_fname
    fname
    load_level_data_for_interp
    calc_new_p
  end
  % after pressure level 15, we are no where near 850 hPa
  % so delete some of these to save memory space;
  puse=pnew(:,1:15,:,:);
  pnew=puse;
  clear puse;
  
  display('loading and converting')
  % load the data on model levels
  load_var_on_level  
  % log-linear interpolation of the data to 850 hPa level
  q850=do_conversion_ONE_pressure(pnew/100,qlev,pres_arr);
  
  q850=squeeze(q850);

  newname=['q850_p1_gfdl_',syear];
  save(newname,'q850','newlon','lat')
end