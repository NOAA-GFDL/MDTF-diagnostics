'''
 Cyclone Intensity: Based on centeral SLP.
    1) The 1/3, 1/3, 1/3 rule: take SLP source distribution and partitioning
       it into 3 equal parts with the lower third being for "weak" cyclones,
       the middle third for "moderate" cyclones and the upper third being for
       "strong" cyclones.
          * Can be applied on a center-by-center basis in which case a cyclone
            track may span multiple intensity categories over time. The
            alternative approach applies a single intensity category to an
            entire cyclone track, often based on the minimum lifetime SLP of
            the track.
          * This is an adaptive measure so results will differ based on the
            distribution of the SLPs used. Thus a strong cyclone might differ
            when the SLP source covers the entire record, a single hemisphere,
            a single season, or just the month the track resides in. This is
            an issue when looking for changes/trends in cyclone intensity as
            this is a sliding scale.
          * Method of application (choice of SLP pool):
             1) Whole record and hemisphere (i.e, 1979-2008 NH).
             2) Whole record, season and hemisphere (i.e., 1979-2008 DJF NH).
             3) By year, hemisphere and season (i.e, 1979 DJF NH).
             4) By month and hemisphere (i.e., Jan 1979 NH).

    2) Fixed SLP Thresholds: Advantage being a fixed criteria that climate
       change could be seen relative too.


    3) Multivariate method used in Bauer and Del Genio (2005); based on ideas
       from Zielinski (2002).

          I = (1030.0 - SLP() + Deepinging_Rate + Pressure_Gradient

          * The deepening rate is taken over the 24 hours preceding
            the SLP minimum (units of hPa per 24 hours). A few
            cyclones are acquired at or near their minimum lifetime
            SLP (due to the break-up of a preexisting system). In
            these cases the SLP tendency of the succeeding 24 hours
            was used instead (although this takes some liberties with
            the idea of cyclone development being symmetrical about
            the point of peak intensity.). The pressure gradient
            represents the maximum value within a 1500 km radius of
            the SLP minima (units of hPa per 1000 km).
'''
import sys,os
import math

def test_spilt(slps,lower_third,upper_third):
    sall = len(slps)
    low = len([x for x in slps if x <= lower_third])
    mid = len([x for x in slps if lower_third < x < upper_third])
    hi  = len([x for x in slps if x >= upper_third])
    if sall != low+mid+hi:
        sys.exit("Percentile Error")

def plot_pdf(plt,Summerize,PDF,slps,mean,median,std,lower_third,upper_third,
             bins_centers,bins_left_edge,title,pname,scale=0.001):

    if pname.find(".pdf") != -1:
        dpi = 144
    else:
        dpi = 140

    fmter = "Count: %d\nMin/Max: %d/%d\nMean/Median: %.2f/%.2f\nSTD: %.2f"
    slps1 = [x*scale for x in slps]
    mean1 = mean*scale
    median1 = median*scale
    std1 = std*scale
    lower_third1 = lower_third*scale
    upper_third1 = upper_third*scale
    fnc_out = Summerize(slps1)
    stitle = fmter % (fnc_out[0],fnc_out[1][0],fnc_out[1][1],fnc_out[2],median1,fnc_out[3])
    stdensity = PDF([x*scale for x in bins_centers],mean1,std1)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = plt.hist(slps1,[x*scale for x in bins_left_edge],normed=True,facecolor='grey',alpha=0.75)
    ax.plot([x*scale for x in bins_centers],stdensity, 'r--', linewidth=1)
    ax.set_xlabel('SLP (hPa)')
    ax.set_ylabel('Normalized Count (i.e., a PDF)')
    ax.set_title(title)
    plt.suptitle(stitle, fontsize=6,x=0.73,y=0.98,horizontalalignment='left')
    ax.grid(True)
    midpnt_x = (lower_third1+fnc_out[1][0])*0.5
    mid_pnt_y = plt.ylim()[1] * 0.5
    yup = mid_pnt_y*0.01
    ax.text(midpnt_x,mid_pnt_y+yup,"Strong",horizontalalignment='center',fontsize='small')
    ax.annotate("",xy=(lower_third1,mid_pnt_y),xytext=(fnc_out[1][0],mid_pnt_y),
               xycoords='data',arrowprops=dict(arrowstyle="<->"))
    midpnt_x = (upper_third1+fnc_out[1][1])*0.5 + 0
    ax.text(midpnt_x,mid_pnt_y+yup,"Weak",horizontalalignment='center',fontsize='small')
    ax.annotate("",xy=(upper_third1,mid_pnt_y),xytext=(fnc_out[1][1],mid_pnt_y),
                xycoords='data',arrowprops=dict(arrowstyle="<->"))
    plt.savefig(pname,dpi=140,facecolor='w',edgecolor='w',orientation='landscape')

    pname = pname.replace("hist","histc")
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = plt.hist(slps1,[x*scale for x in bins_left_edge],histtype='step',
                                normed=True,cumulative=True,facecolor='grey',alpha=0.75)
    ax.set_xlabel('SLP (hPa)')
    ax.set_ylabel('Normalized Cumulative Count')
    ax.set_title(title)
    plt.suptitle(stitle, fontsize=6,x=0.73,y=0.98,horizontalalignment='left')
    ax.grid(True)
    midpnt_x = (lower_third1+fnc_out[1][0])*0.5
    ax.text(midpnt_x,0.335,"Strong",horizontalalignment='center',fontsize='small')
    ax.annotate("",xy=(lower_third1,0.333),xytext=(fnc_out[1][0],0.333),
               xycoords='data',arrowprops=dict(arrowstyle="<->"))
    midpnt_x = (upper_third1+fnc_out[1][1])*0.5 + 0
    ax.text(midpnt_x,0.669,"Weak",horizontalalignment='center',fontsize='small')
    ax.annotate("",xy=(upper_third1,0.666),xytext=(fnc_out[1][1],0.666),
                xycoords='data',arrowprops=dict(arrowstyle="<->"))


    plt.savefig(pname,dpi=140,facecolor='w',edgecolor='w',orientation='landscape')
    plt.close('all')

def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1

def setup_bins(bins_left_edge,bins_width,verbose=0):
    """Set up bins for histograms"""
    # Make a few extras
    bins_width = abs(bins_left_edge[0]-bins_left_edge[1])
    bins_centers = bins_left_edge + 0.5*bins_width
    bins_right_edge = bins_left_edge + bins_width
    if verbose:
        # To print out bins
        fmt = "Bin % 4d: % 7.2f <= % 7.2f < % 7.2f"
        for bin in range(len(bins_left_edge)):
            print fmt % (bin,bins_left_edge[bin],bins_centers[bin],
                         bins_right_edge[bin])
        print "Total Bin Cnt: %d" % (len(bins_centers))
    return (bins_centers,bins_right_edge)


