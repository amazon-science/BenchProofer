"""properties.py — G-PBT falsification battery for django__django-16569 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start``/``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_addFields`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the file elaborates with the obligation closed and
no ``sorry``/``admit``/``native_decide`` and no new ``axiom``/``theorem``;
``expect="reject"`` passes iff it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``), which is the design document. The nagini bundle
contracts a PROCEDURE that mutates a fresh item object and pins THREE
independent postcondition clauses — the presence of an ordering control, the
pre-filling of that ordering control, and the presence of the removal control.
This Lean bundle models only the purely functional core of the SAME change: the
removal-control DECISION, i.e. nagini's third clause. The ordering-control
clauses are not modeled here at all (the surrounding ordering block already
handled a positionless item before the change and is therefore outside the
modeled behavior), so the two nagini rivals that attack those clauses have no
counterpart on this carrier — see the accounting block at the bottom, which
records every nagini case and its disposition. Case-count parity is NOT the
target; coverage of the surface this bundle DOES model is.

DEFENDED SURFACE (one obligation, one top-level clause, four input binders).
``problem_spec_addFields canDelete canDeleteExtra index ifc result`` pins

    result = some (canDelete && (canDeleteExtra || withinInitial index ifc))

a single equation carrying TWO logically separable demands, and the battery
attacks both:

  * TOTALITY — the outcome is ``some _`` for EVERY input, in particular for a
    positionless item. There is no "no answer" outcome. Attacked by
    ``weak-positionless-noanswer``.
  * VALUE — the boolean is exactly ``canDelete && (canDeleteExtra ||
    withinInitial index ifc)``, where ``withinInitial`` is false for a
    positionless item and ``decide (i < ifc)`` for a positioned one. Attacked by
    the five remaining rivals, one per way of getting the combination wrong:
    treating a positionless item as inside the prefix, moving the prefix
    boundary off by one, ignoring the extra-items permission, ignoring the outer
    permission, and ignoring prefix membership itself. The last two are duals —
    each deletes one disjunct — and BOTH are needed, because a witness only
    refutes a dropped disjunct at a point where that disjunct is what makes the
    decision true.

BINDER STRUCTURE. Four input binders — ``canDelete``, ``canDeleteExtra``,
``index``, ``ifc`` — and all four are VARIED by the reject witnesses rather than
pinned (point-spread block at the bottom, ``pts=6``). Binder variation is NOT by
itself coverage: the battery once varied all four while the DERIVED value the
spec's second disjunct turns on (``withinInitial index ifc``) stayed false at
every witness point, which hid a rival that deletes that disjunct. The
point-spread block now tracks that derived value alongside the binders. That
matters here more
than usual because the decision SHORT-CIRCUITS: a battery whose every witness
held ``canDelete = true`` and ``canDeleteExtra = false`` would probe only the
one path where the prefix test is reached, and a rival that mishandled either
switch alone would verify unnoticed. So one witness holds ``canDelete = false``
(refuting a rival that ignores the outer permission) and one holds
``canDeleteExtra = true`` (refuting a rival that ignores the extra-items
permission), while ``index`` ranges over positionless and two distinct concrete
positions and ``ifc`` over four distinct counts.

GROUNDED ORACLE — the echo class is vacuous. Carried over from the nagini
sibling's identical argument: the postcondition is pinned to ``withinInitial``,
a transparent pure ``def`` fully unfolded as a function of the item's optional
position and the pre-populated count. There is no opaque answer key an
implementation could ECHO — computing that helper IS doing the work. So the
positives below are honest cheapest-implementation controls rather than
echo probes.

FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already records this
class as N/A there (its only object input is held at full permission because it
IS the mutated output; every other input is a pass-by-value scalar). On this
carrier it is doubly vacuous: Lean is referentially transparent, the modeled
function returns a value instead of mutating one, and there is no read-only cell
to overwrite. No substitute probe is fabricated.

DIVERGENCE / NON-TERMINATION — VACUOUS ON THIS BACKEND. The nagini sibling
carries ``uniq-selfrec-diverge`` and treats the termination obligation as
MANDATORY, because a partial-correctness contract lets a diverging body satisfy
every postcondition vacuously. That hole cannot be reproduced here:
``implementation_addFields`` is a total Lean ``def``, so a body that fails to
produce an answer is not a rival that verifies — it is a file the elaborator
refuses. The class is genuinely vacuous on lean (contrast velvet under
``set_option loom.semantics.termination "partial"``, where it is a KNOWN SPEC
HOLE rather than a vacuous class; see ``the corpus-wide termination-semantics finding``). Nothing
is fabricated in its place, and no reject case is shipped for it — a reject case
needs a witness, and there is no rival here to refute.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate directly at ONE
concrete input, all four arguments ground literals, and closes by ``decide``.
Each binds NOTHING in its head, so there are no hypotheses whose joint
satisfiability could be in question, and each was checked with two real
``lake env lean`` builds: it HOLDS of its rival and FAILS on the frozen
solution, so it discriminates rather than asserting a tautology.

REFINEMENT. Every reject case's ``refinement`` argues why its faithful real
counterpart would NOT resolve, grounded in the observable behavior the failing
test and its siblings pin: whether a standalone template item, an item inside
the pre-populated prefix, and an item beyond it each carry the removal control,
under each setting of the two permission switches.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed decision is modeled deeply), and the axiom lane belongs
to G-AX, so the nagini ``AXIOM_TESTS`` containment probe is dropped.
"""
from pathlib import Path

