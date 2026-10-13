# properties.py — G-PBT falsification battery for django__django-14631 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for the positives that reprove, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   cleanFields : List FieldModel → List FieldValue
#   A form is an ordered collection of fields; each field carries four inputs:
#     disabled, supportsMicro, rawInitial, data. The single postcondition
#     `problem_spec_cleanFields fields result` pins the WHOLE output structure:
#       result = fields.map cleanedValue
#     where cleanedValue f = (if f.disabled then boundInitial f else f.data) and
#       boundInitial f = (for a temporal rawInitial `ts whole sub`:
#                           if f.supportsMicro then `ts whole sub` else `ts whole 0`;
#                         a non-temporal rawInitial is presented unchanged).
#   This one clause has three independent, fully-transparent sub-clauses, each
#   attackable on its own:
#     (C1) SELECTION per field: a disabled field contributes its presented initial
#          value; an editable field contributes its submitted value. Both
#          directions are pinned — a rival that uses the wrong source on EITHER
#          kind of field fails C1.
#     (C2) PRESENTATION of the initial value: the sub-second component of a
#          temporal initial value is dropped IFF the field's display cannot
#          represent sub-second precision, and is retained otherwise. Both
#          directions are pinned — dropping when it should be kept, or keeping when
#          it should be dropped, fails C2.
#     (C3) STRUCTURE of the output: exactly one entry per field, in field order
#          (`.map` over the input list). A rival that reorders or drops entries
#          fails C3.
#   FieldValue / FieldModel are concrete inductives with DecidableEq and there is
#   no opaque callee or answer-key, so every predicate reduces at a concrete
#   literal input: witnesses need no conditioning on the carrier — `decide` closes
#   the disequality after unfolding the spec.
#
# CARRIER NOTE / relation to the nagini sibling. Nagini modeled a SINGLE field's
# cleaned value, `clean_bound_initial_field(fs) -> int`, over a scalar carrier
# (`fs.first_eval`, `fs.fresh_eval`) with fractional read permissions and a
# MustTerminate obligation. This backend models the richer, referentially
# transparent object the F2P actually exercises: the per-field selection loop over
# a `List FieldModel`, with the presentation step spelled out DEEPLY as
# `boundInitial`. So:
#   * nagini's normalisation rival (`_UNNORMALISED`: return the first evaluation
#     WITHOUT the sub-second strip) ports directly onto clause C2 as `no-strip`
#     — that IS the modeled F2P discriminator per mapping.md (aspect 1: the
#     microsecond strip). It is the primary carry-over.
#   * the lean carrier ADDS structure the nagini scalar model had no binder for —
#     the disabled/editable SELECTION fork (C1) and the field-order TRAVERSAL (C3)
#     — so this battery additionally attacks those with rivals that have no nagini
#     counterpart (`always-data`, `always-initial`, `reverse`). This is carrier
#     widening, not parity-chasing.
# Every reject witness probes a DISTINCT FieldModel shape so all four field binders
# (disabled, supportsMicro, rawInitial/data) and the list length are exercised.
# AUDIT ADDITION: the five ported rivals all attack a clause form-wide or at a single
# field, and an audit sweep of new wrong impls found two shapes that survived all five
# witnesses — a selection fork made conditional on the initial value's CONSTRUCTOR,
# and a presentation guard HOISTED out of the per-field loop. Both are now rivals
# (`nontemporal-disabled-takes-data`, `head-micro-contamination`), so the battery
# additionally pins that each clause is read PER FIELD and independently of the
# value's kind. Both were measured to be rejected with discriminating witnesses.
# SECOND AUDIT ADDITION: an independent sweep found two FURTHER wrong impls that
# survived the seven-rival battery, both about WHERE clause C2 applies rather than
# whether it holds:
#   * `tail-micro-contamination` — the presentation guard hoisted out of the loop but
#     read from the LAST field. The head-hoisted rival's witness carried a ZERO
#     sub-second component on its first field, so it pinned only the second field's
#     presentation; the tail-hoisted rival was gold-like on it (measured, build exit 1).
#     Fixed on both sides: that witness literal is now non-zero on both fields, AND the
#     mirror rival ships.
#   * `data-also-presented` — the presentation applied to the SUBMITTED value too, not
#     only to the preset initial. Every previously shipped witness carries a
#     NON-temporal `data`, so this rival was gold-like on all seven (measured).
# The admissibility lane, previously recorded N/A, now ships as
# `admiss-f2p-shaped-form`; see the ADMISSIBILITY note below for why the old reason
# was insufficient.
#
# NAGINI CASES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * RE-EVALUATION rivals (nagini `pre-patch-fresh-reeval`,
#     `dead-fresh-reeval-then-correct`, `partial-domain-max-mix`): all attack
#     aspect (2) of the fix — that the initial value is computed exactly once and a
#     stateful callable source is not re-evaluated. mapping.md records that aspect
#     (2) is a temporal/side-effect property and is NOT separately modeled here
#     (the microsecond discriminator already separates patched from pre-patch on
#     this carrier). On a referentially-transparent Lean carrier `rawInitial` is a
#     value input, not a callable, so "re-evaluate the source" collapses into
#     "read the same value again" and is indistinguishable from gold — there is no
#     witness that discriminates. These rivals are dropped as NOT-WRONG-ON-CARRIER.
#   * FRAME-MUTATION (nagini `frame-mutate-first-eval`: overwrite the read-only
#     `fs.first_eval` under half-permission). Lean is referentially transparent —
#     no aliasing, no fractional permission — so a "store into a read-only input"
#     rival is not expressible; the lane is VACUOUS here.
#   * DIVERGENCE / NON-TERMINATION (nagini `weak-diverge-reject`, rejected there by
#     MustTerminate(2)). CORRECTED BY AUDIT — the earlier note here claimed "a
#     non-terminating implementation cannot be written at all", which is not true on
#     this backend and was not measured. A diverging impl IS expressible as
#     `partial def spinForever (fields : List FieldModel) : List FieldValue :=
#     spinForever fields` with the obligation delegated to it, and it passes
#     variant_scope cleanly. What the audit measured is that the lane still has
#     nothing to ship, for a DIFFERENT and stronger reason: this backend takes the
#     obligation at face value, so the divergent impl is REJECTED on its own build
#     (`simp made no progress` — the goal `spinForever fields = fields.map
#     cleanedValue` is not provable, since a `partial def` is opaque to the kernel
#     and no equation makes it reduce). It is rejected for the right reason, and no
#     WITNESS can be built for it either: `decide` against the rival gets stuck
#     (`instDecidableNot did not reduce to isTrue or isFalse`) precisely because the
#     partial term is irreducible, which pbt_gate screens as `witness-undecided`. So
#     a reject case here could never be recorded as sound. Lane carries no rival:
#     expressible, already rejected, and not witnessable. This is NOT the
#     velvet-`partial` known spec hole (the corpus-wide termination-semantics finding), which is a
#     property of `loom.semantics.termination "partial"` — plain lean has no such
#     vacuous-verification setting, as the measured rejection above shows.
#   * ADMISSIBILITY (nagini `admiss-f2p-shaped-input`, which defended the
#     half-permission Requires). NOT DROPPED — the lane is now carried as
#     `admiss-f2p-shaped-form`. An earlier pass recorded it N/A because the lean
#     obligation is `∀ (fields : List FieldModel), problem_spec_cleanFields fields
#     (implementation_cleanFields fields)` with NO precondition hypothesis, so
#     "nothing can be PRECOND-TOO-STRONG". That reason is insufficient: on a total
#     carrier the analogue is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, which no amount of abstract `∀`-shape rules out. The lane is
#     tested directly by discharging the spec predicate BY EVALUATION at a concrete
#     F2P-shaped form as a `have`, before closing the frozen obligation verbatim.
#   * AXIOM_TESTS (nagini had none; meta.axioms == []). The presentation step is
#     modeled DEEPLY (boundInitial), so there is no consumed axiom, and the axiom
#     lane is G-AX's job regardless.
from pathlib import Path

