# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os
import sys
import yaml
import util
from util import setenv

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


def read_mdtf_config_file(namelist_file, verbose=0):
   assert(os.path.exists(namelist_file)), "Input file does not exist "+str(namelist_file)

   file_object = open(namelist_file, 'r')
   file_contents = yaml.safe_load(file_object)
   file_object.close()

   if (verbose > 1):
      print yaml.dump(file_contents)  #print it to stdout 
   return file_contents

def set_mdtf_env_vars(args, config, verbose=0):
   config['envvars'] = {}
   # need to expand ./ and ../ in paths
   for key, val in config['paths'].items():
      if (key in args) and (args.__getattribute__(key) != None):
         val = args.__getattribute__(key)
      val = os.path.realpath(val)
      setenv(key, val, config['envvars'], verbose=verbose)

   # following are redundant but used by PODs
   setenv("WKDIR",os.environ['WORKING_DIR'],config['envvars'],verbose=verbose)
   setenv("VARDATA",os.environ["OBS_ROOT_DIR"],config['envvars'],overwrite=False,verbose=verbose)
   setenv("VARCODE",os.environ["DIAG_HOME"]+"/var_code",config['envvars'],overwrite=False,verbose=verbose)
   setenv("RGB",os.environ["VARCODE"]+"/util/rgb",config['envvars'],overwrite=False,verbose=verbose)

   vars_to_set = config['settings'].copy()
   vars_to_set.update(config['case_list'][0])
   for key, val in vars_to_set.items():
      if (key in args) and (args.__getattribute__(key) != None):
         val = args.__getattribute__(key)
      setenv(key, val, config['envvars'], verbose=verbose)


def read_pod_settings_file(pod_name, verbose=0):
   pod_dir = os.environ['VARCODE']+'/'+pod_name
   filename = pod_dir+'/settings.yml'
   assert(os.path.exists(filename)), "Input file does not exist "+str(filename)

   fileobject = open(filename,'r')
   file_contents = yaml.safe_load(fileobject)
   fileobject.close()

   file_contents['settings']['pod_name'] = pod_name
   file_contents['settings']['pod_dir'] = pod_dir
   
   if (verbose > 0): 
      print file_contents['settings']['pod_name']+" settings: "
      print yaml.dump(file_contents['settings'])

   parse_pod_varlist(file_contents['varlist'], verbose)
   if (verbose > 0): 
      print file_contents['settings']['pod_name']+" varlist: "
      print yaml.dump(file_contents['varlist'])

   return file_contents



def read_model_varnames(verbose=0):
   import glob

   model_dict = {}
   config_files = glob.glob(os.environ["DIAG_HOME"]+"/var_code/util/config_*.yml")
   for filename in config_files:
      fileobject = open(filename,'r')
      file_contents = yaml.safe_load(fileobject)
      fileobject.close()

      if type(file_contents['model_name']) is str:
         file_contents['model_name'] = [file_contents['model_name']]
      for model in file_contents['model_name']:
         if verbose > 0: print "found model "+ model
         model_dict[model] = file_contents['var_names']
   return model_dict

def set_model_env_vars(model_name, model_dict):
   # todo: set/unset for multiple models
   # verify all vars requested by PODs have been set
   if model_name in model_dict:
      for key, val in model_dict[model_name].items():
         os.environ[key] = str(val)
   else:
      print "ERROR: model ", model_name," Not Found"
      print "      This is set in namelist "
      print "      CASE case-name *model* start-year end-year"
      quit()



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
