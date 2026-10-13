"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25287 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect:"reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The two batteries look
different because the two carriers do. The nagini bundle contracts TWO
byte-identical functions ``offset_color_primary`` / ``offset_color_secondary``,
each over TWO read-only ``List[int]`` colour inputs, with SIX ensures clauses:
two half-permission FRAME clauses per input, a fresh-result ownership clause, a
grounded oracle equality, and the two branch-pinning ``Implies`` clauses (sentinel
⇒ base, ordinary ⇒ label). It models a colour as the materialised list of code
points, so the ``'inherit'`` sentinel is itself a concrete colour value (the code
points of "inherit").

This Lean bundle models only the purely-functional core, and its carrier is much
tighter. A colour is an OPAQUE token ``Color`` (no constructors, no literals):
only which of the two candidate colours reaches the offset text matters, never
its representation. The label-colour setting is ``Option Color``: an explicit
choice is ``some c`` and the defer-to-ticks sentinel (matplotlib's ``'inherit'``)
is the ABSENCE of a value, ``none`` — NOT a concrete colour token. Both axes
resolve the colour identically, so there are TWO obligations
(``correct_horizOffsetTextColor`` / ``correct_vertOffsetTextColor``) with the
same single-clause spec over the same two binders:

    result = labelColor.getD tickColor

so ``tickColor : Color`` and ``labelColor : Option Color`` are the only inputs.
Every nagini clause that lived on the mutable/permission carrier has NO
counterpart here; the mapping of each nagini case to its Lean port (or its
principled omission) is in the module ``assessment``.

DEFENDED SURFACE (one clause per obligation, two obligations). The result is
fully pinned to ``labelColor.getD tickColor``. There are no independent top-level
conjuncts to attack separately; the single combining operation ``getD`` has two
arms:

  * the SENTINEL arm (``labelColor = none`` ⇒ fall back to ``tickColor``);
  * the EXPLICIT arm (``labelColor = some c`` ⇒ take ``c``).

CARRIER SHAPE — BOTH arms of ``getD`` are attackable, and both are attacked.
``Color`` is an ``opaque`` type with no constructors, so no LITERAL colour token
can be written down. That bounds how a rival is spelled, but it does NOT make
either arm safe:

  * the EXPLICIT arm (``labelColor = some c``) is attacked by returning
    ``tickColor`` there — the pre-fix behaviour (``weak-ignore-labelcolor``),
    which is simultaneously nagini's U1 (base-always) AND nagini's U3 (inverted
    sentinel, which on an absence-modeled sentinel sends every arm to
    ``tickColor``); those two coincide on this carrier.

  * the SENTINEL arm (``labelColor = none``) is attacked by returning a colour
    that is NOT the tick colour (``weak-sentinel-not-tickcolor``), the port of
    nagini's U2 (label-always / drop the fallback). An earlier revision of this
    manifest asserted the sentinel arm was "carrier-forced correct" because
    ``tickColor`` is the only ``Color``-typed local in scope there. That is
    FALSE, and the case below is the machine-checked refutation of it: a
    ``noncomputable def`` can name a further inhabitant of an opaque type
    without any constructor, via ``Classical.choice`` on the ``Nonempty Color``
    instance that ``tickColor`` itself witnesses. The resulting term is a
    genuine ``Color`` the spec does not permit on that arm, it is NOT
    definitionally ``tickColor`` (so the rival is observably wrong, not merely
    reshaped), and the disequality that says so is satisfiable rather than
    derivable — an opaque carrier cannot prove its own inhabitants equal. So
    both branch pins nagini enforced with two ``Implies`` clauses are enforced
    here too, one rival each.

``noncomputable`` is required on that rival's ``def``s (the code generator
rejects ``Classical.choice``) and is admissible: it is a compilation attribute,
not an assumption — it introduces no ``axiom``, no ``sorry``, and no new
declaration, and ``variant_scope`` accepts it with both obligation statements
byte-identical.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini F1) — VACUOUS. Lean is referentially
    transparent: an input carries no heap permission, there is no read-only
    half-permission to overwrite and no aliasing to exploit. The nagini
    "item-assign into a read-only input" rival is expressible only where the
    input is a mutable list with fractional permission. No substitute is
    fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to ``labelColor.getD tickColor``, a term built only from the
    inputs. There is no opaque answer key to echo; any result equal to it IS the
    correct colour by construction. In its place the battery carries an
    honest cheapest-implementation POSITIVE CONTROL that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, with rivals on BOTH arms (see carrier
    shape): ``weak-ignore-labelcolor`` is correct on the sentinel arm and wrong
    exactly on the explicit arm; ``weak-sentinel-not-tickcolor`` is correct on
    the explicit arm and wrong exactly on the sentinel arm. Between them every
    arm of the single combining operation is pinned by a rival that must be
    rejected, which is the port of nagini's two ``Implies`` branch pins.
    ``weak-explicit-foreign-color`` then pins the explicit arm POSITIVELY: it is
    not enough that the result differ from ``tickColor`` there, it must be the
    label colour ``c`` itself.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class, and NOT
    shippable as a reject case. The frozen solution sets no
    ``loom.semantics.termination`` option at all (it is plain Lean 4 + Mathlib,
    with no recursion anywhere in the modeled behaviour), so there is no
    termination obligation for a rival to fail. A rival that makes the impl
    non-reducing — ``partial def`` with a self-call — was BUILT and measured: the
    module is in scope and does fail to verify (exit 1), but a ``partial def``
    has no equation lemmas, so the witness cannot get past
    ``unfold implementation_horizOffsetTextColor`` (measured: exit 1, "Tactic
    `unfold` failed to unfold"). With no provable witness the rejection would
    attribute nothing to the spec, so the case is deliberately NOT shipped and
    the class is recorded as an open hole in the spec rather than as complete.

NAGINI CASE LEDGER (every source case, ported or dropped with a reason):

  * P1 branch-reorder positive        -> ``pos-match-arms-reordered``.
  * P2 single-assignment positive     -> covered by ``pos-getd-direct`` (the
    combining term returned directly) and, in the direction that one cannot
    reach, by ``pos-elim-reshape``: a correct impl that resolves the setting via
    ``Option.elim`` rather than via the spec's own ``getD``, so it agrees with
    the clause VALUE-wise instead of by returning the clause's right-hand side
    verbatim.
  * P3 echo-honest positive           -> folded into ``pos-getd-direct``: the
    spec is GROUNDED (``result`` pinned to a term over the inputs), so there is
    no opaque answer key to echo and no WRONG echo to exhibit; the honest
    cheapest impl IS the echo control.
  * P4 admissibility (self-call)      -> ``admiss-f2p-shaped``, restated as
    ground instances at both F2P scenarios (the frozen theorems carry no
    precondition hypothesis, so there is no binder to drive).
  * F1 frame/permission mutation      -> DROPPED, inexpressible. Lean is
    referentially transparent: an input carries no heap permission, so there is
    no read-only half-permission to overwrite and no aliasing to exploit. The
    rival needs a mutable list with fractional permission to exist at all.
  * U1 base-always (pre-patch bug)    -> ``weak-ignore-labelcolor``.
  * U2 label-always (drop fallback)   -> ``weak-sentinel-not-tickcolor``. Ported,
    NOT dropped: an earlier revision omitted it on the false ground that the
    sentinel arm was carrier-forced correct. See CARRIER SHAPE.
  * U3 inverted sentinel              -> coincides with U1 on this carrier and is
    covered by ``weak-ignore-labelcolor``: with the sentinel modeled as an
    ABSENCE rather than as a concrete colour value, inverting the comparison
    sends every arm to ``tickColor``, which is exactly U1's behaviour. (On
    nagini the two differ only because ``'inherit'`` is itself a materialised
    colour there, so the inverted impl can return the sentinel's own code
    points; there is no such token here.)
  * AXIOM_TESTS                       -> empty in both.

