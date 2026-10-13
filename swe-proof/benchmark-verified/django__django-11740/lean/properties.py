# properties.py — G-PBT falsification battery for django__django-11740 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   generateAlteredFields : List AlteredField → List AlterFieldOp
#   Emits exactly one alteration operation per altered field, IN ORDER, and pins
#   the result ELEMENT-WISE to the input field list:
#       result = fields.map (fun f =>
#         { field := f,
#           dependencies := if f.isRelation then getDependenciesForForeignKey f.fk
#                           else [] })
#   Two independent output components per element are pinned:
#     * `field := f`      — each operation alters PRECISELY its input field, verbatim
#                           (the frame/identity clause);
#     * `dependencies`    — the relation-induced ordering constraints when the field
#                           is a relation, and NO constraint otherwise (the two
#                           branch clauses).
#   `getDependenciesForForeignKey` is modeled DEEPLY here (a transparent pure
#   helper over the reference-target data), NOT an opaque oracle — so its exact
#   value is computable and a wrong-value rival on the relation branch is
#   discriminable by `decide`.
#
# CARRIER NOTE (why the nagini "oracle pin" ports as a discriminable rival). The
# nagini sibling held the relation-induced computation behind an opaque
# @ContractOnly oracle whose only published fact was len>0, so it could only
# supply the honest-echo POSITIVE control for the exact-equality clause (no wrong
# echo could verify). This backend spells the computation out transparently, so
# the exact-value clause is attacked DIRECTLY by a rival that returns a non-empty
# but WRONG constraint on the relation branch — a genuine reject with a witness.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION (nagini's #1, MANDATORY class: the input field
#     was held at Acc(...,1/2) read-only and its mutation rival forced
#     is_relation=False to vacuously take the empty branch). Lean is referentially
#     transparent — no aliasing, no fractional permission, no `mut` heap input —
#     so a "write-back into a read-only input" rival is not expressible and that
#     mechanism is VACUOUS here; it is NOT fabricated. The FRAME CONCERN it guarded
#     (the emitted operation must alter precisely its input field, unchanged) IS
#     modeled on this carrier as the `field := f` clause and is attacked directly
#     by the frame-identity rival below. See 'assessment'.
#   (ADMISSIBILITY IS NOT ON THIS LIST — see admiss-f2p-shaped-input below. An
#   earlier revision of this battery recorded the lane as N/A on the ground that
#   the lean obligation `∀ fields, problem_spec … (implementation …)` carries no
#   precondition hypothesis. That reason is WRONG, and the lane is landed: the
#   analogue of PRECOND-TOO-STRONG on a total carrier is the obligation being
#   unsatisfiable — or only vacuously satisfiable — at exactly the input shape the
#   desired behavior is about, which a positive that discharges the spec at that
#   concrete input BY EVALUATION tests directly.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this bundle declares no opaque
#     callee / axiom (the relation computation is a transparent deep model), so
#     there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
from pathlib import Path

