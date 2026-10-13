# properties.py — G-PBT falsification battery for django__django-16662 (lean lane).
#
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC_TESTS case is a
# FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive reproves, the proof body — is edited), checked by
# variant_scope + the Lean verifier. Every expect="reject" case carries a refutation
# `witness`: a snippet that ELABORATES against the rival and FAILS on the frozen
# solution, so the rejection is attributable to the spec and not to a tactic script
# that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   sortImportStatements : List String → List String
#   Rearranges the statement lines that head a generated module into the canonical
#   order. The single obligation `theorem correct_sortImportStatements` quantifies
#   over the sole input binder `imports` with NO precondition hypothesis (the
#   behavior is total), and the postcondition has TWO independent top-level clauses:
#     (P) List.Perm result imports — the emitted statements are exactly the input
#         statements, none added, dropped, or duplicated. This is the frame clause:
#         it pins the CONTENT to the input carrier, so nothing may be invented.
#     (O) result.Pairwise (fun a b => importLe a b = true) — the emitted order is
#         canonical: every plain module import precedes every selective import, and
#         within each of those two groups the order is by module name. NOTE on the
#         strength of this clause, measured rather than assumed: `List.Pairwise` in
#         this workspace relates EVERY ordered pair, not merely consecutive ones
#         (checked: `List.Pairwise R [a,b,c] → R a c` elaborates, exit 0). The frozen
#         spec_view prose describes it as consecutive-and-hence-global via importLe's
#         totality/transitivity; that reaches the same place, since for a total
#         preorder consecutive-sorted and globally-sorted coincide, and the frozen
#         proof does prove both lemmas. But the clause as WRITTEN is directly the
#         all-pairs statement, so no case below leans on the transitivity step to get
#         a non-adjacent pair — each witness refutes an ADJACENT pair, which is a
#         member of the all-pairs relation either way.
#   `importLe` is GROUNDED: it is spelled out over the transparent statement text
#   (leading token / following token by whitespace split), so there is no opaque
#   answer-key oracle for a rival to echo. meta.json axioms == [] and
#   deep_model_references == [] — nothing is assumed.
#
# The FAIL_TO_PASS ordering test asserts the emitted block groups the plain module
# imports ahead of the selective import even though the selective statement's module
# token sorts lexicographically BEFORE the second plain statement's module token.
# That configuration — one selective statement whose module name sorts below a plain
# statement's — is the discriminating shape, and it is where the load-bearing rival
# below is refuted.
#
# ADVERSARIAL READ of the nagini classes on this carrier:
#
#   * FRAME / PERMISSION MUTATION (nagini cases 3 and 3b, MANDATORY there) —
#     VACUOUS. nagini holds both input carriers at half permission and makes an
#     input-writing rival mandatory, rejected by the permission system rather than
#     by a value defect. Lean is referentially transparent: `imports` is a plain
#     immutable value, there is no fractional permission to violate and no aliasing
#     to exploit, so the class has NO expressible instance here. Note the FRAME
#     INTENT does survive, but as a value obligation rather than a permission one:
#     clause (P) is the frame clause on this carrier, and it is attacked directly by
#     `weak-drop-last` and `weak-collapse-to-head`. No substitute is fabricated for
#     the permission mechanics themselves.
#
#   * PARTIAL-DOMAIN order-by-module-alone (nagini case 4, the load-bearing
#     pre-patch rival) — APPLIES, ported as `weak-module-only-order`. Refuted at the
#     mixed-kind configuration where the module order and the group order disagree.
#
#   * IDENTITY / sortedness dropped (nagini case 5) — APPLIES, ported as
#     `weak-no-order`. Refuted at a SAME-KIND pair out of module order, so it probes
#     the within-group half of clause (O) at a different input point than the
#     mixed-kind rivals.
#
#   * VALUE DROP/DUPLICATE (nagini case 6, the sorted-LOOKING output whose content
#     is wrong) — APPLIES, ported as `weak-collapse-to-head`: every emitted slot
#     carries the first statement, so the output is canonically ordered (clause O
#     holds — a statement never precedes itself improperly) while its content drops
#     the others. Exactly nagini's [min, min, max] argument on this carrier.
#
#   * CONSTANT canned output (nagini case 7, a supporting cheap near-miss) —
#     SUBSUMED, not shipped. Its lean counterpart (`return []`, or any fixed list)
#     fails clause (P) at the SAME input and for the SAME reason as
#     `weak-drop-last` (content not drawn from the carrier), so under the shared-
#     witness rule it would add a case without adding an input point or a clause.
#     SUBSUMPTION MEASURED (audit, not argued): the constant rival `return ([] :
#     List String)` was built as a variant (scope-clean, obligation byte-identical)
#     and it is REJECTED (exit 1); `weak-drop-last`'s witness, used VERBATIM and
#     unmodified against it, ELABORATES (exit 0). So the shipped witness already
#     refutes this rival at the same singleton input and via the same clause, which
#     is what "subsumed" has to mean to be a legitimate omission rather than a gap.
#     See 'assessment'.
#
#   * ADMISSIBILITY (nagini case 2) — APPLIES, and the port's original reason for
#     dropping it was WRONG. It read: "the frozen obligation has no precondition
#     hypothesis at all, so there is nothing that could be PRECOND-TOO-STRONG and
#     nothing to admit." Absence of a precondition is not absence of the lane. On a
#     total carrier the analogue of an over-strong precondition is the obligation
#     being UNSATISFIABLE at exactly an F2P-shaped input, and NONE of the three
#     soundness positives detects that: each discharges the obligation generically
#     over the universally quantified binder, which is compatible with the two
#     clauses being jointly unsatisfiable at the one configuration where the group
#     order and the module order disagree. Landed by audit as `adm-f2p-shape`,
#     which discharges the obligation at that concrete configuration — exhibiting a
#     result list that satisfies both clauses there — before closing the frozen
#     obligation verbatim. Verifies (exit 0).
#
#   * POSITIVE CONTROL / soundness (nagini case 1) — APPLIES, ported as FOUR
#     positives (see their rationales): a value-identical control-flow reshape, a
#     reshape that additionally probes that clause (O) is not over-pinned on ties,
#     and a DIFFERENT ORDERING ALGORITHM. The third exists because the first two
#     both order via `mergeSort importLe`, i.e. the frozen impl's own ordering
#     primitive: with only those two, a spec that had been over-pinned to that
#     primitive (provable only for a `mergeSort`-shaped result) would still show a
#     green verify lane. `pos-insertion-sort` orders by repeated insertion instead,
#     so nothing about `mergeSort` appears in its impl, and its proof discharges the
#     two clauses from the insertion-sort permutation/sortedness lemmas rather than
#     the merge-sort ones. It shares only the ORDER `importLe`, which is the part
#     the spec is entitled to pin. The fourth, `pos-partition-append`, was landed by
#     a later audit out of a reshape the earlier pass had recorded as an unclosable
#     UNCERTAIN; it separates the two statement kinds STRUCTURALLY (two filters and
#     an append) instead of letting the comparator do the grouping, so it is the one
#     positive that never compares a plain statement against a selective one at all.
#
#   * DIVERGENCE / NON-TERMINATION — nothing to port (the nagini sibling carries NO
#     diverge-*/nonterm-*/weak-diverge case, checked), and recorded here as a KNOWN
#     HOLE rather than as a vacuous class. A THIRD audit pass corrected this bullet,
#     which previously read: "on this backend the class is genuinely vacuous
#     regardless: `implementation_sortImportStatements` is a total Lean `def`, so a
#     diverging implementation cannot be written at all." That is FALSE and was
#     measured false: `partial def implementation_sortImportStatements (imports :
#     List String) : List String := implementation_sortImportStatements imports` is
#     scope-clean (variant_problems == [], the obligation statement byte-identical,
#     no new axiom/sorry token — `partial` is not in _ASSUMPTION_TOKENS) and it IS
#     REJECTED, exit 1. So a diverging rival can be written and the verifier does
#     turn it away. This bundle also sets NO `loom.semantics.termination` option at
#     all (it is the plain lean carrier over Mathlib, not the velvet one), so the
#     "total" disposition of that lane is the one that applies.
#     What blocks SHIPPING it is the witness, not the impl, and that was measured
#     both ways rather than argued. A `partial def` self-loop elaborates to an
#     OPAQUE constant of type `List String`: the logic knows nothing about its
#     value, and some list does satisfy both clauses at every input, so the rival is
#     not provably WRONG — merely unprovable. Two witness shapes were built against
#     it: (a) the refutation stated by evaluation (`simp
#     [implementation_sortImportStatements]`) does NOT hold of the rival (exit 1),
#     i.e. `witness-unproven`; (b) the refutation CONDITIONED on the value
#     (`(h : implementation_sortImportStatements [s] = [])`) holds of the rival
#     (exit 0) but ALSO holds of the frozen solution (exit 0), i.e.
#     `witness-vacuous`. Neither is a discriminator, and no third shape can be:
#     refuting an unknown constant requires deriving a value fact the carrier does
#     not supply. So the class is an admitted GAP in this battery — the spec does
#     not distinguish a diverging impl from a correct one by any witness this
#     carrier can state — and NOT a demonstration that the battery is complete.
#     (The velvet lane records the same class as an open SPEC HOLE under
#     partial-correctness semantics; the corpus-wide termination-semantics finding.)
#
#   * AXIOM_TESTS (nagini AXIOM lane) — DROPPED. The axiom lane is G-AX's job and
#     this gate ignores it; this bundle declares no axiom and no opaque callee.
#
# WITNESSES — why they all CONDITION on the carrier, and what that does and does
# NOT excuse. Statement lines are `String`, and the modeled token extraction goes
# through `String.splitOn`, defined by well-founded recursion: re-measured by
# audit, no LITERAL statement reduces. `firstToken "import z" = "import"` fails by
# `rfl` (1), by `decide` (1, stuck at the Decidable instance), by `decide +kernel`
# (1), and by `simp [firstToken]` (1); `moduleName`, `isFromStatement`, `importLe`
# and a literal `("a" : String) ≤ "z"` are all likewise stuck under
# `decide +kernel` (1 each), and the whole postcondition at a literal input is
# stuck under both `decide +kernel` and a fully-unfolded `simp` (1 each). Only
# `native_decide` closes any of them, and that token is banned by variant_scope.
# So no literal input decides anything, and each witness instead states its
# refutation at a point described by HYPOTHESIS on the two modeled projections
# (`isFromStatement` for the statement kind, `moduleName` for the module token) —
# strictly stronger than a single literal input, since it refutes the rival on the
# whole sub-domain where it is wrong.
#
# What that does NOT excuse, and where the audit found real defects: conditioning
# on the carrier does not mean the ordering step is irreducible. UNDER those
# hypotheses the ordering DOES evaluate on both sides — measured, and this is the
# pair that decides whether these cases are real. Claiming the frozen impl's TRUE
# output under the mixed-kind hypotheses (`= [p, q]`) ELABORATES, exit 0; claiming
# the rival's output (`= [q, p]`) at the same binders and hypotheses FAILS, exit 1,
# with the fully-reduced residual `⊢ p = q ∧ q = p`. Same pair for the same-kind
# shape (`= [b, a]` exit 0, `= [a, b]` exit 1, residual `⊢ b = a ∧ a = b`). The
# frozen-side exit code therefore TRACKS THE CLAIM here, which is the whole
# requirement — and the three ordering witnesses were rewritten by audit because
# their earlier shape did not have that property (see the witness block below).
# Each hypothesis set is jointly satisfiable by real statement lines (spelled out
# per case) and was probed for inconsistency with `example <binders> : False := by
# first | omega | simp_all | decide | (simp_all; omega)`: all five probes FAIL to
# derive False, as required. Every witness was built against its rival (must
# ELABORATE — seen to exit 0) and rebuilt against the frozen solution (must FAIL —
# seen to exit 1).
#
# AUDIT RECORD (independent re-derivation; every number below is an observed exit
# code, not an expectation). All 5 reject witnesses were rebuilt exactly as the gate
# builds them: rival 0 / gold 1 / consistency-probe 1 for every one of the five, both
# before and after the repairs below.
#
# TWO DEFECTS FOUND AND FIXED. (1) The three ORDERING witnesses passed for a
# syntactic reason. Their earlier shape performed the rival's reduction inside the
# refutation as `rw [show (<the rival's own comparator term>) = [q, p] by ...]`, and
# on the frozen side that failed with `Tactic `rewrite` failed: Did not find an
# occurrence of the pattern [p, q].mergeSort fun a b => decide (moduleName a ≤
# moduleName b)` — pattern-not-found, which is true of ANY impl not spelled that
# way, wrong or merely reshaped. `weak-no-order`'s failed as a bare `Type mismatch:
# rfl has type ?m = ?m`, same class. Rewritten to state the impl's value as a
# standalone `have` over shared vocabulary with the projections in the simp set; the
# frozen side now fails with the fully-reduced residual `⊢ p = q ∧ q = p`
# (respectively `⊢ b = a ∧ a = b`), and the claim-tracking pair confirms the exit
# code follows the claim: frozen impl's TRUE value exit 0, rival's value exit 1, same
# binders and hypotheses. (2) The ADMISSIBILITY lane was dropped for a reason that
# does not hold (see its bullet above); landed as `adm-f2p-shape`, verifies, exit 0.
#
# The gold-side failures are SEMANTIC, established two independent ways. Gold's OWN
# proven obligation instantiated at each witness's exact binders, hypotheses and
# input (`correct_sortImportStatements [p, q]` etc.) elaborates, exit 0, all five —
# so gold provably SATISFIES the spec at the very point each witness claims a
# violation. And the claim-tracking pair above shows the frozen-side exit code is not
# invariant under the claim. No gold-side failure matches the gate's stuck-reduction
# screen (checked against _STUCK_REDUCTION: no hits). Every rival was confirmed
# OBSERVABLY different from gold on its witness's own input (not a mere reshape).
# SPEC-TOO-WEAK probes (new wrong impls the battery did not contain): module order
# DESCENDING within each correct group; canonical order then de-duplicated;
# canonical order then rotated by one; ordered by the whole statement line instead of
# the module token; a fabricated statement appended; the group test spelled against a
# keyword that never matches — all six scope-clean, all six REJECTED (exit 1).
# SPEC-TOO-STRONG probes (new correct reshapes): insertion sort (now shipped as
# `pos-insertion-sort`) and a pointwise-equal if-cascade comparator proved equal to
# `importLe` by funext both VERIFY (exit 0). A third, filter-the-two-kinds-and-
# concatenate, was recorded by that pass as UNCERTAIN — a faithful correct impl
# whose proof it could not close against the frozen tail. A LATER INDEPENDENT AUDIT
# LANDED IT: the missing step was only the permutation over the append
# (`List.perm_append_comm` then `List.filter_append_perm`; the frozen tail's own
# `List.sorted_mergeSort` idiom is reused per group, and `List.pairwise_append`'s
# cross-group leg follows from the two membership facts). It VERIFIES, exit 0, and
# is now shipped as `pos-partition-append` rather than left as prose, so the
# UNCERTAIN above is retracted. No spec hole found in either direction.
#
# SECOND AUDIT PASS (independent re-derivation; every number an observed exit code).
# All five shipped reject witnesses were rebuilt exactly as the gate builds them and
# reproduce: rival 0 / gold 1 / consistency-probe 1, five for five. Every one of the
# five gold_signatures is a FULLY-REDUCED evaluation residual (`⊢ p = q ∧ q = p`,
# `⊢ b = a ∧ a = b`, `⊢ False`, `⊢ b = a`) and none matches the gate's
# stuck-reduction screens. The FORGERY pair was run for all five in BOTH directions:
# claiming the frozen impl's TRUE value at each witness's exact binders and
# hypotheses elaborates on gold (exit 0, 5/5) and FAILS on the rival (exit 1, 5/5,
# with the mirror-image residual).
#
# CORRECTION by a third audit pass, which re-ran the second direction and got a
# different number. That pass had recorded: "the FLIPPED claim — the witness with
# its `¬` dropped, i.e. asserting the frozen impl SATISFIES the spec at exactly the
# point the witness claims a violation — also elaborates on gold (exit 0, 5/5)."
# Re-measured: it does NOT. Dropping the `¬` and keeping the witness's tactic body
# fails on gold, exit 1, for all six shipped rejects — necessarily, because the body
# opens with `rintro ⟨-, hpair⟩` and there is no longer a negation to introduce
# (`Tactic 'introN' failed: There are no additional binders ... to introduce`). The
# flipped claim as spelled that way is a BROKEN TACTIC SCRIPT, not a true claim
# gold satisfies, so its exit code says nothing either way and that line was
# evidence of nothing. The claim-tracking property is instead established by the
# pair that varies ONLY the asserted VALUE while holding the tactic fixed (the
# `fpair` rows in `witnesses_rebuilt`): gold's true output claimed at the witness's
# own binders and hypotheses elaborates on gold (0) and fails on the rival (1),
# while the rival's output claimed at the same point fails on gold (1) and
# elaborates on the rival (0) — 6/6 in each of the four directions. That is what
# shows gold's exit code tracks the claim rather than the spelling. Independently,
# gold's OWN proven obligation instantiated at each witness's input
# (`correct_sortImportStatements [p, q]`, `[s]`) elaborates, exit 0, so gold
# provably SATISFIES the spec where each witness claims a violation.
# The ADMISSIBILITY case was probed for both failure modes a positive can hide:
# its hypothesis set is satisfiable (the `False` probe over its five hypotheses
# FAILS to derive False, exit 1), and its `have` is LOAD-BEARING — the same case
# with the `have` restated to claim the selective statement leads is REJECTED
# (exit 1, `⊢ False` on the `importLe q p1 = true` step), so the `have` is really
# checked rather than trivially discharged. The nagini case-7 subsumption claim was
# re-measured from scratch and reproduces exactly: the constant rival is rejected
# (exit 1) and `weak-drop-last`'s witness used VERBATIM against it elaborates
# (exit 0). Four FURTHER wrong impls were tried (full reverse of the canonical
# order; the group test spelled as `firstToken != "import"`; the canonical order
# with its first two slots transposed; the selective group left unordered) — all
# four scope-clean, all four REJECTED (exit 1). The last of those was a real
# COVERAGE GAP rather than merely another rejection, and is now shipped as
# `weak-selective-group-unordered`: the within-group half of clause (O) had been
# probed for the PLAIN group only, so no shipped rival was wrong on a pair of two
# SELECTIVE statements. Its witness carries the same evidence as the others
# (rival 0 / gold 1 / probe 1; true-value gold 0 and rival 1; flipped claim
# gold 0). Header claims spot-checked against the verifier: `List.Pairwise R
# [a,b,c] → R a c` elaborates (exit 0, so the all-pairs reading is right), and
# `firstToken "import z" = "import"` is stuck under both `rfl` and `decide +kernel`
# (exit 1 each, so the hypothesis-conditioned witness shape is necessary).
#
# THIRD AUDIT PASS (independent; every number an observed exit code, 90 builds).
# All six shipped reject witnesses rebuilt exactly as the gate builds them:
# rival 0 / gold 1 / consistency-probe 1, six for six, every gold_signature a
# fully-reduced residual (`⊢ p = q ∧ q = p`, `⊢ b = a ∧ a = b`, `⊢ False`,
# `⊢ b = a`, `⊢ r = q ∧ q = r`), none matching any of the four stuck screens
# (_STUCK_REDUCTION / _STUCK_INSTANCE / _STUCK_UNIFICATION checked programmatically
# against each gold log: no hits). The value-claim forgery pair ran in all four
# directions per case and tracks: gold's true value on gold 0 / on rival 1, the
# rival's value on gold 1 / on rival 0. The FLIPPED-claim direction was re-measured
# and the earlier pass's number retracted — see the correction above.
# Carrier claims re-checked, not inherited: `List.Pairwise R [a,b,c] → R a c`
# elaborates (0, so the all-pairs reading is right); `firstToken "import z" =
# "import"` fails under `rfl` (1), `decide +kernel` (1) and `simp [firstToken]` (1)
# and succeeds only under `native_decide` (0, banned by variant_scope); the whole
# postcondition at a literal two-statement input is stuck under a fully-unfolded
# `simp` (1). So the hypothesis-conditioned witness shape is necessary.
# The ADMISSIBILITY positive was probed for both ways it could be hollow. Its
# hypotheses are satisfiable (the `False` probe over its five binders fails to
# derive False, exit 1), and its `have` is LOAD-BEARING three ways: restating it to
# claim the selective statement LEADS is rejected (1), reversing one of the three
# `importLe` facts is rejected (1), and the wrong-order claim stated as a standalone
# example over the same hypotheses is rejected (1, `simp made no progress`).
# SPEC-TOO-WEAK probes, seven NEW wrong impls beyond the earlier passes' ten: the
# group test with both groups left unordered; emitting the module TOKENS instead of
# the statement lines; dropping the whole selective group; the canonical order with
# its head duplicated (right order, wrong content, wrong length); ordering by only
# the module token's first character; the composite key spelled as a `Prod` (the
# componentwise-vs-lexicographic trap mapping.md warns about); and a `partial def`
# self-loop. All seven scope-clean (variant_problems == []), all seven REJECTED
# (exit 1). The Prod-key rival is additionally SUBSUMED rather than merely rejected:
# `weak-module-only-order`'s witness used VERBATIM against it elaborates (exit 0),
# which is the measurement that makes it a duplicate of a shipped case and not a
# gap. Only the length probe was a real gap, and it is now shipped as
# `weak-short-input-only`.
# SPEC-TOO-STRONG probe, one NEW correct reshape: order by module token alone FIRST
# and then stably partition the two kinds (`filter (¬isFrom) ++ filter isFrom` over
# the module-sorted list) — a faithful impl that reaches the canonical order by a
# completely different route from any shipped positive, since the comparator it
# sorts with is the PRE-PATCH module-only one and the grouping is recovered
# afterwards. It VERIFIES, exit 0 (clause (P) by `perm_append_comm` /
# `filter_append_perm` over `mergeSort_perm`, clause (O) by `pairwise_append` with
# each leg from the module-sorted list's own `Pairwise` restricted along
# `filter_sublist`). No spec hole in either direction.
#
# BINDER / CLAUSE COVERAGE. ONE input binder (`imports`), TWO independent clauses,
# and all three lanes present (`soundness`, `admissibility`, `uniqueness`) after the
# audit landed `adm-f2p-shape`.
# The reject witnesses probe SEVEN distinct input points, varying the binder in every
# dimension the spec reads: LENGTH (a singleton, two-element lists, and — after the
# third audit landed `weak-short-input-only` — a three-element list), the STATEMENT
# KIND projection (both-plain, both-selective, and mixed plain/selective), and the
# MODULE-NAME projection (constrained in each direction, and left unconstrained by
# one witness so the group half of clause (O) is shown to bind regardless of module
# order). Clause (O) is attacked in BOTH of its halves and in every sub-domain each
# half has: the GROUP half by `weak-module-only-order` (group flag ignored) and
# `weak-selective-first` (group flag inverted), the WITHIN-GROUP half by
# `weak-no-order` (plain group, no ordering at all) and
# `weak-selective-group-unordered` (selective group, ordering applied to the other
# group only). Clause (P) is attacked by `weak-drop-last` (content dropped) and
# `weak-collapse-to-head` (content dropped AND duplicated behind a
# canonically-ordered output). Both clauses are attacked; the sole binder is
# exercised at seven distinct shapes.
#
# THE LENGTH DIMENSION was a real gap until the third audit, and it is worth naming
# why the earlier passes' "six distinct input points" claim did not catch it. Those
# six points varied the KIND and MODULE projections thoroughly but were all of
# length <= 2 (five at two statements, `weak-drop-last` at one), so nothing in the
# battery was wrong only at longer inputs — while the configuration this behavior
# exists to get right has THREE statements. A spec whose ordering clause bound only
# short collections would have shown a fully green reject lane, and the rival that
# demonstrates this (`weak-short-input-only`) is scope-clean and IS rejected, with
# its witness discriminating (rival 0 / gold 1 / probe 1, and the value-claim pair
# tracking in all four directions).
from pathlib import Path