CASES THIS PORT ADDS beyond the nagini ledger (the nagini carrier had no analogue
to drop, so they are not omissions but coverage this carrier makes reachable):

  * ``pos-elim-reshape``            — a correct impl through a different
    eliminator, distinguishing "agrees value-wise" from "returns the clause's own
    right-hand side".
  * ``weak-explicit-foreign-color`` — the explicit arm pinned POSITIVELY (result
    ``= c``, not merely ``≠ tickColor``). Nagini needed no such rival because
    ``'inherit'`` is a materialised colour there, so its ordinary-branch
    ``Implies`` already compared against ``label_color`` itself.

WITNESS. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``cases labelColor <;> rfl``) is
tuned to the frozen form — so a rejection alone attributes nothing to the spec.
Each ``expect="reject"`` case therefore carries a Lean snippet refuting the spec
predicate at one concrete input, checked to HOLD of its rival and to FAIL on the
frozen solution, for BOTH obligations.

CONDITIONING ON THE CARRIER. ``Color`` is opaque, so no literal input makes the
spec ``decide``-able: the colour terms have no computable value. Each refutation
is therefore stated at a point described by HYPOTHESIS — a single weak
disequality — rather than at a literal:

  * ``weak-ignore-labelcolor``: ``tickColor ≠ c``. Whenever the tick-mark colour
    differs from the explicit label colour, the rival's answer (the tick colour)
    differs from the spec's (the label colour).
  * ``weak-sentinel-not-tickcolor``: the colour the rival picks on the sentinel
    ``≠ tickColor``. Whenever they differ, the rival's answer differs from the
    fallback the spec demands.

  * ``weak-explicit-foreign-color``: the colour the rival picks on the explicit
    arm ``≠ c``. Whenever they differ, the rival's answer differs from the label
    colour the spec demands there.

