import os
from abc import ABCMeta, abstractmethod
from util import run_command

class NetcdfHelper(object):
    __metaclass__ = ABCMeta

    def __init__(self):
    	pass

    @abstractmethod
    def cat_chunks(self, chunk_list, out_file, working_dir=None):
        pass

    @abstractmethod
    def truncate_time_axis(self, blerg):
        pass 

    @abstractmethod
    def extract_3d_slice(self, blerg):
        pass 

class NcoNetcdfHelper(NetcdfHelper):
	def __init__(self):
		super(NcoNetcdfHelper, self).__init__()
		# check nco exists

	def cat_chunks(self, chunk_list, out_file, working_dir=None):
        if working_dir == None:
        	working_dir = os.getcwd()
		# not running in shell, so can't use glob expansion.
        util.run_command(['ncrcat', '-O'] + chunk_list + [out_file], 
            cwd=working_dir)



class CdoNetcdfHelper(NetcdfHelper):
	pass