INSTANCE = "django__django-16569"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (asserted by _swap), so every variant provably edits only the
# impl region and — for the cases that legitimately reprove — the proof body.
# ---------------------------------------------------------------------------

# The whole frozen impl body (inside -- impl-start / -- impl-end).
_I_BODY = """  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      -- The within-prefix test only makes sense for an item that has a concrete
      -- position; a positionless item is treated as outside the prefix.
      match index with
      | some i => if i < ifc then addControl := true
      | none   => pure ()
  return some addControl"""

# The whole frozen tactic body (inside -- proof-start / -- proof-end); the
# `theorem correct_addFields` STATEMENT above it is never touched.
_P_BODY = """  intro canDelete canDeleteExtra index ifc
  unfold problem_spec_addFields implementation_addFields withinInitial
  cases canDelete <;> cases canDeleteExtra <;> cases index <;>
    first
      | rfl
      | (rename_i val; by_cases h : val < ifc <;>
          simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
            pure] <;> rfl)"""

# The frozen proof's first tactic line — a unique hook inside the proof region
# for the admissibility case to prepend a ground `have` without disturbing the
# statement or the spec view.
_P_INTRO = "  intro canDelete canDeleteExtra index ifc"

assert _BASE.count(_I_BODY) == 1 and _BASE.count(_P_BODY) == 1


# ---------------------------------------------------------------------------
# Reshaped-but-CORRECT implementations (soundness positives).
# ---------------------------------------------------------------------------

# Fold the whole decision into ONE local computed from the spec's own transparent
# helper, then drive the single assignment off that local. Structurally different
# (no nested conditionals, no per-case assignment) and observationally identical.
_POS_FOLD_IMPL = """  let wantControl := canDelete && (canDeleteExtra || withinInitial index ifc)
  let mut addControl := false
  if wantControl then
    addControl := true
  return some addControl"""

# Re-proved for the folded shape: case on the value of the folded decision and
# reduce the single conditional. Statement byte-identical; no helper lemma, no
# assumption token.
_POS_FOLD_PROOF = """  intro canDelete canDeleteExtra index ifc
  unfold problem_spec_addFields implementation_addFields
  cases h : (canDelete && (canDeleteExtra || withinInitial index ifc)) <;>
    simp only [Id.run, h, if_true, if_false, pure] <;> rfl"""

