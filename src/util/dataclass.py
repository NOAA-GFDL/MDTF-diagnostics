"""Extensions to Python :py:mod:`dataclasses`, for streamlined class definition.
"""
import collections
import copy
import dataclasses
import enum
import functools
import re
import typing
from . import basic
from . import exceptions

import logging
_log = logging.getLogger(__name__)

class RegexPatternBase():
    """Dummy parent class for :class:`RegexPattern` and
    :class:`ChainedRegexPattern`.
    """
    pass

class RegexPattern(collections.UserDict, RegexPatternBase):
    """Wraps :py:class:`re.Pattern` with more convenience methods for the use case
    of parsing information in a string, using a regex with named capture groups
    corresponding to the data fields being collected from the string.
    """
    def __init__(self, regex, defaults=None, input_field=None,
        match_error_filter=None):
        """Constructor.

        Args:
            regex (str or :py:class:`re.Pattern`): regex to use for string
                parsing. Should contain named match groups corresponding to the
                fields to parse.
            defaults (dict): Optional. If supplied, any fields not matched by the
                named match groups in *regex* will be set equal to their values here.
            input_field (str): Optional. If supplied, add a field to the match with
                the supplied name which will be set equal to the contents of the
                input string on a successful match.
            match_error_filter (bool or :class:`RegexPattern` or :class:`ChainedRegexPattern`):
                Optional. If supplied, determines whether a ValueError is raised
                when the :meth:`match` method fails to parse a string (see below.)

        Attributes:
            data (dict): Key:value pairs corresponding to the contents of the
                matching groups from the last successful call to :meth:`match`, or
                empty if no successful call has been made. From
                :py:class:`collections.UserDict`.
            fields (frozenset): Set of fields matched by the pattern. Consists of the
                union of named match groups in *regex*, and all keys in *defaults*.
            input_string (str): Contains string that was input to last call of
                :meth:`match`, whether successful or not.
            is_matched (bool): True if the last call to :meth:`match` was
                successful, False otherwise.
        """
        try:
            if isinstance(regex, re.Pattern):
                self.regex = regex
            else:
                self.regex = re.compile(regex, re.VERBOSE)
        except re.error as exc:
            raise ValueError('Malformed input regex.') from exc
        if self.regex.groups != len(self.regex.groupindex):
            # _log.warning("Unnamed match groups in regex")
            pass
        if self.regex.groups == 0:
            # _log.warning("No named match groups in regex")
            pass

        if not defaults:
            self._defaults = dict()
        else:
            self._defaults = defaults.copy()
        self.input_field = input_field
        self._match_error_filter = match_error_filter
        self._update_fields()

    def clear(self):
        """Erase field values parsed from a pre-existing match.
        """
        self.data = dict()
        self.input_string = ""
        self.is_matched = False

    def _update_fields(self):
        self.regex_fields = frozenset(self.regex.groupindex.keys())
        self.fields = self.regex_fields.union(self._defaults.keys())
        if self.input_field:
            self.fields = self.fields.union((self.input_field, ))
        self.clear()

    def update_defaults(self, d):
        """Update the default values used for the match with the values in *d*.
        """
        if d:
            self._defaults.update(d)
            self._update_fields()

    def match(self, str_, *args):
        """Match *str\_* using Python :py:func:`re.fullmatch` with *regex* and
        populate object's fields according to the values captured by the named
        capture groups in *regex*.

        Args:
            str\_ (str): Input string to parse.
            args: Optional. Flags (as defined in Python :py:mod:`re`) to use in
                the :py:func:`re.fullmatch` method of the *regex* and *match_error_filter*
                (if defined.)

        Raises:
            :class:`~exceptions.RegexParseError`: If :meth:`match` fails to parse
                the input string, and the following conditions on *match_error_filter*
                are met. If *match_error_filter* not supplied
                (default), always raise when :meth:`match` fails. If *match_error_filter*
                is bool, always/never raise. If *match_error_filter*
                is a :class:`RegexPattern` or :class:`ChainedRegexPattern`, attempt
                to :meth:`match` the input string that caused the failed match
                against the value of *match_error_filter*. If it matches, do not
                raise an error; otherwise raise an error.
            :class:`~exceptions.RegexSuppressedError`: If :meth:`match` fails to
                parse the input string and the above conditions involving
                *match_error_filter* are not met. One of RegexParseError or
                RegexSuppressedError is always raised on failure.
        """
        self.clear() # to be safe
        self.input_string = str_
        m = self.regex.fullmatch(str_, *args)
        if not m:
            self.is_matched = False
            if hasattr(self._match_error_filter, 'match'):
                try:
                    self._match_error_filter.match(str_, *args)
                except Exception as exc:
                    raise exceptions.RegexParseError(
                        f"Couldn't match {str_} against {self.regex}.")
                raise exceptions.RegexSuppressedError(str_)
            elif self._match_error_filter:
                raise exceptions.RegexSuppressedError(str_)
            else:
                raise exceptions.RegexParseError(
                    f"Couldn't match {str_} against {self.regex}.")
        else:
            self.data = m.groupdict(default=NOTSET)
            for k,v in self._defaults.items():
                if self.data.get(k, NOTSET) is NOTSET:
                    self.data[k] = v
            if self.input_field:
                self.data[self.input_field] = m.string

            self._validate_match(m)
            if any(self.data[f] is NOTSET for f in self.fields):
                bad_names = [f for f in self.fields if self.data[f] is NOTSET]
                raise exceptions.RegexParseError((f"Couldn't match the "
                    f"following fields in {str_}: " + ', '.join(bad_names) ))
            self.is_matched = True

    def _validate_match(self, match_obj):
        """Hook for post-processing of match, running after all fields are
        assigned but before final check that all fields are set.
        """
        pass

    def __str__(self):
        if not self.is_matched:
            str_ = ', '.join(self.fields)
        else:
            str_ = ', '.join([f'{k}={v}' for k,v in self.data.items()])
        return f"<{self.__class__.__name__}({str_})>"

    def __copy__(self):
        if hasattr(self._match_error_filter, 'copy'):
            match_error_filter_copy = self._match_error_filter.copy()
        else:
            # bool or None
            match_error_filter_copy = self._match_error_filter
        obj = self.__class__(
            self.regex.pattern,
            defaults=self._defaults.copy(),
            input_field=self.input_field,
            match_error_filter=match_error_filter_copy,
        )
        obj.data = self.data.copy()
        return obj

    def __deepcopy__(self, memo):
        obj = self.__class__(
            copy.deepcopy(self.regex.pattern, memo),
            defaults=copy.deepcopy(self._defaults, memo),
            input_field=copy.deepcopy(self.input_field, memo),
            match_error_filter=copy.deepcopy(self._match_error_filter, memo)
        )
        obj.data = copy.deepcopy(self.data, memo)
        return obj

