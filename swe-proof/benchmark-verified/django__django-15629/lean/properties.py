# properties.py — G-PBT falsification battery for django__django-15629 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte — only the impl
# region, and (where a positive legitimately reproves) the proof body, is edited —
# checked by variant_scope before the verifier runs. Every expect="reject" case
# carries a refutation `witness`: a snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the
# postcondition and not to a tactic script that merely stopped matching a reshaped
# impl.
#
# ---------------------------------------------------------------------------
# Defended surface (read from Solution.lean / mapping.md / refinement.md)
# ---------------------------------------------------------------------------
# This bundle models THREE independently-observable decisions, each with its own
# `theorem correct_*`. That is unusual for the lean lane (451 of 500 bundles carry
# exactly one), and it means the nagini sibling's two contracted functions BOTH
# have counterparts here, plus a third decision nagini did not model at all.
#
# OBL-1  problem_spec_fkColumnParams (fkType : String) (fkCheck : Option String)
#                                    (targetParams : ColumnParams) (result : ColumnParams)
#   Three independent top-level conjuncts, each pinning ONE component of the
#   returned parameter record to an input:
#     (a) result.colType   = fkType                  — own type text (FRAME)
#     (b) result.checkExpr = fkCheck                 — own check expression (FRAME)
#     (c) result.collation = targetParams.collation  — THE load-bearing clause:
#         the collation is pinned to the REFERENCED column's collation, so a
#         referencing column always carries the collation of the column it points
#         at. Clause (c) is what the issue is about; (a)/(b) are the frame
#         obligation in this backend's idiom (§0.5 of the spec guide: Lean is
#         referentially transparent, so "do not disturb the unchanged parts" is
#         expressed as explicit equalities rather than as a permission).
#   No precondition: the obligation binds all three inputs universally.
#
# OBL-2  problem_spec_rebuildIncomingFks (supportsFk oldPk newPk oldUnique
#          newUnique : Bool) (oldType newType : String)
#          (oldCollation newCollation : Option String) (result : Bool)
#   A single clause, but a three-conjunct boolean characterisation — an
#   equality, hence a bi-implication in both directions:
#     result = supportsFk
#              && ((oldPk && newPk) || (oldUnique && newUnique))
#              && ((oldType != newType) || (oldCollation != newCollation))
#   The third conjunct's SECOND disjunct is the load-bearing part: a change to
#   the collation alone must trigger the rebuild, exactly as a change to the type
#   alone does. Because the spec is an equality and not an implication, it is
#   attacked from both sides: a rival that under-fires (misses a sub-domain the
#   spec says must rebuild) and one that over-fires (rebuilds where the spec says
#   it must not) are both refutable.
#
# OBL-3  problem_spec_relatedColumnAlterKind (oldRelCollation relCollation :
#          Option String) (result : RelAlterKind)
#     result = if oldRelCollation != relCollation then collationAlter
#              else typeAlter
#   A two-way branch selection over the two collation inputs. Total on the
#   carrier, so both arms are attackable at literal inputs.
#
# CARRIER NOTE (what the port had to re-express). The nagini sibling abstracted
# the parameter mapping to a `Dict[int,int]` of interned tokens behind fractional
# read permission, so its battery spent cases on membership (`key_collation() in
# Result()`), on a no-spurious-keys quantifier, and on a permission-mutation
# rival. This backend models the same mapping as a THREE-FIELD `structure`, which
# collapses that whole sub-lane by construction: a record has exactly its three
# fields, so "the collation key is absent" and "a fourth spurious key is present"
# are not states a `ColumnParams` can be in. What survives from nagini's
# membership+value pair is a single VALUE attack per component, and the
# no-spurious-keys clause becomes the two frame conjuncts (a)/(b). Nagini's
# `none_value()` sentinel maps to `Option.none`, so its "present but empty
# collation" rival and its "absent collation" rival are the SAME state here.
#
# LANES THAT DO NOT PORT (see `assessment` for the full disposition):
#   * FRAME-MUTATION — nagini's mandatory #1 class (target_params was held at
#     half permission and the rival WROTE it, to satisfy the value clause from
#     the input it had just overwritten). Lean is referentially transparent: no
#     aliasing, no fractional permission, and an input a function cannot observe
#     writing to is an input it cannot corrupt. The class is genuinely VACUOUS
#     here — not a spec hole. Note the frame CONCERN is still tested, in the
#     form this backend admits: clauses (a)/(b) pin the two components the
#     modeled behavior must leave alone, and two rivals attack them.
#     AUDIT re-derivation (attack F): agreed, and DEMONSTRATED rather than
#     asserted. The closest expressible analogue — shadow the referenced mapping
#     with a locally modified copy, then read the collation off THAT — was built
#     and is rejected (exit 1), because the spec's right-hand side names the
#     ORIGINAL input, which no local rebind can reach. The nagini rival's
#     distinctive content (satisfying the value clause by corrupting the input it
#     reads back) therefore has no counterpart here: not "hard to write" but "the
#     state it exploits does not exist". The port's disposition stands; the probe
#     itself reduces to a redundant value-level attack on clause (c) that
#     weak1-own-type-as-collation already covers, so it is not added as a case.
#   * ADMISSIBILITY — nagini's admiss-fn1-f2p-shaped defended a precondition
#     (`Acc(dict_pred(d),1/2)` and the collation key's presence) against being
#     unsatisfiable for an F2P-shaped input.
#     AUDIT CORRECTION (attack F). The port's original disposition — "all three
#     obligations are unconditional `∀` statements with NO precondition
#     hypothesis, so nothing could be PRECOND-TOO-STRONG and the lane is N/A" —
#     is REJECTED, and this audit landed the lane rather than agreeing with it.
#     "The frozen obligation has no precondition" is not the reason: the analogue
#     on a total carrier is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, which a positive that discharges it at that concrete
#     input by evaluation — as a `have`, before closing the frozen obligation
#     verbatim — tests directly. See admiss-f2p-shaped below, which does that for
#     all three obligations at once and is measured NON-INERT (flipping its
#     refusal clause makes the case fail, exit 1).
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling carries no such case.
#     AUDIT CORRECTION (attack F′). The port's original claim — "a diverging
#     implementation cannot be written at all", so the class is VACUOUS — is
#     FALSE and was measured so. This bundle sets no
#     `set_option loom.semantics.termination` line at all, and a diverging rival
#     IS expressible on this carrier: a `partial def spinForever (n : Nat) : Nat
#     := spinForever (n + 1)` declared inside the impl region, consumed by a
#     guard in front of the frozen decision, is scope-clean (variant_problems ==
#     []) and IS rejected (exit 1, `Tactic 'rfl' failed`). So the class is not
#     vacuous. It is nonetheless NOT SHIPPABLE as a reject case, for a reason
#     that is itself measured rather than assumed: the diverging term is
#     irreducible, so a witness against that rival fails with `Tactic 'decide'
#     failed for proposition` — the rival build is the half that must SUCCEED, so
#     no witness can discriminate it and the gate would record `witness-unproven`.
#     Correct disposition therefore: a KNOWN HOLE (the spec does not constrain
#     termination and nothing in this lane can demonstrate that it should), not a
#     vacuous class. A vacuous class would claim the battery is complete; a hole
#     says the spec is not. Note the `Inhabited` variant of this probe
#     (`partial def spinForever : ... : RelAlterKind`) fails for a TOOLING reason
#     instead — "failed to compile 'partial' definition, could not prove that the
#     type ... is Inhabited" — which is not evidence about the spec either way.
#   * AXIOM_TESTS — dropped; the axiom lane is G-AX's job and this gate ignores
#     them. This bundle has no consumed axiom and no opaque callee anyway
#     (axioms == [], deep_model_references == []), so nagini's three A-reference
#     probes have no counterpart to check.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT #2 (adversarial re-audit of the port AND of audit #1).
# Verdict: REPAIRED — two further defects, both in the OMISSION dispositions
# recorded above, both fixed here. Every case in the manifest earns its outcome
# on independently rebuilt evidence.
#
# What this audit re-ran from scratch (66 builds + 19 probes, all exit codes
# observed, none inherited from the record):
#   * STATEMENT INTEGRITY (attack A) re-derived mechanically: all three
#     `theorem correct_*` statements byte-identical to the frozen file in all 21
#     cases, every line OUTSIDE the impl+proof regions byte-identical too,
#     same_spec true and variant_problems == [] for all 21. Nothing reformats.
#   * WITNESS DISCRIMINATION (attack B) rebuilt for all 15 reject cases: rival
#     exit 0 and gold exit 1, fifteen for fifteen. All 15 gold-side failures are
#     `Tactic 'decide' proved that the proposition … is false` — a plain
#     evaluation, no missing identifier, type error, stuck reduction or timeout.
#   * FORGERY TEST (attack B′) run anyway, on all 15, despite every signature
#     being a plain evaluation. The flipped claim (`¬` dropped) built against the
#     FROZEN solution: exit 0 with ZERO errors, all 15 — gold PROVES the positive
#     exactly where the witness refutes the rival. The same flipped claim against
#     the RIVAL: exit 1, all 15. So the gold-side exit code tracks the claim in
#     both directions and no case is hollow. No witness binds anything, so
#     consistency_probe returns None for all 15 and there is no witness-
#     inconsistency to screen.
#   * RIVAL OBSERVABILITY (attack C) re-derived: all 15 rivals transcribed beside
#     the frozen impls and each proven to differ from gold AT ITS OWN WITNESS
#     INPUT (`decide`, one `example` per rival, single file, exit 0). No rival is
#     definitionally equal to gold; no case is vacuous.
#   * SPEC EXACTNESS re-proven independently rather than taken from audit #1:
#     `problem_spec_X i r ↔ r = implementation_X i` for all three obligations,
#     closed in a standalone file (exit 0; the residual goals are `pure x = x` in
#     `Id`, closed by `Id.pure_eq`). That settles both probe lanes structurally.
#     Probed anyway: SEVEN new wrong impls (attack D), all REJECTED — cross-sides
#     stable-key test, collation carried for one literal value only, OBL-3
#     branching on collation PRESENCE, an empty-string collapse of the two
#     collations, an XOR of the two change characteristics, check/collation
#     transposed, and collation taken from the own check expression. FOUR new
#     correct reshapes (attack E), all VERIFY — a destructuring bind, fully
#     commuted disjuncts, an OBL-3 match on the decidable equality, and OBL-1
#     built by two sequential `with` updates off the referenced mapping. No hole
#     in either direction.
#   * PROSE re-derived where it makes a checkable claim: the assertion that
#     nagini's drop-collation and empty-collation rivals are the SAME state here
#     was re-proven (`funext`, closed by `rfl`, exit 0), so that consolidation is
#     honest and not a dropped case.
# The two defects THIS audit found and repaired — both omissions recorded above as
# settled that are not:
#   1. The ADMISSIBILITY lane was dropped as N/A for the one reason the lane's own
#      charter names as insufficient ("the frozen obligation has no
#      precondition"). Landed as admiss-f2p-shaped: a three-`have` triple per
#      obligation at an F2P-shaped input, verified, and measured NON-INERT by
#      flipping its refusal clause (exit 1).
#   2. DIVERGENCE was recorded as a VACUOUS class on the false claim that a
#      diverging impl "cannot be written at all". It can: a scope-clean
#      `partial def` spin over `Nat` consumed by a guard is rejected (exit 1).
#      Corrected to a KNOWN HOLE, with the measured reason no witness can ship
#      for it (the irreducible term makes `decide` fail on the RIVAL side, the
#      half that must succeed).
# No hole was found in the FROZEN spec, and nothing frozen was edited.
#
# ---------------------------------------------------------------------------
# AUDIT #1 (post-port). Verdict at the time: REPAIRED — two real defects, both
# fixed; findings independently re-confirmed by audit #2 above.
# ---------------------------------------------------------------------------
# What was machine-checked, not argued:
#   * STATEMENT INTEGRITY. All three `theorem correct_*` statements are
#     byte-identical to the frozen file in every case, and every line outside the
#     impl and proof regions is byte-identical too. No case reformats or weakens a
#     statement.
#   * WITNESS DISCRIMINATION. Every reject witness rebuilt against rival and gold;
#     15/15 rival exit 0 and gold exit 1, every gold failure a `decide`-refuted
#     concrete claim. See the witness-builder note below.
#   * SPEC EXACTNESS. All three postconditions were proven to be EXACT functional
#     characterisations: `problem_spec_X inputs r ↔ r = implementation_X inputs`,
#     all three closed in a standalone Lean file. So each spec pins the returned
#     value uniquely at every input. That settles the two probe lanes structurally:
#     no wrong impl can satisfy the spec (SPEC-TOO-WEAK is unreachable), and every
#     impl extensionally equal to the frozen one does satisfy it, so a positive can
#     only ever fail on proof SEARCH, never on the spec. Six new wrong impls were
#     tried anyway and all six were rejected: a cross-sides stable-key test, a
#     collation carried over for one literal value only, a branch on collation
#     PRESENCE instead of difference, an empty-string collapse of the two
#     collations, a presence-only change test, and an XOR of the two change
#     characteristics. Three new correct reshapes were tried: a destructuring bind,
#     fully commuted disjuncts, and a dependent-if branch — all three verify (the
#     latter two only after strengthening MY tactic script, which is a proof-search
#     fact and not a spec fact).
# The two defects found and repaired:
#   1. OBL-1 had no positive that actually tested clause (c) as an equality. Both
#      ported positives are DEFINITIONALLY equal to the frozen impl, so the frozen
#      `rfl`-style tactic closes them untouched and neither could have detected an
#      over-fit clause (c). Added pos1-collation-match, whose result is not defeq
#      and whose reproof must genuinely discharge the equality in both arms.
#   2. OBL-2's load-bearing collation disjunct was tested only as
#      absent-vs-present. All seven inherited OBL-2 witnesses hold the two
#      collation binders either equal or with one side unset, so a rival comparing
#      the collations by PRESENCE agrees with the frozen decision at every one of
#      them and was invisible to the lane. Added weak2-collation-presence-only,
#      refuted where a declared collation is replaced by a different declared one.
# No hole was found in the FROZEN spec, and nothing frozen was edited.
from pathlib import Path

