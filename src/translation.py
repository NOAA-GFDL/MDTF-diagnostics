"""Utilities for variable translation
"""
import os
import sys
import abc
import collections
import copy
import dataclasses as dc
import glob
import typing
from src import util, data_model, units
from src.units import Units

import logging
_log = logging.getLogger(__name__)

_NO_TRANSLATION_CONVENTION = 'None' # naming convention for disabling translation


@util.mdtf_dataclass
class TranslatedVarlistEntry(data_model.DMVariable):
    """Class returned by :meth:`VarlistTranslator.translate`. Marks some
    attributes inherited from :class:`~data_model.DMVariable` as being queryable
    in :meth:`~data_manager.DataframeQueryDataSourceBase.query_dataset`.
    """
    # to be more correct, we should probably have VarlistTranslator return a
    # DMVariable, which is converted to this type on assignment to the
    # VarlistEntry, since metadata fields are specific to the VarlistEntry
    # implementation.
    convention: str = util.MANDATORY
    name: str = \
        dc.field(default=util.MANDATORY, metadata={'query': True})
    standard_name: str = \
        dc.field(default=util.MANDATORY, metadata={'query': True})
    units: Units = util.MANDATORY
    # dims: list           # fields inherited from data_model.DMVariable
    # modifier : str
    scalar_coords: list = \
        dc.field(init=False, default_factory=list, metadata={'query': True})
    log: typing.Any = util.MANDATORY # assigned from parent var


@util.mdtf_dataclass
class FieldlistEntry(data_model.DMDependentVariable):
    """Class corresponding to an entry in a fieldlist file.
    """
    # name: str             # fields inherited from DMDependentVariable
    # standard_name: str
    # units: Units
    # modifier : str
    # dims: list            # fields inherited from _DMDimensionsMixin
    # scalar_coords: list
    scalar_coord_templates: dict = dc.field(default_factory=dict)

    def __post_init__(self, coords=None):
        super(FieldlistEntry, self).__post_init__(coords)
        assert len(self.scalar_coords) == 0

    _ndim_to_axes_set = {
        # allow specifying dimensionality as shorthand for explicit list
        # of coordinate dimension names
        1: ('PLACEHOLDER_T_COORD'),
        2: ('PLACEHOLDER_Y_COORD', 'PLACEHOLDER_X_COORD'),
        3: ('PLACEHOLDER_T_COORD', 'PLACEHOLDER_Y_COORD', 'PLACEHOLDER_X_COORD'),
        4: ('PLACEHOLDER_T_COORD', 'PLACEHOLDER_Z_COORD', 'PLACEHOLDER_Y_COORD',
            'PLACEHOLDER_X_COORD')
    }
    _placeholder_class_dict = {
        'PLACEHOLDER_X_COORD': data_model.DMPlaceholderXCoordinate,
        'PLACEHOLDER_Y_COORD': data_model.DMPlaceholderYCoordinate,
        'PLACEHOLDER_Z_COORD': data_model.DMPlaceholderZCoordinate,
        'PLACEHOLDER_T_COORD': data_model.DMPlaceholderTCoordinate,
        'PLACEHOLDER_COORD': data_model.DMPlaceholderCoordinate
    }

    @classmethod
    def from_struct(cls, dims_d, name, **kwargs):
        # if we only have ndim, map to axes names
        if 'dimensions' not in kwargs and 'ndim' in kwargs:
            kwargs['dimensions'] = cls._ndim_to_axes_set[kwargs.pop('ndim')]

        # map dimension names to coordinate objects
        kwargs['coords'] = []
        if 'dimensions' not in kwargs or not kwargs['dimensions']:
            raise ValueError(f"No dimensions specified for fieldlist entry {name}.")
        for d_name in kwargs.pop('dimensions'):
            if d_name in cls._placeholder_class_dict:
                coord_cls = cls._placeholder_class_dict[d_name]
                kwargs['coords'].append(coord_cls())
            elif d_name not in dims_d:
                raise ValueError((f"Unknown dimension name {d_name} in fieldlist "
                    f"entry for {name}."))
            else:
                kwargs['coords'].append(dims_d[d_name])

        for d_name in kwargs.get('scalar_coord_templates', dict()):
            if d_name not in dims_d:
                raise ValueError((f"Unknown dimension name {d_name} in scalar "
                    f"coord definition for fieldlist entry for {name}."))

        filter_kw = util.filter_dataclass(kwargs, cls, init=True)
        assert filter_kw['coords']
        return cls(name=name, **filter_kw)

    def scalar_name(self, old_coord, new_coord, log=_log):
        """Uses one of the scalar_coord_templates to construct the translated
        variable name for this variable on a scalar coordinate slice (eg.
        pressure level).
        """
        c = old_coord # abbreviate
        assert c.is_scalar
        key = new_coord.name
        if key not in self.scalar_coord_templates:
            raise ValueError((f"Don't know how to name {c.name} ({c.axis}) slice "
                              f"of {self.name}."
                              ))
        # construct convention's name for this variable on a level
        name_template = self.scalar_coord_templates[key]
        new_name = name_template.format(value=int(new_coord.value))
        if units.units_equal(c.units, new_coord.units):
            log.debug("Renaming %s %s %s slice of '%s' to '%s'.",
                c.value, c.units, c.axis, self.name, new_name)
        else:
            log.debug("Renaming %s slice of '%s' to '%s' (@ %s %s = %s %s).",
                      c.axis, self.name, new_name, c.value, c.units,
                      new_coord.value, new_coord.units
                      )
        return new_name


