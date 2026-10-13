# properties.py — G-PBT falsification battery for django__django-12050 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against THIS backend's carrier. Each SPEC_TESTS case is a
# FULL Solution.lean variant sharing the FROZEN spec byte-for-byte — only the impl
# region, and (for a positive that honestly reproves) the proof body, is edited — so
# markers.same_spec holds by construction and every rejection is attributable to the
# postcondition rather than to a tampered spec. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so a rejection is never credited to a tactic script that merely
# stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
#   implementation_resolveLookupValue : LV → LV
#   problem_spec_resolveLookupValue (value : LV) (result : LV) : Prop :=
#     result = resolveSpec value
#   Single obligation, single input binder `value : LV`. `LV` is a finite tree with
#   FOUR constructors — `expr` (a value that resolves itself through a context
#   resolver), `plain` (a scalar leaf), `lst` (an ordered collection of one kind),
#   `tup` (an ordered collection of the other kind). The postcondition is one
#   equation, but `resolveSpec` is a transparent recursion, so that equation carries
#   several INDEPENDENT top-level facts, one per constructor arm — and each arm is a
#   separate clause a rival can attack:
#     (a) `expr e ↦ resolveExpression e`   — an expression is resolved, not returned
#         verbatim (the sole opaque term in the whole carrier);
#     (b) `plain n ↦ plain n`             — a scalar leaf is returned unchanged, and
#         in particular is NOT lifted into a collection;
#     (c) `lst xs ↦ lst (xs.map resolveSpec)` — a collection of the first kind stays
#         a collection OF THAT SAME KIND, with the same arity, the same order, and
#         each entry resolved by the very same rule (so recursion re-enters the
#         collection arm for a nested entry);
#     (d) `tup xs ↦ tup (xs.map resolveSpec)` — the mirror fact for the other kind.
#   Clause (c)'s "same kind" half is the load-bearing one: it is the single fact the
#   frozen Solution_prepatch.lean violates, and the one the F2P assertion observes.
#
# CARRIER NOTE (why the cases look different from nagini's)
#   The nagini sibling abstracted this behavior to a FLAT container — a `kind` tag in
#   {0,1} plus a `List[int]` of opaque item identities, with the per-item rule an
#   uninterpretable @Pure primitive. This backend models the SAME behavior as a
#   RECURSIVE tree whose element rule is the function itself, so:
#     * nagini's `kind` field becomes the CHOICE OF CONSTRUCTOR (`lst` vs `tup`), and
#       nagini's `Result().kind == value.kind` clause becomes clauses (c)/(d);
#     * nagini's per-item `normalise_item` clause becomes the recursive `resolveSpec`
#       call inside the `map`, which is transparent here — so the wrong-value attacks
#       that nagini could only state over an opaque primitive can be stated at
#       LITERAL inputs, with no conditioning at all;
#     * two clauses have NO nagini counterpart at all, because nagini's flat carrier
#       could not express them: the `plain`/`expr` dispatch arms ((a),(b)), and the
#       distinction between a SHALLOW single pass over the entries and a RECURSIVE
#       one. Rivals were authored for both — see `assessment`.
#   Only `resolveExpression` is opaque. Where a rival is wrong exactly on the
#   expression arm, its witness CONDITIONS on that term (one weak hypothesis:
#   resolving a given expression identity does not give back the unresolved value)
#   rather than trying to compute it. One hypothesis per witness, about one term, so
#   the binders are trivially jointly satisfiable.
#
# LANES THAT DO NOT PORT (stated here, argued in `assessment`)
#   * FRAME/PERMISSION-MUTATION — nagini's MANDATORY #1 class (two cases: write the
#     read-only input's items, write its kind tag). Lean is referentially
#     transparent: there is no aliasing and no fractional permission, the input is a
#     value, and "mutate the caller's object to satisfy the postcondition" is not
#     expressible. The class is genuinely VACUOUS here, not a spec hole.
#   * ADMISSIBILITY — LANDED BY AUDIT; the reason first recorded here for dropping
#     it was wrong. nagini's admiss-f2p-shaped-input defended a half-permission
#     precondition, and it is true that the lean obligation is `∀ (value : LV),
#     problem_spec … value (implementation … value)` with NO precondition
#     hypothesis, so no HYPOTHESIS can be over-strong. But that is not the right
#     test on a total carrier: the analogue is the obligation being UNSATISFIABLE
#     at exactly an F2P-shaped input, which a positive that discharges the spec
#     predicate at that concrete input — by EVALUATION, as a `have`, before closing
#     the frozen obligation verbatim — tests directly. See `adm-f2p-shaped-input`.
#   * DIVERGENCE / NON-TERMINATION — no such case in the nagini sibling, and on lean
#     the class is vacuous regardless: `implementation_resolveLookupValue` is a total
#     Lean `def` (its recursion is accepted by the termination checker), so a
#     diverging implementation cannot be written at all. Contrast velvet under
#     `loom.semantics.termination "partial"`, where it would be a real spec hole
#     (the corpus-wide termination-semantics finding).
#   * AXIOM_TESTS — the axiom lane is G-AX's job; this gate ignores them. There is no
#     consumed axiom here anyway (the context resolver is `opaque` with no `_prop`).
#
# NAGINI'S BOTH-DIRECTIONS COERCION (uniq-flip-kind) — DROPPED AS SUBSUMED, measured.
#   nagini carried a third coercion rival, `Iterable(1 - value.kind)`, which inverts
#   the container kind for EVERY input. Its lean transliteration is "swap both return
#   lines", and it is expressible here — it was dropped because it is redundant, not
#   because it could not be written, and the redundancy was checked rather than
#   assumed: the shipped weak-coerce-first-kind witness (`LV.lst [LV.plain 7]`) and
#   the shipped weak-coerce-second-kind witness (`LV.tup [LV.plain 7]`) were each
#   rebuilt against that both-directions impl and BOTH elaborate against it (exit 0).
#   So it adds no input at which the battery does not already refute, and it is
#   strictly easier to refute than either one-directional rival (it is wrong on both
#   sub-domains where each of those is wrong on one). The one-directional pair is the
#   stronger test and is what ships.
from pathlib import Path

