# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10466 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   dedupSort : List (String × Int × String) → List (String × Int)
#   Given a list of occurrence records (each a source name, a line number, and an
#   opaque per-occurrence identifier), report the list of positions that should be
#   shown: every distinct (source, line) recorded, each once, in ascending
#   lexicographic order (source first, line as tie-break). The single postcondition
#   has TWO independent top-level clauses over the sole input binder `triples`:
#     (1) List.Sorted lexLt result — the result is STRICTLY ascending, which
#         simultaneously pins the ordering (sorted) AND the absence of repeats
#         (deduplicated); and
#     (2) ∀ p, p ∈ result ↔ ∃ u, (p.1, p.2, u) ∈ triples — a position is reported
#         iff it was recorded by some occurrence (its identifier is irrelevant).
#   Together these pin the result to exactly the distinct recorded positions,
#   ascending. Every clause is grounded structurally in `triples`; there is no
#   opaque callee and no answer-key oracle (meta.json axioms == [],
#   deep_model_references == []), so the ungrounded-oracle-echo attack is N/A.
#
# ADVERSARIAL READ of the nagini classes on this carrier:
#
#   * FRAME / PERMISSION MUTATION (nagini cases 1 & 2, MANDATORY there) — VACUOUS.
#     nagini holds `recorded` / `xs` at Acc(...,1/2) read-only permission and makes
#     an input-write rival mandatory (rejected for insufficient permission). Lean is
#     referentially transparent: the sole input is a plain immutable value, there is
#     no half-permission to violate and no aliasing to exploit, so this whole class
#     has NO expressible instance here. No substitute is fabricated for it.
#
#   * PARTIAL-DOMAIN no-dedup / no-sort (nagini case 3, the load-bearing pre-patch
#     rival) — APPLIES and is ported as TWO distinct rivals, because on this carrier
#     "no dedup, no sort" splits into two separable defects, each attacking clause
#     (1) on a different sub-domain:
#       - `weak-verbatim-projection`: emit the projected positions in scan order
#         with neither dedup nor sort — the literal pre-patch. Refuted at an
#         UNSORTED-DISTINCT input (order clause).
#       - `weak-no-dedup`: sort but do NOT deduplicate (the near-miss that agrees
#         with gold on every all-distinct input and diverges only when a position
#         recurs). Given its own witness at a DUPLICATE input, per the
#         near-miss rule, so its rationale's sub-domain is actually demonstrated.
#
#   * PARTIAL-DOMAIN drop-last (nagini case 5, off-by-one bound) — APPLIES.
#     `weak-drop-last` folds over all but the final occurrence; on a single-occurrence
#     input the reported list is empty though clause (2) demands that position appear.
#     Refuted via the membership clause — a distinct clause from the other two rivals.
#
#   * FABRICATED OUTPUT (no nagini ancestor; added by AUDIT) — APPLIES.
#     Clause (2) is an IFF and therefore has TWO independent directions. drop-last
#     attacks only the BACKWARD one (recorded ⇒ reported). `weak-spurious-position`
#     attacks the FORWARD one (reported ⇒ recorded) by padding the projection with a
#     position no occurrence recorded, refuted at the EMPTY input where the result
#     must be empty. Without it an impl that INVENTS positions was unprobed and the
#     battery's claim to attack "clause (2)" was only half true. This is also where
#     spec_guide §0.5's frame discipline becomes concrete on a transparent carrier:
#     an output only lower-bounded by the input is the analogue of the
#     full-permission hole.
#
#   * PARTIAL-DOMAIN keep-duplicate-key (nagini case 4) — SUBSUMED. nagini modeled a
#     separate `insert_sorted` helper whose per-step dedup was attackable in
#     isolation; this bundle models only the whole-list dedupSort core (see
#     mapping.md — one modeled function), so "keep an equal key" is not a distinct
#     modeled behavior. Its intent (the result must not contain a duplicate that the
#     input recorded twice) is exactly clause (1)'s no-repeats content and is covered
#     by `weak-no-dedup`, which sorts but keeps the duplicate. See 'assessment'.
#
#   * POSITIVE CONTROL / soundness (nagini case 6) — APPLIES, and is carried as TWO
#     positives after an audit found ONE of them too cheap to be load-bearing:
#       - `pos-map-fold`: replaces the mutable accumulator loop with the equivalent
#         `List.map` projection (same value on every input), a pure control-flow
#         reshape. The frozen theorem STATEMENT is byte-identical and the only proof
#         edit is collapsing the loop==map bridge lemma to `rfl` (the map form is
#         definitionally the bridge's RHS). Honest, but the reproof is FREE, so it
#         attests only that the spec tolerates a different control flow.
#       - `pos-sort-then-dedup`: COMMUTES the two post-processing stages
#         (`(sort …).dedup` for `(dedup …).sort`). Same result, but NOT
#         definitionally so, so both clause proofs must be genuinely redone
#         (sortedness via dedup-is-a-sublist-of-a-sorted-list; repeat-freeness from
#         the outer dedup rather than transported across the sort permutation).
#         This is the positive that actually tests the spec pins the RESULT rather
#         than gold's staging. No new lemma/axiom/sorry in either.
#
#   * ADMISSIBILITY (nagini case 7) — APPLIES, and is now carried as
#     `admissibility-ground-instance`. An earlier reading recorded this lane as N/A
#     because the frozen obligation `∀ triples, problem_spec … (implementation …)`
#     has NO precondition hypothesis, hence nothing that could be
#     PRECOND-TOO-STRONG. That confuses the lane's mechanism with its purpose: the
#     question is whether the obligation is SATISFIABLE AT ALL, and on a total
#     carrier the analogue of an inhabited precondition is discharging the
#     postcondition BY EVALUATION at a concrete F2P-shaped input, as a `have` ahead
#     of the frozen tactic script (which then runs verbatim). That is expressible
#     here, so the omission was a genuine gap; see the case's rationale for why it
#     is not subsumed by the positives or by G-VERIFY (all of which route through
#     the same three helper lemmas).
#
#   * AXIOM_TESTS (nagini AXIOM lane) — DROPPED. This bundle declares no axiom / deep-
#     model reference (dedup/sort/order modeled deeply), G-AX is a skip stub, and the
#     axiom lane is not this gate's job.
#
# WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
# reshaping an impl, so a rejection alone attributes nothing. Each expect="reject"
# case therefore states a spec clause directly at a concrete input (small integer
# lines, single-char sources), and each was built against the rival (must
# ELABORATE) and rebuilt against the frozen solution (must FAIL).
#
# Elaborate-vs-fail is NECESSARY but NOT SUFFICIENT, and the four witnesses this
# battery originally shipped are the counterexample: each opened by rewriting the
# impl to a literal value BEFORE mentioning the spec, so the gold-side failure was
# a value mismatch that the claim never entered — asserting the OPPOSITE of each
# witness reproduced the byte-identical gold error. All four were rewritten to
# state the spec claim first and reduce inside the resulting hypothesis, and each
# was then re-checked by the forgery test (flip the claim: must fail DIFFERENTLY)
# and by a type-revealing probe. See the AUDIT NOTE above the witness definitions
# for the measured evidence.
#
# BINDER / CLAUSE COVERAGE. The spec has ONE input binder (`triples`) and TWO
# independent clauses, the second of which is an IFF with two separable directions.
# `triples` is varied across FOUR distinct reject-witness inputs (pts = 4): an
# unsorted-distinct pair, a duplicate pair, a single-occurrence list, and the EMPTY
# list. Each of those changes the spec's verdict for the rival stated at it, so the
# variation is meaningful and not four spellings of one point. Coverage:
#   clause (1) order      -> `weak-verbatim-projection`
#   clause (1) no-repeats -> `weak-no-dedup`   (near-miss; own duplicate input)
#   clause (2) backward   -> `weak-drop-last`  (recorded but not reported)
#   clause (2) forward    -> `weak-spurious-position` (reported but not recorded)
# The admissibility case adds a FIFTH input point (a position recorded twice plus
# two further distinct positions) at which BOTH clauses are discharged positively
# by evaluation, so the binder is exercised on the satisfying side too and not only
# through refutations.
# EXACTNESS. An audit additionally PROVED, against this carrier, that the frozen
# postcondition is functional: any two results satisfying it for the same input are
# equal (`lexLt` is irreflexive and antisymmetric, so Sorted lexLt gives Nodup plus
# a total order, and the membership iff fixes the element set; conclude by
# List.eq_of_perm_of_sorted). So the spec admits EXACTLY ONE result per input and no
# wrong impl of this behavior can satisfy it — the reject lane above samples that
# fact rather than being the whole of the evidence for it.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10466"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). ------------------------------------------------------------
# The whole gold impl body (mutable accumulator loop + dedup/sort return):
_IMPL_GOLD = (
    "def implementation_dedupSort\n"
    "    (triples : List (String × Int × String)) : List (String × Int) := Id.run do\n"
    "  let mut pairs : List (String × Int) := []\n"
    "  for t in triples do\n"
    "    pairs := pairs ++ [(t.1, t.2.1)]\n"
    "  return pairs.dedup.mergeSort lexLe"
)
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"