class RegexPatternWithTemplate(RegexPattern):
    """Adds formatted output to :class:`RegexPattern`.
    """
    def __init__(self, regex, defaults=None, input_field=None,
        match_error_filter=None, template=None, log=_log):
        """Constructor.

        Args:
            template (str): Optional. Template string to use for formatting
                contents of match in :meth:`format` method. Contents of the matched
                fields will be subsituted using the {}-syntax of python string
                formatting.

        Other arguments are the same as in :class:`RegexPattern`.
        """
        super(RegexPatternWithTemplate, self).__init__(regex, defaults=defaults,
            input_field=input_field, match_error_filter=match_error_filter)
        self.template = template
        for f in self.fields:
            if f not in self.template:
                log.warning("Field %s not included in output.", f)

    def format(self):
        """Return *template* string, templated with the values obtained in the last
        successful call to :meth:`match`.
        """
        if self.template is None:
            raise AssertionError('Template string needs to be defined.')
        if not self.is_matched:
            raise ValueError('No match')
        return self.template.format(**self.data)

    def __copy__(self):
        if hasattr(self._match_error_filter, 'copy'):
            match_error_filter_copy = self._match_error_filter.copy()
        else:
            # bool or None
            match_error_filter_copy = self._match_error_filter
        obj = self.__class__(
            self.regex.pattern,
            defaults=self._defaults.copy(),
            input_field=self.input_field,
            match_error_filter=match_error_filter_copy,
            template=self.template
        )
        obj.data = self.data.copy()
        return obj

    def __deepcopy__(self, memo):
        obj = self.__class__(
            copy.deepcopy(self.regex.pattern, memo),
            defaults=copy.deepcopy(self._defaults, memo),
            input_field=copy.deepcopy(self.input_field, memo),
            match_error_filter=copy.deepcopy(self._match_error_filter, memo),
            template=copy.deepcopy(self.template, memo)
        )
        obj.data = copy.deepcopy(self.data, memo)
        return obj

