# properties.py — PBT falsification battery for sympy__sympy-17630 (lean bundle).
#
# PORT of the nagini sibling's battery to the Lean carrier. NOT a Lean source
# file: a manifest the lean PBT runner parses. Each SPEC_TESTS entry is a full
# Solution.lean variant that shares the FROZEN spec byte-for-byte (region
# surgery: only text strictly inside the impl region, and for the soundness
# positive the proof body, is swapped) and is checked by lean verify +
# variant_scope.same_spec. AXIOM_TESTS is dropped (the axiom lane is G-AX's job).
#
# Carrier narrowing (why this port is thinner than nagini's eight rivals):
# the Lean bundle models ONLY the purely-functional core the fix touches — the
# canonicalization of a sum of matrix-valued terms into a matrix-valued result.
# The nagini surface additionally contracted the product/scalar-coefficient
# dispatch (its E3 clause and the has_explicit_matrix input); NONE of that is
# modeled here. So every nagini case attached to the product branch
# (uniq-product-no-absorb, uniq-product-phantom-scalar) or to the scalar-argument
# bit of a sum (uniq-sum-with-scalar-contaminates) has no counterpart on this
# carrier — the abstraction collapses those distinctions into a single question:
# is the canonical sum a shapeless scalar or a matrix, and if a matrix, which
# named terms survive and in what order. See 'assessment' for the full port map.
#
# Defended surface (Solution.lean `canonicalizeMatrixSum` / the modeled
# `matrixSum`):
#   matrixSum(terms : List MatSumTerm) -> MatSum
#   Precondition (correct_matrixSum binder): terms non-empty; no scalarZero term;
#     surviving names distinct.
#   Ensures (single clause):
#     result = MatSum.matrix ((survivingNames terms).mergeSort nameLe)
#   which bundles three INDEPENDENT facets a rival can attack separately:
#     (F1) the result is a matrix, NEVER the shapeless scalar — the discriminating
#          fix clause (an all-identity sum stays a shaped identity matrix, not a
#          scalar zero that has no shape and breaks the downstream consumer);
#     (F2) the carried name list is exactly the surviving named terms (none
#          dropped, none invented) — the count/membership facet;
#     (F3) that name list is in canonical (codepoint) order — the ordering facet.
#
# The frame/permission-mutation class is VACUOUS here: Lean is referentially
# transparent, there is no read-only aliased input to overwrite.
#
# The divergence / non-termination class (nagini's uniq-nonterm-vacuous) is
# VACUOUS on this carrier, and the second audit measured it rather than citing
# the velvet finding (this bundle sets no `loom.semantics.termination` at all, so
# that document's partial/total split does not apply here). Measured with real
# builds: the only way to write a diverging impl in this region is `partial def`,
# which makes `implementation_matrixSum` OPAQUE to the kernel — Lean compiles it
# to an unfolding-free constant backed by `Inhabited`. The frozen obligation then
# cannot be closed at all: `unfold` fails ("failed to unfold
# `implementation_matrixSum`"), and `rfl`/`decide`/`simp_all` leave
# `implementation_matrixSum terms = MatSum.matrix (...)` unsolved. So a diverging
# rival is REJECTED, not vacuously accepted — there is no spec hole to report and
# no shippable reject case either, because the rejection comes from opacity
# rather than from the spec, and a witness cannot attribute it: the computing
# witness fails against such a rival (exit 1), while a hypothesis-stated witness
# is REFUTED BY GOLD TOO (exit 0 on the frozen solution — `witness-vacuous`),
# since the hypothesis `implementation_matrixSum [...] = MatSum.scalar` is
# satisfiable-looking to the probe but contradicts the frozen impl's own value.
#
# AUDIT NOTE (post-port). An independent audit rebuilt all five reject witnesses
# against the frozen solution AND against the flipped claim. Three of the five
# turned out HOLLOW as shipped: gold's build failed for a carrier reason (a stuck
# `Decidable` instance on `List.mergeSort`, or an unreduced `Id.run`/`pure`) that
# produced the byte-identical error for the claim and for its exact negation, so
# the gate's exit code carried no information about the claim. Every witness is
# now stated on a tactic that fully REDUCES the spec/impl chain to a literal
# `MatSum` comparison before deciding, and the flipped claim now ELABORATES
# against gold (exit 0) where the witness FAILS (exit 1). The audit also added
# the missing `admissibility` lane and an F2 rival attacking the invented-name
# direction. See `_witness` for the mechanics.
#
# SECOND AUDIT (independent). Re-derived all of the above from scratch: every
# `theorem correct_matrixSum` statement and both frozen regions are byte-identical
# to Solution.lean across all cases, and all six shipped reject witnesses were
# rebuilt on both sides plus the forgery flip. Every one inverts cleanly — witness
# /rival exit 0, witness/gold exit 1 with `Tactic decide proved that ¬True is
# false`, flipped claim gold exit 0 and rival exit 1 on a CONCRETE literal
# disequality (e.g. `MatSum.scalar = MatSum.matrix []`) — so no shipped case is
# hollow. The admissibility case was forgery-tested too: replacing its ground
# `have` with the FALSE claim `= MatSum.scalar` fails ("unsolved goals ⊢
# MatSum.matrix [] = MatSum.scalar") while the true `= MatSum.matrix []`
# elaborates, so that lane is discharged by evaluation and not vacuously.
# Attack D wrote five NEW wrong impls (reverse-sorted, duplicated names,
# truncated names, identity-as-name, and the scalar-subdomain probe below);
# four were rejected with genuine `¬True` gold signatures and the fifth is the
# vacuity check described under the precondition note. Attack E reshaped the impl
# three more ways (dedup-under-Nodup, foldr-built survivors, match-dispatch); all
# three VERIFY, so the spec is not too strong. No spec hole was found in either
# direction. The one real gap it did find is closed here as
# `uniq-keep-identity-as-name`: the identity-ELIMINATION facet was untested,
# because every shipped rival routes through `survivingNames` and therefore
# agrees with the frozen impl about it.
#
# Why the `Nodup` precondition is not separately attacked: a rival that goes
# wrong ONLY when a `scalarZero` term is present (return `MatSum.scalar` if any
# term is one, else the frozen body) was built and it VERIFIES — correctly, since
# the binder excludes exactly those inputs. That is the demonstrated reason the
# nagini scalar-sub-domain cases have no counterpart here, not an untested
# assumption; see 'omissions' in the audit payload.
from pathlib import Path

