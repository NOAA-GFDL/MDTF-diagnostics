# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)


import re 
import os
import sys
import yaml
sys.path.insert(0,'var_code/util/')
from util import setenv

def get_available_programs(verbose=0):
   return {'py': sys.executable, 'ncl': 'ncl'}  

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

def parse_pod_varlist(varlist, verbose=0):
   func_name = " parse_pod_varlist: "
   default_file_required = False 
   for idx, var in enumerate(varlist):
      varlist[idx]['name_in_model'] = translate_varname(var['var_name'], verbose=verbose)

      assert(var['freq'] in ["1hr","3hr","6hr","day","mon"]), \
         "WARNING: didn't find "+var['freq']+" in frequency options "+\
            " (set in "+__file__+":"+func_name+")"
      if 'requirement' in var.keys():
         varlist[idx]['required'] = (var['requirement'].lower() == 'required')
      else:
         varlist[idx]['required'] = default_file_required
      if not 'alternates' in var.keys():
         varlist[idx]['alternates'] = ''

def makefilepath(varname,timefreq,casename,datadir):
    """ 
    USAGE (varname, timefreq, casename, datadir )
       str varname  (as set by var_code/util/set_variables_*.py)
       str timefreq "mon","day","6hr","3hr","1hr"
       str datadir directory where model data lives

    """
    return datadir+"/"+timefreq+"/"+casename+"."+varname+"."+timefreq+".nc"


def check_for_varlist_files(varlist,verbose=0):
   func_name = "\t \t check_for_varlist_files :"
   if ( verbose > 2 ): print func_name+" check_for_varlist_files called with ",varlist
#   all_required_files_found = True
   missing_list = []
   for item in varlist:
      if (verbose > 2 ): print func_name +" "+item
      filepath = makefilepath(item['name_in_model'],item['freq'],os.environ['CASENAME'],os.environ['DATADIR'])

      if ( os.path.isfile(filepath) ):
         print "found ",filepath
      else:
         if ( not item['required'] ):
            print "WARNING: optional file not found ",filepath
         else: 
            if ( not 'alternates' in item ):
               print "ERROR: required file not found ",filepath
               missing_list.append(filepath)
            else:
               alt_list = item['alternates']
               if ( not alt_list  ):
                  print "ERROR: missing required file ",filepath,". No alternatives found"
                  missing_list.append(filepath)
               else:
                  print "WARNING: required file not found ",filepath,"\n \t Looking for alternatives: ",alt_list
                  for alt_item in alt_list: # maybe some way to do this w/o loop since check_ takes a list
                     if (verbose > 1): print "\t \t examining alternative ",alt_item
                     new_var = item.copy()  # modifyable dict with all settings from original
                     new_var['name_in_model'] = translate_varname(alt_item,verbose=verbose)  # alternative variable name 
                     del new_var['alternates']    # remove alternatives (could use this to implement multiple options)
                     if ( verbose > 2): print "created new_var for input to check_for_varlist_files",new_var
                     missing_list.append(check_for_varlist_files([new_var],verbose=verbose))

   if (verbose > 2): print "check_for_varlist_files returning ",missing_list

   #   return all_required_files_found
   missing_list_wo_empties = [x for x in missing_list if x]
   return missing_list_wo_empties


