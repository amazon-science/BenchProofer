"""properties.py — PBT falsification manifest for matplotlib__matplotlib-24149.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The two functions under spec are

    select_position_x0(seq: List[int])    -> int     # x0  selection block
    select_position_xconv(seq: List[int]) -> int     # xconv selection block

of matplotlib's `Axes._convert_dx`. They are STRUCTURALLY IDENTICAL (the gold
patch adds the same `except StopIteration: safe_first_element(...)` fallback to
each of the two `try` blocks), with the SAME contract verbatim:

    # pre-conditions
    Requires(Acc(list_pred(seq), 1 / 2))        # <-- READ-ONLY input (half perm)
    Requires(len(seq) > 0)
    Requires(MustTerminate(2))                  # P3: TOTAL correctness — the
                                                # selection must actually return
    # post-conditions
    Ensures(Acc(list_pred(seq), 1 / 2))                                         # F
    Ensures(Implies(any_finite(ToSeq(seq)),
                    Result() == first_finite_value(ToSeq(seq))))                # P1
    Ensures(len(ToSeq(seq)) == len(seq))                                        # L
    Ensures(Implies(not any_finite(ToSeq(seq)),
                    len(ToSeq(seq)) > 0 and Result() == ToSeq(seq)[0]))         # P2

A coordinate sequence is abstracted to `List[int]` finiteness flags (0 ==
non-finite/NaN/None; non-zero == finite). `any_finite` / `first_finite_value`
are @Pure front-recursive folds over the carrier (NOT opaque oracles).
`first_finite` / `first_unconditional` are the two @ContractOnly axioms for the
unchanged callees `cbook._safe_first_finite` / `cbook.safe_first_element`.

What the spec actually defends, and the attacks it must survive:

  * FRAME (F): `seq` is a READ-ONLY input — `Acc(list_pred(seq), 1/2)` in both
    Requires and Ensures. A rival that WRITES to `seq` to satisfy a postcondition
    vacuously must be REJECTED for insufficient permission. This is the #1
    weakness class and a byte-fuzzer never finds it. MANDATORY (frame-mutation).

  * IDENTITY (P1): under `any_finite`, the result must equal
    `first_finite_value(ToSeq(seq))` — the input's ACTUAL leftmost finite
    element, pinned by a @Pure fold grounded in the carrier. This closed the
    batch05 directive-8 hole: the prior `Result() != 0` was echo-able by any
    finite constant; the current pin is not. The grounded-oracle question: there
    is NO WRONG echo of `first_finite_value`/`first_finite` here — calling the
    axiom `first_finite(ToSeq(seq))` (or the fold `first_finite_value`) IS the
    correct behaviour, and the @Pure PSeq fold has no executable materialization
    other than the actual selection. So instead of a fake echo-reject we attack
    P1 with a WRONG SELECTOR (return the first element unconditionally even when
    the leading element is non-finite) — a real `verify ⇏ resolve` candidate
    that returns a leading-NaN representative. (has_readonly_input=True;
    ungrounded-oracle echo is documented N/A in 'assessment'.)

  * TOTALITY (P2): under `not any_finite` (every flag 0), the result must equal
    `ToSeq(seq)[0]`. Note the abstraction forces `seq[0] == 0` in this branch, so
    the only admissible value IS 0 — `rep = 0` here is CORRECT (not an attackable
    hole); the discriminating content is that the call SUCCEEDS at all (the
    fallback exists). The prepatch rival attacks this directly (it crashes).

  * TERMINATION (P3): `Requires(MustTerminate(2))` — total correctness. Under
    partial-correctness semantics an impl that computes the right value and then
    spins forever before the return satisfies P1/P2 only vacuously (no execution
    reaches the exit) yet its faithful real patch hangs Axes.bar and every
    F2P/P2P test. This is the exact same-spec rival the G-PANEL-1 auditor built
    (atk_4: a diverging loop after the correct selection verified against the
    value-only spec). Under MustTerminate(2) any loop without a decreasing
    termination measure leaks the caller's obligation and is REJECTED.

  * The axioms `first_finite` / `first_unconditional` are validated against the
    REAL `cbook._safe_first_finite` / `cbook.safe_first_element` in Docker
    (reusing + strengthening axiom_check.py); containment is a pure domain check
    (the model only calls `first_finite` under the `any_finite` guard = the
    axiom's Requires, and `first_unconditional` under `len(seq) > 0`).

Authoring mechanics: the two modeled functions have BYTE-IDENTICAL impl regions,
so every spec variant is built by `_swap_all`, which edits BOTH impl regions
(and ONLY inside `# impl-start`/`# impl-end`) consistently — exactly how a real
bug in `_convert_dx` would appear at both the x0 and xconv sites. `same_spec` is
therefore guaranteed (the frozen spec is never touched) and a rejection comes
from the POSTCONDITION / permission system catching wrong behaviour. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P `test_bar_all_nan` (or the value-sensitive P2P
`test_bar_leading_nan`/`test_bar_timedelta`).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24149"
FLOAT_ENCODING = None   # meta.json float_encoding is null (flag carrier is int)

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap_all(src: str, old: str, new: str, n: int = 2) -> str:
    """Replace EXACTLY `n` occurrences of an impl-region substring (the two
    structurally-identical modeled functions share the same impl body, so a
    faithful rival edits both). Assert the count to fail loudly on model.py
    drift. The substring lives strictly inside the # impl-start/# impl-end
    regions, so same_spec is preserved."""
    c = src.count(old)
    if c == 0:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if c != n:
        raise AssertionError(
            f"properties.py: substring count {c} != expected {n}: {old!r}")
    return src.replace(old, new, n)


# ---------------------------------------------------------------------------
# Region landmarks — the shared gold impl body (appears in BOTH functions,
# strictly inside each # impl-start / # impl-end).
# ---------------------------------------------------------------------------
_GOLD_BODY = """    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) Structurally-DIFFERENT but CORRECT: invert the guard so the all-non-finite
# fallback is tested FIRST, then the finite branch. Same selectors, same values,
# different control shape. No induction/lemma is needed (the @Pure any_finite is
# the same predicate; first_finite is still only reached when any_finite holds —
# `not (not any_finite)` — so its Requires is still discharged). If this fails to
# verify the postcondition is over-fit to one branch nesting => SPEC-TOO-STRONG.
_POS_REORDERED_BODY = """    if not any_finite(ToSeq(seq)):
        rep = first_unconditional(ToSeq(seq))
    else:
        rep = first_finite(ToSeq(seq))
    return rep"""
