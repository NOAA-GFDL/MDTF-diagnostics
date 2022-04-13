"""Classes which parse the framework's command line interface configuration files
and implement the dynamic CLI; see :doc:`fmwk_cli`.

Familiarity with the python :py:mod:`argparse` module is recommended.
"""
import os
import sys
import io
import argparse
import collections
import dataclasses
import importlib
import itertools
import json
import operator
import shlex
import re
import textwrap
import typing
from src import util

import logging
_log = logging.getLogger(__name__)

_SCRIPT_NAME = 'mdtf.py' # mimic argparse error message text

def canonical_arg_name(str_):
    """Convert a flag or other specification to a destination variable name.
    The destination variable name always has underscores, never hyphens, in
    accordance with PEP8.

    E.g., ``canonical_arg_name('--GNU-style-flag')`` returns "GNU_style_flag".
    """
    return str_.lstrip('-').rstrip().replace('-', '_')

def plugin_key(plugin_name):
    """Convert user input for plugin options to string used to lookup plugin
    value from options defined in cli_plugins.jsonc files.

    Ignores spaces and underscores in supplied choices for CLI plugins, and
    make matching of plugin names case-insensititve.
    """
    return re.sub(r"[\s_]+", "", plugin_name).lower()

def word_wrap(str_):
    """Clean whitespace and perform 80-column word wrapping for multi-line help
    and description strings. Explicit paragraph breaks must be encoded as a
    double newline \(``\\n\\n``\).
    """
    paragraphs = textwrap.dedent(str_).split('\n\n')
    paragraphs = [re.sub(r'\s+', ' ', s).strip() for s in paragraphs]
    paragraphs = [textwrap.fill(s, width=80) for s in paragraphs]
    return '\n\n'.join(paragraphs)

def read_config_files(code_root, file_name, site=""):
    """Utility function to read a pair of configuration files: one for the
    framework defaults, another optional one for site-specific configuration.

    Args:
        code_root (str): Code repo directory.
        file_name (str): Name of file to search for. We search for the file
            in all subdirectories of :meth:`CLIConfigManager.site_dir`
            and :meth:`CLIConfigManager.framework_dir`, respectively.
        site (str): Name of the site-specific directory (in ``/sites``) to search.

    Returns:
        A tuple of the two files' contents. First element is the
        site specific file (empty dict if that file isn't found) and second
        is the framework file (if not found, fatal error and exit immediately.)
    """
    src_dir = os.path.join(code_root, 'src')
    site_dir = os.path.join(code_root, 'sites', site)
    site_d = util.find_json(site_dir, file_name, exit_if_missing=False, log=_log)
    fmwk_d = util.find_json(src_dir, file_name, exit_if_missing=True, log=_log)
    return (site_d, fmwk_d)

def read_config_file(code_root, file_name, site=""):
    """Return the site's config file if present, else the framework's file. Wraps
    :func:`read_config_files`.

    Args:
        code_root (str): Code repo directory.
        file_name (str): Name of file to search for. We search for the file
            in all subdirectories of :meth:`CLIConfigManager.site_dir`
            and :meth:`CLIConfigManager.framework_dir`, respectively.
        site (str): Name of the site-specific directory (in ``/sites``) to search.

    Returns:
        Path to the configuration file.
    """
    site_d, fmwk_d = read_config_files(code_root, file_name, site=site)
    if not site_d:
        return fmwk_d
    return site_d

class CustomHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter
    ):
    """Modify help text formatter to only display variable placeholder text
    ("metavar") once, to save space. Taken from
    `<https://stackoverflow.com/a/16969505>`__. Also inherit from
    :py:class:`argparse.RawDescriptionHelpFormatter` in order to preserve line
    breaks in description only (`<https://stackoverflow.com/a/18462760>`__).
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

    def _get_help_string(self, action):
        """Only print the argument's default in the help string if it's defined.
        Based on `<https://stackoverflow.com/a/34545549>`__.
        """
        help_str = action.help
        if help_str == argparse.SUPPRESS:
            # ignore hidden CLI items
            return help_str
        if action.default not in (None, argparse.SUPPRESS) \
            and '%(default)' not in help_str:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                if isinstance(action.default, str):
                    help_str += " (default: '%(default)s')"
                else:
                    help_str += " (default: %(default)s)"
        return help_str


class RecordDefaultsAction(argparse.Action):
    """Argparse :py:class:`~argparse.Action` that adds a boolean to record if user
    actually set the argument's value, or if we're using the default value specified
    in the parser. From `<https://stackoverflow.com/a/50936474>`__. This also
    re-implements the 'store_true' and 'store_false' actions, in order to give
    defaults information on boolean flags.

    If the user specifies a value for an option named ``<option>``, the
    :meth:`__call__` method adds a variable named ``<option>_is_default_`` to
    the returned :py:class:`argparse.Namespace`. This information is used by
    :meth:`.MDTFArgParser.parse_args` to populate the ``is_default`` attribute
    of :class:`.MDTFArgParser`.

    Subclasses of :py:class:`argparse.Action` are only called on user-supplied
    values, not default values. If the ``call_on_defaults`` flag is set on a
    subclass, :meth:`.MDTFArgParser.parse_args` will also call the action on
    default values.
    """
    default_value_suffix = '_is_default_'
    call_on_defaults = False # call action on default values

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
    """Argparse :py:class:`~argparse.Action` that performs shell environment
    variable expansion and resolution of relative paths, using
    :func:`~src.util.filesystem.resolve_path`. Should be specified as the CLI
    action for every option taking paths as a value.
    """
    call_on_defaults = True

    def __call__(self, parser, namespace, values, option_string=None):
        # config = CLIConfigManager()
        path = util.from_iter(values)
        if path is None:
            path = ''
        # Don't do anything else here: may need to use env vars to properly
        # resolve paths, so that's now done later, in core.PathManager.__init__()
        super(PathAction, self).__call__(parser, namespace, path, option_string)

class ClassImportAction(RecordDefaultsAction):
    """Argparse :py:class:`~argparse.Action` to import classes on demand. Values
    are looked up from the 'cli_plugins.jsonc' file. This is a placeholder used
    to trigger behavior when arguments are parsed.
    """
    call_on_defaults = False

    def __call__(self, parser, namespace, values, option_string=None):
        """Do case-insensitive matching on plugin names.
        """
        p_key = plugin_key(util.from_iter(values))
        super(ClassImportAction, self).__call__(
            parser, namespace, p_key, option_string
        )

class PluginArgAction(ClassImportAction):
    """Argparse :py:class:`~argparse.Action` to invoke the CLI plugin functionality,
    specificially importing the plugin's entry point via :class:`ClassImportAction`.
    All CLI options which define a plugin should specify this as the action.
    """
    call_on_defaults = False



# ===========================================================================
# classes for represting CLI configuration information

@dataclasses.dataclass
class CLIArgument(object):
    """Class which stores configuration options for a single argument of an
    :py:class:`argparse.ArgumentParser`, with several custom options to simplify
    the parsing of CLIs defined in JSON files. Attributes correspond to arguments
    to :py:meth:`~argparse.ArgumentParser.add_argument`.
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
        """Post-initialization type conversion of attributes.
        """
        def _flag_names(_arg_name):
            _arg_flags = [_arg_name]
            if '_' in _arg_name:
                # recognize both --hyphen_opt and --hyphen-opt (GNU CLI convention)
                _arg_flags.append(_arg_name.replace('_', '-'))
            return ['--'+s for s in _arg_flags]

        # Format flag name(s) and destination variables
        if self.is_positional:
            assert isinstance(self.name, str) # not a list
            arg_name = canonical_arg_name(self.name)
            self.arg_flags = [arg_name]
            self.name = arg_name
            self.dest = None # positionals can't specify independent dest
            self.required = None # positionals always required
        else:
            # argument is a command-line flag (default)
            # if self.name is a list, recognize all entries as synonyms
            arg_flags = [canonical_arg_name(s) for s in util.to_iter(self.name)]
            if self.dest is None:
                # if synonyms provided, destination is first in list
                self.dest = arg_flags[0]
            self.arg_flags = list(itertools.chain.from_iterable(
                _flag_names(s) for s in arg_flags
            ))
            if self.short_name is not None:
                # recognize both --option and -O, if short_name defined
                self.arg_flags.insert(1, '-' + self.short_name)

        # Add default value set from site-specific file (so that it will show up
        # when the user runs --help)
        config = CLIConfigManager()
        if self.dest in config.site_defaults:
            self.default = config.site_defaults[self.dest]

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
        if isinstance(self.action, type) and issubclass(self.action, ClassImportAction):
            # Enforce case-insensitive matching on plugin names.
            self.nargs = 1
            self.const = None
            self.type = plugin_key
            if self.default:
                self.default = plugin_key(self.default)

        # do not list argument in "mdtf --help", but recognize it
        if self.hidden:
            self.help = argparse.SUPPRESS

    def add(self, target_p):
        """Adds the CLI argument to the parser ``target_p``. Wraps
        :py:meth:`~argparse.ArgumentParser.add_argument`.

        Args:
            target_p: Parser object (or argument group, or subparser) to which the
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
    :py:class:`argparse.ArgumentParser` `argument group
    <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__.
    Attributes correspond to arguments
    to :py:meth:`~argparse.ArgumentParser.add_argument_group`.
    """
    title: str
    description: str = None
    arguments: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, d):
        """Initialize an instance of this object from a nested dict *d* obtained
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
            target_p: Parser object (or subparser) to which the
                argument group will be added.
        """
        if self.arguments:
            # only add group if it has > 0 arguments
            kwargs = {k:v for k,v in dataclasses.asdict(self).items() \
                if v is not None and k in ['title', 'description']}
            arg_gp = target_p.add_argument_group(**kwargs)
            for arg in self.arguments:
                _ = arg.add(arg_gp)
            return arg_gp

