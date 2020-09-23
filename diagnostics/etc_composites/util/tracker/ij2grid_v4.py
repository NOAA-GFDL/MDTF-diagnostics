def ij2grid(j,i,im,jm):
    """returns 1d grid index of an ny,nx 'row-major' array.
    i the 'x' index between 0 , nx-1 where nx is index max
    j the 'y' index between 0 , ny-1 where ny is index max
    """
    if i < im and j < jm:
        k = j*im + i
    return int(k)
