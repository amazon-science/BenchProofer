# properties.py — G-PBT falsification battery for django__django-15957 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC case is a FULL
# Solution.lean variant that shares the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive must reprove, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the postcondition and not to a
# tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   restrictPrefetch (query : RelatedQuery) (fieldName : String)
#                    (instances : List Int) : FilteredQuery
#   Restrict a bulk related-object query to the related objects belonging to a
#   supplied set of parents, honoring any requested contiguous slice of each
#   parent's related objects. The single postcondition
#   `problem_spec_restrictPrefetch` is a two-armed implication on `isSliced query`,
#   and it pins EVERY output component to the input:
#     (1) NO-SLICE arm — `isSliced query = false →` the result is exactly
#         `{ predicate := [memberOf fieldName instances],
#            offset := query.offset, limit := query.limit }`: the membership
#         condition is the WHOLE restriction and the bounds are unchanged.
#     (2) SLICE arm — `isSliced query = true →` three independent conjuncts:
#         (2a) `result.offset = 0` and `result.limit = none` — the plain bounds are
#              dropped, because the slice is now carried by conditions;
#         (2b) `result.predicate` begins with the membership condition
#              `memberOf fieldName instances` — the parent restriction is always
#              present, and is built from BOTH `fieldName` and `instances`;
#         (2c) the per-group position conditions follow, in order: a lower bound
#              `positionAbove r query.offset` and, exactly when a limit is present,
#              an upper bound `positionAtMost r h` — where the ranking
#              `r = { groupBy := fieldName, ordering := query.ordering }` pins the
#              grouping key AND the within-group order.
#   The carrier is FULLY TRANSPARENT: `RelatedQuery`, `FilteredQuery`, `PredAtom`
#   and `Ranking` all derive `DecidableEq`, and `isSliced` is a total Bool fold. So
#   `decide` computes the whole postcondition at any literal input and no witness
#   needs to condition on an opaque term.
#
# CARRIER NOTE — what the nagini rivals BECOME here. The nagini sibling modeled the
# same behavior as an in-place MUTATION of a full-permission query object: a
# forgeable `membership_applied` boolean plus an unforgeable capability token granted
# only by a callee that refuses to run while a slice is present, and `lower_bound` /
# `upper_bound` fields written as side effects. Lean is referentially transparent, so
# this bundle models the identical behavior as a VALUE: the restriction is a
# `List PredAtom` returned in the result, and the "membership was applied" fact is
# the PRESENCE of a `memberOf` conjunct in that list rather than a flag. That is a
# strictly more attackable surface — the membership conjunct's ARGUMENTS are visible,
# not just its existence — so the two nagini token-forgery rivals port as FOUR
# value-level rivals here: the "forge the flag while still sliced" shape becomes an
# empty restriction returned with surviving bounds (weak-echo-sliced), and the "forge
# after a correct clear" shape splits three ways because the conjunct's arguments are
# now visible (omit the conjunct; build it with the wrong parents; build the ranking
# with the wrong grouping key). The two nagini bound-value rivals port directly. So
# nothing in the nagini token lane is dropped — the token is not needed on this
# carrier because what it protected is directly observable in the returned value.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION MUTATION. Nagini's analogue of this class is the capability
#     token (its query is a full-permission carrier meant to be mutated, so even
#     there the classic "write into a read-only half-permission input" probe was
#     N/A). Lean has no aliasing and no fractional permission, so a
#     mutate-a-read-only-input rival is not expressible at all. VACUOUS here — no
#     substitute is fabricated. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class (AUDIT
#     CORRECTION; the port recorded it as "genuinely vacuous ... a diverging
#     implementation cannot be written", which is measurably false). This bundle
#     sets no `loom.semantics.termination` line at all, so the frozen artifact is
#     a plain total Lean `def` and the obligation carries no termination duty that
#     a rival could fail. A diverging rival IS expressible: adding an `Inhabited
#     FilteredQuery` instance in the impl region and making the definition
#     `partial def` with a self-call on the sliced arm passes `variant_scope`
#     cleanly (measured: `variant_problems` -> []) and introduces no banned
#     assumption token. What blocks SHIPPING it is not expressibility but
#     REFUTABILITY: a `partial def` is compiled by well-founded recursion with no
#     equational unfolding, so both the variant build and its witness build fail
#     with `Tactic `unfold` failed to unfold `implementation_restrictPrefetch``
#     — a tactic-shaped failure on BOTH sides, which is exactly the hollow
#     rejection the witness requirement exists to reject. No witness can
#     discriminate, so there is nothing shippable here; the residual gap (a
#     non-terminating impl is neither refuted nor proven wrong by this spec) is
#     recorded as a HOLE and stays visible rather than being dressed up as
#     complete. See 'assessment'.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. (There is
#     no consumed axiom in this bundle regardless — the query-construction
#     primitives are modeled deeply as data, and meta.json records G-AX as a skip.)
from pathlib import Path

INSTANCE = "django__django-15957"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --------------------------------------------------------------------------- #
# Frozen anchors. `_IMPL` is the ENTIRE body of the frozen                      #
# `implementation_restrictPrefetch` (everything after the signature, inside     #
# impl-start/impl-end); `_PROOF` is the ENTIRE frozen tactic body inside         #
# proof-start/proof-end. Both are unique in the file, so every _swap below is    #
# confined to the impl region (or, for a reproving positive, the proof body) and  #
# markers.same_spec holds by construction.                                       #
# --------------------------------------------------------------------------- #

