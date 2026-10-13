"""properties.py — PBT falsification manifest for django__django-13121.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The bundle models TWO changed decision functions of
`django/db/models/expressions.py` (post the gold patch):

    select_arithmetic_path(lhs_kind, rhs_kind, is_subtract, native_duration) -> int
        models the rendering-class dispatch in CombinedExpression.as_sql:
        DurationExpression / TemporalSubtraction / plain CombinedExpression.
    operand_format_flag(operand_kind, is_literal) -> int
        models DurationExpression.compile's per-operand format decision.

The load-bearing contracts (verbatim from model.py):

  select_arithmetic_path:
    Requires(is_kind(lhs_kind)); Requires(is_kind(rhs_kind))     # int domain only
    Requires(MustTerminate(2))                                   # TERMINATION
    Ensures(Result() in {PATH_DURATION, PATH_TEMPORAL, PATH_PLAIN})
    Ensures(Implies(not native and (lhs==DUR or rhs==DUR) and lhs!=rhs,
                    Result()==PATH_DURATION))                    # DURATION pin
    Ensures(Implies(lhs==DUR and rhs==DUR, Result()!=PATH_DURATION))  # discriminator
    Ensures(Implies(not(dur_guard) and is_subtract and is_temporal(lhs)
                    and lhs==rhs, Result()==PATH_TEMPORAL))       # TEMPORAL pin
    Ensures(Implies(not(dur_guard) and not(temporal_guard),
                    Result()==PATH_PLAIN))                        # PLAIN pin
  operand_format_flag:
    Requires(is_kind(operand_kind))
    Requires(MustTerminate(6))                                   # TERMINATION
    Ensures(Result()==0 or Result()==1)
    Ensures(Result()==1 if operand_kind==KIND_DURATION else Result()==0)  # exact pin

Both functions are loop-free and non-recursive, so MustTerminate carries no loop
measure here: its content is entirely the LEVEL ORDER. The levels (6 for
operand_format_flag, 2 for select_arithmetic_path) are ordinals chosen so that
operand_format_flag may call select_arithmetic_path but not vice versa, with room
beneath both for library callees. That order is load-bearing rather than
decorative, and it is what makes the obligation bite: a call at a level that is
not strictly above its callee's leaks, and a SELF-call — which reproduces its own
level — can never take the obligation from itself. Measured, all three directions:
level 6 -> 2 verifies; level 2 -> 6 leaks; level 1 -> 2 leaks. So the obligation
rejects unbounded self-recursion structurally, which is precisely what
rival-diverging-self-call exercises.

WHAT THE SPEC DEFENDS, AND THE ATTACKS IT MUST SURVIVE:

  * NO READ-ONLY (Acc(.,1/2)) INPUTS. Both functions take only pass-by-value
    primitives (int kind codes, bools); there is no heap object held read-only,
    so the FRAME-MUTATION class is structurally N/A here (there is nothing to
    write through). See 'assessment'. (has_readonly_input=False is honest.)

  * THE POSTCONDITION IS FULLY GROUNDED AND TOTAL — NOT AN ORACLE ECHO. The four
    Implies clauses of select_arithmetic_path uniquely pin Result() to the gold
    value on EVERY input in the finite domain (verified exhaustively: for all
    6x6x2x2 inputs exactly one of {DURATION,TEMPORAL,PLAIN} satisfies all
    clauses, and it equals gold); operand_format_flag's value is an exact
    function of operand_kind. The pins are functions of the *arguments* (no
    @Pure answer-key, no opaque marker to echo), so there is no WRONG echo to
    construct — any rival returning a wrong value on any input is rejected by the
    pins. The honest cheapest impl is the structural positive control below.

  * THE TWO DISCRIMINATORS (the content the gold patch adds):
     - duration+duration on a non-native backend is NOT routed to the
       duration-arithmetic subclass — the added `lhs_type != rhs_type` guard.
       model_prepatch.py drops it and fails the discriminator pin (G-DIFF #1).
       Rival `rival-prepatch-dur-dur` reproduces it.
     - a LITERAL duration operand IS formatted (the removed DurationValue
       exemption). model_prepatch_2.py reinstates `if is_literal: return 0` and
       fails the exact pin (G-DIFF #2). Rival `rival-literal-exemption`
       reproduces it.

  * SUB-DOMAIN ATTACKS on the three guards (partial-domain): dropping the
    `native_duration` gate, dropping the `is_subtract` gate on the temporal path,
    and widening the temporal family beyond {date,datetime,time}. Each is correct
    on most of the domain but diverges on a witness sub-domain the pins catch.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY text strictly inside a `# impl-start`/`# impl-end` region, so
`markers.same_spec` is guaranteed and any rejection is attributable to the frozen
POSTCONDITION catching a wrong value, never to a tampered spec. The two impl
bodies are DISTINCT (one returns PATH_* codes, the other 0/1), so each impl
substring occurs EXACTLY once; `_swap` asserts uniqueness so silent drift (a
model.py edit) fails loudly at load. Each `expect:"reject"` rival carries the
refinement argument that its faithful real patch would NOT resolve the F2P
(`test_duration_expressions`).

Axiom lane: this bundle consumes NO @ContractOnly axioms (meta.axioms == []).
The two A-reference deep models are validated against the REAL post-patch Django
callees in Docker (mirroring axiom_check.py): the real
CombinedExpression.as_sql dispatch and DurationExpression.compile, plus the
durations-only F2P scenario round-trip on SQLite, plus a containment note that
the model's finite int domain maps onto the callee's full reachable input set.
"""
from pathlib import Path

