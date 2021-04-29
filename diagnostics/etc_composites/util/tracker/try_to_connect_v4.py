def try_to_connect(copy,new_past_uci,past_scores):#,verbose=False):
    """Try to find most similar current center to past centers"""

    pick = (new_past_uci,0,0) # default result
    if past_scores[new_past_uci] == {}:
        return pick

    if past_scores[new_past_uci]:
        min_val = min(past_scores[new_past_uci].values())
        low_keys = [k for k,v in past_scores[new_past_uci].items()
                    if v == min_val]
        most_same_current_uci = low_keys[0]
        #if verbose:
        #    print "\nChecking Past Center",new_past_uci,past_scores[new_past_uci]
        #    print "\tBest Current Center",most_same_current_uci,\
        #          past_scores[new_past_uci][most_same_current_uci]

        lowest = True
        conflicts = [rival_new_past_uci for rival_new_past_uci in past_scores
                     if most_same_current_uci in
                     past_scores[rival_new_past_uci]]

        for each in conflicts: # always includes at least new_past_uci
            # exact matches are ignored as extremely unlikely.
            if past_scores[each][most_same_current_uci] < \
                   past_scores[new_past_uci][most_same_current_uci]:
                lowest = False
            #if verbose:
            #    print "\t\tConflicts",each,\
            #          past_scores[each][most_same_current_uci],lowest

        if lowest:
            pick = (most_same_current_uci,1,min_val)
            #if verbose:
            #    print "\tUse most_same_current_uci",most_same_current_uci
        else:
            #if verbose:
            #    print "\tMost_same_current_uci Not the Best"
            # remove the disqualified current_center and
            # see if the past_center has any other choices
            # if so recursively run this function on that.
            if len(past_scores[new_past_uci]) > 1:
                #if verbose:
                #    print "\t\tMany choices"
                new_past_scores = copy.deepcopy(past_scores)
                temp = {}
                for each in new_past_scores[new_past_uci]:
                    if each != most_same_current_uci:
                        temp[each] = new_past_scores[new_past_uci][each]
                new_past_scores[new_past_uci] = temp
                pick = try_to_connect(copy,new_past_uci,new_past_scores)
            else:
                pick = (most_same_current_uci,0,min_val)
                #if verbose:
                #    print "\tNo more choices for ",new_past_uci
    else:
        pick = (new_past_uci,-1,-1)
        #if verbose:
        #    print "\nChecking Past Center",new_past_uci,past_scores[new_past_uci]
        #    print "\tNo possible choices for ",new_past_uci
    return pick
