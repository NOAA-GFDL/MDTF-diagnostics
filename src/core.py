"""Common functions and classes used in multiple places in the MDTF code.
"""
import os
import sys
import abc
import collections
import copy
import dataclasses as dc
import glob
import shutil
import signal
import tempfile
import traceback
import typing
from src import util, cli, mdtf_info, data_model, units
from src.units import Units

import logging
_log = logging.getLogger(__name__)

ObjectStatus = util.MDTFEnum(
    'ObjectStatus',
    'NOTSET ACTIVE INACTIVE FAILED SUCCEEDED',
    module=__name__
)
ObjectStatus.__doc__ = """
:class:`util.MDTFEnum` used to track the status of a :class:`MDTFObjectBase`:

- *NOTSET*: the object hasn't been fully initialized.
- *ACTIVE*: the object is currently being processed by the framework.
- *INACTIVE*: the object has been initialized, but isn't being processed (e.g.,
    alternate :class:`~diagnostic.VarlistEntry`\s).
- *FAILED*: processing of the object has encountered an error, and no further
    work will be done.
"""

@util.mdtf_dataclass
class MDTFObjectBase(metaclass=util.MDTFABCMeta):
    """Base class providing shared functionality for the "object hierarchy":

    - :class:`~data_manager.DataSourceBase`\s belonging to a run of the package
        (:class:`MDTFFramework`);
    - :class:`~diagnostic.Diagnostic`\s (PODs) belonging to a
        :class:`~data_manager.DataSourceBase`;
    - :class:`~diagnostic.VarlistEntry`\s (requested model variables) belonging
        to a :class:`~diagnostic.Diagnostic`.
    """
    _id: util.MDTF_ID = None
    name: str = util.MANDATORY
    _parent: typing.Any = dc.field(default=util.MANDATORY, compare=False)
    status: ObjectStatus = dc.field(default=ObjectStatus.NOTSET, compare=False)

    def __post_init__(self):
        if self._id is None:
            # assign unique ID # so that we don't need to rely on names being unique
            self._id = util.MDTF_ID()
        # init object-level logger
        self.log = util.MDTFObjectLogger.get_logger(self._log_name)

    @property
    def _log_name(self):
        if self._parent is None:
            return util.OBJ_LOG_ROOT # framework: root of tree
        else:
            _log_name = f"{self.name}_{self._id}".replace('.', '_')
            return f"{self._parent._log_name}.{_log_name}"

    @property
    def full_name(self):
        return f"<#{self._id}:{self._parent.name}.{self.name}>"

    def __hash__(self):
        return self._id.__hash__()

    @property
    def failed(self):
        return (self.status == ObjectStatus.FAILED) # abbreviate

    @property
    def active(self):
        return (self.status == ObjectStatus.ACTIVE) # abbreviate

    @property
    @abc.abstractmethod
    def _children(self):
        """Iterable of child objects associated with this object."""
        pass

    def iter_children(self, child_type=None, status=None, status_neq=None):
        """Generator iterating over child objects associated with this object.

        Args:
            status: None or :class:`ObjectStatus`, default None. If None,
                iterates over all child objects, regardless of status. If a
                :class:`ObjectStatus` value is passed, only iterates over
                child objects with that status.
            status_neq: None or :class:`ObjectStatus`, default None. If set,
                iterates over child objects which *don't* have the given status.
                If *status* is set, this setting is ignored.
        """
        iter_ = self._children
        if child_type is not None:
            iter_ = filter((lambda x: isinstance(x, child_type)), iter_)
        if status is not None:
            iter_ = filter((lambda x: x.status == status), iter_)
        elif status_neq is not None:
            iter_ = filter((lambda x: x.status != status_neq), iter_)
        yield from iter_

    def child_deactivation_handler(self, child, exc):
        # needs to test for child_type
        pass

    def child_status_update(self, exc=None):
        if next(self.iter_children(), None) is None:
            # should never get here (no children of any status), because this
            # method should only be called by children
            raise ValueError(f"Children misconfigured for {self.full_name}.")

        # if all children have failed, deactivate self
        if not self.failed and \
            next(self.iter_children(status_neq=ObjectStatus.FAILED), None) is None:
            self.deactivate(util.ChildFailureEvent(self), level=None)

    # level at which to log deactivation events
    _deactivation_log_level = logging.ERROR

    def deactivate(self, exc, level=None):
        # always log exceptions, even if we've already failed
        self.log.store_exception(exc)

        if not (self.failed or self.status == ObjectStatus.SUCCEEDED):
            # only need to log and update on status change for still-active objs
            if level is None:
                level = self._deactivation_log_level # default level for child class
            self.log.log(level, "Deactivated %s due to %r.", self.full_name, exc)

            # update status on self
            self.status = ObjectStatus.FAILED
            if self._parent is not None:
                # call handler on parent, which may change parent and/or siblings
                self._parent.child_deactivation_handler(self, exc)
                self._parent.child_status_update()
            # update children (deactivate all)
            for obj in self.iter_children(status_neq=ObjectStatus.FAILED):
                obj.deactivate(util.PropagatedEvent(exc=exc, parent=self), level=None)