INSTANCE = "django__django-13121"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace the UNIQUE occurrence of an impl-region substring. Assert it
    appears exactly once so silent drift (model.py edited) fails loudly at
    load and we never accidentally touch the frozen spec twice."""
    n = src.count(old)
    if n == 0:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if n != 1:
        raise AssertionError(
            f"properties.py: expected 1 occurrence, found {n}: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (strictly INSIDE the impl regions of model.py).
# ---------------------------------------------------------------------------

# Full impl body of select_arithmetic_path (between its # impl-start/# impl-end).
_PATH_IMPL = """    if (not native_duration) and \\
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \\
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()"""

# Full impl body of operand_format_flag.
_FMT_IMPL = """    if operand_kind == KIND_DURATION():
        return 1
    return 0"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-different but CORRECT select_arithmetic_path: compute the
# guards into local bools and select the result into a single local with an
# explicit if/elif/else (different control shape, opposite to the fall-through
# code form), single return point. No loop / @Pure fold is involved, so no
# induction lemma is needed — the verifier discharges it from the same pins.
# If this fails to verify, the postcondition is over-fit to the fall-through
# return shape => SPEC-TOO-STRONG.
_PATH_POS = """    dur = (not native_duration) and \\
        (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \\
        lhs_kind != rhs_kind
    temporal = is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind
    result = PATH_PLAIN()  # type: int
    if dur:
        result = PATH_DURATION()
    elif temporal:
        result = PATH_TEMPORAL()
    else:
        result = PATH_PLAIN()
    return result"""
_POS_PATH = _swap(_BASE, _PATH_IMPL, _PATH_POS)

# (5b) Structurally-different but CORRECT operand_format_flag: invert the test
# (branch on the NON-duration case first) and compute into a single local.
# Semantically identical to the gold two-statement form. If it fails to verify
# the spec is over-fit to one branch order => SPEC-TOO-STRONG.
_FMT_POS = """    flag = 1  # type: int
    if operand_kind != KIND_DURATION():
        flag = 0
    return flag"""
_POS_FMT = _swap(_BASE, _FMT_IMPL, _FMT_POS)

