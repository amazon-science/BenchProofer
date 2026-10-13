"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14496 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside a
``-- impl-start`` / ``-- impl-end`` region, or inside a ``prove_correct`` tactic
body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and both ``prove_correct`` headers survive) and swaps
in a candidate implementation, checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: elaborates against the rival, FAILS against the frozen solution).

DEFENDED SURFACE (TWO contracted methods over one shared pure conversion):

  asAbsoluteCount (value scaled : Rat) : Rat                    -- pure, transparent
    = if value ≤ 1 then ((max 2 (Rat.floor scaled) : Int) : Rat)
      else value

  conditionSizeParameter (value scaled : Rat) (population : Nat) return (out : Rat)
    require 0 < value
    require 1 ≤ population
    require scaledFromPopulation scaled value population
    ensures out = asAbsoluteCount value scaled                            (O1)

  resolvePairedSizes (value secondaryValue scaledPrimary scaledSecondary : Rat)
                     (secondaryGiven : Bool) (population : Nat)
                     return (out : SizePair)
    require 0 < value
    require 0 < secondaryValue
    require 1 ≤ population
    require scaledFromPopulation scaledPrimary value population
    require scaledFromPopulation scaledSecondary
              (pairedSecondarySource value scaledPrimary secondaryValue
                 secondaryGiven) population
    ensures out = resolvedPairedSizes value secondaryValue scaledPrimary
                    scaledSecondary secondaryGiven                        (O2)

The SCALED value is an INPUT, not recomputed: the repository performs the
scaling in the ambient inexact numeric type, so the conditioning step receives a
value that agrees with the ideal product only to within one part in 2^53.
``scaledFromPopulation`` is exactly that admissible-input relation, and every
rival below is refuted at a ``scaled`` the REAL routine actually produces.

A sizing parameter arrives in one of two forms: an absolute count (a value
strictly greater than one) or a fraction of the population (a value in the
half-open interval (0, 1]).  A fraction must be turned into a concrete absolute
count — scale by the population, take the integer part, never fall below two —
while an absolute count passes through untouched.  ``resolvePairedSizes``
conditions a PAIR: the primary parameter first, then an optional secondary one
which defaults to the *already conditioned* primary when it is not supplied, and
is then conditioned in turn.

The two ``ensures`` are each a single exact equality against a transparent pure
function, but each pins several INDEPENDENT facets that a rival can break one at
a time.  For O1 (equivalently, the primary slot of O2):

  * (B) BRANCH SELECTION — the conversion fires only when ``value ≤ 1``; an
        absolute count (``value > 1``) is returned as-is.  Attacked from both
        sides: ``reject-conversion-unguarded`` drops the guard altogether (wrong
        across the whole pass-through branch), and ``reject-guard-strict-at-one``
        makes the comparison STRICT (wrong at exactly one input, the closed end
        of the documented interval).  Neither subsumes the other.
  * (I) INTEGRALITY — the scaled value's INTEGER PART is taken, so a fractional
        input never leaves a fractional residue.  The load-bearing facet: it is
        the whole difference between the pre-image and the frozen spec.  Attacked
        by ``reject-fraction-not-truncated`` (and, on O2's primary slot, by
        ``reject-paired-primary-not-truncated``).
  * (D) TRUNCATION DIRECTION — the integer part is the value BELOW the product,
        not above it and not the nearest one.  Attacked by
        ``reject-round-up`` (rounds up on every non-integral product),
        ``reject-round-to-nearest`` (diverges only past the half-way point) and
        ``reject-off-by-one-on-whole`` (a near-miss: agrees on every
        non-integral product, undercounts exactly on a whole one).
  * (C) THE FLOOR AT TWO — the result never falls below two.  Attacked by
        ``reject-no-lower-clamp``.
  * (V) VALUE DEPENDENCE — the result is a function OF the scaled value, not a
        constant.  Attacked by ``reject-constant-two``.

O2 adds three facets of its own, none of which O1 can express:

  * (S1) THE SECONDARY IS CONDITIONED TOO — the same conversion runs on the
         secondary slot.  Attacked by ``reject-paired-secondary-raw``.
  * (S2) THE SUPPLIED SECONDARY IS HONOURED — when the secondary IS supplied it
         is that value that gets conditioned, not the primary.  Attacked by
         ``reject-paired-ignores-supplied``.
  * (S3) THE DEFAULT IS THE CONDITIONED PRIMARY — when the secondary is absent
         the primary's conditioned value stands in for it.  Attacked by
         ``reject-paired-defaults-to-supplied``.

WITNESS ROUTE — the Velvet tester route, closed by ``with_unfolding_all
decide``.  ``extract_program_for`` / ``prove_{pre,post}condition_decidable_for``
/ ``derive_tester_for`` synthesise ``conditionSizeParameterTester : Rat → Rat →
Nat → Bool`` and ``resolvePairedSizesTester : Rat → Rat → Rat → Rat → Bool → Nat
→ Bool`` with no
added instance (``SizePair`` derives ``DecidableEq`` in the frozen ``pure``
region).  Plain ``decide`` is STUCK on this carrier — measured, on BOTH files:

    error: Tactic `decide` failed ... reduction got stuck at the `Decidable`
    instance ... match ((1 / 10).mul 31).num, ↑3 with ...

which is the ``Rat``-arithmetic stall the spec guide's Rat note describes: the
elaborator's whnf gives up on ``Rat.mul``/``Rat.floor``, because the reducible
transparency setting hides their definitions.  ``with_unfolding_all`` lifts that
restriction, and the goal then decides in the ELABORATOR — a real proof by
reduction, no ``sorry`` / ``admit`` / ``native_decide`` / ``axiom``
(``native_decide`` would trust the compiler and make the witness hold of gold
too, defeating both halves).  Every witness states its refutation at CONCRETE
literal inputs and binds NOTHING in its head, so the gate's inconsistency probe
is a no-op — there are no hypotheses that could fail to be jointly satisfiable,
and no conditioning on an opaque term is needed because this carrier is fully
transparent.

WHY NOT ``decide +kernel`` (the tactic an earlier revision of this battery
used, and the reason it was re-authored).  ``decide +kernel`` defers reduction
to the kernel, which DOES compute the tester — so the witness elaborated
against its rival and failed against gold, clearing both halves of the
discrimination check.  But the way it failed on gold carried no information: the
elaborator still could not build the ``Decidable`` instance, so gold's build
died with ``did not reduce to `isTrue` or `isFalse` `` — the SAME stuck error a
false claim, a true claim, and a trivial claim all produce.  Measured on gold at
(1/10, 31): the refutation ``= false`` reports stuck, while ``= true`` — the
claim gold actually satisfies — closes EXIT 0 under the same tactic, so the two
outcomes were not being distinguished by the spec at all.  A forged witness
asserting a rival CORRECT at an agreement point would have passed identically.
The gate screens exactly this (``witness-undecided``).  Under
``with_unfolding_all decide`` gold instead reports ``decide proved that the
proposition ... is false`` — a real verdict about the spec — and gold decides
the TRUE claim at the same input EXIT 0, which is what makes gold's exit code
evidence rather than an artifact.

