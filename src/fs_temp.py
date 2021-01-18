
import functools
import fsspec


class FSExceptionBase(Exception):
    """Base class and common formatting code for exceptions raised in data 
    query/fetch.
    """
    _error_str = ""

    def __init__(self, cls_nm, func_nm, args=None, kwargs=None):
        self.cls_nm = cls_nm
        self.func_nm = func_nm
        if args:
            self.args = args
        else:
            self.args = []
        if kwargs:
            self.kwargs = kwargs
        else:
            self.kwargs = dict()

    def __str__(self):
        arg_strs = [str(x) for x in self.args] \
            + [f'{k}={v}' for k,v in self.kwargs.items()]
        return (f"{self._error_str} from {self.cls_nm}.{self.func_nm} called "
            f"with ({', '.join(arg_strs)}).")

class NoRmException(FSExceptionBase):
    _error_str = "Cannot rm/rmdir on remote filesystem:"

class NoRmFilesystemMixin():
    """Dummy/safeguard class which causes all write methods defined on 
    :class:`fsspec.AbstractFileSystem` to raise :class:`ReadOnlyException`.
    """
    def rmdir(self, *args, **kwargs):
        raise NoRmException(self.__class__.__name__, 'rmdir', args, kwargs)

    def rm_file(self, *args, **kwargs):
        raise NoRmException(self.__class__.__name__, 'rm_file', args, kwargs)

    def rm(self, *args, **kwargs):
        raise NoRmException(self.__class__.__name__, 'rm', args, kwargs)

class ReadOnlyException(FSExceptionBase):
    _error_str = "Read-only filesystem:"

class ReadOnlyFilesystemMixin():
    """Dummy/safeguard class which causes all write methods defined on 
    :class:`fsspec.AbstractFileSystem` to raise :class:`ReadOnlyException`.
    """
    def mkdir(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'mkdir', args, kwargs)

    def makedirs(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'makedirs', args, kwargs)

    def rmdir(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'rmdir', args, kwargs)

    def put_file(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'put_file', args, kwargs)

    def put(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'put', args, kwargs)

    def mv(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'mv', args, kwargs)

    def rm_file(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'rm_file', args, kwargs)

    def rm(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'rm', args, kwargs)

    def touch(self, *args, **kwargs):
        raise ReadOnlyException(self.__class__.__name__, 'touch', args, kwargs)




def class_wraps(cls):
    """Update a wrapper class `cls` to look like the wrapped, by analogy with
    functools.wraps for functions/methods.
    Source: `https://stackoverflow.com/a/6394966`__.
    """
    class _Wrapper(cls):
        """New wrapper that will extend the wrapper `cls` to make it look like 
        `wrapped`.

        wrapped: Original function or class that is beign decorated.
        assigned: A list of attribute to assign to the the wrapper, by default they are:
             ['__doc__', '__name__', '__module__', '__annotations__'].

        """
        def __init__(self, wrapped, assigned=functools.WRAPPER_ASSIGNMENTS):
            self.__wrapped = wrapped
            for attr in assigned:
                setattr(self, attr, getattr(wrapped, attr))

            super().__init__(wrapped)

        def __repr__(self):
            return repr(self.__wrapped)
    return _Wrapper

def read_only_fs_wrapper(cls_):
    """Insert :class:`ReadOnlyFilesystemMixin` so it comes first in the MRO.
    """
    @class_wraps(cls_)
    class _WrappedCls(ReadOnlyFilesystemMixin, cls_):
        pass
    return _WrappedCls

def no_rm_fs_wrapper(cls_):
    """Insert :class:`ReadOnlyFilesystemMixin` so it comes first in the MRO.
    """
    @class_wraps(cls_)
    class _WrappedCls(NoRmFilesystemMixin, cls_):
        pass
    return _WrappedCls

# ----------------------------------------------

class GFDLGCPMixin(object):
    def get_cwd_():
        pass

    def get_site():
        pass

    def get_filesystem():
        pass

    def is_local():
        # All functionality of LocalFileSystem
        pass

    def is_mounted():
        # LocalFileSystem, but require batching operations into transactions
        pass

    def is_mounted_read_only():
        # Same as is_mounted, but use gcp for writes
        pass

    def is_on_dmf():
        # issue dmget/dmput as part of transaction. 
        pass

    def can_gcp():
        pass

    def gcp():
        pass

# No, better yet have a wrapper that inits and dispatches to individual filesystem
# instances when files on that type of filesystem are requested. 
# - Local relative to current sys
# - mounted but remote (ie NFS), rel. to "
# - mouted remote & read-only
# - not mounted.
# - Implement DMF as a cache wrapper.
# - Also git-LFS -- should be able to use off-the-shelf git?
#
# 3-rd party "cffi" for gcp bindings -- don't need to recompile?