# BRANCH REORDER: discriminate on the item's optional position FIRST and consult
# the two permission switches inside each arm, instead of testing the
# permissions first and the position last. Same values, mirrored control flow —
# the positionless arm now needs the extra-items permission explicitly, which is
# where the two arms visibly disagree.
_POS_REORDER_IMPL = """  let mut addControl := false
  match index with
  | some i =>
    if canDelete && (canDeleteExtra || decide (i < ifc)) then
      addControl := true
  | none   =>
    if canDelete && canDeleteExtra then
      addControl := true
  return some addControl"""


# ---------------------------------------------------------------------------
# Rival implementations (uniqueness). Each shares the frozen spec and changes
# ONLY the impl body.
# ---------------------------------------------------------------------------

# THE BUG. A positionless item reaches the prefix comparison, which cannot be
# performed for an item that has no position, so the decision produces NO answer.
_R_NOANSWER = """  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      match index with
      | some i => if i < ifc then addControl := true
      | none   => return none
  return some addControl"""

# Positionless item treated as if it sat INSIDE the pre-populated prefix.
_R_NONE_WITHIN = """  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      match index with
      | some i => if i < ifc then addControl := true
      | none   => addControl := true
  return some addControl"""

# Prefix boundary off by one: the first item BEYOND the pre-populated prefix is
# counted as inside it.
_R_LE = """  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      match index with
      | some i => if i <= ifc then addControl := true
      | none   => pure ()
  return some addControl"""

# Ignore the extra-items permission entirely: the control is attached only for an
# item inside the pre-populated prefix.
_R_IGNORE_EXTRA = """  let mut addControl := false
  if canDelete then
    match index with
    | some i => if i < ifc then addControl := true
    | none   => pure ()
  return some addControl"""

# Ignore the outer permission entirely: decide from the extra-items switch and
# the position alone.
_R_IGNORE_PERM = """  let mut addControl := false
  if canDeleteExtra then
    addControl := true
  else
    match index with
    | some i => if i < ifc then addControl := true
    | none   => pure ()
  return some addControl"""

# Ignore the PREFIX-MEMBERSHIP disjunct entirely: attach the control only when
# both permissions are set, never on the strength of the item's position. This is
# the disjunct-DROPPING dual of _R_IGNORE_EXTRA (which drops the other disjunct),
# and it is the rival that answers "no comparison at all" — the shape that makes
# the reported failure disappear by removing the position test rather than by
# guarding it. Added by audit: see the point-spread block, every earlier witness
# sits at a point where prefix membership is FALSE, so this rival agreed with the
# frozen solution at all five of them and no shipped witness could refute it.
_R_IGNORE_PREFIX = """  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
  return some addControl"""