def main(imports, defs_set, what_do, over_write_years, over_write_out_path,
        shared_path, over_write_slp_path, model, exit_on_error, skip_to_plots,
        make_plots, land_sea, zmean, skip_high_lat, fig_format, import_read):

    # Some generally useful calendar tools.
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}
    months_inv = {'February': 2, 'October': 10, 'March': 3, 'August': 8, 'May': 5,
                  'January': 1, 'June': 6, 'September': 9, 'April': 4,
                  'December': 12, 'July': 7, 'November': 11}
    months_Length = {'February': 28, 'October': 31, 'March': 31, 'August': 31,
                     'May': 31, 'January': 31, 'June': 30, 'September': 30,
                     'April': 30, 'December': 31, 'July': 31, 'November': 30}
    months_Length_inv = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                         7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    mm2season = { 1  : 0, 2  : 0, 3  : 1,
                  4  : 1, 5  : 1, 6  : 2,
                  7  : 2, 8  : 2, 9  : 3,
                  10 : 3, 11 : 3, 12 : 0}

    # Some division for the data
    seasons          = ["djf","mam","jja","son"]
    hemispheres      = ["nh","sh"]
    surfaces         = ["ocean","land"]
    system_types     = ["1st","last","pmin"]
    intensities      = ["wea", "mod", "str"]

    # For unwinding reads
    ids = {'YYYY' : 0,'MM' : 1, 'DD' : 2, 'HH' : 3, 'JD' : 4,
           'CoLat' : 5, 'Lon' : 6, 'GridID': 7, 'GridSLP' : 8,
           'RegSLP' : 9, 'GridLAP' : 10, 'Flags' : 11, 'Intensity' : 12,
           'Disimularity' : 13, 'UCI' : 14, 'USI' : 15, 'NGrids' : 16,
           'Area' : 17, 'Depth' : 18, 'NearestCenterDist' : 19,
           'NearestCenterAngle' : 20, 'MinOuterEdgeDist' : 21,
           'MaxOuterEdgeDist' : 22, 'AveOuterEdgeDist' : 23,
           'ATTS' : 24}

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    # import needed modules.
    for i in imports:
        exec(i)

    # pre-bind
    Read_MCMS = read_mcms.Read_MCMS
    Bin = numpy.histogram
    NA = numpy.array
    NRA = numpy.arange
    NZ = numpy.zeros
    NMean = numpy.mean
    NSTD = numpy.std
    NM = numpy.multiply
    Median = numpy.median
    Summerize = stats.ldescribe
    LSR = stats.llinregress
    if make_plots:
        PDF = mlab.normpdf

    # Used to know the relative position on the intensity flag
    intensity_skip = len("1979  1  1  0 244387450 15385 24312 001537 0969800 0974578 00651 00 ")
    #fmt_1 = "%4d %02d %02d %02d %09d %05d %05d %06d %07d %07d %05d %02d %02d"

    # Fetch definitions.
    defs_set = {}
    defs = defs.defs(**defs_set)

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
                land_gridids,troubled_centers) = fnc_out
        # Save memory
        del troubled_centers
        if not land_sea:
            del land_gridids
        del lat_edges
        del lon_edges
        del fnc_out
        row_start_index = row_start.index
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))

    # Update over_write values
    if over_write_years:
        super_years = over_write_years
    if over_write_slp_path:
        slp_path = over_write_slp_path
    if over_write_out_path:
        out_path = over_write_out_path

    # Years to check
    years = range(int(super_years[0]),int(super_years[-1])+1)
    clim_tag = "%04d-%04d" % (int(super_years[0]),int(super_years[-1]))

    if make_plots:
        dstart = datetime(years[0],1,1,0,0)
        dend = datetime(years[-1],1,1,0,0)
        delta = timedelta(days=365)
        x_dat_years = dates.drange(dstart, dend, delta)
        dend = datetime(years[-1],12,1,0,0)
        # Below doesn't work due to ambiguity of adding a month to a date
        #delta = timedelta(days=30)
        #x_dat_months = dates.drange(dstart, dend, delta)
        # This works but is less pretty
        delta = relativedelta(months=+1)
        x_dat_months = []
        d = dstart
        while d <= dend:
            d += delta
            x_dat_months.append(dates.date2num(d))

    # The histogram can be used to efficiently calculate the mean
    # and standard deviation of very large data sets without the
    # need to store individual values.
    #
    # Setup bins for these calculations.
    if zmean:
        bin_width = 5.0*defs.accuracy;
        bins_left_edge = NRA(int(-100*defs.accuracy),int(50*defs.accuracy)+bin_width,bin_width)
    else:
        bin_width = 5.0*defs.accuracy;
        bins_left_edge = NRA(int(930.0*defs.accuracy),int(1040.0*defs.accuracy),bin_width)
    (bins_centers,bins_right_edge) = setup_bins(bins_left_edge,
                                                bin_width,verbose=0)
    nbins = len(bins_left_edge)-1
    bins_left_edge = NA(bins_left_edge)

    # Instantiate read_mcms
    readit = Read_MCMS(**what_do)
    readit.check_time()
    readit.check_place()

    # Add Tag if removing zonal mean
    if zmean:
        zm_tag = "_zanom"
        zm_tag_title = "ZAnom"
    else:
        zm_tag = ""
        zm_tag_title = ""

    # Add Tag if screening by land or sea
    if land_sea == 1:
        ls_tag = "_land"
        ls_tag_title = "Land Only"
    elif  land_sea == 2:
        ls_tag = "_ocean"
        ls_tag_title = "Ocean Only"
    else:
        ls_tag = ""
        ls_tag_title = ""

    # Stats file
    stats_file = "%sstats/mcms_%s_%s_intensity_stats%s%s.txt" % (out_path,model,
            clim_tag,zm_tag,ls_tag)
    stats_save = open(stats_file,"w")

    # --------------------------------------------------------------------------
    # Main Program Logic
    # --------------------------------------------------------------------------
    big_table = {}

    if zmean:
        # Create an array of zonal means by month
        the_zmeans = NZ((len(years),12,jm),dtype=numpy.float)
        the_zmean_annual = NZ((len(years),jm),dtype=numpy.float)
        the_zmeans_sclim = NZ((len(seasons),jm),dtype=numpy.float)
        the_zmeans_season = NZ((len(years),len(seasons),jm),dtype=numpy.float)

    # Create a lookup table
    ilook = {}
    i = 0
    for year in years:
        j = {}
        for y in range(1,13):
            j[y] = i
            i += 1
        ilook[year] = j

    if not skip_to_plots:
        iyear = 0
        for loop_year in years:

            print "\n=============%d=============" % (loop_year)

            # Adjust in_file names
            tag = str(readit.in_file[-cut_tail-4:-cut_tail])
            readit.in_file = readit.in_file.replace(tag,str(loop_year))

            if zmean:
                # Open data file, extract data and model definitions
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
                    sys.exit("Need to fix x_dat_years for non-standard calendar")
                elif the_calendar != "proleptic_gregorian":
                    jd_fake = False
