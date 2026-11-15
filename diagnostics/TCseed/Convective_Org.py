import numpy as np
from skimage.measure import regionprops_table
from scipy.ndimage import label, center_of_mass

# Compatibility wrapper for numpy.trapezoid (added in NumPy 2.0)
# Older versions use numpy.trapz instead
if hasattr(np, 'trapezoid'):
    trapezoid_func = np.trapezoid
else:
    trapezoid_func = np.trapz

#The following routines compute the theoretical and observed Besag's L-functions given a 2D binary field of convective/non-convective points and provide the cloud-to-cloud nearest-neighbor distances for the computation of L_org/dL_org and I_org/RI_org.
#Input and output parameters of the main routine _compute_organization_indices:

#	INPUT PARAMETERS (via dictionary)
#		dxy						grid resolution (assumed to be uniform in both directions)
#		cnv_idx					2D binary matrix, =1 in convective points, =0 elsewhere. The Python object class must be numpy.ndarray
#		rmax					maximum search radius (box size in the discrete case) for the neighbor counting (check documentation for details)
#		bins					distance/box size bands in which to evaluate the object counts. The Python object class must be numpy.ndarray
#		periodic_BCs			flag for the assignment of doubly periodic (True)/open (False) boundary conditions
# 		periodic_zonal			flag for the assignment of periodic boundary conditions in the x-direction and open boundary conditions in the y-direction (True). False if domain is doubly periodic or with open boundaries
#		clustering_algo			flag for the application (True) or not (False) of a four-connectivity clustering algorithm to merge aggregates
#		binomial_continuous		flag for binomial point process correction in case finite domains and Poisson model are assumed (True, False otherwise)
#		binomial_discrete		flag for the assumption of discrete binomial model as a reference for spatial randomness (True, False otherwise)
#		edge_mode				In case of open domains, this specifies the edge correction method to compensate the undercount bias (options 'none', 'besag', see manuscript and documentation for details, 'besag' only if binomial_discrete is True)

#	OUTPUT PARAMETERS (via dictionary)
#		I_org				value of the I_org index as originally introduced by Tompkins and Semie (2017)
#		RI_org				value of the RI_org index (i.e., RI_org = I_org - 0.5)
#		L_org				value of the L_org/dL_org index (depends on whether continuous domains or discrete grids are considered)
#		NNCDF_theor			NNCDF theoretically expected in case the ncnv cloud entities were randomly distributed within the domain (Weibull CDF)
#		NNCDF_obs			NNCDF derived from the distribution of the ncnv objects in the scene
#		Besag_theor			Besag's L-function theoretically expected in case the ncnv cloud entities were randomly distributed within the domain
#		Besag_obs			Besag's L-function derived from the distribution of the ncnv objects in the scene   	 	

##EXCLUSION OF CASES FOR WHICH INPUT ARGUMENTS CONFLICT/ARE NOT ACCOUNTED FOR BY THE PRESENT ROUTINES
def _check_input(cnv_idx, periodic_BCs, periodic_zonal, binomial_continuous, binomial_discrete):
	
	if (periodic_BCs and periodic_zonal) or (binomial_continuous and binomial_discrete):
		raise ValueError('--------CONFLICTING INPUT OPTIONS--------')
	
	if not binomial_discrete and not periodic_BCs:
		raise NotImplementedError('--------CASE NOT HANDLED BY THE PRESENT ROUTINE--------')
		#Built-in functions are available for edge corrections in case of random Poisson processes, see https://docs.astropy.org/en/stable/stats/ripley.html 
	
	if not isinstance(cnv_idx, np.ndarray):
		raise TypeError("--------The cloud mask must be of type np.ndarray--------")
	
	unique_vals = np.unique(cnv_idx)
	if not np.all(np.isin(unique_vals, [0, 1])):
		raise ValueError("--------The cloud mask must be binary--------")

##COMPUTATION OF WIDTH AND HEIGHT OF THE OBSERVATION WINDOW (DOMAIN)
def _get_domain_dimensions(dxy, cnv_idx):
    ny, nx = cnv_idx.shape
    return nx, ny, (nx - 1) * dxy, (ny - 1) * dxy

