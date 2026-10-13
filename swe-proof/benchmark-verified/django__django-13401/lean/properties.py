# properties.py — G-PBT falsification battery for django__django-13401 (lean lane).
#
# NOT a Lean module; a manifest of adversarial cases the gate elaborates against
# the frozen spec. PORTED from the nagini sibling's properties.py — the nagini
# file is the design document and its per-case reasoning is carried over here,
# re-expressed against this backend's carrier.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean + mapping.md + instance.json)
# ---------------------------------------------------------------------------
# This is a MULTI-SITE change and — unusually for this corpus — the lean bundle
# models ALL THREE behaviors, so there are THREE obligations to defend and
# attack, not one:
#
#   theorem correct_fieldEq      : ∀ (a b : FieldId), problem_spec_fieldEq …
#   theorem correct_fieldLt      : ∀ (a b : FieldId), problem_spec_fieldLt …
#   theorem correct_fieldHashKey : ∀ (a : FieldId),   problem_spec_fieldHashKey …
#
# The carrier is `FieldId { creationCounter : Int, model : Option (String ×
# String) }`: a creation-order counter plus an OPTIONAL two-component identity of
# the thing the descriptor is attached to. Each spec pins its result exactly —
# there is no output freedom left anywhere:
#
#   * problem_spec_fieldEq a b result
#       result = ((a.creationCounter == b.creationCounter) && (a.model == b.model))
#     TWO independent conjuncts. Attacked separately: a rival may drop the
#     identity conjunct (the whole point of the change), keep only ONE COMPONENT
#     of the identity, keep only the identity's PRESENCE, drop the counter
#     conjunct, or weaken the conjunction to a disjunction.
#
#   * problem_spec_fieldLt a b result
#       result = fieldLtPure a b
#     `fieldLtPure` is a `pure`-region `def` fully unfolded over the two inputs'
#     own fields — a GROUNDED reference, not an opaque answer key — with THREE
#     independent decision arms: (i) counter-first ordering when the counters
#     differ or neither is attached, (ii) an unattached-precedes-attached
#     tie-break when exactly one is attached, (iii) lexicographic identity
#     comparison (label first, then name) when both are attached at one counter.
#     Every arm is attacked by its own rival.
#
#   * problem_spec_fieldHashKey a result
#       result = (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)
#     A THREE-component tuple, each component independently attackable: drop the
#     identity entirely, drop only the second component, duplicate the first into
#     the second's position, or transpose the two.
#
# UNGROUNDED-ORACLE ECHO: N/A, exactly as the nagini sibling records. All three
# right-hand sides are written out over the inputs' own fields (`fieldLtPure` and
# `keyLt` are ordinary `pure`-region `def`s; `meta.axioms == []` and there is no
# `opaque` declaration in the file at all). There is no answer key an impl could
# echo without doing the work, so the positives are honest structurally-different
# correct impls rather than echo-rejects — the same disposition nagini reached.
#
# ---------------------------------------------------------------------------
# CARRIER RE-EXPRESSION (what the port had to change, and why)
# ---------------------------------------------------------------------------
# Nagini modeled the descriptor as `Attr(rank:int, owned:bool, okey:PSeq[int])`:
# a boolean attachment flag and a FLATTENED integer sequence standing for the
# identity, with the two-component structure erased and lexicographic order
# hand-rolled as a front-recursive `lex_lt` over that sequence. This carrier
# keeps the identity STRUCTURED as `Option (String × String)`, which changes the
# port in three ways:
#
#   * `owned : bool` + `okey : PSeq[int]` collapse into ONE binder,
#     `model : Option (String × String)`. Nagini's separate flag can be
#     internally inconsistent with the key (an ownerless attribute with a
#     non-empty residual `okey`); here `none` carries no components at all, so
#     that inconsistent state does not exist VERBATIM. But the SUB-DOMAIN both
#     nagini cases attack — the unattached half of the identity binder — is fully
#     expressible, and an audit re-derived both rather than dropping them:
#       - `partial-domain-attr_eq-okey-on-ownerless` -> weak-eq-require-attachment.
#         Nagini demanded agreement of a residual key two unattached attributes
#         should not have; the carrier-faithful equivalent demands ATTACHMENT
#         before conceding equality, which lands the same claim (equality of two
#         UNATTACHED descriptors must hold) and is the battery's only over-strict
#         equality rival.
#       - `partial-domain-attr_hash_key-bad-tag` -> weak-hash-fabricate-components.
#         Nagini gave an ownerless attribute the owner-present tag plus a residual
#         key; here the equivalent makes both identity components unconditionally
#         `some`, so an unattached descriptor's key wrongly carries components.
#     Nothing from nagini's partial-domain lane is omitted. What is genuinely not
#     writable is only the INTERNALLY INCONSISTENT STATE itself (a `none` that
#     nonetheless carries components) — an unrepresentable value, not an
#     unattacked clause.
#   * the identity's TWO COMPONENTS are visible, which is attack surface nagini's
#     flattened sequence did not expose. Four rivals with no nagini counterpart
#     are added for it: weak-eq-label-only, weak-hash-drop-name,
#     weak-hash-duplicate-label, weak-hash-swap-components — and
#     weak-lt-name-only-tiebreak, which compares the second component while
#     ignoring the first.
#   * the hash key is the KEY TUPLE (see mapping.md), not nagini's `PSeq[int]`
#     encoding with a 0/1 tag byte. So "the tag byte is wrong" is not a shape a
#     rival can take here; "a component is missing, duplicated, or transposed"
#     is, and that is what the hash rivals do.
#
# ---------------------------------------------------------------------------
# WITNESS MECHANICS ON THIS CARRIER (the part with no nagini counterpart)
# ---------------------------------------------------------------------------
# Nagini's reject cases rest on Viper discharging the postcondition. On a
# tactic-proof backend that inference does not hold: the frozen scripts are
# `rfl` / `split <;> rfl`, tuned to the frozen impls' syntactic form, and
# reshaping an impl breaks them whether the reshape is WRONG or merely different.
# So every reject case below carries a witness that was BUILT BOTH WAYS before
# shipping — it elaborates against the rival and FAILS against the frozen
# solution. Nothing here relies on a tactic merely failing to match.
#
# Two tactic shapes suffice, both at fully CONCRETE inputs — no witness needs to
# condition on the carrier, because nothing in this file is opaque:
#   * `decide` closes the equality and hash-key witnesses, and the ordering
#     witnesses whose disagreement is settled by the counter comparison or by the
#     attachment tie-break. `DecidableEq` is derived on `FieldId` and `Int` /
#     `Option String` literals reduce.
#   * `simp [Id.run, keyLt] <;> decide` is needed wherever the disagreement runs
#     through the lexicographic identity comparison. Measured here: `decide`
#     alone gets STUCK on it — `String`'s order instance does not reduce in the
#     kernel (`reduction got stuck at … match String.ltb "a".iter "b".iter`), so
#     `decide` fails on even `("a" : String) < "b"`. Unfolding `keyLt` for `simp`
#     first reduces the goal to a `List Char` order fact, which `decide` then
#     closes. This is the "unfold the operation for simp instead" pattern; the
#     witnesses were NOT dropped over the stuck `decide`.
# Because every witness states its refutation at literal inputs, no witness head
# binds anything, so there are no hypotheses to be jointly unsatisfiable and the
# gate's consistency probe has nothing to run (`consistency_probe` returns None).
# Confirmed by construction: no `example` below takes a binder.
#
# Binder variation (what the reject witnesses actually probe): the counter binder
# is varied across 0, ±1, ±2, ±3, ±4, 5, 6, 7, 8, 9, 10, 11 and is held EQUAL
# between the two inputs in some witnesses and UNEQUAL in others; the identity
# binder is varied across `none`, and `some` values that agree on both
# components, agree on the first only, agree on the second only, and differ on
# both. No binder sits at one value across the battery, and no two rivals share a
# witness — the four near-misses (weak-eq-label-only, weak-eq-attachment-only,
# weak-lt-name-only-tiebreak, weak-hash-duplicate-label) each get the input that
# separates them from the rivals they are refinements of.
#
# BOTH HALVES OF THE IDENTITY BINDER, and both DIRECTIONS of error. An audit
# measured the shipped lane exhaustively over the carrier and found three clauses
# that every rival happened to agree with the spec on, i.e. asserted coverage
# that no case demonstrated. Each now has a rival whose witness lands on exactly
# that clause:
#   * the hash key's components being ABSENT when unattached — every other hash
#     rival reproduces the specified key on the whole unattached half
#     => weak-hash-fabricate-components (witness at `none`).
#   * equality holding between two UNATTACHED descriptors, and more generally the
#     over-strict direction (spec says equal, rival says unequal) — every other
#     equality rival errs only the other way
#     => weak-eq-require-attachment (witness at the reflexivity corner).
#   * the ordering guard's `isNone ∧ isNone` disjunct, which routes an
#     equal-counter unattached pair to the counter comparison — every other
#     ordering rival reproduces the specified decision there
#     => weak-lt-bare-pair-true (witness at a descriptor vs. an equal one).
# So each of the three obligations is now attacked on the unattached half of the
# `model` binder as well as the attached half, and the equality lane is attacked
# in both error directions rather than one.
#
# ---------------------------------------------------------------------------
# VACUOUS / DROPPED CLASSES (stated, not silently omitted)
# ---------------------------------------------------------------------------
#   * FRAME / PERMISSION-MUTATION — VACUOUS on lean. The nagini sibling makes
#     this class MANDATORY (three cases: every input is held read-only at a
#     fraction, so a rival that writes an input field to fabricate its answer must
#     be rejected for insufficient permission). Lean is referentially
#     transparent: `FieldId` is an immutable value, there is no heap, no
#     aliasing and no fractional permission, so there is no read-only input a
#     rival could overwrite and nothing to reject. All three nagini frame cases
#     are omitted as vacuous, and no substitute is fabricated in their place.
#   * DIVERGENCE / NON-TERMINATION — VACUOUS on lean, and the nagini sibling
#     carries no such case either. All three `implementation_*` are total Lean
#     `def`s, so a diverging implementation cannot be WRITTEN here: the rival does
#     not exist on this carrier. (This is the one backend where the class really
#     is vacuous. Under velvet's `loom.semantics.termination "partial"` it would
#     instead be a live spec hole, since a non-terminating impl satisfies every
#     `ensures` vacuously while its faithful patch hangs the F2P — see
#     the corpus-wide termination-semantics finding. Not applicable to lean.)
#   * CONTROL-FLOW-EFFECT — N/A, as nagini records. All three modeled operations
#     are total pure queries returning a fully-pinned value; there is no raise
#     path, no effect channel, and no capability token invisible to the value
#     abstraction.
#   * AXIOM lane — DROPPED. `AXIOM_TESTS = []`, matching nagini. There is no
#     `opaque`/`axiom` declaration in the frozen file (mapping.md: no unchanged
#     callee needs one), and the axiom lane is G-AX's job, which this gate
#     ignores.

