def grid2ij(k,im,jm):
    """returns 2d grid indices of an ny,nx 'row-major' array.
    """
    i = -1
    j = -1
    if k < im*jm:
        i = k % im
        j = k // im
    return i,j
