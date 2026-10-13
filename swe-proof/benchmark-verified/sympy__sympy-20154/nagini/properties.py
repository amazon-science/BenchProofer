# properties.py — PBT falsification battery for sympy__sympy-20154.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# byte-for-byte (region surgery: only the text strictly BETWEEN the single
# # impl-start / # impl-end markers is swapped — the nested invariants live
# inside that region and are elided by markers.spec_view, so editing them does
# NOT change the spec signature) and is checked by Nagini verify + same_spec.
#
# Defended surface (model.py `gather_walk`):
#   gather_walk(steps: int) -> List[int]
#   Requires: steps >= 0; MustTerminate(2) -- a total-correctness obligation:
#       the gather MUST terminate and actually deliver its records. Nagini is a
#       partial-correctness verifier by default, so without the obligation a
#       rival that diverges before returning (infinite loop) satisfies every
#       value Ensures vacuously; the obligation system rejects any loop lacking
#       a decreasing termination measure. The gold loop discharges it with
#       Invariant(MustTerminate(steps - i + 1)).
#   Ensures:  (E1) Acc(list_pred(Result()))            -- output fully owned
#             (E2) len(Result()) == steps               -- one record per step
#             (E3) Forall i. 0<=i<len -> Result()[i] == state_at(i)
#                  where @Pure state_at(i) == i+1 (strictly increasing).
#   (E3) is the LOAD-BEARING discriminator: every gathered record must equal the
#   GROUNDED per-step value of its OWN step. This is exactly the per-step history
#   an aliasing enumerator (whose gathered records all collapse onto the FINAL
#   state) cannot reproduce -- the `yield ms` -> `yield ms.copy()` fix.
#
# Class applicability for THIS instance (justified in 'assessment'):
#   * FRAME-MUTATION: N/A. The sole input `steps` is a pass-by-value `int`; there
#     is NO read-only Acc(x,1/2) reference input to overwrite. The only ownership
#     predicate, Acc(list_pred(Result())), is on the freshly-built OUTPUT. There
#     is nothing to mutate to satisfy the postcondition vacuously, so the
#     frame-mutation probe does not apply (has_readonly_input = False).
#   * UNGROUNDED-ORACLE ECHO: N/A as a *defect* class. (E3) is pinned to the
#     @Pure helper state_at, but state_at is GROUNDED — it fully unfolds to i+1, a
#     pure function of the loop index, with body `return i+1`. There is no opaque
#     answer-key to echo: an impl that "echoes" state_at(i) at index i is doing
#     exactly the required work and IS correct. So there is no WRONG echo that
#     verifies; we substitute the honest cheapest-impl positive control
#     (pos-control-direct: append state_at(i) directly).
#   * CONTROL-FLOW-EFFECT: N/A. gather_walk is pure-functional over the value
#     domain (no raise path, no side effect on any input, returns a fresh list);
#     there is no raise/return/effect difference invisible to the value
#     abstraction, so no capability-token rival is needed.
#   * The strong, applicable classes are PARTIAL-DOMAIN (the spec pins every
#     index; rivals correct on all-but-one index / on a value-class / on length)
#     and the canonical aliasing-collapse defect, plus soundness + admissibility.
#
# AXIOM_TESTS: this bundle consumes NO @ContractOnly axiom (meta.axioms == []).
# The one external semantics relied on — the per-yield duplication `ms.copy()` —
# is an A-REFERENCE deep model (`snap = work`, by-value capture) validated == the
# real callee by axiom_check.py / G-AX. Per PBT_PLAN §2.4/§4, A-reference deep
# models ARE checked in the axiom lane: the deep model must equal the real callee
# on every caller-reachable input. We therefore include two Docker probes that
# run the REAL sympy.utilities.iterables.partitions generator (gold applied) and
# the pure-stdlib dict.copy() primitive to confirm (a) soundness — the by-value
# snapshot history equals the genuine pairwise-distinct per-step truth, and
# (b) containment — every per-step record the model can reach is a dict the
# .copy() primitive handles independently (no reachable input escapes its domain).
from pathlib import Path

