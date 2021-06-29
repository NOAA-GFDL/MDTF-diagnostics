# Last update: 28 june, 2021
#Input - 4-D HGT data [time, lev, lat, lon], NetCDF 
#        2.5-degree grid, lat - 90N to 90S, lon - 0 to 357.5E.  

#Output - Pacific and Atlantic TUTT index (Numpy Array) 
#         Plot of HGT, HGTy, and TUTT
#########################################
# Import Pakcages, may need to install some
#########################################
#import matplotlib.pyplot as pyplot
#from mpl_toolkits.basemap import Basemap
#from mpl_toolkits.basemap import addcyclic
import numpy as np
from normalize import normalize
# http://netcdf4-python.googlecode.com/svn/trunk/docs/netCDF4-module.html
from netCDF4 import Dataset, num2date
# http://scikit-image.org/
from skimage import measure
# conda install -c scitools shapely
from shapely.geometry import Polygon, LineString
from scipy.signal import argrelextrema
from scipy.stats.stats import pearsonr
from scipy.interpolate import interp2d
from scipy.interpolate import RectBivariateSpline


def add_cyclic_BL(dat,lon):
  if dat.shape[2]!=lon.shape[0]:
    print('Dimension error in the input data!')
    return
  dat1=np.zeros((dat.shape[0],dat.shape[1],dat.shape[2]+1))
  lon1=np.zeros(lon.shape[0]+1)
  dat1[:,:,:-1]=dat
  dat1[:,:,-1]=dat[:,:,0]
  lon1[:-1]=lon
  lon1[-1]=lon[0]
  return(dat1,lon1)

#########################################
# Input Data
g=9.81
#dlat=2.5
ra=6371000.
omega=7.2921/100000.

#########################################
#Setting variables equal to environment variables set by the diagnostic
time_coord = os.environ["time_coord"]
lat_coord = os.environ["lat_coord"]
lon_coord = os.environ["lon_coord"]
lev_coord = os.environ["lev_coord"]
z200_var = os.environ["Z200_var"] 
WK_DIR    = os.environ["WK_DIR"] 
OBS_DATA  = os.environ["OBS_DATA"] 
CASENAME  = os.environ["CASENAME"] 

#input file specified 
filein=OBS_DATA+"/hgt_1.25_1.25.nc"; vname='hgt'
#filein="Data/hgt.nc"; vname='z'
print("Input File: "+filein)

##Sometimes Pacific and Atlantic TUTTs are connected together
##choose the separating longitude option here (Jay)
##ridge_option=1, the script will search the longitude where the geopotential height is the largest between 120W-80W
##the geopotential height is averaged between the subtropics (20-30N)
##Sometimes the ridge may be weak over Central America (due to model biases), so the user can set perferred separating longitude (ridge_option=2)
print("Sometimes Pacific and Atlantic TUTTs are connected together")
print("Please choose the separating longitude option here")
print("ridge_option=1, the script will search the subtropical ridge over Central America (120W-80W)")
print("ridge_option=2, the dividing longitude is specified by the user")
ridge_option = int(input("Enter a number for ridge_option: "))
if ridge_option==2:
   user_dividing_longitude = int(input("Enter a number between 240-280 (120 W-80 W): "))

#Ug (15N) value that determines the HGTy & TUTT contour 
UG_N15_target=2.0
lat_target=15

#Minimum TUTT areas, measure by the product of the latitude range and the longitude range
#It is a necessary threshold to remove some small wiggles in certain years
min_TUTT=100

#Latitude range to search for HGTy contours
latN=90
latS=-10

#The longitude ranges for the two basins. 
#lonx_AtlW should be the largest possible eastern boundary of the TUTT(Pac). If a point falls east of
#this longitude, we regard it as related to the Atl TUTT
#lonx_PacE should be the largest possible western boundary of the TUTT(Atl). If a point falls west of
#this longitude, we regard it as related to the Pac TUTT
lonx_PacE=270
lonx_AtlW=240

#ref_lat is shifted southward by lat_shift to avoid the connection of TUTT(Pac) with TUTT(Atl)
#south of the ref. latitude. This, however, may render zero TUTT in some years, especially over Atl
lat_shift=-0.0

