#Downloading anomaly data from the IRI

# Specifying spatial domain
nla=55 	# Northernmost latitude
sla=20 	# Southernmost latitude
wlo=-140 	# Westernmost longitude
elo=-100 	# Easternmost longitude
#Specifying time domain:
season='Jan-Dec'
yeari=1982
yeare=2010
#Indicate if force download all data (True in case it's corrupted or new one is needed)
force=True

#Create folder to input data and figures
!mkdir -p WUS
!cd WUS
!mkdir -p WUS/data/
!mkdir -p figs #this will probably need to be changed


# To download data from the IRI data library, you need an authentication key. This is stored in a file called .IRIDLAUTH, but is not part of the GitHub repository -- you need to contact the IRI Data Library to request access. Once you have done so, you can put your own authentication key in a file called .IRIDLAUTH and use this code. This is a moderately annoying step, and we apologize, but it is required by the S2S Database Terms and Conditions and is necessary for us to share all our code while maintaining some security.

# if you're using git, be sure to add .IRIDLAUTH to your gitignore file

with open('.IRIDLAUTH') as file:
    authkey = file.read() 
    
#NEED TO CHANGE OUTFILE PATHS FOR POD

reanalysis = download_data( #Anomaly data for physical field used to build 
                            # weather types (geopotential height)
    url='http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.DAILY/.Intrinsic/.PressureLevel/.phi/P/(500)/VALUE/T/%28days%20since%201960-01-01%2000:00:00%29/streamgridunitconvert/T/('+season+'%20'+str(yeari)+'-'+str(yeare)+')/RANGE/T//pointwidth/0/def/-0.5/shiftGRID/X/('+str(wlo)+')/('+str(elo)+')/RANGE/Y/('+str(sla)+')/('+str(nla)+')/RANGE/dup/T/to366daysample/%5BYR%5Daverage/T/sampleDOY/sub/T/5/runningAverage/T/0.5/shiftGRID/data.nc',
    outfile='WUS/data/hgt_NNRP_rean.nc', 
    authkey=authkey,
    force_download=force
)

uwnd = download_data(
    url='http://iridl.ldeo.columbia.edu/home/.agmunoz/.NNRP/.chi_200/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.DAILY/.Intrinsic/.PressureLevel/.u/%5BX/Y%5D/regridAverage/T/(days%20since%201960-01-01%2000%3A00%3A00)/streamgridunitconvert/P/(850)/VALUE/T/('+season+'%20'+str(yeari)+'-'+str(yeare)+')/RANGE/T//pointwidth/0/def/-0.5/shiftGRID/X/('+str(wlo)+')/('+str(elo)+')/RANGE/Y/('+str(sla)+')/('+str(nla)+')/RANGE/dup/T/to366daysample/%5BYR%5Daverage/T/sampleDOY/sub/T/5/runningAverage/T/0.5/shiftGRID/data.nc',
    outfile='WUS/data/u_NNRP_rean.nc', 
    authkey=authkey,
    force_download=force
)

vwnd = download_data(
    url='http://iridl.ldeo.columbia.edu/home/.agmunoz/.NNRP/.chi_200/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.DAILY/.Intrinsic/.PressureLevel/.v/%5BX/Y%5D/regridAverage/T/(days%20since%201960-01-01%2000%3A00%3A00)/streamgridunitconvert/P/(850)/VALUE/T/('+season+'%20'+str(yeari)+'-'+str(yeare)+')/RANGE/T//pointwidth/0/def/-0.5/shiftGRID/X/('+str(wlo)+')/('+str(elo)+')/RANGE/Y/('+str(sla)+')/('+str(nla)+')/RANGE/dup/T/to366daysample/%5BYR%5Daverage/T/sampleDOY/sub/T/5/runningAverage/T/0.5/shiftGRID/data.nc',
    outfile='WUS/data/v_NNRP_rean.nc', 
    authkey=authkey,
    force_download=force
)

rainfall = download_data(
    url='http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.CPC/.UNIFIED_PRCP/.GAUGE_BASED/.GLOBAL/.v1p0/.extREALTIME/.rain/T/%28days%20since%201960-01-01%2000:00:00%29/streamgridunitconvert/T/%28%201%20Jan%20'+str(yeari)+'%29/%2830%20Dec%20'+str(yeare)+'%29/RANGEEDGES/T//pointwidth/0/def/0./shiftGRID/X/('+str(wlo)+')/('+str(elo)+')/RANGE/Y/('+str(sla)+')/('+str(nla)+')/RANGE/dup/T/to366daysample/%5BYR%5Daverage/T/sampleDOY/sub/T/5/runningAverage/T/0.5/shiftGRID/data.nc',
    outfile='WUS/data/rainfall_cpc.nc', 
    authkey=authkey,
    force_download=force
)


t2m  = download_data(
    url='http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.CPC/.temperature/.daily/.tmax/SOURCES/.NOAA/.NCEP/.CPC/.temperature/.daily/.tmin/add/2/div/T/(days%20since%201960-01-01%2000%3A00%3A00)/streamgridunitconvert/T/(Jan-Dec%201985-2015)/RANGE/T//pointwidth/0/def/-0.5/shiftGRID/X/('+str(wlo)+')/('+str(elo)+')/RANGE/Y/('+str(sla)+')/('+str(nla)+')/RANGE/dup/T/to366daysample/%5BYR%5Daverage/T/sampleDOY/sub/T/5/runningAverage/T/0.5/shiftGRID/data.nc',
    outfile='WUS/data/t2m_cpc.nc', 
    authkey=authkey,
    force_download=force
)

