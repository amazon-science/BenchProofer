# properties.py — G-PBT falsification battery for django__django-13925 (lean lane).
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
#   checkDefaultPk : CheckInput → List Advisory
#   A model is described by five boolean observations plus the advisory payload it
#   would carry (an identity `modelObj` and the constant message/hint text). The
#   single postcondition `problem_spec_checkDefaultPk` pins the WHOLE result as an
#   equality against the input:
#     result = (if reportAutoPkIssue c then [autoPkWarning c] else [])
#   which decomposes into two attackable facets:
#     (D) the DECISION `reportAutoPkIssue c` = autoCreated ∧ ¬(pkIsToOneRelation ∧
#         pkRelationIsParentLink) ∧ ¬defaultAutoFieldOverridden ∧ ¬appConfigOverridden.
#         A five-input boolean; every conjunct is load-bearing and each is attacked
#         by a rival that mishandles exactly it. The added ¬(toOne ∧ parentLink)
#         conjunct is the bug delta the fix introduces (see below).
#     (P) the PAYLOAD/CONTAINER: when the decision holds the result is EXACTLY the
#         one-element list `[autoPkWarning c]`, whose advisory carries the frozen
#         identifier tag, the model's own identity, and the supplied text in its
#         respective fields; when it does not hold the result is EXACTLY `[]`. Four
#         separable facets, one rival each: the model IDENTITY (weak-wrong-obj), the
#         identifier TAG (weak-wrong-id), the two TEXT fields individually rather
#         than as a set (weak-swap-msg-hint), and the container's LENGTH
#         (weak-duplicate-advisory). The last three were added by audit; as ported
#         the battery probed only the identity, so a rival could emit the wrong
#         advisory, or permute its text, at exactly the right times unchallenged.
#   reportAutoPkIssue and autoPkWarning are total, transparent boolean/record folds
#   over the input (no opaque callee, no answer-key), so every witness is stated at
#   a concrete literal input and closed by `decide` — no conditioning on the carrier.
#
# THE BUG DELTA. The fix adds the ¬(pkIsToOneRelation ∧ pkRelationIsParentLink)
#   conjunct: an auto-created primary key that is really a to-one relation LINKING
#   the model to a parent it extends must NOT raise the advisory (the key is the
#   parent's responsibility). The pre-patch decision lacked that conjunct and warned
#   at (autoCreated, toOne, parentLink)=(T,T,T) — exactly the F2P discriminator. The
#   `weak-prepatch-drop-reuse` rival IS that pre-patch decision.
#
# LANES THAT DO NOT PORT (stated, per instruction, not silently dropped):
#   * FRAME-MUTATION (nagini's MANDATORY `weak-frame-mutate`: pk was held at
#     Acc(...,1/2) read-only and the rival WROTE pk.reuses_ancestor_key_b before
#     reading it). The PROPERTY that case tested — "a write through a read-only
#     input is refused for insufficient permission" — has no counterpart here:
#     Lean is referentially transparent, with no aliasing and no fractional
#     permission, so there is no read-only-ness for a rival to violate.
#     AUDIT NOTE (measured, not argued): the rival TEXT does transliterate — the
#     write becomes a functional record update `let c := { c with
#     pkRelationIsParentLink := false }` ahead of the gold guard, and that module
#     elaborates. What it does NOT do is test anything new: that impl is
#     EXTENSIONALLY EQUAL to `weak-prepatch-drop-reuse` below (both warn exactly
#     when autoCreated ∧ ¬project ∧ ¬app), proven by a `cases`-split equality
#     theorem that built at exit 0 against the update-rival and exit 1 against
#     the frozen impl. So the class is redundant here rather than merely
#     unwritable, and adding it would duplicate an existing rival's witness point.
#     See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. `implementation_checkDefaultPk` is a total Lean
#     `def`; a non-terminating implementation cannot be written at all, so on lean
#     this class is genuinely VACUOUS (NOT the velvet-partial "known spec hole").
#     The nagini sibling carries no divergence case anyway. See 'assessment'.
#   * ADMISSIBILITY — DOES port; the earlier "N/A" reading was wrong and is
#     corrected here (second audit). nagini's `admiss-self-call` defended the
#     half-permission Requires, and it is true that the lean obligation
#     `∀ (c : CheckInput), problem_spec … c (implementation … c)` carries NO
#     precondition hypothesis. But "the frozen obligation has no precondition" is
#     NOT a reason to drop the lane: on a total carrier the analogue of
#     PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, and a positive that discharges the obligation at that
#     concrete input — by evaluation, as a `have`, before closing the frozen
#     obligation verbatim — tests that directly. Landed as `admiss-ground-f2p`
#     below, mirroring the shape sibling lean cells already carry. MEASURED
#     load-bearing, which is the whole point: the same two `have`s fail (each at
#     its OWN `have`, not at the trailing frozen proof) against a wrong impl —
#     exit 1 vs the payload-corrupting rival and exit 1 vs the pre-patch rival,
#     against exit 0 for the frozen impl. So the case is a real probe, not
#     decoration. See 'assessment'.
#   * AXIOM_TESTS (nagini's grounded-oracle enumeration). The axiom lane is G-AX's
#     job; this gate ignores them. The decision is modeled DEEPLY (reportAutoPkIssue),
#     so there is no consumed axiom here anyway.
from pathlib import Path

