'''

PURPOSE: To bin 3D depending on user preference

AUTHOR: Fiaz Ahmed

DATE:   05/6
 
'''

import numpy as np
cimport numpy as np
from libc.math cimport abs,exp, pow, log
import cython

DTYPE = np.float
DTYPE1 = np.int
ctypedef np.float_t DTYPE_t
ctypedef np.int_t DTYPE1_t

cdef extern from "math.h":
    bint isfinite(double x)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
 
 

            
def bin_vert_struct(np.ndarray[DTYPE1_t, ndim=1] lev,np.ndarray[DTYPE1_t, ndim=1] zind,np.ndarray[DTYPE1_t, ndim=1] aind,
np.ndarray[DTYPE1_t, ndim=1] wind,np.ndarray[DTYPE_t, ndim=2] xt,np.ndarray[DTYPE_t, ndim=2] yq,
np.ndarray[DTYPE_t, ndim=4] op1, np.ndarray[DTYPE_t, ndim=4] op2, np.ndarray[DTYPE_t, ndim=4] op3):

    cdef unsigned int vector_size = zind.size
    cdef unsigned int ht_size = lev.size
        
    cdef Py_ssize_t i,j
    
    for i in range(vector_size-1):
        for j in range(lev.size-1):
            
            op1[j,zind[i],aind[i],wind[i]]+=xt[j,i]
            op2[j,zind[i],aind[i],wind[i]]+=yq[j,i]
            op3[i,zind[i],aind[i],wind[i]]+=1
            


def vert_integ_variable_bl(np.ndarray[DTYPE_t, ndim=2] var,
np.ndarray[DTYPE_t, ndim=1] var_ps,
np.ndarray[DTYPE_t, ndim=2] var1,
np.ndarray[DTYPE1_t, ndim=1] pbl_ind,
np.ndarray[DTYPE_t, ndim=1] lev, 
np.ndarray[DTYPE_t, ndim=2] dp,
 
np.ndarray[DTYPE_t, ndim=1] op1,
np.ndarray[DTYPE_t, ndim=1] op2,
np.ndarray[DTYPE_t, ndim=1] op3,
np.ndarray[DTYPE1_t, ndim=1] ind_low):

    cdef unsigned int vector_size = len(var_ps)
    cdef unsigned int ht_size = len(lev)

    cdef Py_ssize_t i,j,ind,il,ctr
    cdef Py_ssize_t im

    for i in range(vector_size):
  
        ind=pbl_ind[i]
        il=ind_low[i]
        op1[i]=var_ps[i]
  
        for j in range(ht_size-1):

        ## PBL ##            
            if j>=ind:
                op1[i]+=var[j,i]*dp[j,i]

        ## Mid and low-level ##
            if (j<ind) & (j>=il):
                op2[i]+=var[j,i]*dp[j,i]
                op3[i]+=var1[j,i]*dp[j,i]
                
def vert_integ_variable_bl(np.ndarray[DTYPE_t, ndim=2] var,
np.ndarray[DTYPE_t, ndim=1] var_ps,
np.ndarray[DTYPE_t, ndim=2] var1,
np.ndarray[DTYPE1_t, ndim=1] pbl_ind,
np.ndarray[DTYPE_t, ndim=1] lev, 
np.ndarray[DTYPE_t, ndim=2] dp,
 
np.ndarray[DTYPE_t, ndim=1] op1,
np.ndarray[DTYPE_t, ndim=1] op2,
np.ndarray[DTYPE_t, ndim=1] op3,
# np.ndarray[DTYPE_t, ndim=1] op4,
# np.ndarray[DTYPE_t, ndim=1] op5,
# DTYPE1_t ind_mid,
np.ndarray[DTYPE1_t, ndim=1] ind_low):

    cdef unsigned int vector_size = len(var_ps)
    cdef unsigned int ht_size = len(lev)

    cdef Py_ssize_t i,j,ind,ctr
    cdef Py_ssize_t il,im
                    
    for i in range(vector_size):
    
        ind=pbl_ind[i]
        il=ind_low[i]
        op1[i]=var_ps[i]
        
        for j in range(ht_size-1):

            ## PBL ##            
            if j>=ind:
                op1[i]+=var[j,i]*dp[j,i]

            ## Low-level ##
            if (j<ind) & (j>=il):
                op2[i]+=var[j,i]*dp[j,i]
                op3[i]+=var1[j,i]*dp[j,i]
 
            ## Mid-level ##
#             if (j<il) & (j>=im):
#                 op4[i]+=var[j,i]*dp[j,i]
#                 op5[i]+=var1[j,i]*dp[j,i]
            