##fix

                tsteps = len(times)
                tstepsperday = float(24.0/timestep)

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
                slp_months = [d.month for d in dtimes]

                # Find the 12 monthly mean maps
                for month in range(1,13):
                    this_month = [step for step in range(0,tsteps) if slp_months[step] == month]
                    # Find the zonal average of the monthly mean maps
                    this_sum = NMean(slp[this_month[0]:this_month[-1]+1,:,:],2)
                    this_sum = NMean(this_sum,0)
                    the_zmeans[iyear,month-1,:] = NM(this_sum,defs.accuracy)

            # Read center files
            readit.fetch_centers()
            centers = readit.center_holder.keys()
            print "\tCenters Read",len(centers)

            # Create a lookup table with keyed with center_uci and storing
            # an array [year,month,season,hemi,gridslp]
            for center in centers:
                # Trim for land/sea if asked
                if land_sea == 1: # land only
                    if int(readit.center_holder[center][7]) not in readit.land_gridids:
                        continue
                elif land_sea == 2: # sea only
                    if int(readit.center_holder[center][7]) in readit.land_gridids:
                        continue
                hemi = (0 if 9000-int(readit.center_holder[center][5]) >= 0 else 1)
                gridslp = int(readit.center_holder[center][8])
                if zmean:
                    center_gridid = int(readit.center_holder[center][7])
                    # Find row for the location
                    row_guess = [x for x in row_start
                                 if x <= center_gridid]
                    row_guess = row_start_index(row_guess[-1])
                    big_table[center] = [hemi,gridslp,row_guess]
                else:
                    big_table[center] = [hemi,gridslp]
            iyear += 1

        if zmean:
            # Find the climatological zonal average (by Year)
            the_zmeans_annual = NMean(the_zmeans,1)
            # Find the climatological zonal average
            the_zmeans_clim = NMean(the_zmeans,1)
            the_zmeans_clim = NMean(the_zmeans_clim,0)
            # Find climatological seasonal zonal average
            the_zmeans_mclim = NMean(the_zmeans,0)
            the_zmeans_sclim[0,:] = NM(the_zmeans_mclim[11,:]+the_zmeans_mclim[0,:]+the_zmeans_mclim[1,:],0.333)
            the_zmeans_sclim[1,:] = NM(the_zmeans_mclim[2,:]+the_zmeans_mclim[3,:]+the_zmeans_mclim[4,:],0.333)
            the_zmeans_sclim[2,:] = NM(the_zmeans_mclim[5,:]+the_zmeans_mclim[6,:]+the_zmeans_mclim[7,:],0.333)
            the_zmeans_sclim[3,:] = NM(the_zmeans_mclim[8,:]+the_zmeans_mclim[9,:]+the_zmeans_mclim[10,:],0.333)
            # Find year to year seasonal zonal average
            iyear = 0
            for year in years:
                the_zmeans_season[iyear,0,:] = NM(the_zmeans[iyear,11,:]+the_zmeans[iyear,0,:]+the_zmeans[iyear,1,:],0.333)
                the_zmeans_season[iyear,1,:] = NM(the_zmeans[iyear,2,:]+the_zmeans[iyear,3,:]+the_zmeans[iyear,4,:],0.333)
                the_zmeans_season[iyear,2,:] = NM(the_zmeans[iyear,5,:]+the_zmeans[iyear,6,:]+the_zmeans[iyear,7,:],0.333)
                the_zmeans_season[iyear,3,:] = NM(the_zmeans[iyear,8,:]+the_zmeans[iyear,9,:]+the_zmeans[iyear,10,:],0.333)
                iyear += 1

        print "\nReading Done"

        centers = big_table.keys()
        print "Total Centers Read",len(centers)

        # Save tmp files in case want to tweak figures.
        fmt1 = "%sstats/tmp/refine_data_%s_%s%s%s.p"
        if zmean:
            pickle.dump((big_table,centers,the_zmeans_annual,
                the_zmeans_clim,the_zmeans_mclim,the_zmeans_sclim,the_zmeans_season),
                    open(fmt1 % (out_path,model,clim_tag,zm_tag,ls_tag),"wb",-1))
        else:
            pickle.dump((big_table,centers),
                    open(fmt1 % (out_path,model,clim_tag,zm_tag,ls_tag),"wb",-1))
    else:
        # unPickle objects:
        fmt1 = "%sstats/tmp/refine_data_%s_%s%s%s.p"
        if zmean:
            (big_table,centers,the_zmeans_annual,the_zmeans_clim,
                    the_zmeans_mclim,the_zmeans_sclim,the_zmeans_season) = pickle.load(
                            open(fmt1 % (out_path,model,clim_tag,zm_tag,ls_tag), 'rb'))
        else:
            (big_table,centers) = pickle.load(
                    open(fmt1 % (out_path,model,clim_tag,zm_tag,ls_tag), 'rb'))
        print "done."

    slp_pools = ["whole_hemi","whole_hemi_season","year_hemi_season","year_hemi_month"]
    list_month_season = []
    for loop_year in years:
        for loop_month in range(1,13):
            list_month_season.append(mm2season[loop_month])
    by_month = NZ((len(years),12,2,2),dtype=numpy.float)

    # Create Table for partitioning Centers.
    # thirds (year_month,hemi,(lower_third,upper_third),slp_pool)
    thirds = NZ((len(years)*12,2,2,len(slp_pools)),dtype=numpy.float)
    # stats(year_month,hemi,(mean,median,STD,min,max,cnt,skew,kurtosis),slp_pool)
    tstats = NZ((len(years)*12,2,8,len(slp_pools)),dtype=numpy.float)
    used_pool = 3

