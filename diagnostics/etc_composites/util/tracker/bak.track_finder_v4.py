""" This module extracts cyclone tracks from input lists of centers
    from a series of sea level pressure fields. The is module contains
    the main logic of this process.
#!/usr/bin/env python -tt

    Options/Arguments:
        defs_set -- directory of options.
        imports -- list of modules to import.
        start_tstep -- starting timestep.
        end_tstep -- ending timestep.
        out_path -- path to directory for storing results.
        center_file -- output of center_finder.
        dumped_file -- discards file from refine_centers and center_finder.
        intensity_file -- file of cyclone intensity statistics from refine_centers.
        shared_path -- path to directory storing info about the data source.
        slp_path -- path to the data.
        year_start -- first year of data.
        year_end -- last year of data.
        model -- designator of the source of the data.
        get_var -- name of the variable to be extracted from the data.

    Returns/Creates:
        tracks_save -- ASCII file of candidate tracks found and kept.
        dumped_centers_file -- ASCII file of candidate centers found and
                               discarded as untrackable.

    Examples:

    Notes: See bottom of this document for extended notes that are denoted
           in the code.

    Memory Use: Depending on resolution and options expect at least 300MB per
            instance and up to 2 GB.

    Run Time: With the 60 Year NCEP Reanalysis I takes roughly 1 hour and uses
              ~2 GB of memory. This is on a Mac Pro with 2.26 GHz processors,
              12 GB of RAM, and a 3 disk RAID.

    Author: Mike Bauer  <mbauer@giss.nasa.gov>

    Log:
        2006/12  MB - File created.
        lost track of dates of updates and fixes... sorry
        2008/10  MB - Added input checks, docstring.
"""
import sys,os
import array
import defines

def process_data(values,outfile,minval,interval,verbose=False,raw=False) :
    """
    Convert to fractional percentage, find peak value etc.
    """

    step = interval

    binsum    = sum(values)
    i         = 0
    bin2gmt   = []
    lower_end = minval - step
    peak_frac = 0.0
    peak_y = -1000.0
    peak_y_x = 0

    for bin in values :
        lower_end = lower_end + step
        if i == 0 :
            min_x = lower_end-0.5*step
        if i == len(values)-1 :
            max_x = lower_end-0.5*step
        if binsum > 0:
            frac = float(bin)/float(binsum)*100.0
        else:
            frac = 0.0
        if frac > peak_frac :

            peak_frac = frac
            peak_y = bin
            peak_y_x = i

        if i == 0:
            min_x = lower_end+(0.5*step)
        if  i == len(values)-1:
            max_x = lower_end+(0.5*step)

        if raw:
            #bin2gmt.append("%f %f\n"%(lower_end+(0.5*step),bin))
            # done so -D option makes a 0 wind centered on 0 in the plot.
            bin2gmt.append("%f %f\n"%(lower_end,bin))
        else:
            bin2gmt.append("%f %f\n"%(lower_end+(0.5*step),frac))

        if verbose :
            if i == 0 :
                llower_end = lower_end - step
                print ( "Bin #%3d |  X  < %f\tCnt = %d" % (i,llower_end+step,bin))
            elif i == len(values)-1 :
                print ( "Bin #%3d | %f <= X\t--- Cnt = %d" % (i,lower_end,bin))
            else :
                print ( "Bin #%3d | %f <= X < %f\tCnt = %d" % (i,lower_end,lower_end+step,bin))
        i+=1

    if verbose:
        print ("Peak Fraction %f for bin %d = %f" % (peak_frac,peak_y_x,peak_y))
        print ("MinX_val      %f" % (min_x))
        print ("MaxX_val      %f" % (max_x))

    file1 = open(outfile, 'w')
    file1.writelines(bin2gmt)
    file1.close()

    return peak_frac,min_x,max_x

def rose_plot(alldat,plot_name,minbin,maxbin,incbin,verbose=False,fig_format='.eps',title="Bearing"):

    """
    Use GMT to plot a histogram.
    """
    import commands

    if verbose :
        print ("Number of bins : %d" % (len(alldat)))
        print ("Minimum bin    : %f" % (minbin))
        print ("Maximum bin    : %f" % (maxbin))
        print ("Bin interval   : %f" % (incbin))

    # Determine bin boundaries and dump to a txt file for GMT. Also, info for
    # fractional amount.
    peak_frac,min_x,max_x = process_data(alldat,"tmp.txt",minbin,incbin,verbose=verbose,raw=1)
    if verbose:
        print ("Peak Scaling Fraction %f" % (peak_frac))

    # Deal with various graphic output options
    defaults = "gmtset HEADER_FONT_SIZE 14p LABEL_FONT_SIZE 12p \
    ANOT_FONT_SIZE 10p PAPER_MEDIA letter DOTS_PR_INCH 600 \
    PAGE_ORIENTATION PORTRAIT"
    temp_ps      = "temp.ps"
    plot_name = plot_name + fig_format
    if fig_format == '.png':
        make_fig = "convert -trim -quality 90 -density 144 144 %s %s; rm -f %s" % (temp_ps,plot_name,temp_ps)
    elif fig_format == '.pdf':
        make_fig = "ps2eps --force --quiet --removepreview --rotate=+ --loose \
                temp.ps; ps2pdf13 -dEPSCrop -r144 temp.eps %s; rm temp.eps" % (plot_name)
        #make_pdf = "ps2pdf13 -dEPSCrop -r144 %s %s; rm -f %s" % (temp_ps,plot_name,temp_ps)
    elif fig_format == '.eps':
        make_fig = "ps2eps --force --quiet --removepreview \
        --rotate=+ --loose temp.ps ; mv temp.eps %s" % (plot_name)
    if verbose:
        print ("Making ",plot_name)

    # Determine intervals etc.
    x_label     = "'Bearing'"
    y_label      = '"Frequency Of Occurrence (%)"'

    #draw_histo = "psrose %s -: -A%s -S1.8in -R0/1/0/360 -B0.2g0.2:'Relative Frequency Of Occurrence':/30g30:.'Bearing': -Gblack -W0.75p,black -D > %s" % \
    #draw_histo = "psrose %s -: -A%s -S1.8in -R0/1/0/360 -B0.2g0.2:'Relative Frequency Of Occurrence':/30g30:.'Bearing': -G124 -W0.75p,black -D > %s" % \
    #             ("tmp.txt",repr(incbin),temp_ps)
    draw_histo = "psrose %s -: -A%s -S1.8in -R0/1/0/360 -B0.2g0.2:'Relative Frequency Of Occurrence':/30g30:.'%s': -G124 -W0.75p,black -D > %s" % \
                 ("tmp.txt",repr(incbin),title,temp_ps)


    #draw_histo = "psrose %s -: -A%s -S1.8in -R0/1/0/360 -B0.2g0.2/30g30 -G125 > %s" % \
    #                 ("tmp.txt",repr(incbin),temp_ps)

    todos = [defaults,draw_histo,"rm -f tmp.txt"]

    todos.append(make_fig)

    for CMD in todos :
        # watch running things in background/threads as some operations
        # must complete before others start and too use of common names
        # could cause overrunning for slow processes...
        if verbose :
            os.system("touch %s" % (plot_name))
        else :
            status = commands.getstatusoutput(CMD)
            #print (status,CMD)
            if status[0] != 0 :
                print ("plothisto ERROR\n",status)
                sys.exit()

