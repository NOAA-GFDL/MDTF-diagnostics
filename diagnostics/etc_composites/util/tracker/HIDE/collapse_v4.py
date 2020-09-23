def collapse(collapsed_centers,center_slices):
    for each in center_slices.keys():
        tmp_holder = {}
        for dech in center_slices[each]:
            tmp_holder.update(
                {}.fromkeys(center_slices[each][dech],1))
        collapsed_centers[each] = tmp_holder.keys()