INSTANCE = "django__django-16662"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it edits and is unique in the
# file, so the manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

# The whole gold impl body (impl-start .. impl-end):
_IMPL_GOLD = (
    "def implementation_sortImportStatements (imports : List String) : List String :=\n"
    "  Id.run do\n"
    "    let mut sortedStatements := imports\n"
    "    sortedStatements := sortedStatements.mergeSort importLe\n"
    "    return sortedStatements"
)
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"

# The ordering step alone, unique inside the impl region:
_ORDER_GOLD = "    sortedStatements := sortedStatements.mergeSort importLe"
assert _BASE.count(_ORDER_GOLD) == 1, "ordering-step anchor drifted"

# The final `return` line, unique inside the impl region:
_RET_GOLD = "    return sortedStatements"
assert _BASE.count(_RET_GOLD) == 1, "return anchor drifted"

# The tail of the frozen obligation's tactic body (inside proof-start..proof-end).
# Only the two positives touch this; the theorem STATEMENT is never edited.
_PROOF_TAIL = (
    "  refine ⟨List.mergeSort_perm imports importLe, ?_⟩\n"
    "  exact List.sorted_mergeSort\n"
    "    (fun a b c => by simpa using importLe_trans a b c)\n"
    "    (fun a b => by simpa using importLe_total a b)\n"
    "    imports"
)
assert _BASE.count(_PROOF_TAIL) == 1, "proof-tail anchor drifted"