@util.mdtf_dataclass
class Fieldlist():
    """Class corresponding to a single variable naming convention (single file
    in data/fieldlist_*.jsonc).

    TODO: implement more robust indexing/lookup scheme. standard_name is not
    a unique identifier, but should include cell_methods, etc. as well as
    dimensionality.
    """
    name: str = util.MANDATORY
    axes: util.WormDict = dc.field(default_factory=util.WormDict)
    axes_lut: util.WormDict = dc.field(default_factory=util.WormDict)
    entries: util.WormDict = dc.field(default_factory=util.WormDict)
    lut: util.WormDict = dc.field(default_factory=util.WormDict)
    env_vars: dict = dc.field(default_factory=dict)

    @classmethod
    def from_struct(cls, d):
        def _process_coord(section_name, d, temp_d):
            # build two-stage lookup table (by axis type, then standard name)
            section_d = d.pop(section_name, dict())
            for k,v in section_d.items():
                ax = v['axis']
                entry = data_model.coordinate_from_struct(v, name=k)
                d['axes'][k] = entry
                temp_d[ax][entry.standard_name] = entry
            return (d, temp_d)

        def _process_var(section_name, d, temp_d):
            # build two-stage lookup table (by standard name, then data
            # dimensionality)
            section_d = d.pop(section_name, dict())
            for k,v in section_d.items():
                entry = FieldlistEntry.from_struct(d['axes'], name=k, **v)
                d['entries'][k] = entry
                temp_d[entry.standard_name][entry.modifier] = entry
            return (d, temp_d)

        temp_d = collections.defaultdict(util.WormDict)
        d['axes'] = util.WormDict()
        d['axes_lut'] = util.WormDict()
        d, temp_d = _process_coord('coords', d, temp_d)
        d['axes_lut'].update(temp_d)

        temp_d = collections.defaultdict(util.WormDict)
        d['entries'] = util.WormDict()
        d['lut'] = util.WormDict()
        d, temp_d = _process_var('aux_coords', d, temp_d)
        d, temp_d = _process_var('variables', d, temp_d)
        d['lut'].update(temp_d)
        return cls(**d)

    def to_CF(self, var_or_name):
        """Returns :class:`FieldlistEntry` for the variable having the given
        name in this convention.
        """
        if hasattr(var_or_name, 'name'):
            return self.entries[var_or_name.name]
        else:
            return self.entries[var_or_name]

    def to_CF_name(self, var_or_name):
        """Like :meth:`to_CF`, but only return the CF standard name, given the
        name in this convention.
        """
        return self.to_CF(var_or_name).standard_name

    def from_CF(self, var_or_name, modifier=None, num_dims=0,
                has_scalar_coords_att=False, name_only=False):
        """Look up :class:`FieldlistEntry` corresponding to the given standard
        name, optionally providing a modifier to resolve ambiguity.

        TODO: this is a hacky implementation; FieldlistEntry needs to be
        expanded with more ways to uniquely identify variable (eg cell methods).
        Args:
            var_or_name: variable or name of the variable
            modifier:optional string to distinguish a 3-D field from a 4-D field with
            the same var_or_name value
            num_dims: number of dimensions of the POD variable corresponding to var_or_name
            has_scalar_coords_att: boolean indicating that the POD variable has a scalar_coords
            attribute, and therefore requires a level from a 4-D field
            name_only: boolean indicating to not return a modifier--hacky way to accommodate
            a from_CF_name call that does not provide other metadata
        """
        if hasattr(var_or_name, 'standard_name'):
            standard_name = var_or_name.standard_name
        else:
            standard_name = var_or_name

        if standard_name not in self.lut:
            raise KeyError((f"Standard name '{standard_name}' not defined in "
                  f"convention '{self.name}'."))
        lut1 = self.lut[standard_name]  # abbreviate
        fl_entry: FieldlistEntry = None
        empty_mod_count = 0  # counter for modifier attributes that are blank strings in the fieldlist lookup table
        if not modifier:  # empty strings and None types evaluate to False
            entries = tuple(lut1.values())
            if len(entries) > 1:
                for e in entries:
                    if not e.modifier.strip():
                        empty_mod_count += 1  # fieldlist LUT entry has no modifier attribute
                        if has_scalar_coords_att or num_dims == len(e.dims) or name_only:
                            # fieldlist lut entry has a blank modifier
                            fl_entry = e
                if empty_mod_count > 1:
                    raise ValueError((f"Variable name in convention '{self.name}' "
                                      f"not uniquely determined by standard name '{standard_name}'."))
            else:
                fl_entry = entries[0]
        else:
            if modifier not in lut1:
                raise KeyError((f"Queried standard name '{standard_name}' with an "
                                f"unexpected modifier {modifier} not in convention "
                                f"'{self.name}'."))
            fl_entry = lut1[modifier]

        if not fl_entry:
            raise ValueError("fl_entry evaluated as a None Type")
        return copy.deepcopy(fl_entry)

    def from_CF_name(self, var_or_name, modifier=None):
        """Like :meth:`from_CF`, but only return the variable's name in this
        convention.

        Args:
            var_or_name: variable or name of the variable
            modifier:optional string to distinguish a 3-D field from a 4-D field with
            the same var_or_name value
        """
        return self.from_CF(var_or_name, modifier=modifier, name_only=True).name

    def translate_coord(self, coord, log=_log):
        """Given a :class:`~data_model.DMCoordinate`, look up the corresponding
        translated :class:`~data_model.DMCoordinate` in this convention.
        """
        ax = coord.axis
        if ax not in self.axes_lut:
            raise KeyError(f"Axis {ax} not defined in convention '{self.name}'.")

        lut1 = self.axes_lut[ax] # abbreviate
        if not hasattr(coord, 'standard_name'):
            coords = tuple(lut1.values())
            if len(coords) > 1:
                raise ValueError((f"Coordinate dimension in convention '{self.name}' "
                    f"not uniquely determined by coordinate {coord.name}."))
            new_coord = coords[0]
        else:
            if coord.standard_name not in lut1:
                raise KeyError((f"Coordinate {coord.name} with standard name "
                    f"'{coord.standard_name}' not defined in convention '{self.name}'."))
            new_coord = lut1[coord.standard_name]

        if hasattr(coord, 'is_scalar') and coord.is_scalar:
            new_coord = copy.deepcopy(new_coord)
            new_coord.value = units.convert_scalar_coord(coord, new_coord.units,
                log=log)
        else:
            new_coord = dc.replace(coord,
                **(util.filter_dataclass(new_coord, coord)))
        return new_coord

    def translate(self, var):
        """Returns :class:`TranslatedVarlistEntry` instance, with populated
        coordinate axes. Units of scalar coord slices are translated to the units
        of the conventions' coordinates. Includes logic to translate and rename
        scalar coords/slices, e.g. :class:`~diagnostic.VarlistEntry` for 'ua'
        (intrinsically 4D) @ 500mb could produce a :class:`TranslatedVarlistEntry`
        for 'u500' (3D slice), depending on naming convention.
        """
        if var.use_exact_name:
            # HACK; dataclass.asdict says VarlistEntry has no _id attribute & not sure why
            fl_entry = {f.name: getattr(var, f.name, util.NOTSET)
                        for f in dc.fields(TranslatedVarlistEntry) if hasattr(var, f.name)}
            new_name = var.name
        else:
            has_scalar_coords = bool(var.scalar_coords)

            fl_entry = self.from_CF(var.standard_name, var.modifier, var.dims.__len__(), has_scalar_coords)
            new_name = fl_entry.name

        new_dims = [self.translate_coord(dim, log=var.log) for dim in var.dims]
        new_scalars = [self.translate_coord(dim, log=var.log) for dim in var.scalar_coords]
        if len(new_scalars) > 1:
            raise NotImplementedError()
        elif len(new_scalars) == 1:
            assert not var.use_exact_name
            # change translated name to request the slice instead of the full var
            # keep the scalar_coordinate value attribute on the translated var
            new_name = fl_entry.scalar_name(
                var.scalar_coords[0], new_scalars[0], log=var.log
            )

        return util.coerce_to_dataclass(
            fl_entry, TranslatedVarlistEntry,
            name=new_name, coords=(new_dims + new_scalars),
            convention=self.name, log=var.log
        )


