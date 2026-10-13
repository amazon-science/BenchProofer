# properties.py — PBT manifest for django__django-11490. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_unified.gates.pbt) parses.
#
# Instance shape: THREE modeled functions in one model.py modeling the gold patch
# (one added line) inside the combinator compilation branch. The behaviour: when a
# compound query restricts its result to a chosen column list, each reused
# component sub-query must be given THAT list for the current compilation WITHOUT
# being mutated, so a later compilation choosing a different list is not corrupted
# (the F2P test_union_with_values regression) — and "being given the list" is not
# a verbatim assignment: it CLASSIFIES each requested name against the derived
# columns the sub-query exposes at that moment (leading family first) and NARROWS
# both families to exactly the requested ones. The per-compilation working object
# must also CARRY the sub-query's accumulated state (abstracted to the `state`
# token), so a blank-slate replacement object is ruled out.
#
#   columns_for_subquery(cached[Acc 1/2 RO], outer_select[Acc 1/2 RO]) -> Query
#       impl: private = detached_copy(cached); with_columns(private, outer_select);
#             return private
#       load-bearing post:
#         (A) cached UNCHANGED  -> len(cached.columns) == 0, and BOTH derived
#             families still exposed un-narrowed (ToSeq(cached.leading) ==
#             Old(...), same for trailing), and cached.state == Old(cached.state)
#         (B) distinct object   -> Result() is not cached
#         (C) distinct lists    -> Result().columns/leading/trailing are each not
#             cached's container
#         (D) functional pin    -> the three classification equalities against the
#             SHARED sub-query's UN-NARROWED families:
#                 ToSeq(Result().columns)  == own_columns(outer_select,
#                                              cached.leading, cached.trailing)
#                 ToSeq(Result().leading)  == kept_leading(cached.leading,
#                                              outer_select)
#                 ToSeq(Result().trailing) == kept_trailing(cached.trailing,
#                                              outer_select, cached.leading)
#         (E) state carried     -> Result().state == cached.state
#       Both inputs are READ-ONLY (Acc(...,1/2)); MustTerminate(3) forbids vacuity.
#       *** (A)-(C) are the aliasing core: the pre-patch recorded the list on the
#       shared sub-query, and the read-only permission on `cached` is exactly what
#       forbids that. (D) is what makes the spec discriminating in the OTHER
#       direction: because each application narrows the families, applying the
#       chosen list to an ALREADY-narrowed working object cannot reach the pinned
#       outcome, so a rival that applies it more than once is turned down. (E) is
#       the anti-blank-slate pin. ***
#
#   detached_copy(q[Acc 1/4 RO]) -> Query   (A-reference deep model of the
#       per-compilation copy operation, i.e. Query.clone())
#       load-bearing post: Result() is not q ; the three containers are each
#                          independent of q's ; all three sequences copied ;
#                          Result().state == q.state ; q untouched.
#       Input q is READ-ONLY (Acc(...,1/4)); MustTerminate(2).
#
#   with_columns(q[columns/leading/trailing Acc full WRITABLE; state Acc 1/2 RO],
#                fields[Acc 1/2 RO]) -> None   (A-reference deep model of applying
#       a chosen column list, i.e. Query.set_values())
#       load-bearing post: the three classification equalities
#           ToSeq(q.columns)  == own_columns(fields, Old(leading), Old(trailing))
#           ToSeq(q.leading)  == kept_leading(Old(leading), fields)
#           ToSeq(q.trailing) == kept_trailing(Old(trailing), fields, Old(leading))
#       plus q.state == Old(q.state) (applying a column list does not disturb the
#       accumulated state) and ToSeq(fields) == Old(ToSeq(fields)) (the chosen list
#       is only read). Requires len(fields) > 0: an empty list is a DIFFERENT
#       operation on the real callee (it selects every concrete column of the
#       query's own table and narrows nothing), so it is excluded by precondition
#       rather than claimed — see the containment probe below.
#       q's three lists are writable; q.state and `fields` are READ-ONLY;
#       MustTerminate(2).
#
# The functional oracles are GROUNDED: each is a fold over the INPUTS (the chosen
# list and the two families the sub-query exposes), computed by the @Pure
# functions the model defines and the loops re-derive, with no opaque answer-key
# helper. There is no wrong value to echo, so the ungrounded-oracle-echo class
# does NOT apply; positive controls stand in its place.
#
# FRAME-MUTATION is one headline class and it coincides with the real bug: any
# rival that writes the chosen column list onto the SHARED `cached` sub-query (the
# pre-patch behaviour) must REJECT for INSUFFICIENT PERMISSION (cached held at
# 1/2). Frame-mutation cases are authored for every read-only input, including the
# state facet. The other headline class is MIS-CLASSIFICATION: a rival that
# records the chosen list verbatim instead of classifying it, or that fails to
# narrow a family, or that applies the list twice, must REJECT on (D).
#
# No @ContractOnly axioms (meta.axioms == []). The two helpers are A-reference deep
# models of real unchanged repo callees; the AXIOM_TESTS run the REAL callees in
# the instance image and assert the deep models hold — the classification and
# narrowing equalities on pristine AND already-narrowed shapes, the state carry,
# and a caller-domain containment probe.
from pathlib import Path

INSTANCE = "django__django-11490"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swap_n(src, old, new, n):
    """Like _swap for an anchor that legitimately occurs `n` times.

    Two of the loops carry the SAME invariant text (the completed kept_front
    equality), so a variant that reshapes it must reshape both; an exact-count
    assertion keeps that as strict as the unique case rather than degrading to a
    blind replace.
    """
    if src.count(old) != n:
        raise AssertionError(f"expected {n} occurrences, got {src.count(old)}: {old!r}")
    return src.replace(old, new, n)


# ---- exact impl-region bodies, EXTRACTED from the shipped model.py ----
# Earlier revisions of this battery pinned the three bodies as hand-copied string
# literals. That is the one anchor form that can silently rot: a spec repair moves
# the impl text, the literal no longer occurs, and the whole battery dies at
# import (G-PBT then reaches no verdict at all, which is worse than any single
# case failing). The bodies are therefore read out of model.py between the
# machine-parsed markers, in source order, and the uniqueness assertions below are
# kept exactly as strict as before: each extracted body must occur in the frozen
# source EXACTLY once, so every _swap on it is a well-defined single edit.
#
# Everything OUTSIDE the impl regions (signatures, pre/post-conditions, the Query
# class, the axioms/pure regions, the module docstring) is NEVER touched by a
# variant => same_spec holds by construction. (The `invariants` regions are nested
# INSIDE the impl regions, so they are elided by the spec view and may be reshaped
# freely.)
_MARK_S = "    # impl-start\n"
_MARK_E = "    # impl-end\n"


def _impl_bodies(src):
    bodies, pos = [], 0
    while True:
        s = src.find(_MARK_S, pos)
        if s < 0:
            return bodies
        s += len(_MARK_S)
        e = src.index(_MARK_E, s)
        bodies.append(src[s:e].rstrip("\n"))
        pos = e + len(_MARK_E)


_BODIES = _impl_bodies(_BASE)
assert len(_BODIES) == 3, f"expected 3 impl regions in model.py, got {len(_BODIES)}"

# region 0 = detached_copy, region 1 = with_columns, region 2 = columns_for_subquery
_IMPL_DC, _IMPL_WC, _IMPL_CFS = _BODIES

# sanity: each body appears verbatim & uniquely in the frozen model.
assert _BASE.count(_IMPL_DC) == 1, "detached_copy anchor drift"
assert _BASE.count(_IMPL_WC) == 1, "with_columns anchor drift"
assert _BASE.count(_IMPL_CFS) == 1, "columns_for_subquery anchor drift"

# and each body is the one we think it is (a marker reordering would otherwise
# silently point every variant at the wrong function).
assert "result = Query(copied, front, back, q.state)" in _IMPL_DC, "DC body mismatch"
assert "q.leading = kept_front" in _IMPL_WC, "WC body mismatch"
assert "private = detached_copy(cached)" in _IMPL_CFS, "CFS body mismatch"


# ====================== columns_for_subquery variants ======================

