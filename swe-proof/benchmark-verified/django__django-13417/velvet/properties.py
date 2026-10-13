"""properties.py — G-PBT falsification battery for django__django-13417 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct ordered`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method, a PURE boolean decision over five
independent yes/no signals about a result set:

    ordered (isEmpty hasRawOrder defaultOn modelHasOrder isGrouped : Bool)
      return (out : Bool)

The postcondition pins the result exactly:

    ensures out = isOrdered isEmpty hasRawOrder defaultOn modelHasOrder isGrouped

where ``isOrdered`` is a total, fully-unfolded pure function of the five args
(``isEmpty || hasRawOrder || (defaultOn && modelHasOrder && !isGrouped)``). It
is GROUNDED — a computation over the inputs, not an opaque answer key — so
returning that disjunction inline IS the correct answer, carried here as an
honest cheapest-impl positive control rather than a wrong echo. Alongside the
exact-equality clause the spec pins four consequence clauses, each tying the
result to a witnessed input: an empty set is ordered; an explicitly-ordered set
is ordered; a set that is neither empty nor explicitly ordered but IS grouped is
NOT ordered; and an inherited-default-ordered non-grouped set IS ordered.

The live falsification surface is PARTIAL-DOMAIN: the carrier is a fully
transparent ``Bool``, so every one of the 2**5 = 32 input combinations is
``decide``-able. A rival correct on 31/32 combinations but wrong on one (above
all the discriminating combination: not-empty + no-raw-order + default-on +
model-has-order + grouped, where the flag must be FALSE) MUST be rejected.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. Structurally different but
    behaviourally identical impls (a single inline disjunction; the independent
    guards reordered with the grouped test nested; a named intermediate local)
    must still verify, else the spec is SPEC-TOO-STRONG on the shape of the
    impl. Each keeps the ``ensures`` obligation and only reshapes the executable
    surface (and, where the shape needs it, retunes the tactic body — elided
    from the spec view, so a proof reshape, not a spec change).
  * ADMISSIBILITY — the method carries no ``require`` clause, so the "a normal
    input satisfies the precondition" probe is not where the risk sits. The
    residual risk is a DEGENERATE post-image (a spec no impl can meet reads like
    a spec every impl meets). ``admiss-grounded`` discharges an in-region assert
    pinning the three interesting F2P-shaped points — a non-grouped
    inherited-default set is ordered, the SAME set grouped is NOT ordered, and an
    empty grouped set IS ordered — with the impl kept verbatim so the method's
    own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only heap input may carry a fractional permission an impl overwrites.
    Lean and Velvet are referentially transparent: all five inputs are immutable
    ``Bool`` values (none declared ``mut``), there is no heap and no aliasing, so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated — reported as an omission in the footer.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
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
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired decision on some sub-domain and MUST be rejected:
    the literal pre-patch bug, the inverted grouped polarity, the empty
    consequence dropped for grouped empty sets, the model-ordering conjunct
    ignored, the raw-order guard dropped, grouping hoisted so it suppresses ALL
    ordering (the over-correction), and the constant-true near-miss. Each
    is a loop-free closed form (so its tester kernel-reduces under ``decide``)
    with a machine-checked refutation witness at a concrete decidable input.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``orderedTester isEmpty hasRawOrder defaultOn modelHasOrder
isGrouped = false`` says the extracted program's result violates the
postcondition at that concrete input, checked in a file whose ``prove_correct``
block has been stripped (no tactic script can mask the verdict). The carrier is
a ground ``Bool`` at every argument, so every tester reduces to a ground boolean
and ``decide`` closes it. The discrimination is thus structural, not a
tactic-tuning artifact. (Verified out of band: each witness builds green against
its rival and red against the frozen solution.)

WITNESS PLACEMENT. The seven rejects probe seven DISTINCT input points, so every
one of the five input binders is genuinely varied rather than pinned:
  isEmpty       — T at (T,F,F,F,T), F at the other six;
  hasRawOrder   — T at (F,T,F,F,F) and (F,T,F,F,T), F at the other five;
  defaultOn     — T and F both appear;
  modelHasOrder — T and F both appear;
  isGrouped     — T and F both appear.
The variation is meaningful and not two spellings of one point: each witness
point was checked to lie inside its OWN rival's divergence set against the full
32-combination domain, and the seven points are pairwise distinct. Both error
directions are represented — rivals that report ordered too OFTEN and rivals
that suppress ordering too AGGRESSIVELY — so a fix that overshoots is caught as
well as one that undershoots. A rival that mishandled only a fixed input
coordinate would still be caught.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the five signals
are read purely for their truth value and there is no consumed callee contract.
The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13417"
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
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the gold-faithful nested decision).
_IMPL = """    -- impl-start
    if isEmpty then
      return true
    else
      if hasRawOrder then
        return true
      else
        if defaultOn && modelHasOrder && !isGrouped then
          return true
        else
          return false
    -- impl-end"""

# The first executable line of the impl region; an in-region assert prepended
# here (before the frozen decision) is discharged by the retuned proof without
# disturbing the method's own obligation.
_IMPL_TOP = """  do
    -- impl-start
    if isEmpty then"""

# The FULL frozen proof body (everything after `prove_correct ordered by`).
_PROOF = """prove_correct ordered by
  loom_solve <;> simp_all [isOrdered]"""


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `orderedTester ... = false` says the extracted program's
# ---- result violates the postcondition at that concrete input.
def _tester(body):
    return ("extract_program_for ordered\n"
            "prove_precondition_decidable_for ordered\n"
            "prove_postcondition_decidable_for ordered\n"
            "derive_tester_for ordered\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps `ensures out = isOrdered ...` and
    # only reshapes the executable surface (retuning the tactic body where the
    # new shape needs it).
    # =====================================================================
    {
        "id": "pos-single-return",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest impl — a single inline return of the grounded
        # disjunction the post-image names directly. No branches, no locals.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    return isEmpty || hasRawOrder || "
            "(defaultOn && modelHasOrder && !isGrouped)\n"
            "    -- impl-end"),
        "rationale": "the maximally-minimal correct impl: one boolean return of "
                     "the grounded disjunction that IS isOrdered fully unfolded. "
                     "Since the decision is grounded (a total function of the five "
                     "args, not an opaque answer key) this is the correct answer "
                     "and must satisfy `out = isOrdered ...`. A structurally-minimal "
                     "correct impl failing here would be SPEC-TOO-STRONG. Exercises "
                     "the obligation from a maximally different (branch-free) shape.",
    },
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different control flow: raw-order guard first, then empty,
        # then a NESTED is-grouped branch (Velvet bans `else if`, so it is a
        # nested if). Same truth table, no induction or framing needed.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if hasRawOrder then\n"
            "      return true\n"
            "    else\n"
            "      if isEmpty then\n"
            "        return true\n"
            "      else\n"
            "        if defaultOn && modelHasOrder then\n"
            "          if isGrouped then\n"
            "            return false\n"
            "          else\n"
            "            return true\n"
            "        else\n"
            "          return false\n"
            "    -- impl-end"),
        "rationale": "the independent guards reordered (raw-order first, then "
                     "empty) with the grouped test split into a nested branch; "
                     "same truth table, no induction lemma or framing assert "
                     "needed for a pure boolean. Must verify (else SPEC-TOO-STRONG "
                     "on the exact branch order/shape).",
    },
    {
        "id": "pos-local-var",
        "kind": "soundness",
        "expect": "verify",
        # Compute an intermediate `let` for the two unconditional guards, then
        # branch on it; same truth table, different data shape.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    let base := isEmpty || hasRawOrder\n"
            "    if base then\n"
            "      return true\n"
            "    else\n"
            "      if defaultOn && modelHasOrder && !isGrouped then\n"
            "        return true\n"
            "      else\n"
            "        return false\n"
            "    -- impl-end"),
        "rationale": "fold the two unconditional guards into a named local and "
                     "branch on it; same truth table, different shape. Must verify "
                     "(else SPEC-TOO-STRONG). Guards against a spec that only "
                     "accepts the exact gold branch nesting.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause, so the "a normal input satisfies the
    # precondition" probe is not the risk; the residual risk is a DEGENERATE
    # post-image. This case discharges an in-region assert at the three
    # F2P-shaped points (non-grouped default-ordered set ACCEPTED, the same set
    # grouped REJECTED, empty grouped set ACCEPTED), establishing the post-image
    # genuinely discriminates them. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the proof gains one `decide` arm
    # to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_TOP,
            "  do\n"
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss\n"
            "      (isOrdered false false true true true = false ∧\n"
            "       isOrdered false false true true false = true ∧\n"
            "       isOrdered true false false false true = true))\n"
            "    if isEmpty then",
            _PROOF,
            "prove_correct ordered by\n"
            "  loom_solve <;> first | decide | simp_all [isOrdered]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: it demands NOT-ordered for a non-empty, "
                     "raw-order-free, inherited-default, GROUPED set (the case the "
                     "fix targets), ordered for that same set non-grouped, and "
                     "ordered for an empty grouped set. The in-region assert must "
                     "discharge (else the obligation is degenerate / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so "
                     "`out = isOrdered ...` still verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating delta. The verbatim pre-patch decision: drop the
        # `&& !isGrouped` conjunct. Correct on every combination EXCEPT the one
        # the fix targets (not-empty, no-raw-order, default-on, model-has-order,
        # grouped), where it reports ordered though the flag must be false.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if isEmpty then\n"
            "      return true\n"
            "    else\n"
            "      if hasRawOrder then\n"
            "        return true\n"
            "      else\n"
            "        if defaultOn && modelHasOrder then\n"
            "          return true\n"
            "        else\n"
            "          return false\n"
            "    -- impl-end"),
        "refinement": "this is the literal pre-image decision (the grouped "
                      "conjunct omitted). Its faithful real counterpart is the "
                      "UNCHANGED buggy body, which reports the grouped, "
                      "inherited-default result set as ordered — exactly the "
                      "failing case the regression tests add — so it would NOT "
                      "resolve. A verifying rival here would be a true "
                      "verify-not-resolve break.",
        "rationale": "REJECT from `out = isOrdered ...`, specifically the pinned "
                     "clause (isEmpty=false ∧ hasRawOrder=false ∧ isGrouped=true) "
                     "→ out=false: at (F,F,T,T,T) the rival returns true but the "
                     "decision is false. Refuted at the load-bearing "
                     "grouped-default sub-domain; SPEC-TOO-WEAK if it verified.",
        "witness": _tester(
            "example : orderedTester false false true true true = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-flip-grouped-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # Use is-grouped with INVERTED polarity (drops the `!`): report ordered
        # for a grouped default-ordered set and NOT ordered for the non-grouped
        # one. Diverges on the grouped sub-domain the opposite way to gold.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if isEmpty then\n"
            "      return true\n"
            "    else\n"
            "      if hasRawOrder then\n"
            "        return true\n"
            "      else\n"
            "        if defaultOn && modelHasOrder && isGrouped then\n"
            "          return true\n"
            "        else\n"
            "          return false\n"
            "    -- impl-end"),
        "refinement": "inverts the grouped polarity: its faithful patch reports a "
                      "NON-grouped inherited-default set as not ordered (failing "
                      "the P2P assertion that such a set stays ordered) and a "
                      "grouped one as ordered (failing the F2P). Does not resolve.",
        "rationale": "REJECT from `out = isOrdered ...`: at (F,F,T,T,F) the "
                     "decision is true (non-grouped default order) but the rival "
                     "returns false. Refuted at the non-grouped default-order "
                     "point — a DISTINCT sub-domain from the pre-patch rival "
                     "(isGrouped flipped). SPEC-TOO-WEAK if it verified.",
        "witness": _tester(
            "example : orderedTester false false true true false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-empty-misses-grouped",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the unconditional "empty ⇒ ordered" guarantee for grouped empty
        # sets: gate the empty guard on `!isGrouped`. Correct everywhere except
        # an empty set that is also grouped, which it wrongly reports not ordered.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if isEmpty && !isGrouped then\n"
            "      return true\n"
            "    else\n"
            "      if hasRawOrder then\n"
            "        return true\n"
            "      else\n"
            "        if defaultOn && modelHasOrder && !isGrouped then\n"
            "          return true\n"
            "        else\n"
            "          return false\n"
            "    -- impl-end"),
        "refinement": "drops the unconditional empty-⇒-ordered guarantee for "
                      "grouped empty sets: its faithful patch reports a "
                      "statically-empty result set that is ALSO grouped as not "
                      "ordered. Honest scope of the claim: the shipped "
                      "regression suite pins the empty case only on a NON-grouped "
                      "empty set, so this rival is not refuted by a shipped test "
                      "— it is refuted by the SPEC, whose first pinned "
                      "consequence (isEmpty=true → out=true) is unconditional in "
                      "the other four signals. The combination is reachable in the "
                      "real carrier (static emptiness is recorded on the filter "
                      "tree and is independent of the grouping flag, so a set can "
                      "be both), which is why the unconditional clause is the "
                      "faithful reading and this rival contradicts it. Carried as "
                      "a SPEC-strength rival, not a test-failure rival.",
        "rationale": "REJECT from the pinned clause isEmpty=true → out=true: at "
                     "(T,F,F,F,T) the rival returns false but the decision is "
                     "true. Refuted at the ONLY point with isEmpty=true, so this "
                     "rival is what varies the isEmpty binder. SPEC-TOO-WEAK if "
                     "it verified.",
        "witness": _tester(
            "example : orderedTester true false false false true = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-ignore-model-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Report ordered whenever a default ordering is active and the set is not
        # grouped, EVEN IF the model declares no default ordering
        # (modelHasOrder=false). Drops the modelHasOrder conjunct.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if isEmpty then\n"
            "      return true\n"
            "    else\n"
            "      if hasRawOrder then\n"
            "        return true\n"
            "      else\n"
            "        if defaultOn && !isGrouped then\n"
            "          return true\n"
            "        else\n"
            "          return false\n"
            "    -- impl-end"),
        "refinement": "reports ordered when default ordering is active even though "
                      "the model declares no default ordering (modelHasOrder="
                      "false). Its faithful patch reports a set with no actual "
                      "ordering as ordered, failing the no-ordering / "
                      "cleared-ordering P2P assertions. Does not resolve.",
        "rationale": "REJECT from `out = isOrdered ...`: at (F,F,T,F,F) the "
                     "decision is false (modelHasOrder is false, so no default "
                     "ordering to honour) but the rival returns true. This is the "
                     "only witness holding modelHasOrder=false while defaultOn=true "
                     ", so it varies the modelHasOrder binder. SPEC-TOO-WEAK if "
                     "it verified.",
        "witness": _tester(
            "example : orderedTester false false true false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-drop-raw-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the explicit-ordering guard entirely: a set with an attached raw
        # ordering but no inherited default falls through to false. Correct
        # everywhere except when hasRawOrder is the ONLY active signal.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if isEmpty then\n"
            "      return true\n"
            "    else\n"
            "      if defaultOn && modelHasOrder && !isGrouped then\n"
            "        return true\n"
            "      else\n"
            "        return false\n"
            "    -- impl-end"),
        "refinement": "drops the explicit-ordering guard: its faithful patch "
                      "reports a set carrying an attached explicit/raw ordering "
                      "(but no inherited default) as not ordered, failing the "
                      "explicit-ordering and order-by-extra P2P assertions. Does "
                      "not resolve.",
        "rationale": "REJECT from the pinned clause hasRawOrder=true → out=true: "
                     "at (F,T,F,F,F) the rival returns false but the decision is "
                     "true. This is the only witness holding hasRawOrder=true, so "
                     "it is what varies the hasRawOrder binder and attacks the "
                     "explicit-ordering consequence clause. SPEC-TOO-WEAK if it "
                     "verified.",
        "witness": _tester(
            "example : orderedTester false true false false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-grouped-suppresses-all",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-SUPPRESSION, the mirror of the pre-image bug and the one direction
        # no other rival attacks. Every existing rival either under-suppresses
        # (reports ordered too often) or mis-polarises the grouped test INSIDE the
        # inherited-default branch. This one hoists grouping to the TOP: grouping
        # suppresses the explicit ordering and the emptiness signal too, not just
        # the inherited default. Correct on the whole non-grouped half of the
        # domain and correct at the discriminating point the fix targets, so it
        # would pass a battery that only checked "is the grouped-default case
        # false?" — the over-correction a plausible wrong fix actually makes.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    if isGrouped then\n"
            "      return false\n"
            "    else\n"
            "      return isEmpty || hasRawOrder || (defaultOn && modelHasOrder)\n"
            "    -- impl-end"),
        "refinement": "suppresses ordering for EVERY grouped result set, not only "
                      "one whose sole ordering is the inherited model default. Its "
                      "faithful patch reports a grouped set carrying an explicit "
                      "attached ordering as not ordered, and a grouped statically-"
                      "empty set as not ordered — so it fails the explicit-ordering "
                      "direction while still fixing the inherited-default one. It "
                      "resolves the newly-added assertions and BREAKS standing ones, "
                      "so it does not resolve the instance.",
        "rationale": "REJECT from two pinned consequence clauses at once, both of "
                     "which are unconditional in isGrouped: hasRawOrder=true → "
                     "out=true (refuted at (F,T,F,F,T), the witness point) and "
                     "isEmpty=true → out=true (refuted at (T,F,F,F,T)). Verified "
                     "out of band: the rival build accepts the witness (exit 0) "
                     "and the frozen solution rejects it with `decide` proving the "
                     "proposition FALSE at that input (exit 1) — a semantic "
                     "refutation, not a tactic gap. This is the only witness "
                     "holding hasRawOrder=true AND isGrouped=true together, so it "
                     "is what separates 'grouping suppresses an INHERITED default' "
                     "from 'grouping suppresses all ordering'. SPEC-TOO-WEAK if it "
                     "verified.",
        "witness": _tester(
            "example : orderedTester false true false false true = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: always-ordered. Trivially wrong (admits a grouped
        # default-only set, a no-ordering set, etc.). Its faithful patch
        # (`return True`) makes every negative-ordering assertion fail.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    return true\n"
            "    -- impl-end"),
        "refinement": "always returns True (cheap supporting near-miss). Its "
                      "faithful patch makes every negative-ordering assertion fail "
                      "(no-default-or-explicit-ordering, cleared-ordering, and the "
                      "F2P grouped-default tests). Does not resolve.",
        "rationale": "REJECT from `out = isOrdered ...` on the all-false input "
                     "(F,F,F,F,F), where the decision is false but the rival "
                     "returns true. Refuted at the all-false point — a sixth "
                     "distinct input, pinning the polarity of the result on the "
                     "sub-domain where nothing makes the set ordered. "
                     "SPEC-TOO-WEAK if it verified.",
        "witness": _tester(
            "example : orderedTester false false false false false = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (3
# soundness positives, 1 admissibility, 5 uniqueness/partial-domain rivals) and
# an EMPTY AXIOM_TESTS. The sibling contracts ONE function, `ordered`, over five
# `bool` value inputs; there are no heap-carried inputs, no @ContractOnly axioms
# and no A-reference deep models. The velvet bundle models the SAME single
# decision over five `Bool` inputs, so the port is near-total — the carrier is
# identical (transparent `Bool`), only the witness mechanics are new.
#
#   sibling case                    kind          -> here                         disposition
#   ------------------------------------------------------------------------------------------------
#   pos-single-return               soundness     -> pos-single-return            PORTED
#   pos-reorder-branches            soundness     -> pos-reorder-branches         PORTED
#   pos-local-var                   soundness     -> pos-local-var                PORTED
#   admiss-f2p-shaped               admissibility -> admiss-grounded              PORTED (re-aimed)
#   weak-prepatch-bug               uniqueness    -> weak-prepatch-bug            PORTED
#   weak-flip-grouped-polarity      uniqueness    -> weak-flip-grouped-polarity   PORTED
#   weak-empty-misses-grouped       uniqueness    -> weak-empty-misses-grouped    PORTED
#   weak-ignore-model-order         uniqueness    -> weak-ignore-model-order      PORTED
#   weak-constant-true              uniqueness    -> weak-constant-true           PORTED
#   (—)                             uniqueness    -> weak-drop-raw-order          ADDED
#   (—)                             uniqueness    -> weak-grouped-suppresses-all  ADDED (audit)
#
# PORTED (all nagini cases): the carrier is the same five `Bool` signals and the
#   same grounded decision, so every nagini case has a direct counterpart. The
#   three positive controls reshape control flow (inline disjunction; reordered
#   guards with a nested grouped branch; a named local) — Velvet bans `else if`,
#   so the reorder case nests its branches, and all three verify under the
#   BYTE-IDENTICAL frozen tactic body (`loom_solve <;> simp_all [isOrdered]`),
#   none needing a retune and none needing a new lemma. Only `admiss-grounded`
#   retunes the tactic body, and only to add a `decide` arm for its ground
#   assert. The admissibility case is
#   RE-AIMED: nagini asserts `ordered(...)` values on F2P-shaped inputs to show
#   the precondition admits them; here there is no `require` clause, so the
#   sharper residual risk is a degenerate post-image — the in-region assert pins
#   the same three F2P-shaped points (grouped-default REJECTED, non-grouped-
#   default ACCEPTED, empty-grouped ACCEPTED) directly on `isOrdered`. The five
#   uniqueness rivals port verbatim in behaviour; each gains a machine-checked
#   `orderedTester` witness (the new work — nagini relied on Viper's verdict).
# ADDED (weak-grouped-suppresses-all): a seventh rival, added by the independent
#   audit of this battery. Every other rival errs by under-suppressing (ordered
#   too often) or by flipping the grouped test inside the inherited-default
#   branch; none tests the OVER-correction, where grouping is hoisted above the
#   emptiness and explicit-ordering guards and suppresses them too. That rival is
#   correct at the discriminating point the fix targets, so a battery without it
#   cannot distinguish "grouping suppresses an INHERITED default" (the spec) from
#   "grouping suppresses all ordering". It also supplies the only witness point
#   holding hasRawOrder and isGrouped true together.
# ADDED (weak-drop-raw-order): a sixth rival dropping the explicit-ordering guard.
#   Nagini's five rivals never hold hasRawOrder=true, so without this the
#   hasRawOrder binder would be pinned at false across every reject witness and a
#   rival that mishandled ONLY the explicit-ordering guard would slip through. It
#   attacks the pinned clause hasRawOrder=true → out=true, refuted at (F,T,F,F,F).
# FRAME-MUTATION: no sibling case exists (the nagini docstring records the class
#   as N/A — every input is a `bool` passed by value, nothing to overwrite). On
#   this referentially-transparent backend it is likewise vacuous.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
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
# AXIOM_TESTS (0): the sibling ships none (meta.axioms == []). The gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has five input binders (isEmpty,
#   hasRawOrder, defaultOn, modelHasOrder, isGrouped) and, alongside the exact-
#   equality clause `out = isOrdered ...`, four pinned consequence clauses. The
#   seven reject witnesses probe seven DISTINCT input points (pts=7):
#     (F,F,T,T,T) (F,F,T,T,F) (T,F,F,F,T) (F,F,T,F,F) (F,T,F,F,F) (F,F,F,F,F)
#     (F,T,F,F,T).
#   Every binder takes BOTH values across the witnesses: isEmpty=T only at the
#   empty-misses-grouped point, hasRawOrder=T at the drop-raw-order and
#   grouped-suppresses-all points, and defaultOn/modelHasOrder/isGrouped each
#   range over T and F. The variation is MEANINGFUL, not two spellings of one
#   point: each rival's own witness point lies inside that rival's divergence set
#   from the frozen decision, checked against the full 32-point domain — the
#   rivals diverge on 1, 2, 4, 1, 7, 7 and 5 of the 32 combinations respectively,
#   and no two witness points coincide. Each pinned consequence clause is
#   attacked: isEmpty⇒ordered by empty-misses-grouped (and by
#   grouped-suppresses-all at a second point), hasRawOrder⇒ordered by
#   drop-raw-order and by grouped-suppresses-all, the grouped⇒not-ordered clause
#   by prepatch (and flip on the opposite side), the non-grouped-default⇒ordered
#   clause by flip, and the exact-equality clause by ignore-model-order and
#   constant-true. Both error DIRECTIONS are covered: under-suppression (prepatch,
#   ignore-model-order, constant-true) and over-suppression
#   (grouped-suppresses-all, drop-raw-order, empty-misses-grouped). No rival that
#   mishandled only a fixed input coordinate could slip through.
AXIOM_TESTS = []
