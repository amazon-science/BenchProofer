"""PBT manifest for django__django-11848.

Instance under attack: `expand_two_digit_year(two_digit_year, reference_year)` —
the two-digit legacy-year expansion the gold patch installs in
`django.utils.http.parse_http_date`. Both parameters are bare scalar `int`s; the
whole operation is exact integer arithmetic. There is NO read-only object/pointer
input (no `Acc(x, 1/2)`), so the FRAME-MUTATION class does not apply here — there
is nothing to overwrite. See `assessment` in the returned verdict.

The postcondition's load-bearing clause is

    Ensures(Result() == resolved_year(two_digit_year, reference_year))

where `resolved_year` is a @Pure helper that is FULLY GROUNDED in the arguments
(only `%`, `+`, `-`, and one comparison on the two int inputs). It is not an
opaque answer-key oracle: an impl that returns `resolved_year(...)` is literally
doing the modeled arithmetic, so there is no "wrong echo". Per directive 2 the
honest substitute is a cheapest-grounded positive control (`pos-cheapest`).

Cases are built by REGION-SURGERY: every variant is `model.py` with ONLY the text
between `# impl-start` and `# impl-end` swapped, so `same_spec` holds by
construction (the frozen spec/pure/pre/post regions are never touched).
"""
from pathlib import Path

INSTANCE = "django__django-11848"
FLOAT_ENCODING = None  # meta.json float_encoding is null; computation is exact int

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen gold impl region (verbatim from model.py, between the markers).
_GOLD_IMPL = """\
    base = reference_year - (reference_year % 100)
    if two_digit_year - (reference_year % 100) > 50:
        # More than fifty years ahead: roll back to the previous century.
        result = two_digit_year + base - 100
    else:
        result = two_digit_year + base
    return result"""


def _impl(body: str) -> str:
    """Return full model source with the impl region body replaced by `body`."""
    return _swap(_BASE, _GOLD_IMPL, body)


# --------------------------------------------------------------------------- #
# SPEC LANE                                                                    #
# --------------------------------------------------------------------------- #

