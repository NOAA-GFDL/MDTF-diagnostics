"""
Drives center_finder to allow for Pretty Dumb Parallelization (PDP): Break the
job into pieces and spawn as separate processes and concatenate end results.
Not SMP so redundant efforts and no shared data.
#!/usr/bin/env python -tt

Usage:

Options:

Examples: python driver_center_finder_v4.py

Notes: Requires python 2.6 or higher (but not the 3.0 fork).
"""
__author__  = "Mike Bauer  <mbauer@giss.nasa.gov>"
__version__ = "3.0 "
__date__    = "Created: Jan 2008        Updated: Jan 2009"

# Standard modules
import os, sys, pickle

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
pick = 1
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
# footprint)
plot_on_error = 0

# Save/plot Stats (debugging mostly,requires matplotlib, also
# doubles or more memory footprint)
save_plot = 0

# Save debugging data for post analysis.
# Note to make unified plot of save_plot data see big_one.py
save_stats = 1

# Extract version number from this scripts name.
tmp = sys.argv[0]
file_len = len(tmp.split("_"))
vnum = "_"+tmp.split("_")[file_len-1][:2]

# --------------------------------------------------------------------------
# Define all modules to be imported.
# --------------------------------------------------------------------------

# Import the center_finder module
tmp = "import %s%s as %s" % ('center_finder',vnum,'center_finder')
exec(tmp)

# Basic standard Python modules to import.
imports = []
system_imports = "import math,pickle,numpy,netcdftime"
imports.append(system_imports)
imports.append("import netCDF4 as NetCDF")

# My modules to import w/ version number appended.
my_base = ["defs","tree_traversal","gcd","g2l","ij2grid",
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
#over_write_years = [1979,2008]
#over_write_years = [2009,2009]
#over_write_years = [1995,1997]

# Need to read s.dat to get super_years.
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
if over_write_out_path:
    out_path = over_write_out_path
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

# Here you can alter the default behavior as determined
# by defs_vX.py and possibly setup_vX.py.
defs_set = {}
if pick <= 1:
    defs_set = {"keep_log":False,"troubled_filter":True,
            "tropical_filter":True}
    #defs_set = {"keep_log":False,"troubled_filter":False,
    #        "tropical_filter":False}
elif pick == 2:
    defs_set = {"keep_log":False,"troubled_filter":True,
        "tropical_filter":True,"read_scale":1.0}
elif pick == 3:
    defs_set = {"keep_log":False,"troubled_filter":True,
            "tropical_filter":True,"topo_filter":False}
elif pick == 4:
    defs_set = {"keep_log":False,"troubled_filter":True,
            "tropical_filter":True,"topo_filter":False}
elif pick == 5:
    defs_set = {"keep_log":False,"polar_filter":False,
            "troubled_filter":True}
    ## match RAIBLE et. all 2007
    #defs_set = {"keep_log":False,"troubled_filter":True,
    #        "tropical_filter":True,'max_cyclone_speed': 42.0,
    #        'age_limit':72.0,"topo_filter":True}

# Define some files
centers_file = "centers.txt"
dumped_centers_file = "dumped_centers.txt"

start_year = int(super_years[0])
end_year = int(super_years[1])+1

# Don't breakup by less than 1 year per processor
max_processors = (end_year-start_year)
if PROCESSORS > max_processors:
    PROCESSORS = max_processors

msg = "\n\tStarting %s%s (process id %s) with %d processors"
print msg % ('center_finder',vnum,os.getpid(),PROCESSORS)

# Spawn n=PROCESSORS processes
pool = mp.Pool(PROCESSORS)

results = []
args_used = []
for loop_year in range(start_year,end_year):
    #print "\n=============%d=============" % (loop_year)    
    # Object holding objects (need array so not copies as messes with processes)
    args_used.append((centers_file, defs_set, dumped_centers_file, imports,
                      pick, over_write_out_path, shared_path, over_write_slp_path,
                      loop_year, exit_on_error, plot_on_error, save_plot,
                      import_read,save_stats))
    pool.apply_async(center_finder.main,args_used[-1],callback=results.append)
pool.close()
pool.join()

# Check all finished normally
years = range(int(start_year),int(end_year))
if len(results) != len(years):
    print "\tPossible Error A",len(results),len(years)
not_fine = [x for x in results if x.find("Finished") == -1]
if not_fine:
    print "\tPossible Error B",not_fine
else:
    print "\tAll Done"

total_cnt = 0
candidates = 0
lap_cnt = 0
reg_cnt = 0
rad_cnt = 0
trb_cnt = 0
pol_cnt = 0
verbose = 1

report_file = "%sstats/mcms_%s_center_final_report_%d-%d.txt"
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
    r_file = "%sstats/mcms_%s_%d_centers_report.txt" % (out_path,model,loop_year)
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
iyears = iyear
for iyear in range(iyears):
    main_line = big_buffer[iyear][1]
    args = main_line.split(" ")
    # Remove any empty strings....
    args = [x for x in args if x]
    if verbose:
        print "\n\tYear", big_buffer[iyear][0],
        print "\tmain_line:",main_line,
        print "\targs:",args

    # if percentage == '(100.00%)' 8 args if '( 99.99%)' 9
    if len(args) == 8:
        total_cnt += int(args[3])
        candidates += int(args[6])
    else:
        total_cnt += int(args[3])
        candidates += int(args[7])
    if verbose:
        print "\tTweaked:",args
        print "\ttotal_cnt:",total_cnt
        print "\tcandidates:",candidates

    if candidates > 0:
        fraction = 100.0*(float(total_cnt)/float(candidates))
    else:
        fraction = 0.0
    f = "%6.2f%%)" % (fraction)
    if verbose:
        print "\tfraction:",fraction

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
        print "\tlap",lap,
        print "\treg",reg,
        print "\trad",rad,
        print "\ttrb",trb,
        print "\tpol",pol

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
            print msg

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
            print smsg

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
            print smsg

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
            print smsg

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
            print smsg

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
            print smsg
