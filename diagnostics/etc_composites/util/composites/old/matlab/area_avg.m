function [H_sum, H_cnt, X, Y] = equal_area_mapping(lat, lon, values, centerLat, centerLon, varargin)

  % check if edges have been given, if not default to -1500 to 1700 by 100km 
  if (nargin < 1)
    edges = -1500:100:1700; 
  else % else see if edges given is a single value or vector, if vector, assume it is the edges, if not it is the divsion per bin
    edges_div = varargin{1}; 
    if (length(edges_div) > 1)
      edges = edges_div; 
    else
      edges = -1500:edges_div:1500+edges_div; 
    end
  end

  % compute the haversine distance from the centerlat and centerlon, in both directions
  dist = haversine_distance(lat, lon, centerLat, centerLon); 
  dist_y = haversine_distance(lat, centerLon, centerLat, centerLon); 

  dist_x = sqrt(dist.^2 - dist_y.^2); 

  % this is needed to mark the +/- distance values, above gives the absolute value
  % here I set the distance w.r.t. the center of the cyclone
  lon_shift = lon; 
  lon_shift = lon_shift - 360;  %shifting everything to range -720 to -180

  % -50 is an arbitary value, i used boxlen + 5 degrees
  west_mask = ((lon - centerLon) < 0) | (((lon_shift - centerLon) < 0) & ((lon_shift - centerLon) >- 50)); 
  south_mask = ((lat - centerLat) < 0); 

  % make the west and south distance negative
  dist_x(west_mask) = dist_x(west_mask) .* -1; 
  dist_y(south_mask) = dist_y(south_mask) .* -1; 

  % compute the sum and cnt given the x and y distance
  [H_sum, H_cnt, X, Y] = custom_hist2d(dist_x(:), dist_y(:), values(:), edges); 
  
end
