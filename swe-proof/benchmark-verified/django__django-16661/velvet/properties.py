"""properties.py — G-PBT falsification battery for django__django-16661 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct keptSegments`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and FAIL,
BY DECIDING THE NEGATION, against a correct impl of the same spec. On this cell
that second subject is the declared ``witness_reference`` rather than the frozen
solution, for the reason set out under WITNESS MECHANICS below).

DEFENDED SURFACE (one contracted method over a finite list of walked segments):

    keptSegments (hops : List Hop) return (out : List Bool)
        ensures out = keepMask hops

with ``keepMask`` mapping, segment by segment and in order,
``keepSegment h`` — the per-segment keep/drop decision:

    keepSegment h = h.isFirst
      ∨ (h.priorIsRelation
          ∧ ¬h.concreteParentLink
          ∧ ¬h.redundantLocalValue
          ∧ (¬h.hasRedundantLocalValue ∨ ¬h.priorAlreadyCovers))

``hops`` is the sole input binder; each element carries SEVEN boolean facts. The
first segment is always recorded; a non-first segment is recorded exactly when
the prior step entered a further record AND the segment is not locally redundant,
redundancy being the disjunction of three independent conditions
(``concreteParentLink``, ``redundantLocalValue``, or
``hasRedundantLocalValue ∧ priorAlreadyCovers``). ``targetOfPrior`` is a coarser
redundancy flag the desired decision does NOT consult — it exists on the carrier
only so the superseded rule can name it. The load-bearing content is that the
retention of a segment is decided by these precise conditions rather than by the
coarse ``targetOfPrior`` test: the two diverge exactly on the sub-domain where a
segment is flagged by the coarse test yet is a genuine descent under the precise
rule.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``Hop`` is a structure of seven ``Bool`` fields with ``DecidableEq``, and
``keepSegment`` / ``keepMask`` are concrete ``def``s in the ``pure`` region (the
``axioms`` region declares nothing). So each rival's violation reduces to a
decidable equality of concrete values, and a ``decide`` witness at a small
literal input discriminates. The reject lane is therefore fully expressible on
this carrier — no NO-REJECT-LANE collapse.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating loop collapsed to the closed
    form the post-image names; the per-segment decision bound to a local) must
    still verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the ``pre-conditions`` region is empty (no ``require``), so
    the usual "a normal input satisfies the precondition" probe is vacuous. The
    residual risk on this transparent carrier is that the post-image is
    UNSATISFIABLE / DEGENERATE at the interesting point — that it does not
    actually demand retention on a genuine descent while dropping a redundant
    segment. ``admiss-grounded`` discharges an in-region assert pinning BOTH
    directions of the per-segment decision at an F2P-shaped input; the impl is
    kept verbatim so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only heap input may carry a fractional permission an impl
    overwrites. Lean and Velvet are referentially transparent: ``hops`` is an
    immutable value (declared read-only, not ``mut``), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe to
    build. Not fabricated — reported as an omission in the footer.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired decision on some sub-domain and MUST be rejected:
    the superseded coarse rule, unconditional retention, dropping each of the
    redundancy conjuncts in turn, dropping the first-segment rule, and the
    traversal ORDER (a clause the list carrier introduces). Each is a loop-free
    closed form (so its tester kernel-reduces) with a machine-checked refutation
    witness.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``keptSegmentsTester args = false`` says the extracted
program's result violates the postcondition at that concrete input, checked in a
file whose ``prove_correct`` block has been stripped (no tactic script can mask
the verdict). Every reject rival is reshaped into a LOOP-FREE closed form, so ITS
tester kernel-reduces under ``decide``.

THE FROZEN SOLUTION CANNOT SERVE AS THE WITNESS'S SECOND SUBJECT, and this is
the load-bearing fact about this cell. Its impl keeps a ``while`` loop whose
fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold, so ``decide`` against it is stuck for EVERY claim rather than deciding
any. Measured here on ``weak-always-retain``'s witness: the real claim
(``... = false``) and its exact opposite (``... = true``) both fail against the
frozen solution with the identical

    Tactic `decide` failed for proposition ... did not reduce to `isTrue` or
    `isFalse`.

so the frozen-side exit code carries NO information, and a forged witness
asserting a rival is CORRECT would clear both halves of the usual check. An
earlier revision of this battery read that stuck failure AS the discrimination
("its tester decides while the loop-bearing frozen solution cannot reduce"),
which is precisely the ``witness-undecided`` forgery: it attests to a refutation
the kernel never performed. Every reject case therefore carries
``witness_reference = _LOOPFREE`` — the same loop-free closed form shipped as the
``pos-closed-form`` positive, which implements the frozen spec CORRECTLY and does
reduce — so each witness is refuted against an impl that actually decides. The
gate independently checks that reference shares the frozen spec and VERIFIES
before using it (an impl that failed everything would refute every witness).
Verified per-case against that reference: each of the six witnesses fails there
by ``decide`` PROVING the negation, and the corresponding ``= true`` claim
succeeds — a real refutation, not a stuck reduction. ``pos-closed-form`` carries
that identical source as an ``expect="verify"`` case, so the battery itself
records that loop-freeness is not what any rival is being rejected for.

WITNESS PLACEMENT. The six rejects probe six DISTINCT input points, chosen so
that EACH of the six facts the decision consults — plus ``targetOfPrior`` and
``hops.length`` — takes both values across the reject battery. No single fact is
pinned, so a rival that mishandled only one fact could not slip through.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the per-segment
facts are read-only inputs, not consumed contracts. The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16661"
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

# The WHOLE executable body of the method: the backward accumulating loop over
# the segments. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`).
_IMPL = """    let mut result : List Bool := []
    let mut i := hops.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ hops.length
      invariant result = keepMask (hops.drop i)
      done_with i = 0
      decreasing i
    do
      let h := hops[i - 1]!
      result := keepSegment h :: result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "keptSegments impl region drifted from expected text"

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let h := hops[i - 1]!
      result := keepSegment h :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop body drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut result : List Bool := []"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this to a bare `loom_solve`; the tactic body is
