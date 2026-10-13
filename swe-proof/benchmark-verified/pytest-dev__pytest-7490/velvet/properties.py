"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7490 (velvet).

NOT a Velvet module: a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a complete ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches only text inside the single
``-- impl-start`` / ``-- impl-end`` block and, for the admissibility case, the
``prove_correct`` tactic body. Both regions are elided from the consumer spec
view, so ``markers.same_spec`` holds by construction and the
``prove_correct resolveDynamicXfail`` obligation survives with a byte-identical
statement. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its ``witness``
discriminates: elaborates against the rival, FAILS against the frozen solution).

DEFENDED SURFACE — one contracted method:

    resolveDynamicXfail (entry evalBefore evalAfter : Option Xfail)
      return (stored : Option Xfail)
      ensures stored = finalXfail entry evalBefore evalAfter        <-- LOAD-BEARING

with the pure region supplying ``finalXfail e b a = refresh (refresh e b) a`` and
``refresh current fresh = (match current with | some x => some x | none =>
fresh)``. Spelled out: the determination handed downstream is the FIRST ``some``
in the priority order ``entry`` -> ``evalBefore`` -> ``evalAfter``, and ``none``
only when all three are ``none``. There is no ``require`` clause and all three
binders are immutable value inputs, so the equality must hold for EVERY triple.

The single top-level clause bundles three independent guarantees:
  (K1) ADOPT-AFTER — when nothing is determined on entry and nothing from the
       markers present as the body is entered (``entry = none``,
       ``evalBefore = none``), the determination from the markers present once the
       body has FINISHED must be adopted. A determination that only becomes
       available while the body runs is not lost. This is the reported scenario.
  (K2) ADOPT-BEFORE — when nothing is determined on entry, the determination from
       the markers present as the body is entered is adopted next, in preference
       to the later one.
  (K3) PRIORITY / VALUE-GROUNDING — the result is EXACTLY the first available
       determination, compared field-wise (``Xfail`` derives ``DecidableEq``): not
       a fabricated stand-in, not ``none``, and not a later determination
       substituted for an earlier one.

GROUNDED, NOT AN ORACLE ECHO. ``finalXfail``/``refresh`` are concrete total
``def``s over the method's own three arguments; the ``axioms`` region declares
nothing (the marker-evaluation callee enters parametrically — its results ARE the
``evalBefore``/``evalAfter`` inputs). There is no opaque answer key to echo, so
the ungrounded-oracle-echo class does not arise here and the carrier computes:
every witness closes by ``decide`` with no conditioning hypotheses, hence no
``witness-inconsistent`` risk.

REACHABILITY IS LOAD-BEARING FOR THE REFINEMENT ARGUMENT — the analysis that
shaped this battery. The three binders are not independently free in the real
system: a marker set only ACCUMULATES across a single test body (markers are
appended during the run and nothing removes them), and the evaluation returns the
FIRST matching marker in iteration order, which is stable once present. So the
reachable triples are exactly

    (none, none, none)  (none, none, some y)  (none, some y, some y)  (some x, some x, some x)

i.e. ``evalBefore = some y`` forces ``evalAfter = some y``, and ``entry = some x``
forces both later evaluations to that same value. A rival that disagrees with the
frozen spec ONLY at an unreachable triple is mathematically refutable yet its
faithful real patch would still resolve every test — shipping it would be a
SPURIOUS reject whose ``refinement`` claims a failure the patch does not have.
Every witness below is therefore stated at a REACHABLE triple, and two sibling
rivals were dropped for exactly this reason (see the footer).

BINDER COVERAGE. The reject witnesses probe the reachable triples and move every
binder across both ``none`` and ``some``:
  * ``adopt-after-dropped``   at (none, none, some) — varies ``evalAfter``;
  * ``no-settle-at-all``      at (none, some, some) — varies ``evalBefore``;
  * ``collapse-to-none``      at (some, some, some) — varies ``entry``;
  * ``fabricate-stand-in``    at (none, none, none) — the all-``none`` corner,
    pinning that an absent determination stays absent;
  * ``degrade-strict-flag``   at (none, none, some d) with ``d.strict = true`` —
    the FIELD axis (added by audit; see below).
