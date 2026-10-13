"""properties.py — PBT falsification manifest for sympy__sympy-15017.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    array_element_count(shape: List[int]) -> int

(the deep model of `ImmutableDenseNDimArray._new`'s `self._loop_size = ...`
assignment — the array's stored-element count reported by `NDimArray.__len__`).
Its load-bearing contract:

    Requires(Acc(list_pred(shape), 1 / 2))                                  # READ-ONLY input
    Requires(MustTerminate(2))                                              # total correctness: the count must ANSWER
    Ensures (Acc(list_pred(shape), 1 / 2))                                  # gives the half back
    Ensures (Result() == axis_count(ToSeq(shape), len(shape)))              # the full product (grounded oracle)
    Ensures (Implies(len(shape) == 0, Result() == 1))                       # the DISCRIMINATING empty-product clause

What the spec defends, and the attacks it must survive:

  * TOTAL CORRECTNESS — NO VACUOUS DIVERGENCE. Nagini verifies partial
    correctness by default: a diverging impl (bare self-recursion, an endless
    loop) satisfies every value `Ensures` vacuously because no execution
    reaches the return. This is the exact spec-too-weak class the G-PANEL-1
    auditor exploited (a non-terminating same-spec impl verified against the
    value-only spec). The contract now carries `Requires(MustTerminate(2))`:
    every loop on the path to the return must consume the obligation with a
    strictly decreasing, bounded-below measure, and the routine may not
    re-invoke itself (measure 2 admits the @Pure helpers only). The
    `weak-nonterminating` rival below MUST be rejected by the obligation
    system.

  * READ-ONLY INPUT. `shape` carries only HALF permission `Acc(list_pred(shape),
    1/2)`, returned unchanged by the postcondition. So the FRAME-MUTATION class
    APPLIES and is MANDATORY: a rival that WRITES to `shape` (`shape[0] = ...` /
    `shape.append(...)`) to wedge the postcondition vacuously needs FULL
    permission and must be rejected for INSUFFICIENT PERMISSION by the Viper
    permission system (the gold contract is kept verbatim so the rejection is
    attributable solely to the write).

  * GROUNDED ORACLE, NO WRONG ECHO. The result is pinned to `axis_count(
    ToSeq(shape), len(shape))`, a `@Pure` prefix-recursive fold that is FULLY a
    function of the input `shape` (it unfolds to `1 * shape[0] * ... *
    shape[k-1]`). It is NOT an opaque answer-key marker, so there is no WRONG
    echo: `return axis_count(ToSeq(shape), len(shape))` is the cheapest HONEST
    impl and is CORRECT — it is included as a positive control (if it failed to
    verify, the spec would be over-fit to the loop spelling => SPEC-TOO-STRONG).
    UNGROUNDED-ORACLE-ECHO is therefore N/A (no answer-key to echo); see the
    return 'assessment'.

  * DISCRIMINATING CLAUSE. The substance of the issue (`len` of a rank-0 array
    must be 1, not 0) lives in `Implies(len(shape)==0, Result()==1)` and,
    equivalently, in `axis_count(s,0)==1` inside the main product clause. The
    prepatch `reduce(mul, shape) if shape else 0` returned 0 on the empty shape;
    `model_prepatch.py` reproduces that (`if len(shape)==0: return 0`) and fails
    exactly this clause (G-DIFF). The headline uniqueness rival is that prepatch.

  * NO CONTROL-FLOW / RAISE / SIDE-EFFECT difference is invisible to the value
    abstraction. The modeled unit returns ONLY the integer count; the downstream
    raise behaviour the F2P observes (`rank_zero_array[0] == x` instead of a
    ValueError) is driven ENTIRELY by this same `_loop_size` value via
    `_parse_index` (raises iff `index >= self._loop_size`), so the value
    abstraction is complete and CONTROL-FLOW-EFFECT is N/A (justified in
    'assessment').

  * NO AXIOMS. `meta.axioms == []`; the changed op (`functools.reduce(mul,
    shape, 1)`) is pure integer arithmetic modeled DEEPLY by `axis_count`. There
    is no `@ContractOnly` callee and no A-reference deep model, so AXIOM_TESTS is
    empty (G-AX is vacuous) — no real callee to fuzz in Docker.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the
nested `# invariants` region is INSIDE impl and is elided by `spec_view`, so
reshaping the loop/invariants does NOT touch the frozen spec). `markers.same_spec`
is therefore guaranteed and a rejection comes from the POST-CONDITIONS / the
permission system, never from a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P (`test_ndim_array_initiation`: rank-0 `len == 1` and the now-succeeding
`rank_zero_array[0] == x`; plus the P2P products `0`, `1`, `81`).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15017"
FLOAT_ENCODING = None  # meta.json float_encoding is null


# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark — the WHOLE gold impl body (strictly INSIDE # impl-start /
# # impl-end, including the nested # invariants region). Every variant replaces
# this single block; the spec view elides the impl region entirely (nested
# invariants included), so same_spec is unaffected and a rejection is
# attributable solely to the swapped body, not to a touched contract.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    acc = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(shape) - i + 1,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT — SINGLE-EXIT / LOCAL RESHAPE. The
# gold body returns `acc` directly; this control binds the running product to a
# typed local `out`, computed by the SAME forward loop with the SAME invariants
# and the SAME unfold lemma, and returns `out` once at the end. The executable
# shape differs (single exit, distinct variable name) while every gold proof
# obligation it still needs is KEPT (the three invariants and the unfold Assert)
# — so it does NOT introduce a proof gap (PLAN pilot-calibration #2). It does NOT
# flip the loop direction (no fold-commutativity lemma needed — PLAN caution #3).
# If this fails to verify, the postcondition is over-fit to the exact gold loop
# spelling => SPEC-TOO-STRONG.
_POS_SINGLEEXIT_IMPL = """    out = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(out == axis_count(ToSeq(shape), i))
        # Discharge the termination obligation identically to gold.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        out = out * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return out"""
