import psutil


def used_memory():
    p = psutil.Process()
    print(
        "used %f MB" % (p.memory_info().rss / 1024 ** 2)
    )  # print out the memory already been used so far

    return
