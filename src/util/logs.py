"""Utilities related to configuration and handling of framework logging.
"""
import os
import sys
import argparse
import datetime
import io
import subprocess
import signal
import traceback

from . import basic, exceptions

import logging
import logging.config
import logging.handlers
_log = logging.getLogger(__name__)

class MDTFConsoleHandler(logging.StreamHandler):
    """Dummy class to designate logging to stdout or stderr from the root logger.
    """
    pass

class StringIOHandler(logging.StreamHandler):
    """:py:class:`~logging.StreamHandler` instance that writes log entries to
    an internal :py:class:`~io.StringIO` buffer.
    """
    def __init__(self):
        self._log_buffer = io.StringIO()
        super(StringIOHandler, self).__init__(stream=self._log_buffer)

    def reset_buffer(self):
        # easier to create a new buffer than reset the existing one
        new_buffer = io.StringIO()
        old_buffer = self.setStream(new_buffer)
        old_buffer.close()
        self._log_buffer = new_buffer

    def close(self):
        super(StringIOHandler, self).close()
        self._log_buffer.close()

    def buffer_contents(self):
        """Return contents of buffer as a string."""
        return self._log_buffer.getvalue()

class MultiFlushMemoryHandler(logging.handlers.MemoryHandler):
    """Subclass :py:class:`~logging.handlers.MemoryHandler` to enable flushing
    the contents of its log buffer to multiple targets. We do this to solve the
    chicken-and-egg problem of logging any events that happen before the log
    outputs are configured: those events are captured by an instance of this
    handler and then transfer()'ed to other handlers once they're set up.
    See `<https://stackoverflow.com/a/12896092>`__.
    """

    def transfer(self, target_handler):
        """Transfer contents of buffer to target_handler.

        Args:
            target_handler (:py:class:`~logging.Handler`): log handler to transfer
                contents of buffer to.
        """
        self.acquire()
        try:
            self.setTarget(target_handler)
            if self.target:
                for record in self.buffer:
                    if self.target.level <= record.levelno:
                        self.target.handle(record)
                # self.buffer = [] # don't clear buffer!
        finally:
            self.release()

    def transfer_to_non_console(self, logger):
        """Transfer contents of buffer to all non-console-based handlers attached
        to *logger* (handlers that aren't :py:class:`MDTFConsoleHandler`.)

        If no handlers are attached to the logger, a warning is printed and the
        buffer is transferred to the :py:class:`~logging.lastResort` handler, i.e.
        printed to stderr.

        Args:
            logger (:py:class:`~logging.Logger`): logger to transfer
                contents of buffer to.
        """
        no_transfer_flag = True
        for h in logger.handlers:
            if not isinstance(h, (MultiFlushMemoryHandler, MDTFConsoleHandler)):
                self.transfer(h)
                no_transfer_flag = False
        if no_transfer_flag:
            logger.warning("No non-console loggers configured.")
            self.transfer(logging.lastResort)

class HeaderFileHandler(logging.FileHandler):
    """Subclass :py:class:`~logging.FileHandler` to print system and git repo
    information in a header at the start of a log file without writing it to
    other loggers (e.g. the console.)
    """
    def _log_header(self):
        return ""

    def _open(self):
        """Write header information right after we open the log file, then
        proceed normally.
        """
        fp = super(HeaderFileHandler, self)._open()
        fp.write(self._log_header())
        return fp

class MDTFHeaderFileHandler(HeaderFileHandler):
    """:py:class:`~logging.FileHandler` which adds a header to log files with
    system information, git repo status etc. provided by :func:`mdtf_log_header`.
    """
    def _log_header(self):
        return mdtf_log_header("MDTF PACKAGE LOG")

