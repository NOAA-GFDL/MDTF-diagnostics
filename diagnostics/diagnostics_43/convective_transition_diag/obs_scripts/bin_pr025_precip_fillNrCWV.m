%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% bin_rss.m                                                %
% Binning:                                                 % 
% Use TMIv7r1 data from Remote Sensing System (RSS)        %
%   and temperature from Reanlysis-2 (R2)                  %
%	TMI can be replaced by SSM/I easily by replacing         %
%   read_tmi_day_v7.m (search "read_tmi_day_v7")           %
%   and using the SSM/I data                               %
% Required data:                                           %
%   (1) TMIv7r1 data (twice daily) & read_tmi_day_v7.m     %
%   (2) R2 1000-200mb mass-averaged temperature (6-hourly) %
%   (3) R2 1000-200mb column-integrated saturation         %
%         specific humidity (6-hourly)                     %
%   (4) Mask for specifying regions with  specific         %
%         resolutions                                      %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
% % Uncomment & Edit this section for excuting this script directly
startDate=datenum(2002,06,01);
endDate=datenum(2014,06,01)-1;
% Spatial resolution (degree) for binning, TMI default=0.25
resolution=0.25*2; % 0.25, 0.50, 1.00, 1.50, etc
% Use 1<=reg<=number_of_regions for reg in the mask
number_of_regions=4;
% Column Water Vapor (CWV,mm), TMI default=0.3
% The bin centers are integral multiples of cwv_bin_width
cwv_bin_width=0.3; % integral multiple of 0.3
cwv_range_max=75; % default=90
% Range of column average temperature (K)
%		With 1K increment and integral bin centers
T_range_min=260;
T_range_max=280;
%	Threshold values defining precipitating events (0.1mm/hr)
dp=1; % dp should be an integer (unit:0.1mm/hr)
precip_threshold=[0:(0.1*dp):50]'; %(mm/hr)
%	Directories for input data for bin_rss.m 
region_mask_dir='/media/yhkuo/rei/REGION_MASK/';
reanalysis_dir='/media/yhkuo/rei/Reanalysis-2/TAVE_QSAT_PROCESSED/';
tmi_dir='/media/yhkuo/MISATO/TMI_v7r1/';
trmmpr_dir='/media/yhkuo/MISATO/2A25/rssGridded/';
%	Directory/filename for output data for bin_rss.m
bin_output_dir='/home/yhkuo/Dropbox/precipPDF/BINNED/';
bin_output_filename_prefix='BINNED_PR_TMIv7r1';
bin_output_filename_suffix='_fillNrCWV';
bin_output_filename=[bin_output_filename_prefix '_'...
										datestr(startDate,'yyyy') datestr(startDate,'mm') '_' ...
										datestr(endDate,'yyyy') datestr(endDate,'mm') '_res=' ...
										sprintf('%.2f',resolution) bin_output_filename_suffix '.mat'];
count_pr_th=27;
%%
coarsen=resolution/0.25-1; % resolution=(coarsen+1)*0.25;
res=num2str(sprintf('%.2f',resolution));

number_cwv_bins=cwv_range_max/cwv_bin_width;
cwv=[1:number_cwv_bins]'*cwv_bin_width;

T_offset=T_range_min-1;
number_T_bins=T_range_max-T_range_min+1;

precip_bdy=[0;precip_threshold+0.05/(coarsen+1)^2];
precip_binCenter=[0;( precip_bdy(2:end-1)+precip_bdy(3:end) )/2];
% Preallocate storage for the binned precip and saturation
PrecMoments=length(precip_threshold);
BIN=zeros(number_of_regions,number_cwv_bins,number_T_bins,PrecMoments);
PMT=zeros(number_of_regions,number_cwv_bins,number_T_bins,3); % precip moments
QSH=zeros(number_of_regions,number_T_bins,PrecMoments,2);
%%
% Load region mask for RSS data (lon, lat, region)
load([region_mask_dir 'region_errTempCorrect_' res 'x' res '.mat']);
lon_rss=lon;
lat_rss=lat;
region_rss=region;
[LAT,LON]=meshgrid(lat_rss,lon_rss);
LAT=repmat(LAT,[1,1,2]);
LON=repmat(LON,[1,1,2]);
%%
% % The original TMI resolution is 0.25 degree.
% % This commented section shows how the lat/lon and region maskloaded in 
% %   the last section were calculated
% lon=[0.125:0.25:(360-0.125)]'; 
% lat=[-89.875:0.25:89.875]';	% lat(281)=-19.875, lat(440)=19.875
% lat=lat(281-ceil(coarsen/2):440+ceil(coarsen/2));
% if (coarsen~=0)
% 	lon=[lon(end-ceil(coarsen/2)+1:end,:,:)-360;lon;lon(1:ceil(coarsen/2))+360];
% 	lon_conv=conv(lon,ones(coarsen+1,1)/(coarsen+1));
% 	lat_conv=conv(lat,ones(coarsen+1,1)/(coarsen+1));
% 	lon=lon_conv(1+coarsen:end-coarsen);
% 	lat=lat_conv(1+coarsen:end-coarsen);
% 	lon=lon(1:(coarsen+1):end); 
% 	lat=lat(1:(coarsen+1):end);		
% 	lon=lon(1:end-mod(coarsen,2)); % mod(coarsen,2): because 0=360, get rid of 360
% end
%%
% Initialization
reanalysis_year=str2double(datestr(startDate,'yyyy'))-1;
% Start pre-processing & binning
for date=startDate:endDate

