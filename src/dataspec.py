import collections
from src import util
from src import util_mdtf
from src import datelabel

class DataSpec(util.NameSpace):
    """Class to describe datasets.

    `<https://stackoverflow.com/a/48806603>`__ for implementation.
    """
    def __init__(self, *args, **kwargs):
        if 'DateFreqMixin' not in kwargs:
            self.DateFreq = datelabel.DateFrequency
        else:
            self.DateFreq = kwargs['DateFreqMixin']
            del kwargs['DateFreqMixin']
        # assign explicitly else linter complains
        self.name = None
        self.date_range = None
        self.date_freq = None
        self._local_data = None
        self._remote_data = []
        self.alternates = []
        self.axes = dict()
        super(DataSpec, self).__init__(*args, **kwargs)
        if ('var_name' in self) and (self.name is None):
            self.name = self.var_name
            del self.var_name
        if ('freq' in self) and (self.date_freq is None):
            self.date_freq = self.DateFreq(self.freq)
            del self.freq

    def copy(self, new_name=None):
        temp = super(DataSpec, self).copy()
        if new_name is not None:
            temp.name = new_name
        return temp  

    @classmethod
    def from_pod_varlist(cls, pod_convention, var, dm_args):
        translate = util_mdtf.VariableTranslator()
        var_copy = var.copy()
        var_copy.update(dm_args)
        ds = cls(**var_copy)
        ds.original_name = ds.name
        ds.CF_name = translate.toCF(pod_convention, ds.name)
        alt_ds_list = []
        for alt_var in ds.alternates:
            alt_ds = ds.copy(new_name=alt_var)
            alt_ds.original_name = ds.original_name
            alt_ds.CF_name = translate.toCF(pod_convention, alt_ds.name)
            alt_ds.alternates = []
            alt_ds_list.append(alt_ds)
        ds.alternates = alt_ds_list
        return ds

    def _freeze(self):
        """Return immutable representation of (current) attributes.

        Exclude attributes starting with '_' from the comparison, in case 
        we want DataSpecs with different timestamps, temporary directories, etc.
        to compare as equal.
        """
        d = self.toDict()
        keys_to_hash = sorted(k for k in d if not k.startswith('_'))
        d2 = {k: repr(d[k]) for k in keys_to_hash}
        FrozenDataSpec = collections.namedtuple('FrozenDataSpec', keys_to_hash)
        return FrozenDataSpec(**d2)
    