#time range
#ZW: Something went wrong when I adjusted iyr2 
iyr1 = 1979
iyr2 = 1979
imn1 = 7
imn2 = imn1+3
nyr = iyr2-iyr1+1
nmon = imn2-imn1+1

#month string info
chmon=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
chmns='JFMAMJJASOND'

if imn1==imn2:
  smon=chmon[imn1-1]
else: 
  smon=chmns[imn1-1:imn2]

#plot monthly data in an individual year?
#if Ture, find "# use this when plotting monthly data in individual years" and make changes
#plotting seasonal mean data is possible, but needs some tuning to avoid error messages
plot_yn=True

#output file for ref. lat
filetxt='WK_DIR/obs/tutt_ref.latitude-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f0=open(filetxt,'w+')
f0.write('Year            Ref.Lat            Ref.Lat0'+'\n')

#create an arrary to store TUTT information
#ZW: There may be 3 TUTT regions when analyzing monthly mean data
tutt_index=np.zeros( (nyr, 2) ) #extent
tutt_lon_wt=np.zeros( (nyr, 2) )#area centroid weighted by Ug
tutt_lat_wt=np.zeros( (nyr, 2) )
tutt_lon=np.zeros( (nyr, 2) )   #area centroid
tutt_lat=np.zeros( (nyr, 2) )
tutt_int=np.zeros( (nyr, 2) )   #intensity

#linux-like routine 
ncFid = Dataset (filein, mode = "r")

#read variables in the file; select the vertical level

lon0 = ncFid.variables[ "lon" ][:]
lat0 = ncFid.variables[ "lat" ][:]

#calculate latlon intervals, assuming regular grid spacing
dlon=lon0[1]-lon0[0]
dlat=lat0[1]-lat0[0]

#confine the analysis to the northern hemisphere TUTT between 10S to 90N
#ZW: np.argmin is used to find the index of the closest value
ilat1=np.argmin(abs(lat0-latS))
ilat2=np.argmin(abs(lat0-latN))

#switch ilat1 and ilat2 if the data starting from the NP; isign is set to -1
#to take into account of the geostrophic wind calculation for reversed latitude
isign=1
if dlat<0:
  ii=ilat1
  ilat1=ilat2
  ilat2=ii
  isign=-1

lat=lat0[ilat1:ilat2]
hgt_all = np.squeeze( ncFid.variables[ vname ][:,ilat1:ilat2,:] )

#data from S to N, does not need to be reversed (Jay)
if isign==1:
   lat=np.array(lat[:])
   hgt_all=np.array(hgt_all[:,:,:])   
   dlat=dlat
#data from N to S, need to be reversed (Jay)
if isign==-1:
   lat=np.array(lat[::-1])
   hgt_all=np.array(hgt_all[:,::-1,:])
   dlat=-dlat

#get date information
time = ncFid.variables[ "tim" ][:]
time_units = ncFid.variables[ "tim" ].units
datevar=num2date(time,time_units)

#store date information
tsteps=len(time)
yr_hgt=np.zeros(tsteps)
mon_hgt=np.zeros(tsteps)
for i in range(tsteps):
    yr_hgt[i]=datevar[i].year
    mon_hgt[i]=datevar[i].month

#indices of interested time range
D1=np.where((mon_hgt >= imn1) & (mon_hgt <= imn2) & (yr_hgt >= iyr1) & (yr_hgt <= iyr2))[0] 
#print(D1)
#D2 saves the indices for the first month in a year
if imn2==imn1:			#just one calendar month per year
  D2=D1
else:
  D2=D1[0:-1:nmon]

#get seasonal mean values of HGT
hgt_in=np.zeros([nyr,ilat2-ilat1,lon0.size])
if imn2==imn1:			#just one calendar month per year
  hgt_in=hgt_all[D1,:,:]/1
else: 
  for i in range(nyr):		#seasonal mean
    hgt_in[i,:,:]=np.mean(hgt_all[D1,:,:][i*nmon:i*nmon+nmon,:,:], axis=0)/1

#meridional gradient of HGT
hgt_y=np.gradient(hgt_in, axis=1)/(dlat/180*np.pi*ra)