# --- CFS frame-mutation == THE REAL BUG (== model_prepatch.py) ---
# The pre-patch branch recorded the chosen list directly on the reused shared
# sub-query (no per-compilation copy) and continued with it. Modeled: apply the
# chosen column list to the SHARED `cached` sub-query and return it.
# `with_columns(cached, ...)` needs full Acc(q.columns) but `cached` is held at
# Acc(cached.columns, 1/2) (read-only, directive 5) — so this MUST reject for
# INSUFFICIENT PERMISSION. This is the headline frame-mutation AND the literal
# bug the patch fixes.
_CFS_REALBUG = (
    "    with_columns(cached, outer_select)\n"
    "    return cached"
)

# --- CFS frame-mutation (direct write to the shared sub-query's list) ---
# A cheaper supporting variant: append the outer columns straight onto the shared
# `cached.columns`. Writing a half-permission list is forbidden -> rejects for
# insufficient permission, not a value mismatch. A faithful real patch that
# recorded the columns in place on the shared/reused query is exactly the
# regression (later compilations reuse the leaked column list).
_CFS_FRAME_DIRECT = (
    "    i = 0\n"
    "    while i < len(outer_select):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(cached.columns))\n"
    "        Invariant(Acc(list_pred(cached.columns)))\n"
    "        Invariant(Acc(list_pred(outer_select), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(outer_select))\n"
    "        Invariant(MustTerminate(len(outer_select) - i))\n"
    "        # invariants-end\n"
    "        cached.columns.append(outer_select[i])\n"
    "        i = i + 1\n"
    "    return cached"
)

# --- CFS BLANK-SLATE: brand-new working object instead of a copy ---
# Builds a FRESH object exposing NO derived columns and carrying the default state
# token, with the chosen list as its own columns. Faithful real patch: replace the
# per-compilation query with a newly-constructed one -> the sub-query's
# accumulated filters and derived-column definitions are lost, and every requested
# name is taken for one of its own columns.
_CFS_BLANK = (
    "    copied = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(outer_select):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_select), 1 / 2))\n"
    "        Invariant(Acc(list_pred(copied)))\n"
    "        Invariant(0 <= i and i <= len(outer_select))\n"
    "        Invariant(ToSeq(copied) == ToSeq(outer_select).take(i))\n"
    "        Invariant(MustTerminate(len(outer_select) - i))\n"
    "        # invariants-end\n"
    "        copied.append(outer_select[i])\n"
    "        i = i + 1\n"
    "    nofront = []  # type: List[int]\n"
    "    noback = []  # type: List[int]\n"
    "    result = Query(copied, nofront, noback, 0)\n"
    "    return result"
)

# --- CFS state reset: the blank-slate defect ISOLATED to clause (E) ---
# Derives the working object correctly and applies the chosen list correctly, then
# resets the accumulated state to the default token. Every column clause holds
# identically to the gold; only the state carry is lost. Faithful real patch: a
# per-compilation object rebuilt from the column selection alone.
_CFS_STATE_RESET = (
    "    private = detached_copy(cached)\n"
    "    with_columns(private, outer_select)\n"
    "    private.state = 0\n"
    "    return private"
)

# --- CFS double application == the audited counterexample ---
# Applies the chosen list, then applies its LAST entry again to the same working
# object. Because the first application narrowed the derived families, the second
# one classifies against the narrowed view: the outcome is a function of the
# already-narrowed object, not of the shared sub-query's un-narrowed families.
# This is the rival the earlier (unconditional-assignment) spec admitted while its
# patch did NOT resolve: F2P passed but two PASS_TO_PASS tests
# (test_union_with_extra_and_values_list, test_union_with_two_annotated_values_list)
# failed, because names resolving to an extra_select / annotation_select entry are
# dropped from the rendered column list. It MUST reject on (D).
_CFS_DOUBLE_LAST = (
    "    private = detached_copy(cached)\n"
    "    with_columns(private, outer_select)\n"
    "    last = []  # type: List[int]\n"
    "    last.append(outer_select[len(outer_select) - 1])\n"
    "    with_columns(private, last)\n"
    "    return private"
)

# --- CFS double application, the AUDITED order: narrow FIRST, then re-apply ---
# The retained counterexample VERBATIM (verdict.md WITNESS atk_12.py): the working
# object is first narrowed to the LAST chosen column, and only then is the full
# chosen list applied.  This order is what made the rival invisible to the earlier
# revision of this spec: that revision's only functional claim was the
# unconditional "the working object's own columns become the chosen list", which
# the SECOND (full-list) call satisfies, so the first call looked like dead code.
# In the real callee it is not dead -- it sets the extra/annotation select masks to
# that one name, so the second call classifies against the narrowed families and
# misfiles every other requested derived-column name as one of the query's own.
# Distinguish this case from `cfs-double-application` above: with the applications
# in the OTHER order the earlier spec would already have rejected the rival (the
# final own-column list is then the one-element list, not the chosen list), so only
# THIS order witnesses the hole that the repair closed.  It must now reject on (D).
_CFS_NARROW_THEN_FULL = (
    "    private = detached_copy(cached)\n"
    "    last = []  # type: List[int]\n"
    "    last.append(outer_select[len(outer_select) - 1])\n"
    "    with_columns(private, last)\n"
    "    with_columns(private, outer_select)\n"
    "    return private"
)

# --- CFS partial-domain: copy but never apply the chosen list ---
# Detaches a working object (so cached is untouched, the result is distinct and
# the state is carried) but FORGETS to apply outer_select. Faithful real patch:
# add the copy step but drop the column-applying call -> the working sub-query
# keeps the shared one's (empty) own column list and its un-narrowed families ->
# the compound query renders the wrong columns -> F2P fails.
_CFS_NO_APPLY = (
    "    private = detached_copy(cached)\n"
    "    return private"
)

# --- CFS mis-classification: assign the chosen list VERBATIM ---
# Copies the shared sub-query, then writes the chosen list straight onto the
# working object's own column list, leaving both derived families un-narrowed.
# This is precisely the behaviour an unconditional "the query's own columns become
# the chosen list" reading would license, and it is NOT what the real callee does
# whenever the sub-query exposes derived columns: names resolving to a derived
# column are served by that column and must not appear among the query's own.
# Faithful real patch: apply the list without consulting the derived columns ->
# the derived columns are still emitted un-narrowed and their names are ALSO
# emitted as own columns -> duplicated/extra columns in the rendered SELECT.
_CFS_VERBATIM = (
    "    private = detached_copy(cached)\n"
    "    chosen = []  # type: List[int]\n"
    "    k = 0\n"
    "    while k < len(outer_select):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_select), 1 / 2))\n"
    "        Invariant(Acc(list_pred(chosen)))\n"
    "        Invariant(0 <= k and k <= len(outer_select))\n"
    "        Invariant(ToSeq(chosen) == ToSeq(outer_select).take(k))\n"
    "        Invariant(MustTerminate(len(outer_select) - k))\n"
    "        # invariants-end\n"
    "        chosen.append(outer_select[k])\n"
    "        k = k + 1\n"
    "    private.columns = chosen\n"
    "    return private"
)

# --- CFS POSITIVE CONTROL: structurally different but CORRECT ---
# Takes TWO chained per-compilation copies (a harmless extra copy) before applying
# the chosen list. The final object is distinct from cached, its three containers
# are fresh, the three classification equalities hold (the extra copy preserves
# both families exactly), and the state token is carried through both copies. A
# genuinely different executable shape that MUST verify (else SPEC-TOO-STRONG).
_CFS_POS = (
    "    scratch = detached_copy(cached)\n"
    "    private = detached_copy(scratch)\n"
    "    with_columns(private, outer_select)\n"
    "    return private"
)

# --- CFS ADMISSIBILITY: precondition facts hold on an F2P-shaped input ---
# Asserts the precondition's own facts (empty shared column list, non-empty chosen
# list) before delegating exactly as the gold does. The asserts discharge, proving
# the Requires admits a normal input (the compound-query compilation the F2P test
# exercises) and, in particular, that it does NOT constrain the two derived
# families — a sub-query exposing any number of them is in domain. A failure would
# be PRECOND-TOO-STRONG. (A literal self-call is not used because the termination
# measure correctly forbids same-measure recursion.)
_CFS_ADMISS = (
    "    # ADMISSIBILITY: the precondition admits a normal in-domain input --\n"
    "    # the shared sub-query has no column list of its own, the chosen list\n"
    "    # is non-empty, both derived families are readable at any length, and\n"
    "    # the accumulated state token is unconstrained.\n"
    "    Assert(len(cached.columns) == 0)\n"
    "    Assert(len(outer_select) > 0)\n"
    "    Assert(len(cached.leading) >= 0)\n"
    "    Assert(len(cached.trailing) >= 0)\n"
    "    private = detached_copy(cached)\n"
    "    with_columns(private, outer_select)\n"
    "    return private"
)