So ``entry``, ``evalBefore``, ``evalAfter`` each take both ``none`` and ``some``
across the witnesses, and the all-``none`` and all-``some`` corners are both
probed. No single binder is held at one value by every witness, so a rival
mishandling only one input cannot slip through the lane.

TWO AXES, NOT ONE — the audit correction to this battery's coverage claim. The
first four rivals all get the determination's PRESENCE wrong: each is refuted on
the ``none``/``some`` axis alone, and each would still be refuted if ``Xfail``
were shrunk to a bare presence bit. That left the CONTENT axis unattacked: an
impl that adopts the right determination at the right moment and then rewrites
one of its fields on the way through satisfied every witness in the battery.
``degrade-strict-flag`` closes that axis, and its witness is stated at a
determination with ``strict`` SET — a point no other witness visits, since the
shared ``_XA`` value has the flag clear and therefore cannot expose an impl that
clears it. The clause does pin content (the ``Xfail`` structure derives
``DecidableEq`` and the equality is field-wise), so this is a battery gap the
audit closed, not a spec gap.

SIBLING (nagini) ACCOUNTING — the adversarial argument carried over. The sibling
models ``settle_saved_evaluation(slot, final_marker_state)`` over a MUTATED heap
carrier with a presence bit, and splits its contract into (P1) present-on-exit /
(P2) refresh / (P3) preserve. Here the purely-functional core is one method whose
single combination clause absorbs all three, so each sibling case lands on that
clause re-expressed over the ``Option Xfail`` triple (the mutated slot and the
integer marker-state token both dissolve into value inputs — no heap, no presence
bit, no object identity). Full disposition table in the footer.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7490"
BACKEND = "velvet"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The ENTIRE frozen impl region, captured verbatim: it lies wholly inside the one
# `-- impl-start`/`-- impl-end` block and is unique in Solution.lean. Both facts
# are asserted at import, so any drift in the frozen solution fails loudly here
# rather than silently producing a variant that no longer tests what it claims.
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    let mut xfailed : Option Xfail := entry\n"
    "    -- Before the body is entered: settle the determination if not already known.\n"
    "    xfailed := match xfailed with\n"
    "      | some x => some x\n"
    "      | none   => evalBefore\n"
    "    -- The body runs here; it may establish a determination dynamically.\n"
    "    -- After the body has finished: settle again against the markers now present,\n"
    "    -- so a determination established while the body ran is observed.\n"
    "    xfailed := match xfailed with\n"
    "      | some x => some x\n"
    "      | none   => evalAfter\n"
    "    return xfailed\n"
    "    -- impl-end"
)
if _GOLD_IMPL not in _BASE:
    raise AssertionError("frozen impl region drifted; update _GOLD_IMPL")

# The frozen proof body, tuned to the frozen impl's straight-line shape. Only the
# admissibility case retunes it (to clear one extra decidable side goal); the
# `prove_correct` HEADER and the obligation statement are never touched.
_GOLD_PROOF = (
    "prove_correct resolveDynamicXfail by\n"
    "  loom_solve\n"
    "  simp [finalXfail, refresh]"
)
if _GOLD_PROOF not in _BASE:
    raise AssertionError("frozen proof body drifted; update _GOLD_PROOF")


