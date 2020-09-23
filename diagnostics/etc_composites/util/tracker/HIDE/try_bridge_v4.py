def try_bridge(bridge,contours,current_contours,base_contours,slpint,
               interval,gdict):#,tropical_start,tropical_end):
     """Try to make a bridge for this contour"""
     for contour in base_contours:

          if contour == base_contours[-1]:
               inter = 0
               # no need to bridge the upper most contour level
               break
          else:
               inter = interval
          done = {}

          if contour in current_contours:

               hold = []
               hold_extend = hold.extend
               # Checks pnts in current contour.
               for pnt in contours[contour]:
                    # Skip Tropics as widespread high pressure there can lead to huge
                    # recursive calls.
                    #if pnt >= tropical_start and pnt <= tropical_end:
                    #    continue
                    new_pnts = bridge(pnt,slpint,contour,inter,gdict,0,done)
                    hold_extend(new_pnts)

               # Check pnts in previous contour (sometimes needed)
               if contour > current_contours[0]:

                    # Sometimes a contour interval is skipped so
                    # need to backtrace for the right one.
                    lastone = 1
                    internew = inter
                    while lastone:
                         if contour-internew not in contours:
                              internew += inter
                         else:
                              lastone = 0
                              use_this = contour-internew
                    for pnt in contours[use_this]:
                         if pnt in hold:
                              continue
                         ## Skip Tropics as widespread high pressure there can lead to huge
                         ## recursive calls.
                         #if pnt >= tropical_start and pnt <= tropical_end:
                         #     continue
                         new_pnts = bridge(pnt,slpint,contour,inter,gdict,0,done)
                         hold_extend(new_pnts)

               # Clean up
               if hold:
                    # clean bridge
                    tt = {}.fromkeys(hold,-1)
                    hold = tt.keys()
                    # this updates contours on the fly so
                    # that the next higher contour see the
                    # bridge.
                    tmp_contours = contours[contour]
                    tmp_contours.extend(hold)
                    contours[contour] = tmp_contours

if __name__=='__main__':

    import sys,os,pickle

    # import arguments (use the following in the main code to save off an example)
#
#     args = (center_slices,collapse,gdict,wander_test,row_start,
#             row_end,im,contours)
#     # to test
#     pickle.dump(args,open("test.p", "wb",-1))
#     sys.exit()

#     tmp = pickle.load(open("/Volumes/scratch/output/test/fest.p"))

# #    filled = fill_holes(tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],tmp[7])
# #    print filled

#     # Does a memory/time profile to find reason for slow downs etc.
#     import cProfile
#     msg = "fill_holes(tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],tmp[7])"
#     cProfile.run(msg,sort=1,filename="h.cprof")
#     import pstats
#     stats = pstats.Stats("h.cprof")
#     stats.strip_dirs().sort_stats('time').print_stats(20)