##CYCLIC CONTINUATION OF THE DOMAIN IN CASE OF DOUBLY PERIODIC/ZONALLY PERIODIC BOUNDARY CONDITIONS  
def _periodic_extend(cnv_idx, mode):
	if mode == "full":
		return np.block([[cnv_idx]*3]*3)
	elif mode == "zonal":
		return np.hstack([cnv_idx]*3)
	else:
		#Open boundary case (no periodic continuation of the domain)
		return cnv_idx

##DETERMINATION OF CLOUD OBJECT NUMBER AND CENTROIDS
def _get_centroids(cnv_idx, periodic_BCs, periodic_zonal, clustering_algo):
    ny, nx = cnv_idx.shape
	
	#If four-connectivity clustering algorithms are applied, adjacent convective pixels (i.e., sharing a common side) are merged into a single one. If the domain is cyclic, aggregates on either sides of the domain are close to each other and identified as single ones if they are contiguous. If the domain is cyclic in the zonal but not in the meridional direction, this applies along the x axis only.
    if clustering_algo:
        if periodic_BCs:
            mode = "full"
        elif periodic_zonal:
            mode = "zonal"
        else:
            mode = None
        mask = _periodic_extend(cnv_idx, mode)
        
        #Identification of the clusters and computation of their centers of mass 
        labeled_array, num_features = label(mask)
        props = regionprops_table(labeled_array, properties=('centroid',))
        centroids = np.stack([props['centroid-0'], props['centroid-1']], axis=1)
        
        # +++ FOR SMALL DOMAINS (LESS THAN 1E6 GRID POINTS), IT MIGHT BE MORE CONVENIENT TO DO +++
        #labeled_array, num_features = label(mask)
        #centroids = np.array(center_of_mass(mask, labeled_array, range(1, num_features + 1)))

		#Only the centroids located within the original (inner) domain are retained.
        if periodic_BCs:
            condition = ((centroids[:,0] >= ny) & (centroids[:,0] < 2*ny) & (centroids[:,1] >= nx) & (centroids[:,1] < 2*nx))
            centroids = centroids[condition] - [ny, nx]
        elif periodic_zonal:
            condition = (centroids[:,1] >= nx) & (centroids[:,1] < 2*nx)
            centroids = centroids[condition] - [0, nx]
            
	#If no clustering algorithms are applied, each cloud object is treated as a single entity
    else:
        centroids = np.argwhere(cnv_idx)
    
    #Determination of the number of convective points
    ncnv = len(centroids)
    return centroids, ncnv

##CONSTRUCTION OF THE ARRAY OF ALL POSSIBLE BASE POINTS (INCLUDING DUPLICATES IN CASE OF PERIODIC BOUNDARIES)
def _duplicate_points(centroids, nx, ny, periodic_BCs, periodic_zonal):
    
    centroids = np.asarray(centroids)
    ncnv = len(centroids)
    
    if periodic_BCs:
        offsets = np.array([[y, x] for x in [0, nx, -nx] for y in [0, ny, -ny]])
    elif periodic_zonal:
        offsets = np.array([[0, x] for x in [0, nx, -nx]])
    else:
        #If no periodicity is assumed, the array of possible points is just the original one
        offsets = np.array([[0, 0]])
    
    all_pts = centroids[:, None, :] + offsets[None, :, :]
    all_pts = all_pts.reshape(-1, 2)
    all_ids = np.repeat(np.arange(ncnv), len(offsets))
    
    return all_pts, all_ids
    