class NoTranslationFieldlist(util.Singleton):
    """Class which partially implements the :class:`Fieldlist` interface but
    does no variable translation. :class:`~diagnostic.VarlistEntry` objects from
    the POD are passed through to create :class:`TranslatedVarlistEntry` objects.
    """
    def __init__(self):
        # only a Singleton to ensure that we only log this message once
        _log.info('Variable name translation disabled.')

    def to_CF(self, var_or_name):
        # should never get here - not called externally
        raise NotImplementedError

    def to_CF_name(self, var_or_name):
        if hasattr(var_or_name, 'name'):
            return var_or_name.name
        else:
            return var_or_name

    def from_CF(self, var_or_name, modifier=None):
        # should never get here - not called externally
        raise NotImplementedError

    def from_CF_name(self, var_or_name, modifier=None):
        if hasattr(var_or_name, 'name'):
            return var_or_name.name
        else:
            return var_or_name

    def translate_coord(self, coord, log=_log):
        # should never get here - not called externally
        raise NotImplementedError

    def translate(self, var):
        """Returns :class:`TranslatedVarlistEntry` instance, populated with
        contents of input :class:`~diagnostic.VarlistEntry` instance.

        .. note::
           We return a copy of the :class:`~diagnostic.VarlistEntry` because
           logic in :class:`~xr_parser.DefaultDatasetParser` alters the translation
           based on the file's actual contents.
        """
        coords_copy = copy.deepcopy(var.dims) + copy.deepcopy(var.scalar_coords)
        # TODO: coerce_to_dataclass runs into recursion limit on var; fix that
        return TranslatedVarlistEntry(
            name=var.name,
            standard_name=var.standard_name,
            units=var.units,
            convention=_NO_TRANSLATION_CONVENTION,
            coords=coords_copy,
            modifier=var.modifier,
            log=var.log
        )