_POS_REORDERED = _swap_all(_BASE, _GOLD_BODY, _POS_REORDERED_BODY)

# (P2) Local-variable reshape: hoist the guard predicate into a typed local
# `finite` and branch on it. Behaviourally identical, different code shape (a
# named intermediate). The Requires(any_finite) of first_finite is discharged via
# the `finite == True` flow. If it fails => the spec is over-fit to the inline
# `if any_finite(ToSeq(seq))` form (SPEC-TOO-STRONG).
_POS_LOCAL_BODY = """    finite = any_finite(ToSeq(seq))  # type: bool
    if finite:
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep"""
_POS_LOCAL = _swap_all(_BASE, _GOLD_BODY, _POS_LOCAL_BODY)

# (P3) GROUNDED-ORACLE POSITIVE CONTROL (in lieu of a wrong echo). The "oracle"
# the postcondition pins to (first_finite_value / the first_finite axiom) is
# GROUNDED in the input carrier — there is no WRONG echo: returning
# first_finite_value(ToSeq(seq)) in the finite branch directly IS the correct,
# pinned selection (it equals first_finite(ToSeq(seq)) by the axiom Ensures). So
# this honest control returns the @Pure fold itself in the finite branch; it must
# verify (P1 is then satisfied by definitional equality). Its purpose is to show
# the spec is not echo-vulnerable: the only thing that satisfies P1 is the actual
# first finite element. If it failed, P1 would be self-inconsistent
# (=> SPEC-TOO-STRONG).
_POS_FOLD_BODY = """    if any_finite(ToSeq(seq)):
        rep = first_finite_value(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep"""
_POS_FOLD = _swap_all(_BASE, _GOLD_BODY, _POS_FOLD_BODY)

