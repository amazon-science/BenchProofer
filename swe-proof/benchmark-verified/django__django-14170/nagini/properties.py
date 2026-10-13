# properties.py — PBT falsification battery for django__django-14170.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery: ONLY text inside
# a `# impl-start`/`# impl-end` block is edited, so the frozen spec (axioms /
# pure / pre / post-conditions + signatures) is byte-identical and same_spec
# holds. The runner checks each variant with the real Nagini verifier on the
# host; AXIOM_TESTS run the real stdlib callee in the instance Docker image.
#
# Defended surface (adversarial read):
#   Three contracted functions, all with Requires(True). Their inputs are scalar
#   value types (int year, bool flags) — there is NO read-only Acc(x,1/2) input
#   and NO input predicate, so the frame-mutation class does NOT apply (justified
#   in 'assessment'). The load-bearing postconditions:
#       date_field_year_range:     Result()[i] == date_lower/date_upper(...)
#       datetime_field_year_range: Result()[i] == dt_lower/dt_upper(...)
#       year_lookup_range:         Result()[i] == lookup_lower/lookup_upper(...)
#   where the helpers are @Pure functions GROUNDED in the args: they unfold to
#   the same cal_jan1/cal_dec31/iso_jan1 (day carrier) and dt_jan1/dt_dec31/
#   dt_iso_jan1 (microsecond-instant carrier) axiom calls the impl makes. So
#   there is no opaque answer-key to echo wrongly (the "echo" IS the correct
#   answer) — directive 2's grounded-oracle path: no wrong-echo case, an honest
#   cheapest-impl positive control instead.
#
#   The discriminating behaviour the spec must defend (the actual bug fixed by
#   the gold patch): the endpoints must follow the ISO calendar when
#   week_numbering and the Gregorian calendar otherwise; the upper ISO endpoint
#   is the day/instant BEFORE the next ISO year; the dispatch must FORWARD the
#   week-numbering flag; and the two field kinds live in DIFFERENT carriers
#   (day ordinals vs. microsecond instants), so routing a datetime lookup to
#   the date endpoints (or collapsing the datetime endpoints to day endpoints)
#   is a spec violation, not a harmless reshuffle. The battery attacks each of
#   these (partial-domain: wrong-calendar, mixed-calendar, swapped endpoints,
#   off-by-one upper, a dispatch that drops the forwarded flag, a dispatch that
#   swaps the field-kind routing, and a datetime site that returns day
#   endpoints — the carrier-collapse attack a prior audit exploited).

from pathlib import Path

INSTANCE = "django__django-14170"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl blocks (verbatim from model.py) we surgically rewrite.
# The date-field and datetime-field impls are now DISTINCT (different carriers,
# different axiom families), so each block is unique and directly targetable.

_DATE_GOLD = (
    "    if week_numbering:\n"
    "        first = iso_jan1(value)\n"
    "        second = iso_jan1(value + 1) - 1\n"
    "    else:\n"
    "        first = cal_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    return [first, second]"
)

_DT_GOLD = (
    "    if week_numbering:\n"
    "        first = dt_iso_jan1(value)\n"
    "        second = dt_iso_jan1(value + 1) - 1\n"
    "    else:\n"
    "        first = dt_jan1(value)\n"
    "        second = dt_dec31(value)\n"
    "    return [first, second]"
)

_DISPATCH_GOLD = (
    "    if is_datetime_field:\n"
    "        bounds = datetime_field_year_range(year, lhs_is_week_numbering)\n"
    "    else:\n"
    "        bounds = date_field_year_range(year, lhs_is_week_numbering)\n"
    "    return bounds"
)


def _swap_date(new_block):
    return _swap(_BASE, _DATE_GOLD, new_block)


def _swap_dt(new_block):
    return _swap(_BASE, _DT_GOLD, new_block)


def _swap_dispatch(new_block):
    return _swap(_BASE, _DISPATCH_GOLD, new_block)


# ===========================================================================
# SPEC TESTS
# ===========================================================================

SPEC_TESTS = []

