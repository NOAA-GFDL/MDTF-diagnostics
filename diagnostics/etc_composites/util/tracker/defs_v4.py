"""
Module containing global (unchanging) parameters for the MCMS routines.
#/usr/bin/env python -tt

Usage: imported as a module not executable as stand alone.

Options:

Examples:

Notes: See bottom of this document
"""

# __author__  = "Mike Bauer  <mbauer@giss.nasa.gov>"
# __status__  = "beta"
# __version__ = "1.0 "+__status__
# __date__    = "Created: 6 June 2008        Updated: 6 June 2008"
#
# NOTES:
#
# 1) One can alter the default values when this object is instantiated.
#
#   import center_finder_defs as cfgd
#   use_defs = cfgd.defs(use_gcd=False)
#   print use_defs.use_gcd
#   > False
#
# 2) One can take advantage of the object-orientated nature of Python by
#    creating a whole new file, possibly with additional options, and
#    using inheritance.
#
#    in a new file called cf.py
#
#    import center_finder_defs
#    # create a new class inheriting from another
#    class defs(center_finder_defs):
#
#        def __init__(self,**kwargs):
#            """Create an instance
#            """
#
#            # use_gcd determines if the great circle or rhumbline method
#            # is to be used. Default is to use great circle distances (GCD)
#            if kwargs.in('use_gcd'):
#                self.use_gcd = kwargs['use_gcd']
#            else:
#                self.use_gcd = False
#
#            # Some new parameter with a default value of 10 if use_gcd is
#            # True else set to 0
#            if kwargs.in('NEW'):
#               self.NEW = kwargs['NEW']
#            else:
#               if self.use_gcd:
#                   self.NEW = 10
#               else:
#                   self.NEW = 0
#
#   Then use it as
#
#   import cfs as cfgd
#   use_defs = cfgd.defs(use_gcd=True)
#   print use_defs.NEW
#   > 10

#-------------------------------------------------------------------------
# Options and Defaults: Arranges such that the parameters mostly likely
#      to be altered by users are nearer the top of the file. Parameters
#      nearer the bottom are generally constants; like Earth's radius.
#-------------------------------------------------------------------------

def garbage():
  pass

