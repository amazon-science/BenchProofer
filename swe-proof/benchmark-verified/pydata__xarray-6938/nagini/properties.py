# properties.py — PBT manifest for pydata__xarray-6938.
#
# NOT a Nagini module: a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec exactly (same_spec) and swap ONLY
# the text inside an # impl-start/# impl-end region; each is checked by Nagini
# verify on the host. Axiom cases are real-callee probes run in Docker.
#
# ---------------------------------------------------------------------------
# Defended surface (adversarially reasoned, per the battery-authoring brief)
# ---------------------------------------------------------------------------
# This instance fixes xarray issue #6931: `IndexVariable.to_index_variable`
# returned `self` (an ALIAS), so `Dataset.swap_dims` -- which does
# `var = v.to_index_variable(); var.dims = dims` -- corrupted the source object.
# The gold patch changes `return self` -> `return self.copy()` (a fresh
# allocation). The F2P `test_to_index_variable_copy` asserts `a is not b` and
# that reassigning `b.dims` leaves `a.dims` unchanged.
#
# There are NO @ContractOnly axioms and NO @Pure answer-key oracle: the changed
# behaviour (alias -> independent copy) is modelled DEEPLY via Nagini's
# permission discipline. So AXIOM_TESTS = [] and there is no ungrounded-oracle
# echo to build (see 'assessment'); the whole defended surface is the
# permission/identity/value postcondition triple on the three modeled functions:
#
#   as_coordinate / independent_clone / as_plain each take the receiver
#   READ-ONLY: Requires(Acc(self.dims, 1/2)) + Requires(Acc(list_pred(self.dims),1/2)),
#   carry a MustTerminate obligation (total correctness: a diverging
#   re-presentation would satisfy the value clauses only vacuously and hang
#   the swap_dims caller -- the audit's atk_5 nontermination rival),
#   and Ensure a DISTINCT result with FULL write permission to its own dims:
#     Acc(Result().dims)                  -- full write perm on result storage
#     Acc(list_pred(Result().dims))       -- full perm on result list
#     Result() is not self                -- distinct object
#     Result().dims is not self.dims      -- distinct storage (the swap_dims fix)
#     ToSeq(Result().dims) == ToSeq(self.dims)   -- carries receiver's names
#     ToSeq(self.dims) == Old(ToSeq(self.dims))  -- receiver survives unchanged
#
# The load-bearing arithmetic: an aliasing result (`return self`) keeps the
# receiver's retained 1/2 read permission AND would need full (1) write
# permission on Result().dims == self.dims => 3/2 > 1 => insufficient permission
# (and `Result() is not self` is also false). That single postcondition triple
# is what every uniqueness rival below attacks.

from pathlib import Path

INSTANCE = "pydata__xarray-6938"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors -- every edit below targets text strictly INSIDE an
# # impl-start/# impl-end region, so spec_view (and hence same_spec) is
# untouched.  The three impl bodies, verbatim, used as _swap anchors:
# ---------------------------------------------------------------------------

# as_coordinate impl body (delegates to independent_clone)
_AS_COORD_IMPL = """    # impl-start
    return independent_clone(self)
    # impl-end"""

# as_plain impl body (element-copy loop)
_AS_PLAIN_IMPL = """    # impl-start
    base_dims = []  # type: List[int]
    j = 0
    while j < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(base_dims)))
        Invariant(0 <= j and j <= len(self.dims))
        Invariant(ToSeq(base_dims) == ToSeq(self.dims).take(j))
        # strictly decreasing measure discharges MustTerminate(4).
        Invariant(MustTerminate(len(self.dims) - j + 1))
        # invariants-end
        base_dims.append(self.dims[j])
        j = j + 1
    Assert(ToSeq(self.dims).take(len(self.dims)) == ToSeq(self.dims))
    return CoordVar(base_dims)
    # impl-end"""

# independent_clone impl body (the deep copy primitive)
_CLONE_IMPL = """    # impl-start
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 0
    while i < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(new_dims)))
        Invariant(ToSeq(self.dims) == s_old)
        Invariant(0 <= i and i <= len(s_old))
        Invariant(ToSeq(new_dims) == s_old.take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure, discharging MustTerminate(2).
        Invariant(MustTerminate(len(self.dims) - i + 1))
        # invariants-end
        new_dims.append(self.dims[i])
        i = i + 1
    Assert(i == len(s_old))
    Assert(s_old.take(len(s_old)) == s_old)
    Assert(ToSeq(new_dims) == s_old)
    res = CoordVar(new_dims)
    Assert(ToSeq(res.dims) == s_old)
    Assert(ToSeq(self.dims) == s_old)
    Assert(ToSeq(res.dims) == ToSeq(self.dims))
    return res
    # impl-end"""