def vert_integ_exneri_variable_bl(np.ndarray[DTYPE_t, ndim=2] var,
np.ndarray[DTYPE_t, ndim=1] var_ps,
np.ndarray[DTYPE1_t, ndim=1] pbl_ind,
np.ndarray[DTYPE_t, ndim=1] lev, 
np.ndarray[DTYPE_t, ndim=2] dp,
 
np.ndarray[DTYPE_t, ndim=1] op1,
np.ndarray[DTYPE_t, ndim=1] op2,
np.ndarray[DTYPE1_t, ndim=1] ind_low):

    cdef unsigned int vector_size = len(var_ps)
    cdef unsigned int ht_size = len(lev)

    cdef Py_ssize_t i,j,ind,ctr
    cdef Py_ssize_t il
    
                
    for i in range(vector_size):
    
        ind=pbl_ind[i]
        il=ind_low[i]
        op1[i]=var_ps[i]
        
        for j in range(ht_size-1):

            ## PBL ##            
            if j>=ind:
                op1[i]+=var[j,i]*dp[j,i]

            ## Low-level ##
            if (j<ind) & (j>=il):
                op2[i]+=var[j,i]*dp[j,i]
 

def vert_integ_lt_variable_bl(np.ndarray[DTYPE_t, ndim=2] var1,
np.ndarray[DTYPE_t, ndim=2] var2,
np.ndarray[DTYPE1_t, ndim=1] pbl_ind,
np.ndarray[DTYPE_t, ndim=1] lev, 
np.ndarray[DTYPE_t, ndim=2] dp,
 
np.ndarray[DTYPE_t, ndim=1] op1,
np.ndarray[DTYPE_t, ndim=1] op2,
np.ndarray[DTYPE1_t, ndim=1] ind_low):

    cdef unsigned int vector_size = len(pbl_ind)
    cdef unsigned int ht_size = len(lev)

    cdef Py_ssize_t i,j,ind,ctr
    cdef Py_ssize_t il
    
                
    for i in range(vector_size):
    
        ind=pbl_ind[i]
        il=ind_low[i]
        
        for j in range(ht_size-1):

            ## Low-level ##
            if (j<ind) & (j>=il):
                op1[i]+=var1[j,i]*dp[j,i]
                op2[i]+=var2[j,i]*dp[j,i]
                
                
def find_closest_index(np.ndarray[DTYPE_t, ndim=1] pres,
np.ndarray[DTYPE_t, ndim=1] lev,
np.ndarray[DTYPE1_t, ndim=1] ind_lev):

    cdef unsigned int vector_size = len(pres)
    cdef unsigned int ht_size = len(lev)
    cdef double delta1,delta2

    cdef Py_ssize_t i,j
    
    for i in range(vector_size):
        ind_lev[i]=0
        for j in range(ht_size-1):
            delta1=abs(lev[ind_lev[i]]-pres[i])
            delta2=abs(lev[j]-pres[i])
            if (delta2<delta1):
                ind_lev[i]=j
                
                
def find_closest_index_2D(np.ndarray[DTYPE_t, ndim=1] pres,
np.ndarray[DTYPE_t, ndim=2] lev,
np.ndarray[DTYPE1_t, ndim=1] ind_lev):

    cdef unsigned int vector_size, height_size
    cdef double delta1,delta2

    cdef Py_ssize_t i,j
    
    ht_size = lev.shape[0]
    vector_size = lev.shape[1]
    
    for i in range(vector_size):
        ind_lev[i]=0
        for j in range(ht_size-1):
            delta1=abs(lev[ind_lev[i],i]-pres[i])
            delta2=abs(lev[j,i]-pres[i])
            if (delta2<delta1):
                ind_lev[i]=j


cdef es_calc_bolton(double temp):
    # in hPa

    cdef double tmelt  = 273.15
    cdef double tempc, es  
    tempc = temp - tmelt 
    es = 6.112*exp(17.67*tempc/(243.5+tempc))
    return es


cdef es_calc(double temp):

    cdef double tmelt  = 273.15
    cdef double tempc,tempcorig 
    cdef double c0,c1,c2,c3,c4,c5,c6,c7,c8
    cdef double es
    
    c0=0.6105851e+03
    c1=0.4440316e+02
    c2=0.1430341e+01
    c3=0.2641412e-01
    c4=0.2995057e-03
    c5=0.2031998e-05
    c6=0.6936113e-08
    c7=0.2564861e-11
    c8=-.3704404e-13

    tempc = temp - tmelt 
    tempcorig = tempc
    
    if tempc < -80:
        # in hPa
        es=es_calc_bolton(temp)
    else:
        # in Pa: convert to hPa
        es=c0+tempc*(c1+tempc*(c2+tempc*(c3+tempc*(c4+tempc*(c5+tempc*(c6+tempc*(c7+tempc*c8)))))))
        es=es/100
    
    return es