#tmp
    #make_plots = 0

    # SLP Pool: Whole record and hemisphere (i.e, 1979-2008 NH)
    print "\tStarting: Whole record and hemisphere (i.e, 1979-2008 NH)"
    for hemi in range(2):
        this_hemi = [x for x in centers if big_table[x][0] == hemi]
        if zmean:
            slps = [big_table[x][1]-the_zmeans_clim[big_table[x][2]] for x in this_hemi]
        else:
            slps = [big_table[x][1] for x in this_hemi]
        (n,bins) = Bin(slps,bins_left_edge)
        mean = NMean(slps)
        median = Median(slps)
        std = NSTD(slps)
        # Find Lower 1/3 and Upper 1/3 Boundary
        slps.sort()
        lower_third = int(percentile(slps,0.333))
        upper_third = int(percentile(slps,0.666))
        test_spilt(slps,lower_third,upper_third)
        thirds[:,hemi,0,0] = lower_third
        thirds[:,hemi,1,0] = upper_third
        tstats[:,hemi,0,0] = mean
        tstats[:,hemi,1,0] = median
        tstats[:,hemi,2,0] = std
        tstats[:,hemi,3,0] = min(slps)
        tstats[:,hemi,4,0] = max(slps)
        tstats[:,hemi,5,0] = len(slps)
        fnc_out = Summerize(slps)
        tstats[:,hemi,6,0] = fnc_out[4]
        tstats[:,hemi,7,0] = fnc_out[5]

        if make_plots:
            pname = "%sfigs/pdfs/%s_slp_hist_%s_%s_%s%s%s%s" % (out_path,model,clim_tag,
                                                            hemispheres[hemi],
                                                            "annual",ls_tag,
                                                            zm_tag,fig_format)
            title = '%s %s %s %s %s %s' % (model.upper(),clim_tag,
                                      hemispheres[hemi].upper(),
                                      "Annual",ls_tag_title,zm_tag_title)
            plot_pdf(plt,Summerize,PDF,slps,mean,median,std,lower_third,upper_third,
                     bins_centers,bins_left_edge,title,pname)
            print "Made",pname

        # SLP Pool: Whole record, season and hemisphere (i.e., 1979-2008 DJF NH).
        for season in range(len(seasons)):
            this_season = [x for x in this_hemi if mm2season[int(x[4:6])] == season]
            if zmean:
                slps = [big_table[x][1]-the_zmeans_sclim[season,big_table[x][2]] for x in this_hemi]
            else:
                slps = [big_table[x][1] for x in this_season]
            (n,bins) = Bin(slps,bins_left_edge)
            mean = NMean(slps)
            median = Median(slps)
            std = NSTD(slps)
            # Find Lower 1/3 and Upper 1/3 Boundary
            slps.sort()
            lower_third = int(percentile(slps,0.333))
            upper_third = int(percentile(slps,0.666))
            test_spilt(slps,lower_third,upper_third)
            for x in range(len(years)*12):
                if list_month_season[x] == season:
                    thirds[x,hemi,0,1] = lower_third
                    thirds[x,hemi,1,1] = upper_third
                    tstats[x,hemi,0,1] = mean
                    tstats[x,hemi,1,1] = median
                    tstats[x,hemi,2,1] = std
                    tstats[x,hemi,3,1] = min(slps)
                    tstats[x,hemi,4,1] = max(slps)
                    tstats[x,hemi,5,1] = len(slps)
                    fnc_out = Summerize(slps)
                    tstats[x,hemi,6,1] = fnc_out[4]
                    tstats[x,hemi,7,1] = fnc_out[5]

            if make_plots:
                pname = "%sfigs/pdfs/%s_slp_hist_%s_%s_%s_%s%s%s" % (out_path,model,clim_tag,
                                                                 hemispheres[hemi],
                                                                 seasons[season],
                                                                 ls_tag,zm_tag,
                                                                 fig_format)
                title = '%s %s %s %s %s %s' % (model.upper(),clim_tag,
                                            hemispheres[hemi].upper(),
                                            seasons[season].upper(),
                                            ls_tag_title,zm_tag_title)
                plot_pdf(plt,Summerize,PDF,slps,mean,median,std,lower_third,upper_third,
                         bins_centers,bins_left_edge,title,pname)
                print "Made",pname