_IMPL = """  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
    if let some h := query.limit then
      predicate := predicate ++ [PredAtom.positionAtMost r h]
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }"""
assert _BASE.count(_IMPL) == 1, "impl-region anchor drifted from Solution.lean"

_PROOF = """  intro query fieldName instances
  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
  by_cases h : isSliced query = true
  · constructor
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
    · intro _
      simp only [h, if_true, Id.run, bind, pure]
      cases hl : query.limit with
      | none => simp
      | some v => simp
  · simp only [Bool.not_eq_true] at h
    constructor
    · intro _
      simp only [h, Bool.false_eq_true, if_false, Id.run, bind, pure]
    · intro hf; rw [h] at hf; exact absurd hf (by simp)"""
assert _BASE.count(_PROOF) == 1, "proof-body anchor drifted from Solution.lean"


def _rival(impl):
    """A variant that edits ONLY the impl region; the frozen proof body stays."""
    return _swap(_BASE, _IMPL, impl)


def _positive(impl, proof):
    """A variant that edits the impl region AND honestly re-closes the proof.
    The `theorem correct_restrictPrefetch` STATEMENT is untouched (only the tactic
    body inside proof-start/proof-end changes) and no axiom / lemma / sorry /
    native_decide is introduced."""
    return _swap(_swap(_BASE, _IMPL, impl), _PROOF, proof)


# =========================================================================== #
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.           #
# =========================================================================== #

# pos-clear-unconditional (ports nagini's pos-reorder-clear-first): drop the two
# bound-clearing assignments out of the conditional entirely and return
# `offset := 0, limit := none` UNCONDITIONALLY. This is correct because
# `isSliced query = false` MEANS `query.offset = 0` and `query.limit = none`, so on
# the no-slice arm the unconditional clear is a no-op that still returns the input
# bounds. Structurally different (one fewer mutable local, the clear hoisted out of
# the branch), behaviourally identical. The frozen script's no-slice arm closed by
# rewriting with `isSliced query = false` directly; here that arm must additionally
# decompose the `isSliced` fold into its two components to see that the returned
# literals equal the input bounds — so the proof body is honestly re-closed. If this
# FAILS => SPEC-TOO-STRONG (the postcondition is over-fit to one branch shape).
_POS_CLEAR_UNCONDITIONAL_IMPL = """  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
    if let some h := query.limit then
      predicate := predicate ++ [PredAtom.positionAtMost r h]
  return { predicate := predicate, offset := 0, limit := none }"""

_POS_CLEAR_UNCONDITIONAL_PROOF = """  intro query fieldName instances
  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
  by_cases h : isSliced query = true
  · constructor
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
    · intro _
      simp only [h, if_true, Id.run, bind, pure]
      cases hl : query.limit with
      | none => simp
      | some v => simp
  · simp only [Bool.not_eq_true] at h
    constructor
    · intro hns
      simp only [hns, Bool.false_eq_true, if_false, Id.run, bind, pure]
      unfold isSliced at h
      simp_all
    · intro hf; rw [h] at hf; exact absurd hf (by simp)"""

# pos-reorder-writes (ports nagini's pos-reorder-writes): keep the branch structure
# but reorder the writes inside it — the bounds are dropped FIRST, and the two
# position conditions are then appended in a single `match` on the limit instead of
# an append followed by a conditional append. The resulting predicate list is the
# same list in the same order, and the bound writes are order-independent, so the
# value spec is untouched. The frozen tactic body still closes it unchanged, which is
# itself the cleanest evidence the postcondition is about VALUES and not about the
# order in which the impl happens to produce them. If it FAILS => SPEC-TOO-STRONG.
_POS_REORDER_WRITES_IMPL = """  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    limit := none
    offset := 0
    predicate := match query.limit with
      | some h => predicate ++
          [PredAtom.positionAbove r query.offset, PredAtom.positionAtMost r h]
      | none => predicate ++ [PredAtom.positionAbove r query.offset]
  return { predicate := predicate, offset := offset, limit := limit }"""

# pos-pure-no-mutation (AUDIT ADDITION — no nagini counterpart; nagini's carrier
# is an in-place mutation of a query object, so "the same behavior with no mutable
# state" is a reshape only this carrier can express). Both existing positives keep
# the frozen `Id.run do` + `let mut` skeleton and vary only the ORDER of writes
# inside it, so before this case the battery never checked that the postcondition
# is indifferent to the imperative shape ITSELF. This impl drops every `let mut`:
# the limit-dependent conjunct and the whole sliced predicate are pre-computed as
# pure `let`s and the two arms `return` finished records, so the result is built by
# `::` on both arms where the frozen impl uses `++` under mutation. Correct because
# the produced list and both bounds agree with the frozen impl at every input.
# `++`-vs-`::` is NOT definitionally equal here at the goal's shape — the frozen
# tactic body does NOT close it (measured: `unsolved goals`), so the proof body is
# honestly re-closed with `simp [hl]` supplying the limit case on the slice arm. If
# it FAILS => SPEC-TOO-STRONG: the postcondition would be over-fit to the frozen
# impl's mutable-accumulator shape rather than to the values it produces.
_POS_PURE_IMPL = """  let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
  let upper : List PredAtom :=
    match query.limit with
    | some h => [PredAtom.positionAtMost r h]
    | none => []
  let sliced : List PredAtom :=
    PredAtom.memberOf fieldName instances ::
      PredAtom.positionAbove r query.offset :: upper
  if isSliced query then
    return { predicate := sliced, offset := 0, limit := none }
  else
    return { predicate := [PredAtom.memberOf fieldName instances],
             offset := query.offset, limit := query.limit }"""