# elided from the spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct keptSegments by
  loom_solve
  rw [keepMask_drop_step hops i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- Hop literal builder. Named fields, so declaration order is irrelevant;
# ---- the tester fixes the element type to `Hop`, so no annotation is needed.
def _hop(isFirst, priorIsRelation, concreteParentLink, redundantLocalValue,
         hasRedundantLocalValue, priorAlreadyCovers, targetOfPrior):
    def b(x):
        return "true" if x else "false"
    return ("{isFirst := %s, priorIsRelation := %s, concreteParentLink := %s, "
            "redundantLocalValue := %s, hasRedundantLocalValue := %s, "
            "priorAlreadyCovers := %s, targetOfPrior := %s}" % (
                b(isFirst), b(priorIsRelation), b(concreteParentLink),
                b(redundantLocalValue), b(hasRedundantLocalValue),
                b(priorAlreadyCovers), b(targetOfPrior)))


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `keptSegmentsTester args = false` says the extracted program's
# ---- result violates the postcondition at that concrete input.
_TESTER = (
    "extract_program_for keptSegments\n"
    "prove_precondition_decidable_for keptSegments\n"
    "prove_postcondition_decidable_for keptSegments\n"
    "derive_tester_for keptSegments\n\n"
)


def _witness(hops_literal):
    return _TESTER + f"example : keptSegmentsTester {hops_literal} = false := by\n  decide\n"


# ---- The witness REFERENCE subject. The frozen impl's `while` loop elaborates
# ---- through Classical.choice, so `decide` against it is stuck for every claim
# ---- and its exit code discriminates nothing (see WITNESS MECHANICS above).
# ---- This is the same loop-free closed form shipped as `pos-closed-form`: it
# ---- shares the frozen spec, implements it CORRECTLY, and reduces — so every
# ---- reject witness is refuted against an impl that genuinely decides. The gate
# ---- re-checks that it verifies before trusting it as a subject.
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL, "    return (keepMask hops)"),
    _PROOF, "prove_correct keptSegments by\n  loom_solve")