# (6) ADMISSIBILITY. Calls on F2P-shaped in-domain inputs must establish the
# Requires (is_kind(.)) for normal inputs. The F2P scenario
# (test_duration_expressions) drives a DurationField column + timedelta literal,
# i.e. the (KIND_DURATION, KIND_DURATION) dispatch and a literal duration
# operand. We call select_arithmetic_path on those shapes (plus a mixed pairing,
# a native-backend pairing, a non-temporal same-kind subtraction and a
# KIND_NONE operand) from the top of operand_format_flag's impl, then run the
# gold body unchanged. If such a call cannot establish is_kind(.) for a
# legitimate int code => PRECOND-TOO-STRONG.
#
# The probes are driven from operand_format_flag (MustTerminate level 6) into
# select_arithmetic_path (level 2) rather than from a SELF-call, because the
# termination obligation orders callers strictly above callees: a self-call
# reproduces the caller's own level and so can never take the obligation from
# itself, no matter how its arguments shrink. Measured, all three directions:
#   level 6 -> level 2 (this case)          verifies
#   level 2 -> level 6 (reverse direction)  "Callee operand_format_flag might
#                                            not take all unsatisfied obligations"
#   level 1 -> level 2 (caller too low)     same leak on select_arithmetic_path
# So the probed property (normal in-domain inputs satisfy the preconditions) is
# unchanged and still fully exercised — six argument shapes rather than the
# previous five — only the CALL SITE moved to a direction the level order
# permits. The old self-call form is retained as a reject-lane rival below,
# since it is a genuinely diverging impl.
_FMT_ADMISS = """    _dd = select_arithmetic_path(KIND_DURATION(), KIND_DURATION(), False, False)
    _mix = select_arithmetic_path(KIND_DURATION(), KIND_DATETIME(), False, False)
    _sub = select_arithmetic_path(KIND_DATE(), KIND_DATE(), True, False)
    _oth = select_arithmetic_path(KIND_OTHER(), KIND_OTHER(), True, False)
    _nat = select_arithmetic_path(KIND_DURATION(), KIND_DATETIME(), False, True)
    _non = select_arithmetic_path(KIND_NONE(), KIND_TIME(), True, False)
""" + _FMT_IMPL
_POS_ADMISS = _swap(_BASE, _FMT_IMPL, _FMT_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) THE DURATION+DURATION DISCRIMINATOR (pre-patch bug, G-DIFF #1). Drop the
# `lhs_kind != rhs_kind` conjunct so EITHER side being a duration routes to the
# duration-arithmetic subclass — exactly the pre-patch guard
# `(lhs_output ... == 'DurationField') or (rhs_output ... == 'DurationField')`
# (model_prepatch.py reverts to this). Its faithful real patch is the unchanged
# pre-patch as_sql, which routes a duration+timedelta-literal (both DurationField)
# arithmetic through DurationExpression and so re-raises the
# `decimal.InvalidOperation` on the F2P test_duration_expressions — it would NOT
# resolve. Rejection source: the discriminator pin
# Implies(lhs==DUR and rhs==DUR, Result()!=PATH_DURATION) — violated on
# (KIND_DURATION, KIND_DURATION).
_PATH_PREPATCH = """    if (not native_duration) and \\
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()):
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()"""
_RIVAL_PREPATCH = _swap(_BASE, _PATH_IMPL, _PATH_PREPATCH)

# (2) PARTIAL-DOMAIN — drop the native_duration gate. A mixed duration+temporal
# pairing is routed to the duration-arithmetic subclass even on a backend with a
# native duration field. Its faithful real patch removes
# `not connection.features.has_native_duration_field` from the guard, so on
# PostgreSQL (native duration) a duration+datetime arithmetic would wrongly route
# to DurationExpression instead of the plain combination — breaking the
# native-backend P2P duration-arithmetic behaviour (the F2P/P2P suite runs across
# backends). It would NOT resolve. Rejection source: the PLAIN pin — on
# (lhs=DUR, rhs=DATETIME, native=True) the guard `not(dur_guard)` holds (dur_guard
# is false because native), `not(temporal_guard)` holds, so Result() must be
# PATH_PLAIN, but the rival returns PATH_DURATION.
_PATH_NO_NATIVE = """    if (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \\
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()"""
_RIVAL_NO_NATIVE = _swap(_BASE, _PATH_IMPL, _PATH_NO_NATIVE)

# (3) PARTIAL-DOMAIN — drop the is_subtract gate on the temporal path. Same-kind
# temporal operands are routed to TemporalSubtraction for ANY connector, not just
# subtraction. Its faithful real patch removes `self.connector == self.SUB` from
# the temporal guard, so a date+date ADDITION (or any non-SUB same-temporal
# combination) would wrongly route through TemporalSubtraction instead of the
# plain combination — changing rendered SQL for those P2P expression scenarios.
# It would NOT resolve. Rejection source: the PLAIN pin — on
# (lhs=rhs=DATE, is_subtract=False, native=False) `not(dur_guard)` holds and
# `not(temporal_guard)` holds (temporal_guard requires is_subtract), so Result()
# must be PATH_PLAIN, but the rival returns PATH_TEMPORAL.
_PATH_NO_SUB = """    if (not native_duration) and \\
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \\
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()"""
_RIVAL_NO_SUB = _swap(_BASE, _PATH_IMPL, _PATH_NO_SUB)

# (4) PARTIAL-DOMAIN — widen the temporal family. Replace the temporal-kind test
# with a bare same-kind test, so ANY same-kind subtraction (including
# non-temporal kinds like KIND_NONE / KIND_OTHER) routes to TemporalSubtraction.
# Its faithful real patch drops the `lhs_type in {'DateField','DateTimeField',
# 'TimeField'}` membership, so e.g. an IntegerField - IntegerField subtraction
# would wrongly route through TemporalSubtraction instead of the plain
# combination — corrupting ordinary numeric-subtraction SQL across the P2P suite.
# It would NOT resolve. Rejection source: the PLAIN pin — on
# (lhs=rhs=KIND_OTHER, is_subtract=True, native=False) is_temporal_kind is false
# so temporal_guard is false and Result() must be PATH_PLAIN, but the rival
# returns PATH_TEMPORAL.
_PATH_WIDE_TEMP = """    if (not native_duration) and \\
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \\
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_subtract and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()"""
_RIVAL_WIDE_TEMP = _swap(_BASE, _PATH_IMPL, _PATH_WIDE_TEMP)

# (5) THE LITERAL-EXEMPTION BUG (pre-patch behaviour, G-DIFF #2). Reinstate the
# DurationValue exemption: a literal duration operand is NOT formatted. Its
# faithful real patch reinstates the deleted `if not isinstance(side,
# DurationValue):` guard, so the literal `timedelta` operand of
# `F('estimated_time') + delta` is left unformatted — exactly the bug that makes
# `convert_durationfield_value` raise `decimal.InvalidOperation` on the F2P
# test_duration_expressions. It would NOT resolve. Rejection source: the exact
# pin Result()==1 if operand_kind==KIND_DURATION else 0 — violated on
# (KIND_DURATION, is_literal=True).
_FMT_EXEMPT = """    if operand_kind == KIND_DURATION() and not is_literal:
        return 1
    return 0"""
_RIVAL_LIT_EXEMPT = _swap(_BASE, _FMT_IMPL, _FMT_EXEMPT)

# (6, supporting near-miss) FORMAT INVERSION. Always format unless duration —
# the format flag is exactly inverted. A real patch returning the wrong wrapper
# decision would format every NON-duration operand and skip every duration one,
# garbling all rendered arithmetic — it would NOT resolve. Rejection source: the
# exact pin on every input. Carries a genuine refinement; supporting only.
_FMT_INVERT = """    if operand_kind == KIND_DURATION():
        return 0
    return 1"""
_RIVAL_FMT_INVERT = _swap(_BASE, _FMT_IMPL, _FMT_INVERT)

# (7) DIVERGENCE — the unguarded self-call. This is the impl the admissibility
# case above used to carry, moved here because it does not terminate: the
# self-call is the FIRST statement and its guard is vacuous (there is none), so
# select_arithmetic_path re-enters itself on every input before reaching any
# return. Established by execution, not by inspection: running this impl region
# under a recursion limit raises RecursionError for in-domain arguments
# (KIND_DATE, KIND_DATE, True, False), i.e. it returns for NO input at all.
#
# It belongs in the reject lane because the old, termination-silent spec
# ACCEPTED it: with the MustTerminate lines stripped from the preconditions this
# very file verifies ("Verification successful"), which is exactly the
# partial-correctness hole the obligation exists to close — every Ensures held
# vacuously of a run that never reaches the return. With the obligation present
# Nagini rejects it: "Obligation leak check failed. Callee
# select_arithmetic_path might not take all unsatisfied obligations from the
# caller." A faithful real patch whose as_sql dispatch re-entered itself before
# dispatching would hang the F2P test_duration_expressions rather than fail it —
# it would NOT resolve. Rejection source: the termination obligation
# Requires(MustTerminate(2)), not any value pin (the returned values, when
# reached, would be gold's).
_PATH_DIVERGE = """    _dd = select_arithmetic_path(KIND_DURATION(), KIND_DURATION(), False, False)
    _mix = select_arithmetic_path(KIND_DURATION(), KIND_DATETIME(), False, False)
    _sub = select_arithmetic_path(KIND_DATE(), KIND_DATE(), True, False)
    _f1 = operand_format_flag(KIND_DURATION(), True)
    _f0 = operand_format_flag(KIND_OTHER(), False)
""" + _PATH_IMPL
_RIVAL_DIVERGE = _swap(_BASE, _PATH_IMPL, _PATH_DIVERGE)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-path-single-return", "kind": "soundness", "expect": "verify",
     "module": _POS_PATH,
     "rationale": "structurally-different but semantically identical "
                  "select_arithmetic_path: guards computed into local bools, result selected via "
                  "if/elif/else into a single local with one return (opposite of the gold "
                  "fall-through form). No loop/@Pure fold => no induction lemma needed; the same "
                  "pins discharge it. If it fails to verify the postcondition is over-fit to the "
                  "fall-through return shape => SPEC-TOO-STRONG. Verified offline to match gold on "
                  "all 6x6x2x2 inputs."},
    {"id": "pos-control-format-inverted-test", "kind": "soundness", "expect": "verify",
     "module": _POS_FMT,
     "rationale": "structurally-different but semantically identical operand_format_flag: branch "
                  "on the NON-duration case first, compute into a single local. If it fails to "
                  "verify the spec is over-fit to one branch order => SPEC-TOO-STRONG."},
    {"id": "admiss-self-calls", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "calls on F2P-shaped in-domain inputs (duration+duration dispatch, mixed "
                  "duration+datetime, same-temporal subtraction, non-temporal same-kind "
                  "subtraction, a native-backend mixed pairing and a KIND_NONE operand) must "
                  "establish the Requires (is_kind(.)) for normal int codes; if any cannot, "
                  "PRECOND-TOO-STRONG. The gold body runs unchanged after. Driven from "
                  "operand_format_flag (MustTerminate level 6) into select_arithmetic_path "
                  "(level 2): the obligation orders callers strictly above callees, so a SELF-call "
                  "reproduces its own level and can never take the obligation from itself. The "
                  "probed property is unchanged; only the call site sits on a legal edge. The old "
                  "self-call form is now rival-diverging-self-call, since it never returns."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-prepatch-dur-dur", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "drops the added `lhs_kind != rhs_kind` conjunct so EITHER side being a "
                   "duration routes to the duration-arithmetic subclass — exactly the PRE-PATCH "
                   "guard (model_prepatch.py reverts to this). Its faithful real patch is the "
                   "unchanged pre-patch CombinedExpression.as_sql, which routes a "
                   "duration+timedelta-literal arithmetic (both DurationField) through "
                   "DurationExpression and re-raises decimal.InvalidOperation on the F2P "
                   "test_duration_expressions — it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (G-DIFF #1 / model_prepatch.py). "
                  "Rejection source: the discriminator pin Implies(lhs==KIND_DURATION and "
                  "rhs==KIND_DURATION, Result()!=PATH_DURATION) — violated on "
                  "(KIND_DURATION, KIND_DURATION) where the rival returns PATH_DURATION. If it "
                  "verified => SPEC-TOO-WEAK (admits the very bug)."},
    {"id": "rival-drop-native-gate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_NATIVE,
     "refinement": "removes `not native_duration` from the duration guard, routing a mixed "
                   "duration+temporal pairing to DurationExpression even on a native-duration "
                   "backend. The faithful real patch drops "
                   "`not connection.features.has_native_duration_field`, so on PostgreSQL "
                   "(native duration) a duration+datetime arithmetic wrongly routes to "
                   "DurationExpression instead of the plain combination, changing rendered SQL on "
                   "the native-backend P2P scenarios — it would NOT resolve.",
     "rationale": "partial-domain: correct on non-native backends, wrong when native_duration is "
                  "true. Rejection source: the PLAIN pin — on (lhs=DURATION, rhs=DATETIME, "
                  "native=True) dur_guard is false (native) and temporal_guard is false, so "
                  "Result() must be PATH_PLAIN, but the rival returns PATH_DURATION. If it "
                  "verified => SPEC-TOO-WEAK (the native-backend gate is unconstrained)."},
    {"id": "rival-drop-subtract-gate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_SUB,
     "refinement": "removes `is_subtract` from the temporal guard, so same-kind temporal operands "
                   "route to TemporalSubtraction for ANY connector. The faithful real patch drops "
                   "`self.connector == self.SUB`, so a date+date ADDITION (or any non-SUB "
                   "same-temporal combination) wrongly routes through TemporalSubtraction instead "
                   "of the plain combination, corrupting that rendered SQL across the P2P "
                   "expression suite — it would NOT resolve.",
     "rationale": "partial-domain: correct under subtraction, wrong on same-temporal non-subtract. "
                  "Rejection source: the PLAIN pin — on (lhs=rhs=DATE, is_subtract=False, "
                  "native=False) temporal_guard requires is_subtract so it is false, hence Result() "
                  "must be PATH_PLAIN, but the rival returns PATH_TEMPORAL. If it verified => "
                  "SPEC-TOO-WEAK (the subtraction gate is unconstrained)."},
    {"id": "rival-widen-temporal-family", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WIDE_TEMP,
     "refinement": "replaces the temporal-kind membership with a bare same-kind test, so ANY "
                   "same-kind subtraction (incl. non-temporal kinds like IntegerField) routes to "
                   "TemporalSubtraction. The faithful real patch drops the "
                   "`lhs_type in {'DateField','DateTimeField','TimeField'}` membership, so an "
                   "IntegerField - IntegerField subtraction wrongly routes through "
                   "TemporalSubtraction instead of the plain combination, corrupting ordinary "
                   "numeric-subtraction SQL across the P2P suite — it would NOT resolve.",
     "rationale": "partial-domain: correct on temporal kinds, wrong on non-temporal same-kind "
                  "subtraction. Rejection source: the PLAIN pin — on (lhs=rhs=KIND_OTHER, "
                  "is_subtract=True, native=False) is_temporal_kind(lhs) is false so temporal_guard "
                  "is false, hence Result() must be PATH_PLAIN, but the rival returns "
                  "PATH_TEMPORAL. If it verified => SPEC-TOO-WEAK (the temporal family is "
                  "unconstrained)."},
    {"id": "rival-literal-exemption", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIT_EXEMPT,
     "refinement": "reinstates the DurationValue exemption (`if operand_kind==KIND_DURATION and "
                   "not is_literal`) — the pre-patch behaviour (model_prepatch_2.py reverts to "
                   "this). Its faithful real patch reinstates the deleted "
                   "`if not isinstance(side, DurationValue):` guard, so the literal timedelta "
                   "operand of `F('estimated_time') + delta` is left unformatted — exactly the bug "
                   "that makes convert_durationfield_value raise decimal.InvalidOperation on the "
                   "F2P test_duration_expressions — it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (G-DIFF #2 / model_prepatch_2.py). "
                  "Rejection source: the exact pin Result()==1 if operand_kind==KIND_DURATION else "
                  "0 — violated on (KIND_DURATION, is_literal=True) where the rival returns 0. If "
                  "it verified => SPEC-TOO-WEAK (admits the literal-exemption bug)."},
    {"id": "rival-format-inverted", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FMT_INVERT,
     "refinement": "inverts the format decision (format iff NOT a duration). A real patch with the "
                   "wrapper decision inverted would skip the format on every duration operand and "
                   "wrap every non-duration one, garbling all duration-arithmetic SQL — it would "
                   "NOT resolve.",
     "rationale": "supporting near-miss with a real refinement. Rejection source: the exact pin on "
                  "every input (it is wrong on all 6 kinds)."},
    {"id": "rival-diverging-self-call", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE,
     "refinement": "DIVERGES — it never returns. The unguarded self-call is the first statement of "
                   "select_arithmetic_path's impl, so the function re-enters itself on every input "
                   "before reaching any return; executing this impl region raises RecursionError "
                   "even for in-domain arguments (KIND_DATE, KIND_DATE, True, False). A faithful "
                   "real patch whose CombinedExpression.as_sql re-entered itself before dispatching "
                   "would HANG the F2P test_duration_expressions rather than fail it — it would NOT "
                   "resolve.",
     "rationale": "the partial-correctness hole the termination obligation closes, and the reason "
                  "this case is in the reject lane rather than the accept lane it started in. "
                  "Measured both ways on this exact source: with MustTerminate stripped from the "
                  "preconditions it VERIFIES (every Ensures holds vacuously of a run that never "
                  "reaches the return — verify without correct); with the obligation present Nagini "
                  "rejects it, 'Obligation leak check failed. Callee select_arithmetic_path might "
                  "not take all unsatisfied obligations from the caller.' Rejection source is "
                  "Requires(MustTerminate(2)) alone, NOT a value pin: the values it would return, "
                  "if it ever returned, are gold's. So this case is only refutable by a spec that "
                  "demands termination, which is a strictly stronger claim than the admissibility "
                  "case it replaced."},
]

