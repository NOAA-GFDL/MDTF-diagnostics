#PyWR.py (version1.1) -- 27 Oct 2020
#Python functions for weather typing (using K-means) and flow-dependent model diagnostics
#Authors: ÁG Muñoz (agmunoz@iri.columbia.edu), James Doss-Gollin, AW Robertson (awr@iri.columbia.edu)
#The International Research Institute for Climate and Society (IRI)
#The Earth Institute at Columbia University.

#Notes:
#Log: see version.log in GitHub

import numpy as np
from numba import jit
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from typing import Tuple

def get_number_eof(X: np.ndarray, var_to_explain: float, plot=False) -> int:
    """Get the number of EOFs of X that explain a given variance proportion
    """
    assert var_to_explain > 0, 'var_to_explain must be between 0 and 1'
    assert var_to_explain < 1, 'var_to_explain must be between 0 and 1'
    pca = PCA().fit(X)
    var_explained = pca.explained_variance_ratio_
    cum_var = var_explained.cumsum()
    n_eof = np.where(cum_var > var_to_explain)[0].min() + 1

    if plot:
        n_padding = 4
        plt.figure(figsize=(12, 7))
        plt.plot(np.arange(1, n_eof + 1 + n_padding), cum_var[0:(n_padding + n_eof)])
        plt.scatter(np.arange(1, n_eof + 1 + n_padding), cum_var[0:(n_padding + n_eof)])
        plt.xlabel('Number of EOFs')
        plt.ylabel('Cumulative Proportion of Variance Explained')
        plt.grid()
        plt.title('{} EOF Retained'.format(n_eof))
        plt.show()
    return n_eof

@jit
def _vector_ci(P: np.ndarray, Q: np.ndarray) -> float:
    """Implement the Michaelangeli (1995) Classifiability Index

    The variable naming here is not pythonic but follows the notation in the 1995 paper
    which makes it easier to follow what is going on. You shouldn't need to call
    this function directly but it is called in cluster_xr_eof.

    PARAMETERS
    ----------
        P: a cluster centroid
        Q: another cluster centroid
    """
    k = P.shape[0]
    Aij = np.ones([k, k])
    for i in range(k):
        for j in range(k):
            Aij[i, j] = np.corrcoef(P[i, :], Q[j, :])[0, 1]
    Aprime = Aij.max(axis=0)
    ci = Aprime.min()
    return ci

def calc_classifiability(P, Q):
    """Implement the Michaelangeli (1995) Classifiability Index
    The variable naming here is not pythonic but follows the notation in the 1995 paper
    which makes it easier to follow what is going on. You shouldn't need to call
    this function directly but it is called in cluster_xr_eof.
    Args:
        P: a cluster centroid
        Q: another cluster centroid
    """
    k = P.shape[0]
    Aij = np.ones([k, k])
    for i in range(k):
        for j in range(k):
            Aij[i, j], _ = correl(P[i, :], Q[j, :])
    Aprime = Aij.max(axis=0)
    ci = Aprime.min()
    return ci

@jit
def get_classifiability_index(centroids: np.ndarray) -> Tuple[float, int]:
    """Get the classifiability of a set of centroids

    This function will compute the classifiability index for a set of centroids and
    indicate which is the best one

    PARAMETERS
    ----------
        centroids: input array of centroids, indexed [simulation, dimension]
    """
    nsim = centroids.shape[0]
    c_pq = np.ones([nsim, nsim])
    for i in range(0, nsim):
        for j in range(0, nsim):
            if i == j:
                c_pq[i, j] = np.nan
            else:
                c_pq[i, j] = _vector_ci(P=centroids[i, :, :], Q=centroids[j, :, :])
    classifiability = np.nanmean(c_pq)
    best_part = np.where(c_pq == np.nanmax(c_pq))[0][0]
    return classifiability, best_part

@jit
def loop_kmeans(X: np.ndarray, n_cluster: int, n_sim: int) -> Tuple[np.ndarray, np.ndarray]:
    """Compute weather types

    PARAMETERS
    ----------
        X: an array (should be in reduced dimension space already) indexed [time, dimension]
        n_cluster: how many clusters to compute
        n_sim: how many times to initialize the clusters (note: computation increases order (n_sim**2))
    """
    centroids = np.zeros(shape=(n_sim, n_cluster, X.shape[1]))
    w_types = np.zeros(shape=(n_sim, X.shape[0]))
    for i in np.arange(n_sim):
        km = KMeans(n_clusters=n_cluster).fit(X)
        centroids[i, :, :] = km.cluster_centers_
        w_types[i, :] = km.labels_
    return centroids, w_types
