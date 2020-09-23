""" This module processes a continuous data set (e.g., SLP)
    by applying a contouring algorithm and using that output
    to define a set of contour objects (putative cyclones) of
    closed isobars around low pressure areas. These are then
    stored for for future linking to tracked cyclones.
#!/usr/bin/env python -tt

    Inputs:

        field : 2d (lat,lon) numpy array of data to be processed.
        lons  : 1d numpy array of longitudes.
        lats  : 1d numpy array of latitudes.
        levels : 1d numpy array of the contours to be checked.
        m_map : basemap instance of a map projection.
        hemi :hemisphere being done
                hemi = 0 global (requires global map projection)
                     = 1 Northern Hemisphere
                     = 2 Southern Hemisphere
        bounding_lat : Equatorward most contours allowed (degrees)
        spanning_grids_e : * see Note 1
        spanning_grids_w : * see Note 1
        date_line : * see Note 2

    Note 1: The contouring program currently being used
            matplotlib version 0.99.0
            matplotlib-basemap 0.99.4
            has the limitation that contour lines crossing
            the international dateline are broken into
            separate parts. Thus steps are needed to
            be sure contours are reassembled for our
            use. spanning_grids_ e and w are the gridids
            for field that are w/in a user set closeness
            to the dateline (we use 10 grids on each side.
            This is for the contour fill.
    Note 2: Same issue as Note 1 but only need the griddids
            one on each side of the dateline. This is for
            the contour merge.

    2010/6 MB - File created.

"""
def isolate_contour_objects(contours,m_map,levels,contour_limit,PL,
        plot_contours,verbose):
    """Use matplotlib's contour package to extract and isolate individual
        closed contours, screen them by size, tropicalness.
    """
    #if verbose:
    #    hemis = ["Northern","Southern"]
    #    bt = 1
    #    msg0 = "\n%sDoing %s Hemisphere"
    #    msg0a = "\n%sDoing Level (%d) w/ %d initial paths"
    #    msg0b = "%s%s\n"
    #    msg1 = "\n%sRetained %d paths after 1st pass"
    #    msg1a = "%sPath_id: %d Vertex Count %d"
    #    msg2 = "%sPath_id: %d Forced Polar Closure"
    #    msg2a = "%sPath_id: %d Forced Close Closure"
    #    msg2b = "%sPath_id: %d Discarded for Lack of Closure"
    #    msg3 = "%sPath_id: %d Dropped Tropical"
    #    msg3a = "%sPath_id: %d Deep Tropical"
    #    msg4 = "%sPath_id: %d Big Contour"
    #    msg4a = "%sPath_id: %d Tiny Contour"
    #    msg6  = "%sPath_ids: %d and %d Merge Drop"
    #    msg6a  = "%sPath_ids: %d and %d Merge"
    #    msg7 = "%sPath_ids: %s %s"
    #    mgs8 = "%sTesting %s for High Pressure"
    #    msg8a = "%sTest Point: %s"
    #    msg8b = "%sSorted Canidates:"
    #    msg8c = "%sTesting Against: %s"
    #    msg8e = "%sDropping these High Pressure Systems:"
    #    msg8f = "%sInside:"

    h_lookup = ["nh","sh"]
    c_objects = {}
    c_lengths = {}
    c_paths = {}
    for hemi in range(2):
        #if verbose:
        #    print msg0  % ("\t"*(bt+0),hemis[hemi])
        #    print msg0b % ("\t"*(bt+0),"+"*50)
        # Start at lowest pressure and work up
        for ilev in range(len(levels)-1):
            # Examining Level
            found_paths = [x for x in contours[hemi][ilev].get_paths()]
            path_lengths = [len(x) for x in found_paths]
            path_order = []
            done_paths = []
            for test_path in sorted(path_lengths,reverse=True):
                if test_path in done_paths:
                    continue
                members = [found_paths.index(x) for x in found_paths
                        if len(x) == test_path]
                done_paths.append(test_path)
                for member in members:
                    path_order.append(member)
            #if verbose:
            #    print msg0a % ("\t"*(bt+1),levels[ilev],len(found_paths))
            #    print msg0b % ("\t"*(bt+1),"="*40)

            # Make polygons
            polygon_vertices = {}
            polygon_paths = {}
            for polygon_id in path_order:
                cpath = found_paths[polygon_id]
                # Double the density of vertics along path (ensure closure
                # better when filling.
                cpath = cpath.interpolated(2)
                polygon_vertices[polygon_id] = [(vertex[0],vertex[1]) for (vertex,code) in
                        cpath.iter_segments(simplify=False)]
                polygon_paths[polygon_id] = cpath
                #if verbose:
            #    print msg1 % ("\t"*(bt+2),len(polygon_vertices))
            #    for polygon_id in polygon_vertices:
            #        print msg1a % ("\t"*(bt+3),polygon_id,
            #                len(polygon_vertices[polygon_id]))

            # Closure Test: Coincident 1st and last vertices. This might
            #   not happen because the polygon is broken due to small
            #   discontinuities in the data (too coarse of a contour
            #   interval for example), especially around the poles and
            #   the edges of the original array. As a test of these
            #   we allow small offset in the vertices to stand.
            #
            #   Mostly likely though, closure is broken because we
            #       masked the data outside the map projection boundaries
            #       and so the contour is incomplete due to low latitude
            #       parts being outside the map projection.
            #if plot_contours: c = {}
            for polygon_id in polygon_vertices.keys():
                closed = (1 if polygon_vertices[polygon_id][0]
                        == polygon_vertices[polygon_id][-1] else 0)
                #if plot_contours: c[polygon_id] = "closed"
                if not closed:
                    # Retrieve lon/lat for end points.
                    vertex_x0, vertex_y0 = m_map[hemi](polygon_vertices[polygon_id][0][0],
                            polygon_vertices[polygon_id][0][1],inverse=True)
                    vertex_x1, vertex_y1 = m_map[hemi](polygon_vertices[polygon_id][-1][0],
                            polygon_vertices[polygon_id][-1][-1],inverse=True)
                    # If either latitude is poleward of 88 force closure
                    #   as large longitude difference meaningless.
                    if abs(int(vertex_y0)) >= 88 or abs(int(vertex_y1)) >= 88:
                        polygon_vertices[polygon_id][-1] = polygon_vertices[polygon_id][0]
                        #if verbose: print msg2 % ("\t"*(bt+3),polygon_id)
                        #if plot_contours: c[polygon_id] = "pole_closed"
                        continue
                    # Check for small discontinuity
                    delta_lon = abs(abs(vertex_x0)-abs(vertex_x1))
                    delta_lat = abs(vertex_y0-vertex_y1)
                    if delta_lon + delta_lat <= 2.0:
                        polygon_vertices[polygon_id][-1] = polygon_vertices[polygon_id][0]
                        #if verbose: print msg2a % ("\t"*(bt+3),polygon_id)
                        #if plot_contours: c[polygon_id] = "close_closed"
                        continue
                    # Discard this polygon
                    #if verbose: print msg2b % ("\t"*(bt+3),polygon_id)
                    #if plot_contours: c[polygon_id] = "open"
                    # Comment if want to plot open below
                    del polygon_vertices[polygon_id]
                    del polygon_paths[polygon_id]
            # Uncomment to plot raw contours as they are now, RAW
            #if plot_contours:
            #    for polygon_id in polygon_vertices:
            #        pname = "%s_%04d_%04d_%s" % (h_lookup[hemi],levels[ilev],polygon_id,c[polygon_id])
            #        c_objects[pname] = polygon_vertices[polygon_id]
            #    c_lengths = {}
            #    # Skip over Checks below.
            #    continue

            ## Discard Contours with more than 75% of vertices are
            ##   below 30 degrees or any below 15 degrees.
            #polygon_lonlats = {}
            ##if plot_contours: c = {}
            #for polygon_id in polygon_vertices.keys():
            #    # Retrieve lon/lats
            #    lonlat_pairs = [m_map[hemi](vertex[0],vertex[1],inverse=True) for
            #            vertex in  polygon_vertices[polygon_id]]
            #    tropical_lats = [x[1] for x in lonlat_pairs
            #            if abs(x[1]) <= 30.0]
            #    tropical = float(len(tropical_lats))/float(len(lonlat_pairs))
            #    #if plot_contours: c[polygon_id] = "extra"
            #    if tropical > 0.75:
            #        # Much of contour inside tropics
            #        #if verbose: print msg3 % ("\t"*(bt+3),polygon_id)
            #        #if plot_contours: c[polygon_id] = "tropical"
            #        # Comment if want to plot open below
            #        del polygon_vertices[polygon_id]
            #        del polygon_paths[polygon_id]
            #        continue
            #    deep_tropical_lats = [x for x in tropical_lats
            #            if abs(x) <= 15.0]
            #    if deep_tropical_lats:
            #        # Contour inside deep tropics
            #        #if verbose: print msg3a % ("\t"*(bt+3),polygon_id)
            #        #if plot_contours: c[polygon_id] = "deep"
            #        # Comment if want to plot open below
            #        del polygon_vertices[polygon_id]
            #        del polygon_paths[polygon_id]
            #        continue
            #    # Store lonlat for later
            #    polygon_lonlats[polygon_id] = lonlat_pairs
            ## Uncomment to plot raw contours as they are now, RAW
            ##if plot_contours:
            ##    for polygon_id in polygon_vertices:
            ##        pname = "%s_%04d_%04d_%s" % (h_lookup[hemi],levels[ilev],polygon_id,c[polygon_id])
            ##        c_objects[pname] = polygon_vertices[polygon_id]
            ##    c_lengths = {}
            ##    # Skip over Checks below.
            ##    continue

            # Discard Big Contours: Contours whose perimeter exceeds
            #   contour_limit. Note lambert azimuthal equal-area projection
            #   is not conformal in distance so need to do this way.
            #
            #if plot_contours: c = {}
            polygon_length = {}
            for polygon_id in polygon_vertices.keys():
                path_length = int(PL(polygon_vertices[polygon_id])[-1]*0.001)
                #if plot_contours: c[polygon_id] = "%s" % int(path_length)
                if path_length > contour_limit:
                    #if verbose: print msg4 % ("\t"*(bt+3),polygon_id)
                    #if plot_contours: c[polygon_id] =  "Big_%s" % int(path_length)
                    # Comment if want to plot open below
                    del polygon_vertices[polygon_id]
                    #del polygon_lonlats[polygon_id]
                    del polygon_paths[polygon_id]
                else:
                    polygon_length[polygon_id] = path_length
            # Uncomment to plot raw contours as they are now, RAW
            #if plot_contours:
            #    for polygon_id in polygon_vertices:
            #        pname = "%s_%04d_%04d_%s" % (h_lookup[hemi],levels[ilev],polygon_id,c[polygon_id])
            #        c_objects[pname] = polygon_vertices[polygon_id]
            #    c_lengths = {}
            #    # Skip over Checks below.
            #    continue

            # Create final c_objects
            for polygon_id in polygon_vertices:
               pname = "%s_%04d_%04d" % (h_lookup[hemi],levels[ilev],polygon_id)
               c_objects[pname] = polygon_vertices[polygon_id]
               c_lengths[pname] = polygon_length[polygon_id]
               c_paths[pname] = polygon_paths[polygon_id]

    return c_objects,c_lengths,c_paths

