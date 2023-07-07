"""Classes that define varlist coordinates and other attributes
"""
import dataclasses as dc
import typing
from abc import ABC
from src import util
from src import data_model
from src import varlistentry_util
from src import translation

import os

# The definitions and classes in the varlist_util module are separate from the
# diagnostic module to prevent circular module imports

PodDataFileFormat = util.MDTFEnum(
    'PodDataFileFormat',
    ("ANY_NETCDF ANY_NETCDF_CLASSIC "
     "ANY_NETCDF3 NETCDF3_CLASSIC NETCDF_64BIT_OFFSET NETCDF_64BIT_DATA "
     "ANY_NETCDF4 NETCDF4_CLASSIC NETCDF4"),
    module=__name__
)


@util.mdtf_dataclass
class _VarlistGlobalSettings(object):
    format: PodDataFileFormat = \
        dc.field(default=PodDataFileFormat.ANY_NETCDF_CLASSIC, metadata={'query': True})
    rename_variables: bool = False
    multi_file_ok: bool = False
    dimensions_ordered: bool = False


@util.mdtf_dataclass
class _VarlistTimeSettings(object):
    frequency:     util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    max_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_duration: str = util.NOTSET
    max_duration: str = util.NOTSET


@util.mdtf_dataclass
class VarlistSettings(_VarlistGlobalSettings, _VarlistTimeSettings):
    """Class to describe options affecting all variables requested by this POD.
    Corresponds to the "data" section of the POD's settings.jsonc file.
    """
    @property
    def global_settings(self):
        return util.filter_dataclass(self, _VarlistGlobalSettings)

    @property
    def time_settings(self):
        return util.filter_dataclass(self, _VarlistTimeSettings)


@util.mdtf_dataclass
class VarlistCoordinateMixin(object):
    """Base class to describe a single dimension (in the netcdf data model sense)
    used by one or more variables. Corresponds to list entries in the
    "dimensions" section of the POD's settings.jsonc file.
    """
    need_bounds: bool = False


@util.mdtf_dataclass
class VarlistCoordinate(data_model.DMCoordinate, VarlistCoordinateMixin):
    # name: str              # fields from data_model.DMCoordinate
    # standard_name: str
    # units: units.Units
    # axis: str
    # bounds: AbstractDMCoordinateBounds
    # value: typing.Union[int, float] # for scalar coordinates only
    # need_bounds: bool      # fields from VarlistCoordinateMixin
    # name_in_model: str
    # bounds_in_model: str
    pass


@util.mdtf_dataclass
class VarlistHorizontalCoordinate(data_model.DMHorizontalCoordinate,
                                  VarlistCoordinateMixin):
    range: tuple = None


@util.mdtf_dataclass
class VarlistVerticalCoordinate(data_model.DMVerticalCoordinate,
                                VarlistCoordinateMixin):
    pass


@util.mdtf_dataclass
class VarlistPlaceholderTimeCoordinate(data_model.DMGenericTimeCoordinate,
                                       VarlistCoordinateMixin):
    frequency: typing.Any = ""
    min_frequency: typing.Any = ""
    max_frequency: typing.Any = ""
    min_duration: typing.Any = 'any'
    max_duration: typing.Any = 'any'

    standard_name = 'time'
    axis = 'T'


@util.mdtf_dataclass
class VarlistTimeCoordinate(_VarlistTimeSettings, data_model.DMTimeCoordinate,
                            VarlistCoordinateMixin, ABC):
    pass


