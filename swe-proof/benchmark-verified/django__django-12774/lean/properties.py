# properties.py — G-PBT falsification battery for django__django-12774 (lean lane).
#
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over and
# the mechanics re-expressed against this backend's carrier. Each SPEC case is a
# FULL Solution.lean variant that shares the FROZEN spec byte-for-byte — only the
# impl region, and where a positive legitimately reproves the proof body, is
# edited — so `markers.same_spec` holds by construction and any rejection is
# attributable to the postcondition rather than to a tampered spec. Every
# expect="reject" case carries a refutation `witness`: a self-contained snippet
# that ELABORATES against the rival and FAILS on the frozen solution, so the
# rejection is attributable to the spec and NOT to a frozen tactic script that
# merely stopped matching a reshaped impl.
#
# ============================  DEFENDED SURFACE  =============================
#
# ONE modeled function over a fully TRANSPARENT carrier (String / Bool / List of
# a two-field structure); no `opaque` callee, no axiom, so every clause is
# decidable at ground literals:
#
#   implementation_inBulk (fieldName : String) (fld : FieldInfo)
#                         (cs : List UniqueConstraint) : Except String Unit
#
# The obligation `theorem correct_inBulk` pins it against a TWO-CLAUSE
# postcondition that partitions on an acceptability predicate:
#
#   problem_spec_inBulk fieldName fld cs result :=
#     (  fieldNameAcceptable fieldName fld cs → result = Except.ok ()) ∧
#     (¬ fieldNameAcceptable fieldName fld cs → result = Except.error fieldName)
#
#   fieldNameAcceptable fieldName fld cs :=
#     fieldName = "pk" ∨ fld.unique = true ∨
#       (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName])
#
# LOAD-BEARING content, and what each rival attacks:
#
#   * The THIRD disjunct of `fieldNameAcceptable` — the existential over the
#     whole constraint list — is the discriminating content of the change. It is
#     grounded STRUCTURALLY in the input carrier (an ∃ over `cs` with two
#     conjuncts on the record's own fields), not pinned to an opaque oracle, so
#     there is no ungrounded-echo shortcut and a direct `cs.any …` impl is simply
#     the cheapest CORRECT impl rather than a cheat. Three independent ways to
#     get that disjunct wrong are attacked separately:
#       - drop it entirely (`uniq-ignore-constraints`);
#       - drop the `c.isPartial = false` conjunct, so a conditional/partial
#         constraint is treated as if it guaranteed uniqueness for every row
#         (`uniq-ignore-partial-flag`);
#       - drop the `c.fields = [fieldName]` ARITY half two DIFFERENT ways, which
#         a single rival cannot cover because they diverge from each other on a
#         real input: keep the head projection so only the FIRST member of a
#         multi-field constraint is wrongly covered (`uniq-ignore-arity`), or
#         scan the whole tuple so EVERY member is (`uniq-any-member-of-multi`);
#       - consult only the FIRST constraint rather than the whole list
#         (`uniq-first-constraint-only`);
#       - read the decision off a FORGED constraint list rather than the declared
#         one (`uniq-forge-constraint`), the observable half of nagini's
#         mandatory frame case.
#   * The FIRST two disjuncts (`fieldName = "pk"`, `fld.unique = true`) are
#     UNCHANGED behaviour the spec must still hold, and each gets its own rival
#     (`uniq-ignore-unique-flag`, `uniq-ignore-pk`) — otherwise a rival that
#     regressed one of them would verify and the battery would never notice.
#   * The SECOND clause pins the error PAYLOAD to `fieldName` itself, not merely
#     "some error". `uniq-wrong-error-payload` attacks that: an impl reporting a
#     constant payload gets the accept/reject decision right on every input and
#     is caught only by the payload half.
#
# ==========================  NAGINI → LEAN PORT  =============================
#
# The nagini sibling contracts `should_reject(field_name, field_unique,
# guarantees) -> bool` over an abstraction that returns a BARE BOOLEAN and
# encodes each guarantee as a `(bool, PSeq[int])` pair. This backend models a
# slightly WIDER surface: the outcome is `Except String Unit`, so the reported
# payload is part of the contract, and each constraint is a named structure whose
# `isPartial` / `fields` components the spec reads directly. Every nagini
# uniqueness rival has a counterpart here, plus three that nagini's carrier could
# not express (see the accounting block at the bottom of this file).
#
# The nagini pin is an EQUALITY to a front-recursive fold (`Result() == (… and
# not any_permits(guarantees, 0, field_name))`); here the same content is an
# implication PAIR over an existential. The arguments transfer unchanged — what
# `any_permits`/`permits_alone` require of a guarantee (unconditional AND
# single-field AND naming this field) is exactly what the existential's two
# conjuncts require of a constraint — but the mechanics do not, because a
# rejection on this backend has to be demonstrated by a witness rather than
# inferred from the verifier's silence.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION, in its MECHANICAL half only. Nagini's
#     mandatory `frame-mutate-guarantees` WRITES to `guarantees` (held at a
#     read-only fractional permission) to forge a permitting guarantee, so the
#     store must fail for insufficient permission. Lean is referentially
#     transparent — every input is an immutable value, no aliasing, no fractional
#     permission, no `mut` binder escaping the impl — so the WRITE, and the
#     permission-system rejection that answers it, are not expressible.
#     The lane's OBSERVABLE half is expressible and IS shipped: the question
#     behind that case is whether an impl can satisfy the postcondition by
#     manufacturing its own uniqueness evidence instead of reading the declared
#     constraint set, and on this carrier the forgery is a local rebinding rather
#     than a store. See `uniq-forge-constraint`, which is rejected with a witness.
#     (An earlier revision of this file recorded the whole lane as VACUOUS. That
#     was right about the write and wrong about the observable attack.)
#   * DIVERGENCE / NON-TERMINATION. Genuinely vacuous on lean:
#     `implementation_inBulk` is a total Lean `def`, so a diverging impl cannot
#     be written at all. (The nagini sibling carries none regardless.)
#   * ADMISSIBILITY, in its PRECONDITION half only. The lean obligation is
#     `∀ fieldName fld cs, problem_spec …` with no hypothesis, so there is no
#     `Requires` a self-call could fail to establish — nagini's
#     `admiss-meta-constraint` exists to discharge
#     `Requires(Acc(list_pred(guarantees), 1/2))`, and that permission does not
#     exist here. But the LANE is not thereby vacuous: on a total carrier the
#     analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
#     exactly a normal, F2P-shaped input, and that is directly testable. See
#     `admiss-ground-constraint-field`, which discharges the postcondition at
#     that concrete input by evaluation as a `have` before closing the frozen
#     obligation verbatim. (An earlier revision recorded the whole lane as N/A on
#     the "no precondition" reasoning; that is right about the permission and
#     wrong about the lane, which is why the case is now shipped.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job and this gate ignores it. Nothing
#     is axiomatized in this bundle anyway: the constraint-set resolution is
#     modeled deeply as list filters/maps over the record fields, so there is no
#     opaque callee to probe.
from pathlib import Path

