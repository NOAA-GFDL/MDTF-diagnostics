"""All framework-specific exceptions are placed in a single module to simplify 
imports.
"""
import os
import errno
import traceback

import logging
_log = logging.getLogger(__name__)

class ExceptionQueue(object):
    """Class to retain information about exceptions that were raised, for later
    output.
    """
    def __init__(self):
        self._queue = []

    @property
    def is_empty(self):
        return (len(self._queue) == 0)

    def log(self, exc, exc_to_chain=None):
        wrapped_exc = traceback.TracebackException.from_exception(exc)
        self._queue.append(wrapped_exc)

    def format(self):
        strs_ = [''.join(exc.format()) for exc in self._queue]
        strs_ = [f"***** Caught exception #{i+1}:\n{exc}\n" \
            for i, exc in enumerate(strs_)]
        return "".join(strs_)

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
    exit(1)

# -----------------------------------------------------------------

class TimeoutAlarm(Exception):
    """Dummy exception raised if a subprocess times out."""
    # NOTE py3 builds timeout into subprocess; fix this
    pass

class MDTFBaseException(Exception):
    """Dummy base class to describe all MDTF-specific errors that can happen
    during the framework's operation."""
    pass

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

class WormKeyError(KeyError, MDTFBaseException):
    """Raised when attempting to overwrite or delete an entry in a
    :class:`~src.util.basic.WormDict`.
    """
    pass

class DataclassParseError(ValueError, MDTFBaseException):
    """Raised when parsing input data fails on a 
    :func:`~src.util.dataclass.mdtf_dataclass` or :func:`~src.util.dataclass.regex_dataclass`.
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
    """Exception raised when we attempt to operate on :class:`Date`s or 
    :class:`DateRange`s with differing levels of precision, which shouldn't
    happen with data sampled at a single frequency.
    """
    def __init__(self, func_name='', msg=''):
        self.func_name = func_name
        self.msg = msg

    def __str__(self):
        return ("Attempted datelabel method '{}' on FXDate "
            "placeholder: {}.").format(self.func_name, self.msg)

class FXDateException(MDTFBaseException):
    """Exception raised when :class:`FXDate`s or :class:`FXDateRange:s, which are
    placeholder/sentinel classes used to indicate static data with no time 
    dependence, are accessed like real :class:`Date`s or :class:`DateRange`s.
    """
    def __init__(self, func_name='', msg=''):
        self.func_name = func_name
        self.msg = msg

    def __str__(self):
        return ("Attempted datelabel method '{}' on FXDate "
            "placeholder: {}.").format(self.func_name, self.msg)

class DataExceptionBase(MDTFBaseException):
    """Base class and common formatting code for exceptions raised in data 
    query/fetch.
    """
    _error_str = ""

    def __init__(self, dataset, msg=None):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if hasattr(self.dataset, 'remote_path'):
            data_id = self.dataset.remote_path
        elif hasattr(self.dataset, 'name'):
            data_id = self.dataset.name
        else:
            data_id = str(self.dataset)
        s = self._error_str + f" for {data_id}"
        if self.msg is not None:
            s += f": {self.msg}."
        else:
            s += "."
        return s

class DataQueryError(DataExceptionBase):
    """Exception signaling a failure to find requested data in the remote location. 
    
    Raised by :meth:`~data_manager.DataManager.queryData` to signal failure of a
    data query. Should be caught properly in :meth:`~data_manager.DataManager.planData`
    or :meth:`~data_manager.DataManager.fetchData`.
    """
    _error_str = "Data query error"

class DataFetchError(DataExceptionBase):
    """Exception signaling a failure to obtain data from the remote location.
    """
    _error_str = "Data fetch error"

class PodExceptionBase(MDTFBaseException):
    """Base class and common formatting code for exceptions affecting a single
    POD.
    """
    _error_str = ""

    def __init__(self, pod, msg=None):
        self.pod = pod
        self.msg = msg

    def __str__(self):
        if hasattr(self.pod, 'name'):
            pod_name = self.pod.name
        else:
            pod_name = self.pod
        s = f"Error in {pod_name}: " + self._error_str
        if self.msg is not None:
            s += f"\nReason: {self.msg}."
        return s

    def __repr__(self):
        # full repr of Diagnostic takes lots of space to print
        return f"{self.__class__.__name__}({str(self)})"

class PodConfigError(PodExceptionBase):
    """Exception raised if we can't parse info in a POD's settings.jsonc file.
    (Covers issues with the file format/schema; malformed JSONC will raise a
    :py:class:`~json.JSONDecodeError` when :func:`~util.parse_json` attempts to
    parse the file.
    """
    _error_str = "Couldn't parse configuration in settings.jsonc file."

class PodDataError(PodExceptionBase):
    """Exception raised if POD doesn't have required data to run. 
    """
    _error_str = "Requested data not available."

class PodRuntimeError(PodExceptionBase):
    """Exception raised if POD doesn't have required resources to run. 
    """
    _error_str = "An error occurred in setting up the POD's runtime environment."

class PodExecutionError(PodExceptionBase):
    """Exception raised if POD doesn't have required resources to run. 
    """
    _error_str = "An error occurred during the POD's execution."

class DataPreprocessError(MDTFBaseException):
    """Exception signaling an error in preprocessing data after it's been 
    fetched, but before any PODs run.
    """
    def __init__(self, dataset, msg=''):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if hasattr(self.dataset, 'name'):
            return 'Data preprocessing error for {}: {}.'.format(
                self.dataset.name, self.msg)
        else:
            return 'Data preprocessing error: {}.'.format(self.msg)
