"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8638 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a FULL
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start``/``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is
changed, so ``markers.same_spec`` holds by construction and the single
``theorem correct_renderVariableItem`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the file elaborates with the obligation closed
(no ``sorry``/``admit``/``native_decide``, no new ``axiom``/``theorem``);
``expect="reject"`` passes iff it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE
---------
This is a PORT of the nagini falsification battery (``../nagini/properties.py``)
onto this backend's carrier, not a fresh invention. Nagini contracts TWO
functions over an ``int`` role code / ``FieldNode`` carrier: a per-token
node-kind renderer (its own clauses X1/X2) and a two-token entry builder
(clauses P1-P4). This Lean bundle models the SAME
purely-functional core as ONE function — the rendering of a whole documented-
variable item into an inline node sequence — over a ``List RenderNode`` carrier,
with the role-application helper spelled out as the pure ``makeXref`` def rather
than contracted separately. So every nagini case carries over, but the ones
nagini attached to the helper's OWN postcondition (X1/X2) re-express here as
attacks on the composite item spec at the point where the helper is applied:
there is no separate ``theorem correct_makeXref`` to attack. See ``assessment``
for the case-by-case correspondence and for the classes that are legitimately
absent.

DEFENDED SURFACE (one modeled behavior; one equation with two branch arms)
-------------------------------------------------------------------------
``problem_spec_renderVariableItem name type? content result`` pins ``result`` to
EXACTLY one list, by cases on whether a type token is present:

  * (C-head)  the head node is a PLAIN ``strong name`` — the variable's name
    token stands on its own and is NOT wrapped in a cross-reference. This is the
    load-bearing, discriminating clause: the frozen sibling behavior wraps that same
    token in a cross-reference, and it is the only observable delta.
  * (C-type, ``some t`` arm)  the head is followed by ``text " ("``, then the
    type token as ``xref variableTypeRole (emph t)`` — a cross-reference over an
    emphasis token, carrying the class reference type — then ``text ")"``. This
    is the UNCHANGED companion behavior; pinning it stops a rival from satisfying
    the spec by ALSO dropping the type cross-reference.
  * (C-none, ``none`` arm)  the head is followed directly by the separator, with
    no parenthesized type group at all.
  * (C-tail, both arms)  the separator ``text " -- "`` then ``content`` verbatim,
    in that order and with no extra nodes. Frame discipline: the description
    fragment is passed through unchanged and the equation is an EQUALITY, so
    there is no unconstrained output position a rival could fill freely.

Because the postcondition is a single ``=`` against a term built only from the
inputs, every clause above is positional: order, node kind, and the role carried
by the type cross-reference are all pinned simultaneously.

BINDER STRUCTURE
----------------
Three input binders: ``name`` (the variable's name), ``type?`` (the optional type
token) and ``content`` (the description fragment). All three are load-bearing and
all three are VARIED across the eight reject witnesses, which probe eight
DISTINCT input points (``pts=8``):

  * ``name`` ranges over ``"attr"``, ``"x"``, ``"n"``, ``"flag"``;
  * ``type?`` takes ``none`` on two witnesses and ``some`` of five different
    tokens (``"int"``, ``"T"``, ``"C"``, ``"cls"``, ``"bool"``) on the other six,
    so BOTH arms of the branch are attacked, not just the type-present one;
  * ``content`` ranges over ``[]``, a one-node list, and two-node lists, and over
    three different node constructors (``text``/``strong``/``emph``), so a rival
    that mishandled the pass-through only for a non-empty or non-``text``
    fragment cannot hide.

ADVERSARIAL READ of the nagini case classes on this carrier
-----------------------------------------------------------
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole battery lives. Six
    of the eight rivals diverge from the spec on a proper sub-domain: a present
    name role (nagini U1), the dropped type cross-reference (U2), a type
    cross-reference carrying the wrong reference type (nagini's reftype mask,
    U5), the two tokens emitted in the wrong positions (U3), the role-application
    decision inverted between the two tokens (U4), and two rivals with no nagini
    counterpart that attack the tail and the type-absent arm (see
    ``assessment``).

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already records
    this class as inapplicable there (both of its inputs are passed by value and
    the only heap permissions are on the freshly built result). On this carrier it
    is doubly so: Lean is referentially transparent, ``name``/``type?``/
    ``content`` are immutable values, there is no aliasing and no caller-owned
    cell a rival could overwrite. No substitute probe is fabricated. What DOES
    port is nagini's result-mutation sanity case (U6), which is not a frame
    property at all but a "the spec pins the FINAL value, not a transient" check;
    ``weak-relink-after`` below is its counterpart, expressed with the local
    ``let mut`` list rather than in-place element assignment.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason nagini gives. The
    postcondition is GROUNDED: ``result`` is equated to a term built from the
    inputs by explicit node constructors, with no opaque callee and no answer key
    to echo. Producing the right list IS doing the work. Honest cheapest-
    implementation positive controls stand in for the class.

  * DIVERGENCE / NON-TERMINATION — no shippable case, and the reason is MEASURED
    rather than asserted. This is vanilla Lean 4: the file carries no
    ``loom.semantics.termination`` option at all, so the carrier is total and the
    elaborator itself discharges termination. Both ways of writing a diverging
    rival were actually built, and neither yields a WITNESSED reject case:

      - an unguarded self-recursive ``def`` (no decreasing measure) is refused by
        the elaborator — ``error: fail to show termination for`` — so the variant
        never reaches a spec question, and a witness appended to it cannot build
        either (the file does not elaborate), which the gate would score
        ``witness-unproven``, an ERROR, not a rejection;
      - a ``partial def`` DOES elaborate, and is genuinely rejected (the frozen
        script fails: ``Tactic `unfold` failed to unfold
        implementation_renderVariableItem``) — but a ``partial def`` is opaque to
        reduction, so the refutation cannot be decided EITHER, and no witness can
        hold of it.

    So the class is empty for a tooling reason intrinsic to the carrier (no
    diverging impl is simultaneously elaborable AND reducible), not because the
    spec has a hole: unlike velvet under
    ``loom.semantics.termination "partial"``, no diverging impl VERIFIES here.
    The nagini sibling carries no such case either.

  * AXIOM lane — EMPTY. The bundle declares no ``opaque`` callee and consumes no
    ``axiom``; the role-application helper is modeled deeply (A-reference,
    G-AX's job). nagini's ``AXIOM_TESTS`` is empty for the same reason and is
    dropped per the porting map.

WITNESSES
---------
On a tactic-proof backend "did not verify" is the DEFAULT outcome of reshaping an
implementation — the frozen script is ``intro``/``cases``/``rfl``, tuned to the
frozen form — so a rejection ALONE attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating
``¬ problem_spec_renderVariableItem`` at ONE concrete input and closing by
``decide``: the carrier is a ``DecidableEq`` inductive over ``String``, so every
probe point computes and no hypothesis is needed. Each witness binds NOTHING in
its head, so there are no assumptions whose joint satisfiability could be in
question (no ``witness-inconsistent`` risk by construction). Each was checked
with two real ``lake env lean`` builds: it HOLDS of its rival (exit 0) and FAILS
on the frozen solution (exit 1, ``decide`` reporting the negation false), so it
discriminates rather than asserting a tautology.

No two rivals share a witness. Each probes the input point where its own
sub-domain claim bites, so the ``rationale`` never claims a divergence the
manifest does not demonstrate.

POSITIVE-CONTROL STRENGTH (audit note)
--------------------------------------
Two of the three soundness positives (``pos-branch-reorder``,
``pos-functional-reshape``) are DEFINITIONALLY equal to the frozen impl: each
carries the frozen ``cases type?``/``rfl`` proof region byte-for-byte and closes
under it. They are honest reshapes, but a spec strong enough to admit only terms
defeq to gold would still pass both, so on their own the lane could not detect a
SPEC-TOO-STRONG. ``pos-content-forloop`` was added by audit to close that: it
builds the description fragment through a ``for`` loop, so the result is a
``forIn`` fold only PROPOSITIONALLY equal to ``par ++ content``, ``rfl`` cannot
close it, and the case must re-prove the obligation by induction on the fragment.

SCOPE OF THE REFINEMENT ARGUMENTS (audit note)
----------------------------------------------
Checked against the actual test lists: the F2P item and every item in the
field-list regression test carry a TYPE token, and no test in either the F2P or
the P2P list renders a type-less item. So ``weak-none-arm-parens`` is NOT
justified by a would-not-resolve argument — its refinement is corrected in place
to say so, and it is retained as a spec-COVERAGE case for the ``none`` arm. Every
other reject case's refinement argument was checked against the F2P assertions
and holds.

REFINEMENT
----------
Every reject case's ``refinement`` argues that its faithful real counterpart
renders the documented-variable item with at least one inline node of the wrong
kind, wrong reference type, or wrong position, and that the F2P test pins the
item's child sequence node-for-node (plus the type cross-reference's reference
type and target as a separate assertion). So each rival's faithful patch would
NOT resolve, and a rival that VERIFIED would be a true
verify-does-not-imply-resolve break rather than an artifact.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8638"
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
# Region anchors. Each is unique in Solution.lean and lies WHOLLY inside the
# `-- impl-start`/`-- impl-end` region, except `_P_INTRO` (wholly inside
# `-- proof-start`/`-- proof-end`). So same_spec holds for every variant and the
# `correct_renderVariableItem` STATEMENT is never touched.
# ---------------------------------------------------------------------------

# The configured role for the NAME token (empty == no cross-reference).
_I_NAMEROLE = '  let nameRole : String := ""'

# The name token append (trailing newline included so it can be MOVED).
_I_NAMEAPP = "  par := par ++ [makeXref nameRole (RenderNode.strong name)]\n"

# The type token append, inside the type-present arm.
_I_TYPEAPP = "  par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]"

# The separator append (both arms).
_I_SEP = '  par := par ++ [RenderNode.text " -- "]'

# The description pass-through, and the final return.
_I_CONTENT = "  par := par ++ content\n"
_I_TAIL = "  par := par ++ content\n  return par"

# The type-absent arm (emits nothing extra).
_I_NONEARM = "  | none => pure ()"

# The whole branch, for the branch-REORDER positive.
_I_MATCH = """  match type? with
  | some t =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
      par := par ++ [RenderNode.text ")"]
  | none => pure ()
"""

# The whole impl region, for the functional-reshape positive.
_I_REGION = _BASE[_BASE.index("-- impl-start"):_BASE.index("-- impl-end")]

# The frozen proof's intro line — wholly inside the proof region — so the
# admissibility positive can PREPEND a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro name type? content"

# The frozen proof's whole tactic BODY — wholly inside the proof region — for the
# positive that cannot inherit gold's `rfl` and must re-prove the obligation.
# Replacing it leaves the theorem STATEMENT untouched (the statement ends at
# `:= by`, which is not part of this anchor).
_P_BODY = """  intro name type? content
  unfold problem_spec_renderVariableItem implementation_renderVariableItem
  cases type? with
  | none => rfl
  | some t => rfl
"""


# ---------------------------------------------------------------------------
# Witness scaffold. The carrier is a `DecidableEq` inductive over `String`, so
# the spec predicate at ground inputs is decidable and `decide` settles it: no
# opaque term, no hypothesis, nothing bound in the head.
# ---------------------------------------------------------------------------
def _w(name, type_, content):
    return (
        f"example : ¬ problem_spec_renderVariableItem {name} {type_} {content}\n"
        f"    (implementation_renderVariableItem {name} {type_} {content}) := by\n"
        "  unfold problem_spec_renderVariableItem "
        "implementation_renderVariableItem\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_renderVariableItem` statement byte-identical and adds no
    # declaration, no helper lemma and no assumption token.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Test the type-ABSENT case first and the type-present case second —
        # nagini's pos-makexref-reorder, re-expressed on the branch this bundle
        # actually models. Identical values, different control-flow shape; the
        # frozen `cases type?` proof still closes both arms by `rfl`, so no proof
        # authoring is needed. (Checked: real build, exit 0.)
        "module": _swap(
            _BASE, _I_MATCH,
            """  match type? with
  | none => pure ()
  | some t =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
      par := par ++ [RenderNode.text ")"]
"""),
        "rationale": "branch-REORDER positive control: the type-absent arm is "
                     "written first, the type-present arm second. Same value on "
                     "every input, so C-head/C-type/C-none/C-tail all still hold "
                     "— if this failed to verify the spec would be rejecting a "
                     "faithful reordering (SPEC-TOO-STRONG). Statement "
                     "byte-identical, no new axiom/lemma; the frozen per-arm "
                     "`rfl` still closes. Ports nagini's pos-makexref-reorder "
                     "(there: try the absent-role branch first) onto the branch "
                     "this bundle models.",
    },
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Drop the accumulator entirely: no `let mut`, no appends, no named role
        # local. Build the node sequence directly with `::`, applying the absent
        # role as a literal at the name token. This is nagini's pos-bvfe-reshape
        # (drop the role local, assemble differently) pushed as far as the
        # carrier allows. (Checked: real build, exit 0.)
        "module": _swap(
            _BASE, _I_REGION,
            """-- impl-start
def implementation_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode) :
    List RenderNode :=
  -- No cross-reference role is configured for a variable NAME, so the name
  -- token is built directly under the absent (empty) role.
  makeXref "" (RenderNode.strong name) ::
    (match type? with
     | some t =>
         RenderNode.text " (" ::
           makeXref variableTypeRole (RenderNode.emph t) ::
           RenderNode.text ")" :: RenderNode.text " -- " :: content
     | none => RenderNode.text " -- " :: content)
"""),
        "rationale": "correct reshape from an accumulator loop to a direct "
                     "cons-built sequence, dropping the intermediate role local "
                     "and applying the absent role as a literal. Every clause is "
                     "satisfied on every input (same list), so it MUST verify "
                     "else SPEC-TOO-STRONG. The frozen `cases type?`/`rfl` proof "
                     "still closes; statement byte-identical, no new "
                     "axiom/lemma. Ports nagini's pos-bvfe-reshape (drop the "
                     "name-role local, assemble the entry differently).",
    },
    {
        "id": "pos-content-forloop",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The two positives above are both DEFINITIONALLY equal to
        # the frozen impl — each closes under the frozen `cases type?`/`rfl`
        # script byte-for-byte, so neither exercises a reduction the frozen proof
        # did not already do, and a spec that only accepted terms defeq to gold
        # would still pass them both. This one does not: the description fragment
        # is appended NODE BY NODE through a `for` loop, so the result is built by
        # a `forIn` fold that is only PROPOSITIONALLY equal to `par ++ content`.
        # `rfl` cannot close it (measured: `maximum recursion depth`/`whnf`
        # timeout); it needs a real induction on `content`. That makes it the only
        # positive here that could actually detect a spec too strong to admit a
        # faithful loop-shaped renderer — the shape the real callee uses when the
        # fragment has several nodes. (Checked: real build, exit 0.)
        "module": _swaps(
            _BASE,
            (_I_REGION,
             """-- impl-start
def implementation_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode) :
    List RenderNode := Id.run do
  let mut par : List RenderNode := [makeXref "" (RenderNode.strong name)]
  match type? with
  | some t =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
      par := par ++ [RenderNode.text ")"]
  | none => pure ()
  par := par ++ [RenderNode.text " -- "]
  for c in content do
    par := par ++ [c]
  return par
"""),
            (_P_BODY,
             """  have flat : ∀ (cs : List RenderNode),
      (List.map (fun x => [x]) cs).flatten = cs := by
    intro cs; induction cs with
    | nil => rfl
    | cons c cs ih => simp [ih]
  intro name type? content
  unfold problem_spec_renderVariableItem implementation_renderVariableItem
  cases type? with
  | none =>
    simp [Id.run, makeXref, flat content]
    rfl
  | some t =>
    simp [Id.run, makeXref, variableTypeRole, flat content]
    rfl
"""),
        ),
        "rationale": "correct reshape that appends the description fragment one "
                     "node at a time through a `for` loop instead of a single "
                     "list append. Same list on every input, so it MUST verify "
                     "else SPEC-TOO-STRONG. Unlike the two positives above it is "
                     "NOT definitionally equal to the frozen impl — the frozen "
                     "`rfl` script cannot close it, so the case re-proves the "
                     "obligation by induction on the fragment rather than "
                     "inheriting gold's reduction. Statement byte-identical; the "
                     "re-proof is confined to the proof region and adds no "
                     "declaration, axiom or assumption token (the `have` is a "
                     "local list identity). Added by audit to give the soundness "
                     "lane a positive whose proof is not gold's.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, F2P-shaped
    # input, i.e. not vacuously true and not excluding the very case the
    # modeled behavior is about. The frozen obligation carries NO precondition hypothesis, so
    # nagini's precondition-admitting self-call re-expresses as: discharge the
    # spec predicate by evaluation at a concrete F2P-shaped item as a `have`
    # inside the existing tactic body, then close the frozen obligation
    # verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical. (Checked: real build, exit 0.)
    # =====================================================================
    {
        "id": "admiss-ground-item",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '''  have _ground : problem_spec_renderVariableItem "attr" (some "int")
      [RenderNode.text "blah blah"]
      (implementation_renderVariableItem "attr" (some "int")
        [RenderNode.text "blah blah"]) := by
    unfold problem_spec_renderVariableItem implementation_renderVariableItem
    decide
''' + _P_INTRO),
        "rationale": "the obligation is discharged BY EVALUATION at an "
                     "F2P-shaped item (a named variable with a present type "
                     "token and a one-node description) as a `have`, then the "
                     "frozen obligation is closed verbatim. If that ground "
                     "instance could not be decided true, the modeled behavior "
                     "would be unsatisfiable at exactly a normal input — the "
                     "analogue of PRECOND-TOO-STRONG, and it would also mean the "
                     "reject witnesses' `decide` verdicts were meaningless. "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical, the `have` sits in the existing tactic "
                     "body. Ports nagini's admiss-bvfe-selfcall.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness, checked
    # by two real builds, pinning the violation at one concrete input.
    # =====================================================================

    # ---- THE central attack: the name token links ----
    {
        "id": "weak-name-role-present",
        "kind": "uniqueness",
        "expect": "reject",
        # The name token is built under a PRESENT role, so it comes out wrapped
        # in a cross-reference instead of plain. This is the sibling behavior the
        # frozen `Solution_prepatch.lean` carries.
        "module": _swap(_BASE, _I_NAMEROLE, '  let nameRole : String := "obj"'),
        "refinement": "configuring a present role for the name token IS the "
                      "configuration the change replaces. Its faithful real "
                      "simply the change not applied, under which the item's "
                      "name token renders as a navigable cross-reference "
                      "instead of a plain strong token. The F2P test asserts the "
                      "item's first child is a plain strong node holding the "
                      "variable name, so it FAILS — the faithful patch would NOT "
                      "resolve, which is exactly the reported defect.",
        "rationale": "REJECT from C-head: the spec pins the head node to a PLAIN "
                     "`strong name`, the rival emits `xref _ (strong name)`. "
                     "Refuted at name=\"attr\", a present type token and a "
                     "one-node description — the F2P-shaped point. If it "
                     "verified, SPEC-TOO-WEAK on the load-bearing clause. Ports nagini's rival-prepatch-namerole (U1).",
        "witness": _w('"attr"', '(some "int")', '[RenderNode.text "blah blah"]'),
    },

    # ---- the companion attack: the type token STOPS linking ----
    {
        "id": "weak-type-link-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # The type token is built under the ABSENT role, collapsing it to a
        # plain emphasis node with no cross-reference.
        "module": _swap(
            _BASE, _I_TYPEAPP,
            '  par := par ++ [makeXref "" (RenderNode.emph t)]'),
        "refinement": "building the type token under the absent role "
                      "corresponds to a real patch that ALSO dropped the type "
                      "cross-reference role from the same field configuration. "
                      "The F2P test asserts the type child is a cross-reference "
                      "wrapping an emphasis token, and separately asserts that "
                      "cross-reference's reference type and target; a bare "
                      "emphasis node fails both — so the faithful patch would "
                      "NOT resolve.",
        "rationale": "REJECT from C-type: the spec pins the type child to "
                     "`xref variableTypeRole (emph t)`, the rival emits a bare "
                     "`emph t`. This is the clause that stops a rival from "
                     "satisfying the spec by ALSO un-linking the type token. "
                     "Refuted at name=\"x\", type=\"T\" and an EMPTY description "
                     "(so the violation is attributed to the type child, not to "
                     "the tail). If it verified, SPEC-TOO-WEAK. Ports nagini's "
                     "rival-drop-type-link (U2).",
        "witness": _w('"x"', '(some "T")', "[]"),
    },

    # ---- near-miss of the above: it links, under a different role ----
    {
        "id": "weak-type-reftype-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS of `weak-type-link-dropped`: the type token still gets a
        # cross-reference (so the node KIND is right), but it carries the wrong
        # reference type. Given its own witness rather than sharing, because it
        # agrees with gold over strictly more of the surface.
        "module": _swap(
            _BASE, _I_TYPEAPP,
            '  par := par ++ [makeXref "obj" (RenderNode.emph t)]'),
        "refinement": "a type cross-reference built with the wrong reference "
                      "type is a real patch that mis-configured the type role. "
                      "The F2P test asserts the type child's reference type "
                      "explicitly, in a separate assertion from the child "
                      "sequence, so a cross-reference of the right SHAPE but the "
                      "wrong reference type still FAILS — the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C-type on the ROLE it carries, not on the node "
                     "kind: the spec pins `xref variableTypeRole (emph t)` and "
                     "the rival emits `xref` of a different role. A NEAR-MISS of "
                     "weak-type-link-dropped (the cross-reference wrapper is "
                     "present here), so it gets its OWN witness at a distinct "
                     "point — name=\"attr\", type=\"int\", a two-node "
                     "mixed-constructor description — rather than sharing one. "
                     "Ports nagini's rival-makexref-reftype-mask (U5), which "
                     "there attacks the helper's own reftype clause X2; this "
                     "bundle has no separate helper obligation, so the same "
                     "corruption is attacked where the helper is applied.",
        "witness": _w('"attr"', '(some "int")',
                      '[RenderNode.text "a", RenderNode.emph "b"]'),
    },

    # ---- positional attack: the name token emitted after the open paren ----
    {
        "id": "weak-token-order",
        "kind": "uniqueness",
        "expect": "reject",
        # The name token is moved AFTER the parenthesized type group, so the
        # sequence opens with `text " ("` and the name lands between the type
        # group and the separator.
        "module": _swaps(
            _BASE,
            (_I_NAMEAPP, ""),
            (_I_SEP, _I_NAMEAPP.rstrip("\n") + "\n" + _I_SEP),
        ),
        "refinement": "emitting the name token after the parenthesized type "
                      "group is a real renderer that appended the item's tokens "
                      "in the wrong order. The F2P test pins the item's child "
                      "SEQUENCE position by position — name token, \" (\", type "
                      "cross-reference, \")\", separator, description — so a "
                      "reordered sequence FAILS on the first child alone. The "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from the POSITIONAL content of the spec equation: "
                     "C-head demands the head node be `strong name`, but the "
                     "rival's head is `text \" (\"`, and the name token appears "
                     "where C-tail demands the separator. Refuted at name=\"n\", "
                     "type=\"C\", a one-node description built from a different "
                     "constructor than the other witnesses use. If it verified, "
                     "the spec would not pin token order (SPEC-TOO-WEAK). Ports "
                     "nagini's rival-order-swap (U3).",
        "witness": _w('"n"', '(some "C")', '[RenderNode.strong "d"]'),
    },

    # ---- the role-application decision inverted between the two tokens ----
    {
        "id": "weak-role-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # The two roles are exchanged: the name token gets the type role (so it
        # links) and the type token gets the absent role (so it does not). The
        # observable effect of reading the role-application decision backwards.
        "module": _swaps(
            _BASE,
            (_I_NAMEAPP,
             "  par := par ++ [makeXref variableTypeRole "
             "(RenderNode.strong name)]\n"),
            (_I_TYPEAPP, "  par := par ++ [makeXref nameRole "
                         "(RenderNode.emph t)]"),
        ),
        "refinement": "exchanging the two roles is the renderer testing the "
                      "role-application condition backwards: it would link the "
                      "token that must stand alone and un-link the token that "
                      "must navigate. The F2P test observes exactly the opposite "
                      "pair — a plain name child and a class-typed "
                      "cross-reference type child — so BOTH assertions fail and "
                      "the faithful patch would NOT resolve.",
        "rationale": "REJECT from C-head AND C-type simultaneously: the head "
                     "becomes a cross-reference where the spec demands a plain "
                     "strong token, and the type child becomes a bare emphasis "
                     "node where the spec demands a cross-reference. Refuted at "
                     "name=\"attr\", type=\"cls\", a two-node all-`text` "
                     "description. If it verified, SPEC-TOO-WEAK. Ports nagini's "
                     "rival-makexref-invert (U4), which there attacks the "
                     "helper's own node-kind clause X1; with no separate helper "
                     "obligation here, the inversion is attacked through its "
                     "effect on both applied tokens.",
        "witness": _w('"attr"', '(some "cls")',
                      '[RenderNode.text "z", RenderNode.text "w"]'),
    },

    # ---- post-hoc overwrite of the (correct) name token ----
    {
        "id": "weak-relink-after",
        "kind": "uniqueness",
        "expect": "reject",
        # Builds the CORRECT sequence, then overwrites element 0 with a linking
        # node after the fact. Confirms the spec pins the returned value's FINAL
        # contents, not a transient the impl passed through.
        "module": _swap(
            _BASE, _I_TAIL,
            """  par := par ++ content
  par := par.set 0 (makeXref variableTypeRole (RenderNode.strong name))
  return par"""),
        "refinement": "an implementation that ENDS UP with a linking name token "
                      "— by any route, a post-hoc rewrite of the assembled "
                      "sequence included — renders the item's name child as a "
                      "cross-reference. The F2P test asserts that child is a "
                      "plain strong node, so it FAILS regardless of how the node "
                      "got there; the faithful patch would NOT resolve.",
        "rationale": "REJECT from C-head evaluated on the RETURNED value rather "
                     "than on a transient: the spec is an equality on the "
                     "function's result, so a correct sequence that is "
                     "subsequently overwritten is still wrong. Refuted at "
                     "name=\"flag\", type=\"bool\", a one-node emphasis "
                     "description. Ports nagini's rival-result-mutate (U6), "
                     "which stands in there for the inapplicable frame lane; "
                     "expressed here as a rewrite of the accumulated list, since "
                     "this carrier has no in-place element assignment.",
        "witness": _w('"flag"', '(some "bool")', '[RenderNode.emph "q"]'),
    },

    # ---- NEW (no nagini counterpart): the type-ABSENT arm ----
    {
        "id": "weak-none-arm-parens",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the branch arm the nagini rivals never reach: nagini's entry
        # builder always emits two tokens, so it has no type-absent case. Here
        # the rival emits an EMPTY parenthesis pair when no type token is
        # present, and is correct on the whole type-present sub-domain.
        "module": _swap(
            _BASE, _I_NONEARM,
            """  | none =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [RenderNode.text ")"]"""),
        "refinement": "a renderer that emitted the parentheses unconditionally "
                      "would decorate a type-less documented item with an empty "
                      "\" (\" \")\" pair. HONEST SCOPE (corrected by audit): the "
                      "F2P item HAS a type and so does every item in the "
                      "surrounding field-list regression test, so NO test in "
                      "either the F2P or the P2P list observes a type-less item "
                      "— this rival's faithful patch would in fact still "
                      "resolve. The case is therefore NOT justified by "
                      "refinement-to-a-failing-test; it is retained on the "
                      "narrower and honest ground that the spec's `none` arm is "
                      "a clause the modeled behavior asserts (emit the "
                      "parenthesized group ONLY when a type is present), and a "
                      "battery that left that arm unprobed would report full "
                      "coverage of an equation one of whose two branches no case "
                      "constrains. Read it as a spec-coverage case, not as a "
                      "would-not-resolve case.",
        "rationale": "REJECT from C-none, the branch arm no nagini rival "
                     "reaches: the spec pins the type-absent result to head, "
                     "separator, content with NO parenthesized group, while the "
                     "rival inserts two extra nodes. This is the coverage gap "
                     "the port adds — every other rival probes the "
                     "type-present arm, so without it a rival that mishandled "
                     "only `type? = none` would verify unnoticed. Refuted at "
                     "type?=none with a one-node description.",
        "witness": _w('"attr"', "none", '[RenderNode.text "d"]'),
    },

    # ---- NEW (no nagini counterpart): the description pass-through ----
    {
        "id": "weak-content-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C-tail's frame discipline: the description fragment must be
        # passed through VERBATIM. The rival drops its first node. Nagini's model
        # has no description input at all (its entry is just the two tokens), so
        # this clause is unattacked by the sibling battery.
        "module": _swap(_BASE, _I_CONTENT,
                        "  par := par ++ content.drop 1\n"),
        "refinement": "a renderer that dropped the first node of the description "
                      "fragment would truncate the documented variable's "
                      "description text. The F2P test pins the description as "
                      "the item's final child, so it FAILS — the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C-tail: the spec pins `content` to appear "
                     "VERBATIM after the separator (frame discipline on the "
                     "pass-through input), and the rival emits a truncated "
                     "fragment. Attacks the third binder, which no other rival "
                     "corrupts — without it a rival that mishandled only the "
                     "description would verify. Refuted at type?=none with a "
                     "non-empty description, so the violation is attributed to "
                     "the tail rather than to the type group.",
        "witness": _w('"attr"', "none", '[RenderNode.text "blah blah"]'),
    },
]

# The axiom lane is G-AX's job and this gate ignores it. The bundle declares no
# `opaque` callee and consumes no `axiom` (the role-application helper is modeled
# deeply, A-reference), so nagini's already-empty AXIOM_TESTS carries over as
# nothing at all.
AXIOM_TESTS = []
