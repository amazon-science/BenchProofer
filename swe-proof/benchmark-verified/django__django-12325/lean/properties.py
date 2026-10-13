# properties.py — G-PBT falsification battery for django__django-12325 (lean lane).
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
#   collectParentLinks : List FieldInfo → List (String × FieldInfo)
#   A candidate field carries four observable attributes:
#     isOneToOne : Bool   — whether it is a one-to-one relation;
#     parentLink : Bool   — whether it is designated the parent link for its target;
#     relatedKey : String — the identity of the related model it points at (map key);
#     name       : String — the field's own stable identity (disambiguates fields
#                           that share a relatedKey; carries only identity).
#   The single postcondition `problem_spec_collectParentLinks fields result` pins the
#   result to be EXACTLY `buildParentLinks fields` — no slack, fully determined:
#     scan the fields IN ORDER and record, keyed by relatedKey with LAST-WRITE-WINS,
#     each field for which `isOneToOne && parentLink` holds; every other field is
#     skipped. This one equality carries several INDEPENDENT sub-obligations, each
#     separately attackable:
#       (G-eligibility) a field is recorded IFF isOneToOne AND parentLink — BOTH
#         boolean toggles gate recording; a rival that drops EITHER conjunct records
#         a field the spec skips.
#       (G-order/retain) every scanned position is considered — no position is
#         dropped by its index; a genuine parent link at the FIRST scanned position
#         is retained just like any other.
#       (G-last-write) when two recorded fields share a relatedKey, the LAST one
#         scanned wins (dictInsert drops the prior entry, appends the new); a rival
#         that keeps the first records a different field object for that key.
#       (G-key) the map key is the RELATED-MODEL identity (relatedKey), not the
#         field's own identity (name); a rival that files each field under `name`
#         collects exactly the right fields under the wrong keys.
#       (G-no-stale) the prior entry for a rewritten key is REMOVED, not merely
#         superseded; a rival that only appends leaves the displaced field in the
#         mapping alongside the one that replaced it.
#       (G-canonical) the obligation is a LIST equality, so the modeled assignment
#         also fixes the SEQUENCE: a rewritten key moves to the end. This clause is
#         NOT attacked, deliberately — see the AUDIT NOTE at 'weak-rewrite-in-place'
#         below. It is an artifact of the assoc-list encoding rather than a
#         behavioural requirement, and an impl that differs from the reference ONLY
#         here is not wrong, so a rival aimed at it would be rejected for the wrong
#         reason. Escalated as a spec finding instead of being scored as a rival.
#   buildParentLinks / dictInsert are total, transparent folds over a fully
#   `DecidableEq` carrier (FieldInfo = Bool/Bool/String/String) — no opaque callee,
#   no answer-key oracle — so every witness states its refutation at concrete
#   literal fields and `decide` closes it. No carrier conditioning is needed here.
#
# CARRIER NOTE / relation to the nagini sibling. Nagini modeled the mapping build
# over two parallel read-only lists `is_parent_link : List[bool]` and
# `related_key : List[int]`, folding the `isinstance(field, OneToOneField)` filter
# into WHICH positions even appear (its list held only OneToOneField instances). The
# lean carrier promotes that filter to an EXPLICIT `isOneToOne : Bool` attribute on
# each `FieldInfo`, so the lean spec has TWO boolean gates (`isOneToOne`,
# `parentLink`) where nagini exposed one plus an implicit list-membership filter.
# Both toggles are therefore attacked and both are varied across the reject
# witnesses (one witness sets isOneToOne=false with parentLink=true, another sets
# parentLink=false with isOneToOne=true) — the "two independent toggles, one held
# constant" hole does not apply here.
#   Nagini's postcondition-clause rivals port as follows:
#     * weak-no-filter-prepatch  -> weak-drop-parent-link  (the pre-patch behaviour:
#                                    record on isOneToOne alone).
#     * (implicit isinstance gate) -> weak-drop-onetoone   (record on parentLink
#                                    alone — the OTHER conjunct, made explicit here).
#     * weak-skip-first-relation -> weak-skip-first-scanned (partial-domain: correct
#                                    on every position but the first).
#     * weak-record-nonparent-on-key0 -> weak-record-nonparent-on-key (value
#                                    sub-domain of relatedKey — invisible to a byte
#                                    fuzzer).
#     * weak-first-writer-wins   -> weak-first-write-wins  (tie-break: keep the FIRST
#                                    field for a key instead of the last).
#     * _FRAME_IPL / _FRAME_RK   -> weak-forge-flags-on-a-copy  (see FRAME-MUTATION
#                                    below: the write does not port, the INTENT does).
#
# Rivals added beyond the nagini set, each closing a sub-obligation the ported five leave
# unattacked (they are NOT reshapes of the five — each is refuted by a clause none of the
# five reaches, and each was confirmed to discriminate by rebuilding its witness against
# both the rival and the frozen solution):
#     * weak-no-stale-removal        (the `filter` half of the modeled assignment: a
#                                     superseded entry lingering beside the fresh one).
#     * weak-key-by-field-identity   (the KEY: files each field under its own identity
#                                     instead of the target model's).
#     (A third addition, weak-rewrite-in-place, was REMOVED by a later audit: its rival
#      was not wrong. See the AUDIT NOTE where it used to stand.)
#
# LANES THAT DO NOT PORT AS WRITTEN:
#   * FRAME-MUTATION (nagini's MANDATORY `_FRAME_IPL` / `_FRAME_RK`: both inputs were
#     Acc(list_pred(.),1/2) read-only and the rivals WROTE into them —
#     `is_parent_link[i] = True` / `related_key[i] = i` — to satisfy a clause
#     vacuously, rejected there for INSUFFICIENT PERMISSION). Lean is referentially
#     transparent — no aliasing, no fractional permission — so the WRITE is not
#     expressible. The INTENT is, however, and it is carried rather than dropped:
#     `weak-forge-flags-on-a-copy` rewrites both eligibility attributes on a local copy
#     and records unconditionally. It is rejected ON THE MERITS (the obligation's `fields`
#     binder denotes the caller's value), which is the executable demonstration that the
#     lane poses no threat here — stronger than asserting the class is vacuous. See
#     'assessment'.
#   * ADMISSIBILITY — LANDED (was previously recorded here as N/A; that was WRONG).
#     Nagini's `_ADMISS` defended the half-permission `Requires` by a self-call on an
#     F2P-shaped input. The earlier reasoning was "the lean obligation binds NO
#     precondition hypothesis, so nothing could be PRECOND-TOO-STRONG, so the lane is
#     N/A". That does not follow. On a TOTAL carrier the analogue of an over-strong
#     precondition is the obligation being UNSATISFIABLE at exactly a task-shaped
#     input — a spec no implementation could discharge precisely where the behaviour
#     matters is broken in the precondition direction even though the statement binds
#     no hypothesis. Nor does "the ∀ covers it transitively" close the gap: the ∀ is
#     discharged by a tactic script, and a script can close a universal without any
#     concrete point ever being EVALUATED. So the lane is landed as
#     `adm-f2p-shaped-input` below, which discharges the postcondition BY EVALUATION
#     at a concrete two-relation input before closing the frozen obligation verbatim.
#   * DIVERGENCE / NON-TERMINATION. `implementation_collectParentLinks` is a total
#     Lean `def`; a non-terminating implementation cannot be written at all, so the
#     class is genuinely VACUOUS on lean (NOT a known spec hole — that disposition is
#     the velvet-partial one). Nagini carried no diverge-* case for this instance.
#   * AXIOM_TESTS. The mapping build (guarded last-write-wins insertion) is modeled
#     DEEPLY over a transparent carrier; there is no consumed axiom / opaque callee,
#     so the axiom lane is vacuous and belongs to G-AX regardless.
from pathlib import Path