##DETERMINATION OF ALL-NEIGHBOR DISTANCES
def _compute_neighbor_distances(base_pt, all_ids_base, all_pts, all_ids, dxy):

	#The given cloud object base_pt is regarded as the base point and all its neighbors are considered. In case of cyclic boundaries, the possible neighbors are all the points in the periodically continued domain, except for the duplications of the base point itself
    neighbors = np.compress(all_ids != all_ids_base, all_pts, axis=0)
    ids_neighbors = np.compress(all_ids != all_ids_base, all_ids, axis=0)
    delta_xy = neighbors - base_pt
    
    #Unit conversion from grid pixels to meters
    dists = dists = np.linalg.norm(delta_xy, axis=1)*dxy
    
    #Prohibit multiple counting: only the duplicate with minimum distance to the base point is retained
    max_id = ids_neighbors.max() + 1
    min_dists = np.full(max_id, np.inf)
    np.minimum.at(min_dists, ids_neighbors, dists)
    is_min = min_dists[ids_neighbors] == dists
    selected_ids = np.where(is_min)[0]
    unique_ids, first_idx = np.unique(ids_neighbors[selected_ids], return_index=True)
    final_ids = selected_ids[first_idx]

    #Values and components of the distances between the base points and all its neighbors 
    unique_dists = np.sort(dists[final_ids])
    unique_delta_xy = np.sort(delta_xy[final_ids])

    return unique_dists, unique_delta_xy
    
##COUNTING OF NEIGHBORS IN A RANGE OF BOX SIZE BANDS FOR THE ESTIMATION OF OBSERVED L-FUNCTION (FOR GRIDDED DATASETS WHERE binomial = True)
def _compute_binomial_cumulative_histogram(unique_delta_xy, dxy, rmax, bins, base_pt, domain_x, domain_y, periodic_BCs, periodic_zonal, edge_mode):
    
    #If the discrete version of the Besag's function is to be determined, the distances have to be computed on the discrete grid and their zonal and meridional components are considered
    dist_bin = dxy * np.abs(unique_delta_xy)
    
    #The size of the box surrounding the base cloud object (k) and determined by its j-th neighbor is twice the maximum between the zonal and meridional components of the distance d_{kj}  
    box_sizes = 2 * np.maximum(dist_bin[:, 0], dist_bin[:, 1])
    
    #Only the box sizes shorter than the maximum allowed size are retained
    box_sizes = box_sizes[box_sizes <= rmax]

    hist = np.zeros(len(bins))
    
    #For each object, perform the neighbor counting as a function of distance/box size (cumulative sum). The following procedure is adopted in order to have right-closed intervals, i.e., evaluation of the number of neighbors over boxes of size less or equal than a given value. Note that the bulit-in function numpy.histogram takes right-open bins by definition, with the exception of the last one, hence a different procedure is implemented here
    values, counts = np.unique(np.digitize(box_sizes, bins, right=True), return_counts=True)
    hist[values] = counts
    cum_hist = np.cumsum(hist)
    
	#Definition of edge correction strategies for open domains
    if not periodic_BCs and edge_mode == 'besag':
    	         
        #With the area-based correction technique, the weight is applied to any possible distance (box size) off the base point
        y, x = base_pt*dxy
        
        if periodic_zonal:
            ir = bins/2; mask = ir > 0            
            
            #The boxes centered at the k-th object are clipped to the domain edges. If periodic_zonal is True, this occurs only along the meridional direction 
            ymax, ymin = np.minimum(y + ir, domain_y), np.maximum(y - ir, 0)
            weights = np.zeros_like(ir)
            
            #For each distance ir off the k-th base point, computation of the weighting factor as the fractional area of the box of size 2*ir centered on it and contained within the domain
            weights[mask] = 2*ir[mask]/(ymax[mask] - ymin[mask])
        
        #Open domain in both directions
        else:
            ir = bins/2; mask = ir>0
                        
            #The boxes are clipped to the domain edges in both the zonal and meridional directions
            ymax, ymin = np.minimum(y + ir, domain_y), np.maximum(y - ir, 0)
            xmax, xmin = np.minimum(x + ir, domain_x), np.maximum(x - ir, 0)
            weights = np.zeros_like(ir)
            
            #Calculation of the weighting factor
            weights[mask] = (2 * ir[mask])**2 / ((ymax[mask] - ymin[mask]) * (xmax[mask] - xmin[mask]))
        
        #For each possible size of search boxes centered on the base convective object, the weighting factors are assigned to the corresponding counting of neighbors contained within the boxes
        cum_hist*=weights
    return cum_hist
   