# The `Id.run` normalization step of the frozen proof, unique in the file:
_PROOF_IDRUN = "  simp only [Id.run, pure]\n"
assert _BASE.count(_PROOF_IDRUN) == 1, "Id.run proof-step anchor drifted"


def _mod_impl(new_impl):
    """_BASE with ONLY the impl region replaced (proof body untouched)."""
    return _swap(_BASE, _IMPL_GOLD, new_impl)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-direct-order: drop the mutable-accumulator scaffolding and apply the
# canonical ordering directly. VALUE-IDENTICAL to the frozen impl on every input
# (the accumulator is assigned once and returned), a pure control-flow reshape.
# The only proof edit is deleting the now-inapplicable `Id.run` normalization
# step; the `theorem correct_sortImportStatements` STATEMENT is byte-identical and
# no new declaration, axiom, or assumption token appears.
_POS_DIRECT_IMPL = (
    "def implementation_sortImportStatements (imports : List String) : List String :=\n"
    "  imports.mergeSort importLe"
)
_MOD_POS_DIRECT = _swap(_swap(_BASE, _IMPL_GOLD, _POS_DIRECT_IMPL),
                        _PROOF_IDRUN, "")

# pos-order-reversed-scan: visit the input statements in the opposite scan order
# before applying the same canonical ordering. Faithful: the input carrier is an
# UNORDERED collection of statements (mapping.md), so any implementation whose
# output depends only on the multiset of statements is a correct implementation of
# the modeled behavior — and reversing preserves the multiset exactly. Its value
# differs from the frozen impl ONLY on an input holding two DISTINCT statements
# with the same kind and the same module name, i.e. precisely where the canonical
# order leaves the tie free; so this positive additionally probes that clause (O)
# is not over-pinned. Reproved by composing the permutation with reversal's; the
# obligation STATEMENT is byte-identical.
_POS_REVERSED_IMPL = (
    "def implementation_sortImportStatements (imports : List String) : List String :=\n"
    "  Id.run do\n"
    "    let mut sortedStatements := imports.reverse\n"
    "    sortedStatements := sortedStatements.mergeSort importLe\n"
    "    return sortedStatements"
)
_POS_REVERSED_PROOF = (
    "  refine ⟨(List.mergeSort_perm imports.reverse importLe).trans\n"
    "    (List.reverse_perm imports), ?_⟩\n"
    "  exact List.sorted_mergeSort\n"
    "    (fun a b c => by simpa using importLe_trans a b c)\n"
    "    (fun a b => by simpa using importLe_total a b)\n"
    "    imports.reverse"
)
_MOD_POS_REVERSED = _swap(_swap(_BASE, _IMPL_GOLD, _POS_REVERSED_IMPL),
                          _PROOF_TAIL, _POS_REVERSED_PROOF)

