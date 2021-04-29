"""This shows how to use the read_mcms module.

Options/Arguments:
    template.py -- template containing information about the dataset
                   and what the request is supposed to do.
#!/usr/bin/env python -tt

Returns:

Examples:
    python read_centers_v4.py template_giss.py

Notes: This should work with any standard installation of python version
    2.4 or greater. I have tested it on Apple OS-X (10.5/10.6), Ubuntu
    (8.04/9.04) and RedHat Enterprise 4.0 Linux distributions.


Author: Mike Bauer  <mbauer@giss.nasa.gov>

Log:
    2008/10  MB - File created.
    2008/10  MB - Added input checks, docstring.
    2009/11  MB - Updated to v4, removed need for model def file.
"""

#---Start of main code block.
if __name__=='__main__':

    import sys,os

    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------
    picks = {0 : "NCEP/NCAR Reanalysis 1",
             1 : "NCEP-DOE Reanalysis 2",
             2 : "NASA GISS GCM ModelE",
             3 : "GFDL GCM",
             4 : "ERA-Interim Reanalysis"}
    pick = 1
    if pick not in picks:
        sys.exit("ERROR: pick not listed in picks.")

    # This next set of lines should be copied from setup_vX.py
    # Short names by which pick will be labeled.
    models = ["nra","nra2","giss","gfdl","erai"]
    try:
        model = models[pick]
    except:
        sys.exit("ERROR: pick not listed in models.")

    # Length of file ending to replace if using year_loop
    tails = ["_att.txt","_tracks.txt","_centers.txt","_dumped_centers.txt"]
    tail = tails[0]
    cut_tail = len(tail)

    # Flags
    #  tracks: track info included in file
    #  atts: attribute info included in file
    #
    # Note tweaked self.just_center_table: in mcms_read for 
    # center/track pre-att read also watch detail_tracks names in template
    tracks = ""
    atts = ""
    if tail.find("tracks") != -1:
        tracks = 1
    if tail.find("att") != -1:
        atts = 1
    # Note atts files can contain track info so if you want
    # track statistics for an att file manually set tracks
    # to 1 here.
    #tracks = 1

    # Directory to be created for storing temporary pick specific files
    # (over written by template).
    out_path = "/Volumes/scratch/output/%s/" % (model)

    # State and end year to be extracted (over written by template).
    super_years = [1979,1979]

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
    
    ## Uncomment to create a new template
    #tmp = Create_Template()
    #sys.exit("Created New Template: %s" % (tmp.fname))

    # -------------------------------------------------------------------------
    # Start parsing the request
    # -------------------------------------------------------------------------
    if len(sys.argv) == 1:
        # Set definitions and instantiate read_mcms w/out a template
        header = "mcms_%s_%04d" % (model,int(super_years[0]))
        in_file = "%s%s%s" % (out_path,header,tail)
        what_do = {"model" : model,
                    "in_file" : in_file,
                    "out_file" : "",
                    "just_center_table" : False,
                    "detail_tracks" : tracks,
                    "as_tracks" : "",
                    "start_time" : "%04d MM DD HH SEASON" % (int(super_years[0])),
                    "end_time" : "%04d MM DD HH SEASON" % (int(super_years[0])),
                    "places" : ["GLOBAL"],
                    "include_atts" : atts,
                    "include_stormy" : atts,
                    "just_centers" : False,
                    "save_output" : False,
                    "overwrite" : True 
                    }
        # Pass in model definitions, if sf_file available this is simple.
        if model in ["nra","nra2"]:
            # For the NCAR/NCEP Reanalysis 1 and 2 these values are provided
            # and nothing need be done.
            pass
        else:
            # Provide values (if ran setup_vX.py import s_dat.p
            pass
            #what_do["tropical_end"] = row_end[tropical_n_alt]
            #what_do["tropical_start"] = row_start[tropical_s_alt]
            #what_do["maxID"] = maxid
            #what_do["land_gridids"] = list[land_gridids]
    else:
        # Use provided template
        template = sys.argv[1]
        what_do = {"template":template,}

        # Read template and extract the info, else use defs_set.
        if len(sys.argv) == 1 and not what_do:
            # Create a new template
            tmp = Create_Template()
            sys.exit("Created New Template: %s" % (tmp.fname))           
        elif what_do:
            pass
        else:
            # Use provided template
            template = sys.argv[1]
            # Fetch definitions.
            what_do = {"template":template}

    # Parse definitions.
    readit = Read_MCMS(**what_do)

    # See if request something other than everything.
    readit.check_time()
    readit.check_place()

    # Read center file
    readit.fetch_centers()





    # Recipes
    # 1) Extract centers and associate attributed and/or stormy grids.
    # 2) Same as 1, but pass stormy grids and embedded secondary centers
    #    to the primary center (the one with lowest central SLP). That is,
    #    reduce cyclone families to a single large center.
    # 3) Extract tracks. That is, reorder centers so presented as complete
    #    tracks.
    # 4) Filter centers for ocean only.
    # 5) Filter centers for DJF only.

