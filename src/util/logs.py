"""Utilities related to configuration and handling of framework logging.
"""
import signal

def signal_logger(caller_name, signum=None, frame=None):
    """Lookup signal name from number; `<https://stackoverflow.com/a/2549950>`__.
    """
    if signum:
        sig_lookup = {
            k:v for v, k in reversed(sorted(list(signal.__dict__.items()))) \
                if v.startswith('SIG') and not v.startswith('SIG_')
        }
        sig_name = sig_lookup.get(signum, 'UNKNOWN')
        print(f"DEBUG: {caller_name} caught signal {sig_name} ({signum})")
        # if frame:
        #     traceback.print_stack(f=frame)
