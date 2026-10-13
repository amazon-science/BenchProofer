"""properties.py — G-PBT falsification battery for django__django-14140 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, where a case
legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_deconstruct`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff the variant is
in scope AND does NOT verify AND its refutation ``witness`` holds of the rival
while FAILING against the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini sibling
models the decomposition over a heap ``Node`` object whose fields are held at
half permission, and pins the result with three ``Ensures`` clauses. This Lean
bundle models the SAME single purely-functional core — deriving the positional
arguments and the keyword-argument mapping of a filter node's decomposition from
the node's stored components — but over an immutable value carrier: the node's
components arrive as four separate binders and the result is a ``Deconstructed``
record. The nagini reasoning carries over clause-for-clause; the mechanics are
restated over that carrier, and nagini's frame/permission-mutation class is
VACUOUS here (see ``assessment`` / the accounting block at the bottom).

DEFENDED SURFACE (one modeled behavior, one obligation, FIVE independent
top-level clauses). ``problem_spec_deconstruct path children connector negated
result`` pins EXACTLY:

  * (C0 path)      ``result.path = path``            — carried through unchanged;
  * (C1 args)      ``result.args = children``        — every child positional, in
    order, whatever the child count and whatever kind of child it is;
  * (C2 pair)      ``result.kwargs.pair = none``     — the keyword mapping never
    carries an inlined key/value entry;
  * (C3 connector) ``result.kwargs.connector =
    (if connector = Connector.cAnd then none else some connector)`` — recorded
    iff the combinator is non-default;
  * (C4 negated)   ``result.kwargs.negated = negated`` — mirrors the flag.

THE BEHAVIOURAL DISCRIMINATOR. C1 together with C2 is the whole substance of the
fix, and it is what nagini's clause (1) says on this carrier: for a node holding
exactly ONE child that is not itself a nested node, that child must still land
positionally in ``args`` and must NOT be relocated into the keyword mapping as an
inlined key/value entry. The ``weak-single-child-inlined`` rival below is exactly
the behavior the frozen ``Solution_prepatch.lean`` carries, and it is the one the
failing tests observe: they exercise single-child nodes and require the child in
the positional arguments — including a child that is a standalone conditional
expression, which is not index-addressable at all, so relocating it is not merely
a different shape but a read that cannot succeed.

BINDER STRUCTURE. The spec predicate has FOUR input binders — ``path``,
``children``, ``connector``, ``negated`` — and all four are load-bearing (one per
clause C0/C1/C3/C4, with C2 a constant clause over the whole domain). All four
are VARIED across the reject witnesses rather than pinned: the nine witnesses
probe nine DISTINCT input tuples (``pts=9``), with ``children`` ranging over
empty / single-``cond`` / single-``expr`` / single-``nested`` / two-``cond`` /
mixed two-element lists, ``connector`` taking both values, ``negated`` taking both
values, and ``path`` distinct in every one. See the point-spread table at the
bottom. This matters here specifically: C1 and C2 interact only on the
single-child sub-domain, so a battery whose witnesses all held ``children`` at
length ≥ 2 would never probe the clause the fix turns on.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Nagini's mandatory class (three cases:
    overwrite the child sequence, the combinator, or the negation flag so that a
    postcondition holds trivially) has no counterpart. Lean is referentially
    transparent: the node's components are immutable value binders, there is no
    heap cell, no aliasing, no fractional permission, and no ``mut`` input to
    write. A rival cannot make a clause true by changing its own input, so no
    substitute probe is fabricated (porting map: vacuous here). What those three
    cases were really protecting — that each clause is pinned to the node's own
    stored component and not to something the impl controls — is instead covered
    directly by the value rivals below, one per clause.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean, and genuinely so rather than
    as a spec hole. The nagini sibling carries no ``diverge-*``/``nonterm-*`` case
    to port, and none could be written here: ``implementation_deconstruct`` is a
    total Lean ``def``, so a non-terminating implementation is not expressible at
    all and there is nothing for the spec to admit vacuously. (Contrast velvet
    under ``loom.semantics.termination "partial"``, where this class IS a known
    spec hole — ``the corpus-wide termination-semantics finding``. That does not apply to this
    backend.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason nagini records N/A: the
    postcondition is GROUNDED component-wise in the node's own stored inputs (the
    child list verbatim, a decidable comparison of the combinator against the
    default, the flag verbatim, and a constant ``none``). The bundle declares no
    ``opaque`` callee and consumes no axiom, so there is no answer key an impl
    could echo without doing the work. In its place the battery carries honest
    positive controls that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole battery lives. NINE
    rivals, at least one per clause: the single-child relocation (the pre-fix
    behavior, attacking C1+C2), an inlined entry emitted on top of correct args
    (C2 alone), dropping the last child and reversing the child order (C1), losing
    the combinator and inverting the combinator test (C3), losing the negation
    flag and inverting the negation test (C4), and losing the carried-through path
    (C0). The two flag clauses C3 and C4 each carry BOTH a drop rival and an
    invert rival, so each is pinned from both sides — a drop rival alone is
    correct over its clause's whole silent sub-domain and cannot force the spec to
    keep the marker absent there.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``unfold`` then a case split
closing five ``rfl``s) is tuned to the frozen form — so a rejection ALONE
attributes nothing to the spec. Every ``expect="reject"`` case therefore carries a
Lean snippet stating ``¬ problem_spec_deconstruct <ground inputs>
(implementation_deconstruct <the same ground inputs>)`` and closing by ``unfold``
+ ``decide``. The whole carrier is decidable at literals (``Child`` and
``Connector`` derive ``DecidableEq``, ``Kwargs`` too, and ``String`` literals
compare), and the impl is loop-free, so ``decide`` REDUCES on both sides — it is
not stuck. Each witness binds NOTHING in its head (all inputs are ground
literals), so there are no hypotheses whose joint satisfiability could be in
question and ``witness-inconsistent`` cannot arise. Each was checked with two real
``lake env lean`` builds: it elaborates against its rival, and against the frozen
solution ``decide`` reports that it proved the OPPOSITE proposition — i.e. the
frozen side DECIDED (no ``witness-undecided``) and decided the witness false, so
each witness is a real discriminator and no ``witness_reference`` is needed.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart —
the decomposition it describes, written into the repository — would leave at
least one of the failing tests failing, or break a currently-passing round-trip
test, because those tests read back the positional arguments and the keyword
markers and rebuild the node from them.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` list is empty there, this bundle
declares no ``opaque`` callee and consumes no ``axiom`` (the changed operation is
modeled deeply), and the axiom lane is G-AX's job — this gate ignores it.

INDEPENDENT AUDIT (post-port, machine-checked; all builds re-run from scratch).
Two defects were found and repaired, and several claims above were confirmed
rather than trusted:

  * ADDED ``weak-negated-inverted``. C4 was attacked from ONE side only: the sole
    C4 rival, ``weak-negated-dropped``, is correct on the entire non-negated
    sub-domain, so no case forced the spec to pin the flag ABSENT at a
    non-negated node. Its C3 counterpart already had this pairing
    (dropped + inverted); C4's was missing. Re-derived with three builds: the
    rival's module FAILS (exit 1), its witness HOLDS of the rival (exit 0), and
    the SAME witness fails on the frozen solution (exit 1) with ``decide``
    reporting it proved the opposite proposition — a semantic refutation, not a
    missing identifier or a stuck reduction.
  * CORRECTED the sibling-battery census. The accounting block said the nagini
    battery has 10 SPEC cases (4 value rivals); it has 11 (5 value rivals). The
    port had in fact mapped all five, so only the prose was wrong — but a census
    that does not match the file it audits cannot be used to check the port for
    omissions, which is what it is for.

  Confirmed by re-derivation, not argument:
  - Statement integrity: all cases' ``theorem correct_deconstruct`` statement is
    byte-identical to the frozen one (whitespace-normalized compare), so no case
    hides a weakened hypothesis in a reformatting.
  - ``weak-single-child-inlined``'s impl region is BYTE-FOR-BYTE the frozen
    ``Solution_prepatch.lean`` impl, so the headline rival really is the pre-fix
    behavior and not a reconstruction of it.
  - Every reject rival differs from gold OBSERVABLY at its own witness point, and
    the drop/invert and C1/C2 near-miss pairs genuinely cannot share a witness
    (each rival AGREES with gold at its partner's point) — so no case is vacuous
    by definitional collapse on this carrier.
  - ``pos-reorder-markers`` is NOT definitionally equal to the frozen impl:
    ``example : impl_reordered = impl_frozen := by rfl`` FAILS, so the positive
    exercises a real reshape rather than restating gold.
  - The frame/permission-mutation class is vacuous here by DEMONSTRATION, not
    assertion: the closest expressible analogues (locally rebind ``children`` /
    ``connector`` / ``negated``, then satisfy the clause against the rebound
    copy) were all built. Each is REJECTED as an ordinary wrong value impl with
    its own refuting witness (exit 0 rival / exit 1 gold) — rebinding a binder
    cannot change what the spec compares against, which is why the class buys
    nothing here rather than being merely hard to write.
  - SPEC-TOO-WEAK is unreachable for ANY rival, machine-checked: the frozen
    postcondition is a FUNCTIONAL characterization. ``problem_spec_deconstruct``
    determines its result uniquely (proved: any two results satisfying it at the
    same inputs are equal), and the frozen impl satisfies it, so exactly one
    output is admissible at every input and no wrong impl can verify. Six new
    tuned wrong impls (invert the negation flag, record the combinator
    unconditionally, emit a constant inlined pair over the whole domain,
    duplicate the child sequence, filter nested children out of args, double the
    path) were each built anyway and each was REJECTED with a refuting witness.
  - SPEC-TOO-STRONG probed with five further CORRECT reshapes beyond the two
    positives (``children.take children.length``, ``children.reverse.reverse``,
    ``children.map id``, the combinator test written against ``cOr``, and a
    ``match`` on the combinator): all five VERIFY, so the spec admits faithful
    impls whose shape and proof differ from the frozen one.
"""
from pathlib import Path