INSTANCE = "django__django-15629"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside an impl region (or, for the two reproving
# positives, inside a proof region) and is unique in the file, so every variant
# is same_spec by construction and the manifest breaks loudly on drift.
# ---------------------------------------------------------------------------

# OBL-1 impl: the record initializer, and the line that pins the collation.
# Plus the frozen OBL-1 proof body, for the one positive whose reshape is NOT
# definitionally equal to the frozen impl and so needs a genuine reproof.
_P1 = "  intro fkType fkCheck targetParams\n  exact ⟨rfl, rfl, rfl⟩"
_A1_INIT = "    { colType := fkType, checkExpr := fkCheck, collation := none }\n"
_A1_PIN = "  params := { params with collation := targetParams.collation }\n"
_A1_BODY = (
    "  let mut params : ColumnParams :=\n"
    "    { colType := fkType, checkExpr := fkCheck, collation := none }\n"
    "  params := { params with collation := targetParams.collation }\n"
    "  return params"
)

# OBL-2 impl: one anchor per conjunct of the decision.
_A2_SUPPORT = "  let mut decision := supportsFk\n"
_A2_KEY = "  decision := decision && ((oldPk && newPk) || (oldUnique && newUnique))\n"
_A2_CHANGE = (
    "  decision := decision && ((oldType != newType) || (oldCollation != newCollation))\n"
)
_A2_BODY = _A2_SUPPORT + _A2_KEY + _A2_CHANGE + "  return decision"

# OBL-3 impl: the whole two-arm branch.
_A3_BODY = (
    "  if oldRelCollation != relCollation then\n"
    "    return RelAlterKind.collationAlter\n"
    "  return RelAlterKind.typeAlter"
)

# Frozen proof bodies (tactic lines only, inside proof-start/proof-end). Only the
# two positives that reshape a branch tree touch these; the theorem STATEMENTS
# stay byte-identical.
_P2 = (
    "  intro supportsFk oldPk newPk oldUnique newUnique oldType newType "
    "oldCollation newCollation\n  rfl"
)
_P3 = (
    "  intro oldRelCollation relCollation\n"
    "  unfold implementation_relatedColumnAlterKind problem_spec_relatedColumnAlterKind\n"
    "  by_cases h : oldRelCollation != relCollation <;> "
    "simp only [h, Id.run, if_true] <;> rfl"
)

for _a in (_A1_INIT, _A1_PIN, _A1_BODY, _A2_SUPPORT, _A2_KEY, _A2_CHANGE,
           _A2_BODY, _A3_BODY, _P1, _P2, _P3):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a!r}")


