import defines
import sys

# snyear = '%d_%d'%(defines.over_write_years[0], defines.over_write_years[1])
# snyear = sys.argv[1]
# snyear = '2000_2029'
# model = 'temp'
# rundir = 'out_temp'

if (defines.over_write_years[0] == defines.over_write_years[1]):
  snyear = '%04d'%(defines.over_write_years[0])
else:
  snyear = '%04d_%04d'%(defines.over_write_years[0], defines.over_write_years[1])

model = defines.model
rundir = 'out_%s'%(defines.model)
startdir = defines.main_folder

in_file = startdir+rundir+'/'+model+'/mcms_'+model+'_'+snyear+'_tracks.txt'
out_file = startdir+'read_%s/'%(defines.model)+rundir+'_output_'+snyear+'.txt'
save_output = True
overwrite = False

just_centers = False
just_center_table = True

start_time = 'YYYY MM DD HH SEASON'
end_time = 'YYYY MM DD HH SEASON'

places = ['GLOBAL']
include_atts = False
include_stormy = False

detail_tracks= startdir+'read_%s/'%(defines.model)+rundir+'_track_out_'+snyear+'.txt'
as_tracks = '' 
#detail_tracks = ''
#as_tracks = startdir+'READ_CAM6/'+rundir+'_track_out_'+snyear+'.txt'


# Name: in_file
# Description: Full path to the msmc data file you wish to read from.
# Default: ''
# Example: '/Volumes/scratch/in.txt'

# Name: out_file
# Description: Full path to the file you wish to save to. If left empty '' the
#              '.txt' in in_file will be replaced with with '_new.txt'.
# Default: ''
# Example: '/Volumes/scratch/in_new.txt'

# Name: save_output
# Description: Save results to out_file. If False/0 results saved in memeory for
#              further analysis such as graphics/plot creation.
# Default: True/1
# Example: True or 1

# Name: overwrite
# Description: Overwrites out_file if it exists.
# Default: False/0
# Example: False or 0

# Name: just_centers
# Description: Saves only basic center info (YYYY MM DD HH LAT LON).
#              YYYY MM DD HH - Date Time Group (hour GMT/Z).
#              LAT           - Latitude (degrees, [-90,90]).
#              LON           - Longitude (degrees, [0,360]).
# Default: False/0
# Example: False or 0

# Name: start_time
# Description: Limits the output date-times on and after start_time. By default
#              all dates-times are returned.
#
#              Flag   : Description
#              YYYY   : Include the year YYYY and all subsquent years until
#                       the end of the record is reached or the ending year.
#              MM     : Include all data from the month number MM and only data
#                       from that month MM. Can in limited with YYYY, DD or HH.
#              DD     : Include all data from the day DD and only data from the
#                       day DD. Can in limited with YYYY, MM or HH.
#              HH     : Include all data from the GMT hour HH and only data from
#                       the GMT hour HH. Can in limited with YYYY, MM or DD.
#              SEASON : Include only data from a list of predefined seasons:
#                       (DJF, MAM, JJA, SON, NDJFMA, MJJASO)
#
#              NOTE: SEASON can't be used concurrently with other time limits.
#                    If you want to do this run the filter more than once passing
#                    the out_file of one as the in_file to the other.
#
# Default: 'YYYY MM DD HH SEASON'
# Example: start_time = '2005 10 1 HH SEASON' -> start saving on Oct, 1st 2005
#          start_time = '2006 MM DD HH SEASON' -> start saving on and after 2005
#          start_time = 'YYYY MM DD 0 SEASON' -> save all 0Z data
#          start_time = 'YYYY MM DD HH DJF' -> save all DJF data.

# Name: end_time
# Description: Limits data extraction to a range when used with start_time. The
#              default sets the end as the final time record in the data set.
#
#              NOTE: SEASON has to match one in start_time!
#
# Default: 'YYYY MM DD HH SEASON'
# Example: end_time = '2006 5 13 HH SEASON' -> stop saving on May, 13th 2006
#          end_time = '2006 MM DD HH SEASON' -> stop saving at the end of 2005

# Name: places
# Description: Limits the output to specific locals. By default all data are
#              returned.
#
#      Flag : Description
#        GLOBAL : Includ centers from everywhere
#        NH     : Include only centers from the Northern Hemisphere.
#        SH     : Include only centers from the Southern Hemisphere.
#        LAND   : Include only centers from over the land as defined by the
#                 land/sea mask provided by the NCEP Reanalysis.
#        SEA    : Include only centers from over the sea as defined by the
#                 land/sea mask provided by the NCEP Reanalysis.
#        GridID : Includ only centers that occupy this list of gridIDs
#                 (can be only one, space seperated, one line). A simple
#                 script (l2g.py will convert a list of lon, lat pairs
#                 into a list of gridIDs).x
#
#      Note: The ability to have multiple places (e.g. ['LAND','NH']) is
#            not yet available. The work around is to run ['LAND'] and
#            use the out_file of that as input and rerun with ['NH'].
#
# Default: ['GLOBAL']
# Example:
#          places = [5503, 3303, 2203] # limited to 3 gridids
#          places = ['NH'] # limited to the Northern Hemisphere
#          places = [7602]

# Name: include_atts
# Description: Include atttritubted grids in the places screen. That is, the
#              default behavior only uses the center gridID's to filter by place.
#              By uncommenting'include_att' attributed grids are also used to
#              filter by place. The differencs is the default treats cyclones as
#              point objects and only gives the cyclones whose centers passed
#              directly over the grid containing say New York City. This option
#              treats cyclones are non-point objects and returns all cyclones for
#              which any of its attributed grids pass overed the grid containing
#              New York City.
# Default: False/0
# Example: False or 0

# Name: include_stormy
# Description: Simular to include_atts but allows for stormy grids to be added
#              as well. In this case the stormy grids are asigned to the closest
#              of the n-centers that they are associated with on a grid by grid
#              basis.
# Default: False/0
# Example: False or 0

# Name: detail_tracks
# Description: A special case where we want to treat centers as tracks. To do
#              this we must first create detail_tracks which is a file storing
#              a list of each track and all of its centers. If left empty ''
#              nothing is done in this reguard.
#
#              WARNING: in_file must contain tracked centers rather than just
#              centers else problems will occur.
# Default: ''
# Example: '/Volumes/scratch/sorted_by_track.txt'

# Name: as_tracks
# Description: Full path to the file created by 'detail_tracks'. The output is
#              sorted by track which means time specificity is lost (i.e., the
#              records are not by time by by track. As a result problematic,
#              stormy, and empty centers are not returned as of now, but filters
#              using include_stormy and include_atts are working. Also, note
#              that track records are separated by -444 and are not stored in
#              strictly chrological order.
#
#              NOTE: Results stored in out_file
# Default: ''
# Example: '/Volumes/scratch/sorted_by_track.txt'
