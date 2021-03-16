import numpy as np

def write_out(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var ,  tadv_var, prefix, nameout,  undef):

    nameout2 = prefix + nameout
    fh = open(nameout2, "wb")

    vmax = 8
    output = np.zeros((vmax),dtype='float32', order = 'F')
 
## modified output to match  the bar charts 
    output[0] = mse_var  
    output[1] = omse_var   
    output[2] = madv_var 
    output[3] = tadv_var
    output[4] = sw_var  
    output[5] = lw_var   
    output[6] = shf_var    
    output[7] = lhf_var      
###    output.tofile(fh)
    output.tofile(fh)    
    fh.close()
