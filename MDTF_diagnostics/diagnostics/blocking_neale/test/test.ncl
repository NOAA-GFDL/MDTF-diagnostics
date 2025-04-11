load "blocking_funcs.ncl"

; For any one of these test cases, set True and run as main
; SETTINGS (for running as main:  ncl func_blocking.ncl )
test_get_all_cases         = False
test_ensemble_find         = False
test_file_read             = False
test_string_to_logical     = False
test_ones_1d_int           = False
test_get_possible_attr     = False
test_get_legend            = False
test_get_light_color       = False
test_get_settings          = False
test_get_plot_settings_all = True

cheyenne = False  ;to set paths, doesn't use envvars yet

if ( test_ones_1d_int ) then
  len = 10
  print("================ test_ones_1d_int ")
  print("The following should be ones of length "+len)
  print(ones_1d_int(len))
end if

if ( test_string_to_logical ) then
  print("string to logical for true   "+string_to_logical("true"))
  print("string to logical for false  "+string_to_logical("false"))
  print("string to logical for string "+string_to_logical("string"))
  print("string to logical for 0      "+string_to_logical("0"))
  print("string to logical for 1      "+string_to_logical("1"))
end if

function set_file_opts_for_test_file_read(myfile,myvar)
begin

   file_opts = True
   file_opts@file_name = myfile
   file_opts@var_name = myvar
   file_opts@year0 = 1979
   file_opts@year1 = 1981
   file_opts@period_name = "ANN"
   file_opts@latn_in = 85.
   file_opts@lats_in = 20.
   file_opts@lone_in = 360.
   file_opts@lonw_in = 0.

   return file_opts
end
; ---

if (test_file_read) then
  if ( cheyenne ) then
    mydir = "/glade/work/rneale/data/"
  else
    mydir = "/project/amp/bundy/mdtf/inputdata/obs_data/blocking"
  end if

  myvar = "z500"
  myfile = mydir + "/ERAI/"+myvar+".day.mean.nc"
  file_opts = set_file_opts_for_test_file_read(myfile,myvar)
  
  print("calling blocking_readfile for: "+myfile)
  mytest = blocking_readfile(file_opts)

  myfile = "/project/amp/bundy/mdtf/inputdata/model/blocking_cam4/f40.1979_amip.track1.1deg.003_dmeans_ts_Z500.nc"
  myvar = "Z500"
  delete(file_opts)
  delete(mytest)
  file_opts = set_file_opts_for_test_file_read(myfile,myvar)

   print("calling blocking_readfile for: "+myfile)
   mytest = blocking_readfile(file_opts)

end if; (test_file_read) then

if ( test_get_all_cases.or.test_ensemble_find.or.test_get_legend.or.test_get_possible_attr.or.test_get_plot_settings_all ) then
  print("================ test_get_all_cases: ")

  all_cases = blocking_get_all_case_info(False)
  print(all_cases)
end if


if ( test_get_settings.or.test_get_plot_settings_all ) then
  print("================ test_get_settings:")
  settings = get_blocking_settings()
end if

if ( test_get_possible_attr ) then
  print("================")
  print("test_get_possible_attr: should return missing: "+get_possible_attr(False,"trash"))

  opts = True
  opts@hello = "hello"
  print("test_get_possible_attr: should return "+opts@hello+"  "+get_possible_attr(opts,"hello"))
 
  opts@array = (/1,2,3,4/)
  print("test_get_possible_attr: should return "+opts@array+"  "+get_possible_attr(opts,"array"))

  print("test_get_possible_attr: should return obs_names ")
  print(get_possible_attr(all_cases,"obs_names"))
end if 


if ( test_ensemble_find.or.test_get_legend.or.test_get_plot_settings_all ) then
  print("================ test_ensemble_find: ")
  ensemble_names = get_ensemble_names(all_cases@case_names) ; Number of ensemble sets
  nens = dimsizes(ensemble_names)
  ne_size = get_ensemble_sizes(ensemble_names,all_cases@case_names)

  ; save info as attribute so don't have to get it again
; save info as attribute so don't have to get it again in plotting funcs
  all_cases@ensemble_names = ensemble_names
  all_cases@ne_size = ne_size  ; need this?


 do iens=0,nens-1
    ;drbdbg change to fileind, and uses as fileind@it0 etc to save lines
    ens_file_inds = get_file_indices_from_ensemble_name(ensemble_names(iens),all_cases@case_names)
    print("Ensemble "+iens+" "+ensemble_names(iens)+": ")
    print("    case "+ens_file_inds+" "+all_cases@file_names(ens_file_inds))
    delete(ens_file_inds) 
  end do

  test = all_cases@case_names
  obs_inds = get_obs_inds(all_cases@case_names)
  if (.not.any(ismissing(obs_inds))) then
    print("Obs "+obs_inds+" "+all_cases@case_names(obs_inds)+" "+all_cases@file_names(obs_inds))
    obs_names = get_obs_names()
    all_cases@obs_names = obs_names
  else
    print("No OBS cases found; if wanted, use MDTF_BLOCKING_OBS = True in $POD_HOME/settings.jsonc")
  end if
end if

if ( test_get_legend.or.test_get_plot_settings_all ) then
  print("================ test_get_legend:")
  
  plot = set_plotting_info(all_cases,settings)
  print(plot)

  figure_name = "test_get_legend"
  figure_type = "ps"
  print("Plotting to "+figure_name+"."+figure_type)
  wks = gsn_open_wks(figure_type, figure_name)
  gsn_define_colormap(wks,"rainbow")
  legend1 = get_legend(wks,all_cases)

  ;nobs & nlines set in get_legend
  nobs = all_cases@nobs
  nlines = all_cases@nlines
  fcolors = get_light_colors_array(all_cases@line_colors(nobs:nlines-1))

  all_cases@line_colors_light = fcolors

  do i = 0,nlines-1
    if (i.lt.nobs ) then
      print("Legend: "+all_cases@legend_names(i)+" "+all_cases@line_colors(i)+" (line type "+all_cases@line_types(i) +")" )
   else
      print("Legend: "+all_cases@legend_names(i)+"  "+all_cases@line_colors(i)+\
                     " (line type "+all_cases@line_types(i) +")"+\ 
                     " shading "+all_cases@line_colors_light(i-nobs))
   end if
  end do
end if

if ( test_get_light_color ) then
  print("================ test_get_light_color: ")
  color = "blue"
  print("get_light_color("+color+") returns light"+color+"? "+get_light_color(color))

  color = "trash"
  print("get_light_color("+color+") returns LightGray? "+get_light_color(color))

  color_array_in = (/"purple","orange","magenta","cyan","trash"/)
  print(color_array_in+" "+get_light_colors_array(color_array_in))

end if

if ( test_get_plot_settings_all ) then
  print("================ test_get_plot_settings_all: ")

  set_plotting_info(all_cases,settings)
  wks = gsn_open_wks("ps", "test_meanlon")
  res = get_plot_settings_meanlon(wks,all_cases) 
  print(res)

  wks_t = gsn_open_wks("ps", "test_ann_cycle")
  gsn_define_colormap(wks_t,"gsdtol")      ; choose
  res_t = get_plot_settings_ann_cycle(wks_t,all_cases)  
  print(res_t)

  res_m = get_plot_settings_panel(res,all_cases)
  print(res_m)

end if