#CUMULATIVE COUNTING OF NEIGHBORS IN A RANGE OF DISTANCE/BOX SIZE BANDS FOR ESTIMATION OF OBSERVED L-FUNCTION
def _compute_neighbor_stats(centroids, all_pts, all_ids, dxy, rmax, bins, periodic_BCs, periodic_zonal, binomial_discrete, domain_x, domain_y, edge_mode):

    ncnv = len(centroids)
    
    #Initialization of the array of cloud-to-cloud nearest-neighbor distances
    NNdist = np.zeros(ncnv)
    #Initialization of the array whose rows represent the cumulative neighbor counting over a range of distances/box sizes (binned) for each element of the pattern
    cum_counting = np.zeros((ncnv, len(bins)))
    
	#Determination of all-neighbor distances from each point of the pattern in the original domain. In case of periodic boundaries, multiple counting is avoided  
    for k, base_pt in enumerate(centroids):
        unique_dists, unique_delta_xy = _compute_neighbor_distances(base_pt, k, all_pts, all_ids, dxy)
        
        #Storage of nearest-neighbor distances
        NNdist[k] = unique_dists[0]
        
        
        if binomial_discrete:
            cum_hist = _compute_binomial_cumulative_histogram(unique_delta_xy, dxy, rmax, bins, base_pt, domain_x, domain_y, periodic_BCs, periodic_zonal, edge_mode)
             
        #Continuous (not discrete) domains                                                            
        else:
        	#Only the inter-point distances smaller than the maximum allowed one are retained
            distances = unique_dists[unique_dists < rmax]
            
            #For each object, the counting of neighbors is performed as a function of distance (binned) 
            hist = np.zeros(len(bins))
            inds, counts = np.unique(np.digitize(distances, bins, right=True), return_counts=True)
            hist[inds] = counts
            cum_hist = np.cumsum(hist)

		#Storage of the neighbor counting in terms of distance into the array cum_counting previously initialized		
        cum_counting[k, :] = cum_hist

    return NNdist, cum_counting