# ---------------------------------------------------------------------------
# Closed-form rivals. keepMask hops = hops.map keepSegment, so each rival is a
# loop-free `.map` whose per-element function is a mangled keepSegment (or a
# structural transform of the whole mask). Loop-free => the tester reduces under
# `decide`.
# ---------------------------------------------------------------------------
def _map_rival(fn_body):
    return _swap(_BASE, _IMPL,
                 "    return (hops.map (fun h =>\n"
                 f"      {fn_body}))")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = keepMask hops`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same flag list; the loop-specific proof is
        # retuned to a bare `loom_solve` since the impl now matches the
        # post-image syntactically.
        # This is the SAME source every reject case names as its
        # `witness_reference`, shipped here as a verify case so the battery
        # itself records that loop-freeness is not what any rival is rejected for.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that returns the flag list directly must "
                     "satisfy `out = keepMask hops`; a correct reshape of the "
                     "modeled behaviour verifying is exactly what SPEC-TOO-STRONG "
                     "would deny. Exercises the obligation from a maximally "
                     "different (loop-free) control-flow shape. Ports the "
                     "sibling's structurally-different-but-correct positive.",
    },
    {
        "id": "pos-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-segment decision to a local `k` inside the loop
        # instead of prepending the expression directly. Same value flow; the
        # loop and the front-recursive invariant are unchanged, so the frozen
        # proof still closes untouched. This is the loop-preserving analogue of
        # the sibling's branch-reorder positive.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let h := hops[i - 1]!\n"
            "      let k : Bool := keepSegment h\n"
            "      result := k :: result\n"
            "      i := i - 1"),
        "rationale": "binding the per-segment decision to a local before "
                     "prepending it computes the same flag list element-for-"
                     "element, with the loop and invariant unchanged, so the "
                     "frozen proof closes and `out = keepMask hops` still holds; "
                     "a correct reshape must verify. (Sibling: pos-control-"
                     "branch-reorder.)",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the "a normal input meets
    # the precondition" probe is vacuous. Re-aimed at the residual risk that the
    # post-image is UNSATISFIABLE / DEGENERATE at the interesting point. This
    # case discharges an in-region assert pinning BOTH directions of the
    # per-segment decision at an F2P-shaped input: a genuine descent flagged by
    # the coarse superseded test must still be RECORDED, while a locally
    # redundant segment must be DROPPED. The surrounding impl is kept verbatim so
    # the method's own obligation still discharges; the assert is live (a false
    # claim leaves an unsolved goal), and the proof's alternation gains one
    # `decide` arm to close it.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `assert\n"
                "      (keepMask [" + _hop(False, True, False, False, False, False, True) + "]\n"
                "         = [true] ∧\n"
                "       keepMask [" + _hop(False, True, True, False, False, False, False) + "]\n"
                "         = [false]))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct keptSegments by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [keepMask_drop_step hops i (by omega) (by omega)]; simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: it demands a genuine descent that the "
                     "coarse superseded test would have flagged (`targetOfPrior` "
                     "true, but not locally redundant) be RECORDED (`[true]`), and "
                     "a locally redundant segment (`concreteParentLink` true) be "
                     "DROPPED (`[false]`). The in-region assert must discharge "
                     "(else the obligation is unsatisfiable / PRECOND-TOO-STRONG); "
                     "the impl is verbatim so `out = keepMask hops` still verifies. "
                     "(Sibling: admissibility-f2p-shape, re-aimed.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-superseded-coarse-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # The superseded rule: a non-first segment is recorded iff the prior step
        # entered a further record AND the coarse `targetOfPrior` flag is unset.
        # Correct on most paths; wrong exactly on the sub-domain where a genuine
        # descent is flagged by the coarse test (targetOfPrior true) yet passes
        # every precise redundancy conjunct — the F2P family.
        "module": _map_rival(
            "h.isFirst || (h.priorIsRelation && !h.targetOfPrior)"),
        "refinement": "this is the literal superseded decision. On the F2P "
                      "scenario a genuine descent is flagged by the coarse test "
                      "(targetOfPrior true) although it is neither a concrete-"
                      "ancestor link nor the record's own identity, so the rule "
                      "drops it, mis-shortcutting the path and wrongly disallowing "
                      "the lookup — exactly the regression the failing test pins. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = keepMask hops`: at a hop with "
                     "priorIsRelation true, targetOfPrior true, and none of the "
                     "precise redundancy conditions set, the post-image records "
                     "the segment (`true`) but the rival drops it (`false`). "
                     "Refuted on the coarse-flag-but-genuine-descent sub-domain; "
                     "the sole witness with `targetOfPrior` true. (Sibling: "
                     "prepatch-target-fields.)",
        "witness": _witness("[" + _hop(False, True, False, False, False, False, True) + "]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-always-retain",
        "kind": "uniqueness",
        "expect": "reject",
        # Records EVERY segment unconditionally. Correct on paths where every
        # non-first segment is a genuine descent; wrong exactly where a segment is
        # locally redundant and must be dropped. Here the redundancy is the
        # concrete-ancestor-link condition.
        "module": _map_rival("true"),
        "refinement": "a counterpart that records every segment retains a locally "
                      "redundant segment the desired decision drops, lengthening "
                      "the recorded path; the unchanged membership check then "
                      "wrongly disallows a lookup that depends on that segment "
                      "being dropped — failing the pre-existing tests that rely on "
                      "the drop. It would NOT resolve.",
        "rationale": "REJECT from `out = keepMask hops`: at a hop with "
                     "priorIsRelation true and concreteParentLink true the "
                     "post-image drops the segment (`false`) but the rival records "
                     "it (`true`). Refuted on the redundant sub-domain; the sole "
                     "witness with `concreteParentLink` true. (Sibling: always-"
                     "retain.)",
        "witness": _witness("[" + _hop(False, True, True, False, False, False, False) + "]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-identity-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `¬redundantLocalValue` conjunct. Agrees with gold except
        # exactly when a segment IS the record's own auto identity
        # (redundantLocalValue true) while the other guards would retain it: gold
        # drops, this rival keeps.
        "module": _map_rival(
            "h.isFirst || (h.priorIsRelation && !h.concreteParentLink "
            "&& (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))"),
        "refinement": "removing the identity conjunct re-admits retention of the "
                      "segment naming the record's own auto identity — the "
                      "locally-reachable value the desired decision excludes — "
                      "lengthening the recorded path and flipping the membership "
                      "verdict on the pre-existing lookups that rely on that "
                      "exclusion. It would NOT resolve.",
        "rationale": "REJECT from `out = keepMask hops`: at a hop with "
                     "priorIsRelation true, concreteParentLink false, and "
                     "redundantLocalValue true, gold drops (`false`) via the "
                     "identity conjunct while the rival records (`true`). Refuted "
                     "on the auto-identity sub-domain; the sole witness with "
                     "`redundantLocalValue` true. (Sibling: drop-auto-identity-"
                     "conjunct.)",
        "witness": _witness("[" + _hop(False, True, False, True, False, False, False) + "]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-covers-clause",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `(¬hasRedundantLocalValue ∨ ¬priorAlreadyCovers)` clause.
        # Agrees with gold except exactly when the record has an auto identity AND
        # the segment names a field the prior relation already references
        # (hasRedundantLocalValue ∧ priorAlreadyCovers), which gold treats as
        # redundant. Attacks the two facts the previous rivals leave unset.
        "module": _map_rival(
            "h.isFirst || (h.priorIsRelation && !h.concreteParentLink "
            "&& !h.redundantLocalValue)"),
        "refinement": "dropping this clause re-admits retention of a segment the "
                      "prior relation already references while the record carries "
                      "an auto identity — a value reachable locally, which the "
                      "desired decision drops. The recorded path lengthens and the "
                      "membership verdict flips on the pre-existing lookups that "
                      "rely on the drop. It would NOT resolve.",
        "rationale": "REJECT from `out = keepMask hops`: at a hop with "
                     "priorIsRelation true, both concreteParentLink and "
                     "redundantLocalValue false, but hasRedundantLocalValue and "
                     "priorAlreadyCovers BOTH true, gold drops (`false`) via the "
                     "final clause while the rival records (`true`). The sole "
                     "witness setting `hasRedundantLocalValue` / "
                     "`priorAlreadyCovers` true. (ADDED to attack the third "
                     "redundancy conjunct and vary its two facts.)",
        "witness": _witness("[" + _hop(False, True, False, False, True, True, False) + "]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-ignore-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `isFirst` disjunct entirely, deciding every segment by the
        # non-first rule. Wrong exactly on the first segment when the prior-step
        # branch would not fire (isFirst true, priorIsRelation false): gold
        # records it, the rival drops it.
        "module": _map_rival(
            "(h.priorIsRelation && !h.concreteParentLink && !h.redundantLocalValue "
            "&& (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))"),
        "refinement": "a counterpart that omits the first-segment rule drops the "
                      "root of the walked path whenever the non-first branch does "
                      "not fire, shortening the recorded path so the join no "
                      "longer matches; the pre-existing lookups that begin at that "
                      "segment become wrongly disallowed. It would NOT resolve.",
        "rationale": "REJECT from `out = keepMask hops`: at the first segment "
                     "(isFirst true, priorIsRelation false) the post-image records "
                     "it (`true`) but the rival, having dropped the first-segment "
                     "disjunct, evaluates the non-first branch to `false`. The "
                     "sole witness with `isFirst` true / `priorIsRelation` false. "
                     "(ADDED to attack the first-segment clause.)",
        "witness": _witness("[" + _hop(True, False, False, False, False, False, False) + "]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Decide every segment correctly but emit the flags in REVERSED order.
        # Every per-segment decision is right; only the traversal order is wrong —
        # a clause that exists here because the carrier is a LIST of segments (the
        # single-decision sibling has no order to attack). Refuted only on a list
        # of length >= 2 with distinct flags.
        "module": _swap(_BASE, _IMPL, "    return ((keepMask hops).reverse)"),
        "refinement": "a counterpart that decided each segment correctly but "
                      "associated the flags with the wrong segments (reversed "
                      "traversal) would record each position's flag from a "
                      "different hop, mis-shaping the recorded path; the tests "
                      "assert each segment's own decision at its own position. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = keepMask hops`: `keepMask` fixes the "
                     "per-index correspondence, and reversing it disagrees on any "
                     "list of length >= 2 with distinct flags. Refuted at a "
                     "two-element list — the sole reject varying `hops.length` "
                     "beyond one, closing the traversal-order clause the list "
                     "carrier introduces. (ADDED for the list carrier.)",
        "witness": _witness(
            "[" + _hop(True, False, False, False, False, False, False) + ", "
            + _hop(False, False, False, False, False, False, False) + "]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 1 frame-mutation rival, 4
# uniqueness/partial-domain rivals) plus an empty AXIOM_TESTS. The sibling
# contracts one function, `retained_segments`, over SIX read-only List[bool] fact
# vectors held at fractional permission; this bundle contracts one method,
# `keptSegments`, over a LIST of `Hop` (each carrying the seven per-segment facts
# as one immutable record) with a deep `keepMask` fold and no axioms. The two
# surfaces model the SAME per-segment keep/drop decision, so the value rivals
# port near-1:1 with two carrier consequences: the frame-mutation rival is
# vacuous here, and the list carrier ADDS a traversal-order clause.
#
#   sibling case                    kind          -> here                       disposition
#   ------------------------------------------------------------------------------------
#   pos-control-branch-reorder      soundness     -> pos-letbind                PORTED
#   (—)                             soundness     -> pos-closed-form            ADDED
#   admissibility-f2p-shape         admissibility -> admiss-grounded            RE-AIMED
#   frame-mut-write-input           uniqueness    -> (none)                     VACUOUS
#   prepatch-target-fields          uniqueness    -> weak-superseded-coarse-rule PORTED
#   always-retain                   uniqueness    -> weak-always-retain         PORTED
#   drop-auto-identity-conjunct     uniqueness    -> weak-drop-identity-conjunct PORTED
#   never-retain-nonfirst           uniqueness    -> weak-ignore-first          RE-EXPRESSED
#   (—)                             uniqueness    -> weak-drop-covers-clause     ADDED
#   (—)                             uniqueness    -> weak-reversed              ADDED
#
# PORTED (pos-control-branch-reorder -> pos-letbind): the sibling's correct
#   reshape (result-build branches swapped) becomes the closest loop-preserving
#   reshape here (bind the per-segment decision to a local), keeping the loop and
#   the front-recursive invariant so the frozen proof closes unchanged.
#   pos-closed-form is ADDED to defend the obligation from a maximally different
#   (loop-free) shape.
# RE-AIMED (admissibility-f2p-shape -> admiss-grounded): the sibling asserts the
#   equal-length precondition facts an in-domain input satisfies. There is no
#   `require` clause here (the pre-conditions region is empty), so that probe is
#   vacuous; the case is re-aimed at proving the post-image is satisfiable and
#   NON-degenerate at the F2P corner (a coarse-flagged genuine descent is
#   RECORDED; a redundant segment is DROPPED). The in-region assert is discharged
#   symbolically against concrete literals so the proof closes.
# VACUOUS (frame-mut-write-input): the sibling's mandatory frame-mutation rival
#   writes to a read-only fact vector held at Acc(...,1/2). This backend is
#   referentially transparent and `hops` is declared read-only (not `mut`), so
#   there is no read-only input to overwrite and no substitute probe. Omitted as
#   vacuous, NOT fabricated.
# PORTED (the value rivals): prepatch-target-fields -> weak-superseded-coarse-rule
#   (the superseded coarse decision, refuted where a coarse-flagged segment is a
#   genuine descent). always-retain -> weak-always-retain (refuted on a redundant
#   segment). drop-auto-identity-conjunct -> weak-drop-identity-conjunct (refuted
#   on the auto-identity sub-domain). never-retain-nonfirst RE-EXPRESSED as
#   weak-ignore-first: the sibling drops every non-first segment (a first-only
#   mask); here the equivalent structural mangling that also VARIES the isFirst
#   fact is to drop the first-segment disjunct, refuted at the first segment when
#   the non-first branch does not fire (the same "first-segment handling is
#   load-bearing" argument, re-aimed so isFirst is exercised at `true`).
# ADDED (weak-drop-covers-clause): the decision's third redundancy conjunct
#   (`¬hasRedundantLocalValue ∨ ¬priorAlreadyCovers`) is attacked by no sibling
#   case; dropping it is refuted exactly when both facts are true, and it is the
#   only rival that varies those two facts to `true`. Without it the battery
#   would pin `hasRedundantLocalValue` and `priorAlreadyCovers` at `false`
#   throughout — the documented "a binder every witness holds fixed" failure.
# ADDED (weak-reversed): the list carrier introduces a traversal-ORDER clause the
#   six-vector sibling has no analogue for. `keepMask` fixes the per-index
#   correspondence; a rival that decides each segment correctly but reverses the
#   order is refutable only on a length >= 2 list, and is the sole reject that
#   varies `hops.length` beyond one.
#
# WITNESS SUBJECT (the one substantive repair over the previous revision of this
#   battery, and the reason the cell was at MALFORMED-TESTS). All six rejects
#   declare `witness_reference = _LOOPFREE`. The earlier revision relied on the
#   frozen impl's `while` loop NOT reducing and read that as the discrimination;
#   measured here, the frozen side fails identically for the real claim and its
#   exact negation ("did not reduce to `isTrue` or `isFalse`"), so it decided
#   nothing and all six cases were correctly reported `witness-undecided`. The
#   reference is the same loop-free closed form as the `pos-closed-form` positive
#   (asserted identical at load: both are `_LOOPFREE`), so it shares the frozen
#   spec and verifies; against it every witness fails by `decide` PROVING the
#   negation, which is a real refutation. Because that source also ships as an
#   `expect="verify"` case, the battery records that loop-freeness is not what any
#   rival is rejected for.
#
# DIVERGENCE / NON-TERMINATION lane: NOTHING TO PORT, and CLOSED BY THE SEMANTICS
#   rather than a spec hole. The nagini sibling carries no `diverge-*` /
#   `nonterm-*` / `weak-diverge` case, so there is no such case to carry over.
#   Independently, this bundle is pinned to
#   `set_option loom.semantics.termination "total"` (with `decreasing i` on the
#   frozen loop), and that option cannot drift from the file's
#   `open TotalCorrectness DemonicChoice`, because the `set_option` elaborator itself
#   runs `openScope `TotalCorrectness` (Loom/MonadAlgebras/WP/Options.lean:169-186).
#   Under "total" a postcondition is claimed of ALL runs, not only terminating ones,
#   and the verifier demands a decreasing measure on every loop. Measured on this
#   bundle with the proof reduced to a bare `loom_solve`: an unmeasured spun loop is
#   refused at elaboration (`Decreasing annotations are required in total correctness
#   semantics`), and the sharper shape that CARRIES a measure which does not decrease
#   (`while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q`, body
#   `q := q`) is REJECTED on the measure's own goal -- `case «decreasing_1: q»`,
#   residual `q < q`. So a diverging rival does not satisfy this spec and there is no
#   hole to record. (An earlier version of this note reached the same disposition by
#   calling this "the 99-of-500 configuration" and citing an internal findings doc
#   for a cohort of 401 `partial` bundles. Both are withdrawn: all 500 velvet
#   bundles now set "total", so there is no such cohort.)
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `hops : List Hop`, whose elements carry seven boolean facts, and one
#   top-level clause, `out = keepMask hops`. The six reject witnesses probe
#   six DISTINCT input points (pts=6). Across them each fact takes both values:
#     isFirst                : true (weak-ignore-first, weak-reversed head), else false
#     priorIsRelation        : true (four rivals), false (weak-ignore-first, weak-reversed)
#     concreteParentLink     : true (weak-always-retain), else false
#     redundantLocalValue    : true (weak-drop-identity-conjunct), else false
#     hasRedundantLocalValue : true (weak-drop-covers-clause), else false
#     priorAlreadyCovers     : true (weak-drop-covers-clause), else false
#     targetOfPrior          : true (weak-superseded-coarse-rule), else false
#     hops.length            : 2 (weak-reversed), else 1
#   so no fact and no length is pinned across the battery. Every conjunct of the
#   decision (the first-segment disjunct, the prior-step guard, and each of the
#   three redundancy conditions) is attacked by some rival, plus the traversal
#   order the list carrier adds. Both directions of the decision (record a
#   genuine descent; drop a redundant segment) are defended by the positive
#   controls and the admissibility case.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the per-segment facts are read-only inputs, not consumed contracts), so
# there is nothing there to probe.
AXIOM_TESTS = []
