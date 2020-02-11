from __future__ import print_function
import os
import sys
import argparse
from ConfigParser import _Chainmap as ChainMap # in collections in py3
import shlex
import collections
import util

class SingleMetavarHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Modify help text formatter to only display variable placeholder 
    ("metavar") once, to save space. 
    Taken from https://stackoverflow.com/a/16969505
    """
    def __init__(self, *args, **kwargs):
        # tweak indentation of help strings
        if not kwargs.get('indent_increment', None):
            kwargs['indent_increment'] = 2
        if not kwargs.get('max_help_position', None):
            kwargs['max_help_position'] = 10
        super(SingleMetavarHelpFormatter, self).__init__(*args, **kwargs)

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
        self.parser = self.make_parser(defaults)

    def iter_cli_actions(self):
        for arg_list in self.parser_args_from_group:
            for arg in arg_list:
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
        d['formatter_class'] = SingleMetavarHelpFormatter
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
        # TODO: what if following require env vars, etc??
        if d.pop('eval', None):
            for attr in util.coerce_to_iter(d['eval']):
                if attr in d:
                    d[attr] = eval(d[attr])

        # set more technical argparse options based on default value
        if 'default' in d:
            if isinstance(d['default'], basestring) and 'nargs' not in d:
                # unless explicitly specified, 
                # string-valued options accept 1 argument
                d['nargs'] = 1
            elif isinstance(d['default'], bool) and 'action' not in d:
                if d['default']:
                    d['action'] = 'store_false' # default true, false if flag set
                else:
                    d['action'] = 'store_true' # default false, true if flag set

        # change help string based on default value
        if d.pop('hidden', False):
            # do not list argument in "mdtf --help", but recognize it
            d['help'] = argparse.SUPPRESS
        elif 'default' in d:
            # display default value in help string
            #self._append_to_entry(d, 'help', "(default: %(default)s)")
            pass

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


class FrameworkCLIHandler(CLIHandler):
    def __init__(self, code_root, defaults_rel_path):
        self.code_root = code_root
        defaults_path = os.path.join(code_root, defaults_rel_path)
        defaults = util.read_json(defaults_path)
        self.case_list = defaults.pop('case_list', [])
        self.pod_list = defaults.pop('pod_list', [])

        self.config = dict()
        self.parser_groups = dict()
        self.parser_args_from_group = collections.defaultdict(list)
        self.parser = self.make_default_parser(defaults, defaults_path)

    def make_default_parser(self, d, config_path):
        # add more standard options to top-level parser
        if 'usage' not in d:
            d['usage'] = ("%(prog)s [options] CASE_ROOT_DIR\n"
                "{}%(prog)s info [INFO_TOPIC]").format(len('usage: ')*' ')
        self._append_to_entry(d, 'description',
            ("The second form ('mdtf info') prints information about available "
                "diagnostics."))
        d['arguments'] = util.coerce_to_iter(d.get('arguments', None))
        d['arguments'].extend([{
                "name": "root_dir",
                "is_positional": True,
                "nargs" : "?", # 0 or 1 occurences: might have set this with CASE_ROOT_DIR
                "help": "Root directory of model data to analyze.",
                "metavar" : "CASE_ROOT_DIR"
            },{
                'name':'version', 
                'action':'version', 'version':'%(prog)s 2.2'
            },{
                'name': 'config_file',
                'short_name': 'f',
                'help': """
                Path to a user configuration file. This can be a JSON
                file (a simple list of key:value pairs, or a modified copy of 
                the defaults file), or a text file containing command-line flags.
                Other options set via the command line will still override 
                settings in this file.
                """,
                'metavar': 'FILE'
            }])
        self._append_to_entry(d, 'epilog',
            "The default values above are set in {}.".format(config_path)
        )
        return self.make_parser(d)

    def make_parser(self, d):
        # used for defaults (above) and if we're passed a config file via the CLI
        # (file_opts, below)
        p = super(FrameworkCLIHandler, self).make_parser(d)
        p._positionals.title = None
        p._optionals.title = 'GENERAL OPTIONS'
        return p

    def parse_cli(self, args=None):
        # explicitly set cmd-line options, parsed according to default parser
        super(FrameworkCLIHandler, self).parse_cli(args)
        cli_opts = self.config
        # default values only, from running default parser on empty input
        defaults = vars(self.parser.parse_args([]))
        chained_dict_list = [cli_opts, defaults]

        # deal with options set in user-specified file, if present
        config_path = cli_opts.get('config_file', None)
        file_str = ''
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    file_str = f.read()
            except Exception:
                print("ERROR: Can't read config file at {}.".format(config_path))
        if file_str:
            try:
                file_opts = util.parse_json(file_str)
                # overwrite default case_list and pod_list, if given
                if 'case_list' in file_opts:
                    self.case_list = file_opts.pop('case_list')
                if 'pod_list' in file_opts:
                    self.pod_list = file_opts.pop('pod_list')
                if 'argument_groups' in file_opts or 'arguments' in file_opts:
                    # assume config_file is a modified copy of the defaults,
                    # with options to define parser. Set up the parser and run 
                    # CLI arguments through it (instead of default).
                    # Don't error on unrecognized args here, since those will be
                    # caught by the default parser.
                    custom_parser = self.make_parser(file_opts)
                    chained_dict_list = [
                        # CLI parsed with config_file's parser
                        vars(custom_parser.parse_known_args()[0]),
                        # defaults set in config_file's parser
                        vars(custom_parser.parse_known_args([])[0])
                    ] + chained_dict_list
                else:
                    # assume config_file a JSON dict of option:value pairs.
                    file_opts = {
                        self.canonical_arg_name(k): v for k,v in file_opts.iteritems()
                    }
                    chained_dict_list = [cli_opts, file_opts, defaults]
            except Exception:
                if 'json' in os.path.splitext('config_path')[1].lower():
                    print("ERROR: Couldn't parse JSON in {}.".format(config_path))
                    raise
                # assume config_file is a plain text file containing flags, etc.
                # as they would be passed on the command line.
                file_str = util.strip_comments(file_str, '#')
                file_opts = vars(self.parser.parse_args(shlex.split(file_str)))
                chained_dict_list = [cli_opts, file_opts, defaults]

        # CLI opts override options set from file, which override defaults
        self.config = dict(ChainMap(*chained_dict_list))


def load_pod_settings(code_root, pod=None, pod_list=None):
    """Wrapper to load POD settings files, used by ConfigManager and CLIInfoHandler.
    """
    # only place we can put it would be util.py if we want to avoid circular imports
    _pod_dir = 'diagnostics'
    _pod_settings = 'settings.json'
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
        bad_pods = list()
        realms = collections.defaultdict(list)
        for p in pod_list:
            d = _load_one_json(p)
            if not d:
                bad_pods.append(p)
                continue
            pods[p] = d
            d['settings']['realm'] = util.coerce_to_iter(
                d['settings'].get('realm', None)
            )
            for realm in d['settings']['realm']:
                realms[realm].append(p)
        for p in bad_pods:
            pod_list.remove(p)
        return (pod_list, pods, realms)
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
        self.pod_list, self.pods, self.realms = load_pod_settings(code_root)

        # build list of recognized topics, in order
        self.cmds = dict()
        self.cmd_list = []
        _add_topic_handler(['diagnostics', 'pods'], self.info_pods_all)
        _add_topic_handler('realms', self.info_realms_all)
        _add_topic_handler(self.realms.keys(), self.info_realm)
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

    def info_pods_all(self, *args):
        print('List of installed diagnostics:')
        print(('Do `mdtf info <diagnostic>` for more info on a specific diagnostic '
            'or check documentation at github.com/NOAA-GFDL/MDTF-diagnostics.'))
        for p in self.pod_list:
            print('  {}: {}.'.format(
                p, self.pods[p]['settings']['long_name']
            ))

    def info_pod(self, pod):
        d = self.pods[pod]
        print('{}: {}.'.format(pod, d['settings']['long_name']))
        print('Realm: {}.'.format(', '.join(d['settings']['realm'])))
        print(d['settings']['description'])
        print('Variables:')
        for var in d['varlist']:
            print('  {} ({}) @ {} frequency'.format(
                var['var_name'].replace('_var',''), 
                var.get('requirement',''), 
                var['freq'] 
            ))
            if 'alternates' in var:
                print ('    Alternates: {}'.format(
                    ', '.join([s.replace('_var','') for s in var['alternates']])
                ))

    def info_realms_all(self, *args):
        print('List of installed diagnostics by realm:')
        for realm in self.realms:
            print(realm)
            for p in self.realms[realm]:
                print('  {}: {}.'.format(
                    p, self.pods[p]['settings']['long_name']
                ))

    def info_realm(self, realm):
        print('List of installed diagnostics for {}:'.format(realm))
        for pod in self.realms[realm]:
            d = self.pods[pod]
            print('  {}: {}.'.format(pod, d['settings']['long_name']))
            print('    {}'.format(d['settings']['description']))
            print('    Variables: {}'.format(
                ', '.join([v['var_name'].replace('_var','') for v in d['varlist']])
            ))

