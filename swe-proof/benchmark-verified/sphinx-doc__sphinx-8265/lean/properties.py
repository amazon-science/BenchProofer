"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8265 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside an ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the matching ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and BOTH
``theorem correct_tupleDisplay`` / ``theorem correct_subscription`` STATEMENTS
stay byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed, no ``sorry``/``admit``/
``native_decide``, no new ``axiom``/``theorem``/``lemma``); ``expect:"reject"``
passes iff (in scope AND it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the same two pure renderers over immutable integer code-point sequences;
this Lean bundle models them over ``List Char``, and the index-shape argument
triple that nagini spells as ``(elts, index_is_member_group, slice_rendered)``
plus a guarding precondition is carried here by a single ``IndexForm`` sum, so
the nagini precondition ``group ⟹ len(elts) > 0`` is discharged BY THE TYPE
rather than by a hypothesis (see ``assessment`` / the accounting block). Every
nagini SPEC case has a counterpart below; the nagini frame-mutation and
ungrounded-oracle lanes are vacuous here for the same reasons they were vacuous
there, plus referential transparency (see the class read-out below).

DEFENDED SURFACE (two modeled behaviors, four independent branch clauses).

``problem_spec_tupleDisplay elts result`` — a single equality whose right-hand
side is a two-way conditional on the one input binder, so it carries two
independent sub-domains:

  * (T-EMPTY) ``elts = []``  ⟹ ``result = ['(', ')']`` — the empty grouping;
  * (T-FULL)  ``elts ≠ []``  ⟹ ``result = ['('] ++ intercalate [',',' '] elts
    ++ [')']`` — the components joined by ``", "`` and enclosed in a MATCHING
    pair of round brackets. Exactly one opener and exactly one closer: this is
    an EXACT structural equality, not a prefix/containment test.

``problem_spec_subscription valueStr idx result`` — a single equality
concatenating three parts, so it carries three independently attackable
obligations over its two input binders:

  * (S-PREFIX) the result opens with ``valueStr`` and then ``'['``, and closes
    with ``']'`` — the subscripted value's own text is preserved verbatim, for
    BOTH index shapes;
  * (S-GROUP)  ``idx = .elementTuple elts`` ⟹ the bracketed text is
    ``intercalate [',',' '] elts`` — the components listed DIRECTLY between the
    brackets, with NO extra surrounding grouping of their own;
  * (S-PLAIN)  ``idx = .plain rendered`` ⟹ the bracketed text is ``rendered``
    unchanged.

Both postconditions are GROUNDED in their inputs: the right-hand side is a total
function of ``elts`` / ``(valueStr, idx)`` built from ``List.intercalate`` and
``++``. There is no opaque answer key, so ``decide`` computes both sides at a
concrete input and every witness below is a literal-input refutation with an
EMPTY binder head — no hypothesis whose consistency could be in question.

BINDER STRUCTURE. Three input binders across the two predicates: ``elts``
(``tupleDisplay``), ``valueStr`` and ``idx`` (``subscription``). All three are
load-bearing and all three are VARIED by the reject witnesses — ``elts`` ranges
over empty / one-component / two-component / three-component; ``valueStr`` over
three distinct non-empty texts; ``idx`` over both constructors with differing
payloads, including a three-component grouping payload. The eight reject
witnesses probe eight DISTINCT input points (``pts=8``); see the point-spread
block at the bottom.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already records
    this class as non-existent on its surface: every input is an immutable value
    sequence with no write permission and no mutating operation, so there is no
    read-only cell a rival could overwrite. On this referentially transparent
    carrier it is doubly vacuous — ``elts`` / ``valueStr`` / ``idx`` are
    immutable values, there is no ``mut`` input binder and no aliasing. No
    substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the sibling's own reason: the only
    oracle in either postcondition is the comma-and-space join, which is a pure
    function OF THE INPUT. Echoing it IS doing the work; there is no answer-key
    marker a wrong implementation could parrot. In its place the battery carries
    the honest cheapest-implementation POSITIVE CONTROLS that must verify
    (``pos-tuple-branchless``, ``pos-subscript-prefix``).

  * CONTROL-FLOW EFFECT — VACUOUS. Both modeled behaviors are total pure value
    functions; the returned text is the entire observable, so nothing is
    invisible to the value abstraction.

  * DIVERGENCE / NON-TERMINATION — VACUOUS ON THIS BACKEND. Each
    ``implementation_*`` is a total Lean ``def``, so a diverging rival cannot be
    written at all: there is no partial-semantics escape hatch under which a
    non-terminating implementation would satisfy the postcondition vacuously.
    This is a genuine collapse of the class, NOT the known spec hole that the
    same lane exposes on a partial-semantics backend.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole live attack surface. Both
    postconditions are branch-guarded, so a rival can be right on one sub-domain
    and wrong on the other. The eight rivals below split as: three attacking
    T-FULL (bare join with no enclosing brackets; an unmatched extra closer; a
    join separator missing its space), one attacking T-EMPTY (the empty grouping
    truncated to a single opener), TWO attacking S-GROUP (the listed components
    given an extra enclosing grouping of their own; the listed components joined
    without the separator space), one attacking S-PLAIN (the bracketed text
    dropped entirely), and one attacking S-PREFIX (the subscripted value's own
    text dropped).

RESOLVE-DISCRIMINATION, MEASURED (audit). Every rival's `refinement` claim was
checked, not argued: each rival's faithful real counterpart was built as a
rendering variant and run against EVERY shipped rendering row. Seven of the
eight fail at least one row, so their refinement claims hold. ONE does not —
`weak-subscript-drop-plain`, whose counterpart passes every row, because the
shipped rows contain exactly one subscription and its index is a multi-component
grouping, so no row exercises the plain-index shape. That case's refinement now
says so in its own field and the case is retained on stated spec-strength
grounds rather than on a resolve claim. Two further refinement notes
(`weak-tuple-separator`, `weak-subscript-drop-value`) claimed a row SPREAD the
row set does not contain and were narrowed to the single row each actually
breaks. Do not restore the broader wording: the row set has one grouping-display
row, one empty-grouping row, and one subscription row.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen tactic script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. (Every rival below
does in fact break the frozen script, and the recorded error is an unsolved
goal, exactly what a merely-RESHAPED correct implementation would also produce.)
Every ``expect="reject"`` case therefore carries a Lean snippet that states the
NEGATION of the spec predicate, applied to the rival's own output, at ONE
concrete literal input, closed by ``unfold``+``decide``. Each was checked with
two real ``lake env lean`` builds: it ELABORATES against its rival and FAILS on
the frozen solution, so it discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
renderer that emits the wrong text for a concrete source construct appearing in
the F2P / P2P rendering rows, so that row's expected round-trip text would
mismatch and the faithful patch would NOT resolve. Every one of those arguments
has now been MEASURED (see RESOLVE-DISCRIMINATION above), and the single case
whose counterpart is not row-discriminated says so in its own ``refinement``
rather than claiming a break it does not have.

SPEC PROBES RUN BY THE AUDIT (independent of the cases above; no hole found).
Seven further wrong implementations the battery does not contain were written and
built against the frozen spec — reversed component order; a missing OPENER
(rather than the missing pair); the empty grouping emitted as empty text (rather
than a lone opener); the subscripted value's text moved to the SUFFIX; round
brackets in place of the square subscript brackets; the grouping index rendered
THROUGH the parenthesizing display of the other modeled behavior; and one wrong
only at a mapping-unreachable index shape. All seven were REJECTED, each with a
fresh witness that refutes it and fails on the frozen solution, so no
SPEC-TOO-WEAK hole is reachable by those shapes. Four further CORRECT reshapes
were also built and all four VERIFIED — a `match` on the component list instead
of an equality test; a length-based guard; the subscription written as the spec's
own single concatenation; and a re-associated concatenation — so the spec pins
values rather than syntax and no SPEC-TOO-STRONG hole was found either.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (``meta.json``'s axiom list is empty); the axiom lane belongs to G-AX,
and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8265"
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
# Region anchors. Each lies ENTIRELY inside the region it names and is unique
# in Solution.lean (asserted by _swap at import time, so this manifest breaks
# loudly if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# --- tupleDisplay impl region ---
_T_IMPL = (
    "  if elts ≠ [] then\n"
    "    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']\n"
    "  else\n"
    "    return ['(', ')']\n")
# the two arms individually, for surgical single-sub-domain rivals
_T_ARM_FULL = "    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']\n"
_T_ARM_EMPTY = "    return ['(', ')']\n"

# --- tupleDisplay proof region ---
_T_PROOF = (
    "  intro elts\n"
    "  unfold problem_spec_tupleDisplay implementation_tupleDisplay\n"
    "  by_cases h : elts = []\n"
    "  · simp [h, Id.run, pure]\n"
    "  · simp [h, Id.run, pure]\n")

# --- subscription impl region ---
_S_IMPL = (
    "  match idx with\n"
    "  | .elementTuple elts =>\n"
    "      let inner := List.intercalate [',', ' '] elts\n"
    "      return valueStr ++ ['['] ++ inner ++ [']']\n"
    "  | .plain rendered =>\n"
    "      return valueStr ++ ['['] ++ rendered ++ [']']\n")
_S_INNER = "      let inner := List.intercalate [',', ' '] elts\n"
_S_RET_GROUP = "      return valueStr ++ ['['] ++ inner ++ [']']\n"
_S_RET_PLAIN = "      return valueStr ++ ['['] ++ rendered ++ [']']\n"

# --- subscription proof region: the intro line, so the admissibility positive
# can PREPEND a ground `have` without touching the theorem STATEMENT or the
# spec view.
_S_INTRO = "  intro valueStr idx\n"


# ---------------------------------------------------------------------------
# Witness scaffolds. Both predicates are total computable functions of their
# inputs, so a refutation at a concrete literal input is decidable outright:
# state ¬ spec of the rival's own output, unfold both, `decide`. Each witness
# head binds NOTHING (all inputs are ground literals), so there are no
# hypotheses whose joint satisfiability could be in question.
# ---------------------------------------------------------------------------
def _w_tuple(elts):
    """Refute `problem_spec_tupleDisplay` at the concrete component list `elts`."""
    return (
        f"example : ¬ problem_spec_tupleDisplay {elts}\n"
        f"    (implementation_tupleDisplay {elts}) := by\n"
        "  unfold problem_spec_tupleDisplay implementation_tupleDisplay\n"
        "  decide\n")


def _w_sub(value, idx):
    """Refute `problem_spec_subscription` at the concrete `(value, idx)` point."""
    return (
        f"example : ¬ problem_spec_subscription {value} ({idx})\n"
        f"    (implementation_subscription {value} ({idx})) := by\n"
        "  unfold problem_spec_subscription implementation_subscription\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps both
    # `correct_*` STATEMENTS byte-identical and adds no declaration.
    # =====================================================================
    {
        "id": "pos-tuple-branchless",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest implementation: no case split at all. The join of an
        # empty component list is empty, so enclosing it in the bracket pair
        # already yields the empty grouping — one expression covers BOTH
        # sub-domains. The frozen proof still case-splits, but the empty arm now
        # needs the join's own base equation to reduce, so the proof body is
        # re-proved by handing `simp` that unfolding on the empty branch. The
        # theorem statement is byte-identical and nothing is assumed.
        # (Verified: real build, exit 0.)
        "module": _swaps(
            _BASE,
            (_T_IMPL,
             "  return ['('] ++ List.intercalate [',', ' '] elts ++ [')']\n"),
            (_T_PROOF,
             "  intro elts\n"
             "  unfold problem_spec_tupleDisplay implementation_tupleDisplay\n"
             "  by_cases h : elts = []\n"
             "  · simp [h, Id.run, pure, List.intercalate]\n"
             "  · simp [h, Id.run, pure]\n"),
        ),
        "rationale": "the cheapest honest implementation builds the enclosed join "
                     "unconditionally, with NO case split: the join of an empty "
                     "component list is empty, so the single expression already "
                     "yields the empty grouping. It agrees with the spec on BOTH "
                     "sub-domains (T-EMPTY and T-FULL) and MUST verify — else "
                     "SPEC-TOO-STRONG, i.e. the postcondition would be demanding a "
                     "branch structure rather than a value. Re-proved inside the "
                     "proof region by giving `simp` the join's base equation on the "
                     "empty branch; statement byte-identical, no new "
                     "axiom/theorem/lemma. Ports nagini's pos-tuple-cheapest, which "
                     "also covers the (vacuous) ungrounded-oracle lane: the join is "
                     "grounded in the input, so the cheapest faithful implementation "
                     "IS correct.",
    },
    {
        "id": "pos-tuple-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch REORDER: test the empty sub-domain FIRST (positively, `= []`
        # rather than `≠ []`), non-empty in the else. Same values, mirrored
        # control flow. The frozen proof's `by_cases` closes both arms unchanged.
        # (Verified: real build, exit 0.)
        "module": _swap(
            _BASE, _T_IMPL,
            "  if elts = [] then\n"
            "    return ['(', ')']\n"
            "  else\n"
            "    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']\n"),
        "rationale": "branch-REORDER positive control: the empty sub-domain is "
                     "tested first and positively, the non-empty one in the else — "
                     "identical values on every input, mirrored control flow. A "
                     "faithful reshape MUST verify, else SPEC-TOO-STRONG. No proof "
                     "authoring was needed (the frozen `by_cases` closes both arms), "
                     "so the proof region is untouched and both statements stay "
                     "byte-identical. Ports nagini's pos-tuple-reorder.",
    },
    {
        "id": "pos-subscript-prefix",
        "kind": "soundness",
        "expect": "verify",
        # subscription reshape: hoist the common `valueStr ++ ['[']` opening into
        # a local BEFORE the case split, swap the two arms (plain first), and drop
        # the intermediate `inner` local on the grouping arm. Same value, three
        # simultaneous shape changes. The frozen `cases` proof closes both arms.
        # (Verified: real build, exit 0.)
        "module": _swap(
            _BASE, _S_IMPL,
            "  let pre := valueStr ++ ['[']\n"
            "  match idx with\n"
            "  | .plain rendered =>\n"
            "      return pre ++ rendered ++ [']']\n"
            "  | .elementTuple elts =>\n"
            "      return pre ++ List.intercalate [',', ' '] elts ++ [']']\n"),
        "rationale": "correct reshape of the subscription renderer: the common "
                     "opening (the subscripted value's text followed by '[') is "
                     "hoisted into a local before the case split, the two index "
                     "shapes are handled in the opposite order, and the "
                     "intermediate local on the grouping arm is dropped. Identical "
                     "value on every input, so S-PREFIX / S-GROUP / S-PLAIN all "
                     "still hold and it MUST verify — else SPEC-TOO-STRONG (the "
                     "postcondition would be pinning the association/order of the "
                     "concatenation rather than the text). The frozen `cases` proof "
                     "closes both arms unchanged; statements byte-identical, "
                     "nothing assumed. Ports nagini's pos-subscript-prefix.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
    # F2P/P2P-shaped input. The nagini sibling's admissibility case is a
    # positive-control CALLER establishing the subscription renderer's guarding
    # precondition for a legitimate in-domain input. This carrier has no such
    # precondition to establish — the index-shape guard is carried by the sum
    # type — so the honest analogue is to DISCHARGE the postcondition by
    # evaluation at exactly that in-domain input (a two-component grouping index
    # over a non-empty subscripted-value text) as a `have`, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, both
    # statements byte-identical, the ground instance is a `have` prepended inside
    # the existing tactic body. (Verified: real build, exit 0.)
    # =====================================================================
    {
        "id": "admiss-subscript-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _S_INTRO,
            "  have _ground : problem_spec_subscription ['T', 'p']\n"
            "      (.elementTuple [['i', 'n', 't'], ['s', 't', 'r']])\n"
            "      (implementation_subscription ['T', 'p']\n"
            "        (.elementTuple [['i', 'n', 't'], ['s', 't', 'r']])) := by\n"
            "    unfold problem_spec_subscription implementation_subscription\n"
            "    decide\n"
            + _S_INTRO),
        "rationale": "the subscription obligation is discharged BY EVALUATION at the "
                     "smallest P2P-shaped in-domain input — a non-empty subscripted "
                     "value text with a two-component grouping index — as a `have`, "
                     "then the frozen obligation is closed verbatim. It verifies, so "
                     "the modeled behavior is satisfiable at exactly a normal input "
                     "(the analogue of nagini's PRECOND-TOO-STRONG probe: if the "
                     "in-domain point were excluded or the postcondition "
                     "unsatisfiable there, this `have` could not close). Re-expresses "
                     "nagini's admiss-subscript-precond, whose caller-side "
                     "precondition has no counterpart here — the index-shape guard "
                     "is discharged by the sum type. Nothing is assumed: no new "
                     "declaration, statements byte-identical.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P /
    # P2P rows, and (b) a witness pinning the violation at one concrete input,
    # SEEN to hold of the rival and to fail on the frozen solution.
    # =====================================================================

    # ---- T-FULL: the enclosing bracket pair is missing entirely ----
    {
        "id": "weak-tuple-bare-join",
        "kind": "uniqueness",
        "expect": "reject",
        # The reported defect: a non-empty multi-component grouping renders as the
        # BARE comma-and-space join, with no enclosing bracket pair. Correct on
        # the empty sub-domain, wrong on the non-empty one.
        "module": _swap(
            _BASE, _T_ARM_FULL,
            "    return List.intercalate [',', ' '] elts\n"),
        "refinement": "this IS the reported behavior: a multi-component grouping is "
                      "emitted as the bare comma-and-space join of its components "
                      "with no enclosing bracket pair, so a three-component grouping "
                      "used as a default value renders as three separate "
                      "comma-separated items and the surrounding argument list is "
                      "silently reshaped — exactly the rendering the problem "
                      "statement contrasts against its expected output. Its faithful "
                      "real counterpart is the unchanged pre-fix renderer, which "
                      "emits the bare join and therefore FAILS the F2P rendering row "
                      "asserting that a three-component grouping round-trips to "
                      "itself. So if this rival verified, that would be a genuine "
                      "verify-without-resolve break.",
        "rationale": "REJECT from T-FULL: the spec pins `['('] ++ intercalate "
                     "[',',' '] elts ++ [')']` on the non-empty sub-domain but the "
                     "rival emits the join alone, which differs for EVERY non-empty "
                     "`elts` (the two texts differ already at their first "
                     "character). Correct on T-EMPTY, so this is a partial-domain "
                     "rival pinning only the empty half. Refuted at the "
                     "three-component grouping `elts` = three single-character "
                     "components — the shape the F2P row exercises.",
        "witness": _w_tuple("[['1'], ['2'], ['3']]"),
    },

    # ---- T-EMPTY: the empty grouping loses its closer ----
    {
        "id": "weak-tuple-empty-unclosed",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual partial-domain rival: correct on every non-empty grouping, but
        # the EMPTY grouping renders as a lone opener instead of the matched pair.
        "module": _swap(_BASE, _T_ARM_EMPTY, "    return ['(']\n"),
        "refinement": "correct on every non-empty grouping but renders the EMPTY "
                      "grouping as a lone opening bracket instead of the matched "
                      "empty pair, emitting syntactically unbalanced text. Its "
                      "faithful real counterpart would FAIL the P2P rendering row "
                      "that round-trips the empty grouping to itself (and would emit "
                      "unbalanced output wherever an empty grouping appears nested), "
                      "so the faithful patch would NOT resolve. A partial-domain "
                      "rival pinning only the non-empty half of the domain.",
        "rationale": "REJECT from T-EMPTY: the spec pins `result = ['(', ')']` when "
                     "`elts = []` but the rival emits `['(']`. Correct on T-FULL. "
                     "Refuted at the one input in that sub-domain, `elts = []` — the "
                     "only witness exercising the empty component list, which is why "
                     "it cannot share a witness with any other rival.",
        "witness": _w_tuple("[]"),
    },

    # ---- T-FULL: an unmatched extra closer (exactness of the equality) ----
    {
        "id": "weak-tuple-extra-closer",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on the SAME sub-domain as weak-tuple-bare-join but agreeing
        # with gold over strictly more of the text: the enclosing pair is present,
        # yet a redundant SECOND closer is appended.
        "module": _swap(
            _BASE, _T_ARM_FULL,
            "    return ['('] ++ List.intercalate [',', ' '] elts ++ [')', ')']\n"),
        "refinement": "near-miss: a non-empty grouping is correctly opened and "
                      "joined but gains a redundant SECOND closing bracket, so the "
                      "emitted text is unbalanced. Its faithful real counterpart "
                      "would render a three-component grouping with a trailing extra "
                      "closer and FAIL the same F2P rendering row, so the faithful "
                      "patch would NOT resolve. Its independent value is that it "
                      "confirms the postcondition is an EXACT structural equality — "
                      "a prefix or containment check would admit it.",
        "rationale": "REJECT from T-FULL: the spec's right-hand side carries exactly "
                     "ONE closing bracket, the rival two, so the two texts differ in "
                     "length for every non-empty `elts`. This is a NEAR-MISS of "
                     "weak-tuple-bare-join (it agrees with gold on the opener and the "
                     "whole join, diverging only at the tail), so it gets its OWN "
                     "witness at a distinct, minimal point — a SINGLE-component "
                     "grouping, where the join performs no separator work at all and "
                     "the only remaining difference is the extra closer. That input "
                     "isolates exactly the sub-domain this rationale claims.",
        "witness": _w_tuple("[['x']]"),
    },

    # ---- T-FULL: the join separator loses its space ----
    {
        "id": "weak-tuple-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Third T-FULL rival, attacking the SEPARATOR rather than the enclosure:
        # components are joined by a bare comma with no following space. Agrees
        # with gold on every grouping of fewer than two components.
        "module": _swap(
            _BASE, _T_ARM_FULL,
            "    return ['('] ++ List.intercalate [','] elts ++ [')']\n"),
        "refinement": "joins the components with a bare comma and no following "
                      "space. Its faithful real counterpart emits a grouping whose "
                      "components are run together, so a multi-component grouping "
                      "round-trips to text that differs from its source by the "
                      "missing separator spaces and FAILS the F2P rendering row "
                      "(which asserts the exact source text, spaces included) — "
                      "measured by building the counterpart and running every row: "
                      "the three-component grouping row renders without its "
                      "separator spaces. So the faithful patch would NOT resolve. "
                      "SCOPE CORRECTION (audit): an earlier version of this note "
                      "added 'as well as every P2P row containing a multi-component "
                      "grouping'. That overreached — the only other row with a "
                      "multi-component grouping carries it as a SUBSCRIPTION INDEX, "
                      "which the other modeled behavior renders, so this rival leaves "
                      "that row passing. One F2P row is the honest count.",
        "rationale": "REJECT from T-FULL, attacking the SEPARATOR sub-structure the "
                     "other two T-FULL rivals leave intact: the spec pins the "
                     "two-character separator, the rival emits one character. "
                     "Correct on T-EMPTY and, unlike the other T-FULL rivals, ALSO "
                     "correct on every single-component grouping — so it needs a "
                     "witness with at least TWO components, which is why it does not "
                     "share the single-component point used by "
                     "weak-tuple-extra-closer nor the three-component point used by "
                     "weak-tuple-bare-join. Refuted at a two-component grouping.",
        "witness": _w_tuple("[['a'], ['b']]"),
    },

    # ---- S-GROUP: the listed components gain their own enclosing grouping ----
    {
        "id": "weak-subscript-inner-group",
        "kind": "uniqueness",
        "expect": "reject",
        # The coupling defect: on the grouping-index shape the bracketed text
        # keeps an inner enclosing pair, so the components are presented as ONE
        # grouped argument instead of listed directly. Correct on `.plain`.
        "module": _swap(
            _BASE, _S_INNER,
            "      let inner := ['('] ++ List.intercalate [',', ' '] elts "
            "++ [')']\n"),
        "refinement": "on a multi-component grouping index the components are given "
                      "an extra enclosing pair of their own, so a subscription whose "
                      "index lists several components renders as a single grouped "
                      "argument rather than several separate ones. Its faithful real "
                      "counterpart is the pre-fix subscription renderer, which — "
                      "once a multi-component grouping is enclosed at the other "
                      "modeled site — emits the extra enclosure inside the brackets "
                      "and FAILS the P2P rendering row that round-trips a "
                      "two-component subscription index to itself. This is the "
                      "coupling between the two modeled behaviors, and a verifying "
                      "rival here would be a genuine verify-without-resolve break.",
        "rationale": "REJECT from S-GROUP: the spec pins the bracketed text as "
                     "`intercalate [',',' '] elts` with NO surrounding grouping, but "
                     "the rival wraps it, so the two results differ for every "
                     "`.elementTuple` index. Correct on S-PLAIN and on S-PREFIX, so "
                     "this is a partial-domain rival pinning only the plain-index "
                     "half. Refuted at a two-component grouping index over a "
                     "single-character subscripted-value text.",
        "witness": _w_sub("['T']", ".elementTuple [['a'], ['b']]"),
    },

    # ---- S-GROUP: the listed components lose their separator space ----
    # ADDED BY AUDIT. The battery attacked the separator on tupleDisplay
    # (weak-tuple-separator) but not on subscription, whose S-GROUP clause pins
    # the SAME two-character separator independently: weak-subscript-inner-group
    # only wraps the join, so an implementation that got the subscription
    # separator wrong while keeping the enclosure right had no rival. This is
    # also the only added rival whose faithful counterpart is discriminated by
    # the one shipped subscription rendering row.
    {
        "id": "weak-subscript-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S_INNER,
            "      let inner := List.intercalate [','] elts\n"),
        "refinement": "on the grouping-index shape the listed components are joined "
                      "by a bare comma with no following space, so a subscription "
                      "whose index lists several components round-trips to text that "
                      "differs from its source by the missing separator spaces. "
                      "Measured by building the faithful counterpart and running "
                      "every shipped rendering row: the subscription row fails "
                      "(its two components come back run together), so the faithful "
                      "patch would NOT resolve. Correct on S-PREFIX and S-PLAIN, and "
                      "correct on the OTHER modeled behavior — the separator is "
                      "pinned twice over, and this is the copy no other rival "
                      "attacked.",
        "rationale": "REJECT from S-GROUP, attacking the separator sub-structure that "
                     "weak-subscript-inner-group leaves intact: the spec pins the "
                     "bracketed text as `intercalate [',',' '] elts`, the rival emits "
                     "a one-character separator. Correct on every grouping index of "
                     "fewer than two components (and on both other clauses), so it "
                     "needs a witness with at least TWO components; refuted at a "
                     "THREE-component grouping index over a two-character "
                     "subscripted-value text — an eighth distinct input point, and "
                     "the only one pairing a multi-character `valueStr` with the "
                     "grouping constructor. Witness checked with two real builds: "
                     "exit 0 against the rival, exit 1 on the frozen solution, where "
                     "`decide` PROVES the negation false (a semantic refutation, not "
                     "a stuck reduction).",
        "witness": _w_sub("['T', 'p']", ".elementTuple [['i'], ['j'], ['k']]"),
    },

    # ---- S-PLAIN: the bracketed text is dropped ----
    {
        "id": "weak-subscript-drop-plain",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: correct on the grouping-index shape, but a plain index loses
        # its own text entirely, emitting empty brackets.
        "module": _swap(
            _BASE, _S_RET_PLAIN,
            "      return valueStr ++ ['['] ++ [']']\n"),
        "refinement": "a plain (non-grouping) index loses its rendered text "
                      "entirely, so the subscription is emitted with empty brackets: "
                      "every subscription whose index is not a multi-component "
                      "grouping — a single name, a literal, a slice — renders with "
                      "nothing between the brackets. HONEST SCOPE (audit-corrected, "
                      "measured rather than argued): this rival's faithful real "
                      "counterpart is NOT resolve-discriminated by the shipped "
                      "F2P/P2P rendering rows. An earlier version of this note "
                      "claimed it would FAIL 'every P2P rendering row of that shape'; "
                      "that was checked by building the counterpart and running every "
                      "row, and it passes all of them — the shipped rows contain "
                      "exactly ONE subscription and its index is a multi-component "
                      "grouping, so no row exercises the plain-index shape at all. "
                      "The case is retained as a genuine SPEC-TOO-WEAK probe (the "
                      "rival is observably wrong, and its witness is a real "
                      "discriminator: it refutes the rival and `decide` proves the "
                      "negation false on the frozen solution), and because S-PLAIN is "
                      "otherwise the one clause of this postcondition no rival would "
                      "attack. Its divergence is real behavior and IS caught "
                      "out-of-band: the plain shape is the MAJORITY of the "
                      "differential conformance generator's subscription draws "
                      "(measured 11244 plain vs 3453 grouping over 40k), so the R/I "
                      "leg would refute the counterpart even though the row set does "
                      "not. Read this case as spec-strength evidence, not as a "
                      "verify-without-resolve break.",
        "rationale": "REJECT from S-PLAIN: the spec pins the bracketed text as "
                     "`rendered` but the rival emits nothing, so the two differ "
                     "whenever the index's own text is non-empty. Correct on S-GROUP "
                     "and on S-PREFIX. Refuted at a plain index with a multi-"
                     "character rendered text, over a MULTI-character "
                     "subscripted-value text — a distinct point from every other "
                     "witness in both binders.",
        "witness": _w_sub("['z', '.', 'q']", ".plain ['1', ':', '2']"),
    },

    # ---- S-PREFIX: the subscripted value's own text is dropped ----
    {
        "id": "weak-subscript-drop-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the clause BOTH nagini rivals leave intact (they only ever
        # touched the bracketed body): the subscripted value's own text is dropped
        # on BOTH index shapes, so only the bracketed part survives.
        "module": _swaps(
            _BASE,
            (_S_RET_GROUP, "      return ['['] ++ inner ++ [']']\n"),
            (_S_RET_PLAIN, "      return ['['] ++ rendered ++ [']']\n"),
        ),
        "refinement": "drops the subscripted value's own already-rendered text, "
                      "emitting only the bracketed index. Its faithful real "
                      "counterpart renders every subscription with its base "
                      "expression missing, and FAILS the P2P rendering row that "
                      "contains a subscription — the base text is asserted verbatim "
                      "in that expected round-trip. Measured by building the "
                      "counterpart and running every row: exactly that row fails, so "
                      "the faithful patch would NOT resolve. SCOPE CORRECTION "
                      "(audit): an earlier version said 'every P2P row that contains "
                      "a subscription (of either index shape)'. The shipped row set "
                      "has exactly ONE subscription row and its index is a "
                      "multi-component grouping, so 'either index shape' claimed a "
                      "row spread the manifest never demonstrates; the rival does "
                      "diverge on both shapes, but only the grouping shape is "
                      "row-observable. This rival exists because the spec's leading "
                      "`valueStr` is an independently attackable obligation that no "
                      "ported nagini rival targeted (see assessment).",
        "rationale": "REJECT from S-PREFIX: the spec pins `result = valueStr ++ "
                     "['['] ++ … ++ [']']`, i.e. the subscripted value's text is "
                     "preserved verbatim at the front for BOTH index shapes; the "
                     "rival omits it, so the results differ whenever `valueStr` is "
                     "non-empty — independent of `idx`. This is the only rival "
                     "attacking that clause, and the only one whose violation is "
                     "driven by the `valueStr` binder rather than by `idx`. Refuted "
                     "at a single-character plain index over a single-character "
                     "value text (a third distinct `valueStr`), the minimal point "
                     "where the omission is the ONLY difference.",
        "witness": _w_sub("['m']", ".plain ['k']"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (3 soundness
# positives, 1 admissibility, 5 uniqueness/partial-domain rivals) plus an EMPTY
# AXIOM lane. This bundle models the SAME two purely-functional renderers, so
# the carrier does NOT narrow here and every sibling case has a counterpart.
# Full accounting:
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-tuple-reorder            -> pos-tuple-reorder            PORTED
#   pos-tuple-cheapest           -> pos-tuple-branchless         PORTED (re-proved)
#   pos-subscript-prefix         -> pos-subscript-prefix         PORTED
#   admiss-subscript-precond     -> admiss-subscript-ground      RE-EXPRESSED
#   rival-tuple-bare-join        -> weak-tuple-bare-join         PORTED
#   rival-tuple-empty-open       -> weak-tuple-empty-unclosed    PORTED
#   rival-tuple-extra-paren      -> weak-tuple-extra-closer      PORTED
#   rival-subscript-inner-parens -> weak-subscript-inner-group   PORTED
#   rival-subscript-drop-body    -> weak-subscript-drop-plain    PORTED
#   (none)                       -> weak-tuple-separator         ADDED
#   (none)                       -> weak-subscript-drop-value    ADDED (S-PREFIX)
#   (none)                       -> weak-subscript-separator     ADDED BY AUDIT
#   AXIOM_TESTS (0)              -> (none)                       DROPPED (G-AX)
#
# NOTHING WAS OMITTED. Every sibling SPEC case is above; no rival was dropped
# for being unrefutable on this carrier and no soundness positive was dropped
# for a proof that would not close (all four positives were confirmed by a real
# `lake env lean` build at exit 0, and only pos-tuple-branchless needed any
# proof authoring — one extra `simp` lemma on its empty branch).
#
# RE-EXPRESSED (admiss-subscript-ground). The sibling's admissibility case is a
#   positive-control CALLER that establishes the subscription renderer's guarding
#   precondition (`grouping-index ⟹ at least one component`) for a legitimate
#   in-domain input, proving it is not PRECOND-TOO-STRONG. On this carrier that
#   precondition DOES NOT EXIST as a hypothesis: the index-shape guard is carried
#   by the `IndexForm` sum, and the invariant that a grouping index is non-empty
#   is a property of the mapping rather than a proof obligation — so there is no
#   `Requires` to admit and no call site to build. The honest analogue keeps the
#   PURPOSE (show the modeled behavior is satisfiable at exactly that in-domain
#   input, not vacuous there) and changes the mechanics: discharge the
#   postcondition by evaluation at that concrete point as a `have`, then close the
#   frozen obligation verbatim. Consequence to record: the nagini
#   PRECOND-TOO-STRONG failure mode is NOT REACHABLE on this bundle, because
#   neither frozen obligation carries a precondition binder at all. That is a
#   property of the carrier, not a gap in this battery.
#
# ADDED (weak-tuple-separator). The sibling's three tupleDisplay rivals all
#   attack the ENCLOSURE (missing pair / lone opener / extra closer) and leave
#   the separator intact, so no sibling rival would notice an implementation that
#   joined the components wrongly. Since the join is half of what T-FULL pins,
#   this rival attacks it directly. It also supplies the two-component witness
#   point, which no other case probes.
#
# ADDED (weak-subscript-drop-value). Both sibling subscription rivals rewrite
#   only the BRACKETED BODY, so the spec's leading `valueStr` — an independent
#   top-level obligation holding on both branches — went unattacked, and a rival
#   that mishandled only the subscripted value's own text would have verified
#   unnoticed. This is also the only rival whose violation is driven by the
#   `valueStr` binder rather than by `idx`, so without it `valueStr` would be a
#   binder no rival was built to abuse.
#
# VACUOUS CLASSES (no substitute probe fabricated for any of them):
#   * frame / permission mutation — the sibling already records this class as
#     non-existent on its own surface (immutable value inputs, no write
#     permission, no mutating operation); referential transparency here makes it
#     doubly so (no `mut` input binder, no aliasing, no read-only cell).
#   * ungrounded-oracle echo — both postconditions are grounded in their inputs;
#     the only oracle is the join, which is a pure function of `elts`, so there
#     is no answer key to echo. Covered instead by pos-tuple-branchless.
#   * control-flow effect — both behaviors are total pure value functions; the
#     returned text is the entire observable.
#   * divergence / non-termination — the sibling carries no such case, and on
#     this backend the class genuinely COLLAPSES rather than exposing a spec
#     hole: each `implementation_*` is a total Lean `def`, so a non-terminating
#     rival cannot be written, and there is no partial-semantics option under
#     which one would satisfy the postcondition vacuously. (Contrast a
#     partial-semantics backend, where the same lane is a KNOWN SPEC HOLE — see
#     the corpus-wide termination-semantics finding — not a vacuous class.)
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT input points
# (`pts=8`), and no binder is held fixed across them:
#
#   tupleDisplay (binder: elts)
#     [['1'], ['2'], ['3']]                 weak-tuple-bare-join        T-FULL
#     []                                    weak-tuple-empty-unclosed   T-EMPTY
#     [['x']]                               weak-tuple-extra-closer     T-FULL
#     [['a'], ['b']]                        weak-tuple-separator        T-FULL
#   subscription (binders: valueStr, idx)
#     ['T'],         .elementTuple [['a'],['b']]      weak-subscript-inner-group S-GROUP
#     ['T','p'],     .elementTuple [['i'],['j'],['k']] weak-subscript-separator  S-GROUP
#     ['z','.','q'], .plain ['1', ':', '2']           weak-subscript-drop-plain  S-PLAIN
#     ['m'],         .plain ['k']                     weak-subscript-drop-value  S-PREFIX
#
#   `elts` takes four distinct values spanning 0, 1, 2 and 3 components (so the
#   empty/non-empty guard AND the separator's arity dependence are both probed);
#   `valueStr` takes three distinct non-empty texts of two different lengths;
#   `idx` takes both constructors, with two different payloads on the `.plain`
#   side and a two-component payload on the grouping side. The three near-miss
#   relationships (bare-join vs extra-closer vs separator, all on T-FULL) are
#   each given their OWN point, at the minimal input that isolates the sub-domain
#   their rationale claims — no two rivals share a witness.
#
# WITNESS FORM. Every witness states `¬ problem_spec_<name> <literals>
# (implementation_<name> <literals>)` and closes with `unfold` + `decide`; both
# predicates are total computable functions of their inputs, so the carrier
# COMPUTES and no conditioning on an opaque term is needed. Consequently every
# witness head binds NOTHING — there are no hypotheses, hence no possibility of
# a `witness-inconsistent` forgery. Each was checked by two real `lake env lean`
# builds: exit 0 against its rival, non-zero against the frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# `opaque` callee and no `axiom` (the changed operations are modeled deeply), so
# there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