_POS_PURE_PROOF = """  intro query fieldName instances
  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
  by_cases h : isSliced query = true
  · constructor
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
    · intro _
      simp only [h, if_true, Id.run, bind, pure]
      cases hl : query.limit with
      | none => simp [hl]
      | some v => simp [hl]
  · simp only [Bool.not_eq_true] at h
    constructor
    · intro _
      simp only [h, Bool.false_eq_true, if_false, Id.run, bind, pure]
    · intro hf; rw [h] at hf; exact absurd hf (by simp)"""


# =========================================================================== #
# ADMISSIBILITY (AUDIT ADDITION) — the obligation must be SATISFIABLE at the   #
# concrete input shapes the change is about.                                   #
# =========================================================================== #
# The port dropped this lane on the ground that "the lean obligation has NO
# precondition hypothesis, so nothing could be PRECOND-TOO-STRONG and the lane is
# N/A". That reason is wrong: on a TOTAL carrier the analogue of a too-strong
# precondition is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input, and that is directly testable — discharge the postcondition at that
# concrete input, BY EVALUATION, as a `have`, before closing the frozen obligation
# verbatim. Dropping the lane removed one of the three directions this gate exists
# to test (the coverage reporter flags it independently).
#
# The two inputs are the two slice shapes the modeled behavior is actually pinned
# at: an OPEN-ENDED slice from a nonzero start position (offset 1, no limit) and a
# CLOSED one-position slice (offset 1, limit 2). They drive the two distinct arms
# of the limit-dependent tail, which is where an unsatisfiable spec would surface
# first — the arm that must append an upper position condition and the arm that
# must not.
#
# The `have`s are MEASURED load-bearing, not decorative: carried verbatim onto the
# slice-ignoring rival (_RIV_IGNORE_SLICE) each one fails AT ITS OWN LINE with
# `decide` proving the proposition FALSE, independently of the frozen tactic body
# that follows. So they really do evaluate the postcondition at these inputs
# rather than discharging something put in front of them.
#
# Nothing is assumed: the `theorem correct_restrictPrefetch` statement stays
# byte-identical, the frozen tactic body follows the `have`s verbatim, and no new
# declaration / axiom / sorry / native_decide is introduced.
_ADMISS_HAVES = """  have admissible_open_ended :
      problem_spec_restrictPrefetch
          { ordering := ["o"], offset := 1, limit := none } "f" [1, 2]
        (implementation_restrictPrefetch
          { ordering := ["o"], offset := 1, limit := none } "f" [1, 2]) := by
    unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
    decide
  have admissible_closed :
      problem_spec_restrictPrefetch
          { ordering := ["o"], offset := 1, limit := some 2 } "f" [1, 2]
        (implementation_restrictPrefetch
          { ordering := ["o"], offset := 1, limit := some 2 } "f" [1, 2]) := by
    unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
    decide
"""

_ADMISS_HEAD = "  intro query fieldName instances\n"
assert _PROOF.startswith(_ADMISS_HEAD), "frozen proof no longer opens with intro"
# The frozen body VERBATIM, with the two evaluation `have`s spliced in after its
# own `intro` and before anything else it does.
_ADMISS_PROOF = _ADMISS_HEAD + _ADMISS_HAVES + _PROOF[len(_ADMISS_HEAD):]


# =========================================================================== #
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the    #
# frozen spec exactly, edits ONLY the impl region, and carries a witness that   #
# was SEEN to elaborate against the rival and fail on the frozen solution.      #
# =========================================================================== #

# (A) ports nagini atk-vacuous: ignore the slice completely — emit only the
# membership condition and hand back the bounds untouched. This is the pre-change
# shape (it is byte-for-byte the frozen Solution_prepatch impl).
_RIV_IGNORE_SLICE = """  let predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  return { predicate := predicate, offset := query.offset, limit := query.limit }"""

# (A2) ports nagini atk-echo-sliced (the "claim membership while the query is STILL
# SLICED" forgery). On nagini this was pinned by the unforgeable capability token,
# whose granting callee refuses to run while a slice is present; here the same
# behavior is a VALUE, so the forgery is simply: emit no restriction at all AND hand
# the bounds back untouched. It is refuted by both halves of the slice arm at once —
# the predicate is empty where (2b)/(2c) demand three conjuncts, and the bounds
# survive where (2a) demands they be dropped. Distinct from weak-drop-membership
# (which translates the slice correctly and only omits the base conjunct) and from
# weak-ignore-slice (which DOES emit the base conjunct); this rival gets neither
# right, which is the shape nagini's token lane actually described.
_RIV_ECHO_SLICED = """  let predicate : List PredAtom := []
  return { predicate := predicate, offset := query.offset, limit := query.limit }"""

# (B) ports the VALUE half of nagini atk-echo-after-clear: everything about the
# slice translation is right, but the membership condition itself is never emitted.
# On the nagini carrier this was a forged flag; here the conjunct is simply absent
# from the returned list.
_RIV_DROP_MEMBERSHIP = _IMPL.replace(
    "[PredAtom.memberOf fieldName instances]", "[]", 1)

# (C) ports nagini atk-drop-lower-offset-only: emit the position conditions ONLY
# when an upper limit is present, so an open-ended (offset-only) slice loses its
# lower position restriction entirely while its bounds are still dropped.
_RIV_LOWER_ONLY_WITH_LIMIT = """  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    if let some h := query.limit then
      predicate := predicate ++
        [PredAtom.positionAbove r query.offset, PredAtom.positionAtMost r h]
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }"""

