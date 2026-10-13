"""properties.py — G-PBT falsification battery for mwaskom__seaborn-3069 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each SPEC
case is a full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte
(region surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a
case that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_nominalAxis``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``): it
carries that battery's adversarial ARGUMENT across to this backend's carrier. It
is not a translation of the nagini text.

DEFENDED SURFACE (one total function returning a two-component decision record)
------------------------------------------------------------------------------
A single modeled function decides, for ONE plot axis at figure-finalization time,
how that axis is drawn:

  nominalAxis (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout

where ``AxisLayout`` carries ``gridHidden : Bool`` (finalization forces the grid
off) and ``fixedLimit : Option (ℚ × ℚ)`` (``some (lo, hi)`` when finalization pins
the axis extent, ``none`` when it defers to the ordinary data-margin logic).

``problem_spec_nominalAxis`` has FOUR independent top-level clauses:

  (C1) result.gridHidden = isNominal
  (C2) isNominal = true → hasLimit = false → result.fixedLimit
         = some (if isY then (nticks - 1/2, -1/2) else (-1/2, nticks - 1/2))
  (C3) isNominal = false → result.fixedLimit = none
  (C4) hasLimit  = true  → result.fixedLimit = none

WHAT DRIVES THE REJECTS. (C1) is a BICONDITIONAL over ``isNominal``, so it is
load-bearing in both directions. (C2) pins the extent as an ORDERED ℚ pair —
equality on ``ℚ × ℚ`` is component-wise and order-sensitive — with a lower edge at
``-1/2``, an upper edge tied to the observed tick count, and the pair reversed on a
vertical axis; each of those four aspects is a separate way to be wrong. (C3) and
(C4) are the two IDENTITY clauses: they say the pin is applied on neither a
non-categorical axis nor an axis the caller already pinned. They are the analogue
of nagini's ``!cat & !explicit`` identity clause, which that battery documents as
NOT optional — the clause exists because a rival that drops the categorical gate
clobbers ordinary axes and breaks hidden PASS_TO_PASS behavior.

Each reject case's ``refinement`` was established EMPIRICALLY, not argued: the
rival's faithful real edit was applied in the instance image and the full
FAIL_TO_PASS + PASS_TO_PASS set (96 tests) was run. The recorded outcome per case
is quoted in its ``refinement``. Eight of the ten rivals fail that run and so do
not resolve; two (``reject-grid-off-everywhere`` and
``reject-upper-edge-nat-truncated``) resolve it, which their ``refinement``s state
outright rather than claiming a break they do not have — see WHAT WAS DROPPED
below for why that does not disqualify a reject case. Those two are the most
valuable cases in the battery for exactly that reason: a wrong impl the test suite
CANNOT see is the hole the spec has to catch by itself.

BINDER / CLAUSE COVERAGE. Ten rejects refute at NINE distinct input points,
varying every input binder of the spec predicate: ``isY`` over both values,
``isNominal`` over both, ``hasLimit`` over both, and ``nticks`` over
{0, 1, 2, 3, 4, 5, 6}. All four combinations of the two GATING booleans
(``isNominal`` × ``hasLimit``) appear among the witness points. Every clause is
attacked, and (C1) in both directions:

  * (C1) nominal→hidden      : reject-grid-never-hidden
  * (C1) ordinary→not-hidden : reject-grid-inverted (wrong in BOTH directions)
  * (C1) ordinary→not-hidden : reject-grid-off-everywhere (a strict NEAR-MISS:
                               wrong in that ONE direction only)
  * (C2) lower edge          : reject-lower-edge-zero
  * (C2) upper edge, tied    : reject-upper-edge-off-by-one
  * (C2) upper edge, ignored : reject-upper-edge-constant
  * (C2) upper edge, carrier : reject-upper-edge-nat-truncated (the STRICTEST
                               near-miss: wrong at exactly ONE input, nticks = 0,
                               where a count-domain step-back saturates instead of
                               going below its floor; agrees with gold everywhere
                               else, so it is the case that shows the ℚ carrier of
                               mapping.md is load-bearing)
  * (C2) vertical reversal   : reject-no-vertical-reverse
  * (C3) ordinary axis       : reject-pin-without-nominal-gate
  * (C4) caller-pinned axis  : reject-pin-over-explicit

Two of those attack a SINGLE point rather than a sub-domain
(``reject-upper-edge-nat-truncated`` at nticks = 0, ``reject-grid-off-everywhere``
at the ordinary-axis direction of (C1) alone), which is what keeps the "every
binder varies" claim above from degenerating into two spellings of the same point:
each rival is refuted at an input where EVERY other rival in the battery agrees
with the frozen solution.

Nine points for ten rejects, and the one collision is forced rather than
careless: ``reject-upper-edge-nat-truncated`` and ``reject-grid-never-hidden``
both witness at (isY, isNominal, hasLimit, nticks) = (false, true, false, 0).
The truncated-edge rival is wrong at nticks = 0 and NOWHERE else, so 0 is the
only count it can be refuted at; the grid rival is wrong on a whole sub-domain
and merely happens to be witnessed there too. The two witnesses discriminate on
different clauses at that shared point -- (C2)'s extent value versus (C1)'s
gridHidden field -- so neither is a respelling of the other, and moving the grid
rival's witness to another count would buy a tenth point without adding any
information. ``scripts/pbt_coverage.py`` reports this as ``pts=9-9`` on ten
rejects; that is the expected reading for this battery, not a finding.

WHY SPEC-TOO-WEAK IS STRUCTURALLY UNREACHABLE HERE (audit result, machine-checked)
-----------------------------------------------------------------------------------
The rivals below are a finite sample, but on this spec a stronger statement holds
and was PROVEN with the real verifier: ``problem_spec_nominalAxis`` is EXACTLY
CHARACTERIZING. Any result satisfying it, at any input, is equal to the frozen
implementation's output —

  example (isY isNominal hasLimit : Bool) (nticks : Nat) (r : AxisLayout)
      (h : problem_spec_nominalAxis isY isNominal hasLimit nticks r) :
      r = implementation_nominalAxis isY isNominal hasLimit nticks := by
    obtain ⟨h1, h2, h3, h4⟩ := h
    obtain ⟨g, f⟩ := r
    simp only [implementation_nominalAxis, Id.run] at *
    cases isNominal <;> cases hasLimit <;> cases isY <;> simp_all <;> rfl

— elaborates against the frozen file (exit 0). The four clauses therefore pin the
result uniquely on all 2×2×2 gate combinations and for every ``nticks``: (C1)
fixes ``gridHidden`` outright, and (C2)/(C3)/(C4) between them fix ``fixedLimit``
in each of the three behavioral cases, leaving no residual freedom. Consequently
NO implementation that disagrees with the frozen one anywhere can satisfy this
spec, so SPEC-TOO-WEAK is not merely unobserved by this battery — it is
unreachable. The rivals remain the per-clause attribution (which clause catches
which error, and at which input); the uniqueness result is what makes their
coverage exhaustive rather than merely broad.

An independent audit re-ran that uniqueness proof (exit 0, confirmed) and then
probed the claim empirically rather than trusting it, with SEVEN new wrong impls
the battery did not contain, aimed at what the existing rivals leave unattacked:
a count-domain truncated far edge; the grid forced off when nominal OR
caller-pinned; the reversal applied on the horizontal axis instead of the
vertical; the pin skipped below two categories; a lower edge whose value depends
on the parity of the count; the pin omitted on the vertical axis; and a symmetric
"centered" extent. All seven are REJECTED (exit 1 each), consistent with the
uniqueness result. The first of them was strong enough to keep and is now
``reject-upper-edge-nat-truncated``; the other six added no input point the
battery does not already refute at, so they are recorded here rather than shipped
as cases. No new wrong impl verified, so no spec hole was found.

Correct-reshape probes (the SPEC-TOO-STRONG direction) were run the same way, with
five new faithful impls beyond the four positives below: the record built from an
``isNominal && !hasLimit`` conjunction; an eight-arm ``match`` on all three
booleans; the pair produced through ``Option.map`` with the swap inside the
mapping function; a structural recursion on the tick count; and the far edge
computed as ``lo + nticks`` instead of ``nticks - 1/2``. All five VERIFY (exit 0
each) — the last two needing their own proof body, supplied by the same
``push_cast``/``ring`` shape as ``pos-halved-integer-edges``. So the spec is not
over-fit to the frozen impl's branch structure, its arithmetic normal form, its
recursion scheme, or its use of a mutable local.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
impl's exact elaboration — so a rejection ALONE attributes nothing to the spec.
Each ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Every witness was checked with the same
three checks the gate applies: it ELABORATES against its rival, it FAILS against
the frozen solution, and that gold-side failure is a real refutation rather than a
stuck reduction (see the tactic note below — this last check is the one that
matters on this carrier). No witness binds a hypothesis (every input is a literal),
so no witness carries a consistency obligation.

A tactic note, since it is carrier-specific and it is where a first attempt at
this battery went wrong. The extent is modeled as ``ℚ`` (mapping.md: order-relevant
exact half-integers are never modeled as kernel ``Float``), and the ``Decidable``
instance for ``ℚ`` equality does not reduce through the division in the ``-1/2``
literal. MEASURED on this bundle, at three levels of the claim:

  * ``decide`` on the spec Prop itself cannot even be attempted — the negation of
    ``problem_spec_nominalAxis`` has no ``Decidable`` instance to synthesize
    (``failed to synthesize Decidable ¬problem_spec_nominalAxis ...``), since the
    predicate is a conjunction of implications over ``Prop``.
  * ``decide`` on a bare ℚ disequality (``(-1/2 : ℚ) ≠ 0``) fails too, and by the
    OTHER mechanism: ``instDecidableNot did not reduce to `isTrue` or `isFalse```
    — the division stalls the instance rather than computing.
  * ``decide +kernel`` DOES close ℚ claims here (``(-1/2 : ℚ) ≠ 0`` elaborates),
    so the blanket "not usable" is wrong. It is nevertheless unusable AS A
    WITNESS TACTIC, and for a sharper reason: measured on the extent projection,
    ``decide +kernel`` closes claims that are TRUE of the frozen impl (both
    ``... .fixedLimit = some (-1/2, 3 - 1/2)`` and the true negation
    ``... ≠ some (0, 3 - 1/2)`` elaborate, exit 0) but fails on the FALSE one
    (``... ≠ some (-1/2, 3 - 1/2)``) with ``instDecidableNot did not reduce to
    `isTrue` or `isFalse```. So a ``decide +kernel`` witness would make the rival
    build SUCCEED and the gold build FAIL — clearing both halves of the
    discrimination check — while gold's failure is a stuck reduction rather than
    a refutation. The gate screens exactly that message and reports
    ``witness-undecided``.

Each witness therefore avoids deciding a ``ℚ`` proposition at all. It selects the
single spec CLAUSE the rival violates, restates the clause instance as a defeq
type ASCRIPTION naming the value the rival actually produces, and then refutes:

  * a wrong extent PAIR is split by ``Option.some.injEq`` / ``Prod.mk.injEq`` and
    closed by ``norm_num`` on the offending component;
  * an extent pinned where the clause demands it be unset is closed by
    ``Option.noConfusion`` (``some _ = none``) — pure constructor discrimination,
    no arithmetic at all;
  * a wrong grid decision is closed by ``Bool.noConfusion``.

A note on the ``simp only [implementation_nominalAxis, Id.run] at h`` step, since
an earlier revision of this docstring described it wrongly and the correction is
the whole reason the mechanism is trustworthy. That step does NOT in fact reduce
``h``: MEASURED by replacing the closing step with a deliberate type error
(``exact (h : Nat)``), Lean prints ``h``'s real type on BOTH sides and it is still
the un-normalized ``(if True then ... else ...).fixedLimit = ...`` monadic term,
not a value. So the step is a no-op on this carrier (on one case Lean even reports
``This simp argument is unused``) and NOTHING here rests on it. What carries the
refutation is the next line: the ascription is checked by DEFEQ, which unfolds the
whole ``Id.run do`` skeleton at literal arguments and therefore succeeds exactly
when the named value is the one that impl computes at that input. That is a
whole-term comparison, so it is if anything stronger than a normalizing rewrite —
but it means the witness must name the value in the rival's own term shape.

The ascription step was separately CONTROLLED for value-sensitivity, in BOTH
directions, because it is the step that carries the gold-side signal. Every
witness here fails on gold with ``error: Type mismatch``, and the control
establishes that this is the value differing rather than the mechanism being
blind to shape. Take the same pipeline but ascribe the value GOLD actually
produces (``some ((-1/2 : ℚ), (3 : ℚ) - 1/2)``): against GOLD the ascription now
ELABORATES and the build gets all the way to the final step, failing there
instead with ``unsolved goals ... h2 : True ⊢ False`` — i.e. the mechanism
accepted gold's shape and then correctly declined to refute a true claim. Against
a RIVAL that same gold-valued ascription fails at the ascription with ``Type
mismatch`` (the rival's reduced term shows ``some (0, ↑3 - 1/2)``). The
``none``-ascription pipeline was controlled the same way: ascribing
``(none : Option (ℚ × ℚ)) = none`` against gold elaborates and then fails at
``Option.noConfusion h2`` with ``Option.noConfusionType ?m.29 none none``. So the
ascription tracks the VALUE, and a gold-side ascription failure means gold's
extent differs from the rival's — which is exactly the refutation claimed.

A second, independent control on the same gold-side signal, run per case: FLIP
each witness's claim (drop the ``¬``, so it asserts the spec HOLDS at that very
input) and prove it with the frozen tactic body. All nine flipped claims
ELABORATE against gold (exit 0) and FAIL against their own rival (exit 1) — the
exact inverse of the witnesses. So gold's exit code tracks WHAT IS CLAIMED and
not merely which file is being built, which is what rules out the hollow-pass
shape where a witness asserting gold is CORRECT would also have been recorded as
a rejection.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle contracts TWO functions over five scalar inputs
(``finalize_axis_range`` returning a ``Tuple[float,float]``, and
``finalize_axis_grid`` returning a ``bool``) and consumes an opaque
contract-only tick-count oracle. This lean carrier models the SAME two decisions
as one total function returning a two-field record, and takes the tick count as a
plain ``Nat`` INPUT rather than an axiomatized callee. The correspondence:

  * nagini ``rival-lo-zero``            ↦ ``reject-lower-edge-zero``
  * nagini ``rival-no-invert``          ↦ ``reject-no-vertical-reverse``
  * nagini ``rival-wrong-upper``        ↦ ``reject-upper-edge-off-by-one``
  * nagini ``rival-hardcode-one``       ↦ ``reject-upper-edge-constant``
  * nagini ``rival-cat-over-explicit``  ↦ ``reject-pin-over-explicit``
  * nagini ``rival-cat-everywhere``     ↦ ``reject-pin-without-nominal-gate``
  * nagini ``rival-grid-passthrough``   ↦ ``reject-grid-never-hidden``
    (as does nagini ``rival-grid-always-on``: the two collapse here — see below)
  * nagini ``rival-grid-force-off``     ↦ ``reject-grid-off-everywhere``
  * nagini ``rival-grid-inverted``      ↦ ``reject-grid-inverted``
  * nagini ``pos-range-reorder`` / ``pos-grid-direct`` / ``cheap-grounded-range``
    ↦ ``pos-pair-swap-form`` / ``pos-functional-match`` / ``pos-limit-gate-first``
    / ``pos-halved-integer-edges`` — structurally different CORRECT impls, each
    re-proven for its own shape.
  * nagini ``admiss-fshaped-input``     ↦ ``admiss-f2p-shaped-inputs``

WHAT WAS DROPPED, AND WHY
-------------------------
  * nagini ``rival-grid-always-on`` (force the grid ON everywhere) and nagini
    ``rival-grid-passthrough`` (keep the incoming visibility) COLLAPSE into each
    other on this carrier, and the collapse is demonstrated rather than asserted.
    The nagini surface takes a ``pre_visible`` input and its grid clause is
    ``Implies(not is_categorical, Result() == pre_visible)``, so there "force ON"
    and "pass through" are distinguishable. This carrier has no such binder — the
    modeled decision is whether finalization FORCES the grid off, a decision that
    is simply absent on an ordinary axis — so both nagini shapes denote the single
    impl ``gridHidden ≡ false``, and that impl is ``reject-grid-never-hidden``.
    Verified as a definitional identity: with ``gridHidden := true`` deleted,
    ``(implementation_nominalAxis isY isNominal hasLimit nticks).gridHidden
    = false`` closes for ALL binders by ``cases ... <;> rfl`` (exit 0). Keeping a
    second copy would be two spellings of one point, not added coverage.
  * nagini ``rival-grid-force-off`` (force the grid off on EVERY axis) is NOT
    dropped: it is carried as ``reject-grid-off-everywhere`` below. An earlier
    revision of this battery dropped it, reasoning that its faithful real edit
    leaves all 96 FAIL_TO_PASS + PASS_TO_PASS tests passing (no test in the suite
    observes grid visibility on a non-categorical axis) and so its ``refinement``
    could not claim a resolve break. That premise is correct and the conclusion
    did not follow: a reject case needs its rival to be WRONG against the SPEC,
    which this one is — (C1) is a biconditional, so forcing the grid off on an
    ordinary axis violates it — and the case now says exactly that, with a
    ``refinement`` that records the measured no-break rather than claiming one.
    It is the only rival wrong in (C1)'s ordinary-axis direction ALONE, which
    makes it a strict near-miss of ``reject-grid-inverted`` (wrong in both).
  * nagini's frame / permission-mutation reasoning — the nagini defended-surface
    note already records this class as N/A there (all inputs are read-only
    scalars). It is doubly vacuous here: Lean is referentially transparent, so
    there is no mutable reference to overwrite and no fractional permission to
    weaken. No substitute was fabricated.
  * nagini's divergence / non-termination lane — the nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` case, and on lean the class is genuinely vacuous
    rather than a spec hole. This bundle sets no ``loom.semantics.termination``
    option at all (it is a plain Lean file, not a loom one), so the carrier is
    TOTAL by construction: the verifier discharges termination as part of
    accepting the ``def`` at all, and there is no "partial" setting under which a
    diverging impl could satisfy the clauses vacuously. Vacuity here is
    DEMONSTRATED rather than asserted — four diverging shapes were built and each
    is rejected before the spec is ever consulted, which is why none of them is
    shippable as a reject case (a reject case needs a witness that refutes the
    rival against the SPEC, and these files do not elaborate far enough to state
    one):
      - unmeasured self-recursion (``... nticks + 1``) => ``fail to show
        termination for implementation_nominalAxis``;
      - a ``while true do`` inside the frozen ``Id.run do`` skeleton => the
        obligation fails on an unreduced ``forIn Lean.Loop.mk`` term, i.e. a
        TACTIC failure, not a spec refutation;
      - ``partial def`` => ``failed to compile 'partial' definition ...  could
        not prove that the type ... is nonempty`` (``AxisLayout`` derives only
        ``DecidableEq``);
      - ``partial def`` plus an inline ``instance : Nonempty AxisLayout`` (which
        ``variant_scope`` does permit, since it is not a theorem/lemma) => the
        definition compiles, but ``partial`` makes the body OPAQUE, so
        ``unfold`` fails (``Tactic `unfold` failed to unfold
        `implementation_nominalAxis```) and — the point for this lane — a witness
        cannot state a refutation either: the same ``Bool.noConfusion`` witness
        that discriminates every other rival fails on it with
        ``Bool.noConfusionType ?m.14 (implementation_nominalAxis false true false
        0).gridHidden true``, an unreduced projection rather than a value. So the
        class cannot be shipped in EITHER direction: the rival never verifies, and
        no witness attributes its rejection to the spec.
    (Contrast velvet under ``loom.semantics.termination "partial"``, where a
    non-terminating impl satisfies every clause vacuously and the spec ADMITS it —
    the corpus-wide termination-semantics finding. That disposition does not apply to this backend.)
  * nagini's ungrounded-oracle-echo slot — N/A for the same reason nagini records
    it as N/A, and more so here: the tick count is a transparent ``Nat`` input, not
    an opaque oracle, so there is no answer-key term to echo and nothing needs
    conditioning on the carrier.
  * nagini ``AXIOM_TESTS`` — dropped by contract; the axiom lane is G-AX's job and
    this gate ignores them. This bundle declares no ``opaque``/``axiom`` callee
    (mapping.md: the decision is a closed expression over its four inputs), so
    G-AX skips here in any case.

No soundness positive was dropped: all four alternative correct impls elaborate
with the ``theorem correct_nominalAxis`` statement byte-identical, no helper
lemma, no new declaration, and no assumption token.
"""
from pathlib import Path

