"""Twin-artifact model for pydata__xarray-7233.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A windowing transform rebuilds a collection of named arrays into a fresh
  container. Each member array carries one bit of status: it is either a
  *labelling* array (a coordinate) or a plain *data* array. The rebuild
  re-inserts every member into the fresh container and then settles each
  member's status.

  Two things decide a member's status in the rebuilt container:

  * Its prior status is PRESERVED: a member that was a labelling array is a
    labelling array afterwards, independent of whether its name is one of the
    windowed axes.
  * Independently, the container itself imposes labelling status on any member
    whose insertion name coincides with one of the rebuilt container's axis
    names; such a member is a labelling array whatever its prior status was.
    This is a standing property of the container the rebuild inserts into, not
    something the rebuild chooses.

  A member that was a plain data array and whose insertion name is not one of
  the rebuilt container's axis names stays a plain data array. So the status a
  member ends with is the union of the two conditions above.

  The rebuild is a bounded per-member pass: it MUST actually DELIVER the
  rebuilt status list (a total-correctness obligation, carried as
  MustTerminate in the precondition). Nagini is a partial-correctness
  verifier by default, so without this obligation a diverging implementation
  (e.g. `while True: pass` in place of the pass) would satisfy the value
  postconditions vacuously; the real rebuild always returns its result.

Names are modelled as `int` identifiers; the per-member status bit
(`was_label`, 1 = labelling array), the "is this name one of the windowed
axes" bit (`is_window`), and the "is this member's insertion name one of the
rebuilt container's axis names" bit (`is_axis_name`) are modelled as parallel
0/1 `int` flags in `List[int]`. The per-member status is modelled deeply
(`promoted`); there is no consumed axiom. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the changed selection is modelled deeply, not axiomatized)
# axioms-end


# pure-start
@Pure
def promoted(was_label: int, is_window: int, is_axis_name: int) -> int:
    """The labelling status a single member must have AFTER the rebuild, given
    whether it was a labelling array before (`was_label`, 0/1), whether its
    name is one of the windowed axes (`is_window`, 0/1), and whether its
    insertion name is one of the rebuilt container's axis names
    (`is_axis_name`, 0/1).

    The outcome is the union of the prior labelling bit and the axis-name bit:
    a member is a labelling array afterwards when it was one before, or when
    its insertion name is one of the rebuilt container's axis names, and
    otherwise it is a plain data array -- in either case independent of
    whether its name is one of the windowed axes."""
    Ensures(Implies(was_label == 1, Result() == 1))
    Ensures(Implies(is_axis_name == 1, Result() == 1))
    Ensures(Implies(was_label == 0 and is_axis_name == 0, Result() == 0))
    sel = 0
    if was_label == 1 and is_window == 1:
        sel = 1
    if was_label == 1:
        sel = 1
    if is_axis_name == 1:
        sel = 1
    return sel
# pure-end


def rebuild_label_status(was_label: List[int], is_window: List[int],
                        is_axis_name: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(was_label), 1 / 2))
    Requires(Acc(list_pred(is_window), 1 / 2))
    Requires(Acc(list_pred(is_axis_name), 1 / 2))
    Requires(len(was_label) == len(is_window))
    Requires(len(was_label) == len(is_axis_name))
    # each input position is a 0/1 status / membership flag
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
                                            was_label[k] == 0 or was_label[k] == 1),
                                     [[was_label[k]]])))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_axis_name),
                                            is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                     [[is_axis_name[k]]])))
    # The rebuild is a bounded pass over the members: it must terminate and
    # deliver the status list. Nagini verifies partial correctness by default,
    # so without this obligation a diverging impl (`while True: pass`) would
    # satisfy the value postconditions vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(was_label), 1 / 2))
    Ensures(Acc(list_pred(is_window), 1 / 2))
    Ensures(Acc(list_pred(is_axis_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(was_label) == len(is_window))
    Ensures(len(was_label) == len(is_axis_name))
    Ensures(len(Result()) == len(was_label))
    # the output labelling status is exactly the per-member status
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
                                           Result()[k] == promoted(was_label[k],
                                                                   is_window[k],
                                                                   is_axis_name[k])),
                                    [[Result()[k]]])))
    # the discriminating property: prior labelling status is PRESERVED --
    # position k of the result is 1 whenever the prior labelling bit at k is 1,
    # so every prior labelling array stays a labelling array, independent of
    # which names are windowed.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
                                           Implies(was_label[k] == 1,
                                                   Result()[k] == 1)),
                                    [[Result()[k]]])))
    # the container's standing axis-name property: a member whose insertion
    # name is one of the rebuilt container's axis names is a labelling array.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
                                           Implies(is_axis_name[k] == 1,
                                                   Result()[k] == 1)),
                                    [[Result()[k]]])))
    # and nothing else is promoted: a prior plain data array whose insertion
    # name is not one of the rebuilt container's axis names stays a plain data
    # array. Together with the two clauses above this pins every position.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
                                           Implies(was_label[k] == 0 and
                                                   is_axis_name[k] == 0,
                                                   Result()[k] == 0)),
                                    [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(was_label):
        # invariants-start
        Invariant(Acc(list_pred(was_label), 1 / 2))
        Invariant(Acc(list_pred(is_window), 1 / 2))
        Invariant(Acc(list_pred(is_axis_name), 1 / 2))
        Invariant(len(was_label) == len(is_window))
        Invariant(len(was_label) == len(is_axis_name))
        Invariant(0 <= i and i <= len(was_label))
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
                                                was_label[k] == 0 or was_label[k] == 1),
                                         [[was_label[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(is_axis_name),
                                                is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                         [[is_axis_name[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                result[k] == promoted(was_label[k],
                                                                      is_window[k],
                                                                      is_axis_name[k])),
                                         [[result[k]]])))
        # the per-member pass consumes the caller's termination obligation
        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(was_label) - i + 1))
        # invariants-end
        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # status: (windowed-axis labels) | (all prior labels) | (axis names)
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        Assert(sel == promoted(wl, iw, ax))
        # carry the per-member status fact across the append (trigger-aligned)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                             result[k] == promoted(was_label[k],
                                                                   is_window[k],
                                                                   is_axis_name[k])),
                                      [[result[k]]])))
        old = ToSeq(result)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                             old[k] == result[k]),
                                      [[old[k]]])))
        result = result + [sel]
        Assert(ToSeq(result) == old + PSeq(sel))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                             result[k] == old[k]),
                                      [[result[k]]])))
        Assert(result[i] == sel)
        i = i + 1
    return result
    # impl-end
