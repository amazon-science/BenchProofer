"""properties.py — G-PBT falsification battery for mwaskom__seaborn-3069 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches ONLY text inside ``-- impl-start`` /
``-- impl-end``, or the elided ``prove_correct`` tactic body, both regions the
consumer spec view elides — so ``markers.same_spec`` holds by construction and
the ``prove_correct finalizeAxis`` header survives. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method decides, for a single axis of a finished
figure, the view limits to install and whether gridlines remain visible:

  finalizeAxis (isCategorical hasUserLimit isY : Bool) (nticks : Nat)
               (userLo userHi autoLo autoHi : Rat) (gridWasOn : Bool)
    return (out : AxisFinal)     -- {lo hi : Rat, gridVisible : Bool}

with THREE top-level ``ensures`` clauses, each pinning one result field to a pure
decision function of the inputs:

  E1  out.gridVisible = decidedGrid   isCategorical gridWasOn
  E2  out.lo          = (decidedLimits …).1
  E3  out.hi          = (decidedLimits …).2

``decidedGrid`` is a two-arm choice (categorical ⇒ suppressed, otherwise the
active style's choice stands). ``decidedLimits`` is a three-way PRIORITY CASCADE
whose arms partition the input cube:

  L1  hasUserLimit                             → (userLo, userHi)
  L2  ¬hasUserLimit ∧ isCategorical ∧ ¬isY     → (-1/2, nticks - 1/2)
  L3  ¬hasUserLimit ∧ isCategorical ∧  isY     → (nticks - 1/2, -1/2)
  L4  ¬hasUserLimit ∧ ¬isCategorical           → (autoLo, autoHi)

So E2/E3 each carry four independently-attackable sub-domains, and the pair
(E2,E3) additionally pins WHICH COMPONENT goes where — the L2/L3 split is exactly
an ORDER claim about the same two edge values, and the L1/L4 arms are ORDER
claims about the two supplied pairs.

The IDENTITY arms L4 and the non-categorical arm of E1 are NOT decoration. They
say the decision leaves an ordinary axis exactly as it found it: its default
margin limits transported verbatim and its grid governed by the active style.
Nagini's sibling records that an earlier, weaker spec left that sub-domain
unconstrained and admitted a rival which applied the categorical treatment to
EVERY axis without pinned limits — a rival whose faithful counterpart clobbered
ordinary continuous axes and broke hidden regression tests. ``rival-cat-
everywhere`` and ``rival-grid-force-off`` below replay that attack against the
strengthened clauses and must be rejected.

CARRIER NOTES vs. the nagini sibling. Nagini contracts TWO functions
(``finalize_axis_range`` over five scalars, ``finalize_axis_grid`` over two) plus
a ``@Pure @ContractOnly`` ``slot_count()`` oracle. This bundle fuses both into
ONE method returning a record, and — the substantive difference — the tick count
is a plain ``Nat`` INPUT rather than an opaque contract-only callee. Two
consequences:

  * the sibling's ungrounded-oracle-echo slot is N/A here for a stronger reason
    than on nagini: there is no oracle at all (the ``axioms`` region is empty),
    so there is no answer key to echo. The sibling's honest-echo positive control
    has no counterpart and is replaced by three grounded positive controls.
  * the sibling's ``rival-hardcode-one`` (pin the edge to the one-tick constant,
    ignoring the count) ports and is STRONGER here: with ``nticks`` a transparent
    input, a single concrete tick count refutes it outright, where nagini needed
    the oracle's ``>= 1`` contract to argue the point.

The carrier is also WIDER in one place: nagini's range function takes the
caller's pinned pair but has no counterpart for the ordinary default-margin pair,
which this spec carries as ``autoLo``/``autoHi`` and pins in L4. Two rivals
(``rival-auto-pair-swapped``, ``rival-user-pair-swapped``) attack the ORDER of
those two pairs — a clause nagini could not state. That is carrier widening, not
fabrication: each attacks a real independent arm of the frozen cascade.

ADVERSARIAL READ of the sibling's classes on this carrier:

  * PARTIAL-DOMAIN / VALUE — the heart of the port. Every rival gets the carrier
    type right (returns an ``AxisFinal``) and is correct on most of the cascade
    while diverging on one arm. All ten of the sibling's uniqueness rivals
    port; one (``rival-hardcode-one``) ports onto a transparent input.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling's own defended-surface
    note records that all inputs are read-only by-value scalars and there is no
    mutable reference input, so even on nagini there was nothing to overwrite.
    This backend is referentially transparent a fortiori: every input is an
    immutable value, the method declares no ``mut`` parameter, there is no heap
    and no aliasing. No substitute probe is fabricated.
  * ADMISSIBILITY — LIVE and CARRIED (``admiss-f2p-decision``). An earlier
    revision of this file recorded the lane VACUOUS on the ground that the
    ``pre-conditions`` region is empty, so no input can be excluded. That
    reasoning is wrong, and an audit demonstrated it wrong with real builds. On a
    TOTAL domain the analogue of PRECOND-TOO-STRONG is not an over-narrow
    ``require`` — it is the OBLIGATION being unsatisfiable or degenerate at
    exactly an F2P-shaped input, which reads from the outside exactly like a spec
    every impl meets. A spec whose decision functions could not be evaluated to
    the values the failing tests demand would still admit every rival below (each
    rival is refuted by a DIFFERENCE from gold, which survives gold's own answer
    being nonsense), so nothing else in this battery covers the direction. The
    lane is therefore filled by discharging the frozen decision functions at the
    concrete F2P-shaped points, by evaluation, as an in-region ``assert`` placed
    BEFORE the frozen impl body, which is then kept verbatim so the method's own
    three ``ensures`` still discharge. The vacuous-precondition fact remains true
    and is still what makes the witnesses attributable: the derived tester is
    ``if decide pre then <postcondition check> else true``, so with a vacuous
    precondition a tester value of ``false`` is attributable to the
    POSTCONDITION alone — the witnesses could not discriminate at all if the
    precondition excluded their inputs.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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
  * AXIOM_TESTS — DROPPED. The sibling's three-probe axiom lane validates
    ``slot_count()``'s contract and its two deep-model references against the
    real callees. This bundle consumes no axiom and declares no deep-model
    reference (``meta.json``: ``axioms: []``, ``deep_model_references: []``,
    G-AX = skip), and this gate ignores ``AXIOM_TESTS`` regardless.

DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE SEMANTICS
against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

RETRACTED, RE-MEASURED (what stood in the two exhibit rows and the paragraph
below them). A superseded revision displayed a two-row build table

    diverging prefix, frozen body afterwards           -> verifies (exit 0)
    diverging prefix, returns the wrong (0, 0, true)   -> verifies (exit 0)

and read the second row as the finding: value clauses satisfied on an unreachable
exit, the returned record entirely unconstrained, a corpus-wide defect scoped by
an internal findings doc to a ``partial`` cohort against a ``total`` one, and a
spec hole rather than a vacuous class. All of it is withdrawn. Vacuous
satisfaction on an unreachable exit is the PARTIAL rule, and this bundle is not
partial: line 4 reads ``"total"``, as it does in all 500 velvet bundles, so the
census has no referent, and the doc it cited no longer exists. Re-built on THIS
bundle with the proof reduced to a bare ``loom_solve``, neither row reproduces: a
spliced loop with no measure is refused at elaboration (``Decreasing annotations
are required in total correctness semantics``), and the sharper shape that CARRIES
a measure the body never shrinks (``while q > 0 / invariant 0 <= q /
done_with q = 0 / decreasing q``, body ``q := q``) is REJECTED on the measure's
own goal, ``case «decreasing_1: q»`` with residual ``q < q`` unsolved. Nothing is
admitted on an unreachable exit, so the disposition recorded above stands: the
class is CLOSED BY THE SEMANTICS. It remains unshippable as a reject case only
because a witness must ELABORATE against the rival and the rival's module does not
compile at all, the descent obligation failing at the ``method`` ahead of any
appended tester. That is a witness-protocol limit, not a spec hole.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery: ``extract_program_for``
gives ``finalizeAxisExec``, the two ``prove_*_decidable_for`` directives supply
the decision procedures, and ``derive_tester_for`` assembles
``finalizeAxisTester args = if decide pre then (match exec args with
| DivM.res out => decide post | _ => false) else true``. Each witness asserts
``finalizeAxisTester <concrete args> = false`` at ONE fully concrete input — a
direct claim that the impl's own output violates the postcondition there. It is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict.

Plain ``decide`` STALLS on this carrier: the goal reduces through
``instDecidableEqRat`` and gets stuck on ``Rat.num`` (measured in this workspace
— the spec_guide's ``Rat`` caveat), failing against the RIVAL as well, so it
never clears the first half of the check. Every witness therefore closes with
``with_unfolding_all rfl``, which computes the tester by definitional unfolding
and yields a REAL verdict on both sides.

``decide +kernel`` was tried first and rejected, for a reason worth recording
because the exit codes alone look fine. It proves the rival's claim and fails
against the frozen solution — but its gold-side failure message is the
elaborator's fallback ``did not reduce to `isTrue` or `isFalse` ``, exactly the
string the gate screens for as a stuck reduction. That screen is right to exist:
an irreducible term fails for EVERY claim, so the exit code would attest to a
refutation never performed. Here the term is fully computable and the screen
fires on a misleading diagnostic — confirmed by building
``finalizeAxisTester <args> = true`` against the frozen solution at every
probe point, which elaborates (exit 0). ``with_unfolding_all rfl`` removes the
ambiguity: its gold-side failure is ``The left-hand side ... is not
definitionally equal to ... false``, a computed refutation with no stuck-reduction
string. Nothing is assumed — no ``sorry``/``admit``/``native_decide``.

Every witness binds NOTHING in its ``example`` head: the whole carrier is
transparent (``Bool``/``Nat``/``Rat`` literals, no ``opaque`` term anywhere), so
no witness conditions on a hypothesis and there is no joint-satisfiability
obligation to discharge. No ``sorry``/``admit``/``native_decide``/``axiom``
appears in any case.

Every reject witness was checked with THREE real builds, reproducing
the gate's own file surgery (``pbt_witness.witness_file``, so the
``prove_correct`` block is stripped exactly as the gate strips it):

  A. ``= false`` against the RIVAL            → exit 0  (the rival violates the
                                                 spec at this input)
  B. ``= false`` against the frozen solution  → exit 1, and the output carries
                                                 NO stuck-reduction message
  C. ``= true``  against the frozen solution  → exit 0

A and B are the two halves the gate requires. C is the reason B counts as
evidence: a stuck reduction fails for every claim regardless of truth, so if the
term were irreducible C would fail too. C passing at every point shows the
kernel really does compute this tester, so B's failure is a computed refutation.
Gold therefore demonstrably SATISFIES the postcondition at every input where a
rival is refuted. All fourteen cases pass A, B and C.
"""
from pathlib import Path

