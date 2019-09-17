import os
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except (ImportError, ModuleNotFoundError):
        import subprocess
else:
    import subprocess
from util import Singleton
from environment_manager import VirtualenvEnvironmentManager, CondaEnvironmentManager


class ModuleManager(Singleton):
    def __init__(self):
        if 'MODULESHOME' not in os.environ:
            # could set from module --version
            raise OSError('Unable to determine how modules are handled on this host.')

        self.user_modules = self._module(['list'])
        self.modules_i_loaded = set()

    def _module(*args):
        # based on $MODULESHOME/init/python.py
        if type(args[0]) == type([]):
            args = args[0]
        else:
            args = list(args)
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        (output, error) = subprocess.Popen(
            [cmd, 'python'] + args, stdout=subprocess.PIPE
        ).communicate()
        exec output

    def load(self, module_name):
        """Wrapper for module load.
        """
        self.modules_i_loaded.add(module_name)
        self._module(['load', module_name])

    def unload(self, module_name):
        """Wrapper for module unload.
        """
        self.modules_i_loaded.discard(module_name)
        self._module(['unload', module_name])
    
    def unload_all(self):
        mods_to_unload = self.modules_i_loaded.difference(self.user_modules)
        for mod in mods_to_unload:
            self._module(['unload', mod])
        # User's modules may have been unloaded if we loaded a different version
        for mod in self.user_modules:
            self._module(['load'], mod)


class GfdlvirtualenvEnvironmentManager(VirtualenvEnvironmentManager):
    # Use module files to switch execution environments, as defined on 
    # GFDL workstations and PP/AN cluster.

    def __init__(self, config, verbose=0):
        modMgr = ModuleManager()
        self.interpreter_modules = {
            'python': 'python/2.7.12',
            'ncl': 'ncarg/6.5.0',
            'r': 'R/3.4.4'
        }
        super(GfdlvirtualenvEnvironmentManager, self).__init__(config, verbose)

    def create_environment(self, env_name):
        modMgr = ModuleManager()
        modMgr.load(self.interpreter_modules[env_name])
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_command(self, pod):
        mod_name = self.interpreter_modules[pod.env]
        parent_cmd = super(GfdlvirtualenvEnvironmentManager, \
            self).activate_env_command(pod)
        return 'module load {} && {}'.format(mod_name, parent_cmd)

    def deactivate_env_command(self, pod):
        mod_name = self.interpreter_modules[pod.env]
        parent_cmd = super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_command(pod)
        return '{} && module unload {}'.format(parent_cmd, mod_name)

    def tearDown(self):
        super(GfdlvirtualenvEnvironmentManager, self).tearDown()
        modMgr = ModuleManager()
        modMgr.unload_all()


class GfdlcondaEnvironmentManager(CondaEnvironmentManager):
    # Use module files to switch execution environments, as defined on 
    # GFDL workstations and PP/AN cluster.

    def __init__(self, config, verbose=0):
        modMgr = ModuleManager()
        modMgr.load('anaconda2/5.1')
        super(GfdlcondaEnvironmentManager, self).__init__(config, verbose)

    def tearDown(self):
        super(GfdlcondaEnvironmentManager, self).tearDown()
        modMgr = ModuleManager()
        modMgr.unload_all()