# ====================== detached_copy variants ======================

# --- DC frame-mutation (q is Acc(q.columns, 1/4) read-only) ---
# Appends to the read-only original q.columns to "make a copy in place" then wraps
# it. Writing a 1/4-permission list is forbidden -> rejects for insufficient
# permission, not a value mismatch. A faithful real patch where the copy operation
# mutated the source query's column list would corrupt the shared sub-query the
# copy is meant to leave pristine — the exact aliasing the fix relies on NOT
# happening.
_DC_FRAME = (
    "    q.columns.append(0)\n"
    "    result = Query(q.columns, q.leading, q.trailing, q.state)\n"
    "    return result"
)

# --- DC partial-domain: alias instead of copy ---
# Wraps q's OWN three containers in the new Query (shares them) instead of copying
# them. The contents match but the result is NOT detached: a later application of
# a column list to it would narrow q's families too. Faithful real patch: a
# shallow alias of the sub-query's containers rather than independent copies ->
# the shared sub-query is still mutated downstream -> the regression persists.
_DC_ALIAS = (
    "    result = Query(q.columns, q.leading, q.trailing, q.state)\n"
    "    return result"
)

# --- DC state-drop: copy the three families but NOT the accumulated state ---
# Rejected by Ensures(Result().state == q.state) (any q.state != 0 is a
# counterexample). Faithful real patch: a copy that rebuilds a query from scratch
# keeping only the column selection -> filters and derived-column definitions are
# lost -> wrong rows.
_DC_STATE_DROP = _swap(
    _IMPL_DC,
    "    result = Query(copied, front, back, q.state)",
    "    result = Query(copied, front, back, 0)")

# --- DC drop-leading: copy the own columns and the trailing family only ---
# The working object comes back exposing NO leading derived columns. Faithful real
# patch: a copy operation that forgets one of the two derived-column families ->
# the component sub-query stops emitting the columns the compound query is about
# to ask for, and every requested name that resolved to one is then taken for an
# own column. Rejected by Ensures(ToSeq(Result().leading) == ToSeq(q.leading)).
_DC_DROP_LEADING = _swap(
    _swap(_IMPL_DC,
          "    result = Query(copied, front, back, q.state)",
          "    nofront = []  # type: List[int]\n"
          "    result = Query(copied, nofront, back, q.state)"),
    "    Assert(ToSeq(result.leading) == ToSeq(q.leading))\n",
    "")

# --- DC swap-families: copy both derived families into each other's slot ---
# Every container is independent and every element is preserved; only WHICH family
# each belongs to is exchanged. The two families are not interchangeable: they are
# rendered on opposite sides of the query's own columns and the leading one is
# consulted FIRST when a requested name is classified, so exchanging them changes
# both the rendered order and the classification. Rejected by the two family
# equalities.
_DC_SWAP_FAMILIES = _swap(
    _swap(
        _swap(_IMPL_DC,
              "    result = Query(copied, front, back, q.state)",
              "    result = Query(copied, back, front, q.state)"),
        "    Assert(ToSeq(result.leading) == ToSeq(q.leading))\n",
        ""),
    "    Assert(ToSeq(result.trailing) == ToSeq(q.trailing))\n",
    "")

# --- DC POSITIVE CONTROL: structurally different but CORRECT ---
# Hoists the own-column length into a local bound `n`, drives the first copy loop
# off `n`, and rebases that loop's invariant and termination measure on it. A
# different executable shape with an identical effect; must verify (else
# SPEC-TOO-STRONG).
_DC_POS = _swap(
    _swap(
        _swap(_IMPL_DC,
              "    i = 0\n"
              "    while i < len(q.columns):",
              "    n = len(q.columns)\n"
              "    i = 0\n"
              "    while i < n:"),
        "        Invariant(0 <= i and i <= len(q.columns))",
        "        Invariant(n == len(q.columns))\n"
        "        Invariant(0 <= i and i <= len(q.columns))"),
    "        Invariant(MustTerminate(len(q.columns) - i))",
    "        Invariant(MustTerminate(n - i))")


# ====================== with_columns variants ======================

# --- WC frame-mutation (fields is Acc(list_pred(fields), 1/2) read-only) ---
# Mutates the read-only `fields` input (append) before the gold body runs. Writing
# a half-permission list is forbidden -> rejects for insufficient permission, and
# it also breaks Ensures(ToSeq(fields) == Old(ToSeq(fields))). A faithful real
# patch where applying a column list mutated its argument would corrupt the OUTER
# query's chosen list, which is shared across the compiler's loop over components,
# so a later component sub-query would be given a different list than the caller
# asked for.
_WC_FRAME_FIELDS = "    fields.append(0)\n" + _IMPL_WC

# --- WC frame-mutation on the STATE facet (q.state is Acc 1/2 read-only) ---
# Applies the column list correctly but then clobbers the query's accumulated
# state token. Writing a half-permission field is forbidden -> rejects for
# insufficient permission, and it contradicts Ensures(q.state == Old(q.state)). A
# faithful real patch where applying a column list wiped the query's filters or
# its derived-column definitions would yield wrong rows even on a private copy.
_WC_STATE_CLOBBER = _IMPL_WC + "\n    q.state = 0"

# --- WC mis-classification: record the chosen list VERBATIM ---
# *** The load-bearing case for the classification obligation. *** Sets the
# query's own columns to a copy of the whole chosen list and leaves both derived
# families untouched — the behaviour an unconditional "own columns become the
# chosen list" reading licenses. The real callee only behaves that way on its
# shortcut path (a query exposing NO derived columns); otherwise it PARTITIONS the
# requested names, serves those resolving to a derived column from that column,
# and narrows both families. So this rival both keeps names among the own columns
# that the callee moves out, and leaves un-narrowed families the callee narrows.
# Faithful real patch: apply the list without consulting the derived columns ->
# names resolving to an extra/annotation entry are emitted twice and the
# un-requested derived columns are still emitted.
_WC_VERBATIM = (
    "    chosen = []  # type: List[int]\n"
    "    k = 0\n"
    "    while k < len(fields):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(fields), 1 / 2))\n"
    "        Invariant(ToSeq(fields) == Old(ToSeq(fields)))\n"
    "        Invariant(Acc(list_pred(chosen)))\n"
    "        Invariant(0 <= k and k <= len(fields))\n"
    "        Invariant(ToSeq(chosen) == ToSeq(fields).take(k))\n"
    "        Invariant(MustTerminate(len(fields) - k))\n"
    "        # invariants-end\n"
    "        chosen.append(fields[k])\n"
    "        k = k + 1\n"
    "    Assert(ToSeq(fields).take(len(fields)) == ToSeq(fields))\n"
    "    q.columns = chosen"
)

# --- WC no-narrow: classify the own columns, but keep the WHOLE leading family --
# The own-column partition is computed exactly as the gold does; only the leading
# family is left un-narrowed (every leading derived column is kept, requested or
# not). Isolates the narrowing half of the obligation to a single clause. Faithful
# real patch: apply the list but never restrict the derived columns the sub-query
# goes on to expose -> the component emits derived columns the compound query did
# not ask for, so the two sides of a UNION disagree on their column count.
# Rejected by Ensures(ToSeq(q.leading) == kept_leading(Old(ToSeq(q.leading)),
# ToSeq(fields))).
_WC_KEEP_LEADING = _swap_n(
    _swap(
        _swap(_IMPL_WC,
              "        if name in fields:\n"
              "            kept_front.append(name)\n",
              "        kept_front.append(name)\n"),
        "        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(q.leading).take(i),\n"
        "                                                    ToSeq(fields)))\n",
        "        Invariant(ToSeq(kept_front) == ToSeq(q.leading).take(i))\n"),
    "        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(q.leading),\n"
    "                                                    ToSeq(fields)))\n",
    "        Invariant(ToSeq(kept_front) == ToSeq(q.leading))\n",
    2)

