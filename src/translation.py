"""Utilities for variable translation
"""
import os
import collections
import copy
import dataclasses as dc
import glob
import typing
import pathlib
from src import util, data_model, units
from src.units import Units

import logging

_log = logging.getLogger(__name__)

_NO_TRANSLATION_CONVENTION = 'no_translation'  # naming convention for disabling translation


@util.mdtf_dataclass
class TranslatedVarlistEntry(data_model.DMVariable):
    """Class returned by :meth:`VarlistTranslator.translate`. Marks some
    attributes inherited from :class:`~data_model.DMVariable`.
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
    long_name: str = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    units: Units = util.MANDATORY
    # dims: list           # fields inherited from data_model.DMVariable
    # modifier : str
    scalar_coords: list = \
        dc.field(init=False, default_factory=list, metadata={'query': True})
    log: typing.Any = util.MANDATORY  # assigned from parent var
    _requires_level_extraction = None

    @property
    def requires_level_extraction(self) -> bool:
        return self._requires_level_extraction

    @requires_level_extraction.setter
    def requires_level_extraction(self, value: bool):
        self._requires_level_extraction = value


@util.mdtf_dataclass
class Fieldlist:
    """Class corresponding to a single variable naming convention (single file
    in data/fieldlist_*.jsonc).

    TODO: implement more robust indexing/lookup scheme. standard_name is not
    a unique identifier, but should include cell_methods, etc. as well as
    dimensionality.
    """
    axes_standard_names: list
    lut_standard_names: list
    name: str = util.MANDATORY
    axes_lut: util.WormDict = dc.field(default_factory=util.WormDict)
    lut: util.WormDict = dc.field(default_factory=util.WormDict)
    env_vars: dict = dc.field(default_factory=dict)
    scalar_coord_templates: dict = dc.field(default_factory=dict)

    @classmethod
    def from_struct(cls, d: dict, code_root: str, log=None):
        def _process_coord(section_name: str,
                           in_dict: collections.OrderedDict,
                           root_dir: str,
                           log=None):
            # build two-stage lookup table by axis type, then name
            # The name is the key since standard_names are not necessarily unique ID's
            # and coordinates may be assigned to variables in multiple realms
            section_d = in_dict.pop(section_name, dict())
            if '$ref' in section_d.keys():
                ref_file_query = pathlib.Path(root_dir, 'data', section_d['$ref'])
                ref_file_path = str(ref_file_query)
                assert ".json" in ref_file_query.suffix, f"{ref_file_path} is not a json(c) file"
                coord_file_entries = util.read_json(ref_file_path, log=log)

                regex_dict = util.RegexDict(coord_file_entries)
                section_d.update([r for r in regex_dict.get_matching_value('axis')][0])
                section_d.pop('$ref', None)

            return section_d

        def _process_var(section_name: str, in_dict, lut_dict):
            # build two-stage lookup table (by standard name, then data
            # dimensionality)
            sct_dict = dict()
            section_d = in_dict.pop(section_name, dict())
            for k, v in section_d.items():
                lut_dict['entries'][k] = v
                # note that realm and modifier class atts are empty strings
                # by default and, therefore, so are the corresponding dictionary
                # keys. TODO: be sure to handle empty keys in PP
                if 'modifier' not in v:
                    lut_dict['entries'][k].update({'modifier': ""})
                if 'long_name' not in v:
                    lut_dict['entries'][k].update({'long_name': ""})
                if 'scalar_coord_templates' in v:
                    sct_dict.update({k: v['scalar_coord_templates']})
                if 'alternate_standard_names' not in v:
                    lut_dict['entries'][k].update({'alternate_standard_names': list()})
            return lut_dict, sct_dict

        d['axes_lut'] = util.WormDict()
        temp_d = _process_coord('coords', d, code_root, log)
        d['axes_lut'].update(temp_d)

        d['axes_standard_names'] = []
        for sn in d['axes_lut'].values():
            d['axes_standard_names'].append(sn['standard_name'])

        temp_d = collections.defaultdict(util.WormDict)
        d['lut'] = util.WormDict()
        d['scalar_coord_templates'] = util.WormDict()
        temp_d, sc_d = _process_var('variables', d, temp_d)
        d['lut'].update(temp_d['entries'])
        d['scalar_coord_templates'].update(sc_d)
        d['lut_standard_names'] = []
        for sn in d['lut'].values():
            d['lut_standard_names'].append(sn['standard_name'])
        return cls(**d)

    def to_CF(self, var_or_name) -> util.WormDict:
        """Returns FieldList lookup table entry for the variable having the given
        name in this convention.
        """
        if hasattr(var_or_name, 'name'):
            return self.lut[var_or_name.name]
        else:
            return self.lut[var_or_name]

    def to_CF_name(self, var_or_name: str):
        """Like :meth:`to_CF`, but only return the CF standard name, given the
        name in this convention.
        """
        return self.to_CF(var_or_name).standard_name

    def to_CF_standard_name(self, standard_name: str,
                            long_name: str,
                            realm: str,
                            modifier: str) -> str:

        precip_vars = ['precipitation_rate', 'precipitation_flux']
        # search the lookup table for the variable with the specified standard_name
        # realm, modifier, and long_name attributes

        for var_name, var_dict in self.lut.items():
            if var_dict['standard_name'] == standard_name \
                    and var_dict['realm'] == realm\
                    and var_dict['modifier'] == modifier:
                # if not var_dict['long_name'] or var_dict['long_name'].lower() == long_name.lower():
                return var_name
            else:
                if var_dict['standard_name'] in precip_vars and standard_name in precip_vars:
                    return var_name
                else:
                    continue

    def from_CF(self,
                standard_name: str,
                realm: str,
                modifier: str = "",
                long_name: str = "",
                num_dims: int = 0,
                has_scalar_coords_att: bool = False,
                name_only: bool = False) -> dict:
        """Look up Fieldlist lookup table entries corresponding to the given standard
        name, optionally providing a modifier to resolve ambiguity.

        TODO: expand with more ways to uniquely identify variable (eg cell methods).
        Args:
            standard_name: variable or name of the variable
            realm: str variable realm (atmos, ocean, land, seaIce, etc...)
            modifier:optional string to distinguish a 3-D field from a 4-D field with
            the same var_or_name value
            long_name: str (optional) long name attribute of the variable
            num_dims: number of dimensions of the POD variable corresponding to var_or_name
            has_scalar_coords_att: boolean indicating that the POD variable has a scalar_coords
            attribute, and therefore requires a level from a 4-D field
            name_only: boolean indicating to not return a modifier--hacky way to accommodate
            a from_CF_name call that does not provide other metadata
        """
        # self.lut corresponds to POD convention
        assert standard_name in self.lut_standard_names, f'{standard_name} not found in Fieldlist lut_standard_names'
        lut1 = dict()
        for k, v in self.lut.items():
            if v['standard_name'] == standard_name and v['realm'] == realm and v['modifier'] == modifier:
                if 'long_name' not in v or v['long_name'].strip('') == '':
                    v['long_name'] = long_name
                v['name'] = k
                lut1.update({k: v})

        entries = tuple(lut1.values())
        if len(entries) > 1:
            _log.error(f'Found multiple entries in {self.name} Fieldlist for {standard_name}')
        fl_entries = dict()
        for e in entries:
            fl_entries.update({e['name']: copy.deepcopy(e)})
        return fl_entries

    def from_CF_name(self,
                     var_or_name: str,
                     realm: str,
                     long_name: str = "",
                     modifier: str = "") -> dict:
        """Like :meth:`from_CF`, but only return the variable's name in this
        convention.

        Args:
            var_or_name: str, variable or name of the variable
            realm: str model realm of variable
            long_name: str (optional): long_name attribute of the variable
            modifier:optional string to distinguish a 3-D field from a 4-D field with
            the same var_or_name value
        """

        return self.from_CF(var_or_name,
                            modifier=modifier,
                            long_name=long_name,
                            name_only=True,
                            realm=realm)

    def get_variable_long_name(self, var, has_scalar_coords: bool) -> str:
        if not var.long_name and has_scalar_coords:
            v = var.scalar_coords[0]
            return var.standard_name.replace('_', ' ') + ' at ' + str(v.value) + ' ' + v.units
        else:
            return var.standard_name.replace('_', ' ')

    def create_scalar_name(self, old_coord, new_coord: dict, var_id: str, log=_log) -> str:
        """Uses one of the scalar_coord_templates to construct the translated
        variable name for this variable on a scalar coordinate slice (eg.
        pressure level).
        """
        c = old_coord
        assert c.is_scalar, f'{c.name} is not a scalar coordinate'
        key = ""
        if hasattr(new_coord, 'name'):
            key = new_coord.name
        elif hasattr(new_coord, 'out_name'):
            key = new_coord.out_name
        for v in self.scalar_coord_templates.values():
            if key not in v.keys():
                raise ValueError((f"Don't know how to name {c.name} ({c.axis}) slice "
                                  f"of {self.name}."
                                  ))
        # construct convention's name for this variable on a level
        name_template = self.scalar_coord_templates[var_id][key]
        if new_coord.units.strip('').lower() == 'pa':
            val = int(new_coord.value / 100)
        else:
            val = int(new_coord.value)

        new_name = name_template.format(value=val)
        if units.units_equal(c.units, new_coord.units):
            log.debug("Renaming %s %s %s slice of '%s' to '%s'.",
                      c.value, c.units, c.axis, self.name, new_name)
        else:
            log.debug("Renaming %s slice of '%s' to '%s' (@ %s %s = %s %s).",
                      c.axis, self.name, new_name, c.value, c.units,
                      new_coord.value, new_coord.units
                      )
        return new_name

    def translate_coord(self, coord, class_dict=None, log=_log) -> dict:
        """Given a :class:`~data_model.DMCoordinate`, look up the corresponding
        translated :class:`~data_model.DMCoordinate` in this convention.
        """
        ax = coord.standard_name

        if ax not in self.axes_standard_names:
            raise KeyError((f"Coordinate {coord.name} with standard name "
                            f"'{coord.standard_name}' not defined in convention '{self.name}'."))

        new_coord = dict()
        lut1 = dict()
        for k, v in self.axes_lut.items():
            if v.get('standard_name') == coord.standard_name:
                lut1.update({k: v})

        if len(lut1) > 1:
            if ax in lut1.keys():
                new_coord = lut1[ax]
            else:
                # TODO refine the following query
                # The logic below optimized for identifying the correct pressure level coordinate to select
                # from the CMIP CV by comparing the VarlistEntry scalar coord value (supplied by the POD settings file)
                # in hPa with the CV values in Pa (hPa * 100 = pa).
                # If both coordinate values are strings, then there is just a simple check to see if the varlistentry
                # value is contained by the CV string value. This is not robust, but sufficient for testing purposes

                if bool(coord.value):
                    lut_val = None
                    for k, v in lut1.items():
                        # some plev entries have a single value that might match the requested level
                        # (e.g., plev700, plev850)
                        if v.get('value', None):
                            lut_val = v.get('value')
                            if isinstance(coord.value, int) and isinstance(lut_val, str):
                                v_int = int(float(lut_val))
                                if v_int > coord.value and v_int / coord.value == 100 \
                                        or v_int < coord.value and coord.value / v_int == 100 or \
                                        v_int == coord.value:
                                    new_coord = v
                                    break
                            elif isinstance(coord.value, str) and isinstance(lut_val, str):
                                if coord.value in lut_val:
                                    new_coord = v
                                    break
                            else:
                                raise KeyError(f'coord value and/or Varlist value could not be parsed'
                                               f' by translate_coord')
                        elif v.get('requested', None):
                            # if no single-level plev coordinate matches the requested pressure level,
                            # search plev19 for the correct level, set the coordinate value to the level if found,
                            # and use the rest of the plev attributes to populate the coordinate information
                            lut_val = v.get('requested')
                            if isinstance(lut_val, list) and k == 'plev19':
                                for val in lut_val:
                                    if isinstance(coord.value, int) and isinstance(val, str):
                                        v_int = int(float(val))
                                        if v_int > coord.value and v_int / coord.value == 100 \
                                                or v_int < coord.value and coord.value / v_int == 100 or \
                                                v_int == coord.value:
                                            new_coord = v
                                            break
        else:
            new_coord = [lut1[k] for k in lut1.keys()][0]  # should return ordered dict
        if hasattr(coord, 'is_scalar') and coord.is_scalar:
            coord_name = ""
            if hasattr(new_coord, 'name'):
                coord_name = new_coord['name']
            elif hasattr(new_coord, 'out_name'):
                coord_name = new_coord['out_name']
            else: # TODO add more robust check for key name == 'plev' (or whatever the coordinate name in the lut should be based on fieldlist)
                coord_name = [k for k in lut1.keys()][0]

            coord_copy = copy.deepcopy(new_coord)
            coord_copy['value'] = units.convert_scalar_coord(coord,
                                                             coord_copy['units'],
                                                             log=log)
            try:
                new_coord = data_model.coordinate_from_struct(coord_copy,
                                                              class_dict=class_dict,
                                                              name=coord_name)
            except ValueError:
                log.error('unable to obtain new_coord from coordinate_from_struct call in translate.translate_coord')
        else:
            new_coord = dc.replace(coord,
                                   **(util.filter_dataclass(new_coord, coord)))

        return new_coord

    def translate(self, var, from_convention: str):
        """Returns :class:`TranslatedVarlistEntry` instance, with populated
        coordinate axes. Units of scalar coord slices are translated to the units
        of the conventions' coordinates. Includes logic to translate and rename
        scalar coords/slices, e.g. :class:`~varlist_util.VarlistEntry` for 'ua'
        (intrinsically 4D) @ 500mb could produce a :class:`TranslatedVarlistEntry`
        for 'u500' (3D slice), depending on naming convention.
        """
        has_scalar_coords = bool(var.scalar_coords)
        if var.use_exact_name:
            # HACK; dataclass.asdict says VarlistEntry has no _id attribute & not sure why
            fl_entry = {f.name: getattr(var, f.name, util.NOTSET)
                        for f in dc.fields(TranslatedVarlistEntry) if hasattr(var, f.name)}
            new_name = var.name
        else:
            # Fieldlist for POD convention
            from_convention_tl = VariableTranslator().get_convention(from_convention)
            # Fieldlist entry for POD variable
            long_name = self.get_variable_long_name(var, has_scalar_coords)
            fl_entries = from_convention_tl.from_CF(var.standard_name,
                                                    var.realm,
                                                    var.modifier,
                                                    long_name,
                                                    var.dims.__len__(),
                                                    has_scalar_coords
                                                    )

            # Use the POD variable standard name, realm, and modifier to get the corresponding
            # information from FieldList for the DataSource convention
            # Modifiers that are not defined are set to empty strings when variable and fieldlist
            # objects are initialized
            fl_atts = [v for v in fl_entries.values()][0]
            new_name = self.to_CF_standard_name(fl_atts['standard_name'],
                                                fl_atts['long_name'],
                                                fl_atts['realm'],
                                                fl_atts['modifier'])
        # build reference dictionary of axes classes so that any scalar_coords are cast to
        # corresponding Varlist[]Coordinate classes
        class_dict = None
        if has_scalar_coords:
            class_dict = dict()
            for k, v in var.axes.items():
                class_dict.update({k: v.__class__})

        new_dims = [self.translate_coord(dim, log=var.log) for dim in var.dims]
        new_scalars = [self.translate_coord(dim, class_dict=class_dict, log=var.log) for dim in var.scalar_coords]
        new_atts = self.lut[new_name]
        if len(new_scalars) > 1:
            raise NotImplementedError()
        elif len(new_scalars) == 1:
            assert not var.use_exact_name, "assertion error: var.use_exact_name set to true for " + var.full_name
            # change translated name to request the slice instead of the full var
            # keep the scalar_coordinate value attribute on the translated var
            new_scalar_name = self.create_scalar_name(
                var.scalar_coords[0], new_scalars[0],
                new_name, log=var.log)

            new_name = new_scalar_name
            if new_name in self.lut:
                new_atts = self.lut[new_name]
            # append an is_scalar attribute for the coordinate check in
            # data_model._DMDimensionsMixin.__post_init__() call from
            # TranslatedVarlistEntry
            for s in new_scalars:
                if not s.is_scalar:
                    s.is_scalar = True

        return util.coerce_to_dataclass(
            new_atts, TranslatedVarlistEntry,
            name=new_name,
            coords=(new_dims + new_scalars),
            convention=self.name, log=var.log
        )


class NoTranslationFieldlist:
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

    def from_CF(self,
                var_or_name: str,
                realm: str,
                modifier=None,
                long_name=None,
                num_dims: int = 0,
                has_scalar_coords_att: bool = False,
                name_only: bool = False):
        # should never get here - not called externally
        raise NotImplementedError

    def from_CF_name(self, var_or_name):
        if hasattr(var_or_name, 'name'):
            return var_or_name.name
        else:
            return var_or_name

    def translate_coord(self, coord, log=_log) -> TranslatedVarlistEntry:
        # should never get here - not called externally
        raise NotImplementedError

    def translate(self, var, data_convention: str):
        """Returns :class:`TranslatedVarlistEntry` instance, populated with
        contents of input :class:`~diagnostic.VarlistEntry` instance.

         note::
           We return a copy of the :class:`~diagnostic.VarlistEntry` because
           logic in :class:`~xr_parser.DefaultDatasetParser` alters the translation
           based on the file's actual contents.
        """
        coords_copy = copy.deepcopy(var.dims) + copy.deepcopy(var.scalar_coords)
        fieldlist_obj = VariableTranslator().get_convention(data_convention)
        fieldlist_entry = dict()
        var_id = ""
        for variable_id, variable_id_dict in fieldlist_obj.lut.items():
            if variable_id_dict.get('standard_name', None) == var.standard_name \
                or var.standard_name in variable_id_dict.get('alternate_standard_names'):
                    if variable_id_dict.get('realm', None) == var.realm \
                        and variable_id_dict.get('units', None) == var.units.units:
                            fieldlist_entry = variable_id_dict
                            var_id = variable_id
                    break
        if len(fieldlist_entry.keys()) < 1:
            var.log.error(f'No {data_convention} fieldlist entry found for variable {var.name}')
            return None
        alt_standard_names = fieldlist_entry.get('alternate_standard_names')
        return TranslatedVarlistEntry(
            name=var_id,
            standard_name=var.standard_name,
            units=var.units,
            convention=var.convention,
            coords=coords_copy,
            modifier=var.modifier,
            alternate_standard_names=alt_standard_names,
            realm=var.realm,
            log=var.log
        )


class VariableTranslator(metaclass=util.Singleton):
    """The use of class:`~util.Singleton` means that the VariableTranslator is not a
    base class. Instead, it is a metaclass that needs to be created only once (done
    in the mdtf_framework.py driver script to hold all the information from the fieldlist
    tables that are later shared. Instead, the SUBCLASSES of the VariableTranslator are customized information for different variable
    naming conventions. These are defined in the ``data/fieldlist_*.jsonc``
    files.
    """

    conventions: util.WormDict
    aliases: util.WormDict
    _unittest: bool = False

    def __init__(self, code_root=None, unittest=False):
        self._unittest = unittest
        self.conventions = util.WormDict()
        self.aliases = util.WormDict()
        self.modifier = util.read_json(os.path.join(code_root, 'data', 'modifiers.jsonc'), log=_log)

    def add_convention(self, d: dict, file_path: str, log=None):
        conv_name = d['name'].lower()
        _log.debug("Adding variable name convention '%s'", conv_name)
        for model in d.pop('models', []):
            self.aliases[model] = conv_name
        self.conventions[conv_name] = Fieldlist.from_struct(d, file_path, log=log)

    def read_conventions(self, code_root: str, unittest=False):
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
                self.add_convention(d, code_root, log=_log)
            except Exception as exc:
                _log.exception("Caught exception loading fieldlist file %s: %r",
                               f, exc)
                continue

    def get_convention_name(self, conv_name: str):
        """Resolve the naming convention associated with a given
        :class:`Fieldlist` object from among a set of possible aliases.
        """
        if conv_name in self.conventions \
                or conv_name == _NO_TRANSLATION_CONVENTION:
            return conv_name
        if conv_name.upper() in self.aliases:
            _log.debug("Using convention '%s' based on alias '%s'.",
                       self.aliases[conv_name], conv_name)
            return self.aliases[conv_name]
        _log.error("Unrecognized variable name convention '%s'.",
                   conv_name)
        raise KeyError(conv_name)

    def get_convention(self, conv_name: str):
        """Return the :class:`Fieldlist` object containing the variable name
        translation logic for a given convention name.
        """
        if conv_name == _NO_TRANSLATION_CONVENTION:
            # hard-coded special case: do no translation
            return NoTranslationFieldlist()
        else:
            # normal case: translate according to data source's naming convention
            conv_name = self.get_convention_name(conv_name.lower())
            return self.conventions[conv_name]

    def _fieldlist_method(self, conv_name: str, method_name: str, *args, **kwargs):
        """Wrapper which determines the requested convention and calls the
        requested *method_name* on the :class:`Fieldlist` object for that
        convention.
        """
        meth = getattr(self.get_convention(conv_name), method_name)
        return meth(*args, **kwargs)

    def to_CF(self, conv_name: str, name: str):
        return self._fieldlist_method(conv_name, 'to_CF', name)

    def to_CF_name(self, conv_name: str, name: str):
        return self._fieldlist_method(conv_name, 'to_CF_name', name)

    def from_CF(self,
                conv_name: str,
                standard_name: str,
                realm: str = "",
                modifier: str = "",
                long_name: str = "",
                num_dims: int = 0,
                has_scalar_coords_att: bool = False,
                name_only: bool = False):

        return self._fieldlist_method(conv_name, 'from_CF',
                                      standard_name,
                                      realm,
                                      long_name,
                                      num_dims,
                                      has_scalar_coords_att,
                                      name_only,
                                      modifier=modifier)

    def from_CF_name(self, conv_name: str, standard_name: str, realm: str, modifier=None):
        return self._fieldlist_method(conv_name, 'from_CF_name',
                                      standard_name, realm, modifier=modifier)

    def to_CF_standard_name(self, conv_name: str, standard_name: str, realm: str, modifier=None):
        return self._fieldlist_method(conv_name, 'to_CF_standard_name',
                                      standard_name, realm, modifier=modifier)

    def translate_coord(self, conv_name: str, coord, log=_log):
        return self._fieldlist_method(conv_name, 'translate_coord', coord, log=log)

    def translate(self, var, to_convention: str, from_convention: str):
        return self._fieldlist_method(to_convention, 'translate', var, from_convention)
