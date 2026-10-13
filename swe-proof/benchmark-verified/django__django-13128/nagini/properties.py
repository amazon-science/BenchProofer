"""PBT manifest for django__django-13128 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  resolve_kind(is_already_temporal: bool, is_sub: bool,
               t_lhs: int, t_rhs: int) -> int
    Requires: T_UNKNOWN <= t_lhs <= T_OTHER, T_UNKNOWN <= t_rhs <= T_OTHER
              (the two operand output-type codes lie in the 0..5 enumeration)
    Ensures (5 clauses):
      1. Result() in {K_PLAIN, K_DURATION, K_TEMPORAL}
      2. Implies(is_already_temporal, Result() == K_PLAIN)
      3. (Result()==K_DURATION) == (not already and wants_duration(t_lhs,t_rhs))
      4. (Result()==K_TEMPORAL) ==
             (not already and not wants_duration and wants_temporal(is_sub,..))
      5. (LOAD-BEARING, full functional pin)
         Result() == resolved_kind(is_already_temporal, is_sub, t_lhs, t_rhs)

  resolved_kind(...) deep model:
      if is_already_temporal:           return K_PLAIN
      if wants_duration(t_lhs,t_rhs):    return K_DURATION   # a DUR operand present AND types differ
      if wants_temporal(is_sub,t_lhs,t_rhs): return K_TEMPORAL  # SUB of two EQUAL date/time operands
      return K_PLAIN

This models the resolve-time classification of a CombinedExpression the gold
patch inserts into CombinedExpression.resolve_expression (plain / duration /
temporal-subtraction), so a bare temporal subtraction acquires its output type
at resolution time instead of raising the mixed-types FieldError.

NO READ-ONLY INPUT / NO FRAME-MUTATION CASE: every parameter is an immutable
scalar (two bool, two int VALUE parameters); there is NO Acc(x,1/2) heap
reference to overwrite. The #1 weakness class (frame mutation through a 1/2
permission) is therefore structurally inapplicable here -- there is no heap
state to mutate to satisfy the postcondition vacuously. See 'assessment'.

GROUNDED-ORACLE NOTE: the load-bearing postcondition clause 5 pins Result() to
the @Pure helper resolved_kind, which is GROUNDED in the arguments -- it unfolds
(through wants_duration / wants_temporal / is_datetime_type) entirely to a
function of the scalar args, with no opaque external answer-key. There is thus
NO *wrong* echo to construct: `return resolved_kind(...)` is the honest cheapest
CORRECT impl (included as a positive control), not an ungrounded-oracle attack.
Any WRONG constant/echo fails clause 5. The uniqueness lane is therefore about
whether a rival can satisfy the decision on the F2P/P2P-tested sub-domain while
diverging on a discriminating sub-domain (duration±duration of EQUAL type / an
already-temporal self / a non-SUB connector) -- exactly the dispatch distinctions
the gold patch makes.

CONTROL-FLOW-EFFECT: N/A. The real patch's control-flow difference (returning a
recursively-resolved Duration/Temporal wrapper vs a plain self.copy()) is fully
observable through the kind code (K_DURATION/K_TEMPORAL/K_PLAIN); there is no
raise / side-effect distinction invisible to the value abstraction. (The model
collapses None/FieldError-typed operands to T_UNKNOWN, an in-domain code, so no
exceptional control flow escapes the abstraction.)

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty).
The changed dispatch is modelled DEEPLY (pure region: resolved_kind) and validated
== the REAL post-patch Django CombinedExpression.resolve_expression dispatch
out-of-band by axiom_check.py (G-AX) over the full 2*2*6*6 enumeration + F2P
witnesses. PBT re-runs that real-callee equivalence as an axiom-soundness probe
(axiom_check.py's logic, read on the HOST at load time and embedded verbatim into
the probe string, since the runner mounts ONLY the probe at /work).

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (a straight-line body, no loop invariants/asserts,
so positive controls carry no dropped-lemma proof-gap risk). The frozen spec
(axioms/pure/pre/post-conditions/signatures) is never touched -> same_spec holds.
"""
from pathlib import Path

