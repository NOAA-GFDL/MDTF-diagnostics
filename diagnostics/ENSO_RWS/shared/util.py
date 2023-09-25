

def setenv (varname,varvalue,env_dict,verbose=0):
    import os
    # Not currently used. Needs to be a dictionary to be dumped once file is created
    #
    # Ideally this could be a wrapper to os.environ so any new env vars 
    # automatically get written to the file
    "replaces os.environ to set the variable AND save it to write out in namelist"

    if (verbose > 2 ): print ("Saving ",varname," = ",varvalue)
    os.environ[varname] = varvalue
    env_dict[varname]   = varvalue
    if ( verbose > 2) : print ("Check ",varname," ",env_dict[varname])



def check_required_dirs(verbose=3, already_exist =[], create_if_nec = []):
    # arguments can be envvar name or just the paths

#   print("var_code/ENSO_MSE/COMPOSITE/util.py check_required_dirs")
    import os
    filestr = __file__+":check_required_dirs: "
    errstr = "ERROR "+filestr
    if verbose > 1: print (filestr +" starting")
    for dir_in in already_exist + create_if_nec : 
        if verbose > 1: print ("\t looking for required dir: "+dir_in )

        if dir_in in os.environ:  
            dir = os.environ[dir_in]
            if verbose>2: print(" \t found "+dir_in+" = "+dir)
        else:
            if verbose>2: print(" envvar "+dir_in+" not defined. Setting to self.")    
            dir = dir_in

        if not os.path.exists(dir):
            if not dir_in in create_if_nec:
                if (verbose>0): 
                    print(errstr+dir_in+" = "+dir+" directory does not exist")
                    print("         and not create_if_nec list: ",create_if_nec)
                exit()
            else:
                print(dir_in+" = "+dir+" created")
                os.makedirs(dir)
        else:
            print("Found "+dir)
