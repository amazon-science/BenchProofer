"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20676 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_initialMarkers`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); it
carries over that battery's adversarial ARGUMENT and re-expresses it against this
backend's carrier. It is not a translation of the nagini text.

DEFENDED SURFACE (one total function selecting an ordered coordinate pair)
--------------------------------------------------------------------------
A single modeled function chooses the initial pair of boundary-marker positions
for an interactive one-dimensional range selector, given the selection direction
and the two candidate coordinate pairs (the axis' current view bounds along the
horizontal axis and along the vertical axis), plus the selector's own degenerate
current span:

  initialMarkers (inp : MarkerSetup) : ℚ × ℚ

The postcondition ``problem_spec_initialMarkers`` has two independent top-level
clauses, one per orientation sub-domain of the ``axis`` binder:

  (HORIZ)  axis = horizontal → result = xViewBounds
  (VERT)   axis = vertical   → result = yViewBounds

WHAT DRIVES THE REJECTS. Each clause pins the result, for its own orientation, to
that orientation's view bounds — as an ORDERED pair (equality of ``ℚ × ℚ`` is
component-wise and order-sensitive). The defect the gold change repairs is that
the initial positions came from the selector's own degenerate span (the abstract
``selectorSpan``, which at set-up time is the origin pair) rather than from the
orientation's current view bounds; drawing markers at that span forces the visible
range to grow to include it, which is exactly the reported regression. So both
clauses are load-bearing and each fixes a distinct sub-domain of ``axis``:

  * ``reject-prepatch-span`` attacks (HORIZ): return the selector's own span rather
    than the view bounds. This IS the pre-patch behavior; on the F2P scenario the
    span is the origin pair while the horizontal view bounds are away from it, so
    the reported positions are wrong and drawing them expands the axis. Refuted at
    the F2P-shaped horizontal input where span=(0,0), xViewBounds=(10,20).
  * ``reject-direction-swap`` attacks (HORIZ): return the OTHER orientation's view
    bounds (horizontal ↦ yViewBounds). Right shape and grounded in *a* bound, but
    the wrong bound for the orientation — refuted at a horizontal input whose x and
    y view bounds differ.
  * ``reject-partial-vertical-span`` attacks (VERT): correct on horizontal but on
    the vertical sub-domain falls back to the degenerate span. Probes that BOTH
    orientations are pinned, not just one — refuted at a vertical input where the
    span differs from yViewBounds.
  * ``reject-direction-swap-vertical`` attacks (VERT) with the SAME swap rival at a
    vertical input (vertical ↦ xViewBounds). Added by the audit: the swap case's
    rationale claimed both sub-domains but only the horizontal one was ever
    witnessed, so the vertical half is now demonstrated instead of asserted.
  * ``reject-order-swap`` attacks (HORIZ) at the ORDER level: return the right
    orientation's bounds but with the two endpoints transposed. Set-equal to the
    bound, but the clause demands the ordered pair — refuted at a horizontal input
    whose two x endpoints differ.

