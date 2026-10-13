# properties.py — G-PBT falsification battery for django__django-16938 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only
# the impl region — and, where a positive honestly reproves, the proof body — is
# edited), checked by variant_scope before the verifier runs. Every
# expect="reject" case carries a refutation `witness`: a self-contained snippet
# that ELABORATES against the rival and FAILS on the frozen solution, so the
# rejection is attributable to the postcondition and not to a tactic script that
# merely stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / refinement.md)
#
#   ONE obligation: `theorem correct_m2mPkQuery : ∀ (qs : QuerySet),
#       problem_spec_m2mPkQuery qs (implementation_m2mPkQuery qs)`.
#
#   The modeled behavior is the construction of the related-object query that a
#   serializer iterates to emit a many-to-many field's related primary keys.
#   The carrier is a transparent record with THREE components, all of which the
#   postcondition constrains:
#     * `relation`  — identity of the related set being iterated (the frame
#                     anchor: the result must be built from THIS query);
#     * `selectRel` — the relational-traversal configuration inherited from the
#                     related manager (`unrestricted` | `fields [..]`);
#     * `immediate` — the immediate-loading field mask (`none` | `some mask`).
#
#   FOUR top-level postcondition clauses:
#     (C1) result.relation = qs.relation           — grounding / frame
#     (C2) result.immediate = some ["pk"]          — load minimization
#     (C3) result.selectRel = SelectRel.unrestricted
#                                                  — the state change the issue
#                                                    demands: an inherited
#                                                    field-RESTRICTED traversal
#                                                    configuration must not
#                                                    survive
#     (C4) raisesFieldError result = false         — the observable behavior:
#                                                    the query must be
#                                                    evaluable without the
#                                                    held-back-yet-traversed
#                                                    conflict
#
#   C4 is ENTAILED by C3 (`raisesFieldError` returns false for every
#   `unrestricted` configuration by definition), so no rival can violate C4
#   while satisfying C3. C3 is therefore the load-bearing clause and C4 is
#   attacked jointly with it; see `assessment` for why that is a property of the
#   spec rather than a gap in this battery. The entailment is machine-checked,
#   not asserted: `∀ r : QuerySet, r.selectRel = SelectRel.unrestricted →
#   raisesFieldError r = false` closes by `rw [h]` after unfolding (audit,
#   exit 0). The converse fails, which is what leaves room for a rival refuted
#   by C3 while C4 still HOLDS — weak-restrict-to-pk-instead-of-clearing, whose
#   clause profile (C1 ✓, C2 ✓, C3 ✗, C4 ✓) is itself machine-checked.
#
#   CARRIER NOTE. The nagini sibling split the same behavior across THREE
#   contracted functions (a clearing transition, a projection-narrowing
#   transition, and the composed builder) over a heap record held at fractional
#   read permission, and stated the rejection condition as an unfolded predicate
#   over three separate arguments. This bundle models only the purely functional
#   core: a single total builder over a transparent record, with the rejection
#   condition modeled deeply as `raisesFieldError`. So the nagini cases attached
#   to the two helper transitions in isolation have no separate obligation here
#   (their effect is the two record updates inside the one modeled builder), and
#   every clause the nagini battery attacked is refutable at a concrete literal
#   input — `decide` computes the whole carrier, and no conditioning on an
#   opaque term is needed anywhere.
#
# NAGINI LANES THAT DO NOT PORT (detailed in `assessment`):
#   * FRAME-MUTATION (nagini's mandatory class, 2 cases): the rival wrote
#     in-place into an input field held at half permission. Lean is
#     referentially transparent — no aliasing, no fractional permission — so a
#     "store into a read-only input" rival is not expressible. VACUOUS here; no
#     substitute is fabricated.
#   * PRECONDITION ADMISSIBILITY: the lean obligation binds `∀ (qs : QuerySet)`
#     with NO precondition hypothesis, so there is nothing that could be
#     PRECOND-TOO-STRONG. The nagini admissibility case is re-expressed as a
#     satisfiability control at the reproducer-shaped input instead.
#   * DIVERGENCE / NON-TERMINATION: the nagini sibling carries no such case.
#     KNOWN HOLE, not a vacuous class — the earlier claim that "a diverging
#     implementation cannot be written" is FALSE and was measured so. Three
#     diverging shapes are scope-legal here (`variant_problems` returns no
#     problem for any of them) and all three are REJECTED, so the class is
#     shippable in the sense that the verifier does discharge termination:
#       (a) `def implementation_m2mPkQuery qs := implementation_m2mPkQuery qs`
#       (b) an auxiliary `def m2mPkLoop q := m2mPkLoop q` threaded through
#       (c) the same auxiliary marked `partial` (`partial` is NOT in
#           variant_scope's `_ASSUMPTION_TOKENS`, so it passes the scope check)
#     (a) and (b) fail with `error: fail to show termination for`; (c)
#     elaborates the impl but then fails the frozen proof scripts.
#     What blocks SHIPPING one is the WITNESS half, and that is the honest
#     reason the case is absent rather than the disposition above:
#       - a `decide` witness cannot reduce a non-terminating impl. Measured on
#         (c): `error: Tactic 'decide' failed for proposition ¬((m2mPkLoop
#         {...}).relation = ... )` — the kernel cannot unfold `m2mPkLoop`, so
#         the exit code discriminates nothing (`witness-undecided` territory).
#       - the hypothesis-conditioned technique (state the refutation at a point
#         described by HYPOTHESIS, as for an opaque carrier) does not rescue it
#         either. For shape (a), which declares no new name and so is
#         witness-scope-legal, the witness build against the RIVAL fails at
#         `fail to show termination for` — the rival file does not compile at
#         all, so the half that must SUCCEED cannot. Shapes (b)/(c) declare
#         `m2mPkLoop`, a name the frozen solution lacks, so a witness over it is
#         rejected by `witness_scope_problems` by construction.
#     So: the termination obligation is real and does reject these rivals, but
#     no witness can attribute that rejection to the postcondition on this
#     carrier. Recorded as a HOLE (the spec/battery pair cannot ship this class),
#     NOT as vacuous (which would claim the battery is complete).
#   * AXIOM_TESTS: the axiom lane is G-AX's job and this gate ignores them. The
#     bundle consumes no axiom and declares no opaque callee anyway.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-16938"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it edits and is unique in the
# file: `_STEP_*` and `_IMPL` inside impl-start/impl-end, `_PROOF` and
# `_DET_HAVE` inside proof-start/proof-end (only a positive that genuinely
# reproves touches those, and it keeps every `theorem` STATEMENT byte-identical).
# ---------------------------------------------------------------------------