INSTANCE = "django__django-12774"
BACKEND = "lean"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched, so silent drift (Solution.lean edited) fails loudly at
    manifest load rather than silently shipping a no-op variant."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors.
#
# `_GOLD_BODY` is the whole frozen impl body: every line between the signature
# and `-- impl-end`, lying ENTIRELY inside `-- impl-start`/`-- impl-end` and
# unique in the file. Anchoring on the complete body (rather than on the
# individual `if` line) keeps every rival's edit provably inside the impl region
# even when it also has to restate the `let`.
#
# `_GOLD_DEF` additionally covers the signature, for the one positive that drops
# the `Id.run do` scaffold entirely.
# ---------------------------------------------------------------------------

_GOLD_BODY = (
    '  let uniqueFields := singleFieldUniqueConstraintFields cs\n'
    '  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

_GOLD_DEF = (
    'def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :\n'
    '    Except String Unit := Id.run do\n'
) + _GOLD_BODY

assert _BASE.count(_GOLD_BODY) == 1
assert _BASE.count(_GOLD_DEF) == 1

# The frozen `theorem correct_inBulk` STATEMENT. variant_scope requires it to
# stay byte-identical in every variant; the two reproving positives below splice
# it back verbatim so the obligation cannot silently weaken.
_OBLIGATION_STMT = (
    'theorem correct_inBulk :\n'
    '    ∀ (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint),\n'
    '      problem_spec_inBulk fieldName fld cs (implementation_inBulk fieldName fld cs)'
)
assert _BASE.count(_OBLIGATION_STMT) == 1

def _reproved(module, tactic_body):
    """`module` with its proof region replaced by the frozen obligation
    STATEMENT plus a new tactic body. Only the body changes; the statement is
    spliced back byte-for-byte from the frozen file, and no new theorem, lemma,
    axiom or assumption token is introduced."""
    new_region = ("-- proof-start\n" + _OBLIGATION_STMT + " := by\n"
                  + tactic_body.rstrip("\n") + "\n\n")
    return module[:module.index("-- proof-start")] + new_region + \
        module[module.index("-- proof-end"):]


# ===========================================================================
# WITNESS SCAFFOLD
# ===========================================================================
#
# The carrier is fully transparent, so each refutation is stated at CONCRETE
# ground literals — no witness binds a hypothesis, so the gate's consistency
# probe is a no-op and there are no assumptions that could be jointly
# unsatisfiable. Nothing is conditioned on, nothing is quantified over.
#
# `decide` cannot be pointed at the whole predicate: `problem_spec_inBulk`'s
# result argument carries the impl's `Id.run do` term, and reducing the
# `Decidable` instance through that monadic `have __do_jp := …` join point fails
# to synthesize ("failed to synthesize Decidable ¬(( … ) → ( … ).run = …)"). So
# the witness ELIMINATES the spec's conjunction first and applies only the
# clause the rival violates:
#
#   * `_wit_must_accept` — the input IS acceptable, so clause 1 forces
#     `Except.ok ()`; the rival returns an error. `decide` is used only on the
#     purely first-order `fieldNameAcceptable`, which needs no impl term.
#   * `_wit_must_reject` — the input is NOT acceptable, so clause 2 forces
#     `Except.error fieldName`; the rival returns something else.
#
# Both then `simp` the resulting equation open and reach `False` from the clash
# of two distinct `Except` constructors (or, for the payload rival, of two
# distinct payload strings). Against the FROZEN solution the same `simp` leaves
# `h : pure (Except.ok ()) = Except.ok ()` (i.e. `True`) and the goal `False`
# stands unsolved — which is exactly what makes each of these a discriminator
# rather than a tautology. Verified by hand, both halves, for all seven.


def _wit_must_accept(field, unique, cs, cs_indent):
    """Refute at a point the spec deems ACCEPTABLE (clause 1)."""
    args = f'{field} {{ unique := {unique} }}\n    {cs}'
    return (
        f'example : ¬ problem_spec_inBulk {args}\n'
        f'    (implementation_inBulk {field} {{ unique := {unique} }}\n'
        f'      {cs}) := by\n'
        '  rintro ⟨hok, -⟩\n'
        f'  have hacc : fieldNameAcceptable {field} {{ unique := {unique} }}\n'
        f'      {cs_indent} := by\n'
        '    unfold fieldNameAcceptable; decide\n'
        '  have h := hok hacc\n'
        '  simp [implementation_inBulk, singleFieldUniqueConstraintFields, Id.run,\n'
        '    pure] at h'
    )


def _wit_must_reject(field, unique, cs, cs_indent):
    """Refute at a point the spec deems UNACCEPTABLE (clause 2)."""
    args = f'{field} {{ unique := {unique} }}\n    {cs}'
    return (
        f'example : ¬ problem_spec_inBulk {args}\n'
        f'    (implementation_inBulk {field} {{ unique := {unique} }}\n'
        f'      {cs}) := by\n'
        '  rintro ⟨-, herr⟩\n'
        f'  have hnacc : ¬ fieldNameAcceptable {field} {{ unique := {unique} }}\n'
        f'      {cs_indent} := by\n'
        '    unfold fieldNameAcceptable; decide\n'
        '  have h := herr hnacc\n'
        '  simp [implementation_inBulk, singleFieldUniqueConstraintFields, Id.run,\n'
        '    pure] at h'
    )


# The seven input points the witnesses probe. Chosen so that every INPUT BINDER
# of `problem_spec_inBulk` is VARIED across the reject lane rather than held at
# one value — a binder every witness pinned would be a binder no rival was built
# to abuse:
#   fieldName : "year" / "a" / "ean" / "brand" / "slug" / "pk" / "author"
#             — including the "pk" literal itself, the only value the first
#               disjunct fires on.
#   fld.unique : false on six, TRUE on `_P_UNIQUE` — the only point where the
#             second disjunct is what accepts, so the rival that ignores it is
#             refuted where nothing else could catch it.
#   cs : empty; one single-field unconditional; one single-field CONDITIONAL;
#             one MULTI-field unconditional; a two-element list whose permitting
#             member is NOT first; and a two-element mixed-shape list. So the
#             list's length, its element ORDER, and both record fields of its
#             elements all move.
_P_YEAR = '[{ fields := ["year"], isPartial := false }]'
_P_NOT_FIRST = ('[{ fields := ["b", "c"], isPartial := false },\n'
                '      { fields := ["a"], isPartial := false }]')
_P_NOT_FIRST_I = ('[{ fields := ["b", "c"], isPartial := false },\n'
                  '        { fields := ["a"], isPartial := false }]')
_P_PARTIAL = '[{ fields := ["ean"], isPartial := true }]'
_P_COMPOSITE = ('[{ fields := ["brand", "name"], isPartial := false },\n'
                '      { fields := ["ean"], isPartial := true }]')
_P_COMPOSITE_I = ('[{ fields := ["brand", "name"], isPartial := false },\n'
                  '        { fields := ["ean"], isPartial := true }]')
_P_EMPTY = '([] : List UniqueConstraint)'
# A MULTI-field unconditional constraint queried at its NON-HEAD member. Distinct
# from _P_COMPOSITE, which is queried at the HEAD: the head is what a
# `headD ""` projection yields, so a rival that scans the whole `fields` tuple
# instead of requiring arity 1 agrees with the frozen impl at the head and
# diverges only here. See `uniq-any-member-of-multi`.
_P_MULTI_TAIL = '[{ fields := ["brand", "name"], isPartial := false }]'


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================
#
# Both are CORRECT impls that are NOT definitionally the frozen one, so the
# frozen tactic body does NOT close them and each has to discharge the
# byte-identical obligation from a genuinely new shape. Neither weakens the
# obligation, adds a lemma, or reaches for an assumption token.

# (P1) The cheapest honest CORRECT impl: state the acceptability decision
# DIRECTLY as a `cs.any` existential, with no `let`, no `Id.run do` scaffold and
# no early return — maximally structurally different from the frozen
# filter-map-then-membership shape. This is nagini's `pos-control-direct-oracle`
# ported: there the direct impl returns the pin's own fold, here it returns the
# decidable reflection of the spec's own existential. It is CORRECT, not an
# ungrounded echo, because the existential IS the real work — resolving which
# constraints guarantee uniqueness for a single named field is the whole
# computation, so spelling it out is doing it. The proof establishes the
# reflection `(… || … || cs.any …) = true ↔ fieldNameAcceptable …` once and
# discharges both clauses by `if_pos` / `if_neg`.
_POS_ANY_IMPL = (
    'def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :\n'
    '    Except String Unit :=\n'
    '  if fieldName == "pk" || fld.unique ||\n'
    '      cs.any (fun c => !c.isPartial && c.fields == [fieldName]) then\n'
    '    Except.ok ()\n'
    '  else\n'
    '    Except.error fieldName'
)
_POS_ANY_PROOF = (
    '  intro fieldName fld cs\n'
    '  have key : (fieldName == "pk" || fld.unique ||\n'
    '      cs.any (fun c => !c.isPartial && c.fields == [fieldName])) = true\n'
    '      ↔ fieldNameAcceptable fieldName fld cs := by\n'
    '    unfold fieldNameAcceptable\n'
    '    simp only [Bool.or_eq_true, beq_iff_eq, List.any_eq_true, Bool.and_eq_true,\n'
    "      Bool.not_eq_true', decide_eq_true_eq]\n"
    '    tauto\n'
    '  unfold problem_spec_inBulk implementation_inBulk\n'
    '  refine ⟨?_, ?_⟩\n'
    '  · intro hacc\n'
    '    rw [if_pos (key.mpr hacc)]\n'
    '  · intro hnacc\n'
    '    rw [if_neg (fun h => hnacc (key.mp h))]'
)
_POS_ANY = _reproved(_swap(_BASE, _GOLD_DEF, _POS_ANY_IMPL), _POS_ANY_PROOF)

# (P2) Structurally-different but CORRECT: the three conjuncts of the rejection
# guard are REORDERED (the field's own uniqueness flag is tested first, the
# primary-key short-circuit last). `&&` is commutative on `Bool` and all three
# conjuncts are total, so the reorder is behaviour-preserving on every input —
# but it is NOT definitionally the frozen guard, so the frozen tactic body's
# `hcond` bridge no longer typechecks and the obligation is reproven with the
# conjuncts destructured in the new order. This is nagini's
# `pos-control-reorder-branches` ported, with the commutation moved onto the
# guard's conjuncts. (Nagini's literal shape — negate the guard and swap the two
# result branches — is ALSO expressible on this impl and also verifies, so it is
# not that there are "no branches to swap"; the conjunct commutation holds this
# slot because it KEEPS the frozen `Id.run do` early-return scaffold, so between
# them the two positives vary the scaffold and the guard independently instead of
# both dropping it.) If either positive failed to verify, the spec would be
# over-fit to the frozen code shape => SPEC-TOO-STRONG.
_POS_REORDER_IMPL = (
    '  let uniqueFields := singleFieldUniqueConstraintFields cs\n'
    '  if !fld.unique && !(uniqueFields.contains fieldName) && fieldName != "pk" then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)
_POS_REORDER_PROOF = (
    '  intro fieldName fld cs\n'
    '  have hmem : (singleFieldUniqueConstraintFields cs).contains fieldName = true ↔\n'
    '      (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName]) := by\n'
    '    unfold singleFieldUniqueConstraintFields\n'
    '    simp only [List.contains_eq_mem, decide_eq_true_eq, List.mem_map, List.mem_filter,\n'
    "      Bool.and_eq_true, Bool.not_eq_true', beq_iff_eq]\n"
    '    constructor\n'
    '    · rintro ⟨c, ⟨hcmem, hpart, hlen⟩, rfl⟩\n'
    '      refine ⟨c, hcmem, ?_, ?_⟩\n'
    '      · simpa using hpart\n'
    '      · rw [List.length_eq_one_iff] at hlen\n'
    '        obtain ⟨a, ha⟩ := hlen\n'
    '        rw [ha]; simp [List.headD]\n'
    '    · rintro ⟨c, hcmem, hpart, hfields⟩\n'
    '      refine ⟨c, ⟨hcmem, ?_, ?_⟩, ?_⟩\n'
    '      · simp [hpart]\n'
    '      · rw [hfields]; rfl\n'
    '      · rw [hfields]; rfl\n'
    '  have hcond : (!fld.unique &&\n'
    '        !(singleFieldUniqueConstraintFields cs).contains fieldName &&\n'
    '        fieldName != "pk") = true\n'
    '      ↔ ¬ fieldNameAcceptable fieldName fld cs := by\n'
    '    unfold fieldNameAcceptable\n'
    "    simp only [Bool.and_eq_true, bne_iff_ne, ne_eq, Bool.not_eq_true', Bool.not_eq_true,\n"
    '      not_or]\n'
    '    rw [← hmem]\n'
    '    constructor\n'
    '    · rintro ⟨⟨hu, hc⟩, hpk⟩\n'
    '      refine ⟨hpk, ?_, ?_⟩\n'
    '      · simp [hu]\n'
    '      · rw [List.contains_eq_mem] at hc; simpa using hc\n'
    '    · rintro ⟨hpk, hu, hc⟩\n'
    '      refine ⟨⟨?_, ?_⟩, hpk⟩\n'
    '      · simpa using hu\n'
    '      · rw [List.contains_eq_mem]; simpa using hc\n'
    '  unfold problem_spec_inBulk implementation_inBulk\n'
    '  simp only [Id.run, bind, pure]\n'
    '  constructor\n'
    '  · intro hacc\n'
    '    rw [if_neg]\n'
    '    intro h\n'
    '    exact (hcond.mp h) hacc\n'
    '  · intro hnacc\n'
    '    rw [if_pos (hcond.mpr hnacc)]'
)
_POS_REORDER = _reproved(_swap(_BASE, _GOLD_BODY, _POS_REORDER_IMPL),
                         _POS_REORDER_PROOF)


# ===========================================================================
# ADMISSIBILITY (non-vacuity at a normal input) — expect "verify"
# ===========================================================================
#
# The frozen obligation carries NO precondition hypothesis, so nothing here can
# fail to establish a `Requires` the way nagini's self-call can. What CAN still
# go wrong on a total carrier, and is what this lane exists to detect, is the
# obligation being UNSATISFIABLE at exactly a normal, F2P-shaped input: a
# postcondition that no impl can meet there is a spec nobody can discharge for
# the very call the change is about, and every other case in this battery would
# still behave as declared. So the ground instance is discharged BY EVALUATION,
# as a `have` prepended to the frozen tactic body, and then the frozen obligation
# is closed verbatim — the statement is untouched, no declaration is added, and
# nothing is assumed.
#
# The input is the F2P shape: a non-primary-key field, NOT itself declared
# unique, that is the sole field of a single unconditional constraint — i.e. the
# point at which acceptance is due to the third disjunct alone and to nothing
# else. `rfl` closes the accept clause by computation and the reject clause is
# closed by `decide` refuting its own hypothesis, so no part of the `have` leans
# on the frozen proof's lemmas.
_ADMISS_GROUND = (
    '  have _ground : problem_spec_inBulk "year" { unique := false }\n'
    '      [{ fields := ["year"], isPartial := false }]\n'
    '      (implementation_inBulk "year" { unique := false }\n'
    '        [{ fields := ["year"], isPartial := false }]) := by\n'
    '    constructor\n'
    '    · intro _\n'
    '      rfl\n'
    '    · intro hnacc\n'
    '      exact absurd (by unfold fieldNameAcceptable; decide) hnacc\n'
)
_ADMISS = _swap(_BASE, _OBLIGATION_STMT + ' := by\n',
                _OBLIGATION_STMT + ' := by\n' + _ADMISS_GROUND)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (R1) Ignore the declared constraint set ENTIRELY — the exact pre-change
# behaviour. nagini's `partial-ignore-guarantees` ported.
_R_IGNORE_CS = (
    '  if fieldName != "pk" && !fld.unique then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R2) Consult only the FIRST declared constraint. nagini's
# `partial-first-guarantee-only` ported.
_R_FIRST_ONLY = (
    '  let uniqueFields := singleFieldUniqueConstraintFields (cs.take 1)\n'
    '  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R3) Drop the "applies to every row" requirement: treat a CONDITIONAL/partial
# constraint as if it guaranteed uniqueness. nagini's
# `weak-ignore-unconditional` ported.
_R_IGNORE_PARTIAL = (
    '  let uniqueFields := (cs.filter (fun c => c.fields.length == 1)).map (fun c => c.fields.headD "")\n'
    '  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R4) Drop the ARITY requirement: treat the first member of a multi-field
# constraint as covered. nagini's `weak-ignore-arity` ported.
_R_IGNORE_ARITY = (
    '  let uniqueFields := (cs.filter (fun c => !c.isPartial)).map (fun c => c.fields.headD "")\n'
    '  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R5) Drop the field's OWN uniqueness declaration from the guard — no nagini
# counterpart, it attacks the second disjunct.
_R_IGNORE_UNIQUE = (
    '  let uniqueFields := singleFieldUniqueConstraintFields cs\n'
    '  if fieldName != "pk" && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R6) Drop the primary-key short-circuit — no nagini counterpart, it attacks
# the first disjunct.
_R_IGNORE_PK = (
    '  let uniqueFields := singleFieldUniqueConstraintFields cs\n'
    '  if !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R7) Right decision, WRONG reported payload — no nagini counterpart, whose
# carrier returns a bare Bool and so cannot express it.
_R_CONST_PAYLOAD = (
    '  let uniqueFields := singleFieldUniqueConstraintFields cs\n'
    '  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error ""\n'
    '  return Except.ok ()'
)

# (R8) Drop the arity requirement the OTHER way: instead of projecting each
# unconditional constraint's HEAD field name (R4), scan its WHOLE `fields` tuple,
# so ANY member of a multi-field constraint is treated as individually covered.
# R4 and R8 are separated by a real input, which is why both are needed: R4
# projects the head, so it wrongly accepts only the FIRST member and agrees with
# the frozen impl on every later one, while R8 wrongly accepts EVERY member. At
# `_P_COMPOSITE` (queried at the head) the two coincide; at `_P_MULTI_TAIL`
# (queried at a non-head member) R4 is CORRECT and only R8 diverges — so R4's
# witness does not refute R8 and this rival needs its own.
_R_ANY_MEMBER = (
    '  if fieldName != "pk" && !fld.unique &&\n'
    '      !(cs.any (fun c => !c.isPartial && c.fields.contains fieldName)) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)

# (R9) FORGE a permitting constraint: prepend a synthetic single-field
# unconditional constraint naming the queried field to the list before
# consulting it, so every field looks covered. This is the value-level shadow of
# nagini's mandatory frame case — there the forgery is a WRITE through a
# read-only reference, which referential transparency makes inexpressible; the
# observable half of that attack (does the spec pin the decision to the
# constraint list as GIVEN, or may an impl fabricate its own?) survives the port
# as a local rebinding and IS expressible. The decision is read off `forged`
# rather than `cs`, so the impl consults a constraint set the caller never
# declared; it accepts on every input and so also covers the "accept-all"
# degenerate shape.
_R_FORGE = (
    '  let forged := { fields := [fieldName], isPartial := false } :: cs\n'
    '  let uniqueFields := singleFieldUniqueConstraintFields forged\n'
    '  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then\n'
    '    return Except.error fieldName\n'
    '  return Except.ok ()'
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
    # Both reprove the byte-identical obligation from a new impl shape.
    # =====================================================================
    {
        "id": "pos-direct-existential",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ANY,
        "rationale": "the cheapest honest CORRECT impl: the acceptability decision is "
                     "stated directly as `fieldName == \"pk\" || fld.unique || cs.any "
                     "(fun c => !c.isPartial && c.fields == [fieldName])`, with the "
                     "`let`, the `Id.run do` scaffold and the early return all dropped "
                     "— maximally structurally different from the frozen "
                     "filter-map-then-membership shape. It must satisfy BOTH clauses of "
                     "problem_spec_inBulk on every input, else the spec is over-fit to "
                     "the frozen code shape (SPEC-TOO-STRONG). This is NOT an "
                     "ungrounded echo: the existential over `cs` IS the real work — "
                     "resolving which declared constraints guarantee uniqueness for one "
                     "named field is the whole computation — so spelling it out is "
                     "doing it, which is why nagini ships the same case as its "
                     "honest-direct control. NOT definitionally the frozen impl, so the "
                     "frozen tactic body does not close it; the obligation STATEMENT is "
                     "spliced back byte-identically and reproven via a single "
                     "reflection lemma plus `if_pos`/`if_neg`. No new theorem, lemma, "
                     "axiom, or assumption token.",
    },
    {
        "id": "pos-reorder-guard-conjuncts",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "structurally-different but CORRECT: the three conjuncts of the "
                     "rejection guard are reordered so the field's own uniqueness flag "
                     "is tested first and the primary-key short-circuit last. `&&` is "
                     "commutative on Bool and all three conjuncts are total, so the "
                     "value is identical on every input — but it is NOT definitionally "
                     "the frozen guard, so the frozen proof's bridging step no longer "
                     "typechecks and the same byte-identical obligation is reproven "
                     "with the conjuncts destructured in the new order. nagini's "
                     "branch-reorder control ported, with the commutation moved onto "
                     "the guard's conjuncts: nagini's literal branch swap (negate the "
                     "guard, exchange the two results) is also expressible here and also "
                     "verifies, so the conjunct form holds this slot because it KEEPS "
                     "the frozen early-return scaffold that pos-direct-existential "
                     "drops — between them the two positives vary the scaffold and the "
                     "guard independently. If it failed => the spec is over-fit to the "
                     "conjunct order (SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at a normal input.
    # =====================================================================
    {
        "id": "admiss-ground-constraint-field",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "non-vacuity at a normal, F2P-shaped input: the "
                     "postcondition is discharged BY EVALUATION at the concrete "
                     "point `fieldName = \"year\"`, `fld.unique = false`, `cs = "
                     "[{ fields := [\"year\"], isPartial := false }]` — a non-pk "
                     "field, not itself declared unique, that is the sole field of "
                     "one unconditional constraint, so acceptance is due to the "
                     "THIRD disjunct alone — as a `have` prepended to the frozen "
                     "tactic body, after which the byte-identical frozen "
                     "obligation is closed verbatim. This is nagini's "
                     "admissibility case ported to what the lane means on a total "
                     "carrier: there the self-call must establish a read-only "
                     "permission `Requires`, which referential transparency "
                     "removes; here the analogue of PRECOND-TOO-STRONG is the "
                     "obligation being UNSATISFIABLE at exactly the input the "
                     "change is about, which a ground discharge tests directly. "
                     "If it failed => the modeled behaviour cannot be met at a "
                     "normal input and every other case's verdict would be about "
                     "an unsatisfiable spec. Accept clause closed by `rfl` "
                     "(computation), reject clause by `decide` refuting its own "
                     "hypothesis, so the `have` borrows nothing from the frozen "
                     "proof's lemmas; statement byte-identical, no new "
                     "declaration, no assumption token.",
    },

    # =====================================================================
    # UNIQUENESS RIVALS — must be REJECTED, each with a witness verified to
    # elaborate against the rival and FAIL on the frozen solution.
    # =====================================================================
    {
        "id": "uniq-ignore-constraints",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_IGNORE_CS),
        "refinement": "this is the EXACT pre-change behaviour: the guard consults only "
                      "the primary-key test and the field's own uniqueness declaration, "
                      "never the model's declared unique constraints. Its faithful real "
                      "patch is the unpatched guard, which raises on a field that is the "
                      "sole field of an unconditional unique constraint — precisely the "
                      "FAIL_TO_PASS case (in_bulk keyed on such a field must now "
                      "succeed, and pre-change it raises). So it does NOT resolve.",
        "rationale": "REJECT from clause 1 (`fieldNameAcceptable → result = Except.ok "
                     "()`) via the THIRD disjunct of fieldNameAcceptable. Partial-domain: "
                     "correct on every field that is the primary key, is itself declared "
                     "unique, or is covered by no constraint; it diverges exactly on the "
                     "sub-domain the existential adds. At the witness point the "
                     "existential is satisfied — a single-field unconditional constraint "
                     "spans `\"year\"` — so the spec forces Except.ok () while the rival "
                     "returns Except.error. Attacks the constraint-list binder `cs`, "
                     "which this rival discards entirely. If it verified => "
                     "SPEC-TOO-WEAK (the spec admits the unpatched guard).",
        "witness": _wit_must_accept('"year"', 'false', _P_YEAR, _P_YEAR),
    },
    {
        "id": "uniq-first-constraint-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_FIRST_ONLY),
        "refinement": "a faithful real patch that inspected only the FIRST declared "
                      "constraint would accept a field only when its permitting "
                      "single-field constraint happens to be listed first. Declaration "
                      "order is arbitrary — a model may declare a multi-field constraint "
                      "before the single-field one — so such a patch would still raise "
                      "for the FAIL_TO_PASS field whenever the permitting constraint is "
                      "not first, and would NOT resolve.",
        "rationale": "REJECT from clause 1 via the existential's quantification over the "
                     "WHOLE list, which `cs.take 1` truncates. Partial-domain: correct "
                     "when the permitting constraint is at index 0 or none exists; "
                     "diverges when it sits later. This is a NEAR-MISS of "
                     "uniq-ignore-constraints — it agrees with the frozen impl over "
                     "strictly more of the domain (it does consult one constraint) — so "
                     "it gets its OWN witness at a two-element list whose permitting "
                     "single-field member is SECOND, the input that separates the two "
                     "rivals. Attacks the ORDER and LENGTH of the `cs` binder. If it "
                     "verified => SPEC-TOO-WEAK (admits a first-only scan).",
        "witness": _wit_must_accept('"a"', 'false', _P_NOT_FIRST, _P_NOT_FIRST_I),
    },
    {
        "id": "uniq-ignore-partial-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_IGNORE_PARTIAL),
        "refinement": "this drops the 'applies to every row' filter, treating a "
                      "conditional/partial unique constraint as if it guaranteed "
                      "uniqueness. A partial constraint only constrains the rows "
                      "matching its condition, so the field may repeat elsewhere and "
                      "keying a bulk mapping on it is unsound. The faithful patch would "
                      "ACCEPT a field covered only by such a constraint, breaking the "
                      "PASS_TO_PASS case that requires exactly that field to still be "
                      "rejected. So it does NOT resolve.",
        "rationale": "REJECT from clause 2 (`¬ fieldNameAcceptable → result = "
                     "Except.error fieldName`) via the existential's `c.isPartial = "
                     "false` conjunct. At the witness point the sole constraint is "
                     "single-field but CONDITIONAL, so the existential fails and the "
                     "spec forces an error, while the rival — whose filter keeps only "
                     "the arity test — reports acceptance. Attacks the `isPartial` "
                     "component of the `cs` binder, held false by every other witness. "
                     "If it verified => SPEC-TOO-WEAK (admits partial constraints as "
                     "uniqueness guarantees).",
        "witness": _wit_must_reject('"ean"', 'false', _P_PARTIAL, _P_PARTIAL),
    },
    {
        "id": "uniq-ignore-arity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_IGNORE_ARITY),
        "refinement": "this drops the arity filter, treating the first member of a "
                      "multi-field constraint as individually covered. A constraint "
                      "spanning several fields only makes the COMBINATION unique; each "
                      "member may repeat on its own. The faithful patch would ACCEPT "
                      "such a member as a bulk key, breaking the PASS_TO_PASS case that "
                      "requires a member of a multi-field constraint to still be "
                      "rejected. So it does NOT resolve.",
        "rationale": "REJECT from clause 2 via the existential's `c.fields = "
                     "[fieldName]` conjunct, which pins the constraint to span EXACTLY "
                     "this one field. At the witness point the queried field is the "
                     "FIRST member of a two-field unconditional constraint, so the "
                     "existential fails and the spec forces an error, while the rival — "
                     "which projects the head of every unconditional constraint "
                     "regardless of length — reports acceptance. Attacks the arity of "
                     "the `c.fields` component; the witness list additionally carries a "
                     "second, differently-shaped element so the rival cannot be refuted "
                     "by list length alone. If it verified => SPEC-TOO-WEAK (admits "
                     "multi-field constraints).",
        "witness": _wit_must_reject('"brand"', 'false', _P_COMPOSITE, _P_COMPOSITE_I),
    },
    {
        "id": "uniq-ignore-unique-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_IGNORE_UNIQUE),
        "refinement": "no nagini counterpart — this attacks UNCHANGED behaviour the "
                      "spec must still hold. A faithful patch that stopped honouring a "
                      "field's own uniqueness declaration would reject the long-standing "
                      "case of keying a bulk mapping on a field declared unique "
                      "directly, breaking the PASS_TO_PASS cases that key on exactly "
                      "such a field. It regresses behaviour orthogonal to the change, so "
                      "it does NOT resolve.",
        "rationale": "REJECT from clause 1 via the SECOND disjunct of "
                     "fieldNameAcceptable (`fld.unique = true`), which no other rival "
                     "attacks. This is the only witness that holds `fld.unique` at TRUE, "
                     "and it is stated with an EMPTY constraint list so the field's own "
                     "declaration is the sole reason the spec accepts — without this "
                     "case a rival mishandling that binder would verify and the battery "
                     "would never notice. If it verified => SPEC-TOO-WEAK (the "
                     "individually-unique disjunct is unenforced).",
        "witness": _wit_must_accept('"slug"', 'true', _P_EMPTY, _P_EMPTY),
    },
    {
        "id": "uniq-ignore-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_IGNORE_PK),
        "refinement": "no nagini counterpart — this too attacks UNCHANGED behaviour. A "
                      "faithful patch dropping the primary-key short-circuit would "
                      "reject the DEFAULT way of calling the method (keying on the "
                      "primary key, which needs no uniqueness declaration of its own and "
                      "for which the real code short-circuits before resolving the "
                      "field at all), breaking the baseline PASS_TO_PASS cases. So it "
                      "does NOT resolve.",
        "rationale": "REJECT from clause 1 via the FIRST disjunct of "
                     "fieldNameAcceptable (`fieldName = \"pk\"`), which no other rival "
                     "attacks. This is the only witness that instantiates `fieldName` at "
                     "the distinguished `\"pk\"` literal — the single value on which that "
                     "disjunct fires — with the other two disjuncts both false (unique "
                     "flag false, constraint list empty), so the primary-key case is the "
                     "sole reason the spec accepts. If it verified => SPEC-TOO-WEAK (the "
                     "primary-key disjunct is unenforced).",
        "witness": _wit_must_accept('"pk"', 'false', _P_EMPTY, _P_EMPTY),
    },
    {
        "id": "uniq-wrong-error-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_CONST_PAYLOAD),
        "refinement": "no nagini counterpart: that carrier returns a bare Bool, so the "
                      "reported payload is outside its abstraction entirely. A faithful "
                      "patch that reported a constant instead of the offending field "
                      "name would raise with the wrong message, and the PASS_TO_PASS "
                      "rejection cases assert on the message TEXT — which embeds the "
                      "field name — not merely on the fact that an error was raised. So "
                      "it does NOT resolve.",
        "rationale": "REJECT from the PAYLOAD half of clause 2 (`result = Except.error "
                     "fieldName`, not merely `∃ e, result = Except.error e`). This rival "
                     "gets the accept/reject DECISION right on every single input — it "
                     "is the frozen guard verbatim — and is caught only because the "
                     "second clause pins which field the error names. At the witness "
                     "point no disjunct holds (non-pk name, unique flag false, empty "
                     "constraint list) so both the frozen impl and the rival reject, and "
                     "the refutation turns purely on the payload. If it verified => "
                     "SPEC-TOO-WEAK (the error payload is unconstrained, the analogue of "
                     "leaving an output component unpinned).",
        "witness": _wit_must_reject('"author"', 'false', _P_EMPTY, _P_EMPTY),
    },
    {
        "id": "uniq-any-member-of-multi",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_ANY_MEMBER),
        "refinement": "a faithful patch that asked whether the field appears ANYWHERE "
                      "among an unconditional constraint's fields, rather than whether "
                      "that constraint spans exactly that one field, would accept every "
                      "member of a multi-field constraint as a bulk key. A constraint over "
                      "several fields makes only the COMBINATION unique, so each member "
                      "may repeat on its own and the mapping would silently lose rows. It "
                      "breaks the PASS_TO_PASS case that requires a member of a "
                      "multi-field constraint to still be rejected, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from clause 2 via the existential's `c.fields = [fieldName]` "
                     "conjunct, attacked from the side `uniq-ignore-arity` leaves open. "
                     "That rival drops the arity FILTER but keeps the head projection, so "
                     "it over-accepts only a constraint's FIRST member and is correct on "
                     "every later one; this rival scans the whole tuple and over-accepts "
                     "EVERY member. The two are therefore separated by a real input, and "
                     "the arity witness (stated at the HEAD member `\"brand\"`) does not "
                     "refute this one: at that point both rivals agree with each other. "
                     "So the witness here is stated at the NON-HEAD member `\"name\"` of a "
                     "two-field unconditional constraint — a point where the frozen impl "
                     "and uniq-ignore-arity BOTH reject and only this rival accepts, which "
                     "is what makes it the input that discriminates. If it verified => "
                     "SPEC-TOO-WEAK (the arity clause pins only the first member).",
        "witness": _wit_must_reject('"name"', 'false', _P_MULTI_TAIL, _P_MULTI_TAIL),
    },
    {
        "id": "uniq-forge-constraint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _R_FORGE),
        "refinement": "no faithful patch corresponds to fabricating a constraint the "
                      "model never declared: the guard READS the model's declared "
                      "constraints, and a patch that manufactured a single-field "
                      "unconditional constraint for whatever field was asked about would "
                      "accept every field name — abandoning the check entirely and "
                      "breaking every PASS_TO_PASS rejection case. So it does NOT resolve.",
        "rationale": "REJECT from clause 2, and the case that pins the decision to the "
                     "constraint list AS GIVEN: the rival consults `forged` — the input "
                     "list with a synthetic permitting constraint prepended — rather than "
                     "`cs` itself, so the existential is satisfied for every field name "
                     "and it accepts unconditionally. This is the value-level shadow of "
                     "nagini's mandatory frame/permission case, whose ARGUMENT (may an "
                     "impl satisfy the postcondition by manufacturing its own "
                     "uniqueness evidence?) ports even though its MECHANICS — a write "
                     "through a read-only fractional reference — do not; the port "
                     "originally recorded the whole lane as vacuous, which is right about "
                     "the write and wrong about the observable attack. The witness point "
                     "carries a single PARTIAL constraint on an unrelated field, so `cs` "
                     "is non-empty yet permits nothing and the acceptance is attributable "
                     "purely to the forgery. If it verified => SPEC-TOO-WEAK (the spec "
                     "would not pin the decision to the declared constraint set).",
        "witness": _wit_must_reject('"title"', 'false', _P_PARTIAL, _P_PARTIAL),
    },
]


# ===========================================================================
# PORT ACCOUNTING — nagini case -> lean disposition
# ===========================================================================
#
#   nagini case                     | lean disposition
#   --------------------------------+--------------------------------------------
#   pos-control-direct-oracle       | PORTED as pos-direct-existential
#   pos-control-reorder-branches    | PORTED as pos-reorder-guard-conjuncts
#                                   |   (the commutation moved onto the guard's
#                                   |    conjuncts, which KEEPS the frozen
#                                   |    early-return scaffold that
#                                   |    pos-direct-existential drops. Nagini's
#                                   |    literal branch swap — negate the guard,
#                                   |    exchange the two results — is expressible
#                                   |    here too and also verifies, so it is not
#                                   |    that there are no branches to swap;
#                                   |    between the two positives the scaffold
#                                   |    and the guard vary independently.)
#   partial-ignore-guarantees       | PORTED as uniq-ignore-constraints
#   partial-first-guarantee-only    | PORTED as uniq-first-constraint-only
#   weak-ignore-unconditional       | PORTED as uniq-ignore-partial-flag
#   weak-ignore-arity               | PORTED as uniq-ignore-arity
#   frame-mutate-guarantees         | PORTED IN PART as uniq-forge-constraint.
#                                   |   The mechanical half (a WRITE through a
#                                   |   read-only fractional reference, rejected
#                                   |   by the permission system) is inexpressible
#                                   |   under referential transparency. The
#                                   |   observable half — an impl manufacturing
#                                   |   its own uniqueness evidence rather than
#                                   |   reading the declared set — is expressible
#                                   |   as a local rebinding, and is shipped.
#   admiss-meta-constraint          | PORTED as admiss-ground-constraint-field.
#                                   |   The MECHANICAL half (a self-call
#                                   |   establishing a read-only fractional
#                                   |   permission `Requires`) is inexpressible:
#                                   |   the lean obligation carries no
#                                   |   precondition hypothesis at all. What the
#                                   |   lane detects on a total carrier — the
#                                   |   obligation being UNSATISFIABLE at exactly
#                                   |   an F2P-shaped input — IS expressible, and
#                                   |   is shipped as a ground discharge at that
#                                   |   input followed by the frozen obligation
#                                   |   verbatim.
#   AXIOM_TESTS (ax-ref-sound,      | DROPPED — the axiom lane is G-AX's job and
#     ax-containment)               |   this gate ignores AXIOM_TESTS.
#
# ADDED here, with no nagini counterpart, because this carrier models more than
# nagini's bare Bool and every disjunct/clause must be attacked:
#   uniq-ignore-unique-flag   — the second disjunct (the field's own declaration)
#   uniq-ignore-pk            — the first disjunct (the primary-key case)
#   uniq-wrong-error-payload  — the error PAYLOAD, which a Bool cannot express
#   uniq-any-member-of-multi  — the arity clause attacked at a NON-HEAD member,
#                               the side uniq-ignore-arity's head projection
#                               leaves correct (the two rivals are separated by
#                               that input, so neither witness refutes the other)
#
# No divergence / non-termination case exists in the nagini sibling, and none is
# expressible here: `implementation_inBulk` is a total Lean `def`. On lean this
# class is genuinely VACUOUS (contrast velvet under partial termination
# semantics, where it is a known spec hole — the corpus-wide termination-semantics finding).