#geostrophic wind
UG=-hgt_y*g/((2.*omega*np.sin(np.pi*lat_target/180.)))
#get gradient value that correspond to UG_N15_target value
#For a reserved latitude mesh, dlat<0 and this is taken into account in hgt_y
hgty_target=-UG_N15_target/g*(2.*omega*np.sin(np.pi*lat_target/180.))
    
#add cyclic points for longtitude dim
hgt_in, lon = add_cyclic_BL(hgt_in, lon0 )
hgt_y, lon = add_cyclic_BL(hgt_y, lon0 )
#Jay: make the final longitude index to be 360, instead of 0
lon[len(lon0)-1]=360.0

#plot_yn=True
#ZW# UG, lon = addcyclic(UG, lon0 )
lons, lats = np.meshgrid(lon, lat)
#set up the plotting window
#if plot_yn:
#    pyplot.close("all")
#    cmap = pyplot.get_cmap('RdBu_r')
#    fig = pyplot.figure(figsize=(8,10))
#   ax1=pyplot.subplot(2,1,1)
#   m1 = Basemap (llcrnrlon=120.,llcrnrlat=-2.5,urcrnrlon=360.,urcrnrlat=45.,projection = "cyl", lon_0=180)
#    lons, lats = np.meshgrid(lon, lat)
#    x, y = m1(lons, lats) # compute map proj coordinates.
#    m1.drawcoastlines(linewidth =1., color="k")
#    m1.drawparallels(np.arange( -80 ,81 ,20) , labels = [1 ,1 ,0 ,0])
#    m1.drawmeridians(np.arange( -180 ,180 ,60) , labels = [0 ,0 ,0 ,1])

#ZW: define the ref_lat0 based on the long-term mean
contour_yn=False
hgt_ym=np.mean(hgt_y,axis=0)	#long-term mean
contours= measure.find_contours(hgt_ym, hgty_target)
if len(contours) != 0:
   #identify the longest contour, candidate for circumglobal contour
   #length is measured by number of grid points along a contour
   contour=max(contours, key=len)
   #only keep the longest contour, which may be circum-global
   #ZW: contour[:,1] saves longitude indices in the reversed order
   #check if the contour is circum-global
   if len(contour) >= lon.size and contour[-1,1]+contour[0,1] == lon.size-1:
      #convert coordinates to latlon
      lonx0=lon[0]+dlon*contour[:, 1]
      latx0=lat[0]+dlat*contour[:, 0] 
      #reverse the order so that lonx goes from W to E
      if lonx0[1]>lonx0[2]:
        lonx=lonx0[::-1]
        latx=latx0[::-1]
      else:
        lonx=lonx0
        latx=latx0
            
      print("Found contours in the long-term mean")
      contour_yn=True

   #reference latitude, weighted avarage of the latitude of HGTy contour
   #An alternate is to define ref_lat based on the latitude of the zonal mean Ug
   #The difference in TUTT between the two ref_lat is a constant number and does 
   #not affect the corr/composite analysis
   #ref_lon0 is the same as ref_lon, but a different array is created for clarity
   ref_lon0=lon
   dlonx=np.abs(np.gradient(lonx))
   #calculate ref_lat as an weighted average; ref_lat is then shift by "lat_shift" degree
   ref_lat0=np.ones(lon.size)*np.sum(latx*dlonx)/np.sum(dlonx) - lat_shift

#ref_lat0[:]=20.160798378056562

#set UG=np.nan north of ref_lat0
ref_j0=np.argmin(abs(lat-ref_lat0[0]))
ref_0N=np.argmin(abs(lat-0))
UG[:,ref_j0+1:,:]=np.NaN		#only consider data between 0N and ref_lat
UG[:,:ref_0N,:]=np.NaN
UG[np.where(UG<UG_N15_target)]=np.NaN	#only consider westerlies

#if plot_yn:
#   im1=m1.contourf( x, y, np.mean(hgt_in,axis=0), \
#     np.arange(12000,12570,40.), cmap = cmap)
#   im2=m1.contour( x, y, np.mean(hgt_in,axis=0), \
#     np.arange(11840,12610,40.), linewidths=0.5, colors='lightblue')

