import defines

def where_y(sys,source,target,interval):

    """This function locates the y_index (integer) of a target latitude
       by searching the source latitude array.

    Options/Arguments:
        sys -- module
        source -- list of latitudes.
        target -- latitude to find in source.
        interval -- half the grid spacing of source.

    Returns:
        y -- the y_index of source holding target.

    Examples:

    Notes: If the target falls on a boundary between grids, then
           we opt to assign y to the equatorward grid.

    Author: Mike Bauer  <mbauer@giss.nasa.gov>

    Log:
        2008/05  MB - File created.
        2008/10  MB - Added input checks, docstring.
        2008/10  MB - Fixed bug in the 'find it' check.
    """
        
    # Given that source are the midpoints of the bin and interval is half
    # the grid/bin spacing, then define the edges as so.
    edges = dict([(round(i+interval),1) for i in source])
    edges.update([(round(i-interval),1) for i in source])
    edges = list(edges.keys())
    edges.sort()

    # Find the "bin" that target falls into. If target is on an edge then
    # choose the equatorward grid. If target is a grid midpoint use that.
    if defines.verbose:        
        print ("target value: "+str(target))
        print (edges)
    if target in source:
        # target in source
        y = source.index(target)
        return y

    if target in edges:
        # target on an edge
        y = edges.index(target)
        if target > 0.0:
            y -= 1
        return y
    for j in range(len(edges)-1):
        # target between edges
        if edges[j] <= target <= edges[j+1]:
##FIX

            ### ADDED BY JJ #########
            ###### We pick the lower end of the edges if target is positive and higher end if target is positive
            ### if target is negative then we have to pick j+1, else pick j 
            if (target > 0):
              y = j
            elif (target < 0):
              y = j+1

            #print "hmmm, I forgot to do this case"
            #print edges[j]
            #sys.exit("Stop HERE")
            return y

    # Error check
    sys.exit("Error in where_y %s %s %s %s" % (repr(source),
                                               repr(target),
                                               repr(interval),
                                               repr(hit)))
