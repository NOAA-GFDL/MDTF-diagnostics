"""
Finds the attributed grids for each center/track.
#!/usr/bin/env python -tt

Usage:

Options:

Examples:

Notes: This should work with any standard installation of python version
       2.4 or greater. I have tested it on Apple OS-X (10.5), Ubuntu (8.04)
       and RedHat Enterprise 4.0 Linux distributions.
       See bottom of this document for extra notes.

Memory Use: Depending on resolution and options expect at least 300MB per
            instance.

Run Time: With the NCEP Reanalysis I get about 2 timesteps per minute per
          instance. Thus a year takes roughly 12 hours. This is on a
          Mac Pro with 2.26 GHz processors, 12 GB of RAM, and a 3 disk RAID.

Author: Mike Bauer  <mbauer@giss.nasa.gov>

Log:
    2006/12 MB - File created.
    2009/5  MB - Updated to v3.
    2009/9  MB - Added zonal mean screen.
    2009/10 MB - Fixed bug where object pointer miss applied.
    2009/11 MB - Updated to v4.
"""
import sys, os

def main(centers_file, defs_set, imports, pick, over_write_out_path,
            shared_path, over_write_slp_path, loop_year, exit_on_error,
               plot_on_error, plot_every, ReDo_List, use_dumped, skip_save,
               use_zmean, use_grad ,speedometer, import_read):

    import sys

    # Diagnostic: comment out more maximum speed, use verbose flag to
    # enable or disable output while debugging.
    verbose = 0

    #print "\tSetting up....",
    # --------------------------------------------------------------------------
    # Setup Section
    # --------------------------------------------------------------------------
    for i in imports:
        exec(i)

    ## Works with multiprocessing
    msg= '\t\tStarting year %d with child process id: %s'
    print msg % (loop_year,os.getpid())

    # Fetch definitions.
    defs = defs.defs(**defs_set)

    # For unwinding reads
    ids = {'YYYY' : 0,'MM' : 1, 'DD' : 2, 'HH' : 3, 'JD' : 4,
           'CoLat' : 5, 'Lon' : 6, 'GridID': 7, 'GridSLP' : 8,
           'RegSLP' : 9, 'GridLAP' : 10, 'Flags' : 11, 'Intensity' : 12,
           'Disimularity' : 13, 'UCI' : 14, 'USI' : 15}
    jd_id = ids['JD']
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}
    mm2season = { 1  : 0, 2  : 0, 3  : 1,
                  4  : 1, 5  : 1, 6  : 2,
                  7  : 2, 8  : 2, 9  : 3,
                  10 : 3, 11 : 3, 12 : 0}
    # NDJFMA and MJJASO
    mm2season = { 1  : 0, 2  : 0, 3  : 0,
                  4  : 0, 5  : 1, 6  : 1,
                  7  : 1, 8  : 1, 9  : 1,
                  10 : 1, 11 : 0, 12 : 0}

    # Pre-bind for speed
    N_array = numpy.array; N_append = numpy.append
    N_less_equal = numpy.less_equal; N_greater_equal = numpy.greater_equal
    N_less = numpy.less; N_int = numpy.int; N_Subtract = numpy.subtract
    N_multiply = numpy.multiply; N_sort = numpy.sort
    N_take = numpy.take; N_alen = numpy.alen; N_average = numpy.average
    N_compress = numpy.compress; twopier = 2.0*math.pi*defs.earth_radius
    N_Mean = numpy.mean; N_Median = numpy.median; N_Zeros = numpy.zeros
    N_grad = numpy.gradient; N_atan = numpy.arctan
    N_sqr = numpy.sqrt; N_add = numpy.add; N_greater = numpy.greater
    N_divide = numpy.divide
    inv_wn = 1.0/float(defs.wavenumber); cos = math.cos
    radians = math.radians
    intersection = set.intersection
    try_bridge = try_bridge.try_bridge
    bridge = bridge.bridge
    scan_contour = scan_contour.scan_contour
    collapse = collapse.collapse
    fill_holes = fill_holes.fill_holes
    find_problematic = find_problematic.find_problematic
    check_overlap = check_overlap.check_overlap
    find_empty_centers = find_empty_centers.find_empty_centers
    clean_bridge = clean_bridge.clean_bridge
    terminal_to_file = att_2_file.terminal_to_file
    att_2_file = att_2_file.att_2_file
    envelope_test = envelope_test.envelope_test
    make_unique_name = make_unique_name.make_unique_name
    scan_center = scan_center.scan_center
    strip_read = strip_read.strip_read
    print_col = print_col.print_col
    flatten = flatten.flatten
    defs_inflated = defs.inflated
    defs_check_inflate = defs.check_inflate
    defs_interval = defs.interval
    defs_check_flare = defs.check_flare
    defs_accuracy = defs.accuracy
    defs_inv_earth_radius_sq = defs.inv_earth_radius_sq
    defs_two_deg_lat = defs.two_deg_lat
    defs_skip_polars  = defs.skip_polars

    # Stats of how often a filter is called
    filters = ["Inner Loop Calls","Hill Test Calls","Inflation Test Calls","Wander Test Calls"]
    filter_count = [0] * len(filters)

    if plot_on_error or plot_every:
        Plot_Map = plot_map.plotmap
        PPlot_Map = plot_map.plotmap_polar
        error_plot = error_plot.error_plot
        # Instantiate matplotlib
        plot = Plot_Map(clevs=[980,1020,2],cints=[960.0,1013.0])

    if use_dumped:
        known_flags = {0 : "Passed all filters",
                       1 : "Failed concavity/Laplacian filter",
                       2 : "Failed regional minimum filter",
                       3 : "Failed critical radius filter",
                       4 : "Failed troubled center filter",
                       5 : "Failed trackable center",
                       6 : "Failed track lifetime filter",
                       7 : "Failed track travel filter",
                       8 : "Failed track minimum SLP filter",
                       9 : "Failed polar screen",
                       10: "Failed extratropical track filter"}
        flag_colors = { 0 : "black",
                        1 : "blue",
                        2 : "yellow",
                        3 : "green",
                        4 : "red",
                        5 : "white",
                        6 : "magenta",
                        7 : "cyan",
                        8 : "#A1F4BB", #teal
                        9 : "#FEDCBA", #wheat
                        10 : "#FF9900" # orange
                        }

    # Get some definitions. Note must have run setup_vx.py already!
    sf_file = "%ss_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(sf_file, 'rb'))
        (im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
                dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
                bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
                bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
                super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
                var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
                no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
                land_gridids,troubled_centers,faux_grids) = fnc_out
        # Save memory
        if not defs.troubled_filter:
            del troubled_centers
        del land_gridids
        del lat_edges
        del lon_edges
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))

    # Update over_write values
    if over_write_slp_path:
        slp_path = over_write_slp_path
    if over_write_out_path:
        out_path = over_write_out_path

    # Equatorial zone's last grid
    eq_end = row_end[eq_grid]
    # Timestep in julian days
    delta_jdate = int(((timestep/24.0)*100))
    inv_accuracy = 1.0/defs_accuracy
    index_array = numpy.arange(im*jm) # list of gridIDs
    row_start_index = row_start.index
    half_way = im/2
    # Comparisons of dictionary membership much faster than list
    if defs.troubled_filter:
        trouble_grids = dict( (x,1) for x in troubled_centers)
        del troubled_centers
    if defs.keep_log:
        # Redirect stdout to file instead of screen (i.e. logfiles)
        tmp = "%s/logfile" % (out_path)
        lfile = make_unique_name(os,tmp,".txt")
        screenout  = sys.stdout
        log_file   = open(lfile, 'w')
        sys.stdout = log_file

    # Import a bunch of model grid specific information
    #   Note must have run setup_vx.py already!
    fnc_out = []
    fnc_out = pickle.load(open("%scf_dat.p" % (shared_path), 'rb'))
    (use_all_lons,search_radius,regional_nys,gdict,rdict,ldict,ijdict,
     min_centers_per_tstep,max_centers_per_tstep,max_centers_per_tstep_change,
     lapp_cutoff,hpg_cutoff) = fnc_out
    del use_all_lons,search_radius,regional_nys,gdict,rdict
    del fnc_out

    # Fetch attribute specific info.
    af_file = "%saf_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(af_file, 'rb'))
        (darea,distance_lookup,angle_lookup,
                close_by,wander_test,gdict,neighbor_test) = fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (af_file))
    del fnc_out

    # Predefine a set of contours.
    base_contours = {}
    base_contours = range(defs.min_contour,defs.max_contour+defs_interval,
                          defs_interval)

    # Predefined data storage
    center_data_type = numpy.dtype(defs.center_data)

    # Quit on error else just send message to logfile?
    if exit_on_error:
        do_this = 'print smsg; print msg; sys.exit("\t\tDate_Stamp:"+date_stamp)'
    else:
        do_this = 'print smsg; print msg; print "\t\tDate_Stamp:"+date_stamp'

    # Set flags to warn of too many or too few atts
    extra_tropical_grid_cnt =  bot_alt+maxid-top_alt
    att_min_cnt = int(extra_tropical_grid_cnt*0.01) # 1% of all grids
    att_max_cnt = int(extra_tropical_grid_cnt*0.30) # 30% of all grids

    # File with list of date_stamps for which errors occurred... use with ReDo_List
    if not skip_save:
        tmp = "%sredos" % (out_path)
        redo_out = make_unique_name(os,tmp,".txt")
        redo_save = open(redo_out,"w")

