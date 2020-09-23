from ecmwfapi import ECMWFDataServer
import os

def get_srf (year, param, targetLoc):
  server = ECMWFDataServer()
  server.retrieve({
    "class": "ei",
    "dataset": "interim",
    "date": "{0}-01-01/to/{0}-12-31".format(year),
    "expver": "1",
    "grid": "1.5/1.5",
    "levtype": "sfc",
    "param": param,
    "step": "0",
    "stream": "oper",
    "time": "00:00:00/06:00:00/12:00:00/18:00:00",
    "type": "an",
    "format": 'netcdf',
    "target": targetLoc
    })

def get_lvl (year, param, targetLoc, plevel):
  #!/usr/bin/env python
  server = ECMWFDataServer()
  server.retrieve({
    "class": "ei",
    "dataset": "interim",
    "date": "{0}-01-01/to/{0}-12-31".format(year),
    "expver": "1",
    "grid": "1.5/1.5",
    "levelist": plevel,
    "levtype": "pl",
    "param": param,
    "step": "0",
    "stream": "oper",
    "time": "00:00:00/06:00:00/12:00:00/18:00:00",
    "type": "an",
    "format": 'netcdf', 
    "target": targetLoc
    })

def get_var3d (year, param, targetLoc):
  #!/usr/bin/env python
  server = ECMWFDataServer()
  server.retrieve({
    "class": "ei",
    "dataset": "interim",
    "date": "{0}-01-01/to/{0}-12-31".format(year),
    "expver": "1",
    "grid": "1.5/1.5",
    "levelist": "1/2/3/5/7/10/20/30/50/70/100/125/150/175/200/225/250/300/350/400/450/500/550/600/650/700/750/775/800/825/850/875/900/925/950/975/1000",
    "levtype": "pl",
    "param": param,
    "step": "0",
    "stream": "oper",
    "time": "00:00:00/06:00:00/12:00:00/18:00:00",
    "type": "an",
    "format": 'netcdf', 
    "target": targetLoc
    })

years = [1979, 1980]

# Front Detection Needed Variables
srf_varList = {'slp': '151.128', 'ps': '134.128'}
srf_varList = {}

lvl_pres = [850]
lvl_varList = {'hgt': '129.128', 'u': '131.128', 'v': '132.128'}
lvl_varList = {}

all_lvl_varList = {'hgt3d': '129.128', 't': '130.128'}
all_lvl_varList = {'u3d': '131.128', 'v3d': '132.128'}
all_lvl_varList = {'w3d': '135.128'}
# all_lvl_varList = {'cc3d': '248.128'}

# # Other variables 
# all_lvl_varList = {'cc3d': '248.128', 'U3d': '131.128', 'V3d': '132.128', 'hgt3d': '129.128', 't': '130.128'}

targetLoc = '/localdrive/drive6/erai/dl/'; 

loopCnt = 0; 

for year in range(years[0], years[1]+1):

  year_folder = os.path.join(targetLoc, '{0}'.format(year))
  if (not os.path.exists(year_folder)):
    os.makedirs(year_folder)

  # download surface variables 
  for key in srf_varList.keys():
    param = srf_varList[key]
    ncFile = os.path.join(targetLoc, '{1}/{0}_{1}.nc'.format(key,year))
    if (not os.path.exists(ncFile)):
      get_srf(year,param,ncFile); 

  # download pressure level variables 
  for key in lvl_varList.keys():
    for pLevelCnt, _ in enumerate(lvl_pres):
      param = lvl_varList[key]
      plevel = str(lvl_pres[pLevelCnt]); 
      ncFile = os.path.join(targetLoc, '{2}/{0}{1}_{2}.nc'.format(key, plevel, year))
      if (not os.path.exists(ncFile)):
        get_lvl(year,param,ncFile,plevel); 
  
  # download variables with all pressure variables
  for key in all_lvl_varList.keys():
    param = all_lvl_varList[key]
    ncFile = os.path.join(targetLoc, '{1}/{0}_{1}.nc'.format(key, year))
    if (not os.path.exists(ncFile)):
      get_var3d(year,param,ncFile); 
  