#tmp
    #make_plots = 0
    print "\tStarting: By year, hemisphere and annual (i.e, 1979 NH) and (i.e., 1979 DJF NH)"
    iyear = 0
    for year in years:
        # SLP Pool: By year, hemisphere and annual (i.e, 1979 NH).
        this_years = [x for x in centers if x.startswith(str(year))]
        for hemi in range(2):
            this_hemi = [x for x in this_years if big_table[x][0] == hemi]
            if zmean:
                slps = [big_table[x][1]-the_zmeans_annual[iyear,big_table[x][2]] for x in this_hemi]
            else:
                slps = [big_table[x][1] for x in this_hemi]
            (n,bins) = Bin(slps,bins_left_edge)
            mean = NMean(slps)
            median = Median(slps)
            std = NSTD(slps)
            # Find Lower 1/3 and Upper 1/3 Boundry
            slps.sort()
            lower_third = int(percentile(slps,0.333))
            upper_third = int(percentile(slps,0.666))
            test_spilt(slps,lower_third,upper_third)
            #i = 0
            #for x in years:
            #    for y in range(12):
            #        if x == year:
            #            thirds[i,hemi,0,2] = lower_third
            #            thirds[i,hemi,1,2] = upper_third
            #        i += 1
            if make_plots:
                pname = "%sfigs/pdfs/%s_slp_hist_%s_%s_%s%s%s%s" % (out_path,model,str(year),
                                                                hemispheres[hemi],"annual",
                                                                ls_tag,zm_tag,fig_format)
                title = '%s %s %s %s %s %s' % (model.upper(),str(year),hemispheres[hemi].upper(),
                                         "Annual",ls_tag_title,zm_tag_title)
                plot_pdf(plt,Summerize,PDF,slps,mean,median,std,lower_third,upper_third,
                         bins_centers,bins_left_edge,title,pname)
                print "Made",pname

            # SLP Pool: By year, season and hemisphere (i.e., 1979 DJF NH).
            for season in range(len(seasons)):
                this_season = [x for x in this_hemi if mm2season[int(x[4:6])] == season]
                if zmean:
                    slps = [big_table[x][1]-the_zmeans_season[iyear,season,big_table[x][2]] for x in this_season]
                else:
                    slps = [big_table[x][1] for x in this_season]
                (n,bins) = Bin(slps,bins_left_edge)
                mean = NMean(slps)
                median = Median(slps)
                std = NSTD(slps)
                # Find Lower 1/3 and Upper 1/3 Boundry
                slps.sort()
                lower_third = int(percentile(slps,0.333))
                upper_third = int(percentile(slps,0.666))
                test_spilt(slps,lower_third,upper_third)
                i = 0
                for x in years:
                    for y in range(12):
                        if x == year:
                            if list_month_season[i] == season:
                                thirds[i,hemi,0,2] = lower_third
                                thirds[i,hemi,1,2] = upper_third
                                tstats[i,hemi,0,2] = mean
                                tstats[i,hemi,1,2] = median
                                tstats[i,hemi,2,2] = std
                                tstats[i,hemi,3,2] = min(slps)
                                tstats[i,hemi,4,2] = max(slps)
                                tstats[i,hemi,5,2] = len(slps)
                                fnc_out = Summerize(slps)
                                tstats[i,hemi,6,2] = fnc_out[4]
                                tstats[i,hemi,7,2] = fnc_out[5]

                        i += 1
                if make_plots:
                    pname = "%sfigs/pdfs/%s_slp_hist_%s_%s_%s%s%s%s" % (out_path,model,str(year),
                                                                    hemispheres[hemi],
                                                                    seasons[season],
                                                                    ls_tag,zm_tag,
                                                                    fig_format)
                    title = '%s %s %s %s %s %s' % (model.upper(),str(year),
                                                hemispheres[hemi].upper(),
                                                seasons[season].upper(),ls_tag_title,zm_tag_title)
                    plot_pdf(plt,Summerize,PDF,slps,mean,median,std,lower_third,upper_third,
                             bins_centers,bins_left_edge,title,pname)
                    print "Made",pname

            # SLP Pool: By year, month and hemisphere (i.e., 1979 January NH).
            for month in range(1,13):
                this_month  = [x for x in this_hemi if int(x[4:6]) == month]
                if zmean:
                    slps = [big_table[x][1]-the_zmeans[iyear,month-1,big_table[x][2]] for x in this_month]
                else:
                    slps = [big_table[x][1] for x in this_month]
                (n,bins) = Bin(slps,bins_left_edge)
                mean = NMean(slps)
                median = Median(slps)
                std = NSTD(slps)
                # Find Lower 1/3 and Upper 1/3 Boundary
                slps.sort()
                lower_third = int(percentile(slps,0.333))
                upper_third = int(percentile(slps,0.666))
                test_spilt(slps,lower_third,upper_third)
                i = 0
                j = 0
                for x in years:
                    for y in range(1,13):
                        if x == year:
                            if y == month:
                                thirds[i,hemi,0,3] = lower_third
                                thirds[i,hemi,1,3] = upper_third
                                by_month[j,y-1,hemi,0] = lower_third
                                by_month[j,y-1,hemi,1] = upper_third
                                tstats[i,hemi,0,3] = mean
                                tstats[i,hemi,1,3] = median
                                tstats[i,hemi,2,3] = std
                                tstats[i,hemi,3,3] = min(slps)
                                tstats[i,hemi,4,3] = max(slps)
                                tstats[i,hemi,5,3] = len(slps)
                                fnc_out = Summerize(slps)
                                tstats[i,hemi,6,3] = fnc_out[4]
                                tstats[i,hemi,7,3] = fnc_out[5]
                        i += 1
                    j += 1
                if make_plots:
                    pname = "%sfigs/pdfs/%s_slp_hist_%s_%s_%s%s%s%s" % (out_path,model,str(year),
                                                                    hemispheres[hemi],
                                                                    months[month],
                                                                    ls_tag,zm_tag,
                                                                    fig_format)
                    title = '%s %s %s %s %s %s' % (model.upper(),str(year),
                                                hemispheres[hemi].upper(),
                                                months[month].upper(),ls_tag_title,zm_tag_title)
                    plot_pdf(plt,Summerize,PDF,slps,mean,median,std,lower_third,upper_third,
                             bins_centers,bins_left_edge,title,pname)
                    print "Made",pname
        iyear += 1
#tmp
    #make_plots = 0
    if len(years) > 10 and make_plots:
        print "\tStarting Time Series"
        # Only do if a decade of data or more
        golden_ratio = 1.61803399*2.0
        width = 10
        height = width/golden_ratio
        third_lines = ['-','--']
        #        hemi_colors = ['r','b']
        hemi_colors = ['k','k']
        season_marker = 'o'
        year_season_marker = '*'
        month_marker = '^'
        for month in range(12):
            for hemi in range(2):
                pname = "%s/figs/pdfs/%s_slp_hist_pressed_%s_%s_%s%s%s%s" % (out_path,model,clim_tag,
                                                                        months[month+1],
                                                                        hemispheres[hemi],
                                                                        ls_tag,zm_tag,fig_format)
                title = '%s %s %s %s %s %s' % (model.upper(),clim_tag,hemispheres[hemi].upper(),
                                            months[month+1].upper(),ls_tag_title,zm_tag_title)
                fig = plt.figure(figsize=(width,height))
                ax = fig.add_subplot(111)
                ax.plot(x_dat_years,thirds[:len(years),hemi,0,0]*0.001,
                        third_lines[0]+hemi_colors[hemi],linewidth=3,
                        label='Climatology-Lower')
                ax.plot(x_dat_years,thirds[:len(years),hemi,1,0]*0.001,
                        third_lines[1]+hemi_colors[hemi],linewidth=3,
                        label='Climatology-Upper')
                ax.plot(x_dat_years,by_month[:,month,hemi,0]*0.001,
                        third_lines[0]+hemi_colors[hemi]+month_marker,linewidth=1,
                        markersize=4,label='Year-Monthly-Lower')
                ax.plot(x_dat_years,by_month[:,month,hemi,1]*0.001,
                        third_lines[1]+hemi_colors[hemi]+month_marker,linewidth=1,
                        markersize=4,label='Year-Monthly-Upper')

                pick = [thirds[month,hemi,0,1]*0.001 for x in x_dat_years]
                ax.plot(x_dat_years,pick,
                        third_lines[0]+hemi_colors[hemi],linewidth=0.5,
                        markersize=4,label='Climatology-Season-Lower')
                pick = [thirds[month,hemi,1,1]*0.001 for x in x_dat_years]
                ax.plot(x_dat_years,pick,
                        third_lines[1]+hemi_colors[hemi],linewidth=0.5,
                        markersize=4,label='Climatology-Season-Upper-')

                ax.set_xlabel('Time (Years)')
                ax.set_ylabel('SLP (hPa)')
                ax.xaxis.set_major_formatter(dates.DateFormatter('%Y'))
                ax.set_title(title)
                ax.grid(True)
                plt.savefig(pname,dpi=140,facecolor='w',edgecolor='w',orientation='landscape')
                print "Made",pname
                plt.close('all')
