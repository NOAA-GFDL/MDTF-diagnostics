; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

;================================================================================
function pinterp (var_name:string,plev:float,fin:file,fin_ps:file)
begin

        print(get_script_name()+":pinterp() interpolating "+var_name+" to pressure level "+plev+" mbar")
	if (isvar("fin_ps")) then
;	   print("found separate PS file ")
        else
;   	   print("assuming PS in only input file ")
	   fin_ps = fin
	end if	   

        ps = fin_ps->PS

        hyam = fin->hyam
        hybm = fin->hybm
        p0 = fin->P0

        if ( p0@units.eq."Pa" ) then
;          print("NOT converting p0 units from Pa to mb")
          p0 = p0*0.01
          p0@units = "mb" 
        end if
        if ( (p0@units.ne."mb").and.(p0@units.ne."mbar")) then
          print("ERROR: p0 units expected to be Pa or mb/mbar. File ")
          exit
        end if
        if ( (ps@units.ne."Pa")) then
          print("ERROR: p0 units expected to be Pa "+fin)
          exit
        end if
        var_in = fin->$var_name$
        var_in_p = vinth2p(var_in,hyam,hybm,plev,ps,2,p0,1,False)
;        print("debug P0 "+p0+" range PS "+min(ps)+" "+max(ps))
;psfc A multi-dimensional array of surface pressures in Pa. 
;p0   Scalar numeric value equal to surface reference pressure in mb. 

        return var_in_p(:,0,:,:)
end

;================================================================================
function read_dim(f,var_name,opt)
begin 

  routine_name = "read_dim"
  verbose = False

  if ( opt ) then
    if ( isatt(opt,"lower_bound")) then
      lower_bound = opt@lower_bound
;      print("found lower_bound "+lower_bound)
    end if
    if ( isatt(opt,"upper_bound")) then
      upper_bound = opt@upper_bound
;      print("found upper_bound "+upper_bound)
    end if
  end if
  if ( isvar("lower_bound").and.(isvar("upper_bound"))) then
;    print("read dim bounding "+var_name+" by "+lower_bound+" "+upper_bound)
    var = f->$var_name$({lower_bound:upper_bound})
;    printVarSummary(var)
  else
;    print(routine_name+" "+var_name+" with no bounds")
    var = f->$var_name$
  end if


  return var
end ; read_dim

;================================================================================
function get_gw(f,latS,latN)
begin 

if(isfilevar(f,"gw")) then
  if (isvar("gw")) then
    delete(gw)
  end if 
  lat_coord = getenv("lat_coord")
  new_gw = f->gw({$lat_coord$|latS:latN})
else
   lat = read_dim(f, getenv("lat_coord"),False)  ;get whole thing, cut range below
   nlat = dimsizes(lat)
   slat = new((/nlat+1/),"double")
   gw = new((/nlat/),"double")
   gw!0 = "lat"
   gw&lat = lat
   if( lat(0).lt.lat(1) ) then
       slat(0) = -90.d0        
       slat(nlat) = 90.d0
   else
       slat(0) = 90.d0  
       slat(nlat) = -90.d0
   end if

   do i=1,nlat-1
       slat(i) = (lat(i-1)+lat(i))/2.d0
   end do

   pi = 4.d0*atan(1.d0)
   do i=0,nlat-1
      gw(i) = abs(sin(slat(i+1)/180.d0*pi)-sin(slat(i)/180.d0*pi))
   end do
   delete(slat)

   new_gw = gw({latS:latN})

   
end if

;print("get_gw"+ getvardims(new_gw))

return new_gw
end ;function get_gw(f,latS,latN)

procedure replace_dim_name(var,old_name,new_name)
begin

  dimNames = getvardimnames(var)  
;  print(dimNames)

  dim_i = ind(dimNames.eq.old_name)
  if ( .not. ismissing(dim_i)) then
    var!dim_i = new_name
  end if

end ; replace_dim_name

procedure interp_save_res(var_name,interp_opts,lat,lon,gw)
begin
       interp_opts@lat_interp_to = lat
       interp_opts@lon_interp_to = lon
       interp_opts@gw = gw
       print("Interpolation: Stored lat/lon from "+var_name+" as desired resolution"+\
            dimsizes(interp_opts@lat_interp_to)+" "+ dimsizes(interp_opts@lon_interp_to))
end ; interp_save_res

function interp_to_saved_res(var_name,interp_opts,var_in)
begin
     ; expected settings (I don't want to have to check)
     ; lat_interp_to (yo), lon_interp_to (xo)
  if (( .not. isatt(interp_opts,"lat_interp_to")) .or. (.not. isatt(interp_opts,"lat_interp_to"))) then
    print("ERROR MJO_Suite utils.ncl interp_to_saved_res")
    print("      Missing interp_opts@lat_interp_to OR interp_opts@lon_interp_to")
    print(interp_opts)
    interp_opts@error = True
    exit
  end if

  fiCyclicX = True ;     ; if global data but longitude values don't quite wrap all the way around the globe.

  dimsize_lon_in = dimsizes(var_in&lon)
  dimsize_lon_interp_to = dimsizes(interp_opts@lon_interp_to)
  if ( dimsize_lon_in .ne. dimsize_lon_interp_to ) then
    print("Found different lon from saved. Interpolating..."+\
          "from "+dimsize_lon_in +"x"+dimsizes(var_in&lat)+\
          " to "+dimsize_lon_interp_to+"x"+dimsizes(interp_opts@lat_interp_to))
    var_out = linint2_Wrap(var_in&lon,var_in&lat,var_in,fiCyclicX, \
                           interp_opts@lon_interp_to,interp_opts@lat_interp_to,0)

    ; returns wrong dimnames. argh. 
    replace_dim_name(var_out,"LAT","lat")
    replace_dim_name(var_out,"LON","lon")

    return var_out

  else
    print("Lon for var "+var_name+" same as stored. NOT interpolating...")
;          "from "+dimsize_lon_in +"x"+dimsizes(var&lat)+\
;          "to "+dimsize_lon_interp_to+"x"+interp_opts@lat_interp_to)
    return var_in  ;gotta return something!
  end if

