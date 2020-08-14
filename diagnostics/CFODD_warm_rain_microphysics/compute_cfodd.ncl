;************************************************
; compute statistics for CFODD.
;************************************************
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"   
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
;
;************************************************
  begin
  variab_dir = getenv("variab_dir")
  casename = getenv("CASENAME")
  time_freq = getenv("time_freq")

; coordinates
  time_coord = getenv("time_coord")
  subcol_coord = getenv("subcol_coord")
  lat_coord = getenv("lat_coord")
  lon_coord = getenv("lon_coord")
  lev_coord = getenv("lev_coord")

; model setups
  reff_conversion_factor=getenv("reff_conversion_factor")
  re_conv_f=stringtofloat(reff_conversion_factor)

;------------------------------------------------------------------------------
; Set data path and file/variable names
;------------------------------------------------------------------------------
; data path
  data_path=getenv("DATADIR")+"/"+time_freq

; files
  file_dtau_s=casename+"."+getenv("dtau_s_var")+"."+time_freq+".nc"
  file_liq_wat=casename+"."+getenv("liq_wat_var")+"."+time_freq+".nc"
  file_ice_wat=casename+"."+getenv("ice_wat_var")+"."+time_freq+".nc"
  file_temp=casename+"."+getenv("ta_var")+"."+time_freq+".nc"
  file_cldtop_reff=casename+"."+getenv("cldtop_reff_var")+"."+time_freq+".nc"
  file_cld_reff=casename+"."+getenv("cld_reff_var")+"."+time_freq+".nc"
  file_dbze=casename+"."+getenv("dbze_var")+"."+time_freq+".nc"
  file_ctype=casename+"."+getenv("cloud_type_var")+"."+time_freq+".nc"

; variables
  dtau_s_var=getenv("dtau_s_var")
  liq_wat_var=getenv("liq_wat_var")
  ice_wat_var=getenv("ice_wat_var")
  ta_var=getenv("ta_var")
  cldtop_reff_var=getenv("cldtop_reff_var")
  cld_reff_var=getenv("cld_reff_var")
  dbze_var=getenv("dbze_var")
  ctype_var=getenv("cloud_type_var")

;------------------------------------------------------------------------------
; check the existance of the netCDF output file
;------------------------------------------------------------------------------
; CFODD output file
  if ( fileexists(variab_dir+"/CFODD_warm_rain_microphysics/model/netCDF/"+casename+".CFODD_ocean.nc") ) then
    print(" "+ variab_dir+"/CFODD_warm_rain_microphysics/model/netCDF/"+casename+".CFODD_ocean.nc exists!!")
    print(" Use "+variab_dir+"/CFODD_warm_rain_microphysics/model/netCDF/"+casename+".CFODD_ocean.nc!!")
    exit
  end if
;------------------------------------------------------------------------------
; check the existance of the input model data
;------------------------------------------------------------------------------
;dbze
  ;print(file_dbze(0))
  ;do iscol=0,nscol-1
  ;  if ( .not. fileexists(data_path+"/"+file_dbze(iscol)) ) then
  ;    print("ERROR missing file "+data_path+"/"+file_dbze(iscol))
  ;    exit
  ;  end if
  ;end do

;ctype
  ;do iscol=0,nscol-1
  ;  if ( .not. fileexists(data_path+"/"+file_ctype(iscol)) ) then
  ;    print("ERROR missing file "+data_path+"/"+file_ctype(iscol))
  ;    exit
  ;  end if
  ;end do

;dtau_s 
  ;if ( .not. fileexists(data_path+"/"+file_dtau_s) ) then
  ;  print("ERROR missing file "+data_path+"/"+file_dtau_s)
  ;  exit
  ;end if

;liq_wat 
  ;if ( .not. fileexists(data_path+"/"+file_liq_wat) ) then
  ;  print("ERROR missing file "+data_path+"/"+file_liq_wat)
  ;  exit
  ;end if