# ===========================================================================
# AXIOM LANE — A-reference deep models validated == REAL post-patch Django.
# This bundle consumes NO @ContractOnly axioms (meta.axioms == []); the two
# modeled decisions are A-reference deep models. Per PBT_PLAN §2.4 an
# A-reference deep model is checked the same way a consumed axiom is: the deep
# model must equal the real callee on every caller-reachable input. The probes
# run the REAL post-patch CombinedExpression.as_sql / DurationExpression.compile
# in Docker (gold applied), mirroring axiom_check.py — they EXECUTE the callee,
# never scrape source. Imports django (the repo under test) + stdlib only; files
# opened with encoding="utf-8" per the codec caveat.
# ===========================================================================

# Self-contained Django bootstrap + the model encodings (kept in lock-step with
# model.py / axiom_check.py). Shared by all probes.
_BOOT = r'''
import datetime, itertools, sys

KIND_NONE, KIND_DURATION, KIND_DATE, KIND_DATETIME, KIND_TIME, KIND_OTHER = range(6)
PATH_DURATION, PATH_TEMPORAL, PATH_PLAIN = range(3)
ALL_KINDS = (KIND_NONE, KIND_DURATION, KIND_DATE, KIND_DATETIME, KIND_TIME, KIND_OTHER)
_TEMPORAL = {KIND_DATE, KIND_DATETIME, KIND_TIME}
# field-type names the kind codes refine (None == FieldError -> KIND_NONE).
_NAME = {KIND_NONE: None, KIND_DURATION: 'DurationField', KIND_DATE: 'DateField',
         KIND_DATETIME: 'DateTimeField', KIND_TIME: 'TimeField', KIND_OTHER: 'IntegerField'}
_DATETIME_NAMES = {'DateField', 'DateTimeField', 'TimeField'}

def model_select(lhs, rhs, is_sub, native):
    if (not native) and (lhs == KIND_DURATION or rhs == KIND_DURATION) and lhs != rhs:
        return PATH_DURATION
    if is_sub and lhs in _TEMPORAL and lhs == rhs:
        return PATH_TEMPORAL
    return PATH_PLAIN

def model_format(operand_kind, is_literal):
    return 1 if operand_kind == KIND_DURATION else 0

# the real post-patch dispatch, transcribed from expressions.py:447-461, as an
# ORACLE over the type-name strings (used only by the containment probe; the
# soundness probes drive the REAL classes end-to-end).
def oracle_select(lhs, rhs, is_sub, native):
    lt, rt = _NAME[lhs], _NAME[rhs]
    if (not native) and 'DurationField' in {lt, rt} and lt != rt:
        return PATH_DURATION
    if is_sub and lt in _DATETIME_NAMES and lt == rt:
        return PATH_TEMPORAL
    return PATH_PLAIN

def _configure():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                            '__main__'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()
'''