INSTANCE = "django__django-12050"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it names and is unique in the
# frozen file, so a `_swap` can never reach the spec view.
# ---------------------------------------------------------------------------

# The whole impl region body (inside impl-start / impl-end).
_IMPL = """def implementation_resolveLookupValue : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.lst resolved
  | LV.tup xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.tup resolved"""

# The first-kind collection arm on its own.
_ARM_LST = """  | LV.lst xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.lst resolved"""

# The two `return` lines that name the emitted collection kind.
_RET_LST = "      return LV.lst resolved"
_RET_TUP = "      return LV.tup resolved"

# The two non-collection dispatch arms. Their TEXT alone is not unique — the spec's
# own transparent recursion spells the same two arms — so the anchor carries the
# following line, which only the impl has, keeping every edit inside impl-start /
# impl-end.
_ARM_HEAD = ("  | LV.expr e  => resolveExpression e\n"
             "  | LV.plain n => LV.plain n\n"
             "  | LV.lst xs  => Id.run do")
_ARM_EXPR = "  | LV.expr e  => resolveExpression e"
_ARM_PLAIN = "  | LV.plain n => LV.plain n"

# The per-entry step inside the first-kind collection arm.
_STEP = "resolved := resolved ++ [implementation_resolveLookupValue sub]"

for _a in (_IMPL, _ARM_LST, _RET_LST, _RET_TUP, _ARM_HEAD):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"impl anchor drifted: {_a[:48]!r}")
if _BASE.count(_STEP) != 2:      # once per collection arm
    raise AssertionError("per-entry step anchor drifted")

# The frozen tactic body (inside proof-start / proof-end, after the byte-identical
# `theorem correct_resolveLookupValue` STATEMENT, which no case may touch).
_PROOF = """  intro value
  unfold problem_spec_resolveLookupValue
  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
  -- element-wise IH for the collection cases.
  refine @LV.rec
    (fun v => implementation_resolveLookupValue v = resolveSpec v)
    (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
    ?_ ?_ ?_ ?_ ?_ ?_ value
  · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec,
      resolveLookupValue_loop_map, List.nil_append]
    rw [ih]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec,
      resolveLookupValue_loop_map, List.nil_append]
    rw [ih]
  · rfl
  · intro head tail ih_head ih_tail
    simp only [List.map_cons, ih_head, ih_tail]"""
if _BASE.count(_PROOF) != 1:
    raise AssertionError("proof body anchor drifted")


# ===========================================================================
# WITNESS BUILDERS
#
# A reject case's `witness` is checked in a file whose proof obligations have been
# removed, so no tactic script can interfere. It must (1) elaborate against the
# rival and (2) FAIL on the frozen solution. Both halves were run by hand with
# scripts/lean_verify.sh for every case below before shipping.
#
# The impl's collection arms are `Id.run do … for … mut …`, which neither `decide`
# (no Decidable instance for an LV equation) nor `rfl` reduces; `simp` with the
# monad-run lemmas does. Hence the single tactic line used everywhere.
# ===========================================================================

_SIMP = "  simp [implementation_resolveLookupValue, resolveSpec, Id.run, bind, pure]"


def _wit(value, note, extra="", tail=""):
    """`¬ problem_spec … v (implementation … v)` at the concrete input `value`.

    `extra` adds a hypothesis binder for the ONE opaque term in the carrier, used
    only by the rivals that are wrong exactly on the expression arm; `tail` closes
    the residual goal that hypothesis leaves (an orientation flip)."""
    return (f"-- {note}\n"
            f"example {extra}: ¬ problem_spec_resolveLookupValue ({value})\n"
            f"    (implementation_resolveLookupValue ({value})) := by\n"
            f"  unfold problem_spec_resolveLookupValue\n"
            f"{_SIMP}\n{tail}").rstrip() + "\n"


# The one hypothesis any conditioned witness needs: resolving the expression
# identity 4 does not hand back the unresolved value itself. Weak (it merely says
# the resolver is not the identity at ONE point), satisfiable (nothing in the
# frozen file constrains the opaque resolver at all), and used at most once per
# witness — so the gate's consistency probe cannot derive `False` from it.
_H4 = "(h : resolveExpression 4 ≠ LV.expr 4) "

# The orientation flip is wrapped in `try` DELIBERATELY, and the reason is about
# what the gold-side build is allowed to fail WITH, not about whether it fails.
#
# The two-build check reads "the witness's build against the frozen solution
# failed" as "the frozen solution satisfies the spec at this input". That
# inference is only worth anything if the failure was the goal being FALSE there.
# With a bare `exact fun hh => h hh.symm`, gold fails one step too early: on gold
# `simp` discharges the equation outright and leaves `⊢ False`, so the tail's
# `fun hh => …` has nothing to introduce and the error reported is
# `Invalid field notation: Type of hh is not known; cannot resolve field symm` —
# an ELABORATION error about the tactic, carrying no information about the spec.
# That is the "fails on gold for a syntactic reason" shape, and the gate cannot
# tell it from a real refutation.
#
# `try` lets the residual goal stand instead of erroring on it, so gold now fails
# as `unsolved goals ⊢ False` — the claim reduced, and it is false of gold. The
# rival half is unaffected: there `simp` leaves the flipped inequation and the
# `exact` still closes it, so the rival continues to elaborate. Measured both
# ways for all three conditioned witnesses.
_FLIP = "  try exact fun hh => h hh.symm"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# Each keeps the `theorem correct_resolveLookupValue` STATEMENT byte-identical and
# introduces no axiom / lemma / sorry; where the reshape breaks the frozen script,
# the proof is honestly RE-CLOSED for the new shape.
# ===========================================================================

# pos-arm-reorder: the four dispatch arms are permuted (scalar leaf first, the two
# collection arms swapped). Pattern-match arms over distinct constructors are
# mutually exclusive, so the function computed is identical on every input; only the
# textual order changes. The frozen tactic script still closes it unchanged (it
# names arms by constructor, not by position), so this positive touches ONLY the
# impl region.
_POS_REORDER = _swap(_BASE, _IMPL, """def implementation_resolveLookupValue : LV → LV
  | LV.plain n => LV.plain n
  | LV.expr e  => resolveExpression e
  | LV.tup xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.tup resolved
  | LV.lst xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.lst resolved""")

