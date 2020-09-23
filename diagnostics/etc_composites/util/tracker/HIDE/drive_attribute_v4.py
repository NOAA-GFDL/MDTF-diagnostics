"""
Drives attribute to allow for Pretty Dumb Parallelization (PDP): Break the
job into pieces and spawn as separate processes and concatenate end results.
Not SMP so redundant efforts and no shared data.
#/usr/bin/env python -tt

Usage:

Options:

Examples: python driver_attribute_v4.py

Notes: Requires python 2.6 or higher (but not the 3.0 fork).
"""
__author__  = "Mike Bauer  <mbauer@giss.nasa.gov>"
__status__  = "alpha"
__version__ = "1.0 "+__status__
__date__    = "Created: 28 Jan 2008        Updated: 14 Jun 2008"

# Standard modules
import os, sys, pickle, math

def std (inlist):
    """Sandard deviation of the values."""
    n = len(inlist)
    mean = float(sum(inlist))/float(n)
    devs = [math.pow((x-mean),2) for x in inlist]
    var = sum(devs)/float(n)
    return n,mean,math.sqrt(var)

def cb(r):
    # The use of a callback function allows for true asynchronicity,
    # since my loop does not have to wait for apply_async to return
    pass

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

# --------------------------------------------------------------------------
# Select options for this run.
# --------------------------------------------------------------------------

picks = {0 : "NCEP/NCAR Reanalysis 1",
         1 : "NCEP-DOE Reanalysis 2",
         2 : "NASA GISS GCM ModelE",
         3 : "GFDL GCM",
         4 : "ERA-Interim Reanalysis",
         5 : "ERA-40 Reanalysis"}
pick = 5
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

# Plot map on error (requires matplotlib, also doubles or more memory
# footprint).
plot_on_error = 0

# Use weekly zonal median to filter contours to leave only those that
# rise above defs.z_anomaly_cutoff and are therefore significant dips in the
# slp field.
use_zmean = 0

# Use local SLP gradient or laplacian to filter potential grids.
use_grad = 0

if use_zmean and use_grad:
    sys.exit("Stop: Can't have use_zmean and use_grad")

# Skip saving of data... faster for debuging
skip_save = 0
if skip_save:
    print "\n\n\n\n\n"
    print "WARNING WARNING NO DATA BEING SAVED!!!!!!!!"

# IF non-zero then every plot_every timesteps a plot of the SLP
# field, centers, ATTS and stormy grid will be created. Example,
# plot_every = 30*(24/timestep) creates a plot every 30 days just
# to allow for monitoring on progress. Set plot_every = 1 to create
# movie. Requires matplotlib, also doubles or more memory footprint)
plot_every = 0 #30*(24/6)

# For plot_every provide a "dumped" file so that rejected centers
# including in plot to help diagnose problems/successes,
use_dumped = 1
if not plot_every:
    # No point
     use_dumped = 0

# Reverse: go backwards through the years
go_backwards = 1

# Speedometer: outputs how fast timesteps are being finished... for debugging mostly
speedometer = 0

# This should not be altered for parallel mode!
ReDo_List = []

# --------------------------------------------------------------------------
# Define all modules to be imported.
# --------------------------------------------------------------------------

# Extract version number from this scripts name.
tmp = sys.argv[0]
file_len = len(tmp.split("_"))
vnum = "_"+tmp.split("_")[file_len-1][:2]

# Import the attribute module
tmp = "import %s%s as %s" % ('attribute',vnum,'attribute')
exec(tmp)

# Basic standard Python modules to import.
imports = []
imports.append("import math,pickle,numpy,netcdftime,stats,copy")
imports.append("import netCDF4 as NetCDF")
imports.append("from operator import add")
if speedometer:
    imports.append("import time,datetime")

