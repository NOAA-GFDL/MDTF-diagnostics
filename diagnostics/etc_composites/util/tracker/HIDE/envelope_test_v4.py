def envelope_test(numpy,this_center,centers,this_slice,center_slices,
                  checked_pair,ijdict,slp,lons,lats):
     N_array = numpy.array
     N_intersect1d = numpy.intersect1d
     N_alen = numpy.alen

     this_center_grids = N_array(center_slices[this_center][this_slice])
     collided = {}
     checked_pair_append = checked_pair.append
     # Check against other centers
     for other_center in centers:

          # Don't check against self
          if other_center == this_center:
               continue
          # Already check this combination?
          rev_match = "%d%d" % (other_center,this_center)
          if rev_match in checked_pair:
               continue
          checked_pair_append("%d%d" % (this_center,other_center))

          other_center_grids = N_array(center_slices[other_center][this_slice])

          # Check for intersection
          hits = N_intersect1d(this_center_grids,other_center_grids)

          if N_alen(hits):
               collided[this_center]  = 1
               collided[other_center] = 1

     return collided