Dx=D2
for it in range(nyr):
    it_ind=it

    print("")
    print(int(yr_hgt[Dx[it_ind]]),int(mon_hgt[Dx[it_ind]])) 
    
    #find the interested contour
    contour_yn=False
    contours = measure.find_contours(hgt_y[it_ind,:,:], hgty_target)
    if len(contours) != 0:
        #identify the longest contour, candidate for circumglobal contour
        contour=max(contours, key=len)
        #check if the contour is circumglobal
        #contour[:,1] saves longitude indices in the reversed order
        if len(contour) >= lon.size and contour[-1,1]+contour[0,1] == lon.size-1:
            #convert coordinates to lat-lon; find_contours provides desending lon values
            #ZW: lonx0=dlat*contour[:, 1]
            #ZW: latx0=latN-dlat*contour[:, 0] 
            lonx0=lon[0]+dlon*contour[:, 1]
            latx0=lat[0]+dlat*contour[:, 0] 
        
            #reverse the order so that lonx goes from W to E
            if lonx0[1]>lonx0[2]:
              lonx=lonx0[::-1]
              latx=latx0[::-1]
            else:
              lonx=lonx0
              latx=latx0
            
            print("Found contours")
            contour_yn=True

            # Plot the contour on the basemap
#            if plot_yn:
#                m1.plot(lonx, latx, linewidth=1, color='gray')
#output TUTT contour position
            length=np.zeros((1))
            length[0]=len(lonx)
            ref_lat_out=np.zeros((len(lonx)))
            hgt_along_ref_lat=np.zeros((len(lonx)))
            for ii in range(len(lonx)):
#                print(ref_lat0)
                ref_lat_out[ii]=ref_lat0[0]
            np.savetxt('TUTT_ref_lat_'+str(it+iyr1)+'-Ug_'+str(UG_N15_target)+'.txt',ref_lat_out)
            np.savetxt('TUTT_contour_length_'+str(it+iyr1)+'-Ug_'+str(UG_N15_target)+'.txt',length)
            np.savetxt('TUTT_contour_lon_'+str(it+iyr1)+'-Ug_'+str(UG_N15_target)+'.txt',lonx)
            np.savetxt('TUTT_contour_lat_'+str(it+iyr1)+'-Ug_'+str(UG_N15_target)+'.txt',latx)
#try to print TUTT lon/lat? (Jay)

            print('output TUTT position',it+iyr1,lonx.shape,latx.shape)

    #reference longtitude, weighted avarage of the longtiude of HGTy contour          
    #ref_lat varies from year to year, different from ref_lat0
    ref_lon=lon
    dlonx=np.abs(np.gradient(lonx))
    #calculate ref_lat as an weighted average; ref_lat is then shift by one degree
    ref_lat=np.ones(lon.size)*np.sum(latx*dlonx)/np.sum(dlonx) - lat_shift
    #save the reference latitude 
    f0.write(str(iyr1+it-1)+'  '+str(ref_lat[0])+'  '+str(ref_lat0[0])+'\n')

    #coordinates of the circumglobal HGTy contour
    line_hgty_coord=np.zeros((lonx.size,2))
    if contour_yn:
        line_hgty_coord[:,0]=lonx
        line_hgty_coord[:,1]=latx 
        line_hgty=LineString(line_hgty_coord)

    #coordinates of reference lat circle
    line_latref_coord=np.zeros((ref_lon.size,2))
    if contour_yn:
        #line_latref_coord[:,0]=ref_lon		#Gan's original for year-to-year varying ref_lat
        #line_latref_coord[:,1]=ref_lat		#Gan's original
        line_latref_coord[:,0]=ref_lon0		#ZW added
        line_latref_coord[:,1]=ref_lat0		#ZW added
        line_latref=LineString(line_latref_coord)     

    itutt=0
    #check if there is enclosed TUTT region        
    if line_hgty.intersects(line_latref) and contour_yn:
        print("Found Intersection point(s)")
        intersect_point = line_hgty.intersection(line_latref)
        
        #index of intersection points
        icount=0                     
        ind=np.zeros(len(list(intersect_point)),dtype=np.int)              
        for intsec in intersect_point:
            #intsec.x,intsec.y save the lon/lat of the intersection points
            # find the point closest to the intersection points on the HGTy contour
            dist=np.square(lonx-intsec.x)+np.square(latx-intsec.y)
            ind[icount]=np.asarray(np.where(dist == min( dist))[0][0])
            #highlight the intersection point
            #m1.scatter((lonx[ind[icount]]),latx[ind[icount]],50,marker='o',color='g', zorder=9) 
            icount=icount+1
        #order the indices and remove redundant; lonx[ind] is the longitude of intersections
        ind=np.sort(np.unique(ind)) 

	#ZW added: If there are only two intersections, there are three possible scenarios:
	#1)TUTT(Pac)>0 and TUTT(Atl)=0 if both intersection points fall over the Pac
	#2)TUTT(Pac)=0 and TUTT(Atl)>0 if both intersection points fall over the Atl
	#3)TUTT(Pac)>0 and TUTT(Atl)>0 if one falls over the Pac and the other over the Atl
        #lonx_PacE and lonx_AtlW are used to determine the basin boundaries.
        #If lonxW falls west of lonx_PacE, we regard it as related to the Pac TUTT
        #If lonxE falls east of lonx_AtlW, we regard it as related to the Atl TUTT
	#In the 3rd scenario, the northmost "local maximum latitude" point btw the two 
	#intersection points is used to separate TUTT(Pac) and TUTT(Atl). A local max function
	#needs to be used as the true intersection points have the maximum lat (equal to ref_lat)
	#This point is added as an interaction point btw the existing two to divide the basins.
        if len(ind)==2:
            lonxW=lonx[ind[0]]
            lonxE=lonx[ind[1]]
            print('lonxW='+str(lonxW)+'  lonxE='+str(lonxE))
            if lonxW<lonx_PacE and (lonxE>lonx_AtlW):	#lonxW falls over Pac and lonxE over Atl
              print('lonxW falls over Pac and lonxE over Atl')
              ind0=ind
              ind=np.zeros(len(ind0)+1,dtype=np.int)
              ind[0]=ind0[0]
              ind[2]=ind0[1]

              if ridge_option==1:
