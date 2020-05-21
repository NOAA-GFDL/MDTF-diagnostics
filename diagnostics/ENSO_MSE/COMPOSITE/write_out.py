import numpy as np
import os.path

def write_out( variable, dataout,  prefix):
##   construct the output name 
    nameout =  prefix+variable+".grd"
    print('write_out opening '+nameout)
    os.system("rm " + nameout + " 2> /dev/null")
    fh = open(nameout, "wb")
    
    dataout.tofile(fh)
    fh.close()