INSTANCE = "sympy__sympy-17630"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- frozen regions (anchors lie entirely inside the editable regions) --------

_IMPL_GOLD = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  -- The terms are all matrix-valued (no scalar coefficient terms), so the sum is\n"
    "  -- built directly from them, with no scalar identity seeded ahead of them.\n"
    "  return canonicalizeMatrixSum terms\n"
)

_PROOF_GOLD = (
    "theorem correct_matrixSum :\n"
    "    ∀ (terms : List MatSumTerm),\n"
    "      terms ≠ [] →\n"
    "      (∀ t ∈ terms, t ≠ MatSumTerm.scalarZero) →\n"
    "      (survivingNames terms).Nodup →\n"
    "      problem_spec_matrixSum terms (implementation_matrixSum terms) := by\n"
    "  intro terms hne hns _\n"
    "  unfold problem_spec_matrixSum implementation_matrixSum canonicalizeMatrixSum\n"
    "  simp only [Id.run]\n"
    "  cases hs : survivingNames terms with\n"
    "  | nil =>\n"
    "    simp only [List.mergeSort_nil]\n"
    "    cases ht : terms with\n"
    "    | nil => exact absurd ht hne\n"
    "    | cons a as =>\n"
    "      have ha : a ≠ MatSumTerm.scalarZero := hns a (by rw [ht]; exact List.mem_cons_self ..)\n"
    "      cases a\n"
    "      · exact absurd rfl ha\n"
    "      · rfl\n"
    "      · rfl\n"
    "  | cons n ns =>\n"
    "    rfl\n"
)


def _variant_impl(new_impl):
    """Swap only the impl body; keep the frozen proof (a reject case's frozen
    tactic script no longer closes the reshaped impl — the module fails to
    verify, and the witness attributes that failure to the spec)."""
    return _swap(_BASE, _IMPL_GOLD, new_impl)


def _variant_impl_proof(new_impl, new_proof):
    """Swap impl AND proof body (statement byte-identical) for a soundness
    positive whose reshaped impl needs its own closing proof."""
    return _swap(_variant_impl(new_impl), _PROOF_GOLD, new_proof)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness). Structurally-different but behaviourally