class defs:
    "Class to hold global definitions"

    def __init__(self,**kwargs):
        """This is where the default values are set with the option to
           alter then upon instantiation.
        """

        # How to read this: the 'if' statement allows for keyword
        # arguments 'kwargs' to alter the default value when 'defs'
        # are called. Thus the parameter name 'pname' is all that's
        # required. The 'else' defines a default value for 'pname'
        # if 'pname' is not passed in 'kwargs'.
        #
        # if kwargs.in('pname'): # pname in quotes
        #   self.pname = kwargs['pname']
        #   # assign value from kwargs written as for example
        #   # pname=10.0. Here self.pname gets the value 10.0
        # else: # use default
        #   self.pname = 0.0
        #

        # Name: keep_log
        # Purpose: Store output to file rather than print to screen
        # Default: True
        #
        
        if 'keep_log' in kwargs:
            self.keep_log = kwargs['keep_log']
        else:
            self.keep_log = True

        # Name: accuracy
        # Purpose: Scales the source data to that it has a fixed
        #          accuracy as the data are used as integers.
        # Default: 1000 which takes an SLP in hPa and makes it accurate
        #          to 0.001 or a deci-Pascal
        if 'accuracy' in kwargs:
            self.accuracy = kwargs['accuracy']
        else:
            self.accuracy = 1000

        # Name: read_scale
        # Purpose: Scales the source data so units of Pa.
        # Default: 0.00001
        if 'read_scale' in kwargs:
            self.read_scale = kwargs['read_scale']
        else:
            self.read_scale = self.accuracy*0.00001
            self.read_scale = self.accuracy*0.001
        
        # Name: use_gcd
        # Purpose: determines if great circle or rhumbline method is to be
        #          used for distance calculations.
        # Default: True
        #
        # Note: The basic difference is great circles are better in general
        #       but they generally don't allow for a fixed angle between points.
        #       Rhumblines allow for a fixed course but the distances are longer
        #       than great circles generally and near the poles much longer and
        #       even wrap around the globe.
        #
        if 'use_gcd' in kwargs:
            self.use_gcd = kwargs['use_gcd']
        else:
            self.use_gcd = True

        # Name: fake_jd
        # Purpose: Use if netcdf of the source file does not use a standard
        #          calendar; for example no leap years.
        #
        # Default: False
        #
        # Note: When True timesteps are used instead of Julian Dates.
        #
        if 'fake_jd' in kwargs:
            self.fake_jd = kwargs['fake_jd']
        else:
            self.fake_jd = False

        # Name: faux_grids
        # Purpose: Origin of the grids as defined by the lat/lon values
        #           when the data is point_registered. That is, the data
        #           are not grid representative but instead point values.
        #   
        #   faux_grids = 0 Nothing done.
        #   faux_grids = 1 Use lon/lat to define grid centers and edges.
        #   faux_grids = 2 Same as 1 but create polar cap which is half-width.
        #   faux_grids = 3 Interpolate to make a grid
        #
        # Default: 0
        #
        # Note:
        #
        if 'faux_grids' in kwargs:
            self.faux_grids = kwargs['faux_grids']
        else:
            self.faux_grids = False

        # Name: keep_discards
        # Purpose: Store all centers that were found but not keep in the
        #          final result. The reason for their rejection is encoded so
        #          this acts as a kind of log for the center_finder process.
        # Default: True
        #
        if 'keep_discards' in kwargs:
            self.keep_discards = kwargs['keep_discards']
        else:
            self.keep_discards = True

        # Name: tropical_boundary
        # Purpose: Absolute latitude (degrees) bounding tropics. Mostly
        # used by center_finder.
        # Default: 15.0
        #
        if 'tropical_boundary' in kwargs:
            self.tropical_boundary = kwargs['tropical_boundary']
        else:
            self.tropical_boundary = 15.0

        # Name: tropical_boundary_alt
        # Purpose: Absolute latitude (degrees) bounding tropics. Mostly
        # used for tracking.
        # Default: 30.0
        #
        if 'tropical_boundary_alt' in kwargs:
            self.tropical_boundary_alt = kwargs['tropical_boundary_alt']
        else:
            self.tropical_boundary_alt = 30.0

        # Name: tropical_filter
        # Purpose: Speeds up searches by skipping the tropics. For now
        #          defined as bounded by tropical_boundary.
        # Default: True
        #
        if 'tropical_filter' in kwargs:
            self.tropical_filter = kwargs['tropical_filter']
        else:
            self.tropical_filter = True

        # Name: troubled_filter
        # Purpose: List of troublesome centers which flagged for
        #  special treatment.
        # Default: False
        #
        # Note:
        #
        if 'troubled_filter' in kwargs:
            self.troubled_filter = kwargs['troubled_filter']
        else:
            self.troubled_filter = False

        # Name: laplacian_filter
        # Purpose: Ignore potential centers that have weak SLP gradients
        # Default: True
        #
        if 'laplacian_filter' in kwargs:
            self.laplacian_filter = kwargs['laplacian_filter']
        else:
            self.laplacian_filter = True

        # Name: regional_slp_threshold
        # Purpose: Sets a minimum value to reject a center from being a regional
        #          minimum. Keeps something like a 0.01 hPa difference from re-
        #          jecting a potential center.
        # Default: 1 hPa
        #
        if 'regional_slp_threshold' in kwargs:
            self.regional_slp_threshold = kwargs['regional_slp_threshold']
        else:
            self.regional_slp_threshold = 1*self.accuracy

        # Name: critical_radius
        # Purpose: Sets the distance/radius for a center being considered
        #          a regional minimum.
        # Default: 720.0 km
        #
        # Note: if set to 0.0 then the radius is set by the wavenumber method
        #
        if 'critical_radius' in kwargs:
            self.critical_radius = kwargs['critical_radius']
        else:
            self.critical_radius = 720.0

        # Name: wavenumber
        # Purpose: Sets the distance/radius for a center being considered
        #          a regional minimum. This is done with the wavenumber so
        #          the radius changes with latitude.
        # Default: 13.0 (Center Finding/Tracking) and 4.0 for attribution.
        #
        # Note: Synoptic features span the range of wavenumber 4-13. If
        #       critical_radius is non-zero wavenumber is not used.
        #
        if 'wavenumber' in kwargs:
            self.wavenumber = kwargs['wavenumber']
        else:
            self.wavenumber = 13.0

        # Name: plim_filter
        # Purpose: Ignores all potential screens with a SLP above this
        #          value. If set to 0 no filtering is done. Note the
        #          value should be in hPa/mb as scaled by accuracy
        # Default: 0 (1020 hPa used in past)
        #
        if 'plim_filter' in kwargs:
            self.plim_filter = kwargs['plim_filter']*self.accuracy
        else:
            self.plim_filter = 0

        # Name: skip_polars
        # Purpose: Skip checks on centers at top/bottom most lat rows.
        # Default: True
        #
        if 'skip_polars' in kwargs:
            self.skip_polars = kwargs['skip_polars']
        else:
            self.skip_polars = True

        # Name: detached_filter
        # Purpose: Filters potential centers for only those that in theory
        #          could be tracked. That is, they have another center within
        #          travel distance 1 time step before or after the current time.
        # Default: True
        #
        if 'detached_filter' in kwargs:
            self.detached_filter = kwargs['detached_filter']*self.accuracy
        else:
            self.detached_filter = True

        # Name: polar_filter
        # Purpose: Ignore tracking when centers at latitudes where they could
        #          travel across a pole in a single timestep.
        # Default: True
        #
        if 'polar_filter' in kwargs:
            self.polar_filter = kwargs['polar_filter']*self.accuracy
        else:
            self.polar_filter = True

        # Name: max_cyclone_speed
        # Purpose: Sets maximum allowable cyclone propagation speed.
        #          Used to determine if two centers at different times
        #          could be part of the same system.
        # Default: 120.0 km/hr
        #
        if 'max_cyclone_speed' in kwargs:
            self.max_cyclone_speed = kwargs['max_cyclone_speed']
        else:
            self.max_cyclone_speed = 120.0

        # Name: maxdp
        # Purpose: Defines a "bomb" cyclone SLP tendency (hPa/hr).
        # Default: 40 hPa/24 hours
        #
        # Note: Must multiply by timestep
        if 'maxdp' in kwargs:
            self.maxdp = kwargs['maxdp']
        else:
            self.maxdp = (40.0*self.accuracy)/24.0

        # Name: travel_distance
        # Purpose: Defines maximum allowed travel distance
        # Default: max_cyclone_speed*timestep (km)
        #
        # Note: Must multiply by timestep
        if 'travel_distance' in kwargs:
            self.travel_distance = kwargs['travel_distance']
        else:
            self.travel_distance = self.max_cyclone_speed

        # Name: min_trk_travel
        # Purpose: Defines minimum allowed total lifetime travel distance.
        # Default: 200.0 km
        #
        if 'min_trk_travel' in kwargs:
            self.min_trk_travel = kwargs['min_trk_travel']
        else:
            self.min_trk_travel = 200.0

        # Name: max_coarse
        # Purpose: Defines maximum allowed course change
        # Default: 95 degrees
        #
        if 'max_coarse' in kwargs:
            self.max_coarse = kwargs['max_coarse']
        else:
            self.max_coarse = 95

        # Name: age_limit
        # Purpose: Defines minimum allowed track lifetime.
        # Default: 24.0 hours
        #
        if 'age_limit' in kwargs:
            self.age_limit = kwargs['age_limit']
        else:
            self.age_limit = 24.0

        # Name: keep_slp
        # Purpose: Defines minimum lifetime SLP a track must reach.
        # Default: 1010 hPa
        #
        if 'keep_slp' in kwargs:
            self.keep_slp = kwargs['keep_slp']
        else:
            self.keep_slp = 1010*self.accuracy

        # Name: min_contour
        # Purpose: Defines minimum SLP contour for Attribution searches. All
        # lower SLP values are placed in this contour.
        # Default: 940 hPa
        #
        if 'min_contour' in kwargs:
            self.min_contour = kwargs['min_contour']
        else:
            self.min_contour = 940*self.accuracy

        # Name: max_contour
        # Purpose: Defines maximum SLP contour for Attribution searches. All
        # higher SLP values are placed in this contour.
        # Default: 1013 hPa, 1015 hPa and 1020 hPa have been used.
        #
        if 'max_contour' in kwargs:
            self.max_contour = kwargs['max_contour']
        else:
            self.max_contour = 1015*self.accuracy

        # Name: interval
        # Purpose: Defines contour interval for Attribution searches.
        # Default: 5.0 hPa (Caution small value allows for many problems,keep about 2 hPa).
        #
        if 'interval' in kwargs:
            self.interval = kwargs['interval']
        else:
            self.interval = int(5.0*self.accuracy)

        # Name: z_anomaly_cutoff
        # Purpose: Defines minimum value at which the zonal anomaly is
        #          deep enough to allow grids use for Attribution searches.
        # Default: -10.0 hPa (should be something like interval)
        #
        if 'z_anomaly_cutoff' in kwargs:
            self.z_anomaly_cutoff = kwargs['z_anomaly_cutoff']
        else:
