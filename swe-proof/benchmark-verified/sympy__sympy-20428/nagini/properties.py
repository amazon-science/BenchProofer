"""properties.py — PBT falsification battery for sympy__sympy-20428.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only a
# impl-start .. # impl-end region is edited via _swap) and are checked by Nagini
verify + markers.same_spec. There are NO @ContractOnly axioms / A-reference
consumed axioms in this bundle (meta.axioms == []; the mathematical-zero facet
is modelled directly by the Coeff.mzero field, validated == the real
Expr.is_zero out-of-band by axiom_check.py / G-AX), so AXIOM_TESTS = [].

DEFENDED SURFACE (why these cases and not byte-fuzz):

  Two modeled functions over a Coeff carrier with TWO int facets:
    lit0  -- 1 iff the structural shape IS the bare zero literal Integer(0)
    mzero -- 1 iff the coefficient denotes zero MATHEMATICALLY (Expr.is_zero)
  Class invariant (constructor): Implies(lit0 == 1, mzero == 1). The converse is
  deliberately NOT imposed, so the ONLY state where lit0 and mzero disagree is
  (lit0 == 0, mzero == 1) -- the issue's coefficient: a non-trivial radical form
  that denotes zero. (The state lit0==1, mzero==0 is unreachable by the invariant.)

  coeff_truthy(c) -> bool
    inputs are READ-ONLY: Requires Acc(c.lit0, 1/2) and Acc(c.mzero, 1/2).
    LOAD-BEARING postcondition: Result() == (c.mzero == 0). Truthiness must track
    the MATHEMATICAL value mzero, NOT the structural shape lit0. This is exactly
    the gold change `f.ex != 0` (structural, == lit0) -> `not f.ex.is_zero`
    (mathematical, == mzero).

  strip_constant_len(c) -> int
    inputs are READ-ONLY (same Acc(...,1/2)). LOAD-BEARING postconditions:
    Implies(c.mzero == 1, Result() == 0) and Implies(c.mzero == 0, Result() == 1)
    (plus Result() in {0,1}). The stored constant-poly list collapses to the
    canonical [] (zero poly) EXACTLY when the coefficient denotes zero -- the
    dup_strip / clear_denoms consequence the F2P test_issue_20427 observes.

  has_readonly_input = True (both functions take Acc(c.*, 1/2)). The
  FRAME-MUTATION class is therefore MANDATORY and the project's #1 weakness: a
  rival that WRITES c.mzero / c.lit0 to satisfy the postcondition vacuously must
  be REJECTED for INSUFFICIENT PERMISSION (only 1/2 share held). A byte-fuzzer
  never thinks to mutate the input.

  UNGROUNDED-ORACLE ECHO is vacuous here: the postcondition is pinned to the
  model FIELD c.mzero, which is itself the ground truth (a function of the input
  fully visible in the contract), not an opaque @Pure answer-key sitting in the
  module that an impl could echo without doing the work. There is no "wrong echo"
  to build -- the cheapest honest impl (read c.mzero) IS the correct impl. Per
  directive 2 we instead carry honest cheapest/structural positive controls.

  CONTROL-FLOW-EFFECT is N/A: both functions return a pure value (bool /
  int 0|1), have no raise/side-effect path in the spec, and there is no
  capability token to discriminate -- the value abstraction captures everything
  observable. (See assessment.)

  VACUOUS NON-TERMINATION is defended by an explicit total-correctness
  obligation: both functions carry Requires(MustTerminate(k)) (and the Coeff
  constructor MustTerminate(1), so admissibility witnesses can still be
  built). This class is exactly the spec-too-weak hole the G-PANEL-1 auditor
  exploited before the obligation was added (atk_8: an infinite
  `while (...) >= 0: pass` spin inserted before the correct return verified
  against the value-only spec, because every value postcondition holds
  vacuously on a diverging trace -- while the corresponding real patch hangs
  __bool__ and times out the F2P test). Under MustTerminate a loop with no
  decreasing termination measure leaks the caller's obligation and Nagini
  rejects it ("Obligation leak check failed"). The nonterm-* cases below pin
  this rejection for both modeled functions.

  The genuine uniqueness attacks are PARTIAL-DOMAIN rivals that are correct on
  the agreeing states (lit0 == mzero) but key the answer on the STRUCTURAL facet
  lit0 instead of the mathematical facet mzero, diverging on exactly the
  discriminating state (lit0 == 0, mzero == 1). `return c.lit0 == 0` is the
  PRE-PATCH bug verbatim (model_prepatch.py); it is the whole point of the issue.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20428"
FLOAT_ENCODING = None  # meta.float_encoding is null; pure int 0/1 carrier, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgical anchors. Every variant edits ONLY text between # impl-start ..
# # impl-end (guarantees same_spec). Two impl regions exist (one per function).
# ---------------------------------------------------------------------------

# coeff_truthy gold impl (unique substring).
_CT_GOLD = "    return c.mzero == 0\n"

# strip_constant_len gold impl (unique substring).
_SL_GOLD = (
    "    if coeff_truthy(c):\n"
    "        return 1\n"
    "    else:\n"
    "        return 0\n"
)


def _ct(new):
    """Swap ONLY the coeff_truthy impl body."""
    return _swap(_BASE, _CT_GOLD, new)


def _sl(new):
    """Swap ONLY the strip_constant_len impl body."""
    return _swap(_BASE, _SL_GOLD, new)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls MUST
# verify; else SPEC-TOO-STRONG.
# ===========================================================================

# pos-ct-negate: coeff_truthy computed as the logical negation of "denotes zero"
# (c.mzero != 1) rather than the equality form (c.mzero == 0). Same truth value
# on every reachable state (mzero in {0,1}), different expression shape. No
# framing/lemma needed (no loop, no helper fold), so directive 2/3 are clear.
_POS_CT_NEGATE = "    return not (c.mzero == 1)\n"

# pos-sl-direct: strip_constant_len computed DIRECTLY from c.mzero, branch
# reordered (mzero-true case first), instead of going through coeff_truthy. Same
# returned length on every state, different control-flow shape. Keeps every gold
# proof obligation (the postcondition is pinned to c.mzero, which this reads
# directly), so no invariant/assert is dropped (directive 2).
_POS_SL_DIRECT = (
    "    if c.mzero == 1:\n"
    "        return 0\n"
    "    else:\n"
    "        return 1\n"
)

# pos-sl-reorder: strip_constant_len keeps the coeff_truthy call but reorders the
# branches (falsy case first). Pure branch reorder, identical values; must verify.
_POS_SL_REORDER = (
    "    if not coeff_truthy(c):\n"
    "        return 0\n"
    "    else:\n"
    "        return 1\n"
)


# ===========================================================================
# ADMISSIBILITY — the precondition must admit a normal, F2P-shaped input MUST
# verify; else PRECOND-TOO-STRONG. We construct the DISCRIMINATING coefficient
# (lit0 == 0, mzero == 1) — the issue's actual coefficient — call coeff_truthy
# on it, and assert the spec result. If the Requires (incl. the class invariant
# Implies(lit0==1, mzero==1)) were too strong to admit this state, the spec would
# be degenerate. Inserted inside strip_constant_len's impl region only: under the
# MustTerminate obligations the witness calls must sit in the LARGER-measure
# context (strip, measure 3) so the constructor (measure 1) and coeff_truthy
# (measure 2) calls are strictly decreasing; a strip_constant_len(witness) call
# is not expressible anywhere (no context outlives measure 3), but strip's
# Requires are byte-identical to coeff_truthy's, so admission carries over.
# ===========================================================================
_ADMISS_CT = (
    "    # admissibility: the issue's coefficient (denotes zero, non-bare-literal\n"
    "    # shape) is a legitimate in-domain input: lit0==0, mzero==1 satisfies the\n"
    "    # class invariant Implies(lit0==1, mzero==1) and both per-field bounds.\n"
    "    witness = Coeff(0, 1)\n"
    "    Assert(witness.lit0 == 0 and witness.mzero == 1)\n"
    "    Assert(coeff_truthy(witness) == False)\n"
    "    if coeff_truthy(c):\n"
    "        return 1\n"
    "    else:\n"
    "        return 0\n"
)

# admiss-nonzero: also confirm a normal NON-zero coefficient (lit0==0, mzero==0)
# is admitted and reads truthy.
_ADMISS_NONZERO = (
    "    # admissibility: an ordinary non-zero coefficient (mzero==0) is in-domain.\n"
    "    nz = Coeff(0, 0)\n"
    "    Assert(coeff_truthy(nz) == True)\n"
    "    if coeff_truthy(c):\n"
    "        return 1\n"
    "    else:\n"
    "        return 0\n"
)


# ===========================================================================
# FRAME-MUTATION (MANDATORY — has_readonly_input). A rival that WRITES the
# read-only input to satisfy the postcondition vacuously MUST be REJECTED for
# INSUFFICIENT PERMISSION. coeff_truthy / strip_constant_len hold only
# Acc(c.mzero, 1/2) / Acc(c.lit0, 1/2); a write needs the full share.
# ===========================================================================

# frame-ct-write-mzero: coeff_truthy overwrites c.mzero before returning so the
# postcondition Result()==(c.mzero==0) becomes trivially establishable for a
# fixed return. Must fail: the impl holds only 1/2 permission on c.mzero, a write
# requires full (1/1). Gold postcondition kept verbatim => the rejection is
# attributable to the write, not to a value mismatch.
_FRAME_CT_WRITE = (
    "    c.mzero = 0\n"
    "    return True\n"
)

# frame-sl-write-lit0: strip_constant_len overwrites c.lit0 (the other read-only
# field). Same insufficient-permission rejection. (Touching lit0 — not even the
# field the postcondition mentions — to show ANY write to the half-share input
# is rejected.)
_FRAME_SL_WRITE = (
    "    c.lit0 = 1\n"
    "    if c.mzero == 1:\n"
    "        return 0\n"
    "    else:\n"
    "        return 1\n"
)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN rivals (must be REJECTED). These key the answer on
# the STRUCTURAL facet lit0 instead of the mathematical facet mzero — correct on
# the agreeing states, wrong on the discriminating state (lit0==0, mzero==1).
# ===========================================================================

# weak-ct-prepatch: the PRE-PATCH bug verbatim — truthiness keyed on the
# structural literal test (lit0) instead of the mathematical zero (mzero).
# Correct on every state EXCEPT (lit0==0, mzero==1). This is model_prepatch.py.
_WEAK_CT_PREPATCH = "    return c.lit0 == 0\n"

# weak-ct-const-true: a coefficient is "always truthy" (the dup_strip-never-
# strips degenerate rival). Correct on non-zero coefficients (mzero==0) but
# wrong on EVERY denoting-zero coefficient (mzero==1).
_WEAK_CT_CONST = "    return True\n"

# weak-sl-via-lit0: strip_constant_len keys the kept/dropped decision on lit0
# (structural) rather than coeff_truthy/mzero. Keeps the bare literal stripped
# but RETAINS a non-trivial denoting-zero coefficient (lit0==0, mzero==1) — the
# exact DMP([EX(0)]) bug at the poly level. (Independent of the coeff_truthy
# impl, so this catches the propagation even if coeff_truthy were correct.)
_WEAK_SL_LIT0 = (
    "    if c.lit0 == 1:\n"
    "        return 0\n"
    "    else:\n"
    "        return 1\n"
)

# weak-sl-const-keep: strip_constant_len ALWAYS keeps the coefficient (length 1),
# never collapsing to the canonical zero poly. Correct on non-zero constants but
# wrong on every zero coefficient (mzero==1) — never reaches DMP([]).
_WEAK_SL_CONST = "    return 1\n"


# ===========================================================================
# VACUOUS NON-TERMINATION (uniqueness) — impls that spin forever before the
# (otherwise correct) return, satisfying every value postcondition only
# vacuously. This is the EXACT G-PANEL-1 atk_8 rival: the auditor inserted
# `while (1 if (f.ex.is_zero is True) else 0) >= 0: pass` before the correct
# `return not f.ex.is_zero` in the real __bool__, and its faithful real patch
# hangs the F2P test (timed out after 240s). Under Requires(MustTerminate(k))
# the loop takes no termination obligation and has no decreasing measure, so
# Nagini's obligation system MUST reject it ("Obligation leak check failed").
# ===========================================================================

# nonterm-ct-spin: coeff_truthy spins on a trivially-true guard (mirroring the
# auditor's `(1 if ... else 0) >= 0` shape) then returns the correct value.
_NONTERM_CT = (
    "    while (1 if (c.mzero == 1) else 0) >= 0:\n"
    "        pass\n"
    "    return c.mzero == 0\n"
)

# nonterm-sl-spin: strip_constant_len spins forever before the correct mzero
# dispatch (guard reads the read-only lit0 field — always >= 0).
_NONTERM_SL = (
    "    while 0 <= c.lit0:\n"
    "        pass\n"
    "    if coeff_truthy(c):\n"
    "        return 1\n"
    "    else:\n"
    "        return 0\n"
)


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-ct-negate",
        "kind": "soundness",
        "expect": "verify",
        "module": _ct(_POS_CT_NEGATE),
        "rationale": (
            "structurally-different CORRECT impl of coeff_truthy: `not "
            "(c.mzero == 1)` instead of `c.mzero == 0`. Same truth value on every "
            "reachable state (mzero in {0,1}); different expression shape. No loop "
            "/ no @Pure fold, so no framing or induction lemma is needed "
            "(directives 2 & 3 avoided). Must verify; if it cannot satisfy "
            "Result()==(c.mzero==0), the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-sl-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _sl(_POS_SL_DIRECT),
        "rationale": (
            "structurally-different CORRECT impl of strip_constant_len: computes "
            "the length DIRECTLY from c.mzero with the mzero-true branch first, "
            "instead of dispatching through coeff_truthy. Identical returned "
            "length on every state. The postcondition is pinned to c.mzero (read "
            "directly here), so no gold proof obligation is dropped. Must verify; "
            "else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-sl-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _sl(_POS_SL_REORDER),
        "rationale": (
            "branch-REORDER positive control for strip_constant_len: keeps the "
            "coeff_truthy call but tests the falsy case first (`if not "
            "coeff_truthy(c): return 0`). Same values, different control flow; "
            "must verify."
        ),
    },
    {
        "id": "admiss-issue-coeff",
        "kind": "admissibility",
        "expect": "verify",
        "module": _sl(_ADMISS_CT),
        "rationale": (
            "admissibility: constructs the issue's DISCRIMINATING coefficient "
            "Coeff(0, 1) (denotes zero, non-bare-literal shape) — the state that "
            "satisfies the class invariant Implies(lit0==1,mzero==1) and both "
            "field bounds — and asserts coeff_truthy(it)==False. Proves the "
            "Requires admit the very input the fix targets (else "
            "PRECOND-TOO-STRONG, e.g. an invariant that wrongly forbade "
            "lit0==0,mzero==1 would make the spec vacuous). Hosted in "
            "strip_constant_len's impl (measure 3) so the Coeff(measure 1) and "
            "coeff_truthy(measure 2) witness calls strictly decrease the "
            "MustTerminate obligation; strip's Requires on c are byte-identical "
            "to coeff_truthy's, so the admitted state is the same. The gold "
            "dispatch is kept, so the postconditions still verify. Must verify."
        ),
    },
    {
        "id": "admiss-nonzero-coeff",
        "kind": "admissibility",
        "expect": "verify",
        "module": _sl(_ADMISS_NONZERO),
        "rationale": (
            "admissibility on the other live state: an ordinary non-zero "
            "coefficient Coeff(0, 0) is in-domain; asserts coeff_truthy==True. "
            "Confirms the precondition accepts normal non-zero inputs too "
            "(hosted in strip_constant_len for the same MustTerminate-measure "
            "reason as admiss-issue-coeff). Must verify."
        ),
    },
    # ----- frame-mutation (MANDATORY; must be rejected for permission) ----
    {
        "id": "frame-ct-write-mzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ct(_FRAME_CT_WRITE),
        "refinement": (
            "writes c.mzero = 0 then returns True. There is NO faithful real "
            "patch for this: the real __bool__ reads the coefficient's "
            "mathematical zeroness (not f.ex.is_zero); it neither can nor does "
            "mutate the expression's is_zero state. A 'patch' that reassigned the "
            "coefficient to a zero expression would change the polynomial's value, "
            "not test it, and would not produce `not f.ex.is_zero` — it cannot "
            "resolve test_issue_20427 (which builds a SPECIFIC denoting-zero "
            "coefficient and checks the poly equals Poly(0,x,EX) WITHOUT altering "
            "the coefficient). So a verifying rival would be a true "
            "verify-but-not-resolve break."
        ),
        "rationale": (
            "REJECTED by the permission system: coeff_truthy holds only "
            "Acc(c.mzero, 1/2); the assignment `c.mzero = 0` requires the full "
            "write permission (1/1), which the impl does not have -> Nagini "
            "insufficient-permission error. The gold postcondition is kept "
            "verbatim so the rejection is attributable to the WRITE, not a value "
            "mismatch."
        ),
    },
    {
        "id": "frame-sl-write-lit0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _sl(_FRAME_SL_WRITE),
        "refinement": (
            "writes c.lit0 = 1 (mutating the read-only structural facet) before "
            "computing the length. No faithful real patch mutates its input "
            "coefficient inside dup_strip / __bool__; the strip is a pure read of "
            "the coefficient list. A real edit that wrote into the coefficient "
            "would corrupt the polynomial, not strip it, and could not yield the "
            "canonical DMP([]) the F2P checks. verify-but-not-resolve."
        ),
        "rationale": (
            "REJECTED by the permission system: strip_constant_len holds only "
            "Acc(c.lit0, 1/2); `c.lit0 = 1` needs full write permission -> "
            "insufficient-permission error. The returned-value logic is otherwise "
            "the correct mzero dispatch, so the rejection is attributable purely "
            "to the write of the half-share input."
        ),
    },
    # ----- vacuous non-termination (must be rejected by obligations) ------
    {
        "id": "nonterm-ct-spin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ct(_NONTERM_CT),
        "refinement": (
            "the G-PANEL-1 atk_8 rival verbatim (modulo the R-refinement "
            "mzero == (f.ex.is_zero is True)): an infinite spin "
            "`while (1 if (c.mzero == 1) else 0) >= 0: pass` inserted before "
            "the correct return. Its faithful real patch adds the same spin to "
            "__bool__ before `return not f.ex.is_zero`; the recorded harness "
            "run shows it HANGS the F2P suite (sympy__sympy-20428: test timed "
            "out after 240 seconds), so it does NOT resolve. Every value "
            "postcondition holds only vacuously on the diverging trace — a "
            "verifying rival is a true verify-but-not-resolve break."
        ),
        "rationale": (
            "REJECTED by the obligation system: coeff_truthy's precondition "
            "carries MustTerminate(2); the always-true loop declares no "
            "decreasing termination measure, so the caller's obligation leaks "
            "into the loop -> Nagini 'Obligation leak check failed'. The "
            "returned value is otherwise the correct mzero dispatch, so the "
            "rejection is attributable purely to the divergence."
        ),
    },
    {
        "id": "nonterm-sl-spin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _sl(_NONTERM_SL),
        "refinement": (
            "the same vacuous-divergence rival aimed at the strip: spins "
            "forever (`while 0 <= c.lit0`, always true for the 0/1 facet) "
            "before the correct coeff_truthy dispatch. Its faithful real patch "
            "hangs dup_strip / Poly construction, so test_issue_20427 (and the "
            "whole polys suite) times out — verify-but-not-resolve."
        ),
        "rationale": (
            "REJECTED by the obligation system: strip_constant_len carries "
            "MustTerminate(3); the measureless infinite loop leaks the "
            "obligation -> 'Obligation leak check failed', independent of the "
            "value postconditions (which the trailing dispatch would satisfy)."
        ),
    },
    # ----- uniqueness / partial-domain rivals (must be rejected) ----------
    {
        "id": "weak-ct-prepatch-lit0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ct(_WEAK_CT_PREPATCH),
        "refinement": (
            "this IS the pre-patch bug verbatim (model_prepatch.py): truthiness "
            "keyed on the STRUCTURAL literal test `c.lit0 == 0`, i.e. the real "
            "`f.ex != 0`. Its faithful real patch is the PRE-patch code, which "
            "does NOT resolve: on the issue's denoting-zero radical coefficient "
            "(lit0==0, mzero==1) it reports truthy, so dup_strip retains it and "
            "the poly's rep stays DMP([EX(0)]) instead of DMP([]) — "
            "test_issue_20427 (`f == Poly(0, x, domain='EX')`) FAILS. A verifying "
            "rival here is a true verify-but-not-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition Result()==(c.mzero==0): on the "
            "discriminating state (lit0==0, mzero==1) the rival returns "
            "(lit0==0)==True while the spec requires (mzero==0)==False. The "
            "rejection comes from the load-bearing equality clause; the class "
            "invariant makes (lit0==0,mzero==1) reachable (it does not forbid it), "
            "so the verifier finds the counterexample."
        ),
    },
    {
        "id": "weak-ct-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ct(_WEAK_CT_CONST),
        "refinement": (
            "a degenerate rival that calls every coefficient truthy (`return "
            "True`) — i.e. dup_strip never strips. Its faithful real patch (a "
            "__bool__ that always returns True) leaves EVERY constant poly "
            "unstripped, so Poly(0,x,EX) itself would have rep DMP([EX(0)]) and "
            "test_issue_20427 plus the PASS_TO_PASS zero-poly tests (test_Poly_zero, "
            "test_Poly_nonzero) fail. verify-but-not-resolve."
        ),
        "rationale": (
            "REJECTED by Result()==(c.mzero==0): on any zero coefficient "
            "(mzero==1) the rival returns True but the spec requires False. The "
            "constructor admits Coeff(_, 1), so the verifier has the witness."
        ),
    },
    {
        "id": "weak-sl-via-lit0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _sl(_WEAK_SL_LIT0),
        "refinement": (
            "strip_constant_len keys the keep/drop decision on the STRUCTURAL "
            "facet lit0 (collapse iff the bare literal) instead of mzero. This is "
            "the poly-level image of the pre-patch bug: a non-trivial coefficient "
            "that denotes zero (lit0==0, mzero==1) is RETAINED (length 1), so the "
            "rep is DMP([EX(0)]) not DMP([]) — exactly the issue's bad_poly. Its "
            "faithful real patch would make dup_strip key on a structural literal "
            "check rather than bool(coeff), and the F2P `f == Poly(0,x,EX)` fails. "
            "verify-but-not-resolve. (Catches the bug propagation independently of "
            "coeff_truthy's body.)"
        ),
        "rationale": (
            "REJECTED by Implies(c.mzero==1, Result()==0): on (lit0==0, mzero==1) "
            "this rival returns 1, but the postcondition demands 0. Rejection "
            "comes from the strip postcondition clause that pins length to the "
            "mathematical facet."
        ),
    },
    {
        "id": "weak-sl-const-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _sl(_WEAK_SL_CONST),
        "refinement": (
            "strip_constant_len always returns 1 (never collapses to the "
            "canonical zero poly). Its faithful real patch is a dup_strip that "
            "never drops the leading coefficient, so even Poly(0,x,EX) keeps a "
            "DMP([EX(0)]) rep and `f == Poly(0,x,domain='EX')` / is_zero break — "
            "test_issue_20427 and the zero-poly P2P tests fail. "
            "verify-but-not-resolve."
        ),
        "rationale": (
            "REJECTED by Implies(c.mzero==1, Result()==0): on any zero "
            "coefficient (mzero==1) the rival returns 1, violating the clause "
            "requiring 0. The verifier instantiates mzero==1 (admitted by the "
            "constructor)."
        ),
    },
]

# No @ContractOnly axioms and no consumed A-reference deep-model callee in this
# bundle (meta.axioms == []). The single changed sub-operation — routing
# truthiness through Expr.is_zero rather than the structural != 0 — is modelled
# DEEPLY by the Coeff.mzero field; there is no axiom Ensures whose soundness or
# caller-domain containment could be a defect. That deep facet's fidelity
# (mzero == the real Expr.is_zero) is the job of axiom_check.py / G-AX, a
# model-fidelity check, not a PBT axiom obligation. Hence:
AXIOM_TESTS = []
