#!/home/Oar.Gfdl.Mdteam/anaconda2/envs/ILAMB-2.2/bin/python
#PBS -N ILAMB
#PBS -l walltime=04:00:00
#PBS -l nodes=1
#PBS -j oe
#PBS -o 
#PBS -r y
#PBS -q bigmem
#PBS -v PYTHONHOME="/home/Oar.Gfdl.Mdteam/anaconda2/envs/ILAMB-2.2"

# Driver script for running the Internation Land Model
# Benchmarking Project (ILAMB) analysis tool

import argparse
import glob
import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import warnings
import timeit
#import netCDF4
import numpy as np
import commands

frepp_stub = str("""
set CASENAME        CM4_historical 
set model           GFDL 
set in_data_dir     /archive/oar.gfdl.cmip6/CM4/warsaw_201710_om4_v1.0.1/ 
set DIAG_HOME       /archive/wnd/MDTF-GFDL/MDTF_v2.0/ 
set yr1             1990
set yr2             1994
set CLEAN           0
set make_variab_tar 1
set test_mode       False
set verbose         0
set varsmon        
set varsday         
set varshr3         
set varshr1
""")

def process_frepp_stub(x):
    # Converts the frepp arguments to a Python dictionary
    D = {}
    x = (x.replace('set ','').replace('=','').splitlines())
    for l in x:
        if l != '':
            l = l.split()
            if len(l) == 2:
                D[l[0]] = l[1]
            else:
                D[l[0]] = None
    return D

def parse_arguments(frepp_stub):
    freppargs = process_frepp_stub(frepp_stub)

    parser = argparse.ArgumentParser()
    parser.add_argument('-C','--CLEAN',  type=int, default=0,\
                        help="do not delete old files")
    parser.add_argument('-T','--make_variab_tar',  type=int, default=1,\
                        help="create tar file of the results, tar file in wkdir")
    parser.add_argument('-H','--DIAG_HOME', type=str,\
                        default='/archive/wnd/MDTF-GFDL/MDTF_v2.0/',
                        help='path to directory that contains MDTF packages')
    parser.add_argument('-i','--in_data_dir', type=str,\
                        default='/archive/oar.gfdl.cmip6/CM4/warsaw_201710_om4_v1.0.1/',
                        help='path to pp directory that contains inputdata')
    parser.add_argument('-M','--model',  type=str,\
                        help="string containing model name")
    parser.add_argument('-N','--CASENAME',  type=str,\
                        help="string containing experiment name")
    parser.add_argument('-yr1','--yr1',  type=int,\
                        help="beginning year of analysis")
    parser.add_argument('-yr2','--yr2',  type=int,\
                        help="ending year of analysis")
    parser.add_argument('-V1','--varsmon', type=str,\
                        default='zg',\
                        help='csv list of monthly model variables to consider')
    parser.add_argument('-V2','--varsday', type=str,\
                        default='zg,hus,rlut,wap,pr,ta,ua,va,prw',\
                        help='csv list of daily model variables to consider')
    parser.add_argument('-V3','--varshr3', type=str,\
                        default='pr',\
                        help='csv list of 3-hour model variables to consider')
    parser.add_argument('-V4','--varshr1', type=str,\
                        default='pr,hus,ta',\
                        help='csv list of 1-hour model variables to consider')


    parser.add_argument('-m','--method', type=str, default="gcp",\
                        help="method to use for copying datasets (options are "+\
                        "link and gcp)")
    parser.add_argument('-l','--ignore_sysmodules', default=False, action='store_true',
                        help='do not attempt to load any system module files when running')
    parser.add_argument('-e','--executable', type=str,\
                        default='/archive/wnd/MDTF-GFDL/MDTF_v2.0/MDTF.sh',
                        help='path to mdtf executable')
    args = parser.parse_args()

    def _check_arguments(args,freppargs,x):
        if args.__dict__[x] is None:
            if freppargs[x] is not None:
                args.__dict__[x] = freppargs[x]
        return args

    def _print_args(x):
        print('='*80)
        for k in sorted(x.__dict__.keys()):
            print('     '+k+': '+str(x.__dict__[k]))
        print('='*80)

    for arg in ['CASENAME','model','yr1','yr2']:
        args = _check_arguments(args,freppargs,arg)
        if args.__dict__[arg] is None:
            parser.print_help()
            raise ValueError('You must provide an argument for '+arg)

    args.yr1 = int(args.yr1)
    args.yr2 = int(args.yr2)

    _print_args(args)

    return args


