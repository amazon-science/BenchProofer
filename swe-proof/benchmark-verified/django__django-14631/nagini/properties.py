"""PBT manifest for django__django-14631.

NOT a Nagini module: an adversarial falsification battery for the frozen spec
of `clean_bound_initial_field`. The runner (`swebench_nagini.pbt`) parses
SPEC_TESTS (full model.py variants — same frozen spec, impl region swapped —
checked by Nagini verify + same_spec) and AXIOM_TESTS (real-callee probes in
Docker). Each variant is built by `_swap` editing ONLY text strictly between
`# impl-start` and `# impl-end`, so the frozen spec (axioms/pure/pre/post) is
never touched and same_spec is guaranteed.

Defended surface (read from model.py + refinement.md + meta.json):
  * `clean_bound_initial_field(fs: FieldState) -> int`.
  * INPUT IS READ-ONLY: `Requires/Ensures(Acc(fs.first_eval, 1/2))` — half
    permission only, returned unchanged. Any write to fs.first_eval needs full
    permission and rejects for INSUFFICIENT PERMISSION. (frame-mutation lane:
    MANDATORY here.)
  * LOAD-BEARING permission pin (no re-evaluation of the source):
    the precondition grants NO permission at all to fs.fresh_eval.  # (P4)
    Evaluating the initial source is STATEFUL in the real repo (a callable
    source advances its own state per call), so ANY extra evaluation — even a
    dead one whose result is discarded — shifts which value the single cached
    evaluation captures and breaks cleaned == bf.initial on the F2P stateful
    FakeTime source. An impl that so much as READS fs.fresh_eval (models a
    second evaluation, dead or live) must reject for INSUFFICIENT PERMISSION.
    This pin was added after the G-EQ audit exhibited atk_8 (dead read of
    fresh_eval, then the correct value) verifying while its faithful patch
    (a dead get_initial_for_field call before value = bf.initial) failed the
    hidden tests (the dead call advances FakeTime, so bf.initial caches the
    LATER evaluation).
  * LOAD-BEARING postcondition (two equivalent pins):
        Ensures(Result() == bound_initial(fs))            # (P1)
        Ensures(Result() == normalise(fs.first_eval))     # (P2)
    where bound_initial(fs) == normalise(fs.first_eval) == (first_eval//1e6)*1e6.
  * LOAD-BEARING termination pin (total correctness):
        Requires(MustTerminate(2))                        # (P3)
    Cleaning a field is a bounded step of form validation; a diverging impl
    (e.g. `while True:` before returning the correct value) satisfies P1/P2
    only vacuously and its faithful real patch hangs form.is_valid() and the
    F2P test (harness timeout, NOT resolved) — the exact break the G-EQ audit
    demonstrated (atk_4/atk_6/atk_7) before P3 was added.
  * The discriminating content vs. the pre-patch bug: the cleaned value must be
    the NORMALISED FIRST evaluation, never the FRESH re-evaluation fs.fresh_eval
    (which the function now has no permission even to read) and never an
    un-normalised first evaluation.
  * No @ContractOnly axioms (meta.axioms == []); the bound_initial/normalise
    deep model is an A-reference validated by axiom_check.py / G-AX, not a
    consumed axiom. AXIOM_TESTS is therefore [] (see 'assessment' / rationale).
"""
from pathlib import Path

