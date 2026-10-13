"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24177 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct collectVertices`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method over a single read-only input):

  collectVertices (segs : List (List Vertex)) return (out : List Vertex)
    ensures out = collectAll segs                                        (C1)

The operation assembles the point list that determines a shape's data extent
from a list of groups, each already given as its own point list. ``collectAll``
is a fully transparent recursive ``def`` (NOT an opaque oracle): the in-order
concatenation of the point lists of ALL the groups, with every group's points
retained. The single top-level ``ensures`` clause pins two facets at once —
(a) EVERY group contributes (no group's point list is dropped), and (b) every
one of a group's points is retained, in order. Both facets are grounded in the
sole input binder ``segs`` via ``collectAll segs``; there is no answer key to
echo (``collectAll`` is a concrete ``def``, and the ``axioms`` region is empty).
The method has NO ``require`` clause, so the admitted domain is total.

CARRIER NOTE — the point payload ``Vertex`` is ``opaque`` and carries NO
``DecidableEq`` (its coordinates are abstracted away; the model is
order-/membership-exact but coordinate-agnostic). Two consequences shape every
witness below:

  * ``derive_tester_for`` needs a decidable postcondition, and the postcondition
    is an equality on ``List Vertex``; with no ``DecidableEq Vertex`` the tester
    cannot be synthesised. So the sibling velvet ``…Tester args = false`` route
    is UNAVAILABLE, exactly as on the ``List Float`` carrier of the step-outline
    bundle.
  * Even so, one observable of ``List Vertex`` IS decidable without a ``Vertex``
    equality: its LENGTH. Each rival below drops a group or a group's points, so
    it returns a list of the WRONG LENGTH at its witness input. The witness
    ``extract_program_for``s the rival (extraction needs no decidability — it
    just names the executable ``collectVerticesExec``) and states, at a concrete
    input built from universally-quantified vertices, that the rival's RESULT
    differs from ``collectAll``:

        collectVerticesExec segs ≠ DivM.res (collectAll segs)

    proved by taking ``congrArg List.length`` of the assumed equality and closing
    the resulting false ``Nat`` equation with ``simp [collectAll]``. Every witness
    binds only fresh ``Vertex`` variables (a b c d) with NO hypotheses, so the
    consistency probe is trivially satisfiable (no opaque-term conditioning is
    needed — length is transparent).

WHICH IMPL THE REFUTATION IS CHECKED AGAINST — measured, not assumed. The frozen
impl is a ``while`` loop whose extracted ``…Exec`` does NOT reduce under this
script: the ``forIn Lean.Loop.mk`` term stays un-normalised, so ``DivM.res.inj h``
fails to unify and the build errors with ``Application type mismatch``. That is a
STUCK build, NOT a refutation, and it must not be read as one: a build asserting
the OPPOSITE claim (that the frozen impl is CORRECT at the same input — the
witness with its ``≠`` replaced by ``=``) fails against the frozen impl with the
same un-normalised-loop error. Gold's exit code therefore carries no information
about the claim, so the frozen impl cannot serve as the second subject here.

What DOES serve, and what the gate actually uses, is a VERIFYING loop-free impl of
this same spec — ``pos-direct-collectall`` above, whose ``…Exec`` reduces to
``pure (collectAll segs)``. Against that subject the exit codes track the claim,
which is the property a discriminator needs:

  * the witness (rival is WRONG here) FAILS there — ``simp`` reduces the length
    equation to ``True``, i.e. it PROVED the lengths agree for that impl and the
    refutation has nothing left to close;
  * the flipped claim (that impl is CORRECT here) SUCCEEDS there;
  * against each rival the same ``simp`` closes the goal outright, having derived
    ``False`` from a length equation that is genuinely false.

Independently controlled: each witness below also FAILS against a DIFFERENT
correct, reducible impl (``return segs.flatten``) that verifies this spec — so
the witnesses discriminate WRONGNESS, not merely the frozen impl's loop shape.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    holds ``verts`` at ``Acc(list_pred(verts), 1/2)`` and its MANDATORY frame
    rival overwrites that read-only input to trip INSUFFICIENT PERMISSION. Lean
    and Velvet are referentially transparent: ``segs`` is an immutable value,
    this bundle declares NO ``mut`` parameter, and there is no heap, no aliasing,
    and no permission system to trip. There is no read-only input to overwrite
    and no substitute probe to fabricate, so the class is vacuous (per the
    porting map, legitimately dropped, not faked).
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is a total function of the sole input
    ``segs`` (``collectAll`` is a concrete ``def``, not an axiomatized oracle);
    there is no opaque answer key a wrong impl could echo. The cheapest correct
    impl returns ``collectAll segs`` directly, which the positive controls cover
    honestly.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: a rival
    right on part of the domain but dropping a group (leading / interior /
    all-but-first) or dropping points within each group, diverging wherever the
    dropped material is non-empty.

WITNESS PLACEMENT. The four reject witnesses sit at FOUR DISTINCT ``segs`` points
— ``[[a],[b]]``, ``[[a,b],[c]]``, ``[[a],[b],[c]]``, ``[[a,b],[c,d]]`` — so the
sole binder ``segs`` moves across the battery over group counts (2 / 2 / 3 / 2)
and group shapes (singletons vs multi-point groups), and no clause is
demonstrated at a single pinned point (pts=4). Facet (a) "every group
contributes" is attacked by the drop-leading, keep-first-only and drop-interior
rivals; facet (b) "every point of a group is retained" is attacked by the
take-first-point rival.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the assembly is
modeled directly over the carrier; ``collectAll`` is a pure ``def``). There is
nothing here for this gate to probe, and the gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24177"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean.
# The ENTIRE frozen backward-fold loop body (used for whole-body reject rivals
# and the straight-line positive controls).
_GOLD_IMPL = """    -- impl-start
    let mut result : List Vertex := []
    let mut i := segs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ segs.length
      invariant result = collectAll (segs.drop i)
      done_with i = 0
      decreasing i
    do
      let s := segs[i - 1]!
      result := s ++ result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# The loop guard alone (unique inside the impl region) — for the guard-reshape
# positive control that keeps the whole loop scaffold + framing invariants.
_GOLD_GUARD = "    while i > 0\n"
assert _BASE.count(_GOLD_GUARD) == 1, "loop-guard anchor drifted"

# The first line of the impl body — for prepending the admissibility assert.
_GOLD_IMPL_HEAD = "    -- impl-start\n    let mut result : List Vertex := []"
assert _BASE.count(_GOLD_IMPL_HEAD) == 1, "impl-head anchor drifted"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward-fold loop (it discharges the loop-body goal via the drop-step
# ---- lemma). A positive control that reshapes the impl away from that loop must
# ---- retune the tactic body; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct collectVertices` obligation survives with an identical
# ---- statement. Unique in the file.
_GOLD_PROOF = """prove_correct collectVertices by
  loom_solve
  rw [collectAll_drop_step segs i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a goal that closes
# without the loop-body drop-step lemma; retune to the bare tactic.
_PROOF_STRAIGHT = "prove_correct collectVertices by\n  loom_solve"


def _reject(impl_body):
    """Full Solution.lean variant with ONLY the impl region body replaced by a
    straight-line rival (frozen tactic script kept — expected NOT to verify)."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + impl_body + "\n    -- impl-end")


# ---- witness preamble. Reaches the rival's extracted program (extraction needs
# ---- no DecidableEq — it just names `collectVerticesExec`) and states, at a
# ---- concrete input built from fresh opaque vertices, that the rival's result
# ---- differs from the transparent model `collectAll`. Discriminated by the
# ---- result's LENGTH (the one observable of `List Vertex` decidable without a
# ---- `Vertex` equality): `congrArg List.length` reduces the assumed equality to
# ---- a false `Nat` equation `simp [collectAll]` closes. Checked in a file whose
# ---- `prove_correct` block is stripped; no `axiom`/`sorry`/`native_decide`.
def _witness(binders, inp):
    return (
        "extract_program_for collectVertices\n\n"
        f"example {binders} :\n"
        f"    collectVerticesExec {inp}\n"
        f"      ≠ DivM.res (collectAll {inp}) := by\n"
        "  unfold collectVerticesExec collectVertices\n"
        "  intro h\n"
        "  have h3 := congrArg List.length (DivM.res.inj h)\n"
        "  simp [collectAll] at h3\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-collectall",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the explicit backward-fold loop and return the modeled
        # assembly directly. This is the honest cheapest-correct impl (collectAll
        # IS the in-order concatenation); the loop only existed to establish
        # `result = collectAll (segs.drop 0)`. Retunes the tactic body to bare
        # `loom_solve` (the loop-body drop-step lemma is no longer needed); the
        # obligation statement is untouched.
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    -- impl-start\n    return collectAll segs\n    -- impl-end"),
            _GOLD_PROOF, _PROOF_STRAIGHT),
        "rationale": "a straight-line assembly (`return collectAll segs`) is the "
                     "simplest correct impl; it meets C1 (`out = collectAll segs`) "
                     "by definition. If it fails to verify the postcondition is "
                     "over-fit to the loop form => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-guard-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the ENTIRE backward-fold scaffold and both framing
        # invariants VERBATIM, but rewrite the loop guard `i > 0` as the
        # logically-equivalent `¬ (i = 0)`. Same behaviour, different executable
        # shape; the frozen loop invariant (result = collectAll (segs.drop i)) is
        # discharged exactly as before, so the frozen proof is kept unchanged.
        "module": _swap(_BASE, _GOLD_GUARD, "    while ¬ (i = 0)\n"),
        "rationale": "the loop guard `i > 0` rewritten as the equivalent "
                     "`¬ (i = 0)`; the entire backward-fold scaffold, both framing "
                     "invariants, and the front-recursive drop-step proof are kept "
                     "verbatim. Must verify, else the spec is over-fit to the `>` "
                     "spelling of the guard => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini "a self-call on an F2P-shaped input satisfies the precondition"
    # probe has no precondition to establish. The analogue on a TOTAL carrier is
    # that the obligation must be SATISFIABLE at exactly an F2P-shaped input: if
    # `out = collectAll segs` were unsatisfiable there (a contradictory or
    # over-constrained post-image), the whole spec would be vacuous and every
    # rival would "reject" for a reason that has nothing to do with the spec.
    # So this case discharges, as an in-region `assert` BY EVALUATION and before
    # the frozen obligation closes verbatim, the obligation's OWN equation at
    # concrete F2P-shaped points over fresh opaque vertices: a multi-group
    # multi-point outline (`[[a,b],[c],[d]]` -> `[a,b,c,d]`), an outline with
    # EMPTY groups interleaved (`[[],[a],[]]` -> `[a]` — the empty-group edge the
    # rivals' "correct only when the omitted material is empty" sub-domain turns
    # on), and the empty outline (`[] -> []`). This pins the post-image
    # element-wise, not merely its length: a length-only assert would be
    # discharged by any impl that got the count right, and the earlier form of
    # this case asserted exactly that. The frozen loop and obligation are kept
    # verbatim so C1 still discharges. Liveness is measured, not assumed: with
    # one clause's right-hand side made false (`= [a, b, c]`) the module leaves
    # an unsolved `adm_1` goal and fails to verify.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL_HEAD,
            "    -- impl-start\n"
            "    assert (with_name_prefix `adm\n"
            "      (∀ a b c d : Vertex,\n"
            "        collectAll ([[a, b], [c], [d]] : List (List Vertex))"
            " = [a, b, c, d] ∧\n"
            "        collectAll ([[], [a], []] : List (List Vertex)) = [a] ∧\n"
            "        collectAll ([] : List (List Vertex)) = []))\n"
            "    let mut result : List Vertex := []"),
        "rationale": "the obligation `out = collectAll segs` is SATISFIABLE at "
                     "F2P-shaped inputs, and its post-image is pinned "
                     "element-wise rather than being degenerate or "
                     "over-constrained: at a multi-group multi-point outline the "
                     "assembly is exactly the in-order concatenation "
                     "(`[[a,b],[c],[d]]` -> `[a,b,c,d]`), interleaved EMPTY "
                     "groups contribute nothing (`[[],[a],[]]` -> `[a]`, the edge "
                     "each rival's correct sub-domain turns on), and the empty "
                     "outline assembles the empty list. Discharged by evaluation "
                     "as an in-region assert before the frozen obligation closes "
                     "verbatim, so C1 still discharges too. If this assert could "
                     "NOT discharge, the modeled domain would exclude a "
                     "legitimate input => PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line impl carrying a machine-checked
    # refutation witness at a DISTINCT concrete `segs` (discriminated by the
    # assembled LENGTH) and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test `test_small_autoscale`.
    # =====================================================================
    {
        "id": "weak-drop-leading-group",
        "kind": "uniqueness",
        "expect": "reject",
        # THE regressed shape: assemble over every group EXCEPT the leading one
        # (the traversal that stops one group short, so the first group's points
        # never reach the extent). Correct only when the leading group is empty;
        # diverges wherever it carries a point.
        "module": _reject("    return collectAll (segs.drop 1)"),
        "refinement": "this is the pre-change behavior: a traversal that omits the "
                      "leading group so its points never reach the extent. When "
                      "the leading group carries the coordinate extreme, the "
                      "autoscaled limit undershoots it and the failing test's "
                      "`>=`/`<=` bound assertions still fail — exactly the reported "
                      "regression. It would NOT resolve.",
        "rationale": "REJECT from C1 (`out = collectAll segs`): dropping the "
                     "leading group omits its points, so the assembled list is "
                     "shorter than `collectAll segs` whenever that group is "
                     "non-empty. Refuted at `segs = [[a],[b]]`, where the impl "
                     "assembles a length-1 list but the post-image demands "
                     "length-2 — the empty-leading edge no other rival isolates.",
        "witness": _witness("(a b : Vertex)", "[[a], [b]]"),
    },
    {
        "id": "weak-first-group-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep ONLY the first group's points and drop every later group (the
        # "seed and don't fold" shape). Correct only when there is at most one
        # group (or the tail groups are all empty); wrong otherwise.
        "module": _reject("    return segs.headD []"),
        "refinement": "a counterpart that seeds the extent from the first group's "
                      "points and never folds the remaining groups omits every "
                      "later group. On the regression outline the coordinate "
                      "extreme sits on an interior group, so the autoscaled limit "
                      "undershoots it and the failing test's bound assertion still "
                      "fails. It would NOT resolve.",
        "rationale": "REJECT from C1: keeping only the first group's points "
                     "assembles a strictly shorter list than `collectAll segs` "
                     "whenever a later group is non-empty. Refuted at "
                     "`segs = [[a,b],[c]]`, where the impl assembles length-2 "
                     "(`[a,b]`) but the post-image demands length-3.",
        "witness": _witness("(a b c : Vertex)", "[[a, b], [c]]"),
    },
    {
        "id": "weak-drop-interior-group",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the first and the trailing groups but SKIP an interior group (the
        # every-other / masked-update shape). Correct only when the skipped
        # interior group is empty; wrong when it carries a point.
        "module": _reject(
            "    return segs.headD [] ++ collectAll (segs.drop 2)"),
        "refinement": "a counterpart that folds the extent over only some of the "
                      "groups (skipping an interior one) drops the skipped group's "
                      "points. On a shape whose coordinate extreme falls on a "
                      "skipped interior group the autoscaled limit undershoots it "
                      "and the failing test's bound assertion still fails. It would "
                      "NOT resolve.",
        "rationale": "REJECT from C1: skipping the interior group at index 1 omits "
                     "its points, so the assembled list is shorter than "
                     "`collectAll segs` whenever that group is non-empty. Refuted "
                     "at `segs = [[a],[b],[c]]`, where the impl assembles length-2 "
                     "(`[a,c]`) but the post-image demands length-3 — an interior "
                     "drop distinct from the boundary drops of the other rivals.",
        "witness": _witness("(a b c : Vertex)", "[[a], [b], [c]]"),
    },
    {
        "id": "weak-take-first-point",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep EVERY group but retain only its FIRST point (the appearance-
        # preserving condensation that keeps one representative per group). Every
        # group contributes, so facet (a) holds, but facet (b) — every one of a
        # group's points — is violated for any multi-point group.
        "module": _reject(
            "    return collectAll (segs.map (fun s => s.take 1))"),
        "refinement": "a counterpart that keeps every group but retains only one "
                      "representative point per group condenses away the interior "
                      "points of a multi-point group. When a dropped interior "
                      "point carries the coordinate extreme, the autoscaled limit "
                      "undershoots it and the failing test's bound assertion still "
                      "fails — the appearance-preserving condensation the change "
                      "replaces. It would NOT resolve.",
        "rationale": "REJECT from C1: retaining only each group's first point "
                     "assembles a strictly shorter list than `collectAll segs` "
                     "whenever any group has more than one point. Refuted at "
                     "`segs = [[a,b],[c,d]]`, where the impl assembles length-2 "
                     "(`[a,c]`) but the post-image demands length-4 — the "
                     "within-group point-retention facet no group-drop rival "
                     "attacks.",
        "witness": _witness("(a b c d : Vertex)", "[[a, b], [c, d]]"),
    },
    {
        "id": "weak-reverse-group-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Retain EVERY group and EVERY point, but assemble the groups in REVERSE
        # traversal order. This attacks the third facet of C1 — IN-ORDER — which
        # the four rivals above cannot reach: each of them drops material, so each
        # is caught by a LENGTH mismatch, and length is invariant under
        # permutation. Correct only when the group order is immaterial (at most
        # one non-empty group); wrong whenever two groups carry points.
        "module": _reject("    return collectAll segs.reverse"),
        "refinement": "a counterpart that walks the groups in the opposite order "
                      "assembles the same points in a permuted sequence. The "
                      "collected list is consumed positionally downstream (it is "
                      "stacked into the point matrix the extent is taken from, "
                      "mapping.md §2), so a permuted assembly misplaces the points "
                      "relative to the outline they came from; the autoscaled "
                      "bound is then taken over a sequence that is not the "
                      "outline's, and the failing test's bound assertions still "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from C1 (`out = collectAll segs`): C1 fixes the "
                     "in-order concatenation, so reversing the group order "
                     "violates it even though every point is retained and the "
                     "length is unchanged. Refuted at `segs = [[a],[b]]` with "
                     "`a ≠ b`, where the impl assembles `[b,a]` but the "
                     "post-image demands `[a,b]` — the ORDER facet that no "
                     "length-based rival can attack, since all four above are "
                     "caught by a length mismatch and length is permutation-"
                     "invariant.",
        # Length is EQUAL here, so the length projection above is blind. The
        # refutation instead projects the HEAD (`List.headD`, decidable-free) and
        # closes with the distinctness hypothesis: `Vertex` is opaque and carries
        # no `DecidableEq`, so two distinct points must be given by hypothesis
        # rather than computed. The consistency probe passes — `a ≠ b` over an
        # opaque type is satisfiable and no tactic can derive `False` from it.
        # Measured: elaborates against this rival (the head projection reduces to
        # `b = a`, closed by `hab`), and FAILS against the verifying loop-free
        # positive (there `simp` reduces the same projection to `True`).
        "witness": (
            "extract_program_for collectVertices\n\n"
            "example (a b : Vertex) (hab : a ≠ b) :\n"
            "    collectVerticesExec [[a], [b]]\n"
            "      ≠ DivM.res (collectAll [[a], [b]]) := by\n"
            "  unfold collectVerticesExec collectVertices\n"
            "  intro h\n"
            "  have h3 := congrArg (fun l => l.headD a) (DivM.res.inj h)\n"
            "  simp [collectAll] at h3\n"
            "  exact hab h3.symm\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 3 uniqueness
# rivals) plus 2 AXIOM_TESTS. The sibling contracts `enclosing_upper_bound(verts:
# List[int]) -> int`, abstracting ONE axis of the per-segment vertex gather to a
# List[int] and returning the per-axis maximum (P_dom dominance + P_att attained).
# This bundle models the assembly ITSELF — the in-order concatenation of ALL the
# groups' point lists (`out = collectAll segs`) — over `List (List Vertex)`; the
# per-axis min/max is downstream of the collected list and is not modeled here.
# So the sibling's max-oriented rivals (return first / last element, mask the max
# on a parity sub-domain) re-aim onto the concatenation's two facets: every group
# contributes, and every point of a group is retained. Every sibling case is
# accounted for below.
#
#   sibling case (nagini)          -> here
#   ---------------------------------------------------------------------
#   pos-direct-seqmax               -> pos-direct-collectall           RE-SHAPED
#   pos-branch-reorder              -> pos-guard-reshape                RE-SHAPED
#   admiss-selfcall                 -> admiss-nondegenerate             RE-AIMED
#   rival-frame-mutate-verts (MAND) -> (none)                          VACUOUS
#   rival-return-first              -> weak-first-group-only            RE-AIMED
#   rival-return-last-seed          -> weak-drop-leading-group          RE-AIMED
#   rival-value-mask-odd            -> weak-drop-interior-group         RE-AIMED
#   (no sibling counterpart)        -> weak-take-first-point            ADDED
#   (no sibling counterpart)        -> weak-reverse-group-order         ADDED
#
# 6 ported/re-aimed, 1 vacuous, 2 added.
#
# RE-SHAPED (positives): the sibling's `pos-direct-seqmax` drops the loop and
#   returns `seq_max(ToSeq(verts))` directly; here the structural analog is to
#   drop the loop and return `collectAll segs` directly (retuning the tactic body,
#   elided from the spec view). The sibling's `pos-branch-reorder` rewrites the
#   loop comparison `>` as `not (<=)`; the analog here reshapes the loop GUARD
#   `i > 0` as `¬ (i = 0)`, keeping the frozen scaffold, invariants and proof.
# RE-AIMED (admissibility): the sibling establishes that a self-call on an
#   F2P-shaped input satisfies the read-only half-permission precondition. This
#   method has NO `require` clause, so there is no precondition to establish. The
#   analogue on a TOTAL carrier is that the obligation must be SATISFIABLE at
#   exactly an F2P-shaped input — an unsatisfiable or over-constrained post-image
#   there would make the whole spec vacuous and every rejection meaningless. So
#   the case discharges the obligation's OWN equation, by evaluation, as an
#   in-region assert before the frozen obligation closes verbatim: at a
#   multi-group multi-point outline (`[[a,b],[c],[d]]` -> `[a,b,c,d]`), at an
#   outline with interleaved EMPTY groups (`[[],[a],[]]` -> `[a]`, the edge each
#   rival's correct sub-domain turns on), and at the empty outline. This pins the
#   post-image ELEMENT-WISE; a length-only assert (the earlier form of this case)
#   is weaker, since any impl with the right count discharges it.
# RE-AIMED (rivals): the sibling models the per-axis MAXIMUM; its dominance rivals
#   (return first / last element; mask the max on odd indices) attack the max.
#   This bundle models the concatenation upstream of the max, so the rivals re-aim
#   onto WHICH groups/points reach the collected list: return-first -> keep only
#   the first group; return-last-seed (the seed-and-don't-fold / condensation that
#   drops the leading material — the G-DIFF prepatch) -> drop the leading group;
#   value-mask-odd (fold over only some positions) -> drop an interior group. Each
#   is a genuine partial-domain rival: correct when the omitted material is empty,
#   wrong when it carries a point (the coordinate extreme, on the F2P outline).
# VACUOUS (rival-frame-mutate-verts, MANDATORY on nagini): the sibling overwrites
#   the read-only input `verts[0]`, held at Acc(list_pred(verts), 1/2), to trip
#   INSUFFICIENT PERMISSION before any postcondition is considered. This backend
#   is referentially transparent: `segs` is an immutable value, this bundle
#   declares NO `mut` parameter, there is no heap, no aliasing, and no permission
#   system. Measured rather than asserted: an impl that assigns to the input
#   (`segs := segs.drop 1`) is refused by the FRONT END, not by the spec —
#   "`segs` cannot be mutated, only variables declared using `let mut` can be
#   mutated" — so such a variant tests the language's binding rules and attributes
#   nothing to the postcondition, which is what makes the class vacuous here (per
#   the porting map, legitimately dropped, not fabricated). Its ARGUMENT (a patch
#   mutating the gathered vertex array would
#   corrupt the shape geometry) has no value footprint the spec can force here —
#   the assembly is read-only by construction (`out = collectAll segs`, a fresh
#   list).
# ADDED (weak-take-first-point): the single `ensures` clause pins TWO facets —
#   every group contributes AND every point of a group is retained. The three
#   re-aimed rivals all attack the first facet (dropping whole groups); without a
#   fourth rival the within-group point-retention facet would go unattacked (a
#   rival that kept every group but condensed each to one point — the appearance-
#   preserving condensation the change fixes — would verify). This rival closes
#   that gap and carries a machine-checked witness at `segs = [[a,b],[c,d]]`.
# ADDED (weak-reverse-group-order): C1 fixes the IN-ORDER concatenation, and that
#   is a third facet the four rivals above cannot reach. Each of them DROPS
#   material, so each is refuted by a LENGTH mismatch — and length is invariant
#   under permutation, so an impl that retains every point but assembles the
#   groups in the wrong ORDER is refuted by no witness in the battery. This rival
#   is that impl (`collectAll segs.reverse`), and its witness projects the HEAD
#   instead of the length. Measured: the rival module does not verify (the
#   obligation is left as `collectAll segs.reverse = collectAll segs`).
#
# BINDER / CLAUSE COVERAGE. The sole input binder is `segs`; the single top-level
#   clause C1 (`out = collectAll segs`) folds three facets: every group
#   contributes, every point of a group is retained, and the assembly is IN ORDER.
#   C1 is DEFENDED by the two positive controls and the admissibility case and
#   ATTACKED by all five rivals: facet (a) by weak-drop-leading-group,
#   weak-first-group-only, weak-drop-interior-group; facet (b) by
#   weak-take-first-point; facet (c) by weak-reverse-group-order. `segs` is varied
#   across the witness inputs [[a],[b]] (2 singleton groups), [[a,b],[c]] (a
#   two-point + a singleton), [[a],[b],[c]] (3 singleton groups), [[a,b],[c,d]]
#   (2 two-point groups) — moving group count over {2,3} and group shape over
#   singleton/multi-point, so no rival is refuted at a pinned input and all three
#   facets are demonstrated.
#
# WITNESS FORM. The tester route is unavailable (no `DecidableEq Vertex`, so
#   `derive_tester_for` cannot synthesise a decidable postcondition). So each
#   rival is a STRAIGHT-LINE impl whose `…Exec` reduces, and each witness asserts
#   the rival's extracted output differs from the transparent model `collectAll`
#   at its concrete point. The four material-dropping rivals are discriminated via
#   the assembled LENGTH; weak-reverse-group-order retains every point, so length
#   is blind there and its witness projects the HEAD (`List.headD`) under an
#   `a ≠ b` hypothesis — `Vertex` is opaque, so distinctness is given rather than
#   computed, and the consistency probe passes because no tactic can derive
#   `False` from `a ≠ b` on an opaque type.
#
#   The second subject is NOT the frozen solution. Measured: the frozen `while`
#   loop's `…Exec` never normalises, so every witness build against it dies on
#   `Application type mismatch` at `DivM.res.inj` — and so does a build asserting
#   the OPPOSITE claim, which means the frozen impl's exit code carries no
#   information about the claim and cannot attest to anything. The attestation
#   subject is instead a VERIFYING loop-free impl of this same spec
#   (`pos-direct-collectall`), against which the exit codes do track the claim:
#   each witness FAILS there (`simp` reduces its projection to `True`, having
#   PROVED the equation for that impl) while the flipped claim SUCCEEDS there.
#   Controlled once more against a DIFFERENT correct reducible impl
#   (`return segs.flatten`, which verifies this spec): every witness fails there
#   too, so the witnesses discriminate WRONGNESS and not the frozen loop's shape.
#   Each rival module does NOT verify, in every case leaving the ensures goal
#   itself unsolved (a semantic failure, not a tactic mismatch).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the `axioms` region is empty — the assembly is
#   modeled directly by the pure `def collectAll`, not via an axiomatized callee),
#   so there is nothing here for this gate to probe.
AXIOM_TESTS = []
