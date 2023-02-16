import pandas as pd


#####################################
#  REANALYSIS/OBS.  
#####################################


def mdtf_case_list():
	

    rl = {} # Revert List
	
	
# BL Vres
    rl['ERA5']   =  ['ERA5']
    rl['ERAI']   =  ['ERAI']
    rl['JRA25']   =  ['JRA25']
    rl['CFSR']   =  ['CFSR']
    rl['MERRA2']   =  ['MERRA2']



# Data frames.


#####################################
# CAM6 Revert Experiments + others   
#####################################

# Releases
    rl['C4']   =  ['f40.1979_amip.track1.1deg.001']
    rl['C5']   =  ['30L_cam5301_FAMIP.001']
    rl['C6']   =  ['f.e20.FHIST.f09_f09.cesm2_1.001']
    rl['CC4']  =  ['b40.20th.track1.1deg.012']
    rl['CE1']  =  ['b.e11.B20TRC5CNBDRD.f09_g16.001']
    rl['CE2']  =  ['b.e21.BHIST.f09_g17.CMIP6-historical.001']

    # Reverts
    rl['rC5now']  =   ['f.e20.FHIST.f09_f09.cesm2_1_cam5.001']
    rl['rC5']     =   ['f.e20.FHIST.f09_f09.cesm2_1_true-cam5.001']
    rl['rC5t']    =   ['f.e20.FHIST.f09_f09.cesm2_1_true-cam5_param_topo.001']
    rl['rUWold']  =   ['f.e20.FHIST.f09_f09.cesm2_1_uw.001']
    rl['rGW']    =   ['f.e20.FHIST.f09_f09.cesm2_1_iogw.001']
    rl['rZMc']  =   ['f.e20.FHIST.f09_f09.cesm2_1_capeten.001']
    rl['rMG1']  =   ['f.e20.FHIST.f09_f09.cesm2_1_mg1.002']
    rl['rSB']  =   ['f.e20.FHIST.f09_f09.cesm2_1_sb.002']
    rl['rTMS']  =   ['f.e20.FHIST.f09_f09.cesm2_1_tms.001']
    rl['rCE2i']  =   ['f.e20.FHIST.f09_f09.cesm2_1_revert125.001']
    rl['rC5p']  =   ['f.e20.FHIST.f09_f09.cesm2_1_revertcam5param.001']
    rl['rC5pm']  =   ['f.e20.FHIST.f09_f09.cesm2_1_revertcam5param.002']
    rl['rZMp']  =   ['f.e20.FHIST.f09_f09.cesm2_1_cam5_zmconv.001']
    rl['rM3']  =   ['f.e20.FHIST.f09_f09.cesm2_1_mam3.001']
    rl['rUW']  =   ['f.e20.FHIST.f09_f09.cesm2_1_uw.002']
    rl['rUWp']  =   ['f.e20.FHIST.f09_f09.cesm2_1_uw.003']
    rl['rMG1']  =   ['f.e20.FHIST.f09_f09.cesm2_1_mg1.002']
    rl['rice']  =   ['f.e20.FHIST.f09_f09.cesm2_1_ice-micro.001']
    rl['rpfrac']  =   ['f.e20.FHIST.f09_f09.cesm2_1_precip_frac_method.001']
    rl['rpremit']  =   ['f.e20.FHIST.f09_f09.cesm2_1_cld_premit.001']
    rl['rnohertz']  = ['f.e20.FHIST.f09_f09.cesm2_1_hetfrz-off.001']
    rl['rC5psalt']  =   ['f.e20.FHIST.f09_f09.cesm2_1_revertc5seasalt.001']
    rl['rC5pdust']  =   ['f.e20.FHIST.f09_f09.cesm2_1_revertc5dust.001']
    rl['rL30']  =   ['f.e20.FHIST.f09_f09.cesm2_1_L30.001']
    rl['rclm4'] = ['f.e20.FHIST.f09_f09.cesm2_1_clm4.001']
    
# SST configs    
    rl['CE2sst']  =   ['f.e20.FHIST.f09_f09.cesm2_1_coupled-sst-amip.001']
    rl['CE2sstd']  =   ['f.e20.FHIST.f09_f09.cesm2_1_coupled-sst-amip_daily.001']
    rl['REYsstd']  =   ['f.e20.FHIST.f09_f09.cesm2_1_reynolds_daily_sst.006']

    
# High vertical resolution.
    rl['W110']  =   ['f.e21.FWscHIST_BCG.f09_f09_mg17_110L.001']
    rl['W121']  =   ['f.e21.FWscHIST_BCG.f09_f09_mg17_121L_DZ_400m_80kmTop.001']







#########################################
# CAM6 Vertical Resolution Experiments   
#########################################

  
     
    #########################################
    # LENS1 
    #########################################
    
    
    e0=1 ; en=30   #Start/end ens. members

    erun = ['b.e11.B20TRC5CNBDRD.f09_g16.%03d'%(itt) for itt in range(e0,en+1)]
    enum = ['CE1.E%01d'%(itt) for itt in range(e0,en+1)]
   
    
    
    for it in range(e0,en+1):
        rl[enum[it-1]] = [erun[it-1]]
        
  
    #########################################
    # LENS2 Experiments   
    #########################################
    
    
    e0=1 ; en=10   #Start/end ens. members

    macro_yr = [1231,1251,1281,1301] # Just the separate micro starts
    
    erun = ['b.e21.BHISTcmip6.f09_g17.LE2-%03d.%03d'%(ity,itn) for ity in macro_yr for itn in range(e0,en+1) ]
    enum = ['CE2.E%01d'%(itt) for itt in range(e0,en*4+1)]
    
    
    for it in range(e0,en*4+1):
        rl[enum[it-1]] = [erun[it-1]]
        
    
    
 
    #########################################
    # CESM2-AMIP 
    #########################################
    
        
    rl['C6.E1'] = ['r1i1p1f1']
    rl['C6.E2'] = ['r2i1p1f1']
    rl['C6.E3'] = ['r3i1p1f1']
    rl['C6.E4'] = ['r4i1p1f1']
    rl['C6.E5'] = ['r5i1p1f1']
    rl['C6.E6'] = ['r6i1p1f1']
    rl['C6.E7'] = ['r7i1p1f1']
    rl['C6.E8'] = ['r8i1p1f1']
    rl['C6.E9'] = ['r9i1p1f1']
    rl['C6.E10'] = ['r10i1p1f1']
    
# Data frame
    rl_df = pd.DataFrame.from_dict(rl, orient='index',columns=['run name'])
#    display(rl_df)
    
    
    return rl_df






#########################################
# CESM LENS sets   
#########################################