def plot_hist(plt,numpy,x,y,width,stat_file,pname,title,xlab):
    total = y.sum()
    cumsum = [(float(z)/float(total))*100.0 for z in numpy.cumsum(y)]
    stat_save = open(stat_file,"w")
    msg = ''.join(["%8.3f" % (z) for z in x])
    stat_save.writelines("Bins  "+msg+"\n")
    msg = ''.join(["%8.3f" % (z) for z in cumsum])
    stat_save.writelines("CFrac "+msg+"\n")
    hmean = float(x.sum())/float(len(x))
    hmin = 0
    for tmp in y:
        if tmp > 0.0:
            break
        hmin += 1
    hmax = -1
    for tmp in y[::-1]:
        if tmp > 0.0:
            break
        hmax -= 1
    msg = "%7.3f" % (hmean)
    stat_save.writelines("Mean  "+msg+"\n")
    msg = "%7.3f" % (x[hmin])
    stat_save.writelines("Min   "+msg+"\n")
    msg = "%7.3f" % (x[hmax])
    stat_save.writelines("Max   "+msg+"\n")
    stat_save.close()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.bar(x,y,width=width,color='0.6',edgecolor='k')
    # Add Labels and such
    ax.set_xlabel(xlab)
    ax.set_ylabel("Count")
    # Add title
    ax.set_title(title)
    #        ax.grid(True)
    # Save to File
    fig.savefig(pname,dpi=144,orientation='landscape')
    plt.close('all')
    return "Made %s" % (pname)

def setup_bins(bins_left_edge):
    """Set up bins for histograms"""
    # Make a few extras
    bins_width = abs(bins_left_edge[0]-bins_left_edge[1])
    bins_centers = bins_left_edge + 0.5*bins_width
    bins_right_edge = bins_left_edge + bins_width

    #     # To print out bins
    #     fmt = "Bin % 4d: % 7.2f <= % 7.2f < % 7.2f"
    #     for bin in range(len(bins_left_edge)):
    #         print fmt % (bin,bins_left_edge[bin],bins_centers[bin],
    #                      bins_right_edge[bin])
    #     import sys;sys.exit()

    return (bins_left_edge,bins_centers,bins_right_edge,bins_width)

def get_bin_index(value,bins,bin_width):
    """Find the correct bin to put value into"""
    if value<=bins[0]:
        bin_index = 0
    elif value>=bins[-1]:
        bin_index = len(bins) - 1
    else:
        bin_index = int((value-bins[0])/bin_width)

    return bin_index

def rewrite(in_file,years,action="w",reorder=False):
    import os
    print ("\tRe-writing %s as yearly files..." % (in_file))
    did_files = []
    #---------------------------------------------------------------------------
    # Partition unified file by year
    #---------------------------------------------------------------------------

    if len(years) < 2:
        out_file = in_file.replace("%4d_%4d" % (years[0],years[-1]),
                                   "%4d" % (years[0]))
        # Only a single year
        os.rename(in_file,out_file)
        return([out_file])

    #JIMMY NEW CODE  USE A DICTIONARY CALLED yrlydir
    # TO HOLD THE HANDLES FOR THE FILES YOU WILL WRITE TO.

    yrlydir = {}

    for nyear in years:

        out_file = in_file.replace("%4d_%4d" % (years[0],years[-1]),
                               "%4d" % (nyear))
        save_file = open(out_file,action)
        yrlydir[nyear] = save_file
        did_files.append(out_file)

    # LEAVE THIS PIECE AS MIKE HAD IT. OPEN THE FILE WITH ALL OF THE
    # DIFFERENT YEARS TRACKS

    read_file = open(in_file,"r")
    yyyy = years[:]
    first_year = years[0]
    yyyy.reverse()

    this_year = yyyy.pop()
    last_year = this_year - 1

    # GO THROUGH EACH LINE IN THE FILE, EXAMINE THE YEAR, FIND THE
    # THE DICTIONARY (yrlydir) CORRESPONDING TO THE YEAR AND WRITE
    # THE LINE TO THAT FILE.
    for line in read_file:
        year_line = int(line[0:4])
        savetofile = yrlydir[year_line]
        savetofile.writelines(line)


    yrlydirkeys = yrlydir.keys()
    for nyear in yrlydirkeys:
        filetoclose = yrlydir[nyear]
        filetoclose.close()



    # For detached file I need to reorder as append didn't tac things
    # on in chronological order
    if reorder:
        print ("\t\tReordering....")
        rev_file = out_file.replace(str(years[-1]),str(years[0]-1))
        for loop_year in years:
            rev_file = rev_file.replace(str(loop_year-1),str(loop_year))
            read_f = open (rev_file,"r")
            ucis = {}
            for line in read_f:
                parts = line.split()
                uci = parts[14]
                ucis[uci] = line
            read_f.close()
            items = list(ucis.keys())
            items.sort()
            # Write to tmp file
            write_f = open("tmp.txt","w")
            for item in items:
                write_f.writelines(ucis[item])
            write_f.close()
            # Replace original
            #os.rename('tmp.txt',rev_file)
            os.system('mv %s %s' % ('tmp.txt',rev_file))
            print ("\t\t\t%s" % (rev_file))
    print ("Done")

    return (did_files)