class ChainedRegexPattern(RegexPatternBase):
    """Class which takes an 'or' of multiple :class:`RegexPattern`\s, to parse
    data that may be represented as a string in one of multiple formats.

    Matches are attempted on the supplied RegexPatterns in order, with the first
    one that succeeds determining the parsed field values. Public methods work
    the same as on :class:`RegexPattern`.
    """
    def __init__(self, *string_patterns, defaults=None, input_field=None,
        match_error_filter=None):
        """Constructor.

        Args:
            string_patterns (iterable of :class:`RegexPattern`): Individual
                regexes which will be tried, in order, when :meth:`match` is
                called. Parsing will be done by the first RegexPattern whose
                :meth:`match` succeeds.

        .. note::
           The constructor changes attributes on :class:`RegexPattern` objects
           passed as *string_patterns*, so once the object is created its
           component :class:`RegexPattern` objects shouldn't be accessed on
           their own.

        Other arguments and attributes are the same as in :class:`RegexPattern`.
        """
        # NB, changes attributes on patterns passed as arguments, so
        # once created they can't be used on their own
        new_pats = []
        for pat in string_patterns:
            if isinstance(pat, RegexPattern):
                new_pats.append(pat)
            elif isinstance(pat, ChainedRegexPattern):
                new_pats.extend(pat._patterns)
            else:
                raise ValueError("Bad input")
        self._patterns = tuple(string_patterns)
        if input_field:
            self.input_field = input_field
        self._match_error_filter = match_error_filter
        for pat in self._patterns:
            if defaults:
                pat.update_defaults(defaults)
            if input_field:
                pat.input_field = input_field
            pat._match_error_filter = None
            pat._update_fields()
        self._update_fields()

    @property
    def is_matched(self):
        return (self._match >= 0)

    @property
    def data(self):
        if self.is_matched:
            return self._patterns[self._match].data
        else:
            return dict()

    def clear(self):
        for pat in self._patterns:
            pat.clear()
        self._match = -1
        self.input_string = ""

    def _update_fields(self):
        self.fields = self._patterns[0].fields
        for pat in self._patterns:
            if pat.fields != self.fields:
                raise ValueError("Incompatible fields.")
        self.clear()

    def update_defaults(self, d):
        if d:
            for pat in self._patterns:
                pat.update_defaults(d)
        self._update_fields()

    def match(self, str_, *args):
        self.clear()
        self.input_string = str_
        for i, pat in enumerate(self._patterns):
            try:
                pat.match(str_, *args)
                if not pat.is_matched:
                    raise ValueError()
                self._match = i
            except ValueError:
                continue
        if not self.is_matched:
            if hasattr(self._match_error_filter, 'match'):
                try:
                    self._match_error_filter.match(str_, *args)
                except Exception as exc:
                    raise exceptions.RegexParseError((f"Couldn't match {str_} "
                        f"against any pattern in {self.__class__.__name__}."))
                raise exceptions.RegexSuppressedError(str_)
            elif self._match_error_filter:
                raise exceptions.RegexSuppressedError(str_)
            else:
                raise exceptions.RegexParseError((f"Couldn't match {str_} "
                    f"against any pattern in {self.__class__.__name__}."))

    def __str__(self):
        if not self.is_matched:
            str_ = ', '.join(self.fields)
        else:
            str_ = ', '.join([f'{k}={v}' for k,v in self.data.items()])
        return f"<{self.__class__.__name__}({str_})>"

    def format(self):
        if not self.is_matched:
            raise ValueError('No match')
        return self._patterns[self._match].format()

    def __copy__(self):
        new_pats = (pat.copy() for pat in self._patterns)
        return self.__class__(
            *new_pats,
            match_error_filter=self._match_error_filter.copy()
        )

    def __deepcopy__(self, memo):
        new_pats = (copy.deepcopy(pat, memo) for pat in self._patterns)
        return self.__class__(
            *new_pats,
            match_error_filter=copy.deepcopy(self._match_error_filter, memo)
        )