class GFDLGCPFileSystem(fsspec.spec.AbstractFileSystem):
    """
    
    Based on fsspec.implementations.sftp.SFTPFileSystem
    fsspec.implementations.ftp.FTPFileSystem
    """

    protocol = "gfdl_gcp"

    def __init__(self, host, **ssh_kwargs):
        """

        Parameters
        ----------
        host: str
            Hostname or IP as a string
        temppath: str
            Location on the server to put files, when within a transaction
        ssh_kwargs: dict
            Parameters passed on to connection. See details in
            http://docs.paramiko.org/en/2.4/api/client.html#paramiko.client.SSHClient.connect
            May include port, username, password...
        """
        if self._cached:
            return
        super(SFTPFileSystem, self).__init__(**ssh_kwargs)
        self.temppath = ssh_kwargs.pop("temppath", "/tmp")
        self.host = host #get host
        self.ssh_kwargs = ssh_kwargs
        self._connect()

    def _connect(self):
        # module load GCP
        pass

    @classmethod
    def _strip_protocol(cls, path):
        return infer_storage_options(path)["path"]

    @staticmethod
    def _get_kwargs_from_urls(urlpath):
        out = infer_storage_options(urlpath)
        out.pop("path", None)
        out.pop("protocol", None)
        return out

    def mkdir(self, path, mode=511):
        self.ftp.mkdir(path, mode)

    def makedirs(self, path, exist_ok=False, mode=511):
        if self.exists(path) and not exist_ok:
            raise FileExistsError("File exists: {}".format(path))

        parts = path.split("/")
        path = ""

        for part in parts:
            path += "/" + part
            if not self.exists(path):
                self.mkdir(path, mode)

    def info(self, path):
        s = self.ftp.stat(path)
        if S_ISDIR(s.st_mode):
            t = "directory"
        elif S_ISLNK(s.st_mode):
            t = "link"
        else:
            t = "file"
        return {
            "name": path + "/" if t == "directory" else path,
            "size": s.st_size,
            "type": t,
            "uid": s.st_uid,
            "gid": s.st_gid,
            "time": s.st_atime,
            "mtime": s.st_mtime,
        }

    def ls(self, path, detail=False):
        out = ["/".join([path.rstrip("/"), p]) for p in self.ftp.listdir(path)]
        out = [self.info(o) for o in out]
        if detail:
            return out
        return sorted([p["name"] for p in out])

    def put(self, lpath, rpath):
        self.ftp.put(lpath, rpath)

    def get(self, rpath, lpath):
        self.ftp.get(rpath, lpath)

    def _open(self, path, mode="rb", block_size=None, **kwargs):
        """
        block_size: int or None
            If 0, no buffering, if 1, line buffering, if >1, buffer that many
            bytes, if None use default from paramiko.
        """
        if kwargs.get("autocommit", True) is False:
            # writes to temporary file, move on commit
            path2 = "{}/{}".format(self.temppath, uuid.uuid4())
            f = self.ftp.open(path2, mode, bufsize=block_size if block_size else -1)
            f.temppath = path2
            f.targetpath = path
            f.fs = self
            f.commit = types.MethodType(commit_a_file, f)
            f.discard = types.MethodType(discard_a_file, f)
        else:
            f = self.ftp.open(path, mode, bufsize=block_size if block_size else -1)
        return f

    def mv(self, old, new):
        self.ftp.posix_rename(old, new)


def commit_a_file(self):
    self.fs.mv(self.temppath, self.targetpath)


def discard_a_file(self):
    self.fs._rm(self.temppath)




#

class GFDLGCPFile(fsspec.spec.AbstractBufferedFile):
    """Taken from fsspec.implementations.ftp.FTPFile, dropping binary 
    mode-specific options.
    """

    def __init__(
        self,
        fs,
        path,
        mode="rb",
        block_size="default",
        autocommit=True,
        cache_type="readahead",
        cache_options=None,
        **kwargs
    ):
        super().__init__(
            fs,
            path,
            mode=mode,
            block_size=block_size,
            autocommit=autocommit,
            cache_type=cache_type,
            cache_options=cache_options,
            **kwargs
        )
        if not autocommit:
            self.target = self.path
            self.path = "/".join([kwargs["tempdir"], str(uuid.uuid4())])

    def commit(self):
        self.fs.mv(self.path, self.target)

    def discard(self):
        self.fs.rm(self.path)


