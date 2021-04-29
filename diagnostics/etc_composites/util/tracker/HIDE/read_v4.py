"""This shows how to use the read_mcms module.

#!/usr/bin/env python -tt
Options/Arguments:
    template.py -- template containing information about the dataset
                   and what the request is supposed to do.

Returns:

Examples:
    python read_v2.py template.py

Notes: This should work with any standard installation of python version
       2.4 or greater. I have tested it on Apple OS-X (10.5), Ubuntu (8.04)
       and RedHat Enterprise 4.0 Linux distributions.

Author: Mike Bauer  <mbauer@giss.nasa.gov>

Log:
    2008/10  MB - File created.
    2008/10  MB - Added input checks, docstring.
    2009/11  MB - Updated to v4.
"""

#---Start of main code block.
if __name__=='__main__':

    import sys,os

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    # Depends on length of this file name
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # Import modules used here tied to vnum
    # Modules by author, import tied to vnum for use in this program
    abase = ("create_template","read_mcms")
    for x in abase:
        tmp = "import %s%s as %s" % (x,vnum,x)
        exec(tmp)

    # pre-bind
    Create_Template = create_template.Create_Template
    Read_MCMS = read_mcms.Read_MCMS

    # -------------------------------------------------------------------------
    # Start parsing the request
    # -------------------------------------------------------------------------
    # Read template and exstract the info
    if len(sys.argv) < 1:
        # Create a new template
        tmp = Create_Template()
        sys.exit("Created New Template: %s" % (tmp.fname))
    else:
        # Use provided template
        template = sys.argv[1]

    ## Fetch definitions.
    #defs_set = {"template":template,"model":"nra_grid_defs"}

    ## Parse definitions.
    #readit = Read_MCMS(**defs_set)

    ## See if request something other than everything.
    #readit.check_time()
    #readit.check_place()

    #if readit.include_stormy:
    #    # Need to read in_file to exstract stormy gridids
    #    readit.fetch_stormy()

    ## Read center file
    #readit.fetch_centers()
#----
#     if readit.detail_tracks:
#         # Issue Warning!
#         if readit.in_file.find("byc") != -1:
#             print ("WARNING: detail_tracks requires that"
#                    "in_file contains tracked centers!")
#         # Save tracks dbase to out_file
#         readit.save_tracks()

#     if readit.as_tracks:
#         readit.dump_tracks()

# #    print readit.stormy_uci

#     centers = readit.center_holder.keys()
#     centers.sort()
# #    centers.reverse() # store in reverse order to use pop
#     print "Centers Read",len(centers)

#     for center in centers:
#         if center in readit.stormy_uci:
#             print "Primary Center",readit.center_holder[center]
#         else:
#             print "Secondary Center",readit.center_holder[center]
        
