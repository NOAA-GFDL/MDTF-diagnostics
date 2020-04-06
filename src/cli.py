from __future__ import print_function
import os
import sys
import argparse
from ConfigParser import _Chainmap as ChainMap # in collections in py3
import shlex
import collections
import util

class CustomHelpFormatter(
        argparse.RawDescriptionHelpFormatter, 
        argparse.ArgumentDefaultsHelpFormatter
    ):
    """Modify help text formatter to only display variable placeholder 
    ("metavar") once, to save space. Taken from 
    https://stackoverflow.com/a/16969505 . Also inherit from 
    RawDescriptionHelpFormatter in order to preserve line breaks in description
    only (https://stackoverflow.com/a/18462760).
    """
    def __init__(self, *args, **kwargs):
        # tweak indentation of help strings
        if not kwargs.get('indent_increment', None):
            kwargs['indent_increment'] = 2
        if not kwargs.get('max_help_position', None):
            kwargs['max_help_position'] = 6
        super(CustomHelpFormatter, self).__init__(*args, **kwargs)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                # if the Optional doesn't take a value, format is: "-s, --long"
                parts.extend(action.option_strings)
            else:
                # if the Optional takes a value, format is: "-s ARGS, --long ARGS"
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                ## NEW CODE:
                if args_string[0].isalpha():
                    args_string = '<' + args_string + '>'
                parts.extend(action.option_strings)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)


class RecordDefaultsAction(argparse.Action):
    """Add boolean to record if user actually set argument's value, or if we're
    using the specified default. From https://stackoverflow.com/a/50936474. This
    also re-implements the 'store_true' and 'store_false' actions, in order to 
    give defaults information on boolean flags.
    """
    flag_suffix = '_is_default_'

    def __init__(self, option_strings, dest, nargs=None, const=None, 
        default=None, required=False, **kwargs):
        assert default is not None
        required = False
        if isinstance(default, bool):
            nargs = 0             # behave like a flag
            const = (not default) # set flag = store opposite of default
        elif isinstance(default, basestring) and nargs is None:
            # unless explicitly specified, string-valued options accept 1 argument
            nargs = 1
            const = None
        super(RecordDefaultsAction, self).__init__(
            option_strings=option_strings, dest=dest, nargs=nargs, const=const,
            default=default, required=required, **kwargs
        )

    def __call__(self, parser, namespace, values, option_string=None):
        if self.nargs == 0 and self.const is not None:
            setattr(namespace, self.dest, self.const)
        elif self.nargs == 1:
            setattr(namespace, self.dest, util.coerce_from_iter(values))
        else:
            setattr(namespace, self.dest, values)
        # set flag to indicate user has set this argument
        setattr(namespace, self.dest+self.flag_suffix, False)


