import xarray as xr
import numpy as np
import math
from math import pi


def _grid_metrics(lat, lon):
    """Return meridional integration lengths and spherical cell areas.

    The legacy expression is retained bit-for-bit on regular grids. Midpoint
    cell edges extend the same calculation to Gaussian and other monotonic
    rectilinear model grids.
    """
    R = 6.371 * 1.e6
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    lat_steps = np.abs(np.diff(lat))
    lon_steps = np.diff(lon)
    regular_lat = np.allclose(lat_steps, lat_steps[0], rtol=1.e-5, atol=1.e-8)
    regular_lon = np.allclose(lon_steps, lon_steps[0], rtol=1.e-5, atol=1.e-8)

    if regular_lat and regular_lon:
        dlat = (lat[0] - lat[1]) * pi / 180
        dlon = (lon[1] - lon[0]) * pi / 180
        clat = np.abs(np.cos(lat * pi / 180)[:, np.newaxis] * np.ones((len(lat), len(lon))))
        dphi = R * dlat * clat
        area = np.zeros((len(lat), len(lon)))
        for la in np.arange(len(lat)):
            if lat[la] == 90 or lat[la] == -90:
                area[la, :] = (R ** 2) * (1 - np.sin(pi / 2 - dlat / 2)) * dlon
            else:
                area[la, :] = (R ** 2) * (
                    np.sin(lat[la] * pi / 180 + dlat / 2)
                    - np.sin(lat[la] * pi / 180 - dlat / 2)
                ) * dlon
        return dphi, area

    lat_edges = np.empty(len(lat) + 1)
    lat_edges[0] = min(90.0, lat[0] + 0.5 * (lat[0] - lat[1]))
    lat_edges[-1] = max(-90.0, lat[-1] - 0.5 * (lat[-2] - lat[-1]))
    lat_edges[1:-1] = 0.5 * (lat[:-1] + lat[1:])
    lat_width = np.deg2rad(lat_edges[:-1] - lat_edges[1:])

    cyclic_gaps = np.concatenate([lon_steps, [360.0 - (lon[-1] - lon[0])]])
    lon_width = np.deg2rad(0.5 * (np.roll(cyclic_gaps, 1) + cyclic_gaps))
    dphi = R * lat_width[:, np.newaxis] * np.abs(np.cos(np.deg2rad(lat)))[:, np.newaxis]
    area = (R ** 2) * (
        np.sin(np.deg2rad(lat_edges[:-1])) - np.sin(np.deg2rad(lat_edges[1:]))
    )[:, np.newaxis] * lon_width[np.newaxis, :]
    return dphi, area

## LWA Calculation
def eqlat(Z500, area, lat, hemisphere):
    R = 6.371*1.e6

    nlat = len(lat)
    fi_t = np.zeros(nlat)    # fi_t is an array storing latitudes which correspond to different qgpv levels

    ## Create the qgpv levels evenly. nlat levels in total
    maxlevel = Z500[:,:].max()
    minlevel = Z500[:,:].min()
    levs = np.linspace(minlevel, maxlevel, nlat)

    #calculate the equivalent latitude
    if hemisphere==1:
        for k in np.arange(nlat):
            A = sum(area[Z500[:,:] <= levs[k]])       #Note, for Z500, the bounded area is where Z500 < contour, becasue Z500 decreases with latitude
            fi = np.arcsin(1 - A/(2*pi*(R**2)))       #This is the formula to calculate the equivlant latitude which corresponds to the kth qgpv level
            fi = fi * (180/pi)
            fi_t[nlat-1-k] = fi

        q_part = np.interp(lat, fi_t[:], levs[::-1])       # A simple interploration that give equivalent qgpv values to each latitude from our data.

    elif hemisphere==2:
        for k in np.arange(nlat):
            A = sum(area[Z500[:,:] <= levs[k]])       #Note, for QGPV, the bounded area is where QGPV > contour, becasue QGPV increases with latitude
            fi = np.arcsin(A/(2*pi*(R**2)) - 1)
            fi = fi * (180/pi)
            fi_t[k] = fi

        q_part = np.interp(lat[:], fi_t[:], levs[:])

    return q_part

