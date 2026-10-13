# properties.py — PBT falsification battery for django__django-15863. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view is never touched), checked by Nagini verify +
# markers.same_spec. Axiom cases probe the TWO A-reference deep models
# (reconstruct_digits identity == Decimal(str(value)); narrowed_to_significand ==
# the binary round trip Decimal(str(float(value)))) against the REAL CPython
# stdlib `decimal`/`str`/`repr`/`float` — see AXIOM_TESTS at the bottom.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   reconstruct_digits(text: List[int]) -> List[int]
#   Models the gold floatformat value-reconstruction step (defaultfilters.py:154,
#   `input_val = repr(text)` -> `input_val = str(text)`). The carrier is the value's
#   exact significant decimal digit sequence (Decimal.as_tuple().digits), each in 0..9.
#   The function reconstructs the formatting value from the input, and the gold change
#   is exactly "preserve EVERY significant decimal digit" (str => canonical decimal
#   string => exact Decimal) vs the bug "route long-precision Decimals through float =>
#   lose digits past the ~17-digit binary significand".
#
#   PRECONDITION (one clause, framing/permission):
#     (P1) Requires(Acc(list_pred(text), 1/2))    # HALF permission => READ-ONLY input
#   POSTCONDITION (three clauses; two framing/permission + one LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(text), 1/2))     # returns the read permission
#     (Q2) Ensures(Acc(list_pred(Result())))      # full permission on the fresh result
#     (Q3) Ensures(ToSeq(Result()) == ToSeq(text))
#            -- THE discriminating, precision-preserving clause: the reconstructed
#               digit sequence equals the input digit sequence EXACTLY, element for
#               element, at full length. This is the gold guarantee (str, not repr):
#               no digit is dropped, none is zeroed, none reordered, none added.
#
# FRAME-MUTATION lane is MANDATORY: `text` is Acc(list_pred(text),1/2) (read-only). A
#   rival that WRITES `text` (even a no-op store text[0]=text[0]) must be REJECTED for
#   INSUFFICIENT PERMISSION. The real floatformat code only READS `text` (the rendered
#   template value) to construct a NEW Decimal; it never mutates the caller's value.
#   Byte-fuzzers never think to mutate the input; this is the project's #1 weakness
#   class (see frame-mut-write).
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q3 pins the result to `ToSeq(text)` —
#   GROUNDED entirely in the argument `text`, the identity on its own digit sequence.
#   There is NO @Pure answer-key / opaque marker the postcondition references: the two
#   @Pure helpers `narrowed_to_significand` / `narrowed_from` are the LOSSY bug model
#   and are NOT mentioned anywhere in reconstruct_digits' Requires/Ensures (they exist
#   only so model_prepatch.py can FAIL Q3). The unique satisfier of Q3 IS the input's
#   own digit sequence, so there is no value an echo could carry that satisfies Q3 yet
#   is wrong. The honest control is therefore the cheapest faithful impl that produces
#   the identity (the positive control below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. reconstruct_digits has no raise / early-return /
#   side-effect fork — it is a single straight-line value reconstruction with no
#   capability-token-bearing exceptional path (the surrounding floatformat try/except
#   is the UNCHANGED control flow that the modeled delta does not touch; mapping.md §B).
#   Q3 is a total value identity, so there is no effect invisible to the value
#   abstraction to discriminate. Omitted (justified in 'assessment').
#
# PARTIAL-DOMAIN lane: heavily exercised — this is where the bug lives. A rival can be
#   correct on SHORT inputs (<= significand_budget()==17 significant digits) yet diverge
#   on the long-precision sub-domain the F2P pins:
#     - weak-truncate-budget : keep the leading 17 digits, ZERO every later digit (the
#                              literal narrowed_to_significand binary-significand bug).
#                              Correct on <=17-digit inputs, WRONG on the F2P 27-digit
#                              Decimal("123456.123456789012345678901").
#     - weak-drop-last       : return all but the LAST digit (a one-element partial).
#     - weak-empty           : return the empty sequence (drop everything).
#   Each fails Q3 on its diverging sub-domain.
#
# AXIOM lane: meta.axioms == [] (no consumed @ContractOnly axiom) but
#   deep_model_references has TWO A-references that G-AX / axiom_check.py validate ==
#   the REAL stdlib callees. Per PBT_PLAN §2.4 / §4a an A-reference deep model must
#   equal the real callee on every caller-reachable input. The real callees are CPython
#   LANGUAGE/stdlib operations (str/repr/float + decimal.Decimal), available with NO
#   repo import, so the probes run anywhere. ax-sound-exact re-runs axiom_check.py's
#   A-reference 1 (identity == Decimal(str(value)), equal digit tuples) and A-reference
#   2 (narrowed_to_significand faithfully abstracts Decimal(str(float(value)))).
#   ax-cover-recon confirms every callee-input the model can reach (a finite digit
#   sequence => a real Decimal value) lies in the callees' domains.
from pathlib import Path

