# properties.py — PBT falsification battery for django__django-13346. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + mapping.md + gold patch):
#   process_membership_rhs(num_values: int) -> List[int]
#   Models KeyTransformIn.process_rhs's per-slot wrapping of the membership
#   comparison string on a non-native-JSON backend (the SQLite/MySQL branch the
#   F2P test_key_in exercises). The base In.process_rhs placeholder is
#   '(' + ', '.join(['%s']*n) + ')'; the fix substitutes rhs % (("JSON_EXTRACT(%s,
#   '$')",) * n), wrapping every slot. The model carries the inner per-slot
#   expansion as List[int] of code points; spec is over PSeq[int] via ToSeq.
#
#   Precondition (ONE input, BY VALUE — no heap, no permission):
#     (P1) Requires(num_values >= 1)
#   Postcondition (two clauses):
#     (Q1) Ensures(Acc(list_pred(Result())))             # full perm, fresh result
#     (Q2) Ensures(ToSeq(Result()) == slots_sql(num_values))  # LOAD-BEARING
#
#   The LOAD-BEARING clause is Q2. slots_sql(n) is a @Pure front-recursive fold
#   spelled out from CONSTANT code-point literals: n copies of wrapped_slot()
#   (JSON_EXTRACT(%s, '$') = PSeq(74,...,41)) joined by sep() (', ' = PSeq(44,32)).
#
# FRAME-MUTATION lane: N/A (has_readonly_input == False). The sole input
#   num_values is a plain `int` passed BY VALUE — there is no Acc(x,1/2) read-only
#   heap input, no list/object reference whose half-permission a rival could
#   illegally write. Writing to the local `num_values` is harmless (a value copy)
#   and would never be a permission violation, so the canonical frame-mutation
#   probe has no target here. See 'assessment'. (No frame-mutation case is
#   included precisely because the directive's precondition — a read-only heap
#   input — does not hold for this instance.)
#
# UNGROUNDED-ORACLE-ECHO lane: N/A as a *wrong* echo. Q2 pins Result to
#   slots_sql(num_values), which is GROUNDED entirely in the input num_values and
#   in fixed code-point constants: it is a fully-unfolded @Pure fold, NOT an opaque
#   answer-key / exact-marker oracle. There is no value an echo could carry that
#   satisfies Q2 yet is behaviourally wrong — the unique satisfier IS the wrapped
#   per-slot expansion. So the honest grounded-oracle control is "produce the
#   wrapped expansion the right way" (the positive controls below). See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. process_membership_rhs is a pure value-returning
#   string builder with no raise / return-vs-fallthrough difference and no
#   side-effect invisible to the value abstraction (the whole output string IS the
#   abstraction). The gold change touches only `rhs` (the placeholder string);
#   rhs_params passes through unchanged and is not modeled (refinement.md A4).
#
# UNIQUENESS / PARTIAL-DOMAIN lane (the real attacks): Q2 must reject any rival
#   that leaves ANY slot unwrapped. The two partial-domain rivals split the F2P
#   input domain exactly on the boundary the issue is about — single-value vs
#   multi-value membership.
#
# AXIOM lane: meta.axioms == []. There is ONE deep_model_reference (slots_sql, an
#   A-reference for the per-slot wrapping) but the proof consumes NO @ContractOnly
#   axiom — slots_sql is spelled out in model.py's pure region and validated ==
#   the real %-substitution out-of-band by axiom_check.py (G-AX). Nothing in this
#   bundle's proof rests on a @ContractOnly axiom, so AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "django__django-13346"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim — everything strictly BETWEEN
# the function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants
# region. Every spec variant _swap()s ONLY this block, so the edit never touches
# the spec (axioms/pure/pre-/post-conditions regions + the function signature).
# same_spec is computed over the spec_view, which elides every impl region (and
# nested invariants), so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        # `result` already holds the expansion of the trailing `num_values - i`
        # slots (built back-to-front so the front-recursive slots_sql unfolds
        # one slot per step).
        Invariant(ToSeq(result) == slots_sql(num_values - i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            # Last slot: no trailing separator.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            # Earlier slot: wrapped slot, then separator, then the rest.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-reorder: structurally DIFFERENT but behaviourally identical. Keeps the SAME
# back-to-front loop direction and the SAME front-recursive invariant
# ToSeq(result) == slots_sql(num_values - i) the gold proof rests on (so it does
# NOT need an f(a+b) fold lemma — pitfall #3). The executable shape differs: the
# two branches are REORDERED (the earlier-slot case is tested first via
# `if i != num_values`) and each literal is bound to a typed local before use
# (`slot` / `slot_sep`) instead of being written inline. No gold framing
# obligation is dropped (pitfall #2). If this fails to verify => SPEC-TOO-STRONG.
_POS_REORDER = """\
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        Invariant(ToSeq(result) == slots_sql(num_values - i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i != num_values:
            # Earlier slot: wrapped slot, then separator, then the rest.
            slot_sep = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                        40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32]  # type: List[int]
            result = slot_sep + result
        else:
            # Last slot: no trailing separator.
            slot = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                    40, 37, 115, 44, 32, 39, 36, 39, 41]  # type: List[int]
            result = slot
        i = i - 1
    return result"""

# admiss-1: an admissibility positive control. The precondition Requires(num_values
# >= 1) must ADMIT the F2P-shaped single-element membership input (key__in=[v],
# num_values == 1 — the exact case the issue is about) and the multi-value case.
# This control asserts the precondition holds and exercises the in-domain count
# before running the gold body verbatim. If the precondition rejected a normal
# in-domain count this would fail => PRECOND-TOO-STRONG. The asserts are pure
# facts derivable from the Requires; no write, no extra permission demand.
_ADMISS = """\
    # Admissibility: a single-value membership (num_values == 1) and any larger
    # count are in-domain; the precondition num_values >= 1 admits them.
    Assert(num_values >= 1)
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        Invariant(ToSeq(result) == slots_sql(num_values - i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals — same spec, WRONG impl — must REJECT.
# Each fails Q2 (ToSeq(Result()) == slots_sql(num_values)); a verify here would be
# SPEC-TOO-WEAK. Each carries the refinement argument that its faithful real patch
# would NOT resolve the F2P.
# ---------------------------------------------------------------------------

# weak-bare: the pre-fix baseline (== model_prepatch.py's impl). EVERY slot is left
# as the bare bind placeholder %s ([37,115]) — the In.process_rhs string with NO
# wrapping. Fails Q2 for every num_values >= 1. This is exactly the bug: a real
# patch that omits `rhs = rhs % func` (no KeyTransformIn override at all) leaves
# key__in producing bare `%s` against the raw stored representation, so test_key_in
# selects the wrong/empty set and does NOT resolve. The invariant is relaxed to the
# trivially-true len(result) >= 0 so the variant TYPE-CHECKS and is rejected by Q2
# at the postcondition (a genuine spec rejection), not by a proof-trigger gap.
_WEAK_BARE = """\
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        Invariant(len(result) >= 0)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            # Last slot: bare placeholder, no trailing separator (the bug).
            result = [37, 115]
        else:
            # Earlier slot: bare placeholder, then separator, then the rest.
            result = [37, 115, 44, 32] + result
        i = i - 1
    return result"""

# partial-last-bare: correct (wrapped) on every slot EXCEPT the trailing one
# (i == num_values), which is left as the bare placeholder %s. This diverges on
# the single-value sub-domain: for num_values == 1 the only slot is the trailing
# one, so the output is just `%s` — the EXACT single-element bug the issue reports
# (key__in=[v] must match key=v). A faithful real patch that wrapped all-but-the-
# last value's slot would still emit bare `%s` for the single-value membership and
# would NOT resolve test_key_in (whose discriminating assertion is the single
# stored-key __in test). Fails Q2 (last slot != wrapped_slot()).
_PARTIAL_LAST_BARE = """\
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        Invariant(len(result) >= 0)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            # Trailing slot left BARE (the bug on the single-value sub-domain).
            result = [37, 115]
        else:
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result"""

# partial-multi-bare: correct on the SINGLE-value sub-domain (num_values == 1 emits
# the fully-wrapped single slot) but on the MULTI-value sub-domain (num_values >= 2)
# every NON-trailing slot is left bare (%s) — only the trailing slot is wrapped.
# This is the complementary domain split to partial-last-bare: it passes the
# single-element case yet diverges for key__in with >= 2 values. A faithful real
# patch wrapping only the last value's slot would emit wrong SQL for multi-value
# membership and would NOT resolve test_key_in (which exercises the lookup over a
# list of values). Fails Q2 for num_values >= 2 (a non-trailing slot != wrapped).
_PARTIAL_MULTI_BARE = """\
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        Invariant(len(result) >= 0)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            # Trailing slot wrapped (correct for the single-value sub-domain).
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            # Non-trailing slot left BARE (the bug on the multi-value sub-domain).
            result = [37, 115, 44, 32] + result
        i = i - 1
    return result"""

# weak-wrong-wrapper: a SUPPORTING near-miss with a real refinement. Every slot is
# the WRONG backend wrapper — the MariaDB form JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))
# instead of the SQLite/MySQL form JSON_EXTRACT(%s, '$'). On the SQLite path the
# F2P exercises (refinement.md §3.1 flag/branch dependency), this wrapper is wrong:
# a real patch using the MariaDB token on the sqlite branch would emit
# JSON_UNQUOTE(...) and NOT resolve test_key_in on the SQLite harness image. Fails
# Q2 (each slot != wrapped_slot()). Code points below spell
# "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))" (and that + ", ").
_WEAK_WRONG_WRAPPER = """\
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        Invariant(len(result) >= 0)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i == num_values:
            result = [74, 83, 79, 78, 95, 85, 78, 81, 85, 79, 84, 69, 40,
                      74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40,
                      37, 115, 44, 32, 39, 36, 39, 41, 41]
        else:
            result = [74, 83, 79, 78, 95, 85, 78, 81, 85, 79, 84, 69, 40,
                      74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40,
                      37, 115, 44, 32, 39, 36, 39, 41, 41, 44, 32] + result
        i = i - 1
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "Structurally-different (branches reordered, literals bound to "
                     "typed locals) but behaviourally identical correct impl; keeps "
                     "the back-to-front loop and the gold front-recursive invariant "
                     "ToSeq(result)==slots_sql(num_values-i). Must verify, else "
                     "SPEC-TOO-STRONG (Q2 rejects a faithful correct impl).",
    },
    {
        "id": "admiss-1",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "Asserts the precondition num_values >= 1 admits the F2P "
                     "single-value (num_values==1) and multi-value counts, then "
                     "runs the gold body. Must verify, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BARE),
        "refinement": "This is the pre-fix behaviour verbatim (== model_prepatch.py): "
                      "no KeyTransformIn override, so In.process_rhs's bare `%s` slots "
                      "survive. key__in compares the raw stored representation, "
                      "selecting the wrong/empty set, so test_key_in does NOT resolve.",
        "rationale": "Rejected at Q2: every slot is bare_slot() %s, so ToSeq(Result()) "
                     "!= slots_sql(num_values) for all num_values >= 1. A verify here "
                     "would be SPEC-TOO-WEAK (rejection comes from postcondition Q2).",
    },
    {
        "id": "partial-last-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_LAST_BARE),
        "refinement": "Wraps all-but-the-trailing slot; the trailing slot stays bare. "
                      "On the SINGLE-value sub-domain (num_values==1, the issue's exact "
                      "case) the only slot is the trailing one, so it emits bare `%s` — "
                      "key__in=[v] would NOT match key=v and test_key_in does NOT resolve.",
        "rationale": "Partial-domain (single-value sub-domain). Rejected at Q2: the "
                     "trailing slot != wrapped_slot(), so ToSeq(Result()) != "
                     "slots_sql(num_values) at num_values==1 (and any count). A verify "
                     "here would be SPEC-TOO-WEAK.",
    },
    {
        "id": "partial-multi-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_MULTI_BARE),
        "refinement": "Complementary split: correct for num_values==1 but leaves every "
                      "non-trailing slot bare for num_values>=2. A real patch wrapping "
                      "only the last value's slot emits wrong SQL for key__in over >=2 "
                      "values, so test_key_in (a list-membership lookup) does NOT resolve.",
        "rationale": "Partial-domain (multi-value sub-domain). Rejected at Q2: a "
                     "non-trailing slot != wrapped_slot(), so ToSeq(Result()) != "
                     "slots_sql(num_values) for num_values>=2. A verify here would be "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-wrong-wrapper",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG_WRAPPER),
        "refinement": "Every slot uses the MariaDB wrapper JSON_UNQUOTE(JSON_EXTRACT(%s, "
                      "'$')) instead of the SQLite/MySQL wrapper JSON_EXTRACT(%s, '$'). "
                      "The F2P runs on the SQLite branch (refinement.md §3.1); the "
                      "MariaDB token is wrong there, so test_key_in does NOT resolve on "
                      "the SQLite harness image.",
        "rationale": "Supporting near-miss with a real refinement. Rejected at Q2: each "
                     "slot != wrapped_slot() (different SQL constant), so ToSeq(Result()) "
                     "!= slots_sql(num_values). A verify here would be SPEC-TOO-WEAK.",
    },
]


# meta.axioms == []; no @ContractOnly axiom is consumed by the proof. The single
# deep_model_reference (slots_sql, an A-reference) is validated == the real
# %-substitution by axiom_check.py (G-AX) and is not an axiom the proof trusts.
AXIOM_TESTS = []