INSTANCE = "mwaskom__seaborn-3069"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique in Solution.lean; asserted at import) -------

# The whole frozen impl body. Lies entirely inside impl-start / impl-end.
_IMPL_GOLD = """def implementation_nominalAxis
    (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let lo : ℚ := -1/2
      let hi : ℚ := (nticks : ℚ) - 1/2
      if isY then
        fixedLimit := some (hi, lo)
      else
        fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩"""

# The frozen proof BODY (everything after `:= by`). Lies entirely inside
# proof-start / proof-end; the theorem STATEMENT above it is never touched.
_PROOF_GOLD = """  intro isY isNominal hasLimit nticks
  unfold problem_spec_nominalAxis implementation_nominalAxis
  cases isNominal <;> cases hasLimit <;> cases isY <;>
    exact ⟨rfl, by intro h; simp_all, by intro h; simp_all, by intro h; simp_all⟩"""


def _impl(body):
    """Full variant with ONLY the impl-region body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


def _impl_proof(body, proof):
    """Full variant with the impl body AND the proof body replaced (a reshaped
    correct impl that needs a proof closing for its own shape). The
    `theorem correct_nominalAxis` STATEMENT is preserved byte-identically."""
    return _swap(_impl(body), _PROOF_GOLD, proof)


def _head(body):
    return ("def implementation_nominalAxis\n"
            "    (isY isNominal hasLimit : Bool) (nticks : Nat) : AxisLayout := "
            + body)


# ---- witness helpers --------------------------------------------------------
# Every witness states the refutation at ONE concrete input with all four
# arguments literal, and binds NOTHING — so no witness carries a consistency
# obligation. None of them decides a `ℚ` proposition: see the module docstring's
# tactic note for why `decide` / `decide +kernel` cannot be used on this carrier
# (and why `decide +kernel` would produce an information-free rejection). Each
# selects the clause the rival violates, normalizes the monadic wrapper with
# `simp only [.., Id.run]`, pins the reduced value by a defeq ascription, and then
# refutes by constructor discrimination or a single `norm_num`.

def _head_args(isY, isNominal, hasLimit, nticks):
    return f"{isY} {isNominal} {hasLimit} {nticks}"


def _wit_extent(isY, isNominal, hasLimit, nticks, got_lo, got_hi):
    """Refute (C2): the rival pins the WRONG ordered extent pair.

    `got_*` is the pair the rival produces; the pair the clause demands is
    derived from the same binders, so the two are compared component-wise.
    """
    args = _head_args(isY, isNominal, hasLimit, nticks)
    want = (f"(({nticks} : ℚ) - 1/2, -1/2)" if isY == "true"
            else f"(-1/2, ({nticks} : ℚ) - 1/2)")
    return (f"example : ¬ problem_spec_nominalAxis {args}\n"
            f"    (implementation_nominalAxis {args}) := by\n"
            f"  intro hs\n"
            f"  have h := hs.2.1 rfl rfl\n"
            f"  simp only [implementation_nominalAxis, Id.run] at h\n"
            f"  have h2 : some ({got_lo}, {got_hi}) = some {want} := h\n"
            f"  rw [Option.some.injEq, Prod.mk.injEq] at h2\n"
            f"  norm_num at h2\n")


def _wit_unset(isY, isNominal, hasLimit, nticks, clause, got_lo, got_hi):
    """Refute (C3) (`clause="3"`) or (C4) (`clause="4"`): the clause demands the
    extent be left unset and the rival pins it. Closed by constructor
    discrimination (`some _ = none`), with no arithmetic at all."""
    args = _head_args(isY, isNominal, hasLimit, nticks)
    sel = "hs.2.2.1 rfl" if clause == "3" else "hs.2.2.2 rfl"
    return (f"example : ¬ problem_spec_nominalAxis {args}\n"
            f"    (implementation_nominalAxis {args}) := by\n"
            f"  intro hs\n"
            f"  have h := {sel}\n"
            f"  simp only [implementation_nominalAxis, Id.run] at h\n"
            f"  have h2 : some ({got_lo}, {got_hi}) = (none : Option (ℚ × ℚ)) := h\n"
            f"  exact Option.noConfusion h2\n")


def _wit_grid(isY, isNominal, hasLimit, nticks):
    """Refute (C1): the rival's grid decision differs from the categorical flag."""
    args = _head_args(isY, isNominal, hasLimit, nticks)
    return (f"example : ¬ problem_spec_nominalAxis {args}\n"
            f"    (implementation_nominalAxis {args}) := by\n"
            f"  intro hs\n"
            f"  have h := hs.1\n"
            f"  simp only [implementation_nominalAxis, Id.run] at h\n"
            f"  exact Bool.noConfusion h\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify; if one cannot, the spec is over-fit to the frozen impl's
    # shape => SPEC-TOO-STRONG. Each keeps the theorem statement byte-identical
    # and adds no declaration, no helper lemma and no assumption token.
    # =====================================================================
    {
        "id": "pos-pair-swap-form",
        "kind": "soundness",
        "expect": "verify",
        # The ordered pair is built ONCE and reversed with `Prod.swap` on the
        # vertical axis, instead of assigning the two orderings in separate
        # branches. Same value at every input; a different data-flow shape.
        "module": _impl(_head("""Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let base : ℚ × ℚ := (-1/2, (nticks : ℚ) - 1/2)
      fixedLimit := some (if isY then base.swap else base)
  return ⟨gridHidden, fixedLimit⟩""")),
        "rationale": "a correct reshape that constructs the ordered extent pair once "
                     "and reverses it for the vertical case via `Prod.swap`, rather "
                     "than assigning the two orderings in separate branches. It "
                     "satisfies (C1)-(C4) at every input, so it MUST verify; if it "
                     "cannot, the spec is pinned to the frozen branch structure rather "
                     "than to the behavior => SPEC-TOO-STRONG. The frozen tactic body "
                     "still closes it (the case split reduces the swap), so no proof "
                     "authoring is needed.",
    },
    {
        "id": "pos-functional-match",
        "kind": "soundness",
        "expect": "verify",
        # No `Id.run do`, no `let mut`, no early return: a plain functional
        # `match` on the two gating booleans building the record directly. A
        # genuinely different executable shape with the same value everywhere.
        "module": _impl(_head("""
  match isNominal, hasLimit with
  | false, _ => { gridHidden := false, fixedLimit := none }
  | true, true => { gridHidden := true, fixedLimit := none }
  | true, false =>
      { gridHidden := true,
        fixedLimit := some (if isY then ((nticks : ℚ) - 1/2, -1/2)
                            else (-1/2, (nticks : ℚ) - 1/2)) }""")),
        "rationale": "a correct point-free reshape: a plain functional `match` on the "
                     "two gating booleans with no monadic wrapper and no mutable "
                     "local, enumerating the three behavioral cases directly. Must "
                     "verify (else SPEC-TOO-STRONG). This is the analogue of the "
                     "nagini conditional-expression positive control.",
    },
    {
        "id": "pos-limit-gate-first",
        "kind": "soundness",
        "expect": "verify",
        # The two gates are tested in the OPPOSITE order (caller-pinned first,
        # categorical second) and the grid decision is written as the gating
        # boolean itself rather than reached by an assignment. Same value
        # everywhere; the branch order and the grid data-flow both differ.
        "module": _impl(_head("""Id.run do
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if hasLimit then
    fixedLimit := none
  else if isNominal then
    if isY then
      fixedLimit := some ((nticks : ℚ) - 1/2, -1/2)
    else
      fixedLimit := some (-1/2, (nticks : ℚ) - 1/2)
  return ⟨isNominal, fixedLimit⟩""")),
        "rationale": "a correct reshape that tests the two gates in the opposite order "
                     "(caller-pinned extent first, categorical second) and returns the "
                     "grid decision as the gating boolean directly instead of reaching "
                     "it by assignment. Value-identical on all inputs, so it must "
                     "verify — this is the case that would catch a spec accidentally "
                     "over-fit to the frozen gate ORDER (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-halved-integer-edges",
        "kind": "soundness",
        "expect": "verify",
        # The two edges are written in an equivalent ARITHMETIC form: as halves of
        # integers (-1/2 and (2n-1)/2) rather than as a subtraction from the tick
        # count. Same rational values; a different computation. The frozen tactic
        # body no longer closes this, so the proof supplies the arithmetic
        # identity by `push_cast; ring` and then closes as before.
        "module": _impl_proof(_head("""Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let lo : ℚ := (-1 : ℤ) / 2
      let hi : ℚ := ((2 * (nticks : ℤ) - 1 : ℤ) : ℚ) / 2
      if isY then
        fixedLimit := some (hi, lo)
      else
        fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩"""),
            """  intro isY isNominal hasLimit nticks
  unfold problem_spec_nominalAxis implementation_nominalAxis
  have e : ((2 * (nticks : ℤ) - 1 : ℤ) : ℚ) / 2 = (nticks : ℚ) - 1/2 := by
    push_cast; ring
  cases isNominal <;> cases hasLimit <;> cases isY <;>
    exact ⟨rfl, by intro h; simp_all, by intro h; simp_all, by intro h; simp_all⟩"""),
        "rationale": "the edges are computed in an equivalent arithmetic form — halves "
                     "of integers rather than a subtraction from the tick count — so "
                     "the pinned pair is the same rational value by a different "
                     "computation. Must verify (else the spec pins a normal FORM of "
                     "the arithmetic rather than its value => SPEC-TOO-STRONG). The "
                     "proof supplies the arithmetic identity in-line (`push_cast; "
                     "ring`) and then closes exactly as the frozen script does; the "
                     "theorem statement is byte-identical and nothing is assumed.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at the ordinary inputs
    # the FAIL_TO_PASS scenarios exercise, not merely provable in the abstract.
    # The frozen theorem carries NO precondition hypothesis (the modeled decision
    # is total on all four inputs), so nagini's precondition-admission probe has
    # no binder to attack here. The honest analogue discharges the spec predicate
    # at the three ground F2P-shaped inputs BY EVALUATION inside the proof
    # region, alongside the frozen obligation: a horizontal categorical axis with
    # three categories, the same on a vertical axis, and a categorical axis the
    # caller has already pinned. Nothing is assumed — no new declaration, the
    # theorem statement is byte-identical, and the ground instances are `have`s
    # inside the existing tactic body.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, """  have _fx : problem_spec_nominalAxis false true false 3
      (implementation_nominalAxis false true false 3) := by
    unfold problem_spec_nominalAxis implementation_nominalAxis
    exact ⟨rfl, by intro h1 h2; simp_all, by intro h; simp_all,
      by intro h; simp_all⟩
  have _fy : problem_spec_nominalAxis true true false 3
      (implementation_nominalAxis true true false 3) := by
    unfold problem_spec_nominalAxis implementation_nominalAxis
    exact ⟨rfl, by intro h1 h2; simp_all, by intro h; simp_all,
      by intro h; simp_all⟩
  have _fl : problem_spec_nominalAxis false true true 3
      (implementation_nominalAxis false true true 3) := by
    unfold problem_spec_nominalAxis implementation_nominalAxis
    exact ⟨rfl, by intro h1 h2; simp_all, by intro h; simp_all,
      by intro h; simp_all⟩
""" + _PROOF_GOLD),
        "rationale": "the decision obligation is discharged at "
                     "the three ground inputs matching the FAIL_TO_PASS scenarios (a "
                     "three-category horizontal axis, the same vertical, and a "
                     "three-category axis whose extent the caller already pinned), and "
                     "then the frozen obligation is closed verbatim. Verifies (else "
                     "the modeled behavior is unsatisfiable at exactly the ordinary "
                     "inputs the tests exercise — the analogue of PRECOND-TOO-STRONG "
                     "on a total function with no precondition binder).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) a `refinement` recording the
    # MEASURED outcome of running its faithful real edit against the full
    # FAIL_TO_PASS + PASS_TO_PASS set in the instance image, so a verifying rival
    # is a true verify-does-not-imply-resolve break and not an artifact, and (b) a
    # `witness` refuting it at one concrete input, checked to hold of the rival
    # and to FAIL on the frozen solution.
    # =====================================================================
    {
        "id": "reject-lower-edge-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # (C2), lower edge: pin the extent from 0 rather than half a unit below
        # the first category position.
        "module": _impl(_IMPL_GOLD.replace("let lo : ℚ := -1/2", "let lo : ℚ := 0")),
        "refinement": "its faithful real edit starts the pinned extent at 0 instead of "
                      "half a unit below the first category position. MEASURED in the "
                      "instance image over the full 96-test FAIL_TO_PASS + "
                      "PASS_TO_PASS set: 2 failed, 94 passed — both categorical-axis "
                      "FAIL_TO_PASS tests fail, because each asserts the finalized "
                      "extent equals the exact half-unit-padded pair. It does NOT "
                      "resolve.",
        "rationale": "violates (C2): with a categorical axis and no caller limit, the "
                      "pinned pair must have lower edge exactly -1/2, and this rival "
                      "reports 0. Refuted at a horizontal categorical axis with three "
                      "categories and no caller limit. If it verifies => SPEC-TOO-WEAK.",
        "witness": _wit_extent("false", "true", "false", "3",
                               "(0 : ℚ)", "(3 : ℚ) - 1/2"),
    },
    {
        "id": "reject-no-vertical-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        # (C2), orientation: never reverse the pair, so a vertical axis gets the
        # increasing ordering instead of the reversed one.
        "module": _impl(_head("""Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let lo : ℚ := -1/2
      let hi : ℚ := (nticks : ℚ) - 1/2
      fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩""")),
        "refinement": "its faithful real edit omits the reversal on a vertical axis, so "
                      "the categories read bottom-to-top instead of top-to-bottom. "
                      "MEASURED over the full 96-test set: 1 failed, 95 passed — the "
                      "vertical-axis FAIL_TO_PASS test fails, since it asserts the "
                      "reversed ordered pair. It does NOT resolve. (This rival is a "
                      "NEAR-MISS: it agrees with the frozen behavior on every "
                      "horizontal input, which is why its witness is stated on the "
                      "vertical side, the only sub-domain where it is wrong.)",
        "rationale": "violates (C2) on the vertical sub-domain: equality of ℚ × ℚ is "
                      "order-sensitive, so the pair must be reversed when isY holds. "
                      "Refuted at a VERTICAL categorical axis with three categories — "
                      "the input that distinguishes it from the frozen solution, which "
                      "it matches everywhere else. If it verifies => SPEC-TOO-WEAK.",
        "witness": _wit_extent("true", "true", "false", "3",
                               "(-1/2 : ℚ)", "(3 : ℚ) - 1/2"),
    },
    {
        "id": "reject-upper-edge-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # (C2), upper edge: overshoot by a full unit — half a unit ABOVE the tick
        # count rather than below it, widening the extent by one slot.
        "module": _impl(_IMPL_GOLD.replace(
            "let hi : ℚ := (nticks : ℚ) - 1/2",
            "let hi : ℚ := (nticks : ℚ) + 1/2")),
        "refinement": "its faithful real edit puts the far edge half a unit ABOVE the "
                      "tick count instead of below it, widening the extent by exactly "
                      "one slot. MEASURED over the full 96-test set: 2 failed, 94 "
                      "passed — both categorical FAIL_TO_PASS tests assert the exact "
                      "pair and see the widened one. It does NOT resolve.",
        "rationale": "violates (C2): the far edge must be the tick count MINUS a half. "
                      "Refuted at a VERTICAL categorical axis with a SINGLE category — "
                      "a boundary tick count, and on the reversed side of the pair, so "
                      "the witness probes the far edge in its reversed position. If it "
                      "verifies => SPEC-TOO-WEAK.",
        "witness": _wit_extent("true", "true", "false", "1",
                               "((1 : ℚ) + 1/2)", "(-1/2 : ℚ)"),
    },
    {
        "id": "reject-upper-edge-nat-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        # (C2), upper edge, ARITHMETIC CARRIER: compute the far edge as
        # `(nticks - 1) + 1/2` with the subtraction done in `Nat` rather than in
        # ℚ. Over the rationals those two expressions are equal, so this rival
        # agrees with the frozen behavior at every tick count EXCEPT the one where
        # `Nat` subtraction saturates instead of going negative — the strictest
        # near-miss in this battery, and the case that proves the spec is stated
        # over ℚ rather than over a truncating carrier.
        "module": _impl(_head("""Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    if !hasLimit then
      let lo : ℚ := -1/2
      let hi : ℚ := ((nticks - 1 : Nat) : ℚ) + 1/2
      if isY then
        fixedLimit := some (hi, lo)
      else
        fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩""")),
        "refinement": "its faithful real edit computes the far edge by stepping back "
                      "one category and adding a half, with that step-back taken on the "
                      "integer tick COUNT before the coordinate is formed. On every "
                      "count the suite exercises the two agree, so MEASURED over the "
                      "full 96-test FAIL_TO_PASS + PASS_TO_PASS set: 0 failed, 96 "
                      "passed — it DOES resolve, and that is recorded here rather than "
                      "hidden. It is nevertheless WRONG against (C2), at the one count "
                      "where a count-domain step-back cannot go below its floor and "
                      "saturates, and no test in the suite plots an empty category set. "
                      "This case is therefore the same shape as "
                      "reject-grid-off-everywhere: a spec hole invisible to the suite.",
        "rationale": "violates (C2) at nticks = 0 ONLY: the clause demands the far edge "
                      "be (nticks : ℚ) - 1/2, which is -1/2 there, and this rival "
                      "reports +1/2 because the step-back is taken in the tick-count "
                      "domain, where it saturates at the floor instead of going below "
                      "it. Refuted at a horizontal categorical axis with ZERO ticks — "
                      "the degenerate boundary of the nticks binder, and the ONLY input "
                      "at which this rival and the frozen solution differ, which is why "
                      "no other case in this battery catches it: the eight other "
                      "extent/grid rivals are all wrong on a whole sub-domain. It also "
                      "demonstrates the mapping.md ℚ choice is load-bearing rather than "
                      "cosmetic (an ℕ-carrier for the count-minus-one would admit this "
                      "impl). If it verifies => SPEC-TOO-WEAK.",
        "witness": _wit_extent("false", "true", "false", "0",
                               "(-1/2 : ℚ)", "(((0 - 1 : Nat) : ℚ) + 1/2)"),
    },
    {
        "id": "reject-upper-edge-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # (C2), upper edge: ignore the observed tick count entirely and hardcode
        # the far edge to its single-category value. Correct only when nticks = 1.
        "module": _impl(_IMPL_GOLD.replace(
            "let hi : ℚ := (nticks : ℚ) - 1/2", "let hi : ℚ := 1/2")),
        "refinement": "its faithful real edit hardcodes the far edge to the value it "
                      "would take for a single category, ignoring the observed tick "
                      "count. MEASURED over the full 96-test set: 2 failed, 94 passed "
                      "— both categorical FAIL_TO_PASS tests use three categories and "
                      "assert an extent scaled to that count. It does NOT resolve.",
        "rationale": "violates (C2): the far edge must be TIED to the nticks binder, "
                      "not constant. This is the case that proves the spec binds the "
                      "extent to the observed count rather than to a literal — refuted "
                      "at FOUR categories, where the constant is furthest off, and on "
                      "a horizontal axis. Distinct from reject-upper-edge-off-by-one, "
                      "which keeps the dependence on nticks and only shifts it: this "
                      "rival drops the dependence, so it is refuted at a different "
                      "tick count. If it verifies => SPEC-TOO-WEAK.",
        "witness": _wit_extent("false", "true", "false", "4",
                               "(-1/2 : ℚ)", "(1/2 : ℚ)"),
    },
    {
        "id": "reject-pin-over-explicit",
        "kind": "uniqueness",
        "expect": "reject",
        # (C4): pin the categorical extent even when the caller already pinned an
        # explicit one, overriding it.
        "module": _impl(_head("""Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
    let lo : ℚ := -1/2
    let hi : ℚ := (nticks : ℚ) - 1/2
    if isY then
      fixedLimit := some (hi, lo)
    else
      fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩""")),
        "refinement": "its faithful real edit drops the guard deferring to a "
                      "caller-supplied extent, so the categorical extent overrides an "
                      "explicit one. MEASURED over the full 96-test set: 3 failed, 93 "
                      "passed — both categorical FAIL_TO_PASS tests (each of which "
                      "asserts a caller-pinned extent is honored verbatim) AND one "
                      "PASS_TO_PASS test covering caller-supplied extents. It does NOT "
                      "resolve, and it regresses previously-passing behavior.",
        "rationale": "violates (C4): when the caller pinned the extent, finalization "
                      "must leave it unset. Refuted at a horizontal categorical axis "
                      "with three categories WHERE THE CALLER HAS PINNED a limit — the "
                      "only witness in this battery holding hasLimit true together "
                      "with isNominal true, which is exactly the sub-domain (C4) "
                      "governs. If it verifies => SPEC-TOO-WEAK.",
        "witness": _wit_unset("false", "true", "true", "3", "4",
                              "(-1/2 : ℚ)", "(3 : ℚ) - 1/2"),
    },
    {
        "id": "reject-pin-without-nominal-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # (C3): drop the categorical gate on the extent, pinning EVERY axis the
        # caller has not pinned — categorical or not. This is the identity-clause
        # attack the nagini sibling records as the original auditor break.
        "module": _impl(_head("""Id.run do
  let mut gridHidden := false
  let mut fixedLimit : Option (ℚ × ℚ) := none
  if isNominal then
    gridHidden := true
  if !hasLimit then
    let lo : ℚ := -1/2
    let hi : ℚ := (nticks : ℚ) - 1/2
    if isY then
      fixedLimit := some (hi, lo)
    else
      fixedLimit := some (lo, hi)
  return ⟨gridHidden, fixedLimit⟩""")),
        "refinement": "its faithful real edit applies the pinned extent to EVERY axis "
                      "without a caller-supplied limit, categorical or not. MEASURED "
                      "over the full 96-test set: 2 failed, 94 passed — and notably "
                      "the two failures are PASS_TO_PASS tests covering "
                      "logarithmically-scaled continuous axes, which get their extents "
                      "clobbered. It does NOT resolve; it breaks behavior that passed "
                      "BEFORE the change. This reproduces the break the nagini sibling "
                      "records as the original auditor attack, which is precisely why "
                      "the identity clause is not optional.",
        "rationale": "violates (C3): a non-categorical axis must be left unpinned. "
                      "Refuted at an ORDINARY (non-categorical) horizontal axis with "
                      "two ticks and no caller limit — the only witness in this "
                      "battery probing (C3), and one of only two holding isNominal "
                      "false. If it verifies => SPEC-TOO-WEAK, and it is the exact "
                      "hole a spec leaving the ordinary-axis sub-domain unconstrained "
                      "would leave.",
        "witness": _wit_unset("false", "false", "false", "2", "3",
                              "(-1/2 : ℚ)", "(2 : ℚ) - 1/2"),
    },
    {
        "id": "reject-grid-never-hidden",
        "kind": "uniqueness",
        "expect": "reject",
        # (C1), forward direction: never force the grid off, so a categorical
        # axis keeps whatever the active style draws. This is the pre-change
        # behavior of the grid decision.
        "module": _impl(_IMPL_GOLD.replace("    gridHidden := true\n", "")),
        "refinement": "its faithful real edit never forces the grid off, so a "
                      "categorical axis keeps whatever the active style draws — this "
                      "is the pre-change behavior of that decision. MEASURED over the "
                      "full 96-test set: 2 failed, 94 passed — both categorical "
                      "FAIL_TO_PASS tests assert no grid line on the categorical axis "
                      "is visible, and the default style draws one. It does NOT "
                      "resolve.",
        "rationale": "violates (C1) in the forward direction: a categorical axis must "
                      "report the grid forced off. Refuted at a horizontal categorical "
                      "axis with ZERO ticks — a degenerate boundary for the nticks "
                      "binder, which the grid decision is independent of, confirming "
                      "(C1) is pinned across the whole extent sub-domain. If it "
                      "verifies => SPEC-TOO-WEAK.",
        "witness": _wit_grid("false", "true", "false", "0"),
    },
    {
        "id": "reject-grid-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # (C1), BOTH directions: report the grid forced off on ordinary axes and
        # left alone on categorical ones — exactly inverted.
        "module": _impl(
            _IMPL_GOLD.replace("  let mut gridHidden := false",
                               "  let mut gridHidden := !isNominal")
                      .replace("    gridHidden := true\n", "")),
        "refinement": "its faithful real edit inverts the grid decision: the grid is "
                      "forced off on ordinary axes and left alone on categorical ones. "
                      "MEASURED over the full 96-test set: 2 failed, 94 passed — both "
                      "categorical FAIL_TO_PASS tests fail, since the categorical axis "
                      "keeps the grid the active style draws. It does NOT resolve.",
        "rationale": "violates (C1) in BOTH directions, since (C1) is a biconditional "
                      "on isNominal. Witnessed on the ORDINARY-axis direction (a "
                      "vertical non-categorical axis with five ticks, no caller limit) "
                      "— that direction is otherwise unattacked in this battery, and "
                      "it is the one an all-axes-grid-off rival would have covered had "
                      "that rival's faithful patch not resolved (see WHAT WAS DROPPED). "
                      "Its measured F2P failure is on the categorical direction; both "
                      "directions are genuinely wrong, so the two are consistent. If "
                      "it verifies => SPEC-TOO-WEAK.",
        "witness": _wit_grid("true", "false", "false", "5"),
    },
    {
        "id": "reject-grid-off-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        # (C1), ordinary-axis direction ALONE: force the grid off on EVERY axis
        # rather than only on a categorical one. Agrees with the frozen decision
        # on every categorical input and on both extent clauses; wrong only where
        # the axis is not categorical. The strict near-miss of
        # reject-grid-inverted, which is wrong in both directions of (C1).
        "module": _impl(_IMPL_GOLD.replace(
            "  let mut gridHidden := false", "  let mut gridHidden := true")),
        "refinement": "its faithful real edit drops the categorical gate on the "
                      "grid-off call, so an ordinary axis whose active style draws "
                      "gridlines loses them. MEASURED in the instance image over the "
                      "full 96-test FAIL_TO_PASS + PASS_TO_PASS set: 0 failed, 96 "
                      "passed — it DOES resolve the suite. That is recorded here "
                      "rather than hidden, and it is why this case makes no "
                      "resolve-break claim: no test in the suite observes grid "
                      "visibility on a non-categorical axis, so the suite cannot see "
                      "this regression. The case is still load-bearing, because a "
                      "reject case's job is to show the SPEC rejects a WRONG impl, "
                      "and this impl is wrong against (C1) independently of what the "
                      "suite happens to observe. If it verifies => SPEC-TOO-WEAK, and "
                      "the hole would be invisible to the test suite — the worst kind.",
        "rationale": "violates (C1) in the ordinary-axis direction: (C1) is a "
                      "biconditional on isNominal, so an axis that is NOT categorical "
                      "must report the grid NOT forced off. Refuted at an ORDINARY "
                      "horizontal axis with six ticks that the caller HAS pinned — an "
                      "input point no other case in this battery uses, and the only "
                      "witness holding isNominal false together with hasLimit true. "
                      "Distinct from reject-grid-inverted: that rival is wrong in BOTH "
                      "directions of (C1), so a spec that had lost the ordinary-axis "
                      "direction would still reject it on the categorical one. This "
                      "rival agrees with the frozen decision everywhere EXCEPT that "
                      "direction, so it is the case that isolates it.",
        "witness": _wit_grid("false", "false", "true", "6"),
    },
]
