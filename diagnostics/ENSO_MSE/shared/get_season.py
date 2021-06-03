import os.path
import sys

def get_season( season, prefix):
##  read in all  parameter data 

    if (os.path.exists(prefix+"../shared/parameters.txt")):
        file = open(prefix+'../shared/parameters.txt', 'r')
        for i in range(1, 11):
            line = file.readline()
            line = line.strip()
            column = line.split()
            season =  column[2]

        file.close()

    else:
        print (" missing file: "  + prefix + "../shared/season.txt")
        print (" exiting get_season.py ")
        sys.exit()
    return season
 
