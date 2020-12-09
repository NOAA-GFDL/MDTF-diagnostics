"""Utilities related to configuration and handling of framework logging.
"""
import os
import sys
import datetime
import subprocess
import signal
import logging
import logging.config
import logging.handlers

from .filesystem import read_json

_log = logging.getLogger(__name__)

class MultiFlushMemoryHandler(logging.handlers.MemoryHandler):
    """Subclass :py:class:`logging.handlers.MemoryHandler` to enable flushing
    the contents of its log buffer to multiple targets. We do this to solve the 
    chicken-and-egg problem of logging any events that happen before the log 
    outputs are configured: those events are captured by an instance of this 
    handler and then transfer()'ed to other handlers once they're set up.
    See `https://stackoverflow.com/a/12896092`__.
    """

    def transfer(self, target_handler):
        """Transfer contents of buffer to target_handler.
        
        Args:
            target_handler (:py:class:`logging.Handler`): log handler to transfer
                contents of buffer to.
        """
        self.acquire()
        try:
            self.setTarget(target_handler)
            if self.target:
                for record in self.buffer:
                    self.target.handle(record)
                # self.buffer = [] # don't clear buffer!
        finally:
            self.release()

    def transfer_to_all(self, logger):
        """Transfer contents of buffer to all handlers attached to logger.

        If no handlers are attached to the logger, a warning is printed and the
        buffer is transferred to the :py:data:`logging.lastResort` handler, i.e.
        printed to stderr.
        
        Args:
            logger (:py:class:`logging.Logger`): logger to transfer
                contents of buffer to.
        """
        no_transfer_flag = True
        for handler in logger.handlers:
            if handler is not self:
                self.transfer(handler)
                no_transfer_flag = False
        if no_transfer_flag:
            logger.warning("No loggers configured.")
            self.transfer(logging.lastResort)


class DebugHeaderFileHandler(logging.FileHandler):
    """Subclass :py:class:`logging.FileHandler` to print system information to
    start of file without writing it to other loggers.
    """
    def _debug_header(self):
        """Returns string of system debug information to use as log file header.
        Calls :func:`git_info`.
        """
        try:
            (git_branch, git_hash, git_dirty) = git_info()
            str_ = (
            "Started logging at {0}\n"
            "git hash/branch: {1} (on {2})\n"
            "uncommitted files: {3}\n"
            "sys.platform: '{4}'\nsys.executable: '{5}'\nsys.version: '{6}'\n"
            "sys.path: {7}\nsys.argv: {8}\n").format(
                datetime.datetime.now(), 
                git_hash, git_branch,
                git_dirty,
                sys.platform, sys.executable, sys.version, 
                sys.path, sys.argv
            ) + (80 * '-') + '\n\n'
            return str_
        except Exception as exc:
            print(exc)
            return "ERROR: couldn't gather header information.\n"
    
    def _open(self):
        """Write header information right after we open the log file, then
        proceed normally.
        """
        fp = super(DebugHeaderFileHandler, self)._open()
        fp.write(self._debug_header())
        return fp


