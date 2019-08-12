# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os
import sys
import yaml

def read_yaml(file_path, verbose=0):
    # wrapper to load config files
    assert(os.path.exists(file_path))
    with open(file_path, 'r') as file_obj:
        file_contents = yaml.safe_load(file_obj)

    if (verbose > 2):
        print yaml.dump(file_contents)  #print it to stdout 
    return file_contents

def write_yaml(struct, file_path, verbose=0):
    # wrapper to write config files
    with open(file_path, 'w') as file_obj:
        yaml.dump(struct, file_obj)

def get_available_programs(verbose=0):
    return {'py': 'python', 'ncl': 'ncl', 'R': 'Rscript'}
    #return {'py': sys.executable, 'ncl': 'ncl'}  

def makefilepath(varname,timefreq,casename,datadir):
    """ 
    USAGE (varname, timefreq, casename, datadir )
        str varname  (as set by src/config_*.yml.py)
        str timefreq "mon","day","6hr","3hr","1hr"
        str datadir directory where model data lives

    """
    return datadir+"/"+timefreq+"/"+casename+"."+varname+"."+timefreq+".nc"

def setenv(varname,varvalue,env_dict,verbose=0,overwrite=True):
    # env_dict: a dictionary to be dumped once file is created
    # This is a wrapper to os.environ so any new env vars 
    # automatically get written to the file
   
    if (not overwrite) and (varname in env_dict): 
        if (verbose > 0): print "Not overwriting ENV ",varname," = ",env_dict[varname]
    else:
        if ('varname' in env_dict) and (env_dict[varname] != varvalue) and (verbose > 0): 
            print "WARNING: setenv ",varname," = ",varvalue," overriding previous setting ",env_dict[varname]
        env_dict[varname] = varvalue

        # environment variables must be strings
        if type(varvalue) is bool:
            if varvalue == True:
                varvalue = '1'
            else:
                varvalue = '0'
        elif type(varvalue) is not str:
            varvalue = str(varvalue)
        os.environ[varname] = varvalue

        if (verbose > 0): print "ENV ",varname," = ",env_dict[varname]
    if ( verbose > 2) : print "Check ",varname," ",env_dict[varname]


def translate_varname(varname_in,verbose=0):
    func_name = " translate_varname "
    if ( verbose > 2): print func_name+" read in varname: ",varname_in
    if ( varname_in in os.environ ):
        varname = os.environ[varname_in]  #gets variable name as imported by set_variables_$modeltype.py
        if ( verbose > 1): print func_name+" found varname: ",varname
    else: 
        varname = varname_in
        if ( verbose > 1): print func_name+"WARNING: didn't find ",varname, " in environment vars, not substituting"
        #      print "To do: Modify read_files.main to accept argument of model type and import"
    if ( verbose > 2): print func_name + "returning ",varname
    return varname


def check_required_envvar(verbose=0,*varlist):
    varlist = varlist[0]   #unpack tuple
    for n in range(len(varlist)):
        if ( verbose > 2): print "checking envvar ",n,varlist[n],str(varlist[n])
        try:
            test = os.environ[varlist[n]]
        except:
            print "ERROR: Required environment variable ",varlist[n]," not found "
            print "       Please set in input file (default namelist) as VAR ",varlist[n]," value "
            exit()


def check_required_dirs(already_exist =[], create_if_nec = [], verbose=3):
    # arguments can be envvar name or just the paths
    filestr = __file__+":check_required_dirs: "
    errstr = "ERROR "+filestr
    if verbose > 1: filestr +" starting"
    for dir_in in already_exist + create_if_nec : 
        if verbose > 1: "\t looking at "+dir_in
 
        if dir_in in os.environ:  
            dir = os.environ[dir_in]
        else:
            if verbose>2: print(" envvar "+dir_in+" not defined")    
            dir = dir_in

        if not os.path.exists(dir):
            if not dir_in in create_if_nec:
                if (verbose>0): 
                    print errstr+dir_in+" = "+dir+" directory does not exist"
                    #print "         and not create_if_nec list: "+create_if_nec
                exit()
            else:
                print(dir_in+" = "+dir+" created")
                os.makedirs(dir)
        else:
            print("Found "+dir)