SPEC_TESTS = [

    # ----- POSITIVE CONTROLS (soundness): correct impls MUST verify ---------- #

    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Cheapest grounded impl: return the deep model directly. Since\n"
            "    # `resolved_year` is fully unfolded in the two int args, this IS\n"
            "    # the modeled arithmetic (no opaque oracle to echo). Must verify\n"
            "    # (else the postcondition is unsatisfiable => SPEC-TOO-STRONG).\n"
            "    result = resolved_year(two_digit_year, reference_year)\n"
            "    return result"
        ),
        "rationale": (
            "The oracle `resolved_year` is grounded in the inputs (fully unfolded "
            "% / + / - on the two ints), so the honest cheapest impl returns it "
            "directly. It must verify; if it could not, the Ensures would be "
            "unsatisfiable (SPEC-TOO-STRONG). Doubles as the grounded positive "
            "control mandated by directive 2."
        ),
    },

    {
        "id": "pos-reshaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Structurally-different but CORRECT: hoist `c = ref % 100`,\n"
            "    # test the SAME-CENTURY case first via a negated guard, and\n"
            "    # compute the century start inline. Same arithmetic, reshaped\n"
            "    # control flow + extra locals. Keeps the gold proof valid (no\n"
            "    # loop, no induction lemma needed).\n"
            "    c = reference_year % 100\n"
            "    base = reference_year - c\n"
            "    if two_digit_year - c <= 50:\n"
            "        # Within fifty years ahead: stay in the reference century.\n"
            "        result = two_digit_year + base\n"
            "    else:\n"
            "        result = two_digit_year + base - 100\n"
            "    return result"
        ),
        "rationale": (
            "A correct impl with reordered branches (negated guard, else-first), "
            "an extra hoisted local `c`, and inline century arithmetic must "
            "verify. No loop / fold, so no induction lemma is needed (avoids the "
            "pilot positive-control proof-gap traps). If it could not verify, the "
            "postcondition would be SPEC-TOO-STRONG."
        ),
    },

    # ----- ADMISSIBILITY: the precondition admits an F2P-shaped input -------- #

    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # Admissibility: the Requires (0<=year<100, ref>=1000) must admit\n"
            "    # the F2P-pinned shapes. We compute the gold result, then ASSERT\n"
            "    # that on the pinned inputs it equals the value the F2P test pins\n"
            "    # (utcnow=2019,year=69 -> 2069; utcnow=2020,year=70 -> 2070;\n"
            "    #  utcnow=2048,year=99 -> 1999). A provable assertion under a\n"
            "    # legitimate in-domain input => PRECOND is not too strong.\n"
            "    base = reference_year - (reference_year % 100)\n"
            "    if two_digit_year - (reference_year % 100) > 50:\n"
            "        result = two_digit_year + base - 100\n"
            "    else:\n"
            "        result = two_digit_year + base\n"
            "    Assert(Implies(two_digit_year == 69 and reference_year == 2019,\n"
            "                   result == 2069))\n"
            "    Assert(Implies(two_digit_year == 70 and reference_year == 2020,\n"
            "                   result == 2070))\n"
            "    Assert(Implies(two_digit_year == 99 and reference_year == 2048,\n"
            "                   result == 1999))\n"
            "    return result"
        ),
        "rationale": (
            "An F2P-shaped input (two-digit year in 0..99, four-digit reference "
            "year) is admitted by the precondition and the gold computation "
            "produces exactly the value each F2P case pins. The Asserts verify "
            "only because the Requires domain is non-vacuous and contains these "
            "shapes; failure would mean PRECOND-TOO-STRONG."
        ),
    },

    # ----- UNIQUENESS / SPEC-TOO-WEAK: wrong impls MUST be rejected ---------- #

    {
        "id": "weak-prepatch-fixed-cutoff",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # The PRE-PATCH (buggy) skeleton: a FIXED cut-off at 70 that\n"
            "    # ignores the reference year entirely (0..69 -> 2000s, 70..99 ->\n"
            "    # 1900s). This is exactly the behaviour the gold patch removes.\n"
            "    if two_digit_year < 70:\n"
            "        result = two_digit_year + 2000\n"
            "    else:\n"
            "        result = two_digit_year + 1900\n"
            "    return result"
        ),
        "refinement": (
            "This is the verbatim pre-patch logic (G-DIFF). Its faithful real "
            "patch is the unpatched `parse_http_date`, which the F2P tests fail. "
            "Decisive break: test_parsing_rfc850 at utcnow=2020 pins 'Wednesday, "
            "31-Dec-70' -> datetime(2070,...), but the fixed cut-off (year 70 -> "
            "+1900) gives 1970. So its faithful patch does NOT resolve "
            "test_parsing_rfc850."
        ),
        "rationale": (
            "Rejected by Ensures clause 1 (Result()==resolved_year): for any "
            "reference_year with last two digits != ~20, the fixed cut-off "
            "disagrees with the reference-relative expansion (e.g. ref=2020, "
            "year=70: spec 2070, cut-off 1970). model_prepatch.py confirms this "
            "fails at the resolved_year clause."
        ),
    },

    {
        "id": "weak-boundary-ge50",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Off-by-one at the rollback THRESHOLD: uses `>= 50` instead of\n"
            "    # `> 50`. Correct everywhere except the exact boundary input\n"
            "    # `two_digit_year - reference_year%100 == 50`, where it wrongly\n"
            "    # rolls back one century.\n"
            "    base = reference_year - (reference_year % 100)\n"
            "    if two_digit_year - (reference_year % 100) >= 50:\n"
            "        result = two_digit_year + base - 100\n"
            "    else:\n"
            "        result = two_digit_year + base\n"
            "    return result"
        ),
        "refinement": (
            "Diverges only at `two_digit_year - ref%100 == 50`. The F2P case "
            "(utcnow=2019, 'Tuesday, 31-Dec-69') has 69 - 19 == 50 and pins "
            "datetime(2069,...): gold => 69+2000 = 2069, this rival => "
            "69+2000-100 = 1969. So its faithful real patch fails "
            "test_parsing_rfc850 and does NOT resolve."
        ),
        "rationale": (
            "Rejected by Ensures clause 1: at the boundary `t - ref%100 == 50` "
            "the spec keeps the reference century (resolved_year uses strict "
            "`> 50`), but this impl rolls back, giving Result() 100 less than "
            "resolved_year(...)."
        ),
    },

    {
        "id": "weak-threshold-49",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # SUPPORTING near-miss: threshold `> 49` (rolls back one input\n"
            "    # too early). Diverges at `t - ref%100 == 50`, same boundary as\n"
            "    # the >=50 rival but reached from the other side of the\n"
            "    # comparison family.\n"
            "    base = reference_year - (reference_year % 100)\n"
            "    if two_digit_year - (reference_year % 100) > 49:\n"
            "        result = two_digit_year + base - 100\n"
            "    else:\n"
            "        result = two_digit_year + base\n"
            "    return result"
        ),
        "refinement": (
            "Identical observable effect to weak-boundary-ge50 (rolls back at "
            "`t-ref%100 == 50`). Faithful patch fails the same F2P case "
            "(utcnow=2019, year=69 -> gold 2069, rival 1969); does NOT resolve. "
            "Cheap supporting case for the threshold family."
        ),
        "rationale": (
            "Rejected by Ensures clause 1 at the boundary input "
            "`t - ref%100 == 50`."
        ),
    },

    {
        "id": "weak-no-rollback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Drops the future-rollback rule entirely: always stays in the\n"
            "    # reference century. Correct on the near-half of the domain but\n"
            "    # wrong on every input that is >50 years ahead.\n"
            "    base = reference_year - (reference_year % 100)\n"
            "    result = two_digit_year + base\n"
            "    return result"
        ),
        "refinement": (
            "Never rolls back. The F2P case (utcnow=2019, 'Tuesday, 10-Nov-70') "
            "pins datetime(1970,...): 70 - 19 == 51 > 50, so gold rolls back to "
            "1970, but this rival gives 70+2000 = 2070. Its faithful patch fails "
            "test_parsing_rfc850 and does NOT resolve."
        ),
        "rationale": (
            "Rejected by Ensures clause 1 on the future subdomain (and clause 3 "
            "`Result()-reference_year <= 50`): for `t - ref%100 > 50`, "
            "resolved_year subtracts 100 but this impl does not, so Result() is "
            "100 too large and exceeds the +50 bound."
        ),
    },

    {
        "id": "weak-century-noclear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Mis-computes the century start: forgets to clear the reference\n"
            "    # year's last two digits (uses `reference_year` itself as the\n"
            "    # base instead of `reference_year - reference_year%100`). The\n"
            "    # last-two-digits postcondition then fails for most inputs.\n"
            "    base = reference_year\n"
            "    if two_digit_year - (reference_year % 100) > 50:\n"
            "        result = two_digit_year + base - 100\n"
            "    else:\n"
            "        result = two_digit_year + base\n"
            "    return result"
        ),
        "refinement": (
            "Uses ref (not ref with its last two digits cleared) as the century "
            "base, so Result() = year + ref (+/-100) carries ref's own last two "
            "digits added in. For utcnow=2019, year=94 ('Sunday, 06-Nov-94', "
            "94-19=75>50 so the rollback branch): gold pins 1994 but this rival "
            "gives 94+2019-100 = 2013. Faithful patch fails test_parsing_rfc850 "
            "(and yields a non-1994 year); does NOT resolve."
        ),
        "rationale": (
            "Rejected by Ensures clause 2 (Result() % 100 == two_digit_year): "
            "adding the full reference_year instead of its century start makes "
            "the last two digits wrong whenever ref%100 != 0, and clause 1 also "
            "fails."
        ),
    },
]


