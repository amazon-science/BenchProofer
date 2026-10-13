"""Twin-artifact model for matplotlib__matplotlib-13989.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A histogram-drawing routine assembles the keyword options it will forward to
  the underlying histogram computation into a single options mapping. Two
  options may be placed in that mapping:

    * an explicit value range, recorded under the range key. It is recorded
      exactly when the routine is responsible for constraining the binning to a
      given interval -- i.e. in the single-pass case where the bins are not
      pre-computed across several datasets. (In the multi-dataset pre-computed
      case the interval is folded into the pre-computed bins instead, so the
      range key is not placed in the mapping.)

    * a normalisation flag, recorded under the density key. It is recorded
      exactly when normalisation is requested and the datasets are not being
      stacked.

  The behaviour that matters: these two options are INDEPENDENT entries of the
  one mapping. Recording the normalisation flag must not disturb a range entry
  that was already placed: whenever the range was recorded, it remains present
  with its original value in the mapping that is finally forwarded, regardless
  of whether the normalisation flag is also recorded. Symmetrically, the
  normalisation flag is present exactly in the requested-and-not-stacked case
  and absent otherwise, and the range entry is present exactly in the
  single-pass case and absent otherwise.

Modelling choices (Nagini fragment):
  * The options mapping is a ``Dict[int, int]`` from an option-name token to its
    recorded value. ``KEY_RANGE``/``KEY_DENSITY`` are the two option-name
    tokens; only membership (is the option recorded) and per-option value are
    observed, so an integer carrier is faithful (mapping.md S2).
  * The routine builds and returns the freshly-created options mapping (a local
    that is assembled before being forwarded). The runtime conditions that
    select each branch -- whether the bins are pre-computed across several
    datasets, whether normalisation is requested, whether datasets are stacked
    -- are explicit boolean parameters. The range value to record is an opaque
    integer token (only its preservation is observed). The normalisation flag
    records as 1 when requested.

No string indexing is used (Nagini bans it). The behaviour is modelled deeply
(the mapping assembly is spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the mapping assembly is the behaviour under specification and is
# spelled out deeply in the impl region. There is no unchanged opaque callee to
# axiomatise (the downstream histogram computation that consumes the mapping is
# not modelled -- only the assembly of the mapping it receives is).
# axioms-end


# pure-start
@Pure
def KEY_RANGE() -> int:
    # Option-name token under which an explicit value range is recorded.
    return 0


@Pure
def KEY_DENSITY() -> int:
    # Option-name token under which the normalisation flag is recorded.
    return 1
# pure-end


def assemble_binning_options(multi_precomputed: bool, density: bool,
                             stacked: bool, range_value: int) -> Dict[int, int]:
    # pre-conditions-start
    Requires(KEY_RANGE() != KEY_DENSITY())
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(Result()))
    # The range entry is present exactly in the single-pass case, and when it
    # is present it carries exactly the supplied range value. Crucially this
    # holds REGARDLESS of whether the normalisation flag is also recorded: a
    # recorded range survives the recording of the density flag.
    Ensures(Implies(not multi_precomputed,
                    KEY_RANGE() in Result()
                    and Result()[KEY_RANGE()] == range_value))
    Ensures(Implies(multi_precomputed, not (KEY_RANGE() in Result())))
    # The normalisation flag is present exactly when normalisation is requested
    # and the datasets are not stacked, and then records as 1.
    Ensures(Implies(density and not stacked,
                    KEY_DENSITY() in Result()
                    and Result()[KEY_DENSITY()] == 1))
    Ensures(Implies(not (density and not stacked),
                    not (KEY_DENSITY() in Result())))
    # The forwarded mapping contains only the two recognised option entries:
    # every key present is the range key or the density key, never any other.
    Ensures(Forall(int, lambda k: Implies(k in Result(),
                    k == KEY_RANGE() or k == KEY_DENSITY())))
    # post-conditions-end
    # impl-start
    hist_kwargs = {}  # type: Dict[int, int]
    if not multi_precomputed:
        hist_kwargs[KEY_RANGE()] = range_value
    if density and not stacked:
        # Pre-patch: the normalisation branch REBINDS the options mapping to a
        # freshly-created mapping holding only the density flag, discarding any
        # range entry that had been recorded for the single-pass case.
        fresh = {}  # type: Dict[int, int]
        fresh[KEY_DENSITY()] = 1
        hist_kwargs = fresh
    return hist_kwargs
    # impl-end