# -----------------------------------------------------------------------------

ConfigTuple = collections.namedtuple(
    'ConfigTuple', 'name backup_filename contents'
)
ConfigTuple.__doc__ = """
    Class wrapping general structs used for configuration
"""

class ConfigManager(util.Singleton, util.NameSpace):
    def __init__(self, cli_obj=None, pod_info_tuple=None, global_env_vars=None,
        case_d=None, log_config=None, unittest=False):
        self._unittest = unittest
        self._configs = dict()
        if self._unittest:
            self.pod_data = dict()
        else:
            # normal code path
            self.pod_data = pod_info_tuple.pod_data
            self.update(cli_obj.config)
            backup_config = self.backup_config(cli_obj, case_d)
            self._configs[backup_config.name] = backup_config
            self._configs['log_config'] = ConfigTuple(
                name='log_config',
                backup_filename=None,
                contents=log_config
            )
        if global_env_vars is None:
            self.global_env_vars = dict()
        else:
            self.global_env_vars = global_env_vars

    def backup_config(self, cli_obj, case_d):
        """Copy serializable version of parsed settings, in order to write
        backup config file.
        """
        d = copy.deepcopy(cli_obj.config)
        d = {k:v for k,v in d.items() if not k.endswith('_is_default_')}
        d['case_list'] = copy.deepcopy(case_d)
        return ConfigTuple(
            name='backup_config',
            backup_filename='config_save.json',
            contents=d
        )

class PathManager(util.Singleton, util.NameSpace):
    """:class:`~util.Singleton` holding the root directories for all paths used
    by the code.
    """
    def __init__(self, cli_obj=None, env_vars=None, unittest=False):
        self._unittest = unittest
        if self._unittest:
            for path in ['CODE_ROOT', 'OBS_DATA_ROOT', 'MODEL_DATA_ROOT',
                'WORKING_DIR', 'OUTPUT_DIR']:
                setattr(self, path, 'TEST_'+path)
            self.TEMP_DIR_ROOT = self.WORKING_DIR
        else:
            # normal code path
            self.CODE_ROOT = cli_obj.code_root
            assert os.path.isdir(self.CODE_ROOT)

            d = cli_obj.config
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            # set following explictly: redundant, but keeps linter from complaining
            self.OBS_DATA_ROOT = self._init_path('OBS_DATA_ROOT', d, env=env)
            self.MODEL_DATA_ROOT = self._init_path('MODEL_DATA_ROOT', d, env=env)
            self.WORKING_DIR = self._init_path('WORKING_DIR', d, env=env)
            self.OUTPUT_DIR = self._init_path('OUTPUT_DIR', d, env=env)

            if not self.OUTPUT_DIR:
                self.OUTPUT_DIR = self.WORKING_DIR

            # set as attribute any CLI setting that has "action": "PathAction"
            # in its definition in the .jsonc file
            cli_paths = [act.dest for act in cli_obj.iter_actions() \
                if isinstance(act, cli.PathAction)]
            if not cli_paths:
                _log.warning("Didn't get list of paths from CLI.")
            for key in cli_paths:
                self[key] = self._init_path(key, d, env=env)
                if key in d:
                    d[key] = self[key]

            # set root directory for TempDirManager
            if not getattr(self, 'TEMP_DIR_ROOT', ''):
                if 'MDTF_TMPDIR' in env:
                    self.TEMP_DIR_ROOT = env['MDTF_TMPDIR']
                else:
                    # default to writing temp files in working directory
                    self.TEMP_DIR_ROOT = self.WORKING_DIR

    def _init_path(self, key, d, env=None):
        if self._unittest: # use in unit testing only
            return 'TEST_'+key
        else:
            # need to check existence in case we're being called directly
            if not d.get(key, False):
                _log.fatal(f"Error: {key} not initialized.")
                util.exit_handler(code=1)
            return util.resolve_path(
                util.from_iter(d[key]), root_path=self.CODE_ROOT, env=env,
                log=_log
            )

    def model_paths(self, case, overwrite=False):
        d = util.NameSpace()
        if isinstance(case, dict):
            name = case['CASENAME']
            yr1 = case['FIRSTYR']
            yr2 = case['LASTYR']
        else:
            name = case.name
            yr1 = case.attrs.date_range.start.format(precision=1)
            yr2 = case.attrs.date_range.end.format(precision=1)
        case_wk_dir = 'MDTF_{}_{}_{}'.format(name, yr1, yr2)
        d.MODEL_DATA_DIR = os.path.join(self.MODEL_DATA_ROOT, name)
        d.MODEL_WK_DIR = os.path.join(self.WORKING_DIR, case_wk_dir)
        d.MODEL_OUT_DIR = os.path.join(self.OUTPUT_DIR, case_wk_dir)
        if not overwrite:
            # bump both WK_DIR and OUT_DIR to same version because name of
            # former may be preserved when we copy to latter, depending on
            # copy method
            d.MODEL_WK_DIR, ver = util.bump_version(
                d.MODEL_WK_DIR, extra_dirs=[self.OUTPUT_DIR])
            d.MODEL_OUT_DIR, _ = util.bump_version(d.MODEL_OUT_DIR, new_v=ver)
        return d

    def pod_paths(self, pod, case):
        d = util.NameSpace()
        d.POD_CODE_DIR = os.path.join(self.CODE_ROOT, 'diagnostics', pod.name)
        d.POD_OBS_DATA = os.path.join(self.OBS_DATA_ROOT, pod.name)
        d.POD_WK_DIR = os.path.join(case.MODEL_WK_DIR, pod.name)
        d.POD_OUT_DIR = os.path.join(case.MODEL_OUT_DIR, pod.name)
        return d


