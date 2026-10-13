# properties.py — G-PBT falsification battery for django__django-15380 (lean).
#
# PORT of the nagini sibling's spec-lane battery to the Lean carrier. NOT a Lean
# module: a manifest the runner parses. Each SPEC_TESTS case is a full
# Solution.lean variant that SHARES the frozen spec (region surgery: only the
# impl region — and, for the soundness positives, the proof body — is edited, so
# markers.same_spec holds by construction) and swaps only the implementation
# (and its proof). Reject cases carry a `witness`: a Lean snippet proving the
# rival contradicts the spec at one concrete input, checked in a file whose
# frozen obligation has been removed (so no tactic script can mask the verdict).
#
# Defended surface (from Solution.lean + mapping.md + instance.json):
#   implementation_resolveFieldModels renameMap priorStates currentStates entries
#   returns, entry-for-entry and in order, a pair of located owning-model states
#   per candidate field key. The single load-bearing postcondition clause is
#     result = entries.map (resolveOne renameMap priorStates currentStates)
#   where, per entry, resolveOne
#     * translates the current name back through renameMap (falling back to the
#       current name) to obtain the PRIOR name,
#     * indexes the PRIOR snapshot by that prior name  -> slot 0,
#     * indexes the CURRENT snapshot by the CURRENT name -> slot 1.
#   The discriminating point (the gold one-line key change) is that the CURRENT
#   snapshot is indexed by the CURRENT name, never by the prior name: on a model
#   renamed in the same step (prior name != current name) the prior-name index
#   locates nothing. The carrier is fully transparent — `List.lookup` is total —
#   so every rival is refutable at concrete literal inputs with `decide`.
#
#   The clause quantifies over the whole list, so it pins the per-entry VALUE,
#   the ORDER, and the LENGTH. A rival attacking only the per-entry value is
#   refutable at a single-entry input; the order and length halves are
#   unobservable there and need a two-entry witness (`reject-reversed-order`,
#   `reject-first-entry-only`).
from pathlib import Path

INSTANCE = "django__django-15380"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _between(src, start, end):
    a = src.index(start) + len(start)
    b = src.index(end, a)
    return src[a:b]


# --- Frozen region text, sliced from the file (no transcription risk) ---------
# The impl region content (def head + Id.run loop). Unique in the file.
_GOLD_IMPL = _between(_BASE, "-- impl-start\n", "\n-- impl-end")
# The per-entry loop body, from the prior-name translation to `return acc`.
# Entirely inside the impl region; unique in the file. Used by the reorder
# positive, which RELOCATES the `let priorName` binding, so it must own it.
_GOLD_LOOP_BODY = _GOLD_IMPL[_GOLD_IMPL.index("    let priorName"):]
# The loop tail from the two snapshot lookups onward (the `let priorName`
# translation is LEFT IN PLACE). Used by the reject rivals, which reshape only
# the lookups / the returned pair and keep `priorName` where it is. Unique.
_GOLD_LOOP_TAIL = _GOLD_IMPL[_GOLD_IMPL.index("    let priorState"):]
# The proof body (tactic block between `:= by\n` and the region terminator).
_GOLD_PROOF = _between(_BASE, ":= by\n", "\n-- proof-end")
# The frozen proof's `intro` line (inside the proof region, unique in the file).
# The admissibility positive PREPENDS a ground `have` to it, so the theorem
# STATEMENT and the spec view are both untouched.
_GOLD_INTRO = "  intro renameMap priorStates currentStates entries"


# ---------------------------------------------------------------------------
# POSITIVES (soundness). Two structurally-different CORRECT impls, each with a
# proof that actually closes for its new shape (the obligation statement is
# byte-identical — only the tactic body changes).