;ice_wat
  ;if ( .not. fileexists(data_path+"/"+file_ice_wat) ) then
  ;  print("ERROR missing file "+data_path+"/"+file_ice_wat)
  ;  exit
  ;end if

;temp
  ;if ( .not. fileexists(data_path+"/"+file_temp) ) then
  ;  print("ERROR missing file "+data_path+"/"+file_temp)
  ;  exit
  ;end if

;cldtop_reff or cld_reff
  if ( fileexists(data_path+"/"+file_cldtop_reff)) then
    use_cldtop_reff=True
  else
    use_cldtop_reff=False
    if ( .not. fileexists(data_path+"/"+file_cld_reff)) then
      print("ERROR missing file "+data_path+"/"+file_cldtop_reff+" or "+ \
            data_path+"/"+file_cld_reff)
      exit
    end if
  end if

;------------------------------------------------------------------------------
; creat bin information (radar reflectivity and optical depth) for CFODD
;------------------------------------------------------------------------------
  num_rebin=6
  num_cotbin=15
  num_zebin=25
  pdfcz=new((/num_rebin,num_cotbin,num_zebin/),"float")
  pdfcz=0.0
  count_cld_sum=new((/num_rebin,num_cotbin/),"float")
  count_cld_sum=0.0
  
  ;--re bin setup--
  rebnd_center=new((/num_rebin/),"float")
  re_min=0.
  re_max=30.
  rebnd=fspan(re_min,re_max,num_rebin+1)
  do ire=0,num_rebin-1
    rebnd_center(ire)=0.5*(rebnd(ire)+rebnd(ire+1))
  end do
  re_del=(re_max-re_min)/num_rebin
  
  ;--cot bin setup--
  cotbnd=new((/num_cotbin+1/),"float")
  cotbnd_center=new((/num_cotbin/),"float")
  cot_min=0.
  cot_max=60.
  cotbnd=fspan(cot_min,cot_max,num_cotbin+1)
  do ic=0,num_cotbin-1
     cotbnd_center(ic)=0.5*(cotbnd(ic)+cotbnd(ic+1))
  end do
  cot_del=(cot_max-cot_min)/num_cotbin
  
  ;--ze bin setup--
  zebnd=new((/num_zebin+1/),"float")
  zebnd_center=new((/num_zebin/),"float")
  ze_min=-30.
  ze_max=20.
  zebnd=fspan(ze_min,ze_max,num_zebin+1)
  do iz=0,num_zebin-1
     zebnd_center(iz)=0.5*(zebnd(iz)+zebnd(iz+1))
  end do
  ze_del=(ze_max-ze_min)/num_zebin
  

  qcld_min=1.0e-4
  rair=287.04 ; gas constant

;--variable to count # of clouds in each bin --
  count_cld=new((/num_rebin,num_cotbin,num_zebin/),"float")
  count_cld(:,:,:)=0.0

  print("Opening file "+data_path+"/"+file_dbze)
  fdbze=addfile(data_path+"/"+file_dbze,"r")
  nscol=dimsizes(fdbze->$subcol_coord$)
  ntime=dimsizes(fdbze->$time_coord$)
  nlev=dimsizes(fdbze->$lev_coord$)
  nlat=dimsizes(fdbze->$lat_coord$)
  nlon=dimsizes(fdbze->$lon_coord$)
  lat=fdbze->$lat_coord$
  lon=fdbze->$lon_coord$
  pres=fdbze->$lev_coord$
  delete(fdbze)

 ; check if the level coordinate is in Pa at first step.
  if (max(pres) .gt. 800. .and. max(pres) .lt. 1500.) 
    pres=pres*100.  ;hPa to Pa
  else 
    if (max(pres) .gt. 80000. .and. max(pres) .lt. 150000.)  
      pres=pres     
    else 
      print("*** Make sure the vertical coordinate is in units of hPa or Pa !! ***")
      exit
    end if
  end if
  
 ; check whether the level coordinate is in up-down or down-up order. 
  if (pres(0) .lt. pres(nlev-1)) then
    vert_ord="updown"
  else 
    if (pres(0) .gt. pres(nlev-1)) then
      vert_ord="downup"
    end if
  end if
  if (vert_ord .eq. "downup") then
    pres=pres(::-1)
  end if
  
