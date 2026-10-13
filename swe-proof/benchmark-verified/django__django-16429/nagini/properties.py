"""properties.py — PBT falsification battery for django__django-16429.

NOT a Nagini module; a record of adversarially-reasoned cases. The runner
(swebench_nagini.pbt) writes each SPEC_TESTS[*]["module"] to a temp file, runs
Nagini verify on the HOST and checks markers.same_spec against the frozen
model.py; it runs each AXIOM_TESTS[*]["probe"] in the instance Docker image.

DEFENDED SURFACE (reasoned from model.py, not a corruption template)
--------------------------------------------------------------------
`pivot_remaining(d, now, pivot_year, pivot_month, pivot_day) ->
Tuple[Moment, int]` builds the intermediate reference moment ("pivot") that the
source moment `d` is advanced to, measures the leftover span via the deep
A-reference `well_defined_diff(now, pivot)`, and returns BOTH. The reference's
load-bearing content is (1) its DOMAIN guard
`Requires(same_disposition(now.tz, pivot.tz))` (the real datetime subtraction is
defined iff both operands share an aware/naive disposition) and (2) its VALUE
claim `Ensures(Result() == moment_span(now, pivot))` — the abstract ordered span
of exactly that operand pair, in that order.

Read-only inputs: EVERY field of `d` is `Acc(d.*, 1/2)` and `now.tz` is
`Acc(now.tz, 1/2)` — strictly read-only. => FRAME-MUTATION is MANDATORY.

Load-bearing postcondition clauses (the discriminators that make verify⇒resolve):
  * Result()[0].year/month/day == pivot_year/pivot_month/pivot_day  (the pivot
    is advanced to the SUPPLIED calendar position — pins the rendered span)
  * Result()[0].hour/minute/second == d.hour/d.minute/d.second   (clock carried)
  * Result()[0].tz is d.tz                                (disposition carried)
  * Result()[1] == moment_span(now, Result()[0])          (the measured span is
    the ordered difference of the current moment and the constructed pivot —
    an operand swap, a self-difference, or dropping the measurement entirely
    all fail this clause, since moment_span is uninterpreted and ordered)
  * the well_defined_diff(now, pivot) call is provable ONLY because pivot
    carries d.tz and now agrees with d (precondition same_disposition).

moment_span is an ABSTRACT (uninterpreted) pure function, so the only way to
obtain a value provably equal to moment_span(now, pivot) is to measure exactly
that ordered pair; a rival cannot conjure the value from constants. Echoing
moment_span(now, pivot) directly refines to the very same ordered real
difference, i.e. a correct patch — not a break.
"""
from pathlib import Path