##Jay: get HGT values between 20-30N to search ridge maximum
                 f=interp2d(lon,lat,hgt_in[it,:,:],kind='cubic',copy=False,bounds_error=True)
                 for ii in range(len(ref_lat_out)):
                     hgt_along_ref_lat[ii]=(f(lonx[ii],20)+f(lonx[ii],21)+f(lonx[ii],22)+f(lonx[ii],23)+f(lonx[ii],24)+f(lonx[ii],25)+f(lonx[ii],26)+f(lonx[ii],27)+f(lonx[ii],28)+f(lonx[ii],29)+f(lonx[ii],30))/11

                 max_hgt=0
                 for ii in range(len(ref_lat_out)):
                     if hgt_along_ref_lat[ii]>max_hgt and lonx[ii]>=240 and lonx[ii]<=280:
                        max_hgt=hgt_along_ref_lat[ii]
#              hgt_along_ref_lat_temp=hgt_along_ref_lat[ind0[0]+1:ind0[1]]
#              hgt_lmax=argrelextrema(hgt_along_ref_lat_temp,np.greater)
              #add the HGT maximum point along the reference lat as a dividing point
                 ind[1]=np.where(hgt_along_ref_lat==max_hgt)[0]
                 print('The dividing longitude based on HGT maximum between 20-30 N: '+str(lonx[ind[1]]))
              if ridge_option==2:
                 temp=np.array(abs(lonx-user_dividing_longitude))
                 min_diff=np.amin(temp,axis=0)
                 ind[1]=np.where(temp==min_diff)[0]
                 print('The dividing longitude set by user: '+str(lonx[ind[1]]))

#output dividing longitude
              lat_0_30N=np.zeros((13))
              dividing_longitude=np.zeros((13))
              for ii in range(13):
                  lat_0_30N[ii]=0+ii*2.5
                  dividing_longitude[ii]=lonx[ind[1]]
              np.savetxt('lat_0_30N.txt',lat_0_30N)
              np.savetxt('dividing_longitude_'+str(it+iyr1)+'.txt',dividing_longitude)

            elif lonxE<lonx_PacE and all(latx[ind[1]:]<=latx[ind[1]]+1.0):
              print('TUTT starts in Pac and extends beyond 360E and is set by lonxW')
              ind0=ind
              ind=np.zeros(len(ind0)+1,dtype=np.int)
              ind[0:2]=ind0
	      #local max lat. on the contour btw lonxE and the east bound of Pac
              ilon_PacE=np.asscalar(np.where(lonx==lonx_PacE)[0])

              if ridge_option==1:
