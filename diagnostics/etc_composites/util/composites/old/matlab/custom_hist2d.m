function [H_sum, H_cnt, x_vals, y_vals] = custom_hist2d(X, Y, values, edges)

  % initialize the outputs 
  H_sum = zeros(length(edges)-1, length(edges)-1); 
  H_cnt = zeros(length(edges)-1, length(edges)-1); 
  x_div = edges(2) - edges(1); 
  x_vals = edges(1:end-1) + x_div/2;
  y_vals = x_vals; 

  % loop throught the output 2d hist, 
  % find values that fall into each bin, 
  % get the sum and cnt of the values
  for row = 1:size(H_sum, 1)-1
    for col = 1:size(H_sum, 2)-1
      ind = (Y >= edges(row)) & (Y <= edges(row+1)) & (X >= edges(col)) & (X <= edges(col+1)); 
      H_sum(row, col) = H_sum(row, col) + nansum(values(ind)); 
      H_cnt(row, col) = H_cnt(row, col) + sum(~isnan(values(ind))); 
    end
  end

end
