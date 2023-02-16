'''

	Case Setup functions

'''

import numpy as np
import pandas as pd


def vprof_setup() :

		''''' Which case to use???? '''''

		
		case_types = ['reanal'] # 'revert', 'renanl' or 'lens'
		
		print('"""""" CASES = ',case_types)
		

		''' ##### REVERT EXPERIMENTS ##### '''

		if 'revert' in case_types:
		
			#pref_out = 'cam6_revert'
			#case_desc = np.array(['C6','C5','rC5now','rUW','rUWp','rMG1','rC5p','rC5pm','rZMc','rZMp','rpfrac','rCE2i'])



			#case_desc = np.array(['C6','C5','rC5now','rUW','rUWp','rMG1','rC5p','rC5pm','rZMc','rZMp','rpfrac','rCE2i']) ; pref_out = 'revert'

	
			#case_desc = ['C6','rC5','rCE2i','rUW','rMG1','rC5p','rZMc'] 
			## Do not have. -- 'rZMc','rZMp','rpfrac','rTMS','rGW']
			#case_desc = ['C6','rC5','rCE2i','rUW','rMG1','rC5p','rZMc','rZMp','rpfrac','rTMS','rGW'] 




			pref_out = 'c5_c6_scatter'  
			#ase_desc = ['C6','rC5','rCE2i','rUW','rMG1','rC5p','rZMc','rpfrac']  
			case_desc = ['C6','rC5']

		###
			nrevert = len(case_desc)
			case_type = ['cam6_revert']*nrevert







		''' ##### SETTINGS INCLUDING ENSEMBLES ###### '''

		
		if 'lens' in case_types:
		
			pref_out = 'lens2_divlev_test'    

			lens_set = 'lens1' ; lens_suff = 'CE1' # lens1, lens2, c6_amip
			#lens_set = 'lens2' ; lens_suff = 'CE2'
			#	lens_set = 'c6_amip' ; lens_suff = 'C6'

			nens = 1
		####

			case_desc = [lens_suff+'.E%01d'%(itt) for itt in range(1,nens+1)]
			case_type  = [lens_set]*nens


		''' ###### REANAL+ABOVE MODEL SIMS ######## '''

		if 'reanal' in case_types:
		

				pref_out = 'reanal_all'

			#	case_reanal = ['ERA5','ERAI','CFSR','MERRA2','JRA25'] 
			#	type_reanal = ['reanal','reanal','reanal','reanal','reanal']

				case_reanal = ['ERA5','ERAI','CFSR','MERRA2','JRA25'] 
				type_reanal = ['reanal','reanal','reanal','reanal','reanal']


		reanal_climo = True # Grab climo. values for mean, Nino and nina events for reanalysis only




		''' ######  Stitch Cases Togther ###### '''

		try: case_reanal
		except NameError: 
			case_desc_out = np.array(case_desc)
			case_type_out = np.array(case_type)



		try: case_desc
		except NameError: 
			case_desc_out = np.array(case_reanal)
			case_type_out = np.array(type_reanal)

		try: case_desc_out
		except NameError: 
			case_desc_out = np.array(case_desc+case_reanal)
			case_type_out = np.array(case_type+type_reanal)




		#case_desc = np.flip(case_desc)
		#case_type = np.flip(case_type)


		return case_desc_out,case_type_out,reanal_climo,pref_out






'''

	Variable settings routine

'''


def vprof_set_vars() :
	
	
## Variables ##

	var_desc = {}

	var_desc['DTCOND'] = ['dT/dt Total',86400.,1., -5.,5.,-2.,2.,'K/day']
	var_desc['DCQ']    = ['dq/dt Total',86400*1000.,1., -4.,4.,-4.,4.,'g/kg/day']
	var_desc['ZMDT']   = ['dT/dt Convection',86400., 1.,-5.,5.,-2.,2.,'K/day']
	var_desc['ZMDQ']   = ['dq/dt Convection',86400.*1000., 1.,-4.,4.,-4.,4.,'g/kg/day']
	var_desc['MPDT']   = ['dT/dt Microphysics',86400./1004., 1.,-5.,5.,-2.,2.,'K/day']
	var_desc['STEND_CLUBB'] = ['dT/dt turbulence',86400./1004., 1. ,-2.,8.,-2.,8.,'K/day']


	var_desc['OMEGA'] = ['OMEGA',-1., -1., -0.06,0.06,-0.06,0.06,'pa/s']
	var_desc['DIV'] = ['Divergence',1., 100./86400., -0.0004,0.0004,-0.0004,0.0004,'s^-1']
	var_desc['T'] = ['Temperature',1., 1., -10.,10.,-10.,10.,'K']
	var_desc['Q'] = ['Specific Humidity',1000., 1000., 0.,20.,-1.,1.,'g/kg']
	var_desc['U'] = ['Zonal Wind',1., 1., -60.,60.,-10.,10.,'m/s']

	
	var_df = pd.DataFrame.from_dict(var_desc, orient='index',columns=['long_name','vscale','ovscale','xmin','xmax','axmin','axmax','vunits'])
	
	return var_df



'''

	Regions settings routine

'''


def vprof_set_regions():
	
	
	
	''''' Named Regions '''''

	reg_names = {}

	#### RBN Original Locations ####
	#reg_names['Nino Wet'] = ['C. Pacific Nino Wet',-10,0.,160.,210]  # Core of nino precip signal
	#reg_names['WP Dry']   = ['West Pac. Nino Dry.',-5.,10.,120.,150]  # Core of W. Pacific signal
	#reg_names['Conv U']   = ['Convergence Min',25,50.,160,190]       # Core of RWS convergence min.
	#reg_names['CE Pac']   = ['East Pacific ITCZ',5,10.,220,270]       # Core of RWS convergence min.

	#### Anna Locations ####

	reg_names['Nino Wet'] = ['C. Pacific Nino Wet',-10,0.,160.,220]  # Core of nino precip signal
	reg_names['WP Dry']   = ['West Pac. Nino Dry.',0.,15.,110.,150]  # Core of W. Pacific signal
	reg_names['Conv U']   = ['Convergence Min',25,40.,150,200]       # Core of RWS convergence min.


	#1. positive precipitation anomalies -equatorial central Pacific : 160E-140W; 10S-EQ (Main tropical forcing)
	#2. Divergence anomalies subtropical North Pacific: 150E-160W; 25-40N (RWS generation region)
	#3. Negative precipitation anomalies western Pacific: 110E-150E; EQ-15N (Additional contribution to RWS) 
	
	reg_df = pd.DataFrame.from_dict(reg_names, orient='index',columns=['long_name','lat_s','lat_n','lon_w','lon_e'])
	
	
	return reg_df