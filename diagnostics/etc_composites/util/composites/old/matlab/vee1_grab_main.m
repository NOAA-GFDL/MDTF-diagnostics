%
% grab the data
%
%YEARIN = 1841;
YEARIN1 = 2000;
YEARIN2 = 2029;

% SET basedir to directory holding the txt file.
% basedir = '/Users/jfbooth/MCMS_DIR/VEEV1/READ_VEEV1/'
basedir = '/mnt/drive1/jj/MCMS/MCMS_DIR/3kasym/read_3kasym'

model_in = '3kasym';

all_csi = [];  all_usi = [];
lat_ho =[]; lon_ho =[];
yr_ho = [];  mon_ho =[];  day_ho =[];  hr_ho = [];
slp_ho = []; flags_ho =[];

full_all_csi = [];  
full_all_usi = [];
full_lat_ho =[]; 
full_lon_ho =[];
full_yr_ho = [];  
full_mon_ho =[];  
full_day_ho =[];  
full_hr_ho = [];
full_slp_ho = [];
full_flags_ho =[];

%%% Jimmy code
%{
for nyear = YEARIN1:YEARIN2
  nyear
  %file_in = [basedir,'/out_',model_in,'_output_',num2str(nyear),'.txt']
  file_in = [basedir,'/out_',model_in,'_output_',num2str(YEARIN1),'_',num2str(YEARIN2),'.txt']
  fid = fopen(file_in);
  %------------- READ IN ALL OF THE INFORMATION IN MCMS's TXT FILE.
  
  grab_C_put_into_vec

  convert_MB_to_CYC
  
  save(['veev1_',num2str(nyear)],'cyc')
end
%}


% all the years are in a single file, so have to create cycs for different years

%file_in = [basedir,'/out_',model_in,'_output_',num2str(nyear),'.txt']
file_in = [basedir,'/out_',model_in,'_output_',num2str(YEARIN1),'_',num2str(YEARIN2),'.txt']
fid = fopen(file_in);
grab_C_put_into_vec

for nyear = YEARIN1:YEARIN2
  nyear
  %------------- READ IN ALL OF THE INFORMATION IN MCMS's TXT FILE.

  convert_MB_to_CYC_jj
  
  save(['./out/veev1_',num2str(nyear)],'cyc')
end