Each is exactly the sub-domain where its rival is wrong. Each carries a SINGLE
hypothesis (one disequality over opaque colours), so the assumptions are jointly
satisfiable — nothing forces ``Color`` to be a subsingleton, and no tactic can
derive ``False`` from a disequality between two opaque inhabitants — which is
what the gate's consistency probe confirms.

WHY THESE WITNESSES DISCRIMINATE, and how it was checked rather than argued. Each
witness closes with ``simp`` then ``exact h``. On the RIVAL, ``simp`` normalises
the goal to the very disequality the hypothesis states, and ``exact h`` closes it.
On the FROZEN solution ``simp`` PROVES the underlying equation, so the goal
collapses to ``False`` and ``exact h`` fails with ``h has type ... but is expected
to have type False``. That gold-side error therefore reports what ``simp``
established about the impl, and it TRACKS THE CLAIM in both directions — verified
by building, for every reject case, all four corners of the claim/subject square:

  * claim NEGATED (the shipped witness): gold fails, rival succeeds;
  * claim FLIPPED (assert the spec HOLDS, ``¬`` dropped, tactic body ending at
    ``simp``): gold SUCCEEDS, rival fails with ``unsolved goals`` displaying the
    concrete open equation.

Gold's exit code flips when the claim flips, so it carries information about the
claim and no forged witness asserting gold is CORRECT at these points could be
recorded as a rejection. Additionally — the check that separates a real refutation
from a mere tactic mismatch on this backend — each witness was built against the
CORRECT reshapes this battery ships as positives, and against the other rival's
impl: it fails on every one of them, and succeeds only against the specific rival
whose arm it names.

