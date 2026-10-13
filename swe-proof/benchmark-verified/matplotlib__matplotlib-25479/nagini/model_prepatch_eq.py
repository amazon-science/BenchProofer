"""Twin-artifact model for matplotlib__matplotlib-25479.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Two scalar-to-colour mappings are considered equal exactly when they
      carry the SAME extension flag and the SAME lookup-table contents. The
      human-readable label a mapping happens to carry is NOT part of this
      comparison: two mappings with identical lookup tables and identical
      extension flags are equal even when their labels differ, and unequal
      whenever either the lookup table or the extension flag differs.
      Lookup-table contents are compared ENTRY BY ENTRY, and the entrywise
      comparison is the one the numeric tables themselves supply: an entry
      that carries no determinate numeric value compares unequal to every
      entry, including an entry holding that same indeterminate value. So a
      table carrying such an entry is equal to NO table, not even to itself.

  (2) When a mapping is published into the by-label registry under a chosen
      label, the registry stores an INDEPENDENT snapshot reachable under that
      label, and the snapshot's own label is the label it was published under —
      not whatever label the supplied mapping happened to carry. So a later
      lookup by the chosen label returns a mapping whose own label equals the
      chosen label, even when the supplied mapping was labelled differently.
      The supplied mapping is left untouched.

Modelling choices (Nagini fragment):
  * A mapping is a minimal object with only the three touched attributes: its
    label, its extension flag, and its lookup-table contents. Labels are
    modelled as `int` tokens (distinct labels <-> distinct ints); the tested
    behaviour observes only label EQUALITY / INEQUALITY, never label spelling,
    so an `int` carrier is faithful. The extension flag is likewise modelled
    as an `int` token over its whole value domain (distinct flag values <->
    distinct ints): the comparison observes only flag EQUALITY / INEQUALITY,
    never a flag's spelling, and the domain has more than two mutually
    distinguishable values, so a two-valued carrier could not separate values
    the comparison separates. The lookup table is modelled as a `List[int]`,
    one token per entry: a NON-NEGATIVE token is a determinate entry (two of
    them are equal exactly when the tokens are equal), a NEGATIVE token is an
    INDETERMINATE entry, which the entrywise numeric comparison reports as
    unequal to every entry -- itself included. Table comparison is entrywise
    over that relation, matching the elementwise array comparison the real
    mappings use.
  * The by-label registry is a `Dict[int, Cmap]` from a label token to the
    stored snapshot. Dict access is guarded by an explicit membership test.

No callee is axiomatized: both behaviours are pure object/structure logic,
modelled deeply. The independent-snapshot primitive the registration builds on
is validated against its real Python semantics out-of-band by axiom_check.py
(G-AX) as an A-reference, not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class LabelAlreadyBound(Exception):
    """The publication's out-of-band condition: the chosen label is ALREADY bound
    in the registry, so no snapshot is published and the condition is reported to
    the caller instead of a value. A user-defined exception because a builtin
    exception in an ``Exsures`` crashes the Nagini translator."""


class Cmap:
    def __init__(self, name: int, colorbar_extend: int, lut: List[int]) -> None:
        Requires(Acc(list_pred(lut), 1 / 2))
        # The snapshot must actually be BUILT: level 2 leaves room below for the
        # list operations the table-building loop performs (each carries its own
        # obligation), and stays strictly below every caller's level.
        Requires(MustTerminate(2))
        Ensures(Acc(self.name) and self.name == name)  # type: ignore
        Ensures(Acc(self.colorbar_extend) and self.colorbar_extend == colorbar_extend)  # type: ignore
        Ensures(Acc(self.lut) and Acc(list_pred(self.lut)))  # type: ignore
        Ensures(Acc(list_pred(lut), 1 / 2))
        # The snapshot's lookup table holds the same contents as the source.
        Ensures(ToSeq(self.lut) == ToSeq(lut))  # type: ignore
        self.name = name  # type: int
        self.colorbar_extend = colorbar_extend  # type: int
        self.lut = []  # type: List[int]
        i = 0
        while i < len(lut):
            # invariants-start
            Invariant(Acc(list_pred(lut), 1 / 2))
            Invariant(Acc(self.lut) and Acc(list_pred(self.lut)))
            Invariant(0 <= i and i <= len(lut))
            Invariant(len(self.lut) == i)
            Invariant(ToSeq(self.lut) == ToSeq(lut).take(i))
            # The build walks the source table once: `len(lut) - i + 1` bounds the
            # iterations still to come. `i` grows by exactly one per pass and
            # `len(lut)` cannot change (the source is read-only at 1/2
            # permission), so the bound strictly decreases; the guard
            # `i < len(lut)` keeps it >= 2 whenever the body runs, hence positive.
            Invariant(MustTerminate(len(lut) - i + 1))
            # invariants-end
            self.lut.append(lut[i])
            i = i + 1
        Assert(ToSeq(lut).take(len(lut)) == ToSeq(lut))


# axioms-start
# No consumed axioms. Both behaviours under specification are modelled deeply
# (the equality predicate over a mapping's observable state, and the
# label-rebinding registration). The independent-snapshot primitive the
# registration composes is validated against its real Python semantics
# out-of-band by axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def entry_eq(x: int, y: int) -> bool:
    """The entrywise comparison the numeric lookup tables supply. A
    NON-NEGATIVE token is a determinate entry: two determinate entries are
    equal exactly when their tokens are equal. A NEGATIVE token is an
    INDETERMINATE entry, and an indeterminate entry compares unequal to EVERY
    entry -- including an entry carrying that same indeterminate value, so
    this relation is deliberately NOT reflexive."""
    # An entry never compares equal to an indeterminate one, in either slot:
    Ensures(Implies(Result(), x >= 0 and y >= 0))
    return x == y and x >= 0


@Pure
def seq_eq(a: PSeq[int], b: PSeq[int]) -> bool:
    """Content equality of two lookup tables: same length and entrywise-equal
    entries in order, entry equality being `entry_eq`. Front-recursive so a
    single unfold is available per loop step. This mirrors the elementwise
    array comparison the real mappings use, indeterminate entries included."""
    # Equal content implies equal length (proven by the recursive structure):
    Ensures(Implies(Result(), len(a) == len(b)))
    if len(a) == 0 or len(b) == 0:
        return len(a) == 0 and len(b) == 0
    return entry_eq(a[0], b[0]) and seq_eq(a.drop(1), b.drop(1))
# pure-end


def colormaps_equal(self: Cmap, other: Cmap) -> bool:
    # pre-conditions-start
    # Both mappings are read-only: required (and ensured) at fractional
    # permission only.
    Requires(Acc(self.name, 1 / 2) and Acc(self.colorbar_extend, 1 / 2))
    Requires(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))
    Requires(Acc(other.name, 1 / 2) and Acc(other.colorbar_extend, 1 / 2))
    Requires(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))
    # The verdict must actually be DELIVERED: a comparison that never finishes
    # cannot satisfy the characterisation below vacuously. The level is
    # input-dependent so that a caller may compare strictly shorter tables
    # (e.g. freshly built probe mappings) without leaking its own obligation.
    Requires(MustTerminate(len(self.lut) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.name, 1 / 2) and Acc(self.colorbar_extend, 1 / 2))
    Ensures(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))
    Ensures(Acc(other.name, 1 / 2) and Acc(other.colorbar_extend, 1 / 2))
    Ensures(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))
    # Equality is decided by the extension flag AND the lookup-table contents
    # ONLY. The label plays no role: it is absent from this characterisation,
    # so two mappings differing only in label are equal, and any difference in
    # extension flag or lookup table makes them unequal.
    Ensures(Result() == (self.colorbar_extend == other.colorbar_extend
                         and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: equality also requires the labels to match, so
    # two mappings with identical lookup tables and extension flags but distinct
    # labels are wrongly reported unequal.
    if self.name != other.name:
        return False
    if self.colorbar_extend != other.colorbar_extend:
        return False
    if len(self.lut) != len(other.lut):
        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))
        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))
        return False
    i = 0
    while i < len(self.lut):
        # invariants-start
        Invariant(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))
        Invariant(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))
        Invariant(len(self.lut) == len(other.lut))
        Invariant(0 <= i and i <= len(self.lut))
        Invariant(seq_eq(ToSeq(self.lut), ToSeq(other.lut))
                  == seq_eq(ToSeq(self.lut).drop(i), ToSeq(other.lut).drop(i)))
        # The scan advances one entry per pass and the table is read-only, so
        # `len(self.lut) - i + 1` strictly decreases; the guard `i < len(self.lut)`
        # keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(self.lut) - i + 1))
        # invariants-end
        Assert(ToSeq(self.lut).drop(i)[0] == self.lut[i])
        Assert(ToSeq(other.lut).drop(i)[0] == other.lut[i])
        Assert(ToSeq(self.lut).drop(i).drop(1) == ToSeq(self.lut).drop(i + 1))
        Assert(ToSeq(other.lut).drop(i).drop(1) == ToSeq(other.lut).drop(i + 1))
        if not entry_eq(self.lut[i], other.lut[i]):
            return False
        i = i + 1
    Assert(len(ToSeq(self.lut).drop(i)) == 0)
    Assert(len(ToSeq(other.lut).drop(i)) == 0)
    return True
    # impl-end


def register_named(reg: Dict[int, Cmap], name: int, cmap: Cmap) -> None:
    # pre-conditions-start
    Requires(Acc(dict_pred(reg)))
    # The supplied mapping is read-only (the registry stores a snapshot of it):
    # required (and ensured) at fractional permission only.
    Requires(Acc(cmap.name, 1 / 2) and Acc(cmap.colorbar_extend, 1 / 2))
    Requires(Acc(cmap.lut, 1 / 2) and Acc(list_pred(cmap.lut), 1 / 2))
    # The snapshot must actually be PUBLISHED: level 3 sits strictly above the
    # constructor's 2, which this body calls to build the independent snapshot.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(reg)))
    Ensures(Acc(cmap.name, 1 / 2) and Acc(cmap.colorbar_extend, 1 / 2))
    Ensures(Acc(cmap.lut, 1 / 2) and Acc(list_pred(cmap.lut), 1 / 2))
    # The supplied mapping is left untouched.
    Ensures(cmap.name == Old(cmap.name))
    Ensures(cmap.colorbar_extend == Old(cmap.colorbar_extend))
    # Publication happens ONLY under a label that was FREE beforehand: a normal
    # return at all means the chosen label was unbound in the pre-state.
    Ensures(not Old(name in reg))
    # The chosen label now resolves in the registry to a stored snapshot ...
    Ensures(name in reg)
    # ... which is an INDEPENDENT object, not the supplied mapping itself.
    Ensures(reg[name] is not cmap)
    Ensures(Acc(reg[name].name) and Acc(reg[name].colorbar_extend))
    Ensures(Acc(reg[name].lut) and Acc(list_pred(reg[name].lut)))
    # The discriminating clause: the snapshot's OWN label equals the label it
    # was published under, even when the supplied mapping was labelled
    # differently.
    Ensures(reg[name].name == name)
    # The snapshot otherwise carries the supplied mapping's observable state.
    Ensures(reg[name].colorbar_extend == cmap.colorbar_extend)
    Ensures(ToSeq(reg[name].lut) == ToSeq(cmap.lut))
    # No other registry entry is disturbed: publishing under the chosen label
    # writes that label ONLY. Every other label keeps exactly its previous
    # membership (nothing else is added or dropped) and, when present, stays
    # bound to the very same mapping object it held before.
    Ensures(Forall(int, lambda k: Implies(k != name,
                                          (k in reg) == Old(k in reg))))
    Ensures(Forall(int, lambda k: Implies(k != name and Old(k in reg),
                                          reg[k] is Old(reg[k]))))
    # post-conditions-end
    # A label that is ALREADY bound is REFUSED: nothing is published under it and
    # the condition reaches the caller out of band instead. The registry is left
    # exactly as it was -- every label keeps its previous membership AND the very
    # same mapping object it was bound to -- and the supplied mapping is
    # untouched. So a live binding is never replaced by a snapshot of the
    # supplied mapping, nor relabelled, nor dropped.
    Exsures(LabelAlreadyBound,
            Acc(dict_pred(reg))
            and Acc(cmap.name, 1 / 2) and Acc(cmap.colorbar_extend, 1 / 2)
            and Acc(cmap.lut, 1 / 2) and Acc(list_pred(cmap.lut), 1 / 2)
            and Old(name in reg)
            and cmap.name == Old(cmap.name)
            and cmap.colorbar_extend == Old(cmap.colorbar_extend)
            and Forall(int, lambda k: Implies(k != name,
                                              (k in reg) == Old(k in reg)))
            and Forall(int, lambda k: Implies(k != name and Old(k in reg),
                                              reg[k] is Old(reg[k])))
            and name in reg and reg[name] is Old(reg[name]))
    # impl-start
    # The already-bound label is refused before anything is built or stored.
    if name in reg:
        raise LabelAlreadyBound()
    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)
    # The published snapshot is relabelled to the chosen registration label, so
    # that a later lookup by that label yields a mapping whose own label matches
    # the label it was looked up under.
    snapshot.name = name
    reg[name] = snapshot
    # impl-end