# ---------------------------------------------------------

NOTSET = basic.sentinel_object_factory('NotSet')
"""
Sentinel object to detect uninitialized values for fields in :func:`mdtf_dataclass`
objects, for use in cases where ``None`` is a valid value for the field.
"""

MANDATORY = basic.sentinel_object_factory('Mandatory')
"""
Sentinel object to mark all :func:`mdtf_dataclass` fields that do not take a default
value. This is a workaround to avoid errors with non-default fields coming after
default fields in the dataclass auto-generated ``__init__`` method under
`inheritance <https://docs.python.org/3/library/dataclasses.html#inheritance>`__:
we use the second solution described in `<https://stackoverflow.com/a/53085935>`__.
"""

def _mdtf_dataclass_get_field_types(obj, f):
    """Common functionality for :func:`_mdtf_dataclass_type_coercion` and
    :func:`_mdtf_dataclass_type_check`. Given a :py:class:`datacalsses.Field`
    object *f*, return either a tuple of the type its value should be coerced to
    and a tuple of the valid types its value can have, or (None, None) to signal
    a case we don't handle.
    """
    if not f.init:
        # ignore fields that aren't handled at init
        return (None, None)
    value = getattr(obj, f.name)
    # ignore unset field values, regardless of type
    if value is None or value is NOTSET:
        return (None, None)
    # guess what types are valid
    new_type = None
    if f.type is typing.Any or isinstance(f.type, typing.TypeVar):
        return (None, None)
    if dataclasses.is_dataclass(f.type):
        # ignore if type is a dataclass: use this type annotation to
        # implement dataclass inheritance
        if not isinstance(obj, f.type):
            raise exceptions.DataclassParseError((f"Field {f.name} specified "
                f"as dataclass {f.type.__name__}, which isn't a parent class "
                f"of {obj.__class__.__name__}."))
        return (None, None)
    elif isinstance(f.type, typing._GenericAlias) \
        or isinstance(f.type, typing._SpecialForm):
        # type is a generic from typing module, eg "typing.List"
        if f.type.__origin__ is typing.Union:
            new_type = None # can't do coercion, but can test type
            valid_types = list(f.type.__args__)
        elif issubclass(f.type.__origin__, typing.Generic):
            return (None, None) # can't do anything in this case
        else:
            new_type = f.type.__origin__
            valid_types = [new_type]
    else:
        new_type = f.type
        valid_types = [new_type]
    # Get types of field's default value, if present. Dataclass doesn't
    # require defaults to be same type as what's given for field.
    if not isinstance(f.default, dataclasses._MISSING_TYPE):
        valid_types.append(type(f.default))
    if not isinstance(f.default_factory, dataclasses._MISSING_TYPE):
        valid_types.append(type(f.default_factory()))
    return (new_type, valid_types)

