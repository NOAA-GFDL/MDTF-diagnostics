# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os
import sys
import glob
import shutil
import yaml
from util import setenv, translate_varname
from input_validation import check_required_dirs




























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
