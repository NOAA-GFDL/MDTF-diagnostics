
def write_out_mse_clima(imax, jmax, zmax,mse2, mse2_adv, mse2_div, mdiv2, madv2, tadv2,  omse2, prefixout):
    
##  write out full MSE variables 
    nameout = prefixout + "MSE_mse_clim.out"
    fh = open(nameout, "wb")
    mse2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_adv_clim.out"
    fh = open(nameout, "wb")
    mse2_adv.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_div_clim.out"    
    fh = open(nameout, "wb")
    mse2_div.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_mdiv_clim.out"
    fh = open(nameout, "wb")
    mdiv2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_madv_clim.out"
    fh = open(nameout, "wb")
    madv2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_tadv_clim.out"
    fh = open(nameout, "wb")
    tadv2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_omse_clim.out"
    fh = open(nameout, "wb")
    omse2.tofile(fh)
    fh.close()    

