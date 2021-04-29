#
import sys,os,time,datetime

import os.path
import commands

def get_osx_creation_time(filename):
    """Accepts a filename as a string. Gets the OS X creation date/time by parsing "mdls" output.

    Returns file creation date as a float; float is creation date as seconds-since-epoch.
    """
    status, output = commands.getstatusoutput('/usr/bin/mdls -name kMDItemFSCreationDate "%s"' % (filename))
    if status != 0:
        print('Error getting OS X metadata for %s. Error was %d. Error text was: <%s>.' %
              (filename, status, output))
        sys.exit(3)
    datestring = output.split('=')[1].strip()
    datestring_split = datestring.split(' ')
    datestr = datestring_split[0]
    timestr = datestring_split[1]
    # At present, we're ignoring timezone.
    tzstr = datestring_split[2]

    date_split = datestr.split('-')
    year = int(date_split[0])
    month = int(date_split[1])
    day = int(date_split[2])

    time_split = timestr.split(':')
    hour = int(time_split[0])
    minute = int(time_split[1])
    second = int(time_split[2])

    # convert to "seconds since epoch" to be compatible with os.path.getctime and os.path.getmtime.
    return time.mktime([year, month, day, hour, minute, second, 0, 0, -1])
    

def done():
    """This function reads in progress files from mcms software and
    returns a progress bar.

    Options/Arguments:
        start-- directory to search for progress files.

    Returns:
        progress -- % of total job completed. As well as the modification time of each file.

    Examples:

           # For short report
           pyf done.py /Volumes/scratch/output/test 1
           # For long repor
           pyf done.py /Volumes/scratch/output/test

    Notes:

    Author: Mike Bauer  <mbauer@giss.nasa.gov>

    Log:
        2008/11  MB - File created.
    """

def fractSec(s,text=1):
   if text:
       years, s = divmod(s, 31556952)
       min, s = divmod(s, 60)
       h, min = divmod(min, 60)
       d, h = divmod(h, 24)
       elapsed_time = "%02d Days %02d Hours %02d Minutes %02d Seconds " % (d,h,min,int(s))
       # estimated_completion
       return elapsed_time
   else:
#       return s # per s
       return (divmod(s, 60)[0]) # per min
#        return divmod(s, 3600)[0] # per hour

if __name__=='__main__':

    # Check for progress files in directory args[1]
    if len(sys.argv) < 2:
        print "using done.txt"
#        sys.exit("Provide a source directory")
        tf = open("done.txt","r")
        source = tf.readline()
        tf.close() 
    else:
        source = sys.argv[1]

    long_fmt = 1
    if len(sys.argv) == 3:
        long_fmt = 0

    if source.endswith("/"):
        pass
    else:
        source = source.replace ( "\n", "" )
        source = source + "/"

    print "Checking....",source

    # List progress files
    file_list = os.listdir(source)
    file_list.sort()
    pfiles = [x for x in file_list if x.find("progress") != -1]
    if not pfiles:
        sys.exit("No progress files found")
    else:
        print "Found progress files...%s" % ([x for x in pfiles])

    # Read progress files (1st line gives start and end timesteps for that file)
    print "\nProgress Report"
    start_tstep = 0
    storage = {}
    for pf in pfiles:
        read_pf = open(source+pf,"r")
        dat_file = source+pf
        dat_file = dat_file.replace("progress","att")
        year = pf.split("_")[2]
        start = 1
        for line in read_pf:
            if start:
                end_tstep = int(line)-1
                start = 0
                continue
            else:
                val = int(line)
        prog = float(val)/float(end_tstep)*100.0
        msg = ''
        if prog < 100:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(dat_file)
            atime = get_osx_creation_time(dat_file)
            fnc = fractSec(mtime-atime)
            fsize = os.path.getsize(dat_file)
            if long_fmt:
                msg = "\t%s is %0.3f%% complete. Start: %d End: %d Now: %d\n" % (pf,prog,start_tstep,end_tstep,val)
                msg = msg + "\t\tAssociated Att File:\n"
                msg = msg +  "\t\t\tFile Created  : %s\n" % time.ctime(atime)
                msg = msg + "\t\t\tLast Modified : %s\n" % time.ctime(mtime)
                msg = msg + "\t\t\tElapsed Time  : %s\n" % fnc
                if (mtime-atime):
                    step_per_second = float(val)/float(mtime-atime)
#                    step_per_second = float(val)/fractSec(mtime-atime,text=0) 
                    seconds_to_finish = (float(end_tstep)-float(val))/step_per_second
                    fnc = fractSec(seconds_to_finish)
#                    msg = msg + "\t\t\tFrame Rate (per minute): %f\n" % ((float(end_tstep)-float(val))/fractSec(mtime-atime,text=0))
                    msg = msg + "\t\t\tFrame Rate (per minute): %f\n" % (float(val)/fractSec(mtime-atime,text=0))
                    msg = msg + "\t\t\tRemaining Time: %s or %s\n" % (fnc,time.ctime(mtime+seconds_to_finish)) 
                msg = msg + "\t\t\tFile Size     : %0.1f kb" % float(fsize/1000.0)
            else:
                msg = "\t%s is %7.3f%% complete. Start: % 5d End: % 5d Now: % 5d" % (pf,prog,start_tstep,end_tstep,val)
        else:
                msg = "*\t%s is Complete." % (pf)
        storage[year] = msg

    for pf in sorted(storage.keys()):
        print storage[pf]