AXIOM lane: EMPTY here. The bundle declares one ``opaque`` leaf (the colour
token) and consumes no ``axiom``; the changed operation is a direct two-way
conditional selection between two already-available colour values. The nagini
``AXIOM_TESTS`` were also empty; dropped.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25287"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap_both(src, old, new):
    """Replace BOTH occurrences of the impl-region body (one per identical site).

    The two functions resolve the offset-text colour identically, so their gold
    impl bodies are byte-identical: the gold body appears exactly twice, each
    strictly inside an ``-- impl-start`` / ``-- impl-end`` region. Replacing both
    keeps ``same_spec`` (the spec view elides impl) while applying the attack /
    control symmetrically to both sites, matching the two F2P tests
    (test_xaxis_offsetText_color / test_yaxis_offsetText_color)."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 2:
        raise AssertionError(
            f"expected the gold body twice (one per site), "
            f"found {src.count(old)}: {old!r}")
    return src.replace(old, new)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (verified at load) --------------------------------------
# The whole gold impl body, identical in both functions, strictly INSIDE each
# impl region.
_GOLD_BODY = (
    "  let mut chosen := tickColor\n"
    "  match labelColor with\n"
    "  | none   => chosen := tickColor\n"
    "  | some c => chosen := c\n"
    "  return chosen\n"
)

# The horizontal proof's first `unfold` line (unique in the file); used to stage
# the admissibility ground instances inside the proof body without touching the
# obligation statement.
_H_UNFOLD = (
    "  unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor\n"
)

# The vertical proof's `unfold` line (also unique); the admissibility case stages
# its ground instances at BOTH obligations, not just the horizontal one — the two
# F2P tests observe the two axes independently, so a probe that discharges only
# one leaves the other's satisfiability at the F2P inputs unmeasured.
_V_UNFOLD = (
    "  unfold problem_spec_vertOffsetTextColor implementation_vertOffsetTextColor\n"
)


def _f2p_haves(prefix):
    """Ground instances of one obligation at the two F2P-shaped inputs.

    An explicit label colour (`some c`) and the defer-to-ticks sentinel (`none`),
    for arbitrary opaque colours, each discharged BY EVALUATION (`rfl`) as an
    anonymous `have` before the frozen obligation is closed verbatim."""
    return (f"  have _f2p_explicit : ∀ tc c : Color,\n"
            f"      problem_spec_{prefix}OffsetTextColor tc (some c)\n"
            f"        (implementation_{prefix}OffsetTextColor tc (some c)) := "
            "fun _ _ => rfl\n"
            f"  have _f2p_sentinel : ∀ tc : Color,\n"
            f"      problem_spec_{prefix}OffsetTextColor tc none\n"
            f"        (implementation_{prefix}OffsetTextColor tc none) := "
            "fun _ => rfl\n")


def _noncomputable(src):
    """Mark BOTH impl `def`s `noncomputable`.

    Needed only by the sentinel-arm rival, whose body names a further inhabitant
    of the opaque colour type through `Classical.choice`: the code generator
    refuses to compile that (`Classical.choice` has no executable content), so
    without this the file fails with a codegen error rather than with the
    spec-level refutation the case is about — a rejection for a TOOLING reason,
    which attributes nothing to the spec.

    Admissible: `noncomputable` is a compilation attribute, not an assumption. It
    introduces no `axiom`, no `sorry` and no new declaration, it leaves both
    `theorem correct_*` STATEMENTS byte-identical, and the `def` keyword line it
    edits sits strictly inside an `-- impl-start` / `-- impl-end` region, so the
    spec view (which elides impl) is untouched and `same_spec` still holds."""
    for name in ("implementation_horizOffsetTextColor",
                 "implementation_vertOffsetTextColor"):
        src = _swap(src, f"def {name}", f"noncomputable def {name}")
    return src


# A further inhabitant of the opaque colour type, named WITHOUT any constructor:
# `tickColor` witnesses `Nonempty Color`, and `Classical.choice` on that instance
# yields a `Color` term. Nothing proves it equal to `tickColor` (an opaque type
# cannot prove its own inhabitants equal), which is exactly what makes it usable
# as the "some colour other than the tick colour" the sentinel arm forbids.
_OTHER_COLOR = "Classical.choice (⟨tickColor⟩ : Nonempty Color)"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps both theorem STATEMENTs byte-identical; the reshapes preserve the
    # definitional form so the frozen tactic body (`cases labelColor <;> rfl`)
    # still closes — no helper lemma, no axiom, no assumption token.
    # =====================================================================
    {
        "id": "pos-getd-direct",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: return the combining term directly,
        # collapsing the mutable-local `match` into a single expression. Same
        # value on every input, so `result = labelColor.getD tickColor` still
        # holds. Doubles as the cheapest-honest control: the spec is GROUNDED (no
        # answer key to echo), so this honest impl IS the cheapest verifier.
        "module": _swap_both(
            _BASE, _GOLD_BODY,
            "  return labelColor.getD tickColor\n",
        ),
        "rationale": "the single modeled clause is reshaped by returning the "
                     "combining term `labelColor.getD tickColor` directly, "
                     "collapsing the mutable-local `match` into one expression. "
                     "The value is identical on every input (sentinel arm ⇒ "
                     "tickColor, explicit arm ⇒ the label colour), so `result = "
                     "labelColor.getD tickColor` still holds for both obligations. "
                     "Must verify, else the clause is SPEC-TOO-STRONG (over-fit to "
                     "the mutate-local control shape). Doubles as the "
                     "cheapest-honest / echo control: the spec is grounded in the "
                     "inputs, so no wrong oracle echo could satisfy it. Proof: "
                     "frozen tactic body retained (`cases labelColor`; each arm "
                     "`rfl`).",
    },
    {
        "id": "pos-match-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: present the explicit-colour arm
        # first and the sentinel fallback second (mirror-image control flow).
        # Same selection; the `match` still reduces definitionally per arm, so the
        # frozen `cases labelColor <;> rfl` proof closes.
        "module": _swap_both(
            _BASE, _GOLD_BODY,
            "  let mut chosen := tickColor\n"
            "  match labelColor with\n"
            "  | some c => chosen := c\n"
            "  | none   => chosen := tickColor\n"
            "  return chosen\n",
        ),
        "rationale": "a correct impl with the two `match` arms in the opposite "
                     "order (explicit-colour arm first, sentinel fallback second) "
                     "must verify; if not, the spec is over-fit to one arm "
                     "ordering => SPEC-TOO-STRONG. Both arm-paths still produce "
                     "`labelColor.getD tickColor` for both obligations. Proof: "
                     "frozen tactic body retained (`cases labelColor`; each arm "
                     "`rfl`). Ports nagini's branch-reorder soundness positive.",
    },

    {
        "id": "pos-elim-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT, and NOT spelled with the spec's own
        # combinator: resolve the setting with `Option.elim` (fallback first,
        # `id` on the explicit arm) instead of `getD`. `pos-getd-direct` returns
        # the spec's own right-hand side verbatim, so on its own it cannot tell an
        # honest reshape from the spec being over-fit to the term `getD` — this
        # one reaches the same value through a different eliminator.
        "module": _swap_both(
            _BASE, _GOLD_BODY,
            "  return labelColor.elim tickColor id\n",
        ),
        "rationale": "a correct impl that resolves the setting through a DIFFERENT "
                     "eliminator (`Option.elim tickColor id`) rather than through "
                     "the spec's own `getD` must verify. This is the reshape "
                     "`pos-getd-direct` cannot provide: that one returns the "
                     "spec's right-hand side verbatim, so it would verify even if "
                     "the clause were over-fit to the literal term `getD`, whereas "
                     "this one agrees only VALUE-wise (sentinel arm ⇒ tickColor, "
                     "explicit arm ⇒ the label colour). If it were rejected the "
                     "clause would be over-fit to one spelling of the combining "
                     "operation => SPEC-TOO-STRONG. Proof: frozen tactic body "
                     "retained (`cases labelColor`; each arm `rfl`).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped inputs rather than only in the abstract. The
    # frozen theorems carry NO precondition hypothesis (the modeled behavior is
    # total, so `∀` is unguarded), so nagini's precondition-admission probe has no
    # binder to attack here; the honest analogue discharges the spec predicate at
    # BOTH F2P scenarios — an explicit label colour (`some c`) and the
    # defer-to-ticks sentinel (`none`) — as anonymous `have`s, then closes the
    # frozen obligation verbatim. Ports nagini's admissibility case.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge BOTH obligations at the F2P-shaped inputs (an explicit label
        # colour, and the defer-to-ticks sentinel) for arbitrary opaque colours by
        # `rfl`, then close each frozen obligation verbatim. Nothing is assumed: no
        # new declaration, both statements byte-identical, ground instances are
        # anonymous `have`s in the existing tactic bodies.
        "module": _swap(
            _swap(_BASE, _H_UNFOLD, _f2p_haves("horiz") + _H_UNFOLD),
            _V_UNFOLD, _f2p_haves("vert") + _V_UNFOLD,
        ),
        "rationale": "BOTH obligations are discharged at both F2P scenarios — an "
                     "explicit label colour (`some c`, the 'set labelcolor to blue "
                     "⇒ offset text is blue' case) and the defer-to-ticks sentinel "
                     "(`none`, the 'labelcolor inherit ⇒ offset text follows the "
                     "tick colour' case) — for arbitrary opaque colours by `rfl`, "
                     "then the frozen obligation is closed verbatim. Verifies (else "
                     "the modeled behavior is unsatisfiable at exactly the inputs "
                     "the F2P exercises — the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, both theorem "
                     "statements byte-identical, the ground instances are anonymous "
                     "`have`s inside the existing tactic body. Ports nagini's "
                     "admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rival — the EXPLICIT arm, negatively. It MUST be
    # rejected. Carries (a) the refinement argument that its faithful real patch
    # would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break, and (b) a refutation witness
    # conditioning on the opaque colour at one concrete input, for both sites.
    # =====================================================================
    {
        "id": "weak-ignore-labelcolor",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior: colour the offset text from the tick-mark colour
        # unconditionally, ignoring the label-colour setting. Correct on the
        # sentinel arm, wrong whenever an explicit label colour is set.
        "module": _swap_both(
            _BASE, _GOLD_BODY,
            "  return tickColor\n",
        ),
        "refinement": "this IS the pre-fix behavior: the offset text is coloured "
                      "from the tick-mark colour setting unconditionally, never "
                      "consulting the tick-LABEL colour setting. The F2P asserts "
                      "that after setting the tick-label colour to an explicit "
                      "value the offset text takes THAT value (not the tick-mark "
                      "colour); this rival keeps it at the tick-mark colour, so the "
                      "faithful real patch (the unpatched code) would NOT resolve. "
                      "It is also the faithful port of nagini's inverted-sentinel "
                      "rival: with the sentinel modeled as an absence, inverting "
                      "the comparison sends every arm to the tick-mark colour, "
                      "which is this same behavior.",
        "rationale": "REJECT from the single modeled clause on its EXPLICIT arm: "
                     "with `labelColor = some c` the spec pins the result to `c` "
                     "while the rival returns `tickColor`, distinct opaque colours. "
                     "This rival is CORRECT on the sentinel arm, so it is a "
                     "partial-domain rival, not the only expressible one: the "
                     "sentinel arm is attacked separately by "
                     "`weak-sentinel-not-tickcolor` and the explicit arm is pinned "
                     "positively by `weak-explicit-foreign-color`. It "
                     "attacks BOTH obligations symmetrically (both impls edited). "
                     "If it verified => SPEC-TOO-WEAK (the explicit label colour is "
                     "not pinned — the exact bug). Binders exercised: `tickColor` "
                     "and `labelColor` both appear in the refutation "
                     "(disequality between the tick colour and the explicit label "
                     "colour at `labelColor = some c`).",
        "witness": (
            "-- Refuted at an explicit label colour, for BOTH sites. `Color` is\n"
            "-- opaque, so no literal input decides the goal; condition on the\n"
            "-- carrier instead. The single hypothesis `tickColor ≠ c` is\n"
            "-- satisfiable (nothing forces Color to be a subsingleton) and states\n"
            "-- exactly the sub-domain where the rival is wrong: whenever the\n"
            "-- tick-mark colour differs from the explicit label colour, the\n"
            "-- rival's answer (tickColor) differs from the spec's (the label\n"
            "-- colour c).\n"
            "example (tickColor c : Color) (h : tickColor ≠ c) :\n"
            "    ¬ problem_spec_horizOffsetTextColor tickColor (some c)\n"
            "        (implementation_horizOffsetTextColor tickColor (some c)) := by\n"
            "  unfold problem_spec_horizOffsetTextColor "
            "implementation_horizOffsetTextColor\n"
            "  simp\n"
            "  exact h\n"
            "example (tickColor c : Color) (h : tickColor ≠ c) :\n"
            "    ¬ problem_spec_vertOffsetTextColor tickColor (some c)\n"
            "        (implementation_vertOffsetTextColor tickColor (some c)) := by\n"
            "  unfold problem_spec_vertOffsetTextColor "
            "implementation_vertOffsetTextColor\n"
            "  simp\n"
            "  exact h\n"
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rival — the SENTINEL arm. Port of nagini's U2
    # (label-always / drop the sentinel fallback). This is the arm an earlier
    # revision of this manifest declared unattackable ("the only Color in scope
    # is tickColor"); it is attackable, and this case is the machine-checked
    # refutation of that claim. See the CARRIER SHAPE note.
    # =====================================================================
    {
        "id": "weak-sentinel-not-tickcolor",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the defer-to-ticks fallback: on the sentinel the offset text takes
        # some colour that is NOT the tick colour. Correct on the explicit arm
        # (returns `c`), wrong exactly on the sentinel arm, where the spec pins
        # the result to `tickColor`.
        "module": _noncomputable(_swap_both(
            _BASE, _GOLD_BODY,
            "  match labelColor with\n"
            f"  | none   => return {_OTHER_COLOR}\n"
            "  | some c => return c\n",
        )),
        "refinement": "this is the opposite half-bug from the pre-fix behavior: "
                      "the label-colour setting is consulted, but its "
                      "defer-to-ticks sentinel is not honoured — on the sentinel "
                      "the offset text is given a colour other than the tick-mark "
                      "colour instead of falling back to it. The F2P's second "
                      "scenario fixes the tick-mark colour and leaves the "
                      "label-colour setting at its defer-to-ticks sentinel, then "
                      "asserts the offset text comes out the tick-mark colour; "
                      "this rival gives it a different colour there, so a faithful "
                      "patch of this shape would NOT resolve. Ports nagini's "
                      "label-always rival, whose sentinel sub-domain failure was "
                      "caught by Implies(label == inherit, Result == base).",
        "rationale": "REJECT from the single modeled clause on its SENTINEL arm: "
                     "with `labelColor = none` the spec pins the result to "
                     "`tickColor` while the rival returns a different colour "
                     "token. The rival is correct on the explicit arm, so this is "
                     "a genuine partial-domain rival complementary to "
                     "`weak-ignore-labelcolor`, and between them BOTH arms of "
                     "`getD` are pinned. It attacks BOTH obligations symmetrically "
                     "(both impls edited). If it verified => SPEC-TOO-WEAK (the "
                     "defer-to-ticks fallback would be unenforced — the offset "
                     "text could be coloured arbitrarily whenever the label-colour "
                     "setting expresses no opinion). The rival is observably wrong "
                     "and not merely reshaped: its sentinel-arm result is not "
                     "definitionally `tickColor`, which is what the witness "
                     "establishes. Binders exercised: `labelColor` at `none` (the "
                     "arm the other rival leaves correct) and `tickColor` as the "
                     "value the fallback must produce.",
        "witness": (
            "-- Refuted on the SENTINEL arm, for BOTH sites. `Color` is opaque, so\n"
            "-- no literal input decides the goal; condition on the carrier. The\n"
            "-- single hypothesis says the colour the rival picks on the sentinel\n"
            "-- differs from the tick colour the spec demands there. It is\n"
            "-- SATISFIABLE, not derivable: an opaque type cannot prove its own\n"
            "-- inhabitants equal, so nothing forces `Classical.choice` on\n"
            "-- `Nonempty Color` to land on `tickColor` (the gate's consistency\n"
            "-- probe confirms `False` does not follow). Under that hypothesis the\n"
            "-- rival's answer differs from the spec's `none.getD tickColor =\n"
            "-- tickColor` — exactly the sub-domain where the rival is wrong.\n"
            "example (tickColor : Color)\n"
            f"    (h : {_OTHER_COLOR} ≠ tickColor) :\n"
            "    ¬ problem_spec_horizOffsetTextColor tickColor none\n"
            "        (implementation_horizOffsetTextColor tickColor none) := by\n"
            "  unfold problem_spec_horizOffsetTextColor "
            "implementation_horizOffsetTextColor\n"
            "  simp\n"
            "  exact h\n"
            "example (tickColor : Color)\n"
            f"    (h : {_OTHER_COLOR} ≠ tickColor) :\n"
            "    ¬ problem_spec_vertOffsetTextColor tickColor none\n"
            "        (implementation_vertOffsetTextColor tickColor none) := by\n"
            "  unfold problem_spec_vertOffsetTextColor "
            "implementation_vertOffsetTextColor\n"
            "  simp\n"
            "  exact h\n"
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rival — the EXPLICIT arm, pinned POSITIVELY.
    # `weak-ignore-labelcolor` only shows the explicit arm may not return
    # `tickColor`; that leaves "return some OTHER colour there" unattacked, and a
    # spec pinning merely "not the tick colour" on that arm would still be too
    # weak. This rival closes it: on the explicit arm it returns a colour that is
    # neither `tickColor` nor the label colour `c`, so the result must be pinned
    # to `c` itself and not merely away from `tickColor`.
    # =====================================================================
    {
        "id": "weak-explicit-foreign-color",
        "kind": "uniqueness",
        "expect": "reject",
        # Honour the sentinel fallback, but on the explicit arm discard the label
        # colour and hand back a further inhabitant of the opaque colour type.
        # Correct on the sentinel arm, wrong exactly on the explicit arm.
        "module": _noncomputable(_swap_both(
            _BASE, _GOLD_BODY,
            "  match labelColor with\n"
            "  | none   => return tickColor\n"
            f"  | some _ => return {_OTHER_COLOR}\n",
        )),
        "refinement": "the label-colour setting is consulted well enough to know "
                      "whether it expresses an opinion, but its VALUE is then "
                      "discarded: on an explicit setting the offset text is given "
                      "some third colour rather than the one that was set. The "
                      "F2P's first scenario sets the tick-label colour to an "
                      "explicit value and asserts the offset text comes out THAT "
                      "value; this rival gives it an unrelated colour, so a "
                      "faithful patch of this shape would NOT resolve — and unlike "
                      "`weak-ignore-labelcolor` it would not even leave the offset "
                      "text at the tick-mark colour, so no accidental agreement "
                      "could rescue it.",
        "rationale": "REJECT from the single modeled clause on its EXPLICIT arm, in "
                     "the direction the other explicit-arm rival cannot reach: "
                     "`weak-ignore-labelcolor` returns `tickColor` there, so on its "
                     "own it certifies only that the result differs from the tick "
                     "colour. A spec that pinned the explicit arm to `≠ tickColor` "
                     "rather than to `= c` would reject that rival and still be "
                     "SPEC-TOO-WEAK. This rival returns a colour equal to neither, "
                     "so its rejection is attributable to the result being pinned "
                     "to the label colour ITSELF. Correct on the sentinel arm, so "
                     "it is a genuine partial-domain rival. It attacks BOTH "
                     "obligations symmetrically (both impls edited). Binders "
                     "exercised: `labelColor` at `some c` and `c` as the value the "
                     "explicit arm must produce — the refutation is a disequality "
                     "between the rival's colour and `c`, and mentions neither "
                     "arm's fallback.",
        "witness": (
            "-- Refuted on the EXPLICIT arm, for BOTH sites, against the LABEL\n"
            "-- colour rather than against the tick colour. `Color` is opaque, so\n"
            "-- no literal input decides the goal; condition on the carrier. The\n"
            "-- single hypothesis says the colour the rival picks on the explicit\n"
            "-- arm differs from the label colour `c` the spec demands there. It is\n"
            "-- SATISFIABLE, not derivable: an opaque type cannot prove its own\n"
            "-- inhabitants equal, so nothing forces `Classical.choice` on\n"
            "-- `Nonempty Color` to land on `c` (the gate's consistency probe\n"
            "-- confirms `False` does not follow). `simp` proves the spec equation\n"
            "-- against the frozen impl and leaves it open against this rival, so\n"
            "-- the two sides' exit codes differ for a reason about the claim.\n"
            "example (tickColor c : Color)\n"
            f"    (h : {_OTHER_COLOR} ≠ c) :\n"
            "    ¬ problem_spec_horizOffsetTextColor tickColor (some c)\n"
            "        (implementation_horizOffsetTextColor tickColor (some c)) := by\n"
            "  unfold problem_spec_horizOffsetTextColor "
            "implementation_horizOffsetTextColor\n"
            "  simp\n"
            "  exact h\n"
            "example (tickColor c : Color)\n"
            f"    (h : {_OTHER_COLOR} ≠ c) :\n"
            "    ¬ problem_spec_vertOffsetTextColor tickColor (some c)\n"
            "        (implementation_vertOffsetTextColor tickColor (some c)) := by\n"
            "  unfold problem_spec_vertOffsetTextColor "
            "implementation_vertOffsetTextColor\n"
            "  simp\n"
            "  exact h\n"
        ),
    },
]

# No AXIOM lane here: the bundle declares one `opaque` leaf (the colour token) and
# consumes no `axiom`. The changed operation is a direct two-way conditional
# selection between two already-available colour values. The nagini AXIOM_TESTS
# were also empty; dropped.
AXIOM_TESTS = []
