# use python2.5 setup_rhumb_line_nav.py build_ext --inplace
cdef extern from "math.h":
    double sin(double x)
    double cos(double x)
    double atan2(double y, double x)
    double log(double x)
    double tan(double x)
    double sqrt(double x)
    double pow(double x, int y)

def rhumb_line_nav(double lon2,lat2,lon1,lat1,distance=False):
    """
    The true course between the points (lat1,lon1), (lat2,lon2)
    is given by Rhumb Line Navigation.

    true_course = mod(atan2(lon1-lon2,
                      log(tan(lat2/2+pi/4)/tan(lat1/2+pi/4))),2*pi)
    Angle is measured clockwise from north 0 degrees, east 90 degrees etc.

    NOTES: Rhumb lines follow a spiral on the globe and are least simular
    (i.e, longer) when two ends are co-latitude and most simular when the
    two ends are co-longitude. Rhumb lines spiral very tightly at high
    latitudes which can result in comparatively long distances between
    points. Rhumb lines need special treatment if the coarse crosses the
    dateline.
    """

    cdef double lon1r,lat1r,lon2r,lat2r,dphi,dlon_w,dlon_e,d,q,TOL,bearing,de

    TOL =  1e-15 # small number to avoid 0/0 indeterminacies on E-W courses.
    d = 0.0
    q = 0.0

    # Ensure that longitude in +-180 form
    if lon1 > 180.0:
        lon1 = lon1 - 360.0
    if lon2 > 180.0:
        lon2 = lon2 - 360.0
##     # Ensure that longitude in 360 form
##     if lon1 < 0.0:
##         lon1 = lon1 + 360.0
##     if lon2 < 0.0:
##           lon2 = lon2 + 360.0

    lon1r = lon1*0.0174532925
    lat1r = lat1*0.0174532925
    lon2r = lon2*0.0174532925
    lat2r = lat2*0.0174532925

    tmp = lon1r-lon2r
    dlon_w = tmp%6.28318531
    tmp = lon2r-lon1r
    dlon_e = tmp%6.28318531
##    # for some reason fmod won't return correct answer for dlon_w
##    dlon_w = fmod(lon2r-lon1r,6.28318531)
##    dlon_e = fmod(lon1r-lon2r,6.28318531)
    dphi = log(tan(lat2r*0.5 + 0.7853981625) /
                 tan(lat1r*0.5 + 0.7853981625))

    if distance:
        if abs(lat2r-lat1r) < sqrt(TOL):
            q = cos(lat1r)
        else:
            q = (lat2r-lat1r)/dphi

    if dlon_w < dlon_e:
        # Westerly rhumb line is the shortest
        tmp = atan2(-1.0*dlon_w,dphi)
        bearing = tmp%6.28318531
        if distance:
            d  = sqrt(pow(q,2)*pow(dlon_w,2) + pow((lat2r-lat1r),2))
    else:
        tmp = atan2(dlon_e,dphi)
        bearing = tmp%6.28318531
        if distance:
            d  = sqrt(pow(q,2)*pow(dlon_e,2) + pow((lat2r-lat1r),2))

    # Convert to the +-2pi (0-360) system
    tmp = bearing+6.28318531
    bearing = tmp%6.28318531

    # Convert to degrees
    bearing = bearing * 57.2957795

##     # Convert to 0-360 format
##     if bearing < 0.0:
##         bearing = bearing + 360.0

##     # This formula was written assuming West longitudes are positive
##     # so I reverse the bearing orientation for the usual convention.
##     # That is, compensate for unit circle orientation so 270 is to west not east
##     bearing = 360.0 - bearing

##     if bearing == 360.0:
##         bearing = 0.0

    if distance:
        # convert from distance in radians to nautical miles to km
        d = d*((180.0*60.0)/3.14159265)
        d = d*1.852
        return bearing,d
    else:
        return bearing

# tests
##     lon1 = 0.0
##     lat1 = 0.0
##     lon2 = -100.0
##     lat2 = 0.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2 
##     print "bearing",rln(lon2,lat2,lon1,lat1,True) 
##     print ""
    
##     lon1 = 0.0
##     lat1 = 0.0
##     lon2 = 100.0
##     lat2 = 0.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
     
##     lon1 = 0.0
##     lat1 = 0.0
##     lon2 = 0.0
##     lat2 = 80.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
    
##     lon1 = 0.0
##     lat1 = 0.0
##     lon2 = 0.0
##     lat2 = -80.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
    
##     lon1 = 0.0
##     lat1 = 0.0
##     lon2 = 179.9
##     lat2 = 0.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
    
##     lon1 = 0.0
##     lat1 = 0.0
##     lon2 = -179.9
##     lat2 = 0.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
    
##     lon1 = 0.0
##     lat1 = -90.0
##     lon2 = 0.0
##     lat2 = 90.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
    
##     lon1 = 0.0
##     lat1 = -40.0
##     lon2 = -145.0+360
##     lat2 = -45.0
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     print "bearing",rln(lon2,lat2,lon1,lat1,True)
##     print ""
    
## ##    Suppose point 1 is LAX: (33deg 57min N, 118deg 24min W)
## ##    Suppose point 2 is JFK: (40deg 38min N,  73deg 47min W)

##     lat1 = 0.592539*57.2957795
##     lon1 = -2.066470*57.2957795
##     lat2 = 0.709185*57.2957795
##     lon2 = -1.287762*57.2957795
##     print "lon,lat",lon1,lat1,"->",lon2,lat2
##     fnc = []
##     fnc = rln(lon2,lat2,lon1,lat1,True)
##     print fnc
##     print "bearing",round(fnc[0],2),round(fnc[1])
## # tc 79.32 degrees
## #  2164.6 nm