# (D) ports nagini atk-no-clear: build both position conditions correctly but never
# drop the plain bounds, so the result still carries the slice it just re-expressed.
_RIV_NO_CLEAR = _IMPL.replace("    offset := 0\n    limit := none\n", "", 1)

# (E) ports nagini atk-swap-bounds: the lower position condition carries the LIMIT
# and the upper carries the OFFSET.
_RIV_SWAP_BOUNDS = """  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ (match query.limit with
      | some h => [PredAtom.positionAbove r h, PredAtom.positionAtMost r query.offset]
      | none => [PredAtom.positionAbove r query.offset])
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }"""

# (F) ports nagini atk-upper-always: always emit an upper position condition, using
# the offset as a stand-in when no limit was requested.
_RIV_UPPER_ALWAYS = """  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
    predicate := predicate ++ (match query.limit with
      | some h => [PredAtom.positionAtMost r h]
      | none => [PredAtom.positionAtMost r query.offset])
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }"""

# (G) NEW on this carrier (no nagini counterpart — nagini's membership step was an
# opaque effect with no visible arguments, so its parent list could not be attacked).
# The membership condition IS emitted, in the right position, but built over an EMPTY
# parent set instead of the supplied one.
_RIV_MEMBERSHIP_DROPS_PARENTS = _IMPL.replace(
    "[PredAtom.memberOf fieldName instances]", "[PredAtom.memberOf fieldName []]", 1)

# (H) NEW on this carrier: the per-group ranking is built with NO within-group
# ordering, so the position a condition refers to is not the position in the
# requested order.
_RIV_RANKING_DROPS_ORDERING = _IMPL.replace(
    "{ groupBy := fieldName, ordering := query.ordering }",
    "{ groupBy := fieldName, ordering := [] }", 1)

# (I) NEW on this carrier: the ranking's GROUPING key is empty rather than the
# relation being traversed, so positions are counted over the whole flat result
# instead of within each parent's group. This is the exact distinction the whole
# behavior exists to make, and it is invisible on nagini's carrier.
_RIV_RANK_NOT_PER_GROUP = _IMPL.replace(
    "{ groupBy := fieldName, ordering := query.ordering }",
    '{ groupBy := "", ordering := query.ordering }', 1)


