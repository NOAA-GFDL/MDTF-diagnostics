%
% after reading in MB .txt file for storms, put lat,lon 
% and time into a dictionary.
%
%
 
% added by jj to select only the year we need 
yr_ind = (full_yr_ho == nyear); 

% extracting the data from the list to variables used by Jimmy
all_csi = full_all_csi(yr_ind);
all_usi = full_all_usi(yr_ind);
lat_ho = full_lat_ho(yr_ind);
lon_ho = full_lon_ho(yr_ind);
yr_ho = full_yr_ho(yr_ind);
mon_ho = full_mon_ho(yr_ind);
day_ho = full_day_ho(yr_ind);
hr_ho = full_hr_ho (yr_ind);
slp_ho = full_slp_ho(yr_ind);
flags_ho = full_flags_ho(yr_ind);

% now we follow through jimmy's code

total_length = length(all_usi);
tracks_id = zeros(total_length,1);
usi_holder = all_usi(1);
track_counter = 1;
for nn = 1:total_length
  
  usi_now = all_usi(nn);
  if usi_now == usi_holder
    tracks_id(nn) = track_counter;
  else
    usi_holder = usi_now;
    track_counter = track_counter + 1;
    tracks_id(nn) = track_counter;    
  end
end

%  ASSIGN THE LARGE VECTORS WITH ALL OF THE DATA.
all_lats = 90 - lat_ho(:)/100;
all_lons = lon_ho(:)/100;

all_years = yr_ho(:);
all_mon = mon_ho(:);
all_day = day_ho(:);
all_hr = hr_ho(:);
all_slp = slp_ho(:);
all_flags = flags_ho(:);

% CREATE THE OBJECT OF STORMS
total_cyclones = tracks_id(end);
clear cyc

for tt = 1:total_cyclones
  if mod(tt,500) == 0
    display(tt)
  end
  usinow =all_usi(tracks_id==tt);
  cyc(tt).UID=usinow;
  cyc(tt).UIDsingle=usinow(1);
  cyc(tt).CID=all_csi(tracks_id==tt);
  cyc(tt).fulllon = all_lons(tracks_id==tt);
  cyc(tt).fulllat = all_lats(tracks_id==tt);
  cyc(tt).fullslp = all_slp(tracks_id==tt)*1e-3;
  cyc(tt).flag = all_flags(tracks_id==tt,1);
  tn_yr = all_years(tracks_id==tt);
  tn_mon = all_mon(tracks_id==tt);
  tn_day = all_day(tracks_id==tt);
  tn_hr = all_hr(tracks_id==tt);
  
  ddd = length(tn_yr);
  date_now = zeros(ddd,1);
  yr_now   = zeros(ddd,1);
  mon_now  = zeros(ddd,1);
  day_now  = zeros(ddd,1);

  for dd =1:ddd
    date_now(dd) = datenum([num2str(tn_mon(dd)),'_',...
                        num2str(tn_day(dd)),'_',...
                        num2str(tn_yr(dd))]);
    date_now(dd) = date_now(dd) + tn_hr(dd)/24;
    yr_now(dd)   = (tn_yr(dd));
    mon_now(dd)   =(tn_mon(dd));
    day_now(dd)   = (tn_day(dd));
  end
  
  cyc(tt).fulldate = date_now;
  cyc(tt).date1 = date_now(1);

  cyc(tt).fullyr   = yr_now;
  cyc(tt).fullmon  = mon_now;
  cyc(tt).fullday  = day_now;
  
  cyc(tt).mon_mode   = mode(mon_now);
  cyc(tt).yr_mode   = mode(yr_now);
end
