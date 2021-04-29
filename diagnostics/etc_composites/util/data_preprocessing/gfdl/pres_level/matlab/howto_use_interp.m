flager=1
pres_arr=850;

for nyear=1979%1981:2005

  % load the a, b, p0, psurf to create pnew (in Pascals)
  % load the data on model levels, to create vlev
 
  % log-linear interpolation of the data to 850 hPa level
  v850=do_conversion_ONE_pressure(pnew/100,vlev,pres_arr);

end