# the step that discards any inherited field-restricted traversal configuration
_STEP_CLEAR = "  q := { q with selectRel := SelectRel.unrestricted }\n"
# the step that pins the immediate-load mask to the primary key alone
_STEP_MASK = '  q := { q with immediate := some ["pk"] }\n'
_LET_MUT = "  let mut q := qs\n"

_IMPL = (
    "def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do\n"
    + _LET_MUT
    + _STEP_CLEAR
    + _STEP_MASK
    + "  return q\n"
)

_PROOF = (
    "  intro qs\n"
    "  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError\n"
    "  simp only [Id.run]\n"
    "  exact ⟨rfl, rfl, rfl, trivial⟩\n"
)

_DET_HAVE = (
    "  have himpl : implementation_m2mPkQuery qs =\n"
    "      { relation := qs.relation, selectRel := SelectRel.unrestricted,\n"
    '        immediate := some ["pk"] } := rfl\n'
)

for _a in (_STEP_CLEAR, _STEP_MASK, _LET_MUT, _IMPL, _PROOF, _DET_HAVE):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted / not unique: {_a!r}")


# ---------------------------------------------------------------------------
# Witness template. The whole carrier is transparent and `DecidableEq`, so the
# refutation is stated at a CONCRETE literal record and closed by `decide`; no
# hypothesis binder is needed, hence no consistency question can arise.
# ---------------------------------------------------------------------------

def _q(relation, select_rel, immediate):
    return ("{ relation := %s, selectRel := %s, immediate := %s }"
            % (relation, select_rel, immediate))


def _wit(qs, note):
    """`¬ problem_spec_m2mPkQuery qs (implementation_m2mPkQuery qs)` at a literal
    input. Elaborates against a rival whose output differs from the pinned record
    there; fails on the frozen solution, which satisfies the spec at every input."""
    return (
        "-- %s\n"
        "example : ¬ problem_spec_m2mPkQuery\n"
        "    %s\n"
        "    (implementation_m2mPkQuery\n"
        "      %s) := by\n"
        "  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError\n"
        "  decide" % (note, qs, qs)
    )


