"""
Connects the attributed grids from pre_calculate_contours_vX.py 
to center/track data.
#/usr/bin/env python -tt

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
    2010/6 MB - File created.
"""
import sys, os


def attribute():
    return

def main(defs_set,imports,what_do,loop_year,out_path,
        shared_path,clevs,verbose,plot_contours):

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
    
    scnt = [0]*12

    # For unwinding reads
    ids = {'YYYY' : 0,'MM' : 1, 'DD' : 2, 'HH' : 3, 'JD' : 4,
           'CoLat' : 5, 'Lon' : 6, 'GridID': 7, 'GridSLP' : 8,
           'RegSLP' : 9, 'GridLAP' : 10, 'Flags' : 11, 'Intensity' : 12,
           'Disimularity' : 13, 'UCI' : 14, 'USI' : 15, 'NGrids' : 16,
           'Area' : 17, 'Depth' : 18, 'NearestCenterDist' : 19,
           'NearestCenterAngle' : 20, 'MinOuterEdgeDist' : 21,
           'MaxOuterEdgeDist' : 22, 'AveOuterEdgeDist' : 23,
           'ATTS' : 24}

    # --------------------------------------------------------------------------
    # Setup Section
    # --------------------------------------------------------------------------
    for i in imports:
        exec(i)

    # Fetch definitions and impose those set in defs_set.
    defs = defs.defs(**defs_set)
    Read_MCMS = read_mcms.Read_MCMS

    # Parse definitions.
    readit = Read_MCMS(**what_do)
    # Determine the source of the centers
    source = os.path.basename(readit.in_file).split(".")[0]
    # See if request something other than everything.
    readit.check_time()
    readit.check_place()
    readit.fetch_centers()
    centers = readit.center_holder.keys()
    if verbose: print "\tCenters Read",len(centers)
    centers.sort()
    centers.reverse()

    # Extract all Julian dates
    alldates = []
    alldates = [readit.center_holder[x][4] for x in readit.center_holder]

    # Get unique dates via dictionary
    b = {}
    for i in alldates: b[i] = 0
    alldates = b.keys()
    alldates.sort() # sort as dictionary unsorted
    nsteps = len(alldates)
    if verbose: print "\tNumber of unique dates/times:",nsteps

    # Get all current date-stamps which are the UCI starters.
    dtimes = [netcdftime.DateFromJulianDay(adate*0.01) for adate in alldates]
    date_stamps = ["%4d%02d%02d%02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]

    # Read contour objects
    cfmt = "%scontours_%s_%04d_%04d_%04d_%04d.p"
    # File name to save results to
    contour_file = cfmt % (out_path,readit.model,clevs[0],clevs[1],clevs[2],loop_year)
#tmp
    contour_file = '/Volumes/Scratch/output/nra/contours_nra_0940_1020_0005_1996.p'
    try:
        c_file = open(contour_file, "rb",-1)
    except:
        sys.exit("\n\tWARNING: Error Opening %s." % (contour_file))
    
    # Open data file to save results
    att_file = readit.in_file.replace("tracks","attc")
    att_save = open(att_file,"w")

#tmp
    tsteps = 1

    last_center = ""
    for step in range(0,tsteps):
        date_stamp = date_stamps[step]
#tmp
        #if date_stamp != '1996010300':
        #    continue
        #elif date_stamp == '1996010306':
        #    import sys; sys.exit("Early Out")

        #if date_stamp == '1996010112':
        #    import sys; sys.exit("Stop Here")

        if verbose: print "\t\tDoing ",date_stamp

        # Fetch c_objects
        c_objects = pickle.load(c_file)
        
        # Get current centers.
        current_centers = []
        found_none = 1
        if len(centers) < 1:
            more = 0
        else:
            more = 1
        while more:
            # See if overflow from last read useful or read new record
            if last_center:
                center = last_center
                last_center = ""
            else:
                center = centers.pop()
                if len(centers) < 1: # No more centers
                    more = 0
            # Store if center falls on wanted date.
            if center.startswith(date_stamp,0,10):
                current_centers.append(center)
                found_none = 0
            else:
                # Store for next time
                last_center = center
                more = 0
        if found_none:
            # No centers found
            msg = "\tError: No Centers Found! %s" % date_stamp
            sys.exit(msg)
        if verbose: print "\t\tCurrent Centers: %d" % len(current_centers)
        
        # Assign c_objects to centers
        centers_objects = {}
        for center in current_centers:
            cgrid = readit.center_holder[center][ids['GridID']]
            inside = [x for x in c_objects if cgrid in c_objects[x]]
            centers_objects[center] = inside
        #print centers_objects
 

 '19960101001450000250': ['sh_0980_0000', 'sh_0975_0000', 'sh_0970_0001']
 '19960101000425005250': ['nh_1013_0001', 'nh_1015_0000', 'nh_1014_0000']
        # Envelope Test: Find Centers that share same c_objects.
        shared_objects = {}
        for center in current_centers:
            shared = [x for x in centers_objects[center]

        #print c_objects.keys()

    c_file.close()
    att_save.close()
    print "bottom"

    return

#---Start of main code block.
if __name__=='__main__':

    import pickle,sys,os

    verbose = 1
    plot_contours = 0
    
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

    # Set contour levels used to make c_objects
    #clevs=[940,1020,5]
    clevs=[940,1017,2]

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    imports = ["import sys,os,math, netcdftime, numpy"]
    #imports.append("import matplotlib.pyplot as plt")
    #imports.append("from mpl_toolkits.basemap import Basemap, shiftgrid, addcyclic")
    imports.append("from itertools import chain, permutations")
    #imports.append("import netCDF4 as NetCDF")

    # My modules to import w/ version number appended.
    my_base = ["defs","read_mcms"]
    if verbose:
        my_base.append("print_col")
    if plot_contours:
        my_base.append("plot_map")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)

    # To save a double copy of the data being retained by pull_data it is
    # necessary to reimport and delete pull_data_vX.py inside each loop.
    #import_read = "import %s%s as %s" % ("pull_data",vnum,"pull_data")

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
        slp_path = fnc_out[inputs.index("slp_path")]
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
        out_path+'/stats/tmp/',
        out_path+'/netcdfs/',
        out_path+'/figs/pdfs/',
        out_path+'/figs/comps/')))
        print "\tDirectory %s Created." % (out_path)
    
    if plot_contours:
        plot_contours = out_path+'/figs/'

    defs_set = {}

    start_year = int(super_years[0])
    end_year = int(super_years[1])+1

    tail = "_tracks.txt"
    cut_tail = len(tail)
    header = "mcms_%s_%04d" % (model,start_year)
    in_file = "%s%s%s" % (out_path,header,tail)
    # Set definitions and instantiate read_mcms w/out a template
    what_do = {"model" : model,
                "in_file" : in_file,
                "out_file" : "",
                "just_center_table" : True,
                "detail_tracks" : 0,
                "as_tracks" : "",
                "start_time" : "YYYY MM DD HH SEASON",
                "end_time" : "YYYY MM DD HH SEASON",
                "places" : ["GLOBAL"],
                "include_atts" : 0, 
                "include_stormy" : 0,
                "just_centers" : False,
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
        what_do["land_gridids"] = land_gridids


    # TEST main w/o multiprocessing
    for loop_year in range(start_year,end_year):
        main(defs_set,imports,what_do,loop_year,out_path,shared_path,
                clevs,verbose,plot_contours)
    import sys; sys.exit("all done")


    # --------------------------------------------------------------------------
    # Note on parallel processing
    # --------------------------------------------------------------------------
    
    # If you are running on a machine with multiple CPUs or multicore CPUs then
    # I will take advantage of that and speed things up a lot.

    # The form of parallelism used here is dumb brute force in that
    # I simply launch processes that work independently on part of
    # the problem and put it all back together when I'm done. This
    # is not MPI message passing or OpenMP shared memory.

    # Test requires python 2.6 or higher
    #
    # Test for python version with parallel processing capabilities.
    PROCESSORS =  1
    if sys.version_info >= (2, 6):
        import multiprocessing as mp
        PROCESSORS = mp.cpu_count()
    else:
        print "Parallelism requires python 2.6 or higher."
        print "If this isn't the case just run attribute_vX.py directly."
        sys.exit()

    # Can manually set processors by commenting out below
    PROCESSORS =  14

    # Don't breakup by less than 1 year per processor
    max_processors = (end_year-start_year)
    if PROCESSORS > max_processors:
        PROCESSORS = max_processors

    msg = "\n\tStarting %s%s (process id %s) with %d processors"
    print msg % ('pre_calculate_contours',vnum,os.getpid(),PROCESSORS)

    # -------------------------------------------------------------------------
    # Start Main Loop over super_years
    # -------------------------------------------------------------------------

    # Spawn n=PROCESSORS processes
    pool = mp.Pool(PROCESSORS)

    results = []
    args_used = []
    for loop_year in range(start_year,end_year): 
        # Object holding objects (need array so not copies as messes with processes)
        args_used.append((defs_set,imports,import_read,loop_year,
            out_path,shared_path,slp_path,clevs,plot_contours))
        pool.apply_async(main,args_used[-1],callback=results.append)
    pool.close()
    pool.join()