INSTANCE = "django__django-12325"

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
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if field.isOneToOne && field.parentLink then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "  return parentLinks"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof block (helper theorem + correct_ theorem), lying ENTIRELY inside
# proof-start/proof-end and unique in the file. Swapped ONLY by the positives, whose
# different impl shapes need a (cheap, honest) reproof of the byte-identical
# `theorem correct_collectParentLinks` STATEMENT. The rivals leave it in place: the
# frozen script no longer closes for a reshaped impl (so the rival does not verify),
# and the gate reads the WITNESS, checked in a file with this block removed.
_PROOF = (
    "/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals\n"
    "the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/\n"
    "theorem forIn_collectParentLinks (fields : List FieldInfo)\n"
    "    (init : List (String × FieldInfo)) :\n"
    "    Id.run (forIn fields init (fun field r =>\n"
    "        (if (field.isOneToOne && field.parentLink) = true then\n"
    "          ForInStep.yield (dictInsert r field.relatedKey field)\n"
    "        else ForInStep.yield r : Id _))) =\n"
    "      List.foldl\n"
    "        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)\n"
    "        init fields := by\n"
    "  induction fields generalizing init with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    by_cases h : (a.isOneToOne && a.parentLink) = true\n"
    "    · simp only [h, List.foldl_cons, if_true, ih]\n"
    "    · simp only [Bool.not_eq_true] at h\n"
    "      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]\n"
    "\n"
    "theorem correct_collectParentLinks :\n"
    "    ∀ (fields : List FieldInfo),\n"
    "      problem_spec_collectParentLinks fields\n"
    "        (implementation_collectParentLinks fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks\n"
    "  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>\n"
    "              (if (field.isOneToOne && field.parentLink) = true then\n"
    "                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))\n"
    "              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))\n"
    "          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>\n"
    "              (if (field.isOneToOne && field.parentLink) = true then\n"
    "                ForInStep.yield (dictInsert r field.relatedKey field)\n"
    "              else ForInStep.yield r : Id _))) := rfl\n"
    "  simp only [Id.run]\n"
    "  rw [h2]\n"
    "  exact forIn_collectParentLinks fields []"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# AUDIT NOTE — a positive that was DROPPED and why. An earlier revision of this battery
# carried `pos-functional-fold`, whose impl was the pure fold
#   `fields.foldl (fun d f => if f.isOneToOne && f.parentLink then dictInsert … else d) []`
# — i.e. the body of `buildParentLinks` VERBATIM. That impl is DEFINITIONALLY the spec
# target, so its reproof is `rfl` and its verification is guaranteed by construction: it
# says only "the spec's own reference fold satisfies the spec", which is a tautology and
# measures nothing about spec strength. It was replaced by the two positives below, whose
# impls are NOT definitionally the target and whose reproofs need a real generalizing
# induction (accumulator generalization; filter/fold fusion). Both strictly dominate it:
# they still establish that the postcondition is not bound to the monadic impl shape, and
# they additionally establish that it is not bound to the fold's recursion scheme.

# pos-filter-then-fold: a structurally different CORRECT impl that makes TWO passes —
# first `List.filter` the eligible fields, then fold `dictInsert` over the survivors with
# no guard at all. Semantics identical on every input, but the shape is not definitionally
# the spec's single guarded fold: closing it needs a filter/fold FUSION lemma, proven here
# by induction with the guard case-split, as an in-proof `have` (no new top-level
# theorem/lemma, no axiom/sorry). The theorem STATEMENT is byte-identical. If it FAILS
# => SPEC-TOO-STRONG (the postcondition is over-fit to the one-pass guarded-fold shape).
_POS_FILTERFOLD = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
        "    List (String × FieldInfo) :=\n"
        "  (fields.filter (fun f => f.isOneToOne && f.parentLink)).foldl\n"
        "    (fun d f => dictInsert d f.relatedKey f) []",
    ),
    _PROOF,
    "theorem correct_collectParentLinks :\n"
    "    ∀ (fields : List FieldInfo),\n"
    "      problem_spec_collectParentLinks fields\n"
    "        (implementation_collectParentLinks fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks\n"
    "  have key : ∀ (l : List FieldInfo) (init : List (String × FieldInfo)),\n"
    "      (l.filter (fun f => f.isOneToOne && f.parentLink)).foldl\n"
    "          (fun d f => dictInsert d f.relatedKey f) init =\n"
    "        List.foldl (fun d f =>\n"
    "          if f.isOneToOne && f.parentLink then dictInsert d f.relatedKey f else d) init l := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro init; rfl\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      by_cases h1 : a.isOneToOne = true\n"
    "      · by_cases h2 : a.parentLink = true\n"
    "        · simp [List.filter_cons, h1, h2, ih]\n"
    "        · simp [List.filter_cons, h1, h2, ih]\n"
    "      · simp [List.filter_cons, h1, ih]\n"
    "  exact key fields []",
)

