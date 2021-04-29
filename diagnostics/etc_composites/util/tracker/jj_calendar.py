import datetime as dt
from dateutil.relativedelta import relativedelta


def get_time_info(the_time_units, times, calendar='standard'):
  '''
  Function to convert times to date_stamps, datetimes, adates needed by the main parts of the code
  Input:  the_time_units - the netcdf time variable units, e.g. hours since 2001-01-01 00:00:00
          times - the timesteps as extracted from the netcdf file
          calendar - ('standard' = 'proleptic_greogrian' = 'julian') or '365_day'
  Note: Had to change the adates print out in hours instead of days.
  If I use days, the adates increment by 25 for every 6hrs, which is fine
  But for 1hrly data, it increments by 4.1666666, this causes error, as we are rounding out adates
  So we have to convert adates to hours, which means adates now will increment by 6 for 6 hrly data. 
  So I have to get the datetime, get the days. Then do days*24 + dt
  '''

  if (calendar == 'proleptic_gregorian') | (calendar == 'julian'):
    calendar = 'standard'

  # getting the number of timesteps
  tsteps = len(times)
  
  # getting the range of the times variable
  the_time_range = [times[0],times[tsteps-1]]

  # getting the start date in datetime format
  # first get the date in a string format from netcdf time units
  # then convert it to an acutal datetime
  start, delta_type = get_start_date(the_time_units)
  start_date = dt.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')

  # here I check what is the unit of my timesteps
  # example 'hours since' 
  # hours since = tmp[0],tmp[1]
  # the if condition can be removed, if needed
  if (delta_type == 'hours'):
    dtimes = [start_date + relativedelta(hours=float(i_time)) for i_time in times]
  else:
    raise Exception('jj_calendar.py: Unknown time units in netcdf input files.')
  

  # if the calendar is 365_day we have to adjust the datetimes by 1
  if (calendar == '365_day'):
    dtimes = adjust_dtimes(dtimes, calendar)

  # note: we have to create adates and date_stamps
  # AFTER we adjust the dtimes depending on the calendar (i.e. '365_day' calendar)

  # Get the time stamps
  date_stamps = get_datestamps(dtimes, calendar)
  
  # adates have to be unique, when u run for multiple years
  # adates = ['%09d'%(x) for x in range(tsteps)]
  adates = [get_adate(x, calendar) for x in dtimes]

  # import pdb; pdb.set_trace()
  # print('Jeyavinoth: Start and End adate for Year: ', adates[0], adates[-1])

  return dtimes, date_stamps, adates

def get_adate(dtime, calendar='standard'):

  if (calendar == 'standard'):
    # I choose a manual start date of 1900
    # Make sure I account for this when I revert back the adates
    # have to add one day worth of seconds
    adate_num = (dtime - dt.datetime(1900, 1, 1))

    # here I have to divide by 3600*24 to get the timestamp in days
    # because the code runs it in days
    # adate_num = float(adate_num.days) + float(adate_num.seconds)/3600./24.
    # adate = int(100*adate_num)
    # Jeyavinoth: converting above line: convert from days to hours
    # also I don't need to multiply 100 anymore, because we get nice rounded out numbers when we calculate using hours
    adate_num = float(adate_num.days)*24 + float(adate_num.seconds)/3600.
    adate = int(adate_num)
    adate = '%09d'%(adate)
  elif (calendar == '365_day'):

    # if the calendar is julian, then I need to add 365 from day the year 1900 till the current date year
    # then add the number of days to this 
    year = dtime.year  

    # get the start of the year in datetime
    # then get the number of days from dtime to start of year
    start_yr = dt.datetime(dtime.year, 1, 1)
    delta_yr = (dtime - start_yr)
   
    # we get the number of years to add to 1/1/1900
    num_year = (year - 1900)

    # create adate_num for all the years since 1/1/1900
    # adate_num = float(num_year * 365)
    # Jeyavinoth: converting above line: convert from days to hours
    adate_num = float(num_year * 365)*24.
    if (check_leap(dtime)):
      # if it is a leap year & dtime >= feb 29th, then we have to reduce 1 day from the total count
      # note that normal calculation has to include a +1, which we dont do here
      if (dtime >= dt.datetime(dtime.year, 2, 29)):
        # adate_num += delta_yr.total_seconds()/(3600*24)
        # Jeyavinoth: converting above line: convert from days to hours
        adate_num += delta_yr.total_seconds()/(3600)
      else:
        # if it is before feb 29th, then we do the normal calculation
        # adate_num += delta_yr.total_seconds()/(3600*24) + 1
        # Jeyavinoth: converting above line: convert from days to hours
        adate_num += delta_yr.total_seconds()/(3600) + 24
    else:
      # adate_num += delta_yr.total_seconds()/(3600*24) + 1
      # Jeyavinoth: converting above line: convert from days to hours
      adate_num += delta_yr.total_seconds()/(3600) + 24

    # convert adate to a string
    # adate = '%09d'%(adate_num*100)
    # Jeyavinoth: converting above line: convert from days to hours
    adate = '%09d'%(adate_num)
  return adate

