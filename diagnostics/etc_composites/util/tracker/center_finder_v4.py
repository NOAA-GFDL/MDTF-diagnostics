""" This module extracts cyclone centers/tracks from a series of sea level
    pressure fields. The is module contains the main logic of this process.

    Options/Arguments:
    centers_file -- file_name template for storing results.
    dumped_centers_file -- file_name template for storing results
        for rejected centers.
    defs_set -- alterations of defaults from defs_vX.py.
    imports -- list of modules to import.
    over_write_out_path -- override value from setup_vX.py.
    over_write_shared_path -- override value from setup_vX.py.
    over_write_slp_path -- override value from setup_vX.py.
    over_write_years -- override value from setup_vX.py.
    exit_on_error -- have program exit on error.
    plot_on_error -- have program plot errors.
    save_plot -- save some plots

    Returns/Creates:
    centers_file -- ASCII file of candidate centers found and kept.
    dumped_centers_file -- ASCII file of candidate centers found and
                           discarded.

    Examples:

    Notes: See bottom of this document for extended notes that are denoted
       in the code. For parallel execution see drive_center_finder.

       If using python version 2.6 and greater we can make use of multiple
       CPUs or multi-core CPUs in a symmetric multi-processing (SMP)
       or shared memory environment.

    Memory Use: Depending on resolution and options expect at least 200MB per
            instance.

    Run Time: With the NCEP Reanalysis I get about 140 timesteps per minute per
          instance. Thus a year takes roughly 10 minutes. This is on a
          Mac Pro with 2.26 GHz processors, 12 GB of RAM, and a 3 disk RAID.

    Author: Mike Bauer  <mbauer@giss.nasa.gov>

    Log:
    2006/12  MB - File created.
    lost track of dates of updates and fixes... sorry
    2008/10  MB - Added input checks, docstring.
    2008/11  MB - Added Polar_Fix to keep N pole from having 40 centers.
    2009/11  MB - Fixed problem on Julian Days for GCMs using noleap calendars.
    2009/11  MB - Reduced memory leak issue my removing year loop.
"""

import sys,os
import defines
import jj_calendar as jjCal

