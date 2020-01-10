import numpy as np
import os.path

def write_out_2D(imax, jmax,  variable, dataout,  prefix):
##   construct the output name 
    nameout =  prefix+variable+".grd"
    print('write_out_2D opening '+nameout)
    fh = open(nameout, "wb")
    
    dataout2 = dataout.T
 
    dataout2.tofile(fh)
    fh.close()
