"""properties.py — G-PBT falsification battery for django__django-11734 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region is changed — the consumer spec view elides those regions
and the ``prove_correct`` tactic bodies are kept verbatim, so ``markers.same_spec``
holds and every ``prove_correct`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. Two contracted methods over a three-valued tagged carrier
``Target`` = {``outerRef``, ``localRef``, ``directValue``} — a reference to the
enclosing query, a reference to a field of the query under construction, or a
plain directly-supplied value. There is NO opaque answer key to echo: each
``ensures`` grounds the result in the method's own inputs through the transparent
pure functions ``normalizesAsValue`` / ``isExpression`` and
``resolveInSubquery`` / ``rebind`` (directive 8).

  comparisonNormalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target)
      return (out : Bool)
    ensures out = normalizesAsValue lhsSpansMultipleColumns t
          = (!lhsSpansMultipleColumns) && (!isExpression t)

    Fully pins all six (Bool × Target) points. The load-bearing clause is the
    ``!isExpression t`` factor: a reference to the enclosing query is NOT a
    direct value even for a single-column relation, so it must be left untouched
    (result ``false``) rather than coerced. The ``!lhsSpansMultipleColumns``
    factor is a second independent clause: a multi-column relation is never
    normalized regardless of the target kind.

  subqueryTargetResolution (t : Target) return (out : Resolution)
    ensures out = resolveInSubquery (rebind t)

    Fully pins all three tags: ``outerRef`` -> ``staysOuter`` (still bound to the
    enclosing query, the usable case), ``localRef`` -> ``resolvesLocally``,
    ``directValue`` -> ``plainValue``. The load-bearing clause is the
    ``outerRef`` arm: an enclosing-query reference must be rebound so it KEEPS
    denoting the enclosing query across the extra nesting layer the rebuilt
    subquery adds; the previous behaviour rebound it the same way as a plain
    field reference and it resolved at this level instead, making the subquery
    unusable (the ValueError the issue reports).

BINDER STRUCTURE (read before judging binder coverage).

  * ``comparisonNormalizesAsValue`` has TWO input binders,
    ``lhsSpansMultipleColumns`` and ``t``. Both are load-bearing and are varied
    by the reject witnesses: ``lhsSpansMultipleColumns`` takes BOTH ``false``
    (the single-column arm, where the target-kind classification decides the
    result) and ``true`` (the multi-column arm, where the result must be
    ``false`` for every target); ``t`` takes all three tags. Note the two
    factors interact: when ``lhsSpansMultipleColumns = true`` the result is
    ``false`` for every ``t``, so a rival wrong ONLY in the target
    classification cannot be refuted there — that sub-domain is attacked by a
    rival that mishandles the multi-column guard instead (``ignore-multicol-guard``).
    Note also that five of the six points pin the result ``false``; the single
    point pinning ``true`` is ``(false, directValue)``, and it is attacked on its
    own by ``never-normalize`` (an audit addition). Without that case every
    method-1 rival happens to AGREE with the frozen impl there, so nothing would
    force the clause's positive arm and an impl that normalizes NOTHING would
    satisfy every other witness in the battery.
  * ``subqueryTargetResolution`` has ONE input binder, ``t``, varied across all
    three tags by the three method-2 reject witnesses.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME-MUTATION — VACUOUS. The nagini sibling documents this class N/A too:
    both modeled functions take their argument BY VALUE, there is no
    reference/heap input to overwrite. Lean/Velvet are additionally referentially
    transparent — every input here is an immutable value, no ``mut`` binder, no
    aliasing — so there is no read-only field to mutate and no substitute probe
    to build. Not fabricated.
  * DIVERGENCE / NON-TERMINATION - nothing to ship here, but NOT because the
    class is inexpressible and NOT because the spec admits it. An earlier
    revision of this bullet said this bundle runs under
    ``loom.semantics.termination "partial"``, so a non-terminating impl satisfies
    every ``ensures`` vacuously and VERIFIES, and cited that as an escalated spec
    hole. Both halves are false and are retracted. Line 4 of the frozen
    ``Solution.lean`` reads ``"total"``, and the file's only correctness ``open``
    is ``open TotalCorrectness DemonicChoice``; the two cannot disagree, because
    the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Under ``total`` a
    postcondition is claimed of ALL runs, not only terminating ones, and the
    verifier demands a decreasing measure on every loop. Measured on this bundle,
    proofs reduced to a bare ``loom_solve``: a spun loop with no ``decreasing``
    clause is refused at elaboration (``Decreasing annotations are required in
    total correctness semantics``), and the sharper shape that CARRIES a
    non-decreasing measure (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q`` with body ``q := q``) is REJECTED on the measure's own goal,
    ``case «decreasing_1: q»`` with residual ``⊢ q < q``. So the class is closed
    by the semantics, not open in the spec, and there is no hole to escalate. The
    nagini sibling carries no ``diverge-*`` / ``nonterm-*`` case either. What
    still blocks a reject CASE is the witness contract: a witness must ELABORATE
    against its rival, and a rejected diverging rival's module does not compile at
    all (the obligation fails at the ``method``, ahead of any appended tester), so
    the gate would return ``witness-unproven`` -> INCONCLUSIVE rather than a
    rejection.
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are grounded in the method
    inputs via transparent pure functions; the ``axioms`` region declares no
    ``axiom`` (the one A-reference callee ``resolveInSubquery`` is a concrete
    ``def``, validated ``== the real callee`` by G-AX, not an oracle whose
    contract the proof assumes). There is no answer key to echo.
  * PARTIAL-DOMAIN — the principal attack, as in nagini. Each reject rival is
    correct on most of the {outerRef, localRef, directValue} × {single, multi}
    domain but diverges on one point, and carries the refinement argument that
    its faithful real patch would NOT resolve the F2P
    (``test_subquery_exclude_outerref``) / would regress a P2P.

The two carriers differ in shape but carry the SAME argument. Nagini modeled the
site-2 change as an integer HOP COUNT (value->0, local->1, outer->1); velvet
models it as the RESOLUTION OUTCOME of the rebound target
(``resolveInSubquery (rebind t)``). "an OuterRef gets zero extra hops"
(nagini ``weak-outer-zero-hops``, the gold-fix discriminator) re-expresses as
"an outer reference is rebound like a plain field reference and resolves
locally" (``outer-resolves-locally`` here) — the exact pre-patch behaviour
modeled by ``Solution_prepatch_2.lean``.
"""
from pathlib import Path