# P1: a purely FUNCTIONAL impl — the per-entry resolution written as a single
# `entries.map` over an inline closure (no `Id.run`, no accumulator, no `for`).
# Value reasoning is unchanged, so it must verify; if it cannot, SPEC-TOO-STRONG.
_POS_MAP_IMPL = (
    "def implementation_resolveFieldModels\n"
    "    (renameMap : List (ModelKey × String))\n"
    "    (priorStates currentStates : List (ModelKey × ModelState))\n"
    "    (entries : List (String × String × String)) :\n"
    "    List (Option ModelState × Option ModelState) :=\n"
    "  entries.map (fun entry =>\n"
    "    let appLabel  := entry.1\n"
    "    let modelName := entry.2.1\n"
    "    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName\n"
    "    (priorStates.lookup (appLabel, priorName), currentStates.lookup (appLabel, modelName)))"
)
_POS_MAP_PROOF = (
    "  intro renameMap priorStates currentStates entries\n"
    "  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels resolveOne\n"
    "  rfl"
)

# P2: keep the imperative `Id.run`/`for` skeleton but compute the CURRENT-snapshot
# lookup BEFORE the prior-name translation and prior lookup (independent reads,
# reordered). The result tuple is unchanged, so the gold proof body still
# discharges verbatim — impl-only edit. Must verify.
_POS_REORDER_BODY = (
    "    let currentState := currentStates.lookup (appLabel, modelName)\n"
    "    let priorName := (renameMap.lookup (appLabel, modelName)).getD modelName\n"
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)


# ---------------------------------------------------------------------------
# REJECT RIVALS (uniqueness). Each reshapes ONLY the loop body; the frozen proof
# body is retained (it no longer closes against the reshaped impl, so the
# verifier rejects). The `witness` is what attributes the rejection to the spec.

# R1: THE bug. Index the CURRENT snapshot by the PRIOR name instead of the
# current name. Correct on the unchanged-name subdomain (prior name == current
# name); wrong the moment a model was renamed this step.
_R1_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    let currentState := currentStates.lookup (appLabel, priorName)\n"
    "    acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)

# R2: index the PRIOR snapshot by the CURRENT name (skip the rename-map
# translation). Coincides with gold only when no rename occurred; on a renamed
# model the prior snapshot has no entry under the current name.
_R2_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, modelName)\n"
    "    let currentState := currentStates.lookup (appLabel, modelName)\n"
    "    acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)

# R3: return the two located states TRANSPOSED (current in slot 0, prior in slot
# 1). Both lookups are legal, but the ordered pair is wrong whenever the two
# states differ.
_R3_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    let currentState := currentStates.lookup (appLabel, modelName)\n"
    "    acc := acc ++ [(currentState, priorState)]\n"
    "  return acc"
)

# R4: fetch the CURRENT-snapshot slot from the PRIOR snapshot (right key, wrong
# snapshot). Returns a stale/absent state for slot 1.
_R4_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    let currentState := priorStates.lookup (appLabel, modelName)\n"
    "    acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)

# R5: resolve every entry CORRECTLY but emit the results in reverse order
# (accumulate by prepending, never re-reversed). Added by audit: the spec clause
# is `result = entries.map …`, which pins ORDER as well as content, and every
# other rival here reshapes only the per-entry value — each is refuted at a
# SINGLE-entry input, where order is unobservable. So the "and in order" half of
# the clause was carried entirely by prose. Refuted at a two-entry input.
_R5_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    let currentState := currentStates.lookup (appLabel, modelName)\n"
    "    acc := (priorState, currentState) :: acc\n"
    "  return acc"
)

# R6: resolve the FIRST entry correctly and drop every later one (the append is
# guarded on the accumulator still being empty). Added by audit: attacks the
# LENGTH/entry-for-entry half of the same clause, which single-entry witnesses
# also leave unobservable — on a one-entry input this rival equals gold exactly.
# Refuted at a two-entry input.
_R6_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    let currentState := currentStates.lookup (appLabel, modelName)\n"
    "    if acc.isEmpty then\n"
    "      acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)