# ===========================================================================
# WITNESS BUILDERS — each states `¬ problem_spec_<name> <inputs> (implementation_
# <name> <inputs>)` at a CONCRETE literal input and closes it with `decide`.
#
# The carrier is fully transparent (String / Option String / Bool / a derived-
# DecidableEq structure and inductive), so no witness needs to CONDITION on an
# opaque term: `decide` computes both the spec and the impl at any literal. Every
# witness head therefore binds NOTHING, which also means no witness can be
# `witness-inconsistent` — there are no hypotheses to be contradictory. Verified
# by hand, both halves, for all 14 rivals: rival build exit 0, gold build exit 1.
#
# AUDIT (independent re-derivation, attack B): all 15 reject witnesses — the 14
# ported ones and the one this audit added — were rebuilt from scratch against the
# rival and against the frozen solution: rival exit 0, gold exit 1 for every one.
# Each gold-side failure was READ, and all 15 report `Tactic 'decide' proved that
# the proposition … is false` — a semantic refutation of the concrete claim, not a
# missing identifier, a type error, an unfolding failure, a stuck reduction, or a
# timeout. No witness references a name the rival declares and the frozen solution
# does not (checked mechanically).
# ===========================================================================

def _cp(col_type, check, collation):
    """A `ColumnParams` literal."""
    return ("{ colType := %s, checkExpr := %s, collation := %s }"
            % (col_type, check, collation))


def _wit1(fk_type, fk_check, target, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_fkColumnParams {fk_type} {fk_check} {target}\n"
        f"    (implementation_fkColumnParams {fk_type} {fk_check} {target}) := by\n"
        f"  unfold problem_spec_fkColumnParams implementation_fkColumnParams\n"
        f"  decide"
    )


def _wit2(args, note):
    a = " ".join(args)
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_rebuildIncomingFks {a}\n"
        f"    (implementation_rebuildIncomingFks {a}) := by\n"
        f"  unfold problem_spec_rebuildIncomingFks implementation_rebuildIncomingFks\n"
        f"  decide"
    )