;------------------------------------------------------------------------------
; creat the land_sea mask according to lat and lon
;------------------------------------------------------------------------------
  landsea_file= addfile("$NCARG_ROOT/lib/ncarg/data/cdf/landsea.nc","r")
  lsdata=landsea_file->LSMASK
  lsm = landsea_mask(lsdata,lat,lon) ;0=ocean, 1=land, 2=lake, 3=small island, 4=ice shelf.
  delete(landsea_file)

  ctop_idx_wm=new((/nlat,nlon/),"integer")
  ctop_re_bin=new((/nlat,nlon/),"integer")
  cot_bin=new((/nlev,nlat,nlon/),"integer")
  ctop_idx_wm=-9999
  ctop_re_bin=-9999
  cot_bin=-9999

  total_task=int2flt(nscol*ntime)
  begtime=get_cpu_time()/60.
  remntime=-999.
  
  track="-----START-----"
  asciiwrite(variab_dir+"/CFODD_warm_rain_microphysics/run_where.txt",track)
  delete(track)
  
  do it=0,ntime-1
  
  ;----------------------------------------------------
  ; read input data (except for subcolumns)
  ;----------------------------------------------------

  ;liq_wat

    f=addfile(data_path+"/"+file_liq_wat,"r")
    liq_wat=f->$liq_wat_var$($time_coord$|it,$lev_coord$|:,$lat_coord$|:,$lon_coord$|:)
    liq_wat=where(liq_wat .ge. 0., liq_wat, 0.)
    delete(f)
  
  ;ice_wat
    f=addfile(data_path+"/"+file_ice_wat,"r")
    ice_wat=f->$ice_wat_var$($time_coord$|it,$lev_coord$|:,$lat_coord$|:,$lon_coord$|:)
    ice_wat=where(ice_wat .ge. 0., ice_wat, 0.)
    delete(f)

  ;total cloud water
    qcld=liq_wat+ice_wat
  
  ;dtau_s
    f=addfile(data_path+"/"+file_dtau_s,"r")
    dtau_s=f->$dtau_s_var$($time_coord$|it,$lev_coord$|:,$lat_coord$|:,$lon_coord$|:)
    dtau_s=where(dtau_s .gt. 0., dtau_s, 0.0) 
    delete(f)
  
  ;temp
    print("Opening file "+data_path+"/"+file_temp)
    f=addfile(data_path+"/"+file_temp,"r")
    print(" Looking for variables: "+time_coord+" "+lev_coord+" "+lat_coord+" "+lon_coord+" ")
    temp=f->$ta_var$($time_coord$|it,$lev_coord$|:,$lat_coord$|:,$lon_coord$|:)
    delete(f)
    
  ;cldtop_reff or cld_reff  
    if (use_cldtop_reff) then
      f=addfile(data_path+"/"+file_cldtop_reff,"r")
      cldtop_reff=f->$cldtop_reff_var$($time_coord$|it,$lat_coord$|:,$lon_coord$|:)
      cldtop_reff=where(cldtop_reff .ge. 0, cldtop_reff*re_conv_f, -999.0)
      delete(f)
    else
      f=addfile(data_path+"/"+file_cld_reff,"r")
      cld_reff=f->$cld_reff_var$($time_coord$|it,$lev_coord$|:,$lat_coord$|:,$lon_coord$|:)
      cld_reff=where(cld_reff .ge. 0, cld_reff*re_conv_f, -999.0)
      delete(f)
    end if

  ;----------------------------------------------------
  ; flip vertical order to updown if it is downup
  ;----------------------------------------------------

    if (vert_ord .eq. "downup") then
      liq_wat(:,:,:) = liq_wat(::-1,:,:)
      ice_wat(:,:,:) = ice_wat(::-1,:,:)
      qcld(:,:,:)    = qcld(::-1,:,:) 
      dtau_s(:,:,:)  = dtau_s(::-1,:,:) 
      temp(:,:,:)    = temp(::-1,:,:)
      if (.not. use_cldtop_reff) then
        cld_reff(:,:,:) = cld_reff(::-1,:,:)
      end if
    end if 

 ;------------------------------------------------------------------------------
 ; Identify warm clouds, save cloud top level, cloud top reff bin, and COD profile. 
 ;------------------------------------------------------------------------------

    do ilon=0,nlon-1
      do ilat=0,nlat-1
        surf_type=lsm(ilat,ilon)
        ;only over ocean
        if (surf_type .eq. 0) then
         ;determin warm cloud top
          do ilev=0,nlev-1
	    qcld_min=1.0e-4
	    rair=287.04 ; gas constant
	    qcld_tmp=pres(ilev)/(rair*temp(ilev,ilat,ilon)) * qcld(ilev,ilat,ilon)
	    if (qcld_tmp .gt. qcld_min) then ;detect cloud top 
              if( temp(ilev,ilat,ilon) .ge. 273.15) then  ;warm cloud or not 

                ctop_idx_wm (ilat,ilon)=ilev  ;warm cloud top loation
                if (use_cldtop_reff) then 
                   ctop_re=cldtop_reff(ilat,ilon)
                else
                   ctop_re=cld_reff(cldtop_idx,ilat,ilon)
                end if
                ctop_re_bin(ilat,ilon)=toint(floor((ctop_re-re_min)/re_del)) ;ctop re bin
              end if
              break
            end if
          end do ;ilev

          if (ctop_idx_wm(ilat,ilon) .ge. 0) then
            taud_tmp=0.0
            do ilev=ctop_idx_wm(ilat,ilon),nlev-1
              taud_tmp=taud_tmp+dtau_s(ilev,ilat,ilon)
              cot_bin(ilev,ilat,ilon)= toint(floor((taud_tmp-cot_min)/cot_del))
            end do
          end if
        end if ; surf_type
      end do ;ilon
    end do ;ilat

 ;------------------------------------------------------------------------------
 ; counting numbers cloud occurence in each (reff, COD, Ze) bin. 
 ; loop over subcolumns within a timestep.
 ;------------------------------------------------------------------------------
   ;1. dbze
    fdbze=addfile(data_path+"/"+file_dbze,"r")
   ;2. ctype
    fctype=addfile(data_path+"/"+file_ctype,"r")

    if (it .eq. 0) then
      nscol=dimsizes(fdbze->$subcol_coord$)
    end if

    do iscol=0,nscol-1

      curr_task=it*nscol+iscol 
      per_task=(curr_task/total_task)*100.
     
    ; write runwhere information to file
      if (remntime .gt. 0) then 
        track="Processing time "+tostring(it+1)+" of "+tostring(ntime)+ \
          ",subcolumn "+tostring(iscol+1)+" of "+tostring(nscol)+" ..."+ \
          sprintf("%5.1f",per_task)+"%."+                                \
          " Remaining time: ~"+sprintf("%5.1f",remntime)+" min."
      else
        track="Processing time "+tostring(it+1)+" of "+tostring(ntime)+ \
          ",subcolumn "+tostring(iscol+1)+" of "+tostring(nscol)+" ..."+ \
          sprintf("%5.1f",per_task)+"%."
      end if
      asciiwrite(variab_dir+"/CFODD_warm_rain_microphysics/run_where.txt",track)
      delete(track)

    ;----------------------------------------------------
    ; read input data (subcolumns)
    ;----------------------------------------------------
      dbze_prof  = fdbze->$dbze_var$($subcol_coord$|iscol,$time_coord$|it,$lev_coord$|:, \
                   $lat_coord$|:,$lon_coord$|:)
      ctype_prof = fctype->$ctype_var$($subcol_coord$|iscol,$time_coord$|it,$lev_coord$|:, \
                   $lat_coord$|:,$lon_coord$|:)

    ; use only large scale clouds
      dbze_prof=where(ctype_prof .eq. 1. .and. dbze_prof .gt. ze_min, dbze_prof, \
                   dbze_prof@_FillValue)

      do ilon=0,nlon-1
        do ilat=0,nlat-1
          if (surf_type .eq. 0) then  ;only over ocean
            if (ctop_idx_wm(ilat,ilon) .ge. 0 ) then 
              do ilev=ctop_idx_wm(ilat,ilon),nlev-1
                dbze_tmp=dbze_prof(ilev,ilat,ilon)
                if (ismissing(dbze_tmp)) then 
                  continue
                end if
                if (dbze_tmp .ge. ze_min) then 
                  izebin= toint(floor((dbze_tmp-ze_min)/ze_del))
	          icotbin=cot_bin(ilev,ilat,ilon)
	          irebin=ctop_re_bin(ilat,ilon)
                  if (irebin .ge. 0 .and. irebin .lt. num_rebin .and. \
                    icotbin .ge. 0 .and. icotbin .lt. num_cotbin .and. \
                    izebin .ge. 0 .and. izebin .lt. num_zebin) then 
                    count_cld(irebin,icotbin,izebin)=count_cld(irebin,icotbin,izebin)+1
                  end if
                end if 
              end do ;ilev
	    end if ; ctop_idx_wm .ge. 0 
	  end if ;surf_type .eq. 0
        end do ;ilon
      end do ;ilat

    end do ;iscol

    nowtime=get_cpu_time()/60.
    elaptime=nowtime-begtime
    steptime=tofloat(elaptime)/tofloat(it+1)
    remntime=(tofloat(ntime)-tofloat(it+1))*steptime

    ctop_idx_wm=-9999
    ctop_re_bin=-9999
    cot_bin=-9999
  end do ;it

