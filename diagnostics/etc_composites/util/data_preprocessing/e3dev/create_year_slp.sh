cdo mergetime ./2010/2D/slp/*slp*.nc slp.2010.time.nc
cdo mergetime ./2011/2D/slp/*slp*.nc slp.2011.time.nc
cdo mergetime ./2012/2D/slp/*slp*.nc slp.2012.time.nc
cdo mergetime ./2013/2D/slp/*slp*.nc slp.2013.time.nc

# cdo setreftime,2010-01-01,00:00:00 -setcalendar,365_day slp.2010.time.nc slp.2010.nc
# cdo setreftime,2011-01-01,00:00:00 -setcalendar,365_day slp.2011.time.nc slp.2011.nc
# cdo setreftime,2012-01-01,00:00:00 -setcalendar,365_day slp.2012.time.nc slp.2012.nc
# cdo setreftime,2013-01-01,00:00:00 -setcalendar,365_day slp.2013.time.nc slp.2013.nc
#
# cdo setreftime,2010-01-01,00:00:00 -setcalendar,standard slp.2010.time.nc slp.2010.nc
# cdo setreftime,2011-01-01,00:00:00 -setcalendar,standard slp.2011.time.nc slp.2011.nc
# cdo setreftime,2012-01-01,00:00:00 -setcalendar,standard slp.2012.time.nc slp.2012.nc
# cdo setreftime,2013-01-01,00:00:00 -setcalendar,standard slp.2013.time.nc slp.2013.nc

# rm slp.*.time.nc