@dataclasses.dataclass
class CLIParser(object):
    """Class holding configuration options for an instance of
    :py:class:`argparse.ArgumentParser` (or equivalently a subcommand parser or
    a CLI plugin). Attributes correspond to arguments given to the
    :py:class:`argparse.ArgumentParser` constructor.
    """
    prog: str = None
    usage: str = None
    description: str = None
    epilog: str = None
    arguments: list = dataclasses.field(default_factory=list)
    argument_groups: list = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Post-initialization type conversion of attributes.
        """
        for attr_ in ['prog', 'usage', 'description', 'epilog']:
            str_ = getattr(self, attr_, None)
            if str_:
                setattr(self, attr_, word_wrap(str_))

    @classmethod
    def from_dict(cls, d):
        """Initialize an instance of this object from a nested dict *d* obtained
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

    def iter_args(self, filter_class=None):
        """Iterator over all :class:`.CLIArgument` objects associated with this
        parser; if *filter_class* is specified, only iterate over objects having
        (a subclass of) *filter_class* as their ``action``.
        """
        def _iter_all_args():
            yield from self.arguments
            for arg_gp in self.argument_groups:
                yield from arg_gp.arguments

        if filter_class is None:
            yield from _iter_all_args()
        else:
            filter_fn = (lambda arg: isinstance(arg.action, type) \
                and issubclass(arg.action, filter_class))
            yield from filter(filter_fn, _iter_all_args())

    def configure(self, target_p):
        """Configures a parser object by setting top-level attributes and adding
        all arguments and argument groups.

        Args:
            target_p: Parser object to configure.
        """
        # enforce choices for plugin args:
        config = CLIConfigManager()
        for arg in self.iter_args(filter_class=ClassImportAction):
            arg.choices = list(config.get_plugin(arg.name).keys())
            if not arg.default or arg.default not in arg.choices:
                _log.warning(
                    "Default '%s' not found in available choices for %s, using '%s'.",
                    arg.default, str(arg.choices), arg.choices[0]
                )
                arg.default = arg.choices[0]

        # add everything
        if self.arguments:
            for arg in self.arguments:
                # add arguments not in any group
                _ = arg.add(target_p)
        if self.argument_groups:
            for arg_gp in self.argument_groups:
                # add groups and arguments therein
                _ = arg_gp.add(target_p)
        for attr_ in ['prog', 'usage', 'epilog']:
            str_ = getattr(self, attr_, None)
            if str_:
                setattr(target_p, attr_, str_)

        # append source of default values to description, to reduce user confusion
        description_text = getattr(self, 'description', None)
        defaults_text = config.site_default_text()
        if defaults_text:
            if description_text is None:
                description_text = defaults_text
            else:
                description_text += '\n\n' + defaults_text
        if description_text:
            setattr(target_p, 'description', description_text)

    def add_plugin_args(self, preparsed_d):
        """Revise arguments after we know what plugins are being used. This
        annotates the help string of the plugin selector argument and configures
        its ``choices`` attribute (which lists the allowed values for each option
        in the online help). It then inserts the plugin-specifc CLI
        arguments following that argument.

        Args:
            preparsed_d: dict of results of the preparsing operation. Keys are
                the destination strings of the plugin selector arguments
                (identified by having their ``action`` set to
                :class:`.PluginArgAction`), and values are the values assigned
                to them by preparsing.
        """
        def _add_plugins_to_arg_list(arg_list, splice_d):
            # insert plugin args into arg_list
            return util.splice_into_list(
                arg_list, splice_d, operator.attrgetter('dest'), log=_log
            )

        config = CLIConfigManager()

        d = dict()
        for flag_name, flag_value in preparsed_d.items():
            plugin = config.get_plugin(flag_name, flag_value)
            if not plugin:
                choices = [f"'{x}'" for x in config.get_plugin(flag_name).keys()]
                _log.critical(("%s: error: argument --%s: invalid choice: '%s' "
                    "(choose from %s)"),
                    _SCRIPT_NAME, flag_name, flag_value, ', '.join(choices)
                )
                util.exit_handler(code=2) # exit code for  CLI syntax error
            d[flag_name] = list(plugin.cli.iter_args())
        self.arguments = _add_plugins_to_arg_list(self.arguments, d)
        for arg_gp in self.argument_groups:
            arg_gp.arguments = _add_plugins_to_arg_list(arg_gp.arguments, d)

        for arg in self.iter_args(filter_class=PluginArgAction):
            if arg.help == argparse.SUPPRESS:
                # skip hidden CLI items
                continue
            flag_value = preparsed_d[arg.name]
            plugin = config.get_plugin(arg.name, flag_value)
            if plugin.help:
                arg.help = arg.help.strip() + \
                    f" Selected value = '{flag_value}': {plugin.help.strip()} "
            else:
                arg.help = arg.help.strip() + f" Selected value = '{flag_value}'. "
            arg.help = arg.help + word_wrap(f"""
                NOTE: flags below are specific to this value. Set a different
                value along with '--help' to see flags for that option.
            """)