#tmp
    # Save tmp files in case want to tweak figures and data save.
    #fmt1 = "%sstats/tmp/tmp.p"
    #pickle.dump((x_dat_years,x_dat_months,thirds,tstats),open(fmt1 % (out_path),"wb",-1))
    # unPickle objects:
    #(x_dat_years,x_dat_months,thirds,tstats) = pickle.load(open(fmt1 % (out_path)))
    #make_plots = 1

    if make_plots:
        golden_ratio = 1.61803399*2.0
        width = 40.0
        # Just Annual Cycle Version
        #width = 10
        height = width/golden_ratio

        pname = "%sfigs/%s_slp_bounds_time_%s%s%s" % (out_path,model,clim_tag,
                                                        ls_tag,fig_format)
        title = '%s %s' % (model.upper(),clim_tag)
        fig = plt.figure()
        fig = plt.figure(figsize=(width,height))
        ax = fig.add_subplot(111)
        third_lines = ['-','--']
        hemi_colors = ['r','b']
        season_marker = 'o'
        year_season_marker = '*'
        month_marker = '^'

        for hemi in range(2):

            # Uncomment a Set to plot. I find Set A the most interesting.

            ## Set B: Just Annual Cycle Version (uses "whole_hemi" and "whole_hemi_season" slp_pool)
            #ax.plot([x+1 for x in range(12)],thirds[0:12,hemi,0,0]*0.001,
            #        third_lines[0]+hemi_colors[hemi],linewidth=3)
            #ax.plot([x+1 for x in range(12)],thirds[0:12,hemi,1,0]*0.001,
            #        third_lines[1]+hemi_colors[hemi],linewidth=3)
            #ax.plot([x+1 for x in range(12)],thirds[0:12,hemi,0,1]*0.001,
            #        third_lines[0]+hemi_colors[hemi]+season_marker,linewidth=1)
            #ax.plot([x+1 for x in range(12)],thirds[0:12,hemi,1,1]*0.001,
            #        third_lines[1]+hemi_colors[hemi]+season_marker,linewidth=1)

            # Set A: plots climatological as lines (uses "whole_hemi" slp_pool)
            ax.plot(x_dat_months,thirds[:,hemi,0,0]*0.001,
                    third_lines[0]+hemi_colors[hemi],linewidth=3,
                    label='Climatology-Lower')
            ax.plot(x_dat_months,thirds[:,hemi,1,0]*0.001,
                    third_lines[1]+hemi_colors[hemi],linewidth=3,
                    label='Climatology-Upper')

            ## Set C: plots seasonal thirds (uses "whole_hemi_season","year_hemi_season"
            ## slp_pools)
            #ax.plot(x_dat_months,thirds[:,hemi,0,1]*0.001,
            #        third_lines[0]+hemi_colors[hemi]+season_marker,linewidth=1,
            #        markersize=12,label='Climatology-Season-Lower')
            #ax.plot(x_dat_months,thirds[:,hemi,1,1]*0.001,
            #        third_lines[1]+hemi_colors[hemi]+season_marker,linewidth=1,
            #        markersize=12,label='Climatology-Season-Upper-')
            #ax.plot(x_dat_months,thirds[:,hemi,0,2]*0.001,
            #        third_lines[0]+hemi_colors[hemi]+year_season_marker,linewidth=1,
            #        markersize=12,label='Year-Season-Lower')
            #ax.plot(x_dat_months,thirds[:,hemi,1,2]*0.001,
            #        third_lines[1]+hemi_colors[hemi]+year_season_marker,linewidth=1,
            #        markersize=12,label='Year-Season-Upper')

            # Set A: plots monthly thirds with lines and symbols
            # (uses "year_hemi_month" slp_pool)
            ax.plot(x_dat_months,thirds[:,hemi,0,used_pool]*0.001,
                    third_lines[0]+hemi_colors[hemi]+month_marker,linewidth=1,
                    markersize=12,label='Year-Monthly-Lower')
            ax.plot(x_dat_months,thirds[:,hemi,1,used_pool]*0.001,
                    third_lines[1]+hemi_colors[hemi]+month_marker,linewidth=1,
                    markersize=12,label='Year-Monthly-Upper')
            ax.xaxis.set_major_formatter(dates.DateFormatter('%Y'))

        ax.set_xlabel('Time (Months)')
        ax.set_ylabel('SLP (hPa)')
        ax.set_title(title)
        ax.grid(True)
        plt.savefig(pname,dpi=140,facecolor='w',edgecolor='w',orientation='landscape')
        plt.close('all')
        print "Made",pname

    # Alter Files to include new intensity values.
    tag = str(what_do["in_file"][-cut_tail-4:-cut_tail])
    center_file = what_do["in_file"]
    for loop_year in years:
        # Adjust in_file names
        center_file = center_file.replace(tag,str(loop_year))
        tag = str(loop_year)
        print "Altering:",center_file
        # Create a temporary write file
        tmp_file = center_file.replace(".txt","new.txt")
        # Open files for read and write
        centers_read = open(center_file,"r")
        centers_write = open(tmp_file,"w")
        for line in centers_read:
            # Process line
            parts = line.split(None)
            flag = int(parts[0])
            len_start = len(line)
            if flag > 0:
                # Assign Intensity to Center
                year = int(parts[0])
                month = int(parts[1])
                gridslp = int(parts[8])
                hemi = (0 if 9000-int(parts[5]) >= 0 else 1)
                ival = ilook[year][month]
                # Assigned Intensity Classification
                up_third = int(thirds[ival,hemi,1,used_pool])
                low_third = int(thirds[ival,hemi,0,used_pool])
                # Use the 1/3, 1/3, 1/3 rule for intensity.
                if gridslp < low_third:
                    intensity = 3 # Strong
                elif gridslp > up_third:
                    intensity = 1 # Weak
                else:
                    intensity =  2 # Moderate
                # Modify line for output
                line = line[:intensity_skip]+"%02d" % (intensity)+line[intensity_skip+2:]
            # Check nothing wrong
            len_finish = len(line)
            if len_start != len_finish:
                sys.exit("Length Error: Stopping (%d,%d)" % (len_start,len_finish))
            # Save to line to file
            centers_write.writelines(line)
        # Close Files
        centers_read.close()
        centers_write.close()
        # If made it here, then safe to rename and thus replace original file.
        # Warning I highly recommend you work with a copy and save the original
        # files for save keeping.
        os.rename(tmp_file,center_file)

    # Save Intensity Info for review and such
    # SEofEst = Standard Error of the Estimate
    # 2tailP = two-tailed probability
    terms = ("Year","Month","Hemi","Mean","Median","STD",
             "Min","Max","Lower 1/3","Upper 1/3","Cnt","Skew",
             "Kurtosis","Slope","Intercept","R",
              "2tailP","SEofEst")
    tag = ''.join(["%12s " % (x) for x in terms])
    fmts = "%12d %12d %12s %12d %12d %12d %12d %12d %12d %12d %12d %12f %12f %12f %12f %12f %12f %12f"
    hemis = ("NH","SH")

    # SLP Pool: Whole record and hemisphere (i.e, 1979-2008 NH)
    stats_save.writelines("# SLP Pool: Whole record and hemisphere (i.e, %s NH)\n" % (clim_tag))
    stats_save.writelines(tag+"\n")
    fmts = "%12s %12s %12s %12d %12d %12d %12d %12d %12d %12d %12d %12f %12f %12s %12s %12s %12s %12s"
    for hemi in range(2):
        line = fmts % (clim_tag,"Annual",hemis[hemi],
                       int(tstats[0,hemi,0,0]),
                       int(tstats[0,hemi,1,0]),
                       int(tstats[0,hemi,2,0]),
                       int(tstats[0,hemi,3,0]),
                       int(tstats[0,hemi,4,0]),
                       int(thirds[0,hemi,1,0]),
                       int(thirds[0,hemi,0,0]),
                       int(tstats[0,hemi,5,0]),
                       tstats[0,hemi,6,0],
                       tstats[0,hemi,7,0],"-","-", "-", "-", "-")
        stats_save.writelines(line+"\n")
    # SLP Pool: Whole record, season and hemisphere (i.e., 1979-2008 DJF NH)
    stats_save.writelines("# SLP Pool: Whole record, season and hemisphere (i.e., %s DJF NH)\n" % (clim_tag))
    stats_save.writelines(tag+"\n")
    for hemi in range(2):
        for seas in range(len(seasons)):
            # remap to get correct values
            if seas == 0:
                tseas = 0
            elif seas == 1:
                tseas = 3
            elif seas == 2:
                tseas = 8
            elif seas == 3:
                tseas = 11
            line = fmts % (clim_tag,seasons[seas].upper(),hemis[hemi],
                           int(tstats[tseas,hemi,0,1]),
                           int(tstats[tseas,hemi,1,1]),
                           int(tstats[tseas,hemi,2,1]),
                           int(tstats[tseas,hemi,3,1]),
                           int(tstats[tseas,hemi,4,1]),
                           int(thirds[tseas,hemi,1,1]),
                           int(thirds[tseas,hemi,0,1]),
                           int(tstats[tseas,hemi,5,1]),
                           tstats[tseas,hemi,6,1],
                           tstats[tseas,hemi,7,1],"-","-", "-", "-", "-")
            stats_save.writelines(line+"\n")
    # SLP Pool: By year, hemisphere and annual (i.e, 1979 NH).
    # SLP Pool: By year, season and hemisphere (i.e., 1979 DJF NH).

    # SLP Pool: By year, month and hemisphere (i.e., 1979 January NH).
    fmts = "%12d %12d %12s %12d %12d %12d %12d %12d %12d %12d %12d %12f %12f %12s %12s %12s %12s %12s"
    stats_save.writelines("# SLP Pool: By year, month and hemisphere (i.e., 1979 January NH)\n")
    stats_save.writelines(tag+"\n")
    for loop_year in years:
        intensity_file = "%sstats/mcms_%s_%04d_intensity.txt" % (out_path,model,int(loop_year))
        intensity_save = open(intensity_file,"w")
        intensity_save.writelines(tag+"\n")
        for hemi in range(2):
            for month in range(1,13):
                ival = ilook[loop_year][month]
                line = fmts % (loop_year,month,hemis[hemi],
                               int(tstats[ival,hemi,0,used_pool]),
                               int(tstats[ival,hemi,1,used_pool]),
                               int(tstats[ival,hemi,2,used_pool]),
                               int(tstats[ival,hemi,3,used_pool]),
                               int(tstats[ival,hemi,4,used_pool]),
                               int(thirds[ival,hemi,1,used_pool]),
                               int(thirds[ival,hemi,0,used_pool]),
                               int(tstats[ival,hemi,5,used_pool]),
                               tstats[ival,hemi,6,used_pool],
                               tstats[ival,hemi,7,used_pool],"-","-", "-", "-", "-")
                intensity_save.writelines(line+"\n")
                line = fmts % (loop_year,month,hemis[hemi],
                               int(tstats[ival,hemi,0,3]),
                               int(tstats[ival,hemi,1,3]),
                               int(tstats[ival,hemi,2,3]),
                               int(tstats[ival,hemi,3,3]),
                               int(tstats[ival,hemi,4,3]),
                               int(thirds[ival,hemi,1,3]),
                               int(thirds[ival,hemi,0,3]),
                               int(tstats[ival,hemi,5,3]),
                               tstats[ival,hemi,6,3],
                               tstats[ival,hemi,7,3],"-","-", "-", "-", "-")
                stats_save.writelines(line+"\n")
        intensity_save.close()
        print "Made",intensity_file

    # Test for Trends in boundaries see by thirds sorted by month and hemisphere over years
    if len(years) > 10:
       # Only do if a decade of data or more
        y_vals = NZ((len(years),12,2,3),dtype=numpy.float)
        iyear = 0
        for loop_year in years:
            for hemi in range(2):
                for month in range(1,13):
                    ival = ilook[loop_year][month]
                    y_vals[iyear,month-1,hemi,0] = thirds[ival,hemi,0,3] # strong
                    y_vals[iyear,month-1,hemi,1] = thirds[ival,hemi,1,3] # weak
                    y_vals[iyear,month-1,hemi,2] = thirds[ival,hemi,0,3] - thirds[ival,hemi,1,3] # seperation between strong and weak
            iyear += 1

        fmts = "%12s %12d %12s %12d %12d %12d %12d %12d %12s %12s %12d %12f %12f %12.3f %12.3f %12.3f %12.3f %12.3f"
        stats_save.writelines("# Trend Analysis with SLP Pool: By year, month and hemisphere (i.e., 1979 January NH)\n")
        stats_save.writelines(tag+"\n")
        whats = ["Strong","Weak","Spread"]
        for hemi in range(2):
            for month in range(1,13):
                for whaty in range(3):
                    y = y_vals[:,month-1,hemi,whaty]
                    x = range(len(years))
                    mean = NMean(y)
                    median = Median(y)
                    std = NSTD(y)
                    fnc_out = Summerize(list(y))
                    # Use Linear Regession
                    fnc = LSR(x,list(y))
                    line = fmts % (clim_tag,month,hemis[hemi],int(mean),int(median),
                                   int(std),min(y),max(y),whats[whaty],"",len(y),
                                   fnc_out[4],fnc_out[5],fnc[0],fnc[1],fnc[2],fnc[3],fnc[4])
                    stats_save.writelines(line+"\n")

    print "Made",stats_file
    stats_save.close()
    return "Done"