# ---- POSITIVE CONTROL 1: structurally-different but CORRECT date impl ----
# Reorder the branch (test `not week_numbering` first) and build the result via
# a local list bound + per-element assignment instead of a literal. No proof
# obligation is dropped (the postcondition is a direct value pin, no loop
# invariant / framing lemma), so a faithful correct impl MUST verify. If it
# does not => SPEC-TOO-STRONG.
_POS_REORDER_DATE = (
    "    if not week_numbering:\n"
    "        lo = cal_jan1(value)\n"
    "        hi = cal_dec31(value)\n"
    "    else:\n"
    "        lo = iso_jan1(value)\n"
    "        hi = iso_jan1(value + 1) - 1\n"
    "    res = [lo, hi]  # type: List[int]\n"
    "    return res"
)
SPEC_TESTS.append({
    "id": "pos-reorder-date",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap_date(_POS_REORDER_DATE),
    "rationale": "branch-reorder + local-list reshape is the same value map as "
                 "gold; the postcondition is a direct value pin (no loop/lemma), "
                 "so a faithful correct impl must verify, else SPEC-TOO-STRONG.",
})

# ---- POSITIVE CONTROL 2: cheapest honest impls — echo the GROUNDED oracles ----
# Directive 2 (grounded-oracle path): the pure helpers are functions of the
# args, fully unfolded to the same axioms the impl uses; there is no WRONG echo
# possible. The honest cheapest impl returns exactly the @Pure oracle. This
# MUST verify (it is the correct answer) — a positive control, not a defect.
_POS_ECHO_DATE = (
    "    res = [date_lower(value, week_numbering), "
    "date_upper(value, week_numbering)]  # type: List[int]\n"
    "    return res"
)
SPEC_TESTS.append({
    "id": "pos-grounded-oracle-echo-date",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap_date(_POS_ECHO_DATE),
    "rationale": "the postcondition oracle (date_lower/date_upper) is grounded "
                 "in the args (unfolds to the same axioms), so echoing it is the "
                 "CORRECT answer and must verify — there is no wrong echo to "
                 "exploit (grounded-oracle path of directive 2).",
})

_POS_ECHO_DT = (
    "    res = [dt_lower(value, week_numbering), "
    "dt_upper(value, week_numbering)]  # type: List[int]\n"
    "    return res"
)
SPEC_TESTS.append({
    "id": "pos-grounded-oracle-echo-datetime",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap_dt(_POS_ECHO_DT),
    "rationale": "same grounded-oracle echo for the instant-carrier site: "
                 "dt_lower/dt_upper unfold to the same dt_* axioms the impl "
                 "calls, so the echo is correct and must verify.",
})

# ---- POSITIVE CONTROL 3: structurally-different CORRECT dispatch ----
# Reorder the field-kind branch (test the date case first via `not`). Forwards
# the flag identically. Must verify.
_POS_DISPATCH = (
    "    if not is_datetime_field:\n"
    "        bounds = date_field_year_range(year, lhs_is_week_numbering)\n"
    "    else:\n"
    "        bounds = datetime_field_year_range(year, lhs_is_week_numbering)\n"
    "    return bounds"
)
SPEC_TESTS.append({
    "id": "pos-dispatch-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap_dispatch(_POS_DISPATCH),
    "rationale": "reordered field-kind branch that still routes each field kind "
                 "to its own carrier and forwards the week-numbering flag "
                 "verbatim — a faithful correct dispatch must verify (else "
                 "SPEC-TOO-STRONG).",
})