INSTANCE = "django__django-14631"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value := if f.disabled then boundInitial f else f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (everything strictly inside proof-start/proof-end). Swapped
# only by positives whose different impl shape needs an (equally cheap, honest)
# reproof of the byte-identical `correct_cleanFields` statement.
_PROOF = _BASE[
    _BASE.index("-- proof-start\n") + len("-- proof-start\n") : _BASE.index("-- proof-end")
]
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

# The opening two lines of the frozen `correct_cleanFields` tactic body. The
# admissibility case PREPENDS a ground `have` here and then closes the frozen
# obligation verbatim, so the statement stays byte-identical and no declaration
# is added.
_P_INTRO = (
    "  intro fields\n"
    "  unfold problem_spec_cleanFields implementation_cleanFields"
)
assert _BASE.count(_P_INTRO) == 1, "proof-intro anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-pure-map: a structurally DIFFERENT but behaviourally identical impl written as
# a pure `List.map` (no `Id.run do`, no `let mut`, no early return, no accumulator
# loop). The per-field selection is inlined into the mapped function, so the output
# equals the frozen impl's on every input. The `correct_cleanFields` statement is
# byte-identical; its proof is reproven honestly (`unfold … ; simp [cleanedValue]`)
# — no new axiom/lemma/sorry, just the cheapest tactic for the map shape. If it
# FAILS => SPEC-TOO-STRONG (postcondition over-fit to the monadic loop shape).
_POS_MAP = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_cleanFields (fields : List FieldModel) : List FieldValue :=\n"
        "  fields.map (fun f => if f.disabled then boundInitial f else f.data)",
    ),
    _PROOF,
    "theorem correct_cleanFields :\n"
    "    ∀ (fields : List FieldModel),\n"
    "      problem_spec_cleanFields fields (implementation_cleanFields fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_cleanFields implementation_cleanFields\n"
    "  simp [cleanedValue]\n",
)

