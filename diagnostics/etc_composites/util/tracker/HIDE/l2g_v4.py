import numpy

def l2g2(lon,lat,i_lons,j_lats,n):
    """Converts lon, lat into nearest gridID
    This version is 10x faster!
    """
    # Convert longitude to 0-360 if not already
    lon = (lon + 360.0)%360.0
    # Find i_lon closest to lon
    i = (numpy.abs(i_lons-lon)).argmin()
    # Find j_lat closest to lat
    j = (numpy.abs(j_lats-lat)).argmin()
    gridid = j*n + i
    return gridid,i_lons[i],j_lats[j]

def l2g(lon,lat,i_lons,j_lats):
    """Converts lon, lat into nearest gridID"""

    # Convert longitude to 0-360 if not already
    if lon < 0.0:
        lon += 360.0

    # Find i_lon closest to lon
    lon_diffs = [abs(lon-x) for x in i_lons]
    tmp = lon_diffs[:] # store unsorted copy
#    for i in range(len(i_lons)):
#        print i,i_lons[i],lon_diffs[i]
    lon_diffs.sort() #ADDED!=
    closest = lon_diffs[0]
#    print closest
    # i-index of closest center longitude
    i = tmp.index(closest)
#    print i

    # Find j_lat closest to lat
    lat_diffs = [abs(lat-x) for x in j_lats]
#    for j in range(len(j_lats)):
#        print j,j_lats[j],lat_diffs[j]
    tmp = lat_diffs[:] # store unsorted copy
    lat_diffs.sort()
    closest = lat_diffs[0]
#    print closest
    # j-index of closest center latgitude
    j = tmp.index(closest)
#    print j

    # Determine gridID
    if i < len(i_lons) and j < len(j_lats):
        gridid = j*len(i_lons) + i
    else:
        import sys;sys.exit("ERROR in l2g")

#    print "\tConverted % 4d % 4d to % 6d" % (lon,lat,gridid)

    return gridid,i_lons[i],j_lats[j]

#---Start of main code block.
if __name__=='__main__':     

    lons = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0,
            27.5, 30.0, 32.5, 35.0, 37.5, 40.0, 42.5, 45.0, 47.5, 50.0, 52.5
            , 55.0, 57.5, 60.0, 62.5, 65.0, 67.5, 70.0, 72.5, 75.0, 77.5,
            80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0, 97.5, 100.0, 102.5,
            105.0, 107.5, 110.0, 112.5, 115.0, 117.5, 120.0, 122.5, 125.0,
            127.5, 130.0, 132.5, 135.0, 137.5, 140.0, 142.5, 145.0, 147.5,
            150.0, 152.5, 155.0, 157.5, 160.0, 162.5, 165.0, 167.5, 170.0,
            172.5, 175.0, 177.5, 180.0, 182.5, 185.0, 187.5, 190.0, 192.5,
            195.0, 197.5, 200.0, 202.5, 205.0, 207.5, 210.0, 212.5, 215.0,
            217.5, 220.0, 222.5, 225.0, 227.5, 230.0, 232.5, 235.0, 237.5,
            240.0, 242.5, 245.0, 247.5, 250.0, 252.5, 255.0, 257.5, 260.0,
            262.5, 265.0, 267.5, 270.0, 272.5, 275.0, 277.5, 280.0, 282.5,
            285.0, 287.5, 290.0, 292.5, 295.0, 297.5, 300.0, 302.5, 305.0,
            307.5, 310.0, 312.5, 315.0, 317.5, 320.0, 322.5, 325.0, 327.5,
            330.0, 332.5, 335.0, 337.5, 340.0, 342.5, 345.0, 347.5, 350.0,
            352.5, 355.0, 357.5]

    lats = [-89.375, -87.5, -85.0, -82.5, -80.0, -77.5, -75.0, -72.5, -70.0,
            -67.5, -65.0, -62.5, -60.0, -57.5, -55.0, -52.5, -50.0, -47.5,
            -45.0, -42.5, -40.0, -37.5, -35.0, -32.5, -30.0, -27.5, -25.0,
            -22.5, -20.0, -17.5, -15.0, -12.5, -10.0, -7.5, -5.0, -2.5, 0.0,
            2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0, 27.5, 30.0,
            32.5, 35.0, 37.5, 40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5,
            60.0, 62.5, 65.0, 67.5, 70.0, 72.5, 75.0, 77.5, 80.0, 82.5, 85.0,
            87.5, 89.375]
        
    lons = numpy.array(lons)
    lats = numpy.array(lats)
    n = len(lons)
    results = []
    for lat in lats:
        for lon in lons:
            gridid,ilon,ilat = l2g(lon,lat,lons,lats)
            gridid2,ilon2,ilat2 = l2g2(lon,lat,lons,lats,n)
            if gridid-gridid2:
                print lat,lon
                print gridid,ilon,ilat 
                print gridid2,ilon2,ilat2
                print lon,(lon + 360.0)%360.0
                import sys; sys.exit("Stop Here")
#            results.append(gridid-gridid2)
#    print results

