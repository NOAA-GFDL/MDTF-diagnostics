import numpy as np
import os.path
import sys

def get_dimensions(imax, jmax,  zmax, prefix):
##  read in  all the domain dimensions and the actual values lon/lat/plevs


###    dimensions first needed for the rest 
    dir_path = os.path.join(prefix,"xyz_dimensions.txt")
    if (os.path.exists(dir_path)):
        file = open(dir_path, 'r')
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
        print (" missing file ", dir_path)
        print (" needed for the code "  )
        print (" exiting get_dimensions.py ")
        sys.exit()

    return imax, jmax,  zmax
 
