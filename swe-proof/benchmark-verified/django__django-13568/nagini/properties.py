# properties.py — PBT falsification battery for django__django-13568. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view is never touched), checked by Nagini verify +
# markers.same_spec. There are no axiom cases (see AXIOM_TESTS at the bottom).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   username_field_diagnostic(field_unique: bool,
#                             c_span:   List[int],   # READ-ONLY  Acc(...,1/2)
#                             c_single: List[int],   # READ-ONLY  Acc(...,1/2)
#                             c_total:  List[int],   # READ-ONLY  Acc(...,1/2)
#                             username_field: int,
#                             default_regime: bool) -> int
#   Models the gold username-uniqueness guard of check_user_model: emit the
#   USERNAME_FIELD-uniqueness diagnostic iff the field is NOT directly unique AND
#   no UNCONDITIONAL single-field UniqueConstraint ranges over exactly that field;
#   the severity is auth.E003 (HARD_ERROR=1) under the single default backend regime,
#   auth.W004 (WARNING=2) otherwise; no diagnostic => NO_DIAGNOSTIC=0.
#
#   PRECONDITION (three READ-ONLY sequence inputs + a length tie):
#     (P1) Requires(Acc(list_pred(c_span),   1/2))   # HALF permission => no write
#     (P2) Requires(Acc(list_pred(c_single), 1/2))
#     (P3) Requires(Acc(list_pred(c_total),  1/2))
#     (P4) Requires(len(c_span)==len(c_single) and len(c_single)==len(c_total))
#   POSTCONDITION (six clauses; four framing/permission/length + two LOAD-BEARING):
#     (Q1-Q3) Ensures(Acc(list_pred(c_*),1/2))       # returns the read permission
#     (Q4)    Ensures(len(c_span)==len(c_single) and len(c_single)==len(c_total))
#     (Q5)    Ensures(Implies(field_unique or any_covers(ToSeq(c_span),ToSeq(c_single),
#                             ToSeq(c_total),username_field), Result()==NO_DIAGNOSTIC))
#     (Q6)    Ensures(Implies(not(field_unique or any_covers(...)),
#                             Result()==(HARD_ERROR if default_regime else WARNING)))
#   where covers(sp,sg,tt,f) := tt==1 and sp==1 and sg==f  and any_covers is the
#   front-recursive existential fold over the three parallel sequences.
#
# FRAME-MUTATION lane is MANDATORY: c_span/c_single/c_total are all Acc(...,1/2)
#   (read-only). A rival that WRITES any of them must be REJECTED for INSUFFICIENT
#   PERMISSION. Byte-fuzzers never think to mutate the input; this is the #1 class.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q5/Q6 are pinned to
#   `field_unique or any_covers(ToSeq(c_span),ToSeq(c_single),ToSeq(c_total),
#   username_field)` and the regime constant — both GROUNDED entirely in the
#   function arguments. `any_covers`/`covers` are @Pure helpers fully unfolded over
#   the input sequences (no @ContractOnly axiom, no opaque answer-key, no exact
#   marker): the pure region computes the answer from the args, it does not assert
#   it. There is therefore no value an echo could carry that satisfies Q5/Q6 yet is
#   wrong — the unique satisfier IS the grounded decision. So the honest control is
#   the cheapest faithful impl that computes that decision (the positive controls
#   below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. The function returns a pure int code; there is no
#   raise / return-vs-fallthrough / side-effect difference invisible to the value
#   abstraction. The only genuine control-flow point of the gold change — emit vs
#   suppress, and at which severity — is fully captured by Q5 (suppress iff
#   field_unique or any_covers) and Q6 (severity by regime), which every rival must
#   satisfy. The append-of-Error-vs-Warning-vs-nothing is the value the int code
#   abstracts (mapping.md §2), not a hidden effect.
#
# PARTIAL-DOMAIN lane: heavily exercised. The decision surface has several sub-
#   domains a rival can get right on most inputs yet diverge on one:
#     - the regime severity (HARD_ERROR vs WARNING)   -> weak-swap-regime
#     - field_unique==False but a covering constraint exists (the F2P
#       test_username_unique_with_model_constraint discriminator) -> weak-prepatch
#     - never-suppress / always-suppress edges        -> weak-always-* supporting
#
# AXIOM lane: meta.axioms == [] and deep_model_references == []. The existential
#   constraint search is modeled DEEPLY (any_covers/covers + the verified backward
#   loop), not behind a @ContractOnly axiom or an A-reference. axiom_check.py /
#   G-AX already validates the deep predicate against real Django UniqueConstraint /
#   total_unique_constraints semantics. Nothing in this bundle's proof rests on an
#   axiom, so AXIOM_TESTS = []. (See 'assessment'.)
from pathlib import Path

