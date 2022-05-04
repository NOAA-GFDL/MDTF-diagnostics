def resort(infile,strip_read,jd_key,cf):
    # Important STEP: re-read tracks and discards and sort by date as now
    # may not be in order
    read_file = open(infile,"r")
    centers = []
    centers_append = centers.append
    for line in read_file:
        # Process line
        fnc = strip_read(line)
        centers_append(fnc)
    read_file.close()
    # Sort by Julian date
    centers.sort(key=jd_key)
    # Dump to a file, overwritting original!
    save_file = open(infile,"w")
    for center in centers:
        msg = cf % (center[0],center[1],center[2],center[3],center[4],
                    center[5],center[6],center[7],center[8],center[9],
                    center[10],center[11],center[12],center[13],center[14],center[15])
        save_file.writelines(msg)
    save_file.close()