# pos-insertion-sort: a DIFFERENT ORDERING ALGORITHM under the same order.
# Added by audit: the two positives above both order via `mergeSort importLe`, the
# frozen impl's own primitive, so neither can distinguish "the spec pins the
# canonical ORDER" from "the spec is only provable for a mergeSort-shaped result".
# This one builds the result by repeated insertion — `mergeSort` does not appear in
# its impl at all — and discharges clause (P) from insertion sort's permutation
# lemma and clause (O) from its sortedness lemma, supplying the transitivity and
# totality of `importLe` as the instances those lemmas require (both already proved
# in the frozen proof region, reused, not restated). The `theorem
# correct_sortImportStatements` STATEMENT is byte-identical and no new declaration,
# axiom, or assumption token appears.
_POS_INSERTION_IMPL = (
    "def implementation_sortImportStatements (imports : List String) : List String :=\n"
    "  imports.insertionSort (fun a b => importLe a b = true)"
)
_POS_INSERTION_PROOF = (
    "  haveI htr : IsTrans String (fun a b => importLe a b = true) :=\n"
    "    ⟨fun a b c h1 h2 => importLe_trans a b c h1 h2⟩\n"
    "  haveI hto : IsTotal String (fun a b => importLe a b = true) :=\n"
    "    ⟨fun a b => by have h := importLe_total a b; simpa using h⟩\n"
    "  refine ⟨List.perm_insertionSort _ imports, ?_⟩\n"
    "  exact List.sorted_insertionSort (fun a b => importLe a b = true) imports"
)
_MOD_POS_INSERTION = _swap(
    _swap(_swap(_BASE, _IMPL_GOLD, _POS_INSERTION_IMPL),
          _PROOF_TAIL, _POS_INSERTION_PROOF),
    _PROOF_IDRUN, "")


# adm-f2p-shape: the ADMISSIBILITY positive, added by audit. The port dropped
# this lane on the ground that the frozen obligation carries no precondition, so
# nothing could be PRECOND-TOO-STRONG. That reason is not sufficient: on a total
# carrier the analogue of an over-strong precondition is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input, which no positive above tests —
# all three of them discharge the obligation generically, over the universally
# quantified binder, and would still verify if the postcondition happened to be
# contradictory at the one configuration this behavior exists to get right.
#
# So this case discharges the obligation AT that concrete configuration, as a
# `have`, BEFORE closing the frozen obligation verbatim: three statements, two
# plain module imports and one selective import whose module token sorts at or
# below the second plain statement's — i.e. precisely the shape where the group
# order and the module order DISAGREE, the configuration the ordering
# requirement is about. The `have` exhibits a witness list satisfying BOTH
# clauses there (the identity permutation, and Pairwise discharged from the three
# pairwise `importLe` facts, each proved from the modeled projections), so the
# postcondition is demonstrably inhabited at that input rather than merely
# non-contradictory. The frozen impl and the frozen proof tail are then kept
# verbatim; the obligation STATEMENT is byte-identical and no new
# declaration/axiom/assumption token appears. If it FAILS => the spec is
# unsatisfiable at the discriminating input (the total-carrier analogue of
# PRECOND-TOO-STRONG), which no other case in this battery would detect.
_ADM_HAVE = (
    "  have hadmissible : ∀ p1 p2 q : String,\n"
    "      isFromStatement p1 = false → isFromStatement p2 = false →\n"
    "      isFromStatement q = true →\n"
    "      moduleName p1 ≤ moduleName p2 → moduleName q ≤ moduleName p2 →\n"
    "      problem_spec_sortImportStatements [p1, p2, q] [p1, p2, q] := by\n"
    "    intro p1 p2 q h1 h2 hq h12 hq2\n"
    "    refine ⟨List.Perm.refl _, ?_⟩\n"
    "    have e12 : importLe p1 p2 = true := by simp [importLe, h1, h2, h12]\n"
    "    have e1q : importLe p1 q = true := by simp [importLe, h1, hq]\n"
    "    have e2q : importLe p2 q = true := by simp [importLe, h2, hq]\n"
    "    simp [List.pairwise_cons, e12, e1q, e2q]\n"
)
_MOD_ADM = _swap(_BASE, _PROOF_TAIL, _ADM_HAVE + _PROOF_TAIL)