##DERIVATION OF THE THEORETICAL AND OBSERVED BESAG'S FUNCTIONS
def _compute_L_functions(cum_counting, bins, rmax, domain_x, domain_y, ncnv, nx, ny, periodic_BCs, periodic_zonal, binomial_continuous, binomial_discrete):
    
    #Computation of the mean number of neighbors off any typical point of the pattern as a function of distance/box size. This is by definition the quantity lambda K(r), lambda being the spatial density of points and K(r) the Ripley's function
    mean_count = np.mean(cum_counting, axis = 0)
    
    #Computation of OBSERVED Besag's functions
    if binomial_discrete:
        #To get the simulated Besag's function, the square root of the Ripley's function has to be taken. Note that mean_count = lambda K(r), hence K(r) = mean_count/lambda, where lambda is estimated as (ncnv-1)/(domain_x*domain_y) in order to have an unbiased estimator. This is formula eqn. (20) in the paper
        Besag_obs = np.sqrt(mean_count*domain_x*domain_y/(ncnv-1))
    else:
        #Same as above, but with the factor 1/pi for the derivation of the Besag's function from the Ripley's function. This is formula eqn. (11) in the paper	
        Besag_obs = np.sqrt(1/np.pi*mean_count*domain_x*domain_y/(ncnv-1))
    
    #Computation of THEORETICAL Besag's functions	
    #Square domains
    if nx == ny:
        if periodic_BCs:
            if binomial_continuous:			
                #Distance beyond which the correction for multiple counting must be included (see Sections 4a and 4c in the manuscript)
                rcrit = domain_x/2.			
                #This is formula eqn. (18) in the paper, normalized by rmax. For reasonable sample sizes (ncnv > 15), the factor (ncnv-1)/ncnv can be dropped. See also code documentation section 2.1.2
                Besag_theor = np.piecewise(bins, [bins<=rcrit, bins>rcrit], [lambda b: np.sqrt((ncnv-1)/ncnv)*b, lambda b: np.sqrt((ncnv-1)/(ncnv*np.pi)*(np.pi*b**2-4*(b**2*np.arccos(rcrit/b)-rcrit*np.sqrt(b**2-rcrit**2))))])
            else:		
                #This includes cases with periodic boundaries and Poisson and discrete binomial models for spatial randomness, eqns. (10) and (19) in the paper, normalized by rmax (r_max and ell_max in the text respectively). See also code documentation sections 2.1.1 and 2.1.3)
                Besag_theor = bins
        elif periodic_zonal:
            #This is eqn. (1) in the code documentation (section 2.1.5), with approximations already applied
            Besag_theor = np.piecewise(bins, [bins<=min(domain_x, domain_y), bins>min(domain_x, domain_y)], [lambda b: b, lambda b: np.sqrt(b*min(domain_x, domain_y))])
        else:
            #Open boundary case (see code documentation section 2.1.4)
            Besag_theor = bins
            
    #Non-square domains
    if nx!=ny:
        if periodic_BCs:
            if binomial_continuous:
                min_rcrit = min(domain_x, domain_y)/2.
                max_rcrit = max(domain_x, domain_y)/2.
                #This is formula eqn. (22) in the paper, normalized by rmax. For reasonable sample sizes (ncnv > 15), the factor (ncnv-1)/ncnv can be dropped. See also section 2.2.2 in the code documentation
                Besag_theor = np.piecewise(bins, [bins<=min_rcrit, np.logical_and(bins>min_rcrit, bins<=max_rcrit), bins>max_rcrit], [lambda b: np.sqrt((ncnv-1)/ncnv)*b, lambda b: np.sqrt((ncnv-1)/ncnv*1./np.pi*(np.pi*b**2-2*(b**2*np.arccos(min_rcrit/b)-min_rcrit*np.sqrt(b**2-min_rcrit**2)))), lambda b: np.sqrt((ncnv-1)/ncnv*1./np.pi*(np.pi*b**2-2*(b**2*np.arccos(min_rcrit/b)-min_rcrit*np.sqrt(b**2-min_rcrit**2))-2*(b**2*np.arccos(max_rcrit/b)-max_rcrit*np.sqrt(b**2-max_rcrit**2))))])
            elif binomial_discrete:
                #This is formula eqn. (23) in the paper, normalized by rmax. A simplification similar to eqn. (19) has been performed (see also code documentation section 2.2.3)
                Besag_theor = np.piecewise(bins, [bins<=min(domain_x, domain_y), bins>min(domain_x, domain_y)], [lambda b: b, lambda b: np.sqrt(b*min(domain_x,domain_y))])
            else:
                #Case corresponding to Poisson distribution for complete spatial randomness and periodicity in both directions (see section 2.2.1 in the code documentation)
                Besag_theor = bins
        elif periodic_zonal:
            #Case of zonally cyclic domains, see code documentation section 2.2.5 
            if (domain_x<domain_y or domain_x<2*domain_y):
                #This is eqn. (2) in the code documentation, with simplifications already applied
                Besag_theor = np.piecewise(bins, [bins<=min(domain_x, 2*domain_y), bins>min(domain_x, 2*domain_y)], [lambda b: b, lambda b: np.sqrt(b*min(domain_x, 2*domain_y))])
            elif domain_x >= 2*domain_y:
                Besag_theor = bins
        else:			
            #Open boundary case (code documentation section 2.2.4)
            Besag_theor = bins
			
    #Normalization of L-functions is performed
    Besag_obs=Besag_obs/rmax
    Besag_theor=Besag_theor/rmax 
    
    return Besag_theor, Besag_obs