def _mdtf_dataclass_type_coercion(self, log):
    """Do type checking on all dataclass fields after the auto-generated
    ``__init__`` method, but before any ``__post_init__`` method.

    .. warning::
       Type checking logic used is specific to the ``typing`` module in python
       3.7. It may or may not work on newer pythons, and definitely will not
       work with 3.5 or 3.6. See `<https://stackoverflow.com/a/52664522>`__.
    """
    for f in dataclasses.fields(self):
        value = getattr(self, f.name, NOTSET)
        new_type, valid_types = _mdtf_dataclass_get_field_types(self, f)
        try:
            if valid_types is None or isinstance(value, tuple(valid_types)):
                continue # don't coerce if we're already a valid type
            if new_type is None or hasattr(new_type, '__abstract_methods__'):
                continue # can't do type coercion
            else:
                if hasattr(new_type, 'from_struct'):
                    new_value = new_type.from_struct(value)
                elif isinstance(new_type, enum.Enum):
                    # need to use item syntax to create enum from name
                    new_value = new_type.__getitem__(value)
                else:
                    new_value = new_type(value)
                # https://stackoverflow.com/a/54119384 for implementation
                object.__setattr__(self, f.name, new_value)
        except (TypeError, ValueError, dataclasses.FrozenInstanceError) as exc:
            raise exceptions.DataclassParseError((f"{self.__class__.__name__}: "
                f"Couldn't coerce value {repr(value)} for field {f.name} from "
                f"type {type(value)} to type {new_type}.")) from exc
        except Exception as exc:
            log.exception("%s: Caught exception: %r", self.__class__.__name__, exc)
            raise exc

def _mdtf_dataclass_type_check(self, log):
    """Do type checking on all dataclass fields after ``__init__`` and
    ``__post_init__`` methods.

    .. warning::
       Type checking logic used is specific to the ``typing`` module in python
       3.7. It may or may not work on newer pythons, and definitely will not
       work with 3.5 or 3.6. See `<https://stackoverflow.com/a/52664522>`__.
    """
    for f in dataclasses.fields(self):
        value = getattr(self, f.name, NOTSET)
        if value is None or value is NOTSET:
            continue
        if value is MANDATORY:
            raise exceptions.DataclassParseError((f"{self.__class__.__name__}: "
                f"No value supplied for mandatory field {f.name}."))

        _, valid_types = _mdtf_dataclass_get_field_types(self, f)
        if valid_types is not None and not isinstance(value, tuple(valid_types)):
            log.exception("%s: Failed type check for field '%s': %s != %s.",
                self.__class__.__name__, f.name, type(value), valid_types)
            raise exceptions.DataclassParseError((f"{self.__class__.__name__}: "
                f"Expected {f.name} to be {f.type}, got {type(value)} "
                f"({repr(value)})."))

DEFAULT_MDTF_DATACLASS_KWARGS = {'init': True, 'repr': True, 'eq': True,
    'order': False, 'unsafe_hash': False, 'frozen': False}