# pos-partition-append: order each of the two statement KINDS separately and
# concatenate, rather than applying one ordering to the whole collection. Added
# by a later audit, which also corrected the record: an earlier audit pass had
# recorded this reshape as UNCERTAIN — "a faithful correct impl whose proof the
# audit could NOT close against the frozen tail (`simp made no progress`)" — and
# that is no longer true. The proof DOES close (exit 0, measured); what the
# earlier attempt lacked was the `Perm` composition over the append, which is
# `List.perm_append_comm` followed by `List.filter_append_perm` (the frozen tail's
# own `List.sorted_mergeSort` idiom, including the transitivity/totality
# arguments, is reused verbatim for each group, and the cross-group leg of
# `List.pairwise_append` is discharged from the two membership facts). Recording
# it as an unlanded proof was therefore understating the verify lane by one real
# reshape, so it is shipped rather than left as prose.
#
# What it adds over the other three positives: they all produce their result by
# ONE ordering pass over the whole statement collection. This one never compares
# a plain statement with a selective one at all — the grouping is structural (two
# filters and an append) rather than a consequence of the comparator — so it is
# the only positive that would still be a faithful impl if `importLe`'s first two
# match arms were unreachable. The obligation STATEMENT is byte-identical and no
# new declaration/axiom/assumption token appears.
_POS_PARTITION_IMPL = (
    "def implementation_sortImportStatements (imports : List String) : List String :=\n"
    "  (imports.filter (fun l => !isFromStatement l)).mergeSort importLe\n"
    "    ++ (imports.filter (fun l => isFromStatement l)).mergeSort importLe")
_POS_PARTITION_PROOF = (
    "  refine ⟨?_, ?_⟩\n"
    "  · refine ((List.mergeSort_perm (imports.filter (fun l => !isFromStatement l))"
    " importLe).append\n"
    "      (List.mergeSort_perm (imports.filter (fun l => isFromStatement l))"
    " importLe)).trans ?_\n"
    "    exact List.perm_append_comm.trans\n"
    "      (List.filter_append_perm (fun l => isFromStatement l) imports)\n"
    "  · rw [List.pairwise_append]\n"
    "    refine ⟨List.sorted_mergeSort\n"
    "        (fun a b c => by simpa using importLe_trans a b c)\n"
    "        (fun a b => by simpa using importLe_total a b) _,\n"
    "      List.sorted_mergeSort\n"
    "        (fun a b c => by simpa using importLe_trans a b c)\n"
    "        (fun a b => by simpa using importLe_total a b) _, ?_⟩\n"
    "    intro a ha c hc\n"
    "    have ha' := (List.mergeSort_perm _ importLe).mem_iff.mp ha\n"
    "    have hc' := (List.mergeSort_perm _ importLe).mem_iff.mp hc\n"
    "    have hafalse : isFromStatement a = false := by\n"
    "      simpa using (List.mem_filter.mp ha').2\n"
    "    have hctrue : isFromStatement c = true := by\n"
    "      simpa using (List.mem_filter.mp hc').2\n"
    "    simp [importLe, hafalse, hctrue]")
_MOD_POS_PARTITION = _swap(
    _swap(_swap(_BASE, _IMPL_GOLD, _POS_PARTITION_IMPL),
          _PROOF_TAIL, _POS_PARTITION_PROOF),
    _PROOF_IDRUN, "")


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly, edits ONLY the impl region, and carries a witness.
# ---------------------------------------------------------------------------

# weak-module-only-order: order by MODULE NAME ALONE, ignoring which of the two
# statement kinds a line is. This is the pre-patch behavior.
_MODULE_ONLY_IMPL = _IMPL_GOLD.replace(
    _ORDER_GOLD,
    "    sortedStatements := sortedStatements.mergeSort "
    "(fun a b => decide (moduleName a ≤ moduleName b))")

# weak-no-order: emit the statements in scan order with no ordering applied.
_NO_ORDER_IMPL = _IMPL_GOLD.replace(_ORDER_GOLD + "\n", "")

# weak-selective-first: group the two statement kinds the wrong way round —
# selective imports ahead of plain module imports — keeping the module-name order
# within each group. The near-miss of the module-only rival: wrong on EVERY
# mixed-kind pair, whereas the module-only rival is wrong only on the mixed-kind
# pairs where the module order disagrees with the group order.
_SELECTIVE_FIRST_IMPL = _IMPL_GOLD.replace(
    _ORDER_GOLD,
    "    sortedStatements := sortedStatements.mergeSort (fun a b =>\n"
    "      match isFromStatement a, isFromStatement b with\n"
    "      | true,  false => true\n"
    "      | false, true  => false\n"
    "      | _,     _     => decide (moduleName a ≤ moduleName b))")

# weak-selective-group-unordered: get the GROUPING right and order the plain
# module imports correctly, but leave the SELECTIVE group in collection order.
# Added by a later audit, which found the within-group half of clause (O) probed
# in one group only: `weak-no-order` refutes at two PLAIN statements, and every
# other rival is refuted at a MIXED pair, so nothing in the shipped battery was
# wrong on a pair of two SELECTIVE statements. A spec that constrained the module
# order inside the plain group but not inside the selective group would have
# shown a fully green reject lane. This rival is correct everywhere except there,
# so its witness is refuted at exactly that pair and nowhere else.
_SELECTIVE_GROUP_UNORDERED_IMPL = _IMPL_GOLD.replace(
    _ORDER_GOLD,
    "    sortedStatements := (sortedStatements.filter "
    "(fun l => !isFromStatement l)).mergeSort importLe\n"
    "      ++ sortedStatements.filter (fun l => isFromStatement l)")

# weak-short-input-only: order correctly on inputs of two statements or fewer and
# hand anything LONGER through in collection order. Added by a third audit, which
# found every shipped rival wrong only at inputs of length <= 2 (five at two
# statements, one at a singleton), so a spec whose ordering clause bound only short
# lists would have shown a fully green reject lane. This rival is correct on every
# input the rest of the battery probes and wrong only at length >= 3 — which is
# also the length the discriminating real configuration actually has (two plain
# statements and one selective one).
_SHORT_INPUT_ONLY_IMPL = _IMPL_GOLD.replace(
    _ORDER_GOLD,
    "    sortedStatements := if sortedStatements.length ≤ 2 then\n"
    "        sortedStatements.mergeSort importLe else sortedStatements")

# weak-drop-last: canonically order the statements, then silently drop the final
# one.
_DROP_LAST_IMPL = _IMPL_GOLD.replace(_RET_GOLD,
                                     "    return sortedStatements.dropLast")

# weak-collapse-to-head: emit the right NUMBER of statements, canonically ordered
# (every slot carries the same line, so no line improperly precedes another), but
# every slot holds the FIRST statement — the others are dropped and that one is
# duplicated. The sorted-LOOKING output whose content is wrong.
_COLLAPSE_HEAD_IMPL = _IMPL_GOLD.replace(
    _RET_GOLD,
    '    return sortedStatements.map (fun _ => sortedStatements.headD "")')


# --- witnesses -------------------------------------------------------------
# Each conditions on the two modeled projections at a two-element (or singleton)
# input, reduces the rival's ordering step to a concrete list, and then refutes
# the clause named in the case's rationale.
#
# WITNESS SHAPE, corrected by audit — the three ordering witnesses below were
# REWRITTEN, and the reason is the whole substance of what this lane attests. The
# earlier shape performed the rival's reduction INSIDE the refutation, as a
# `rw [show (<the rival's own mergeSort term>) = [q, p] by ...] at hpair`. That
# elaborates against the rival and fails against the frozen solution, so it
# passed the gate — but it failed on the frozen side with
#   `Tactic `rewrite` failed: Did not find an occurrence of the pattern
#    [p, q].mergeSort fun a b => decide (moduleName a ≤ moduleName b)`
# i.e. because the rival's comparator term is not SYNTACTICALLY present in the
# frozen goal, which is true of any reshaped impl whatever its values. A rewrite
# whose pattern names the rival's own syntax cannot discriminate a WRONG rival
# from a merely differently-spelled correct one, so that exit code attested to a
# tactic mismatch and not to the spec. Same defect in `_WIT_NO_ORDER`, whose
# `... = [a, b] from rfl` step failed on the frozen side as a bare
# `Type mismatch: rfl has type ?m = ?m`.
#
# The corrected shape states the impl's value as a STANDALONE `have himpl :
# implementation_sortImportStatements [..] = [..]`, named over the shared
# vocabulary only, with the modeled projections (`importLe` and the kind
# hypotheses) in the simp set so the ordering step actually EVALUATES on both
# sides. Measured, and this is the pair that makes the case real: the same `have`
# reduces fully against the frozen solution and leaves the residual equation
# `⊢ p = q ∧ q = p` (a refutation PERFORMED — the frozen output is the other
# list, so the claim is false of it unless the two statements coincide), while
# claiming the frozen solution's TRUE value at the same binders and hypotheses
# ELABORATES, exit 0. So the frozen-side exit code now tracks the CLAIM: it is 0
# for a true claim about that impl and 1 for a false one. The earlier shape's
# error was invariant under the claim.

