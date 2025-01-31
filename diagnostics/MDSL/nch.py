# Script to run generalized TCH

import numpy as np
import numpy.matlib
from scipy import optimize
from itertools import combinations
import math
# from tqdm.notebook import tnrange, tqdm



def compute_error(threshold, destgrid, wts, conserv_mask, data_flat, model_flat):

    length_test = [len(data_flat[i])==len(model_flat) for i in range(len(data_flat))]
    if not np.array(length_test).ravel().all():
        raise IndexError('Input flat datasets must be the same length. You have likely not regridded correctly.')

    # Number of data sets in NCH is number of observational datasets plus the model.
    num_datasets = len(data_flat) + 1

    # Create grids of NaNs to hold error information
    col = len(destgrid.lon.values)
    row = len(destgrid.lat.values)
    # Error std dev
    err = np.zeros((num_datasets, col, row)) * np.nan
    R_cov = np.zeros((math.comb(num_datasets, 2), col, row)) * np.nan
    # Number of points in each TCH box
    num_points = np.zeros((col, row)) 
    # Square root of cost function, <(data-model)^2>/error^2 for each TCH box
    cost_func = np.zeros((num_datasets-1, col, row)) * np.nan

    nlons = len(destgrid.lon.values)

    # Initiate covariance. Will return this value if not reset in the loop. 
    R = np.zeros((num_datasets, num_datasets))*np.nan
    
    for i in (range(len(destgrid.lon.values))):
        if np.mod(i,5)<1:
            print(str(i) + " of " + str(nlons) + " longitude indices")
        for j in range(len(destgrid.lat.values)):

            # Index for weights
            w_idx = i%len(destgrid.lon.values) + j*len(destgrid.lon.values)
            # Get cell weights corresponding to that TCH box and add mask for poles and land
            unmasked_cellwt = wts[w_idx,:].data.todense()
            cellwt = unmasked_cellwt * conserv_mask
            
            # Make sure there are points that are non-zero and non-nan
            if ~np.isnan(cellwt).all() and (cellwt>0).any():
            # if ~np.isnan(cellwt).any() and (cellwt>0).any():

                # Get indices where the weights are non-zero (meaning whether the gridpoints are inside the cell)
                ind = np.array([l for l in range(len(cellwt)) if cellwt[l] > 0 and ~np.isnan(cellwt[l])])
                # Record number of valid gridpoints inside the TCH box
                num_points[i,j] = len(ind)
                
                # Require TCH cells to be sufficiently large (at least 3 points) in order to run calculation
                if len(ind)> threshold:
                    # Create new array of only the mdt points actually in the cell
                    mdt_tch = np.zeros((num_datasets,len(ind)))
                    mdt_tch[0] = data_flat[0][ind]
                    mdt_tch[1] = data_flat[1][ind]
                    mdt_tch[2] = model_flat[ind]
                    if num_datasets==4:
                        mdt_tch[3] = data_flat[2][ind]


                    # Transpose to get into same format as original TCH input
                    mdt_tch = mdt_tch.transpose()
    
                    # perform TCH
                    R = generalized_TCH(mdt_tch)
    
                    if (np.linalg.det(R) < 0):
                        # Place a marker
                        print('invalid point here')
                    for k in np.arange(num_datasets):
                        # Get the variance for kth dataset.
                        Rkk = R[k, k]
                        if Rkk > 0:
                            err[k, i, j] = np.sqrt(Rkk)
                            
                            if k != 2:
                                # Compute cost function for datasets
                                variance = np.nanmean((mdt_tch[:,k]-mdt_tch[:,2])**2)
                                if k>2:
                                    cost_func[k-1, i, j] = np.sqrt(variance)/err[k, i, j]
                                else:
                                    cost_func[k, i, j] = np.sqrt(variance)/err[k, i, j]
                        # TODO: can you take out this section because anyhwere that Rkk<=0 will be taken care of by if statement in TCH?
                        else:
                            err[k, i, j] = np.nan
                            if not np.isnan(Rkk):
                                print('Rkk is not positive nor nan. Rkk is ', Rkk)

                    cov_idx = list(combinations(range(num_datasets), 2))
                    for k in np.arange(math.comb(num_datasets, 2)):
                        R_cov[k, i, j] = R[cov_idx[k][0], cov_idx[k][1]]
    # option to return R_cov here
    return err, num_points, cost_func