INSTANCE = "django__django-13925"

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
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-if-expression positive, whose different impl shape needs an (equally cheap,
# honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro c\n"
    "  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning\n"
    "  by_cases h : c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden\n"
    "  · simp only [h, Id.run, if_true]; rfl\n"
    "  · simp only [h, Id.run]; rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-let-bound-decision: structurally-DIFFERENT but behaviourally identical. The
# decision is bound to a local `warranted` before the branch; both branch bodies and
# the result are otherwise unchanged, so the output equals the frozen impl's on every
# input. The frozen `theorem correct_checkDefaultPk` statement is kept byte-identical
# AND the frozen proof body still closes (the `let` binding is definitionally
# transparent). No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG.
_POS_LET = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  let warranted := c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden\n"
    "  if warranted then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# pos-pure-if-expression: a structurally different CORRECT impl written as a pure
# `if`-expression (no `Id.run do` monad, no early `return`), directly returning the
# list. Semantics identical on every input. The theorem STATEMENT is byte-identical;
# its proof is reproven honestly (`split <;> rfl`) inside proof-start/proof-end — no
# new axiom/lemma/sorry, just the cheapest tactic for the new shape. If it FAILS =>
# SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_checkDefaultPk (c : CheckInput) : List Advisory :=\n"
        "  if c.autoCreated\n"
        "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
        "      && !c.defaultAutoFieldOverridden\n"
        "      && !c.appConfigOverridden then\n"
        "    [{ id := \"models.W042\", obj := c.modelObj,\n"
        "       msg := c.warnMsg, hint := c.warnHint }]\n"
        "  else\n"
        "    []",
    ),
    _PROOF,
    "  intro c\n"
    "  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning\n"
    "  split <;> rfl",
)


# pos-early-out-reorder (added by audit): the DIRECT port of nagini's
# `pos-control-reorder`, which the lean battery had dropped without recording it. The
# guard is decomposed into four per-conjunct early-outs returning `[]`, with the
# advisory in the fall-through — the control flow is INVERTED relative to the frozen
# impl (four sequential exits instead of one conjunction), which is a genuinely
# different shape rather than a rebinding of the same expression. The theorem STATEMENT
# stays byte-identical; the proof is reproven by exhausting the five booleans
# (`cases a <;> cases t <;> ...`), which is honest work and no new axiom/lemma/sorry.
# This is the strongest available soundness control: unlike the `let` positive it does
# not reduce to the frozen impl definitionally, so it tests that the postcondition is
# BEHAVIOURAL. If it FAILS => SPEC-TOO-STRONG.
_POS_EARLY = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
        "  if !c.autoCreated then return []\n"
        "  if c.pkIsToOneRelation && c.pkRelationIsParentLink then return []\n"
        "  if c.defaultAutoFieldOverridden then return []\n"
        "  if c.appConfigOverridden then return []\n"
        "  return [{ id := \"models.W042\", obj := c.modelObj,\n"
        "            msg := c.warnMsg, hint := c.warnHint }]",
    ),
    _PROOF,
    "  intro c\n"
    "  obtain ⟨a, t, p, d, g, o, m, hh⟩ := c\n"
    "  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning\n"
    "  cases a <;> cases t <;> cases p <;> cases d <;> cases g <;> rfl",
)


