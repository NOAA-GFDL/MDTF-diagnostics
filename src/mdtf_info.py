"""'mdtf info' subcommand for online (command-line) help about installed PODs.
"""
import os
import collections
from json import JSONDecodeError
from src import util

import logging
_log = logging.getLogger(__name__)

PodDataTuple = collections.namedtuple(
    'PodDataTuple', 'sorted_pods sorted_realms pod_data realm_data'
)
def load_pod_settings(code_root, pod=None, pod_list=None):
    """Wrapper to load POD settings files, used by ConfigManager and CLIInfoHandler.
    """
    # only place we can put it would be util.py if we want to avoid circular imports
    _pod_dir = 'diagnostics'
    _file_name = 'settings.jsonc'

    def _load_one_json(pod_):
        pod_dir = os.path.join(code_root, _pod_dir, pod_)
        settings_path = os.path.join(pod_dir, _file_name)
        try:
            d = util.read_json(settings_path)
            for section in ['settings', 'varlist']:
                if section not in d:
                    raise AssertionError(f"'{section}' entry not found in '{_file_name}'.")
        except util.MDTFFileNotFoundError as exc:
            if not os.path.isdir(pod_dir):
                raise util.PodConfigError((f"'{pod_}' directory not found in "
                    f"'{os.path.join(code_root, _pod_dir)}'."), pod_)
            elif not os.path.isfile(settings_path):
                raise util.PodConfigError((f"'{_file_name}' file not found in "
                    f"'{pod_dir}'."), pod_)
            else:
                raise exc
        except (JSONDecodeError, AssertionError) as exc:
            raise util.PodConfigError((f"Syntax error in '{_file_name}': "
                f"{str(exc)}."), pod_)
        except Exception as exc:
            raise util.PodConfigError((f"Error encountered in reading '{_file_name}': "
                f"{repr(exc)}."), pod_)
        return d

    # get list of pods
    if not pod_list:
        pod_list = os.listdir(os.path.join(code_root, _pod_dir))
        pod_list = [s for s in pod_list if not s.startswith(('_', '.'))]
        pod_list.sort(key=str.lower)
    if pod == 'list':
        return pod_list

    # load one settings.jsonc file
    if pod is not None:
        if pod not in pod_list:
            print(f"Couldn't recognize '{pod}' out of the following diagnostics:")
            print(', '.join(pod_list))
            return dict()
        return _load_one_json(pod)

    # load all of them
    pods = dict()
    realm_list = set()
    bad_pods = []
    realms = collections.defaultdict(list)
    for p in pod_list:
        try:
            d = _load_one_json(p)
        except Exception as exc:
            _log.error(exc)
            bad_pods.append(p)
            continue
        pods[p] = d
        # PODs requiring data from multiple realms get stored in the dict
        # under a tuple of those realms; realms stored indivudally in realm_list
        _realm = util.to_iter(d['settings'].get('realm', None), tuple)
        if len(_realm) == 0:
            continue
        elif len(_realm) == 1:
            _realm = _realm[0]
            realm_list.add(_realm)
        else:
            realm_list.update(_realm)
        realms[_realm].append(p)
    if bad_pods:
        _log.critical(("Errors were encountered when finding the following PODS: "
            "[%s]."), ', '.join(f"'{p}'" for p in bad_pods))
        util.exit_handler(code=1)
    return PodDataTuple(
        pod_data=pods, realm_data=realms,
        sorted_pods=pod_list,
        sorted_realms=sorted(list(realm_list), key=str.lower)
    )


class InfoCLIHandler(object):
    def __init__(self, code_root, arg_list):
        def _add_topic_handler(keywords, function):
            # keep cmd_list ordered
            keywords = util.to_iter(keywords)
            self.cmd_list.extend(keywords)
            for k in keywords:
                self.cmds[k] = function

        self.code_root = code_root
        pod_info_tuple = load_pod_settings(self.code_root)
        self.pod_list = pod_info_tuple.sorted_pods
        self.realm_list = pod_info_tuple.sorted_realms
        self.pods = pod_info_tuple.pod_data
        self.realms = pod_info_tuple.realm_data

        # build list of recognized topics, in order
        self.cmds = dict()
        self.cmd_list = []
        _add_topic_handler(['diagnostics', 'pods'], self.info_pods_all)
        _add_topic_handler('realms', self.info_realms_all)
        _add_topic_handler(self.realm_list, self.info_realm)
        _add_topic_handler(self.pod_list, self.info_pod)
        # ...

        # dispatch based on topic
        if not arg_list:
            self.info_cmds()
        elif arg_list[0] in self.cmd_list:
            self.cmds[arg_list[0]](arg_list[0])
        else:
            print("ERROR: '{}' not a recognized topic.".format(' '.join(arg_list)))
            self.info_cmds()

    def info_cmds(self):
        print('Recognized topics for `mdtf.py info`:')
        print(', '.join(self.cmd_list))

    def _print_pod_info(self, pod, verbose):
        ds = self.pods[pod]['settings']
        dv = self.pods[pod]['varlist']
        if verbose == 1:
            print('  {}: {}.'.format(pod, ds['long_name']))
        elif verbose == 2:
            print('  {}: {}.'.format(pod, ds['long_name']))
            print('    {}'.format(ds['description']))
            print('    Variables: {}'.format(
                ', '.join([v['var_name'].replace('_var','') for v in dv])
            ))
        elif verbose == 3:
            print('{}: {}.'.format(pod, ds['long_name']))
            print('  Realm: {}.'.format(' and '.join(util.to_iter(ds['realm']))))
            print('  {}'.format(ds['description']))
            print('  Variables:')
            for var in dv:
                var_str = '    {} ({}) @ {} frequency'.format(
                    var['var_name'].replace('_var',''),
                    var.get('requirement',''),
                    var['freq']
                )
                if 'alternates' in var:
                    var_str = var_str + '; alternates: {}'.format(
                        ', '.join([s.replace('_var','') for s in var['alternates']])
                    )
                print(var_str)

    def info_pods_all(self, *args):
        print('List of installed diagnostics:')
        print(('Do `mdtf info <diagnostic>` for more info on a specific diagnostic '
            'or check documentation at github.com/NOAA-GFDL/MDTF-diagnostics.'))
        for pod in self.pod_list:
            self._print_pod_info(pod, verbose=1)

    def info_pod(self, pod):
        self._print_pod_info(pod, verbose=3)

    def info_realms_all(self, *args):
        print('List of installed diagnostics by realm:')
        for realm in self.realms:
            if isinstance(realm, str):
                print('{}:'.format(realm))
            else:
                # tuple of multiple realms
                print('{}:'.format(' and '.join(realm)))
            for pod in self.realms[realm]:
                self._print_pod_info(pod, verbose=1)

    def info_realm(self, realm):
        print('List of installed diagnostics for {}:'.format(realm))
        for pod in self.realms[realm]:
            self._print_pod_info(pod, verbose=2)