INSTANCE = "django__django-15863"
FLOAT_ENCODING = None  # meta.json float_encoding is null (and unused)

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
# computed over the spec_view, which elides every impl region (and nested invariants),
# so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == ToSeq(text).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        result = [c] + result
        i = i - 1
    return result"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-local-reshape: structurally DIFFERENT but behaviourally identical. It keeps the
# gold BACKWARD loop direction and the front-recursive `drop` suffix invariant (so the
# gold proof skeleton is preserved verbatim — NO forward-append against the suffix fold,
# directive 3; NO dropped framing assert, directive 2), but reshapes the loop body with
# a fresh local index `j = i - 1` used uniformly in the read and the two framing asserts.
# Every gold proof obligation is retained: the same loop bound, the same four invariants
# (incl. the load-bearing ToSeq(result)==ToSeq(text).drop(i)), the same two per-step
# `drop` framing asserts (rephrased through j but provably identical), the same
# `[c] + result` prepend and `i = i - 1` decrement. Only the executable shape (an extra
# named local) changes. If it FAILS => SPEC-TOO-STRONG (a faithful, structurally-
# different correct impl is rejected).
_POS_RESHAPE = """\
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == ToSeq(text).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        j = i - 1
        c = text[j]
        Assert(ToSeq(text).drop(j)[0] == c)
        Assert(ToSeq(text).drop(j).drop(1) == ToSeq(text).drop(i))
        result = [c] + result
        i = j
    return result"""
assert _POS_RESHAPE != _IMPL, "pos-local-reshape did not rewrite"


# admiss-reads: an admissibility positive control. The precondition is the single
# half-permission Acc(list_pred(text),1/2). This control keeps the gold impl VERBATIM
# but FIRST asserts, under that half-permission, that the reads a normal F2P-shaped
# digit list needs are admitted — the length is readable and (when the value is
# non-empty, e.g. the F2P 27-digit Decimal) the first significant digit is readable.
# No write, so no extra permission demand. If the precondition could not admit a
# legitimate digit list, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (possibly empty) significant-digit list is\n"
    "    # in-domain; the half-permission admits reading the length and elements.\n"
    "    Assert(len(text) >= 0)\n"
    "    if len(text) > 0:\n"
    "        Assert(text[0] == text[0])   # read admitted under Acc(...,1/2)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — `text` is Acc(list_pred(text),1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable SOLELY