INSTANCE = "django__django-13568"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions + the function signature). same_spec is
# computed over the spec_view, which elides every impl region (and nested
# invariants), so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    satisfied = field_unique
    if not satisfied:
        i = len(c_span)
        found = False
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(c_span), 1 / 2))
            Invariant(Acc(list_pred(c_single), 1 / 2))
            Invariant(Acc(list_pred(c_total), 1 / 2))
            Invariant(len(c_span) == len(c_single) and
                      len(c_single) == len(c_total))
            Invariant(0 <= i and i <= len(c_span))
            Invariant(found == any_covers(ToSeq(c_span).drop(i),
                                          ToSeq(c_single).drop(i),
                                          ToSeq(c_total).drop(i),
                                          username_field))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            sp = c_span[i - 1]
            sg = c_single[i - 1]
            tt = c_total[i - 1]
            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
            if tt == 1 and sp == 1 and sg == username_field:
                found = True
            i = i - 1
        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
        satisfied = found
    if satisfied:
        return NO_DIAGNOSTIC
    if default_regime:
        return HARD_ERROR
    return WARNING"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# The loop block (computes the TRUE `found == any_covers(...)`), verbatim, as a
# reusable component so rivals/controls that keep the gold proof reuse it exactly.
# It is written to run UNCONDITIONALLY (the gold's `if not satisfied:` guard is
# factored out by the surrounding control flow in each variant).
_GOLD_LOOP = """\
    i = len(c_span)
    found = False
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(c_span), 1 / 2))
        Invariant(Acc(list_pred(c_single), 1 / 2))
        Invariant(Acc(list_pred(c_total), 1 / 2))
        Invariant(len(c_span) == len(c_single) and
                  len(c_single) == len(c_total))
        Invariant(0 <= i and i <= len(c_span))
        Invariant(found == any_covers(ToSeq(c_span).drop(i),
                                      ToSeq(c_single).drop(i),
                                      ToSeq(c_total).drop(i),
                                      username_field))
        # The constraint-scan loop counts down to 0, so i + 1 stays positive and
        # strictly decreases each step, discharging the caller's obligation.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        sp = c_span[i - 1]
        sg = c_single[i - 1]
        tt = c_total[i - 1]
        Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
        Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
        Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
        Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
        Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
        Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
        if tt == 1 and sp == 1 and sg == username_field:
            found = True
        i = i - 1
    Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
    Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
    Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-eager-loop: structurally DIFFERENT but behaviourally identical. The gold
# guards the loop behind `if not satisfied:` (skip the search when field_unique is
# already True); this control runs the SAME loop UNCONDITIONALLY (eager search) and
# then combines `satisfied = field_unique or found`, with the outcome computed by a
# reshaped nested if/else (regime decided inside the `else` arm). It keeps EVERY
# gold proof obligation verbatim — the same backward loop, the same
# found==any_covers(drop(i)) invariant, the same per-step drop(i-1) framing asserts,
# the same final drop(0)==whole asserts (directives 2/3: no dropped lemma, no
# forward-append against the front-recursive fold). The decision value is identical:
# satisfied == field_unique or any_covers(full). If it FAILS => SPEC-TOO-STRONG (a
# faithful, structurally-different correct impl is rejected).
_POS_EAGER = (
    _GOLD_LOOP + "\n"
    "    satisfied = field_unique or found\n"
    "    if not satisfied:\n"
    "        if default_regime:\n"
    "            return HARD_ERROR\n"
    "        return WARNING\n"
    "    return NO_DIAGNOSTIC"
)

# admiss-reads: an admissibility positive control. The precondition is the three
# half-permissions Acc(list_pred(c_*),1/2) plus the length tie. This control keeps
# the gold impl VERBATIM but first asserts, under those half-permissions, that the
# reads a normal F2P-shaped input needs are admitted — the lengths are readable and
# equal, and (when the list is non-empty) the first records of each sequence are
# readable. No write, so no extra permission demand. If the precondition could not
# admit a legitimate constraint-list input, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (possibly empty) equal-length constraint list is\n"
    "    # in-domain; the half-permissions admit reading the lengths and elements.\n"
    "    Assert(len(c_span) >= 0)\n"
    "    Assert(len(c_span) == len(c_single) and len(c_single) == len(c_total))\n"
    "    if len(c_span) > 0:\n"
    "        Assert(c_span[0] == c_span[0])      # read admitted under Acc(...,1/2)\n"
    "        Assert(c_single[0] == c_single[0])\n"
    "        Assert(c_total[0] == c_total[0])\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS (MANDATORY — c_span/c_single/c_total are Acc(...,1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input: c_span[0] = c_span[0]. A no-op store, but a STORE — it demands
# FULL write permission on c_span, which the caller granted only at 1/2. The
# verifier must reject for insufficient permission. (A real impl that mutated the
# shared constraint records would corrupt the model's _meta; the spec must forbid
# ANY write.) Guarded by len>0 so the store is reachable on a normal input.
_FRAME_MUT = (
    _IMPL.rsplit("    if satisfied:", 1)[0]
    + "    if len(c_span) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        c_span[0] = c_span[0]\n"
    "    if satisfied:"
    + _IMPL.rsplit("    if satisfied:", 1)[1]
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only the function impl region.
# ---------------------------------------------------------------------------

# weak-prepatch: the EXACT pre-patch skeleton (model_prepatch.py) — the obligation
# is discharged ONLY by the field's own direct uniqueness; the declared constraints
# are never consulted. PARTIAL-DOMAIN: correct on every input where field_unique is
# True (no constraint needed) and on every input where no constraint covers (a
# diagnostic is due either way); WRONG exactly on the F2P discriminator
# field_unique==False AND a covering unconditional single-field constraint exists.
# There the rival returns a diagnostic but Q5 requires NO_DIAGNOSTIC.
_WEAK_PREPATCH = """\
    satisfied = field_unique
    if satisfied:
        return NO_DIAGNOSTIC
    if default_regime:
        return HARD_ERROR
    return WARNING"""

# weak-swap-regime: keeps the gold loop and decision VERBATIM (so the verifier KNOWS
# satisfied == field_unique or any_covers(...)), but INVERTS the severity — returns
# WARNING under the default regime and HARD_ERROR otherwise. PARTIAL-DOMAIN on the
# regime sub-domain: correct whenever no diagnostic is due (Q5 still holds), but on
# every not-satisfied input the code is the wrong severity. Q6 pins
# Result()==(HARD_ERROR if default_regime else WARNING); this rival contradicts it.
_WEAK_SWAP_REGIME = (
    _IMPL.rsplit("    if default_regime:\n        return HARD_ERROR\n    return WARNING", 1)[0]
    + "    if default_regime:\n        return WARNING\n    return HARD_ERROR"
)

# weak-always-error: keeps the gold loop VERBATIM (so satisfied is the true decision)
# but ALWAYS returns the diagnostic, ignoring `satisfied`. Never suppresses. WRONG on
# Q5 on every suppress input (field_unique or any_covers => NO_DIAGNOSTIC required,
# but it returns a code). The pre-patch-with-no-suppression baseline: a real check
# that emitted auth.E003/W004 unconditionally would fail every "must be []" F2P/P2P.
_WEAK_ALWAYS_ERR = (
    _IMPL.rsplit("    if satisfied:\n        return NO_DIAGNOSTIC\n", 1)[0]
    + "    if default_regime:\n        return HARD_ERROR\n    return WARNING"
)

# weak-always-suppress: the dual — ALWAYS return NO_DIAGNOSTIC. Never emits. WRONG on
# Q6 on every not-satisfied input (a diagnostic is required but it returns 0). A real
# check that simply removed the guard body would never report a non-unique
# USERNAME_FIELD, failing the P2P test_username_non_unique / test_username_partially_
# unique (both of which assert a diagnostic IS produced). Cheap supporting near-miss
# with a genuine refinement; bound to a typed-free constant (no `# type:` pitfall).
_WEAK_ALWAYS_SUPPRESS = """\
    return NO_DIAGNOSTIC"""


SPEC_TESTS = [
    {
        "id": "pos-eager-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_EAGER),
        "rationale": (
            "structurally-different but CORRECT impl: the constraint search runs "
            "UNCONDITIONALLY (the gold's `if not satisfied:` guard is factored out) "
            "and the outcome is computed by a reshaped nested if/else, while EVERY "
            "gold proof obligation is kept verbatim (same backward loop, same "
            "found==any_covers(drop(i)) invariant, same per-step drop(i-1) framing "
            "asserts, same final drop(0)==whole asserts). The decision value is "
            "identical: satisfied == field_unique or any_covers(full). If it FAILS "
            "=> SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (three Acc(list_pred(c_*),1/2) half-permissions + the "
            "length tie) must admit a normal F2P-shaped constraint list: the lengths "
            "are readable and equal and the first records are readable under the "
            "half-permissions. The gold impl is otherwise verbatim (only reads/asserts "
            "added inside the impl region, no write). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch only READS the model's declared constraints "
            "(`for constraint in cls._meta.total_unique_constraints`); it NEVER "
            "mutates a constraint record or _meta. A faithful real patch that wrote "
            "back into the shared constraint list (e.g. normalising "
            "`constraint.fields` in place) would corrupt the model's metadata for "
            "every other system check and diverge from the gold's read-only scan — "
            "it would not be the gold patch and would not faithfully resolve. The "
            "store here is a no-op only by coincidence; the point is the spec must "
            "forbid ANY write to the inputs."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: c_span is granted at Acc(...,1/2) "
            "(P1); the store c_span[0]=c_span[0] demands FULL write permission, which "
            "is not available, so the verifier rejects for INSUFFICIENT PERMISSION. "
            "The gold decision/return body is kept verbatim so the rejection is "
            "attributable solely to the write. If it VERIFIES => the read-only frame "
            "is hollow (frame-mutation, the #1 weakness class; a byte-fuzzer never "
            "thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the original "
            "`if not cls._meta.get_field(cls.USERNAME_FIELD).unique:` guard with NO "
            "`any(constraint.fields == (USERNAME_FIELD,) ...)` conjunct — the declared "
            "unique constraints are never consulted. Its faithful real patch is the "
            "UNCHANGED repo, which still emits auth.E003 for a model whose username is "
            "covered only by an unconditional UniqueConstraint(fields=['username']) — "
            "exactly the F2P test_username_unique_with_model_constraint, which now "
            "asserts run_checks() == []. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5 (Implies(field_unique or any_covers(...), "
            "Result()==NO_DIAGNOSTIC)): on the discriminating sub-domain field_unique"
            "==False AND a covering unconditional single-field constraint exists "
            "(any_covers True), the rival returns HARD_ERROR/WARNING but Q5 requires "
            "NO_DIAGNOSTIC. This is the precise change the spec senses (G-DIFF). If it "
            "VERIFIES => SPEC-TOO-WEAK (the added constraint search is not enforced)."
        ),
    },
    {
        "id": "weak-swap-regime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP_REGIME),
        "refinement": (
            "a real patch that swapped the two branches of the severity test "
            "(`if settings.AUTHENTICATION_BACKENDS == ['...ModelBackend']:` "
            "appending auth.W004 instead of auth.E003, and vice versa) is correct on "
            "every input where no diagnostic is due but emits the WRONG diagnostic id "
            "on every non-unique USERNAME_FIELD. It fails the P2P test_username_non_"
            "unique (asserts auth.E003 under the default backend) and the warning arm "
            "of test_username_partially_unique (asserts auth.W004 under a custom "
            "backend). A genuine PARTIAL-DOMAIN break on the regime sub-domain; does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q6 (Implies(not(...), Result()==(HARD_ERROR if "
            "default_regime else WARNING))): the gold loop is kept verbatim so the "
            "verifier knows satisfied==field_unique or any_covers(...); on every "
            "not-satisfied input the rival returns the inverted severity (WARNING "
            "under default_regime, HARD_ERROR otherwise), contradicting the pinned "
            "code. If it VERIFIES => SPEC-TOO-WEAK on the severity sub-domain."
        ),
    },
    {
        "id": "weak-always-error",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_ERR),
        "refinement": (
            "always emitting the diagnostic (ignoring whether the obligation is "
            "discharged) is what a real patch that kept the Error/Warning append "
            "OUTSIDE the guard would do. It reports auth.E003/W004 even for a "
            "genuinely-unique username, failing every F2P/P2P that asserts "
            "run_checks() == [] (test_username_unique_with_model_constraint, and the "
            "implicit unique-field-OK cases). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5 (Implies(field_unique or any_covers(...), "
            "Result()==NO_DIAGNOSTIC)): the gold loop is kept verbatim so the "
            "verifier knows the true `satisfied`; on a suppress input the rival "
            "returns a diagnostic code while Q5 requires NO_DIAGNOSTIC. If it "
            "VERIFIES => SPEC-TOO-WEAK (the suppression is unpinned). Supporting "
            "near-miss with a real refinement."
        ),
    },
    {
        "id": "weak-always-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_SUPPRESS),
        "refinement": (
            "always returning NO_DIAGNOSTIC is what a real patch that deleted the "
            "Error/Warning append entirely would do — it never reports a non-unique "
            "USERNAME_FIELD. It fails the P2P test_username_non_unique and "
            "test_username_partially_unique (both assert a diagnostic IS produced for "
            "a username that is neither directly unique nor covered by an "
            "unconditional single-field constraint). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q6 (Implies(not(field_unique or any_covers(...)), "
            "Result()==(HARD_ERROR if default_regime else WARNING))): on a "
            "not-satisfied input the rival returns NO_DIAGNOSTIC while Q6 requires a "
            "diagnostic code. `return NO_DIAGNOSTIC` is a typed-free int constant so "
            "there is no `# type:` pitfall. If it VERIFIES => SPEC-TOO-WEAK. Cheap "
            "supporting near-miss with a genuine refinement."
        ),
    },
]


# No @ContractOnly axioms (meta.axioms == []) and no A-reference deep model
# (deep_model_references == []): the existential constraint search the patch
# introduces is modeled DEEPLY (the @Pure any_covers/covers + the verified backward
# loop), fully expressible from the inputs, NOT hidden behind an axiom. There is no
# axiom Ensures to over-approximate and no callee to execute. axiom_check.py / G-AX
# already validates the deep predicate against real Django UniqueConstraint tuple-
# equality + total_unique_constraints(condition is None) semantics on 12 boundary +
# 4000 fuzz constraint lists. Nothing in this bundle's proof rests on an axiom, so
# the axiom lane is vacuous.
AXIOM_TESTS = []