def _hanging_indent(str_, initial_indent, subsequent_indent):
    """Poor man's indenter. Easier than using textwrap for this case.

    Args:
        str_ (str): String to be indented.
        initial_indent (str): string to insert as the indent for the first
            line.
        subsequent_indent (str): string to insert as the indent for all
            subsequent lines.

    Returns:
        Indented string.
    """
    if isinstance(initial_indent, int):
        initial_indent = initial_indent * ' '
    if isinstance(subsequent_indent, int):
        subsequent_indent = subsequent_indent * ' '
    lines_ = str_.splitlines()
    lines_out = []
    if len(lines_) > 0:
        lines_out = lines_out + [initial_indent + lines_[0]]
    if len(lines_) > 1:
        lines_out = lines_out + [(subsequent_indent+l) for l in lines_[1:]]
    return '\n'.join(lines_out)

class HangingIndentFormatter(logging.Formatter):
    """:py:class:`~logging.Formatter` that applies a hanging indent, making it
    easier to tell where one entry stops and the next starts.
    """
    # https://blog.belgoat.com/python-textwrap-wrap-your-text-to-terminal-size/
    def __init__(self, fmt=None, datefmt=None, style='%', tabsize=0, header="", footer=""):
        """Initialize formatter with extra arguments.

        Args:
            fmt (str): format string, as in :py:class:`~logging.Formatter`.
            datefmt (str): date format string, as in :py:class:`~logging.Formatter`
                or `strftime <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`__.
            style (str): string templating style, as in :py:class:`~logging.Formatter`.
            tabsize (int): Number of spaces to use for hanging indent.
            header (str): Optional constant string to prepend to each log entry.
            footer (str): Optional constant string to append to each log entry.
        """
        super(HangingIndentFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.indent = 4
        self.stack_indent = self.indent
        self.header = str(header)
        self.footer = str(footer)

    def format(self, record):
        """Format the specified :py:class:`~logging.LogRecord` as text, adding
        indentation and header/footer.

        Args:
            record (:py:class:`~logging.LogRecord`): Logging record object
                to be formatted.

        Returns:
            String representation of the log entry.

        This essentially repeats the method's `implementation
        <https://github.com/python/cpython/blob/4e02981de0952f54bf87967f8e10d169d6946b40/Lib/logging/__init__.py#L595-L625>`__
        in the python standard library. See comments there and the logging module
        `documentation <https://docs.python.org/3.7/library/logging.html>`__.
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        # indent the text of the log message itself
        s = _hanging_indent(s, 0, self.indent)
        if self.header:
            s = self.header + s

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # text from formatting the exception. NOTE that this includes the
            # stack trace without populating stack_info or calling formatStack.
            if not s.endswith('\n'):
                s = s + '\n'
            s = s + _hanging_indent(
                record.exc_text,
                self.indent, self.stack_indent
            )
        if record.stack_info:
            # stack_info apparently only used if our format string (ie, 'fmt' in
            # init) requests a stack trace?
            if not s.endswith('\n'):
                s = s + '\n'
            s = s + _hanging_indent(
                self.formatStack(record.stack_info),
                self.stack_indent, self.stack_indent
            )
        if self.footer:
            s = s + self.footer
        return s

class _LevelFilterBase(logging.Filter):
    """Base class to implement common features of level-based filters."""
    def __init__(self, name="", level=None):
        super(_LevelFilterBase, self).__init__(name=name)
        if level is None:
            level = logging.NOTSET
        if not isinstance(level, int):
            if hasattr(logging, str(level)):
                level = getattr(logging, str(level))
            else:
                level = int(level)
        self.levelno = level

class GeqLevelFilter(_LevelFilterBase):
    """:py:class:`~logging.Filter` to include only log messages with a severity of
    *level* or worse. This is normally done by setting the *level* attribute on a
    :py:class:`~logging.Handler`, but we need to add a filter when transferring
    records from another logger (the :class:`MultiFlushMemoryHandler` cache), as
    shown in `<https://stackoverflow.com/a/24324246>`__.
    """
    def filter(self, record):
        return record.levelno >= self.levelno

class LtLevelFilter(_LevelFilterBase):
    """:py:class:`~logging.Filter` to include only log messages with a severity
    less than *level*.
    """
    def filter(self, record):
        return record.levelno < self.levelno

class EqLevelFilter(_LevelFilterBase):
    """:py:class:`~logging.Filter` to include only log messages with a severity
    equal to *level*.
    """
    def filter(self, record):
        return record.levelno == self.levelno

class NameMatchFilter(logging.Filter):
    """:py:class:`~logging.Filter` that only accepts log events directed to it
    specifically, rejecting all events coming from child loggers.

    Intended to be attached to a handler -- the effect of attaching this to a
    logger is the same as setting *propagate* = False on it.
    """
    def __init__(self, name=""):
        super(NameMatchFilter, self).__init__()
        self._name = name

    def filter(self, record):
        return (record.name == self._name)

OBJ_LOG_TAG_ATTR_NAME = 'tags'

class TagMatchFilter(logging.Filter):
    """:py:class:`~logging.Filter` which only accepts records having the
    designated combination of custom 'tag' attributes. These are assigned by the
    methods in :class:`MDTFObjectLogger` or can be passed via the 'extra' kwarg
    on any logger (see discussion in entry for
    `~logging.Logger
    <https://docs.python.org/3.7/library/logging.html#logging.Logger.debug>`__.)
    """
    def __init__(self, name="", tags=None):
        super(TagMatchFilter, self).__init__(name=name)
        self._tags = basic.to_iter(tags, set)

    def filter(self, record):
        if not hasattr(record, OBJ_LOG_TAG_ATTR_NAME):
            return False
        tags = basic.to_iter(record.tags, set)
        return self._tags.issubset(tags)

# ------------------------------------------------------------------------------

# standardize
OBJ_LOG_ROOT = 'MDTF' # "root logger" of the object logger hierarchy
ObjectLogTag = basic.MDTFEnum(
    "ObjectLogTag",
    "NC_HISTORY BANNER IN_FILE OUT_FILE",
    module=__name__
)
ObjectLogTag.__doc__ = """Standardized values that the MDTF-defined *tags*
attribute on :py:class:`~logging.LogRecord` objects can take, and that
:class:`TagMatchFilter` can listen for. These specify different destinations for
the logging events.
"""

class MDTFObjectLogger(logging.Logger):
    """This class wraps functionality for use by :class:`MDTFObjectLoggerMixin`
    for log record-keeping by objects in the object hierarchy:

    - A :py:class:`~logging.Logger` to record events affecting the parent object
      only. This logger does not propagate events up the log hierarchy: the
      module-level logger should be used if that functionality is desired.
    - A queue (*\_exceptions*) for holding :py:class:`Exception` objects received
      by the parent object.
    """
    def __init__(self, name):
        super(MDTFObjectLogger, self).__init__(name)
        self._exceptions = []
        self._tracebacks = []

    def log(self, level, msg, *args, **kw):
        # add "tags" attribute to all emitted LogRecords
        if 'extra' not in kw:
            kw['extra'] = dict()
        kw['extra'][OBJ_LOG_TAG_ATTR_NAME] = basic.to_iter(
            kw['extra'].get(OBJ_LOG_TAG_ATTR_NAME, None), set
        )
        if OBJ_LOG_TAG_ATTR_NAME in kw:
            kw['extra'][OBJ_LOG_TAG_ATTR_NAME].update(
                basic.to_iter(kw[OBJ_LOG_TAG_ATTR_NAME])
            )
            del kw[OBJ_LOG_TAG_ATTR_NAME]
        super(MDTFObjectLogger, self).log(level, msg, *args, **kw)

    # wrap convenience methods
    # nb: typo in https://github.com/python/cpython/blob/3.7/Lib/logging/__init__.py line 1407
    def debug(self, msg, *args, **kw):
        self.log(logging.DEBUG, msg, *args, **kw)

    def info(self, msg, *args, **kw):
        self.log(logging.INFO, msg, *args, **kw)

    def warning(self, msg, *args, **kw):
        self.log(logging.WARNING, msg, *args, **kw)

    def error(self, msg, *args, **kw):
        self.log(logging.ERROR, msg, *args, **kw)

    def critical(self, msg, *args, **kw):
        self.log(logging.CRITICAL, msg, *args, **kw)

    def exception(self, msg, *args, exc_info=True, **kw):
        if exc_info:
            exc_type, _, _ = sys.exc_info()
            if issubclass(exc_type, exceptions.MDTFEvent):
                # "exception" isn't an exception, just an event, so log with
                # severity info
                self.log(logging.INFO, msg, *args, exc_info=False, **kw)
                return
        self.log(logging.ERROR, msg, *args, exc_info=exc_info, **kw)

    # exception object storage
    @property
    def has_exceptions(self):
        """Return boolean corresponding to whether this object has received any
        exceptions (via :meth:`store_exception`.)
        """
        return (len(self._exceptions) > 0)

    def store_exception(self, exc):
        """Add an Exception object *exc* to the internal list.
        """
        self._exceptions.append(exc)
        tb_exc = traceback.TracebackException(*(sys.exc_info()))
        self._tracebacks.append(tb_exc)

    @classmethod
    def get_logger(cls, log_name):
        """Workaround for setting the logger class, since logger objects have
        global state (calling getLogger with the same name returns the same
        object, like a Singleton.)
        """
        old_log_class = logging.getLoggerClass()
        logging.setLoggerClass(cls)
        log = logging.getLogger(log_name)
        logging.setLoggerClass(old_log_class)
        # default settings
        log.propagate = True
        log.setLevel(logging.NOTSET)
        return log

class MDTFObjectLoggerMixinBase():
    """Dummy base class acting as a parent for all logging mixin classes for
    elements of the object hierarchy.
    """
    pass

class MDTFObjectLoggerMixin(MDTFObjectLoggerMixinBase):
    """Base class to implement per-object logging for objects in the object hierarchy.
    Based on `<https://stackoverflow.com/q/57813096>`__.

    This wraps related functionalities:

    - A :py:class:`~logging.Logger` to record events affecting the object
      only. Log messages are cached in a :py:class:`~io.StringIO` buffer.
    - A method :meth:`~MDTFObjectLogger.format` for formatting the contents of
      the above into a string, along with log messages of any child objects.
      This is intended for preparing per-POD and per-case log files; logging
      intended for the console should use the module loggers.
    """
    def init_log(self, fmt=None):
        """Logger initialization. This is a mixin class, so we don't define a
        ``__init__`` method for simplicity.
        """
        if fmt is None:
            fmt = '%(levelname)s: %(message)s'

        assert hasattr(self, 'log')
        self._log_handler = StringIOHandler()
        # don't record events from children in StringIO buffer
        self._log_handler.addFilter(NameMatchFilter(self._log_name))
        formatter = logging.Formatter(fmt=fmt, datefmt='%H:%M:%S')
        self._log_handler.setFormatter(formatter)
        self.log.addHandler(self._log_handler)

        self.init_extra_log_handlers()

    def init_extra_log_handlers(self):
        """Hook used by child classes to add class-specific log handlers.
        """
        pass

    @property
    def last_exception(self):
        """Return most recent Exception received by the object.
        """
        if self.log.has_exceptions:
            return self.log._exceptions[-1]
        else:
            return None

    def format_log(self, children=True):
        """Return contents of log buffer, as well as that of any child objects
        in *child_objs*, as a formatted string.
        """
        if hasattr(self, 'debug_str'):
            str_ = f"Log for variable {self.debug_str()}\n"
        else:
            str_ = f"Log for {self.full_name}:\n"
        # list exceptions before anything else:
        if self.log.has_exceptions:
            exc_strs = [''.join(exc.format()) for exc in self.log._tracebacks]
            exc_strs = [f"*** caught exception (#{i+1}):\n{exc}" \
                for i, exc in enumerate(exc_strs)]
            str_ += "".join(exc_strs) + '\n'
        # then log contents:
        str_ += self._log_handler.buffer_contents().rstrip()
        # then contents of children:
        if children:
            str_ += '\n'
            for child in self.iter_children():
                str_ += '\n'
                if hasattr(child, 'format_log'):
                    str_ += child.format_log(children=children)
                else:
                    str_ += f"<{child} log placeholder>\n"
        return _hanging_indent(str_, 0, 4) + '\n'

class VarlistEntryLoggerMixin(MDTFObjectLoggerMixin):
    """Mixin providing per-object logging for :class:`~diagnostic.VarlistEntry`.
    """
    def init_extra_log_handlers(self):
        # add extra handler for additions to netCDF history attribute
        self._nc_history_log = StringIOHandler()
        self._nc_history_log.addFilter(TagMatchFilter(tags=ObjectLogTag.NC_HISTORY))
        formatter = logging.Formatter(
            fmt='%(asctime)s: MDTF package: %(message)s',
            datefmt='%a %b %d %H:%M:%S %Y' # mimic date format used by NCO, CDO
        )
        self._nc_history_log.setFormatter(formatter)
        self.log.addHandler(self._nc_history_log)

class _CaseAndPODHandlerMixin():
    """Common methods for providing per-object logging for
    :class:`PODLoggerMixin` and :class:`CaseLoggerMixin`.
    """
    def init_extra_log_handlers(self):
        # add handler for warning banner
        self._banner_log = StringIOHandler()
        self._banner_log.addFilter(TagMatchFilter(tags=ObjectLogTag.BANNER))
        formatter = logging.Formatter(
            fmt='%(levelname)s: %(message)s', datefmt='%H:%M:%S'
        )
        self._banner_log.setFormatter(formatter)
        self.log.addHandler(self._banner_log)

        # add handlers for log of data files used
        formatter = logging.Formatter(fmt='%(message)s', datefmt='%H:%M:%S')
        self._in_file_log = StringIOHandler()
        self._in_file_log.addFilter(TagMatchFilter(tags=ObjectLogTag.IN_FILE))
        self._in_file_log.setFormatter(formatter)
        self.log.addHandler(self._in_file_log)
        self._out_file_log = StringIOHandler()
        self._out_file_log.addFilter(TagMatchFilter(tags=ObjectLogTag.OUT_FILE))
        self._out_file_log.setFormatter(formatter)
        self.log.addHandler(self._out_file_log)

class PODLoggerMixin(_CaseAndPODHandlerMixin, MDTFObjectLoggerMixin):
    """Mixin providing per-object logging for :class:`~diagnostic.Diagnostic`
    (POD objects.)
    """
    pass

class CaseLoggerMixin(_CaseAndPODHandlerMixin, MDTFObjectLoggerMixinBase):
    """Mixin providing per-object logging for :class:`~data_manager.DataSourceBase`
    (case objects, corresponding to experiments.)
    """
    def init_log(self, log_dir, fmt=None):
        # Mixin class, so no __init__ for simplicity
        # NB: no super(); redefining the method
        if fmt is None:
            fmt = ("%(asctime)s %(levelname)s: %(funcName)s (%(filename)s line "
                "%(lineno)d):\n%(message)s")

        assert hasattr(self, 'log')
        self.log.propagate = True
        self.log.setLevel(logging.DEBUG)
        if self.log.hasHandlers():
            for handler in self.log.handlers:
                self.log.removeHandler(handler)
        self._log_handler = MDTFHeaderFileHandler(
            filename=os.path.join(log_dir, f"{self.name}.log"),
            mode="w", encoding="utf-8"
        )
        formatter = HangingIndentFormatter(
            fmt=fmt, datefmt='%H:%M:%S',
            header="", footer="\n"
        )
        self._log_handler.setFormatter(formatter)
        self.log.addHandler(self._log_handler)

        self.init_extra_log_handlers()

        # transfer stuff from root logger cache
        transfer_log_cache(self.log, close=False)

    def close_log_file(self, log=True):
        self._log_handler.close()
        self._log_handler = None

# ------------------------------------------------------------------------------

def git_info():
    """Get the current git branch, hash, and list of uncommitted files, if
    available. Based on NumPy's implementation: `<https://stackoverflow.com/a/40170206>`__.
    """
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = os.environ.copy()
        env.update({'LANGUAGE':'C', 'LANG':'C', 'LC_ALL':'C'})
        try:
            out = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env
            ).communicate()[0]
        except subprocess.CalledProcessError:
            out = ''
        return out.strip().decode('utf-8')

    git_branch = ""
    git_hash = ""
    git_dirty = ""
    try:
        git_branch = _minimal_ext_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        git_hash = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        git_dirty = _minimal_ext_cmd(['git', 'diff', '--no-ext-diff', '--name-only'])
    except OSError:
        pass

    if git_dirty:
        git_dirty = git_dirty.splitlines()
    elif git_hash:
        git_dirty = "<none>"
    else:
        git_dirty = "<couldn't get uncomitted files>"
    if not git_branch:
        git_branch = "<no branch>"
    if not git_hash:
        git_hash = "<couldn't get git hash>"
    return (git_branch, git_hash, git_dirty)

def mdtf_log_header(title):
    """Returns string of system debug information to use as log file header.
    Calls :func:`git_info` to get repo status.
    """
    try:
        git_branch, git_hash, _ = git_info()
        str_ = (
            f"{title}\n\n"
            f"Started logging at {datetime.datetime.now()}\n"
            f"git hash/branch: {git_hash} (on {git_branch})\n"
            # f"uncommitted files: {git_dirty}\n"
            f"sys.platform: '{sys.platform}'\n"
            # f"sys.executable: '{sys.executable}'\n"
            f"sys.version: '{sys.version}'\n"
            # f"sys.path: {sys.path}\nsys.argv: {sys.argv}\n"
        )
    except Exception:
        err_str = "Couldn't gather log file header information."
        _log.exception(err_str)
        str_ = f"ERROR: {err_str}\n"
    return str_ + (80 * '-') + '\n\n'

def signal_logger(caller_name, signum=None, frame=None, log=_log):
    """Lookup signal name from number and write to log. Taken from
    `<https://stackoverflow.com/a/2549950>`__.

    Args:
        caller_name (str): Calling function name, only used in log message.
        signum: Signal number of the signal we recieved.
        frame: Parameters of the signal we recieved.
    """
    if signum:
        sig_lookup = {
            k:v for v, k in reversed(sorted(list(signal.__dict__.items()))) \
                if v.startswith('SIG') and not v.startswith('SIG_')
        }
        log.info(
            "%s caught signal %s (%s)",
            caller_name, sig_lookup.get(signum, 'UNKNOWN'), signum
        )
    else:
        log.info("%s caught unknown signal.", caller_name)

def _set_excepthook(root_logger):
    """Ensure all uncaught exceptions, other than user KeyboardInterrupt, are
    logged to the root logger.

    See `<https://docs.python.org/3/library/sys.html#sys.excepthook>`__.
    """
    def uncaught_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Skip logging for user interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root_logger.critical(
            (70*'*') + "\nUncaught exception:\n", # banner so it stands out
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = uncaught_exception_handler

def _configure_logging_dict(log_d, log_args):
    """Convert CLI flags (``--verbose``/``--quiet``) into log levels. Configure
    log level and filters on console handlers in a logging config dictionary.
    """
    # smaller number = more verbose
    level = getattr(log_args, 'quiet', 0) - getattr(log_args, 'verbose', 0)
    if level <= 1:
        stderr_level = logging.WARNING
    elif level == 2:
        stderr_level = logging.ERROR
    else:
        stderr_level = logging.CRITICAL
    log_d['filters'] = {
        "stderr_filter": {"()": GeqLevelFilter, "level": stderr_level},
        "stdout_filter": {"()": EqLevelFilter, "level": logging.INFO},
        "debug_filter": {"()": LtLevelFilter, "level": logging.INFO}
    }
    for h in ('stderr', 'stdout', 'debug'):
        if h in log_d['handlers']:
            log_d['handlers'][h]['filters'] = [h+'_filter']
    if 'stderr' in log_d['handlers']:
        log_d['handlers']['stderr']['level'] = stderr_level

    if level <= -2:
        for d in log_d['handlers'].values():
            d['formatter'] = 'debug'
    if level == 0:
        del log_d['handlers']['debug']
        log_d['root']['handlers'] = ["stdout", "stderr"]
    elif level == 1:
        del log_d['handlers']['debug']
        del log_d['handlers']['stdout']
        log_d['root']['handlers'] = ["stderr"]
    return log_d

def initial_log_config():
    """Configure the root logger for logging to console and to a cache provided
    by :class:`MultiFlushMemoryHandler`.

    This is temporary logging configuration, used to solve the chicken-and-egg
    problem of logging any problems that happen before we've set up logging
    according to the user's log config files, which requires doing a full parse
    of the user input. Once this is set up, any messages in the cache are sent
    to the user-configured logs.
    """
    logging.captureWarnings(True)
    # log uncaught exceptions
    root_logger = logging.getLogger()
    _set_excepthook(root_logger)

    log_d = {
        "version": 1,
        "disable_existing_loggers": True,
        "root": {
            "level": "NOTSET",
            "handlers": ["debug", "stdout", "stderr", "cache"]
        },
        "handlers": {
            "debug": {
                "()": "src.util.logs.MDTFConsoleHandler",
                "formatter": "level",
                "level": logging.DEBUG,
                "stream": "ext://sys.stdout"
            },
            "stdout": {
                "()": "src.util.logs.MDTFConsoleHandler",
                "formatter": "normal",
                "level": logging.INFO,
                "stream": "ext://sys.stdout"
            },
            "stderr": {
                "()": "src.util.logs.MDTFConsoleHandler",
                "formatter": "level",
                "level": logging.WARNING,
                "stream": "ext://sys.stderr"
            },
            "cache": {
                "()": "src.util.logs.MultiFlushMemoryHandler",
                "level": logging.NOTSET,
                "capacity": 8*1024,
                "flushOnClose": False
            }
        },
        "formatters": {
            "normal": {"format": "%(message)s"},
            "level": {"format": "%(levelname)s: %(message)s"},
            "debug": {
                "()": HangingIndentFormatter,
                "format": ("%(levelname)s in %(funcName)s() (%(filename)s line "
                    "%(lineno)d):\n%(message)s"),
                "tabsize": 4,
                "footer": "\n"
            }
        }
    }
    log_parser = argparse.ArgumentParser(add_help=False)
    log_parser.add_argument('--verbose', '-v', default=0, action="count")
    log_parser.add_argument('--quiet', '-q', default=0, action="count")
    log_args, _ = log_parser.parse_known_args()

    log_d = _configure_logging_dict(log_d, log_args)
    logging.config.dictConfig(log_d)
    root_logger.debug('Console loggers configured.')

def transfer_log_cache(target_log=None, close=False):
    """Transfer the contents of the root log cache
    (:class:`MultiFlushMemoryHandler`) to logs on newly-configured objects.
    """
    root_logger = logging.getLogger()
    cache_idx = [i for i,handler in enumerate(root_logger.handlers) \
        if isinstance(handler, MultiFlushMemoryHandler)]
    if len(cache_idx) > 0:
        temp_log_cache = root_logger.handlers[cache_idx[0]]
        if target_log is not None:
            try:
                temp_log_cache.transfer_to_non_console(target_log)
            except Exception:
                root_logger.debug("Couldn't transfer log to '%s'.", target_log.name)
        if close:
            # delete it
            temp_log_cache.close()
            root_logger.removeHandler(temp_log_cache)