#---Start of main code block.
if __name__=='__main__':

    import sys, pickle
    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------

    picks = {0 : "NCEP/NCAR Reanalysis 1",
             1 : "NCEP-DOE Reanalysis 2",
             2 : "NASA GISS GCM ModelE",
             3 : "GFDL GCM",
             4 : "ERA-Interim Reanalysis"}
    pick = 0
    if pick not in picks:
        sys.exit("ERROR: pick not listed in picks.")

    # This next set of lines should be copied from setup_vX.py
    # Short names by which pick will be labeled.
    models = ["nra","nra2","giss","gfdl","erai"]
    try:
        model = models[pick]
    except:
        sys.exit("ERROR: pick not listed in models.")

    # Halt program on error or just warn?
    exit_on_error = 0

    # Save/plot Stats
    make_plots = 1

    # Remove zonal mean
    zmean = 0

    # Separate by land_sea screen # land_sea = 0 All, land_sea = 1 Land, land_sea = 2 Ocean
    land_sea = 0

    # Skip high latitude centers
    skip_high_lat = 85

    # What sort of figures
    #    fig_format = ".png"
    #    fig_format = ".eps"
    fig_format = ".pdf"

    # Set to 1 to skip past reading data to tweak plots.
    skip_to_plots = 0

    # Length of file ending to replace if using year_loop
    tails = ["_att.txt","_tracks.txt","_centers.txt","_dumped_centers.txt"]
    tail = tails[0]
    cut_tail = len(tail)

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # Basic standard Python modules to import.
    imports = []
    imports.append("import stats,numpy,pickle")
    if zmean:
        imports.append("import netcdftime")
        imports.append("import netCDF4 as NetCDF")
    if make_plots or zmean:
        imports.append("from datetime import datetime, timedelta")
        imports.append("from dateutil.relativedelta import relativedelta")
        imports.append("import matplotlib.pyplot as plt")
        imports.append("import matplotlib.mlab as mlab")
        imports.append("import matplotlib.dates as mdates")
        imports.append("from matplotlib import dates")

    # My modules to import w/ version number appended.
    my_base = ["defs","read_mcms"]
    if make_plots:
        my_base.append("save_netcdf")
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
    result_directories = ["/Volumes/scratch/output/","/Volumes/scratch/output/",
            "/Volumes/scratch/output/","/Volumes/scratch/output/",
            "/Volumes/scratch/output/"]
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
    over_write_years = [1979,2008]
    #over_write_years = [1979,1980]

    # Here you can alter the default behavior as determined
    # by defs_vX.py and possibly setup_vX.py.
    defs_set = {}
    if pick <= 1:
        defs_set = {"keep_log":False}
    elif pick == 2:
        defs_set = {"keep_log":False,"read_scale":1.0}
    elif pick == 3:
        defs_set = {"keep_log":False}
    elif pick == 4:
        defs_set = {"keep_log":False}

    # --------------------------------------------------------------------------
    # Run main()
    # --------------------------------------------------------------------------

    msg = "\n\t====\tCenter Refine\t===="
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
        (im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
                dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
                bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
                bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
                super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
                var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
                no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
                land_gridids,troubled_centers) = fnc_out
        # Save memory
        del troubled_centers
        del lat_edges
        del lon_edges
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
    if over_write_years:
        super_years = over_write_years
    if over_write_out_path:
        out_path = over_write_out_path
    if over_write_slp_path:
        slp_path = over_write_slp_path

    header = "mcms_%s_%04d" % (model,int(super_years[0]))
    in_file = "%s%s%s" % (out_path,header,tail)

    if len(sys.argv) == 1:
        # Set definitions and instantiate read_mcms w/out a template
        what_do = {"model" : model,
                    "in_file" : in_file,
                    "out_file" : "",
                    "just_center_table" : True,
                    "detail_tracks" : "",
                    "as_tracks" : "",
                    "start_time" : "YYYY MM DD HH SEASON",
                    "end_time" : "YYYY MM DD HH SEASON",
                    "places" : ["GLOBAL"],
                    "include_atts" : False,
                    "include_stormy" : False,
                    "just_centers" : True,
                    "save_output" : False,
                    "overwrite" : False
                    }
        # Pass in model definitions, if sf_file available this is simple.
        if model in ["nra","nra2"]:
            # For the NCAR/NCEP Reanalysis 1 and 2 these values are provided
            # and nothing need be done.
            pass
        else:
            # Provide values
            what_do["tropical_end"] = row_end[tropical_n_alt]
            what_do["tropical_start"] = row_start[tropical_s_alt]
            what_do["maxID"] = maxid
            what_do["land_gridids"] = list[land_gridids]
    else:
        # Use provided template
        template = sys.argv[1]
        what_do = {"template":template}

    # Shortcut to keep parameter list shorter.
    specifics = {'over_write_years' : over_write_years,
                 'over_write_out_path' : over_write_out_path,
                 'shared_path' : shared_path,
                 'over_write_slp_path' : over_write_slp_path,
                 'model' : model,
                 'exit_on_error' : exit_on_error,
                 'make_plots' : make_plots,
                 'zmean' : zmean,
                 'land_sea' : land_sea,
                 'skip_high_lat' : skip_high_lat,
                 'fig_format' : fig_format,
                 'import_read' : import_read,
                 'skip_to_plots' : skip_to_plots
                 }

    msg = main(imports,defs_set,what_do,**specifics)
    print msg