disp(datestr(date))

	%%
	% load Reanalysis-2 column-integrated temperature (1000-200 mb) if it's
	%   not loaded yet
	if (reanalysis_year~=str2double(datestr(date,'yyyy')))
		reanalysis_year=str2double(datestr(date,'yyyy'));
		disp(reanalysis_year)
		date_offset=datenum(reanalysis_year,01,01);
		load([reanalysis_dir 'TAVE_QSAT_' num2str(reanalysis_year)]); 
		TAVE=tave; 
 		QSAT=qsat;
		% load data for 00z on Jan/1 next year
		load([reanalysis_dir 'TAVE_QSAT_' num2str(reanalysis_year+1)]); 
		TAVE(:,:,end+1)=tave(:,:,1);
 		QSAT(:,:,end+1)=qsat(:,:,1);
		% Reanalysis-2 data in single -> double
		lat_reanalysis=double(lat_reanalysis);
		lon_reanalysis=double([lon_reanalysis(end)-360;lon_reanalysis;lon_reanalysis(1)+360]);
		TAVE=double([TAVE(end,:,:);TAVE;TAVE(1,:,:)]); 
 		QSAT=double([QSAT(end,:,:);QSAT;QSAT(1,:,:)]);
	end
	%% 
	% Modify this section for using data different from TMIv7r1 (twice daily)
	% Load TMIv7r1 data
	file_name=[tmi_dir datestr(date,'yyyy') '/f12_'...
							datestr(date,'yyyy') datestr(date,'mm') datestr(date,'dd') 'v7.1'];
	[time,sst,wind11,wind37,vapor,cloud,rain]=read_tmi_day_v7(file_name);
	if (~isempty(time)) % if the data is not missing
		pr_filename=[trmmpr_dir datestr(date,'yyyy') '/2A25rssGrid.' datestr(date,'yyyy') datestr(date,'mm') datestr(date,'dd') '.mat'];
		if exist(pr_filename)
		load(pr_filename)
		% Only consider 20S-20N (with extension for CWV-gap-filling and coarsening)
		time=time([1440-20+1:1440,1:1440,1:20],281-ceil(coarsen/2)-20:440+ceil(coarsen/2)+20,:);
		vapor=vapor([1440-20+1:1440,1:1440,1:20],281-ceil(coarsen/2)-20:440+ceil(coarsen/2)+20,:);
		rain=rain([1440-20+1:1440,1:1440,1:20],281-ceil(coarsen/2)-20:440+ceil(coarsen/2)+20,:);
		rain_pr=rain_pr_rssgrid([1440-20+1:1440,1:1440,1:20],81-ceil(coarsen/2)-20:240+ceil(coarsen/2)+20,:);
		count_pr_rssgrid=count_pr_rssgrid([1440-20+1:1440,1:1440,1:20],81-ceil(coarsen/2)-20:240+ceil(coarsen/2)+20,:);
		% Values greater than 250 indicate missing/bad data
		data_availability=(time<=250).*(rain<=250);%.*(vapor<=250);
		time(~data_availability)=nan;
		rain(~data_availability)=nan;
		vapor(~data_availability)=nan;
		rain_pr(~data_availability)=nan;
		%vapor(vapor>250)=75.3;
		%%
		% Fill missing CWV using max(nearest CWV values)
		nocwv=(rain<=250).*(vapor>250);
		vapor(vapor>250)=nan;
		fillTemp=nan(size(nocwv)); % temp variable used for filling
		for ad_idx=1:2
			nocwv_cc=bwconncomp(nocwv(:,:,ad_idx),4);
			numPixels = cellfun(@numel,nocwv_cc.PixelIdxList);
			for cc_idx=1:length(nocwv_cc.PixelIdxList)
				%xy_list_idx=(yval-1)*nocwv_cc.ImageSize(1)+xval, 2-D index in 1-D
				xval=mod(nocwv_cc.PixelIdxList{cc_idx}-1,nocwv_cc.ImageSize(1))+1; % Note: mod(Nx,Nx)=0 -> Nx
				yval=ceil(nocwv_cc.PixelIdxList{cc_idx}/nocwv_cc.ImageSize(1));
				% For each point, search its sourinding (a square of area~numPixels)
				for sidx=1:length(xval)
					ls=ceil(sqrt(numPixels(cc_idx)+1)/2)-5; % search for an (2*ls+1)x(2*ls+1) box
					vs=nan;
					while sum(~isnan(vs(:)))==0 % extend search area if necessary
						ls=ls+5;
						vs=vapor([max(xval(sidx)-ls,1):min(xval(sidx)+ls,nocwv_cc.ImageSize(1))],...
											[max(yval(sidx)-ls,1):min(yval(sidx)+ls,nocwv_cc.ImageSize(2))],ad_idx);
					end
					[ys,xs]=meshgrid([max(yval(sidx)-ls,1):min(yval(sidx)+ls,nocwv_cc.ImageSize(2))],...
														[max(xval(sidx)-ls,1):min(xval(sidx)+ls,nocwv_cc.ImageSize(1))]);
					% Coordinates with valid CWV in the search area
					xs=xs(~isnan(vs));
					ys=ys(~isnan(vs));
					vs=vs(~isnan(vs));
					% Squared distance w.r.t. (xval(sidx),yval(sidx))
					dist2=(xs-xval(sidx)).^2+(ys-yval(sidx)).^2; 
					fillTemp(xval(sidx),yval(sidx),ad_idx)=max(vs(dist2==min(dist2)));
				end % end for sidx				
			end %end for cc_idx
		end
		vapor(~isnan(fillTemp))=fillTemp(~isnan(fillTemp));
		time=time(21:end-20,21:end-20,:);
		%rain=rain(21:end-20,21:end-20,:);
		rain_pr(count_pr_rssgrid<=count_pr_th)=nan;
		rain=rain_pr(21:end-20,21:end-20,:);
		vapor=vapor(21:end-20,21:end-20,:);
		%% Coarsen
		if (coarsen~=0)
			% Back up time for checking overlapping orbit
			time_b=time(:,1+ceil(coarsen/2):end-ceil(coarsen/2),:);
			% Extend along lon for coarsening
			time=[time(end-ceil(coarsen/2)+1:end,:,:);time;time(1:ceil(coarsen/2),:,:)];
			vapor=[vapor(end-ceil(coarsen/2)+1:end,:,:);vapor;vapor(1:ceil(coarsen/2),:,:)];
			rain=[rain(end-ceil(coarsen/2)+1:end,:,:);rain;rain(1:ceil(coarsen/2),:,:)];
			% Coarsen by convolution
			for ad_idx=1:2
				time_conv2(:,:,ad_idx)=conv2(time(:,:,ad_idx),ones(coarsen+1)/(coarsen+1)^2);
				vapor_conv2(:,:,ad_idx)=conv2(vapor(:,:,ad_idx),ones(coarsen+1)/(coarsen+1)^2);
				rain_conv2(:,:,ad_idx)=conv2(rain(:,:,ad_idx),ones(coarsen+1)/(coarsen+1)^2);
			end
			% Crop the boundaries
			time=time_conv2(1+coarsen:end-coarsen,1+coarsen:end-coarsen,:);
			vapor=vapor_conv2(1+coarsen:end-coarsen,1+coarsen:end-coarsen,:);
			rain=rain_conv2(1+coarsen:end-coarsen,1+coarsen:end-coarsen,:);
			% Identify grids from averaging orbits ~24hr away in time
			overlapOrbitMask=... % The threshold 0.3 is good until coarsen=8 (res=2.25deg)
				( time_b-time([1:size(time_b,1)],[1:size(time_b,2)],:) > 0.3) |...
				( time_b-time([1:size(time_b,1)]+mod(coarsen,2),[1:size(time_b,2)],:) > 0.3) |...
				( time_b-time([1:size(time_b,1)],[1:size(time_b,2)]+mod(coarsen,2),:) > 0.3) |...
				( time_b-time([1:size(time_b,1)]+mod(coarsen,2),[1:size(time_b,2)]+mod(coarsen,2),:) > 0.3);
			if mod(coarsen,2)==1
				overlapOrbitMask(end+1,:,:)=0;
				overlapOrbitMask(:,end+1,:)=0;
			end
			% Get rid of overlaping-orbit points
			time(overlapOrbitMask)=nan;
			vapor(overlapOrbitMask)=nan;
			rain(overlapOrbitMask)=nan;
			% Get rid of overlaping points
			time=time(1:(coarsen+1):end,1:(coarsen+1):end,:);
			vapor=vapor(1:(coarsen+1):end,1:(coarsen+1):end,:);
			rain=rain(1:(coarsen+1):end,1:(coarsen+1):end,:);
			% For lon, 0=360, get rid of 360
			time=time(1:end-mod(coarsen,2),:,:);
			vapor=vapor(1:end-mod(coarsen,2),:,:);
			rain=rain(1:end-mod(coarsen,2),:,:);
		end
		%%
		% Reshape for binning
		lon=LON(:);
		lat=LAT(:);
		time=time(:);
		vapor=vapor(:);
		rain=rain(:);
		lon=lon(~isnan(rain(:)));
		lat=lat(~isnan(rain(:)));
		time=time(~isnan(rain(:)));
		vapor=vapor(~isnan(rain(:)));
		rain=round(rain(~isnan(rain(:)))/(0.1/(coarsen+1)^2)); % rain rate unit -> [0.1/(coarsen+1)^2 mm/hr]
		%%
		% Interpolation for region, That, qsat_hat
		region=uint16(round(interp2(lat_rss,lon_rss,region_rss,lat,lon)));
		That=uint16(round(interp3(lat_reanalysis,lon_reanalysis,[0:6:24],...
									TAVE(:,:,4*(date-date_offset)+1:4*(date-date_offset)+5),...
									lat,lon,time)-T_offset));
		qsat_hat=interp3(lat_reanalysis,lon_reanalysis,[0:6:24],...
									QSAT(:,:,4*(date-date_offset)+1:4*(date-date_offset)+5),...
									lat,lon,time);
		%%
		% Binning
		vapor_index=uint16(round(vapor/cwv_bin_width));
		rain_index=uint16(ceil(rain/(dp*(coarsen+1)^2)))+1;
		for idx=1:length(vapor_index)
			reg=region(idx);
			cwv_idx=vapor_index(idx);
			that_idx=That(idx);
			rain_idx=rain_index(idx);
			if ( (cwv_idx>0)&&(cwv_idx<=number_cwv_bins)...
						&&(reg>0)&&(reg<=number_of_regions)...
						&&(that_idx>0)&&(that_idx<=number_T_bins) )
				BIN(reg,cwv_idx,that_idx,min(rain_idx,PrecMoments))=BIN(reg,cwv_idx,that_idx,min(rain_idx,PrecMoments))+1;
				PMT(reg,cwv_idx,that_idx,:)=PMT(reg,cwv_idx,that_idx,:)+permute([1;rain(idx);rain(idx)^2],[4 3 2 1]); % RHS are all integers
				
				if (vapor(idx)>0.6*qsat_hat(idx))
					QSH(reg,that_idx,min(rain_idx,PrecMoments),1)=QSH(reg,that_idx,min(rain_idx,PrecMoments),1)+1;
					QSH(reg,that_idx,min(rain_idx,PrecMoments),2)=QSH(reg,that_idx,min(rain_idx,PrecMoments),2)+qsat_hat(idx);
				end
			end
		end %end for idx
		
		else
			disp('No Radar Data!')
		end
	end %end-if the data is not missing
end %end for date
% Correct units for precip moments PMT
PMT(:,:,:,2)=PMT(:,:,:,2)*0.1/(coarsen+1)^2;
PMT(:,:,:,3)=PMT(:,:,:,3)*( 0.1/(coarsen+1)^2 )^2;
%%
tave=[T_range_min:T_range_max]';
% Rearrange dimensions of BIN and QSH so that it will be easier for later analysis
BIN=permute(BIN,[2 4 3 1]); % BIN(cwv,precip,tave,reg)
PMT=permute(PMT,[2 4 3 1]); % PMT(cwv,premoment,tave,reg)
QSH=permute(QSH,[3 4 2 1]); % QSH(precip,premoment,tave,reg)
eval(['!mkdir -p ' bin_output_dir]);
save([bin_output_dir bin_output_filename],...
			'cwv','tave','precip_threshold','precip_bdy','precip_binCenter',...
			'BIN','PMT','QSH','resolution','startDate','endDate','count_pr_th');