# --- WC precedence: drop the leading-wins rule when narrowing the trailing family
# A requested name may be exposed by BOTH families. The real callee classifies it
# against the leading family FIRST, so the trailing entry of the same name is NOT
# kept. This rival keeps it (the guard `not (later in q.leading)` is dropped, and
# the loop invariants are rebased accordingly so the rejection lands on the
# postcondition rather than on a proof step). Faithful real patch: narrow the two
# families independently -> a name exposed by both is emitted twice.
# Rejected by Ensures(ToSeq(q.trailing) == kept_trailing(...)).
_WC_NO_PRECEDENCE = _swap(
    _swap(
        _swap(_IMPL_WC,
              "        if later in fields and not (later in q.leading):\n",
              "        if later in fields:\n"),
        "        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(q.trailing).take(j),\n"
        "                                                    ToSeq(fields),\n"
        "                                                    ToSeq(q.leading)))\n",
        "        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(q.trailing).take(j),\n"
        "                                                    ToSeq(fields),\n"
        "                                                    PSeq(0).take(0)))\n"),
    "        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(q.trailing),\n"
    "                                                    ToSeq(fields),\n"
    "                                                    ToSeq(q.leading)))\n",
    "        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(q.trailing),\n"
    "                                                    ToSeq(fields),\n"
    "                                                    PSeq(0).take(0)))\n")

# --- WC partial-domain: drop the LAST requested name ---
# The own-column loop stops one entry short (`k + 1 < len(fields)`). Faithful real
# patch: an application step that loses the last requested column -> the compound
# query renders one fewer column than the values_list asked for -> F2P (and any
# P2P selecting that column) fails. Rejected by the own_columns clause.
_WC_DROP_LAST = _swap(_IMPL_WC,
                      "    while k < len(fields):",
                      "    while k + 1 < len(fields):")

# --- WC POSITIVE CONTROL: structurally different but CORRECT ---
# Inverts BOTH derived-family guards into if/else form (the empty branch asserting
# the negated condition), so the classification decisions are taken in the
# opposite syntactic order while the computed families are identical. Must verify
# (else SPEC-TOO-STRONG).
_WC_POS = _swap(
    _swap(_IMPL_WC,
          "        if name in fields:\n"
          "            kept_front.append(name)\n",
          "        if not (name in fields):\n"
          "            Assert(not (name in fields))\n"
          "        else:\n"
          "            kept_front.append(name)\n"),
    "        if later in fields and not (later in q.leading):\n"
    "            kept_back.append(later)\n",
    "        if not (later in fields) or later in q.leading:\n"
    "            Assert(not (later in fields) or later in q.leading)\n"
    "        else:\n"
    "            kept_back.append(later)\n")

# --- WC ADMISSIBILITY: the non-empty-list precondition admits its input --------
# `Requires(len(fields) > 0)` is the domain restriction the empty-chosen-list
# divergence forces (an empty list is a different operation on the real callee).
# This case asserts that fact plus the absence of any constraint on the two
# derived families before running the gold body: the precondition admits a chosen
# list of any positive length applied to a query exposing any number of derived
# columns. A failure would be PRECOND-TOO-STRONG.
_WC_ADMISS = (
    "    # ADMISSIBILITY: the precondition admits a normal in-domain input --\n"
    "    # a non-empty chosen list, applied to a query whose two derived\n"
    "    # families may be of any length and whose state token is arbitrary.\n"
    "    Assert(len(fields) > 0)\n"
    "    Assert(len(q.leading) >= 0)\n"
    "    Assert(len(q.trailing) >= 0)\n" + _IMPL_WC
)