def Save_To_File(centers_data,center_group_fmt,att_group_fmt,
                 atts_group_fmt,empty_group_fmt,problematic_fmt):
    """Dump the results to a text file."""

    print att_group_fmt
    print  atts_group_fmt
    print empty_group_fmt
    print problematic_fmt
    for center in centers_data:
        # *****************************************************************
        #                   Fill the Center/Track Group
        # *****************************************************************
        center_group = center_group_fmt.format(centers_data[center])
        print center_group

   



    # *****************************************************************
    #                     Fill the Attribution Group
    # *****************************************************************

    # Attributed grids minus center
    #sans_center = [x for x in collapsed_centers[acenter] if x != acenter]

    # Number of grids attributed to this center (includes center)
    #NGrids = len()

    return 0

#class mcms_data():


#    def __init__(self,center_fields):
#        # Private Variables
#        self.center_fields = center_fields


def main(defs_set,imports,import_read,loop_year,over_write_out_path,
        over_write_shared_path,over_write_slp_path,clevs,what_do,
        plot_contours,save_hi_res,save_source_res,
        cut_tail,verbose):

    # Some generally useful calendar tools.
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}
    months_inv = {'February': 2, 'October': 10, 'March': 3, 'August': 8, 'May': 5,
                  'January': 1, 'June': 6, 'September': 9, 'April': 4,
                  'December': 12, 'July': 7, 'November': 11}
    months_Length = {'February': 28, 'October': 31, 'March': 31, 'August': 31,
                     'May': 31, 'January': 31, 'June': 30, 'September': 30,
                     'April': 30, 'December': 31, 'July': 31, 'November': 30}
    months_Length_inv = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                         7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

    scnt = [0]*12

    # For unwinding reads/writes=
    ids = {'YYYY' : 0,'MM' : 1, 'DD' : 2, 'HH' : 3, 'JD' : 4,
           'CoLat' : 5, 'Lon' : 6, 'GridID': 7, 'GridSLP' : 8,
           'RegSLP' : 9, 'GridLAP' : 10, 'Flags' : 11, 'Intensity' : 12,
           'Disimularity' : 13, 'UCI' : 14, 'USI' : 15}
    # Format statement for center info
    center_table = {'YYYY'          : '{0[0]:04d}',
                    'MM'            : '{0[1]:02d}',
                    'DD'            : '{0[2]:02d}',
                    'HH'            : '{0[3]:02d}',
                    'JD'            : '{0[4]:09d}',
                    'CoLat'         : '{0[5]:05d}',
                    'Lon'           : '{0[6]:05d}',
                    'GridID'        : '{0[7]:07d}',
                    'GridSLP'       : '{0[8]:07d}',
                    'RegSLP'        : '{0[9]:07d}',
                    'GridLAP'       : '{0[10]:05d}',
                    'Flags'         : '{0[11]:02d}',
                    'Intensity'     : '{0[12]:02d}',
                    'Dissimilarity' : '{0[13]:04d}',
                    'UCI'           : '{0[14]:s}',
                    'USI'           : '{0[15]:s}'}
    center_fields = ('YYYY','MM','DD','HH','JD','CoLat','Lon',
                     'GridID','GridSLP','RegSLP','GridLAP','Flags',
                     'Intensity','Dissimilarity','UCI','USI')
    center_group_fmt = " ".join(['%s' % (center_table[x])
                                 for x in center_fields])
    # Fo rma t statement for ATT info
    att_table = {'N_ATT_Grids'                 : '{0[0]:05d}',
                 'Area_ATT'                    : '{0[1]:09d}',
                 'ATT_Perimeter'               : '{0[2]:06d}',
                 'ATT_MinOuterEdgeDist'        : '{0[3]:05d}',
                 'ATT_MaxOuterEdgeDist'        : '{0[4]:05d}',
                 'ATT_AveOuterEdgeDist'        : '{0[5]:05d}',
                 'Depth_ATT'                   : '{0[6]:04d}',
                 'NearestCenterDist_All'       : '{0[7]:05d}',
                 'NearestCenterDist_Alt'       : '{0[8]:05d}',
                 'NearestCenter_UCI_All'       : '{0[9]:s}',
                 'NearestCenter_UCI_Alt'       : '{0[10]:s}',
                 'ATT'                        : '{0[11]:s}'}
    att_fields = ('N_ATT_Grids','Area_ATT','ATT_Perimeter',
                  'ATT_MinOuterEdgeDist','ATT_MaxOuterEdgeDist',
                  'ATT_AveOuterEdgeDist','Depth_ATT',
                  'NearestCenterDist_All','NearestCenterDist_Alt',
                  'NearestCenter_UCI_All','NearestCenter_UCI_Alt',
                'ATT')
    att_group_fmt = " ".join(['%s' % (att_table[x])
                                 for x in att_fields]) + "\n"
    # Format statement for ATTS info
    atts_table = {'Primary_UCI'           : '{0[0]:s}',      
                  'N_Entangled'           : '{0[1]:02d}',
                  'Entangled_UCIs'        : '{0[2]:s}',
                  'N_ATTS_Grids'          : '{0[3]:05d}',
                  'Area_ATTS'             : '{0[4]:09d}',
                  'ATTS_Perimeter'        : '{0[5]:06d}',
                  'Depth_ATTS'            : '{0[9]:04d}',
                  'ATTS_MinOuterEdgeDist' : '{0[6]:05d}',
                  'ATTS_MaxOuterEdgeDist' : '{0[7]:05d}',
                  'ATTS_AveOuterEdgeDist' : '{0[8]:05d}',
                  'ATTS'                  : '{0[10]:s}'}
    atts_fields = ('Primary_UCI','N_Entangled','Entangled_UCIs','N_ATTS_Grids',
                   'Area_ATTS','ATTS_Perimeter','Depth_ATTS','ATTS_MinOuterEdgeDist',
                   'ATTS_MaxOuterEdgeDist','ATTS_AveOuterEdgeDist','ATTS')
    atts_group_fmt = "-888 " + " ".join(['%s' % (atts_table[x])
                                         for x in atts_fields]) + "\n"
    # Format statement for Empty Centers
    empty_group_fmt = "-999 " + center_group_fmt + "\n"
    # Format statement for problematic grids
    problematic_fmt = "-777 {0[0]:s}\n"

    #Note put this in read_mcms_v5?

    #centers_data = {'19960101000125006750' : [1996, 1, 1, 0, 245008350, 1340, 6707, 9675, 983199, 985066, 866, 0, 0, 29, '19960101000125006750', '19951229120125035250']}
    #import collections
    #mcms_data = collections.namedtuple('mcms_data',
    #                                   " ".join(center_fields),verbose=True)
    #p = mcms_data(**dict(zip(center_fields,centers_data['19960101000125006750'])))
    #print p.YYYY
    #print center_group_fmt.format(p)


    #msms_fields = center_UCI : ['center_group','att_group','atts_group','empty_group']
    #mcms_data = {'center_group'}

    #data_holder = mcms_data()
    #import sys; sys.exit("Stop Here")

    #Save_To_File(centers_data,center_group_fmt,att_group_fmt,
    #             atts_group_fmt,empty_group_fmt,problematic_fmt)
    #import sys; sys.exit("Stop Here")
    # --------------------------------------------------------------------------
    # Setup Section
    # --------------------------------------------------------------------------
    for i in imports:
        exec(i)

    # Fetch definitions and impose those set in defs_set.
    defs = defs.defs(**defs_set)
    Read_MCMS = read_mcms.Read_MCMS
    l2g = l2g.l2g2
    dump = pickle.dump
    inside_test = nx.pnpoly
    interior_test = nx.points_inside_poly
    first_last_lons = first_last_lons.first_last_lons
    NA = numpy.array
    NHIS = numpy.histogram2d
    NABS = numpy.absolute
    unpack = chain.from_iterable
    NM = numpy.multiply
    NS = numpy.sum
    PL = mlab.path_length
    SEP = mlab.dist
    Summerize = stats.ldescribe
    #Median = stats.lmedian
    NMean = numpy.mean
    NMin = numpy.min
    NMax = numpy.max

    if verbose:
       print_col = print_col.print_col
    else:
        print_col = 0

    # Get some definitions. Note must have run setup_vx.py already!
    sf_file = "%ss_dat.p" % (over_write_shared_path)
    try:
        fnc_out = pickle.load(open(sf_file, 'rb'))
        (im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
                dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
                bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
                bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
                super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
                var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
                no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
                land_gridids,troubled_centers,faux_grids) = fnc_out
        # Save memory
        #del troubled_centers
        del land_gridids
        del lat_edges
        del lon_edges
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
    # Update over_write values
    if over_write_slp_path:
        slp_path = over_write_slp_path
    if over_write_out_path:
        out_path = over_write_out_path
    if over_write_shared_path:
        shared_path = over_write_shared_path
    row_start_index = row_start.index
    n = len(lons)

    if save_source_res:
        # Import a bunch of model grid specific information
        #   Note must have run setup_vX.py already!
        cf_file = "%scf_dat.p" % (shared_path)
        try:
            fnc_out = pickle.load(open(cf_file, 'rb'))
            (use_all_lons,search_radius,regional_nys,gdict,rdict,ldict,ijdict,
            min_centers_per_tstep,max_centers_per_tstep,max_centers_per_tstep_change,
            lapp_cutoff,hpg_cutoff) = fnc_out
            del use_all_lons,search_radius,regional_nys,rdict
            del fnc_out
        except:
            sys.exit("\n\tWARNING: Error reading or finding %s." % (cf_file))

        ## Fetch attribute specific info.
        #af_file = "%saf_dat.p" % (shared_path)
        #try:
        #    fnc_out = pickle.load(open(af_file, 'rb'))
        #    darea = fnc_out[0]
        #    del fnc_out
        #except:
        #    sys.exit("\n\tWARNING: Error reading or finding %s." % (af_file))

    # Not non-linear interval
    #l1 = numpy.arange(clevs[0], clevs[1], clevs[2])
    #l2 = numpy.arange(995, l1[-1], 1)
    #levels = list(l1)
    #levels.extend(list(l2))
    #levels = dict((x,1) for x in levels)
    #levels = levels.keys()
    #levels.sort()
    #levels = NA(levels)

    levels = numpy.arange(clevs[0], clevs[1], clevs[2])
    if verbose: 
        print "\tLevels:"
        print_col(list(levels),indent_tag="\t\t",fmt="% 5d",cols=5,width=5)

    if not save_hi_res:
        if not save_source_res:
            print "\n\nI'm Not Saving Anything!\n\n"

    # Open file for progress
    cfmt = "%scontours_%s_%04d_%04d_%04d_%04d_progress.txt"
    prog_file = cfmt % (out_path,model,clevs[0],clevs[1],clevs[2],loop_year)
    # Open with a buffer size of zero to make updates rapid
    try:
        prog_save = open(prog_file,"w",0)
    except:
        sys.exit("\n\tWARNING: Error Creating %s." % (prog_file))

    # ---------------------------------------------------------------------
    # Pull in reference field
    # ---------------------------------------------------------------------
    # Open data file, extract data and model definitions
    exec(import_read)
    fnc = pull_data.pull_data(NetCDF,numpy,slp_path,file_seperator,loop_year,
            defs.read_scale,var_slp,var_time,lat_flip,lon_shift)
    (slp,times,the_time_units) = fnc
    del fnc

    # Work with the time dimension a bit.
    # This is set in setup_vX.py
    jd_fake = 0
    if the_calendar != 'standard':
        # As no calendar detected assume non-standard
        jd_fake = 1
    elif the_calendar != "proleptic_gregorian":
        jd_fake = False

    tsteps = len(times)
    the_time_range = [times[0],times[tsteps-1]]
    start = "%s" % (the_time_units)
    tmp = start.split()
    tmp1 = tmp[2].split("-")
    tmp2 = tmp[3].split(":")
    tmp3 = tmp2[2][0]
    start = "%s %s %04d-%02d-%02d %02d:%02d:%02d" % \
            (tmp[0],tmp[1],int(tmp1[0]),int(tmp1[1]),
             int(tmp1[2]),int(tmp2[0]),int(tmp2[1]),
             int(tmp3))
    # Warning this could get weird for non-standard
    # calendars if not set correctly (say to noleap)
    # in setup_vX.py
    cdftime = netcdftime.utime(start,calendar=the_calendar)
    get_datetime = cdftime.num2date
    dtimes = [get_datetime(times[step]) for step in range(0,tsteps)]
    # Get Julian Days.. unless GCM uses non-standard calendar in which case
    #  enumerate with timestep and use uci_stamps for datetime things.
    if jd_fake:
        # Use timesteps rather than dates
        # examples '000000000', '000000001'
        adates = ["%09d" % (x) for x in range(tsteps)]
        # Modify output format for timesteps
        fmt_1 = "%s %s %05d %05d %06d %07d " # use date_stamp
        fmt_2 = "%07d %05d %02d %02d %04d %s%05d%05d %s\n" # use uci_stamp
        defs.center_fmt = fmt_1 + fmt_2
    else:
        # Using regular date/times
        # examples 244460562, 244971850i
        date2jd = netcdftime.JulianDayFromDate
        adates = [int(100*date2jd(x,calendar='standard')) for x in dtimes]
        # Modify output format for datetimes
        fmt_1 = "%s %09d %05d %05d %06d %07d " # use date_stamp
        fmt_2 = "%07d %05d %02d %02d %04d %s%05d%05d %s\n" # use uci_stamp
        defs.center_fmt = fmt_1 + fmt_2
    date_stamps  = ['%4d%02d%02d%02d' % (d.year,d.month,d.day,d.hour) for d in dtimes]
    del times
    del dtimes

    # List tsteps in progress file.
    prog_save.write("%d\n" % (tsteps))

    # Create polar Basemap instance.
    #   Set boundaries for map
    lat_bound = -1*defs.tropical_boundary
    if plot_contours:
        res = "c"
    else:
        res = None
    m_map_nh = Basemap(projection=mproj_nh,lat_0=lats[-1],boundinglat=-1*lat_bound,
            lon_0=lons[0],resolution=res,rsphere=6378137.0)
    m_map_sh = Basemap(projection=mproj_sh,lat_0=lats[0],boundinglat=lat_bound,
            lon_0=lons[0],resolution=res,rsphere=6378137.0)
    the_geoid = pyproj.Geod(ellps='WGS84')
    geoid = the_geoid.inv

    # Limit contours to those whose circumference is less than
    #   some set amount. Here we use the circumference of a
    #   small circle on a sphere with the diameter of a set
    #   zonal wave number 4 centered on a latitude of 45 degrees.
    #contour_limit = 21000.0
    # zonal wave number 5 centered on a latitude of 45 degrees.
    contour_limit = 17000.0
    # zonal wave number 6 centered on a latitude of 45 degrees.
    #contour_limit = 14000.0

    # Smooth/interpolate data field by
    #   hemisphere to higher grid density
    nxx = 180
    nyy = 180

    make_sm = 0
    smooth_grid_x = smooth_grid_y = smooth_grid_area = bins = 0
    smooth_grid_row_start = smooth_grid_row_start_index = 0
    sm_file = "%ssm_%04d_%04d_dat.p" % (shared_path,nyy,nxx)
    if os.path.exists(sm_file):
        try:
            fnc_out = pickle.load(open(sm_file, 'rb'))
            (smooth_grid_x,smooth_grid_y,smooth_grid_area,
             smooth_grid_row_start,smooth_grid_row_end,bins) = fnc_out
            smooth_grid_row_start_index = smooth_grid_row_start.index
            # Save memory
            del fnc_out
        except:
            sys.exit("\n\tWARNING: Error reading %s." % (sm_file))
    else:
        make_sm = 1
    #specifics = {'levels' : levels,
    #             'contour_limit' : contour_limit,
    #             'geoid' : geoid,
    #             'plot_contours' : plot_contours,
    #             'verbose' : verbose
    #             }
    specifics = {'levels' : levels,
                 'contour_limit' : contour_limit,
                 'PL' : PL,
                 'plot_contours' : plot_contours,
                 'verbose' : verbose
                 }

    # Start working with center data
    # Adjust in_file names
    tag = str(what_do["in_file"][-cut_tail-4:-cut_tail])
    what_do["in_file"] = what_do["in_file"].replace(tag,str(loop_year))

    # Parse definitions.
    readit = Read_MCMS(**what_do)
    # Determine the source of the centers
    source = os.path.basename(readit.in_file).split(".")[0]
    # See if request something other than everything.
    readit.check_time()
    readit.check_place()
    readit.fetch_centers()
    centers = readit.center_holder.keys()
    centers.sort()
    centers.reverse()
    if verbose: print "\tCenters Read",len(centers)

    if save_hi_res:
        # Open data file to save results
        att_file_hi = readit.in_file.replace("tracks","attchi")
        try:
            att_save_hi = open(att_file_hi,"w")
        except:
            sys.exit("\n\tWARNING: Error Creating %s." % (att_file_hi))
    if save_source_res:
        # Open data file to save results
        att_file= readit.in_file.replace("tracks","attc")
        try:
            att_save = open(att_file,"w")
        except:
            sys.exit("\n\tWARNING: Error Creating %s." % (att_file))

  #tmp
    #print "\n\tUsing Shortened tsteps!\n"
    #tsteps = 31*4

    if verbose: print "\n\n%s" % ("="*40)
    last_center = ""
    for step in range(0,tsteps):
        date_stamp = date_stamps[step]

        if verbose: print "\tDoing ",date_stamp

        field = slp[step,:,:]

        # Add cyclic longitude to data and longitudes
        z,x = addcyclic(field,lons)
        # Shift data and longitudes to start at start_lon
        # also converts 0-360 to +-180 format
        z,x = shiftgrid(180.0,z,x,start=False)
        # Smooth Field
        smooth_field_nh,xx_nh,yy_nh = m_map_nh.transform_scalar(z,x,lats,
                nxx,nyy,returnxy=True,masked=True)

        # Make a LineCollection of contours
        contours_nh = m_map_nh.contour(xx_nh,yy_nh,smooth_field_nh,levels).collections
        # Smooth Field
        smooth_field_sh,xx_sh,yy_sh = m_map_sh.transform_scalar(z,x,lats,
                nxx,nyy,returnxy=True,masked=True)
        # Make a LineCollection of contours
        contours_sh = m_map_sh.contour(xx_sh,yy_sh,smooth_field_sh,levels).collections

        # Stuff for convenience
        hemis = ["nh","sh"]
        m_map = [m_map_nh,m_map_sh]
        xx = [xx_nh,xx_sh]
        yy = [yy_nh,yy_sh]
        lat_bounds = [lat_bound*-1,lat_bound]
        smooth_field = [smooth_field_nh,smooth_field_sh]
        contours = [contours_nh,contours_sh]

        if step == 0 and make_sm:
            # Setup grid mapping to the new smooth grid
            #   Do this once, save the results, comment
            #   this out and read it above.
            # Create what we need and save
            # Get gridids for 1st and last lon of each lat row.
            smooth_grid_row_start,smooth_grid_row_end = first_last_lons(nyy,nxx)
            smooth_grid_x_nh = list(xx_nh[0])
            smooth_grid_y_nh = [x[0] for x in yy_nh]
            # Create a set of bins for 2d histogram, here we need the
            #   left edges of the grids
            bins = [0,0,NA(smooth_grid_x_nh),NA(smooth_grid_y_nh)]
            smooth_grid_dx_nh = smooth_grid_x_nh[1] - smooth_grid_x_nh[0]
            smooth_grid_dy_nh = smooth_grid_y_nh[1] - smooth_grid_y_nh[0]
            # Set fixed grid area (km**2) note that dx,dy are in meters.
            smooth_grid_area = int((smooth_grid_dx_nh*smooth_grid_dy_nh)*0.000001)
            # Reframe smooth_grid_? of offset by smooth_grid_d?*0.5, these
            #   are our grid centers.
            smooth_grid_x_nh = [x+smooth_grid_dx_nh*0.5 for x in
                                smooth_grid_x_nh]
            smooth_grid_y_nh = [y+smooth_grid_dy_nh*0.5 for y in
                                smooth_grid_y_nh]
            bins[0] = (NA(smooth_grid_x_nh),NA(smooth_grid_y_nh))
            #if verbose:
            #    print "Smooth_Grid_X:"
            #    print_col(smooth_grid_x_nh,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            #    print "Smooth_Grid_Y:"
            #    print_col(smooth_grid_y_nh,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            #    print "Smooth_Grid_dX: %f8.2" % smooth_grid_dx_nh
            #    print "Smooth_Grid_dY: %f8.2" % smooth_grid_dy_nh
            #    print "Smooth_Grid_Area: %d Km**2" % smooth_grid_area
            #    print "Smooth_Grid_Row_start:"
            #    print_col(smooth_grid_row_start,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            #    print "Smooth_Grid_Row_end:"
            #    print_col(smooth_grid_row_end,indent_tag="\t",fmt="% 6d",cols=10,width=10)

            smooth_grid_x_sh = list(xx_sh[0])
            smooth_grid_y_sh = [x[0] for x in yy_sh]
            smooth_grid_dx_sh = smooth_grid_x_sh[1] - smooth_grid_x_sh[0]
            smooth_grid_dy_sh = smooth_grid_y_sh[1] - smooth_grid_y_sh[0]

            # Reframe smooth_grid_? of offset by smooth_grid_d?*0.5, these
            #   are our grid centers.
            smooth_grid_x_sh = [x+smooth_grid_dx_sh*0.5 for x in
                                smooth_grid_x_sh]
            smooth_grid_y_sh = [y+smooth_grid_dy_sh*0.5 for y in
                                smooth_grid_y_sh]
            bins[1] = (NA(smooth_grid_x_sh),NA(smooth_grid_y_sh))
            #if verbose:
            #    print "Smooth_Grid_X:"
            #    print_col(smooth_grid_x_sh,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            #    print "Smooth_Grid_Y:"
            #    print_col(smooth_grid_y_sh,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            #    print "Smooth_Grid_dX: %f8.2" % smooth_grid_dx_sh
            #    print "Smooth_Grid_dY: %f8.2" % smooth_grid_dy_sh
            #    print "Smooth_Grid_Area: %d Km**2" % smooth_grid_area
            #    print "Smooth_Grid_Row_start:"
            #    print_col(smooth_grid_row_start,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            #    print "Smooth_Grid_Row_end:"
            #    print_col(smooth_grid_row_end,indent_tag="\t",fmt="% 6d",cols=10,width=10)
            # Save output
            smooth_grid_x = [smooth_grid_x_nh,smooth_grid_x_sh]
            smooth_grid_y = [smooth_grid_x_nh,smooth_grid_x_sh]
            fnc_out = (smooth_grid_x,smooth_grid_y,smooth_grid_area,smooth_grid_row_start,
                       smooth_grid_row_end,bins)
            pickle.dump(fnc_out, open(sm_file, "wb",-1))
            make_sm = 0
            smooth_grid_row_start_index = smooth_grid_row_start.index
            specifics['smooth_grid_row_start'] = smooth_grid_row_start
            specifics['smooth_grid_row_start_index'] = smooth_grid_row_start_index
            specifics['bins'] = bins

        c_objects,c_lengths,c_paths = isolate_contour_objects(contours,m_map,**specifics)

        #c_lengths = 0
        #if not c_lengths:
        #    # Empty c_lengths a flag to do this and stop
        #    # Plot *vertices* as individual objects
        #    figsize=(8,8)
        #    for path_id in c_objects.keys():
        #        fig = plt.figure(figsize=figsize,frameon=True)
        #        ax = fig.add_subplot(1,1,1)
        #        h = hemis.index(path_id[:2])
        #        image = m_map[h].contour(xx[h],yy[h],smooth_field[h],
        #                [int(path_id[3:7])],colors='k')
        #        circles = [lat_bounds[h]]
        #        image2 = plt.clabel(image,fontsize=5,inline=1,inline_spacing=0,fmt='%d')
        #        m_map[h].drawparallels(circles)
        #        m_map[h].drawmeridians([0.0])
        #        m_map[h].drawmeridians([180.0])
        #        m_map[h].fillcontinents(color='0.9')
        #        m_map[h].drawcoastlines(linewidth=0.25)
        #        for a in c_objects[path_id]:
        #            pnt_x, pnt_y = a
        #            pnt_image = m_map[h].plot(pnt_x,pnt_y,'o',markersize=1.0,
        #                    markerfacecolor='red',markeredgecolor='red',
        #                    linewidth=1,zorder=1)
        #        pname = "%sicontours_%s%s" % (plot_contours,path_id,fig_format)
        #        ax.set_title(path_id)
        #        fig.savefig(pname,dpi=144,facecolor='w',edgecolor='w',
        #                orientation='landscape',bbox_inches='tight',
        #                pad_inches=0.03)
        #        print "\tMade",pname
        #        plt.close('all')
        #    import sys; sys.exit("Stop Here")

        # Get current centers.
        current_centers = []
        found_none = 1
        if len(centers) < 1:
            more = 0
        else:
            more = 1
        while more:
            # See if overflow from last read useful or read new record
            if last_center:
                center = last_center
                last_center = ""
            else:
                center = centers.pop()
                if len(centers) < 1: # No more centers
                    more = 0
            # Store if center falls on wanted date.
            if center.startswith(date_stamp,0,10):
                current_centers.append(center)
                found_none = 0
            else:
                # Store for next time
                last_center = center
                more = 0
        if found_none:
            # No centers found
            msg = "\tError: No Centers Found! %s" % date_stamp
            sys.exit(msg)
        if verbose: print "\t\tCurrent Centers: %d" % len(current_centers)

    #TMP
    #    if date_stamp != '1996010112':
    #        continue
    #    elif date_stamp == '1996010118':
    #        import sys; sys.exit("Early Out")
    ##TMP
        #current_centers = ['19960101000350031250']

        # Convert centers into map coordinates (vertices)
        center_places = {}
        canidates_nh = []
        canidates_sh = []
        for center in current_centers:
            clat = 90.0 - (readit.center_holder[center][ids['CoLat']]*0.01)
            clon = readit.center_holder[center][ids['Lon']]*0.01
            #clon = ((clon+180.0)%360)-180.0
            cslp = readit.center_holder[center][ids["GridSLP"]]*0.001
            h = (0 if clat >= 0 else 1)
            hi = hemis[h]
            cx,cy = m_map[h](clon,clat)
            center_places[center] = (cx,cy,h,cslp,clat,clon)
            if h:
                canidates_sh.append(center)
            else:
                canidates_nh.append(center)   
        canidates = [canidates_nh,canidates_sh]

        # Assign centers to c_objects
        #
        # Some c_objects (contours) contain a single center, in which
        #   case these are ATT contours for that center, other c_objects
        #   contain multiple centers are are thus ATTS contours. We
        #   ignore contours with no centers and usually these are either
        #   high pressure systems or low pressure systems that contain
        #   centers we have discarded. Also, sometimes a center has
        #   no c_objects (i.e., an open-wave system) these are empty
        #   centers.
        unique_contours = {}
        shared_contours = {}
        for polygon_id in c_objects.keys():
            h = hemis.index(polygon_id[:2])
            # Find centers falling inside this c_object
            contains = [("",center)[inside_test(center_places[center][0],
                center_places[center][1],c_objects[polygon_id])]
                   for center in canidates[h]]
            contains = [x for x in contains if x]
            if not contains:
                continue
            elif len(contains) == 1:
                if contains[0] not in unique_contours:
                    unique_contours[contains[0]] = [polygon_id]
                else:
                    old = unique_contours[contains[0]]
                    old.append(polygon_id)
                    unique_contours[contains[0]] = old
            else:
                for con in contains:
                    if con not in shared_contours:
                        shared_contours[con] = [polygon_id]
                    else:
                        old = shared_contours[con]
                        old.append(polygon_id)
                        shared_contours[con] = old

        empty_centers = dict.fromkeys([x for x in current_centers if x not in unique_contours],1)
        empty_centers = empty_centers.keys()
        if verbose: 
            print "\t\tUnique Contours (ATT): %d" % len(unique_contours)
            msg = "\t\t\tCenter (%s) has %d ATT Contours:"
            for center in unique_contours:
                print msg % (center,len(unique_contours[center]))
                print_col(unique_contours[center],indent_tag="\t\t\t\t",
                          fmt="%12s",cols=3,width=12,sort_me=0)
            print "\t\tEmpty Centers (%d):" % (len(empty_centers))
            print_col(empty_centers,indent_tag="\t\t\t\t",
                          fmt="%22s",cols=2,width=25,sort_me=0)

        ## Plot what we've done so far
        #for h in range(2):
        #    figsize=(8,8)
        #    fig = plt.figure(figsize=figsize,frameon=True)
        #    ax = fig.add_subplot(1,1,1)
        #    image = m_map[h].contour(xx[h],yy[h],smooth_field[h],levels,colors='k')
        #    circles = [lat_bounds[h],2*lat_bounds[h]]
        #    image2 = plt.clabel(image,fontsize=5,inline=1,inline_spacing=0,fmt='%d')
        #    m_map[h].drawparallels(circles)
        #    m_map[h].drawmeridians([0.0])
        #    m_map[h].drawmeridians([180.0])
        #    m_map[h].fillcontinents(color='0.9')
        #    m_map[h].drawcoastlines(linewidth=0.25)
        #    done = {}
        #    for center in canidates[h]:
        #        # Draw Center
        #        cx,cy,h,cslp,clat,clon = center_places[center]
        #        pnt_image = m_map[h].plot(cx,cy,'s',markersize=5.0,
        #                    markerfacecolor='k',markeredgecolor='k',
        #                    linewidth=1,zorder=1)
        #        pnt_image = m_map[h].plot(cx,cy,'x',markersize=4.5,
        #                    markerfacecolor='k',markeredgecolor='white',
        #                    linewidth=1,zorder=1)
        #        if center in unique_contours:
        #            for path_id in unique_contours[center]:
        #                for a in c_objects[path_id]:
        #                    if a in done:
        #                        continue
        #                    else:
        #                        done[a] = 1
        #                        pnt_image = m_map[h].plot(a[0],a[1],'o',markersize=1.0,
        #                                markerfacecolor='red',markeredgecolor='red',
        #                                linewidth=1,zorder=1)
        #        if center in shared_contours:
        #            for path_id in shared_contours[center]:
        #                for a in c_objects[path_id]:
        #                    if a in done:
        #                        continue
        #                    else:
        #                        done[a] = 1
        #                        pnt_image = m_map[h].plot(a[0],a[1],'o',markersize=1.0,
        #                                markerfacecolor='cyan',markeredgecolor='cyan',
        #                                linewidth=1,zorder=1)
        #    ttitle = "%02d %02d %s %04d"
        #    ttitle = ttitle % (int(date_stamp[8:10]),int(date_stamp[6:8]),
        #                months[int(date_stamp[4:6])],int(date_stamp[:4]))
        #    ax.set_title(ttitle)
        #    pname = "%sc_%s_%04d_%02d_%s%s" % (plot_contours,hemis[h],
        #            clevs[1]-clevs[2],clevs[2],date_stamp,fig_format)
        #    fig.savefig(pname,dpi=144,facecolor='w',edgecolor='w',
        #            orientation='landscape',bbox_inches='tight',
        #            pad_inches=0.03)
        #    print "\tMade",pname
        #    plt.close('all')

        # Fill ATT or unique_contours: Find the highest pressure
        #   unique_contour for each center and fill it.
        #
        # Fill interior points. These being points inside a given contour
        #   w/ SLP values at or below the given contour. This is down with
        #   the point-in-polygon (PIP) method from computational
        #   geometry. Also called the crossing-number or even-odd rule algorithm.
        #   See also: Jordan curve theorem.
        #
        #   Also find the center to edge distance (great circle) for each
        #       point along the outermost contour. This is used to find
        #       the min,max,mean/median center to edge distance. Note
        #       care is taken for cases where the center-to-edge line
        #       leaves the contour (i.e., edge around a corner) and the
        #       distance is taken as the distance along the contour to
        #       the nearest edge that can reach the center plus the
        #       distance from their to the center.
        #
        #   Also find the center depth which is the difference between
        #       the contour value of the outer most ATT contour and
        #       the central SLP of the center.
        #
        #  Also find the surface area of the enclosing contours.
        #   For the projected map, the grids are all equal area so this is
        #   simple. Because the grids are small/high density this
        #   estimate will be more accurate, or at least, less blocky
        #   than the one based on the original data source grids which
        #   tend to be much larger.
        if verbose:
            print "\n\t\tATT Finding\n\t\t%s\n" % ("--"*30)
        center_att = {}
        center_att_radius = {}
        center_att_depth = {}
        center_att_area = {}
        center_att_perimeter = {}
        for center in unique_contours:
            maxvalue, maxindex = max(izip([int(x[3:7]) for x
                in unique_contours[center]], count()))
            polygon_id = unique_contours[center][maxindex]

            if verbose:
                msg = "\t\tCenter %s using Contour %s as outer ATT"
                print msg % (center,polygon_id)

            # Store the perimeter of the outer contour
            center_att_perimeter[center] = c_lengths[polygon_id]

            # Find the center-to-edge separation around this
            #   contour and its depth
            cx,cy,h,cslp,clat,clon = center_places[center]
            center_att_depth[center] = int(10*round(int(polygon_id[3:7]) - cslp))
            cen = NA((cx,cy))
            # Find all center-to-edge distances
            all_dists = [SEP(cen,NA(edge_pnt))*0.001 for edge_pnt in
                    c_objects[polygon_id]]
            if verbose:
                print "\t\t\tCenter Depth: %d" % (center_att_depth[center])
                print "\t\t\tCenter-to-Edge Separations:"
                print_col([int(round(x)) for x in all_dists],
                          indent_tag="\t\t\t\t",fmt="% 5d",
                          cols=4,width=10,sort_me=0)
            ipnt = 0
            these_crossed = []
            for edge_pnt in c_objects[polygon_id]:
                e = m_map[h](*edge_pnt,inverse=True)
                # See if line crosses the contour edge
                lpath = m_map[h].drawgreatcircle(e[0],e[1],clon,clat)
                lpath = lpath[0].get_path()
                lverts = [(vertex[0],vertex[1]) for (vertex,code) in
                        lpath.iter_segments(simplify=False)]
                # Remove the 1st vertex as this is on the contour
                lverts = lverts[1:]
                lcodes = [Path.LINETO for x in lverts]
                lcodes[0] = Path.MOVETO
                lcodes[-1] = Path.CLOSEPOLY
                lpath = Path(lverts,lcodes)
                # See if crosses the contour edge
                crosses = lpath.intersects_path(c_paths[polygon_id],filled=False)
                if crosses:
                    all_dists[ipnt] = -1
                    these_crossed.append(ipnt)
                ipnt += 1
            if verbose:
                msg = "\t\t\tCrossing Lines Count (%d):"
                print msg % (len(these_crossed))

            # If any lines crossed, we find the distance from that edge
            #   along the contour to the closest edge that can get to
            #   the center and add that edge_to_center distance to the
            #   along contour distance to the problem point.
            all_dists_cp = all_dists[:]
            if verbose:
                tmpc = []
            for cpnt in these_crossed:
                ncnt = len(all_dists_cp)
                if cpnt == 0:
                    closest = [i for i in range(cpnt,ncnt)
                            if all_dists_cp[i] >= 0][0]
                    foreward = closest
                elif cpnt == ncnt-1:
                    closest = [i for i in range(cpnt,-1,-1)
                            if all_dists_cp[i] >= 0][0]
                    foreward = ""
                else:
                    # Find Closest non-crossing point going toward
                    #   the beginning of the contour
                    backward = [i for i in range(cpnt,-1,-1)
                            if all_dists_cp[i] >= 0]
                    if backward:
                        backward = backward[0]
                    else:
                        # Force to go other way all bad to end of array.
                        backward = ncnt*2
                    # Find Closest non-crossing point going toward
                    #   the end of the contour
                    foreward = [i for i in range(cpnt,ncnt) 
                            if all_dists_cp[i] >= 0]
                    if foreward:
                        foreward = foreward[0]
                    else:
                        # Force to go other way all bad to end of array.
                        foreward = ncnt*2
                    # Best match
                    closest = (foreward if abs(cpnt-backward) > 
                            abs(cpnt-foreward) else backward)
                # Distance along contour between cpnt and closest
                if closest == foreward:
                    curve = c_objects[polygon_id][cpnt:closest+1]
                else:
                    curve = c_objects[polygon_id][closest:cpnt+1]
                dist = int(PL(curve)[-1]*0.001)
                # Add the center-to-edge distance of closest
                all_dists[cpnt] = dist + all_dists[closest]
                if verbose:
                    tmpc.append(all_dists[cpnt])
            if verbose and these_crossed:
                print "\t\t\tCrossing Lines Updated Distances:"
                print_col([int(round(x)) for x in tmpc],
                          indent_tag="\t\t\t\t",fmt="% 5d",
                          cols=4,width=10,sort_me=0)

            # Find the max,min,mean of center-to-edge separation
            all_dists = NA(all_dists) 
            center_att_radius[center] = (int(NMin(all_dists)),
                                       int(NMax(all_dists)),int(NMean(all_dists)))
            if verbose:
                msg = "\t\t\tCenter-to-Edge Separations:"
                msg = msg + " Min(%d) Ave(%d) Max(%d)"
                print msg % (center_att_radius[center][0],
                             center_att_radius[center][2],
                             center_att_radius[center][1])

            ## Draw what is happening.
            #figsize=(8,8)
            #fig = plt.figure(figsize=figsize,frameon=True)
            #ax = fig.add_subplot(1,1,1)
            #circles = [lat_bounds[h],2*lat_bounds[h]]
            #m_map[h].drawparallels(circles)
            #m_map[h].drawmeridians([0.0])
            #m_map[h].drawmeridians([180.0])
            #m_map[h].fillcontinents(color='0.9')
            #m_map[h].drawcoastlines(linewidth=0.25)
            ## Draw all center-to-edge lines cross the boundary
            #for a in these_crossed:
            #    # Draw the line on the fig maximum center-to-edge
            #    eb = m_map[h](*c_objects[polygon_id][a],inverse=True)
            #    pmt_imate = m_map[h].drawgreatcircle(eb[0],eb[1],clon,clat,
            #            linestyle='-',linewidth=0.5,color='k',zorder=1)
            ## Draw the Center
            #pnt_image = m_map[h].plot(cx,cy,'s',markersize=5.0,
            #            markerfacecolor='k',markeredgecolor='k',
            #            linewidth=1,zorder=3)
            #pnt_image = m_map[h].plot(cx,cy,'x',markersize=4.5,
            #            markerfacecolor='k',markeredgecolor='white',
            #            linewidth=1,zorder=3)
            ## Draw the contour
            #for a in c_objects[polygon_id]:
            #    pnt_image = m_map[h].plot(a[0],a[1],'o',markersize=1.0,
            #            markerfacecolor='red',markeredgecolor='red',
            #            linewidth=1,zorder=2)
            #minx, x_index = min(izip(all_dists, count()))
            #min_line = (m_map[h](*c_objects[polygon_id][x_index],inverse=True))
            #maxx, x_index = max(izip(all_dists, count()))
            #max_line = (m_map[h](*c_objects[polygon_id][x_index],inverse=True))
            ## Draw the line on the fig minimum center-to-edge
            #m_map[h].drawgreatcircle(min_line[0],min_line[1],clon,clat,
            #        linestyle='-',linewidth=1.5,color='green')
            ## Draw the line on the fig maximum center-to-edge
            #m_map[h].drawgreatcircle(max_line[0],max_line[1],clon,clat,
            #        linestyle='-',linewidth=1.5,color='blue')
            #pname = "%s%s_%s_%04d_%02d_%s%s" % (plot_contours,center,hemis[h],
            #        clevs[1]-clevs[2],clevs[2],date_stamp,fig_format)
            #fig.savefig(pname,dpi=144,facecolor='w',edgecolor='w',
            #        orientation='landscape',bbox_inches='tight',
            #        pad_inches=0.03)
            #print "\tMade",pname
            #plt.close('all')

            ## Draw what is happening.
            #import matplotlib.patches as patches
            ## Draw contour, fill with cross-hatch
            ##   Hatch : * stars, O big circles, o circles, . small circles
            ##           + cross hatch / or \\ slashs
            ##patch = patches.PathPatch(c_paths[polygon_id],fc='k',
            ##        fill=False,hatch=".",lw=1)
            ## solid fill
            ##patch = patches.PathPatch(c_paths[polygon_id],fc='red',
            ##        fill=True,lw=1)
            ##ax.add_patch(patch)
            ## Draw Centroid of contour
            #p_verts = NA(c_objects[polygon_id])
            #a = numpy.diff(p_verts[:-1][:,[1,0]]*p_verts[1:])
            #area = a.sum()/2.0
            #centroid = ((p_verts[:-1,:] + p_verts[1:,:])*a).sum(axis=0)/(6.0*area)
            #pnt_image = m_map[h].plot(centroid[0],centroid[1],'s',markersize=3.0,
            #            markerfacecolor='cyan',markeredgecolor='b',
            #            linewidth=1,zorder=3)

            #Fix
            # Note this might work but I need to figure it out.
            #fillup = mlab.poly_between(c_objects[polygon_id],
            #        c_objects[polygon_id], c_objects[polygon_id])
            #xvals,yvals = izip(*fillup)
            #print len(xvals)
            #print xvals
            #fverts = zip(list(fill[0]),list(fill[1]))
            #print fverts

            # Use a 2d histogram of the vertices to collapse to gridIDs.
            #   This is done so that we can quickly by the envelope of
            #   points surrounding and interior to the contour.
            xvals,yvals = zip(*c_objects[polygon_id])
            H, xedges, yedges = NHIS(NABS(NA(xvals)),NABS(NA(yvals)),bins=bins[2])
            indices = H.nonzero()
            the_path = dict.fromkeys([j*nxx+i for i, j in
                zip(indices[0],indices[1])],1)
            the_path = the_path.keys()
        
            # Find the envelope structure holding the polygon
            envelope = []
            # Scan all rows on the map and find the occupied grids.
            row_width = [0]*nyy
            occupied_rows = {}
            for pnt in the_path:
                row_guess = [x for x in smooth_grid_row_start
                             if x <= pnt]
                row_guess = smooth_grid_row_start_index(row_guess[-1])
                row_width[row_guess] += 1
                occupied_rows[row_guess] = 1
            occupied_rows = occupied_rows.keys()
            occupied_rows.sort()
            # Loop over each occupied row and look for gaps
            for row in occupied_rows:
                row_starter = smooth_grid_row_start[row]
                row_ender = row_starter+nxx-1
                in_row = [x for x in the_path if row_starter <= x <= row_ender]
                in_row.sort()
                full_row = range(in_row[0],in_row[-1]+1)
                envelope.extend(full_row)
            gaps = [x for x in envelope if x not in the_path]
            if gaps:
                # Fill the interior
                verts = NA(c_objects[polygon_id],float)
                pnts = [(bins[h][0][pnt%nxx],bins[h][1][pnt/nyy]) for
                         pnt in envelope]
                pnts = NA(pnts,float)
                interior = interior_test(pnts, verts)
                the_fill = list(interior.ravel().nonzero()[0])
                the_fill = [list(pnts[x]) for x in the_fill]
                # Collapse the the_fill to gridIDs.
                xvals,yvals = zip(*the_fill)
                H, xedges, yedges = NHIS(NABS(NA(xvals)),NABS(NA(yvals)),bins=bins[2])
                indices = H.nonzero()
                the_fill = dict.fromkeys([j*nxx+i for i, j in
                    zip(indices[0],indices[1])],1)
                the_fill = the_fill.keys()
                # Add the contour itself
                the_fill.extend(the_path)
                #
                # Store everything as full res vertices (can't use for area)
                #the_fill.extend([(bins[h][0][pnt%nxx],bins[h][1][pnt/nyy]) for
                #         pnt in the_path])
                #the_fill.extend(c_objects[polygon_id])
            else:
                # No Fill to be added.
                the_fill = the_path
                #the_fill = c_objects[polygon_id]

            # Store the results
            center_att[center] = the_fill
            if verbose:
                print "\t\t\tATT (%d):" % (len(the_fill))
                print_col(the_fill,
                          indent_tag="\t\t\t\t",fmt="% 7d",
                          cols=5,width=10,sort_me=1)

            # Find Area
            area = [len(the_fill)*smooth_grid_area]
            ## Find Area
            ##   From Paul Bourke's webpage:
            ##       http://astronomy.swin.edu.au/~pbourke/geometry
            #p_verts = NA(c_objects[polygon_id])
            #v_first = p_verts[:-1][:,[1,0]]
            #v_second = p_verts[1:]
            #area = numpy.diff(v_first*v_second).sum()/2.0
            #print "AREA",abs(area)*0.000001
            center_att_area[center] = area[0]
            if verbose:
                print "\t\t\tATT Area: %d" % (area[0])

        # Fill ATTS or shared_contours: Find the highest pressure
        #   shared_contour for each center and fill it, excluding
        #   any ATT points.
        if verbose:
            print "\n\t\tATTS Finding\n\t\t%s\n" % ("--"*30)
        center_atts = {}
        center_atts_radius = {}
        center_atts_depth = {}
        center_entangled = {}
        center_atts_area = {}
        center_atts_perimeter = {}
        sc = dict.fromkeys(list(unpack([shared_contours[cob] for cob in shared_contours])),1)
        sc = sc.keys()
        sc.sort(key=lambda s: s.split("_")[1])
        done = []
        while sc:
            scon = sc.pop()
            if scon in done:
                continue

            # Retrieve centers embedded in this contour
            entangled = dict.fromkeys([cob for cob in 
                shared_contours if scon in shared_contours[cob]],1)
            entangled = entangled.keys()
            if verbose:
                msg = "\t\tATTS Contour %s contains these centers:"
                print msg % (scon)
                print_col(entangled,indent_tag="\t\t\t",
                        fmt="%22s",cols=2,width=25,sort_me=0)

            # Find the common set of contours shared by the
            #   entangled centers. They should be all the
            #   same.
            entangled_cons = dict.fromkeys(list(unpack(
                [shared_contours[cob] for cob in entangled])),1)
            entangled_cons = entangled_cons.keys()
            exclusive_cons = [(cob,[ec for ec in shared_contours[cob] if ec not
                in entangled_cons]) for cob in entangled]
            if sum([len(x[1]) for x in exclusive_cons]):
                msg = "\tWarning Exclusive Contours!\n"
                msg1 = "\tEntangled Contours:",entangled_cons
                msg2 ="\tExclusive Contours:",exclusive_cons
                sys.exit(msg+msg1+msg2)
            if verbose:
                print "\t\t\tEntangled Contours:"
                print_col(entangled_cons,indent_tag="\t\t\t\t",
                        fmt="%12s",cols=2,width=15,sort_me=1)

            # Pick a "primary" which is the center among those with
            #   contours in common with the lowest SLP.
            maxvalue, maxindex = max(izip([center_places[x][3] for x
                in entangled],count()))
            primary = entangled[maxindex]
            # Centers entangled with the primary
            center_entangled[primary] = [0,[x for x in 
                        entangled if x != primary]]
            # Depth of the primary
            center_atts_depth[primary] = int(10*round(int(scon[3:7])
                                                     - center_places[primary][3]))
            # Perimeter of the outer contour
            center_atts_perimeter[primary] = c_lengths[scon]
            if verbose:
                print "\t\t\tPrimary Center: %s" % primary
                print "\t\t\t"
                msg = "\t\t\tDepth for Primary Center: %d"
                print msg % (center_atts_depth[primary])
                msg = "\t\t\tPerimeter for Primary Center: %d"
                print msg % (center_att_perimeter[primary])

            # Find the center-to-edge separation around this
            #   contour
            cx,cy,h,cslp,clat,clon = center_places[primary]
            cen = NA((cx,cy))
            # Find all center-to-edge distances
            all_dists = [SEP(cen,NA(edge_pnt))*0.001 for edge_pnt in
                    c_objects[scon]]
            if verbose:
                msg = "\t\t\tCenter-to-Edge Separations for %s:"
                print msg % primary
                print_col([int(round(x)) for x in all_dists],
                          indent_tag="\t\t\t\t",fmt="% 5d",
                          cols=4,width=10,sort_me=0)
            ipnt = 0
            these_crossed = []
            for edge_pnt in c_objects[scon]:
                e = m_map[h](*edge_pnt,inverse=True)
                # See if line crosses the contour edge
                lpath = m_map[h].drawgreatcircle(e[0],e[1],clon,clat)
                lpath = lpath[0].get_path()
                lverts = [(vertex[0],vertex[1]) for (vertex,code) in
                        lpath.iter_segments(simplify=False)]
                # Remove the 1st vertex as this is on the contour
                lverts = lverts[1:]
                lcodes = [Path.LINETO for x in lverts]
                lcodes[0] = Path.MOVETO
                lcodes[-1] = Path.CLOSEPOLY
                lpath = Path(lverts,lcodes)
                # See if crosses the contour edge
                crosses = lpath.intersects_path(c_paths[scon],filled=False)
                if crosses:
                    all_dists[ipnt] = -1
                    these_crossed.append(ipnt)
                ipnt += 1
            if verbose:
                msg = "\t\t\tCrossing Lines Count (%d):"
                print msg % (len(these_crossed))
                tmpc = []

            # If any lines crossed, we find the distance from that edge
            #   along the contour to the closest edge that can get to
            #   the center and add that edge_to_center distance to the
            #   along contour distance to the problem point.
            all_dists_cp = all_dists[:]
            for cpnt in these_crossed:
                ncnt = len(all_dists_cp)
                if cpnt == 0:
                    closest = [i for i in range(cpnt,ncnt)
                            if all_dists_cp[i] >= 0][0]
                    foreward = closest
                    backward = ""
                elif cpnt == ncnt-1:
                    closest = [i for i in range(cpnt,-1,-1)
                            if all_dists_cp[i] >= 0][0]
                    foreward = ""
                    backward = closest
                else:
                    # Find Closest non-crossing point going toward
                    #   the beginning of the contour
                    backward = [i for i in range(cpnt,-1,-1)
                            if all_dists_cp[i] >= 0]
                    if backward:
                        backward = backward[0]
                    else:
                        # Force to go other way all bad to end of array.
                        backward = ncnt*2
                    # Find Closest non-crossing point going toward
                    #   the end of the contour
                    foreward = [i for i in range(cpnt,ncnt) 
                            if all_dists_cp[i] >= 0]
                    if foreward:
                        foreward = foreward[0]
                    else:
                        # Force to go other way all bad to end of array.
                        foreward = ncnt*2
                    # Best match
                    closest = (foreward if abs(cpnt-backward) >
                            abs(cpnt-foreward) else backward)
                # Distance along contour between cpnt and closest
                if closest == foreward:
                    curve = c_objects[scon][cpnt:closest+1]
                else:
                    curve = c_objects[scon][closest:cpnt+1]
                dist = int(PL(curve)[-1]*0.001)
                # Add the center-to-edge distance of closest
                all_dists[cpnt] = dist + all_dists[closest]
                if verbose: tmpc.append(all_dists[cpnt])
            if verbose and these_crossed:
                print "\t\t\tCrossing Lines Updated Distances:"
                print_col([int(round(x)) for x in tmpc],
                        indent_tag="\t\t\t\t",fmt="% 5d",
                        cols=4,width=10,sort_me=0)

            # Find the max,min,mean of center-to-edge separation
            all_dists = NA(all_dists) 
            center_atts_radius[primary] = (int(NMin(all_dists)),
                                   int(NMax(all_dists)),int(NMean(all_dists)))
            if verbose:
                msg = "\t\t\tCenter-to-Edge Separations:"
                msg = msg + " Min(%d) Ave(%d) Max(%d)"
                print msg % (center_atts_radius[primary][0],
                             center_atts_radius[primary][2],
                             center_atts_radius[primary][1])

            # Use a 2d histogram of the vertices to collapse to gridIDs.
            #   This is done so that we can quickly by the envelope of
            #   points surrounding and interior to the contour.
            hemi = hemis.index(scon[:2])
            xvals,yvals = zip(*c_objects[scon])
            H, xedges, yedges = NHIS(NABS(NA(xvals)),NABS(NA(yvals)),bins=bins[2])
            indices = H.nonzero()
            the_path = dict.fromkeys([j*nxx+i for i, j in
                zip(indices[0],indices[1])],1)
            the_path = the_path.keys()

            # Find the envelope structure holding the polygon
            envelope = []
            # Scan all rows on the map and find the occupied grids.
            row_width = [0]*nyy
            occupied_rows = {}
            for pnt in the_path:
                row_guess = [x for x in smooth_grid_row_start
                             if x <= pnt]
                row_guess = smooth_grid_row_start_index(row_guess[-1])
                row_width[row_guess] += 1
                occupied_rows[row_guess] = 1
            occupied_rows = occupied_rows.keys()
            occupied_rows.sort()
            # Loop over each occupied row and look for gaps
            for row in occupied_rows:
                row_starter = smooth_grid_row_start[row]
                row_ender = row_starter+nxx-1
                in_row = [x for x in the_path if row_starter <= x <= row_ender]
                in_row.sort()
                full_row = range(in_row[0],in_row[-1]+1)
                envelope.extend(full_row)
            gaps = [x for x in envelope if x not in the_path]
            if gaps:
                # Fill the interior
                verts = NA(c_objects[scon],float)
                pnts = [(bins[hemi][0][pnt%nxx],bins[hemi][1][pnt/nyy]) for
                         pnt in envelope]
                pnts = NA(pnts,float)
                interior = interior_test(pnts, verts)
                the_fill = list(interior.ravel().nonzero()[0])
                the_fill = [list(pnts[x]) for x in the_fill]
                # Collapse the the_fill to gridIDs.
                xvals,yvals = zip(*the_fill)
                H, xedges, yedges = NHIS(NABS(NA(xvals)),NABS(NA(yvals)),bins=bins[2])
                indices = H.nonzero()
                the_fill = dict.fromkeys([j*nxx+i for i, j in
                    zip(indices[0],indices[1])],1)
                the_fill = the_fill.keys()
                # Add the contour itself
                the_fill.extend(the_path)
                # Exclude ATT values
                for en in entangled:
                    if en in center_att:
                        the_fill = [x for x in the_fill
                                if x not in center_att[en]]
                #Store everything as full res vertices
                #the_fill.extend([(bins[h][0][pnt%nxx],bins[h][1][pnt/nyy]) for
                #         pnt in the_path])
                # stores high res vertex of contour
                #fill.extend(c_objects[scon])
            else:
                # No Fill to be added.
                the_fill = the_path
                #Store everything as full res vertices
                #fill.extend(c_objects[scon])

            # Store results
            center_atts[primary] = [entangled,the_fill]
            if verbose:
                print "\t\t\tATTS (%d):" % (len(the_fill))
                print_col(the_fill,
                          indent_tag="\t\t\t\t",fmt="% 7d",
                          cols=5,width=10,sort_me=1)

            # Find Area
            area = [len(the_fill)*smooth_grid_area]
            center_atts_area[primary] = area[0]
            if verbose:
                print "\t\t\tATTS Area: %d" % (center_atts_area[primary])

            # Skip contours already included
            done.extend(entangled_cons)
        
        ## Plot what we've done so far
        #for h in range(2):
        #    figsize=(8,8)
        #    fig = plt.figure(figsize=figsize,frameon=True)
        #    ax = fig.add_subplot(1,1,1)
        #    image = m_map[h].contour(xx[h],yy[h],smooth_field[h],levels,colors='k')
        #    circles = [lat_bounds[h],2*lat_bounds[h]]
        #    image2 = plt.clabel(image,fontsize=5,inline=1,inline_spacing=0,fmt='%d')
        #    m_map[h].drawparallels(circles)
        #    m_map[h].drawmeridians([0.0])
        #    m_map[h].drawmeridians([180.0])
        #    m_map[h].fillcontinents(color='0.9')
        #    m_map[h].drawcoastlines(linewidth=0.25)
        #    for center in canidates[h]:
        #        if center in center_att:
        #            for a in center_att[center]:
        #                pnt_image = m_map[h].plot(a[0],a[1],'o',markersize=1.0,
        #                        markerfacecolor='red',markeredgecolor='red',
        #                        linewidth=1,zorder=1)
        #        if center in center_atts:
        #            aa = center_atts[center][1]
        #            for a in aa:
        #                 pnt_image = m_map[h].plot(a[0],a[1],'o',markersize=1.0,
        #                        markerfacecolor='cyan',markeredgecolor='cyan',
        #                        linewidth=1,zorder=1)
        #        # Draw Center
        #        cx,cy,h,cslp,clat,clon = center_places[center]
        #        pnt_image = m_map[h].plot(cx,cy,'s',markersize=5.0,
        #                    markerfacecolor='k',markeredgecolor='k',
        #                    linewidth=1,zorder=1)
        #        pnt_image = m_map[h].plot(cx,cy,'x',markersize=4.5,
        #                    markerfacecolor='k',markeredgecolor='white',
        #                    linewidth=1,zorder=1)
        #    ttitle = "%02d %02d %s %04d"
        #    ttitle = ttitle % (int(date_stamp[8:10]),int(date_stamp[6:8]),
        #                months[int(date_stamp[4:6])],int(date_stamp[:4]))
        #    ax.set_title(ttitle)
        #    pname = "%sca_%s_%04d_%02d_%s%s" % (plot_contours,hemis[h],
        #            clevs[1]-clevs[2],clevs[2],date_stamp,fig_format)
        #    fig.savefig(pname,dpi=144,facecolor='w',edgecolor='w',
        #            orientation='landscape',bbox_inches='tight',
        #            pad_inches=0.03)
        #    print "\tMade",pname
        #    plt.close('all')


        # Find the distance to nearest center for each center. This
        #   is done 2 ways. First exclude entangled centers from the
        #   calculation for any center so it's nearest center is one
        #   from a different system. The second way drops this requirement
        #   so entangled systems will likely have small distance to
        #   nearest centers. For isolated centers both distances are
        #   the same.
        center_seperation = {}
        for h in range(2):
            isolated = [center for center in canidates[h] if center not in
                        center_entangled]
            primaries = dict.fromkeys([center for center in canidates[h] if
                                       center in center_entangled and
                                       center ==
                                       center_entangled[center][0]],1)
            disentangled = primaries.keys()
            disentangled.extend(isolated)
            for center in canidates[h]:
                # Find the separation distances to all centers in this
                #   hemisphere.
                cen = NA((center_places[center][0],center_places[center][1]))
                all_dists = [SEP(cen,
                                 NA((center_places[pnt][0],center_places[pnt][1])))*0.001 
                             for pnt in canidates[h] if pnt != center]
                minvalue, minindex = min(izip(all_dists,count()))
                center_seperation[center] = [int(minvalue),-1,canidates[h][minindex],""]
                #
                # Repeat if this center in entangled with other but
                #   this time exclude the entangled centers to ensure
                #   the nearest center distance is with another system.
                # For non-entangled systems collapse entangled systems
                #   to their primary so that in effect we're acting like
                #   all systems have a single center
                if center in center_entangled:
                    entangled = center_entangled[center][1]
                    entangled.append(center)
                    all_dists = [SEP(cen, 
                                     NA((center_places[pnt][0],center_places[pnt][1])))*0.001 
                                for pnt in canidates[h] if pnt not in
                                 entangled]
                    minvalue, minindex = min(izip(all_dists,count()))
                    center_seperation[center][1] = int(minvalue)
                    center_seperation[center][3] = canidates[h][minindex]
                else:
                    all_dists = [SEP(cen,
                                 NA((center_places[pnt][0],center_places[pnt][1])))*0.001 
                             for pnt in disentangled if pnt != center]
                    minvalue, minindex = min(izip(all_dists,count()))
                    center_seperation[center][1] = int(minvalue)
                    center_seperation[center][3] = canidates[h][minindex]

        if save_hi_res:
            # Save full resolution data to file
            center_group = []
            empty_group = []
            atts_group = []
            for center in current_centers:
                if center in empty_centers: 
                    # Populate empty_group
                    empty_group.append(empty_group_fmt.format(readit.center_holder[center]))
                elif center in center_att:
                    # Populate center_group
                    fill_set = [len(center_att[center]),center_att_area[center],
                                center_att_perimeter[center],center_att_radius[center][0],
                                center_att_radius[center][1],center_att_radius[center][2],
                                center_att_depth[center],center_seperation[center][0],
                                center_seperation[center][1],center_seperation[center][2],
                                center_seperation[center][3]]
                    fill_set.append(" ".join(['%06d' % x 
                                              for x in center_att[center]]))
                    tmp = center_group_fmt.format(readit.center_holder[center])
                    tmp += " " + att_group_fmt.format(fill_set)
                    center_group.append(tmp)
                if center in center_atts:
                    # Populate atts_group
                    fill_set = [center,len(center_entangled[center]),
                                " ".join(center_entangled[center][1]),
                                len(center_atts[center]),center_atts_area[center],
                                center_atts_perimeter[center],center_atts_depth[center],
                                center_atts_radius[center][0],center_atts_radius[center][1],
                                center_atts_radius[center][2]]
                    fill_set.append(" ".join(['%06d' % x 
                                              for x in center_atts[center][1]]))
                    atts_group.append(atts_group_fmt.format(fill_set))
            # Problematic grids over troublesome regions.
            prob_group = problematic_fmt.format([""])
            # Dump to file
            att_save_hi.writelines(center_group)
            att_save_hi.writelines(empty_group)
            att_save_hi.writelines(atts_group)
            att_save_hi.write(prob_group)

        if save_source_res:
            # Collapse c_objects to gridIDs of the SLP source grid
            c_gridids = {}
            s_gridids = {}
            for center in center_att:
                h = center_places[center][2]
                verts = [(bins[h][0][pnt%nxx],bins[h][1][pnt/nyy]) for
                         pnt in center_att[center]]
                lonlat_pairs = [m_map[h](vertex[0],vertex[1],inverse=True) for
                        vertex in verts]
                the_path = dict.fromkeys([l2g(vertex[0],vertex[1],lons,lats,n)[0]
                                          for vertex in lonlat_pairs],1)
                c_gridids[center] = the_path.keys()
                #area = int(reduce(add,[darea[x] for x in c_gridids[center]]))
                #center_att_area[center][1] = area
            for center in center_atts:
                h = center_places[center][2]
                verts = [(bins[h][0][pnt%nxx],bins[h][1][pnt/nyy]) for
                         pnt in center_atts[center][1]]
                lonlat_pairs = [m_map[h](vertex[0],vertex[1],inverse=True) for
                        vertex in verts]
                the_path = dict.fromkeys([l2g(vertex[0],vertex[1],lons,lats,n)[0]
                                          for vertex in lonlat_pairs],1)
                s_gridids[center] = the_path.keys()
                #area = int(reduce(add,[darea[x] for x in s_gridids[center]]))
                #center_atts_area[center][1] = area
            # Save full resolution data to file
            center_group = []
            empty_group = []
            atts_group = []
            for center in current_centers:
                if center in empty_centers: 
                    # Populate empty_group
                    empty_group.append(empty_group_fmt.format(readit.center_holder[center]))
                elif center in center_att:
                    # Populate center_group
                    fill_set = [len(c_gridids[center]),center_att_area[center],
                                center_att_perimeter[center],center_att_radius[center][0],
                                center_att_radius[center][1],center_att_radius[center][2],
                                center_att_depth[center],center_seperation[center][0],
                                center_seperation[center][1],center_seperation[center][2],
                                center_seperation[center][3]]
                    fill_set.append(" ".join(['%06d' % x 
                                              for x in c_gridids[center]]))
                    tmp = center_group_fmt.format(readit.center_holder[center])
                    tmp += " " + att_group_fmt.format(fill_set)
                    center_group.append(tmp)
                if center in center_atts:
                    # Populate atts_group
                    fill_set = [center,len(center_entangled[center]),
                                " ".join(center_entangled[center][1]),
                                len(s_gridids[center]),center_atts_area[center],
                                center_atts_perimeter[center],center_atts_depth[center],
                                center_atts_radius[center][0],center_atts_radius[center][1],
                                center_atts_radius[center][2]]
                    fill_set.append(" ".join(['%06d' % x 
                                              for x in s_gridids[center]]))
                    atts_group.append(atts_group_fmt.format(fill_set))
            # Problematic grids over troublesome regions.
            prob_group = problematic_fmt.format([""])
            # Dump to file
            att_save.writelines(center_group)
            att_save.writelines(empty_group)
            att_save.writelines(atts_group)
            att_save.write(prob_group)

    #    ## Uncomment to plot consolidated contours (gridIDs)
    #    #if plot_contours:
    #    #    for h in range(2):
    #    #        figsize=(8,8)
    #    #        fig = plt.figure(figsize=figsize,frameon=True)
    #    #        ax = fig.add_subplot(1,1,1)
    #    #        image = m_map[h].contour(xx[h],yy[h],smooth_field[h],levels,colors='k')
    #    #        circles = [lat_bounds[h],2*lat_bounds[h]]
    #    #        image2 = plt.clabel(image,fontsize=5,inline=1,inline_spacing=0,fmt='%d')
    #    #        m_map[h].drawparallels(circles)
    #    #        m_map[h].drawmeridians([0.0])
    #    #        m_map[h].drawmeridians([180.0])
    #    #        m_map[h].fillcontinents(color='0.9')
    #    #        m_map[h].drawcoastlines(linewidth=0.25)
    #    #        done = {}
    #    #        for center in canidates[h]:
    #    #            if center in center_att:
    #    #                for a in center_att[center]:
    #    #                    if a in done:
    #    #                        continue
    #    #                    else:
    #    #                        done[a] = 1
    #    #                    pnt_x, pnt_y = bins[h][0][a%nxx],bins[h][1][a/nyy]
    #    #                    pnt_image = m_map[h].plot(pnt_x,pnt_y,'o',markersize=1.0,
    #    #                            markerfacecolor='red',markeredgecolor='red',
    #    #                            linewidth=1,zorder=1)
    #    #            if center in center_atts:
    #    #                aa = center_atts[center][1]
    #    #                for a in aa:
    #    #                    if a in done:
    #    #                        continue
    #    #                    else:
    #    #                        done[a] = 1
    #    #                    pnt_x, pnt_y = bins[h][0][a%nxx],bins[h][1][a/nyy]
    #    #                    pnt_image = m_map[h].plot(pnt_x,pnt_y,'o',markersize=1.0,
    #    #                            markerfacecolor='cyan',markeredgecolor='cyan',
    #    #                            linewidth=1,zorder=1)
    #    #        for center in canidates[h]:
    #    #            # Do last so not over written by att/atts
    #    #            # Draw Center
    #    #            cx,cy,h,cslp,clat,clon = center_places[center]
    #    #            pnt_image = m_map[h].plot(cx,cy,'s',markersize=5.0,
    #    #                        markerfacecolor='k',markeredgecolor='k',
    #    #                        linewidth=1,zorder=1)
    #    #            pnt_image = m_map[h].plot(cx,cy,'x',markersize=4.5,
    #    #                        markerfacecolor='k',markeredgecolor='white',
    #    #                        linewidth=1,zorder=1)
    #    #        ttitle = "%02d UTC %02d %s %04d"
    #    #        ttitle = ttitle % (int(date_stamp[8:10]),int(date_stamp[6:8]),
    #    #                    months[int(date_stamp[4:6])],int(date_stamp[:4]))
    #    #        ax.set_title(ttitle)
    #    #        pname = "%sc_%s_%04d_%02d_%s%s" % (plot_contours,hemis[h],
    #    #                clevs[1]-clevs[2],clevs[2],date_stamp,fig_format)
    #    #        fig.savefig(pname,dpi=144,facecolor='w',edgecolor='w',
    #    #                orientation='landscape',bbox_inches='tight',
    #    #                pad_inches=0.03)
    #    #        print "\tMade",pname
    #    #        plt.close('all')

        # Even if not plotting the contour call creates an object that is
        #   retained each loop and will cause large memory usage if not
        #   terminated with this call.
        plt.close('all')

        # Update progress file
        prog_save.write("%d\n" % (step))

    if save_hi_res:
        try:
            att_save_hi.close()
        except:
            sys.exit("\n\tWARNING: Error Closing %s." % (att_file_hi))
    if save_source_res:
        try:
            att_save.close()
        except:
            sys.exit("\n\tWARNING: Error Closing %s." % (att_file))
    try:
        prog_save.close()
    except:
        sys.exit("\n\tWARNING: Error Closing %s." % (prog_file))

    return