#            self.z_anomaly_cutoff = int(-10.0*self.accuracy)
            self.z_anomaly_cutoff = int(-5.0*self.accuracy)
#            self.z_anomaly_cutoff = int(-0.01*self.accuracy)

        # Name: check_flare
        # Purpose: Defines minimum number of grids in a system before
        #          the flare and inflation tests applied.
        # Default: 25
        #
        if 'check_flare' in kwargs:
            self.check_flare = kwargs['check_flare']
        else:
            self.check_flare = 25

        # Name: check_inflate
        # Purpose: Defines minimum center SLP to apply
        #          the inflation test.
        # Default: 1000 hPa
        #
        if 'check_inflate' in kwargs:
            self.check_inflate = kwargs['check_inflate']
        else:
            self.check_inflate = int(1000.0*self.accuracy)

        # Name: inflated
        # Purpose: Maximum ratio of new grids being added
        #          to a center with pre-existing grids.
        # Default: 5
        #
        # Note: So the if new_grids/old_girds >= inflated
        # it is likely that the attributed contours are
        # running along a wide shallow slp field which
        # if left unchecked result in huge attributed storms.
        # Almost always occurs with weak lows (SLPs > 1000 hPa).
        if 'inflated' in kwargs:
            self.inflated = kwargs['inflated']
        else:
            self.inflated = 5.0

        # Name: find_highs
        # Purpose: Find slp maximums/highs instead of minimas/lows.
        # Default: False
        #
        # Note: EXPERIMENTAL and not well tested.
        #
        if 'find_highs' in kwargs:
            self.find_highs = kwargs['find_highs']
        else:
            self.find_highs = False

        # Name: earth_radius
        # Purpose: constant
        # Default: 6371.2 km
        #
        self.earth_radius = 6371.2

        # Name: inv_earth_radius_sq
        # Purpose: constant
        # Default:
        #
        self.inv_earth_radius_sq = 1.0/(self.earth_radius*self.earth_radius)

        # Name: two_deg_lat
        # Purpose: constant
        # Default: 111.0 km squared
        #
        self.two_deg_lat = 111.0*111.0

        # Name: usi_template
        # Purpose: place holder prior to tracking
        # Default: "00000000000000000000"
        #
        self.usi_template = "00000000000000000000"

        # Name: center_fmt
        # Purpose: Format statement for writing center to file
        # Default:
        #

        # Jeyavinoth: Since I changed the adate values, I have more than 9 characters for it, 
        # my adates has 12 characters
        # So I change the line below: 
        # fmt_1 = "%4d %02d %02d %02d %09d %05d %05d %06d %07d "
        # to: 
        fmt_1 = "%4d %02d %02d %02d %09d %05d %05d %06d %07d " # since adates is in days *100, I leave the formula as is

        fmt_2 = "%07d %05d %02d %02d %04d %4d%02d%02d%02d%05d%05d %s\n"
        self.center_fmt = fmt_1 + fmt_2

        # Name: center_fmt2
        # Purpose: Version of center_fmt
        # Default:
        #
        fmt_2 = "%07d %05d %02d %02d %04d %s %s\n"
        self.center_fmt2 = fmt_1 + fmt_2

        # Name: intensity_fmt
        # Purpose: Format statement for writing intensity to file
        # Default:
        #
        self.intensity_fmt = "%6s %s %07d %07d %07d %07d %d\n"

        # Name: seasons
        # Purpose: Define various seasons for screening.
        # Default:
        #
        seasons = {}
        seasons["djf"]    = [1,1,0,0,0,0,0,0,0,0,0,1]
        seasons["mam"]    = [0,0,1,1,1,0,0,0,0,0,0,0]
        seasons["jja"]    = [0,0,0,0,0,1,1,1,0,0,0,0]
        seasons["son"]    = [0,0,0,0,0,0,0,0,1,1,1,0]
        seasons["ndjfma"] = [1,1,1,1,0,0,0,0,0,0,1,1]
        seasons["mjjaso"] = [0,0,0,0,1,1,1,1,1,1,0,0]
        self.seasons = seasons

        # Name: seasons_pick
        # Purpose: method for selecting seasons
        # Default:
        #
        self.season_pick = ["djf","djf","mam","mam","mam","jja","jja","jja",
                            "son","son","son","djf"]

        self.center_data = [('YYYY'        , 'int64'),
                            ('MM'          , 'int64'),
                            ('DD'          , 'int64'),
                            ('HH'          , 'int64'),
                            ('JD'          , 'int64'),
                            ('CoLat'       , 'int64'),
                            ('Lon'         , 'int64'),
                            ('GridID'      , 'int64'),
                            ('GridSLP'     , 'int64'),
                            ('RegSLP'      , 'int64'),
                            ('GridLAP'     , 'int64'),
                            ('Flags'       , 'int64'),
                            ('Intensity'   , 'int64'),
                            ('Disimularity', 'int64'),
                            ('UCI'         , 'S20'),
                            ('USI'         , 'S20')]

