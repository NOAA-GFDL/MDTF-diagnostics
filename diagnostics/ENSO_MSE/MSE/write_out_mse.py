import numpy as np

def write_out_mse(imax, jmax, zmax, mse2,  mdiv2, madv2, tadv2,  omse2, prefixout):
 
   
##  write out full MSE variables 
    nameout = prefixout + "MSE_mse.out"
    fh = open(nameout, "wb")
    dataout =  np.array( mse2)
    dataout2 = dataout.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_mdiv.out"
    fh = open(nameout, "wb")
    dataout =  np.array( mdiv2)
    dataout2 = dataout.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_madv.out"
    fh = open(nameout, "wb")
    dataout =  np.array( madv2)
    dataout2 = dataout.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_tadv.out"
    fh = open(nameout, "wb")
    dataout =  np.array( tadv2)
    dataout2 = dataout.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_omse.out"
    fh = open(nameout, "wb")
    dataout =  np.array( omse2)
    dataout2 = dataout.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()    

