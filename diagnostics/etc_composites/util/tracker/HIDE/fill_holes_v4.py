def fill_holes(center_slices,collapse,gdict,rdict,row_start,row_end,im,jm,contours,offsets,neighbors):
    """
    Simple Idea:
        1) For each time step get list of centers and current SLP field
        2) For each center get list of used contours and regional grids:
        2a) screen SLP for regional and then for all SLPs > highest used
            contour for center. Screen out already captured grids as well.
            The remaining non-screened grids might be holes, but they have
            to be connectible to the center.
        3) Filled grids can't include center grids

        Note a slight issue with hole-fills in that they sometimes are
        lower SLP than any of the shared contours and so don't become
        ATTs but they are often far from any center and so you see small
        islands of ATTs embedded in stormy pixels. This is correct, but
        looks a little odd. Attempts have been made to minimize this.
    """

    collapsed_centers = {}
    collapse(collapsed_centers,center_slices)

    filled_holes = {}

    filled = {}

    # Get all current contours in use
    current_contours = sorted(contours,reverse=True)

    # Loop over each center
    for center in collapsed_centers:
##CUT
#        print "Doing center",center,len(collapsed_centers[center])

        # Skip 'empty' centers
        if not center_slices[center].keys():
##CUT
#            print "\tskipped empty"
            continue

        # Highest SLP already associated with center?
        cons = sorted(center_slices[center])
        peak = cons[-1]
##CUT
#        print "\tPeak SLP",peak

        # Get a limited search region
        row_start_index = row_start.index
        # Find lat row for center
        row_guess = [x for x in row_start if x <= center]
        row_guess = row_start_index(row_guess[-1])
        # Find the correct longitude offset from row_start
        lon_offset = center - row_start[row_guess]
        # Get regional screen for center's row
        if lon_offset != 0:
            # Cases where center in not in row_start
            # Need to shift whole screen over.
            reg_screen = []
            reg_screen_append = reg_screen.append
            for i in rdict[row_guess]:
                shifted = i + lon_offset
                # deal with wrap around
                row_guess_pnt = [x for x in row_start if x <= i]
                row_guess_pnt = row_start_index(row_guess_pnt[-1])
                if shifted > row_end[row_guess_pnt]:
                    shifted = shifted - im
                reg_screen_append(shifted)
        else:
            reg_screen = rdict[row_guess]
##CUT
#        print "\treg_screen (%d):" % (len(reg_screen))

        # Get all unique grids with SLP <= peak.
        n = dict((int(x),1) for y in cons for x in contours[y]).keys()

        # Cache all grids already harvested for this center
        grids_for_center = [int(x) for x in collapsed_centers[center]]

        # Screen reg_screen for grids already part of this center
        reg_screen = [int(x) for x in reg_screen if x not in grids_for_center]

        # Screen reg_screen for grids already associated with another center
        # because an embedded center will incorrectly appear to be a hole
        # to this center. We want to fill holes that do not have a center
        # within them.
        grid_pool = {}
        if neighbors[center]:
            grid_pool = dict( (int(x),1) for y in neighbors[center] for x in collapsed_centers[y])
        # Limit search grid to possbile fill grids
        reg_screen = [int(x) for x in reg_screen if x not in grid_pool]
        reg_screen = [x for x in reg_screen if x in n]

##CUT
# #        print "\tgrid_pool (%d) with %d other_centers" % (len(grid_pool),len(other_centers))
#         yellow_balls = []
# #        for c in reg_screen:
#         for c in grids_for_center:
#             yellow_balls.append((ijdict[c][2],ijdict[c][3]))
#         red_balls = []
# #        for c in grid_pool:
#         for c in reg_screen:
#             red_balls.append((ijdict[c][2],ijdict[c][3]))
#         big_cross = []
#         for c in neighbors[center]:
#             big_cross.append((ijdict[c][2],ijdict[c][3]))
#         small_dots = []
#         for c in grid_pool:
#             small_dots.append((ijdict[c][2],ijdict[c][3]))
#         msg = "edge_screen for Center %d" % (center)
#         mout = error_plot("%sfigs/plot_reg_%d.png" % (out_path,center),
#                           plot,slp,lons,lats,[(ijdict[center][2],ijdict[center][3])],
#                           yellow_balls,red_balls,big_cross,small_dots,msg)

        # Disallow grids outside of original edges. This prevents a problem
        # where reg_screen contains a contour outside the bounds of a center
        # but at lower SLP (i.e. a small hump in the slp field) which then
        # allows the hole to make the center larger (often much larger) than
        # before... a spill over of sorts.