# identical: compute the surviving names up front and wrap the sorted list
# directly, skipping the `canonicalizeMatrixSum` case split entirely. Because
# the modeled precondition forbids a scalarZero term, the two shapes agree on
# every admissible input, so the obligation still closes — here with a two-line
# proof (the case split the frozen proof performs is unnecessary for this
# shape). MUST verify, else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_IMPL = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  -- Compute the surviving named terms once and wrap the canonically-ordered\n"
    "  -- list directly; equivalent on every admissible (scalar-seed-free) input.\n"
    "  let names := survivingNames terms\n"
    "  return MatSum.matrix (names.mergeSort nameLe)\n"
)
_POS_PROOF = (
    "theorem correct_matrixSum :\n"
    "    ∀ (terms : List MatSumTerm),\n"
    "      terms ≠ [] →\n"
    "      (∀ t ∈ terms, t ≠ MatSumTerm.scalarZero) →\n"
    "      (survivingNames terms).Nodup →\n"
    "      problem_spec_matrixSum terms (implementation_matrixSum terms) := by\n"
    "  intro terms _ _ _\n"
    "  unfold problem_spec_matrixSum implementation_matrixSum\n"
    "  simp only [Id.run, pure]\n"
)

# ---------------------------------------------------------------------------
# F1 rival — the FAITHFUL pre-patch bug (mirrors nagini uniq-prepatch-sum-inject
# -identity). A scalar identity is seeded ahead of the matrix terms, so when
# every surviving term is an identity the canonical result degenerates to the
# shapeless scalar instead of the shaped identity matrix. This is exactly the
# behavior whose faithful patch leaves an all-zero block as a scalar Zero (no
# shape), so block_collapse(b*b*b) raises on the missing shape and both F2P
# tests stay unresolved. Attacks facet F1. MUST reject.
# ---------------------------------------------------------------------------
_REJ_SEED_SCALAR = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  return canonicalizeMatrixSum (MatSumTerm.scalarZero :: terms)\n"
)

# ---------------------------------------------------------------------------
# F1 rival, blunt (mirrors nagini uniq-sum-always-scalar-supporting). Always
# returns the shapeless scalar. Supporting near-miss on facet F1, refuted at a
# NON-degenerate input (a single named term) where the correct result plainly
# carries a name. MUST reject.
# ---------------------------------------------------------------------------
_REJ_ALWAYS_SCALAR = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  return MatSum.scalar\n"
)

# ---------------------------------------------------------------------------
# F2 rival — drops every surviving name (always the empty identity-matrix
# result). The constructor facet F1 is satisfied (it IS a matrix), so an F1-only
# check would miss it; it violates the count/membership facet F2. MUST reject.
# ---------------------------------------------------------------------------
_REJ_DROP_ALL = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  return MatSum.matrix []\n"
)

# ---------------------------------------------------------------------------
# F2 rival, subtle — keeps canonical ORDER but drops the first name. Correct on
# F1 and F3; a fuzzer flipping the scalar/matrix constructor or checking sortedness
# would never catch it. Violates F2 (a matrix term is silently dropped, so the
# rebuilt sum spans the wrong number of blocks). MUST reject.
# ---------------------------------------------------------------------------
_REJ_DROP_ONE = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  return MatSum.matrix (((survivingNames terms).mergeSort nameLe).drop 1)\n"
)

# ---------------------------------------------------------------------------
# F3 rival — keeps the surviving names in INPUT order instead of canonical
# order. Correct on F1 and F2 (right constructor, right multiset of names);
# violates F3 only. Refuted at an input whose surviving names are not already
# sorted. MUST reject.
# ---------------------------------------------------------------------------
_REJ_UNSORTED = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  return MatSum.matrix (survivingNames terms)\n"
)