# ===========================================================================
# 1. POSITIVE CONTROLS (soundness) — a structurally DIFFERENT but CORRECT impl
#    must VERIFY, else SPEC-TOO-STRONG. Ported from the nagini positives
#    (pos-build-direct-construct, pos-build-reorder, pos-onlypk-local-reshape),
#    whose argument was: reshape the executable form, keep the output value.
#    On this backend each reshape must additionally be RE-PROVEN honestly —
#    the `theorem` statements stay byte-identical and no lemma / axiom / sorry
#    is introduced.
# ===========================================================================

# 1a. pos-direct-construct — port of nagini pos-build-direct-construct. Instead
#     of threading a mutable local through two successive record updates,
#     construct the pinned output record DIRECTLY in one expression. This is the
#     same value on every input, so all four clauses hold by `rfl` after
#     unfolding. Both proof bodies are re-closed (the frozen `simp only [Id.run]`
#     step is no longer needed and C4 now closes by `rfl` rather than `trivial`).
_POS_DIRECT = _swap(
    _swap(
        _BASE, _IMPL,
        "def implementation_m2mPkQuery (qs : QuerySet) : QuerySet :=\n"
        "  { relation := qs.relation, selectRel := SelectRel.unrestricted,\n"
        '    immediate := some ["pk"] }\n',
    ),
    _PROOF,
    "  intro qs\n"
    "  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError\n"
    "  exact ⟨rfl, rfl, rfl, rfl⟩\n",
)

# 1b. pos-reorder — port of nagini pos-build-reorder. The two builder steps are
#     applied in the OPPOSITE order (pin the immediate-load mask first, then
#     discard the inherited traversal restriction). The two updates touch
#     disjoint components, so both orders produce the identical record; only the
#     step order changes — a form a faithful patch could equally take. The frozen
#     proof body still closes, so this variant edits the impl region ONLY.
_POS_REORDER = _swap(_BASE, _STEP_CLEAR + _STEP_MASK, _STEP_MASK + _STEP_CLEAR)

# 1c. pos-redundant-branch — the local reshape argument of nagini
#     pos-onlypk-local-reshape, re-expressed as the reshape this carrier admits:
#     branch on the inherited traversal configuration and clear it only on the
#     arm where a restriction is actually present (the other arm already carries
#     the unrestricted configuration, so the branch is redundant, not
#     conditional). Same output on every input; the branch makes the frozen
#     `rfl`-shaped script insufficient, so both proof bodies are re-closed by
#     case-splitting on the inherited configuration. If a faithful correct impl
#     with this shape cannot verify => SPEC-TOO-STRONG (the postcondition would
#     be over-fit to one branch-free form).
_POS_BRANCH = _swap(
    _swap(
        _swap(
            _BASE, _STEP_CLEAR,
            "  match q.selectRel with\n"
            "  | SelectRel.unrestricted => q := q\n"
            "  | SelectRel.fields _ =>\n"
            "    q := { q with selectRel := SelectRel.unrestricted }\n",
        ),
        _PROOF,
        "  intro qs\n"
        "  unfold problem_spec_m2mPkQuery implementation_m2mPkQuery raisesFieldError\n"
        "  simp only [Id.run]\n"
        "  cases qs.selectRel <;> exact ⟨rfl, rfl, rfl, rfl⟩\n",
    ),
    _DET_HAVE,
    "  have himpl : implementation_m2mPkQuery qs =\n"
    "      { relation := qs.relation, selectRel := SelectRel.unrestricted,\n"
    '        immediate := some ["pk"] } := by\n'
    "    unfold implementation_m2mPkQuery\n"
    "    simp only [Id.run]\n"
    "    cases qs.selectRel <;> rfl\n",
)


