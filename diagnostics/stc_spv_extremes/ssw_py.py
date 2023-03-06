def getConsecutiveValues(arr): 
    
    """
    This calculates and groups consecutive values of an array of numbers, 
    which must be in an ascending order.
    """
    final = []
    end = 0
    start = 0
    if len(arr) == 1:
        final.append(arr)
    else:    
        for i in range(1,len(arr)) :
            if arr[i] - arr[i-1] == 1 :
                end = i
            else :
                if len(arr[start:end+1])==0:
                    final.append(arr[start:start+1])
                else:
                    final.append(arr[start:end+1])
                start = i
            if i == len(arr) - 1 :
                if len(arr[start:end+1])==0:
                    final.append(arr[start:start+1])
                else:
                    final.append(arr[start:end+1])
    return final

def ssw_cp07(variable,threshold=0, consec_days=20, hem="NH"):
    
    """
    This calculates central dates of sudden stratospheric warmings following the definition in
    Charlton and Polvani (2007).
    Read in reanalysis data of zonal-mean zonal wind U at 10 hPa and 60degLat

    Parameters:
    ----------------------------------------------------
    variable : `xarray.DataArray` 
              The input DataArray or Dataset of zonal-mean zonal wind U at 10 hPa 
              and 60 degLat as a function of time. 
              Note: time variable must be named "time"
              Note: if hem = 'SH', then zonal winds should be for 60 degS latitude
            
    threshold : Numeric quantity
              An optional variable to determine the value below which a SSW occurs; 
              default is 0 m/s
               
    consec_days : Numeric quantity
               The number of consecutive days required that the zonal winds remain
               above `threshold` for a SSW to be independent of the event before it;
               default is 20 days, as defined in Charlton and Polvani (2007).
        
    hem: String quantity
        An optional variable that applies code to either NH or SH; default is NH
    """

    import numpy as np 
    import xarray as xr
    import matplotlib.pyplot as plt
    import datetime
    
    year = variable.time.dt.year.values   
    yr = np.arange(year[0],year[-1]+1,1)
    yr = yr.tolist()
    
    ssw_dates = []
    
    for y in yr:
        
        # look for mid-winter SSWs between Nov-Mar in the NH
        if hem == "NH":
            s_str = str(y)+"-11-01"
            e_str = str(y+1)+"-03-31"
            print("Calculating NH SSWs for "+s_str+" to "+e_str)
            var = variable.sel(time=slice(s_str,e_str))
            var_chk = variable.sel(time=slice(s_str,str(y+1)+"-04-30")) #this variable enables check for final warming
        if hem == "SH":
            s_str = str(y)+"-06-01"
            e_str = str(y)+"-10-31"
            print("Calculating SH SSWs for "+s_str+" to "+e_str)
            var = variable.sel(time=slice(s_str,e_str))
            var_chk = variable.sel(time=slice(s_str,str(y)+"-11-30")) #this variable enables check for final warming
        
        var = var.assign_coords(dayofwinter=("time", np.arange(len(var.time.values))))
        var_chk = var_chk.assign_coords(dayofwinter=("time", np.arange(len(var_chk.time.values))))
        
        #Find instances where U1060 is less than threshold
        vor_neg = var.where(var < threshold,drop=True)
        
        #determine consecutive groups of easterlies
        dayswitheasterlies = getConsecutiveValues(vor_neg.dayofwinter.values)
        
        # if there's only one group, check for final warming and if no final warming, append central date to ssw_dates #
        if len(dayswitheasterlies) == 1:
            firstvalue = dayswitheasterlies[0][0]
            lastvalue = dayswitheasterlies[0][-1]

            # search over all winds between end of candidate central event and april 30th for 10 consecutive days of 
            # westerlies. if 10 consecutive days of westerlies are found, append the central date to ssws #
            windsafterwinter = var_chk[lastvalue:]
            westerlies = windsafterwinter.where(windsafterwinter > threshold,drop=True)

            if len(westerlies) > 0:
                westerlygroups = getConsecutiveValues(westerlies.dayofwinter.values)
                westerlygroupslength = [len(group) for group in westerlygroups]
                maxlength = np.nanmax(westerlygroupslength)
                if maxlength > 9:
                    ssw_dates.append([var.dayofwinter[firstvalue].time.dt.day.values, var.dayofwinter[firstvalue].time.dt.month.values,
                                 var.dayofwinter[firstvalue].time.dt.year.values])
        
        # if there are multiple 'groups,' first append the first central date using the exact same code as above #  
        # then, search for additional central dates that are not final warmings #
        if len(dayswitheasterlies) > 1:
        
            firstvalue = dayswitheasterlies[0][0]
            lastvalue = dayswitheasterlies[0][-1]
            windsafterwinter = var_chk[lastvalue:]

            westerlies = windsafterwinter.where(windsafterwinter > threshold, drop=True)
            if len(westerlies) > 0:
                westerlygroups = getConsecutiveValues(westerlies.dayofwinter.values)
                westerlygroupslength = [len(group) for group in westerlygroups]
                maxlength = np.nanmax(westerlygroupslength)
                if maxlength > 9:
                    ssw_dates.append([var.dayofwinter[firstvalue].time.dt.day.values, var.dayofwinter[firstvalue].time.dt.month.values,
                                 var.dayofwinter[firstvalue].time.dt.year.values])
        
        # search for multiple SSWs by looping over 'groups' #
        
        for i,v in enumerate(dayswitheasterlies):

            # "break" statement used b/c the loop always considers a group[i] and the next group[i+1], #
            # so the loop must be exited on the the 2nd to last index #

            if i+1 == len(dayswitheasterlies):
                break

            # Get the first/last index from the current group
            currentgroup = dayswitheasterlies[int(i)]
            first_currentgroup = currentgroup[0]
            last_currentgroup = currentgroup[-1]

            # Get the first index from the next (current+1) group
            nextgroup = dayswitheasterlies[int(i+1)]
            first_nextgroup = nextgroup[0]
            
            # If the groups are separated by "consec_days" of westerlies, check for final warming #
            if first_nextgroup - last_currentgroup > consec_days:
                # search over all winds between candidate central date and april 30th for 10 consecutive days of westerlies #
                # if 10 consecutive days of westerlies are found, append the central date to ssw_dates #
                windsafterwinter = var_chk[first_nextgroup:]
                westerlies = windsafterwinter.where(windsafterwinter > threshold, drop=True)
                if len(westerlies) > 0:
                    westerlygroups = getConsecutiveValues(westerlies.dayofwinter.values)
                    westerlygroupslength = [len(group) for group in westerlygroups]
                    maxlength = np.nanmax(westerlygroupslength)
                    if maxlength > 9:
                        ssw_dates.append([var.dayofwinter[first_nextgroup].time.dt.day.values, 
                                 var.dayofwinter[first_nextgroup].time.dt.month.values,
                                 var.dayofwinter[first_nextgroup].time.dt.year.values])
 
    return ssw_dates