INSTANCE = "sympy__sympy-20154"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim text strictly BETWEEN "    # impl-start\n" and "    # impl-end\n"
# (markers excluded). Every variant is _BASE with this block replaced; because
# the block is entirely inside the impl region, markers.same_spec is preserved by
# construction. (The nested # invariants-start/# invariants-end live inside the
# impl region, so the invariants may be reshaped freely without touching the
# spec.)
_IMPL = (
    "    result = []  # type: List[int]\n"
    "    # The live working value the walk advances IN PLACE across steps: it starts\n"
    "    # before the first step and is incremented one step at a time (never\n"
    "    # recomputed from scratch), exactly as the enumerator advances its single\n"
    "    # working record from one state to the next.\n"
    "    work = 0\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        # The working value carries the running state from the previous step.\n"
    "        Invariant(work == i)\n"
    "        # Every already-gathered record holds the snapshot of its own step --\n"
    "        # an INDEPENDENT value that subsequent steps never disturb.\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == state_at(k)))))\n"
    "        # The loop consumes the termination obligation: steps - i is the\n"
    "        # strictly decreasing, bounded-below measure.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        # Advance the working state in place by one step (the enumerator's\n"
    "        # mutation step): the record now holds the state for step i.\n"
    "        work = work + 1\n"
    "        # Hand out an INDEPENDENT snapshot of the working state (the snapshot\n"
    "        # step): the current value is recorded by value, so later mutations of\n"
    "        # the working state leave this gathered record untouched.\n"
    "        snap = work\n"
    "        result.append(snap)\n"
    "        i = i + 1\n"
    "    return result\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: impl block not found verbatim")
    if src.count(old) != 1:
        raise AssertionError("not unique: impl block")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Full model source with the impl-region body replaced by new_impl (the text
    that goes strictly between the # impl-start / # impl-end markers, so same_spec
    is preserved by construction)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl.
# Local-variable RESHAPE: the working `work` accumulator is dropped entirely; each
# record is the per-step value computed directly as `state_at(i)` (== i+1) and
# appended. No loop-direction flip, no fold/append induction lemma — the prefix-
# preservation invariant is discharged exactly as in gold (each append adds
# state_at(i) at index i). Keeps every gold proof obligation it still needs
# (Acc/len/prefix-preservation). MUST verify, else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = (
    "    # Structurally-different but behaviourally-identical: no `work`\n"
    "    # accumulator at all; record the per-step value directly.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == state_at(k)))))\n"
    "        # The loop consumes the termination obligation: steps - i is the\n"
    "        # strictly decreasing, bounded-below measure.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        # The per-step snapshot, computed directly from the step index.\n"
    "        snap = state_at(i)\n"
    "        result.append(snap)\n"
    "        i = i + 1\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY — the precondition must admit a normal F2P-shaped input (a