##Jay: get HGT values between 20-30N to search ridge maximum
                 f=interp2d(lon,lat,hgt_in[it,:,:],kind='cubic',copy=False,bounds_error=True)
                 for ii in range(len(ref_lat_out)):
                     hgt_along_ref_lat[ii]=(f(lonx[ii],20)+f(lonx[ii],21)+f(lonx[ii],22)+f(lonx[ii],23)+f(lonx[ii],24)+f(lonx[ii],25)+f(lonx[ii],26)+f(lonx[ii],27)+f(lonx[ii],28)+f(lonx[ii],29)+f(lonx[ii],30))/11

                 max_hgt=0
                 for ii in range(len(ref_lat_out)):
                     if hgt_along_ref_lat[ii]>max_hgt and lonx[ii]>=240 and lonx[ii]<=280:
                        max_hgt=hgt_along_ref_lat[ii]
                 ind[2]=np.where(hgt_along_ref_lat==max_hgt)[0]
                 print('The dividing longitude based on HGT maximum between 20-30 N: '+str(lonx[ind[2]]))
              if ridge_option==2:
                 temp=np.array(abs(lonx-user_dividing_longitude))
                 min_diff=np.amin(temp,axis=0)
                 ind[2]=np.where(temp==min_diff)[0]
                 print('The dividing longitude set by user: '+str(lonx[ind[2]]))

              lat_0_30N=np.zeros((13))
              dividing_longitude=np.zeros((13))
              for ii in range(13):
                  lat_0_30N[ii]=0+ii*2.5
                  dividing_longitude[ii]=lonx[ind[2]]
              np.savetxt('lat_0_30N.txt',lat_0_30N)
              np.savetxt('dividing_longitude_'+str(it+iyr1)+'.txt',dividing_longitude)

            else:
              print('TUTT over one of the basins is zero')
              print(ind)
              print(lonxW,lonxE,lonx_PacE,lonx_AtlW)
        else:
            print('2+ intersections mean more than one TUTT identified')

	#EOT by ZW
        
        #extend the longitude range for the calculation of TUTT indices
        #the Atlantic TUTT can extend eastward and beyond Prime Meridian
        #ZW: lonx_circum=np.append(lonx, lonx[1:180]+360)
        #ZW: latx_circum=np.append(latx, latx[1:180])
        lonx_circum=np.append(lonx, lonx+360)		#ZW
        latx_circum=np.append(latx, latx)		#ZW
        ind_circum=np.append(ind, ind[0]+lonx.size)
        lon_circum=np.append(lon,lon+360)

        #ZW: prepare arrays to calculate tutt_int, tutt_lon and tutt_lat
        lat_south=np.min(latx_circum)		#southmost latitude of lat_circum
        ref_south=np.argmin(abs(lat-lat_south))
        UG[it_ind,:ref_south,:]=np.NaN		#set UG south of ref_south to NaN
        UG_tmp=UG[it_ind]
        Ones_tmp=UG_tmp-UG_tmp+1.0
        UG_circum=np.concatenate((UG_tmp,UG_tmp),axis=1)
        UGx_circum=np.concatenate((UG_tmp*lons[:,:-1],UG_tmp*(lons[:,:-1]+360)),axis=1)
        UGy_circum=np.concatenate((UG_tmp*lats[:,:-1],UG_tmp*lats[:,:-1]),axis=1)
        AREAx_circum=np.concatenate((Ones_tmp*lons[:,:-1],Ones_tmp*(lons[:,:-1]+360)),axis=1)
        AREAy_circum=np.concatenate((Ones_tmp*lats[:,:-1],Ones_tmp*lats[:,:-1]),axis=1)

        for i in range(len(ind)):
            # approximation of arcs, including both TUTT and the ridges
            poly_coord1=np.zeros((ind_circum[i+1]-ind_circum[i]+1,2))
            poly_coord1[:,0]=lonx_circum[ ind_circum[i]:ind_circum[i+1]+1 ]
            poly_coord1[:,1]=latx_circum[ ind_circum[i]:ind_circum[i+1]+1 ]
            #longtitude and latitude range of the arcs
            dy_test=np.amax(poly_coord1[:,1]) - np.amin(poly_coord1[:,1])
            dx_test=np.amax(poly_coord1[:,0]) - np.amin(poly_coord1[:,0])
            #print(i, ind_circum[i], ind_circum[i+1]+1)
            #must be south of the reference latitude, north of 5S, and covers a large area            
            #ZW: if all(poly_coord1[1:-2,1]<=ref_lat[0]) and all(poly_coord1[1:-2,1]>=-5) \
            if all(poly_coord1[1:-2,1]<=ref_lat0[0]) and all(poly_coord1[1:-2,1]>=-5) \
                  and dx_test*dy_test>=min_TUTT:
                #construct a polygon with poly_coord1 as vertices. The ref lat. is the north edge