def main(defs_set,imports,years,out_path,centers_file,shared_path,slp_path,
         model,exit_on_error,save_plot,track_stats):

    # --------------------------------------------------------------------------
    # Setup Section
    # --------------------------------------------------------------------------
    print ("\tSetting up....",)


    # Import needed modules.
    for i in imports:
        exec(i, globals())

    defs_v4 = globals()['defs']
    numpy = globals()['numpy']
    strip_read = globals()['strip_read']
    gcd = globals()['gcd']
    ij2grid = globals()['ij2grid']
    grid2ij = globals()['grid2ij']
    rhumb_line_nav = globals()['rhumb_line_nav']
    clean_dict = globals()['clean_dict']
    jd_key = globals()['jd_key']
    resort = globals()['resort']
    try_to_connect = globals()['try_to_connect']

    import pickle

    # Fetch definitions.
    defs = defs_v4.defs(**defs_set)

    # What sort of figures
    #    fig_format = ".png"
    #    fig_format = ".eps"
    fig_format = ".pdf"

    # pre-bind for speed
    gcd = gcd.gcd
    ij2grid = ij2grid.ij2grid
    grid2ij = grid2ij.grid2ij
    rhumb_line_nav = rhumb_line_nav.rhumb_line_nav
    strip_read = strip_read.strip_read
    clean_dict = clean_dict.clean_dict
    jd_key = jd_key.jd_key
    resort = resort.resort
    try_to_connect = try_to_connect.try_to_connect
    cos = math.cos; sin = math.sin
    d2r = math.radians; r2d = math.degrees
    atan2 = math.atan2
    if save_plot:
        Save_NetCDF = save_netcdf.Save_NetCDF
    if track_stats:
         Plot_Map = plot_map.plotmap
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
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
        # Save memory
    if not defs.troubled_filter:
        del troubled_centers
    del land_gridids
    del lat_edges
    del lon_edges
    del fnc_out

    # Update over_write values
    if slp_path:
        slp_path = over_write_slp_path
    if years:
        print ("jimmy, hacker: ")
        print (years)
        super_years = years

    # Create out_path if it doesn't exist.
    if over_write_out_path:
        out_path = over_write_out_path
        if not os.path.exists(out_path):
            dirs = list(map(os.makedirs, (out_path,
            out_path+'/comps/',
            out_path+'/pdfs/',
            out_path+'/stats/',
            out_path+'/netcdfs/',
            out_path+'/figs/pdfs/',
            out_path+'/figs/comps/')))
            print ("Directory %s Created." % (out_path))

    if defs.keep_log:
        # Redirect stdout to file instead of screen (i.e. logfiles)
        tmp = "%s/logfile" % (out_path)
        lfile = make_unique_name(os,tmp,".txt")
        screenout  = sys.stdout
        log_file   = open(lfile, 'w')
        sys.stdout = log_file

    # timestep in julian days
    # delta_jdate = int(((timestep/24.0)*100))
    # Jeyavinoth: above line of code, 
    # computes the time step that is used adates
    # this value is used to do a sanity check below, to make sure that the 
    # adates dont increment by more than 25
    # hence I change this to hours, instead of days
    delta_jdate = int(timestep)

    fnc_out = []
    tf_file = "%stf_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(tf_file, 'rb'))
        (tdict,lwdict) = fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (tf_file))
    del lwdict
    del fnc_out

    # fnc_out some things
    defs.maxdp = defs.maxdp*timestep
    defs.travel_distance = defs.travel_distance*timestep

    # Shortest allowable track length (based on time elapsed between pnts, such
    # that 1 timestep spans 2 pnts).
    min_trk_cnt = int(defs.age_limit/timestep) + 1

    # Gives a bergero of 1 at 6 hPa per timestep at 60 degrees
    sin60 = math.sin(d2r(60.0))/float(timestep)
    ## Gives a bergero of 1 at 12 hPa per timestep at 60 degrees
    # sin60 = math.sin(d2r(60.0))/float(2*timestep)
    ## Gives a bergero of 1 at 10 hPa per timestep at 60 degrees
    # sin60 = math.sin(d2r(60.0))/float(1.67*timestep)

    # Skip high latitude for angle, separation, area
    # if non-zero the value is the absolute latitude
    # above which no values retained.
    skip_high_lat = 85

    # Limit bearing stats and StheC to centers with at least
    # this must separation as likely to be large angle
    # changes when centers are say 10 km apart due to
    # a stalled/blocked cyclone.
    # 2 deg lat equivalent separation
    # Jeyavinoth: change following
    # min_sep = 222.0
    # with
    min_sep = (222.0/6.0)*float(timestep)
    # Jeyavinoth: End

    inv_accuracy = 1.0/defs.accuracy

    # Summary Stats: Checks on operation to report and catch oddities.
    known_flags = {5 : "Failed trackable center",
                   6 : "Failed track lifetime filter",
                   7 : "Failed track travel filter",
                   8 : "Failed track minimum SLP filter",
                   10: "Failed extratropical track filter"}