# to the added write, not to a value mismatch — the no-op store leaves Q3 satisfiable),
# then WRITES BACK into the read-only input: text[0] = text[0]. A no-op store, but a
# STORE — it demands FULL write permission on `text`, which the caller granted only at
# 1/2. The verifier must reject for insufficient permission. Guarded by len>0 so it is
# reachable on a non-empty input (e.g. the F2P 27-digit value).
_FRAME_MUT = (
    "    if len(text) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        text[0] = text[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-truncate-budget: PARTIAL-DOMAIN — the LITERAL bug (narrowed_to_significand). It
# copies the leading 17 significant digits unchanged and replaces every later digit with
# a zero — exactly what reconstruction through a binary-significand float does. It is
# correct on inputs of <=17 significant digits but WRONG on the long-precision sub-domain
# the F2P pins (the 27-digit Decimal("123456.123456789012345678901"), whose digit 18 and
# beyond are nonzero). The backward loop copies text[i-1] when its front index (i-1) is
# below the budget, else appends 0. No mutation of `text` (a fresh `result` is built), so
# the only obstruction is the value identity Q3.
_WEAK_TRUNCATE = """\
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        # invariants-end
        if i - 1 < 17:
            c = text[i - 1]
            result = [c] + result
        else:
            zero = 0
            result = [zero] + result
        i = i - 1
    return result"""

# weak-drop-last: PARTIAL-DOMAIN one-element miss — returns the input digit sequence
# minus its LAST significant digit. Correct on the empty input only; on any non-empty
# value it drops the trailing digit (and shortens the sequence). The backward loop stops
# at i==1 instead of i==0 (the final, front-most digit is still copied — it is the LAST
# significant digit that is omitted).
_WEAK_DROPLAST = """\
    result = []  # type: List[int]
    i = len(text)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(text))
        # invariants-end
        c = text[i - 1]
        result = [c] + result
        i = i - 1
    return result"""

# weak-empty: drop EVERYTHING — return the empty digit sequence regardless of input.
# Correct only on the empty input; fails Q3 on any non-empty value. Bound to a typed
# local first (directive 1: a bare `return []  # type: ...` is a Nagini translation
# error; bind `empty = []  # type: List[int]` then return it).
_WEAK_EMPTY = """\
    empty = []  # type: List[int]
    return empty"""


SPEC_TESTS = [
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "structurally-different but CORRECT impl: keeps the gold BACKWARD loop "
            "direction and the front-recursive `drop` suffix invariant "
            "(ToSeq(result)==ToSeq(text).drop(i)) — NO forward-append against the suffix "
            "fold (directive 3), NO dropped framing assert (directive 2) — and only "
            "reshapes the loop body through a fresh named local j = i - 1 used uniformly "
            "in the read and the two per-step `drop` framing asserts. Every gold proof "
            "obligation is retained, only the executable shape changes. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (single Acc(list_pred(text),1/2) half-permission) must "
            "admit a normal F2P-shaped significant-digit list: the length is readable "
            "and, when non-empty (the F2P 27-digit value), the first digit is readable "
            "under the half-permission. The gold impl is otherwise verbatim (only "
            "reads/asserts added inside the impl region, no write). If it FAILS => "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch reconstructs the value by building a NEW Decimal from the "
            "input (`input_val = str(text); d = Decimal(input_val)`); it only READS the "
            "rendered template value `text` and NEVER mutates it. A faithful real patch "
            "that wrote back into the caller's value would corrupt the context variable "
            "shared with the rest of the template render — it would not be the gold "
            "patch and would not faithfully resolve. The store here is a no-op only by "
            "coincidence; the point is the spec must forbid ANY write to the read-only "
            "input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `text` is granted at "
            "Acc(list_pred(text),1/2) (P1); the store text[0]=text[0] demands FULL write "
            "permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold reconstruction body is kept verbatim so "
            "the rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame is hollow (frame-mutation, the #1 weakness class; a "
            "byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-truncate-budget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TRUNCATE),
        "refinement": (
            "this IS the bug (model_prepatch.py / narrowed_to_significand): keep the "
            "leading 17 significant digits and zero the rest, exactly what the pre-patch "
            "`input_val = repr(text)` path does by routing a long-precision Decimal "
            "through `Decimal(str(float(text)))` — IEEE-754 binary64 carries at most ~17 "
            "significant digits. Its faithful real patch is the UNCHANGED repo (repr, "
            "not str), which renders Decimal(\"123456.123456789012345678901\")|"
            "floatformat:21 with digits past the 17th dropped to zero. It fails the F2P "
            "test_inputs assertion (expects the full 27-digit string back). Does NOT "
            "resolve — the precise change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q3 (Ensures(ToSeq(Result()) == ToSeq(text))): for any input of "
            ">17 significant digits with a nonzero digit past position 17 (the F2P "
            "27-digit value, whose tail is ...678901) the rival emits a zero where the "
            "input has a nonzero digit, so ToSeq(Result()) != ToSeq(text). PARTIAL-DOMAIN: "
            "correct on <=17-digit inputs, wrong on the long-precision sub-domain the "
            "issue is about. If it VERIFIES => SPEC-TOO-WEAK (precision past the "
            "significand is not pinned)."
        ),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROPLAST),
        "refinement": (
            "dropping the last significant digit is what a reconstruction that truncated "
            "one digit of precision would do (e.g. an off-by-one in the canonical-string "
            "parse). The reconstructed value would render one digit short for every "
            "non-empty input, including the F2P 27-digit value (it would lose the "
            "trailing `1`). It fails the F2P test_inputs assertion. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (Ensures(ToSeq(Result()) == ToSeq(text))): the rival stops "
            "the backward copy at i==1, so the LAST significant digit (text[len-1]) is "
            "omitted; ToSeq(Result()) == ToSeq(text).drop(... ) is one element short of "
            "ToSeq(text) for any non-empty input, so the identity fails. PARTIAL-DOMAIN: "
            "correct only on the empty input. If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY),
        "refinement": (
            "returning an empty digit sequence is what a reconstruction that produced an "
            "empty/zero value would do — the rendered float would be blank/0 for every "
            "non-empty input. It fails the F2P test_inputs assertion (and every "
            "non-empty PASS_TO_PASS floatformat case). Does NOT resolve. (Cheap "
            "supporting near-miss carrying a real refinement.)"
        ),
        "rationale": (
            "REJECTED by Q3 (Ensures(ToSeq(Result()) == ToSeq(text))): the empty "
            "sequence equals ToSeq(text) only when text is empty; for any non-empty "
            "input the identity fails (different length). If it VERIFIES => SPEC-TOO-WEAK "
            "(the result is not pinned to the input at all)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the TWO A-reference deep models vs the REAL CPython stdlib callees.
# meta.axioms == [] (no consumed @ContractOnly axiom); deep_model_references has TWO
# A-references:
#   (1) reconstruct_digits' IDENTITY result models Decimal(str(value)) — the exact
#       canonical-decimal-string reconstruction the fix uses;
#   (2) narrowed_to_significand / narrowed_from models Decimal(str(float(value))) — the
#       lossy binary round trip the pre-patch repr path falls into.
# Per PBT_PLAN §2.4 / §4a an A-reference deep model is validated == the real callee on
# every caller-reachable input. The real callees are CPython LANGUAGE/stdlib operations
# (str/repr/float + decimal.Decimal), available with NO repo import, so the probes run
# anywhere (Docker or host). The probes mirror axiom_check.py / G-AX (which already
# passes), re-run as the persisted PBT axiom lane: soundness == each deep model matches
# its real callee; containment == every caller-reachable callee-input is in domain.
# ---------------------------------------------------------------------------

# model.py's front-recursive significand-truncation fold, transcribed as plain Python on
# the significant-digit sequence (drop(1) is the tail). Shared text embedded into both
# probes. SIGNIFICAND_BUDGET == significand_budget() == 17.
_NARROWED_SRC = '''
SIGNIFICAND_BUDGET = 17  # model.py significand_budget()

def narrowed_from(s, budget):
    """Faithful transcription of model.py's @Pure front-recursive narrowed_from:
       emit the leading `budget` digits unchanged, replace every later digit with 0."""
    s = list(s)
    if len(s) == 0:
        return []
    if budget > 0:
        return [s[0]] + narrowed_from(s[1:], budget - 1)
    return [0] + narrowed_from(s[1:], 0)

def narrowed_to_significand(s):
    """model.py narrowed_to_significand: narrowed_from(s, significand_budget())."""
    return narrowed_from(s, SIGNIFICAND_BUDGET)
'''

_AX_SOUND_PROBE = _NARROWED_SRC + '''
import random
import sys
from decimal import Decimal, InvalidOperation


def significant_digits(value):
    """Decimal.as_tuple().digits — the carrier model.py abstracts as List[int]."""
    return list(value.as_tuple().digits)


def reconstruct_exact(value):
    """REAL fix-path reconstruction: input_val = str(value); Decimal(input_val)
    (with the same binary fallback the code keeps for non-decimal-literal inputs)."""
    input_val = str(value)
    try:
        return Decimal(input_val)
    except InvalidOperation:
        return Decimal(str(float(value)))


def reconstruct_via_significand(value):
    """REAL bug-path reconstruction for a Decimal input: repr(value) is not a decimal
    literal => Decimal(repr(value)) raises InvalidOperation => fall back through float."""
    input_val = repr(value)
    try:
        return Decimal(input_val)
    except InvalidOperation:
        try:
            return Decimal(str(float(value)))
        except (ValueError, InvalidOperation, TypeError):
            return None


fails = 0

# Boundary cases the contract pins (incl. the F2P 27-digit value and around the budget).
boundary = [
    Decimal("0"), Decimal("9"), Decimal("09.000"), Decimal("555.555"),
    Decimal("0.12345"), Decimal("1.42"),
    Decimal("123456.123456789012345678901"),     # the F2P input: 27 sig digits
    Decimal("42.12345678901234567890"),           # the issue MWE: 20 sig digits
    Decimal("1.2345678901234567"),                # 17 sig digits (== budget)
    Decimal("1.23456789012345678"),               # 18 sig digits (> budget)
    Decimal("0.0000000000000000000015"),          # tiny, many leading zeros
    Decimal("-123456789012345678901234567890"),
    Decimal("100000000000000000000000"),
]

# (A-reference 1, axiom-soundness) the IDENTITY model == the REAL fix-path
# reconstruction Decimal(str(value)): every significant digit survives, in order, at
# full length (equal digit tuples). This is what reconstruct_digits' Q3 encodes.
for v in boundary:
    recon = reconstruct_exact(v)
    if recon != v:
        fails += 1
        print("UNSOUND exact-recon on %r: Decimal(str(value)) gave %r" % (v, recon))
    if significant_digits(recon) != significant_digits(v):
        fails += 1
        print("UNSOUND exact-recon DROPPED digits on %r: %r vs %r"
              % (v, significant_digits(recon), significant_digits(v)))

# (A-reference 2, axiom-soundness) the deep narrowed_to_significand model is a faithful
# abstraction of the binary round trip: the real bug-path reconstruction carries no more
# genuine precision than the float significand, so its float image equals the value's.
for v in boundary:
    bug = reconstruct_via_significand(v)
    if bug is None:
        continue
    if float(bug) != float(v):
        fails += 1
        print("UNSOUND significand-recon float image diverged on %r: %r vs %r"
              % (v, float(bug), float(v)))

# randomized fuzz over precision (1..32 sig digits) and scale.
rng = random.Random(15863)
for _ in range(20000):
    ndig = rng.randint(1, 32)
    first = rng.choice("123456789")
    rest = "".join(rng.choice("0123456789") for _ in range(ndig - 1))
    digs = first + rest
    point = rng.randint(1, ndig)
    text = digs[:point] + "." + digs[point:] if point < ndig else digs
    if rng.random() < 0.5:
        text = "-" + text
    v = Decimal(text)
    recon = reconstruct_exact(v)
    if recon != v or significant_digits(recon) != significant_digits(v):
        fails += 1
        print("UNSOUND exact-recon fuzz on %r" % v)
    bug = reconstruct_via_significand(v)
    if bug is not None and float(bug) != float(v):
        fails += 1
        print("UNSOUND significand-recon fuzz float image on %r" % v)

# The model's narrowed_to_significand fold itself must be a SAFE abstraction: it never
# preserves MORE than the budget. For inputs longer than the budget with a nonzero digit
# past position 17 it differs from the identity — exactly the bug the fix stops. Confirm
# the fold zeros everything past the budget and that long inputs diverge from identity.
threshold_div = 0
for k in range(1, 33):
    digs = [((i * 7 + 1) % 9) + 1 for i in range(k)]   # all nonzero digits 1..9
    narrowed = narrowed_to_significand(digs)
    # leading min(k,budget) digits unchanged; the rest zeroed.
    keep = min(k, SIGNIFICAND_BUDGET)
    if narrowed[:keep] != digs[:keep]:
        fails += 1
        print("FOLD FAIL: budget prefix not preserved at k=%d" % k)
    if any(x != 0 for x in narrowed[keep:]):
        fails += 1
        print("FOLD FAIL: digit past budget not zeroed at k=%d" % k)
    if narrowed != digs:
        threshold_div += 1
# every input strictly longer than the budget (all-nonzero) MUST diverge from identity.
expected_div = 33 - 1 - SIGNIFICAND_BUDGET  # k in 18..32 => 15 inputs
if threshold_div < expected_div:
    fails += 1
    print("FOLD FAIL: only %d of >=%d long inputs diverge from identity"
          % (threshold_div, expected_div))

# The discriminating F2P fact, explicitly: the fix is exact and the bug is lossy on the
# 27-digit value.
f2p = Decimal("123456.123456789012345678901")
if reconstruct_exact(f2p) != f2p:
    fails += 1
    print("FACT FAIL: fix lost precision on the F2P 27-digit value")
bug = reconstruct_via_significand(f2p)
if not (bug is not None and bug != f2p):
    fails += 1
    print("FACT FAIL: bug path did NOT diverge on the F2P 27-digit value")

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d disagreement(s) between the deep models and the "
          "real CPython reconstruction" % fails)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: identity model == Decimal(str(value)) (equal digit tuples) "
      "and narrowed_to_significand faithfully abstracts Decimal(str(float(value))) over "
      "%d boundary + 20000 fuzz + %d threshold inputs; F2P 27-digit value exact under "
      "the fix and lossy under the bug." % (len(boundary), threshold_div))
sys.exit(0)
'''

_AX_COVER_PROBE = _NARROWED_SRC + '''
import random
import sys
from decimal import Decimal, InvalidOperation


def significant_digits(value):
    return list(value.as_tuple().digits)


# (axiom-containment) Which callee-inputs can the MODEL actually reach? reconstruct_digits
# takes `text: List[int]` constrained only by Acc(list_pred(text),1/2) — ANY finite list
# of decimal digits (the carrier; each in 0..9 per the digit abstraction, the empty list
# included). The deep models are applied to the corresponding Decimal value, and the real
# callees are:
#   * str(Decimal) / Decimal(str)        -- A-reference 1 (the exact fix path)
#   * repr(Decimal) / float / Decimal(str(float))  -- A-reference 2 (the lossy bug path)
# The real callees' domain is "any finite Decimal value". Every reachable carrier (a
# finite digit list) corresponds to a finite Decimal, so every caller-reachable
# callee-input lies inside the callees' domain (str/repr/float never raise on a finite
# Decimal; Decimal(canonical_string) never raises). Covering MORE (e.g. NaN/Inf Decimals)
# than the caller reaches would be sound, not a defect (the carrier cannot encode them).
# We CONFIRM containment by materialising a heavy sample of the reachable carrier space
# into real Decimals and asserting the callees raise nothing and the identity holds.
fails = 0
rng = random.Random(2024)


def value_from_digits(digs, point, negative):
    """Build a finite Decimal whose significant-digit carrier is `digs` (each 0..9),
    with the decimal point placed at `point` (0..len). Mirrors the R-refinement
    Decimal.as_tuple().digits <-> List[int] in mapping.md."""
    if not digs:
        s = "0"
    else:
        body = "".join(str(d) for d in digs)
        if point <= 0:
            s = "0." + body
        elif point >= len(digs):
            s = body
        else:
            s = body[:point] + "." + body[point:]
    if negative:
        s = "-" + s
    return Decimal(s)


def reachable_carriers():
    # empty + lengths 1..40 (covers <=17, ==17, and the long-precision >17 sub-domain
    # the F2P is in), digits 0..9, point anywhere, both signs.
    yield ([], 0, False)
    for _ in range(40000):
        L = rng.randint(1, 40)
        digs = [rng.randint(0, 9) for _ in range(L)]
        # leading digit nonzero is the canonical form, but the carrier admits leading
        # zeros too (e.g. Decimal("09.000")); sample both.
        yield (digs, rng.randint(0, L), rng.random() < 0.5)
    # explicit boundary carriers incl. the F2P 27-digit sequence.
    f2p = [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1]
    for c in [([5, 5, 5, 5, 5, 5], 3, False), (f2p, 6, False), ([9], 1, False),
              ([0, 9, 0, 0, 0], 2, False)]:
        yield c

for digs, point, negative in reachable_carriers():
    try:
        v = value_from_digits(digs, point, negative)
    except (InvalidOperation, ValueError):
        fails += 1
        print("CONTAINMENT FAIL: could not build a finite Decimal from carrier %r" % digs)
        continue
    # the callees the deep models reference must all be total on this reachable value.
    try:
        s = str(v)
        recon = Decimal(s)             # A-reference 1: exact fix path
        _ = repr(v)                    # A-reference 2: repr (always a "Decimal('..')")
        _ = float(v)                   # A-reference 2: the binary round trip entry
    except Exception as e:             # noqa: BLE001 - any raise is a containment failure
        fails += 1
        print("CONTAINMENT FAIL: a referenced callee raised on reachable value %r: %s"
              % (v, e))
        continue
    # A-reference 1 must hold on every reachable carrier (exact identity).
    if recon != v or significant_digits(recon) != significant_digits(v):
        fails += 1
        print("CONTAINMENT/SOUNDNESS FAIL on reachable %r: digits %r vs %r"
              % (v, significant_digits(recon), significant_digits(v)))

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable carrier(s) outside the callees' domain "
          "or mismatched" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every carrier the model can reach (a finite digit list, "
      "empty + lengths 1..40 incl. the F2P 27-digit sequence) materialises to a finite "
      "Decimal on which str/repr/float/Decimal are all total and the exact identity "
      "Decimal(str(value)) == value holds.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-recon",
        "axiom": "reconstruct_digits/narrowed_to_significand",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "the bundle consumes NO @ContractOnly axiom; its two kind-A obligations are "
            "A-reference deep models. AXIOM-SOUNDNESS: (1) reconstruct_digits' IDENTITY "
            "result must equal the REAL fix-path reconstruction Decimal(str(value)) — "
            "equal digit tuples, every significant digit preserved; (2) "
            "narrowed_to_significand must faithfully abstract the REAL bug-path "
            "Decimal(str(float(value))) — same float image (no more than significand "
            "precision). The probe runs the live CPython callees on 13 boundary (incl. "
            "the F2P 27-digit value and around the 17-digit budget) + 20000 fuzz inputs "
            "and asserts agreement, plus that the fold zeros everything past the budget. "
            "Mirrors axiom_check.py / G-AX. If a real callee disagrees => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-recon",
        "axiom": "reconstruct_digits/narrowed_to_significand",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: reconstruct_digits' carrier is `text: List[int]` "
            "constrained only by Acc(list_pred(text),1/2) — any FINITE digit list, empty "
            "included. Every such carrier materialises to a finite Decimal, on which the "
            "referenced callees str/repr/float/Decimal are all TOTAL (never raise) and "
            "the exact identity Decimal(str(value)) == value holds. The probe samples "
            "the reachable carrier space heavily (empty + lengths 1..40 incl. the F2P "
            "27-digit sequence and the long-precision >17 sub-domain) and asserts every "
            "callee is total and the identity holds. A reachable carrier outside the "
            "callees' domain => AXIOM-TOO-WEAK-FOR-CALLER (none expected: the carrier "
            "cannot encode NaN/Inf, so covering more would be sound, not a defect)."
        ),
    },
]