# pos-recursive-accumulator: a structurally different CORRECT impl written as an explicit
# tail-recursive helper `collectAux` threading the mapping as an accumulator — a different
# RECURSION SCHEME, not a fold at all (an impl-region `def`, which the variant scope
# admits; the banned category is a new top-level theorem/lemma/axiom). Semantics identical
# on every input. Closing it needs the accumulator GENERALIZED over the induction (the
# statement is not reflexive at any fixed accumulator), proven as an in-proof `have`. The
# theorem STATEMENT is byte-identical. If it FAILS => SPEC-TOO-STRONG (the postcondition
# is over-fit to `List.foldl` as the way the scan is expressed).
_POS_RECURSIVE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def collectAux : List FieldInfo → List (String × FieldInfo) →\n"
        "    List (String × FieldInfo)\n"
        "  | [], acc => acc\n"
        "  | f :: rest, acc =>\n"
        "      collectAux rest\n"
        "        (if f.isOneToOne && f.parentLink then dictInsert acc f.relatedKey f else acc)\n"
        "\n"
        "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
        "    List (String × FieldInfo) := collectAux fields []",
    ),
    _PROOF,
    "theorem correct_collectParentLinks :\n"
    "    ∀ (fields : List FieldInfo),\n"
    "      problem_spec_collectParentLinks fields\n"
    "        (implementation_collectParentLinks fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks\n"
    "  have key : ∀ (l : List FieldInfo) (init : List (String × FieldInfo)),\n"
    "      collectAux l init =\n"
    "        List.foldl (fun d f =>\n"
    "          if f.isOneToOne && f.parentLink then dictInsert d f.relatedKey f else d) init l := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro init; rfl\n"
    "    | cons a as ih => intro init; simp [collectAux, List.foldl_cons, ih]\n"
    "  exact key fields []",
)

# pos-branch-reorder: a structurally different CORRECT impl written as a pure fold
# whose per-field lambda NEGATES the eligibility test and records in the ELSE branch
# (skip when NOT eligible; otherwise record). Behaviourally identical to gold on every
# input. The theorem STATEMENT is byte-identical; its proof is reproven honestly
# (pointwise congruence on the fold lambda, `by_cases` on the guard). No new
# axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the postcondition is over-fit to
# one syntactic branch orientation).
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
        "    List (String × FieldInfo) :=\n"
        "  fields.foldl\n"
        "    (fun d f => if !(f.isOneToOne && f.parentLink) then d else dictInsert d f.relatedKey f)\n"
        "    []",
    ),
    _PROOF,
    "theorem correct_collectParentLinks :\n"
    "    ∀ (fields : List FieldInfo),\n"
    "      problem_spec_collectParentLinks fields\n"
    "        (implementation_collectParentLinks fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks\n"
    "  congr 1\n"
    "  funext d f\n"
    "  by_cases h : (f.isOneToOne && f.parentLink) = true\n"
    "  · simp [h]\n"
    "  · simp [h]",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof block is left in place
