import os
import shutil
import datelabel
import util

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
    def nc_cat_chunks(chunk_list, out_file, working_dir=None, dry_run=False):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @staticmethod
    def nc_crop_time_axis(time_var_name, date_range, in_file, 
        out_file=None, working_dir=None, dry_run=False):   
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

    def _outfile_decorator(function):
        """Wrapper handling cleanup for NCO operations that modify files.
        NB must come between staticmethod and base function definition.
        See https://stackoverflow.com/a/18732038. 
        """
        def wrapper(*args, **kwargs):
            if 'out_file' not in kwargs or kwargs['out_file'] is None:
                kwargs['out_file'] = 'MDTF_NCO_temp.nc'
                move_back = True
            else:
                move_back = False
            if 'working_dir' not in kwargs or kwargs['working_dir'] is None:
                kwargs['working_dir'] = os.getcwd()
            assert 'in_file' in kwargs
            
            # only pass func the arguments it accepts
            named_args = function.func_code.co_varnames
            fkwargs = dict((k, kwargs[k]) for k in named_args if k in kwargs)
            result = function(*args, **fkwargs)
            
            if move_back:
                # manually move file back 
                if kwargs.get('dry_run', False):
                    print 'DRY_RUN: move {} to {}'.format(
                        kwargs['out_file'], kwargs['in_file'])
                else:
                    cwd = os.getcwd()
                    os.chdir(kwargs['working_dir'])
                    os.remove(kwargs['in_file'])
                    shutil.move(kwargs['out_file'], kwargs['in_file'])
                    os.chdir(cwd)
            return result
        return wrapper

    @staticmethod
    def nc_check_environ():
        # check nco exists
        if not util.check_executable('ncks'):
            raise OSError('NCO utilities not found on $PATH.')

    @staticmethod
    def nc_cat_chunks(chunk_list, out_file, working_dir=None, dry_run=False):
        if working_dir is None:
            working_dir = os.getcwd()
        # not running in shell, so can't use glob expansion.
        util.run_command(['ncrcat', '--no_tmp_fl', '-O'] + chunk_list + [out_file], 
            cwd=working_dir, 
            dry_run=dry_run
        )

    @staticmethod
    @_outfile_decorator
    def nc_crop_time_axis(time_var_name, date_range, 
        in_file=None, out_file=None, working_dir=None, dry_run=False):
        # don't need to quote time strings in args to ncks because it's not 
        # being called by a shell
        util.run_command(
            ['ncks', '--no_tmp_fl', '-O', '-d', "{},{},{}".format(
                time_var_name, 
                date_range.start.isoformat(),
                date_range.end.isoformat()
            ), in_file, out_file],
            cwd=working_dir, 
            dry_run=dry_run
        )

    @staticmethod
    def ncdump_h(in_file, dry_run=False):
        # JSON output for -m is malformed in NCO <=4.5.4, verified OK for 4.7.6
        json_str = util.run_command(
            ['ncks', '--jsn', '-m', in_file],
            dry_run=dry_run
        )
        if dry_run:
            # dummy answer
            return {'dimensions': dict(), 'variables':dict()}
        else:
            return util.parse_json('\n'.join(json_str))

class CdoNetcdfHelper(NetcdfHelper):
    pass