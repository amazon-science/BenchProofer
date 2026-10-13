"""PBT falsification battery for matplotlib__matplotlib-24627.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants (frozen spec, swapped impl region) checked by Nagini verify +
same_spec; this bundle has NO @ContractOnly axiom and NO consumed-axiom A-step,
so AXIOM_TESTS is empty (see meta.json axioms == [], deep_model_references is a
single A-reference validated end-to-end by axiom_check.py / G-AX).

Defended surface (reset_container : Container -> None)
------------------------------------------------------
Preconditions:
  * Acc(self.members) and Acc(list_pred(self.members))                 [full]
  * Forall k in [0,len): Acc(self.members[k].host) and
        Acc(self.members[k].canvas)                                    [FULL perm]
    -> the member back-references are WRITE-permitted inputs by design (the gold
       patch writes them). There is NO read-only Acc(.,1/2) INPUT parameter, so
       the frame-mutation weakness class (overwrite a half-permission read-only
       input to satisfy a postcondition vacuously) does NOT apply to this spec;
       a "write to a 1/2 input" rival here would fail for a manufactured proof
       reason, not expose a spec defect. has_readonly_input == False. (The 1/2
       fractions in this bundle live only in the POSTcondition, where they hand
       read-only access to the surviving old members BACK to the caller, and in
       the loop invariant.)

Postconditions (load-bearing clauses):
  (1) len(self.members) == 0                              -- collection emptied
  (2) Acc(list_pred(Old(self.members)), 1/2)              -- former members
                                                             survive (read-only)
  (3) Forall k in [0,len(Old(members))):
          Acc(Old(members)[k].host,1/2) and Acc(Old(members)[k].canvas,1/2)
          and Old(members)[k].host is None
          and Old(members)[k].canvas is None              -- DE-PARENTING clause
      This is the discriminating clause: it is exactly what the F2P test
      test_cla_clears_children_axes_and_fig observes (after ax.clear(), every
      former child has art.axes is None AND art.figure is None) and exactly the
      property model_prepatch.py violates (the pre-patch __clear left .axes /
      .figure stale). Clause (3) pins BOTH fields, on EVERY former member.

No ungrounded oracle: the postconditions are grounded constants (`is None`,
`len == 0`) computed from the inputs, not pinned to a @Pure answer-key that an
impl could echo. So there is no "wrong echo" rival; UNGROUNDED-ORACLE is covered
by an honest cheapest-impl positive control (the gold structural variants below)
rather than an echo-reject.

The free region is the impl block (markers inclusive; the loop Invariants are
NESTED inside impl, so they too are part of the free region per spec_view). Each
variant below is built by _swap on _BASE, editing ONLY inside # impl-start /
# impl-end -- the frozen spec (axioms/pure/pre/post-conditions) is never touched,
which mechanically GUARANTEES same_spec.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24627"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl block, verbatim from model.py (markers + nested invariants),
# everything strictly between (and including) the bodies inside # impl-start /
# # impl-end. Swapping this whole block edits ONLY the free region.
_GOLD = '''    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): de-parent FIRST, rebind to [] AFTER the loop.
# Structurally different ordering from the gold (gold rebinds self.members
# before the loop; here we bind a local alias to the existing collection,
# de-parent every member through it, and rebind self.members=[] LAST).
# Still correct: every member is de-parented, then the collection is emptied.
# Keeps a per-element-progress invariant + the full-permission framing invariant
# it needs (directive: do NOT drop framing asserts a positive control still
# needs). MUST verify; else SPEC-TOO-STRONG.
#
# NB: the loop must hold its list_pred permission against a STABLE local name
# (`members`) rather than the field expression `self.members`. After the
# post-loop rebind `self.members = []`, the field no longer denotes the old
# list, so framing the postcondition `Acc(list_pred(Old(self.members)), 1/2)`
# requires a named handle on the original list object that the rebind does not
# touch. Iterating over the field expression directly (and only learning
# `self.members is members` after the Acc) leaves Nagini unable to connect the
# retained list_pred to Old(self.members) -- a framing/proof-engineering gap,
# not a spec defect. The alias `members` (+ `self.members is members` invariant)
# is the in-region proof that closes it; the spec is untouched.
# ---------------------------------------------------------------------------
_POS_REBIND_AFTER = '''    members = self.members
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(self.members))
        Invariant(self.members is members)
        Invariant(Acc(list_pred(members)))
        Invariant(0 <= i and i <= len(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                  Acc(members[k].host) and Acc(members[k].canvas)),
                  [[members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  members[k].host is None and members[k].canvas is None),
                  [[members[k]]])))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        members[i].host = None
        members[i].canvas = None
        i = i + 1
    self.members = []'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): clear canvas before host within the loop body
# (field-write order reshape) and keep the gold loop structure/invariants. The
# de-parenting is order-independent per the refinement; both writes still land.
# A trivial-but-correct reshape that must verify.
# ---------------------------------------------------------------------------
_POS_SWAP_FIELDS = '''    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].canvas = None
        old_members[i].host = None
        i = i + 1'''


# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold impl, but assert at entry that the precondition is
# non-vacuous -- i.e. when the collection is non-empty we can actually READ a
# member's back-references (proving we hold the permission the Requires grants).
# If a normal F2P-shaped (non-empty) input could not establish the Requires this
# would fail => PRECOND-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS = '''    if len(self.members) > 0:
        Assert(self.members[0].host is self.members[0].host)
        Assert(self.members[0].canvas is self.members[0].canvas)
''' + _GOLD


# ---------------------------------------------------------------------------
# UNIQUENESS / partial-domain rivals (each MUST be rejected by a postcondition).
# ---------------------------------------------------------------------------

# (a) clear ONLY host, leave canvas attached. Fails clause (3) on canvas.
_W_HOST_ONLY = '''    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].host = None
        i = i + 1'''

# (b) clear ONLY canvas, leave host attached. Fails clause (3) on host.
_W_CANVAS_ONLY = '''    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].canvas is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].canvas = None
        i = i + 1'''

# (c) skip the FIRST member (start at i=1): member 0 left fully attached.
#     Fails clause (3) at k=0. The per-element invariant is rephrased to
#     1 <= k < i so the loop still verifies internally; the postcondition is
#     what must reject it (the spec, not the proof).
_W_SKIP_FIRST = '''    old_members = self.members
    self.members = []
    i = 1
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(1 <= i and i <= len(old_members) or len(old_members) == 0)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(1 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1'''

# (d) skip the LAST member (stop at len-1): the final member left attached.
#     Fails clause (3) at k = len-1.
_W_SKIP_LAST = '''    old_members = self.members
    self.members = []
    i = 0
    while i + 1 < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members), 1 / 2))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1'''

# (e) prepatch twin: rebind self.members = [] and SKIP the de-parenting loop
#     entirely. Satisfies (1) but fails clause (3) -- this is exactly the
#     pre-patch __clear bug (former children keep their stale .axes/.figure).
_W_NO_DEPARENT = '''    self.members = []'''

# (f) de-parent every member correctly but FORGET to rebind the collection to
#     empty: clause (3) holds, clause (1) (len == 0) fails. Isolates clause (1).
_W_NO_EMPTY = '''    old_members = self.members
    i = 0
    while i < len(old_members):
        # invariants-start
        Invariant(Acc(list_pred(old_members)))
        Invariant(0 <= i and i <= len(old_members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(old_members),
                  Acc(old_members[k].host) and Acc(old_members[k].canvas)),
                  [[old_members[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  old_members[k].host is None and old_members[k].canvas is None),
                  [[old_members[k]]])))
        Invariant(MustTerminate(len(old_members) - i + 1))
        # invariants-end
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1'''


SPEC_TESTS = [
    {
        "id": "pos-rebind-after",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_REBIND_AFTER),
        "rationale": "structurally-different CORRECT impl: de-parent every member "
        "by iterating self.members directly, then rebind self.members=[] AFTER "
        "the loop (gold rebinds before). Keeps the full-permission framing "
        "invariant and per-element progress invariant it still needs. Must "
        "verify; else SPEC-TOO-STRONG (the spec would reject a faithful correct "
        "reorder).",
    },
    {
        "id": "pos-swap-fields",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_SWAP_FIELDS),
        "rationale": "correct reshape: write canvas then host (gold writes host "
        "then canvas). De-parenting is order-independent (refinement step 5); "
        "both writes still land None. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-readable-fields",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "the precondition is non-vacuous for a normal F2P-shaped "
        "(non-empty) input: when len(members)>0 we can READ member 0's host and "
        "canvas, proving the Requires actually grants the per-member field "
        "permission. Must verify; else PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-host-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_HOST_ONLY),
        "refinement": "its faithful real patch is `chld.axes = None` (host only) "
        "WITHOUT clearing `chld.figure` -- so after ax.clear() every former "
        "child still has art.figure is fig. The F2P test "
        "test_cla_clears_children_axes_and_fig asserts `art.figure is None` for "
        "each former child, so this patch FAILS the F2P. A verifying rival here "
        "would be a true verify-not-resolve break.",
        "rationale": "rejected by postcondition (3): Forall k. "
        "Old(members)[k].canvas is None is violated (canvas never written).",
    },
    {
        "id": "weak-canvas-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_CANVAS_ONLY),
        "refinement": "its faithful real patch is `chld.figure = None` (canvas "
        "only) WITHOUT clearing `chld.axes` -- so after ax.clear() every former "
        "child still has art.axes is ax, exactly the original bug the issue "
        "reports (`a.cla(); print(l.axes)` -> Axes(...)). The F2P test asserts "
        "`art.axes is None`, so this patch FAILS the F2P.",
        "rationale": "rejected by postcondition (3): Forall k. "
        "Old(members)[k].host is None is violated (host never written).",
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_SKIP_FIRST),
        "refinement": "partial-domain: its faithful real patch de-parents every "
        "child EXCEPT old_children[0] (e.g. `for chld in old_children[1:]:`). The "
        "F2P plots four lines + one image; the first line is a former child and "
        "would keep art.axes/.figure set, so the test's `for art in ...: assert "
        "art.axes is None` FAILS on that first artist. A verify-not-resolve break.",
        "rationale": "rejected by postcondition (3) at k=0: Old(members)[0].host "
        "/.canvas are never written to None.",
    },
    {
        "id": "weak-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_SKIP_LAST),
        "refinement": "partial-domain: its faithful real patch de-parents every "
        "child EXCEPT the last (e.g. `for chld in old_children[:-1]:`). The F2P's "
        "last former child (the imshow image) would keep art.axes/.figure set, so "
        "`assert art.axes is None` FAILS on it. A verify-not-resolve break.",
        "rationale": "rejected by postcondition (3) at k=len-1: the final member's "
        "host/canvas are never cleared.",
    },
    {
        "id": "weak-no-deparent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_NO_DEPARENT),
        "refinement": "this is the PRE-PATCH bug verbatim: `self._children = []` "
        "with no de-parenting loop (the original __clear). The issue and the F2P "
        "both target exactly this: after a.cla(), l.axes is still the Axes. The "
        "F2P FAILS entirely. model_prepatch.py is this skeleton and fails "
        "postcondition (3) (G-DIFF).",
        "rationale": "rejected by postcondition (3): no Old(members)[k] field is "
        "ever set to None, so Forall k. host is None and canvas is None fails.",
    },
    {
        "id": "weak-no-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_NO_EMPTY),
        "refinement": "its faithful real patch de-parents the children but FORGETS "
        "`self._children = []`, so the axes keeps its old children list. The P2P "
        "tests that re-clear / re-draw an axes (and the invariant that clear "
        "empties the collection) FAIL: ax._children is non-empty after clear. A "
        "verify-not-resolve break against clause (1).",
        "rationale": "rejected by postcondition (1): len(self.members) == 0 is "
        "violated (self.members is never rebound to the empty list).",
    },
]

# No @ContractOnly axiom and no consumed-axiom A-step in this bundle (meta.json
# axioms == []). The single deep_model_reference is an A-reference validated
# end-to-end by axiom_check.py / G-AX (real Axes.clear() de-parents every former
# child). There is therefore no per-axiom Requires-domain to fuzz or contain.
AXIOM_TESTS = []
