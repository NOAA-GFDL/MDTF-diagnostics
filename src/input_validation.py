
import os
import util

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


def check_for_varlist_files(varlist,verbose=0):
   func_name = "\t \t check_for_varlist_files :"
   if ( verbose > 2 ): print func_name+" check_for_varlist_files called with ",varlist
   found_list = []
   missing_list = []
   for item in varlist:
      if (verbose > 2 ): print func_name +" "+item
      filepath = util.makefilepath(item['name_in_model'],item['freq'],os.environ['CASENAME'],os.environ['DATADIR'])

      if (os.path.isfile(filepath)):
         print "found ",filepath
         found_list.append(filepath)
         continue
      if (not item['required']):
         print "WARNING: optional file not found ",filepath
         continue
      if not (('alternates' in item) and (len(item['alternates'])>0)):
         print "ERROR: missing required file ",filepath,". No alternatives found"
         missing_list.append(filepath)
      else:
         alt_list = item['alternates']
         print "WARNING: required file not found ",filepath,"\n \t Looking for alternatives: ",alt_list
         for alt_item in alt_list: # maybe some way to do this w/o loop since check_ takes a list
            if (verbose > 1): print "\t \t examining alternative ",alt_item
            new_var = item.copy()  # modifyable dict with all settings from original
            new_var['name_in_model'] = util.translate_varname(alt_item,verbose=verbose)  # alternative variable name 
            del new_var['alternates']    # remove alternatives (could use this to implement multiple options)
            if ( verbose > 2): print "created new_var for input to check_for_varlist_files",new_var
            new_files = check_for_varlist_files([new_var],verbose=verbose)
            found_list.extend(new_files['found_files'])
            missing_list.extend(new_files['missing_files'])

   if (verbose > 2): print "check_for_varlist_files returning ",missing_list
   # remove empty list entries
   files = {}
   files['found_files'] = [x for x in found_list if x]
   files['missing_files'] = [x for x in missing_list if x]
   return files

def check_pod_driver(settings, verbose=0):
   from distutils.spawn import find_executable #determine if a program is on $PATH

   func_name = "check_pod_driver "
   if (verbose > 1):  print func_name," received POD settings: ", settings

   pod_name = settings['pod_name']
   pod_dir  = settings['pod_dir']
   programs = util.get_available_programs()

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