cdef esi_calc(double temp):
    cdef double esi
    esi = exp(23.33086 - (6111.72784/temp) + (0.15215 * log(temp)))
    return esi
    
cdef qs_calc(double press_hPa, double temp):

    cdef double tmelt  = 273.15
    cdef double RV=461.5
    cdef double RD=287.04
    cdef double EPS, press, tempc, es, qs

    EPS=RD/RV

    press = press_hPa * 100. 
    tempc = temp - tmelt 

    es=es_calc(temp) 
    es=es * 100. #hPa
    qs = (EPS * es) / (press + ((EPS-1.)*es))
    return qs

cdef theta_e_calc (double press_hPa, double temp, double q):

    cdef double pref = 100000.
    cdef double tmelt  = 273.15
    cdef double CPD=1005.7
    cdef double CPV=1870.0
    cdef double CPVMCL=2320.0
    cdef double RV=461.5
    cdef double RD=287.04
    cdef double EPS=RD/RV
    cdef double ALV0=2.501E6
    cdef double press, tempc,theta_e
    cdef double r,ev_hPa, TL, chi_e
    
    press = press_hPa * 100. # in Pa
    tempc = temp - tmelt # in C

    r = q / (1. - q)

    # get ev in hPa 
    ev_hPa = press_hPa * r / (EPS + r)

    #get TL
    TL = (2840. / ((3.5*log(temp)) - (log(ev_hPa)) - 4.805)) + 55.

    #calc chi_e:
    chi_e = 0.2854 * (1. - (0.28*r))

    theta_e = temp * pow((pref / press),chi_e) * exp(((3.376/TL) - 0.00254) * r * 1000. * (1. + (0.81 * r)))
    return theta_e

def compute_layer_thetae(np.ndarray[DTYPE_t, ndim=2] temp, np.ndarray[DTYPE_t, ndim=2] q,
np.ndarray[DTYPE_t, ndim=2] lev, 
np.ndarray[DTYPE1_t, ndim=1] ind_pbl_top, np.ndarray[DTYPE1_t, ndim=1] ind_pmid,
np.ndarray[DTYPE_t, ndim=1] thetae_bl, np.ndarray[DTYPE_t, ndim=1] thetae_lt,
np.ndarray[DTYPE_t, ndim=1] thetae_sat_lt, np.ndarray[DTYPE_t, ndim=1] wb):

    cdef unsigned int vector_size, height_size
    cdef Py_ssize_t i,j
    cdef double pres_hPa, qs, thetae, thetae_sat, dp1, dp2
    cdef double pbl_thickness, lt_thickness
    
    ht_size = lev.shape[0]
    vector_size = lev.shape[1]
    
    for j in range(vector_size):

        pbl_thickness=(lev[0,j]-lev[ind_pbl_top[j],j])
        lt_thickness=(lev[ind_pbl_top[j],j]-lev[ind_pmid[j],j])

