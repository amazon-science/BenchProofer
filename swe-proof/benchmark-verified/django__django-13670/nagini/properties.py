# properties.py — PBT falsification battery for django__django-13670.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are full
# model.py variants that share the FROZEN spec verbatim (region surgery edits
# ONLY inside # impl-start/# impl-end) and are checked by Nagini verify +
# markers.same_spec; this bundle has no @ContractOnly axiom (axioms[] == []),
# so AXIOM_TESTS is empty.
#
# Defended surface (read tasks/django__django-13670/model.py):
#   abbreviated_year(year: int) renders the two-digit abbreviated year.
#   - INPUT is an int SCALAR with Requires(1 <= year <= 9999). There is NO
#     read-only list parameter (no Acc(x, 1/2)), so the frame-mutation class is
#     N/A here (confirmed by G-HYGIENE: "no full-permission read-only list
#     param (year is an int scalar)"). See 'assessment'.
#   - The postcondition is FULLY GROUNDED in the input: it pins
#       len(Result()) == 2,
#       48 <= Result()[k] <= 57            (decimal-digit code points),
#       Result()[0] == tens_digit(year % 100)  == 48 + (year%100)//10,
#       Result()[1] == units_digit(year % 100) == 48 + (year%100)%10,
#     where tens_digit/units_digit are @Pure and FULLY UNFOLDED (bodies are the
#     literal arithmetic). There is no opaque answer-key oracle to echo without
#     doing the work — the "oracle" IS a closed-form function of `year`. So the
#     ungrounded-oracle-echo class has no WRONG echo to build; in its place we
#     supply an honest cheapest-impl positive control. See 'assessment'.
#   - The function is pure value computation; there is no raise / return /
#     side-effect distinction the value abstraction misses, so the
#     control-flow-effect class is N/A. See 'assessment'.
#
# The load-bearing discriminator (the actual bug the gold patch fixes) is the
# leading-zero / fixed-width-2 guarantee for years whose last two digits are
# below ten (the F2P witness 4 -> '04'): the old body str(year)[2:] yields an
# empty/short string there. Our partial-domain rivals attack exactly this seam.

from pathlib import Path

INSTANCE = "django__django-13670"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl region (verbatim between the markers in model.py). All rivals
# are produced by replacing ONLY this block, so same_spec is guaranteed.
_IMPL = """    # impl-start
    v = year % 100
    result = [tens_digit(v), units_digit(v)]  # type: List[int]
    return result
    # impl-end"""


