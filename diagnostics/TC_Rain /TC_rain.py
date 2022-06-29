# This file is part of the TC Rain Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
# Azimuthal Average of TC Rain Rate POD
# 
#   Last update: 5/27/2022
# 

# 
#   Version & Contact info
# 
#   Here you should describe who contributed to the diagnostic, and who should be
#   contacted for further information:
# 
#   - Version/revision information: version 1 (5/06/2020)
#   - PI Daehyun Kim, University of Washington, daehyun@uw.edu
#   - Developer/point of contact Nelly Emlaw, University of Washington, gnemlaw@uw.edu
# 
#   Open source copyright agreement
# 
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
# 
# #   Functionality

# This POD calculates and plots azimuthal averages for tropical cyclone (TC) rain rates 
# from TC track data and model output precipitation. 

# This POD does not pull track data from model output precip. The TC track data required 
# snapshots of latitude and longitude coordinates of the center of a storm, and the date
# and time of those snapshots. An option addition are storm traits of each snapshot such 
# as maximum wind, central pressure, etc through which snapshots can be filtered for 
# inclusion of the azimuthal rain rate average. For the azimuthal average calculation, 
# the track data is organized into the form of a dictionary:

# track_dict[date in datetime64 format][key for storm identifier, and required data 
# (coordinate/wind/etc)]

# In this example code, the model output is interpolated and regridded to 0.25 x 0.25 
# degree arrays and the average is calcuated from 0 to 600 km from the center of the 
# storm in 25 km discrete sections. Here we only take the avearge of snaphots where the
# max wind speed is between 50 and 60 kt. The output of this diagnostic is a plot in the
# form of an .eps file with distance from the center of the storm along the horizonal 
# average and precip rate along the vertical axis.   

# 
#   
# 
#   Required programming language and libraries
# 
#   Python version 3, xarray, numpy, scipy and matplotlib.
# 
#   Required model output variables
#   
#   Total Precipitation 
#   Model Track Output (required: storm center latitude and longitude, time of snapshot, 
#   optional: max wind, central surface pressure, sst, etc)
# 
#   References
#   I will ask my advisor what an appropriate reference would be to put here. 
# 
#


import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
from scipy.interpolate import interp2d #used to interpolate the output model data
import numpy as np



### 1) Loading model data files: ###############################################
#
# Apologies I am very new to collaborating with my code. I have a friend who is 
# going to help me with how to us os to import data efficently, but currently 
# I am simly using the paths on my serve. I thought it might be a better use of 
# our time to simply send the draft pull request to get your comments on the code 
# as it is, while I figure out os. 


#load precip netcdf data
pr_path = '/home/disk/p/gnemlaw/nasa_grant/sample_files/example1/pr_2002-07-12.nc'
pr = xr.open_dataset(pr_path)

#for the sake of time in this draft I am only including the western pacific. 
regions = {'WNP':[[0,31.5],[100.5,181.5]]}

#get only feild of view for basin storm is in
basin = 'WNP'
latrange = np.arange(regions[basin][0][0],regions[basin][0][1],1.5)
lonrange = np.arange(regions[basin][1][0],regions[basin][1][1],1.5)
pr_wnp = pr.sel(longitude = lonrange,latitude = latrange )

#Organizing Track Data
# This code does not have a TC tracking mechanism of its own an needs to be fed TC 
# track data which includes: 
# Required: snapshops of storm center coordinates (latitude, longitude), 
# time of snapshot
# Optional: some means of filtering which snapshots to average over (max wind, 
# central surface pressure, etc)
# 
# The data is organized within the code as a dictionary of the form:
# track_dict[basin][stormID (here latlon)][keys for required and optional data]
# the example data was tracked with the ECMWF tracker and includes a small sample
# of western north pacific storm tracks from hindecast data of 2002. 

wnptracks = open('/home/disk/p/gnemlaw/nasa_grant/sample_files/example1/wnp')

track_dict = {}

for line in wnptracks:
    if 'SNBR' in line: #formatting of data.
        n_snap = float(line[19:21]) #number of storm days
        start_line_num = line[0:6]
        track_dict[start_line_num] = {}
        x = 0
    if 'SNBR' not in line and len(line)>10:
        if x < n_snap:
            date = line[6:16]
            datesplit = date.split('/')
            d = datesplit[2]
            m = datesplit[1]
            y = datesplit[0]
            dt64 = y+'-'+m+'-'+d+'T'+'12' #I'm setting the track date64s at 12z 
            #rather than 00z where the model output says the track points are 
            #are so that when we take the rain rate (accum_rain_day - accum_rain_yesterday)/24
            #the lat lon center of the storm is between the todays feild and yesterdays feild. 
            lat = float(line[20:23])/10
            lon = float(line[23:27])/10
            maxwind = float(line[29:31])
            track_dict[start_line_num][dt64] = {"ID": start_line_num,
                               "date":date,
                               "date64":dt64,
                               "lat":lat,
                               "lon":lon,
                               "maxwind":maxwind,
                               "index":x
                               }
            x = x+1

### 2) Doing azimuthal average computations: #####################################################


#dist function calculates the distancing between two points on a sphere
def dist(p1,p2,radius):
    
    import numpy as np
    
    phi1 = p1[0]
    phi2 = p2[0]
    lam1 = p1[1]
    lam2 = p2[1]
    
    sins = (np.sin((phi2-phi1)/2))**2
    coscossin = np.cos(phi1)*np.cos(phi2)*(np.sin((lam2-lam1)/2)**2)
    
    d = 2*np.arcsin((sins+coscossin)**.5)
    dis = d*radius
    return dis

