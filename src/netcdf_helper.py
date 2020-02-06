from __future__ import print_function
import os
import shutil
import datelabel
import util
from xml.parsers import expat
import xml.etree.ElementTree as ET

class DisableXmlNamespaces:
    def __enter__(self):
            self.oldcreate = expat.ParserCreate
            expat.ParserCreate = lambda encoding, sep: self.oldcreate(encoding, None)
    def __exit__(self, type, value, traceback):
            expat.ParserCreate = self.oldcreate


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
    def nc_cat_chunks(chunk_list, out_file=None, cwd=None, dry_run=False):
        raise NotImplementedError(
            """NetcdfHelper is a stub defining method signatures for netcdf 
            manipulation wrapper functions, and shouldn't be called directly."""
            )

    @staticmethod
    def nc_crop_time_axis(time_var_name, date_range, 
        in_file=None, out_file=None, cwd=None, dry_run=False):
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



def _nco_outfile_decorator(function):
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
        if 'cwd' not in kwargs:
            kwargs['cwd'] = None
        assert 'in_file' in kwargs
        
        # only pass func the keyword arguments it accepts
        fkwargs = util.filter_kwargs(kwargs, function)
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
    @staticmethod
    def nc_check_environ():
        # check nco exists
        if not util.check_executable('ncks'):
            raise OSError('NCO utilities not found on $PATH.')

    @staticmethod
    def nc_cat_chunks(chunk_list, out_file=None, cwd=None, dry_run=False):
        # not running in shell, so can't use glob expansion.
        util.run_command(['ncrcat', '--no_tmp_fl', '-O'] + chunk_list + [out_file], 
            cwd=cwd, dry_run=dry_run
        )

    @staticmethod
    @_nco_outfile_decorator
    def nc_crop_time_axis(time_var_name, date_range, 
        in_file=None, out_file=None, cwd=None, dry_run=False):
        # don't need to quote time strings in args to ncks because it's not 
        # being called by a shell
        util.run_command(
            ['ncks', '--no_tmp_fl', '-O', '-d', "{},{},{}".format(
                time_var_name, 
                date_range.start.isoformat(),
                date_range.end.isoformat()
            ), in_file, out_file],
            cwd=cwd, dry_run=dry_run
        )

    @staticmethod
    def ncdump_h(in_file=None, cwd=None, dry_run=False):
        """Return header information for all variables in a file.
        """
        d = {'dimensions': dict(), 'variables':dict()}
        if dry_run:
            return d # dummy answer
        # JSON output for -m is malformed in NCO <=4.5.4, verified OK for 4.7.6
        xml_str = util.run_command(
            ['ncks', '--xml', '-m', in_file],
            cwd=cwd, dry_run=dry_run
        )
        with DisableXmlNamespaces():
            root = ET.fromstring('\n'.join(xml_str))  # need parser=None?
        for dim in root.iter('dimension'):
            d['dimensions'][dim.attrib['name']] = int(dim.attrib['length'])
        for var in root.iter('variable'):
            k = var.attrib['name']
            d['variables'][k] = var.attrib.copy()
            del d['variables'][k]['name']
            for att in var:
                if 'name' not in att.attrib or 'value' not in att.attrib:
                    continue
                att_nm = att.attrib['name']
                if att_nm == 'shape':
                    d['variables'][k][att_nm] = att.attrib['value'].split(' ')
                else:
                    d['variables'][k][att_nm] = att.attrib['value']
        return d

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
            util.run_command(
                ['ncap2', '-O', '-s', ''.join(cmds), in_file, out_file],
                cwd=cwd, dry_run=dry_run
            )

    @staticmethod
    def nc_dump_axis(ax_name, in_file=None, cwd=None, dry_run=False):
        # OK for 4.7.6, works on 4.5.4 if "--trd" flag removed
        ax_vals = util.run_command(
            ['ncks','-H','-V','-v', ax_name, in_file],
            cwd=cwd, dry_run=dry_run
        )
        return [float(val) for val in ax_vals if val]

class CdoNetcdfHelper(NetcdfHelper):
    pass