end ; interp_to_saved_res

;================================================================================
; DRB: should be called 're-write model file'
; The only point seems to be writing a file with only the necessary
; time dimension, and lat bounds, and putting gw in. 
; Why not just read in and use with bounds?
;
procedure read_model_file (\   
	  var_name_in:string, file_in:string,\
	  var_name_out:string,file_out:string,\
	  delete_existing:logical,\
	  i1:integer,i2:integer,time_coord:string,lat_coord:string,lon_coord:string,date:integer,\
          interp_opts,\  ; optional args for interpolating in space
	  var_name_in_3d:string,plev:integer,file_3d:string,file_ps:string)  ; optional args for pressure interp
begin

;print("START read_model_file() with file_in = "+file_in+", var_name_in ="+var_name_in)
;print("      var_name_in_3d "+var_name_in)
;print("      var_name_out "+var_name_out)


; need to deal with missing input arguments here by
; if (.not.isvar("")) then
;    var = defaults
; end if

latS = -40
latN = 40
opt = True 
opt@lower_bound = latS
opt@upper_bound = latN


if (fileexists(file_out) .and. (.not. delete_existing)) then  ; DON'T WRITE NEW FILE
;      print("L49 fileexists and not delete_existing")
      print("WARNING: using existing file "+file_out)
      print("         To over-ride, change delete_existing in call to "+get_script_name())

      if ( interp_opts ) then  ;since not re-writing, read from already-written-outfile
        if ( interp_opts@interp_to_var_name .eq. var_name_out ) then ; save
          f_out_for_interp = addfile(file_out,"r")
          var = f_out_for_interp->$var_name_out$
          gw = get_gw(f_out_for_interp,latS,latN) 
          interp_save_res(var_name_out,interp_opts,var&lat,var&lon,gw)
          delete(f_out_for_interp)
        end if
      end if
else  ; DO WRITE NEW FILE

   if (fileexists(file_out)) then
;      print("L60 fileexists and delete_existing")
      print("WARNING: over-writing existing file "+file_out)
      system("rm "+file_out)
   end if

   if( isfilepresent(file_in) ) then

;    print("opening "+var_name_in+" from "+file_in)
    f_in = addfile(file_in,"r")

    lat = read_dim(f_in, getenv("lat_coord"),opt)
    opt = False
    lon = read_dim(f_in, getenv("lon_coord"),opt)
;    gwEq = get_gw(f_in,latS,latN) ; to calculate for here 
    gw = get_gw(f_in,latS,latN) 

    var = f_in->$var_name_in$($time_coord$|i1:i2,{$lat_coord$|-40:40},$lon_coord$|:)

   else; if( isfilepresent(file_in) ) then

    print("WARNING: file does not exist for MJO diagnostics: "+file_in)
    print("         Looking for file matching "+var_name_in_3d+" at plev "+tostring(plev))

    ; needs a bunch of checks for var_name_in_3d, plev and file_ps
    if (.not.isvar("file_ps")) then
      print("ERROR: can't find required PS file "+file_ps)
      exit
    end if

    f_3d    = addfile(file_3d,"r")
    f_ps    = addfile(file_ps,"r")
    var_1 = pinterp(var_name_in_3d,plev,f_3d,f_ps)
    var = var_1($time_coord$|i1:i2,{$lat_coord$|-40:40},$lon_coord$|:)

   end if ; if( isfilepresent(file_in) ) then
   
   if ( interp_opts ) then
     if ( interp_opts@interp_to_var_name .eq. var_name_out ) then ; save
       gw = get_gw(f_in,latS,latN) 
       interp_save_res(var_name_out,interp_opts,var&lat,var&lon,gw)
       if ( isatt(interp_opts,"error")) then
         print("ERROR: interp_save_res failed.")
         exit
       end if
     else
       if (isvar("var_new_res") ) then
         print("Somehow var_new_res still survives")
       end if
       var_new_res = interp_to_saved_res(var_name_out,interp_opts,var)
       delete(var)
       var = var_new_res

       ; dims also need to be changed
       if (isvar("gw")) then
         delete(gw)
       end if
       gw = interp_opts@gw

       delete(var_new_res)
     end if
   else 
     gw = get_gw(f_out_for_interp,latS,latN) 
   end if ; interp_opts
   
; ---------- Writing new file --------------------------
;   print("Creating "+file_out)
   fo = addfile(file_out,"c")


;   print("Trying to write "+var_name_out)
;   printVarSummary(var)

   fo->$var_name_out$ = var
;   print(fo)

   ; These get written automatically because they are dimensions of var
;   fo->lat = lat
;   fo->lon = lon


   gw!0 = "lat"
   gw&lat = var&lat
   fo->gw = gw
   date!0 = "time"
   date&time = var&time
   fo->date = date

   print("Finished writing file "+file_out)
   system("ls "+file_out)
;   print(fo)

   
end if; if (fileexists(file_out) .and. (.not. delete_existing)) 



end