# ---- ADMISSIBILITY: Requires(True) admits an F2P-shaped input ----
# Gold value map with explicit Asserts that the postcondition endpoints hold
# for an in-domain input. Requires(True) is trivially admissible, but a
# self-call that verifies confirms the precond accepts a normal input (else
# PRECOND-TOO-STRONG).
_ADMISS = (
    "    if week_numbering:\n"
    "        first = iso_jan1(value)\n"
    "        second = iso_jan1(value + 1) - 1\n"
    "    else:\n"
    "        first = cal_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    out = [first, second]  # type: List[int]\n"
    "    Assert(out[0] == date_lower(value, week_numbering))\n"
    "    Assert(out[1] == date_upper(value, week_numbering))\n"
    "    return out"
)
SPEC_TESTS.append({
    "id": "admiss-self-assert",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap_date(_ADMISS),
    "rationale": "the gold value map with explicit Assert that the postcondition "
                 "endpoints hold for an in-domain input — confirms Requires(True) "
                 "admits a normal F2P-shaped input (else PRECOND-TOO-STRONG).",
})

# ---- REJECT 1: WRONG CALENDAR (the actual regression / prepatch bug) ----
# Ignore week_numbering entirely: always return the calendar-year endpoints.
# This is EXACTLY the pre-patch source (operations.py had no ISO branch and the
# YearLookup optimisation applied uniformly to __year and __iso_year). Its
# faithful real patch is "no change" — so test_extract_iso_year_func_boundaries
# (filter iso_year=2015 must include the 2014-12-31 row) FAILS exactly as
# before the fix.
_REJ_WRONGCAL_DATE = (
    "    first = cal_jan1(value)\n"
    "    second = cal_dec31(value)\n"
    "    return [first, second]"
)
SPEC_TESTS.append({
    "id": "rej-wrong-calendar-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_date(_REJ_WRONGCAL_DATE),
    "refinement": "this is the pre-patch behaviour verbatim (no iso_year branch); "
                  "the faithful real patch makes no change, so "
                  "test_extract_iso_year_func_boundaries still mis-buckets the "
                  "late-Dec / early-Jan rows (e.g. 2014-12-31 is ISO-2015 but the "
                  "calendar bounds for 2015 exclude it) and does NOT resolve.",
    "rationale": "rejected by Ensures Result()[0]==date_lower(value,week_numbering): "
                 "when week_numbering=True the spec requires iso_jan1(value) but "
                 "this returns cal_jan1(value) (and likewise the upper). "
                 "partial-domain: correct only on the non-week-numbering subdomain.",
})

_REJ_WRONGCAL_DT = (
    "    first = dt_jan1(value)\n"
    "    second = dt_dec31(value)\n"
    "    return [first, second]"
)
SPEC_TESTS.append({
    "id": "rej-wrong-calendar-datetime",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_dt(_REJ_WRONGCAL_DT),
    "refinement": "the datetime-site pre-patch behaviour: always calendar-year "
                  "instants, no ISO branch — the F2P DateTimeField boundary test "
                  "still fails (its rows ARE datetimes).",
    "rationale": "rejected by Ensures Result()[0]==dt_lower(value,week_numbering): "
                 "when week_numbering=True the spec requires dt_iso_jan1(value) "
                 "but this returns dt_jan1(value).",
})

# ---- REJECT 2: MIXED CALENDAR — ISO lower, calendar upper ----
# Picks the ISO first day but the calendar last day when week_numbering.
_REJ_MIXED = (
    "    if week_numbering:\n"
    "        first = iso_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    else:\n"
    "        first = cal_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    return [first, second]"
)
SPEC_TESTS.append({
    "id": "rej-mixed-calendar-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_date(_REJ_MIXED),
    "refinement": "ISO start but calendar (Dec-31) end: a faithful patch would "
                  "set the right lower bound but the wrong upper bound, so ISO "
                  "years that extend into the next calendar's January (or end "
                  "before Dec-31) bound the wrong day-set and "
                  "test_extract_iso_year_func_boundaries fails on the upper edge.",
    "rationale": "rejected by Ensures Result()[1]==date_upper(value,week_numbering): "
                 "for week_numbering=True the spec requires iso_jan1(value+1)-1 but "
                 "this returns cal_dec31(value). partial-domain on the upper endpoint.",
})

