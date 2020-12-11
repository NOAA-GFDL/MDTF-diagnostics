"""Extensions to :py:module:`dataclasses`, for streamlined class definition.
"""
import collections
import copy
import dataclasses
import enum
import functools
import re
import typing
from . import basic

import logging
_log = logging.getLogger(__name__)

class RegexPatternBase():
    """Dummy parent class for :class:`RegexPattern` and 
    :class:`ChainedRegexPattern`.
    """
    pass

class RegexPattern(collections.UserDict, RegexPatternBase):
    """Wraps :py:class:`re.Pattern` with more convenience methods. Extracts 
    values of named fields from a string by parsing it with a regex with 
    named capture groups, and stores those values in a dict. 
    """
    def __init__(self, regex, defaults=None, input_field=None, 
        match_error_filter=None):
        """Constructor.

        Args:
            regex: str or :py:class:`re.Pattern`: regex to use for string 
                parsing. Should contain named match groups corresponding to the
                fields to parse.
            defaults: dict, optional. If supplied, any fields not matched by the
                regex will be set equal to their values here.
            input_field: str, optional. If supplied, add a field to the match with
                the supplied name which will be set equal to the contents of the
                input string on a successful match.
            match_error_filter: optional, bool or :class:`RegexPattern` or 
                :class:`ChainedRegexPattern`.
                If supplied, suppresses raising ValueErrors when match() fails.
                If boolean or none, either always or never raise ValueError.
                If a RegexPattern, try matching the input string that caused 
                the failed match against it. If it matches, do not raise an error.

        Attributes:
            data: dict, either empty when unmatched, or containing the contents
                of the match. From :py:class:`collections.UserDict`.
            fields: frozenset of fields matched by the pattern. Consists of the 
                *union* of named match groups in regex, and *all* keys in defaults.
            input_string: Contains string that was input to last call of match(),
                whether successful or not.
        """
        try:
            if isinstance(regex, re.Pattern):
                self.regex = regex
            else:
                self.regex = re.compile(regex, re.VERBOSE)
        except re.error as exc:
            raise exc
        if self.regex.groups != len(self.regex.groupindex):
            _log.warning("Unnamed match groups in regex")
        if self.regex.groups == 0:
            _log.warning("No named match groups in regex")
        
        if not defaults:
            self._defaults = dict()
        else:
            self._defaults = defaults.copy()
        self.input_field = input_field
        self._match_error_filter = match_error_filter
        self._update_fields()
    
    @property
    def is_matched(self):
        return bool(self.data)
    
    def clear(self):
        """Erase an existing match.
        """
        self.data = dict()
        self.input_string = ""
        
    def _update_fields(self):
        self.regex_fields = frozenset(self.regex.groupindex.keys())
        self.fields = self.regex_fields.union(self._defaults.keys())
        if self.input_field:
            self.fields = self.fields.union((self.input_field, ))
        self.clear()
        
    def update_defaults(self, d):
        """Update the default values used for the match with the values in d.
        """
        if d:
            self._defaults.update(d)
            self._update_fields()
                
    def match(self, str_, *args):
        self.clear() # to be safe
        self.input_string = str_
        m = self.regex.fullmatch(str_, *args)
        if not m:
            if not self._match_error_filter:
                raise ValueError("No match.")
            elif hasattr(self._match_error_filter, 'match'):
                try:
                    self._match_error_filter.match(str_, *args)
                except Exception as exc:
                    raise ValueError("No match.")
        else:    
            self.data = m.groupdict(default=NOTSET)
            for k,v in self._defaults.items():
                if self.data.get(k, NOTSET) is NOTSET:
                    self.data[k] = v
            if self.input_field:
                self.data[self.input_field] = m.string
            
            self._validate_match(m)
            if any(self.data[f] == NOTSET for f in self.fields):
                raise ValueError("No match.")
        
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
    """Adds formatted output to RegexPattern.

        Args:
            template: str, optional. Template string to use for formatting 
                contents of match in format() method. Contents of the matched
                fields will be subsituted using the {}-syntax of python string
                formatting.
            Other arguments the same
    """
    def __init__(self, regex, defaults=None, input_field=None, 
        match_error_filter=None, template=None):
        super(RegexPatternWithTemplate, self).__init__(regex, defaults=defaults, 
            input_field=input_field, match_error_filter=match_error_filter)
        self.template = template
        for f in self.fields:
            if f not in self.template:
                _log.warning("Field %s not included in output.", f)

    def format(self):
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
    """Class which takes an 'or' of multiple RegexPatterns. Matches are 
    attempted on the supplied RegexPatterns in order, with the first one that
    succeeds determining the returned answer. Public methods work the same as
    on RegexPattern.
    """
    def __init__(self, *string_patterns, defaults=None, input_field=None, match_error_filter=None):
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
            if not self._match_error_filter:
                raise ValueError("No match.")
            elif hasattr(self._match_error_filter, 'match'):
                try:
                    self._match_error_filter.match(str_, *args)
                except Exception as exc:
                    raise ValueError("No match.")
    
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
NOTSET.__doc__ = """
Sentinel object to detect uninitialized values, in cases where ``None`` is a 
valid value. 
"""

