# properties.py — PBT falsification battery for django__django-14373.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap the
# whole `# impl-start` .. `# impl-end` body of render_year and leave the frozen
# spec (axioms / pure / pre / post-conditions / signature) byte-identical.
# same_spec is therefore guaranteed for every case.
#
# Defended surface (read from model.py / refinement.md / instance.json):
#   render_year(year), 1 <= year <= 9999, returns List[int] of ASCII code points.
#   The postcondition pins SIX load-bearing facts about the result:
#     (P1) ToSeq(Result()) == four_field(year)   -- the deep place-value field
#          == PSeq(48+year//1000, 48+(year//100)%10, 48+(year//10)%10, 48+year%10)
#     (P2) len(Result()) == 4                     -- CONSTANT width = the zero-pad
#     (P3) Forall k in-bounds: 48 <= Result()[k] <= 57   -- each char an ASCII digit
#     (P4) (R[0]-48)*1000 + (R[1]-48)*100 + (R[2]-48)*10 + (R[3]-48) == year
#                                                 -- the 4 digits reconstruct year
#     (P5) Result()[0] == 48 + year // 1000       -- leading thousands digit, NOT dropped
#   The bug-delta (the discriminating content): a year BELOW 1000 must render with
#   its leading zeros retained (1 -> '0001', 999 -> '0999') rather than as its bare
#   significant digits. That delta lives in (P2) len==4 and (P5)/(P1) leading-digit.
#
# Read-only inputs: NONE. The sole parameter `year` is a plain `int` (value type,
# immutable; there is no Acc(year,1/2) and no heap input). The only owned heap is
# the freshly-built Result() held with FULL permission (Acc(list_pred(Result()))).
# The frame-mutation / Acc(...,1/2) class therefore DOES NOT APPLY here -- there is
# no caller-owned heap input an impl could overwrite to satisfy the postcondition
# vacuously. See 'assessment' in the structured return.
#
# Oracle grounding: four_field / thousands / hundreds / tens / units / digit are
# @Pure, but each is GROUNDED in the argument `year` (four_field fully unfolds to
# arithmetic on year). There is NO opaque @ContractOnly answer-key to echo: an impl
# that satisfies (P1) is literally computing the place-value digits of `year`, i.e.
# doing the real work. So the ungrounded-oracle-echo class has no wrong echo to
# build; the honest stand-in is a cheapest-correct positive control (pos-cheapest).
#
# Axioms: NONE consumed. The lone deep-model reference (four_field == '%04d' % year)
# is an A-reference validated by axiom_check.py (G-AX). We re-run that host-validated
# oracle in-container as the single axiom-lane probe so the A-reference is grounded
# in the REAL '%04d' operation the gold patch performs (not a regex over source).
from pathlib import Path

INSTANCE = "django__django-14373"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor (the gold render_year body). We swap exactly the
# text between `# impl-start\n` and `\n    # impl-end`, so the edit stays strictly
# inside render_year's impl region; every spec region is byte-identical => same_spec.
# ---------------------------------------------------------------------------

_IMPL = (
    "    # impl-start\n"
    "    result = []  # type: List[int]\n"
    "    result.append(digit(thousands(year)))\n"
    "    result.append(digit(hundreds(year)))\n"
    "    result.append(digit(tens(year)))\n"
    "    result.append(digit(units(year)))\n"
    "    Assert(ToSeq(result) == four_field(year))\n"
    "    return result\n"
    "    # impl-end"
)


def _impl(new_body: str) -> str:
    """Replace ONLY render_year's impl body, keeping the # impl-start / # impl-end
    markers so the region boundary (and thus the frozen spec) is untouched."""
    return _swap(_BASE, _IMPL, "    # impl-start\n" + new_body + "\n    # impl-end")


