import os,sys

def pull_data(NetCDF,numpy,in_path,file_seperator,read_year,
        scale,var_slp,var_time,lat_flip,lon_shift):
    """
       This function takes an input directory (in_path) and finds all 
       the available files to be read. Then the requested file is 
       read and put into a single array.
       
        Options/Arguments:
            NetCDF     -- module.
            numpy      -- module.
            in_path    -- path to the data files.
            read_year  -- year desired.
            scale      -- scales the variable as desired
                          (can be 1.0 to do nothing).
            var_slp    -- variable to be extracted.
            var_time   -- variable for time.
            lat_flip   -- Reverse latitude in arrays.
            lon_shift  -- Force longitude shift so 1st index
                          contains Greenwich Meridian.
        Returns:
           slp   -- numpy array containing data.
           times -- numpy array of time data. 
           the_time_units -- string of time units.

        Examples:

        Author: Mike Bauer  <mbauer@giss.nasa.gov>

        Log:
            2008/01  MB - File created.
            2008/10  MB - Added input checks, docstring.
            2008/10  MB - Fixed error where file_list was unordered...
            2009/11  MB - Updated to version 4.
    """
    verbose = 0

    read_year = int(read_year)

    # Pull the list of available files, put in chronological order.
    file_list = os.listdir(in_path)
    file_list = [x for x in file_list if x.find(".nc") != -1]
    file_list.sort()

    # Loop over available files for correct year.
    found_years = {}
    found_file = ""
    for infile in file_list:
        if infile.find(".nc") != -1:
            #if verbose:
            #    print "Scanning File:",infile
            # This works for filenames like slp.1998.nc
            year = int(infile.split(file_seperator)[1])
            if year == read_year:
                found_file = infile
                break
    if not found_file:
        msg = "WARNING: Cannot file for year %d in directory %s"
        sys.exit(msg % (read_year,in_path))
    #if verbose:
    #    print "\nFound File:",found_file

    # Open file to read, use the netcdf 3 format
    nc_in = NetCDF.Dataset(in_path+found_file,'r',format='NETCDF3_CLASSIC')

    # Pull var_time
    times = nc_in.variables[var_time][:]
    the_time_units = nc_in.variables[var_time].units
    times = times.astype(numpy.float32)
    
    ## See if need to scale or add offset to var_slp
    #if 'add_offset' in nc_in.variables[var_slp].ncattrs():
    #    add_offset = getattr(nc_in.variables[var_slp],'add_offset')
    #    #if verbose:
    #    #    print "add_offset",add_offset
    #else:
    #    add_offset = 0.0

    #if 'scale_factor' in nc_in.variables[var_slp].ncattrs():
    #    scale_factor = getattr(nc_in.variables[var_slp],'scale_factor')
    #    #if verbose:
    #    #    print "scale_factor",scale_factor
    #else:
    #    scale_factor = 1.0

##CUT
    #lat_flip = lon_shift = 0
    #lat_flip = 1; lon_shift = 72

    # Pull slp_var, assume has dimensions of [time,lat,lon]
    #slp = numpy.multiply(
    #        numpy.add(
    #            numpy.array(nc_in.variables[var_slp][:],dtype=numpy.float32,copy=1),add_offset),scale_factor*scale)
    
    # Pull slp_var, assume has dimensions of [time,lat,lon]
    slp = numpy.multiply(numpy.array(nc_in.variables[var_slp][:],dtype=numpy.float32,copy=1),scale)
 
    if lat_flip:
        slp = slp[:,::-1,:]
        #if verbose:
        #    print "Lat Flipped"

    if lon_shift:
        slp = numpy.roll(slp,lon_shift,axis=2)
        #if verbose:
        #    print "Lon Shifted"

    # Close File
    nc_in.close()

    return slp,times,the_time_units