def check_pod_driver(settings, verbose=0):
   from distutils.spawn import find_executable #determine if a program is on $PATH

   func_name = "check_pod_driver "
   if (verbose > 1):  print func_name," received POD settings: ", settings

   pod_name = settings['pod_name']
   pod_dir  = settings['pod_dir']
   programs = get_available_programs()

   if (not 'driver' in settings):  
      print "WARNING: no valid driver entry found for ", pod_name
      #try to find one anyway
      try_filenames = [pod_name+".","driver."]      
      file_combos = [ file_root + ext for file_root in try_filenames for ext in programs.keys()]
      if verbose > 1: print "Checking for possible driver names in ",pod_dir," ",file_combos
      for try_file in file_combos:
         try_path = os.path.join(pod_dir,try_file)
         if verbose > 1: print " looking for driver file "+try_path
         if os.path.exists(try_path):
            settings['driver'] = try_path
            if (verbose > 0): print "Found driver script for "+pod_name+" : "+settings['driver']
            break    #go with the first one found
         else:
            if (verbose > 1 ): print "\t "+try_path+" not found..."
   errstr_nodriver = "No driver script found for package "+pod_name +"\n\t"\
      +"Looked in "+pod_dir+" for pod_name.* or driver.* \n\t"\
      +"To specify otherwise, add a line to "+pod_name+"/settings file containing:  driver driver_script_name \n\t" \
      +"\n\t"+func_name
   assert ('driver' in settings), errstr_nodriver

   if not os.path.isabs(settings['driver']): # expand relative path
      settings['driver'] = os.path.join(settings['pod_dir'], settings['driver'])

   errstr = "ERROR: "+func_name+" can't find "+ settings['driver']+" to run "+pod_name
   assert(os.path.exists(settings['driver'])), errstr 

   if (not 'program' in settings):
      # Find ending of filename to determine the program that should be used
      driver_ext  = settings['driver'].split(".")[-1]
      # Possible error: Driver file type unrecognized
      errstr_badext = func_name+" does not know how to call a ."+driver_ext+" file \n\t"\
         +"Available programs: "+str(programs.keys())
      assert (driver_ext in programs), errstr_badext
      settings['program'] = programs[driver_ext]
      if ( verbose > 1): print func_name +": Found program "+programs[driver_ext]
   errstr = "ERROR: "+func_name+" can't find "+ settings['program']+" to run "+pod_name
   assert(find_executable(settings['program']) is not None), errstr     


def read_mdtf_config_file(argv, verbose=0):
   if (verbose > 2): print "read_mdtf_config_file received arguments "+str(argv)
   
   namelist_file_default = os.environ["DIAG_HOME"]+"/config.yml"  
   if (len(argv) > 1 ):
      namelist_file = argv[1]
      if ( verbose > 0 ): print "Received command-line argument for input namelist file: ", namelist_file
   else:  #try the default
      namelist_file = namelist_file_default
      if ( verbose > 0 ): print """WARNING : Expected command-line argument with input namelist file name.
         \n\t Checking for default input namelist file """, namelist_file
   assert(os.path.exists(namelist_file)), "Input file does not exist "+str(namelist_file)

   file_object = open(namelist_file, 'r')
   file_contents = yaml.safe_load(file_object)
   file_object.close()

   file_contents['envvars'] = {}
   for key, val in file_contents['case_list'][0].items():
      setenv(key, val, file_contents['envvars'], verbose=verbose)
   for key, val in file_contents['settings'].items():
      setenv(key, val, file_contents['envvars'], verbose=verbose)

   if (verbose > 1):
      print yaml.dump(file_contents)  #print it to stdout 
   return file_contents


def read_pod_settings_file(pod_name, verbose=0):
   pod_dir = os.environ['VARCODE']+'/'+pod_name
   filename = pod_dir+'/settings.yml'
   assert(os.path.exists(filename)), "Input file does not exist "+str(filename)

   fileobject = open(filename,'r')
   file_contents = yaml.safe_load(fileobject)
   fileobject.close()

   file_contents['settings']['pod_name'] = pod_name
   file_contents['settings']['pod_dir'] = pod_dir
   check_pod_driver(file_contents['settings'], verbose)
   if (verbose > 0): 
      print file_contents['settings']['pod_name']+" settings: "
      print yaml.dump(file_contents['settings'])

   parse_pod_varlist(file_contents['varlist'], verbose)
   if (verbose > 0): 
      print file_contents['settings']['pod_name']+" varlist: "
      print yaml.dump(file_contents['varlist'])
   return file_contents


# ------------ MAIN for testing ----------------------------------------------
# USAGE  python read_files.py filename [namelist,settings,varlist]

if ( __name__ != '__main__'): 
   pass
else:
   from sys import argv

   verbose = 1
   if (verbose > 0):
       print 'Testing functionality of read_files'

   if (len(argv) < 2 ):
       print "ERROR, read_files.py in testing mode requires filename argument"
   exit()

   read_mdtf_config_file(argv[1],verbose=verbose)
