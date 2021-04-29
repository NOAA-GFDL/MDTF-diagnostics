def find_empty_centers(empty_centers,center_slices,current_centers):
    """This function takes a list of all found centers and the attributed
    grids and determines if any are 'empty', which means there are no grids
    attached. This happens because the synoptic_cuttoff trims the center on
    its first contour... thus this center is an open-wave based on the given
    contour interval. That is, the 'bowl' of that center is too shallow to
    be contained to a synoptic scale by the contour interval. Other cases
    occur because an 'empty' center shares all of its contours with another
    center(s) and thus all of it's grids are now stormy.

    Options/Arguments:
        empty_centers -- list created here of all 'empty' centers.
        center_slices -- list of all currently found centers and their
                         attributed centers.
        current_centers -- list of all current centers.

    Returns:
       empty_centers -- see above.

    Examples:

    Notes:

    Author: Mike Bauer  <mbauer@giss.nasa.gov>

    Log:
        2008/05  MB - File created.
        2008/10  MB - 
    """
    empty_centers_append = empty_centers.append
    t = {}
    for ii in center_slices:
         if len(center_slices[ii]):
              t[ii] = center_slices[ii]
         else:
              mark = [x for x in current_centers if x[7] == ii]
              empty_centers_append(mark[0])
    return t
