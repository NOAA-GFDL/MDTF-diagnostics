"""Provides a check on center finding and attributes etc. By comparing the
gridSLP recorded for each center with the SLP found at gridID for that center
in the original source. Ensures no miss alignment occurs. Also, check the
PDF of SLP (total) and just center to see if consistent with a standard.
#/usr/bin/env python -tt

Also, checks are made for the number of centers per timestep, track length (if applicable),
and attribute and stormy count (if applicable).

NOTE: Only works with single year files.

Options/Arguments:
    template.py -- template containing information about the dataset
                   and what the request is supposed to do.

Returns:

Examples:

Notes: This should work with any standard installation of python version
       2.4 or greater. I have tested it on Apple OS-X (10.5), Ubuntu (8.04)
       and RedHat Enterprise 4.0 Linux distributions.

Author: Mike Bauer  <mbauer@giss.nasa.gov>

Log:
    2009/1  MB - File created.
    2009/11 MB - Updated to version 4.
"""

import sys,os,math

def check_program(name):
    for dir in os.environ['PATH'].split(':'):
        prog = os.path.join(dir, name)
        if os.path.exists(prog): 
            return prog

def inv_zonal_wavenumber(latitude,wn):
    earth_radius = 6371.0002 # Earth's radius (km)
    circumference = 2.0 * math.pi * earth_radius * math.cos(math.radians(float(latitude)))
    z_len = int(round(circumference/float(wn)))
    return z_len