# --------------------------------------------------------------------------- #
# AXIOM LANE                                                                   #
# --------------------------------------------------------------------------- #
# No @ContractOnly axioms are consumed (meta.axioms == []). The bundle DOES
# carry one A-reference deep model — `resolved_year` / `century_start` — which
# the refinement validates `== the real patch arithmetic` (G-AX). We probe that
# A-reference on both fronts the plan §2.4 requires:
#   * axiom-soundness: re-run the REAL patch arithmetic and assert the deep model
#     agrees on every caller-reachable input, plus the provenance of the
#     reference year (datetime.utcnow().year is a real four-digit int);
#   * axiom-containment: every callee-input the MODEL can reach (derived from the
#     model's Requires: 0<=year<100, ref>=1000) lies inside the domain over
#     which the deep model is defined/validated.
# Both probes are stdlib-only (datetime) and self-contained; they reuse the
# verbatim arithmetic from axiom_check.py.

_AX_SOUNDNESS_PROBE = r'''
import datetime, random, sys

# --- deep model (model.py @Pure resolved_year / century_start, lock-step) ---
def century_start(reference_year):
    return reference_year - (reference_year % 100)

def resolved_year(two_digit_year, reference_year):
    if two_digit_year - (reference_year % 100) > 50:
        return two_digit_year + century_start(reference_year) - 100
    return two_digit_year + century_start(reference_year)

# --- the REAL patch arithmetic (verbatim from django/utils/http.py post-patch)
def real_expansion(two_digit_year, reference_year):
    year = two_digit_year
    current_year = reference_year
    current_century = current_year - (current_year % 100)
    if year - (current_year % 100) > 50:
        year += current_century - 100
    else:
        year += current_century
    return year

def check(t, ref):
    obs = real_expansion(t, ref)        # real callee arithmetic
    exp = resolved_year(t, ref)         # deep model
    assert obs == exp, (
        "A-reference UNSOUND at (year=%d, ref=%d): real=%d deep=%d"
        % (t, ref, obs, exp))
    # the three auxiliary postconditions must also hold on the real value
    assert obs % 100 == t, "last-two-digits violated at (%d,%d): %d" % (t, ref, obs)
    assert obs - ref <= 50, "+50-bound violated at (%d,%d): %d" % (t, ref, obs)
    assert ref - obs < 150, "recency violated at (%d,%d): %d" % (t, ref, obs)

# --- provenance: reference_year == datetime.datetime.utcnow().year ----------
now = datetime.datetime.utcnow()
ref_now = now.year
assert isinstance(ref_now, int), "utcnow().year is not int: %r" % (ref_now,)
assert ref_now >= 1000, "utcnow().year not four-digit: %r" % (ref_now,)
assert ref_now == now.year, "year attr is not the calendar year"

# --- exhaustive over the full two-digit domain x boundary reference years ---
refs = [1000, 1900, 1970, 1999, 2000, 2019, 2020, 2048, 2069, 2099,
        2100, 2101, 2150, 2999, 9999, ref_now,
        1100, 1150, 1199, 2049, 2050, 2051]
checked = 0
for ref in refs:
    for t in range(0, 100):
        check(t, ref); checked += 1

# --- the seven F2P-pinned (mocked-utcnow) cases, explicitly ----------------
pinned = [(2019,69,2069),(2019,70,1970),(2019,94,1994),
          (2020,70,2070),(2020,71,1971),(2048,0,2000),(2048,99,1999)]
for ref, t, expect_full in pinned:
    got = resolved_year(t, ref)
    assert got == expect_full, "pinned (%d,%d)=%d expected %d" % (t, ref, got, expect_full)
    check(t, ref)

# --- randomized fuzz over the precondition domain --------------------------
rng = random.Random(11848)
for _ in range(200000):
    ref = rng.randint(1000, 9999)
    t = rng.randint(0, 99)
    check(t, ref); checked += 1

print("AX-SOUND OK: resolved_year deep model == real patch arithmetic on %d "
      "boundary+exhaustive+fuzz inputs; 7 F2P-pinned cases match; "
      "utcnow().year provenance confirmed (== %d)" % (checked, ref_now))
sys.exit(0)
'''