def generalized_TCH(X, constrained=True):
    """
    X(M,N): N series with M datapoints (no NaN)
    r(N,N): covariances of the errors, R_ij=cov(err_i,err_j)
    Y(N-1,N-1): covariances of differences to reference datasets N

    We only need to solve r_1N, r_2N, ..., r_NN because of the following relation:
    r_ij = C_ij - r_NN + r_iN + r+jN
    We seek to minimize the function F(r)=sum((r_ij)^2) / K^2; (i<j); K=|C|^((N-1)/2)
    subject to the constraint that G(r)= -H(r)/K < 0 where K = mean(mean(C))/1000 is a better choice for numerical stability from Galindo (private communications with Kquinn and Rui?)\
    The meaning of H(r) may be expressed as G(r) = -H(r)/K = -|R|/K <0
    """
    
    M = X.shape[0]
    N = X.shape[1]
    # Creates an array of size (M, N-1)
    # XN is the reference dataset
    XN = np.matlib.repmat(X[:, -1][:, np.newaxis], 1, N - 1)
    # Covariance of the two datasets minus the reference data
    C = np.cov((X[:, :-1] - XN).transpose())
    
    
    # scale C to avoid numerical instability
    K = np.mean(C) / 1000
    C = C / K
    Cinv = np.linalg.inv(C)


    # Initial guess
    r = np.append(np.zeros(N-1), 0.5/np.sum(Cinv))
    

    R = np.zeros((N, N))

    # Run constrained optimization
    if constrained:
        def constr(r_guess, *args):
            """
            Determine whether det(R)>0, a constraint for the generalized TCH...
            ... except that determinant as a constraint is unstable....
            ... so instead check with some minimum eigenvalue
            """

            R[:, -1] = r_guess
            R[-1, :] = r_guess
            for j in np.arange(N - 1):
                for i in np.arange(N - 1):
                    R[i, j] = C[i, j] - r_guess[-1] + r_guess[i] + r_guess[j]

            lambda_min = np.trace(R)*1e-4

            return np.linalg.det(R-np.identity(len(r_guess))*lambda_min)

        const = ({'type':'ineq', 'fun': constr})

        # Constrained optimization
        r_new = optimize.minimize(F, r, constraints=const, args=(C, N), method='COBYLA', ).x
        
        # construct R from r
        R[:, -1] = r_new
        R[-1, :] = r_new
        for j in np.arange(N - 1):
            for i in np.arange(N - 1):
                R[i, j] = C[i, j] - r_new[-1] + r_new[i] + r_new[j]
        # Rescale back to original scale
        R = R * K


    else:
        k = 1

        # Initial penalty value
        p = 0.9 * F(r, C, N) * H(r, Cinv, N)
        #Pparameter used to decrease the penalty term
        c = 0.7

        
        while k < 500:
            # Unconstrained conjugate gradient optimization
            r_new = optimize.fmin_cg(Phi, r, fprime=dPhi, gtol=1e-7, args=(p, C, Cinv, N), disp=False)
            
            # Construct R from r
            R[:, -1] = r_new
            R[-1, :] = r_new
            for j in np.arange(N - 1):
                for i in np.arange(N - 1):
                    R[i, j] = C[i, j] - r_new[-1] + r_new[i] + r_new[j]
            # Rescale back to original scale
            R = R * K
    
            # If det(R)<0, will get set to 0 in err_std anyway
            # Instances where det(R)<0 cause optimize to take an exceptionally...
            # ... long time to converge, so avoid having to rerun 500 times
            if np.linalg.det(R)<0:
                break
                
            # Also break if reach an appropriately good guess
            if (np.max(np.abs(r_new - r)) < 1e-8) & (np.linalg.det(R) > 0):
                break
        
            p = c * p
            r = r_new
            k = k + 1


    return R


def F(r, C, N):
    """
    F(r) function to be minimized in TCH method
    """
    y = 0
    for j in range(N-1):
        for i in range(j):
            y+= (C[i, j] - r[-1] + r[i] + r[j]) ** 2
    return y


def gradF(r, C, N):
    """
    Determine partials of F with respect to r_kN
    """

    dF = np.zeros((N, 1))
    r_2d = np.atleast_2d(r).transpose()

    for k in np.arange(0, N - 1):
        if k == 0:
            j = range(k + 1, N - 1)
            dF[k, 0] = 2 * (
                np.sum(C[k, j] + r_2d[j, 0].transpose())
                + (N - 2) * (r_2d[k, 0] - r_2d[-1, 0])
                + r_2d[k, 0]
            )
        elif k == N - 2:
            i = range(k)
            dF[k, 0] = 2 * (
                np.sum(C[i, k])
                + r_2d[i, 0]
                + (N - 2) * (r_2d[k, 0] - r_2d[-1, 0])
                + r_2d[k, 0]
            )
        else:
            i = range(k)
            j = range(k + 1, N - 1)
            dF[k, 0] = 2 * (
                np.sum(C[i, k])
                + r_2d[i, 0]
                + np.sum(C[k, j] + r_2d[j, 0].transpose())
                + (N - 2) * (r_2d[k, 0] - r_2d[-1, 0])
                + r_2d[k, 0]
            )

    dF[-1, 0] = 0
    for i in np.arange(N - 2):
        for j in np.arange(i + 1, N - 1):
            dF[-1, 0] = dF[-1, 0] - 2 * (
                C[i, j] - r_2d[-1, 0] + r_2d[j, 0] + r_2d[i, 0]
            )

    return dF


def H(r, Cinv, N):
    """
    H(r_1N, r_2N, ..., r_NN) = det(R)/det(C) = r_NN - L*inv(C)*L^T,
    where L = (r_1N-r_NN, r_2N-r_NN, ..., r_(N-1)N-r_NN)
    """
    L = r[:-1]-r[-1]
    return r[-1] - np.matmul(np.matmul(L, Cinv), np.transpose(L))

# + tags=[]
def gradH(r, Cinv, N):
    """
    Calculates gradients of H
    """
    dH = np.zeros((N, 1))
    dH[-1, 0] = 1
    for k in np.arange(N - 1):
        dH[k, 0] = np.matmul(-(Cinv[:, k].transpose() + Cinv[k, :]), r[:-1] - r[-1])
        dH[-1, 0] = dH[-1, 0] + np.matmul(
            Cinv[:, k].transpose(), r[:-1] + r[k] - 2 * r[-1]
        )
    return dH


# -


def Phi(r, *args):
    """
    Sets the penalty function Phi for the constrained optimization for use in the Interior Penalty method:
    Phi(r)=F(r)-p_k/G(r)=F(r)+p_k*K/H(r),
    where G(r)<0 is our constraint condition
    """
    p, C, Cinv, N = args
    f = F(r, C, N) + p * 1 / H(r, Cinv, N)

    return f


def dPhi(r, *args):

    p, C, Cinv, N = args
    gradf = gradF(r, C, N) - p * 1 * gradH(r, Cinv, N) / (H(r, Cinv, N) ** 2)

    return gradf.ravel()