# Clause (O), mixed-kind sub-domain where the module order disagrees with the
# group order: `p` is a plain module import, `q` a selective one, and `q`'s module
# token sorts strictly below `p`'s. Satisfiable — e.g. p = "import z",
# q = "from a import x, y".
_WIT_MODULE_ONLY = """example (p q : String)
    (hp : isFromStatement p = false) (hq : isFromStatement q = true)
    (hm : ¬ (moduleName p ≤ moduleName q)) :
    ¬ problem_spec_sortImportStatements [p, q]
      (implementation_sortImportStatements [p, q]) := by
  have hd : ¬ ((moduleName p).data ≤ (moduleName q).data) := by simpa using hm
  have himpl : implementation_sortImportStatements [p, q] = [q, p] := by
    simp [implementation_sortImportStatements, Id.run, pure, List.mergeSort,
      importLe, hp, hq, hd]
  rintro ⟨-, hpair⟩
  rw [himpl, List.pairwise_cons] at hpair
  have h := hpair.1 p (by simp)
  simp [importLe, hp, hq] at h"""

# Clause (O), SAME-kind sub-domain: two plain module imports whose module tokens
# are in the wrong relative order. Satisfiable — e.g. a = "import z",
# b = "import a".
_WIT_NO_ORDER = """example (a b : String)
    (ha : isFromStatement a = false) (hb : isFromStatement b = false)
    (hm : ¬ (moduleName a ≤ moduleName b)) :
    ¬ problem_spec_sortImportStatements [a, b]
      (implementation_sortImportStatements [a, b]) := by
  have hd : ¬ ((moduleName a).data ≤ (moduleName b).data) := by simpa using hm
  have himpl : implementation_sortImportStatements [a, b] = [a, b] := by
    simp [implementation_sortImportStatements, Id.run, pure, List.mergeSort,
      importLe, ha, hb, hd]
  rintro ⟨-, hpair⟩
  rw [himpl, List.pairwise_cons] at hpair
  have h := hpair.1 b (by simp)
  simp [importLe, ha, hb, hm] at h"""

# Clause (O), group sub-domain with NO assumption on the module tokens at all —
# the group ordering must hold however the module names compare. Satisfiable —
# e.g. p = "import a", q = "from b import x, y".
_WIT_SELECTIVE_FIRST = """example (p q : String)
    (hp : isFromStatement p = false) (hq : isFromStatement q = true) :
    ¬ problem_spec_sortImportStatements [p, q]
      (implementation_sortImportStatements [p, q]) := by
  have himpl : implementation_sortImportStatements [p, q] = [q, p] := by
    simp [implementation_sortImportStatements, Id.run, pure, List.mergeSort,
      importLe, hp, hq]
  rintro ⟨-, hpair⟩
  rw [himpl, List.pairwise_cons] at hpair
  have h := hpair.1 p (by simp)
  simp [importLe, hp, hq] at h"""

# Clause (O), the WITHIN-SELECTIVE-GROUP sub-domain: two SELECTIVE imports whose
# module tokens are in the wrong relative order. The one sub-domain no other
# witness reaches — every other reject case is refuted at a mixed pair or at a
# pair of two PLAIN statements. Same corrected shape as the other ordering
# witnesses (standalone `have` over shared vocabulary, so the ordering step
# evaluates on BOTH sides). Satisfiable — e.g. q1 = "from z import x",
# q2 = "from a import y".
_WIT_SELECTIVE_GROUP = """example (q1 q2 : String)
    (h1 : isFromStatement q1 = true) (h2 : isFromStatement q2 = true)
    (hm : ¬ (moduleName q1 ≤ moduleName q2)) :
    ¬ problem_spec_sortImportStatements [q1, q2]
      (implementation_sortImportStatements [q1, q2]) := by
  have hd : ¬ ((moduleName q1).data ≤ (moduleName q2).data) := by simpa using hm
  have himpl : implementation_sortImportStatements [q1, q2] = [q1, q2] := by
    simp [implementation_sortImportStatements, Id.run, pure, List.mergeSort,
      importLe, h1, h2, hd]
  rintro ⟨-, hpair⟩
  rw [himpl, List.pairwise_cons] at hpair
  have h := hpair.1 q2 (by simp)
  simp [importLe, h1, h2, hm] at h"""

# Clause (O), the LENGTH sub-domain: three statements, where the rival applies no
# ordering at all. `p` and `r` are plain module imports with p's module token at or
# below r's, and `q` is a selective import sitting BETWEEN them in collection order
# — so the refuted adjacent pair is (q, r), a selective statement ahead of a plain
# one, which `importLe`'s second match arm forbids whatever the module names are.
# The hypotheses pin gold's output completely too (`= [p, r, q]`), which is what
# makes the frozen side reduce and fail on the residual rather than get stuck.
# Satisfiable — e.g. p = "import a", q = "from b import x", r = "import c".
_WIT_SHORT_INPUT = """example (p q r : String)
    (hp : isFromStatement p = false) (hq : isFromStatement q = true)
    (hr : isFromStatement r = false) (hm : moduleName p ≤ moduleName r) :
    ¬ problem_spec_sortImportStatements [p, q, r]
      (implementation_sortImportStatements [p, q, r]) := by
  have hd : (moduleName p).data ≤ (moduleName r).data := by simpa using hm
  have himpl : implementation_sortImportStatements [p, q, r] = [p, q, r] := by
    simp [implementation_sortImportStatements, Id.run, pure, List.mergeSort,
      importLe, hp, hq, hr, hd]
  rintro ⟨-, hpair⟩
  rw [himpl, List.pairwise_cons, List.pairwise_cons] at hpair
  have h := hpair.2.1 r (by simp)
  simp [importLe, hq, hr] at h"""

# Clause (P), content-dropped sub-domain: a single statement must still be
# emitted. One unconstrained binder, trivially satisfiable.
_WIT_DROP_LAST = """example (s : String) :
    ¬ problem_spec_sortImportStatements [s]
      (implementation_sortImportStatements [s]) := by
  rintro ⟨hperm, -⟩
  rw [show implementation_sortImportStatements [s] = ([] : List String) by
      simp [implementation_sortImportStatements, Id.run, pure]] at hperm
  simp at hperm"""

# Clause (P), content-duplicated sub-domain behind a canonically-ordered output:
# two DISTINCT plain module imports already in module order, so the rival's output
# is ordered (clause O holds) yet the second statement is missing. Satisfiable —
# e.g. a = "import a", b = "import z".
_WIT_COLLAPSE_HEAD = """example (a b : String) (hne : a ≠ b)
    (ha : isFromStatement a = false) (hb : isFromStatement b = false)
    (hm : moduleName a ≤ moduleName b) :
    ¬ problem_spec_sortImportStatements [a, b]
      (implementation_sortImportStatements [a, b]) := by
  have hd : (moduleName a).data ≤ (moduleName b).data := by simpa using hm
  have hs : [a, b].mergeSort importLe = [a, b] := by
    simp [List.mergeSort, importLe, ha, hb, hd]
  rintro ⟨hperm, -⟩
  rw [show implementation_sortImportStatements [a, b] = [a, a] by
      simp [implementation_sortImportStatements, Id.run, pure, hs]] at hperm
  have hmem := hperm.mem_iff.mpr (by simp : b ∈ [a, b])
  simp [hne.symm] at hmem"""