#tmp rotate to test overrun
#         slide = 150
#         center = center + slide
#         aaa = []
#         bbb = []
#         for row in range(jm):
#             start = row_start[row]
#             end = row_end[row]
#             row_sweep = [x+slide for x in reg_screen if start <= x <= end]
#             row_sweep = [(x,start-1+(x-end)+im)[x>end] for x in row_sweep]
#             aaa.extend(row_sweep)

#             row_sweep = [x+slide for x in grids_for_center if start <= x <= end]
#             row_sweep = [(x,start-1+(x-end)+im)[x>end] for x in row_sweep]
#             bbb.extend(row_sweep)
#         reg_screen = aaa
#         grids_for_center = bbb

        # Shift everything to central longitude and equator.
#        lat_offset = row_guess - eq_grid
#        lon_offset = center - (row_start[row_guess]+im/2)
#        offset = (im*lat_offset) + lon_offset
        offset = offsets[center]
        center_off = center - offset
        reg_screen_off = [x-offset for x in reg_screen]
        grids_for_center_off = [x-offset for x in grids_for_center]

#         print "Doing center",center,
#         print "eq_grid",eq_grid,"center_lon",row_start[row_guess]+im/2
#         print "lon_offset,lat_offset",lon_offset,lat_offset
#         print "offset",offset

        # Find interior points
        edge = {}
        row_edges = {}
        interior = {}
        for row in range(jm):
            start = row_start[row]
            end = row_end[row]
            row_sweep = [x for x in grids_for_center_off if start <= x <= end]
            # Look for gaps
            nrow = len(row_sweep)
            if nrow > 1:
                row_sweep.sort()
                # Find edge of center by finding members with uncomplete
                # moore neighborhoods.
                row_edge = {}
                for xt in row_sweep:
                    hits = len([x for x in gdict[xt] if x in grids_for_center_off])
                    if hits < 9:
                        edge[xt] = 1
                        row_edge[xt] = 1
                    elif hits == 9:
                        edge[xt] = 1

                if row_edge:
                    t = sorted(row_edge.keys())
                    # Okay, find the outer edge values for each row. These are used to
                    # limit hole filling to the interior of the orginal object.
                    row_edges[row] = [t[0],t[-1]]
                    # Limit to only grids inside the bounds of the orginal object.
                    interior.update( dict((x,1) for x in range(t[0],t[-1]+1) if x in reg_screen_off))

#         print "final"
#         for row in sorted(row_edges):
#             print row,lats[row],row_edges[row],1+(row_edges[row][1]-row_edges[row][0]),row_start[row]+im/2
#         c_loc = []
# #         for c in edge:
# #             c_loc.append((ijdict[c][2],ijdict[c][3]))
#         a_loc = []
#         for c in interior:
#             a_loc.append((ijdict[c][2],ijdict[c][3]))
#         e_loc = []
# #        for c in grids_for_center:
#         for c in reg_screen:
#             e_loc.append((ijdict[c][2],ijdict[c][3]))
#         msg = "edge_screen for Center %d" % (center)
#         mout = error_plot("%sfigs/plot_edge_%d.png" % (out_path,center),
#                           plot,slp,lons,lats,[(ijdict[center][2],ijdict[center][3])],
#                           a_loc,c_loc,[],e_loc,msg)

        # If hole detected.... apply and recast back to where it belongs
        if interior:
            interior = [x+offset for x in interior]

            # Store hole fills
            filled_holes[center] = interior

            # Which contour does each hold grid belong too?
            for addon in interior:
#CUT
#                print "\tAdding",addon
                # contours containing addon (multiple if bridged)
                hits = [x for x in contours if addon in contours[x]]
                # Ensure contour less than highes SLP already on books.
                hits = [x for x in hits if x <= peak]
                hits.sort()
#CUT
#                print "\t\thits",hits

                for hit in hits:
                    if hit in center_slices[center]:
                        # Use pre-existing contour for center
#CUT
#                        print "\t\t\tPre-existing",hit,len(center_slices[center][hit]),
                        old = center_slices[center][hit]
                        old_append = old.append
                        # trim out duplicates
                        if addon not in old:
                            old_append(addon)
                        center_slices[center][hit] = old