SPEC_TESTS = [
    # =====================================================================
    # 1. POSITIVE CONTROL (soundness) -- a structurally-DIFFERENT but CORRECT
    #    independent_clone that MUST verify.  Reshape: introduce an extra local
    #    `cur` for the read element and a redundant length local, and reorder
    #    the trailing asserts.  The gold loop invariants + framing asserts are
    #    KEPT verbatim (per pilot bug #2/#3: never drop a framing assert, never
    #    flip the loop direction against the front-recursive take() invariant).
    #    If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-clone-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _CLONE_IMPL,
            """    # impl-start
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 0
    while i < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(new_dims)))
        Invariant(ToSeq(self.dims) == s_old)
        Invariant(0 <= i and i <= len(s_old))
        Invariant(ToSeq(new_dims) == s_old.take(i))
        # strictly decreasing measure discharges MustTerminate(2).
        Invariant(MustTerminate(len(self.dims) - i + 1))
        # invariants-end
        cur = self.dims[i]  # type: int
        new_dims.append(cur)
        i = i + 1
    Assert(s_old.take(len(s_old)) == s_old)
    Assert(i == len(s_old))
    Assert(ToSeq(new_dims) == s_old)
    res = CoordVar(new_dims)
    Assert(ToSeq(self.dims) == s_old)
    Assert(ToSeq(res.dims) == s_old)
    Assert(ToSeq(res.dims) == ToSeq(self.dims))
    return res
    # impl-end""",
        ),
        "rationale": (
            "Same forward element-copy (kept, so the front-recursive take() "
            "invariant still triggers -- pilot bug #3), but reshaped: read the "
            "element into a typed local `cur` before append and reorder the two "
            "leading trailing asserts. All gold loop invariants and per-element "
            "framing asserts are kept verbatim (pilot bug #2). A correct, "
            "structurally-distinct clone must verify; if not => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # 2. ADMISSIBILITY -- a self-call confirming the precondition admits a
    #    normal F2P-shaped input.  In as_plain's impl, before the real body,
    #    allocate a fresh CoordVar with a 1-element dims list (the F2P uses a
    #    single dim name "x") and call as_coordinate on it, asserting the
    #    result is distinct.  If the Requires cannot be established for this
    #    legitimate input => PRECOND-TOO-STRONG.
    #    NB: the helper allocations live entirely inside the impl region; the
    #    real as_plain body is preserved verbatim after them.
    # =====================================================================
    {
        "id": "admiss-fresh-coordvar",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _AS_PLAIN_IMPL,
            """    # impl-start
    probe_dims = []  # type: List[int]
    probe_dims.append(120)
    probe = CoordVar(probe_dims)
    rep = as_coordinate(probe)
    Assert(rep is not probe)
    Assert(rep.dims is not probe.dims)
    base_dims = []  # type: List[int]
    j = 0
    while j < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(base_dims)))
        Invariant(0 <= j and j <= len(self.dims))
        Invariant(ToSeq(base_dims) == ToSeq(self.dims).take(j))
        # strictly decreasing measure discharges MustTerminate(4).
        Invariant(MustTerminate(len(self.dims) - j + 1))
        # invariants-end
        base_dims.append(self.dims[j])
        j = j + 1
    Assert(ToSeq(self.dims).take(len(self.dims)) == ToSeq(self.dims))
    return CoordVar(base_dims)
    # impl-end""",
        ),
        "rationale": (
            "Constructs an F2P-shaped 1-element CoordVar and calls "
            "as_coordinate on it; the precondition Acc(self.dims,1/2) must be "
            "establishable for a freshly-built variable (the constructor leaves "
            "full Acc, so 1/2 is available) and the distinct-object guarantee "
            "must hold. If the call site fails to satisfy Requires for this "
            "legitimate input => PRECOND-TOO-STRONG. The real as_plain body is "
            "preserved verbatim after the probe."
        ),
    },

    # =====================================================================
    # 3. UNIQUENESS / the actual bug -- the aliasing `return self`.
    #    This IS model_prepatch: the pre-patch `return self` reproduces #6931.
    #    Must REJECT: Result() is self => Acc(self.dims,1/2) retained + full
    #    Acc(Result().dims) = 3/2 > 1 insufficient permission, and
    #    `Result() is not self` is false.  The F2P checks `a is not b`.
    # =====================================================================
    {
        "id": "weak-alias-return-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _AS_COORD_IMPL,
            """    # impl-start
    return self
    # impl-end""",
        ),
        "refinement": (
            "This is the verbatim pre-patch bug (model_prepatch.py): "
            "`to_index_variable` returns the receiver itself. A faithful real "
            "patch leaving `return self` is exactly what issue #6931 reports and "
            "what test_to_index_variable_copy fails on (`assert a is not b`; "
            "reassigning b.dims corrupts a.dims). It does NOT resolve the F2P."
        ),
        "rationale": (
            "Rejected by the postcondition: Result() is self makes "
            "`Result() is not self` false AND requires full Acc(Result().dims) "
            "while the receiver keeps Acc(self.dims,1/2) => 3/2 > 1, insufficient "
            "permission. The permission discipline forbids the alias."
        ),
    },

    # =====================================================================
    # 4. UNIQUENESS / aliased-storage (value-correct, storage-shared).
    #    A rival that returns a FRESH object but constructs it directly from
    #    self.dims: `return CoordVar(self.dims)`.  Value-equal (carries the
    #    receiver's names) and a distinct object, so it would pass naive value
    #    and identity checks -- but Result().dims IS self.dims, so reassigning
    #    the result's dims (what swap_dims does) corrupts the receiver.  Must
    #    REJECT: CoordVar.__init__ requires FULL Acc(list_pred(dims)) but
    #    as_coordinate only holds 1/2 => insufficient permission; and
    #    `Result().dims is not self.dims` would be false.
    # =====================================================================
    {
        "id": "weak-shared-storage-ctor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _AS_COORD_IMPL,
            """    # impl-start
    res = CoordVar(self.dims)
    return res
    # impl-end""",
        ),
        "refinement": (
            "A real patch like `return IndexVariable(self._dims, self._data, "
            "..., fastpath=True)` that REUSES the receiver's `_dims` object "
            "(no copy.copy) yields a distinct IndexVariable whose `_dims` is the "
            "SAME tuple/storage. swap_dims then does `var.dims = dims` -- the "
            "setter reassigns `_dims`, so this particular variant happens to be "
            "safe for tuples, but the model carrier is a mutable List and the "
            "discriminating guarantee the fix relies on is independent storage "
            "(`Result().dims is not self.dims`). A shared-storage re-presentation "
            "is precisely the aliasing #6931 forbids and does NOT establish the "
            "swap_dims safety obligation the gold copy() provides."
        ),
        "rationale": (
            "Rejected two ways: (a) CoordVar.__init__ Requires "
            "Acc(list_pred(dims)) at FULL permission but as_coordinate holds only "
            "Acc(list_pred(self.dims),1/2) => insufficient permission to pass "
            "self.dims to the constructor; (b) even ignoring (a), "
            "`Result().dims is not self.dims` in the postcondition is false. The "
            "distinct-storage clause is the swap_dims safety obligation."
        ),
    },

    # =====================================================================
    # 5. FRAME-MUTATION (MANDATORY -- read-only input).  A rival that WRITES
    #    to the read-only receiver to satisfy the postcondition vacuously:
    #    overwrite self.dims with a fresh list then return a distinct copy.
    #    The receiver is Acc(self.dims,1/2) (read-only); a field write needs
    #    FULL Acc(self.dims).  Must REJECT for INSUFFICIENT PERMISSION.  The
    #    gold postcondition invariants are untouched so the rejection is
    #    attributable to the write.
    # =====================================================================
    {
        "id": "frame-mutate-receiver-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _AS_COORD_IMPL,
            """    # impl-start
    stolen = []  # type: List[int]
    self.dims = stolen
    return independent_clone(self)
    # impl-end""",
        ),
        "refinement": (
            "A real patch that mutates the receiver (`self._dims = ...`) inside "
            "to_index_variable would corrupt the source object on every call -- "
            "the opposite of the #6931 fix, which exists precisely so the "
            "re-presentation does NOT touch the original. It would fail the F2P "
            "`a.dims == ('x',)` after the operation and break PASS_TO_PASS that "
            "rely on to_index_variable being non-mutating."
        ),
        "rationale": (
            "Rejected by the permission system: `self.dims = stolen` is a field "
            "write requiring full Acc(self.dims), but the precondition grants "
            "only Acc(self.dims,1/2) => insufficient permission. This is the #1 "
            "frame-mutation weakness class; a byte-fuzzer never tries to write "
            "the input. Gold postcondition kept verbatim so the failure is the "
            "write."
        ),
    },

    # =====================================================================
    # 6. FRAME-MUTATION (supporting) -- mutate the read-only list contents via
    #    append instead of a field reassignment, then return a fresh copy.
    #    self.dims.append(...) needs FULL list_pred(self.dims) write permission
    #    but only Acc(list_pred(self.dims),1/2) is held => insufficient
    #    permission.  Confirms the LIST-CONTENTS half of the frame condition,
    #    not just the field.
    # =====================================================================
    {
        "id": "frame-mutate-receiver-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _AS_COORD_IMPL,
            """    # impl-start
    self.dims.append(999)
    return independent_clone(self)
    # impl-end""",
        ),
        "refinement": (
            "Appending to the receiver's dimension-name list is an in-place "
            "mutation of the source -- exactly the corruption #6931 reports. A "
            "real patch doing this changes the original variable's dims and "
            "fails both the F2P (`a.dims == ('x',)`) and the swap_dims invariant "
            "the fix protects; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by the permission system: `self.dims.append(...)` needs "
            "full Acc(list_pred(self.dims)) write permission, but the "
            "precondition grants only the 1/2 read fraction => insufficient "
            "permission. Targets the list-contents half of the frame condition."
        ),
    },

    # =====================================================================
    # 7. PARTIAL-DOMAIN -- a rival correct on the empty/length-class subdomain
    #    but DIVERGING on the first element: drop the first dim name.  In
    #    independent_clone, start the copy at i=1 instead of i=0 (so for a
    #    1-element receiver -- the F2P input -- the result is empty; for the
    #    0-element case it is trivially equal).  Returns a fresh, distinct,
    #    full-permission object (so identity/permission clauses pass) but
    #    ToSeq(Result().dims) != ToSeq(self.dims).  Must REJECT on the value
    #    postcondition.
    #    NB: the loop invariant is adjusted to the wrong start so the variant
    #    is internally consistent; the failure is the FINAL value postcondition,
    #    not a proof gap.
    # =====================================================================
    {
        "id": "weak-drop-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _CLONE_IMPL,
            """    # impl-start
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 1
    while i < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(new_dims)))
        Invariant(ToSeq(self.dims) == s_old)
        Invariant(1 <= i and i <= len(s_old) + 1)
        # decreasing measure keeps the loop obligation-clean so the rejection
        # stays attributable to the FINAL value postcondition, not termination.
        Invariant(MustTerminate(len(self.dims) - i + 1))
        # invariants-end
        new_dims.append(self.dims[i])
        i = i + 1
    res = CoordVar(new_dims)
    return res
    # impl-end""",
        ),
        "refinement": (
            "A re-presentation that drops the first dimension name produces a "
            "variable with the wrong dims tuple. The F2P starts from "
            "IndexVariable('x', ['a']) and asserts the copy's dims == ('x',); a "
            "drop-first variant yields () and fails. It also breaks every "
            "PASS_TO_PASS that round-trips dims through to_index_variable. Does "
            "NOT resolve."
        ),
        "rationale": (
            "Rejected by the value postcondition "
            "`ToSeq(Result().dims) == ToSeq(self.dims)`: the result omits the "
            "first name, so the sequences differ for any non-empty receiver "
            "(the F2P's 1-element 'x'). Identity/permission clauses pass (fresh "
            "distinct object), isolating the value divergence."
        ),
    },

    # =====================================================================
    # 8. UNIQUENESS / fabricate-names -- a rival that returns a fresh, distinct,
    #    fully-owned object whose dims are a DIFFERENT sequence (a constant
    #    singleton), so it satisfies the identity + permission + receiver-
    #    unchanged clauses but violates ToSeq(Result().dims)==ToSeq(self.dims).
    #    Distinct from #7 (which preserves a prefix); this fabricates content.
    #    Must REJECT.
    # =====================================================================
    {
        "id": "weak-fabricate-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _CLONE_IMPL,
            """    # impl-start
    new_dims = []  # type: List[int]
    new_dims.append(424242)
    res = CoordVar(new_dims)
    return res
    # impl-end""",
        ),
        "refinement": (
            "Returning a fresh variable whose dimension names are fabricated "
            "(a constant) rather than copied from the receiver is not a "
            "re-presentation at all. swap_dims/to_index_variable callers depend "
            "on the result carrying the receiver's names; the F2P asserts the "
            "copy's dims equal the original's ('x',). A constant-name result "
            "fails it and does NOT resolve."
        ),
        "rationale": (
            "Rejected by `ToSeq(Result().dims) == ToSeq(self.dims)`: the result "
            "carries [424242] regardless of the receiver, so the value "
            "postcondition fails (e.g. against the F2P's 'x'). The object is "
            "distinct and fully owned, so the failure is purely the value pin."
        ),
    },
]


# ---------------------------------------------------------------------------
# No @ContractOnly axioms, no consumed axioms (meta.axioms == []).  The single
# A-reference deep model (independent allocation) is already validated against
# the real post-patch xarray callees by axiom_check.py / G-AX (F2P scenario +
# 5 boundary variables + 2000 fuzz cases).  There is no per-axiom Requires
# domain to fuzz or contain, so AXIOM_TESTS is empty by construction.
# ---------------------------------------------------------------------------
AXIOM_TESTS = []
