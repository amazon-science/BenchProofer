"""properties.py — PBT falsification manifest for sympy__sympy-12419.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    diagonal_unit_entry(i: int, j: int) -> int

(the deep model of `Identity._entry(self, i, j)`: the (i, j) entry of an
identity matrix, decided 3-ways on the unchanged symbolic equality callee). Its
load-bearing contract (NO value precondition; a termination obligation plus the
post-conditions are the whole defence):

    Requires(MustTerminate(2))                                                # total: must deliver
    Ensures(Result() == ZERO or Result() == ONE or Result() == DEFERRED)        # totality
    Ensures(Implies(eq_class(i, j) == EQ_TRUE,    Result() == ONE))           # equal   -> unit
    Ensures(Implies(eq_class(i, j) == EQ_FALSE,   Result() == ZERO))          # unequal -> zero
    Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))         # UNDECIDED -> DEFERRED, NOT zero

What the spec actually defends, and the attacks it must survive:

  * The oracle is the @Pure @ContractOnly axiom `eq_class(i, j)` — the unchanged
    SymPy `Eq(i, j)` read 3-valued. It is GROUNDED in the inputs (a function of
    i, j) and its three branches PIN the result to a *distinct* cell tag. There
    is NO wrong "echo" available: the cell tags {ZERO=10, ONE=11, DEFERRED=12} are
    chosen DISJOINT from the equality codes {EQ_FALSE=0, EQ_TRUE=1, EQ_UNKNOWN=2}
    (see model.py's tag definitions, refinement.md §D), so `return eq_class(i, j)` is
    ill-typed against the contract (a {0,1,2} value can never satisfy
    `Result() in {10,11,12}`); the entry MUST be produced by genuinely branching
    on the classifier. So UNGROUNDED-ORACLE-ECHO is N/A — there is no opaque
    answer-key marker to echo; instead the positive controls confirm the cheapest
    HONEST impl that satisfies the pins is exactly a 3-way branch on `eq_class`.

  * The DISCRIMINATING clause (the substance of the issue) is
    `Implies(eq_class(i,j)==EQ_UNKNOWN, Result()==DEFERRED)`: an UNDECIDED index
    pair must yield the deferred delta, NOT the zero cell. The pre-patch code
    tested only STRUCTURAL identity (`if i == j: S.One else: S.Zero`), collapsing
    every structurally-distinct-but-undecided pair to S.Zero — so a later
    `Sum(In[i,j], ...)` over a range evaluated to 0 instead of n. Every uniqueness
    rival exploits a position where it returns the wrong cell on one of the three
    equality outcomes; the headline rival is the EXACT prepatch behaviour
    (UNKNOWN -> ZERO), modeled two ways (directly on EQ_UNKNOWN, and via the
    A-consumed `struct_eq` link the way model_prepatch.py does).

  * There is NO read-only (Acc(..., 1/2)) input: both parameters are plain
    immutable `int` identity tags passed by value, with NO permission predicate
    and NO value precondition. A Python int cannot be mutated in place and there
    is no array/object the impl could write through to satisfy a postcondition
    vacuously. So the FRAME-MUTATION class does not apply here (justified in the
    return 'assessment'); the closest analogue — rebinding the local `i`/`j` —
    changes no caller-visible state and the postcondition still quantifies over
    the ORIGINAL argument values via the @Pure `eq_class(i, j)`, so it cannot help
    a wrong impl. There is also NO raise / side-effect difference invisible to
    the value abstraction: the function only returns a cell tag.

  * VACUOUS NON-TERMINATION is a REAL attack class here (it was the recorded
    G-EQ / G-PANEL-1 counterexample family: a diverging `while` inserted before
    the gold 3-way branch verified against the value-only contract because a
    non-returning execution satisfies every Ensures vacuously, while its
    faithful real patch hangs `_entry` and times the F2P out). The contract
    carries `Requires(MustTerminate(2))` — the real `_entry` is a bounded,
    loop-free decision that always returns — so any impl that spins in a loop
    (no obligation-carrying invariant) or self-recurses at the same measure is
    rejected by Nagini's obligation system, not admitted vacuously. Two
    uniqueness rivals below pin exactly the recorded attack shapes.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end` (model.py's impl region), so
`markers.same_spec` is guaranteed and a rejection comes from the POST-CONDITIONS
catching wrong behaviour, never from a tampered spec. Each `expect:"reject"`
rival carries the refinement argument that its faithful real patch would NOT
resolve the F2P (`test_Identity`: `In[i,j] != 0` and the nested
`Sum(In[i,j], ...).subs(n,3).doit() == 3`). Axiom cases run the REAL sympy callee
(`Eq` / `==`) in Docker against the gold patch (mirroring + strengthening
axiom_check.py).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12419"
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
# # impl-end). Every variant replaces this single block; the spec view elides
# the impl region entirely, so same_spec is unaffected and a rejection is
# attributable solely to the swapped body, not to a touched contract.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT — BRANCH REORDER. The gold body tests
# EQ_TRUE, then EQ_FALSE, then falls through to DEFERRED. This control tests the
# UNDECIDED case FIRST, then EQ_FALSE, then falls through to ONE on the remaining
# (EQ_TRUE) outcome. Semantically identical (eq_class's trichotomy
# `Result() in {EQ_FALSE,EQ_TRUE,EQ_UNKNOWN}` makes the fall-through provably
# EQ_TRUE), different source order. No loop / no induction lemma, so nothing the
# verifier can't auto-discharge (PLAN caution N/A). If this fails to verify, the
# postcondition is over-fit to the exact gold branch order => SPEC-TOO-STRONG.
_POS_REORDER_IMPL = """    e = eq_class(i, j)
    if e == EQ_UNKNOWN:
        return DEFERRED
    elif e == EQ_FALSE:
        return ZERO
    return ONE"""
_POS_REORDER = _swap(_BASE, _GOLD_IMPL, _POS_REORDER_IMPL)

# (5b) Structurally-DIFFERENT but CORRECT — LOCAL-VARIABLE RESHAPE. The result is
# bound to a typed local `out` (set in each branch) and returned ONCE at the end,
# instead of three early returns. Same trichotomy decision, different control
# shape (single exit). If this fails, the spec is over-fit to the early-return
# spelling => SPEC-TOO-STRONG.
_POS_SINGLEEXIT_IMPL = """    e = eq_class(i, j)
    out = DEFERRED  # type: int
    if e == EQ_TRUE:
        out = ONE
    elif e == EQ_FALSE:
        out = ZERO
    return out"""
_POS_SINGLEEXIT = _swap(_BASE, _GOLD_IMPL, _POS_SINGLEEXIT_IMPL)

# (5c) HONEST CHEAPEST IMPL / no-wrong-echo control. The tags are disjoint from
# the eq codes, so there is no opaque oracle to echo; the cheapest honest impl is
# exactly the gold 3-way branch. This control keeps the gold body and adds, right
# before the fall-through return, an Assert that the impl genuinely branched on
# the classifier (the DEFERRED return is reached only when e is neither EQ_TRUE nor
# EQ_FALSE, i.e. EQ_UNKNOWN given trichotomy). It is CORRECT (expect="verify");
# its purpose is to demonstrate there is NO wrong echo that verifies — the oracle
# is grounded in (i, j), not an answer-key marker. (If a wrong echo COULD verify,
# this would instead be a SPEC-TOO-WEAK reject case; no such echo exists here.)
_ECHO_HONEST_IMPL = """    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    Assert(e == EQ_UNKNOWN)
    return DEFERRED"""
_ECHO_HONEST = _swap(_BASE, _GOLD_IMPL, _ECHO_HONEST_IMPL)

# (6) ADMISSIBILITY. There is no value precondition (only the termination
# obligation), so the contract must admit ANY input. The probe evaluates the
# @Pure classifier on two opaque F2P-shaped index tags (7 and 8, two distinct
# integer-symbol handles — the `In[i, j]` shape with distinct i, j) and asserts
# its trichotomy Ensures fires for that normal input, in-line at the top of the
# impl region; the gold body follows unchanged. (The probe is in-line rather
# than a self-call: under Requires(MustTerminate(2)) a same-measure self-call
# is correctly rejected by the obligation-leak check — that is exactly the
# anti-self-echo property pinned by the nonterm-self-recursion rival below.)
# If the probe cannot verify for a legitimate input => PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    _c = eq_class(7, 8)
    Assert(_c == EQ_FALSE or _c == EQ_TRUE or _c == EQ_UNKNOWN)
    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED"""
