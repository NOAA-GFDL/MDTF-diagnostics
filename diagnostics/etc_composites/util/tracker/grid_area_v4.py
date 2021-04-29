def grid_area(math,the_grid,multiplier):
     """Define the area of a grid.
     Assumes an regular-grid for now ... perhaps with polar cap.
     """
     # NOTE only checked for regular grid!!

     # Polar cap?
     if the_grid[0] == the_grid[2]:
          if the_grid[0] < the_grid[1]:
               # N Hemi
               bot_lat = the_grid[0]
               top_lat = the_grid[1]
          else:
               # S Hemi
               bot_lat = the_grid[1]
               top_lat = the_grid[0]
     else:
          if the_grid[0] < the_grid[2]:
               # N Hemi
               bot_lat = the_grid[0]
               top_lat = the_grid[2]
          else:
               # S Hemi
               bot_lat = the_grid[2]
               top_lat = the_grid[0]
     # Find area
     area = abs(multiplier *
                (math.sin(math.radians(bot_lat)) -
                 math.sin(math.radians(top_lat))))
     return area