INSTANCE = "mwaskom__seaborn-3069"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the `prove_correct finalizeAxis` header
# intact.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method, verbatim, INCLUDING its comments (they
# live inside the elided impl region). Every variant replaces this single block,
# so no swap can stray outside the impl region.
_IMPL = """    -- Start from the limits the prior (user-limit / default-margin) logic
    -- resolves and the grid the active style chose.
    let mut lo : Rat := autoLo
    let mut hi : Rat := autoHi
    let mut grid : Bool := gridWasOn
    if hasUserLimit then
      lo := userLo
      hi := userHi
    else
      pure ()
    -- Categorical special-casing: suppress the grid, and (only when the
    -- consumer did not pin limits) draw to ±1/2 of the tick range, reversed on
    -- the vertical axis.
    if isCategorical then
      grid := false
      if hasUserLimit then
        pure ()
      else
        let edge : Rat := (nticks : Rat) - 1 / 2
        if isY then
          lo := edge
          hi := -1 / 2
        else
          lo := -1 / 2
          hi := edge
    else
      pure ()
    return { lo := lo, hi := hi, gridVisible := grid }"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof, verbatim. Rivals leave it as-is (the wrong body then leaves
# the postcondition goal unsolved and the module fails to build — the intended
# rejection); one positive control retunes it, which is permitted since the
# tactic body is elided from the spec view and the `prove_correct finalizeAxis`
# header is untouched.
_PROOF = ("prove_correct finalizeAxis by\n"
          "  loom_solve <;> simp_all [decidedGrid, decidedLimits]")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body, proof=None):
    """Full Solution.lean variant: impl body replaced, proof optionally retuned."""
    out = _swap(_BASE, _IMPL, body)
    if proof is not None:
        out = _swap(out, _PROOF, proof)
    return out


# ---- witness preamble. Names the extracted program and the two decision
# ---- procedures, then assembles the tester. All four directives live INSIDE the
# ---- witness, so they are appended to both the rival file and the gold file and
# ---- exist on both sides by construction (no name is referenced that only one
# ---- side declares).
_PRE = ("extract_program_for finalizeAxis\n"
        "prove_precondition_decidable_for finalizeAxis\n"
        "prove_postcondition_decidable_for finalizeAxis\n"
        "derive_tester_for finalizeAxis\n\n")


def _witness(args):
    """`finalizeAxisTester <args> = false` — the impl violates the spec here.

    Closed with `with_unfolding_all rfl`, and the choice of tactic is load-bearing
    for the SECOND half of the discrimination check, so it is worth recording why.

    Both `decide` and `decide +kernel` are unusable here, for the same underlying
    reason but with different symptoms (all measured in this workspace):

      * plain `decide` reduces through `instDecidableEqRat` and sticks on
        `Rat.num` — it fails on the RIVAL too, so the witness never even clears
        half 1.
      * `decide +kernel` DOES prove the rival's claim (half 1 passes) and does
        fail against the frozen solution (half 2 passes on exit code). But its
        gold-side failure message is the elaborator's fallback
        `... did not reduce to isTrue or isFalse`, which is precisely the string
        the gate screens for as a STUCK REDUCTION. The screen exists because a
        genuinely irreducible term makes `decide` fail for every claim, true or
        false, so the exit code would attest to a refutation nobody performed.

    Here that screen fires on a MISLEADING diagnostic rather than a real stall:
    the term is fully computable, and `decide +kernel` decides it in the true
    direction. Verified directly — against the frozen solution,
    `finalizeAxisTester <args> = true` elaborates (exit 0) at every probe
    point, so the kernel plainly does reduce this term. The gate cannot see that,
    and rightly refuses to distinguish "stuck" from "stuck-looking" by exit code.

    `with_unfolding_all rfl` avoids the ambiguity entirely: it computes the tester
    by definitional unfolding, so its gold-side failure is the honest
    `The left-hand side ... is not definitionally equal to the right-hand side
    false`, with the goal displayed. No stuck-reduction string, and a real verdict
    on both sides. It is not an escape hatch — it decides strictly more here than
    `decide` does, and nothing is assumed: no `sorry`/`admit`/`native_decide`.

    Each witness was checked with THREE real builds (see the accounting note at
    the foot of this file): `= false` against the rival (exit 0), `= false`
    against the frozen solution (exit 1, no stuck-reduction message), and
    `= true` against the frozen solution (exit 0). The third is what proves the
    second is a refutation and not a stall.
    """
    return _PRE + (f"example : finalizeAxisTester {args} = false := by\n"
                   "  with_unfolding_all rfl\n")


# ---------------------------------------------------------------------------
# Rival body builders. Each keeps the gold SHAPE and perturbs one arm, so the
# rival reads as a plausible near-miss rather than as obviously broken.
# ---------------------------------------------------------------------------

def _cascade(lo_cat="-1 / 2", hi_cat="edge", edge="(nticks : Rat) - 1 / 2",
             grid="if isCategorical then false else gridWasOn",
             limit_guard="isCategorical", inner_guard=True,
             init_lo="autoLo", init_hi="autoHi",
             user_lo="userLo", user_hi="userHi"):
    lines = [f"    let mut lo : Rat := {init_lo}",
             f"    let mut hi : Rat := {init_hi}",
             f"    let grid : Bool := {grid}",
             "    if hasUserLimit then",
             f"      lo := {user_lo}",
             f"      hi := {user_hi}",
             "    else",
             "      pure ()",
             f"    if {limit_guard} then"]
    ind = "      "
    if inner_guard:
        lines += ["      if hasUserLimit then", "        pure ()", "      else"]
        ind = "        "
    lines += [f"{ind}let edge : Rat := {edge}",
              f"{ind}if isY then",
              f"{ind}  lo := {hi_cat}",
              f"{ind}  hi := {lo_cat}",
              f"{ind}else",
              f"{ind}  lo := {lo_cat}",
              f"{ind}  hi := {hi_cat}",
              "    else",
              "      pure ()",
              "    return { lo := lo, hi := hi, gridVisible := grid }"]
    return "\n".join(lines)


def _grid_rival(expr):
    """Gold's limit cascade verbatim; only the grid decision is perturbed."""
    return _cascade(grid=expr)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness). Three structurally DIFFERENT but
    # value-identical implementations. Each must verify; a failure would mean the
    # postcondition is over-fit to one code shape => SPEC-TOO-STRONG. All three
    # were confirmed to build out-of-band.
    # =====================================================================
    {
        "id": "pos-expr-ladder",
        "kind": "soundness",
        "expect": "verify",
        # No mutable locals at all: the grid state and both candidate edge
        # positions are `let`-bound expressions, and the cascade is three
        # separate `return`s. The sibling's pos-grid-direct (a conditional
        # expression replacing assign-then-override) generalised to the whole
        # record.
        "module": _impl(
            "    let grid : Bool := if isCategorical then false else gridWasOn\n"
            "    let edge : Rat := (nticks : Rat) - 1 / 2\n"
            "    let catLo : Rat := if isY then edge else -1 / 2\n"
            "    let catHi : Rat := if isY then -1 / 2 else edge\n"
            "    if hasUserLimit then\n"
            "      return { lo := userLo, hi := userHi, gridVisible := grid }\n"
            "    else\n"
            "      if isCategorical then\n"
            "        return { lo := catLo, hi := catHi, gridVisible := grid }\n"
            "      else\n"
            "        return { lo := autoLo, hi := autoHi, gridVisible := grid }",
            # The reshape pushes the vertical-axis choice INSIDE each component,
            # so the residual goal is `(if isY then a else b) = (if isY then
            # (a, b') else (b, a')).1` — a conditional on both sides that the
            # frozen script does not case-split. One `split` closes it. The
            # obligation statement is untouched; only the elided tactic body
            # changes, which a variant may do.
            _PROOF + " <;> split <;> simp_all"),
        "rationale": "structurally different CORRECT impl: no mutable state at "
                     "all — the grid decision and both candidate edge positions "
                     "are let-bound expressions and the cascade is three "
                     "separate returns. Observationally identical to gold on "
                     "every input (the four cascade arms partition the same "
                     "cube), so E1/E2/E3 all still hold. Verifies with the "
                     "frozen obligation and a one-tactic-longer proof body "
                     "(the reshape moves the vertical choice inside each "
                     "component, so the residual needs one `split`). If it "
                     "FAILED to verify, the postcondition would be over-fit to "
                     "the mutable assign-then-override shape => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inverted-guards",
        "kind": "soundness",
        "expect": "verify",
        # Every guard is INVERTED and the initial values are the opposite corner
        # of the cascade: start from the pinned pair and a suppressed grid, then
        # walk outward. Ports the sibling's pos-range-reorder (branch order
        # changed, verbatim arm moved to the else).
        "module": _impl(
            "    let mut lo : Rat := userLo\n"
            "    let mut hi : Rat := userHi\n"
            "    let mut grid : Bool := false\n"
            "    if !isCategorical then\n"
            "      grid := gridWasOn\n"
            "    else\n"
            "      pure ()\n"
            "    if !hasUserLimit then\n"
            "      if isCategorical then\n"
            "        let edge : Rat := (nticks : Rat) - 1 / 2\n"
            "        if !isY then\n"
            "          lo := -1 / 2\n"
            "          hi := edge\n"
            "        else\n"
            "          lo := edge\n"
            "          hi := -1 / 2\n"
            "      else\n"
            "        lo := autoLo\n"
            "        hi := autoHi\n"
            "    else\n"
            "      pure ()\n"
            "    return { lo := lo, hi := hi, gridVisible := grid }"),
        "rationale": "structurally different CORRECT impl: EVERY guard is "
                     "inverted (¬isCategorical, ¬hasUserLimit, ¬isY) and the "
                     "locals are initialised from the opposite corner of the "
                     "cascade (the pinned pair and a suppressed grid), so the "
                     "identity arms are reached by assignment rather than by "
                     "fallthrough — the mirror image of gold's data flow, same "
                     "values everywhere. Verifies with the frozen proof "
                     "unchanged. Must verify, else the spec is over-fit to one "
                     "guard polarity => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reverse-pair",
        "kind": "soundness",
        "expect": "verify",
        # The categorical edges are named as an ASCENDING pair (first/last) and
        # the vertical axis reverses them at the point of assignment, instead of
        # gold's per-branch literal duplication. Also hoists the grid decision
        # above the limit cascade, so the two clauses are decided in the opposite
        # order from gold.
        "module": _impl(
            "    let mut lo : Rat := autoLo\n"
            "    let mut hi : Rat := autoHi\n"
            "    let mut grid : Bool := gridWasOn\n"
            "    if isCategorical then\n"
            "      grid := false\n"
            "    else\n"
            "      pure ()\n"
            "    if hasUserLimit then\n"
            "      lo := userLo\n"
            "      hi := userHi\n"
            "    else\n"
            "      if isCategorical then\n"
            "        let first : Rat := -1 / 2\n"
            "        let last : Rat := (nticks : Rat) - 1 / 2\n"
            "        if isY then\n"
            "          lo := last\n"
            "          hi := first\n"
            "        else\n"
            "          lo := first\n"
            "          hi := last\n"
            "      else\n"
            "        pure ()\n"
            "    return { lo := lo, hi := hi, gridVisible := grid }"),
        "rationale": "structurally different CORRECT impl: the two categorical "
                     "edge positions are named ONCE as an ascending "
                     "first/last pair and the vertical axis reverses them at "
                     "assignment (gold duplicates the literals per branch), and "
                     "the grid decision is hoisted ABOVE the limit cascade so "
                     "the two clauses are decided in the opposite order. "
                     "Value-identical; verifies with the frozen proof "
                     "unchanged. Must verify, else E1 and E2/E3 are coupled to "
                     "a decision ORDER the spec never states => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY. On a total carrier with an empty `pre-conditions` region
    # there is no `require` that could exclude an input, so the residual
    # PRECOND-TOO-STRONG risk takes its other form: the OBLIGATION being
    # UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input. That failure is
    # invisible to every other case here — a rival is rejected for DIFFERING from
    # gold, and a difference survives gold's own answer at the interesting point
    # being unreachable or collapsed — so this is the only case that looks at it.
    #
    # It is discharged by EVALUATION, as an in-region `assert` placed before the
    # frozen impl body, which is kept verbatim so the method's own three
    # `ensures` still discharge as well. The six conjuncts pin the frozen
    # decision functions at the concrete F2P-shaped points of BOTH failing tests:
    # a three-tick categorical axis horizontally and vertically (with the
    # vertical pair genuinely REVERSED, not merely present), the pinned-pair arm
    # at a non-half-integer pair, the ordinary-axis identity arm at a default
    # pair far from any half-integer interval, and both arms of the grid
    # decision. Non-degeneracy is what the last four buy: a spec that collapsed
    # every arm to one answer, or that agreed with gold's shape but not its
    # values, fails at least one conjunct.
    #
    # The assert is LIVE, not decoration — machine-checked during the audit that
    # added this case. Five separate one-value mutations of it each leave an
    # unsolved goal and the module fails to build (exit 1): the horizontal upper
    # edge moved one step, the vertical pair un-reversed, the categorical grid
    # arm flipped, the pinned upper limit perturbed, and the default upper limit
    # perturbed. As written it builds (exit 0). The proof body is extended only
    # to split the conjunction and close each conjunct by evaluation; the
    # `prove_correct finalizeAxis` header and every `ensures` are untouched, and
    # the tactic body is elided from the spec view.
    # =====================================================================
    {
        "id": "admiss-f2p-decision",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (decidedGrid true true = false\n"
            "        ∧ decidedGrid false true = true\n"
            "        ∧ decidedLimits true false false 3 0 0 1 100 = (-1 / 2, 5 / 2)\n"
            "        ∧ decidedLimits true false true 3 0 0 1 100 = (5 / 2, -1 / 2)\n"
            "        ∧ decidedLimits true true false 3 (-1) (21 / 10) 1 100 = (-1, 21 / 10)\n"
            "        ∧ decidedLimits false false false 3 0 0 1 100 = (1, 100)))\n"
            + _IMPL,
            _PROOF + "\n"
            "  all_goals (repeat' apply And.intro)\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (with_unfolding_all rfl)\n"
            "    | simp_all [decidedGrid, decidedLimits]"),
        "rationale": "the frozen obligation is SATISFIABLE and NON-DEGENERATE at "
                     "the F2P-shaped inputs of both failing tests, discharged by "
                     "evaluation in an in-region assert before the impl body "
                     "(which is kept verbatim, so E1/E2/E3 discharge too). Six "
                     "conjuncts: a three-tick categorical axis draws to "
                     "(-1/2, 5/2) horizontally and to the REVERSED (5/2, -1/2) "
                     "vertically; a pinned non-half-integer pair comes back "
                     "verbatim even on a categorical axis; an ordinary axis is "
                     "left at a default pair (1, 100) no tick-relative interval "
                     "could coincide with; and the grid decision is suppressed on "
                     "the categorical arm while standing on the identity arm. "
                     "This is the total-carrier form of PRECOND-TOO-STRONG: with "
                     "an empty pre-conditions region nothing can exclude an "
                     "input, so the live risk is the obligation being "
                     "unsatisfiable or collapsed exactly where the failing tests "
                     "look — which every reject case here is blind to, since a "
                     "rival is refuted by DIFFERING from gold and a difference "
                     "survives gold's own answer being degenerate. The assert is "
                     "live: five one-value mutations of it (the horizontal upper "
                     "edge, the vertical reversal, the categorical grid arm, the "
                     "pinned upper limit, the default upper limit) each leave an "
                     "unsolved goal and fail to build. If this FAILED to verify "
                     "=> PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each shares the frozen spec, attacks
    # one arm of the cascade or of the grid decision, keeps the frozen proof
    # (which cannot close the wrong body — the intended rejection), and carries a
    # machine-checked witness that ELABORATES against the rival and FAILS against
    # the frozen solution. The witness — not the tactic failure — is what
    # attributes the rejection to the spec.
    # =====================================================================

    # ---- E2 / L2: the categorical lower edge ----
    {
        "id": "rival-lo-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # The categorical interval starts at the first tick's own position rather
        # than half a step before it.
        "module": _impl(_cascade(lo_cat="0")),
        "refinement": "its faithful counterpart starts the categorical interval "
                      "AT the first tick rather than half a step before it, so "
                      "the observed lower view limit on the failing "
                      "horizontal-axis test would be the tick position instead "
                      "of the half-step offset the test asserts by exact "
                      "equality. It would NOT resolve.",
        "rationale": "REJECT from E2 via L2 (¬hasUserLimit ∧ isCategorical ∧ "
                     "¬isY → lo = -1/2): the rival emits 0. Refuted at "
                     "isCategorical=true, hasUserLimit=false, isY=false, "
                     "nticks=3 — gold's tester returns true there, the rival's "
                     "false. Non-default filler pairs (7,9) and (11,13) keep the "
                     "input point distinct from every other witness and confirm "
                     "the violation is in the categorical arm, not a leaked "
                     "supplied value. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("true false false 3 7 9 11 13 true"),
    },

    # ---- E2/E3 / L3: the vertical-axis reversal ----
    {
        "id": "rival-no-invert",
        "kind": "uniqueness",
        "expect": "reject",
        # Omits the vertical reversal entirely: a vertical categorical axis gets
        # the same ascending pair as a horizontal one.
        "module": _impl(
            "    let mut lo : Rat := autoLo\n"
            "    let mut hi : Rat := autoHi\n"
            "    let grid : Bool := if isCategorical then false else gridWasOn\n"
            "    if hasUserLimit then\n"
            "      lo := userLo\n"
            "      hi := userHi\n"
            "    else\n"
            "      pure ()\n"
            "    if isCategorical then\n"
            "      if hasUserLimit then\n"
            "        pure ()\n"
            "      else\n"
            "        lo := -1 / 2\n"
            "        hi := (nticks : Rat) - 1 / 2\n"
            "    else\n"
            "      pure ()\n"
            "    return { lo := lo, hi := hi, gridVisible := grid }"),
        "refinement": "its faithful counterpart never reverses the interval on "
                      "the vertical axis, so a categorical vertical axis comes "
                      "out ascending. The failing vertical-axis test asserts the "
                      "reversed (descending) pair by exact equality, so it would "
                      "NOT resolve — and the reversal is one of the three "
                      "behaviours the public request names explicitly.",
        "rationale": "REJECT from E2 AND E3 via L3 (¬hasUserLimit ∧ "
                     "isCategorical ∧ isY → (lo, hi) = (nticks - 1/2, -1/2)): "
                     "the rival returns the ascending pair, so both components "
                     "are wrong simultaneously. Uniquely attacks the ORDER of "
                     "the two edge values (both are individually correct edge "
                     "positions — only their assignment to lo/hi is swapped), "
                     "which no value-level rival can reach. Refuted at "
                     "isY=true, nticks=3; gold's tester is true there. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness("true false true 3 1 2 4 8 false"),
    },

    # ---- E2/E3 / L1: the pinned pair must outrank the categorical treatment ----
    {
        "id": "rival-cat-over-explicit",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the inner guard, so the categorical treatment overwrites a pair
        # the consumer pinned explicitly.
        "module": _impl(_cascade(inner_guard=False)),
        "refinement": "its faithful counterpart drops the guard that skips the "
                      "categorical limit-set when the consumer pinned limits, so "
                      "the categorical interval overwrites them. Both failing "
                      "tests pin an explicit pair in their second half and "
                      "assert it comes back verbatim, so this counterpart would "
                      "NOT resolve.",
        "rationale": "REJECT from E2/E3 via L1 (hasUserLimit → (lo, hi) = "
                     "(userLo, userHi)), the highest-priority arm: when BOTH "
                     "hasUserLimit and isCategorical hold, the pinned pair must "
                     "win. Refuted at hasUserLimit=true, isCategorical=true, "
                     "userLo=-1, userHi=21/10 — a non-half-integer pinned pair, "
                     "so the rival's substituted categorical interval cannot "
                     "coincide with it at any tick count. Uniquely varies "
                     "hasUserLimit=true WITH isCategorical=true (the only "
                     "witness at that corner). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("true true false 3 (-1) (21/10) 0 0 true"),
    },

    # ---- E3 / L2: the categorical upper edge, off by one step ----
    {
        "id": "rival-wrong-upper",
        "kind": "uniqueness",
        "expect": "reject",
        # The interval extends half a step PAST where it should, widening it by a
        # full step.
        "module": _impl(_cascade(edge="(nticks : Rat) + 1 / 2")),
        "refinement": "its faithful counterpart offsets the upper edge in the "
                      "wrong direction, widening the interval by a full step. "
                      "The failing horizontal-axis test asserts the exact upper "
                      "limit, so a one-step-wider interval would NOT resolve.",
        "rationale": "REJECT from E3 via L2 (hi = nticks - 1/2): the rival emits "
                     "nticks + 1/2. Refuted at a DIFFERENT tick count from every "
                     "other witness (nticks=5), which is what shows the clause "
                     "binds the edge to the count rather than to a constant: the "
                     "rival's error is a fixed offset, so it must be exhibited "
                     "at a count where gold's value is known — gold's tester is "
                     "true at this point. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("true false false 5 2 3 6 7 false"),
    },

    # ---- E2/E3 / L2-L3: the edge must track the tick count, not a constant ----
    {
        "id": "rival-hardcode-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Pins the far edge to the single-tick constant, ignoring the count
        # entirely. Correct only when there is exactly one tick.
        "module": _impl(_cascade(edge="1 / 2")),
        "refinement": "its faithful counterpart ignores the tick count and pins "
                      "the far edge to the value that is only correct for a "
                      "single tick, so on the failing tests' three-level axes "
                      "the interval would span one step instead of three. It "
                      "would NOT resolve. (It coincides with correct behaviour "
                      "only at a one-tick axis, which neither failing test uses.)",
        "rationale": "REJECT from E2 via L3 (¬hasUserLimit ∧ isCategorical ∧ "
                     "isY → lo = nticks - 1/2): the rival emits the constant "
                     "1/2 regardless of the count, so "
                     "it agrees with gold at nticks=1 and diverges everywhere "
                     "else. At the witness point the rival returns "
                     "(lo, hi) = (1/2, -1/2) where gold's decision is "
                     "(7/2, -1/2) — machine-checked, so it is the LOWER "
                     "component (E2) that the isY arm refutes here, while hi "
                     "is coincidentally right; on the horizontal arm the same "
                     "constant instead breaks E3. Refuted at nticks=4 — a "
                     "fourth distinct tick count "
                     "across the battery, chosen away from 1 precisely because "
                     "that is the point the rival gets right. NOTE this rival is "
                     "STRONGER here than on the nagini sibling, where the count "
                     "was an opaque contract-only callee and the argument had to "
                     "route through its `>= 1` contract; here the count is a "
                     "transparent input and one concrete value refutes it "
                     "outright. If it verified => SPEC-TOO-WEAK (the spec would "
                     "have failed to bind the edge to the tick count).",
        "witness": _witness("true false true 4 0 1 2 3 true"),
    },

    # ---- E2/E3 / L4: the ordinary-axis identity (the recorded prior break) ----
    {
        "id": "rival-cat-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the categorical gate on the limit cascade: EVERY axis without a
        # pinned pair gets the categorical interval, ordinary or not.
        "module": _impl(_cascade(limit_guard="true")),
        "refinement": "the attack the sibling records as an actual prior break. "
                      "Its faithful counterpart drops the categorical gate on "
                      "the limit decision and applies the tick-relative interval "
                      "to EVERY axis without a pinned pair, clobbering ordinary "
                      "continuous axes — including log-scaled ones, whose hidden "
                      "regression tests then fail (observed: not resolved, in "
                      "the recorded attack run). It would NOT resolve.",
        "rationale": "REJECT from E2/E3 via L4 (¬hasUserLimit ∧ ¬isCategorical → "
                     "(lo, hi) = (autoLo, autoHi)): an ordinary axis must be "
                     "left at its default margin limits. Refuted at "
                     "isCategorical=FALSE with a wide default pair "
                     "(autoLo=1, autoHi=100) that no tick-relative interval can "
                     "coincide with: at nticks=3 gold's L4 answer is (1, 100) "
                     "while the rival substitutes (-1/2, 5/2), so BOTH components "
                     "are wrong at once. (autoLo/autoHi are load-bearing in "
                     "rival-auto-pair-swapped and rival-grid-always-on too; what "
                     "is unique here is the SUBSTITUTION of a tick-relative "
                     "interval for the supplied pair, which needs a default pair "
                     "far from any half-integer interval.) This is "
                     "the clause a weaker earlier spec left unconstrained; if it "
                     "verified => SPEC-TOO-WEAK (a replay of the original "
                     "break).",
        "witness": _witness("false false false 3 0 0 1 100 true"),
    },

    # ---- E2/E3 / L4: the default pair's ORDER ----
    {
        "id": "rival-auto-pair-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Reads the ordinary default-margin pair in the wrong order, inverting an
        # ordinary axis instead of leaving it alone.
        "module": _impl(_cascade(init_lo="autoHi", init_hi="autoLo")),
        "refinement": "its faithful counterpart transposes the ordinary default "
                      "margin limits, inverting every continuous axis that has "
                      "no pinned pair. Inversion is supposed to apply only to a "
                      "categorical vertical axis; applying it to ordinary axes "
                      "flips them upside down and would break the many "
                      "regression tests that read back an ordinary axis's "
                      "limits, so it would NOT resolve.",
        "rationale": "REJECT from E2/E3 via L4, attacking the arm's ORDER rather "
                     "than its values: both components are transported, but into "
                     "the wrong fields. rival-cat-everywhere attacks the same arm "
                     "by SUBSTITUTING different values and agrees with gold "
                     "whenever the default pair happens to equal the categorical "
                     "interval; this near-miss agrees with gold on every "
                     "SYMMETRIC default pair and needs an ASYMMETRIC one, so it "
                     "gets its own input point: autoLo=-2, autoHi=17/4 at "
                     "isY=true. Gold's tester is true there. This ORDER clause "
                     "has no nagini counterpart (the sibling's carrier had no "
                     "default-margin pair). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("false false true 3 0 0 (-2) (17/4) false"),
    },

    # ---- E2/E3 / L1: the pinned pair's ORDER ----
    {
        "id": "rival-user-pair-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Reads the consumer's pinned pair in the wrong order.
        "module": _impl(_cascade(user_lo="userHi", user_hi="userLo")),
        "refinement": "its faithful counterpart transposes the consumer's pinned "
                      "pair, so a requested interval comes back reversed. Both "
                      "failing tests pin a pair and assert it is returned "
                      "verbatim (as an ordered pair), so this counterpart would "
                      "NOT resolve.",
        "rationale": "REJECT from E2/E3 via L1, attacking that arm's ORDER: the "
                     "pinned components are used but transposed. Distinct from "
                     "rival-cat-over-explicit, which attacks L1 by letting the "
                     "categorical arm OVERRIDE it — that rival is refutable only "
                     "where isCategorical holds, whereas this one is wrong on "
                     "every asymmetric pinned pair including on ORDINARY axes, "
                     "so it is refuted at isCategorical=FALSE, hasUserLimit=true "
                     "with the asymmetric pair (-1, 21/10) — a corner no other "
                     "witness occupies. Gold's tester is true there. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness("false true false 3 (-1) (21/10) 0 0 true"),
    },

    # ---- E1: the grid decision ----
    {
        "id": "rival-grid-always-on",
        "kind": "uniqueness",
        "expect": "reject",
        # Reports the grid visible on every axis: never suppressed on a
        # categorical axis, and forced on for an ordinary axis whose style
        # suppresses it.
        "module": _impl(_grid_rival("true")),
        "refinement": "its faithful counterpart forces gridlines on for every "
                      "axis. The failing tests assert that NO gridline is "
                      "visible on the categorical axis, so it would NOT resolve; "
                      "it additionally forces a grid onto ordinary axes whose "
                      "active style suppresses it.",
        "rationale": "REJECT from E1 (gridVisible = decidedGrid isCategorical "
                     "gridWasOn) on BOTH arms: it violates the categorical arm "
                     "(must be suppressed) and the identity arm whenever "
                     "gridWasOn is false. Refuted on the IDENTITY arm at "
                     "isCategorical=false, gridWasOn=FALSE — the corner where "
                     "the two clauses disagree, so forcing the grid on is wrong "
                     "there on E1 alone: this witness holds the limit cascade at "
                     "gold's own L4 answer (autoLo, autoHi) = (5, 6), leaving the "
                     "grid clause as the only violated one. (rival-auto-pair-"
                     "swapped shares the isCategorical=false, gridWasOn=false "
                     "corner; it is separated from this case by needing an "
                     "ASYMMETRIC default pair, which this witness deliberately "
                     "does not use.) Gold's tester is true "
                     "there. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("false false false 3 0 0 5 6 false"),
    },
    {
        "id": "rival-grid-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Exactly backwards: visible on a categorical axis, suppressed on an
        # ordinary one.
        "module": _impl(_grid_rival("isCategorical")),
        "refinement": "its faithful counterpart is exactly inverted — it "
                      "suppresses gridlines on ordinary axes and keeps them on "
                      "categorical ones. The failing tests assert no visible "
                      "gridline on the categorical axis, so it would NOT resolve.",
        "rationale": "REJECT from E1: the rival returns isCategorical, the exact "
                     "negation of the required behaviour on the categorical arm. "
                     "Refuted at isCategorical=true with gridWasOn=false, the "
                     "input where the rival's answer differs from BOTH of gold's "
                     "arms, so no reading of the clause admits it. Distinct "
                     "input point from grid-passthrough (which needs gridWasOn "
                     "TRUE to be wrong). Gold's tester is true there. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness("true false false 2 0 0 0 0 false"),
    },
    {
        "id": "rival-grid-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # The unfixed behaviour: the decision never touches any axis's grid, so a
        # categorical axis keeps whatever the style chose.
        "module": _impl(_grid_rival("gridWasOn")),
        "refinement": "this is the unfixed behaviour verbatim: the decision never "
                      "suppresses any axis's gridlines, so under a "
                      "grid-drawing style the categorical axis keeps them. That "
                      "is exactly the state the failing tests observe and the "
                      "change removes, so it does NOT resolve — the "
                      "differential-gate witness.",
        "rationale": "REJECT from E1 (isCategorical → ¬gridVisible): the rival "
                     "returns gridWasOn on every axis, so it is wrong precisely "
                     "when a categorical axis's active style WOULD draw the grid. "
                     "Refuted at isCategorical=true, gridWasOn=TRUE (the "
                     "scenario the failing tests exercise) — the complementary "
                     "corner to grid-inverted, and at a fifth distinct tick "
                     "count (6) on the vertical axis. Gold's tester is true "
                     "there. If it verified => SPEC-TOO-WEAK (the spec would "
                     "admit the unfixed behaviour).",
        "witness": _witness("true false true 6 0 0 0 0 true"),
    },
    {
        "id": "rival-grid-force-off",
        "kind": "uniqueness",
        "expect": "reject",
        # Suppresses the grid on EVERY axis: drops the categorical gate on the
        # grid decision. Indistinguishable from correct on the categorical side —
        # only the identity arm refutes it.
        "module": _impl(_grid_rival("false")),
        "refinement": "its faithful counterpart drops the categorical gate on the "
                      "grid decision and suppresses gridlines unconditionally, so "
                      "an ordinary axis under a grid-drawing style silently loses "
                      "its grid. The failing tests would still pass, but this is "
                      "a behaviour change on axes the decision must leave alone — "
                      "observable on any continuous axis under a grid-drawing "
                      "style — so it would NOT resolve.",
        "rationale": "REJECT from E1's IDENTITY arm (¬isCategorical → "
                     "gridVisible = gridWasOn): the rival is correct on the whole "
                     "categorical side and wrong ONLY where an ordinary axis's "
                     "style draws the grid. That makes it the near-miss of the "
                     "grid trio, so it is refuted at its own point: "
                     "isCategorical=false, gridWasOn=TRUE. It is also the only "
                     "witness that combines hasUserLimit=true with "
                     "isCategorical=false and isY=true, exercising L1 on an "
                     "ordinary vertical axis. Gold's tester is true there. This "
                     "is the exact hole a weaker earlier spec (which hardcoded "
                     "the ordinary-axis grid result) left open; if it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _witness("false true true 3 (-3) 4 0 0 true"),
    },

    # ---- E2 / L2-L3: the edge at a ZERO tick count (added by audit) ----
    {
        "id": "rival-nat-truncated-edge",
        "kind": "uniqueness",
        "expect": "reject",
        # Recomputes the far edge by stepping back one TICK and then forward half
        # a step: `(nticks - 1) + 1/2` with the subtraction done in `Nat`. Equal
        # to gold at every positive tick count, so it survives every other
        # witness in this battery; `Nat` truncation at nticks=0 makes it emit
        # +1/2 where the clause demands -1/2.
        "module": _impl(_cascade(edge="((nticks - 1 : Nat) : Rat) + 1 / 2")),
        "refinement": "its faithful counterpart computes the far edge by backing "
                      "up one tick and adding half a step, in an integer type "
                      "that cannot go below zero. On every axis that has at least "
                      "one tick it agrees with the correct behaviour exactly, so "
                      "both failing tests still resolve; on an axis with NO ticks "
                      "the truncation places the far edge half a step on the "
                      "wrong side of the origin, inverting a degenerate axis "
                      "instead of collapsing it. A near-miss that the failing "
                      "tests cannot see, which is precisely why the spec has to.",
        "rationale": "REJECT from E2 via L2/L3 (edge = nticks - 1/2), attacking "
                     "the arm at the one input the rest of the battery never "
                     "reaches: nticks=0. Every other witness uses a count in "
                     "2..6, where this rival is EXACTLY gold — it is refutable "
                     "only at zero, because `Nat` subtraction truncates there "
                     "(0 - 1 = 0, so the rival's edge is +1/2 while the clause "
                     "demands -1/2). This is the carrier trap the clause is "
                     "stated over `Rat` to avoid, and the arithmetic that "
                     "realises it is a plausible way to write the same edge. "
                     "If it verified => SPEC-TOO-WEAK (the cascade would be "
                     "pinned only on positive tick counts).",
        "witness": _witness("true false false 0 0 0 0 0 true"),
    },

    # ---- E2/E3 / L1: the pinned pair transposed on ONE axis (added by audit) ----
    {
        "id": "rival-user-pair-swapped-on-y",
        "kind": "uniqueness",
        "expect": "reject",
        # Transposes the consumer's pinned pair only on the VERTICAL axis, as if
        # the categorical inversion rule also governed pinned limits. Strictly
        # subtler than rival-user-pair-swapped: correct on every horizontal axis.
        "module": _impl(_cascade(user_lo="if isY then userHi else userLo",
                                 user_hi="if isY then userLo else userHi")),
        "refinement": "its faithful counterpart over-applies the vertical "
                      "inversion rule: it reverses the consumer's pinned pair on "
                      "a vertical axis, as though pinning limits opted into the "
                      "same reversal the categorical treatment performs. A "
                      "consumer who pins a vertical range then gets it back "
                      "upside down, so any test that pins a vertical pair and "
                      "reads it back would NOT resolve.",
        "rationale": "REJECT from E2/E3 via L1 (hasUserLimit → (lo, hi) = "
                     "(userLo, userHi)) — which the clause states with NO "
                     "dependence on isY, and that independence is what this "
                     "rival denies. Strictly subtler than "
                     "rival-user-pair-swapped, which transposes on both axes and "
                     "so is refuted at isY=false: this one is EXACTLY gold on "
                     "every horizontal axis, so the existing L1 witnesses (both "
                     "at isY=false) cannot see it. Refuted at hasUserLimit=true, "
                     "isY=TRUE with the asymmetric pair (-1, 21/10), a corner no "
                     "other witness occupies. If it verified => SPEC-TOO-WEAK "
                     "(L1 would be pinned only on the horizontal axis).",
        "witness": _witness("false true true 3 (-1) (21/10) 0 0 true"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING
#
# The sibling battery has 14 SPEC cases (3 soundness positives, 1 admissibility,
# 10 uniqueness rivals) plus a 3-case AXIOM lane. It contracts TWO functions
# (`finalize_axis_range` over five scalars, `finalize_axis_grid` over two) and a
# `@Pure @ContractOnly` `slot_count()` oracle. This bundle fuses both into ONE
# method returning a record, with the tick count as a transparent `Nat` input.
#
#   sibling case                -> here                        disposition
#   -------------------------------------------------------------------------
#   pos-range-reorder           -> pos-inverted-guards         PORTED (re-expressed)
#   pos-grid-direct             -> pos-expr-ladder             PORTED (re-expressed)
#   cheap-grounded-range        -> pos-reverse-pair            PORTED (re-aimed)
#   admiss-fshaped-input        -> admiss-f2p-decision         PORTED (re-aimed;
#                                                              audit: was wrongly
#                                                              recorded VACUOUS)
#   rival-lo-zero               -> rival-lo-zero               PORTED
#   rival-no-invert             -> rival-no-invert             PORTED
#   rival-cat-over-explicit     -> rival-cat-over-explicit     PORTED
#   rival-wrong-upper           -> rival-wrong-upper           PORTED
#   rival-hardcode-one          -> rival-hardcode-one          PORTED (strengthened)
#   rival-cat-everywhere        -> rival-cat-everywhere        PORTED
#   rival-grid-always-on        -> rival-grid-always-on        PORTED
#   rival-grid-inverted         -> rival-grid-inverted         PORTED
#   rival-grid-passthrough      -> rival-grid-passthrough      PORTED
#   rival-grid-force-off        -> rival-grid-force-off        PORTED
#   (no sibling counterpart)    -> rival-auto-pair-swapped     NEW (L4 order)
#   (no sibling counterpart)    -> rival-user-pair-swapped     NEW (L1 order)
#   (no sibling counterpart)    -> rival-nat-truncated-edge    NEW (audit: nticks=0)
#   (no sibling counterpart)    -> rival-user-pair-swapped-on-y NEW (audit: L1 vs isY)
#   AXIOM_TESTS ([3 probes])    -> (none)                      DROPPED (G-AX/G-CONF)
#   frame / permission-mutation -> (none)                      VACUOUS
#   divergence lane            -> (none)             SPEC-CLOSED (see below)
#
# ALL TEN of the sibling's uniqueness rivals PORTED — the two carriers model the
# same decision, so nothing was lost to carrier narrowing on the attack side.
# Each carries a witness seen to discriminate with two real builds.
#
# PORTED, strengthened (rival-hardcode-one). On nagini the tick count is an opaque
#   `@Pure @ContractOnly` callee, so the argument had to route through its
#   `Result() >= 1` contract. Here the count is a transparent `Nat` input, so one
#   concrete value (nticks=4) refutes the constant outright — a strictly stronger
#   demonstration of the same clause.
# PORTED, re-aimed (cheap-grounded-range -> pos-reverse-pair). The sibling's third
#   positive exists to show that returning the oracle's value directly is GOLD and
#   not a wrong echo — it fills the ungrounded-oracle slot with an honest control.
#   There is no oracle here at all (the `axioms` region is empty; meta.json
#   declares `axioms: []` and `deep_model_references: []`), so the echo-vulnerability
#   class does not exist and its honest control has no target. Its DEFENSIVE role
#   — a third independent correct shape for the categorical arm — is kept, re-aimed
#   at naming the two edges once as an ascending pair and reversing them for the
#   vertical axis.
# NEW (2 rivals, carrier widening). The sibling's range function receives the
#   consumer's pinned pair but has no counterpart for the ordinary default-margin
#   pair; this spec carries both and pins each as an ORDERED pair (L1, L4). Two
#   rivals transpose them. These are not fabrications: each attacks a real
#   independent arm of the frozen cascade, and each is a genuine near-miss
#   (correct on every symmetric pair) refuted at its own asymmetric input point.
# PORTED, re-aimed (admiss-fshaped-input -> admiss-f2p-decision). The sibling
#   self-calls the range function to show its numeric precondition (non-NaN,
#   non-singular pinned pair) admits an F2P-shaped input. An earlier revision of
#   this file recorded the lane VACUOUS because this bundle declares NO `require`
#   clause (the `pre-conditions` region is EMPTY), so no input can be excluded.
#   An audit showed that reason to be WRONG, with real builds. "No precondition"
#   removes only ONE of the two shapes PRECOND-TOO-STRONG takes. On a total
#   domain the other is live: the OBLIGATION can be unsatisfiable or DEGENERATE
#   at exactly an F2P-shaped input, and a spec whose decision functions do not
#   evaluate to the values the failing tests demand looks identical from the
#   outside to a spec every impl meets. No reject case here can see it — each
#   rival is refuted by DIFFERING from gold, and a difference survives gold's own
#   answer at the interesting point being degenerate — so dropping the lane
#   dropped the direction entirely. `admiss-f2p-decision` fills it by discharging
#   the frozen decision functions at both failing tests' concrete points, by
#   evaluation, in an in-region assert before the frozen impl body (kept verbatim
#   so E1/E2/E3 discharge too). Machine-checked live: as written exit 0, and five
#   separate one-value mutations of the assert each exit 1 on an unsolved goal.
#   The vacuous-precondition fact remains true and is still load-bearing for the
#   WITNESSES: the derived tester is `if decide pre then <post check> else true`,
#   so a tester value of `false` requires the precondition to HOLD at that input.
#   All fourteen reject witnesses depend on it, and all of them elaborate.
# VACUOUS (frame / permission-mutation). The sibling's own defended-surface note
#   records that all five range inputs are read-only by-value scalars with no
#   mutable reference input, so the class was already empty on nagini. This
#   backend is referentially transparent: every input is an immutable value, the
#   method declares no `mut` parameter, and there is no heap or aliasing. Per the
#   porting map this class is dropped, not replaced; no substitute probe is
#   fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
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
# DROPPED (AXIOM_TESTS). The sibling's three probes validate `slot_count()`'s
#   contract and its two deep-model references against the real callees in the
#   instance image. This bundle consumes no axiom and declares no deep-model
#   reference (meta.json: `axioms: []`, `deep_model_references: []`, G-AX = skip);
#   the whole decision is concrete over the method's own inputs, so there is
#   nothing to probe. The gate ignores AXIOM_TESTS regardless.
#
# AUDIT ADDENDUM (independent re-derivation of the twelve original cases).
#   An independent auditor rebuilt all twelve reject witnesses with the gate's own
#   surgery (three builds each: `= false` vs rival -> exit 0, `= false` vs the
#   frozen solution -> exit 1 with a computed `The left-hand side ... is not
#   definitionally equal to ... false` and NO stuck-reduction string, `= true` vs
#   the frozen solution -> exit 0), rebuilt the three positives (all exit 0), and
#   re-ran the statement-integrity diff (every case's text outside the impl region
#   and the `prove_correct` tactic body is byte-identical to the frozen file). It
#   also re-measured the tactic claims above: plain `decide` is stuck against BOTH
#   the rival and gold, and `decide +kernel` proves the rival (exit 0) while
#   failing on gold with the elaborator's `did not reduce to isTrue or isFalse`
#   fallback — exactly as recorded, and exactly the string the gate screens.
#   Two prose claims were WRONG and are corrected above (the input points are
#   unchanged; only the descriptions were): rival-grid-always-on is not the only
#   witness at isCategorical=false with gridWasOn=false (rival-auto-pair-swapped
#   shares that corner), and rival-cat-everywhere is not the only witness making
#   autoHi load-bearing (rival-auto-pair-swapped and rival-grid-always-on do too).
#   rival-hardcode-one's clause label was also wrong: at its isY witness point the
#   rival returns (1/2, -1/2) against gold's (7/2, -1/2), so the refuted component
#   is E2's, not E3's (both machine-checked).
#   TWO rivals were ADDED to close gaps the twelve left open, each a near-miss the
#   pre-existing witnesses provably cannot see:
#     rival-nat-truncated-edge      L2/L3 at nticks=0 (every other witness uses
#                                   2..6, where the rival IS gold)
#     rival-user-pair-swapped-on-y  L1 at isY=true (both other L1 witnesses sit at
#                                   isY=false, where the rival IS gold)
#   SPEC PROBES, no hole found. Five further wrong impls were built and all were
#   rejected with discriminating witnesses (the two above plus: the default pair
#   normalised by min/max, refuted on a DESCENDING auto pair; the grid additionally
#   suppressed whenever limits are pinned; the categorical lower edge collapsed at
#   a zero count). Four correct reshapes were built: a boolean-conjunction grid and
#   a single-`return` pair-destructuring cascade both verify with the frozen proof
#   body; a `Prod.swap` reshape verifies with one added `split`. The fourth writes
#   the edge as `(2n-1)/2` and was NOT closed — it leaves a residual `Rat`
#   identity, and this workspace has no `ring`/`ring_nf`/`linarith`/`norm_num`/
#   `field_simp` (each measured `unknown tactic`) and no `sub_div` lemma. That is
#   an UNRESOLVED reshape, not a demonstrated spec-too-strong: the obligation is
#   about a provable equality of two `Rat` expressions, and failing to find the
#   tactic is not evidence the spec rejects the shape.
#
# OBLIGATION / CLAUSE / BINDER COVERAGE (what the gate does NOT check).
#   ONE obligation (`prove_correct finalizeAxis`), DEFENDED by three soundness
#   positives plus one admissibility positive (`admiss-f2p-decision`, which pins
#   the obligation as satisfiable and non-degenerate at both failing tests'
#   concrete points) and ATTACKED by fourteen uniqueness rivals.
#   Every top-level clause and every cascade arm is attacked:
#     E1 categorical arm -> grid-always-on, grid-inverted, grid-passthrough
#     E1 identity arm    -> grid-always-on, grid-force-off
#     E2/E3 via L1       -> cat-over-explicit (override), user-pair-swapped (order),
#                           user-pair-swapped-on-y (order, vertical axis only)
#     E2/E3 via L2       -> lo-zero (lower edge), wrong-upper (upper edge),
#                           hardcode-one (edge vs. count),
#                           nat-truncated-edge (edge at a zero count)
#     E2/E3 via L3       -> no-invert (reversal/order), hardcode-one,
#                           nat-truncated-edge
#     E2/E3 via L4       -> cat-everywhere (substitution), auto-pair-swapped (order)
#   Every one of the NINE input binders is VARIED by the reject witnesses, and each
#   is load-bearing in at least one:
#     isCategorical true (lo-zero, no-invert, cat-over-explicit, wrong-upper,
#                   hardcode-one, grid-inverted, grid-passthrough,
#                   nat-truncated-edge)
#                   / FALSE (cat-everywhere, auto-pair-swapped, user-pair-swapped,
#                   user-pair-swapped-on-y, grid-always-on, grid-force-off)
#     hasUserLimit  true (cat-over-explicit, user-pair-swapped,
#                   user-pair-swapped-on-y, grid-force-off)
#                   / false (the other ten)
#     isY           true (no-invert, hardcode-one, grid-passthrough,
#                   auto-pair-swapped, grid-force-off, user-pair-swapped-on-y)
#                   / false (the other eight)
#     nticks        SIX distinct counts — 0 (nat-truncated-edge),
#                   2 (grid-inverted), 3 (lo-zero,
#                   no-invert, cat-over-explicit, cat-everywhere, grid-always-on,
#                   all three pair-swaps, grid-force-off), 4 (hardcode-one),
#                   5 (wrong-upper), 6 (grid-passthrough) — which is what makes
#                   the "edge tracks the count" clause testable at all: a battery
#                   at one fixed count could not distinguish `nticks - 1/2` from
#                   any constant. ZERO is its own corner: it is the only count at
#                   which a `Nat`-truncated recomputation of the edge diverges
#                   from the clause, which is what nat-truncated-edge exploits.
#     userLo/userHi load-bearing in cat-over-explicit, user-pair-swapped and
#                   user-pair-swapped-on-y with
#                   the ASYMMETRIC non-half-integer pair (-1, 21/10); varied as
#                   filler elsewhere ((7,9), (1,2), (2,3), (0,1), (-3,4)) so no
#                   two witnesses share an input point.
#     autoLo/autoHi load-bearing in cat-everywhere (1, 100), where the rival
#                   SUBSTITUTES a tick-relative interval for the supplied pair,
#                   and in auto-pair-swapped (-2, 17/4), where an ASYMMETRIC pair
#                   is what exposes a transposition; also load-bearing (as gold's
#                   own L4 answer) in grid-always-on (5, 6). Varied as filler
#                   elsewhere ((11,13), (4,8), (6,7)).
#     gridWasOn     load-bearing at BOTH values: TRUE in grid-passthrough (a
#                   categorical axis whose style draws the grid) and
#                   grid-force-off (an ordinary axis whose style draws it), FALSE
#                   in grid-always-on and grid-inverted (where forcing it on is
#                   the violation). A battery holding it at one value would miss
#                   one of the two grid rivals entirely.
#   The fourteen reject witnesses probe FOURTEEN DISTINCT input tuples (pts = 14):
#   no two rivals share an input point. The six NEAR-MISSES that agree with gold
#   over more of the domain than their siblings each get their own discriminating
#   point rather than sharing one — grid-force-off (correct on the whole
#   categorical side; refuted on the identity arm at gridWasOn=true),
#   auto-pair-swapped and user-pair-swapped (correct on every symmetric pair;
#   refuted at asymmetric pairs), hardcode-one (correct at a one-tick axis;
#   refuted at nticks=4), nat-truncated-edge (correct at EVERY positive count;
#   refuted only at nticks=0) and user-pair-swapped-on-y (correct on every
#   horizontal axis; refuted only at isY=true).
# WITNESS DISCRIMINATION (three real builds per reject case, during authoring).
#   Reproducing the gate's own file surgery (pbt_witness.witness_file, so the
#   `prove_correct` block is stripped exactly as the gate strips it), each of the
#   fourteen witnesses was built three ways:
#     A. `= false` vs the RIVAL            -> exit 0
#     B. `= false` vs the frozen solution  -> exit 1, no stuck-reduction message
#     C. `= true`  vs the frozen solution  -> exit 0
#   A and B are the gate's two halves; C is what makes B evidence rather than an
#   artifact (a stuck reduction fails for EVERY claim, so C would fail too if the
#   term were irreducible). All fourteen pass A, B and C.
#
#   TACTIC CHOICE, and why it is load-bearing. Plain `decide` reduces through
#   `instDecidableEqRat` and sticks on `Rat.num` (measured) — it fails on the
#   RIVAL as well, so it never clears half A. `decide +kernel` clears A and B on
#   exit codes, but its gold-side failure message is the elaborator's fallback
#   `did not reduce to isTrue or isFalse`, which is exactly the string the gate
#   screens for as a stuck reduction — so an earlier revision of this battery was
#   recorded MALFORMED-TESTS with nine cases `witness-undecided`. That screen is
#   correct to exist (an irreducible term fails for every claim, so the exit code
#   would attest to a refutation never performed); it simply cannot tell "stuck"
#   from "stuck-looking" by exit code. Here the term IS computable — column C
#   proves it — so the fix is a tactic whose failure is unambiguous:
#   `with_unfolding_all rfl` computes the tester by definitional unfolding and
#   reports `The left-hand side ... is not definitionally equal to ... false`.
#   Same rivals, same twelve probe points, same clauses attacked; only the closing
#   tactic changed. It decides strictly more here than `decide` does and assumes
#   nothing.
#
#   No witness binds a hypothesis (the carrier is fully transparent — no `opaque`
#   term exists), so no joint-satisfiability obligation arises and no consistency
#   probe is needed. No `sorry`/`admit`/`native_decide`/`axiom` appears in any
#   case, and no case adds a `theorem`/`lemma`/`def` beyond the frozen set.
AXIOM_TESTS = []