INSTANCE = "django__django-14140"
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
# Region anchors. Each lies ENTIRELY inside `-- impl-start`/`-- impl-end` (or,
# for `_P_*`, inside `-- proof-start`/`-- proof-end`) and is unique in the
# frozen file; `_swap` raises on drift so the manifest breaks loudly if the
# frozen solution ever changes.
# ---------------------------------------------------------------------------

# The positional-arguments assignment: the whole of clause C1's computation.
_I_ARGS = "  let args := children\n"

# The mutable keyword-mapping accumulator, initialized empty.
_I_KWINIT = ("  let mut kw : Kwargs := "
             "{ pair := none, connector := none, negated := false }\n")

# The combinator branch (clause C3's computation).
_I_CONNIF = ("  if connector ≠ Connector.cAnd then\n"
             "    kw := { kw with connector := some connector }\n")

# The negation branch (clause C4's computation).
_I_NEGIF = "  if negated then\n    kw := { kw with negated := true }\n"

# The assembled result record (clause C0's pass-through lives in `path :=`).
_I_RET = "  return { path := path, args := args, kwargs := kw }"

# The whole signature tail + body, for the one positive that abandons the
# `Id.run do` shape entirely.
_I_SIG_BODY = (
    "    (connector : Connector) (negated : Bool) : Deconstructed := Id.run do\n"
    + _I_ARGS + _I_KWINIT + _I_CONNIF + _I_NEGIF + _I_RET)

