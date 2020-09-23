# import netcdftime # Jeyavinoth removed netcdftime
import netCDF4 as NetCDF
#import netCDF3 as NetCDF
import datetime
import jj_calendar as jjCal

class Save_NetCDF:
    """Save to basic NetCDF File"""

    def __init__(self,*args,**kwargs):

        self.z = args[0]
        self.lons = args[1]
        self.lats = args[2]
        self.cdf_file = args[3]
        self.missing = args[4]
        
        if 'name' in kwargs:
            self.zname = kwargs['name']
        else:
            self.zname = 'comp'

        if 'long_name' in kwargs:
            self.zlong_name= kwargs['long_name']
        else:
            self.zlong_name = ''
 
        if 'units' in kwargs:
            self.zunits= kwargs['units']
        else:
            self.zunits = ''

        # # Calendar Date Stuff
        # the_calendar = 'standard'
        # unit_string = 'hours since 1-1-1 00:00:0.0'
        # cdftime = netcdftime.utime('hours since 0001-01-01 00:00:00',calendar=the_calendar)
        #
        # times = []
        # for year in range(1990,1991):
        #     d = datetime.datetime(year,1,1,0)
        #     t = cdftime.date2num(d)
        #     times.append(t)
        #
        # Create the file

        rootgrp = NetCDF.Dataset(self.cdf_file, 'w', format='NETCDF3_CLASSIC')

        # Create dimensions:
        rootgrp.createDimension('lon', len(self.lons))
        rootgrp.createDimension('lat', len(self.lats))

        # Create Variables:
        lat = rootgrp.createVariable('lat','f4',('lat',))
        lon = rootgrp.createVariable('lon','f4',('lon',))
        thedata = rootgrp.createVariable(self.zname,'f4',('lat','lon',))

        # Attributes:
        lat.units = 'degrees north'
        lat.actual_range = [self.lats[-1],self.lats[0]]
        lat.long_name = "Latitude"

        lon.units = 'degrees east'
        lon.actual_range = [self.lons[-1],self.lons[0]]
        lon.long_name = "Longitude" 

        if self.zunits:
            thedata.units = self.zunits
        if self.zlong_name:
            thedata.long_name = self.zlong_name 

        # missing_value:
        thedata.missing_value = self.missing

        # Populate lats
        lat[:] = self.lats

        # Populate lons
        lon[:] = self.lons

        # Populate data
        thedata[:] = self.z

        # Write to file
        rootgrp.close()

class Save_NetCDF_TimeSeries:
    """Save to basic NetCDF File with multiple time steps"""

    def __init__(self,*args,**kwargs):

        self.z = args[0]
        self.lons = args[1]
        self.lats = args[2]
        self.times = args[3]
        self.cdf_file = args[4]

        # # Jeyavinoth: here I am removing till "Jeyavinoth: End"
        # # I try and get rid of any netcdftime dependencies
        # # so I use my jj_calendar.py code here to get datetimes
        # # What is needed is the self.the_time, which is datetime format given the times
        # # This code doesn't look like it is getting used anywhere, but not sure 
        # # Calendar Date Stuff
        # the_calendar = 'standard'
        # unit_string = 'hours since 1-1-1 00:00:0.0'
        # #cdftime = netcdftime.utime('hours since 0001-01-01 00:00:00',calendar=the_calendar)
        # cdftime = netcdftime.utime('hours since 1800-1-1 00:00:0.0',calendar=the_calendar)
        # self.the_times = []
        # for dt in self.times:
        #     year = int(dt[:4])
        #     month = int(dt[4:6])
        #     day = int(dt[6:8])
        #     hour = int(dt[8:10])
        #     d = datetime.datetime(year,month,day,hour)
        #     t = cdftime.date2num(d)
        #     self.the_times.append(t)
        # # Jeyavinoth:End

        # above commented out code is replaced by the code below
        the_calendar = 'standard'
        unit_string = 'hours since 1800-1-1 00:00:0.0'
        self.the_times, _, _ = jjCal.get_time_info(unit_string, self.times, calendar=the_calendar)

        # Create the file
        rootgrp = NetCDF.Dataset(self.cdf_file, 'w', format='NETCDF3_CLASSIC')

        # Create dimensions:
        rootgrp.createDimension('lon', len(self.lons))
        rootgrp.createDimension('lat', len(self.lats))
        rootgrp.createDimension('time', None)

        # Create Variables:
        lat = rootgrp.createVariable('lat','f4',('lat',))
        lon = rootgrp.createVariable('lon','f4',('lon',))
        times = rootgrp.createVariable('time','f8',('time',))
        thedata = rootgrp.createVariable('comp','f4',('time','lat','lon',))

        # Attributes:
        lat.units = 'degrees north'
        lat.actual_range = [self.lats[-1],self.lats[0]]
        lat.long_name = "Latitude"

        lon.units = 'degrees east'
        lon.actual_range = [self.lons[-1],self.lons[0]]
        lon.long_name = "Longitude" 

        times.units = 'hours since 1800-1-1 00:00:0.0'
        times.calendar = the_calendar
        times.long_name = "Time"
        times.delta_t = "0000-00-00 06:00:00"
        times.standard_name = "time";
        times.axis = "t";
        times.coordinate_defines = "point";
        times._CoordinateAxisType = "Time";
        times.actual_range = self.the_times[0],self.the_times[-1]; 
         
        # Populate lats
        lat[:] = self.lats

        # Populate lons
        lon[:] = self.lons

        # Populate times
        times[:] = self.the_times

        # Populate data
        thedata[:] = self.z

        # Write to file
        rootgrp.close()

class Read_NetCDF:

    def __init__(self,*args,**kwargs):
        cdf_file = args[0]

        # Open for read
        rootgrp = NetCDF.Dataset(cdf_file, 'r', format='NETCDF3_CLASSIC')
   
        #print rootgrp.dimensions 
        #print rootgrp.variables

        # Extract data
        self.lats = rootgrp.variables["lat"][:]
        self.lons = rootgrp.variables["lon"][:]
        self.thedata = rootgrp.variables["comp"][:]
    
        # Close file
        rootgrp.close()
