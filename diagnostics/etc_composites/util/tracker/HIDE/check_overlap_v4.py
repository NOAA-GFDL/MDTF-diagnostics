def check_overlap(numpy,copy,envelope_test,current_contours,center_slices,
                  near_stormy,ijdict,slp,lons,lats,filled):
    """This function takes a list of current centers and their contours/grids
    and tests for shared contours/grids among the centers. This is ensured
    in the following manner.

    Rules:
    1) Work from the highest pressure downward to ensure the best solution.
    2) Drop all grids from all conflicted centers at pressures higher than
       the pressure of the first conflict ... ensures proper trimming.
    3) Drop all grids from all conflicted centers for the 1st shared contour.
    4) Always check that conflict(s) remain after any drops.
    5) If holes where filled previously for a center and that center has
       shared grids, then pass the holes to the shared grids else-wise the
       one time hole is likely to become an island; a patch of attributed
       grids with no direct connection of a center as the stormy grids
       surround it.

    Options/Arguments:
        numpy -- Module
        copy -- Module
        envelope_test -- Module
        current_contours -- List of centers for this timestep.
        center_slices -- Grids listed by contour for each center
                         in current_contours.
        near_stormy -- List of grids that are part of a shared contour.
                       Provides a list of the primary and secondary
                       centers that share this contour.
        ijdict -- Lookup table to convert grid locations to lon/lat etc.
        slp -- The data field in question.
        lons -- Array of longitudes for slp.
        lats -- Array of latitudes for slp.
        filled -- List of holes that where filled previously.

    Returns:
        near_stormy -- See above.
        backup -- updated copy of center_slices ... copy means can't
                  pass back as center_slices.

    Examples:

    Notes: When calling check_overlap reverse current_contours by using
           the [::-1] indexing so that search is done from high to low.

    Author: Mike Bauer  <mbauer@giss.nasa.gov>

    Log:
        2008/05  MB - File created.
        2008/10  MB - Added input checks, docstring.
        2008/10  MB - Fixed bug in how holes dealt with.
    """
    overlaps = {}
    # Loop over contours from high to low.
    for this_slice in current_contours:

         # List of all centers with this_slice
         peers = [x for x in center_slices.keys()
                  if center_slices[x].has_key(this_slice)]

         # Skip simple cases
         if len(peers) <= 1:
              continue

         # Check for overlapping centers with this slice
         # (i.e., centers with shared grids at this contour):
         overlapping_centers = {}
         checked_pair = []
         for this_center in peers:
              hits = envelope_test(numpy,this_center,peers,this_slice,
                                   center_slices,checked_pair,
                                   ijdict,slp,lons,lats)
              overlapping_centers.update({}.fromkeys(hits,1))

         # Track which centers overlap which centers, needed for attributed filled grids.
         # From here it's hard to know which centers to 'share' these filled grids. We
         # will share them will all the centers this center shared any grids with.

         overs = overlapping_centers.keys()
         for hit in overs:
              not_hit = [x for x in overs if x != hit]
              if hit in overlaps:
                   # Center already in overlaps
                   a = overlaps[hit]
                   not_here = [x for x in not_hit if x not in a]
                   a.extend(not_here)
                   overlaps[hit] = a
              else:
                   # Brand new entry
                   overlaps[hit] = not_hit

         # Remove this whole slice and all higher valued slices from
         # centers with conflicts. Move these to near_stormy.
         #
         # Loop over the overlapping centers.
         for conflicted_center in overlapping_centers:

              # All contours for this center at this_slice or
              # higher contour values.
              cut = [x for x in center_slices[conflicted_center].keys()
                     if x >= this_slice]

              # Remove these whole contours from center_slices and transfer
              # their grids to near_stormy.
              for takeout in cut:
                   for contested_grid in center_slices[conflicted_center][takeout]:
                        near_stormy[contested_grid] = overlapping_centers
                   del center_slices[conflicted_center][takeout]

    # Loop over all centers
    backup = copy.deepcopy(center_slices)
    for center in center_slices:
        #print "center",center

        # Was a hole filled in the center?
        if center in filled.keys():
            #print "\tWas filled",filled[center]

            # Does this center overlap any other centers?
            if center in overlaps.keys():
                #print "\t\tOverlaps",overlaps[center]

                # Add filled[center] to near_stormy, attribute to
                # center and centers it overlaps.
                tmp = {}
                tmp[center] = 1
                for overs in overlaps[center]:
                    tmp[overs] = 1
                for grid in filled[center]:
                    #print "\t\t\tAdding grid",grid
                    near_stormy[grid] = tmp

                # Loop over each these centers and remove filled grids, and
                # if necessary the whole slice if now empty.
                lloop = overlaps[center]
                lloop.append(center)
                for deep in lloop:
                    #print "\t\tChecking Deep",deep
                    for this_slice in center_slices[deep]:
                        #print "\t\t\tChecking slice",this_slice,
                        not_hits = [x for x in center_slices[deep][this_slice] if x not in filled[center]]
                        #print " not_hits",len(not_hits),len(center_slices[deep][this_slice])

                        # Remove filled grids from this_slice, if this_slice empty
                        # after, then remove this_slice altogether.
                        if len(not_hits) < 1:
                            # Remove slice
                            #print "\t\t\tCut Slice."
                            del backup[deep][this_slice]
                        elif len(not_hits) == len(center_slices[deep][this_slice]):
                            # No hits so leave alone
                            #print "\t\t\tLeave as is."
                            continue
                        else:
                            # Only keep not_hits
                            #print "\t\t\t\tHits",[x for x in center_slices[deep][this_slice] if x in filled[center]]
                            backup[deep][this_slice] = not_hits
    # Update
    return (backup)