def _wit(query, field, instances, note):
    """A refutation witness: `¬ problem_spec_restrictPrefetch <args>
    (implementation_restrictPrefetch <args>)` at a CONCRETE literal input, closed by
    `decide`. The whole carrier derives DecidableEq and `isSliced` is a total Bool
    fold, so no conditioning on an opaque term is needed and the head binds nothing
    (hence no consistency probe is required — there are no hypotheses to be
    inconsistent). Elaborates against a rival that diverges from the specified
    result at this point; fails on the frozen solution, which satisfies the
    postcondition everywhere."""
    args = f"{query} {field} {instances}"
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_restrictPrefetch {args}\n"
        f"    (implementation_restrictPrefetch {args}) := by\n"
        f"  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ---------------- #
    {
        "id": "pos-clear-unconditional",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_CLEAR_UNCONDITIONAL_IMPL,
                            _POS_CLEAR_UNCONDITIONAL_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl (ports nagini "
            "pos-reorder-clear-first): the two bound-clearing writes are hoisted OUT "
            "of the conditional, so the result always carries offset := 0 / "
            "limit := none. Correct because `isSliced query = false` MEANS "
            "query.offset = 0 and query.limit = none, so on the no-slice arm the "
            "unconditional clear returns exactly the input bounds and clause (1) "
            "still holds; the slice arm is unchanged. The `theorem "
            "correct_restrictPrefetch` STATEMENT is byte-identical and the proof body "
            "is honestly re-closed (the no-slice arm now decomposes the isSliced fold "
            "into its offset and limit components) with no new axiom / lemma / sorry / "
            "native_decide. If it FAILS => SPEC-TOO-STRONG: the postcondition would be "
            "over-fit to the frozen branch shape rather than to the values."
        ),
    },
    {
        "id": "pos-reorder-writes",
        "kind": "soundness",
        "expect": "verify",
        "module": _rival(_POS_REORDER_WRITES_IMPL),
        "rationale": (
            "correct impl with the writes inside the slice branch REORDERED (ports "
            "nagini pos-reorder-writes): the plain bounds are dropped first, and the "
            "lower and upper position conditions are produced by a single match on "
            "the limit instead of an append followed by a conditional append. The "
            "predicate list and both bounds are identical on every input, so every "
            "clause of both arms still holds and the frozen tactic body closes it "
            "unchanged — direct evidence the postcondition constrains VALUES, not the "
            "order in which the impl produces them. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-no-mutation",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_PURE_IMPL, _POS_PURE_PROOF),
        "rationale": (
            "AUDIT ADDITION: correct impl with the imperative skeleton REMOVED "
            "entirely — no `let mut`, no accumulator. The limit-dependent conjunct "
            "and the full sliced predicate are pre-computed as pure `let`s and each "
            "arm returns a finished record, so the restriction is built by `::` "
            "where the frozen impl builds it by `++` under mutation. This is the "
            "reshape the two existing positives do NOT cover: both of them keep the "
            "frozen `Id.run do` + `let mut` shape and vary only the ORDER of the "
            "writes inside it, so before this case nothing checked that the "
            "postcondition is indifferent to the imperative shape itself. Correct "
            "because the predicate list and both bounds agree with the frozen impl "
            "at every input — clause (1) on the no-slice arm and (2a)/(2b)/(2c) on "
            "the slice arm. The `theorem correct_restrictPrefetch` STATEMENT is "
            "byte-identical; the proof body is honestly re-closed (the `++`-to-`::` "
            "change is NOT definitionally equal at the goal's shape — the frozen "
            "tactic body leaves `unsolved goals`, measured — so the slice arm now "
            "supplies the limit case with `simp [hl]`) and no new axiom / lemma / "
            "sorry / native_decide is introduced. If it FAILS => SPEC-TOO-STRONG: "
            "the postcondition would be over-fit to the frozen mutable-accumulator "
            "shape rather than to the values produced."
        ),
    },

    # ---------------- admissibility (must VERIFY) ---------------- #
    {
        "id": "admiss-f2p-slice-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _positive(_IMPL, _ADMISS_PROOF),
        "rationale": (
            "AUDIT ADDITION — the port dropped this lane entirely, recording it as "
            "N/A because the frozen obligation carries no precondition hypothesis. "
            "That is not the right test on a TOTAL carrier: nothing here can be "
            "PRECOND-TOO-STRONG in the nagini sense, but the analogue is the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input, and "
            "this case tests it directly. The frozen postcondition is discharged BY "
            "EVALUATION (`decide`) at two ground inputs, as `have`s ahead of the "
            "frozen tactic body which then follows VERBATIM: an open-ended slice "
            "from a nonzero start position (offset 1, no limit) and a closed "
            "one-position slice (offset 1, limit 2). Those are the two shapes the "
            "modeled behavior is pinned at, and they drive the two distinct arms of "
            "the limit-dependent tail of clause (2c) — the arm that must append an "
            "upper position condition and the arm that must not — which is where an "
            "unsatisfiable spec would surface first. If either FAILS the modeled "
            "behavior is unsatisfiable at the very input the change is about. The "
            "`have`s are MEASURED load-bearing rather than decorative: carried "
            "verbatim onto the slice-ignoring rival each one fails AT ITS OWN LINE "
            "with `decide` proving the proposition FALSE, independently of the "
            "frozen proof that follows. Nothing is assumed — statement "
            "byte-identical, impl region byte-identical to the frozen one, no new "
            "declaration / axiom / sorry / native_decide. Ports nagini's "
            "admiss-sliced-input."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ---------------- #
    {
        "id": "weak-ignore-slice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_IGNORE_SLICE),
        "refinement": (
            "the faithful real patch is the UNCHANGED pre-fix code: restrict the "
            "related-object query to the supplied parents and leave any requested "
            "slice in place as plain bounds, never re-expressing it as conditions. "
            "That is the reported defect verbatim — narrowing a query that already "
            "carries a slice is rejected outright ('Cannot filter a query once a "
            "slice has been taken', quoted in the issue), so all four F2P "
            "(test_m2m_forward, test_m2m_reverse, test_foreignkey_reverse, "
            "test_reverse_ordering) error out rather than assert. Does NOT resolve, so "
            "a verifying rival here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the SLICE arm (2) in full: on a sliced input the result must "
            "have offset = 0 and limit = none (2a) and its predicate must carry the "
            "two position conditions after the membership condition (2c); this rival "
            "returns the input bounds and a one-element predicate. Attacks the "
            "isSliced-true sub-domain of the `query` binder. If it VERIFIES => "
            "SPEC-TOO-WEAK. (Ports nagini atk-vacuous; it is also the frozen prepatch "
            "impl, so it is the shape G-DIFF already shows the spec must see.)"
        ),
        "witness": _wit('{ ordering := ["t"], offset := 1, limit := none }',
                        '"f"', "[7]",
                        "open-ended slice: the specified result drops the bounds and "
                        "carries a lower position condition; this rival returns "
                        "neither"),
    },
    {
        "id": "weak-echo-sliced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_ECHO_SLICED),
        "refinement": (
            "the faithful real patch neither narrows the query to the supplied "
            "parents nor re-expresses the requested slice, and leaves the plain "
            "bounds in place — it returns the query it was handed. Narrowing a query "
            "that still carries a slice is rejected outright, so the F2P that slice "
            "error out; and even setting that aside, nothing restricts the fetch to "
            "the supplied parents, so the compared attribute is neither per-parent "
            "nor sliced. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the slice arm on BOTH of its independent halves at once: "
            "(2a) demands offset = 0 and limit = none and this rival returns the "
            "input bounds, while (2b)/(2c) demand a three-conjunct predicate and it "
            "returns the empty list. Attacks the conjunction of the bound-dropping "
            "and restriction-building duties, which no other rival leaves BOTH wrong "
            "— weak-ignore-slice keeps the bounds but does emit the base conjunct, "
            "weak-drop-membership omits the base conjunct but translates the slice "
            "and drops the bounds correctly. Witnessed at a closed slice with a "
            "nonzero offset and a distinct limit. If it VERIFIES => SPEC-TOO-WEAK. "
            "(Ports nagini atk-echo-sliced, whose token-forgery framing has no "
            "counterpart here: on this carrier the same forgery is just an empty "
            "restriction returned alongside surviving bounds.)"
        ),
        "witness": _wit('{ ordering := ["r"], offset := 7, limit := some 9 }',
                        '"y"', "[21]",
                        "closed slice: the specified result drops both bounds and "
                        "carries three conjuncts; this rival returns the input "
                        "bounds and an empty restriction"),
    },
    {
        "id": "weak-drop-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_DROP_MEMBERSHIP),
        "refinement": (
            "the faithful real patch translates the slice into per-group position "
            "conditions and drops the plain bounds correctly, but never narrows the "
            "query to the supplied parents at all. Every parent's bulk fetch would "
            "then draw from the related objects of ALL parents, so the attribute each "
            "F2P compares is not the per-parent slice it asserts — all four F2P fail "
            "the assertEqual. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the membership clause in BOTH arms: (1) pins the no-slice "
            "result's predicate to exactly [memberOf fieldName instances], and (2b) "
            "pins the slice result's predicate to START with that same conjunct. This "
            "rival emits an empty base, so the head of the predicate list is wrong "
            "everywhere. Attacks clause (1) / (2b) — the always-present parent "
            "restriction, i.e. the `fieldName` and `instances` binders. Witnessed on "
            "the UNSLICED sub-domain, where clause (1) alone carries the refutation. "
            "If it VERIFIES => SPEC-TOO-WEAK. (Ports the value half of nagini "
            "atk-echo-after-clear / atk-echo-sliced: nagini pinned this with an "
            "unforgeable capability token because its membership step was an invisible "
            "control-flow effect; on this carrier the conjunct is data, so its absence "
            "is directly refutable.)"
        ),
        "witness": _wit('{ ordering := [], offset := 0, limit := none }',
                        '"g"', "[3, 4]",
                        "unsliced input: the specified result is exactly the "
                        "membership condition; this rival returns an empty "
                        "restriction"),
    },
    {
        "id": "weak-lower-only-with-limit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_LOWER_ONLY_WITH_LIMIT),
        "refinement": (
            "the faithful real patch emits the per-group position conditions only "
            "when an upper limit was requested, while still dropping the plain bounds "
            "unconditionally. Three of the four F2P slice open-endedly (offset only, "
            "no stop: test_m2m_forward, test_foreignkey_reverse, test_reverse_ordering "
            "all take a from-position-1 slice), so on those the query loses its lower "
            "restriction AND its bounds and returns each parent's related objects from "
            "position 0 — the compared attribute is the full list, not the slice. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2c): on a sliced input the predicate must be "
            "`base :: positionAbove r query.offset :: (limit-dependent tail)`, so the "
            "lower position condition is required WHENEVER a slice is present, "
            "independently of whether a limit is. On an open-ended slice this rival's "
            "predicate is just [base]. Attacks the limit = none sub-domain of the "
            "`query` binder — precisely the F2P slice shape. It is the ONLY reject "
            "case that GATES the lower position condition on the limit's presence "
            "while dropping both bounds correctly, so it is the only one whose "
            "refutation isolates the lower conjunct's unconditional presence: the "
            "other rivals witnessed at a nonzero offset with an absent limit "
            "(weak-ignore-slice, weak-upper-always, weak-ranking-drops-ordering) each "
            "emit that conjunct and are refuted by a different part of the clause. If "
            "it VERIFIES => SPEC-TOO-WEAK on exactly that sub-domain. (Ports nagini "
            "atk-drop-lower-offset-only.)"
        ),
        "witness": _wit('{ ordering := ["a", "b"], offset := 2, limit := none }',
                        '"h"', "[5]",
                        "open-ended slice at a nonzero offset: the lower position "
                        "condition is required here and this rival omits it"),
    },
    {
        "id": "weak-no-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_NO_CLEAR),
        "refinement": (
            "the faithful real patch builds both per-group position conditions "
            "correctly but never drops the plain offset/limit bounds. The query then "
            "still carries the slice it just re-expressed, so narrowing it to the "
            "supplied parents is again rejected for the same reason as the original "
            "defect; every F2P errors out. Even if it did not, the slice would be "
            "applied twice. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2a) — `result.offset = 0 ∧ result.limit = none` on "
            "any sliced input. This is the one conjunct of the slice arm that is about "
            "the remaining bounds rather than the predicate, and this rival is the "
            "only case that leaves both wrong while the predicate is entirely correct, "
            "so the refutation is attributable to (2a) alone. Witnessed on a CLOSED "
            "slice (nonzero offset AND a limit), where both bounds survive. If it "
            "VERIFIES => SPEC-TOO-WEAK. (Ports nagini atk-no-clear.)"
        ),
        "witness": _wit('{ ordering := ["c"], offset := 3, limit := some 6 }',
                        '"k"', "[1, 2]",
                        "closed slice: the specified result drops both bounds; this "
                        "rival returns them unchanged"),
    },
    {
        "id": "weak-swap-bounds",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_SWAP_BOUNDS),
        "refinement": (
            "the faithful real patch swaps the two position marks: the strict lower "
            "condition is given the requested STOP position and the inclusive upper "
            "condition the requested START position. test_m2m_reverse asks for the "
            "one-element slice from position 1 up to 2, which under the swap keeps "
            "objects whose within-group position is above 2 and at most 1 — an empty "
            "result where a single object was asserted. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2c) at the VALUE level: it pins the lower condition's "
            "argument to `query.offset` and the upper condition's to the limit `h`. "
            "This rival exchanges them, so on any closed slice whose offset and limit "
            "differ both conditions carry the wrong position. Attacks the argument "
            "values of (2c) rather than the presence of its conjuncts, which no other "
            "rival does; witnessed at a closed slice with offset ≠ limit. If it "
            "VERIFIES => SPEC-TOO-WEAK on the bound-value clause. (Ports nagini "
            "atk-swap-bounds.)"
        ),
        "witness": _wit('{ ordering := ["d"], offset := 1, limit := some 4 }',
                        '"m"', "[9]",
                        "closed slice with distinct marks: the two position "
                        "conditions must carry offset and limit respectively, and "
                        "this rival exchanges them"),
    },
    {
        "id": "weak-upper-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_UPPER_ALWAYS),
        "refinement": (
            "the faithful real patch always emits the inclusive upper position "
            "condition, substituting the requested start position when no stop was "
            "asked for. That imposes a spurious finite ceiling on an open-ended "
            "slice: the three F2P that slice from position 1 with no stop would keep "
            "only objects whose position is simultaneously above 1 and at most 1 — "
            "nothing — where the whole tail of each parent's list was asserted. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the limit-dependent tail of clause (2c): the match on "
            "`query.limit` pins the tail to `[]` when no limit is present, so an upper "
            "position condition is FORBIDDEN there. This rival appends one anyway, "
            "making the predicate one conjunct too long on the limit = none "
            "sub-domain. Attacks the upper-condition PRESENCE half of (2c) — the "
            "complement of weak-lower-only-with-limit, which attacks the same "
            "sub-domain from the other side. If it VERIFIES => SPEC-TOO-WEAK. (Ports "
            "nagini atk-upper-always.)"
        ),
        "witness": _wit('{ ordering := ["e"], offset := 4, limit := none }',
                        '"n"', "[2, 8]",
                        "open-ended slice: the limit-dependent tail must be empty and "
                        "this rival appends an upper position condition"),
    },
    {
        "id": "weak-membership-drops-parents",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_MEMBERSHIP_DROPS_PARENTS),
        "refinement": (
            "the faithful real patch narrows the query to an EMPTY parent set rather "
            "than to the parents actually supplied, while getting the slice "
            "translation and the bound dropping right. Every parent's bulk fetch comes "
            "back empty, so each F2P compares an empty attribute against a non-empty "
            "expected slice. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the membership clause's ARGUMENTS: both arms pin the base "
            "conjunct to `PredAtom.memberOf fieldName instances`, i.e. to the "
            "`instances` binder specifically, not merely to the presence of a "
            "membership conjunct. This rival passes the wrong parent list. It is the "
            "NEAR-MISS of weak-drop-membership (the conjunct is present and in the "
            "right position; only its second argument is wrong), so it gets its own "
            "witness — at a limit-only slice with offset 0, a shape no other reject "
            "case probes. If it VERIFIES => SPEC-TOO-WEAK: the spec would pin only "
            "that SOME membership condition exists, and a rival restricting to the "
            "wrong parents would pass. (NEW on this carrier: nagini's membership step "
            "was an opaque effect whose arguments were invisible, so this rival could "
            "not be expressed there.)"
        ),
        "witness": _wit('{ ordering := ["p"], offset := 0, limit := some 3 }',
                        '"q"', "[11]",
                        "limit-only slice: the membership condition must carry the "
                        "supplied parents and this rival supplies none"),
    },
    {
        "id": "weak-ranking-drops-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_RANKING_DROPS_ORDERING),
        "refinement": (
            "the faithful real patch builds the per-group position conditions without "
            "carrying over the query's requested ordering, so within-group positions "
            "are assigned in an unspecified order instead of the asked-for one. "
            "test_reverse_ordering (a reversed default ordering) and test_m2m_reverse "
            "(an explicit ordering) both slice under a specific order, so the wrong "
            "objects land inside the retained position window and the compared "
            "attribute differs from the expected slice. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2c) through the ranking `r`, which the spec fixes as "
            "`{ groupBy := fieldName, ordering := query.ordering }`: both position "
            "conditions must refer to positions in the input's own ordering. This "
            "rival substitutes an empty ordering, so both conjuncts are built over the "
            "wrong ranking. Attacks the `query.ordering` component — the ONLY reject "
            "case that varies it away from the value the spec demands, so without it a "
            "rival mishandling the ordering would go uncaught. Witnessed at an "
            "open-ended slice with a non-empty ordering. If it VERIFIES => "
            "SPEC-TOO-WEAK. (NEW on this carrier: nagini modeled the ranking as an "
            "opaque effect and could not attack it.)"
        ),
        "witness": _wit('{ ordering := ["z"], offset := 5, limit := none }',
                        '"s"', "[6]",
                        "non-empty ordering: the position conditions must be built "
                        "over it and this rival builds them over the empty ordering"),
    },
    {
        "id": "weak-rank-not-per-group",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIV_RANK_NOT_PER_GROUP),
        "refinement": (
            "the faithful real patch computes within-window positions WITHOUT "
            "partitioning by the grouping relation, so the slice is applied to the "
            "flat combined result instead of per parent. That is exactly the "
            "distinction the desired behavior turns on: with a from-position-1 slice, "
            "a single global window keeps one contiguous run of the flat result, so "
            "all but one parent's attribute comes back empty or wrong while each F2P "
            "asserts the slice of EVERY parent's own list. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2c) through the ranking's `groupBy` component, which "
            "the spec pins to `fieldName`: the position conditions must speak about "
            "position WITHIN a parent's group. This rival uses an empty grouping key, "
            "so both conjuncts are built over a ranking that is not per-group. Attacks "
            "the `fieldName` binder in its ranking role (weak-drop-membership and "
            "weak-membership-drops-parents attack its membership role); witnessed at a "
            "closed slice with a two-element ordering, a point no other reject case "
            "probes. If it VERIFIES => SPEC-TOO-WEAK — and this is the weakness that "
            "would matter most, since per-group rather than flat application is the "
            "whole point of the behavior. (NEW on this carrier.)"
        ),
        "witness": _wit('{ ordering := ["u", "v"], offset := 2, limit := some 5 }',
                        '"w"', "[12, 13]",
                        "closed slice: the ranking's grouping key must be the supplied "
                        "relation and this rival leaves it empty"),
    },
]