#---Start of main code block.
if __name__=='__main__':

    import pickle,sys,os

    plot_contours = 0

    # Save ATT etc using the projection grid (large, high resolution)
    save_hi_res = 1

    # Save ATT etc using the data source grid
    save_source_res = 1

    verbose = 0

    # Set contour levels and interval
    clevs=[940,1020,5]
    clevs=[900,1017,2]

    #fig_format = ".pdf"
    fig_format = ".png"
    #fig_format = ".eps"

    projs = ['laea','stere','aeqd']
    pmap = projs[0]
    mproj_sh = 'sp'+pmap
    mproj_nh = 'np'+pmap

    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------
    picks = {0 : "NCEP/NCAR Reanalysis 1",
             1 : "NCEP-DOE Reanalysis 2",
             2 : "NASA GISS GCM ModelE",
             3 : "GFDL GCM",
             4 : "ERA-Interim Reanalysis",
             5 : "ERA-40 Reanalysis"}
    pick = 1
    if pick not in picks:
        sys.exit("ERROR: pick not listed in picks.")

    # This next set of lines should be copied from setup_vX.py
    # Short names by which pick will be labeled.
    models = ["nra","nra2","giss","gfdl","erai","era40"]
    try:
        model = models[pick]
    except:
        sys.exit("ERROR: pick not listed in models.")

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    imports = ["import sys,os,math,netcdftime,numpy,stats"]
    imports.append("import matplotlib.pyplot as plt")
    imports.append("from mpl_toolkits.basemap import Basemap, shiftgrid, addcyclic, pyproj")
    imports.append("import matplotlib.nxutils as nx")
    imports.append("from matplotlib.path import Path")
    imports.append("import matplotlib.mlab as mlab")
    imports.append("import netCDF4 as NetCDF")
    imports.append("from operator import add")
    imports.append("from itertools import chain, count, izip")
    # My modules to import w/ version number appended.
    my_base = ["defs","l2g","first_last_lons","read_mcms"]
    if verbose:
        my_base.append("print_col")
    if plot_contours:
        my_base.append("plot_map")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)

    # To save a double copy of the data being retained by pull_data it is
    # necessary to reimport and delete pull_data_vX.py inside each loop.
    import_read = "import %s%s as %s" % ("pull_data",vnum,"pull_data")

    # --------------------------------------------------------------------------
    # Alter default behavior found in either defs_vX.py or setup_vX.py
    # --------------------------------------------------------------------------

    # The default behavior is to read SLP data from the
    # directory slp_path defined in setup_vX.py.
    # Here you can elect to override this behavior.
    over_write_slp_path = ""
    #over_write_slp_path = "/data/nra2/"

    # The default behavior is to save results
    # in the directory out_path defined in
    # setup_vX.py. Here you can elect to override
    # this behavior.
    over_write_out_path = ""
    #over_write_out_path = "/output/nra2/"

    # This next set of lines should be copied from setup_vX.py
    # Full path to the root directory where pick specific output will be stored.
    # Note it's possible that all of these directories are identical.
    # Uncomment to use unique structure for each model
    #result_directories = ["/output/","/output/"]
    # Uncomment to use same structure for all models
    #result_directories = ["/output/" for x in range(len(picks))]
    result_directories = ["/Volumes/scratch/output/" for x in range(len(picks))]
    # Uncomment to make current directory for all models
    #result_directories = [os.getcwd() for x in picks]
    try:
        result_directory = result_directories[pick]
        if not os.path.exists(result_directory):
            sys.exit("ERROR: result_directory not found.")
    except:
        sys.exit("ERROR: pick not listed in result_directories.")

    # Directory to be created for storing temporary pick specific files.
    shared_path = "%s%s_files/" % (result_directory,model)

    # The default behavior is to run over all the
    # years found by setup_vX.py. Here you can
    # elect to override this behavior.
    #over_write_years = ""
    #over_write_years = [1988,1988]
    #over_write_years = [1996,1996]

    # Get some definitions. Note must have run setup_vx.py already!
    sf_file = "%ss_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(sf_file))
        inputs = ["im","jm","maxid","lats","lons","timestep","dx","dy","dlon","dlat",
            "start_lat","start_lon","dlon_sq","dlat_sq","two_dlat","model_flag","eq_grid",
            "tropical_n","tropical_s","bot","mid","top","row_start","row_end",
            "tropical_n_alt","tropical_s_alt","bot_alt","top_alt","lon_shift","lat_flip",
            "the_calendar","found_years","super_years","dim_lat","dim_lon","dim_time",
            "var_lat","var_lon","var_time","var_slp","var_topo","var_land_sea_mask",
            "file_seperator","no_topo","no_mask","slp_path","model","out_path",
            "shared_path","lat_edges","lon_edges","land_gridids","troubled_centers",
            "faux_grids"]
        super_years = fnc_out[inputs.index("super_years")]
        out_path = fnc_out[inputs.index("out_path")]
        slp_path = fnc_out[inputs.index("slp_path")]
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s" % (sf_file))
    if over_write_years:
        super_years = over_write_years
    if over_write_out_path:
        out_path = over_write_out_path
    if over_write_slp_path:
        slp_path = over_write_slp_path

    # Create out_path if it doesn't exist.
    if not os.path.exists(out_path):
        dirs = map(os.makedirs, (out_path,
        out_path+'/comps/',
        out_path+'/pdfs/',
        out_path+'/stats/',
        out_path+'/stats/tmp/',
        out_path+'/netcdfs/',
        out_path+'/figs/pdfs/',
        out_path+'/figs/comps/'))
        print "\tDirectory %s Created." % (out_path)
    if plot_contours:
        plot_contours = out_path+'/figs/'

    defs_set = {}
    start_year = int(super_years[0])
    end_year = int(super_years[1])+1
    tail = "_tracks.txt"
    cut_tail = len(tail)
    header = "mcms_%s_%04d" % (model,start_year)
    in_file = "%s%s%s" % (out_path,header,tail)
    # Set definitions and instantiate read_mcms w/out a template
    what_do = {"model" : model,
                "in_file" : in_file,
                "out_file" : "",
                "just_center_table" : True,
                "detail_tracks" : 0,
                "as_tracks" : "",
                "start_time" : "YYYY MM DD HH SEASON",
                "end_time" : "YYYY MM DD HH SEASON",
                "places" : ["GLOBAL"],
                "include_atts" : 0,
                "include_stormy" : 0,
                "just_centers" : False,
                "save_output" : False,
                "overwrite" : False
                }
    # Pass in model definitions, if sf_file available this is simple.
    if model in ["nra","nra2"]:
        # For the NCAR/NCEP Reanalysis 1 and 2 these values are provided
        # and nothing need be done.
        pass
    else:
        # Provide values
        what_do["tropical_end"] = row_end[tropical_n_alt]
        what_do["tropical_start"] = row_start[tropical_s_alt]
        what_do["maxID"] = maxid
        what_do["land_gridids"] = land_gridids
    # Save ATT etc using the projection grid (large, high resolution)

  ##tmp
  #  print "Warning Not Running multiprocessing!"
  #  # TEST main w/o multiprocessing
  #  for loop_year in range(start_year,end_year):

  #      main(defs_set,imports,import_read,loop_year,
  #          out_path,shared_path,slp_path,clevs,what_do,
  #          plot_contours,save_hi_res,
  #          save_source_res,cut_tail,verbose)

  #      ## does a memory/time profile to find reason for slow downs etc.
  #      #import cProfile,pstats
  #      #msg = "main(defs_set,imports,import_read,loop_year,"
  #      #msg += "out_path,shared_path,slp_path,clevs,"
  #      #msg += "what_do,plot_contours,save_hi_res,save_source_res,cut_tail,verbose)"
  #      #cProfile.run(msg,sort=1,filename="h.cprof")
  #      #stats = pstats.Stats("h.cprof")
  #      #stats.strip_dirs().sort_stats('time').print_stats(20)

  #  import sys; sys.exit("all done")

    # --------------------------------------------------------------------------
    # Note on parallel processing
    # --------------------------------------------------------------------------

    # If you are running on a machine with multiple CPUs or multicore CPUs then
    # I will take advantage of that and speed things up a lot.

    # The form of parallelism used here is dumb brute force in that
    # I simply launch processes that work independently on part of
    # the problem and put it all back together when I'm done. This
    # is not MPI message passing or OpenMP shared memory.

    # Test requires python 2.6 or higher
    #
    # Test for python version with parallel processing capabilities.
    PROCESSORS =  1
    if sys.version_info >= (2, 6):
        import multiprocessing as mp
        PROCESSORS = mp.cpu_count()
    else:
        print "Parallelism requires python 2.6 or higher."
        print "If this isn't the case just run attribute_vX.py directly."
        sys.exit()

    # Can manually set processors by commenting out below
    PROCESSORS =  14

    # Don't breakup by less than 1 year per processor
    max_processors = (end_year-start_year)
    if PROCESSORS > max_processors:
        PROCESSORS = max_processors

    msg = "\n\tStarting %s%s (process id %s) with %d processors"
    print msg % ('pre_calculate_contours',vnum,os.getpid(),PROCESSORS)

    # -------------------------------------------------------------------------
    # Start Main Loop over super_years
    # -------------------------------------------------------------------------

    # Spawn n=PROCESSORS processes
    pool = mp.Pool(PROCESSORS)
    args_used = []
    results = []
    for loop_year in range(start_year,end_year):
        #Object holding objects (need array so not copies as messes with processes)
        args_used.append((defs_set,imports,import_read,loop_year,
            out_path,shared_path,slp_path,clevs,what_do,plot_contours,
            save_hi_res,save_source_res,cut_tail,verbose))
        result = pool.apply_async(main,args_used[-1],callback=results.append)
    pool.close()
    pool.join()
