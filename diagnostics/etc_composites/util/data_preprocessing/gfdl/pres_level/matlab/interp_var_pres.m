%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   interp_var_pres - function that interpolates a vertical profile of 
%                     data to a specific pressure level using a log 
%                     P profile
%
%   vint = interp_var(varin, pres, level)
%
%    varin - field to interpolate
%     pres - pressure levels of input field
%    level - desired pressure level to interpolate to
%     vint - interpolated field
%
%     created Sept. 2003 Ryan Torn, U. Washington
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function vint = interp_var(varin, pres, level)

[iz iy ix] = size(varin);

% loop over all grid points in horizontal
for ii = 1:ix; for jj = 1:iy

  if ((pres(1,jj,ii) > level) && (pres(iz,jj,ii) < level))

    % look for grid points bounding pressure level
    for kk = 1:iz
      if pres(kk,jj,ii) < level
        klev = kk-1;
        break;
      end;
    end;

    % linearly linterpolate in log p to pressure level
    m = (varin(klev+1,jj,ii) - varin(klev,jj,ii)) ./ ...
        (log(pres(klev+1,jj,ii)) - log(pres(klev,jj,ii))); 
    vint(jj,ii) = m .* (log(level) - log(pres(klev,jj,ii))) + ...
                           varin(klev,jj,ii);

  else % set to not a number if level below ground

    vint(jj,ii) = NaN;

  end;

end; end;
