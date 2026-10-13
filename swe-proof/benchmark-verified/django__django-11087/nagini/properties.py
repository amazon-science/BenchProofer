# properties.py — PBT falsification battery for django__django-11087. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   rows_exposed_to_observers(pre, post) -> bool
#     plain booleans, NO heap permission. Pinned five ways, incl.
#       Ensures(Result() == exposed_to_observers(pre, post))   # the @Pure oracle
#       Ensures(Result() == (pre or post))                     # grounded, unfolded
#       three Implies pins.
#     The @Pure oracle `exposed_to_observers` IS `return pre or post` — it is
#     FULLY GROUNDED in the args, not an opaque answer-key, so there is NO wrong
#     echo to build (echoing the oracle yields the correct value). The
#     ungrounded-oracle-echo class therefore does NOT apply; we attack the value
#     pins instead (drop a term / fold in a third) and add an honest positive
#     control.
#   select_cascade_fields(all_fields, already_selected, referenced, pk,
#                         whole_row_required, pre, post) -> List[int]
#     READ-ONLY list inputs: Requires(Acc(list_pred(all_fields), 1/2)),
#     Requires(Acc(list_pred(already_selected), 1/2)) and
#     Requires(Acc(list_pred(referenced), 1/2)). => FRAME-MUTATION is MANDATORY,
#     and there are THREE read-only carriers to guard, not two.
#     Load-bearing postconditions pin the result BY FULL VALUE on each cell of
#     the decision partition, which has FOUR cells:
#       Implies(not whole_row_required and not exposed_to_observers(pre,post)
#               and len(referenced) > 0 and Exists(k: referenced[k] == pk),
#               ToSeq(Result()) == ToSeq(referenced))              # cell 1
#       Implies(not whole_row_required and not exposed_to_observers(pre,post)
#               and len(referenced) > 0 and not Exists(k: referenced[k] == pk),
#               ToSeq(Result()) == ToSeq(referenced) + PSeq(pk))   # cell 2
#       Implies(not whole_row_required and not exposed_to_observers(pre,post)
#               and len(referenced) == 0,
#               ToSeq(Result()) == ToSeq(all_fields))              # cell 3
#       Implies(whole_row_required or exposed_to_observers(pre,post),
#               ToSeq(Result()) == ToSeq(already_selected))        # cell 4
#     plus the cell-1 / cell-4 phrasings tied to (whole_row_required or pre or
#     post).
#     Note cells 3 and 4 return DIFFERENT sets (`all_fields` vs
#     `already_selected`), and they coincide only when the pending query happens
#     to fetch every column. Two rivals below (`partial-cell4-returns-full-set`
#     and `partial-cell3-returns-pending-set`) each exploit exactly that
#     coincidence: they are correct on every shape whose pending query fetches
#     everything — which includes the F2P shape — and wrong only where it
#     carries a narrowing of its own. They exist so neither of those two cells
#     can be collapsed into the other without the battery noticing.
#     No value-proxy / length-only / double-mask clause exists, so partial-domain
#     rivals must diverge on a real sub-domain (a flag sub-case, the presence of
#     the identity column, an empty consulted set, the pending query's own
#     column set, or a list shape). Every cell is guarded by its OWN rival below,
#     so no cell can be dropped without the battery noticing.
from pathlib import Path

INSTANCE = "django__django-11087"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl regions (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------

# rows_exposed_to_observers impl (unique because it is the one followed by
# # impl-end; the other `return pre or post` lives in the # pure region).
_BOOL_IMPL_OLD = """    # impl-start
    return pre or post
    # impl-end"""

# select_cascade_fields impl (the whole block; anchored on the unique typed
# local binding).
_FIELDS_IMPL_OLD = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

assert _BOOL_IMPL_OLD in _BASE and _BASE.count(_BOOL_IMPL_OLD) == 1
assert _FIELDS_IMPL_OLD in _BASE and _BASE.count(_FIELDS_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — a structurally-DIFFERENT but CORRECT impl
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-control-fields: branch-REORDER. The gold impl tests the leave-alone guard
# first; this control tests the NARROWING guard first and reorders the other two
# cells behind it. Identical loop shapes (forward append against the same
# front-prefix `.take(i)` invariant — so NO new induction lemma is needed, per
# pilot pitfalls #2/#3), every gold framing Invariant/Assert kept.
_POS_FIELDS = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    if not whole_row_required and not exposed and len(referenced) > 0:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) > 0)
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    elif whole_row_required or exposed:
        Assert(whole_row_required or exposed_to_observers(pre, post))
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

