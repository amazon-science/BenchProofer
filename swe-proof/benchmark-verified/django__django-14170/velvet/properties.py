"""properties.py — G-PBT falsification battery for django__django-14170 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant produced by region surgery:
only text inside a ``-- impl-start`` / ``-- impl-end`` block is changed. No case
touches a ``prove_correct`` tactic body, so all three frozen proof scripts stay
byte-identical. The impl region is elided from the consumer spec view, so
``markers.same_spec`` holds by construction, all three ``prove_correct`` headers
survive, and no case adds an ``axiom`` / ``theorem`` / ``lemma`` / ``sorry`` /
``native_decide``.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — elaborates against the rival, fails against the frozen
solution).

Ported from the nagini sibling's battery, which is the design document for the
adversarial reasoning below. The porting ledger (what carried over, what did
not, and why) is in the handoff ``assessment``; the short version is that all 13
of the sibling's SPEC cases have a counterpart here, because this bundle happens
to model the SAME three-function surface the sibling contracts.

A later independent AUDIT re-derived every case against the real verifier and
added three things the port lacked: an instant-carrier off-by-one rival
(``rej-offby1-upper-datetime`` — the offset arithmetic had been pinned on the day
carrier only), a corrected mechanism note on ``admiss-self-assert`` (its tactic
retune was dead code and is gone; the assert's load-bearingness is now measured
rather than asserted), and a recorded SPEC-TOO-STRONG boundary at
``E7`` (see the footer).

A SECOND independent audit re-ran all 40 witness builds from scratch (10 rivals,
10 gold, 8 consistency probes, plus the checks below), ran the mandatory FORGERY
pair on every reject case, and added one case: ``admiss-f2p-point-datetime``,
because the admissibility lane covered only the DAY obligation and only
generically in ``value``. Its two other measurements are recorded where they
belong — the forgery pair in the WITNESS section, the ``assert``
two-directional discrimination in ``admiss-self-assert``'s own rationale — and
it found no hollow case and no spec hole. See the footer for its attack ledger.

---------------------------------------------------------------------------
DEFENDED SURFACE (read off the frozen Solution.lean)
---------------------------------------------------------------------------
THREE contracted methods, none carrying a ``require`` (both ``pre-conditions``
regions are empty), over two DISTINCT value carriers:

  yearBoundsDate     (value : Int) (isoYear : Bool)          -> List Int
  yearBoundsDatetime (value : Int) (isoYear : Bool)          -> List Int
  yearLookupBounds   (isDateTimeField isoYear : Bool) (value : Int) -> List Int

The load-bearing clause of each is the first ``ensures`` — a FULL-VALUE pin of
the returned two-element ``[lower, upper]`` list:

  out = dateBounds value isoYear
  out = datetimeBounds value isoYear
  out = (if isDateTimeField then datetimeBounds value isoYear
         else dateBounds value isoYear)

with the two remaining clauses of each method spelling the same pin out per
branch of the deciding flag. Those per-branch clauses are NOT independent
content — each is implied by the value pin plus the transparent ``def`` — but
they are attacked anyway: every rival below violates the branch clause for the
branch it corrupts as well as the top-level pin, so no clause of any obligation
goes unattacked.

The discriminating behaviour the spec must defend:
  * an ISO-8601 week-numbering year's range is delimited by the ISO landmarks,
    an ordinary calendar year's by the calendar landmarks — the two notions
    disagree near the new-year boundary, so picking the wrong family is a real
    divergence and not a reshuffle;
  * the ISO UPPER bound is the unit immediately BEFORE the next ISO year's first
    unit (the ``value + 1`` landmark minus one), not that landmark itself;
  * the endpoints are ORDERED ``[lower, upper]``;
  * the flag selecting ISO-vs-calendar must be FORWARDED by the dispatcher, on
    BOTH arms — a dispatcher that computes the routing correctly but passes a
    constant instead never reaches the ISO landmarks at all;
  * the two column types live in DIFFERENT carriers (day ordinals vs microsecond
    instants, mapping.md §2). Routing one column type's query to the other's
    bounds, or computing day-scale endpoints where instant-scale ones are
    required, is a spec violation — this is the carrier-collapse hole a prior
    audit of the sibling exploited when the model had only ONE carrier.

CARRIER NOTE (decisive for the witness route). All six landmark symbols are
``axiom``s — opaque ``Int -> Int`` with NO constraining lemma. So nothing
computes: ``dateBounds 2015 true`` is a list of two opaque terms, and the
``derive_tester_for`` + ``decide`` route is unavailable (extraction has no
executable code for an ``axiom``; the ``pure`` region is even marked
``noncomputable``). That does NOT empty the reject lane. An opaque term has no
VALUE to compute but is still a term one can QUANTIFY over, so every witness
below refutes the method's Hoare triple at a point described by HYPOTHESIS:
one assumption SEPARATING the two landmarks the rival confuses, e.g.

    (h : isoFirst 2015 ≠ gregJan1 2015)

which is exactly the sub-domain where that rival is wrong, and a stronger claim
than any single literal input could make. The reduction is
``unfold <method>; simp [triple, pure, dateBounds, datetimeBounds]`` (plus
``wp_bind, wp_pure`` for the dispatcher, whose body binds a callee method's
result monadically) and then ``omega`` on the residual disequality over the
opaque atoms. Every witness carries at MOST ONE hypothesis, about a PAIR of
distinct landmark terms, so the assumptions are trivially jointly satisfiable
and no witness can be a forgery-from-contradiction; the gate's consistency probe
was run on each and leaves ``False`` unsolved. Two witnesses
(``rej-offby1-upper-date`` / ``-datetime``) need NO hypothesis at all: they
separate a term from that same term minus one, which ``omega`` refutes outright.

Every witness in this file was SEEN to discriminate with two real builds: it
ELABORATES against its own rival (exit 0) and FAILS against the frozen solution
(exit 1). Re-derived independently by the audit, which additionally read every
gold-side failure and confirmed each is a SEMANTIC refusal rather than a
syntactic accident: ``omega`` reports the frozen solution's residual constraint
as SATISFIABLE, naming the two opaque landmark atoms it cannot separate
(e.g. ``a := gregJan1 2015``, ``b := isoFirst 2015``) — not an unknown
identifier, not a type error, not a stuck reduction. On the two hypothesis-free
witnesses the gold-side residual is stronger still: ``simp`` closes the frozen
postcondition outright and the goal ``omega`` is handed is literally ``False``.

FORGERY TEST (the check that decides whether a gold-side exit code carries any
information about the claim, run by the second audit on ALL TEN reject cases,
30 further builds). Two experiments per case:

  * FLIP THE CLAIM. Same file, same tactic script, ``¬ triple`` -> ``triple``:
    the witness now asserts gold is CORRECT at that point. Gold's error CHANGES,
    on every case — ``omega could not prove the goal: ... a := gregJan1 2015
    b := isoFirst 2015`` becomes ``No goals to be solved``, i.e. ``simp`` had
    already closed the positive triple and left ``omega`` nothing to do. And the
    flipped claim fails against the RIVAL with the original omega message. So
    the two sides' exit codes are not interchangeable and neither is a constant:
    the pair (rival 0 / gold 1) inverts to (rival 1 / gold 1-for-a-different-
    reason) when the claim inverts, which is exactly what a real refutation
    looks like and what a hollow one cannot do.
  * PROVE THE FLIP. The flipped claim with the trailing ``omega`` REMOVED
    elaborates against the frozen solution — exit 0, all ten cases. That is the
    positive statement of the same fact: gold provably SATISFIES its obligation
    at each witness's point, by ``simp`` alone, which is why the negation cannot
    be proven there. Gold's failure is a satisfied spec, not a stuck tactic.

Two more independent checks, same audit. (i) The residual goal handed to
``omega`` was read on both sides by dropping the final tactic: on gold it is
literally ``⊢ False`` under a satisfiable hypothesis (or bare ``⊢ False`` for the
two unconditioned witnesses), while on the rival it is the concrete
disequality over named landmark atoms (e.g. ``⊢ ¬gregDec31 2004 = isoFirst 2005
- 1``, ``⊢ ¬isoFirst 2010 = isoFirst 2010 - 1``) — different goals, so different
verdicts. (ii) Every witness was ALSO built against a CORRECT RESHAPE of all
three impls at once (``cond`` at the day site, a higher-order pair constructor
at the instant site, ``= true`` at the dispatcher; that impl verifies, exit 0)
and all ten FAIL there exactly as on gold. So no witness discriminates
impl SHAPE rather than behaviour, which is the failure mode a tactic-tuned
backend produces by default.

Each witness's hypothesis was additionally checked to be TRUE on the real
carrier, not merely satisfiable in the model: all eight conditioned witnesses'
disequalities hold when the landmarks are evaluated with the platform date
library (the four years used — 2004, 2009, 2015, 2020 — each have an ISO year
that starts in the PREVIOUS December, so the two notions really do disagree
there). A witness whose hypothesis were satisfiable in the opaque model but
false in reality would refute on an empty sub-domain; none is.

---------------------------------------------------------------------------
BINDER COVERAGE (the criterion the case count does not capture)
---------------------------------------------------------------------------
Every INPUT BINDER of every obligation is varied across the reject witnesses, so
no rival could abuse a binder the battery holds pinned:

  yearBoundsDate      value   2015 / 2004 / 2015 / 2009    isoYear  true, false
  yearBoundsDatetime  value   2020 / 2020 / 2015            isoYear  true, false
  yearLookupBounds    value   2015 / 2004 / 2020
                      isDateTimeField  false / true / true
                      isoYear          true / false / true

The years are not decorative: 2004, 2009, 2015 and 2020 are the boundary years
where the two notions of "year" genuinely disagree (the long ISO years), and
2015 is the year the newly-covered behaviour turns on.

---------------------------------------------------------------------------
ADVERSARIAL READ of the sibling's weakness classes on this carrier
---------------------------------------------------------------------------
  * FRAME / PERMISSION-MUTATION — VACUOUS, and vacuous in the sibling too: it
    records that its inputs are scalar value types with no read-only fractional
    heap permission and no input predicate, so the class does not apply even
    there. On this backend it could not apply regardless: Lean and Velvet are
    referentially transparent, every parameter is an immutable value, no binder
    is ``mut``, there is no heap and no aliasing. No substitute is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an ATTACK, exactly as in the sibling
    (its "grounded-oracle path"). ``dateBounds`` / ``datetimeBounds`` are
    transparent ``def``s over the method's own arguments that unfold to the very
    landmark applications the impl makes, so echoing one is the CORRECT answer,
    not a cheat. There is no wrong echo to exploit. The sibling therefore ships
    the echo as a positive CONTROL rather than a rival, and so does this port
    (``pos-grounded-oracle-echo-*``).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * CONTROL-FLOW / PARTIAL-DOMAIN / VALUE — heavily exercised: wrong landmark
    family, mixed families, transposed endpoints, off-by-one upper bound, a
    dispatcher that drops the forwarded flag (on both arms, and on one arm
    only), a dispatcher that swaps the column-type routing, and a carrier
    collapse.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The sibling carries two probes over
the real platform date/datetime landmark callees; that is G-AX's job
(``axiom_check.py`` / ``mapping.md`` §3) and this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14170"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region-surgery anchors: the three frozen impl bodies, verbatim — everything
# strictly BETWEEN each method's `-- impl-start` / `-- impl-end`. Each anchor
# lies WHOLLY inside its own impl region and is unique in Solution.lean (both
# asserted at load), so no edit below can reach the frozen spec. The `let out`
# / `return out` frame is part of every anchor on purpose: the bare landmark
# expressions also occur in the spec-visible `pure` region and the `ensures`
# clauses, so an anchor without the frame would not be unique.
# ---------------------------------------------------------------------------
_IMPL_DATE = (
    "    let out : List Int :=\n"
    "      if isoYear then\n"
    "        [isoFirst value, isoFirst (value + 1) - 1]\n"
    "      else\n"
    "        [gregJan1 value, gregDec31 value]\n"
    "    return out"
)

_IMPL_DT = (
    "    let out : List Int :=\n"
    "      if isoYear then\n"
    "        [dtIsoFirst value, dtIsoFirst (value + 1) - 1]\n"
    "      else\n"
    "        [dtJan1 value, dtDec31 value]\n"
    "    return out"
)

_IMPL_DISPATCH = (
    "    let out ← if isDateTimeField then\n"
    "        yearBoundsDatetime value isoYear\n"
    "      else\n"
    "        yearBoundsDate value isoYear\n"
    "    return out"
)

# NO case in this file touches a `prove_correct` tactic body. Every variant is
# pure impl-region surgery, so all three frozen proof scripts stay byte-identical
# and the only thing under test is whether the frozen obligation still closes.
for _a in (_IMPL_DATE, _IMPL_DT, _IMPL_DISPATCH):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted or not unique: {_a[:48]!r}")


def _date(body):
    return _swap(_BASE, _IMPL_DATE, body)


def _dt(body):
    return _swap(_BASE, _IMPL_DT, body)


def _dispatch(body):
    return _swap(_BASE, _IMPL_DISPATCH, body)


# ---------------------------------------------------------------------------
# WITNESS BUILDERS.
#
# The spec is a `method` CONTRACT over an entirely opaque landmark carrier, so
# the tester route (`derive_tester_for` -> `<name>Tester args = false`, closed by
# `decide`) is unavailable: the landmarks are `axiom`s with no executable code
# and the `pure` region is `noncomputable`. Each witness instead refutes the
# method's Hoare triple DIRECTLY, at a point described by hypothesis, in a file
# whose `prove_correct` blocks the gate has stripped — so no tactic script can
# mask the verdict.
#
# The full postcondition (all three `ensures` conjoined) is restated at the
# probed point, so the witness refutes the WHOLE obligation, not a chosen
# fragment. `triple` / `pure` / `wp_bind` / `wp_pure` all come from the frozen
# `Velvet.Std` import; `dateBounds` / `datetimeBounds` are the frozen pure defs.
# No banned token (sorry / admit / native_decide / axiom / opaque) appears, and
# no name is used that the frozen solution does not already declare.
#
# `hyp` is at most ONE assumption, always a DISEQUALITY BETWEEN TWO DISTINCT
# landmark terms — satisfiable by construction, so the consistency probe cannot
# derive `False` from it. `None` means the refutation needs no assumption.
# ---------------------------------------------------------------------------
def _w_date(value, iso, hyp):
    head = f"    ({hyp})\n" if hyp else ""
    return (
        f"example\n{head}"
        f"    : ¬ triple (l := Prop) True\n"
        f"      (yearBoundsDate {value} {iso})\n"
        f"      (fun out => out = dateBounds {value} {iso}\n"
        f"        ∧ ({iso} = true  → out = [isoFirst {value}, "
        f"isoFirst ({value} + 1) - 1])\n"
        f"        ∧ ({iso} = false → out = [gregJan1 {value}, "
        f"gregDec31 {value}])) := by\n"
        f"  unfold yearBoundsDate\n"
        f"  simp [triple, pure, dateBounds]\n"
        f"  omega\n"
    )


def _w_dt(value, iso, hyp):
    head = f"    ({hyp})\n" if hyp else ""
    return (
        f"example\n{head}"
        f"    : ¬ triple (l := Prop) True\n"
        f"      (yearBoundsDatetime {value} {iso})\n"
        f"      (fun out => out = datetimeBounds {value} {iso}\n"
        f"        ∧ ({iso} = true  → out = [dtIsoFirst {value}, "
        f"dtIsoFirst ({value} + 1) - 1])\n"
        f"        ∧ ({iso} = false → out = [dtJan1 {value}, "
        f"dtDec31 {value}])) := by\n"
        f"  unfold yearBoundsDatetime\n"
        f"  simp [triple, pure, datetimeBounds]\n"
        f"  omega\n"
    )


def _w_lookup(is_dt, iso, value, hyp):
    # The dispatcher's body binds a callee method's result with `←`, so the
    # weakest precondition goes through a monadic bind: `wp_bind` / `wp_pure`
    # are what reduce it to the callee's returned list.
    head = f"    ({hyp})\n" if hyp else ""
    return (
        f"example\n{head}"
        f"    : ¬ triple (l := Prop) True\n"
        f"      (yearLookupBounds {is_dt} {iso} {value})\n"
        f"      (fun out => out = (if {is_dt} then datetimeBounds {value} {iso}\n"
        f"                        else dateBounds {value} {iso})\n"
        f"        ∧ ({is_dt} = true  → out = datetimeBounds {value} {iso})\n"
        f"        ∧ ({is_dt} = false → out = dateBounds {value} {iso})) := by\n"
        f"  unfold yearLookupBounds yearBoundsDate yearBoundsDatetime\n"
        f"  simp [triple, pure, dateBounds, datetimeBounds, wp_bind, wp_pure]\n"
        f"  omega\n"
    )


SPEC_TESTS = []

# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
# that MUST verify. If a faithful correct impl is rejected, the spec is
# SPEC-TOO-STRONG on the SHAPE of the impl rather than on its behaviour. Each
# keeps the returned value identical on every input and reshapes only the
# executable surface, so the frozen `loom_solve` still discharges the
# byte-identical obligation with no proof authoring.
# ===========================================================================

SPEC_TESTS.append({
    "id": "pos-reorder-date",
    "kind": "soundness",
    "expect": "verify",
    "module": _date(
        "    let out : List Int :=\n"
        "      if !isoYear then\n"
        "        [gregJan1 value, gregDec31 value]\n"
        "      else\n"
        "        [isoFirst value, isoFirst (value + 1) - 1]\n"
        "    return out"),
    "rationale": "Ports the sibling's `pos-reorder-date`. The deciding flag is "
                 "tested NEGATED, so the two arms appear in the opposite order "
                 "and the ordinary-calendar case is written first. Same value "
                 "map on every (value, isoYear); the load-bearing clause is a "
                 "direct full-value pin (no loop invariant, no lemma), so a "
                 "faithful correct impl MUST verify. If it does not => "
                 "SPEC-TOO-STRONG.",
})

SPEC_TESTS.append({
    "id": "pos-grounded-oracle-echo-date",
    "kind": "soundness",
    "expect": "verify",
    "module": _date("    let out : List Int := dateBounds value isoYear\n"
                    "    return out"),
    "rationale": "Ports the sibling's `pos-grounded-oracle-echo-date` (its "
                 "grounded-oracle path). The postcondition's oracle is a "
                 "TRANSPARENT `def` over the method's own arguments that unfolds "
                 "to exactly the landmark applications the frozen impl makes, so "
                 "echoing it is the CORRECT answer and must verify — there is no "
                 "wrong echo to exploit, which is why this is a control and not "
                 "a rival. Guards against the spec being satisfiable only by one "
                 "particular spelling of the right answer.",
})

SPEC_TESTS.append({
    "id": "pos-grounded-oracle-echo-datetime",
    "kind": "soundness",
    "expect": "verify",
    "module": _dt("    let out : List Int := datetimeBounds value isoYear\n"
                  "    return out"),
    "rationale": "Ports the sibling's `pos-grounded-oracle-echo-datetime`: the "
                 "same grounded-oracle echo at the OTHER carrier's site, whose "
                 "oracle unfolds to the instant-scale landmarks. Must verify.",
})

SPEC_TESTS.append({
    "id": "pos-endpoint-locals-date",
    "kind": "soundness",
    "expect": "verify",
    "module": _date(
        "    let lo : Int := if isoYear then isoFirst value else gregJan1 value\n"
        "    let hi : Int :=\n"
        "      if isoYear then isoFirst (value + 1) - 1 else gregDec31 value\n"
        "    let out : List Int := [lo, hi]\n"
        "    return out"),
    "rationale": "A THIRD impl shape for the same obligation, beyond the two the "
                 "sibling ships: the flag is consulted once PER ENDPOINT and the "
                 "two endpoints are bound to locals before the list is assembled, "
                 "instead of one branch selecting a whole list literal. Chosen "
                 "because it dissolves the branch structure the frozen proof "
                 "script sees while preserving the value map exactly — the "
                 "sharpest cheap probe for a spec that accidentally constrains "
                 "control flow rather than behaviour. Must verify.",
})

SPEC_TESTS.append({
    "id": "pos-dispatch-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _dispatch(
        "    let out ← if !isDateTimeField then\n"
        "        yearBoundsDate value isoYear\n"
        "      else\n"
        "        yearBoundsDatetime value isoYear\n"
        "    return out"),
    "rationale": "Ports the sibling's `pos-dispatch-reorder`: the column-type "
                 "branch is tested negated so the arms are transposed, while each "
                 "column type still reaches its OWN carrier's bounds and the "
                 "ISO-vs-calendar flag is still forwarded verbatim on both arms. "
                 "A faithful correct dispatcher must verify, else "
                 "SPEC-TOO-STRONG.",
})

# ===========================================================================
# ADMISSIBILITY — the contract is satisfiable, and by a gold-shaped computation.
# Both `pre-conditions` regions are EMPTY (no `require`), so the classic
# "a normal input is admitted" probe cannot fail for a precondition reason; the
# residual risk on a precondition-free domain is that the three conjoined
# `ensures` are jointly satisfiable AT ALL. The sibling's `admiss-self-assert`
# ports directly, because Velvet has an in-impl `assert` gadget: the gold value
# map plus an explicit in-region assertion that the pinned post-image holds.
# ===========================================================================

SPEC_TESTS.append({
    "id": "admiss-self-assert",
    "kind": "admissibility",
    "expect": "verify",
    "module": _date(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [isoFirst value, isoFirst (value + 1) - 1]\n"
        "      else\n"
        "        [gregJan1 value, gregDec31 value]\n"
        "    assert out = dateBounds value isoYear\n"
        "    return out"),
    "rationale": "Ports the sibling's `admiss-self-assert`. The gold value map "
                 "with an EXPLICIT in-impl `assert` that the pinned post-image "
                 "holds at an arbitrary in-domain input — the direct counterpart "
                 "of the sibling's in-body `Assert(...)` on the endpoints. Since "
                 "there is no `require`, this confirms the domain is total and "
                 "the conjoined clauses are jointly satisfiable by a real "
                 "computation on BOTH arms of the flag (else SPEC-UNSATISFIABLE / "
                 "PRECOND-TOO-STRONG). The `assert` is LOAD-BEARING and was "
                 "measured so: replacing it with a false claim at the same point "
                 "(`out = [0, 0]`, `out = dateBounds (value + 1) isoYear`, "
                 "`out = dateBounds value (!isoYear)`, `(1 : Int) = 2`) makes the "
                 "build FAIL, so the assertion really is discharged against the "
                 "impl's post-image rather than skipped. The frozen "
                 "`prove_correct yearBoundsDate` script is left BYTE-IDENTICAL: "
                 "the assertion's side goal is closed by the frozen `loom_solve` "
                 "itself (an earlier revision of this case appended "
                 "`all_goals grind`, which the verifier then reported as "
                 "`'all_goals grind' tactic does nothing` / `this tactic is never "
                 "executed` — the retune was dead, so the case now touches no "
                 "tactic body at all and nothing is assumed). A SECOND audit "
                 "additionally measured the assert's discrimination in BOTH "
                 "directions, because a false assert here fails with Loom's "
                 "`Failed to parse an assertion without names: <the claim>` — a "
                 "message that reads like a SYNTAX complaint and would be the "
                 "obvious hollow-case shape if it did not track truth. It does: "
                 "six TRUE claims of unrelated spellings all build (exit 0) — "
                 "`(1 : Int) = 1`, `out = out`, `out.length = 2`, the pin written "
                 "inline as the `if`-expression, and two CONCRETE-year claims "
                 "(`dateBounds 2015 true = [isoFirst 2015, isoFirst (2015 + 1) - "
                 "1]`, and the instant-carrier conjunction) — while four FALSE "
                 "claims all fail (exit 1) with that same message, `(0 : Int) = "
                 "1`, `out.length = 3`, `out = datetimeBounds value isoYear`, and "
                 "`dateBounds 2015 true = [gregJan1 2015, gregDec31 2015]`. So the "
                 "text is just how Loom reports an assertion goal it could not "
                 "close, and exit code tracks the CLAIM, not its shape.",
})

SPEC_TESTS.append({
    "id": "admiss-f2p-point-datetime",
    "kind": "admissibility",
    "expect": "verify",
    "module": _dt(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [dtIsoFirst value, dtIsoFirst (value + 1) - 1]\n"
        "      else\n"
        "        [dtJan1 value, dtDec31 value]\n"
        "    assert out = datetimeBounds value isoYear\n"
        "      ∧ datetimeBounds 2015 true = [dtIsoFirst 2015, dtIsoFirst (2015 + 1) - 1]\n"
        "      ∧ datetimeBounds 2015 false = [dtJan1 2015, dtDec31 2015]\n"
        "    return out"),
    "rationale": "Added by the second audit: the admissibility lane held only ONE "
                 "case, generic in `value` and on the DAY obligation, so the "
                 "instant obligation had no admissibility probe and no obligation "
                 "had one at a CONCRETE point. On a total carrier with no "
                 "`require`, PRECOND-TOO-STRONG cannot present as a rejected "
                 "precondition; the analogue is the obligation being "
                 "unsatisfiable at exactly an F2P-shaped input, and that is what "
                 "this discharges — by evaluation, as a `have`-style in-region "
                 "`assert`, BEFORE the frozen obligation closes verbatim. The "
                 "point is the boundary year the newly-covered behaviour turns "
                 "on, taken on the instant carrier because the rows the new "
                 "behaviour filters are timestamp-typed, and BOTH arms of the "
                 "flag are pinned there at once — so the conjoined clauses are "
                 "shown jointly satisfiable at the exact input that matters "
                 "rather than only generically. Discrimination measured: the same "
                 "case with the ISO arm's claim replaced by the CALENDAR "
                 "landmarks (`datetimeBounds 2015 true = [dtJan1 2015, dtDec31 "
                 "2015]`) FAILS (exit 1), so the concrete conjunct is "
                 "load-bearing and not decoration.",
})

# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries a machine-checked refutation `witness` at its
# OWN point (no two rivals lean on the same evidence) and the `refinement`
# argument for why its faithful real counterpart would NOT resolve the failing
# test, so a rival that verified would be a true verify-does-not-imply-resolve
# break rather than an artifact of a reshaped impl.
# ===========================================================================

SPEC_TESTS.append({
    "id": "rej-wrong-calendar-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _date("    let out : List Int := [gregJan1 value, gregDec31 value]\n"
                    "    return out"),
    "witness": _w_date(2015, "true", "h : isoFirst 2015 ≠ gregJan1 2015"),
    "refinement": "Ports the sibling's `rej-wrong-calendar-date`, the headline "
                  "rival: it is the behaviour as it stood BEFORE the change — the "
                  "ISO-8601 branch simply absent, so a week-numbering-year query "
                  "is answered with ordinary calendar landmarks. Its faithful "
                  "real counterpart is therefore the no-op patch, and the "
                  "newly-covered boundary test still mis-buckets the rows that "
                  "sit in the disagreement window between the two notions of "
                  "year (a late-December row belonging to the NEXT ISO year is "
                  "excluded by that year's calendar range). It does not resolve.",
    "rationale": "Rejected by the value pin `out = dateBounds value isoYear` and "
                 "by the `isoYear = true` branch clause: with the flag set the "
                 "spec demands the ISO landmarks and this returns the calendar "
                 "ones. PARTIAL-DOMAIN — correct on the whole non-ISO subdomain, "
                 "which is why the witness is placed at `isoYear = true`. Witness "
                 "at (value=2015, isoYear=true), conditioned on the two lower "
                 "landmarks of 2015 differing (they do — 2015 is a boundary year "
                 "where the notions disagree); SEEN to discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-wrong-calendar-datetime",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _dt("    let out : List Int := [dtJan1 value, dtDec31 value]\n"
                  "    return out"),
    "witness": _w_dt(2020, "true", "h : dtIsoFirst 2020 ≠ dtJan1 2020"),
    "refinement": "Ports the sibling's `rej-wrong-calendar-datetime`: the same "
                  "pre-change behaviour at the OTHER column type — always the "
                  "ordinary calendar instants, no ISO branch. The rows the "
                  "newly-covered boundary test filters live in a timestamp-typed "
                  "column, so this is precisely the tree that fails it, and its "
                  "faithful counterpart does not resolve.",
    "rationale": "Rejected by `out = datetimeBounds value isoYear` and the "
                 "`isoYear = true` branch clause at the instant carrier. Probes a "
                 "DIFFERENT obligation and a DIFFERENT year (2020) from the "
                 "date-carrier rival above, so the two do not share evidence. "
                 "Witness at (value=2020, isoYear=true) conditioned on the two "
                 "lower instant landmarks differing; SEEN to discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-mixed-calendar-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _date(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [isoFirst value, gregDec31 value]\n"
        "      else\n"
        "        [gregJan1 value, gregDec31 value]\n"
        "    return out"),
    "witness": _w_date(2004, "true", "h : gregDec31 2004 ≠ isoFirst 2005 - 1"),
    "refinement": "Ports the sibling's `rej-mixed-calendar-date`: the ISO branch "
                  "picks the right LOWER landmark but keeps the ordinary "
                  "calendar's last day as the upper one. Faithfully realised this "
                  "is a half-done change — the range starts correctly and ends in "
                  "the wrong place, so a week-numbering year that runs on past "
                  "the calendar year's end (or stops before it) bounds the wrong "
                  "row set and the newly-covered boundary test fails on the upper "
                  "edge. It does not resolve.",
    "rationale": "Rejected by the value pin and by the `isoYear = true` branch "
                 "clause on the UPPER endpoint specifically: the spec requires "
                 "the unit before the next ISO year's first unit, this returns "
                 "the calendar year's last day. A NEAR-MISS relative to the "
                 "wrong-calendar rival — it agrees with the spec on the lower "
                 "endpoint everywhere — so its witness is placed at the upper "
                 "endpoint and at a DIFFERENT year (2004, a long ISO year, where "
                 "the two upper landmarks demonstrably differ). SEEN to "
                 "discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-swapped-endpoints-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _date(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [isoFirst (value + 1) - 1, isoFirst value]\n"
        "      else\n"
        "        [gregDec31 value, gregJan1 value]\n"
        "    return out"),
    "witness": _w_date(2015, "false", "h : gregJan1 2015 ≠ gregDec31 2015"),
    "refinement": "Ports the sibling's `rej-swapped-endpoints-date`: the two "
                  "endpoints are TRANSPOSED, so the emitted range runs from the "
                  "later unit to the earlier one. Faithfully realised, an "
                  "inclusive range with its bounds reversed selects NO rows for "
                  "any year-valued query at all — it fails the newly-covered "
                  "boundary test and regresses every pre-existing year-lookup "
                  "test as well. It does not resolve.",
    "rationale": "Rejected by the value pin: the spec fixes the ORDER of the "
                 "two-element carrier as `[lower, upper]`, and this returns "
                 "`[upper, lower]`. The only rival that attacks the ORDERING "
                 "clause rather than the choice of landmark family, and the only "
                 "one refuted on the NON-ISO branch of this obligation — which is "
                 "why its witness sits at `isoYear = false`, the value every "
                 "other date-carrier witness holds at `true`. Conditioned on the "
                 "year's first and last day differing; SEEN to discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-offby1-upper-date",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _date(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [isoFirst value, isoFirst (value + 1)]\n"
        "      else\n"
        "        [gregJan1 value, gregDec31 value]\n"
        "    return out"),
    "witness": _w_date(2009, "true", None),
    "refinement": "Ports the sibling's `rej-offby1-upper-date`: the ISO upper "
                  "bound is the next week-numbering year's FIRST unit instead of "
                  "the unit immediately before it — the minus-one step dropped. "
                  "Faithfully realised, the inclusive range LEAKS that one "
                  "boundary row, so a query for one week-numbering year also "
                  "matches the opening row of the next; the newly-covered "
                  "boundary test fails with an extra row. It does not resolve.",
    "rationale": "Rejected by the value pin and the `isoYear = true` branch "
                 "clause on the upper endpoint. The narrowest rival in the "
                 "battery — it diverges from the spec on a SINGLE unit — which is "
                 "exactly why it is worth carrying: a spec that pinned only the "
                 "landmark FAMILY and not the offset arithmetic would admit it. "
                 "Its witness is the strongest in the file: it needs NO "
                 "hypothesis, because separating a term from that same term minus "
                 "one is unconditional, so the refutation holds at EVERY year "
                 "rather than on a conditioned sub-domain (stated at 2009, a "
                 "fourth distinct year). SEEN to discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-offby1-upper-datetime",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _dt(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [dtIsoFirst value, dtIsoFirst (value + 1)]\n"
        "      else\n"
        "        [dtJan1 value, dtDec31 value]\n"
        "    return out"),
    "witness": _w_dt(2020, "true", None),
    "refinement": "The off-by-one upper bound at the INSTANT carrier — the "
                  "counterpart of `rej-offby1-upper-date` on the other column "
                  "type, beyond what the sibling ships. The ISO upper bound is "
                  "the next week-numbering year's FIRST instant rather than the "
                  "instant immediately before it. Faithfully realised, the "
                  "inclusive range leaks that one boundary instant, so a query "
                  "for one week-numbering year also matches a row timestamped at "
                  "exactly the next ISO year's opening microsecond. It does not "
                  "resolve.",
    "rationale": "Added by audit. The battery pinned the minus-one-unit offset "
                 "arithmetic only on the DAY carrier: every instant-carrier rival "
                 "attacked the landmark FAMILY (`rej-wrong-calendar-datetime`, "
                 "`rej-carrier-collapse-datetime`) or the dispatch "
                 "(`rej-dispatch-*`), so a spec that pinned the instant-scale "
                 "family without its offset would have gone unprobed on this "
                 "obligation. Rejected by `out = datetimeBounds value isoYear` "
                 "and the `isoYear = true` branch clause on the upper endpoint. "
                 "Like its day-carrier twin the witness needs NO hypothesis — "
                 "separating a term from that same term minus one is "
                 "unconditional — so the refutation holds at every year (stated "
                 "at 2020). Measured: rival build exit 0, frozen-solution build "
                 "exit 1 with `omega could not prove the goal`.",
})

SPEC_TESTS.append({
    "id": "rej-carrier-collapse-datetime",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _dt(
        "    let out : List Int :=\n"
        "      if isoYear then\n"
        "        [isoFirst value, isoFirst (value + 1) - 1]\n"
        "      else\n"
        "        [gregJan1 value, gregDec31 value]\n"
        "    return out"),
    "witness": _w_dt(2015, "false", "h : dtJan1 2015 ≠ gregJan1 2015"),
    "refinement": "Ports the sibling's `rej-carrier-collapse-datetime`, the case "
                  "a prior audit of the sibling exploited when its model had only "
                  "ONE carrier. The timestamp-typed site selects the correct "
                  "landmark FAMILY and the correct offset arithmetic, but at "
                  "DAY granularity. Faithfully realised, the bounds for a "
                  "timestamp column become whole days, so the upper bound loses "
                  "the final day's interior — rows timestamped inside that last "
                  "day fall outside the range and the year-lookup behaviour "
                  "breaks. It does not resolve.",
    "rationale": "Rejected by `out = datetimeBounds value isoYear`: the spec "
                 "requires the instant-scale landmarks and this returns the "
                 "day-scale ones. The two landmark families are DISTINCT opaque "
                 "symbols, so nothing lets the verifier conflate them — this is "
                 "the case that certifies the two-carrier model does not "
                 "collapse. Witness at (value=2015, isoYear=false) conditioned on "
                 "the day-scale and instant-scale lower landmarks of the same "
                 "year differing (they must: mapping.md §2 fixes different units "
                 "and origins). Placed on the NON-ISO branch, and so probes the "
                 "instant obligation's `isoYear = false` arm that the other "
                 "datetime rival leaves at `true`. SEEN to discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-dispatch-drops-flag",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _dispatch(
        "    let out ← if isDateTimeField then\n"
        "        yearBoundsDatetime value false\n"
        "      else\n"
        "        yearBoundsDate value false\n"
        "    return out"),
    "witness": _w_lookup("false", "true", 2015,
                         "h : isoFirst 2015 ≠ gregJan1 2015"),
    "refinement": "Ports the sibling's `rej-dispatch-drops-flag`: the dispatcher "
                  "routes by column type correctly but forwards a CONSTANT "
                  "ordinary-calendar flag instead of the one it was given. This "
                  "models the change made half-way — the ISO-vs-calendar "
                  "distinction is determined at the dispatch site but never "
                  "passed on to the bounds computation — so the ISO branch is "
                  "unreachable and a week-numbering query still gets calendar "
                  "bounds. The newly-covered boundary test fails exactly as "
                  "before. It does not resolve.",
    "rationale": "Rejected by `yearLookupBounds`'s value pin and its "
                 "`isDateTimeField = false` branch clause: the callee returns the "
                 "ordinary-calendar bounds, which differ from the required ones "
                 "whenever the flag is set. This is the only rival attacking the "
                 "FORWARDING of the flag rather than its interpretation, and the "
                 "reason the dispatcher's `isoYear` binder is load-bearing at all. "
                 "Witness at (isDateTimeField=false, isoYear=true, value=2015).",
})

SPEC_TESTS.append({
    "id": "rej-dispatch-drops-flag-datetime-arm",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _dispatch(
        "    let out ← if isDateTimeField then\n"
        "        yearBoundsDatetime value false\n"
        "      else\n"
        "        yearBoundsDate value isoYear\n"
        "    return out"),
    "witness": _w_lookup("true", "true", 2020,
                         "h : dtIsoFirst 2020 ≠ dtJan1 2020"),
    "refinement": "A NEAR-MISS refinement of the previous rival, beyond what the "
                  "sibling ships. The flag is forwarded correctly on the "
                  "date-typed arm and dropped ONLY on the timestamp-typed one. "
                  "Faithfully realised this is the change applied to one of the "
                  "two bounds helpers and missed on the other — a plausible "
                  "partial edit, and the more dangerous one here, because the "
                  "rows the newly-covered boundary test filters live in a "
                  "timestamp-typed column: that test still fails while the "
                  "date-typed path looks fixed. It does not resolve.",
    "rationale": "Rejected by the `isDateTimeField = true` branch clause. Carried "
                 "as its own case rather than folded into "
                 "`rej-dispatch-drops-flag` because it agrees with the spec over "
                 "strictly MORE of the domain (the entire date-typed arm), so "
                 "that rival's witness would not refute it and its own "
                 "sub-domain claim would go undemonstrated. Its witness "
                 "therefore sits on the OPPOSITE arm — (isDateTimeField=true, "
                 "isoYear=true, value=2020) — which also varies all three of the "
                 "dispatcher's binders against the two other dispatch witnesses. "
                 "SEEN to discriminate.",
})

SPEC_TESTS.append({
    "id": "rej-dispatch-routing-swap",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _dispatch(
        "    let out ← if isDateTimeField then\n"
        "        yearBoundsDate value isoYear\n"
        "      else\n"
        "        yearBoundsDatetime value isoYear\n"
        "    return out"),
    "witness": _w_lookup("true", "false", 2004,
                         "h : dtJan1 2004 ≠ gregJan1 2004"),
    "refinement": "Ports the sibling's `rej-dispatch-routing-swap`: each column "
                  "type is routed to the OTHER one's bounds, with the flag "
                  "forwarded faithfully. Faithfully realised, the emitted range "
                  "parameters get the wrong type and granularity for the column "
                  "being compared — whole days against a timestamp column "
                  "truncate away each day's interior, and instants against a "
                  "date column over-specify it — so the year-lookup behaviour "
                  "breaks. It does not resolve.",
    "rationale": "Rejected by `yearLookupBounds`'s value pin and its "
                 "`isDateTimeField = true` branch clause: for a timestamp-typed "
                 "column the spec requires the instant-scale bounds and the "
                 "swapped routing returns the day-scale ones. Together with "
                 "`rej-carrier-collapse-datetime` this closes the "
                 "carrier-collapse hole from BOTH ends — at the dispatch site "
                 "and at the endpoint site. Witness at (isDateTimeField=true, "
                 "isoYear=false, value=2004), which is the only dispatch witness "
                 "on the `isoYear = false` arm, conditioned on the two carriers' "
                 "landmarks for the same year differing. SEEN to discriminate.",
})


# ===========================================================================
# AXIOM lane — dropped by design (the porting map): the axiom lane is G-AX's
# job and this gate ignores AXIOM_TESTS. The sibling's two probes over the real
# platform landmark callees have counterparts in axiom_check.py / mapping.md §3.
# ===========================================================================
AXIOM_TESTS = []


# ===========================================================================
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# RETRACTED IN FULL (what stood in the lines below before). This footer used to
# continue with the opposite disposition: that the bundle is "one of the 401
# velvet bundles" whose semantics claim an `ensures` clause only of TERMINATING
# runs, so an impl that never terminates satisfies all three clauses VACUOUSLY
# and verifies; that this was MEASURED on THIS bundle with a diverging prefix
# returning the unambiguously wrong `[0, 0]` at exit 0; and that the FROZEN SPEC
# therefore ADMITS the rival, an open escalated hole closable only by a semantics
# change. All of it is withdrawn. Claiming a postcondition only of terminating
# runs is the PARTIAL rule, and no velvet bundle is partial: all 500 set
# `set_option loom.semantics.termination "total"`, and in Loom that option is
# itself what opens `TotalCorrectness` scope, so the setting and the `open`
# cannot disagree. The census of a `partial` cohort against a `total` one has no
# referent. Under `total` a postcondition is claimed of ALL runs and every loop
# owes a measure that STRICTLY DECREASES; the rebuilt measurements are in the
# block above, where a spin prefix CARRYING a constant `decreasing` clause is
# REJECTED on the measure's own descent goal and one without the clause is
# refused earlier still by the elaborator. There is no hole here, nothing
# escalated, and no verify-does-not-imply-resolve break in this class.
#
# The class still ships no `expect="reject"` case, for a witness-path reason
# rather than a spec one: a reject case needs a witness that ELABORATES against
# the rival, and a diverging rival's module does not compile at all (the descent
# obligation fails at the `method` itself, upstream of any appended tester), so
# the case would score MALFORMED instead of rejecting. The sibling battery
# That is the shape with NO measure. A rival that CARRIES a measure which does
# not decrease is refused at the ``prove_correct`` site instead, which the
# witness file strips, so that module does elaborate; but its post-image is
# then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
# ``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise
# to a value a concrete-input tester can decide. Both shapes therefore land
# ``witness-unproven``.
# carries no divergence case either. The notice is kept rather than the text
# simply deleted, so a reader who saw the earlier claim can see it withdrawn.
# ===========================================================================


# ===========================================================================
# AUDIT LEDGER — new attacks run against the FROZEN spec, and what they found.
#
# Attack D (SPEC-TOO-WEAK probe): 8 NEW wrong impls the battery did not contain,
# aimed at what the shipped rivals leave unattacked. ALL 8 were REJECTED (build
# exit 1), so no spec hole in the value lane:
#   - ISO LOWER bound shifted by one (`isoFirst value - 1`) — the mirror of the
#     upper-bound off-by-one, which nothing had probed;
#   - ISO span widened to two years (`isoFirst (value + 2) - 1`);
#   - dispatcher ignoring the column-type flag entirely (always the instant
#     bounds) — the routing lane's degenerate case;
#   - instant-carrier ISO/calendar arms TRANSPOSED (flag interpreted backwards,
#     as opposed to merely dropped);
#   - a SINGLETON list (`[isoFirst value]`) — probes that the two-element carrier
#     shape is pinned and not just its contents;
#   - instant upper bound derived from `value` instead of `value + 1`;
#   - dispatcher NEGATING the forwarded flag on both arms;
#   - date bounds computed for the WRONG year (`dateBounds (value + 1) isoYear`).
#   One of these (the instant-carrier upper-bound off-by-one) was promoted to a
#   shipped case as `rej-offby1-upper-datetime`; it was the one genuine coverage
#   gap the probe set exposed.
#
# Attack E (SPEC-TOO-STRONG probe): 8 NEW correct reshapes. 7 VERIFIED (exit 0):
# the dispatcher fully INLINED (both callees dissolved, so the monadic bind the
# frozen proof reduces through is gone); `match isoYear with` instead of `if`; a
# higher-order local (`fun a b => [a, b]`) assembling the pair; endpoint locals
# at the INSTANT carrier; the dispatcher computing BOTH branches then selecting;
# `::` cons notation instead of list-literal notation; and a let-bound copy of
# the forwarded flag with an explicit `= true` test. So the spec constrains
# behaviour, not impl shape, across bind-structure, pattern-matching, notation
# and evaluation-order reshapes.
#
#   The 8th (`E7`) is a NON-hole worth recording so a later audit does not
#   re-derive it as one. It rewrites the CALENDAR upper bound as the next
#   calendar year's first day minus one — extensionally equal to the frozen
#   `gregDec31` on the real carrier (verified in Python over years 1..9998: the
#   two agree at every year), so it is a FAITHFUL correct reshape in the repo's
#   value domain. The spec REJECTS it (exit 1, `unsolved goals` on
#   `ensures_1`/`ensures_3`). This is NOT a soundness hole: the two landmarks are
#   DISTINCT opaque `axiom`s here with no equational contract relating them, so
#   the equality that makes the reshape faithful is a fact about the real
#   date library that the Lean model deliberately does not import. Admitting it
#   would require an axiom `gregDec31 y = gregJan1 (y + 1) - 1`, i.e. a STRONGER
#   callee contract than the proof needs — precisely the over-claiming that the
#   axiom-liability rule forbids, and G-AX would then have to carry it. The
#   frozen spec is correctly silent; a reshape that depends on an un-imported
#   library identity is outside the modeled vocabulary, not wrongly rejected.
#   Recorded as `uncertain-by-design`, not escalated.
#
# Attack F (dropped-nagini-case re-derivation): the port dropped NO nagini SPEC
# case — all 13 have counterparts and the only dropped lane is AXIOM_TESTS,
# which this gate ignores by construction (it is G-AX's lane, and G-AX passes).
# Re-verified by the second audit against the sibling manifest case by case.
#
# ---------------------------------------------------------------------------
# SECOND AUDIT LEDGER — independent re-derivation, ~100 builds.
#
# Attack A (statement integrity): every case's module was split on the
# impl-region markers and the text OUTSIDE those regions diffed against the
# frozen file. All 17 cases are byte-identical outside their own impl region, so
# no case reformats, weakens or restates an obligation. The three anchors are
# additionally asserted unique at load, above.
#
# Attack B/B' (witness re-derivation + forgery): all ten reject cases rebuilt
# from scratch — rival exit 0, gold exit 1, consistency probe exit 1 (`False`
# left unsolved under the witness's own hypothesis) on every one, matching the
# recorded `gold_signature`s exactly. The forgery pair is in the WITNESS section
# above; it is the substance of this audit and it CONFIRMS the cases.
#
# Attack C (is the rival wrong, or just different?): each rival differs from
# gold on a value the spec PINS, not on shape — the residual goals read on the
# rival side name concrete distinct landmark atoms. No two rivals share a
# witness point. Nothing here is a Nat truncation / Option collapse / coercion
# trap: the carrier is `List Int` over six DISTINCT opaque `axiom`s, so no two
# landmark families are definitionally equal and no rival is gold-equivalent.
#
# Attack D (SPEC-TOO-WEAK, 15 NEW wrong impls beyond the first audit's 8): ALL
# REJECTED (exit 1), each on a NAMED `ensures` clause. Beyond the obvious
# reshuffles (ISO arm duplicated into the calendar arm, mixed lower landmark,
# instant endpoints transposed, dispatcher ignoring the column flag, a THREE-
# element list, a duplicated lower endpoint, an instant mixed upper, dispatcher
# on the wrong year, ISO lower shifted, an instant calendar arm with an ISO
# upper, instant ISO lower off by one, an ISO upper written as `isoFirst value +
# 364`), the sharpest were three TUNED rivals that are gold EVERYWHERE except a
# single point — `if value = 2015 then <calendar> else dateBounds value isoYear`,
# its instant twin at 2020, and a dispatcher that mis-routes only at
# (isDateTimeField, isoYear, value) = (true, true, 2015). All three are rejected,
# so the value pin binds every `value` pointwise and not merely generically:
# there is no input at which the spec looks away. No spec hole in the value lane.
#
# Attack E (SPEC-TOO-STRONG, 8 NEW correct reshapes beyond the first audit's 8):
# 8 VERIFIED (exit 0) — endpoints built as two singleton lists then `++`; an
# explicit `= true` test on the flag; `cond` instead of `if`; `match` at the
# instant site; `::` cons; the dispatcher with `= true`; the dispatcher's bound
# result re-let before return; a higher-order pair constructor. Plus the
# all-three-sites-at-once reshape used as the witness control above. So the spec
# constrains behaviour, not shape. `E7` was re-derived and re-confirmed as the
# first audit recorded it (extensional equality of `gregDec31 y` and
# `gregJan1 (y + 1) - 1` re-checked over years 1..9998: 0 disagreements, and the
# spec still rejects it, `unsolved goals` on the calendar clause) — a reshape
# resting on a library identity the model deliberately does not import, hence
# `uncertain-by-design` and NOT a soundness hole. Not escalated, again.
#
# DIVERGENCE: re-read, not re-measured here. The disposition above is correct and
# the reason is the one recorded there (closed by the `total` semantics, with the
# builds cited); this audit spent no builds on it and adds no new finding.
# ===========================================================================