# My modules to import w/ version number appended.
my_base = ["defs","bridge","try_bridge","find_problematic","scan_contour",
        "check_overlap","find_empty_centers","collapse","clean_bridge",
        "strip_read","att_2_file","fill_holes","envelope_test",
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
over_write_years = [1961,1990]
#over_write_years = [2009,2009]

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
    defs_set = {"keep_log":False,"wavenumber":4.0,"troubled_filter":True}

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
    dirs = map(os.makedirs, (out_path,
    out_path+'/comps/',
    out_path+'/pdfs/',
    out_path+'/stats/',
    out_path+'/stats/tmp/',
    out_path+'/netcdfs/',
    out_path+'/figs/pdfs/',
    out_path+'/figs/comps/'))
    print "\tDirectory %s Created." % (out_path)

# -------------------------------------------------------------------------
# Start Main Loop over super_years
# -------------------------------------------------------------------------
start_year = int(super_years[0])
end_year = int(super_years[1])+1

# Don't breakup by less than 1 year per processor
max_processors = (end_year-start_year)
if PROCESSORS > max_processors:
    PROCESSORS = max_processors

years = [x for x in range(int(super_years[0]),int(super_years[-1])+1)]
if go_backwards:
    years.reverse()

msg = "\n\tStarting %s%s (process id %s) with %d processors"
print msg % ('attribute',vnum,os.getpid(),PROCESSORS)

# Spawn n=PROCESSORS processes
pool = mp.Pool(PROCESSORS)

args_used = []
results = []
for loop_year in range(start_year,end_year):
    # Object holding objects (need array so not copies as messes with processes)
    args_used.append((centers_file, defs_set, imports, pick, out_path, shared_path,
            over_write_slp_path, loop_year, exit_on_error,
            plot_on_error, plot_every, ReDo_List, use_dumped, skip_save,
            use_zmean, use_grad ,speedometer, import_read))
    result = pool.apply_async(attribute.main,args_used[-1],callback=results.append)

# Ensure that all processes which have been fired up finish execution and
# are terminated. This also eliminates any footprints from your parallel
# execution, such as zombie processes left behind.
pool.close()
pool.join()

# Check all finished normally
not_fine = [x for x in results if x != 'Done']
if not_fine:
    print "\tPossible Error",not_fine
else:
    print "\tAll Done"

#
# Create a summery report
#

ithings = [[],[],[],[]]
inames = []

verbose = 0
report_file = "%sstats/mcms_%s_filter_stats_report_%d-%d.txt"
report_file = report_file % (out_path,model,int(super_years[0]),int(super_years[-1]))
print "\tCreating",report_file
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
    r_file = "%sstats/mcms_%s_filter_stats_report_%d.txt" % (out_path,model,loop_year)
    if verbose:
        print "\tAdding",r_file
    try:
        r_read = open(r_file,"r")
    except:
        sys.exit("Error opening: %s" % (r_file))
    for line in r_read:
        r_buffer.append(line)
    r_read.close()
    big_buffer[iyear] = r_buffer
    iyear += 1
iyears = len(years)

for iyear in range(iyears):
    main_line = big_buffer[iyear][1]
    args = main_line.split(" ")
    # Remove any empty strings....
    args = [x for x in args if x]
    if verbose:
        print "\n\tYear", big_buffer[iyear][0],
        print "\tmain_line:",main_line,
        print "\targs:",args

    for i in range(len(ithings)):
        tmp = big_buffer[iyear][i+2]
        tmp = tmp.split("=")
        # Remove any empty strings....
        tmp = [x for x in tmp if x]
        if iyear == 0:
            inames.append(tmp[0].replace('\t', ''))
        ithings[i].append(int(tmp[1].split(" ")[0]))

    # Done Reading... now write
    if iyear == iyears-1:
        verbose = 1
        msg = " ".join(args)
        report_save.writelines(msg)
        if verbose:
            print msg
        length = max(len(w) for w in inames) + 2
        for i in range(len(ithings)):
            i_sum = sum(ithings[i])
            if i == 0:
                big_sum = i_sum
            (n,imean,istd) = std(ithings[i])
            imean = "Mean: %10d"  % (int(round(imean,0)))
            istd = int(round(istd,0))
            per = "%6.2f%%   " % (100.0*(float(i_sum)/float(big_sum)))
            i_sum = "%12d"  % (i_sum)
            istd = "STD: %10d" % (istd)
            imax = "Max: %10d" % max(ithings[i])
            imin = "Min: %10d" % min(ithings[i])
            if i == 0:
                per = "  -       "
            msg = "\t%s%s%s%s%s%s%s%s\n" % (
                        inames[i].ljust(length),"==>".ljust(5),
                        i_sum,per.ljust(6),imin.ljust(20),imean.ljust(20),
                        imax.ljust(20),istd)
            report_save.writelines(msg)
            if verbose:
                print msg
# ------------------------------------------------------------------------------
# Notes: Rather than embed in code make reference here
# ------------------------------------------------------------------------------
Notes = """
"""
