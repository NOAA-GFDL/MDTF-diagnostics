def clean_dict(d,dump):
    """recursive delete of a key value"""
    for key,val in list(d.items()):
        if isinstance(val, dict):
            val = clean_dict(val,dump)
        if key == dump:
            del d[key]
    return d