# R7: instead of indexing the current snapshot by the current name, SHADOW the
# snapshot — copy the located current state in under the model's PRIOR name and
# then read slot 1 back by the prior name. On a referentially transparent carrier
# the "write" can only build a local shadow list, so this is an ordinary value
# rival rather than a frame violation (see the omission note at the foot of this
# file). It coincides with gold whenever the current snapshot holds the model
# under its current name, and diverges when the current snapshot instead carries
# a stale entry under the prior name: gold finds nothing, this rival finds the
# stale state.
_R7_PRELUDE = "  let mut acc := []\n  let mut cur := currentStates\n"
_R7_BODY = (
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    match cur.lookup (appLabel, modelName) with\n"
    "    | some st => cur := ((appLabel, priorName), st) :: cur\n"
    "    | none    => pure ()\n"
    "    let currentState := cur.lookup (appLabel, priorName)\n"
    "    acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)


# ---------------------------------------------------------------------------
# P3 (added by audit): the recovered `pos-inline-priorname` omission. The nagini
# sibling inlined the prior-name helper's body as a guarded conditional; the
# Lean analogue replaces `.getD` with an explicit `match` on the `Option`. That
# is a genuinely different SHAPE (a case split rather than a library projection)
# and the frozen tactic body does NOT discharge it — the induction step needs a
# case split on the rename-map lookup — so it is a real reproof, not a restated
# obligation. Must verify.
_POS_INLINE_BODY = (
    "    let priorName := match renameMap.lookup (appLabel, modelName) with\n"
    "      | some n => n\n"
    "      | none   => modelName\n"
    "    let priorState   := priorStates.lookup (appLabel, priorName)\n"
    "    let currentState := currentStates.lookup (appLabel, modelName)\n"
    "    acc := acc ++ [(priorState, currentState)]\n"
    "  return acc"
)
_POS_INLINE_PROOF = (
    "  intro renameMap priorStates currentStates entries\n"
    "  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels\n"
    "  simp only [Id.run]\n"
    "  have helper : ∀ (es : List (String × String × String))\n"
    "      (init : List (Option ModelState × Option ModelState)),\n"
    "      (forIn (m := Id) es init (fun entry r =>\n"
    "            pure (ForInStep.yield\n"
    "              (r ++ [(List.lookup (entry.1, match List.lookup (entry.1, entry.2.1) renameMap with\n"
    "                        | some n => n | none => entry.2.1) priorStates,\n"
    "                      List.lookup (entry.1, entry.2.1) currentStates)]))))\n"
    "        = init ++ es.map (resolveOne renameMap priorStates currentStates) := by\n"
    "    intro es\n"
    "    induction es with\n"
    "    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [bind, List.map_cons]\n"
    "      rw [ih]\n"
    "      cases hl : List.lookup (a.1, a.2.1) renameMap <;>\n"
    "        simp [resolveOne, hl, List.append_assoc]\n"
    "  have h2 : (forIn (m := Id) entries [] (fun entry r =>\n"
    "            (do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield\n"
    "                (r ++ [(List.lookup (entry.1, match List.lookup (entry.1, entry.2.1) renameMap with\n"
    "                          | some n => n | none => entry.2.1) priorStates,\n"
    "                        List.lookup (entry.1, entry.2.1) currentStates)])))))\n"
    "        = forIn (m := Id) entries [] (fun entry r =>\n"
    "            pure (ForInStep.yield\n"
    "              (r ++ [(List.lookup (entry.1, match List.lookup (entry.1, entry.2.1) renameMap with\n"
    "                        | some n => n | none => entry.2.1) priorStates,\n"
    "                      List.lookup (entry.1, entry.2.1) currentStates)]))) := rfl\n"
    "  rw [h2, helper, List.nil_append]\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (added by the second audit). The first audit recorded this lane
# as INEXPRESSIBLE on the ground that the frozen obligation binds four inputs
# with NO hypothesis, so there is no precondition to be too strong. That reason
# is the one the audit protocol names as measured-wrong: on a TOTAL carrier the
# analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly
# an F2P-shaped input, which a positive that discharges the obligation at that
# concrete input tests directly — and it is not the same claim as the `∀`, because
# the `∀` is discharged by a symbolic induction that never evaluates the carrier
# at any point at all. Here the ground instance is the RENAMED-model
# configuration (prior name != current name, the current snapshot holding the
# model only under its current name): the exact shape the issue concerns and the
# one the whole discriminating clause turns on. `decide` closes it by evaluation,
# so it also certifies the three `List.lookup`s actually reduce at that point —
# the thing every reject witness in this file silently depends on.
#
# Nothing is assumed: no new declaration, no axiom, the obligation STATEMENT is
# byte-identical, and the frozen tactic body follows the `have` verbatim.
_ADMISS_RMAP = '[(("a","m2"), "m1")]'
_ADMISS_PRIOR = '[(("a","m1"), { name := "m1", fields := ["x"] })]'
_ADMISS_CUR = '[(("a","m2"), { name := "m2", fields := ["x","y"] })]'
_ADMISS_ENT = '[("a","m2","f")]'
_ADMISS_HAVE = (
    "  have _ground : problem_spec_resolveFieldModels\n"
    f"      {_ADMISS_RMAP}\n      {_ADMISS_PRIOR}\n"
    f"      {_ADMISS_CUR}\n      {_ADMISS_ENT}\n"
    "      (implementation_resolveFieldModels\n"
    f"        {_ADMISS_RMAP}\n        {_ADMISS_PRIOR}\n"
    f"        {_ADMISS_CUR}\n        {_ADMISS_ENT}) := by\n"
    "    unfold problem_spec_resolveFieldModels implementation_resolveFieldModels\n"
    "    decide\n" + _GOLD_INTRO
)


def _witness(rmap, prior, cur, entries):
    """A refutation stated at concrete literal inputs; `decide` closes it against
    the rival and fails against gold (List.lookup is total, so every argument
    computes). Binders are empty, so the assumptions are trivially satisfiable.
    """
    call = (f"problem_spec_resolveFieldModels\n"
            f"    {rmap} {prior}\n"
            f"    {cur} {entries}")
    impl = (f"(implementation_resolveFieldModels\n"
            f"      {rmap} {prior}\n"
            f"      {cur} {entries})")
    return (f"example : ¬ {call}\n"
            f"    {impl} := by\n"
            f"  unfold problem_spec_resolveFieldModels implementation_resolveFieldModels\n"
            f"  decide")


# Renamed-model configuration (prior name != current name): renameMap present.
_W1 = _witness(
    '[(("a","m2"), "m1")]',
    '[(("a","m1"), { name := "m1", fields := ["x"] })]',
    '[(("a","m2"), { name := "m2", fields := ["x","y"] })]',
    '[("a","m2","f")]')
_W2 = _witness(
    '[(("b","n2"), "n1")]',
    '[(("b","n1"), { name := "n1", fields := ["p"] })]',
    '[(("b","n2"), { name := "n2", fields := ["p","q"] })]',
    '[("b","n2","g")]')
# Not-renamed configuration (prior name == current name): renameMap empty. R3/R4
# are refuted here because they mishandle the pair shape / the snapshot choice
# independently of any rename.
_W3 = _witness(
    '[]',
    '[(("a","m"), { name := "m", fields := ["x"] })]',
    '[(("a","m"), { name := "m", fields := ["x","y"] })]',
    '[("a","m","f")]')
_W4 = _witness(
    '[]',
    '[(("c","k"), { name := "k", fields := ["s"] })]',
    '[(("c","k"), { name := "k", fields := ["s","t"] })]',
    '[("c","k","h")]')
# TWO-entry configuration (added by audit). Order and length are only observable
# at length >= 2, and the two located pairs must differ so that a reversal is
# detectable: entry 1 resolves to (m1, m2) states, entry 2 to (q1, q2) states.
# Both models are renamed this step, so this also exercises the translation.
_TWO_RMAP = '[(("a","m2"), "m1"), (("a","q2"), "q1")]'
_TWO_PRIOR = ('[(("a","m1"), { name := "m1", fields := ["x"] }), '
              '(("a","q1"), { name := "q1", fields := ["z"] })]')
_TWO_CUR = ('[(("a","m2"), { name := "m2", fields := ["x","y"] }), '
            '(("a","q2"), { name := "q2", fields := ["z","w"] })]')
_TWO_ENT = '[("a","m2","f"), ("a","q2","g")]'
_W5 = _witness(_TWO_RMAP, _TWO_PRIOR, _TWO_CUR, _TWO_ENT)
_W6 = _witness(_TWO_RMAP, _TWO_PRIOR, _TWO_CUR, _TWO_ENT)
# R7's divergence point: the current snapshot carries the model under its PRIOR
# name only (a stale entry), NOT under its current name. Gold's current-name
# index locates nothing; R7's shadow-then-read-by-prior-name locates the stale
# state. Single entry suffices — the defect is per-entry.
_W7 = _witness(
    '[(("a","m2"), "m1")]',
    '[(("a","m1"), { name := "m1", fields := ["x"] })]',
    '[(("a","m1"), { name := "m1", fields := ["x","y"] })]',
    '[("a","m2","f")]')


SPEC_TESTS = [
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_MAP_IMPL),
                        _GOLD_PROOF, _POS_MAP_PROOF),
        "rationale": "structurally-different CORRECT impl: the per-entry resolution "
                     "is expressed as a single `entries.map` over an inline closure "
                     "instead of an accumulator loop. It is definitionally equal to "
                     "`entries.map resolveOne`, so the postcondition clause "
                     "`result = entries.map (resolveOne …)` closes by `rfl`; must "
                     "verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-reorder-lookups",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_LOOP_BODY, _POS_REORDER_BODY),
        "rationale": "keeps the imperative loop skeleton but computes the "
                     "current-snapshot lookup before the prior-name translation and "
                     "prior lookup (independent reads, reordered). The result tuple "
                     "is unchanged, so the frozen proof body discharges verbatim; "
                     "must verify.",
    },
    {
        "id": "pos-inline-priorname",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_LOOP_BODY, _POS_INLINE_BODY),
                        _GOLD_PROOF, _POS_INLINE_PROOF),
        "rationale": "recovers the sibling battery's inlined-helper positive on this "
                     "carrier: the prior-name translation is written as an explicit "
                     "`match` on the rename-map lookup's `Option` instead of the "
                     "`.getD` projection. The shape genuinely differs — the frozen "
                     "tactic body does NOT discharge it, and the induction step needs "
                     "a case split on that lookup — so the obligation is REPROVEN, not "
                     "restated. Must verify (else SPEC-TOO-STRONG on a faithful "
                     "reshape of the fallback).",
    },
    {
        "id": "admiss-ground-renamed",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_INTRO, _ADMISS_HAVE),
        "rationale": "the obligation is discharged, by EVALUATION, at a concrete "
                     "renamed-model input — the rename map sends the current key to "
                     "a distinct prior name, the prior snapshot holds the model "
                     "under that prior name, and the current snapshot holds it under "
                     "its CURRENT name — as a `have`, before the frozen tactic body "
                     "closes the shipped obligation verbatim. This is the total "
                     "carrier's analogue of PRECOND-TOO-STRONG: it shows the modeled "
                     "behavior is SATISFIABLE at exactly the configuration the "
                     "discriminating clause turns on, which the shipped `∀` does not "
                     "establish, since its symbolic induction never evaluates the "
                     "carrier at any point. It also certifies that the three "
                     "association lookups genuinely reduce there — the property every "
                     "reject witness in this battery relies on. Nothing is assumed: "
                     "no new declaration, statement byte-identical. Must verify.",
    },
    {
        "id": "reject-current-by-prior-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_LOOP_TAIL, _R1_BODY),
        "witness": _W1,
        "rationale": "attacks the discriminating clause: slot 1 must be the CURRENT "
                     "snapshot indexed by the CURRENT name. This rival indexes it by "
                     "the PRIOR name, so on a renamed model (prior name != current "
                     "name) it locates a different/absent state. Witness: renameMap "
                     "maps the current key to a distinct prior name, both snapshots "
                     "populated — gold returns the current state, the rival returns "
                     "`none`.",
        "refinement": "this is the pre-patch index (the current snapshot keyed by "
                     "the prior model name). On the F2P — a model AND one of its "
                     "fields renamed in one step — the renamed model is absent from "
                     "the current snapshot under its prior name, raising the KeyError "
                     "in the issue traceback; the faithful patch does NOT resolve.",
    },
    {
        "id": "reject-prior-by-current-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_LOOP_TAIL, _R2_BODY),
        "witness": _W2,
        "rationale": "attacks slot 0: the prior snapshot must be indexed by the "
                     "PRIOR name (the current name translated back through the rename "
                     "map). This rival drops the translation and indexes by the "
                     "current name, so on a renamed model the prior state is "
                     "wrong/absent. Witness: renameMap maps the current key to a "
                     "distinct prior name and the prior snapshot is keyed by that "
                     "prior name — gold locates it, the rival returns `none`.",
        "refinement": "skipping the rename-map translation regresses the prior-state "
                     "lookup (`from_state.models[app_label, old_model_name]`) to the "
                     "current name; the prior snapshot is keyed by the prior name, so "
                     "the model is not found and rename detection mis-fires — it does "
                     "not resolve the F2P.",
    },
    {
        "id": "reject-transposed-slots",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_LOOP_TAIL, _R3_BODY),
        "witness": _W3,
        "rationale": "attacks the ORDER of the located pair: both lookups are legal, "
                     "but the result must be `(prior, current)`. This rival returns "
                     "`(current, prior)`. Witness (no rename): the same model has "
                     "different field sets in the two snapshots, so the two states "
                     "differ and the transposed pair is not the gold pair. Probed at "
                     "the unchanged-name subdomain so the refutation isolates the "
                     "slot order, not the keying.",
        "refinement": "feeding the current-snapshot ModelState where the prior is "
                     "expected (and vice versa) into the downstream field-rename "
                     "comparison mis-detects renames; transposing the states is "
                     "neither the gold nor the pre-patch line and would not resolve "
                     "the F2P.",
    },
    {
        "id": "reject-current-from-prior-snapshot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_LOOP_TAIL, _R4_BODY),
        "witness": _W4,
        "rationale": "attacks slot 1's SNAPSHOT: the current state must come from the "
                     "current snapshot. This rival reads slot 1 from the PRIOR "
                     "snapshot (correct key, wrong snapshot). Witness (no rename): "
                     "the same key holds different states in the two snapshots, so "
                     "the rival returns the stale prior state where gold returns the "
                     "current one. Slot 0 agrees with gold here, isolating the "
                     "snapshot choice.",
        "refinement": "reading the current-snapshot slot out of the prior-state "
                     "registry returns a stale ModelState (or none) to the rename "
                     "scan, comparing the wrong field surface; it is neither the gold "
                     "nor the pre-patch line and would not resolve the F2P.",
    },
    {
        "id": "reject-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_LOOP_TAIL, _R5_BODY),
        "witness": _W5,
        "rationale": "attacks the ORDER half of the clause `result = entries.map …`: "
                     "every per-entry pair is resolved correctly, but the accumulator "
                     "prepends and is never re-reversed, so the result is the reverse "
                     "of the required sequence. Witness is stated at a TWO-entry input "
                     "whose two located pairs differ — order is unobservable at length "
                     "one, which is why the other rivals here do not reach this half "
                     "of the clause.",
        "refinement": "emitting the per-entry results in reverse feeds the downstream "
                     "per-field selection step the wrong owning-model states for every "
                     "candidate but the palindromic case; it is neither the gold nor "
                     "the pre-patch line and would not resolve the F2P.",
    },
    {
        "id": "reject-first-entry-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_LOOP_TAIL, _R6_BODY),
        "witness": _W6,
        "rationale": "attacks the ENTRY-FOR-ENTRY (length) half of the same clause: "
                     "the first candidate is resolved correctly and every later one is "
                     "dropped, so the result is a strict prefix of the required list. "
                     "On a one-entry input this rival is observably IDENTICAL to gold, "
                     "so the witness must use two entries — the gap the single-entry "
                     "witnesses left open.",
        "refinement": "dropping all but the first candidate field key silently skips "
                     "rename detection for the remaining candidates; it is neither the "
                     "gold nor the pre-patch line and would not resolve the F2P.",
    },
    {
        "id": "reject-shadowed-current-snapshot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_swap(_BASE, "  let mut acc := []\n", _R7_PRELUDE),
                        _GOLD_LOOP_TAIL, _R7_BODY),
        "witness": _W7,
        "rationale": "instead of indexing the current snapshot by the CURRENT name, "
                     "this rival copies the located state in under the model's PRIOR "
                     "name (a local shadow of the snapshot list) and reads slot 1 back "
                     "by that prior name. Witness: the current snapshot carries the "
                     "model under its prior name only, so gold's current-name index "
                     "locates nothing while the rival returns the stale state — "
                     "`none` vs `some`.",
        "refinement": "re-keying the current-snapshot entry under the prior model name "
                     "so a prior-name index succeeds preserves the pre-patch keying "
                     "rather than correcting it, and on the F2P the state it surfaces "
                     "is the one carried under the prior name — not the renamed "
                     "model's current state; it does not resolve the F2P.",
    },
]