class CLIHandler(object):
    def __init__(self, code_root, defaults_rel_path):
        self.code_root = code_root
        defaults_path = os.path.join(code_root, defaults_rel_path)
        defaults = util.read_json(defaults_path)
        self.config = dict()
        self.parser_groups = dict()
        # no way to get this from public interface? _actions of group
        # contains all actions for entire parser
        self.parser_args_from_group = collections.defaultdict(list)
        # manually track args requiring custom postprocessing (even if default
        # is used, so can't do with action=.. in argument)
        self.custom_types = collections.defaultdict(list)
        self.parser = self.make_parser(defaults)

    def iter_cli_actions(self):
        for arg_gp in self.parser_args_from_group:
            for arg in self.parser_args_from_group[arg_gp]:
                yield arg

    def iteritems_cli(self, group_nm=None):
        if not group_nm:
            _groups = self.parser_groups
        else:
            _groups = util.coerce_to_iter(group_nm)
        for group in _groups:
            for action in self.parser_args_from_group[group]:
                key = action.dest
                yield (key, self.config[key])

    @staticmethod
    def _append_to_entry(d, key, str_):
        if key in d:
            d[key] = d[key] + '\n' + str_
        else:
            d[key] = str_

    def make_parser(self, d):
        args = util.coerce_to_iter(d.pop('arguments', None))
        arg_groups = util.coerce_to_iter(d.pop('argument_groups', None))
        d['formatter_class'] = CustomHelpFormatter
        p_kwargs = util.filter_kwargs(d, argparse.ArgumentParser.__init__)
        p = argparse.ArgumentParser(**p_kwargs)
        for arg in args:
            # add arguments not in any group
            self.add_parser_argument(arg, p, 'parser')
        for group in arg_groups:
            # add groups and arguments therein
            self.add_parser_group(group, p)
        return p

    def add_parser_group(self, d, target_obj):
        gp_nm = d.pop('name')
        if 'title' not in d:
            d['title'] = gp_nm
        args = util.coerce_to_iter(d.pop('arguments', None))
        gp_kwargs = util.filter_kwargs(d, argparse._ArgumentGroup.__init__)
        gp_obj = target_obj.add_argument_group(**gp_kwargs)
        self.parser_groups[gp_nm] = gp_obj
        for arg in args:
            self.add_parser_argument(arg, gp_obj, gp_nm)
    
    @staticmethod
    def canonical_arg_name(str_):
        # convert flag or other specification to destination variable name
        # canonical identifier/destination always has _s, no -s (PEP8)
        return str_.lstrip('-').rstrip().replace('-', '_')

    def add_parser_argument(self, d, target_obj, target_name):
        # set flags:
        arg_nm = self.canonical_arg_name(d.pop('name'))
        assert arg_nm, "No argument name found in {}".format(d)
        arg_flags = [arg_nm]
        if d.pop('is_positional', False):
            # code to handle positional arguments
            pass
        else:
            # argument is a command-line flag (default)
            if 'dest' not in d:
                d['dest'] = arg_nm
            if '_' in arg_nm:
                # recognize both --hyphen_opt and --hyphen-opt (GNU CLI convention)
                arg_flags = [arg_nm.replace('_', '-'), arg_nm]
            arg_flags = ['--'+s for s in arg_flags]
            if 'short_name' in d:
                # recognize both --option and -O, if short_name defined
                arg_flags.append('-' + d.pop('short_name'))

        # type conversion of default value
        if 'type' in d:
            d['type'] = eval(d['type'])
            if 'default' in d:
                d['default'] = d['type'](d['default'])
        if d.get('action', '') == 'count' and 'default' in d:
            d['default'] = int(d['default'])
        if d.get('parse_type', None):
            # make list of args requiring custom post-parsing later
            self.custom_types[d.pop('parse_type')].append(d['dest'])
        # TODO: what if following require env vars, etc??
        if d.get('eval', None):
            for attr in util.coerce_to_iter(d.pop('eval')):
                if attr in d:
                    d[attr] = eval(d[attr])

        # set more technical argparse options based on default value
        if 'default' in d and 'action' not in d:
            d['action'] = RecordDefaultsAction

        # change help string based on default value
        if d.pop('hidden', False):
            # do not list argument in "mdtf --help", but recognize it
            d['help'] = argparse.SUPPRESS

        # d = util.filter_kwargs(d, argparse.ArgumentParser.add_argument)
        self.parser_args_from_group[target_name].append(
            target_obj.add_argument(*arg_flags, **d)
        )

    def edit_defaults(self, **kwargs):
        # Change default value of arguments. If a key doesn't correspond to an
        # argument previously added, its value is still returned when parse_args()
        # is called.
        self.parser.set_defaults(**kwargs)
        
    def parse_cli(self, args=None):
        # default will parse sys.argv[1:]
        if isinstance(args, basestring):
            args = shlex.split(args, posix=True)
        self.config = vars(self.parser.parse_args(args))

        # set flag for arguments that were left as default values
        self.is_default = dict()
        for arg in self.iter_cli_actions():
            if isinstance(arg, RecordDefaultsAction):
                flag_name = arg.dest + arg.flag_suffix
                if flag_name in self.config:
                    del self.config[flag_name]
                    self.is_default[arg.dest] = False
                else:
                    self.is_default[arg.dest] = True
            else:
                self.is_default[arg.dest] = None