MANDATORY = basic.sentinel_object_factory('Mandatory')
MANDATORY.__doc__ = """
Sentinel object to mark :func:`mdtf_dataclass` fields that do not take a default 
value. This is a workaround to avoid errors with non-default fields coming after
default fields in the dataclass-generated ``__init__`` method under 
`inheritance <https://docs.python.org/3/library/dataclasses.html#inheritance>`__:
we use the second solution described in `https://stackoverflow.com/a/53085935`__.
"""

# declaration to allow calling with and without args: python cookbook 9.6
# https://github.com/dabeaz/python-cookbook/blob/master/src/9/defining_a_decorator_that_takes_an_optional_argument/example.py
def mdtf_dataclass(cls=None, **deco_kwargs):
    """Wrap :py:func:`~dataclasses.dataclass` class decorator to customize
    dataclasses to provide (very) rudimentary type checking and conversion. This
    is hacky, since dataclasses don't enforce type annontations for their fields.
    A better solution would be to use a deserialization library like pydantic.

    After the auto-generated ``__init__`` and the class' ``__post_init__``, the
    following tasks are performed:

    1. Verify that mandatory fields have values specified. We have to work around
       the usual :py:func:`~dataclasses.dataclass` way of doing this, because it 
       leads to errors in the signature of the dataclass-generated ``__init__`` 
       method under inheritance (mandatory fields can't come after optional 
       fields.) Mandatory fields must be designated by setting their default to
       ``MANDATORY``, and a ValueError is raised here if mandatory fields are
       uninitialized.

    2. Check each field's value to see if it's consistent with known type info. 
       If not, attempt to coerce it to that type, using a ``from_struct`` method if
       it exists. Raise ValueError if this fails.

    .. warning::
       Unlike :py:func:`~dataclasses.dataclass`, all fields **must** have a 
       *default* or *default_factory* defined. Fields which are mandatory must 
       have their default value set to the sentinel object ``MANDATORY``.

    .. warning::
       Type checking logic used is specific to the ``typing`` module in python 
       3.7. It may or may not work on newer pythons, and definitely will not 
       work with 3.5 or 3.6. See `https://stackoverflow.com/a/52664522`__.
    """
    dc_kwargs = {'init': True, 'repr': True, 'eq': True, 'order': False, 
        'unsafe_hash': False, 'frozen': False}
    dc_kwargs.update(deco_kwargs)
    if cls is None:
        # called without arguments
        return functools.partial(mdtf_dataclass, **dc_kwargs)

    cls = dataclasses.dataclass(cls, **dc_kwargs)
    _old_init = cls.__init__

    @functools.wraps(_old_init)
    def _new_init(self, *args, **kwargs):
        # Execute dataclass' auto-generated __init__ and __post_init__:
        _old_init(self, *args, **kwargs)
        
        for f in dataclasses.fields(self):
            if not f.init:
                # ignore fields that aren't handled at init
                continue
            value = getattr(self, f.name)
            # ignore unset field values, regardless of type
            if value is None or value is NOTSET:
                continue
            if value is MANDATORY:
                raise ValueError((f"{self.__class__.__name__}: No value supplied "
                    f"for mandatory field {f.name}."))
            # guess what types are valid
            new_type = None
            if f.type is typing.Any or isinstance(f.type, typing.TypeVar):
                continue
            elif isinstance(f.type, typing._GenericAlias) \
                or isinstance(f.type, typing._SpecialForm):
                # type is a generic from typing module, eg "typing.List"
                if f.type.__origin__ is typing.Union:
                    new_type = None # can't do coercion, but can test type
                    valid_types = list(f.type.__args__)
                elif issubclass(f.type.__origin__, typing.Generic):
                    continue # can't do anything in this case
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
            
            try:
                if isinstance(value, tuple(valid_types)):
                    continue
                if new_type is None or hasattr(new_type, '__abstract_methods__'):
                    continue
                    # # can't do type coercion, so print a warning
                    # print((f"\tWarning: {self.__class__.__name__}: type of "
                    #     f" {f.name} is ({f.type}), recieved {repr(value)} of "
                    #     "conflicting type."))
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
                _log.exception("%s", repr(exc))
                raise TypeError((f"{self.__class__.__name__}: Expected {f.name} "
                    f"to be {f.type}, got {type(value)} ({repr(value)}).")) from exc

    type.__setattr__(cls, '__init__', _new_init)
    return cls

