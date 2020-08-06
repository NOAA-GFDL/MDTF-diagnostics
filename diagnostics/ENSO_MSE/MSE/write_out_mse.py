
def write_out_mse(imax, jmax, zmax, mse2, mse2_adv, mse2_div, mdiv2, madv2, tadv2, omse2, prefixout):
    
##  write out full MSE variables 
    nameout = prefixout + "MSE_mse.out"
    fh = open(nameout, "wb")
    dataout2 = mse2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_adv.out"
    fh = open(nameout, "wb")
    dataout2 = mse2_adv.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_div.out"    
    fh = open(nameout, "wb")
    dataout2 = mse2_div.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_mdiv.out"
    fh = open(nameout, "wb")
    dataout2 = mdiv2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_madv.out"
    fh = open(nameout, "wb")
    dataout2 = madv2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_tadv.out"
    fh = open(nameout, "wb")
    dataout2 = tadv2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_omse.out"
    fh = open(nameout, "wb")
    dataout2 = omse2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()    
