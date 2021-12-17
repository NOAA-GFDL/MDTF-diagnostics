"""Utility functions for dealing with subprocesses.
"""
from distutils.spawn import find_executable
import errno
import shlex
import signal
import subprocess
import threading
from . import exceptions

import logging
_log = logging.getLogger(__name__)

class ExceptionPropagatingThread(threading.Thread):
    """Class to propagate exceptions raised in a child thread back to the caller
    thread when the child is join()ed. Adapted from
    `<https://stackoverflow.com/a/31614591>`__.
    """
    def run(self):
        self.ret = None
        self.exc = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(ExceptionPropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        return self.ret


def poll_command(command, shell=False, env=None):
    """Runs a command in a subprocess and prints stdout in real-time. Wraps
    :py:class:`~subprocess.Popen`.

    Args:
        command: list of command + arguments, or the same as a single string.
            See :py:mod:`subprocess` syntax. Note this interacts with the `shell`
            setting.
        shell (bool): Optional. Whether to run *command* in a shell. Default False.
        env (dict): Optional. Environment variables to set.
    """
    process = subprocess.Popen(
        command, shell=shell, env=env, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc


def run_command(command, env=None, cwd=None, timeout=0, dry_run=False, log=_log):
    """Subprocess wrapper to facilitate running a single command without starting
    a shell.

    Note:
        We hope to save some process overhead by not running the command in a
        shell, but this means the command can't use piping, quoting, environment
        variables, or filename globbing etc.

    See documentation for :py:class:`~subprocess.Popen`.

    Args:
        command (list of str): List of commands to execute.
        env (dict): Optional. Environment variables to set.
        cwd (str): Optional. Child processes' working directory. Default is `None`,
            which uses the current working directory.
        timeout (int): Optionally, kill the command's subprocess
            and raise a MDTFCalledProcessError if the command doesn't finish in
            `timeout` seconds. Set to 0 to disable.

    Returns:
        List of str containing output that was written to stdout
        by each command. Note: this is split on newlines after the fact.

    Raises:
        :class:`~exceptions.MDTFCalledProcessError`: If any commands return with
            nonzero exit code. Stderr for that command is stored in the ``output``
            attribute of the exception.
    """
    def _timeout_handler(signum, frame):
        raise exceptions.TimeoutAlarm

    if isinstance(command, str):
        command = shlex.split(command)
    cmd_str = ' '.join(command)
    if dry_run:
        log.info('DRY_RUN: call %s', cmd_str)
        return
    proc = None
    pid = None
    retcode = 1
    stderr = ''
    try:
        proc = subprocess.Popen(
            command, shell=False, env=env, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, bufsize=1
        )
        pid = proc.pid
        # py3 has timeout built into subprocess; this is a workaround
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(int(timeout))
        (stdout, stderr) = proc.communicate()
        signal.alarm(0)  # cancel the alarm
        retcode = proc.returncode
    except exceptions.TimeoutAlarm:
        if proc:
            proc.kill()
        retcode = errno.ETIME
        stderr += f"\nKilled by timeout ( > {timeout} sec)."
    except Exception as exc:
        if proc:
            proc.kill()
        stderr += f"\nCaught exception {repr(exc)}."
    if retcode != 0:
        log.error('run_command on %s (pid %s) exit status=%s:%s\n',
            cmd_str, pid, retcode, stderr)
        raise exceptions.MDTFCalledProcessError(
            returncode=retcode, cmd=cmd_str, output=stderr)
    if '\0' in stdout:
        return stdout.split('\0')
    else:
        return stdout.splitlines()

def run_shell_command(command, env=None, cwd=None, dry_run=False, log=_log):
    """Subprocess wrapper to facilitate running shell commands. See documentation
    for :py:class:`~subprocess.Popen`.

    Args:
        commands (list of str): List of commands to execute.
        env (dict): Optional. Environment variables to set.
        cwd (str): Optional. Child processes' working directory. Default is `None`,
            which uses the current working directory.

    Returns:
        List of str containing output that was written to stdout
        by each command. Note: this is split on newlines after the fact, so if
        commands give != 1 lines of output this will not map to the list of commands
        given.

    Raises:
        :class:`~exceptions.MDTFCalledProcessError`: If any commands return with
            nonzero exit code. Stderr for that command is stored in the ``output``
            attribute of the exception.
    """
    # shouldn't lookup on each invocation, but need abs path to bash in order
    # to pass as executable argument. Pass executable argument because we want
    # bash specifically (not default /bin/sh, and we save a bit of overhead by
    # starting bash directly instead of from sh.)
    bash_exec = find_executable('bash')

    if not isinstance(command, str):
        command = ' '.join(command)
    if dry_run:
        log.info('DRY_RUN: call %s', command)
        return
    proc = None
    pid = None
    retcode = 1
    stderr = ''
    try:
        proc = subprocess.Popen(
            command,
            shell=True, executable=bash_exec,
            env=env, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, bufsize=1
        )
        pid = proc.pid
        (stdout, stderr) = proc.communicate()
        retcode = proc.returncode
    except Exception as exc:
        if proc:
            proc.kill()
        stderr += f"\nCaught exception {repr(exc)}."
    if retcode != 0:
        log.error('run_shell_command on %s (pid %s) exit status=%s:\n%s\n',
            command, pid, retcode, stderr)
        raise exceptions.MDTFCalledProcessError(
            returncode=retcode, cmd=command, output=stderr)
    if '\0' in stdout:
        return stdout.split('\0')
    else:
        return stdout.splitlines()