# ---- REJECT 3: SWAPPED ENDPOINTS (lower/upper transposed) ----
_REJ_SWAP = (
    "    if week_numbering:\n"
    "        first = iso_jan1(value)\n"
    "        second = iso_jan1(value + 1) - 1\n"
    "    else:\n"
    "        first = cal_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    return [second, first]"
)
SPEC_TESTS.append({
    "id": "rej-swapped-endpoints-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_date(_REJ_SWAP),
    "refinement": "returning [upper, lower] makes BETWEEN(lower, upper) reversed "
                  "(lower > upper), selecting zero rows for every year lookup, so "
                  "the F2P boundary test (and P2P year-lookup tests) all fail.",
    "rationale": "rejected by Ensures Result()[0]==date_lower(...): the first "
                 "element is date_upper, not date_lower (they differ since the "
                 "interval is non-empty). control-flow-/structure-visible swap.",
})

# ---- REJECT 4: OFF-BY-ONE upper ISO endpoint (drops the `-1`) ----
# second = iso_jan1(value+1) (the FIRST day of the NEXT ISO year) instead of the
# day before it. The upper bound now leaks the first row of the next ISO year.
_REJ_OFFBY1 = (
    "    if week_numbering:\n"
    "        first = iso_jan1(value)\n"
    "        second = iso_jan1(value + 1)\n"
    "    else:\n"
    "        first = cal_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    return [first, second]"
)
SPEC_TESTS.append({
    "id": "rej-offby1-upper-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_date(_REJ_OFFBY1),
    "refinement": "second = fromisocalendar(value+1,1,1) WITHOUT the "
                  "- timedelta(days=1): the upper bound is the FIRST day of the "
                  "next ISO year, so the BETWEEN range leaks that boundary row "
                  "(e.g. iso_year=2015 also matches the first day of ISO 2016) "
                  "and test_extract_iso_year_func_boundaries fails with an extra row.",
    "rationale": "rejected by Ensures Result()[1]==date_upper(value,week_numbering) "
                 "== iso_jan1(value+1)-1; this returns iso_jan1(value+1), off by one. "
                 "partial-domain: only the single boundary day diverges.",
})

# ---- REJECT 5: DISPATCH DROPS THE FLAG (forwards False always) ----
# The dispatch computes the right field-kind routing but forwards a CONSTANT
# False instead of lhs_is_week_numbering, so an __iso_year lookup is answered
# with calendar bounds. Faithful patch: the C1 fix (iso_year = isinstance(...,
# ExtractIsoYear)) is computed but never forwarded — the regression survives,
# F2P fails.
_REJ_DROPFLAG = (
    "    if is_datetime_field:\n"
    "        bounds = datetime_field_year_range(year, False)\n"
    "    else:\n"
    "        bounds = date_field_year_range(year, False)\n"
    "    return bounds"
)
SPEC_TESTS.append({
    "id": "rej-dispatch-drops-flag",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_dispatch(_REJ_DROPFLAG),
    "refinement": "the dispatch computes the field routing but forwards a "
                  "constant False instead of the week-numbering flag — modeling a "
                  "patch that adds `iso_year = isinstance(self.lhs, ExtractIsoYear)` "
                  "but forgets to pass iso_year= to the endpoint method. The ISO "
                  "branch is never reached, so the iso_year boundary test still "
                  "fails (calendar bounds used for __iso_year).",
    "rationale": "rejected by year_lookup_range's Ensures "
                 "Result()[0]==lookup_lower(is_datetime_field, year, "
                 "lhs_is_week_numbering): the callee returns the week_numbering="
                 "False endpoints, which differ when the flag is True. "
                 "value-/dispatch-level: the forwarded flag is discriminating "
                 "content of the change.",
})

