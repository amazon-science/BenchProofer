# properties.py — G-PBT falsification battery for django__django-14170 (lean lane).
#
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC case is a FULL
# Solution.lean variant built by region surgery — only the impl region (and, where a
# positive honestly reproves, the proof body) is edited, so the frozen spec is
# byte-identical and `same_spec` holds by construction. Every expect="reject" case
# carries a refutation `witness`: a snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the postcondition
# and not to a tactic script that merely stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean + mapping.md + instance.json)
# ---------------------------------------------------------------------------------
# Two obligations, each a total function of TWO input binders and each with NO
# precondition hypothesis (`∀ (value : Int) (isoYear : Bool), problem_spec … impl`):
#
#   problem_spec_yearBoundsDate     value isoYear (result : Int × Int)
#   problem_spec_yearBoundsDatetime value isoYear (result : Int × Int)
#
# Each postcondition is a conjunction of TWO independent top-level clauses — the
# lower endpoint (`result.1`) and the upper endpoint (`result.2`) — and each clause
# is itself a two-armed conditional on the `isoYear` binder. So the surface is a
# 2 (obligation) x 2 (endpoint clause) x 2 (calendar selector) grid, and the battery
# has to attack each cell rather than each function.
#
# The two obligations live in DIFFERENT CARRIERS: the date obligation returns day
# ordinals, the timestamp obligation returns microsecond counts (`* usPerDay`), and
# its upper endpoint is one microsecond BEFORE the start of the next period rather
# than the last day of the current one. Collapsing the timestamp result to the day
# scale, or collapsing its upper endpoint to a period boundary, are spec violations
# here and not harmless reshuffles — the nagini sibling's carrier-collapse attack
# ports directly.
#
# The oracle is fully GROUNDED and TRANSPARENT: `gregJan1` / `gregDec31` /
# `isoYearStart` are total integer arithmetic on `value`, so `decide` computes both
# postconditions at any literal input and no witness needs to condition on an opaque
# term. There is no opaque answer-key to echo wrongly (the echo IS the correct
# answer), which is why the nagini "grounded-oracle echo" case ports as an honest
# POSITIVE control rather than as a rival.
#
# The discriminating behaviour the spec must defend: the endpoints must follow the
# week-numbering calendar when the selector is set and the ordinary calendar
# otherwise; the upper week-numbering endpoint is the day (resp. microsecond) BEFORE
# the next period starts; and the two column kinds must keep their own carriers.
#
# ---------------------------------------------------------------------------------
# WHICH OBLIGATION THE SHIPPED SUITE REACHES (audit-measured; read this before
# writing any `refinement` prose here)
# ---------------------------------------------------------------------------------
# The two obligations are NOT equally observable through the shipped tests, and an
# earlier revision of this manifest overclaimed on that point. Measured by replaying
# the shipped row sets and lookups against each rival's bound pair:
#
#   * The TIMESTAMP obligation is the one the boundary test exercises: that test's
#     rows are stored in, and filtered on, a timestamp column. Rivals that break the
#     timestamp bounds do break it — `weak-calendar-only-datetime` (one row missing
#     on the equality lookup, one extra on the at-most variant) and
#     `weak-day-scale-datetime` (empty result) are genuine
#     verify-does-not-imply-resolve cases.
#   * The DATE obligation is reached by exactly ONE shipped query, whose rows sit in
#     June of two adjacent years and which asserts a single match. Every window any
#     value-level date rival here produces still contains exactly that one row, so
#     that query cannot distinguish them. The single exception is
#     `weak-transposed-endpoints-date`, whose reversed bounds empty the range and
#     select zero rows where one is asserted.
#
# So the date-carrier value rivals are SPEC-STRENGTH cases, not resolution cases:
# they attest that the postcondition pins an obligation the shipped suite undertests.
# That is a legitimate and desirable thing for a uniqueness rival to attest — the
# spec states both obligations and must pin both — but it must be SAID, not dressed
# up as an F2P failure. Do not reintroduce a claim that the boundary test fails on a
# date-carrier rival; it does not, and five such claims were withdrawn here.
#
# ---------------------------------------------------------------------------------
# CARRIER NARROWING vs. the nagini sibling (case parity is NOT the target)
# ---------------------------------------------------------------------------------
# nagini contracts THREE functions: the two endpoint computations plus a dispatcher
# that selects a column kind and forwards the selector flag. This bundle models only
# the purely functional core — the two endpoint computations — and states explicitly
# that the selector's computation and the column-kind dispatch are the caller's job
# and out of scope. So nagini's three dispatch-level cases (a correct reordered
# dispatch, a dispatch that forwards a constant instead of the flag, a dispatch that
# swaps the two column kinds) have NO counterpart here: there is no dispatch symbol
# to reshape, and fabricating one would require adding a function to the frozen spec.
# They are omitted as carrier narrowing, itemised in 'assessment'.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION MUTATION. Vacuous on both sides. nagini's own manifest
#     already justified it as inapplicable there (the inputs are scalar value types,
#     no read-only aliased input and no input predicate); on lean it is vacuous for
#     the stronger reason that the language is referentially transparent. Nothing to
#     substitute.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries no such case, and on
#     lean the class is genuinely vacuous: `implementation_*` is a total Lean `def`,
#     so a diverging implementation cannot be written at all. (Contrast velvet under
#     partial termination semantics, where the same rival is a real spec hole —
#     the corpus-wide termination-semantics finding — but that is not this backend.)
#   * AXIOM_TESTS. The axiom lane belongs to G-AX, which this gate ignores; and there
#     is no consumed callee axiom here anyway (the calendar day-number computations
#     are modeled deeply as arithmetic, validated as A-references by G-CONF).
from pathlib import Path

