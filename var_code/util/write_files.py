# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os



def write_namelist_case(file,case):
#format    CASE QBOi.EXP1.AMIP.001 CESM 1977 1981   
#   from read_files import Namelist  #is this necessary?
   file.write("CASE "+case['CASENAME'] +\
              " "    +case['model'] +\
              " "    +str(case['FIRSTYR']) +\
              " "    +str(case['LASTYR'])  +\
              "\n")


def write_namelist (dir,namelist,verbose=0):
   "write_namelist creates a file with MDTF run settings: dir/namelist_YYYYMMDDHHMM"
   from read_files import pprint_dict
   outfile = create_namelist_outfile(dir,verbose)
   write_namelist_case(outfile,namelist['case_list'][0])
   write_list(outfile,namelist['pod_list'],tag="POD")

   #drb: need to combine these dictionaries, make uniq, and sort output alpha
   if (verbose >2 ):pprint_dict(namelist['envvars'],title= "Env vars from namelist")
   if (verbose >2): pprint_dict(namelist['settings'],title= "OLD envvars")
   #envvars.update(namelist.envvar)   #adds namelist envvars to others, over-riding any repeats with namelist
   #if ( verbose >1 ): pprint_dict(envvars,title= "Env vars written to output namelist in "+dir)
   write_dict(outfile,namelist['envvars'],tag="VAR")

#   write_envvar_all(outfile)



def create_namelist_outfile(dir,verbose=0):
   import time
   import shutil
   func_name = "create_namelist_outfile"
   #   time_str = time.strftime("%04Y%02m%02d%02H%02M", time.localtime())   #namelist_YYYYMMDDHH
   str = "save"
   outfile = dir+"/namelist_"+str

   print("Using archived namelist file "+outfile+"\n \t as argument to mdtf.py should exactly reproduce this analysis.")
   if ( verbose > 1 ): print "\t filename set in "+__file__+":"+func_name

   # DRB Ideally, create a directory Old_namelist and move all but the latest there at this point
   if os.path.isfile(outfile):
      outfileold = outfile+"_old"
      if ( verbose > 1 ): print "WARNING: moving existing namelist file to ",outfileold
      shutil.move(outfile,outfileold)

   file = open(outfile,'w')  #create it
   return file

def write_dict(file,dict_in,tag=""):
   for key, value in dict_in.iteritems():
      file.write(tag+" "+key+" "+str(value)+"\n")

def write_list(file,list_in,tag=""):
   for item in list_in:
      file.write(tag+" "+str(item)+"\n")



   


def write_envvar (filename, varname, verbose=0):
   "This writes a line into filename in the format: setenv varname value"

   var_value = os.environ[varname]
   if (verbose > 2 ): print "write_envvar ",varname," ",var_value
   file = open(filename,'a',0,)
   file.write("VAR "+varname+" "+os.environ[varname]+"\n")
   return;

def write_envvar_all (outfile):

   # DRB should really print the dictionary of namelist.envvar
   # Even better to check if file contains these already
   write_envvar(outfile,"CASENAME")   #take out this and other case items
   write_envvar(outfile,"NCARG_ROOT")
   write_envvar(outfile,"DIAG_HOME")
   write_envvar(outfile,"WKDIR")
   write_envvar(outfile,"variab_dir")
   write_envvar(outfile,"DATADIR")
   write_envvar(outfile,"OUTDIR")
   write_envvar(outfile,"save_ps")
   write_envvar(outfile,"save_nc")
   write_envvar(outfile,"make_variab_tar")
   write_envvar(outfile,"model")   #case specifiec, remove
   write_envvar(outfile,"VARCODE")  
   write_envvar(outfile,"VARDATA")
   write_envvar(outfile,"RGB")
   write_envvar(outfile,"NCL")
   print("Saved envvars in ",outfile)
