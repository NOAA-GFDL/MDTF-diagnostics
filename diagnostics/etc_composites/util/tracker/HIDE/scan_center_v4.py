def scan_center(seeds,candidates,gdict):

    #import print_col_v2

    harvest = {}

    #print "\t\t\t====START===="
    #print "\t\t\tseeds (%d):" % (len(seeds))
    #print_col_v2.print_col(seeds.keys(),indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)

    # Compile a list of all immediate neighbors from seeds.
    tmp = [x for seed in seeds for x in gdict[seed]]
    seed_swath = dict( (x,1) for x in tmp)
    #print "\t\t\tseed_swath (%d):" % (len(seed_swath.keys()))
    #print_col_v2.print_col(seed_swath.keys(),indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)

    # Any candidates in seed_swath's immediate neighbors?
    #   If so these can be immediately harvested
    harvest = dict( (x,1) for x in candidates if x in seed_swath)
    #print "\t\t\tharvest (%d):" % (len(harvest.keys()))
    #print_col_v2.print_col(harvest.keys(),indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)

    # Terminating condition
    if not harvest:
        return

    # Update seeds
    seeds.update(harvest)

    # Any candidates not in seed_swath's immediate neighbors?
    for h in harvest:
        del candidates[h]
    #print "\t\t\tcandidates (%d):" % (len(candidates.keys()))
    #print_col_v2.print_col(candidates.keys(),indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)
    #print "\t\t\tseeds (%d):" % (len(seeds))
    #print_col_v2.print_col(seeds.keys(),indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)

    # Rinse and Repeat: Loop over queue
    #    Terminating condition (empty candidates)
    if candidates:
        # Recursive call
        scan_center(seeds,candidates,gdict)

    #print "\t\t\tTerminating Condition"
    #print "\t\t\tHarvest Returned (%d):" % (len(harvest.keys()))
    #print_col_v2.print_col(harvest.keys(),indent_tag="\t\t\t\t",fmt="%6d",cols=6,width=10)
    #print "\t\t\t====END===="
    #print 
    return

if __name__=='__main__':
    import sys,os,pickle,copy,print_col_v2

    # For model grid defs and such
    picks = {0 : ["nra",'slp',"/Volumes/scratch/output/nra_files/","/Volumes/scratch/data/nra_4808/"],
             1 : ["nra2",'mslp',"/Volumes/scratch/output/nra2_files/","/Volumes/scratch/data/nra2_7908/"]
             }
    pick = 1
    model = picks[pick][0]
    get_var = picks[pick][1]
    shared_dir = picks[pick][2]
    slp_path = picks[pick][3]  

    fnc_out = []
    fnc_out = pickle.load(open("%scf_dat.p" % (shared_dir), 'rb'))
    (use_all_lons,search_radius,regional_nys,gdict,rdict,ldict,ijdict,
     min_centers_per_tstep,max_centers_per_tstep,max_centers_per_tstep_change,
     lapp_cutoff,hpg_cutoff) = fnc_out

    center_slices = {2405: {985000: [2404, 2549, 2405,1], 990000: [2693, 2694, 2401, 2402, 2403, 2406, 2407, 2546, 2547, 2548, 2549, 2550, 2551], 1005000: [2984, 2983], 995000: [2690, 2691, 2692, 2693, 2694, 2695, 2696, 2838, 2839, 2400, 2544, 2545, 2546, 2552], 1000000: [2689, 2690, 2691, 2692, 2693, 2694, 2695, 2696, 2697, 2836, 2837, 2838, 2839, 2840, 2841, 2982, 2983, 2400, 2401, 2402, 2403, 2404, 2405, 2406, 2407, 2544, 2545, 2546, 2547, 2548, 2549, 2550, 2551, 2552]}, 2109: {990000: [2400, 2401, 2402, 2403, 2693, 2694, 2407, 2546, 2547, 2548, 2549, 2550, 2551, 2406], 995000: [2690, 2691, 2692, 2693, 2694, 2695, 2696, 2838, 2839, 2400, 2544, 2545, 2546, 2552], 1005000: [2984, 2983], 1000000: [2689, 2690, 2691, 2692, 2693, 2694, 2695, 2696, 2697, 2836, 2837, 2838, 2839, 2840, 2841, 2982, 2983, 2400, 2401, 2402, 2403, 2404, 2405, 2406, 2407, 2544, 2545, 2546, 2547, 2548, 2549, 2550, 2551, 2552]}}


    backup = copy.deepcopy(center_slices)  
    for center in center_slices:
        print 
        print "Scanning center",center
        seeds = dict.fromkeys([center],1) 
        for this_slice in sorted(center_slices[center]):
            print "\tthis_slice",this_slice
            print "\t\tseeds (%d):" % (len(seeds.keys()))
            print_col_v2.print_col(seeds.keys(),indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
            print "\t\tCandidates or center_slices[center][this_slice] (%d):" % (len(center_slices[center][this_slice]))
            print_col_v2.print_col(center_slices[center][this_slice],indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
            print

            # Okay check slice for connection to center
            candidates = dict.fromkeys(center_slices[center][this_slice],1)
            scan_center(seeds,candidates,gdict)
            print "\t\tseeds (%d):" % (len(seeds.keys()))
            print_col_v2.print_col(seeds.keys(),indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
            harvest = [x for x in seeds if x in center_slices[center][this_slice]]
            print "\t\tharvest (%d):" % (len(harvest))
            print_col_v2.print_col(harvest,indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
            lost = [x for x in center_slices[center][this_slice] if x not in harvest]
            print "\t\tlost (%d):" % (len(lost))
            print_col_v2.print_col(lost,indent_tag="\t\t\t",fmt="%6d",cols=6,width=10)
            
            # Store what was gleaned from this_slice... note it's possible to skip
            # a slice and still have more values to add in higher slices.
            if harvest:
                backup[center][this_slice] = harvest
            else:
                del backup[center][this_slice]


#        import sys; sys.exit("Stop HERE")