@dataclasses.dataclass
class CLICommand(object):
    """Class holding configuration options for a subcommand (invoked via a
    subparser) or a plugin.
    """
    name: str
    entry_point: str
    help: str = ""
    cli_file: str = None
    cli: dict = None
    parser: typing.Any = dataclasses.field(init=False, default=None)
    code_root: dataclasses.InitVar = ""

    def __post_init__(self, code_root):
        """Post-initialization type converstion of attributes.
        """
        if self.cli is None and self.cli_file is not None:
            try:
                self.cli = util.read_json(
                    os.path.join(code_root, self.cli_file), log=_log
                )
            except util.MDTFFileNotFoundError:
                _log.critical("Couldn't find CLI file %s.", self.cli_file)
                util.exit_handler(code=2) # exit code for  CLI syntax error
        if self.cli is not None:
            self.cli = CLIParser.from_dict(self.cli)

    def import_target(self):
        """Imports the function or class referred to by the ``entry_point``
        attribute.
        """
        mod_name, cls_name = self.entry_point.split(':')
        try:
            mod_ = importlib.import_module(mod_name)
        except ImportError:
            _log.error('Unable to import %s.', mod_name)
            raise ValueError(self.entry_point)
        try:
            return getattr(mod_, cls_name)
        except Exception:
            _log.error('Unable to import %s in %s.', cls_name, mod_name)
            raise ValueError(self.entry_point)

    def call(self, *args, **kwargs):
        """Imports the function or class referred to by the
        ``entry_point`` attribute, and calls it with the passed arguments.
        """
        cls_ = self.import_target()
        instance = cls_(*args, **kwargs)
        return instance

DefaultsFileTypes = util.MDTFEnum('DefaultsFileTypes', 'USER SITE GLOBAL')
DefaultsFileTypes.__doc__ = """
    :class:`~util.MDTFEnum` to distinguish the three different categories of
    input settings files. In order of precedence:

    1. ``USER``: Input settings read from a file supplied by the user.
    2. ``SITE``: Settings specific to the given site (set with the ``--site`` flag.)
    3. ``GLOBAL``: Settings applicable to all sites. The main intended use case
       of this file is to enable the user to configure a default site at
       install time.
"""

