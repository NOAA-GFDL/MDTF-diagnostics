"""All framework-specific exceptions are placed in a single module to simplify
imports.
"""
import os
import sys
import errno
from subprocess import CalledProcessError

import logging
_log = logging.getLogger(__name__)


def exit_on_exception(exc, msg=None):
    """Prints information about a fatal exception to the console beofre exiting.
    Use case is in user-facing subcommands (``mdtf install`` etc.), since we
    have more sophisticated logging in the framework itself.
    Args:
        exc: :py:class:`Exception` object
        msg (str, optional): additional message to print.
    """
    # if subprocess failed, will have already logged its own info
    print(f'ERROR: caught exception {repr(exc)}')
    if msg:
        print(msg)
    exit_handler(code=1)

def exit_handler(code=1, msg=None):
    """Wraps all calls to :py:func:`sys.exit`; could do additional
    cleanup not handled by atexit() here.
    """
    if msg:
        print(msg)
    sys.exit(code)

def chain_exc(exc, new_msg, new_exc_class=None):
    if new_exc_class is None:
        new_exc_class = type(exc)
    try:
        if new_msg.istitle():
            new_msg = new_msg[0].lower() + new_msg[1:]
        if new_msg.endswith('.'):
            new_msg = new_msg[:-1]
        new_msg = f"{exc_descriptor(exc)} while {new_msg.lstrip()}: {repr(exc)}."
        raise new_exc_class(new_msg) from exc
    except Exception as chained_exc:
        return chained_exc

def exc_descriptor(exc):
    # MDTFEvents are raised during normal program operation; use correct wording
    # for log messages so user doesn't think it's an error
    if isinstance(exc, MDTFEvent):
        return "Received event"
    else:
        return "Caught exception"

class TimeoutAlarm(Exception):
    """Dummy exception raised if a subprocess times out."""
    # NOTE py3 builds timeout into subprocess; fix this
    pass

class MDTFBaseException(Exception):
    """Base class to describe all MDTF-specific errors that can happen during
    the framework's operation."""

    def __repr__(self):
        # full repr of attrs of child classes may take lots of space to print;
        # instead just print message
        return f'{self.__class__.__name__}("{str(self)}")'

class ChildFailureEvent(MDTFBaseException):
    """Exception raised when a member of the object hierarchy is deactivated
    because all its child objects have failed.
    """
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return (f"Deactivating {self.obj.full_name} due to failure of all "
            f"child objects.")

class PropagatedEvent(MDTFBaseException):
    """Exception passed between members of the object hierarchy when a parent
    object (:class:`~core.MDTFObjectBase`) has been deactivated and needs to
    deactivate its children.
    """
    def __init__(self, exc, parent):
        self.exc = exc
        self.parent = parent

    def __str__(self):
        return (f"{exc_descriptor(self.exc)} {repr(self.exc)} from deactivation "
            f"of parent {self.parent.full_name}.")


class MDTFFileNotFoundError(FileNotFoundError, MDTFBaseException):
    """Wrapper for :py:class:`FileNotFoundError` which handles error codes so we
    don't have to remember to import :py:mod:`errno` everywhere.
    """
    def __init__(self, path):
        super(MDTFFileNotFoundError, self).__init__(
            errno.ENOENT, os.strerror(errno.ENOENT), path
        )

class MDTFFileExistsError(FileExistsError, MDTFBaseException):
    """Wrapper for :py:class:`FileExistsError` which handles error codes so we
    don't have to remember to import :py:mod:`errno` everywhere.
    """
    def __init__(self, path):
        super(MDTFFileExistsError, self).__init__(
            errno.EEXIST, os.strerror(errno.EEXIST), path
        )

class MDTFCalledProcessError(CalledProcessError, MDTFBaseException):
    """Wrapper for :py:class:`subprocess.CalledProcessError`."""
    pass

class WormKeyError(KeyError, MDTFBaseException):
    """Raised when attempting to overwrite or delete an entry in a
    :class:`~src.util.basic.WormDict`.
    """
    pass

class DataclassParseError(ValueError, MDTFBaseException):
    """Raised when parsing input data fails on a
    :func:`~src.util.dataclass.mdtf_dataclass` or
    :func:`~src.util.dataclass.regex_dataclass`.
    """
    pass

class RegexParseError(ValueError, MDTFBaseException):
    """Raised when parsing input data fails on a
    :func:`~src.util.dataclass.RegexPattern`.
    """
    pass

class RegexSuppressedError(ValueError, MDTFBaseException):
    """Raised when parsing input data fails on a
    :func:`~src.util.dataclass.RegexPattern`, but we've decided to supress
    error based on the associated RegexPattern's match_error_filter attribute.
    """
    pass

class UnitsError(ValueError, MDTFBaseException):
    """Raised when trying to convert between quantities with physically
    inequivalent units.
    """
    pass

class ConventionError(MDTFBaseException):
    """Exception raised by a duplicate variable convention name."""
    def __init__(self, conv_name):
        self.conv_name = conv_name

    def __str__(self):
        return f"Error in the definition of convention '{self.conv_name}'."