# (it no longer closes for the reshaped impl, so the rival does not verify, but the
# gate decides the case by the WITNESS — checked in a file with the obligation
# removed — not by the rival's own build).
# ===========================================================================

# weak-drop-parent-link: the PRE-PATCH behaviour. Records a field on `isOneToOne`
# alone — the `parentLink` conjunct of the eligibility gate is dropped. So a
# one-to-one relation NOT designated the parent link is recorded, which gold skips.
_RIV_DROP_PL = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if field.isOneToOne then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "  return parentLinks",
)

# weak-drop-onetoone: the DUAL conjunct. Records a field on `parentLink` alone — the
# `isOneToOne` conjunct is dropped. So a field designated a parent link but NOT a
# one-to-one relation is recorded, which gold skips. Attacks the OTHER boolean gate,
# the one the nagini carrier folded into an implicit list-membership filter.
_RIV_DROP_OO = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if field.parentLink then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "  return parentLinks",
)

# weak-skip-first-scanned: PARTIAL-DOMAIN. Applies the eligibility gate correctly at
# every position EXCEPT the first scanned one (index 0), which is never recorded. When
# a genuine parent link is the first scanned field, its key is lost from the result.
_RIV_SKIP0 = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  let mut idx : Nat := 0\n"
    "  for field in fields do\n"
    "    if idx > 0 && field.isOneToOne && field.parentLink then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "    idx := idx + 1\n"
    "  return parentLinks",
)

# weak-record-nonparent-on-key: VALUE-PARTIAL-DOMAIN. Records eligible fields always
# (keeps every genuine parent link) but ALSO records any field whose relatedKey token
# is one particular value ("Z"), regardless of its flags. On that sub-domain a
# non-eligible field is recorded, which gold skips. Targets the value abstraction of
# relatedKey directly — a class a byte-fuzzer never reaches.
_RIV_KEYVAL = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if (field.isOneToOne && field.parentLink) || field.relatedKey == \"Z\" then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "  return parentLinks",
)

# weak-first-write-wins: TIE-BREAK. Records an eligible field only if its key is not
# already present, so the FIRST designated parent link per related model wins instead
# of the repo's last-write-wins dict assignment. Eligibility is correct (every
# recorded field is eligible; no key is lost), so this slips past a spec that pins
# only membership — it is refuted only by the last-write-wins sub-obligation, when two
# eligible fields share a relatedKey and differ by `name`.
_RIV_FIRSTWIN = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if field.isOneToOne && field.parentLink"
    " && parentLinks.all (fun p => p.1 ≠ field.relatedKey) then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "  return parentLinks",
)


# weak-no-stale-removal: STALE-ENTRY. Records every eligible field by APPENDING
# `(relatedKey, field)` without first dropping any entry already held for that key. Every
# genuine parent link is present and the LAST entry for a rewritten key is the right one,
# so both the eligibility and the "last one scanned wins" sub-obligations are satisfied in
# the weak sense a membership-or-lookup check would use. It is refuted only because the
# result must be the mapping ITSELF — a stale entry for a rewritten key survives alongside
# the fresh one, which the modeled assignment removes. Attacks the half of dictInsert the
# other rivals leave untouched (the `filter` that drops the prior entry, not the append).
_RIV_NOSTALE = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if field.isOneToOne && field.parentLink then\n"
    "      parentLinks := parentLinks ++ [(field.relatedKey, field)]\n"
    "  return parentLinks",
)

# weak-key-by-field-identity: KEY CONFUSION. Eligibility is exactly right and every
# eligible field is recorded, but the mapping is keyed by the field's OWN identity
# (`name`) instead of the identity of the model it points at (`relatedKey`). The recorded
# FIELDS are therefore the correct set — only the key each is filed under is wrong — so
# any check that looks at which fields were collected, or counts them, passes. Pins that
# the map key is the related-model identity, the one attribute no other rival varies in
# the key position.
_RIV_KEYBYNAME = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in fields do\n"
    "    if field.isOneToOne && field.parentLink then\n"
    "      parentLinks := dictInsert parentLinks field.name field\n"
    "  return parentLinks",
)