INSTANCE = "django__django-14170"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------------
# ANCHORS. Each lies ENTIRELY inside the region it edits and is unique in the file,
# so the manifest breaks LOUDLY if the frozen solution ever changes.
# ---------------------------------------------------------------------------------

# The frozen branch body of the day-ordinal impl (inside its impl-start/impl-end).
_DATE_BODY = (
    "  if isoYear then\n"
    "    first := isoYearStart value\n"
    "    second := isoYearStart (value + 1) - 1\n"
    "  else\n"
    "    first := gregJan1 value\n"
    "    second := gregDec31 value\n"
)

# The frozen branch body of the microsecond impl.
_DT_BODY = (
    "  if isoYear then\n"
    "    first := isoYearStart value * usPerDay\n"
    "    second := isoYearStart (value + 1) * usPerDay - 1\n"
    "  else\n"
    "    first := gregJan1 value * usPerDay\n"
    "    second := gregJan1 (value + 1) * usPerDay - 1\n"
)

# The day-ordinal impl's branch body TOGETHER with its return — the anchor used by
# the endpoint-transposition rival, which edits the return and nothing else. Still
# entirely inside the impl region.
_DATE_BODY_RET = _DATE_BODY + "  return (first, second)"

# Proof-body anchors. The bare tactic body is identical in both obligations, so each
# anchor carries the last line of its own theorem STATEMENT to disambiguate; every
# replacement reproduces that line byte-for-byte, keeping each
# `theorem correct_<name>` statement identical and editing only the tactic script.
_PF_DATE_HEAD = "        (implementation_yearBoundsDate value isoYear) := by\n"
_PF_DT_HEAD = "        (implementation_yearBoundsDatetime value isoYear) := by\n"
_PF_TACTICS = (
    "  intro value isoYear\n"
    "  cases isoYear <;> exact ⟨rfl, rfl⟩"
)
_PF_DATE = _PF_DATE_HEAD + _PF_TACTICS
_PF_DT = _PF_DT_HEAD + _PF_TACTICS

for _a in (_DATE_BODY, _DT_BODY, _DATE_BODY_RET, _PF_DATE, _PF_DT):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted (count={_BASE.count(_a)}): {_a!r}")


def _wit(fn, value, flag, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a CONCRETE
    literal input, closed by `decide`.

    The oracle is total transparent integer arithmetic, so `decide` computes both
    endpoint clauses at the literal — no conditioning on the carrier is needed and
    the witness binds nothing, so it has no hypotheses that could be inconsistent.
    Elaborates against a rival that diverges from the frozen endpoints at that
    input; FAILS on the frozen solution, which satisfies the spec everywhere.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_yearBounds{fn} {value} {flag}\n"
        f"    (implementation_yearBounds{fn} {value} {flag}) := by\n"
        f"  unfold problem_spec_yearBounds{fn} implementation_yearBounds{fn}\n"
        f"  decide"
    )


# =================================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY, else SPEC-TOO-STRONG.
# =================================================================================

# pos-reorder-date: nagini's `pos-reorder-date`. Test the ordinary-calendar arm
# first via a negated selector and swap the two arms. Same value map on every input;
# only the branch FORM changes. The frozen tactic script still closes it.
_POS_REORDER_DATE = _swap(_BASE, _DATE_BODY, (
    "  if !isoYear then\n"
    "    first := gregJan1 value\n"
    "    second := gregDec31 value\n"
    "  else\n"
    "    first := isoYearStart value\n"
    "    second := isoYearStart (value + 1) - 1\n"
))

# pos-branchless-date / -datetime: nagini's two `pos-grounded-oracle-echo-*` cases.
# The oracle is grounded in the arguments (total transparent arithmetic), so
# assigning each endpoint the conditional expression the postcondition names is the
# honest CHEAPEST correct impl, not an ungrounded echo — there is no wrong echo to
# exploit here, and a wrong constant simply fails the postcondition. Replaces the
# branching statement with two branchless assignments.
_POS_BRANCHLESS_DATE = _swap(_BASE, _DATE_BODY, (
    "  first := if isoYear then isoYearStart value else gregJan1 value\n"
    "  second := if isoYear then isoYearStart (value + 1) - 1 else gregDec31 value\n"
))
_POS_BRANCHLESS_DT = _swap(_BASE, _DT_BODY, (
    "  first := (if isoYear then isoYearStart value else gregJan1 value) * usPerDay\n"
    "  second := (if isoYear then isoYearStart (value + 1) else gregJan1 (value + 1))"
    " * usPerDay - 1\n"
))