# pos-cleanedValue-call: keeps the imperative accumulator loop but selects each
# field's value by calling the shared `cleanedValue` helper instead of inlining the
# `if f.disabled …` expression. Behaviourally identical on every input. The theorem
# statement is byte-identical; the frozen proof's helper lemma is restated over
# `cleanedValue f` (the definitionally-equal body) and closes with the same tactics
# — no new axiom, no sorry. If it FAILS => SPEC-TOO-STRONG.
_POS_CALL = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
        "  let mut cleaned : List FieldValue := []\n"
        "  for f in fields do\n"
        "    let value := cleanedValue f\n"
        "    cleaned := cleaned ++ [value]\n"
        "  return cleaned",
    ),
    _PROOF,
    "theorem helper_cleanFields (fields : List FieldModel) :\n"
    "    ∀ (init : List FieldValue),\n"
    "      Id.run (forIn fields init (fun f r =>\n"
    "        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [cleanedValue f]))))) =\n"
    "      init ++ fields.map cleanedValue := by\n"
    "  induction fields with\n"
    "  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl\n"
    "  | cons a as ih =>\n"
    "    intro init\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind, pure] at ih ⊢\n"
    "    rw [ih]\n"
    "    simp only [List.map_cons, List.append_assoc, List.cons_append, List.nil_append]\n"
    "\n"
    "theorem correct_cleanFields :\n"
    "    ∀ (fields : List FieldModel),\n"
    "      problem_spec_cleanFields fields (implementation_cleanFields fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_cleanFields implementation_cleanFields\n"
    "  simp only [Id.run, bind, pure]\n"
    "  have h := helper_cleanFields fields []\n"
    "  simp only [Id.run, bind, pure] at h\n"
    "  rw [h]\n"
    "  simp\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# no-strip: a disabled field contributes its RAW initial value directly, skipping the
# presentation step. Correct whenever the initial value has no sub-second component
# (or the field supports sub-second precision), WRONG on a disabled temporal field
# with a non-zero sub-second component whose display cannot represent it — the exact
# F2P discriminator (mapping.md aspect 1). The direct port of nagini's `_UNNORMALISED`.
_RIV_NOSTRIP = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value := if f.disabled then f.rawInitial else f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned",
)

# always-strip: the DUAL presentation error — always drops the sub-second component of
# a temporal initial value, even for a field whose display CAN represent it. Correct on
# non-supporting fields, WRONG whenever the field supports sub-second precision and the
# initial value carries one. Attacks clause C2 in the retain direction.
_RIV_ALWAYSSTRIP = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value :=\n"
    "      if f.disabled then\n"
    "        (match f.rawInitial with\n"
    "         | FieldValue.ts w _ => FieldValue.ts w 0\n"
    "         | FieldValue.other n => FieldValue.other n)\n"
    "      else f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned",
)

# always-data: ignores the disabled/editable SELECTION fork and always contributes the
# submitted value. Correct on editable fields, WRONG on a disabled field whose
# presented initial value differs from its submitted value. Attacks clause C1 in the
# disabled direction.
_RIV_ALWAYSDATA = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    cleaned := cleaned ++ [f.data]\n"
    "  return cleaned",
)

# always-initial: the DUAL selection error — always contributes the presented initial
# value, ignoring the submitted value even on editable fields. Correct on disabled
# fields, WRONG on an editable field whose submitted value differs from its initial.
# Attacks clause C1 in the editable direction.
_RIV_ALWAYSINIT = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    cleaned := cleaned ++ [boundInitial f]\n"
    "  return cleaned",
)

# nontemporal-disabled-takes-data: ADDED BY AUDIT. Honours the disabled/editable fork
# only when the field's initial value is TEMPORAL; a disabled field holding a
# non-temporal initial wrongly takes the submitted value. Correct on every input the
# other five rivals' witnesses probe that has a temporal initial, so it survives the
# battery as ported. WRONG on a disabled field whose initial is non-temporal and
# differs from its submitted value. Attacks C1 restricted to the sub-domain the spec
# reaches through `boundInitial`'s `other` arm — the arm no other rival's witness
# discriminates at (the two C1 witnesses both use `other` initials but neither makes
# the selection fork depend on the value's CONSTRUCTOR).
_RIV_NONTEMPORAL = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value :=\n"
    "      match f.rawInitial with\n"
    "      | FieldValue.ts _ _ => if f.disabled then boundInitial f else f.data\n"
    "      | FieldValue.other _ => f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned",
)

