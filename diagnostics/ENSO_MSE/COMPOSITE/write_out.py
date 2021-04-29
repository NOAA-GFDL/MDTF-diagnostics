import numpy as np
import os.path

def write_out( variable, dataout,  prefix):
##   construct the output name 
    nameout =  os.path.join(prefix, variable + ".grd")
    os.system("rm " + nameout + " 2> /dev/null")
    fh = open(nameout, "wb")
 
    ndims =  dataout.ndim
    if( ndims == 2 ):
      dataout2 = dataout.swapaxes(0, 1)   
      dataout2.tofile(fh)
      fh.close()

    if( ndims == 3 ):
      dataout2 = dataout.swapaxes(0, 2)
      dataout2.tofile(fh)
      fh.close()

    if( ndims == 4 ):
      dataout2 = dataout.swapaxes(0, 3)
      dataout3 = dataout2.swapaxes(1, 2)
      dataout3.tofile(fh)
      fh.close()
