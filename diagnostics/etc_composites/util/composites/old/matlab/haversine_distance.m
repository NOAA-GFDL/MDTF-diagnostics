function dist = haversine_distance(lat, lon, centerLat, centerLon)
  
  mean_radius_earth = 6371; 
  
  lat1 = lat .* pi/180; 
  lat2 = centerLat .* pi/180;

  lon1 = lon .* pi/180; 
  lon2 = centerLon .* pi/180;

  dLat = lat1 - lat2; 
  dLon = lon1 - lon2; 

  R = mean_radius_earth; 

  a = sin(dLat/2).^2 + cos(lat1) .* cos(lat2) .* sin(dLon/2).^2; 
  c = atan2(sqrt(a), sqrt(1-a)); 
  dist = 2.*R.*c; 
end
