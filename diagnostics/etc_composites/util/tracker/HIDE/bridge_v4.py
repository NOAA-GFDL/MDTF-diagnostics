def bridge(seed,field,level,cint,gdict,interation=0,done={}):
     """
     Create a bridge from the local slp field. That is, we assume that the
     underlying SLP field is continuous and smooth. Thus, contours are allowed
     to extend across an otherwise blocked pathway if neighboring grids
     suggest that a contour was skipped. To fix this we 'borrow' the some
     grids to populate the skipped contour.

     Example: Assume we are contouring A,B,C,D and are currently checking
     contour "B" such that B <= X < C. So the previous contour is A <= X < B
     and the next contour is C <= X < D.

     Search pattern: the current grid (0) has a value of "B" and the facing
     grids (1,2,3) are being examined. That is.
     123
      0

      Possible Permutations:

      1) All the same: do nothing as either contour passes or does not.

        BBB  CCC  AAA DDD
         B    B    B   B

      2) Permutations of B and (C or A): do nothing as no place where hidden
      contour exists.

        BBC CBB BCB
         B   B   B

        BBA ABB BAB
         B   B   B

        BCC CCB CBC
         B   B   B

        BAA AAB ABA
         B   B   B

      3) Permutations of B and (C and A): if A and C (or any higher value) are
      neighbors then let A be a bridge so that B contour could pass between
      A and C (or higher value).

       Orginal:
       ABC ACB BAC BCA CAB CBA ... ADB DBA DCA
        B   B   B   B   B   B       B   B   B

       Bridged:
       ABC BCB BAB BCB CBB CBA ... BDB DBA DCB
        B   B   B   B   B   B       B   B   B

     Recursive in that the bridge neighbors then checked in the same manner.
     Uses a version of the Pavlidis' Contour Tracing Algorithm (PCTA).
     """
     bridged = {}

     # Append seed to done or skip if all ready checked
     if seed in done:
          return bridged.keys()
     done[seed] = 1

     # Get surrounding 8 for this grid
     moore_grid = gdict[seed]

     # Remove seed from moore_grid
     moore_grid = moore_grid[:8]

     # Special test for grids from previous contours being examined that
     # are not totally enclosed by higher contours.
     #
     # Example: Assume we are contouring A,B,C,D and are currently checking
     # contour 'B' such that B <= X < C. So the previous contour is A <= X < B
     # and the next contour is C <= X < D.
     #
     #     A B D   Here the center grid 'A' needs a bridge to 'D' as the
     #     B A B   contour 'C' must loop inside between them... i.e. we
     #     B B B   need a bridge at the center of the moore_grid rather
     #             than at the edges which all the other tests look for.
     if field[seed] < level:
          local_slp = [x for x in moore_grid
                       if field[x] >= level+cint]
          if local_slp:
               bridged[seed] = 1

     # Any grids lower pressure than current contour?
     lower = [x for x in moore_grid if field[x] < level]
     tmp = len(lower)
     if tmp == 0 or tmp == 8:
          # Nothing found or all lower pressure
          return bridged

     # Any grids higher pressure than current contour?
     higher = [x for x in moore_grid if field[x] >= level+cint]
     tmp = len(higher)
     if tmp == 0 or tmp == 8:
          # Nothing found or all higher pressure
          return bridged

     # Any combinations of a lower and higher pressure neighbors?
     hits = []
     for i in range(9):
          if i < 7:
               if moore_grid[i] in lower and moore_grid[i+1] in higher:
                    hits.append(moore_grid[i])
                    continue
               if moore_grid[i] in higher and moore_grid[i+1] in lower:
                    hits.append(moore_grid[i+1])
          else:
               if moore_grid[7] in lower and moore_grid[0] in higher:
                    hits.append(moore_grid[7])
                    continue
               if moore_grid[7] in higher and moore_grid[0] in lower:
                    hits.append(moore_grid[0])
     # Add all hits to bridged
     for hit in hits:
          bridged[hit] = 1

     # Screen for grids already done
     hits = [x for x in hits if x not in done]
     for hit in hits:
          new_pnts = bridge(hit,field,level,cint,
                            gdict,interation+1,done)
          for ee in new_pnts:
               bridged[ee] = 1
     return bridged.keys()