# 3-step walk: list(partitions(...)) gathers >=1 yields in every F2P test).
# The precondition for such an input is re-derived by leading Asserts (a
# self-call is no longer usable: the caller's own MustTerminate(2) obligation
# cannot be handed to a callee demanding the same measure — the obligation
# system requires a strictly smaller callee measure, and that rejection would
# be about obligations, not admissibility). If a normal in-domain input could
# not establish the Requires, this would fail => PRECOND-TOO-STRONG. The real
# (correct) body follows unchanged.
# ---------------------------------------------------------------------------
_ADMISS = (
    "    # Admissibility: a normal F2P-shaped input (a 3-step walk) satisfies\n"
    "    # the precondition; re-derive it here, then run the gold body.\n"
    "    probe = 3  # type: int\n"
    "    Assert(probe >= 0)\n"
    "    Assert(state_at(0) == 1 and state_at(2) == 3)\n"
    "    # Real logic (unchanged behaviour).\n"
    "    result = []  # type: List[int]\n"
    "    work = 0\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(work == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == state_at(k)))))\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        work = work + 1\n"
    "        snap = work\n"
    "        result.append(snap)\n"
    "        i = i + 1\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 3a. ALIASING-COLLAPSE (uniqueness; the canonical modeled defect, == the
# pre-patch behaviour / model_prepatch.py). Every gathered record reads back as
# the FINAL state `steps` instead of the snapshot of its own step. Translatable
# with a sound invariant (every gathered record == steps); the ONLY obligation it
# fails is the postcondition (E3) Result()[i] == state_at(i) == i+1, which for
# steps>=2 is violated at index 0 (result[0]==steps != 1). MUST reject.
# ---------------------------------------------------------------------------
_REJ_COLLAPSE = (
    "    # PRE-PATCH DEFECT: hand out a live alias, so every gathered record reads\n"
    "    # back as the FINAL state (`steps`) -- the per-step history is lost.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == steps))))\n"
    "        # Discharge the termination obligation identically to gold, so the\n"
    "        # reject stays on the SPEC (the value clause), not an obligation leak.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        snap = steps\n"
    "        result.append(snap)\n"
    "        i = i + 1\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 3b. OFF-BY-ONE / wrong per-step VALUE (uniqueness). Records the working state
# BEFORE the advance (snap = i, the 0-based pre-step value) instead of after, so
# every record is one too small: Result()[i] == i. Correct length and ownership;
# correct shape; fails (E3) on every index (Result()[i]==i != i+1==state_at(i)).
# A faithful real analogue: yielding the dict at the WRONG point in the mutation
# loop (an off-by-one in the snapshot), so gathered records lag by one step.
# MUST reject.
# ---------------------------------------------------------------------------
_REJ_OFFBYONE = (
    "    # WRONG: record the working state BEFORE the per-step advance, so every\n"
    "    # gathered record lags by one (Result()[i] == i, not i+1).\n"
    "    result = []  # type: List[int]\n"
    "    work = 0\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(work == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == k))))\n"
    "        # Discharge the termination obligation identically to gold, so the\n"
    "        # reject stays on the SPEC (the value clause), not an obligation leak.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        snap = work\n"
    "        result.append(snap)\n"
    "        work = work + 1\n"
    "        i = i + 1\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 3c. PARTIAL-DOMAIN (first-element divergence; uniqueness). Correct on EVERY
# index except the first: the first record is seeded at 0 (a stale initial-state
# leak) while every later record is the genuine state_at(i)==i+1. A whole-domain
# value fuzzer that only checks "are the records strictly increasing / distinct"
# would PASS this (0,2,3,4,... is still strictly increasing); only the exact
# per-index pin catches it. Fails (E3) at index 0 (Result()[0]==0 != 1) for
# steps>=1. MUST reject.
# ---------------------------------------------------------------------------
_REJ_FIRST = (
    "    # WRONG only on the FIRST record: it leaks the stale initial state (0)\n"
    "    # instead of the step-0 snapshot (1); every later record is correct.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Implies(i > 0, result[0] == 0))\n"
    "        Invariant(Forall(int, lambda k: (Implies(1 <= k and k < i,\n"
    "            result[k] == state_at(k)))))\n"
    "        # Discharge the termination obligation identically to gold, so the\n"
    "        # reject stays on the SPEC (the value clause), not an obligation leak.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        if i == 0:\n"
    "            first = 0\n"
    "            result.append(first)\n"
    "        else:\n"
    "            snap = state_at(i)\n"
    "            result.append(snap)\n"
    "        i = i + 1\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 3d. LENGTH-DIVERGENCE (uniqueness; supporting). Correct per-step values but the
# gather appends one EXTRA record at the end (a duplicated final state), so
# len(Result()) == steps+1. Fails (E2) len(Result())==steps. A faithful real
# analogue: a gather that yields once too many (e.g. an off-by-one loop bound in
# the enumerator) — list length wrong, so every F2P list-equality assertion
# fails. MUST reject. (Guarded so it stays well-typed when steps==0.)
# ---------------------------------------------------------------------------
_REJ_LEN = (
    "    # WRONG length: append one extra (duplicate final-state) record so the\n"
    "    # gathered list is one longer than the number of steps.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == state_at(k)))))\n"
    "        # Discharge the termination obligation identically to gold, so the\n"
    "        # reject stays on the SPEC (the value clause), not an obligation leak.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        snap = state_at(i)\n"
    "        result.append(snap)\n"
    "        i = i + 1\n"
    "    extra = steps  # type: int\n"
    "    result.append(extra)\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 3e. REVERSED ORDER (uniqueness; value/structure). Same multiset of per-step
# values but in REVERSED index order: Result()[i] == steps - i. A value proxy
# that only checked the SET / SUM of gathered records would accept this; only the
# per-INDEX postcondition (E3) catches that the k-th gathered record must be the
# k-th step's state, not some permutation. A faithful real analogue: gathering
# the enumerator's yields in reverse / mis-ordering the per-step records. Fails
# (E3) at index 0 for steps>=2 (Result()[0]==steps != 1). MUST reject.
# ---------------------------------------------------------------------------
_REJ_REVERSED = (
    "    # WRONG order: record the per-step values in REVERSED index order, so the\n"
    "    # multiset matches but Result()[i] == steps - i, not i+1.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < steps:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= steps)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "            result[k] == steps - k))))\n"
    "        # Discharge the termination obligation identically to gold, so the\n"
    "        # reject stays on the SPEC (the value clause), not an obligation leak.\n"
    "        Invariant(MustTerminate(steps - i + 1))\n"
    "        # invariants-end\n"
    "        snap = steps - i\n"
    "        result.append(snap)\n"
    "        i = i + 1\n"
    "    return result\n"
)

# ---------------------------------------------------------------------------
# 3f. NON-TERMINATION (uniqueness; vacuous divergence). An impl that never
# returns: it spins forever (while 0 <= i with i increasing), so every value
# postcondition is satisfiable only vacuously — no execution reaches the
# return. This is exactly the spec-too-weak class the G-PANEL-1 auditor's
# verifying candidates belonged to before the MustTerminate obligation was
# added (any same-spec impl was admitted as long as its VALUE claims held or
# never had to hold). Under Requires(MustTerminate(2)) the spinning loop takes
# no termination obligation and has no decreasing measure, so Nagini's
# obligation system MUST reject it. The invariants are relaxed to what the
# spinning loop maintains — the reject must come from the obligation system,
# not a broken proof. MUST reject.
# ---------------------------------------------------------------------------
_REJ_NONTERM = (
    "    # Vacuous non-termination: spin forever, never deliver the records.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while 0 <= i:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        # invariants-end\n"
    "        i = i + 1\n"
    "    return result\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS),
        "rationale": "A structurally-different but behaviourally-identical impl "
                     "(no `work` accumulator; each record computed directly as "
                     "state_at(i) and appended). No loop-direction flip / no fold "
                     "induction lemma, so the prefix-preservation invariant and "
                     "the Acc/len obligations are discharged exactly as in gold. "
                     "Produces [1,2,...,steps] and MUST verify; if it cannot, "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-3-step-walk",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "Re-derives the precondition for a normal F2P-shaped input "
                     "(a 3-step walk; every F2P test gathers >=1 yield) with "
                     "leading Asserts (probe==3 satisfies steps>=0; state_at pins "
                     "the per-step values 1..3), then the gold body runs "
                     "unchanged. A self-call is no longer usable under the "
                     "termination obligation (the caller's MustTerminate(2) "
                     "cannot be handed to a callee demanding the same measure). "
                     "If the precondition rejected this normal input, "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "uniq-aliasing-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_COLLAPSE),
        "refinement": "This is exactly the pre-patch behaviour (model_prepatch.py / "
                      "`yield ms` with the live alias): every gathered record reads "
                      "back as the FINAL state. The faithful real patch is the "
                      "UNCHANGED pre-patch `yield ms`, under which "
                      "[p.copy() for p in partitions(6, k=2)] == "
                      "[{1:6},{1:6},{1:6},{1:6}] (all the final partition) instead "
                      "of the genuine [{2:3},{1:2,2:2},{1:4,2:1},{1:6}]; so "
                      "test_partitions' list-equality assertions and test_uniq fail "
                      "-> both F2P unresolved.",
        "rationale": "Violates Ensures (E3) Result()[i]==state_at(i): for steps>=2 "
                     "the collapse makes result[0]==steps != 1. The rejection comes "
                     "from the per-step-history postcondition clause — the exact "
                     "discriminator the .copy() fix installs.",
    },
    {
        "id": "uniq-off-by-one-snapshot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_OFFBYONE),
        "refinement": "Records the working state BEFORE the per-step advance, so "
                      "every gathered record lags one step (Result()[i]==i). A "
                      "faithful real analogue is snapshotting the working dict at "
                      "the wrong point in the mutation loop: the gathered list is a "
                      "shifted history, so test_partitions' element-by-element "
                      "comparison against the expected per-step partitions fails "
                      "(every entry off by one step) -> F2P unresolved.",
        "rationale": "Violates Ensures (E3): Result()[i]==i != i+1==state_at(i) on "
                     "every index. Targets the per-step VALUE facet (the snapshot "
                     "timing), distinct from the collapse defect.",
    },
    {
        "id": "uniq-partial-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_FIRST),
        "refinement": "Correct on every step EXCEPT the first, where it leaks the "
                      "stale initial state (0) instead of the step-0 snapshot (1). "
                      "A monotonicity/distinctness proxy (records strictly "
                      "increasing) would accept 0,2,3,4,...; only the exact per-step "
                      "pin catches it. The faithful real analogue mis-records the "
                      "FIRST yielded partition (the first `yield ms` left "
                      "un-copied or seeded from the pre-loop dict), so the first "
                      "element of every F2P gather is wrong -> test_partitions "
                      "first-row comparison fails, F2P unresolved.",
        "rationale": "Violates Ensures (E3) on the single sub-domain i==0 "
                     "(Result()[0]==0 != 1) while satisfying it for every i>=1. "
                     "This is the partial-domain attack the per-index postcondition "
                     "defends.",
    },
    {
        "id": "uniq-length-divergence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_LEN),
        "refinement": "Per-step values are all correct, but the gather appends one "
                      "EXTRA (duplicate final-state) record, so the list is one too "
                      "long. The faithful real analogue is a gather with an "
                      "off-by-one loop bound / a spurious trailing yield: every F2P "
                      "test that asserts the exact list of partitions (length and "
                      "contents) fails because there is one extra entry -> F2P "
                      "unresolved.",
        "rationale": "Violates Ensures (E2) len(Result())==steps "
                     "(len==steps+1). Targets the cardinality facet that the "
                     "per-element pin alone would not catch.",
    },
    {
        "id": "uniq-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_REVERSED),
        "refinement": "Records the SAME multiset of per-step values but in reversed "
                      "index order (Result()[i]==steps-i). A value proxy keyed on "
                      "the set/sum of records would accept it; only the per-INDEX "
                      "postcondition catches that the k-th gathered record must be "
                      "the k-th step's state. The faithful real analogue gathers the "
                      "enumerator's yields in the wrong order, so test_partitions' "
                      "ordered list comparison fails -> F2P unresolved.",
        "rationale": "Violates Ensures (E3) at index 0 for steps>=2 "
                     "(Result()[0]==steps != 1). Targets the index/order facet — a "
                     "value-level-double-mask style attack the per-index pin "
                     "defeats.",
    },
    {
        "id": "uniq-nonterminating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_NONTERM),
        "refinement": "The rival never returns: it spins in an unbounded loop, so "
                      "every value postcondition holds only vacuously and the "
                      "gathered records are never delivered. Its faithful real "
                      "patch is a partitions/gather that hangs — "
                      "list(partitions(...)) would never return, every F2P test "
                      "(test_partitions, test_uniq) times out/fails, so it does "
                      "NOT resolve. This is the vacuous-divergence class the "
                      "value-only spec admitted before the MustTerminate "
                      "obligation was added.",
        "rationale": "MUST reject via the OBLIGATION system: "
                     "Requires(MustTerminate(2)) forces every loop on the path to "
                     "the return to carry a decreasing termination measure; the "
                     "spinning loop has none, so Nagini rejects it (obligation "
                     "leak). Rejection source: the termination obligation, not a "
                     "value clause — demonstrating the spec no longer admits "
                     "vacuous divergence.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — A-reference deep-model validation (no @ContractOnly axiom is
# consumed; meta.axioms == []). Per PBT_PLAN §2.4/§4, the A-reference deep model
# (`snap = work` by-value capture <-> `ms.copy()` per yield) is checked against
# the REAL callee on every caller-reachable input. Both probes run in the
# instance image with the gold patch applied (apply_gold=True), where
# `partitions` yields independent copies (the modeled fix). Probes import only
# the stdlib + the repo function under test; they print a diagnostic and
# sys.exit(0) iff the obligation holds.
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import random, sys

# --- (1) the pure-stdlib dict.copy() independence primitive the deep model
#         encodes: a fresh copy is a DISTINCT object, equal in contents at copy
#         time, and isolated from subsequent source mutations. This is the
#         `snap = work` by-value capture in the integer abstraction.
def check_dict_copy_independence():
    samples = [
        {}, {1: 6}, {2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1},
        {4: 2}, {1: 1, 3: 1, 4: 1}, {2: 2, 4: 1}, {2: 1, 3: 2},
        {k: k * k for k in range(1, 12)},
    ]
    for d in samples:
        c = d.copy()
        assert c is not d, "copy not a distinct object for %r" % (d,)
        assert c == d, "copy contents differ at copy time for %r" % (d,)
        snapshot = d.copy()
        d[999] = 1
        if d:
            kk = next(iter(d)); d[kk] = d[kk] + 1000
        assert c == snapshot, "copy %r disturbed by later source mutation" % (c,)

def _arglist():
    fixed = [
        (6, None, 2, False), (6, None, 3, False), (8, 3, 4, False),
        (3, 2, None, False), (4, None, 3, False), (4, None, None, False),
        (6, 2, 2, False), (6, 2, None, False), (1, 0, None, False),
        (0, None, None, False), (6, None, 2, True), (8, 3, 4, True),
        (3, 2, None, True), (7, None, None, False), (10, 4, 5, False),
    ]
    rng = random.Random(20154)
    fuzz = []
    for _ in range(400):
        n = rng.randint(0, 14)
        m = rng.choice([None, rng.randint(0, 6)])
        k = rng.choice([None, rng.randint(0, 6)])
        size = rng.choice([False, True])
        fuzz.append((n, m, k, size))
    return fixed + fuzz

def _part_of(y, size):
    return y[1] if size else y

# --- (2) the real partitions generator (gold applied => yields .copy()). The
#         deep model's encoded property: gathering BY-VALUE snapshots equals the
#         genuine per-step history (consumed one-at-a-time), with pairwise-
#         distinct neighbours; and, post-patch, the bare gather is itself fully
#         independent (every entry a distinct object) and equals that truth.
def check_partitions(partitions):
    saw_multi = False
    for (n, m, k, size) in _arglist():
        snaps = [_part_of(y, size).copy() for y in partitions(n, m=m, k=k, size=size)]
        truth = []
        for y in partitions(n, m=m, k=k, size=size):
            truth.append(_part_of(y, size).copy())
        assert snaps == truth, (
            "snapshot history != one-at-a-time truth for n=%r m=%r k=%r size=%r: %r vs %r"
            % (n, m, k, size, snaps, truth))
        for a, b in zip(snaps, snaps[1:]):
            assert a != b, ("consecutive snapshots equal for n=%r m=%r k=%r size=%r: %r"
                            % (n, m, k, size, a))
        gathered = list(partitions(n, m=m, k=k, size=size))
        parts = [_part_of(y, size) for y in gathered]
        if len(parts) > 1:
            saw_multi = True
            ids = {id(p) for p in parts}
            # gold applied => fully independent gather; must equal the truth.
            assert len(ids) == len(parts), (
                "gold-applied gather is NOT fully independent for n=%r m=%r k=%r size=%r"
                % (n, m, k, size))
            assert [p.copy() for p in parts] == truth, (
                "independent gather != true per-step history for n=%r m=%r k=%r size=%r"
                % (n, m, k, size))
    return saw_multi

def main():
    check_dict_copy_independence()
    try:
        from sympy.utilities.iterables import partitions
    except Exception as exc:
        print("AX-SOUND FAIL: sympy.partitions not importable: %s" % (exc,))
        return 1
    saw_multi = check_partitions(partitions)
    if not saw_multi:
        print("AX-SOUND FAIL: no multi-partition case exercised (probe vacuous)")
        return 1
    print("AX-SOUND OK: dict.copy independence holds; gold-applied partitions "
          "yields fully-independent per-step snapshots equal to the one-at-a-time "
          "truth with pairwise-distinct neighbours -- by-value deep model sound.")
    return 0

sys.exit(main())
'''

_AX_CONTAIN_PROBE = r'''
import random, sys

# CONTAINMENT: every per-step record the model can reach (the working partition
# `ms` at each yield, abstracted to `snap = work`) must lie inside the domain the
# A-reference primitive (`dict.copy()`) handles. The deep model passes ARBITRARY
# dicts to the copy primitive; dict.copy() is total over dicts, so every
# caller-reachable yielded object is in-domain. We confirm this concretely: every
# object the REAL partitions generator hands out (gold applied) is a dict whose
# .copy() is a distinct, equal, mutation-isolated object -- so no reachable input
# escapes the primitive's domain (no AXIOM-TOO-WEAK-FOR-CALLER).
def _arglist():
    fixed = [
        (6, None, 2, False), (6, None, 3, False), (8, 3, 4, False),
        (3, 2, None, False), (4, None, 3, False), (0, None, None, False),
        (1, 0, None, False), (6, None, 2, True), (8, 3, 4, True),
        (3, 2, None, True), (7, None, None, False), (10, 4, 5, False),
    ]
    rng = random.Random(200154)
    fuzz = []
    for _ in range(300):
        n = rng.randint(0, 14)
        m = rng.choice([None, rng.randint(0, 6)])
        k = rng.choice([None, rng.randint(0, 6)])
        size = rng.choice([False, True])
        fuzz.append((n, m, k, size))
    return fixed + fuzz

def _part_of(y, size):
    return y[1] if size else y

def main():
    try:
        from sympy.utilities.iterables import partitions
    except Exception as exc:
        print("AX-CONTAIN FAIL: sympy.partitions not importable: %s" % (exc,))
        return 1
    seen = 0
    for (n, m, k, size) in _arglist():
        for y in partitions(n, m=m, k=k, size=size):
            p = _part_of(y, size)
            # Every reachable yielded record must be a dict in dict.copy()'s domain.
            assert isinstance(p, dict), (
                "reachable record is not a dict (outside the copy primitive's "
                "domain) for n=%r m=%r k=%r size=%r: %r" % (n, m, k, size, p))
            c = p.copy()
            assert c is not p and c == p, (
                "copy primitive ill-behaved on a reachable record for "
                "n=%r m=%r k=%r size=%r: %r" % (n, m, k, size, p))
            seen += 1
    if seen == 0:
        print("AX-CONTAIN FAIL: no reachable records enumerated (probe vacuous)")
        return 1
    print("AX-CONTAIN OK: all %d caller-reachable per-step records are dicts the "
          ".copy() primitive handles independently -- the A-reference domain "
          "covers every input the model can reach." % (seen,))
    return 0

sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-ref-copy-soundness",
        "axiom": "snap=work (by-value per-step capture) <-> dict.copy() per yield",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "A-reference deep-model soundness: the by-value per-step "
                     "capture the impl encodes must equal the real dict.copy() / "
                     "partitions semantics. With gold applied, the real partitions "
                     "generator yields independent copies whose gathered history "
                     "equals the one-at-a-time truth with pairwise-distinct "
                     "neighbours -- exactly Result()[i]==state_at(i) (strictly "
                     "increasing). If the real callee disagreed, the deep model "
                     "would be unsound (AXIOM-UNSOUND).",
    },
    {
        "id": "ax-ref-copy-containment",
        "axiom": "snap=work (by-value per-step capture) <-> dict.copy() per yield",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "A-reference caller-domain containment: every per-step record "
                     "the model can reach (the working dict at each yield) is a "
                     "dict in dict.copy()'s (total) domain, so no caller-reachable "
                     "input escapes the primitive validated against. A reachable "
                     "record outside that domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
