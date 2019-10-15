import os
from abc import ABCMeta, abstractmethod, abstractproperty
from types import FunctionType
import datelabel
from util import run_command, check_executable

class abstractstatic(staticmethod):
    """Mark static methods as abstract, since we can't combine the decorators in
    python < 3.3.

    Source: https://stackoverflow.com/a/4474495
    """
    __slots__ = ()
    def __init__(self, function):
        super(abstractstatic, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True

class ABCMetaTypeCheck(ABCMeta):
    """Throw error if child classes try to implement abstract methods with
    methods of the wrong type. Unfortunately there doesn't seem to be a way
    to check if the child's method has the same signature as parent, which is
    what we really want.

    Source: https://stackoverflow.com/q/29455660
    """
    _typemap = {  # map abstract type to expected implementation type
        abstractproperty: property,
        abstractstatic: staticmethod,
        # abstractmethods return function objects
        FunctionType: FunctionType,
    }
    def __new__(mcls, name, bases, namespace):
        cls = super(ABCMetaTypeCheck, mcls).__new__(mcls, name, bases, namespace)
        wrong_type = set()
        seen = set()
        abstractmethods = cls.__abstractmethods__
        for base in bases:
            for name in getattr(base, "__abstractmethods__", set()):
                if name in seen or name in abstractmethods:
                    continue  # still abstract or later overridden
                value = base.__dict__.get(name)  # bypass descriptors
                if getattr(value, "__isabstractmethod__", False):
                    seen.add(name)
                    expected = mcls._typemap[type(value)]
                    if not isinstance(namespace[name], expected):
                        wrong_type.add(name)
        if wrong_type:
            cls.__abstractmethods__ = abstractmethods | frozenset(wrong_type)
        return cls

class NetcdfHelper(object):
    __metaclass__ = ABCMetaTypeCheck

    def __init__(self):
    	pass

    @abstractstatic
    def cat_chunks(chunk_list, out_file, working_dir=None):
        pass

    @abstractstatic
    def crop_time_axis(time_var_name, date_range, in_file, 
        out_file=None, working_dir=None):
        pass 

    @abstractstatic
    def extract_3d_slice():
        pass 



class NcoNetcdfHelper(NetcdfHelper):
    # Just calls command-line utilities, doesn't use PyNCO bindings
	def __init__(self):
		# check nco exists
        if not check_executable('ncks'):
            raise OSError('NCO utilities not found on $PATH.')
		super(NcoNetcdfHelper, self).__init__()

    @staticmethod
	def cat_chunks(chunk_list, out_file, working_dir=None):
        if working_dir is None:
            working_dir = os.getcwd()
		# not running in shell, so can't use glob expansion.
        util.run_command(['ncrcat', '-O'] + chunk_list + [out_file], 
            cwd=working_dir)

    @staticmethod
    def crop_time_axis(time_var_name, date_range, in_file, 
        out_file=None, working_dir=None):
        if out_file is None:
            # NCO v4.0.3 seems to handle overwriting existing file in-place OK
            # assume internally it's writing to temp file and moving that, so
            # we don't have to do it manually
            out_file = in_file
        if working_dir is None:
            working_dir = os.getcwd()
        ncks_time_format = '%Y-%m-%d %H:%M:%S'
        util.run_command(
            ['ncks', '-O', '-d', "{},'{}','{}'".format(
                time_var_name, 
                date_range.start.strftime(ncks_time_format),
                date_range.end.strftime(ncks_time_format)
            ), in_file, out_file],
            cwd=working_dir)

    @staticmethod
    def extract_3d_slice():
        raise NotImplementedError 


class CdoNetcdfHelper(NetcdfHelper):
	def __init__(self):
        raise NotImplementedError

    @staticmethod
	def cat_chunks(chunk_list, out_file, working_dir=None):
        raise NotImplementedError 

    @staticmethod
    def crop_time_axis(time_var_name, date_range, in_file, 
        out_file=None, working_dir=None):
        raise NotImplementedError 

    @staticmethod
    def extract_3d_slice():
        raise NotImplementedError 