# This module is to calculate the last part of lwa
def lwa(Z500, area, q_part, nlat, nlon, laa, lat, dphi, hemisphere, flag):
    import numpy as np

    if hemisphere ==1:
        LWA = np.zeros((nlat,nlon))

        for k in np.arange(nlat):
            QB = np.zeros((nlat,nlon))                  # QGPV increases with latitude, so we need areas where q>=0 but latitude <= lat[k]
            q = Z500[:,:] - q_part[k]                   # Difference between real qgpv and equivlent qgpv for the kth latitude
            if flag == "anticyclone":
                QB[(laa>=lat[k]) & (q>=0)] = 1          # Anticyclonic component
            elif flag == "cyclone":
                QB[(laa<=lat[k]) & (q<=0)] = -1         # cyclonic component
            elif flag == "all":
                QB[(laa>=lat[k]) & (q>=0)] = 1          # Anticyclonic component
                QB[(laa<=lat[k]) & (q<=0)] = -1         # cyclonic component
            else:
                raise ValueError("Error: Unauthorized name! Program stopped.")

            LWA[k,:] = np.sum(QB * q * dphi, axis=0)

    elif hemisphere == 2:
        LWA = np.zeros((nlat,nlon))

        for k in np.arange(nlat):
            QB = np.zeros((nlat,nlon))
            q = Z500[:,:] - q_part[k]
            if flag == "anticyclone":
                QB[(laa<=lat[k]) & (q>=0)] = 1              # Anticyclonic component
            elif flag == "cyclone":
                QB[(laa>=lat[k]) & (q<=0)] = -1             # cyclonic component
            elif flag == "all":
                QB[(laa<=lat[k]) & (q>=0)] = 1              # Anticyclonic component
                QB[(laa>=lat[k]) & (q<=0)] = -1             # cyclonic component
            else:
                raise ValueError("Error: Unauthorized name! Program stopped.")

            LWA[k,:] = np.sum(QB * q * dphi, axis=0)

    return LWA

def Cal(ds, lat_name, lon_name, time_name, flag):
    # Latitude has to go from 90 to 0 to -90
    ds = ds.sortby(lat_name, ascending=False)
    #lat, lon, z = ds[lat_name].values, ds[lon_name].values, ds.values
    lat, lon = ds[lat_name].values, ds[lon_name].values

    nlat, nlon, ndays = len(lat), len(lon), ds[time_name].shape[0]

    nh_desc = np.flatnonzero(lat > 0)
    sh_desc = np.flatnonzero(lat <= 0)
    if len(nh_desc) < 2 or len(sh_desc) < 2:
        raise ValueError("LWA requires grid points in both hemispheres")
    dphi, area = _grid_metrics(lat, lon)

    LWA_td = np.zeros((ndays,nlat,nlon))

    ti = -1
    ###--------The core code-----------------
    for t in np.arange(ndays):
        ti+=1

        Z500 = ds.isel(**{time_name: t}).values

        #print('z500= ', Z500)

        ###Core part for calculating LWA
        LWA_z = np.zeros((nlat,nlon))

        ##------------------------Northern Hemisphere------------------------------
        nh = nh_desc[::-1]
        lat1 = lat[nh]
        #print('lat NH =', lat1)
        nlat1 = len(lat1)
        dphi1 = dphi[nh]
        LWA_z1 = np.zeros((nlat1,nlon))
        loo1,laa1 = np.meshgrid(lon,lat1)

        q_part1 = eqlat(Z500[nh, :], area[nh], lat1, 1)  #1 is for NH
        LWA_z1[:,:] = lwa(Z500[nh, :], area[nh], q_part1, nlat1, nlon, laa1, lat1, dphi1, 1, flag)

        ##-------------------------Southern Hemisphere-----------------------------
        sh = sh_desc[::-1]
        lat2 = lat[sh]
        #print('lat SH =', lat2)
        nlat2 = len(lat2)
        dphi2 = dphi[sh]
        LWA_z2 = np.zeros((nlat2,nlon))
        loo2,laa2 = np.meshgrid(lon,lat2)


        q_part2 = eqlat(Z500[sh, :], area[sh], lat2, 2)   #2 is for SH
        LWA_z2[:,:] = lwa(Z500[sh, :], area[sh], q_part2, nlat2, nlon, laa2, lat2, dphi2, 2, flag)

        LWA_z[nh_desc, :] = LWA_z1[::-1, :]
        LWA_z[sh_desc, :] = LWA_z2[::-1, :]
        LWA_td[ti,:,:] = LWA_z

        #print('t= ', ti)


    # LWA Calulation Part II
    for x in np.arange(nlat):
        if np.isclose(np.abs(lat[x]), 90):  # Poles at ±90°
            LWA_td[:, x, :] = np.nan
        else:
            cos_lat = np.cos(np.deg2rad(lat[x]))
            LWA_td[:, x, :] = LWA_td[:, x, :] / cos_lat

    return LWA_td, lat, lon