class FrameworkCLIHandler(CLIHandler):
    def __init__(self, code_root, cli_rel_path):
        self.code_root = code_root
        cli_config = util.read_json(os.path.join(code_root, cli_rel_path))
        self.case_list = cli_config.pop('case_list', [])
        self.pod_list = cli_config.pop('pod_list', [])
        self.config = dict()
        self.parser_groups = dict()
        self.parser_args_from_group = collections.defaultdict(list)
        self.custom_types = collections.defaultdict(list)
        self.parser = self.make_default_parser(cli_config, cli_rel_path)

    def make_default_parser(self, d, config_path):
        # add more standard options to top-level parser
        _ = d.setdefault(
            'usage',
            ("%(prog)s [options] [INPUT_FILE] [CASE_ROOT_DIR]\n"
                "{}%(prog)s info [TOPIC]").format(len('usage: ')*' ')
        )
        return self.make_parser(d)

    def make_parser(self, d):
        # used for defaults (above) and if we're passed a config file via the CLI
        # (file_opts, below)
        p = super(FrameworkCLIHandler, self).make_parser(d)
        p._positionals.title = None
        p._optionals.title = 'GENERAL OPTIONS'
        return p

    def parse_positionals(self, var_name):
        _ = self.config.setdefault('INPUT_FILE', None)
        _ = self.config.setdefault('CASE_ROOT_DIR', None)

        var_val = self.config.pop(var_name, None)
        if var_val is None:
            # maybe it was set with flag
            var_val = self.config.pop('flag_'+var_name, None)
        if var_val is None:
            return
        is_file = os.path.isfile(var_val)
        is_dir = os.path.isdir(var_val)
        if not is_file and not is_dir:
            print("Error: couldn't locate {}".format(var_val))
            exit()
        elif is_file:
            if self.config['INPUT_FILE'] is not None:
                print(("Error: trying to set INPUT_FILE twice (got "
                    "'{}', '{}')").format(self.config['INPUT_FILE'], var_val))
                exit()
            else:
                self.config['INPUT_FILE'] = var_val
        elif is_dir:
            if self.config['CASE_ROOT_DIR'] is not None:
                print(("Error: trying to set CASE_ROOT_DIR twice (got "
                    "'{}', '{}')").format(self.config['CASE_ROOT_DIR'], var_val))
                exit()
            else:
                self.config['CASE_ROOT_DIR'] = var_val

    def parse_cli(self, args=None):
        # explicitly set cmd-line options, parsed according to default parser;
        # result stored in self.config
        super(FrameworkCLIHandler, self).parse_cli(args)

        # handle positionals here because we need to find input_file
        self.parse_positionals('input_file')
        self.parse_positionals('root_dir')

        cli_opts = self.config
        # defaults from cli.jsonc, from running default parser on empty input
        cli_base = vars(self.parser.parse_args([]))
        chained_dict_list = [cli_opts, cli_base]

        # deal with options set in user-specified defaults file, if present
        config_path = cli_opts.get('INPUT_FILE', None)
        file_str = ''
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    file_str = f.read()
            except Exception:
                print("ERROR: Can't read input file at {}.".format(config_path))
        if file_str:
            try:
                defaults = util.parse_json(file_str)
                # overwrite default case_list and pod_list, if given
                if 'case_list' in defaults:
                    self.case_list = defaults.pop('case_list')
                if 'pod_list' in defaults:
                    self.pod_list = defaults.pop('pod_list')
                # assume config_file a JSON dict of option:value pairs.
                defaults = {
                    self.canonical_arg_name(k): v for k,v in defaults.iteritems()
                }
                chained_dict_list = [cli_opts, defaults, cli_base]
            except Exception:
                if 'json' in os.path.splitext('config_path')[1].lower():
                    print("ERROR: Couldn't parse JSON in {}.".format(config_path))
                    raise
                # assume config_file is a plain text file containing flags, etc.
                # as they would be passed on the command line.
                file_str = util.strip_comments(file_str, '#')
                defaults = vars(self.parser.parse_args(shlex.split(file_str)))
                chained_dict_list = [cli_opts, defaults, cli_base]

        # CLI opts override options set from file, which override defaults
        self.config = dict(ChainMap(*chained_dict_list))


PodDataTuple = collections.namedtuple(
    'PodDataTuple', 'sorted_lists pod_data realm_data'
)
def load_pod_settings(code_root, pod=None, pod_list=None):
    """Wrapper to load POD settings files, used by ConfigManager and CLIInfoHandler.
    """
    # only place we can put it would be util.py if we want to avoid circular imports
    _pod_dir = 'diagnostics'
    _pod_settings = 'settings.jsonc'
    def _load_one_json(pod):
        d = dict()
        try:
            d = util.read_json(
                os.path.join(code_root, _pod_dir, pod, _pod_settings)
            )
            assert 'settings' in d
        except Exception:
            pass # better error handling?
        return d

    # get list of pods
    if not pod_list:
        pod_list = os.listdir(os.path.join(code_root, _pod_dir))
        pod_list = [s for s in pod_list if not s.startswith(('_','.'))]
        pod_list.sort(key=str.lower)
    if pod == 'list':
        return pod_list

    # load JSON files
    if not pod:
        # load all of them
        pods = dict()
        realm_list = set()
        bad_pods = []
        realms = collections.defaultdict(list)
        for p in pod_list:
            d = _load_one_json(p)
            if not d:
                bad_pods.append(p)
                continue
            pods[p] = d
            # PODs requiring data from multiple realms get stored in the dict
            # under a tuple of those realms; realms stored indivudally in realm_list
            _realm = util.coerce_to_iter(d['settings'].get('realm', None), tuple)
            if len(_realm) == 0:
                continue
            elif len(_realm) == 1:
                _realm = _realm[0]
                realm_list.add(_realm)
            else:
                realm_list.update(_realm)
            realms[_realm].append(p)
        for p in bad_pods:
            pod_list.remove(p)
        return PodDataTuple(
            pod_data=pods, realm_data=realms,
            sorted_lists={
                "pods": pod_list,
                "realms": sorted(list(realm_list), key=str.lower)
            }
        )
    else:
        if pod not in pod_list:
            print("Couldn't recognize POD {} out of the following diagnostics:".format(pod))
            print(', '.join(pod_list))
            return dict()
        return _load_one_json(pod)


class InfoCLIHandler(object):
    def __init__(self, code_root, arg_list):
        def _add_topic_handler(keywords, function):
            # keep cmd_list ordered
            keywords = util.coerce_to_iter(keywords)
            self.cmd_list.extend(keywords)
            for k in keywords:
                self.cmds[k] = function

        self.code_root = code_root
        pod_info_tuple = load_pod_settings(self.code_root)
        self.pod_list = pod_info_tuple.sorted_lists.get('pods', [])
        self.pods = pod_info_tuple.pod_data
        self.realm_list = pod_info_tuple.sorted_lists.get('realms', [])
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
        # displayed info, now exit
        exit()

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
            print('  Realm: {}.'.format(' and '.join(util.coerce_to_iter(ds['realm']))))
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
            if isinstance(realm, basestring):
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