# ---- REJECT 6: DISPATCH SWAPS THE FIELD-KIND ROUTING ----
# Routes is_datetime_field to the DATE method and vice-versa. The two field
# kinds live in DIFFERENT carriers (day ordinals vs. microsecond instants), so
# this returns day-scale numbers where instant-scale ones are required (and
# vice versa) — a real Django patch that called the date-field bounds method
# for a DateTimeField would emit BETWEEN over date-typed params against a
# datetime column, breaking the year-lookup tests. A prior audit exploited the
# earlier single-carrier spec exactly here (the collapse admitted the swap);
# the two-carrier spec must REJECT it.
_REJ_DISPATCH_SWAP = (
    "    if is_datetime_field:\n"
    "        bounds = date_field_year_range(year, lhs_is_week_numbering)\n"
    "    else:\n"
    "        bounds = datetime_field_year_range(year, lhs_is_week_numbering)\n"
    "    return bounds"
)
SPEC_TESTS.append({
    "id": "rej-dispatch-routing-swap",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_dispatch(_REJ_DISPATCH_SWAP),
    "refinement": "a faithful patch shaped this way calls "
                  "year_lookup_bounds_for_date_field for DateTimeFields and "
                  "_for_datetime_field for DateFields: the BETWEEN parameters "
                  "get the wrong type/granularity (dates for a datetime column "
                  "truncate away the day's interior instants; datetimes for a "
                  "date column), so the year-lookup tests fail.",
    "rationale": "rejected by year_lookup_range's Ensures Result()[0]=="
                 "lookup_lower(is_datetime_field, ...): for a datetime field the "
                 "spec requires dt_lower (instant carrier) but the swapped "
                 "routing returns date_lower (day carrier); the axioms are "
                 "uninterpreted and distinct, so the verifier cannot conflate "
                 "them. This closes the carrier-collapse hole a prior audit "
                 "exploited.",
})

# ---- REJECT 7: CARRIER COLLAPSE — datetime site returns DAY endpoints ----
# The datetime-field site computes the date-field (day-ordinal) endpoints
# instead of instant endpoints. This is the audit's atk1_collapse_date shape
# applied at the endpoint site: under the old single-carrier spec it verified;
# the two-carrier spec must reject it (dt_lower != date_lower — different
# uninterpreted axiom families).
_REJ_COLLAPSE_DT = (
    "    if week_numbering:\n"
    "        first = iso_jan1(value)\n"
    "        second = iso_jan1(value + 1) - 1\n"
    "    else:\n"
    "        first = cal_jan1(value)\n"
    "        second = cal_dec31(value)\n"
    "    return [first, second]"
)
SPEC_TESTS.append({
    "id": "rej-carrier-collapse-datetime",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_dt(_REJ_COLLAPSE_DT),
    "refinement": "a faithful patch shaped this way makes "
                  "year_lookup_bounds_for_datetime_field return datetime.date "
                  "objects (whole days) instead of datetime instants: the upper "
                  "bound loses the 23:59:59.999999 / -1µs interior of the last "
                  "day, so datetime rows inside the final day fall outside the "
                  "BETWEEN range and the year-lookup tests fail.",
    "rationale": "rejected by Ensures Result()[0]==dt_lower(value,week_numbering): "
                 "the impl returns iso_jan1/cal_jan1 (day-carrier axioms) where "
                 "dt_iso_jan1/dt_jan1 (instant-carrier axioms) are required; the "
                 "two axiom families are distinct uninterpreted functions.",
})


# ===========================================================================
# AXIOM TESTS  (real stdlib callee in the instance Docker image, gold applied)
# ===========================================================================
#
# The six axioms cal_jan1 / cal_dec31 / iso_jan1 (day carrier) and dt_jan1 /
# dt_dec31 / dt_iso_jan1 (microsecond-instant carrier) are @ContractOnly @Pure
# A-consumed: the proof pins the returned endpoints to these stdlib
# constructors. The probes EXECUTE the real callee (datetime.date /
# datetime.datetime and their .fromisocalendar) — never scrape source — and
# assert:
#   (soundness) each interval is EXACTLY its year under its own calendar in its
#     own carrier over named + fuzz years, including the F2P boundary days; the
#     two calendars genuinely disagree (the bug is observable); and the two
#     carriers are consistent (each instant landmark lies on its day-carrier
#     day) yet distinct (no numeral collision), so field-kind routing is
#     observable;
#   (containment) every callee-input the MODEL can reach is in the axiom's
#     Requires domain. The model's Requires is True over int years, and the impl
#     calls the constructors with `value` and `value+1`. The real callee's
#     domain is datetime.MINYEAR..MAXYEAR (1..9999); the probe enumerates the
#     reachable boundary inputs and asserts the constructor accepts them.
#
# The probe needs only the stdlib `datetime` (the django 4.0 image ships
# Python >=3.8, which has date/datetime.fromisocalendar... datetime.datetime
# .fromisocalendar exists on 3.8+ as inherited classmethod returning datetime).