INSTANCE = "django__django-13128"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# The whole impl body is straight-line; these are the exact gold lines.
# ---------------------------------------------------------------------------
_GUARD = "    if not is_already_temporal:\n"
_DUR_BRANCH = (
    "        if (t_lhs == T_DURATION or t_rhs == T_DURATION) and t_lhs != t_rhs:\n"
    "            return K_DURATION\n"
)
_TMP_BRANCH = (
    "        if is_sub and is_datetime_type(t_lhs) and t_lhs == t_rhs:\n"
    "            return K_TEMPORAL\n"
)
_FALLTHROUGH = "    return K_PLAIN\n"
# The full impl body (between the markers), used for whole-body replacements.
_IMPL_BODY = (
    "    if not is_already_temporal:\n"
    "        if (t_lhs == T_DURATION or t_rhs == T_DURATION) and t_lhs != t_rhs:\n"
    "            return K_DURATION\n"
    "        if is_sub and is_datetime_type(t_lhs) and t_lhs == t_rhs:\n"
    "            return K_TEMPORAL\n"
    "    return K_PLAIN\n"
)

# NB: _FALLTHROUGH ("    return K_PLAIN\n") is NOT unique in _BASE (it also
# appears in the @Pure resolved_kind helper), so it is verified only as part of
# the unique _IMPL_BODY (= _GUARD + _DUR_BRANCH + _TMP_BRANCH + _FALLTHROUGH),
# never swapped standalone.
for _a in (_GUARD, _DUR_BRANCH, _TMP_BRANCH, _IMPL_BODY):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"
assert _IMPL_BODY == _GUARD + _DUR_BRANCH + _TMP_BRANCH + _FALLTHROUGH


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- branch reorder. The two dispatch branches are
# swapped (temporal-subtraction tested BEFORE duration). wants_temporal requires
# t_lhs == t_rhs while wants_duration requires t_lhs != t_rhs, so the two
# branch GUARDS are mutually exclusive -- reordering them is SEMANTICALLY
# IDENTICAL to the gold (verified exhaustively over all 2*2*6*6 inputs offline:
# 0 differences). Straight-line body, no invariants to drop. MUST verify; else
# the postcondition is over-fit to the gold branch ORDER => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _DUR_BRANCH + _TMP_BRANCH, _TMP_BRANCH + _DUR_BRANCH,
)

# (5b) POSITIVE CONTROL -- the cheapest HONEST impl. Clause 5 is literally
# Result() == resolved_kind(...), and resolved_kind is GROUNDED in the args (a
# @Pure dispatch fully computable from the scalars), so directly returning it is
# a correct, fully-grounded implementation, not an ungrounded-oracle echo. MUST
# verify; else SPEC-TOO-STRONG. It also demonstrates the spec is not
# echo-vulnerable: any WRONG constant/echo fails clause 5.
_POS_DIRECT = _swap(
    _BASE, _IMPL_BODY,
    "    return resolved_kind(is_already_temporal, is_sub, t_lhs, t_rhs)\n",
)

# (5c) POSITIVE CONTROL -- structurally different shape: compute the kind into a
# local via the @Pure predicates wants_duration / wants_temporal directly (a
# data-flow reshape rather than the early-return cascade), single return. The
# guard ordering is the same logical dispatch. MUST verify; else SPEC-TOO-STRONG.
_POS_LOCAL = _swap(
    _BASE, _IMPL_BODY,
    "    k = K_PLAIN  # type: int\n"
    "    if not is_already_temporal:\n"
    "        if wants_duration(t_lhs, t_rhs):\n"
    "            k = K_DURATION\n"
    "        elif wants_temporal(is_sub, t_lhs, t_rhs):\n"
    "            k = K_TEMPORAL\n"
    "    return k\n",
)