# ===========================================================================
# 2. ADMISSIBILITY — re-expression of nagini admiss-reproducer-shaped-input.
#    Nagini's version defended the read-only PRECONDITION against the issue's
#    worst-case input. This obligation has no precondition hypothesis at all
#    (`∀ (qs : QuerySet)`), so PRECOND-TOO-STRONG is structurally unreachable.
#    What survives of the argument is the other half of the nagini case: that
#    the postcondition is SATISFIABLE — non-vacuous, non-contradictory — at
#    exactly the reproducer-shaped input the issue reports (a related set whose
#    manager supplied a field-restricted traversal configuration naming a field
#    that a primary-key-only load mask holds back). That claim is discharged
#    in-body by `decide`, with the frozen impl body and both frozen proof
#    scripts otherwise verbatim, so the only thing this case can fail on is a
#    spec-shape regression at that point.
# ===========================================================================
_ADMISS = _swap(
    _BASE, _LET_MUT,
    "  have _hAdmissible : problem_spec_m2mPkQuery\n"
    '      { relation := "tags", selectRel := SelectRel.fields ["master"],\n'
    "        immediate := none }\n"
    '      { relation := "tags", selectRel := SelectRel.unrestricted,\n'
    '        immediate := some ["pk"] } := by\n'
    "    unfold problem_spec_m2mPkQuery raisesFieldError\n"
    "    decide\n"
    + _LET_MUT,
)


# ===========================================================================
# 3. UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the
#    frozen spec exactly, edits ONLY the impl region, and leaves the frozen
#    proof scripts in place (they will not close for a reshaped impl — which is
#    precisely why the verdict is read off the WITNESS, checked in a file with
#    the obligations removed). Every witness below was built against the rival
#    and against the frozen solution and SEEN to discriminate.
# ===========================================================================

# 3a. THE PRE-PATCH BUG (Solution_prepatch.lean) — port of nagini
#     partial-prepatch-keep-restriction. Omit the clearing step entirely: pin the
#     primary-key-only load mask but let the related manager's inherited
#     field-restricted traversal configuration survive. Correct on every input
#     whose inherited configuration was already unrestricted; WRONG on exactly
#     the reproducer sub-domain. Violates C3, and C4 with it.
_RIV_KEEP = _swap(_BASE, _STEP_CLEAR, "")

# 3b. THE GROUNDING ATTACK — port of nagini
#     partial-drop-base-fabricate-request (the documented atk_drop_base that G-EQ
#     had to close). Discard the input query and build the result from a fresh
#     one, so the related-set identity is fabricated rather than threaded. C2/C3
#     and hence C4 all hold; only the frame/grounding clause C1 rejects it.
_RIV_FABRICATE = _swap(
    _BASE, _IMPL,
    "def implementation_m2mPkQuery (qs : QuerySet) : QuerySet := Id.run do\n"
    "  let mut q : QuerySet :=\n"
    '    { relation := "", selectRel := SelectRel.unrestricted, immediate := none }\n'
    + _STEP_CLEAR
    + _STEP_MASK
    + "  return q\n",
)

# 3c. THE LOAD-MINIMIZATION DROP — port of nagini partial-no-projection-narrow.
#     Discard the inherited traversal restriction but omit the step that pins the
#     immediate-load mask, carrying the input's mask through instead. C1/C3 and
#     hence C4 all hold; only C2 rejects it. Correct exactly when the input mask
#     already was the primary key alone.
_RIV_NO_MASK = _swap(_BASE, _STEP_MASK, "")

# 3d. NEAR-MISS on C3 — no nagini counterpart; it exists because C4 is entailed
#     by C3 and something has to show C3 is load-bearing on its OWN. Rather than
#     removing the inherited restriction, REPLACE it with a restriction naming
#     just the primary key. That configuration provokes no
#     held-back-yet-traversed conflict against a primary-key-only mask, so C4
#     HOLDS — this rival agrees with the frozen solution on C1, C2 and C4 and is
#     refuted by C3 alone. Its witness sits at an input whose inherited
#     configuration was ALREADY unrestricted, a sub-domain where 3a is correct,
#     so the two rivals are refuted at genuinely different points.
_RIV_PK_RESTRICTED = _swap(
    _BASE, _STEP_CLEAR,
    '  q := { q with selectRel := SelectRel.fields ["pk"] }\n',
)

