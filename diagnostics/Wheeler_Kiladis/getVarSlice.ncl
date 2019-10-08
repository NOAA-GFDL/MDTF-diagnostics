; This file is part of the Wheeler_Kiladis module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"


undef("getVarSlice")
function getVarSlice( fili[*], varName:string, level:string, latS, latN, lonL, lonR, tstride:integer, i1:integer, i2:integer)
begin


    nfil = dimsizes(fili)
    f    = addfile (fili(0), "r")
    if (isfilevar(f,varName)) then
        if(varName.eq.getenv("omega500_var").and.level.eq."500")
              tmpx  = f->$varName$(i1:i2,{50000},{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:)
              poisson_grid_fill(x,True,1,1000,1e-2,0.6,0)
              delete(tmpx)
        end if
        if(varName.eq.getenv("u200_var").and.level.eq."200")
              tmpx  = f->$varName$(i1:i2,{20000},{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:)
              poisson_grid_fill(x,True,1,1000,1e-2,0.6,0)
              delete(tmpx)
        end if
        if(varName.eq.getenv("u850_var").and.level.eq."850")
              tmpx  = f->$varName$(i1:i2,{85000},{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:)
              poisson_grid_fill(x,True,1,1000,1e-2,0.6,0)
              delete(tmpx)
        end if
        if(varName.eq.getenv("rlut_var"))
              tmpx  = f->$varName$(i1:i2,{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:)
              delete(tmpx)
        end if
        if(varName.eq.getenv("pr_var"))
              tmpx  = f->$varName$(i1:i2,{latS:latN},{lonL:lonR})
              x  = tmpx(::tstride,:,:)
              delete(tmpx)
        end if
    end if
   return(x)

end