# pos-map-shape: a structurally DIFFERENT correct impl — the accumulator loop that
# rebuilds each collection is replaced by a direct element-wise traversal. Same
# entries, same order, same arity, same emitted kind; a different program shape (the
# shape a functional rendering of the same fix would take). The frozen script's
# collection cases go through the loop-to-map bridge lemma, which no longer applies,
# so the proof is re-closed with the same induction minus that rewrite. If a
# faithful, structurally-different correct impl could not verify => SPEC-TOO-STRONG.
_POS_MAP = _swap(
    _swap(_BASE, _IMPL, """def implementation_resolveLookupValue : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => LV.lst (xs.map implementation_resolveLookupValue)
  | LV.tup xs  => LV.tup (xs.map implementation_resolveLookupValue)"""),
    _PROOF,
    """  intro value
  unfold problem_spec_resolveLookupValue
  refine @LV.rec
    (fun v => implementation_resolveLookupValue v = resolveSpec v)
    (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
    ?_ ?_ ?_ ?_ ?_ ?_ value
  · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec]
    rw [ih]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec]
    rw [ih]
  · rfl
  · intro head tail ih_head ih_tail
    simp only [List.map_cons, ih_head, ih_tail]""")

# pos-direct: the cheapest HONEST impl — return the canonical resolution directly.
# This is NOT an ungrounded-oracle echo: the postcondition's right-hand side is a
# transparent recursion over the ACTUAL input tree, not an axiomatized answer key,
# and its only opaque leaf is the context resolver the frozen impl invokes
# identically. So there is no wrong value to echo — any impl satisfying the equation
# has performed the same traversal. Must verify (the postcondition IS this
# equation); else SPEC-TOO-STRONG. Proof collapses to `rfl` after unfolding.
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL,
          "def implementation_resolveLookupValue : LV → LV := resolveSpec"),
    _PROOF,
    "  intro value\n"
    "  unfold problem_spec_resolveLookupValue implementation_resolveLookupValue\n"
    "  rfl")


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly, edits only the impl region, and leaves the frozen tactic body in
# place (it cannot close against a wrong impl; the gate reads the WITNESS, not that
# build, for the attribution).
# ===========================================================================

# Clause (c), the load-bearing half: emit the OTHER collection kind for a
# first-kind input. This is the modeled defect itself.
_RIV_COERCE_LST = _swap(_BASE, _RET_LST, _RET_TUP)

# Clause (d): the mirror coercion — a second-kind input emitted as the first kind.
_RIV_COERCE_TUP = _swap(_BASE, _RET_TUP, _RET_LST)

# Clause (c), arity: the rebuilt collection is short by its last entry.
_RIV_DROP_LAST = _swap(_BASE, _ARM_LST,
                       _ARM_LST.replace(_RET_LST, _RET_LST + ".dropLast"))

# Clause (c), per-entry: every position carries the FIRST entry's resolution.
_RIV_BROADCAST = _swap(
    _BASE, _ARM_LST,
    _ARM_LST.replace(
        _RET_LST,
        "      return LV.lst (resolved.map (fun _ => resolved.headD (LV.plain 0)))"))

# Clause (c), order: the entries are emitted in the opposite order.
_RIV_REVERSE = _swap(_BASE, _ARM_LST,
                     _ARM_LST.replace(_RET_LST, _RET_LST + ".reverse"))

# Clause (c), per-entry resolution: each entry is copied verbatim instead of being
# resolved. Wrong exactly where an entry has something to resolve.
_RIV_ENTRY_RAW = _swap(_BASE, _ARM_LST,
                       _ARM_LST.replace(_STEP, "resolved := resolved ++ [sub]"))

# Clause (c), RECURSION: entries are resolved by a SHALLOW single pass — an entry is
# resolved only if it is itself an expression; an entry that is a nested collection
# is copied verbatim instead of re-entering the collection rule. No nagini
# counterpart (its flat carrier had no nested entries).
_RIV_SHALLOW = _swap(_BASE, _ARM_LST, _ARM_LST.replace(_STEP, """resolved := resolved ++ [(match sub with
          | LV.expr e => resolveExpression e
          | other     => other)]"""))

# Clause (a): an expression is returned unresolved instead of being resolved.
_RIV_EXPR_RAW = _swap(_BASE, _ARM_HEAD,
                      _ARM_HEAD.replace(_ARM_EXPR, "  | LV.expr e  => LV.expr e"))

# Clause (b): a scalar leaf is lifted into a singleton collection instead of being
# returned unchanged.
_RIV_PLAIN_WRAP = _swap(
    _BASE, _ARM_HEAD,
    _ARM_HEAD.replace(_ARM_PLAIN, "  | LV.plain n => LV.lst [LV.plain n]"))

# Clause (d), arity — the SECOND-kind mirror of the arity attack. Every other
# rival that attacks a collection's INTERNALS (arity, order, per-entry rule,
# recursion) edits `_ARM_LST` only, so clause (d) was defended for its emitted
# kind alone and its arity/order/entry halves rested on the reader's assumption
# that the two arms are symmetric. They are separate arms of a `match`: nothing
# in the spec forces an impl that gets the first kind right to get the second
# kind right, so the assumption needs a rival of its own.
_RIV_TUP_DROP_LAST = _swap(_BASE, _RET_TUP, _RET_TUP + ".dropLast")

# Clause (a), the resolved IDENTITY: the expression arm calls the resolver, but on
# the WRONG expression identity (the neighbouring one). Every other rival on this
# arm either resolves the right identity or does not resolve at all, so what was
# defended was "the resolver is invoked", not "it is invoked on THIS input" — a
# rival that resolves a different expression than the one it was handed satisfies
# the former and violates the spec.
_RIV_EXPR_SHIFT = _swap(_BASE, _ARM_HEAD,
                        _ARM_HEAD.replace(_ARM_EXPR,
                                          "  | LV.expr e  => resolveExpression (e + 1)"))