def _swap_impl(new_body: str) -> str:
    """Return _BASE with the impl region replaced by `new_body` (which must
    itself open with '    # impl-start' and close with '    # impl-end')."""
    if _IMPL not in _BASE:
        raise AssertionError("drift: frozen impl region not found verbatim")
    if _BASE.count(_IMPL) != 1:
        raise AssertionError("frozen impl region not unique")
    return _BASE.replace(_IMPL, new_body, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally-DIFFERENT but CORRECT impl.
# Shape change: compute v, then build the two code points via explicit per-digit
# locals in a DIFFERENT order (units first, then tens) and assemble with a typed
# local list bound BEFORE return (the # type: comment attaches to an assignment
# target, never a bare return — pilot bug #1). The arithmetic is still linear
# integer //,% which Viper discharges against tens_digit/units_digit; we keep no
# loop, so there is no invariant/lemma to lose (pilot bugs #2/#3 N/A). If this
# fails to verify, the postcondition is SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_CONTROL = """    # impl-start
    v = year % 100
    u = 48 + (v % 10)            # units code point, computed first
    t = 48 + (v // 10)           # tens code point, computed second
    out = [t, u]                 # type: List[int]
    return out
    # impl-end"""

# A second positive control: same shape as gold but assembled by appending to a
# fresh typed list (different executable shape, no loop). Must verify.
_POS_CONTROL_APPEND = """    # impl-start
    v = year % 100
    out = []                     # type: List[int]
    out.append(tens_digit(v))
    out.append(units_digit(v))
    return out
    # impl-end"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY: a caller that establishes the precondition for an F2P-shaped
# input (year=4, the 4 -> '04' witness in the sub-100 leading-zero regime) and
# self-calls abbreviated_year, asserting its postcondition discharges. We keep
# the gold impl so the only thing under test is whether Requires admits a normal
# input. If the call site cannot establish Requires for a legitimate year, the
# precondition is PRECOND-TOO-STRONG. (Implemented as a second function added
# AFTER the gold return, INSIDE the impl region, so same_spec is preserved.)
# ---------------------------------------------------------------------------
_ADMISS = """    # impl-start
    v = year % 100
    result = [tens_digit(v), units_digit(v)]  # type: List[int]
    return result


def _admiss_caller() -> None:
    # F2P-shaped in-domain witness from test_year_before_1000: year 4 -> '04'.
    r = abbreviated_year(4)
    Assert(len(r) == 2)
    Assert(r[0] == 48)   # '0' — the leading zero the change supplies
    Assert(r[1] == 52)   # '4'
    # impl-end"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals (each expect=reject). Every one shares the
# spec verbatim and changes only the impl; each carries the refinement argument
# that its faithful real patch would NOT resolve the F2P.
# ---------------------------------------------------------------------------

# R1 — the PRE-PATCH behaviour, reproduced deeply: render the full decimal
# expansion and drop the first two characters (str(year)[2:]). For years < 100
# this yields fewer than two characters, so len(Result()) != 2. Rejects on
# Ensures(len(Result()) == 2). This is the bug the gold patch fixes.
_R1_SLICE = """    # impl-start
    # Pre-patch shape: build the year's 1..4 decimal digits (most significant
    # first) and keep everything from the third character on — i.e. str(year)[2:].
    digits = []  # type: List[int]
    if year >= 1000:
        digits = digits + [48 + (year // 1000) % 10]
    if year >= 100:
        digits = digits + [48 + (year // 100) % 10]
    if year >= 10:
        digits = digits + [48 + (year // 10) % 10]
    digits = digits + [48 + year % 10]
    result = digits[2:]  # type: List[int]
    return result
    # impl-end"""

# R2 — wrong modulus: reduce modulo 1000 instead of 100, then take two digits.
# For year=476 this is 476 (three digits): the tens position becomes
# 48 + (476//10) = 95, outside 0x30..0x39, and != tens_digit(476 % 100 == 76).
# Rejects on the digit-range AND tens_digit pins.
_R2_MOD1000 = """    # impl-start
    v = year % 1000
    result = [48 + (v // 10), 48 + (v % 10)]  # type: List[int]
    return result
    # impl-end"""

# R3 — transposed digits: units then tens. For year=42 yields [units,tens] =
# ['2','4'] but the postcondition pins Result()[0] == tens_digit(42) == '4'.
# Rejects on the element-wise tens/units pins.
_R3_SWAP = """    # impl-start
    v = year % 100
    result = [units_digit(v), tens_digit(v)]  # type: List[int]
    return result
    # impl-end"""

# R4 — three-character output (a real off-by-one a faithful patch could have):
# emit hundreds/tens/units of year%1000-ish. Concretely emit a length-3 list.
# Rejects on Ensures(len(Result()) == 2).
_R4_LEN3 = """    # impl-start
    v = year % 100
    result = [tens_digit(v), units_digit(v), units_digit(v)]  # type: List[int]
    return result
    # impl-end"""

# R5 — partial-domain leading-zero drop: correct for year%100 >= 10, but for the
# sub-ten tail it emits a single units character (the conventional non-padded
# abbreviation, e.g. '%d' instead of '%02d'). This is the exact seam the change
# defends: year=4 -> ['4'] (len 1). Rejects on Ensures(len(Result()) == 2) for
# the sub-ten sub-domain. Correct elsewhere, so a pure value abstraction that
# dropped the width clause would MISS it — but our spec pins len==2.
_R5_NOPAD = """    # impl-start
    v = year % 100
    if v >= 10:
        result = [48 + (v // 10), 48 + (v % 10)]  # type: List[int]
        return result
    single = [48 + v]  # type: List[int]
    return single
    # impl-end"""

# R6 — off-by-one ON THE LEADING DIGIT only (partial-domain on the tens place):
# tens digit computed as v // 10 + 1 when v >= 10, correct units. Wrong on every
# year with v >= 10 at the tens position; rejects on the tens_digit pin /
# digit-range. (Distinct seam from R3: a single mis-incremented digit.)
_R6_TENS_OFF1 = """    # impl-start
    v = year % 100
    result = [48 + (v // 10) + 1, 48 + (v % 10)]  # type: List[int]
    return result
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_CONTROL),
        "rationale": (
            "structurally-different CORRECT impl (units computed first, tens "
            "second, assembled into a typed local bound before return). The "
            "two code points equal tens_digit/units_digit by linear //,% "
            "arithmetic Viper discharges; no loop, so no invariant/lemma to "
            "lose. Must verify or the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-append",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_CONTROL_APPEND),
        "rationale": (
            "CORRECT impl assembled by appending tens then units to a fresh "
            "typed list (different executable shape from the literal list "
            "constructor; still no loop). Must verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-year4",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_impl(_ADMISS),
        "rationale": (
            "a caller self-calls abbreviated_year(4) — the F2P sub-100 "
            "leading-zero witness — and asserts the postcondition discharges "
            "(len 2, '0' then '4'). The precondition 1<=year<=9999 must admit "
            "a normal in-domain year; if the call site cannot establish "
            "Requires, the precondition is PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "weak-prepatch-slice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_R1_SLICE),
        "refinement": (
            "this IS the pre-patch body str(self.data.year)[2:] reproduced "
            "deeply. As the gold patch's removed line, its faithful real patch "
            "does NOT resolve: test_year_before_1000 expects 4 -> '04' and "
            "42 -> '42', but str(4)[2:] == '' and str(42)[2:] == '' (the F2P "
            "fails). model_prepatch.py is this exact regime."
        ),
        "rationale": (
            "for any year < 100 the deep slice yields fewer than two "
            "characters, so Ensures(len(Result()) == 2) cannot hold; the "
            "rival must REJECT. If it verified, the spec would not sense the "
            "fixed-width change => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-mod1000",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_R2_MOD1000),
        "refinement": (
            "faithful real patch '%02d' % (self.data.year % 1000): for year "
            "476 this is '476' (length 3, not '76'); for 123 it is '123' not "
            "'23'. test_year_before_1000 expects 476 -> '76' and the original "
            "report 123 -> '23', so this patch does NOT resolve."
        ),
        "rationale": (
            "year % 1000 for year=476 is 476; the tens position 48 + 476//10 "
            "= 95 is outside 0x30..0x39 and != tens_digit(year % 100 == 76). "
            "Rejects on the digit-range AND Result()[0]==tens_digit(year%100) "
            "pins; if it verified the modulus would be unconstrained => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-swap-digits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_R3_SWAP),
        "refinement": (
            "faithful real patch that transposes the two characters (units "
            "then tens) renders 42 -> '24', 476 -> '67', 4 -> '40'. None match "
            "the F2P expectations ('42','76','04'), so it does NOT resolve."
        ),
        "rationale": (
            "Result()[0] is pinned to tens_digit(year%100) and Result()[1] to "
            "units_digit(year%100); the transposition violates BOTH whenever "
            "the two digits differ (e.g. year=42). Rejects on the element-wise "
            "pins; if it verified the ordering would be unconstrained => "
            "SPEC-TOO-WEAK (a value-multiset proxy would miss this — the spec "
            "pins per-index)."
        ),
    },
    {
        "id": "weak-len3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_R4_LEN3),
        "refinement": (
            "a faithful patch emitting three characters (e.g. duplicating the "
            "units digit, or '%03d') renders 42 -> '422'/'042' etc.; the F2P "
            "expects exactly two characters '42', so it does NOT resolve."
        ),
        "rationale": (
            "the result has length 3, violating Ensures(len(Result()) == 2). "
            "Rejects on the width clause; if it verified the fixed width would "
            "be unconstrained => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-partial-nopad",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_R5_NOPAD),
        "refinement": (
            "faithful real patch '%d' % (self.data.year % 100) (no zero-pad): "
            "correct for years whose last two digits are >= 10 (476 -> '76', "
            "42 -> '42') but renders 4 -> '4' and 9 -> '9'. test_year_before_"
            "1000 expects 4 -> '04', so this patch does NOT resolve — this is "
            "precisely the leading-zero seam the gold patch fixes."
        ),
        "rationale": (
            "for the sub-ten sub-domain (year%100 < 10) the result is a single "
            "character, violating Ensures(len(Result()) == 2). A rival correct "
            "on most of the domain but diverging on the leading-zero "
            "sub-domain must REJECT on the width clause; if it verified the "
            "spec would miss the exact bug => SPEC-TOO-WEAK (partial-domain)."
        ),
    },
    {
        "id": "weak-tens-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_R6_TENS_OFF1),
        "refinement": (
            "faithful real patch with the tens digit mis-incremented (e.g. "
            "((year//10) % 10 + 1) in the high position): renders 42 -> '52', "
            "476 -> '86'. The F2P expects '42'/'76', so it does NOT resolve."
        ),
        "rationale": (
            "Result()[0] == 48 + (year%100)//10 + 1 != tens_digit(year%100) "
            "whenever year%100 >= 10, and for year%100 in 90..99 it reaches 58 "
            "( ':' ) which also fails the 48<=Result()[0]<=57 range. Rejects "
            "on the tens_digit pin / digit-range; if it verified a per-digit "
            "off-by-one would be admitted => SPEC-TOO-WEAK."
        ),
    },
]

# No @ContractOnly axiom and no A-consumed callee (meta.axioms == []). The only
# soundness obligation is deep-model fidelity of tens_digit/units_digit ==
# '%02d' % (year%100), which axiom_check.py (G-AX) already validates EXHAUSTIVELY
# over all admitted years 1..9999 in Docker. There is no axiom Requires-domain
# containment question here (the @Pure helpers are part of the verified spec,
# not contract-only library axioms), so the axiom lane is vacuous.
AXIOM_TESTS = []  # type: list
