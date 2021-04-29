def scan_contour(seed,canidates,gdict,slices,this_center,this_slice,peers):

    harvest = {}

    # Do any of seed's immediate neighbors fall in this contour,
    # i.e. in canidates? These are the grids that will be searched.
    #queue = [x for x in gdict[seed] if x in canidates]
    queue = dict( (x,1) for x in gdict[seed] if x in canidates)

    # Check to see if any of these grids have already been associated
    # with another center (at this contour), if so add all those
    # slices to this center and skip checks on them. This overlap
    # will be sorted out latter.
    for peer in peers:
        overlap = [x for x in slices[peer][this_slice] if x in queue]
        if overlap:
            # Add whole slice to harvest and terminate
            #for addon in slices[peer][this_slice]:
            #    harvest[addon] = 1
            harvest.update( (addon,1) for addon in slices[peer][this_slice])
            #queue = []
            queue = {}
            return harvest.keys() # new addition be sure okay!

    # Exclude seed, but add to harvest
    if seed in queue:
        del queue[seed]
        #queue.remove(seed)
        harvest[seed] = 1
 
    # Terminating condition (empty queue)
    if queue:
        # Trim canidates so no overlap with queue
        refined_canidates = canidates.fromkeys([x for x in canidates if x not in queue],1)
        if seed in refined_canidates:
            del refined_canidates[seed]
            #refined_canidates = [x for x in canidates if x not in queue]
            #if seed in refined_canidates:
            #    refined_canidates.remove(seed)
        # Add queue to harvest
        for hit in queue:
            # add to harvest
            harvest[hit] = 1
            # Recursive call on hit
            results = scan_contour(hit,refined_canidates,gdict,slices,
                                   this_center,this_slice,peers)
            if results:
                # Add to harvest and trim canidates
                harvest.update([(ee,1) for ee in results])
                cuts = [x for x in results if x in refined_canidates]
                for ee in cuts:
                    del refined_canidates[ee]
            else:
                return harvest.keys()
    return harvest.keys()