# AUDIT NOTE — a rival that was DROPPED as VACUOUS, and why (attack C).
# An earlier revision carried `weak-rewrite-in-place`: an impl that overwrote the entry
# for an already-present key IN PLACE (keeping that key at its first-seen position)
# instead of dropping the old entry and appending the new one at the end. It was scored
# as the battery's tightest rival, on the ground that it agrees with the reference on the
# whole key→field association and is refuted "only" by the sequence the list equality
# fixes. Re-derived on the real verifier, that rival is NOT WRONG, so its rejection
# attested to the encoding rather than to the spec, and scoring it as a uniqueness rival
# was a false claim about spec strength. Three machine-checked reasons, in order:
#
#   1. It is behaviourally indistinguishable through the projection the modeled behaviour
#      is actually consumed through. The mapping is consumed ONLY by a presence test and
#      a lookup by related-model identity; the collection is never traversed in order, so
#      no consumer can observe the position of a rewritten key. Checked exhaustively, not
#      argued: over every input list up to length 3 drawn from both booleans x three
#      relatedKey tokens x two names (4369 inputs), the two impls agree on
#      `lookup d k` for every key — `#eval` of the agreement predicate returned `true`
#      under `decide +kernel` — while differing as LISTS on at least one input. The
#      divergence is therefore purely positional.
#   2. On the point the dropped witness used, the in-place impl is the one that matches
#      the modeled reality and the reference is the one that does not. For a scan
#      recording keys A, B, A, an assignment into a mapping keyed by related-model
#      identity leaves the rewritten key at its FIRST-seen position — the sequence is
#      [A, B] — because assigning to a key already present updates the value and does not
#      move the key. `dictInsert` instead yields [B, A]. So the discarded witness's
#      "gold records [B,A], the rival records [A,B]" had the fidelity backwards: [A,B] is
#      the faithful order and [B,A] is the encoding's artifact.
#   3. Consequently the rival could not be refuted for the right reason on this carrier,
#      and a case whose rejection is attributable to the encoding rather than to the
#      behaviour is exactly the hollow shape the witness requirement exists to exclude.
#
# Dropped rather than repaired: there is no witness that could rescue it, because the
# discrimination it needs does not exist behaviourally. The residue is a property of the
# FROZEN spec — `problem_spec_collectParentLinks` pins a list equality and so
# over-constrains a mapping whose order is unobservable — which is escalated as a
# spec-level finding in the audit payload (`spec_holes`, SPEC-TOO-STRONG direction), NOT
# patched here: the spec is frozen, and changing it would have to re-clear the
# equivalence and leakage gates outside this lane. Note this is a hole in the
# SPEC-TOO-STRONG direction only; the spec remains an equality to a total reference
# function, so it cannot be too WEAK (see the `specPinsUniquely` observation in the
# audit notes: any two results satisfying it are equal).

# weak-forge-flags-on-a-copy: the lean ANALOGUE of nagini's mandatory frame-mutation
# probe, landed rather than dropped. Nagini's rivals wrote into the read-only inputs
# (`is_parent_link[i] = True`) so that a clause quantified over the input held vacuously,
# and were rejected for INSUFFICIENT PERMISSION. Lean has no aliasing to exploit, but the
# same INTENT is expressible: rewrite the flags on a local copy and then record
# unconditionally. This is the strongest form of that cheat available here, and it is
# rejected ON THE MERITS rather than by a permission system — the spec's `fields` binder
# denotes the caller's value, so forging a copy cannot make the obligation vacuous. Kept
# as the executable demonstration of why the nagini frame lane has no analogue that
# threatens this spec (see 'assessment'), not merely an assertion that it does not.
_RIV_FORGE = _swap(
    _BASE,
    _IMPL,
    "def implementation_collectParentLinks (fields : List FieldInfo) :\n"
    "    List (String × FieldInfo) := Id.run do\n"
    "  let forged := fields.map (fun f => { f with isOneToOne := true, parentLink := true })\n"
    "  let mut parentLinks : List (String × FieldInfo) := []\n"
    "  for field in forged do\n"
    "    if field.isOneToOne && field.parentLink then\n"
    "      parentLinks := dictInsert parentLinks field.relatedKey field\n"
    "  return parentLinks",
)


# ===========================================================================
# ADMISSIBILITY (must VERIFY) — the PRECOND-TOO-STRONG direction.
# ===========================================================================
# The frozen obligation binds no precondition hypothesis, so there is no `Requires` to
# be over-strong. The analogue on this total carrier is the obligation being
# UNSATISFIABLE at exactly a task-shaped input. This case tests that directly: it
# discharges `problem_spec_collectParentLinks` BY EVALUATION, as a `have`, at the
# concrete scenario the reported behaviour is about — a designated parent link and an
# ordinary one-to-one relation targeting the SAME base, the ordinary one declared later,
# so the eligibility gate must reject the second while the mapping retains the first —
# and only then closes the frozen obligation with the frozen tactic body VERBATIM.
#
# The `have` is bound to an unused name: it is a pure non-vacuity assertion and is never
# used to close the real goal, so it cannot weaken anything. The theorem STATEMENT stays
# byte-identical, no declaration is added, no assumption token is introduced.
#
# The step is INFORMATIVE rather than a tautology, and that was checked by control rather
# than asserted: the same `have` shape asserting the postcondition of a WRONG result (the
# empty mapping) at the same input does NOT close — `decide` reports it proved
# `[] = buildParentLinks [...]` false. So `decide` is genuinely evaluating the claim at
# this input, and a spec unsatisfiable here would surface as a failure of this case.
_ADM_INPUT = (
    '[{ isOneToOne := true, parentLink := true, relatedKey := "P", name := "p" },\n'
    '       { isOneToOne := true, parentLink := false, relatedKey := "P", name := "q" }]'
)

# The frozen tactic body's opening two lines, unique in the file: the `have` is inserted
# BEFORE them and they are re-emitted verbatim, so the frozen script still closes the
# obligation unchanged.
_TAC_HEAD = (
    "  intro fields\n"
    "  unfold problem_spec_collectParentLinks implementation_collectParentLinks"
    " buildParentLinks\n"
)
assert _BASE.count(_TAC_HEAD) == 1, "tactic-head anchor drifted from expected text"