# The SECOND-kind collection arm on its own — the mirror of `_ARM_LST`. Needed by
# the clause-(d) rivals an audit added: every collection-INTERNALS rival the port
# shipped edits `_ARM_LST`, so (d) was probed for its emitted kind and nothing else.
_ARM_TUP = """  | LV.tup xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.tup resolved"""
if _BASE.count(_ARM_TUP) != 1:
    raise AssertionError("second-kind arm anchor drifted")

# Clause (d), ORDER: the second kind's entries are emitted in the opposite order.
_RIV_TUP_REVERSE = _swap(_BASE, _RET_TUP, _RET_TUP + ".reverse")

# Clause (d), PER-ENTRY: the second kind's entries are copied verbatim instead of
# being resolved.
_RIV_TUP_ENTRY_RAW = _swap(_BASE, _ARM_TUP,
                           _ARM_TUP.replace(_STEP, "resolved := resolved ++ [sub]"))

# Clause (b), the leaf's IDENTITY: the scalar arm returns a leaf — just not the
# one it was handed. weak-scalar-wrapped attacks the arm by changing the result's
# KIND, so what was defended was "a scalar leaf comes back as a scalar leaf", not
# "as THIS scalar leaf"; the payload `n` was pinned by no witness.
_RIV_PLAIN_SHIFT = _swap(
    _BASE, _ARM_HEAD,
    _ARM_HEAD.replace(_ARM_PLAIN, "  | LV.plain n => LV.plain (n + 1)"))

# ---------------------------------------------------------------------------
# ADMISSIBILITY (landed by audit). Prefix the frozen tactic body with a `have`
# that discharges the spec predicate at a concrete F2P-shaped input BY EVALUATION,
# then close the frozen obligation with the frozen script verbatim. Nothing is
# assumed: no new declaration, no axiom, no `sorry`, and the
# `theorem correct_resolveLookupValue` STATEMENT stays byte-identical (only the
# tactic body is prefixed, which `variant_scope` permits).
#
# The input is the shape the sole F2P assertion is stated over: a TOP-LEVEL
# collection of the first kind holding two scalar leaves. That drives the `have`
# through the load-bearing arm — clause (c), same-kind reconstruction over a
# multi-entry collection — which is where an unsatisfiable obligation would show
# up first.
#
# The `have` is INFORMATIVE, not a tautology `simp` would close regardless:
# audited by control, the same `have` shape asserting the spec of a WRONG result
# (the other collection kind in place of the implementation's) does NOT close,
# failing with `unsolved goals ⊢ False`.
_ADM_F2P = "LV.lst [LV.plain 1, LV.plain 2]"
_ADM = _swap(_BASE, _PROOF, f"""  -- ADMISSIBILITY: the frozen obligation is SATISFIABLE at an F2P-shaped input
  -- (a top-level first-kind collection of two scalar leaves), discharged here by
  -- EVALUATION before the frozen obligation is closed verbatim below.
  have adm : problem_spec_resolveLookupValue ({_ADM_F2P})
      (implementation_resolveLookupValue ({_ADM_F2P})) := by
    unfold problem_spec_resolveLookupValue
    simp [implementation_resolveLookupValue, resolveSpec, Id.run, bind, pure]
{_PROOF}""")

# The hypothesis the identity rival's witness needs: the resolver does not take
# two DISTINCT expression identities to the same value. Weak (it separates the
# resolver at one pair of points), satisfiable for the same reason `_H4` is —
# nothing in the frozen file constrains the opaque resolver anywhere.
_H54 = "(h : resolveExpression 5 ≠ resolveExpression 4) "
_EXACT_H = "  try exact h"