Each witness was SEEN to discriminate with real builds: it ELABORATES against
its rival (EXIT 0) and is REFUTED against the frozen solution (EXIT 1 with a
genuine ``is false`` verdict, not a stuck reduction).

ADVERSARIAL READ of the nagini classes on this carrier (footer has the
case-by-case accounting):

  * SOUNDNESS / positive controls — APPLY.  Three structurally-different but
    CORRECT reshapes must verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY — APPLIES, RE-AIMED.  The sibling injects an in-region
    assertion that a normal input satisfies the precondition.  Here the
    preconditions (``0 < value``, ``1 ≤ population``) are met by every
    normally-shaped input, so that probe alone is degenerate; the sharper
    residual risk is a DEGENERATE post-image (a conversion that collapses every
    input to one value would read as admissible).  The case is re-aimed to pin
    the post-image at THREE separating outcomes at once.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records it.  The
    ``axioms`` region is EMPTY and ``asAbsoluteCount`` is a transparent ``def``
    over the method's own inputs, not an opaque answer key.  Echoing it IS the
    gold value, so there is no wrong-echo to build; in its place the honest
    cheapest reshapes are the positive controls, and the pre-image echo (the
    un-truncated conversion) is shipped as a uniqueness rival the spec MUST
    reject on facet (I).
  * PARTIAL-DOMAIN — the core of the battery.  Every rival below is correct on
    part of the input domain and wrong on a sub-domain, and each is refuted at a
    point inside its own wrong sub-domain.
  * FRAME / PERMISSION-MUTATION — VACUOUS here, and the sibling itself already
    records the class N/A (its input is a pass-by-value scalar with no
    read-only heap reference to overwrite).  Velvet is referentially
    transparent: every parameter of both methods is an immutable value, neither
    method declares a ``mut`` binder, and there is no heap, no aliasing and no
    permission system.  No substitute is fabricated.
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
  * AXIOM lane — DROPPED.  The sibling's ``AXIOM_TESTS`` is already empty, and
    this bundle declares no axiom at all (the conversion is modeled deeply, as
    directive 7 requires); this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14496"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS. Each lies WHOLLY inside the region it edits and is unique in the file
# (both asserted at load by _swap), so every variant keeps same_spec by
# construction and leaves both `prove_correct` headers intact.

# The executable body of the FIRST method, verbatim (strictly inside its
# `-- impl-start` / `-- impl-end` span).
_IMPL_1 = """    let mut size : Rat := value
    if value ≤ 1 then
      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)
    return size"""

# The executable body of the SECOND method, verbatim (strictly inside its own
# `-- impl-start` / `-- impl-end` span).
_IMPL_2 = """    let mut primary : Rat := value
    if value ≤ 1 then
      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)
    let mut secondary : Rat := primary
    if secondaryGiven then
      secondary := secondaryValue
    if secondary ≤ 1 then
      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)
    return { primary := primary, secondary := secondary }"""

# The FIRST method's impl-start marker plus the first line of its body — the
# unique prefix the admissibility case inserts its in-region assertion after.
_IMPL_1_HEAD = "    -- impl-start\n    let mut size"

# The frozen proof body of the first obligation. Elided from the consumer spec
# view; only the admissibility case touches it (to close the residual goal its
# own live assertion adds), and the `prove_correct` HEADER is preserved.
_PROOF_1 = ("prove_correct conditionSizeParameter by\n"
            "  loom_solve <;> simp_all [asAbsoluteCount]")

for _a in (_IMPL_1, _IMPL_2, _IMPL_1_HEAD, _PROOF_1):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"frozen anchor drifted or not unique: {_a[:60]!r}")


def _impl1(body):
    """Full Solution.lean with ONLY the first method's frozen body replaced."""
    return _swap(_BASE, _IMPL_1, body)


def _impl2(body):
    """Full Solution.lean with ONLY the second method's frozen body replaced."""
    return _swap(_BASE, _IMPL_2, body)


# ---------------------------------------------------------------------------
# WITNESS BUILDERS. The Velvet tester machinery is brought in by directives
# INSIDE the witness, so the derived names exist on BOTH sides by construction
# (the witness is appended to the rival file and to the frozen file alike) and
# no witness references a name only one side declares. Closed by
# `with_unfolding_all decide` — see the module docstring's WITNESS ROUTE note on
# why plain `decide` stalls on this carrier, and why `decide +kernel` (which
# also "works") produces a gold-side failure that discriminates nothing.
_TESTER_1 = """extract_program_for conditionSizeParameter
prove_precondition_decidable_for conditionSizeParameter
prove_postcondition_decidable_for conditionSizeParameter
derive_tester_for conditionSizeParameter
"""

_TESTER_2 = """extract_program_for resolvePairedSizes
prove_precondition_decidable_for resolvePairedSizes
prove_postcondition_decidable_for resolvePairedSizes
derive_tester_for resolvePairedSizes
"""


def _wit1(value, scaled, population):
    """Refute the FIRST contract at one concrete (value, scaled, population).

    ``scaled`` is the value the REAL routine hands the conditioning step for
    this (value, population) — the ideal product, which for every point used
    below is in-band per ``scaledFromPopulation`` AND has the same integer part
    as the machine product the repository actually computes (recomputed from the
    real expression during this repair, not carried over)."""
    return (_TESTER_1 + "\nexample : conditionSizeParameterTester "
            f"({value} : Rat) ({scaled} : Rat) {population} = false := by "
            "with_unfolding_all decide\n")