def check_leap(dtime):
  '''
  Check if the datetime is part of a leap year
  '''
  num_days = (dt.datetime(dtime.year, 12, 31) - dt.datetime(dtime.year, 1, 1)).days + 1
  if (num_days == 366):
    return True
  else:
    return False

def get_datestamps(dtimes, calendar):
  date_stamps = ["%4d %02d %02d %02d" % (d.year,d.month,d.day,d.hour) for d in dtimes]
  return date_stamps


def get_start_date(the_time_units):
  ''' 
  Function to get start date string from units of time in netcdf
  e.g: from 'hours since 2001-1-1 00:00:00' to '2001-01-01', 
  so that I can use this to create my datetimes
  '''

  # getting start date from the units of time variable in netcdf
  start = "%s" % (the_time_units)

  # splitting up the start date by spaces
  tmp = start.split()

  # stripping the start variable to create get the year, month, day and time
  tmp1 = tmp[2].split("-")
  tmp2 = tmp[3].split(":")
  tmp3 = 0

  # String that specifies the start date
  # will be used in the datetime function to get the start datetime variable
  start = "%04d-%02d-%02d %02d:%02d:%02d" % \
          (int(tmp1[0]),int(tmp1[1]),\
           int(tmp1[2]),int(tmp2[0]),int(tmp2[1]),\
           int(tmp3))

  return start, tmp[0]


# Jeyavinoth: 
# Functions below this are for debugging purposes, can be removed in final version
def compare_lists(li1, li2): 
  ''' 
  Debug: Function to compare two lists 
  Note: just makes sure both lists have the same variables in each, 
  doesnt care of the length
  '''
  li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
  return li_dif 
          
# def revert_adate(adate):
#   ''' 
#   Function converts a sinlge adate to datetime 
#   '''
#
#   ordinal = np.int(adate/100.)
#   hours = (adate/100. - ordinal)*24
#   dtime = dt.datetime.fromordinal(np.int(adate/100.)) + relativedelta(hours=hours)
#   return dtime

def adjust_dtimes(dtimes, calendar='365_day'):
  '''
  Adjusts the date time for a julian calendar, 
  what if the list is not sorted? 
  Do I force a sort, can i sort a datetime list? 
  check this!
  '''
  # have to write this code
  if (calendar=='365_day'): 

    # get the start_date, from the list
    start_date = dtimes[0]

    # we set a flag to adjust all the values in dtimes list
    adjust_flag = True

    # if there are multiple years in a file, then we have to account for this 
    # initially we dont have to adjust until we face a leap year and go past feb 29
    # then we have to increment this value, and add this number of days to datetime 
    adjust_days = 0

    # check if the start date is already past february 29th for a leap year
    # if so we don't have to adjust the values for the first year
    # our datetimes will be fine, because we started on an off date
    # we also don't adjust the dates in the current year if it starts on non leap year
    if (check_leap(start_date)):
      if (start_date > dt.datetime(start_date.year, 2, 29)):
        adjust_flag = False
    else: 
      adjust_flag = False
  

    # new dtimes list set to empty
    new_dtimes = []

    # setting the previous year to start_date, because we already did the necessary checks and flags set accordingly
    prev_year = start_date.year 
    for dtime in dtimes:  
      # check if we changed years
      # if so now we have do the check for a leap or not and set the flag appropriately
      if (prev_year != dtime.year):
        # HA! now we are in a new year
        # if we come across a leap year, we now have to start adjusting values
        # if the current year is leap, then we set this flag to true
        # this will be set to false, when we pass feb 28, because at that point we will increment adjust_days
        # there will be no need to adjust_day anymore, till the next leap year
        if (check_leap(dtime)):
          adjust_flag = True

        # set the prev_year to be current year
        # so we enter this if condition, when we face a new year
        prev_year = start_date.year

      # if we have to adjust (only set to true if it is a leap year), 
      # then we go and check if the current dtime is greater than feb 29
      if (adjust_flag):
        if (dtime >= dt.datetime(dtime.year, 2, 29)):
          # now we have met the criteria,
          # we are on feb 29, 0 hrs
          # this dtime has to be incremented by a day, to make it march 1st
          adjust_days += 1
          adjust_flag = False

      # Each time in the loop, we increment the dtime by the number of adjust_days
      new_dtimes.append(dtime + relativedelta(days=adjust_days))

    return new_dtimes
    raise Exception('jj_calendar.py: have to write this code')
  else:
    raise Exception('jj_calendar.py: Unknown Calendar')

