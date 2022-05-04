"""This module runs all the setup routines to pre-calculate things for
the MCMS project.

#!/usr/bin/env python -tt
Options/Arguments:
    defs_set -- directory of options.
    imports -- list of modules to import.

Returns/Creates:

Examples:

Notes:

Author: Mike Bauer  <mbauer@giss.nasa.gov>

Log:
    2009/04  MB - File created.
"""

import sys,os
import math, numpy
import defines
import jj_calendar as jjCal

def setup_center_finder(defs,gcd,g2l,ij2grid,grid2ij,defs_grid):
    """Setup stuff for center_finder"""

    # Tunable parameters to warn that something might be wrong....
    #
    # min_centers_per_tstep: smallest number of center found per timestep
    #   before a warning or a halt of the center_finder is called. Generally
    #   20-40 centers found at any given time on whole planet.
    # max_centers_per_tstep: same as min_centers_per_tstep but for maximum number
    #   of centers.
    # max_centers_per_tstep_change: Maximum allowable timestep to timestep change
    #   in total center count.
    min_centers_per_tstep = 10
    max_centers_per_tstep = 60
    max_centers_per_tstep_change = 10

    #
    # Threshold for Laplacian Test below which center discarded as unlikely
    # to be cyclone.
    #
    lapp_cutoff = 0.15#0.4

    #
    # Threshold for the peak horizontal pressure gradient.
    # Holton says the horizontal pressure gradient is on the order of 0.01 hPa/km.
    #
    hpg_cutoff = 0.07

    # Find latitudes where all longitudes fit with critical_radius.
    use_all_lons = []
    search_radius = []
    regional_nys = []
    for row in range(jm):
        start = row_start[row]
        starti,startj = grid2ij(start,im,jm)
        startlon = g2l(starti,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                       edge_flag=False,center_flag="center",flag_360=True,
                      faux_grids = defs.faux_grids)
        startlat = g2l(startj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                       edge_flag=False,center_flag="center",
                       faux_grids = defs.faux_grids)
        end = row_end[row]
        endi,endj = grid2ij(end,im,jm)
        endlon = g2l(endi,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                     edge_flag=False,center_flag="center",flag_360=True,
                     faux_grids = defs.faux_grids)
        endlat = g2l(endj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                     edge_flag=False,center_flag="center",
                     faux_grids = defs.faux_grids)

        # Deal with cases of 89.99999
        startlon = round(startlon,2)
        startlat = round(startlat,2)
        endlon = round(endlon,2)
        endlat = round(endlat,2)

        distx = round(gcd(startlon,startlat,endlon,endlat),2)
        if defs.critical_radius > 0.0:
            tmp = defs.critical_radius
            search_radius.append(tmp)
        else:
            tmp = 0.5 * (2.0 * math.pi * defs.earth_radius *
                         math.cos(math.radians(startlat)) ) / float(defs.wavenumber)
            tmp = round(tmp,2)
            search_radius.append(tmp)

        # Circumference less than *fixed* critical_radius or grid spacing
        # effectively zero (i.e. centered on pole)
        #print "row %02d, distx(dx) %8.2f, tmp(radius) %8.2f, distx*im(circum) %8.2f" % (row,distx,tmp,distx*im)
        if distx*im <= tmp or distx <= 1.0:
            use_all_lons.append(row)

        # Maximum number of rows to check within critical_radius, minimum 1
        temp = int(round(tmp/111.0)/math.degrees(dlat))
        if temp < 1:
            temp = 1
        regional_nys.append(temp)
  
    """
    Define a gridid for every grid point on the entire
    model grid and then makes a dictionary with the 8
    grid points around gridid ... adapting for poles
    grid nomenclature

    upm     upc       upp     0 1 2
    cnm     cnt       cnp     3 4 5
    dnm     dnc       dnp     6 7 8

    Check: Counts will show that each point on map
    visited 9 times (once for each grid in the 9-pnt
    cell). The exceptions to this are in the polar rows
    because of wrap over more visits are possible.
    Specifically, the upper/lower most rows are visited
    only 6 times because 3 wrap over visits are put into
    the next row (down/up) so that the row before/after
    the upper/lower most rows is visited 12 times.

    Checked as correct for NCEP reanalysis grid.

    * For fixed critical_radius the pattern should be zonally symmetric
    with the count increasing rapidly toward the poles because the number
    grids within critical_radius increases with latitude and over-the
    pole wrap-around leads to multiple hits.

    * For wave-number the pattern should be the opposite as the number of
    search grids decreases with latitude. Thus the peak is around the
    equator.
    """

    gdict = {} # define dictionary of gridids
    rdict = {} # define dictionary of regional grids
    ldict = {} # define dictionary for laplacian calcuations
    ijdict = {} # define dictionary of i,j lon,lat for gridid

    for cnt in range(maxid):

        i,j = grid2ij(cnt,im,jm)
        lon = g2l(i,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                  edge_flag=False,center_flag="center",flag_360=True,
                  faux_grids = defs.faux_grids)
        lat = g2l(j,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                  edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)
        ijdict[cnt] = [i,j,lon,lat]

        lat = round(lat,2)
        lon = round(lon,2)
        # Laplacian in spherical coordinates (radians)
        #  LAP_P = 1/a^2 * d^2P/dlat^2 + 1/a^2sin^2(lat) * d^2P/dlon^2
        #          + cot(lat)/a^2 * dP/dlat
        rlat = math.radians(lat)
        temps = 0.5*(1.0+math.cos(rlat*2.0)) # equivulent sin^2(lat)
        part1 = 1
        # Note convert radius to m as pressure in Pa (kg/ms^2)
        if temps == 0.0:
            # Poles
            part1 = part2 = 0.0
        else:
            # 1/sin^2(lat) * 1/a^2
            part2 = 1.0/temps * (defs.inv_earth_radius_sq*0.0001)
        temps = math.tan(rlat)
        if temps == 0.0:
            # Equator
            part1 = part3 = 0.0
        else:
            #  cot(lat)/a^2
            part3 = 1.0/temps * (defs.inv_earth_radius_sq*0.0001)
        # Pre-calculated values for each grid
        # [1 if non-polar,1/sin^2(lat)*1/a^2,cot(lat)/a^2]

        ldict[cnt] = [part1,part2,part3]

        # Assign center grid offsets
        cnp = cnt + 1
        cnm = cnt - 1
        if cnt in row_end: # wrap
            cnp -= im
        if cnt in row_start: # wrap
            cnm += im

        upc = cnt + im
        dnc = cnt - im
        # Deal with polar rows
        if cnt < im:
            dnc = cnt + (im//2) + im
            if dnc > 2*im - 1:
                dnc -= im
        elif cnt > row_start[-1] - 1:
            upc = cnt + im//2 - im
            if upc > row_start[-1] - 1:
                upc -= im

        # Deal with Diagonals
        upm = upc - 1
        upp = upc + 1
        dnm = dnc - 1
        dnp = dnc + 1
        # Deal with polar rows
        if upc in row_start:
            upm = upc + im - 1
        if upc in row_end:
            upp -= im
        if dnc in row_start:
            dnm += im
        if dnc in row_end:
            dnp -= im
        # Push into dictionary
        gdict[cnt] = [upm,upc,upp,cnm,cnt,cnp,dnm,dnc,dnp]

        """
        Define a gridid for every grid point on the entire
        model grid and then makes a dictionary with all the
        points within a great circle radius of (critical_radius).
        """
        bylat = []
        bylat.append(int(cnt))

        # Find candidate grid centers by latitude
        goingy = 0
        polarity = 1
        check_here = cnt

        # Which latitude row is center in?
        for rowe in row_end:
            if check_here <= rowe:
                row = row_end.index(rowe)
                break

        # Search "up"
        while goingy < regional_nys[row]:
            cupc = check_here + polarity*im
            if check_here > row_start[-1] - 1 and polarity > 0: # upper polar
                polarity = -1 # wrap over
                cupc = check_here - (im // 2) + im
                if cupc > maxid - 1:
                    cupc -= im
                elif cupc > row_start[-1]:
                    cupc -= im
            bylat.append(int(cupc))
            check_here = cupc # shift search
            goingy += 1

        # Search "down"
        goingy = 0
        polarity = -1
        check_here = cnt
        while goingy < regional_nys[row]:
            dnpc = check_here + polarity*im
            if check_here < im and polarity < 0: # lower polar
                polarity *= -1 # wrap over
                dnpc = check_here + im + (im // 2)
                if dnpc > 2*im - 1:
                    dnpc -= im
                if dnpc < 0:
                    dnpc = abs(dnpc)
            bylat.append(int(dnpc))
            check_here = dnpc # sift search
            goingy += 1

        bylon = []

        for eachone in bylat:
            # Which latitude row is center in?
            for rowe in row_end:
                if eachone <= rowe:
                    row = row_end.index(rowe)
                    break

            if row in use_all_lons: # only keep 1st entry
                continue
                ## uncomment instead to keep all lons
                #for nextgrid in range(row_start[row],row_end[row]+1):
                #    if nextgrid not in bylon:
                #        bylon.append(int(nextgrid))
            else:
                # Check along "plus" longitude at this latitude
                nextgrid = eachone + 1
                polarity = 1
                newadds = 0
                distx = 0.0
                while distx < search_radius[row]:
                    if nextgrid > row_end[row]:
                        nextgrid -= im*polarity
                    nexti,nextj = grid2ij(nextgrid,im,jm)
                    tmplon = g2l(nexti,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                              edge_flag=False,center_flag="center",flag_360=True,
                              faux_grids = defs.faux_grids)
                    tmplat = g2l(nextj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                              edge_flag=False,center_flag="center",
                              faux_grids = defs.faux_grids)
                    distx = gcd(lon,lat,tmplon,tmplat)
                    if nextgrid not in bylon:
                        bylon.append(int(nextgrid))
                    newadds += 1
                    nextgrid += 1
                    if newadds >= im: # stop inf loops
                        distx = search_radius[row]
                bylon.pop()

                # Check along "minus" longitude at this latitude
                nextgrid = eachone  - 1
                polarity = -1
                newadds = 0
                distx = 0.0
                while distx < search_radius[row]:
                    if nextgrid < row_start[row]:
                        nextgrid -= im*polarity
                    nexti,nextj = grid2ij(nextgrid,im,jm)
                    tmplon = g2l(nexti,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                                 edge_flag=False,center_flag="center",flag_360=True,
                                 faux_grids = defs.faux_grids)
                    tmplat = g2l(nextj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                                 edge_flag=False,center_flag="center",
                                 faux_grids = defs.faux_grids)
                    distx = gcd(lon,lat,tmplon,tmplat)
                    if nextgrid not in bylon:
                        bylon.append(int(nextgrid))
                    newadds += 1
                    nextgrid -= 1
                    if newadds >= im: # stop inf loops
                        distx = search_radius[row]
                bylon.pop()

        # Merge center list
        regional = bylat
        for g in bylon:
            if g not in regional:
                regional.append(g)
        rdict[cnt] = regional
    #for row in range(jm):
    #    print row,lats[row],search_radius[row],regional_nys[row],len(rdict[row_start[row]])
    #sys.exit()
    return (use_all_lons,search_radius,regional_nys,gdict,rdict,ldict,ijdict,
            min_centers_per_tstep,max_centers_per_tstep,max_centers_per_tstep_change,
            lapp_cutoff,hpg_cutoff)

def setup_tracking(defs,gdict,gcd,g2l,ij2grid,grid2ij,defs_grid):

    """Setup stuff"""

    travel_distance = defs.max_cyclone_speed*timestep
    sin60 = math.sin(math.radians(60.0))

    # Find Latitude weighting function
    lwdict = {} # define dictionary of latitude weighting
    gridid = -1
    for each in lats:
        weight = 100.0
        # Deal with equator and division by zero.
        if abs(each) > 2.0:
            weight = sin60/(timestep*math.sin(math.radians(abs(each))))
        for j in range(im):
            gridid += 1
            lwdict[gridid] = weight

    # Calculate maximum absolute latitude for tracking... don't allow tracking
    # above latitude where a center could cross-over pole at maximum assumed
    # cyclone speed in 1 time step.
    if defs.polar_filter:
        polar_screen = [] # define list of polar screened gridids
        plon = 0.0
        polar_cross = defs.max_cyclone_speed*timestep
        for each in row_start:
            i,j = grid2ij(each,im,jm)
            lon = g2l(i,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                      edge_flag=False,center_flag="center",flag_360=True,
                      faux_grids = defs.faux_grids)
            lat = g2l(j,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                      edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)
            if lat < 0.0:
                plat = -90.0
            else:
                plat = 90.0
            distp = gcd(plon,plat,lon,lat)
            if distp <= polar_cross:
                gridid = each-1
                for jj in range(im):
                    gridid += 1
                    polar_screen.append(gridid)

    # Find latitudes where all longitudes fit within travel_distance. Not
    # the same as for center_finder as this is for reasonable cyclone movement
    # not reasonable low pressure proximity.
    use_all_lons = []
    regional_nys = []
    for row in range(jm):
        start = row_start[row]
        starti,startj = grid2ij(start,im,jm)
        startlon = g2l(starti,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                       edge_flag=False,center_flag="center",flag_360=True,
                       faux_grids = defs.faux_grids)
        startlat = g2l(startj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                       edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)

        end = row_end[row]
        endi,endj = grid2ij(end,im,jm)
        endlon = g2l(endi,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                  edge_flag=False,center_flag="center",flag_360=True,
                  faux_grids = defs.faux_grids)
        endlat = g2l(endj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                  edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)

        distx = gcd(startlon,startlat,endlon,endlat)

        # Circumference less than *fixed* travel_distance or grid spacing
        # effectively zero (i.e. centered on pole)
        if distx*im <= travel_distance or distx <= 1.0:
            use_all_lons.append(row)

        # Maximum number of rows to check within travel_distance, minimum 1
        temp = int(round(travel_distance/111.0)/math.degrees(dlat))
        if temp < 1:
            temp = 1
        regional_nys.append(temp)

    tdict = {} # define dictionary of travel_distance grids
    for cnt in range(maxid):

        upm,upc,upp,cnm,cnt,cnp,dnm,dnc,dnp = gdict[cnt]

        if defs.polar_filter:
            #if cnt in polar_screen: # total screen centers in polar
            #    tdict[cnt] = []
            #    continue
            if cnt in polar_screen: # limit to local-9 in polar
                tdict[cnt] = [cnp,cnm,cnt,upc,dnc,upm,upp,dnm,dnp]
                continue

        """
        Define a gridid for every grid point on the entire
        model grid and then makes a dictionary with all the
        points within a great circle radius of (travel_distance).
        """
        bylat = []
        bylat.append(int(cnt))

        # Find candidate grid centers by latitude
        goingy = 0
        polarity = 1
        check_here = cnt

        # which latitude row is center in?
        for rowe in row_end:
            if check_here <= rowe:
                row = row_end.index(rowe)
                break

        # Search "up"
        while goingy < regional_nys[row]:
            cupc = check_here + polarity*im
            if check_here > row_start[-1] - 1 and polarity > 0: # upper polar
                polarity = -1 # wrap over
                cupc = check_here - (im // 2) + im
                if cupc > maxid - 1:
                    cupc -= im
                elif cupc > row_start[-1]:
                    cupc -= im
            bylat.append(int(cupc))
            check_here = cupc # shift search
            goingy += 1

        # Seach "down"
        goingy = 0
        polarity = -1
        check_here = cnt
        while goingy < regional_nys[row]:
            dnpc = check_here + polarity*im
            if check_here < im and polarity < 0: # lower polar
                polarity *= -1 # wrap over
                dnpc = check_here + im + (im // 2)
                if dnpc > 2*im - 1:
                    dnpc -= im
                if dnpc < 0:
                    dnpc = abs(dnpc)
            bylat.append(int(dnpc))
            check_here = dnpc # sift search
            goingy += 1

        # Find candidate grid centers along longitude for each lat
        i,j = grid2ij(cnt,im,jm)
        lon = g2l(i,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                  edge_flag=False,center_flag="center",flag_360=True,
                  faux_grids = defs.faux_grids)
        lat = g2l(j,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                  edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)
        bylon = []

        for eachone in bylat:
            # which latitude row is center in?
            for rowe in row_end:
                if eachone <= rowe:
                    row = row_end.index(rowe)
                    break

            if row in use_all_lons: # only keep 1st entry
                continue
                ## uncomment instead to keep all lons
                #for nextgrid in range(row_start[row],row_end[row]+1):
                #   if nextgrid not in bylon:
                #       bylon.append(int(nextgrid))
            else:
                # check along "plus" longitude at this latitude
                nextgrid = eachone + 1
                polarity = 1
                newadds = 0
                distx = 0.0
                while distx < travel_distance:
                    if nextgrid > row_end[row]:
                        nextgrid -= im*polarity
                    nexti,nextj = grid2ij(nextgrid,im,jm)
                    tmplon = g2l(nexti,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                                 edge_flag=False,center_flag="center",flag_360=True,
                                 faux_grids = defs.faux_grids)
                    tmplat = g2l(nextj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                                 edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)
                    distx = gcd(lon,lat,tmplon,tmplat)
                    if nextgrid not in bylon:
                        bylon.append(int(nextgrid))
                    newadds += 1
                    nextgrid += 1
                    if newadds >= im: # stop inf loops
                        distx = travel_distance
                bylon.pop()

                # check along "minus" longitude at this latitude
                nextgrid = eachone  - 1
                polarity = -1
                newadds = 0
                distx = 0.0
                while distx < travel_distance:
                    if nextgrid < row_start[row]:
                        nextgrid -= im*polarity
                    nexti,nextj = grid2ij(nextgrid,im,jm)
                    tmplon = g2l(nexti,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lon",
                                 edge_flag=False,center_flag="center",flag_360=True,
                                 faux_grids = defs.faux_grids)
                    tmplat = g2l(nextj,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                                 edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)
                    distx = gcd(lon,lat,tmplon,tmplat)

                    if nextgrid not in bylon:
                        bylon.append(int(nextgrid))
                    newadds += 1
                    nextgrid -= 1
                    if newadds >= im: # stop inf loops
                        distx = travel_distance
                bylon.pop()

        # Merge center list
        regional = bylat
        for g in bylon:
            if g not in regional:
                regional.append(g)
        if defs.polar_filter:
            #for check in regional[:]: # total screen of regional in polar
            #    if check in polar_screen:
            #        regional.remove(check)
            temps = [cnp,cnm,cnt,upc,dnc,upm,upp,dnm,dnp]
            for check in regional[:]: # limit to local-9 regional in polar
                if check in polar_screen:
                    if check not in temps:
                        regional.remove(check)
        # populate dictionary
        tdict[cnt] = regional

    return tdict,lwdict

def setup_att(defs,gdict,gcd,g2l,ij2grid,grid2ij,
            grid_area,make_screen,rhumb_line_nav,defs_grid):
     """Setup stuff"""

     # Pre-bind and define.
     twopi = 2.0 * math.pi;cos = math.cos
     radians = math.radians; degrees = math.degrees
     twopier = twopi*defs.earth_radius
     rln = rhumb_line_nav

     gdict_new = {} # same as gdict but reordered.
     ijdict = {} # define dictionary of i,j lon,lat for gridID
     darea = {} # define dictionary of area for grid i

     top_lat = defs.tropical_boundary
     bot_lat = -1*top_lat

     # Find the area of each grid
     # NOTE only checked for regular grid!!
     multiplier = defs.earth_radius * defs.earth_radius * dlon

     distance_lookup = -1*numpy.ones((jm,maxid),numpy.int)
     angle_lookup = -1*numpy.ones((jm,maxid),numpy.int)

     # Apply a parabolic tropical penitally such that at ABS(30 lat) the
     # distance from the center is exaggerated such that a wavenumber
     # 4 search radius can't see equatorward of ABS(lat 12) degrees for a
     # center located at ABS(30 lat).
     force_constant = 0.0005
     meridional_tropical_debt = []
     distc = -1*dx*111.0

     #
     # Everything done relative to a single lon and all lats
     #
     for cnt in row_start:
          i,j = grid2ij(cnt,im,jm)
          lon = g2l(i,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                    edge_flag=False,center_flag="center",flag_360=True,
                    faux_grids = defs.faux_grids)
          lat = g2l(j,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                    edge_flag=False,center_flag="center",faux_grids = defs.faux_grids)

          # Loop over all grids finding distance/angle from central lon
          for pnt in range(maxid):

               # Skip current grid
               if pnt == cnt:
                    distance_lookup[j][pnt] = 0
                    angle_lookup[j][pnt] = 0
                    ii,jj = grid2ij(pnt,im,jm)
                    llat = g2l(jj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                               edge_flag=True,center_flag="center",faux_grids = defs.faux_grids)
                    darea[pnt] = grid_area(math,llat,multiplier)
                    continue

               # Calculate the distance/angle
               ii,jj = grid2ij(pnt,im,jm)
               llat = g2l(jj,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lat",
                          edge_flag=True,center_flag="center",faux_grids = defs.faux_grids)
               if cnt == 0:
                    darea[pnt] = grid_area(math,llat,multiplier)
               llat = llat[1]
               llon = g2l(ii,start_lon,start_lat,dlon,dlat,jm=jm,lat_lon_flag="lon",
                          edge_flag=False,center_flag="center",flag_360=True,
                          faux_grids = defs.faux_grids)

               fnc = []
               fnc = rln(llon,llat,lon,lat,True)
               if defs.use_gcd:
                    dist = gcd(llon,llat,lon,lat)
                    distance_lookup[j][pnt] = int(round(dist))
               else:
                    distance_lookup[j][pnt] = int(round(fnc[1]))
               # angle_lookup[j][pnt] = int(round(fnc[0]))

               ## JJJ fix angle lookup error that happens if the first value of fnc[0] is nan
               if math.isnan(fnc[0]):
                 angle_lookup[j][pnt] = angle_lookup[j-1][pnt]
               else:
                 angle_lookup[j][pnt] = int(round(fnc[0]))

          if bot_lat <= round(lat):
               if lat <= 0.0:
                    distc += dx*111.0
                    parab = force_constant*(distc*distc)
                    meridional_tropical_debt.append(round(parab))
               elif round(lat) <= top_lat:
                    distc -= dx*111.0
                    parab = force_constant*(distc*distc)
                    meridional_tropical_debt.append(round(parab))
               else:
                    meridional_tropical_debt.append(0.0)
          else:
               meridional_tropical_debt.append(0.0)

     scale_b = 0.50
     close_by = make_screen(jm,im,inv_wn,scale_b,row_start,row_end,dx,
                            bot,top,dlat,dlon,start_lon,start_lat,defs.faux_grids,
                            meridional_tropical_debt,twopier,cos,radians,
                            degrees,g2l,gcd)

     scale_a = 0.25
     if scale_a >= scale_b:
          # The search logic depends on the opposite condition!
          print ("Warning scale_a >= scale_b!")
     wander_test = make_screen(jm,im,inv_wn,scale_a,row_start,row_end,dx,bot,
                               top,dlat,dlon,start_lon,start_lat,defs.faux_grids,
                               meridional_tropical_debt,twopier,cos,radians,
                               degrees,g2l,gcd)

     scale_c = 0.25
     # Used to say a center is a potential stormy neighbor for another grid.
     # Set wavenumber at double input
     inv_wn1 = inv_wn * 0.5
     neighbor_test = make_screen(jm,im,inv_wn1,scale_c,row_start,row_end,dx,bot,
                                 top,dlat,dlon,start_lon,start_lat,defs.faux_grids,
                                 meridional_tropical_debt,twopier,cos,radians,
                                 degrees,g2l,gcd)

     #
     # Fill Moore Neighbor Lookup Table
     #
     for cnt in range(maxid):
         #    upm     upc       upp     0 1 2
         #    cnm     cnt       cnp     3 4 5
         #    dnm     dnc       dnp     6 7 8
         upm,upc,upp,cnm,cnt,cnp,dnm,dnc,dnp = gdict[cnt]
         # push into dictionary in different order.
         gdict_new[cnt] =  [upm,upc,upp,cnp,dnp,dnc,dnm,cnm,cnt]

     return(darea,distance_lookup,angle_lookup,close_by,wander_test,gdict_new,neighbor_test)

#---Start of main code block.
if __name__=='__main__':

    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}

    # Set to 1 if plots wanted and matplotlib available.
    save_plot = 1

    # If setup_vX.py executed with a file, redirect output to that file.
    #  e.g. python setup_v2.py /Volumes/scratch/output/logfile.txt
    keep_log = 0
    if len(sys.argv) > 1:
        keep_log = 1
    if keep_log:
        screenout  = sys.stdout
        log_file   = open(sys.argv[1], 'w',0)
        sys.stdout = log_file

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # Basic standard Python modules to import.
    imports = []
    system_imports = "import math,numpy, pickle"
    imports.append(system_imports)
    imports.append("import netCDF4 as NetCDF")

    # My modules to import w/ version number appended.
    my_base = ["defs","where_y","gcd","g2l","ij2grid","grid2ij",
               "rhumb_line_nav","first_last_lons","grid_area",
               "make_screen","print_col"]
    if save_plot:
        # Jeyavinoth: removed netcdftime from line below; in this case I just remove the line below
        # imports.append("import netcdftime")
        my_base.append("plot_map")
        my_base.append("pull_data")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)
    for i in imports:
        exec(i)

    # Pre_bind
    where_y = where_y.where_y
    gcd = gcd.gcd
    g2l = g2l.g2l
    ij2grid = ij2grid.ij2grid
    grid2ij = grid2ij.grid2ij
    rhumb_line_nav = rhumb_line_nav.rhumb_line_nav
    first_last_lons = first_last_lons.first_last_lons
    grid_area = grid_area.grid_area
    make_screen = make_screen.make_screen
    print_col = print_col.print_col
    if save_plot:
        Plot_Map = plot_map.plotmap

    # --------------------------------------------------------------------------
    # Start basic definitions of what is to be done.
    # --------------------------------------------------------------------------

    # If set to 1, then topography information will not be used to determine
    #  potentially troublesome locations for SLP dependent analysis. For
    #  example, regions of very high or steep topography can result in erroneous
    #  SLP values that either mimic or obscure cyclones. Generally, the
    #  results are better with no_topo set to 0.
    no_topo = 0

    # If set to 1, then the land_sea mask is not used to separate results
    #  that occur over land or ocean grids. This info is not required for
    #  full analysis. Note: the topography field can be used for this in
    #  a pinch.
    no_mask = 0

    model=defines.model
    
    # Full path to the directory where the SLP data files are stored.
    slp_source_directories = defines.slp_folder

    slp_path = slp_source_directories
    if not os.path.exists(slp_path):
        sys.exit("ERROR: slp_path not found.")

    # Full path to the root directory where output will be stored.
    # Note it's possible that all of these directories are identical.
    result_directory = defines.out_folder 
    if not os.path.exists(result_directory):
        sys.exit("ERROR: result_directory not found.")

    # Directory to be created for storing temporary model specific files.
    shared_path = "%s%s_files/" % (result_directory,model)

    # Directory to be created for storing model specific results.
    out_path = "%s%s/" % (result_directory,model)
    if not os.path.exists(out_path):
        dirs = list(map(os.makedirs, (out_path,
            out_path+'comps/',
            out_path+'pdfs/',
            out_path+'netcdfs/',
            out_path+'stats/',
            out_path+'figs/pdfs/',
            out_path+'figs/comps/')))
        print ("Directory %s Created." % (out_path))


    print ("Running Setup\n")
    print ("Using:")
    msg = "\tModel:\t\t %s\n\tOut_Path:\t%s\n\tShared_Dir:\t%s\n\tSLP_Path:\t%s"
    print (msg % (model,out_path,shared_path,slp_path))
    msg = "\tno_topo:\t%s\n\tno_mask:\t%s"
    print (msg % (bool(no_topo),bool(no_mask)))

    # --------------------------------------------------------------------------
    # Define the definitions to be read in.
    #
    # Hows how to alter a parameter in defs w/out having to alter the file
    # itself. Here I use setup_all as a flag to alter the defs so that all data
    # that can be precalculated and saved are, rather than the default which is
    # to read those data from file.
    # --------------------------------------------------------------------------

    # Select wavenumber for regional screens.
    wavenumbers = [4.0,8.0,13.0,26.0,52.0]

    # This value is used by center_finder_vX.py to screen for regional minima
    #  status. Generally, using too low wavenumbers means overly screening
    #  centers and too large values have little effect other than to
    #  make the analysis run longer. Good rule of thumb is 8-26.
    wavenumber = wavenumbers[2]

    # This value is used by attribute_vX.py to limit searches. This value
    #  should be lower wavenumber than wavenumber above. Basically this
    #  defines the largest system allowed. A good rule of thumb is 3-5.
    wavenumber_a = wavenumbers[0]

    # See defs_vX.py for what these variables represent.
    defs_set = {'tropical_boundary':15, "tropical_boundary_alt":30,
                "critical_radius":0.0,"polar_filter":False,
                "skip_polars":True,"wavenumber":wavenumber, "use_gcd":True}
    # match RAIBLE et. all 2007
    #defs_set = {'max_cyclone_speed': 42.0,'age_limit':72.0}

    # Fetch and update definitions. These are held in defs_vX.py
    defs = defs.defs(**defs_set)
    #######
    #defs.read_scale = 1.0  # I have made this change in defs_v4.py

    # Here we attempt read a sample of the SLP data in order
    #  to auto-configure some things such as the grid geometry
    #  for this model/data source. It is assumed that these
    #  files are netCDF files following the so called
    #  Climate and Forecast (CF) Metadata Convention
    #  (http://cf-pcmdi.llnl.gov/).
    #
    #  At a minimum this assumes that the files contain
    #  the latitude, longitude, time and SLP fields.
    #
    #  Here is an example header from the NCEP-DOE Reanalysis 2
    #  showing the expected output of ncdump -c file.nc
    #    ncdump -c mslp.2008.nc
    #    netcdf mslp.2008 {
    #    dimensions:
    #        lon = 144 ;
    #        lat = 73 ;
    #        time = UNLIMITED ; // (1464 currently)
    #    variables:
    #        float lat(lat) ;
    #            lat:units = "degrees_north" ;
    #            lat:actual_range = 90.f, -90.f ;
    #            lat:long_name = "Latitude" ;
    #            lat:standard_name = "latitude_north" ;
    #            lat:axis = "y" ;
    #            lat:coordinate_defines = "point" ;
    #        float lon(lon) ;
    #            lon:units = "degrees_east" ;
    #            lon:long_name = "Longitude" ;
    #            lon:actual_range = 0.f, 357.5f ;
    #            lon:standard_name = "longitude_east" ;
    #            lon:axis = "x" ;
    #            lon:coordinate_defines = "point" ;
    #        double time(time) ;
    #            time:units = "hours since 1800-1-1 00:00:0.0" ;
    #            time:long_name = "Time" ;
    #            time:actual_range = 1823280., 1832058. ;
    #            time:delta_t = "0000-00-00 06:00:00" ;
    #            time:standard_name = "time" ;
    #            time:axis = "t" ;
    #            time:coordinate_defines = "point" ;
    #        short mslp(time, lat, lon) ;
    #            mslp:long_name = "6-Hourly Mean Sea Level Pressure" ;
    #            mslp:valid_range = -32765s, 15235s ;
    #            mslp:unpacked_valid_range = 77000.f, 125000.f ;
    #            mslp:actual_range = 92980.f, 107630.f ;
    #            mslp:units = "Pascals" ;
    #            mslp:add_offset = 109765.f ;
    #            mslp:scale_factor = 1.f ;
    #            mslp:missing_value = 32766s ;
    #            mslp:_FillValue = -32767s ;
    #            mslp:precision = 0s ;
    #            mslp:least_significant_digit = -1s ;
    #            mslp:GRIB_id = 2s ;
    #            mslp:GRIB_name = "PRMSL" ;
    #            mslp:var_desc = "Mean Sea Level Pressure" ;
    #            mslp:dataset = "NCEP/DOE AMIP-II Reanalysis (Reanalysis-2)" ;
    #            mslp:level_desc = "Sea Level" ;
    #            mslp:statistic = "Individual Obs" ;
    #            mslp:parent_stat = "Other" ;
    #            mslp:standard_name = "pressure" ;
    #
    #    // global attributes:
    #            :Conventions = "CF-1.0" ;
    #            :title = "4x Daily NCEP/DOE Reanalysis 2" ;
    #            :history = "created 2009/03 by NOAA/ESRL/PSD" ;
    #            :comments = "Data is from \n",
    #                "NCEP/DOE AMIP-II Reanalysis (Reanalysis-2)\n",
    #                "(4x/day).  Data interpolated from model (sigma) surfaces to\n",
    #                "a rectangular grid." ;
    #            :platform = "Model" ;
    #            :source = "NCEP/DOE AMIP-II Reanalysis (Reanalysis-2) Model" ;
    #            :institution = "National Centers for Environmental Prediction" ;
    #            :references = "http://www.cpc.ncep.noaa.gov/products/wesley/reanalysis2/\n",
    #                "http://www.cdc.noaa.gov/data/gridded/data.ncep.reanalysis2.html" ;
    #    data:
    #
    #     lat = 90, 87.5, 85, 82.5, 80, 77.5, 75, 72.5, 70, 67.5, 65, 62.5, 60, 57.5,
    #        55, 52.5, 50, 47.5, 45, 42.5, 40, 37.5, 35, 32.5, 30, 27.5, 25, 22.5, 20,
    #        17.5, 15, 12.5, 10, 7.5, 5, 2.5, 0, -2.5, -5, -7.5, -10, -12.5, -15,
    #        -17.5, -20, -22.5, -25, -27.5, -30, -32.5, -35, -37.5, -40, -42.5, -45,
    #        -47.5, -50, -52.5, -55, -57.5, -60, -62.5, -65, -67.5, -70, -72.5, -75,
    #        -77.5, -80, -82.5, -85, -87.5, -90 ;
    #
    #     lon = 0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35,
    #        37.5, 40, 42.5, 45, 47.5, 50, 52.5, 55, 57.5, 60, 62.5, 65, 67.5, 70,
    #        72.5, 75, 77.5, 80, 82.5, 85, 87.5, 90, 92.5, 95, 97.5, 100, 102.5, 105,
    #        107.5, 110, 112.5, 115, 117.5, 120, 122.5, 125, 127.5, 130, 132.5, 135,
    #        137.5, 140, 142.5, 145, 147.5, 150, 152.5, 155, 157.5, 160, 162.5, 165,
    #        167.5, 170, 172.5, 175, 177.5, 180, 182.5, 185, 187.5, 190, 192.5, 195,
    #        197.5, 200, 202.5, 205, 207.5, 210, 212.5, 215, 217.5, 220, 222.5, 225,
    #        227.5, 230, 232.5, 235, 237.5, 240, 242.5, 245, 247.5, 250, 252.5, 255,
    #        257.5, 260, 262.5, 265, 267.5, 270, 272.5, 275, 277.5, 280, 282.5, 285,
    #        287.5, 290, 292.5, 295, 297.5, 300, 302.5, 305, 307.5, 310, 312.5, 315,
    #        317.5, 320, 322.5, 325, 327.5, 330, 332.5, 335, 337.5, 340, 342.5, 345,
    #        347.5, 350, 352.5, 355, 357.5 ;
    #
    #     time = 1823280, 1823286, 1823292, 1823298, 1823304, 1823310,
    #        1823316,                  ...                   1832058 ;
    #    }
    #
    #  It is not necessary that your data files be exactly like this.
    #  However, there are some basic requirements and also some
    #  conventions that will make your life easier if followed.
    #
    #  If your files differ from what is required you can modify
    #  pull_data_vX.py to accommodate your data, completely replace
    #  pull_data_vX.py to suit your data or modify your data.
    #
    #  Requirements:
    #  1) Files need 3 dimensions named by default lon,lat and time.
    #     If your files use these dimensions with different names
    #     you can alter these assumptions below.
    #  2) Files need 4 variables named by default lat, lon, time and slp.
    #  3) The variables lat, lon, time and slp have units of
    #     "degrees_north","degrees_east", "hours since ", and "Pascals"
    #     (or other unit that can be scaled to hPa) respectfully.
    #  4) The time dimension supports 2 calendars; "standard" and "noleap".
    #
    #  Conventions to make your work easier and faster:
    #  1) The SLP files are assumed to contain a single year's worth
    #     of data with the file name something like slp.1990.nc. On
    #     a practical note be aware that parallel processing works by
    #     spawning versions of the code each with parts of the data
    #     (i.e., different files) so that a single large data file
    #     precludes multiprocessing.
    #  2) The 1st latitude is assumed to start at the south pole, or
    #     at least to contain it. If not the case the code will auto
    #     flip the latitude and data arrays.
    #  3) The 1st longitude is assumed to start at the prime meridian,
    #     or at least to contain it. If not the case the code will
    #     auto rotate the longitude and data arrays.
    #  4) We assume regular lat-lon grids. Gaussian grids will work
    #     but with this assumption, or a version which accommodates
    #     Gaussian grids can be made (contact mbauer@giss.nasa.gov).
    #  5) Longitude is assumed to be in the 0-360 degree format. If
    #     using the +-180 degree format, the code will auto convert
    #     for you.
    #  6) It's best if the time variable has the attribute "delta_t".
    #     In any event, we assume constant time steps. Also, as a
    #     general rule cyclone tracking works best with time steps
    #     of 6 hours or less.

    # Data can be stored in one of three ways:
    # 
    #   pixel-registered (i.e. nodes centered on the grid boxes).
    #       The lon/lat points represent the center of the grid.
    #           Number of longitudes = (lon[-1]-lon[0])/dx
    #           Number of latitudes = (lat[-1]-lat[0])/dy
    #       Sometimes people store pixel-registered data but
    #       give the lon/lat as a grid edge/corner. This is done so that
    #       it is easy to see the data covers a full range. For
    #       example, the first grid might be centered on 88.75N 
    #       with a 2.5 spacing but the first longitude is 90N or the
    #       upper edge.
    #
    #   gridline-registered (i.e. nodes are at gridline intersections).
    #       The lon/lat points represent the edge of the grid (often the
    #       upper right hand corner).
    #           Number of longitudes = (lon[-1]-lon[0])/(dx+1)
    #           Number of latitudes = (lat[-1]-lat[0])/(dy+1)
    #
    #   point-registered (i.e. nodes point measurements. There are no grids).
    #       Here the data is sampled at the lon/lat points but do not
    #       represent grid-values. In this case some sort of interpolation
    #       can be used to fill in the grids or one can assume faux-grids
    #       based on the point spacing.
    #
    pixel_registered = []
    point_registered = defines.model
    gridline_registered = []
    all_registered = pixel_registered[:]
    all_registered.extend(point_registered)
    all_registered.extend(gridline_registered)

    # Assess the slp_path. Get a list of files and from the file
    # names get the time frame that the data cover; if this won't
    # work allow user to manually set years.

    # Determine years, if manually set use integers (i.e., 1989).
    # If using model results without 'years' just enumerate them
    # or if all data in a single large file use 1 (note no
    # multiprocessing in this case).
    #start_year = -1
    #end_year = -1
    start_year = defines.over_write_years[0] 
    end_year = defines.over_write_years[1]

    # What symbol separates file name.
    file_seperator = "."

    # Pull the list of available files, put in chronological order.
    print ("\nScanning %s for data files:" % (slp_path))
    file_list = os.listdir(slp_path)
    file_list = [x for x in file_list if x.find(".nc") != -1]
    file_list.sort()
    print_col(file_list,indent_tag="\t",fmt="%s",cols=6,width=10)

    # Loop over available files for correct years
    found_years = {}
    for infile in file_list:
        if infile.find(".nc") != -1:
            #print "Scanning File:",infile,
            # This works for filenames like slp.1998.nc
            year = infile.split(file_seperator)[1]
            found_years[year] = 1
    found_years = list(found_years.keys())
    found_years.sort()
    print ("\nFound_years:")
    print_col(found_years,indent_tag="\t",fmt="%s ",cols=10,width=10)

    if start_year == end_year == -1:
        start_year = found_years[0]
        end_year = found_years[-1]
    super_years =[start_year,end_year]

    print ("\nYear Bounds: [%s,%s]" % (super_years[0],super_years[1]))

    # Pull in the 1st data file to extract some information.
    #
    # Dimension & Variable Names: These can be changed if needed.
    dim_lat = "lat"
    dim_lon = "lon"
    dim_time = "time"
    var_lat = "lat"
    var_lon = "lon"
    var_time = "time"
    var_slp = "slp"
    var_topo = "hgt"
    var_land_sea_mask = var_topo


    # Test for extra files if requested.
    if not os.path.exists(shared_path):
        os.makedirs(shared_path)
        print ("Directory %s Created." % (shared_path))
        if no_topo and no_mask:
            print ("WARNING: Proceeding without topography or land_sea mask.")
        elif not no_topo and no_mask:
            print ("WARNING: Proceeding without land_sea mask.")
            print ("Copy topography file into %s and re-run setup." % (shared_path))
            sys.exit()
        elif no_topo and not no_mask:
            print ("WARNING: Proceeding without topography.")
            print ("Copy land_sea mask file into %s and re-run setup." % (shared_path))
            sys.exit()
        else:
            msg = "Copy the topography and land_sea mask files into %s and re-run setup."
            print (msg % (shared_path))
            msg = "This step can be skipped by setting no_topo and no_mask to 1 and re-running."
            sys.exit(msg)
    else:
        topo_file = "%s%s_%s.nc" % (shared_path,model,var_topo)
        # If no specific land/sea mask available the topo_file can be
        #  used to separate land as all grids with topography > sea_level.
        #  Do this by setting var_land_sea_mask = var_topo.
        mask_file = "%s%s_%s.nc" % (shared_path,model,var_land_sea_mask)
        if no_topo and no_mask:
            print ("WARNING: Proceeding without topography or land_sea mask.")
        elif not no_topo and no_mask:
            print ("WARNING: Proceeding without land_sea mask.")
            if not os.path.exists(topo_file):
                sys.exit("ERROR: %s not found." % (topo_file))
        elif no_topo and not no_mask:
            print ("WARNING: Proceeding without topography.")
            if not os.path.exists(mask_file):
                sys.exit("ERROR: %s not found." % (mask_file))
        else:
            if not os.path.exists(topo_file):
                sys.exit("ERROR: %s not found." % (topo_file))
            if not os.path.exists(mask_file):
                sys.exit("ERROR: %s not found." % (mask_file))
    
    # Open test file
    test_file = "%s%s" % (slp_path,file_list[0])
    #    print ("JJJ")
    print (test_file)
    nc_in = NetCDF.Dataset(test_file,'r',format='NETCDF3_CLASSIC')

    # Pull Time
    time = nc_in.variables[var_time]
    time = numpy.array(time[:],dtype=float,copy=1)
    tsteps = len(time)
    if 'calendar' in nc_in.variables[var_time].ncattrs():
        the_calendar = nc_in.variables[var_time].calendar
        the_calendar = the_calendar.lower()
    else:
        the_calendar = 'standard'
    if 'delta_t' in nc_in.variables[var_time].ncattrs():
        tmp = nc_in.variables[var_time].delta_t.split(':')
    else:
        print ("WARNING! netcdf file lacks delta_t', using 6hr default!")
        tmp = "0000-00-00 06:00:00".split(':')
    timestep = int(tmp[0][-2:])
    print ("\nTime Information:")
    print ("\tCalendar:\t%s" % (the_calendar))
    print ("\tTime steps:\t%d" % (tsteps))
    print ("\tTime step:\t%d" % (timestep))

    # Pull in Latitude
    lat = nc_in.variables[var_lat]
    lats = numpy.array(lat[:],dtype=float,copy=1)
    if lats[0] > lats[-1]:
        lat_flip = 1
        lats = lats[::-1]
    else:
        lat_flip = 0
    dy =  abs(lats[10]-lats[11])
    jm = len(lats)
    dlat = math.radians(dy)
    start_lat = lats[0]
    dlat_sq = dlat*dlat
    two_dlat = 2.0*dlat
    interval = dy*0.5
    edges = dict([(i+interval,1) for i in lats])
    edges.update([(i-interval,1) for i in lats])
    edges = list(edges.keys())
    edges.sort()
    lat_edges = edges
    
    # Make faux_grids based on point-registered data.
    faux_grids = 1
    defs.faux_grids = faux_grids  
    if lat_flip:
        lats = lats[::-1]
    # if faux_grids==1; % reminder JJJ
    edges = dict([(round(i+interval),1) for i in lats])
    edges.update([(round(i-interval),1) for i in lats])
    edges = list(edges.keys())
    edges.sort()
    edges.reverse()
    lat_edges = edges
    if lat_flip:
        lats = lats[::-1]
        
    print ("\tLatitude Flipped: %s" % (bool(lat_flip)))
    print ("\tLatitude Spacing: %g" % (dy))
    if defines.verbose:
        print ("\tLatitudes (jm = %d):" % (jm))
        print_col(list(lats),indent_tag="\t\t",fmt="% 7.2f",cols=5,width=10)
        print ("\tLatitudes Edges (%d):" % (len(lat_edges)))
        print_col(lat_edges,indent_tag="\t\t",fmt="% 7.2f",cols=5,width=10)

    # Pull in Longitude
    lon = nc_in.variables[var_lon]
    lons = numpy.array(lon[:],dtype=float,copy=1)
    # If lons in +-180 format shift to 360
    if numpy.any(numpy.less(lons,0.0)):
        tmp = numpy.where(lons < 0.0,numpy.add(lons,360.0),lons)
        lons = tmp
    dx = abs(lons[0]-lons[1])
    for lon_shift in range(len(lons)):
        left_edge = lons[lon_shift] - dx*0.5
        #if left_edge < 0.0:
        #    left_edge += 360.0
        right_edge = lons[lon_shift] + dx*0.5
        #if right_edge > 360.0:
        #    right_edge -= 360.0
        # Test where prime meridian is located
        if left_edge <= 0.0 < right_edge:
            break
    if lon_shift:
        lons = numpy.roll(lons,lon_shift)
    im = len(lons)
    dlon = math.radians(dx)
    start_lon = lons[0]
    dlon_sq = dlon*dlon
    interval = dx*0.5
    edges = dict([(i+interval,1) for i in lons])
    edges.update([(i-interval,1) for i in lons])
    edges = list(edges.keys())
    edges.sort()
    lon_edges = edges
    print ("\nLongitude Information:")
    print ("\tLongitude Rotated: %s (%d)" % (bool(lon_shift),lon_shift))
    print ("\tLongitude Spacing: %g degrees" % (dx))
    if defines.verbose:
        print ("\tLongitudes (im = %d):" % (im))
        print_col(list(lons),indent_tag="\t\t",fmt="% 7.2f",cols=5,width=10)
        print ("\tLongitude Edges (%d):" % (len(lon_edges)))
        print_col(lon_edges,indent_tag="\t\t",fmt="% 7.2f",cols=5,width=10)

    # Maximum number of gridIDs in model grid
    maxid = jm*im

    model_flag = "_%s_" % (model.upper())

    # Set some boundaries (latitude row)
    eq_grid = where_y(sys,list(lats),0.0,dy*0.5)
    defs.tropical_boundary=15.0
    tropical_s = where_y(sys,list(lats),-1*defs.tropical_boundary,dy*0.5)
    tropical_n = where_y(sys,list(lats),defs.tropical_boundary,dy*0.5)
    bot = ij2grid(tropical_s,0,im,jm)
    mid =  ij2grid(eq_grid,0,im,jm)
    top = ij2grid(tropical_n,im-1,im,jm)
    msg = "\nTropical_boundary:\t%d degrees\nTropical_n:\t\t%d %d (row,gridid)\nEQ_grid:\t\t%d %d (row,gridid)\nTropical_s:\t\t%d %d (row,gridid)"
    print (msg % (defs.tropical_boundary,tropical_n,top,eq_grid,mid,tropical_s,bot))
    
    defs.tropical_boundary_alt = -30.0
    tropical_s_alt = where_y(sys,list(lats),-1*defs.tropical_boundary_alt,dy*0.5)
    tropical_n_alt = where_y(sys,list(lats),defs.tropical_boundary_alt,dy*0.5)
    bot_alt = ij2grid(tropical_s_alt,0,im,jm)
    top_alt = ij2grid(tropical_n_alt,im-1,im,jm)
    msg = "\nTropical_boundary Alt:\t%d degrees\nTropical_n_alt:\t\t%d %d (row,gridid)\nEQ_grid:\t\t%d %d (row,gridid)\nTropical_s_alt:\t\t%d %d (row,gridid)"
    print (msg % (defs.tropical_boundary_alt,tropical_n_alt,top_alt,eq_grid,mid,tropical_s_alt,bot_alt))

    # Get gridids for 1st and last lon of each lat row.
    row_start,row_end = first_last_lons(jm,im)
    if defines.verbose:            
        print ("\nRow_start:")
        print_col(row_start,indent_tag="\t",fmt="% 6d",cols=10,width=10)
        print ("Row_end:")
        print_col(row_end,indent_tag="\t",fmt="% 6d",cols=10,width=10)

    # Set up some default values for the next set of routines
    defs_grid = {"im" : im, "jm" : jm, "maxid" : maxid, "lats" : lats,
                 "lons" : lons, "dx" : dx, "dy" : dy, "dlon" : dlon,
                 "dlat" : dlat, "dlon_sq" : dlon_sq, "dlat_sq" : dlat_sq,
                 "two_dlat" : two_dlat, "start_lat" : start_lat,
                 "start_lon" : start_lon, "model_flag" : model_flag,
                 "eq_grid" : eq_grid, "tropical_s" : tropical_s,
                 "tropical_n" : tropical_n, "bot" : bot,"top" : top,
                 "mid" : mid, "row_start" : row_start, "row_end" : row_end,
                 "timestep" : timestep, "tropical_s_alt" : tropical_s_alt,
                 "tropical_n_alt" : tropical_n_alt, "bot_alt" : bot_alt,
                 "top_alt" : top_alt, "lon_shift" : lon_shift,
                 "lat_flip" : lat_flip, "faux_grids" : faux_grids
                 }

    # Purpose: Create various things needed for center_finder and others.
    # Returns:
    #  use_all_lons - Latitude row where whole thing fits in critical_radius.
    #  search_radius - Defines Regional_Low radius by critical_radius or wavenumber.
    #  regional_nys - Maximum number or latitude rows to check based on critical_radius.
    #  gdict - Lookup table for local-8 grids by gridid.
    #  rdict - Lookup table for all grids fit within search_radius by gridid.
    #  ldict - Lookup table for Concavity/Laplacian Test.
    #  ijdict - Lookup table for i,j,lon,lat of a gridid.
    # Stores: cf_dat.p
    fnc_out = []
    args = (defs,gcd,g2l,ij2grid,grid2ij,defs_grid)
    print ("\nSetup Center_Finder...")
    fnc_out = setup_center_finder(*args)
    cf_file = "%scf_dat.p" % (shared_path)
    pickle.dump(fnc_out, open(cf_file, "wb",-1))
    print ("\tMade: %s\n" % (cf_file))
    # Re-read/test.
    #fnc_out = pickle.load(open(cf_file))
    (use_all_lons,search_radius,regional_nys, gdict,rdict,ldict,ijdict,
     min_centers_per_tstep,max_centers_per_tstep,max_centers_per_tstep_change,
     lapp_cutoff,hpg_cutoff) = fnc_out
    if save_plot:
        pname = "%s/%s_regional_radius_by_latitude.pdf" % (shared_path,model)
        plot = Plot_Map(missing=-1.0,color_scheme="gray_r",nocolorbar='nocolorbar',lon_0=0.0)
        plot.create_fig()
        blank = numpy.zeros(im*jm)
        #print "Row Latitude, Search Radius (km)   Approximate model Grids "
        tmp = [abs(180.0-lons[x]) for x in range(im)]
        center_lon = tmp.index(min(tmp))
        # Note these plots may seem offset in longitude due to how lons
        # breaks with a plot centered on 180.0 degrees. A similar problem
        # occurs in latitude so the polar most grids may look offset.
        for j in range(jm):
            #print j,lats[j],search_radius[j],search_radius[j]/(dx*111.0)
            for pnt in rdict[row_start[j]+center_lon]:
                # Just values along this latitude
                if pnt >= row_start[j] and pnt <= row_end[j]:
                    blank[pnt] = 1.0
        #plot.add_field(lons,lats,blank,ptype='pcolor')
        plot.add_field(lons,lats,blank,ptype='imshow')
        title = "Regional Radius At Each Latitude"
        plot.finish(pname,title=title)
        print ("\tMade figure %s" % (pname))
        pname = "%s/%s_regional_radius_full.pdf" % (shared_path,model)
        plot = Plot_Map(missing=-1.0,color_scheme="gray_r",nocolorbar='nocolorbar')
        plot.create_fig()
        blank = numpy.zeros(im*jm)
        # Note: the poleward and equatorward ends are not exactly
        # symmetrical because the fixed length search radius can
        # result in differing numbers of latitudes being reached as
        # of latitude spacing changes with latitude.
        for j in range(jm):
            interval = dy*0.5
            edge1 = lats[j]-interval
            edge2 = lats[j]+interval
            if edge1 <= -45.0 and edge2 >= -45.0:
                for pnt in rdict[row_start[j]+center_lon]:
                    blank[pnt] = 1.0
                break
        for j in range(jm):
            interval = dy*0.5
            edge1 = lats[j]-interval
            edge2 = lats[j]+interval
            if edge1 <= 45.0 and edge2 >= 45.0:
                for pnt in rdict[row_start[j]+center_lon]:
                    blank[pnt] = 1.0
                break
        #plot.add_field(lons,lats,blank,ptype='pcolor')
        plot.add_field(lons,lats,blank,ptype='imshow')
        title = u"Full Regional Search at 45\u00b0N/S"
        plot.finish(pname,title=title)
        print ("\tMade figure %s" % (pname))

    # Purpose: Locate grids for land-sea mask
    # Returns: lists of gridids used for optional screens.
    # Stores:
    if not no_mask:
        if mask_file == topo_file:
            if no_topo:
                # Topography screen disabled, but want
                # to use topo field to make mask.
                tfile = NetCDF.Dataset(topo_file,'r',format='NETCDF3_CLASSIC')
                topo = tfile.variables[var_topo]
                topo = numpy.array(topo[:],dtype=float,copy=1)
                if len(topo.shape) > 2:
                    # Assuming arranged as time,lat,long
                    topo = topo[0,:,:]
                if lat_flip:
                    tmp = topo[::-1,:]
                    topo = numpy.array(tmp) # ensures contiguous
                if lon_shift:
                    tmp = numpy.roll(topo,lon_shift,axis=1)
                    topo = numpy.array(tmp)
                tfile.close()
                topo.shape = im*jm
                # Use topo file to make land-sea mask
                #land_gridids = [x for x in range(maxid) if topo[x] > 0.0]
                land_gridids = [x for x in range(maxid) if topo[x] > defines.thresh_landsea_hgt]
            else:
                # Mask created below
                pass
        else:
            # Use provided mask file. Note it is assumed that land grids
            #   have a value of > 0. If not please make exception based
            #   on if pick:
            tfile = NetCDF.Dataset(mask_file,'r',format='NETCDF3_CLASSIC')
            mask = tfile.variables[var_land_sea_mask]
            mask = numpy.array(mask[:],dtype=float,copy=1)
            # Remove time dimension
            if len(mask.shape) > 2:
                # Assuming arranged as time,lat,long
                mask = mask[0,:,:]
            if lat_flip:
                tmp = mask[::-1,:]
                mask = numpy.array(tmp) # ensures contiguous
            if lon_shift:
                tmp = numpy.roll(mask,lon_shift,axis=1)
                mask = numpy.array(tmp)
            tfile.close()
            mask.shape = im*jm
            # Make land-sea mask
            land_gridids = [x for x in range(maxid) if mask[x] > defines.thresh_landsea_lsm]
            land_gridids.sort()

    # Purpose: Locate grids that fail the topography screen.
    # Returns: lists of gridids used for optional screens.
    # Stores:
    if not no_topo:
        print ("\nMaking Masks")
        tfile = NetCDF.Dataset(topo_file,'r',format='NETCDF3_CLASSIC')
        topo = tfile.variables[var_topo]
        topo = numpy.array(topo[:],dtype=float,copy=1)
        # Remove time dimension
        if len(topo.shape) > 2:
            # Assuming arranged as time,lat,long
            topo = topo[0,:,:]
        if lat_flip:
            tmp = topo[::-1,:]
            topo = numpy.array(tmp) # ensures contiguous
        if lon_shift:
            tmp = numpy.roll(topo,lon_shift,axis=1)
            topo = numpy.array(tmp)
        if 'add_offset' in tfile.variables[var_topo].ncattrs():
            offset = getattr(tfile.variables[var_topo],'add_offset')
            #print (" JJJ OFFSET")
            offset = 0.0
            print (offset)
        else:
            offset = 0.0
        if 'scale_factor' in tfile.variables[var_topo].ncattrs():
            scale_factor = getattr(tfile.variables[var_topo],'scale_factor')
            #print (" JJJ SCALE FACTOR HACK")
            scale_factor = 1.0
            print (scale_factor)
        else:
            scale_factor = 1.0
        ## Apply offset and scale_factor
        tmp = numpy.multiply(numpy.add(numpy.array(topo[:],dtype=float,copy=1)
                                       ,offset),scale_factor)
        topo = numpy.array(tmp)
        tfile.close()
        topo.shape = im*jm
        if mask_file == topo_file:
            # Use topo file to make land-sea mask
            land_gridids = [x for x in range(maxid) if topo[x] > 0.0]
            #JJJ - using non-zero for land-sea mask so that
            land_gridids = [x for x in range(maxid) if topo[x] > defines.thresh_landsea_hgt]

        # Troubled Grids: SLP away from sea level is a derived quantity.
        #   Certain conditions seem to allow for erroneous SLP values.
        #   These can hamper cyclone detection by mimicking or
        #   obscuring real cyclones. Here we create an optional list
        #   of grids that the scheme used to warn itself that the
        #   SLP values in these locations may not be reliable.
        #   Generally, we are skeptical of SLP values over high
        #   elevation (>= 1000m) or steep topography (average local
        #   relief > 150m) and in some cases land bound grids with
        #   sub-level elevations (deep basins). Note centers in these
        #   grids are not discarded out of hand, but rather, undergo
        #   extra tests during the analysis.

        # List all land or near land grids
        troubled_centers = []
        for gridid in range(maxid):
            # Skip grids where all 8 neighbors are ocean
            near_8 = gdict[gridid]
            land = [x for x in near_8 if x in land_gridids]
            if len(land) < 1:
                continue
            relief = [topo[x]-topo[gridid] for x in gdict[gridid]]
            ave_relief = sum(relief)/9.0
            if ave_relief >= 150:
                troubled_centers.append(gridid)
            elif topo[gridid] >= 1000:
                troubled_centers.append(gridid)

        # Add gridids that you specifically want screened, for
        #  example if you find you have a hotspot of center
        #  activity that you feel is erroneous due to say SLP
        #  reduction errors that are not caught by the above
        #  screen. Or if you want to discard all centers from
        #  a certain locale.
        grids_of_interest = []
        for gridid in grids_of_interest:
            if gridid not in troubled_centers:
                troubled_centers.append(gridid)

        troubled_centers.sort()

        if save_plot:
            pname = "%s/%s_topo.pdf" % (shared_path,model)
            plot = Plot_Map(clevs=[-500,4000,200],cints=[-500.0,4000.0],color_scheme='bone_r')
            #            plot = Plot_Map(clevs=[30000,40000,200],cints=[30000.0,40000.0],color_scheme='bone_r')
            center_loc = []
            plot.create_fig()
            plot.add_field(lons,lats,topo,ptype='pcolor')
            plot.finish(pname,title="Topography")
            print ("\tMade figure: %s" % (pname))

            if land_gridids:
                pname = "%s/%s_land_mask.pdf" % (shared_path,model)
                plot = Plot_Map(missing=-1.0,color_scheme="gray_r",nocolorbar='nocolorbar')
                plot.create_fig()
                center_loc = []
                for pnt in land_gridids:
                    i,j = grid2ij(pnt,im,jm)
                    latval = g2l(j,lons[0],lats[0],dlon,dlat,jm,"lat","center",False,False,defs.faux_grids)
                    lonval = g2l(i,lons[0],lats[0],dlon,dlat,jm,"lon","center",False,True,defs.faux_grids)
                    center_loc.append((lonval,latval))
                blank = numpy.zeros(im*jm)
                plot.add_field(lons,lats,blank,ptype='pcolor',)
                plot.add_pnts(center_loc,marker='o',msize=4,mfc='black',mec='black',lw=1.)
                title = "Land Mask"
                plot.finish(pname,title=title)
                print ("\tMade figure %s" % (pname))

            if troubled_centers:
                pname = "%s/%s_troubled_grids.pdf" % (shared_path,model)
                plot = Plot_Map(missing=-1.0,color_scheme="gray_r",nocolorbar='nocolorbar')
                plot.create_fig()
                center_loc = []
                for pnt in troubled_centers:
                    i,j = grid2ij(pnt,im,jm)
                    latval = g2l(j,lons[0],lats[0],dlon,dlat,jm,"lat","center",False,False,defs.faux_grids)
                    lonval = g2l(i,lons[0],lats[0],dlon,dlat,jm,"lon","center",False,True,defs.faux_grids)
                    center_loc.append((lonval,latval))
                blank = numpy.zeros(im*jm)
                plot.add_field(lons,lats,blank,ptype='pcolor',)
                plot.add_pnts(center_loc,marker='o',msize=4,mfc='black',mec='black',lw=1.)
                title = "Troubled Grids"
                plot.finish(pname,title=title)
                print ("\tMade figure %s" % (pname))
    # ---------------------------------
    # For Center_Finder, and others
    # ---------------------------------

    # Purpose: Store all the setup stuff I just imported.
    # Returns:
    # Stores: s_dat.p
    print ("\nStoring Setup Values...")
    fnc_out = (im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
               dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
               bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
               bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
               super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
               var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
               no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
               land_gridids,troubled_centers,faux_grids)
    sf_file = "%ss_dat.p" % (shared_path)
    pickle.dump(fnc_out, open(sf_file, "wb",-1))
    print ("\tMade: %s\n" % (sf_file))
    del fnc_out
    if save_plot:
        print ("\nTesting Pull_Data...")
        # Produce an example plot of the SLP field. Good idea to check
        # correctness with other software as this is how the data will
        # be read and used. Look for upside down or longitude shifts
        # in output.
        print (defs.read_scale)
        fnc = pull_data.pull_data(NetCDF,numpy,slp_path,file_seperator,
                int(super_years[0]),defs.read_scale,var_slp,var_time,
                lat_flip,lon_shift)
        (slp,times,the_time_units) = fnc
        del fnc

        print (slp[1])

        
        # Jeyavinoth
        # removed the way the original code computes date time 
        # wrote my own function for the calendar proceesing
        # function returns dtimes, date_stamps & adates
        # since the code below doesn't use adates or dtimes, I don't save those variables here
        # if needed use 
        # dtimes, date_stamps, adates = jjCal.get_time_info(the_time_units, times, calendar=the_calendar)
        # right now the code runs assuming it is "standarad" calendar
        # I started writing code for 'julian' calendar, but have to test this 
        # since adates is a different format output now, I change defs_v4.py to account for this (check comments in that file)
        defs.start_date_str = jjCal.get_start_date(the_time_units)
        _, date_stamps, _ = jjCal.get_time_info(the_time_units, times, calendar=the_calendar)

        # # Jeyavinoth: Commented code from here till "Jeyavinoth: End"
        # # Work with the time dimension a bit.
        # # This is set in setup_vX.py
        #
        # jd_fake = 0
        # if the_calendar != 'standard':
        #     # As no calendar detected assume non-standard
        #     jd_fake = 1
        # elif the_calendar == 'proleptic_gregorian':
        #     jd_fake = False
        # tsteps = len(times)
        # print (tsteps)
        # print (the_time_units)
        # the_time_range = [times[0],times[tsteps-1]]
        # start = "%s" % (the_time_units)
        # tmp = start.split()
        #
        # print ('JIMMY, here is tmp:')
        # print (tmp)
        # tmp1 = tmp[2].split("-")
        # tmp2 = tmp[3].split(":")
        #
        # print (tmp1 )
        # print (tmp2)
        # #tmp3 = tmp2[2][0]
        # tmp3 = 0
        # start = "%s %s %04d-%02d-%02d %02d:%02d:%02d" % \
        #         (tmp[0],tmp[1],int(tmp1[0]),int(tmp1[1]),\
        #          int(tmp1[2]),int(tmp2[0]),int(tmp2[1]),\
        #          int(tmp3))
        # print (start)
        # # Warning this could get weird for non-standard
        # # calendars if not set correctly (say to noleap)
        # # in setup_vX.py
        # cdftime = netcdftime.utime(start,calendar=the_calendar)
        # get_datetime = cdftime.num2date
        # dtimes = [get_datetime(times[step]) for step in range(0,tsteps)]
        #    
        # # Get Julian Days.. unless GCM uses non-standard calendar in which case
        # #  enumerate with timestep and use uci_stamps for datetime things.
        # if jd_fake:
        #     # Use timesteps rather than dates
        #     # examples '000000000', '000000001'
        #     adates = ["%09d" % (x) for x in range(tsteps)]
        # else:
        #     # Using regular date/times
        #     # examples 244460562, 244971850i
        #     date2jd = netcdftime.JulianDayFromDate
        #     adates = [int(100*date2jd(x,calendar='standard')) for x in dtimes]
        # date_stamps = ["%4d %02d %02d %02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]
        # print ("Start %s and End %s" % (date_stamps[0],date_stamps[-1]))
        # del times
        # del dtimes
        #
        # # Jeyavinoth: End

        # Plot an example to see if okay.
        plot = plot_map.plotmap(clevs=[960,1040,2],
                cints=[960.0,1040.0],color_scheme="jet")
        for step in range(tsteps):
            msg = "State at %s UTC" % (date_stamps[step])
            pname = "%s%s_example_slp_%s.pdf" % (shared_path,model,
                    date_stamps[step].replace(" ",""))
            plot.create_fig()
            slp_step = slp[step,:,:].copy()
            slp_step.shape = jm*im
#            plot.add_field(lons,lats,slp_step,ptype='pcolor')
            plot.add_field(lons,lats,slp_step,ptype='contour')
            plot.finish(pname,title=msg)
            print ("\tMade figure: %s" % (pname))
            # only make a single plot, for more comment break
            break
        del slp

    # Purpose: Create various things needed for tracking and others.
    # Returns:
    #   tdict - Lookup table for grids within a great circle radius of (travel_distance).
    #   lwdict - Lookup table for latitude weights to ?
    # Stores: tf_dat.p
    print ("\nSetup Track_Finder...")
    args = (defs,gdict,gcd,g2l,ij2grid,grid2ij,defs_grid)
    fnc_out = setup_tracking(*args)
    tf_file = "%stf_dat.p" % (shared_path)
    pickle.dump(fnc_out, open(tf_file, "wb",-1))
    print ("\tMade: %s\n" % (tf_file))
    # Uncomment to re-read/test.
    #fnc_out = pickle.load(open(tf_file))
    (tdict,lwdict) = fnc_out
    if save_plot:
        pname = "%s/%s_travel_distance_by_latitude.pdf" % (shared_path,model)
        plot = Plot_Map(missing=-1.0,color_scheme="gray_r",nocolorbar='nocolorbar',lon_0=0.0)
        plot.create_fig()
        blank = numpy.zeros(im*jm)
        tmp = [abs(180.0-lons[x]) for x in range(im)]
        center_lon = tmp.index(min(tmp))
        # Note these plots may seem offset in longitude due to how lons
        # breaks with a plot centered on 180.0 degrees.
        for j in range(jm):
           for pnt in tdict[row_start[j]+center_lon]:
                # Just values along this latitude
                if pnt >= row_start[j] and pnt <= row_end[j]:
                    blank[pnt] = 1.0
        #plot.add_field(lons,lats,blank,ptype='pcolor')
        plot.add_field(lons,lats,blank,ptype='imshow')
        title = "Travel Distance At Each Latitude"
        plot.finish(pname,title=title)
        print ("\tMade figure %s" % (pname))
        pname = "%s/%s_travel_distance_full.pdf" % (shared_path,model)
        plot = Plot_Map(missing=-1.0,color_scheme="gray_r",nocolorbar='nocolorbar')
        plot.create_fig()
        blank = numpy.zeros(im*jm)
        # Note: the poleward and equatorward ends are not exactly
        # symmetrical because the fixed length search radius can
        # result in differing numbers of latitudes being reached as
        # of latitude spacing changes with latitude.
        for j in range(jm):
            interval = dy*0.5
            edge1 = lats[j]-interval
            edge2 = lats[j]+interval
            if edge1 <= -45.0 and edge2 >= -45.0:
                for pnt in tdict[row_start[j]+center_lon]:
                    blank[pnt] = 1.0
                break
        for j in range(jm):
            interval = dy*0.5
            edge1 = lats[j]-interval
            edge2 = lats[j]+interval
            if edge1 <= 45.0 and edge2 >= 45.0:
                for pnt in tdict[row_start[j]+center_lon]:
                    blank[pnt] = 1.0
                break
        #plot.add_field(lons,lats,blank,ptype='pcolor')
        plot.add_field(lons,lats,blank,ptype='imshow')
        title = u"Full Travel Distance at 45\u00b0N/S"
        plot.finish(pname,title=title)
        print ("\tMade figure %s" % (pname))

    # Purpose: Create various things needed for attributing.
    # Returns:
    #   darea - Lookup table for area of each grid.
    #   distance_lookup - Lookup table for distance from grid to any another.
    #   angle_lookup -  Lookup table for angle from grid to any another.
    #   close_by - Lookup table based on zonal wavenumber to limit search area.
    #   wander_test - Like close_by by larger... to limit runaway searches.
    #   gdict_new - Same as gdict but reordered.
    # Stores: af_dat.p
    print ("\nSetup Attributed...")
    inv_wn = 1.0/float(wavenumber_a)
    args = (defs,gdict,gcd,g2l,ij2grid,grid2ij,
            grid_area,make_screen,rhumb_line_nav,defs_grid)
    fnc_out = setup_att(*args)
    af_file = "%saf_dat.p" % (shared_path)
    pickle.dump(fnc_out, open(af_file, "wb",-1))
    print ("\tMade: %s\n" % (af_file))
    # Uncomment to re-read/test.
    #fnc_out = pickle.load(open(af_file))
    (darea,distance_lookup,angle_lookup,close_by,wander_test,gdict_new,neighbor_test) = fnc_out

    if keep_log:
        # Redirect stdout back to screen
        log_file.close()
        sys.stdout = screenout