##COMPUTATION OF THE INDICES I_ORG/RI_ORG AND L_ORG
def _compute_indices(ncnv, NNdist, Besag_obs, Besag_theor, bins, domain_x, domain_y, dxy, periodic_BCs, rmax):

    #The average spatial density of cloud objects is computed. If the clustering algorithm is applied, the resulting number of convective objects is used in the calculation of density
    lambd = ncnv/(domain_x*domain_y)
    
    #Evaluation of theoretical NNCDF. A different (binned) range of distances is introduced to evaluate the theoretical Weibull NNCDF and construct the observed NNCDF. 
    if periodic_BCs:
        r_Iorg = np.arange(0, np.sqrt((domain_x**2 + domain_y**2) / 2) + dxy, dxy)
    else:
        r_Iorg = np.arange(0, np.sqrt(domain_x**2 + domain_y**2) + dxy, dxy)

    bins_Iorg = r_Iorg
    NNCDF_theor = 1 - np.exp(-lambd * np.pi * r_Iorg**2)

	#Computation of the NNCDF of the given scene (observed NNCDF). The latter is not computed through the python built-in function numpy.histogram (see note above about the fact that the bins in numpy.histogram are not right-closed, which conflicts with the formal definition of cumulative distribution function)
    values, counts = np.unique(np.digitize(NNdist, bins=bins_Iorg, right=True), return_counts=True)
    hist_Iorg = np.zeros(len(bins_Iorg), dtype=int)
    hist_Iorg[values] = counts
    NNPDF = hist_Iorg / np.sum(hist_Iorg)
    NNCDF_obs = np.cumsum(NNPDF)

    #Integration of the joint CDFs to give I_org/RI_org
    I_org = trapezoid_func(NNCDF_obs, x=NNCDF_theor)
    RI_org = trapezoid_func(NNCDF_obs - NNCDF_theor, x=NNCDF_theor)
    
    #Computation of L_org
    L_org = trapezoid_func(Besag_obs - Besag_theor, x=bins) / rmax
    
    return I_org, RI_org, L_org, NNCDF_theor, NNCDF_obs

##MAIN ROUTINES
def _compute_organization(dxy, cnv_idx, rmax, bins, periodic_BCs, periodic_zonal, clustering_algo, binomial_continuous, binomial_discrete, edge_mode):
    _check_input(cnv_idx, periodic_BCs, periodic_zonal, binomial_continuous, binomial_discrete)
    nx, ny, domain_x, domain_y = _get_domain_dimensions(dxy, cnv_idx)
    centroids,ncnv = _get_centroids(cnv_idx, periodic_BCs, periodic_zonal, clustering_algo)
    all_pts,all_ids=_duplicate_points(centroids, nx, ny, periodic_BCs, periodic_zonal)
    NNdist,cum_count=_compute_neighbor_stats(centroids, all_pts, all_ids, dxy, rmax, bins, periodic_BCs, periodic_zonal, binomial_discrete, edge_mode, domain_x, domain_y)
    Besag_theor, Besag_obs=_compute_L_functions(cum_count, bins, rmax, domain_x, domain_y, ncnv, nx, ny, periodic_BCs, periodic_zonal, binomial_continuous, binomial_discrete)
    I_org, RI_org, L_org, NNCDF_theor, NNCDF_obs=_compute_indices(ncnv, NNdist, Besag_obs, Besag_theor, bins, domain_x, domain_y, dxy, periodic_BCs, rmax)
    
    return {"I_org": I_org, "RI_org": RI_org, "L_org": L_org, "NNCDF_theor": NNCDF_theor, "NNCDF_obs": NNCDF_obs, "Besag_theor": Besag_theor, "Besag_obs": Besag_obs}

def _compute_organization_indices(params:dict):
    defaults = {
        "dxy": None,
        "cnv_idx": None,
        "rmax": None,
        "bins": None,
        "periodic_BCs": False,
        "periodic_zonal": False,
        "clustering_algo": False,
        "binomial_continuous": False,
        "binomial_discrete": True,
        "edge_mode": 'besag'
    }

    full_params = {**defaults, **params}

    if full_params["dxy"] is None:
        full_params["dxy"] = 1e3
    if full_params["cnv_idx"] is None:
        full_params["cnv_idx"] = np.random.choice([0, 1], size=(50, 50), p=[0.99, 0.01])
    if full_params["rmax"] is None:
        full_params["rmax"] = 100e3
    if full_params["bins"] is None:
        full_params["bins"] = np.arange(0, 100e3, 1e3)

    return _compute_organization(dxy=full_params["dxy"], 
                                 cnv_idx=full_params["cnv_idx"], 
                                 rmax=full_params["rmax"], 
                                 bins=full_params["bins"],
                                 periodic_BCs=full_params["periodic_BCs"],
                                 periodic_zonal=full_params["periodic_zonal"],
                                 clustering_algo=full_params["clustering_algo"],
                                 binomial_continuous=full_params["binomial_continuous"],
                                 binomial_discrete=full_params["binomial_discrete"],
                                 edge_mode=full_params["edge_mode"]
                                )