; This file is part of the Wheeler_Kiladis module of the MDTF code package (see LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"


undef("getVarSlice")
function getVarSlice( fili[*], varName:string, level, latS, latN, lonL, lonR, tstride:integer, i1:integer, i2:integer)
begin


    nfil = dimsizes(fili)
    f    = addfile (fili(0), "r")

    combine_precs=False

    if (.not.isfilevar(f,varName)) then
       if (varName .eq. "PRECT") then
          if (isfilevar(f,"PRECC").and.isfilevar(f,"PRECL")) then
             combine_precs=True
             print("getVarSlice: PRECT is being computed from PRECC and PRECL")
          else
             print("getVarSlice: PRECT,PRECC, and/or PRECL are not variables in file "+fili(0))
          end if
       else
          print("getVarSlice: "+varName+" is not a variable in file "+fili(0))
          exit
       end if
    end if

    if (combine_precs) then
       rank = dimsizes( filevardimsizes(f,"PRECC") )
    else
       rank = dimsizes( filevardimsizes(f,varName) )
    end if 

    if (rank.lt.3 .or. rank.gt.4) then
        print("getVarSlice: only 3D and 4D supported: rank="+rank+"D")
        exit
    end if

; The following tmpx variables are a workaround for a bug in the stride
; argument when using addfiles.

    if (nfil.eq.1) then                    ; SINGLE FILE    
       if (rank.eq.3) then
           if (combine_precs) then
              tmpp  = f->PRECC(i1:i2,{latS:latN},{lonL:lonR})
              precc  = tmpp(::tstride,:,:)
              tmpp  = f->PRECL(i1:i2,{latS:latN},{lonL:lonR})
              precl  = tmpp(::tstride,:,:)
              x  = precc
              x  = (/precc+precl/)
              delete(tmpp)
              delete(precc)
              delete(precl)
           else
              tmpx  = f->$varName$(i1:i2,{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:)
              delete(tmpx)
           end if
       else
           if (combine_precs) then
              tmpp  = f->PRECC(i1:i2,{level},{latS:latN},{lonL:lonR})
              precc  = tmpp(::tstride,:,:,:)
              tmpp  = f->PRECL(i1:i2,{level},{latS:latN},{lonL:lonR})
              precl  = tmpp(::tstride,:,:,:)
              x  = precc
              x  = (/precc+precl/)
              delete(tmpp)
              delete(precc)
              delete(precl)
           else
              tmpx  = f->$varName$(i1:i2,{level},{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:,:)
              delete(tmpx)
           end if
       end if
    else      
                             ; MULTIPLE FILES
       if (combine_precs) then
          dNam   = getfilevardims(f,"PRECC")
       else
          dNam   = getfilevardims(f,varName)
       end if
 
       setfileoption("nc","SuppressClose",False)
 
       flist  = addfiles( fili, "r")
                                              ; make TIME  [tedious]
;
;
;       TIME           = flist[:]->$dNam(0)$(::tstride)   ; values
       tmpt            = flist[:]->$dNam(0)$(i1:i2)
       TIME           = tmpt(::tstride)
       delete(tmpt)
       if (isfilevaratt(flist[0],  dNam(0) ,  "units") ) then  
           TIME@units = flist[0]->$dNam(0)$@units   ; assign units attribute
       end if
       if (isfilevarcoord( flist[0], dNam(0), dNam(0) ) ) then
           TIME!0     = dNam(0)          ; name the dimension
           TIME&$dNam(0)$ = TIME         ; assign values [coord]
       end if

       if (rank.eq.3) then
          if (combine_precs) then
             tmpp   = flist[:]->PRECC(i1:i2,{latS:latN},{lonL:lonR})
             precc   = tmpp(::tstride,:,:)
             tmpp   = flist[:]->PRECL(i1:i2,{latS:latN},{lonL:lonR})
             precl   = tmpp(::tstride,:,:)
             x  = precc
             x  = (/precc+precl/)
             delete(tmpp)
             delete(precc)
             delete(precl)
          else
             tmpx   = flist[:]->$varName$(i1:i2,{latS:latN},{lonL:lonR})
             x   = tmpx(::tstride,:,:)
             delete(tmpx)
          end if
 
          x!0 = dNam(0)
          x!1 = dNam(1)
          x!2 = dNam(2)
 
       else
          if (combine_precs) then
             tmpp   = flist[:]->PRECC(i1:i2,{level},{latS:latN},{lonL:lonR})
             precc   = tmpp(::tstride,:,:,:)
             tmpp   = flist[:]->PRECL(i1:i2,{level},{latS:latN},{lonL:lonR})
             precl   = tmpp(::tstride,:,:,:)
             x  = precc
             x  = (/precc+precl/)
             delete(tmpp)
             delete(precc)
             delete(precl)
          else
             tmpx   = flist[:]->$varName$(i1:i2,{level},{latS:latN},{lonL:lonR})
             x   = flist[:]->$varName$(::tstride,:,:,:)
             delete(tmpx)
          end if
          x!0 = dNam(0)
          x!1 = dNam(2)
          x!2 = dNam(3)
       end if

    ; NOT required but create meta data

       dNamx  = getvardims(x)            
     
       x&$dNamx(0)$ = TIME      ; assign coordinates
       x&$dNamx(1)$ = flist[0]->$dNamx(1)$({latS:latN})
       x&$dNamx(2)$ = flist[0]->$dNamx(2)$({lonL:lonR})
       if (isfilevaratt( flist[0], varName, "long_name")) then
           if (combine_precs) then
              x@long_name = "total precipitation"
           else
              x@long_name = flist[0]->$varName$@long_name
           end if
       end if
       if (isfilevaratt( flist[0], varName, "units"    )) then  
           if (combine_precs) then
              x@units = flist[0]->PRECC@units
           else
              x@units = flist[0]->$varName$@units
          end if     
       end if     
    end if

    if (isatt(x,"_FillValue")) then
       nMsg = num(ismissing(x))
       if (nMsg.gt.0) then
           print("nMsg="+nMsg+"  User must preprocess to remove _FillValue")
           print("               FFTs do not allow missing values!!       ")
           exit
       end if
       delete(x@_FillValue)     ; avoid warning messages from fft
   end if

   return(x)

end