# The final `return` line (dedup + sort), unique inside the impl region:
_RET_GOLD = "  return pairs.dedup.mergeSort lexLe"
assert _BASE.count(_RET_GOLD) == 1, "return anchor drifted"

# The loop header line, unique inside the impl region:
_FOR_GOLD = "  for t in triples do"
assert _BASE.count(_FOR_GOLD) == 1, "for-loop anchor drifted"

# The frozen loop==map bridge lemma proof body (inside proof-start/proof-end):
_LOOP_HEAD = (
    "theorem loop_eq_map (triples : List (String × Int × String)) :\n"
    "    implementation_dedupSort triples = (mappedPairs triples).dedup.mergeSort lexLe := by\n"
)
assert _BASE.count(_LOOP_HEAD) == 1, "loop_eq_map head anchor drifted"

_LOOP_PROOF = (
    "theorem loop_eq_map (triples : List (String × Int × String)) :\n"
    "    implementation_dedupSort triples = (mappedPairs triples).dedup.mergeSort lexLe := by\n"
    "  simp only [implementation_dedupSort, mappedPairs, Id.run]\n"
    "  have key : (List.map (fun x2 : String × Int × String => [(x2.1, x2.2.1)]) triples).flatten\n"
    "      = List.map (fun t => (t.1, t.2.1)) triples := by\n"
    "    induction triples with\n"
    "    | nil => rfl\n"
    "    | cons h t ih => simp only [List.map_cons, List.flatten_cons, List.singleton_append, ih]\n"
    "  simp\n"
    "  rw [key]\n"
    "  rfl"
)
assert _BASE.count(_LOOP_PROOF) == 1, "loop_eq_map proof anchor drifted"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------
# pos-map-fold: replace the mutable accumulator loop with the equivalent direct
# `List.map` projection. Same value on every input (the loop's fold IS the map),
# a pure control-flow reshape. The map form is DEFINITIONALLY the RHS of the
# frozen `loop_eq_map` bridge lemma, so the only proof edit is collapsing that
# lemma's body to `rfl`; the `theorem correct_dedupSort` STATEMENT is byte-
# identical and no new declaration/axiom/sorry is introduced. If it FAILS =>
# SPEC-TOO-STRONG (a faithful, structurally-different correct impl rejected).
_POS_IMPL = (
    "def implementation_dedupSort\n"
    "    (triples : List (String × Int × String)) : List (String × Int) :=\n"
    "  (triples.map (fun t => (t.1, t.2.1))).dedup.mergeSort lexLe"
)
_POS_LOOP_PROOF = (
    "theorem loop_eq_map (triples : List (String × Int × String)) :\n"
    "    implementation_dedupSort triples = (mappedPairs triples).dedup.mergeSort lexLe := by\n"
    "  rfl"
)
_MOD_POS = _swap(_swap(_BASE, _IMPL_GOLD, _POS_IMPL), _LOOP_PROOF, _POS_LOOP_PROOF)