INSTANCE = "django__django-11734"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies WHOLLY inside one ``-- impl-start`` /
# ---- ``-- impl-end`` region and is unique in Solution.lean (both facts asserted
# ---- at load by _swap). Anchoring on the code lines (not the leading comment)
# ---- keeps the surgery inside the elided impl region so the spec view and the
# ---- prove_correct scripts are untouched. ----
_M1_IMPL = """    let targetIsExpression : Bool :=
      match t with
      | .directValue => false
      | _            => true
    -- The direct-value normalization runs only for a single-column relation and
    -- only when the target is a plain value (not an expression).
    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))"""

_M2_IMPL = """    let b : Rebound :=
      match t with
      | .outerRef    => .outerKeepingDepth
      | .localRef    => .outerByName
      | .directValue => .unchanged
    -- Consult the rebound target from inside the subquery (the unchanged step).
    let r : Resolution :=
      match b with
      | .outerKeepingDepth => .staysOuter
      | .outerByName       => .resolvesLocally
      | .unchanged         => .plainValue
    pure r"""


def _m1(new_impl: str) -> str:
    return _swap(_BASE, _M1_IMPL, new_impl)


def _m2(new_impl: str) -> str:
    return _swap(_BASE, _M2_IMPL, new_impl)


# ---- prove_correct tactic bodies. The consumer spec view elides both the impl
# ---- regions AND the `prove_correct` tactic bodies (markers.spec_view), so a
# ---- variant may retune the tactic body while keeping the byte-identical
# ---- `prove_correct <name>` header (the surviving obligation). The two
# ---- structurally-reshaped positive controls need one extra `cases t` split
# ---- for the frozen `simp_all` to close the reshaped body; every reject rival
# ---- keeps the frozen tactic bodies verbatim (its rejection is judged by its
# ---- witness, not by whether the frozen script happens to break). ----
_M1_PROOF = ("prove_correct comparisonNormalizesAsValue by\n"
             "  loom_solve <;> simp_all [normalizesAsValue, isExpression]")
_M2_PROOF = ("prove_correct subqueryTargetResolution by\n"
             "  loom_solve <;> simp_all [resolveInSubquery, rebind]")