#----- Define helper functions
def fix_dir_str(x):
   # Ensures strings intended to be paths end with a slash
   if x[-1] != '/': x = x+'/'
   return x

def run_command1(command,env=None):
    # Runs a system call and prints stdout in real-time
    # Optional ability to pass a differnt environment to the subprocess
    process = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, env=env)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()
    rc = process.poll()
    return rc

def run_command(command,env=None):
    # Runs a system call and prints stdout in real-time
    # Optional ability to pass a differnt environment to the subprocess
    process = subprocess.Popen(command, stdout=subprocess.PIPE, env=env)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()
    rc = process.poll()
    return rc

def copy_directory(srcdir,dstdir,method='gcp'):
    # Either copies or links a source directory to a destination diretory
    srcdir = fix_dir_str(srcdir)
    dstdir = fix_dir_str(dstdir)
    if method == 'gcp':
        rc = run_command(['gcp','-r','-v',srcdir,dstdir])
        if rc != 0:
            raise OSError('Unable to copy directory')
    elif method == 'link':
        os.symlink(srcdir,dstdir+srcdir.split('/')[-2])
    else:
        raise ValueError('Unknown method for copying datasets')

def copy_files(srcfile,dstdir,method='gcp',remove_prefix=None,time_label=None,yr1=None,yr2=None):
    # Either copies or links a source files to a destination diretory
    srcfile = glob.glob(srcfile)
    dstdir = fix_dir_str(dstdir)

    def _gcp(f,dstdir,remove_prefix):
        rc = run_command(['gcp','-v',f,dstdir])
        if remove_prefix is not None:
            fdst = f.replace(remove_prefix,time_label)
            os.rename(dstdir+os.path.basename(f),dstdir+os.path.basename(fdst))
    def _link(f,dstdir,remove_prefix):
        fdst = f
        if remove_prefix is not None: fdst = f.replace(remove_prefix,time_label)
        os.symlink(f,dstdir+os.path.basename(fdst))

    for f in srcfile:
        if (yr1 is not None) and (yr2 is not None):
            fyears = os.path.basename(f).split('.')[1]
            fyears = fyears.split('-')
            fyears = (int(fyears[0][0:4]),int(fyears[1][0:4]))
            if not (yr1 <= fyears[0] <= yr2) and not (yr1 <= fyears[1] <= yr2):
                continue
        if method == 'gcp':
            _gcp(f,dstdir,remove_prefix)
        elif method == 'link':
            _link(f,dstdir,remove_prefix)
        else:
            raise ValueError('Unknown method for copying datasets')
def cat_file(srcfile,dstfile):
    cmd = 'ncrcat ' +srcfile+' '+dstfile
    rc = run_command(shlex.split(cmd))