def test_laplacian(test):
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
    """
    # Test case
    if test == 1:
        tgrid = 8149
        tgrids = [7859, 7860, 7861, 7862, 7863, 8003, 8004, 8005,
                  8006, 8007, 8147, 8148, 8149, 8150, 8151, 8291,
                  8292, 8293, 8294, 8295, 8435, 8436, 8437, 8438, 8439]
        tslps = [992600, 989700, 989300, 990500, 992700, 983800, 979200,
                 978200, 980700, 984900, 978100, 972600, 971500, 974200,
                 978500, 980400, 974200, 972700, 975100, 979200, 991200,
                 986100, 984200, 985800, 990100]
        # 9-pnt average around tgrid
        nine_pnt = [979000.0, 977377.777778, 979033.333333, 976744.444444,
                    975377.777778, 977222.222222, 981666.666667,
                    980655.555556, 982277.777778]

        # termA, termB, termC, lap for this field
        aterma = 0.000100564132136
        atermb = 9.41719495596e-05
        atermc = -7.76431575284e-07
        alap = 2.38977684913
    else:
        sys.exit("Error test not defined!")
    return (tgrid,tgrids,tslps,nine_pnt,aterma,atermb,atermc,alap)

def print_region(height,width,area,center,source,
             fmt1="(%06d)",fmt2=" %06d ",local=0,cols=6):
    """Prints the local matrix of area,source around center"""
    fmt = "%% %dd " % (cols)
    k = len(area)-1
    for j in range(height-1,-1,-1):
        if j == height-1:
            print ("  ", end='')
            for jj in range(width):
                print (fmt % (jj), end='')
            print ("")
        print ("%02d" % (j), end='')
        row = []
        for i in range(width):
            row.append(k)
            k -= 1
        row.reverse()
        if local:
            for i in row:
                if area[i] == center:
                    print (fmt1 % (source[i]), end='')
                else:
                    print (fmt2 % (source[i]), end='')
        else:
            for i in row:
                if area[i] == center:
                    print (fmt1 % (source[area[i]]), end='')
                else:
                    print (fmt2 % (source[area[i]]), end='')
        print ("")
    print ("\n")

def main(centers_file, defs_set, dumped_centers_file, imports, 
        over_write_out_path, shared_path, over_write_slp_path,
        loop_year, exit_on_error, plot_on_error, save_plot, import_read,
        save_stats):

    import os, sys

    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}
    
    # --------------------------------------------------------------------------
    # Setup Section
    # --------------------------------------------------------------------------
    for i in imports:
      exec (i, globals())

    defs_v4 = globals()['defs']
    numpy = globals()['numpy']
    strip_read = globals()['strip_read']
    
    # Fetch definitions and impose those set in defs_set.
    defs = defs_v4.defs(**defs_set)
    
    # Predefined data storage
    center_data_type = numpy.dtype(defs.center_data)

    # Pre-bind for speed
    Tree_Traversal = tree_traversal.tree_traversal
    #Pull_Data = pull_data.pull_data
    GCD = gcd.gcd
    G2L = g2l.g2l
    IJ2Grid = ij2grid.ij2grid
    Grid2ij = grid2ij.grid2ij
    Rhumb_Line_Nav = rhumb_line_nav.rhumb_line_nav
    Polar_Fix = polar_fix.polar_fix
    if save_plot or plot_on_error:
        Plot_Map = plot_map.plotmap
        Save_NetCDF = save_netcdf.Save_NetCDF
        Error_Plot = error_plot.error_plot_cf
    if save_stats:
        Save_NetCDF = save_netcdf.Save_NetCDF

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
#Lap comment out if want to screen with and/or change tropical screen.
        #bot = bot_alt
        #top = top_alt
        #tt = [x for x in land_gridids if x not in troubled_centers]
        #troubled_centers.extend(tt)
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

    # Import a bunch of model grid specific information
    #   Note must have run setup_vX.py already!
    fnc_out = []
    cf_file = "%scf_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(cf_file, 'rb'))
        (use_all_lons,search_radius,regional_nys,gdict,rdict,ldict,ijdict,
        min_centers_per_tstep,max_centers_per_tstep,max_centers_per_tstep_change,
        lapp_cutoff,hpg_cutoff) = fnc_out
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (cf_file))

    # Pre-bind object calls for speed.
    N_less = numpy.less; N_greater = numpy.greater
    N_average = numpy.average; N_take = numpy.take
    N_ones = numpy.ones; N_size = numpy.size; N_array = numpy.array
    N_multiply = numpy.multiply; N_sometrue = numpy.sometrue
    N_subtract = numpy.subtract; N_add = numpy.add
    strip_read = strip_read.strip_read
    stored_centers = []; stored_centers_append = stored_centers.append

    # Summary Stats: Checks on operation to report and catch oddities.
    known_flags = {0 : "Passed all filters",
                   1 : "Failed concavity/Laplacian filter",
                   2 : "Failed regional minimum filter",
                   3 : "Failed critical radius filter",
                   4 : "Failed troubled center filter",
                   9 : "Failed polar screen"}
    flag_files = {0 : "passed",
                  1 : "lap",
                  2 : "reg",
                  3 : "crit",
                  4 : "troub",
                  9 : "polar"}
    flag_colors = { 0 : "black",
                    1 : "blue",
                    2 : "yellow",
                    3 : "green",
                    4 : "red",
                    9 : "orange"
                    }
    total_time_steps = 0
    nflags = 10
    # Used flags
    flags_used = [1,2,3,4,9]
    #flags_used = [1,2,3,9]

    # Quit on error else just send message to logfile?
    if exit_on_error:
        do_this = 'print (smsg); print (msg); sys.exit("\t\tDate_Stamp:"+date_stamp)'
    else:
        do_this = 'print (smsg); print (msg); print "\t\tDate_Stamp:"+date_stamp'

##CUT
    ## Temp array for histograms
    #plot_dat_x = []
    #plot_dat_y = []
    #plot_dat_z = []
    #plot_dat_x_append  =plot_dat_x.append
    #plot_dat_y_append = plot_dat_y.append
    #plot_dat_z_append = plot_dat_z.append

    if save_plot:
        fplot = Plot_Map(missing=-10000000000.0,color_scheme="hot_r")

    if plot_on_error or save_plot:
        plot = Plot_Map(clevs=[980,1020,2],cints=[960.0,1013.0],color_scheme="bone")

    inv_accuracy = 1.0/defs.accuracy
    # Counters for report
    total_centers_used = 0
    total_centers_cnt = [0]*nflags # make size of total flag count

    #print "\n=============%d=============" % (loop_year)

    # Define some files
    header = "mcms_%s_%04d_" % (model,loop_year)
    centers_file = "%s%scenters.txt" % (out_path,header)
    dumped_centers_file = "%s%sdumped_centers.txt" % (out_path,header)

    # Open files for storage.
    centers_save = open(centers_file,"w")
    if defs.keep_discards:
        dumped_centers_save = open(dumped_centers_file,"w")
    else:
        dumped_centers_file = ""

    # ---------------------------------------------------------------------
    # Pull in reference field
    # ---------------------------------------------------------------------

    # Open data file, extract data and model definitions
    exec(import_read, globals())
    pull_data = globals()['pull_data']
    fnc = pull_data.pull_data(NetCDF,numpy,slp_path,file_seperator,loop_year,
            defs.read_scale,var_slp,var_time,lat_flip,lon_shift)
    (slp,times,the_time_units) = fnc
    del fnc

    # # Jeyavinoth: Start
    # # comment from here till "Jeyavinoth: End"
    # # getting the dtimes and adates
    # # Work with the time dimension a bit.
    # # This is set in setup_vX.py
    # jd_fake = 0
    # print (" Jimmy the calendar is "+the_calendar)
    # if the_calendar != 'standard':
    #     # As no calendar detected assume non-standard
    #     jd_fake = 1
    #
    # tsteps = len(times)
    #
    # the_time_range = [times[0],times[tsteps-1]]
    # start = "%s" % (the_time_units)
    # tmp = start.split()
    # tmp1 = tmp[2].split("-")
    # tmp2 = tmp[3].split(":")
    # #tmp3 = tmp2[2][0]
    # tmp3 = 0
    # start = "%s %s %04d-%02d-%02d %02d:%02d:%02d" % \
    #         (tmp[0],tmp[1],int(tmp1[0]),int(tmp1[1]),
    #          int(tmp1[2]),int(tmp2[0]),int(tmp2[1]),
    #          int(tmp3))
    # # Warning this could get weird for non-standard
    # # calendars if not set correctly (say to noleap)
    # # in setup_vX.py
    # cdftime = netcdftime.utime(start,calendar=the_calendar)
    # get_datetime = cdftime.num2date
    # dtimes = [get_datetime(times[step]) for step in range(0,tsteps)]
    #
    # # Get Julian Days.. unless GCM uses non-standard calendar in which case
    # #  enumerate with timestep and use uci_stamps for datetime things.
    # # JIMadd
    # jd_fake = True
    #
    # if (the_calendar == 'proleptic_gregorian'):
    #   jd_fake = False
    #
    # # jd_fake = False ######## JJ set this to fake to make it work with leap years
    # if jd_fake:
    #     # Use timesteps rather than dates
    #     # examples '000000000', '000000001'
    #     print ("JIMMY INSIDE jd_fake creation of adates")
    #     print (loop_year)
    #     start_year = over_write_years[0] 
    #     print (start_year)
    #     counter_upper=(loop_year-start_year)*1460
    #     adates = ["%09d" % (x+counter_upper) for x in range(tsteps)]
    #     print (adates)
    #     # Modify output format for timesteps
    #     fmt_1 = "%s %s %05d %05d %06d %07d " # use date_stamp
    #     fmt_2 = "%07d %05d %02d %02d %04d %s%05d%05d %s\n" # use uci_stamp
    #     defs.center_fmt = fmt_1 + fmt_2
    # else:
    #     # Using regular date/times
    #     # examples 244460562, 244971850i
    #     date2jd = netcdftime.JulianDayFromDate
    #     adates = [int(100*date2jd(x,calendar='standard')) for x in dtimes]
    #     # Modify output format for datetimes
    #     fmt_1 = "%s %09d %05d %05d %06d %07d " # use date_stamp
    #     fmt_2 = "%07d %05d %02d %02d %04d %s%05d%05d %s\n" # use uci_stamp
    #     defs.center_fmt = fmt_1 + fmt_2
    #
    # # Jeyavinoth: End
   
    # Jeyavinoth
    # we don't have to set a new format here, 
    # our outputs match the format specified in defs_v4.py
    # code below replaces the above code to get dtimes, date_stamps, and adates
    dtimes, date_stamps, adates = jjCal.get_time_info(the_time_units, times, calendar=the_calendar)

    tsteps = len(times)
    the_time_range = [times[0],times[tsteps-1]]
    
    # copied this over from the above code, to use the correct format for date_stamp and uci_stamp
    fmt_1 = "%s %s %05d %05d %06d %07d " # use date_stamp
    fmt_2 = "%07d %05d %02d %02d %04d %s%05d%05d %s\n" # use uci_stamp
    defs.center_fmt = fmt_1 + fmt_2

    uci_stamps = ['%4d%02d%02d%02d' % (d.year,d.month,d.day,d.hour) for d in dtimes]
    date_stamps = ["%4d %02d %02d %02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]

    if save_plot or save_stats:
        # Files for histogram
#Lap
        #lap_file = centers_file.replace("centers","laplacian")
        #lap_save =  open(lap_file,"w")

        flag_sum = numpy.zeros((jm*im,nflags),dtype=numpy.float)
        flag_cnt = numpy.zeros((jm*im,nflags),dtype=numpy.float)
        ## Uncomment following lines to plot SLP Field to check all is reading
        #splot = Plot_Map(clevs=[960,1040,4],cints=[960.0,1040.0],color_scheme="jet")
        #for step in range(tsteps):
        #    msg = "State at %s UTC" % (date_stamps[step])
        #    msg1 = "%sfigs/%s_slp_field_%s.pdf"
        #    pname = msg1 % (out_path,model,date_stamps[step].replace(" ",""))
        #    splot.create_fig()
        #    slp_step = slp[step,:,:].copy()
        #    slp_step.shape = jm*im
        #    #splot.add_field(lons,lats,slp_step,ptype='pcolor')
        #    splot.add_field(lons,lats,slp_step,ptype='contour')
        #    splot.finish(pname,title=msg)
        #    print ("\tMade figure: %s" % (pname))
        #    # Uncomment break to plot all steps
        #    break
        #del slp_step
        #del splot
    del times
    del dtimes

    # --------------------------------------------------------------------------
    # Main Program Logic
    # --------------------------------------------------------------------------
    # Read SLP field one time step at a time

##CUT
    #tsteps = 2

    last_center_cnt = -1
    for step in range(0,tsteps):

        if plot_on_error or save_plot:
            temp_centers = []
            temp_discards = []
            temp_centers_append = temp_centers.append
            temp_discards_append = temp_discards.append

        adate = adates[step]
        uci_stamp = uci_stamps[step]
        date_stamp = date_stamps[step]

        #print ("Doing",date_stamp)

        # Get SLP field, make 1d integer array. To allow for exact comparisons
        # impose a fixed accuracy (significant digits) via defs.accuracy.
        slp_step = N_multiply(slp[step,:,:].copy(),defs.accuracy)
        slp_step.shape = im*jm
        # Jeyavinoth changed this to int64
        slpint = slp_step.astype(numpy.int64)

        # Check 4 corners of array
        #print (slpint[0],slpint[143],slpint[-144],slpint[-1])

        # If searching for high pressure reverse pressure field so
        # that highs are lows.
        if defs.find_highs:
            slpint = slpint*-1

        # Screen SLP field by defs.plim.
        if defs.plim_filter:
            tmp1 = N_less(slpint,defs.plim_filter)
        else:
            tmp1 = N_ones(N_size(slpint))

        # Screen SLP field in tropics
        if defs.tropical_filter:
            tmp1[bot:top] = 0

        # Apply previous filters and create initial center list
        centers = {}
        for gridid in range(maxid):
            if tmp1[gridid]:
                centers[gridid] = slpint[gridid]

        #----------------------------------------------------------------------
        # Stage 1: Cycle over initial center list, apply more filters and checks
        #----------------------------------------------------------------------
        if not centers:
            err_num = 1
            smsg = "\n\tFail Check %d: No initial centers for this timestep." % (err_num)
            msg = "\t\tlen(centers): %d" % (len(centers))
            if plot_on_error:
                msg1 = "Fail Check %d: No initial centers for this timestep." % (err_num)
                center_loc = []
                discard_loc = []
                Error_Plot("%s/error_%d_%s.png" % (out_path,err_num,adate),
                           plot,slp_step*inv_accuracy,lons,lats,center_loc,discard_loc,msg1)
            exec(do_this)

        total_time_steps += 1 # Got to initial center list

        # Pre bind for some speedup
        kept_centers = []
        kept_centers_append = kept_centers.append

        #print ("\tStage 1 Grid Pool CNT:",len(centers))

        for center in centers:
            # Centers to be kept fall out the bottom
            # of this loop.

            # Use temporary flag for potential problem centers
            # that pass but might bear closer examination.
            temp_flag = 0

            # Retrieve pre-calculated 8 neighboring gridIDs
            upm,upc,upp,cnm,cnt,cnp,dnm,dnc,dnp = gdict[center][:]

            # Screen for along longitude non-minima
            if N_less(slpint[cnm],slpint[center]) or \
                   N_greater(slpint[center],slpint[cnp]):
                continue

            # Screen for along latitude non-minima
            if N_less(slpint[dnc],slpint[center]) or \
                   N_greater(slpint[center],slpint[upc]):
                continue # drop center

            # Screen for diagonal non-minima
            if N_less(slpint[upm],slpint[center]) or \
                   N_greater(slpint[center],slpint[upp]):
                continue # drop center
            else:
                if N_less(slpint[dnm],slpint[center]) or \
                       N_greater(slpint[center],slpint[dnp]):
                    continue # drop center

            # Okay if got here at least a local minima
            total_centers_used += 1

            # DISCOVERY MODE: Turn off (via commenting from DISCOVERY START
            # to  DISCOVERY END and uncommenting the next line down. Allows
            # for center finding without Concavity Test.
            center_laplacian = 0

#LAP when used with trouble_land use as land/sea mask
            #if defs.troubled_filter:
            #    if center in troubled_centers:
            #        total_centers_cnt[4] += 1
            #        if save_plot or save_stats:
            #            flag_cnt[center,4] += 1
            #        if plot_on_error:
            #            temp_discards_append(msg)
            #        continue # drop center

            # DISCOVERY START
            if defs.troubled_filter:
                # Derived SLP Test: SLPs from grids whose surface elevation is
                # above sea level or who have immediate neighbors with that
                # quality are tested with more caution due to the indirect
                # methods used to determine SLP.
                if center in troubled_centers:

                    # Filter to see if center SLP too high implying that SLP
                    # reduction error in play. The value 1020 is based on
                    # examination of 2D histograms of center SLP and the
                    # horizontal SLP gradient from NCEP Reanalysis suggesting
                    # that high SLP centers over land mostly occur over very
                    # high topography (Greenland and Antarctica) and are suspect.
                    if slpint[center] > 1020000:
                        if defs.keep_discards:
                            msg = defs.center_fmt % (date_stamp,adate,
                                                     int((90.0-ijdict[center][3])*100),
                                                     int(ijdict[center][2]*100),
                                                     center,centers[center],0,
                                                     center_laplacian,4,0,0,
                                                     uci_stamp,
                                                     int(round((90.0-
                                                                ijdict[center][3])*100)),
                                                     int(round(ijdict[center][2]*100)),
                                                     defs.usi_template
                                                     )
                            dumped_centers_save.writelines(msg)
                            total_centers_cnt[4] += 1
                            if save_plot or save_stats:
                                flag_cnt[center,4] += 1
                            if plot_on_error:
                                temp_discards_append(msg)
                        continue # drop center

                    # Ring Symmetry Test: Normally the SLP around a cyclone increases
                    #  radially in a fairly smooth and symmetrical way. Errors in SLP
                    #  reduction can create large departures from this and we flag
                    #  these as potentially non-physical results. Found to be the
                    #  result of large relief (absolute topography changes) around
                    #  the center rather than just high topography.
                    ring = numpy.take(slpint,gdict[center][:])
                    ring_slp_diff = [x - ring[4] for x in ring]
                    tmp = ring_slp_diff[:]
                    tmp.sort()
                    # Find HPG (horizontal pressure gradient hPa/km)
                    clon = ijdict[center][2]
                    clat = ijdict[center][3]
                    bit = ring_slp_diff.index(tmp[-1])
                    bite_high = gdict[center][bit]
                    # Find Horizontal Pressure Gradient
                    rlon = ijdict[bite_high][2]
                    rlat = ijdict[bite_high][3]
                    distx = GCD(clon,clat,rlon,rlat)
                    # Take the steepest gradient for comparison.
                    hpg_high = tmp[-1]/distx

                    # Holton says the horizontal pressure gradient is on the
                    # order of 0.01 hPa/km.The NCEP Reanalysis suggests that
                    # overland HPG above this value are often in areas of
                    # high relief and/or high topography.
                    # Find the Absolute HPG

                    # Save HPG for post analysis uncomment save lap below
                    #lap_save.writelines("%f " % (abs(hpg_high)*inv_accuracy))

                    if abs(hpg_high)*inv_accuracy > hpg_cutoff: # make hPa/km
                        if defs.keep_discards:
                            msg = defs.center_fmt % (date_stamp,adate,
                                                     int((90.0-ijdict[center][3])*100),
                                                     int(ijdict[center][2]*100),
                                                     center,centers[center],0,
                                                     center_laplacian,4,0,0,
                                                     uci_stamp,
                                                     int(round((90.0-
                                                                ijdict[center][3])*100)),
                                                     int(round(ijdict[center][2]*100)),
                                                     defs.usi_template
                                                     )
                            dumped_centers_save.writelines(msg)
                            total_centers_cnt[4] += 1
                            if save_plot or save_stats:
                                flag_cnt[center,4] += 1
                            if plot_on_error:
                                temp_discards_append(msg)
                        continue # drop center

            # Concavity Test: See Note 1

            # Uncomment test_lap to check algorithm (not related to slp source!).
            #test_lap = 1
            #if test_lap:
            #    ltest = 1
            #    center,tgrids,tslps,nine_pnt,aterma,atermb,atermc,alap = test_laplacian(ltest)
            #    i = 0
            #    for each in tgrids:
            #        slpint[each] = tslps[i]
            #        i += 1
            #    print ("\n\nLaplacian Test: Source")
            #    print_region((5,5,tgrids,center,slpint))

            # Find 9-pnt average SLP for each of the 9-pnts around center.
            all_nine = gdict[center][:]
            nine_pnt_aves = []
            nine_pnt_aves_append = nine_pnt_aves.append # prebind for speedup
            for eachone in all_nine:
                nine_pnt_aves_append(N_average(N_take(
                    slpint,gdict[eachone][:])))

            #if test_lap:
            #    if abs(sum(nine_pnt) - sum(nine_pnt_aves)) > 0.1:
            #        smsg = "\n\tFailed Laplacian Test %d: 9-pnt Ave" % (ltest)
            #        msg = ""
            #        print ("Got")
            #        print_region((3,3,all_nine,center,nine_pnt_aves,fmt1="(%08.2f)",fmt2=" %08.2f ",cols=10,local=1))
            #        print ("Wanted")
            #        print_region((3,3,all_nine,center,nine_pnt,fmt1="(%08.2f)",fmt2=" %08.2f ",cols=10,local=1))
            #        exec(do_this)
            #    else:
            #        print ("Passed Laplacian Test %d: 9-pnt Ave" % (ltest))

            # Find 9-pnt Laplacian of the averaged SLPs. See Note 2
            center_laplacian = 0
            if ldict[center][0]: # non-polar (90 degrees)

                # Scale pressures back to hPa
                nine_pnt_aves = [x*inv_accuracy for x in nine_pnt_aves]

                # 1/a^2sin^2(lat) * d^2P/dlon^2
                termA = ldict[center][1] * (nine_pnt_aves[3] -
                                            2.0*nine_pnt_aves[4] +
                                            nine_pnt_aves[5]) / dlon_sq
                # 1/a^2 * d^2P/dlat^2
                termB = defs.inv_earth_radius_sq * ((nine_pnt_aves[1] -
                                                     2.0*nine_pnt_aves[4] +
                                                     nine_pnt_aves[7])/
                                                    dlat_sq)
                # cot(lat)/a^2 * dP/dlat
                termC = ldict[center][2] * (nine_pnt_aves[1] -
                                            nine_pnt_aves[7]) / two_dlat

                lapp = defs.two_deg_lat*(termA + termB + termC) # hPa/lat^2
#Lap Save laplacian for post analysis
                #lap_save.writelines("%f " % (lapp))

                #if test_lap:
                #    print "\n9-pnt Ave"
                #    print_region(3,3,all_nine,center,nine_pnt,fmt1="(%08.2f)",fmt2=" %08.2f ",cols=10,local=1)
                #    if abs(lapp-alap) > 0.01:
                #        smsg = "\nFailed Laplacian Test %d: Laplacian" % (ltest)
                #        msg = ""
                #        print "Got:",lapp
                #        print "Wanted:",alap
                #        print "termA:",termA
                #        print "termB:",termB
                #        print "termC:",termC
                #        exec(do_this)
                #    else:
                #         print "Passed Laplacian Test %d: Laplacian" % (ltest)

                # Scale for saving
                center_laplacian = int(lapp*1000.0)

                if lapp < lapp_cutoff:
                #if lapp < 0.15:
                    if defs.keep_discards:
                        msg = defs.center_fmt % (date_stamp,adate,
                                                  int((90.0-ijdict[center][3])*100),
                                                 int(ijdict[center][2]*100),
                                                 center,centers[center],0,
                                                 center_laplacian,1,0,0,
                                                 uci_stamp,
                                                 int(round((90.0-
                                                            ijdict[center][3])*100)),
                                                 int(round(ijdict[center][2]*100)),
                                                 defs.usi_template
                                                 )
                        dumped_centers_save.writelines(msg)
                        total_centers_cnt[1] += 1
                        if save_plot or save_stats:
                            flag_cnt[center,1] += 1
                        if plot_on_error:
                            temp_discards_append(msg)
                    continue # drop center
            # DISCOVERY END

            # Calculate regional_average SLP (pyhack)
            slp_ave = int(N_average(N_take(slpint,rdict[center])))

            ## out for raw
            ## Check center is also a regional minimum, which means
            ## it's the lowest-or equal SLP within a great circle
            ## radius of (defs.critical_radius).
            #not_reg_min = False
            #if N_sometrue(N_greater(slpint[center],
            #                        N_take(slpint,rdict[center])
            #                        +defs.regional_slp_threshold)):
            #    if defs.keep_discards:
            #        msg = defs.center_fmt % (date_stamp,adate,
            #                                 int((90.0-ijdict[center][3])*100),
            #                                 int(ijdict[center][2]*100),
            #                                 center,centers[center],slp_ave,
            #                                 center_laplacian,2,0,0,
            #                                 uci_stamp,
            #                                 int(round((90.0-
            #                                            ijdict[center][3])*100)),
            #                                 int(round(ijdict[center][2]*100)),
            #                                 defs.usi_template
            #                                 )
            #        dumped_centers_save.writelines(msg)
            #    total_centers_cnt[2] += 1
            #    if save_plot or save_stats:
            #        flag_cnt[center,2] += 1
            #    if plot_on_error:
            #        temp_discards_append(msg)
            #    not_reg_min = True
            #if not_reg_min:
            #    continue
            ## out for raw

            kept_centers_append((center,centers[center],ijdict[center][3],
                                 ijdict[center][2],slp_ave,center_laplacian,
                                 temp_flag))

        #-----------------------------------------------------------------------
        # Stage 2: Cycle over centers that passed Stage 1. Reduce the center
        # list to contain only a single center within defs.critical_radius of
        # each other.
        #-----------------------------------------------------------------------
        #msg1 = "\tStage 2 Center CNT: %d from %d candidates"
        #print msg1 % (len(kept_centers),total_centers_used)
        #msg1 = "\t\t% 3d %s"
        #for e in flags_used:
        #    print msg1 % (total_centers_cnt[e],known_flags[e])
        
        if not kept_centers:
            err_num = 2
            smsg = "\n\tFail Check %d: No kept centers for this timestep." % (err_num)
            msg = "\t\tlen(kept_centers): %d" % (len(kept_centers))
            if plot_on_error:
                msg1 = "Fail Check %d: No kept centers for this timestep." % (err_num)
                center_loc = []
                discard_loc = []
                for c in temp_centers:
                    parts = c.split()
                    llon = int(parts[6])*0.01
                    llat = 90.0 - int(parts[5])*0.01
                    center_loc.append((llon,llat))
                for c in temp_discards:
                    parts = c.split()
                    llon = int(parts[6])*0.01
                    llat = 90.0 - int(parts[5])*0.01
                    discard_loc.append((llon,llat))
                Error_Plot("%s/error_%d_%s.png" % (out_path,err_num,adate),
                           plot,slp_step*inv_accuracy,lons,lats,center_loc,discard_loc,msg1)
            exec(do_this)

        # out for raw
        # Remove all but one center if at such high latitude that all longitudes
        # fit within defs.critical_radius. Can be done even with wavenumber based
        # radius because possibility of many centers along longitude.
        # Check if polar rows (can set use_all_lons = [] above to skip this check)
        if len(use_all_lons):
            kept_centers,dumped = Polar_Fix(use_all_lons,kept_centers,row_end)
            for cdump in dumped:
                msg = defs.center_fmt % (date_stamp,adate,
                                         int((90.0-cdump[2])*100),
                                         int(cdump[3]*100),cdump[0],cdump[1],cdump[4],
                                         cdump[5],9,0,0,
                                         uci_stamp,
                                         int(round(90.0-cdump[2])*100),
                                         int(round(cdump[3]*100)),defs.usi_template)
                total_centers_cnt[9] += 1
                if save_plot or save_stats:
                    flag_cnt[int(cdump[0]),9] += 1
                if plot_on_error:
                    temp_discards_append(msg)
                dumped_centers_save.writelines(msg)
        # out for raw

        # Find fractional grid positions based on fitting a parabolic function
        # to the local slp field.
        new_kept_centers = []
        new_kept_centers_append = new_kept_centers.append
        for g in kept_centers:
            upm,upc,upp,cnm,cnt,cnp,dnm,dnc,dnp = gdict[g[0]][:]
            numerator = N_subtract(slpint[cnm],slpint[cnp])
            denominator = N_subtract(N_add(slpint[cnm],
                                           slpint[cnp]),2*slpint[g[0]])
            if denominator == 0:
                factor = 0.0 # use original grid
            else:
                factor = 0.5 * float(numerator)/float(denominator)
                # This happens because of adjacent equality
                if factor > 0.5:
                    factor = 0.5
                if factor < -0.5:
                    factor = -0.5
            final_x = factor + ijdict[g[0]][0]
            if final_x < 0.0: # wrap around
                final_x = (im-1) + final_x

            numerator = N_subtract(slpint[dnc],slpint[upc])
            denominator = N_subtract(N_add(slpint[dnc],slpint[upc]),
                                     2*slpint[g[0]])
            if denominator == 0:
                factor = 0.0 # use original grid
            else:
                factor = 0.5 * float(numerator)/float(denominator)
                # This happens because of adjacent equality
                if factor > 0.5:
                    factor = 0.5
                if factor < -0.5:
                    factor = -0.5
            final_y = factor + ijdict[g[0]][1]
            if final_y > jm-1:
                final_y = jm-1
            if final_y < 0.0:
                final_y = 0

            new_kept_centers_append((g[0],g[1],int(final_y*100),
                                     int(100*final_x),g[4],g[5],g[6]))
        kept_centers = new_kept_centers

        # out for raw
        # Step 3: See Note 3 at bottom of this file

        # Dictionary all uci for each center that fall w/in search_radius.
        center_tree  = {}
        for test_center in kept_centers:
            # Which latitude row is center in?
            for rowe in row_end:
                if test_center[0] <= rowe:
                    row = row_end.index(rowe)
                    break

            # Use fractional grid positions.
            # At high lats, better than grid-centers
            tci = float(test_center[3])*0.01
            tcj = float(test_center[2])*0.01
            tclon = G2L(tci,start_lon,start_lat,dlon,dlat,jm,
                            "lon","free",False,True,faux_grids)
            tclat = G2L(tcj,start_lon,start_lat,dlon,dlat,jm,
                            "lat","free",False,True,faux_grids)

            # Other close by centers?
            embeded = []
            embeded_append = embeded.append
            for embeded_center in kept_centers:
                if embeded_center[0] != test_center[0]:
                    # Use fractional grid positions.
                    # At high lats, better than grid-centers
                    eci = float(embeded_center[3])*0.01
                    ecj = float(embeded_center[2])*0.01
                    eclon = G2L(eci,start_lon,start_lat,dlon,dlat,jm,
                                "lon","free",False,True,faux_grids)
                    eclat = G2L(ecj,start_lon,start_lat,dlon,dlat,jm,
                                "lat","free",False,True,faux_grids)
                    if defs.use_gcd:
                        distx = GCD(tclon,tclat,eclon,eclat)
                    else:
                        fnc = Rhumb_Line_Nav(eclon,eclat,tclon,tclat,True)
                        distx = fnc[1]

                    if distx < search_radius[row]: # neighbor
                        if embeded_center[0] not in embeded:
                            embeded_append(embeded_center)
                else:
                    if embeded_center[0] not in embeded:
                        embeded_append(test_center)
                center_tree[test_center[0]] = embeded

        # Traverse the tree of inter-referencing centers in center_tree.
        linked_centers = {}
        ctree_keys = list(center_tree.keys())
        ctree_keys.sort()
        # for test_center in center_tree.keys(): # center A
        for test_center in ctree_keys: # center A
            harvest = {}
            Tree_Traversal(test_center,center_tree,harvest)
            linked_centers[test_center] = harvest
 
        # Traverse linked_centers for each center to see if in used_or_discarded
        # if not then for each also not in used_or_discarded rank by lowest slp
        # and then start of add to used list
        lost_centers = []
        used_or_discarded = [] # centers not to be used again
        used = [] # centers to be kept
        lc_keys = list(linked_centers.keys())
        lc_keys.sort()
        # for test_center in linked_centers:
        for test_center in lc_keys:
            # A center can only be used once
            if test_center not in used_or_discarded:

                # For each linked center see if it is unused,
                # if so make list of these slps
                # list of slps
                inner_centers = [x for x in linked_centers[test_center]
                                if x not in used_or_discarded]
                slps = []
                slps = [linked_centers[test_center][x] for x in inner_centers]
                # Only unique values
                u = {}
                for x in slps:
                    u[x] =  1
                slps = list(u.keys())
                # Order slps
                slps.sort()

                # Starting with the lowest SLP exclude all centers overlapping
                # that center. Note that there could be ties by slp value in
                # this case just take the middle center for the lowest slps.
                for lowest in slps:
                    keys = []
                    keys = [x for x in linked_centers[test_center]
                            if linked_centers[test_center][x] == lowest]
                    if len(keys) > 1:
                        if len(keys)%2:
                            middle = int(len(keys)*0.5)-1
                        else:
                            middle = int(len(keys)*0.5)-1
                        # Tie(s), drop all but the middle entry
                        for xx in keys:
                            if keys.index(xx) != middle:
                                if xx not in used_or_discarded:
                                    used_or_discarded.append(xx)
                    # Use this center
                    key = [x for x in keys if x not in used_or_discarded]
                    if key:
                        if key[0] not in used:
                            used.append(key[0])
                        if key[0] not in used_or_discarded:
                            used_or_discarded.append(key[0])
                            # Discard all centers w/in search radius of this
                            # center from further consideration.
                            for each in linked_centers[key[0]].keys():
                                if each not in used_or_discarded:
                                    used_or_discarded.append(each)
        if defs.keep_discards:
            lost_centers = [x for x in kept_centers if x[0] not in used]

        kept_centers = [x for x in kept_centers[:] if x[0] in used]

        # Save these centers to disk
        for g in lost_centers:
            msg = defs.center_fmt % (date_stamp,adate,
                                     int((90.0-ijdict[g[0]][3])*100),
                                     int(ijdict[g[0]][2]*100),
                                     g[0],g[1],g[4],g[5],3,0,0,
                                     uci_stamp,
                                     int(round((90.0-ijdict[g[0]][3])*100)),
                                     int(round(ijdict[g[0]][2]*100)),
                                     defs.usi_template
                                     )
            total_centers_cnt[3] += 1
            if save_plot or save_stats:
                flag_cnt[int(g[0]),3] += 1
            if plot_on_error:
                temp_discards_append(msg)
            dumped_centers_save.writelines(msg)
        # out for raw

        # Save these centers to disk as potential cyclones
        for g in kept_centers:
            # Find fractional location of center
            flon = G2L(g[3]*0.01,start_lon,start_lat,dlon,dlat,jm,
                           "lon","free",False,True,faux_grids)
            flat = 90.0 - G2L(g[2]*0.01,start_lon,start_lat,dlon,dlat,jm,
                                  "lat","free",False,True,faux_grids)
            msg = defs.center_fmt % (date_stamp,adate,
                                     int(flat*100),int(flon*100),
                                     g[0],g[1],g[4],g[5],g[6],0,0,
                                     uci_stamp,
                                     int(round((90.0-ijdict[g[0]][3])*100)),
                                     int(round(ijdict[g[0]][2]*100)),
                                     defs.usi_template
                                     )
            total_centers_cnt[0] += 1
            if save_plot or save_stats:
                flag_cnt[int(g[0]),0] += 1
            if plot_on_error or save_plot:
                temp_centers_append(msg)
            centers_save.writelines(msg)

        # Plot timestep
        if save_plot:
            # set to step < tsteps+1 to do every step
            if step < 1:
                err_num = 0
                msg1 = "Kept %d of %d centers on %s." % (len(kept_centers),total_centers_used,date_stamp)
                center_loc = []
                discard_loc = []
                d_colors = []
                c_colors = []
                for c in temp_centers:
                    parts = c.split()
                    llon = int(parts[6])*0.01
                    llat = 90.0 - int(parts[5])*0.01
                    center_loc.append((llon,llat))
                    c_colors.append(flag_colors[int(parts[11])])
                for c in temp_discards:
                    parts = c.split()
                    llon = int(parts[6])*0.01
                    llat = 90.0 - int(parts[5])*0.01
                    discard_loc.append((llon,llat))
                    d_colors.append(flag_colors[int(parts[11])])
                msg1 = "%sfigs/%s_center_finder_%s.png"
                pname = msg1 % (out_path,model,date_stamps[step].replace(" ",""))
                Error_Plot(pname,plot,slp_step*inv_accuracy,lons,lats,center_loc,
                           discard_loc,pname,c_colors,d_colors)
                print ("\tMade figure: %s" % (pname))

#tmp
        #if step == 6:
        #    break

        # # Sanity Check: Flag potential problems.
        #k_centers = len(kept_centers)
        #if k_centers <= min_centers_per_tstep:
        #    err_num = 3
        #    smsg = "\n\tFail Check %d: Too few centers for this timestep." % (err_num)
        #    msg = "\t\tlen(k_centers): %d" % (k_centers)
        #    exec(do_this)
        #if k_centers >= max_centers_per_tstep:
        #    err_num = 4
        #    smsg = "\n\tFail Check %d: Too many centers for this timestep." % (err_num)
        #    msg = "\t\tlen(k_centers): %d" % (k_centers)
        #    exec(do_this)
        #if last_center_cnt > 0:
        #     #ttest = abs(last_center_cnt - k_centers)
        #     #if ttest >= max_centers_per_tstep_change:
        #     #    err_num = 5
        #     #    smsg = "\n\tFail Check %d: Too much change in center count this and previous timestep." % (err_num)
        #     #    msg = "\t\tlen(k_centers): %d\n\t\tlen(last_center_cnt): %d" % (k_centers,last_center_cnt)
        #     #    exec(do_this)
        #    # Warn if last center count doubled/halved to this center count
        #    double = round(last_center_cnt*0.6)
        #    ttest = abs(last_center_cnt - k_centers)
        #    if ttest >= double:
        #        err_num = 5
        #        smsg = "\n\tFail Check %d: Too much change in center count this and previous timestep." % (err_num)
        #        msg = "\t\tlen(k_centers): %d\n\t\tlen(last_center_cnt): %d\n\t\tdouble: %d" % (k_centers,last_center_cnt,double)
        #        exec(do_this)

##CUT
        #if last_center_cnt > 0:
        #    plot_dat_x_append(k_centers)
        #    plot_dat_y_append(double)
        #    plot_dat_z_append(ttest)
        #last_center_cnt = k_centers

        #msg1 = "\tFinal Center CNT: %d from %d candidates where"
        #print msg1 % (len(kept_centers),total_centers_used)
        #msg1 = "\t\t% 3d %s"
        #for e in flags_used:
        #    print msg1 % (total_centers_cnt[e],known_flags[e])
    # -------------------------------------------------------------------------
    # Clean up
    # -------------------------------------------------------------------------

    # Close open files
    centers_save.close()
    if defs.keep_log:
        log_file.close()
        sys.stdout = screenout # redirect stdout back to screen
    if defs.keep_discards:
        dumped_centers_save.close()

    #
    # FINAL check to be sure all timesteps run and all centers accounted for.
    #
    report_file = centers_file.replace("centers.txt","centers_report.txt")
    report_file = report_file.replace(out_path,"%sstats/" % (out_path))
    report_save = open(report_file,"w")

    report_save.writelines("%d\n" % (loop_year))
    msg1 = "Final Center CNT: %d (%6.2f%%) from %d candidates where\n"
    msg = msg1 % (total_centers_cnt[0],
                  100.0*(float(total_centers_cnt[0])/float(total_centers_used)),
                  total_centers_used)
    # Last minute check that reasonable count.
    if total_centers_cnt[0] < 10*tsteps:
        err_num = 6
        smsg = "\n\tFail Check %d: Final Center CNT < 10*tsteps" % (err_num)
        msg = "\t\tFinal Center CNT: %d < 10*tsteps %d " % (total_centers_cnt[0],10*tsteps)
        date_stamp = "Full Record"
        exec(do_this)
    report_save.writelines(msg)
    msg1 = "\t% 6d\t(%6.2f%%)\t%s\n"
    for e in flags_used:
        msg = msg1 % (total_centers_cnt[e],
                      100.0*(float(total_centers_cnt[e])/float(total_centers_used)),
                      known_flags[e])
        report_save.writelines(msg)
    if total_centers_used != sum(total_centers_cnt):
        msg = "%d Total Count Error:\n\ttotal_centers_used = %d\n\ttotal_centers_cnt = %s sum(%d)"
        sys.exit(msg % (loop_year,total_centers_used,repr(total_centers_cnt),
                        sum(total_centers_cnt)))
    report_save.close()

    if save_plot or save_stats:
        # Make frequency plot
        for flag in flag_files:
            # Just counts
            # FIX error with numpy/matplot lib and missing so just set to zero now
            comp_out = numpy.where(flag_cnt[:,flag] < 1.,-10000000000.0,flag_cnt[:,flag])
            comp_out = numpy.where(flag_cnt[:,flag] < 1.,0.0,flag_cnt[:,flag])
            pname = "%sfigs/%s_freq_%s_%d.png" % (out_path,model,flag_files[flag],loop_year)
            if save_plot:
                fplot.create_fig()
                fplot.add_field(lons,lats,comp_out,ptype='pcolor',)
                fplot.finish(pname)
                #print "\tMade figure %s" % (pname)
            if save_stats:
                pname = pname.replace(".png",".nc")
                pname = pname.replace("figs","netcdfs")
                save_it = Save_NetCDF(flag_cnt[:,flag],lons,lats,pname,0)
                #print "\tCreated file %s" % (pname)
                del save_it
            del comp_out
#Lap
    #lap_save.close()

##CUT
## Plot temp array histograms
## for plotting
#import matplotlib.pyplot as plt
#pname = "%splot_dat_x.png" % (out_path)
#fig = plt.figure()
#n, bins, patches = plt.hist(plot_dat_x,50, normed=1,facecolor='green',alpha=0.75)
#plt.grid(True)
#fig.savefig(pname,dpi=144)
#print "Created %s" % (pname)
#tmp = numpy.array(plot_dat_x)
#print "\tMin: %f Max: %f Mean: %f" %(tmp.max(),tmp.min(),tmp.mean())
#plt.close('all')
#pname = "%splot_dat_y.png" % (out_path)
#fig = plt.figure()
#n, bins, patches = plt.hist(plot_dat_y,50, normed=1,facecolor='green',alpha=0.75)
#plt.grid(True)
#fig.savefig(pname,dpi=144)
#print "Created %s" % (pname)
#tmp = numpy.array(plot_dat_y)
#print "\tMin: %f Max: %f Mean: %f" %(tmp.max(),tmp.min(),tmp.mean())
#plt.close('all')
#pname = "%splot_dat_z.png" % (out_path)
#fig = plt.figure()
#n, bins, patches = plt.hist(plot_dat_z,50, normed=1,facecolor='green',alpha=0.75)
#plt.grid(True)
#fig.savefig(pname,dpi=144)
#print "Created %s" % (pname)
#tmp = numpy.array(plot_dat_z)
#print "\tMin: %f Max: %f Mean: %f" %(tmp.max(),tmp.min(),tmp.mean())
#plt.close('all')
##pname = "%shisto2d.png" % (out_path)
##fig = plt.figure()
##x = numpy.array(plot_dat_z)
##xmin = x.min()
##xmax = x.max()
##y = numpy.array(plot_dat_y)
##ymin = y.min()
##ymax = y.max()
##gridsize = int(xmax-xmin)
##plt.hexbin(plot_dat_z,plot_dat_y,gridsize=gridsize)
##plt.axis([xmin, xmax, ymin, ymax])
##fig.savefig(pname,dpi=144)
##print "Created %s" % (pname)
##plt.close('all')

    # Save memory when pull_data called in loop stores a copy of slp
    #  and thus doubles the memory footprint of the code.
    del pull_data,slpint,slp_step,slp

    # Jeyavinoth
    # we don't seem to use the variables named "start", "tmp2", "tmp3", "cdftime" 
    # it was something I commented out before
    # so I change the followning line 
    # del tsteps,the_time_range,start,tmp1,tmp2,tmp3,cdftime
    # with: 
    del tsteps,the_time_range,tmp1

    del adates,uci_stamps,date_stamps
    if plot_on_error or save_plot:
        del plot_map,Plot_Map,fplot,plot,Error_Plot

    # Exit
    msg = "Finished %d" % (loop_year)
    return (msg)

# --------------------------------------------------------------------------
# Done. Below is a special case when center_finder_main can be called
# directly (rather than via a driver) for debugging and such. Not normally
# used, but works perfectly albeit on a single processor.
#
# NOTES are at the very bottom of the file.
# --------------------------------------------------------------------------

#---Start of main code block.
if __name__=='__main__':
    import pickle

    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------

    # This next set of lines should be copied from setup_vX.py
    # Short names by which model will be labeled.
    model = defines.model

    # Halt program on error or just warn?
    exit_on_error = 0

    # Plot map on error (requires matplotlib, also doubles or more memory
    # footprint)
    plot_on_error = 0

    # Plot Stats (debugging mostly,requires matplotlib, also
    # doubles or more memory footprint)
    save_plot = 0

    # Save debugging data for post analysis.
    # Note to make unified plot of save_plot data see big_one.py
    save_stats = 0

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Basic standard Python modules to import.
    imports = []
    # Jeyavinoth: Removed netcdftime from line below
    # system_imports = "import math,numpy,netcdftime,pickle"
    system_imports = "import math,numpy,pickle"
    imports.append(system_imports)
    imports.append("import netCDF4 as NetCDF")


    # My modules to import w/ version number appended.
    my_base = ["tree_traversal","defs","gcd","g2l","ij2grid",
            "grid2ij","rhumb_line_nav","polar_fix","strip_read"]
    if save_plot or plot_on_error:
        my_base.append("save_netcdf")
        my_base.append("plot_map")
        my_base.append("error_plot")
    if save_stats and "save_netcdf" not in my_base:
        my_base.append("save_netcdf")
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
    # Full path to the root directory where model specific output will be stored.
    result_directory = defines.out_folder

    if not os.path.exists(result_directory):
        sys.exit("ERROR: result_directory not found.")

    # Directory to be created for storing temporary model specific files.
    shared_path = "%s%s_files/" % (result_directory,model)

    # The default behavior is to run over all the
    # years found by setup_vX.py. Here you can
    # elect to override this behavior.
    # example of hard-coded years:
    # over_write_years = [2010,2010]
    over_write_years = defines.over_write_years 

    # Here you can alter the default behavior as determined
    # by defs_vX.py and possibly setup_vX.py.

    defs_set = {"keep_log":False,"troubled_filter":True,
                "tropical_filter":True,"read_scale":1.0}

    # Define some files
    centers_file = "centers.txt"
    dumped_centers_file = "dumped_centers.txt"

    # --------------------------------------------------------------------------
    # Run main()
    # --------------------------------------------------------------------------

    msg = "\n\t====\tCenter Finding\t===="
    print (msg)
    if over_write_slp_path:
        print ("\tUsing over_write_slp_path: %s" % (over_write_slp_path))
    else:
        print ("\tUsing default slp_path")
    if over_write_out_path:
        print ("\tUsing over_write_out_path: %s" % (over_write_out_path))
    else:
        print ("\tUsing default out_path")
    if not os.path.exists(shared_path):
        print (shared_path)
        sys.exit("\tCan't find shared_path!")
    else:
        print ("\tUsing shared_path: %s" % (shared_path))
    if over_write_years:
        print ("\tUsing over_write_years: %s" % (repr(over_write_years)))
    else:
        print ("\tUsing default years")
    if defs_set:
        print ("\tUsing modified defs for defs_vX.py:")
        for d in defs_set:
            print ("\t\t%20s:\t%s" % (d,defs_set[d]))
    else:
        print ("\tUsing defaults from defs_vX.py")

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

    # Create out_path if it doesn't exist.
    print (out_path)
    if not os.path.exists(out_path):
        dirs = list(map(os.makedirs, (out_path,
        out_path+'/comps/',
        out_path+'/pdfs/',
        out_path+'/stats/',
        out_path+'/stats/tmp/',
        out_path+'/netcdfs/',
        out_path+'/figs/pdfs/',
        out_path+'/figs/comps/')))
        print ("\tDirectory %s Created." % (out_path))

    # -------------------------------------------------------------------------
    # Start Main Loop over super_years
    # -------------------------------------------------------------------------

    # This is a single processor version
    for loop_year in range(int(super_years[0]),int(super_years[-1])+1):
        print ("\n\t=============%d=============" % (loop_year))
        msg = main(centers_file, defs_set, dumped_centers_file, imports, 
                out_path, shared_path, over_write_slp_path, loop_year, exit_on_error,
                plot_on_error, save_plot, import_read,save_stats)
        print (msg)

    total_cnt = 0
    candidates = 0
    lap_cnt = 0
    reg_cnt = 0
    rad_cnt = 0
    trb_cnt = 0
    pol_cnt = 0
    verbose = 0

    report_file = "%sstats/mcms_%s_center_final_report_%d-%d.txt"
    report_file = report_file % (out_path,model,int(super_years[0]),int(super_years[-1]))
    print ("\tCreating",report_file)
    try:
        report_save = open(report_file,"w")
    except:
        sys.exit("Error opening: %s" % (report_file))
    report_save.writelines("%d--%d\n" % (int(super_years[0]),int(super_years[-1])))
    big_buffer = {}
    # Read partial reports
    iyear = 0
    for loop_year in range(int(super_years[0]),int(super_years[-1])+1):
        r_buffer = []
        r_file = "%sstats/mcms_%s_%d_centers_report.txt" % (out_path,model,loop_year)
        if verbose:
            print ("\tAdding",r_file)
        try:
            r_read = open(r_file,"r")
        except:
            sys.exit("Error opening: %s" % (r_file))
        for line in r_read:
            r_buffer.append(line)
        r_read.close()
        big_buffer[iyear] = r_buffer
        iyear += 1
    iyears = iyear
    for iyear in range(iyears):
        main_line = big_buffer[iyear][1]
        args = main_line.split(" ")
        # Remove any empty strings....
        args = [x for x in args if x]
        if verbose:
            print ("\n\tYear", big_buffer[iyear][0],)
            print ("\tmain_line:",main_line,)
            print ("\targs:",args)

        # if percentage == '(100.00%)' 8 args if '( 99.99%)' 9
        if len(args) == 8:
            total_cnt += int(args[3])
            candidates += int(args[6])
        else:
            total_cnt += int(args[3])
            candidates += int(args[7])
        if verbose:
            print ("\tTweaked:",args)
            print ("\ttotal_cnt:",total_cnt)
            print ("\tcandidates:",candidates)

        if candidates > 0:
            fraction = 100.0*(float(total_cnt)/float(candidates))
        else:
            fraction = 0.0
        f = "%6.2f%%)" % (fraction)
        if verbose:
            print ("\tfraction:",fraction)

        lap = big_buffer[iyear][2]
        brgs = lap.split(" ")
        # Remove any empty strings....
        brgs = [x for x in brgs if x]
        aa = brgs[1].split("\t")
        lap_cnt += int(aa[0])

        reg = big_buffer[iyear][3]
        brgs = reg.split(" ")
        # Remove any empty strings....
        brgs = [x for x in brgs if x]
        aa = brgs[1].split("\t")
        reg_cnt += int(aa[0])

        rad = big_buffer[iyear][4]
        brgs = rad.split(" ")
        # Remove any empty strings....
        brgs = [x for x in brgs if x]
        aa = brgs[1].split("\t")
        rad_cnt += int(aa[0])

        trb = big_buffer[iyear][5]
        brgs = trb.split(" ")
        # Remove any empty strings....
        brgs = [x for x in brgs if x]
        aa = brgs[1].split("\t")
        trb_cnt += int(aa[0])

        pol = big_buffer[iyear][6]
        brgs = pol.split(" ")
        # Remove any empty strings....
        brgs = [x for x in brgs if x]
        aa = brgs[1].split("\t")
        pol_cnt += int(aa[0])

        if verbose:
            print ("\tlap",lap,)
            print ("\treg",reg,)
            print ("\trad",rad,)
            print ("\ttrb",trb,)
            print ("\tpol",pol)

        if iyear == iyears-1:
            if len(args) == 8:
                args[6] = str(candidates)
                args[3] = str(total_cnt)
            else:
                args[3] = str(total_cnt)
                args[7] = str(candidates)
            args[5] = f
            msg = " ".join(args)
            report_save.writelines(msg)
            if verbose:
                print (msg)

            msg = lap.split(" ")
            # Remove any empty strings....
            msg = [x for x in msg if x]
            a = '% d\t(' % (lap_cnt)
            msg[1] = a
            if candidates > 0:
                fraction = 100.0*(float(lap_cnt)/float(candidates))
            else:
                fraction = 0.0
            f = "%6.2f%%)\tFailed" % (fraction)
            msg[2] = f
            smsg =  " ".join(msg)
            report_save.writelines(smsg)
            if verbose:
                print (smsg)

            msg = reg.split(" ")
            # Remove any empty strings....
            msg = [x for x in msg if x]
            a = '% d\t(' % (reg_cnt)
            msg[1] = a
            if candidates > 0:
                fraction = 100.0*(float(reg_cnt)/float(candidates))
            else:
                fraction = 0.0
            f = "%6.2f%%)\tFailed" % (fraction)
            msg[2] = f
            smsg =  " ".join(msg)
            report_save.writelines(smsg)
            if verbose:
                print (smsg)

            msg = rad.split(" ")
            # Remove any empty strings....
            msg = [x for x in msg if x]
            a = '% d\t(' % (rad_cnt)
            msg[1] = a
            if candidates > 0:
                fraction = 100.0*(float(rad_cnt)/float(candidates))
            else:
                fraction = 0.0
            f = "%6.2f%%)\tFailed" % (fraction)
            msg[2] = f
            smsg =  " ".join(msg)
            report_save.writelines(smsg)
            if verbose:
                print (smsg)

            msg = trb.split(" ")
            # Remove any empty strings....
            msg = [x for x in msg if x]
            a = '% d\t(' % (trb_cnt)
            msg[1] = a
            if candidates > 0:
                fraction = 100.0*(float(trb_cnt)/float(candidates))
            else:
                fraction = 0.0
            f = "%6.2f%%)\tFailed" % (fraction)
            msg[2] = f
            smsg =  " ".join(msg)
            report_save.writelines(smsg)
            if verbose:
                print (smsg)

            msg = pol.split(" ")
            # Remove any empty strings....
            msg = [x for x in msg if x]
            a = '% d\t(' % (pol_cnt)
            msg[1] = a
            if candidates > 0:
                fraction = 100.0*(float(pol_cnt)/float(candidates))
            else:
                fraction = 0.0
            f = "%6.2f%%)\tFailed" % (fraction)
            msg[2] = f
            smsg =  " ".join(msg)
            report_save.writelines(smsg)
            if verbose:
                print (smsg)