_ADMISS = _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) PREPATCH COLLAPSE — the headline rival, the EXACT issue. On the UNDECIDED
# outcome it returns ZERO instead of DEFERRED (the symbolic-collapse-to-zero bug).
# Everything else is gold. This is the behaviour of model_prepatch.py expressed
# directly on EQ_UNKNOWN. Rejection source: the DISCRIMINATING postcondition
# `Implies(eq_class(i,j)==EQ_UNKNOWN, Result()==DEFERRED)` — returning ZERO (=10) on
# the EQ_UNKNOWN branch contradicts `Result()==DEFERRED` (=12), and ZERO != DEFERRED.
_RIVAL_PREPATCH_IMPL = """    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return ZERO"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_IMPL, _RIVAL_PREPATCH_IMPL)

# (1b) PREPATCH via struct_eq — the SAME bug, but expressed exactly as
# model_prepatch.py does it: decide on the A-consumed STRUCTURAL-identity callee
# `struct_eq` (`if struct_eq(i,j): return ONE else: return ZERO`, the old
# `if i == j: S.One else: S.Zero`). The one-directional axiom link
# `struct_eq(i,j) -> eq_class(i,j)==EQ_TRUE` lets the verifier prove the ONE
# return correct when struct_eq holds, but does NOT give the converse
# `not struct_eq(i,j) -> eq_class(i,j) != EQ_UNKNOWN`; so on a structurally-
# distinct-but-undecided pair the ZERO return is unprovable against the EQ_UNKNOWN
# clause (and, secondarily, the EQ_TRUE clause for semantically-equal-but-
# structurally-distinct pairs). Rejection source: the EQ_UNKNOWN postcondition
# clause, with `struct_eq`'s one-directional Ensures consumed (exactly the G-DIFF
# differential).
_RIVAL_STRUCT_IMPL = """    if struct_eq(i, j):
        return ONE
    return ZERO"""
_RIVAL_STRUCT = _swap(_BASE, _GOLD_IMPL, _RIVAL_STRUCT_IMPL)

# (3) PARTIAL-DOMAIN — undecided handled as the UNIT cell instead of DEFERRED. A
# rival correct on the decidably-equal and decidably-unequal sub-domains but
# diverging on the UNDECIDED sub-domain, returning ONE (not DEFERRED). Faithful real
# patch: `_entry` returns `S.One` when `Eq(i,j)` is unevaluated (treat undecided
# as on-diagonal). This over-counts: `In[i, j]` for distinct symbolic i, j would
# be S.One, so off-diagonal symbolic entries are wrongly 1 and the nested
# `Sum(In[i,j], (i,0,n-1), (j,0,n-1)).subs(n,3).doit()` would be 9 (every cell 1),
# not 3 — FAILS the F2P. Rejection source: the EQ_UNKNOWN clause requires DEFERRED
# (=12); returning ONE (=11) contradicts it (ONE != DEFERRED).
_RIVAL_UNKNOWN_ONE_IMPL = """    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return ONE"""
_RIVAL_UNKNOWN_ONE = _swap(_BASE, _GOLD_IMPL, _RIVAL_UNKNOWN_ONE_IMPL)

# (3b) PARTIAL-DOMAIN — the DECIDABLY-EQUAL sub-domain wrong. Correct on FALSE and
# UNKNOWN, but returns DEFERRED (not ONE) on the EQ_TRUE outcome. Faithful real
# patch: `_entry` returns `KroneckerDelta(i,j)` even when `Eq(i,j) is S.true`
# (never collapse a decided-equal diagonal entry to S.One). The on-diagonal
# entries `In[i,i]` would then be KroneckerDelta instead of S.One, so the
# diagonal sum no longer evaluates to n=3 cleanly (the doit() relies on the
# diagonal being the literal S.One) — FAILS the F2P. Rejection source: the
# EQ_TRUE clause requires ONE (=11); returning DEFERRED (=12) contradicts it.
_RIVAL_TRUE_DELTA_IMPL = """    e = eq_class(i, j)
    if e == EQ_FALSE:
        return ZERO
    elif e == EQ_UNKNOWN:
        return DEFERRED
    return DEFERRED"""
_RIVAL_TRUE_DELTA = _swap(_BASE, _GOLD_IMPL, _RIVAL_TRUE_DELTA_IMPL)

# (3c) MASK-SWAP — equal/unequal cells transposed. Returns ZERO on EQ_TRUE and
# ONE on EQ_FALSE (UNKNOWN still DEFERRED). Faithful real patch: an `_entry` with the
# `is S.true`/`is S.false` returns swapped — `In[i,i]` becomes S.Zero and
# off-diagonal decided `In[i,i+1]` becomes S.One; the diagonal sum is then 0, not
# 3, and `In[i,j] != 0` fails for the diagonal — FAILS the F2P. Rejection source:
# the EQ_TRUE clause (ONE) and EQ_FALSE clause (ZERO) are both violated.
_RIVAL_SWAP_IMPL = """    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ZERO
    elif e == EQ_FALSE:
        return ONE
    return DEFERRED"""
_RIVAL_SWAP = _swap(_BASE, _GOLD_IMPL, _RIVAL_SWAP_IMPL)

# (2a) VACUOUS NON-TERMINATION — LOOP-BEFORE-RETURN. The RECORDED G-EQ /
# G-PANEL-1 attack shape: an infinite `while` inserted before the gold 3-way
# branch (the audit's atk_6 spun `while eq == eq: eq = eq` inside `_entry`).
# Against a value-only contract this verified — a non-returning execution
# satisfies every Ensures vacuously. Under Requires(MustTerminate(2)) the loop
# carries no obligation-taking invariant (and no decreasing measure), so Nagini
# must REJECT it ("Loop might not take all unsatisfied obligations from the
# context").
_RIVAL_NONTERM_LOOP_IMPL = """    spin = 0
    while spin >= 0:
        spin = spin + 1
    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED"""
_RIVAL_NONTERM_LOOP = _swap(_BASE, _GOLD_IMPL, _RIVAL_NONTERM_LOOP_IMPL)

# (2b) VACUOUS NON-TERMINATION — SELF-RECURSION. Echo every value postcondition
# through a same-measure self-call that never returns. The value clauses are
# "established" by the callee's own Ensures, but no execution delivers an
# entry. MustTerminate(2) gives the callee the same measure as the caller, so
# the self-call leaks the obligation => Nagini must REJECT ("Obligation leak
# check failed" / measure not decreasing).
_RIVAL_NONTERM_SELF_IMPL = """    return diagonal_unit_entry(i, j)"""
_RIVAL_NONTERM_SELF = _swap(_BASE, _GOLD_IMPL, _RIVAL_NONTERM_SELF_IMPL)

# (3d) CONSTANT DEFERRED (cheap supporting case, real refinement). Drops both decided
# branches and always returns DEFERRED. Faithful real patch: `_entry` unconditionally
# returns `KroneckerDelta(i,j)`. Then `In[i,i]` is KroneckerDelta not S.One, and
# the F2P `Sum(In[i,j], ...).doit() == 3` relies on decided entries being literal
# S.One/S.Zero — FAILS the F2P. Rejection source: the EQ_TRUE clause requires ONE
# (DEFERRED != ONE) and the EQ_FALSE clause requires ZERO (DEFERRED != ZERO); both are
# violated on the respective decided sub-domains.
_RIVAL_ALLDELTA_IMPL = """    empty = DEFERRED  # type: int
    return empty"""
_RIVAL_ALLDELTA = _swap(_BASE, _GOLD_IMPL, _RIVAL_ALLDELTA_IMPL)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl (tests EQ_UNKNOWN first, "
                  "EQ_FALSE next, falls through to ONE on the remaining EQ_TRUE outcome "
                  "via eq_class trichotomy). No loop/induction lemma. Must verify; if it "
                  "fails the postcondition is over-fit to the gold branch order => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-control-single-exit", "kind": "soundness", "expect": "verify",
     "module": _POS_SINGLEEXIT,
     "rationale": "structurally-different but CORRECT impl (single exit; result bound to "
                  "a typed local `out`, default DEFERRED, overwritten on the two decided "
                  "branches). Same trichotomy decision, different control shape. If it "
                  "fails the spec is over-fit to the early-return spelling => "
                  "SPEC-TOO-STRONG."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the cell tags {10,11,12} are disjoint from the eq codes {0,1,2}, so "
                  "there is NO oracle to echo (return eq_class(i,j) is ill-typed against "
                  "the contract). This cheapest honest impl keeps the gold 3-way branch "
                  "and asserts the DEFERRED return is reached only on EQ_UNKNOWN; it must "
                  "verify, demonstrating UNGROUNDED-ORACLE-ECHO is N/A (no wrong echo "
                  "exists)."},
    {"id": "admiss-classify-distinct-tags", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "there is no value precondition (only MustTerminate), so the contract "
                  "must admit any input; an in-line probe of the @Pure classifier on two "
                  "distinct opaque index tags (7, 8) — the In[i, j] distinct-index shape — "
                  "must verify, with its trichotomy Ensures asserted. In-line rather than "
                  "a self-call: a same-measure self-call is correctly rejected by the "
                  "obligation-leak check (pinned by nonterm-self-recursion). If the probe "
                  "fails for a normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "prepatch-unknown-to-zero", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this IS the issue's bug: on an UNDECIDED pair return the zero cell "
                   "instead of the deferred delta. Its faithful real patch returns "
                   "S.Zero when Eq(i,j) is unevaluated — exactly the pre-patch "
                   "symbolic-collapse behaviour: In[i,j] for distinct symbolic i,j "
                   "becomes 0, so `In[i,j] != 0` FAILS and the nested "
                   "`Sum(In[i,j],...).subs(n,3).doit()` evaluates to 0, not 3. "
                   "Definitively non-resolving.",
     "rationale": "rejection from the DISCRIMINATING postcondition "
                  "`Implies(eq_class(i,j)==EQ_UNKNOWN, Result()==DEFERRED)`: on the "
                  "EQ_UNKNOWN branch the impl returns ZERO (=10) but the clause requires "
                  "DEFERRED (=12), and ZERO != DEFERRED."},
    {"id": "prepatch-via-struct-eq", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_STRUCT,
     "refinement": "this is model_prepatch.py verbatim — the old `if i == j: S.One else: "
                   "S.Zero`, deciding on STRUCTURAL identity only. Its faithful real "
                   "patch is the UNPATCHED code, which treats every structurally-distinct "
                   "pair (incl. undecided symbolic pairs) as the zero cell and FAILS the "
                   "F2P exactly as the prepatch model does (G-DIFF).",
     "rationale": "rejection from the EQ_UNKNOWN clause with the A-consumed struct_eq "
                  "link: the axiom gives only struct_eq(i,j) -> eq_class==EQ_TRUE (one "
                  "direction); it does NOT give not struct_eq -> eq_class != EQ_UNKNOWN, "
                  "so on a structurally-distinct-but-undecided pair the ZERO return is "
                  "unprovable against Result()==DEFERRED (also fails the EQ_TRUE clause for "
                  "semantically-equal-but-structurally-distinct pairs)."},
    {"id": "nonterm-loop-before-return", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONTERM_LOOP,
     "refinement": "this is the RECORDED G-EQ/G-PANEL-1 counterexample shape (audit "
                   "atk_6/atk_7: an infinite `while` inserted before the gold 3-way "
                   "branch of `_entry`). Its faithful real patch hangs `Identity._entry` "
                   "on the first indexing call, so the F2P `test_Identity` (In[i,j], the "
                   "nested Sum(...).doit()) TIMES OUT (the recorded eval hit the 180s "
                   "guillotine) — definitively non-resolving.",
     "rationale": "rejection from the termination obligation: the contract carries "
                  "Requires(MustTerminate(2)) and the inserted loop has no obligation-"
                  "taking invariant (and no decreasing measure), so Nagini reports the "
                  "loop might not take all unsatisfied obligations; the value "
                  "postconditions alone would be satisfied only vacuously."},
    {"id": "nonterm-self-recursion", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONTERM_SELF,
     "refinement": "its faithful real patch is `return self._entry(i, j)` — infinite "
                   "recursion: the F2P's first `In[i, j]` hits RecursionError instead of "
                   "returning a cell value — FAILS the F2P.",
     "rationale": "rejection from the termination obligation: MustTerminate(2) gives the "
                  "callee the same measure as the caller, so the self-call leaks the "
                  "obligation (obligation-leak / measure check); every value clause would "
                  "otherwise be echoed vacuously from the callee's own Ensures."},
    {"id": "partial-unknown-to-one", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNKNOWN_ONE,
     "refinement": "a real patch that returns S.One (not KroneckerDelta) when Eq(i,j) is "
                   "unevaluated treats every undecided pair as on-diagonal: off-diagonal "
                   "symbolic entries In[i,j] become 1, so the nested "
                   "`Sum(In[i,j],(i,0,n-1),(j,0,n-1)).subs(n,3).doit()` is 9 (every cell "
                   "1), not 3 — FAILS the F2P. Faithful but non-resolving.",
     "rationale": "rejection from the EQ_UNKNOWN clause: it requires DEFERRED (=12); "
                  "returning ONE (=11) on the EQ_UNKNOWN branch contradicts it "
                  "(ONE != DEFERRED)."},
    {"id": "partial-true-to-delta", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRUE_DELTA,
     "refinement": "a real patch that returns KroneckerDelta even when Eq(i,j) is S.true "
                   "never collapses a decided-equal diagonal entry to S.One: In[i,i] "
                   "becomes KroneckerDelta(i,i) instead of S.One, so the diagonal sum no "
                   "longer cleanly doit()s to n=3 (the F2P relies on the diagonal being "
                   "the literal S.One) — FAILS the F2P. Faithful but non-resolving.",
     "rationale": "rejection from the EQ_TRUE clause "
                  "`Implies(eq_class(i,j)==EQ_TRUE, Result()==ONE)`: returning DEFERRED "
                  "(=12) on the EQ_TRUE branch contradicts it (DEFERRED != ONE)."},
    {"id": "mask-swap-equal-unequal", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP,
     "refinement": "a real patch with the `is S.true`/`is S.false` returns swapped maps "
                   "the diagonal to S.Zero and decided-unequal cells to S.One: the "
                   "diagonal sum is 0 not 3 and `In[i,i] != 0` fails — FAILS the F2P. "
                   "Faithful but non-resolving.",
     "rationale": "rejection from BOTH decided clauses: EQ_TRUE requires ONE but the impl "
                  "returns ZERO; EQ_FALSE requires ZERO but the impl returns ONE."},
    {"id": "constant-delta", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALLDELTA,
     "refinement": "a real patch that unconditionally returns KroneckerDelta(i,j) makes "
                   "In[i,i] a KroneckerDelta instead of S.One; the F2P "
                   "`Sum(In[i,j],...).doit() == 3` relies on decided entries being "
                   "literal S.One/S.Zero, so it FAILS. Cheap supporting case with a real "
                   "refinement.",
     "rationale": "rejection from the decided clauses: EQ_TRUE requires ONE (DEFERRED != "
                  "ONE) and EQ_FALSE requires ZERO (DEFERRED != ZERO); both violated on "
                  "their respective sub-domains."},
]


# ===========================================================================
# AXIOM LANE (Docker, real sympy callee under the gold patch)
# ===========================================================================
# Two A-consumed axioms: `eq_class` (== real `Eq(i,j)` read 3-valued) and
# `struct_eq` (== real Python `i == j`). The probes RUN the real callees (never
# scrape source — directive 4) on boundary + sentinel + fuzz index pairs and
# assert each axiom's Ensures. They mirror + strengthen axiom_check.py.
#
#   eq_class Ensures:  Result() in {EQ_FALSE,EQ_TRUE,EQ_UNKNOWN}      (trichotomy)
#                      Implies(i == j, Result() == EQ_TRUE)           (reflexivity)
#   struct_eq Ensures: Implies(i == j, Result())                     (reflexivity)
#                      Implies(Result(), eq_class(i,j) == EQ_TRUE)    (one-directional link)
#
# Containment: enumerate EXACTLY the callee-inputs the model can reach. The model
# has NO precondition and passes its OWN arguments (i, j) UNCHANGED to both
# eq_class and struct_eq; both axioms' Requires domains are UNRESTRICTED (any two
# index expressions / int tags). So every reachable input is trivially in-domain;
# the containment probe confirms the two axioms accept the full range of index
# pairs the real `_entry` is invoked with (bare symbols, integers, symbol
# arithmetic) without the model being able to reach anything outside.

# (1) axiom-soundness for eq_class + struct_eq. Runs real Eq and == on a pool of
# index pairs covering every shape `_entry` sees, asserts trichotomy +
# reflexivity for eq_class, reflexivity + the one-directional link for struct_eq,
# and EXERCISES the discriminating witness (structurally-distinct-but-undecided)
# so EQ_UNKNOWN is proven reachable (else the 3-valued spec would be vacuous and
# the EQ_UNKNOWN postcondition clause untested). Opens nothing; imports only
# stdlib + sympy. encoding="utf-8" not needed (no file reads) but harmless.
_AX_SOUND = r'''
import itertools, sys
from sympy import Eq, S, Symbol, Integer, symbols

EQ_FALSE, EQ_TRUE, EQ_UNKNOWN = 0, 1, 2

def real_eq_class(i, j):
    eq = Eq(i, j)
    if eq is S.true:
        return EQ_TRUE
    if eq is S.false:
        return EQ_FALSE
    return EQ_UNKNOWN

def real_struct_eq(i, j):
    return bool(i == j)

i, j, k = symbols('i j k', integer=True)
m, p = symbols('m p', integer=True, positive=True)
n = Symbol('n', integer=True, positive=True)
pool = [i, j, k, m, p, n,
        i + 1, i - 1, j + 1, i + k, i + k + 1, 2 * i, i + j,
        Integer(0), Integer(1), Integer(2), Integer(3), Integer(-1),
        S.Zero, S.One]

bad = []
# reflexivity for both axioms on every element.
for x in pool:
    if not real_struct_eq(x, x):
        bad.append(("struct_eq reflexivity", repr(x)))
    if real_eq_class(x, x) != EQ_TRUE:
        bad.append(("eq_class reflexivity (Eq(x,x) not S.true)", repr(x)))

# trichotomy + the one-directional link over all ordered pairs.
seen = {EQ_FALSE: 0, EQ_TRUE: 0, EQ_UNKNOWN: 0}
for a, b in itertools.product(pool, repeat=2):
    ec = real_eq_class(a, b)
    if ec not in (EQ_FALSE, EQ_TRUE, EQ_UNKNOWN):
        bad.append(("eq_class trichotomy", repr(a), repr(b), ec))
        continue
    seen[ec] += 1
    # struct_eq(a,b) => eq_class(a,b) == EQ_TRUE (the consumed link).
    if real_struct_eq(a, b) and ec != EQ_TRUE:
        bad.append(("struct->true link broken", repr(a), repr(b), ec))

# all three outcomes must be reachable (else the 3-valued spec is vacuous).
if seen[EQ_TRUE] == 0:
    bad.append(("no decidably-equal pair",))
if seen[EQ_FALSE] == 0:
    bad.append(("no decidably-unequal pair",))
if seen[EQ_UNKNOWN] == 0:
    bad.append(("no UNDECIDED pair (EQ_UNKNOWN clause untested)",))

# discriminating witness: structurally-distinct yet undecided (the substance of
# the change — structural-only decision returns ZERO, contract requires DEFERRED).
witnesses = [(i, j), (i, k), (j, k), (i, j + 1), (i, i + k)]
found = 0
for a, b in witnesses:
    if not real_struct_eq(a, b) and real_eq_class(a, b) == EQ_UNKNOWN:
        found += 1
if found == 0:
    bad.append(("no structurally-distinct-but-undecided witness",))

# decided sentinels: distinct concrete ints are S.false; i vs i+1 is S.false;
# i vs i+0 collapses to i (S.true) — the canonical boundaries.
if real_eq_class(Integer(2), Integer(3)) != EQ_FALSE:
    bad.append(("2 vs 3 not EQ_FALSE",))
if real_eq_class(i, i + 1) != EQ_FALSE:
    bad.append(("i vs i+1 not EQ_FALSE",))
if real_eq_class(i, i + 0) != EQ_TRUE:
    bad.append(("i vs i+0 not EQ_TRUE",))

if bad:
    print("AXIOM-UNSOUND eq_class/struct_eq:", bad[:10]); sys.exit(1)
print("eq_class + struct_eq SOUND on %d reflexive + %d ordered pairs; "
      "outcomes true=%d false=%d unknown=%d; %d structurally-distinct-but-"
      "undecided witnesses confirm the EQ_UNKNOWN->DEFERRED requirement; decided "
      "sentinels (2vs3, i vs i+1, i vs i+0) confirmed."
      % (len(pool), len(pool) ** 2, seen[EQ_TRUE], seen[EQ_FALSE],
         seen[EQ_UNKNOWN], found))
sys.exit(0)
'''

# (2) axiom-containment for eq_class + struct_eq. The model has NO precondition
# and passes its OWN unmodified arguments (i, j) to both callees; both axioms'
# Requires domains are UNRESTRICTED. So every callee-input the model can reach is
# trivially in-domain. This probe confirms the real callees accept (return a
# defined 3-valued outcome / a bool) on the FULL range of index-pair shapes the
# real Identity._entry is invoked with under the gold patch — the indexing path
# `In[i, j]` for symbols, integers, and symbol arithmetic — so there is no
# reachable input outside the covered (unrestricted) domain. Covering MORE than
# the caller reaches would be SOUND over-coverage, not a defect.
_AX_CONTAIN = r'''
import sys
from sympy import Eq, S, Symbol, Integer, symbols, MatrixSymbol
from sympy.matrices.expressions.matexpr import Identity

EQ_FALSE, EQ_TRUE, EQ_UNKNOWN = 0, 1, 2

def real_eq_class(i, j):
    eq = Eq(i, j)
    if eq is S.true:
        return EQ_TRUE
    if eq is S.false:
        return EQ_FALSE
    return EQ_UNKNOWN

i, j, k = symbols('i j k', integer=True)
n = Symbol('n', integer=True, positive=True)

# Exactly the index-pair shapes the model can reach: the model has NO Requires
# and forwards (i, j) unchanged, so the reachable callee-input set is "any two
# index tags". Enumerate the real shapes Identity._entry is invoked with.
reachable = [(i, j), (i, i), (i, k), (i + 1, j), (Integer(2), Integer(3)),
             (Integer(1), Integer(1)), (i, i + 1), (i, i + 0), (n, n)]

bad = []
for a, b in reachable:
    ec = real_eq_class(a, b)
    # axiom Requires domain is UNRESTRICTED: every pair must yield a defined
    # 3-valued outcome (no exception, no out-of-domain).
    if ec not in (EQ_FALSE, EQ_TRUE, EQ_UNKNOWN):
        bad.append(("eq_class out of domain", repr(a), repr(b), ec))
    se = bool(a == b)  # struct_eq Requires also unrestricted: must return a bool
    if not isinstance(se, bool):
        bad.append(("struct_eq not a bool", repr(a), repr(b)))

# Confirm the real Identity._entry (gold patch) actually drives these callees on
# a symbolic index pair without restricting the input domain (reaches _entry).
In = Identity(n)
entry_ij = In[i, j]        # distinct symbolic indices -> the EQ_UNKNOWN path
entry_ii = In[i, i]        # identical index -> EQ_TRUE path -> S.One
if entry_ii != S.One:
    bad.append(("In[i,i] not S.One under gold", repr(entry_ii)))
if entry_ij == S.Zero:
    bad.append(("In[i,j] collapsed to 0 (prepatch bug present)", repr(entry_ij)))

if bad:
    print("AXIOM-TOO-WEAK-FOR-CALLER eq_class/struct_eq:", bad[:10]); sys.exit(1)
print("containment OK: model has no precondition and forwards (i,j) unchanged to "
      "eq_class/struct_eq (both Requires domains unrestricted), so every reachable "
      "index pair is in-domain; real Identity._entry under the gold patch drives "
      "the callees on %d shapes with In[i,i]==S.One and In[i,j] NOT collapsed to 0."
      % (len(reachable),))
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-eq-struct-sound", "axiom": "eq_class", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_SOUND,
     "rationale": "runs the REAL Eq + == on boundary/sentinel/fuzz index pairs; if the "
                  "real callee violates eq_class trichotomy/reflexivity or the struct_eq "
                  "one-directional link, or no EQ_UNKNOWN pair is reachable, the axioms "
                  "over-claim => AXIOM-UNSOUND. The structurally-distinct-but-undecided "
                  "witness proves the EQ_UNKNOWN->DEFERRED clause is non-vacuous."},
    {"id": "ax-eq-struct-containment", "axiom": "eq_class", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAIN,
     "rationale": "the model has no precondition and forwards (i,j) unchanged; both "
                  "axioms' Requires domains are unrestricted, so every reachable index "
                  "pair is in-domain. A reachable pair on which the real callee is "
                  "undefined / out-of-domain would be AXIOM-TOO-WEAK-FOR-CALLER. Also "
                  "confirms the gold Identity._entry drives the callees (In[i,i]==S.One, "
                  "In[i,j] not collapsed to 0)."},
]
