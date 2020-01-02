import numpy as np
import os.path

def write_out_4D(imax, jmax, zmax,  tmax,  variable, dataout,  prefix):
##   construct the output name
    nameout =  prefix+variable+".grd"
    print('write_out_4D opening ',nameout)
    fh = open(nameout, "wb")
    
    dataout2 = dataout.swapaxes(0, 3)
    dataout3 = dataout2.swapaxes(1, 2)
    
    dataout3.tofile(fh)
    fh.close()    
