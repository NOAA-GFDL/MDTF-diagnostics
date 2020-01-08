import numpy as np
import os.path
import sys

def get_season( season, prefix):
##  read in all  parameter data 

    if (os.path.exists(prefix+"parameters.txt")):
        file = open(prefix+'parameters.txt', 'r')
        line = file.readline()

        line = file.readline()
        
        line = file.readline()

        line = file.readline()

        line = file.readline()

        line = file.readline()

        line = file.readline()

        line = file.readline()

        line = file.readline()

        line = file.readline()

        line = file.readline()
    
        line = file.readline()

        line = file.readline()
        line = line.strip()
        column = line.split()
        season =  column[2]

        file.close()

    else:
        ffile = prefix + "season.txt"
        print " missing file: "  + prefix + "season.txt"
        print " exiting get_season.py "
        sys.exit()
    return season
 
