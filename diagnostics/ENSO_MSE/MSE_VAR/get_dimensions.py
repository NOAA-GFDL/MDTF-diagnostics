import numpy as np
import os.path
import sys

def get_dimensions(imax, jmax,  zmax, prefix):
##  read in  all the domain dimensions and the actual values lon/lat/plevs


###    dimensions first needed for the rest 

    if (os.path.exists(prefix+"xyz_dimensions.txt")):
        file = open(prefix+'xyz_dimensions.txt', 'r')
        line = file.readline()
        line = line.strip()
        column = line.split()
        imax = int( column[0])
        line = file.readline()
        line = line.strip()
        column = line.split()
        jmax = int( column[0])
        line = file.readline()
        line = line.strip()
        column = line.split()
        zmax = int( column[0])
        file.close()
    else:
        print " missing file "+  prefix+"plevs.txt"
        print " needed for the code "  
        print " exiting get_plevels_in.py "
        sys.exit()

    return imax, jmax,  zmax
 
