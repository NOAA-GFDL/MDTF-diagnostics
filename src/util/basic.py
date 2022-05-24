"""Classes and functions that define and operate on basic data structures.
"""
import abc
import collections
import collections.abc
import enum
import itertools
import string
import unittest.mock
import uuid
from . import exceptions

import logging
_log = logging.getLogger(__name__)

class _AbstractAttributePlaceholder():
    """Placeholder class used in the definition of the :func:`abstract_attribute`
    decorator.
    """
    pass

def abstract_attribute(obj=None):
    """Decorator for abstract attributes in abstract base classes by analogy
    with :py:func:`abc.abstract_method`. Based on
    `<https://stackoverflow.com/a/50381071>`__.
    """
    if obj is None:
        obj = _AbstractAttributePlaceholder()
    obj.__is_abstract_attribute__ = True
    return obj

class MDTFABCMeta(abc.ABCMeta):
    """Wrap the metaclass for abstract base classes to enable definition of
    abstract attributes via :func:`abstract_attribute`. Based on
    `<https://stackoverflow.com/a/50381071>`__.

    Raises:
        NotImplementedError: If a child class doesn't define an
            abstract attribute, by analogy with :py:func:`abc.abstract_method`.
    """
    def __call__(cls, *args, **kwargs):
        instance = abc.ABCMeta.__call__(cls, *args, **kwargs)
        abstract_attributes = set([])
        for attr in dir(instance):
            if isinstance(getattr(cls, attr, None), property):
                # Don't call properties on instance before it's inited
                continue
            if getattr(getattr(instance, attr), '__is_abstract_attribute__', False):
                abstract_attributes.add(attr)
        if abstract_attributes:
            raise NotImplementedError(("Can't instantiate abstract class {} with "
                "abstract attributes: {}").format(
                    cls.__name__, ', '.join(abstract_attributes)
            ))
        return instance