_POS_SINGLEEXIT = _swap(_BASE, _GOLD_IMPL, _POS_SINGLEEXIT_IMPL)

# (5b) GROUNDED-ORACLE HONEST CHEAPEST IMPL / no-wrong-echo control. The result
# pin `axis_count(ToSeq(shape), len(shape))` is a function of the input, fully
# unfolded — there is no opaque answer-key to echo. The cheapest HONEST impl is
# to return that grounded fold directly. It is CORRECT (expect="verify"); its
# purpose is to demonstrate UNGROUNDED-ORACLE-ECHO is N/A (there is no WRONG echo
# that verifies — echoing the grounded oracle IS the right answer). It keeps the
# half-permission read of `shape` (ToSeq reads, does not write) so the
# Ensures(Acc(list_pred(shape),1/2)) is preserved.
_ECHO_HONEST_IMPL = """    return axis_count(ToSeq(shape), len(shape))"""
_ECHO_HONEST = _swap(_BASE, _GOLD_IMPL, _ECHO_HONEST_IMPL)

# (6) ADMISSIBILITY. The precondition is `Acc(list_pred(shape), 1/2)` plus the
# total-correctness obligation `MustTerminate(2)`. A normal F2P-shaped input is
# a concrete list of axis lengths; the function must accept it. This control
# confirms the spec ADMITS the reads a normal input needs: it reads `len(shape)`
# and (when non-empty) re-reads an element under the half-permission before
# running the gold body. NO self-call: under measure 2 the routine may not
# re-invoke itself (a self-call could never discharge its own obligation), so
# admissibility is shown by the in-domain reads instead — no write, no proof
# gap. If the precondition rejected a legitimate normal input =>
# PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    # Admissibility: a normal (possibly empty) list of axis lengths is
    # in-domain; the half-permission admits reading its length and elements.
    Assert(len(shape) >= 0)
    if len(shape) > 0:
        Assert(shape[0] == shape[0])  # read admitted at 1/2
    acc = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # Discharge the termination obligation identically to gold.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc"""
_ADMISS = _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL)


# ===========================================================================
# FRAME-MUTATION (MANDATORY — read-only input) — expect "reject"
# ===========================================================================