#list of all snapshot averages
allazaverages = []
#list of snapshot averages with max wind speeds 30-40 knots
azaverage_30_40_kt = []
 

for storm in track_dict:
    for snapshot in track_dict[storm]:
        index = track_dict[storm][snapshot]["index"]
        if index == 0: #getting initial snapshot for calculating rain rate for storm
            initial_Z = pr_wnp.sel(time = snapshot)
            initial_Z = initial_Z.tp
        if index > 0:
            #storm center
            latitude = track_dict[storm][snapshot]["lat"]
            longitude = track_dict[storm][snapshot]["lon"]
            #calculating rain rate
            Z = pr_wnp.sel(time = snapshot)
            Z = Z['tp']
            Z_anom = Z-initial_Z
            Z_anom = Z_anom/24
            #interpdataset
            latrange = np.arange(0,31.5,1.5)
            lonrange = np.arange(100.5,181.5,1.5)
            x = lonrange
            y = latrange
            interp_pr_wnp = interp2d(x, y, Z_anom, kind='cubic')
            lonnew = np.arange(100,180.25,0.25)
            latnew = np.arange(0,30.25,0.25)
            pr_wnp25 = interp_pr_wnp(lonnew,latnew)
            
            initial_Z = Z #updating intial accumulated rate to calculate next snaps rain rate

            #putting together new rainrate dataset
            ds_pr_rate_snap = xr.Dataset(
                data_vars=dict(
                    p_r=(["lat", "lon"], pr_wnp25)
                ),
                coords=dict(
                    lon=(["lon"], lonnew),
                    lat=(["lat"], latnew),

                ),
                attrs=dict(description="precip rate for snapshot"),
            )

            
            #get azimuthals
            az_avrs = []
            r_dists = [[0,25,12.5],[25,50,37.5],[50,75,62,5],[75,100,87.5],
                       [100,125,112.5],[125,150,137.5],[150,175,162.5],
                       [175,200,187.5],[200,225,212.5],[225,250,237.5],
                       [250,275,262.5],[275,300,287.5],[300,325,312.5],
                       [325,350,337.5],[350,375,362.5],[375,400,387.5],
                       [400,425,412.5],[425,450,437.5],[450,475,462.5],
                       [475,500,487.5],[500,525,512.5],[525,550,537.5],    #over
                       [550,575,562.5],[575,600,587.5]] 

            storm_center_rad = (np.deg2rad(longitude),np.deg2rad(latitude)) #center of storm in radians
            
            pr_rates = {}
            
            for r in r_dists:
                pr_rates[r[2]]= []
                
            #calculate azimuthal average for each discrete radius
            for lat_vals in ds_pr_rate_snap['p_r']: #going over each latitude value
                for lon_val in lat_vals: #each longitude
                    r_latitude = lon_val['lat'].values
                    r_longitude = lon_val['lon'].values
                    pr_rate = lon_val.values #rainrate at that lat lon 
                    r_radians = [np.deg2rad(r_longitude), np.deg2rad(r_latitude)] #lat lon in radians
                    d = dist( storm_center_rad, r_radians, 6371000/1000 ) 
                    for r in r_dists:
                        if d>=r[0] and d<=r[1]: #if distance matches discrete radius values in 
                                                #list add to list
                            pr_rates[r[2]].append(pr_rate)
            azavs = []
            
            for r in r_dists:
                azav_r = np.nanmean(pr_rates[r[2]])
                azavs.append(azav_r)
            
            allazaverages.append(azavs)

            maxwind = latitude = track_dict[storm][snapshot]["maxwind"]
            if maxwind>=30 and maxwind <=40:
                azaverage_30_40_kt.append(azavs)





### 3) plotting and saving output: #####################################################

r = [12.5, 37.5, 62.5, 87.5, 112.5, 137.5, 162.5, 187.5, 212.5, 237.5, 262.5, 287.5, 312.4,
    337.5, 362.5, 387.5, 412.5, 437.5, 462.5, 487.5, 512.5, 537.5, 562.5, 587.5,]

fig = plt.figure(num=None, figsize=(12, 8))
plt.scatter(r, np.nanmean(azaverage_30_40_kt,axis = 0))
plt.ylim(0, 3)

fname = '/home/disk/p/gnemlaw/mdtf/WorkingDirectory/'+basin+'azimuthal_average_30-40kt.eps'

plt.savefig(fname,format = 'eps' )

# That is the draft code as is it now.I hope I have explained everything sufficiently.
# I currently do not have any error exeption handles/or any messages. I assume I will 
# probably need one but I figured I should get the draft code to you as soon as possible. 
# I'm sure you have lots of comments for how to make the code more general and more effective 
# for the package. Please don't hesitate to bring anything to my attention. 

# ### 7) Error/Exception-Handling Example ########################################
# nonexistent_file_path = "{DATADIR}/mon/nonexistent_file.nc".format(**os.environ)
# try:
#     nonexistent_dataset = xr.open_dataset(nonexistent_file_path)
# except IOError as error:
#     print(error)
#     print("This message is printed by the example POD because exception-handling is working!")


# ### 8) Confirm POD executed sucessfully ########################################
print("Finished successfully! Azimuthal average plot eps file in working directory.")
