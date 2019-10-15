import os
import datelabel
from util import run_command, check_executable

class NetcdfHelper(object):
    def __init__(self):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @staticmethod
    def nc_check_environ():
        pass

    @staticmethod
    def nc_cat_chunks(chunk_list, out_file, working_dir=None):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @staticmethod
    def nc_crop_time_axis(time_var_name, date_range, in_file, 
        out_file=None, working_dir=None):   
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @staticmethod
    def nc_extract_level():
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )


class NcoNetcdfHelper(NetcdfHelper):
    # Just calls command-line utilities, doesn't use PyNCO bindings
    @staticmethod
    def nc_check_environ():
        # check nco exists
        if not check_executable('ncks'):
            raise OSError('NCO utilities not found on $PATH.')

    @staticmethod
    def nc_cat_chunks(chunk_list, out_file, working_dir=None):
        if working_dir is None:
            working_dir = os.getcwd()
        # not running in shell, so can't use glob expansion.
        run_command(['ncrcat', '-O'] + chunk_list + [out_file], 
            cwd=working_dir)

    @staticmethod
    def nc_crop_time_axis(time_var_name, date_range, in_file, 
        out_file=None, working_dir=None):
        if out_file is None:
            # NCO v4.0.3 seems to handle overwriting existing file in-place OK
            # assume internally it's writing to temp file and moving that, so
            # we don't have to do it manually
            out_file = in_file
        if working_dir is None:
            working_dir = os.getcwd()
        ncks_time_format = '%Y-%m-%d %H:%M:%S'
        run_command(
            ['ncks', '-O', '-d', "{},'{}','{}'".format(
                time_var_name, 
                date_range.start.strftime(ncks_time_format),
                date_range.end.strftime(ncks_time_format)
            ), in_file, out_file],
            cwd=working_dir)


class CdoNetcdfHelper(NetcdfHelper):
    pass