# (1) axiom-soundness — the REAL end-to-end F2P scenario: a DurationField column
# plus a timedelta literal, annotated and evaluated on SQLite, must round-trip
# the arithmetic WITHOUT raising (the bug raised decimal.InvalidOperation). This
# exercises the real CombinedExpression.as_sql dispatch AND
# DurationExpression.compile (the two A-references). If the round-trip fails the
# A-reference behaviour the model encodes is not what the real callee does =>
# AXIOM-UNSOUND.
_AX_F2P_ROUNDTRIP = _BOOT + r'''
_configure()
from django.db import models, connection
from django.db.models import F

class Experiment(models.Model):
    estimated_time = models.DurationField()
    class Meta:
        app_label = '__main__'

with connection.schema_editor() as se:
    se.create_model(Experiment)

deltas = [datetime.timedelta(days=1), datetime.timedelta(hours=1, minutes=30),
          datetime.timedelta(0), datetime.timedelta(microseconds=42),
          datetime.timedelta(days=3, seconds=7, microseconds=5)]
base = datetime.timedelta(days=2, seconds=10)
Experiment.objects.create(estimated_time=base)
bad = []
for delta in deltas:
    qs = Experiment.objects.annotate(duration=F('estimated_time') + delta)
    for obj in qs:
        if obj.duration != obj.estimated_time + delta:
            bad.append((delta, obj.duration, obj.estimated_time + delta))
if bad:
    print("AXIOM-UNSOUND: duration+timedelta did not round-trip:", bad); sys.exit(1)
print("OK F2P round-trip: %d duration+timedelta-literal annotations evaluated and "
      "matched on SQLite (the real as_sql/compile A-references)" % len(deltas))
sys.exit(0)
'''