# pos-hoist-scale-datetime: choose the two period-boundary days FIRST, then apply the
# microsecond scaling once outside the branch. Structurally different (the scaling is
# hoisted, two extra locals), identical value map.
_POS_HOIST_DT = _swap(_BASE, _DT_BODY, (
    "  let mut firstDay : Int := 0\n"
    "  let mut nextDay : Int := 0\n"
    "  if isoYear then\n"
    "    firstDay := isoYearStart value\n"
    "    nextDay := isoYearStart (value + 1)\n"
    "  else\n"
    "    firstDay := gregJan1 value\n"
    "    nextDay := gregJan1 (value + 1)\n"
    "  first := firstDay * usPerDay\n"
    "  second := nextDay * usPerDay - 1\n"
))

# pos-uniform-upper-date: express the ordinary-calendar upper endpoint the same way
# the week-numbering arm expresses its own — the day before the next period's first
# day — instead of via the named last-day helper. An equivalent arithmetic form
# (definitionally equal, so the frozen script still closes).
_POS_UNIFORM_UPPER_DATE = _swap(_BASE, _DATE_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value\n"
    "    second := isoYearStart (value + 1) - 1\n"
    "  else\n"
    "    first := gregJan1 value\n"
    "    second := gregJan1 (value + 1) - 1\n"
))

# pos-lastmicro-datetime: the genuinely DIFFERENT arithmetic shape for the timestamp
# upper endpoint — the last day of the period, scaled, plus the last intra-day
# microsecond — instead of "one microsecond before the next period starts". Equal by
# ring arithmetic but NOT definitionally, so the frozen `rfl`-style script no longer
# closes and the proof body is honestly RE-CLOSED: the `theorem correct_*` statement
# is byte-identical, no new axiom/lemma/sorry, and each arm is discharged by
# unfolding the two arithmetic definitions the reshape moved and calling `ring`.
# This is the positive that actually defends the `- 1` clause against being over-fit
# to one syntactic form.
_POS_LASTMICRO_DT = _swap(
    _swap(_BASE, _DT_BODY, (
        "  if isoYear then\n"
        "    first := isoYearStart value * usPerDay\n"
        "    second := (isoYearStart (value + 1) - 1) * usPerDay + (usPerDay - 1)\n"
        "  else\n"
        "    first := gregJan1 value * usPerDay\n"
        "    second := gregDec31 value * usPerDay + (usPerDay - 1)\n"
    )),
    _PF_DT,
    _PF_DT_HEAD + (
        "  intro value isoYear\n"
        "  cases isoYear\n"
        "  · refine ⟨rfl, ?_⟩\n"
        "    show gregDec31 value * usPerDay + (usPerDay - 1)"
        " = gregJan1 (value + 1) * usPerDay - 1\n"
        "    unfold gregDec31 usPerDay\n"
        "    ring\n"
        "  · refine ⟨rfl, ?_⟩\n"
        "    show (isoYearStart (value + 1) - 1) * usPerDay + (usPerDay - 1)\n"
        "        = isoYearStart (value + 1) * usPerDay - 1\n"
        "    unfold usPerDay\n"
        "    ring"
    ),
)

# admiss-point-date: nagini's `admiss-self-assert`. The obligation carries NO
# precondition hypothesis, so there is no domain restriction that could be
# PRECOND-TOO-STRONG; the honest lean counterpart is to establish the postcondition
# at a CONCRETE in-domain input for BOTH selector values as a `have`, before proving
# the general statement exactly as frozen. That shows the postcondition is
# satisfiable (not vacuously unreachable) at a realistic input — the analogue of
# nagini's in-domain self-assert. Impl unchanged; only the tactic script grows.
_ADMISS_DATE = _swap(_BASE, _PF_DATE, _PF_DATE_HEAD + (
    "  have hIso : problem_spec_yearBoundsDate 2015 true\n"
    "      (implementation_yearBoundsDate 2015 true) := by\n"
    "    unfold problem_spec_yearBoundsDate implementation_yearBoundsDate\n"
    "    decide\n"
    "  have hCal : problem_spec_yearBoundsDate 2015 false\n"
    "      (implementation_yearBoundsDate 2015 false) := by\n"
    "    unfold problem_spec_yearBoundsDate implementation_yearBoundsDate\n"
    "    decide\n"
    "  intro value isoYear\n"
    "  cases isoYear <;> exact ⟨rfl, rfl⟩"
))


# =================================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly, edits only the impl region, and carries a witness SEEN to
# discriminate (elaborates on the rival, fails on the frozen solution).
# =================================================================================

# weak-calendar-only-*: nagini's two `rej-wrong-calendar-*`. Ignore the selector
# entirely and always return the ordinary-calendar endpoints. This is the pre-change
# behaviour verbatim, at each carrier.
_RIV_CAL_ONLY_DATE = _swap(_BASE, _DATE_BODY, (
    "  first := gregJan1 value\n"
    "  second := gregDec31 value\n"
))
_RIV_CAL_ONLY_DT = _swap(_BASE, _DT_BODY, (
    "  first := gregJan1 value * usPerDay\n"
    "  second := gregJan1 (value + 1) * usPerDay - 1\n"
))