def _witness(canDelete, canDeleteExtra, index, ifc):
    """Refute the spec predicate at ONE ground input.

    All four arguments are literals, so the head binds nothing (no hypotheses
    whose consistency could be in question) and the whole statement is decided
    by evaluation. Holds of its rival, fails on the frozen solution.
    """
    args = f"{canDelete} {canDeleteExtra} {index} {ifc}"
    return (f"example : ¬ problem_spec_addFields {args}\n"
            f"    (implementation_addFields {args}) := by\n"
            "  unfold problem_spec_addFields implementation_addFields "
            "withinInitial\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-fold-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(_BASE,
                         (_I_BODY, _POS_FOLD_IMPL),
                         (_P_BODY, _POS_FOLD_PROOF)),
        "rationale": "collapses the nested conditionals into ONE local holding "
                     "the whole decision, computed from the spec's own "
                     "transparent prefix helper, then drives a single "
                     "assignment off it. Observationally identical on every "
                     "input, so the equation still holds and it MUST verify — "
                     "else SPEC-TOO-STRONG. Re-proved honestly for the folded "
                     "shape (case on the folded decision's value, reduce the "
                     "single conditional): statement byte-identical, no helper "
                     "lemma, no assumption token. Ports nagini's "
                     "pos-control-flag-fold, whose precomputed booleans this "
                     "collapses to the one boolean this carrier models. Note "
                     "the helper is NOT an oracle echo: it is a transparent "
                     "def over the inputs, so computing it IS doing the work.",
    },
    {
        "id": "pos-position-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _I_BODY, _POS_REORDER_IMPL),
        "rationale": "BRANCH REORDER: discriminates on the item's optional "
                     "position FIRST and consults the two permission switches "
                     "inside each arm, mirroring the frozen order. The "
                     "positionless arm must now name the extra-items "
                     "permission explicitly, so the two arms visibly differ "
                     "while agreeing on every input. A faithful reshape MUST "
                     "verify, else SPEC-TOO-STRONG; the frozen tactic script "
                     "still closes it verbatim (checked with a real build), so "
                     "nothing is reproved and the statement is untouched. "
                     "Ports nagini's pos-control-helper-reorder, narrowed to "
                     "the one branch this bundle models.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at exactly the input the
    # reported defect is observed at, so the modeled behavior is not vacuous
    # there (the analogue of nagini's PRECOND-TOO-STRONG probe: this
    # obligation carries no precondition hypotheses to admit, so the honest
    # counterpart is to discharge the postcondition at that input).
    # =====================================================================
    {
        "id": "admiss-positionless-item",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _adm : problem_spec_addFields true false none 0\n"
            "      (implementation_addFields true false none 0) := by\n"
            "    unfold problem_spec_addFields implementation_addFields "
            "withinInitial\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "discharges the spec by EVALUATION at the canonical "
                     "input the defect is reported at — removal permitted, "
                     "extra items not removable, a positionless item, nothing "
                     "pre-populated — as a `have`, then closes the frozen "
                     "obligation verbatim. Verifies unless the modeled "
                     "behavior is unsatisfiable at exactly that normal input, "
                     "which is this carrier's image of PRECOND-TOO-STRONG. "
                     "Nothing is assumed: no new declaration, no assumption "
                     "token, statement byte-identical, the ground instance is "
                     "a `have` inside the existing tactic body. Ports nagini's "
                     "admiss-empty-form (there: assert each Requires conjunct "
                     "for that same configuration).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries a witness seen to hold
    # of the rival and to FAIL on the frozen solution.
    # =====================================================================
    {
        "id": "weak-positionless-noanswer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, _R_NOANSWER),
        "refinement": "this IS the behavior at issue: a positionless item is "
                      "sent into the prefix comparison, which has no meaning "
                      "for an item that has no position, so instead of "
                      "answering, the decision fails outright. A faithful real "
                      "counterpart does not merely mis-attach a control — it "
                      "aborts whenever a standalone template item is prepared "
                      "under 'removal permitted, extra items not removable'. "
                      "The failing test's added assertion inspects exactly "
                      "that item's controls under exactly those two settings, "
                      "so it never reaches its assertion at all. Does NOT "
                      "resolve.",
        "rationale": "REJECT from the TOTALITY half of the equation: the spec "
                     "pins `result = some _` for EVERY input, and this rival "
                     "produces no answer for a positionless item when removal "
                     "is permitted and extra items are not removable. Refuted "
                     "at (canDelete=true, canDeleteExtra=false, "
                     "index=positionless, ifc=0) — the sole witness attacking "
                     "totality rather than the boolean value.",
        "witness": _witness("true", "false", "none", "0"),
    },
    {
        "id": "weak-positionless-counted-inside",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, _R_NONE_WITHIN),
        "refinement": "answers for a positionless item, but counts it as "
                      "sitting INSIDE the pre-populated prefix. A faithful "
                      "real counterpart that special-cased the positionless "
                      "item to 'inside' would attach the removal control to "
                      "the standalone template item under 'removal permitted, "
                      "extra items not removable' — and the failing test's "
                      "added assertion requires that item to carry NO removal "
                      "control. Does NOT resolve; this rival is the "
                      "over-correction that avoids the crash and still fails "
                      "the same assertion.",
        "rationale": "REJECT from the VALUE half: `withinInitial` is false for "
                     "a positionless item, so the spec demands the control be "
                     "withheld when extra items are not removable, but the "
                     "rival attaches it. Refuted at (true, false, "
                     "positionless, ifc=3) — a NON-ZERO pre-populated count, "
                     "distinguishing this from the totality rival above and "
                     "showing the disagreement is about the positionless case "
                     "rather than about an empty collection. Ports nagini's "
                     "uniq-none-counts-initial.",
        "witness": _witness("true", "false", "none", "3"),
    },
    {
        "id": "weak-prefix-boundary-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, _R_LE),
        "refinement": "moves the prefix boundary by one, so the FIRST item "
                      "beyond the pre-populated prefix counts as inside it. "
                      "A faithful real counterpart would hand the removal "
                      "control to that first non-pre-populated item under "
                      "'removal permitted, extra items not removable' — and "
                      "the failing test walks exactly that boundary, "
                      "requiring the control on the pre-populated item and "
                      "NOT on the ones past it. Does NOT resolve.",
        "rationale": "REJECT from the VALUE half at the boundary point "
                     "index = ifc, where `withinInitial` is false (strict "
                     "comparison) but the rival's non-strict test is true. "
                     "This rival agrees with the frozen solution everywhere "
                     "else, so it is refuted at its own distinguishing point: "
                     "(true, false, position 2, ifc=2) — a CONCRETE position, "
                     "the near-miss that the positionless witnesses could not "
                     "expose. Ports nagini's uniq-delete-le-boundary.",
        "witness": _witness("true", "false", "(some 2)", "2"),
    },
    {
        "id": "weak-ignores-extra-permission",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, _R_IGNORE_EXTRA),
        "refinement": "drops the extra-items permission from the decision, so "
                      "the control is attached only inside the pre-populated "
                      "prefix. Correct on the reported configuration (which "
                      "has that permission off) but a regression wherever it "
                      "is on: a faithful real counterpart would strip the "
                      "removal control from every item beyond the "
                      "pre-populated prefix in the DEFAULT configuration, "
                      "which the sibling passing test requires to carry it. "
                      "Does NOT resolve.",
        "rationale": "REJECT from the VALUE half: the spec's disjunction makes "
                     "the control unconditional when extra items may be "
                     "removed, and the rival withholds it. Refuted at "
                     "(canDelete=true, canDeleteExtra=TRUE, position 5, "
                     "ifc=1) — the only witness exercising the extra-items "
                     "permission in its enabled state, and a position beyond "
                     "the prefix. Without it that binder would be held at "
                     "`false` by every rival and this whole disjunct would go "
                     "untested. Ports nagini's uniq-delete-ignore-extra.",
        "witness": _witness("true", "true", "(some 5)", "1"),
    },
    {
        "id": "weak-ignores-outer-permission",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, _R_IGNORE_PERM),
        "refinement": "drops the OUTER permission, deciding from the "
                      "extra-items switch and the position alone. A faithful "
                      "real counterpart would attach a removal control to "
                      "items in collections where removal is not permitted at "
                      "all — the extra-items switch defaults to enabled, so "
                      "this adds the control to essentially every collection "
                      "in the suite, and the many passing tests that pin "
                      "rendered output and field sets for non-removable "
                      "collections all break. Does NOT resolve.",
        "rationale": "REJECT from the VALUE half: the spec's outer conjunct "
                     "makes the whole decision false whenever removal is not "
                     "permitted, and the rival ignores it. Refuted at "
                     "(canDelete=FALSE, canDeleteExtra=true, positionless, "
                     "ifc=0) — the only witness holding the outer permission "
                     "DISABLED. ADDED beyond the nagini set (see the "
                     "accounting block): nagini's rivals all keep that "
                     "conjunct, so without this case every witness would pin "
                     "the binder to `true` and a rival that mishandled only "
                     "the outer switch would verify unnoticed.",
        "witness": _witness("false", "true", "none", "0"),
    },
    {
        "id": "weak-ignores-prefix-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, _R_IGNORE_PREFIX),
        "refinement": "drops the prefix-membership disjunct, so the control is "
                      "attached from the two permission switches alone and an "
                      "item's position never earns it. A faithful real "
                      "counterpart withholds the removal control from every "
                      "pre-populated item whenever extra items are not "
                      "removable — and the failing test's FIRST assertion "
                      "requires exactly that item to CARRY the control, in the "
                      "same configuration whose later assertion motivated the "
                      "change. So this rival breaks the very test the change is "
                      "measured by, in its already-passing half. Does NOT "
                      "resolve.",
        "rationale": "REJECT from the VALUE half, at the only sub-domain the "
                     "other rivals leave unattacked: prefix membership TRUE. "
                     "The spec's second disjunct must be able to carry the "
                     "decision on its own — with removal permitted and extra "
                     "items NOT removable, an item inside the pre-populated "
                     "prefix still gets the control. Refuted at (true, false, "
                     "position 0, ifc=1), the first witness in this battery "
                     "where `withinInitial` is TRUE. ADDED by audit: every "
                     "other witness sits at a point where that helper is false, "
                     "so this rival agreed with the frozen solution at all five "
                     "of them (machine-checked: the spec predicate ELABORATES "
                     "of this rival at each) and its wrongness was invisible to "
                     "the battery — a rival mishandling only this disjunct "
                     "would have verified unnoticed.",
        "witness": _witness("true", "false", "(some 0)", "1"),
    },
]


