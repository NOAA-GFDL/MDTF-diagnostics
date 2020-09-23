def first_last_lons(jm,im):
     """Get gridIDs for 1st lon of each lat"""
     row_start = [0]
     maxID = jm*im
     for gridID in range(maxID-1):
          test = gridID % im + 1
          if test == im:
               row_start.append(gridID+1)
     row_end = []
     for each in row_start:
          row_end.append(each+im-1)
     return row_start,row_end