_M1_PROOF_CASES = ("prove_correct comparisonNormalizesAsValue by\n"
                   "  loom_solve <;> (cases t <;> "
                   "simp_all [normalizesAsValue, isExpression])")
_M2_PROOF_CASES = ("prove_correct subqueryTargetResolution by\n"
                   "  loom_solve <;> (cases t <;> "
                   "simp_all [resolveInSubquery, rebind])")


def _m1_pos(new_impl: str) -> str:
    """method-1 impl swap + `cases t` proof retune (reshaped positive)."""
    return _swap(_m1(new_impl), _M1_PROOF, _M1_PROOF_CASES)


def _m2_pos(new_impl: str) -> str:
    """method-2 impl swap + `cases t` proof retune (reshaped positive)."""
    return _swap(_m2(new_impl), _M2_PROOF, _M2_PROOF_CASES)


# ---- admissibility. The proof body needs one extra alternative to clear the
# ---- in-region `assert` goal (`decide` on a closed Resolution equation); the
# ---- `prove_correct <name>` header stays byte-identical, so the frozen
# ---- obligation survives and is still discharged by the frozen `simp_all` arm.
_M2_PROOF_ASSERT = ("prove_correct subqueryTargetResolution by\n"
                    "  loom_solve\n"
                    "  all_goals first\n"
                    "    | decide\n"
                    "    | simp_all [resolveInSubquery, rebind]")


def _m2_admiss(assert_block: str) -> str:
    """frozen method-2 impl PREFIXED by `assert_block` + assert-clearing proof."""
    return _swap(_swap(_BASE, _M2_IMPL, assert_block + _M2_IMPL),
                 _M2_PROOF, _M2_PROOF_ASSERT)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the postcondition through Velvet's own tester
# ---- machinery: `<name>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` blocks have been stripped, so no tactic script
# ---- can mask the verdict. There are no `require` clauses, so every input
# ---- reaches the postcondition (nothing is vacuously excluded). `Target` has
# ---- DecidableEq and is finite, so `decide` settles every point. ----
def _w1(args: str) -> str:
    return (
        "extract_program_for comparisonNormalizesAsValue\n"
        "prove_precondition_decidable_for comparisonNormalizesAsValue\n"
        "prove_postcondition_decidable_for comparisonNormalizesAsValue\n"
        "derive_tester_for comparisonNormalizesAsValue\n\n"
        f"example : comparisonNormalizesAsValueTester {args} = false := by\n"
        "  decide\n"
    )