# ===========================================================================
# ADMISSIBILITY — the obligation must be SATISFIABLE at a normal, F2P-shaped
# input, not only in the abstract. Added by the second audit; the first port
# recorded this lane as N/A on the grounds that the frozen obligation carries no
# precondition, which is not a sufficient reason (see header).
# ===========================================================================

# The two concrete inputs the failing/passing tests actually exercise, as literal
# CheckInputs. `_ADM_F2P` is the F2P shape: an auto-created primary key that is a
# to-one relation linking the model to a parent it extends, with no default type
# opted into at either level — the configuration on which the advisory must be
# SUPPRESSED. `_ADM_P2P` is the neighbouring pre-existing-test shape: the same
# thing with a plain (non-relation) auto-created key, on which the advisory must be
# EMITTED with its full payload. Together they pin BOTH branches of the decision at
# ground inputs, so the case cannot pass by landing twice in the same branch.
_ADM_F2P = (
    '{ autoCreated := true, pkIsToOneRelation := true, pkRelationIsParentLink := true, '
    'defaultAutoFieldOverridden := false, appConfigOverridden := false, modelObj := 4, '
    'warnMsg := "m", warnHint := "h" }'
)
_ADM_P2P = (
    '{ autoCreated := true, pkIsToOneRelation := false, pkRelationIsParentLink := false, '
    'defaultAutoFieldOverridden := false, appConfigOverridden := false, modelObj := 4, '
    'warnMsg := "m", warnHint := "h" }'
)

# The ground instances are PREPENDED to the frozen tactic body, which then closes
# the byte-identical frozen statement verbatim. Nothing is assumed: no new
# top-level declaration, no axiom/lemma/sorry, and the theorem statement is
# untouched — only the tactic body grows by four `have`s.
#
# Each input gets TWO `have`s on purpose. The `problem_spec …` one alone would be
# closable without ever showing WHICH outcome the input produces (the spec pins
# `result` to a term over the same input, so it reads the same whichever branch is
# taken). The second `have` EVALUATES the modeled behavior at that input down to a
# concrete result — `[]` for the parent-link inherited key, and the fully-populated
# single advisory for the plain auto-created key — which is what pins the admission
# to the branch the real tests exercise. Measured load-bearing: against a rival
# that corrupts the payload the `_adm_plain_value` have fails, and against the
# pre-patch rival the `_adm_inherited` have fails, each AT ITS OWN have.
_ADM_HAVES = (
    "  have _adm_inherited : problem_spec_checkDefaultPk\n"
    f"      ({_ADM_F2P})\n"
    "      (implementation_checkDefaultPk\n"
    f"      ({_ADM_F2P})) := by\n"
    "    unfold problem_spec_checkDefaultPk implementation_checkDefaultPk"
    " reportAutoPkIssue autoPkWarning\n"
    "    decide\n"
    "  have _adm_inherited_value : implementation_checkDefaultPk\n"
    f"      ({_ADM_F2P}) = [] := by decide\n"
    "  have _adm_plain : problem_spec_checkDefaultPk\n"
    f"      ({_ADM_P2P})\n"
    "      (implementation_checkDefaultPk\n"
    f"      ({_ADM_P2P})) := by\n"
    "    unfold problem_spec_checkDefaultPk implementation_checkDefaultPk"
    " reportAutoPkIssue autoPkWarning\n"
    "    decide\n"
    "  have _adm_plain_value : implementation_checkDefaultPk\n"
    f"      ({_ADM_P2P})"
    ' = [{ id := "models.W042", obj := 4, msg := "m", hint := "h" }] := by decide\n'
)

