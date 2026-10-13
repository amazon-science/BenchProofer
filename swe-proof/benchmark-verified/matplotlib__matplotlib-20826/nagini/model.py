"""Twin-artifact model for matplotlib__matplotlib-20826.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An axis keeps a mapping of tick-appearance settings (e.g. which sides show
  tick marks, whether tick labels are drawn, and other per-side visibility
  flags). When the axis is re-initialised for re-use, exactly one designated
  appearance entry of that mapping is refreshed from two ambient configuration
  flags -- the entry is on exactly when the first flag is enabled AND the
  configured selection covers this mapping's tick class -- WHILE every other
  previously-established entry of the mapping is preserved exactly as it was.

  The consequence that matters: settings a caller has stored to hide tick marks
  and tick labels on one side (as happens for the inner members of a set of
  linked, shared axes) survive re-initialisation. Re-initialising the axis
  refreshes only the one designated entry; it does not discard the other
  appearance entries and therefore does not cause ticks or tick labels that
  should be hidden to reappear.

  There are two such mappings -- one for the major tick class, one for the minor
  tick class. They are re-initialised identically except for which selection
  covers them: the major mapping's designated entry is on when the selection is
  the all-inclusive one or the major one; the minor mapping's designated entry
  is on when the selection is the all-inclusive one or the minor one.

Modelling choices (Nagini fragment):
  * Each tick-appearance mapping is a ``Dict[int, bool]`` from a setting-name
    token to its on/off value; only key membership and the boolean values are
    observed, so integer-keyed identity is the faithful carrier (mapping.md
    section 2). The designated refreshed entry is the module-level constant
    ``refreshed_key()``; any other setting (e.g. a side-hiding tick/label
    visibility flag) is a distinct key.
  * Re-initialisation yields the new tick-appearance mapping (the resulting
    state), so each operation RETURNS a ``Dict[int, bool]`` and reads its input
    mapping only (held at fractional permission, directive 5 -- the result is a
    related mapping, the input itself is not observed mutated).
  * The two ambient configuration flags are ``bool`` parameters: ``flag_enabled``
    (the first ambient flag) and ``selection_covers`` (the configured selection
    covers this mapping's tick class). booleans need no permission. The computed
    designated value is ``flag_enabled and selection_covers`` -- exactly the
    conjunction the configuration prescribes.
  * ``dict_carry_over`` is the unchanged mapping-copy primitive (a fresh mapping
    with the same key/value content as its argument); it is axiomatized and its
    soundness is checked against the real copy primitive out-of-band by
    axiom_check.py (G-AX). It is the WEAKEST contract the proof needs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def dict_carry_over(d: Dict[int, bool]) -> Dict[int, bool]:
    """The unchanged mapping-copy primitive: returns a FRESH mapping with the
    same key/value content as ``d`` -- every key carried over with its value and
    no key introduced; ``d`` is read-only. Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(dict_pred(d), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    Ensures(Forall(int, lambda k: (Implies(k in d,
                                           k in Result() and Result()[k] == d[k]))))
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           k in d and Result()[k] == d[k]))))
# axioms-end


# pure-start
@Pure
def refreshed_key() -> int:
    # The setting-name token for the one designated entry that is refreshed.
    return 0
# pure-end


def reinit_tick_kw_major(tick_kw: Dict[int, bool],
                         flag_enabled: bool,
                         selection_covers: bool) -> Dict[int, bool]:
    # pre-conditions-start
    # The input mapping is read-only (the result is a related mapping):
    # fractional permission (directive 5).
    Requires(Acc(dict_pred(tick_kw), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(tick_kw), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # (1) The one designated entry is present on exit and equals the prescribed
    #     conjunction: the first ambient flag is enabled AND the configured
    #     selection covers this (major) tick class.
    Ensures(refreshed_key() in Result())
    Ensures(Result()[refreshed_key()] == (flag_enabled and selection_covers))
    # (2) Every OTHER entry present on entry is preserved exactly -- present in
    #     the result with the same value. This is the survival guarantee:
    #     appearance settings (e.g. a side-hiding tick/label flag) stored before
    #     re-initialisation are not discarded. An implementation that drops them
    #     cannot verify.
    Ensures(Forall(int, lambda k: (Implies(k in tick_kw and k != refreshed_key(),
                                           k in Result() and Result()[k] == tick_kw[k]))))
    # (3) The result introduces no entry other than the designated entry:
    #     any key in the result other than the designated key was present on
    #     entry with the same value. Stated forward so it constrains spurious
    #     additions.
    Ensures(Forall(int, lambda k: (Implies(k in Result() and k != refreshed_key(),
                                           k in tick_kw and Result()[k] == tick_kw[k]))))
    # post-conditions-end
    # impl-start
    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
    result[refreshed_key()] = flag_enabled and selection_covers
    return result
    # impl-end


def reinit_tick_kw_minor(tick_kw: Dict[int, bool],
                         flag_enabled: bool,
                         selection_covers: bool) -> Dict[int, bool]:
    # pre-conditions-start
    # The input mapping is read-only (the result is a related mapping):
    # fractional permission (directive 5).
    Requires(Acc(dict_pred(tick_kw), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(tick_kw), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # (1) The one designated entry is present on exit and equals the prescribed
    #     conjunction for the minor tick class.
    Ensures(refreshed_key() in Result())
    Ensures(Result()[refreshed_key()] == (flag_enabled and selection_covers))
    # (2) Every OTHER entry present on entry is preserved exactly.
    Ensures(Forall(int, lambda k: (Implies(k in tick_kw and k != refreshed_key(),
                                           k in Result() and Result()[k] == tick_kw[k]))))
    # (3) The result introduces no entry other than the designated entry.
    Ensures(Forall(int, lambda k: (Implies(k in Result() and k != refreshed_key(),
                                           k in tick_kw and Result()[k] == tick_kw[k]))))
    # post-conditions-end
    # impl-start
    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]
    result[refreshed_key()] = flag_enabled and selection_covers
    return result
    # impl-end