# (6) ADMISSIBILITY -- a self-call on the F2P-shaped input (a bare datetime
# subtraction: not already temporal, SUB connector, two EQUAL DateTimeField
# operands) must establish the precondition (T_DATETIME==2 is in 0..5) and the
# result-property assert (it classifies as K_TEMPORAL, the temporal-subtraction
# form -- the exact behaviour test_datetime_subtraction_microseconds exercises).
# MUST verify; else the precondition rejects a normal F2P input => PRECOND-TOO-STRONG.
#
# TERMINATION NOTE (why the self-call is GUARDED, and why the guard is not a
# dodge). The spec now carries Requires(MustTerminate(2 + t_lhs + t_rhs)), so a
# self-call must DESCEND: Nagini requires the caller's obligation level to be
# strictly greater than the callee's. The probe calls itself at the fixed
# operand codes (T_DATETIME, T_DATETIME), i.e. callee level 2+2+2; so the call
# is admissible exactly when the CALLER's t_lhs + t_rhs exceeds
# T_DATETIME + T_DATETIME, which is precisely the guard. An UNGUARDED probe (the
# shape this case used while the spec demanded nothing of termination) is
# literal infinite recursion -- an unconditional self-call on CONSTANT arguments
# ahead of the guard, which re-enters with the same arguments forever and never
# reaches a return. It "verified" under the old spec only because partial
# correctness claims the postconditions of runs that REACH the return, and that
# run never does. The guard is what makes the probe a terminating program;
# the property it defends (an F2P-shaped input is ADMITTED by the precondition
# and classifies as K_TEMPORAL) is unchanged and still asserted.
#
# The guard is FEASIBLE, not vacuously true: t_lhs + t_rhs > 4 is reachable
# inside the precondition's 0..5 x 0..5 box (e.g. T_DURATION - T_OTHER = 4+5),
# so the self-call and its Assert are really verified. Checked out-of-band by
# planting Assert(False) in the guarded branch: Nagini REJECTS it ("Assertion
# False might not hold"), which it could not do were the branch unreachable.
_POS_ADMISS = _swap(
    _BASE, _GUARD,
    "    if t_lhs + t_rhs > T_DATETIME + T_DATETIME:\n"
    "        _k = resolve_kind(False, True, T_DATETIME, T_DATETIME)\n"
    "        Assert(_k == K_TEMPORAL)\n"
    "    if not is_already_temporal:\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (3a) PARTIAL-DOMAIN -- drop the `t_lhs != t_rhs` guard on the duration branch.
# Now ANY operand of duration type dispatches to K_DURATION, including
# T_DURATION - T_DURATION (BOTH duration, EQUAL types). The gold wants_duration
# requires the types to DIFFER, so equal-duration operands stay K_PLAIN.
# Correct on every differing-type input; WRONG on the equal-duration sub-domain.
_RIVAL_DROP_NEQ = _swap(
    _BASE, _DUR_BRANCH,
    "        if t_lhs == T_DURATION or t_rhs == T_DURATION:\n"
    "            return K_DURATION\n",
)

# (3b) PARTIAL-DOMAIN -- drop the is_already_temporal guard. An expression that
# is ALREADY a specialised temporal/duration form is now re-classified by the
# operand types (e.g. an already-temporal self that is a SUB of two equal
# date/time operands becomes K_TEMPORAL again). The gold leaves an
# already-specialised expression PLAIN (the isinstance guard skips the dispatch).
# Correct on every plain self; WRONG on the already-temporal sub-domain.
_RIVAL_DROP_IAT = _swap(
    _BASE, _GUARD + _DUR_BRANCH + _TMP_BRANCH + _FALLTHROUGH,
    _DUR_BRANCH.replace("        ", "    ", 2)
    + _TMP_BRANCH.replace("        ", "    ", 2)
    + _FALLTHROUGH,
)

# (3c) PARTIAL-DOMAIN -- drop the is_sub requirement on the temporal branch.
# Now ADD (not just SUB) of two equal date/time operands dispatches to
# K_TEMPORAL. The gold wants_temporal requires the SUB connector. Correct on
# every SUB input; WRONG on the ADD-of-equal-date/time sub-domain.
_RIVAL_DROP_SUB = _swap(
    _BASE, _TMP_BRANCH,
    "        if is_datetime_type(t_lhs) and t_lhs == t_rhs:\n"
    "            return K_TEMPORAL\n",
)

# (3d) PARTIAL-DOMAIN (cheap supporting baseline) -- constant K_PLAIN. This is
# EXACTLY model_prepatch.py's behaviour (pre-patch resolve_expression performed
# no classification). It fails clauses 3/4/5 on every duration/temporal case.
# A faithful patch doing this is the pre-patch code and FAILS all 7 F2P tests
# (the bare temporal subtraction still raises the mixed-types FieldError) --
# verify-not-resolve. Cheap supporting near-miss, still carries a real refinement.
_RIVAL_CONST_PLAIN = _swap(
    _BASE, _IMPL_BODY,
    "    plain = K_PLAIN  # type: int\n    return plain\n",
)


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (temporal-subtraction branch tested "
                  "BEFORE the duration branch) but CORRECT impl: the two branch "
                  "guards are mutually exclusive (wants_temporal needs "
                  "t_lhs==t_rhs, wants_duration needs t_lhs!=t_rhs), so the "
                  "reorder is semantically identical (0 diffs over all 144 "
                  "inputs offline). Straight-line body, no dropped invariant. "
                  "Must verify; else the postcondition is over-fit to the gold "
                  "branch ORDER => SPEC-TOO-STRONG."},
    {"id": "pos-control-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT,
     "rationale": "clause 5 is literally Result()==resolved_kind(...), and "
                  "resolved_kind is GROUNDED in the args (a @Pure dispatch over "
                  "the scalars), so `return resolved_kind(...)` is the honest "
                  "cheapest CORRECT impl, not an ungrounded echo. Must verify; "
                  "else SPEC-TOO-STRONG. Also shows the spec is not "
                  "echo-vulnerable: any WRONG constant fails clause 5."},
    {"id": "pos-control-local-predicates", "kind": "soundness",
     "expect": "verify", "module": _POS_LOCAL,
     "rationale": "data-flow reshape: accumulate the kind into a typed local via "
                  "the @Pure predicates wants_duration/wants_temporal and a "
                  "single return, instead of the early-return cascade. Same "
                  "logical dispatch. Must verify; else SPEC-TOO-STRONG (the "
                  "postcondition would be over-fit to the early-return SHAPE)."},
    {"id": "admiss-f2p-datetime-sub", "kind": "admissibility",
     "expect": "verify", "module": _POS_ADMISS,
     "rationale": "a self-call on the F2P-shaped input (not already temporal, "
                  "SUB, two EQUAL DateTimeField operands -- the bare datetime "
                  "subtraction the issue is about) must establish the "
                  "precondition (T_DATETIME=2 in 0..5) and classify as "
                  "K_TEMPORAL (Assert). If the precondition rejects this normal "
                  "F2P input => PRECOND-TOO-STRONG. The self-call sits under a "
                  "t_lhs+t_rhs > T_DATETIME+T_DATETIME guard so it DESCENDS in "
                  "the MustTerminate(2+t_lhs+t_rhs) level (the caller must "
                  "outrank the callee); unguarded it would be unconditional "
                  "self-recursion on constant args that never reaches a return, "
                  "which only the old termination-silent spec could accept. The "
                  "guard is feasible (4 < t_lhs+t_rhs <= 10 is in-domain), so "
                  "the Assert is really discharged, not skipped."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "weak-drop-duration-neq-guard", "kind": "uniqueness",
     "expect": "reject", "module": _RIVAL_DROP_NEQ,
     "refinement": "dropping the `lhs_type != rhs_type` guard makes the real "
                   "patch wrap a DurationField - DurationField (two EQUAL "
                   "duration operands) in a DurationExpression. The gold dispatch "
                   "('DurationField' in {a,b} AND a != b) leaves equal-duration "
                   "operands as a plain CombinedExpression; a DurationField "
                   "subtraction of two durations is a plain duration result, not "
                   "the mixed duration-arithmetic form. A faithful patch wrapping "
                   "it would change the SQL emitted for duration-duration "
                   "arithmetic and diverge from the gold dispatch (the deep model "
                   "G-AX validates against the real callee), so it does not "
                   "reproduce gold behaviour -- verify-not-resolve.",
     "rationale": "rejection source: postcondition clause 5 "
                  "Result()==resolved_kind and clause 3 (Result()==K_DURATION) "
                  "== (not already and wants_duration). On T_DURATION-T_DURATION "
                  "(equal) wants_duration is False so resolved_kind is K_PLAIN, "
                  "but the rival returns K_DURATION -- the verifier cannot close "
                  "clauses 3/5. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-drop-already-temporal-guard", "kind": "uniqueness",
     "expect": "reject", "module": _RIVAL_DROP_IAT,
     "refinement": "dropping the isinstance(self,(DurationExpression,"
                   "TemporalSubtraction)) guard makes the real patch RE-classify "
                   "an already-specialised expression: a TemporalSubtraction "
                   "re-resolving itself would re-enter the dispatch and wrap "
                   "again, contradicting the gold's `if not isinstance(...)` "
                   "guard whose whole purpose is to stop the recursive "
                   ".resolve_expression() re-entry from re-wrapping. A faithful "
                   "patch without that guard recurses/re-wraps and does not match "
                   "the gold dispatch -- verify-not-resolve.",
     "rationale": "rejection source: postcondition clause 2 "
                  "Implies(is_already_temporal, Result()==K_PLAIN) and clause 5. "
                  "On is_already_temporal=True with a SUB of two equal date/time "
                  "operands the rival returns K_TEMPORAL, but clause 2 forces "
                  "K_PLAIN -- the verifier cannot close clauses 2/5 (23 diverging "
                  "inputs offline). If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-drop-sub-requirement", "kind": "uniqueness",
     "expect": "reject", "module": _RIVAL_DROP_SUB,
     "refinement": "dropping the `connector == SUB` test makes the real patch "
                   "wrap an ADDITION of two equal date/time operands (e.g. "
                   "DateField + DateField) in a TemporalSubtraction. The gold "
                   "dispatch only produces a TemporalSubtraction for the SUB "
                   "connector; adding two dates is not a temporal subtraction and "
                   "must stay plain. A faithful patch wrapping date addition as a "
                   "TemporalSubtraction would emit subtraction SQL for an add and "
                   "diverge from gold -- verify-not-resolve.",
     "rationale": "rejection source: postcondition clause 4 (Result()==K_TEMPORAL) "
                  "== (not already and not wants_duration and wants_temporal), "
                  "where wants_temporal REQUIRES is_sub, and clause 5. On "
                  "is_sub=False with two equal date/time operands the rival "
                  "returns K_TEMPORAL, but resolved_kind is K_PLAIN -- the "
                  "verifier cannot close clauses 4/5 (3 diverging inputs "
                  "offline). If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-const-plain-prepatch", "kind": "uniqueness",
     "expect": "reject", "module": _RIVAL_CONST_PLAIN,
     "refinement": "constant K_PLAIN is EXACTLY model_prepatch.py / the pre-patch "
                   "resolve_expression, which performed no resolve-time "
                   "classification. A faithful patch doing this is the pre-patch "
                   "code: the bare temporal subtraction is never specialised at "
                   "resolution time and raises FieldError: Expression contains "
                   "mixed types -- it FAILS all 7 F2P tests (test_date_subtraction, "
                   "test_datetime_subtraction_microseconds, ...). verify-not-resolve. "
                   "Cheap supporting baseline, carrying a real refinement.",
     "rationale": "rejection source: postcondition clauses 3/4/5. On any "
                  "duration/temporal F2P case (e.g. SUB of two equal DateTimeField "
                  "operands) resolved_kind is K_DURATION/K_TEMPORAL but the rival "
                  "returns K_PLAIN -- the verifier cannot close clauses 3/4/5 "
                  "(this is the same failure G-DIFF records for model_prepatch.py). "
                  "If it verified => SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed; the changed dispatch is an
# A-reference deep model (resolved_kind) validated == the REAL post-patch Django
# CombinedExpression.resolve_expression dispatch. We re-run that real-callee
# equivalence (axiom_check.py's logic, read on the HOST at load time and embedded
# verbatim into a self-contained probe -- the runner mounts ONLY the probe at
# /work) as an axiom-soundness check: if the deep model ever disagrees with the
# real dispatch over the full 2*2*6*6 enumeration + F2P witnesses, the
# A-reference is unsound. The probe self-applies the gold patch to /testbed
# (idempotently) so the real resolve_expression carries the inserted branch.
# A containment probe is N/A: there is no @ContractOnly axiom Requires domain to
# fall outside, and the enumeration covers EXACTLY the model's full input space
# (all 6*6 type-code pairs the Requires admits x both bools), which is a superset
# of the caller-reachable set, so containment is trivially satisfied.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-resolved-kind-equals-real-dispatch",
        "axiom": "resolved_kind",  # A-reference deep model (NOT a consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model resolved_kind (pure region) is an "
                     "A-reference: it must equal the REAL post-patch Django "
                     "CombinedExpression.resolve_expression DISPATCH DECISION "
                     "(which specialised wrapper, if any, the resolution newly "
                     "creates) on every input. This probe (axiom_check.py "
                     "verbatim, stdlib + Django only) self-applies the gold patch "
                     "to /testbed, drives the real resolve_expression over the "
                     "full 2*2*6*6=144 enumeration of (already_temporal, is_sub, "
                     "t_lhs, t_rhs) -- mapping each type code to a real Value of "
                     "the matching field (T_UNKNOWN -> a Value with no "
                     "output_field, whose .output_field raises FieldError) -- and "
                     "asserts the created wrapper class == resolved_kind, plus the "
                     "two F2P witnesses (bare DateTimeField-DateTimeField resolves "
                     "to a TemporalSubtraction with a DurationField output_field, "
                     "no mixed-types FieldError; DateTimeField-DurationField "
                     "resolves to a DurationExpression). Exit 0 iff every "
                     "observation agrees; any disagreement => the A-reference is "
                     "UNSOUND.",
    },
]