_ADMISS = _swap(
    _BASE,
    _TAC_HEAD,
    "  -- The obligation is SATISFIABLE at a task-shaped input, discharged here BY\n"
    "  -- EVALUATION before the general obligation is closed below.\n"
    "  have _ground : problem_spec_collectParentLinks\n"
    f"      {_ADM_INPUT}\n"
    "      (implementation_collectParentLinks\n"
    f"        {_ADM_INPUT}) := by\n"
    "    unfold problem_spec_collectParentLinks implementation_collectParentLinks\n"
    "    decide\n"
    + _TAC_HEAD,
)


def _fld(oo, pl, key, nm):
    return ("{ isOneToOne := %s, parentLink := %s, relatedKey := %r, name := %r }"
            % ("true" if oo else "false", "true" if pl else "false", key, nm)
            ).replace("'", '"')


def _wit(fields_lit, note):
    """A refutation witness: `¬ problem_spec … (implementation … fields)` at a
    concrete literal `fields`. The carrier is fully `DecidableEq` and every callee
    (buildParentLinks / dictInsert) is a transparent fold, so `decide` closes the
    disequality after unfolding. It ELABORATES against a rival that diverges from the
    spec at `fields`, and FAILS on gold (which satisfies the spec at every input) —
    SEEN to discriminate both ways in a scratch build."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_collectParentLinks\n"
        f"    [{fields_lit}]\n"
        f"    (implementation_collectParentLinks\n"
        f"      [{fields_lit}]) := by\n"
        f"  unfold problem_spec_collectParentLinks implementation_collectParentLinks\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-filter-then-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FILTERFOLD,
        "rationale": (
            "structurally-different but CORRECT impl making TWO passes: `List.filter` the "
            "eligible fields, then fold `dictInsert` over the survivors with no guard. "
            "Behaviourally identical to gold on every input, but NOT definitionally the "
            "spec's single guarded fold — the reproof needs a filter/fold FUSION lemma "
            "(induction + guard case-split, as an in-proof `have`; no new top-level "
            "theorem/lemma, no axiom/sorry). The theorem STATEMENT is byte-identical. This "
            "replaces an earlier positive whose impl WAS `buildParentLinks`'s body verbatim "
            "and so verified by `rfl` — definitionally the spec target, hence a tautology "
            "that measured nothing. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to the one-pass guarded-fold shape)."
        ),
    },
    {
        "id": "pos-recursive-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RECURSIVE,
        "rationale": (
            "structurally-different but CORRECT impl using an explicit tail-recursive "
            "helper that threads the mapping as an accumulator — a different RECURSION "
            "SCHEME, not a fold, and not the monadic loop either. Behaviourally identical "
            "to gold on every input. The reproof must GENERALIZE the accumulator over the "
            "induction (no fixed accumulator makes the goal reflexive), done as an in-proof "
            "`have`. The theorem STATEMENT is byte-identical; the helper is an impl-region "
            "`def`, which the variant scope admits. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to `List.foldl` as the way the scan is expressed)."
        ),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: a pure fold whose per-field lambda "
            "NEGATES the eligibility test and records in the ELSE branch. Behaviourally "
            "identical to gold on every input. The theorem STATEMENT is byte-identical; "
            "its proof is reproven honestly (pointwise congruence + by_cases on the guard) "
            "— no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to one syntactic branch orientation)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "adm-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADMISSIBILITY — added by audit; this battery previously carried NO case of "
            "this kind, so the PRECOND-TOO-STRONG direction, one of the three this gate "
            "exists to test, was untested. The prior justification ('the obligation binds "
            "no precondition hypothesis, so nothing could be PRECOND-TOO-STRONG') does not "
            "follow: on a total carrier the analogue of an over-strong precondition is the "
            "obligation being UNSATISFIABLE at exactly a task-shaped input, and a spec no "
            "implementation could discharge precisely where the behaviour matters is broken "
            "in that direction even with no hypothesis bound. Nor does the ∀ cover it "
            "transitively — a tactic can close a universal without any concrete point ever "
            "being EVALUATED. So this case discharges the postcondition BY EVALUATION, as a "
            "`have`, at the concrete two-relation scenario the behaviour is about (a "
            "designated parent link and an ordinary one-to-one relation targeting the SAME "
            "base, the ordinary one declared later, so the eligibility gate must reject the "
            "second while the mapping retains the first), and only then closes the frozen "
            "obligation with the frozen tactic body VERBATIM. The `have` is bound to an "
            "unused name, so it cannot weaken the goal; the theorem STATEMENT is "
            "byte-identical; no declaration, axiom, or `sorry` is added. The step is "
            "INFORMATIVE rather than a tautology, checked by control rather than asserted: "
            "the same `have` shape asserting the postcondition of a WRONG result (the empty "
            "mapping) at the same input does NOT close — `decide` reports it proved "
            "`[] = buildParentLinks [...]` false — so `decide` is genuinely evaluating the "
            "claim here. If this case REJECTS, the modeled behaviour is unsatisfiable at a "
            "normal input it must admit => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-drop-parent-link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_PL,
        "refinement": (
            "this IS the pre-patch behaviour: record on the one-to-one test ALONE, "
            "without the parent-link-designation conjunct the fix adds. Its faithful real "
            "patch is the UNCHANGED repo, which records an ordinary one-to-one relation "
            "targeting a base and then promotes it, raising the misconfiguration error for "
            "that ordinary relation — exactly the reported bug. The F2P case that asserts "
            "an ordinary one-to-one relation to the parent produces NO error still fails. "
            "Does NOT resolve; a verifying rival would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the eligibility sub-obligation (the `parentLink` conjunct). A "
            "field with isOneToOne=true, parentLink=false is skipped by gold but recorded "
            "by the rival, so the results differ. Witness varies the parentLink binder to "
            "false while holding isOneToOne=true. If it VERIFIES => SPEC-TOO-WEAK (the "
            "parent-link designation is not enforced)."
        ),
        # isOneToOne=true, parentLink=false: gold skips -> []; rival records -> [(A, …)].
        "witness": _wit(_fld(True, False, "A", "x"),
                        "one-to-one, NOT parent link: gold skips, prepatch rival records"),
    },
    {
        "id": "weak-drop-onetoone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_OO,
        "refinement": (
            "records on the parent-link-designation ALONE, without the one-to-one test. "
            "Its faithful real patch drops the `isinstance(field, OneToOneField)` guard, "
            "so a non-one-to-one field that happens to carry the parent-link marker enters "
            "the mapping and is promoted like a link — a field the base selection is "
            "supposed to exclude — breaking the pk/link setup the F2P tests exercise. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the eligibility sub-obligation (the `isOneToOne` conjunct — the "
            "OTHER boolean gate, which the nagini carrier folded into an implicit "
            "list-membership filter). A field with isOneToOne=false, parentLink=true is "
            "skipped by gold but recorded by the rival. Witness varies the isOneToOne "
            "binder to false while holding parentLink=true — so across the two "
            "eligibility rivals BOTH toggles are exercised in BOTH states. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the one-to-one gate is not enforced)."
        ),
        # isOneToOne=false, parentLink=true: gold skips -> []; rival records -> [(A, …)].
        "witness": _wit(_fld(False, True, "A", "x"),
                        "parent-link marker but NOT one-to-one: gold skips, rival records"),
    },
    {
        "id": "weak-skip-first-scanned",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP0,
        "refinement": (
            "applies the eligibility gate correctly at every position EXCEPT the first "
            "scanned field, which it never records (a faithful `if idx and …:` patch). "
            "When a genuine parent link is the first scanned field — the exact ordering "
            "the issue reports as broken — its key is dropped, the related model has no "
            "recorded link, and the MTI pk setup breaks. The F2P case with the parent link "
            "declared first still fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the order/retain sub-obligation. Gold records a genuine parent "
            "link regardless of its scanned index; the rival drops it at index 0. Witness "
            "is a single ELIGIBLE field (isOneToOne=true, parentLink=true) at position 0: "
            "gold records it, the rival returns empty. Partial-domain — correct on i>0, "
            "wrong on the first element. If it VERIFIES => SPEC-TOO-WEAK (position-0 "
            "retention is unpinned)."
        ),
        # single eligible field at index 0: gold -> [(A, …)]; rival -> [].
        "witness": _wit(_fld(True, True, "A", "x"),
                        "genuine parent link, first scanned: gold records, skip-first rival drops"),
    },
    {
        "id": "weak-record-nonparent-on-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEYVAL,
        "refinement": (
            "records eligible fields always (keeps every genuine parent link) but ALSO "
            "records any field whose related-model identity is one particular token, "
            "regardless of its flags (a faithful `if eligible or make_model_tuple(related) "
            "== <fixed token>:` patch). For that target an ordinary non-eligible field is "
            "recorded and promoted, and the misconfiguration error fires for it — the F2P "
            "assertion that ordinary relations to that parent are NOT promoted fails on "
            "that sub-domain. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the eligibility sub-obligation on a VALUE sub-domain of "
            "relatedKey. A field with relatedKey=\"Z\" that is NOT eligible "
            "(isOneToOne=true, parentLink=false) is skipped by gold but recorded by the "
            "rival. Witness varies the relatedKey binder to the trigger value — a "
            "value-partial-domain class invisible to a byte fuzzer. If it VERIFIES => "
            "SPEC-TOO-WEAK on that relatedKey sub-domain."
        ),
        # relatedKey="Z", not eligible: gold skips -> []; rival records -> [(Z, …)].
        "witness": _wit(_fld(True, False, "Z", "x"),
                        "non-eligible field on the trigger relatedKey: gold skips, rival records"),
    },
    {
        "id": "weak-first-write-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRSTWIN,
        "refinement": (
            "keeps the FIRST designated parent link per related model and ignores later "
            "ones, instead of the repo's last-write-wins dict assignment (a faithful "
            "`if eligible and related_key not in parent_links:` patch). When two "
            "designated parent links target the same base, `_prepare` promotes a DIFFERENT "
            "field object than the patched repo does (the first, not the last), so field "
            "identity / pk promotion downstream diverges from gold. Does NOT refine the "
            "patched behaviour."
        ),
        "rationale": (
            "REJECTED by the last-write-wins sub-obligation. Eligibility holds for this "
            "rival (every recorded field is eligible; no key is lost), so membership-only "
            "checks miss it — the exact weakness a first-writer-wins impl exploits. When "
            "two ELIGIBLE fields share a relatedKey and differ by `name`, gold records the "
            "LAST (dictInsert drops the prior, appends the new) but the rival keeps the "
            "FIRST. Witness varies the `name` binder across two same-key fields, so the "
            "recorded field object differs. If it VERIFIES => SPEC-TOO-WEAK (the tie-break "
            "/ which-field pinning is unpinned)."
        ),
        # two eligible fields, same key "A", names x then y:
        # gold last-write-wins -> [(A, name=y)]; rival first-write -> [(A, name=x)].
        "witness": _wit(_fld(True, True, "A", "x") + ",\n     " + _fld(True, True, "A", "y"),
                        "two parent links to the same model: gold keeps the last, "
                        "first-write rival keeps the first"),
    },
    {
        "id": "weak-no-stale-removal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOSTALE,
        "refinement": (
            "appends each recorded field without first removing any entry the mapping "
            "already holds for that related model — a faithful patch that accumulates "
            "`(key, field)` pairs in a list instead of assigning into the mapping. The "
            "stale field for a rewritten target survives, so a consumer that looks the "
            "target up can retrieve the SUPERSEDED field and promote it, and the extra "
            "entry also makes the collection report more links than there are targets. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED because the result must BE the mapping. This rival satisfies "
            "eligibility (every recorded field is eligible) AND retains the correct field "
            "as the last entry for each key, so it survives both the eligibility and the "
            "last-write sub-obligations as a membership/lookup check would state them. It "
            "is refuted only by the stale-entry-removal half of the modeled assignment — "
            "the `filter` that drops the prior entry, which no other rival attacks (the "
            "others all vary the guard or the append). Witness: two eligible fields sharing "
            "a relatedKey, differing by `name` — gold yields one entry, the rival two. If "
            "it VERIFIES => SPEC-TOO-WEAK (a superseded entry may linger in the mapping)."
        ),
        # two eligible fields, same key: gold -> [(A,y)]; rival -> [(A,x),(A,y)].
        "witness": _wit(_fld(True, True, "A", "x") + ",\n     " + _fld(True, True, "A", "y"),
                        "rewritten key: gold drops the superseded entry, "
                        "append-only rival keeps both"),
    },
    {
        "id": "weak-key-by-field-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEYBYNAME,
        "refinement": (
            "files each recorded field under the field's OWN identity instead of the "
            "identity of the model it points at — a faithful patch that keys the mapping by "
            "`field.name` rather than by the derived related-model token. The set of "
            "collected fields is exactly right, but the consumer looks each target model up "
            "by its own identity and finds nothing, so no declared link is ever matched to "
            "its target and the auto-created link is fabricated instead. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the keying sub-obligation. Eligibility is exactly right here and "
            "every eligible field is recorded exactly once, so any check on WHICH fields "
            "were collected — or on how many — passes; only the key each is filed under is "
            "wrong. Pins that the map key is the related-model identity, the one attribute "
            "no other rival varies in the KEY position (the others vary it only as a value "
            "trigger or a collision source). Witness: one eligible field whose `name` "
            "differs from its `relatedKey`, so the two keyings are distinguishable. If it "
            "VERIFIES => SPEC-TOO-WEAK (the map key is unpinned)."
        ),
        # one eligible field, name != relatedKey: gold -> [(A,…)]; rival -> [(x,…)].
        "witness": _wit(_fld(True, True, "A", "x"),
                        "eligible field whose own identity differs from its target's: "
                        "gold keys by the target, rival keys by the field"),
    },
    {
        "id": "weak-forge-flags-on-a-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FORGE,
        "refinement": (
            "rewrites both eligibility attributes to true on a local copy of the scanned "
            "fields and then records every one of them — a faithful patch that sets the "
            "designation on each candidate before testing it. Every ordinary one-to-one "
            "relation to a base is then collected and promoted, which is the reported "
            "misbehaviour in its strongest form: the explicit designation stops mattering "
            "at all. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED on the MERITS, and that is the point of the case. This is the lean "
            "analogue of the nagini sibling's MANDATORY frame-mutation probe, LANDED rather "
            "than recorded as inexpressible: nagini's rivals wrote into a read-only input so "
            "that a clause quantified over that input held vacuously, and were rejected by "
            "the permission system rather than by the postcondition. Lean has no aliasing, "
            "so the write itself does not port — but the INTENT does (forge the attributes, "
            "then record unconditionally), and here it is refuted by the spec directly, "
            "because `fields` in the obligation denotes the caller's value and no local copy "
            "can change it. Witness: a one-to-one field NOT designated the parent link — "
            "gold skips it, the forging rival records it. If it VERIFIES => SPEC-TOO-WEAK "
            "(the obligation could be satisfied against a rewritten input)."
        ),
        # isOneToOne=true, parentLink=false: gold skips -> []; forger records -> [(A,…)].
        "witness": _wit(_fld(True, False, "A", "x"),
                        "forged local copy of the input: gold skips the non-designated "
                        "field, forging rival records it"),
    },
]


# No @ContractOnly axioms and no opaque callees: the guarded last-write-wins mapping
# build (buildParentLinks / dictInsert) is modeled DEEPLY over a transparent carrier,
# so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