class Varlist(data_model.DMDataSet):
    """Class to perform bookkeeping for the model variables requested by a
        single POD for multiple cases/ensemble members
    """

    def find_var(self, v):
        """If a variable matching *v* is already present in the Varlist, return
        (a reference to) it (so that we don't try to add duplicates), otherwise
        return None.
        """
        for vv in self.iter_vars():
            if v == vv:
                return vv
        return None

    def setup_var(self, pod, v):
        """Update VarlistEntry fields with information that only becomes
        available after DataManager and Diagnostic have been configured (ie,
        only known at runtime, not from settings.jsonc.)

        Could arguably be moved into VarlistEntry's init, at the cost of
        dependency inversion.
        """
        translate = translation.VariableTranslator().get_convention(self.convention)
        if v.T is not None:
            v.change_coord(
                'T',
                new_class={
                    'self': VarlistTimeCoordinate,
                    'range': util.DateRange,
                    'frequency': util.DateFrequency
                },
                range=self.attrs.date_range,
                calendar=util.NOTSET,
                units=util.NOTSET
            )
        v.dest_path = self.variable_dest_path(pod, v)
        try:
            trans_v = translate.translate(v)
            v.translation = trans_v
            # copy preferred gfdl post-processing component during translation
            if hasattr(trans_v, "component"):
                v.component = trans_v.component
        except KeyError as exc:
            # can happen in normal operation (eg. precip flux vs. rate)
            chained_exc = util.PodConfigEvent((f"Deactivating {v.full_name} due to "
                                               f"variable name translation: {str(exc)}."))
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)
        except Exception as exc:
            chained_exc = util.chain_exc(exc, f"translating name of {v.full_name}.",
                                         util.PodConfigError)
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)

        v.stage = VarlistEntryStage.INITED

    def variable_dest_path(self, pod, var):
        """Returns the absolute path of the POD's preprocessed, local copy of
        the file containing the requested dataset. Files not following this
        convention won't be found by the POD.
        """
        if var.is_static:
            f_name = f"{self.name}.{var.name}.static.nc"
            return os.path.join(pod.POD_WK_DIR, f_name)
        else:
            freq = var.T.frequency.format_local()
            f_name = f"{self.name}.{var.name}.{freq}.nc"
            return os.path.join(pod.POD_WK_DIR, freq, f_name)

    @classmethod
    def from_struct(cls, parent):
        """Parse the "dimensions", "data" and "varlist" sections of the POD's
        settings.jsonc file when instantiating a new :class:`Diagnostic` object.

        Args:
            parent: instance of the parent class object

        Returns:
            :py:obj:`dict`, keys are names of the dimensions in POD's convention,
            values are :class:`PodDataDimension` objects.
        """

        def _pod_dimension_from_struct(name, dd, v_settings):
            class_dict = {
                'X': VarlistHorizontalCoordinate,
                'Y': VarlistHorizontalCoordinate,
                'Z': VarlistVerticalCoordinate,
                'T': VarlistPlaceholderTimeCoordinate,
                'OTHER': VarlistCoordinate
            }
            try:
                return data_model.coordinate_from_struct(
                    dd, class_dict=class_dict, name=name,
                    **v_settings.time_settings
                )
            except Exception:
                raise ValueError(f"Couldn't parse dimension entry for {name}: {dd}")

        def _iter_shallow_alternates(var):
            """Iterator over all VarlistEntries referenced as alternates. Doesn't
            traverse alternates of alternates, etc.
            """
            for alt_vs in var.alternates:
                yield from alt_vs

        vlist_settings = util.coerce_to_dataclass(
            parent.pod_data, VarlistSettings)
        globals_d = vlist_settings.global_settings

        dims_d = parent.pod_dims

        vlist_vars = {
            k: varlistentry_util.VarlistEntry.from_struct(globals_d, dims_d, name=k, parent=parent, **v)
            for k, v in parent.pod_vars.items()
        }
        for v in vlist_vars.values():
            # validate & replace names of alt vars with references to VE objects
            for altv_name in _iter_shallow_alternates(v):
                if altv_name not in vlist_vars:
                    raise ValueError((f"Unknown variable name {altv_name} listed "
                                      f"in alternates for varlist entry {v.name}."))
            linked_alts = []
            for alts in v.alternates:
                linked_alts.append([vlist_vars[v_name] for v_name in alts])
            v.alternates = linked_alts
        return cls(contents=list(vlist_vars.values()))