INSTANCE = "django__django-16429"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact, unique impl region of model.py (between # impl-start / # impl-end).
_GOLD_IMPL = """    pivot = Moment(
        pivot_year,
        pivot_month,
        pivot_day,
        d.hour,
        d.minute,
        d.second,
        d.tz,
    )
    # The leftover span: requires now and pivot share a disposition. This call
    # is provable only because pivot carries d.tz and now agrees with d; it
    # measures the ordered difference of the current moment and the reference
    # moment, which is returned alongside the constructed reference moment.
    remaining = well_defined_diff(now, pivot)
    return pivot, remaining"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _with_impl(new_impl):
    """Replace ONLY the gold impl body (inside impl-start/impl-end) — the frozen
    spec (axioms/pure/pre/post-conditions + signatures) is never touched, so
    same_spec is guaranteed."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# Sanity: the gold impl region must be present verbatim and unique.
assert _GOLD_IMPL in _BASE and _BASE.count(_GOLD_IMPL) == 1, "gold impl drift"


# --------------------------------------------------------------------------- #
# SPEC LANE
# --------------------------------------------------------------------------- #
SPEC_TESTS = [

    # ----- 1. FRAME-MUTATION (MANDATORY: d is read-only at Acc(.,1/2)) ------ #
    # A rival that WRITES the read-only source moment `d` to satisfy a
    # postcondition cannot: it only holds Acc(d.hour, 1/2). Writing d.hour
    # requires FULL permission. This MUST reject for insufficient permission,
    # NOT for a value mismatch. Gold invariants are kept verbatim so the
    # rejection is attributable to the write, not to a contract change.
    {
        "id": "frame-mut-write-d-clock",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    d.hour = pivot_year\n"
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        d.tz,\n"
            "    )\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "datetime.datetime is immutable, but more to the point a faithful "
            "patch that mutated the source moment `d` in place would corrupt "
            "the caller's own `d` (timesince reads d.year/d.month/.. AFTER the "
            "pivot branch to compute the rendered string and the avoid_wrapping "
            "logic), changing the elapsed-time output for every F2P/P2P input — "
            "it would NOT resolve. The model forbids it structurally: d is "
            "read-only (Acc(.,1/2))."
        ),
        "rationale": (
            "Permission system: writing d.hour needs full permission but only "
            "Acc(d.hour, 1/2) is held; rejects for INSUFFICIENT PERMISSION."
        ),
    },
    {
        # second frame-mutation: write the disposition field d.tz (the field
        # the bug lives in). Same insufficient-permission rejection.
        "id": "frame-mut-write-d-tz",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    d.tz = now.tz\n"
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        d.tz,\n"
            "    )\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "Overwriting d.tz to force same_disposition vacuously: a real patch "
            "that reassigned the source's tzinfo would change which branch "
            "timesince's caller takes for naive sources and corrupt the rendered "
            "result; it would not resolve. Structurally forbidden: d.tz is "
            "Acc(d.tz, 1/2) read-only."
        ),
        "rationale": (
            "Permission system: writing d.tz needs full permission; only "
            "Acc(d.tz, 1/2) held -> INSUFFICIENT PERMISSION."
        ),
    },

    # ----- 2. PARTIAL-DOMAIN: naive pivot (the model_prepatch shape) -------- #
    # Build the pivot with tz=None (drop the source's disposition). Correct
    # ONLY when d is offset-naive; diverges on every offset-aware source. Fails
    # BOTH the disposition postcondition Result().tz is d.tz AND the
    # well_defined_diff precondition same_disposition(now.tz, pivot.tz). This is
    # the actual bug the gold patch fixes.
    {
        "id": "partial-naive-pivot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    naive = None  # type: Optional[int]\n"
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        naive,\n"
            "    )\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "This IS the pre-patch construction (pivot built without "
            "tzinfo=d.tzinfo). For an offset-aware source (the F2P "
            "TZAwareTimesinceTests with USE_TZ=True, e.g. test_thousand_years_ago "
            "/ test_depth) `now` is aware but the pivot is naive, so "
            "`(now - pivot).total_seconds()` raises "
            "TypeError: can't subtract offset-naive and offset-aware datetimes — "
            "the crash the patch fixes. It does NOT resolve."
        ),
        "rationale": (
            "Postcondition Result().tz is d.tz FAILS when d.tz is a non-None "
            "offset (naive pivot has tz None); AND the well_defined_diff "
            "precondition same_disposition(now.tz, pivot.tz) is unprovable for "
            "an aware now vs naive pivot. Either witness rejects."
        ),
    },

    # ----- 3. PARTIAL-DOMAIN: un-advanced pivot (the prior atk_7) ----------- #
    # Build the pivot at the SOURCE calendar position (d.year/d.month/d.day)
    # instead of the supplied advanced position. Carries d.tz so the
    # disposition guard passes — but renders the WRONG leftover span. This is
    # the hole the G-EQ DEFECT-1 refinement closed by pinning Result().year etc.
    {
        "id": "partial-unadvanced-pivot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    pivot = Moment(\n"
            "        d.year,\n"
            "        d.month,\n"
            "        d.day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        d.tz,\n"
            "    )\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "A pivot built at the un-advanced source calendar position "
            "(d.year/d.month/d.day) instead of (pivot_year/pivot_month/"
            "pivot_day) measures the WHOLE span instead of the leftover span "
            "beyond the advanced years/months. timesince would render the wrong "
            "number — test_thousand_years_ago expects '1000 years' but the "
            "leftover beyond 1000 advanced years is ~0; it does NOT resolve."
        ),
        "rationale": (
            "Postcondition Result().year == pivot_year (and .month/.day) FAILS: "
            "the pivot carries d.year, which is not pivot_year in the "
            "years-or-months branch. This is exactly the DEFECT-1 hole the "
            "full-field pinning closes (G-EQ note)."
        ),
    },

    # ----- 4. PARTIAL-DOMAIN: zeroed clock fields (the prior atk_4) --------- #
    # Carry the advanced calendar position and d.tz, but zero the clock fields.
    # Correct only on the midnight sub-domain; fails Result().hour == d.hour.
    {
        "id": "partial-zeroed-clock",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        0,\n"
            "        0,\n"
            "        0,\n"
            "        d.tz,\n"
            "    )\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "A pivot with zeroed clock fields drops d.hour/d.minute/d.second, "
            "shifting the leftover span by up to ~24h. For any source whose "
            "clock is not midnight the rendered residual minutes/seconds differ "
            "(the P2P depth/units tests observe sub-day components), so it does "
            "NOT resolve; correct only on the midnight sub-domain."
        ),
        "rationale": (
            "Postcondition Result().hour == d.hour FAILS whenever d.hour != 0 "
            "(likewise minute/second). Partial-domain rejection from the clock "
            "pins added in the DEFECT-1 refinement."
        ),
    },

    # ----- 5. CONTROL-FLOW-EFFECT: drop the span measurement ---------------- #
    # An impl that DROPS the well_defined_diff(now, pivot) call and returns a
    # constant in place of the measured span. The behaviour consumes the span
    # downstream to render the residual string, so omitting the measurement is
    # observable: the second Result component cannot be shown equal to the
    # abstract ordered span moment_span(now, pivot) (uninterpreted — no
    # constant can be proven equal to it). MUST reject.
    {
        "id": "drop-span-measurement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        d.tz,\n"
            "    )\n"
            "    return pivot, 0"
        ),
        "refinement": (
            "A faithful patch that drops the leftover-span assignment leaves "
            "the residual-span consumer downstream with no measured value (a "
            "NameError / wrong constant residual), so the rendered elapsed-time "
            "string is wrong for every years-or-months input — it does NOT "
            "resolve. The span postcondition rejects it structurally."
        ),
        "rationale": (
            "Postcondition Result()[1] == moment_span(now, Result()[0]) FAILS: "
            "moment_span is uninterpreted, so the constant 0 cannot be proven "
            "equal to it; only actually measuring the ordered pair discharges "
            "the clause."
        ),
    },

    # ----- 5b. OPERAND-ORDER: swapped difference ---------------------------- #
    # An impl that measures the difference with the operands REVERSED (the
    # reference moment minus the current moment). The domain guard is symmetric
    # so the call itself is provable — but the measured value is
    # moment_span(pivot, now), which is NOT provably moment_span(now, pivot)
    # (moment_span is uninterpreted and ordered). MUST reject.
    {
        "id": "swapped-span-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        d.tz,\n"
            "    )\n"
            "    remaining = well_defined_diff(pivot, now)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "A faithful patch measuring the reversed difference sign-flips the "
            "residual span, making every non-zero leftover negative, so the "
            "rendered partial units are wrong for every years-or-months input — "
            "it does NOT resolve. The ordered span postcondition rejects it."
        ),
        "rationale": (
            "well_defined_diff(pivot, now) Ensures its result equals "
            "moment_span(pivot, now); the postcondition demands "
            "moment_span(now, Result()[0]) — an uninterpreted function of the "
            "ORDERED pair, so the swapped value is not provably equal. Rejects."
        ),
    },

    # ----- 6. POSITIVE CONTROL: local-variable reshape (structurally diff) -- #
    # Bind each constructor argument to a typed local first, then construct from
    # the locals and call the guard. Same proof obligations, different shape.
    # Keeps the gold proof valid (no reordering that needs a lemma).
    {
        "id": "posctl-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    py = pivot_year   # type: int\n"
            "    pm = pivot_month  # type: int\n"
            "    pd = pivot_day    # type: int\n"
            "    h = d.hour        # type: int\n"
            "    mi = d.minute     # type: int\n"
            "    s = d.second      # type: int\n"
            "    z = d.tz          # type: Optional[int]\n"
            "    pivot = Moment(py, pm, pd, h, mi, s, z)\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "Behaviourally identical to gold (same constructor arguments, just "
            "named into locals first) — a faithful refinement, MUST verify. If "
            "it failed, the spec would be too strong for an equivalent shape."
        ),
        "rationale": (
            "Every pinned Result field maps to the same value via the locals; "
            "the disposition guard is still discharged (z is d.tz, now agrees "
            "with d). Structurally different, correct => verifies."
        ),
    },

    # ----- 7. ADMISSIBILITY: precondition is non-vacuously satisfiable ------ #
    # Inside the impl region (so the spec view is untouched and same_spec holds),
    # construct two F2P-shaped witnesses — an offset-AWARE pair (mirroring the
    # new TZAwareTimesinceTests USE_TZ=True / make_aware source) and an
    # offset-NAIVE pair (the original TimesinceTests, USE_TZ default) — and
    # Assert that each satisfies the precondition predicate
    # same_disposition(now.tz, d.tz). If a witness cannot be shown to satisfy the
    # Requires for a legitimate input, the precondition is too strong / vacuous
    # (PRECOND-TOO-STRONG). The gold pivot is then built and returned unchanged.
    {
        "id": "admiss-disposition-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(
            "    # AWARE F2P witness (make_aware source, USE_TZ=True): an aware\n"
            "    # source with a matching aware current moment satisfies Requires.\n"
            "    aware_src = Moment(2007, 8, 14, 13, 46, 0, 330)\n"
            "    aware_now = Moment(2017, 8, 14, 13, 46, 0, 0)\n"
            "    Assert(same_disposition(aware_now.tz, aware_src.tz))\n"
            "    Assert(is_offset_aware(aware_src.tz))\n"
            "    # NAIVE F2P witness (original TimesinceTests, USE_TZ default).\n"
            "    naive = None  # type: Optional[int]\n"
            "    naive_src = Moment(2007, 8, 14, 13, 46, 0, naive)\n"
            "    naive_now = Moment(2017, 8, 14, 13, 46, 0, naive)\n"
            "    Assert(same_disposition(naive_now.tz, naive_src.tz))\n"
            "    Assert(not is_offset_aware(naive_src.tz))\n"
            "    pivot = Moment(\n"
            "        pivot_year,\n"
            "        pivot_month,\n"
            "        pivot_day,\n"
            "        d.hour,\n"
            "        d.minute,\n"
            "        d.second,\n"
            "        d.tz,\n"
            "    )\n"
            "    remaining = well_defined_diff(now, pivot)\n"
            "    return pivot, remaining"
        ),
        "refinement": (
            "Admissibility, not a break: shows the precondition predicate "
            "same_disposition(now.tz, d.tz) is non-vacuously satisfiable for "
            "BOTH a normal aware input (TZAwareTimesinceTests, the F2P-adding "
            "class) and a normal naive input (original TimesinceTests). If "
            "these Asserts could not be discharged the precondition would reject "
            "a legitimate input (PRECOND-TOO-STRONG)."
        ),
        "rationale": (
            "same_disposition(330's-class, 0's-class)=True (both aware) and "
            "same_disposition(None, None)=True (both naive); both asserts hold "
            "and the gold pivot still verifies. The spec view elides the impl "
            "region so same_spec is preserved."
        ),
    },
]