##CUT
    # Tmp info_out file for storing info... to make histograms or other diagnostic
    # normally commented out.
    #if not skip_save:
    #    tmp = "%s/info" % (out_path)
    #    info_out = make_unique_name(os,tmp,".txt")
    #    info_save = open(info_out,"w")

    # Define some files
    header = "mcms_%s_%04d_" % (model,loop_year)
    c_file = "%s%s%s" % (out_path,header,centers_file)

    # Read center file
    #print c_file
    read_file = open(c_file,"r")
    centers = []
    centers_append = centers.append
    for line in read_file:
        fnc = strip_read(line)
        centers_append(fnc)
    read_file.close()

    # Speed things up A LOT by making a sorted list of centers
    # and shrinking it as we find centers.
    centers.sort()
    centers.reverse()

    total_centers = len(centers)
    print "\tCenters Read",total_centers

    if use_dumped:
        dumped_file = c_file.replace("tracks","dumped_centers")
        dumped_read = open(dumped_file,"r")
        dumped_centers = []
        dumped_centers_append = dumped_centers.append
        for line in dumped_read:
            fnc = strip_read(line)
            dumped_centers_append(fnc)
        dumped_read.close()
        # Speed things up A LOT by making a sorted list of centers
        # and shrinking it as we find centers.
        dumped_centers.sort()
        dumped_centers.reverse()
        #print "\tDumped Centers Read",len(dumped_centers)

    # Get unique dates from centers file
    alldates = sorted(dict( (x,1) for x in [x[4] for x in centers]).keys())
    nsteps = len(alldates)
    date_stamps = sorted(dict( (x,1) for x in ["%4d%02d%02d%02d" % (x[0],x[1],x[2],x[3])  for x in centers]).keys())
    print "\tNumber of unique dates/times:",nsteps

    redo_check = []
    if ReDo_List:
        redo_check = [x for x in date_stamps if x in ReDo_List]
        if redo_check:
            pass
            #print "\tThere are Redos to Do!"
        else:
            return "No Redos to Do here."

    #print "\tStart Attribute Search...."
    # -------------------------------------------------------------------------
    # Pull in reference field
    # -------------------------------------------------------------------------

    if not skip_save:
        # Open data file to save results
        att_file = c_file.replace("tracks","att")
        if ReDo_List:
            # Make special case
            att_file =  c_file.replace(".txt","")
            att_file = make_unique_name(os,att_file,".txt")
        att_save = open(att_file,"w")

    # Open data file, extract data
    exec(import_read)
    fnc = pull_data.pull_data(NetCDF,numpy,slp_path,file_seperator,loop_year,
            defs.read_scale,var_slp,var_time,lat_flip,lon_shift)
    (slp,times,the_time_units) = fnc
    del fnc

    # Work with the time dimension a bit.
    # This is set in setup_vX.py
    jd_fake = 0
    if the_calendar != 'standard':
        # As no calendar detected assume non-standard
        jd_fake = 1
      elif the_calendar != 'proleptic_gregorian':
        jd_fake = False

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
    # Warning this could get weird for non-standard
    # calendars if not set correctly (say to noleap)
    # in setup_vX.py
    cdftime = netcdftime.utime(start,calendar=the_calendar)
    get_datetime = cdftime.num2date
    dtimes = [get_datetime(times[step]) for step in range(0,tsteps)]

    # Get Julian Days.. unless GCM uses non-standard calendar in which case
    #  enumerate with timestep and use uci_stamps for datetime things.
    if jd_fake:
        # Use timesteps rather than dates
        # examples '000000000', '000000001'
        adates = ["%09d" % (x) for x in range(tsteps)]
    else:
        # Using regular date/times
        # examples 244460562, 244971850i
        date2jd = netcdftime.JulianDayFromDate
        adates = [int(100*date2jd(x,calendar='standard')) for x in dtimes]
    uci_starters = ['%4d%02d%02d%02d' % (d.year,d.month,d.day,d.hour) for d in dtimes]
    date_stamps1 = ["%4d%02d%02d%02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]

    # Check that dates from centers file match the datafile
    if date_stamps != date_stamps1:
        print len(date_stamps),len(date_stamps1)
        print  [x for x in date_stamps if x not in date_stamps1]
        print "dd"
        print  [x for x in date_stamps1 if x not in date_stamps]
        sys.exit("Warning: date_stamp difference.")

    if speedometer:
        # Optional: Here I copy the 1st tstep to all the others so that
        # every tstep should take the same amount of time....
        print "\n\nWARNING COPY only 1st step!!!\n\n"
        # SEE ALSO A trim to current_centers!!!!
        slp1 = slp[0,:,:]
        for step in range(0,tsteps):
            slp[step,:,:] = slp1

    if use_zmean:
        # Note that this results in 53 weeks so I make the
        # last week of the year fuse with the second to last
        # making that a 8 or 9 days week.
        slp_weeks = [int(d.strftime("%W")) - (0,1)[int(d.strftime("%W")) > 52] for d in dtimes]
        # for 2 week sample convert every even one to the previous odd value
        slp_weeks = [ x - (1,0)[x % 2] for x in slp_weeks]
        week_cnt = dict.fromkeys([x for x in slp_weeks],1)
        the_zmean = N_Zeros((len(week_cnt),jm),dtype=numpy.float)
        # Find the weekly zonal mean
        #for week in range(slp_weeks[0],slp_weeks[-1]+1):
        iweek = 0
        for week in week_cnt:
            this_week = [step for step in range(0,nsteps) if slp_weeks[step] == week]
            # Find the zonal average of the weekly mean maps
            #this_sum = N_Mean(slp[this_week[0]:this_week[-1]+1,:,:],2)
            #the_zmean[week-1,:] = N_Mean(this_sum,0)
            this_sum = N_Median(slp[this_week[0]:this_week[-1]+1,:,:],2)
            the_zmean[iweek,:] = N_Median(this_sum,0)
            iweek += 1

        # Create the anomaly array
        zanom = N_Zeros((tsteps,jm,im),dtype=numpy.float)
        wkeys = week_cnt.keys()
        # Create the anomaly
        for step in range(0,tsteps):
            for j in range(jm):
                #zanom[step,j,:] = N_Subtract(slp[step,j,:],the_zmean[slp_weeks[step]-1,j])
                zanom[step,j,:] = N_Subtract(slp[step,j,:],the_zmean[wkeys.index(slp_weeks[step]),j])

    # Force some memory free
    del times
    del dtimes
    del date_stamps1
    del cdftime
    del get_datetime

    if use_grad:
        """Provide tests to Laplacian filter
        Laplacian
        LAP_P = (d^2P/dx^2 + d^2P/dy^2) in spherical coordinates (radians)
              = 1/a^2 * d^2P/dlat^2 + 1/a^2sin^2(lat) * d^2P/dlon^2
                + cot(lat)/a^2 * dP/dlat

        Scaled to (deg lat)^2 by altering km^2 and fixed km per deg
        latitude = 111.0

        Centered finite differences:
           d^2P/dlon^2 = ( P(lon+1) - 2*P(lon) + P(lon-1) ) / dlon**2
           dP/dlon     = ( P(lon+1) - P(lon-1) ) / 2*dlon

        1) Laplacian measures degree of curvature in local SLP field
        (proportional to local geostrophic relative vorticty).

        * Tends to be large and positive at the bottom of depressions,
        and large and negative on top of domes
        * Relative vorticity is positive in areas of low heights
        (troughs), low in areas of high heights (ridges)

        Similar to Zhang etal 2004 the averaged SLP of the 8 surrounding
        points of a center are used where each of these 8 surrounding
        points is the average SLP of their 8 surrounding points.
        """
        lap = N_Zeros((tsteps,jm*im),dtype=numpy.float)
        for step in range(0,tsteps):

            ## Take gradient of the local SLP field
            #slp_tmp = N_array(slp[step,:,:])
            ## Note grad[0] xdir, grad[0] ydir
            #grad = N_grad(slp_tmp)

            ## The magnitude of the gradient
            ## See the Sobel operator for edge detection
            #mag = N_sqr(N_add(N_multiply(grad[0],grad[0]),N_multiply(grad[1],grad[1])))

            ## Direction of the gradient tan-1(Gy/Gx) clockwise from north
            #sign = 180.0 - N_atan(N_divide(grad[1],grad[0]))+N_multiply(90.0,N_divide(grad[0],N_sqr(N_multiply(grad[0],grad[0]))))

            slp_step = slp[step,:,:].copy()
            slp_step.shape = im*jm
            for gridid in range(maxid):
                if ldict[gridid][0]: # non-polar (90 degrees)

                    # Find 9-pnt average SLP for each of the 9-pnts around center.
                    all_nine = gdict[gridid][:]
                    nine_pnt_aves = []

                    # If using local nine raw
                    nine_pnt_aves = (N_take(slp_step,all_nine))

                    #nine_pnt_aves_append = nine_pnt_aves.append # prebind for speedup
                    #for eachone in all_nine:
                    #    nine_pnt_aves_append(N_average(N_take(
                    #        slp_step,gdict[eachone][:])))

                    # 1/a^2sin^2(lat) * d^2P/dlon^2
                    termA = ldict[gridid][1] * (nine_pnt_aves[3] -
                                                2.0*nine_pnt_aves[4] +
                                                nine_pnt_aves[5]) / dlon_sq
                    # 1/a^2 * d^2P/dlat^2
                    termB = defs_inv_earth_radius_sq * ((nine_pnt_aves[1] -
                                                         2.0*nine_pnt_aves[4] +
                                                         nine_pnt_aves[7])/
                                                        dlat_sq)
                    # cot(lat)/a^2 * dP/dlat
                    termC = ldict[gridid][2] * (nine_pnt_aves[1] -
                                                nine_pnt_aves[7]) / two_dlat

                    #lap[step,gridid] = defs_two_deg_lat*(termA + termB + termC) # hPa/lat^2
                    tmp = defs_two_deg_lat*(termA + termB + termC) # hPa/lat^2
                    lap[step,gridid] = N_sqr(N_multiply(tmp,tmp))


            lap_step = lap[step,:]
            grad_cut = 2.0
            #zgrids = N_compress(N_less(lap_step,grad_cut),index_array)
            zgrids = N_compress(N_greater(lap_step,grad_cut),index_array)
            zgrids = zgrids.tolist()
            #plota = Plot_Map(clevs=[-10,grad_,1],cints=[-10.0,grad_cut])
            plota = Plot_Map(clevs=[980,1020,2],cints=[960.0,1013.0])
            c_loc = []
            for c in zgrids:
                c_loc.append((ijdict[c][2],ijdict[c][3]))
            tmp = "SLP Gradient (%d hPa)\n%4d %s %02d %02d UTC"
            msg1 = tmp % (int(grad_cut),int(date_stamps[step][:4]),
                          months[int(date_stamps[step][4:6])],
                          int(date_stamps[step][6:8]),
                          int(date_stamps[step][8:]))
            mout = error_plot("%sfigs/pgrad_%s.png" % (out_path,uci_starters[step]),
                              plota,slp_step,lons,lats,[],c_loc,[],[],[],msg1)
            del plota
            #sys.exit("Stop HERE")

            ## plota = Plot_Map(clevs=[-50,-5,5],cints=[-50.0,-5.0]
            ##plota = Plot_Map()
            ## plota = Plot_Map(cints=[180.0,360.0])
            #plota = Plot_Map(cints=[-5.0,0.0])
            ##  c_loc = []
            ##   for c in zgrids:
            ##       c_loc.append((ijdict[c][2],ijdict[c][3]))
            #tmp = "Local SLP Gradient\n%4d %s %02d %02d UTC"
            #msg1 = tmp % (int(date_stamps[step][:4]),
            #              months[int(date_stamps[step][4:6])],
            #              int(date_stamps[step][6:8]),
            #              int(date_stamps[step][8:]))
            #mout = error_plot("%sfigs/pgrad_%s.png" % (out_path,uci_starters[step]),

            #                  plota,lap[step,:],lons,lats,[],[],[],[],[],msg1)
            #sys.exit("Stop HERE")

    if not skip_save:
        # Open file for progress
        prog_file = att_file.replace("att","progress")
        # Open with a buffer size of zero to make updates rapid
        prog_save = open(prog_file,"w",0)
        # List tsteps in progress file.
        prog_save.write("%d\n" % (tsteps))

    if speedometer:
        speed_file = c_file.replace("tracks","speed")
        speed_save = open(speed_file,"w",0)

    used_step = 0
    centers_used = 0
    centers_skipped = 0
    last_center = []
    last_dumped_center = []
    short_skip = 0

##CUT
    tsteps = 4*2
    short_skip = 1

    # ------------------------------------------------------------------------
    # Big Loop over YEAR
    # ------------------------------------------------------------------------
    for step in range(0,tsteps):

        if speedometer:
            # Get current time
            time1 = time.clock()
            # only due 1st month
            if step > 30:
                break

        if not skip_save:
            # Update progress file
            prog_save.write("%d\n" % (step))
        adate = adates[step]
        current_centers = N_array([], dtype=center_data_type)
        found_none = 1
        polar_centers = []
        while centers:
            # See if overflow from last read useful or read new record
            if last_center:
                center = last_center
                last_center = []
            else:
                center = centers.pop()
            # Store if center falls on wanted date.
            if center[jd_id] == adate:
                unpacked = N_array([(center[0],center[1],center[2],
                                center[3],center[4],center[5],
                                center[6],center[7],center[8],
                                center[9],center[10],center[11],
                                center[12],center[13],
                                center[14],center[15])],
                              dtype=center_data_type)
                # Skip centers in polar-most lat rows
                if defs_skip_polars:
                    if im <= unpacked['GridID'] < maxid-im:
                        current_centers = N_append(current_centers,unpacked)
                    else:
                        centers_skipped += 1
                        # These are stored as empty centers below
                        polar_centers.append((center[0],center[1],center[2],
                                center[3],center[4],center[5],
                                center[6],center[7],center[8],
                                center[9],center[10],center[11],
                                center[12],center[13],
                                center[14],center[15]))
                else:
                    current_centers = N_append(current_centers,unpacked)
                found_none = 0
            else:
                # Store for next time
                last_center = center
                break
        centers_used += len(current_centers)
        if use_dumped:
            # Read in current dumped centers too
            current_dumped_centers = N_array([], dtype=center_data_type)
            found_none_dumped = 1
            while dumped_centers:
                # See if overflow from last read useful or read new record
                if last_dumped_center:
                    dumped_center = last_dumped_center
                    last_dumped_center = []
                else:
                    dumped_center = dumped_centers.pop()

                # Store if center falls on wanted date.
                if dumped_center[jd_id] == adate:
                    unpacked = N_array([(dumped_center[0],dumped_center[1],dumped_center[2],
                                         dumped_center[3],dumped_center[4],dumped_center[5],
                                         dumped_center[6],dumped_center[7],dumped_center[8],
                                         dumped_center[9],dumped_center[10],dumped_center[11],
                                         dumped_center[12],dumped_center[13],
                                         dumped_center[14],dumped_center[15])],
                                       dtype=center_data_type)
                    # Skip centers in polar-most lat rows
                    if defs_skip_polars:
                        if im <= unpacked['GridID'] < maxid-im:
                            current_dumped_centers = N_append(current_dumped_centers,unpacked)
                    else:
                        current_dumped_centers = N_append(current_dumped_centers,unpacked)
                    found_none = 0
                else:
                    # Store for next time
                    last_dumped_center = dumped_center
                    break
        if speedometer:
            # Optional: Here I copy the 1st tstep to all the others so that
            # every tstep should take the same amount of time....
            if step == 0:
                cc = current_centers
            else:
                current_centers = cc

        # See if special request
        if ReDo_List:
            if date_stamps[step] not in redo_check:
                centers_used -= len(current_centers)
                centers_skipped -= len(polar_centers)
                continue

        ## Diagnostic
        #if verbose:
        #    msg = "\t\tFound %d Centers at Step %s  (Current %d and Skipped %d Centers)"
        #    print msg % (len(current_centers)+len(polar_centers),uci_starters[step],
        #            len(current_centers),len(polar_centers))
        
        ## Get field, make 1d integer array (0.1 hPa) to allow for exact
        ## comparisons and some reasonable idea of significant digits.
        slp_step = N_multiply(slp[step,:,:].copy(),defs_accuracy)
        slp_step.shape = im*jm
        slp_step = slp_step.astype(N_int)
        if use_zmean:
            zanom_step = zamon[step,:]

        ## If searching for high pressure reverse pressure field so
        ## that highs are lows.
        #if defs.find_highs:
        #    slp_step = slp_step*-1

        # Check that something to look at.
        if len(current_centers) < 1:
            err_num = 1
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: No initial centers for this timestep." % (err_num)
            msg = "\t\tlen(current_centers): %d" % (len(current_centers))
            if plot_on_error:
                tmp = "Fail Check %d: No initial centers for %4d %s %02d %02d UTC"
                msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                              months[int(date_stamps[step][4:6])],
                              int(date_stamps[step][6:8]),
                              int(date_stamps[step][8:]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[],
                                  [],[],[],[],msg1)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        # Set aside centers with central SLPs of less than defs.keep_slp
        # This is done because weak centers are difficult to deal with
        # and not main source of "storminess"....
        empty_skipped = {}
        #for c in current_centers:
        #    if c['GridSLP'] > defs.keep_slp:
        #        empty_skipped[c['GridID']] = 1

###WARNING For Debugging only!!!!!
#        ## A way of only allowing certain centers in a diagnostic run.
#        #cccc = N_array([], dtype=center_data_type)
#        #keepers = [2405,2109]
#        #for each in current_centers:
#        #    if each['GridID'] in keepers:
#        #        cccc = N_append(cccc,each)
#        #    print "\n%s\n\n\n%s\n\n\n%s" % (80*"*","WARNING KEEPERS LIMITING RUN!",80*"*")
#        #    current_centers = cccc

        # ID all centers/tracks found at this datetime
        # Nested dictionary that holds results; keyed by center gridID
        center_slices = {}.fromkeys(current_centers['GridID'],{})

        # Sweep for all grids that fall into each contour. This is sort
        # of like a CAT scan where 'slices' of the field show only grids
        # that fall within a particular contour.
        contours = {}

        if use_grad:
            lap_step = lap[step,:]
            zgrids = N_compress(N_less(lap_step,-2.0),index_array)
            zgrids = zgrids.tolist()
            plota = Plot_Map(clevs=[-10,-2,1],cints=[-10.0,-2.0])
            c_loc = []
            for c in zgrids:
                c_loc.append((ijdict[c][2],ijdict[c][3]))
            tmp = "SLP Gradient (%d hPa)\n%4d %s %02d %02d UTC"
            msg1 = tmp % (int(defs.z_anomaly_cutoff*0.001),int(date_stamps[step][:4]),
                          months[int(date_stamps[step][4:6])],
                          int(date_stamps[step][6:8]),
                          int(date_stamps[step][8:]))
            mout = error_plot("%sfigs/pgrad_%s.png" % (out_path,uci_starters[step]),
                              plota,lap_step[:],lons,lats,c_loc,[],[],[],[],msg1)
            del plota
            #sys.exit("Stop HERE")
            continue


        if use_zmean:
            # Limit searches to only grids that host zonal anomalies
            # of equal or lesser value than defs.z_anomaly_cutoff

            ## if by season
            #if mm2season[int(zmonths[step])]:
            #    # NH Warm, SH Cold
            #        nht = int(defs.z_anomaly_cutoff*0.5)
            #        sht = defs.z_anomaly_cutoff
            #    else:
            #        sht = int(defs.z_anomaly_cutoff*0.5)
            #        nht = defs.z_anomaly_cutoff

            zgrids = N_compress(N_less(zanom_step,defs.z_anomaly_cutoff),index_array)
            zgrids = zgrids.tolist()

            #plota = Plot_Map(clevs=[-50,-5,5],cints=[-50.0,-5.0])
            #c_loc = []
            #for c in zgrids:
            #    c_loc.append((ijdict[c][2],ijdict[c][3]))
            #tmp = "Zonal Anomaly (%d hPa)\n%4d %s %02d %02d UTC"
            #msg1 = tmp % (int(defs.z_anomaly_cutoff*0.001),int(date_stamps[step][:4]),
            #              months[int(date_stamps[step][4:6])],
            #              int(date_stamps[step][6:8]),
            #              int(date_stamps[step][8:]))
            #mout = error_plot("%sfigs/zanom_%s.png" % (out_path,uci_starters[step]),
            #                  plota,N_multiply(zanom_step[:],inv_accuracy),lons,lats,c_loc,
            #                  [],[],[],[],msg1)
            #sys.exit("Stop HERE")
            #continue

        for contour in base_contours:
            if contour == base_contours[0]:
                tmp = N_compress(N_less(slp_step,contour+defs_interval),
                                 index_array)
            elif contour == base_contours[-1]:
                tmp = N_compress(N_greater_equal(slp_step,contour),index_array)
            else:
                tmp = N_compress(N_greater_equal(slp_step,contour) &
                                 N_less(slp_step,contour+defs_interval),
                                 index_array)
            if len(tmp):
                contours[contour] = tmp.tolist()
                ## change gridmax
                #if use_zmean:
                #    tmp = [x for x in tmp.tolist() if x in zgrids]
                #    if tmp:
                #        contours[contour] = tmp
                #else:
                #    contours[contour] = tmp.tolist()
        current_contours = N_array(contours.keys())
        current_contours = N_sort(current_contours)

        gridmax = maxid
        #if use_zmean:
        #    gridmax = len(zgrids)
        #else:
        #    gridmax = maxid

        # Check that something to look at.
        if len(current_contours) < 1:
            err_num = 2
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: No initial contours for this timestep." % (err_num)
            msg = "\t\tlen(current_contours): %d" % (len(current_contours))
            if plot_on_error:
                tmp = "Fail Check %d: No initial contours for %4d %s %02d %02d UTC"
                msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                              months[int(date_stamps[step][4:6])],
                              int(date_stamps[step][6:8]),
                              int(date_stamps[step][8:]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[],
                                  [],[],[],msg1)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        # Test contours should contain all maxID grids
        total_grids = N_array([], dtype=int)
        for each in current_contours:
            total_grids = N_append(total_grids,contours[each])
        total_grids = N_alen(total_grids)
        if total_grids != gridmax:
            err_num = 3
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: Initial contours skip grids for this timestep." % (err_num)
            msg = "\t\ttotal_grids: %d" % (total_grids)
            seen = []
            # See if duplicate is the problem
            for each in current_contours:
                a = contours[each]
                dupe = intersection(set(a),set(seen))
                if dupe:
                    print "Duplicate Found",dupe,"for contour",each,"grid SLP",slp_step[each]
                else:
                    print "No Duplicate for contour",each
                seen.extend(a)
            if plot_on_error:
                tmp = "Fail Check %d: Initial contours skip grids for %4d %s %02d %02d UTC"
                msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                              months[int(date_stamps[step][4:6])],
                              int(date_stamps[step][6:8]),
                              int(date_stamps[step][8:]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[],
                                  [],[],[],[],msg1)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        # Test for bridge situations, see function for why.
        args = (bridge,contours,current_contours,base_contours,slp_step,
                defs_interval,gdict)
        try_bridge(*args)

        # Scan SLP field in slices, defined by current_contours, to
        # see if any current_center falls in that contour, or the
        # last contour returned from a center neighbors.
        center_active = {}.fromkeys(current_centers['GridID'],0)

        # Fetch some info for each center in current_centers.
        r_s = {}
        w_s = {}
        n_s = {}
        neighbors = {}
        offsets = {}
        for center in current_centers:
            # Pre-bind
            center_gridid = center['GridID']
            # Find row for the location
            row_guess = [x for x in row_start
                         if x <= center_gridid]
            row_guess = row_start_index(row_guess[-1])

            # Find the correct longitude offset from row_start
            lon_offset = center_gridid - row_start[row_guess]

            # For shifting everything to central longitude and equator. Easy way
            # to deal with contours that span the edges of the model grid.
            lat_offset = row_guess - eq_grid
            lon_offset2 = center_gridid - (row_start[row_guess]+im/2)
            offsets[center_gridid] = (im*lat_offset) + lon_offset2

            # Get regional screen for center's row
            if lon_offset != 0:
                # Need to shift by lon.
                regional_screen = []
                for i in close_by[row_guess]:
                    shifted = i + lon_offset
                    # Deal with wrap around
                    row_guess_pnt = [x for x in row_start if x <= i]
                    row_guess_pnt = row_start_index(row_guess_pnt[-1])
                    if shifted > row_end[row_guess_pnt]:
                        shifted = shifted - im
                    regional_screen.append(shifted)
                wander_screen = []
                for i in wander_test[row_guess]:
                    shifted = i + lon_offset
                    # Deal with wrap around
                    row_guess_pnt = [x for x in row_start if x <= i]
                    row_guess_pnt = row_start_index(row_guess_pnt[-1])
                    if shifted > row_end[row_guess_pnt]:
                        shifted = shifted - im
                    wander_screen.append(shifted)
                neighbor_screen = []
                for i in neighbor_test[row_guess]:
                    shifted = i + lon_offset
                    # Deal with wrap around
                    row_guess_pnt = [x for x in row_start if x <= i]
                    row_guess_pnt = row_start_index(row_guess_pnt[-1])
                    if shifted > row_end[row_guess_pnt]:
                        shifted = shifted - im
                    neighbor_screen.append(shifted)
            else:
                # Need copy [:] so mod of w_s not applied to wander_test.
                regional_screen = close_by[row_guess][:]
                wander_screen = wander_test[row_guess][:]
                neighbor_screen = neighbor_test[row_guess][:]

            # Store for recall
            r_s[center_gridid] = regional_screen
            w_s[center_gridid] = wander_screen
            n_s[center_gridid] = neighbor_screen

            # List of all current_centers within wander_screen range
            # of the current center.
            n = [x['GridID'] for x in current_centers if x['GridID'] in wander_screen]
            neighbors[center_gridid] = [x for x in n if x != center_gridid]

        ## Diagnostic
        #if verbose:
        #    msg = "\t\tCenterID %d -> row_guess %d lon_offset %d"
        #    print msg % (center_gridid,row_guess,lon_offset)
        #    print "\t\tNeighbors:"
        #    print_col(the_list=neighbors[center_gridid],indent_tag="\t\t\t",
        #              fmt="%6d",cols=6,width=10)

        # As pre-caution append wander_screen for all
        # neighbors to allow for large cyclone families.
        for center in current_centers:
            center_gridid = center['GridID']
            for near in neighbors[center_gridid]:
                # Update wander_screen.
                old = w_s[center_gridid]
                old.extend(n_s[near])
                w_s[center_gridid] = old
        ## Plots
        #for center in current_centers:
        #    # Pre-bind
        #    center_gridid = center['GridID']
        #    # Make plot neighbor_screen for this center
        #    a_loc = []
        #    s_loc = []
        #    e_loc = []
        #    for c in neighbors[center_gridid]:
        #        e_loc.append((ijdict[c][2],ijdict[c][3]))
        #        for a in n_s[c]:
        #             s_loc.append((ijdict[a][2],ijdict[a][3]))
        #    for a in w_s[center_gridid]:
        #        a_loc.append((ijdict[a][2],ijdict[a][3]))
        #    msg = "Neighbor Screen for Center %d at %4d %s %02d %02d UTC" % (center_gridid,int(date_stamps[step][:4]),
        #    months[int(date_stamps[step][4:6])],
        #    int(date_stamps[step][6:8]),
        #    int(date_stamps[step][8:]))
        #    mout = error_plot("%sfigs/plot_neighbor_%d_%s.png" % (out_path,center_gridid,uci_starters[step]),
        #    plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],
        #    s_loc,a_loc,e_loc,[],msg)
        #    # Make plot wander_screen for this center
        #    c_loc = []
        #    for c in w_s[center_gridid]:
        #        c_loc.append((ijdict[c][2],ijdict[c][3]))
        #    if c_loc:
        #        msg = "Wander Screen for Center %d at %4d %s %02d %02d UTC" % (center_gridid,int(date_stamps[step][:4]),
        #                                                                       months[int(date_stamps[step][4:6])],
        #                                                                       int(date_stamps[step][6:8]),
        #                                                                       int(date_stamps[step][8:]))
        #        mout = error_plot("%sfigs/plot_wander_%d_%s.png" % (out_path,center_gridid,uci_starters[step]),
        #                          plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],
        #                          [],c_loc,[],[],msg)
        #    # Make plot region_screen for this center
        #    c_loc = []
        #    for c in r_s[center_gridid]:
        #        c_loc.append((ijdict[c][2],ijdict[c][3]))
        #    if c_loc:
        #        msg = "Regional Screen for Center %d at %4d %s %02d %02d UTC" % (center_gridid,int(date_stamps[step][:4]),
        #                                                                       months[int(date_stamps[step][4:6])],
        #                                                                       int(date_stamps[step][6:8]),
        #                                                                       int(date_stamps[step][8:]))
        #        mout = error_plot("%sfigs/plot_regional_%d_%s.png" % (out_path,center_gridid,uci_starters[step]),
        #                          plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],
        #                          [],c_loc,[],[],msg)
        #sys.exit("Stop HERE")

        # Special Fudge Factor for centers less than defs.min_contour
        # This allows the bottom contour to be a catch all for all
        # SLPS less than defs.min_contour
        current_center_slps = sorted([slp_step[center['GridID']] for center in current_centers])
        slp_offset = 0
        if current_center_slps[0] < current_contours[0]:
            slp_offset = current_contours[0] - current_center_slps[0]

        for this_slice in current_contours:

            # Screen current_contours to include only grids whole zonal anomaly matches or
            # falls below that defined by defs.z_anomaly_cutoff.
            # so either limit contours here or at end like where I used to screen for runaways etc.

##CUT
            #if this_slice == 1017500:
            #    verbose = 1

            # # Diagnostic
            # # Make plot every contour for this timestep
            # c_loc = []
            # for c in contours[this_slice]:
            #     c_loc.append((ijdict[c][2],ijdict[c][3]))
            # if c_loc:
            #     msg = "Contour Slice %d at %4d %s %02d %02d UTC" % (this_slice,int(date_stamps[step][:4]),
            #                                                         months[int(date_stamps[step][4:6])],
            #                                                         int(date_stamps[step][6:8]),
            #                                                         int(date_stamps[step][8:]))
            #     mout = error_plot("%sfigs/plot_slice_%d_%s.png" % (out_path,this_slice,uci_starters[step]),
            #                       plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[],
            #                       [],c_loc,[],[],msg)
            # continue

            # Screen contours by hemisphere
            ccc = dict( (x,1) for x in [x for x in contours[this_slice]])
            sh_contours = ccc.fromkeys([x for x in ccc if x <= eq_end],1)
            nh_contours = ccc.fromkeys([x for x in ccc if x not in sh_contours],1)

            ## Diagnostic
            #if verbose:
            #    print "\t\tDoing Slice: %d" % (this_slice)

            for center in current_centers:

                filter_count[0] += 1

                # Pre-bind
                center_gridid = center['GridID']

                #if center_gridid in empty_skipped:
                #    continue

                # FIX: Okay, due to small rounding errors we can't use
                # center['GridSLP'] because sometimes that contour is skipped in
                # current_centers. That is, if the slp_step is 1000001 but I
                # rounded center['GridSLP'] to 1000000 then the contour for
                # 1000000 might be empty and the whole center is skipped....
                # need to make center['GridSLP'] with the way I use intslp

                center_slp = slp_step[center['GridID']]
                if center_slp < current_contours[0]:
                    center_slp += slp_offset

                # Inner dictionary of center_slices that holds the results of
                # each slice; keyed by the lower pressure bound of the contour
                harvested = {}

                ## Diagnostic
                #extra = ""

                # Special case of lowest contour for each center:
                if this_slice <= center_slp < this_slice+defs_interval:
                    # Create key for first contour
                    center_active[center_gridid] = this_slice
                    ## Diagnostic
                    #extra = "   * 1st Contour *"

                 ## Diagnostic
                 #if verbose:
                 #   msg = "\t\t\tChecking Center % 6d (%6.2f,%6.2f) with SLP % 8d -> %s"
                 #   state = "Inactive"
                 #   if center_active[center_gridid] > 0:
                 #       state = "Active"+extra
                 #   print msg % (center_gridid,ijdict[center_gridid][2],
                 #       ijdict[center_gridid][3],center_slp,state)

                # Restrict to 'active' centers. That is, centers that are
                # still having contours filled. Otherwise go on to next
                # center... top of this loop.
                if center_active[center_gridid] > 0:

                    # Reduce the candidate grids in contours[this_slice] to
                    # the same hemisphere are the center... speed up
                    if center_gridid <= eq_end: # SH hemi
                        use_contours = sh_contours.copy()#sh_contours[:]
                    else: # NH hemi
                        use_contours = nh_contours.copy()#nh_contours[:]
                    ## Diagnostic
                    #if verbose:
                    #     if not use_contours:
                    #         print "NO contours"
                    #    hh = "NH"
                    #    if center_gridid <= eq_end:
                    #        hh = "SH"
                    #    print "\t\t\t\tUse %s use_contour (start):" % (hh)
                    #    print_col(the_list=use_contours.keys(),indent_tag="\t\t\t\t",
                    #               fmt="%6d",cols=6,width=10)

                    # Further limit the search to just a bit larger
                    # than the synoptic scale bracketed by wavenumbers
                    # 4-13... here we allow for wider systems
                    # before enacting the cut-off (note must be larger
                    # than the next similar screen or that screen never
                    # is enacted for cases where only a single contour
                    # exits for a center
                    regional_screen = dict( (x,1) for x in r_s[center_gridid])
                    wander_screen = dict( (x,1) for x in w_s[center_gridid])

                    # Trim to grids near the center
                    use_contours = use_contours.fromkeys([x for x in use_contours if x in regional_screen],1)

                    ## Diagnostic
                    ## Make plot use_contours for this center
                    #c_loc = []
                    #for c in use_contours:
                    #    c_loc.append((ijdict[c][2],ijdict[c][3]))
                    #if c_loc:
                    #    msg = "Use Contours for Slice %d and Center %d at %4d %s %02d %02d UTC" % (this_slice,center_gridid,int(date_stamps[step][:4]),
                    #                                                                            months[int(date_stamps[step][4:6])],
                    #                                                                            int(date_stamps[step][6:8]),
                    #                                                                            int(date_stamps[step][8:]))
                    #    mout = error_plot("%sfigs/plot_use_contours_%d_%d_%s.png" % (out_path,center_gridid,this_slice,uci_starters[step]),
                    #                   plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],
                    #                   [],c_loc,[],[],msg)

                    # List of all centers with this_slice already checked.
                    # If this center touches a grid from one of these centers
                    # then add all grids from that center (same slice) to this
                    # center and sort out later. Large speed improvement.
                    the_peers = [x for x in center_slices.keys()
                                 if center_slices[x].has_key(this_slice)]

                    ## Diagnostic
                    #if verbose:
                    #    print "\t\t\t\tuse_contours (trimmed):"
                    #    print_col(the_list=use_contours.keys(),indent_tag="\t\t\t\t",
                    #              fmt="%6d",cols=6,width=10)
                    #    print "\t\t\t\tpeers:"
                    #    print_col(the_list=the_peers,indent_tag="\t\t\t\t",
                    #              fmt="%6d",cols=6,width=10)

                    # Recursive check of this_slice seeded with the previous
                    # slice. This way, each new grid touches a grid that is
                    # trackable to a center.

                    # If 1st contour, seed with the center's moore neighbors
                    # in this contour.
                    if center_active[center_gridid] == this_slice:
                        need_do = [x for x in gdict[center_gridid]
                                   if x in use_contours]
                        catch = {}

                        ## Diagnostic
                        #if verbose:
                        #    print "\t\t\t\tInitial Seeds:"
                        #    print_col(the_list=need_do,indent_tag="\t\t\t\t",
                        #              fmt="%6d",cols=6,width=10)

                        for check in need_do:
                            ## FIX: bridge allows a center to appear in multiple contours which makes this not work correctly.
                            ## Skip checks for grids checked earlier in this loop.
                            #if check in catch:
                            #    continue

                            # Trim use_contours also
                            use_contours.fromkeys([x for x in use_contours if x not in catch],1)
                            args= (check,use_contours,gdict,center_slices,
                                   center_gridid,this_slice,the_peers)
                            harvest = scan_contour(*args)

                            # Screen by zonal anomaly status
                            if use_zmean:
                                harvest = [x for x in harvest if x in zgrids]

                            # Store unique results
                            catch.update(dict((x,1) for x in harvest))

                    else:
                        # Not 1st contour and last contour non-empty
                        catch = {}

                        # Sometimes a contour defs_interval is skipped so
                        # we use the last contour tested, which is
                        # most often this_slice-defs_interval. These grids
                        # are used to seed the check.
                        tsd = sorted(center_slices[center_gridid])
                        try_this = tsd[-1]

                        ## Diagnostic
                        #if verbose:
                        #    print "\t\t\t\tSecond Seeds:"
                        #    print_col(the_list=center_slices[center_gridid][try_this],
                        #              indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)

                        for check in center_slices[center_gridid][try_this]:
                            ## FIX bridge allows a center to appear in multiple contours which makes this not work correctly.
                            ## Skip checks for grids fully checked earlier in this loop.
                            #if check in catch:
                            #    continue

                            # Trim use_contours also
                            use_contours.fromkeys([x for x in use_contours if x not in catch],1)
                            args = (check,use_contours,gdict,center_slices,
                                    center_gridid,this_slice,the_peers)
                            harvest = scan_contour(*args)

                            # Screen by zonal anomaly status
                            if use_zmean:
                                harvest = [x for x in harvest if x in zgrids]

                            # Store unique results
                            catch.update(dict((x,1) for x in harvest))

                        ## Diagnostic
                        #if verbose:
                        #    print "\t\t\t\tCaught:"
                        #    print_col(the_list=catch.keys(),indent_tag="\t\t\t\t",
                        #              fmt="%6d",cols=6,width=10)

                    # Hill/Spill/Flare Test: Sometimes an open-wave center will follow a contour
                    # that sweeps around the high pressure surrounding the center and then
                    # all that high pressure is eventually attached to the center. This is
                    # wrong in that the "low" is surrounded by attributed high SLP. The trick
                    #
                    # Get counts of grids already added and those being added
                    base_grids = flatten(center_slices[center_gridid].values())
                    base_grids = dict((x,1) for x in base_grids)
                    added_grids = [x for x in catch if x not in base_grids]
                    added_grids = dict((x,1) for x in added_grids)
                    if base_grids:
                        all_grids = base_grids.keys()
                        all_grids.extend(added_grids.keys())
                    else:
                        all_grids = added_grids.keys()
                    big_cnt = len(all_grids)

                    # Skip small centers as unlikely to have this issue
                    if big_cnt >= defs_check_flare and base_grids:
                        flare_fix = 0
                        # For comparison test shift to center of model grid
                        offset = offsets[center_gridid]
                        center_off = center_gridid - offset
                        all_grids_off = [x-offset for x in all_grids]
                        hill_cnt = 0

                        ## Make plot
                        #c_loc = []
                        #for c in all_grids_off:
                        #    c_loc.append((ijdict[c][2],ijdict[c][3]))
                        #a_loc = []
                        #for c in added_grids:
                        #    a_loc.append((ijdict[c][2],ijdict[c][3]))
                        #if c_loc:
                        #    msg = "Flare for Slice %d and Center %d at %4d %s %02d %02d UTC" % (this_slice,center_off,int(date_stamps[step][:4]),months[int(date_stamps[step][4:6])],int(date_stamps[step][6:8]), int(date_stamps[step][8:]))
                        #    mout = error_plot("%sfigs/plot_flare_off_%d_%d_%s.png" % (out_path,center_off,this_slice,uci_starters[step]),plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_off][2],ijdict[center_off][3])],[],c_loc,[],a_loc,msg)

                        #print
                        #print "\t\t\t\tthis_slice",this_slice,"next_slice",int(this_slice+defs_interval)
                        #print "\t\t\t\toffset",offset
                        #print "\t\t\t\tcenter_slp",center_slp

                        for row in range(jm):
                            start = row_start[row]
                            end = row_end[row]
                            row_sweep = [x for x in all_grids_off if start <= x <= end]
                            # Look for gaps
                            nrow = len(row_sweep)
                            if nrow > 1:
                                row_sweep.sort()
                                # Look for flare (large tropical longitude spread)
                                dif = [(x-row_sweep[i])-1 for i,x in enumerate(row_sweep[1:])]
                                # Potential Gaps
                                dif_sum = reduce(add,dif)

                                #print "\t\t\t\tlat",lats[row]
                                #print "\t\t\t\tlons",[lons[x-start] for x in row_sweep]
                                #print "\t\t\t\trow(%d) [%d,%d]" % (row,start,end)
                                #print "\t\t\t\t\trow_sweep (%d):" % (nrow)
                                #print_col(the_list=row_sweep,indent_tag="\t\t\t\t\t\t",
                                #          fmt="%6d",cols=6,width=10,sort_me=0)

                                if dif_sum:
                                    # Examine gaps for high pressure
                                    gaps = [row_sweep[0]]
                                    for i,x in enumerate(row_sweep[1:]):
                                        if dif[i]:
                                            # Fill gap, account for possible issue at end.
                                            fill = [(y,y+im)[y < start] for y in range(x-dif[i],x+1)]
                                            gaps.extend(fill)
                                        else:
                                            gaps.append(x)
                                    # Find the SLPs in the gaps that are higher pressure
                                    next_slice = int(this_slice+defs_interval)

                                    gap_slps = [slp_step[x+offset] for x in gaps if x not in row_sweep]
                                    gap_slps = [x for x in gap_slps if int(x) >= next_slice]
                                    # Count the number of higher pressure gaps
                                    dif_sum = len(gap_slps)
                                    hill_cnt += dif_sum

                                    #print "\t\t\t\t\tdifs (%d,%d):" % (dif_sum,hill_cnt)
                                    #print_col(the_list=dif,indent_tag="\t\t\t\t\t\t",
                                    #          fmt="%2d",cols=15,width=6,sort_me=0)
                                    #print "\t\t\t\t\trow_sweep_full (%d):" % (row_sweep[-1]-row_sweep[0]+1)
                                    #print_col(the_list=range(row_sweep[0],row_sweep[-1]+1),indent_tag="\t\t\t\t\t\t",
                                    #          fmt="%6d",cols=6,width=10,sort_me=0)
                                    #print "\t\t\t\t\tslps (%d):" % (len(slp_step[row_sweep[0]:row_sweep[-1]+1]))
                                    #print_col(the_list=list(slp_step[row_sweep[0]+offset:row_sweep[-1]+offset+1]),indent_tag="\t\t\t\t\t\t",
                                    #              fmt="%6d",cols=6,width=10,sort_me=0)
                                    #print "\t\t\t\t\tgap slps (%d):" % (len(gap_slps))
                                    #print_col(the_list=gap_slps,indent_tag="\t\t\t\t\t\t",
                                    #          fmt="%6d",cols=6,width=10,sort_me=0)
##CUT
                                #else:
                                #    next_slice = this_slice
                                #    gaps = []
                                #    gap_slps = []
                                #    print "\t\t\t\t\thill (%d)" % (len(gap_slps))

                                # Are there more gaps than grids?
                                if hill_cnt > big_cnt:
                                    filter_count[1] += 1
                                    # Limit to just grids within region of neighbor_screen... need to
                                    # recheck to ensure all grids contigous to center.
                                    catch = dict((x,1) for x in [y for y in catch if y in n_s[center_gridid]])
                                    catchy = dict((x,1) for x in base_grids)
                                    for check in base_grids:
                                        args = (check,catch,gdict,center_slices,
                                                center_gridid,this_slice,[])
                                        harvest = scan_contour(*args)
                                        catchy.update(dict((x,1) for x in harvest))
                                    catch = catchy
                                    flare_fix = 1
                                    break

                                    ## UN/COMMENT OUT ABOVE BREAK!
                                    ## Make plot
                                    #c_loc = []
                                    #for c in all_grids:
                                    #    c_loc.append((ijdict[c][2],ijdict[c][3]))
                                    #a_loc = []
                                    #for c in added_grids:
                                    #    a_loc.append((ijdict[c][2],ijdict[c][3]))
                                    #e_loc = []
                                    #for c in catch:
                                    #    e_loc.append((ijdict[c][2],ijdict[c][3]))
                                    #if c_loc:
                                    #    msg = "Flare for Slice %d and Center %d at %4d %s %02d %02d UTC" % (this_slice,center_gridid,int(date_stamps[step][:4]),months[int(date_stamps[step][4:6])],int(date_stamps[step][6:8]), int(date_stamps[step][8:]))
                                    #    mout = error_plot("%sfigs/plot_flare_%d_%d_%s.png" % (out_path,center_gridid,this_slice,uci_starters[step]),plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],[],c_loc,e_loc,a_loc,msg)
                                    #break

                        # Inflation Test: Watch for cases where the coverage (number of added grids) for this
                        # contour is much larger than accrued so far. Happens when a very wide and shallow
                        # contour is encountered. Drop contouring when this happens as not usually what we want.
                        # This only seems to happen only for relatively high pressure lows so only check these

                        if center_slp >= defs_check_inflate and not flare_fix:
                            inflate = float(len(added_grids))/float(len(base_grids))
                            if inflate >= defs_inflated:
                                filter_count[2] += 1
                                # Drop this whole contour, which will terminate further attribute searching.
                                catch = {}
                                flare_fix = 1

                                ## Make plot
                                #c_loc = []
                                #for c in all_grids:
                                #    c_loc.append((ijdict[c][2],ijdict[c][3]))
                                #a_loc = []
                                #for c in added_grids:
                                #    a_loc.append((ijdict[c][2],ijdict[c][3]))
                                #if c_loc:
                                #    msg = "Inflation for Slice %d and Center %d at %4d %s %02d %02d UTC" % (this_slice,center_gridid,int(date_stamps[step][:4]),months[int(date_stamps[step][4:6])],int(date_stamps[step][6:8]), int(date_stamps[step][8:]))
                                #    mout = error_plot("%sfigs/plot_inflation_%d_%d_%s.png" % (out_path,center_gridid,this_slice,uci_starters[step]),plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],[],c_loc,[],a_loc,msg)

                    # Store results and do some screening
                    if catch:
                        harvested[this_slice] = catch.keys()
                        catch = {}

                        ## Diagnostic
                        #if verbose:
                        #    msg = "\t\t\t\tEnter Wander Test: %d"
                        #    print msg % (len(harvested[this_slice]))
                        #    print_col(the_list=harvested[this_slice],indent_tag="\t\t\t\t",
                        #              fmt="%6d",cols=6,width=10)

                        ## Make plot harvested contours for this center
                        #c_loc = []
                        #for c in harvested[this_slice]:
                        #    c_loc.append((ijdict[c][2],ijdict[c][3]))
                        #if c_loc:
                        #    msg = "Caught Contours for Slice %d and Center %d at %4d %s %02d %02d UTC" % (this_slice,center_gridid,int(date_stamps[step][:4]),
                        #                                                                                  months[int(date_stamps[step][4:6])],
                        #                                                                                  int(date_stamps[step][6:8]),
                        #                                                                                  int(date_stamps[step][8:]))
                        #    mout = error_plot("%sfigs/plot_caught_contours_%d_%d_%s.png" % (out_path,center_gridid,this_slice,uci_starters[step]),
                        #                      plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,[(ijdict[center_gridid][2],ijdict[center_gridid][3])],
                        #                      [],c_loc,[],[],msg)

                        # Wander Test: does this contour wonder too far from the
                        # center? If so, drop this contour and any further
                        # contouring for this center. Does slice contain grids
                        # too far out? This occurs if any harvested grid is not
                        # in regional_screen.
                        w_test = [x for x in harvested[this_slice]
                                  if x not in wander_screen]

                        if w_test:
                            # Done checking this center... failed test
                            filter_count[3] += 1
                            harvested[this_slice] = []
                            center_active[center_gridid] = 0
                        else:
                            # Append to previous results if any pnts remaining
                            t = dict(center_slices[center_gridid])
                            t.update({this_slice:harvested[this_slice]})
                            center_slices[center_gridid] = t

                        ## Diagnostic
                        #if verbose:
                        #    msg = "\t\t\t\tExit Wander Test: %d"
                        #    print msg % (len(harvested[this_slice]))
                        #    print_col(the_list=harvested[this_slice],indent_tag="\t\t\t\t",
                        #              fmt="%6d",cols=6,width=10)

                    else:
                        # Set this so center not checked again as
                        # the center is done being contoured.
                        center_active[center_gridid] = 0

                        ## Diagnostic
                        #if verbose:
                        #    msg = "\t\t\tCenter % 6d -> Dead" % (center_gridid)

                ## Diagnostic
                #print center_slices[center_gridid]
            #-----------------------------------------------------------------------
            # End Loop Over Centers
            #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # End Loop Over Slices
        #-----------------------------------------------------------------------

        if speedometer:
            time2 = time.clock()
            #print "\t\t\tInner Frame Rate: %f per min (%d centers)" % (round(time2-time1,3)/60.0,len(current_centers))

        ## Diagnostic
        #if verbose:
        #    msg = "\n\t\t%s\n\t\tPost-Processing Harvest" % (60*"-")
        #    print msg

        # Final tests to be done after all centers checked for all contours

        # Fix issues such as detached grids or wrongful stormy due to
        # use_zmean
        if use_zmean:
            backup = copy.deepcopy(center_slices)
            for center in center_slices:
                #print
                #print "Scanning center",center
                seeds = dict.fromkeys([center],1)
                for this_slice in sorted(center_slices[center]):
                    #print "\tthis_slice",this_slice
                    #print "\t\tseeds (%d):" % (len(seeds.keys()))
                    #print_col(seeds.keys(),indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
                    #print "\t\tCandidates or center_slices[center][this_slice] (%d):" % (len(center_slices[center][this_slice]))
                    #print_col(center_slices[center][this_slice],indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
                    #print

                    # Okay check slice for connection to center
                    candidates = dict.fromkeys(center_slices[center][this_slice],1)
                    scan_center(seeds,candidates,gdict)
                    #print "\t\tseeds (%d):" % (len(seeds.keys()))
                    #print_col(seeds.keys(),indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
                    harvest = [x for x in seeds if x in center_slices[center][this_slice]]
                    #print "\t\tharvest (%d):" % (len(harvest))
                    #print_col(harvest,indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
                    #lost = [x for x in center_slices[center][this_slice] if x not in harvest]
                    #print "\t\tlost (%d):" % (len(lost))
                    #print_col(lost,indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)

                    # Store what was gleaned from this_slice... note it's possible to skip
                    # a slice and still have more values to add in higher slices.
                    if harvest:
                        backup[center][this_slice] = harvest
                    else:
                        del backup[center][this_slice]
            center_slices = backup

        # Hole Fill: Sometimes a conspicuous hole appears where, because
        # the scan_contour can't fill lower pressure grids, some grids
        # need to be backfilled for completeness. NOTE: profiling shows
        # that this step is one of the most computationally intensive.
        #args = (center_slices,collapse,gdict,wander_test,row_start,
        #         row_end,im,jm,contours,ijdict,N_multiply(slp_step[:],inv_accuracy),
        #         lons,lats,error_plot,out_path,plot,deque,eq_grid,neighbors)
        args = (center_slices,collapse,gdict,wander_test,row_start,
                 row_end,im,jm,contours,offsets,neighbors)
        filled = fill_holes(*args)

        ## Diagnostic
        #if verbose:
        #    print "\t\t\tFill_Holes:"
        #    if not filled:
        #        print "\t\t\t\tNone"
        #    else:
        #        keys = filled.keys()
        #        keys.sort()
        #        for cc in keys:
        #            print "\t\t\t\t%6d:" % (cc)
        #            print_col(the_list=filled[cc],indent_tag="\t\t\t\t\t",
        #                      fmt="%6d",cols=6,width=10)
        ## Plot all filled holes are precaution for problems
        #c_loc = []
        #a_loc = []
        #for c in filled:
        #    c_loc.append((ijdict[c][2],ijdict[c][3]))
        #    if c_loc:
        #        msg = "Filled Hole Center %d at %4d %s %02d %02d UTC" % (c,int(date_stamps[step][:4]),
        #        months[int(date_stamps[step][4:6])],
        #        int(date_stamps[step][6:8]),
        #        int(date_stamps[step][8:]))
        #        for cc in filled[c]:
        #            a_loc.append((ijdict[cc][2],ijdict[cc][3]))
        #        mout = error_plot("%sfigs/plot_filled_hole_%d_%s.png" % (out_path,c,uci_starters[step]),
        #                          plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
        #                          [],a_loc,[],[],msg)

        # Problematic Test: Grids over troublesome regions.
        # Append centers with flag = 4 as previously IDed as
        # having non-cyclone like properties.
        flagged_centers = [center['GridID'] for center in current_centers if int(center['Flags']) != 0]
        if flagged_centers and defs.troubled_filter:
            trouble_grids.update(dict((x,1) for x in flagged_centers))
        args = (center_slices,trouble_grids)
        problematic = find_problematic(*args)

        ## Diagnostic
        #if verbose:
        #    print "\t\t\tProblematic Grids:"
        #    keys = problematic.keys()
        #    keys.sort()
        #    for cc in keys:
        #        print "\t\t\t\t%6d:" % (cc)
        #        print_col(the_list=problematic[cc],indent_tag="\t\t\t\t\t",
        #                 fmt="%6d",cols=6,width=10)

        # Overlap/Envelope Test: Centers share same attributed grids.
        near_stormy = {} # list of grids that where associated with a
        # center(s) but got dropped in this step.
        slp_tmp = slp[0,:].copy()
        slp_tmp.shape = (jm,im)
        args = (numpy,copy,envelope_test,current_contours[::-1],center_slices,
                near_stormy,ijdict,slp_tmp,lons,lats,filled)
        center_slices = check_overlap(*args)

        ## Diagnostic
        #if verbose:
        #    print "\t\t\tNear_Stormy:"
        #    if not near_stormy:
        #        print "\t\t\t\tNone"
        #    else:
        #        keys = near_stormy.keys()
        #        keys.sort()
        #        for cc in keys:
        #            print "\t\t\t\t%6d:" % (cc)
        #            print_col(the_list=near_stormy[cc].keys(),indent_tag="\t\t\t\t\t",
        #                     fmt="%6d",cols=6,width=10)

        # Find and remove empty centers
        empty_centers = []
        args = (empty_centers,center_slices,current_centers)
        center_slices = find_empty_centers(*args)
        ## Diagnostic
        #if verbose:
        #    print "\t\t\tEmpty Centers:"
        #    print_col(the_list=[int(x[7]) for x in empty_centers],indent_tag="\t\t\t",
        #              fmt="%6d",cols=6,width=10)
        # collapse center_slices to a list of gridids:
        collapsed_centers = {}
        collapse(collapsed_centers,center_slices)

        # Append polar skipped centers
        if polar_centers:
            empty_centers.extend(polar_centers)

    # Clean-up for bridging
        clean_bridge(near_stormy,collapsed_centers)
        stormy_loc = near_stormy.keys()

        atts_loc = [x for y in center_slices.keys()
                    for x in collapsed_centers[y]]

        # Insure that some atts collected but not too many
        coverage = len(atts_loc) + len(stormy_loc)

        if coverage < att_min_cnt or coverage > att_max_cnt:
            err_num = 7
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: Att count problem for this timestep." % (err_num)
            msg = "\t\tcoverage: %d" % (coverage)
            tmp = "Fail Check %d: Att count problem %4d %s %02d %02d UTC"
            msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                          months[int(date_stamps[step][4:6])],
                          int(date_stamps[step][6:8]),
                          int(date_stamps[step][8:]))
            if plot_on_error:
                c_loc = []
                for each in center_slices.keys():
                    ix = ijdict[each][2]
                    c_loc.append((ix,ijdict[each][3]))
                a_loc = []
                for each in atts_loc:
                    ix = ijdict[each][2]
                    a_loc.append((ix,ijdict[each][3]))
                s_loc = []
                for each in stormy_loc:
                    ix = ijdict[each][2]
                    s_loc.append((ix,ijdict[each][3]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
                                  s_loc,a_loc,[],[],msg1)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        ## Diagnostic
        #if verbose:
        #    print "\t\t\tKept Centers (%d) and Attributed Grids (%d):" % (len(center_slices),len(atts_loc))
        #    if not center_slices:
        #        print "\t\t\t\tNone"
        #    else:
        #        keys = center_slices.keys()
        #        keys.sort()
        #        for cc in keys:
        #            print "\t\t\t\t%6d:" % (cc)
        #            print_col(the_list=collapsed_centers[cc],indent_tag="\t\t\t\t\t",
        #                      fmt="%6d",cols=6,width=10)

        # Final check that near_stormy and centers don't collide
        t1 = [x for x in stormy_loc if x in center_slices.keys()]
        if t1:
            err_num = 4
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: Overlap of near_stormy and centers for this timestep." % (err_num)
            msg = "\t\tt1: %s" % (repr(t1))
            tmp = "Fail Check %d: Overlap of near_stormy and centers for %4d %s %02d %02d UTC"
            msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                          months[int(date_stamps[step][4:6])],
                          int(date_stamps[step][6:8]),
                          int(date_stamps[step][8:]))
            if plot_on_error:
                c_loc = []
                for each in center_slices.keys():
                    ix = ijdict[each][2]
                    c_loc.append((ix,ijdict[each][3]))
                s_loc = []
                for each in stormy_loc:
                    ix = ijdict[each][2]
                    s_loc.append((ix,ijdict[each][3]))
                a_loc = []
                for each in atts_loc:
                    ix = ijdict[each][2]
                    a_loc.append((ix,ijdict[each][3]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
                              s_loc,a_loc,[],[],msg1)
            print "Stormy_loc:"
            print_col(the_list=stormy_loc,indent_tag="\t",
                      fmt="%6d",cols=6,width=10)
            print "center_slices.key:"
            print_col(the_list=center_slices.keys(),indent_tag="\t",
                      fmt="%6d",cols=6,width=10)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        # Final check that attributed and near_stormy don't collide
        t1 = [x for x in atts_loc if x in stormy_loc]
        if t1:
            err_num = 5
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: Overlap of near_stormy and attributed for this timestep." % (err_num)
            msg = "\t\tt1: %s" % (repr(t1))
            tmp = "Fail Check %d: Overlap of near_stormy and attributed for %4d %s %02d %02d UTC"
            msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                          months[int(date_stamps[step][4:6])],
                          int(date_stamps[step][6:8]),
                          int(date_stamps[step][8:]))
            if plot_on_error:
                c_loc = []
                for each in center_slices.keys():
                    ix = ijdict[each][2]
                    c_loc.append((ix,ijdict[each][3]))
                s_loc = []
                for each in stormy_loc:
                    ix = ijdict[each][2]
                    s_loc.append((ix,ijdict[each][3]))
                a_loc = []
                for each in atts_loc:
                    ix = ijdict[each][2]
                    a_loc.append((ix,ijdict[each][3]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
                              s_loc,a_loc,[],[],msg1)
            print "T1:"
            print_col(the_list=t1,indent_tag="\t",
                      fmt="%6d",cols=6,width=10)
            print "Stormy_loc:"
            print_col(the_list=stormy_loc,indent_tag="\t",
                      fmt="%6d",cols=6,width=10)
            print "Att_loc:"
            print_col(the_list=atts_loc,indent_tag="\t",
                      fmt="%6d",cols=6,width=10)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        # Store in files
        args = (current_centers,collapsed_centers,center_slices,
                darea,row_start,row_end,angle_lookup,distance_lookup)
        saved_centers = [att_2_file(add,stats,acenter,*args)
                         for acenter in collapsed_centers.keys()]
        fnc_out = []
        args = (add,empty_centers,near_stormy,problematic,saved_centers,darea,
                row_start,row_end,angle_lookup,distance_lookup)
        fnc_out= terminal_to_file(*args)
        empty_group  = fnc_out[0]
        stormy_group = fnc_out[1]
        prob_group   = fnc_out[2]

        # Final check that all current_centers either attributed
        # or empty
        if (len(current_centers)+len(polar_centers)) != (len(empty_group)+len(collapsed_centers)):
            err_num = 6
            date_stamp = date_stamps[step]
            smsg = "\n\tFail Check %d: Center Loss/Gain" % (err_num)
            msg2 = "\t\tlen(current_centers): %d\n\t\tlen(empty_group): %d"
            msg2 = msg2 + "\n\t\tlen(collapsed_centers): %d"
            msg = msg2 % (len(current_centers),len(empty_group),len(collapsed_centers))
            if plot_on_error:
                tmp = "Fail Check %d: Center Loss/Gain for %4d %s %02d %02d UTC"
                msg1 = tmp % (err_num,int(date_stamps[step][:4]),
                              months[int(date_stamps[step][4:6])],
                              int(date_stamps[step][6:8]),
                              int(date_stamps[step][8:]))
                c_loc = []
                for each in current_centers:
                    c_loc.append((int(each[6])*0.01,90.0-int(each[5])*0.01))
                e_loc = []
                for each in empty_group:
                    parts= strip_read(each)
                    e_loc.append( (int(parts[6])*0.01,90.0-int(parts[5])*0.01))
                a_loc = []
                for each in collapsed_centers.keys():
                    ix = ijdict[each][2]
                    a_loc.append((ix,ijdict[each][3]))
                mout = error_plot("%sfigs/error_%d_%s.png" % (out_path,err_num,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
                                  [],a_loc,e_loc,[],msg1)
            if not skip_save:
                redo_save.writelines("%s," % (date_stamp))
            exec(do_this)

        if not skip_save:
            # Save
            att_save.writelines(saved_centers)
            att_save.writelines(empty_group)
            att_save.writelines(stormy_group)
            att_save.write(prob_group)

        ## Use with Mike_Test tag above
        ## Use to list centers and counts
        ## with with WARNING!!!
        #print "current_centers",len(current_centers)
        #i = 0
        #print "Centers with Attributions"
        #fmts = "\tCount %02d: Center %05d i,j (%03d,%03d), lon,lat (%8.2f,%8.2f), Grid Cnt %d Depth %f"
        #for x in center_slices:
        #    i += 1
        #    ac = sorted(center_slices[x].keys())
        #    Depth = ac[-1] - ac[0]
        #    print fmts % (i,x,ijdict[x][0],ijdict[x][1],ijdict[x][2],ijdict[x][3],
        #                   len(collapsed_centers[x]),Depth)
        #print "Empty Centers"
        #for each in empty_group:
        #    i += 1
        #    parts = strip_read(each)
        #    x = int(parts[8])
        #    print fmts % (i,x,ijdict[x][0],ijdict[x][1],ijdict[x][2],ijdict[x][3],0,0)

        # Make plot of this time step
        if plot_every and not step % plot_every:
            c_loc = []
            e_loc = []
            a_loc = []
            s_loc = []
            p_loc = []

            for center in saved_centers:
                parts = center.split()
                # Unpack attribution group
                ngrids = int(parts[16])
                atts = parts[24:23+ngrids]
                atts = [int(x) for x in atts]
                for a in atts:
                    a_loc.append((ijdict[a][2],ijdict[a][3]))
                c_loc.append((int(parts[6])*0.01,90.0 - int(parts[5])*0.01))
            for each in empty_group:
                parts = strip_read(each)
                e_loc.append( (int(parts[7])*0.01,90.0-int(parts[6])*0.01))
            for a in stormy_loc:
                s_loc.append((ijdict[a][2],ijdict[a][3]))
            for b in problematic:
                for a in problematic[b]:
                    p_loc.append((ijdict[a][2],ijdict[a][3]))
            msg = "State at %4d %s %02d %02d UTC" % (int(date_stamps[step][:4]),
                                                     months[int(date_stamps[step][4:6])],
                                                     int(date_stamps[step][6:8]),
                                                     int(date_stamps[step][8:]))
            if use_dumped:
                discard_loc = []
                d_colors = []
                for c in current_dumped_centers:
                    llon = int(c[6])*0.01
                    llat = 90.0 - int(c[5])*0.01
                    discard_loc.append((llon,llat))
                    d_colors.append(flag_colors[int(c[11])])
                mout = error_plot("%sfigs/plot_%s.png" % (out_path,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
                                  s_loc,a_loc,e_loc,p_loc,msg,discard_loc=discard_loc,d_colors=d_colors)
            else:
                mout = error_plot("%sfigs/plot_%s.png" % (out_path,uci_starters[step]),
                                  plot,N_multiply(slp_step[:],inv_accuracy),lons,lats,c_loc,
                                  s_loc,a_loc,e_loc,p_loc,msg)
        if speedometer:
            time3 = time.clock()
            #print "\t\t\tOuter Frame Rate: %f/%f per min" % (round(time3-time1,3)/60.0,round(time3-time2,3)/60.0)
            if not skip_save:
                speed_save.write("%04d %03d %f %f\n" % (step,len(current_centers),
                    round(time2-time1,3)/60.0,round(time3-time1,3)/60.0))

    #---------------------------------------------------------------------------
    # End YEAR
    #---------------------------------------------------------------------------
    
    # Check to see that all centers that were read were used.
    if total_centers != centers_used + centers_skipped:
        if ReDo_List or short_skip:
            pass
        else:
            msg = "Error centers used differs from read."
            msg += "total_centers %d != centers_used %d + centers_skipped %d"
            import sys; sys.exit(msg % (total_centers,centers_used,centers_skipped))
        
    if not skip_save:
        # Close open files
        att_save.close()
        prog_save.close()
    if speedometer:
        speed_save.close()
    # Save memory when pull_data called in loop stores a copy of slp
    #  and thus doubles the memory footprint of the code.
    del slp
    del pull_data
    if use_zmean:
        del zanom
    if plot_on_error or plot_every:
        del plot_map,Plot_Map, error_plot

    if not skip_save:
        # Parse filter stats and save to a file
        tmp = "%sstats/mcms_%s_filter_stats_report_%d" % (out_path,model,loop_year)
        fstat_out = make_unique_name(os,tmp,".txt")
        fstat_save = open(fstat_out,"w")
        fstat_save.writelines("%04d\n" % (loop_year))
        msg1 = "Filter Call Counts:\n\t%s\t=\t%d\n\t%s\t=\t%d (%f)\n\t%s\t=\t%d (%f)\n\t%s\t=\t%d (%f)\n"
        msg = msg1 % (filters[0],filter_count[0],
                      filters[1],filter_count[1],100.0*(float(filter_count[1])/float(filter_count[0])),
                      filters[2],filter_count[2],100.0*(float(filter_count[2])/float(filter_count[0])),
                      filters[3],filter_count[3],100.0*(float(filter_count[3])/float(filter_count[0])))
        fstat_save.writelines(msg)
        fstat_save.close()

        #info_save.close()
        redo_save.close()
        # Erase redo if empty.
        fsize = os.path.getsize(redo_out)
        if fsize == 0:
            os.remove(redo_out)
    return "Done"

#---Start of main
if __name__=='__main__':

    import os,sys
    import pickle

    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------

    picks = {0 : "NCEP/NCAR Reanalysis 1",
             1 : "NCEP-DOE Reanalysis 2",
             2 : "NASA GISS GCM ModelE",
             3 : "GFDL GCM",
             4 : "ERA-Interim Reanalysis",
             5 : "ERA-40 Reanalysis"}
    pick = 0
    if pick not in picks:
        sys.exit("ERROR: pick not listed in picks.")

    # This next set of lines should be copied from setup_vX.py
    # Short names by which pick will be labeled.
    models = ["nra","nra2","giss","gfdl","erai","era40"]
    try:
        model = models[pick]
    except:
        sys.exit("ERROR: pick not listed in models.")

    # Halt program on error or just warn?
    exit_on_error = 0

    # Plot map on error (debugging mostly,requires matplotlib, also
    # doubles or more memory footprint)
    plot_on_error = 0

    # Reverse: go backwards through the years
    go_backwards = 1

    # Use weekly zonal median to filter contours to leave only those that
    # rise above defs.z_anomaly_cutoff and are therefore significant dips in the
    # slp field.
    use_zmean = 0

    # Use local SLP gradient or laplacian to filter potential grids.
    use_grad = 0

    # Speedometer: outputs how fast timesteps are being finished... for debugging mostly
    speedometer = 0

    if use_zmean and use_grad:
        sys.exit("Stop: Can't have use_zmean and use_grad")

    # Skip saving of data... faster for debuging
    skip_save = 0
    if skip_save:
        print "\n\n\n\n\n"
        print "WARNING WARNING NO DATA BEING SAVED!!!!!!!!"

    ## ReDo_List: List of date_stamps (YYYYMMDDHH or timestep).
    ## This allows particular timesteps to be redone without having
    ## to redo the whole record. Note: Separate att_file created
    ## for each record.
    ReDo_List = []
    #ReDo_List = ['1979111106']
    ##    ReDo_List =  "/Volumes/scratch/output/test/redos_001.txt"
    # To run fast on multiple processes for 1 year, change do_redo and launch
    # in the background manually.... see make_redo.py
    # use command line argument to rotate through options i.e.,
    # python attribute_vX.py 1 for redoes 1
    #ReDo_Lists = ['redos_test_01.txt','redos_test_02.txt','redos_test_03.txt',
    #        'redos_test_04.txt','redos_test_05.txt','redos_test_06.txt',
    #        'redos_test_07.txt','redos_test_08.txt','redos_test_09.txt',
    #        'redos_test_10.txt','redos_test_11.txt','redos_test_12.txt']
    #do_redo = int(sys.argv[1])
    #ReDo_List = '/Volumes/scratch/output/nra2/%s' % (ReDo_Lists[do_redo-1])
    #print "Using do_redo %d: %s " % (do_redo,ReDo_List)
    #if isinstance(ReDo_List, str):
    #    # ReDo_List is a string/path to a file to read
    #    if not os.path.exists(ReDo_List):
    #        sys.exit("Error: redo file %s does not exist." % (ReDo_List))
    #    # Open ReDo_List and pull entries into a list
    #    tmp_read = open(ReDo_List,"r")
    #    for line in tmp_read:
    #        # There can only be a single line!
    #        tmp_r = line.split(",")
    #    tmp_read.close()
    #     # Remove any empty strings.
    #    tmp_r = [x for x in tmp_r if x]
    #    ReDo_List = tmp_r
   
    # IF non-zero then every plot_every timesteps a plot of the SLP
    # field, centers, ATTS and stormy grid will be created. Example,
    # plot_every = 30*(24/timestep) creates a plot every 30 days just
    # to allow for monitoring on progress. Set plot_every = 1 to create
    # movie. Requires matplotlib, also doubles or more memory footprint.
    plot_every = 0#30*(24/6)

    # For plot_every provide a "dumped" file so that rejected centers
    # including in plot to help diagnose problems/successes,
    use_dumped = 1
    if not plot_every:
        # No point
        use_dumped = 0

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # Basic standard Python modules to import.
    imports = []
    imports.append("import math,pickle,numpy,netcdftime,stats,copy")
    imports.append("import netCDF4 as NetCDF")
    imports.append("from operator import add")
    if speedometer:
        imports.append("import time,datetime")

    # My modules to import w/ version number appended.
    my_base = ["defs", "bridge","try_bridge","find_problematic",
            "scan_contour","check_overlap","find_empty_centers","collapse",
            "clean_bridge","strip_read","att_2_file","fill_holes","envelope_test",
            "make_unique_name","print_col","flatten","scan_center"]
    if plot_on_error or plot_every:
        my_base.append("error_plot")
        my_base.append("plot_map")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)

    # To save a double copy of the data being retained by pull_data it is
    # necessary to reimport and delete pull_data_vX.py inside each loop.
    import_read =  "import %s%s as %s" % ("pull_data",vnum,"pull_data")

    # --------------------------------------------------------------------------
    # Alter default behavior found in either defs_vX.py or setup_vX.py
    # --------------------------------------------------------------------------

    # The default behavior is to read SLP data from the
    # directory slp_path defined in setup_vX.py.
    # Here you can elect to override this behavior.
    over_write_slp_path = ""

    # The default behavior is to save results
    # in the directory out_path defined in
    # setup_vX.py. Here you can elect to override
    # this behavior.
    over_write_out_path = ""

    # This next set of lines should be copied from setup_vX.py
    # Full path to the root directory where pick specific output will be stored.
    # Note it's possible that all of these directories are identical.
    # Uncomment to use unique structure for each model
    #result_directories = ["/Volumes/scratch/output/",] 
    # Uncomment to use same structure for all models
    result_directories = ["/Volumes/scratch/output/" for x in range(len(picks))]
    # Uncomment to make current directory for all models
    #result_directories = [os.getcwd() for x in picks]
    try:
        result_directory = result_directories[pick]
        if not os.path.exists(result_directory):
            sys.exit("ERROR: result_directory not found.")
    except:
        sys.exit("ERROR: pick not listed in result_directories.")

    # Directory to be created for storing temporary pick specific files.
    shared_path = "%s%s_files/" % (result_directory,model)

    # The default behavior is to run over all the
    # years found by setup_vX.py. Here you can
    # elect to override this behavior.
    over_write_years = []
    over_write_years = [1996,1996]

    # Here you can alter the default behavior as determined
    # by defs_vX.py and possibly setup_vX.py.
    defs_set = {}
    if pick <= 1:
        defs_set = {"keep_log":False,"wavenumber":4.0,"troubled_filter":True}
    elif pick == 2:
        defs_set = {"keep_log":False,"wavenumber":4.0,"read_scale":1.0,
                "troubled_filter":True}
    elif pick == 3:
        defs_set = {"keep_log":False,"wavenumber":4.0,"troubled_filter":True}
    elif pick == 4:
        defs_set = {"keep_log":False,"wavenumber":4.0,"troubled_filter":True}
    elif pick == 5:
        # match RAIBLE et. all 2007
        defs_set = {"keep_log":False,"wavenumber":4.0,"troubled_filter":True,
                "tropical_filter":True,'max_cyclone_speed': 42.0,
                'age_limit':72.0,"topo_filter":True}

    # Define some files
    centers_file = "tracks.txt"

    msg = "\n\t====\tAttribute Finding\t===="
    print msg
    print "\tPick: %d" % (pick)
    if over_write_slp_path:
        print "\tUsing over_write_slp_path: %s" % (over_write_slp_path)
    else:
        print "\tUsing default slp_path"
    if over_write_out_path:
        print "\tUsing over_write_out_path: %s" % (over_write_out_path)
    else:
        print "\tUsing default out_path"
    if not os.path.exists(shared_path):
        sys.exit("\tCan't find shared_path!")
    else:
        print "\tUsing shared_path: %s" % (shared_path)
    if over_write_years:
        print "\tUsing over_write_years: %s" % (repr(over_write_years))
    else:
        print "\tUsing default years"
    if defs_set:
        print "\tUsing modified defs for defs_vX.py:"
        for d in defs_set:
            print "\t\t%20s:\t%s" % (d,defs_set[d])
    else:
        print "\tUsing defaults from defs_vX.py"

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
            "shared_path","lat_edges","lon_edges","land_gridids","troubled_centers",
            "faux_grids")
        super_years = fnc_out[inputs.index("super_years")]
        out_path = fnc_out[inputs.index("out_path")]
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
    if over_write_years:
        super_years = over_write_years
    if over_write_out_path:
        out_path = over_write_out_path
    if over_write_slp_path:
        slp_path = over_write_slp_path

    # Create out_path if it doesn't exist.
    if not os.path.exists(out_path):
        dirs = list(map(os.makedirs, (out_path,
        out_path+'/comps/',
        out_path+'/pdfs/',
        out_path+'/stats/',
        out_path+'/netcdfs/',
        out_path+'/figs/pdfs/',
        out_path+'/figs/comps/')))
        print "\tDirectory %s Created." % (out_path)

    # -------------------------------------------------------------------------
    # Start Main Loop over super_years
    # -------------------------------------------------------------------------
    years = [x for x in range(int(super_years[0]),int(super_years[-1])+1)]
    if go_backwards:
        years.reverse()

    # This is a single processor version.
    for loop_year in range(int(super_years[0]),int(super_years[-1])+1):
        print "\n\t=============%d=============" % (loop_year)
        msg = main(centers_file, defs_set, imports, pick, out_path, shared_path,
                over_write_slp_path, loop_year, exit_on_error,
                plot_on_error, plot_every, ReDo_List, use_dumped, skip_save,
                use_zmean, use_grad ,speedometer, import_read)
        print "\t",msg

#     # Does a memory/time profile to find reason for slow downs etc.
#     import cProfile
#     msg = "main(centers_file,get_var,defs_set,imports,model,out_path,shared_path,"
#     msg = msg + "slp_path,years,exit_on_error,plot_on_error,plot_every,ReDo_List,use_dumped)"
#     cProfile.run(msg,sort=1,filename="h.cprof")
#     import pstats
#     stats = pstats.Stats("h.cprof")
#     stats.strip_dirs().sort_stats('time').print_stats(20)

    # ------------------------------------------------------------------------------
    # Notes: Rather than embed in code make reference here
    # ------------------------------------------------------------------------------
    Notes = """
    """
