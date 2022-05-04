def g2l(double the_grid,double start_lon, double start_lat,
        double dlon, double dlat, int jm, lat_lon_flag, center_flag="center",
        edge_flag=False,flag_360=False,faux_grids=0):
        # Note dlat and dlon in RADIANS!
        cdef double location, edge1, edge2

        location = -999.0
        edge1    = -999.0
        edge2    = -990.0
        if lat_lon_flag == "lon" :
            # for regular and gaussian grids.
            if center_flag == "center" :
                # NOTE! the_grid needs to be the i,j not the gridID!
                location = start_lon + (int(the_grid)) \
                              * 57.2957795*(dlon)
            elif center_flag == "free" :
                # NOTE! the_grid needs to be the i,j not the gridID!
                location = start_lon + (the_grid) * \
                                57.2957795*(dlon)
            edge1 = location - 28.64788975*(dlon)
            edge2 = location + 28.64788975*(dlon)
            if edge1  < 0.0 :
                edge1 = 360.0 + edge1
            if edge2 > 360.0 :
                edge2 =  360.0 - edge2
            if(not flag_360) :
                if location > 180.0 :  # put into +/- form
                    location = location - 360.0
                if edge1 > 180.0 :
                    edge1 = edge1 - 360.0
                if edge2 > 180.0 :
                    edge2 = edge2 - 360.0

        elif lat_lon_flag == "lat" :
            # for regular grids (linear)
            if center_flag == "center" :
                # NOTE! the_grid needs to be the i,j not the gridID!
                location = start_lat + (int(the_grid)) * \
                              57.2957795*(dlat)
                # Deal with polar cap w/ faux_grids
                if faux_grids == 2:
                    if int(the_grid) == 0:
                        location = start_lat + 57.2957795*(dlat*0.25)  
                    if int(the_grid) == jm-1:
                        location = -1.0*start_lat - 57.2957795*(dlat*0.25)
            elif center_flag == "free":
                # NOTE! the_grid needs to be the i,j not the gridID!
                if faux_grids == 2:
                    if the_grid < 0.5:
                        location = start_lat + (
                                (the_grid+0.5)*57.2957795*(dlat*0.5))
                    if the_grid > float(jm)-1.5:
                        location = -1.0*start_lat - (
                                (float(jm)-the_grid-0.5)*57.2957795*(dlat*0.5))
                    else:
                        location = start_lat + (the_grid) * \
                                    57.2957795*(dlat)
                else:
                    location = start_lat + (the_grid) * \
                                57.2957795*(dlat)
            edge1 = location - 28.64788975*(dlat)
            edge2 = location + 28.64788975*(dlat)
            if faux_grids == 2:
                # Deal with polar cap w/ faux_grids 
                if the_grid < 1.0 or the_grid > float(jm)-2.0:
                    edge1 = location - 14.323944875*(dlat)
                    edge2 = location + 14.323944875*(dlat)
            if edge2 > 90.0:
                edge2 = edge1
            if edge1  < -90.0:
                edge1 = edge2

        if edge_flag :
            return edge2,location,edge1
        else :
            return location
