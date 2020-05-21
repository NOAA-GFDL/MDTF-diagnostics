
def write_out_mse(imax, jmax, zmax, mse2, mse2_adv, mse2_div, mdiv2, madv2, tadv2, omse2, prefixout):
    
##  write out full MSE variables 
    nameout = prefixout + "MSE_mse.out"
    fh = open(nameout, "wb")
    mse2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_adv.out"
    fh = open(nameout, "wb")
    mse2_adv.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_div.out"    
    fh = open(nameout, "wb")
    mse2_div.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_mdiv.out"
    fh = open(nameout, "wb")
    mdiv2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_madv.out"
    fh = open(nameout, "wb")
    madv2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_tadv.out"
    fh = open(nameout, "wb")
    tadv2.tofile(fh)
    fh.close()

    nameout = prefixout + "MSE_omse.out"
    fh = open(nameout, "wb")
    omse2.tofile(fh)
    fh.close()    
