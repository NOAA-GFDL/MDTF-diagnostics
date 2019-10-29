# Eulerian Storm Tracker

This code will track Eulerian Strom Tracks. 

## Functions:

six\_hrly\_to\_daily --> converts the six hourly data into daily data

INPUTS: six hrly data, start\_year of the data, and the time variable that is given as hours since start\_year

if multiple years are provided then the time variable has to continue and should not reset every year. 

OUTPUTS: daily output data, and the daily time variable (days since start year)

<br>

daily\_diff --> computes the daily difference, i.e X(t+1) - X(t)

INPUTS: daily\_data

OUTPUTS: difference in daily data

<br> 

std\_dev --> 

  INPUTS: daily data, start year, time array as days since start year

    data input has to be daily in the format (time, lat, lon),

    optional: time_period and season, check below for details

  OUTPUTS: standard\_deviation for the given time\_period, and the time array that corresponds to the std\_dev output (i.e. for yearly it will be the years)
  
  time vaiable has to be specified in days, since start\_year [1,2,3,4,5,6,7...365, 366, 367,... ]

  time\_period can be 'yearly', 'seasonally', or 'all'. Default='all' means standard deviation avarage of all years

  'yearly' means for each year in the input daily data we will compute yearly standard deviation averages

  'seasonally' means for each year in the input daily data we will compute sesonal standard deviation averages. If set as seasonally, then we have to assign the season variable, which can be 'djf', 'mam', jja', or 'son'