# head-micro-contamination: ADDED BY AUDIT. Presents EVERY field's temporal initial at
# the precision of the FIRST field's display instead of at its own. Behaviourally
# identical to gold on every single-field form, and on every multi-field form whose
# fields AGREE on supportsMicro — which is every input the five ported witnesses probe
# (four are length 1; the one length-2 witness holds supportsMicro=true on both
# fields). So this rival passes the battery as ported while violating the spec. WRONG
# on a two-field form whose fields DISAGREE on supportsMicro. Attacks the per-field
# INDEPENDENCE of clause C2 — that the presentation guard is read from the field being
# presented, which `.map cleanedValue` pins but no existing rival tests.
_RIV_HEADMICRO = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let headMicro : Bool := match fields with\n"
    "    | [] => true\n"
    "    | g :: _ => g.supportsMicro\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value :=\n"
    "      if f.disabled then\n"
    "        (match f.rawInitial with\n"
    "         | FieldValue.ts w s => if headMicro then FieldValue.ts w s else FieldValue.ts w 0\n"
    "         | FieldValue.other n => FieldValue.other n)\n"
    "      else f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned",
)

# tail-micro-contamination: ADDED BY THE SECOND AUDIT. The mirror image of
# head-micro-contamination — it hoists the presentation guard out of the per-field loop
# too, but reads it from the LAST field instead of the first. The earlier audit's
# head-micro witness holds `ts 1 0` on its first field (a temporal initial with a ZERO
# sub-second component), so on that input the first field's entry is `ts 1 0` under
# every hoisting direction and the witness only pins the SECOND field — which this
# rival presents at the second field's own (non-supporting) precision, exactly as gold
# does. Measured: this rival survives the shipped head-micro witness (build exit 1,
# i.e. gold-like) and every other shipped witness. WRONG on a two-field form whose
# fields disagree on supportsMicro AND whose FIRST field carries a non-zero sub-second
# component. Attacks the same per-field independence of C2 from the other side.
_RIV_TAILMICRO = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let tailMicro : Bool := match fields.reverse with\n"
    "    | [] => true\n"
    "    | g :: _ => g.supportsMicro\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value :=\n"
    "      if f.disabled then\n"
    "        (match f.rawInitial with\n"
    "         | FieldValue.ts w s => if tailMicro then FieldValue.ts w s else FieldValue.ts w 0\n"
    "         | FieldValue.other n => FieldValue.other n)\n"
    "      else f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned",
)

# data-also-presented: ADDED BY THE SECOND AUDIT. Applies the presentation step to the
# SUBMITTED value as well as to the preset initial — i.e. it treats the display's
# sub-second capability as a property of every value the field contributes, rather than
# only of the value the field presents from its own initial. Correct on every disabled
# field and on every editable field whose submitted value is non-temporal or whose
# display supports sub-second precision. Measured to survive ALL SEVEN previously
# shipped witnesses (each build exit 1, gold-like), because no shipped witness has an
# editable field whose submitted value is temporal. WRONG on an editable field whose
# display lacks sub-second support but whose submitted value carries a sub-second
# component: the spec passes the submitted value through untouched. Attacks the
# LOCUS of clause C2 — the presentation applies to the initial-value path only.
_RIV_DATASTRIP = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let present : FieldValue → FieldValue := fun v =>\n"
    "      match v with\n"
    "      | FieldValue.ts w s => if f.supportsMicro then FieldValue.ts w s else FieldValue.ts w 0\n"
    "      | FieldValue.other n => FieldValue.other n\n"
    "    let value := if f.disabled then boundInitial f else present f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned",
)

# reverse-order: selects each field's value correctly (clauses C1/C2 hold element-wise)
# but emits the entries in REVERSE field order. Attacks clause C3 (structure/order) —
# the cleaned data must correspond to the fields in declared order.
_RIV_REVERSE = _swap(
    _BASE,
    _IMPL,
    "def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do\n"
    "  let mut cleaned : List FieldValue := []\n"
    "  for f in fields do\n"
    "    let value := if f.disabled then boundInitial f else f.data\n"
    "    cleaned := cleaned ++ [value]\n"
    "  return cleaned.reverse",
)