# pos-control-bool: structurally-different CORRECT bool impl. `not (not pre and
# not post)` is De Morgan-equal to `pre or post`; the verifier discharges it
# against all five postcondition pins.
_POS_BOOL = """    # impl-start
    return not (not pre and not post)
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness, MANDATORY) — read-only inputs are Acc(...,1/2).
# A rival that WRITES a read-only input to satisfy the postcondition must be
# REJECTED for INSUFFICIENT PERMISSION. Gold invariants kept verbatim so the
# rejection is attributable solely to the write. All THREE read-only list
# carriers get their own case.
# ===========================================================================

# frame-mut-referenced: in the narrowing branch, write back into `referenced`
# while scanning it. Holding only Acc(list_pred(referenced), 1/2) forbids the
# write `referenced[i] = ...` — verification fails for insufficient permission,
# NOT for a wrong value.
_FRAME_MUT_REFERENCED = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            referenced[i] = referenced[i]
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

# frame-mut-allfields: in the keep-everything branch, mutate `all_fields` in
# place (write back the element it just read) while building the result. Only
# Acc(...,1/2) is held => insufficient permission to write `all_fields[i] = ...`.
_FRAME_MUT_ALLFIELDS = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            all_fields[i] = all_fields[i]
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

# frame-mut-pending: the same attack on the THIRD read-only carrier, the pending
# query's own column set, in the leave-alone branch. This carrier is what the
# realigned cell 4 returns, so it needs its own frame guard: only Acc(...,1/2) is
# held => `already_selected[i] = ...` is insufficient permission.
_FRAME_MUT_PENDING = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            already_selected[i] = already_selected[i]
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness) — a rival correct on most of the F2P/P2P domain
# but diverging on a sub-domain. Must be REJECTED.
# ===========================================================================

# partial-prepatch-passthrough: the PRE-PATCH bug exactly — never make any
# request to the query layer, so whatever the pending query already fetches is
# what is fetched, in every cell. Correct on cell 4 but WRONG on the narrowing
# cells (the F2P scenario: the unneeded column over-fetched). This is the
# behaviour model_prepatch.py reproduces and G-DIFF flags.
_PARTIAL_PASSTHROUGH = """    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(already_selected):
        # invariants-start
        Invariant(Acc(list_pred(already_selected), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(already_selected))
        Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
        Invariant(MustTerminate(len(already_selected) - i + 1))
        # invariants-end
        result = result + [already_selected[i]]
        i = i + 1
    Assert(ToSeq(already_selected).take(len(already_selected))
           == ToSeq(already_selected))
    return result
    # impl-end"""

# partial-ignore-whole-row-required: drop the whole-row term from the guard.
# Correct whenever whole_row_required is False (the whole F2P scenario), but
# WRONG on the sub-domain whole_row_required=True and not(pre or post): it would
# narrow the fetch when the spec requires the pending query to stand.
_PARTIAL_IGNORE_WRR = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    if exposed:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif len(referenced) > 0:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

# partial-drop-identity-retention: keep the narrowing, but return ONLY the
# consulted columns — i.e. omit the row-identity column when it is not itself
# one of them. Correct on cell 1 (the F2P shape, where the identity column IS
# consulted) and on the other cells, but WRONG on cell 2. This is the rival that
# pins the identity-retention half of the modelled behaviour.
_PARTIAL_DROP_PK = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

# partial-empty-consulted-narrows: keep the narrowing, but apply it even when NO
# consulted column is reachable, returning just the identity column. Correct on
# cells 1, 2 and 4, but WRONG on cell 3, where naming no column is a reset and
# every column is fetched. Pins the empty-consulted-set half of the behaviour.
_PARTIAL_EMPTY_REDUCES = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    if whole_row_required or exposed:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    else:
        n_ref = len(referenced)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    return result
    # impl-end"""

# partial-cell4-returns-full-set: in cell 4, return the FULL column set instead
# of the pending query's own column set. This is precisely the over-strong claim
# the spec used to make, and it is correct on EVERY shape whose pending query
# fetches every column — which includes the F2P shape and every plain-queryset
# shape — and wrong only where the pending query carries a narrowing of its own.
# It exists so cell 4 cannot be re-strengthened back to `all_fields`.
_PARTIAL_CELL4_FULL = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    if whole_row_required or exposed:
        Assert(whole_row_required or exposed_to_observers(pre, post))
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    elif len(referenced) > 0:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""

# partial-cell3-returns-pending-set: the converse — in cell 3, return the pending
# query's own column set instead of the full one, i.e. treat "name no column" as
# leaving the query alone rather than as a reset. Also correct wherever the
# pending query fetches everything, wrong wherever it carries a narrowing. It
# exists so cell 3 cannot be collapsed into cell 4.
_PARTIAL_CELL3_PENDING = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    if whole_row_required or exposed:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif len(referenced) > 0:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    return result
    # impl-end"""

# partial-bool-drop-post: the bool helper rival that drops the `post` term
# (returns just `pre`). Correct whenever post is False, but WRONG on the
# sub-domain post=True, pre=False. Must be rejected by
# Ensures(Implies(post, Result() is True)).
_PARTIAL_BOOL_DROP_POST = """    # impl-start
    return pre
    # impl-end"""

# partial-bool-add-flag: fold a THIRD term into the disjunction. We cannot add a
# real third flag (the signature has none), so the supporting near-miss is the
# always-True echo, which is correct on the exposed sub-domain but WRONG when
# not pre and not post (must be False). Rejected by
# Ensures(Implies(not pre and not post, Result() is False)).
_PARTIAL_BOOL_ALWAYS_TRUE = """    # impl-start
    return True
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (soundness/verify) — confirm the precondition admits a normal
# F2P-shaped input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller
# function: a new module-level def changes the projected spec view and breaks
# same_spec. Instead we inject the admissibility witness INSIDE the
# select_cascade_fields impl region (elided from the spec view), as a leading
# block that constructs the EXACT F2P column configuration
# (all_fields=[1,2,3], referenced=[1,2], already_selected=[1,2,3], pk=1),
# establishes ALL THREE structural preconditions for that concrete input, shows
# the identity column is among the consulted ones there, and exercises the inner
# verified callee rows_exposed_to_observers on F2P flags. The real impl then runs
# unchanged over the actual params. If a precondition could not be established
# for this legitimate input, the Assert would fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS_FIELDS = """    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # --- admissibility witness for the F2P-shaped input (elided from spec view) ---
    adm_all = [1, 2, 3]  # type: List[int]
    adm_ref = [1, 2]  # type: List[int]
    adm_sel = [1, 2, 3]  # type: List[int]
    # the consulted-subset precondition is establishable for the F2P config
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(adm_ref),
                                          adm_ref[k] in ToSeq(adm_all)))))
    # the pending-column-subset precondition is establishable too
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(adm_sel),
                                          adm_sel[k] in ToSeq(adm_all)))))
    # the row-identity precondition is establishable for that config
    Assert(1 in ToSeq(adm_all))
    # the identity column is among the consulted ones in the F2P config
    Assert(Exists(int, lambda k: (0 <= k and k < len(adm_ref)
                                  and adm_ref[k] == 1)))
    # the inner verified callee accepts the plain-bool F2P flags
    Assert(rows_exposed_to_observers(False, False) == False)
    Assert(rows_exposed_to_observers(True, False) == True)
    # --- end admissibility witness; the real impl follows unchanged ---
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-fields-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _POS_FIELDS),
        "rationale": "structurally-different CORRECT impl: the decision is taken "
                     "narrowing-first instead of leave-alone-first, with the three "
                     "cell bodies reordered to match. Same forward-append loop shape "
                     "against the same front-prefix .take(i) invariant, gold framing "
                     "Invariant/Assert kept (pilot pitfalls #2/#3 avoided), so no new "
                     "induction lemma is needed. If a faithful correct impl cannot "
                     "verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-bool-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _BOOL_IMPL_OLD, _POS_BOOL),
        "rationale": "De Morgan-equal correct impl `not (not pre and not post)` "
                     "== `pre or post`; must satisfy all five postcondition pins. "
                     "If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _ADMISS_FIELDS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds the "
                     "exact F2P column config, establishes ALL THREE structural "
                     "preconditions for that concrete input and shows the identity "
                     "column is among the consulted ones there, then exercises the "
                     "inner callee on F2P flags; the real impl then runs unchanged. "
                     "If a precondition could not be established for this "
                     "legitimate input the Assert fails => PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (MANDATORY; must reject for insufficient permission) ----
    {
        "id": "frame-mut-referenced-inplace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _FRAME_MUT_REFERENCED),
        "refinement": "A faithful real patch that writes back into the read-only "
                      "consulted-column set has no analogue that resolves: that set "
                      "is derived from the related model's metadata; mutating it "
                      "would corrupt state shared across the whole deletion graph "
                      "and the collect loop would compute wrong column sets for "
                      "sibling relations, failing the F2P (and many P2P fast-delete "
                      "cases). It only 'works' here by vacuously satisfying the "
                      "postcondition via an illegal write.",
        "rationale": "the read-only input is held at Acc(list_pred(referenced),1/2); "
                     "writing referenced[i] needs full permission. MUST be rejected "
                     "for INSUFFICIENT PERMISSION (the permission system), not for a "
                     "wrong value. The #1 weakness class; a byte-fuzzer never finds it.",
    },
    {
        "id": "frame-mut-allfields-inplace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _FRAME_MUT_ALLFIELDS),
        "refinement": "writing back into the read-only full column set has no "
                      "resolving real analogue: the gold branch never mutates the "
                      "column set, only reads it to build the SELECT. A patch that "
                      "wrote the field list would corrupt the model metadata and "
                      "break the cascade for every related set, resolving nothing.",
        "rationale": "the keep-everything read-only input is held at "
                     "Acc(list_pred(all_fields),1/2); the in-place write "
                     "all_fields[i]=... requires full permission. MUST be rejected "
                     "for INSUFFICIENT PERMISSION.",
    },
    {
        "id": "frame-mut-pending-inplace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _FRAME_MUT_PENDING),
        "refinement": "the pending query's own column set is likewise read, never "
                      "written, by the real branch: when no request is made the "
                      "pending query is simply handed on. A patch that wrote into it "
                      "would mutate a queryset shared with the caller and resolve "
                      "nothing. This carrier is what the leave-alone cell returns, "
                      "so it needs its own frame guard.",
        "rationale": "held at Acc(list_pred(already_selected),1/2); the in-place "
                     "write already_selected[i]=... requires full permission. MUST "
                     "be rejected for INSUFFICIENT PERMISSION.",
    },

    # ---- PARTIAL-DOMAIN (must reject) ----
    {
        "id": "partial-prepatch-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _PARTIAL_PASSTHROUGH),
        "refinement": "this IS the pre-patch behaviour (never make any request to "
                      "the query layer, hand the pending query on untouched) that "
                      "model_prepatch.py reproduces and G-DIFF flags. The sole F2P "
                      "test asserts the unneeded column is ABSENT from the cascade "
                      "SELECT when nothing observes the rows; handing on the full "
                      "pending query fails that assertion. Its faithful real patch "
                      "(the un-optimized branch) is exactly what does NOT resolve.",
        "rationale": "rejected by the cell-1 value pin: when the consulted set is "
                     "non-empty, contains the identity column, and the pending query "
                     "fetches more, returning the pending set violates "
                     "ToSeq(Result())==ToSeq(referenced).",
    },
    {
        "id": "partial-ignore-whole-row-required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _PARTIAL_IGNORE_WRR),
        "refinement": "dropping the whole-row term narrows the fetch even when the "
                      "whole row was required for that related set. The desired "
                      "behaviour deliberately leaves the pending query alone in that "
                      "case, because narrowing it would interact with the "
                      "already-requested wider fetch; a patch that narrowed it would "
                      "re-introduce that interaction and not be the resolving change.",
        "rationale": "rejected by the cell-4 value pin "
                     "Implies(whole_row_required or exposed_to_observers(pre,post), "
                     "ToSeq(Result())==ToSeq(already_selected)): on the sub-domain "
                     "whole_row_required=True and not(pre or post) the rival returns "
                     "the narrowed set.",
    },
    {
        "id": "partial-drop-identity-retention",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _PARTIAL_DROP_PK),
        "refinement": "a real patch that named the consulted columns to the query "
                      "layer and expected ONLY those back does not describe what the "
                      "query layer does: naming a non-empty column set always "
                      "retains the row-identity column as well. A related model "
                      "reached only through a non-identity reference target has an "
                      "identity column outside the consulted set, and the emitted "
                      "SELECT fetches it; a spec without this clause would be "
                      "satisfied by a model that contradicts the real column set.",
        "rationale": "rejected by the cell-2 value pin "
                     "ToSeq(Result()) == ToSeq(referenced) + PSeq(pk): on the "
                     "sub-domain where the consulted set is non-empty and omits the "
                     "identity column, the rival returns the consulted set alone.",
    },
    {
        "id": "partial-empty-consulted-narrows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _PARTIAL_EMPTY_REDUCES),
        "refinement": "a real patch that applied the narrowing with an EMPTY "
                      "consulted set does not describe the query layer either: "
                      "naming no column at all is a reset, not a narrowing, so every "
                      "column is fetched. A related model with no incoming reference "
                      "at all has an empty consulted set and its SELECT fetches "
                      "every column; a spec without this clause would admit a model "
                      "predicting a narrowed set there.",
        "rationale": "rejected by the cell-3 value pin "
                     "Implies(not whole_row_required and "
                     "not exposed_to_observers(pre,post) and len(referenced)==0, "
                     "ToSeq(Result())==ToSeq(all_fields)).",
    },
    {
        "id": "partial-cell4-returns-full-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _PARTIAL_CELL4_FULL),
        "refinement": "in the leave-alone cell this rival returns the model's FULL "
                      "column set rather than what the pending query was already "
                      "going to fetch. That is wrong of the real branch: when no "
                      "request is made, the pending query is handed on exactly as it "
                      "stands, and a pending query obtained from a source that "
                      "already narrowed it fetches LESS than every column. The rival "
                      "is nevertheless correct on every shape whose pending query "
                      "fetches everything — including the F2P shape — so only the "
                      "cell-4 value pin separates it from the desired behaviour.",
        "rationale": "rejected by the cell-4 value pin "
                     "Implies(whole_row_required or exposed_to_observers(pre,post), "
                     "ToSeq(Result())==ToSeq(already_selected)): where the pending "
                     "column set is a strict part of all_fields the rival returns "
                     "all_fields.",
    },
    {
        "id": "partial-cell3-returns-pending-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FIELDS_IMPL_OLD, _PARTIAL_CELL3_PENDING),
        "refinement": "the converse rival: in the no-consulted-column cell it hands "
                      "the pending query on instead of fetching every column, i.e. "
                      "it treats naming no column as making no request. The real "
                      "query layer distinguishes the two: naming nothing CLEARS any "
                      "narrowing the pending query carried, so the full column set "
                      "comes back. Correct wherever the pending query fetches "
                      "everything, wrong wherever it carries a narrowing of its own.",
        "rationale": "rejected by the cell-3 value pin "
                     "Implies(not whole_row_required and "
                     "not exposed_to_observers(pre,post) and len(referenced)==0, "
                     "ToSeq(Result())==ToSeq(all_fields)): the rival returns "
                     "already_selected, which may be a strict part of all_fields.",
    },
    {
        "id": "partial-bool-drop-post",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BOOL_IMPL_OLD, _PARTIAL_BOOL_DROP_POST),
        "refinement": "the helper rival returns only `pre`, dropping the second "
                      "observation term. The F2P's second half attaches an observer "
                      "of that second kind and asserts the unneeded column IS "
                      "fetched; with the term dropped the exposure predicate stays "
                      "False, columns are narrowed, and the assertion fails. Its "
                      "faithful real patch (a one-term helper) does NOT resolve.",
        "rationale": "rejected by Ensures(Implies(post, Result() is True)) and "
                     "Ensures(Result() == (pre or post)): on post=True, pre=False the "
                     "rival returns False.",
    },

    # ---- supporting mechanical near-misses (cheap; still carry a refinement) ----
    {
        "id": "partial-bool-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BOOL_IMPL_OLD, _PARTIAL_BOOL_ALWAYS_TRUE),
        "refinement": "an always-True exposure predicate forces every cascade to "
                      "leave the pending query alone (the always-over-fetch impl the "
                      "public problem_statement literally requests). It fails the "
                      "F2P's first assertion (the unobserved case must narrow the "
                      "fetch). Supporting near-miss for the 'fold in a spurious "
                      "term' attack the boolean signature cannot express directly.",
        "rationale": "rejected by Ensures(Implies(not pre and not post, "
                     "Result() is False)): on pre=False, post=False it returns True.",
    },
]

# No @ContractOnly axioms in this bundle (meta.axioms == []; axioms region is an
# empty comment). Both changed decisions are modelled DEEPLY as pure boolean /
# sequence logic — there is no opaque callee contract the proof consumes. The two
# A-reference facts (real two-term observation disjunction; the real column-set
# semantics of naming / not naming / not requesting columns of the query layer)
# are validated by axiom_check.py (G-AX) against the real django runtime, which
# is the correct lane for A-references; nothing here is an axiom-soundness /
# axiom-containment obligation. So AXIOM_TESTS is empty.
AXIOM_TESTS = []