_AX_CONTAINMENT_PROBE = r'''
import sys

# The deep model `resolved_year` / `century_start` is total integer arithmetic;
# it is "defined+validated" over the domain the MODEL can reach. We enumerate
# EXACTLY the inputs the caller (expand_two_digit_year) can pass, derived from
# its precondition:
#     Requires(0 <= two_digit_year and two_digit_year < 100)
#     Requires(reference_year >= 1000)
# and assert each lies inside the deep model's only stated requirement
#     resolved_year.Requires(reference_year >= 0)
# (i.e. ref >= 1000 ==> ref >= 0, trivially; year unconstrained beyond int).
# Covering MORE (ref >= 0 vs the caller's ref >= 1000) is SOUND, not a defect.

def deep_model_domain_ok(t, ref):
    # the single Requires of the @Pure resolved_year
    return ref >= 0

# Enumerate the caller-reachable boundary inputs exhaustively over the two-digit
# axis and across reference-year boundaries (lowest admissible 1000, century
# edges, and large) -- every one must be inside resolved_year's domain.
caller_refs = [1000, 1001, 1099, 1100, 1999, 2000, 2019, 2020, 2048,
               2099, 2100, 5000, 9998, 9999]
checked = 0
out_of_domain = []
for ref in caller_refs:
    assert ref >= 1000, "test bug: ref %d violates caller Requires" % ref
    for t in range(0, 100):             # the full caller two-digit domain
        assert 0 <= t < 100, "test bug: t %d violates caller Requires" % t
        if not deep_model_domain_ok(t, ref):
            out_of_domain.append((t, ref))
        checked += 1

assert not out_of_domain, (
    "AXIOM-TOO-WEAK-FOR-CALLER: caller-reachable inputs outside the deep "
    "model domain: %r" % (out_of_domain[:10],))

# Containment argument in closed form: caller guarantees ref >= 1000 >= 0, which
# satisfies resolved_year's `reference_year >= 0`; two_digit_year is an
# unconstrained int in the deep model, so 0..99 is trivially inside. No
# caller-reachable input escapes the deep model's domain.
print("AX-CONTAIN OK: all %d caller-reachable (year in 0..99, ref>=1000) inputs "
      "lie inside resolved_year's domain (ref>=0); containment holds (caller "
      "ref>=1000 is a strict subset of the modeled ref>=0)." % checked)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-resolved_year",
        "axiom": "resolved_year (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": (
            "The deep model `resolved_year`/`century_start` is validated `== the "
            "real patch arithmetic` (G-AX). The probe re-runs the verbatim "
            "post-patch arithmetic over the full two-digit domain x boundary "
            "reference years + 200k fuzz + the 7 F2P-pinned cases, asserts the "
            "deep model agrees and the three auxiliary postconditions hold on the "
            "real value, and confirms utcnow().year is a real four-digit int. Any "
            "disagreement => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-contain-resolved_year",
        "axiom": "resolved_year (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": (
            "Every callee-input the model can reach (year in 0..99, "
            "reference_year >= 1000, from expand_two_digit_year's Requires) lies "
            "inside resolved_year's domain (reference_year >= 0). The caller's "
            "ref>=1000 is a strict subset of the modeled ref>=0, so containment "
            "holds; a reachable input outside that domain would be "
            "AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