# declaration to allow calling with and without args: python cookbook 9.6
# https://github.com/dabeaz/python-cookbook/blob/master/src/9/defining_a_decorator_that_takes_an_optional_argument/example.py
def mdtf_dataclass(cls=None, **deco_kwargs):
    """Wrap the Python :py:func:`~dataclasses.dataclass` class decorator to customize
    dataclasses to provide rudimentary type checking and conversion. This
    is hacky, since dataclasses don't enforce type annontations for their fields.
    A better solution would be to use the third-party
    `cattrs <https://github.com/Tinche/cattrs>`__ package, which has essentially
    the same aim.

    The decorator rewrites the class's constructor as follows:

    1. Execute the auto-generated ``__init__`` method from Python
       :py:func:`~dataclasses.dataclass`.

    2. Verify that fields with ``MANDATORY`` default have been assigned values.
       We have to work around the usual :py:func:`~dataclasses.dataclass` way of
       doing this, because it leads to errors in the signature of the auto-generated
       ``__init__`` method under inheritance (mandatory fields can't come after
       optional fields in the signature.)

    3. Execute the class's ``__post_init__`` method, if defined, which can do
       more complex type coercion and validation.

    4. Finally, check each field's value to see if it's consistent with the given
       type information. If not, attempt to coerce it to that type, using a
       ``from_struct`` method on that type if it exists.

    .. warning::
       Unlike :py:func:`~dataclasses.dataclass`, all fields **must** have a
       *default* or *default_factory* defined. Fields which are mandatory must
       have their default value set to the sentinel object ``MANDATORY``.
       This is necessary in order for dataclass inheritance to work properly, and
       is not currently enforced when the class is decorated.

    Args:
        cls (class): Class to be decorated.
        deco_kwargs: Optional. Keyword arguments to pass to the Python
            :py:func:`~dataclasses.dataclass` class decorator.

    Raises:
        :class:`~exceptions.DataclassParseError`: If we attempted to construct an
            instance without giving values for ``MANDATORY`` fields, or if values
            of some fields after ``__post_init__`` could not be coerced into the
            types given in their annotation.
    """
    dc_kwargs = DEFAULT_MDTF_DATACLASS_KWARGS.copy()
    dc_kwargs.update(deco_kwargs)
    if cls is None:
        # called without arguments
        return functools.partial(mdtf_dataclass, **dc_kwargs)

    if not hasattr(cls, '__post_init__'):
        # create dummy __post_init__ if none defined, so we can wrap it.
        # contrast with what we do below in regex_dataclass()
        def _dummy_post_init(self, *args, **kwargs): pass
        type.__setattr__(cls, '__post_init__', _dummy_post_init)

    # apply dataclasses' decorator
    cls = dataclasses.dataclass(cls, **dc_kwargs)

    # Do type coercion after dataclass' __init__, but before user __post_init__
    # Do type check after __init__ and __post_init__
    _old_post_init = cls.__post_init__
    @functools.wraps(_old_post_init)
    def _new_post_init(self, *args, **kwargs):
        if hasattr(self, 'log'):
            _post_init_log = self.log # for object hierarchy
        else:
            _post_init_log = _log # fallback: use module-level logger
        _mdtf_dataclass_type_coercion(self, _post_init_log)
        _old_post_init(self, *args, **kwargs)
        _mdtf_dataclass_type_check(self, _post_init_log)
    type.__setattr__(cls, '__post_init__', _new_post_init)

    return cls

def is_regex_dataclass(obj):
    """Returns True if *obj* is a :func:`regex_dataclass`.
    """
    return hasattr(obj, '_is_regex_dataclass') and obj._is_regex_dataclass == True

def _regex_dataclass_preprocess_kwargs(self, kwargs):
    """Edit kwargs going to the auto-generated __init__ method of this dataclass.
    If any fields are regex_dataclasses, construct and parse their values first.

    Raises a DataclassParseError if different regex_dataclasses (at any level of
    inheritance) try to assign different values to a field of the same name. We
    do this by assigning to a :class:`~src.util.basic.ConsistentDict`.
    """
    new_kw = filter_dataclass(kwargs, self, init='all')
    new_kw = basic.ConsistentDict.from_struct(new_kw)
    for cls_ in self.__class__.__bases__:
        if not is_regex_dataclass(cls_):
            continue
        for f in dataclasses.fields(self):
            if not f.type == cls_:
                continue
            if f.name in kwargs:
                val = kwargs[f.name]
            elif not isinstance(f.default, dataclasses._MISSING_TYPE):
                val = f.default
            elif not isinstance(f.default_factory, dataclasses._MISSING_TYPE):
                val = f.default_factory()
            else:
                raise exceptions.DataclassParseError(f"Can't set value for {f.name}.")
            new_d = dataclasses.asdict(f.type.from_string(val))
            new_d = filter_dataclass(new_d, self, init='all')
            try:
                new_kw.update(new_d)
            except exceptions.WormKeyError as exc:
                raise exceptions.DataclassParseError((f"{self.__class__.__name__}: "
                    f"Tried to make inconsistent field assignment when parsing "
                    f"{f.name} as an instance of {f.type.__name__}.")) from exc
    post_init = dict()
    for f in dataclasses.fields(self):
        if not f.init and f.name in new_kw:
            post_init[f.name] = new_kw.pop(f.name)
    return (new_kw, post_init)