#                   10 : "Troubled center"}
    flag_files = {0 : "passed",
                  5 : "trackable",
                  6 : "lifetime",
                  7 : "travel",
                  8 : "minslp",
                  10 : "tropical"}
    nflags = 11
    total_time_steps = 0
    flags_used = [5,6,7,8,10] # used flags
    super_total_centers_read = 0
    super_total_tracks = 0
    super_total_centers_cnt = [0]*nflags#*11 # make size of total flag count

    if save_plot:
        flag_cnt = numpy.zeros((jm*im,nflags),dtype=numpy.float)
        # to see touch concerns
        touch_concerns =  numpy.zeros((jm*im),dtype=numpy.float)

    if track_stats:
        # insert quantity info:
        # 0 - CisG
        # 1 - StheC
        # 2 - CisB
        # 3 - Dissimilarity Scores
        # 4 - Bearing
        # 5 - Ccount
        # 6 - Dscore used (selected) when dscore used at all
        # 7 - Dscore not used (unselected values)  when dscore used at all
        stat_groups = ["CisG","StheC","CisB","Dscore","Bearing",
                       "Ccount","Dscore_Used","Dscore_Unused"]

        # For frequency plots
        data_index = [len(stat_groups)]
        data_index.append(jm*im)
        bucket_freq_sum = numpy.zeros(data_index,dtype=numpy.float)
        bucket_freq_cnt = numpy.zeros(data_index,dtype=numpy.float)

        big_bins = [x for x in range(len(stat_groups))]

        # CisG bins for histograms
        bin_width = 0.1
        bins_left_edge = numpy.arange(0.0,5.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        CisG_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                     tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[0] = CisG_bins

        # StheC bins for histograms
        bin_width = 0.1
        bins_left_edge = numpy.arange(0.0,2.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        StheC_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                     tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[1] = StheC_bins

        # CisB bins for histograms
        bin_width = 0.1
        bins_left_edge = numpy.arange(0.0,2.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        CisB_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                     tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[2] = CisB_bins

        # Dscore bins for histograms
        bin_width = 0.1
        bins_left_edge = numpy.arange(0.0,5.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        Dscore_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                     tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[3] = Dscore_bins

        # Bearing bins for histograms
        bin_width = 5.0#45.0
        bins_left_edge = numpy.arange(0.0,360.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        bearing_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                     tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[4] = bearing_bins

        # Ccount bins for histograms (number of potential connections)
        bin_width = 1.0
        bins_left_edge = numpy.arange(0.0,10.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        Ccount_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                     tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[5] = Ccount_bins

        # Dscore_Used bins for histograms (these of the dscores used to make choice)
        bin_width = 0.1
        bins_left_edge = numpy.arange(0.0,5.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        Dscore_Used_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                       tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[6] = Dscore_Used_bins

        # Dscore_Unused bins for histograms (these are the pool of dscores when a choice is made)
        bin_width = 0.1
        bins_left_edge = numpy.arange(0.0,5.0,bin_width)
        tmp = setup_bins(bins_left_edge)
        Dscore_Unused_bins = [numpy.zeros(len(bins_left_edge),dtype=numpy.integer),
                       tmp[0],tmp[1],tmp[2],tmp[3]]
        big_bins[7] = Dscore_Unused_bins

    # Quit on error else just send message to logfile?
    if exit_on_error:
        do_this = 'print (smsg); print (msg); sys.exit("\t\tDate_Stamp:"+date_stamp)'
    else:
        do_this = 'print (smsg); print (msg); print ("\t\tDate_Stamp:"+date_stamp)'

    print ("Done\n\tReading Centers....",)

    #---------------------------------------------------------------------------
    # Read all centers into memory
    #---------------------------------------------------------------------------

    # Counters for report
    centers = []
    centers_append = centers.append
    # Read all centers into memory
    i = 0
    years = [x for x in range(int(super_years[0]),int(super_years[-1])+1)]
    for loop_year in years:
        # Define some files
        header = "mcms_%s_%04d_" % (model,loop_year)
        centers_file = "%s%scenters.txt" % (out_path,header)
        # Open files for read.
        centers_read = open(centers_file,"r")
        ingested = 0
        for line in centers_read:
            # Process line
            fnc = strip_read(line)
            centers_append(fnc)
            ingested += 1
        centers_read.close()
        if i == 0:
            print ("                   %d (%d)" % (loop_year,ingested),)
        elif loop_year == years[-1]:
            print ( "%d (%d)" % (loop_year,ingested))
        elif i < 55555:
            print ("%d (%d)" % (loop_year,ingested),)
        else:
            print ("%d (%d)" % (loop_year,ingested))
            i = -1
        i += 1
    super_total_centers_read = len(centers)
    print ("Jimmy: super_total_centers_read")
    print (super_total_centers_read)

    # Ensure sorted and put in inverse order so t=0 at end of array
    centers.sort()
    centers.reverse()
    # Make copy for later use
    center_orig = centers[:]

    # # Jeyavinoth: Start
    # # commented out till "Jeyavinoth: End"
    # # Extract all unique Julian dates
    # # JIMMY: the lack of unique julian dates might be an issue.
    # alldates = sorted(dict((x,1) for x in [x[4] for x in centers]).keys())
    # nsteps = len(alldates)
    # # JB/JJ removed print here
    # # print ("Jimmy version 1 of alldates" )
    # # print (alldates)
    #
    # # This is set in setup_vX.py
    # jd_fake = 0
    # print ("Jimmy, the calendar is: "+the_calendar)
    # if the_calendar != 'standard':
    #     # As no calendar detected assume non-standard
    #     jd_fake = 1
    #
    # if the_calendar == 'proleptic_gregorian':
    #   jd_fake = True
    # # jd_fake = False #### JJ sets this to fake to make it work with leap years
    # if jd_fake:
    #     date_stamps = sorted(dict((x,1) for x in ["%4d%02d%02d%02d" % (x[0],x[1],x[2],x[3]) for x in centers]).keys())
    # else:
    #     dtimes = [netcdftime.DateFromJulianDay(adate*0.01) for adate in alldates]
    #     date_stamps = ["%4d%02d%02d%02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]
    # # Jeyavinoth: End

    # Jeyavinoth 
    # replaced above commented out code with the following
    # here the date stamps are the values saved in the center data 
    alldates = sorted(dict((x,1) for x in [x[4] for x in centers]).keys())
    nsteps = len(alldates)
    date_stamps = sorted(dict((x,1) for x in ["%4d%02d%02d%02d" % (x[0],x[1],x[2],x[3]) for x in centers]).keys())

    # JB/JJ removed print here
    # print (date_stamps)
    # JIMMY, forcing the lenght of alldates to be to corrects does not solve the problem
    #sorteddates=sorted(date_stamps)
    #alldates=array.array('i',(i+0 for i in range(0,2920)))
    #print ("Jimmy new alldates" )
    #print (alldates)

    print ("\tDone\n\tFinding Dissimilarity Scores....",)

    #---------------------------------------------------------------------------
    # Main Program Logic
    #---------------------------------------------------------------------------
    # Save track stuff to a master file for all times and breakup later

    tracks_file = centers_file.replace("centers","tracks")
    # JIMMY: issue is here for file-dir name. problem is my dir name has the year in it.
    # simplest solution: dont use the year in the directory name.
    tracks_file = tracks_file.replace(str(loop_year),
                                      "%4d_%4d" % (years[0],years[-1]))

    dumped_file = tracks_file.replace("tracks","dumped_centers")

    # Open files for storage
    if track_stats != 2:
        tracks_save = open(tracks_file,"w")
        if defs.keep_discards:
            dumped_centers_save = open(dumped_file,"w")
        else:
            dumped_file = ""

    # Containers
    live_tracks = {}
    dead_tracks = {}
    current_centers = []
    past_centers = []
    dissimilar_score = 0.0

    # Tracking Step 1: See Note 4
    step = -1
    adatelast = alldates[0]
    print ("Jimmy adate last")
    print (alldates[-1])

    #Jeyavinoth: 
    jj_dlist = numpy.zeros((10, 1))
    # Jeyavinoth: End
    for adate in alldates:

        # Check for gapless alldates
        if adate > alldates[0]:
            if adate-adatelast > delta_jdate:
                err_num = 1
                smsg = "\n\tFail Check %d: A timestep(s) skipped." % (err_num)
                msg = "\t\tadate: %d adatelast: %d" % (adate,adatelast)
                exec(do_this)
        adatelast = adate
        step += 1
        # Tracking Step 2: See Note 5
        if adate == alldates[0]:
            # Add all current_centers as track starts
            current = True
            current_centers = []
            while current:
                try:
                    center = centers.pop()
                except: # Hit end of list
                    break
                if center[4] == adate:
                    current_centers.append(center)
                else:
                    current = False
                    centers.append(center) # Overshoot, put back on
            for x in current_centers:
                live_tracks[x[14]] = [(x[14],"")]
            continue # Get another date
        else:
            # Move last set of current_centers to past_centers
            past_centers = current_centers # Set to past centers
            current = True
            current_centers = []
            while current:
                try:
                    center = centers.pop()
                except: # Hit end of list
                    break
                if center[4] == adate:
                    current_centers.append(center)
                else:
                    current = False
                    centers.append(center) # Overshoot, put back on
        deaddate = date_stamps[step]
        
        #print "Doing",deaddate#,step
        #print "\tFound current and past centers:",len(current_centers),len(past_centers)

        # Tracking Step 3: See Note 6
        past_scores = {}
        for past in past_centers:
            # All current_centers w/in search radius of past.
            # Note that a center in past_centers might not
            # fall into candidates at all
            candidates = [x for x in current_centers
                         if x[7] in tdict[past[7]]]

            # Selection based on minimizing the dissimilar_score
            #  between past and all candidates.
            scores = {}

            if track_stats:
                # Accrue Freq plot
                Ccount = len(candidates)
                bucket_freq_sum[5,past[7]] += Ccount
                bucket_freq_cnt[5,past[7]] += 1
                # Bin for histogram
                bin_index = get_bin_index(Ccount,Ccount_bins[1],float(Ccount_bins[4]))
                Ccount_bins[0][bin_index] += 1

            if candidates:

                clon = past[6]*0.01
                clat = 90.0 - past[5]*0.01

                for pnt in candidates:

                    if pnt[7] == past[7]:
                        # skip same grid
                        dissimilar_score = 0.0
                        scores[pnt[14]] = dissimilar_score
                        continue

                    plon = pnt[6]*0.01
                    plat = 90.0 - pnt[5]*0.01

                    if defs.use_gcd:
                        distx = gcd(clon,clat,plon,plat)
                    else:
                        fnc = rhumb_line_nav(plon,plat,clon,clat)
                        distx = fnc[1]
                        bearing = fnc[0]

                    # Close is Best
                    CisB = distx/defs.travel_distance
                    if track_stats:
                        # Acrue Freq plot
                        bucket_freq_sum[2,pnt[7]] += CisB
                        bucket_freq_cnt[2,pnt[7]] += 1
                        # Bin for histogram
                        bin_index = get_bin_index(CisB,CisB_bins[1],float(CisB_bins[4]))
                        CisB_bins[0][bin_index] += 1

                    # Change is Gradual
                    mid_lat = 1.0/abs(sin(d2r((plat+clat)*0.5)))
                    CisG = abs(past[8]-pnt[8])*inv_accuracy*sin60*mid_lat
                    if track_stats:
                        # Accrue Freq plot
                        bucket_freq_sum[0,pnt[7]] += CisG
                        bucket_freq_cnt[0,pnt[7]] += 1
                        # Bin for histogram
                        bin_index = get_bin_index(CisG,CisG_bins[1],float(CisG_bins[4]))
                        CisG_bins[0][bin_index] += 1

                    # Because of the limitations of bearing finding at high latitudes
                    # and because a nearly stationary center (i.e., small distx) the
                    # apparent bearing could be large but not relevant.
                    if distx > min_sep and abs(clat) <= skip_high_lat:
                        # Bearing always from rhumb line, gcd can't be used!
                        fnc = rhumb_line_nav(
                            plon,plat,clon,clat,True)
                        bearing = fnc[0]
                        if track_stats:
                            # Acrue Freq plot
                            bucket_freq_sum[4,pnt[7]] += bearing
                            bucket_freq_cnt[4,pnt[7]] += 1
                            # Bin for histogram
                            bin_index = get_bin_index(bearing,bearing_bins[1],float(bearing_bins[4]))
                            bearing_bins[0][bin_index] += 1

                        # Stay the Coarse
                        # 1 at 0deg or 180deg
                        # 0 at 90deg
                        # if bearing greater than 180 discourage by
                        # increasing from 1 at 360deg and 180deg to 2 at 270deg
                        if bearing <= 180.0:
                            StheC = abs(bearing-90.0)/90.0
                        else:
                            StheC = (-1.0*abs(bearing-270.0)/90.0) + 2.0
                        if track_stats:
                            # Accrue Freq plot
                            bucket_freq_sum[1,pnt[7]] += StheC
                            bucket_freq_cnt[1,pnt[7]] += 1
                            # Bin for histogram
                            bin_index = get_bin_index(StheC,StheC_bins[1],float(StheC_bins[4]))
                            StheC_bins[0][bin_index] += 1
                    else:
                        bearing = 0.0
                        StheC = 0.0

                    # Weighting by CisB means that large coarse or pressure
                    # changes not as important if grids very close.
                    dissimilar_score = CisB*(StheC + CisG)
                    scores[pnt[14]] = dissimilar_score # key by current uci
                    if track_stats:
                        # Accrue Freq plot
                        bucket_freq_sum[3,pnt[7]] += dissimilar_score
                        bucket_freq_cnt[3,pnt[7]] += 1
                        # Bin for histogram
                        bin_index = get_bin_index(dissimilar_score,Dscore_bins[1],float(Dscore_bins[4]))
                        Dscore_bins[0][bin_index] += 1

            # Example of past_scores nested dictionary:
            # keyed on a prior center with dissimilar_scores for each
            # candidate among all current_centers.
            # {19960101001742823250:
            #        {19960101061741323000: 0.085061230289818587}}
            past_scores[past[14]] = scores

            if track_stats and len(scores) > 1:
                # only when multiple choices possible
                for peach in scores:
                    pnt = -1
                    for cc in candidates:
                        if cc[14] == peach:
                            pnt = cc[7]
                            break
                    if pnt < 0:
                        sys.exit("pnt Error: %s" % (pnt))
                    bucket_freq_sum[7,pnt] += scores[peach]
                    bucket_freq_cnt[7,pnt] += 1
                    bin_index = get_bin_index(scores[peach],Dscore_Unused_bins[1],float(Dscore_Unused_bins[4]))
                    Dscore_Unused_bins[0][bin_index] += 1

        # Tracking Step 4: See Note 7
        # FIX? sort order of past_centers has some effect
        #    see diff with v2 and v3 for usi 20080903001725023750  20080903121700018000
        #    with v3 see as one track and v2 as two tracks.
        for past in past_centers:

            # See if past can be connected to a current center
            tfpick = try_to_connect(copy,past[14],past_scores)

            if tfpick[1] == 1:
                # A connection was made
                # Remove past from further consideration
                del past_scores[past[14]]

                # Cull the current center from further consideration
                past_scores = clean_dict(past_scores,tfpick[0])

                if track_stats and scores:
                    for peach in past_scores:
                        pnt = past[7]
                        ss = list(past_scores[peach].values())
                        if not ss:
                            break
                        bucket_freq_sum[6,pnt] += ss[0]
                        bucket_freq_cnt[6,pnt] += 1
                        # Bin for histogram
                        bin_index = get_bin_index(ss[0],Dscore_Used_bins[1],float(Dscore_Used_bins[4]))
                        Dscore_Used_bins[0][bin_index] += 1

                # Update live_tracks
                new_track = True

                for usi in live_tracks:
                    # Continuation of a existing track
                    if past[14] == live_tracks[usi][-1][0]:
                        live_tracks[usi].append((tfpick[0],tfpick[2]))
                        new_track = False
                        break
                if new_track:
                    # Create a new track
                    live_tracks[past[14]] = [(past[14],""),(tfpick[0],tfpick[2])]
            elif tfpick[1] == 0:
                # No connection made
                # Update past_scores to prevent duplication
                del past_scores[past[14]]
            else:
                err_num = 2
                smsg = "\n\tFail Check %d: No discard or use of a connection" % (err_num)
                msg = "\t\tpast usi and score" % (past[14],past_scores)
                exec(do_this)
        #print "\tLive Tracks cnt:",len(live_tracks)

        # Saved_tracks get large and slow to search so separate
        # tracks into 'live' (last entry was current datetime),
        # 'dead' (last entry was too old to possibly be used again).
        test = list(live_tracks.keys())
        test.sort()
        for usi in test:
            # See if last entry was today
            lasttrack = live_tracks[usi][-1][0]
            if lasttrack[:10] != deaddate:
                # Dead track removed from live_tracks
                dead_tracks[usi] = live_tracks.pop(usi)

        #print "\tDead Tracks cnt:",len(dead_tracks)

    # Move all remaining live tracks to dead... clearly these did
    # not terminate in the normal way, just as tracks starting on
    # t=0 might not be the full track.
    for usi in list(live_tracks.keys()):
        dead_tracks[usi] = live_tracks.pop(usi)

    # Make a dictionary of centers to
    # speed up recalls, note chronological
    # nature of centers is lost.
    centers = center_orig
    hits = {}
    for each in centers:
        hits[each[14]] = each

    print ("Done\n\tFiltering Tracks....",)
    print ("\tNumber of original centers",len(hits))
    #print "\tNumber of potential tracks",len(dead_tracks),
    
    if track_stats:
        for loopy in range(len(stat_groups)):

            use_bins = big_bins[loopy]
            x = use_bins[1]
            y = use_bins[0]
            # Jeyavinoth 1hr: I turn this off here
            # if there are no cases found, I skip onto the next plot
            if (y.sum() == 0):
              print('\n****\nJeyavinoth: Skipping %s, %s\n****\n'%(title, xlab))
              import pdb; pdb.set_trace()
              continue

            # Jeyavinoth 1hr end
            width = use_bins[4]
            title = "%s %4d-%4d" % (model,years[0],years[-1])
            xlab = stat_groups[loopy]
            stat_file = "%s%s_%s_%4d_%4d.txt" % (out_path,model,stat_groups[loopy],years[0],years[-1])
            pname = "%sfigs/%s_hist_%s_%4d_%4d%s" % (out_path,model,stat_groups[loopy],years[0],years[-1],fig_format)
            msg = plot_hist(plt,numpy,x,y,width,stat_file,pname,title,xlab)
            print ("\t\t"+msg)

            bave = numpy.zeros(im*jm,dtype=numpy.float)
            for i in range(im*jm): # loop over each grid
                if bucket_freq_cnt[loopy,i] >= 1:
                    bave[i] = numpy.divide(bucket_freq_sum[loopy,i],bucket_freq_cnt[loopy,i])
                else:
                    bave[i] = 0.0
            pname = "%sfigs/%s_freq_%s_%4d_%4d%s" % (out_path,model,stat_groups[loopy],years[0],years[-1],fig_format) 
            fplot =  Plot_Map(missing=0.0,color_scheme="jet")
            fplot.create_fig()
            fplot.add_field(lons,lats,bave,ptype='pcolor',)
            fplot.finish(pname)
            pname = pname.replace("/figs","/netcdfs")
            pname = pname.replace(fig_format,".nc")
            save_it = Save_NetCDF(bave,lons,lats,pname,0)

        #pname = "%sfigs/%s_hist_rose_%4d_%4d%s" % (out_path,model,years[0],years[-1],fig_format)
        #use_bins = big_bins[4]
        #x = use_bins[1]
        #y = use_bins[0]
        #rose_plot(y,pname,use_bins[1][0],use_bins[1][-1],big_bins[4][4],verbose=0,fig_format=fig_format)

    if track_stats == 2:
        return

    # Refactor Tracks:
    # 1) Update each center's usi, i.e., assign to a track
    # 2) Apply post-tracking filters
    #    a) Tropical Filter
    #    b) Minimum Lifetime
    #    c) Minimum Lifetime SLP
    #    d) Minimum Lifetime Travel
    used_usi = list(dead_tracks.keys())
    used_usi.sort()

    # Loop over tracks and find member centers
    for usi in used_usi:

        caught = []
        # Centers found with this usi
        caught = [hits[y[0]] for y in dead_tracks[usi]]

        # Get dissimilarity scores
        ds = [x[1] for x in dead_tracks[usi]]

        # Trim for speed as search pool shrinks
        for each in caught:
            del hits[each[14]]
        del dead_tracks[usi]

        # Apply Tropical Test:
        #   Whole track discarded if track never leaves the tropics.
        extra_tropical_system = [x[5] for x in caught if
                           abs(90-x[5]*0.01) >= defs.tropical_boundary_alt]
        if not extra_tropical_system:
            if defs.keep_discards:
                for part in caught:
                    msg = defs.center_fmt2 % (part[0],part[1],part[2],part[3],
                                              part[4],part[5],part[6],part[7],
                                              part[8],part[9],part[10],10,
                                              part[12],part[13],part[14],
                                              part[15])
                    dumped_centers_save.writelines(msg)
                    super_total_centers_cnt[10] += 1
                    # Jeyavinoth
                    jj_dlist[0] += 1
                    if save_plot:
                        flag_cnt[part[7],10] += 1
            continue

        # Don't apply remaining filters is track starts in the very
        # 1st timestep as it could have been truncated and so
        # might incorrectly fail these tests. Same idea if last member
        # of the track in the last timestep.
        do_filter = 1
        if usi.startswith(date_stamps[0]):
            do_filter = 0
        if caught[-1][14].startswith(date_stamps[-1]):
            do_filter = 0

        if do_filter:

            if save_plot and defs.troubled_filter:
                # To make map of tracks that touch troubled grids uncomment
                # and comment minimum lifetime flag_cnt
                in_trouble = [x for x in caught if x[7] in troubled_centers]
                if in_trouble:
                    for part in caught:
                        touch_concerns[part[7]] += 1

            # Apply minimum lifetime
            if len(caught) < min_trk_cnt:

                if defs.keep_discards:
                    for part in caught:
                        msg = defs.center_fmt2 % (part[0],part[1],part[2],part[3],
                                                  part[4],part[5],part[6],part[7],
                                                  part[8],part[9],part[10],6,
                                                  part[12],part[13],part[14],
                                                  part[15])
                        dumped_centers_save.writelines(msg)
                        # Jeyavinoth
                        jj_dlist[1] += 1
                        super_total_centers_cnt[6] += 1
                        if save_plot:
                            flag_cnt[part[7],6] += 1
                continue
            # Apply minimum lifetime SLP
            min_val = min(x[8] for x in caught)

            if min_val > defs.keep_slp:
                if defs.keep_discards:
                    for part in caught:
                        msg = defs.center_fmt2 % (part[0],part[1],part[2],part[3],
                                                  part[4],part[5],part[6],part[7],
                                                  part[8],part[9],part[10],8,
                                                  part[12],part[13],part[14],
                                                  part[15])
                        dumped_centers_save.writelines(msg)
                        # Jeyavinoth
                        jj_dlist[2] += 1
                        super_total_centers_cnt[8] += 1
                        if save_plot:
                            flag_cnt[part[7],8] += 1
                continue

            # Apply Minimum Lifetime Travel:
            # Methods:
            #  1) total distance traveled between segments
            #  2) distance between start and end centers
            #  3) maximum displacement from start center
            #
            # Note option to discard tracks that never
            # leave high topography regions... likely noise
            #
            first = True
            total_travel = 0.0

            ## Method 1
            #for segment in caught:
            #    if first:
            #        first = False
            #        plon = segment[6]*0.01
            #        plat = 90.0 - segment[5]*0.01
            #        continue
            #    elon = segment[6]*0.01
            #    elat = 90.0 - segment[5]*0.01

            #    if defs.use_gcd:
            #        disty = gcd(plon,plat,elon,elat)
            #    else:
            #        fnc = rhumb_line_nav(elon,elat,plon,plat,True)
            #        disty = fnc[1]

            #    total_travel += disty
            #    plon = elon
            #    plat = elat

            # Method 3
            total_travel = 0.0
            for segment in caught:
                if first:
                    first = False
                    plon = segment[6]*0.01
                    plat = 90.0 - segment[5]*0.01
                    continue
                elon = segment[6]*0.01
                elat = 90.0 - segment[5]*0.01

                if defs.use_gcd:
                    disty = gcd(plon,plat,elon,elat)
                else:
                    fnc = rhumb_line_nav(elon,elat,plon,plat,True)
                    disty = fnc[1]

                if disty > total_travel:
                    total_travel = disty

            # Discard tracks that never leave troubled area
            if defs.troubled_filter:
                in_trouble = [x for x in caught if x[7] in troubled_centers]
                if len(in_trouble) == len(caught):
                    total_travel = 0.0

            if total_travel < defs.min_trk_travel:
                if defs.keep_discards:
                    for part in caught:
                        msg = defs.center_fmt2 % (part[0],part[1],part[2],part[3],
                                                  part[4],part[5],part[6],part[7],
                                                  part[8],part[9],part[10],7,
                                                  part[12],part[13],part[14],
                                                  part[15])
                        dumped_centers_save.writelines(msg)
                        # Jeyavinoth
                        jj_dlist[3] += 1
                        super_total_centers_cnt[7] += 1
                        if save_plot:
                            flag_cnt[part[7],7] += 1
                continue

        # Extract dissimilarity scores for track and alter usi
        ii = 0
        for part in caught:
            if ii == 0:
                dissimilarity = 0
            else:
                dissimilarity = int(ds[ii]*100.0)
            ii += 1
            msg = defs.center_fmt2 % (part[0],part[1],part[2],part[3],part[4],
                                      part[5],part[6],part[7],part[8],part[9],
                                      part[10],part[11],part[12],dissimilarity
                                      ,part[14],usi)
            tracks_save.writelines(msg)
            #Move and change
            super_total_centers_cnt[0] += 1
            if save_plot:
                flag_cnt[part[7],0] += 1
        super_total_tracks += 1
    tracks_save.close()

    if defs.keep_discards:
        # Dump untrackable centers
        for part in hits.values():
            msg = defs.center_fmt2 % (part[0],part[1],part[2],part[3],part[4],
                                      part[5],part[6],part[7],part[8],part[9],
                                      part[10],5,part[12],part[13],part[14],
                                      part[15])
            dumped_centers_save.writelines(msg)
            # Jeyavinoth
            jj_dlist[4] += 1
            super_total_centers_cnt[5] += 1
            if save_plot:
                flag_cnt[part[7],5] += 1
        dumped_centers_save.close()
    if track_stats:
        print ("\tDone")
    else:
        print ("Done")

    # import pdb; pdb.set_trace()
    #-------------------------------------------------------------------------
    # Clean up and Quit
    #-------------------------------------------------------------------------
    if defs.keep_discards:
        dumped_centers_save.close()

    # Final check to ensure order
    resort(tracks_file,strip_read,jd_key,defs.center_fmt2)
    if defs.keep_discards:
        resort(dumped_file,strip_read,jd_key,defs.center_fmt2)

    if defs.keep_log:
        log_file.close()
        sys.stdout = screenout # redirect stdout back to screen

    #
    # FINAL check to be sure all timesteps run and all centers accounted for.
    #
    report_file = tracks_file.replace("tracks.txt","tracks_report.txt")
    report_file = report_file.replace(out_path,"%sstats/" % (out_path))
    report_save = open(report_file,"w")

    msg1 = "Total Centers Read: %d\nTotal Centers Saved: %d (%6.2f%%)\nTotal Tracks: %d\nDiscards:\n"
    msg = msg1 % (super_total_centers_read,super_total_centers_cnt[0],
                  100.0*(float(super_total_centers_cnt[0])/float(super_total_centers_read)),super_total_tracks)
    report_save.writelines(msg)
    msg1 = "\t% 6d\t(%6.2f%%)\t%s\n"
    for e in flags_used:
        msg = msg1 % (super_total_centers_cnt[e],
                      100.0*(float(super_total_centers_cnt[e])/float(super_total_centers_read)),
                      known_flags[e])
        report_save.writelines(msg)

    # Final sanity check that everything is accounted for.
    if super_total_centers_read != sum(super_total_centers_cnt):
        msg = "Final Total Count Error:\n\tsuper_total_centers_read = %d\n\tsuper_total_centers_cnt = %s sum(%d)"
        sys.exit(msg % (super_total_centers_read,repr(super_total_centers_cnt),
                        sum(super_total_centers_cnt)))
    report_save.close()

    if save_plot:
        # Make frequency plot
        for flag in flag_files:

            # Just counts
            # FIX error with numpy/matplot lib and missing so just set to zero now
            #comp_out = numpy.where(flag_cnt[:,flag] < 1.,-10000000000.0,flag_cnt[:,flag])
            comp_out = numpy.where(flag_cnt[:,flag] < 1.,0.0,flag_cnt[:,flag])
            pname = "%sfigs/%s_freq_%s_%4d_%4d%s" % (out_path,model,flag_files[flag],
                                                     years[0],years[-1],fig_format) 
            fplot = Plot_Map(missing=0.0,color_scheme="jet")
            fplot.create_fig()
            fplot.add_field(lons,lats,comp_out,ptype='pcolor',)
            fplot.finish(pname)
            pname = pname.replace("/figs","/netcdfs")
            pname = pname.replace(fig_format,".nc")
#            pname = "%sfreq_%s_%4d_%4d.nc" % (out_path,flag_files[flag],years[0],years[-1])
            save_it = Save_NetCDF(flag_cnt[:,flag],lons,lats,pname,0)
            print ("\t\tCreated flag %d: %s" % (flag,pname))
        comp_out = numpy.where(touch_concerns < 1.,0.0,touch_concerns)
        pname = "%sfigs/%s_touch_concerns_%4d_%4d%s" % (out_path,model,
                                                        years[0],years[-1],fig_format)
        fplot = Plot_Map(missing=0.0,color_scheme="jet")
        fplot.create_fig()
        fplot.add_field(lons,lats,comp_out,ptype='pcolor',)
        fplot.finish(pname)
        pname = pname.replace("/figs","/netcdfs")
        pname = pname.replace(fig_format,".nc")
#        pname = "%stouch_concerns_%4d_%4d.nc" % (out_path,years[0],years[-1])
        save_it = Save_NetCDF(touch_concerns,lons,lats,pname,0)
        print ("\tCreated: %s" % (pname))

    return (tracks_file,dumped_file,years)

#---Start of main code block
if __name__=='__main__':

    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------

    # This next set of lines should be copied from setup_vX.py
    # Short names by which model will be labeled.
    model = defines.model

    # Halt program on error or just warn?
    exit_on_error = 0

    # Save/plot Stats (debugging mostly)
    save_plot = 1

    # Store tracking stats and make plots
    # Set track_stats = 2 to not save tracks to file... just stats and plots
    track_stats = 1

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # Basic standard Python modules to import.
    imports = []
    # Jeyavinoth: removed netcdftime from line below
    # imports.append("import math,numpy,netcdftime")
    imports.append("import math,numpy")

    imports.append("import copy")
    imports.append("import netCDF4 as NetCDF")
    imports.append("import _pickle as cPicke")
    if track_stats:
        imports.append("import matplotlib.pyplot as plt")

    # My modules to import w/ version number appended.
    my_base = ["defs","make_unique_name","strip_read","gcd","ij2grid",
            "grid2ij","clean_dict","jd_key","resort","rhumb_line_nav",
            "try_to_connect"]
    if save_plot or track_stats:
        my_base.append("save_netcdf")
        my_base.append("plot_map")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)

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
    over_write_years = defines.over_write_years
 
    # Here you can alter the default behavior as determined
    # by defs_vX.py and possibly setup_vX.py.
    defs_set = {"keep_log":False,"polar_filter":False,
                "troubled_filter":True}

    # Define some files
    centers_file = "centers.txt"
    dumped_centers_file = "dumped_centers.txt"

    # Shortcut to keep parameter list shorter.
    specifics = {'years' : over_write_years,
                 'out_path' : over_write_out_path,
                 'centers_file' : centers_file,
                 'shared_path' : shared_path,
                 'slp_path' : over_write_slp_path,
                 'model' : model,
                 'exit_on_error' : exit_on_error,
                 'save_plot' : save_plot,
                 'track_stats' : track_stats
                 }

    ### --------------------------------------------------------------------------
    ## Run main()
    ## --------------------------------------------------------------------------
    msg = "\n\t====\tCenter Tracking\t===="
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

    msg = main(defs_set,imports,**specifics)
    print ("\tCreated:",msg[0],msg[1])
    years = msg[2]    

    #print "JIMMY"      
    ## To test rewrite, comment out main call above and uncomment below
    #    super_years = [1989,1990]
    #    jimdir = '/Users/jfbooth/MCMS_DIR/CODE/TEST_TRACK_CENTER_REWRITE/'
    #    years = [x for x in range(int(super_years[0]),int(super_years[-1])+1)]
    #    msg = (jimdir+'%s/mcms_%s_%04d_%04d_tracks.txt' % (model,model,years[0],years[-1]),
    #         jimdir+'%s/mcms_%s_%04d_%04d_dumped_centers.txt' % (model,model,years[0],years[-1]))
    #    print msg
    
    # Rewrite tracks
    msg2 = rewrite(msg[0],years)
    
    # Append dumped
    msg3 = rewrite(msg[1],years,action="a",reorder=True)

# ------------------------------------------------------------------------------
# Notes: Rather than embed in code make reference here
# ------------------------------------------------------------------------------
Notes = """

4): Loop over each datetime connecting the 'current' set of centers
    to the 'past' set of centers via nearest neighbor and likeness
    arguments.

    Important objects:
    adate: the current julian date being examined.
    saved_tracks: dictionary with key value of the 1st uci
                  in the track. The values from each key are a list of
                  ucis making up that track.

5) Find all current centers. If first adate then all centers
   are new tracks and immediately get next adate. Otherwise,
   move the previous adate's current_centers to past_centers
   before updating the current_centers list.

   What can happen to each candidate from current_centers?
   A) If 1st datetime then all of current_centers goes to
      saved_tracks as a new track.
   B) The candidate center mismatches with all prior centers because:
      B1) The candidate center is too isolated from prior centers.
      B2) Other candidate centers are more more similar to all
          prior centers than is this candidate center.
            * Note the candidate center may be the start of a new
              track. This will be dealt with in the next iteration.
    C) Connects to a prior center and:
       C1) The candidate center is appended to an existing track
           of which the prior center is member.
       C2) The candidate center is appended to an new track of
           which the prior center becomes the first member.
    Important object:
    current_centers: list of the centers for adate.
    past_centers: the current_centers for the previous adate.
    saved_tracks: dictionary keyed on the 1st trackable point
                  containing list of all centers as tuples
                  (dislikeness_scores,choice_codes) in this track.

6) Find the dislikeness_scores for current and past centers.

   Important objects:
   candidates: list of all current_centers w/in the pre-defined
              search radius in tdict for each center in past_centers.
   dissimilar_score: Weighted estimate of the dissimilarity b/t
                     a past_center and a current_center. Based on proximity,
                     SLP difference, and implied relative coarse between the
                     centers.
   past_scores: dictionary keyed by past uci with
                the dissimilar_score for each candidate current center.

7) Loop over each prior center in past_scores and find the
   current center with the lowest dissimilar_score and then loop
   over all the other past_scores to ensure that other centers don't
   claim that current_center as well as are maybe more similar.

   If a conflict arises the following procedure is followed:
     a) the original past center uses the current center only if
        its dissimilar_score is lower than the current center's
        dissimilar_score with any other past center.
     b) if another past center has a lower dissimilar_score
        with the current center, then the original past center
        must try again with the next least dissimilar
        current center (if one exists) or go unattached.

   When a current center is associated with a past center into
   a track. Then those centers are no longer used to judge other
   centers for tracking purposes.

   The dissimilar_score for each track segment is stored as a
   rough measure of the uncertainty of that tracking choice.

   Past centers without a associated current center are treated
   as terminated tracks.

   Current centers without a trackable past center are treated
   as new tracks.

   Important objects:
   used_current_centers: list of current centers that have been
                         associated with a past center and should no longer be
                         considered for tracking.
   used_past_centers: same as above but for past centers
   tfpick: a tuple of the (uci,choice_flag).
         If choice_flag = 1, then a connection is made, if 0 then no
         connection found, if -1 something went wrong.

8) Searching very large lists is very slow. There are two approaches
   to this that are basically the same speed. Both depend on the list
   to be sorted, in this case chronologically, so that we can use shortcuts
   to limit the search. Both of these methods are about equally fast, both
   being 500x faster than doing the search over the whole list.

   Method 1: Reverse the list and remove items off and check to see if
   one correct day. This is done because removing items off the end of
   a list is much faster because the remaining list items don't have
   to be renumbered. In this case the search is limited to testing
   each item as if comes off until we've gone too far.

   Method 2: Assume that there are only a limited number of items that
   we want at any one search and limit how far forward we search... that
   is a sliding search window. Not used because it is more complicated
   than Method 1. Included here in case Method 1 ever proves problematic.
   # cinc = sets how far forward I will search for
   #        centers, set to 3 times the average number
   #        of centers per day to accommodate variability
   #        and future looks.
   # Basically this is a sliding search
   cmax = len(centers)
   cinc = (cmax/len(alldates))*3
   cstart = 0
   fstart = 0
   cend = cstart + cinc
   # don't overshoot array
   if cend > cmax:
       cend = cmax
   for adate in alldates:
       if adate == alldates[0]:
           nextdate = alldates[alldates.index(adate)+1]
           past_centers = []
           # generator to extract subset based on julian date (pyhack)
           current_centers = [x for x in
                              centers[cstart:cend] if x[4] == adate]
           # search forward of last current_center
           fstart = cstart + len(current_centers)
           fend = fstart + cinc
           # don't overshoot array
           if fend > cmax:
               fend = cmax
           future_centers = [x for x in
                             centers[fstart:fend] if x[4] == nextdate]
           # warn if the number of found centers is too close to the
           # assumption of cinc
           if len(current_centers) > cinc*0.8:
               print 'Warning cinc = %d may be too small. Found %d centers' \
                     % (cinc,len(current_centers))
               stop()
       elif adate == alldates[-1]:
           past_centers = current_centers
           current_centers = future_centers
           future_centers = []
       else:
           nextdate = alldates[alldates.index(adate)+1]
           past_centers = current_centers
           current_centers = future_centers
           # search forward of last current_center
           fstart = cstart + len(current_centers)
           fend = fstart + cinc
           # don't overshoot array
           if fend > cmax:
               fend = cmax
           future_centers = [x for x in
                             centers[fstart:fend] if x[4] == nextdate]
       # move search forward
       cstart = cstart + len(past_centers)
       cend = cstart + cinc
       # don't overshoot array
       if cend > cmax:
           cend = cmax

"""