_POS_ADMISS = _swap(_BASE, _PROOF, _ADM_HAVES + _PROOF)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-prepatch-drop-reuse: THE bug delta. Drops the ¬(toOne ∧ parentLink) conjunct —
# the literal pre-patch decision. Correct on every model whose pk is not a
# parent-linking to-one relation, WRONG exactly on the auto-created inherited
# parent-link key (toOne ∧ parentLink), which it warns on and gold suppresses.
_RIV_DROP_REUSE = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-suppress-on-toone-only: over-suppresses using pkIsToOneRelation ALONE (drops
# the conjunction with pkRelationIsParentLink). Correct whenever the two flags agree,
# WRONG on (toOne, parentLink)=(T,F): a to-one pk that is NOT a parent link should
# still warn, but this suppresses it.
_RIV_SUPPRESS_TOONE = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !c.pkIsToOneRelation\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-ignore-appconfig: drops the appConfigOverridden conjunct. Correct whenever the
# application-level default is not opted into, WRONG when only the application-level
# override is set (should suppress, this still warns).
_RIV_IGNORE_APPCFG = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-ignore-project: drops the defaultAutoFieldOverridden conjunct. Correct whenever
# the project-level default is not opted into, WRONG when only the project-level
# override is set (should suppress, this still warns). The dual of the previous rival
# on the OTHER override binder.
_RIV_IGNORE_PROJECT = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-ignore-autocreated: drops the autoCreated conjunct — the primary trigger.
# Correct whenever the pk was auto-created, WRONG on a model whose pk was DECLARED by
# the author (autoCreated=F): the advisory is for auto-created keys only, but this
# warns on an explicitly-declared pk too.
_RIV_IGNORE_AUTO = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-wrong-obj: makes the RIGHT decision on every input (clause (D) holds) but on
# the emit branch attaches the advisory to a FABRICATED model identity (constant 0)
# instead of the model's own `modelObj`. Attacks clause (P) — the payload identity a
# rival could leave unconstrained if the spec did not pin the advisory's fields.
_RIV_WRONG_OBJ = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := 0,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-wrong-id (added by audit): makes the RIGHT decision and carries the model's own
# identity and text, but tags the advisory with a DIFFERENT identifier. The battery as
# ported attacked the `obj` field and the list LENGTH but left the `id` field — the one
# facet of (P) that is a frozen constant rather than a carried input — unprobed, so
# nothing demonstrated that the spec pins WHICH advisory is emitted, only that one is.
_RIV_WRONG_ID = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W041\", obj := c.modelObj,\n"
    "              msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)

# weak-swap-msg-hint (added by audit): makes the RIGHT decision, tags the RIGHT
# identifier and the RIGHT model, but TRANSPOSES the two text fields — message text
# delivered as the hint and vice versa. The remaining unprobed facet of (P): the ported
# battery pinned obj, and length, but never showed that each supplied string lands in
# its OWN field, which is the part of the payload a reshaped record could permute for
# free.
_RIV_SWAP_TEXT = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj,\n"
    "              msg := c.warnHint, hint := c.warnMsg }]\n"
    "  return []",
)

# weak-duplicate-advisory: makes the RIGHT decision and carries the RIGHT payload, but
# emits the advisory TWICE. Attacks clause (P)'s CONTAINER shape — the result must be
# exactly the one-element list, not a list of two identical advisories.
_RIV_DUPLICATE = _swap(
    _BASE,
    _IMPL,
    "def implementation_checkDefaultPk (c : CheckInput) : List Advisory := Id.run do\n"
    "  if c.autoCreated\n"
    "      && !(c.pkIsToOneRelation && c.pkRelationIsParentLink)\n"
    "      && !c.defaultAutoFieldOverridden\n"
    "      && !c.appConfigOverridden then\n"
    "    return [{ id := \"models.W042\", obj := c.modelObj, msg := c.warnMsg, hint := c.warnHint },\n"
    "            { id := \"models.W042\", obj := c.modelObj, msg := c.warnMsg, hint := c.warnHint }]\n"
    "  return []",
)


