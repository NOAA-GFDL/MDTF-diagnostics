from __future__ import print_function
import os
import sys
import shutil
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
import datelabel
import util
import util_mdtf
import StringIO
import xml.etree.ElementTree as ET

class NetcdfHelper(object):
    def __init__(self):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @classmethod
    def nc_check_environ(cls):
        pass

    @classmethod
    def nc_cat_chunks(cls, chunk_list, out_file=None, cwd=None, dry_run=False):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @classmethod
    def nc_crop_time_axis(cls, time_var_name, date_range, 
        in_file=None, out_file=None, cwd=None, dry_run=False):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @classmethod
    def nc_extract_level(cls):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @classmethod
    def ncdump_h(cls, in_file=None, cwd=None, dry_run=False):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )
            
    @classmethod
    def nc_get_attribute(cls, attr_name, in_file=None, cwd=None, dry_run=False):
        """Return dict of variables and values of a given attribute.
        
        If the attribute is not defined for the variable (or is the empty string), 
        it's not included in the returned dict.
        """
        d = cls.ncdump_h(in_file=in_file, cwd=cwd, dry_run=dry_run)
        dd = dict()
        for var in d['variables']:
            if d['variables'][var].get(attr_name, None):
                dd[var] = d['variables'][var][attr_name]
        return dd

    @classmethod
    def nc_get_axes_attributes(cls, var, in_file=None, cwd=None, dry_run=False):
        """Return variable names corresponding to an axis attribute.
        """
        d = cls.ncdump_h(in_file=in_file, cwd=cwd, dry_run=dry_run)
        dd = dict()
        if var not in d['variables']:
            print("Can't find variable {} in {}.".format(var, in_file))
            return dd
        if 'shape' not in d['variables'][var]:
            print("Can't find shape attribute for {} in {}.".format(var, in_file))
            return dd
        for ax in d['variables'][var]['shape']:
            assert ax in d['variables']
            dd[ax] = d['variables'][ax].copy() # copy dict of all attributes
        return dd


def _nco_outfile_decorator(function):
    """Wrapper handling cleanup for NCO operations that modify files.
    NB must come between classmethod and base function definition.
    See https://stackoverflow.com/a/18732038. 
    """
    def wrapper(*args, **kwargs):
        if 'out_file' not in kwargs or kwargs['out_file'] is None:
            kwargs['out_file'] = 'MDTF_NCO_temp.nc'
            move_back = True
        else:
            move_back = False
        if 'cwd' not in kwargs:
            kwargs['cwd'] = None
        if 'in_file' not in kwargs:
            print("nchelper didn't get in_file: {}".format(kwargs))
            raise AssertionError()
        
        # only pass func the keyword arguments it accepts
        named_args = function.func_code.co_varnames
        fkwargs = dict((k, kwargs[k]) for k in named_args if k in kwargs)
        result = function(*args, **fkwargs)
        
        if move_back:
            # manually move file back 
            if kwargs.get('dry_run', False):
                print('DRY_RUN: move {} to {}'.format(
                    kwargs['out_file'], kwargs['in_file']))
            else:
                if kwargs['cwd']:
                    cwd = os.getcwd()
                    os.chdir(kwargs['cwd'])
                os.remove(kwargs['in_file'])
                shutil.move(kwargs['out_file'], kwargs['in_file'])
                if kwargs['cwd']:
                    os.chdir(cwd)
        return result
    return wrapper