# weak-iso-only-date: the MIRROR of the above, with no nagini counterpart. Ignore the
# selector in the other direction: always the week-numbering endpoints. Added because
# every nagini rival that abuses the selector holds it at the same value (the
# week-numbering arm), which would leave the ordinary-calendar arm attacked by no
# rival at all — a rival that mishandled only that arm would verify unnoticed.
_RIV_ISO_ONLY_DATE = _swap(_BASE, _DATE_BODY, (
    "  first := isoYearStart value\n"
    "  second := isoYearStart (value + 1) - 1\n"
))

# weak-mixed-upper-date: nagini's `rej-mixed-calendar-date`. Correct lower endpoint
# under the week-numbering calendar, ordinary-calendar upper endpoint.
_RIV_MIXED_DATE = _swap(_BASE, _DATE_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value\n"
    "    second := gregDec31 value\n"
    "  else\n"
    "    first := gregJan1 value\n"
    "    second := gregDec31 value\n"
))

# weak-transposed-endpoints-date: nagini's `rej-swapped-endpoints-date`. Correct
# endpoint VALUES, returned in the wrong positions.
_RIV_TRANSPOSED_DATE = _swap(_BASE, _DATE_BODY_RET,
                             _DATE_BODY + "  return (second, first)")

# weak-offbyone-upper-date: nagini's `rej-offby1-upper-date`. Drop the `- 1` from the
# week-numbering upper endpoint, so it names the FIRST day of the next period.
_RIV_OFFBYONE_DATE = _swap(_BASE, _DATE_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value\n"
    "    second := isoYearStart (value + 1)\n"
    "  else\n"
    "    first := gregJan1 value\n"
    "    second := gregDec31 value\n"
))

# weak-day-scale-datetime: nagini's `rej-carrier-collapse-datetime`. The timestamp
# obligation returns DAY-scale numbers (the day-ordinal endpoints) where
# microsecond-scale ones are required — the carrier collapse a prior audit exploited
# against a single-carrier spec.
_RIV_DAY_SCALE_DT = _swap(_BASE, _DT_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value\n"
    "    second := isoYearStart (value + 1) - 1\n"
    "  else\n"
    "    first := gregJan1 value\n"
    "    second := gregDec31 value\n"
))

# weak-midnight-upper-datetime: no nagini counterpart. The timestamp upper endpoint
# is taken at the START of the period's last day instead of at its last microsecond
# (drops the intra-day remainder). This is the timestamp-carrier analogue of the
# off-by-one rival, and it is the only rival that attacks the timestamp obligation's
# UPPER clause specifically — without it that clause is attacked only by rivals that
# also break the lower clause, so a rival wrong on the upper endpoint alone would
# verify unnoticed.
_RIV_MIDNIGHT_DT = _swap(_BASE, _DT_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value * usPerDay\n"
    "    second := (isoYearStart (value + 1) - 1) * usPerDay\n"
    "  else\n"
    "    first := gregJan1 value * usPerDay\n"
    "    second := gregDec31 value * usPerDay\n"
))

# weak-cal-lower-offbyone-date / -datetime: added by the AUDIT, no nagini counterpart.
# The coverage map of this battery's rivals over the 8 spec cells (2 obligations x
# {lower, upper} x 2 selector arms) showed every cell attacked, but the ordinary-
# calendar LOWER endpoint of each obligation only by rivals that ALSO break its
# upper endpoint (or the whole carrier). So a change that shifted just that one
# endpoint on just that arm — the single likeliest arithmetic slip at a period start,
# and the one place where the two obligations differ only by a scale factor — was
# pinned by no isolating rival. These two shift the ordinary-calendar lower endpoint
# by one day (resp. one day's worth of microseconds) and leave every other cell
# exactly as frozen, so each is refuted by ONE clause on ONE arm and nothing else.
_RIV_CAL_LOWER_OFF_DATE = _swap(_BASE, _DATE_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value\n"
    "    second := isoYearStart (value + 1) - 1\n"
    "  else\n"
    "    first := gregJan1 value + 1\n"
    "    second := gregDec31 value\n"
))
_RIV_CAL_LOWER_OFF_DT = _swap(_BASE, _DT_BODY, (
    "  if isoYear then\n"
    "    first := isoYearStart value * usPerDay\n"
    "    second := isoYearStart (value + 1) * usPerDay - 1\n"
    "  else\n"
    "    first := (gregJan1 value + 1) * usPerDay\n"
    "    second := gregJan1 (value + 1) * usPerDay - 1\n"
))