# 3e. DOMAIN-SPLIT on C3 — added by audit. Every rival above is wrong on a
#     sub-domain carved out by ONE component of the input; none makes the
#     clearing step CONDITIONAL on another component, so nothing tested whether
#     C3 is demanded UNIFORMLY over the binder rather than just somewhere. This
#     rival clears the inherited traversal restriction only when the input
#     carries NO pre-existing immediate-load mask, and skips the clearing
#     exactly when a mask is already present — the correlation that makes the
#     conflict reachable. Machine-checked to be a genuine partial domain: it
#     agrees with the frozen output at `{tags, fields ["master"], none}` (the
#     point where 3a is refuted, exit 0 on the equality probe) and diverges from
#     it at `{tags, fields ["master"], some ["name"]}`, so it is refuted at a
#     point no existing rival's witness occupies. Its witness input is one where
#     ALL FOUR shipped rivals differ from gold, which is precisely why the
#     domain-split axis needed its own case rather than being covered by theirs.
_RIV_CLEAR_ONLY_IF_NO_MASK = _swap(
    _BASE, _STEP_CLEAR,
    "  match q.immediate with\n"
    "  | none => q := { q with selectRel := SelectRel.unrestricted }\n"
    "  | some _ => q := q\n",
)


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "structurally-different CORRECT impl (port of nagini "
            "pos-build-direct-construct): instead of threading a mutable local "
            "through two successive record updates, construct the pinned output "
            "record directly in one expression. Identical value on every input, "
            "so C1 (relation grounding), C2 (primary-key-only load mask), C3 "
            "(no field-restricted traversal configuration survives) and C4 (no "
            "held-back-yet-traversed conflict) all close by `rfl` after "
            "unfolding. Both `theorem` STATEMENTS are byte-identical and the "
            "proof bodies are re-closed honestly (no new lemma/axiom/sorry). If "
            "this faithful correct impl cannot verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-reorder-steps",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different CORRECT impl (port of nagini "
            "pos-build-reorder): the two builder steps are applied in the "
            "OPPOSITE order. They update disjoint components of the carrier, so "
            "both orders yield the identical record and every clause C1-C4 is "
            "unaffected; only the step order changes — a form a faithful patch "
            "could equally take. This variant edits the impl region ONLY (the "
            "frozen proof scripts still close), so nothing but the "
            "postcondition can reject it. If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition would be over-fit to one step order)."
        ),
    },
    {
        "id": "pos-redundant-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH,
        "rationale": (
            "the local-reshape argument of nagini pos-onlypk-local-reshape, "
            "re-expressed as the reshape this carrier admits: branch on the "
            "inherited traversal configuration and clear it only on the arm "
            "where a restriction is present. The other arm already carries the "
            "unrestricted configuration, so the branch is REDUNDANT rather than "
            "conditional and the output is unchanged on every input. The branch "
            "defeats the frozen `rfl`-shaped scripts, so both proof bodies are "
            "re-closed by case-splitting on the inherited configuration — "
            "`theorem` statements byte-identical, no new lemma/axiom/sorry. If "
            "it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one "
            "branch-free form)."
        ),
    },

    # ---------------- admissibility control (must VERIFY) ----------------
    {
        "id": "admiss-reproducer-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "re-expression of nagini admiss-reproducer-shaped-input. This "
            "obligation binds `∀ (qs : QuerySet)` with NO precondition "
            "hypothesis, so PRECOND-TOO-STRONG is structurally unreachable and "
            "the nagini permission half of the case has no counterpart. What "
            "ports is the other half: the postcondition is SATISFIABLE — "
            "non-vacuous and non-contradictory — at exactly the reproducer-"
            "shaped input the issue reports (a related set whose manager "
            "supplied a field-restricted traversal configuration naming a field "
            "that a primary-key-only load mask holds back). Discharged in-body "
            "by `decide` at that literal point, with the frozen impl body and "
            "both frozen proof scripts otherwise verbatim, so the only thing "
            "this can fail on is a spec-shape regression there."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "weak-keep-inherited-restriction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEEP,
        "refinement": (
            "this IS the pre-patch behaviour (Solution_prepatch.lean): the "
            "builder narrows the immediate-load mask to the primary key but "
            "never discards the relational-traversal restriction the related "
            "manager baked into its base queryset. For the scenario the issue "
            "reports — a related collection whose custom manager restricts "
            "relational traversal to a foreign key that a primary-key-only load "
            "mask then holds back — evaluating the query is rejected outright "
            "with the deferred-versus-traversed FieldError, so serialization "
            "raises instead of emitting the related primary keys. The F2P "
            "test_serialize_prefetch_related_m2m and test_serialize_only_pk "
            "(all four serializer formats) fail. Does NOT resolve — it is "
            "literally the defect under repair, so a verifying rival here would "
            "be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by C3 (result.selectRel = SelectRel.unrestricted) and, "
            "with it, C4 (raisesFieldError result = false): on an input whose "
            "inherited configuration restricts traversal to a field absent from "
            "the primary-key-only mask, the rival's result keeps that "
            "restriction, so C3 is false and the conflict predicate is true. "
            "Attacks the `selectRel = fields [..]` sub-domain of the binder qs "
            "with `immediate = none`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # gold => {tags, unrestricted, some ["pk"]}; rival keeps fields ["master"]
        # against a ["pk"] mask, so C3 is false and the conflict predicate true.
        "witness": _wit(
            _q('"tags"', 'SelectRel.fields ["master"]', "none"),
            "inherited field-restricted traversal survives: C3 and C4 both fail",
        ),
    },
    {
        "id": "weak-fabricate-relation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FABRICATE,
        "refinement": (
            "this discards the input query and builds the iterator from a fresh "
            "one, so the related-set identity is fabricated rather than "
            "threaded through. Its faithful real counterpart builds the related-"
            "object iterator from a different (here, empty) related collection "
            "instead of the one belonging to the object being serialized, so "
            "the emitted many-to-many row list is not that object's actual "
            "related members. The behavioural F2P tests assert the exact "
            "many-to-many primary-key list — test_serialize_prefetch_related_m2m "
            "and the basic serialization tests across all four serializer "
            "formats — and would fail. Does NOT resolve. This is the "
            "verified-but-unresolved shape G-EQ closed by adding the grounding "
            "clause."
        ),
        "rationale": (
            "REJECTED by C1 (result.relation = qs.relation) ALONE: the rival "
            "satisfies C2, C3 and hence C4, and differs from the frozen "
            "solution only in the frame component. Attacks the `relation` "
            "binder component, which every other rival threads correctly — "
            "without C1 the postcondition would leave that component "
            "unconstrained. Witness input additionally holds the inherited "
            "configuration UNRESTRICTED and a non-primary-key mask; at that "
            "point weak-keep-inherited-restriction is CORRECT (machine-checked: "
            "its output equals the frozen output there), so C1 is genuinely the "
            "only clause carrying this case. The other two rivals are NOT "
            "correct at this point — weak-drop-load-minimization is refuted "
            "there by C2 (the `some [\"name\"]` mask survives) and "
            "weak-restrict-to-pk-instead-of-clearing by C3 — so this input is "
            "not a sub-domain where all other rivals agree with gold, only one "
            "where the C1 attack is isolated from C2/C3/C4. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # gold => {topics, unrestricted, some ["pk"]}; rival => relation "" .
        "witness": _wit(
            _q('"topics"', "SelectRel.unrestricted", 'some ["name"]'),
            "related-set identity fabricated rather than threaded: C1 fails",
        ),
    },
    {
        "id": "weak-drop-load-minimization",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_MASK,
        "refinement": (
            "this discards the inherited traversal restriction but omits the "
            "step that pins the immediate-load mask, carrying the input's mask "
            "through instead. A faithful real counterpart therefore loads every "
            "column of each related row rather than just the primary key, "
            "losing the by-reference / no-superfluous-column guarantee. The F2P "
            "test_serialize_only_pk and "
            "test_serialize_no_only_pk_with_natural_keys assert that the "
            "cascade query carries ONLY the primary key (an assertNotIn on the "
            "extra column), so over-loading columns fails them on all four "
            "serializer formats. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2 (result.immediate = some [\"pk\"]) ALONE: the rival "
            "satisfies C1, C3 and hence C4, and is correct exactly on the "
            "sub-domain where the input mask already was the primary key alone. "
            "Attacks the `immediate` binder component at `some [\"name\"]` — a "
            "pre-existing, non-primary-key mask — together with a "
            "field-restricted inherited configuration. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # gold => immediate some ["pk"]; rival carries some ["name"] through.
        "witness": _wit(
            _q('"tags"', 'SelectRel.fields ["master"]', 'some ["name"]'),
            "pre-existing non-primary-key load mask carried through: C2 fails",
        ),
    },
    {
        "id": "weak-restrict-to-pk-instead-of-clearing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PK_RESTRICTED,
        "refinement": (
            "instead of discarding the inherited relational-traversal "
            "restriction, this REPLACES it with one naming the primary key. Its "
            "faithful real counterpart requests relational traversal of the "
            "primary-key field, which is not a relational field at all: query "
            "compilation rejects it with an invalid-field-name FieldError "
            "instead of the deferred-versus-traversed one. Serialization still "
            "raises, so test_serialize_prefetch_related_m2m and "
            "test_serialize_only_pk still fail across all four serializer "
            "formats — it trades one rejection for another. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C3 (result.selectRel = SelectRel.unrestricted) ALONE, "
            "and this is the case that shows C3 is load-bearing INDEPENDENTLY "
            "of C4: a traversal restriction naming only the primary key "
            "provokes no held-back-yet-traversed conflict against a "
            "primary-key-only mask, so `raisesFieldError result = false` HOLDS "
            "and the rival also satisfies C1 and C2. Only the clause demanding "
            "that no field-restricted configuration survive refutes it. NEAR-"
            "MISS relative to weak-keep-inherited-restriction, so it is refuted "
            "at a DIFFERENT point: an input whose inherited configuration was "
            "ALREADY unrestricted (with no pre-existing mask), a sub-domain "
            "where merely omitting the clearing step is correct. If it VERIFIES "
            "=> SPEC-TOO-WEAK (C3 would collapse into C4 and the spec would "
            "admit swapping one rejected configuration for another)."
        ),
        # gold => selectRel unrestricted; rival => fields ["pk"], which keeps C4
        # true, so ONLY C3 discriminates.
        "witness": _wit(
            _q('"categories"', "SelectRel.unrestricted", "none"),
            "restriction substituted for clearing on an already-unrestricted "
            "input: C3 fails while C4 still holds",
        ),
    },
    {
        "id": "weak-clear-only-when-no-existing-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CLEAR_ONLY_IF_NO_MASK,
        "refinement": (
            "this makes discarding the inherited relational-traversal "
            "restriction CONDITIONAL on the related manager's queryset not "
            "already carrying an immediate-load mask, and skips it whenever one "
            "is present. Its faithful real counterpart clears the inherited "
            "traversal configuration only for related managers that applied no "
            "load restriction of their own, and leaves it in place for the rest "
            "— so for a related collection whose manager both restricts "
            "relational traversal to a field and narrows its own loaded columns, "
            "evaluating the query is still rejected with the "
            "deferred-versus-traversed FieldError and serialization still "
            "raises. That is the reported scenario under a manager that also "
            "narrows its columns, so test_serialize_prefetch_related_m2m and "
            "test_serialize_only_pk still fail across all four serializer "
            "formats. Does NOT resolve — it fixes the issue on part of the input "
            "domain only."
        ),
        "rationale": (
            "REJECTED by C3 (result.selectRel = SelectRel.unrestricted) and, "
            "with it, C4. Added by audit to attack an axis no shipped rival "
            "touched: every other rival is wrong on a sub-domain carved by ONE "
            "input component, whereas this one CORRELATES the clearing step with "
            "a different component, testing that C3 is demanded UNIFORMLY over "
            "the binder `qs` rather than merely somewhere. Machine-checked to be "
            "a genuine partial domain rather than a restatement of 3a: it "
            "reproduces the frozen output at `{tags, fields [\"master\"], none}` "
            "— the very point where weak-keep-inherited-restriction is refuted — "
            "and diverges only once a pre-existing mask is present, so its "
            "refutation point is new. If it VERIFIES => SPEC-TOO-WEAK (C3 would "
            "be satisfiable by clearing on part of the domain only)."
        ),
        # gold => {tags, unrestricted, some ["pk"]}; rival keeps fields ["master"]
        # because the input already carries a mask, so C3 is false and C4 true.
        "witness": _wit(
            _q('"tags"', 'SelectRel.fields ["master"]', 'some ["name"]'),
            "clearing skipped because a load mask was already present: C3 and "
            "C4 both fail on the masked sub-domain",
        ),
    },
]


# The bundle consumes NO axiom and declares no opaque callee (the axioms region
# is empty): the rejection condition is modeled DEEPLY over a transparent
# carrier, so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