def regex_dataclass(pattern, **deco_kwargs):
    """Decorator combining the functionality of :class:`RegexPattern` and
    :func:`mdtf_dataclass`: dataclass fields are parsed from a regex and coerced
    to appropriate classes.

    Specifically, this is done via a ``from_string`` classmethod, added by this
    decorator, which creates dataclass instances by parsing an input string with
    a :class:`RegexPattern` or :class:`ChainedRegexPattern`. The values of all
    fields returned by the :meth:`~RegexPattern.match` method of the pattern are
    passed to the ``__init__`` method of the dataclass as kwargs.

    Additionally, if the type of one or more fields is set to a class that's
    also been decorated with regex_dataclass, the parsing logic for that field's
    regex_dataclass will be invoked on that field's value (i.e., a string obtained
    by regex matching in *this* regex_dataclass), and the parsed values of those
    fields will be supplied to this regex_dataclass constructor. This is our
    implementation of composition for regex_dataclasses.

    .. note::
       Unlike :func:`mdtf_dataclass`, type coercion here is done *after*
       ``__post_init__`` for these dataclasses. This is necessary due to
       composition: if a regex_dataclass is being instantiated as a field of
       another regex_dataclass, all values being passed to it will be strings
       (the regex fields), and type coercion is the job of ``__post_init__``.
    """
    dc_kwargs = DEFAULT_MDTF_DATACLASS_KWARGS.copy()
    dc_kwargs.update(deco_kwargs)

    def _dataclass_decorator(cls):
        if '__post_init__' not in cls.__dict__:
            # Prevent class from inheriting __post_init__ from parents if it
            # doesn't overload it (which is why we use __dict__ and not
            # hasattr().) __post_init__ of all parents will have been called when
            # the parent classes are instantiated by _regex_dataclass_preprocess_kwargs.
            def _dummy_post_init(self, *args, **kwargs): pass
            type.__setattr__(cls, '__post_init__', _dummy_post_init)

        # apply dataclasses' decorator
        cls = dataclasses.dataclass(cls, **dc_kwargs)
        # check that all DCs specified as fields are also in class hierarchy
        # so that we inherit their fields; probably no way this could happen though
        for f in dataclasses.fields(cls):
            if is_regex_dataclass(f.type) and f.type not in cls.__mro__:
                raise TypeError((f"{cls.__name__}: Field {f.name} specified as "
                    f"{f.type.__name__}, but we don't inherit from it."))

        _old_init = cls.__init__
        @functools.wraps(_old_init)
        def _new_init(self, first_arg=None, *args, **kwargs):
            if isinstance(first_arg, str) and not args and not kwargs:
                # instantiate from running regex on string, if a string is the
                # only argument to the constructor
                self._pattern.match(first_arg)
                first_arg = None
                kwargs = self._pattern.data
            new_kw, other_kw = _regex_dataclass_preprocess_kwargs(self, kwargs)
            for k,v in other_kw.items():
                # set field values that aren't arguments to _old_init
                object.__setattr__(self, k, v)
            if first_arg is None:
                _old_init(self, *args, **new_kw)
            else:
                _old_init(self, first_arg, *args, **new_kw)

            _mdtf_dataclass_type_coercion(self, _log)
            _mdtf_dataclass_type_check(self, _log)
        type.__setattr__(cls, '__init__', _new_init)

        def _from_string(cls_, str_, *args):
            """Create an object instance from a string representation *str\_*.
            Used by :func:`regex_dataclass` for parsing field values and automatic
            type coercion.
            """
            cls_._pattern.match(str_, *args)
            return cls_(**cls_._pattern.data)
        type.__setattr__(cls, 'from_string', classmethod(_from_string))

        type.__setattr__(cls, '_is_regex_dataclass', True)
        type.__setattr__(cls, '_pattern', pattern)
        return cls
    return _dataclass_decorator