# ---------------------------------------------------------------------------
# nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus a 1-case AXIOM lane.
# This bundle models a NARROWER surface — the removal-control decision only, not
# the two ordering-control clauses — so two sibling rivals have no counterpart
# here. Every sibling case is recorded, and one rival is ADDED for binder
# coverage this backend's tooling (rightly) demands.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-helper-reorder   -> pos-position-first          RE-EXPRESSED
#   pos-control-flag-fold        -> pos-fold-decision           RE-EXPRESSED
#   admiss-empty-form            -> admiss-positionless-item    RE-EXPRESSED
#   uniq-drop-guard              -> weak-positionless-noanswer  PORTED
#   uniq-none-counts-initial     -> weak-positionless-counted-inside  PORTED
#   uniq-delete-le-boundary      -> weak-prefix-boundary-off-by-one   PORTED
#   uniq-delete-ignore-extra     -> weak-ignores-extra-permission     PORTED
#   uniq-prefill-always          -> (none)                      OMITTED (unmodeled)
#   uniq-order-iff-prefill       -> (none)                      OMITTED (unmodeled)
#   uniq-selfrec-diverge         -> (none)                      VACUOUS on lean
#   (none)                       -> weak-ignores-outer-permission     ADDED
#   (none)                       -> weak-ignores-prefix-membership    ADDED (audit)
#   AXIOM_TESTS (1 containment)  -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED (pos-position-first): the sibling reorders its two ATTACHMENT
#   branches (removal branch before ordering branch) and lifts the shared prefix
#   predicate into a local. Only one of those branches is modeled here, so the
#   analogous reshape reorders the DISCRIMINATION instead: match on the item's
#   optional position first, consult the permission switches inside each arm.
# RE-EXPRESSED (pos-fold-decision): the sibling precomputes three booleans, one
#   per clause, then assigns each flag. This carrier has one clause, so the fold
#   collapses to the one boolean — and it is computed from the spec's own
#   transparent prefix helper, which is the sibling's "helper into a local" move.
# RE-EXPRESSED (admiss-positionless-item): the sibling's obligation carries a
#   real precondition (a fresh item, all flags down, a non-negative count) and
#   its witness asserts each conjunct. This obligation is unconditional — there
#   is no precondition to admit — so the honest counterpart is to discharge the
#   postcondition by evaluation at the same canonical configuration, which shows
#   the modeled behavior is satisfiable exactly where the defect is reported.
# OMITTED (uniq-prefill-always, uniq-order-iff-prefill): both attack the
#   ordering-control clauses — the presence of an ordering control, and its
#   pre-filling for an item inside the pre-populated prefix. This bundle does
#   NOT model those clauses at all: the surrounding ordering behavior already
#   handled a positionless item before the change, so it lies outside the
#   modeled surface and the spec predicate has no ordering component to attack.
#   Writing rivals for it would mean inventing behavior this bundle does not
#   model. This is carrier narrowing, not a proof that would not close.
# VACUOUS (uniq-selfrec-diverge): the sibling's rival replaces the body with a
#   bare self-call so every postcondition holds vacuously, and its rejection
#   comes from the sibling's explicit termination obligation. Here
#   `implementation_addFields` is a total Lean `def`: a self-call has no
#   decreasing measure, so it is not a rival that verifies but a file that does
#   not elaborate, and a diverging implementation cannot be written at all. No
#   reject case is shipped, because a reject case needs a witness and there is
#   no rival to refute. (This is genuinely vacuous on lean, unlike velvet under
#   partial termination semantics, where the same class is a KNOWN SPEC HOLE —
#   the corpus-wide termination-semantics finding.)
# VACUOUS (frame / permission mutation): N/A in the sibling already (no
#   read-only input to overwrite; every non-output input is a scalar), and doubly
#   so here — referential transparency, a returned value rather than a mutated
#   one, no aliasing. No substitute probe fabricated.
# ADDED (weak-ignores-prefix-membership, by audit): the nagini sibling's
#   uniq-delete-ignore-extra drops ONE disjunct of the decision; nothing on
#   either side dropped the OTHER. That left the spec's prefix-membership
#   disjunct attested only at points where it evaluates to false, where deleting
#   it changes nothing. The rival that deletes it agreed with the frozen solution
#   at all five pre-audit witness points, so the battery recorded SOUND while
#   that disjunct's load-bearing role was untested. Its faithful counterpart
#   breaks the already-passing half of the very test the change is measured by.
# ADDED (weak-ignores-outer-permission): every nagini rival keeps the outer
#   permission conjunct intact, so a straight port would hold that binder at
#   `true` in all five witnesses — precisely the failure mode where a rival
#   mishandling only that switch verifies and the battery never notices. It
#   attacks a real, load-bearing conjunct of the SAME modeled spec, and its
#   faithful counterpart breaks the many passing tests that pin field sets for
#   collections where removal is not permitted.
#
# POINT SPREAD. The six reject witnesses probe six DISTINCT input tuples
# (pts=6), and every input binder MOVES across them. The last column is the
# value of `withinInitial index ifc` at that point, which is the binder-level
# fact the audit added a case for:
#   (canDelete, canDeleteExtra, index, ifc)                        withinInitial
#     (true,  false, none,     0)  weak-positionless-noanswer      false  totality
#     (true,  false, none,     3)  weak-positionless-counted-inside false value
#     (true,  false, some 2,   2)  weak-prefix-boundary-off-by-one  false value
#     (true,  true,  some 5,   1)  weak-ignores-extra-permission    false value
#     (false, true,  none,     0)  weak-ignores-outer-permission    false value
#     (true,  false, some 0,   1)  weak-ignores-prefix-membership   TRUE   value
#   canDelete takes both values; canDeleteExtra takes both values; index is
#   positionless in three witnesses and three DISTINCT concrete positions in the
#   others; ifc takes four distinct counts, including the boundary case
#   index = ifc that the off-by-one rival needs and a non-zero count that keeps
#   the positionless witnesses from all sitting on an empty collection.
#
#   The last row is the one an audit had to add, and the reason is a coverage
#   fact no binder-level report shows: the first five witnesses all sit at points
#   where the prefix-membership helper is FALSE, so the spec's second disjunct is
#   never observed CARRYING the decision. Every binder "varied" while the derived
#   value that the disjunct turns on did not. A rival that simply deletes that
#   disjunct is therefore observationally equal to the frozen solution at all
#   five earlier points — machine-checked, the spec predicate elaborates of it at
#   each — and only a witness with withinInitial TRUE refutes it.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no opaque callee (the decision is modeled deeply), so the sibling's
# containment probe has nothing to bind to and the gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []
