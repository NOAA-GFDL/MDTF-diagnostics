# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os
import sys
import yaml
import util
from util import setenv
from util_validation import check_pod_driver, check_for_varlist_files

def parse_pod_varlist(varlist, verbose=0):
   func_name = " parse_pod_varlist: "
   default_file_required = False 
   for idx, var in enumerate(varlist):
      varlist[idx]['name_in_model'] = util.translate_varname(var['var_name'], verbose=verbose)

      assert(var['freq'] in ["1hr","3hr","6hr","day","mon"]), \
         "WARNING: didn't find "+var['freq']+" in frequency options "+\
            " (set in "+__file__+":"+func_name+")"
      if 'requirement' in var:
         varlist[idx]['required'] = (var['requirement'].lower() == 'required')
      else:
         varlist[idx]['required'] = default_file_required
      if ('alternates' in var) and (type(var['alternates']) is not list):
         varlist[idx]['alternates'] = [var['alternates']]


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

   var_files = check_for_varlist_files(file_contents['varlist'], verbose)
   file_contents.update(var_files)

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