SPEC_TESTS = [
    # ---------------- columns_for_subquery (the modeled changed code) ----------------
    {
        "id": "cfs-frame-realbug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_REALBUG),
        "refinement": "The literal PRE-PATCH branch (== model_prepatch.py): the "
                      "chosen column list is applied directly to the reused/shared "
                      "component sub-query (no per-compilation copy), and that same "
                      "query is carried into the rest of the compilation. Modeled "
                      "as with_columns(cached, outer_select); return cached. The "
                      "shared sub-query object is the SAME across repeated "
                      "evaluations of the compound queryset, so the first "
                      "evaluation's mutation leaks: the second values_list('order') "
                      "evaluation finds a non-empty column list and narrowed "
                      "derived families and reuses the stale ones -> F2P "
                      "test_union_with_values fails.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: `cached` is held at "
                     "Acc(cached.columns, 1/2) (read-only, directive 5) but "
                     "with_columns requires full Acc(q.columns) to write. The "
                     "rejection comes from the permission system, attributable to "
                     "mutating the shared sub-query (the bug). It also contradicts "
                     "Ensures(len(cached.columns)==0), the two un-narrowed family "
                     "clauses, and Ensures(Result() is not cached). Gold "
                     "postconditions kept verbatim.",
    },
    {
        "id": "cfs-frame-direct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_FRAME_DIRECT),
        "refinement": "Appends the outer columns directly onto the shared "
                      "cached.columns and returns cached. A faithful real patch "
                      "that mutates the reused query's column list in place (the "
                      "regression) leaks the column list into later compilations of "
                      "the same reused component entry -> F2P fails. Not the gold "
                      "copy-then-apply fix.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: cached.columns is "
                     "held at Acc(list_pred(cached.columns), 1/2); establishing the "
                     "loop's full-permission invariant (needed by .append) is "
                     "impossible. Attributable to the write on the read-only shared "
                     "sub-query, not a value mismatch.",
    },
    {
        "id": "cfs-blank-slate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_BLANK),
        "refinement": "Swaps in a BRAND-NEW blank working object: no derived "
                      "columns, the default state token, and the chosen list as its "
                      "own columns. Faithful real patch: replace the "
                      "per-compilation query with a newly-constructed one -> the "
                      "sub-query's accumulated filters and derived-column "
                      "definitions are lost, and every requested name is taken for "
                      "one of the sub-query's own columns even when the sub-query "
                      "exposes a derived column of that name -> the F2P target may "
                      "pass while sibling P2P tests exercising that accumulated "
                      "state regress.",
        "rationale": "Rejected by the state-carrying pin Ensures(Result().state == "
                     "cached.state) (the blank object's default token differs from "
                     "any cached.state != 0) and, whenever the shared sub-query "
                     "exposes a derived column, by the three classification "
                     "clauses (the blank object's families are empty, so it "
                     "narrows nothing and classifies nothing).",
    },
    {
        "id": "cfs-state-reset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_STATE_RESET),
        "refinement": "Derives the working object from the shared sub-query and "
                      "applies the chosen list exactly as the gold does, then "
                      "resets the accumulated state to the default token. Faithful "
                      "real patch: a per-compilation object rebuilt from the column "
                      "selection alone -> the component contributes the wrong rows "
                      "even though it renders the right columns.",
        "rationale": "The blank-slate defect ISOLATED: every column clause holds "
                     "identically to the gold, so the ONLY failing clause is "
                     "Ensures(Result().state == cached.state). Any cached.state != "
                     "0 is a counterexample.",
    },
    {
        "id": "cfs-double-application",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_DOUBLE_LAST),
        "refinement": "Applies the chosen list to the working object and then "
                      "applies its LAST entry again — the same wrong-fix family as "
                      "the audited counterexample (see cfs-narrow-then-full for the "
                      "audited order), reached by a faithful real patch that calls "
                      "set_values twice on the cloned query. Its patch does not "
                      "resolve: the second application classifies against the "
                      "ALREADY-NARROWED families, so every requested name that "
                      "resolves to an extra_select / annotation_select entry is "
                      "misfiled or dropped from the rendered column list.",
        "rationale": "Must reject on the functional pin "
                     "Ensures(ToSeq(Result().columns) == own_columns(ToSeq("
                     "outer_select), ToSeq(cached.leading), ToSeq(cached.trailing)"
                     ")): the oracle is a function of the SHARED sub-query's "
                     "UN-NARROWED families, which only a single application to a "
                     "faithful copy reaches. Measured on the real callee (G-AX leg "
                     "F): 984 of 984 shapes show a second application never "
                     "reaching the pinned outcome, so the rejection is not a "
                     "spec-too-strong artifact.",
    },
    {
        "id": "cfs-narrow-then-full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_NARROW_THEN_FULL),
        "refinement": "The AUDITED counterexample VERBATIM (verdict.md WITNESS "
                      "atk_12.py): narrow the working object to the LAST chosen "
                      "column first, THEN apply the full chosen list. The earlier "
                      "revision of this spec pinned the working object's own columns "
                      "to the chosen list UNCONDITIONALLY, which the second call "
                      "satisfies, so the first call looked like dead code and the "
                      "rival VERIFIED — yet its patch does NOT resolve the instance: "
                      "FAIL_TO_PASS passes 1/1 but PASS_TO_PASS fails 2/23 "
                      "(queries.test_qs_combinators.QuerySetSetOperationTests."
                      "test_union_with_extra_and_values_list and "
                      "test_union_with_two_annotated_values_list). In the real callee "
                      "the first call is NOT dead: set_values narrows the extra and "
                      "annotation select masks to that single name, so the second "
                      "call classifies against the narrowed families and misfiles "
                      "every other requested derived-column name as one of the "
                      "query's own. Note the ORDER matters as a control: with the "
                      "applications reversed (cfs-double-application) the earlier "
                      "spec would already have rejected the rival, so only this order "
                      "witnesses the hole the repair closed.",
        "rationale": "Must reject on the functional pin "
                     "Ensures(ToSeq(Result().columns) == own_columns(ToSeq("
                     "outer_select), ToSeq(cached.leading), ToSeq(cached.trailing)"
                     ")) — measured directly: the rival now fails verification at "
                     "exactly that clause. The repaired oracle is a function of the "
                     "SHARED sub-query's UN-NARROWED families, so the narrowing done "
                     "by the first application can no longer be treated as "
                     "unobservable. G-AX leg F measures the same fact on the real "
                     "callee (984 of 984 shapes), so this is a behavioural "
                     "distinction, not a spec-too-strong artifact.",
    },
    {
        "id": "cfs-no-apply",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_NO_APPLY),
        "refinement": "Copies the shared sub-query (detached_copy) but FORGETS to "
                      "apply the chosen column list. Faithful real patch: add the "
                      "per-compilation copy but DROP the applying call -> the copied "
                      "sub-query keeps the shared one's empty own column list and "
                      "un-narrowed derived families, so the compound query renders "
                      "the wrong/default columns -> F2P test_union_with_values fails "
                      "(values_list('order') would not yield (2,)).",
        "rationale": "Satisfies the aliasing-break clauses (cached untouched; "
                     "Result distinct object with distinct containers; state "
                     "carried) but VIOLATES the functional pin "
                     "Ensures(ToSeq(Result().columns) == own_columns(...)): the "
                     "copy keeps cached's empty own column list (len 0 by "
                     "precondition) while the chosen list is non-empty (len>0) and "
                     "need not name a derived column.",
    },
    {
        "id": "cfs-verbatim-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_VERBATIM),
        "refinement": "Copies the shared sub-query and then writes the chosen list "
                      "VERBATIM onto the working object's own column list, leaving "
                      "both derived families un-narrowed. This is the behaviour an "
                      "unconditional 'the sub-query's own columns become the chosen "
                      "list' reading licenses. The real callee only behaves that "
                      "way on its shortcut path (a sub-query exposing NO derived "
                      "columns); otherwise it partitions the requested names and "
                      "narrows both families. Faithful real patch: apply the list "
                      "without consulting the derived columns -> names resolving to "
                      "a derived column are emitted twice and un-requested derived "
                      "columns are still emitted.",
        "rationale": "Rejected by the classification clauses: "
                     "Ensures(ToSeq(Result().columns) == own_columns(ToSeq("
                     "outer_select), ToSeq(cached.leading), ToSeq(cached.trailing))) "
                     "fails as soon as a requested name is one of the shared "
                     "sub-query's derived columns, and the two family clauses fail "
                     "as soon as a derived column is not requested.",
    },
    {
        "id": "cfs-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_POS),
        "rationale": "A structurally-different but CORRECT impl: chains TWO "
                     "per-compilation copies (a harmless extra copy) before "
                     "applying the chosen list. Satisfies every load-bearing clause "
                     "(cached untouched at len 0 with both families un-narrowed and "
                     "its state; distinct object; three distinct containers; the "
                     "three classification equalities, since the extra copy "
                     "preserves both families exactly; state token carried through "
                     "both copies). Must verify; a failure would be "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "cfs-admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_CFS, _CFS_ADMISS),
        "rationale": "Asserts the precondition's own facts on the incoming "
                     "F2P-shaped input (empty shared column list; non-empty chosen "
                     "list; both derived families readable at any length; "
                     "unconstrained state) before delegating exactly as the gold "
                     "does, confirming the precondition admits a normal input and "
                     "does not secretly force the derived families to be empty. A "
                     "failure would be PRECOND-TOO-STRONG. (No literal self-call: "
                     "the termination measure correctly forbids same-measure "
                     "recursion.)",
    },

    # ---------------- detached_copy (deep model of the per-compilation copy) ----------------
    {
        "id": "dc-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_DC, _DC_FRAME),
        "refinement": "Mutates the read-only original q.columns (append) and wraps "
                      "it. A faithful real patch where the copy operation mutated "
                      "the SOURCE query's column list would corrupt the shared "
                      "sub-query the copy is meant to leave pristine — the exact "
                      "aliasing the fix relies on NOT happening — so the regression "
                      "persists.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: q.columns is held at "
                     "Acc(q.columns, 1/4) / Acc(list_pred(q.columns), 1/4) "
                     "(read-only); .append needs full permission. Attributable to "
                     "the write on the read-only original.",
    },
    {
        "id": "dc-alias-not-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_DC, _DC_ALIAS),
        "refinement": "Wraps q's OWN three containers in the new Query (aliases, "
                      "not copies): the contents match but Result().columns IS "
                      "q.columns and likewise for both derived families. Faithful "
                      "real patch: a shallow alias of the sub-query's containers "
                      "rather than independent copies -> applying a column list to "
                      "the 'copy' narrows the shared sub-query's families too -> "
                      "the regression persists -> F2P fails.",
        "rationale": "Rejected by the permission system (the constructor requires "
                     "the full lists while q's are held at 1/4) and by "
                     "Ensures(Result().columns is not q.columns) plus the two "
                     "family container clauses: the detached-copy contract requires "
                     "INDEPENDENT containers, but this rival shares the "
                     "original's.",
    },
    {
        "id": "dc-state-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_DC, _DC_STATE_DROP),
        "refinement": "Copies all three column families faithfully but constructs "
                      "the new object with a DEFAULT state token instead of the "
                      "original's. Faithful real patch: a copy that rebuilds the "
                      "query from scratch keeping only the column selection -> the "
                      "accumulated filters and derived-column definitions are lost "
                      "-> wrong rows on the sibling P2P tests.",
        "rationale": "Rejected by Ensures(Result().state == q.state): any "
                     "q.state != 0 is a counterexample. This pins the deep model "
                     "to carrying the WHOLE abstracted state, not just the column "
                     "selection.",
    },
    {
        "id": "dc-drop-leading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_DC, _DC_DROP_LEADING),
        "refinement": "Copies the own columns and the trailing derived family but "
                      "gives the new object an EMPTY leading family. Faithful real "
                      "patch: a copy operation that forgets one of the two "
                      "derived-column families -> the component sub-query stops "
                      "emitting the columns the compound query is about to ask for, "
                      "and every requested name that resolved to one is then taken "
                      "for one of the sub-query's own columns.",
        "rationale": "Rejected by Ensures(ToSeq(Result().leading) == "
                     "ToSeq(q.leading)): any non-empty q.leading is a "
                     "counterexample. Pins the derived-column facets of the deep "
                     "model, which the classification in with_columns reads.",
    },
    {
        "id": "dc-swap-families",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_DC, _DC_SWAP_FAMILIES),
        "refinement": "Copies both derived families into each other's slot. Every "
                      "container is independent and every element survives; only "
                      "WHICH family each belongs to is exchanged. The two families "
                      "are not interchangeable: they are rendered on opposite sides "
                      "of the sub-query's own columns and the leading one is "
                      "consulted FIRST when a requested name is classified. "
                      "Faithful real patch: a copy that conflates the two families "
                      "-> the rendered column order changes and a name exposed by "
                      "both is served by the wrong one.",
        "rationale": "Rejected by Ensures(ToSeq(Result().leading) == "
                     "ToSeq(q.leading)) and Ensures(ToSeq(Result().trailing) == "
                     "ToSeq(q.trailing)): any q where the two families differ is a "
                     "counterexample.",
    },
    {
        "id": "dc-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_DC, _DC_POS),
        "rationale": "A structurally-different but CORRECT impl: hoists the "
                     "own-column length into a local bound `n`, drives the first "
                     "copy loop off `n`, and rebases that loop's invariant and "
                     "termination measure on it. Must verify; a failure would be "
                     "SPEC-TOO-STRONG.",
    },

    # ---------------- with_columns (deep model of applying a chosen list) ----------------
    {
        "id": "wc-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_WC, _WC_FRAME_FIELDS),
        "refinement": "Mutates the read-only `fields` input (append) before the "
                      "gold body runs. A faithful real patch where applying a "
                      "column list mutated its argument would corrupt the OUTER "
                      "query's chosen list, which is shared across the compiler's "
                      "loop over the component sub-queries, so a later component "
                      "would be given a different list than the caller asked for.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: `fields` is held at "
                     "Acc(list_pred(fields), 1/2); .append needs full permission. "
                     "It also breaks Ensures(ToSeq(fields) == Old(ToSeq(fields))). "
                     "Attributable to the write on the read-only argument, not to a "
                     "classification mismatch (the gold body is kept verbatim).",
    },
    {
        "id": "wc-state-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_WC, _WC_STATE_CLOBBER),
        "refinement": "Applies the column list correctly but then wipes the query's "
                      "accumulated state token. Faithful real patch: an applying "
                      "step that resets the query's filters or its derived-column "
                      "definitions -> wrong rows even though the rendered columns "
                      "are right.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: q.state is held at "
                     "Acc(q.state, 1/2) (read-only); the write needs full "
                     "permission. Also contradicts Ensures(q.state == "
                     "Old(q.state)). Defends the state facet of the deep model.",
    },
    {
        "id": "wc-verbatim-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_WC, _WC_VERBATIM),
        "refinement": "*** The load-bearing mis-classification case. *** Sets the "
                      "query's own columns to a copy of the WHOLE chosen list and "
                      "leaves both derived families untouched. The real callee only "
                      "behaves that way on its shortcut path (a query exposing no "
                      "derived columns at all); otherwise it PARTITIONS the "
                      "requested names — a name resolving to a derived column is "
                      "served by that column and does NOT become one of the query's "
                      "own — and it narrows both families to the requested ones. "
                      "Faithful real patch: apply the list without consulting the "
                      "derived columns -> names resolving to an extra/annotation "
                      "entry are emitted twice and un-requested derived columns are "
                      "still emitted, so the two sides of a UNION disagree on their "
                      "column list.",
        "rationale": "Rejected by all three classification clauses: "
                     "Ensures(ToSeq(q.columns) == own_columns(ToSeq(fields), "
                     "Old(ToSeq(q.leading)), Old(ToSeq(q.trailing)))) fails as soon "
                     "as a requested name is a derived column, and the two family "
                     "clauses fail as soon as a derived column is not requested. "
                     "This case is what forbids the unconditional reading of the "
                     "operation.",
    },
    {
        "id": "wc-keep-unrequested-leading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_WC, _WC_KEEP_LEADING),
        "refinement": "Computes the own-column partition exactly as the gold does "
                      "but leaves the LEADING family un-narrowed (every leading "
                      "derived column is kept, requested or not). Faithful real "
                      "patch: apply the list but never restrict the derived columns "
                      "the sub-query goes on to expose -> the component emits "
                      "derived columns the compound query did not ask for, so the "
                      "two sides of a UNION disagree on their column count.",
        "rationale": "The narrowing half of the obligation ISOLATED to one clause: "
                     "Ensures(ToSeq(q.leading) == kept_leading(Old(ToSeq("
                     "q.leading)), ToSeq(fields))) fails for any leading derived "
                     "column that was not requested, while the own-column and "
                     "trailing clauses still hold.",
    },
    {
        "id": "wc-no-leading-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_WC, _WC_NO_PRECEDENCE),
        "refinement": "Narrows the two derived families INDEPENDENTLY, dropping the "
                      "rule that a requested name exposed by both is claimed by the "
                      "leading family first. Faithful real patch: partition the "
                      "requested names against each family separately -> a name "
                      "exposed by both is emitted twice, once on each side of the "
                      "sub-query's own columns. Validated against the real callee "
                      "(G-AX leg D): a name defined as BOTH an extra_select and an "
                      "annotation_select entry is served by the extra one only.",
        "rationale": "Rejected by Ensures(ToSeq(q.trailing) == "
                     "kept_trailing(Old(ToSeq(q.trailing)), ToSeq(fields), "
                     "Old(ToSeq(q.leading)))). The loop invariants are rebased on "
                     "an empty leading argument so the rival's own proof "
                     "discharges and the rejection lands on the POSTCONDITION, "
                     "attributable to the precedence rule itself.",
    },
    {
        "id": "wc-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_WC, _WC_DROP_LAST),
        "refinement": "The own-column loop stops one entry short (k + 1 < len). "
                      "Faithful real patch: an applying step that loses the last "
                      "requested column -> the compound query renders one fewer "
                      "column than the values_list asked for -> F2P (and any P2P "
                      "selecting the dropped column) fails.",
        "rationale": "Rejected by Ensures(ToSeq(q.columns) == own_columns(...)): "
                     "the computed list is own_columns(fields.take(len-1), ...), "
                     "one short whenever the last requested name is not one of the "
                     "query's derived columns.",
    },
    {
        "id": "wc-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_WC, _WC_POS),
        "rationale": "A structurally-different but CORRECT impl: inverts BOTH "
                     "derived-family guards into if/else form (the empty branch "
                     "asserting the negated condition), so the classification "
                     "decisions are taken in the opposite syntactic order while the "
                     "computed families are identical and q.state is never touched. "
                     "Must verify; a failure would be SPEC-TOO-STRONG.",
    },
    {
        "id": "wc-admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_WC, _WC_ADMISS),
        "rationale": "Requires(len(fields) > 0) is the domain restriction the "
                     "empty-chosen-list divergence forces (on the real callee an "
                     "empty list selects every concrete column of the query's own "
                     "table and narrows nothing — a different operation; see the "
                     "containment probe). This case asserts that fact, plus the "
                     "absence of any constraint on the two derived families, before "
                     "running the gold body: the precondition admits a chosen list "
                     "of any positive length applied to a query exposing any number "
                     "of derived columns. A failure would be PRECOND-TOO-STRONG.",
    },
]


