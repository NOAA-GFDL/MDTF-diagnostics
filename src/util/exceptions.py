"""All framework-specific exceptions are placed in a single module to simplify 
imports.
"""

import traceback

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