_AX_SOUNDNESS_PROBE = r'''
import datetime, random, sys

DT_MIN = datetime.datetime(1, 1, 1)
USEC = datetime.timedelta(microseconds=1)

def cal_jan1(y):  return datetime.date(y, 1, 1).toordinal()
def cal_dec31(y): return datetime.date(y, 12, 31).toordinal()
def iso_jan1(y):  return datetime.date.fromisocalendar(y, 1, 1).toordinal()
def dt_inst(t):   return (t - DT_MIN) // USEC
def dt_jan1(y):   return dt_inst(datetime.datetime(y, 1, 1))
def dt_dec31(y):  return dt_inst(datetime.datetime(y, 12, 31, 23, 59, 59, 999999))
def dt_iso_jan1(y): return dt_inst(datetime.datetime.fromisocalendar(y, 1, 1))
def cal_year_of(o):  return datetime.date.fromordinal(o).year
def iso_year_of(o):  return datetime.date.fromordinal(o).isocalendar()[0]
def dt_of(i):     return DT_MIN + i * USEC

def check_calendar_year(y):
    lo, hi = cal_jan1(y), cal_dec31(y)
    assert lo <= hi, "calendar interval empty for %d" % y
    assert cal_year_of(lo) == y and cal_year_of(hi) == y, "endpoint not in year %d" % y
    if lo - 1 >= 1:
        assert cal_year_of(lo - 1) == y - 1, "below cal_jan1(%d) wrong" % y
    assert cal_year_of(hi + 1) == y + 1, "above cal_dec31(%d) wrong" % y
    for d in range(max(1, lo - 5), hi + 6):
        assert (lo <= d <= hi) == (cal_year_of(d) == y), \
            "calendar membership mismatch y=%d o=%d" % (y, d)

def check_iso_year(y):
    lo, hi = iso_jan1(y), iso_jan1(y + 1) - 1
    assert lo <= hi, "ISO interval empty for %d" % y
    assert iso_year_of(lo) == y and iso_year_of(hi) == y, "ISO endpoint not in year %d" % y
    if lo - 1 >= 1:
        assert iso_year_of(lo - 1) == y - 1, "below iso_jan1(%d) wrong" % y
    assert iso_year_of(hi + 1) == y + 1, "above iso last(%d) wrong" % y
    for d in range(max(1, lo - 5), hi + 6):
        assert (lo <= d <= hi) == (iso_year_of(d) == y), \
            "ISO membership mismatch y=%d o=%d" % (y, d)

def check_dt_calendar_year(y):
    lo, hi = dt_jan1(y), dt_dec31(y)
    assert lo <= hi, "dt calendar interval empty for %d" % y
    assert dt_of(lo).year == y and dt_of(hi).year == y, "dt endpoint not in year %d" % y
    assert hi + 1 == dt_jan1(y + 1), "dt_dec31(%d)+1 != dt_jan1(%d)" % (y, y + 1)
    if lo - 1 >= 0:
        assert dt_of(lo - 1).year == y - 1, "below dt_jan1(%d) wrong" % y
    assert dt_of(hi + 1).year == y + 1, "above dt_dec31(%d) wrong" % y

def check_dt_iso_year(y):
    lo, hi = dt_iso_jan1(y), dt_iso_jan1(y + 1) - 1
    assert lo <= hi, "dt ISO interval empty for %d" % y
    assert dt_of(lo).isocalendar()[0] == y, "dt_iso_jan1(%d) not in ISO year" % y
    assert dt_of(hi).isocalendar()[0] == y, "dt ISO last(%d) not in ISO year" % y
    assert dt_of(hi + 1).isocalendar()[0] == y + 1, "above dt ISO last(%d) wrong" % y
    if lo - 1 >= 0:
        assert dt_of(lo - 1).isocalendar()[0] == y - 1, "below dt_iso_jan1(%d) wrong" % y
    # gold patch's upper endpoint arithmetic on the real callee
    real_upper = datetime.datetime.fromisocalendar(y + 1, 1, 1) - USEC
    assert dt_inst(real_upper) == hi, "dt ISO -1usec identity broken at %d" % y

def check_carriers(y):
    assert dt_of(dt_jan1(y)).date().toordinal() == cal_jan1(y)
    assert dt_of(dt_dec31(y)).date().toordinal() == cal_dec31(y)
    assert dt_of(dt_iso_jan1(y)).date().toordinal() == iso_jan1(y)
    assert dt_jan1(y) != cal_jan1(y), "carriers collide at %d" % y

def check_disagree(y):
    assert (cal_jan1(y), cal_dec31(y)) != (iso_jan1(y), iso_jan1(y + 1) - 1), \
        "calendar and ISO intervals coincide for %d (bug invisible)" % y
    assert (dt_jan1(y), dt_dec31(y)) != (dt_iso_jan1(y), dt_iso_jan1(y + 1) - 1), \
        "dt calendar and ISO intervals coincide for %d" % y

def check_f2p_boundaries():
    days = {
        "w52_2014": datetime.date(2014, 12, 27),     # ISO 2014
        "w1_2014_2015": datetime.date(2014, 12, 31), # ISO 2015
        "w53_2015": datetime.date(2015, 12, 31),     # ISO 2015
    }
    exp = {"w52_2014": 2014, "w1_2014_2015": 2015, "w53_2015": 2015}
    for n, d in days.items():
        assert iso_year_of(d.toordinal()) == exp[n], "F2P day %s ISO year wrong" % n
    lo, hi = iso_jan1(2015), iso_jan1(2016) - 1
    sel = {n for n, d in days.items() if lo <= d.toordinal() <= hi}
    assert sel == {"w1_2014_2015", "w53_2015"}, "ISO 2015 bounds select %s" % sel
    clo, chi = cal_jan1(2015), cal_dec31(2015)
    buggy = {n for n, d in days.items() if clo <= d.toordinal() <= chi}
    assert "w1_2014_2015" not in buggy, "calendar bounds should drop the Dec-31-2014 row"
    assert buggy != sel, "calendar and ISO selections must differ on F2P"
    hi14 = iso_jan1(2015) - 1
    sel_lte = {n for n, d in days.items() if d.toordinal() <= hi14}
    assert sel_lte == {"w52_2014"}, "iso_year__lte=2014 selects %s" % sel_lte
    # instant carrier replay (the F2P field is a DateTimeField)
    stamps = {n: datetime.datetime(d.year, d.month, d.day, 14, 30, 50, 321)
              for n, d in days.items()}
    dlo, dhi = dt_iso_jan1(2015), dt_iso_jan1(2016) - 1
    dsel = {n for n, t in stamps.items() if dlo <= dt_inst(t) <= dhi}
    assert dsel == {"w1_2014_2015", "w53_2015"}, "dt ISO 2015 bounds select %s" % dsel

def main():
    named = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021,
             1, 100, 1000, 1999, 2000, 2400, 9998]
    for y in named:
        check_calendar_year(y); check_iso_year(y)
        check_dt_calendar_year(y); check_dt_iso_year(y)
        check_carriers(y); check_disagree(y)
    rng = random.Random(14170)
    for _ in range(2000):
        y = rng.randint(2, 9998)
        check_calendar_year(y); check_iso_year(y)
        check_dt_calendar_year(y); check_dt_iso_year(y)
        check_carriers(y)
    check_f2p_boundaries()
    print("AX-SOUND OK: day + instant carrier endpoint axioms each interval == "
          "its year under its calendar (%d named + 2000 fuzz years); carriers "
          "consistent and distinct; F2P ISO boundaries reproduced in both "
          "carriers." % len(named))
    sys.exit(0)

main()
'''

