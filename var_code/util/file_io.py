# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os
import sys
import glob
import shutil
import yaml
from util import setenv, translate_varname
from input_validation import check_required_dirs

def parse_pod_varlist(varlist, verbose=0):
   func_name = " parse_pod_varlist: "
   default_file_required = False 
   for idx, var in enumerate(varlist):
      varlist[idx]['name_in_model'] = translate_varname(var['var_name'], verbose=verbose)

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
      if (key in args.__dict__) and (args.__getattribute__(key) != None):
         val = args.__getattribute__(key)
      val = os.path.realpath(val)
      setenv(key, val, config['envvars'], verbose=verbose)

   # following are redundant but used by PODs

   setenv("RGB",os.environ["DIAG_HOME"]+"/var_code/util/rgb",config['envvars'],overwrite=False,verbose=verbose)

   vars_to_set = config['settings'].copy()
   vars_to_set.update(config['case_list'][0])
   for key, val in vars_to_set.items():
      if (key in args.__dict__) and (args.__getattribute__(key) != None):
         val = args.__getattribute__(key)
      setenv(key, val, config['envvars'], verbose=verbose)


def read_pod_settings_file(pod_name, verbose=0):
   pod_dir = os.environ["DIAG_HOME"]+"/var_code/"+pod_name
   filename = pod_dir+'/settings.yml'
   assert(os.path.exists(filename)), "Input file does not exist "+str(filename)

   fileobject = open(filename,'r')
   file_contents = yaml.safe_load(fileobject)
   fileobject.close()

   file_contents['settings']['pod_name'] = pod_name
   file_contents['settings']['pod_dir'] = pod_dir
   if 'conda_env' not in file_contents['settings']:
      file_contents['settings']['conda_env'] = '_MDTF-diagnostics'
   elif not file_contents['settings']['conda_env'].startswith('_MDTF-diagnostics'):
      file_contents['settings']['conda_env'] = \
         '_MDTF-diagnostics' + '-' + file_contents['settings']['conda_env']
   
   if (verbose > 0): 
      print file_contents['settings']['pod_name']+" settings: "
      print yaml.dump(file_contents['settings'])

   parse_pod_varlist(file_contents['varlist'], verbose)
   if (verbose > 0): 
      print file_contents['settings']['pod_name']+" varlist: "
      print yaml.dump(file_contents['varlist'])

   return file_contents


def set_pod_env_vars(pod_settings, config, verbose=0):
   pod_name = pod_settings['pod_name']
   pod_envvars = {}
   # location of POD's code
   setenv("POD_HOME", os.environ["DIAG_HOME"]+"/var_code/"+pod_name,
      pod_envvars,overwrite=False,verbose=verbose)
   # POD's observational data
   setenv("OBS_DATA",os.environ["OBS_ROOT_DIR"]+"/"+pod_name,
      pod_envvars,overwrite=False,verbose=verbose)
   # POD's subdir within working directory
   setenv("WK_DIR", os.environ['variab_dir']+"/"+pod_name,
      pod_envvars,overwrite=False,verbose=verbose)

   check_required_dirs(
      already_exist =["POD_HOME", 'OBS_DATA'], create_if_nec = ["WK_DIR"], 
      verbose=verbose)

   # optional POD-specific env vars defined in settings.yml
   if 'pod_env_vars' in pod_settings:
      for key, val in pod_settings['pod_env_vars'].items():
         setenv(key, val, pod_envvars,overwrite=False,verbose=verbose)
   
   return pod_envvars


def read_model_varnames(verbose=0):
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


def setup_pod_directories(pod_name):
   pod_wk_dir = os.path.join(os.environ['variab_dir'], pod_name)
   dirs = ['', 'model', 'model/PS', 'model/netCDF', 'obs', 'obs/PS','obs/netCDF']
   for d in dirs:
      if not os.path.exists(os.path.join(pod_wk_dir, d)):
         os.makedirs(os.path.join(pod_wk_dir, d))

