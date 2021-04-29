def tree_traversal (parent,tree,harvest,level=0):
    '''Utility function for center_finder
    '''
    if parent not in harvest:
        # if use x[4] using regional mean slp
        # if use x[1] using raw center mean slp
        #slp = [x[4] for x in tree[parent] if x[0] == parent]
        slp = [x[1] for x in tree[parent] if x[0] == parent]
        harvest[parent] = slp[0]
    children = [x[0] for x in tree[parent] if x[0] not in harvest]
    if children:
        for child in children:
            if child not in harvest:
                #slp = [x[4] for x in tree[child] if x[0] == child]
                slp = [x[1] for x in tree[child] if x[0] == child]
                harvest[child] = slp[0]
            tree_traversal(child,tree,harvest,level+1)
    else:
        return
