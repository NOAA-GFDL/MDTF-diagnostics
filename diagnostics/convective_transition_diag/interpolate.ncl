load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
begin

    datadir = getenv("DATADIR")
    casename = getenv("CASENAME")
    ;datadir = "/archive/wnd/MDTF-GFDL/inputdata/model/CM4_historical"
    ;casename = "CM4_historical"
    varname = (/"ta","hus","prw"/)
    do i=1,1;dimsizes(varname)-1
    filein  = datadir+"/day/"+casename+"."+varname(i)+".day.nc"
    fileout = datadir+"/1hr/"+casename+"."+varname(i)+".1hr.nc"
    if (fileexists(filein)) then
    f = addfile(filein,"r")
    time = cd_calendar(f->time,0)
    YMD = time(0,0)+"-0"+time(0,1)+"-0"+time(0,2)
    HMS = time(0,3)+":0"+time(0,4)+":0"+time(0,5)
    CDO = "cdo inttime,"+YMD+","+HMS+",1hour "+filein+" "+fileout
    print(CDO)
    system(CDO)
    delete(f)
    delete(time)
    delete(YMD)
    delete(HMS)
    delete(CDO)
    else 
        print("File not exists!")
    end if 
    delete(filein)
    delete(fileout)
    end do
end