INSTANCE = "django__django-11740"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- region anchors (each lies ENTIRELY inside its region and is unique in the
# file, verified at load). The whole impl def is the load-bearing shape; every
# reshape lands inside `-- impl-start`/`-- impl-end`. ------------------------------
_IMPL = (
    "def implementation_generateAlteredFields\n"
    "    (fields : List AlteredField) : List AlterFieldOp := Id.run do\n"
    "  let mut result := []\n"
    "  for f in fields do\n"
    "    let mut dependencies := []\n"
    "    -- A relation alteration must carry the constraints induced by its reference\n"
    "    -- target, so the referenced model's application is ordered before it.\n"
    "    if f.isRelation then\n"
    "      dependencies := dependencies ++ getDependenciesForForeignKey f.fk\n"
    "    -- Emit the alteration operation for this field carrying the assembled\n"
    "    -- constraints.\n"
    "    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]\n"
    "  return result"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# The frozen tactic body (lies wholly inside `-- proof-start`/`-- proof-end`). Only
# a positive that legitimately re-proves touches this; the reject rivals leave it
# frozen (they are judged by their witness, not by whether this script matches). ---
_PROOF = (
    "  intro fields\n"
    "  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields\n"
    "  simp only [Id.run, bind, pure]\n"
    "  -- Route B: helper over the cleaned `forIn`, generalized over the accumulator.\n"
    "  have helper : ∀ (init : List AlterFieldOp),\n"
    "      (forIn (m := Id) fields init (fun f r =>\n"
    "        (if f.isRelation = true then\n"
    "            ForInStep.yield (r ++ [({ field := f, dependencies := [] ++ getDependenciesForForeignKey f.fk } : AlterFieldOp)])\n"
    "          else\n"
    "            ForInStep.yield (r ++ [({ field := f, dependencies := [] } : AlterFieldOp)]))))\n"
    "        = init ++ fields.map (fun f =>\n"
    "            ({ field := f, dependencies := if f.isRelation = true then getDependenciesForForeignKey f.fk else [] } : AlterFieldOp)) := by\n"
    "    intro init\n"
    "    induction fields generalizing init with\n"
    "    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "    | cons a as ih =>\n"
    "        rw [List.forIn_cons]\n"
    "        simp only [bind, pure, List.nil_append] at ih ⊢\n"
    "        by_cases h : a.isRelation = true <;>\n"
    "          simp [h, ih, List.append_assoc]\n"
    "  rw [helper]\n"
    "  simp"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


def _with_impl(new_impl: str) -> str:
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_proof(new_impl: str, new_proof: str) -> str:
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


# The head of the frozen tactic body, used to PREPEND a `have` to the frozen proof
# while leaving the frozen impl and the frozen closing script byte-for-byte intact
# (an admissibility positive reproves nothing — it discharges an extra obligation
# at a concrete input and then closes the frozen obligation verbatim).
_PROOF_HEAD = (
    "  intro fields\n"
    "  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields\n"
    "  simp only [Id.run, bind, pure]"
)
assert _BASE.count(_PROOF_HEAD) == 1, "proof-head anchor drifted"


def _with_proof_prefix(prefix: str) -> str:
    """Frozen module with `prefix` inserted at the START of the frozen tactic body."""
    return _swap(_BASE, _PROOF_HEAD, prefix + _PROOF_HEAD)


# --- witness scaffold. The spec is a bare predicate over the input field list, so
# a witness states `¬ problem_spec … fields (implementation … fields)` at a ground
# singleton list and `decide`s the resulting `List AlterFieldOp` (in)equality (all
# carriers derive DecidableEq and literals are ground). Checked in a file whose
# frozen obligation is elided by the gate, so no tactic script can mask the verdict.
# Verified (real builds): each ELABORATES against its rival and FAILS on gold. ------
def _witness(fields_lit: str) -> str:
    return (
        "example : ¬ problem_spec_generateAlteredFields\n"
        f"    {fields_lit}\n"
        "    (implementation_generateAlteredFields\n"
        f"      {fields_lit}) := by\n"
        "  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields\n"
        "  decide\n"
    )


# --- concrete input points (each a distinct singleton field list). --------------
# W1: a field that BECAME a relation, plain reference target (no intermediary).
_W1 = ('[({ isRelation := true, fk := { swappableSetting := none, '
       'remoteAppLabel := "testapp", remoteObjectName := "App2", '
       'through := none } } : AlteredField)]')
# W2: an ordinary NON-relation field.
_W2 = ('[({ isRelation := false, fk := { swappableSetting := none, '
       'remoteAppLabel := "otherapp", remoteObjectName := "Thing", '
       'through := none } } : AlteredField)]')
# W3: a relation routing through an explicit, non-auto-generated intermediary
# (two induced constraints — exercises the intermediary branch of the helper).
_W3 = ('[({ isRelation := true, fk := { swappableSetting := none, '
       'remoteAppLabel := "m2mapp", remoteObjectName := "Link", '
       'through := some ("through_app", "ThroughModel", false) } } : AlteredField)]')
# W4: an ordinary NON-relation field with a distinctive reference-target payload
# (so a rival that perturbs the emitted field's identity is caught).
_W4 = ('[({ isRelation := false, fk := { swappableSetting := some "AUTH_USER_MODEL", '
       'remoteAppLabel := "a", remoteObjectName := "B", through := none } } : AlteredField)]')
# ADMISS: a realistic MULTI-element input mixing the two altered-field kinds the
# behavior distinguishes — an ordinary value field alongside a field that is a
# relation pointing at another application's model. This is the shape the desired
# behavior is actually about, and the admissibility case discharges the spec here
# by evaluation. Deliberately length 2 (not a singleton) so satisfiability is
# exercised across elements, where the per-element branches must BOTH hold at once.
_ADMISS_PT = (
    '[({ isRelation := false, fk := { swappableSetting := none, '
    'remoteAppLabel := "testapp", remoteObjectName := "App2", '
    'through := none } } : AlteredField),\n'
    '        ({ isRelation := true, fk := { swappableSetting := none, '
    'remoteAppLabel := "testapp", remoteObjectName := "App2", '
    'through := none } } : AlteredField)]')


# --- positive-control proof bodies (each verified to close for its impl shape). ---
# Pure functional map: the equality is definitional, `rfl` closes.
_PROOF_MAP = (
    "  intro fields\n"
    "  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields\n"
    "  rfl"
)
# Imperative for-loop whose per-element dependency is a single if-EXPRESSION (no
# `mut` seed, no `[] ++`): the accumulator helper needs no per-branch case split.
_PROOF_INLINE = (
    "  intro fields\n"
    "  unfold problem_spec_generateAlteredFields implementation_generateAlteredFields\n"
    "  simp only [Id.run, bind, pure]\n"
    "  have helper : ∀ (init : List AlterFieldOp),\n"
    "      (forIn (m := Id) fields init (fun f r =>\n"
    "        (ForInStep.yield (r ++ [({ field := f, dependencies := if f.isRelation = true then getDependenciesForForeignKey f.fk else [] } : AlterFieldOp)]))))\n"
    "        = init ++ fields.map (fun f =>\n"
    "            ({ field := f, dependencies := if f.isRelation = true then getDependenciesForForeignKey f.fk else [] } : AlterFieldOp)) := by\n"
    "    intro init\n"
    "    induction fields generalizing init with\n"
    "    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "    | cons a as ih =>\n"
    "        rw [List.forIn_cons]\n"
    "        simp only [bind] at ih ⊢\n"
    "        simp [ih, List.append_assoc]\n"
    "  rw [helper]\n"
    "  simp"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_generateAlteredFields` STATEMENT byte-identical and closes
    # a real proof for the new impl shape (no new axiom/lemma, no sorry).
    # =====================================================================
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        # Drop the `Id.run do` / `mut` / `for` scaffold entirely and express the
        # assembly as a single functional map — the exact shape of the spec's
        # right-hand side. Definitionally identical, so the proof collapses to
        # `rfl` (verified with a real build). Structurally the FURTHEST-from-frozen
        # correct impl; if it cannot verify, SPEC-TOO-STRONG.
        "module": _with_impl_proof(
            "def implementation_generateAlteredFields\n"
            "    (fields : List AlteredField) : List AlterFieldOp :=\n"
            "  fields.map (fun f =>\n"
            "    { field := f,\n"
            "      dependencies := if f.isRelation then getDependenciesForForeignKey f.fk else [] })",
            _PROOF_MAP),
        "rationale": (
            "correct reshape of the mutable-do loop into the functional map the spec "
            "names directly; it produces the identical result on every input, so "
            "`result = fields.map …` holds — else SPEC-TOO-STRONG. Proof: the "
            "equality is definitional, `rfl` closes; statement byte-identical, no "
            "new axiom/lemma."),
    },
    {
        "id": "pos-inline-if",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: keep the imperative for-loop but
        # compute each element's dependency list as a single if-EXPRESSION (no
        # `mut dependencies` seed, no `[] ++`). Same value on every input; the
        # accumulator-induction proof is retuned to the collapsed loop body
        # (verified with a real build). Only the impl and proof regions change; the
        # theorem STATEMENT is byte-identical.
        "module": _with_impl_proof(
            "def implementation_generateAlteredFields\n"
            "    (fields : List AlteredField) : List AlterFieldOp := Id.run do\n"
            "  let mut result := []\n"
            "  for f in fields do\n"
            "    let dependencies : List Dep :=\n"
            "      if f.isRelation then getDependenciesForForeignKey f.fk else []\n"
            "    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]\n"
            "  return result",
            _PROOF_INLINE),
        "rationale": (
            "structurally-different CORRECT impl: the per-element dependency is a "
            "direct conditional expression rather than a seeded `mut` accumulation, "
            "producing the identical ordered result. A faithful reshape MUST verify, "
            "else SPEC-TOO-STRONG. Proof: the retuned accumulator induction closes; "
            "no new axiom/lemma, statement unchanged."),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must actually be SATISFIABLE at a
    # realistic, F2P-shaped input, not merely provable in the abstract. On a
    # total carrier with no precondition hypothesis, the analogue of
    # PRECOND-TOO-STRONG is the obligation being unsatisfiable (or only
    # vacuously satisfiable) at exactly the input shape the desired behavior is
    # about. This case discharges the spec AT that concrete input BY EVALUATION,
    # as a `have`, and only then closes the frozen obligation verbatim.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        # Impl region UNTOUCHED (byte-identical to frozen); the frozen closing
        # script is also untouched — the `have` is PREPENDED to it. The `have`
        # states the frozen spec predicate at a two-element input list that mixes
        # the two altered-field kinds the behavior distinguishes (an ordinary
        # value field, and a field that is a relation with a cross-application
        # reference target), and discharges it by `decide` — i.e. by KERNEL
        # EVALUATION of both sides, with no appeal to the frozen theorem. If the
        # spec were unsatisfiable at this shape, or satisfiable only vacuously,
        # `decide` could not close it and this case would fail.
        "module": _with_proof_prefix(
            "  have admissible_at_concrete :\n"
            "      problem_spec_generateAlteredFields\n"
            f"        {_ADMISS_PT}\n"
            "        (implementation_generateAlteredFields\n"
            f"          {_ADMISS_PT}) := by\n"
            "    unfold problem_spec_generateAlteredFields"
            " implementation_generateAlteredFields\n"
            "    decide\n"),
        "rationale": (
            "ADMISSIBILITY on a total carrier: the frozen obligation carries no "
            "precondition hypothesis, so the PRECOND-TOO-STRONG analogue is the "
            "obligation being unsatisfiable at exactly the input the desired "
            "behavior is about. This case pins that down positively — it proves "
            "`problem_spec … pt (implementation … pt)` at a concrete two-element "
            "list spanning BOTH branches (an ordinary value field, and a relation "
            "field with a cross-application reference target) by `decide`, i.e. by "
            "evaluating both sides in the kernel rather than by instantiating the "
            "frozen theorem. It then closes the frozen obligation verbatim. If the "
            "spec admitted no realistic input at this shape the `have` would not "
            "close => PRECOND-TOO-STRONG / vacuous-obligation. Impl region and the "
            "frozen closing script are byte-identical; statement unchanged; the "
            "`have` adds no top-level declaration, so no new axiom/lemma."),
    },

    # =====================================================================
    # UNIQUENESS RIVALS — wrong impls sharing the frozen spec that MUST be
    # rejected (else SPEC-TOO-WEAK). Each edits ONLY the impl region and carries a
    # machine-checked witness that ELABORATES against the rival and FAILS on gold.
    # The four witnesses probe four DISTINCT input points, spanning the relation
    # branch (with and without an intermediary), the non-relation branch, and a
    # distinctive reference-target payload.
    # =====================================================================
    {
        "id": "weak-always-empty-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: emit an UNCONDITIONALLY empty constraint list,
        # never consulting whether the field became a relation. Correct on the
        # non-relation branch, WRONG on the relation branch. This is the frozen
        # prepatch skeleton (Solution_prepatch.lean's loop body).
        "module": _with_impl(
            "def implementation_generateAlteredFields\n"
            "    (fields : List AlteredField) : List AlterFieldOp := Id.run do\n"
            "  let mut result := []\n"
            "  for f in fields do\n"
            "    let dependencies : List Dep := []\n"
            "    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]\n"
            "  return result"),
        "refinement": (
            "this IS the pre-change behaviour: every alteration operation is emitted "
            "with an empty ordering-constraint list, even for a field that has just "
            "become a relation. Its faithful real counterpart is the unchanged repo, "
            "which emits zero constraints when a plain field is altered into a "
            "relation — so the referenced application is not ordered first and the "
            "alteration cannot be resolved. The failing scenario the fix targets "
            "(altering a plain value field into a cross-application relation, which "
            "must now carry that application's ordering constraint) is STILL "
            "unresolved. verify-does-not-imply-resolve would be a true break here."),
        "rationale": (
            "REJECTED by the relation-branch clause: on a field with isRelation=true "
            "the spec pins dependencies to getDependenciesForForeignKey f.fk (a "
            "non-empty list), but the rival returns []. Refuted at W1 (a single "
            "relation field, no intermediary). If it VERIFIES => SPEC-TOO-WEAK."),
        "witness": _witness(_W1),
    },
    {
        "id": "weak-nonrelation-pollution",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual miss: attach the relation-induced constraints UNCONDITIONALLY,
        # ignoring the relation guard. Correct on the relation branch, WRONG on the
        # non-relation branch (a non-relation field gets a spurious constraint).
        "module": _with_impl(
            "def implementation_generateAlteredFields\n"
            "    (fields : List AlteredField) : List AlterFieldOp := Id.run do\n"
            "  let mut result := []\n"
            "  for f in fields do\n"
            "    let dependencies : List Dep := getDependenciesForForeignKey f.fk\n"
            "    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]\n"
            "  return result"),
        "refinement": (
            "a real patch that computed the constraints OUTSIDE the relation guard "
            "would attach a spurious ordering constraint to an ordinary "
            "(non-relation) field alteration, demanding an unrelated application be "
            "migrated first. Every scenario that alters a plain field WITHOUT making "
            "it a relation (and asserts no extra ordering constraint) would then "
            "regress. Does NOT resolve."),
        "rationale": (
            "REJECTED by the non-relation-branch clause: on a field with "
            "isRelation=false the spec pins dependencies to [], but the rival emits "
            "the relation-induced constraints. Refuted at W2 (a single non-relation "
            "field). If it VERIFIES => SPEC-TOO-WEAK."),
        "witness": _witness(_W2),
    },
    {
        "id": "weak-relation-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # The value-pin attack (nagini's oracle-pin, now discriminable because the
        # computation is a TRANSPARENT deep model): on the relation branch emit SOME
        # non-empty constraint that is NOT the one the reference target induces (a
        # placeholder). Satisfies a mere len>0, but the spec pins the EXACT value.
        "module": _with_impl(
            "def implementation_generateAlteredFields\n"
            "    (fields : List AlteredField) : List AlterFieldOp := Id.run do\n"
            "  let mut result := []\n"
            "  for f in fields do\n"
            "    let mut dependencies := []\n"
            "    if f.isRelation then\n"
            '      dependencies := [({ appLabel := "placeholder", objectName := "placeholder", fieldName := none, create := true } : Dep)]\n'
            "    result := result ++ [({ field := f, dependencies := dependencies } : AlterFieldOp)]\n"
            "  return result"),
        "refinement": (
            "a real patch that attached an arbitrary non-empty placeholder "
            "constraint (rather than the one computed from the relation's reference "
            "target) would record the WRONG ordering constraint on a relation "
            "alteration — depending on a non-existent or unrelated application. A "
            "scenario that reads back the EXACT induced constraint (the referenced "
            "application ordered first) would still observe the wrong value, so it "
            "does NOT resolve — a true verify-does-not-imply-resolve break if it "
            "verified."),
        "rationale": (
            "REJECTED by the relation-branch clause's EXACT value pin: the spec "
            "requires dependencies = getDependenciesForForeignKey f.fk, which for W3 "
            "(a relation routing through an explicit non-auto-generated intermediary) "
            "is a specific TWO-element list; the rival returns a one-element "
            "placeholder. The transparent deep model makes this decidable — a mere "
            "len>0 does NOT satisfy the spec. If it VERIFIES => SPEC-TOO-WEAK (the "
            "spec would pin only non-emptiness, not the value)."),
        "witness": _witness(_W3),
    },
    {
        "id": "weak-frame-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # The FRAME clause attack (the referentially-transparent counterpart of
        # nagini's read-only-input mutation): compute the dependency list correctly
        # but attach the operation to a PERTURBED field (its reference-target payload
        # blanked). The spec pins `field := f` verbatim, so the identity change is
        # caught even where the dependency list matches.
        "module": _with_impl(
            "def implementation_generateAlteredFields\n"
            "    (fields : List AlteredField) : List AlterFieldOp := Id.run do\n"
            "  let mut result := []\n"
            "  for f in fields do\n"
            "    let mut dependencies := []\n"
            "    if f.isRelation then\n"
            "      dependencies := dependencies ++ getDependenciesForForeignKey f.fk\n"
            '    let f\' : AlteredField := { f with fk := { swappableSetting := none, remoteAppLabel := "", remoteObjectName := "", through := none } }\n'
            "    result := result ++ [({ field := f', dependencies := dependencies } : AlterFieldOp)]\n"
            "  return result"),
        "refinement": (
            "the field an alteration operation targets must be the input field "
            "itself, unchanged — the rest of the migration generation and every "
            "downstream consumer read it. A real patch that rebuilt or overwrote the "
            "field's reference target while assembling its operation would corrupt "
            "which field is altered and its subsequent constraint computation, so no "
            "scenario asserting the operation alters precisely its own field would "
            "resolve. Does NOT resolve."),
        "rationale": (
            "REJECTED by the frame/identity clause `field := f`: the spec pins each "
            "emitted operation's field to its input field verbatim, but the rival "
            "blanks the reference-target payload. Refuted at W4 (a non-relation field "
            "with a distinctive reference-target payload: the dependency lists agree "
            "— both [] — so the ONLY divergence is the perturbed field, isolating the "
            "frame clause). If it VERIFIES => SPEC-TOO-WEAK (an output component left "
            "unconstrained — the referential-transparency analogue of the frame "
            "hole)."),
        "witness": _witness(_W4),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 value/uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models the SAME single behavior but on a
# referentially-transparent carrier, so the count is 7 SPEC cases
# (3 verify + 4 reject) and the axiom lane drops.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-guard-early-return              -> pos-functional-map        RE-EXPRESSED
#   pos-cheapest-honest-echo            -> (folded into positives)   FOLDED
#                                          (+ pos-inline-if)          ADDED positive
#   admiss-fshaped-selfcall             -> admiss-f2p-shaped-input   RE-EXPRESSED
#   weak-frame-mutate-input             -> weak-frame-identity       RE-EXPRESSED
#   weak-always-empty-prepatch          -> weak-always-empty-prepatch PORTED
#   weak-nonrelational-pollution        -> weak-nonrelation-pollution PORTED
#   weak-relational-nonequal-nonempty   -> weak-relation-wrong-value  PORTED (now
#                                          discriminable: transparent helper)
#   AXIOM_TESTS (2)                     -> (none)                    DROPPED (G-AX)
#
# RE-EXPRESSED (positives): the sibling's two positives were (a) a branch-reordered
#   guard early-return and (b) the honest oracle echo defending the exact-equality
#   pin against an opaque oracle. Here the computation is transparent, so the "honest
#   echo" is simply the correct value — folded into both positives. pos-functional-map
#   carries the "structurally-different correct impl must verify" argument (the
#   furthest reshape: the spec's own map form, `rfl`); pos-inline-if adds a second
#   correct shape (imperative loop, if-expression dependency) whose accumulator
#   induction is retuned. Both close real proofs.
# RE-EXPRESSED (admissibility): the sibling's case defended a half-permission
#   PRECONDITION admitting a freshly-built field. This carrier's obligation binds no
#   precondition, so the permission MECHANISM does not port — but the OBLIGATION the
#   lane exists to test does. Its analogue on a total carrier is satisfiability at a
#   realistic input: an obligation that no realistic input satisfies (or that only a
#   vacuous one does) is the total-carrier form of PRECOND-TOO-STRONG, and it would
#   pass every soundness and uniqueness case in this battery unnoticed.
#   admiss-f2p-shaped-input closes it by discharging the spec predicate at a
#   concrete two-element input BY KERNEL EVALUATION (`decide`) — not by
#   instantiating the frozen theorem — before closing the frozen obligation
#   verbatim. Landed, not omitted.
# RE-EXPRESSED (frame): the sibling's MANDATORY frame-mutation rival WROTE the
#   read-only half-permission input (forcing is_relation=False to vacate the
#   relation branch). Lean has no aliasing / permissions / heap input, so that
#   MECHANISM is vacuous and is NOT fabricated. The CONCERN it guarded — the emitted
#   operation must alter precisely its input field, unchanged — is a real clause on
#   this carrier (`field := f`), and weak-frame-identity attacks it directly with a
#   witness. This is coverage of a genuine transparent clause, not a fabricated
#   substitute for the permission mechanism.
# PORTED (value rivals): weak-always-empty-prepatch is the literal prepatch (empty
#   on the relation branch). weak-nonrelation-pollution is the dual miss (non-empty
#   on the non-relation branch). weak-relation-wrong-value ports the oracle-pin
#   attack: on nagini it could not be a rival (opaque oracle => no wrong echo
#   verifies, hence only a positive control), but the transparent deep model makes
#   the exact value decidable, so it ships as a genuine reject with a witness.
#
# BINDER / CLAUSE COVERAGE: the spec has ONE input binder, `fields : List
# AlteredField`; the discriminating structure lives inside the list elements. The
# four reject witnesses probe four DISTINCT singleton lists (pts=4), spanning
# isRelation ∈ {true,false}, through ∈ {none, some(_,_,false)}, and swappableSetting
# ∈ {none, some _}. The three independent clauses of the element-wise equality are
# each attacked: the relation branch (weak-always-empty-prepatch, and the exact
# value by weak-relation-wrong-value), the non-relation branch
# (weak-nonrelation-pollution), and the frame/identity `field := f` clause
# (weak-frame-identity).
#
# AXIOM_TESTS: dropped. This bundle declares no opaque callee / axiom (the relation
# computation is a directive-7 transparent deep model, validated == the real callee
# by G-AX, not consumed as an axiom here), so there is nothing to probe and the gate
# ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