# AXIOM_TESTS: none. The axioms region of this bundle is empty (the three map
# indexings are modeled deeply as total `List.lookup`s; no opaque callee
# contract is consumed), so the axiom lane (G-AX) has nothing to probe.
AXIOM_TESTS = []


# ---------------------------------------------------------------------------
# Sibling-battery cases NOT ported, with the reason each is inexpressible here.
# Re-derived by audit with real builds rather than inherited.
#
# * the two frame-mutation cases (a read-only input written to, rejected for
#   insufficient permission): INEXPRESSIBLE AS A FRAME CASE. The sibling's
#   rejection came from fractional permission on a shared mutable mapping; this
#   carrier is referentially transparent, so `cur := … :: cur` can only rebind a
#   LOCAL shadow and no permission obligation exists to violate. The shape does
#   survive as an ordinary VALUE rival, so it is not dropped: it is ported that
#   way as `reject-shadowed-current-snapshot`, refuted on values. The prior-side
#   sibling (overwrite the prior snapshot so slot 0 echoes slot 1) is likewise a
#   value rival here; it was built and confirmed refutable, but it is subsumed by
#   `reject-transposed-slots`/`reject-current-from-prior-snapshot` (same clause,
#   same subdomain) and is left out as redundant rather than as inexpressible.
#
# * the admissibility case (a self-call on a renamed-model input, showing the
#   precondition admits the configuration the issue concerns): EXPRESSIBLE, and
#   now ported as `admiss-ground-renamed` (found missing by the SECOND audit).
#   The first audit's "INEXPRESSIBLE" reason — the frozen obligation binds four
#   inputs with no hypothesis, so there is no precondition to be too strong —
#   describes the frozen obligation correctly but draws the wrong conclusion. On
#   a total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#   unsatisfiable at exactly an F2P-shaped input, and a ground instance is NOT a
#   strictly weaker restatement of the shipped `∀`: the `∀` is discharged by a
#   symbolic induction over the entry list that never evaluates the carrier at any
#   concrete point, so it does not witness that the modeled behavior HOLDS
#   anywhere, nor that the three association lookups reduce. Both were confirmed
#   by a real build at the renamed-model configuration.
#
# * the nagini `diverge`/`nonterm` divergence lane: VACUOUS on this carrier, and
#   demonstrated rather than asserted. This bundle sets no
#   `loom.semantics.termination` (vanilla Lean 4 + Mathlib, not a Loom carrier),
#   so termination is not a discharged obligation but a CONDITION OF DEFINITION.
#   Both routes were built. (a) A recursive impl with no decreasing measure is
#   rejected at `fail to show termination for`, i.e. the impl region does not
#   elaborate at all — so the witness build fails on the RIVAL side, the half that
#   must succeed, and the case can only ever land as `witness-unproven`. (b) The
#   only way vanilla Lean ACCEPTS a diverging definition is `partial def`, which
#   is opaque to the kernel: `unfold` then fails on `implementation_…` on BOTH
#   sides, so no witness can discriminate, and `partial` is a banned witness token
#   besides. There is no third route, so the class ships nothing here — this is a
#   vacuous class, not a known hole.
#
# * the inlined-helper positive: EXPRESSIBLE, and now ported as
#   `pos-inline-priorname` (found missing by audit).