SPEC_TESTS = [

    # ----------------------------------------------------------------- soundness
    # POSITIVE CONTROL #1 (structurally different, fully CORRECT). The four
    # place-value digits are bound to typed locals FIRST (a local-variable reshape),
    # then appended in the same most-significant-first order. The keeping framing
    # Assert(ToSeq(result) == four_field(year)) is RETAINED (it is the trigger the
    # gold proof uses to close (P1); dropping it would fail the postcondition for a
    # PROOF reason, not a spec reason -- AVOID-bug #2). No fold/induction lemma is
    # needed: four_field is a direct 4-tuple PSeq(...), and forward-append of four
    # elements matches that constructor order exactly (so AVOID-bug #3 does not
    # apply). If this cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    d3 = digit(thousands(year))  # type: int\n"
            "    d2 = digit(hundreds(year))  # type: int\n"
            "    d1 = digit(tens(year))  # type: int\n"
            "    d0 = digit(units(year))  # type: int\n"
            "    result = []  # type: List[int]\n"
            "    result.append(d3)\n"
            "    result.append(d2)\n"
            "    result.append(d1)\n"
            "    result.append(d0)\n"
            "    Assert(ToSeq(result) == four_field(year))\n"
            "    return result"
        ),
        "rationale": "a correct local-variable-reshaped impl (digits bound to "
                     "typed locals, appended MS-first) must verify; the gold "
                     "framing Assert is kept so (P1) still closes. else SPEC-TOO-STRONG.",
    },

    # POSITIVE CONTROL #2 / cheapest-honest (grounded oracle stand-in). Since the
    # oracle four_field is GROUNDED in `year`, the cheapest correct impl just appends
    # the same digit(place(year)) values the spec computes -- which IS the real work.
    # This stands in for the ungrounded-oracle case (there is no wrong echo to build).
    # Inlines the place arithmetic explicitly to show the digits are a function of
    # the arg, keeping the framing Assert. Must verify.
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    result.append(digit(year // 1000))\n"
            "    result.append(digit((year // 100) % 10))\n"
            "    result.append(digit((year // 10) % 10))\n"
            "    result.append(digit(year % 10))\n"
            "    Assert(ToSeq(result) == four_field(year))\n"
            "    return result"
        ),
        "rationale": "grounded-oracle stand-in: the cheapest correct impl appends "
                     "digit(<place arithmetic on year>) directly, doing exactly the "
                     "real work the spec pins. must verify (no wrong echo exists).",
    },

    # ----------------------------------------------------------------- admissibility
    # A self-call caller that invokes render_year on an F2P-shaped in-domain input
    # (year == 1, the test_Y_format_year_before_1000 witness, and year == 999) and
    # asserts a postcondition consequence. The precondition 1 <= year <= 9999 must
    # admit these normal inputs; if the Requires cannot be established for a
    # legitimate datetime year => PRECOND-TOO-STRONG. The caller lives in the impl
    # region (spec untouched). The probe binds the call results to typed locals and
    # reads only postcondition facts the spec already guarantees.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    result.append(digit(thousands(year)))\n"
            "    result.append(digit(hundreds(year)))\n"
            "    result.append(digit(tens(year)))\n"
            "    result.append(digit(units(year)))\n"
            "    Assert(ToSeq(result) == four_field(year))\n"
            "    # admissibility probe: F2P-shaped sub-1000 years satisfy the\n"
            "    # precondition; the call sites verify and the post facts hold.\n"
            "    Assert(1 <= 1 and 1 <= 9999)\n"
                            "    Assert(1 <= 999 and 999 <= 9999)\n"
                            "    return result"
        ),
        "rationale": "the precondition must admit normal F2P-shaped datetime years "
                     "(year=1, year=999); the self-calls verify and (P2) len==4 / "
                     "(P5) leading-zero hold for them. else PRECOND-TOO-STRONG.",
    },

    # ----------------------------------------------------------------- uniqueness
    # ATTACK 1 (partial-domain, THE bug-delta = the pre-patch skeleton). Render the
    # year by its BARE significant digits, dropping most-significant leading zeros:
    # for a year >= 1000 this is the correct four chars, but a year < 1000 yields
    # FEWER than four characters. This is exactly model_prepatch.py's behaviour and
    # the bug the gold fix repairs. Must reject (on (P2) len==4 / (P1)).
    {
        "id": "weak-leading-zeros-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    started = False\n"
            "    d3 = thousands(year)  # type: int\n"
            "    if d3 > 0:\n"
            "        result.append(digit(d3))\n"
            "        started = True\n"
            "    d2 = hundreds(year)  # type: int\n"
            "    if started or d2 > 0:\n"
            "        result.append(digit(d2))\n"
            "        started = True\n"
            "    d1 = tens(year)  # type: int\n"
            "    if started or d1 > 0:\n"
            "        result.append(digit(d1))\n"
            "        started = True\n"
            "    d0 = units(year)  # type: int\n"
            "    result.append(digit(d0))\n"
            "    return result"
        ),
        "refinement": "this is the PRE-PATCH `return self.data.year` skeleton: the "
                      "bare integer's decimal rendering drops most-significant "
                      "leading zeros, so datetime(1,1,1).Y -> '1' and "
                      "datetime(999,1,1).Y -> '999'. The F2P "
                      "test_Y_format_year_before_1000 asserts '0001' and '0999' => "
                      "the faithful real patch FAILS the F2P; it does NOT resolve.",
        "rationale": "violates (P2) len(Result())==4 (a sub-1000 year yields 1-3 "
                     "chars) and (P1) ToSeq==four_field / (P5) leading-digit. The "
                     "rejection comes from the constant-width postcondition.",
    },

    # ATTACK 2 (partial-domain, wrong fill character). Pad to a constant FOUR-width
    # field but fill the leading positions with the ASCII SPACE (' ' = 32) instead
    # of the zero digit, only when the year is below 1000. len==4 is satisfied, but
    # the fill is not an ASCII decimal digit. This mimics a `'%4d' % year` (space-pad)
    # refinement instead of `'%04d'`. Must reject (on (P3) each-char-a-digit and (P5)
    # leading == 48 + year//1000, and (P4) reconstruction since 32 != 48).
    {
        "id": "weak-space-pad",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    d3 = thousands(year)  # type: int\n"
            "    if d3 > 0:\n"
            "        result.append(digit(d3))\n"
            "    else:\n"
            "        result.append(32)\n"
            "    result.append(digit(hundreds(year)))\n"
            "    result.append(digit(tens(year)))\n"
            "    result.append(digit(units(year)))\n"
            "    return result"
        ),
        "refinement": "this is the `'%4d' % year` (SPACE-pad) mistake instead of "
                      "`'%04d'` (ZERO-pad): datetime(1,1,1).Y -> '   1' and "
                      "datetime(999,1,1).Y -> ' 999'. The F2P asserts '0001'/'0999' "
                      "(literal zero chars) => the faithful real patch FAILS the "
                      "F2P; it does NOT resolve.",
        "rationale": "violates (P3) 48<=Result()[k]<=57 (32 is not a digit), (P5) "
                     "Result()[0]==48+year//1000 (32 != 48 for year<1000), and (P1)/"
                     "(P4). Rejection from the each-char-is-a-digit + leading-digit "
                     "postconditions.",
    },

    # ATTACK 3 (value double-mask: transposed digits). Produce a four-char field
    # with every position an ASCII digit and the SAME MULTISET of digits, but with
    # the tens and units transposed. A value-proxy that only checked "len==4, all
    # digits, and the multiset/sum reconstructs" could miss it -- but (P1) ToSeq ==
    # four_field pins the ORDER and (P4) the place-weighted reconstruction catches
    # the transposition (weights 10 vs 1 differ). Must reject.
    {
        "id": "weak-transpose-tens-units",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    result.append(digit(thousands(year)))\n"
            "    result.append(digit(hundreds(year)))\n"
            "    result.append(digit(units(year)))\n"
            "    result.append(digit(tens(year)))\n"
            "    return result"
        ),
        "refinement": "this transposes the tens and units digits (e.g. year 1234 -> "
                      "'1243', year 2021 -> '2012'). Real `'%04d' % year` never "
                      "reorders digits; the PASS_TO_PASS dateformat tests "
                      "(test_dateformat, test_date_formats) assert the exact rendered "
                      "year string => the faithful real patch FAILS those P2P tests "
                      "and does NOT resolve.",
        "rationale": "violates (P1) ToSeq(Result())==four_field(year) (order differs) "
                     "and (P4) place-weighted reconstruction (units/tens weights 1 "
                     "vs 10 differ unless tens==units). Rejection from the deep "
                     "place-value postcondition.",
    },

    # ATTACK 4 (partial-domain, units off-by-one on a sub-domain). Render correctly
    # except add 1 to the units digit when the units place is 0 (so the last digit
    # becomes '1' instead of '0'). Correct on every year NOT ending in 0; WRONG on
    # multiples of 10 (e.g. year 2020 -> '2021', year 10 -> '0011'). A cheap
    # supporting near-miss that still carries a real refinement. Must reject.
    {
        "id": "weak-units-plus-one-on-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    result.append(digit(thousands(year)))\n"
            "    result.append(digit(hundreds(year)))\n"
            "    result.append(digit(tens(year)))\n"
            "    u = units(year)  # type: int\n"
            "    if u == 0:\n"
            "        result.append(digit(1))\n"
            "    else:\n"
            "        result.append(digit(u))\n"
            "    return result"
        ),
        "refinement": "this corrupts the units digit for years ending in 0 "
                      "(datetime(2020,1,1).Y -> '2021', datetime(10,1,1).Y -> "
                      "'0011'). Real `'%04d' % 2020` is '2020'; the dateformat P2P "
                      "tests assert the exact year string => the faithful real patch "
                      "FAILS those P2P tests on any year ending in 0 and does NOT "
                      "resolve.",
        "rationale": "violates (P1) ToSeq==four_field and (P4) reconstruction for "
                     "every year whose units digit is 0 (Result()[3]==49 but "
                     "four_field gives 48). Rejection from the deep place-value + "
                     "reconstruction postconditions.",
    },

    # ATTACK 5 (partial-domain, five-char overflow for the largest sub-domain).
    # Append a spurious trailing zero digit only when the year is >= 1000, yielding
    # FIVE characters for four-digit years while sub-1000 years still get four. This
    # is the inverse of attack 1: correct length only on the low sub-domain. Must
    # reject (on (P2) len==4). Cheap supporting near-miss with a real refinement.
    {
        "id": "weak-five-chars-high",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    result.append(digit(thousands(year)))\n"
            "    result.append(digit(hundreds(year)))\n"
            "    result.append(digit(tens(year)))\n"
            "    result.append(digit(units(year)))\n"
            "    if thousands(year) > 0:\n"
            "        result.append(digit(0))\n"
            "    return result"
        ),
        "refinement": "this appends a spurious trailing '0' for four-digit years "
                      "(datetime(1999,1,1).Y -> '19990'). Real `'%04d' % 1999` is "
                      "'1999' (exactly four chars); the dateformat P2P tests "
                      "(test_dateformat asserts '1973' etc.) assert the exact "
                      "four-char year => the faithful real patch FAILS those P2P "
                      "tests on any four-digit year and does NOT resolve.",
        "rationale": "violates (P2) len(Result())==4 for every year >= 1000 (yields "
                     "5 chars). Rejection from the constant-width postcondition.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. NO @ContractOnly axioms are consumed in this bundle. The lone
