import os, sys
import numpy
import matplotlib.pyplot as plt
import stats

Summerize = stats.ldescribe
Median = stats.lmedian
Mode = stats.lmode
Nsum = numpy.sum


# For model grid defs and such
mcms_model = "nra2"
mcms_model = "giss"
get_var = 'slp'

# Years to check
years = range(1948,2009)
years = range(2007,2008)

#years = range(1948,1969)

# Define some paths and files
out_path = "/Volumes/scratch/output/test/"
out_path = "/Volumes/scratch/output/giss_redo/"
header = "mcms_%s_%04d_" % (mcms_model,int(years[0]-1))

pname_base = "%sfigs/pdfs/%s" % (out_path,header)
pname_base = "%sfigs/pdfs/mcms_%s_%04d-%04d_" % (out_path,mcms_model,years[0],years[-1]-1)

lap_file = "%s%slaplacian.txt" % (out_path,header)

laps = []
for loop_year in years:
    print "\n=============%d=============" % (loop_year)

    # Read file
    lap_file = lap_file.replace(str(loop_year-1),str(loop_year))
    xdat = open(lap_file,"r").readlines()
    xdat = [float(x) for x in xdat[0][:-1].split(" ")]

#     # Trim non-positives
#     xdat = [x for x in xdat if x > 0.0]

    laps.extend(xdat)

###########

# make a cumlative histogram (no_plot) to see what percentage of total
# passes threshold
threshold = 0.15
threshold = 0.05
bins_width = 0.05
bins_left_edge = numpy.arange(-5.0,5.0+bins_width,bins_width)
bins_centers = bins_left_edge + 0.5*bins_width
bins_right_edge = bins_left_edge + bins_width

n, bins, patches = plt.hist(laps,bins=bins_left_edge,range=None,normed=1,cumulative=1,bottom=None,histtype='bar',
                            align='mid',orientation='vertical', rwidth=None, log=False,facecolor='grey', alpha=0.75)
plt.close('all')

fmt = "Bin % 4d: % 7.2f <= % 7.2f < % 7.2f  | Cumlative Percentage %f"
fmt_hit = "Bin % 4d: % 7.2f <= % 7.2f < % 7.2f  | Cumlative Percentage %f *****"
for bin in range(len(bins_left_edge)-1):
    if bins_left_edge[bin] <= threshold < bins_right_edge[bin]:
        print fmt_hit % (bin,bins_left_edge[bin],bins_centers[bin],
                     bins_right_edge[bin],n[bin])
    else:
        print fmt % (bin,bins_left_edge[bin],bins_centers[bin],
                     bins_right_edge[bin],n[bin])

pname =  pname_base+"laplacian_pdf.pdf"

fig = plt.figure()
ax = fig.add_subplot(111)
# the histogram of the data (not cumulative)
bin_width = 0.1
bins_left_edge = numpy.arange(-5.0,5.0,bin_width)
n, bins, patches = ax.hist(laps,bins=bins_left_edge,range=None,normed=1,cumulative=0,bottom=None,histtype='bar',
                           align='mid',orientation='vertical', rwidth=None, log=False,facecolor='grey', alpha=0.75)

# Add Labels and such
ax.set_xlabel(r"9-pnt Laplacian ($hPa\,^{\circ}lat^2$)")
ax.set_ylabel("Count")
# Add title
ax.set_title("9-pnt Laplacian")

# Note mode can take a very long time for very large arrays
fmter = "Count: %d\nMin/Max: %d/%d\nMean/Median: %.2f/%.2f\nSTD: %.2f"
fnc_out = Summerize(laps)
stitle = fmter % (fnc_out[0],fnc_out[1][0],fnc_out[1][1],fnc_out[2],Median(laps),fnc_out[3])
plt.suptitle(stitle, fontsize=4,x=0.8,y=0.95,horizontalalignment='left')
ax.grid(True)
# Save to File
fig.savefig(pname,dpi=144)
plt.close('all')


# Note that 5% have Laplacians of <= 0 which cant be centers and are spurious errors due to SLP reduction
# os 0.4 removes about 20% of centers with a positive laplacian (0.3 would remove about 15%, 0.2 would remove about 8%)