# (1) FRAME-MUTATION via index write. The impl OVERWRITES the read-only input
# `shape[0] = 1` before computing the gold product, then returns the gold value.
# `shape` carries only `Acc(list_pred(shape), 1/2)`; an indexed store requires
# FULL permission `Acc(list_pred(shape), 1)`. So this must be rejected for
# INSUFFICIENT PERMISSION — the rejection is attributable solely to the write
# (the gold postcondition and the whole gold loop are kept verbatim). A
# byte-fuzzer never thinks to mutate the input; this is the project's #1 weakness
# class. (The store is guarded by `len(shape) > 0` only so the assignment is
# type-correct; the permission failure does not depend on the guard.)
_FRAME_WRITE_IMPL = """    if len(shape) > 0:
        shape[0] = 1
    acc = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # Discharge the termination obligation identically to gold, so the
        # reject stays on the PERMISSION system, not an obligation leak.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc"""
_FRAME_WRITE = _swap(_BASE, _GOLD_IMPL, _FRAME_WRITE_IMPL)

# (1b) FRAME-MUTATION via append. A different write shape: `shape.append(1)`
# (extend the list with a length-1 axis — which would NOT change the gold product
# value, so the impl tries to mutate the input "harmlessly"). Appending mutates
# the list and needs FULL permission on `list_pred(shape)`; with only the half
# the spec must reject it for INSUFFICIENT PERMISSION. Same attack class, distinct
# mutation operation — confirms the rejection is the permission system, not a
# quirk of indexed stores. (After the append the gold loop is still run over the
# now-extended list, but the impl never gets that far: the append fails to verify.)
_FRAME_APPEND_IMPL = """    shape.append(1)
    acc = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # Discharge the termination obligation identically to gold, so the
        # reject stays on the PERMISSION system, not an obligation leak.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc"""
_FRAME_APPEND = _swap(_BASE, _GOLD_IMPL, _FRAME_APPEND_IMPL)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) PREPATCH COLLAPSE — the headline rival, the EXACT issue. On the empty
# (rank-zero) shape it returns 0 instead of the empty product 1; otherwise it
# folds shape[0] then the remaining axes (seed = first axis). This is
# model_prepatch.py's impl verbatim — `reduce(mul, shape) if shape else 0`.
# Rejection source: the DISCRIMINATING postcondition
# `Implies(len(shape)==0, Result()==1)` (and the main clause
# `Result()==axis_count(ToSeq(shape),len(shape))`, whose base case
# `axis_count(s,0)==1` is violated): for the empty shape the impl returns 0 but
# the spec requires 1, and 0 != 1.
_RIVAL_PREPATCH_IMPL = """    if len(shape) == 0:
        return 0
    acc = shape[0]
    i = 1
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(1 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # Discharge the termination obligation identically to gold, so the
        # reject stays on the SPEC (the empty-shape clause), not an obligation leak.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_IMPL, _RIVAL_PREPATCH_IMPL)

# (2) PARTIAL-DOMAIN — empty shape returns 0, non-empty correct. A leaner variant
# of the prepatch that keeps the gold seed-1 forward loop but SHORT-CIRCUITS the
# empty shape to 0 (the prepatch `... else 0`). Correct on every non-empty
# domain (rank-1 `(1,)`->1, rank-1 `(0,)`->0, rank-4 `(3,3,3,3)`->81) but wrong
# on the rank-zero sub-domain. This is precisely the sub-domain the F2P now
# exercises. Rejection source: `Implies(len(shape)==0, Result()==1)` — returns 0,
# spec requires 1.
_RIVAL_EMPTY_ZERO_IMPL = """    if len(shape) == 0:
        return 0
    acc = 1
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        # Discharge the termination obligation identically to gold, so the
        # reject stays on the SPEC (the empty-shape clause), not an obligation leak.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc"""
_RIVAL_EMPTY_ZERO = _swap(_BASE, _GOLD_IMPL, _RIVAL_EMPTY_ZERO_IMPL)