from pathlib import Path

INSTANCE = "django__django-13401"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# Each anchor lies ENTIRELY inside one impl region or one proof TACTIC BODY —
# the only regions a variant may edit. The spec view and every `theorem
# correct_*` STATEMENT are never touched, so same_spec holds by construction.
# ---------------------------------------------------------------------------

_IMPL_EQ = """\
def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
  return (a.creationCounter == b.creationCounter) && (a.model == b.model)"""

_IMPL_LT = """\
def implementation_fieldLt (a b : FieldId) : Bool := Id.run do
  -- Order by creation-order counter first (so descriptors with differing
  -- counters, or both unattached, keep their historical order).
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    -- exactly one is attached: the unattached descriptor comes first
    return a.model.isNone
  else
    -- counters equal and both attached: compare by model identity
    match a.model, b.model with
    | some ka, some kb => return keyLt ka kb
    | _, _ => return false"""

_IMPL_HASH = """\
def implementation_fieldHashKey
    (a : FieldId) : Int × Option String × Option String := Id.run do
  return (a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)"""

_PROOF_EQ = """\
  intro a b
  unfold problem_spec_fieldEq implementation_fieldEq
  rfl"""

_PROOF_LT = """\
  intro a b
  unfold problem_spec_fieldLt implementation_fieldLt fieldLtPure
  simp only [Id.run]
  split <;> rfl"""

for _anchor in (_IMPL_EQ, _IMPL_LT, _IMPL_HASH, _PROOF_EQ, _PROOF_LT):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"drift: anchor not unique: {_anchor[:60]!r}")


def _variant(impl_old, impl_new, proof_old=None, proof_new=None):
    """A complete Solution.lean with ONE impl region replaced, and (only for a
    reshaped soundness positive whose frozen script no longer matches) that
    function's proof TACTIC BODY replaced. Every `theorem correct_*` statement
    stays byte-identical; nothing outside impl/proof is edited."""
    out = _swap(_BASE, impl_old, impl_new)
    if proof_new is not None:
        out = _swap(out, proof_old, proof_new)
    return out


def _eq(body):
    return ("def implementation_fieldEq (a b : FieldId) : Bool := Id.run do\n"
            + body)


def _lt(body):
    return ("def implementation_fieldLt (a b : FieldId) : Bool := Id.run do\n"
            + body)


