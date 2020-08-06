
def write_out_mse_clima(imax, jmax, zmax,mse2, mse2_adv, mse2_div, mdiv2, madv2, tadv2,  omse2, prefixout):
    
##  write out full MSE variables 
    nameout = prefixout + "MSE_mse_clim.out"
    fh = open(nameout, "wb")
    dataout2 = mse2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_adv_clim.out"
    fh = open(nameout, "wb")
    dataout2 = mse2_adv.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_div_clim.out"    
    fh = open(nameout, "wb")
    dataout2 = mse2_div.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_mdiv_clim.out"
    fh = open(nameout, "wb")
    dataout2 = mdiv2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_madv_clim.out"
    fh = open(nameout, "wb")
    dataout2 = madv2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_tadv_clim.out"
    fh = open(nameout, "wb")
    dataout2 = tadv2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_omse_clim.out"
    fh = open(nameout, "wb")
    dataout2 = omse2.swapaxes(0, 1)
    dataout2.tofile(fh)
    fh.close()    

