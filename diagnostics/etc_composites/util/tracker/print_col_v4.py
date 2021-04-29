def print_col(the_list,indent_tag,fmt,cols,width,sort_me=1):
    line = 0
    if not the_list:
        print (indent_tag+"   None")
        return
    if sort_me:
        the_list.sort()
    wide = width*cols
    end = len(the_list)
    i = 0
    for g in the_list:
        i += 1
        tag = ""
        if not line:
            tag = indent_tag
        if i == end:
            print (tag+fmt % (g))
        elif line <= wide:
            print (tag+fmt % (g),end='')
            line += width
        else:
            print (tag+fmt % (g))
            line = 0
    return
