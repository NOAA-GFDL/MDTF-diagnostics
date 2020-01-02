import numpy as np
import os.path
import math
import sys

###   linear regression  gives a and b as  y = ax + b
##def fit( x, y, ndata, a, b, siga, sigb, chi2, q):
def fit( x, y, ndata, a, b):
    
    
    sx = 0.
    sy = 0.
    st2 = 0.
    b = 0.
    
    for i in range( 0, ndata):
        sx = sx + x[i]
        sy = sy + y[i]
    ss = float(ndata)
    sxoss = sx/ss
        
    for i  in range( 0, ndata):
        t = x[i] - sxoss
        st2 = st2 + t*t
        b = b + t*y[i]
    b= b/st2
    a = (sy - sx*b)/ss
    siga = math.sqrt( (1. + (sx*sx)/(ss*st2)) /ss)    
    sigb = math.sqrt( 1./st2)

    chi2 = 0.
    for i  in range( 0, ndata):
        chi2 = chi2 + (y[i] - a - b*x[i])* (y[i] - a - b*x[i])
    q = 1.
    sigdat = math.sqrt( chi2/float( ndata-2)) 
    siga = siga * sigdat
    sigb = sigb * sigdat
    
    return a, b
##    return a, b,     siga, sigb, chi2, q
########################
import numpy as np
import os.path
import math
import sys

###   
def gammln( xx):
    cof = [76.180091730,-86.505320330,24.014098220, -1.2317395160,0.120858003E-2,-0.536382E-5 ]
    stp = 2.506628274650
    half = 0.50
    one = 1.0
    fpf = 5.50
    
    x = xx - one
    tmp = x + fpf
    tmp = (x+half) * math.log(tmp)  - tmp
    ser = one

    for j in range (0, 6):
        x = x + one
        ser = ser + cof[n]/x
    gammln = tmp + math.log(stp*ser)
    return gammln 
import numpy as np
import os.path
import math
import sys

###   
def gammq( a, x):
    if( x < (a+1.)):
        gamser = gser( gamser, z, x, gln)
        gammq = 1. - gamser
    else:
        gammcf = gcf( gammcf, a, x, gln)
        gammq = gammcf
    
    return gammq
import numpy as np
import os.path
import math
import sys

###   read in data and make composite average - full  values (not anomaly !!)
def gcf( gammcf, a, x, gln):
    itmax = 100
    eps = 3.5E-07
    gln = gammln(a)
    gold = 0.
    a0 = 1.
    a1 = x
    b0 = 0.
    b1 = 1.
    fac = 1.
    
    for n in range( 0, itmax):
        ann = float( n) 
        ana = an - a
        a0 = (a1 + a0 * ana) * fac
        b0 = (b1 + b0 * ana) * fac
        anf = an * fac
        a1 = x*a0 + anf*a1
        b1 = x*b0 + anf*b1
        if( a1 != 0.):
            fac = 1./a1
            g = b1 * fac
            if( math.fabs((g-gold)/g)  < eps):
                break
            gold = g

    gammcf =  math.exp( -x + a* math.log(x) - gln)* g
    return gammcf
import numpy as np
import os.path
import math
import sys

###   read in data and make composite average - full  values (not anomaly !!)
def gser( gamser, a, x, gln):
    itmax = 100
    eps = 3.5E-07
    gln = gammln(a)

    if( x <= 0.):
        gamser = 0.
        return gamser
    ap = a
    summ = 1./a
    dell = summ
    for n in range( 0, itmax):
        ap = ap + 1.
        dell = dell * x/ap
        summ = summ + dell
        if( math.fabs(dell) < math.fabs(summ)*eps):
            break
    gamser = summ * math.exp( -x  + a * math.log(x) - gln)
    return gamser