;----------------------------------------------------
; compute PDF
;----------------------------------------------------

  do ii=0,num_rebin-1
   do jj=0,num_cotbin-1
     count_cld_sum(ii,jj)=sum(count_cld(ii,jj,:))
     count_cld_sum_tmp=count_cld_sum(ii,jj)
     if (count_cld_sum_tmp .gt. 0 ) then
       do kk=0,num_zebin-1
         pdfcz(ii,jj,kk)=count_cld(ii,jj,kk)/count_cld_sum_tmp*100./ze_del
       end do
     end if
   end do
  end do
  
  pdfcz!0="reff"
  pdfcz!1="cot"
  pdfcz!2="zmax"
  pdfcz&reff=rebnd_center
  pdfcz&cot=cotbnd_center
  pdfcz&zmax=zebnd_center
  
  count_cld_sum!0="reff"
  count_cld_sum!1="cot"
  count_cld_sum&reff=rebnd_center
  count_cld_sum&cot=cotbnd_center
  
;------------------------------------------------------------------------------
; Write PDFs and counts to netCDF file
;------------------------------------------------------------------------------
  fo = addfile(variab_dir+"/CFODD_warm_rain_microphysics/model/netCDF/"+casename+".CFODD_ocean.nc","c")
  fo->cfodd = pdfcz
  fo->count = count_cld_sum
  
  nowtime=get_cpu_time()/60.
  elaptime=nowtime-begtime
  track="FINISHED. Elapsed time = " + sprintf("%5.1f",elaptime)+" min."
  asciiwrite(variab_dir+"/CFODD_warm_rain_microphysics/run_where.txt",track)
  delete(track)

  end
