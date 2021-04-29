% CONVERT DATA TO PRESSURE LEVELS.
%instructions:
% INPUT:  
%    pres ::full pressure output from WRF
% 
% To obtain full pressure: read the perturbation pressure and 
% the baseline pressure
% in from WRF in the sigma coordinates and add them together
% and convert from Pa to  hPa.
%  pres = (pmatrix + pbmatrix)/ 100;
%
%   var_eta :: the variable to be converted to pressure coordinates.
%
% matrix lay-out: [time sigma-levels lat lon]
%%%%%     %%%%%     %%%%%     %%%%%     %%%%%     %%%%%     
function [var_pres pres_arr] = conv_to_plev(pres, var_eta,pres_arr)
  
% DEFINE A PRESSURE ARRAY TO INTERPOLATE TOWARDS.
%  p_top = 100;
%  pres_arr = 1000:-25:p_top;

  %   pres_arr = [850];
  Nz = length(pres_arr);  
  [nnn zzz yyy xxx] = size(var_eta);
  
  clear var_pres
  for nn=1:1:nnn
    if mod(nn,50)==0; display(nn); end
    for lev_ind=1:Nz
      
      presNOW = squeeze(pres(nn,:,:,:));
      varNOW = squeeze(var_eta(nn,:,:,:));
      cur_lev = pres_arr(lev_ind);
      var_pres(nn,lev_ind,:,:) = interp_var_pres(varNOW, presNOW, cur_lev);
      
    end
  end
  
