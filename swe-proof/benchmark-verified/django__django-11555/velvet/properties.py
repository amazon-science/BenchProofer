"""properties.py — G-PBT falsification battery for django__django-11555 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct expandOrdering`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a specification of ordering items,
parametric in the recursive name→ordering resolution). The single obligation is

    expandOrdering (items : List Item) (resolve : Name → List Pair)
        return (out : List Pair)
      ensures out = expandItems resolve items

``expandItems resolve items`` is a total, fully-unfolded pure function: it maps
each item, IN SPECIFICATION ORDER, to its contribution and concatenates them
(``itemContribution``): an item that is already a complete order *expression*
contributes exactly ITSELF, paired with ``false``, and is NOT routed through name
resolution (it carries no name to look up); an item that is a *field-name* lookup
contributes whatever the recursive resolution yields. The load-bearing clause
pins the WHOLE output sequence to this per-item image, so it constrains three
independent things at once: the pass-through branch (an expression contributes
``[(e, false)]``, identity preserved), the resolution branch (a name contributes
``resolve n``, and it is the name that is resolved), and the order/length of the
produced sequence.

``resolve : Name → List Pair`` is a FREE input the spec quantifies over: the
``ensures`` holds for EVERY value of it, so the spec makes no claim about how a
name resolves to orderings — only that an expression is NEVER handed to it and a
name IS. Because the result is pinned for every ``resolve``, a rival that routes
the wrong kind of item through it (or corrupts the pass-through identity) is
refuted uniformly, and can be caught by instantiating ``resolve`` at a concrete
function that separates the two branches.

ADVERSARIAL READ of the nagini classes on THIS carrier (see the footer for the
case-by-case accounting):
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating backward loop collapsed to the
    closed form the post-image names; the per-item branch reordered with the
    pass-through target staged into an explicit local) must still verify, else the
    spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries NO ``require`` clause (the pre-conditions
    region is empty), so the sibling's "a normal input satisfies the
    precondition" probe is degenerate here (every input is in-domain). The
    residual risk on a total-domain spec is that the post-image is DEGENERATE at
    the interesting point — a spec no impl distinguishes reads exactly like one
    every impl meets. ``admiss-mixed-nondegenerate`` discharges an in-region
    assert pinning that the per-item image genuinely distinguishes its two
    branches (an expression contributes itself and is NOT resolved; a name is
    resolved) and that a MIXED specification is assembled in order — exactly the
    reported reproduction (a default ordering mixing an order expression and a
    field name).
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's two
    MANDATORY frame-mutation rivals write back into read-only sequence inputs that
    carry only a fractional heap permission (``Acc(...,1/2)``) and are rejected for
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent: every
    parameter is an immutable value, this bundle declares no ``mut`` binder, there
    is no heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. No substitute is
    fabricated (per the porting map, this class is legitimately dropped here rather
    than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. The post-image is pinned
    to ``expandItems resolve items`` — a concrete ``def`` computed entirely from
    the method's own inputs; the ``axioms`` region is empty (no opaque answer key).
    The free ``resolve`` is quantified over, not an answer key: the output is
    pinned to whatever ``resolve`` yields on a NAME item and to the expression's
    own identity on an EXPRESSION item, which a wrong impl cannot fake for every
    ``resolve``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against the single
    ensures. A rival can route an expression through the resolver (the reported
    crash), invert the discriminant, treat every item as an expression (never
    resolve a name), corrupt the pass-through identity, or drop the pass-through
    contribution entirely.
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS (specific to this carrier), and an HONEST accounting of which
half of the gate's two-build check carries the signal here. The spec is a
``method`` CONTRACT, not a bare predicate, so a witness reaches it through
Velvet's own tester machinery: ``expandOrderingTester items resolve = false``
says the extracted program's result violates the postcondition at that concrete
input, checked in a file whose ``prove_correct`` block has been stripped (no
tactic script can mask the verdict). The free resolver ``resolve`` is
instantiated at a concrete decidable function in each witness, so the tester
reduces to a ground boolean.

The RIVAL half is where all the content is, and it is a genuine computation.
Every reject rival is written LOOP-FREE (``items.flatMap``), so its extracted
tester kernel-reduces and ``decide`` really evaluates the postcondition at the
probed input and finds it FALSE. That is a machine-checked semantic refutation of
that rival against the frozen ``ensures``, and it is attributable to the spec
rather than to loop-freeness: the SAME witness built against a CORRECT loop-free
impl (``return (items.flatMap (fun it => match it with | .expr e => [(e, false)]
| .name n => resolve n))``) FAILS, with ``decide`` reporting that the proposition
``... = false`` *is false*. So each witness discriminates wrong-from-correct
among impls whose testers reduce; that recorded check, not the gate's gold half,
is what makes these rejections mean something.

The GOLD half is INERT on this carrier, and the earlier claim that the
discrimination was therefore "structural" was wrong — structural non-reduction is
precisely NOT discrimination. The frozen program's ``while`` compiles through
``Loop.forIn.loop``, which is defined by ``partial_fixpoint`` and so is
kernel-irreducible: gold's tester will not reduce for ANY argument. Measured: the
gold-side build fails with ``Tactic `decide` failed ... did not reduce to isTrue
or isFalse`` even at ``items = []`` (zero loop iterations), and it fails the same
way for a witness asserting the tester is ``true``. The gold half therefore
returns "failed" unconditionally and supplies no evidence at all, so it cannot
perform the anti-tautology job the protocol assigns it. Consequence, recorded so
no reader over-reads a SOUND on any loop-bearing velvet bundle: a CORRECT
loop-free impl shipped as a reject rival with a NON-refuting witness
(``... = true``) passes both halves of the gate and is recorded as "rejected
(witness refutes the rival)". Reproduced here with real builds. That is a
limitation of the witness protocol against a ``partial_fixpoint`` loop, not a
defect in these cases; ``native_decide`` DOES reduce gold's tester and confirms
it is ``true`` at every input probed below, i.e. gold genuinely satisfies the
spec at each of those points, which is the fact the gold half was supposed to
establish and does not.

Every reject witness states its refutation at LITERAL inputs (a concrete
``List Item`` and a concrete ``resolve`` closure — no head binder, no
hypothesis), so no witness conditions on an opaque term and the consistency probe
is vacuous by construction.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
recursive name resolution enters as the free input ``resolve`` — an A-reference
the R/I legs differential-test (G-CONF's job), not a consumed contract. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11555"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or is the whole prove_correct tactic block, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the specification. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`); the loop-free positive control does too.
_IMPL = """    -- impl-start
    let mut result : List Pair := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = expandItems resolve (items.drop i)
      done_with i = 0
      decreasing i
    do
      let it := items[i - 1]!
      -- An order expression is already a complete ordering: take it as-is,
      -- paired with `false`. A field name is expanded by its recursive
      -- resolution. (The branch is what keeps an expression off the
      -- name-resolution path.)
      let contribution : List Pair :=
        match it with
        | .expr e => [(e, false)]
        | .name n => resolve n
      result := contribution ++ result
      i := i - 1
    return result
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    -- impl-start\n    let mut result : List Pair := []"