# (P4) ADMISSIBILITY. Establish, inside the verified body, every precondition
# conjunct for the EXACT F2P-shaped input the regression exercises: the single
# all-non-finite coordinate `ax.bar([np.nan])`, i.e. the flag list `[0]` (len 1,
# every element non-finite). The probe builds the fresh list (full permission,
# so Acc(list_pred, 1/2) is establishable), asserts `len(probe) > 0` (the only
# value precondition), and — via two drop-unfold stepping stones — asserts
# `not any_finite(ToSeq(probe))`, i.e. the input sits in the P2 (all-non-finite)
# branch the fix is about. If any assert failed => PRECOND-TOO-STRONG / the
# spec's domain excludes the very regression input. (A SELF-CALL is no longer
# usable here: under the P3 total-correctness obligation MustTerminate(2) a
# callee invocation requires a STRICTLY smaller measure than the caller holds,
# so the equal-measure recursive probe is rejected by the obligation system —
# an artifact of the termination spec, not of the value preconditions. The
# sibling MustTerminate bundles use the same assert-on-in-domain-facts shape.)
_ADMISS_HEAD = "    if any_finite(ToSeq(seq)):"
_ADMISS_HEAD_NEW = (
    "    probe = [0]  # type: List[int]\n"
    "    Assert(len(probe) > 0)\n"
    "    Assert(ToSeq(probe)[0] == 0)\n"
    "    Assert(len(ToSeq(probe).drop(1)) == 0)\n"
    "    Assert(not any_finite(ToSeq(probe).drop(1)))\n"
    "    Assert(not any_finite(ToSeq(probe)))\n"
    "    if any_finite(ToSeq(seq)):"
)
_ADMISS = _swap_all(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS / FRAME RIVALS (spec-too-weak / frame probes) — expect "reject"
# ===========================================================================

# (U1) FRAME-MUTATION (MANDATORY — #1 weakness class). The rival overwrites the
# READ-ONLY input `seq` (assign seq[0] = ...) before returning. With only
# Acc(list_pred(seq), 1/2) the function CANNOT write to seq — the verifier must
# reject for INSUFFICIENT PERMISSION (you need full list_pred to mutate an
# element). The gold postconditions are kept verbatim, so the rejection is
# attributable to the WRITE, not to a value mismatch. A real patch that mutated
# the caller's x0/xconv array in place (e.g. `x0[0] = first_finite(x0)`) would
# corrupt the caller's data that downstream `convert(x0 + ddx) - x` reads, and
# would not be the gold one-line fallback — it would NOT resolve (it changes the
# observed bar geometry / P2P image comparisons). Rejection source: the half
# permission Acc(list_pred(seq), 1/2) in pre/post (the permission system).
_RIVAL_FRAME_BODY = """    if any_finite(ToSeq(seq)):
        seq[0] = first_finite(ToSeq(seq))
        rep = seq[0]
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep"""
_RIVAL_FRAME = _swap_all(_BASE, _GOLD_BODY, _RIVAL_FRAME_BODY)

# (U2) PREPATCH / PARTIAL-DOMAIN (the G-DIFF witness). Drop the else branch and
# call first_finite unconditionally — exactly the pre-gold code (no `except
# StopIteration` fallback). Under the function's precondition `len(seq) > 0`
# (which does NOT imply any_finite), first_finite's Requires(any_finite(s))
# cannot be discharged on the all-non-finite input `[0]` — the verifier reports
# "precondition of first_finite might not hold". Rejection source: the
# Requires(any_finite) of the first_finite axiom (= the spec sensing the missing
# fallback). Refinement: this is the unpatched code; on `ax.bar([np.nan])` the
# real _safe_first_finite raises StopIteration, which is uncaught (the inner try
# catches only TypeError/IndexError/KeyError) and crashes Axes.bar — F2P
# test_bar_all_nan fails. Does NOT resolve.
_RIVAL_PREPATCH_BODY = """    rep = first_finite(ToSeq(seq))
    return rep"""
_RIVAL_PREPATCH = _swap_all(_BASE, _GOLD_BODY, _RIVAL_PREPATCH_BODY)

# (U3) WRONG SELECTOR in the finite branch (the value/identity attack on P1).
# Use first_unconditional even when a finite element exists: returns the FIRST
# element (seq[0]) regardless of finiteness, instead of the first FINITE element.
# On a leading-non-finite input like the flag list [0, 1] (a leading NaN then a
# finite value) this returns seq[0] == 0 (the NaN flag), but P1 requires
# first_finite_value([0,1]) == 1. VIOLATES P1. Rejection source:
# Implies(any_finite, Result() == first_finite_value(ToSeq(seq))). Refinement: a
# real patch that called cbook.safe_first_element instead of _safe_first_finite
# would anchor the bar on the LEADING NaN coordinate instead of the first finite
# one; the value-sensitive P2P test_bar_leading_nan asserts the surviving bars
# have finite xy / width, and test_bar_timedelta depends on the actual selected
# coordinate flowing through unit conversion — so it would NOT resolve.
_RIVAL_WRONG_SEL_BODY = """    if any_finite(ToSeq(seq)):
        rep = first_unconditional(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    return rep"""
_RIVAL_WRONG_SEL = _swap_all(_BASE, _GOLD_BODY, _RIVAL_WRONG_SEL_BODY)

# (U5) VACUOUS NON-TERMINATION (the G-PANEL-1 atk_4 class). Compute the CORRECT
# representative, then spin forever before returning it. Under partial
# correctness this VERIFIED (P1/P2/F hold on the never-reached exit — the exact
# same-spec rival the auditor built), and its faithful real patch (an endless
# loop inserted in _convert_dx after the selection) hangs Axes.bar and every
# F2P/P2P test to the harness timeout — verified but NOT resolved. Under P3
# (Requires(MustTerminate(2))) the loop declares no decreasing MustTerminate
# measure, so the caller's termination obligation leaks and Nagini's obligation
# system MUST reject it ("Obligation leak check failed"). The loop invariants
# are exactly what the spinning loop maintains (the read frame), so the
# rejection is attributable to the obligation system, not a broken proof.
_RIVAL_NONTERM_BODY = """    if any_finite(ToSeq(seq)):
        rep = first_finite(ToSeq(seq))
    else:
        rep = first_unconditional(ToSeq(seq))
    while rep == rep:
        Invariant(Acc(list_pred(seq), 1 / 2))
        rep = rep
    return rep"""
_RIVAL_NONTERM = _swap_all(_BASE, _GOLD_BODY, _RIVAL_NONTERM_BODY)

# (U4) INVERTED GUARD (control-flow / domain attack). Swap which branch each
# selector goes in: call first_finite when NOT any_finite, and first_unconditional
# when any_finite. On the all-non-finite input the first_finite call's
# Requires(any_finite(s)) cannot be discharged (precondition failure); and on a
# finite-with-leading-NaN input the first_unconditional branch returns seq[0]
# (non-finite) violating P1. Rejection source: BOTH the Requires(any_finite) of
# first_finite (in the not-any_finite branch) AND P1. Refinement: this inverts
# the patch's fallback logic — it would call safe_first_element on the COMMON
# finite path (anchoring on the leading element, wrong representative) and
# _safe_first_finite on the all-NaN path (re-introducing the StopIteration crash
# test_bar_all_nan checks). Does NOT resolve.
_RIVAL_INVERT_BODY = """    if any_finite(ToSeq(seq)):
        rep = first_unconditional(ToSeq(seq))
    else:
        rep = first_finite(ToSeq(seq))
    return rep"""
_RIVAL_INVERT = _swap_all(_BASE, _GOLD_BODY, _RIVAL_INVERT_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different (all-non-finite fallback tested first via the "
                  "inverted guard) but CORRECT impl with the same selectors/values must verify; "
                  "first_finite is still reached only when any_finite holds (its Requires is "
                  "discharged), no induction lemma needed. If it fails => the postcondition is "
                  "over-fit to one branch nesting (SPEC-TOO-STRONG)."},
    {"id": "pos-control-local", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "a correct impl that hoists the guard predicate into a typed local "
                  "`finite = any_finite(ToSeq(seq))` and branches on it — a different code shape "
                  "for the same behaviour — must verify. If not, the spec is over-fit to the "
                  "inline `if any_finite(ToSeq(seq))` form (SPEC-TOO-STRONG)."},
    {"id": "pos-fold-grounded", "kind": "soundness", "expect": "verify",
     "module": _POS_FOLD,
     "rationale": "the P1 oracle (first_finite_value / first_finite) is GROUNDED in the input — "
                  "there is no wrong echo. Returning the @Pure fold first_finite_value(ToSeq(seq)) "
                  "in the finite branch directly IS the correct pinned selection (it equals "
                  "first_finite(ToSeq(seq)) by the axiom Ensures), so it must verify. Demonstrates "
                  "the spec is not echo-vulnerable: only the actual first finite element satisfies "
                  "P1. If it failed, P1 would be self-inconsistent (SPEC-TOO-STRONG)."},
    {"id": "admiss-f2p-all-nan", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the F2P-shaped regression input — the single all-non-finite coordinate "
                  "ax.bar([np.nan]) modeled as the flag list [0] — must be in-domain: the probe "
                  "builds the fresh list (full permission, so Acc(list_pred,1/2) is establishable) "
                  "and ASSERTS every value precondition (len([0]) == 1 > 0) plus the branch fact "
                  "not any_finite([0]) (the P2 case under repair). If any assert cannot be "
                  "established for the very input the fix targets => PRECOND-TOO-STRONG. "
                  "(Assert-style rather than a self-call: under P3 MustTerminate(2) an equal-"
                  "measure recursive self-call is rejected by the obligation system as an "
                  "artifact, unrelated to the value preconditions.)"},

    # ---- frame + uniqueness rivals (must be REJECTED) ----
    {"id": "rival-frame-mutation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "a faithful real patch of this shape MUTATES the caller's coordinate array in "
                   "place (x0[0] = cbook._safe_first_finite(x0)) before reading it back. That "
                   "corrupts the caller's x0/xconv that downstream convert(x0 + ddx) - x reads, "
                   "changing the rendered bar geometry — the P2P image-comparison tests "
                   "(test_bar_*[png]) would differ, so it would NOT resolve. The gold fix binds a "
                   "LOCAL, never writing the input.",
     "rationale": "FRAME-MUTATION (#1 weakness class). seq is READ-ONLY: pre/post carry only "
                  "Acc(list_pred(seq), 1/2). Writing seq[0] needs FULL list_pred permission, which "
                  "the function does not hold — the verifier rejects for INSUFFICIENT PERMISSION. "
                  "Gold postconditions kept verbatim so the rejection is attributable to the write. "
                  "If it verified => the frame contract is vacuous (SPEC-TOO-WEAK / unsound frame)."},
    {"id": "rival-prepatch-no-fallback", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "the exact pre-gold code (model_prepatch.py): first_finite called "
                   "unconditionally with no except-StopIteration fallback. On ax.bar([np.nan]) the "
                   "real _safe_first_finite raises StopIteration, which the inner try (catching "
                   "only TypeError/IndexError/KeyError) does NOT catch — it propagates and crashes "
                   "Axes.bar. F2P test_bar_all_nan fails; the unpatched code does NOT resolve "
                   "(this is the G-DIFF prepatch witness).",
     "rationale": "PARTIAL-DOMAIN / prepatch. Under the precondition len(seq) > 0 (which does NOT "
                  "imply any_finite) the first_finite call's Requires(any_finite(s)) cannot be "
                  "discharged on the all-non-finite input. Rejection source: the Requires(any_finite) "
                  "of the first_finite axiom (the spec sensing the missing fallback). If it "
                  "verified => SPEC-TOO-WEAK (admits the crash)."},
    {"id": "rival-wrong-selector-leading-nan", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_SEL,
     "refinement": "calls safe_first_element (first element unconditionally) even when a finite "
                   "element exists. On a leading-NaN-then-finite input it anchors the bar on the "
                   "LEADING NaN coordinate instead of the first FINITE one. The value-sensitive "
                   "P2P test_bar_leading_nan asserts the non-leading bars have finite xy/width, and "
                   "test_bar_timedelta depends on the actual selected coordinate flowing through "
                   "unit conversion — a NaN/wrong representative breaks both, so it would NOT resolve.",
     "rationale": "VALUE-IDENTITY attack on P1. On the flag list [0, 1] this returns seq[0] == 0 "
                  "(the non-finite flag) but P1 requires first_finite_value([0,1]) == 1. Rejection "
                  "source: Implies(any_finite, Result() == first_finite_value(ToSeq(seq))) — the "
                  "directive-8-closing identity pin. If it verified => SPEC-TOO-WEAK (the prior "
                  "Result()!=0 hole would re-open)."},
    {"id": "rival-inverted-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "refinement": "inverts the patch's fallback logic: safe_first_element on the COMMON finite "
                   "path (wrong, leading-element representative) and _safe_first_finite on the "
                   "all-NaN path (re-introducing the StopIteration crash). Both the wrong-anchor "
                   "regression (P2P) and the all-NaN crash (F2P test_bar_all_nan) recur, so it "
                   "would NOT resolve.",
     "rationale": "control-flow/domain attack. In the not-any_finite branch first_finite's "
                  "Requires(any_finite(s)) cannot be discharged (the all-non-finite input), AND in "
                  "the any_finite branch first_unconditional returns seq[0] violating P1 on a "
                  "leading-NaN input. Rejection source: Requires(any_finite) of first_finite + P1. "
                  "If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-nonterm-vacuous", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONTERM,
     "refinement": "the faithful real patch of this rival adds an infinite loop to _convert_dx "
                   "after computing the correct representative — Axes.bar never returns, so the "
                   "F2P test_bar_all_nan and every P2P test hang to the harness timeout; it does "
                   "NOT resolve. This is the exact same-spec impl the G-PANEL-1 auditor exhibited "
                   "(atk_4) while the spec was partial-correctness only.",
     "rationale": "VACUOUS NON-TERMINATION. The impl computes the right value then spins in "
                  "`while rep == rep:` forever; P1/P2/F hold only vacuously (no execution reaches "
                  "the return). Rejection source: P3 Requires(MustTerminate(2)) — the loop takes "
                  "no termination obligation and has no decreasing measure, so Nagini reports "
                  "'Obligation leak check failed'. If it verified => SPEC-TOO-WEAK (the atk_4 "
                  "hole would re-open)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real matplotlib callee) — two A-consumed axioms.
# Reuse + strengthen axiom_check.py. The probes EXECUTE the real callee (never
# scrape source); files opened with encoding='utf-8'; nothing but stdlib +
# numpy + matplotlib.cbook imported. axiom_check.py is NOT mounted in-container,
# so its load-bearing logic is embedded directly below.
# ===========================================================================

# (A1) axiom-soundness for first_finite ↔ cbook._safe_first_finite.
# Under the precondition any_finite(s) the real callee must return normally with
# THE FIRST FINITE element of the input (identity, observable because finite flags
# materialize as DISTINCT finite floats) — the Ensures(Result()==first_finite_value(s)).
# Outside the precondition (all non-finite) the base_commit (3.6) callee raises
# StopIteration — confirming Requires(any_finite) is the WEAKEST sound guard and
# witnessing the regression. (Version-adaptive: a later refactor absorbed the
# fallback; the load-bearing identity check holds unconditionally.)
_AX_FIRST_FINITE = r'''
import math, random, sys
import numpy as np
from matplotlib import cbook

def any_finite(flags):
    for f in flags:
        if f != 0:
            return True
    return False

def first_finite_index(flags):
    for i, f in enumerate(flags):
        if f != 0:
            return i
    return -1

def to_values(flags):
    # finite flag -> a DISTINCT finite float (identity observable); 0 -> NaN
    return [float(i + 1) if f != 0 else float("nan") for i, f in enumerate(flags)]

def flag_of(value):
    if value is None:
        return 0
    if np.isscalar(value):
        return 1 if bool(np.isfinite(value)) else 0
    return 1

def raises_when_no_finite():
    try:
        cbook._safe_first_finite([float("nan")])
        return False
    except StopIteration:
        return True
    except Exception:
        return False

RAISES = raises_when_no_finite()

def check(flags):
    vals = to_values(flags)
    if any_finite(flags):
        idx = first_finite_index(flags)
        expected = vals[idx]
        try:
            observed = cbook._safe_first_finite(vals)
        except StopIteration:
            print("AXIOM-UNSOUND first_finite: raised StopIteration although a "
                  "finite element exists:", vals); sys.exit(1)
        if flag_of(observed) == 0:
            print("AXIOM-UNSOUND first_finite: returned a non-finite element",
                  observed, "for", vals); sys.exit(1)
        # IDENTITY: must be THE first finite element (the value first_finite_value pins).
        if observed != expected:
            print("AXIOM-UNSOUND first_finite: returned", observed,
                  "but the axiom pins the FIRST finite element", expected,
                  "(index", idx, ") for", vals); sys.exit(1)
    else:
        if len(vals) == 0:
            return  # excluded by the function precondition len(seq) > 0
        if RAISES:
            raised = False
            try:
                cbook._safe_first_finite(vals)
            except StopIteration:
                raised = True
            if not raised:
                print("WEAKEST-GUARD VIOLATION: _safe_first_finite did NOT raise "
                      "on all-non-finite", vals, "- the no-finite case is reachable "
                      "without the any_finite guard"); sys.exit(1)

boundary = [[1], [0], [0, 0], [0, 0, 0], [1, 1], [1, 0], [0, 1],
            [0, 0, 1], [1, 0, 1], [0, 1, 0], [1, 1, 1, 1]]
for case in boundary:
    check(case)

# explicit all-NaN regression witness (the exact ax.bar([nan]) case).
if RAISES:
    raised = False
    try:
        cbook._safe_first_finite([float("nan")])
    except StopIteration:
        raised = True
    if not raised:
        print("all-NaN input must raise StopIteration in _safe_first_finite"); sys.exit(1)

rng = random.Random(24149)
for _ in range(20000):
    n = rng.randint(1, 12)
    check([1 if rng.random() < 0.5 else 0 for _ in range(n)])

mode = ("base_commit 3.6 (raises StopIteration on all-non-finite)"
        if RAISES else "post-refactor (callee falls back internally)")
print("AXIOM first_finite SOUND: under any_finite the real cbook._safe_first_finite "
      "returns exactly the FIRST FINITE element (identity over distinct floats) over "
      "%d boundary + 20000 fuzz sequences; installed callee mode: %s"
      % (len(boundary), mode))
sys.exit(0)
'''

# (A2) axiom-soundness for first_unconditional ↔ cbook.safe_first_element.
# On a non-empty sequence the real callee must return the FIRST element
# (NaN-aware identity) — the Ensures(Result() == s[0]). This is the fallback the
# patch reaches on an all-non-finite input.
_AX_FIRST_UNCOND = r'''
import math, random, sys
import numpy as np
from matplotlib import cbook

def to_values(flags):
    return [float(i + 1) if f != 0 else float("nan") for i, f in enumerate(flags)]

def check(flags):
    vals = to_values(flags)
    if len(vals) == 0:
        return  # precondition len(s) > 0
    observed = cbook.safe_first_element(vals)
    first = vals[0]
    ok = (observed is first) or (observed == first) or (
        isinstance(observed, float) and isinstance(first, float)
        and math.isnan(observed) and math.isnan(first))
    if not ok:
        print("AXIOM-UNSOUND first_unconditional: safe_first_element returned",
              observed, "but the axiom pins the FIRST element", first, "for", vals)
        sys.exit(1)

boundary = [[1], [0], [0, 0], [0, 0, 0], [1, 1], [1, 0], [0, 1],
            [0, 0, 1], [1, 0, 1], [0, 1, 0], [1, 1, 1, 1]]
for case in boundary:
    check(case)

# all-NaN fallback witness: safe_first_element returns the (NaN) first element.
if not math.isnan(cbook.safe_first_element([float("nan")])):
    print("all-NaN fallback: safe_first_element must return the (NaN) first element")
    sys.exit(1)

rng = random.Random(241490)
for _ in range(20000):
    n = rng.randint(1, 12)
    check([1 if rng.random() < 0.5 else 0 for _ in range(n)])

print("AXIOM first_unconditional SOUND: cbook.safe_first_element returns the FIRST "
      "element (NaN-aware identity) over %d boundary + 20000 fuzz sequences."
      % len(boundary))
sys.exit(0)
'''

# (A3) axiom-containment for first_finite. The model's ONLY call site is the
# `if any_finite(ToSeq(seq))` branch: `rep = first_finite(ToSeq(seq))`. So every
# input the model forwards to first_finite satisfies `any_finite` — which is
# EXACTLY the axiom's Requires(any_finite(s)). This is a pure domain check: over
# a wide enumeration of flag patterns the model can reach (any non-empty list
# under the function precondition len(seq) > 0), assert that whenever the model
# reaches the first_finite call (i.e. any_finite holds), the axiom's Requires
# holds — by construction they are the SAME predicate, so no caller-reachable
# input lies outside the axiom domain. A reachable input outside any_finite would
# be AXIOM-TOO-WEAK-FOR-CALLER (none can exist). No real-callee execution needed.
_AX_CONTAINMENT_FF = r'''
import random, sys

def any_finite(flags):
    for f in flags:
        if f != 0:
            return True
    return False

# axiom Requires(first_finite): any_finite(s)  (verbatim from model.py axioms).
def axiom_requires(flags):
    return any_finite(flags)

# the model reaches `first_finite(ToSeq(seq))` ONLY inside `if any_finite(...)`,
# under the function precondition len(seq) > 0.
def model_reaches_first_finite(flags):
    return len(flags) > 0 and any_finite(flags)

violations = []
n = 0
# exhaustive small patterns + randomized.
def all_patterns(maxlen):
    pats = []
    for L in range(1, maxlen + 1):
        for v in range(1 << L):
            pats.append([(v >> i) & 1 for i in range(L)])
    return pats

for flags in all_patterns(8):
    if model_reaches_first_finite(flags) and not axiom_requires(flags):
        violations.append(flags)
    n += 1

rng = random.Random(2414901)
for _ in range(20000):
    L = rng.randint(1, 16)
    flags = [1 if rng.random() < 0.5 else 0 for _ in range(L)]
    if model_reaches_first_finite(flags) and not axiom_requires(flags):
        violations.append(flags)
    n += 1

if violations:
    print("AXIOM-TOO-WEAK-FOR-CALLER first_finite: model reaches inputs outside "
          "any_finite:", violations[:8]); sys.exit(1)
print("CONTAINMENT OK first_finite: over %d flag patterns every input the model "
      "forwards to first_finite (only under the any_finite guard) lies in the "
      "axiom's Requires(any_finite) domain (identical predicates)." % n)
sys.exit(0)
'''

# (A4) axiom-containment for first_unconditional. The model's ONLY call site is
# `rep = first_unconditional(ToSeq(seq))` in the `else` (not any_finite) branch.
# The axiom's Requires is `len(s) > 0`, which is EXACTLY the function's own
# precondition Requires(len(seq) > 0) — so every input the model forwards to
# first_unconditional is non-empty by construction. (Note: ToSeq preserves length,
# Ensures(len(ToSeq(seq)) == len(seq)).) A reachable empty input would be
# AXIOM-TOO-WEAK-FOR-CALLER (none can exist; the function precondition forbids it).
_AX_CONTAINMENT_FU = r'''
import random, sys

def any_finite(flags):
    for f in flags:
        if f != 0:
            return True
    return False

# axiom Requires(first_unconditional): len(s) > 0  (verbatim from model.py).
def axiom_requires(flags):
    return len(flags) > 0

# the model reaches `first_unconditional(ToSeq(seq))` ONLY in the else (not
# any_finite) branch, under the function precondition len(seq) > 0; ToSeq
# preserves length.
def model_reaches_first_unconditional(flags):
    return len(flags) > 0 and not any_finite(flags)

violations = []
n = 0
def all_patterns(maxlen):
    pats = []
    for L in range(1, maxlen + 1):
        for v in range(1 << L):
            pats.append([(v >> i) & 1 for i in range(L)])
    return pats

for flags in all_patterns(8):
    if model_reaches_first_unconditional(flags) and not axiom_requires(flags):
        violations.append(flags)
    n += 1

rng = random.Random(2414902)
for _ in range(20000):
    L = rng.randint(1, 16)
    flags = [1 if rng.random() < 0.5 else 0 for _ in range(L)]
    if model_reaches_first_unconditional(flags) and not axiom_requires(flags):
        violations.append(flags)
    n += 1

if violations:
    print("AXIOM-TOO-WEAK-FOR-CALLER first_unconditional: model reaches inputs "
          "outside len(s) > 0:", violations[:8]); sys.exit(1)
print("CONTAINMENT OK first_unconditional: over %d flag patterns every input the "
      "model forwards to first_unconditional lies in the axiom's Requires(len(s)>0) "
      "domain (it is the function's own precondition)." % n)
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-first-finite-sound", "axiom": "first_finite", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_FIRST_FINITE,
     "rationale": "the real cbook._safe_first_finite, under any_finite, must return exactly the "
                  "FIRST FINITE element (identity, distinct floats) — the Ensures(Result()=="
                  "first_finite_value(s)) the proof consumes for P1; and outside the precondition "
                  "(all non-finite) the base_commit 3.6 callee raises StopIteration, confirming "
                  "Requires(any_finite) is the weakest sound guard. Any disagreement => AXIOM-UNSOUND."},
    {"id": "ax-first-unconditional-sound", "axiom": "first_unconditional", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_FIRST_UNCOND,
     "rationale": "the real cbook.safe_first_element on a non-empty sequence must return the FIRST "
                  "element (NaN-aware identity) — the Ensures(Result()==s[0]) the proof consumes "
                  "for the all-non-finite fallback P2. Any disagreement => AXIOM-UNSOUND."},
    {"id": "ax-first-finite-containment", "axiom": "first_finite", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT_FF,
     "rationale": "the model calls first_finite ONLY inside the `if any_finite(ToSeq(seq))` guard, "
                  "so every input it forwards satisfies any_finite = the axiom's Requires "
                  "(identical predicates). A caller-reachable input outside any_finite would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER (none can exist)."},
    {"id": "ax-first-unconditional-containment", "axiom": "first_unconditional",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT_FU,
     "rationale": "the model calls first_unconditional ONLY in the else branch under the function "
                  "precondition len(seq) > 0 (ToSeq preserves length), so every forwarded input is "
                  "non-empty = the axiom's Requires(len(s) > 0). A reachable empty input would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER (the function precondition forbids it)."},
]