# Frozen proof anchors. `_P_INTRO` lets the admissibility positive prepend a
# ground `have` without touching the theorem STATEMENT; `_P_CASES` is the case
# split the declarative positive re-proves past.
_P_INTRO = "  intro path children connector negated\n"
_P_CASES = (
    "  cases negated <;> by_cases hc : connector = Connector.cAnd <;>\n"
    "    simp only [hc, ne_eq, not_true, not_false_iff, if_true, if_false, "
    "Id.run] <;>\n"
    "    exact ⟨rfl, rfl, rfl, rfl, rfl⟩")


def _w(path, children, connector, negated):
    """A refutation witness at one ground input tuple.

    States that the rival's own output FAILS the frozen spec predicate at these
    literal inputs. Binds nothing, so there are no hypotheses to be consistent
    about; `decide` reduces because every carrier type is decidable at literals
    and the implementation is loop-free.
    """
    a = f"{path} {children} {connector} {negated}"
    return (f"example : ¬ problem_spec_deconstruct {a}\n"
            f"    (implementation_deconstruct {a}) := by\n"
            f"  unfold problem_spec_deconstruct implementation_deconstruct\n"
            f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both keep the
    # `theorem correct_deconstruct` statement byte-identical and introduce no
    # new axiom/theorem/lemma and no assumption token.
    # =====================================================================
    {
        "id": "pos-reorder-markers",
        "kind": "soundness",
        "expect": "verify",
        # Swap the ORDER of the two independent keyword-mapping updates: record
        # the negation flag first, the combinator second. The two updates touch
        # disjoint components of the mapping and neither reads the other, so the
        # assembled result is identical on every input. The frozen proof closes
        # unchanged (its case split covers both branches in either order).
        # (Verified: real build, exit 0.)
        "module": _swap(_BASE, _I_CONNIF + _I_NEGIF, _I_NEGIF + _I_CONNIF),
        "rationale": "structurally-different CORRECT impl: the two keyword-mapping "
                     "updates (combinator, negation flag) are applied in the "
                     "opposite order. They write disjoint components and neither "
                     "reads the other, so C0-C4 all still hold on every input — if "
                     "this cannot verify => SPEC-TOO-STRONG. The frozen tactic body "
                     "closes it unchanged; statement byte-identical, no new "
                     "axiom/lemma. Ports the nagini pos-reorder-kwargs positive "
                     "(there: hoist the two marker booleans above the copy loop; the "
                     "same independence argument, restated for this carrier where "
                     "there is no loop to hoist above).",
    },
    {
        "id": "pos-declarative",
        "kind": "soundness",
        "expect": "verify",
        # A much larger reshape: abandon the imperative accumulator entirely and
        # build the whole result as ONE record literal, with the combinator
        # component written as a conditional expression instead of a mutating
        # branch. Different control-flow shape, same value everywhere. The proof
        # region is re-proved: the case split is no longer needed because the
        # result is now definitionally the spec's right-hand side, so the five
        # component equations close by `rfl` directly. Statement byte-identical,
        # no new axiom/lemma. (Verified: real build, exit 0.)
        "module": _swaps(
            _BASE,
            (_I_SIG_BODY,
             "    (connector : Connector) (negated : Bool) : Deconstructed :=\n"
             "  { path := path,\n"
             "    args := children,\n"
             "    kwargs := { pair := none,\n"
             "                connector := if connector = Connector.cAnd then none "
             "else some connector,\n"
             "                negated := negated } }"),
            (_P_CASES, "  exact ⟨rfl, rfl, rfl, rfl, rfl⟩"),
        ),
        "rationale": "the cheapest honest implementation, in a structurally very "
                     "different shape: no mutable accumulator and no branching at "
                     "all — one record literal whose combinator component is a "
                     "conditional expression. Same value on every input, so C0-C4 "
                     "hold; if it cannot verify => SPEC-TOO-STRONG. Re-proved "
                     "honestly inside the proof region: the frozen case split "
                     "becomes unnecessary because each component is now "
                     "definitionally the spec's right-hand side, so the five "
                     "component equations close by `rfl`. Statement byte-identical, "
                     "no new axiom/lemma, no assumption token. Ports the nagini "
                     "pos-inline-flags positive (drop the temporaries and build the "
                     "result inline) and doubles as its "
                     "UNGROUNDED-ORACLE-ECHO positive control: the postcondition is "
                     "grounded, so the cheapest honest impl must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at exactly the
    # input shape the failing tests exercise. The frozen theorem carries NO
    # precondition hypothesis (the modeled behavior is total), so nagini's
    # "can the Requires be established for a single-child node" question
    # re-expresses as "is the postcondition dischargeable AT that node": a ground
    # `have` for a node holding exactly ONE standalone conditional-expression
    # child (the shape that is not index-addressable) is discharged by evaluation,
    # then the frozen obligation is closed verbatim. Nothing is assumed: no new
    # declaration, statement byte-identical, the instance is a `have` prepended to
    # the existing tactic body. (Verified: real build, exit 0.)
    # =====================================================================
    {
        "id": "admiss-single-child-expr",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_deconstruct "p" [Child.expr "e"] '
            "Connector.cAnd false\n"
            '      (implementation_deconstruct "p" [Child.expr "e"] '
            "Connector.cAnd false) := by\n"
            "    unfold problem_spec_deconstruct implementation_deconstruct\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged BY EVALUATION at the input shape "
                     "the failing tests exercise — a node holding exactly one child "
                     "which is a standalone conditional expression (not "
                     "index-addressable), default combinator, not negated — as a "
                     "`have`, and then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable at "
                     "exactly a normal in-domain input, the analogue of "
                     "PRECOND-TOO-STRONG; the frozen theorem carries no precondition "
                     "hypothesis, so satisfiability at the interesting point is what "
                     "there is to admit). Nothing is assumed: no new declaration, "
                     "statement byte-identical. Ports nagini's "
                     "admiss-single-child-node.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve, and (b) a witness pinning the
    # violation at one concrete input, checked to hold of the rival and to FAIL
    # on the frozen solution.
    # =====================================================================

    # ---- THE FIX ITSELF: relocate a lone child into the keyword mapping ----
    {
        "id": "weak-single-child-inlined",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior, byte-for-byte the impl the frozen
        # Solution_prepatch.lean carries: when the node holds exactly one child
        # that is not itself a nested node, leave the positional arguments EMPTY
        # and relocate that child into the keyword mapping as an inlined
        # key/value entry (read out of the child by index-addressing it, which
        # yields nothing at all for a child that has no subscript). Correct for
        # every other child count, so this is a partial-domain rival that
        # diverges on precisely the sub-domain the fix is about.
        "module": _swap(
            _BASE, _I_SIG_BODY,
            "    (connector : Connector) (negated : Bool) : Deconstructed := "
            "Id.run do\n"
            "  let mut args : List Child := []\n"
            "  let mut kw : Kwargs := "
            "{ pair := none, connector := none, negated := false }\n"
            "  if children.length = 1 ∧ ¬ (children.headI.isNode) then\n"
            "    let child := children.headI\n"
            '    kw := { kw with pair := some (child.asPair.getD ("", "")) }\n'
            "  else\n"
            "    args := children\n"
            "    if connector ≠ Connector.cAnd then\n"
            "      kw := { kw with connector := some connector }\n"
            "  if negated then\n"
            "    kw := { kw with negated := true }\n"
            "  return { path := path, args := args, kwargs := kw }"),
        "refinement": "this is the behavior the frozen pre-patch artifact carries and "
                      "the one the failing tests were written against. A faithful "
                      "real decomposition that keeps the lone-child special case "
                      "leaves the positional arguments empty and puts the child into "
                      "the keyword mapping instead, so a test that reads back the "
                      "decomposition of a single-child node sees empty positional "
                      "arguments where it requires the child — and for a child that "
                      "is a standalone conditional expression the index-addressing "
                      "step cannot even be performed, which is the reported "
                      "failure. Every one of the failing tests observes a "
                      "single-child node, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C1 (args) AND C2 (pair): on a node with exactly one "
                     "non-nested child the spec pins `result.args = children` and "
                     "`result.kwargs.pair = none`, but this rival returns args `[]` "
                     "and a `some _` pair. Correct on every other child count "
                     "(partial-domain: it diverges only where `children` has length "
                     "1 and that child is not nested). Refuted at a single "
                     "standalone-conditional-expression child — the input shape "
                     "whose index-addressing has no result at all — with the default "
                     "combinator and no negation.",
        "witness": _w('"a"', '[Child.expr "e"]', "Connector.cAnd", "false"),
    },

    # ---- inlined entry emitted ON TOP of correct positional arguments (C2 alone) ----
    {
        "id": "weak-pair-also-emitted",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS of the rival above, and strictly closer to gold: the
        # positional arguments are the full child sequence (C1 correct, unlike
        # the pre-fix rival), but a lone index-addressable child is ADDITIONALLY
        # inlined into the keyword mapping. Isolates C2, which no other rival
        # attacks on its own — and it needs its own witness precisely because it
        # agrees with gold over strictly more of the domain than
        # `weak-single-child-inlined` does.
        "module": _swap(
            _BASE, _I_ARGS + _I_KWINIT,
            _I_ARGS + _I_KWINIT
            + "  if children.length = 1 ∧ ¬ (children.headI.isNode) then\n"
              "    kw := { kw with pair := children.headI.asPair }\n"),
        "refinement": "a faithful real decomposition that emitted the lone child BOTH "
                      "positionally and as an inlined keyword entry would rebuild a "
                      "node carrying that condition twice: the round-trip tests "
                      "reconstruct the node from the decomposition and compare it "
                      "with the original, and a duplicated condition (or an "
                      "unexpected extra keyword marker where the tests assert the "
                      "keyword mapping is empty for a plain single-child node) makes "
                      "that comparison fail. So the faithful patch would NOT resolve "
                      "— it breaks the very tests the fix must keep green.",
        "rationale": "REJECT from C2 (pair) ALONE: the spec pins "
                     "`result.kwargs.pair = none` over the WHOLE domain, and this "
                     "rival emits `some (k, v)` whenever the node holds exactly one "
                     "index-addressable child. C0/C1/C3/C4 are left gold, so the "
                     "rejection is attributable to C2 only. Refuted at a distinct "
                     "point from the pre-fix rival — a single key/value child with "
                     "the NON-default combinator — which is where this near-miss "
                     "first departs from gold while the pre-fix rival's own witness "
                     "input (a non-addressable child) leaves it in agreement.",
        "witness": _w('"h"', '[Child.cond "u" "9"]', "Connector.cOr", "false"),
    },

    # ---- drop the last child (C1) ----
    {
        "id": "weak-drop-last-child",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain off-by-one on the positional arguments: copy every child
        # except the last. Correct exactly on the empty node.
        "module": _swap(_BASE, _I_ARGS, "  let args := children.dropLast\n"),
        "refinement": "a faithful patch that built the positional arguments from all "
                      "but the last child would silently drop a condition from the "
                      "decomposition: the round-trip tests rebuild the node from the "
                      "positional arguments and compare it with the original, so a "
                      "node missing one of its conditions compares unequal, and the "
                      "multi-condition decomposition tests read back the full "
                      "sequence. The faithful patch would NOT resolve.",
        "rationale": "REJECT from C1 (args): the spec pins `result.args = children` "
                     "but this rival returns the child sequence minus its last "
                     "element, which differs for every non-empty node "
                     "(partial-domain: correct only on the empty node). Refuted at a "
                     "TWO-child node of key/value children — the multi-child "
                     "sub-domain, which the single-child rivals leave untouched.",
        "witness": _w('"b"', '[Child.cond "x" "1", Child.cond "y" "2"]',
                      "Connector.cAnd", "false"),
    },

    # ---- reverse the child order (C1) ----
    {
        "id": "weak-reverse-children",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps every child but emits them in REVERSE order: attacks the ORDER
        # half of C1, which a length- or membership-only spec would have missed.
        "module": _swap(_BASE, _I_ARGS, "  let args := children.reverse\n"),
        "refinement": "a faithful patch that emitted the children in reverse order "
                      "would produce a decomposition whose positional arguments are "
                      "a permutation of the node's conditions. The decomposition "
                      "tests compare the returned positional arguments against an "
                      "expected tuple in a fixed order, so any node with two or more "
                      "conditions mismatches. The faithful patch would NOT resolve.",
        "rationale": "REJECT from C1 (args), the ORDER half specifically: the spec "
                     "pins `result.args = children` as a LIST, so a reversal is a "
                     "violation for every non-palindromic child sequence. Refuted at "
                     "a MIXED two-child node (a key/value child followed by a nested "
                     "child) under the non-default combinator and with the negation "
                     "flag set — a point that simultaneously exercises the nested "
                     "child kind and both flags at their non-default values.",
        "witness": _w('"c"', '[Child.cond "x" "1", Child.nested "n"]',
                      "Connector.cOr", "true"),
    },

    # ---- lose the combinator marker (C3) ----
    {
        "id": "weak-connector-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Never record the combinator: the keyword mapping's combinator component
        # stays absent even for a non-default combinator. Everything else gold,
        # so the rejection isolates C3.
        "module": _swap(_BASE, _I_CONNIF, ""),
        "refinement": "a faithful patch that never emitted the combinator marker "
                      "would decompose a non-default-combinator node without "
                      "recording which combinator it had, so rebuilding from the "
                      "decomposition yields a node with the DEFAULT combinator "
                      "instead: the currently-passing decomposition and round-trip "
                      "tests for a non-default-combinator node observe that marker "
                      "and rebuild through it, so they would fail. The faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from C3 (connector): the spec pins "
                     "`result.kwargs.connector = if connector = Connector.cAnd then "
                     "none else some connector`, and a constantly-absent component "
                     "cannot equal `some connector` when the combinator is "
                     "non-default. Correct on the default-combinator sub-domain "
                     "(partial-domain). Refuted at the EMPTY node under the "
                     "non-default combinator, which isolates C3 from the args "
                     "clause entirely.",
        "witness": _w('"d"', "[]", "Connector.cOr", "false"),
    },

    # ---- invert the combinator test (C3 near-miss) ----
    {
        "id": "weak-connector-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss on C3 from the other side: record the combinator
        # exactly when it EQUALS the default — the opposite guard. Disagrees with
        # gold on BOTH combinator values, so it needs a witness at a
        # DEFAULT-combinator point, where `weak-connector-dropped` agrees with
        # gold and this rival does not.
        "module": _swap(
            _BASE, _I_CONNIF,
            "  if connector = Connector.cAnd then\n"
            "    kw := { kw with connector := some connector }\n"),
        "refinement": "a faithful patch with the combinator guard inverted attaches "
                      "the combinator marker to DEFAULT-combinator nodes and omits "
                      "it from non-default ones: exactly backwards. The tests assert "
                      "an EMPTY keyword mapping for a plain default-combinator node "
                      "and a present combinator marker for a non-default one, so "
                      "both directions fail. The faithful patch would NOT resolve.",
        "rationale": "REJECT from C3 (connector): `if connector = Connector.cAnd then "
                     "some connector else none` is the pointwise NEGATION of the "
                     "required presence condition, so it disagrees with the spec at "
                     "every combinator value. Refuted at a DEFAULT-combinator point "
                     "— a single key/value child with the negation flag set — which "
                     "is the sub-domain where the drop-the-marker rival is still "
                     "correct, so this near-miss gets its own discriminating input "
                     "rather than sharing one.",
        "witness": _w('"e"', '[Child.cond "k" "v"]', "Connector.cAnd", "true"),
    },

    # ---- lose the negation flag (C4) ----
    {
        "id": "weak-negated-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Never record the negation flag: the mapping's flag stays false even for
        # a negated node. Everything else gold, so the rejection isolates C4.
        "module": _swap(_BASE, _I_NEGIF, ""),
        "refinement": "a faithful patch that never emitted the negation marker would "
                      "decompose a negated node as if it were not negated, so "
                      "rebuilding from the decomposition yields a node with the "
                      "negation lost — inverting the meaning of the filter. Both the "
                      "failing negated-node test and the currently-passing negated "
                      "round-trip test observe that marker, so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C4 (negated): the spec pins "
                     "`result.kwargs.negated = negated` but this rival's mapping "
                     "keeps the flag at its initial `false`, which differs on every "
                     "negated node (partial-domain: correct on non-negated nodes). "
                     "Refuted at a NESTED single child under the non-default "
                     "combinator with the flag set — a distinct child kind, and the "
                     "only witness where the lone child IS a nested node, which is "
                     "the sub-domain the pre-fix special case explicitly excluded.",
        "witness": _w('"f"', '[Child.nested "n"]', "Connector.cOr", "true"),
    },

    # ---- invert the negation flag (C4 near-miss) ----
    {
        "id": "weak-negated-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss on C4 from the other side, mirroring what
        # `weak-connector-inverted` does for C3: record the flag exactly when the
        # node is NOT negated — the opposite guard. Added by audit: C4 was
        # attacked only by `weak-negated-dropped`, which is a rival that is
        # CORRECT on the whole non-negated sub-domain, so nothing in the battery
        # forced the spec to pin the flag at a non-negated node. This rival
        # disagrees with gold on BOTH flag values, so it needs a witness at a
        # NON-negated point, where `weak-negated-dropped` agrees with gold and
        # this one does not.
        "module": _swap(
            _BASE, _I_NEGIF,
            "  if ¬ negated then\n    kw := { kw with negated := true }\n"),
        "refinement": "a faithful patch with the negation guard inverted attaches "
                      "the negation marker to NON-negated nodes and omits it from "
                      "negated ones: exactly backwards. The tests assert an EMPTY "
                      "keyword mapping for a plain non-negated node and a present "
                      "negation marker for a negated one, and the round-trip tests "
                      "rebuild through that marker — so a plain node would rebuild "
                      "as its own logical inverse. Both directions fail, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C4 (negated): `if ¬ negated then true else false` "
                     "is the pointwise NEGATION of the required flag, so it "
                     "disagrees with the spec at every flag value. Refuted at the "
                     "EMPTY node with the default combinator and the flag NOT set — "
                     "the sub-domain where the drop-the-flag rival is still correct, "
                     "so this near-miss gets its own discriminating input rather "
                     "than sharing one, and the point isolates C4 from the args and "
                     "connector clauses entirely.",
        "witness": _w('"i"', "[]", "Connector.cAnd", "false"),
    },

    # ---- lose the carried-through path (C0) ----
    {
        "id": "weak-path-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the frame clause: the pass-through component is replaced by a
        # constant instead of being carried through. No nagini counterpart (its
        # sibling does not model this component); it is a real, load-bearing
        # top-level clause of THIS spec and is otherwise unattacked.
        "module": _swap(
            _BASE, _I_RET,
            '  return { path := "", args := args, kwargs := kw }'),
        "refinement": "a faithful patch that returned a constant in place of the "
                      "identifying path component would hand back a decomposition "
                      "that names nothing rebuildable: every decomposition test "
                      "compares the returned triple's first component against the "
                      "expected dotted identifier, and the round-trip tests rebuild "
                      "through it. A patch losing it fails all of them, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from C0 (path): the spec pins `result.path = path` — the "
                     "frame clause requiring the component be carried through "
                     "unchanged — and this rival substitutes a constant, which "
                     "differs for every non-empty `path` argument. This is the sole "
                     "rival exercising the `path` binder's clause, and it is why the "
                     "witnesses give `path` a DISTINCT literal in every case rather "
                     "than pinning it: a rival mishandling only that component would "
                     "otherwise go unnoticed. Refuted at the empty node with the "
                     "default combinator and no negation, so C0 is isolated from "
                     "every other clause.",
        "witness": _w('"g"', "[]", "Connector.cAnd", "false"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 11 SPEC cases (2 soundness
# positives, 1 admissibility, 3 frame/permission-mutation rivals, 5
# value/partial-domain rivals) plus an EMPTY axiom lane. This bundle models the
# SAME single purely-functional core over an immutable value carrier and carries
# ONE obligation, so the map is:
#
#   sibling case                    -> here
#   -----------------------------------------------------------------------
#   pos-reorder-kwargs              -> pos-reorder-markers        RE-EXPRESSED
#   pos-inline-flags                -> pos-declarative            RE-EXPRESSED
#   admiss-single-child-node        -> admiss-single-child-expr   RE-EXPRESSED
#   frame-mutate-children           -> (none)                     VACUOUS
#   frame-mutate-connector          -> (none)                     VACUOUS
#   frame-mutate-negated            -> (none)                     VACUOUS
#   uniq-single-child-special-case  -> weak-single-child-inlined  PORTED
#   uniq-drop-last                  -> weak-drop-last-child       PORTED
#   uniq-connector-constant-false   -> weak-connector-dropped     PORTED
#   uniq-negated-constant-false     -> weak-negated-dropped       PORTED
#   uniq-connector-flip             -> weak-connector-inverted    PORTED
#   (none)                          -> weak-pair-also-emitted     ADDED (C2)
#   (none)                          -> weak-reverse-children      ADDED (C1 order)
#   (none)                          -> weak-path-dropped          ADDED (C0)
#   (none)                          -> weak-negated-inverted      ADDED (C4 flip)
#   AXIOM_TESTS (0)                 -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (pos-reorder-markers): the sibling hoists the two marker booleans
#   ABOVE its copy loop to show they are independent of the copied arguments.
#   This carrier has no loop to hoist above (the positional arguments are the
#   child list itself), so the same independence argument is made where it still
#   bites: the two marker updates are applied in the opposite order.
# RE-EXPRESSED (pos-declarative): the sibling's inline positive drops its
#   temporaries and passes the grounded expressions straight into the result
#   constructor. Here that goes further — the accumulator and both branches
#   disappear into a single record literal — which required re-proving inside the
#   proof region (the frozen case split becomes unnecessary; the five component
#   equations close by `rfl`). Honest re-proof: statement byte-identical, no new
#   declaration, no assumption token.
# RE-EXPRESSED (admiss-single-child-expr): the sibling's admissibility witness
#   asserts its five half-permission accesses are establishable for a concrete
#   single-child node, because its precondition IS those accesses. This bundle's
#   obligation carries NO precondition hypothesis (the modeled behavior is
#   total), so there is no precondition to admit; the honest analogue is to show
#   the POSTCONDITION is dischargeable at that same single-child shape, which is
#   what would fail if the spec were unsatisfiable at a normal in-domain input.
# VACUOUS (the three frame/permission-mutation rivals): nagini's #1 weakness
#   class has NO counterpart on this carrier and no substitute is fabricated.
#   There, the node is a heap object whose every field is held at half
#   permission, and a rival can overwrite a field to make a clause hold
#   trivially. Here Lean is referentially transparent: the node's components
#   arrive as four immutable value binders, there is no heap cell, no aliasing,
#   no fractional permission and no `mut` input, so "write the input to satisfy
#   the postcondition" is not expressible. The property those three cases
#   protected — each clause pinned to the node's own stored component — is
#   covered instead by one value rival per clause (C0 weak-path-dropped, C1
#   weak-drop-last-child / weak-reverse-children, C2 weak-pair-also-emitted, C3
#   weak-connector-dropped / weak-connector-inverted, C4
#   weak-negated-dropped / weak-negated-inverted).
# VACUOUS (divergence / non-termination): the sibling carries NO `diverge-*`,
#   `nonterm-*` or `weak-diverge` case, and on this backend the class is
#   genuinely vacuous rather than a spec hole — `implementation_deconstruct` is a
#   total Lean `def`, so a non-terminating rival cannot be written at all and
#   there is nothing for the frozen spec to admit vacuously. (The known
#   spec-hole disposition in the corpus-wide termination-semantics finding applies to velvet under
#   `loom.semantics.termination "partial"`, not to lean.)
# ADDED (weak-pair-also-emitted, weak-reverse-children, weak-path-dropped): this
#   spec has FIVE independent top-level clauses where the sibling's has three,
#   because this carrier models the pass-through component (C0) and the
#   inlined-entry component (C2) explicitly. C2 was attacked only jointly with
#   C1 by the pre-fix rival, C1's ORDER half was unattacked (the sibling's
#   drop-last rival only shortens), and C0 was unattacked entirely. The three
#   additions are not fabricated for an unmodeled behavior: each attacks a real,
#   load-bearing clause of the SAME modeled spec, and each carries its own
#   refinement argument.
#
# POINT SPREAD. The nine reject witnesses probe nine DISTINCT input tuples
# (pts=9), and no input binder is held at a single value across them:
#
#   (path, children, connector, negated)                        case              clause
#   ("a", [expr],                    cAnd, false)   weak-single-child-inlined     C1+C2
#   ("h", [cond],                    cOr,  false)   weak-pair-also-emitted        C2
#   ("b", [cond, cond],              cAnd, false)   weak-drop-last-child          C1
#   ("c", [cond, nested],            cOr,  true )   weak-reverse-children         C1
#   ("d", [],                        cOr,  false)   weak-connector-dropped        C3
#   ("e", [cond],                    cAnd, true )   weak-connector-inverted       C3
#   ("f", [nested],                  cOr,  true )   weak-negated-dropped          C4
#   ("i", [],                        cAnd, false)   weak-negated-inverted         C4
#   ("g", [],                        cAnd, false)   weak-path-dropped             C0
#
#   * `path`      — nine distinct literals (never pinned; C0's rival needs it).
#   * `children`  — empty, and length-1 in each of the THREE child kinds
#                   (key/value, standalone expression, nested), and length-2 in
#                   two different kind combinations. The length-1 vs length-2
#                   split is what the fix turns on, and both are probed.
#   * `connector` — both values (five `cAnd`, four `cOr`).
#   * `negated`   — both values (three `true`, six `false`).
#
#   The three near-miss pairs are deliberately NOT sharing a witness:
#   weak-pair-also-emitted agrees with gold over strictly more of the domain than
#   weak-single-child-inlined (its positional arguments are correct), so it is
#   refuted at a key/value child where the pre-fix rival's own witness input
#   would not separate it; weak-connector-inverted is refuted at a
#   DEFAULT-combinator point, which is exactly where weak-connector-dropped is
#   still correct; and weak-negated-inverted is refuted at a NON-negated point,
#   which is exactly where weak-negated-dropped is still correct. Each
#   drop/invert pair therefore pins its clause from BOTH sides: the drop rival
#   forces the clause to fire where it must, the invert rival forces it to stay
#   silent where it must not.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and this bundle declares no
# `opaque` callee and consumes no axiom (the changed operation is modeled
# deeply), so there is nothing to probe; the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