if __name__=='__main__':

    import os,sys
    import time

    def pretty_filesize(bytes,msg=""):
        if bytes >= 1073741824:
            return msg+str(bytes / 1024 / 1024 / 1024) + ' GB'
        elif bytes >= 1048576:
            return msg+str(bytes / 1024 / 1024) + ' MB'
        elif bytes >= 1024:
            return msg+str(bytes / 1024) + ' KB'
        elif bytes < 1024:
            return msg+str(bytes) + ' bytes'

    save_plot = 1

    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Basic standard Python modules to import.
    imports = []
    # Jeyavinoth: removed necdftime from line below
    # system_imports = "import numpy,netcdftime,pickle"
    system_imports = "import numpy,pickle"

    imports.append(system_imports)
    imports.append("import netCDF4 as NetCDF")

    # My modules to import w/ version number appended.
    my_base = ["defs"]
    if save_plot:
        my_base.append("plot_map")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)

    for i in imports:
        exec(i)
    defs_set = {}

    # Fetch definitions and impose those set in defs_set.
    defs = defs.defs(**defs_set)

    shared_path = "/Volumes/scratch/output/nra_files/"

    # Get some definitions. Note must have run setup_vx.py already!
    sf_file = "%ss_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(sf_file, 'rb'))
        inputs = ("im","jm","maxid","lats","lons","timestep","dx","dy","dlon","dlat",
            "start_lat","start_lon","dlon_sq","dlat_sq","two_dlat","model_flag","eq_grid",
            "tropical_n","tropical_s","bot","mid","top","row_start","row_end",
            "tropical_n_alt","tropical_s_alt","bot_alt","top_alt","lon_shift","lat_flip",
            "the_calendar","found_years","super_years","dim_lat","dim_lon","dim_time",
            "var_lat","var_lon","var_time","var_slp","var_topo","var_land_sea_mask",
            "file_seperator","no_topo","no_mask","slp_path","model","out_path",
            "shared_path","lat_edges","lon_edges","land_gridids","troubled_centers") 
        if save_plot:
            lats = fnc_out[inputs.index("lats")]
            lons = fnc_out[inputs.index("lons")]
            model = fnc_out[inputs.index("model")]
        slp_path = fnc_out[inputs.index("slp_path")]
        the_calendar = fnc_out[inputs.index("the_calendar")]
        file_seperator = fnc_out[inputs.index("file_seperator")]
        super_years = fnc_out[inputs.index("super_years")]
        var_slp = fnc_out[inputs.index("var_slp")]
        var_time = fnc_out[inputs.index("var_time")]
        lat_flip = fnc_out[inputs.index("lat_flip")]
        lon_shift = fnc_out[inputs.index("lon_shift")]
        im = fnc_out[inputs.index("im")]
        jm = fnc_out[inputs.index("jm")]

        #(im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
        #        dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
        #        bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
        #        bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
        #        super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
        #        var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
        #        no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
        #        land_gridids,troubled_centers) = fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
    del fnc_out # reduces memory footprint by 83464 bytes
    del pickle

    years = [x for x in range(int(super_years[0]),int(super_years[-1])+1)]

    for loop_year in years:

        loop_year = int(loop_year)

        print ("\n=============%d=============" % (loop_year))

        # Open data file, extract data
        fnc = pull_data(NetCDF,numpy,slp_path,file_seperator,loop_year,
                defs.read_scale,var_slp,var_time,lat_flip,lon_shift)
        (slp,times,the_time_units) = fnc
        del fnc

        msg = "\nMemory Use: "
        print (pretty_filesize(slp.size*slp.itemsize,msg),)
        print (pretty_filesize(times.size*times.itemsize,"& "))
        d = {'slp':slp,'times':times}
        print (numpy.who(d))
        del d

        #print "Memory Usage:"
        #for i in dir():
        #    print type(i)
        #    print "\tObject %s: %s " % (i, pretty_filesize(sys.getsizeof(i)))
        time.sleep(6)
        if loop_year == years[1]:
            import sys; sys.exit("Stop HERE")

        tsteps = len(times)
        the_time_range = [times[0],times[tsteps-1]]
        start = "%s" % (the_time_units)
        tmp = start.split()
        tmp1 = tmp[2].split("-")
        tmp2 = tmp[3].split(":")
        tmp3 = tmp2[2][0]
        start = "%s %s %04d-%02d-%02d %02d:%02d:%02d" % \
                (tmp[0],tmp[1],int(tmp1[0]),int(tmp1[1]),
                 int(tmp1[2]),int(tmp2[0]),int(tmp2[1]),
                 int(tmp3))
        print (start)
        import sys; sys.exit("Stop Here")
        # # Jeyavinoth Start: the code below is commented out till Jeyavinoth: End
        # # seems like this code never gets used, because the code is forced to crash above
        # # right before these lines. 
        # # In anycase I change the code below to use my jj_calendar.py functions
        # # Only date_stamps is getting used anyways
        # cdftime = netcdftime.utime(start,calendar=the_calendar)
        # get_datetime = cdftime.num2date
        # dtimes = (get_datetime(times[step]) for step in range(0,tsteps))
        # date_stamps = ["%4d%02d%02d%02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]
        # # Jeyavinoth: End
        _, date_stamps, _ = jjCal.get_time_info(start, times, calendar=the_calendar)
        del times
        del dtimes

        print ("Start %s and End %s" % (date_stamps[0],date_stamps[-1]))

        if save_plot:
            # Plot an example to see if okay.
            plot = plot_map.plotmap(clevs=[960,1040,2],cints=[960.0,1040.0],color_scheme="jet")
            for step in range(tsteps):
                msg = "State at %4d %s %02d %02d UTC" % (int(date_stamps[step][:4]),
                                                                 months[int(date_stamps[step][4:6])],
                                                                 int(date_stamps[step][6:8]),
                                                                 int(date_stamps[step][8:]))
                pname = "%s%s_example_slp_%s.pdf" % (shared_path,model,date_stamps[step])
                plot.create_fig()
                slp_step = slp[step,:,:].copy()
                slp_step.shape = jm*im
#            plot.add_field(lons,lats,slp_step,ptype='pcolor')
                plot.add_field(lons,lats,slp_step,ptype='contour')
                plot.finish(pname,title=msg)
                print ("\tMade figure: %s" % (pname))
                #continue # Exit early from this year
                sys.exit("Stopped Early.")
        del slp