# (2) axiom-soundness — the DISPATCH DISCRIMINATOR on the REAL classes: a
# duration+duration arithmetic on the (non-native) SQLite backend must NOT be
# routed to the DurationExpression subclass, and the model must predict
# PATH_PLAIN. This is the content the gold patch added (`lhs_type != rhs_type`).
# If the real resolved expression had both operands DurationField yet the model
# predicted PATH_DURATION, the A-reference would be unsound for the discriminator.
_AX_DISPATCH_DISCRIM = _BOOT + r'''
_configure()
from django.db import models, connection
from django.db.models import F
from django.db.models.expressions import CombinedExpression, Combinable

class Experiment(models.Model):
    estimated_time = models.DurationField()
    class Meta:
        app_label = '__main__'

with connection.schema_editor() as se:
    se.create_model(Experiment)
Experiment.objects.create(estimated_time=datetime.timedelta(days=2, seconds=10))

if connection.features.has_native_duration_field:
    print("AXIOM-UNSOUND: sqlite unexpectedly reports a native duration field"); sys.exit(1)

# both operands durations: F('estimated_time') + timedelta literal.
expr = F('estimated_time') + datetime.timedelta(days=1)
resolved = expr.resolve_expression(Experiment.objects.all().query)
if not isinstance(resolved, CombinedExpression):
    print("AXIOM-MISMATCH: resolved expr is not a CombinedExpression:", type(resolved)); sys.exit(1)
lt = resolved.lhs.output_field.get_internal_type()
rt = resolved.rhs.output_field.get_internal_type()
if not (lt == 'DurationField' and rt == 'DurationField'):
    print("AXIOM-MISMATCH: expected both operands DurationField, got %s / %s" % (lt, rt)); sys.exit(1)
predicted = model_select(KIND_DURATION, KIND_DURATION,
                         resolved.connector == Combinable.SUB,
                         connection.features.has_native_duration_field)
if predicted != PATH_PLAIN:
    print("AXIOM-UNSOUND: model predicts %d for duration+duration, expected PATH_PLAIN" % predicted)
    sys.exit(1)
# the real renderer must not raise for this expression.
compiler = Experiment.objects.all().query.get_compiler(connection.alias)
sql, params = resolved.as_sql(compiler, connection)
if not sql:
    print("AXIOM-UNSOUND: real as_sql produced empty SQL for duration+duration"); sys.exit(1)
print("OK dispatch discriminator: real duration+duration (both DurationField) is "
      "NOT routed to DurationExpression; model predicts PATH_PLAIN; real as_sql "
      "renders without raising")
sys.exit(0)
'''