def _wit2(value, secondary, scaled_primary, scaled_secondary, given, population):
    """Refute the SECOND contract at one concrete input tuple.

    ``scaled_primary`` / ``scaled_secondary`` are the scaled values the REAL
    paired routine produces for the primary parameter and for the secondary
    SOURCE (the supplied value when given, else the conditioned primary), each
    in-band per ``scaledFromPopulation``."""
    return (_TESTER_2 + "\nexample : resolvePairedSizesTester "
            f"({value} : Rat) ({secondary} : Rat) ({scaled_primary} : Rat) "
            f"({scaled_secondary} : Rat) {given} {population}"
            " = false := by with_unfolding_all decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify under the frozen proof. If a faithful correct impl cannot
    # verify, the spec is SPEC-TOO-STRONG. All three were built out-of-band
    # (EXIT 0).
    # =====================================================================
    {
        "id": "pos-expression-ladder",
        "kind": "soundness",
        "expect": "verify",
        # Replace the mutable-slot-then-overwrite shape with a single immutable
        # binding selected by a `let ... := if ... then ... else ...` ladder.
        # Different control-flow shape (no mutation at all), identical value.
        "module": _impl1(
            "    let size : Rat :=\n"
            "      if value ≤ 1 then (((max 2 (Rat.floor scaled)) : Int) : Rat)\n"
            "      else value\n"
            "    return size"),
        "rationale": (
            "structurally-different CORRECT reshape of the first obligation: the "
            "mutable-slot-then-conditional-overwrite shape becomes ONE immutable "
            "binding selected by a `let := if … then … else …` ladder, so the "
            "absolute-count branch is written out explicitly instead of being the "
            "un-overwritten initial value. No mutation remains. Both branches "
            "yield exactly the values facets (B) and (I) demand on every input, so "
            "O1 still discharges under the frozen proof. Must verify, else "
            "SPEC-TOO-STRONG on the control-flow shape. "
            "(Sibling: pos-reorder-rename.)"),
    },
    {
        "id": "pos-named-intermediates",
        "kind": "soundness",
        "expect": "verify",
        # Keep the mutable slot but decompose the conversion into named typed
        # intermediates: the scaled product, then its integer part, then the
        # clamp. A different data shape for the same arithmetic.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      let truncated : Int := Rat.floor scaled\n"
            "      size := ((max 2 truncated : Int) : Rat)\n"
            "    return size"),
        "rationale": (
            "a genuinely different data shape for the first obligation: the "
            "conversion is decomposed into named typed intermediates — the scaled "
            "product as a `Rat`, its integer part as an `Int`, then the clamp — "
            "instead of one nested expression. A faithful author would plausibly "
            "write it this way. Same value at every input, so facets (B), (I), "
            "(D) and (C) all still hold and the frozen proof closes unchanged. "
            "Must verify, else SPEC-TOO-STRONG on the data shape. "
            "(Sibling: pos-single-carrier.)"),
    },
    {
        "id": "pos-paired-explicit-source",
        "kind": "soundness",
        "expect": "verify",
        # Second obligation: name the secondary slot's SOURCE explicitly with a
        # `let ... := if ...` instead of initialise-to-primary-then-overwrite.
        # Makes the "supplied value, else the conditioned primary" choice
        # explicit; same pair on every input.
        "module": _impl2(
            "    let mut primary : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)\n"
            "    let source : Rat := if secondaryGiven then secondaryValue else primary\n"
            "    let mut secondary : Rat := source\n"
            "    if secondary ≤ 1 then\n"
            "      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)\n"
            "    return { primary := primary, secondary := secondary }"),
        "rationale": (
            "structurally-different CORRECT reshape of the SECOND obligation — the "
            "one the first two positives cannot reach. The secondary slot's SOURCE "
            "is named explicitly by a `let := if secondaryGiven …` selection "
            "instead of the initialise-to-the-conditioned-primary-then-overwrite "
            "shape, so facets (S2) and (S3) are expressed as one choice rather "
            "than two assignments. The conditioning that follows is unchanged, so "
            "the returned pair is identical on every input and O2 discharges under "
            "the frozen proof. Must verify, else SPEC-TOO-STRONG. (No sibling: "
            "nagini models only the scalar conversion, so this obligation has no "
            "counterpart there — it is carrier widening, not parity chasing.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the preconditions are met by every normally-shaped input,
    # so the sibling's "a normal input satisfies the precondition" probe is
    # degenerate on its own. RE-AIMED at the sharper residual risk: a DEGENERATE
    # post-image. The in-region assertion pins the conversion at THREE
    # SEPARATING outcomes at once, so a post-image that collapsed every input to
    # one value (which reads exactly like an admissible one) is ruled out. The
    # impl is kept verbatim so the obligation still discharges on its own merits;
    # the assertion is LIVE (flipping one conjunct to a false claim leaves the
    # residual goal unprovable — verified out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate-post-image",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_1_HEAD,
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `admiss\n"
                  "      (asAbsoluteCount (1/10 : Rat) (31/10 : Rat) = 3\n"
                  "       ∧ asAbsoluteCount (8/100 : Rat) (62/25 : Rat) = 2\n"
                  "       ∧ asAbsoluteCount (5 : Rat) (155 : Rat) = 5))\n"
                  "    let mut size"),
            # The live assertion leaves one residual decidable goal the frozen
            # tail does not close; the `prove_correct` HEADER and the obligation
            # statement are untouched (only the elided tactic body grows).
            _PROOF_1, _PROOF_1 + " <;> decide +kernel"),
        "rationale": (
            "the preconditions (`0 < value`, `1 ≤ population`) admit every "
            "normally-shaped input, so the sibling's precondition-satisfiability "
            "probe alone would be degenerate; this case is RE-AIMED at the sharper "
            "risk that the post-image is DEGENERATE. The in-region assertion pins "
            "the conversion at three SEPARATING outcomes on one population: a "
            "fraction that scales past three, a smaller fraction that clamps down "
            "to the floor of two, and an absolute count that passes through "
            "unchanged — three different results, so the post-image demonstrably "
            "distinguishes inputs rather than collapsing them. The assertion is "
            "LIVE (flipping a conjunct leaves the residual goal unprovable — "
            "checked during authoring), the impl is kept verbatim so O1 still "
            "discharges on its own merits, and only the elided proof body grows to "
            "close the extra decidable goal. If it cannot verify ⇒ "
            "PRECOND-TOO-STRONG / degenerate post-image. "
            "(Sibling: admiss-f2p-shaped-input, re-aimed.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input inside its own wrong sub-domain, plus the
    # refinement argument that its faithful real counterpart would NOT resolve.
    # Twelve rivals at TWELVE distinct input points.
    # =====================================================================

    # ---- facet (I): INTEGRALITY, the load-bearing clause ----
    {
        "id": "reject-fraction-not-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-IMAGE shape: scale and clamp, but never take the integer part,
        # so a fractional input leaves a fractional residue.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      size := max 2 scaled\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart scales the fraction by the population and "
            "clamps it at two but never reduces it to an integer count — the exact "
            "pre-change behaviour. The conditioned value is consumed downstream by "
            "a routine that accepts only a whole count and REJECTS a fractional "
            "one outright with a type error, which is the failure the issue "
            "reports; the failing test drives the public entry point with a "
            "fractional sizing parameter and would still raise, so it does NOT "
            "resolve. A verifying rival here would be a true "
            "verify-does-not-imply-resolve break on the load-bearing facet."),
        "rationale": (
            "REJECT from O1, facet (I) INTEGRALITY: `asAbsoluteCount` takes the "
            "integer part of the scaled value, and the rival returns the scaled "
            "value itself, which need not be integral. Facets (B) and (C) still "
            "hold (the branch and the clamp are intact), so integrality is the "
            "ONLY failing facet — the cleanest possible attribution. Refuted at "
            "(value=1/10, population=31): the product is 31/10, the spec demands "
            "3, the rival yields 31/10. If it verified ⇒ SPEC-TOO-WEAK on exactly "
            "the clause that separates the pre-image from the fix. "
            "(Sibling: uniq-unfloored-echo.)"),
        "witness": _wit1("1/10", "31/10", 31),
    },
    {
        "id": "reject-paired-primary-not-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        # The same integrality break on the SECOND obligation's PRIMARY slot
        # only — the secondary slot's conditioning is left correct, so this
        # isolates O2's primary facet. Distinct obligation, distinct input.
        "module": _impl2(
            "    let mut primary : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      primary := max 2 scaledPrimary\n"
            "    let mut secondary : Rat := primary\n"
            "    if secondaryGiven then\n"
            "      secondary := secondaryValue\n"
            "    if secondary ≤ 1 then\n"
            "      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)\n"
            "    return { primary := primary, secondary := secondary }"),
        "refinement": (
            "the faithful counterpart fixes the integer conversion at the "
            "single-parameter site but leaves the PRIMARY slot of the paired site "
            "un-truncated. The failing test exercises the paired entry point with "
            "BOTH sizing parameters given as fractions, so a fractional residue "
            "surviving on the primary slot still reaches the whole-count-only "
            "consumer and still raises — it does NOT resolve. This is the rival "
            "that shows a partial fix is not enough: the same defect must be "
            "closed at every conditioning site, and this obligation is the one "
            "that observes the second site."),
        "rationale": (
            "REJECT from O2, facet (I) on the PRIMARY slot: `resolvedPairedSizes` "
            "pins the primary component to `asAbsoluteCount value scaledPrimary`, and "
            "the rival leaves the un-truncated scaled value there while "
            "conditioning the secondary slot correctly. Isolates the second "
            "obligation's primary facet — the first obligation's rivals cannot "
            "reach it. Refuted at (value=1/10, secondaryValue=3, "
            "secondaryGiven=true, population=71): the primary product is 71/10, "
            "the spec demands 7, the rival yields 71/10; the supplied secondary is "
            "an absolute count (3 > 1) so it passes through and the primary is the "
            "sole disagreement. Moves `secondaryValue` above one, the only "
            "witness that probes the secondary's pass-through branch. If it "
            "verified ⇒ SPEC-TOO-WEAK. (Sibling: uniq-unfloored-echo, re-aimed at "
            "the second obligation.)"),
        "witness": _wit2("1/10", "3", "71/10", "213", "true", 71),
    },

    # ---- facet (D): TRUNCATION DIRECTION ----
    {
        "id": "reject-round-up",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the integer part ABOVE the product instead of below it: integral
        # (so facet (I) holds) but over-counts on every non-integral product.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      size := (((max 2 (Rat.ceil scaled)) : Int) : Rat)\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart rounds the scaled fraction UP to a whole "
            "count. It is integral, so the type error is gone and a test that only "
            "checked the type would pass — but the count is one too many on every "
            "non-integral product. The failing test asserts that the fractional "
            "run produces the SAME result as the equivalent absolute-count run, "
            "and an over-large count changes that result, so it does NOT resolve. "
            "This is the rival that shows the spec pins the direction of "
            "truncation, not merely integrality."),
        "rationale": (
            "REJECT from O1, facet (D) TRUNCATION DIRECTION: the spec takes the "
            "integer part BELOW the scaled value; the rival takes the one above, "
            "which differs on every non-integral product. Facets (I), (B) and (C) "
            "hold, so direction is the sole failing facet. Refuted at "
            "(value=1/10, population=41): the product is 41/10, the spec demands "
            "4, the rival yields 5. If it verified ⇒ SPEC-TOO-WEAK (integrality "
            "alone would be a strictly weaker spec than the fix needs). "
            "(Sibling: uniq-overcount-ceiling.)"),
        "witness": _wit1("1/10", "41/10", 41),
    },
    {
        "id": "reject-round-to-nearest",
        "kind": "uniqueness",
        "expect": "reject",
        # Round to nearest (integer part of the product plus one half): agrees
        # with the spec on any product whose fractional part is below one half,
        # and diverges above it. A wider-agreement near-miss than round-up.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      size := (((max 2 (Rat.floor (scaled + 1/2))) : Int) : Rat)\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart rounds the scaled fraction to the NEAREST "
            "whole count. It agrees with the specified conversion on every product "
            "whose fractional part is below one half — including the fractions the "
            "failing test itself uses — which is precisely why it is dangerous: it "
            "is integral and it passes the failing test, yet it diverges from the "
            "documented conversion on any product at or past the half-way point, "
            "returning a count one too large. Callers that pass such a fraction "
            "get a different result from the equivalent absolute-count call, "
            "breaking the equivalence the surrounding suite relies on, so a patch "
            "with this body does NOT resolve the instance as a whole. The spec is "
            "deliberately stronger than the failing test on this sub-domain."),
        "rationale": (
            "REJECT from O1, facet (D): rounding to nearest coincides with the "
            "specified integer part on a large part of the domain and over-counts "
            "by one past the half-way point. A WIDER-AGREEMENT near-miss than "
            "reject-round-up (which is wrong on every non-integral product), so it "
            "gets its own witness inside its own narrower wrong sub-domain rather "
            "than sharing one: refuted at (value=1/2, population=5), where the "
            "product is exactly 5/2, the spec demands 2 and the rival yields 3. "
            "At reject-round-up's point (1/10, 41) this rival would AGREE with "
            "gold, so the distinct input is what makes the sub-domain claim in "
            "this rationale real. If it verified ⇒ SPEC-TOO-WEAK. "
            "(Sibling: uniq-round-to-nearest.)"),
        "witness": _wit1("1/2", "5/2", 5),
    },
    {
        "id": "reject-off-by-one-on-whole",
        "kind": "uniqueness",
        "expect": "reject",
        # The tightest near-miss: integer part above the product, minus one.
        # That EQUALS the specified conversion on every NON-integral product and
        # undercounts by one exactly when the product is a whole number.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      size := (((max 2 (Rat.ceil scaled - 1)) : Int) : Rat)\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart is an off-by-one truncation that agrees with "
            "the specified conversion on EVERY non-integral product — including "
            "both fractions the failing test uses — and undercounts by exactly one "
            "when the scaled value lands on a whole number. It therefore passes the "
            "failing test while silently producing a different count from the "
            "equivalent absolute-count call for any caller whose fraction times the "
            "population is integral (a fraction of one, or any fraction dividing "
            "the population evenly), so the fractional/absolute equivalence the "
            "surrounding suite asserts breaks on those inputs and a patch with this "
            "body does NOT resolve. The TIGHTEST near-miss in the battery: the spec "
            "must pin the conversion on the boundary, not just in the interior."),
        "rationale": (
            "REJECT from O1, facet (D) at the INTEGRAL BOUNDARY. This rival agrees "
            "with the spec on strictly more of the domain than either other "
            "direction rival — it is wrong ONLY where the scaled product is a whole "
            "number — so it must be refuted inside that measure-zero sub-domain and "
            "cannot share a witness with them. Refuted at (value=1/2, "
            "population=10): the product is exactly 5, the spec demands 5, the "
            "rival yields 4. At every other witness point in this battery the "
            "product is non-integral and this rival AGREES with gold, which is what "
            "makes the boundary claim in this rationale demonstrated rather than "
            "asserted. If it verified ⇒ SPEC-TOO-WEAK on the boundary. "
            "(Sibling: uniq-strict-undercount.)"),
        "witness": _wit1("1/2", "5", 10),
    },

    # ---- facets (V) and (C): VALUE DEPENDENCE and THE FLOOR AT TWO ----
    {
        "id": "reject-constant-two",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse the conversion to the constant lower bound: correct exactly
        # where the real count is two, wrong wherever it exceeds two.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      size := 2\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart collapses every fractional sizing parameter "
            "to the constant lower bound of two, ignoring the population "
            "entirely. It is integral — the type error is gone — and it is even "
            "CORRECT for fractions small enough that the real count is two, which "
            "is why a test checking only the type would accept it. But the failing "
            "test uses a fraction whose count must exceed two, and a count of two "
            "gives a different result from the equivalent absolute-count run, so it "
            "does NOT resolve. This is the VALUE-DEPENDENCE rival: it shows the "
            "spec forces the result to be computed FROM the inputs rather than "
            "merely satisfying the bound."),
        "rationale": (
            "REJECT from O1, facet (V) VALUE DEPENDENCE: the result must be a "
            "function of the scaled value, and the rival returns a constant that "
            "happens to satisfy the lower bound (C) and integrality (I) on every "
            "input. Guards against reading the conversion as 'any whole number at "
            "least two will do'. Refuted at (value=1/10, population=71), the "
            "largest population probed: the spec demands 7 and the rival yields 2. "
            "If it verified ⇒ SPEC-TOO-WEAK in the strongest sense — the spec "
            "would not force the computation at all. "
            "(Sibling: uniq-floor-of-two-only.)"),
        "witness": _wit1("1/10", "71/10", 71),
    },
    {
        "id": "reject-no-lower-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the integer part but drop the floor at two: correct wherever the
        # scaled value already reaches two, wrong on a small fraction.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      size := ((Rat.floor scaled : Int) : Rat)\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart takes the integer part of the scaled value "
            "but drops the guarantee that the count never falls below two. It "
            "agrees with the specified conversion on every input whose scaled value "
            "already reaches two — including the failing test's own inputs — and "
            "produces one, or zero, for a small fraction on a small population. "
            "Such a count is degenerate for the downstream computation (the "
            "documented contract promises at least two), so callers in that regime "
            "get behaviour the surrounding suite does not tolerate and a patch with "
            "this body does NOT resolve the instance as a whole."),
        "rationale": (
            "REJECT from O1, facet (C) THE FLOOR AT TWO: `asAbsoluteCount` clamps "
            "the integer part from below at two, and the rival omits the clamp. "
            "Facets (I), (B) and (D) hold, so the lower bound is the sole failing "
            "facet — no other rival attacks it in isolation (reject-constant-two "
            "satisfies it). Refuted at (value=1/10, population=11), the smallest "
            "population probed: the product is 11/10, its integer part is 1, and "
            "the spec demands 2. Probes the clamp-active sub-domain that every "
            "other first-obligation witness sits outside of. If it verified ⇒ "
            "SPEC-TOO-WEAK. (No sibling: nagini's clamp is baked into its `@Pure` "
            "helper and its impl region cannot omit it, so this facet is newly "
            "attackable on this carrier.)"),
        "witness": _wit1("1/10", "11/10", 11),
    },

    # ---- facet (B): BRANCH SELECTION ----
    {
        "id": "reject-conversion-unguarded",
        "kind": "uniqueness",
        "expect": "reject",
        # Run the fraction conversion UNCONDITIONALLY, so an absolute count gets
        # scaled by the population too instead of passing through.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    size := (((max 2 (Rat.floor scaled)) : Int) : Rat)\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart applies the fraction-to-count conversion "
            "unconditionally, dropping the guard that distinguishes the two input "
            "forms. It is CORRECT on every fractional input — so it passes the "
            "failing test, which supplies fractions — but it also multiplies an "
            "input that was ALREADY an absolute count by the population, inflating "
            "it enormously. Every caller that passes an absolute count (the "
            "documented default form) then gets a wildly wrong count, so the "
            "surrounding suite's absolute-count cases break and a patch with this "
            "body does NOT resolve. This rival is why the spec's branch guard is "
            "load-bearing and not incidental."),
        "rationale": (
            "REJECT from O1, facet (B) BRANCH SELECTION: `asAbsoluteCount` applies "
            "the conversion only when `value ≤ 1` and returns an absolute count "
            "as-is; the rival converts unconditionally. This is the ONLY rival "
            "that moves the `value` binder ABOVE one, into the pass-through branch "
            "— every other first-obligation witness sits in the fraction branch, so "
            "without it a rival mishandling only absolute-count inputs would go "
            "unnoticed and the battery would say nothing about the guard. Refuted "
            "at (value=5, population=31): the spec demands the input back "
            "unchanged as 5, the rival yields 155. If it verified ⇒ "
            "SPEC-TOO-WEAK on the branch. (No sibling: nagini's helper applies the "
            "clamp inside a `@Pure` function its impl region cannot bypass, so the "
            "guard is newly attackable on this carrier.)"),
        "witness": _wit1("5", "155", 31),
    },
    {
        "id": "reject-guard-strict-at-one",
        "kind": "uniqueness",
        "expect": "reject",
        # The BOUNDARY of the guard: fire the conversion only on a value strictly
        # below one, so a value of exactly one takes the pass-through path. Wrong
        # on that single input and correct everywhere else.
        "module": _impl1(
            "    let mut size : Rat := value\n"
            "    if value < 1 then\n"
            "      size := (((max 2 (Rat.floor scaled)) : Int) : Rat)\n"
            "    return size"),
        "refinement": (
            "the faithful counterpart writes the form-selecting comparison as a "
            "STRICT one, so a sizing parameter of exactly one is treated as an "
            "absolute count instead of as a fraction of the whole population. It "
            "agrees with the specified conversion on every other input — including "
            "every fraction the failing test supplies, so the failing test passes — "
            "and is wrong only at that one value, where the documented interval is "
            "half-open and CLOSED at the top: a parameter of one means the entire "
            "population, not a count of one. A caller passing it gets a count of "
            "one, which is below the promised minimum of two and degenerate for the "
            "downstream computation, so the surrounding suite's boundary cases break "
            "and a patch with this body does NOT resolve. An off-by-one in a "
            "comparison operator is among the likeliest ways a real author gets this "
            "conditioning wrong, which is what makes the boundary worth pinning."),
        "rationale": (
            "REJECT from O1, facet (B) at the BOUNDARY of the guard. "
            "`asAbsoluteCount` selects the conversion on `value ≤ 1`; the rival "
            "selects it on `value < 1`, so the two disagree at exactly one point in "
            "the whole domain. reject-conversion-unguarded attacks the same facet "
            "from the other side (it drops the guard entirely, and is wrong on the "
            "pass-through branch as a whole), so neither subsumes the other and "
            "neither can borrow the other's witness: at (5, 31) this rival AGREES "
            "with gold. Refuted at (value=1, population=5), the only input where it "
            "differs: the spec demands the whole population as an absolute count, "
            "namely 5, and the rival passes the raw 1 straight through. This is the "
            "ONLY case at which `value` takes the guard's boundary value — every "
            "other first-obligation witness sits strictly inside one branch or the "
            "other — so without it a rival that mishandles only the closed end of "
            "the documented interval would verify unnoticed. If it verified ⇒ "
            "SPEC-TOO-WEAK on the boundary of the branch condition. (No sibling: "
            "nagini's modeled function receives the ALREADY-SCALED product, so the "
            "form-selecting comparison happens before its impl region is entered "
            "and this boundary is newly attackable on this carrier.)"),
        "witness": _wit1("1", "5", 5),
    },

    # ---- facets (S1)-(S3): the SECOND obligation's own structure ----
    {
        "id": "reject-paired-secondary-raw",
        "kind": "uniqueness",
        "expect": "reject",
        # Condition the primary correctly, then return the supplied secondary
        # WITHOUT conditioning it at all.
        "module": _impl2(
            "    let mut primary : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)\n"
            "    let mut secondary : Rat := primary\n"
            "    if secondaryGiven then\n"
            "      secondary := secondaryValue\n"
            "    return { primary := primary, secondary := secondary }"),
        "refinement": (
            "the faithful counterpart conditions the primary sizing parameter but "
            "hands the secondary one downstream exactly as supplied, never "
            "converting it. The failing test supplies BOTH parameters as "
            "fractions, so the secondary arrives at the whole-count-only consumer "
            "still fractional and still raises the very error the issue reports — "
            "it does NOT resolve. It is the same defect as the primary-slot rival "
            "but on the slot the first obligation cannot observe at all, which is "
            "exactly why this obligation exists."),
        "rationale": (
            "REJECT from O2, facet (S1) THE SECONDARY IS CONDITIONED TOO: "
            "`resolvedPairedSizes` pins the secondary component to "
            "`asAbsoluteCount` of the chosen source, and the rival returns that "
            "source raw. The primary component is correct, so the secondary "
            "conditioning is the sole failing facet. Refuted at (value=1/2, "
            "secondaryValue=3/25, secondaryGiven=true, population=50): the "
            "secondary's product is 6, the spec demands 6, the rival yields 3/25. "
            "If it verified ⇒ SPEC-TOO-WEAK (a spec blind to the second slot would "
            "certify a half-fix). (No sibling: nagini models one scalar conversion, "
            "so it has no paired obligation.)"),
        "witness": _wit2("1/2", "3/25", "25", "6", "true", 50),
    },
    {
        "id": "reject-paired-ignores-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the supplied-secondary flag entirely: always derive the
        # secondary from the primary, discarding the caller's value.
        "module": _impl2(
            "    let mut primary : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)\n"
            "    let mut secondary : Rat := primary\n"
            "    if secondary ≤ 1 then\n"
            "      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)\n"
            "    return { primary := primary, secondary := secondary }"),
        "refinement": (
            "the faithful counterpart ignores the supplied secondary parameter and "
            "always derives the secondary from the primary — i.e. it treats the "
            "parameter as if it had been omitted. The failing test supplies a "
            "secondary fraction DIFFERENT from the primary one and asserts the "
            "outcome matches the equivalent absolute-count run; discarding the "
            "caller's value substitutes a different count and changes that "
            "outcome, so it does NOT resolve. It is also a silent contract "
            "violation for every caller that sets the parameter, which is worse "
            "than the original defect."),
        "rationale": (
            "REJECT from O2, facet (S2) THE SUPPLIED SECONDARY IS HONOURED: the "
            "spec conditions `if secondaryGiven then secondaryValue else p`, and "
            "the rival conditions `p` regardless, so the `secondaryValue` binder "
            "is dead in the rival. Refuted at (value=1/10, secondaryValue=8/100, "
            "secondaryGiven=true, population=31): the spec's secondary is the "
            "integer part of 62/25, namely 2, while the rival re-conditions the "
            "primary 3 and yields 3. Note the primary component AGREES here, so "
            "the disagreement is attributable to (S2) alone. If it verified ⇒ "
            "SPEC-TOO-WEAK (the supplied value would be unconstrained). "
            "(No sibling: nagini has no paired obligation.)"),
        "witness": _wit2("1/10", "8/100", "31/10", "62/25", "true", 31),
    },
    {
        "id": "reject-paired-defaults-to-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the default: always start the secondary from the SUPPLIED value,
        # even when the flag says it was not supplied.
        "module": _impl2(
            "    let mut primary : Rat := value\n"
            "    if value ≤ 1 then\n"
            "      primary := (((max 2 (Rat.floor scaledPrimary)) : Int) : Rat)\n"
            "    let mut secondary : Rat := secondaryValue\n"
            "    if secondary ≤ 1 then\n"
            "      secondary := (((max 2 (Rat.floor scaledSecondary)) : Int) : Rat)\n"
            "    return { primary := primary, secondary := secondary }"),
        "refinement": (
            "the faithful counterpart drops the defaulting rule: it always "
            "conditions the secondary slot from the secondary argument, even when "
            "the caller did not supply one. It is CORRECT on every input that DOES "
            "supply the parameter — including the failing test — and wrong exactly "
            "when the parameter is absent, where the documented behaviour is to "
            "fall back to the already-conditioned primary. Callers relying on the "
            "default (the common case, since the parameter is optional) get a "
            "count derived from an unrequested value instead, so the surrounding "
            "suite's default-path cases break and a patch with this body does NOT "
            "resolve. It is the mirror image of reject-paired-ignores-supplied: "
            "each is correct exactly where the other is wrong."),
        "rationale": (
            "REJECT from O2, facet (S3) THE DEFAULT IS THE CONDITIONED PRIMARY: "
            "the spec's source is `if secondaryGiven then secondaryValue else p`, "
            "and the rival uses `secondaryValue` unconditionally. This is the ONLY "
            "witness that sets `secondaryGiven = false`, so it is what keeps that "
            "binder from being pinned at one value across the whole reject set — "
            "without it a rival mishandling only the default path would verify "
            "unnoticed. Refuted at (value=1/10, secondaryValue=1/4, "
            "secondaryGiven=false, population=31): the spec defaults the secondary "
            "to the conditioned primary 3 (an absolute count, so it passes "
            "through as 3), while the rival conditions the unrequested 1/4 and "
            "yields the integer part of 31/4, namely 7. If it verified ⇒ "
            "SPEC-TOO-WEAK on the defaulting rule. (No sibling: nagini has no "
            "paired obligation.)"),
        "witness": _wit2("1/10", "1/4", "31/10", "93", "false", 31),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
# The sibling battery ships 8 SPEC cases (2 soundness positives, 1
# admissibility, 5 uniqueness rivals) and an EMPTY axiom lane. It contracts ONE
# function, `neighborhood_size(scaled: float) -> float`, over a single
# pass-by-value scalar: the repository's ALREADY-SCALED value, converted to a
# whole count by a verified counting loop, with the clamp hidden inside a `@Pure`
# helper. Its four postcondition clauses (integrality; at least two; not above
# the clamped value; the clamped value below the next integer) jointly pin the
# result to the integer part of the clamped scaled value.
#
# This bundle's carrier is WIDER in one direction and NARROWER in another, and
# both differences drive the case list:
#   * WIDER: it models the conversion at its call sites, as TWO contracted
#     methods over the RAW inputs (`value`, `population`, and for the paired
#     method `secondaryValue` and `secondaryGiven`) rather than one method over
#     the pre-scaled product. So the scaling, the branch guard, the clamp and the
#     paired defaulting are all inside the impl region and therefore ATTACKABLE
#     here, where nagini's impl region could not reach them (its scaling happens
#     before the modeled function is entered, and its clamp lives in a `@Pure`
#     helper an impl variant cannot bypass). That yields six rivals with no
#     sibling, plus one extra positive.
#   * NARROWER: nagini's counting loop and its three loop invariants are the
#     substance of both its positive controls, and there is no loop here at all —
#     the conversion is a straight-line expression. The positives are therefore
#     re-expressed as reshapes of that expression, which is the same ARGUMENT
#     (a faithful author's alternative shape must verify) on this carrier's terms.
#
#   nagini case                  kind          -> here                                disposition
#   ---------------------------------------------------------------------------------------------
#   pos-reorder-rename           soundness     -> pos-expression-ladder               PORTED (re-expressed)
#   pos-single-carrier           soundness     -> pos-named-intermediates             PORTED (re-expressed)
#   admiss-f2p-shaped-input      admissibility -> admiss-nondegenerate-post-image     PORTED (re-aimed)
#   uniq-unfloored-echo          uniqueness    -> reject-fraction-not-truncated       PORTED
#                                              +  reject-paired-primary-not-truncated PORTED (2nd obligation)
#   uniq-overcount-ceiling       uniqueness    -> reject-round-up                     PORTED
#   uniq-round-to-nearest        uniqueness    -> reject-round-to-nearest             PORTED
#   uniq-strict-undercount       uniqueness    -> reject-off-by-one-on-whole          PORTED (re-expressed)
#   uniq-floor-of-two-only       uniqueness    -> reject-constant-two                 PORTED
#   AXIOM_TESTS (empty)          axiom         -> (none)                              N/A (already empty)
#   (no counterpart)             uniqueness    -> reject-no-lower-clamp               NEW (carrier widening)
#   (no counterpart)             uniqueness    -> reject-conversion-unguarded         NEW (carrier widening)
#   (no counterpart)             uniqueness    -> reject-guard-strict-at-one          NEW (audit: guard boundary)
#   (no counterpart)             uniqueness    -> reject-paired-secondary-raw         NEW (2nd obligation)
#   (no counterpart)             uniqueness    -> reject-paired-ignores-supplied      NEW (2nd obligation)
#   (no counterpart)             uniqueness    -> reject-paired-defaults-to-supplied  NEW (2nd obligation)
#   (no counterpart)             soundness     -> pos-paired-explicit-source          NEW (2nd obligation)
#
# EVERY sibling SPEC case is accounted for and NONE is omitted. Totals: 16 cases
# = 3 soundness positives + 1 admissibility + 12 uniqueness rivals (4 verify, 12
# reject).
#
# reject-guard-strict-at-one was added by the INDEPENDENT AUDIT of this battery,
# not by the port. The port attacked facet (B) only by dropping the guard
# outright, which leaves the guard's BOUNDARY — a value of exactly one, the
# closed end of the documented half-open interval — unprobed by any case: the
# port's `value` binder took the values {1/10, 1/2, 5}, all strictly inside one
# branch or the other. A strict-comparison rival disagrees with the spec at that
# single point and nowhere else (differential-tested over 16 values x populations
# 1..399: 399 disagreements, ALL at value = 1), and its witness was SEEN to
# discriminate — EXIT 0 against the rival, EXIT 1 against the frozen solution
# with `decide proved that the proposition ... is false`.
#
# RE-EXPRESSED, not translated:
#   * pos-reorder-rename / pos-single-carrier reorder the sibling's loop-body
#     updates and rename its accumulator locals, keeping the loop invariants
#     verbatim. There is no loop here, so the same argument is carried by two
#     reshapes of the straight-line conversion: pos-expression-ladder drops
#     mutation entirely for a `let := if …` ladder (and so writes the
#     pass-through branch out explicitly instead of leaving it implicit in the
#     slot's initial value), and pos-named-intermediates decomposes the nested
#     expression into named typed intermediates (scaled product → integer part →
#     clamp). Both verified out-of-band (EXIT 0) under the frozen proof.
#   * uniq-strict-undercount uses a strict loop bound, which undercounts by one
#     exactly when the value is already whole. With no loop, the same
#     sub-domain is hit by "the integer part above the product, minus one":
#     identical to the specified conversion on every non-integral product,
#     one too small precisely on a whole one. Same boundary claim, same
#     refutation sub-domain, expression-level mechanics.
#   * admiss-f2p-shaped-input asserts a normally-shaped input satisfies the
#     precondition. Here both preconditions are met by every normally-shaped
#     input, so that probe alone is degenerate; the case is re-aimed at the
#     sharper residual risk (a degenerate post-image) by pinning the conversion
#     at three SEPARATING outcomes. Same class, sharper target.
#
# DROPPED — one rival, and the reason is NOT proof difficulty:
#   * A "default the secondary slot from the RAW primary input rather than its
#     CONDITIONED value" rival was authored and DROPPED as not actually wrong on
#     this carrier. Attempting its witness at (value=1/10, secondaryValue=1/4,
#     secondaryGiven=false, population=31) left the tester unprovably false
#     under every tactic tried, because the two impls AGREE there. Re-confirmed
#     independently of any tactic by transliterating both post-images and
#     differential-testing them over 9 fraction/absolute values x both flag
#     settings x populations 1..199: ZERO disagreements — and in general, since
#     the conditioned primary is an integer at least two, re-conditioning it is a
#     no-op (values above one pass through), so seeding the slot from the raw
#     input and from the conditioned primary reach the same result whenever the
#     raw input is a fraction. Its abstraction collapses a distinction that a
#     more operational carrier would keep. Per the porting rule, a rival with no
#     discriminating witness is dropped and reported rather than shipped: no
#     reject case here rests on a witness that was not SEEN to discriminate.
#     For the record it does not verify either (the frozen proof does not close
#     for its reshaped body, and `omega` on the residual goal reports a possible
#     counterexample over `(max 2 (value * population).floor * population).floor`
#     — a proof gap, not a behavioural difference), so it could NOT be salvaged
#     as a soundness positive without a new lemma about that iterated floor,
#     which rule 3 forbids. It is therefore absent in both directions, and this
#     is the one genuine gap in the port: an OBSERVABLY EQUIVALENT reshape of the
#     secondary slot's seed is not certified by any case here.
#
# FRAME / PERMISSION-MUTATION: VACUOUS, and the sibling itself records the class
#   N/A for the same underlying reason (its only input is a pass-by-value scalar
#   with no read-only heap reference — nothing to overwrite to satisfy the
#   postcondition vacuously). Velvet is referentially transparent: every
#   parameter of both methods is an immutable value, neither declares a `mut`
#   binder, and there is no heap, aliasing or permission system. Unlike bundles
#   with a `mut` output slot there is not even a frame ARGUMENT to re-express
#   here, so no substitute is fabricated.
#
# DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
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
# CLAUSE / BINDER COVERAGE (what replaces case-count parity).
#   BOTH obligations are DEFENDED and ATTACKED:
#     prove_correct conditionSizeParameter — defended by pos-expression-ladder,
#       pos-named-intermediates and admiss-nondegenerate-post-image; attacked by
#       seven rivals.
#     prove_correct resolvePairedSizes     — defended by
#       pos-paired-explicit-source; attacked by four rivals.
#   EVERY independent facet of each post-image is attacked:
#     (B) branch selection   -> reject-conversion-unguarded (the guard dropped
#                               entirely: wrong across the whole pass-through
#                               branch) and reject-guard-strict-at-one (the guard
#                               made strict: wrong at exactly one input, the
#                               closed end of the interval) — two nested
#                               sub-domains, each refuted inside its own
#     (I) integrality        -> reject-fraction-not-truncated,
#                               reject-paired-primary-not-truncated
#     (D) truncation direction -> reject-round-up (wrong on every non-integral
#                               product), reject-round-to-nearest (wrong past the
#                               half-way point only), reject-off-by-one-on-whole
#                               (wrong on whole products only) — three nested
#                               sub-domains, each refuted INSIDE its own, so no
#                               near-miss borrows a coarser rival's witness
#     (C) floor at two       -> reject-no-lower-clamp
#     (V) value dependence   -> reject-constant-two
#     (S1) secondary conditioned -> reject-paired-secondary-raw
#     (S2) supplied secondary honoured -> reject-paired-ignores-supplied
#     (S3) default is the conditioned primary -> reject-paired-defaults-to-supplied
#   EVERY INPUT BINDER of both spec predicates is VARIED by the reject witnesses,
#   so no binder is held at a single value across the set:
#     value          {1/10, 1/2, 1, 5} — spans BOTH branches of the guard AND its
#                                      boundary (5 > 1 is the pass-through branch,
#                                      reached only by reject-conversion-unguarded;
#                                      1 is the closed end of the documented
#                                      interval, reached only by
#                                      reject-guard-strict-at-one)
#     population     {5, 10, 11, 31, 41, 50, 71} — includes the clamp-active
#                                      small end (11, via reject-no-lower-clamp)
#                                      and the large end (71)
#     secondaryValue {8/100, 3/25, 1/4, 3} — spans both forms: fractions AND an
#                                      absolute count (3 > 1, the pass-through
#                                      branch on the secondary slot)
#     secondaryGiven {true, false}   — both values; `false` is reached only by
#                                      reject-paired-defaults-to-supplied, which
#                                      is why that case is what keeps this binder
#                                      from being pinned
#   The twelve witnesses sit at TWELVE DISTINCT input points (pts=12):
#     (1/10,31) (1/10,41) (1/2,5) (1/2,10) (1/10,71) (1/10,11) (5,31) (1,5)
#     (1/10,3,true,71) (1/2,3/25,true,50) (1/10,8/100,true,31) (1/10,1/4,false,31)
#   No two rivals share a witness. The three direction rivals in particular sit
#   at three different points chosen so that each is INSIDE its own wrong
#   sub-domain and the other two agree with gold there, so each rationale's
#   sub-domain claim is demonstrated by the manifest rather than merely asserted.
#
# CARRIER NOTE. The carrier is fully TRANSPARENT (no `opaque` callee, no axiom),
#   so no witness needs to condition on an unknown term: every one is stated at
#   concrete literals and binds nothing, making the gate's inconsistency probe a
#   no-op. Plain `decide` is nonetheless STUCK on both files — the derived
#   `Decidable` instance does not reduce through `Rat.mul` / `Rat.floor`, whose
#   definitions the default reducible transparency hides — so each witness closes
#   with `with_unfolding_all decide`, which lifts that restriction and decides the
#   goal in the ELABORATOR. A real proof with no `sorry` / `admit` /
#   `native_decide` / `axiom`.
#
#   The tactic choice is load-bearing, not cosmetic. `decide +kernel` also makes
#   every witness elaborate against its rival and fail against gold, but gold's
#   failure is then the STUCK-reduction error rather than a verdict, and that
#   error is identical for a false claim, a true claim and a trivial one — so it
#   attributes nothing to the spec, and the gate correctly refuses such a case as
#   `witness-undecided`. Measured on gold at (1/10, 31) under `decide +kernel`:
#   `= false` -> stuck (EXIT 1), `= true` -> EXIT 0. Under
#   `with_unfolding_all decide` the same gold build instead reports `decide proved
#   that the proposition ... is false`, and the TRUE claim closes EXIT 0, so each
#   witness was SEEN to discriminate for the right reason: ELABORATES against its
#   rival (EXIT 0), REFUTED against the frozen solution (EXIT 1, genuine verdict).
AXIOM_TESTS = []