#Jay: set the latitude in poly_coord1 higher than reference latitude equals to reference latitude
                for ii in range(len(poly_coord1[:,0])):
                    if poly_coord1[ii,1] > ref_lat0[0]:
                       poly_coord1[ii,1]=ref_lat0[0]

#Jay: scenario 1, the starting latitude and ending latitude of poly_coord1 both lower than reference latitude
                if poly_coord1[0,1] < ref_lat0[0] and poly_coord1[len(poly_coord1[:,0])-1,1] < ref_lat0[0]:
                   poly_coord1_new=np.zeros((len(poly_coord1[:,0])+2,2))
                   poly_coord1_new[0,0]=poly_coord1[0,0]
                   poly_coord1_new[0,1]=ref_lat0[0]
                   poly_coord1_new[len(poly_coord1[:,0])+1,0]=poly_coord1[len(poly_coord1[:,0])-1,0]
                   poly_coord1_new[len(poly_coord1[:,0])+1,1]=ref_lat0[0]
                   poly_coord1_new[1:len(poly_coord1[:,0])+1,:]=poly_coord1[:,:]

#Jay: scenario 2, the starting latitude is lower than reference latitude
                elif poly_coord1[0,1] < ref_lat0[0]:
                   poly_coord1_new=np.zeros((len(poly_coord1[:,0])+1,2))
                   poly_coord1_new[0,0]=poly_coord1[0,0]
                   poly_coord1_new[0,1]=ref_lat0[0]
                   poly_coord1_new[1:len(poly_coord1[:,0])+1,:]=poly_coord1[:,:]

#Jay: scenario 3, the ending latitude is lower than reference latitude
                elif poly_coord1[len(poly_coord1[:,0])-1,1] < ref_lat0[0]:
                   poly_coord1_new=np.zeros((len(poly_coord1[:,0])+1,2))
                   poly_coord1_new[len(poly_coord1[:,0]),0]=poly_coord1[len(poly_coord1[:,0])-1,0]
                   poly_coord1_new[len(poly_coord1[:,0]),1]=ref_lat0[0]
                   poly_coord1_new[0:len(poly_coord1[:,0]),:]=poly_coord1[:,:]
                else:
                   poly_coord1_new=np.array((poly_coord1))


                mm=Polygon(poly_coord1_new)

                # Area approximation by scaling with cos, Python don't have good functions to 
                # calculate the area of spherical polygons
                tutt_area=mm.area*np.cos(np.pi*np.mean(poly_coord1[:,1])/180. )
                print(tutt_area)
                #store TUTT index. Ideally there should be two TUTTs, Pac(0) and Atl(1)
                tutt_index[ int(yr_hgt[Dx[it_ind]])-iyr1, itutt ] = tutt_area

		#ZW:calculate the other TUTT indices
                i1=np.argmin(abs(lon_circum-lonx_circum[ind_circum[i]]))
                i2=np.argmin(abs(lon_circum-lonx_circum[ind_circum[i+1]]))+1
	        Ugmean=np.nanmean(UG_circum[:,i1:i2])
                tutt_lon_wt[it_ind,itutt]=np.nanmean(UGx_circum[:,i1:i2])/Ugmean
                tutt_lat_wt[it_ind,itutt]=np.nanmean(UGy_circum[:,i1:i2])/Ugmean
                tutt_lon[it_ind,itutt]=np.nanmean(AREAx_circum[:,i1:i2])
                tutt_lat[it_ind,itutt]=np.nanmean(AREAy_circum[:,i1:i2])

                # print to check
                itutt=itutt+1