The reject witnesses vary the ``axis`` binder across BOTH orientations (three
horizontal, two vertical) and the value binders (``selectorSpan`` / ``xViewBounds``
/ ``yViewBounds``) across five distinct input points, so a rival mishandling only
one orientation, or only the endpoint order, or only the selector-span-vs-bound
distinction, is caught by a witness built for exactly that sub-domain. Both (VERT)
witnesses matter and are not two spellings of one point: one attacks the vertical
clause with a SPAN fallback, the other with the WRONG VIEW BOUND, so together they
pin that (VERT) names ``yViewBounds`` specifically rather than merely "not the
span".

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
impl's exact elaboration — so a rejection alone attributes nothing to the spec.
Each ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input, stated by unfolding the spec predicate
and the rival impl directly and closing by ``decide``. The carrier is fully
transparent (``ℚ`` literals in ``ℚ × ℚ`` pairs, a two-constructor
``SelectDirection``), so no term needs conditioning and no witness binds a
hypothesis — there is no consistency obligation. Each witness was checked with two
real builds: it ELABORATES against its rival and FAILS against the frozen solution
(``decide`` proves the negation false on gold), so each discriminates rather than
asserting a tautology.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models the imperative set-up step as producing a
freshly-allocated ``List[int]`` under list-predicate permission, and its cases
split into a value-selection family and clauses about the produced list's shape.
This lean carrier is referentially transparent and models only the pure ordered
selection — the single observable component the patch changes — as a total
function returning the chosen ``ℚ × ℚ`` pair. The correspondence and omissions:

  * nagini ``reject-prepatch-other-coords`` (return the unrelated (0,0) extents) ↦
    ``reject-prepatch-span`` here: the abstract ``selectorSpan`` is the model of
    that degenerate span; returning it violates (HORIZ). Same argument, ported.
  * nagini ``reject-direction-swap`` ↦ ``reject-direction-swap`` here (horizontal
    reads the vertical view bounds and vice versa).
  * nagini ``reject-partial-vertical-prepatch`` ↦ ``reject-partial-vertical-span``
    here (correct horizontal, span fallback on vertical). Pins the VERT sub-domain.
  * nagini ``reject-order-swap`` ↦ ``reject-order-swap`` here. On this carrier the
    result is an ordered ``ℚ × ℚ`` pair and equality is component-wise, so a
    transposed pair violates the clause exactly as list order-sensitivity does in
    nagini.
  * nagini ``reject-wrong-length-three`` (a 3-element ``List`` violating the
    ``len == 2`` clause) — VACUOUS here. The result type is a fixed 2-tuple
    ``ℚ × ℚ``; a three-value result cannot be typed at all, so the length is
    enforced by the type system rather than by a spec clause. There is nothing to
    reject and no substitute is fabricated. (Carrier narrowing: the nagini P1
    length clause has no counterpart on a fixed-arity tuple.) DEMONSTRATED during
    the audit rather than asserted: an impl returning
    ``(xViewBounds.1, xViewBounds.2, xViewBounds.1)`` does not elaborate —
    ``Application type mismatch: the argument (…, …) has type ℚ × ℚ but is
    expected to have type ℚ``. The case cannot be written as a REJECT because it
    is rejected by the elaborator, not by the spec, so it would attribute nothing.
  * nagini P0 (``Acc(list_pred(Result()))`` — the freshly-produced list's
    permission) and the FRAME / PERMISSION-MUTATION class — VACUOUS here. Lean is
    referentially transparent: the modeled function returns a bare value pair with
    no heap permission, no aliasing, and no read-only mutable input to frame. The
    nagini manifest already records this class as N/A on its own carrier (tuples
    are immutable, no ``Acc(x,1/2)`` input); it is likewise N/A here, and no
    substitute is fabricated.
  * NON-TERMINATION / divergence — VACUOUS here. ``implementation_initialMarkers``
    is a total Lean ``def``; a diverging implementation cannot be written at all,
    so there is nothing to port. (The nagini sibling carries no ``diverge-*`` case
    either.)
  * nagini ``pos-control-vertical-first-reorder`` (structurally different but
    correct) ↦ ``pos-vertical-first-reorder`` here: the same ``Id.run do`` shape
    with the branch condition flipped to test the vertical orientation first, and
    a proof that closes the reshaped elaboration (theorem statement byte-identical,
    no helper lemma, no axiom, no assumption token). nagini
    ``pos-control-append-grounded`` ↦ ``pos-functional-match`` here: a plain
    functional ``match`` (no ``Id.run do``, no monadic bind) — a genuinely
    different control-flow shape, re-proven directly. nagini
    ``admiss-f2p-horizontal`` ↦ ``admiss-f2p-horizontal`` here: a ``have`` inside
    the frozen proof body discharging the spec predicate at the F2P-shaped
    horizontal input by evaluation, then the frozen obligation closes verbatim.