# ============================ AXIOM lane ============================
# No @ContractOnly axioms (meta.axioms == []). The two helpers are A-reference deep
# models of UNCHANGED real Django callees the gold patch invokes:
#   detached_copy  <-> django.db.models.sql.query.Query.clone()
#   with_columns   <-> django.db.models.sql.query.Query.set_values()
# These probes RUN THE REAL CALLEES in the instance image (gold patch applied) and
# assert the deep models' load-bearing properties — the classification and
# narrowing equalities on PRISTINE and on ALREADY-NARROWED shapes, the
# accumulated-state preservation the `state` token abstracts, and the
# caller-domain containment (including the empty-chosen-list divergence that
# justifies the len(fields) > 0 precondition).
# The probe logic mirrors the bundle's own axiom_check.py (G-AX); it imports only
# Django + the stdlib, opens nothing on disk, and exits 0 iff every obligation holds.

# Shared Django setup + minimal model + executable transcriptions of the model's
# @Pure functions, embedded into each probe string (the runner mounts ONLY the
# probe at /work; model.py/axiom_check.py are NOT in-container).
_PROBE_SETUP = r'''
import itertools, os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )
django.setup()
from django.db import connection, models
from django.db.models import Q, Value, IntegerField
from django.core.exceptions import FieldError
from django.db.models.sql.query import Query

class Reserved(models.Model):
    name = models.CharField(max_length=32)
    order = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as editor:
    editor.create_model(Reserved)

OWN_FIELDS = ["name", "order"]
EXTRA_SQL = {"e1": "1+1", "e2": "2+2"}
ANNOT_VAL = {"a1": 3, "a2": 4}

# Under the mapping (mapping.md S1) a modelled Query carries
#   columns  <-> the ordered keys of values_select
#   leading  <-> the ordered keys of extra_select      (rendered first, and
#                consulted FIRST when a requested name is classified)
#   trailing <-> the ordered keys of annotation_select (rendered last)
#   state    <-> the where clause together with the extra/annotations DEFINITION
#                dicts, abstracted to one opaque token
def build(extra_keys, annot_keys, where=True):
    q = Query(Reserved)
    if where:
        q.add_q(Q(order__gt=1))
    for k in extra_keys:
        q.add_extra({k: EXTRA_SQL[k]}, None, None, None, None, None)
    for k in annot_keys:
        q.add_annotation(Value(ANNOT_VAL[k], output_field=IntegerField()), k)
    return q

def requests(pool, sizes=(1, 2, 3)):
    out, seen = [], set()
    for n in sizes:
        for c in itertools.permutations(pool, min(n, len(pool))):
            if c not in seen:
                seen.add(c)
                out.append(list(c))
    return out

# executable transcriptions of the model's back-recursive @Pure functions: each
# is exactly the order-preserving filter below, by induction on the length of the
# recursed-on sequence.
def own_columns(fields, leading, trailing):
    return [f for f in fields if f not in leading and f not in trailing]

def kept_leading(leading, fields):
    return [x for x in leading if x in fields]

def kept_trailing(trailing, fields, leading):
    return [x for x in trailing if x in fields and x not in leading]
'''


