; This file is part of the MJO_suite module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

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
procedure read_model_file (\
	  var_name_in:string, file_in:string,\
	  var_name_out:string,file_out:string,\
	  delete_existing:logical,\
	  i1:integer,i2:integer,time_coord:string,lat_coord:string,lon_coord:string,gwEq:double,date:integer,\
	  var_name_in_3d:string,plev:integer,file_3d:string,file_ps:string)  ; optional args for pressure interp
begin

print("START read_model_file() with file_in = "+file_in+", var_name_in ="+var_name_in)
;print("      var_name_in_3d "+var_name_in)
;print("      var_name_out "+var_name_out)

; need to deal with missing input arguments here by
; if (.not.isvar("")) then
;    var = defaults
; end if

if (fileexists(file_out) .and. (.not. delete_existing)) then  ; DON'T WRITE NEW FILE
;      print("L49 fileexists and not delete_existing")
      print("WARNING: using existing file "+file_out)
      print("         To over-ride, change delete_existing in call to "+get_script_name())

else  ; DO WRITE NEW FILE

   if (fileexists(file_out)) then
;      print("L60 fileexists and delete_existing")
      print("WARNING: over-writing existing file "+file_out)
      system("rm "+file_out)
   end if

   if( isfilepresent(file_in) ) then

    f_in = addfile(file_in,"r")


    var = f_in->$var_name_in$($time_coord$|i1:i2,{$lat_coord$|-40:40},$lon_coord$|:)

   else; if( isfilepresent(file_in) ) then

    print("WARNING: file does not exist for MJO diagnostics: "+file_in)
    print("         Looking for file matching "+var_name_in_3d+" at plev "+tostring(plev))

    ; needs a bunch of checks for var_name_in_3d, plev and this
    if (.not.isvar("file_ps")) then
    end if

    f_3d    = addfile(file_3d,"r")
    f_ps    = addfile(file_ps,"r")
    var_1 = pinterp(var_name_in_3d,plev,f_3d,f_ps)
    var = var_1($time_coord$|i1:i2,{$lat_coord$|-40:40},$lon_coord$|:)


   end if ; if( isfilepresent(file_in) ) then

   print("writing "+file_out)
   fo = addfile(file_out,"c")
   fo->gw = gwEq
   fo->date = date
   fo->$var_name_out$ = var
   print("Finished writing file")

end if; if (fileexists(file_out) .and. (.not. delete_existing)) 



end