def convert_pod_figures(pod_name):
   # Convert PS to png
   pod_wk_dir = os.path.join(os.environ['variab_dir'], pod_name)
   dirs = ['figures', 'model/PS', 'obs/PS']
   for d in dirs:
      full_path = os.path.join(pod_wk_dir, d)
      files = glob.glob(full_path+"/*.ps")
      files.extend(glob.glob(full_path+"/*.eps"))
      for f in files:
         (dd, ff) = os.path.split(os.path.splitext(f)[0])
         ff = os.path.join(os.path.dirname(dd), ff) # parent directory/filename
         command_str = 'convert '+ os.environ['convert_flags'] + ' ' \
            + f + ' ' + ff + '.' + os.environ['convert_output_fmt']
         os.system(command_str)   


def make_pod_html(pod_name, pod_description):
   # do templating on POD's html file
   pod_code_dir = os.path.join(os.environ['DIAG_HOME'], 'var_code', pod_name)
   pod_wk_dir = os.path.join(os.environ['variab_dir'], pod_name)
   html_file = pod_wk_dir+'/'+pod_name+'.html'
   temp_file = pod_wk_dir+'/tmp.html'

   if os.path.exists(html_file):
      os.remove(html_file)
   shutil.copy2(pod_code_dir+'/'+pod_name+'.html', pod_wk_dir)
   os.system("cat "+ html_file \
      + " | sed -e s/casename/" + os.environ["CASENAME"] + "/g > " \
      + temp_file)
   # following two substitutions are specific to convective_transition_diag
   # need to find a more elegant way to handle this
   if pod_name == 'convective_transition_diag':
      temp_file2 = pod_wk_dir+'/tmp2.html'
      if ("BULK_TROPOSPHERIC_TEMPERATURE_MEASURE" in os.environ) \
         and os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"] == "2":
         os.system("cat " + temp_file \
            + " | sed -e s/_tave\./_qsat_int\./g > " + temp_file2)
         shutil.move(temp_file2, temp_file)
      if ("RES" in os.environ) and os.environ["RES"] != "1.00":
         os.system("cat " + temp_file \
            + " | sed -e s/_res\=1\.00_/_res\=" + os.environ["RES"] + "_/g > " \
            + temp_file2)
         shutil.move(temp_file2, temp_file)
   shutil.copy2(temp_file, html_file) 
   os.remove(temp_file)

   # add link and description to main html page
   html_file = os.environ["variab_dir"]+"/index.html"
   a = os.system("cat " + html_file + " | grep " + pod_name)
   if a != 0:
      os.system("echo '<H3><font color=navy>" + pod_description \
         + " <A HREF=\""+ pod_name+"/"+pod_name+".html\">plots</A></H3>' >> " \
         + html_file)



def cleanup_pod_files(pod_name):
   pod_code_dir = os.path.join(os.environ['DIAG_HOME'], 'var_code', pod_name)
   pod_data_dir = os.path.join(os.environ['OBS_ROOT_DIR'], pod_name)
   pod_wk_dir = os.path.join(os.environ['variab_dir'], pod_name)

   # copy PDF documentation (if any) to output
   files = glob.glob(pod_code_dir+"/*.pdf")
   for file in files:
      shutil.copy2(file, pod_wk_dir)

   # copy premade figures (if any) to output 
   files = glob.glob(pod_data_dir+"/*.gif")
   files.extend(glob.glob(pod_data_dir+"/*.png"))
   files.extend(glob.glob(pod_data_dir+"/*.jpg"))
   files.extend(glob.glob(pod_data_dir+"/*.jpeg"))
   for file in files:
      shutil.copy2(file, pod_wk_dir+"/obs")

   # remove .eps files if requested
   if os.environ["save_ps"] == "0":
      dirs = ['model/PS', 'obs/PS']
      for d in dirs:
         if os.path.exists(os.path.join(pod_wk_dir, d)):
            shutil.rmtree(os.path.join(pod_wk_dir, d))

   # delete netCDF files if requested
   if os.environ["save_nc"] == "0":    
      dirs = ['model/netCDF', 'obs/netCDF']
      for d in dirs:
         if os.path.exists(os.path.join(pod_wk_dir, d)):
            shutil.rmtree(os.path.join(pod_wk_dir, d))

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