SPEC_TESTS = [
    {
        "id": "pos-direct-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _MOD_POS_DIRECT,
        "rationale": (
            "structurally-different but CORRECT impl: the mutable-accumulator "
            "scaffolding is dropped and the canonical ordering is applied directly "
            "to the input statements. VALUE-IDENTICAL to the frozen impl on every "
            "input (the accumulator is assigned once and returned), so it must "
            "satisfy both clause (P) List.Perm result imports and clause (O) "
            "result.Pairwise importLe. The only proof edit deletes the "
            "now-inapplicable `Id.run` normalization step; the "
            "`theorem correct_sortImportStatements` STATEMENT is byte-identical and "
            "no new declaration, axiom, or assumption token is introduced. If it "
            "FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-order-reversed-scan",
        "kind": "soundness",
        "expect": "verify",
        "module": _MOD_POS_REVERSED,
        "rationale": (
            "structurally-different but CORRECT impl: the input statements are "
            "visited in the opposite scan order before the SAME canonical ordering "
            "is applied. Faithful because the input carrier is an UNORDERED "
            "collection of statements (mapping.md), so any impl whose output depends "
            "only on the multiset of statements implements the modeled behavior — "
            "and reversal preserves the multiset exactly, keeping clause (P). Its "
            "value differs from the frozen impl ONLY on an input holding two "
            "DISTINCT statements of the same kind with the same module name, i.e. "
            "exactly where the canonical order leaves the tie free, so this also "
            "probes that clause (O) is not OVER-pinned (a spec demanding a "
            "particular tie order would reject a faithful impl). Reproved by "
            "composing the ordering's permutation with reversal's; the obligation "
            "STATEMENT is byte-identical, no new declaration/axiom/assumption. If it "
            "FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-insertion-sort",
        "kind": "soundness",
        "expect": "verify",
        "module": _MOD_POS_INSERTION,
        "rationale": (
            "structurally-different but CORRECT impl, and the only positive here "
            "that does not reuse the frozen impl's own ordering PRIMITIVE: the "
            "statements are ordered by repeated insertion rather than by merge, so "
            "`mergeSort` appears nowhere in its impl region. Faithful because "
            "insertion under the same `importLe` yields a permutation of the input "
            "that is ordered by that relation, which is exactly clauses (P) and (O); "
            "the proof discharges them from insertion sort's permutation and "
            "sortedness lemmas, supplying `importLe`'s transitivity and totality — "
            "both already proved in the frozen proof region — as the instances those "
            "lemmas require. Added by audit to close a real gap in the verify lane: "
            "with only the two mergeSort-based positives, a spec that happened to be "
            "provable ONLY for a mergeSort-shaped result would still have shown a "
            "green verify lane, so neither positive could distinguish 'the spec pins "
            "the canonical ORDER' from 'the spec pins the frozen ALGORITHM'. This one "
            "shares only the order. The obligation STATEMENT is byte-identical and no "
            "new declaration/axiom/assumption is introduced. If it FAILS => "
            "SPEC-TOO-STRONG (the spec would be pinned to the frozen algorithm rather "
            "than to the behavior)."
        ),
    },
    {
        "id": "pos-partition-append",
        "kind": "soundness",
        "expect": "verify",
        "module": _MOD_POS_PARTITION,
        "rationale": (
            "structurally-different but CORRECT impl: the two statement KINDS are "
            "separated first, each group is ordered on its own, and the results "
            "are concatenated — so the grouping is STRUCTURAL (two filters and an "
            "append) rather than a consequence of the comparator. Faithful "
            "because the plain-before-selective grouping and the module order "
            "within each group are exactly what the concatenation of two "
            "separately-ordered groups produces, which is clauses (P) and (O); "
            "clause (P) is discharged by composing the two groups' permutations "
            "with `List.perm_append_comm` and `List.filter_append_perm`, and "
            "clause (O) by `List.pairwise_append`, whose cross-group leg follows "
            "from the two membership facts and the modeled kind projection. "
            "Added by a later audit, which ALSO corrected the record: an earlier "
            "pass had recorded this reshape as an UNCERTAIN — a correct impl "
            "whose proof it could not close — and that understated the verify "
            "lane, since the proof does close once the append's permutation is "
            "composed the right way round. It is the only positive here that "
            "never compares a plain statement against a selective one, so it is "
            "the only one that would remain faithful if `importLe`'s two "
            "group arms were unreachable. The obligation STATEMENT is "
            "byte-identical and no new declaration/axiom/assumption appears. If "
            "it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "adm-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _MOD_ADM,
        "rationale": (
            "ADMISSIBILITY: the obligation is discharged AT the discriminating "
            "configuration, not merely generically. The frozen obligation "
            "quantifies over `imports` with no precondition, so there is no "
            "hypothesis that could be over-strong — but the total-carrier "
            "analogue of PRECOND-TOO-STRONG is the postcondition being "
            "UNSATISFIABLE at an F2P-shaped input, and no other case here tests "
            "that: the three soundness positives all discharge the obligation "
            "over the universally quantified binder and would verify even if the "
            "two clauses were jointly unsatisfiable at the one configuration this "
            "behavior exists to get right. This case adds a `have` that exhibits, "
            "for three statements — two plain module imports and one selective "
            "import whose module token sorts at or below the second plain "
            "statement's, i.e. exactly where the GROUP order and the MODULE order "
            "disagree — a concrete result list satisfying BOTH clause (P) (the "
            "identity permutation) and clause (O) (Pairwise, discharged from the "
            "three pairwise `importLe` facts proved from the modeled "
            "projections). The frozen impl and proof tail are then kept verbatim, "
            "so the obligation is still closed as frozen; the STATEMENT is "
            "byte-identical and no new declaration/axiom/assumption appears. If it "
            "FAILS => the spec cannot be satisfied at the discriminating input."
        ),
    },
    {
        "id": "weak-module-only-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_MODULE_ONLY_IMPL),
        "refinement": (
            "this IS the pre-patch behaviour: the statements are ordered by module "
            "name alone, with no regard for which of the two statement kinds each "
            "line is. Its faithful real counterpart is the unchanged repo, which is "
            "what the FAIL_TO_PASS ordering test was added to reject: on the "
            "discriminating configuration a selective import whose module token "
            "sorts low is emitted BETWEEN two plain module imports, so the asserted "
            "block (all plain module imports first, then the selective one) is not "
            "produced. Solution_prepatch.lean carries exactly this impl and fails "
            "G-VERIFY. It does NOT resolve, so a verifying rival here would be a "
            "true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (O) `result.Pairwise (fun a b => importLe a b = "
            "true)`. Refuted on the sub-domain where the module order disagrees with "
            "the group order: `imports = [p, q]` with p a plain module import, q a "
            "selective import, and q's module token strictly below p's. Ordering by "
            "module name alone then emits [q, p], and the head relation "
            "`importLe q p` is FALSE by importLe's second match arm (a selective "
            "import never precedes a plain one) whatever the module names are. "
            "Attacks the GROUP half of clause (O) — the discriminating clause "
            "(G-DIFF). If it VERIFIES => SPEC-TOO-WEAK (the spec would not force "
            "the two statement kinds to be grouped)."
        ),
        "witness": _WIT_MODULE_ONLY,
    },
    {
        "id": "weak-no-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_NO_ORDER_IMPL),
        "refinement": (
            "drops the ordering entirely and emits the statements in whatever order "
            "they were collected. Its faithful real counterpart hands the collected "
            "statements straight through; since they are gathered into an UNORDERED "
            "collection, the emitted block is in an arbitrary order and the "
            "FAIL_TO_PASS ordering test's asserted block is not guaranteed at all. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (O) `result.Pairwise (fun a b => importLe a b = "
            "true)`, on the SAME-KIND sub-domain: `imports = [a, b]` with both a and "
            "b plain module imports and a's module token NOT ≤ b's. The unordered "
            "output is [a, b] verbatim, and the head relation `importLe a b` falls "
            "to importLe's third match arm, which demands `moduleName a ≤ moduleName "
            "b` — false by hypothesis. Attacks the WITHIN-GROUP (module-name) half "
            "of clause (O), at a different input point from the mixed-kind rivals. "
            "If it VERIFIES => SPEC-TOO-WEAK (the spec would not force any ordering "
            "within a group)."
        ),
        "witness": _WIT_NO_ORDER,
    },
    {
        "id": "weak-selective-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_SELECTIVE_FIRST_IMPL),
        "refinement": (
            "groups the two statement kinds the WRONG way round — selective imports "
            "ahead of plain module imports — while keeping the module-name order "
            "within each group. Its faithful real counterpart is an inverted group "
            "key, which emits the selective statement FIRST and so contradicts the "
            "FAIL_TO_PASS ordering test just as the unchanged repo does (the test "
            "asserts the plain module imports lead the block). It does NOT resolve. "
            "This is the NEAR-MISS of weak-module-only-order and is given its own "
            "witness accordingly: it is wrong on EVERY mixed-kind input, whereas the "
            "module-only rival is wrong only on those mixed-kind inputs where the "
            "module order happens to disagree with the group order — so this "
            "witness assumes NOTHING about the module tokens, demonstrating the "
            "wider sub-domain its rationale claims."
        ),
        "rationale": (
            "REJECTED by clause (O) `result.Pairwise (fun a b => importLe a b = "
            "true)`. Refuted at `imports = [p, q]` with p a plain module import and q "
            "a selective one and NO hypothesis on either module token: the inverted "
            "grouping emits [q, p], and `importLe q p` is false by importLe's second "
            "match arm regardless of the module names. Attacks the group half of "
            "clause (O) in its purest form — the group flag is inverted rather than "
            "ignored. If it VERIFIES => SPEC-TOO-WEAK (the spec would not fix WHICH "
            "kind leads)."
        ),
        "witness": _WIT_SELECTIVE_FIRST,
    },
    {
        "id": "weak-selective-group-unordered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_SELECTIVE_GROUP_UNORDERED_IMPL),
        "refinement": (
            "gets the GROUPING right — plain module imports ahead of selective "
            "imports — and orders the plain group by module name, but hands the "
            "selective group through in collection order. Its faithful real "
            "counterpart applies the ordering to only one of the two groups. "
            "Since the statements are gathered into an UNORDERED collection, the "
            "selective statements are emitted in an arbitrary order, so the "
            "asserted block is not guaranteed whenever two or more selective "
            "statements are present; it does NOT resolve. Added by a later audit "
            "to close a coverage gap the shipped battery had: the within-group "
            "half of clause (O) was probed for the PLAIN group only "
            "(`weak-no-order` is refuted at two plain statements) while every "
            "other rival is refuted at a MIXED pair, so no shipped rival was "
            "wrong on a pair of two SELECTIVE statements."
        ),
        "rationale": (
            "REJECTED by clause (O) `result.Pairwise (fun a b => importLe a b = "
            "true)`, on the WITHIN-SELECTIVE-GROUP sub-domain: `imports = "
            "[q1, q2]` with BOTH q1 and q2 selective imports and q1's module "
            "token NOT ≤ q2's. Both fall on the same side of the group split, so "
            "the grouping is satisfied and the un-ordered selective group is "
            "emitted verbatim as [q1, q2]; the head relation `importLe q1 q2` "
            "then falls to importLe's third match arm, which demands `moduleName "
            "q1 ≤ moduleName q2` — false by hypothesis. This is the ONE "
            "sub-domain of clause (O) no other witness reaches, so it is what "
            "shows the module order is pinned inside BOTH groups rather than only "
            "inside the plain one. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "would leave the selective group's order free)."
        ),
        "witness": _WIT_SELECTIVE_GROUP,
    },
    {
        "id": "weak-short-input-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_SHORT_INPUT_ONLY_IMPL),
        "refinement": (
            "orders the statements correctly whenever there are two or fewer of "
            "them and hands any longer collection through in the order it was "
            "gathered. Its faithful real counterpart is an ordering step guarded "
            "by a short-circuit on the collection's size — a plausible "
            "micro-optimisation, since a block of one or two statements is "
            "already in order often enough. Because the statements are gathered "
            "into an UNORDERED collection, any block of three or more is then "
            "emitted arbitrarily, so the FAIL_TO_PASS ordering test's asserted "
            "block is not produced at exactly the size that test uses: its "
            "configuration has THREE statements, two plain module imports and "
            "one selective import. It does NOT resolve. Added by a third audit "
            "to close a coverage gap the shipped battery had: every other rival "
            "is refuted at an input of two statements or fewer (five at two, "
            "`weak-drop-last` at one), so a spec whose ordering clause bound "
            "only short collections would have shown a fully green reject lane."
        ),
        "rationale": (
            "REJECTED by clause (O) `result.Pairwise (fun a b => importLe a b = "
            "true)`, on the LENGTH sub-domain no other witness reaches: "
            "`imports = [p, q, r]` with p and r plain module imports whose module "
            "tokens are already in order and q a selective import between them. "
            "The rival applies no ordering at that length, so it emits "
            "[p, q, r] verbatim; the adjacent pair (q, r) then puts a selective "
            "import ahead of a plain one, and `importLe q r` is FALSE by "
            "importLe's second match arm whatever the module tokens are. Note "
            "the input is a permutation of the input either way, so clause (P) "
            "holds and only (O) refutes it. Attacks the GROUP half of clause (O) "
            "at length three — the size the discriminating configuration actually "
            "has. If it VERIFIES => SPEC-TOO-WEAK (the spec would constrain the "
            "order only on collections of two statements or fewer)."
        ),
        "witness": _WIT_SHORT_INPUT,
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_DROP_LAST_IMPL),
        "refinement": (
            "canonically orders the statements and then silently drops the final "
            "one. Its faithful real counterpart emits a block missing a statement, "
            "so the generated module would not import something it uses — the "
            "FAIL_TO_PASS ordering test asserts a block containing ALL of the "
            "collected statements, and a short block fails it. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P) `List.Perm result imports` — the FRAME clause, "
            "which pins the emitted content to the input carrier and is the value-"
            "level counterpart of the read-only-input obligation. At `imports = [s]` "
            "for an arbitrary statement s the rival emits [], which is not a "
            "permutation of [s] (the lengths differ). Attacks clause (P) on the "
            "content-DROPPED sub-domain, a different clause from every ordering "
            "rival, at a singleton input no other witness uses. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would not force every collected statement to be "
            "emitted)."
        ),
        "witness": _WIT_DROP_LAST,
    },
    {
        "id": "weak-collapse-to-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mod_impl(_COLLAPSE_HEAD_IMPL),
        "refinement": (
            "emits the right NUMBER of statements but fills every slot with the "
            "first one, so the remaining statements are dropped and that one is "
            "duplicated. Its faithful real counterpart is a mis-written de-duplication"
            " or rewrite step: the emitted block repeats one statement and omits the "
            "others, which fails the FAIL_TO_PASS ordering test's asserted block "
            "(that block lists distinct statements, each once). It does NOT resolve. "
            "Distinct from weak-drop-last: this output has the CORRECT LENGTH and is "
            "canonically ordered, so a length- or order-only spec would miss it — "
            "hence its own witness at a two-element input rather than the singleton."
        ),
        "rationale": (
            "REJECTED by clause (P) `List.Perm result imports`, on the content-"
            "DUPLICATED sub-domain, behind an output that clause (O) accepts: at "
            "`imports = [a, b]` with a and b DISTINCT plain module imports already in "
            "module order, the canonical ordering fixes [a, b] and the rival emits "
            "[a, a] — Pairwise holds (a never improperly precedes itself) but b is "
            "absent, so `[a, a].Perm [a, b]` fails via membership. Shows clause (P) "
            "genuinely grounds the output in the input carrier and is not implied by "
            "clause (O) plus a length check. If it VERIFIES => SPEC-TOO-WEAK (a "
            "sorted-LOOKING output with invented content would pass)."
        ),
        "witness": _WIT_COLLAPSE_HEAD,
    },
]


# The axiom lane is empty by construction: meta.json declares no axiom and no
# deep-model reference. The statement-kind and module-name projections and the
# ordering itself are modeled DEEPLY over the transparent statement text, so there
# is no @ContractOnly-style trust point for this lane to probe — and the axiom lane
# belongs to G-AX regardless.
AXIOM_TESTS = []
