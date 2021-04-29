# use python2.4 setup_gcd.py build_ext --inplace

cdef extern from "math.h":
    double sin(double x)
    double cos(double x)
    double atan2(double y, double x)
    double sqrt(double x)
    double pow(double x, double y)

def gcd(double lona,lata,lonb,latb):
    xlona = lona*0.0174532925
    xlata = lata*0.0174532925
    xlonb = lonb*0.0174532925
    xlatb = latb*0.0174532925
    sin_lata = sin(xlata)
    sin_latb =  sin(xlatb)
    cos_lata = cos(xlata)
    cos_latb = cos(xlatb)
    cos_delta_lon = cos(xlonb - xlona)
    sin_delta_lon = sin(xlonb - xlona)
    d = atan2(sqrt(pow(cos_latb * sin_delta_lon,2) + pow(cos_lata * sin_latb -
                  sin_lata * cos_latb * cos_delta_lon,2)),
                  sin_lata * sin_latb + cos_lata * cos_latb * cos_delta_lon)*6372.795
    return d
