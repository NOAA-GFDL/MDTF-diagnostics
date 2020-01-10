import numpy as np
import os.path

def write_out_3D(imax, jmax, zmax,  variable, dataout,  prefix):
##   construct the output name 
    nameout =  prefix+variable+".grd"
    print('write_out_3D opening '+nameout)
    fh = open(nameout, "wb")
    
    dataout2 = dataout.swapaxes(0, 2)
    
    dataout2.tofile(fh)
    fh.close()    