class TempDirManager(util.Singleton):
    _prefix = 'MDTF_temp_'

    def __init__(self, temp_root=None, unittest=False):
        self._unittest = unittest
        if not temp_root:
            temp_root = tempfile.gettempdir()
        if not self._unittest:
            assert os.path.isdir(temp_root)
        self._root = temp_root
        self._dirs = []

        # delete temp files if we're killed
        signal.signal(signal.SIGTERM, self.tempdir_cleanup_handler)
        signal.signal(signal.SIGINT, self.tempdir_cleanup_handler)

    def make_tempdir(self, hash_obj=None):
        if hash_obj is None:
            new_dir = tempfile.mkdtemp(prefix=self._prefix, dir=self._root)
        elif isinstance(hash_obj, str):
            new_dir = os.path.join(self._root, self._prefix+hash_obj)
        else:
            # nicer-looking hash representation
            hash_ = hex(hash(hash_obj))[2:]
            assert isinstance(hash_, str)
            new_dir = os.path.join(self._root, self._prefix+hash_)
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)
        assert new_dir not in self._dirs
        self._dirs.append(new_dir)
        return new_dir

    def rm_tempdir(self, path):
        assert path in self._dirs
        self._dirs.remove(path)
        _log.debug("Cleaning up temp dir %s", path)
        shutil.rmtree(path)

    def cleanup(self):
        config = ConfigManager()
        if not config.get('keep_temp', False):
            for d in self._dirs:
                self.rm_tempdir(d)

    def tempdir_cleanup_handler(self, signum=None, frame=None):
        # delete temp files
        util.signal_logger(self.__class__.__name__, signum, frame, log=_log)
        self.cleanup()

# --------------------------------------------------------------------

_NO_TRANSLATION_CONVENTION = 'None' # naming convention for disabling translation

