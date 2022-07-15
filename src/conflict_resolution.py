"""Currently unused; implements dependency resolution for plug-ins, intended as
part of a future release.
"""

from itertools import chain
from collections import defaultdict

import logging
_log = logging.getLogger(__name__)

def _default_tiebreaker(*args):
    assert len(args) == 1
    return args[0]

def require_all_same(option_dict, option_fn, tiebreaker_fn=None):
    if tiebreaker_fn is None:
        tiebreaker_fn = _default_tiebreaker

    allowed_opts = set(option_fn(v) \
        for v in chain.from_iterable(iter(option_dict.values())))
    for key in option_dict:
        allowed_opts = allowed_opts.intersection(
            set(option_fn(val) for val in option_dict[key])
        )
    if not allowed_opts:
        raise ValueError('Unable to choose the same value for all variables.')
    return dict.fromkeys(option_dict, tiebreaker_fn(allowed_opts))

def same_for_subsets(option_dict, subsets, option_fn, tiebreaker_fn=None):
    if set(option_dict) != set(k for k in chain.from_iterable(subsets)):
        raise AssertionError('Union of subsets is different than set of all keys.')

    choices = dict.fromkeys(option_dict)
    for subset in subsets:
        subset_options = {key: option_dict[key] for key in subset}
        subset_choice = require_all_same(subset_options, option_fn, tiebreaker_fn)
        for key, val in iter(subset_choice.items()):
            if choices[key] not in [None, val]:
                raise ValueError(
                    'Conflicting assignment for {}: {} != {}'.format(
                    key, val, choices[key])
                )
            choices[key] = val
    return choices

def all_same_if_possible(option_dict, subsets, option_fn, tiebreaker_fn=None):
    try:
        return require_all_same(option_dict, option_fn, tiebreaker_fn)
    except ValueError:
        return same_for_subsets(option_dict, subsets, option_fn, tiebreaker_fn)

def minimum_cover(option_dict, option_fn, tiebreaker_fn=None):
    """Determine experiment component(s) from heuristics.

    1. Pick all data from the same component if possible, and from as few
        components if not. See `<https://en.wikipedia.org/wiki/Set_cover_problem>`__
        and `<http://www.martinbroadhurst.com/greedy-set-cover-in-python.html>`__.

    2. If multiple components satisfy (1) equally well, use a tie-breaking
        heuristic (:meth:`~gfdl.GfdlppDataManager._component_tiebreaker`).

    Args:
        datasets (iterable of :class:`~data_manager.DataSetBase`):
            Collection of all variables being requested in this DataManager.

    Returns:
        List of :py:obj:`str`: name(s) of model components to use.

    Raises: AssertionError if problem is unsatisfiable. This indicates some
        error in the input data.
    """
    if tiebreaker_fn is None:
        tiebreaker_fn = _default_tiebreaker

    # drop empty entries from option_dict, although these shouldn't have been
    # passed in the first place

    print("\tDEBUG:", option_dict)
    option_dict = {k:v for k,v in option_dict.items() if v}
    all_idx = set()
    d = defaultdict(set)
    for idx, k in enumerate(list(option_dict)):
        all_idx.add(idx)
        for v in option_dict[k]:
            d[option_fn(v)].add(idx)
    print("\tDEBUG min_cover indices:", all_idx)
    print("\tDEBUG min_cover sets:", d)
    assert set(e for s in iter(d.values()) for e in s) == all_idx

    covered_idx = set()
    cover = []
    while covered_idx != all_idx:
        # max() with k=... only returns one entry if there are duplicates
        # so we need to do two passes in order to call our tiebreaker logic
        max_uncovered = max(len(v - covered_idx) for v in d.values())
        elt_to_add = tiebreaker_fn(
            [k for k, v in d.items() \
                if (len(v - covered_idx) == max_uncovered)]
        )
        cover.append(elt_to_add)
        covered_idx.update(d[elt_to_add])
    assert cover # is not empty
    print("\tDEBUG min_cover:", cover)

    choices = dict.fromkeys(option_dict)
    for k in option_dict:
        choices[k] = tiebreaker_fn(
            set(option_fn(v) for v in option_dict[k] if option_fn(v) in cover)
        )
    return choices