_AX_CONTAINMENT_PROBE = r'''
import datetime, sys

# Containment: every callee-input the MODEL can reach must lie in the real
# callee's Requires domain. The model's Requires is True; the impl applies
# cal_jan1(value)/cal_dec31(value)/iso_jan1(value)/dt_jan1(value)/
# dt_dec31(value)/dt_iso_jan1(value) and iso_jan1/dt_iso_jan1(value + 1).
# The caller-reachable years are real proleptic-Gregorian / ISO years the
# F2P + P2P tests exercise. datetime.date/datetime accept MINYEAR..MAXYEAR
# (1..9999); fromisocalendar accepts the same year range. We assert every
# reachable boundary input is ACCEPTED by the real constructor (no ValueError)
# and that value+1 (the ISO upper endpoint) stays in domain for value <= 9998.
# Covering MORE than the caller reaches is SOUND, not a defect.

MIN, MAX = datetime.MINYEAR, datetime.MAXYEAR   # 1, 9999
assert (MIN, MAX) == (1, 9999), "unexpected datetime year range %d..%d" % (MIN, MAX)

reachable = [2014, 2015, 2016, 1, 100, 1000, 1999, 2000, 2400, 9998]
for y in reachable:
    # day-carrier constructors the model calls
    datetime.date(y, 1, 1)
    datetime.date(y, 12, 31)
    datetime.date.fromisocalendar(y, 1, 1)
    # instant-carrier constructors the model calls
    datetime.datetime(y, 1, 1)
    datetime.datetime(y, 12, 31, 23, 59, 59, 999999)
    datetime.datetime.fromisocalendar(y, 1, 1)
    # upper ISO endpoints call fromisocalendar(value + 1, 1, 1); must be in domain
    assert y + 1 <= MAX, "value+1 out of domain for %d" % y
    datetime.date.fromisocalendar(y + 1, 1, 1)
    datetime.datetime.fromisocalendar(y + 1, 1, 1)

# Boundary of the domain itself: the largest year whose value+1 the model can
# still build is 9998 (value+1 = 9999 = MAXYEAR accepted); 9999 would push the
# ISO upper endpoint to year 10000 which is OUT of domain. The F2P/P2P tests
# only use small modern years, so they never reach value=9999; the model being
# total over int is wider than the caller, which is SOUND (not flagged) — we
# only verify the actually-reachable inputs are covered.
datetime.date.fromisocalendar(9999, 1, 1)
datetime.datetime.fromisocalendar(9999, 1, 1)
try:
    datetime.date.fromisocalendar(10000, 1, 1)
    raise AssertionError("year 10000 unexpectedly accepted")
except ValueError:
    pass

print("AX-CONTAIN OK: every caller-reachable endpoint input (year + value+1, "
      "both carriers) is in the real datetime constructor domain 1..9999; "
      "reachable F2P/P2P years well inside; out-of-domain only for years the "
      "caller never reaches.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-endpoints",
        "axiom": "cal_jan1/cal_dec31/iso_jan1/dt_jan1/dt_dec31/dt_iso_jan1",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "executes the real stdlib datetime.date / datetime.datetime "
                     "and their .fromisocalendar (the constructors the gold patch "
                     "calls) and asserts each axiom interval is EXACTLY its year "
                     "under its calendar in its carrier over named + 2000 fuzz "
                     "years plus the F2P boundary days; the two calendars "
                     "disagree and the two carriers are consistent yet distinct. "
                     "Any violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-endpoints",
        "axiom": "cal_jan1/cal_dec31/iso_jan1/dt_jan1/dt_dec31/dt_iso_jan1",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every callee-input the model can reach (value and value+1 "
                     "for the ISO upper endpoints, both carriers) over the "
                     "caller-reachable F2P/P2P years lies in the real constructor "
                     "domain 1..9999; a reachable input outside the domain would "
                     "be AXIOM-TOO-WEAK-FOR-CALLER, but none is reachable.",
    },
]