SPEC_TESTS = [
    # ------------------------------------------------------------------ positives
    {
        "id": "pos-reorder-date",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER_DATE,
        "rationale": (
            "PORT of nagini pos-reorder-date. Structurally different but CORRECT: the "
            "two calendar arms of the day-ordinal obligation are swapped and the "
            "selector negated, which is the same value map on every (value, isoYear) "
            "pair — only the branch FORM differs, a shape a faithful change could "
            "equally take. Both postcondition clauses are direct value pins (no loop, "
            "no induction), so the frozen `theorem correct_yearBoundsDate` statement "
            "is kept byte-identical and its tactic script still closes. If this is "
            "REJECTED => SPEC-TOO-STRONG (the postcondition is over-fit to one "
            "branch order rather than to the value map)."
        ),
    },
    {
        "id": "pos-branchless-date",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCHLESS_DATE,
        "rationale": (
            "PORT of nagini pos-grounded-oracle-echo-date. The postcondition oracle is "
            "GROUNDED in the two input binders — total transparent integer arithmetic "
            "on `value`, selected by `isoYear` — so assigning each endpoint the "
            "conditional expression the postcondition names is the honest CHEAPEST "
            "CORRECT impl, not an ungrounded answer-key echo: there is no wrong echo "
            "available here, since any constant or wrong selection fails the "
            "postcondition (which is exactly what the rivals below demonstrate). "
            "Replaces the branching statement with two branchless assignments. MUST "
            "verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-branchless-datetime",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCHLESS_DT,
        "rationale": (
            "PORT of nagini pos-grounded-oracle-echo-datetime — the same "
            "grounded-oracle positive at the microsecond carrier, including the "
            "one-microsecond-before-the-next-period upper endpoint. Defends the "
            "second obligation against SPEC-TOO-STRONG in a branchless shape."
        ),
    },
    {
        "id": "pos-hoist-scale-datetime",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HOIST_DT,
        "rationale": (
            "No nagini counterpart (nagini's second carrier had no scaling step to "
            "hoist). Selects the two period-boundary DAYS inside the branch and "
            "applies the microsecond scaling ONCE outside it, via two extra locals. "
            "Different control/data flow, identical value map — a faithful change "
            "could be written either way, so a rejection would be SPEC-TOO-STRONG "
            "against a legitimate factoring of the carrier conversion."
        ),
    },
    {
        "id": "pos-uniform-upper-date",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_UNIFORM_UPPER_DATE,
        "rationale": (
            "No nagini counterpart. Expresses the ordinary-calendar UPPER endpoint the "
            "way the week-numbering arm expresses its own — the day before the next "
            "period's first day — instead of via the named last-day helper. An "
            "equivalent arithmetic form of the same clause: it must verify, or the "
            "postcondition is pinned to a particular SPELLING of the upper endpoint "
            "rather than to its value (SPEC-TOO-STRONG). Pairs with "
            "weak-offbyone-upper-date, which shows the same clause still rejects the "
            "genuinely off-by-one form."
        ),
    },
    {
        "id": "pos-lastmicro-datetime",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LASTMICRO_DT,
        "rationale": (
            "No nagini counterpart; the most load-bearing positive here. The timestamp "
            "upper endpoint is computed as 'the period's last day, scaled, plus the "
            "last intra-day microsecond' instead of 'one microsecond before the next "
            "period starts'. The two are equal by ring arithmetic but NOT "
            "definitionally, so the frozen tactic script no longer closes and the "
            "proof body is HONESTLY RE-CLOSED: the `theorem correct_yearBoundsDatetime` "
            "statement is byte-identical, no new axiom/lemma/sorry/native_decide, and "
            "each arm is discharged by unfolding the two arithmetic definitions the "
            "reshape moved and calling `ring`. This is what stops the upper-endpoint "
            "clause from being defended only in one syntactic form: if it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-point-date",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_DATE,
        "rationale": (
            "PORT of nagini admiss-self-assert. The lean obligation carries NO "
            "precondition hypothesis (`∀ (value : Int) (isoYear : Bool), …`), so there "
            "is no domain restriction that could be literally PRECOND-TOO-STRONG; the "
            "honest counterpart of nagini's in-domain self-assert is to establish the "
            "postcondition at a CONCRETE realistic input for BOTH selector values as a "
            "`have` before proving the general statement exactly as frozen. That "
            "confirms the postcondition is satisfiable and computable at an in-domain "
            "point rather than vacuously unreachable. The impl is untouched and the "
            "theorem statement byte-identical; only the tactic script grows. If it "
            "FAILS the postcondition is unsatisfiable at a normal input."
        ),
    },

    # ------------------------------------------------------------------- rivals
    {
        "id": "weak-calendar-only-date",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CAL_ONLY_DATE,
        "refinement": (
            "This is the PRE-CHANGE behaviour verbatim at the day-ordinal site: the "
            "selector is ignored and the ordinary-calendar endpoints are returned "
            "unconditionally, so its faithful real counterpart leaves the DATE-column "
            "half of the change undone — a week-numbering year lookup against a date "
            "column keeps getting ordinary-calendar bounds, which is exactly the "
            "defect at that site. AUDIT CORRECTION (measured, not argued): this is a "
            "SPEC-STRENGTH case, not an F2P-resolution case. The shipped boundary test "
            "filters a TIMESTAMP column only, so it never reaches this obligation; and "
            "the one suite query that does reach it stores rows in June of adjacent "
            "years, whose selection is unchanged by any calendar choice (the widest "
            "window any date rival here produces for 2015 still excludes the June-2016 "
            "row). So a counterpart shaped this way WOULD pass the shipped suite. The "
            "case is retained because the spec states this obligation and must pin it: "
            "the rejection attests to spec strength BEYOND the F2P, which is the point "
            "of a uniqueness rival. The prior claim that the boundary test fails here "
            "was false and is withdrawn."
        ),
        "rationale": (
            "REJECTED by BOTH clauses of problem_spec_yearBoundsDate: at isoYear=true "
            "the spec pins result.1 to isoYearStart value and result.2 to "
            "isoYearStart (value + 1) - 1, and this returns the ordinary-calendar pair. "
            "Attacks the `isoYear` binder's true arm on the day carrier. Partial-domain: "
            "correct on the whole isoYear=false sub-domain, which is why the witness "
            "must probe the true arm. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit(
            "Date", "2015", "true",
            "week-numbering selector set at a year whose two calendars disagree: the "
            "frozen endpoints differ from the ordinary-calendar pair this rival returns",
        ),
    },
    {
        "id": "weak-calendar-only-datetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CAL_ONLY_DT,
        "refinement": (
            "The same pre-change behaviour at the timestamp site — and, of the two "
            "carriers, this is the one the shipped boundary test actually queries, so "
            "this rival is the battery's load-bearing resolution case. With the selector "
            "ignored the range test keeps using ordinary-calendar instants and the "
            "boundary rows stay mis-bucketed exactly as before. Measured against the "
            "shipped assertions: the equality lookup for the 2015 week-numbering year "
            "returns only the late-December-2015 row and MISSES the late-December-2014 "
            "row that belongs to that period (two rows asserted, one returned), and the "
            "at-most-2014 variant returns that same row as an EXTRA (one asserted, two "
            "returned). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by both clauses of problem_spec_yearBoundsDatetime at "
            "isoYear=true (spec: isoYearStart value * usPerDay and "
            "isoYearStart (value + 1) * usPerDay - 1). Attacks the `isoYear` true arm on "
            "the microsecond carrier — the second obligation, so it is not covered by "
            "the day-carrier rival above. Witness probes a DIFFERENT `value` from that "
            "rival, so the two do not collapse to one input point."
        ),
        "witness": _wit(
            "Datetime", "2020", "true",
            "week-numbering selector set on the microsecond carrier, at a different "
            "year than the day-carrier rival probes",
        ),
    },
    {
        "id": "weak-iso-only-date",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ISO_ONLY_DATE,
        "refinement": (
            "The MIRROR over-correction: the week-numbering endpoints are applied "
            "unconditionally, so an ORDINARY year lookup against a date column now gets "
            "week-numbering bounds — a real behavioural regression at that site, since "
            "the two periods genuinely differ (for 2015 the ordinary period is Jan 1 – "
            "Dec 31 while the week-numbering one runs Dec 29 2014 – Jan 3 2016). AUDIT "
            "CORRECTION (measured): the prior claim that this 'regresses every ordinary "
            "year lookup (the P2P year-lookup suite)' is FALSE and is withdrawn. The "
            "only shipped query reaching this obligation stores rows in June of "
            "adjacent years and asserts a single match; both windows above select "
            "exactly that one row, so the suite does not distinguish them. Retained as "
            "a SPEC-STRENGTH rival: it is the only one that gets the selector's TRUE "
            "arm right and the FALSE arm wrong, so without it a counterpart mishandling "
            "only the ordinary-calendar arm would verify unnoticed."
        ),
        "rationale": (
            "REJECTED by both clauses of problem_spec_yearBoundsDate at isoYear=false "
            "(spec: gregJan1 value and gregDec31 value). Attacks the `isoYear` binder's "
            "FALSE arm — the arm every ported nagini rival holds at the other value. "
            "Without this case a rival that mishandled only the ordinary-calendar arm "
            "would verify and the battery would never notice. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit(
            "Date", "2016", "false",
            "ordinary-calendar selector at a year where the week-numbering period "
            "starts after the ordinary one: the frozen lower endpoint is the earlier day",
        ),
    },
    {
        "id": "weak-mixed-upper-date",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MIXED_DATE,
        "refinement": (
            "PORT of nagini rej-mixed-calendar-date. A faithful counterpart sets the "
            "correct week-numbering LOWER bound but leaves the UPPER bound on the "
            "ordinary calendar, so a week-numbering period extending past the ordinary "
            "year's end truncates the row set at the wrong upper edge (for 2015 it stops "
            "at Dec 31 2015 instead of Jan 3 2016, dropping the first days of the next "
            "ordinary January that still belong to this week-numbering period). AUDIT "
            "CORRECTION (measured): the prior claim that 'the F2P boundary test fails on "
            "the upper edge' is FALSE and is withdrawn — that test filters a TIMESTAMP "
            "column and never reaches this obligation, and the one shipped query that "
            "does reach it is insensitive to the upper edge at these rows. Retained as a "
            "SPEC-STRENGTH near-miss: it isolates the upper-endpoint clause of the day "
            "obligation, which no other rival does."
        ),
        "rationale": (
            "REJECTED by the SECOND clause only (result.2 = isoYearStart (value + 1) - 1 "
            "at isoYear=true); the first clause is satisfied. This is the NEAR-MISS of "
            "weak-calendar-only-date — it agrees with the frozen solution over strictly "
            "more of the domain (the whole lower-endpoint clause plus the entire "
            "isoYear=false arm) — so it gets its own witness at its own `value`, "
            "demonstrating exactly the upper-clause sub-domain its rationale claims. "
            "Isolates the upper-endpoint clause of the day obligation."
        ),
        "witness": _wit(
            "Date", "2016", "true",
            "upper endpoint only: at this year the two calendars' period ends differ, so "
            "the frozen upper endpoint is not the ordinary-calendar last day",
        ),
    },
    {
        "id": "weak-transposed-endpoints-date",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRANSPOSED_DATE,
        "refinement": (
            "PORT of nagini rej-swapped-endpoints-date. Both endpoint VALUES are "
            "correct; they are returned in the wrong positions. A faithful counterpart "
            "hands the range test its bounds reversed (lower above upper), so the "
            "inclusive range is empty and every year lookup against a date column "
            "selects ZERO rows. This one DOES break the shipped suite, and it is the "
            "only date-carrier rival here that does: the surviving date-column year "
            "lookup asserts exactly one matching row and gets none (measured: 0 of 2 "
            "rows selected, for both selector values, where 1 is asserted). Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by both clauses of problem_spec_yearBoundsDate: result.1 is pinned "
            "to the period's first day and result.2 to its last, and the periods are "
            "non-degenerate, so the transposed pair satisfies neither. Attacks the "
            "POSITIONAL content of the postcondition — the pairing of clause to "
            "component — which no other rival touches: every other rival gets the "
            "positions right and the values wrong. Witness probes the isoYear=FALSE arm, "
            "so this rival also varies the selector binder away from the true arm."
        ),
        "witness": _wit(
            "Date", "2015", "false",
            "ordinary calendar: the frozen lower endpoint is the period's first day, "
            "which the transposed pair puts in the second position",
        ),
    },
    {
        "id": "weak-offbyone-upper-date",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OFFBYONE_DATE,
        "refinement": (
            "PORT of nagini rej-offby1-upper-date. Drops the single-day step back from "
            "the week-numbering upper endpoint, so the bound names the FIRST day of the "
            "NEXT period instead of the last day of this one, and a faithful "
            "counterpart's inclusive range over a date column leaks that one boundary "
            "day — a row on the first day of the next week-numbering period is reported "
            "as belonging to this one. AUDIT CORRECTION (measured): the prior claim that "
            "'the F2P boundary test fails with an extra row' is FALSE and is withdrawn — "
            "that test filters a TIMESTAMP column, so it never reaches this obligation, "
            "and no shipped row sits on the leaked day. Retained as a SPEC-STRENGTH "
            "rival: it is the narrowest in the battery (a single day, one clause, one "
            "selector arm), so it is what shows the clause pins an exact value rather "
            "than the right neighbourhood."
        ),
        "rationale": (
            "REJECTED by the second clause at isoYear=true (spec: "
            "isoYearStart (value + 1) - 1; rival: isoYearStart (value + 1)). The "
            "narrowest rival in the battery — it diverges on a SINGLE day, at the upper "
            "endpoint, on one arm of the selector — so it is the one that shows the "
            "clause pins an exact value and not merely the right neighbourhood. Its own "
            "`value` again, distinct from the other upper-clause rival's."
        ),
        "witness": _wit(
            "Date", "2014", "true",
            "single-day divergence at the week-numbering upper endpoint: the frozen "
            "bound is one day before the next period's first day",
        ),
    },
    {
        "id": "weak-day-scale-datetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DAY_SCALE_DT,
        "refinement": (
            "PORT of nagini rej-carrier-collapse-datetime. The timestamp obligation "
            "returns the DAY-scale endpoints — correct as day ordinals, meaningless as "
            "microsecond counts on the carrier this obligation is stated over. A "
            "faithful counterpart hands day-granular bounds to a timestamp column, and "
            "the mismatch is not a rounding error but a scale error of a factor of "
            "86400000000: reading the 2015 week-numbering ordinals as microsecond counts "
            "places both bounds a fraction of a second after the epoch (measured: "
            "0001-01-01 00:00:00.735596 .. .735966), so the range selects NOTHING and "
            "the shipped boundary test fails with an empty result where two rows are "
            "asserted. Does NOT resolve. This is the shape a prior audit exploited "
            "against a spec that collapsed the two carriers into one; the two-carrier "
            "spec must reject it."
        ),
        "rationale": (
            "REJECTED by both clauses of problem_spec_yearBoundsDatetime, which pin each "
            "endpoint to a microsecond count (`* usPerDay`, and the upper one minus a "
            "single microsecond). Attacks the CARRIER of the second obligation rather "
            "than its calendar selection — the one thing the two obligations do not "
            "share. Witness probes isoYear=FALSE, so the datetime obligation's selector "
            "binder is varied across its rivals too (the other two datetime rivals probe "
            "the true arm)."
        ),
        "witness": _wit(
            "Datetime", "2015", "false",
            "day-scale result on the microsecond carrier: the frozen lower endpoint is "
            "the scaled day, which the unscaled ordinal cannot equal",
        ),
    },
    {
        "id": "weak-midnight-upper-datetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MIDNIGHT_DT,
        "refinement": (
            "No nagini counterpart; the timestamp analogue of the off-by-one rival. The "
            "upper endpoint is taken at the START of the period's last day rather than "
            "at its last microsecond, so a faithful counterpart truncates the upper "
            "bound to midnight and every row timestamped later on that final day falls "
            "outside the inclusive range — a real behavioural defect on the carrier the "
            "shipped boundary test actually queries. AUDIT CORRECTION (measured): the "
            "prior claim that this drops 'the boundary rows the F2P test stores with a "
            "mid-afternoon time' is FALSE and is withdrawn. Those rows are not on the "
            "final day of the week-numbering period they belong to (the 2015 period ends "
            "Jan 3 2016, while the stored rows are late-December), so the truncated "
            "bound still admits them and the shipped assertions all hold. Retained as a "
            "SPEC-STRENGTH near-miss: it is the only rival isolating the timestamp "
            "obligation's upper-endpoint clause, which would otherwise be attacked only "
            "by rivals that also break the lower clause."
        ),
        "rationale": (
            "REJECTED by the SECOND clause of problem_spec_yearBoundsDatetime only "
            "(spec: next period's first day scaled, minus one microsecond; rival: this "
            "period's last day scaled). The lower clause is satisfied, so this is the "
            "near-miss that isolates the timestamp obligation's upper-endpoint clause — "
            "the only rival that does. Without it that clause is attacked only by rivals "
            "that also break the lower clause, and a rival wrong on the upper endpoint "
            "alone would verify unnoticed. Probes a third distinct `value`."
        ),
        "witness": _wit(
            "Datetime", "2019", "true",
            "upper endpoint only, microsecond carrier: the frozen bound is one "
            "microsecond before the next period, not the last day's midnight",
        ),
    },
    {
        "id": "weak-cal-lower-offbyone-date",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CAL_LOWER_OFF_DATE,
        "refinement": (
            "Added by the AUDIT to close a coverage gap, so it is a SPEC-STRENGTH rival "
            "and makes no F2P claim (the shipped boundary test queries the timestamp "
            "carrier, not this one). A faithful counterpart starts the ordinary-calendar "
            "period one day late, so a row dated on January 1st of the looked-up year is "
            "reported as NOT belonging to that year — a wrong answer at the period's "
            "first day, on the arm that serves every ordinary year lookup. The shipped "
            "suite happens not to store a January-1st row, which is precisely why this "
            "rival has to exist: without it the spec's pin on this endpoint rests on no "
            "isolating case, and a counterpart with this slip would verify unnoticed."
        ),
        "rationale": (
            "REJECTED by the FIRST clause of problem_spec_yearBoundsDate at "
            "isoYear=false only (spec: gregJan1 value; rival: gregJan1 value + 1). Every "
            "other cell of the surface — the upper clause on this arm, and both clauses "
            "on the isoYear=true arm — is byte-identical to frozen, so this is the "
            "narrowest possible attack on the ordinary-calendar LOWER endpoint of the "
            "day obligation, the cell no pre-existing rival isolated. If it VERIFIES => "
            "SPEC-TOO-WEAK on that clause."
        ),
        "witness": _wit(
            "Date", "2015", "false",
            "ordinary-calendar lower endpoint, isolated: the frozen bound is the "
            "period's first day, and this rival names the day after it",
        ),
    },
    {
        "id": "weak-cal-lower-offbyone-datetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CAL_LOWER_OFF_DT,
        "refinement": (
            "The same isolated slip at the timestamp carrier, and here it DOES bite the "
            "shipped surface in principle: the lower bound lands a whole day late, so a "
            "row timestamped anywhere on January 1st of the looked-up year drops out of "
            "an ordinary year lookup. Added by the AUDIT for the same reason as its date "
            "sibling — the timestamp obligation's ordinary-calendar lower clause was "
            "attacked only by the carrier-collapse rival, which breaks all four of its "
            "cells at once and so attests nothing about this one specifically."
        ),
        "rationale": (
            "REJECTED by the FIRST clause of problem_spec_yearBoundsDatetime at "
            "isoYear=false only (spec: gregJan1 value * usPerDay; rival: "
            "(gregJan1 value + 1) * usPerDay). The upper clause on this arm and both "
            "clauses on the isoYear=true arm are frozen-identical, so the rejection "
            "isolates one cell. Note this is NOT the day-scale rival's shape: the scale "
            "factor is correct here and only the day index is off, so a spec that pinned "
            "the carrier but not the endpoint would still admit it."
        ),
        "witness": _wit(
            "Datetime", "2015", "false",
            "ordinary-calendar lower endpoint on the microsecond carrier, isolated: the "
            "frozen bound is midnight of the period's first day, one day earlier",
        ),
    },
]


# The axiom lane is G-AX's job and this gate ignores AXIOM_TESTS. There is no consumed
# callee axiom in this bundle regardless: the two calendars' day-number computations
# are modeled DEEPLY as total integer arithmetic on the input year (A-references
# validated against the standard library by the differential conformance check), so
# there is no opaque callee for a witness to have to condition on and no axiom for
# this manifest to probe.
AXIOM_TESTS = []