def _wit(fields, note):
    """A refutation witness: `¬ problem_spec_cleanFields fields (implementation … fields)`
    at a concrete literal list of FieldModel. FieldValue/FieldModel are concrete
    inductives with DecidableEq and there is no opaque callee, so `decide` reduces the
    whole `Id.run`/`for` computation and the spec's `.map` and closes the disequality.
    Elaborates against a rival that diverges from the spec at `fields`, and FAILS on
    gold (which satisfies the spec at every input) — SEEN to discriminate both ways
    (`decide` reports it proved `False`)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_cleanFields {fields}\n"
        f"    (implementation_cleanFields {fields}) := by\n"
        f"  unfold problem_spec_cleanFields\n"
        f"  decide"
    )


# FieldModel literals used by the witnesses. Each probes a DISTINCT shape so every
# binder is exercised across the battery.
#   no-strip       : disabled=true,  supportsMicro=FALSE, ts sub≠0  -> gold strips, rival keeps
#   always-strip   : disabled=true,  supportsMicro=TRUE,  ts sub≠0  -> gold keeps,  rival strips
#   always-data    : disabled=TRUE,  boundInitial≠data              -> gold=initial, rival=data
#   always-initial : disabled=FALSE, data≠boundInitial              -> gold=data,    rival=initial
#   reverse        : TWO fields with distinct values                -> order differs
_F_NOSTRIP = (
    "[{ disabled := true, supportsMicro := false, "
    "rawInitial := FieldValue.ts 5 7, data := FieldValue.other 0 }]"
)
_F_ALWAYSSTRIP = (
    "[{ disabled := true, supportsMicro := true, "
    "rawInitial := FieldValue.ts 5 7, data := FieldValue.other 0 }]"
)
_F_ALWAYSDATA = (
    "[{ disabled := true, supportsMicro := true, "
    "rawInitial := FieldValue.other 1, data := FieldValue.other 2 }]"
)
_F_ALWAYSINIT = (
    "[{ disabled := false, supportsMicro := true, "
    "rawInitial := FieldValue.other 1, data := FieldValue.other 2 }]"
)
_F_REVERSE = (
    "[{ disabled := false, supportsMicro := true, "
    "rawInitial := FieldValue.other 0, data := FieldValue.other 1 }, "
    "{ disabled := false, supportsMicro := true, "
    "rawInitial := FieldValue.other 0, data := FieldValue.other 2 }]"
)
#   nontemporal    : disabled=TRUE, rawInitial NON-temporal, initial≠data
#                    -> gold takes the initial, rival takes the data
_F_NONTEMPORAL = (
    "[{ disabled := true, supportsMicro := false, "
    "rawInitial := FieldValue.other 7, data := FieldValue.other 9 }]"
)
#   head-micro     : TWO disabled temporal fields DISAGREEING on supportsMicro; the
#                    second field's sub-second component must be dropped on its OWN
#                    display, not retained because the FIRST field supports it
#                    STRENGTHENED BY THE SECOND AUDIT: the first field's sub-second
#                    component is now NON-ZERO (`ts 1 5`, was `ts 1 0`). With a zero
#                    first component the witness pinned only the SECOND field's
#                    presentation, so it was blind to a guard hoisted from the LAST
#                    field rather than the first (measured: the tail-hoisting rival
#                    built exit 1, gold-like, against the old literal). Both fields'
#                    presentations are now pinned, so the witness discriminates every
#                    hoisting direction, not just the head one.
_F_HEADMICRO = (
    "[{ disabled := true, supportsMicro := true, "
    "rawInitial := FieldValue.ts 1 5, data := FieldValue.other 0 }, "
    "{ disabled := true, supportsMicro := false, "
    "rawInitial := FieldValue.ts 2 9, data := FieldValue.other 0 }]"
)
#   tail-micro     : the SAME mixed two-field form. Under the strengthened literal the
#                    first field's non-zero sub-second component is what separates a
#                    tail-hoisted guard from gold.
_F_TAILMICRO = _F_HEADMICRO
#   data-stripped  : an EDITABLE field whose display lacks sub-second support but whose
#                    SUBMITTED value is temporal and carries a sub-second component ->
#                    gold contributes the submitted value unchanged (the presentation
#                    step applies only to the initial-value path)
_F_DATASTRIP = (
    "[{ disabled := false, supportsMicro := false, "
    "rawInitial := FieldValue.other 0, data := FieldValue.ts 3 8 }]"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": (
            "a structurally different CORRECT impl written as a pure `List.map` (no "
            "`Id.run do`, no `let mut`, no accumulator loop, no early return), with the "
            "per-field selection inlined into the mapped function. Output equals the "
            "frozen impl's on every input, so both C1/C2/C3 hold. The theorem STATEMENT "
            "is byte-identical; its proof is reproven honestly with "
            "`unfold …; simp [cleanedValue]` — no new axiom/lemma/sorry, just the "
            "cheapest tactic for the map shape. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to the monadic loop shape rather than the behaviour). "
            "Ports nagini's `_POS_INLINE`/`_POS_DIRECT` positive controls."
        ),
    },
    {
        "id": "pos-cleanedValue-call",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CALL,
        "rationale": (
            "keeps the imperative accumulator loop but selects each field's value by "
            "calling the shared `cleanedValue` helper instead of inlining the branch. "
            "Behaviourally identical on every input. The theorem STATEMENT is "
            "byte-identical; the loop-invariant helper lemma is restated over the "
            "definitionally-equal `cleanedValue f` body and closes with the same tactic "
            "family — no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition is bound to the exact syntactic selection expression)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    # ADDED BY THE SECOND AUDIT. The port recorded this lane as N/A because the frozen
    # obligation carries no precondition hypothesis. That reason is not sufficient: on a
    # total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input, which a `∀`-statement can be while
    # still being provable-looking in the abstract. This case tests it directly — it
    # discharges the spec predicate BY EVALUATION at a concrete F2P-shaped form, as a
    # `have`, before closing the frozen obligation verbatim. Nothing is assumed: no new
    # declaration, no axiom/sorry, statement byte-identical.
    {
        "id": "admiss-f2p-shaped-form",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _P_INTRO,
            # First `have`: EVALUATE the modeled behavior at the F2P-shaped form down to
            # concrete entries, so the admission is pinned to the branch the F2P
            # actually exercises (a disabled field whose display cannot represent the
            # sub-second component its preset initial carries, alongside an ordinary
            # editable field) rather than merely restating the spec at that input.
            # Measured load-bearing: it FAILS against a wrong impl.
            "  have _eval : implementation_cleanFields\n"
            "      [{ disabled := true, supportsMicro := false,\n"
            "         rawInitial := FieldValue.ts 5 123456, data := FieldValue.other 0 },\n"
            "       { disabled := false, supportsMicro := true,\n"
            "         rawInitial := FieldValue.ts 7 1, data := FieldValue.other 4 }]\n"
            "      = [FieldValue.ts 5 0, FieldValue.other 4] := by decide\n"
            "  have _adm : problem_spec_cleanFields\n"
            "      [{ disabled := true, supportsMicro := false,\n"
            "         rawInitial := FieldValue.ts 5 123456, data := FieldValue.other 0 },\n"
            "       { disabled := false, supportsMicro := true,\n"
            "         rawInitial := FieldValue.ts 7 1, data := FieldValue.other 4 }]\n"
            "      (implementation_cleanFields\n"
            "        [{ disabled := true, supportsMicro := false,\n"
            "           rawInitial := FieldValue.ts 5 123456, data := FieldValue.other 0 },\n"
            "         { disabled := false, supportsMicro := true,\n"
            "           rawInitial := FieldValue.ts 7 1, data := FieldValue.other 4 }]) := by\n"
            "    unfold problem_spec_cleanFields\n"
            "    decide\n"
            + _P_INTRO,
        ),
        "rationale": (
            "the obligation is SATISFIABLE at a normal F2P-shaped form, shown by "
            "evaluation rather than in the abstract: a two-field form combining a "
            "disabled temporal field whose display cannot represent the sub-second "
            "component its preset initial carries with an ordinary editable field "
            "reduces to concrete entries (the first presented sub-second-zeroed, the "
            "second the submitted value), and the spec predicate then holds there by "
            "`decide`. The frozen obligation is closed verbatim afterwards. This is the "
            "total-carrier analogue of nagini's `admiss-f2p-shaped-input`: the frozen "
            "theorem has no precondition binder to attack, but a `∀`-obligation can "
            "still be unsatisfiable at exactly the shape the F2P exercises, and only a "
            "ground discharge at that shape rules it out. Nothing is assumed — no new "
            "declaration, no axiom/sorry, statement byte-identical. If it FAILS => the "
            "modeled behavior is unsatisfiable at a normal input (PRECOND-TOO-STRONG's "
            "analogue). Ports nagini `admiss-f2p-shaped-input`."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "no-strip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOSTRIP,
        "refinement": (
            "a disabled field contributing its RAW initial value without the "
            "presentation step is exactly the pre-patch behaviour (mapping.md aspect 1): "
            "the value the field would present drops any sub-second component when the "
            "display cannot represent it, but this rival emits the raw value. On the F2P "
            "input — a disabled temporal field with a non-zero sub-second component whose "
            "display lacks sub-second support — the cleaned value would carry the "
            "sub-second component the patched code strips, so the F2P assertion (cleaned "
            "value equals the value the field presents) FAILS. A faithful patch of this "
            "shape does NOT resolve; a verifying rival is a true "
            "verify-does-not-imply-resolve break. Direct port of nagini `_UNNORMALISED`."
        ),
        "rationale": (
            "REJECTED by clause C2 (presentation). On a disabled, non-sub-second-"
            "supporting field with a sub-second-bearing temporal initial value the spec "
            "demands the sub-second-zeroed value; the rival returns the raw one. Witness "
            "sets supportsMicro=FALSE with a temporal rawInitial whose sub component is "
            "non-zero. If it VERIFIES => SPEC-TOO-WEAK (the presentation step is unpinned)."
        ),
        "witness": _wit(
            _F_NOSTRIP,
            "disabled temporal field, no sub-second support, non-zero sub-second: "
            "gold presents the stripped value, no-strip rival keeps the raw value",
        ),
    },
    {
        "id": "always-strip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYSSTRIP,
        "refinement": (
            "always dropping the sub-second component — even for a field whose display "
            "CAN represent it — is what a patch that unconditionally stripped precision "
            "would do. It is correct on non-supporting fields but WRONG whenever the "
            "field supports sub-second precision and the initial value carries one: the "
            "cleaned value loses a component the field would present, so a P2P-style "
            "assertion on a sub-second-supporting field FAILS. Does NOT resolve — the "
            "dual of the pre-patch bug."
        ),
        "rationale": (
            "REJECTED by clause C2 (presentation, retain direction). On a disabled field "
            "with supportsMicro=TRUE and a sub-second-bearing temporal initial value the "
            "spec demands the value UNCHANGED; the rival zeroes the sub component. Witness "
            "varies supportsMicro=TRUE (the binder value no-strip's witness holds FALSE), "
            "so the two rivals are separated at the exact sub-domain each abuses. If it "
            "VERIFIES => SPEC-TOO-WEAK (the retain direction of the presentation is "
            "unpinned)."
        ),
        "witness": _wit(
            _F_ALWAYSSTRIP,
            "disabled temporal field, sub-second support, non-zero sub-second: "
            "gold retains the value, always-strip rival zeroes the sub-second component",
        ),
    },
    {
        "id": "always-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYSDATA,
        "refinement": (
            "always contributing the submitted value ignores the disabled/editable "
            "selection fork entirely — what a patch that dropped the `if field.disabled` "
            "branch would do. Correct on editable fields, WRONG on a disabled field whose "
            "submitted payload differs from its presented initial value: the cleaned data "
            "reflects the payload instead of the field's own initial, so the F2P "
            "assertion (a disabled field takes its initial, not the submitted data) "
            "FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (selection, disabled direction). For a disabled field "
            "with boundInitial ≠ data the spec demands the presented initial value; the "
            "rival returns the submitted data. Witness sets disabled=TRUE with distinct "
            "initial/data payloads. If it VERIFIES => SPEC-TOO-WEAK (the disabled branch "
            "is unpinned)."
        ),
        "witness": _wit(
            _F_ALWAYSDATA,
            "disabled field, initial ≠ data: gold takes the initial, "
            "always-data rival takes the submitted data",
        ),
    },
    {
        "id": "always-initial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYSINIT,
        "refinement": (
            "always contributing the presented initial value is the DUAL selection error "
            "— what a patch that treated every field as disabled would do. Correct on "
            "disabled fields, WRONG on an editable field whose submitted value differs "
            "from its initial: the cleaned data reflects the initial instead of the "
            "submitted value, so any assertion on an editable field's cleaned value "
            "FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (selection, editable direction). For an editable field "
            "with data ≠ boundInitial the spec demands the submitted value; the rival "
            "returns the presented initial. Witness varies disabled=FALSE (the binder "
            "value the always-data witness holds TRUE), pinning the other side of the "
            "selection fork. If it VERIFIES => SPEC-TOO-WEAK (the editable branch is "
            "unpinned)."
        ),
        "witness": _wit(
            _F_ALWAYSINIT,
            "editable field, data ≠ initial: gold takes the submitted data, "
            "always-initial rival takes the presented initial",
        ),
    },
    {
        "id": "nontemporal-disabled-takes-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NONTEMPORAL,
        "refinement": (
            "taking the submitted value for a disabled field whenever its preset "
            "initial is not a date/time is what a patch that reached for the field's "
            "own initial only on the temporal path would do — the selection fork made "
            "conditional on the value's kind rather than on the field's editability. "
            "Correct on every disabled temporal field, WRONG on a disabled field whose "
            "preset initial is an ordinary (non-temporal) value differing from its "
            "submitted payload: the cleaned value reflects the payload, but a disabled "
            "field must never take the payload whatever its value's kind. Any "
            "assertion on such a field's cleaned value FAILS, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (selection) on the sub-domain reached through the "
            "non-temporal arm of the presentation: the spec's `cleanedValue` branches "
            "on `disabled` ALONE, so a disabled field takes its presented initial "
            "regardless of the initial's constructor. Witness holds disabled=TRUE with "
            "a non-temporal rawInitial ≠ data — the constructor/selection combination "
            "no other rival's witness reaches (the two C1 witnesses use non-temporal "
            "initials but neither makes the fork depend on the constructor). If it "
            "VERIFIES => SPEC-TOO-WEAK (the selection fork is pinned only on the "
            "temporal sub-domain)."
        ),
        "witness": _wit(
            _F_NONTEMPORAL,
            "disabled field with a NON-temporal initial ≠ its submitted value: gold "
            "takes the initial, this rival falls through to the submitted data",
        ),
    },
    {
        "id": "head-micro-contamination",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_HEADMICRO,
        "refinement": (
            "presenting every field's temporal initial at the FIRST field's display "
            "precision is what a patch that read the sub-second-support flag once, "
            "outside the per-field loop, would do — hoisting a per-field property to "
            "the form. Correct on any single-field form and on any form whose fields "
            "agree on sub-second support, WRONG on a form mixing a sub-second-capable "
            "field with one that is not: the second field either keeps a sub-second "
            "component its display cannot represent or loses one it can. A multi-field "
            "assertion on the mixed form FAILS, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 read PER FIELD: the spec is `fields.map "
            "cleanedValue`, and `cleanedValue`/`boundInitial` consult `f.supportsMicro` "
            "of the very field being presented, so each field's presentation is "
            "independent of its neighbours'. Witness is the only one in the battery "
            "with length > 1 AND supportsMicro DISAGREEING across the two fields — the "
            "reverse-order witness holds it true on both, so this rival survives every "
            "other witness in the battery. Its witness literal was STRENGTHENED by a "
            "later audit to carry a non-zero sub-second component on the FIRST field "
            "too; with a zero there it pinned only the second field's presentation and "
            "a guard hoisted from the LAST field was indistinguishable from gold (now "
            "shipped separately as `tail-micro-contamination`). If it VERIFIES => "
            "SPEC-TOO-WEAK (the presentation guard is pinned only form-wide, not per "
            "field)."
        ),
        "witness": _wit(
            _F_HEADMICRO,
            "two disabled temporal fields disagreeing on sub-second support: gold "
            "presents each at its OWN precision, this rival uses the first field's "
            "for both",
        ),
    },
    {
        "id": "tail-micro-contamination",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TAILMICRO,
        "refinement": (
            "reading the sub-second-support flag once from the LAST field and applying "
            "it to every field is the mirror image of the head-hoisted error, and is "
            "what a patch that captured the flag from the wrong end of the field "
            "collection would do. Correct on any single-field form and on any form "
            "whose fields agree on sub-second support, WRONG on a mixed form: the "
            "leading field then either keeps a sub-second component its display cannot "
            "represent or loses one it can. A multi-field assertion on the mixed form "
            "FAILS, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 read PER FIELD, from the opposite side to "
            "head-micro-contamination: the spec's `boundInitial` consults "
            "`f.supportsMicro` of the field being presented, so no single form-wide "
            "flag reproduces it. This case exists because the head-hoisted rival's "
            "witness previously held a ZERO sub-second component on its first field, "
            "which pinned only the second field's presentation and left a "
            "tail-hoisted guard indistinguishable from gold (measured). The witness "
            "literal is now non-zero on BOTH fields, which discriminates both "
            "hoisting directions. If it VERIFIES => SPEC-TOO-WEAK (the presentation "
            "guard is pinned only form-wide)."
        ),
        "witness": _wit(
            _F_TAILMICRO,
            "two disabled temporal fields disagreeing on sub-second support, both "
            "carrying a sub-second component: gold presents each at its OWN "
            "precision, this rival uses the last field's for both",
        ),
    },
    {
        "id": "data-also-presented",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DATASTRIP,
        "refinement": (
            "putting the submitted value through the same display-precision "
            "presentation as the preset initial is what a patch that applied the "
            "sub-second normalisation to every value a field contributes — rather than "
            "only to the value the field presents from its own initial — would do. "
            "Correct on every disabled field and wherever the submitted value is "
            "non-temporal or the display supports sub-second precision, WRONG on an "
            "editable field whose display lacks sub-second support but whose submitted "
            "payload carries a sub-second component: the cleaned value would silently "
            "lose precision the submitted payload actually had, so an assertion on "
            "that field's cleaned value FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the LOCUS of clause C2: `cleanedValue` routes an editable "
            "field's contribution straight to `f.data` and applies `boundInitial` "
            "only on the disabled path, so the presentation step is pinned to the "
            "initial-value path alone. Witness is the only one in the battery with a "
            "TEMPORAL submitted value on an editable field — every other witness "
            "carries a non-temporal `data`, which is exactly why this rival was "
            "measured to survive all seven previously shipped witnesses. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec would not say which of the two "
            "value paths the presentation applies to)."
        ),
        "witness": _wit(
            _F_DATASTRIP,
            "editable field whose display lacks sub-second support but whose SUBMITTED "
            "value carries a sub-second component: gold contributes the submitted "
            "value unchanged, this rival presents it through the display precision",
        ),
    },
    {
        "id": "reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "selecting each field's value correctly but emitting the entries in reverse "
            "field order is what a patch that iterated the fields in the wrong direction "
            "would do. Every individual cleaned value is right, but the cleaned data no "
            "longer corresponds to the fields in declared order, so any multi-field "
            "assertion that reads a field's cleaned value by position/name FAILS. Does "
            "NOT resolve — the traversal order is observable."
        ),
        "rationale": (
            "REJECTED by clause C3 (structure/order): the spec demands "
            "`fields.map cleanedValue`, i.e. entries in field order, but the rival "
            "reverses them. Witness uses a TWO-field list with distinct values, "
            "exercising the list-length binder the single-field witnesses hold at 1 "
            "(it is no longer the battery's ONLY length-2 witness — the two "
            "presentation-hoisting rivals also carry one). If it VERIFIES => "
            "SPEC-TOO-WEAK (order/structure is unpinned)."
        ),
        "witness": _wit(
            _F_REVERSE,
            "two editable fields with distinct submitted values: gold keeps field order, "
            "reverse rival flips it",
        ),
    },
]


# No @ContractOnly axioms and no opaque callees: the per-field selection and the
# presentation step (boundInitial) are modeled DEEPLY over transparent inductive
# carriers, so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
