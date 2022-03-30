def make_screen(jm,im,inv_wn,scale,row_start,row_end,ddlon,bot,top,dlat,dlon,
                start_lon,start_lat,faux_grids,meridional_tropical_debt,twopier,
                cos,radians,degrees,g2l,gcd):

     # This makes a screen on the zonal wavenumber by latitude and
     # each center (no matter it's latitude) uses the same screen
     # for each latitude.
     close_by = {}
     lat_spread = {}
     lat_rows = {}

     # Wavenumber (zonal, Nz) is roughtly the number of equally spaced and
     # sized lows around a given latitude circle. That is, a wavenumber
     # of 4 suggests 4 cyclone at that latitude at any given time. The
     # wavelenght of these waves changes with laitude and is inversely
     # related to the wavenumber (higher wavenumber less cyclones).
     #
     # Given that the model has a fixed number of longitude grids (columns)
     # the the number of columns is fixed by wavenumber. Such that for
     # anygiven latitude the same number of columns are needed to screen
     # by wavenumber.
     wavelength_z = im*inv_wn
     wavelength_z = wavelength_z + wavelength_z*scale
     ncols = (wavelength_z - 1)*0.5 # number of grids on each side
                                    # not counting center
     ncols = int(round(ncols,0))

#      print "scale",scale
#      print "inv_wn",inv_wn
#      print "wavelength_z",wavelength_z, im*inv_wn
#      print "ncols",ncols

     # Assume a zonal wave at 45 degrees
     circumference = twopier * cos(radians(45.0))
     # Nrows is determined by half the zonal wavelength, and half
     # on each side of center
     meridional_synoptic_cuttoff = (inv_wn*circumference + inv_wn*circumference*scale)*0.25
     nrows = int(round(meridional_synoptic_cuttoff/111.0)/degrees(dlat))

     # Latitude row/j boundry where tropical penalty felt, which means
     # some latitude dependence of ncols,nrows, and indeed, some asymmetry.
     # This will be reflected in the_screen.
     trop_penalty_bot = row_start.index(bot) - nrows
     trop_penalty_top = row_start.index(top-im+1) + nrows

     the_screen = {}
     top_row = jm - 1 # due to count starting at zero

     # Loop over all allows latitudes where a center can exist.
     for center_j in range(jm):
          matrix = []
          # Check to see if can just use ncols,nrows
          if center_j <= trop_penalty_bot:
               # Southern Hemisphere, outside tropical penalty
               center_top = center_j+nrows
               center_bot = center_j-nrows
               # Add columns
               for bottom_up in range(center_bot,center_top+1):
                    jlat = g2l(bottom_up,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                              edge_flag=True,center_flag="center",faux_grids=faux_grids)
                    if bottom_up < 0:
                         # polar wrap over, shift 180 degrees, same row
                         middle_pnt = row_start[-1*bottom_up] + im//2
                         matrix.extend(range(middle_pnt-ncols,middle_pnt+ncols+1))
                    else:
                         middle_pnt = row_start[bottom_up]
                         left = range(row_end[bottom_up]-ncols+1,row_end[bottom_up]+1)
                         right = range(middle_pnt,middle_pnt+ncols+1)
                         matrix.extend(left)
                         matrix.extend(right)
          elif center_j >= trop_penalty_top:
               # Northern Hemisphere, outside tropical penalty
               center_top = center_j+nrows
               center_bot = center_j-nrows
               # Add columns
               for bottom_up in range(center_bot,center_top+1):
                    if bottom_up > top_row:
                         # polar wrap over, shift 180 degrees, same row
                         jlat = g2l(top_row-(bottom_up-top_row),start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                                    edge_flag=True,center_flag="center",faux_grids=faux_grids)
                         # polar wrap over, shift 180 degrees, same row
                         middle_pnt = row_start[top_row-(bottom_up-top_row)] + im//2
                         matrix.extend(range(middle_pnt-ncols,middle_pnt+ncols+1))
                    else:
                        jlat = g2l(bottom_up,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                                   edge_flag=True,center_flag="center",faux_grids=faux_grids)
                        # polar wrap over, shift 180 degrees, same row
                        middle_pnt = row_start[bottom_up]
                        left = range(row_end[bottom_up]-ncols+1,row_end[bottom_up]+1)
                        right = range(middle_pnt,middle_pnt+ncols+1)
                        matrix.extend(left)
                        matrix.extend(right)
          else:
               # Possible region of tropical penalty, so need to find
               # distance to each included grid.

               # Apply a linear tropical penitally, which means a larger
               # dlon and dlat in the tropics.
               lat = g2l(center_j,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                         edge_flag=True,center_flag="center",faux_grids=faux_grids)
               center_lat = lat[1]

               # Maximum number of rows to check in each direction
               center_top = center_j+nrows
               center_bot = center_j-nrows
               # IF SH(NH) then southern(northern) part uses nrows,ncols
               if center_j <= row_start.index(bot):
                    # SH belows tropics, hence no penalty.
                    # Add columns
                    calculate = 0

                    for bottom_up in range(center_bot,center_top+1):
                         # Add SH part with tropical penalty, max possible equals nrows,ncols
                         if bottom_up > row_start.index(bot):
                              # Add SH part with tropical penalty, max possible equals nrows,ncols
                              jlat = g2l(bottom_up,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                                         edge_flag=True,center_flag="center",faux_grids=faux_grids)
                              dist = gcd(start_lon,jlat[1],start_lon,lat[1]) + meridional_tropical_debt[bottom_up]
                              # Use row until excedes cutoff
                              if dist <= meridional_synoptic_cuttoff:
                                   # See how many columns to use, find dlon at this latitude
                                   dlon_dist = gcd(start_lon,jlat[1],start_lon+ddlon,jlat[1])
                                   circumference = twopier * cos(radians(jlat[1]))
                                   zonal_synoptic_cuttoff = (inv_wn*circumference) - (10.0*meridional_tropical_debt[bottom_up])
                                   new_ncols = (zonal_synoptic_cuttoff*0.5)/dlon_dist
                                   new_ncols = int(round(new_ncols,0))
                                   middle_pnt = row_start[bottom_up]
                                   left = range(row_end[bottom_up]-new_ncols+1,row_end[bottom_up]+1)
                                   right = range(middle_pnt,middle_pnt+new_ncols+1)
                                   matrix.extend(left)
                                   matrix.extend(right)
                         else:
                              middle_pnt = row_start[bottom_up]
                              left = range(row_end[bottom_up]-ncols+1,row_end[bottom_up]+1)
                              right = range(middle_pnt,middle_pnt+ncols+1)
                              matrix.extend(left)
                              matrix.extend(right)
               elif center_j >= row_start.index(top-im+1):
                    # NH above tropics, hence no penalty.
                    # Add columns
                    for bottom_up in range(center_bot,center_top+1):
                         if bottom_up < row_start.index(top-im+1):
                              jlat = g2l(bottom_up,start_lon,start_lat,dlon,dlat,jm,lat_lon_flag="lat",
                                         edge_flag=True,center_flag="center",faux_grids=faux_grids)
                              dist = gcd(start_lon,jlat[1],start_lon,lat[1]) + meridional_tropical_debt[bottom_up]

                              # Use row until excedes cutoff
                              if dist <= meridional_synoptic_cuttoff:
                                   # See how many columns to use, find dlon at this latitude
                                   dlon_dist = gcd(start_lon,jlat[1],start_lon+ddlon,jlat[1])
                                   circumference = twopier * cos(radians(jlat[1]))
                                   zonal_synoptic_cuttoff = (inv_wn*circumference) - (10.0*meridional_tropical_debt[bottom_up])
                                   new_ncols = (zonal_synoptic_cuttoff*0.5)/dlon_dist
                                   new_ncols = int(round(new_ncols,0))
                                   middle_pnt = row_start[bottom_up]
                                   left = range(row_end[bottom_up]-new_ncols+1,row_end[bottom_up]+1)
                                   right = range(middle_pnt,middle_pnt+new_ncols+1)
                                   matrix.extend(left)
                                   matrix.extend(right)
                         else:
                              middle_pnt = row_start[bottom_up]
                              left = range(row_end[bottom_up]-ncols+1,row_end[bottom_up]+1)
                              right = range(middle_pnt,middle_pnt+ncols+1)
                              matrix.extend(left)
                              matrix.extend(right)
          the_screen[center_j] = matrix
     return the_screen