@util.mdtf_dataclass
class TranslatedVarlistEntry(data_model.DMVariable):
    """Class returned by :meth:`VarlistTranslator.translate`. Marks some
    attributes inherited from :class:`~data_model.DMVariable` as being queryable
    in :meth:`data_manager.DataframeQueryDataSourceBase.query_dataset`.
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
    # dims: list           # field inherited from data_model.DMVariable
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
            log.debug(("Renaming %s slice of '%s' to '%s' (@ %s %s = %s %s)."),
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
            # dimensionality) -- should just make FieldlistEntry hashable
            section_d = d.pop(section_name, dict())
            for k,v in section_d.items():
                entry = FieldlistEntry.from_struct(d['axes'], name=k, **v)
                d['entries'][k] = entry
                temp_d[entry.standard_name][entry.dim_axes_set] = entry
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

    def from_CF(self, var_or_name, axes_set=None):
        """Look up :class:`FieldlistEntry` corresponding to the given standard
        name, optionally providing an axes_set to resolve ambiguity.

        TODO: this is a hacky implementation; FieldlistEntry needs to be
        expanded with more ways to uniquely identify variable (eg cell methods).
        """
        if hasattr(var_or_name, 'standard_name'):
            standard_name = var_or_name.standard_name
        else:
            standard_name = var_or_name

        if standard_name not in self.lut:
            raise KeyError((f"Standard name '{standard_name}' not defined in "
                f"convention '{self.name}'."))

        lut1 = self.lut[standard_name] # abbreviate
        if axes_set is None:
            entries = tuple(lut1.values())
            if len(entries) > 1:
                raise ValueError((f"Variable name in convention '{self.name}' "
                    f"not uniquely determined by standard name '{standard_name}'."))
            fl_entry = entries[0]
        else:
            axes_set = frozenset(axes_set)
            if axes_set not in lut1:
                raise KeyError((f"Queried standard name '{standard_name}' with an "
                    f"unexpected set of axes {axes_set} not in convention "
                    f"'{self.name}'."))
            fl_entry = lut1[axes_set]

        return copy.deepcopy(fl_entry)

    def from_CF_name(self, var_or_name, axes_set=None):
        """Like :meth:`from_CF`, but only return the variable's name in this
        convention.
        """
        return self.from_CF(var_or_name, axes_set=axes_set).name

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
            fl_entry = {f.name: getattr(var, f.name, util.NOTSET) \
                for f in dc.fields(TranslatedVarlistEntry) if hasattr(var, f.name)}
            new_name = var.name
        else:
            fl_entry = self.from_CF(var.standard_name, var.axes_set)
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

    def from_CF(self, var_or_name, axes_set=None):
        # should never get here - not called externally
        raise NotImplementedError

    def from_CF_name(self, var_or_name, axes_set=None):
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

    def add_convention(self, d):
        conv_name = d['name']
        _log.debug("Adding variable name convention '%s'", conv_name)
        for model in d.pop('models', []):
            self.aliases[model] = conv_name
        self.conventions[conv_name] = Fieldlist.from_struct(d)

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

    def from_CF(self, conv_name, standard_name, axes_set=None):
        return self._fieldlist_method(conv_name, 'from_CF',
            standard_name, axes_set=axes_set)

    def from_CF_name(self, conv_name, standard_name, axes_set=None):
        return self._fieldlist_method(conv_name, 'from_CF_name',
            standard_name, axes_set=axes_set)

    def translate_coord(self, conv_name, coord, log=_log):
        return self._fieldlist_method(conv_name, 'translate_coord', coord, log=log)

    def translate(self, conv_name, var):
        return self._fieldlist_method(conv_name, 'translate', var)

# ---------------------------------------------------------------------------

class MDTFFramework(MDTFObjectBase):
    def __init__(self, cli_obj):
        super(MDTFFramework, self).__init__(
            name=self.__class__.__name__,
            _parent=None,
            status=ObjectStatus.ACTIVE
        )
        self.code_root = cli_obj.code_root
        self.pod_list = []
        self.cases = dict()
        self.global_env_vars = dict()
        try:
            # load pod data
            pod_info_tuple = mdtf_info.load_pod_settings(self.code_root)
            # load log config
            log_config = cli.read_config_file(
                self.code_root, "logging.jsonc", site=cli_obj.site
            )
            self.configure(cli_obj, pod_info_tuple, log_config)
        except Exception as exc:
            tb_exc = traceback.TracebackException(*(sys.exc_info()))
            _log.critical("Framework caught exception %r", exc)
            print(''.join(tb_exc.format()))
            util.exit_handler(code=1)

    @property
    def _children(self):
        """Iterable of child objects associated with this object."""
        return self.cases.values()

    @property
    def full_name(self):
        return self.name

    def configure(self, cli_obj, pod_info_tuple, log_config):
        """Wrapper for all configuration done based on CLI arguments.
        """
        self._cli_post_parse_hook(cli_obj)
        self.dispatch_classes(cli_obj)
        self.parse_mdtf_args(cli_obj, pod_info_tuple)
        # init singletons
        config = ConfigManager(cli_obj, pod_info_tuple,
            self.global_env_vars, self.cases, log_config)
        paths = PathManager(cli_obj)
        self.verify_paths(config, paths)
        _ = TempDirManager(paths.TEMP_DIR_ROOT, self.global_env_vars)
        _ = VariableTranslator(self.code_root)

        # config should be read-only from here on
        self._post_parse_hook(cli_obj, config, paths)
        self._print_config(cli_obj, config, paths)

    def _cli_post_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler after parsing
        # although most of the work done by parse_mdtf_args
        pass

    def dispatch_classes(self, cli_obj):
        def _dispatch(setting):
            return cli_obj.imports[setting]

        self.DataSource = _dispatch('data_manager')
        self.EnvironmentManager = _dispatch('environment_manager')
        self.RuntimeManager = _dispatch('runtime_manager')
        self.OutputManager = _dispatch('output_manager')

    @staticmethod
    def _populate_from_cli(cli_obj, group_nm, target_d=None):
        if target_d is None:
            target_d = dict()
        for arg in cli_obj.iter_group_actions(subcommand=None, group=group_nm):
            key = arg.dest
            val = cli_obj.config.get(key, None)
            if val: # assign nonempty items only
                target_d[key] = val
        return target_d

    def parse_mdtf_args(self, cli_obj, pod_info_tuple):
        """Parse script options returned by the CLI. For greater customizability,
        most of the functionality is spun out into sub-methods.
        """
        self.parse_flags(cli_obj)
        self.parse_env_vars(cli_obj)
        pod_list = cli_obj.config.pop('pods', [])
        self.pod_list = self.parse_pod_list(pod_list, pod_info_tuple)
        self.parse_case_list(cli_obj, pod_info_tuple)

    def parse_flags(self, cli_obj):
        if cli_obj.config.get('dry_run', False):
            cli_obj.config['test_mode'] = True

        if cli_obj.config.get('disable_preprocessor', False):
            _log.warning(("User disabled metadata checks and unit conversion in "
                "preprocessor."), tags=util.ObjectLogTag.BANNER)
        if cli_obj.config.get('overwrite_file_metadata', False):
            _log.warning(("User chose to overwrite input file metadata with "
                "framework values (convention = '%s')."),
                cli_obj.config.get('convention', ''),
                tags=util.ObjectLogTag.BANNER
            )
        # check this here, otherwise error raised about missing caselist is not informative
        try:
            if cli_obj.config.get('CASE_ROOT_DIR', ''):
                util.check_dir(cli_obj.config['CASE_ROOT_DIR'], 'CASE_ROOT_DIR',
                    create=False)
        except Exception as exc:
            _log.fatal((f"Mis-specified input for CASE_ROOT_DIR (received "
                f"'{cli_obj.config.get('CASE_ROOT_DIR', '')}', caught {repr(exc)}.)"))
            util.exit_handler(code=1)

    def parse_env_vars(self, cli_obj):
        # don't think PODs use global env vars?
        # self.env_vars = self._populate_from_cli(cli_obj, 'PATHS', self.env_vars)
        self.global_env_vars['RGB'] = os.path.join(self.code_root,'shared','rgb')
        # globally enforce non-interactive matplotlib backend
        # see https://matplotlib.org/3.2.2/tutorials/introductory/usage.html#what-is-a-backend
        self.global_env_vars['MPLBACKEND'] = "Agg"

    def parse_pod_list(self, pod_list, pod_info_tuple):
        pod_data = pod_info_tuple.pod_data # pod names -> contents of settings file
        args = util.to_iter(pod_list, set)
        bad_args = []
        pods = []
        for arg in args:
            if arg == 'all':
                # add all PODs except example PODs
                pods.extend([p for p in pod_data if not p.startswith('example')])
            elif arg == 'example' or arg == 'examples':
                # add example PODs
                pods.extend([p for p in pod_data if p.startswith('example')])
            elif arg in pod_info_tuple.realm_data:
                # realm_data: realm name -> list of POD names
                # add all PODs for this realm
                pods.extend(pod_info_tuple.realm_data[arg])
            elif arg in pod_data:
                # add POD by name
                pods.append(arg)
            else:
                # unrecognized argument
                _log.error("POD identifier '%s' not recognized.", arg)
                bad_args.append(arg)

        if bad_args:
            valid_args = ['all', 'examples'] \
                + pod_info_tuple.sorted_realms \
                + pod_info_tuple.sorted_pods
            _log.critical(("The following POD identifiers were not recognized: "
                "[%s].\nRecognized identifiers are: [%s].\n(Received --pods = %s)."),
                ', '.join(f"'{p}'" for p in bad_args),
                ', '.join(f"'{p}'" for p in valid_args),
                str(list(args))
            )
            util.exit_handler(code=1)

        pods = list(set(pods)) # delete duplicates
        if not pods:
            _log.critical(("ERROR: no PODs selected to be run. Do `./mdtf info pods`"
                " for a list of available PODs, and check your -p/--pods argument."
                f"\nReceived --pods = {str(list(args))}"))
            util.exit_handler(code=1)
        return pods

    def set_case_pod_list(self, case, cli_obj, pod_info_tuple):
        # if pods set from CLI, overwrite pods in case list
        # already finalized self.pod-list by the time we get here
        if not cli_obj.is_default['pods'] or not case.get('pod_list', None):
            return self.pod_list
        else:
            return self.parse_pod_list(case['pod_list'], pod_info_tuple)

    def parse_case(self, n, d, cli_obj, pod_info_tuple):
        # really need to move this into init of DataManager
        if 'CASE_ROOT_DIR' not in d and 'root_dir' in d:
            d['CASE_ROOT_DIR'] = d.pop('root_dir')
        case_convention = d.get('convention', '')
        if case_convention:
            d['convention'] = case_convention

        if not ('CASENAME' in d or ('model' in d and 'experiment' in d)):
            _log.warning(("Need to specify either CASENAME or model/experiment "
                "in caselist entry #%d, skipping."), n+1)
            return None
        _ = d.setdefault('model', d.get('convention', ''))
        _ = d.setdefault('experiment', '')
        _ = d.setdefault('CASENAME', '{}_{}'.format(d['model'], d['experiment']))

        for field in ['FIRSTYR', 'LASTYR', 'convention']:
            if not d.get(field, None):
                _log.warning(("No value set for %s in caselist entry #%d, "
                    "skipping."), field, n+1)
                return None
        # if pods set from CLI, overwrite pods in case list
        d['pod_list'] = self.set_case_pod_list(d, cli_obj, pod_info_tuple)
        return d

    def parse_case_list(self, cli_obj, pod_info_tuple):
        d = cli_obj.config # abbreviate
        if 'CASENAME' in d and d['CASENAME']:
            # defined case from CLI
            cli_d = self._populate_from_cli(cli_obj, 'MODEL')
            if 'CASE_ROOT_DIR' not in cli_d and d.get('root_dir', None):
                # CASE_ROOT was set positionally
                cli_d['CASE_ROOT_DIR'] = d['root_dir']
            case_list_in = [cli_d]
        else:
            case_list_in = util.to_iter(cli_obj.file_case_list)
        self.cases = dict()
        for i, case_d in enumerate(case_list_in):
            case = self.parse_case(i, case_d, cli_obj, pod_info_tuple)
            if case:
                self.cases[case['CASENAME']] = case
        if not self.cases:
            _log.critical(("No valid entries in case_list. Please specify "
                "model run information.\nReceived:"
                f"\n{util.pretty_print_json(case_list_in)}"))
            util.exit_handler(code=1)

    def verify_paths(self, config, p):
        # needs to be here, instead of PathManager, because we subclass it in
        # NOAA_GFDL
        keep_temp = config.get('keep_temp', False)
        # clean out WORKING_DIR if we're not keeping temp files:
        if os.path.exists(p.WORKING_DIR) and not \
            (keep_temp or p.WORKING_DIR == p.OUTPUT_DIR):
            shutil.rmtree(p.WORKING_DIR)

        try:
            for dir_name, create_ in (
                ('CODE_ROOT', False), ('OBS_DATA_ROOT', False),
                ('MODEL_DATA_ROOT', True), ('WORKING_DIR', True)
            ):
                util.check_dir(p, dir_name, create=create_)
        except Exception as exc:
            _log.fatal((f"Input settings for {dir_name} mis-specified (caught "
                f"{repr(exc)}.)"))
            util.exit_handler(code=1)

    def _post_parse_hook(self, cli_obj, config, paths):
        # init other services
        pass

    def _print_config(self, cli_obj, config, paths):
        """Log end result of parsing package settings. This is only for the user's
        benefit; a machine-readable version which is usable for
        provenance/reproducibility is saved by the OutputManager as
        ``config_save.jsonc``.
        """
        d = dict()
        for n, case in enumerate(self.iter_children()):
            key = 'case_list({})'.format(n)
            d[key] = case
        d['paths'] = paths.toDict()
        d['paths'].pop('_unittest', None)
        d['settings'] = dict()
        all_groups = set(arg_gp.title for arg_gp in \
            cli_obj.iter_arg_groups(subcommand=None))
        settings_gps = all_groups.difference(
            ('parser','PATHS','MODEL','DIAGNOSTICS'))
        for group in settings_gps:
            d['settings'] = self._populate_from_cli(cli_obj, group, d['settings'])
        d['settings'] = {k:v for k,v in d['settings'].items() \
            if k not in d['paths']}
        d['env_vars'] = config.global_env_vars
        _log.info('PACKAGE SETTINGS:')
        _log.info(util.pretty_print_json(d))

    # --------------------------------------------------------------------

    @property
    def failed(self):
        """Overall success/failure of this run of the framework. Return True if
        any case or any POD has failed, else return False.
        """
        def _failed(obj):
            # need this workaround in case we failed early in init
            return (not hasattr(obj, 'failed')) or obj.failed

        # should be unnecessary if we've been propagating status correctly
        if self.status == ObjectStatus.FAILED or not self.cases:
            return True
        for case in self.iter_children():
            if _failed(case) or not hasattr(case, 'pods') or not case.pods:
                return True
            if any(_failed(p) for p in case.iter_children()):
                return True
        return False

    def main(self):
        # only run first case in list until dependence on env vars cleaned up
        self.cases = dict(list(self.cases.items())[0:1])

        new_d = dict()
        for case_name, case_d in self.cases.items():
            _log.info("### %s: initializing case '%s'.", self.full_name, case_name)
            case = self.DataSource(case_d, parent=self)
            case.setup()
            new_d[case_name] = case
        self.cases = new_d
        util.transfer_log_cache(close=True)

        for case_name, case in self.cases.items():
            if not case.failed:
                _log.info("### %s: requesting data for case '%s'.",
                    self.full_name, case_name)
                case.request_data()
            else:
                _log.info(("### %s: initialization for case '%s' failed; skipping "
                    f"data request."), self.full_name, case_name)

            if not case.failed:
                _log.info("### %s: running case '%s'.", self.full_name, case_name)
                run_mgr = self.RuntimeManager(case, self.EnvironmentManager)
                run_mgr.setup()
                run_mgr.run()
            else:
                _log.info(("### %s: Data request for case '%s' failed; skipping "
                    "execution."), self.full_name, case_name)

            out_mgr = self.OutputManager(case)
            out_mgr.make_output()

        tempdirs = TempDirManager()
        tempdirs.cleanup()
        print_summary(self)
        return (1 if self.failed else 0) # exit code

# --------------------------------------------------------------------

def print_summary(fmwk):
    def summary_info_tuple(case):
        """Debug information; will clean this up.
        """
        if not hasattr(case, 'pods') or not case.pods:
            return (
                ['dummy sentinel string'], [],
                getattr(case, 'MODEL_OUT_DIR', '<ERROR: dir not created.>')
            )
        else:
            return (
                [p_name for p_name, p in case.pods.items() if p.failed],
                [p_name for p_name, p in case.pods.items() if not p.failed],
                getattr(case, 'MODEL_OUT_DIR', '<ERROR: dir not created.>')
            )

    d = {c_name: summary_info_tuple(c) for c_name, c in fmwk.cases.items()}
    failed = any(len(tup[0]) > 0 for tup in d.values())
    _log.info('\n' + (80 * '-'))
    if failed:
        _log.info(f"Exiting with errors.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            if tup[0][0] == 'dummy sentinel string':
                _log.info('\tAn error occurred in setup. No PODs were run.')
            else:
                if tup[1]:
                    _log.info((f"\tThe following PODs exited normally: "
                        f"{', '.join(tup[1])}"))
                if tup[0]:
                    _log.info((f"\tThe following PODs raised errors: "
                        f"{', '.join(tup[0])}"))
            _log.info(f"\tOutput written to {tup[2]}")
    else:
        _log.info(f"Exiting normally.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            _log.info(f"\tAll PODs exited normally.")
            _log.info(f"\tOutput written to {tup[2]}")
