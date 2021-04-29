import itertools

def find_problematic(center_slices,topo_screen):
    """Problematic Test: Because the center finding routine excludes
    centers from high elevation it is possible that a real center
    is missed, and owing to its presence there is a likely situation
    where the next test will fail to detect that a contour encloses
    more than one center. For now these grids are flagged rather
    than removed."""

    grid_pool = dict( (x,list(itertools.chain(*center_slices[x].values()))) for x in center_slices)
    tmp = dict((y,list(set([x for x in grid_pool[y] if x in topo_screen]))) for y in grid_pool)
    keys = tmp.keys()
    for i in keys:
        if not tmp[i]:
            del tmp[i]
    return tmp

if __name__=='__main__':

    import sys,os,pickle

    # import arguments (use the following in the main code to save off an example)
#
#     args = (center_slices,topo_screen)
#     # to test
#     pickle.dump(args,open("fest.p", "wb",-1))
#     sys.exit()

    tmp = pickle.load(open("/Volumes/scratch/output/test/fest.p", 'rb'))

    #problematic = find_problematic(*tmp)
    #print problematic

    # Does a memory/time profile to find reason for slow downs etc.
    import cProfile
    msg = "find_problematic(tmp[0],tmp[1])"
    cProfile.run(msg,sort=1,filename="h.cprof")
    import pstats
    stats = pstats.Stats("h.cprof")
    stats.strip_dirs().sort_stats('time').print_stats(20)