def _w2(args: str) -> str:
    return (
        "extract_program_for subqueryTargetResolution\n"
        "prove_precondition_decidable_for subqueryTargetResolution\n"
        "prove_postcondition_decidable_for subqueryTargetResolution\n"
        "derive_tester_for subqueryTargetResolution\n\n"
        f"example : subqueryTargetResolutionTester {args} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness; must verify, else SPEC-TOO-STRONG).
    # =====================================================================
    # A structurally-different but CORRECT method-1 impl: a single explicit
    # case split over the three target kinds directly yields the classification
    # result, instead of computing an `isExpression` intermediate and ANDing.
    # Same truth table (directValue -> !lhsSpans, localRef/outerRef -> false).
    # A faithful reshape MUST verify.
    #
    # The tactic body IS retuned (`_m1_pos` adds one `cases t` split); the
    # `prove_correct <name>` HEADER — the surviving obligation — is byte-
    # identical, and the tactic body is elided from the consumer spec view, so
    # the frozen statement is unchanged. Measured (audit wave, real build): this
    # same impl under the frozen `simp_all`-only script FAILS (exit 1, three
    # `unsolved goals` — one per Target constructor), which is exactly why the
    # split is needed. That is a tactic-shape gap, not a spec gap: the spec
    # ACCEPTS this impl (exit 0 with the split), so it is not SPEC-TOO-STRONG.
    {
        "id": "pos-normalize-explicit",
        "kind": "soundness",
        "expect": "verify",
        "module": _m1_pos(
            "    -- structurally different but correct: an explicit case split\n"
            "    -- over the three target kinds directly yields the result.\n"
            "    let result : Bool :=\n"
            "      match t with\n"
            "      | .directValue => !lhsSpansMultipleColumns\n"
            "      | .localRef    => false\n"
            "      | .outerRef    => false\n"
            "    pure result"),
        "rationale": "structurally-different CORRECT method-1 impl (explicit "
                     "three-way case split producing the Bool directly, rather "
                     "than the frozen `isExpression`-intermediate-then-AND shape). "
                     "Same truth table on all six (Bool × Target) points, so "
                     "`out = normalizesAsValue lhsSpansMultipleColumns t` holds; a "
                     "faithful impl MUST verify (else SPEC-TOO-STRONG).",
    },
    # A structurally-different but CORRECT method-2 impl: the rebind step and the
    # (unchanged) in-subquery resolution are COLLAPSED into one direct case split
    # over `t`, rather than the frozen two-step `let b := rebind t; let r :=
    # resolveInSubquery b`. Same outcome on all three tags.
    {
        "id": "pos-rebind-collapse",
        "kind": "soundness",
        "expect": "verify",
        "module": _m2_pos(
            "    -- structurally different but correct: the rebind and the\n"
            "    -- (unchanged) in-subquery resolution are collapsed into one\n"
            "    -- direct case split over the target kind.\n"
            "    let r : Resolution :=\n"
            "      match t with\n"
            "      | .outerRef    => .staysOuter\n"
            "      | .localRef    => .resolvesLocally\n"
            "      | .directValue => .plainValue\n"
            "    pure r"),
        "rationale": "structurally-different CORRECT method-2 impl (the two-step "
                     "rebind-then-resolve is collapsed into a single case split "
                     "over `t`). Same outcome on all three tags, so "
                     "`out = resolveInSubquery (rebind t)` holds; a faithful impl "
                     "MUST verify (else SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY. Neither method declares a `require` clause, so the
    # sibling's "the precondition admits a normal input" probe has no
    # precondition to probe. The analogue on a total carrier is the residual
    # risk that the OBLIGATION is unsatisfiable or DEGENERATE at exactly the
    # F2P-shaped input — a post-image nothing can meet reads like one
    # everything meets, and a post-image that is CONSTANT across the tags
    # would pin nothing while every case still behaved as declared.
    #
    # This case discharges that at the concrete F2P-shaped point (an
    # enclosing-query reference target) with an in-region `assert`, by
    # evaluation, BEFORE closing the frozen obligation verbatim: the
    # post-image at `outerRef` (a) is satisfiable and equals the usable
    # outcome `staysOuter`, and (b) DIFFERS from the post-image at
    # `localRef` — so the obligation genuinely separates the F2P-shaped
    # input from the tag the previous behaviour conflated it with, rather
    # than being trivially satisfiable everywhere.
    #
    # The assert is LIVE, not decoration: measured (real build) the same
    # case with the claim replaced by the FALSE
    # `resolveInSubquery (rebind Target.outerRef) = Resolution.resolvesLocally`
    # fails at exit 1 with an unsolved `admiss_1 ... |- False` goal. The impl
    # is the frozen one verbatim so the method's own `ensures` still
    # discharges; only the tactic BODY gains an assert-clearing alternative
    # (elided from the spec view; the obligation header is byte-identical).
    # =====================================================================
    {
        "id": "admiss-outer-target-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _m2_admiss(
            "    assert (with_name_prefix `admiss\n"
            "      (resolveInSubquery (rebind Target.outerRef) = Resolution.staysOuter ∧\n"
            "       resolveInSubquery (rebind Target.outerRef)\n"
            "         ≠ resolveInSubquery (rebind Target.localRef)))\n"),
        "rationale": "the obligation `out = resolveInSubquery (rebind t)` is "
                     "SATISFIABLE and NON-DEGENERATE at the F2P-shaped input: at "
                     "`t = outerRef` the post-image evaluates to the usable "
                     "outcome `staysOuter`, and it DIFFERS from the post-image at "
                     "`t = localRef` — the tag the previous behaviour conflated it "
                     "with. So there is a value an impl can return there (not "
                     "PRECOND-TOO-STRONG / not an unsatisfiable obligation) and the "
                     "post-image actually discriminates that point rather than "
                     "being constant across the carrier. The in-region assert must "
                     "discharge by evaluation and the frozen impl's own `ensures` "
                     "must still discharge alongside it.",
    },

    # =====================================================================
    # UNIQUENESS / PARTIAL-DOMAIN rivals (must be REJECTED). Each carries a
    # machine-checked witness that ELABORATES against the rival and FAILS
    # against the frozen solution.
    # =====================================================================

    # ---- method 2 (subqueryTargetResolution) ----------------------------
    # (1) THE GOLD-FIX DISCRIMINATOR (== Solution_prepatch_2.lean): an
    # enclosing-query reference is rebound the SAME way as a plain field
    # reference (by name) instead of being re-wrapped to survive the nesting, so
    # it resolves at this level (`resolvesLocally`) instead of staying bound to
    # the outer query (`staysOuter`). Correct on localRef and directValue.
    {
        "id": "outer-resolves-locally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m2(
            "    -- rival: an enclosing-query reference is rebound the SAME way as\n"
            "    -- a plain field reference (by name) instead of being re-wrapped\n"
            "    -- to survive the extra nesting layer.\n"
            "    let b : Rebound :=\n"
            "      match t with\n"
            "      | .outerRef    => .outerByName\n"
            "      | .localRef    => .outerByName\n"
            "      | .directValue => .unchanged\n"
            "    let r : Resolution :=\n"
            "      match b with\n"
            "      | .outerKeepingDepth => .staysOuter\n"
            "      | .outerByName       => .resolvesLocally\n"
            "      | .unchanged         => .plainValue\n"
            "    pure r"),
        "refinement": "Faithful real patch: drop the new branch that re-wraps an "
                      "enclosing-query reference before it is carried into the "
                      "freshly generated inner subquery, so it is rebound like a "
                      "plain field reference. It then resolves ONE level too far "
                      "in — onto the inner subquery rather than the outer query — "
                      "so the enclosing reference points at the wrong table and "
                      "the F2P test_subquery_exclude_outerref returns the wrong "
                      "rows / raises. This is exactly the pre-patch behaviour "
                      "(Solution_prepatch_2.lean); it would NOT resolve.",
        "rationale": "REJECT from the `outerRef` arm of "
                     "`out = resolveInSubquery (rebind t)`: the spec pins "
                     "`outerRef -> staysOuter`; this rival yields `resolvesLocally`. "
                     "Refuted at `t = outerRef`; correct on the other two tags.",
        "witness": _w2("Target.outerRef"),
    },
    # (2) PARTIAL-DOMAIN: a field reference of the query under construction is
    # wrongly re-wrapped as if it were an enclosing-query reference, so it stays
    # bound to the outer query (`staysOuter`) instead of resolving at this level
    # (`resolvesLocally`). Correct on outerRef and directValue.
    {
        "id": "local-stays-outer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m2(
            "    -- rival: a field reference of the query under construction is\n"
            "    -- wrongly re-wrapped as if it were an enclosing-query reference.\n"
            "    let b : Rebound :=\n"
            "      match t with\n"
            "      | .outerRef    => .outerKeepingDepth\n"
            "      | .localRef    => .outerKeepingDepth\n"
            "      | .directValue => .unchanged\n"
            "    let r : Resolution :=\n"
            "      match b with\n"
            "      | .outerKeepingDepth => .staysOuter\n"
            "      | .outerByName       => .resolvesLocally\n"
            "      | .unchanged         => .plainValue\n"
            "    pure r"),
        "refinement": "Faithful real patch: rebind a local field reference as if "
                      "it were an enclosing-query reference (re-wrap to keep depth) "
                      "rather than to an outer reference by name. A local field "
                      "reference would then STAY bound to the outer query instead "
                      "of resolving at the query under construction's level, so an "
                      "exclude/~Q with a local field rhs over an N-to-many relation "
                      "matches the wrong rows — regressing the pre-existing local "
                      "field-reference rebind path (a P2P regression). Not the gold "
                      "patch; it would NOT resolve.",
        "rationale": "REJECT from the `localRef` arm: the spec pins "
                     "`localRef -> resolvesLocally`; this rival yields `staysOuter`. "
                     "Refuted at `t = localRef`; correct on the other two tags.",
        "witness": _w2("Target.localRef"),
    },
    # (3) PARTIAL-DOMAIN: a plain value is spuriously rebound as an outer
    # reference by name instead of being carried through unchanged, so it
    # resolves as a query reference at this level (`resolvesLocally`) rather than
    # staying a plain value (`plainValue`). Correct on outerRef and localRef.
    {
        "id": "value-resolves-locally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m2(
            "    -- rival: a plain value is spuriously rebound as an outer\n"
            "    -- reference by name instead of being carried through unchanged.\n"
            "    let b : Rebound :=\n"
            "      match t with\n"
            "      | .outerRef    => .outerKeepingDepth\n"
            "      | .localRef    => .outerByName\n"
            "      | .directValue => .outerByName\n"
            "    let r : Resolution :=\n"
            "      match b with\n"
            "      | .outerKeepingDepth => .staysOuter\n"
            "      | .outerByName       => .resolvesLocally\n"
            "      | .unchanged         => .plainValue\n"
            "    pure r"),
        "refinement": "Faithful real patch: wrap a plain concrete value as an outer "
                      "reference when carrying it into the inner subquery. A literal "
                      "carries no query reference; turning it into a (broken) outer "
                      "reference makes an exclude(field=<value>) over an N-to-many "
                      "relation resolve a non-existent reference and crash / return "
                      "wrong rows. The gold patch leaves a plain value untouched (no "
                      "rewrite branch fires); this regresses the common literal-rhs "
                      "exclude path (P2P). It would NOT resolve.",
        "rationale": "REJECT from the `directValue` arm: the spec pins "
                     "`directValue -> plainValue`; this rival yields `resolvesLocally`. "
                     "Refuted at `t = directValue`; correct on the other two tags.",
        "witness": _w2("Target.directValue"),
    },

    # ---- method 1 (comparisonNormalizesAsValue) -------------------------
    # (4) THE NORMALISE-GUARD DISCRIMINATOR (== Solution_prepatch.lean intent):
    # treat EVERY target as a direct value to normalize whenever the relation is
    # single-column — the target-kind classification is dropped entirely.
    # Correct on directValue; wrong on the two query-expression kinds.
    {
        "id": "normalize-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m1(
            "    -- rival: drop the target-kind classification and treat EVERY\n"
            "    -- target as a direct value to normalize for a single-column\n"
            "    -- relation (the pre-patch \"normalise everything\" guard).\n"
            "    pure (!lhsSpansMultipleColumns)"),
        "refinement": "Faithful real patch: keep the pre-patch guard that treats the "
                      "target as a direct value whenever it is not directly "
                      "SQL-renderable — true for an enclosing-query reference and a "
                      "local field reference too, since neither is renderable. It "
                      "then coerces a query expression that has no concrete value, "
                      "mangling the enclosing reference before it can be resolved "
                      "against the right query level — the OuterRef-in-exclude path "
                      "(the F2P motivation) breaks. This is the unfixed behaviour; "
                      "it would NOT resolve.",
        "rationale": "REJECT from the `!isExpression t` factor of "
                     "`out = (!lhsSpansMultipleColumns) && (!isExpression t)`: for a "
                     "query-expression target the spec pins the result `false` (in "
                     "the single-column arm), but the rival returns "
                     "`!lhsSpansMultipleColumns = true`. Refuted at "
                     "`(false, outerRef)`.",
        "witness": _w1("false Target.outerRef"),
    },
    # (5) PARTIAL-DOMAIN: an enclosing-query reference is correctly left
    # untouched, but a local field reference is wrongly taken as a direct value.
    # Correct on outerRef and directValue; wrong on localRef.
    {
        "id": "normalize-local-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m1(
            "    -- rival: an enclosing-query reference is correctly excluded from\n"
            "    -- normalization, but a local field reference is wrongly taken as\n"
            "    -- a direct value (only the enclosing kind is treated as an expr).\n"
            "    let targetIsExpression : Bool :=\n"
            "      match t with\n"
            "      | .outerRef => true\n"
            "      | _         => false\n"
            "    pure ((!lhsSpansMultipleColumns) && (!targetIsExpression))"),
        "refinement": "Faithful real patch: guard normalization on \"is an "
                      "enclosing-query reference\" instead of \"is a query "
                      "expression\" — passing an enclosing reference through but "
                      "still normalizing a local field reference. A local field "
                      "reference is a query expression with no concrete value; "
                      "coercing it corrupts the field reference for related-field "
                      "lookups (a P2P regression). The gold predicate excludes BOTH "
                      "query-expression kinds from normalization; it would NOT resolve.",
        "rationale": "REJECT from the `!isExpression t` factor: for a local field "
                     "reference `isExpression = true`, so the spec pins the result "
                     "`false` (single-column arm); this rival treats only the "
                     "enclosing kind as an expression and returns "
                     "`!lhsSpansMultipleColumns = true` for a local reference. "
                     "Refuted at `(false, localRef)` — a near-miss the "
                     "`normalize-all` rival (wrong on outerRef too) does not "
                     "subsume at this point.",
        "witness": _w1("false Target.localRef"),
    },
    # (6) PARTIAL-DOMAIN on the OTHER binder: the target-kind classification is
    # correct, but the single-column guard is dropped, so a plain value is
    # normalized even for a MULTI-column relation. Correct whenever the relation
    # is single-column; wrong on the multi-column arm for a plain value.
    {
        "id": "ignore-multicol-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m1(
            "    -- rival: the target-kind classification is correct, but the\n"
            "    -- single-column guard is dropped, so a plain value is normalized\n"
            "    -- even for a multi-column relation.\n"
            "    let targetIsExpression : Bool :=\n"
            "      match t with\n"
            "      | .directValue => false\n"
            "      | _            => true\n"
            "    pure (!targetIsExpression)"),
        "refinement": "Faithful real patch: drop the single-column guard from the "
                      "normalization condition, so a plain value is normalized into "
                      "the related field's value domain even for a relation that "
                      "spans multiple columns. A multi-column relation cannot be "
                      "reduced to a single normalized value; coercing it corrupts "
                      "multi-column related lookups (a P2P regression on the "
                      "multi-column path). The gold predicate keeps both factors; it "
                      "would NOT resolve.",
        "rationale": "REJECT from the `!lhsSpansMultipleColumns` factor of "
                     "`out = (!lhsSpansMultipleColumns) && (!isExpression t)`: for a "
                     "multi-column relation the spec pins the result `false` for "
                     "every target, but the rival ignores that factor and returns "
                     "`!isExpression t = true` for a plain value. Refuted at "
                     "`(true, directValue)` — the ONLY reject witness that exercises "
                     "the `lhsSpansMultipleColumns = true` sub-domain.",
        "witness": _w1("true Target.directValue"),
    },
    # (7) PARTIAL-DOMAIN at the one point the other five rivals all AGREE with
    # the frozen impl: `(false, directValue)`, the SOLE input of the six where
    # the spec pins the result `true`. Enumerated over the whole finite domain,
    # rivals (4)/(5)/(6) are each correct there, so nothing above forces the
    # positive arm of `normalizesAsValue` — an impl that simply never normalizes
    # would slip past all of them. This rival is that impl: it refuses to treat
    # ANY target as a direct value, which is correct on five of the six points
    # and wrong only at the point that matters for the clause's `true` side.
    {
        "id": "never-normalize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m1(
            "    -- rival: never treat the target as a direct value to normalize,\n"
            "    -- for any target kind and any relation arity — the positive arm\n"
            "    -- of the classification is dropped entirely.\n"
            "    pure false"),
        "refinement": "Faithful real patch: over-tighten the new guard so the "
                      "direct-value normalization never fires — e.g. add the "
                      "query-expression exclusion but leave the branch that "
                      "actually performs the value coercion unreachable. A plain "
                      "directly-supplied value on a single-column relation would "
                      "then never be normalized into the related field's value "
                      "domain, so an ordinary related-field lookup against a model "
                      "instance or a literal no longer coerces to the related "
                      "column's value and compares against the wrong thing. That "
                      "regresses the common literal/instance-rhs related-lookup "
                      "path (a broad P2P regression) while doing nothing for the "
                      "enclosing-reference case; it would NOT resolve.",
        "rationale": "REJECT from the POSITIVE side of "
                     "`out = (!lhsSpansMultipleColumns) && (!isExpression t)`: at "
                     "`(false, directValue)` both factors are `true`, so the spec "
                     "pins the result `true`; this rival returns `false`. Refuted "
                     "at `(false, directValue)` — the ONLY point of the six where "
                     "the spec demands `true`, and the only one at which every "
                     "other method-1 rival AGREES with the frozen impl. Without "
                     "this case no rival forces the clause's true arm, so an impl "
                     "that normalizes nothing would satisfy every other witness.",
        "witness": _w1("false Target.directValue"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals) plus a 2-case AXIOM
