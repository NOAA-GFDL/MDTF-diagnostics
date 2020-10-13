"""Classes related to customizing the framework's command line interface and 
parsing the configuration options passed to it.
"""

import os
import sys
import io
import argparse
import collections
import shlex
import re
import textwrap
from src import util, diagnostic

import logging
_log = logging.getLogger(__name__)

def word_wrap(str_):
    """Clean whitespace and produces better word wrapping for multi-line help
    and description strings. Explicit paragraph breaks must be encoded as a 
    double newline (``\n\n``).
    """
    paragraphs = textwrap.dedent(str_).split('\n\n')
    paragraphs = [re.sub(r'\s+', ' ', s).strip() for s in paragraphs]
    paragraphs = [textwrap.fill(s, width=80) for s in paragraphs]
    return '\n\n'.join(paragraphs)

class CustomHelpFormatter(
        argparse.RawDescriptionHelpFormatter, 
        argparse.ArgumentDefaultsHelpFormatter
    ):
    """Modify help text formatter to only display variable placeholder 
    ("metavar") once, to save space. Taken from 
    `<https://stackoverflow.com/a/16969505>`__ . Also inherit from 
    RawDescriptionHelpFormatter in order to preserve line breaks in description
    only (`<https://stackoverflow.com/a/18462760>`__).
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
    """Add a boolean to record if user actually set argument's value, or if we're
    using the default value specified in the parser. From 
    `<https://stackoverflow.com/a/50936474>`__. This also re-implements the 
    'store_true' and 'store_false' actions, in order to give defaults 
    information on boolean flags.

    If the user specifies a value for ``option``, the :meth:`__call__` method
    adds a variable named ``option_is_default_`` to the returned 
    :py:class:`argparse.Namespace`. This information is used by 
    :meth:`.MDTFArgParser.parse_args` to populate the ``is_default`` attribute 
    of :class:`.MDTFArgParser`.
    """
    default_value_suffix = '_is_default_'

    def __init__(self, option_strings, dest, nargs=None, const=None, 
        default=None, required=False, **kwargs):
        if isinstance(default, bool):
            nargs = 0             # behave like a flag
            const = (not default) # set flag = store opposite of default
        elif isinstance(default, str) and nargs is None:
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
            setattr(namespace, self.dest, util.from_iter(values))
        else:
            setattr(namespace, self.dest, values)
        # set additional flag to indicate user has set this argument
        setattr(namespace, self.dest+self.default_value_suffix, False)


class MDTFArgParser(argparse.ArgumentParser):
    """Customized :py:class:`argparse.ArgumentParser` used by the framework. The
    main added functionality is the ability to configure the parser from an 
    external json file (:meth:`~MDTFArgParser.from_config`). We also implement

    - Customized help text formatting provided by :class:`.CustomHelpFormatter`.
    - Recording whether the user specified each argument value, or whether the
        default was used, via :class:`.RecordDefaultsAction`.
    - Better bookkeeping of `argument groups <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__ 
        (eg which arguments belong to which group).
    - Bookkeeping for arguments requiring additional processing (validation etc.)
        after parsing, via custom_types.
    """
    def __init__(self, *args, **kwargs):
        # no way to get this from public interface? _actions of group
        # contains all actions for entire parser
        self.parser_groups = dict()
        self.parser_args_from_group = collections.defaultdict(list)
        # manually track args requiring custom postprocessing (even if default
        # is used, so can't do with action=.. in argument)
        self.custom_types = collections.defaultdict(list)
        # Dict to store whether default value was used, for arguments using the
        # RecordDefaultsAction
        self.is_default = dict()
        self.parsed_args = None

        kwargs['formatter_class'] = CustomHelpFormatter
        super(MDTFArgParser, self).__init__(*args, **kwargs)
        self._positionals.title = None
        self._optionals.title = 'COMMAND OPTIONS'

    def iter_actions(self, group_name=None):
        """Iterator over :py:class:`~argparse.Action` objects associated with 
        arguments defined in parser.

        Args:
            group_name (optional): If supplied, only iterate over arguments
                belonging to this `argument group <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__.
                If omitted, iterate over all arguments. 
        """
        if not group_name:
            _groups = self.parser_args_from_group
        else:
            _groups = util.to_iter(group_name)
        for arg_gp in _groups:
            for arg in self.parser_args_from_group[arg_gp]:
                yield arg
    
    @staticmethod
    def canonical_arg_name(str_):
        """Convert flag or other specification to destination variable name.
        The destination variable name always has ``_``s, never ``-``s, in
        accordance with PEP8.
        """
        return str_.lstrip('-').rstrip().replace('-', '_')

    def add_arg_from_config(self, d, target=None, group_name=None):
        """Adds a CLI argument (flag or other setting) to the parser based on 
        settings read from a configuration file.

        Args:
            d (:obj:`dict`): dict of configuration settings for this argument of
                the parser.
            target (optional): Parser object (or parser group, or subparser) to 
                which the argument will be added. If omitted, the argument will
                be added to ``self``.
            group_name (optional): Name of the argument group to add the argument, 
                used by internal bookkeeping. If omitted, argument will be added
                at the top level, outside of any group, and added to the "parser"
                entry in ``parser_args_from_group``.
        """
        # Determine name, aliases and desitnation variable for flags:
        if 'name' not in d:
            raise ValueError("No argument name found in {}".format(d))
        arg_nm = self.canonical_arg_name(d.pop('name'))
        arg_flags = [arg_nm]
        if d.pop('is_positional', False):
            _ = d.pop('dest', None) # positionals can't specify independent dest
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

        # Type conversion of default value:
        if 'type' in d:
            d['type'] = eval(d['type'])
            if 'default' in d:
                d['default'] = d['type'](d['default'])
        if d.get('action', '') == 'count' and 'default' in d:
            d['default'] = int(d['default'])
        if d.get('parse_type', None):
            # make list of args requiring custom post-parsing later
            self.custom_types[d.pop('parse_type')].append(d['dest'])

        # record whether user set this value, or whether it's default
        _ = d.setdefault('action', RecordDefaultsAction)

        # change help string based on default value
        if d.pop('hidden', False):
            # do not list argument in "mdtf --help", but recognize it
            d['help'] = argparse.SUPPRESS

        # append argument object to the list of args for this arg group, so that
        # we can look it up later.
        if group_name is None:
            group_name = 'parser'
        if target is None:
            target = self
        self.parser_args_from_group[group_name].append(
            target.add_argument(*arg_flags, **d)
        )

    def add_group_from_config(self, d, target=None):
        """Adds a CLI `argument group <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__ 
        to the parser based on settings read from a configuration file.

        Args:
            d (:obj:`dict`): dict of configuration settings for this argument 
                group of the parser.
            target (optional): Parser object (or parser group, or subparser) to 
                which the argument will be added. If omitted, the argument will
                be added to ``self``.
        """
        if target is None:
            target = self
        gp_nm = d.pop('name')
        _ = d.setdefault('title', gp_nm)
        args = util.to_iter(d.pop('arguments', None))
        if args:
            # only add group if it has > 0 arguments
            gp_kwargs = util.filter_kwargs(d, argparse._ArgumentGroup.__init__)
            gp_obj = target.add_argument_group(**gp_kwargs)
            self.parser_groups[gp_nm] = gp_obj
            for arg in args:
                self.add_arg_from_config(arg, gp_obj, gp_nm)

    def configure(self, d):
        """Configures the argument parser based on settings read in from a file.
        Handles functionality provided by :py:meth:`~argparse.ArgumentParser.__init__`
        as well as :py:meth:`~argparse.ArgumentParser.add_argument` and 
        :py:meth:`~argparse.ArgumentParser.add_argument_group`.

        Args:
            d (:obj:`dict`): dict of configuration settings for the parser.

        Returns:
            Configured instance of :class:`MDTFArgParser`.
        """
        for attr_ in ['prog', 'usage', 'description', 'epilog']:
            if attr_ in d:
                setattr(self, attr_, word_wrap(d[attr_]))
        for arg_d in util.to_iter(d.pop('arguments', [])):
            # add arguments not in any group
            self.add_arg_from_config(arg_d)
        for group_d in util.to_iter(d.pop('argument_groups', [])):
            # add groups and arguments therein
            self.add_group_from_config(group_d)

    def parse_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_args` which
        populates the ``is_default`` attribute based on whether the user specified
        a value in ``args``, or whether the default was used.

        Args:
            args (optional): String or list of strings to parse. If a single 
                string is passed, it's split using :py:meth:`shlex.split`. 
                If not supplied, the default behavior parses :py:meth:`sys.argv`.
            namespace (optional): An object to store the parsed arguments. 
                The default is a new empty :py:class:`argparse.Namespace` object.

        Returns:
            Populated namespace containing parsed arguments, as with 
            :py:meth:`argparse.ArgumentParser.parse_args`. This is also stored 
            in the ``parsed_args`` attribute.
        """
        if isinstance(args, str):
            args = shlex.split(args, posix=True)
        self.parsed_args = super(MDTFArgParser, self).parse_args(args, namespace)

        # populate is_default with status of arguments left as default values
        for arg in self.iter_actions():
            if isinstance(arg, RecordDefaultsAction):
                default_value_flag = arg.dest + arg.default_value_suffix
                if default_value_flag in self.parsed_args:
                    self.is_default[arg.dest] = False
                    # delete the flag set by RecordDefaultsAction.__call__, 
                    # since we're transferring the information to is_default
                    delattr(self.parsed_args, default_value_flag)
                else:
                    self.is_default[arg.dest] = True
            else:
                self.is_default[arg.dest] = (arg.dest is arg.default)
        return self.parsed_args


class ConfigManager(util.Singleton):
    """:class:`~framework.util.Singleton` to make the results of CLI argument
    parsing more easily available for commands with a larger code base. Also 
    implements functionality to set "partial default" values from an external
    configuration file or other source.
    """
    def __init__(self, parser=None, partial_defaults=None):
        self._p = parser
        self._partial_defaults = partial_defaults
        # have "config" point to parsed_args namespace for now
        self.config = self._p.parsed_args
        # not really related, but store this info here as well
        self.global_envvars = dict()

    def parse_partial_defaults(self, config_str=None):
        """Set ``_partial_defaults`` using values read in from a configuration
        file in one of two formats. 
        
        Args:
            config_str (str): contents of the configuration file, either:

            1. A JSON/JSONC file of key-value pairs. This is parsed using
                :func:`~framework.util.file_io.parse_json`.
            2. A plain text file containing flags and arguments as they would
                be passed on the command line (except shell expansions are not 
                performed). This is parsed by the :meth:`MDTFArgParser.parse_args`
                method of the configured parser.

        The format is determined from context. ValueError is raised if the string
        cannot be parsed.
        """
        if not config_str:
            return
        # try to determine if file is json
        is_json = 'json' in os.path.splitext('config_path')[1].lower()
        # check if first non-comment, non-whitespace character is '{':
        try:
            temp_str = util.strip_comments(config_str, delimiter= '//')
            temp_ind = len(temp_str) - len(temp_str.lstrip())
            is_json = is_json or (temp_str[temp_ind] == '{')
        except Exception:
            is_json = False
        if is_json:
            try:
                file_input = util.parse_json(config_str)
                # overwrite default case_list and pod_list, if given
                # XXX HANDLE THIS
                # if 'case_list' in file_input:
                #     self.case_list = file_input.pop('case_list')
                # if 'pod_list' in file_input:
                #     self.pod_list = file_input.pop('pod_list')
                # assume config_file a JSON dict of option:value pairs.
                self._partial_defaults = [{
                    self._p.canonical_arg_name(k): v for k,v in file_input.items()
                }]
            except Exception:
                _log.exception('Attempted to parse input file as JSONC; failed.')
                raise ValueError()
        else:
            # assume config_file is a plain text file containing flags, etc.
            # as they would be passed on the command line.
            try:
                config_str = util.strip_comments(config_str, '#')
                self._partial_defaults = [vars(
                    self._p.parse_args(shlex.split(config_str))
                )]
            except Exception:
                _log.exception('Attempted to parse input file as plain text; failed.')
                raise ValueError()

    def parse_with_defaults(self):
        """Re-parse command-line arguments, allowing default values to be 
        overridden by values (if any) in the ``_partial_defaults`` attribute.
        The precedence order is:

        1. Argument values explictly given by the user on the command line, as 
            recorded in the ``is_default`` attribute of :class:`.MDTFArgParser`.
        2. Argument values given in the ``_partial_defaults`` attribute.
        3. Argument values specified as the default values in the argument parser.
        """
        # if no partial_defaults were set, results of the existing parse are
        # sufficient
        if self._partial_defaults is None:
            self.config = util.NameSpace.fromDict(vars(self._p.parsed_args))
        else:
            # Highest priority: options that were explicitly set by user on CLI
            # Note that is_default[opt] = None (not True or False) if no default 
            # value is defined for that option.
            user_cli_opts = {k:v for k,v in vars(self._p.parsed_args).items() \
                if not self._p.is_default.get(k, True)}

            if isinstance(self._partial_defaults, dict):
                # not handled correctly by to_iter, since dicts are iterable
                self._partial_defaults = [self._partial_defaults] 
            self._partial_defaults = util.to_iter(self._partial_defaults)
            partial_defaults = []
            for d in self._partial_defaults:
                # drop values equal to the empty string
                partial_defaults.append({k:v for k,v in d.items() if v != ""})

            # Lowest priority: set of defaults from running parser on empty input
            defaults = vars(self._p.parse_args([]))
            
            # CLI opts override options set from file, which override defaults
            chained_dict_list = [user_cli_opts] + partial_defaults + [defaults]
            self.config = dict(collections.ChainMap(*chained_dict_list))
            self.config = util.NameSpace.fromDict(self.config)