##ZW# print tutt index
for iy in range(iyr1,iyr2+1):
  print(iy,tutt_index[iy-iyr1,:])

#calculate the corr. between Atl and Pac
rr=np.corrcoef(tutt_index.T)[0,1]
print('Corr = '+str(rr))

#if plot_yn:
#    m1.plot(ref_lon0, ref_lat0, linewidth=2, linestyle="--",color='w')
#    cbar_ax = fig.add_axes([0.20, 0.58, 0.6, 0.02])
#    fig.colorbar(im1, cax=cbar_ax,orientation='horizontal')
#    ax1.set_title('(a) TUTT in Individual Years',loc='left',fontsize=12)

#    ax2=pyplot.subplot(4,1,3)
#    iyrs=np.arange(iyr1,iyr2+1)
#    pyplot.plot(iyrs,normalize(tutt_index[:,0]),label='Pac')
#    pyplot.plot(iyrs,normalize(tutt_index[:,1]),label='Atl')
#    pyplot.plot(iyrs,np.zeros(len(iyrs)),color='gray',linewidth='0.4')
#    ax2.set_xlim(iyr1,iyr2)
#    ax2.legend()
#    ax2.set_title('(b) TUTT Time Series',loc='left',fontsize=12)
#    ax2.set_title('r='+str(np.round(rr,2)),loc='right',fontsize=12)

#    fmt='pdf'
#    pyplot.show(block=False)
#    pyplot.savefig(''+str(model)+'_'+str(scenario)+'_TUTT_'+smon+'_UG15N_'+str(UG_N15_target)+'.'+fmt,format=fmt,bbox_inches='tight')

#close the file for ref.lat
#f0.close()
#Save the TUTT time series in a text file
fileout='tutt_area-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f1=open(fileout,'w+')
f1.write('Year            Pac             Atl'+'\n')
for iy in range(iyr1,iyr2+1):
  f1.write(str(iy)+'  '+str(tutt_index[iy-iyr1,0])+'  '+str(tutt_index[iy-iyr1,1])+'\n')
f1.close()

fileout='tutt_intensity-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f1=open(fileout,'w+')
f1.write('Year            Pac             Atl'+'\n')
for iy in range(iyr1,iyr2+1):
  f1.write(str(iy)+'  '+str(tutt_int[iy-iyr1,0])+'  '+str(tutt_int[iy-iyr1,1])+'\n')
f1.close()

fileout='tutt_UG.wt_lon-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f1=open(fileout,'w+')
f1.write('Year            Pac             Atl'+'\n')
for iy in range(iyr1,iyr2+1):
  f1.write(str(iy)+'  '+str(tutt_lon_wt[iy-iyr1,0])+'  '+str(tutt_lon_wt[iy-iyr1,1])+'\n')
f1.close()

fileout='tutt_UG.wt_lat-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f1=open(fileout,'w+')
f1.write('Year            Pac             Atl'+'\n')
for iy in range(iyr1,iyr2+1):
  f1.write(str(iy)+'  '+str(tutt_lat_wt[iy-iyr1,0])+'  '+str(tutt_lat_wt[iy-iyr1,1])+'\n')
f1.close()

fileout='tutt_Area_lon-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f1=open(fileout,'w+')
f1.write('Year            Pac             Atl'+'\n')
for iy in range(iyr1,iyr2+1):
  f1.write(str(iy)+'  '+str(tutt_lon[iy-iyr1,0])+'  '+str(tutt_lon[iy-iyr1,1])+'\n')
f1.close()

fileout='tutt_Area_lat-'+str(iyr1)+'-'+str(iyr2)+smon+'-Ug_'+str(UG_N15_target)+'.txt'
f1=open(fileout,'w+')
f1.write('Year            Pac             Atl'+'\n')
for iy in range(iyr1,iyr2+1):
  f1.write(str(iy)+'  '+str(tutt_lat[iy-iyr1,0])+'  '+str(tutt_lat[iy-iyr1,1])+'\n')
f1.close()

print('Normal End!')

