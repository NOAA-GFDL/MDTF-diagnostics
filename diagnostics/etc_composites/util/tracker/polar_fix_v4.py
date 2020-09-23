def c_partition(pp):
    # Find the minimum SLP
    mins = [x[1] for x in pp]
    mins.sort()
    mins = mins[0]

    # Find the gridIDs with mins (may be multiple)
    # because in a single longitude we can just use
    # the median gridID as the "central" grid if
    # multiple grids with mins.
    cmins = [x[0] for x in pp if x[1] == mins]
    cmins.sort()

    # Partition cmins into contiguous grids.
    groups = {}
    # 1st value always a group
    groups[0] = [cmins[0]]
    last = 0
    # JIMMY, I added an if statement on the len of cmins equal to 1, b/c otherwise I 
    # was getting an error with no value assigned to new_pp.
    #print len(cmins)
    if len(cmins) == 1:
        pick = cmins[0]
        new_pp = [] 
        new_pp.append(pick) 
        #        print "hello"
    else:
        for x in range(1,len(cmins)):
            diff = abs(cmins[x-1]-cmins[x])
            if diff == 1:
                # Add to existing group
                d = groups[last]
                d.append(cmins[x])
                groups[last] = d
            else:
                # Create new group
                last = x
                groups[x] = [cmins[x]]
                
            # Find Median grid(s)
            new_pp = []
            for x in groups:
                n = len(groups[x])
                if n & 1: # odd number
                    pick = groups[x][n // 2]
                else:
                    pick = (groups[x][n // 2 - 1] + groups[x][n // 2]) // 2
                new_pp.append(pick)

    return new_pp

def polar_fix(use_all_lons,kept_centers,row_end):
    """Fix problem of too many centers, due to ties, at poles.
    """
    poleless = []
    s_polar = []
    n_polar = []
    poleless_append = poleless.append
    s_polar_append = s_polar.append
    n_polar_append = n_polar.append

    # Split use_all_lons into 2 equal parts (NH,SH)
    dd = len(use_all_lons)//2
    need_pole_row = []
    need_pole_row_append = need_pole_row.append
    for row in use_all_lons: # keep track of rows used
        need_pole_row_append(1)
    for g in kept_centers:
        for rowe in row_end:
            if g[0] <= rowe:
                row = row_end.index(rowe)
                break
        if row in use_all_lons[:dd]:
            s_polar_append(g)
        elif  row in use_all_lons[dd:]:
            n_polar_append(g)
        elif g not in poleless:
            poleless_append(g)
        else:
            import sys
            sys.exit("Error in polar filter")

   # For each pole retain the center with the lowest center
    # pressure... if ties then average location.
    if len(s_polar):
        new_polar = c_partition(s_polar)
        # Add any grids
        for p in new_polar:
            poleless_append([x for x in kept_centers if x[0] == p][0])

    if len(n_polar):
        #JIMMY
        #print n_polar
        new_polar = c_partition(n_polar)
        #JIMMY
        #print new_polar
        # Add any grids
        for p in new_polar:
            poleless_append([x for x in kept_centers if x[0] == p][0])

    # log discard for discards
    dumped = [x for x in kept_centers if x not in poleless]

#     print "kept_centers"
#     for e in kept_centers:
#         print e
#     print "poleless"
#     for e in poleless:
#         print e
#     print "dumped"
#     for e in dumped:
#         print e
#     sys.exit()

    # Check
    if len(poleless)+len(dumped) != len(kept_centers):
        import sys
        sys.exit("Error in polar_fix")

    return poleless,dumped

if __name__=='__main__':

    use_all_lons = [0, 72]

    # set with no issues
#    kept_centers = [(542, 977300, 300, 11000, 977969, 1533, 0), (710, 977800, 400, 13400, 979031, 1733, 0), (804, 960200, 500, 8400, 961671, 1231, 0), (805, 960200, 500, 8500, 961828, 1204, 0), (1129, 965000, 700, 12100, 969734, 1667, 0), (1358, 974200, 900, 6200, 980428, 1616, 0), (1455, 956300, 1000, 1500, 965156, 1727, 0), (1514, 956700, 1000, 7400, 967460, 2640, 0), (1570, 968700, 1000, 13000, 973070, 766, 0), (1633, 967600, 1100, 4900, 975716, 1502, 0), (1761, 957300, 1200, 3300, 967217, 1845, 0), (3319, 1011300, 2300, 700, 1017794, 634, 0), (7317, 1005700, 5000, 11700, 1018754, 1422, 0), (7841, 1000600, 5400, 6500, 1012826, 1427, 0), (7970, 1017500, 5500, 5000, 1026146, 1021, 0), (7971, 1017500, 5500, 5100, 1025738, 1047, 0), (8115, 1017500, 5600, 5100, 1024903, 1295, 0), (8436, 971200, 5800, 8400, 987119, 2065, 0), (8713, 972900, 6000, 7300, 984857, 2638, 0), (8740, 991500, 6000, 10000, 998937, 1509, 0), (8916, 996200, 6100, 13200, 1007151, 1856, 0), (8932, 957000, 6200, 400, 969353, 2413, 0), (8933, 957000, 6200, 500, 967624, 1708, 0), (9237, 967000, 6400, 2100, 973361, 1596, 0), (9371, 966600, 6500, 1100, 969855, 814, 0), (9617, 1008200, 6600, 11300, 1010852, 867, 0), (9755, 1008700, 6700, 10700, 1010347, 605, 0), (10048, 1008500, 6900, 11200, 1009392, 636, 0), (10049, 1008500, 6900, 11300, 1009369, 1274, 0), (10050, 1008500, 6900, 11400, 1009446, 1188, 0), (10202, 1009500, 7000, 12200, 1010015, 1021, 0), (10203, 1009500, 7000, 12300, 1010000, 858, 0), (10204, 1009500, 7000, 12400, 1010015, 909, 0)]

    # set with polar issues
    kept_centers = [(544, 978300, 300, 11200, 979292, 2191, 0), (654, 962100, 400, 7800, 963521, 743, 0), (655, 962100, 400, 7900, 963594, 803, 0), (709, 979400, 400, 13300, 980442, 1595, 0), (1129, 966800, 700, 12100, 971962, 1984, 0), (1214, 970500, 800, 6200, 975202, 404, 0), (1252, 973800, 800, 10000, 978482, 1055, 0), (1456, 960600, 1000, 1600, 968658, 1430, 0), (1491, 963800, 1000, 5100, 971319, 1491, 0), (1515, 956600, 1000, 7500, 967153, 2726, 0), (1717, 969100, 1100, 13300, 973865, 885, 0), (1718, 969100, 1100, 13400, 973560, 795, 0), (1764, 959200, 1200, 3600, 965986, 1030, 0), (3319, 1012200, 2300, 700, 1018100, 614, 0), (7462, 995000, 5100, 11800, 1015929, 2133, 0), (7973, 1015400, 5500, 5300, 1024335, 1067, 0), (7987, 991700, 5500, 6700, 1007912, 2069, 0), (8581, 965500, 5900, 8500, 981574, 2949, 0), (8713, 978300, 6000, 7300, 988702, 2292, 0), (8742, 989400, 6000, 10200, 997384, 1673, 0), (8794, 957000, 6100, 1000, 969593, 2269, 0), (8937, 957000, 6200, 900, 965602, 1109, 0), (9062, 993800, 6200, 13400, 1001912, 1888, 0), (9193, 1012800, 6300, 12100, 1017246, 893, 0), (9340, 1012600, 6400, 12400, 1019751, 3477, 0), (9372, 966500, 6500, 1200, 968831, 617, 0), (9373, 966500, 6500, 1300, 968472, 580, 0), (9378, 965600, 6500, 1800, 968110, 899, 0), (9379, 965600, 6500, 1900, 968444, 1098, 0), (9616, 1010000, 6600, 11200, 1012052, 648, 0), (9617, 1010000, 6600, 11300, 1012144, 684, 0), (9754, 1009300, 6700, 10600, 1011538, 1040, 0), (9755, 1009300, 6700, 10700, 1011128, 799, 0), (10049, 1011400, 6900, 11300, 1012046, 469, 0), (10431, 1008500, 7200, 6300, 1009033, 469, 0), (10432, 1008500, 7200, 6400, 1009033, 469, 0), (10433, 1008500, 7200, 6500, 1009066, 469, 0), (10434, 1008500, 7200, 6600, 1009100, 469, 0), (10435, 1008500, 7200, 6700, 1009133, 469, 0), (10503, 1008500, 7200, 13500, 1008866, 469, 0), (10504, 1008500, 7200, 13600, 1008766, 469, 0), (10505, 1008500, 7200, 13700, 1008700, 469, 0), (10506, 1008500, 7200, 13800, 1008633, 469, 0), (10507, 1008500, 7200, 13900, 1008566, 469, 0)]

    row_end = [143, 287, 431, 575, 719, 863, 1007, 1151, 1295, 1439, 1583, 1727, 1871, 2015, 2159, 2303, 2447, 2591, 2735, 2879, 3023, 3167, 3311, 3455, 3599, 3743, 3887, 4031, 4175, 4319, 4463, 4607, 4751, 4895, 5039, 5183, 5327, 5471, 5615, 5759, 5903, 6047, 6191, 6335, 6479, 6623, 6767, 6911, 7055, 7199, 7343, 7487, 7631, 7775, 7919, 8063, 8207, 8351, 8495, 8639, 8783, 8927, 9071, 9215, 9359, 9503, 9647, 9791, 9935, 10079, 10223, 10367, 10511]

    print ("Start",len(kept_centers))
    kept_centers,discards = polar_fix(use_all_lons,kept_centers,row_end) 
    print ("End",len(kept_centers))