INSTANCE = "django__django-14631"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything strictly between the markers).
# Every variant replaces THIS block — and only this block — so the swap edits
# nothing outside `# impl-start`/`# impl-end`.
_GOLD_IMPL = """    # Read the value through the field's bound initial (single cached,
    # normalised evaluation), then clean it. Cleaning a date/time value is the
    # identity on the value it is given.
    value = bound_initial(fs)
    cleaned = value
    return cleaned"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


# --------------------------------------------------------------------------- #
# 1. FRAME-MUTATION (read-only input) — MANDATORY.                            #
#    fs.first_eval is Acc(..., 1/2): half permission, so the function may     #
#    READ but never WRITE it. This rival overwrites first_eval                 #
#    so that normalise(fs.first_eval) trivially equals the returned value      #
#    (a vacuous way to "satisfy" P2). It keeps a postcondition-satisfying      #
#    return so the rejection is attributable ONLY to the write, which needs    #
#    full permission the caller never granted -> INSUFFICIENT PERMISSION.      #
# --------------------------------------------------------------------------- #
_FRAME_MUTATE = """    # ATTACK (frame-mutation): overwrite the read-only input fs.first_eval to
    # make the value-abstraction agree vacuously, then return the matching
    # value. fs has only Acc(fs.first_eval, 1/2) here, so this assignment lacks
    # the permission to write -> must reject for insufficient permission.
    fs.first_eval = 0
    cleaned = normalise(fs.first_eval)
    return cleaned"""


# --------------------------------------------------------------------------- #
# 2. PARTIAL-DOMAIN — un-normalised first evaluation.                          #
#    Returns fs.first_eval WITHOUT normalising. Correct iff first_eval already #
#    has no sub-second component (first_eval % 1_000_000 == 0); diverges on    #
#    every microsecond-bearing value — precisely the F2P case (initial         #
#    datetime(...,46) carrying microseconds=123456, which BoundField.initial   #
#    strips). Fails P2: Result() == normalise(fs.first_eval).                  #
# --------------------------------------------------------------------------- #
_UNNORMALISED = """    # ATTACK (partial-domain): use the FIRST evaluation but skip the sub-second
    # normalisation. Agrees on whole-second values, diverges whenever the
    # source carries microseconds (the F2P datetime with microseconds=123456).
    value = fs.first_eval
    cleaned = value
    return cleaned"""


# --------------------------------------------------------------------------- #
# 3. PARTIAL-DOMAIN / pre-patch bug — the fresh re-evaluation.                 #
#    This IS the pre-patch path (model_prepatch.py): the cleaned value is a    #
#    fresh, independent re-evaluation of the initial source (fs.fresh_eval)    #
#    instead of the cached, normalised bound initial. Fails P1/P2 whenever     #
#    fs.fresh_eval != normalise(fs.first_eval) — the F2P stateful callable     #
#    (FakeTime advancing the second AND retaining microseconds).               #
# --------------------------------------------------------------------------- #
_FRESH_EVAL = """    # ATTACK (pre-patch bug): clean a FRESH re-evaluation of the initial source
    # (fs.fresh_eval), not the field's cached/normalised bound initial. This is
    # exactly the bug the gold patch removes.
    value = fs.fresh_eval
    cleaned = value
    return cleaned"""


# --------------------------------------------------------------------------- #
# 3b. DEAD RE-EVALUATION — the audit's atk_8 (verified-but-not-resolved).      #
#     Reads the fresh re-evaluation, DISCARDS it, then returns the correct     #
#     bound initial. Under the old spec (which granted Acc(fs.fresh_eval,1/2)) #
#     this VERIFIED, yet its faithful patch — a dead get_initial_for_field     #
#     call before value = bf.initial — fails the hidden tests: the F2P source  #
#     is stateful (FakeTime), so the dead call advances it and bf.initial      #
#     caches the LATER evaluation. (P4) removes all permission to fresh_eval,  #
#     so even this dead read must now reject (INSUFFICIENT PERMISSION).        #
# --------------------------------------------------------------------------- #
_DEAD_FRESH_THEN_CORRECT = """    # ATTACK (dead re-evaluation, audit atk_8): evaluate the source afresh,
    # throw the value away, then return the correct bound initial. The value
    # postconditions hold, but the extra (dead) evaluation advances a stateful
    # source in the real repo, so the faithful patch does NOT resolve. Must be
    # rejected by the no-permission-to-fresh_eval pin (P4).
    value = fs.fresh_eval
    value = bound_initial(fs)
    cleaned = value
    return cleaned"""


# --------------------------------------------------------------------------- #
# 4. PARTIAL-DOMAIN — "max" mixes fresh and normalised first.                  #
#    Returns the larger of the normalised first eval and the fresh eval. For a #
#    stateful source the fresh evaluation is a LATER second (fresh > first), so #
#    this returns fresh_eval on the F2P input -> wrong. Agrees only on the      #
#    sub-domain fresh_eval <= normalise(first_eval). A genuinely distinct       #
#    wrong impl, not a copy of #3.                                             #
# --------------------------------------------------------------------------- #
_MAX_MIX = """    # ATTACK (partial-domain): pick the larger of the bound initial and the
    # fresh re-evaluation. Correct only when the fresh eval does not exceed the
    # normalised first eval; wrong for the stateful F2P source (fresh is later).
    base = bound_initial(fs)
    if fs.fresh_eval > base:
        cleaned = fs.fresh_eval
    else:
        cleaned = base
    return cleaned"""


# --------------------------------------------------------------------------- #
# 4b. NON-TERMINATION — the exact break the G-EQ audit found while the spec    #
#     was partial-correctness only. Computes the CORRECT value (bound_initial) #
#     but spins in an infinite loop before returning it. Under partial         #
#     correctness this VERIFIED (P1/P2 hold on the never-reached exit) and its #
#     faithful real patch (`while True: pass` inside the disabled branch of    #
#     _clean_fields) hung the F2P test to the 300s harness timeout — verified  #
#     but NOT resolved (audit atk_4/atk_6/atk_7). With (P3)                    #
#     Requires(MustTerminate(2)) the loop has no decreasing MustTerminate      #
#     measure, so the caller's termination obligation leaks -> REJECTED.       #
# --------------------------------------------------------------------------- #
_DIVERGE = """    # ATTACK (non-termination): compute the correct bound initial, then spin
    # forever before returning it. Partial correctness would accept this
    # (the postconditions hold vacuously on the never-exiting path); the
    # MustTerminate obligation must reject it.
    b = bound_initial(fs)
    while b == b:
        Invariant(Acc(fs.first_eval, 1 / 4) and fs.first_eval >= 0)
        Invariant(b == bound_initial(fs))
    return b"""


# --------------------------------------------------------------------------- #
# 5. POSITIVE CONTROL (soundness) — structurally different, still CORRECT.     #
#    Inlines the normalisation arithmetic directly (the unfolded body of       #
#    bound_initial/normalise) instead of calling the bound_initial helper, and #
#    branches on the microsecond component. Both P1 and P2 reduce to           #
#    (fs.first_eval // 1_000_000) * 1_000_000, which this computes either way,  #
#    so it MUST verify. No induction / fold lemma is involved (pure integer    #
#    arithmetic the verifier discharges directly).                            #
# --------------------------------------------------------------------------- #
_POS_INLINE = """    # POSITIVE CONTROL: a different shape that still returns the normalised
    # first evaluation. Branch on whether the value already has no sub-second
    # component; both arms equal (fs.first_eval // 1000000) * 1000000.
    whole = (fs.first_eval // 1000000) * 1000000
    if fs.first_eval == whole:
        cleaned = fs.first_eval
    else:
        cleaned = whole
    return cleaned"""


# --------------------------------------------------------------------------- #
# 6. POSITIVE CONTROL (cheapest honest impl).                                  #
#    Calls normalise(fs.first_eval) directly (the grounded oracle is a         #
#    function of the input — there is no answer-key to echo, see 'assessment'),#
#    using a single local. Must verify; if it cannot, the spec is TOO-STRONG.  #
# --------------------------------------------------------------------------- #
_POS_DIRECT = """    # POSITIVE CONTROL (cheapest honest impl): return normalise(fs.first_eval)
    # directly via a single local. The oracle is grounded in the input, so this
    # is the correct value, not a vacuous echo.
    cleaned = normalise(fs.first_eval)
    return cleaned"""


# --------------------------------------------------------------------------- #
# 7. ADMISSIBILITY — the precondition admits a normal F2P-shaped input.        #
#    A correct impl that ALSO asserts the in-domain facts the Requires demands #
#    of an F2P-shaped FieldState (both evaluations non-negative; first_eval     #
#    carries microseconds, e.g. encodes datetime(...,46) + 123456 us). If the   #
#    precondition were too strong these reads/asserts would fail; it must       #
#    verify. (We assert on the function's own in-domain inputs rather than      #
#    constructing a fresh FieldState, to avoid a constructor-permission proof   #
#    obligation unrelated to the precondition under test.)                     #
# --------------------------------------------------------------------------- #
_ADMISS = """    # ADMISSIBILITY: the precondition must accept a normal F2P-shaped input.
    # Read the in-domain facts the Requires guarantees, then return the correct
    # cleaned value. These reads/asserts hold for any legitimate input.
    # (fs.fresh_eval is NOT read: the spec deliberately grants no permission
    # to it — cleaning may not re-evaluate the source.)
    Assert(fs.first_eval >= 0)
    cleaned = bound_initial(fs)
    Assert(cleaned == normalise(fs.first_eval))
    return cleaned"""


SPEC_TESTS = [
    {
        "id": "frame-mutate-first-eval",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUTATE),
        "refinement": (
            "The faithful real patch of this rival WRITES to the field's initial "
            "source / its cached BoundField.initial inside _clean_fields, mutating "
            "the form's read-only initial state to force agreement. That is not "
            "the gold edit (gold only READS bf.initial) and would corrupt the "
            "form's bound state, so it would NOT resolve the F2P tests (which read "
            "form[name].initial after cleaning and require it unchanged). In the "
            "model the input is Acc(fs.first_eval, 1/2): the write has no "
            "permission and must reject."
        ),
        "rationale": (
            "Rejection comes from the permission system: fs.first_eval is held at "
            "1/2 (read-only) by the precondition and re-promised at 1/2 by the "
            "postcondition; assigning to it requires full permission the caller "
            "never granted -> INSUFFICIENT PERMISSION, not a value mismatch."
        ),
    },
    {
        "id": "partial-domain-unnormalised-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _UNNORMALISED),
        "refinement": (
            "Its faithful real patch sets the disabled value to the FIRST "
            "evaluation WITHOUT the BoundField.initial microsecond strip (e.g. "
            "value = self.get_initial_for_field(field, name) cached but not "
            "normalised). On the F2P input the initial datetime carries "
            "microseconds=123456, so the cleaned value would be "
            "datetime(...,46,123456) != datetime(...,46); the F2P assertion "
            "(microseconds stripped) FAILS -> does not resolve."
        ),
        "rationale": (
            "Fails postcondition P2 Ensures(Result() == normalise(fs.first_eval)): "
            "fs.first_eval != normalise(fs.first_eval) whenever first_eval % 1e6 != 0."
        ),
    },
    {
        "id": "pre-patch-fresh-reeval",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRESH_EVAL),
        "refinement": (
            "This is the pre-patch code itself (model_prepatch.py): the disabled "
            "value comes from a fresh get_initial_for_field re-evaluation, not "
            "bf.initial. The F2P stateful FakeTime callable advances the second "
            "AND keeps microseconds on each call, so the fresh evaluation "
            "(datetime(...,47,123456)) disagrees with the cached normalised bound "
            "initial (datetime(...,46)); the F2P assertion that "
            "form._clean_fields value == form[name].initial FAILS -> does not "
            "resolve (this is exactly the bug the ticket fixes)."
        ),
        "rationale": (
            "Rejected twice over: reading fs.fresh_eval needs a permission the "
            "precondition deliberately does not grant (P4, INSUFFICIENT "
            "PERMISSION — cleaning may not re-evaluate the source), and even "
            "granted the read the value fails P1/P2 (fs.fresh_eval is "
            "unconstrained relative to normalise(fs.first_eval)). (Mirrors "
            "G-DIFF / model_prepatch.)"
        ),
    },
    {
        "id": "dead-fresh-reeval-then-correct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DEAD_FRESH_THEN_CORRECT),
        "refinement": (
            "This is the audit's atk_8: read the fresh re-evaluation into a "
            "local, DISCARD it, then return the correct bound initial. Its "
            "faithful real patch inserts a dead "
            "'value = self.get_initial_for_field(field, name)' line before the "
            "gold 'value = bf.initial' in _clean_fields. The dead call is NOT "
            "inert in the real repo: the F2P initial source is a stateful "
            "FakeTime callable that advances one second per call, so the dead "
            "evaluation consumes ...:46 and bf.initial (first read AFTER it) "
            "caches ...:47 — the hidden tests assert cleaned == "
            "datetime(...,46) and FAIL. Verified-but-not-resolved unless the "
            "spec rejects the extra evaluation."
        ),
        "rationale": (
            "REJECTED by (P4): the precondition grants NO permission to "
            "fs.fresh_eval, so even a dead read of it fails verification for "
            "INSUFFICIENT PERMISSION. If it VERIFIES => SPEC-TOO-WEAK (the "
            "no-re-evaluation obligation is unpinned — the exact G-EQ break)."
        ),
    },
    {
        "id": "partial-domain-max-mix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _MAX_MIX),
        "refinement": (
            "Its faithful real patch would return max(bf.initial, fresh "
            "re-evaluation) — correct only when the fresh re-evaluation is not a "
            "later value. For the F2P stateful source the fresh evaluation is a "
            "strictly later second, so the cleaned value would be the fresh "
            "(wrong) datetime and != form[name].initial -> the F2P equality "
            "assertion FAILS, does not resolve."
        ),
        "rationale": (
            "Rejected twice over: the comparison READS fs.fresh_eval, which "
            "(P4) grants no permission for (INSUFFICIENT PERMISSION — cleaning "
            "may not re-evaluate the source); and even granted the read, it "
            "fails P1/P2 on the sub-domain fs.fresh_eval > "
            "normalise(fs.first_eval). A genuinely distinct wrong impl from "
            "the plain fresh-eval rival."
        ),
    },
    {
        "id": "weak-diverge-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DIVERGE),
        "refinement": (
            "The faithful real patch puts an infinite loop (`while True: pass`) "
            "inside the disabled-field branch of _clean_fields before assigning "
            "value = bf.initial. Empirically confirmed by the G-EQ audit "
            "(atk_4/atk_6/atk_7): the patch applies cleanly and the F2P test run "
            "times out after 300s (EvaluationError: Test timed out) — does NOT "
            "resolve, while the partial-correctness spec still verified it."
        ),
        "rationale": (
            "REJECTED by (P3) Requires(MustTerminate(2)): the loop has no "
            "decreasing MustTerminate measure, so the caller's termination "
            "obligation cannot be discharged (obligation leak) and verification "
            "fails. Under the previous partial-correctness spec this VERIFIED "
            "(P1/P2 held vacuously on the never-exiting path). If it VERIFIES => "
            "SPEC-TOO-WEAK (the termination obligation is unpinned)."
        ),
    },
    {
        "id": "pos-control-inline-normalise",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_INLINE),
        "rationale": (
            "Structurally different (inlined normalisation arithmetic + a "
            "microsecond branch) but behaviourally identical: both arms equal "
            "(fs.first_eval // 1000000) * 1000000 == normalise(fs.first_eval) == "
            "bound_initial(fs), satisfying P1 and P2. Pure integer arithmetic, no "
            "induction/fold lemma; must verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_DIRECT),
        "rationale": (
            "Cheapest honest correct impl: return normalise(fs.first_eval). The "
            "postcondition oracle is GROUNDED in the input (a fully-unfolded @Pure "
            "function of fs.first_eval), so this is the correct value, not a "
            "vacuous echo. Must verify."
        ),
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": (
            "The precondition (Acc 1/2 on first_eval only, first_eval >= 0; "
            "deliberately no permission to fresh_eval) must admit a "
            "normal F2P-shaped FieldState. A correct impl that also Asserts the "
            "in-domain facts the Requires guarantees verifies; if the precondition "
            "were too strong these reads/asserts would fail -> PRECOND-TOO-STRONG."
        ),
    },
]


# No @ContractOnly axioms (meta.json axioms == []). bound_initial/normalise is
# an A-reference deep model already validated end-to-end against the real Django
# form machinery by axiom_check.py / G-AX (R1: BoundField.initial == normalise
# of the single first eval; R2: disabled cleaned value == bf.initial; R3:
# pre-patch fresh re-eval disagrees; + 50008 normalise fuzz observations). There
# is no consumed-axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