class VariableTranslator(util.Singleton):
    """:class:`~util.Singleton` containing information for different variable
    naming conventions. These are defined in the ``data/fieldlist_*.jsonc``
    files.
    """
    def __init__(self, code_root=None, unittest=False):
        self._unittest = unittest
        self.conventions = util.WormDict()
        self.aliases = util.WormDict()
        self.modifier = util.read_json(os.path.join(code_root, 'data', 'modifiers.jsonc'), log=_log)

    def add_convention(self, d):
        conv_name = d['name']
        _log.debug("Adding variable name convention '%s'", conv_name)
        for model in d.pop('models', []):
            self.aliases[model] = conv_name
        self.conventions[conv_name] = Fieldlist.from_struct(d)

    def read_conventions(self,code_root, unittest=False):
        """ Read in the conventions from the Fieldlists and populate the convention attribute. """
        if unittest:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            config_files = []
        else:
            glob_pattern = os.path.join(
                code_root, 'data', 'fieldlist_*.jsonc'
            )
            config_files = glob.glob(glob_pattern)
        for f in config_files:
            try:
                d = util.read_json(f, log=_log)
                self.add_convention(d)
            except Exception as exc:
                _log.exception("Caught exception loading fieldlist file %s: %r",
                    f, exc)
                continue

    def get_convention_name(self, conv_name):
        """Resolve the naming convention associated with a given
        :class:`Fieldlist` object from among a set of possible aliases.
        """
        if conv_name in self.conventions \
            or conv_name == _NO_TRANSLATION_CONVENTION:
            return conv_name
        if conv_name in self.aliases:
            _log.debug("Using convention '%s' based on alias '%s'.",
                       self.aliases[conv_name], conv_name)
            return self.aliases[conv_name]
        _log.error("Unrecognized variable name convention '%s'.",
                   conv_name)
        raise KeyError(conv_name)

    def get_convention(self, conv_name):
        """Return the :class:`Fieldlist` object containing the variable name
        translation logic for a given convention name.
        """
        if conv_name == _NO_TRANSLATION_CONVENTION:
            # hard-coded special case: do no translation
            return NoTranslationFieldlist()
        else:
            # normal case: translate according to data source's naming convention
            conv_name = self.get_convention_name(conv_name)
            return self.conventions[conv_name]

    def _fieldlist_method(self, conv_name, method_name, *args, **kwargs):
        """Wrapper which determines the requested convention and calls the
        requested *method_name* on the :class:`Fieldlist` object for that
        convention.
        """
        meth = getattr(self.get_convention(conv_name), method_name)
        return meth(*args, **kwargs)

    def to_CF(self, conv_name, name):
        return self._fieldlist_method(conv_name, 'to_CF', name)

    def to_CF_name(self, conv_name, name):
        return self._fieldlist_method(conv_name, 'to_CF_name', name)

    def from_CF(self, conv_name, standard_name, modifier=None):
        return self._fieldlist_method(conv_name, 'from_CF',
            standard_name, modifier=modifier)

    def from_CF_name(self, conv_name, standard_name, modifier=None):
        return self._fieldlist_method(conv_name, 'from_CF_name',
                                      standard_name, modifier=modifier)

    def translate_coord(self, conv_name, coord, log=_log):
        return self._fieldlist_method(conv_name, 'translate_coord', coord, log=log)

    def translate(self, conv_name, var):
        return self._fieldlist_method(conv_name, 'translate', var)