class MixedDatePrecisionException(MDTFBaseException):
    """Exception raised when we attempt to operate on :class:`Date` or
    :class:`DateRange` objects with differing levels of precision, which shouldn't
    happen with data sampled at a single frequency.
    """
    def __init__(self, func_name='', msg=''):
        self.func_name = func_name
        self.msg = msg

    def __str__(self):
        return ("Attempted datelabel method '{}' on FXDate "
            "placeholder: {}.").format(self.func_name, self.msg)

class FXDateException(MDTFBaseException):
    """Exception raised when :class:`FXDate` or :class:`FXDateRange` classes,
    which are placeholder/sentinel classes used to indicate static data with no
    time dependence, are accessed like real :class:`Date` or :class:`DateRange`
    objects.
    """
    def __init__(self, func_name='', msg=''):
        self.func_name = func_name
        self.msg = msg

    def __str__(self):
        return ("Attempted datelabel method '{}' on FXDate "
            "placeholder: {}.").format(self.func_name, self.msg)

class DataRequestError(MDTFBaseException):
    """Dummy class used for fatal errors that take place during the
    data query/fetch/preprocess stage of the framework.
    """
    pass

class MDTFEvent(MDTFBaseException):
    """Dummy class to denote non-fatal errors, specifically "events" that are
    passed during the data query/fetch/preprocess stage of the framework.
    """
    pass

class FatalErrorEvent(MDTFBaseException):
    """Dummy class used to "convert" :class:`MDTFEvent`\s to fatal errors
    (resulting in deactivation of a variable, pod or case.) via exception
    chaining.
    """
    pass

class DataProcessingEvent(MDTFEvent):
    """Base class and common formatting code for events raised in data
    query/fetch. These should *not* be used for fatal errors (when a variable or
    POD is deactivated.)
    """
    def __init__(self, msg="", dataset=None):
        self.msg = msg
        self.dataset = dataset

    def __str__(self):
        # if self.dataset is not None:
        #     if hasattr(self.dataset, 'remote_path'):
        #         data_id = self.dataset.remote_path
        #     elif hasattr(self.dataset, 'name'):
        #         data_id = self.dataset.name
        #     else:
        #         data_id = str(self.dataset)
        return self.msg

class DataQueryEvent(DataProcessingEvent):
    """Exception signaling a failure to find requested data in the remote location.
    """
    pass

class DataExperimentEvent(DataProcessingEvent):
    """Exception signaling a failure to uniquely select an experiment for all
    variables based on query results.
    """
    pass

class DataFetchEvent(DataProcessingEvent):
    """Exception signaling a failure to obtain data from the remote location.
    """
    pass

class DataPreprocessEvent(DataProcessingEvent):
    """Exception signaling an error in preprocessing data after it's been
    fetched, but before any PODs run.
    """
    pass

class MetadataEvent(DataProcessingEvent):
    """Exception signaling discrepancies in variable metadata.
    """
    pass

class MetadataError(MDTFBaseException):
    """Exception signaling unrecoverable errors in variable metadata.
    """
    pass

class UnitsUndefinedError(MetadataError):
    """Exception signaling unrecoverable errors in variable metadata.
    """
    pass

class GenericDataSourceEvent(DataProcessingEvent):
    """Exception signaling a failure originating in the DataSource query/fetch
    pipeline whose cause doesn't fall into the above categories.
    """
    pass

class PodExceptionBase(MDTFBaseException):
    """Base class and common formatting code for exceptions affecting a single
    POD.
    """
    _error_str = ""

    def __init__(self, msg=None, pod=None):
        self.pod = pod
        self.msg = msg

    def __str__(self):
        s = self._error_str
        if self.pod is not None:
            if hasattr(self.pod, 'full_name'):
                pod_name = self.pod.full_name
            else:
                pod_name = f"'{self.pod}'"
            s += f" for POD {pod_name}"
        if self.msg is not None:
            s += f": {self.msg}"
        if not s.endswith('.'):
            s += "."
        return s

class PodConfigError(PodExceptionBase):
    """Exception raised if we can't parse info in a POD's settings.jsonc file.
    (Covers issues with the file format/schema; malformed JSONC will raise a
    :py:class:`~json.JSONDecodeError` when :func:`~util.parse_json` attempts to
    parse the file.
    """
    _error_str = "Couldn't parse the settings.jsonc file"

class PodConfigEvent(MDTFEvent):
    """Exception raised during non-fatal events in resolving POD configuration.
    """
    pass

class PodDataError(PodExceptionBase):
    """Exception raised if POD doesn't have required data to run.
    """
    _error_str = "Requested data not available"

class PodRuntimeError(PodExceptionBase):
    """Exception raised if POD doesn't have required resources to run.
    """
    _error_str = "Error in setting the runtime environment"

class PodExecutionError(PodExceptionBase):
    """Exception raised if POD exits with non-zero retcode or otherwise raises
    an error during execution.
    """
    _error_str = "Error during POD execution"
