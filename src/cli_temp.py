"""Classes related to customizing the framework's command line interface and 
parsing the configuration options passed to it.
"""

import os
import sys
import io
import argparse
import collections
import dataclasses
import enum
import importlib
import logging
import operator
import shlex
import re
import textwrap
import typing
from framework import util

_log = logging.getLogger(__name__)

def canonical_arg_name(str_):
    """Convert a flag or other specification to a destination variable name.
    The destination variable name always has ``_``s, never ``-``s, in
    accordance with PEP8. Eg., "--GNU-style-flag" -> "GNU_style_flag".
    """
    return str_.lstrip('-').rstrip().replace('-', '_')

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
                if args_string[0].isalpha():
                    args_string = '<' + args_string + '>'
                parts.extend(action.option_strings)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)


class RecordDefaultsAction(argparse.Action):
    """:py:class:`~argparse.Action` that adds a boolean to record if user 
    actually set argument's value, or if we're using the default value specified
    in the parser. From `<https://stackoverflow.com/a/50936474>`__. This also 
    re-implements the 'store_true' and 'store_false' actions, in order to give 
    defaults information on boolean flags.

    If the user specifies a value for ``option``, the :meth:`__call__` method
    adds a variable named ``option_is_default_`` to the returned 
    :py:class:`argparse.Namespace`. This information is used by 
    :meth:`.MDTFArgParser.parse_args` to populate the ``is_default`` attribute 
    of :class:`.MDTFArgParser`.
    """
    default_value_suffix = '_is_default_'

    def __init__(self, option_strings, dest, nargs=None, const=None, 
        default=None, type=None, **kwargs):
        if isinstance(default, bool):
            nargs = 0             # behave like a flag
            const = (not default) # set flag = store opposite of default
        elif (isinstance(default, str) or type == str) and nargs is None:
            # unless nargs given explictly, string-valued options accept 1 argument
            nargs = 1
            const = None
        super(RecordDefaultsAction, self).__init__(
            option_strings, dest, nargs=nargs, const=const, default=default, 
            type=type, **kwargs
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

class PathAction(RecordDefaultsAction):
    """:py:class:`~argparse.Action` that performs shell environment variable 
    expansion and resolution of relative paths, using 
    :func:`framework.util.file_io.resolve_path`.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        config = CLIConfigManager()
        path = util.from_iter(values)
        path = util.resolve_path(
            path, root_path=config.code_root, env=os.environ
        )
        super(PathAction, self).__call__(parser, namespace, path, option_string)

class PluginArgAction(RecordDefaultsAction):
    """:py:class:`~argparse.Action` to invoke the CLI plugin functionality.
    """    
    def __call__(self, parser, namespace, values, option_string=None):
        super(PluginArgAction, self).__call__(parser, namespace, values, option_string)
        config = CLIConfigManager()
        if getattr(config, 'plugins', None):
            value = util.from_iter(values)
            plugin_cmd = config.get_plugin(self.dest, value)
            setattr(namespace, self.dest, plugin_cmd.import_func())


@dataclasses.dataclass
class CLIArgument(object):
    """Class holding configuration options for a single argument of an 
    :py:class:`argparse.ArgumentParser`, with several custom options to simplify
    the parsing of CLIs defined in JSON files.
    """
    name: str
    action: str = None
    nargs: str = None
    const: typing.Any = None
    default: typing.Any = None
    type: typing.Any = None
    choices: typing.Iterable = None
    required: bool = False
    help: str = None
    metavar: str = None
    dest: str = None
    # following are custom additions to syntax
    arg_flags: list = dataclasses.field(init=False)
    is_positional: bool = False
    short_name: str = None
    hidden: bool = False

    def __post_init__(self):
        """Post-initialization type converstion of attributes.
        """
        # Format flag name(s) and destination variables
        arg_name = canonical_arg_name(self.name)
        self.arg_flags = [arg_name]
        if self.is_positional:
            self.name = arg_name
            self.dest = None # positionals can't specify independent dest
            self.required = None # positionals always required
        else:
            # argument is a command-line flag (default)
            if self.dest is None:
                self.dest = arg_name
            if '_' in arg_name:
                # recognize both --hyphen_opt and --hyphen-opt (GNU CLI convention)
                self.arg_flags = [arg_name.replace('_', '-'), arg_name]
            self.arg_flags = ['--'+s for s in self.arg_flags]
            if self.short_name is not None:
                # recognize both --option and -O, if short_name defined
                self.arg_flags.append('-' + self.short_name)

        # Type conversion of default value:
        if self.type is not None:
            if isinstance(self.type, str):
                self.type = util.deserialize_class(self.type)
            if self.default is not None:
                if not isinstance(self.default, self.type):
                    self.default = self.type(self.default)
                if self.action == 'count':
                    self.default = int(self.default)
            if self.const is not None and not isinstance(self.const, self.type):
                self.const = self.type(self.const)

        # parse action
        if self.action is None:
            self.action = RecordDefaultsAction
        elif isinstance(self.action, str) and self.action not in ['store',
            'store_const','store_true','store_false','append','append_const',
            'count','help','version']:
            self.action = util.deserialize_class(self.action)

        # do not list argument in "mdtf --help", but recognize it
        if self.hidden:
            self.help = argparse.SUPPRESS

    def add(self, target_p):
        """Adds the CLI argument to the parser ``target_p``. Wraps 
        :py:meth:`~argparse.ArgumentParser.add_argument`.

        Args:
            target_p: Parser object (or parser group, or subparser) to which the
                argument will be added. 
        """
        kwargs = {k:v for k,v in dataclasses.asdict(self).items() \
                if v is not None and k not in [
                'name', 'arg_flags', 'is_positional', 'short_name', 'hidden'        
            ]}
        return target_p.add_argument(*self.arg_flags, **kwargs)

@dataclasses.dataclass
class CLIArgumentGroup(object):
    """Class holding configuration options for an 
    :py:class:`argparse.ArgumentParser`
    `argument group <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__.
    """
    title: str
    description: str = None
    arguments: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, d):
        """Initialize an instance of this object from a nested dict obtained 
        from reading a JSON file.
        """
        args_list = d.get('arguments', [])
        d['arguments'] = [CLIArgument(**kwargs) for kwargs in args_list]
        return cls(**d)

    def add(self, target_p):
        """Adds the CLI argument group, as well as all arguments it contains, 
        to the parser ``target_p``. Wraps 
        :py:meth:`~argparse.ArgumentParser.add_argument_group`.

        Args:
            target_p: Parser object (or parser group, or subparser) to which the
                argument group will be added. 
        """
        if self.arguments:
            # only add group if it has > 0 arguments
            try:
                kwargs = {k:v for k,v in dataclasses.asdict(self).items() \
                    if v is not None and k in ['title', 'description']} 
            except Exception:
                print(self)
                print(repr(self))
            arg_gp = target_p.add_argument_group(**kwargs)
            for arg in self.arguments:
                _ = arg.add(arg_gp)
            return arg_gp

@dataclasses.dataclass
class CLIParser(object):
    """Class holding configuration options for an instance of 
    :py:class:`argparse.ArgumentParser` (or equivalently a subparser or a 
    command plugin).
    """
    prog: str = None
    usage: str = None
    description: str = None
    epilog: str = None
    arguments: list = dataclasses.field(default_factory=list)
    argument_groups: list = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Post-initialization type converstion of attributes.
        """
        for attr_ in ['prog', 'usage', 'description', 'epilog']:
            str_ = getattr(self, attr_, None)
            if str_:
                setattr(self, attr_, word_wrap(str_))

    @classmethod
    def from_dict(cls, d):
        """Initialize an instance of this object from a nested dict obtained 
        from reading a JSON file.
        """
        args_list = d.get('arguments', [])
        if args_list:
            d['arguments'] = [CLIArgument(**arg_d) for arg_d in args_list]
        arg_gps = d.get('argument_groups', [])
        if arg_gps:
            d['argument_groups'] = \
                [CLIArgumentGroup.from_dict(gp_d) for gp_d in arg_gps]
        return cls(**d)

    def configure(self, target_p):
        """Configures a parser object by setting top-level attributes and adding
        all arguments and argument groups.

        Args:
            target_p: Parser object (or parser group, or subparser) to configure.
        """
        if self.arguments: 
            for arg in self.arguments:
                # add arguments not in any group
                _ = arg.add(target_p)
        if self.argument_groups:
            for arg_gp in self.argument_groups:
                # add groups and arguments therein
                _ = arg_gp.add(target_p)
        for attr_ in ['prog', 'usage', 'description', 'epilog']:
            str_ = getattr(self, attr_, None)
            if str_:
                setattr(target_p, attr_, str_)

    def iter_args(self):
        """Iterator over all :class:`.CLIArgument` objects associated with this
        parser.
        """
        yield from self.arguments
        for arg_gp in self.argument_groups:
            yield from arg_gp.arguments

    def add_plugin_args(self, preparsed_d):
        """Revise arguments after we know what plugins are being used. This 
        annotates the help string of the plugin selector argument and configures
        its ``choices`` attribute. It then inserts the plugin-specifc CLI 
        arguments following that argument.

        Args:
            preparsed_d: dict of results of the preparsing operation. Keys are 
                the destination strings of the plugin selector arguments 
                (identified by having their ``action`` set to 
                :class:`.PluginArgAction`), and values are the values assigned 
                to them by preparsing.
        """
        def _add_plugins_to_arg_list(arg_list, splice_d):
            for arg in arg_list:
                if arg.action == PluginArgAction:
                    # update the arg controlling the plugin
                    preparsed_val = preparsed_d[arg.name]
                    plugin_d = config.get_plugin(arg.name)
                    
                    arg.help = arg.help + "\n\n" + word_wrap(f"""
                        NOTE: additional arguments below are specific to the 
                        chosen value '{preparsed_val}' of this option. 
                    """)
                    arg.choices = list(plugin_d.keys())
                    if not arg.default or arg.default not in arg.choices:
                        _log.warning(
                            "Default %s not found in available plugins %s, using %s.",
                            arg.default, str(arg.choices), arg.choices[0]
                        )
                        arg.default = arg.choices[0]
            # insert plugin args into arg_list
            return util.splice_into_list(
                arg_list, splice_d, operator.attrgetter('name')
            )

        config = CLIConfigManager()
        d = {k: list(config.get_plugin(k,v).cli.iter_args()) \
            for k,v in preparsed_d.items()}
        self.arguments = _add_plugins_to_arg_list(self.arguments, d)
        for arg_gp in self.argument_groups:
            arg_gp.arguments = _add_plugins_to_arg_list(arg_gp.arguments, d)

@dataclasses.dataclass
class CLICommand(object):
    """Class holding configuration options for a subcommand (invoked via a 
    subparser) or a plugin. 
    """
    name: str
    module: str
    entry_point: str
    help: str = None
    cli_file: str = None
    cli: dict = None
    parser: dataclasses.field(init=False) = None

    def __post_init__(self):
        """Post-initialization type converstion of attributes.
        """
        if self.cli is None:
            try:
                self.cli = util.read_json(self.cli_file)
            except util.MDTFFileNotFoundError:
                raise
        self.cli = CLIParser.from_dict(self.cli)

    def import_func(self):
        """Imports or returns the function or method object referred to by the
        ``module`` and ``entry_point`` attributes.
        """
        try:
            x = importlib.import_module(self.module)
            for attr_ in self.entry_point.split('.'):
                x = getattr(x, attr_)
            return x
        except ImportError:
            _log.error('Unable to import %s', self.module)
        except Exception:
            _log.error('Unable to import %s in %s', self.entry_point, self.module)

DefaultsFileTypes = enum.Enum('DefaultsFileTypes', 'USER SITE GLOBAL')
DefaultsFileTypes.__doc__ = """
    :py:class:`~enum.Enum` to distinguish the three different categories of 
    input settings files. In order of precedence:

    1. ``USER``: Input settings read from a file supplied by the user.
    2. ``SITE``: Settings specific to the given site (``--site`` flag.)
    3. ``GLOBAL``: Settings applicable to all sites. The main intended use case
        of this file is to enable the user to configure a default site at 
        install time.
"""

class CLIConfigManager(util.Singleton):
    """:class:`~framework.util.Singleton` to handle search, loading and parsing 
    of configuration files for the CLI and CLI default values. We encapsulate 
    this functionality in its own class, instead of :class:`.MDTFArgParser` or 
    its children, to try to make the code easier to understand (not out of 
    necessity).

    .. warning::
       This is intended to be initialized by a calling script *before* being 
       referenced by the classes in this module.
    """
    def __init__(self, code_root=None):
        # singleton, so this will only be invoked once
        self.code_root = code_root
        self.site = self.default_site

        self.subcommands = []
        self.subparser_kwargs = dict()
        self.plugins = dict()

        self.defaults = dict()
        for def_type in DefaultsFileTypes:
            self.defaults[def_type] = dict()
        self.defaults[DefaultsFileTypes.GLOBAL] = {'site': self.default_site}
    
    default_site = 'local'
    defaults_filename = "defaults.jsonc"
    subcommands_filename = "cli_subcommands.jsonc"
    plugins_filename = "cli_plugins.jsonc"

    @property
    def framework_dir(self):
        return os.path.join(self.code_root, 'framework')

    @property
    def sites_dir(self):
        return os.path.join(self.code_root, 'sites')

    @property
    def site_dir(self):
        assert self.site is not None
        return os.path.join(self.sites_dir, self.site)

    @property
    def partial_defaults(self):
        return collections.ChainMap(
            *([self.defaults[def_type] for def_type in DefaultsFileTypes])
        )

    def read_defaults(self, def_type, path=None):
        """Populate one of the entries in ``self.defaults`` by reading from the
        appropriate defaults file.

        Args:
            def_type (:class:`DefaultsFileTypes`): Type of defaults file to read.
            path (str, optional): path of the file. Only used for user-specified
                defaults.
        """
        def _read_defaults(path_):
            try:
                d = util.read_json(path_)
                # drop values equal to the empty string
                d = {k:v for k,v in d.items() if v != ""}
                self.defaults[def_type].update(d)
            except util.MDTFFileNotFoundError:
                _log.debug('Config file %s not found; not updating defaults.', path_)

        if def_type == DefaultsFileTypes.GLOBAL:
            # NB file lives in "sites_dir", not a "site_dir" for a given site
            _read_defaults(os.path.join(self.sites_dir, self.defaults_filename))
        elif def_type == DefaultsFileTypes.SITE:
            _read_defaults(os.path.join(self.site_dir, self.defaults_filename))
        elif def_type == DefaultsFileTypes.USER:
            assert path is not None
            _read_defaults(path)

    def _read_config_files(self, file_name):
        """Utility function to read a *pair* of configuration files (one for the
        framework defaults, another optional one for site-specific config.) 

        Args:
            file_name (str): Name of file to search for. We search for the file
                in all subdirectories of :class:meth:`._CLIConfigHandler.site_dir`
                and :class:meth:`._CLIConfigHandler.framework_dir`, respectively.

        Returns: a tuple of the two files' contents. First entry is the 
            site specific file (null dict if that file isn't found) and second 
            is the framework file (fatal error; exit immediately if not found.)
        """
        try:
            f = util.find_files(self.site_dir, file_name, n_files=1)
            site_d = util.read_json(util.from_iter(f))
        except util.MDTFFileNotFoundError:
            _log.debug('Config file %s not found in site dir %s; continuing.',
                    file_name, self.site_dir
            )
            site_d = dict()
        try:
            f = util.find_files(self.framework_dir, file_name, n_files=1)
            fmwk_d = util.read_json(util.from_iter(f))
        except util.MDTFFileNotFoundError:
            sys.exit((
                f"Error: Couldn't find {file_name} configuration file in"
                f" {self.framework_dir}."
            ))
        return (site_d, fmwk_d)

    @staticmethod
    def _dict_append_lists(ds, keys_to_append=None):
        """Utility function used to merge framework and site-specific
        configurations. 

        Args:
            ds: list of 1 or 2 dicts. If only one dict, return it. If passed 2 
                dicts, update the first with entries in the second, except for 
                those with keys listed in ``append_keys``.
            append_keys: str or list of str. Keys whose values in each of the 
                dicts in ``args`` will be coerced to a list and appended, instead
                of overwritten.

        Returns: dict of merged entries.
        """
        if len(ds) == 0:
            raise ValueError('No dicts were passed.')
        elif len(ds) == 1:
            return ds[0]
        elif len(ds) == 2:
            # ds = (site dict, fmwk dict)
            keys_to_append = util.to_iter(keys_to_append)
            appended_d = dict.fromkeys(keys_to_append)
            for key in keys_to_append:
                appended_d[key] = util.to_iter(ds[1].pop(key, [])) \
                    + util.to_iter(ds[0].pop(key, []))
            ds[0].update(ds[1])
            ds[0].update(appended_d)
            return ds[0]
        else:
            raise ValueError('Passed too many dicts ({} > 2)'.format(len(ds)))

    def read_subcommands(self):
        """Populates ``subcommands`` and ``subparser_kwargs`` attributes with 
        contents of CLI plugin files for the framework and site.
        """
        (site_d, fmwk_d) = self._read_config_files(self.subcommands_filename)
        # merge CLI files from framework and site
        d = self._dict_append_lists([site_d, fmwk_d], 'subcommands')
        self.subcommands = [
            CLICommand(**kwargs) for kwargs in d.pop('subcommands', [])
        ]
        self.subparser_kwargs = d

    def read_plugins(self):
        """Populates ``plugins`` attribute with contents of CLI plugin files for
        the framework and site.
        """
        (site_dlist, fmwk_dlist) = self._read_config_files(self.plugins_filename)
        temp = collections.defaultdict(list)
        for list_ in (site_dlist, fmwk_dlist):
            for plugin_d in list_:
                temp[plugin_d.get('dest','')].append(plugin_d)
        for dest in temp:
            # merge CLI files from framework and site
            d = self._dict_append_lists(temp[dest], 'choices')
            cmds = [CLICommand(**kwargs) for kwargs in d.pop('choices', [])]
            self.plugins[dest] = {cmd.name: cmd for cmd in cmds}

    def get_plugin(self, plugin_name, choice_of_plugin=None):
        """Lookup requested CLI plugin from ``plugins`` attribute, logging 
        appropriate errors where KeyErrors would be raised.

        Args:
            plugin_name (str): Name of the plugin selected.
            choice_of_plugin (str, optional): if provided, the name of the
                choice of plugin.

        Returns: :class:`.CLICommand` object corresponding to the requested
            plugin choice if both arguments are given, or a dict of recognized
            choices if only the first argument is given.
        """
        if plugin_name not in self.plugins:
            _log.error('Plugin %s not found (recognized: %s)', 
                plugin_name, str(list(self.plugins.keys()))
            )
            return dict()
        if choice_of_plugin is None:
            return self.plugins[plugin_name]
        if choice_of_plugin not in self.plugins[plugin_name]:
            _log.error('Choice of %s for plugin %s not found (recognized: %s)', 
                choice_of_plugin, plugin_name, 
                str(list(self.plugins[plugin_name].keys()))
            )
            return dict()
        return self.plugins[plugin_name][choice_of_plugin]


class MDTFArgParser(argparse.ArgumentParser):
    """Customized :py:class:`argparse.ArgumentParser`. Added functionality:

    - Configuring the parser from an external file (:meth:`~MDTFArgParser.configure`).
    - Customized help text formatting provided by :class:`.CustomHelpFormatter`.
    - Recording whether the user specified each argument value, or whether the
        default was used, via :class:`.RecordDefaultsAction`.
    - Better bookkeeping of `argument groups <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__ 
        (eg which arguments belong to which group).
    """
    def __init__(self, *args, **kwargs):
        # Dict to store whether default value was used, for arguments using the
        # RecordDefaultsAction
        self.is_default = dict()

        kwargs['formatter_class'] = CustomHelpFormatter
        super(MDTFArgParser, self).__init__(*args, **kwargs)
        self._positionals.title = None
        self._optionals.title = 'COMMAND OPTIONS'

    @staticmethod
    def split_args(argv):
        """Wrapper for :py:meth:`shlex.split`.
        """
        if isinstance(argv, str):
            argv = shlex.split(argv, posix=True)
        return argv

    def iter_actions(self):
        """Iterator over :py:class:`~argparse.Action` objects associated with 
        all user-defined arguments in parser, as well as those for any 
        subcommands.
        """
        def _iter_all_actions():
            for act in self._actions:
                if isinstance(act, argparse._SubParsersAction):
                    choices = getattr(act, 'choices', dict())
                    for p in choices.values():
                        yield from p._actions
                else:
                    yield act

        def _pred(act):
            return not isinstance(act, 
                (argparse._HelpAction, argparse._VersionAction))

        return filter(_pred, _iter_all_actions())

    def _set_is_default(self, parsed_args):
        """Populates the ``is_default`` attribute based on whether the user 
        explicitly specified a value, or whether a default was used.

        Args:
            parsed_args: dict of args and values returned by initial parsing.
        """
        self.is_default = dict() # clear in case we parsed previously
        for act in self.iter_actions():
            if isinstance(act, RecordDefaultsAction):
                default_value_flag = act.dest + act.default_value_suffix
                if default_value_flag in parsed_args:
                    self.is_default[act.dest] = False
                    # delete the flag set by RecordDefaultsAction.__call__, 
                    # since we're transferring the information to is_default
                    del parsed_args[default_value_flag]
                else:
                    self.is_default[act.dest] = True
            else:
                # check if value is equal to default; doesn't handle the case
                # where the user set the option equal to its default value 
                # (which is why RecordDefaultsAction is necessary.)
                self.is_default[act.dest] = (act.dest is act.default)

    def _default_argv(self, parsed_args):
        """Utility method returning the arguments passed to the parser for 
        lowest-priority defaults in 
        :meth:`.MDTFArgParser.parse_known_args`.
        """
        config = CLIConfigManager()
        return ['--site', parsed_args.get('site', config.default_site)]

    def parse_known_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args` which
        handles intermediate levels of default settings derived from the
        user's settings files. These override defaults defined in the parser 
        itself. The precedence order is:

        1. Argument values explictly given by the user on the command line, as 
            recorded in the ``is_default`` attribute of :class:`.MDTFArgParser`.
        2. Argument values given in the :meth:`~.CLIConfigManager.partial_defaults`` 
            property of :class:`~.CLIConfigManager`.
        3. Argument values specified as the default values in the argument parser.

        Args:
            args (optional): String or list of strings to parse. If a single 
                string is passed, it's split using :py:meth:`shlex.split`. 
                If not supplied, the default behavior parses :py:meth:`sys.argv`.
            namespace (optional): An object to store the parsed arguments. 
                The default is a new empty :py:class:`argparse.Namespace` object.

        Returns:
            Tuple of 1) populated namespace containing parsed arguments and 2) 
            unrecognized arguments, as with 
            :py:meth:`argparse.ArgumentParser.parse_known_args`.
        """
        def _to_dict(ns):
            if isinstance(ns, argparse.Namespace):
                return vars(ns)
            else:
                return dict(ns)

        config = CLIConfigManager()
        (parsed_args, remainder) = super(MDTFArgParser, self).parse_known_args(
            self.split_args(args), None
        )
        parsed_args = _to_dict(parsed_args)
        self._set_is_default(parsed_args)
        # Highest priority: options that were explicitly set by user on CLI
        # Note that is_default[opt] = None (not True or False) if no default 
        # value is defined for that option.
        user_cli_opts = {k:v for k,v in parsed_args.items() \
            if not self.is_default.get(k, True)}
        # drop values equal to the empty string
        partial_d = {k:v for k,v in config.partial_defaults.items() if v != ""}
        # Lowest priority: set of defaults from running parser on empty input
        parser_defaults, _ = super(MDTFArgParser, self).parse_known_args(
            self._default_argv(parsed_args), None
        )
        # CLI opts override options set from file, which override defaults
        parsed_args = _to_dict(collections.ChainMap(
            user_cli_opts, partial_d, vars(parser_defaults)
        ))
        if namespace is None:
            namespace = argparse.Namespace(**parsed_args)
        else:
            for k,v in parsed_args.items():
                setattr(namespace, k, v)
        return (namespace, remainder)

    def parse_args(self, args=None, namespace=None):
        """Subclassed implementation of :py:meth:`~argparse.ArgumentParser.parse_args`
        which wraps :meth:`~.MDTFArgParser.parse_known_args`.
        """
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            _log.error('unrecognized arguments: %s', ' '.join(argv))
        return args


class MDTFArgPreparser(MDTFArgParser):
    """Parser class used to "preparse" plugin selector arguments, to determine
    which plugins to use. Plugin selector arguments are identified by having 
    their ``action`` set to :class:`.PluginArgAction`.
    """
    def __init__(self):
        super(MDTFArgPreparser, self).__init__(add_help=False)

    def _default_argv(self, parsed_args):
        """Utility method returning the arguments passed to the parser for 
        lowest-priority defaults in 
        :meth:`.MDTFArgParser.parse_known_args`.
        """
        config = CLIConfigManager()
        return [
            '--site', parsed_args.get('site', config.default_site),
            parsed_args.get('subcommand', 'help')
        ]

    def parse_site(self, argv=None, default_site=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args`
        used to determine what site to use.
        """
        d = vars(self.parse_known_args(argv)[0])
        return d.get('site', default_site)

    def parse_plugins(self, argv=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args`
        used to parse the plugin selector arguments.
        """
        d = vars(self.parse_known_args(argv)[0])
        keys = [act.dest for act in self.iter_actions() \
            if isinstance(act, PluginArgAction)]
        return {k: d.get(k, None) for k in keys}
            

class MDTFTopLevelArgParser(MDTFArgParser):
    """Class for constructing the command-line interface, parsing the options,
    and handing off execution to the selected subcommand.
    """
    def __init__(self, argv=None):
        self.installed = False
        self.sites = []
        if argv is None:
            self.argv = sys.argv[1:]
        else:
            self.argv = self.split_args(argv)

        super(MDTFTopLevelArgParser, self).__init__(
            prog="mdtf",
            usage="%(prog)s [flags] <command> [command-specific options]",
            description=word_wrap("""
                Driver script for the NOAA Model Diagnostics Task Force (MDTF)
                package, which runs process-oriented diagnostics (PODs) on
                climate model data. See documentation at
                https://mdtf-diagnostics.rtfd.io.
            """)
        )

    def add_input_file_arg(self, target_p):
        """Convenience method to add the flag to pass a user-designated defaults
        file to the parser ``target_p`` (either the top-level parser, or the 
        preparser.)
        """
        kwargs = {'type': str}
        if isinstance(target_p, MDTFTopLevelArgParser):
            kwargs.update({
                'metavar': "INPUT_FILE",
                'help': word_wrap("""
                    Path to a user configuration file that sets options listed 
                    here. This can be a JSON file of the form given in 
                    sample_input.jsonc, or a text file containing command-line 
                    arguments. Options set explicitly on the command line will 
                    still override settings in this file.
                """)
            })     
        target_p.add_argument('--input_file', '--input-file', '-f', **kwargs)

    def init_user_defaults(self):
        """Set user defaults using values read in from a configuration
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
        config = CLIConfigManager()
        user_file_p = argparse.ArgumentParser(add_help=False)
        self.add_input_file_arg(user_file_p)
        path = getattr(user_file_p.parse_known_args()[0], 'input_file', None)
        if not path:
            return
        try:
            with io.open(path, 'r', encoding='utf-8') as f:
                str_ = f.read()
        except Exception:
            sys.exit(f"ERROR: Can't read input file at {path}.")
        if not str_:
            return
        if 'json' in os.path.splitext(path)[1].lower():
            # assume config file is JSON or JSON with //-comments
            try:
                d = util.parse_json(str_)
                # overwrite default case_list and pod_list, if given
                # TODO HANDLE THIS
                # if 'case_list' in d:
                #     self.case_list = d.pop('case_list')
                # if 'pod_list' in d:
                #     self.pod_list = d.pop('pod_list')
                d = {canonical_arg_name(k): v for k,v in d.items()}
                config.defaults[DefaultsFileTypes.USER].update(d)
            except Exception as exc:
                sys.exit(f"ERROR: JSON syntax error in {path}:\n\t{exc}")
        else:
            # assume config_file is a plain text file containing flags, etc.
            # as they would be passed on the command line.
            try:
                self.argv = self.argv + shlex.split(str_, comments=True, posix=True)
            except Exception as exc:
                sys.exit(f"ERROR: Couldn't parse flags in {path}.")

    def add_site_arg(self, target_p):
        """Convenience method to add the argument flag to select which
        site-specific code to use, to the parser ``target_p`` (either the 
        top-level parser, or the preparser.)
        """
        config = CLIConfigManager()
        kwargs = {'default': config.default_site}
        if isinstance(target_p, MDTFTopLevelArgParser):
            kwargs.update({
                'choices': self.sites,
                'metavar': "<site>", 
                'help': word_wrap("""
                    Site-specific functionality to use. 
                """)
            })
        target_p.add_argument('--site', '-s', **kwargs)

    def init_site(self):
        """We allow site-specific installations to customize the CLI, so before 
        we construct the CLI parser we need to determine what site to use. We do
        this by running a parser that only looks for the ``--site`` flag.

        This sets the ``site`` attribute and populates the global and
        site-specific settings dicts.
        """
        config = CLIConfigManager()
        config.read_defaults(DefaultsFileTypes.GLOBAL)
        default_site = config.partial_defaults.get('site', config.default_site)

        self.sites = [d for d in os.listdir(config.sites_dir) \
            if os.path.isdir(os.path.join(config.sites_dir, d))]
        if default_site in self.sites:
            self.installed = True

        site_p = MDTFArgPreparser()
        self.add_site_arg(site_p)
        site = site_p.parse_site(self.argv, default_site)
        if site not in self.sites \
            and not (site == default_site and not self.installed):
            sys.exit((
                f"Error: requested site {site} not found in"
                f" sites directory {config.sites_dir}."
            ))
        config.default_site = default_site
        config.site = site
        config.read_defaults(DefaultsFileTypes.SITE)

    def build_subparsers(self, target_p):
        """Convenience method to fully configure a parser ``target_p`` (either 
        the top-level parser, or the preparser), adding subparsers for all
        subcommands.
        """
        def _defaultdict_update(d1, d2):
            tmp_d = {k: (d1[k] + d2[k]) for k in set(d1) & set(d2)}
            d1.update(d2)
            d1.update(tmp_d)

        config = CLIConfigManager()
        add_help = isinstance(target_p, MDTFTopLevelArgParser)
        self.add_site_arg(target_p)
        self.add_input_file_arg(target_p)
        sub_p = target_p.add_subparsers(**config.subparser_kwargs)
        _ = sub_p.add_parser(
            "help", help="Show this help message and exit.", add_help=add_help
        )
        for cmd in config.subcommands:
            cmd.parser = sub_p.add_parser(
                cmd.name, help=cmd.help, add_help=add_help,
                usage=cmd.cli.usage, description=cmd.cli.description
            )
            cmd.cli.configure(cmd.parser)

    def configure(self):
        """Method that assembles the top-level CLI parser. Options specific to 
        the script are hard-coded here; CLI options for each subcommand are 
        given in jsonc configuration files for each command which are read in 
        here. See associated documentation for :class:`~framework.cli.MDTFArgParser`
        for information on the configuration file mechanism.
        """
        self.add_argument(
            '--version', action="version", version="%(prog)s 3.0 beta 3"
        )
        self._optionals.title = 'GENERAL OPTIONS'
        if not self.installed:
            self.epilog=word_wrap("""
                Warning: User-customized configuration files not found. Consider
                running 'mdtf install' to configure your installation.
            """)
        self.build_subparsers(self)

    def setup(self):
        """Method to wrap all configuration methods needed to configure the 
        parser before calling parse_arg: reading the defaults files and 
        configuring plugins based on existing values.
        """
        config = CLIConfigManager()
        self.init_user_defaults()
        self.init_site()
        config.read_subcommands()
        config.subparser_kwargs.update({
            'required':True, 'dest':'subcommand', 'parser_class': MDTFArgParser
        })
        config.read_plugins()
        # preparse arguments to get plugin configuration, and revise CLI
        temp_p = MDTFArgPreparser()
        self.build_subparsers(temp_p)
        plugin_args = temp_p.parse_plugins(self.argv)
        for cmd in config.subcommands:
            cmd.cli.add_plugin_args(plugin_args)
        # Build the real CLI parser now that we have plugins
        self.configure()

    def _default_argv(self, parsed_args):
        """Utility method returning the arguments passed to the parser for 
        lowest-priority defaults in 
        :meth:`.MDTFArgParser.parse_known_args`.
        """
        config = CLIConfigManager()
        return [
            '--site', parsed_args.get('site', config.default_site),
            parsed_args.get('subcommand', 'help')
        ]

    def parse_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_args` which
        handles intermediate levels of default settings.
        """
        if args:
            args = self.split_args(args)
        else:
            args = self.argv
        return super(MDTFTopLevelArgParser, self).parse_args(args, namespace)

    def parse_known_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args` which
        handles intermediate levels of default settings.
        """
        if args:
            args = self.split_args(args)
        else:
            args = self.argv
        return super(MDTFTopLevelArgParser, self).parse_known_args(args, namespace)


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