def run_plots(fnc):
    (setup_bins,plot_stats,numpy,plt,mdates,PDF,NA,NMean,NSTD,Summerize,
        Median,Mode,math,out_path,model,tail,atts,tracks,do_group,do_dtimes,
        do_dtimes1,maxid,max_grid_count,h_area,no_title,no_stats,psrose,
        process_data,rose_plot,depth_binsize,fig_format) = fnc

    histo_stuff = {}
    msg = ("make_plot = %d; normalized = %d; title = '%s'; xlab = '%s';",
            "ylab = '%s'; bin_width = %f; bins_left_edge = %s; sum_type = %d;",
            "xlabt = '%s'; ylabt = '%s'; ytupper = %f; ytlower = %f;",
            "xlab2d = '%s'; ylab2d = '%s'; yuppern = %f; xupper = %f;",
            "xlower = %f; trim_max = %f; trim_min = %f; may_trim = %d")
    msg = " ".join(msg)

    do = {}
    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone Count Per Time Step'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(15.0,50.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone Count Per Time Step'
    do["ytupper"] = 50.0
    do["ytlower"] = 15.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.16
    do["xupper"] = 0
    do["xlower"] = 0
    do["trim_max"] = 20
    do["trim_min"] = 0
    do["may_trim"] = 1
    histo_stuff['center_CNTS'] = msg % (do["make_plot"],
            do["normalized"],do["title"],do["xlab"],do["ylab"],
            do["bin_width"],do["bins_left_edge"],do["sum_type"],
            do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
            do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
            do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Abs. Diff. in Cyclone Count Per Time Step'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,7.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Abs. Diff. in Cyclone Count Per Time Step'
    do["ytupper"] = 7.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.6
    do["xupper"] = 7
    do["xlower"] = 0
    do["trim_max"] = 20
    do["trim_min"] = 5
    do["may_trim"] = 0
    histo_stuff['center_CNTS_DIFFS'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone GridIDs'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,10512,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone GridIds'
    do["ytupper"] = 10512
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.005
    do["xupper"] = 10512
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_GRIDIDS'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone Longitudes'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,360,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone Longitudes'
    do["ytupper"] = 360
    do["ytlower"] = .0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.007
    do["xupper"] = 360
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_LONS'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone Latitudes'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 2.5
    do["bins_left_edge"] = 'numpy.arange(-90.0,90.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone Latitudes'
    do["ytupper"] = 90.0
    do["ytlower"] = -90.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.03
    do["xupper"] = 90
    do["xlower"] = -90
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_LATS'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Number of Attributed Grids (Fraction of Hemisphere Grids)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 0.1
    do["bins_left_edge"] = 'numpy.arange(0.0,10.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Number of Attributed Grids (Fraction of Hemisphere Grids)'
    do["ytupper"] = 10
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 1.8
    do["xupper"] = 10
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_NGRIDS'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Center Intensity Class (1 = Weak 2 = Moderate 3 = Strong)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 0.99 
    do["bins_left_edge"] = 'numpy.array([0,0.99,1.99,2.99])' #'numpy.arange(0.,4.,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Center Intensity Class (1 = Weak 2 = Moderate 3 = Strong)'
    do["ytupper"] = 10
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = .8
    do["xupper"] = 4
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_INTENSITY'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    #do["make_plot"] = True
    #do["normalized"] = True
    #do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    #do["xlab"] = 'Cyclone Attributed Area (Fraction of Hemisphere)'
    #do["ylab"] = 'Normalized Relative Fraction of Total'
    #do["bin_width"] = 0.1
    #do["bins_left_edge"] = 'numpy.arange(0.0,10.0,bin_width)'
    #do["sum_type"] = True
    #do["xlabt"] = 'Time'
    #do["ylabt"] = 'Cyclone Attributed Area (Fraction of Hemisphere)'
    #do["ytupper"] = 10.0
    #do["ytlower"] = 0.0
    #do["xlab2d"] = ''
    #do["ylab2d"] = ''
    #do["yuppern"] = 1.0
    #do["xupper"] = 0
    #do["xlower"] = 0
    #do["trim_max"] = 0
    #do["trim_min"] = 0
    #do["may_trim"] = 0
    #histo_stuff['center_AREA'] = msg % (do["make_plot"],
    #    do["normalized"],do["title"],do["xlab"],do["ylab"],
    #    do["bin_width"],do["bins_left_edge"],do["sum_type"],
    #    do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
    #    do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
    #    do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone Attributed Area (Radius of Equivalent Circle, km)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 100
    do["bins_left_edge"] = 'numpy.arange(0.0,2000.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone Attributed Area (Radius of Equivalent Circle, km)'
    do["ytupper"] = 10.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.002
    do["xupper"] = 0
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_AREA'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    #do["make_plot"] = True
    #do["normalized"] = True
    #do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    #do["xlab"] = 'Total Cyclone Area (Fraction of Hemisphere)'
    #do["ylab"] = 'Normalized Relative Fraction of Total'
    #do["bin_width"] = 0.1
    #do["bins_left_edge"] = 'numpy.arange(0.0,10.0,bin_width)'
    #do["sum_type"] = True
    #do["xlabt"] = 'Time'
    #do["ylabt"] = 'Total Cyclone Area (Fraction of Hemisphere)'
    #do["ytupper"] = 10.0
    #do["ytlower"] = 0.0
    #do["xlab2d"] = ''
    #do["ylab2d"] = ''
    #do["yuppern"] = 0.6
    #do["xupper"] = 0
    #do["xlower"] = 0
    #do["trim_max"] = 0
    #do["trim_min"] = 0
    #do["may_trim"] = 0
    #histo_stuff['center_AREA_TOTAL'] = msg % (do["make_plot"],
    #    do["normalized"],do["title"],do["xlab"],do["ylab"],
    #    do["bin_width"],do["bins_left_edge"],do["sum_type"],
    #    do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
    #    do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
    #    do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Total Cyclone Area (Radius of Equivalent Circle, km)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 100
    do["bins_left_edge"] = 'numpy.arange(0.0,2000.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Total Cyclone Area (Radius of Equivalent Circle, km)'
    do["ytupper"] = 10.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.002
    do["xupper"] = 0
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_AREA_TOTAL'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone Stormy Area (Radius of Equivalent Circle, km)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 100
    do["bins_left_edge"] = 'numpy.arange(0.0,2000.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone Stomry Area (Radius of Equivalent Circle, km)'
    do["ytupper"] = 10.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.002
    do["xupper"] = 0
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_STORMY_AREA'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Cyclone Depth (hPa)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = depth_binsize
    do["bins_left_edge"] = 'numpy.arange(0.0,50.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Cyclone Depth (hPa)'
    do["ytupper"] = 50.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.1
    do["xupper"] = 70
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_DEPTH'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Distance to Nearest Center (Zonal Wavenumber)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,30.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Distance to Nearest Center (Zonal Wavenumber)'
    do["ytupper"] = 30.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.14
    do["xupper"] = 30
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_SEP'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Track Dissimilarity'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 0.05
    do["bins_left_edge"] = 'numpy.arange(0.0,5.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Track Dissimilarity'
    do["ytupper"] = 30.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 6.0
    do["xupper"] = 5
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_DISSIMILARITY'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Center Laplacian ' + r"(hPa $^\circ$Lat$^{-2}$)"
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 0.05
    do["bins_left_edge"] = 'numpy.arange(0.0,5.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] =  'Center Laplacian ' + r"(hPa $^\circ$Lat$^{-2}$)"
    do["ytupper"] = 30.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 2.0
    do["xupper"] = 2
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_LAPLACIAN'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])
    
    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Angle to Nearest Center (Degrees)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,360.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Angle to Nearest Center (Degrees)'
    do["ytupper"] = 360.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.0
    do["xupper"] = 0
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_ANGLE'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])
    histo_stuff['center_BEARING'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Empty Cyclone Count Per Time Step'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(1.0,10.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Empty Cyclone Count Per Time Step'
    do["ytupper"] = 10.0
    do["ytlower"] = 1.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.4
    do["xupper"] = 10
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_EMPTY'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'New Tracks Created Per Time Step'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,8.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'New Tracks Created Per Time Step'
    do["ytupper"] = 8.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.35
    do["xupper"] = 10
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_NEW_USI'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Dropped Tracks Per Time Step'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,8.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Dropped Tracks Per Time Step'
    do["ytupper"] = 8.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.35
    do["xupper"] = 0
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_LOST_USI'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Retained Tracks Per Time Step'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(15.0,50.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Retained Tracks Per Time Step'
    do["ytupper"] = 50.0
    do["ytlower"] = 15.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.16
    do["xupper"] = 50
    do["xlower"] = 15
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_CONTINUED_USI'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Average Track Length Per Time Step (Days)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,20.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Average Track Length Per Time Step (Days)'
    do["ytupper"] = 20.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.3
    do["xupper"] = 20
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['track_AVE'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Track Length (Days)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 1.0
    do["bins_left_edge"] = 'numpy.arange(0.0,20.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Track Length (Days)'
    do["ytupper"] = 20.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.4
    do["xupper"] = 20
    do["xlower"] = 0
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['track_LENGTH'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    do["make_plot"] = True
    do["normalized"] = True
    do["title"] = 'Model: %s Years: %s' % (model.upper(),tail)
    do["xlab"] = 'Central SLP (hPA)'
    do["ylab"] = 'Normalized Relative Fraction of Total'
    do["bin_width"] = 2.0
    do["bins_left_edge"] = 'numpy.arange(940.0,1040.0,bin_width)'
    do["sum_type"] = True
    do["xlabt"] = 'Time'
    do["ylabt"] = 'Central SLP (hPA)'
    do["ytupper"] = 20.0
    do["ytlower"] = 0.0
    do["xlab2d"] = ''
    do["ylab2d"] = ''
    do["yuppern"] = 0.04
    do["xupper"] = 1040
    do["xlower"] = 940
    do["trim_max"] = 0
    do["trim_min"] = 0
    do["may_trim"] = 0
    histo_stuff['center_SLP'] = msg % (do["make_plot"],
        do["normalized"],do["title"],do["xlab"],do["ylab"],
        do["bin_width"],do["bins_left_edge"],do["sum_type"],
        do["xlabt"],do["ylabt"],do["ytupper"],do["ytlower"],
        do["xlab2d"],do["ylab2d"],do["yuppern"],do["xupper"],
        do["xlower"],do["trim_max"],do["trim_min"],do["may_trim"])

    # Ensure the order of operations
    do_group_trim = [x.split("do_")[1] for x in do_group.keys()]
    do_group_trim = [y.split("_annual")[0] for y in do_group_trim]
    histo_stuff_sort = ["center_CNTS","center_CNTS_DIFFS",
            'center_GRIDIDS','center_LONS','center_LATS','center_SLP',
            "center_DISSIMILARITY","center_LAPLACIAN",'center_INTENSITY']
    if atts:
        tmp = ["center_NGRIDS","center_AREA","center_AREA_TOTAL",
                "center_DEPTH","center_SEP","center_ANGLE",
                "center_EMPTY","center_STORMY_AREA"]
        histo_stuff_sort.extend(tmp)
    if tracks:
        tmp = ["center_NEW_USI","center_LOST_USI","center_BEARING",
                "center_CONTINUED_USI","track_AVE","track_LENGTH"]
        histo_stuff_sort.extend(tmp)
    histo_stuff_sort_trim = [x.split("center_")[1] for x in histo_stuff_sort if
            x.find("center_") != -1]
    tmp = [x for x in histo_stuff_sort if x.find("track_") != -1]
    if tmp:
        histo_stuff_sort_trim.extend(tmp)
    histo_stuff_sort_trim = [x.lower() for x in histo_stuff_sort_trim]
    histo_data_sort = []
    for x in histo_stuff_sort_trim:
        if x in do_group_trim:
            y = "do_%s_annual" % (x)
            histo_data_sort.append(do_group[y])

    # Make time series for these
    tseries = ['center_CNTS','center_CNTS_DIFFS','track_AVE',
            'center_CONTINUED_USI','center_LOST_USI','center_NEW_USI','center_EMPTY']
    use_dtimes1 = ['center_CONTINUED_USI','center_LOST_USI','center_NEW_USI','track_AVE']
    plot_cmd_1d_histo = ["use_bins_left_edge = bins_left_edge\nuse_bins_centers = bins_centers\nif may_trim:\n\tbmax = pile2.max()\n\tif bmax <= trim_max:\n\t\tuse_bins_left_edge = numpy.arange(trim_min,trim_max,bins_width)\n\t\tuse_bins_centers = use_bins_left_edge + 0.5*bins_width\nn, bins, patches = ax.hist(pile, bins=use_bins_left_edge.tolist(), range=None,normed=normalized, cumulative=0, bottom=None,histtype='bar',align='mid',orientation='vertical', rwidth=None, log=False,facecolor='grey', alpha=0.75)",
            "if normalized:\n\tstdensity = PDF(use_bins_centers,NMean(pile2),NSTD(pile2))\n\tl = ax.plot(use_bins_centers, stdensity, 'r--', linewidth=1)\n\tif yuppern:\n\t\tax.set_ylim(0.0,yuppern)\nif xupper:\n\t\tax.set_xlim(xlower,xupper)"]
    plot_cmd_time_series = ("ax.plot(extra_pile,pile,'k.')",
                            "if len(pile)*0.25 >= 365*int(24/6):\n\tannual = smooth(numpy,pile,window_len=365*int(24/6),window='hanning')\n\tax.plot(extra_pile,annual,'g--',linewidth=6)\n\tmonthly = smooth(numpy,pile,window_len=30*int(24/6),window='hanning')\n\tax.plot(extra_pile,monthly,'r-',linewidth=1)\nelse:\n\tmonthly = smooth(numpy,pile,window_len=30*int(24/6),window='hanning')\n\tax.plot(extra_pile,monthly,'r-',linewidth=1)",
                            "days = mdates.DayLocator()",
                            "years = mdates.YearLocator()",
                            "months = mdates.MonthLocator()",
                            "yearsFmt = mdates.DateFormatter('%Y')",
                            "monthsFmt = mdates.DateFormatter('%m')",
                            "if len(pile)*0.25 < 365*int(24/6):\n\tax.xaxis.set_major_locator(months)\n\tax.xaxis.set_major_formatter(monthsFmt)\nelse:\n\tax.xaxis.set_major_locator(years)\n\tax.xaxis.set_major_formatter(yearsFmt)",
                            "datemin = extra_pile[0]",
                            "datemax = extra_pile[-1]",
                            "ax.set_xlim(datemin, datemax)",
                            "ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')",
                            "fig.autofmt_xdate()",
                            "if ytlower:\n\tif may_trim:\n\t\tbmax = pile2.max()\n\t\tif bmax <= trim_max:\n\t\t\tax.set_ylim(trim_min,trim_max)\n\t\telse:\n\t\t\tax.set_ylim(ytlower,ytupper)\n\telse:\n\t\tax.set_ylim(ytlower,ytupper)")
    #for i in plot_cmd_1d_histo:
    #   print i
    #import sys;sys.exit("HERERHERHE")

    ## Add these to wn_low and wn_high
    #wn_13 = inv_zonal_wavenumber(45.0,13)
    #wn_4 = inv_zonal_wavenumber(45.0,4)
    #print wn_13,wn_4
    #> 2177 7076
    #wn_low = "ax.annotate(r'$Wn_13', xy=(2177,0),xycoords='data',xytext=(2177,ytupper),arrowprops=dict(facecolor='black',shrink=0.05),horizontalalignment='right',verticalalignment='top')"
    #wn_low = "ax.annotate('hi',xy=(2177,0),xycoords='data',xytext=(2177,ytupper),textcoords='data')"

    # Save some stats and plots
    i = 0
    for stat_class in histo_stuff_sort:

        which_one = histo_stuff_sort.index(stat_class)
## cut
#       if stat_class == "center_CNTS_DIFFS":
#           pass
#       else:
#           continue
        if stat_class != 'center_INTENSITY':
#        if stat_class not in tseries:
            continue

        print "\t\tDoing ",stat_class

        # Pull needed info 
        fnc = setup_bins(numpy,model,tail,histo_stuff[stat_class])
        (bins_left_edge,bins_centers,bin_width,normalized,
            ytlower,ytupper,title,xlab,ylab,xlabt,ylabt,xlab2d,ylab2d,
         yuppern,xupper,xlower,trim_max,trim_min,may_trim) = fnc

        print bins_left_edge,bins_centers

        if xlab.find('Per Time Step') != -1:
            tmp = "%sfigs/pdfs/%s_%s_histo_per_step_%s" 
        else:
            tmp = "%sfigs/pdfs/%s_%s_histo_%s"
        pname_base = tmp % (out_path,model,stat_class,tail)

        if stat_class == 'center_ANGLE' or stat_class == "center_BEARING":
            if psrose:
                # plot rose diagram
                tmp = "%sfigs/pdfs/%s_%s_rose_%s" 
                pname = tmp % (out_path,model,stat_class,tail)
                bin_width = 12.
                bins_left_edge = numpy.arange(-5.0,360.0,bin_width)
                bb = bins_left_edge.tolist()
                bb.append(360.0)
                bb.append(365.0)
                bb = NA(bb)
                fncd_out = numpy.histogram(histo_data_sort[which_one],bb,normed=False)
                counts = fncd_out[0].tolist()
                bins = fncd_out[1].tolist()
                # Best as eps
                rose_plot(counts,pname,bins[0],bins[-1],bin_width,
                    verbose=0,fig_format=fig_format,title="Angle to Nearest Center")
                # This skips the regular histogram of angle, which is also made
                # of psrose is false.   
                continue

        # Plot 1d histogram/PDF
        if stat_class == "track_AVE" or stat_class == "track_LENGTH" or stat_class == "center_STORMY_AREA":
            # For c_track_ave_super and c_track_length_super need to
            # trimmed for zero values. These are there as sometimes due
            # to the way I collect these values a day as now new tracks
            # and so the lifetime average track is zero.
            # For histogram the values outside the range are ignored, but
            # this is not true for the mean, median and STD.
            tmp = [x for x in histo_data_sort[which_one] if abs(x) != 0.0]
            #if stat_class.find("AREA") != -1:
            #    pcd = plot_cmd_1d_histo[:]    
            #    pcd.append(wn_low)
            #else:
            #    pcd = plot_cmd_1d_histo
            pcd = plot_cmd_1d_histo
            msg = plot_stats(numpy,plt,mdates,PDF,NA,NMean,NSTD,Summerize,Median,Mode,
                             tmp,[],pname_base,bins_left_edge,bins_centers,
                             bin_width,tail,pcd,normalized=normalized,may_trim=may_trim,title=title,
                             xlab=xlab,ylab=ylab,trim_max=trim_max,trim_min=trim_min,
                             no_title=no_title,no_stats=no_stats,yuppern=yuppern,
                             xupper=xupper,xlower=xlower,fig_format=fig_format)
        else:
            #if stat_class.find("AREA") != -1:
            #    print "hit"
            #    pcd = plot_cmd_1d_histo.append(wn_low)
            #else:
            #    pcd = plot_cmd_1d_histo
            pcd = plot_cmd_1d_histo
            msg = plot_stats(numpy,plt,mdates,PDF,NA,NMean,NSTD,Summerize,Median,Mode,
                             histo_data_sort[which_one],[],pname_base,bins_left_edge,bins_centers,
                             bin_width,tail,pcd,normalized=normalized,may_trim=may_trim,title=title,
                             xlab=xlab,ylab=ylab,trim_max=trim_max,trim_min=trim_min,
                             no_title=no_title,no_stats=no_stats,yuppern=yuppern,
                             xupper=xupper,xlower=xlower,fig_format=fig_format)
        print "\t\t"+msg

        if stat_class in tseries:
            # Plot time-series
            pname = pname_base.replace('_histo','_time')
            pname = pname.replace("/pdfs","")
            if stat_class in use_dtimes1:
                msg = plot_stats(numpy,plt,mdates,PDF,NA,NMean,NSTD,Summerize,Median,Mode,
                                 histo_data_sort[which_one],do_dtimes1,pname,bins_left_edge,bins_centers,
                                 bin_width,tail,plot_cmd_time_series,
                                 normalized=0,may_trim=may_trim,ytlower=ytlower,
                                 ytupper=ytupper,title=title,
                                 xlab=xlabt,ylab=ylabt,trim_max=trim_max,trim_min=trim_min,
                                 no_title=no_title,no_stats=no_stats,use_grid=0,time=1,fig_format=fig_format)
            else:
                msg = plot_stats(numpy,plt,mdates,PDF,NA,NMean,NSTD,Summerize,Median,Mode,
                                 histo_data_sort[which_one],do_dtimes,pname,bins_left_edge,bins_centers,
                                 bin_width,tail,plot_cmd_time_series,
                                 normalized=0,may_trim=may_trim,ytlower=ytlower,
                                 ytupper=ytupper,title=title,
                                 xlab=xlabt,ylab=ylabt,trim_max=trim_max,trim_min=trim_min,
                                 no_title=no_title,no_stats=no_stats,use_grid=0,time=1,fig_format=fig_format)
            print "\t\t"+msg

def plot_stats(numpy,plt,mdates,PDF,NA,NMean,NSTD,Summerize,
               Median,Mode,*args,**kwargs):
    """Use matplotlib to make 1d histograms or PDFs"""

    pile = args[0]
    extra_pile = args[1]
    pname_base = args[2]
    bins_left_edge = args[3]
    bins_centers = args[4]
    bins_width = args[5]
    tail = args[6]

    # pass in a string command for the particular plot
    plot_cmd = args[7]

    # Name: normalized
    # Purpose: Counts normalized to form a probability density,
    #          i.e., n/(len(x)*dbin).
    #
    # Default: False
    if kwargs.has_key('normalized'):
        normalized = kwargs['normalized']
    else:
        normalized = False

    # Name: may_trim
    # Purpose: Allow adjustment of bins edges.
    #
    # Default: False
    #
    # Note:
    #
    if kwargs.has_key('may_trim'):
        may_trim = kwargs['may_trim']
    else:
        may_trim = 0

    # Name: title
    # Purpose: String to use as title of plot
    #
    # Default: "Title"
    #
    if kwargs.has_key('title'):
        title = kwargs['title']
    else:
        title = "Title"

    # Name: xlab
    # Purpose: String to use as label for x-axis
    #
    # Default: "Bins"
    #
    if kwargs.has_key('xlab'):
        xlab = kwargs['xlab']
    else:
        xlab = "Bins"

    # Name: ylab
    # Purpose: String to use as label for y-axis
    #
    # Default: "Count"
    #
    # Note: Watch for state of normalized.
    #
    if kwargs.has_key('ylab'):
        ylab = kwargs['ylab']
    else:
        if normalized:
            ylab = "Normalized Fraction of Total"
        else:
            ylab = "Count"

    # Name: ytlower
    # Purpose: Set lower value for y-axis time-series
    #
    # Default: None
    #
    # Note:
    #
    if kwargs.has_key('ytlower'):
        ytlower = kwargs['ytlower']
    else:
        ytlower = None

    # Name: ytupper
    # Purpose: Set upper value for y-axis time-series
    #
    # Default: None
    #
    # Note:
    #
    if kwargs.has_key('ytupper'):
        ytupper = kwargs['ytupper']
    else:
        ytupper = None

    # Name: yuppern
    # Purpose: Set upper value for y-axis normalized histograms
    #
    # Default: None (set by matplotlib
    #
    # Note:
    #
    if kwargs.has_key('yuppern'):
        yuppern = kwargs['yuppern']
    else:
        yuppern = None

    # Name: xupper
    # Purpose: Set upper value for x-axis for histograms
    #
    # Default: None (set by matplotlib
    #
    # Note:
    #
    if kwargs.has_key('xupper'):
        xupper = kwargs['xupper']
    else:
        xupper = None

    # Name: xlower
    # Purpose: Set lower value for x-axis for histograms.
    #
    # Default: 0
    #
    # Note: Only used if xupper used
    #
    if kwargs.has_key('xlower'):
        xlower = kwargs['xlower']
    else:
        xlower = 0

    # Name: trim_max
    # Purpose: Set upper value for y-axis time-series trim
    #
    # Default: None
    #
    # Note:
    #
    if kwargs.has_key('trim_max'):
        trim_max = kwargs['trim_max']
    else:
        trim_max = None

    # Name: trim_min
    # Purpose: Set upper value for y-axis time-series trim
    #
    # Default: None
    #
    # Note:
    #
    if kwargs.has_key('trim_min'):
        trim_min = kwargs['trim_min']
    else:
        trim_min = None

    # Name: stat_2d
    # Purpose: Add stats to the plot (x-axis values)
    #
    # Default: False
    #
    if kwargs.has_key('stat_2d'):
        stat_2d = kwargs['stat_2d']
    else:
        stat_2d = 0

    # Name: no_title
    # Purpose: Do not add a title to the plot
    #
    # Default: True
    #
    if kwargs.has_key('no_title'):
        no_title = kwargs['no_title']
    else:
        no_title = 1

    # Name: no_stats
    # Purpose: Do not add stats to the plot (y-axis values)
    #
    # Default: True
    #
    if kwargs.has_key('no_stats'):
        no_stats = kwargs['no_stats']
    else:
        no_stats = 1

    # Name: polar
    # Purpose: Makeing a polar-rose diagram
    #
    # Default: False
    #
    if kwargs.has_key('polar'):
        polar = 1
    else:
        polar = 0

    # Name: use_grid
    # Purpose: add a grid to the plot
    #
    # Default: True
    #
    if kwargs.has_key('use_grid'):
        use_grid = kwargs['use_grid']
    else:
        use_grid = 1

    # Name: time
    # Purpose: plot timeseries with very wide figure
    #
    # Default: False
    #
    if kwargs.has_key('time'):
        time = kwargs['time']
    else:
        time = 0

    # Name: fig_format
    # Purpose: format of the output plots
    #
    # Default: png
    #
    if kwargs.has_key('fig_format'):
        fig_format = kwargs['fig_format']
    else:
        fig_format = '.png'

    # Test for nothing
    if len(pile) < 1:
       return "Nothing to plot"

    # Make a numpy array
    pile2 = NA(pile)

    # Test for all the same value.
    if abs(pile2.max()-pile2.min()) <= 0.00000000001:
        return "Flat"

    # Create a figure (histogram) using matplotlib
    # --------------------------------------------
    pname = '%s%s' % (pname_base,fig_format)

    # Start figure
    if not polar:
        if time:
            golden_ratio = 1.61803399*2.0
            width = 40.0
        else:
            golden_ratio = 1.61803399
            width = 10.0
        hieght = width/golden_ratio

        fig = plt.figure(figsize=(width,hieght))
        ax = fig.add_subplot(111)

    # Execute Plot
    for each in plot_cmd:
        exec(each)

    # Add Labels and such
    ax.set_xlabel(xlab)
    if not polar:
        ax.set_ylabel(ylab)

    if not no_title:
        # Add title
        ax.set_title(title)

    if not no_stats:
#         fmter = "Count: %d\nMin/Max: %d/%d\nMean/Median/Mode: %.2f/%.2f/%.2f\nSTD: %.2f"
#         fnc_out = Summerize(pile)
#         stitle = fmter % (fnc_out[0],fnc_out[1][0],fnc_out[1][1],fnc_out[2],Median(pile),
#                           Mode(pile)[1][0],fnc_out[3])
        # Note mode can take a very long time for very large arrays
        fmter = "Count: %d\nMin/Max: %d/%d\nMean/Median: %.2f/%.2f\nSTD: %.2f"
        fnc_out = Summerize(pile)
        stitle = fmter % (fnc_out[0],fnc_out[1][0],fnc_out[1][1],fnc_out[2],Median(pile),fnc_out[3])
        if time:
            plt.suptitle(stitle, fontsize=4,x=0.875,y=0.93,horizontalalignment='left')
        else:
            plt.suptitle(stitle, fontsize=4,x=0.8,y=0.95,horizontalalignment='left')

    if use_grid:
        ax.grid(True)

    # Save to File
    fig.savefig(pname,dpi=144)
    plt.close('all')

    return "Made %s" % (pname)

def setup_bins(numpy,*args):
    """Set up bins for histograms"""
    # Parse input args list
    model = args[0]
    tail = args[1]
    exec(args[2])
    # Make a few extras
    bins_width = abs(bins_left_edge[0]-bins_left_edge[1])
    bins_centers = bins_left_edge + 0.5*bins_width
    bins_right_edge = bins_left_edge + bins_width

    ## To print out bins
    #fmt = "Bin % 4d: % 7.2f <= % 7.2f < % 7.2f"
    #for bin in range(len(bins_left_edge)):
    #    print fmt % (bin,bins_left_edge[bin],bins_centers[bin],
    #                 bins_right_edge[bin])
    #import sys;sys.exit()

    return (bins_left_edge,bins_centers,bin_width,normalized,
            ytlower,ytupper,title,xlab,ylab,xlabt,ylabt,xlab2d,
            ylab2d,yuppern,xupper,xlower,trim_max,trim_min,may_trim)


def smooth(numpy,x,window_len=10,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
    x: the input signal
    window_len: the dimension of the smoothing window
    window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
    flat window will produce a moving average smoothing.

    output:
    the smoothed signal
    """

    x = numpy.array(x)

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"

    s=numpy.r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]

    if window == 'flat': #moving average
        w=ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='same')

    return y[window_len-1:-window_len+1]

def error_plot(pname,plot,slp_step,lons,lats,center_loc,stormy_loc,atts_loc,msg):
    plot.create_fig()
    plot.add_field(lons,lats,slp_step,ptype='pcolor')
    plot.add_pnts(center_loc,marker='s',msize=3.,
                  mfc='black',mec='black',lw=1.)
    plot.add_pnts(center_loc,marker='x',msize=2.5,
                  mfc='black',mec='white',lw=1.)
    if stormy_loc:
        plot.add_pnts(stormy_loc,marker='o',msize=2.,
                      mfc='yellow',mec='yellow',lw=1.)
    if atts_loc:
        plot.add_pnts(atts_loc,marker='o',msize=2.,
                      mfc='red',mec='red',lw=1.)
    plot.finish(pname,title=msg)
    return "\tmMade figure: %s" % (pname)

def main(imports,import_read,defs_set,what_do,super_years,out_path,shared_path,slp_path,
        cut_tail,tracks,atts,no_plots,skip_to_plots,model,skip_high_lat,
        life_cycle_stuff,exit_on_error,plot_on_error,psrose,fig_format,
        point_source,store_netcdf):

    # Some generally useful calendar tools.
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
              6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
              11: 'November', 12: 'December'}
    months_inv = {'February': 2, 'October': 10, 'March': 3, 'August': 8, 'May': 5,
                  'January': 1, 'June': 6, 'September': 9, 'April': 4,
                  'December': 12, 'July': 7, 'November': 11}
    months_Length = {'February': 28, 'October': 31, 'March': 31, 'August': 31,
                     'May': 31, 'January': 31, 'June': 30, 'September': 30,
                     'April': 30, 'December': 31, 'July': 31, 'November': 30}
    months_Length_inv = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                         7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    mm2season = { 1  : 0, 2  : 0, 3  : 1,
                  4  : 1, 5  : 1, 6  : 2,
                  7  : 2, 8  : 2, 9  : 3,
                  10 : 3, 11 : 3, 12 : 0}

    seasons = ["annual","ndjfma","mjjaso"]
    mm2season = { 1  : 1, 2  : 1, 3  : 1,
                  4  : 1, 5  : 2, 6  : 2,
                  7  : 2, 8  : 2, 9  : 2,
                  10 : 2, 11 : 1, 12 : 1}

    print "\tSetting up...",

    # Years to check
    years = range(int(super_years[0]),int(super_years[-1])+1)

    # Tell the plotting part to pool all whole record for making
    # plots rather than doing them year by year. Set to 0 or ""
    # for year by year plots.
    #super_run = ""
    super_run = "%04d-%04d" % (int(super_years[0]),int(super_years[-1]))

    # Maximum area per hemisphere
    #earth_radius = 6371.2 # Earth's radius (km)
    #h_area = 2.0 * math.pi * (earth_radius * earth_radius) * (1.0 - math.sin(math.radians(30.0)))
    h_area = 127524124.138

    #
    # Threshold for error flags
    #

    # If Normally distributed then
    #
    # At least 68.27% of the data would be within 1 standard deviations of the mean.
    # At least 95% of the data would be within 1.96 standard deviations of the mean.
    # At least 99% of the data would be within 2.576 standard deviations of the mean.
    # At least 99.73% of the data would be within 3.0 standard deviations of the mean.
    # At least 99.9999998027% of the data would be within 6.0 standard deviations of the mean.

    # Chebyshev's inequality: states that in any data sample or probability distribution,
    # nearly all the values are close to the mean value, and provides a quantitative
    # description of "nearly all" and "close to". Such that:
    #
    # At least 50% of the values are within SQRT(2) standard deviations from the mean.
    # At least 75% of the values are within 2 standard deviations from the mean.
    # At least 89% of the values are within 3 standard deviations from the mean.
    # At least 94% of the values are within 4 standard deviations from the mean.
    # At least 96% of the values are within 5 standard deviations from the mean.
    # At least 97% of the values are within 6 standard deviations from the mean.
    # At least 98% of the values are within 7 standard deviations from the mean.

    spread_norm = 3 # 99.73%
    spread_cheb = 6 # 97%

    # Total Center Count per Time Step
    # c_cnt stats (looks approximately normal)
    #    Min/Max/Mean = 5/21.49/36
    #    STD = 3.26
    # Example: if c_cnt < total_center_count_per_time_step_spread[0]:
    total_center_count_per_time_step_mean = 21.49
    total_center_count_per_time_step_std = 3.26
    total_center_count_per_time_step_spread = (
        round(total_center_count_per_time_step_mean-(total_center_count_per_time_step_std*spread_norm)),
        round(total_center_count_per_time_step_mean+(total_center_count_per_time_step_std*spread_norm))
        )

    # Maximum absolute difference allowed in number of centers at any given
    # time-step from the previous time-step. This is a percentage of the
    # previous time-step count.
    # c_cnt_diff stats (looks something like chi distribution)
    #    Min/Max/Mean = 0/1.3/8
    #    STD = 1.12
    # So given c_cnt mean of 22 then +- 22*0.25 or 6
    # Example: if c_cnt_diff > round(center_count_before*c_cnt_threshold):
    c_cnt_threshold = 0.25

    # Maximum difference between the SLP stored for the center and that
    # pulled from the reference SLP field at the grid location the center
    # is reported to be. Detected mismatch or error in locating something.
    # SLP is int(slp*1000) so 1 is a difference of 0.001 hPa...
    # Example:
    #     slp_test = abs(readit.center_holder[center][ids['GridSLP']]-slp_step[key])
    #     if slp_test > slp_error:
    slp_error = 1

    # Maximum number of usi (tracks) terminated in a given time step.
    #    Min/Max/Mean = 0/1.7/10
    #    STD = 1.28
    # Example:
    #    if lost_usi > max_lost_usi:
    max_lost_usi = round(1.7+(1.28*spread_cheb))

    # Maximum number of usi (tracks) added in a given time step.
    #    Min/Max/Mean = 0/1.7/9
    #    STD = 1.28
    # Example:
    #    if new_usi > max_new_usi:
    max_new_usi = max_lost_usi

    # Maximum number of attributed grids given to a single center
    # as a % of total grids in a hemisphere.
    #    Min/Max/Mean = 0/0.68/10
    #    STD = 0.80
    # Example:
    #    if (ngrids/float(max_grid_count))*100.0 > ngrid_max:
    ngrid_max =  0.68 + (0.80*spread_cheb)

    # Maximum surface area attributed to a single center:
    # as a % of total area in a hemisphere.
    #    Min/Max/Mean = 0/1.4/26
    #    STD = 1.67
    # Example:
    #    if (float(area_total)/h_area)*100.0 > area_max:
    area_max =  1.4 + (1.67*spread_cheb)

    # Maximum number of stormy grids
    #    Min/Max/Mean = ?
    #    STD = ?
    # Example:
    #    if len(readit.stormy_uci[key2]) > stormy_max:
#FIX
    stormy_max = 1000

    # Maximum difference in the SLP of the center and the
    # outermost contour for a given center.
    #    Min/Max/Mean = 0/9/72
    #    STD = 8.76
    # Example:
    #    if depth > depth_max:
    depth_max = (8.99 + (8.76*spread_cheb))*1000.0
    depth_min = 0

    # Maximum distance (great circle) between two centers.
    # Converted to zonal wavenumber at the latitude of the center.
    # Note this is not along latitude to could exceed synoptic scale.
    #    Min/Max/Mean = 1/10.87/41
    #    STD = 4.33
    # Example:
    #    if sep > sep_max:
    sep_max = 10.87 + (4.33*spread_cheb)
    sep_min = 1

#cut
    # If want to turn off all the threshold warnings:
    total_center_count_per_time_step_spread = (0,100)
    c_cnt_threshold = 1.5
    slp_error = 0
    max_lost_usi = 1000
    max_new_usi = 1000
    ngrid_max =  1000
    area_max = 10e10
    stormy_max = 1000
    depth_max = 100000
    depth_min = 0
    sep_max = 100000
    sep_min = 0

    # Quit on error else just send message to logfile?
    exit_on_error = 0
    if exit_on_error:
        do_this = 'print smsg; print msg; print date_stamp; sys.exit(center_stamp)'
    else:
        do_this = 'print smsg; print msg; print date_stamp; print center_stamp'

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    # Import needed modules.
    for i in imports:
        exec(i)

    # Fetch definitions and impose those set in defs_set.
    defs = defs.defs(**defs_set)

    depth_binsize = float(defs.interval)*0.001
    
    # Get some definitions. Note must have run setup_vx.py already!
    sf_file = "%ss_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(sf_file, 'rb'))
        (im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
                dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
                bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
                bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
                super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
                var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
                no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
                land_gridids,troubled_centers,faux_grids) = fnc_out
        # Save memory
        del troubled_centers
        del land_gridids
        del lat_edges
        del lon_edges
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
    tstepsperday = float(24.0/timestep)

    # Update over_write values
    if over_write_slp_path:
        slp_path = over_write_slp_path
    if over_write_out_path:
        out_path = over_write_out_path

    if atts and not skip_to_plots:
        # Fetch attribute specific info.
        af_file = "%saf_dat.p" % (shared_path)
        try:
            fnc_out = pickle.load(open(af_file, 'rb'))
            inputs = ("darea","distance_lookup","angle_lookup","close_by",
                    "wander_test","gdict","neighbor_test")
            darea = fnc_out[inputs.index("darea")]
            del fnc_out
        except:
            sys.exit("\n\tWARNING: Error reading or finding %s." % (af_file))

        # Fetch model grid specific information.
        cf_file = "%scf_dat.p" % (shared_path)
        try:
            fnc_out = pickle.load(open(cf_file, 'rb'))
            inputs = ("use_all_lons","search_radius","regional_nys","gdict",
                    "rdict","ldict","ijdict","min_centers_per_tstep",
                    "max_centers_per_tstep","max_centers_per_tstep_change",
                    "lapp_cutoff","hpg_cutoff")
            ijdict = fnc_out[inputs.index("ijdict")]
            del fnc_out
        except:
            sys.exit("\n\tWARNING: Error reading or finding %s." % (cf_file))

    # Used for plots
    tropical_end = row_end[tropical_n_alt]
    tropical_start = row_start[tropical_s_alt]
    # Maximum number of grids per hemisphere
    max_grid_count = maxid - (tropical_end-tropical_start)
    # If true plots have not title or stats embedded.
    no_title = False
    no_stats = False

    # pre-bind
    Create_Template = create_template.Create_Template
    Read_MCMS = read_mcms.Read_MCMS
    Pull_Data = pull_data.pull_data
    #Make_Wavenumber = wavenumber.zonal_wavenumber
    PDF = mlab.normpdf; Bin = numpy.histogram
    Summerize = stats.ldescribe; Median = stats.lmedian; Mode = stats.lmode
    Nsum = numpy.sum; N1d = numpy.ravel; NT = numpy.take
    NZ = numpy.nonzero; NAOX = numpy.apply_over_axes; NO = numpy.ones
    ND = numpy.divide; NW = numpy.where; NNAN = numpy.isnan
    NINF = numpy.isinf; NA = numpy.array; NMean = numpy.mean
    NSTD = numpy.std; NM = numpy.multiply; Nint = numpy.int
    RLV = rhumb_line_nav.rhumb_line_nav
    if store_netcdf:
        Save_NetCDF = save_netcdf.Save_NetCDF 
    if not no_plots or plot_on_error:
        Plot_Map = plot_map.plotmap
        grid2ij = grid2ij.grid2ij

    # For unwinding reads
    ids = {'YYYY' : 0,'MM' : 1, 'DD' : 2, 'HH' : 3, 'JD' : 4,
           'CoLat' : 5, 'Lon' : 6, 'GridID': 7, 'GridSLP' : 8,
           'RegSLP' : 9, 'GridLAP' : 10, 'Flags' : 11, 'Intensity' : 12,
           'Dissimilarity' : 13, 'UCI' : 14, 'USI' : 15, 'NGrids' : 16,
           'Area' : 17, 'Depth' : 18, 'NearestCenterDist' : 19,
           'NearestCenterAngle' : 20, 'MinOuterEdgeDist' : 21,
           'MaxOuterEdgeDist' : 22, 'AveOuterEdgeDist' : 23,
           'ATTS' : 24}

    stats_path = "%sstats/tmp/" % (out_path)
    print "Jimmy"
    print stats_path

    stat_titles = ["cnts_diffs_","cnts_","lons_","lats_","gridids_","slp_",
            "dissimilarity_","laplacian_","intensity_"]
    att_titles = ["ngrids_","area_","area_total_","depth_","sep_",
            "angle_","empty_","stormy_area_"]
    track_titles = ["new_usi_","lost_usi_","continued_usi_",
            "track_length_","track_ave_","track_age_","bearing_"]
    life_cycle_titles = ["life_cycle_"]
    tmp = [x.rstrip("_") for x in stat_titles]
    tr = tmp
    
    if atts:
             stat_titles.extend(att_titles)
             tmp = [x.rstrip("_") for x in att_titles]
             tr.extend(tmp)
    if tracks:
        stat_titles.extend(track_titles)
        tmp = [x.rstrip("_") for x in track_titles]
        tr.extend(tmp)
        if life_cycle_stuff:
            stat_titles.extend(life_cycle_titles)
            tmp = [x.rstrip("_") for x in life_cycle_titles]
            tr.extend(tmp)
    stat_titles.sort()
    stat_group = dict.fromkeys(tr,None)

    # How data is stored and read   
    as_ints = ["cnts_diffs_","cnts_","gridids_","ngrids_","empty_","new_usi_",
            "lost_usi_","continued_usi_",'intensity_']
    as_float = ["lons_","lats_","slp_","area_","area_total_","depth_","sep_",
            "angle_","stormy_area_","track_length_","track_ave_","track_age_",
            "bearing_","dissimilarity_","laplacian_"]

    if list(set(as_ints) & set(as_float)):
        msg = "\tNon-Empty Intersection of as_ints and as_floats: %s"
        sys.exit(msg % repr(list(set(as_ints) & set(as_float))))
    if len(stat_group) != len(as_ints)+len(as_float):
        msg = "\tMismatch between stat_group and as_ints and as_floats: %d %d"
        #sys.exit(msg % (len(stat_group),len(as_ints)+len(as_float)))
        print "JIMMY COMMMENTED OUT SYS.EXIT ISSUE HERE"

    # Scale area by the surface area of a hypothetical cyclone with
    # a circular radius of 1000 km ignoring small spherical component.
    radius = 1000.0 # hypothetical radius of 1000 km
    SArea = math.pi * (radius*radius)

    map_group = ["cnts_","slp_","intensity_","bearing_",
            "laplacian_","dissimilarity_"]
    if atts:
        map_group.extend(["empty_","area_","area_total_","depth_","sep_",
            "angle_","stormy_area_"])
    if tracks:
        map_group.extend(["track_length_","track_age_"])
    map_group.sort()
    data_index = [len(map_group),len(seasons),maxid]
    di = data_index 
    # Store Mean and STD of each stat_group member
    mean_sums = NM(numpy.ones(di,dtype=numpy.float),-1.0)
    mean_cnts = NM(numpy.ones(di,dtype=numpy.float),-1.0)
        ## See if dumped/discarded center file
        #dumped = 0
        #if readit.in_file.find("dumped") != -1:
        #    dumped = 1
        #    dumped_cnt_freq = numpy.zeros((jm*im,nflags),dtype=numpy.float)
        #else:
        #    dumped_cnt_freq = numpy.zeros((1),dtype=numpy.float)

    if not skip_to_plots:

        # -------------------------------------------------------------------------
        # Start parsing the request (Centers)
        # -------------------------------------------------------------------------

        # Parse definitions.
        readit = Read_MCMS(**what_do)

        # Determine the source of the centers
        source = os.path.basename(readit.in_file).split(".")[0]

        # See if request something other than everything.
        readit.check_time()
        readit.check_place()

        if tracks:
            # Some limitations to using track data when reading year by year
            # is that tracks that fall in two years are not fully scene. This
            # is only a problem for collecting statistics in this manner.
            readit2 = Read_MCMS(**what_do)
            readit2.check_time()
            readit2.check_place()

        if defs.keep_log:
            # Redirect stdout to file instead of screen (i.e. logfiles)
            # open with a buffer size of zero to make updates rapid
            ttt = "%d_%d" % (years[0],years[-1])
            lfile = "%s/logfile_%s_%s.txt" % (out_path,model,ttt)
            screenout  = sys.stdout
            log_file   = open(lfile, 'w',0)
            sys.stdout = log_file

        if plot_on_error:
            # Instantiate matplotlib
            plot =  Plot_Map(clevs=[980,1020,2],cints=[960.0,1013.0])

        used_steps = [0 for x in range(len(seasons))]

        for loop_year in years:

            print "\n=============%d=============" % (loop_year)
            
            print "JIMMY HERE"

            # Note Likely to need ADJUSTMENT for differing datasets!
            # Adjust in_file name
            tag = str(readit.in_file[-cut_tail-4:-cut_tail])
            readit.in_file = readit.in_file.replace(tag,str(loop_year))
            
            # Open data files
            base_names = ["%sc_%s%s_%s_%s.txt" % (stats_path,j,model,i,str(loop_year))
                    for j in stat_titles for i in seasons]
            #stat_files = dict.fromkeys(base_names,None)
            stat_files = {}
            for fileName in base_names:
            #for fileName in stat_files:
                try:
                    stat_files[fileName] = open(fileName, "w")
                    #print "Opened: %s" % fileName
                except IOError:
                    print "File not found: %s" % fileName
            if readit.include_stormy:
                # Need to read in_file to extract stormy gridids
                readit.fetch_stormy()
            else:
                readit.stormy_uci = {}
            print readit
            # ISSUE HERE.  RELATED TO CALL TO read_mcms_v4.py
            if tracks:
                readit.detail_tracks = in_file.replace(".txt","_tracks_dbase.txt")

            # Read center file, if tracks then return sorted tracks dbase.
            print atts
            readit.fetch_centers()
            print "NOT HERE"
            if tracks:
                # Re-read centers
                readit.detail_tracks = ""
                readit.as_tracks = ""
                readit.fetch_centers()
            
            print "JIMMY HOUND"
            ## Speed things up A LOT by making a sorted list of centers
            # and shrinking it as we find centers.
            centers = readit.center_holder.keys()
            centers.sort()
            centers.reverse() # store in reverse order to use pop
            print "\nCenters Read",len(centers)

            # Extract all Julian dates
            alldates = []
            alldates = [readit.center_holder[x][4] for x in readit.center_holder]

            # Get unique dates via dictionary
            b = {}
            for i in alldates: b[i] = 0
            alldates = b.keys()
            alldates.sort() # sort as dictionary unsorted
            nsteps = len(alldates)
            print "Number of unique dates/times:",nsteps

            if tracks and loop_year != years[-1]:
                # Tracks can extend into the next year, which if not accounted for
                # give the impression of shorter track lengths etc. at the end of
                # each year if tracks read in on a year-to-year basis as they are
                # here (centers not so affected). Solution is to read a year ahead
                # and extend any tracks starting in this year with centers from next year.
                readit2.in_file = readit.in_file.replace(str(loop_year),str(loop_year+1))
                readit2.detail_tracks = 0
                readit2.fetch_centers()
                centers2 = readit2.center_holder.keys()
                centers2.sort()

                # readit.sorted_tracks has the usi for all tracks starting this year
                # so screen and add any centers with these usi to the correct
                # center in  readit.sorted_tracks
                addon_uci_usi = [(readit2.center_holder[x][14],readit2.center_holder[x][15])
                             for x in readit2.center_holder if
                             readit2.center_holder[x][15] in readit.sorted_tracks.keys()]
                 #import copy
                 #s = copy.deepcopy(readit.sorted_tracks)
                 #just_usi = {}
                #Okay add these uci to the usi that they point too in  readit.sorted_tracks
                # don't add centers to centers etc as will be double counted....
                for uci_usi in addon_uci_usi:
                    uci = uci_usi[0]
                    usi = uci_usi[1]
                    old = readit.sorted_tracks[usi]
                    old.append(uci)
                    readit.sorted_tracks[usi] = old
            #         just_usi[usi] = 1
            #     for usi in just_usi:
            #         print usi,len(s[usi]),"->",len(readit.sorted_tracks[usi])

            # -------------------------------------------------------------------------
            # Pull in reference field
            # -------------------------------------------------------------------------

            # Open data file, extract data and model definitions
            exec(import_read)
            fnc = pull_data.pull_data(NetCDF,numpy,slp_path,file_seperator,loop_year,
                    defs.read_scale,var_slp,var_time,lat_flip,lon_shift)
            (slp,times,the_time_units) = fnc
            del fnc

            # Work with the time dimension a bit.
            # This is set in setup_vX.py
            jd_fake = 0
            if the_calendar != 'standard':
                # As no calendar detected assume non-standard
                jd_fake = 1

            tsteps = len(times)
            the_time_range = [times[0],times[tsteps-1]]
            start = "%s" % (the_time_units)
            tmp = start.split()
            tmp1 = tmp[2].split("-")
            tmp2 = tmp[3].split(":")
            tmp3 = tmp2[2][0]
            start = "%s %s %04d-%02d-%02d %02d:%02d:%02d" % \
                    (tmp[0],tmp[1],int(tmp1[0]),int(tmp1[1]),
                     int(tmp1[2]),int(tmp2[0]),int(tmp2[1]),
                     int(tmp3))
            # Warning this could get weird for non-standard
            # calendars if not set correctly (say to noleap)
            # in setup_vX.py
            cdftime = netcdftime.utime(start,calendar=the_calendar)
            get_datetime = cdftime.num2date
            dtimes = [get_datetime(times[step]) for step in range(0,tsteps)]

            uci_starters = ['%4d%02d%02d%02d' % (d.year,d.month,d.day,d.hour) for d in dtimes]

            # CHECK 1: Be sure that alldates matches dtimes. That is, that same date-times
            # and all covered. This also ensures no date-times skipped in center file.
            if len(alldates) != len(times):
                smsg = "\nFail Check 1: Length of date arrays differ."
                msg = "\tlen(alldates) = %d\n\tlen(times) = %d" % (len(alldates),len(times))
                exec(do_this)

            # -------------------------------------------------------------------------
            # Big Loop over Time
            # -------------------------------------------------------------------------
            print ""
            fmt = "\tDoing step: %05d\n\tDateTime: %04d\\%02d\\%02d\\%02d"
            fmt_c = "\tDoing Center: %s"
            last_center = ""
            used_step = 0
            centers_used = 0
            center_count_before = -1
            if tracks:
                # Due to constrains on tracking don't start checking cyclone
                # counts for the first 7 days
                import pdb; pdb.set_trace()
                start_check_2 = (24*7)/timestep
            else:
                # Center only checks can start after the 4th timestep.
                start_check_2 =  4

            # Set the buffer on each side of the pmin
            if life_cycle_stuff:
                life_cycle_width = int(round(48.0/float(timestep)))
                life_cycle_width_max = int(round(life_cycle_width*1.5))
                total_life_cycle_min = life_cycle_width_max*2 + 1

            last_usi = []
            past_lon_lats = {}

#CUT
            #tsteps = 30

            for step in range(0,tsteps):

                # Date of interest
                uci_starter = uci_starters[step]

                date_stamp =  fmt % (step,int(uci_starter[:4]),int(uci_starter[4:6]),
                                     int(uci_starter[6:8]),int(uci_starter[8:10]))
                center_stamp = ""

                s_num = mm2season[int(uci_starter[4:6])]
                s_nam = seasons[s_num]

                # Shrink center_holder to speed searches
                current_centers = []
                found_none = 1
                if len(centers) < 1:
                    more = 0
                else:
                    more = 1
                while more:
                    # See if overflow from last read useful or read new record
                    if last_center:
                        center = last_center
                        last_center = ""
                    else:
                        center = centers.pop()
                        if len(centers) < 1: # No more centers
                            more = 0
                    # Store if center falls on wanted date.
                    if center.startswith(uci_starter,0,10):
                        current_centers.append(center)
                        found_none = 0
                    else:
                        # Store for next time
                        last_center = center
                        more = 0
                if found_none:
                    # No centers found
                    smsg = "\tError: No Centers Found!"
                    msg = ""
                    exec(do_this)

                # Get SLP field, make 1d integer array. To allow for exact comparisons
                # impose a fixed accuracy (significant digits) via defs.accuracy.
                slp_step = NM(slp[step,:,:].copy(),defs.accuracy)
                slp_step.shape = im*jm
                slp_step = slp_step.astype(Nint)
    
                used_steps[s_num] += 1
                used_steps[0] += 1
 
                if plot_on_error:
                    center_loc_all = []
                    atts_loc_all = []
                    stormy_loc_all = []

                    for center in current_centers:

                        # Collect center locations
                        llon = readit.center_holder[center][ids['Lon']]*0.01
                        llat = 90.0 - (readit.center_holder[center][ids['CoLat']]*0.01)
                        center_loc_all.append((llon,llat))
                        if atts:
                            # Count attributes grids
                            if len(readit.center_holder[center]) == 16:
                                pass # empty center
                            else:
                                for j in readit.center_holder[center][ids['ATTS']]:
                                    ix = ijdict[j][2]
                                    atts_loc_all.append((ix,ijdict[j][3]))
                            # Add Stormy if any
                            if readit.center_holder[center][ids['UCI']] in readit.stormy_uci.keys():
                                for j in readit.stormy_uci[readit.center_holder[center][ids['UCI']]]:
                                    ix = ijdict[j][2]
                                    stormy_loc_all.append((ix,ijdict[j][3]))

                stat_group['cnts'] = len(current_centers)
                if step < start_check_2:
                    center_count_before = stat_group['cnts']
                stat_group['cnts_diffs'] = abs(stat_group['cnts']  - center_count_before)
                ##print "\tFound: %d Centers\n\t\tDiff: %d"  % (c_cnt,c_cnt_diff)

                # CHECK 2: Ensure that current center count is not wildly different than
                # the previous one. This is a relative test.
                if stat_group['cnts_diffs'] > round(center_count_before*c_cnt_threshold):
                    smsg = "Fail Check 2: Short-term center cnt difference."
                    msg = "\tc_cnt = %d\n\tcenter_count_before = %d"
                    msg = msg % (stat_group['cnts'],center_count_before)
                    if plot_on_error:
                        mout = error_plot("%s/figs/error_check_2_%s.png" % (out_path,uci_starter),
                                          plot,NM(slp_step[:],0.001),lons,lats,center_loc_all,
                                          stormy_loc_all,atts_loc_all,smsg)
                        print mout
                    exec(do_this)
                used_step += 1
                centers_used += stat_group['cnts']
                ##print "\t\tC_cnt Ave: %d" % (centers_used/used_step)

                # CHECK 3: Ensure the current center count is within
                # time average values. This is an absolute test.
                smsg = "Fail Check 3: Long-term center cnt difference."
                if stat_group['cnts'] < total_center_count_per_time_step_spread[0]:
                    msg = "\tcnts = %d < %d"
                    msg = msg % (stat_group['cnts'],total_center_count_per_time_step_spread[0])
                    if plot_on_error:
                        mout = error_plot("%s/figs/error_check_3a_%s.png" % (out_path,uci_starter),
                                          plot,NM(slp_step[:],0.001),lons,lats,center_loc_all,
                                          stormy_loc_all,atts_loc_all,smsg)
                        print mout
                    exec(do_this)
                if stat_group['cnts'] > total_center_count_per_time_step_spread[1]:
                    msg = "\tcnts = %d >  %d"
                    msg = msg % (stat_group['cnts'],total_center_count_per_time_step_spread[1])
                    if plot_on_error:
                        mout = error_plot("%s/figs/error_check_3b_%s.png" % (out_path,uci_starter),
                                          plot,NM(slp_step[:],0.001),lons,lats,center_loc_all,
                                          stormy_loc_all,atts_loc_all,smsg)
                        print mout
                    exec(do_this)

                if tracks:
                    # Find list of current USI (i.e. active tracks)
                    #current_usi = [readit.center_holder[center][ids['USI']] for center in current_centers]
                    #new_usi = len([x for x in current_usi if x not in last_usi])
                    #continued_usi = len([x for x in current_usi if x in last_usi])
                    #lost_usi = len([x for x in last_usi if x not in current_usi])
                    stat_group['current_usi'] = [readit.center_holder[center][ids['USI']] for center in current_centers]
                    stat_group['new_usi'] = len([x for x in stat_group['current_usi'] if x not in last_usi])
                    stat_group['continued_usi'] =  len([x for x in stat_group['current_usi'] if x in last_usi])
                    stat_group['lost_usi'] = len([x for x in last_usi if x not in stat_group['current_usi']])

                    # CHECK 7: Ensure tracks are new, continued, lost at realistic rate:
                    # Don't check at beginning of record
                    if step > start_check_2:
                        smsg = "Fail Check 7: Tracking Error"
                        if stat_group['lost_usi'] > max_lost_usi:
                            msg = "too many tracks discontinued %d" % (stat_group['lost_usi'])
                            if plot_on_error:
                                mout = error_plot("%s/figs/error_check_7a_%s.png" % (out_path,uci_starter),
                                                  plot,NM(slp_step[:],0.001),lons,lats,center_loc_all,
                                                  stormy_loc_all,atts_loc_all,msg)
                                print mout
                            exec(do_this)
                        if stat_group['new_usi'] > max_new_usi:
                            msg = "too many tracks created %d" % (stat_group['new_usi'])
                            if plot_on_error:
                                mout = error_plot("%s/figs/error_check_7b_%s.png" % (out_path,uci_starter),
                                                  plot,NM(slp_step[:],0.001),lons,lats,center_loc_all,
                                                  stormy_loc_all,atts_loc_all,msg)
                                print mout
                            exec(do_this)

                        ## Special case with looking at life_cycle
                        #if life_cycle_stuff:
                        #    # Loop over new tracks:
                        #    for new_guy in [x for x in current_usi if x not in last_usi]:
                        #        # Check is long enough to composite
                        #        if len(readit.sorted_tracks[new_guy]) >= life_cycle_width_max:
                        #            # Examine the SLP structure of the track
                        #            center_SLPs = [readit.center_holder[c][ids['GridSLP']] for c in readit.sorted_tracks[new_guy]]
                        #            print center_SLPs
                        #            slp_min = min(center_SLPs)
                        #            slp_min_loc = center_SLPs.index(slp_min)
                        #            print slp_min,slp_min_loc
                        #            # Check enough SLPs on each side of slp_min_loc
                        #            if slp_min_loc+1 >= life_cycle_width:
                        #                if len(center_SLPs)-slp_min_loc >= life_cycle_width:
                        #                    # Okay collect stats.
                        #                    filled_life_cycle_min = life_cycle_width_max + 1
                        #                    filled_life_cycle = [0 for x in range(total_life_cycle_min+1)]
                        #                    print filled_life_cycle_min,total_life_cycle_min,filled_life_cycle
                        #                    #13 25 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        #                    sys.exit()
                        #                     #okay make filld_life_cycle such at center is always pegged on a fixed
                        #                     #colume and then start counting up and put 0s in until reach beginning
                        #                     #of center_SLPs... can tell by saying okay slp_min_loc = filled_life_cycle_min center
                        #                     #minus the difference in left edge so is  life_cycle_width_max
                        #                     ##c_life_cycle_f.write("%d," % (area_total))
                #life_cycle_width = int(round(48.0/float(timestep)))
                #life_cycle_width_max = int(round(life_cycle_width*1.5))
                #total_life_cycle_min = life_cycle_width_max*2 + 1

                # -------------------------------------------------------------------------
                # Loop over current cyclone
                # -------------------------------------------------------------------------
                stat_group['empty'] = 0
                for center in current_centers:
                    stat_group['gridids'] = readit.center_holder[center][ids['GridID']]
                    key = stat_group['gridids']
                    center_stamp = fmt_c % (repr(readit.center_holder[center]))

                    # Retrieve center gridid
                    zone = [key]
                    azone = []
                    szone = []
                    mean_holder = [-1 for x in range(len(map_group))]

                    if plot_on_error:
                        center_loc = []
                        atts_loc = []
                        stormy_loc = []

                        # Collect center locations
                        llon = readit.center_holder[center][ids['Lon']]*0.01
                        llat = 90.0 - (readit.center_holder[center][ids['CoLat']]*0.01)
                        center_loc.append((llon,llat))

                    if atts:
                        # Count attributes grids
                        if len(readit.center_holder[center]) == 16:
                            pass # empty center
                        else:
                            for j in readit.center_holder[center][ids['ATTS']]:
                                if plot_on_error:
                                    ix = ijdict[j][2]
                                    atts_loc.append((ix,ijdict[j][3]))
                                if not point_source:
                                   zone.append(j)
                                   azone.append(j)
                        # Add Stormy if any
                        if readit.center_holder[center][ids['UCI']] in readit.stormy_uci.keys():
                            for j in readit.stormy_uci[readit.center_holder[center][ids['UCI']]]:
                                if plot_on_error:
                                    ix = ijdict[j][2]
                                    stormy_loc.append((ix,ijdict[j][3]))
                                if not point_source:
                                    zone.append(j)
                                    szone.append(j)

                    # CHECK 4: Ensure that GridSLP is the same as the SLP in the
                    # reference field at this time.
                    slp_test = abs(readit.center_holder[center][ids['GridSLP']]-slp_step[key])
                    smsg = "Fail Check 4: GridSLP differs from SLP reference."
                    if slp_test > slp_error:
                        msg = "readit.center_holder[center][ids['GridSLP']] \n\t = %d < %d"
                        msg = msg % (readit.center_holder[center][ids['GridSLP']],slp_step[key])
                        if plot_on_error:
                            mout = error_plot("%s/figs/error_check_4_%s_%s.png" % (out_path,uci_starter,key),
                                              plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                              stormy_loc,atts_loc,msg)
                            print mout
                        exec(do_this)

                    # Pull central SLP
                    stat_group['slp'] = float(readit.center_holder[center][ids['GridSLP']])*0.001
                    mean_holder[map_group.index('slp_')] = stat_group['slp']

                    # CHECK 5: Ensure the encoded Latitude is realistic:
                    smsg = "Fail Check 5: Center Latitude Error"
                    stat_group['lats'] = 90.0 - (readit.center_holder[center][ids['CoLat']]*0.01)
                    if abs(stat_group['lats']) > 90.0:
                        msg = "Latitude Excess: %g" % (stat_group['lats'])
                        if plot_on_error:
                            mout = error_plot("%s/figs/error_check_5a_%s_%s.png" % (out_path,uci_starter,key),
                                              plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                              stormy_loc,atts_loc,msg)
                            print mout
                        exec(do_this)
                    if abs(stat_group['lats']) < 15.0: # see tropical_boundary in setup_vx.py
                        msg = "Latitude Excess: %g" % (stat_group['lats'])
                        if plot_on_error:
                            mout = error_plot("%s/figs/error_check_5b_%s_%s.png" % (out_path,uci_starter,key),
                                              plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                              stormy_loc,atts_loc,msg)
                            print mout
                        exec(do_this)

                    # CHECK 6: Ensure the encoded Latitude is realistic:
                    smsg = "Fail Check 6: Center Longitude Error"
                    stat_group['lons'] = readit.center_holder[center][ids['Lon']]*0.01
                    if abs(stat_group['lons']) > 360.0:
                        msg = "Longitude Excess: %g" % (stat_group['lons'])
                        if plot_on_error:
                            mout = error_plot("%s/figs/error_check_6_%s_%s.png" % (out_path,uci_starter,key),
                                              plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                              stormy_loc,atts_loc,msg)
                            print mout
                        exec(do_this)

                    # CHECK 7: Ensure tracks are new, continued, lost at realistic rate:
                    if tracks:
                         ## Don't check at beginning of record
                         #if step > start_check_2:
                         #    smsg = "Fail Check 7: Tracking Error"
                         #if lost_usi > max_lost_usi:
                         #    msg = "too many tracks discontinued %d" % (lost_usi)
                         #    if plot_on_error:
                         #        mout = error_plot("%s/figs/error_check_7a_%s_%s.png" % (out_path,uci_starter,key),
                         #                          plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                         #                          stormy_loc,atts_loc,msg)
                         #        print mout
                         #    exec(do_this)
                         #if new_usi > max_new_usi:
                         #    msg = "too many tracks created %d" % (new_usi)
                         #    if plot_on_error:
                         #        mout = error_plot("%s/figs/error_check_7b_%s_%s.png" % (out_path,uci_starter,key),
                         #                          plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                         #                          stormy_loc,atts_loc,msg)
                         #        print mout
                         #    exec(do_this)
                        # update
                        last_usi = stat_group['current_usi']
                        # Find Some track info, if not beginning of record or
                        # an empty center.
                        if step > start_check_2 and len(readit.center_holder[center]) != 16:
#Mike
                            if not readit.sorted_tracks.has_key(readit.center_holder[center][ids['USI']]):
                                print readit.sorted_tracks.keys()
                            these_tracks = readit.sorted_tracks[readit.center_holder[center][ids['USI']]]
                            if center not in these_tracks:
                                print center
                                print these_tracks
#Mike
                            track_index = these_tracks.index(center)
                            stat_group['track_age'] = float(track_index)/float(tstepsperday)
                            mean_holder[map_group.index('track_age_')] = stat_group['track_age']
                            if track_index == 0:
                                mean_holder[map_group.index('track_length_')] = float(len(these_tracks))/float(tstepsperday)
                            # Find bearing to the previous track (can't for
                            # first center in track). Because of the limitations of bearing 
                            # finding at high latitudes the apparent bearing could be large but not relevant.
                            if center != these_tracks[0]:
                                    if abs(stat_group['lats']) <= skip_high_lat:
                                        # Bearing always from rhumb line, gcd can't be used!
                                        # Use UCI to get rough lon,lat... only
                                        # approximate! In fact, very crude, if
                                        # not unusable. 
                                        clon = stat_group['lons']
                                        clat = stat_group['lats']
                                        plon = past_lon_lats[readit.center_holder[center][ids['USI']]][0]
                                        plat = past_lon_lats[readit.center_holder[center][ids['USI']]][1]
                                        fnc = RLV(clon,clat,plon,plat,True)
                                        if fnc[1] > 222.0:
                                            # Very close centers (stationary)
                                            # can give very large angles, but
                                            # not meaningful ones.
                                            mean_holder[map_group.index('bearing_')] = fnc[0]
                                            stat_group['bearing'] = fnc[0]
                                        else:
                                            stat_group['bearing'] = -1
                            else:
                                past_lon_lats[readit.center_holder[center][ids['USI']]] = (stat_group['lons'],stat_group['lats'])
                        else:
                            past_lon_lats[readit.center_holder[center][ids['USI']]] = (stat_group['lons'],stat_group['lats'])
                    stat_group['dissimilarity'] = float(readit.center_holder[center][ids['Dissimilarity']])*0.01
                    stat_group['laplacian'] = float(readit.center_holder[center][ids['GridLAP']])*0.001
                    stat_group['intensity'] = int(readit.center_holder[center][ids['Intensity']])
                    mean_holder[map_group.index('dissimilarity_')] = stat_group['dissimilarity'] 
                    mean_holder[map_group.index('laplacian_')] = stat_group['laplacian'] 
                    mean_holder[map_group.index('intensity_')] = stat_group['intensity'] 
                    mean_holder[map_group.index('cnts_')] = 1.0
                    if atts:
                        # Check for empty centers
                        if len(readit.center_holder[center]) == 16:
                            # Empty center
                            stat_group['empty'] += 1
                            mean_holder[map_group.index('empty_')] = 1
                        else:
                            # Regular center

                            # CHECK 8: Ensure Attribute Count is realistic:
                            smsg = "Fail Check 8: NGrids Error"
                            stat_group['ngrids'] = readit.center_holder[center][ids['NGrids']]
                            if (stat_group['ngrids']/float(max_grid_count))*100.0 > ngrid_max:
                                msg = "NGrid Excess: %g" % (stat_group['ngrids'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_8a_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)
                            elif stat_group['ngrids'] < 1:
                                msg = "NGrid None: %g" % (stat_group['ngrids'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_8b_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)

                            # CHECK 9: Ensure Attribute Area is realistic:
                            smsg = "Fail Check 9: Area Error"
                            stat_group['area'] = readit.center_holder[center][ids['Area']]

                            # Add Stormy if any area
                            key2 = readit.center_holder[center][ids['UCI']]
                            area_s = 0
                            if key2 in readit.stormy_uci.keys():
                                #stat_group['stormy'] = len(readit.stormy_uci[key2])
                                # Add to area as primary center
                                area_s = int(reduce(add,[darea[x] for x in readit.stormy_uci[key2]]))
                                # Check 10: Ensure stormy grid count reasonable:
                                smsg = "Fail Check 10: Stormy Error"
                                if len(readit.stormy_uci[key2]) > stormy_max:
                                    msg = "Number of Stormy grids %d" % (len(readit.stormy_uci[key2]))
                                    if plot_on_error:
                                        mout = error_plot("%s/figs/error_check_10_%s_%s.png" % (out_path,uci_starter,key),
                                                          plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                          stormy_loc,atts_loc,msg)
                                        print mout
                                    exec(do_this)
                            stat_group['stormy_area'] = area_s
                            stat_group['area_total'] = stat_group['area']+area_s
                            if area_s:
                                mean_holder[map_group.index('stormy_area_')] = area_s
                            mean_holder[map_group.index('area_')] = readit.center_holder[center][ids['Area']]
                            mean_holder[map_group.index('area_total_')] = stat_group['area_total'] 
                            if (float(stat_group['area_total'])/h_area)*100.0 > area_max:
                                msg = "Area Excess: %g" % (stat_group['area'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_9_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)

                            # Check 11: Ensure depth reasonable:
                            stat_group['depth'] = readit.center_holder[center][ids['Depth']]*0.001
                            mean_holder[map_group.index('depth_')] = stat_group['depth'] 
                            smsg = "Fail Check 11: Depth Error"
                            if stat_group['depth'] > depth_max:
                                msg = "Depth too high: %d\n" % (stat_group['depth'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_11a_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)
                            if stat_group['depth'] < depth_min:
                                msg = "Depth too low: %d" % (stat_group['depth'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_11b_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)

                            # Check 12: Ensure NearestCenterDist reasonable:
                            #sep = readit.center_holder[center][ids['NearestCenterDist']]
                            stat_group['sep'] = Make_Wavenumber(stat_group['lats'],readit.center_holder[center][ids['NearestCenterDist']]*1.0)
                            mean_holder[map_group.index('sep_')] = stat_group['sep'] 
                            smsg = "Fail Check 12: Seperation Error"
                            if stat_group['sep'] > sep_max:
                                msg = "NearestCenterDist too high: %d" % (stat_group['sep'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_12a_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)
                            if stat_group['sep'] < sep_min:
                                msg = "NearestCenterDist too low: %d" % (stat_group['sep'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_12b_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)

                            # Check 13: Ensure NearestCenterAngle reasonable:
                            stat_group['angle'] = readit.center_holder[center][ids['NearestCenterAngle']]
                            mean_holder[map_group.index('angle_')] = stat_group['angle']
                            smsg = "Fail Check 13: Angle Error"
                            if stat_group['angle'] > 360:
                                msg = "NearestCenterDist too high: %d" % (stat_group['angle'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_13a_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)
                            if stat_group['angle'] < 0:
                                msg = "NearestCenterDist too low: %d" % (stat_group['angle'])
                                if plot_on_error:
                                    mout = error_plot("%s/figs/error_check_13b_%s_%s.png" % (out_path,uci_starter,key),
                                                      plot,NM(slp_step[:],0.001),lons,lats,center_loc,
                                                      stormy_loc,atts_loc,msg)
                                    print mout
                                exec(do_this)

                            # Accrue Stats
                            for ss in [0,s_num]:
                                
                                t =  att_titles[:]
                                if tracks:
                                    if step > start_check_2:
                                        t.append("track_age_")
                                        t.append("bearing_")
                                for sn in t:
                                    if sn == "empty_":
                                        continue
                                    sf = '%s%s' % (sn,seasons[ss])
                                    base_name = "%sc_%s%s_%s_%s.txt" % (stats_path,sn,model,seasons[ss],str(loop_year))
                                    if skip_high_lat:
                                        if abs(stat_group['lats']) <= skip_high_lat:
                                            if sn in as_float:
                                                stat_files[base_name].writelines("%f," % (stat_group[sn.rstrip("_")]))
                                            else:
                                                stat_files[base_name].writelines("%d," % (stat_group[sn.rstrip("_")]))
                                    else:
                                        if sn in as_float:
                                            stat_files[base_name].writelines("%f," % (stat_group[sn.rstrip("_")]))
                                        else:
                                            stat_files[base_name].writelines("%d," % (stat_group[sn.rstrip("_")]))

                    # End att check
                    for ss in [0,s_num]:
                        for sn in ["lons_","lats_","gridids_","slp_","dissimilarity_","laplacian_",'intensity_']:
                            sf = '%s%s' % (sn,seasons[ss])
                            base_name = "%sc_%s%s_%s_%s.txt" % (stats_path,sn,model,seasons[ss],str(loop_year))
                            if skip_high_lat:
                                if abs(stat_group['lats']) <= skip_high_lat:
                                    if sn in as_float:
                                        stat_files[base_name].writelines("%f," % (stat_group[sn.rstrip("_")]))
                                    else:
                                        stat_files[base_name].writelines("%d," % (stat_group[sn.rstrip("_")]))
                            else:
                                if sn in as_float:
                                    stat_files[base_name].writelines("%f," % (stat_group[sn.rstrip("_")]))
                                else:
                                    stat_files[base_name].writelines("%d," % (stat_group[sn.rstrip("_")]))
                    """
                    # JIMMY
                    for pnt in azone:
                        sn = map_group.index('area_')
                        for ss in [0,s_num]:
                            if mean_holder[sn] < 0.0:
                                    continue
                            if mean_cnts[sn,ss,pnt] < 0.0:
                                # Initialize as non-mission point.
                                mean_cnts[sn,ss,pnt] = 0.0
                                mean_sums[sn,ss,pnt] = 0.0
                            mean_sums[sn,ss,pnt] += mean_holder[sn]
                            mean_cnts[sn,ss,pnt] += 1
                    for pnt in szone:
                        sn = map_group.index('stormy_area_')
                        for ss in [0,s_num]:
                            if mean_holder[sn] < 0.0:
                                    continue
                            if mean_cnts[sn,ss,pnt] < 0.0:
                                # Initialize as non-mission point.
                                mean_cnts[sn,ss,pnt] = 0.0
                                mean_sums[sn,ss,pnt] = 0.0
                            mean_sums[sn,ss,pnt] += mean_holder[sn]
                            mean_cnts[sn,ss,pnt] += 1
                    for pnt in zone:
                        for ss in [0,s_num]:
                            for sn in range(len(map_group)):
                                if sn == map_group.index('stormy_area_'):
                                    continue
                                if sn == map_group.index('area_'):
                                    continue
                                if mean_holder[sn] < 0.0:
                                    continue
                                if mean_cnts[sn,ss,pnt] < 0.0:
                                    # Initialize as non-mission point.
                                    mean_cnts[sn,ss,pnt] = 0.0
                                    mean_sums[sn,ss,pnt] = 0.0
                                #if sn == map_group.index('angle_'):
                                #    print pnt, mean_holder[sn],mean_sums[sn,ss,pnt],mean_cnts[sn,ss,pnt]
                                mean_sums[sn,ss,pnt] += mean_holder[sn]
                                mean_cnts[sn,ss,pnt] += 1
                                #if sn == map_group.index('angle_'):
                                #    print "\t",mean_sums[sn,ss,pnt],mean_cnts[sn,ss,pnt]
                    #JIMMY
                    """
                # -------------------------------------------------------------------------
                # End Loop over current cyclone
                # -------------------------------------------------------------------------
                # Accrue Stats
                for ss in [0,s_num]:
                    if atts:
                        nlist = ["empty_","cnts_diffs_","cnts_"]
                    else:
                        nlist = ["cnts_diffs_","cnts_"]
                    for sn in nlist:
                        sf = '%s%s' % (sn,seasons[ss])
                        base_name = "%sc_%s%s_%s_%s.txt" % (stats_path,sn,model,seasons[ss],str(loop_year))
                        stat_files[base_name].writelines("%d," % (stat_group[sn.rstrip("_")]))

                if tracks:
                    if step > start_check_2:
                        # note means dtimes not exactly the same!
                        for ss in [0,s_num]:
                            for sn in ["new_usi_","lost_usi_","continued_usi_"]:
                                sf = '%s%s' % (sn,seasons[ss])
                                base_name = "%sc_%s%s_%s_%s.txt" % (stats_path,sn,model,seasons[ss],str(loop_year))
                                stat_files[base_name].writelines("%d," % (stat_group[sn.rstrip("_")]))

                        # NOTE Sometimes no new tracks so ave_len will be zero as
                        # it measures the length of only starting tracks at this
                        # time. So can ignore zero values! Need to write a zero
                        # so that date/time index of arrays for times series
                        # plots work.
                        #
                        # Find total track length of all current_centers that
                        # are the start of a new track (i.e., uci = usi)
                        check = [x for x in current_centers if x in readit.sorted_tracks]
                        stat_group["track_ave"] = 0.0
                        lens = [float(len(readit.sorted_tracks[x]))/tstepsperday for x in check]
                        if lens:
                            import pdb; pdb.set_trace()
                            stat_group["track_ave"]  = sum(lens)/len(lens)
# tmp
                         #if stat_group["track_ave"]  > 0 and stat_group["track_ave"]  < 1:
                         #    print "check",check
                         #    print "lens",lens
                         #    for each in check:
                         #        print "\t",each,"->",readit.sorted_tracks[each]
                         #    print
                        for ss in [0,s_num]:
                            sn = "track_ave_"
                            sf = '%s%s' % (sn,seasons[ss])
                            base_name = "%sc_%s%s_%s_%s.txt" % (stats_path,sn,model,seasons[ss],str(loop_year))
                            stat_files[base_name].writelines("%5.2f," % (stat_group[sn.rstrip("_")]))
                            sn = "track_length_"
                            sf = '%s%s' % (sn,seasons[ss])
                            base_name = "%sc_%s%s_%s_%s.txt" % (stats_path,sn,model,seasons[ss],str(loop_year))
                            for x in lens:
                                stat_files[base_name].writelines("%5.2f," % (x))

                # Reset
                center_count_before = stat_group['cnts']
            # -------------------------------------------------------------------------
            # End Year
            # -------------------------------------------------------------------------

            # Save memory when pull_data called in loop stores a copy of slp
            #  and thus doubles the memory footprint of the code.
            del pull_data,slp_step,slp,uci_starters
            del tsteps,the_time_range,start,tmp1,tmp2,tmp3,cdftime

            # Pickle datetime objects:
            fmt1 = "%s/stats/tmp/dtimes_%s_%d.p"
            pickle.dump((dtimes,start_check_2),open(fmt1 % (out_path,model,loop_year),"wb",-1))
            del dtimes
            # Close Files
            for fileName, fileObject in stat_files.iteritems():
                if fileObject:
                    fileObject.close()
                    #print "Closed: %s" % fileName
            print "Done with this year"

        # -------------------------------------------------------------------------
        # End Big Loop over Time
        # -------------------------------------------------------------------------
        
        # Pickle mean objects:
        fmt1 = "%s/stats/tmp/meanmaps_%s_%s.p"
        pickle.dump((mean_sums,mean_cnts,used_steps),open(fmt1 % (out_path,model,super_run),"wb",-1))
        del mean_sums,mean_cnts

        if defs.keep_log:
            log_file.close()
            sys.stdout = screenout # redirect stdout back to screen
        if no_plots:
            sys.exit("No Plots: early out")

    # -------------------------------------------------------------------------
    # Done with Files... now making plots
    # -------------------------------------------------------------------------

    #   By_Step: Which means the average value of all cyclones per timestep.
    #            For example, the average number of cyclone present per
    #            timestep.
    #   By_Cyclone: Which means the average value over all cyclones.
    #               For example, the average area per cyclone.
    #import sys; sys.exit("Stop Here")
    super_titles = ["%ssuper_" % (x) for x in stat_titles]
    super_group = {}
    dtimes_super = []
    dtimes1_super = []
    dtime_seasons_super = {}
    dtime1_seasons_super = {}
    stat_group_ext = {}
    stat_group_ext_titles = []
    if stat_group.has_key('current_usi'):
        del stat_group["current_usi"]
    xfx = stat_group.keys()
    xfx.sort()
    for sn in xfx:
        for ss in range(len(seasons)):
            sf = '%s_%s' % (sn,seasons[ss])
            stat_group_ext[sf] = None
            stat_group_ext_titles.append(sf)
    float_files = ['%s%s' % (sn,seasons[ss]) 
            for ss in range(len(seasons)) for sn in as_float]

    for loop_year in years:
        print "\n=============%d=============" % (loop_year)
        # Read file
        print "\tReading data files ...",

        base_names = ["%sc_%s%s_%s_%s.txt" % (stats_path,j,model,i,str(loop_year))
                for j in stat_titles for i in seasons]
        stati_files = {}
        for i in range(len(base_names)):
            stati_files[base_names[i]] = stat_group_ext_titles[i]
        for fileName, var in stati_files.iteritems():
            try:
                tline = open(fileName,"r").readlines()
                print "\n\t\tRead: %s from %s" % (var,fileName),
                if var.find("ngrids") != -1:
                    # Make ngrids a % of total grids in a hemisphere.
                    stat_group_ext[var] = [int(x) for x in tline[0][:-1].split(",")]
                    stat_group_ext[var] = [(float(x)/float(max_grid_count))*100.0 for x in stat_group_ext[var]]
                elif var.find("area") != -1:
                    stat_group_ext[var] = [float(x) for x in tline[0][:-1].split(",")]
                    # Make area a % of total hemisphere
                    #stat_group_ext[var] = [(float(x)/h_area)*100.0 for x in stat_group_ext[var]]
                    # Make area a radius of an equivalent circle.
                    stat_group_ext[var] = [math.sqrt((float(x)/math.pi)) for x in stat_group_ext[var]]
                elif var in float_files:
                    stat_group_ext[var] = [float(x) for x in tline[0][:-1].split(",")]
                else:
                    stat_group_ext[var] = [int(x) for x in tline[0][:-1].split(",")]
                print "\t\t\tExample:",stat_group_ext[var][:2] 
                # Remove missing values
                if var.find("bearing") != -1:
                    stat_group_ext[var] = [x for x in stat_group_ext[var] if x >= 0.0]
                if var.find("dissimilarity") != -1:
                    stat_group_ext[var] = [x for x in stat_group_ext[var] if x > 0.0]
            except IOError:
                print "Error reading:" % fileName

            # Accrue values
            if var in super_group:
                super_group[var].extend(stat_group_ext[var])
            else:
                super_group[var] = stat_group_ext[var]
            msg = "\t\tRead: %s from %s with %d entries\n\t\tstored in super_group[%s] with %d entries"
            print msg % (var,fileName,len(stat_group_ext[var]),var,len(super_group[var]))
        
        # unPickle datetime objects:
        fmt = "%s/stats/tmp/dtimes_%s_%d.p"
        (dtimes,start_check_2) = pickle.load(open(fmt % (out_path,model,loop_year), 'rb'))
        # Tweak for Tracking based time series.
        dtimes1 = dtimes[start_check_2+1:]
        dtimes_super.extend(dtimes)
        dtimes1_super.extend(dtimes1)
        print "done."

        # Partition dtimes by season
        dtime_seasons = {}
        dtime1_seasons = {}
        dtime_seasons[0] = dtimes
        if 0 not in dtime_seasons_super.keys():
            dtime_seasons_super[0] = dtime_seasons[0]
        else:
            dtime_seasons_super[0].extend(dtime_seasons[0])
        dtime1_seasons[0] = dtimes1
        if 0 not in dtime1_seasons_super.keys():
            dtime1_seasons_super[0] = dtime1_seasons[0]
        else:
            dtime1_seasons_super[0].extend(dtime1_seasons[0])
        for ss in range(len(seasons)):
            if ss == 0:
                continue
            this_season = [x for x in mm2season if mm2season[x] == ss]
            dtime_seasons[ss] = [x for x in dtimes if x.month in this_season]
            dtime1_seasons[ss] = [x for x in dtimes1 if x.month in this_season]
            if ss not in dtime_seasons_super.keys():
                dtime_seasons_super[ss] = dtime_seasons[ss]
                dtime1_seasons_super[ss] = dtime1_seasons[ss]
            else:
                dtime_seasons_super[ss].extend(dtime_seasons[ss])
                dtime1_seasons_super[ss].extend(dtime1_seasons[ss])

        # Note: Some of these plots are on a per timestep basis. That is, the
        # number are averages based on all centers per a given
        # timestep. This is the case for all the time_series. Otherwise,
        # the plots represent all cases.
        if loop_year <= years[-1]:
            # This set of plots are done for each year. In this
            # case only 'annual' data is used.
            do_group = {}
            for var in stat_group_ext.keys():
                if var.find("annual") != -1:
                    do_var = "do_%s" % (var)
                    do_group[do_var] = stat_group_ext[var]
            if not atts:
                for var in att_titles:
                    ss = "annual"
                    do_var = 'do_%s%s' % (var,seasons[ss])
                    do_group[do_var] = []
            if not tracks:
                for var in track_titles:
                    ss = "annual"
                    do_var = 'do_%s%s' % (var,seasons[ss])
                    do_group[do_var] = []
            tail = str(loop_year)
            do_dtimes = dtimes
            do_dtimes1 = dtimes1
            fnc = (setup_bins,plot_stats,numpy,plt,mdates,PDF,NA,NMean,
                   NSTD,Summerize,Median,Mode,math,out_path,model,
                   tail,atts,tracks,do_group,do_dtimes,do_dtimes1,
                   maxid,max_grid_count,h_area,no_title,no_stats,psrose,
                   process_data,rose_plot,depth_binsize,fig_format)
            run_plots(fnc)
            
            if loop_year == years[-1]:
                print "\n=============%s=============" % (super_run)
                # These plots are the accumulation over the entire record.
                tail = super_run
                do_group = {}
                for var in super_group.keys():
                    do_var = "do_%s" % (var)
                    do_group[do_var] = super_group[var]
                if not atts:
                    for var in att_titles:
                        ss = "annual"
                        do_var = 'do_%s%s' % (var,seasons[ss])
                        do_group[do_var] = []
                if not tracks:
                    for var in track_titles:
                        ss = "annual"
                        do_var = 'do_%s%s' % (var,seasons[ss])
                        do_group[do_var] = []
                do_dtimes = dtimes_super
                do_dtimes1 = dtimes1_super
                fnc = (setup_bins,plot_stats,numpy,plt,mdates,PDF,NA,NMean,
                       NSTD,Summerize,Median,Mode,math,out_path,model,
                       tail,atts,tracks,do_group,do_dtimes,do_dtimes1,
                       maxid,max_grid_count,h_area,no_title,no_stats,psrose,
                       process_data,rose_plot,depth_binsize,fig_format)
                run_plots(fnc)

    # unPickle mean objects:
    fmt1 = "%sstats/tmp/meanmaps_%s_%s.p"
    (mean_sums,mean_cnts,used_steps) = pickle.load(open(fmt1 % (out_path,model,super_run), 'rb'))
    print fmt1 % (out_path,model,super_run)

    roots = {}
    roots['angle_'] = 'Angle to Nearest Neighboring Center (degrees)'
    roots['area_'] = 'Cyclone Attributed Area (Radius of Equivalent Circle, km)'
    roots['area_total_'] = 'Total Cyclone Area (Radius of Equivalent Circle, km)'
    roots['bearing_'] = 'Angle to Next Center Along Track (degrees)'
    roots['cnts_'] = 'Occurrence of Cyclone Centers (% of Total Time Steps)'
    roots['depth_'] = 'Cyclone Depth (hPa)' 
    roots['dissimilarity_'] = 'Track Dissimilarity'
    roots['empty_'] =  'Occurrence of Empty Cyclones (% of Total Time Steps)'
    roots['intensity_'] ='Center Intensity Class (1 = Weak 2 = Moderate 3 = Strong)' 
    roots['laplacian_'] = 'Center Laplacian ' + r"(hPa $^\circ$Lat$^{-2}$)"
    roots['sep_'] = 'Distance to Nearest Center (Zonal Wavenumber)'
    roots['slp_'] = 'Central SLP (hPA)' 
    roots['stormy_area_'] = 'Cyclone Stormy Area (Radius of Equivalent Circle, km)'
    roots['track_age_'] = 'Cyclone Age (Days from Track Inception)'
    roots['track_length_'] = 'Average Track Length Per Time Step (Days)'
    roots['area_freq_'] = 'Occurrence of Attributed Grids (% of Total Time Steps)'
    roots['area_total_freq_'] = 'Occurrence of Attributed + Stormy Grids (% of Total Time Steps)'
    roots['area_stormy_freq_'] = 'Occurrence of Stormy Grids (% of Total Time Steps)'
    roots['track_length_'] = 'Average Track Length Per Time Step (Days)'

    # Set to adjust colors to focus on mid-latitude values, which means
    # some tropical regions will be blownout.
    zoom = 1

    map_group.extend(["area_freq_","area_total_freq_","area_stormy_freq_"])

    for ss in range(len(seasons)):
        for sn in range(len(map_group)):

            # Note mean maps of angle, based on the rose diagram, are going to
            # seem odd as often the nearest center angle is often either near 90 or
            # 270 degrees (in front or behind) so the mean is near 180!
            normalization = 0.0
            cbar = "Paired"
            #cbar = "spectral"
            #cbar = "jet"
            cints = ""
            clevs = ""
            ptype='pcolor'
            zoomed = 0
            if map_group[sn] == "angle_" or map_group[sn] == "bearing_":
                cints = [0.0,360.0]
                if zoom:
                    if map_group[sn] == "angle_":
                        cints = [140.0,240.0]
                    else:
                         cints = [0.0,140.0]
                    zoomed = 1
            elif map_group[sn].find("area") != -1:
                cints = [500.0,2000.0]
                if zoom:
                    cints = [800.0,1600.0]
                    zoomed = 1
            elif map_group[sn] == "cnts_":
                #cbar = "bone_r"
                cints = [0.0,70.0]
                normalization = (1.0/float(used_steps[ss])) * 100.0
            elif map_group[sn] == "empty_":
                #cbar = "bone_r"
                cints = [0.0,10.0]
                normalization = (1.0/float(used_steps[ss])) * 100.0
            if map_group[sn].find("freq") != -1:
                normalization = (1.0/float(used_steps[ss])) * 100.0
                cints = [0.0,40.0]
            elif map_group[sn] == 'depth_':
                cints = [0.0,20.0]
                if zoom:
                    cints = [5.0,20.0]
                    zoomed = 1
            elif map_group[sn] == 'dissimilarity_':
                cints = [0.0,0.5]
                if zoom:
                    cints = [0.1,0.4]
                    zoomed = 1
            elif map_group[sn] == 'intensity_':
                cints = [1.0,3.0]
                if zoom:
                    cints = [1.4,2.6]
                    zoomed = 1
            elif map_group[sn] == 'laplacian_':
                cints = [0.0,1.0]
                if zoom:
                    cints = [0.4,0.9]
                    zoomed = 1
            elif map_group[sn] == 'sep_':
                cints = [4.0,13.0]
                if zoom:
                    cints = [6.0,12.0]
                    zoomed = 1
            elif map_group[sn] == 'slp_':
                cints = [960.0,1010.0]
                if zoom:
                    cints = [965.0,1000.0]
                    zoomed = 1
            elif map_group[sn] == 'track_age_':
                cints = [1.2,3.0]
                if zoom:
                    cints = [1.0,3.0]
                    zoomed = 1
            elif map_group[sn] == 'track_length_':
                cints = [1.0,8.0]
                if zoom:
                    cints = [1.5,4.0]
                    zoomed = 1

            #if ss != 0:
            #    continue
            #if map_group[sn].find("freq") != -1:
            #    pass
            #else:
            #    continue

            fplot = Plot_Map(missing=-1.0,color_scheme=cbar,cints=cints,clevs=clevs)

            if map_group[sn].find("freq") != -1:
                if map_group[sn].find("area_total_freq_") != -1:
                    counter = numpy.array(mean_cnts[map_group.index('area_total_'),ss,:],copy=False)
                elif map_group[sn].find("area_freq_") != -1:
                    counter = numpy.array(mean_cnts[map_group.index('area_'),ss,:],copy=False)
                elif map_group[sn].find("area_stormy_freq_") != -1:
                    counter = numpy.array(mean_cnts[map_group.index('stormy_area_'),ss,:],copy=False)
                summer = counter
            else:
                counter = numpy.array(mean_cnts[sn,ss,:],copy=False)
                summer = numpy.array(mean_sums[sn,ss,:],copy=False)

            #msg = "Name: %20s\tNumber: %4d\tMin Value  : %10g\tMax Value  : %10g\tNon-Missing Count  : %5d" 
            #print msg % (map_group[sn],sn,summer.min(),summer.max(),len(numpy.where(summer >= 0)[0]))
            #print msg % ("",sn,counter.min(),counter.max(),len(numpy.where(counter >= 0)[0]))

            meanval = NM(numpy.ones(maxid,dtype=numpy.float),-1.0) 
            for i in range(maxid):
                if counter[i] > 0:
                    pdb.set_trace()
                    meanval[i] = summer[i]/counter[i]
                    if map_group[sn].find("area") != -1:
                        # Make area a radius of an equivalent circle.
                        meanval[i] = math.sqrt(meanval[i]/math.pi) 
                    if normalization:
                        meanval[i] = counter[i] * normalization
#cut fix for earlier problem
#                    if map_group[sn] == 'track_length_':
#                         meanval[i] = float(meanval[i])/float(tstepsperday)    
                    #print i,counter[i],summer[i],meanval[i]
            
            #msg = "%26s\t%12s\tAve Min Val: %10g\tAve Max Val: %10g\tAve Non-Missing Cnt: %5d"
            #print msg % ("","",meanval.min(),meanval.max(),len(numpy.where(meanval >= 0)[0]))
            
            meanval.shape = (jm,im)

            # Make mean maps.
            fplot.create_fig()
            fplot.add_field(lons,lats,meanval,ptype=ptype)
            root = roots[map_group[sn]]
            title = "%s\n%s %s %s" % (root,model.upper(),seasons[ss].upper(),super_run)
            pname = "%sfigs/%smean_map_%s_%s%s" % (out_path,map_group[sn],seasons[ss],super_run,fig_format)
            if zoomed:
                pname = pname.replace(fig_format,"_zoom%s" % (fig_format))
            if map_group[sn] == "stormy_area_":
                pname = pname.replace("stormy_area_","area_stormy_")
            fplot.finish(pname,title=title)
            print "\tMade %s" % (pname)
            if store_netcdf:
                pname = pname.replace(fig_format,".nc")
                pname = pname.replace("/figs","/netcdfs")
                save_it = Save_NetCDF(meanval,lons,lats,pname)
                print "\tSaved %s" % (pname)

            #import sys; sys.exit("Stop Here")
    # Done Plots
    return "Done"

#---Start of main code block.
if __name__=='__main__':

    import pickle,sys
    
    # Create a log file?
    log = 0

    # --------------------------------------------------------------------------
    # Select options for this run.
    # --------------------------------------------------------------------------
    picks = {0 : "NCEP/NCAR Reanalysis 1",
             1 : "NCEP-DOE Reanalysis 2",
             2 : "NASA GISS GCM ModelE",
             3 : "GFDL GCM",
             4 : "ERA-Interim Reanalysis",
             5 : "ERA-40 Reanalysis"}
    pick = 4
    if pick not in picks:
        sys.exit("ERROR: pick not listed in picks.")

    # This next set of lines should be copied from setup_vX.py
    # Short names by which pick will be labeled.
    models = ["nra","nra2","giss","gfdl","erai","era40"]
    try:
        model = models[pick]
    except:
        sys.exit("ERROR: pick not listed in models.")

    # Length of file ending to replace if using year_loop
    tails = ["_att.txt","_tracks.txt","_centers.txt","_dumped_centers.txt"]
    # JIMMY CHANGE TAIL HERE!
    tail = tails[0]
    tail = tails[1]
    cut_tail = len(tail)

    # Flags
    #  tracks: track info included in file
    #  atts: attribute info included in file
    #
    # Note tweaked self.just_center_table: in mcms_read for center/track pre-att read
    # also watch detail_tracks names in template
    tracks = ""
    atts = ""
    if tail.find("tracks") != -1:
        tracks = 1
    if tail.find("att") != -1:
        atts = 1
    # Note atts files can contain track info so if you want
    # track statistics for an att file manually set tracks
    # to 1 here.
    tracks = 1
    print "JIMMY TESTER"
    print atts
    print tracks

    # Halt program on error or just warn?
    exit_on_error = 0

    # Plot map on error (requires matplotlib, also doubles or more memory
    # footprint)
    plot_on_error = 0

    # Stop before making plots. (plots require matplotlib and 
    #   GMT (The Generic Mapping Tools) 
    no_plots = 0

    # What sort of figures
    fig_format = ".png"
    #fig_format = ".eps"
    #fig_format = ".pdf"

    # Store some maps and netcdf files for latter use
    store_netcdf = 1

    # Check for graphics programs
    psrose = check_program("psrose")
    if not psrose:
        print "\n\tWarning: GMT (The Generic Mapping Tools) not found. Some plots will not be made."
    try:
        import matplotlib
    except ImportError:
        print "\n\tWarning: matplotlib not available. Disabling plotting altogether."
        no_plots = 1

    # Skip to making plots (use pre-calculated data)
    if len(sys.argv) > 1:
        skip_to_plots = sys.argv[1]
    else:
        skip_to_plots = 0

    # Values only taken at center rather than over area (for mean maps)
    point_source = 0 
    if not atts:
        point_source = 1

    if no_plots and skip_to_plots:
        sys.exit("Stop: Can't have no_plots and skip_to_plots")

    # Skip high latitude for angle, separation, area
    # if non-zero the value is the absolute latitude
    # above which no values retained.
    skip_high_lat = 85

    # Filter to cycles with tracks lasting +- track_width timesteps
    # on either side of the tracks lowest SLP timestep.
    life_cycle_stuff = 0
    if life_cycle_stuff:
        sys.exit("Not added yet")

    # --------------------------------------------------------------------------
    # Define all modules to be imported.
    # --------------------------------------------------------------------------

    # Extract version number from this scripts name.
    tmp = sys.argv[0]
    file_len = len(tmp.split("_"))
    vnum = "_"+tmp.split("_")[file_len-1][:2]

    # Basic standard Python modules to import.
    imports = []
    system_imports = "import netcdftime,numpy,stats,math,pickle,sys,os,copy,string"
    imports.append(system_imports)
    imports.append("import netCDF4 as NetCDF")
    imports.append("from operator import add")
    if not no_plots or plot_on_error:
        imports.append("import matplotlib.pyplot as plt")
        imports.append("import matplotlib.mlab as mlab")
        imports.append("import matplotlib.dates as mdates")
        imports.append("import matplotlib.cm as cm")

    # My modules to import w/ version number appended.
    #JIMMY
    """if not no_plots or plot_on_error:
        my_base = ["create_template","read_mcms","pull_data","wavenumber",
                "plot_map","grid2ij","defs","rhumb_line_nav"]
    else:
        my_base = ["create_template","defs","read_mcms","pull_data",
                "rhumb_line_nav","wavenumber"]
    """
    if not no_plots or plot_on_error:
        my_base = ["create_template","read_mcms","pull_data",
                "plot_map","grid2ij","defs","rhumb_line_nav"]
    else:
        my_base = ["create_template","defs","read_mcms","pull_data",
                "rhumb_line_nav"]
    #JIMMY
    if store_netcdf:
        my_base.append("save_netcdf")
    for x in my_base:
        tmp = "import %s%s as %s" % (x,vnum,x)
        imports.append(tmp)
    tmp = "from %s%s import %s" % ("track_finder",vnum,"process_data")
    imports.append(tmp)
    tmp = "from %s%s import %s" % ("track_finder",vnum,"rose_plot")
    imports.append(tmp)

    # To save a double copy of the data being retained by pull_data it is
    # necessary to reimport and delete pull_data_vX.py inside each loop.
    import_read =  "import %s%s as %s" % ("pull_data",vnum,"pull_data")

    # --------------------------------------------------------------------------
    # Alter default behavior found in either defs_vX.py or setup_vX.py
    # --------------------------------------------------------------------------

    # The default behavior is to read SLP data from the
    # directory slp_path defined in setup_vX.py.
    # Here you can elect to override this behavior.
    over_write_slp_path = ""

    # The default behavior is to save results
    # in the directory out_path defined in
    # setup_vX.py. Here you can elect to override
    # this behavior.
    over_write_out_path = ""

    # This next set of lines should be copied from setup_vX.py
    # Full path to the root directory where pick specific output will be stored.
    # Note it's possible that all of these directories are identical.
    #result_directories = ["/Volumes/scratch/output/",] 
    # Uncomment to use same structure for all models
    #result_directories = ["/Volumes/scratch/output/" for x in range(len(picks))]
    result_directories = [" "," "," ", " ", "/mnt/drive1/jj/MCMS/out_multi/",] # JJ_CHECK
    
    # Uncomment to make current directory for all models
    #result_directories = [os.getcwd() for x in picks]
    try:
        result_directory = result_directories[pick]
        if not os.path.exists(result_directory):
            sys.exit("ERROR: result_directory not found.")
    except:
        sys.exit("ERROR: pick not listed in result_directories.")

    # Directory to be created for storing temporary pick specific files.
    shared_path = "%s%s_files/" % (result_directory,model)

    # The default behavior is to run over all the
    # years found by setup_vX.py. Here you can
    # elect to override this behavior.
    over_write_years = []
    #if pick == 5:
    #    over_write_years = [1961,1990]
    #over_write_years = [1979,2009]
    over_write_years = [1990,1990]

    msg = "\n\t====\tRunning Check\t===="
    print msg
    print "\tPick: %d" % (pick)
    if over_write_slp_path:
        print "\tUsing over_write_slp_path: %s" % (over_write_slp_path)
    else:
        print "\tUsing default slp_path"
    if over_write_out_path:
        print "\tUsing over_write_out_path: %s" % (over_write_out_path)
    else:
        print "\tUsing default out_path"
    if not os.path.exists(shared_path):
        sys.exit("\tCan't find shared_path!")
    else:
        print "\tUsing shared_path: %s" % (shared_path)
    if over_write_years:
        print "\tUsing over_write_years: %s" % (repr(over_write_years))
    else:
        print "\tUsing default years"

    # Get some definitions. Note must have run setup_vx.py already!
    sf_file = "%ss_dat.p" % (shared_path)
    try:
        fnc_out = pickle.load(open(sf_file, 'rb'))
        (im,jm,maxid,lats,lons,timestep,dx,dy,dlon,dlat,start_lat,start_lon,
                dlon_sq,dlat_sq,two_dlat,model_flag,eq_grid,tropical_n,tropical_s,
                bot,mid,top,row_start,row_end,tropical_n_alt,tropical_s_alt,
                bot_alt,top_alt,lon_shift,lat_flip,the_calendar,found_years,
                super_years,dim_lat,dim_lon,dim_time,var_lat,var_lon,var_time,
                var_slp,var_topo,var_land_sea_mask,file_seperator,no_topo,
                no_mask,slp_path,model,out_path,shared_path,lat_edges,lon_edges,
                land_gridids,troubled_centers,faux_grids) = fnc_out
        # Save memory
        del troubled_centers
        del lat_edges
        del lon_edges
        del fnc_out
    except:
        sys.exit("\n\tWARNING: Error reading or finding %s." % (sf_file))
    if over_write_years:
        super_years = over_write_years
    if over_write_out_path:
        out_path = over_write_out_path
    if over_write_slp_path:
        slp_path = over_write_slp_path

    header = "mcms_%s_%04d" % (model,int(super_years[0]))
    in_file = "%s%s%s" % (out_path,header,tail)

    if len(sys.argv) == 1:
        # Set definitions and instantiate read_mcms w/out a template
        what_do = {"model" : model,
                   "in_file" : in_file,
                   "out_file" : "",
                   # JIMMY
                   #                   "just_center_table" : False,
                   "just_center_table" : True,
                    "detail_tracks" : tracks,
                    "as_tracks" : "",
                    "start_time" : "YYYY MM DD HH SEASON",
                    "end_time" : "YYYY MM DD HH SEASON",
                    "places" : ["GLOBAL"],
                   # JIMMY
                   #                    "include_atts" : atts,
                   #                    "include_stormy" : atts,
                    "include_atts" : False,
                    "include_stormy" : False,
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
            # Provide values
            what_do["tropical_end"] = row_end[tropical_n_alt]
            what_do["tropical_start"] = row_start[tropical_s_alt]
            what_do["maxID"] = maxid
            what_do["land_gridids"] = land_gridids
    else:
        # Use provided template
        template = sys.argv[1]
        what_do = {"template":template}

    # Create out_path if it doesn't exist.
    stat_dir = out_path+'stats/tmp/'
    if not os.path.exists(stat_dir):
        dirs = os.makedirs(stat_dir)
        print "\tDirectory %s Created." % (stat_dir)

    defs_set = {}
    if pick <= 1:
        defs_set.update({"keep_log":log})
    elif pick == 2:
        defs_set.update({"keep_log":log,"read_scale":1.0})
    elif pick == 3:
        defs_set.update({"keep_log":log})
    elif pick == 4:
        defs_set.update({"keep_log":log})

    # Shortcut to keep parameter list shorter.
    specifics = {'super_years' : super_years,
                 'out_path' : out_path,
                 'shared_path' : shared_path,
                 'slp_path' : slp_path,
                 'cut_tail' : cut_tail,
                 'tracks' : tracks,
                 #JIMMY
                 #                 'atts' : atts,
                 'atts' : False,
                 'no_plots' : no_plots,
                 'skip_to_plots' : skip_to_plots,
                 'model' : model,
                 'skip_high_lat' : skip_high_lat,
                 'life_cycle_stuff' : life_cycle_stuff,
                 'exit_on_error' : exit_on_error,
                 'plot_on_error' : plot_on_error,
                 'psrose' : psrose,
                 'fig_format' : fig_format,
                 'point_source' : point_source,
                 'store_netcdf' : store_netcdf
                 }
    msg = main(imports,import_read,defs_set,what_do,**specifics)
    print msg
