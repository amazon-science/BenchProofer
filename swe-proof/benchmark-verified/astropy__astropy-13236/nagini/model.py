"""Twin-artifact model for astropy__astropy-13236.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Converting an arbitrary column-like input into a stored table column chooses
  exactly one column *kind* from the input's classification. The classification
  is given by a predetermined set of boolean facts about the input (whether it is
  already a column object, whether it is a mixin column, whether its first
  element is a mixin, whether a column of that first element's own class can in
  fact be built from the whole sequence, whether it is an n-dimensional numeric
  array, whether that array carries a structured/record layout of several
  fields, whether it is masked, whether it lacks a dtype but its
  sequence-to-array conversion yields a masked array — e.g. a plain list with
  embedded masked entries — and whether it is empty/None). The rules are tried
  in order and the FIRST one that applies decides:

    * an input that is already a column object keeps its own column nature: a
      masked one is a masked column, an unmasked one an ordinary column. Being
      already a column takes precedence over every rule below, so no later
      rule can re-classify it;
    * otherwise an input that is a mixin column is kept as that mixin kind;
    * otherwise a sequence whose elements are themselves mixins is built from
      the element mixin kind, but ONLY when a column of the element's own class
      can actually be built from the whole sequence; when that construction
      does not succeed the sequence is stored as an ordinary object column
      instead;
    * otherwise a masked array becomes a masked column;
    * otherwise a non-None input without a dtype whose sequence conversion
      yields a masked array (it contains masked entries) also becomes a masked
      column;
    * otherwise (every remaining case, INCLUDING an array carrying a structured
      layout of several fields that is neither an existing column nor a mixin)
      becomes an ordinary, non-masked column.

  In particular a structured (multi-field) array is selected by the SAME rule
  as any other array of the same shape of classification: a masked one yields a
  masked column and an unmasked one yields an ordinary column. Its structured
  layout does NOT divert it into the mixin kind.

  The kinds name WHICH of these selection rules applies to the input, and the
  rule is decided by the input's own classification alone. The masked kind
  means that classification is what forces a masked column class; the ordinary
  kind means it forces nothing masked, so the column is asked for as the
  storing table's own default column class — or, for an input that is already
  an ordinary column, as that column's own class. So a table whose own default
  column class is itself a masked one selects the same kind by the same rule:
  its ordinary selections are asked for as that default, and which kind is
  selected never depends on the table's default.

The classification facts are modelled as booleans (Nagini cannot run the
runtime `isinstance`/dtype probes that produce them); the selected kind is a
small integer code. No library callee is consumed inside a postcondition, so
the axioms region is empty (see mapping.md §3). `axiom_check.py` validates the
decision against the real conversion routine (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modelled delta is a pure boolean decision procedure; no opaque
# library callee is consumed inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def KIND_MIXIN() -> int:
    # input kept as its own mixin column kind
    return 0


@Pure
def KIND_SEQ_MIXIN() -> int:
    # sequence of mixins, built from the element mixin kind
    return 1


@Pure
def KIND_MASKED() -> int:
    # masked column kind
    return 2


@Pure
def KIND_COLUMN() -> int:
    # ordinary, non-masked column kind
    return 3


@Pure
def selected_kind(is_column: bool, is_mixin: bool, data0_is_mixin: bool,
                  elem_cls_builds: bool, is_ndarray: bool, is_structured: bool,
                  is_masked: bool, has_dtype: bool, seq_masked: bool,
                  is_none: bool) -> int:
    """The column kind the conversion must select for an input with the given
    classification facts. This is the desired behaviour spelled out as a total
    function of the classification (the specification the impl must meet); the
    guards are written in the same first-match order the rules are tried in."""
    # An input that is ALREADY a column object is decided first and keeps its
    # own column nature, masked or not; no rule below can re-classify it.
    if is_column and is_masked:
        return KIND_MASKED()
    if is_column:
        return KIND_COLUMN()
    if is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()
# pure-end


def select_column_kind(is_column: bool, is_mixin: bool, data0_is_mixin: bool,
                       elem_cls_builds: bool, is_ndarray: bool,
                       is_structured: bool, is_masked: bool, has_dtype: bool,
                       seq_masked: bool, is_none: bool) -> int:
    # pre-conditions-start
    # The selection must actually be REACHED for every admissible input: the
    # classification is decided in a bounded number of steps and a kind is
    # returned, never left undecided by a computation that runs on forever.
    # This is demanded of every input in the domain, so it is an obligation the
    # implementation carries rather than a restriction on the inputs.
    Requires(MustTerminate(1))
    # Domain facts among the classification bits (real np semantics, mapping.md
    # §4): a masked array is an ndarray; an ndarray always has a dtype; neither
    # a masked array nor any ndarray is the None object; the sequence-conversion
    # bit is defined only for inputs that lack a dtype (an object that already
    # has a dtype never takes the sequence-conversion path).
    Requires(Implies(is_masked, is_ndarray))
    Requires(Implies(is_ndarray, has_dtype))
    Requires(Implies(is_masked, not is_none))
    Requires(Implies(is_ndarray, not is_none))
    Requires(Implies(seq_masked, not has_dtype))
    # The element-class construction probe is likewise a fact ABOUT the
    # sequence-of-mixins case only: it is defined (and only consulted) for a
    # non-column input whose first element is a mixin.
    Requires(Implies(elem_cls_builds, data0_is_mixin and not is_column))
    # Domain facts about an input that is already a column object: the mixin
    # classification excludes every column object by construction, a column
    # object always carries a dtype, and it is not the None object. These
    # narrow nothing realisable — no real column object violates any of them.
    Requires(Implies(is_column, not is_mixin))
    Requires(Implies(is_column, has_dtype))
    Requires(Implies(is_column, not is_none))
    # pre-conditions-end
    # post-conditions-start
    # The selected kind is exactly the desired classification-driven selection.
    Ensures(Result() == selected_kind(is_column, is_mixin, data0_is_mixin,
                                       elem_cls_builds, is_ndarray,
                                       is_structured, is_masked, has_dtype,
                                       seq_masked, is_none))
    # A structured multi-field array that is not a mixin is NOT diverted into
    # the mixin kind: a masked one is a masked column, an unmasked one an
    # ordinary column — the same rule as any plain array of the same
    # classification (this is the discriminating clause the spec pins).
    Ensures(Implies(is_structured and is_ndarray and not is_mixin
                    and not data0_is_mixin and is_masked,
                    Result() == KIND_MASKED()))
    Ensures(Implies(is_structured and is_ndarray and not is_mixin
                    and not data0_is_mixin and not is_masked,
                    Result() == KIND_COLUMN()))
    # The structured layout never changes the selection: an input carrying a
    # multi-field layout selects the same kind its classification would select
    # without it.
    Ensures(Result() == selected_kind(is_column, is_mixin, data0_is_mixin,
                                       elem_cls_builds, is_ndarray, False,
                                       is_masked, has_dtype, seq_masked,
                                       is_none))
    # A sequence whose first element is a mixin selects the element mixin kind
    # only when a column of that element's class can be built from the whole
    # sequence; otherwise it selects the ordinary object column kind.
    Ensures(Implies(not is_mixin and not is_column and data0_is_mixin
                    and not elem_cls_builds, Result() == KIND_COLUMN()))
    # An input that is already a column object keeps its own column nature and
    # is never re-classified by a later rule: a masked one is a masked column,
    # an unmasked one an ordinary column — whatever its layout, and whatever
    # its first element would classify as on its own.
    Ensures(Implies(is_column and is_masked, Result() == KIND_MASKED()))
    Ensures(Implies(is_column and not is_masked, Result() == KIND_COLUMN()))
    # Only an input whose own classification carries a mask selects the masked
    # kind: it is either a masked input (a masked column or a masked array), or
    # a dtype-less one whose sequence conversion yields a masked array. No
    # other classification — a multi-field layout included — selects it.
    Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
    # post-conditions-end
    # impl-start
    # Faithful skeleton of the if/elif column-class selection chain. Each guard
    # mirrors one branch of the real method, in the real first-match order: the
    # already-a-column branch is tested FIRST and keeps the input's own column
    # nature, and every branch below it is an elif under it. The
    # structured-array clause is NOT present, so a structured array falls
    # through to the masked / plain branch. A sequence of mixins is built from
    # the element mixin kind only when that construction succeeds, otherwise it
    # is stored as an ordinary object column. A dtype-less non-None input whose
    # sequence conversion carries a mask is routed to the masked kind by the
    # unchanged sequence-conversion branch.
    if is_column:
        if is_masked:
            return KIND_MASKED()
        return KIND_COLUMN()
    data_is_mixin = is_mixin
    if data_is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()
    # impl-end