# --------------------------------------------------------------------------- #
# AXIOM LANE  (no @ContractOnly consumed axiom; ONE A-reference deep model:
# well_defined_diff <-> datetime subtraction definedness. Validate it against
# the REAL stdlib datetime callee in-container, and check caller-domain
# containment.)
# --------------------------------------------------------------------------- #

# Reuse/strengthen the bundle's host-side soundness check by embedding its
# logic directly into the in-container probe (the runner mounts ONLY the probe;
# axiom_check.py is NOT in the container — pilot-bug #6). stdlib `datetime`
# only; open() unused so no codec concern (pilot-bug #5 N/A here).

_AX_SOUND_PROBE = r'''
import datetime, random, sys

def is_aware(dt):
    return dt.utcoffset() is not None

def diff_is_defined(now, pivot):
    try:
        (now - pivot).total_seconds()
        return True
    except TypeError:
        return False

# (1) The deep model's guard `same_disposition` == the REAL datetime subtraction
#     definedness, over all aware/naive disposition pairs + raise paths.
tzs = [
    None,
    datetime.timezone.utc,
    datetime.timezone(datetime.timedelta(hours=5, minutes=30)),
    datetime.timezone(datetime.timedelta(hours=-8)),
    datetime.timezone(datetime.timedelta(minutes=195)),
    datetime.timezone(datetime.timedelta(0)),
]
sample_a = datetime.datetime(2023, 6, 1, 12, 0, 0)
sample_b = datetime.datetime(2023, 5, 1, 9, 30, 0)
pairs = 0
for tz_a in tzs:
    for tz_b in tzs:
        now = sample_a.replace(tzinfo=tz_a)
        pivot = sample_b.replace(tzinfo=tz_b)
        model_defined = (is_aware(now) == is_aware(pivot))  # same_disposition
        real_defined = diff_is_defined(now, pivot)
        if model_defined != real_defined:
            print("AXIOM-UNSOUND: now_aware=%r pivot_aware=%r model=%r real=%r"
                  % (is_aware(now), is_aware(pivot), model_defined, real_defined))
            sys.exit(1)
        pairs += 1

# (2)+(3) The fix's effect: pivot built WITH tzinfo=d.tzinfo shares the source's
#     disposition (Result().tz is d.tz) and matches the current moment
#     (established aware iff d is aware), so the leftover-span diff is defined;
#     the pre-patch (naive) construction breaks it for every aware source.
def build_pivot(d, with_tzinfo):
    if with_tzinfo:
        return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute,
                                 d.second, tzinfo=d.tzinfo)
    return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)

def current_moment(d):
    return datetime.datetime.now(datetime.timezone.utc if is_aware(d) else None)

def check_fix(d):
    now = current_moment(d)
    if is_aware(now) != is_aware(d):
        print("AXIOM-UNSOUND: current moment disposition disagrees with source")
        sys.exit(1)
    fixed = build_pivot(d, True)
    if is_aware(fixed) != is_aware(d):
        print("AXIOM-UNSOUND: fixed pivot disposition != source on %r" % (d,))
        sys.exit(1)
    if not diff_is_defined(now, fixed):
        print("AXIOM-UNSOUND: fixed pivot leftover-span diff undefined on %r" % (d,))
        sys.exit(1)
    prepatch = build_pivot(d, False)  # always naive
    if is_aware(d) and diff_is_defined(now, prepatch):
        print("AXIOM-UNSOUND: pre-patch defined for aware source %r" % (d,))
        sys.exit(1)

boundary = [
    datetime.datetime(2007, 8, 14, 13, 46, 0),
    datetime.datetime(2022, 1, 1, 0, 0, 0),
    datetime.datetime(1007, 8, 14, 13, 46, 0),     # the 1000-years-ago boundary
    datetime.datetime(2016, 2, 29, 23, 59, 59),    # leap-day boundary
    datetime.datetime(2080, 1, 1, 0, 0, 0),
]
for base in boundary:
    for tz in tzs:
        check_fix(base.replace(tzinfo=tz))

rng = random.Random(16429)
for _ in range(20000):
    d = datetime.datetime(rng.randint(1, 9999), rng.randint(1, 12),
                          rng.randint(1, 28), rng.randint(0, 23),
                          rng.randint(0, 59), rng.randint(0, 59),
                          tzinfo=rng.choice(tzs))
    check_fix(d)

# (4) The ordered-span claim behind moment_span: the real difference's value is
#     a deterministic function of its two operands IN ORDER — repeating it
#     yields the same value, and reversing the operands changes it whenever the
#     span is non-zero (the reversal is the negation).
span_pairs = 0
for tz in tzs:
    for base_b in boundary:
        a = sample_a.replace(tzinfo=tz)
        b = base_b.replace(tzinfo=tz)
        if (a - b).total_seconds() != (a - b).total_seconds():
            print("AXIOM-UNSOUND: ordered span not deterministic")
            sys.exit(1)
        if a != b and (a - b).total_seconds() == (b - a).total_seconds():
            print("AXIOM-UNSOUND: reversed span unexpectedly equal")
            sys.exit(1)
        span_pairs += 1

print("AXIOM-SOUND: same_disposition == real datetime subtraction definedness "
      "over %d disposition pairs (incl. all aware/naive raise paths); the "
      "tzinfo=d.tzinfo fix carries the source disposition (diff defined) on %d "
      "boundary + 20000 fuzz sources; pre-patch naive construction breaks every "
      "aware source; ordered-span claim holds on %d same-disposition pairs."
      % (pairs, len(boundary) * len(tzs), span_pairs))
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import datetime, random, sys

def is_aware(dt):
    return dt.utcoffset() is not None

# CONTAINMENT: enumerate EXACTLY the (now, pivot) disposition pairs the MODEL can
# reach at the well_defined_diff call site, and assert each lies in the deep
# model's Requires domain: same_disposition(now.tz, pivot.tz).
#
# What the model can reach (from pivot_remaining's Requires + control flow):
#   * pivot.tz IS d.tz                       (constructor arg is d.tz; Result().tz is d.tz)
#   * now and d share a disposition          (precondition same_disposition(now.tz, d.tz))
#   => therefore now and pivot ALWAYS share a disposition at the call site.
# We model d.tz over the full disposition space the caller can present (naive +
# every aware offset) and `now` over every disposition that satisfies the
# precondition (i.e. same aware/naive class as d). Each reachable pair MUST be
# in the domain. (Covering MORE than the caller reaches would be SOUND; here we
# show every REACHABLE pair is covered.)
tzs = [
    None,
    datetime.timezone.utc,
    datetime.timezone(datetime.timedelta(hours=5, minutes=30)),
    datetime.timezone(datetime.timedelta(hours=-8)),
    datetime.timezone(datetime.timedelta(minutes=195)),
    datetime.timezone(datetime.timedelta(0)),
]

def same_disposition(a, b):
    # model.py: is_offset_aware(a) == is_offset_aware(b); aware == (tz is not None)
    return (a is not None) == (b is not None)

reached = 0
escaped = 0
rng = random.Random(99)
for d_tz in tzs:
    # pivot carries d.tz exactly (model constructor + Result().tz is d.tz):
    pivot_tz = d_tz
    for now_tz in tzs:
        # the precondition only admits a `now` sharing d's disposition class:
        if not same_disposition(now_tz, d_tz):
            continue   # caller CANNOT reach this (precondition rejects it)
        reached += 1
        # the call-site obligation: same_disposition(now.tz, pivot.tz)
        if not same_disposition(now_tz, pivot_tz):
            escaped += 1
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable pair now_tz aware=%r "
                  "pivot_tz aware=%r escapes well_defined_diff Requires domain"
                  % (now_tz is not None, pivot_tz is not None))

# Cross-check with the REAL datetime subtraction: every reachable pair must be
# defined by the real callee too (the domain we claim to cover is real).
sa = datetime.datetime(2023, 6, 1, 12, 0, 0)
sb = datetime.datetime(2023, 5, 1, 9, 30, 0)
for d_tz in tzs:
    pivot = sb.replace(tzinfo=d_tz)
    for now_tz in tzs:
        if not same_disposition(now_tz, d_tz):
            continue
        now = sa.replace(tzinfo=now_tz)
        try:
            (now - pivot).total_seconds()
        except TypeError:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable pair undefined for REAL "
                  "datetime: now_tz=%r d_tz=%r" % (now_tz, d_tz))
            sys.exit(1)

if escaped:
    sys.exit(1)
print("AXIOM-COVERED: all %d caller-reachable (now,pivot) disposition pairs lie "
      "inside well_defined_diff's Requires domain same_disposition(now.tz, "
      "pivot.tz) and are defined by the REAL datetime subtraction; 0 escapes. "
      "(pivot.tz is d.tz; the precondition admits only `now` sharing d's "
      "disposition.)" % reached)
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-well-defined-diff",
        "axiom": "well_defined_diff",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "well_defined_diff is an A-reference for datetime subtraction. Its "
            "domain guard same_disposition MUST equal the real subtraction's "
            "definedness over every aware/naive pair (incl. the TypeError raise "
            "paths), and the tzinfo=d.tzinfo fix MUST make the pivot share the "
            "source disposition so the diff is defined; the pre-patch naive "
            "construction MUST break it for aware sources. Any mismatch => "
            "AXIOM-UNSOUND. (Mirrors + extends axiom_check.py.)"
        ),
    },
    {
        "id": "ax-contain-well-defined-diff",
        "axiom": "well_defined_diff",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Containment: every (now, pivot) disposition pair the MODEL can "
            "reach at the well_defined_diff call site — pivot.tz is d.tz, and "
            "`now` admitted only when it shares d's disposition — must lie in "
            "the guard's Requires domain same_disposition(now.tz, pivot.tz). A "
            "reachable escape => AXIOM-TOO-WEAK-FOR-CALLER. Cross-checked: every "
            "reachable pair is defined by the real datetime subtraction."
        ),
    },
]