class HangingIndentFormatter(logging.Formatter):
    """:py:class:`logging.Formatter` that applies a hanging indent, making it 
    easier to tell where one entry stops and the next starts.
    """
    # https://blog.belgoat.com/python-textwrap-wrap-your-text-to-terminal-size/
    def __init__(self, fmt=None, datefmt=None, style='%', tabsize=0, header="", footer=""):
        """Initialize formatter with extra arguments.

        Args:
            fmt (str): format string, as in :py:class:`logging.Formatter`.
            datefmt (str): date format string, as in :py:class:`logging.Formatter`
                or `strftime <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`__.
            style (str): string templating style, as in :py:class:`logging.Formatter`.
            tabsize (int): Number of spaces to use for hanging indent.
            header (str): Optional constant string to prepend to each log entry.
            footer (str): Optional constant string to append to each log entry.
        """
        super(HangingIndentFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.indent = (tabsize * ' ')
        self.stack_indent = self.indent + '|'
        self.header = str(header)
        self.footer = str(footer)

    @staticmethod
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
        lines_ = str_.splitlines()
        lines_out = []
        if len(lines_) > 0:
            lines_out = lines_out + [initial_indent + lines_[0]]
        if len(lines_) > 1:
            lines_out = lines_out + [(subsequent_indent+l) for l in lines_[1:]]
        return '\n'.join(lines_out)

    def format(self, record):
        """Format the specified :py:class:`logging.LogRecord` as text, adding
        indentation and header/footer.

        Args:
            record (:py:class:`logging.LogRecord`): logging record to be formatted.

        Returns:
            String representation of the log entry.

        This essentially repeats the method's `implementation 
        <https://github.com/python/cpython/blob/4e02981de0952f54bf87967f8e10d169d6946b40/Lib/logging/__init__.py#L595-L625>`__
        in the python standard library. See comments there and the `documentation
        <https://docs.python.org/3.7/library/logging.html>`__ for :py:module:`logging`.
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        # indent the text of the log message itself
        s = self._hanging_indent(s, '', self.indent)
        if self.header:
            s = self.header + s

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # text from formatting the exception. NOTE that this includes the 
            # stack trace without populating stack_info or calling formatStack.
            if not s.endswith('\n'):
                s = s + '\n'
            s = s + self._hanging_indent(
                record.exc_text, 
                self.indent, self.stack_indent
            )
        if record.stack_info:
            # stack_info apparently only used if our format string (ie, 'fmt' in
            # init) requests a stack trace?
            if not s.endswith('\n'):
                s = s + '\n'
            s = s + self._hanging_indent(
                self.formatStack(record.stack_info),
                self.stack_indent, self.stack_indent
            )
        if self.footer:
            s = s + self.footer
        return s


class GeqLevelFilter(logging.Filter):
    """:py:class:`logging.Filter` to include only log messages with a severity of
    level or worse. This is normally done by setting the level attribute on a
    :py:class:`logging.Handler`, but we need to add a filter when transferring
    records from another logger, as shown in 
    `https://stackoverflow.com/a/24324246`__."""
    def __init__(self, name="", level=None):
        super(GeqLevelFilter, self).__init__(name=name)
        if level is None:
            level = logging.NOTSET
        if not isinstance(level, int):
            if hasattr(logging, str(level)):
                level = getattr(logging, str(level))
            else:
                level = int(level)
        self.levelno = level

    def filter(self, record):
        return record.levelno >= self.levelno

class LtLevelFilter(logging.Filter):
    """:py:class:`logging.Filter` to include only log messages with a severity 
    less than level.
    """
    def __init__(self, name="", level=None):
        super(LtLevelFilter, self).__init__(name=name)
        if level is None:
            level = logging.NOTSET
        if not isinstance(level, int):
            if hasattr(logging, str(level)):
                level = getattr(logging, str(level))
            else:
                level = int(level)
        self.levelno = level

    def filter(self, record):
        return record.levelno < self.levelno


def git_info():
    """Get the current git branch, hash, and list of uncommitted files, if 
    available.

    Called by :meth:`DebugHeaderFileHandler._debug_header`. Based on NumPy's 
    implementation: `https://stackoverflow.com/a/40170206`__.
    """
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {'LANGUAGE':'C', 'LANG':'C', 'LC_ALL':'C'}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
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

# ------------------------------------------------------------------------------

def signal_logger(log, caller_name, signum=None, frame=None):
    """Lookup signal name from number and write to log.
    
    Taken from `<https://stackoverflow.com/a/2549950>`__.

    Args:
        log (:py:class:`logging.Logger`): Log to write information to.
        caller_name (str): Calling function name, only used in log message.
        signum, frame: parameters of the signal we recieved.
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
        # log.debug("%s frame: %s", caller_name, frame)

def _set_excepthook(root_logger):
    """Ensure all uncaught exceptions, other than user KeyboardInterrupt, are 
    logged to the root logger.

    See `https://docs.python.org/3/library/sys.html#sys.excepthook`__.
    """
    def _handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Skip logging for user interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root_logger.critical(
            (80*'*') + "\nUncaught exception:", # banner so it stands out 
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = _handle_uncaught_exception

def _level_from_cli(cli_d = None):
    """Convert CLI flags (``--verbose``/``--quiet``) into log levels for 
    :func:`_set_console_log_level`.

    Args: 
        cli_d (dict): Dict of parsed CLI settings, in particular 'verbose'/'quiet'.

    Returns: 
        Tuple of log levels for stdout loggers and stderr loggers, respectively.
    """
    # default case: INFO to stdout, WARNING and ERROR to stderr
    default_ = (logging.INFO, logging.WARNING)

    if not cli_d:
        _log.error("CLI dict not set, using default verbosity.")
        return default_
    elif not (cli_d.get('verbose',0) or cli_d.get('quiet',0)):
        return default_
    elif cli_d.get('verbose',0) >= 1:
        return (logging.DEBUG, logging.WARNING)
    elif cli_d.get('quiet',0) >= 1:
        return (None, logging.WARNING)
    elif cli_d.get('quiet',0) >= 2:
        return (None, logging.ERROR)
    elif cli_d.get('quiet',0) >= 3:
        return (None, None)
    else:
        _log.warning("Couldn't parse log verbosity, using defaults.")
        return default_

def _set_console_log_level(d, stdout_level, stderr_level, filter_=True):
    """Configure log levels for handlers writing to stdout and stderr.

    Levels are asummed to follow Python's numerical scale; see 
    `https://docs.python.org/3.7/library/logging.html#logging-levels`__.

    Args:
        d (dict): Nested dict read from the log configuration file.
        stdout_level (int): New log level to impose on handlers writing to stdout.
            If 'None', deactivates these handlers.
        stderr_level (int): New log level to impose on handlers writing to stderr.
            If 'None', deactivates these handlers.
        filter_ (bool, default True): If true, apply :py:class:`logging.Filter`s
            to ensure that every log message is written to at most one of stdout
            or stderr (in standard usage, this means errors are written to stderr
            only).
    """
    def _set_handler_level(dd, type_, new_lev, new_filt):
        if 'handlers' not in d or 'root' not in d:
            _log.warning('No loggers configured.')
            return
        handlers = d['handlers']
        type_handlers = [hk for (hk, hv) in handlers.items() \
            if hv.get('stream','').lower().endswith(type_)]
        print('#', type_, type_handlers)
        if len(type_handlers) > 1:
            _log.warning('More than one handler using %s: %s', type_, type_handlers)
        if new_lev is None:
            _log.debug('Logging to %s suppressed.', type_)
            for hk in type_handlers:
                del handlers[hk]
            new_root_handlers = set(d['root'].get('handlers', []))
            d['root']['handlers'] = list(new_root_handlers.difference(type_handlers))
        else:
            for hk in type_handlers:
                handlers[hk]['level'] = new_lev
                if new_filt:
                    _ = handlers[hk].setdefault('filters', [])
                    handlers[hk]['filters'].append(new_filt)

    if filter_ and stdout_level is not None and stderr_level is not None:
        filter_lev = max(stdout_level, stderr_level)
        _ = d.setdefault('filters', dict())
        d['filters'].update({
            "_geq_level_filter": {"()": GeqLevelFilter, "level": filter_lev},
            "_lt_level_filter": {"()": LtLevelFilter, "level": filter_lev}
        })
        if stdout_level < stderr_level:
            stdout_filt, stderr_filt = ("_lt_level_filter", "_geq_level_filter")
        else:
            stdout_filt, stderr_filt = ("_geq_level_filter", "_lt_level_filter")
    else:
        stdout_filt, stderr_filt = (None, None)

    if 'handlers' in d:
        _set_handler_level(d['handlers'], 'stdout', stdout_level, stdout_filt)
        _set_handler_level(d['handlers'], 'stderr', stderr_level, stderr_filt)

def _set_log_file_paths(d, new_paths):
    """Assign paths to log files. Paths are assumed to be well-formed and in 
    writeable locations.

    Args:
        d (dict): Nested dict read from the log configuration file.
        new_paths (dict): Dict of new log file names to assign. Keys are the 
            names of :py:class:`logging.Handler`s in the config file, and values
            are the new paths.
    """
    if not new_paths:
        _log.error("Log file paths not set.")
        return
    handlers = d.setdefault('handlers', dict())
    for h in handlers:
        if h in new_paths:
            d['handlers'][h]["filename"] = new_paths[h]
            del new_paths[h]
    if new_paths:
        _log.warning("Couldn't find handlers for the following log files: %s",
            new_paths)

def mdtf_log_config(config_path, root_logger, cli_d=None, new_paths=None):
    """Wrapper to handle logger configuration from a file and transfer of the 
    temporary log cache to the newly-configured loggers.

    Args:
        config_path (str): Path to the logger configuration file. This is taken
            to be in .jsonc format, following the :py:mod:`logging` ``dictConfig``
            `schema <https://docs.python.org/3.7/library/logging.config.html#logging-config-dictschema>`__.
        root_logger (:py:class:`logging.Logger`): Framework's root logger, to
            which the temporary log cache was attached.
        cli_d (dict): Dict of parsed CLI settings, in particular 'verbose'/'quiet'.
        new_paths (dict): Dict of new log file names to assign. Keys are the 
            names of :py:class:`logging.Handler`s in the config file, and values
            are the new paths.
    """
    # temporary cache handler should be the only handler attached to root_logger
    # as of now
    if len(root_logger.handlers) > 1 \
        or not isinstance(root_logger.handlers[0], MultiFlushMemoryHandler):
        _log.error("Unexpected handlers attached to root: %s", root_logger.handlers)
    temp_log_cache = root_logger.handlers[0]

    # log uncaught exceptions
    _set_excepthook(root_logger)

    # set console verbosity level
    stdout_level, stderr_level = _level_from_cli(cli_d)

    # read the config file, munge it according to CLI settings, configure loggers
    try:
        log_config = read_json(config_path)
        _set_console_log_level(log_config, stdout_level, stderr_level)
        _set_log_file_paths(log_config, new_paths)
        logging.config.dictConfig(log_config)
    except Exception as exc:
        _log.exception("Logging config failed.")

    # transfer cache contents to newly-configured loggers and delete it
    temp_log_cache.transfer_to_all(root_logger)
    temp_log_cache.close()
    root_logger.removeHandler(temp_log_cache)