def _hk(body):
    return ("def implementation_fieldHashKey\n"
            "    (a : FieldId) : Int × Option String × Option String := "
            "Id.run do\n" + body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# Structurally different but behaviourally identical correct impls, one per
# obligation, each shipped with a proof that ACTUALLY CLOSES for the new shape
# (all three were built and confirmed rc=0 before shipping). No new lemma,
# axiom, sorry, admit or native_decide anywhere; every theorem statement
# byte-identical.
# ---------------------------------------------------------------------------

# pos-eq-match-on-identity — ports nagini `positive-attr_eq-direct-ref` /
# `positive-attr_hash_key-typed-locals` in the only form that carries content
# here. Nagini's version returned the `@Pure` reference helper directly; this
# spec has no helper to return (its right-hand side is written inline), so the
# reshape instead drops the imperative wrapper entirely and dispatches on the
# identity conjunct by pattern match, testing the counter only in the branch
# where the identities already agree. Short-circuits in the OPPOSITE order from
# the frozen `&&`, so it also covers nagini's conjunct-reorder intent. The frozen
# `rfl` cannot close this shape; the replacement is a two-way case split on the
# same boolean, no new lemma.
_POS_EQ = """\
def implementation_fieldEq (a b : FieldId) : Bool :=
  match a.model == b.model with
  | false => false
  | true  => a.creationCounter == b.creationCounter"""

_POS_EQ_PROOF = """\
  intro a b
  unfold problem_spec_fieldEq implementation_fieldEq
  cases h : (a.model == b.model) <;> simp [h]"""

# pos-lt-restructured — ports nagini `positive-attr_lt-branch-reorder`. The
# three-arm decision is restructured so the equal-counter case is handled FIRST
# and its three sub-cases are dispatched by a single match on the pair of
# identities, rather than by the frozen "counter-first, then presence, then key"
# ladder. Same function on every input; the frozen `split <;> rfl` no longer
# matches, so the proof destructures both descriptors and splits on the identity
# shapes — still just `cases`/`simp_all`/`omega`, no new lemma.
_POS_LT = """\
def implementation_fieldLt (a b : FieldId) : Bool :=
  if a.creationCounter = b.creationCounter ∧ (a.model.isSome ∨ b.model.isSome) then
    match a.model, b.model with
    | none,    some _  => true
    | some _,  none    => false
    | some ka, some kb => keyLt ka kb
    | none,    none    => false
  else
    decide (a.creationCounter < b.creationCounter)"""

_POS_LT_PROOF = """\
  intro a b
  unfold problem_spec_fieldLt implementation_fieldLt fieldLtPure
  obtain ⟨ca, ma⟩ := a
  obtain ⟨cb, mb⟩ := b
  cases ma <;> cases mb <;>
    by_cases hc : ca = cb <;> simp_all <;> omega"""

# pos-hash-named-components — ports nagini
# `positive-attr_hash_key-typed-locals`: bind each identity component to a local
# before assembling the result tuple. `let`-inlining is definitional, so the
# frozen `rfl` closes unchanged (confirmed). Cheap, and it confirms the
# obligation is pinned to the tuple's VALUE and not to the frozen expression's
# syntactic form.
_POS_HASH = _hk("""\
  let label := a.model.map Prod.fst
  let name := a.model.map Prod.snd
  return (a.creationCounter, label, name)""")


# ---------------------------------------------------------------------------
# ADMISSIBILITY — must VERIFY, else PRECOND-TOO-STRONG / unsatisfiable spec.
# ---------------------------------------------------------------------------

# admiss-reproducer-shape — ports nagini `admissibility-f2p-shaped-trio`. None of
# the three obligations carries a precondition hypothesis (they are `∀ (a b :
# FieldId), problem_spec … ` with no antecedent), so there is no `Requires` to
# establish at a call site and nagini's construction becomes the claim that
# survives it: the three specs are jointly SATISFIABLE, at the concrete
# reproducer-shaped points, in the direction the issue demands. Nagini's in-body
# `Assert(...)` becomes an in-body `have … := by decide`. Seven points are
# pinned: two descriptors sharing one counter but attached to distinct models
# are NOT equal; a descriptor is equal to a same-identity one; two unattached
# descriptors at one counter ARE equal (the backward-compatible reading); those
# two same-counter distinct-identity descriptors ARE strictly ordered, by
# identity; an unattached descriptor precedes an attached one at equal counter;
# a lower counter precedes a higher one even when the identity order would
# disagree (so the historical order is preserved); and the two same-counter
# descriptors' hash keys are the expected tuples AND those tuples DIFFER — the
# de-duplication the issue is about. The impl body is otherwise the frozen one
# and all three frozen proofs are kept verbatim, so the only thing this can fail
# on is a spec-shape regression at those points.
_ADMISS = """\
def implementation_fieldEq (a b : FieldId) : Bool := Id.run do
  -- The three specs are satisfiable, together, at the reproducer-shaped points:
  -- descriptors sharing one creation-order counter but attached to distinct
  -- models, plus an unattached descriptor at that same counter.
  have _hDistinctNotEqual :
      problem_spec_fieldEq
        { creationCounter := 0, model := some ("model_fields", "abstractmodel") }
        { creationCounter := 0,
          model := some ("model_fields", "inheritabstractmodel1") }
        false := by
    unfold problem_spec_fieldEq
    decide
  have _hSameEqual :
      problem_spec_fieldEq
        { creationCounter := 0, model := some ("model_fields", "abstractmodel") }
        { creationCounter := 0, model := some ("model_fields", "abstractmodel") }
        true := by
    unfold problem_spec_fieldEq
    decide
  have _hBareEqual :
      problem_spec_fieldEq
        { creationCounter := 0, model := none }
        { creationCounter := 0, model := none } true := by
    unfold problem_spec_fieldEq
    decide
  have _hDistinctOrdered :
      problem_spec_fieldLt
        { creationCounter := 0, model := some ("model_fields", "abstractmodel") }
        { creationCounter := 0,
          model := some ("model_fields", "inheritabstractmodel1") }
        true := by
    unfold problem_spec_fieldLt fieldLtPure
    simp [keyLt] <;> decide
  have _hBareFirst :
      problem_spec_fieldLt
        { creationCounter := 0, model := none }
        { creationCounter := 0, model := some ("model_fields", "abstractmodel") }
        true := by
    unfold problem_spec_fieldLt fieldLtPure
    decide
  have _hCounterKeepsOrder :
      problem_spec_fieldLt
        { creationCounter := 0, model := some ("model_fields", "zeta") }
        { creationCounter := 1, model := some ("model_fields", "alpha") }
        true := by
    unfold problem_spec_fieldLt fieldLtPure
    decide
  have _hHashApart :
      problem_spec_fieldHashKey
        { creationCounter := 0, model := some ("model_fields", "abstractmodel") }
        (0, some "model_fields", some "abstractmodel")
      ∧ problem_spec_fieldHashKey
        { creationCounter := 0,
          model := some ("model_fields", "inheritabstractmodel1") }
        (0, some "model_fields", some "inheritabstractmodel1")
      ∧ ((0 : Int), some "model_fields", some "abstractmodel")
        ≠ ((0 : Int), some "model_fields", some "inheritabstractmodel1") := by
    unfold problem_spec_fieldHashKey
    refine ⟨by decide, by decide, by decide⟩
  return (a.creationCounter == b.creationCounter) && (a.model == b.model)"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each edits ONLY one
# impl region and keeps every frozen proof script, and each ships a `witness`
# built both ways (elaborates against the rival, fails against gold).
# ---------------------------------------------------------------------------

# --- equality (problem_spec_fieldEq: counter conjunct AND identity conjunct)

# weak-eq-counter-only — ports nagini `partial-domain-attr_eq-rank-only`, the
# central rival: drop the identity conjunct and decide equality on the
# creation-order counter alone. This is the behaviour the change replaces.
_WEAK_EQ_COUNTER_ONLY = _eq(
    "  return (a.creationCounter == b.creationCounter)")

# weak-eq-label-only — NO nagini counterpart (nagini's identity was a single
# flattened sequence, so "compare one component" was not a shape it could take).
# Keeps the identity conjunct but compares only the identity's FIRST component,
# ignoring the second. A tight near-miss: it agrees with the frozen decision on
# every pair whose identities differ in the first component and on every pair
# whose identities agree entirely, and diverges only where two identities share
# their first component and differ in the second — which is exactly the
# reproducer's shape.
_WEAK_EQ_LABEL_ONLY = _eq(
    "  return (a.creationCounter == b.creationCounter) &&\n"
    "    (a.model.map Prod.fst == b.model.map Prod.fst)")

# weak-eq-attachment-only — NO nagini counterpart in this form (nagini's
# attachment flag came WITH a residual key, so flag-agreement alone was not a
# separable rival). Weakens the identity conjunct all the way down to identity
# PRESENCE: two attached descriptors count as sharing an identity whatever their
# identities are. Agrees with the frozen decision whenever the two descriptors
# differ in attachment, and on unattached pairs; diverges on every equal-counter
# pair of distinctly-attached descriptors.
_WEAK_EQ_ATTACHMENT_ONLY = _eq(
    "  return (a.creationCounter == b.creationCounter) &&\n"
    "    (a.model.isSome == b.model.isSome)")

# weak-eq-disjunction — NO nagini counterpart. Both conjuncts are present but
# combined with `||` instead of `&&`. Agrees with the frozen decision on every
# pair that agrees on both observations or on neither; diverges on both mixed
# sub-domains, and in particular makes two descriptors with DIFFERENT counters
# but one identity compare equal.
_WEAK_EQ_DISJUNCTION = _eq(
    "  return (a.creationCounter == b.creationCounter) || (a.model == b.model)")

# weak-eq-identity-only — the mirror of weak-eq-counter-only, attacking the OTHER
# conjunct: drop the creation-order counter and decide equality on the attached
# identity alone. No nagini counterpart (nagini attacked only the newly-added
# conjunct). Included so the counter conjunct is not defended solely by the
# rivals that keep it.
_WEAK_EQ_IDENTITY_ONLY = _eq("  return (a.model == b.model)")

# weak-eq-require-attachment — ports nagini
# `partial-domain-attr_eq-okey-on-ownerless`, which the first cut of this port
# recorded as inexpressible. It is expressible: nagini's rival wrongly demanded
# identity agreement of two UNATTACHED descriptors, and the shape that survives
# the carrier collapse is to demand ATTACHMENT before conceding equality at all.
# Measured need: every other equality rival errs in one direction only (it
# reports equal where the spec says unequal), so the spec's ability to reject an
# OVER-STRICT equality — one that reports unequal where the spec says equal —
# rested on no rival at all. This one closes that: it is the only equality rival
# whose divergence has gold True and rival False.
_WEAK_EQ_REQUIRE_ATTACHMENT = _eq(
    "  return (a.creationCounter == b.creationCounter) && a.model.isSome &&\n"
    "    (a.model == b.model)")

# weak-lt-bare-pair-true — attacks the both-unattached corner of the ordering
# guard's FIRST arm. Measured need: the frozen guard's first disjunct is
# `a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone)`,
# and the second half of that disjunction is what routes an equal-counter pair of
# UNATTACHED descriptors to the counter comparison (yielding false — no strict
# order between two descriptors that are indistinguishable). Checked
# exhaustively: all four other ordering rivals reproduce the specified decision
# on that corner, so the `isNone ∧ isNone` clause was pinned by no rival. This
# rival drops it and lets the match's fallback arm answer, reporting a strict
# order between a descriptor and an equal one — irreflexivity broken.
_WEAK_LT_BARE_PAIR_TRUE = _lt("""\
  if a.creationCounter ≠ b.creationCounter then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    return a.model.isNone
  else
    match a.model, b.model with
    | some ka, some kb => return keyLt ka kb
    | _, _ => return true""")

# --- ordering (problem_spec_fieldLt = fieldLtPure: three decision arms)

# weak-lt-counter-only — ports nagini `partial-domain-attr_lt-rank-only`: drop
# both tie-breaks and order by the creation-order counter alone. Correct on every
# differing-counter pair and on equal-counter unattached pairs; at an equal
# counter with attachments present it reports "not less" in both directions,
# leaving no strict order at all.
_WEAK_LT_COUNTER_ONLY = _lt(
    "  return decide (a.creationCounter < b.creationCounter)")

# weak-lt-flip-presence — ports nagini
# `partial-domain-attr_lt-flip-presence`: keep the counter-first arm and the
# attachment tie-break but INVERT its direction, ordering the attached descriptor
# ahead of the unattached one. Agrees with the frozen decision on differing
# counters and on equal-counter both-attached pairs; diverges on exactly the
# equal-counter attached-vs-unattached boundary the spec fixes the direction of.
_WEAK_LT_FLIP_PRESENCE = _lt("""\
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    return a.model.isSome
  else
    match a.model, b.model with
    | some ka, some kb => return keyLt ka kb
    | _, _ => return false""")

# weak-lt-swap-key-operands — NO nagini counterpart. Gets the first two arms
# exactly right and reverses the OPERANDS of the third: compares the second
# descriptor's identity against the first's. Agrees with the frozen decision
# everywhere except the equal-counter both-attached arm, where it is the exact
# negation on distinct identities (and still agrees on identical ones).
_WEAK_LT_SWAP_KEY_OPERANDS = _lt("""\
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    return a.model.isNone
  else
    match a.model, b.model with
    | some ka, some kb => return keyLt kb ka
    | _, _ => return false""")

# weak-lt-name-only-tiebreak — NO nagini counterpart (nagini's flattened key had
# no separable components). The tightest near-miss in the ordering lane: both
# earlier arms right, and the identity tie-break compares only the identity's
# SECOND component, dropping the primary one. Agrees with the frozen decision on
# every equal-counter both-attached pair whose identities share their first
# component — a large majority of realistic pairs, including the reproducer's own
# trio — and diverges only where the first components differ and the two
# components' orders disagree.
_WEAK_LT_NAME_ONLY_TIEBREAK = _lt("""\
  if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone) then
    return decide (a.creationCounter < b.creationCounter)
  else if a.model.isSome ≠ b.model.isSome then
    return a.model.isNone
  else
    match a.model, b.model with
    | some ka, some kb => return decide (ka.2 < kb.2)
    | _, _ => return false""")

# --- hash key (problem_spec_fieldHashKey: a three-component tuple)

# weak-hash-drop-identity — ports nagini
# `partial-domain-attr_hash_key-drop-owner`: the key carries the creation-order
# counter only, both identity components absent whatever the descriptor is
# attached to. Correct for unattached descriptors; for attached ones the identity
# is lost entirely, so two same-counter descriptors attached to distinct models
# share a key and collapse in a hashed collection.
_WEAK_HASH_DROP_IDENTITY = _hk("  return (a.creationCounter, none, none)")

# weak-hash-drop-name — NO nagini counterpart (there were no separable
# components to drop one of). Carries the counter and the identity's FIRST
# component but leaves the second absent. Agrees with the frozen key on every
# unattached descriptor and, in its first two components, on every attached one;
# it collides exactly the descriptors that share a first identity component and
# differ in the second — the reproducer's shape.
_WEAK_HASH_DROP_NAME = _hk(
    "  return (a.creationCounter, a.model.map Prod.fst, none)")

# weak-hash-duplicate-label — NO nagini counterpart, and the tightest near-miss
# in the hash lane: a three-component key of the right SHAPE (present exactly
# when the descriptor is attached), but the identity's first component is written
# into both slots. Agrees with the frozen key on every unattached descriptor and
# on every attached one whose two identity components coincide, and diverges only
# where they differ — while still, unlike weak-hash-drop-name, distinguishing
# nothing about the second component at all.
_WEAK_HASH_DUPLICATE_LABEL = _hk(
    "  return (a.creationCounter, a.model.map Prod.fst,\n"
    "    a.model.map Prod.fst)")

# weak-hash-swap-components — NO nagini counterpart. TRANSPOSES the two identity
# components. Injective, so it never collides two descriptors the frozen key
# separates — it would pass a test that only asserts keys differ — yet it is not
# the specified key, and the spec pins the key itself rather than merely its
# separating power. Agrees with the frozen key on every unattached descriptor and
# on attached ones whose components coincide.
_WEAK_HASH_SWAP_COMPONENTS = _hk(
    "  return (a.creationCounter, a.model.map Prod.snd,\n"
    "    a.model.map Prod.fst)")

# weak-hash-fabricate-components — ports nagini
# `partial-domain-attr_hash_key-bad-tag` in the form this carrier admits, and the
# first cut of this port recorded it as inexpressible. It is not: nagini's rival
# gave an ownerless attribute the owner-PRESENT tag plus a residual key, and the
# structured equivalent is to make BOTH identity components unconditionally
# `some`, filling them for an unattached descriptor with a fabricated value.
# Measured need: the specified key's second and third components are absent
# exactly when the descriptor is unattached, and all four other hash rivals
# reproduce the specified key on every UNATTACHED descriptor — so that half of
# the `model` binder was pinned by no rival at all, and "the key is absent when
# unattached" was an untested clause. This rival is correct on every ATTACHED
# descriptor and wrong on every unattached one, the exact complement of the
# shipped four, so its witness sits on the unattached half.
_WEAK_HASH_FABRICATE_COMPONENTS = _hk(
    "  return (a.creationCounter, some ((a.model.map Prod.fst).getD \"\"),\n"
    "    some ((a.model.map Prod.snd).getD \"\"))")


# ---------------------------------------------------------------------------
# Witness builders. Every witness states the frozen spec predicate at a FULLY
# CONCRETE input and denies it of the rival's own result — so it elaborates only
# if the rival really contradicts the spec there, and it cannot hold of gold.
# No witness head binds anything: there are no hypotheses, hence nothing for the
# gate's consistency probe to find. `_w_lt_key` carries the extra `simp [Id.run,
# keyLt]` step the lexicographic arm needs because `String`'s order does not
# reduce under `decide` (see the header).
# ---------------------------------------------------------------------------

def _fid(counter, model):
    return "{ creationCounter := %s, model := %s }" % (counter, model)


def _some(label, name):
    return f'some ("{label}", "{name}")'


def _w_eq(a, b):
    return (f"example : ¬ problem_spec_fieldEq {a} {b}\n"
            f"    (implementation_fieldEq {a} {b}) := by\n"
            f"  unfold problem_spec_fieldEq implementation_fieldEq\n"
            f"  decide")


def _w_lt(a, b, tactic="decide"):
    return (f"example : ¬ problem_spec_fieldLt {a} {b}\n"
            f"    (implementation_fieldLt {a} {b}) := by\n"
            f"  unfold problem_spec_fieldLt implementation_fieldLt fieldLtPure\n"
            f"  {tactic}")


def _w_lt_key(a, b):
    return _w_lt(a, b, "simp [Id.run, keyLt] <;> decide")


def _w_hk(a):
    return (f"example : ¬ problem_spec_fieldHashKey {a}\n"
            f"    (implementation_fieldHashKey {a}) := by\n"
            f"  unfold problem_spec_fieldHashKey implementation_fieldHashKey\n"
            f"  decide")


SPEC_TESTS = [
    # ------------------------------------------------------------- POSITIVES
    {
        "id": "pos-eq-match-on-identity",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_IMPL_EQ, _POS_EQ, _PROOF_EQ, _POS_EQ_PROOF),
        "rationale": (
            "Ports nagini positive-attr_eq-direct-ref. This spec's right-hand "
            "side is written inline rather than delegated to a helper, so "
            "'return the reference helper' has no counterpart; the reshape that "
            "carries the same content is to drop the imperative wrapper and "
            "dispatch on the identity observation by pattern match, testing the "
            "counter only inside the branch where the identities already agree. "
            "That short-circuits in the OPPOSITE order from the frozen "
            "conjunction, so it also covers nagini's conjunct-reorder intent. "
            "The same boolean function on every input, so the equality "
            "postcondition must still hold; the frozen `rfl` cannot close the "
            "new shape, and the replacement is a two-way `cases` on the same "
            "boolean plus `simp` — no lemma, no axiom, statement "
            "byte-identical. If it fails => SPEC-TOO-STRONG (the obligation "
            "would be pinned to the frozen syntactic form rather than to the "
            "function)."
        ),
    },
    {
        "id": "pos-lt-restructured",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_IMPL_LT, _POS_LT, _PROOF_LT, _POS_LT_PROOF),
        "rationale": (
            "Ports nagini positive-attr_lt-branch-reorder. The three-arm "
            "ordering decision is restructured so the equal-counter case is "
            "handled FIRST and its sub-cases are dispatched by a single match "
            "on the pair of identities, instead of the frozen counter-first / "
            "presence / identity ladder. Decides identically to the ordering "
            "reference on every input — including the both-unattached corner, "
            "which the restructured guard routes to the counter comparison — so "
            "the ordering postcondition must still hold. The frozen `split <;> "
            "rfl` no longer matches; the replacement destructures both "
            "descriptors and case-splits on the identity shapes with "
            "`simp_all`/`omega`. No lemma, no axiom, statement byte-identical. "
            "If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-hash-named-components",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_IMPL_HASH, _POS_HASH),
        "rationale": (
            "Ports nagini positive-attr_hash_key-typed-locals: bind each "
            "identity component to a named local before assembling the result "
            "tuple. `let`-inlining is definitional, so the frozen `rfl` closes "
            "unchanged. Confirms the hash-key obligation is pinned to the "
            "tuple's VALUE and not to the frozen expression's syntactic form. "
            "If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-reproducer-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_IMPL_EQ, _ADMISS),
        "rationale": (
            "Ports nagini admissibility-f2p-shaped-trio. None of the three "
            "obligations carries a precondition hypothesis, so there is no "
            "Requires to establish at a call site; what survives of the nagini "
            "control is the claim that all three specs are jointly SATISFIABLE "
            "at the reproducer-shaped points, in the direction the issue "
            "demands. Nagini's in-body Assert(...) becomes an in-body `have … "
            ":= by decide` over seven points: two same-counter descriptors "
            "attached to distinct models are NOT equal, a descriptor is equal "
            "to a same-identity one, two unattached descriptors at one counter "
            "ARE equal, those distinct-identity descriptors ARE strictly "
            "ordered by identity, an unattached descriptor precedes an attached "
            "one at equal counter, a lower counter precedes a higher one even "
            "when the identity order would disagree, and the two "
            "same-counter descriptors' keys are the expected tuples AND those "
            "tuples DIFFER. The impl is otherwise frozen and all three frozen "
            "proofs are kept verbatim, so the only failure mode is a spec-shape "
            "regression at those points => PRECOND-TOO-STRONG / unsatisfiable "
            "spec."
        ),
    },

    # --------------------------------------------------------------- RIVALS
    {
        "id": "weak-eq-counter-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_EQ, _WEAK_EQ_COUNTER_ONLY),
        "witness": _w_eq(_fid(0, _some("model_fields", "abstractmodel")),
                         _fid(0, _some("model_fields",
                                       "inheritabstractmodel1"))),
        "rationale": (
            "Attacks the identity conjunct of problem_spec_fieldEq, over the "
            "`model` binder of both inputs: the spec requires "
            "`a.model == b.model` as well as counter agreement, and this impl "
            "returns counter agreement alone. The witness sits at two "
            "descriptors sharing counter 0 and attached to two distinct models, "
            "where the spec's right-hand side is false and the rival returns "
            "true; `decide` closes it because `FieldId` derives DecidableEq and "
            "the literals reduce. Built both ways: elaborates against the "
            "rival, fails against the frozen solution."
        ),
        "refinement": (
            "This is precisely the behaviour the issue reports and the change "
            "replaces: descriptors that share a creation-order counter but "
            "belong to different owners compare equal, so one of them is "
            "silently discarded from a de-duplicating collection. The faithful "
            "real patch is therefore the unpatched comparison, and the single "
            "F2P test asserts directly that three descriptors sharing one "
            "counter across three distinct owners are pairwise NOT equal. "
            "Under this rival all three of those assertions fail, so a "
            "verifying rival here would be a genuine "
            "verify-does-not-imply-resolve break rather than an artifact."
        ),
    },
    {
        "id": "weak-eq-label-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_EQ, _WEAK_EQ_LABEL_ONLY),
        "witness": _w_eq(_fid(3, _some("app_a", "alpha")),
                         _fid(3, _some("app_a", "beta"))),
        "rationale": (
            "Attacks the identity conjunct at COMPONENT granularity — surface "
            "the nagini carrier did not expose, since its identity was a single "
            "flattened sequence. The spec compares the whole identity; this "
            "impl compares only its first component. Refuted at a DIFFERENT "
            "input from weak-eq-counter-only, as the near-miss requires: the "
            "counter binder is at 3, not 0, and the two identities AGREE on "
            "their first component and differ only in the second, which is the "
            "sole sub-domain where this rival and the counter-only rival part "
            "company. Built both ways."
        ),
        "refinement": (
            "A patch that compared only the first half of the owner's identity "
            "would still equate descriptors owned by two different owners that "
            "happen to share that half — which is exactly the F2P's "
            "configuration, since all three owners there are declared in one "
            "place and differ only in the second half of their identity. All "
            "three not-equal assertions in the F2P would still fail, so this "
            "rival does not resolve either."
        ),
    },
    {
        "id": "weak-eq-attachment-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_EQ, _WEAK_EQ_ATTACHMENT_ONLY),
        "witness": _w_eq(_fid(-2, _some("app_a", "alpha")),
                         _fid(-2, _some("app_b", "alpha"))),
        "rationale": (
            "Weakens the identity conjunct to identity PRESENCE: any two "
            "attached descriptors count as sharing an identity. Refuted at a "
            "NEGATIVE counter (-2, a value no other witness uses) on a pair "
            "whose identities differ in their FIRST component and agree in the "
            "second — the mirror of weak-eq-label-only's input, so the two "
            "near-misses are separated in both directions and neither's claimed "
            "sub-domain is asserted without a demonstration. Built both ways."
        ),
        "refinement": (
            "A patch that only checked whether both descriptors are attached at "
            "all — rather than to WHOM — leaves every attached descriptor equal "
            "to every other attached descriptor at the same counter. The F2P's "
            "three descriptors are all attached, so all three not-equal "
            "assertions still fail. Note the divergence is one-sided and is "
            "confined to the equal-counter both-attached sub-domain: on every "
            "pair whose descriptors DIFFER in attachment this rival agrees "
            "with the specified decision (both report not-equal), so it does "
            "not additionally disturb the attached-vs-unattached boundary — "
            "the witness therefore has to sit on the both-attached half, and "
            "does."
        ),
    },
    {
        "id": "weak-eq-disjunction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_EQ, _WEAK_EQ_DISJUNCTION),
        "witness": _w_eq(_fid(1, _some("app_a", "alpha")),
                         _fid(7, _some("app_a", "alpha"))),
        "rationale": (
            "Both of the spec's conjuncts are present but combined "
            "disjunctively, so agreement on EITHER observation is enough. The "
            "witness varies the counter binder in the direction no other "
            "equality witness does — the two counters DIFFER (1 vs 7) while the "
            "identities are identical — so the spec's right-hand side is false "
            "and the rival returns true. This is the sub-domain that separates "
            "it from every conjunctive rival above. Built both ways."
        ),
        "refinement": (
            "Combining the two observations disjunctively makes descriptors "
            "created at different times equal whenever they share an owner, "
            "which collapses distinct descriptors of the SAME owner in a "
            "de-duplicating collection and violates the ordering/equality "
            "consistency the P2P creation-order test relies on. It does not "
            "resolve: the F2P's three descriptors all share one counter, so the "
            "first disjunct alone is satisfied and all three not-equal "
            "assertions fail exactly as before the change."
        ),
    },
    {
        "id": "weak-eq-identity-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_EQ, _WEAK_EQ_IDENTITY_ONLY),
        "witness": _w_eq(_fid(4, "none"), _fid(9, "none")),
        "rationale": (
            "The mirror of weak-eq-counter-only, attacking the OTHER conjunct: "
            "the counter is dropped and equality is decided on the attached "
            "identity alone. Included so the counter conjunct is not defended "
            "only by rivals that happen to keep it. The witness probes the "
            "`model` binder at the value no other equality witness uses — BOTH "
            "inputs unattached — with differing counters (4 vs 9), where the "
            "spec is false and the rival is true. Built both ways."
        ),
        "refinement": (
            "Dropping the creation-order counter from equality equates every "
            "pair of unattached descriptors and every pair of descriptors "
            "sharing one owner, regardless of when they were created. The "
            "creation-order counter is the pre-existing half of the identity "
            "the change was careful to preserve for backward compatibility, so "
            "a patch that removed it breaks the P2P test asserting descriptors "
            "are ordered and distinguished by their creation, while adding "
            "nothing the F2P needs."
        ),
    },
    {
        "id": "weak-eq-require-attachment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_EQ, _WEAK_EQ_REQUIRE_ATTACHMENT),
        "witness": _w_eq(_fid(11, "none"), _fid(11, "none")),
        "rationale": (
            "Ports nagini partial-domain-attr_eq-okey-on-ownerless, which "
            "attacked the sub-domain where equality is asserted BETWEEN "
            "UNATTACHED descriptors. Nagini's shape (demand agreement of a "
            "residual identity key that an unattached descriptor should not "
            "have) does not survive the carrier collapse, because `none` "
            "carries no components; the shape that does is to demand "
            "ATTACHMENT before conceding equality. This is the only equality "
            "rival that errs in the OVER-STRICT direction — checked "
            "exhaustively over the equality lane, every other rival reports "
            "equal where the spec says unequal and never the reverse, so the "
            "spec's power to reject an equality that is too DISCRIMINATING "
            "rested on no rival before this one. The witness sits at a "
            "descriptor compared with an identical unattached descriptor at "
            "counter 11 (used by no other witness), where the spec's "
            "right-hand side is true and the rival returns false — the "
            "reflexivity corner. Built both ways: elaborates against the "
            "rival (rc=0), fails against the frozen solution (rc=1) by "
            "`decide` evaluating the claim and proving it false."
        ),
        "refinement": (
            "Requiring a descriptor to be attached before it can equal "
            "anything makes an unattached descriptor unequal to ITSELF, which "
            "breaks the reflexivity every hashed and de-duplicating collection "
            "assumes: a descriptor not yet attached to anything would fail to "
            "be found in a collection it was just put into. The change was "
            "written to leave the unattached reading alone, and a patch that "
            "conditioned equality on attachment would disturb the "
            "creation-order behaviour the ordering P2P preserves, while adding "
            "nothing for the F2P, whose three descriptors are all attached."
        ),
    },
    {
        "id": "weak-lt-counter-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_LT, _WEAK_LT_COUNTER_ONLY),
        "witness": _w_lt_key(
            _fid(0, _some("model_fields", "abstractmodel")),
            _fid(0, _some("model_fields", "inheritabstractmodel1"))),
        "rationale": (
            "Attacks the ordering reference's THIRD arm (and, collaterally, its "
            "second) by deleting both tie-breaks: the result is the counter "
            "comparison alone. The witness sits at equal counters with both "
            "descriptors attached to distinct owners, where the reference takes "
            "the lexicographic arm and yields true while the rival yields "
            "false. Refuted through the identity comparison, so the witness "
            "needs `simp [Id.run, keyLt]` before `decide` — `String`'s order "
            "instance does not reduce in the kernel. Built both ways."
        ),
        "refinement": (
            "This is the unpatched ordering: at an equal creation-order counter "
            "it reports 'not less' in both directions, so same-counter "
            "descriptors have no strict order at all. The F2P asserts each of "
            "its three same-counter descriptors is strictly less than the next; "
            "under a counter-only comparison every one of those assertions "
            "fails, so the faithful patch does not resolve."
        ),
    },
    {
        "id": "weak-lt-flip-presence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_LT, _WEAK_LT_FLIP_PRESENCE),
        "witness": _w_lt(_fid(5, "none"),
                         _fid(5, _some("app_a", "alpha"))),
        "rationale": (
            "Attacks the ordering reference's SECOND arm alone, inverting the "
            "attachment tie-break's direction while leaving the other two arms "
            "correct. The witness moves the `model` binder to the mixed "
            "configuration no other ordering witness uses — the first input "
            "unattached, the second attached — at counter 5, where the "
            "reference yields true and the rival yields false. This arm needs "
            "no identity comparison, so plain `decide` closes it. Built both "
            "ways."
        ),
        "refinement": (
            "The spec fixes the direction of this boundary deliberately: an "
            "unattached descriptor precedes an attached one at an equal "
            "counter, which is what keeps the historical relative order of "
            "descriptors that are not yet attached to anything. A patch that "
            "ordered attached descriptors ahead of unattached ones inverts "
            "exactly the case the change was written not to disturb, so the "
            "P2P test asserting descriptors are ordered by their creation would "
            "see a reordering it does not expect — while the F2P's three "
            "descriptors are all attached, so it gains nothing there either."
        ),
    },
    {
        "id": "weak-lt-swap-key-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_LT, _WEAK_LT_SWAP_KEY_OPERANDS),
        "witness": _w_lt_key(_fid(2, _some("app_a", "zeta")),
                             _fid(2, _some("app_b", "alpha"))),
        "rationale": (
            "Attacks the ordering reference's THIRD arm while keeping the first "
            "two exactly right: the identity comparison is applied to its "
            "operands in the reverse order, so on distinct identities it is the "
            "exact negation of the reference. Refuted at counter 2 on a pair "
            "whose identities differ in their FIRST component and whose two "
            "components' orders DISAGREE (first ascending, second descending) — "
            "an input distinct from weak-lt-counter-only's and chosen so that "
            "it also cannot be confused with the name-only rival's failure. "
            "Built both ways."
        ),
        "refinement": (
            "Comparing the identities the wrong way round makes the ordering "
            "antisymmetric in the wrong direction on every same-counter "
            "attached pair: the descriptors sort in reverse. The F2P asserts a "
            "specific direction for each of its three same-counter pairs — the "
            "one whose owner's identity sorts earlier must come first — so "
            "under this rival every one of those assertions fails, in the "
            "opposite direction from the unpatched code rather than for lack of "
            "an order."
        ),
    },
    {
        "id": "weak-lt-name-only-tiebreak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_LT, _WEAK_LT_NAME_ONLY_TIEBREAK),
        "witness": _w_lt_key(_fid(-1, _some("app_b", "alpha")),
                             _fid(-1, _some("app_a", "zeta"))),
        "rationale": (
            "The tightest near-miss in the ordering lane, and surface the "
            "nagini carrier could not express (its identity was flattened, so "
            "'compare only the second component' was not a shape). Both earlier "
            "arms are right and the identity tie-break drops the PRIMARY "
            "component, comparing only the secondary one. It therefore agrees "
            "with the reference on every pair sharing a first component — "
            "including the F2P's own trio — so it must be refuted at the input "
            "that distinguishes it: counter -1 (used by no other witness), "
            "first components differing, and the two components' orders "
            "disagreeing, so the reference is false where the rival is true. "
            "Built both ways."
        ),
        "refinement": (
            "The spec orders attached descriptors lexicographically, primary "
            "component first. A patch that consulted only the secondary "
            "component would order two descriptors owned by different primary "
            "groupings by the wrong key, producing an order inconsistent with "
            "the equality the same change installs — the pair would compare "
            "unequal yet sort in an order the specified comparison contradicts, "
            "which breaks the total-ordering contract the comparison is "
            "declared under and so the sorting the P2P creation-order test "
            "exercises. It happens to satisfy the F2P, whose three owners share "
            "a primary component — which is exactly why the spec, and not the "
            "test, has to be the thing that rejects it."
        ),
    },
    {
        "id": "weak-lt-bare-pair-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_LT, _WEAK_LT_BARE_PAIR_TRUE),
        "witness": _w_lt(_fid(-4, "none"), _fid(-4, "none")),
        "rationale": (
            "Attacks the SECOND DISJUNCT of the ordering reference's first "
            "guard — `a.model.isNone ∧ b.model.isNone` — which is what routes "
            "an equal-counter pair of UNATTACHED descriptors to the counter "
            "comparison rather than to the identity arm. Checked exhaustively: "
            "all four other ordering rivals reproduce the specified decision on "
            "that corner, so that clause was pinned by no rival and the "
            "battery's ordering coverage stopped at the attached half. This "
            "rival deletes the disjunct and lets the match's fallback answer "
            "`true`. The witness compares a descriptor with an identical "
            "unattached one at counter -4 (used by no other witness), where the "
            "reference yields false and the rival yields true; the disagreement "
            "never reaches the identity comparison, so plain `decide` closes "
            "it. Built both ways: rc=0 against the rival, rc=1 against the "
            "frozen solution by `decide` refuting the concrete claim."
        ),
        "refinement": (
            "Reporting a strict order between a descriptor and an equal one "
            "makes the comparison non-irreflexive, which is the one property "
            "every sorting routine may assume without checking: a comparator "
            "that says a value precedes itself can make a sort loop or produce "
            "an arbitrary permutation. It affects precisely the descriptors not "
            "yet attached to anything — the population the change was written "
            "not to disturb — so the P2P test asserting descriptors are ordered "
            "by their creation is what it breaks, while the F2P's three "
            "descriptors are all attached and would not notice."
        ),
    },
    {
        "id": "weak-hash-drop-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_HASH, _WEAK_HASH_DROP_IDENTITY),
        "witness": _w_hk(_fid(0, _some("model_fields", "abstractmodel"))),
        "rationale": (
            "Attacks the second and third components of "
            "problem_spec_fieldHashKey: the key carries the counter only, both "
            "identity components absent whatever the descriptor is attached to. "
            "The witness sits at an ATTACHED descriptor at counter 0, where the "
            "spec's tuple has both components present and the rival's has "
            "neither; `decide` closes it on `Option String` literals. Correct "
            "on the whole unattached half of the `model` binder, which is why "
            "the witness has to be on the attached half. Built both ways."
        ),
        "refinement": (
            "This is the unpatched hash: the key ignores the owner entirely, so "
            "two same-counter descriptors with different owners produce one key "
            "and collapse into a single entry of a hashed collection — the "
            "de-duplication the issue reports. The F2P asserts the three "
            "same-counter descriptors' hash values are pairwise different; "
            "under a counter-only key all three of those assertions fail, so "
            "the faithful patch does not resolve."
        ),
    },
    {
        "id": "weak-hash-drop-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_HASH, _WEAK_HASH_DROP_NAME),
        "witness": _w_hk(_fid(6, _some("app_a", "alpha"))),
        "rationale": (
            "Attacks the THIRD component alone — component-level surface the "
            "nagini carrier did not have. The key carries the counter and the "
            "identity's first component and leaves the second absent. Refuted "
            "at counter 6 (used by no other witness) on an attached descriptor "
            "whose second component is present in the spec's tuple and absent "
            "in the rival's, so it is separated from weak-hash-drop-identity, "
            "which also gets the second component wrong but the FIRST one too. "
            "Built both ways."
        ),
        "refinement": (
            "A key that carries only the first half of the owner's identity "
            "still collides every pair of owners sharing that half. In the F2P "
            "all three owners are declared in one place and so share it "
            "exactly, meaning all three hash values remain equal and all three "
            "assertions fail — the same non-resolution as the unpatched hash, "
            "reached by a patch that looks like it added the owner."
        ),
    },
    {
        "id": "weak-hash-duplicate-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_HASH, _WEAK_HASH_DUPLICATE_LABEL),
        "witness": _w_hk(_fid(-3, _some("app_a", "alpha"))),
        "rationale": (
            "The tightest near-miss in the hash lane: a three-component key of "
            "the right SHAPE — present exactly when the descriptor is attached, "
            "unlike weak-hash-drop-name, whose third component is always "
            "absent — but the identity's first component is written into both "
            "slots. It therefore agrees with the spec's tuple on every "
            "unattached descriptor AND on every attached one whose two identity "
            "components coincide, so it is refuted at a NEGATIVE counter (-3, "
            "unused elsewhere) on an attached descriptor whose two components "
            "DIFFER. Built both ways."
        ),
        "refinement": (
            "Duplicating the first identity component into the second slot "
            "means the key never observes the second component at all, so the "
            "distinguishing power is exactly that of weak-hash-drop-name while "
            "the key's shape looks correct. The F2P's three owners share their "
            "first component and differ only in the second, so all three keys "
            "coincide and all three hash assertions fail; and because the key "
            "shape is plausible, nothing short of the spec catches it."
        ),
    },
    {
        "id": "weak-hash-swap-components",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_HASH, _WEAK_HASH_SWAP_COMPONENTS),
        "witness": _w_hk(_fid(8, _some("aaa", "zzz"))),
        "rationale": (
            "Transposes the two identity components. Notable because it is "
            "INJECTIVE: it never collides two descriptors the spec's key "
            "separates, so it would satisfy any test that merely asserts keys "
            "differ — yet the spec pins the key itself, component by component, "
            "not merely its separating power, and this is what makes that "
            "strength a measured claim. Refuted at counter 8 on an attached "
            "descriptor whose two components differ (they must, or the "
            "transposition is invisible); the two components are chosen "
            "far apart so the disagreement is unmistakable. Built both ways."
        ),
        "refinement": (
            "A patch that assembled the owner's identity components in the "
            "wrong order produces a key that is not the specified one, and the "
            "key is an observable of the modeled behaviour: the specified key "
            "is the pair of the owner's components in a fixed order, and any "
            "consumer that reads the key positionally — or compares it against "
            "an independently-constructed key for the same owner, as equality "
            "of hashed entries requires — sees the wrong value. It happens to "
            "keep the F2P's three hash values pairwise distinct, which is "
            "precisely why the spec rather than the test has to reject it: "
            "shipping it would leave the key transposed for every consumer "
            "while the one test that looks at hashing still passes."
        ),
    },
    {
        "id": "weak-hash-fabricate-components",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_IMPL_HASH, _WEAK_HASH_FABRICATE_COMPONENTS),
        "witness": _w_hk(_fid(10, "none")),
        "rationale": (
            "Ports nagini partial-domain-attr_hash_key-bad-tag, whose target "
            "was the key of an UNATTACHED descriptor. Nagini's shape (the "
            "owner-present tag byte plus a residual key) has no counterpart "
            "because this carrier has no tag byte; the equivalent that does "
            "exist is to make both identity components unconditionally `some`, "
            "fabricating a filler value where the descriptor is unattached. "
            "Measured need: the spec pins the second and third components to be "
            "ABSENT exactly when the descriptor is unattached, and all four "
            "other hash rivals reproduce the specified key on every unattached "
            "descriptor — checked exhaustively — so the whole unattached half "
            "of the `model` binder was pinned by no rival and 'the components "
            "are absent when unattached' was an asserted but undemonstrated "
            "clause. This rival is the exact complement: correct on every "
            "attached descriptor, wrong on every unattached one. The witness "
            "sits at an unattached descriptor at counter 10 (used by no other "
            "witness), where the spec's tuple has both components absent and "
            "the rival's has both present. Built both ways: rc=0 against the "
            "rival, rc=1 against the frozen solution by `decide` refuting it."
        ),
        "refinement": (
            "A key that reports both identity components as present for a "
            "descriptor attached to nothing gives that descriptor a key "
            "indistinguishable in shape from an attached one's, so a hashed "
            "collection mixes the two populations and an unattached descriptor "
            "can collide with an attached one whose components happen to be the "
            "filler value. It is also the direction the change was careful NOT "
            "to move in: the specified key for an unattached descriptor is the "
            "counter with both components absent, which is what preserves the "
            "pre-existing hashing of descriptors that are not attached to "
            "anything. The F2P's three descriptors are all attached, so it "
            "passes there and only the spec rejects it."
        ),
    },
]

# No axiom lane: `meta.axioms == []`, there is no `opaque`/`axiom` declaration in
# the frozen file, and every operation is a total read/comparison over the
# descriptor's own data. Matches the nagini sibling's AXIOM_TESTS = [].
AXIOM_TESTS = []
