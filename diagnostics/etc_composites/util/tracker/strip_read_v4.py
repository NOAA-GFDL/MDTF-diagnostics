def strip_read(line):
    """
    Reads parses a line from the read_file for the purpose of
    extracting certain info
    """
    parts = line.split()

    center_table = [int(parts[0]),int(parts[1]),int(parts[2]),
                    int(parts[3]),int(parts[4]),int(parts[5]),
                    int(parts[6]),int(parts[7]),int(parts[8]),
                    int(parts[9]),int(parts[10]),int(parts[11]),
                    int(parts[12]),int(parts[13]),parts[14],
                    parts[15]]
    return center_table
