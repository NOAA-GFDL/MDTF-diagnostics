% main code to reproject the data
load('temp.mat'); 

% creating an area average grid
% given in lat, lon, data, centerlat, centerlon, and edges as 100km bins or the actual edges of the bins 
% [H_sum, H_cnt, X, Y] = area_avg(lat, lon, data, centerLat, centerLon, 100); 
[H_sum, H_cnt, X, Y] = area_avg(lat, lon, data, centerLat, centerLon, -3000:100:3000); 

% plotting the figures
figure()
subplot(1,2,1)
pcolor(lon, lat, data);
shading flat; 
hold on; 
plot(centerLon, centerLat, 'k*'); 
xlabel('Longitude')
ylabel('Latitude')
title('Original')

subplot(1,2,2)
pcolor(X, Y, H_sum./H_cnt); 
shading flat;
xlabel('Distance from center')
ylabel('Distance from center')
title('Reprojected')