#CUT
#                        print len(center_slices[center][hit])
                    else:
                        # Need to create a new contour for center
#CUT
#                        print "\t\t\tNew",hit,
                        center_slices[center][hit] = [addon]
#CUT
#                        print len(center_slices[center][hit])
        else:
            continue
#CUT
#         print len(interior)
#         print len(collapsed_centers[center])

#         c_loc = []
#         for c in collapsed_centers[center]:
#             c_loc.append((ijdict[c][2],ijdict[c][3]))
#         a_loc = []
#         collapsed_centers = {}
#         collapse(collapsed_centers,center_slices)
#         for c in collapsed_centers[center]:
#             a_loc.append((ijdict[c][2],ijdict[c][3]))
#         big_cross = []
#         for c in neighbors[center]:
#             big_cross.append((ijdict[c][2],ijdict[c][3]))
#         msg = "edge_screen for Center %d" % (center)
#         mout = error_plot("%sfigs/plot_fihole_%d.png" % (out_path,center),
#                           plot,slp,lons,lats,[(ijdict[center][2],ijdict[center][3])],
#                           a_loc,c_loc,big_cross,[],msg)

    return filled_holes

#-----------------------------

if __name__=='__main__':

    import sys,os,pickle


    # import arguments (use the following in the main code to save off an example)
#
#     args = (center_slices,collapse,gdict,wander_test,row_start,
#             row_end,im,contours)
#     # to test
#     pickle.dump(args,open("test.p", "wb",-1))
#     sys.exit()

#    tmp = pickle.load(open("/Volumes/scratch/output/test/test.p"))

#     filled = fill_holes(tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],tmp[7])
#     print filled
#     sys.exit("Stop HERE")

#     # Does a memory/time profile to find reason for slow downs etc.
#     import cProfile
#     msg = "fill_holes(tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],tmp[7])"
#     cProfile.run(msg,sort=1,filename="h.cprof")
#     import pstats
#     stats = pstats.Stats("h.cprof")
#     stats.strip_dirs().sort_stats('time').print_stats(20)

    center_slices = pickle.load(open("/Volumes/scratch/output/test/test0.p", 'rb'))
    collapse = pickle.load(open("/Volumes/scratch/output/test/test1.p", 'rb'))
    gdict = pickle.load(open("/Volumes/scratch/output/test/test2.p", 'rb'))
    wander_test = pickle.load(open("/Volumes/scratch/output/test/test3.p", 'rb'))
    row_start = pickle.load(open("/Volumes/scratch/output/test/test4.p", 'rb'))
    row_end = pickle.load(open("/Volumes/scratch/output/test/test5.p", 'rb'))
    im = pickle.load(open("/Volumes/scratch/output/test/test6.p", 'rb'))
    contours = pickle.load(open("/Volumes/scratch/output/test/test7.p", 'rb'))

    # Does a memory/time profile to find reason for slow downs etc.
    import cProfile
    msg = "fill_holes(center_slices,collapse,gdict,wander_test,row_start,row_end,im,contours)"
    cProfile.run(msg,sort=1,filename="h.cprof")
    import pstats
    stats = pstats.Stats("h.cprof")
    stats.strip_dirs().sort_stats('time').print_stats(20)


# orginal
# Tue May 26 17:31:27 2009    h.cprof

#          30459 function calls in 41.156 CPU seconds

#          Ordered by: internal time

#          ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#          1   41.101   41.101   41.156   41.156 fill_holes_v2.py:1(fill_holes)
#          14375    0.028    0.000    0.028    0.000 {method 'index' of 'list' objects}
#          342    0.017    0.000    0.017    0.000 {method 'union' of 'set' objects}
#          14356    0.003    0.000    0.003    0.000 {method 'append' of 'list' objects}
#          595    0.002    0.000    0.002    0.000 {built-in method fromkeys}
#          595    0.002    0.000    0.002    0.000 {method 'update' of 'dict' objects}
#          1    0.001    0.001    0.006    0.006 collapse_v2.py:1(collapse)
#          38    0.000    0.000    0.000    0.000 {method 'sort' of 'list' objects}
#          97    0.000    0.000    0.000    0.000 {method 'keys' of 'dict' objects}
#          1    0.000    0.000   41.156   41.156 <string>:1(<module>)
#          38    0.000    0.000    0.000    0.000 {len}
#          19    0.000    0.000    0.000    0.000 {method 'values' of 'dict' objects}
#          1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}