_PROBE_SETVALUES = _PROBE_SETUP + r'''
# AXIOM-SOUNDNESS for with_columns <-> Query.set_values().
# Load-bearing deep-model obligations (model.py with_columns Ensures):
#   ToSeq(q.columns)  == own_columns(fields, Old(leading), Old(trailing))
#   ToSeq(q.leading)  == kept_leading(Old(leading), fields)
#   ToSeq(q.trailing) == kept_trailing(Old(trailing), fields, Old(leading))
#   q.state == Old(q.state)   (where clause and BOTH definition dicts survive)
# Checked on the PRISTINE shape the compilation actually meets AND on an
# ALREADY-NARROWED query, so the model is pinned off the gold path too: after one
# application the exposed derived columns are narrowed, so a name that WAS derived
# is no longer classified as derived. The model says exactly that; the real callee
# must agree, or reject the request outright (the name is then taken for one of the
# query's own columns and the table has no such column).
violations = 0
checked = 0
assertions = 0

def check_application(q, req, tag):
    global violations, assertions
    pre_leading = list(q.extra_select)
    pre_trailing = list(q.annotation_select)
    pre_extra = dict(q.extra)
    pre_annot = set(q.annotations)
    pre_where = len(q.where.children)
    q.set_values(tuple(req))                       # REAL Query.set_values()
    exp_own = own_columns(req, pre_leading, pre_trailing)
    exp_lead = kept_leading(pre_leading, req)
    exp_trail = kept_trailing(pre_trailing, req, pre_leading)
    if list(q.values_select) != exp_own:
        print("VIOLATION %s: set_values(%r) on leading=%r trailing=%r gave "
              "values_select %r, model own_columns says %r"
              % (tag, req, pre_leading, pre_trailing, list(q.values_select), exp_own))
        violations += 1
    if list(q.extra_select) != exp_lead:
        print("VIOLATION %s: set_values(%r) left extra_select %r, model "
              "kept_leading says %r" % (tag, req, list(q.extra_select), exp_lead))
        violations += 1
    if list(q.annotation_select) != exp_trail:
        print("VIOLATION %s: set_values(%r) left annotation_select %r, model "
              "kept_trailing says %r"
              % (tag, req, list(q.annotation_select), exp_trail))
        violations += 1
    if dict(q.extra) != pre_extra or set(q.annotations) != pre_annot:
        print("VIOLATION %s: set_values disturbed the derived-column definitions" % tag)
        violations += 1
    if len(q.where.children) != pre_where:
        print("VIOLATION %s: set_values disturbed the accumulated row restriction" % tag)
        violations += 1
    assertions += 5

# leg A: pristine shapes -- every combination of exposed families x every
# ordered request of up to three names drawn from own + derived columns.
for eks in [[], ["e1"], ["e2"], ["e1", "e2"], ["e2", "e1"]]:
    for aks in [[], ["a1"], ["a1", "a2"], ["a2", "a1"]]:
        for req in requests(OWN_FIELDS + list(eks) + list(aks)):
            check_application(build(eks, aks), req, "pristine")
            checked += 1
leg_a = checked

# leg B: the same three equalities on an ALREADY-NARROWED query.
narrowed = 0
rejected = 0
for eks in (["e1", "e2"], ["e1"]):
    for aks in (["a1", "a2"], ["a1"]):
        pool = OWN_FIELDS + list(eks) + list(aks)
        for first in itertools.permutations(pool, 2):
            for second in itertools.permutations(pool, 2):
                q = build(eks, aks)
                q.set_values(tuple(first))
                try:
                    check_application(q, list(second), "narrowed")
                except FieldError:
                    # a narrowed-away name became an own column the table cannot
                    # serve: outside the modelled domain, and still NOT the
                    # outcome a single application would give.
                    rejected += 1
                narrowed += 1
                checked += 1

# leg D: a name exposed by BOTH families -> the leading one wins (the precedence
# rule the wc-no-leading-precedence case pins).
q = Query(Reserved)
q.add_extra({"x": "1+1"}, None, None, None, None, None)
q.add_annotation(Value(9, output_field=IntegerField()), "x")
check_application(q, ["x"], "collision")
checked += 1

if checked == 0 or assertions == 0 or leg_a == 0 or narrowed == 0:
    print("PROBE FAIL: no obligations executed"); sys.exit(1)
if violations:
    print("AXIOM-UNSOUND: %d violation(s) over %d shapes" % (violations, checked)); sys.exit(1)
print("OK: with_columns<->Query.set_values() sound over %d shapes (%d assertions): "
      "the classification/narrowing equalities (own_columns / kept_leading / "
      "kept_trailing) hold on %d pristine shapes AND on %d already-narrowed ones "
      "(%d of those the callee rejects outright); a name exposed by both families "
      "is claimed by the leading one; and the where clause and both "
      "derived-column definition dicts survive every application."
      % (checked, assertions, leg_a, narrowed, rejected))
sys.exit(0)
'''


_PROBE_CLONE = _PROBE_SETUP + r'''
# AXIOM-SOUNDNESS for detached_copy <-> Query.clone().
# Load-bearing deep-model obligations (model.py detached_copy Ensures):
#   (B) Result() is not q                        -> a DISTINCT object
#   (C) the three containers are each independent -> incl. independent narrowing
#       masks, so applying a list to the copy cannot narrow the original
#   (D) all three sequences copied                -> values_select, extra_select
#       and annotation_select mirror the original
#   (E) Result().state == q.state                 -> the copy CARRIES the where
#       clause and both derived-column definition dicts; a fresh Query does not
#   (q untouched)                                 -> a later application on the
#       copy leaves the original's own column list AND both of its UN-NARROWED
#       families pristine (model.py clause (2), what lets a later compilation
#       choose a different list)
violations = 0
checked = 0

for eks in [[], ["e1"], ["e1", "e2"], ["e2", "e1"]]:
    for aks in [[], ["a1"], ["a1", "a2"]]:
        q = build(eks, aks)
        lead_before = list(q.extra_select)
        trail_before = list(q.annotation_select)
        own_before = tuple(q.values_select)
        where_before = len(q.where.children)
        extra_before = dict(q.extra)
        annot_before = set(q.annotations)
        c = q.clone()                                   # REAL Query.clone()
        if c is q:
            print("VIOLATION: clone() returned the same object for %r/%r" % (eks, aks)); violations += 1
        if c.extra is q.extra or c.annotations is q.annotations:
            print("VIOLATION: clone() shares a definition container for %r/%r" % (eks, aks)); violations += 1
        if tuple(c.values_select) != own_before:
            print("VIOLATION: clone() values_select %r != original %r"
                  % (c.values_select, own_before)); violations += 1
        if list(c.extra_select) != lead_before:
            print("VIOLATION: clone() lost the leading family: %r != %r"
                  % (list(c.extra_select), lead_before)); violations += 1
        if list(c.annotation_select) != trail_before:
            print("VIOLATION: clone() lost the trailing family: %r != %r"
                  % (list(c.annotation_select), trail_before)); violations += 1
        if len(c.where.children) != where_before:
            print("VIOLATION: clone() lost the accumulated row restriction"); violations += 1
        if dict(c.extra) != extra_before or set(c.annotations) != annot_before:
            print("VIOLATION: clone() lost the derived-column definitions"); violations += 1
        # applying a column list to the copy must leave the ORIGINAL pristine,
        # in particular its families UN-NARROWED.
        req = OWN_FIELDS + list(eks) + list(aks)
        c.set_values(tuple(req))                        # REAL set_values()
        if tuple(q.values_select) != own_before:
            print("VIOLATION: set_values on the copy leaked into the shared "
                  "sub-query: %r -> %r" % (own_before, q.values_select)); violations += 1
        if list(q.extra_select) != lead_before or list(q.annotation_select) != trail_before:
            print("VIOLATION: set_values on the copy narrowed the shared "
                  "sub-query's derived families: %r/%r != %r/%r"
                  % (list(q.extra_select), list(q.annotation_select),
                     lead_before, trail_before)); violations += 1
        if len(q.where.children) != where_before or dict(q.extra) != extra_before:
            print("VIOLATION: set_values on the copy disturbed the original's state"); violations += 1
        checked += 1

# a brand-new Query does NOT carry that state: the blank-slate shape the model's
# state pin rejects is genuinely different from a copy.
stateful = build(["e1"], ["a1"])
blank = Query(Reserved)
if len(blank.where.children) == len(stateful.where.children) and stateful.where.children:
    print("VIOLATION: a fresh Query unexpectedly carries the row restriction"); violations += 1
if blank.extra or blank.annotations:
    print("VIOLATION: a fresh Query unexpectedly carries the derived-column definitions"); violations += 1
# and the narrowing masks are independent across clone()
s2 = stateful.clone()
s2.set_values(("name",))
if stateful.extra_select_mask is not None or s2.extra_select_mask is None:
    print("VIOLATION: the narrowing masks are not independent across clone()"); violations += 1
checked += 1

if checked == 0:
    print("PROBE FAIL: no obligations executed"); sys.exit(1)
if violations:
    print("AXIOM-UNSOUND: %d violation(s) over %d cases" % (violations, checked)); sys.exit(1)
print("OK: detached_copy<->Query.clone() sound over %d shapes: a distinct object "
      "with independent containers and independent narrowing masks, all three "
      "column families copied, the where/extra/annotation state carried (which a "
      "fresh Query does not carry), and the original never mutated -- in "
      "particular never narrowed -- by a later application on the copy." % checked)
sys.exit(0)
'''