class CLIConfigManager(util.Singleton):
    """:class:`~src.util.Singleton` to handle search, loading and parsing
    of configuration files for the CLI and CLI default values. We encapsulate
    this functionality in its own class, instead of :class:`.MDTFArgParser` or
    its children, to try to make the code easier to understand (not out of
    necessity).

    .. note::
       This is initialized in :class:`MDTFTopLevelArgParser`; as a Singleton, it
       must be properly initialized before being referenced by the classes in
       this module.
    """
    def __init__(self, code_root=None, skip_defaults=False):
        # singleton, so this will only be invoked once

        self.code_root = code_root
        self.skip_defaults = skip_defaults
        self.site = self.default_site

        self.subcommands = dict()
        self.subcommand_files = []
        self.subparser_kwargs = dict()
        self.plugins = dict()
        self.plugin_files = []

        self.defaults_files = dict()
        self.site_defaults = {'site': self.default_site}
        self.user_defaults = dict()

    default_site = 'local'
    """Name of the default value for the ``--site`` option.
    """
    defaults_filename = "defaults.jsonc"
    """Name of the JSONC file for site-specific default settings.
    """
    subcommands_filename = "cli_subcommands.jsonc"
    """Name of the JSONC files defining site-specific and built-in CLI subcommands.
    """
    plugins_filename = "cli_plugins.jsonc"
    """Name of the JSONC files defining site-specific and built-in CLI plugins.
    """

    @property
    def framework_dir(self):
        """Absolute path to the framework code directory, <CODE_ROOT>/src.
        """
        return os.path.join(self.code_root, 'src')

    @property
    def sites_dir(self):
        """Absolute path to the directory for site-specific code, <CODE_ROOT>/sites.
        """
        return os.path.join(self.code_root, 'sites')

    @property
    def site_dir(self):
        """Absolute path to the directory for the site-specific code for the
        chosen site, <CODE_ROOT>/sites/<site>.
        """
        assert self.site is not None
        return os.path.join(self.sites_dir, self.site)

    def read_defaults(self, def_type, path=None):
        """Populate one of the entries in ``self.defaults`` by reading from the
        appropriate defaults file.

        Args:
            def_type (:class:`DefaultsFileTypes`): Type of defaults file to read.
            path (str, optional): path of the file. Only used for user-specified
                defaults.
        """
        if self.skip_defaults:
            return
        if def_type == DefaultsFileTypes.GLOBAL:
            # NB file lives in "sites_dir", not a "site_dir" for a given site
            path = os.path.join(self.sites_dir, self.defaults_filename)
            dest_d = self.site_defaults
        elif def_type == DefaultsFileTypes.SITE:
            path = os.path.join(self.site_dir, self.defaults_filename)
            dest_d = self.site_defaults
        elif def_type == DefaultsFileTypes.USER:
            assert path # is not none
            dest_d = self.user_defaults

        try:
            d = util.read_json(path, log=_log)
            self.defaults_files[def_type] = path
            # drop values equal to the empty string
            d = {k:v for k,v in d.items() if (v is not None and v != "")}
            dest_d.update(d)
        except util.MDTFFileNotFoundError:
            _log.debug('Config file %s not found; not updating defaults.', path)

    def site_default_text(self):
        """Return text to be used in online help describing the paths to the
        defaults files that are being used.
        """
        files_str = [self.defaults_files.get(x, None) for x in [
            DefaultsFileTypes.SITE, DefaultsFileTypes.GLOBAL]]
        files_str = '\n'.join([x for x in files_str if x is not None])
        if files_str:
            return "Default values have been set from the following files:" \
                + '\n' + files_str
        else:
            return None

    def read_subcommands(self):
        """Populates ``subcommands`` and ``subparser_kwargs`` attributes with
        contents of CLI plugin files for the framework and site. Site-specific
        subcommand definitions override those defined on the framework.
        """
        (site_d, fmwk_d) = read_config_files(
            self.code_root, self.subcommands_filename, self.site
        )
        site_cmds = site_d.pop('subcommands', dict())
        fmwk_cmds = fmwk_d.pop('subcommands', dict())
        self.subparser_kwargs = fmwk_d
        self.subparser_kwargs.update(site_d)
        self.subcommands = {
            k: CLICommand(name=k, **v, code_root=self.code_root) \
                for k,v in fmwk_cmds.items()
        }
        for k,v in site_cmds.items():
            if k in self.subcommands:
                _log.debug("Replacing subcommand '%s' with site-specific version.", k)
            self.subcommands[k] = CLICommand(name=k, **v, code_root=self.code_root)

    def read_plugins(self):
        """Populates ``plugins`` attribute with contents of CLI plugin files for
        the framework and site.
        """
        def _add_new_plugin_type(plugin_arg, arg_choices):
            self.plugins[plugin_arg] = {
                plugin_key(k): CLICommand(name=k, **v, code_root=self.code_root) \
                    for k,v in arg_choices.items()
            }

        (site_d, fmwk_d) = read_config_files(
            self.code_root, self.plugins_filename, self.site
        )
        for k, v in fmwk_d.items():
            _add_new_plugin_type(k, v)
        for k, v in site_d.items():
            if k not in self.plugins:
                _add_new_plugin_type(k, v)
                continue
            for kk, vv in v.items():
                p_key = plugin_key(kk)
                if p_key in self.plugins[k]:
                    _log.debug(
                        'Replacing plugin %s (for %s) with site-specific version.',
                        kk, k
                    )
                self.plugins[k][p_key] = \
                    CLICommand(name=kk, **vv, code_root=self.code_root)

    def get_plugin(self, plugin_name, choice_of_plugin=None):
        """Look up requested CLI plugin from ``plugins`` attribute, logging
        appropriate errors where KeyErrors would be raised.

        Args:
            plugin_name (str): Name of the plugin selected.
            choice_of_plugin (str, optional): if provided, the name of the
                choice of plugin.

        Returns:
            :class:`.CLICommand` object corresponding to the requested
            plugin choice if both arguments are given, or a dict of recognized
            choices if only the first argument is given.
        """
        if plugin_name not in self.plugins:
            _log.error('Plugin %s not found (recognized: %s)',
                plugin_name, str(list(self.plugins.keys()))
            )
            return dict()
        if choice_of_plugin is None:
            # return entire dict
            return self.plugins[plugin_name]
        p_key = plugin_key(choice_of_plugin)
        if p_key not in self.plugins[plugin_name]:
            _log.critical(("%s: error: argument --%s: invalid choice: '%s' "
                "(choose from %s)"),
                _SCRIPT_NAME, plugin_name, choice_of_plugin,
                str(list(self.plugins[plugin_name].keys()))
            )
            util.exit_handler(code=2) # exit code for CLI syntax error
        return self.plugins[plugin_name][p_key]

# ===========================================================================
# CLI parsers