class NcoNetcdfHelper(NetcdfHelper):
    # Just calls command-line utilities, doesn't use PyNCO bindings

    _run_command = staticmethod(util.run_command)

    @classmethod
    def nc_check_environ(cls):
        # check nco exists
        if not util.check_executable('ncks'):
            raise OSError('NCO utilities not found on $PATH.')

    @classmethod
    def nc_cat_chunks(cls, chunk_list, out_file=None, cwd=None, dry_run=False):
        # not running in shell, so can't use glob expansion.
        cls._run_command(['ncrcat', '-O'] + chunk_list + [out_file], 
            cwd=cwd, dry_run=dry_run
        )

    @classmethod
    @_nco_outfile_decorator
    def nc_crop_time_axis(cls, time_var_name, date_range, 
        in_file=None, out_file=None, cwd=None, dry_run=False):
        # don't need to quote time strings in args to ncks because it's not 
        # being called by a shell
        cls._run_command(
            ['ncks', '-O', '-d', "{},{},{}".format(
                time_var_name, 
                date_range.start.isoformat(),
                date_range.end.isoformat()
            ), in_file, out_file],
            cwd=cwd, dry_run=dry_run
        )

    @classmethod
    def ncdump_h(cls, in_file=None, cwd=None, dry_run=False):
        """Return header information for all variables in a file.
        """
        def _parse_xml_wrapper(str_):
            # strips namespaces; https://stackoverflow.com/a/25920989
            # https://stackoverflow.com/a/53738357 would be more robust, but for
            # some reason I can't reproduce it
            f_obj = StringIO.StringIO(str_)
            it = ET.iterparse(f_obj)
            for _, el in it:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
                for at in el.attrib.keys(): # strip namespaces of attributes too
                    if '}' in at:
                        newat = at.split('}', 1)[1]
                        el.attrib[newat] = el.attrib[at]
                        del el.attrib[at]
            return it.root

        d = {'dimensions': dict(), 'variables':dict()}
        if dry_run:
            return d # dummy answer
        # JSON output for -m is malformed in NCO <=4.5.4, verified OK for 4.7.6
        xml_str = util.run_command(
            ['ncks', '--xml', '-m', in_file],
            cwd=cwd, dry_run=dry_run
        )
        root = _parse_xml_wrapper('\n'.join(xml_str))
        for dim in root.iter('dimension'):
            d['dimensions'][dim.attrib['name']] = int(dim.attrib['length'])
        dv = d['variables']
        for var in root.iter('variable'):
            k = var.attrib['name']
            dv[k] = var.attrib.copy()
            del dv[k]['name']
            for att in var:
                if 'name' not in att.attrib or 'value' not in att.attrib:
                    continue
                dv[k][att.attrib['name']] = att.attrib['value']
            if dv[k].get('shape', None):
                dv[k]['shape'] = dv[k]['shape'].split(' ')
        return d

    @classmethod
    @_nco_outfile_decorator
    def nc_change_variable_units(cls, new_units_dict,
        in_file=None, out_file=None, cwd=None, dry_run=False):
        """Unit conversion of several variables in a file.

        See http://nco.sourceforge.net/nco.html#UDUnits-script. Requires
        NCO > 4.6.3.
        """
        # ncap2 errors if var doesn't have a units attribute, and will do 
        # processing even if new units are the same as old, so filter these 
        # cases out first.
        d = cls.nc_get_attribute('units', in_file=in_file, cwd=cwd, dry_run=dry_run)
        dd = dict()
        for var, unit in new_units_dict.iteritems():
            if var not in d:
                print(("Warning: no unit attribute for {} in {}."
                    " Skipping unit conversion").format(var, in_file))
            elif d[var] != unit:
                dd[var] = unit
        cmd_string = '{var}=udunits({var},"{unit}");{var}@units="{unit}";'
        cmds = [cmd_string.format(var=k, unit=v) for k,v in dd.iteritems()]
        if cmds:
            cls._run_command(
                ['ncap2', '-O', '-s', ''.join(cmds), in_file, out_file],
                cwd=cwd, dry_run=dry_run
            )

    @classmethod
    def nc_dump_axis(cls, ax_name, in_file=None, cwd=None, dry_run=False):
        # OK for 4.7.6, works on 4.5.4 if "--trd" flag removed
        ax_vals = util.run_shell_command(
            "ncks --trd -H -V -v '{}' {}".format(ax_name, in_file),
            cwd=cwd, dry_run=dry_run
        )
        return [float(val) for val in ax_vals if val]


class CdoNetcdfHelper(NetcdfHelper):
    pass