# (3) axiom-soundness/containment — model == oracle over the WHOLE finite domain.
# The model's int kind codes refine the closed finite set of get_internal_type()
# names; this enumerates EVERY (lhs, rhs, is_subtract, native) and every
# (operand_kind, is_literal) the model can reach and asserts the deep model
# equals the verbatim-source oracle. Because the model's domain is exactly the
# finite name set, every caller-reachable callee-input is covered — there is no
# input outside the A-reference's domain (containment is total). A mismatch =>
# AXIOM-UNSOUND; an uncovered reachable name => AXIOM-TOO-WEAK-FOR-CALLER (none
# exists here — the name set is closed and fully enumerated).
_AX_MODEL_EQ_ORACLE = _BOOT + r'''
bad = []
for lhs, rhs, sub, native in itertools.product(ALL_KINDS, ALL_KINDS, (False, True), (False, True)):
    m = model_select(lhs, rhs, sub, native)
    o = oracle_select(lhs, rhs, sub, native)
    if m != o:
        bad.append(("path", lhs, rhs, sub, native, m, o))
for kind, lit in itertools.product(ALL_KINDS, (False, True)):
    m = model_format(kind, lit)
    o = (1 if _NAME[kind] == 'DurationField' else 0)
    if m != o:
        bad.append(("fmt", kind, lit, m, o))
if bad:
    print("AXIOM-UNSOUND: model != oracle on", bad[:10]); sys.exit(1)
# containment: the model only ever passes kind codes in ALL_KINDS, whose names
# are exactly the closed get_internal_type() name set the dispatch reads; every
# reachable callee-input is therefore inside the A-reference domain.
covered = {_NAME[k] for k in ALL_KINDS}
assert None in covered and 'DurationField' in covered and _DATETIME_NAMES <= covered, covered
print("OK model==oracle over the full finite domain (6x6x2x2 dispatch + 6x2 "
      "format); containment total: model-reachable names = %r cover the closed "
      "get_internal_type() name set the dispatch reads" % (sorted(str(c) for c in covered),))
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-f2p-roundtrip", "axiom": "select_arithmetic_path/operand_format_flag",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_F2P_ROUNDTRIP,
     "rationale": "the REAL post-patch CombinedExpression.as_sql + DurationExpression.compile "
                  "(both A-references) must round-trip a DurationField + timedelta-literal "
                  "annotation on SQLite — the exact F2P test_duration_expressions behaviour. The "
                  "pre-patch code raised decimal.InvalidOperation here; if the real callee fails "
                  "to round-trip, the A-reference behaviour the model encodes is wrong => "
                  "AXIOM-UNSOUND."},
    {"id": "ax-dispatch-discriminator", "axiom": "select_arithmetic_path",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_DISPATCH_DISCRIM,
     "rationale": "the gold-added discriminator on the REAL classes: a duration+duration "
                  "arithmetic (both operands DurationField) on the non-native SQLite backend must "
                  "NOT be routed to DurationExpression and the model must predict PATH_PLAIN; the "
                  "real as_sql must render without raising. If the real dispatch routed it to "
                  "DurationExpression while the model said PATH_PLAIN, the A-reference would be "
                  "unsound for the discriminator."},
    {"id": "ax-model-eq-oracle-containment", "axiom": "select_arithmetic_path/operand_format_flag",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_MODEL_EQ_ORACLE,
     "rationale": "the deep models equal the verbatim post-patch source oracle over the WHOLE "
                  "finite domain (6x6x2x2 dispatch + 6x2 format), and the model's int kind codes "
                  "refine exactly the closed get_internal_type() name set the real dispatch reads "
                  "(== / != / finite-set membership only). Every caller-reachable callee-input is "
                  "covered => containment total; a mismatch would be AXIOM-UNSOUND and an "
                  "uncovered reachable name AXIOM-TOO-WEAK-FOR-CALLER (none exists — closed set "
                  "fully enumerated)."},
]