class MDTFArgParser(argparse.ArgumentParser):
    """Customized :py:class:`argparse.ArgumentParser`. Added functionality:

    - Configuring the parser from an external file (:meth:`~MDTFArgParser.configure`).
    - Customized help text formatting provided by :class:`.CustomHelpFormatter`.
    - Recording whether the user specified each argument value, or whether the
      default was used, via :class:`.RecordDefaultsAction`.
    - Better bookkeeping of `argument groups
      <https://docs.python.org/3.7/library/argparse.html#argument-groups>`__,
      e.g. which arguments belong to which group.
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

    def _call_actions_on_defaults(self, namespace):
        """Subclasses of :py:class:`argparse.Action` are only called on
        user-supplied values, not default values. If the ``call_on_defaults``
        flag has been set on our custom actions, call the action on default
        values to do the same parsing for default values that we would've done
        for user input.
        """
        for act in self.iter_actions():
            if isinstance(act, RecordDefaultsAction) and act.call_on_defaults:
                values = getattr(namespace, act.dest, None)
                act(self, namespace, values, None)

    def _default_argv(self, parsed_args):
        """Utility method returning the arguments passed to the parser for
        lowest-priority defaults in
        :meth:`.MDTFArgParser.parse_known_args`.
        """
        config = CLIConfigManager()
        default_site = parsed_args.get('site', config.default_site)
        return ['--site', util.from_iter(default_site)]

    def parse_known_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args` which
        handles intermediate levels of default settings derived from the
        user's settings files. These override defaults defined in the parser
        itself. The precedence order is:

        1. Argument values explictly given by the user on the command line, as
           recorded in the ``is_default`` attribute of :class:`.MDTFArgParser`.
        2. Argument values from a file the user gave via the ``-f`` flag.
           (CLIConfigManager.defaults[DefaultsFileTypes.USER]).
        3. Argument values specified as the default values in the argument
           parser, which in turn are set with the following precedence order:

           a. Default values from a site-specfic file (defaults.jsonc), stored in
              CLIConfigManager.defaults[DefaultsFileTypes.SITE].
           b. Default values from a defaults.jsonc file in the ``/sites`` directory,
              stored in CLIConfigManager.defaults[DefaultsFileTypes.GLOBAL].
           c. Default values hard-coded in the CLI definition file itself.

        Args:
            args (optional): String or list of strings to parse. If a single
                string is passed, it's split using :meth:`split_args`.
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
        try:
            (parsed_args, remainder) = super(MDTFArgParser, self).parse_known_args(
                self.split_args(args), None
            )
        except SystemExit as exc:
            if exc.code != 0:
                # hit a parse error; include description of the source of error.
                print("Error occurred in user-supplied explict CLI flags.")
            raise
        parsed_args = _to_dict(parsed_args)
        self._set_is_default(parsed_args)
        # Highest priority: options that were explicitly set by user on CLI
        # Note that is_default[opt] = None (not True or False) if no default
        # value is defined for that option.
        user_cli_opts = {k:v for k,v in parsed_args.items() \
            if not self.is_default.get(k, True)}
        # Lowest priority: set of defaults from running parser on empty input
        try:
            parser_defaults, _ = super(MDTFArgParser, self).parse_known_args(
                self._default_argv(parsed_args), None
            )
        except SystemExit as exc:
            if exc.code != 0:
                # hit a parse error; include description of the source of error.
                print("Error occurred in CLI definitions.")
            raise
        # CLI opts override options set from file, which override defaults
        parsed_args = _to_dict(collections.ChainMap(
            user_cli_opts, config.user_defaults, vars(parser_defaults)
        ))
        if namespace is None:
            namespace = argparse.Namespace(**parsed_args)
        else:
            for k,v in parsed_args.items():
                setattr(namespace, k, v)
        self._call_actions_on_defaults(namespace)
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
    what site and plugin values were set by the user. Plugin selector arguments
    are identified by having their ``action`` set to :class:`.PluginArgAction`.
    """
    def __init__(self):
        super(MDTFArgPreparser, self).__init__(add_help=False)

    def parse_site(self, argv=None, default_site=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args`
        used to determine what site to use.
        """
        namespace = self.parse_known_args(argv)[0]
        return getattr(namespace, 'site', default_site)

    def parse_input_file(self, argv=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args`
        used to determine what user input file to use.
        """
        namespace = self.parse_known_args(argv)[0]
        return getattr(namespace, 'input_file', None)

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
    def __init__(self, code_root, skip_defaults=False, argv=None):
        _ = CLIConfigManager(code_root, skip_defaults=skip_defaults)
        self.code_root = code_root
        self.installed = False
        self.sites = []
        self.site = None
        if argv is None:
            self.argv = sys.argv[1:]
        else:
            self.argv = self.split_args(argv)

        self.file_case_list = []
        self.config = dict()
        self.log_config = dict()
        self.imports = dict()
        self.setup()

    def iter_arg_groups(self, subcommand=None):
        """Iterate over all arguments defined on the parser for the subcommand
        *subcommand*.
        """
        config = CLIConfigManager()
        if subcommand:
            subcmds = config.subcommands.get(subcommand, [])
        else:
            subcmds = list(config.subcommands.values())
        for cmd in subcmds:
            if hasattr(cmd, 'cli') and cmd.cli:
                yield from cmd.cli.argument_groups

    def iter_group_actions(self, subcommand=None, group=None):
        """Iterate over all arguments defined on the parser group *group* for the
        subcommand *subcommand*.
        """
        groups = util.to_iter(group)
        for arg_gp in self.iter_arg_groups(subcommand=subcommand):
            if groups:
                if arg_gp.title in groups:
                    yield from arg_gp.arguments
            else:
                yield from arg_gp.arguments

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
                    here. This can be a JSONC file of the form given in
                    sample_input.jsonc, or a text file containing command-line
                    arguments. Options set explicitly on the command line will
                    still override settings in this file.
                """)
            })
        target_p.add_argument('--input_file', '--input-file', '-f', **kwargs)

    def init_user_defaults(self):
        """Set user defaults using values read in from a configuration
        file in one of two formats. The format is determined from context: either

        1) A JSON/JSONC file of key-value pairs. This is parsed using
           :func:`~src.util.filesystem.parse_json`.
        2) A plain text file containing flags and arguments as they would be
           passed on the command line (except shell expansions are not performed).
           This is parsed by the :meth:`MDTFArgParser.parse_args` method of the
           configured parser.

        The file's path is determined from the argument to the ``-f`` flag via
        :meth:`MDTFArgPreparser.parse_input_file`.

        Raises:
            ValueError: if the string cannot be parsed.
        """
        config = CLIConfigManager()
        input_p = MDTFArgPreparser()
        self.add_input_file_arg(input_p)
        path = input_p.parse_input_file(self.argv)
        if not path:
            return
        try:
            with io.open(path, 'r', encoding='utf-8') as f:
                str_ = f.read()
        except Exception:
            _log.exception("Can't read user input file at %s.", path)
            raise ValueError()
        if not str_:
            return
        # try to determine if file is json
        if 'json' in os.path.splitext(path)[1].lower():
            # assume config_file a JSON dict of option:value pairs.
            try:
                d = util.parse_json(str_)
                self.file_case_list = d.pop('case_list', [])
                d = {canonical_arg_name(k): v for k,v in d.items()}
                config.user_defaults.update(d)
            except json.JSONDecodeError as exc:
                sys.exit(f"ERROR: JSON syntax error in {path}:\n\t{exc}")
            except Exception:
                _log.exception('Attempted to parse %s as JSONC; failed.', path)
                raise ValueError()
        else:
            # assume config_file is a plain text file containing flags, etc.
            # as they would be passed on the command line.
            try:
                self.argv = self.argv + shlex.split(str_, comments=True, posix=True)
            except Exception:
                _log.exception(
                    'Attempted to parse %s as shell input; failed.', path)
                raise ValueError()

    def add_site_arg(self, target_p):
        """Convenience method to add the argument flag to select which
        site-specific code to use, to the parser ``target_p`` (either the
        top-level parser, or a preparser.)
        """
        config = CLIConfigManager()
        kwargs = {'default': config.default_site, 'nargs': 1}

        if isinstance(target_p, MDTFTopLevelArgParser):
            kwargs.update({
                'choices': self.sites,
                'help': word_wrap(f"""
                    Site-specific functionality to use. Options below are
                    specific to the selected value '{self.site}'.
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
        default_site = config.site_defaults.get('site', config.default_site)

        self.sites = [d for d in os.listdir(config.sites_dir) \
            if os.path.isdir(os.path.join(config.sites_dir, d)) \
                and not d.startswith(('.','_'))]
        # TODO: if we're checking to see if installer has been run, only set
        # self.installed = True if default_site in self.sites
        self.installed = True

        site_p = MDTFArgPreparser()
        self.add_site_arg(site_p)
        site = util.from_iter(site_p.parse_site(self.argv, default_site))
        if site not in self.sites \
            and not (site == default_site and not self.installed):
            _log.critical("Requested site %s not found in sites directory %s.",
                site, config.sites_dir)
            util.exit_handler(code=2) # exit code for  CLI syntax error
        config.default_site = default_site
        config.site = site
        self.site = site
        config.read_defaults(DefaultsFileTypes.SITE)

    def add_contents(self, target_p):
        """Convenience method to fully configure a parser ``target_p`` (either
        the top-level parser, or a preparser), adding subparsers for all
        subcommands.
        """
        config = CLIConfigManager()
        self.add_site_arg(target_p)
        self.add_input_file_arg(target_p)
        assert len(config.subcommands) == 1
        cmd = tuple(config.subcommands.values())[0]
        cmd.cli.configure(target_p)

    def setup(self):
        """Method to wrap all configuration methods needed to configure the
        parser before calling :meth:`parse_args`: reading the defaults files and
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
        self.add_contents(temp_p)
        plugin_args = temp_p.parse_plugins(self.argv)
        for cmd in config.subcommands.values():
            cmd.cli.add_plugin_args(plugin_args)
        # Build the real CLI parser now that we have plugins
        self.configure()

    def configure(self):
        """Method that assembles the top-level CLI parser; called at the end of
        :meth:`setup`. Options specific to the script are hard-coded here; CLI
        options for each subcommand are given in jsonc configuration files for
        each command which are read in by :meth:`setup`. See documentation for
        :meth:`~src.cli.MDTFArgParser.parse_known_args` for information on the
        configuration file mechanism.
        """
        MDTFArgParser.__init__(self,
            prog="mdtf",
            usage="%(prog)s [options] [CASE_ROOT_DIR]",
            description=word_wrap("""
                Driver script for the NOAA Model Diagnostics Task Force (MDTF)
                package, which runs process-oriented diagnostics (PODs) on climate
                model data. See documentation at https://mdtf-diagnostics.rtfd.io.
            """),
            add_help=True,
        )
        self.add_argument(
            '--version', action="version", version="%(prog)s 3.0 beta 3"
        )
        self._optionals.title = 'GENERAL OPTIONS'
        if not self.installed:
            self.epilog=word_wrap("""
                Warning: User-customized configuration files not found. Consider
                running 'mdtf install' to configure your installation.
            """)
        self.add_contents(self)

    def parse_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_args` which
        handles intermediate levels of default settings. See documentation for
        :meth:`~src.cli.MDTFArgParser.parse_known_args`.
        """
        if args is None:
            args = self.argv
        else:
            args = self.split_args(args)
        return super(MDTFTopLevelArgParser, self).parse_args(args, namespace)

    def parse_known_args(self, args=None, namespace=None):
        """Wrapper for :py:meth:`~argparse.ArgumentParser.parse_known_args` which
        handles intermediate levels of default settings; see documentation for
        :meth:`~src.cli.MDTFArgParser.parse_known_args`.
        """
        if args is None:
            args = self.argv
        else:
            args = self.split_args(args)
        return super(MDTFTopLevelArgParser, self).parse_known_args(args, namespace)

    def dispatch(self, args=None):
        """Parse *args*, and call the subcommand that was selected.
        """
        config = CLIConfigManager()

        # finally parse the user's CLI arguments
        self.config = vars(self.parse_args(args))
        # log use of site-wide default files here (not earlier, in case user
        # just wanted --help or --version)
        defaults_text = config.site_default_text()
        if defaults_text:
            _log.info(defaults_text)
        # import plugin classes
        for act in self.iter_actions():
            if isinstance(act, ClassImportAction):
                key = act.dest
                assert key in self.config
                plugin_cmd = config.get_plugin(key, self.config[key])
                self.imports[key] = plugin_cmd.import_target()
        # multiple subcommand functionality not being used yet
        assert len(config.subcommands) == 1
        cmd = tuple(config.subcommands.values())[0]
        return cmd.call(self)


class MDTFTopLevelSubcommandArgParser(MDTFTopLevelArgParser):
    """Extends :class:`MDTFTopLevelArgParser` to add support for subcommands.
    Currently unused, intended for a future release.
    """

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

    def add_contents(self, target_p):
        """Convenience method to fully configure a parser ``target_p`` (either
        the top-level parser, or a preparser), adding subparsers for all
        subcommands.
        """
        config = CLIConfigManager()
        add_help = isinstance(target_p, MDTFTopLevelArgParser)
        self.add_site_arg(target_p)
        self.add_input_file_arg(target_p)
        sub_p = target_p.add_subparsers(**config.subparser_kwargs)
        _ = sub_p.add_parser(
            "help", help="Show this help message and exit.", add_help=add_help
        )
        for cmd in config.subcommands.values():
            cmd.parser = sub_p.add_parser(
                cmd.name, help=cmd.help, add_help=add_help,
                usage=cmd.cli.usage, description=cmd.cli.description
            )
            cmd.cli.configure(cmd.parser)

    def configure(self):
        """Method that assembles the top-level CLI parser. Options specific to
        the script are hard-coded here; CLI options for each subcommand are
        given in jsonc configuration files for each command which are read in
        here. See documentation for :meth:`~src.cli.MDTFArgParser.parse_known_args`
        for information on the configuration file mechanism.
        """
        MDTFArgParser.__init__(self,
            prog="mdtf",
            usage="%(prog)s [flags] <command> [command-specific options]",
            description=word_wrap("""
                Driver script for the NOAA Model Diagnostics Task Force (MDTF)
                package, which runs process-oriented diagnostics (PODs) on
                climate model data. See documentation at
                https://mdtf-diagnostics.rtfd.io.
            """)
        )
        self.add_argument(
            '--version', action="version", version="%(prog)s 3.0 beta 3"
        )
        self._optionals.title = 'GENERAL OPTIONS'
        if not self.installed:
            self.epilog=word_wrap("""
                Warning: User-customized configuration files not found. Consider
                running 'mdtf install' to configure your installation.
            """)
        self.add_contents(self)

    def dispatch(self):
        raise NotImplementedError()