class _Singleton(type):
    """Private metaclass that creates a :class:`~util.Singleton` base class when
    called. This version is taken from `<https://stackoverflow.com/a/6798042>`__
    and is compatible with Python 2 and 3.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})):
    """Parent class defining the
    `Singleton <https://en.wikipedia.org/wiki/Singleton_pattern>`_ pattern. We
    use this as safer way to pass around global state.
    """
    @classmethod
    def _reset(cls):
        """Private method of all :class:`~util.Singleton`-derived classes added
        for use in unit testing only. Calling this method on test teardown
        deletes the instance, so that tests coming afterward will initialize the
        :class:`~util.Singleton` correctly, instead of getting the state set
        during previous tests.
        """
        # pylint: disable=maybe-no-member
        if cls in cls._instances:
            del cls._instances[cls]


class MultiMap(collections.defaultdict):
    """Extension of the :py:obj:`dict` class that allows doing dictionary lookups
    from either keys or values.

    Syntax for lookup from keys is unchanged, while lookup from values is done on
    the :meth:`inverse` attribute and returns a list of matching keys if more
    than one match is present. See `<https://stackoverflow.com/a/21894086>`__.

    Example:

    .. code-block:: python

       >>> d = MultiMap({'key1': 'val', 'key2':'val'})

       >>> d['key1']
       'val'

       >>> d.inverse['val']
       ['key1', 'key2']

    """
    def __init__(self, *args, **kwargs):
        """Inherited from :py:class:`collections.defaultdict`. Construct by
        passing an ordinary :py:obj:`dict`.
        """
        super(MultiMap, self).__init__(set, *args, **kwargs)
        for key in iter(self.keys()):
            super(MultiMap, self).__setitem__(key, to_iter(self[key], set))

    def __setitem__(self, key, value):
        super(MultiMap, self).__setitem__(key, to_iter(value, set))

    def get_(self, key):
        """Re-implement ``__getitem__`` to handle returning possibly multiple
        items."""
        if key not in list(self.keys()):
            raise KeyError(key)
        return from_iter(self[key])

    def to_dict(self):
        """Convert to ordinary :py:obj:`dict`."""
        d = {}
        for key in iter(self.keys()):
            d[key] = self.get_(key)
        return d

    def inverse(self):
        """Construct inverse dict mapping values to keys."""
        d = collections.defaultdict(set)
        for key, val_set in iter(self.items()):
            for v in val_set:
                d[v].add(key)
        return dict(d)

    def inverse_get_(self, val):
        """Construct inverse dict and return keys corresponding to *val*."""
        # don't raise keyerror if empty; could be appropriate result
        inv_lookup = self.inverse()
        return from_iter(inv_lookup[val])

class WormDict(collections.UserDict, dict):
    """Dict which raises exceptions when trying to overwrite or delete an
    existing entry. "WORM" is an acronym for "write once, read many."

    Raises:
        :class:`~src.util.exceptions.WormKeyError`: If code attempts to reassign
            or delete an existing key.
    """
    def __setitem__(self, key, value):
        if key in self.data:
            raise exceptions.WormKeyError(("Attempting to overwrite entry for "
                f"'{key}'. Existing value: '{self[key]}', new value: '{value}'."))
        self.data[key] = value

    def __delitem__(self, key):
        raise exceptions.WormKeyError(("Attempting to delete entry for "
                f"'{key}'. Existing value: '{self[key]}'."))

    @classmethod
    def from_struct(cls, d):
        """Construct a WormDict from a dict *d*. Intended to be used for automatic
        type coercion done on fields of a :func:`~src.util.dataclass.mdtf_dataclass`.
        """
        return cls(**d)

class ConsistentDict(WormDict):
    """Like :class:`WormDict`, but we only raise
    :class:`~src.util.exceptions.WormKeyError` if we try to reassign to a
    different value.

    Raises:
        :class:`~src.util.exceptions.WormKeyError`: If code attempts to reassign
            an existing key to a value different than the current one.
    """
    def __setitem__(self, key, value):
        if key in self.data and self[key] != value:
            raise exceptions.WormKeyError(("Attempting to overwrite entry for "
                f"'{key}'. Existing value: '{self[key]}', new value: '{value}'."))
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

class WormDefaultDict(WormDict):
    """:class:`src.util.basic.WormDict` with :py:class:`collections.defaultdict`
    functionality.
    """
    def __init__(self, default_factory=None, *args, **kwargs):
        """Inherited from :py:class:`collections.defaultdict` and takes same
        arguments.
        """
        if not (default_factory is None or callable(default_factory)):
            raise TypeError('First argument must be callable or None')
        super(WormDefaultDict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return super(WormDefaultDict, self).__getitem__(key)
        except KeyError:
            if self.default_factory is None:
                raise KeyError(key) # normal KeyError for missing key
            return self.default_factory()

class NameSpace(dict):
    """A dictionary that provides attribute-style access.

    For example, `d['key'] = value` becomes `d.key = value`. All methods of
    :py:obj:`dict` are supported.

    Note:
        Recursive access (`d.key.subkey`, as in C-style languages) is not supported.

    Implementation is based on `<https://github.com/Infinidat/munch>`__.

    Raises:
        :py:class:`AttributeError`: In cases where dict would raise a
            :py:class:`KeyError`.
    """

    # only called if k not found in normal places
    def __getattr__(self, k):
        """Gets key if it exists, otherwise throws AttributeError.
            nb. __getattr__ is only called if key is not found in normal places.
        """
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, k)
        except AttributeError:
            try:
                return self[k]
            except KeyError:
                raise AttributeError(k)

    def __setattr__(self, k, v):
        """Sets attribute k if it exists, otherwise sets key k. A KeyError
            raised by set-item (only likely if you subclass NameSpace) will
            propagate as an AttributeError instead.
        """
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                self[k] = v
            except Exception:
                raise AttributeError(k)
        else:
            object.__setattr__(self, k, v)

    def __delattr__(self, k):
        """Deletes attribute k if it exists, otherwise deletes key k. A KeyError
            raised by deleting the key -- such as when the key is missing -- will
            propagate as an AttributeError instead.
        """
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                del self[k]
            except KeyError:
                raise AttributeError(k)
        else:
            object.__delattr__(self, k)

    def __dir__(self):
        return list(self.keys())
    __members__ = __dir__  # for python2.x compatibility

    def __repr__(self):
        """Invertible string-form of a Munch. (Invertible so long as collection
        contents are each ``repr``-invertible.)
        """
        return '{0}({1})'.format(self.__class__.__name__, dict.__repr__(self))

    def __getstate__(self):
        """Implement a serializable interface used for pickling.
        See `<https://docs.python.org/3.6/library/pickle.html>`__.
        """
        return {k: v for k, v in iter(self.items())}

    def __setstate__(self, state):
        """Implement a serializable interface used for pickling.
        See `<https://docs.python.org/3.6/library/pickle.html>`__.
        """
        self.clear()
        self.update(state)

    def toDict(self):
        """Recursively converts a NameSpace back into a dictionary.
        """
        return type(self)._toDict(self)

    @classmethod
    def _toDict(cls, x):
        """Recursively converts a NameSpace back into a dictionary.
        (Note: as dicts are not hashable, they cannot be nested in
        sets/frozensets.)
        """
        if isinstance(x, dict):
            return dict((k, cls._toDict(v)) for k, v in iter(x.items()))
        elif isinstance(x, (list, tuple)):
            return type(x)(cls._toDict(v) for v in x)
        else:
            return x

    @property
    def __dict__(self):
        return self.toDict()

    @classmethod
    def fromDict(cls, x):
        """Recursively transforms a dictionary into a NameSpace via copy.
        (Note: as dicts are not hashable, they cannot be nested in
        sets/frozensets.)
        """
        if isinstance(x, dict):
            return cls((k, cls.fromDict(v)) for k, v in iter(x.items()))
        elif isinstance(x, (list, tuple)):
            return type(x)(cls.fromDict(v) for v in x)
        else:
            return x

    def copy(self):
        return type(self).fromDict(self)
    __copy__ = copy

    def _freeze(self):
        """Return immutable representation of (current) attributes.

        We do this to enable comparison of two Namespaces, which otherwise would
        be done by the default method of testing if the two objects refer to the
        same location in memory. See `<https://stackoverflow.com/a/45170549>`__.
        """
        d = self.toDict()
        d2 = {k: repr(d[k]) for k in d}
        FrozenNameSpace = collections.namedtuple(
            'FrozenNameSpace', sorted(list(d.keys()))
        )
        return FrozenNameSpace(**d2)

    def __eq__(self, other):
        if type(other) is type(self):
            return (self._freeze() == other._freeze())
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof

    def __hash__(self):
        return hash(self._freeze())

class _MDTFEnumMixin():
    def __str__(self):
        return str(self.name).lower()

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    @classmethod
    def from_struct(cls, str_):
        """Instantiate from string."""
        if str_.upper() not in cls.__members__:
            raise ValueError(f"Unrecognized value '{str_}' for '{cls.__name__}'.")
        return cls[str_.upper()]

class MDTFEnum(_MDTFEnumMixin, enum.Enum):
    """Customize behavior of :py:class:`~enum.Enum`:

    1) Assign (integer) values automatically to the members of the enumeration.
    2) Provide a :meth:`~_MDTFEnumMixin.from_struct` method to simplify
       instantiating an instance from a string. Intended to be used for automatic
       type coercion done on fields of a :func:`~src.util.dataclass.mdtf_dataclass`.
       To avoid potential confusion with reserved keywords, we use the Python
       convention that members of the enumeration are all uppercase.
    """
    def __new__(cls, *args, **kwargs):
        """AutoNumber recipe from python stdlib docs."""
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

class MDTFIntEnum(_MDTFEnumMixin, enum.IntEnum):
    """Customize :py:class:`~enum.IntEnum` analogous to :class:`MDTFEnum`.
    """
    pass

def sentinel_object_factory(obj_name):
    """Return a unique singleton object/class (same difference for singletons).
    For implementation, see `python docs
    <https://docs.python.org/3/library/unittest.mock.html#unittest.mock.sentinel>`__.
    """
    return getattr(unittest.mock.sentinel, obj_name)

class MDTF_ID():
    """Class wrapping :py:class:`~uuid.UUID`, to provide unique ID numbers for
    members of the object hierarchy (cases, pods, variables, etc.), so that we
    don't need to require that objects in these classes have unique names.
    """
    def __init__(self, id_=None):
        """
        Args:
            id\_ (optional): hard-code an ID instead of generating one.
        """
        if id_ is None:
            # set node=0 to eliminate hostname; only dependent on system clock
            self._uuid = uuid.uuid1(node=0)
        else:
            self._uuid = id_

    def __str__(self):
        """Print compact string representation (4 alphanumeric characters) instead
        of the entire uuid, to get more readable logs.
        """
        chars = string.digits + string.ascii_letters
        base = len(chars)
        num = self._uuid.time_low # least significant bits
        str_ = '0000'
        while num:
            str_ += chars[num % base]
            num //= base
        return str_[-2:-6:-1] # reversed so most-significant is 1st

    def __repr__(self):
        return f"{self.__class__.__name__}({self._uuid})"

    def __hash__(self):
        return hash(self._uuid)

    def __eq__(self, other):
        if hasattr(other, '_uuid'):
            return (self._uuid == other._uuid)
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof

# ------------------------------------------------------------------

def is_iterable(obj):
    """Test if *obj* is an iterable collection.

    Args:
        obj: Object to test.

    Returns:
        bool: True if *obj* is an iterable collection and not a string.
    """
    return isinstance(obj, collections.abc.Iterable) \
        and not isinstance(obj, str) # py3 strings have __iter__

def to_iter(obj, coll_type=list):
    """Cast arbitrary object *obj* to an iterable collection. If *obj* is not a
    collection, returns a one-element list containing *obj*.

    Args:
        obj: Object to cast to collection.
        coll_type: One of :py:obj:`list`, :py:obj:`set` or :py:obj:`tuple`,
            default :py:obj:`list`. Class to cast *obj* to.

    Returns:
        *obj*, cast to an iterable collection of type *coll_type*.
    """
    assert coll_type in [list, set, tuple] # only supported types for now
    if obj is None:
        return coll_type([])
    elif isinstance(obj, coll_type):
        return obj
    elif is_iterable(obj):
        return coll_type(obj)
    else:
        return coll_type([obj])

def from_iter(obj):
    """Inverse of :func:`to_iter`. If *obj* is a single-element iterable collection,
    return its only element.
    """
    if is_iterable(obj):
        if len(obj) == 1:
            return list(obj)[0]
        else:
            return list(obj)
    else:
        return obj

def remove_prefix(s1, s2):
    """If string *s1* starts with string *s2*, return *s1* with *s2* removed.
    Otherwise return *s1* unmodified.
    """
    if s1.startswith(s2):
        s1 = s1[len(s2):]
    return s1

def remove_suffix(s1, s2):
    """If string *s1* ends with string *s2*, return *s1* with *s2* removed.
    Otherwise return *s1* unmodified.
    """
    if s1.endswith(s2):
        s1 = s1[:-len(s2)]
    return s1

def filter_kwargs(kwarg_dict, function):
    """Given keyword arguments *kwarg_dict*, return only those kwargs accepted
    by *function*.

    Args:
        kwarg_dict (dict): Keyword arguments to be passed to *function*.
        function (function): Function to be called.

    Returns:
        dict: Subset of *key*\:*value* entries of *kwarg_dict* where *key*\s are
        keyword arguments recognized by *function*.
    """
    named_args = set(function.__code__.co_varnames)
    # if 'kwargs' in named_args:
    #    return kwarg_dict # presumably can handle anything
    return dict((k, kwarg_dict[k]) for k in named_args \
        if k in kwarg_dict and k not in ['self', 'args', 'kwargs'])

def splice_into_list(list_, splice_d,  key_fn=None, log=_log):
    """Splice sub-lists (values of *splice_d*) into list *list\_* after their
    corresponding entries (keys of *slice_d*). Example:

    .. code-block:: python

       >>> splice_into_list(['a','b','c'], {'b': ['b1', 'b2']})
       ['a', 'b', 'b1', 'b2', 'c']

    Args:
        list\_ (list): Parent list to splice sub-lists into.
        splice_d (dict): Sub-lists to splice in. Keys are entries in *list\_*
            and values are the sub-lists to insert after that entry. Duplicate
            or missing entries are handled appropriately.
        key_fn (function): Optional. If supplied, function applied to elements
            of *list\_* to compare to keys of *splice_d*.

    Returns:
        Spliced *list\_* as described above.
    """
    if key_fn is None:
        key_fn = lambda x: x
    chunks = [0, len(list_)]
    for k in splice_d:
        idx = [i + 1 for i,el in enumerate(list_) if key_fn(el) == k]
        if len(idx) > 1:
            log.debug('%s not unique (%s) in %s.', k, idx, list_)
        chunks.extend(idx)
    chunk_0, chunk_1 = itertools.tee(sorted(chunks))
    next(chunk_1, None)
    chunks = [list_[c[0]:c[1]] for c in zip(chunk_0, chunk_1)]
    spliced_chunks = []
    for c in chunks:
        if c and key_fn(c[-1]) in splice_d:
            spliced_chunks.append(c + splice_d[key_fn(c[-1])])
        else:
            spliced_chunks.append(c)
    return list(itertools.chain.from_iterable(spliced_chunks))

def deserialize_class(name):
    """Given the name of a currently defined class, return the class itself.
    This avoids security issues with calling :py:func:`eval`. Based on
    `<https://stackoverflow.com/a/11781721>`__.

    Args:
        name (str): name of the class to look up.

    Returns:
        :obj:`class` with the given name, if currently imported.

    Raises:
        :py:class:`ValueError`: If class not found in current namespace.
    """
    try:
        # for performance, search python builtin types first before going
        # through everything
        return getattr(__builtins__, name)
    except AttributeError:
        # _log.debug('%s not found in builtin types.', name)
        pass
    q = collections.deque([object]) # everything inherits from object
    while q:
        t = q.popleft()
        if t.__name__ == name:
            return t
        try: # keep looking
            q.extend(t.__subclasses__())
        except TypeError:
            # type.__subclasses__ needs an argument, for whatever reason.
            if t is type:
                continue
            else:
                raise
    raise ValueError('No such type: %r' % name)