# deep-model REFERENCE -- four_field(year) == the real `'%04d' % year` rendering
# the gold patch performs -- is an A-reference validated out-of-band by G-AX
# (axiom_check.py). We re-run that exact host-validated oracle in-container as a
# single axiom-soundness+containment probe so the A-reference is grounded in the
# REAL '%04d' operation (an actual run of the callee, NOT a regex over source --
# AVOID-bug #4). It reads no files (so no utf-8 codec concern -- AVOID-bug #5) and
# is fully self-contained (the runner mounts only this probe -- AVOID-bug #6).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-four-field-vs-printf",
        "axiom": "four_field",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        # The probe is the bundle's host-validated G-AX oracle, embedded verbatim.
        # It EXECUTES the real `'%04d' % year` (the very operation the gold patch
        # calls) and asserts code-point equality with the deep model four_field over
        # an EXHAUSTIVE sweep of the full supported datetime year range 1..9999 plus
        # the explicit F2P boundary witnesses (1->'0001', 999->'0999', 476, 42, 4,
        # 1000, 1999, 9999, 10, 100). Exits 0 iff every observation matches.
        #
        # Containment: the model's Requires is 1 <= year <= 9999 and the deep model's
        # four_field Requires is 0 <= year <= 9999, so EVERY caller-reachable year is
        # inside the reference domain (1..9999 is a subset of 0..9999); the exhaustive
        # 1..9999 sweep covers exactly the caller-reachable inputs. Covering 0 too
        # (which the caller never reaches) is sound, not a defect (float-vs-int rule).
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "axiom-soundness + containment: the deep model four_field must "
                     "equal the REAL `'%04d' % year` on every year the model's "
                     "Requires (1..9999) admits; the exhaustive 1..9999 sweep runs "
                     "the real callee and asserts code-point equality. A mismatch => "
                     "AXIOM-UNSOUND (the A-reference would be a wrong deep model). "
                     "Every caller-reachable year lies in four_field's 0..9999 "
                     "domain, so there is no AXIOM-TOO-WEAK-FOR-CALLER gap.",
    },
]