# (3) PARTIAL-DOMAIN — drops the FIRST axis. Seeds acc=1 but starts the fold at
# i=1, omitting shape[0] from the product. Correct only when shape[0]==1 (or the
# empty shape); wrong on every shape whose first axis length != 1. The invariant
# is honestly weakened to `acc == axis_count(ToSeq(shape), i) / shape[0]`-shaped
# tracking is NOT attempted — instead the loop tracks the product of axes 1..i,
# so the final value is the product MISSING shape[0]. Rejection source: the main
# clause `Result()==axis_count(ToSeq(shape),len(shape))` — the returned value
# omits shape[0], so for `(3,3,3,3)` it is 27 not 81. (Modeled with a sound
# invariant so the rejection is the postcondition, not a proof artifact.)
_RIVAL_SKIP_FIRST_IMPL = """    acc = 1
    i = 1
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(1 <= i and i <= len(shape) or len(shape) == 0)
        Invariant(i >= 1)
        # Discharge the termination obligation, so the reject stays on the
        # SPEC (the main product clause), not an obligation leak.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        acc = acc * shape[i]
        i = i + 1
    return acc"""
_RIVAL_SKIP_FIRST = _swap(_BASE, _GOLD_IMPL, _RIVAL_SKIP_FIRST_IMPL)

# (4) CONSTANT ONE (cheap supporting case, real refinement). Always returns 1,
# regardless of the axes. Correct ONLY on the empty shape and on shapes whose
# product is 1 (e.g. `(1,)`); wrong on `(0,)`->0 and `(3,3,3,3)`->81. Faithful
# real patch: `self._loop_size = 1` unconditionally — `len` would report 1 for
# every array. Then `len(ImmutableDenseNDimArray([], shape=(0,)))` would be 1
# (the F2P asserts 0) and `len(...range(81), (3,3,3,3))` would be 1 (the F2P/P2P
# asserts 81) — FAILS. Rejection source: the main clause
# `Result()==axis_count(ToSeq(shape),len(shape))` — for `(0,)` axis_count==0 != 1.
_RIVAL_CONST_ONE_IMPL = """    return 1"""
_RIVAL_CONST_ONE = _swap(_BASE, _GOLD_IMPL, _RIVAL_CONST_ONE_IMPL)

# (5) ACC SEED ZERO (cheap supporting case, real refinement). Initializes the
# fold accumulator to 0 instead of 1, so the running product collapses to 0 for
# every shape (0 * anything == 0). Faithful real patch: `reduce(mul, shape, 0)`
# — `len` would report 0 for EVERY array (rank-0 `0` not `1`, rank-4 `0` not
# `81`) — FAILS both the F2P rank-0 clause and the P2P products. Rejection
# source: the main clause for non-empty positive-product shapes (0 != 81) AND the
# empty clause `Implies(len(shape)==0, Result()==1)` (0 != 1).
_RIVAL_SEED_ZERO_IMPL = """    acc = 0
    i = 0
    while i < len(shape):
        # invariants-start
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == 0)
        # Discharge the termination obligation, so the reject stays on the
        # SPEC (the value clauses), not an obligation leak.
        Invariant(MustTerminate(len(shape) - i + 1))
        # invariants-end
        acc = acc * shape[i]
        i = i + 1
    return acc"""
_RIVAL_SEED_ZERO = _swap(_BASE, _GOLD_IMPL, _RIVAL_SEED_ZERO_IMPL)

# (6) NON-TERMINATION (vacuous divergence) — the class the G-PANEL-1 auditor
# actually exploited. The impl spins forever (`while 0 <= i` with `i`
# increasing), so no execution reaches the return and every value postcondition
# is satisfiable only vacuously. Before the `MustTerminate(2)` obligation was
# added to the contract, this same-spec impl VERIFIED (Nagini checks partial
# correctness by default) — the recorded spec-too-weak defect. Under
# `Requires(MustTerminate(2))` the spinning loop takes no termination
# obligation and has no decreasing measure, so Nagini's OBLIGATION system must
# reject it. The invariant is relaxed to what the spinning loop actually
# maintains — the reject must come from the obligation system, not a broken
# proof.
_RIVAL_NONTERM_IMPL = """    # Vacuous non-termination: spin forever, never deliver the count.
    acc = 1
    i = 0
    while 0 <= i:
        # invariants-start
        Invariant(0 <= i)
        # invariants-end
        i = i + 1
    return acc"""