# ---------------------------------------------------------------------------
# F2 rival, the OPPOSITE direction (added by the audit). Every existing F2 rival
# DROPS names; none INVENTS one, so nothing in the shipped battery pinned the
# "no term is added" half of the membership facet. This one keeps every surviving
# name, in canonical order, and appends a term that was never in the input.
# Correct on F1 (a matrix) and F3 (sorted); violates F2 upward. MUST reject.
# ---------------------------------------------------------------------------
_REJ_INVENT_NAME = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  return MatSum.matrix (((survivingNames terms) ++ [\"ZZ\"]).mergeSort nameLe)\n"
)

# The invented-name rival needs `List.cons_append`/`List.nil_append` in the
# reduction set before `mergeSort` can be rewritten, and the sorted pair is
# ["A","ZZ"] rather than ["A","B"], so it carries its own witness rather than
# reusing `_witness`. Same principle: reduce to a literal `MatSum`, then decide.
_W_INVENT = (
    "example : ¬ problem_spec_matrixSum [MatSumTerm.named \"A\"]\n"
    "    (implementation_matrixSum [MatSumTerm.named \"A\"]) := by\n"
    "  have h1 : ([\"A\"] : List String).mergeSort nameLe = [\"A\"] := by simp\n"
    "  have hAZ : ([\"A\",\"ZZ\"] : List String).mergeSort nameLe = [\"A\",\"ZZ\"] := by\n"
    "    have h : nameLe \"A\" \"ZZ\" = true := by\n"
    "      simp only [nameLe, decide_eq_true_eq, String.le_iff_toList_le]; decide\n"
    "    simp [List.mergeSort, h]\n"
    "  simp only [problem_spec_matrixSum, implementation_matrixSum,\n"
    "    canonicalizeMatrixSum, survivingNames, List.filterMap_cons,\n"
    "    List.filterMap_nil, List.head?_cons, List.cons_append,\n"
    "    List.nil_append, Id.run, pure, h1, hAZ]\n"
    "  all_goals decide\n"
)

# ---------------------------------------------------------------------------
# F1/F2 rival — the IDENTITY-ELIMINATION facet (added by the second audit).
#
# Every other rival in this battery reaches the surviving-name list through
# `survivingNames` itself, so all of them agree with the frozen impl that an
# identity term contributes NOTHING to the result. That agreement was never
# tested: the clause "identity terms are dropped" is the other half of the
# discriminating behaviour (the first half being that the result stays a shaped
# matrix), and nothing pinned it.
#
# This rival maps EVERY term to a name instead of filtering — an identity term
# becomes the anonymous name "" and is carried into the result as a survivor,
# rather than eliminated. It is correct on F3 (the output is still canonically
# ordered) and it is a matrix (F1's constructor), so neither a sortedness check
# nor a constructor check detects it; it violates the elimination facet, and
# with it F2 (a term the input never named appears among the survivors).
# MUST reject.
# ---------------------------------------------------------------------------
_REJ_KEEP_IDENTITY = (
    "def implementation_matrixSum (terms : List MatSumTerm) : MatSum := Id.run do\n"
    "  let names := terms.map (fun x => match x with\n"
    "    | MatSumTerm.named n => n\n"
    "    | _ => \"\")\n"
    "  return MatSum.matrix (names.mergeSort nameLe)\n"
)

# Its witness is stated below, after `_W_MERGESORT_HAVES` (which it reuses).

# ---------------------------------------------------------------------------
# ADMISSIBILITY positive (added by the audit; the shipped port carried no
# `admissibility` case and gave no demonstrated reason, so the lane that detects
# PRECOND-TOO-STRONG was simply absent).
#
# The frozen obligation's binder is a genuine PRECONDITION — `terms ≠ []`, no
# `scalarZero` term, surviving names distinct — so the honest question is whether
# it ADMITS an F2P-shaped input, and whether the obligation is SATISFIABLE there
# rather than only vacuously true. The discriminating F2P shape is an all-identity
# matrix sum: several shaped additive-identity terms and no named term, which is
# exactly the input on which the degenerate shapeless-scalar outcome would arise.
#
# So the proof region first discharges, at that concrete input and by evaluation,
# every conjunct of the binder AND the Ensures clause itself — then closes the
# frozen obligation verbatim. Nothing is assumed: the `theorem correct_matrixSum`
# STATEMENT is byte-identical, the ground instance is a `have` inside the existing
# tactic body, and no new declaration / axiom / `sorry` appears. If this cannot
# verify, the precondition excludes a normal input (PRECOND-TOO-STRONG) or the
# obligation is unsatisfiable there.
# ---------------------------------------------------------------------------
_ADMISS_PROOF = (
    "theorem correct_matrixSum :\n"
    "    ∀ (terms : List MatSumTerm),\n"
    "      terms ≠ [] →\n"
    "      (∀ t ∈ terms, t ≠ MatSumTerm.scalarZero) →\n"
    "      (survivingNames terms).Nodup →\n"
    "      problem_spec_matrixSum terms (implementation_matrixSum terms) := by\n"
    "  -- Admissibility at the F2P-shaped input: an all-identity matrix sum.\n"
    "  -- Every binder conjunct holds there, and the Ensures clause is satisfied\n"
    "  -- by EVALUATION (not vacuously) -- the result is the shaped identity\n"
    "  -- matrix `matrix []`, carrying no names.\n"
    "  have hAdm :\n"
    "      ([MatSumTerm.zeroMatrix, MatSumTerm.zeroMatrix] ≠ []) ∧\n"
    "      (∀ t ∈ [MatSumTerm.zeroMatrix, MatSumTerm.zeroMatrix],\n"
    "        t ≠ MatSumTerm.scalarZero) ∧\n"
    "      (survivingNames [MatSumTerm.zeroMatrix, MatSumTerm.zeroMatrix]).Nodup ∧\n"
    "      problem_spec_matrixSum [MatSumTerm.zeroMatrix, MatSumTerm.zeroMatrix]\n"
    "        (implementation_matrixSum\n"
    "          [MatSumTerm.zeroMatrix, MatSumTerm.zeroMatrix]) := by\n"
    "    refine ⟨by simp, ?_, ?_, ?_⟩\n"
    "    · intro t ht\n"
    "      simp only [List.mem_cons, List.not_mem_nil, or_false] at ht\n"
    "      rcases ht with h | h <;> simp [h]\n"
    "    · simp [survivingNames]\n"
    "    · simp only [problem_spec_matrixSum, implementation_matrixSum,\n"
    "        canonicalizeMatrixSum, survivingNames, List.filterMap_cons,\n"
    "        List.filterMap_nil, List.head?_cons, List.mergeSort_nil, Id.run, pure]\n"
    "  -- The frozen obligation, closed verbatim.\n"
    "  intro terms hne hns _\n"
    "  unfold problem_spec_matrixSum implementation_matrixSum canonicalizeMatrixSum\n"
    "  simp only [Id.run]\n"
    "  cases hs : survivingNames terms with\n"
    "  | nil =>\n"
    "    simp only [List.mergeSort_nil]\n"
    "    cases ht : terms with\n"
    "    | nil => exact absurd ht hne\n"
    "    | cons a as =>\n"
    "      have ha : a ≠ MatSumTerm.scalarZero := hns a (by rw [ht]; exact List.mem_cons_self ..)\n"
    "      cases a\n"
    "      · exact absurd rfl ha\n"
    "      · rfl\n"
    "      · rfl\n"
    "  | cons n ns =>\n"
    "    rfl\n"
)


# ---------------------------------------------------------------------------
# WITNESS TACTIC (shared by every reject case). AUDIT REPAIR.
#
# The naive shape (`unfold ...; decide` / `unfold ...; simp`) does NOT work on
# this carrier, and the way it fails is silent rather than loud. Two blockers,
# both measured with real builds against the frozen solution:
#
#  (a) `decide` reduces the `Decidable` instance rather than evaluating, and
#      `List.mergeSort` is compiled by well-founded recursion, so
#      `(l.mergeSort nameLe).hasDecEq …` gets STUCK for any l with >= 2
#      elements. `rfl`, `decide +kernel` and plain `decide` all fail on
#      `["B","A"].mergeSort nameLe = ["A","B"]`, and the failure is a stuck
#      instance, not a verdict.
#  (b) `Id.run`/`pure` do not reduce under `unfold` alone: a goal left as
#      `pure (MatSum.matrix []) = MatSum.matrix []` defeats `simp` and `rfl`.
#
# Either blocker makes the gold-side build fail for a reason that has NOTHING
# to do with what the witness claims — the same error appears for the claim and
# for its exact negation — so the rejection would attest to a carrier limit
# instead of to the spec. The FORGERY test is what exposes that: flipping the
# `¬` must CHANGE gold's exit code, and under the naive shape it does not.
#
# So each witness first discharges the `mergeSort` values it needs as `have`s
# (the sizes are 0, 1 and 2, and `nameLe` on two literals is closed via
# `String.le_iff_toList_le` + `decide`, which DOES reduce), then rewrites the
# whole spec/impl chain — including `Id.run`, `pure` and the `filterMap`
# equations — down to a literal `MatSum` (in)equality, and only then decides.
# With that, `decide` is handed a ground `MatSum` comparison and evaluates: gold
# reduces the claim to `¬True` and reports "`decide` proved … is false", while
# the flipped claim ELABORATES (exit 0). The exit code now tracks the claim,
# which is the whole point.
_W_MERGESORT_HAVES = (
    "  have h0 : ([] : List String).mergeSort nameLe = [] := by simp\n"
    "  have h1 : ([\"A\"] : List String).mergeSort nameLe = [\"A\"] := by simp\n"
    "  have hAB : ([\"A\",\"B\"] : List String).mergeSort nameLe = [\"A\",\"B\"] := by\n"
    "    have h : nameLe \"A\" \"B\" = true := by\n"
    "      simp only [nameLe, decide_eq_true_eq, String.le_iff_toList_le]; decide\n"
    "    simp [List.mergeSort, h]\n"
    "  have hBA : ([\"B\",\"A\"] : List String).mergeSort nameLe = [\"A\",\"B\"] := by\n"
    "    have h : nameLe \"B\" \"A\" = false := by\n"
    "      simp only [nameLe, decide_eq_false_iff_not, String.le_iff_toList_le]; decide\n"
    "    simp [List.mergeSort, h]\n"
)
_W_REDUCE_DECIDE = (
    "  simp only [problem_spec_matrixSum, implementation_matrixSum,\n"
    "    canonicalizeMatrixSum, survivingNames, List.filterMap_cons,\n"
    "    List.filterMap_nil, List.head?_cons, Id.run, pure, h0, h1, hAB, hBA]\n"
    "  all_goals decide\n"
)


def _witness(terms):
    """`¬ problem_spec_matrixSum <terms> (implementation_matrixSum <terms>)`.

    Stated at a literal input and closed by full reduction + `decide`, so the
    build's verdict is a decision about THIS claim at THIS input. `all_goals`
    rather than a bare `decide` because the reduction closes the goal outright
    for some impls (the rival's own value already differs syntactically), and a
    bare `decide` would then error with "no goals" on exactly the cases where
    the refutation is most obvious.
    """
    return (f"example : ¬ problem_spec_matrixSum {terms}\n"
            f"    (implementation_matrixSum {terms}) := by\n"
            + _W_MERGESORT_HAVES + _W_REDUCE_DECIDE)


# Witness for the identity-elimination rival. Refuted at a MIXED input (one named
# term plus one identity term) — the point where elimination is observable at
# all: on an all-named input this rival and the frozen impl agree, and on an
# all-identity input "" is the only name either shape could carry.
# `List.map_cons`/`List.map_nil` reduce the rival's traversal, and the sorted pair
# is ["","A"] (the empty string precedes "A" in codepoint order), so it needs its
# own `have` rather than reusing `_witness`'s set. Same principle throughout:
# reduce the whole spec/impl chain to a literal `MatSum`, then decide.
_W_KEEP_IDENTITY = (
    "example : ¬ problem_spec_matrixSum [MatSumTerm.named \"A\", MatSumTerm.zeroMatrix]\n"
    "    (implementation_matrixSum [MatSumTerm.named \"A\", MatSumTerm.zeroMatrix]) := by\n"
    + _W_MERGESORT_HAVES +
    "  have hEA : ([\"A\",\"\"] : List String).mergeSort nameLe = [\"\",\"A\"] := by\n"
    "    have h : nameLe \"A\" \"\" = false := by\n"
    "      simp only [nameLe, decide_eq_false_iff_not, String.le_iff_toList_le]; decide\n"
    "    simp [List.mergeSort, h]\n"
    "  simp only [problem_spec_matrixSum, implementation_matrixSum,\n"
    "    canonicalizeMatrixSum, survivingNames, List.filterMap_cons,\n"
    "    List.filterMap_nil, List.head?_cons, List.map_cons, List.map_nil,\n"
    "    Id.run, pure, h0, h1, hAB, hBA, hEA]\n"
    "  all_goals decide\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-direct-wrap",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant_impl_proof(_POS_IMPL, _POS_PROOF),
        "rationale": "A structurally-different but behaviourally-identical impl "
                     "(surviving names computed up front and the sorted list "
                     "wrapped directly, skipping the case split) with its own "
                     "closing proof. Satisfies the single Ensures clause on every "
                     "admissible input. If it cannot verify, SPEC-TOO-STRONG.",
    },
    {
        "id": "uniq-seed-scalar-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_SEED_SCALAR),
        "refinement": "The faithful real form seeds a scalar identity ahead of the "
                      "matrix terms, so an all-identity sum canonicalizes to a "
                      "shapeless scalar instead of the shaped identity matrix. Its "
                      "real patch leaves an all-zero block as a scalar with no "
                      "shape, so block_collapse over repeated block products reads "
                      ".cols on a shapeless object and raises — both F2P "
                      "(test_issue_17624, test_zero_matrix_add) stay unresolved.",
        "rationale": "Violates facet F1 (result is a matrix, never the shapeless "
                     "scalar) on the all-identity sub-domain. This is the "
                     "discriminating fix clause.",
        # Refuted at the all-identity input, where gold yields the shaped
        # identity matrix `matrix []` and this rival's seeded scalar makes it
        # `scalar`. Rebuilt during the audit: the previous `unfold …; decide`
        # form failed on GOLD with a stuck `instDecidableNot`, i.e. the same
        # error for this claim and for its negation, so it discriminated
        # nothing. See `_witness`.
        "witness": _witness("[MatSumTerm.zeroMatrix]"),
    },
    {
        "id": "uniq-always-scalar-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_ALWAYS_SCALAR),
        "refinement": "Cheap supporting near-miss: every sum is claimed to "
                      "degenerate to a shapeless scalar. A faithful patch would "
                      "strip the shape off every matrix sum, so every downstream "
                      "consumer reading a shape raises and both F2P stay "
                      "unresolved. Refuted at a non-degenerate input where the "
                      "correct result plainly carries a named term.",
        "rationale": "Violates facet F1 on the whole domain; subsumes the seed "
                     "rival there but is refuted at a DIFFERENT input point (a "
                     "single named term, not the all-identity input), so it is not "
                     "a substitute for the reasoned seed rival.",
        # Refuted at a single named term, where the correct result plainly
        # carries the name. Rebuilt on the shared reducing tactic so gold's exit
        # code tracks the claim (the prior `simp` form left gold's goal
        # unsolved for the claim AND for its negation alike).
        "witness": _witness("[MatSumTerm.named \"A\"]"),
    },
    {
        "id": "uniq-drop-all-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_DROP_ALL),
        "refinement": "Always returns the empty (identity-matrix) result. The "
                      "constructor facet is correct (it IS a matrix), so an "
                      "F1-only check misses it; but it discards every surviving "
                      "named term. A faithful patch would collapse a genuine "
                      "matrix sum to the identity matrix, producing a structurally "
                      "wrong canonical form that would not match the gold "
                      "BlockMatrix in the F2P tests.",
        "rationale": "Violates facet F2 (carried name list = surviving named "
                     "terms) while leaving F1 correct.",
        # Refuted at a mixed input (one named term plus an identity term), where
        # gold keeps the name and this rival discards it. Rebuilt on the shared
        # reducing tactic; the prior `simp` form left gold's goal unsolved
        # identically for the claim and its negation.
        "witness": _witness("[MatSumTerm.named \"A\", MatSumTerm.zeroMatrix]"),
    },
    {
        "id": "uniq-drop-one-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_DROP_ONE),
        "refinement": "Keeps the canonical ORDER but silently drops the first "
                      "surviving name. Correct on F1 (matrix) and F3 (sorted), so "
                      "neither a constructor check nor a sortedness check detects "
                      "it; the rebuilt sum spans the wrong number of matrix terms. "
                      "A faithful patch would build a sum over the wrong blocks, "
                      "diverging from the gold canonical form in the F2P tests.",
        "rationale": "Violates facet F2 (a surviving term is dropped) while "
                     "leaving F1 and F3 correct. Targets the count facet a "
                     "constructor- or order-only rival would not exercise.",
        # Refuted at two already-sorted named terms, where gold carries both and
        # this rival carries only the second. Rebuilt on the shared reducing
        # tactic: the prior form rewrote gold's goal to
        # `¬(pure (MatSum.matrix ["A","B"])).run = MatSum.matrix ["A","B"]` and
        # `decide` then reported "proved … is false" — which reads like a
        # refutation but is the SAME error the flipped claim produces, because
        # the `pure` was never reduced.
        "witness": _witness("[MatSumTerm.named \"A\", MatSumTerm.named \"B\"]"),
    },
    {
        "id": "uniq-unsorted-input-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_UNSORTED),
        "refinement": "Keeps the surviving names in INPUT order instead of "
                      "canonical order. Correct on F1 and F2 (right constructor, "
                      "same multiset of names); a faithful patch would build a "
                      "canonically-unequal sum node, so the result would not match "
                      "the gold canonical form when the terms are not already "
                      "sorted (the matadd canonical-ordering tests would diverge).",
        "rationale": "Violates facet F3 (canonical ordering) while leaving F1 and "
                     "F2 correct. Refuted at an input whose surviving names are in "
                     "reverse order.",
        # Refuted at two named terms in REVERSE order, the point where input
        # order and canonical order differ. Rebuilt on the shared reducing
        # tactic for the same reason as the drop-one case: the prior form's
        # `decide` decided an unreduced `pure …` goal and produced the identical
        # error for the flipped claim.
        "witness": _witness("[MatSumTerm.named \"B\", MatSumTerm.named \"A\"]"),
    },
    {
        "id": "uniq-invent-extra-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_INVENT_NAME),
        "refinement": "Appends a name that was never among the input terms, "
                      "keeping every genuine survivor and canonical order. A "
                      "faithful patch would build the canonical sum over a term "
                      "the caller never supplied, so the rebuilt result spans one "
                      "block more than the input describes; the downstream "
                      "consumer reads a shape that does not correspond to any "
                      "input term and the canonical form diverges from gold on "
                      "every matrix sum, F2P included.",
        "rationale": "Violates facet F2 in the direction the rest of the battery "
                     "leaves unattacked: every other F2 rival DROPS a surviving "
                     "name, so none of them pins 'no term is invented'. Correct "
                     "on F1 (still a matrix) and F3 (still sorted), so neither a "
                     "constructor nor a sortedness check detects it.",
        "witness": _W_INVENT,
    },
    {
        "id": "uniq-keep-identity-as-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant_impl(_REJ_KEEP_IDENTITY),
        "refinement": "Maps every term to a name instead of filtering, so an "
                      "additive-identity term is carried into the result as an "
                      "anonymous survivor rather than eliminated. A faithful patch "
                      "would rebuild the canonical sum with one node per input "
                      "term, identity terms included, so the identity blocks are "
                      "never dropped: the canonical form has the wrong arity on "
                      "every sum containing a zero block, which is exactly the F2P "
                      "shape, and the downstream consumer reads a term the input "
                      "never named.",
        "rationale": "Pins the identity-ELIMINATION half of the discriminating "
                     "behaviour, which no other rival here tests: every other "
                     "rival reaches its name list through `survivingNames` and so "
                     "AGREES with the frozen impl that an identity term "
                     "contributes nothing. Violates F2 (a name the input never "
                     "supplied appears among the survivors) while leaving F1's "
                     "constructor and F3's ordering correct.",
        # Refuted at a MIXED input (one named + one identity term) — the only
        # shape where elimination is observable; an all-named input has nothing
        # to eliminate and an all-identity input collapses either way. Audit
        # builds: witness/rival exit 0, witness/gold exit 1 with `¬True` (gold
        # reduces the claim to a decided falsehood), and the flipped claim
        # inverts both (gold exit 0, rival exit 1 on
        # `MatSum.matrix ["", "A"] = MatSum.matrix ["A"]`), so gold's exit code
        # tracks the claim rather than a carrier limit.
        "witness": _W_KEEP_IDENTITY,
    },
    {
        "id": "admiss-all-identity-sum",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": "The obligation's binder (terms non-empty; no scalar-identity "
                     "term; surviving names distinct) must ADMIT the F2P-shaped "
                     "input, and the Ensures clause must be satisfiable there "
                     "rather than vacuously true. Every binder conjunct is "
                     "discharged at the concrete all-identity matrix sum "
                     "[zeroMatrix, zeroMatrix] and the Ensures clause is closed by "
                     "EVALUATION (the result reduces to the shaped identity matrix "
                     "`matrix []`), as a `have` preceding the frozen obligation, "
                     "which is then closed verbatim with a byte-identical "
                     "statement. If this cannot verify, the precondition excludes "
                     "a normal input (PRECOND-TOO-STRONG) or the obligation is "
                     "unsatisfiable at exactly the input the fix is about.",
    },
]

# No axiom lane in this port: AXIOM_TESTS is the G-AX gate's responsibility and
# this gate ignores it.
AXIOM_TESTS = []