# pos-sort-then-dedup: a SECOND positive whose correctness is NOT definitional.
# AUDIT NOTE. `pos-map-fold` above is a genuine reshape, but its proof edit is
# free: the map form is definitionally the frozen bridge lemma's RHS, so the
# whole reproof collapses to `rfl` and the two clauses are re-established by the
# frozen lemmas verbatim. That makes it a weak soundness control — it exercises
# the spec's tolerance of a different CONTROL FLOW but not of a different
# post-processing PIPELINE. This case closes that gap: it commutes the two
# post-processing stages, computing `(sort …).dedup` instead of
# `(dedup …).sort`. Both yield the distinct positions ascending, but the
# equality is NOT definitional and neither frozen lemma applies as written, so
# the proof has to be genuinely redone on both clauses:
#   * sortedness now comes from `dedup` being a SUBLIST of a sorted list
#     (List.Pairwise.sublist (List.dedup_sublist _) …) rather than directly from
#     List.sorted_mergeSort; and
#   * nodup now holds of the outer `dedup` directly (List.nodup_dedup) instead
#     of being transported across the mergeSort permutation.
# The `theorem correct_dedupSort` STATEMENT stays byte-identical and no new
# declaration/axiom/sorry appears — only the three helper lemmas' own statements
# follow the reshaped intermediate, which is what a legitimate reproof does. If
# it FAILS => SPEC-TOO-STRONG: the spec would be pinning gold's particular
# dedup-then-sort staging rather than the distinct-positions-ascending result.
_POS2_IMPL = _IMPL_GOLD.replace(_RET_GOLD, "  return (pairs.mergeSort lexLe).dedup")
_MOD_POS2 = _swap(_BASE, _IMPL_GOLD, _POS2_IMPL)
# Retarget the bridge lemma and the two clause lemmas at the commuted pipeline.
_MOD_POS2 = _swap(
    _MOD_POS2, _LOOP_HEAD,
    "theorem loop_eq_map (triples : List (String × Int × String)) :\n"
    "    implementation_dedupSort triples = ((mappedPairs triples).mergeSort lexLe).dedup := by\n",
)
_MOD_POS2 = _swap(
    _MOD_POS2,
    "      p ∈ (mappedPairs triples).dedup.mergeSort lexLe ↔",
    "      p ∈ ((mappedPairs triples).mergeSort lexLe).dedup ↔",
)
_MOD_POS2 = _swap(
    _MOD_POS2,
    "  simp only [List.mem_mergeSort, List.mem_dedup, mappedPairs, List.mem_map]",
    "  simp only [List.mem_dedup, List.mem_mergeSort, mappedPairs, List.mem_map]",
)
_MOD_POS2 = _swap(
    _MOD_POS2,
    "      ((mappedPairs triples).dedup.mergeSort lexLe) := by\n"
    "  exact List.sorted_mergeSort lexLe_trans\n"
    "    (fun a b => by simp only [Bool.or_eq_true]; exact lexLe_total a b) _",
    "      (((mappedPairs triples).mergeSort lexLe).dedup) := by\n"
    "  exact List.Pairwise.sublist (List.dedup_sublist _)\n"
    "    (List.sorted_mergeSort lexLe_trans\n"
    "      (fun a b => by simp only [Bool.or_eq_true]; exact lexLe_total a b) _)",
)
_MOD_POS2 = _swap(
    _MOD_POS2,
    "    ((mappedPairs triples).dedup.mergeSort lexLe).Nodup :=\n"
    "  (List.mergeSort_perm _ _).nodup_iff.mpr (List.nodup_dedup _)",
    "    (((mappedPairs triples).mergeSort lexLe).dedup).Nodup :=\n"
    "  List.nodup_dedup _",
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness.
# ---------------------------------------------------------------------------

# weak-verbatim-projection (= the literal pre-patch): emit the projected
# (source, line) positions in SCAN ORDER with neither dedup nor sort.
_VERBATIM_IMPL = _IMPL_GOLD.replace(_RET_GOLD, "  return pairs")

# weak-no-dedup (near-miss): SORT the positions but do NOT deduplicate, so a
# position recorded twice is reported twice. Agrees with gold on every
# all-distinct input; diverges only when a position recurs.
_NODEDUP_IMPL = _IMPL_GOLD.replace(_RET_GOLD, "  return pairs.mergeSort lexLe")

# weak-drop-last (off-by-one bound): fold over all occurrences EXCEPT the final
# one. On a single-occurrence input the reported list is empty though the
# recorded position should appear.
_DROPLAST_IMPL = _IMPL_GOLD.replace(_FOR_GOLD, "  for t in triples.dropLast do")

# weak-spurious-position: report a position that NO occurrence recorded.
# AUDIT NOTE. Clause (2) is an IFF, so it has two independent directions, and
# the ported battery attacked only one of them. `weak-drop-last` refutes the
# BACKWARD direction (recorded ⇒ reported: a position was recorded but is
# missing). Nothing in the battery attacked the FORWARD direction
# (reported ⇒ recorded: a position is reported that was never recorded), so the
# port's own coverage claim that "clause (2) is attacked" was only half true and
# an impl that INVENTS positions was unprobed. This rival appends a fixed
# position to the projection before dedup/sort, so it reports a position with no
# occurrence backing it; on the empty input it reports one position where the
# result must be empty. This is also the direction that makes the frame
# discipline of §0.5 concrete on a referentially transparent carrier: a spec
# clause that only demanded "every recorded position appears" would let an impl
# pad its output with anything.
_SPURIOUS_IMPL = _IMPL_GOLD.replace(
    _RET_GOLD, '  return (pairs ++ [("z", 9)]).dedup.mergeSort lexLe')


def _mod_impl(impl_body):
    return _swap(_BASE, _IMPL_GOLD, impl_body)


# --- witnesses -------------------------------------------------------------------
# AUDIT NOTE — WHY THESE WITNESSES WERE REWRITTEN. The witnesses this battery
# originally shipped opened by REWRITING the impl to a literal result before
# stating anything about the spec:
#
#     rw [show implementation_dedupSort <input> = <literal> from rfl]
#     rintro ⟨hsorted, -⟩ ...
#
# That elaborates against the rival (whose result IS that literal) and fails on
# the frozen solution — both halves the gate checks — but the failure is at the
# `rw`/`show` step, which never mentions the spec at all: it is the step that
# says "gold's value is a different list". A gold-side error produced BEFORE the
# claim is used carries no information about the claim, and the two-line
# experiment demonstrates it: rebuilding each witness against the frozen solution
# with the leading `¬` DROPPED — i.e. asserting the exact OPPOSITE, that gold
# SATISFIES the spec at that input, which is TRUE — produced the byte-identical
# error on all four cases (measured; e.g. `Type mismatch rfl ... expected
# implementation_dedupSort [("a",2,"x"),("a",1,"y")] = [("a",2),("a",1)]`).
# So the gate would have recorded `rejected` for a witness claiming gold is
# CORRECT, and the rejections attested to a value/reduction mismatch rather than
# to the spec.
#
# THE REPAIR is to state the spec claim FIRST and let the impl reduce inside the
# resulting hypothesis, so the surviving hypothesis is what decides the build:
#
#     rintro ⟨hsorted, -⟩            -- assume the spec holds of the rival
#     simp [<reduction set>] at hsorted
#
# Against the RIVAL, `simp` reduces the impl AND refutes the clause, closing the
# goal (exit 0). Against the frozen solution `simp` reduces the impl and PROVES
# the clause, so the hypothesis becomes `True` and no contradiction is available:
# `unsolved goals ... hsorted : True ⊢ False` (exit 1). That pair tracks the
# claim, which is the property the previous shape lacked. Confirmed by the
# type-revealing probe (append `exact (hsorted : Nat)`): gold prints
# `hsorted has type True` — simp PROVED the clause there — while the rival prints
# `No goals to be solved`, i.e. simp had already derived the contradiction. Both
# directions machine-checked on every case.
#
# `simp` (not `decide`) does the reducing: `decide` reduces the `Decidable`
# instance and stalls on `String.decEq`/`String.decidableLT'` ("did not reduce to
# isTrue or isFalse"), so it cannot compare two `String × Int` lists at all. The
# reduction set below (`Id.run, pure, bind` for the accumulator loop;
# `List.dedup, List.mergeSort, List.merge` for the post-processing; `lexLt, lexLe,
# List.sorted_cons` for the clause) is what actually computes on this carrier.
_REDUCE = (
    "implementation_dedupSort, Id.run, pure, bind, lexLt, lexLe, "
    "List.sorted_cons, List.mergeSort, List.merge, List.dedup"
)


# Order/strictness-clause refutation: assume clause (1) of the spec for the
# rival's own result, then reduce. `List.Sorted lexLt` is STRICT, so this refutes
# both an out-of-order pair and a repeated one, at whichever input is given.
def _wit_sorted(triples_lit):
    return (
        f"example : ¬ problem_spec_dedupSort\n"
        f"    {triples_lit}\n"
        f"    (implementation_dedupSort {triples_lit}) := by\n"
        f"  rintro ⟨hsorted, -⟩\n"
        f"  simp [{_REDUCE}] at hsorted"
    )


_WIT_VERBATIM = _wit_sorted('[("a", 2, "x"), ("a", 1, "y")]')
_WIT_NODEDUP = _wit_sorted('[("a", 1, "x"), ("a", 1, "y")]')

# Clause (2) BACKWARD (recorded ⇒ reported): instantiate the `↔` with `.mpr` on
# the position the sole occurrence records, obtaining membership in the rival's
# result; reducing that result exposes the empty list, so the membership is
# absurd. On gold the same reduction makes the hypothesis `True` (the position IS
# reported), so nothing closes the goal.
_WIT_DROPLAST = (
    'example : ¬ problem_spec_dedupSort\n'
    '    [("p", 1, "x")]\n'
    '    (implementation_dedupSort [("p", 1, "x")]) := by\n'
    "  rintro ⟨-, hmem⟩\n"
    '  have hin := (hmem ("p", 1)).mpr ⟨"x", by simp⟩\n'
    f"  simp [{_REDUCE}] at hin"
)

# Clause (2) FORWARD (reported ⇒ recorded) — the direction `weak-drop-last`
# leaves unattacked. Specialise the `↔` at the fabricated position and reduce the
# whole biconditional: against the rival it says "reported, therefore some
# occurrence recorded it" over the EMPTY occurrence list, which is false and
# closes the goal; against gold the position simply is not reported, the `↔`
# reduces to `True`, and no contradiction follows.
_WIT_SPURIOUS = (
    'example : ¬ problem_spec_dedupSort\n'
    '    ([] : List (String × Int × String))\n'
    '    (implementation_dedupSort ([] : List (String × Int × String))) := by\n'
    "  rintro ⟨-, hmem⟩\n"
    '  have h := hmem ("z", 9)\n'
    f"  simp [{_REDUCE}] at h"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — must VERIFY.
# ---------------------------------------------------------------------------
# AUDIT NOTE. This lane was originally dropped as "N/A", on the reasoning that
# the frozen obligation carries NO precondition hypothesis so there is nothing
# that could be PRECOND-TOO-STRONG. That reasoning is wrong about what the lane
# is for. Admissibility asks whether the obligation is SATISFIABLE AT ALL, and
# on a total carrier the analogue of "the precondition is inhabited" is: at a
# concrete, F2P-shaped input, the postcondition can be discharged BY EVALUATION,
# independently of the frozen proof's lemma chain. That is expressible here, so
# the omission was a real gap and this case closes it.
#
# Why it is not redundant with the positives or with G-VERIFY. Both positives
# and the frozen proof establish the ∀-statement through the same three helper
# lemmas (loop_eq_map / mergeSort_sorted_lexLe / mem_result_iff): if any of those
# were subtly mis-stated in a way that still composed, every one of those checks
# would pass together. This case instead names a concrete input whose shape
# matches the FAIL_TO_PASS scenario — a position recorded TWICE plus two further
# distinct positions, exactly the dedup-and-order interaction under test — and
# COMPUTES both clauses at it: the impl's value is obtained by reduction
# (`simp` + `decide`, since `rfl`/`decide` alone stall on String equality and
# `native_decide` is a banned assumption token), the strict-ordering clause is
# decided on the two adjacent comparisons, and the membership iff is checked in
# both directions by exhibiting a recording occurrence for each of the three
# reported positions and, conversely, matching each of the FOUR occurrences to a
# reported position. If the postcondition were unsatisfiable at that input — an
# over-constrained spec, e.g. one demanding both strict ordering and a repeat —
# this case would FAIL while the ∀-proof's lemma chain could still typecheck.
#
# Mechanically it inserts the evaluation as a `have` INSIDE the frozen
# `correct_dedupSort` proof, before the frozen script runs verbatim: the impl
# region is byte-identical to gold, the theorem STATEMENT is byte-identical, the
# frozen tactic body follows unchanged, and `have` is a local term (not a new
# top-level theorem/lemma), so nothing in variant_scope is disturbed. If it
# FAILS => the frozen postcondition is not satisfiable at a concrete input of
# the very shape the task's tests exercise, i.e. a SPEC DEFECT, not a port bug.
_ADM_INPUT = '[("f", 1, "u1"), ("f", 1, "u2"), ("f", 2, "u3"), ("g", 1, "u4")]'
_ADM_ANCHOR = "  intro triples\n  rw [loop_eq_map]\n"
_ADM_GROUND = (
    f"  have _ground : problem_spec_dedupSort\n"
    f"      {_ADM_INPUT}\n"
    f"      (implementation_dedupSort {_ADM_INPUT}) := by\n"
    f"    have hv : implementation_dedupSort {_ADM_INPUT}\n"
    f'        = [("f", 1), ("f", 2), ("g", 1)] := by\n'
    f"      simp [implementation_dedupSort, Id.run, pure, bind, List.mergeSort,\n"
    f"            List.merge, List.dedup, List.pwFilter, lexLe]\n"
    f"      decide\n"
    f"    rw [hv]\n"
    f"    refine ⟨?_, ?_⟩\n"
    f"    · simp [lexLt, List.sorted_cons]\n"
    f"      decide\n"
    f"    · intro p\n"
    f"      constructor\n"
    f"      · intro hp\n"
    f"        simp only [List.mem_cons, List.not_mem_nil, or_false] at hp\n"
    f"        rcases hp with rfl | rfl | rfl\n"
    f'        · exact ⟨"u1", by simp⟩\n'
    f'        · exact ⟨"u3", by simp⟩\n'
    f'        · exact ⟨"u4", by simp⟩\n'
    f"      · rintro ⟨u, hu⟩\n"
    f"        simp only [List.mem_cons, List.not_mem_nil, or_false,\n"
    f"          Prod.mk.injEq] at hu\n"
    f"        rcases hu with ⟨h1,h2,-⟩|⟨h1,h2,-⟩|⟨h1,h2,-⟩|⟨h1,h2,-⟩ <;>\n"
    f"          simp [Prod.ext_iff, h1, h2]\n"
)
_MOD_ADM = _swap(_BASE, _ADM_ANCHOR, _ADM_GROUND + _ADM_ANCHOR)


SPEC_TESTS = [
    {
        "id": "pos-map-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _MOD_POS,
        "rationale": (
            "structurally-different but CORRECT impl: the mutable accumulator loop "
            "that projects each occurrence to its (source, line) is replaced by the "
            "equivalent `List.map` projection, producing the identical list before "
            "the shared dedup+sort — a pure control-flow reshape. The map form is "
            "definitionally the RHS of the frozen `loop_eq_map` bridge lemma, so the "
            "only proof edit collapses that lemma's body to `rfl`; the "
            "`theorem correct_dedupSort` STATEMENT is byte-identical and no new "
            "declaration, axiom, or assumption token is introduced. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-sort-then-dedup",
        "kind": "soundness",
        "expect": "verify",
        "module": _MOD_POS2,
        "rationale": (
            "structurally-different but CORRECT impl, with a NON-definitional "
            "reproof: the two post-processing stages are COMMUTED, computing "
            "`(sort …).dedup` instead of gold's `(dedup …).sort`. Both produce "
            "the distinct positions in ascending order, but the equality is not "
            "definitional and neither frozen clause lemma applies as written, so "
            "the proof is genuinely redone: sortedness now follows from `dedup` "
            "being a SUBLIST of a sorted list, and repeat-freeness from the "
            "outer `dedup` directly instead of being transported across the "
            "mergeSort permutation. This is the soundness control that "
            "`pos-map-fold` cannot be: that case's reproof collapses to `rfl`, "
            "so it probes a different control flow but not a different "
            "post-processing pipeline. The `theorem correct_dedupSort` STATEMENT "
            "is byte-identical and no new declaration, axiom, or assumption "
            "token is introduced. If it FAILS => SPEC-TOO-STRONG (the spec would "
            "be pinning gold's particular staging rather than the result)."
        ),
    },
    {
        "id": "weak-verbatim-projection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_VERBATIM_IMPL),
        "refinement": (
            "this IS the pre-patch behaviour: the projected (source, line) positions "
            "are emitted in scan order with NEITHER deduplication NOR ordering. Its "
            "faithful real counterpart is the unchanged repo, which reports the raw "
            "projection — so a text recorded at several positions is shown with "
            "repeats and in encounter order rather than as the distinct positions in "
            "ascending order the FAIL_TO_PASS test now asserts. It does NOT resolve, "
            "so a verifying rival here would be a true verify-does-not-imply-resolve "
            "break."
        ),
        "rationale": (
            "REJECTED by clause (1) `List.Sorted lexLt result`: on an "
            "unsorted-but-distinct input the verbatim projection preserves the "
            "encounter order, which is not strictly ascending. At "
            'triples = [("a",2,_),("a",1,_)] the result is [("a",2),("a",1)]; the '
            "head relation lexLt (\"a\",2) (\"a\",1) requires 2 < 1 on the line "
            "tie-break, which is false, so the Sorted clause fails. Attacks the "
            "ordering content of clause (1). If it VERIFIES => SPEC-TOO-WEAK "
            "(the spec would not force ascending order)."
        ),
        "witness": _WIT_VERBATIM,
    },
    {
        "id": "weak-no-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_NODEDUP_IMPL),
        "refinement": (
            "sorts the projected positions but does NOT deduplicate — the near-miss "
            "of the verbatim rival that agrees with gold on every input whose "
            "positions are all distinct and diverges only when a position recurs. Its "
            "faithful real counterpart orders the positions but never collapses "
            "equal ones, so it reports a position recorded twice TWICE; the "
            "FAIL_TO_PASS scenario records the same (source, line) more than once "
            "and expects it listed exactly ONCE, so it does NOT resolve. Given its "
            "own witness at a DUPLICATE input (not the verbatim rival's unsorted "
            "input), so the "
            "no-repeats sub-domain it is claimed to violate is actually demonstrated."
        ),
        "rationale": (
            "REJECTED by clause (1) `List.Sorted lexLt result`: `lexLt` is STRICT, so "
            "a repeated position makes the result non-strictly-ascending. At "
            'triples = [("a",1,_),("a",1,_)] the sorted-without-dedup result is '
            '[("a",1),("a",1)]; the head relation lexLt ("a",1) ("a",1) requires '
            "1 < 1, which is false, so the Sorted clause fails. Attacks the "
            "no-repeats (dedup) content of clause (1), distinct from the ordering "
            "sub-domain the verbatim rival attacks. If it VERIFIES => SPEC-TOO-WEAK "
            "(the spec would not force distinctness)."
        ),
        "witness": _WIT_NODEDUP,
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_DROPLAST_IMPL),
        "refinement": (
            "off-by-one bound: folds over every occurrence EXCEPT the final one, "
            "silently dropping the last recorded position. Its faithful real "
            "counterpart drops the final recorded occurrence, so a text seen exactly "
            "once yields an EMPTY report where the FAIL_TO_PASS single-occurrence "
            "scenario expects that one position listed. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2) `∀ p, p ∈ result ↔ ∃ u, (p.1,p.2,u) ∈ triples`: "
            'at triples = [("p",1,"x")] the sole occurrence records the position '
            '("p",1), so the ↔ forces ("p",1) ∈ result; but dropLast removes the only '
            "occurrence, the loop runs empty, and the result is []. Attacks the "
            "membership clause (2) — a distinct clause from the ordering rivals — on "
            "the recorded-but-missing sub-domain. If it VERIFIES => SPEC-TOO-WEAK "
            "(the spec would not force every recorded position to be reported)."
        ),
        "witness": _WIT_DROPLAST,
    },
    {
        "id": "weak-spurious-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_SPURIOUS_IMPL),
        "refinement": (
            "reports a position that no occurrence ever recorded: the projection "
            "is padded with a fixed extra position before the dedup/sort. Its "
            "faithful real counterpart unions the recorded positions with a "
            "constant, so every text — including one with no occurrences at all "
            "— is reported at a location that was never seen. The FAIL_TO_PASS "
            "scenario asserts the reported list EXACTLY, so a fabricated extra "
            "entry fails it. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2) `∀ p, p ∈ result ↔ ∃ u, (p.1,p.2,u) ∈ "
            "triples`, in the FORWARD direction (reported ⇒ recorded) — the "
            "half of the iff that `weak-drop-last` (recorded ⇒ reported) leaves "
            "unattacked. At triples = [] no occurrence records anything, so the "
            "↔ forces the result to be empty; but this rival still reports "
            '("z",9), and instantiating the ↔ left-to-right on it yields an '
            "occurrence in the empty list. If it VERIFIES => SPEC-TOO-WEAK (the "
            "spec would let an impl invent positions, leaving the output only "
            "lower-bounded by the input)."
        ),
        "witness": _WIT_SPURIOUS,
    },
    {
        "id": "admissibility-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _MOD_ADM,
        "rationale": (
            "ADMISSIBILITY on a total carrier: the obligation has no "
            "precondition hypothesis, so the analogue of 'the precondition is "
            "inhabited' is that the postcondition is DISCHARGEABLE BY "
            "EVALUATION at a concrete input, independently of the frozen "
            "proof's lemma chain. The impl region is byte-identical to gold "
            "and the frozen tactic script still runs verbatim; a `have` is "
            "inserted ahead of it that establishes `problem_spec_dedupSort t "
            "(implementation_dedupSort t)` at a fixed F2P-shaped "
            "t = [(\"f\",1,_),(\"f\",1,_),(\"f\",2,_),(\"g\",1,_)] — one position "
            "recorded TWICE plus two further distinct positions, the "
            "dedup-and-order interaction the task's tests exercise. The impl's "
            "value is obtained by reduction, the strict-ordering clause is "
            "decided on its adjacent comparisons, and the membership iff is "
            "checked in BOTH directions (a recording occurrence exhibited for "
            "each of the three reported positions; each of the four "
            "occurrences matched to a reported position). This is not "
            "subsumed by the soundness positives or by G-VERIFY: those all "
            "route through the same three helper lemmas, so a mutually "
            "consistent mis-statement among them would pass every one of them "
            "together, whereas this case computes the postcondition directly. "
            "If it FAILS the frozen postcondition is unsatisfiable at a "
            "concrete input of the shape under test — an over-constrained "
            "spec (a SPEC DEFECT to escalate), not a port bug."
        ),
    },
]


# No @ContractOnly axioms and no opaque callees: the projection, deduplication, and
# ordering are all modeled DEEPLY over the transparent input carrier, so the axiom
# lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