def _wit(auto, toOne, pl, dov, aov, note, obj=5):
    """A refutation witness: `¬ problem_spec_checkDefaultPk c (implementation … c)` at
    a concrete literal `CheckInput`. Every field is a boolean/`Nat`/`String` literal,
    so `decide` reduces reportAutoPkIssue and autoPkWarning and closes the
    disequality. Elaborates against a rival that diverges from the spec at this input,
    and FAILS on gold (which satisfies the spec at every input) — SEEN to discriminate
    both ways. The five boolean fields plus `modelObj` are varied across the battery so
    each conjunct of (D) and each facet of (P) is probed at its own point. `warnMsg` and
    `warnHint` are held at the DISTINCT literals "m" and "h" (not one shared string):
    weak-swap-msg-hint transposes those two fields, and equal text would make that
    rival's witness vacuous rather than discriminating."""
    b = lambda x: "true" if x else "false"
    c = ('{ autoCreated := %s, pkIsToOneRelation := %s, pkRelationIsParentLink := %s, '
         'defaultAutoFieldOverridden := %s, appConfigOverridden := %s, modelObj := %d, '
         'warnMsg := "m", warnHint := "h" }'
         % (b(auto), b(toOne), b(pl), b(dov), b(aov), obj))
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_checkDefaultPk\n"
        f"    ({c})\n"
        f"    (implementation_checkDefaultPk\n"
        f"    ({c})) := by\n"
        f"  unfold problem_spec_checkDefaultPk implementation_checkDefaultPk reportAutoPkIssue autoPkWarning\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-let-bound-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "structurally-different but CORRECT impl: the decision is bound to a local "
            "`warranted` before the branch, keeping both branch bodies and the result, "
            "so the output equals the frozen impl's on every input. The theorem "
            "statement is byte-identical and the FROZEN proof body still closes (the "
            "let binding is definitionally transparent) — a faithful restructure with "
            "no reproof and no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to one syntactic impl shape). Source: (D)+(P)."
        ),
    },
    {
        "id": "pos-pure-if-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure `if`-expression "
            "(no `Id.run do`, no early return), directly returning the list. Semantics "
            "identical on every input. The theorem STATEMENT is byte-identical; its "
            "proof is reproven honestly with `split <;> rfl` — no new axiom/lemma/"
            "sorry, just the cheapest tactic for the new shape. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape "
            "rather than the behaviour). Source: (D)+(P)."
        ),
    },
    {
        "id": "pos-early-out-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EARLY,
        "rationale": (
            "the direct port of the nagini battery's `pos-control-reorder`, restored by "
            "audit. A CORRECT impl whose control flow is inverted: four per-conjunct "
            "early-outs returning `[]`, advisory in the fall-through. Unlike the `let` "
            "positive this does NOT reduce to the frozen impl definitionally — the "
            "frozen proof body does not close it — so it is the control that actually "
            "tests whether the postcondition is BEHAVIOURAL rather than shape-bound. "
            "Statement byte-identical; reproven by exhausting the five booleans, no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG. Source: (D)+(P)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "the obligation must be SATISFIABLE at the concrete inputs the real "
            "failing/passing tests exercise, not merely in the abstract. The frozen "
            "impl is kept verbatim; the spec predicate is discharged BY EVALUATION, "
            "as `have`s, at two ground inputs — the auto-created parent-linking "
            "to-one primary key with no default type opted into (where the advisory "
            "must be suppressed, and the second `have` evaluates the result to "
            "exactly `[]`), and the plain auto-created key in the same configuration "
            "(where it must be emitted, and the second `have` evaluates the result to "
            "exactly the one-element list carrying the identifier, the model's own "
            "identity and each supplied string in its own field) — before the frozen "
            "obligation is closed verbatim by the frozen tactic body. Both branches "
            "of the decision are therefore pinned at ground inputs, so the case "
            "cannot pass by landing twice in the same branch. Statement "
            "byte-identical, no new axiom/lemma/sorry, no new top-level declaration. "
            "This is the total-carrier analogue of nagini's precondition-admission "
            "probe: the lean obligation has no precondition hypothesis to attack, so "
            "what would correspond to PRECOND-TOO-STRONG here is the obligation "
            "being unsatisfiable at exactly an F2P-shaped input. If it FAILS => the "
            "modeled behaviour cannot be discharged at a normal input. Measured "
            "load-bearing rather than decorative: the same `have`s FAIL (each at its "
            "own `have`) against the pre-patch rival and against a "
            "payload-corrupting rival. Source: (D)+(P) at ground inputs."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch-drop-reuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_REUSE,
        "refinement": (
            "this IS the pre-patch decision: it drops the conjunct suppressing the "
            "advisory for an auto-created primary key that is really a parent-linking "
            "to-one relation. Its faithful real patch is the UNCHANGED (buggy) repo, "
            "which emits the advisory on a model that takes its primary key from a "
            "parent it extends — exactly the regression the fix corrects. The F2P tests "
            "(auto-created inherited pk / explicit inherited pk) assert NO advisory on "
            "such a model, so the faithful real patch FAILS them; it does NOT resolve. "
            "A verifying rival is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (D): at (autoCreated, toOne, parentLink)=(T,T,T) the "
            "spec's decision is False (the ¬(toOne ∧ parentLink) conjunct fails) so the "
            "result must be `[]`, but the rival emits the advisory. Witness probes the "
            "parent-link inherited-key sub-domain the dropped conjunct governs. If it "
            "VERIFIES => SPEC-TOO-WEAK (the bug delta is unpinned)."
        ),
        "witness": _wit(True, True, True, False, False,
                        "parent-link inherited pk: gold suppresses, prepatch rival warns"),
    },
    {
        "id": "weak-suppress-on-toone-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SUPPRESS_TOONE,
        "refinement": (
            "suppresses the advisory on the to-one-relation flag ALONE, dropping the "
            "conjunction with the parent-link flag. It is WRONG against the spec on "
            "the sub-domain toOne ∧ ¬parentLink, which is a different sub-domain from "
            "the pre-patch rival's (toOne ∧ parentLink) — so as a SPEC-strength case "
            "it stands on its own, and its witness is machine-checked below. "
            "HONEST SCOPE (corrected by audit; the earlier text overclaimed): this "
            "rival's faithful real patch would NOT be caught by the harness. The "
            "point it diverges from the spec at — an AUTO-CREATED to-one primary key "
            "that is NOT a parent link — is not a configuration the framework ever "
            "builds: every auto-created to-one primary key it creates is a parent "
            "link, and a to-one primary key that is not a parent link is one the "
            "author declared, hence not auto-created. So the divergence sub-domain is "
            "unreachable in the real project, the faithful real patch agrees with gold "
            "on every F2P and PASS_TO_PASS test, and it WOULD resolve. This case "
            "therefore certifies that the spec pins the CONJUNCTION rather than either "
            "flag alone; it does NOT exhibit a verify-does-not-imply-resolve break. "
            "The genuine such break is weak-prepatch-drop-reuse. Kept deliberately: "
            "the spec constrains this point, so a rival that violates it is a real "
            "uniqueness case, and the carrier models the two flags independently."
        ),
        "rationale": (
            "REJECTED by clause (D): at (autoCreated, toOne, parentLink)=(T,T,F) the "
            "spec's decision is True (¬(T ∧ F) holds) so the result must be the "
            "advisory, but the rival returns `[]`. Witness probes the to-one / "
            "non-parent-link sub-domain that distinguishes it from the pre-patch rival. "
            "If it VERIFIES => SPEC-TOO-WEAK (the conjunction is not enforced)."
        ),
        "witness": _wit(True, True, False, False, False,
                        "to-one non-parent-link pk: gold warns, over-suppress rival silences"),
    },
    {
        "id": "weak-ignore-appconfig",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_APPCFG,
        "refinement": (
            "drops the application-level override conjunct. Its faithful real patch "
            "still emits the advisory when the owning application has opted into a "
            "configured default primary-key type, where the advisory must be "
            "suppressed. The PASS_TO_PASS app-default test asserts NO advisory in that "
            "configuration, so the faithful patch warns spuriously and FAILS it; does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (D): at appConfigOverridden=T (others warranting) the "
            "spec's decision is False so the result must be `[]`, but the rival emits "
            "the advisory. Witness varies the appConfigOverridden binder to True. If it "
            "VERIFIES => SPEC-TOO-WEAK (the application-level override is unpinned)."
        ),
        "witness": _wit(True, False, False, False, True,
                        "app-level default configured: gold suppresses, rival warns"),
    },
    {
        "id": "weak-ignore-project",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_PROJECT,
        "refinement": (
            "drops the project-level override conjunct — the dual of the previous rival "
            "on the OTHER override binder. Its faithful real patch still emits the "
            "advisory when the project has opted into a configured default primary-key "
            "type, where it must be suppressed. The PASS_TO_PASS project-default test "
            "asserts NO advisory in that configuration, so the faithful patch FAILS it; "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (D): at defaultAutoFieldOverridden=T (others "
            "warranting) the spec's decision is False so the result must be `[]`, but "
            "the rival emits the advisory. Witness varies the defaultAutoFieldOverridden "
            "binder to True (holding appConfigOverridden False, unlike the previous "
            "rival). If it VERIFIES => SPEC-TOO-WEAK (the project-level override is "
            "unpinned)."
        ),
        "witness": _wit(True, False, False, True, False,
                        "project-level default configured: gold suppresses, rival warns"),
    },
    {
        "id": "weak-ignore-autocreated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_AUTO,
        "refinement": (
            "drops the primary trigger — the auto-created conjunct. Its faithful real "
            "patch emits the advisory even for a model whose primary key was DECLARED "
            "by the author, where the advisory (which is specifically about "
            "auto-created keys) must never fire. The PASS_TO_PASS explicit-pk test "
            "asserts NO advisory for a declared primary key, so the faithful patch "
            "warns spuriously and FAILS it; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (D): at autoCreated=F (no override, no relation) the "
            "spec's decision is False so the result must be `[]`, but the rival emits "
            "the advisory. Witness varies the autoCreated binder to False. If it "
            "VERIFIES => SPEC-TOO-WEAK (the primary trigger is unpinned)."
        ),
        "witness": _wit(False, False, False, False, False,
                        "author-declared (non-auto) pk: gold silent, rival warns"),
    },
    {
        "id": "weak-wrong-obj",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_OBJ,
        "refinement": (
            "makes the RIGHT emit/suppress decision on every input but attaches the "
            "advisory to a FABRICATED model identity instead of the model the "
            "examination concerns. Its faithful real patch reports the warning against "
            "the wrong object, so the F2P/PASS_TO_PASS assertions — which pin the "
            "advisory's `obj=` to the specific model — fail. A decision-correct impl "
            "that still breaks the pinned payload; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P): on the emit branch the spec demands "
            "`[autoPkWarning c]`, whose advisory carries the model's OWN `modelObj`, "
            "but the rival substitutes the constant 0. Witness sets modelObj to a "
            "non-zero identity (5) at a warranting input so the two advisories differ. "
            "This facet — the payload identity — is what would be left unconstrained "
            "were the spec to pin only the decision. If it VERIFIES => SPEC-TOO-WEAK "
            "(the advisory's identity is unpinned)."
        ),
        "witness": _wit(True, False, False, False, False,
                        "warranting input: gold advisory concerns model 5, rival invents 0",
                        obj=5),
    },
    {
        "id": "weak-wrong-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_ID,
        "refinement": (
            "makes the RIGHT emit/suppress decision and carries the model's own identity "
            "and text, but tags the advisory with a DIFFERENT identifier. Its faithful "
            "real patch emits an advisory under the wrong identifier, so every assertion "
            "that pins the advisory's `id=` — the F2P inherited-key cases and the "
            "PASS_TO_PASS auto-created-key case alike compare against an advisory "
            "carrying the specific identifier — fails on the identifier mismatch. It "
            "does NOT resolve. Added by audit: the ported battery probed the advisory's "
            "`obj` and the list length but never the identifier."
        ),
        "rationale": (
            "REJECTED by clause (P): on the emit branch the spec demands "
            "`[autoPkWarning c]`, whose `id` field is the frozen constant tag, but the "
            "rival substitutes a different tag. Witness is stated at a warranting input "
            "so the emit branch is actually taken and the two advisories differ in the "
            "`id` field alone — the one facet of the payload that is a frozen constant "
            "rather than a carried input, and so the one a rival could redirect without "
            "touching any input. If it VERIFIES => SPEC-TOO-WEAK (the advisory's "
            "identifier is unpinned, and the spec would admit an impl that emits the "
            "wrong advisory at exactly the right times)."
        ),
        "witness": _wit(True, False, False, False, False,
                        "warranting input: gold emits the advisory under its own "
                        "identifier, rival emits a different one",
                        obj=3),
    },
    {
        "id": "weak-swap-msg-hint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP_TEXT,
        "refinement": (
            "makes the RIGHT decision, tags the RIGHT identifier and the RIGHT model, "
            "but TRANSPOSES the two supplied text fields — the message text is delivered "
            "as the hint and the hint as the message. Its faithful real patch emits an "
            "advisory whose two text fields are swapped; the F2P/PASS_TO_PASS assertions "
            "compare the collected advisory against one built with each string in its "
            "own field, so the transposition fails the comparison. Does NOT resolve. "
            "Added by audit: no ported case constrained the text fields at all."
        ),
        "rationale": (
            "REJECTED by clause (P): the spec pins the advisory's `msg` to the supplied "
            "message and its `hint` to the supplied hint, individually — not merely that "
            "both supplied strings appear somewhere in the record. The witness supplies "
            "DISTINCT message and hint text, so a transposition is observable; had the "
            "two been equal the case would be vacuous, which is why the witness varies "
            "them. If it VERIFIES => SPEC-TOO-WEAK (the payload's text fields are pinned "
            "only as a set, so the spec would admit an impl that permutes them)."
        ),
        "witness": _wit(True, False, False, False, False,
                        "warranting input with distinct message/hint text: gold carries "
                        "each in its own field, rival transposes them",
                        obj=9),
    },
    {
        "id": "weak-duplicate-advisory",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DUPLICATE,
        "refinement": (
            "makes the RIGHT decision AND carries the RIGHT payload, but emits the "
            "advisory TWICE. Its faithful real patch contributes a two-element list "
            "where exactly one advisory is expected, so the F2P/PASS_TO_PASS "
            "assertions — which compare the collected warnings against a list holding a "
            "SINGLE advisory — fail on the duplicate. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P), the CONTAINER shape: on the emit branch the spec "
            "demands EXACTLY the one-element list `[autoPkWarning c]`, but the rival "
            "returns a two-element list. Witness probes the same warranting input as "
            "weak-wrong-obj but attacks the list LENGTH rather than the advisory's "
            "identity — a distinct clause of (P). If it VERIFIES => SPEC-TOO-WEAK (the "
            "result container is unpinned)."
        ),
        "witness": _wit(True, False, False, False, False,
                        "warranting input: gold emits one advisory, rival emits two",
                        obj=7),
    },
]


# No @ContractOnly axioms and no opaque callees: the five-input boolean decision
# (reportAutoPkIssue) and the advisory payload (autoPkWarning) are modeled DEEPLY over
# transparent carriers, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
