# Import modules
import os
import numpy as np
import pandas as pd
import xarray as xr


# ####################### MATH FUNCTION(S) ############################################
def boxavg(thing, lat, lon):
    coslat_values = np.transpose(np.tile(np.cos(np.deg2rad(lat)), (len(lon), 1)))
    thing1 = thing * coslat_values
    thing2 = thing1 / thing1
    average = np.nansum(np.nansum(thing1, 0)) / np.nansum(np.nansum(coslat_values * thing2, 0))

    return average


# ###########################READING IN TRACK DATA######################################################
# Give the start and end year of track data


start_year = np.int(os.getenv("startdate"))
end_year = np.int(os.getenv("enddate"))

# Input of the specific model's lat/lon resolution or grid spacing (degrees) and name of model being run
modelname = str(os.getenv("modelname"))
latres = float(os.getenv("latres"))
lonres = float(os.getenv("lonres"))

# Getting track data, it is currently set up to read in a .txt file, this function will need to be changed
# if your model track data is not in the same format as this .txt file.
trackdata = os.environ["OBS_DATA"] + "/trackdata.txt"


def ReadTrackData(trackdata, start_year, end_year):
    df = pd.read_csv(trackdata, sep='\s+', header=None, names=
    ['lon', 'lat', 'windspeed (m/s)', 'pressure (hPa)', 'year', 'month', 'day', 'hour'])
    # Add flag so it knows where to start from
    df_starts = df[df['lon'] == 'start']
    # Start by assigning first storm in dataset with an ID of 1
    storm_id = 1
    for idx, num_steps in zip(df_starts.index, df_starts['lat'].values):
        # Add in column for storm ID
        df.loc[idx:idx + num_steps + 1, 'stormid'] = storm_id
        # Add 1 to storm ID each time you get to the end of a particular storm track to continue looping
        storm_id += 1

    # Drop the rows that have the starter variable
    df = df.dropna().reset_index(drop=True)  # only in the rows with start have NaN values, so this works

    # Adjust format of some columns
    df.loc[:, 'year'] = df.loc[:, 'year'].astype(int).astype(str)
    df.loc[:, 'month'] = df.loc[:, 'month'].astype(int).astype(str)
    df.loc[:, 'day'] = df.loc[:, 'day'].astype(int).astype(str)
    df.loc[:, 'hour'] = df.loc[:, 'hour'].astype(int).astype(str)

    # Adjust the times to match CMIP6 time read-in format
    df.loc[:, 'hour'] = np.where(df['hour'].astype(int) < 10, '0' + df['hour'], df['hour'])
    df.loc[:, 'day'] = np.where(df['day'].astype(int) < 10, '0' + df['day'], df['day'])
    df.loc[:, 'month'] = np.where(df['month'].astype(int) < 10, '0' + df['month'], df['month'])
    # Create a date stamp column in identical format to cftime conversion to string
    df.loc[:, 'Modeltime'] = df['year'] + '-' + df['month'] + '-' + df['day'] + ' ' + df['hour'] + ':00:00'

    # Find max storm ID number
    num_storms = int(max(df.iloc[:]['stormid']))

    # Creating list of storm IDs by year
    tracks_by_year = {year: [] for year in range(start_year, end_year + 1)}  # empty array of storm tracks by yr
    # Loop through all storms
    for storm in range(1, num_storms + 1):
        # Get list of characteristics of storm ID you're on
        ds_storm = df[df['stormid'] == storm]
        # Get years unique to that storm
        times = ds_storm['year'].values
        if (int(times[0]) < start_year and int(times[-1]) < start_year or
                int(times[0]) > end_year and int(times[-1]) > end_year):
            continue

        tracks_by_year[int(times[0])].append(storm)  # Append list of storms to start year

    return df, tracks_by_year


# Gather relevant variables returned from the track data read in function
df, tracks_by_year = ReadTrackData(trackdata, start_year, end_year)
# C reate empty list of years that are in tracks_by_years to loop through later
years = []
for yr in tracks_by_year:
    years.append(yr)

# ################################## READING IN MODEL DATA FROM TRACK DATA###########################