_RIVAL_NONTERM = _swap(_BASE, _GOLD_IMPL, _RIVAL_NONTERM_IMPL)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-single-exit", "kind": "soundness", "expect": "verify",
     "module": _POS_SINGLEEXIT,
     "rationale": "structurally-different but CORRECT impl (single exit; running product "
                  "bound to a typed local `out`, same forward loop, same three invariants, "
                  "same unfold lemma Assert — every needed gold proof obligation kept; loop "
                  "direction unchanged so no fold-commutativity lemma needed). If it fails, "
                  "the postcondition is over-fit to the exact gold spelling => SPEC-TOO-STRONG."},
    {"id": "honest-grounded-oracle-return", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the result pin axis_count(ToSeq(shape),len(shape)) is GROUNDED in the "
                  "input (a fully-unfolded function of shape), not an opaque answer-key, so "
                  "returning it directly is the cheapest HONEST impl and is CORRECT. Must "
                  "verify; demonstrates UNGROUNDED-ORACLE-ECHO is N/A (no wrong echo "
                  "exists). If it fails, the spec is over-fit to the loop spelling => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-reads", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the precondition Acc(list_pred(shape),1/2) + MustTerminate(2) must admit "
                  "a normal F2P-shaped list of axis lengths; this control reads len(shape) "
                  "and (when non-empty) re-reads an element under the half-permission before "
                  "the gold body. (No self-call: under measure 2 the routine may not "
                  "re-invoke itself.) If a legitimate normal input is rejected => "
                  "PRECOND-TOO-STRONG."},

    # ---- frame-mutation (MANDATORY, read-only input) — must reject ----
    {"id": "frame-mutation-index-write", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_WRITE,
     "refinement": "an impl that overwrites the input shape (`shape[0] = 1`) does not "
                   "correspond to any faithful real patch: `_new` receives the sympified "
                   "`shape` Tuple and must NOT mutate it to compute `_loop_size` (a Tuple is "
                   "immutable; rewriting the caller's shape would corrupt the array's "
                   "declared dimensions, changing `.shape`/`.rank()` and failing the F2P "
                   "`arr_with_no_elements.rank()==1` / `rank_zero_array.shape==()`). It is "
                   "non-resolving by construction.",
     "rationale": "rejection from the PERMISSION SYSTEM: `shape` holds only "
                  "Acc(list_pred(shape),1/2); an indexed store `shape[0]=1` requires FULL "
                  "permission Acc(list_pred(shape),1). The gold postcondition is kept "
                  "verbatim, so the failure (INSUFFICIENT PERMISSION) is attributable solely "
                  "to the write."},
    {"id": "frame-mutation-append", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_APPEND,
     "refinement": "appending an axis to the input shape (`shape.append(1)`) mutates the "
                   "caller's shape sequence — no faithful real patch does this: `_new` "
                   "stores `self._shape = shape` and reports `.rank() == len(shape)`, so "
                   "appending would change the reported rank (F2P `rank()==1`/`rank()==0` "
                   "would fail). Non-resolving.",
     "rationale": "rejection from the PERMISSION SYSTEM: `list.append` mutates list_pred and "
                  "requires FULL permission; only the half is held. Distinct mutation "
                  "operation from the index write — confirms the rejection is the permission "
                  "system, not an index-store quirk."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "prepatch-empty-zero-firstseed", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this IS the prepatch (`reduce(mul, shape) if shape else 0`, "
                   "model_prepatch.py verbatim): for the empty (rank-0) shape it returns 0, "
                   "so `len(sympy.Array(x)) == 0` — exactly the bug the issue reports and "
                   "the F2P now forbids (`len(rank_zero_array) == 1`; and the downstream "
                   "`rank_zero_array[0]` would still raise ValueError since "
                   "`0 >= _loop_size==0`). Definitively non-resolving (G-DIFF).",
     "rationale": "rejection from `Implies(len(shape)==0, Result()==1)` and the main clause "
                  "whose base case is axis_count(s,0)==1: for the empty shape the impl "
                  "returns 0, the spec requires 1, and 0 != 1. (Non-empty shapes verify; the "
                  "ONLY observable divergence is the empty-shape clause.)"},
    {"id": "partial-domain-empty-zero", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY_ZERO,
     "refinement": "keeps the seed-1 forward loop (so non-empty shapes are correct: "
                   "`(1,)`->1, `(0,)`->0, `(3,3,3,3)`->81) but short-circuits the empty "
                   "shape to 0 — exactly the F2P sub-domain `len(sympy.Array(x))`. Its "
                   "faithful real patch keeps the `if shape else 0` guard, so rank-0 `len` "
                   "stays 0 and `rank_zero_array[0]` keeps raising — FAILS the F2P. "
                   "Non-resolving.",
     "rationale": "rejection from the empty-shape clause `Implies(len(shape)==0, "
                  "Result()==1)`: 0 != 1 on the rank-zero sub-domain, while every non-empty "
                  "sub-domain matches the gold (a true partial-domain divergence)."},
    {"id": "partial-domain-skip-first-axis", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SKIP_FIRST,
     "refinement": "drops shape[0] from the product (folds axes 1..k-1 only). Correct only "
                   "when the first axis length is 1; wrong otherwise. Its faithful real "
                   "patch is `reduce(mul, shape[1:], 1)` — for `(3,3,3,3)` the array would "
                   "report `len == 27`, not 81, failing the P2P/F2P "
                   "`len(...range(81),(3,3,3,3)) == 81`. Non-resolving.",
     "rationale": "rejection from the main clause Result()==axis_count(ToSeq(shape),"
                  "len(shape)): the returned value omits shape[0] (its weakened invariant "
                  "honestly tracks the product of axes 1..i), so it does not equal the full "
                  "product for any shape with shape[0] != 1."},
    {"id": "constant-one", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONST_ONE,
     "refinement": "always returns 1 (`self._loop_size = 1`). `len` would report 1 for every "
                   "array: `len(ImmutableDenseNDimArray([], shape=(0,)))` would be 1 (F2P "
                   "asserts 0) and `len(...range(81),(3,3,3,3))` would be 1 (F2P/P2P asserts "
                   "81) — FAILS. Cheap supporting case with a real refinement.",
     "rationale": "rejection from the main clause: for `(0,)` axis_count(ToSeq(shape),1)==0 "
                  "(a zero-length axis), but the impl returns 1, and 1 != 0."},
    {"id": "acc-seed-zero", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SEED_ZERO,
     "refinement": "seeds the fold accumulator at 0 (`reduce(mul, shape, 0)`), collapsing "
                   "every product to 0; `len` would report 0 for every array (rank-0 0 not "
                   "1, rank-4 0 not 81) — FAILS both the F2P rank-0 clause and the P2P "
                   "products. Cheap supporting case with a real refinement.",
     "rationale": "rejection from BOTH clauses: the main clause (0 != 81 for `(3,3,3,3)`) "
                  "and the empty clause `Implies(len(shape)==0, Result()==1)` (0 != 1)."},
    {"id": "weak-nonterminating", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONTERM,
     "refinement": "the rival never returns: it spins in an unbounded loop, so every value "
                   "postcondition holds only vacuously and no element count is ever "
                   "delivered. Its faithful real patch is a `_new` that hangs computing "
                   "`_loop_size` — constructing ANY ImmutableDenseNDimArray would never "
                   "return, every F2P/P2P test times out — it does NOT resolve. This is "
                   "the attack class the G-PANEL-1 auditor exploited before the "
                   "MustTerminate obligation was added.",
     "rationale": "MUST reject via the OBLIGATION system: Requires(MustTerminate(2)) "
                  "forces every loop on the path to the return to carry a strictly "
                  "decreasing, bounded-below termination measure; the spinning loop has "
                  "none, so Nagini rejects it (obligation leak). Rejection source: the "
                  "termination obligation, not a value clause — demonstrating the spec no "
                  "longer admits vacuous divergence."},
]


# ===========================================================================
# AXIOM LANE — none.
# ===========================================================================
# meta.axioms == [] and deep_model_references == []. The only operation the fix
# changes is the running product of the axis lengths with the empty-product seed
# 1 (`functools.reduce(lambda x,y: x*y, shape, 1)`), which is PURE INTEGER
# ARITHMETIC modeled DEEPLY by the prefix-recursive @Pure axis_count (base case
# axis_count(s,0)==1). There is no @ContractOnly axiom (A-consumed) and no
# deep-model-vs-real-callee equivalence (A-reference) to validate; no
# axiom_check.py is shipped and G-AX is vacuous. So there is no real callee to
# fuzz in Docker.
AXIOM_TESTS = []  # type: list