# The axiom lane belongs to G-AX and is ignored by this gate. There is nothing to
# put here regardless: no callee is consumed as an opaque axiom in this bundle (the
# axioms region is empty and meta.json records G-AX as a skip) — the membership
# condition, the per-group position conditions, the slice-present test and the
# dropping of the bounds are all modeled DEEPLY as transparent data construction.
AXIOM_TESTS = []


# =========================================================================== #
# AUDIT RECORD (independent adversarial audit of the ported battery)           #
# =========================================================================== #
# The port recorded G-PBT=SOUND on 12 cases. Re-derived here with real builds;
# the SOUND was EARNED on all 12, and two lane-level defects were repaired.
#
# ATTACK A (statement integrity) — CLEAN. Every case's `post-conditions` region,
# `pure` region and `theorem correct_restrictPrefetch` statement were extracted
# from the generated module and compared to the frozen file: all 12 identical
# (frozen statement sha256 prefix acf47f31b086). Nothing reformatted, nothing
# logically restated.
#
# ATTACK B / B′ (witness discrimination, re-derived) — CLEAN on all 10 reject
# cases. Each witness was rebuilt independently through the real harness
# (`pbt_witness.witness_file`), against the rival and against the frozen
# solution: rival exit 0, gold exit 1, ten for ten. No witness binds anything, so
# `consistency_probe` is None for all ten — matching the gate — and there are no
# hypotheses that could be inconsistent. Every gold-side failure is
# `Tactic `decide` proved that the proposition ¬... is false`, i.e. a plain kernel
# EVALUATION of the concrete claim, not a missing identifier, type error,
# unfolding failure or timeout. The FORGERY test was run anyway on all ten rather
# than argued: a second gold-side file differing ONLY in dropping the `¬` (thereby
# claiming gold is CORRECT at that input) SUCCEEDS, exit 0, with an empty error
# log — so gold's exit code tracks the claim in both directions and carries real
# information. No case is hollow.
#
# ATTACK C (is the rival wrong, or just different?) — all 10 differ from the
# frozen impl OBSERVABLY, and each witness is the machine-checked proof of it: a
# `decide` refutation at a literal input cannot elaborate against a rival that is
# definitionally equal to gold. No vacuous rival; nothing dropped.
#
# ATTACK D (SPEC-TOO-WEAK probe) — NO HOLE. Seven NEW wrong impls the battery did
# not contain were written and built, aimed at what the existing rivals leave
# unattacked: a wrong slice TEST (only a present limit counts as a slice, so a
# nonzero start position is ignored); the upper mark read as a COUNT rather than
# an absolute position (offset + h); an off-by-one on the lower mark; a PARTIAL
# clear (start position dropped, upper bound survives — half of clause 2a); the
# membership conjunct emitted LAST instead of first (conjunct order); the two
# position CONSTRUCTORS exchanged while keeping the marks; and the ranking's
# grouping key taken from the ordering's head instead of the relation. All seven
# were REJECTED (full-variant build exit 1) and all seven carry a discriminating
# `decide` witness that elaborates against them (exit 0). The spec has no hole at
# any of those points.
#
# ATTACK E (SPEC-TOO-STRONG probe) — NO HOLE. Three NEW correct reshapes were
# written and honestly re-proven: a fully PURE impl with no mutable state (built
# by `::` from pre-computed `let`s), a variant branching on the two `isSliced`
# COMPONENTS separately rather than on the fold, and one accumulating the slice
# tail in a separate local appended once. All three VERIFY (exit 0). The first is
# now shipped as `pos-pure-no-mutation`, since it is the reshape the two ported
# positives did not cover.
#
# ATTACK F (omission re-derivation) — one real defect, now FIXED. Of the nagini
# sibling's 9 SPEC cases, 8 port and all 8 are present. The dropped one is
# `admiss-sliced-input`, and the recorded reason ("the lean obligation has no
# precondition, so the lane is N/A") is NOT a demonstration of vacuity: the
# analogue on a total carrier is the obligation being unsatisfiable at an
# F2P-shaped input. Landed as `admiss-f2p-slice-shapes`, with its `have`s
# measured load-bearing against a wrong impl. The FRAME/PERMISSION lane is
# genuinely inexpressible (Lean has no aliasing and no fractional permission, and
# nagini's own analogue was the capability token, which this carrier replaces with
# directly observable data) — that omission stands.
#
# ATTACK F′ (divergence lane) — KNOWN HOLE, re-measured, disposition corrected in
# the header above. The port's claim that a diverging impl "cannot be written" is
# false; what is missing is refutability, not expressibility.
#
# ATTACK G (coverage) — the reporter's only finding was the missing admissibility
# lane, which this audit fixed. Binder variation was checked for MEANINGFULNESS
# rather than spelling: across the 10 reject witnesses `fieldName` takes 10
# distinct values, `instances` varies in both length and content (including the
# empty-parent near-miss), and `query` covers all four slice shapes — unsliced,
# offset-only, limit-only-at-offset-0, and closed with distinct marks — each of
# which changes which arm and which clause of the postcondition decides the case.
#
# FROZEN SPEC — no defect found; no escalation. `Solution.lean`, `meta.json` and
# `instance.json` were not modified.