def dataclass_factory(dataclass_decorator, class_name, *parents, **kwargs):
    """Function that returns a dataclass (ie, a decorated class) whose fields
    are the union of the fields in *parents*, which the new dataclass inherits
    from.

    Args:
        dataclass_decorator (function): decorator to apply to the new class.
        class_name (str): name of the new class.
        parents: collection of other mdtf_dataclasses to inherit from. Order in
            the collection determines the MRO.
        kwargs: Optional; arguments to pass to dataclass_decorator when it's
            applied to produce the returned class.
    """
    def _to_dataclass(self, cls_, **kwargs_):
        f"""Method to create an instance of one of the parent classes of
        {class_name} by copying over the relevant subset of fields.
        """
        # above docstring gets templated
        new_kwargs = filter_dataclass(self, cls_)
        new_kwargs.update(kwargs_)
        return cls_(**new_kwargs)

    def _from_dataclasses(cls_, *other_dcs, **kwargs_):
        f"""Classmethod to create a new instance of {class_name} from instances
        of its parents, along with any other field values passed in kwargs.
        """
        # above docstring gets templated
        new_kwargs = dict()
        for dc in other_dcs:
            new_kwargs.update(filter_dataclass(dc, cls_))
        new_kwargs.update(kwargs_)
        return cls_(**new_kwargs)

    methods = {
        'to_dataclass': _to_dataclass,
        'from_dataclasses': classmethod(_from_dataclasses),
    }
    for dc in parents:
        method_nm = 'to_' + dc.__name__
        methods[method_nm] = functools.partialmethod(_to_dataclass, cls_=dc)
    new_cls = type(class_name, tuple(parents), methods)
    return dataclass_decorator(new_cls, **kwargs)

# ----------------------------------------------------

def filter_dataclass(d, dc, init=False):
    """Return a dict of the subset of fields or entries in *d* that correspond to
    the fields in dataclass *dc*.

    Args:
        d (dict, dataclass or dataclass instance): Object to take field values from.
        dc (dataclass or dataclass instance): Dataclass defining the set of fields
            that are returned. Values of fields in *d* that are not fields of *dc*
            are discarded.
        init (bool or 'all'): Optional, default False. Controls whether `init-only fields
            <https://docs.python.org/3/library/dataclasses.html#init-only-variables>`__
            are included:

            - If False: Include only the fields of *dc* as returned by
              :py:func:`dataclasses.fields`.
            - If True: Include only the arguments to *dc*\'s constructor (i.e.,
              include any init-only fields and exclude any of *dc*\'s fields
              with *init*\=False.)
            - If 'all': Include the union of the above two options.

    Returns:
        dict: The subset of key:value pairs from *d* such that the keys are
        included in the set of *dc*\'s fields specified by the value of *init*.
    """
    assert dataclasses.is_dataclass(dc)
    if dataclasses.is_dataclass(d):
        if isinstance(d, type):
            d = d() # d is a class; instantiate with default field values
        d = dataclasses.asdict(d)
    if not init or (init == 'all'):
        ans = {f.name: d[f.name] for f in dataclasses.fields(dc) if f.name in d}
    else:
        ans = {f.name: d[f.name] for f in dataclasses.fields(dc) \
            if (f.name in d and f.init)}
    if init or (init == 'all'):
        init_fields = filter(
            (lambda f: f.type == dataclasses.InitVar),
            dc.__dataclass_fields__.values()
        )
        ans.update({f.name: d[f.name] for f in init_fields if f.name in d})
    return ans

def coerce_to_dataclass(d, dc, **kwargs):
    """Given a dataclass *dc* (may be the class or an instance of it), and a dict,
    dataclass or dataclass instance *d*, return an instance of *dc*\'s class with
    field values initialized from those in *d*, along with any extra values
    passed in *kwargs*.

    Because this constructs a new dataclass instance, it copies field values
    according to the *init*\=True logic in :func:`filter_dataclass`.

    Args:
        d (dict, dataclass or dataclass instance): Object to take field values from.
        dc (dataclass or dataclass instance): Class to instantiate.
        kwargs: Optional. If provided, override field values provided in *d*.

    Returns:
        Instance of dataclass *dc* with field values populated from *kwargs* and *d*.
    """
    new_kwargs = filter_dataclass(d, dc, init=True)
    if kwargs:
        new_kwargs.update(kwargs)
        new_kwargs = filter_dataclass(new_kwargs, dc, init=True)
    if not isinstance(dc, type):
        dc = dc.__class__
    return dc(**new_kwargs)
