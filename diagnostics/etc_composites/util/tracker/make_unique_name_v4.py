def make_unique_name(os,basename,extension):
    """Ensure basename is not used already"""
    taken = 1
    tag = 0
    newname = "%s_%03d%s" % (basename,tag,extension)
    while taken:
        if os.path.exists(newname):
            tag += 1
            newname = "%s_%03d%s" % (basename,tag,extension)
        else:
            taken = 0
    return newname