def _impl(body):
    """Full variant replacing the impl block; `body` is the text BETWEEN the
    markers, wrapped back in the exact marker lines so the region is unchanged."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_BASE, _GOLD_IMPL, block)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_swap(_BASE, _GOLD_IMPL, block), _GOLD_PROOF, proof)


# --- witness machinery -------------------------------------------------------
# The spec is a `method` CONTRACT, not a bare predicate, so a witness reaches it
# through Velvet's tester machinery. `derive_tester_for` emits
#   <name>Tester args = if decide (pre args) then (match <name>Exec args with
#                        | DivM.res out => decide (post args out) | _ => false)
#                       else true
# so the tester takes exactly the method's three inputs in declaration order (NOT
# the return value) and `= false` says the extracted program VIOLATES the
# postcondition at that concrete triple. There is no `require` clause, so `pre` is
# trivially true and every triple is inside the guard — the `= false` claim is
# never vacuously satisfied by falling outside the precondition. Checked in a file
# whose `prove_correct` block is stripped, so no tactic script can mask the
# verdict. The impl is straight-line (no loop, no `Classical.choice`), so the
# extracted program reduces under the kernel and each witness closes by `decide`;
# against the FROZEN solution the tester computes `true`, so `= false` is
# unprovable — the required discrimination half. Both halves were run per case.
_TESTER = ("extract_program_for resolveDynamicXfail\n"
           "prove_precondition_decidable_for resolveDynamicXfail\n"
           "prove_postcondition_decidable_for resolveDynamicXfail\n"
           "derive_tester_for resolveDynamicXfail\n\n")

# Concrete determinations. `_XA` carries a distinctive `reason` so a fabricated
# fixed stand-in is field-wise UNEQUAL to it under the derived `DecidableEq`.
_XA = '(some { reason := "a", run := true, strict := false } : Option Xfail)'
_XN = "(none : Option Xfail)"
# Same determination as `_XA` but with the `strict` flag SET. Needed by the
# field-axis rival: a witness stated at `_XA` cannot refute an impl that clears
# `strict`, since `_XA` already has it clear.
_XS = '(some { reason := "a", run := true, strict := true } : Option Xfail)'


def _wit(entry, before, after):
    return (_TESTER
            + f"example : resolveDynamicXfailTester {entry} {before} {after} = false := by\n"
            + "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # (1) SOUNDNESS positive — structurally different but CORRECT.
    # Ports the sibling's `pos-combined-guard`: there, the two-branch
    # `if not present / elif value is None` collapses into one boolean-equal
    # guard. Here the corresponding reshape replaces the two inline `match`
    # steps with explicit calls to the pure `refresh` combinator and renames the
    # local. It computes the identical combination on EVERY triple and introduces
    # no new obligation, so after `loom_solve` the residual goal is still closed
    # by the frozen `simp [finalXfail, refresh]` — kept byte-identical, so this
    # positive cannot pass by having had its obligation weakened. If a faithful
    # correct impl in a different shape could NOT verify, the postcondition is
    # over-fit to the frozen syntactic form => SPEC-TOO-STRONG.
    # Also the honest cheapest-impl control (sibling `pos-grounded-assert`): the
    # post-image is a grounded pure def of the inputs, so the cheapest impl that
    # satisfies it IS the real combination — there is no verifying wrong echo.
    # =====================================================================
    {
        "id": "pos-refresh-combinator-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let mut det : Option Xfail := entry\n"
            "    det := refresh det evalBefore\n"
            "    det := refresh det evalAfter\n"
            "    return det\n"),
        "rationale": "the cheapest-honest-impl control: settle via explicit `refresh` "
                     "calls rather than the two inline `match` steps, with the local "
                     "renamed. AUDIT-CORRECTED SCOPE — this reshape is only a "
                     "SYNTACTIC paraphrase: its impl term is DEFINITIONALLY equal to "
                     "the post-image (`refresh (refresh e b) a = finalXfail e b a` "
                     "closes by `rfl`), so it discharges under the UNCHANGED frozen "
                     "tactic body but does NOT by itself show the spec admits a "
                     "differently-SHAPED correct impl. It stands as the "
                     "grounded-post-image control (the post-image is a concrete pure "
                     "def of the method's own inputs, not an opaque oracle, so no "
                     "wrong echo can satisfy it); the SPEC-TOO-STRONG probe proper is "
                     "`pos-priority-match-reshape` below, whose impl term is NOT "
                     "definitionally equal to the post-image.",
    },

    # =====================================================================
    # (1b) SOUNDNESS positive — the real SPEC-TOO-STRONG probe (added by audit).
    # A correct impl in a genuinely DIFFERENT shape: one simultaneous three-way
    # `match` on the whole triple, selecting the first available determination
    # directly, instead of two sequential single-step settles. Unlike (1) this
    # term is NOT definitionally equal to the post-image — `rfl` fails on
    # `(match e, b, a with ...) = finalXfail e b a`, and the frozen tactic body
    # leaves the residual goal unsolved — so verifying it requires the SPEC to
    # admit the reshape rather than the frozen syntax to match it. The proof body
    # is retuned (case-split on the two leading binders, then the frozen simp
    # set); the `prove_correct` HEADER and the obligation statement stay
    # byte-identical, so nothing about the defended clause is weakened. If this
    # could not be proven, the postcondition would be over-fit to the frozen
    # impl's sequential form => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-priority-match-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    return match entry, evalBefore, evalAfter with\n"
            "      | some x, _, _     => some x\n"
            "      | none, some y, _  => some y\n"
            "      | none, none, a    => a\n",
            "prove_correct resolveDynamicXfail by\n"
            "  loom_solve\n"
            "  cases entry <;> cases evalBefore <;> simp [finalXfail, refresh]"),
        "rationale": "a CORRECT impl in a genuinely different shape: one simultaneous "
                     "three-way `match` selecting the first available determination, "
                     "instead of two sequential single-step settles. It agrees with "
                     "`finalXfail` on every (entry, evalBefore, evalAfter) triple but "
                     "its term is NOT definitionally equal to the post-image (`rfl` "
                     "fails, and the frozen tactic body leaves the goal unsolved), so "
                     "it is admitted by the CLAUSE and not by syntactic coincidence — "
                     "which is what a SPEC-TOO-STRONG probe has to establish. Only the "
                     "tactic body is retuned (case-split then the frozen simp set); "
                     "the obligation statement is byte-identical, so the positive "
                     "cannot pass by having had its obligation weakened. If a faithful "
                     "correct impl in this shape were REJECTED => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # (2) ADMISSIBILITY. The sibling's `admiss-empty-saved` self-calls on the
    # reported-scenario pre-state to attest the PRECONDITION admits it. This
    # bundle has NO `require` clause, so "a normal input satisfies the
    # precondition" is vacuously true and a direct port would test nothing. The
    # case is therefore RE-AIMED at the residual admissibility risk on a total
    # domain: that the post-image is DEGENERATE (unsatisfiable, or satisfied only
    # by collapsing) at the decisive point. The impl stays verbatim so the
    # method's own obligation still discharges; an in-region `assert` pins the
    # post-image at the reported-scenario triple — nothing determined on entry or
    # as the body is entered, a determination available only AFTER — demanding
    # that determination be adopted VALUE-identically. The assert is LIVE: a false
    # claim about the same point leaves an unsolved goal and the case fails. The
    # proof is retuned only to clear that extra decidable side goal; the
    # `prove_correct` header and obligation statement are byte-identical.
    # =====================================================================
    {
        "id": "admiss-adopt-after-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `admiss\n"
            "      (finalXfail none none (some { reason := \"d\", run := true, strict := false })\n"
            "        = some { reason := \"d\", run := true, strict := false }))\n"
            "    let mut xfailed : Option Xfail := entry\n"
            "    xfailed := match xfailed with\n"
            "      | some x => some x\n"
            "      | none   => evalBefore\n"
            "    xfailed := match xfailed with\n"
            "      | some x => some x\n"
            "      | none   => evalAfter\n"
            "    return xfailed\n",
            "prove_correct resolveDynamicXfail by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (simp [finalXfail, refresh])\n"
            "    | decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "decisive corner: with nothing determined on entry and nothing "
                     "from the markers present as the body is entered, a "
                     "determination that becomes available only once the body has "
                     "finished MUST be adopted, field-wise identically — "
                     "`finalXfail none none (some d) = some d`, neither collapsed to "
                     "`none` nor replaced by a different determination. There is no "
                     "`require` clause, so the sibling's precondition-admits-input "
                     "reading is vacuous here and this is the meaningful re-aim. The "
                     "in-region assert must discharge (else the obligation is "
                     "degenerate exactly where the behaviour matters) and the "
                     "verbatim impl keeps the equality clause discharging too.",
    },

    # =====================================================================
    # UNIQUENESS rivals (expect reject). Each is a wrong impl sharing the frozen
    # spec, kept straight-line so its tester reduces and its witness is
    # `decide`-able, and each witness sits at a REACHABLE triple so the
    # `refinement` argument is about a failure the faithful patch really has.
    # =====================================================================

    # (3) Ports the sibling's `refresh-partial-absent-only` — its central rival
    # and the exact pre-image behaviour. Settle once against the markers present
    # as the body is ENTERED and never reconsider afterwards.
    {
        "id": "adopt-after-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let mut xfailed : Option Xfail := entry\n"
            "    xfailed := match xfailed with\n"
            "      | some x => some x\n"
            "      | none   => evalBefore\n"
            "    return xfailed\n"),
        "refinement": "the faithful counterpart settles the stored determination only "
                      "against the markers present as the body is ENTERED and never "
                      "re-settles it once the body has finished. A determination that "
                      "becomes available only during the run is therefore dropped, so "
                      "a failing test that acquired one mid-run is reported as a "
                      "plain failure instead of an expected failure, and the strict "
                      "variant that passed is not flagged. This is precisely the "
                      "regressed behaviour the change repairs, so both F2P tests "
                      "would still fail: it would NOT resolve.",
        "rationale": "REJECT from (K1): with entry = none and evalBefore = none the "
                     "clause requires adopting evalAfter, but this impl returns none. "
                     "Refuted at the REACHABLE triple (none, none, some a) — the "
                     "reported scenario — where finalXfail = some a and the rival "
                     "gives none. Varies evalAfter across none/some. If it verified "
                     "=> SPEC-TOO-WEAK (the spec would not pin the after-body "
                     "determination, the whole point of the modeled behaviour).",
        "witness": _wit(_XN, _XN, _XA),
    },

    # (4) Ports the sibling's `refresh-norefresh` (its bare-`pass` pre-patch
    # rival): settle NOTHING, hand back whatever was determined on entry,
    # ignoring both evaluations. Strictly weaker than (3) — it also drops the
    # before-body adoption — so it gets its own witness at a triple where a
    # determination IS available before the body, which is the sub-domain that
    # distinguishes it from (3) rather than one (3) already covers.
    {
        "id": "no-settle-at-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return entry"),
        "refinement": "the faithful counterpart never (re-)settles the stored "
                      "determination across the body at all: it keeps whatever was "
                      "determined on entry. In the reported scenario nothing is "
                      "determined on entry, so no determination is ever adopted and "
                      "the failing test is reported as a plain failure — the F2P "
                      "tests would NOT resolve. It additionally regresses the "
                      "already-working case where a determination is available as the "
                      "body is entered, so the statically-marked xfail family would "
                      "break as well.",
        "rationale": "REJECT from (K2) (and a fortiori (K1)): with entry = none the "
                     "result must adopt the first available evaluation, but the impl "
                     "yields none. Refuted at the REACHABLE triple (none, some a, "
                     "some a), which varies evalBefore to some and is the sub-domain "
                     "separating this rival from `adopt-after-dropped` (that one is "
                     "CORRECT here, so the two cannot share a witness). If it "
                     "verified => SPEC-TOO-WEAK (admits the wholly unsettled "
                     "pre-image).",
        "witness": _wit(_XN, _XA, _XA),
    },

    # (5) Attacks (K3) from the opposite side to `fabricate`: rather than
    # inventing content, discard every determination and always report none. It
    # satisfies the all-none corner and so cannot be caught there; refuted where a
    # determination genuinely exists on entry.
    {
        "id": "collapse-to-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return (none : Option Xfail)"),
        "refinement": "the faithful counterpart stores no determination at all, "
                      "leaving the slot empty however the markers evaluate. Every "
                      "expected-failure report — the dynamically acquired ones the "
                      "F2P tests cover AND the statically marked ones the existing "
                      "suite covers — degrades to a plain outcome, so the F2P tests "
                      "and the broad xfail-reporting family would both fail: it would "
                      "NOT resolve.",
        "rationale": "REJECT from (K3): the result must be EXACTLY the first "
                     "available determination, so an unconditional none violates the "
                     "clause whenever any input is some. Refuted at the REACHABLE "
                     "triple (some a, some a, some a), which varies entry to some and "
                     "probes the all-some corner no other witness reaches. If it "
                     "verified => SPEC-TOO-WEAK (the clause would not force any "
                     "determination to be reported).",
        "witness": _wit(_XA, _XA, _XA),
    },

    # (6) Ports the sibling's `refresh-fabricate`. The sibling's object-identity
    # pin (`is`) has no counterpart on a value carrier, but the VALUE-grounding it
    # protected does: a fixed stand-in is field-wise unequal to the real
    # determination. Refuted at the all-none corner, where the true answer is
    # `none` and any fabricated `some` is wrong — a triple that also pins "absent
    # stays absent", which no other witness asserts.
    {
        "id": "fabricate-stand-in",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return (some { reason := \"\", run := true, strict := false })"),
        "refinement": "the faithful counterpart stores a hardcoded determination that "
                      "the marker evaluation never produced, so it does not reflect "
                      "the test's actual markers (wrong reason, and wrong strict/run "
                      "flags). Tests with no marker at all would be reported as "
                      "expected failures, and the strict scenario would be judged on "
                      "the wrong flag — so the F2P tests and the surrounding "
                      "xfail-reporting family would fail: it would NOT resolve.",
        "rationale": "REJECT from (K3), value-grounding: a fixed fabricated `some "
                     "{reason := \"\"}` is not field-wise equal to the real "
                     "first-available determination under the derived DecidableEq. "
                     "Refuted at the REACHABLE all-none triple (none, none, none), "
                     "where finalXfail = none and the rival invents a determination; "
                     "this is the corner pinning that an absent determination stays "
                     "absent. If it verified => SPEC-TOO-WEAK (the carrier would have "
                     "dropped value-grounding, letting an invented determination "
                     "stand for a real one).",
        "witness": _wit(_XN, _XN, _XN),
    },

    # (7) ADDED BY AUDIT — the content-degrading rival class the four rivals above
    # leave unattacked. Every existing rival gets the determination's PRESENCE
    # wrong (returns `none` where a `some` is required, or a `some` where `none`
    # is): each witness is refuted on the none/some axis alone, so a rival that
    # adopts the RIGHT determination at the RIGHT moment but rewrites one of its
    # fields on the way through would slip past all four. This one settles exactly
    # as the frozen impl does and then flattens `strict` to `false`. It is the
    # sharpest instance of the class because `strict` is precisely the flag the
    # two guarantees split on: the same dynamically-acquired determination must
    # produce one outcome when `strict` is set and a different one when it is not,
    # so a spec that did not carry the flag through would not distinguish them.
    {
        "id": "degrade-strict-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let mut xfailed : Option Xfail := entry\n"
            "    xfailed := match xfailed with\n"
            "      | some x => some x\n"
            "      | none   => evalBefore\n"
            "    xfailed := match xfailed with\n"
            "      | some x => some x\n"
            "      | none   => evalAfter\n"
            "    return match xfailed with\n"
            "      | some x => some { reason := x.reason, run := x.run, strict := false }\n"
            "      | none   => none\n"),
        "refinement": "the faithful counterpart settles the determination at exactly the "
                      "right moments — it adopts the one that only became available "
                      "while the body ran — but hands downstream a REBUILT "
                      "determination whose strict flag has been cleared instead of the "
                      "one the marker evaluation produced. Presence is right, timing is "
                      "right, content is not: the scenario that acquires a strict "
                      "determination mid-run would be judged on the non-strict path and "
                      "reported as an expected failure rather than the failure the "
                      "strict setting demands, so one of the two F2P tests would still "
                      "fail: it would NOT resolve. (The other F2P test, which does not "
                      "depend on the flag, would pass — which is exactly why this rival "
                      "is not covered by the presence-only rivals above.)",
        "rationale": "REJECT from (K3) value-grounding, on the FIELD axis rather than "
                     "the none/some axis: the clause pins `stored` to the first "
                     "available determination under the derived `DecidableEq`, so "
                     "rewriting any field breaks it even though presence and timing "
                     "are correct. Refuted at the REACHABLE triple (none, none, some "
                     "d) with `d.strict = true` — the reported scenario carrying the "
                     "flag — where `finalXfail = some d` and the rival returns `some "
                     "d` with `strict := false`. This is the first witness in the "
                     "battery whose refutation turns on a FIELD VALUE and not on "
                     "presence; every other reject case is still refuted if `Xfail` is "
                     "shrunk to a presence bit. If it verified => SPEC-TOO-WEAK (the "
                     "spec would pin only WHICH determination is adopted and not WHAT "
                     "it carries, admitting a passthrough that silently rewrites it).",
        "witness": _wit(_XN, _XN, _XS),
    },
]


# ---------------------------------------------------------------------------
# SIBLING (nagini) -> velvet DISPOSITION. The sibling ships 8 SPEC cases (2
# soundness, 1 admissibility, 5 uniqueness) over `settle_saved_evaluation(slot,
# final_marker_state)` with a three-clause postcondition (P1 present-on-exit /
# P2 refresh / P3 preserve). This bundle models the same purely-functional core as
# ONE method with a single combination clause, so every portable case lands on
# that clause. 6 cases here vs 8 there is carrier narrowing, not thinning.
#
#   sibling case                 -> here                              status
#   ------------------------------------------------------------------------
#   pos-combined-guard            -> pos-priority-match-reshape       PORTED (re-aimed by audit)
#   pos-grounded-assert           -> pos-refresh-combinator-reshape   PORTED
#   admiss-empty-saved            -> admiss-adopt-after-nondegenerate RE-AIMED
#   refresh-partial-absent-only   -> adopt-after-dropped              PORTED
#   refresh-norefresh             -> no-settle-at-all                 PORTED
#   refresh-fabricate             -> fabricate-stand-in               PORTED
#   refresh-stale-state           -> (none)                           DROPPED (carrier)
#   refresh-clobber-prior         -> (none)                           DROPPED (unreachable)
#   frame-mutation (implicit N/A) -> (none)                           VACUOUS
#   (no sibling counterpart)      -> collapse-to-none                 ADDED
#   (no sibling counterpart)      -> degrade-strict-flag              ADDED (audit)
#   AXIOM_TESTS (ax-eval-*)       -> (none)                           OUT OF LANE
#
# TWO POSITIVES, TWO JOBS (audit re-aim). The port shipped ONE positive doing both
#   jobs, and it could only ever do the second: its impl term
#   `refresh (refresh e b) a` is DEFINITIONALLY equal to the post-image
#   `finalXfail e b a` (measured — closes by `rfl`), so it verifies under the
#   frozen tactic body however form-tuned the spec might be, and it cannot witness
#   that the spec admits a differently-SHAPED impl. It is retained as the
#   sibling's `pos-grounded-assert` counterpart — the grounded-post-image control:
#   the post-image is a concrete pure def over the method's own inputs, not an
#   opaque callee, so the oracle-echo class cannot arise, and the grounding is
#   additionally defended positively by the admissibility corner (which pins the
#   exact adopted value) and negatively by `fabricate-stand-in`,
#   `collapse-to-none` and `degrade-strict-flag`.
#   The sibling's `pos-combined-guard` — whose job IS the SPEC-TOO-STRONG probe,
#   since collapsing two branches into one boolean-equal guard is a genuine
#   reshape there — is re-aimed onto `pos-priority-match-reshape`, whose
#   simultaneous three-way match is NOT defeq to the post-image (`rfl` fails, and
#   under the frozen tactic body the goal is left unsolved), so verifying it takes
#   the CLAUSE and not a syntactic coincidence. Measured: it verifies once the
#   tactic body is retuned by a case-split on the two leading binders, with the
#   obligation statement byte-identical. So the spec is NOT over-fit to the frozen
#   impl's sequential form — only the frozen TACTIC is, which is expected and is
#   exactly what `_impl_proof` exists for.
#
# RE-AIMED (admissibility): the sibling attests that the PRECONDITION admits the
#   reported-scenario pre-state. This bundle has no `require` clause, so that
#   reading is vacuous; the case is re-aimed at post-image non-degeneracy at the
#   same decisive point. Documented rather than silently converted.
#
# ADDED (collapse-to-none): no sibling counterpart — the sibling's carrier keeps a
#   separate presence bit, so "always present on exit" (P1) is a distinct clause
#   there and an impl that reported nothing is caught by it directly. On this
#   carrier presence is folded into the single Option-valued clause, so the
#   discard-everything impl is a genuinely distinct rival and is attacked
#   explicitly. It also supplies the all-some witness corner.
#
# DROPPED (refresh-stale-state) — CARRIER narrowing, not a proof difficulty. The
#   sibling re-evaluates at a FIXED/stale marker-state token distinct from the
#   post-body one. Here the evaluation RESULTS are already the inputs; there is no
#   separate state token to evaluate at. The nearest re-expression is "settle
#   twice against `evalBefore`", which is EXTENSIONALLY equal to
#   `adopt-after-dropped`: `refresh (refresh e b) b = refresh e b` holds for every
#   `e`, `b` (provable by case-split, though NOT by `rfl` — the audit measured
#   `rfl` failing on it, so the earlier "definitionally equal" wording here was
#   wrong; the extensional equality is what makes the case redundant, and it is
#   the relevant one since the spec compares VALUES). The two rivals therefore
#   agree at every triple, so a witness refuting one refutes the other and the
#   same (K1) content is already covered. Re-derived by the audit: the stale
#   re-expression is refuted by `adopt-after-dropped`'s own witness at
#   (none, none, some a). Shipping it would pad the count without probing a new
#   sub-domain.
#
# DROPPED (refresh-clobber-prior) — UNREACHABLE, so no honest refinement exists.
#   The sibling attacks (P3) preserve via OBJECT IDENTITY: re-running the
#   evaluator yields a DIFFERENT object for the same logical marker, breaking an
#   `is` pin. mapping.md §2 states this carrier compares field-wise by VALUE and
#   that object identity is explicitly orthogonal. Under marker accumulation a
#   determination present on entry implies the marker is still present afterwards,
#   so the after-body evaluation returns a VALUE-EQUAL determination: the clobber
#   `return evalAfter` agrees with the frozen spec at EVERY reachable triple
#   (verified by enumerating them). A mathematical witness exists only at the
#   unreachable (entry = some, evalAfter = none) — a marker present at entry but
#   gone afterwards, which the real system never produces. The witness at that
#   triple does elaborate against the rival and fail against gold, so it would
#   have PASSED the gate's two mechanical halves; it is dropped anyway because its
#   faithful patch would RESOLVE, making the `refinement` claim false. Recorded
#   here as a deliberate refusal to ship a spurious reject, not an omission.
#   (The value-preserve content that IS observable is defended by
#   `collapse-to-none`, `fabricate-stand-in` and `degrade-strict-flag`.)
#   AUDIT RE-DERIVATION (independent, with real builds): confirmed. The clobber
#   re-expression `return evalAfter` was built and DOES agree with the frozen spec
#   at all four reachable triples — its tester computes `true` at each of
#   (none,none,none), (none,none,some a), (none,some a,some a),
#   (some a,some a,some a), all four checked in one file which elaborated clean.
#   Its only refutation point is (some a, some a, none), and the port's reading of
#   that triple as unreachable is right: a determination present on entry means the
#   marker is present, markers only accumulate across one body, and the evaluation
#   is stable once the marker is there, so the after-body evaluation cannot be
#   `none` there. The witness at that triple was also built and does clear both
#   mechanical halves (rival 0, gold 1, gold failing semantically) — i.e. the gate
#   would have recorded this case as a clean reject — which is precisely why the
#   refusal is the correct call and is recorded here rather than left implicit.
#
# VACUOUS (frame-mutation): the sibling's #1 weakness class overwrites a read-only
#   input held at a fractional heap permission. Lean and Velvet are referentially
#   transparent — no heap, no aliasing, every input an immutable value, and this
#   bundle's only `mut` binder is a fresh local rather than a parameter. There is
#   no read-only input to overwrite, so no discriminating witness could exist.
#   Reported vacuous; deliberately not replaced by a fabricated substitute. The
#   sibling itself records has_readonly_input=False for the same reason.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
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
# AXIOM_TESTS: dropped. The axiom lane belongs to G-AX and this gate ignores it.
#   This bundle declares no `axiom` in any case — the marker-evaluation callee is
#   modeled parametrically, its results arriving as the evalBefore/evalAfter
#   inputs — so the sibling's determinism probe has no obligation to attach to
#   here; axiom_check.py already covers that callee.
AXIOM_TESTS = []