# Can open any data variable to do this for the given model as the sample 'ds' dataset has all the same dimensions
# and spacing
ds = xr.open_dataset(os.environ["ta_var"], decode_times=True, use_cftime=True)
# Get a list of times from model data into an indexed list to use for later when pulling track
# data for a given time of focus
tarray = ds.indexes['time'].to_datetimeindex()
tarray = tarray.astype(str)
itarray = pd.Index(tarray)
itlist = itarray.tolist()
# Now gather and put general lats/lons list into index format to use later for gathering lat/lonbox data for a given
# time
lats = np.array(ds['lat'])
lons = np.array(ds['lon'])
plevs = np.array(ds['plev'])
ilats = pd.Index(lats)
ilons = pd.Index(lons)
iplevs = pd.Index(plevs)
ilatlist = ilats.tolist()
ilonlist = ilons.tolist()
iplevlist = iplevs.tolist()
# From the track data gather the minimum MSLP for column-integrated MSE
minMSLP = min(df['pressure (hPa)']) * 100
minplev = ds['plev'].sel(plev=minMSLP, method='nearest')
upperlvlplev = min(ds['plev'])
iminplev = iplevlist.index(minplev)
iupperplev = iplevlist.index(upperlvlplev)
# Now close the sample dataset used for gathering indexed lists of variables
ds.close()
# Gather the land-sea mask data and convert the percentages to zeros or NaN's based on if grid point is >20%
# (can use same lat/lon index lists made above as it is the same as other files)
mask_ds = xr.open_dataset(os.environ["OBS_DATA"] + "/sftlf_fx_GFDL-CM4_amip_r1i1p1f1_gr1.nc", decode_times=True,
                          use_cftime=True)
lsm = mask_ds.sftlf
# We have our land-sea mask read in at this point, we can close the parent dataset
mask_ds.close()
# Now open the general variable datasets so they can be pulled from below and only be opened once
phi_ds = xr.open_dataset(os.environ["zg_var"], decode_times=True, use_cftime=True)
T_ds = xr.open_dataset(os.environ["ta_var"], decode_times=True, use_cftime=True)
q_ds = xr.open_dataset(os.environ["hus_var"], decode_times=True, use_cftime=True)
hfls_ds = xr.open_dataset(os.environ["hfls_var"], decode_times=True, use_cftime=True)
hfss_ds = xr.open_dataset(os.environ["hfss_var"], decode_times=True, use_cftime=True)
rlds_ds = xr.open_dataset(os.environ["rlds_var"], decode_times=True, use_cftime=True)
rlus_ds = xr.open_dataset(os.environ["rlus_var"], decode_times=True, use_cftime=True)
rlut_ds = xr.open_dataset(os.environ["rlut_var"], decode_times=True, use_cftime=True)
rsds_ds = xr.open_dataset(os.environ["rsds_var"], decode_times=True, use_cftime=True)
rsdt_ds = xr.open_dataset(os.environ["rsdt_var"], decode_times=True, use_cftime=True)
rsus_ds = xr.open_dataset(os.environ["rsus_var"], decode_times=True, use_cftime=True)
rsut_ds = xr.open_dataset(os.environ["rsut_var"], decode_times=True, use_cftime=True)