def main(args,run=True,cleanup=True):
    # Prepare the input datasets for GFDL model (!!!Note: We keep consistent with the CESM structure in this test version!!!)
    # Create a temporary directory to hold the model datasets (Currently, we need several further pre-processing procedures, e.g. combining the datasets, extracting certain level, etc.)
    tmpdir = fix_dir_str(tempfile.mkdtemp())
    os.chdir(tmpdir)

    # Copy files from pp directory to temporary directory: !!!Note: We need to copy different variables on different time scales

    # Copy monthly dataset
    mondir = fix_dir_str(os.path.abspath(os.path.join(fix_dir_str(args.DIAG_HOME),"..")))+'inputdata/model/'+fix_dir_str(args.CASENAME)+'mon/'
    if os.path.exists(mondir) is False: os.makedirs(mondir)
    path_mon = fix_dir_str(args.in_data_dir)+args.CASENAME+'/gfdl.ncrc4-intel16-prod-openmp/pp/atmos_cmip/ts/monthly/5yr/'
    for v in args.varsmon.split(','):
        copy_files(fix_dir_str(path_mon)+'*.'+v+'.nc',tmpdir,method=args.method,\
                 remove_prefix='atmos_cmip',time_label="mon",yr1=args.yr1,yr2=args.yr2)
        src = commands.getoutput('ls ' +fix_dir_str(os.getcwd())+'mon*.'+v+'.nc')
        dst = args.CASENAME+'.'+v+'.mon.nc'

        if os.path.isfile(mondir+dst): os.remove(mondir+dst)
        cat_file(src,mondir+dst)

    # Copy daily dataset (try to find different variables in different folders)
    daydir = fix_dir_str(os.path.abspath(os.path.join(fix_dir_str(args.DIAG_HOME),"..")))+'inputdata/model/'+fix_dir_str(args.CASENAME)+'day/'
    if os.path.exists(daydir) is False: os.makedirs(daydir)
    path_day = path_mon.replace('monthly','daily')
    for v in args.varsday.split(','): 
        atmos_daily_2D_dir = path_day.replace('atmos_cmip','atmos_cmip_2deg_daily_2D')
        atmos_daily_3D_dir = path_day.replace('atmos_cmip','atmos_cmip_2deg_daily_3D')
        copy_files(fix_dir_str(path_day)+'*.'+v+'.nc',tmpdir,method=args.method,\
                 remove_prefix='atmos_cmip',time_label="day",yr1=args.yr1,yr2=args.yr2)
        try:
            copy_files(fix_dir_str(atmos_daily_2D_dir)+'*.'+v+'.nc',tmpdir,method=args.method,\
                                     remove_prefix='atmos_cmip_2deg_daily_2D',time_label="day",yr1=args.yr1,yr2=args.yr2)
        except:
            print('')
        try:
            copy_files(fix_dir_str(atmos_daily_3D_dir)+'*.'+v+'.nc',tmpdir,method=args.method,\
                                     remove_prefix='atmos_cmip_2deg_daily_3D',time_label="day",yr1=args.yr1,yr2=args.yr2)
        except:
            print('Unable to copy atmos_cmip files. Some analyses may be missing')
        src = commands.getoutput('ls ' +fix_dir_str(os.getcwd())+'day*.'+v+'.nc')
        dst = args.CASENAME+'.'+v+'.day.nc'
        if os.path.isfile(daydir+dst): os.remove(daydir+dst)
        cat_file(src,daydir+dst)

    # Copy 3-hour dataset
    hr3dir = fix_dir_str(os.path.abspath(os.path.join(fix_dir_str(args.DIAG_HOME),"..")))+'inputdata/model/'+fix_dir_str(args.CASENAME)+'3hr/'
    if os.path.exists(hr3dir) is False: os.makedirs(hr3dir)
    path_hr3 = path_mon.replace('monthly','3hr')
    print(path_hr3)
    for v in args.varshr3.split(','):
        copy_files(fix_dir_str(path_hr3)+'*.'+v+'.nc',tmpdir,method=args.method,\
                 remove_prefix='atmos_cmip',time_label="hr3",yr1=args.yr1,yr2=args.yr2)
        src = commands.getoutput('ls ' +fix_dir_str(os.getcwd())+'hr3*.'+v+'.nc')
        dst = args.CASENAME+'.'+v+'.3hr.nc'

        if os.path.isfile(hr3dir+dst): os.remove(hr3dir+dst)
        cat_file(src,hr3dir+dst)

    # Copy 1-hour dataset (Currently, we just setup the directory to save output from some scripts)
    hr1dir = fix_dir_str(os.path.abspath(os.path.join(fix_dir_str(args.DIAG_HOME),"..")))+'inputdata/model/'+fix_dir_str(args.CASENAME)+'1hr/'
    if os.path.exists(hr1dir) is False: os.makedirs(hr1dir)

    shutil.rmtree(tmpdir) # remove the tempory dir after we cat&put them into the right structure

    os.chdir(args.DIAG_HOME)
    runcmd = args.executable
    if run is True:
        rc = run_command1(shlex.split(runcmd))
        
if __name__ == '__main__':
    # Parse command line arguments
    args = parse_arguments(frepp_stub)
    sys.stdout.flush()
    os.environ['CLEAN'] = "0"
    os.environ['make_variab_tar'] = "1"
    os.environ['DIAG_HOME'] = args.DIAG_HOME 

    # Bootstrap ability to use system modules
    if args.ignore_sysmodules is False:
        if 'MODULESHOME' in os.environ.keys():
            execfile(os.environ['MODULESHOME']+'/init/python.py')
            module(['load','gcp'])
            module(['load','nco'])
        else:
            raise OSError('Unable to determine how modules are handled on this host.')
    else:
        warnings.warn('Ignoring system modules',RuntimeWarning)
    # Run the main function
    main(args,run=True,cleanup=True) #,run=False,cleanup=False) # for testing
    exit(0)
