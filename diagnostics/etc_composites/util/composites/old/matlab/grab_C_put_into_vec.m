  [C ] = ...
      textscan(fid, ...
               ['%f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %*[^\' ...
                'n]']);
  fclose(fid);
  %  yr/mo/day/hr/Jul/latSPECIAL\lon\
  %                      /grID/SLP1/SLP2/gridLAPLacian/flags/Intensity/Dissim
  % #15 = UCI  (unique center identifier)
  % #16 = USI (unique storm identifier)
  %
  %
  full_yr_ho = [full_yr_ho; C{1}(:)];
  full_mon_ho =[full_mon_ho; C{2}(:)];
  full_day_ho =[full_day_ho; C{3}(:)];
  full_hr_ho = [full_hr_ho ;C{4}(:)];

  full_lat_ho =[full_lat_ho; C{6}(:)];
  full_lon_ho =[full_lon_ho; C{7}(:)];
  full_slp_ho = [full_slp_ho; C{9}(:)];

  full_flags_ho =[full_flags_ho; C{12}(:)];
  full_all_csi = [full_all_csi; C{15}(:)];
  full_all_usi = [full_all_usi; C{16}(:)];

  disp('Done Grabing Data into vectors from text file.'); 