INDEPENDENT AUDIT (attacks D and E, machine-checked)
----------------------------------------------------
Why no wrong impl can slip past this spec, established structurally rather than by
sampling rivals: the postcondition's two clauses are exhaustive over the ``axis``
binder (``SelectDirection`` has exactly two constructors) and each pins the whole
result to a specific input field, so the spec is a FUNCTIONAL relation — it admits
exactly one result per input. Proved during the audit in a standalone file (build
exit 0), over the frozen spec's own text:

  * ``spec_pins_uniquely (inp) (r) : problem_spec_initialMarkers inp r →
    r = initialMarkers inp`` — any impl satisfying the spec is pointwise equal to
    the gold selection, so no wrong impl can verify. This closes SPEC-TOO-WEAK by
    construction, not by enumeration.
  * ``spec_satisfiable (inp) : problem_spec_initialMarkers inp (initialMarkers inp)``
    — the obligation is satisfiable at EVERY input, so it is nowhere vacuous
    (a stronger statement than the single ground instance
    ``admiss-f2p-horizontal`` checks).
  * ``spec_no_slack (inp) (r₁ r₂) : … → r₁ = r₂`` — no two distinct results
    satisfy the spec at any input, i.e. the spec leaves no freedom to exploit.

Attack D (four NEW wrong impls the battery does not contain: mixed x/y components,
both markers duplicated at the lower endpoint, the axis binder ignored entirely,
and the bounds shifted by the selector span) — none verified, as the uniqueness
theorem predicts. Attack E (four NEW correct reshapes: ``==`` boolean dispatch on
the DecidableEq instance, component-wise ``(b.1, b.2)`` reconstruction, delegation
to the pure helper ``initialMarkers``, and an impl-region helper ``def`` taking the
direction and both bounds) — ALL FOUR verify, so the spec is not over-fit to the
frozen impl's shape. Two of them needed a stronger tactic than a first attempt at
``simp_all``; that was an audit tactic gap, not a spec defect, and is recorded as
such rather than as a SPEC-TOO-STRONG finding.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's job
and this gate ignores it. This bundle has no ``opaque``/``axiom`` pair (the
selection is modeled directly over transparent data — the identity pass-through of
the marker container is an I refinement, not an axiom), so there is no oracle to
echo; the spec is grounded in the input binders via equality.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20676"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The whole gold impl body (impl region). Unique; lies entirely inside
# impl-start / impl-end.
_IMPL_GOLD = (
    "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do\n"
    "  let positions ←\n"
    "    if inp.axis = SelectDirection.horizontal then\n"
    "      pure inp.xViewBounds\n"
    "    else\n"
    "      pure inp.yViewBounds\n"
    "  return positions"
)

# The frozen proof BODY (after `:= by`). Unique; lies entirely inside
# proof-start / proof-end. Only the tactic body is edited by the cases that
# re-prove; the `theorem correct_initialMarkers : …` STATEMENT is untouched.
_PROOF_GOLD = (
    "  intro inp\n"
    "  refine ⟨fun h => ?_, fun h => ?_⟩ <;>\n"
    "    simp only [implementation_initialMarkers, Id.run, h, if_true, pure] <;> rfl"
)