# lane, and documents FRAME-MUTATION as N/A. This bundle models the SAME two
# functions the nagini sibling models (site 1 = comparisonNormalizesAsValue,
# site 2 = subqueryTargetResolution), so the port is close to 1:1 on the
# uniqueness rivals; the carrier reshape is nagini's integer HOP COUNT ->
# velvet's RESOLUTION OUTCOME.
#
#   sibling case                 -> here                      disposition
#   ---------------------------------------------------------------------
#   pos-rebind-reorder           -> pos-rebind-collapse        RE-EXPRESSED
#   pos-normalize-explicit       -> pos-normalize-explicit     PORTED
#   admiss-rebind-outer          -> admiss-outer-target-       RE-EXPRESSED
#                                    nondegenerate
#   weak-outer-zero-hops         -> outer-resolves-locally     PORTED (discriminator)
#   weak-local-zero-hops         -> local-stays-outer          PORTED
#   weak-value-one-hop           -> value-resolves-locally     PORTED
#   weak-normalize-all           -> normalize-all              PORTED (discriminator)
#   weak-normalize-local-true    -> normalize-local-true       PORTED
#   (new, for lhsSpans coverage) -> ignore-multicol-guard      ADDED
#   (new, for the `true` arm)    -> never-normalize            ADDED (audit)
#   AXIOM_TESTS (2)              -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (pos-rebind-collapse): the nagini positive reorders branches and
#   writes the hop count as the level-arithmetic difference. Velvet has no hop
#   count; the equivalent structural reshape is to collapse the two-step
#   rebind-then-resolve into a single case split over `t`, yielding the same
#   Resolution on every tag. It builds under the RETUNED tactic body (`_m2_pos`,
#   one extra `cases t`; the `prove_correct` header and hence the obligation are
#   byte-identical). Measured under the frozen `simp_all`-only body it FAILS
#   (exit 1, `unsolved goals`) — a tactic-shape gap, not a spec gap: the spec
#   accepts the reshaped impl, so it is not SPEC-TOO-STRONG.
# RE-EXPRESSED (admissibility): the nagini admissibility case adds a leading
#   Assert that the tagged domain is the expected concrete set and the F2P-shaped
#   input is in-domain, verifying iff the precondition admits it. This bundle
#   declares NO `require` clause on either method (the pre-conditions region is
#   empty), so there is no PRECONDITION to demonstrate non-vacuous.
#
#   That is not a reason to drop the lane, and an earlier revision of this file
#   wrongly claimed any assertion here would be trivially `x = x`. The analogue
#   on a total carrier is the OBLIGATION being unsatisfiable or degenerate at an
#   F2P-shaped input, and that is assertable and non-trivial: see
#   admiss-outer-target-nondegenerate, which discharges by evaluation that the
#   post-image at `outerRef` exists and DIFFERS from the post-image at `localRef`
#   before closing the frozen obligation verbatim. Measured live: the same case
#   with a FALSE claim about that same point fails (exit 1, unsolved
#   `admiss_1 ... |- False`), so the assert carries information.
# FRAME-MUTATION: VACUOUS here, and the nagini sibling ALSO documents it N/A
#   (both functions take their argument by value; no reference/heap input). Lean/
#   Velvet add referential transparency on top. Not fabricated.
# DIVERGENCE: the nagini sibling carries no divergence case; on this backend the
#   class is inexpressible (total defs) anyway. No hole to record.
# AXIOM_TESTS: dropped. The axiom lane (validating `resolveInSubquery == the real
#   resolve_expression` and the classification against real OuterRef/F objects)
#   is G-AX's job; this gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. subqueryTargetResolution's single binder `t` is
# refuted at all three tags (outerRef / localRef / directValue), each arm of the
# `resolveInSubquery (rebind t)` clause attacked. comparisonNormalizesAsValue's
# two binders are both varied: `t` across all three tags, and
# `lhsSpansMultipleColumns` across BOTH `false` (normalize-all, normalize-local-true)
# and `true` (ignore-multicol-guard) — so each of the two independent factors
# `!lhsSpansMultipleColumns` and `!isExpression t` is attacked by a rival that is
# wrong ONLY in that factor. Every reject witness probes a DISTINCT input point:
# method 2 at {outerRef, localRef, directValue}; method 1 at {(false,outerRef),
# (false,localRef), (true,directValue)}.
AXIOM_TESTS = []