SPEC_TESTS = [
    # ------------------------------------------------------------------
    # positive controls (must VERIFY)
    # ------------------------------------------------------------------
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the four dispatch arms are "
            "permuted (scalar leaf first, the two collection arms swapped). The arms "
            "match distinct constructors and so are mutually exclusive — the function "
            "computed is identical at every input, only the textual order differs, "
            "which is a shape a faithful patch could equally take. The frozen "
            "`theorem correct_resolveLookupValue` statement is untouched and the "
            "frozen tactic body still closes it (it names arms by constructor, not "
            "position), so this case edits ONLY the impl region. If it is rejected => "
            "SPEC-TOO-STRONG (the postcondition would be over-fit to one arm order)."
        ),
    },
    {
        "id": "pos-map-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": (
            "a genuinely different program shape that is still CORRECT: the "
            "accumulate-into-a-local traversal that rebuilds each collection is "
            "replaced by a direct element-wise traversal. Same emitted kind, same "
            "arity, same order, same per-entry recursion — the functional rendering "
            "of the same behavior. The frozen script's collection cases route through "
            "the accumulator-to-traversal bridge lemma, which no longer applies, so "
            "the proof is HONESTLY re-closed: same structural induction, same list "
            "motive, minus that one rewrite. The theorem STATEMENT is byte-identical "
            "and no axiom / lemma / sorry / native_decide is introduced. If this is "
            "rejected => SPEC-TOO-STRONG: the spec would be pinning the loop's SHAPE "
            "rather than the value it computes."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the cheapest HONEST impl — return the canonical resolution of the input "
            "directly. Not an ungrounded-oracle echo: the postcondition's right-hand "
            "side is a transparent recursion over the ACTUAL input tree (not an "
            "axiomatized answer key), and its single opaque leaf is the context "
            "resolver, which the frozen impl invokes identically. There is therefore "
            "no wrong value available to echo — any impl satisfying the equation has "
            "performed the same traversal, which is exactly why every rival below "
            "are refutable. Must verify (the postcondition IS this equation); else "
            "SPEC-TOO-STRONG. Proof collapses to `rfl` after unfolding, statement "
            "byte-identical."
        ),
    },

    # ------------------------------------------------------------------
    # admissibility (must VERIFY) — landed by audit
    # ------------------------------------------------------------------
    {
        "id": "adm-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "the frozen obligation is SATISFIABLE at an F2P-shaped input. This lane "
            "was first dropped here on the ground that the lean obligation carries no "
            "precondition hypothesis, so nothing could be PRECOND-TOO-STRONG; that is "
            "true of the hypothesis and beside the point on a total carrier, where the "
            "analogue is the obligation being UNSATISFIABLE at exactly an F2P-shaped "
            "input. This case tests that directly: it discharges "
            "`problem_spec_resolveLookupValue` at a concrete top-level first-kind "
            "collection of two scalar leaves — the shape the sole FAIL_TO_PASS "
            "assertion is stated over — by EVALUATION, as a `have`, and only then "
            "closes the frozen obligation with the frozen tactic body verbatim. The "
            "`have` goes through the load-bearing arm (clause (c): same-kind "
            "reconstruction over a multi-entry collection), which is where an "
            "unsatisfiable obligation would surface first. It is INFORMATIVE rather "
            "than a tautology `simp` closes regardless — audited by control: the same "
            "`have` asserting the spec of a WRONG result (the other collection kind) "
            "does NOT close, failing `unsolved goals ⊢ False`. Statement "
            "byte-identical, no axiom / lemma / sorry / native_decide. If this is "
            "rejected => PRECOND-TOO-STRONG: the spec would be unsatisfiable at the "
            "very input the change is judged by, and every rejection below would "
            "attest to nothing but an inconsistent postcondition."
        ),
    },

    # ------------------------------------------------------------------
    # uniqueness rivals (must be REJECTED)
    # ------------------------------------------------------------------
    {
        "id": "weak-coerce-first-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_COERCE_LST,
        "refinement": (
            "THE modeled defect: a collection of the first kind is rebuilt as a "
            "collection of the SECOND kind, so the returned container's kind no "
            "longer matches the input's. This is precisely the behavior the frozen "
            "Solution_prepatch.lean reproduces and G-DIFF flags. Its faithful real "
            "counterpart is the pre-change collection branch, which reconstructs the "
            "entries into a fixed container kind rather than the input's own; the "
            "sole FAIL_TO_PASS assertion pins the rendered right-hand side of an "
            "exact-match lookup built from a first-kind collection literal, and a "
            "second-kind container renders differently, so the assertEqual fails. A "
            "patch behaving this way is exactly the un-patched code and does NOT "
            "resolve — a verifying rival here would be a true verify-does-not-imply-"
            "resolve break."
        ),
        "rationale": (
            "REJECTED by clause (c) of the postcondition: `resolveSpec (LV.lst xs) = "
            "LV.lst (…)`, so the result's constructor is pinned to the input's. The "
            "rival returns `LV.tup (…)`, a distinct constructor, so the equation "
            "fails for EVERY first-kind input. Attacks the same-kind half of clause "
            "(c); binder `value` is probed at a first-kind collection. If it VERIFIES "
            "=> SPEC-TOO-WEAK, and the spec would not see the modeled bug at all."
        ),
        # `LV.lst [LV.plain 7]`: gold => lst [plain 7]; rival => tup [plain 7].
        "witness": _wit("LV.lst [LV.plain 7]",
                        "first-kind collection emitted as the second kind"),
    },
    {
        "id": "weak-coerce-second-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_COERCE_TUP,
        "refinement": (
            "the mirror coercion: a SECOND-kind collection is rebuilt as a first-kind "
            "one. The problem statement demands the returned iterable type MATCH the "
            "input iterable type, which is a requirement in BOTH directions — field "
            "types whose lookups compare against the input container type break "
            "either way round. A patch that always emitted the first kind would fix "
            "the reported direction and break the other, so it does not implement the "
            "required behavior and would regress the second-kind cases the existing "
            "suite already covers. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (d): `resolveSpec (LV.tup xs) = LV.tup (…)`. The "
            "rival returns `LV.lst (…)` for a second-kind input, a distinct "
            "constructor, so the equation fails. This is a DIFFERENT sub-domain from "
            "weak-coerce-first-kind (the two rivals agree with gold on each other's "
            "witness input), which is why it carries its own witness at a second-kind "
            "collection rather than sharing one. If it VERIFIES => SPEC-TOO-WEAK: "
            "clause (d) would be hollow and only one direction of the type-matching "
            "requirement defended."
        ),
        # `LV.tup [LV.plain 7]`: gold => tup [plain 7]; rival => lst [plain 7].
        "witness": _wit("LV.tup [LV.plain 7]",
                        "second-kind collection emitted as the first kind"),
    },
    {
        "id": "weak-drop-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_LAST,
        "refinement": (
            "the rebuilt collection is short by its final entry. A patch whose "
            "reconstruction lost the last element would return a shorter iterable "
            "than it was given: the F2P assertion's two-element collection literal "
            "would render as a one-element container, so the compared right-hand "
            "side differs and the assertion fails; more broadly any multi-element "
            "lookup would silently drop a value. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ARITY half of clause (c): `resolveSpec (LV.lst xs) = "
            "LV.lst (xs.map resolveSpec)` fixes the entry count to the input's, and "
            "the rival emits one fewer for any non-empty collection. Attacks arity "
            "independently of kind (the constructor is still right). Binder `value` "
            "probed at a one-entry first-kind collection — the smallest input where "
            "arity is observable. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # `LV.lst [LV.plain 7]`: gold => lst [plain 7]; rival => lst [].
        "witness": _wit("LV.lst [LV.plain 7]",
                        "final entry dropped from the rebuilt collection"),
    },
    {
        "id": "weak-broadcast-first-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BROADCAST,
        "refinement": (
            "every position of the rebuilt collection carries the FIRST entry's "
            "resolution. A patch that resolved one sub-value and repeated it across "
            "the collection would produce a wrong right-hand side for any lookup with "
            "two or more distinct entries (a two-element collection would come back "
            "with its first element twice), failing both the F2P comparison and the "
            "existing multi-element lookup cases. Does NOT resolve. Note it is "
            "CORRECT at position 0 and at every single-entry input, so it is a "
            "partial-domain rival: it needs a witness with at least two DISTINCT "
            "entries, which is why its probed input differs from the arity rival's."
        ),
        "rationale": (
            "REJECTED by the PER-ENTRY half of clause (c): entry k of the result must "
            "be the resolution of entry k of the input, and the rival puts entry 0's "
            "resolution everywhere. Attacks the element-wise correspondence "
            "independently of kind and arity (both still right). Binder `value` "
            "probed at a two-entry collection with distinct entries — the smallest "
            "input outside this rival's correct sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # `LV.lst [LV.plain 1, LV.plain 2]`: gold => [plain 1, plain 2];
        # rival => [plain 1, plain 1].
        "witness": _wit("LV.lst [LV.plain 1, LV.plain 2]",
                        "first entry's resolution broadcast over every position"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "the rebuilt collection carries the right entries with the right arity "
            "and the right kind, in the OPPOSITE order. A patch that reversed the "
            "iteration would render an ordered lookup value back-to-front: the F2P "
            "assertion compares the rendered right-hand side of a collection literal "
            "whose order is part of that rendering, and any ordered-container lookup "
            "would be built against the wrong sequence. Does NOT resolve. Correct on "
            "collections of fewer than two entries and on palindromic ones, so it is "
            "a partial-domain rival distinct from the broadcast one: the broadcast "
            "rival agrees with gold at position 0 while this one does not, and this "
            "one agrees with gold on the entry MULTISET while the broadcast one does "
            "not — so each is probed at its own input."
        ),
        "rationale": (
            "REJECTED by the ORDER half of clause (c): the result's entry list is "
            "`xs.map resolveSpec`, which fixes the position of each entry, and the "
            "rival emits its reverse. Attacks ordering independently of kind, arity "
            "and the per-entry rule (all three still right), which is the clause a "
            "spec stated only as a set/multiset relation would leave undefended. "
            "Binder `value` probed at a three-entry collection with pairwise-distinct "
            "entries — a length where reversal is observable and not a coincidence of "
            "a two-element swap. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # `LV.lst [LV.plain 1, LV.plain 2, LV.plain 3]`: gold => 1,2,3;
        # rival => 3,2,1.
        "witness": _wit("LV.lst [LV.plain 1, LV.plain 2, LV.plain 3]",
                        "entries emitted in the opposite order"),
    },
    {
        "id": "weak-entry-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ENTRY_RAW,
        "refinement": (
            "each entry is copied VERBATIM into the rebuilt collection instead of "
            "being resolved. The kind, the arity and the order are all right; only "
            "the per-entry resolution is skipped. Its faithful real counterpart is a "
            "reconstruction that rebuilds the container of the same type but no "
            "longer resolves the sub-values — the entries of a collection may "
            "themselves need resolving, so such a patch would leave an unresolved "
            "sub-value in the lookup's right-hand side and break every lookup whose "
            "entries are resolvable. Does NOT resolve (and it regresses the existing "
            "cases the change that introduced the modeled defect was written for)."
        ),
        "rationale": (
            "REJECTED by the PER-ENTRY half of clause (c) composed with clause (a): "
            "entry k of the result must be `resolveSpec` of entry k, and for an entry "
            "that is an expression that is the resolver's value, not the entry "
            "itself. The witness CONDITIONS on the one opaque term in the carrier "
            "rather than computing it: assuming only that resolving expression "
            "identity 4 does not hand back the unresolved value, the rival's answer "
            "differs from the spec's at a one-entry collection holding that "
            "expression. One hypothesis, about one term, nothing in the frozen file "
            "constrains the resolver — so the binders are jointly satisfiable and the "
            "refutation is not vacuous. If it VERIFIES => SPEC-TOO-WEAK: the "
            "postcondition would pin only the container and not its contents."
        ),
        # `LV.lst [LV.expr 4]`: gold => lst [resolveExpression 4];
        # rival => lst [LV.expr 4]. Distinct under `h`.
        "witness": _wit("LV.lst [LV.expr 4]",
                        "entries copied verbatim instead of resolved",
                        extra=_H4, tail=_FLIP),
    },
    {
        "id": "weak-shallow-single-pass",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SHALLOW,
        "refinement": (
            "entries are resolved by a SHALLOW single pass: an entry that is itself "
            "an expression is resolved, and any other entry — including one that is "
            "itself a collection — is copied verbatim rather than re-entering the "
            "collection rule. This is the OTHER half of the modeled defect (the "
            "pre-change collection branch resolved entries in one non-recursive pass "
            "and never re-dispatched on a nested collection entry), and it is the "
            "half that survives if only the container kind is repaired: a nested "
            "collection entry then keeps whatever kind it arrived with only by "
            "accident, and is never resolved through the full dispatch, so a lookup "
            "holding a nested collection of resolvable sub-values comes back "
            "unresolved. A patch that fixed the outer container but kept the shallow "
            "pass does NOT implement the required behavior. NO nagini counterpart: "
            "its flat carrier had no nested entries to leave unresolved."
        ),
        "rationale": (
            "REJECTED by the RECURSION in clause (c): the entry rule is `resolveSpec` "
            "itself, so a nested collection entry must be resolved through the same "
            "rule, and the rival leaves it untouched. Attacks a clause the two "
            "coercion rivals cannot reach (this rival gets every top-level kind "
            "right) and that the entry-passthrough rival also cannot (this rival DOES "
            "resolve an entry that is directly an expression, so it agrees with gold "
            "at that rival's witness input — hence its own witness, one nesting level "
            "deeper). Same single weak hypothesis about the one opaque term. If it "
            "VERIFIES => SPEC-TOO-WEAK: the spec would not force resolution to "
            "recurse, and a half-fixed patch would verify without resolving."
        ),
        # `LV.lst [LV.lst [LV.expr 4]]`: gold => lst [lst [resolveExpression 4]];
        # rival => lst [lst [LV.expr 4]] (inner collection copied verbatim).
        "witness": _wit("LV.lst [LV.lst [LV.expr 4]]",
                        "nested collection entry left unresolved by a shallow pass",
                        extra=_H4, tail=_FLIP),
    },
    {
        "id": "weak-expression-unresolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EXPR_RAW,
        "refinement": (
            "a value that resolves itself is returned VERBATIM instead of being "
            "resolved, when it appears at the top level rather than inside a "
            "collection. This arm is UNCHANGED by the modeled change, so a patch "
            "breaking it is a regression rather than a wrong fix: it would leave the "
            "unresolved value as the lookup's right-hand side for every "
            "expression-valued lookup, which the existing suite covers heavily "
            "(the PASS_TO_PASS set includes the expression-valued lookup paths). It "
            "does not resolve, and it is included because the spec must defend the "
            "arms the change did NOT touch too — directive 5's frame analogue: a "
            "clause left unconstrained is where a wrong impl can put anything."
        ),
        "rationale": (
            "REJECTED by clause (a): `resolveSpec (LV.expr e) = resolveExpression e`, "
            "and the rival returns `LV.expr e`. Attacks the expression dispatch arm, "
            "which no other rival touches; binder `value` probed at a BARE expression "
            "(not a collection) — a top-level constructor no other witness in this "
            "battery uses. Conditioned on the same single weak hypothesis about the "
            "one opaque term (its value at identity 4 is not the unresolved value "
            "itself), jointly satisfiable since nothing in the frozen file constrains "
            "the resolver. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # `LV.expr 4`: gold => resolveExpression 4; rival => LV.expr 4.
        "witness": _wit("LV.expr 4", "bare expression returned unresolved",
                        extra=_H4, tail=_FLIP),
    },
    {
        "id": "weak-scalar-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PLAIN_WRAP,
        "refinement": (
            "a scalar leaf is lifted into a singleton collection instead of being "
            "returned unchanged. Its faithful real counterpart is a reconstruction "
            "that treats every value as a collection — the change that introduced the "
            "modeled defect is about which container kind a collection is rebuilt "
            "into, and a patch that also wrapped non-collection values would turn "
            "every ordinary lookup value into a one-element container, breaking the "
            "overwhelming majority of the existing suite (scalar-valued lookups) as "
            "well as the F2P comparison. Does NOT resolve. Included for the same "
            "reason as the expression arm: the untouched arms of the dispatch must be "
            "pinned, or a wrong impl can put anything there."
        ),
        "rationale": (
            "REJECTED by clause (b): `resolveSpec (LV.plain n) = LV.plain n`, so a "
            "scalar leaf's result is pinned to the leaf itself, and the rival returns "
            "a collection. Attacks the scalar-leaf dispatch arm, which no other rival "
            "touches; binder `value` probed at a BARE scalar leaf — a fourth distinct "
            "top-level constructor, and the only witness in the battery whose input "
            "is not a collection or an expression. Fully decidable, no conditioning "
            "needed. If it VERIFIES => SPEC-TOO-WEAK: the spec would leave the "
            "no-op arm of the dispatch unconstrained."
        ),
        # `LV.plain 7`: gold => plain 7; rival => lst [plain 7].
        "witness": _wit("LV.plain 7", "scalar leaf lifted into a collection"),
    },
    {
        "id": "weak-tup-drop-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TUP_DROP_LAST,
        "refinement": (
            "the SECOND-kind collection is rebuilt short by its final entry, while "
            "the first kind is rebuilt correctly. Its faithful real counterpart is a "
            "reconstruction whose same-kind repair was applied to one container kind "
            "and whose entry loop is off by one on the other: a lookup built from a "
            "second-kind container of two or more values silently loses a value, so "
            "the rendered right-hand side is short and the comparison fails, while "
            "every first-kind lookup keeps passing. That asymmetry is exactly what "
            "makes it dangerous — the F2P assertion is stated over the FIRST kind, so "
            "this impl passes the one test the change is judged by and still does not "
            "implement the required behavior; the second-kind lookups the existing "
            "suite covers would regress. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ARITY half of clause (d): `resolveSpec (LV.tup xs) = "
            "LV.tup (xs.map resolveSpec)` fixes the second kind's entry count to the "
            "input's, and the rival emits one fewer for any non-empty second-kind "
            "collection. This closes a real gap rather than mirroring an existing "
            "case: every other collection-internals rival in this battery edits the "
            "FIRST-kind arm only, so clause (d) was probed for its emitted KIND "
            "(weak-coerce-second-kind) and for nothing else. The two arms are "
            "separate `match` arms — an impl correct on one is not thereby correct on "
            "the other — so the arity/order/per-entry halves of (d) rested on an "
            "assumed symmetry until this rival tested one of them. Binder `value` "
            "probed at a one-entry SECOND-kind collection, an input at which the "
            "rival is the only member of the battery to differ from gold. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # `LV.tup [LV.plain 7]`: gold => tup [plain 7]; rival => tup [].
        # Rebuilt by hand: rival exit 0, gold exit 1 (`unsolved goals ⊢ False`).
        "witness": _wit("LV.tup [LV.plain 7]",
                        "final entry dropped from the rebuilt second-kind collection"),
    },
    {
        "id": "weak-expression-identity-shifted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EXPR_SHIFT,
        "refinement": (
            "the expression arm DOES resolve — it just resolves the wrong one, the "
            "neighbouring identity rather than the value it was handed. Its faithful "
            "real counterpart is a dispatch that resolves some other object reachable "
            "from the call site instead of the argument itself (a stale local, the "
            "wrong element of an enclosing collection): the lookup then comes back "
            "carrying a resolved value that belongs to a DIFFERENT expression, which "
            "is a wrong right-hand side rather than an unresolved one. Does NOT "
            "resolve, and it is the more dangerous shape than returning the value "
            "unresolved, because the result is well-formed and merely wrong."
        ),
        "rationale": (
            "REJECTED by clause (a) read as an equation in `e`: `resolveSpec (LV.expr "
            "e) = resolveExpression e` pins WHICH identity is resolved, not merely "
            "that the resolver is invoked. weak-expression-unresolved attacks the arm "
            "by not resolving at all, so between them the two rivals separate the two "
            "independent facts in (a) — that resolution happens, and that it happens "
            "at the input's own identity — where before only the first was probed. "
            "The witness conditions on a DIFFERENT and equally weak hypothesis than "
            "the rest of the battery: that the resolver does not identify two "
            "distinct expression identities. Nothing in the frozen file constrains "
            "the opaque resolver at any point, so it is satisfiable and the gate's "
            "consistency probe cannot derive `False` from it (re-run by hand: probe "
            "exit 1). If it VERIFIES => SPEC-TOO-WEAK: an impl could resolve anything "
            "it liked as long as it resolved something."
        ),
        # `LV.expr 4`: gold => resolveExpression 4; rival => resolveExpression 5.
        # Distinct under `h`. Rebuilt by hand: rival 0, gold 1 (`⊢ False`), probe 1.
        "witness": _wit("LV.expr 4", "the neighbouring expression identity resolved "
                                     "instead of the input's own",
                        extra=_H54, tail=_EXACT_H),
    },
    {
        "id": "weak-tup-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TUP_REVERSE,
        "refinement": (
            "the SECOND-kind collection is rebuilt back-to-front while the first kind "
            "is rebuilt correctly. Its faithful real counterpart is a reconstruction "
            "whose entry traversal runs the wrong way round for one container kind "
            "only: a lookup built from a second-kind container of two or more values "
            "comes back with its values in the wrong sequence, so the rendered "
            "right-hand side differs and any ordered second-kind lookup is built "
            "against the wrong sequence, while every first-kind lookup keeps passing. "
            "Like the second-kind arity rival, the asymmetry is what makes it "
            "dangerous — the F2P assertion is stated over the FIRST kind, so this impl "
            "passes the one test the change is judged by and still does not implement "
            "the required behavior. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ORDER half of clause (d): `resolveSpec (LV.tup xs) = "
            "LV.tup (xs.map resolveSpec)` fixes the position of each second-kind "
            "entry, and the rival emits its reverse. Added by audit to close a real "
            "gap: weak-reverse-order attacks ordering on the FIRST-kind arm only, and "
            "the two are separate `match` arms, so nothing in the spec makes an impl "
            "that orders one kind correctly order the other correctly — clause (d)'s "
            "order half rested on an assumed symmetry. Binder `value` probed at a "
            "three-entry SECOND-kind collection with pairwise-distinct entries, a "
            "length where reversal is not a coincidence of a two-element swap. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # `LV.tup [LV.plain 1, LV.plain 2, LV.plain 3]`: gold => 1,2,3; rival => 3,2,1.
        # Rebuilt by hand: rival exit 0, gold exit 1 (`unsolved goals ⊢ False`).
        "witness": _wit("LV.tup [LV.plain 1, LV.plain 2, LV.plain 3]",
                        "second-kind entries emitted in the opposite order"),
    },
    {
        "id": "weak-tup-entry-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TUP_ENTRY_RAW,
        "refinement": (
            "each entry of the SECOND-kind collection is copied VERBATIM instead of "
            "being resolved, while the first kind resolves its entries correctly. The "
            "second kind's emitted kind, arity and order are all right; only its "
            "per-entry resolution is skipped. Its faithful real counterpart is a "
            "reconstruction that rebuilds one container kind properly and, for the "
            "other, rebuilds the container but no longer resolves the sub-values — so "
            "a second-kind lookup whose entries are themselves resolvable comes back "
            "carrying an unresolved sub-value as its right-hand side. Does NOT "
            "resolve, and it passes the first-kind F2P assertion while regressing the "
            "second-kind lookups the existing suite covers."
        ),
        "rationale": (
            "REJECTED by the PER-ENTRY half of clause (d) composed with clause (a): "
            "entry k of a second-kind result must be `resolveSpec` of entry k, and for "
            "an entry that is an expression that is the resolver's value, not the "
            "entry itself. Added by audit for the same reason as the order rival above "
            "— every per-entry attack the battery shipped edits the FIRST-kind arm, so "
            "clause (d)'s entry half was pinned by no witness. Conditioned on the same "
            "single weak hypothesis about the one opaque term, jointly satisfiable "
            "since nothing in the frozen file constrains the resolver. If it VERIFIES "
            "=> SPEC-TOO-WEAK: the spec would pin the second kind's container and not "
            "its contents."
        ),
        # `LV.tup [LV.expr 4]`: gold => tup [resolveExpression 4];
        # rival => tup [LV.expr 4]. Distinct under `h`.
        # Rebuilt by hand: rival exit 0, gold exit 1 (`⊢ False` under `h`), probe 1.
        "witness": _wit("LV.tup [LV.expr 4]",
                        "second-kind entries copied verbatim instead of resolved",
                        extra=_H4, tail=_FLIP),
    },
    {
        "id": "weak-scalar-identity-shifted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PLAIN_SHIFT,
        "refinement": (
            "the scalar-leaf arm returns a scalar leaf — just not the one it was "
            "handed, but the neighbouring identity. Its faithful real counterpart is a "
            "dispatch whose no-op branch returns some other value reachable from the "
            "call site rather than the argument itself (a stale local, the wrong "
            "element of an enclosing collection): the lookup then comes back carrying "
            "a well-formed scalar that is simply the WRONG one, which breaks the "
            "overwhelming majority of the existing suite (scalar-valued lookups) as "
            "well as the F2P comparison, whose collection literal holds scalar "
            "entries. Does NOT resolve, and like the expression-identity rival it is "
            "the more dangerous shape than a kind error, because the result has the "
            "right shape and merely wrong content."
        ),
        "rationale": (
            "REJECTED by clause (b) read as an equation in `n`: `resolveSpec (LV.plain "
            "n) = LV.plain n` pins WHICH leaf comes back, not merely that a leaf "
            "does. Added by audit: weak-scalar-wrapped attacks this arm by changing "
            "the result's KIND (a leaf lifted into a collection), so between them the "
            "two rivals separate the two independent facts in (b) — that the result is "
            "a scalar leaf, and that it is the INPUT's own leaf — where before only "
            "the first was probed and the payload `n` was pinned by no witness. Binder "
            "`value` probed at a bare scalar leaf; fully decidable, no conditioning "
            "needed. If it VERIFIES => SPEC-TOO-WEAK: an impl could return any leaf it "
            "liked as long as it returned a leaf."
        ),
        # `LV.plain 7`: gold => plain 7; rival => plain 8.
        # Rebuilt by hand: rival exit 0, gold exit 1 (`unsolved goals ⊢ False`).
        "witness": _wit("LV.plain 7",
                        "the neighbouring scalar leaf returned instead of the input's"),
    },
]


# The axiom lane belongs to G-AX and is ignored by this gate. There is nothing to
# put here in any case: the context resolver is declared `opaque` with NO consumed
# property axiom (the spec and the impl invoke it identically, so it cancels in the
# correctness argument), and the changed behavior — which collection kind is
# rebuilt, and that entry resolution recurses — is modeled DEEPLY rather than
# assumed.
AXIOM_TESTS = []