def _impl(body: str) -> str:
    """Full Solution.lean variant with ONLY the impl-region body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


def _impl_proof(body: str, proof: str) -> str:
    """Full variant with the impl body AND the proof body replaced (soundness
    positives whose reshaped impl needs a proof that closes for the new shape;
    the theorem STATEMENT is preserved byte-identically)."""
    return _swap(_impl(body), _PROOF_GOLD, proof)


# ---- witness helper ---------------------------------------------------------
# A reject witness states the spec predicate directly at one concrete transparent
# input and refutes it by `decide` (no opaque term to condition on, so no
# hypothesis is bound and there is no consistency obligation).

def _wit(setup: str) -> str:
    return (
        f"example : ¬ problem_spec_initialMarkers\n"
        f"    {setup}\n"
        f"    (implementation_initialMarkers\n"
        f"      {setup}) := by\n"
        f"  unfold problem_spec_initialMarkers implementation_initialMarkers\n"
        f"  decide\n"
    )


def _setup(axis: str, span: str, xb: str, yb: str) -> str:
    return (
        f"{{ axis := SelectDirection.{axis}, selectorSpan := {span}, "
        f"xViewBounds := {xb}, yViewBounds := {yb} }}"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify (else the spec is over-fit => SPEC-
    # TOO-STRONG). Each keeps the `theorem correct_initialMarkers` statement
    # byte-identical; a proof that closes the new shape is supplied inside the
    # proof region — no helper lemma, no axiom, no assumption token.
    # =====================================================================
    {
        "id": "pos-vertical-first-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Same monadic `Id.run do` shape, but the branch condition is flipped to
        # test the vertical orientation first. Same value on every input, a
        # different control-flow shape. AUDIT NOTE (measured, not assumed): the
        # FROZEN tactic body also closes this reshape (build exit 0), so this
        # case does not depend on the supplied re-proof; the re-proof is kept
        # because it is the honest one for the new branch order (it case-splits
        # the direction rather than relying on `if_true` firing on the flipped
        # condition). The load-bearing content of the case is therefore the
        # VALUE-level claim — the flipped branch order still satisfies both
        # clauses — not the tactic difference.
        "module": _impl_proof(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ := Id.run do\n"
            "  let positions ←\n"
            "    if inp.axis = SelectDirection.vertical then\n"
            "      pure inp.yViewBounds\n"
            "    else\n"
            "      pure inp.xViewBounds\n"
            "  return positions",
            "  intro inp\n"
            "  refine ⟨fun h => ?_, fun h => ?_⟩ <;>\n"
            "    simp only [implementation_initialMarkers, Id.run, bind, pure, h] <;>\n"
            "    cases hax : inp.axis <;> simp_all",
        ),
        "rationale": "a structurally-different but correct impl (the vertical branch "
                     "tested first) must satisfy both clauses (HORIZ) and (VERT); if "
                     "it cannot verify, the spec is over-fit to the exact branch order "
                     "=> SPEC-TOO-STRONG. Proof: the direction is case-split and each "
                     "branch reduces to the correct view bounds — no induction, no "
                     "helper lemma.",
    },
    {
        "id": "pos-functional-match",
        "kind": "soundness",
        "expect": "verify",
        # Plain functional `match` on the direction: no `Id.run do`, no monadic
        # bind, no mutable local — a genuinely different executable shape. Same
        # value on every input. Reproved directly by unfolding the match under the
        # orientation hypothesis.
        "module": _impl_proof(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=\n"
            "  match inp.axis with\n"
            "  | SelectDirection.horizontal => inp.xViewBounds\n"
            "  | SelectDirection.vertical => inp.yViewBounds",
            "  intro inp\n"
            "  refine ⟨fun h => ?_, fun h => ?_⟩ <;>\n"
            "    simp only [implementation_initialMarkers, h]",
        ),
        "rationale": "a correct point-free reshape (a plain functional `match`, no "
                     "monadic wrapper) must verify (else SPEC-TOO-STRONG). Proof: "
                     "under each orientation hypothesis the `match` reduces to that "
                     "orientation's view bounds and the clause closes by `simp only`.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at a normal, F2P-shaped input rather than only provable in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the modeled
    # behavior is total), so the nagini precondition-admission probe has no binder
    # to attack here; the honest analogue discharges the spec predicate at a ground
    # input matching the F2P scenario (horizontal selector, x view bounds (10,20))
    # by evaluation, inside the proof region, alongside the frozen obligation. If
    # that ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input shape the F2P exercises. Nothing is
    # assumed: no new declaration, the theorem statement is byte-identical, and the
    # ground instance is a `have` inside the existing tactic body.
    # =====================================================================
    {
        "id": "admiss-f2p-horizontal",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_GOLD,
            "  have _ground : problem_spec_initialMarkers\n"
            "      { axis := SelectDirection.horizontal, selectorSpan := (0, 0),\n"
            "        xViewBounds := (10, 20), yViewBounds := (10, 30) }\n"
            "      (implementation_initialMarkers\n"
            "        { axis := SelectDirection.horizontal, selectorSpan := (0, 0),\n"
            "          xViewBounds := (10, 20), yViewBounds := (10, 30) }) := by\n"
            "    unfold problem_spec_initialMarkers implementation_initialMarkers\n"
            "    decide\n"
            "  intro inp\n"
            "  refine ⟨fun h => ?_, fun h => ?_⟩ <;>\n"
            "    simp only [implementation_initialMarkers, Id.run, h, if_true, pure] <;> rfl",
        ),
        "rationale": "the selection obligation is discharged at a ground F2P-shaped "
                     "input (horizontal selector, x view bounds (10,20), degenerate "
                     "span (0,0)) by evaluation, then the frozen obligation is closed "
                     "verbatim. Verifies (else the spec is unsatisfiable at the normal "
                     "F2P input, the analogue of PRECOND-TOO-STRONG).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the frozen
    # spec that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival is a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "reject-prepatch-span",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH: return the selector's own degenerate span rather than the
        # orientation's view bounds.
        "module": _impl(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=\n"
            "  inp.selectorSpan",
        ),
        "refinement": "this IS the pre-patch behavior: the initial marker positions are "
                      "read from the selector's own current span, which at set-up time "
                      "is the degenerate origin pair. On the F2P scenario the horizontal "
                      "view bounds are away from the origin, so the reported positions "
                      "are the origin pair and drawing the markers there forces the "
                      "visible range to grow to include the origin — the F2P assertion "
                      "that the positions equal the view bounds (and that the view is "
                      "undisturbed) FAILS. It does NOT resolve.",
        "rationale": "REJECT from clause (HORIZ) (axis = horizontal → result = "
                     "xViewBounds): at a horizontal input whose span differs from the x "
                     "view bounds the rival returns the span while the spec requires the "
                     "view bounds. If it verified => SPEC-TOO-WEAK (admits the pre-patch "
                     "selection).",
        "witness": _wit(_setup("horizontal", "(0, 0)", "(10, 20)", "(10, 30)")),
    },
    {
        "id": "reject-direction-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG: horizontal selector reads the vertical view bounds and vice versa.
        "module": _impl(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=\n"
            "  match inp.axis with\n"
            "  | SelectDirection.horizontal => inp.yViewBounds\n"
            "  | SelectDirection.vertical => inp.xViewBounds",
        ),
        "refinement": "a faithful patch that supplies the vertical view bounds to a "
                      "horizontal selector places the marker lines at y-range "
                      "coordinates that lie partly outside the x view range, forcing the "
                      "x axis to expand, and the reported positions equal the y bounds "
                      "rather than the x bounds — the F2P assertion (positions equal the "
                      "horizontal view bounds) FAILS. It does NOT resolve.",
        "rationale": "REJECT from clause (HORIZ) on the horizontal sub-domain (result = "
                     "yViewBounds ≠ xViewBounds); a verify here is SPEC-TOO-WEAK (the "
                     "clause would not bind the orientation to its own bound). Refuted at "
                     "a horizontal input whose x and y view bounds differ. This rival ALSO "
                     "violates (VERT) symmetrically, which the companion case "
                     "`reject-direction-swap-vertical` demonstrates with its own witness "
                     "rather than leaving it as an unbacked claim here.",
        "witness": _wit(_setup("horizontal", "(1, 2)", "(10, 20)", "(10, 30)")),
    },
    {
        # AUDIT ADDITION. The direction-swap rival's rationale asserted a
        # violation on BOTH sub-domains, but the battery only ever refuted it on
        # the horizontal one; the (VERT) half was prose the manifest never
        # demonstrated. The same rival is re-attacked here at a VERTICAL input,
        # where it returns xViewBounds while (VERT) demands yViewBounds. Built by
        # hand during the audit: the witness ELABORATES against the rival (exit 0)
        # and FAILS on the frozen solution by semantic refutation (exit 1,
        # "`decide` proved that the proposition ¬(...) is false"), so it
        # discriminates. This makes the vertical half of the swap claim
        # machine-checked instead of asserted, and it is the only reject case that
        # pins (VERT) against a rival grounded in the WRONG BOUND rather than in
        # the selector span.
        "id": "reject-direction-swap-vertical",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=\n"
            "  match inp.axis with\n"
            "  | SelectDirection.horizontal => inp.yViewBounds\n"
            "  | SelectDirection.vertical => inp.xViewBounds",
        ),
        "refinement": "a faithful patch that supplies the horizontal view bounds to a "
                      "vertical selector places the marker lines at x-range coordinates "
                      "that lie partly outside the y view range, forcing the vertical axis "
                      "to expand, and the reported positions equal the x bounds rather "
                      "than the y bounds — the F2P[vertical] assertion (positions equal "
                      "the vertical view bounds) FAILS. It does NOT resolve.",
        "rationale": "REJECT from clause (VERT) (axis = vertical → result = yViewBounds): "
                     "at a vertical input whose x and y view bounds differ the rival "
                     "returns the x bounds. A verify here is SPEC-TOO-WEAK (the vertical "
                     "clause would not bind the orientation to its own bound). Distinct "
                     "from `reject-partial-vertical-span`, which attacks (VERT) with a "
                     "span fallback: this one is grounded in a real view bound, so it "
                     "probes that (VERT) names the *y* bound specifically.",
        "witness": _wit(_setup("vertical", "(1, 2)", "(10, 20)", "(10, 30)")),
    },
    {
        "id": "reject-partial-vertical-span",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on HORIZONTAL, but on the VERTICAL sub-domain falls back to the
        # degenerate span. Passes the horizontal clause; diverges on vertical.
        "module": _impl(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=\n"
            "  match inp.axis with\n"
            "  | SelectDirection.horizontal => inp.xViewBounds\n"
            "  | SelectDirection.vertical => inp.selectorSpan",
        ),
        "refinement": "this fixes only the horizontal orientation but leaves the "
                      "vertical branch reading the degenerate span. For a vertical "
                      "selector the span (the origin pair at set-up) sits outside the y "
                      "view range, so drawing the markers there expands the y axis and "
                      "the reported positions equal the span rather than the y view "
                      "bounds — the F2P[vertical] assertion FAILS even though "
                      "F2P[horizontal] passes. It does NOT resolve both orientations.",
        "rationale": "REJECT from clause (VERT) (axis = vertical → result = yViewBounds) "
                     "on the vertical sub-domain; a verify here is SPEC-TOO-WEAK (only "
                     "one orientation pinned). Refuted at a vertical input whose span "
                     "differs from the y view bounds — the sub-domain the horizontal "
                     "rivals never touch.",
        "witness": _wit(_setup("vertical", "(0, 0)", "(10, 20)", "(10, 30)")),
    },
    {
        "id": "reject-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG ORDER: selects the right orientation's bounds but transposes the
        # two endpoints (upper first, lower second).
        "module": _impl(
            "def implementation_initialMarkers (inp : MarkerSetup) : ℚ × ℚ :=\n"
            "  match inp.axis with\n"
            "  | SelectDirection.horizontal => (inp.xViewBounds.2, inp.xViewBounds.1)\n"
            "  | SelectDirection.vertical => (inp.yViewBounds.2, inp.yViewBounds.1)",
        ),
        "refinement": "the gold patch supplies the view bounds as the ordered pair "
                      "(lower, upper); the marker container reports the positions back "
                      "in that order. Transposing to (upper, lower) makes the reported "
                      "positions the reversed pair, so the F2P assertion that the "
                      "positions equal the view-bounds list (an order-sensitive "
                      "sequence equality) FAILS. It does NOT resolve.",
        "rationale": "REJECT from the component-wise, order-sensitive equality in clause "
                     "(HORIZ) (result = xViewBounds as an ordered pair): set-equality is "
                     "not enough. A verify here would mean the clause does not pin "
                     "endpoint order (SPEC-TOO-WEAK). Refuted at a horizontal input "
                     "whose two x endpoints differ.",
        "witness": _wit(_setup("horizontal", "(1, 2)", "(2, 8)", "(5, 9)")),
    },
]