assert _BASE.count(_IMPL_TOP) == 1, "impl-top anchor drifted from expected text"

# The FULL frozen proof body. A positive control that reshapes the impl retunes
# THIS block (elided from the spec view); reject rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = """prove_correct expandOrdering by
  loom_solve
  rw [expandItems_drop_step resolve items i (by omega) (by omega)]
  simp_all [itemContribution]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full variant with ONLY the impl region body replaced (frozen proof kept —
    used for reject rivals, which are expected NOT to verify)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(old, new, new_proof):
    """Reshape an in-region anchor AND retune the tactic body (correct reshapes
    whose new impl no longer matches the frozen loop-tuned script)."""
    return _swap(_swap(_BASE, old, new), _PROOF, new_proof)


# ---- Reject rivals are written LOOP-FREE as a per-item `items.flatMap`, so the
# ---- extracted tester reduces under `decide` at a concrete input; the frozen
# ---- while-loop tester stays stuck, which is exactly the discrimination.
def _flatmap(exprarm, namearm):
    return _impl(
        "    return (items.flatMap (fun it => match it with\n"
        f"      | .expr e => {exprarm}\n"
        f"      | .name n => {namearm}))")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `expandOrderingTester items resolve = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped.
def _tester(body):
    return ("extract_program_for expandOrdering\n"
            "prove_precondition_decidable_for expandOrdering\n"
            "prove_postcondition_decidable_for expandOrdering\n"
            "derive_tester_for expandOrdering\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the `ensures out = expandItems resolve items`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating backward loop into the closed form the
        # post-image names directly. A completely different control-flow shape (no
        # loop, no accumulator, no drop-step lemma) computing the same image; the
        # loop-specific proof collapses to `loom_solve`.
        "module": _impl_reproved(
            _IMPL,
            "    -- impl-start\n"
            "    return expandItems resolve items\n"
            "    -- impl-end",
            "prove_correct expandOrdering by\n  loom_solve"),
        "rationale": "a loop-free impl that returns the expansion directly must "
                     "satisfy `out = expandItems resolve items`; a correct reshape "
                     "of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Ports the nagini "
                     "pos-control-precomputed-bound in spirit — a structurally "
                     "different but content-identical impl — from a maximally "
                     "different (loop-free) control-flow shape.",
    },
    {
        "id": "pos-arms-reordered-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward loop but swap the two arms of the per-item
        # match (name arm first) and stage the pass-through target into an explicit
        # typed local `single` before wrapping it. Same value flow; the loop and
        # the front-recursive invariant are unchanged, so only the final
        # `simp_all [itemContribution]` needs one Item case-split to align the
        # reordered arms.
        "module": _impl_reproved(
            _IMPL,
            "    -- impl-start\n"
            "    let mut result : List Pair := []\n"
            "    let mut i := items.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ items.length\n"
            "      invariant result = expandItems resolve (items.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let it := items[i - 1]!\n"
            "      let contribution : List Pair :=\n"
            "        match it with\n"
            "        | .name n => resolve n\n"
            "        | .expr e =>\n"
            "          let single : Pair := (e, false)\n"
            "          [single]\n"
            "      result := contribution ++ result\n"
            "      i := i - 1\n"
            "    return result\n"
            "    -- impl-end",
            "prove_correct expandOrdering by\n"
            "  loom_solve\n"
            "  rw [expandItems_drop_step resolve items i (by omega) (by omega)]\n"
            "  simp_all [itemContribution]\n"
            "  cases items[i - 1]?.getD default <;> rfl"),
        "rationale": "reordering the per-item match arms and staging the "
                     "pass-through target through an explicit local computes the "
                     "same contribution value-for-value with the loop and invariant "
                     "unchanged, so `out = expandItems resolve items` still holds; a "
                     "correct reshape must verify (else SPEC-TOO-STRONG on the "
                     "branch order / staging shape). Ports the nagini "
                     "pos-control-explicit-local. The reproof adds only an Item "
                     "case-split to align the reordered arms with `itemContribution`.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries no `require` clause, so the "a normal
    # input satisfies the precondition" probe is degenerate (every input is
    # in-domain). The residual risk on a total-domain spec is that the post-image
    # is DEGENERATE at the interesting point (a spec no impl distinguishes reads
    # like one every impl meets). This case discharges an in-region assert at
    # concrete inputs establishing that the per-item image really does DISTINGUISH
    # its two branches — an expression contributes itself paired with `false` and
    # is NOT resolved, a name is resolved — and assembles a MIXED specification IN
    # ORDER (exactly the reported reproduction: a default ordering mixing an order
    # expression and a field name). The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live (a false claim
    # leaves an unsolved goal), and the proof gains one `decide` arm.
    # =====================================================================
    {
        "id": "admiss-mixed-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            _IMPL_TOP,
            "    -- impl-start\n"
            "    assert (with_name_prefix `assert\n"
            "      (itemContribution (fun _ => [(9, true)]) (Item.expr 5) = [(5, false)] ∧\n"
            "       itemContribution (fun _ => [(9, true)]) (Item.name 0) = [(9, true)] ∧\n"
            "       expandItems (fun _ => [(9, true)]) [Item.expr 5, Item.name 0]\n"
            "         = [(5, false), (9, true)]))\n"
            "    let mut result : List Pair := []",
            "prove_correct expandOrdering by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [expandItems_drop_step resolve items i (by omega) (by omega)];\n"
            "       simp_all [itemContribution])"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: an order expression contributes exactly "
                     "itself paired with `false` and is NOT routed through the "
                     "resolver (`Item.expr 5 ↦ [(5, false)]`, independent of "
                     "`resolve`), a field name IS resolved (`Item.name 0 ↦ resolve "
                     "0 = [(9, true)]`), and a MIXED specification is assembled in "
                     "order (`[(5, false), (9, true)]`). The in-region assert must "
                     "discharge (else the image would be constant / the obligation "
                     "degenerate); the impl is kept verbatim so `out = expandItems "
                     "resolve items` still verifies. Ports the nagini "
                     "admissibility-mixed-ordering (an OrderBy item + a textual "
                     "name), re-aimed from a precondition-admits probe to a "
                     "post-image-nondegeneracy probe since this method has no "
                     "`require`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test. All attack the single ensures; the `items`
    # binder is varied across expression / name / mixed items and the `resolve`
    # binder is instantiated at separating closures.
    # =====================================================================
    {
        "id": "real-bug-route-expr-through-resolver",
        "kind": "uniqueness",
        "expect": "reject",
        # THE headline weakness (the literal pre-image behaviour): route EVERY
        # item through the recursive resolver, with NO separate pass-through for an
        # already-formed order expression. Correct on every name item; diverges on
        # the expression sub-domain, where the post-image demands the expression's
        # own `[(e, false)]`.
        "module": _flatmap("resolve e", "resolve n"),
        "refinement": "this is the literal pre-image behaviour: every item — "
                      "including an already-formed order expression — is handed to "
                      "the recursive name-resolution, whose first step parses the "
                      "item as a field-name string and raises on a non-string "
                      "expression. Its faithful real counterpart is the UNCHANGED "
                      "repo, which crashes on exactly the reported scenario (a "
                      "default ordering that contains an order expression), so the "
                      "failing test does not even complete — it would NOT resolve. "
                      "This is the exact defect the fix corrects.",
        "rationale": "REJECT from `out = expandItems resolve items` via "
                     "`itemContribution`'s `.expr e => [(e, false)]` branch: at an "
                     "expression item the image demands `[(e, false)]` — the "
                     "expression's own identity, independent of `resolve` — but the "
                     "rival returns `resolve e`. Refuted at a single expression "
                     "item `[Item.expr 5]` under a `resolve` whose value at 5 "
                     "(`[(99, true)]`) differs from `[(5, false)]`. If it verified "
                     "=> SPEC-TOO-WEAK (admits the crashing bug).",
        "witness": _tester(
            "example : expandOrderingTester [Item.expr 5] (fun _ => [(99, true)]) "
            "= false := by\n  decide\n"),
    },
    {
        "id": "inverted-discriminant",
        "kind": "uniqueness",
        "expect": "reject",
        # Back-to-front discriminant: pass a NAME item straight through as
        # `[(n, false)]` (never resolved) and route an EXPRESSION item into the
        # resolver. Wrong on BOTH branches wherever the two differ.
        "module": _flatmap("resolve e", "[(n, false)]"),
        "refinement": "a counterpart that inverted the guard sense — passing a "
                      "field-name straight through unresolved while handing an "
                      "order expression to the name-resolution — leaves textual "
                      "names never expanded into concrete orderings AND crashes the "
                      "expression on the resolver's string-parse. It fails both the "
                      "reported crash scenario and any default-ordering test with a "
                      "textual name, so it would NOT resolve.",
        "rationale": "REJECT from `out = expandItems resolve items` via "
                     "`itemContribution`'s `.name n => resolve n` branch: at a name "
                     "item the image demands `resolve n`, but the rival returns "
                     "`[(n, false)]`. Refuted at a single name item `[Item.name 3]` "
                     "under a `resolve` whose value (`[(9, true)]`) differs from "
                     "`[(3, false)]` — a DISTINCT input point and branch from the "
                     "expression rivals, varying the `items` binder onto a name. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : expandOrderingTester [Item.name 3] (fun _ => [(9, true)]) "
            "= false := by\n  decide\n"),
    },
    {
        "id": "always-passthrough-never-resolve",
        "kind": "uniqueness",
        "expect": "reject",
        # Treat EVERY item as an already-formed expression: contribute
        # `[(n, false)]` for a name too, never consulting the resolver. Correct on
        # every expression item; diverges on the name sub-domain.
        "module": _flatmap("[(e, false)]", "[(n, false)]"),
        "refinement": "a counterpart that appended every item as-is and dropped the "
                      "recursive resolution emits a textual field-name raw instead "
                      "of expanding it into its concrete ordering(s), so the "
                      "default-ordering tests that assert a name resolves to real "
                      "column orderings fail — it would NOT resolve.",
        "rationale": "REJECT from `out = expandItems resolve items` via "
                     "`itemContribution`'s `.name n => resolve n` branch: at a name "
                     "item the image demands `resolve n`, but the rival returns "
                     "`[(n, false)]`, never consulting the resolver. Refuted at "
                     "`[Item.name 4]` under a `resolve` (`fun _ => [(2, true)]`) "
                     "whose value differs from `[(4, false)]` — a distinct input "
                     "point and `resolve` from inverted-discriminant, varying both "
                     "binders. If it verified => SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : expandOrderingTester [Item.name 4] (fun _ => [(2, true)]) "
            "= false := by\n  decide\n"),
    },
    {
        "id": "wrong-passthrough-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Right control flow but corrupts the expression's identity: contribute
        # `[(e + 1, false)]` for an expression item instead of `[(e, false)]`.
        # Correct on every name item and on the flag; diverges on the pass-through
        # identity.
        "module": _flatmap("[(e + 1, false)]", "resolve n"),
        "refinement": "a counterpart that passed an order expression through but "
                      "under a DIFFERENT identity (a freshly built expression, or "
                      "the wrong variable) emits an ordering by the wrong "
                      "expression, so a query ordering by the very passed-through "
                      "expression sorts on the wrong thing — it would NOT resolve.",
        "rationale": "REJECT from `out = expandItems resolve items` via the CONTENT "
                     "of `itemContribution`'s pass-through: it pins `[(e, false)]` "
                     "with the expression's OWN identity `e`, so a rival "
                     "contributing `[(e + 1, false)]` contradicts the image at any "
                     "expression item. Refuted at `[Item.expr 5]` (image demands "
                     "`[(5, false)]`, rival yields `[(6, false)]`) — a near-miss on "
                     "the same branch as the real-bug rival but at the IDENTITY, "
                     "not the routing, refuted at the same input under an "
                     "expression-agnostic `resolve`. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : expandOrderingTester [Item.expr 5] (fun _ => [(0, false)]) "
            "= false := by\n  decide\n"),
    },
    {
        "id": "drop-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Has the expression guard (so no crash) but contributes NOTHING for an
        # expression item (empty list). Correct on every name item; diverges on the
        # expression sub-domain by omission.
        "module": _flatmap("[]", "resolve n"),
        "refinement": "a counterpart that guarded the expression (so it did not "
                      "crash) but never appended it — silently dropping the order "
                      "expression from the result — leaves the query missing the "
                      "very expression it must order by, so the failing test that "
                      "orders by that expression fails (wrong/short ordering). It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = expandItems resolve items` via the "
                     "pass-through's EXISTENCE: `itemContribution` on an expression "
                     "yields the singleton `[(e, false)]`, but the rival yields the "
                     "empty list, so the sequences differ in length at any "
                     "expression item. Refuted at `[Item.expr 5]` (image demands "
                     "`[(5, false)]`, rival yields `[]`). If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : expandOrderingTester [Item.expr 5] (fun _ => [(0, false)]) "
            "= false := by\n  decide\n"),
    },
    # --- ADDED BY AUDIT. The five rivals above are all per-item CONTENT attacks
    # --- refuted at a length-1 input, so two clauses of `expandItems` went
    # --- unattacked by any reject case: the ORDER of the concatenation, and the
    # --- behaviour on inputs longer than the probed ones. The footer previously
    # --- argued an order rival was "NOT applicable" because a length-1 witness
    # --- cannot expose an order defect — true, and the answer is a length-2
    # --- witness, which builds fine here. Both rivals below are refuted at
    # --- `[Item.expr 5, Item.name 0]`, a length-2 MIXED point no other reject
    # --- case reaches.
    {
        "id": "order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Right per-item contribution on BOTH branches, but the contributions are
        # concatenated in REVERSE specification order. Correct on every input of
        # length <= 1 (so invisible to all five witnesses above); wrong on any
        # mixed or longer specification.
        "module": _impl(
            "    return (items.reverse.flatMap (fun it => match it with\n"
            "      | .expr e => [(e, false)]\n"
            "      | .name n => resolve n))"),
        "refinement": "a counterpart that accumulated the expansion in the "
                      "opposite direction — prepending each item's contribution "
                      "instead of appending it — emits the model's default "
                      "ordering back-to-front, so the query sorts by the right "
                      "set of orderings in the WRONG precedence. A default "
                      "ordering is precedence-sensitive by definition (the first "
                      "entry is the primary sort key), so any test asserting the "
                      "resulting order of rows, including the reported scenario "
                      "where a passed-through expression must lead, sees the rows "
                      "in a different order — it would NOT resolve.",
        "rationale": "REJECT from `out = expandItems resolve items` via the "
                     "ORDER/position clause rather than the per-item content: "
                     "`expandItems` is the front-recursive concatenation "
                     "`itemContribution it ++ expandItems rest`, so item `i`'s "
                     "contribution must precede item `i+1`'s. This rival emits "
                     "them back-to-front while getting every individual "
                     "contribution right. Refuted at the length-2 MIXED point "
                     "`[Item.expr 5, Item.name 0]` under `fun _ => [(9, true)]`: "
                     "the image demands `[(5, false), (9, true)]`, the rival "
                     "yields `[(9, true), (5, false)]`. This is the ONLY reject "
                     "case that varies the length/order binder — the other five "
                     "are length-1 and this rival is correct on every length-1 "
                     "input, so it is refutable at no point any of them probes. "
                     "If it verified => SPEC-TOO-WEAK on the order clause.",
        "witness": _tester(
            "example : expandOrderingTester [Item.expr 5, Item.name 0] "
            "(fun _ => [(9, true)]) = false := by\n  decide\n"),
    },
    {
        "id": "length-gated-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # A TUNED rival aimed at the battery's own blind spot: it agrees with the
        # frozen behaviour on every input of length <= 1 — i.e. on every point the
        # five original witnesses probe — and returns the empty expansion beyond.
        # It exists to show the spec still pins the LONGER sub-domain, which no
        # length-1 witness can attest.
        "module": _impl(
            "    if items.length ≤ 1 then\n"
            "      return (items.flatMap (fun it => match it with\n"
            "        | .expr e => [(e, false)]\n"
            "        | .name n => resolve n))\n"
            "    else\n"
            "      return []"),
        "refinement": "a counterpart that special-cased the trivial ordering "
                      "specification and fell out of the expansion for a longer "
                      "one returns an EMPTY expansion whenever the model declares "
                      "more than one default ordering entry, so such a model is "
                      "queried with no default ordering at all — the rows come "
                      "back unordered. Every default-ordering test over a "
                      "multi-entry specification, including the reported "
                      "multi-entry scenario, sees the wrong row order; it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = expandItems resolve items` on the "
                     "LENGTH sub-domain the rest of this battery leaves open: "
                     "`expandItems` pins the expansion at EVERY length, so "
                     "collapsing to `[]` beyond length 1 contradicts the image. "
                     "Deliberately constructed to be observationally identical to "
                     "the frozen impl at all four input points the five original "
                     "witnesses use, so it is a live check that the spec — and "
                     "not merely the probed points — is what rejects a wrong "
                     "impl. Refuted at `[Item.expr 5, Item.name 0]` under "
                     "`fun _ => [(9, true)]` (image demands "
                     "`[(5, false), (9, true)]`, rival yields `[]`). If it "
                     "verified => SPEC-TOO-WEAK beyond length 1.",
        "witness": _tester(
            "example : expandOrderingTester [Item.expr 5, Item.name 0] "
            "(fun _ => [(9, true)]) = false := by\n  decide\n"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling ships 10 SPEC cases (2 soundness positives, 1
# admissibility, 2 mandatory frame-mutation rivals, 5 uniqueness/partial-domain
# rivals) and 2 AXIOM_TESTS. The nagini bundle contracts ONE function,
# expand_default_ordering(kinds, ids), over two index-aligned READ-ONLY
# `List[int]` carriers at Acc(list_pred(.),1/2), pinning the output sequence to a
# @Pure fold `expanded`/`contribution` and treating the unchanged name machinery
# as an OPAQUE axiom resolve_name_seq (Ensures(True)). This backend models the
# SAME decision as a referentially-transparent FUNCTION `expandOrdering (items)
# (resolve) return out`, with the per-item image the pure
# `itemContribution`/`expandItems`: the two index-aligned lists collapse to one
# `List Item` (the kind discriminant becomes the `Item.expr`/`Item.name`
# constructor, the identity becomes the constructor's `Int` argument), and the
# opaque name machinery becomes the FREE function input `resolve` (quantified
# over, not axiomatized). The value surface carries across intact; the permission
# surface, the read-only carriers, and the opaque-axiom machinery do not exist
# here.
#
#   nagini case                                   -> here                              disposition
#   ----------------------------------------------------------------------------------------------
#   frame-mutate-ids                              -> (none)                            VACUOUS
#   frame-mutate-kinds                            -> (none)                            VACUOUS
#   real-bug-route-orderby-through-name-machinery -> real-bug-route-expr-through-resolver  PORTED
#   inverted-kind-discriminant                    -> inverted-discriminant             PORTED
#   always-passthrough-never-resolve              -> always-passthrough-never-resolve  PORTED
#   wrong-passthrough-identity                    -> wrong-passthrough-identity        PORTED
#   drop-passthrough                              -> drop-passthrough                  PORTED
#   (no nagini counterpart)                       -> order-reversed                    ADDED BY AUDIT
#   (no nagini counterpart)                       -> length-gated-collapse             ADDED BY AUDIT
#   pos-control-explicit-local                    -> pos-arms-reordered-local          PORTED (reshaped)
#   pos-control-precomputed-bound                 -> pos-closed-form                   PORTED (reshaped)
#   admissibility-mixed-ordering                  -> admiss-mixed-nondegenerate        RE-AIMED
#   AXIOM_TESTS (2)                               -> (none)                            DROPPED (G-AX lane)
#
# VACUOUS (frame-mutate-ids, frame-mutate-kinds): the nagini bundle's two
#   MANDATORY frame-mutation rivals keep the gold body verbatim then WRITE back
#   into a read-only carrier granted only at half permission (`ids.append(0)` /
#   `kinds.append(1)`), each rejected for INSUFFICIENT PERMISSION. This backend is
#   referentially transparent: `items` and `resolve` are immutable values, the
#   method declares no `mut` binder, there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the whole
#   class is vacuous. No substitute is fabricated (per the porting map).
#   DEMONSTRATED BY THE AUDIT rather than asserted, since "the carrier collapses
#   this distinction" is only a real reason when it is measured. A variant whose
#   impl region opens with `items := items ++ [Item.expr 0]` (and likewise
#   `resolve := (fun _ => [])`) does not elaborate, and the error is not a spec
#   verdict at all: "`items` cannot be mutated, only variables declared using
#   `let mut` can be mutated". So the write is rejected by the ELABORATOR before
#   any obligation is generated — there is no permission judgement for such a
#   rival to fail, and a case built on it would attribute its rejection to Velvet's
#   binder syntax rather than to the spec. Correctly dropped, not merely skipped.
# PORTED (5 uniqueness rivals): the partial-domain / value rivals carry across
#   intact — only the carrier changes from a nagini two-list `List[int]` fold with
#   an opaque `resolve_name_seq` axiom to a Velvet `List Item` map with a free
#   `resolve` function. Each keeps its nagini refinement argument (the pre-patch
#   crash, the inverted guard, the never-resolve raw-name emission, the corrupted
#   pass-through identity, the silently dropped expression) and is now backed by a
#   machine-checked witness. Where nagini relied on the opacity of
#   resolve_name_seq to block an equality, the velvet witness instead instantiates
#   the free `resolve` at a concrete separating closure and DECIDES the tester —
#   a stronger, executable refutation.
# PORTED-RESHAPED (2 soundness positives): the nagini positives both KEEP the
#   back-to-front prepend direction to avoid a front-recursive-fold proof gap.
#   pos-control-precomputed-bound (hoist the loop bound into a local `n`) maps to
#   pos-closed-form (collapse the whole loop to the closed form the post-image
#   names — a maximally different, loop-free correct impl, whose proof collapses
#   to a bare `loom_solve`; the loop-bound reshape itself is invisible on this
#   carrier because the frozen impl already reads `items.length` inline).
#   pos-control-explicit-local (hoist the pass-through identity into a local
#   `single`, branch on the textual case first) maps to pos-arms-reordered-local
#   (same reshape: name arm first, `single : Pair := (e, false)` staged into a
#   local, loop kept), whose reproof adds one Item case-split. Both verified
#   (lean_verify EXIT 0).
# RE-AIMED (admissibility-mixed-ordering -> admiss-mixed-nondegenerate): the
#   nagini case self-calls on an F2P-shaped MIXED input (an OrderBy item kind 1 +
#   a textual name kind 0) to show the read-only Acc(.,1/2) precondition ADMITS a
#   normal input. This backend's method has NO precondition, so that probe is
#   degenerate (every input is in-domain). Re-aimed at the residual total-domain
#   risk — a degenerate post-image — via an in-region assert that the per-item
#   image genuinely distinguishes its two branches (an expression is NOT resolved;
#   a name IS) and assembles the SAME mixed specification (`Item.expr 5`,
#   `Item.name 0`) in order. Verified EXIT 0.
# DROPPED (AXIOM_TESTS): the nagini file's two axiom-soundness/containment probes
#   (contribution(1,id)==PSeq(id) pass-through; the resolve_name machinery) are
#   G-AX's job. This bundle declares NO consumed axiom — the unchanged name
#   resolution enters as the free input `resolve`, an A-reference validated by
#   G-CONF, not a consumed contract (meta.json axioms: []) — so there is nothing
#   for a G-AX probe to check here, and the G-PBT gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER / POINT COVERAGE of the reject witnesses over the two input
#   binders of the sole ensures (pts = 4 distinct input points):
#     items (kind of element)   — expr (real-bug, wrong-passthrough-identity,
#                                  drop-passthrough), name (inverted-discriminant,
#                                  always-passthrough): BOTH branches of
#                                  `itemContribution` attacked.
#     items (identity)          — expr 5, name 3, name 4: varied (never held fixed).
#     items (length/order)      — CORRECTED BY AUDIT. The five original rivals are
#                                  all length-1 probes, and the claim that a
#                                  dedicated order/length reject was "NOT
#                                  applicable" was false: the reason given (a
#                                  length-1 witness cannot expose an order defect)
#                                  is correct but argues for a LONGER witness, not
#                                  against the case. A length-2 witness builds and
#                                  discriminates here, so two rivals were added —
#                                  `order-reversed` (right per-item contributions,
#                                  reversed concatenation: correct on every
#                                  length-<=1 input, so refutable at no point the
#                                  original five probe) and `length-gated-collapse`
#                                  (agrees with the frozen impl at all four of
#                                  those points, collapses beyond length 1). Both
#                                  are refuted at `[Item.expr 5, Item.name 0]`, and
#                                  both were confirmed non-tautologous: the same
#                                  witness built against a CORRECT loop-free impl
#                                  fails with `decide` reporting the proposition
#                                  false. The order clause is now attacked
#                                  NEGATIVELY as well as defended positively by
#                                  admiss-mixed-nondegenerate and pos-closed-form.
#     resolve                   — the free resolver is instantiated at a SEPARATING
#                                  closure in every witness (`_ => [(99,true)]`,
#                                  `_ => [(9,true)]`, `_ => [(2,true)]`,
#                                  `_ => [(0,false)]`) chosen so its value at the
#                                  probed name/expression identity differs from the
#                                  rival's contribution — the only way the routing
#                                  and never-resolve defects are observable. `resolve`
#                                  is never the answer key: on an expression item the
#                                  image is independent of it, and the two
#                                  expression rivals (identity, drop) are refuted
#                                  under a `resolve` whose value is irrelevant.
#   Every independent top-level behavior of the post-image is attacked: the
#   pass-through branch's ROUTING (real-bug, inverted), its EXISTENCE
#   (drop-passthrough), its IDENTITY (wrong-passthrough-identity), and the
#   resolution branch (inverted, always-passthrough). The order/length clause is
#   defended by the positives + admissibility.
#
# WITNESS MECHANICS: the tester+`decide` path is LIVE on the RIVAL side (unlike
#   the sibling django-11276, whose opaque `entityDecode` blocks it): the
#   postcondition `out = expandItems resolve items` mentions no opaque axiom —
#   `resolve` is a quantified parameter instantiated at a concrete decidable
#   closure in each witness, so `expandOrderingTester items resolve` reduces to a
#   ground boolean under `decide`. Every reject rival is loop-free
#   (`items.flatMap`) so its tester `decide`s and the refutation is a real
#   evaluation. No witness binds a hypothesis, so no consistency probe is needed.
#   Re-checked with scripts/lean_verify.sh by the audit: all 7 rival witnesses
#   exit 0, all 7 gold builds exit 1, and all 7 rival modules fail to verify
#   (correct reject).
#   HONEST LIMIT (see the module docstring): gold's side of the check is inert.
#   `Loop.forIn.loop` is `partial_fixpoint`, hence kernel-irreducible, so gold's
#   tester does not reduce for ANY argument — measured stuck even at `items = []`,
#   and stuck likewise for a `= true` assertion. The gold build therefore fails
#   unconditionally and is NOT evidence of discrimination. What the audit
#   substituted for it, per rival: the same witness rebuilt against a CORRECT
#   loop-free impl FAILS (`decide` proved the proposition `... = false` is false),
#   which is the anti-tautology fact the gold half was meant to supply; and
#   `native_decide` reduces gold's tester at each probed input to `true`,
#   confirming gold really does satisfy the spec there. This limit applies to
#   every loop-bearing velvet bundle (203 of them), not just this cell.
AXIOM_TESTS = []
