; This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

; FILE: nc_format.ncl
; NCL's name for the netCDF format differs from the framework's, and MDTF v4
; does not export MDTF_NC_FORMAT at all, so passing getenv("MDTF_NC_FORMAT")
; straight to setfileoption gave "FileSetFileOption: invalid value supplied
; for option Format". Map the framework name, defaulting to NetCDF4Classic.

undef("get_ncl_nc_format")
function get_ncl_nc_format()
local nc_format
begin
  nc_format = getenv("MDTF_NC_FORMAT")
  if (ismissing(nc_format)) then
    nc_format = "NetCDF4Classic"
  end if
  if ((nc_format.eq."NetCDF4_Classic").or.(nc_format.eq."NETCDF4_CLASSIC")) then
    nc_format = "NetCDF4Classic"
  end if
  if (nc_format.eq."NETCDF4") then
    nc_format = "NetCDF4"
  end if
  return(nc_format)
end