# Start Looping through the years so we can have a ntecdf file saved per year that has all the data of variables
# for 10deg lat/lon boxes
for year in years:
    # Set up the 4 dimensions of the data arrays from model data
    # Latitude, Longitude amounts to get 10X10 deg box
    latlen = int(10 / latres + 1)  # Center lat position is one index, then 5 degrees up and 5 degrees down
    lonlen = int(10 / lonres + 1)  # Center lon position is one index, then 5 degrees left and 5 degrees right
    # Get the amount of storms in the year
    numstorms = len(tracks_by_year[year])
    # Get the maximum track observations across all storms in track data
    numsteps = max(df['stormid'].value_counts())

    # Create the 4-D arrays for all variables desired
    h_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    ClmnLWfluxConv_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    ClmnSWfluxConv_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    ClmnRadfluxConv_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    OLR_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistContrib_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempContrib_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hfls_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hfss_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    sfcMoistEnthalpyFlux_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hvar_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistvar_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempvar_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_LWanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_OLRanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_SWanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_RADanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_SEFanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_hflsanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hanom_hfssanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_LWanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_OLRanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_SWanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_RADanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_SEFanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_hflsanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hMoistanom_hfssanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_LWanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_OLRanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_SWanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_RADanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_SEFanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_hflsanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    hTempanom_hfssanom_save = np.ones((numstorms, numsteps, latlen, lonlen)) * np.nan

    # Non-Radiative variables (ex: slp, wind, years, months, days, hours, latbox, lonbox, clat, clon, etc.)
    # 3D variables
    latbox_save = np.ones((numstorms, numsteps, latlen)) * np.nan

    lonbox_save = np.ones((numstorms, numsteps, lonlen)) * np.nan

    # 2D variables
    maxwind_save = np.ones((numstorms, numsteps)) * np.nan

    minSLP_save = np.ones((numstorms, numsteps)) * np.nan

    Clat_save = np.ones((numstorms, numsteps)) * np.nan

    Clon_save = np.ones((numstorms, numsteps)) * np.nan

    year_save = np.ones((numstorms, numsteps)) * np.nan

    month_save = np.ones((numstorms, numsteps)) * np.nan

    day_save = np.ones((numstorms, numsteps)) * np.nan

    hour_save = np.ones((numstorms, numsteps)) * np.nan

    # Start Looping through the storms in the given year
    for s, storm in enumerate(tracks_by_year[year]):
        # Get the storm data for the storm the index is on
        stormdata = df[df['stormid'] == storm]
        # Get list/arrays of all storm track data for the specific storm
        times = stormdata['Modeltime'].values
        clats = np.array(stormdata.loc[:, 'lat'].astype(float))
        clons = np.array(stormdata.loc[:, 'lon'].astype(float))
        maxwind = np.array(stormdata.loc[:, 'windspeed (m/s)'])
        minSLP = np.array(stormdata.loc[:, 'pressure (hPa)'])
        yr = np.array(stormdata.loc[:, 'year'].astype(int))
        mo = np.array(stormdata.loc[:, 'month'].astype(int))
        d = np.array(stormdata.loc[:, 'day'].astype(int))
        hr = np.array(stormdata.loc[:, 'hour'].astype(int))
        # Start looping through all the times in the given storm we are on
        for t, time in enumerate(times):
            # Get time index from the model list of times that matches the track time currently on
            tind = itlist.index(times[t])
            # Get the clat/clon position that is closest to what is provided in track data
            clat = ds['lat'].sel(lat=clats[t], method='nearest')
            clon = ds['lon'].sel(lon=clons[t], method='nearest')
            # Get the index of the above found clat/clon
            iclat = ilatlist.index(clat)
            iclon = ilonlist.index(clon)
            # Now set up bounds of 10X10 deg box based on index spacing and must go 1 higher for largest bound
            latmax = iclat + int((latlen - 1) / 2 + 1)
            latmin = iclat - int((latlen - 1) / 2)
            lonmax = iclon + int((lonlen - 1) / 2 + 1)
            lonmin = iclon - int((lonlen - 1) / 2)
            # Now gather the lat/lon array for the box
            latbox = np.array(ds.lat.isel(lat=slice(latmin, latmax)))
            lonbox = np.array(ds.lon.isel(lon=slice(lonmin, lonmax)))
            # Now make a 2D array based on the land-sea mask that is zeros or NaN if >20%
            landsea_zerosNaNs = np.zeros((len(latbox), len(lonbox)))
            # Open the parent land-sea mask file from outside the loop that is sliced according to the
            # lat/lon bounds above
            landsea_sliced = np.squeeze(lsm.isel(lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            # Now loop through the sliced land-sea mask to assign NaNs to the grid points that are >20
            for i in range(0, len(latbox)):
                for j in range(0, len(lonbox)):
                    if (landsea_sliced[i][j] > 20):
                        landsea_zerosNaNs[i][j] = np.nan

            # Getting h data and calculating h
            g = 9.8  # m/s^2
            Cp = 1.00464e3  # J/(kg*K)
            Lv = 2.501e6  # J/kg
            # Getting geopotential
            phi = np.squeeze(phi_ds['zg'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            # Getting temp
            T = np.squeeze(T_ds['ta'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            # Getting q
            q = np.squeeze(q_ds['hus'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            # Calculate MSE
            mse = Cp * T + g * phi + Lv * q
            # Calculate MSE (Temperature Contribution)
            mseT = Cp * T
            # Calculate MSE (Moisture Contribution)
            mseMoist = Lv * q
            # Get dp and range of p from any of datasets above as they all use same p and indexing
            dp = -1 * np.diff(phi_ds['plev'].isel(plev=slice(iminplev - 1, iupperplev + 1)))  # To get a positive dp
            dptile = np.transpose(np.tile(dp, (mse.shape[1], mse.shape[2], 1)), (2, 0, 1))
            # Do column integration for column-integrated MSE
            h = sum(mse[iminplev:iupperplev + 1, :, :] * dptile) / g  # Column-Integrated MSE
            hTempContrib = sum(mseT[iminplev:iupperplev + 1, :,
                               :] * dptile) / g  # Column-Integrated MSE (Only Temperature Contribution)
            hMoistContrib = sum(mseMoist[iminplev:iupperplev + 1, :,
                                :] * dptile) / g  # Column-Integrated MSE (Only Moisture Contribution)

            # Net LW at sfc regular (rlus-rlds)
            rlus = np.squeeze(rlus_ds['rlus'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            rlds = np.squeeze(rlds_ds['rlds'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            netLWsfc = rlus - rlds

            # Net SW at sfc regular (rsds - rsus)
            rsds = np.squeeze(rsds_ds['rsds'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            rsus = np.squeeze(rsus_ds['rsus'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            netSWsfc = rsds - rsus

            # Net LW at TOA regular (rlut) (no downwelling of LW at TOA)
            rlut = np.squeeze(rlut_ds['rlut'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            netLWtoa = rlut

            # Net SW at TOA regular (rsdt - rsut) (only one downwelling SW at TOA variable, incident)
            rsdt = np.squeeze(rsdt_ds['rsdt'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            rsut = np.squeeze(rsut_ds['rsut'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            netSWtoa = rsdt - rsut

            # Column LW Flux Convergence regular (netLWsfc - netLWtoa)
            ClmnLWfluxConv = netLWsfc - netLWtoa

            # Column SW Flux Convergence regular (netSWtoa - netSWsfc)
            ClmnSWfluxConv = netSWtoa - netSWsfc

            # Column Radiative Flux Convergence regular (ClmnLWfluxConv + ClmnSWfluxConv)
            ClmnRadfluxConv = ClmnLWfluxConv + ClmnSWfluxConv

            # Surface Moist Enthalpy Flux, sfc upward latent heat flux + sfc upward sensible heat flux (hfls + hfss)
            hfls = np.squeeze(hfls_ds['hfls'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            hfss = np.squeeze(hfss_ds['hfss'].isel(time=tind, lat=slice(latmin, latmax), lon=slice(lonmin, lonmax)))
            SfcMoistEnthalpyFlux = hfls + hfss

            # Outgoing Longwave Radiation (OLR):
            OLR = rlut

            # MSE Budget Variables Calculations
            havg = boxavg(h, latbox, lonbox)
            hanom = h - havg

            hTempavg = boxavg(hTempContrib, latbox, lonbox)
            hTempanom = hTempContrib - hTempavg

            hMoistavg = boxavg(hMoistContrib, latbox, lonbox)
            hMoistanom = hMoistContrib - hMoistavg

            LWavg = boxavg(ClmnLWfluxConv, latbox, lonbox)
            LWanom = ClmnLWfluxConv - LWavg

            OLRavg = boxavg(OLR, latbox, lonbox)
            OLRanom = OLR - OLRavg

            SWavg = boxavg(ClmnSWfluxConv, latbox, lonbox)
            SWanom = ClmnSWfluxConv - SWavg

            RADavg = boxavg(ClmnRadfluxConv, latbox, lonbox)
            RADanom = ClmnRadfluxConv - RADavg

            SEFavg = boxavg(SfcMoistEnthalpyFlux, latbox, lonbox)
            SEFanom = SfcMoistEnthalpyFlux - SEFavg

            HFLSavg = boxavg(hfls, latbox, lonbox)
            HFLSanom = hfls - HFLSavg

            HFSSavg = boxavg(hfss, latbox, lonbox)
            HFSSanom = hfss - HFSSavg

            hvar = np.multiply(np.array(hanom), np.array(hanom))

            hMoistvar = np.multiply(np.array(hMoistanom), np.array(hMoistanom))

            hTempvar = np.multiply(np.array(hTempanom), np.array(hTempanom))

            hanomLWanom = np.multiply(np.array(hanom), np.array(LWanom))

            hanomOLRanom = np.multiply(np.array(hanom), np.array(OLRanom))

            hanomSWanom = np.multiply(np.array(hanom), np.array(SWanom))

            hanomRADanom = np.multiply(np.array(hanom), np.array(RADanom))

            hanomSEFanom = np.multiply(np.array(hanom), np.array(SEFanom))

            hanomHFLSanom = np.multiply(np.array(hanom), np.array(HFLSanom))

            hanomHFSSanom = np.multiply(np.array(hanom), np.array(HFSSanom))

            hMoistanomLWanom = np.multiply(np.array(hMoistanom), np.array(LWanom))

            hMoistanomOLRanom = np.multiply(np.array(hMoistanom), np.array(OLRanom))

            hMoistanomSWanom = np.multiply(np.array(hMoistanom), np.array(SWanom))

            hMoistanomRADanom = np.multiply(np.array(hMoistanom), np.array(RADanom))

            hMoistanomSEFanom = np.multiply(np.array(hMoistanom), np.array(SEFanom))

            hMoistanomHFLSanom = np.multiply(np.array(hMoistanom), np.array(HFLSanom))

            hMoistanomHFSSanom = np.multiply(np.array(hMoistanom), np.array(HFSSanom))

            hTempanomLWanom = np.multiply(np.array(hTempanom), np.array(LWanom))

            hTempanomOLRanom = np.multiply(np.array(hTempanom), np.array(OLRanom))

            hTempanomSWanom = np.multiply(np.array(hTempanom), np.array(SWanom))

            hTempanomRADanom = np.multiply(np.array(hTempanom), np.array(RADanom))

            hTempanomSEFanom = np.multiply(np.array(hTempanom), np.array(SEFanom))

            hTempanomHFLSanom = np.multiply(np.array(hTempanom), np.array(HFLSanom))

            hTempanomHFSSanom = np.multiply(np.array(hTempanom), np.array(HFSSanom))

            # Now save the data variables to its corresponding save name created in outer loop and add the land-sea mask to convert >20% land grids to NaN
            # 4D Variables
            h_save[s, t, 0:len(latbox), 0:len(lonbox)] = h + landsea_zerosNaNs
            hMoistContrib_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistContrib + landsea_zerosNaNs
            hTempContrib_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempContrib + landsea_zerosNaNs
            ClmnLWfluxConv_save[s, t, 0:len(latbox), 0:len(lonbox)] = ClmnLWfluxConv + landsea_zerosNaNs
            ClmnSWfluxConv_save[s, t, 0:len(latbox), 0:len(lonbox)] = ClmnSWfluxConv + landsea_zerosNaNs
            ClmnRadfluxConv_save[s, t, 0:len(latbox), 0:len(lonbox)] = ClmnRadfluxConv + landsea_zerosNaNs
            OLR_save[s, t, 0:len(latbox), 0:len(lonbox)] = OLR + landsea_zerosNaNs
            hfls_save[s, t, 0:len(latbox), 0:len(lonbox)] = hfls + landsea_zerosNaNs
            hfss_save[s, t, 0:len(latbox), 0:len(lonbox)] = hfss + landsea_zerosNaNs
            sfcMoistEnthalpyFlux_save[s, t, 0:len(latbox), 0:len(lonbox)] = SfcMoistEnthalpyFlux + landsea_zerosNaNs
            # MSE Budget Variables
            hanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanom + landsea_zerosNaNs
            hvar_save[s, t, 0:len(latbox), 0:len(lonbox)] = hvar + landsea_zerosNaNs
            hMoistvar_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistvar + landsea_zerosNaNs
            hTempvar_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempvar + landsea_zerosNaNs
            hanom_LWanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomLWanom + landsea_zerosNaNs
            hanom_OLRanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomOLRanom + landsea_zerosNaNs
            hanom_SWanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomSWanom + landsea_zerosNaNs
            hanom_RADanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomRADanom + landsea_zerosNaNs
            hanom_SEFanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomSEFanom + landsea_zerosNaNs
            hanom_hflsanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomHFLSanom + landsea_zerosNaNs
            hanom_hfssanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hanomHFSSanom + landsea_zerosNaNs
            hMoistanom_LWanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomLWanom + landsea_zerosNaNs
            hMoistanom_OLRanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomOLRanom + landsea_zerosNaNs
            hMoistanom_SWanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomSWanom + landsea_zerosNaNs
            hMoistanom_RADanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomRADanom + landsea_zerosNaNs
            hMoistanom_SEFanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomSEFanom + landsea_zerosNaNs
            hMoistanom_hflsanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomHFLSanom + landsea_zerosNaNs
            hMoistanom_hfssanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hMoistanomHFSSanom + landsea_zerosNaNs
            hTempanom_LWanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomLWanom + landsea_zerosNaNs
            hTempanom_OLRanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomOLRanom + landsea_zerosNaNs
            hTempanom_SWanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomSWanom + landsea_zerosNaNs
            hTempanom_RADanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomRADanom + landsea_zerosNaNs
            hTempanom_SEFanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomSEFanom + landsea_zerosNaNs
            hTempanom_hflsanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomHFLSanom + landsea_zerosNaNs
            hTempanom_hfssanom_save[s, t, 0:len(latbox), 0:len(lonbox)] = hTempanomHFSSanom + landsea_zerosNaNs

            # 3D Variables
            latbox_save[s, t, 0:len(latbox)] = latbox
            lonbox_save[s, t, 0:len(lonbox)] = lonbox

            # 2D Variables
            maxwind_save[s, t] = maxwind[t]
            minSLP_save[s, t] = minSLP[t]
            Clat_save[s, t] = clat
            Clon_save[s, t] = clon
            year_save[s, t] = yr[t]
            month_save[s, t] = mo[t]
            day_save[s, t] = d[t]
            hour_save[s, t] = hr[t]

    ##### Save the variables, regular variables for each year and budget variables for each year
    regvars_ds = xr.Dataset(
        data_vars=dict(
            h=(['numstorms', 'numsteps', 'latlen', 'lonlen'], h_save,
               {'units': 'J/m^2', 'long_name': 'Column-Integrated MSE', '_FillValue': -9999,
                'GridType': 'Lat/Lon Grid'}),
            hMoistContrib=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistContrib_save,
                           {'units': 'J/m^2', 'long_name': 'Column-Integrated MSE', '_FillValue': -9999,
                            'GridType': 'Lat/Lon Grid'}),
            hTempContrib=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempContrib_save,
                          {'units': 'J/m^2', 'long_name': 'Column-Integrated MSE', '_FillValue': -9999,
                           'GridType': 'Lat/Lon Grid'}),
            ClmnLWfluxConv=(['numstorms', 'numsteps', 'latlen', 'lonlen'], ClmnLWfluxConv_save,
                            {'units': 'W/m^2', 'long_name': 'Column LW Flux Convergence', '_FillValue': -9999,
                             'GridType': 'Lat/Lon Grid'}),
            ClmnSWfluxConv=(['numstorms', 'numsteps', 'latlen', 'lonlen'], ClmnSWfluxConv_save,
                            {'units': 'W/m^2', 'long_name': 'Column SW Flux Convergence', '_FillValue': -9999,
                             'GridType': 'Lat/Lon Grid'}),
            ClmnRadfluxConv=(['numstorms', 'numsteps', 'latlen', 'lonlen'], ClmnRadfluxConv_save,
                             {'units': 'W/m^2', 'long_name': 'Column Radiative Flux Convergence', '_FillValue': -9999,
                              'GridType': 'Lat/Lon Grid'}),
            OLR=(['numstorms', 'numsteps', 'latlen', 'lonlen'], OLR_save,
                 {'units': 'W/m^2', 'long_name': 'Outgoing LW Radiation', '_FillValue': -9999,
                  'GridType': 'Lat/Lon Grid'}),
            hfls=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hfls_save,
                  {'units': 'W/m^2', 'long_name': 'Surface Upward Latent Heat Flux', '_FillValue': -9999,
                   'GridType': 'Lat/Lon Grid'}),
            hfss=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hfss_save,
                  {'units': 'W/m^2', 'long_name': 'Surface Upward Sensible Heat Flux', '_FillValue': -9999,
                   'GridType': 'Lat/Lon Grid'}),
            SEF=(['numstorms', 'numsteps', 'latlen', 'lonlen'], sfcMoistEnthalpyFlux_save,
                 {'units': 'W/m^2', 'long_name': 'Surface Moist Enthalpy Flux', '_FillValue': -9999,
                  'GridType': 'Lat/Lon Grid'}),
            latitude=(['numstorms', 'numsteps', 'latlen'], latbox_save,
                      {'units': 'Degrees', 'long_name': 'Latitude', '_FillValue': -9999,
                       'GridType': '1.0 deg Latitude Spacing'}),
            longitude=(['numstorms', 'numsteps', 'lonlen'], lonbox_save,
                       {'units': 'Degrees', 'long_name': 'Longitude', '_FillValue': -9999,
                        'GridType': '1.25 deg Longitude Spacing'}),
            maxwind=(['numstorms', 'numsteps'], maxwind_save,
                     {'units': 'm/s', 'long_name': 'Maximum Wind Speed', '_FillValue': -9999,
                      'GridType': 'Lat/Lon Grid'}),
            minSLP=(['numstorms', 'numsteps'], minSLP_save,
                    {'units': 'hPa', 'long_name': 'Minimum Sea Level Pressure', '_FillValue': -9999,
                     'GridType': 'Lat/Lon Grid'}),
            centerLat=(['numstorms', 'numsteps'], Clat_save,
                       {'units': 'Degrees', 'long_name': 'TC Center Latitude Position', '_FillValue': -9999,
                        'GridType': '1.0 deg Latitude Spacing'}),
            centerLon=(['numstorms', 'numsteps'], Clon_save,
                       {'units': 'Degrees', 'long_name': 'TC Center Longitude Position', '_FillValue': -9999,
                        'GridType': '1.25 deg Longitude Spacing'}),
            year=(['numstorms', 'numsteps'], year_save, {'units': 'Year of given storm', 'long_name': 'year'}),
            month=(['numstorms', 'numsteps'], month_save, {'units': 'Month of given storm', 'long_name': 'month'}),
            day=(['numstorms', 'numsteps'], day_save, {'units': 'Day of given storm', 'long_name': 'day'}),
            hour=(['numstorms', 'numsteps'], hour_save, {'units': 'Hour of given storm', 'long_name': 'hour'})
        )
    )
    regvars_ds.to_netcdf(os.environ['WK_DIR'] + '/model/Model_Regular_Variables_' + str(year) + '.nc')
    regvars_ds.close()

    budgvars_ds = xr.Dataset(
        data_vars=dict(
            hanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_save,
                   {'units': 'J/m^2', 'long_name': 'Column-Integrated MSE Anomaly', '_FillValue': -9999,
                    'GridType': 'Lat/Lon Grid'}),
            hvar=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hvar_save,
                  {'units': 'J^2*m^-4', 'long_name': 'Variance of Anomaly of Column-Integrated MSE',
                   '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hMoistvar=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistvar_save,
                       {'units': 'J^2*m^-4', 'long_name': 'Variance of Anomaly of Moist Contribution of h',
                        '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hTempvar=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempvar_save,
                      {'units': 'J^2*m^-4', 'long_name': 'Variance of Anomaly of Temp Contribution of h',
                       '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_LWanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_LWanom_save,
                          {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of LW Anomaly and h Anomaly',
                           '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_OLRanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_OLRanom_save,
                           {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of OLR Anomaly and h Anomaly',
                            '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_SWanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_SWanom_save,
                          {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of SW Anomaly and h Anomaly',
                           '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_RADanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_RADanom_save,
                           {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of RAD Anomaly and h Anomaly',
                            '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_SEFanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_SEFanom_save,
                           {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of SEF Anomaly and h Anomaly',
                            '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_hflsanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_hflsanom_save,
                            {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of HFLS Anomaly and h Anomaly',
                             '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hanom_hfssanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hanom_hfssanom_save,
                            {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of HFSS Anomaly and h Anomaly',
                             '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hMoistanom_LWanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_LWanom_save,
                               {'units': 'J^2*m^-4*s^-1',
                                'long_name': 'Product of LW Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                'GridType': 'Lat/Lon Grid'}),
            hTempanom_LWanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_LWanom_save,
                              {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of LW Anomaly and hTempContrib Anomaly',
                               '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hMoistanom_SWanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_SWanom_save,
                               {'units': 'J^2*m^-4*s^-1',
                                'long_name': 'Product of SW Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                'GridType': 'Lat/Lon Grid'}),
            hTempanom_SWanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_SWanom_save,
                              {'units': 'J^2*m^-4*s^-1', 'long_name': 'Product of SW Anomaly and hTempContrib Anomaly',
                               '_FillValue': -9999, 'GridType': 'Lat/Lon Grid'}),
            hMoistanom_OLRanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_OLRanom_save,
                                {'units': 'J^2*m^-4*s^-1',
                                 'long_name': 'Product of OLR Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                 'GridType': 'Lat/Lon Grid'}),
            hTempanom_OLRanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_OLRanom_save,
                               {'units': 'J^2*m^-4*s^-1',
                                'long_name': 'Product of OLR Anomaly and hTempContrib Anomaly', '_FillValue': -9999,
                                'GridType': 'Lat/Lon Grid'}),
            hMoistanom_RADanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_RADanom_save,
                                {'units': 'J^2*m^-4*s^-1',
                                 'long_name': 'Product of RAD Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                 'GridType': 'Lat/Lon Grid'}),
            hTempanom_RADanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_RADanom_save,
                               {'units': 'J^2*m^-4*s^-1',
                                'long_name': 'Product of RAD Anomaly and hTempContrib Anomaly', '_FillValue': -9999,
                                'GridType': 'Lat/Lon Grid'}),
            hMoistanom_SEFanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_SEFanom_save,
                                {'units': 'J^2*m^-4*s^-1',
                                 'long_name': 'Product of SEF Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                 'GridType': 'Lat/Lon Grid'}),
            hTempanom_SEFanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_SEFanom_save,
                               {'units': 'J^2*m^-4*s^-1',
                                'long_name': 'Product of SEF Anomaly and hTempContrib Anomaly', '_FillValue': -9999,
                                'GridType': 'Lat/Lon Grid'}),
            hMoistanom_hflsanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_hflsanom_save,
                                 {'units': 'J^2*m^-4*s^-1',
                                  'long_name': 'Product of HFLS Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                  'GridType': 'Lat/Lon Grid'}),
            hTempanom_hflsanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_hflsanom_save,
                                {'units': 'J^2*m^-4*s^-1',
                                 'long_name': 'Product of HFLS Anomaly and hTempContrib Anomaly', '_FillValue': -9999,
                                 'GridType': 'Lat/Lon Grid'}),
            hMoistanom_hfssanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hMoistanom_hfssanom_save,
                                 {'units': 'J^2*m^-4*s^-1',
                                  'long_name': 'Product of HFSS Anomaly and hMoistContrib Anomaly', '_FillValue': -9999,
                                  'GridType': 'Lat/Lon Grid'}),
            hTempanom_hfssanom=(['numstorms', 'numsteps', 'latlen', 'lonlen'], hTempanom_hfssanom_save,
                                {'units': 'J^2*m^-4*s^-1',
                                 'long_name': 'Product of HFSS Anomaly and hTempContrib Anomaly', '_FillValue': -9999,
                                 'GridType': 'Lat/Lon Grid'}),
            latitude=(['numstorms', 'numsteps', 'latlen'], latbox_save,
                      {'units': 'Degrees', 'long_name': 'Latitude', '_FillValue': -9999,
                       'GridType': '1.0 deg Latitude Spacing'}),
            longitude=(['numstorms', 'numsteps', 'lonlen'], lonbox_save,
                       {'units': 'Degrees', 'long_name': 'Longitude', '_FillValue': -9999,
                        'GridType': '1.25 deg Longitude Spacing'}),
            maxwind=(['numstorms', 'numsteps'], maxwind_save,
                     {'units': 'm/s', 'long_name': 'Maximum Wind Speed', '_FillValue': -9999,
                      'GridType': 'Lat/Lon Grid'}),
            minSLP=(['numstorms', 'numsteps'], minSLP_save,
                    {'units': 'hPa', 'long_name': 'Minimum Sea Level Pressure', '_FillValue': -9999,
                     'GridType': 'Lat/Lon Grid'}),
            centerLat=(['numstorms', 'numsteps'], Clat_save,
                       {'units': 'Degrees', 'long_name': 'TC Center Latitude Position', '_FillValue': -9999,
                        'GridType': '1.0 deg Latitude Spacing'}),
            centerLon=(['numstorms', 'numsteps'], Clon_save,
                       {'units': 'Degrees', 'long_name': 'TC Center Longitude Position', '_FillValue': -9999,
                        'GridType': '1.25 deg Longitude Spacing'}),
            year=(['numstorms', 'numsteps'], year_save, {'units': 'Year of given storm', 'long_name': 'year'}),
            month=(['numstorms', 'numsteps'], month_save, {'units': 'Month of given storm', 'long_name': 'month'}),
            day=(['numstorms', 'numsteps'], day_save, {'units': 'Day of given storm', 'long_name': 'day'}),
            hour=(['numstorms', 'numsteps'], hour_save, {'units': 'Hour of given storm', 'long_name': 'hour'})
        )
    )
    budgvars_ds.to_netcdf(os.environ['WORK_DIR'] + '/model/Model_Budget_Variables_' + str(year) + '.nc')
    budgvars_ds.close()