#         if (lt_thickness>20000): 
        if (lt_thickness>5000): 

            wb[j]=(pbl_thickness/lt_thickness)*log((pbl_thickness+lt_thickness)/pbl_thickness)
        
            for i in range(ht_size):
        
                if (i<=ind_pmid[j]):
            
                    pres_hPa=lev[i,j]/100 # convert to hPa
                    qs= qs_calc(pres_hPa,temp[i,j])        
                    thetae=theta_e_calc(pres_hPa, temp[i,j], q[i,j])

                    dp1=lev[i,j]-lev[i+1,j]

                    if(i<ind_pbl_top[j]):
                
                        if(i==0):
                            thetae_bl[j]+=thetae*dp1/2
                        elif (i>0) & (i<ind_pbl_top[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_bl[j]+=thetae*(dp1+dp2)/2
                                                 
                    else:
                        thetae_sat=theta_e_calc(pres_hPa, temp[i,j], qs)
 
                        if(i==ind_pbl_top[j]):

                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_bl[j]+=thetae*(dp2)/2

                            thetae_lt[j]+=thetae*dp1/2
                            thetae_sat_lt[j]+=thetae_sat*dp1/2

                        elif (i>ind_pbl_top[j]) & (i<ind_pmid[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_lt[j]+=thetae*(dp1+dp2)/2
                            thetae_sat_lt[j]+=thetae_sat*(dp1+dp2)/2
 
                        elif (i==ind_pmid[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_lt[j]+=thetae*(dp2)/2
                            thetae_sat_lt[j]+=thetae_sat*(dp2)/2
                        
            
            thetae_bl[j]=thetae_bl[j]/(pbl_thickness)
            thetae_lt[j]=thetae_lt[j]/(lt_thickness)
            thetae_sat_lt[j]=thetae_sat_lt[j]/(lt_thickness)
            
            
def compute_3layer_thetae(np.ndarray[DTYPE_t, ndim=2] temp, np.ndarray[DTYPE_t, ndim=2] q,
np.ndarray[DTYPE_t, ndim=2] lev, 
np.ndarray[DTYPE1_t, ndim=1] ind_pbl_top, np.ndarray[DTYPE1_t, ndim=1] ind_plow, np.ndarray[DTYPE1_t, ndim=1] ind_pmid,
np.ndarray[DTYPE_t, ndim=1] thetae_bl, np.ndarray[DTYPE_t, ndim=1] thetae_lt, np.ndarray[DTYPE_t, ndim=1] thetae_sat_lt,
np.ndarray[DTYPE_t, ndim=1] thetae_mt, np.ndarray[DTYPE_t, ndim=1] thetae_sat_mt):

### This function performs vertical averaging on pressure levels with the assumptions:
### i)  Index 0 has highest pressure, and pressure is monotonically decreasing away from index 0
### ii) Each value is at the vertex of the function being integrated, such that the
###     boundary values (pbl, lt) contribute to layer averages both above and below.

    cdef unsigned int vector_size, height_size
    cdef Py_ssize_t i,j
    cdef double pres_hPa, qs, thetae, thetae_sat, dp1, dp2
    cdef double pbl_thickness, lt_thickness, mt_thickness
    
    ht_size = lev.shape[0]
    vector_size = lev.shape[1]
    
    for j in range(vector_size):

        pbl_thickness=(lev[0,j]-lev[ind_pbl_top[j],j])
        lt_thickness=(lev[ind_pbl_top[j],j]-lev[ind_plow[j],j])
        mt_thickness=(lev[ind_plow[j],j]-lev[ind_pmid[j],j])
#         if (lt_thickness>20000): 
        if (mt_thickness>10000): 

            for i in range(ht_size):
        
                if (i<=ind_pmid[j]):
            
                    pres_hPa=lev[i,j]/100 # convert to hPa
                    qs= qs_calc(pres_hPa,temp[i,j])        
                    thetae=theta_e_calc(pres_hPa, temp[i,j], q[i,j])

                    dp1=lev[i,j]-lev[i+1,j]

                    if (i<ind_pbl_top[j]):
                
                        if(i==0):
                            thetae_bl[j]+=thetae*dp1/2
                        elif (i>0) & (i<ind_pbl_top[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_bl[j]+=thetae*(dp1+dp2)/2
                                      
                    else:
                        thetae_sat=theta_e_calc(pres_hPa, temp[i,j], qs)
 
                        if(i==ind_pbl_top[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_bl[j]+=thetae*(dp2)/2              
                            
                            thetae_lt[j]+=thetae*dp1/2
                            thetae_sat_lt[j]+=thetae_sat*dp1/2
                            

                        elif (i>ind_pbl_top[j]) & (i<ind_plow[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_lt[j]+=thetae*(dp1+dp2)/2
                            thetae_sat_lt[j]+=thetae_sat*(dp1+dp2)/2

                        elif (i==ind_plow[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_lt[j]+=thetae*(dp2)/2
                            thetae_sat_lt[j]+=thetae_sat*(dp2)/2
                            
                            thetae_mt[j]+=thetae*dp1/2
                            thetae_sat_mt[j]+=thetae_sat*dp1/2

                        elif (i>ind_plow[j]) & (i<ind_pmid[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_mt[j]+=thetae*(dp1+dp2)/2
                            thetae_sat_mt[j]+=thetae_sat*(dp1+dp2)/2

                        elif (i==ind_pmid[j]):
                            dp2=lev[i-1,j]-lev[i,j]
                            thetae_mt[j]+=thetae*(dp2)/2
                            thetae_sat_mt[j]+=thetae_sat*(dp2)/2
                        
            
            thetae_bl[j]=thetae_bl[j]/(pbl_thickness)
            thetae_lt[j]=thetae_lt[j]/(lt_thickness)
            thetae_sat_lt[j]=thetae_sat_lt[j]/(lt_thickness)
            thetae_mt[j]=thetae_mt[j]/(mt_thickness)
            thetae_sat_mt[j]=thetae_sat_mt[j]/(mt_thickness)