_PROBE_CONTAINMENT = _PROBE_SETUP + r'''
# AXIOM-CONTAINMENT: every callee-input the MODEL can reach lies in the real
# callee's accepted domain, and the model's domain RESTRICTION is justified.
#  - detached_copy reaches Query.clone() on the shared sub-query whose model
#    `columns` is EMPTY (precondition len(cached.columns)==0), exposing any
#    number of derived columns, in any accumulated state, and the double-copy
#    positive control also clones a clone.
#  - with_columns reaches Query.set_values() with a NON-EMPTY chosen list whose
#    names are the sub-query's own columns and/or the derived columns it exposes.
#  - The EMPTY chosen list is excluded by precondition (len(fields) > 0). That
#    exclusion must be JUSTIFIED, not assumed: the probe records that the real
#    callee treats an empty list as a DIFFERENT operation (it selects every
#    concrete column of the query's own table and narrows nothing), so a model
#    claiming the non-empty behaviour there would be unsound.
# This is a containment check (the caller's reachable inputs are IN the domain),
# NOT a demand that the callee's whole domain be covered.
violations = 0
checked = 0

# (1) clone() on every reachable shared-sub-query shape, and on a clone-of-clone.
for eks in [[], ["e1"], ["e1", "e2"]]:
    for aks in [[], ["a1"], ["a1", "a2"]]:
        for where in (True, False):
            q = build(eks, aks, where=where)
            try:
                c = q.clone()
                _ = (tuple(c.values_select), list(c.extra_select),
                     list(c.annotation_select))
                cc = c.clone()                  # clone of a clone (double-copy)
                _ = tuple(cc.values_select)
            except Exception as e:
                print("VIOLATION: clone() rejected a caller-reachable state "
                      "%r/%r/where=%r: %r" % (eks, aks, where, e)); violations += 1
            checked += 1

# (2) set_values() on the non-empty chosen lists the caller can pass: names drawn
#     from the sub-query's own columns and the derived columns it exposes.
for eks in [[], ["e1"], ["e1", "e2"]]:
    for aks in [[], ["a1"]]:
        pool = OWN_FIELDS + list(eks) + list(aks)
        for req in requests(pool):
            q = build(eks, aks)
            try:
                q.set_values(tuple(req))
                # codomain: the outcome is the model's classification, and every
                # requested name is served by exactly one family.
                served = (list(q.values_select) + list(q.extra_select)
                          + list(q.annotation_select))
                if sorted(served) != sorted(set(req)):
                    print("VIOLATION: set_values(%r) on %r/%r served %r"
                          % (req, eks, aks, served)); violations += 1
            except Exception as e:
                print("VIOLATION: set_values() rejected a caller-reachable chosen "
                      "list %r on %r/%r: %r" % (req, eks, aks, e)); violations += 1
            checked += 1

# (3) the EXCLUDED input: an empty chosen list is a different operation, which is
#     why the model restricts the domain instead of claiming it.
q = build(["e1"], ["a1"])
pre_lead, pre_trail = list(q.extra_select), list(q.annotation_select)
q.set_values(())
if (list(q.values_select) == [] and list(q.extra_select) == []
        and list(q.annotation_select) == []):
    print("VIOLATION: an empty chosen list behaved like the non-empty case; the "
          "len(fields) > 0 precondition would then be gratuitous"); violations += 1
if list(q.extra_select) != pre_lead or list(q.annotation_select) != pre_trail:
    print("VIOLATION: an empty chosen list unexpectedly narrowed the derived "
          "columns"); violations += 1
checked += 1

if checked == 0:
    print("PROBE FAIL: no obligations executed"); sys.exit(1)
if violations:
    print("AXIOM-TOO-WEAK-FOR-CALLER: %d reachable input(s) outside the callee "
          "domain" % violations); sys.exit(1)
print("OK: every caller-reachable input lies in the real callees' accepted domain "
      "over %d cases (clone() on any exposed-derived-column shape in any "
      "accumulated state, and on a clone-of-a-clone; set_values() on every "
      "non-empty chosen list drawn from the sub-query's own and derived columns, "
      "each requested name served by exactly one family), and the EXCLUDED empty "
      "chosen list is confirmed to be a different operation -- which is what "
      "justifies the len(fields) > 0 precondition." % checked)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-clone-soundness",
        "axiom": "detached_copy",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_CLONE,
        "rationale": "Runs the REAL django.db.models.sql.query.Query.clone() over "
                     "every reachable shared-sub-query shape (any combination of "
                     "exposed extra_select / annotation_select entries, with and "
                     "without an accumulated row restriction). Asserts clone() "
                     "returns a distinct object with independent containers and "
                     "independent narrowing masks, copies all three column "
                     "families, CARRIES the where/extra/annotation state (the "
                     "model's Result().state == q.state pin) where a fresh Query "
                     "does not, and is never mutated -- never narrowed -- by a "
                     "later set_values on the copy (the aliasing break, model.py "
                     "clause (2)). A violation => AXIOM-UNSOUND (the detached_copy "
                     "deep model claims more than the real clone()).",
    },
    {
        "id": "ax-setvalues-soundness",
        "axiom": "with_columns",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SETVALUES,
        "rationale": "Runs the REAL Query.set_values() and asserts the model's "
                     "three classification/narrowing equalities (own_columns, "
                     "kept_leading, kept_trailing) plus state preservation, on "
                     "PRISTINE shapes and on ALREADY-NARROWED queries, and on a "
                     "name exposed by BOTH derived families (the leading-wins "
                     "precedence). The already-narrowed leg is what pins the model "
                     "OFF the gold path: it is why applying a chosen list twice "
                     "cannot reach the specified outcome. A violation => "
                     "AXIOM-UNSOUND (the with_columns deep model claims more than "
                     "the real set_values()).",
    },
    {
        "id": "ax-containment",
        "axiom": "detached_copy+with_columns",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "Enumerates EXACTLY the callee inputs the model can reach "
                     "(clone() on any exposed-derived-column shape in any "
                     "accumulated state and on a clone-of-a-clone; set_values() on "
                     "every non-empty chosen list drawn from the sub-query's own "
                     "and derived columns) and asserts each lies in the real "
                     "callees' accepted domain with every requested name served by "
                     "exactly one family. It also JUSTIFIES the model's domain "
                     "restriction: the excluded empty chosen list is confirmed to "
                     "be a different operation on the real callee. A reachable "
                     "input the callee rejects => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