def _wit3(old_rel, rel, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_relatedColumnAlterKind {old_rel} {rel}\n"
        f"    (implementation_relatedColumnAlterKind {old_rel} {rel}) := by\n"
        f"  unfold problem_spec_relatedColumnAlterKind "
        f"implementation_relatedColumnAlterKind\n"
        f"  decide"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Ported from nagini's pos-fn1-reorder /
# pos-fn1-temp / pos-fn2-branch, re-expressed over this carrier. Two of them
# reshape a branch tree and so need a genuine REPROOF; both are closed honestly
# (theorem statement byte-identical, no new axiom/lemma/sorry, no
# native_decide), and each was built and confirmed to elaborate.
# ===========================================================================

# pos1-single-literal: build the record in ONE literal instead of initializing
# the collation to the empty state and then pinning it. Nagini's pos-fn1-temp
# analogue (a local reshape of the same assembly). Every component is the same
# value, so all three conjuncts hold; the frozen `exact ⟨rfl, rfl, rfl⟩` still
# closes, so no reproof is needed.
_POS1_SINGLE = _swap(
    _BASE, _A1_BODY,
    "  return { colType := fkType, checkExpr := fkCheck,\n"
    "           collation := targetParams.collation }",
)

# pos1-reorder: assemble the components in a DIFFERENT ORDER — the referenced
# column's collation FIRST, then the two own components. Nagini's
# pos-fn1-reorder: a record's field values are order-independent, so the result
# is identical on every input and only the assembly order changes. The frozen
# proof still closes.
_POS1_REORDER = _swap(
    _BASE, _A1_BODY,
    '  let mut params : ColumnParams :=\n'
    '    { colType := "", checkExpr := none, collation := targetParams.collation }\n'
    "  params := { params with colType := fkType }\n"
    "  params := { params with checkExpr := fkCheck }\n"
    "  return params",
)

# pos1-collation-match (ADDED BY AUDIT): case-split on whether the referenced
# column declares a collation at all, and rebuild the component in each arm. This
# is the only OBL-1 positive whose result is NOT definitionally equal to the
# frozen impl's — the other two are `Id.run`-level rearrangements that the frozen
# `exact ⟨rfl, rfl, rfl⟩` still closes, so they never actually exercise clause (c)
# as an EQUALITY (measured: both build with the frozen tactic untouched). Here the
# returned collation is `some c` / `none` under a match rather than the input
# projection, so `rfl` cannot see through it and the reproof must genuinely
# establish `result.collation = targetParams.collation` in both arms. Correct on
# every input (the `none` arm reconstructs exactly the value the hypothesis names).
# Reproven honestly: statement byte-identical, no axiom/sorry/native_decide.
_POS1_MATCH = _swap(
    _swap(
        _BASE, _A1_BODY,
        "  match targetParams.collation with\n"
        "  | none => return { colType := fkType, checkExpr := fkCheck, collation := none }\n"
        "  | some c => return { colType := fkType, checkExpr := fkCheck, collation := some c }",
    ),
    _P1,
    "  intro fkType fkCheck targetParams\n"
    "  unfold problem_spec_fkColumnParams implementation_fkColumnParams\n"
    "  rcases hc : targetParams.collation with _ | c <;>\n"
    "    simp only [hc, Id.run] <;> exact ⟨rfl, rfl, rfl⟩",
)

# pos2-let-bound: name the two sub-decisions and combine them in a single
# conjunction, instead of folding them in one at a time. Behaviourally identical
# (`&&` is associative and the accumulation order is the same), so the frozen
# `rfl` still closes.
_POS2_LET = _swap(
    _BASE, _A2_BODY,
    "  let keyOnBothSides := (oldPk && newPk) || (oldUnique && newUnique)\n"
    "  let mirroredChange := (oldType != newType) || (oldCollation != newCollation)\n"
    "  return supportsFk && keyOnBothSides && mirroredChange",
)

# pos2-guards: nagini's pos-fn2-branch — an explicit early-return guard chain
# instead of the single accumulated conjunction. Returns false as soon as any
# conjunct fails and otherwise the last one's value, which is exactly `&&`, so
# the verdict is identical on every input. This RESHAPES the branch tree, so the
# frozen `rfl` no longer closes and the proof is honestly re-closed by case
# analysis on the five booleans (the two string/collation inequalities are left
# symbolic — the shape is the same on both sides once the guards are resolved).
_POS2_GUARDS = _swap(
    _swap(
        _BASE, _A2_BODY,
        "  if !supportsFk then return false\n"
        "  if !((oldPk && newPk) || (oldUnique && newUnique)) then return false\n"
        "  return (oldType != newType) || (oldCollation != newCollation)",
    ),
    _P2,
    "  intro supportsFk oldPk newPk oldUnique newUnique oldType newType "
    "oldCollation newCollation\n"
    "  unfold problem_spec_rebuildIncomingFks implementation_rebuildIncomingFks\n"
    "  cases supportsFk <;> cases oldPk <;> cases newPk <;> cases oldUnique <;>\n"
    "    cases newUnique <;> simp [Id.run, pure] <;> rfl",
)

# pos3-inverted-guard: test the two collation inputs for EQUALITY and take the
# type-aligning arm then, rather than testing for difference and taking the
# collation-aligning arm. The two arms are swapped along with the test, so the
# selection is identical on every input — a shape a faithful patch could equally
# take. Reshaping the branch breaks the frozen `by_cases … <;> rfl`, so the proof
# is honestly re-closed by case analysis on the equality (statement unchanged).
_POS3_INVERTED = _swap(
    _swap(
        _BASE, _A3_BODY,
        "  if oldRelCollation == relCollation then\n"
        "    return RelAlterKind.typeAlter\n"
        "  return RelAlterKind.collationAlter",
    ),
    _P3,
    "  intro oldRelCollation relCollation\n"
    "  unfold implementation_relatedColumnAlterKind problem_spec_relatedColumnAlterKind\n"
    "  by_cases h : oldRelCollation = relCollation <;>\n"
    "    simp only [h, Id.run, bind, pure, beq_self_eq_true, bne_self_eq_false,\n"
    "      if_true] <;> simp_all",
)


# ===========================================================================
# ADMISSIBILITY (ADDED BY AUDIT, attack F) — the obligation must be SATISFIABLE,
# and NON-VACUOUSLY so, at an F2P-shaped input. On a total carrier with no
# precondition hypothesis this is the analogue of PRECOND-TOO-STRONG: were the
# modeled relation unsatisfiable at exactly the input the reported behavior turns
# on, the obligation would hold there for a reason having nothing to do with the
# behavior. Each obligation gets a THREE-`have` triple at one concrete
# F2P-shaped input, all three proven by evaluation, then the frozen obligation is
# closed VERBATIM:
#   (a) _adm_holds   — the spec holds of the impl's value there (satisfiable);
#   (b) _adm_pinned  — the impl's value there IS a named concrete literal, so the
#                      satisfaction is not degenerate;
#   (c) _adm_refuses — the spec REFUSES the un-changed answer at that SAME input,
#                      which is what makes the case non-inert: a spec that
#                      accepted everything there would satisfy (a) too.
# The input is F2P-shaped throughout: a referencing column pointing at a stable
# primary key that declares a collation, the key's collation being replaced while
# its type stays put. Nothing is assumed — every `theorem correct_*` statement
# stays byte-identical, no new axiom/sorry/native_decide/lemma, and the `have`s
# live inside the existing tactic bodies. Measured non-inert: flipping (c) for
# OBL-3 makes the case FAIL (exit 1, `decide` proved the negation), so the
# `have`s are load-bearing rather than decorative.
# ===========================================================================

_ADM_TARGET = _cp('"varchar(10)"', "none", '(some "nocase")')

_ADMISS = _swap(
    _swap(
        _swap(
            _BASE, _P1,
            "  have _adm_holds : problem_spec_fkColumnParams \"varchar(10)\" none\n"
            f"      {_ADM_TARGET}\n"
            "      (implementation_fkColumnParams \"varchar(10)\" none\n"
            f"        {_ADM_TARGET}) := by\n"
            "    unfold problem_spec_fkColumnParams implementation_fkColumnParams\n"
            "    decide\n"
            "  have _adm_pinned : implementation_fkColumnParams \"varchar(10)\" none\n"
            f"      {_ADM_TARGET}\n"
            "      = { colType := \"varchar(10)\", checkExpr := none,\n"
            "          collation := some \"nocase\" } := by\n"
            "    unfold implementation_fkColumnParams\n"
            "    decide\n"
            "  have _adm_refuses : ¬ problem_spec_fkColumnParams \"varchar(10)\" none\n"
            f"      {_ADM_TARGET}\n"
            "      { colType := \"varchar(10)\", checkExpr := none, collation := none } := by\n"
            "    unfold problem_spec_fkColumnParams\n"
            "    decide\n"
            + _P1,
        ),
        _P2,
        "  have _adm_holds : problem_spec_rebuildIncomingFks true true true false false\n"
        "      \"varchar(10)\" \"varchar(10)\" (some \"utf8_bin\") (some \"nocase\")\n"
        "      (implementation_rebuildIncomingFks true true true false false\n"
        "        \"varchar(10)\" \"varchar(10)\" (some \"utf8_bin\") (some \"nocase\")) := by\n"
        "    unfold problem_spec_rebuildIncomingFks implementation_rebuildIncomingFks\n"
        "    decide\n"
        "  have _adm_pinned : implementation_rebuildIncomingFks true true true false false\n"
        "      \"varchar(10)\" \"varchar(10)\" (some \"utf8_bin\") (some \"nocase\") = true := by\n"
        "    unfold implementation_rebuildIncomingFks\n"
        "    decide\n"
        "  have _adm_refuses : ¬ problem_spec_rebuildIncomingFks true true true false false\n"
        "      \"varchar(10)\" \"varchar(10)\" (some \"utf8_bin\") (some \"nocase\") false := by\n"
        "    unfold problem_spec_rebuildIncomingFks\n"
        "    decide\n"
        + _P2,
    ),
    _P3,
    "  have _adm_holds : problem_spec_relatedColumnAlterKind (some \"utf8_bin\")\n"
    "      (some \"nocase\")\n"
    "      (implementation_relatedColumnAlterKind (some \"utf8_bin\")\n"
    "        (some \"nocase\")) := by\n"
    "    unfold problem_spec_relatedColumnAlterKind implementation_relatedColumnAlterKind\n"
    "    decide\n"
    "  have _adm_pinned : implementation_relatedColumnAlterKind (some \"utf8_bin\")\n"
    "      (some \"nocase\") = RelAlterKind.collationAlter := by\n"
    "    unfold implementation_relatedColumnAlterKind\n"
    "    decide\n"
    "  have _adm_refuses : ¬ problem_spec_relatedColumnAlterKind (some \"utf8_bin\")\n"
    "      (some \"nocase\") RelAlterKind.typeAlter := by\n"
    "    unfold problem_spec_relatedColumnAlterKind\n"
    "    decide\n"
    + _P3,
)


# ===========================================================================
# UNIQUENESS RIVALS — wrong impls that share the frozen spec exactly and edit
# only the impl region. Each MUST be rejected; a verifying rival is a real
# verify-does-not-imply-resolve break (SPEC-TOO-WEAK). Every one carries a
# witness confirmed to discriminate.
# ===========================================================================

# --- OBL-1: attacks on the three component clauses ---

# The pre-change behavior: never carry the referenced column's collation over, so
# the referencing column's parameters report no collation at all. Nagini's
# uniq-fn1-drop-collation AND uniq-fn1-empty-collation collapse into this ONE
# rival here, because `Option.none` is both "absent" and nagini's `none_value()`
# empty sentinel.
_RIV1_DROP = _swap(_BASE, _A1_PIN, "")

# Nagini's uniq-fn1-wrong-collation: report a collation that is present but is
# the column's OWN type text rather than the referenced column's collation.
# Value-level attack on clause (c) with the component present.
_RIV1_OWN_TYPE = _swap(
    _BASE, _A1_PIN, "  params := { params with collation := some fkType }\n")

# Frame attack on clause (a): take the type text from the referenced column
# instead of using the referencing column's own. This is the lean-carrier
# counterpart of nagini's no-spurious-entries rival — the class of "a component
# the modeled behavior must leave alone was disturbed".
_RIV1_TYPE_FROM_TARGET = _swap(
    _BASE, _A1_INIT,
    "    { colType := targetParams.colType, checkExpr := fkCheck, collation := none }\n")

# Frame attack on clause (b): take the check expression from the referenced
# column instead of using the referencing column's own.
_RIV1_CHECK_FROM_TARGET = _swap(
    _BASE, _A1_INIT,
    "    { colType := fkType, checkExpr := targetParams.checkExpr, collation := none }\n")

# --- OBL-2: attacks on the rebuild decision, from both directions ---

# THE pre-change trigger (nagini's uniq-fn2-type-only): fire on a type change
# only, ignoring the collation. Under-fires on the pure-collation-change domain.
_RIV2_TYPE_ONLY = _swap(
    _BASE, _A2_CHANGE, "  decision := decision && (oldType != newType)\n")

# Nagini's uniq-fn2-collation-only: the symmetric partial-domain rival — fire on
# a collation change only, dropping the pre-existing type disjunct.
_RIV2_COLLATION_ONLY = _swap(
    _BASE, _A2_CHANGE, "  decision := decision && (oldCollation != newCollation)\n")

# weak2-collation-presence-only (ADDED BY AUDIT): keep both disjuncts, but compare
# the two collations by PRESENCE rather than by value, so replacing a declared
# collation with a DIFFERENT declared one reads as "nothing changed". This is the
# gap the ported OBL-2 rivals left open: every one of the seven inherited witnesses
# holds the two collation inputs either equal or with one of them unset, so this
# rival agrees with the frozen decision at all seven of them (computed over the
# manifest, then confirmed by build) and only diverges at two distinct PRESENT
# values. Without it the load-bearing collation disjunct is only tested as
# absent-vs-present, which is a weaker claim than the spec makes.
_RIV2_PRESENCE_ONLY = _swap(
    _BASE, _A2_CHANGE,
    "  decision := decision && ((oldType != newType) ||\n"
    "    (oldCollation.isSome != newCollation.isSome))\n")

# Nagini's uniq-fn2-and: require BOTH to change. Under-fires on either single
# change.
_RIV2_BOTH = _swap(
    _BASE, _A2_CHANGE,
    "  decision := decision && ((oldType != newType) && (oldCollation != newCollation))\n")

# Nagini's uniq-fn2-const-true, expressed as the smallest impl edit that produces
# it: drop the whole "something is changing" conjunct, so the decision fires on
# any stable key regardless of whether anything changed. OVER-fires.
_RIV2_DROP_CHANGE = _swap(_BASE, _A2_CHANGE, "")

# Drop the backend-support conjunct: decide to rebuild even where the backend
# does not support such references. Over-fires on a different binder.
_RIV2_DROP_SUPPORT = _swap(_BASE, _A2_SUPPORT, "  let mut decision := true\n")

# Weaken the stable-key conjunct from "on BOTH sides" to "on EITHER side", so a
# key that is stable on only one side still triggers a rebuild. Over-fires; the
# only rival that moves the four key booleans.
_RIV2_EITHER_SIDE = _swap(
    _BASE, _A2_KEY,
    "  decision := decision && ((oldPk || newPk) || (oldUnique || newUnique))\n")

# Nagini's uniq-fn2-const-false: never rebuild. Supporting near-miss, refuted at
# the input where BOTH characteristics change — the strongest possible demand.
_RIV2_CONST_FALSE = _swap(_BASE, _A2_CHANGE, "  decision := false\n")

# --- OBL-3: attacks on the branch selection (no nagini counterpart) ---

# The pre-change behavior: always re-align the referencing column by type, never
# by collation. This is the arm the issue is about.
_RIV3_ALWAYS_TYPE = _swap(_BASE, _A3_BODY, "  return RelAlterKind.typeAlter")

# The opposite constant: always take the collation-aligning arm, even when the
# collation is unchanged.
_RIV3_ALWAYS_COLLATION = _swap(
    _BASE, _A3_BODY, "  return RelAlterKind.collationAlter")

# Swap the two arms while keeping the test: the selection is exactly inverted.
_RIV3_INVERTED = _swap(
    _BASE, _A3_BODY,
    "  if oldRelCollation != relCollation then\n"
    "    return RelAlterKind.typeAlter\n"
    "  return RelAlterKind.collationAlter")


SPEC_TESTS = [
    # ================= POSITIVE CONTROLS (must VERIFY) =================
    {
        "id": "pos1-single-literal",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS1_SINGLE,
        "rationale": (
            "structurally-different CORRECT impl of the referencing column's "
            "parameter mapping: build the record in ONE literal rather than "
            "initializing the collation to the empty state and pinning it "
            "afterwards. Every component takes the same value, so all three "
            "conjuncts (own type text, own check expression, collation pinned to "
            "the referenced column's) still hold; the frozen proof closes "
            "unchanged, so the theorem statement AND tactic body are untouched. "
            "If it FAILS => SPEC-TOO-STRONG (the postcondition would be over-fit "
            "to one assembly shape rather than to the values). AUDIT CAVEAT: this "
            "reshape is DEFINITIONALLY equal to the frozen impl — that is why the "
            "frozen tactic still closes — so on its own it is a weak positive, "
            "confirming only that the spec is not over-fit at the syntactic level. "
            "The non-defeq positive pos1-collation-match was added to carry the "
            "real soundness claim for this obligation."
        ),
    },
    {
        "id": "pos1-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS1_REORDER,
        "rationale": (
            "the nagini reorder positive on this carrier: assemble the referenced "
            "column's collation FIRST, then the two own components. A record's "
            "field values are order-independent, so the result is identical on "
            "every input and only the assembly order changes. All three conjuncts "
            "hold and the frozen proof closes unchanged. If it FAILS => "
            "SPEC-TOO-STRONG. AUDIT CAVEAT: like pos1-single-literal this is "
            "DEFINITIONALLY equal to the frozen impl (the frozen tactic closes it "
            "untouched), so it is a syntactic-robustness control rather than a "
            "full soundness probe; pos1-collation-match carries the latter."
        ),
    },
    {
        "id": "pos1-collation-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS1_MATCH,
        "rationale": (
            "ADDED BY AUDIT. The other two OBL-1 positives reshape only the "
            "assembly and stay DEFINITIONALLY equal to the frozen impl — the "
            "frozen `exact ⟨rfl, rfl, rfl⟩` closes them untouched — so neither "
            "actually exercises clause (c) as an equality that has to be proven. "
            "This one case-splits on whether the referenced column declares a "
            "collation and rebuilds the component in each arm, so the returned "
            "value is `some c` / `none` under a match instead of the input "
            "projection and `rfl` cannot see through it. Correct on every input: "
            "in the empty arm the reconstructed `none` IS the referenced "
            "column's collation by the hypothesis of that arm. Reproven honestly "
            "by case analysis — `theorem correct_fkColumnParams` keeps a "
            "byte-identical statement and nothing is assumed. If it FAILS => "
            "SPEC-TOO-STRONG (clause (c) would be satisfiable only by impls that "
            "hand the input projection back syntactically, not by every impl that "
            "computes the right value)."
        ),
    },
    {
        "id": "pos2-let-bound",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS2_LET,
        "rationale": (
            "structurally-different CORRECT impl of the rebuild decision: name the "
            "stable-key and the mirrored-change sub-decisions and combine them in a "
            "single conjunction, instead of folding them in one at a time. "
            "Identical on every input, so the equality clause holds; the frozen "
            "proof closes unchanged. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos2-guards",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS2_GUARDS,
        "rationale": (
            "the nagini pos-fn2-branch positive on this carrier: an explicit "
            "early-return guard chain instead of the single accumulated "
            "conjunction. Returns the negative verdict as soon as any conjunct "
            "fails and otherwise the last conjunct's value, which is exactly what "
            "the conjunction computes, so the verdict is identical on every input. "
            "This RESHAPES the branch tree, so the frozen tactic no longer matches "
            "and the proof is HONESTLY re-closed by case analysis on the five "
            "boolean inputs — `theorem correct_rebuildIncomingFks` keeps a "
            "byte-identical statement and no axiom/lemma/sorry/native_decide is "
            "introduced. If it FAILS => SPEC-TOO-STRONG (a faithful "
            "structurally-different impl rejected because the postcondition is "
            "over-fit to one accumulation order)."
        ),
    },
    {
        "id": "pos3-inverted-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS3_INVERTED,
        "rationale": (
            "structurally-different CORRECT impl of the branch selection: test the "
            "two collation inputs for EQUALITY and take the type-aligning strategy "
            "then, rather than testing for difference and taking the "
            "collation-aligning strategy. Test and arms are swapped together, so "
            "the selection is identical on every input. Reshaping the branch breaks "
            "the frozen tactic, so the proof is HONESTLY re-closed by case analysis "
            "on the equality; the theorem statement is byte-identical and nothing is "
            "assumed. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # ================= ADMISSIBILITY (must VERIFY) =================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADDED BY AUDIT. The port dropped this lane as N/A on the ground that "
            "the three obligations carry no precondition hypothesis, and that is "
            "not the right test: the analogue of PRECOND-TOO-STRONG on a total "
            "carrier is the obligation being UNSATISFIABLE at exactly an "
            "F2P-shaped input, which this case tests directly. All three "
            "obligations are discharged at one concrete F2P-shaped input — a "
            "referencing column pointing at a stable primary key that declares a "
            "collation, the key's collation being replaced while its type stays "
            "put — as three `have`s proven by EVALUATION, before the frozen "
            "obligation is closed verbatim: (a) the spec holds of the impl's "
            "value there; (b) that value IS a named concrete literal, so the "
            "satisfaction is not degenerate; (c) the spec REFUSES the un-changed "
            "answer at that same input, which is what makes the case non-inert "
            "rather than a restatement. Nothing is assumed: every theorem "
            "statement is byte-identical, no new axiom/sorry/native_decide/lemma, "
            "and the `have`s sit inside the existing tactic bodies. Measured "
            "load-bearing, not argued: flipping clause (c) for the branch "
            "decision makes the case FAIL (exit 1, `decide` proved the "
            "negation). If it FAILS => PRECOND-TOO-STRONG (the modeled relation "
            "would be unsatisfiable at, or vacuous at, precisely the input the "
            "reported behavior turns on)."
        ),
    },

    # ============= OBL-1 RIVALS (must be REJECTED) =============
    {
        "id": "weak1-collation-not-carried",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV1_DROP,
        "refinement": (
            "this IS the pre-change behavior the bundle's prepatch-A variant "
            "reproduces and G-DIFF flags: a referencing column's reported "
            "parameters carry only its own type text and check expression, so "
            "every consumer that reads the collation off that mapping sees nothing "
            "and the referencing column is emitted without the referenced column's "
            "collation. Both F2P tests observe exactly that value — one asserts the "
            "referencing column's collation equals the referenced key's right after "
            "the referencing model is created, the other asserts it after the "
            "referenced key's collation is altered. With no collation reported "
            "there is nothing for either to read, so the faithful un-changed "
            "function is precisely what does NOT resolve, and a verifying rival "
            "here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by conjunct (c), `result.collation = targetParams.collation`: "
            "the rival leaves the collation component at the empty state while the "
            "referenced column declares one. Attacks the load-bearing clause via "
            "the `targetParams` binder. Note this ONE rival covers both nagini "
            "cases uniq-fn1-drop-collation and uniq-fn1-empty-collation: on this "
            "carrier `Option.none` is simultaneously 'no collation entry' and "
            "nagini's present-but-empty `none_value()` sentinel, so the two are the "
            "same state and a second rival would be the same test twice — the "
            "audit checked this by PROVING the two ported impls equal as "
            "functions (`funext`, closed by `rfl`) rather than taking it on "
            "argument, and by building the explicit-`none`-write form and "
            "confirming it is rejected too. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit1(
            '"varchar(10)"', "none",
            _cp('"varchar(10)"', "none", '(some "utf8_bin")'),
            "referenced column declares a collation; rival leaves it unset"),
    },
    {
        "id": "weak1-own-type-as-collation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV1_OWN_TYPE,
        "refinement": (
            "reports a collation that is PRESENT but is the column's own type text "
            "rather than the referenced column's collation. Its faithful real "
            "counterpart is a change that populated the collation slot from the "
            "wrong source: the referencing column would then be emitted with a "
            "collation naming a type string, so it still does not match the "
            "referenced key and the constraint the issue is about still fails. The "
            "F2P test asserts the referencing column's collation EQUALS the "
            "referenced key's declared collation, and a mismatched value fails that "
            "assertion just as an absent one does — it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by conjunct (c): the collation component is present but is "
            "not equal to `targetParams.collation`. Nagini's "
            "uniq-fn1-wrong-collation — the purely value-level attack on the "
            "load-bearing clause, distinguished from weak1-collation-not-carried by "
            "attacking it at a point where the component IS populated, so the two "
            "rivals do not share a witness. Varies the `fkType` binder, which the "
            "collation-not-carried witness holds elsewhere. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit1(
            '"varchar(22)"', "none",
            _cp('"varchar(22)"', "none", '(some "utf8_bin")'),
            "rival reports its own type text as the collation"),
    },
    {
        "id": "weak1-type-from-referenced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV1_TYPE_FROM_TARGET,
        "refinement": (
            "takes the TYPE TEXT from the referenced column's mapping instead of "
            "using the referencing column's own. Its faithful real counterpart "
            "overreaches while carrying the collation across: it copies the "
            "referenced column's type as well. Those two type texts genuinely "
            "differ — a referencing column derives its type from what a related "
            "column pointing at that key should use, which for an auto-incrementing "
            "key is the plain integer type and not the key's own "
            "auto-increment-bearing type. Emitting the key's own type on the "
            "referencing column produces a column definition of the wrong type "
            "(and, for an auto-increment key, a second auto-increment column), so "
            "the referencing table would not even build; the F2P tests create the "
            "referencing models before reading any collation off them, so this "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECTED by conjunct (a), `result.colType = fkType`. This is the "
            "FRAME lane in the form this backend admits: the spec pins the two "
            "components the modeled behavior must leave alone, and this rival "
            "disturbs one of them while getting the load-bearing collation clause "
            "right. It is the counterpart of nagini's no-spurious-entries rival "
            "(uniq-fn1-spurious-entry) — a record cannot carry a spurious fourth "
            "field, so the way to over-report here is to overwrite a component "
            "from the wrong source. Varies `targetParams.colType` against "
            "`fkType`, which every other OBL-1 witness holds equal. If it VERIFIES "
            "=> SPEC-TOO-WEAK (clause (a) would be hollow and a rival could put "
            "anything in the type slot)."
        ),
        "witness": _wit1(
            '"integer"', "none", _cp('"serial"', "none", '(some "nocase")'),
            "referenced type text differs from the referencing type text"),
    },
    {
        "id": "weak1-check-from-referenced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV1_CHECK_FROM_TARGET,
        "refinement": (
            "takes the CHECK EXPRESSION from the referenced column's mapping "
            "instead of using the referencing column's own. Its faithful real "
            "counterpart copies one component too many while carrying the collation "
            "across. A referencing column contributes no check expression of its "
            "own, whereas a referenced key constrained to non-negative values "
            "contributes one naming ITS column; copying it emits that constraint a "
            "second time on the referencing table, naming a column in the wrong "
            "table. The generated definition is then invalid, so the referencing "
            "model cannot be created and the F2P tests, which create it first, "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECTED by conjunct (b), `result.checkExpr = fkCheck`. The second "
            "half of the FRAME lane: the load-bearing collation clause and the type "
            "clause are both satisfied, and only the check component is disturbed, "
            "so the rejection is attributable to clause (b) alone. This is the only "
            "witness that moves the `fkCheck` binder off the empty state, which "
            "matters because a rival mishandling only the check component would "
            "otherwise be invisible. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit1(
            '"integer"', '(some "positive")', _cp('"integer"', "none", "none"),
            "rival takes the check expression from the referenced column"),
    },

    # ============= OBL-2 RIVALS (must be REJECTED) =============
    {
        "id": "weak2-type-change-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_TYPE_ONLY,
        "refinement": (
            "this IS the pre-change trigger the bundle's prepatch-B variant "
            "reproduces and G-DIFF flags: the decision to tear down and rebuild "
            "incoming references fires on a type change alone. A change to the "
            "referenced key's collation with its type unchanged therefore leaves "
            "the referencing columns untouched, so they keep the old collation "
            "while the key has the new one. The F2P test that alters a primary "
            "key's collation does exactly that — the type is unchanged across the "
            "alteration — and then asserts the referencing columns carry the new "
            "collation. This rival misses that sub-domain entirely and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause on the pure-collation-change "
            "sub-domain: with `oldType = newType` and "
            "`oldCollation != newCollation` the spec's third conjunct is true, so "
            "the result must be true, but the rival's narrowed conjunct is false. "
            "Attacks the load-bearing SECOND DISJUNCT of the mirrored-change "
            "conjunct via the two collation binders. Nagini's uniq-fn2-type-only. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "true", "true", "false", "false",
             '"varchar(10)"', '"varchar(10)"', "none", '(some "utf8_bin")'],
            "pure collation change on a stable primary key"),
    },
    {
        "id": "weak2-collation-change-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_COLLATION_ONLY,
        "refinement": (
            "the symmetric partial-domain rival: its faithful real counterpart "
            "adds the collation disjunct but DROPS the pre-existing type one, so a "
            "change to the referenced key's type with its collation unchanged no "
            "longer rebuilds the referencing columns. That regresses long-standing "
            "behavior the pre-existing type-change tests depend on: they alter a "
            "primary key's type and assert the referencing columns' type follows. "
            "Those are P2P tests here, so this rival breaks the suite rather than "
            "fixing it and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause on the pure-type-change sub-domain: "
            "with `oldType != newType` and `oldCollation = newCollation` the spec "
            "demands true and the rival returns false. Attacks the FIRST disjunct "
            "of the mirrored-change conjunct, which the collation-focused rivals "
            "leave alone. Nagini's uniq-fn2-collation-only. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "true", "true", "false", "false",
             '"text"', '"varchar(20)"', '(some "nocase")', '(some "nocase")'],
            "pure type change on a stable primary key"),
    },
    {
        "id": "weak2-collation-presence-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_PRESENCE_ONLY,
        "refinement": (
            "ADDED BY AUDIT. Keeps both disjuncts but compares the two collations "
            "by PRESENCE rather than by value, so the decision fires when a "
            "collation appears or disappears and NOT when a declared collation is "
            "replaced by a different declared one. Its faithful real counterpart "
            "tests whether each side has a collation at all instead of testing "
            "the two values for difference — a plausible slip when widening a "
            "condition over optional values. Altering a referenced key from one "
            "declared collation to another then leaves the referencing columns "
            "untouched, so they keep the old collation while the key has the new "
            "one: exactly the mismatch the issue is about, merely reached from a "
            "different starting state. The F2P test that alters a primary key's "
            "collation and asserts the referencing columns follow does NOT "
            "resolve whenever the key already declared one."
        ),
        "rationale": (
            "REJECTED by the equality clause where the two collations are both "
            "PRESENT and DIFFERENT with the type unchanged: the spec's second "
            "disjunct is true so the result must be true, and the rival's "
            "presence comparison is false. Added because every inherited OBL-2 "
            "witness holds the two collation binders either EQUAL or with one of "
            "them unset, so this rival agrees with the frozen decision at all "
            "seven of them — it was invisible to the ported lane, which tested "
            "the load-bearing disjunct only as absent-vs-present. Rebuilt both "
            "halves: witness elaborates against the rival, fails on the frozen "
            "solution by `decide` refuting the concrete claim. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "true", "true", "false", "false",
             '"varchar(10)"', '"varchar(10)"',
             '(some "utf8_bin")', '(some "utf8_general_ci")'],
            "a declared collation is replaced by a DIFFERENT declared one"),
    },
    {
        "id": "weak2-requires-both-changes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_BOTH,
        "refinement": (
            "requires the type AND the collation to change together. Its faithful "
            "real counterpart writes a conjunction where the behavior needs a "
            "disjunction, so NEITHER a type-only change nor a collation-only change "
            "rebuilds the referencing columns. That fails both the pre-existing "
            "type-change expectations and the new collation-change one, so it "
            "resolves neither the F2P nor keeps the P2P suite green — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause on either single-change sub-domain; "
            "the witness pins it at a pure type change on a key that is stable by "
            "UNIQUENESS rather than by being primary, which also exercises the "
            "second disjunct of the stable-key conjunct — the only witness in the "
            "lane that reaches it. Nagini's uniq-fn2-and. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "false", "false", "true", "true",
             '"varchar(10)"', '"varchar(30)"', "none", "none"],
            "pure type change on a stable unique key"),
    },
    {
        "id": "weak2-always-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_DROP_CHANGE,
        "refinement": (
            "drops the 'something the referencing columns mirror is changing' "
            "conjunct entirely, so the decision fires on any stable key whether or "
            "not anything relevant changed. Its faithful real counterpart tears "
            "down and rebuilds incoming references on every alteration of a "
            "primary or unique key, issuing constraint drop/rebuild statements for "
            "alterations that touch neither the type nor the collation. The "
            "pre-existing alteration tests assert exactly which statements an "
            "unrelated alteration produces, so this over-firing rival breaks them "
            "and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause from the OTHER direction: the spec is "
            "an equality, not a one-way implication, so where nothing the "
            "referencing columns mirror is changing it demands the result be "
            "false. The witness holds both the type and the collation FIXED on a "
            "key stable on both sides, where the rival still returns true. This is "
            "the over-fire lane (nagini's uniq-fn2-const-true) and it is what makes "
            "the mirrored-change conjunct load-bearing in both directions rather "
            "than merely sufficient. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "true", "true", "true", "true",
             '"varchar(10)"', '"varchar(10)"',
             '(some "utf8_bin")', '(some "utf8_bin")'],
            "nothing the referencing columns mirror has changed"),
    },
    {
        "id": "weak2-ignores-backend-support",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_DROP_SUPPORT,
        "refinement": (
            "drops the backend-support conjunct, deciding to rebuild incoming "
            "references even where the backend does not support such references at "
            "all. Its faithful real counterpart would emit constraint teardown and "
            "rebuild statements on a backend that has no such constraints to "
            "manage, so the generated statements are invalid there. The pre-existing "
            "suite runs against backends both with and without that support and "
            "asserts the latter produce no such statements, so this does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause: with `supportsFk = false` the spec "
            "demands the result be false regardless of the other inputs, and the "
            "rival returns true. The only witness that moves the `supportsFk` "
            "binder off true, which the coverage invariant requires — a rival "
            "mishandling only that input would otherwise verify unnoticed. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["false", "true", "true", "false", "false",
             '"varchar(10)"', '"varchar(10)"', "none", '(some "utf8_bin")'],
            "backend does not support such references"),
    },
    {
        "id": "weak2-key-stable-either-side",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_EITHER_SIDE,
        "refinement": (
            "weakens the stable-key requirement from 'on BOTH sides' to 'on either "
            "side', so a key that is primary or unique only BEFORE or only AFTER "
            "the alteration still triggers a rebuild of incoming references. Its "
            "faithful real counterpart rebuilds references while the key is losing "
            "or gaining the property that made it referenceable, which is handled "
            "by a different path; the references it rebuilds are the ones being "
            "dropped or created anyway, so it emits duplicate or contradictory "
            "statements. The pre-existing tests that alter a key INTO or OUT OF "
            "primary-key status assert the statement sequence, so this does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause: with the key primary on the OLD side "
            "only and unique on neither, the spec's stable-key conjunct is false so "
            "the result must be false, but the rival's weakened disjunction is "
            "true. The only witness that separates the four key booleans from each "
            "other (all others hold each pair equal), so it is what makes the "
            "both-sides structure of that conjunct tested rather than assumed. No "
            "nagini counterpart: nagini's carrier did not model the stable-key "
            "conjunct at all. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "true", "false", "false", "false",
             '"text"', '"text"', "none", '(some "utf8_bin")'],
            "key is stable on neither side (primary on one side only)"),
    },
    {
        "id": "weak2-never-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV2_CONST_FALSE,
        "refinement": (
            "never rebuilds incoming references. Its faithful real counterpart "
            "removes the rebuild path altogether, so referencing columns are left "
            "stale after any alteration of the referenced key — failing both the new "
            "collation-change expectation and the pre-existing type-change one. "
            "Does NOT resolve; supporting near-miss."
        ),
        "rationale": (
            "REJECTED by the equality clause wherever a rebuild is required. "
            "Refuted at the input where BOTH the type and the collation change on a "
            "key stable on both sides and the backend supports such references — "
            "the point where the spec's demand is strongest and every conjunct is "
            "true — which distinguishes this witness from the single-change ones "
            "used by the two partial-domain rivals. Nagini's uniq-fn2-const-false. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit2(
            ["true", "true", "true", "true", "true",
             '"varchar(10)"', '"varchar(40)"', "none", '(some "utf8_bin")'],
            "both the type and the collation are changing on a stable key"),
    },

    # ============= OBL-3 RIVALS (must be REJECTED) =============
    {
        "id": "weak3-always-type-aligned",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV3_ALWAYS_TYPE,
        "refinement": (
            "this IS the pre-change behavior the bundle's prepatch-C variant "
            "reproduces and G-DIFF flags: a referencing column being re-aligned is "
            "always re-aligned by TYPE, never by collation. Its faithful real "
            "counterpart therefore emits a type-aligning statement for a "
            "referencing column whose collation is what actually changed, so the "
            "column keeps its old collation and still does not match the referenced "
            "key. The F2P test that alters a primary key's collation asserts the "
            "referencing columns end up with the new collation, and the "
            "type-aligning statement does not carry one — so it does NOT resolve. "
            "No nagini counterpart: nagini's carrier did not model this decision."
        ),
        "rationale": (
            "REJECTED by the equality clause on the collation-differs arm: with "
            "`oldRelCollation != relCollation` the spec pins the result to the "
            "collation-aligning strategy and the rival returns the type-aligning "
            "one. Attacks the branch this bundle's third decision exists for. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit3("none", '(some "utf8_bin")',
                         "the referencing collation is changing"),
    },
    {
        "id": "weak3-always-collation-aligned",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV3_ALWAYS_COLLATION,
        "refinement": (
            "the opposite constant: always re-align by collation, even where the "
            "referencing column's collation is unchanged and only its type needs "
            "to follow. Its faithful real counterpart replaces the type-aligning "
            "path rather than adding a branch beside it, so a referencing column "
            "whose type changed while its collation stayed put is re-aligned by a "
            "statement that restates the collation and skips the accompanying "
            "actions the type-aligning path contributes. The pre-existing tests "
            "that alter a referenced key's type assert those actions, so this does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause on the collation-EQUAL arm: with the "
            "two collation inputs equal the spec pins the result to the "
            "type-aligning strategy and the rival returns the collation-aligning "
            "one. This is the over-fire direction of the branch — it makes the "
            "`else` arm load-bearing rather than a don't-care — and its witness "
            "holds the two binders EQUAL where the other two OBL-3 witnesses make "
            "them differ. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit3('(some "nocase")', '(some "nocase")',
                         "the referencing collation is unchanged"),
    },
    {
        "id": "weak3-arms-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV3_INVERTED,
        "refinement": (
            "keeps the test on the two collation inputs but SWAPS the two arms, so "
            "the strategy chosen is exactly inverted. Its faithful real counterpart "
            "wires the new branch to the wrong side of the condition — a plausible "
            "slip when adding a branch — and so re-aligns by type precisely when "
            "the collation changed and by collation precisely when it did not. It "
            "is wrong on the whole domain and fails both the new F2P expectation "
            "and the pre-existing type-change ones; it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause on both arms. Refuted at an input "
            "where BOTH sides declare a collation and they differ — distinguishing "
            "this witness from weak3-always-type-aligned, whose witness has the old "
            "side unset: this rival is the near-miss that agrees with the frozen "
            "solution nowhere, so it is refuted at a point that also demonstrates "
            "the decision turns on the two collations being DIFFERENT rather than "
            "on either being absent. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit3('(some "utf8_bin")', '(some "nocase")',
                         "both sides declare a collation and they differ"),
    },
]


# The axiom lane belongs to G-AX and this gate ignores it. This bundle consumes
# no axiom and declares no opaque callee (axioms == [], opaque_callees == [],
# deep_model_references == []): all three decisions are modeled deeply over
# transparent carriers, so nagini's three A-reference probes have nothing to
# check here.
AXIOM_TESTS = []