def regex_dataclass(pattern):
    """Decorator for a dataclass that adds a from_string classmethod which 
    creates instances of that dataclass by parsing an input string with a 
    :class:`RegexPattern` or :class:`ChainedRegexPattern`. The values of all
    fields returned by the match() method of the pattern are passed to the 
    __init__ method of the dataclass as kwargs.
    """
    def _dataclass_decorator(cls):
        def _from_string(cls_, str_, *args):
            cls_._pattern.match(str_, *args)
            return cls_(**cls_._pattern.data)

        type.__setattr__(cls, '_pattern', pattern)
        type.__setattr__(cls, 'from_string', classmethod(_from_string))
        return cls
    return _dataclass_decorator

def dataclass_factory(dataclass_decorator, class_name, *parents, **kwargs):
    """Function that returns a dataclass (ie, a decorated class) whose fields 
    are the union of the fields specified in its parent classes.

    Args:
        dataclass_decorator: decorator to apply to the new class.
        class_name: name of the new class.
        parents: collection of other mdtf_dataclasses to inherit from. Order in
            the collection determines the MRO.
        kwargs: optional; arguments to pass to dataclass_decorator when it's
            applied to produce the returned class.
    """ 
    def _to_dataclass(self, cls_, **kwargs_):
        f"""Method to create an instance of one of the parent classes of
        {class_name} by copying over the relevant subset of fields.
        """
        new_kwargs = filter_dataclass(self, cls_)
        new_kwargs.update(kwargs_)
        return cls_(**new_kwargs)

    def _from_dataclasses(cls_, *other_dcs, **kwargs_):
        f"""Classmethod to create a new instance of {class_name} from instances
        of its parents, along with any other field values passed in kwargs.
        """
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
    """Given a dataclass dc (may be the class or an instance of it), and a dict,
    dataclass or dataclass instance d, return a dict of the subset of fields or 
    entries in d that correspond to the fields in dc.

    If init=True, include any `init-only fields 
    <https://docs.python.org/3/library/dataclasses.html#init-only-variables>`__
    that dc has in the returned dict.
    """
    assert dataclasses.is_dataclass(dc)
    if dataclasses.is_dataclass(d):
        if isinstance(d, type):
            d = d() # d is a class; instantiate with default field values
        d = dataclasses.asdict(d)
    ans = {f.name: d[f.name] for f in dataclasses.fields(dc) if f.name in d}
    if init:
        init_fields = filter(
            (lambda f: f.type == dataclasses.InitVar), 
            dc.__dataclass_fields__.values()
        )
        ans.update({f.name: d[f.name] for f in init_fields if f.name in d})
    return ans
    
def coerce_to_dataclass(d, dc, **kwargs):
    """Given a dataclass dc (may be the class or an instance of it), and a dict,
    dataclass or dataclass instance d, return an instance of dc's class with 
    field values initialized from those in d, along with any extra values
    passed in kwargs.
    """
    new_kwargs = filter_dataclass(d, dc, init=True)
    new_kwargs.update(kwargs)
    if not isinstance(dc, type):
        dc = dc.__class__
    return dc(**new_kwargs)
