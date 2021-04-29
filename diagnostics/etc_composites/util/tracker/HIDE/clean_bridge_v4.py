def clean_bridge(near_stormy,collapsed_centers):
    """
    Due to bridging a single grid could be listed at several contours
    thus near_stormy needs to be purged of overlaps where at one
    pressure it is 'stormy' but at another lower contour it is able
    to hold an attribute status."""
    oldy = {}
    for each in near_stormy.keys():
        for dach in collapsed_centers.keys():
            if each in collapsed_centers[dach]:
                del near_stormy[each]
                break # don't remove again!
