clear; 
close all; 
clc; 

old = load('/mnt/drive1/jj/TRACKSMATLAB/TOJJ/out/erai/new_version/erai_MCMS_NH_special_slp_datacyc_2016_boxlen_degrees_45.mat'); 

old = old.datacyc_2016; 
old_data = old(1).data; 
old_lat = old(1).lat; 
old_lon = old(1).lon; 

old_temp = old(1).data; 
old_temp = squeeze(old_temp(5,:,:));

% new_file = sprintf('/mnt/drive1/jj/MCMS/v1/create_dict/out_nc/erai/slp/2000/track_erai_slp_2000_%d.nc', old(1).UIDsingle); 
new_file = '/mnt/drive1/jj/MCMS/v1/create_dict/out_nc/erai/slp/2016/track_erai_slp_NH_2016_20160101000090030080.nc'; 

new_data = ncread(new_file,'data'); 
new_lat = ncread(new_file, 'latgrid');
new_lon = ncread(new_file, 'longrid');

new_temp = ncread(new_file, 'data');
new_temp = squeeze(new_temp(:,:,5));

figure
subplot(1,2,1)
% pcolor(squeeze(new_data(:,:,1)))
pcolor(old_temp)
shading flat
colorbar
% caxis([9.8e4, 1.2e5])

subplot(1,2,2)
% pcolor(squeeze(old_data(1,:,:)))
pcolor(new_temp)
shading flat
colorbar
% caxis([9.8e4, 1.2e5])
