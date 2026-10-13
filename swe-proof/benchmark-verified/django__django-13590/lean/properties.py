# properties.py — G-PBT falsification battery for django__django-13590 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Every SPEC case is
# a FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive honestly reproves, the proof body — differs), checked
# by variant_scope before the verifier runs. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the postcondition
# and not to a tactic script that merely stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read off Solution.lean / mapping.md / instance.json). ONE
# obligation, ONE impl region:
#
#   implementation_resolveValue
#     (resolveExpr : Nat → Value) (v : Value) : Option Value
#
#   theorem correct_resolveValue :
#     ∀ (resolveExpr : Nat → Value) (v : Value),
#       problem_spec_resolveValue resolveExpr v
#         (implementation_resolveValue resolveExpr v)
#
#   problem_spec_resolveValue resolveExpr v result :=
#     result = some (resolveRef resolveExpr v)
#
# There is no precondition hypothesis: the obligation is universally quantified over
# BOTH binders, so the postcondition must hold at every single-expression resolver and
# every input value. The single equation is a total-correctness pin that bundles four
# INDEPENDENT top-level demands, each of which a rival can attack in isolation:
#
#   (a) TOTALITY / DEFINEDNESS — the result is `some _` for every input, INCLUDING a
#       sequence of every container kind. `Option` is the modeled carrier of "the
#       rebuild did not complete", so `none` on any kind is a violation of this
#       clause alone (the load-bearing clause: it is the one the frozen behavior
#       differs from the pre-change behavior on, and the one Solution_prepatch.lean
#       cannot discharge).
#   (b) SCALAR / EXPRESSION DISPATCH — a scalar maps to itself; an expression maps to
#       `resolveExpr` of its identifier. The resolver binder is what makes the second
#       arm attackable: an impl that returns the expression UNRESOLVED agrees with the
#       spec only at resolvers that happen to be the identity on that identifier, so
#       the clause is refutable exactly by varying `resolveExpr`.
#   (c) KIND PRESERVATION — the rebuilt sequence carries the SAME container kind. The
#       kind enumeration is three-valued precisely so this is pinned; collapsing two
#       kinds is a distinct violation from failing to produce a result.
#   (d) ELEMENT-WISE CONTENT + LENGTH + ORDER — the rebuilt sequence holds the
#       resolutions of the originals, all of them, in order. Three separable ways to
#       break it: leave the elements unresolved, drop one, permute them.
#
# CARRIER NOTE (what the nagini rivals BECOME here). The nagini sibling abstracted the
# same behavior over a `List[int]` behind a fractional read permission, and lifted the
# "the rebuild does not complete" difference — invisible to a contents-only value
# abstraction — into an abstract capability token `well_formed_container(contents,
# field_named)` that no impl could Fold and only a convention-matching construction
# could mint. This backend does not need that device: the effect is modeled DIRECTLY in
# the result type as `Option Value`, and the container kind is a first-class component
# of the returned value. So the nagini token clause and its `field_named` argument port
# to clause (a) + clause (c) respectively, and both are TRANSPARENT — `simp` computes
# the reference resolution at any literal input, so no witness needs to condition on
# the carrier. Concretely:
#
#   nagini atk_1 (never construct; return the bare resolved contents) and
#   nagini atk_3 (construct for the plain kind, skip it for the field-named kind) and
#   nagini atk_4 (hand the single bundle to every kind unconditionally)
#     all express, in nagini's carrier, "the field-named path never went through a
#     well-formed construction". Here that is exactly "the special-kind arm yields no
#     result" => weak-special-kind-no-result (the pre-change behavior, and the same
#     rival Solution_prepatch.lean carries). atk_1's OTHER half — "return a value-equal
#     thing" — is not wrong on this carrier at all (see pos-direct-oracle), because
#     there is no separate effect to skip once the result value is pinned.
#   nagini atk_5 (mint the token for the WRONG kind to dodge the precondition)
#     ports to weak-special-kind-collapsed: produce a result, but tag it with the
#     wrong container kind. Clause (c).
#   nagini partial-domain-drop-first-field-named
#     ports to weak-special-kind-drops-element: correct on every other kind, one
#     element short on the special kind. Clause (d), length half.
#   nagini pos_control2 (single computed call site) and the branch-reorder positive
#     port to pos-collapse-kind-dispatch and pos-arm-reorder.
#
# ADDED BY AUDIT (no nagini counterpart; both close gaps in the ported set rather
# than porting a dropped case):
#   weak-bundle-kinds-swapped        — clause (c) at the pair of kinds that SHARE a
#     rebuild convention. Every ported kind rival moves the `.special` arm, so the
#     distinction the three-valued enumeration exists to pin between the OTHER two
#     kinds was attested by no case.
#   weak-elements-resolved-one-level — clause (d) at DEPTH. The ported content rival
#     deletes the resolution step, so it is refuted at depth one and says nothing
#     about the step having to RECURSE; the spec's reference resolution is a
#     structural recursion, and this rival performs the step but stops descending.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's frame-mutation-write-value, its #1 weakness class: the
#     input carried only half permission and the rival wrote back into it). Lean is
#     referentially transparent — no aliasing, no fractional permission, no heap — so a
#     "store into a read-only input" rival is not EXPRESSIBLE here. The class is
#     genuinely VACUOUS on this carrier, not a spec hole; no substitute is fabricated.
#     See 'assessment'.
#   * (WITHDRAWN — see admiss-ground-f2p below.) The shipped manifest recorded
#     ADMISSIBILITY (nagini's admissibility-readonly-usable) as N/A on the ground
#     that the lean obligation binds `∀ resolveExpr v` with no precondition
#     hypothesis, so there is nothing for a PRECOND-TOO-STRONG case to probe. That
#     reason is WRONG and the second audit removed it: "the frozen obligation has no
#     precondition" is not what makes the lane vacuous. On a TOTAL carrier the
#     analogue of an over-strong precondition is the obligation being UNSATISFIABLE
#     at exactly an F2P-shaped input — which a positive that discharges the spec
#     predicate at that concrete input, by evaluation, before closing the frozen
#     obligation verbatim, tests directly. Such a case is expressible here and it
#     VERIFIES (measured: real build, exit 0), so the lane is now carried.
#   * DIVERGENCE / NON-TERMINATION. `implementation_resolveValue` is a total Lean
#     `def`, so a diverging implementation cannot be written at all: the class is
#     vacuous here (unlike velvet under partial termination semantics, where it is a
#     known spec hole — the corpus-wide termination-semantics finding). The nagini sibling carries no
#     diverge-* case either.
#   * AXIOM_TESTS. The axiom lane is G-AX's job and this gate ignores it. There is no
#     consumed axiom here regardless: the single-expression resolution is a
#     universally-quantified PARAMETER rather than an `opaque` callee with a contract,
#     which is also why every witness below can pick its own resolver.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-13590"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Every one lies ENTIRELY inside -- impl-start / -- impl-end and
# is unique in the file, so each _swap edits only the impl region and same_spec holds
# by construction. Asserted here so the manifest breaks LOUDLY if the frozen solution
# ever changes shape.
# ---------------------------------------------------------------------------

# the arm for the kind whose elements must be supplied individually
_ARM_SPECIAL = (
    "      | .special =>\n"
    "          -- this kind requires its elements supplied individually; rebuild it\n"
    "          return some (.seq .special values)\n"
)
# the two arms for the kinds that take their elements as a single bundle
_ARM_PLAIN = (
    "      | .plain =>\n"
    "          return some (.seq .plain values)\n"
)
_ARM_TUPLELIKE = (
    "      | .tupleLike =>\n"
    "          return some (.seq .tupleLike values)\n"
)
# the element-wise resolution step that feeds every rebuild
_MAP = "      let values := elems.map (resolveRef resolveExpr)\n"
# the two non-sequence arms
_ARM_EXPR = (
    "  | .expr id =>\n"
    "      -- an expression is replaced by its resolved form\n"
    "      return some (resolveExpr id)\n"
)
_ARM_SCALAR = (
    "  | .scalar n =>\n"
    "      -- a plain scalar is returned unchanged\n"
    "      return some (.scalar n)\n"
)
# the whole per-kind dispatch (all three arms), for the collapse positive
_KIND_DISPATCH = "      match c with\n" + _ARM_SPECIAL + _ARM_PLAIN + _ARM_TUPLELIKE
# the whole top-level dispatch, for the arm-reorder positive
_TOP_DISPATCH = (
    "  match v with\n"
    + _ARM_EXPR
    + "  | .seq c elems =>\n"
      "      -- the elements may themselves be values, so resolve each independently;\n"
      "      -- then rebuild a sequence of the same container kind from the results\n"
    + _MAP
    + _KIND_DISPATCH
    + _ARM_SCALAR
)
# the whole impl definition, for the direct-oracle positive
_IMPL_DEF = _BASE[_BASE.index("def implementation_resolveValue"):_BASE.index("-- impl-end")]

for _a in (_ARM_SPECIAL, _ARM_PLAIN, _ARM_TUPLELIKE, _MAP, _ARM_EXPR, _ARM_SCALAR,
           _KIND_DISPATCH, _TOP_DISPATCH, _IMPL_DEF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"impl anchor drifted: {_a!r}")

# The frozen proof body (the tactic lines only, inside -- proof-start / -- proof-end).
# Swapped ONLY by positives that reshape the impl enough that the frozen script no
# longer closes; the `theorem correct_resolveValue` STATEMENT is never touched, and no
# new axiom / lemma / sorry is ever introduced.
_PROOF = (
    "  intro resolveExpr v\n"
    "  cases v with\n"
    "  | scalar n =>\n"
    "      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]\n"
    "      rfl\n"
    "  | expr id =>\n"
    "      simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]\n"
    "      rfl\n"
    "  | seq c elems =>\n"
    "      cases c <;>\n"
    "        · simp only [problem_spec_resolveValue, implementation_resolveValue, resolveRef, Id.run]\n"
    "          rfl\n"
)
if _BASE.count(_PROOF) != 1:
    raise AssertionError("proof body anchor drifted")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================

# pos-collapse-kind-dispatch — nagini's pos_control2 ("one computed call site instead
# of literal per-kind branches"). The three per-kind arms, which differ only in which
# kind literal they re-tag the rebuilt sequence with, collapse into a SINGLE rebuild
# that carries the kind it was given through. Behaviourally identical on every input
# (each arm already returned its own kind); only the branch structure changes — the
# shape a faithful patch could equally take. The frozen proof still closes verbatim,
# because `cases c` leaves each branch in the same reducible form.
_POS_COLLAPSE = _swap(
    _BASE, _KIND_DISPATCH,
    "      -- rebuild a sequence of the same container kind from the resolved results\n"
    "      return some (.seq c values)\n",
)

# pos-arm-reorder — nagini's branch-reorder positive. The top-level dispatch is
# reordered (scalar, then sequence, then expression) and the per-kind arms inside it
# are reordered too (the individually-supplied kind moved LAST). Pattern matching on an
# inductive is order-insensitive for disjoint constructor patterns, so the result value
# is identical at every input; only the arm order moves. Frozen proof closes verbatim.
_POS_REORDER = _swap(
    _BASE, _TOP_DISPATCH,
    "  match v with\n"
    + _ARM_SCALAR
    + "  | .seq c elems =>\n"
      "      -- the elements may themselves be values, so resolve each independently;\n"
      "      -- then rebuild a sequence of the same container kind from the results\n"
    + _MAP
    + "      match c with\n" + _ARM_PLAIN + _ARM_TUPLELIKE + _ARM_SPECIAL
    + _ARM_EXPR,
)

# pos-direct-oracle — the cheapest HONEST impl. The postcondition's reference
# resolution is a TOTAL, TRANSPARENT structural recursion over the input value (it is
# in the `pure` region, not an opaque callee and not an answer-key table), so returning
# it directly is a fully grounded correct implementation rather than an
# ungrounded-oracle echo: there is nothing to echo, and any WRONG value fails the
# postcondition (that is exactly what the eight rivals below demonstrate). This is the
# lean counterpart of nagini's atk_6 positive, and the reason the nagini
# "ungrounded-oracle-echo" class is N/A here too. The impl shape changes enough that
# the frozen case split is no longer needed, so the proof body is honestly re-closed
# with `rfl` after unfolding — the theorem STATEMENT is byte-identical and no
# axiom/lemma/sorry is added.
_POS_DIRECT = _swap(
    _swap(
        _BASE, _IMPL_DEF,
        "def implementation_resolveValue\n"
        "    (resolveExpr : Nat → Value) (v : Value) : Option Value :=\n"
        "  -- the resolution of the value, computed structurally from the input\n"
        "  some (resolveRef resolveExpr v)\n",
    ),
    _PROOF,
    "  intro resolveExpr v\n"
    "  unfold problem_spec_resolveValue implementation_resolveValue\n"
    "  rfl\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly, edits only the impl region, leaves the frozen proof body in place
# (which will not close for the reshaped impl — that is the DEFAULT outcome of
# reshaping and is exactly why each carries a witness), and is refuted at a concrete
# input by a witness checked in a file with the obligation removed.
# ===========================================================================

# (a) TOTALITY. No result for the kind whose elements must be supplied individually —
# the pre-change behavior, i.e. the rival Solution_prepatch.lean carries.
_RIV_SPECIAL_NONE = _swap(_BASE, _ARM_SPECIAL,
                          "      | .special =>\n          return none\n")
# (a) TOTALITY, other sub-domain. No result for a bundle-taking kind instead.
_RIV_PLAIN_NONE = _swap(_BASE, _ARM_PLAIN,
                        "      | .plain =>\n          return none\n")
# (a) TOTALITY, non-sequence sub-domain. No result for a scalar.
_RIV_SCALAR_NONE = _swap(_BASE, _ARM_SCALAR,
                         "  | .scalar n =>\n      return none\n")
# (c) KIND PRESERVATION. A result IS produced for the individually-supplied kind, but
# it is tagged with a bundle-taking kind instead.
_RIV_KIND_COLLAPSE = _swap(_BASE, _ARM_SPECIAL,
                           "      | .special =>\n"
                           "          return some (.seq .plain values)\n")
# (d) CONTENT. The elements are carried over UNRESOLVED — the rebuild is shallow.
_RIV_UNRESOLVED = _swap(_BASE, _MAP, "      let values := elems\n")
# (d) ORDER. The elements are resolved, all of them, but the rebuild reverses them.
_RIV_REVERSED = _swap(
    _BASE, _MAP,
    "      let values := (elems.map (resolveRef resolveExpr)).reverse\n")
# (d) LENGTH. Correct on every other kind; one element short on the
# individually-supplied kind (nagini's partial-domain rival, same sub-domain).
_RIV_DROP_ELEM = _swap(_BASE, _ARM_SPECIAL,
                       "      | .special =>\n"
                       "          return some (.seq .special values.tail)\n")
# (b) EXPRESSION DISPATCH. An expression is returned UNRESOLVED rather than replaced by
# its resolved form.
_RIV_EXPR_UNRESOLVED = _swap(_BASE, _ARM_EXPR,
                             "  | .expr id =>\n      return some (.expr id)\n")
# (c) KIND PRESERVATION, the OTHER kind pair. The two bundle-taking kinds are swapped
# for each other. Added by audit: every other kind rival moves the .special arm, so the
# pair of kinds that SHARE a rebuild convention was never separated by any case — and
# that pair is exactly what the three-valued kind enumeration exists to keep apart.
_RIV_KIND_SWAP = _swap(_BASE, _ARM_PLAIN,
                       "      | .plain =>\n"
                       "          return some (.seq .tupleLike values)\n")
# (d) CONTENT, at DEPTH. The element-wise step resolves only the top layer of each
# element instead of recursing, so a nested sequence keeps its own sub-elements
# unresolved. Added by audit: `weak-elements-unresolved` deletes the step outright, so a
# rival that performs it only one level deep — the natural shallow-recursion slip, and
# the one closest to a plausible faithful patch — was unprobed.
_RIV_SHALLOW_DEPTH = _swap(
    _BASE, _MAP,
    "      let values := elems.map (fun e =>\n"
    "        match e with\n"
    "        | .expr id => resolveExpr id\n"
    "        | x => x)\n")


# --- witnesses -------------------------------------------------------------------
# Two shapes, by what the rival gets wrong at the probed point. Both instantiate the
# postcondition at a CONCRETE resolver and a CONCRETE input value and then derive the
# contradiction from the transparent reference resolution. `_wit_value` is for a rival
# that produces a WRONG value (strip the `some` by unification, then refute the values,
# which leaves `⊢ False` on gold because `simp` PROVES the equation there);
# `_wit_none` is for a rival that produces NO value. Neither binds anything, so neither
# can have inconsistent hypotheses; each has been checked to elaborate against its
# rival and to FAIL on the frozen solution.
#
# AUDIT NOTE (third audit) — `_wit_none` RE-AUTHORED, because its gold-side failure was
# measured to be HOLLOW. It used to close with `exact absurd h (by simp [resolveRef])`,
# and the `simp` set omitted the `pure`/`Id.run` step that the frozen proof itself
# discharges with `rfl`. So on gold the inner `by simp` stalled with
#   unsolved goals h : pure (some (Value.scalar 5)) = some (resolveRef ... (Value.scalar 5))
#   ⊢ ¬pure (some (Value.scalar 5)) = some (Value.scalar 5)
# — the Id-carrier defeq gap, not a fact about gold. The OPPOSITE-CLAIM CONTROL proves
# it attested nothing: the same tactic set applied to the claim that gold DOES satisfy
# the spec at that very point (a claim `correct_resolveValue` proves) fails with the
# byte-identical message minus the `¬`,
#   unsolved goals ⊢ pure (some (Value.scalar 5)) = some (Value.scalar 5)
# so gold's exit code did not depend on what was claimed. Measured, not argued: three
# baseline builds (gold exit 1) and three control builds (gold exit 1, identical
# residue), all six reaching a verdict in 5.8-10.9 s.
#
# The re-authored witness routes the refutation through the DECIDABLE projection of the
# clause the rival actually breaks: totality. The spec instance forces
# `(implementation_resolveValue r v).isSome = true`, `isSome` is a `Bool`, and `decide`
# EVALUATES it on the subject under test — the rival computes `false` there (witness
# elaborates, exit 0), while gold computes `true`, so gold's build now reports
#   Tactic `decide` proved that the proposition
#     ¬(implementation_resolveValue (fun x => Value.scalar 0) (Value.scalar 5)).isSome = true
#   is false
# i.e. a DECISION about gold's own output. Claim-dependence re-measured on the repaired
# witness: the same `decide` on the un-negated claim `(...).isSome = true` VERIFIES on
# gold (exit 0) and is proved FALSE against each rival (exit 1), so the exit code tracks
# the claim in both directions. (`decide` cannot be used on the full equation instead:
# `Value` carries no `DecidableEq`, which is why `_wit_value` stays on the
# `simp`-collapses-to-`False` shape — measured decisive for all seven of its cases.)

def _wit_value(resolver, value, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_resolveValue {resolver} {value}\n"
        f"    (implementation_resolveValue {resolver} {value}) := by\n"
        f"  intro h\n"
        f"  simp only [problem_spec_resolveValue, implementation_resolveValue, Id.run] at h\n"
        f"  exact absurd (Option.some.inj h) (by simp [resolveRef])"
    )


def _wit_none(resolver, value, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_resolveValue {resolver} {value}\n"
        f"    (implementation_resolveValue {resolver} {value}) := by\n"
        f"  intro h\n"
        f"  simp only [problem_spec_resolveValue] at h\n"
        f"  -- The spec instance DEMANDS a result at this input, so it forces the\n"
        f"  -- decidable projection `isSome` of the impl's OWN output to be `true`.\n"
        f"  have hs : (implementation_resolveValue {resolver} {value}).isSome = true := by\n"
        f"    simp [h]\n"
        f"  -- `decide` then EVALUATES that projection on the subject under test instead\n"
        f"  -- of rewriting it away: the rival yields no result here, so the projection\n"
        f"  -- computes `false` and the spec instance is refuted. On the frozen solution\n"
        f"  -- the same `decide` computes `true` and reports the goal FALSE — gold's\n"
        f"  -- failure is a DECISION about gold's own output, and the un-negated claim\n"
        f"  -- `(...).isSome = true` VERIFIES on gold under this very tactic.\n"
        f"  exact absurd hs (by decide)"
    )


# The F2P-shaped input: a two-element sequence of the individually-supplied kind
# carrying the boundary values the failing test filters on.
_V_SPECIAL_2 = "(Value.seq Container.special [Value.scalar 51, Value.scalar 100])"


SPEC_TESTS = [
    # ------------------------------------------------------------------ positives
    {
        "id": "pos-collapse-kind-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_COLLAPSE,
        "rationale": (
            "nagini's pos_control2 ported: the three literal per-kind rebuild arms — "
            "which differ only in which kind literal they re-tag the rebuilt sequence "
            "with — collapse into ONE rebuild that carries the given kind through. "
            "Behaviourally identical at every (resolveExpr, v): each arm already "
            "returned its own kind, so kind preservation (clause c), totality (a) and "
            "the element-wise content (d) are unchanged. A structurally different but "
            "CORRECT impl of the modeled behavior must verify; the frozen "
            "`theorem correct_resolveValue` statement and proof body are both kept "
            "verbatim. If it FAILS => SPEC-TOO-STRONG (the postcondition would be "
            "over-fit to one dispatch shape rather than to the behavior)."
        ),
    },
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "nagini's branch-reorder positive ported: the top-level dispatch is "
            "reordered (scalar first, expression last) AND the per-kind arms are "
            "reordered inside it (the individually-supplied kind moved last). The "
            "constructor patterns are disjoint and exhaustive, so the result is "
            "identical at every input and every resolver; only arm ORDER moves — the "
            "shape a faithful patch could equally take. Statement and proof body kept "
            "verbatim. If it FAILS => SPEC-TOO-STRONG (the postcondition would be "
            "over-fit to one arm order)."
        ),
    },
    {
        "id": "pos-direct-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the cheapest HONEST correct impl, and the lean counterpart of nagini's "
            "atk_6 positive. The postcondition's reference resolution is a total, "
            "TRANSPARENT structural recursion over the input value (it is a plain "
            "helper, not an opaque callee and not an answer-key table), so returning it "
            "directly is fully GROUNDED in the binders, not an ungrounded-oracle echo — "
            "which is why the echo class is N/A here just as it was on nagini. Must "
            "verify: the postcondition is literally that equation. The proof body is "
            "honestly re-closed with `rfl` after unfolding (statement byte-identical; "
            "no new axiom, lemma or sorry). If it FAILS => SPEC-TOO-STRONG. It also "
            "shows the spec is not echo-VULNERABLE: the eight rivals below are exactly "
            "the wrong answers that fail this same equation."
        ),
    },

    # --------------------------------------------------------- admissibility
    {
        "id": "admiss-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # The spec predicate is discharged at the concrete F2P-shaped input — a
        # two-element sequence of the individually-supplied kind carrying the
        # boundary values the failing test filters on — BY EVALUATION, as a `have`
        # prepended to the frozen tactic body; the frozen obligation is then closed
        # verbatim after it. Nothing is assumed: no new declaration, no axiom, no
        # lemma, no sorry, and the `theorem correct_resolveValue` statement is
        # byte-identical. (Verified: real build, exit 0.)
        "module": _swap(
            _BASE, "  intro resolveExpr v\n",
            "  have _ground : problem_spec_resolveValue (fun _ => Value.scalar 0)\n"
            "      (Value.seq Container.special [Value.scalar 51, Value.scalar 100])\n"
            "      (implementation_resolveValue (fun _ => Value.scalar 0)\n"
            "        (Value.seq Container.special "
            "[Value.scalar 51, Value.scalar 100])) := by\n"
            "    simp only [problem_spec_resolveValue, implementation_resolveValue, "
            "Id.run,\n"
            "      resolveRef, List.map]\n"
            "    rfl\n"
            "  intro resolveExpr v\n"),
        "rationale": (
            "ADDED BY THE SECOND AUDIT, replacing a lane the shipped manifest "
            "recorded as N/A for a reason that does not hold. The obligation binds "
            "both parameters with no precondition hypothesis, so PRECOND-TOO-STRONG "
            "has no precondition to over-constrain — but that is NOT what makes the "
            "lane vacuous on a total carrier. The analogue here is the obligation "
            "being UNSATISFIABLE at exactly a normal, F2P-shaped input: a spec that "
            "no impl could discharge at the very input the failing test exercises "
            "would be as broken as an over-strong precondition, and every other case "
            "in this battery would still behave as declared. So this case discharges "
            "the spec predicate at that concrete input (the individually-supplied "
            "kind at the boundary values) by EVALUATION as a `have`, then closes the "
            "frozen obligation verbatim. It must verify. If it FAILS => "
            "PRECOND-TOO-STRONG: the modeled behavior would be unsatisfiable at a "
            "normal input, i.e. the reference resolution does not actually compute to "
            "anything the impl can return there — which no soundness or uniqueness "
            "case in this battery would detect, since all of them are stated over "
            "the SAME predicate and would fail or pass together with it."
        ),
    },

    # ------------------------------------------------------------------ rivals
    {
        "id": "weak-special-kind-no-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SPECIAL_NONE,
        "refinement": (
            "This is the pre-change behavior, on the sub-domain the failing test "
            "exercises: for the container kind whose constructor takes one argument per "
            "element, the rebuild is handed all the elements as a single bundle and so "
            "never completes. Its faithful real counterpart raises on a filter argument "
            "of that kind — precisely the TypeError the issue reports — so the filtered "
            "queryset never materializes and the F2P "
            "test_range_lookup_namedtuple does NOT pass. A rival that VERIFIED here "
            "would therefore be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the TOTALITY clause (a): the postcondition demands "
            "`result = some (resolved value)` for EVERY input, including a sequence of "
            "this kind, and this rival yields no result there. Attacks the `v` binder's "
            "`.seq .special` sub-domain; the load-bearing clause, since it is the one "
            "the frozen behavior differs from the pre-change behavior on. If it "
            "VERIFIES => SPEC-TOO-WEAK (the modeled effect would be unpinned and the "
            "whole spec hollow)."
        ),
        # Two-element sequence of the individually-supplied kind (the F2P shape):
        # gold => some(rebuilt), rival => none.
        "witness": _wit_none(
            "(fun _ => Value.scalar 0)", _V_SPECIAL_2,
            "the individually-supplied kind at the F2P boundary values: gold yields a "
            "rebuilt sequence, the rival yields no result"),
    },
    {
        "id": "weak-bundle-kind-no-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PLAIN_NONE,
        "refinement": (
            "The mirror sub-domain: no result for ONE of the two bundle-taking container "
            "kinds — the one modeled as `.plain` — which the frozen behavior handles and "
            "always handled. Its faithful counterpart raises on an ordinary list-valued "
            "filter argument, breaking the already-passing P2P "
            "test_in_lookup_allows_F_expressions_and_expressions_for_integers, whose "
            "filter arguments are lists. Does NOT resolve. (AUDIT NOTE: the shipped "
            "prose also cited "
            "test_range_lookup_allows_F_expressions_and_expressions_for_integers here; "
            "that citation was WRONG and has been removed — that test's filter "
            "arguments are of the OTHER bundle-taking kind, which this rival still "
            "handles correctly, so it would keep passing. The claim a case makes about "
            "which tests it breaks has to be true of the sub-domain the case actually "
            "moves.)"
        ),
        "rationale": (
            "REJECTED by the same TOTALITY clause (a) but at a DIFFERENT value of the "
            "`v` binder — a bundle-taking kind rather than the individually-supplied "
            "one. Shipped separately from weak-special-kind-no-result precisely because "
            "the two are NOT the same failure: this one demonstrates the totality demand "
            "is not special-cased to one kind, so a rival that broke only the ordinary "
            "kinds could not slip through. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # A bundle-taking kind: gold => some(rebuilt), rival => none.
        "witness": _wit_none(
            "(fun _ => Value.scalar 0)",
            "(Value.seq Container.plain [Value.scalar 1, Value.scalar 2])",
            "a bundle-taking kind: gold yields a rebuilt sequence, the rival yields no "
            "result"),
    },
    {
        "id": "weak-scalar-no-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SCALAR_NONE,
        "refinement": (
            "No result for a value with no sub-structure. Its faithful counterpart "
            "raises on (or drops) every ordinary scalar filter argument, which is the "
            "overwhelmingly common case for the function under change — it would break "
            "essentially the whole lookup suite, including the P2P "
            "test_expressions_in_lookups_join_choice. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the TOTALITY clause (a) on the NON-SEQUENCE sub-domain of `v`: "
            "the postcondition pins a scalar to `some` of itself. Distinct from the two "
            "sequence rivals above because it moves `v` off the sequence constructor "
            "entirely, so the battery demonstrates the totality demand covers the whole "
            "input carrier and not just the container arm. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # A scalar: gold => some(itself), rival => none.
        "witness": _wit_none(
            "(fun _ => Value.scalar 0)", "(Value.scalar 5)",
            "a value with no sub-structure: gold returns it unchanged, the rival yields "
            "no result"),
    },
    {
        "id": "weak-special-kind-collapsed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KIND_COLLAPSE,
        "refinement": (
            "nagini's atk_5 ported (there: mint the capability for the kind you CLAIM "
            "rather than the kind you HAVE, so the single-bundle convention becomes "
            "legal). Here the rebuild completes but re-tags the result with a "
            "bundle-taking kind: a faithful counterpart treats a filter argument of the "
            "individually-supplied kind as an ordinary one and hands its constructor a "
            "single bundle — which is exactly the pre-change call that raises — or, if "
            "it instead substitutes a plain container, returns a value of the wrong type "
            "to the caller. Either way the F2P test_range_lookup_namedtuple does NOT "
            "pass. This is a NEAR-MISS: it agrees with the frozen behavior on the "
            "elements, the length and the order, and on every other kind, so it is given "
            "its own witness at the kind it mis-tags rather than sharing one."
        ),
        "rationale": (
            "REJECTED by the KIND-PRESERVATION clause (c): the postcondition pins the "
            "rebuilt sequence to carry the SAME container kind as the input, and the "
            "kind enumeration is three-valued precisely so this is not collapsible. "
            "Attacks the container-kind component of `v` — a strictly different clause "
            "from weak-special-kind-no-result, which this rival satisfies (it does "
            "produce `some`). If it VERIFIES => SPEC-TOO-WEAK (the exact rebuilt type "
            "would be unpinned)."
        ),
        # Same input as the totality rival, but the rival now RETURNS a value — a
        # wrongly-tagged one. gold => .special, rival => .plain.
        "witness": _wit_value(
            "(fun _ => Value.scalar 0)", _V_SPECIAL_2,
            "the individually-supplied kind: gold preserves the kind, the rival "
            "re-tags the rebuilt sequence as a bundle-taking kind"),
    },
    {
        "id": "weak-elements-unresolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNRESOLVED,
        "refinement": (
            "The rebuild carries the elements over verbatim instead of resolving each "
            "independently — a shallow copy. Its faithful counterpart rebuilds the "
            "container from the RAW sub-values, so a filter argument holding resolvable "
            "sub-expressions is passed through unresolved and compiles to the wrong SQL: "
            "it breaks the P2P "
            "test_in_lookup_allows_F_expressions_and_expressions_for_integers and "
            "test_range_lookup_allows_F_expressions_and_expressions_for_integers (both "
            "filter on containers of resolvable sub-expressions). Does NOT resolve. "
            "(AUDIT NOTE: the shipped prose also claimed this rival breaks the F2P test; "
            "that claim was removed. The F2P filter argument's elements carry no "
            "sub-structure to resolve, so on THAT input this rival agrees with the "
            "frozen behavior — which is precisely why the witness below is stated at a "
            "different input, over a resolvable sub-expression, rather than at the F2P "
            "shape. A refinement may only name a test the rival's own sub-domain "
            "reaches.)"
        ),
        "rationale": (
            "REJECTED by the ELEMENT-WISE CONTENT clause (d): the postcondition pins "
            "each element of the rebuilt sequence to the RESOLUTION of the "
            "corresponding original, not to the original. This is the clause that "
            "consumes the `resolveExpr` binder, so the witness moves that binder off "
            "the value the rival would agree at — with a resolver that is the identity "
            "on the probed sub-expression the rival would be indistinguishable, which "
            "is exactly why the witness picks one that is not. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # A different kind AND a different resolver from the rivals above: a
        # bundle-taking sequence over a resolvable sub-expression, resolver mapping it
        # to a scalar. gold => [resolved], rival => [unresolved].
        "witness": _wit_value(
            "(fun _ => Value.scalar 7)",
            "(Value.seq Container.tupleLike [Value.expr 3])",
            "a sequence over a resolvable sub-expression: gold rebuilds from the "
            "resolved element, the rival keeps the original"),
    },
    {
        "id": "weak-elements-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSED,
        "refinement": (
            "Every element is resolved and none is lost — only the ORDER is reversed. "
            "Its faithful counterpart rebuilds the container from the resolved "
            "sub-values back to front, so a two-element range filter argument arrives "
            "with its bounds swapped and the filter selects the empty set: the F2P "
            "test_range_lookup_namedtuple asserts the query returns exactly the one "
            "matching row, so it does NOT pass. The already-passing "
            "test_range_lookup_allows_F_expressions_and_expressions_for_integers breaks "
            "for the same reason."
        ),
        "rationale": (
            "REJECTED by the ORDER half of clause (d): the postcondition pins element i "
            "of the result to the resolution of element i of the input ('in order'), a "
            "demand independent of totality (a), kind (c) and the length/content the "
            "other (d) rivals attack — this rival satisfies all of those. Attacks the "
            "element-list component of the `v` binder. If it VERIFIES => SPEC-TOO-WEAK "
            "(the rebuilt order would be unpinned, which for a two-bound range argument "
            "is a silently wrong result rather than an error)."
        ),
        # Order is only observable at length >= 2 with DISTINCT elements, and only on a
        # kind the rival still returns a value for: a bundle-taking sequence at the two
        # boundary values. gold => [51,100], rival => [100,51].
        "witness": _wit_value(
            "(fun _ => Value.scalar 0)",
            "(Value.seq Container.plain [Value.scalar 51, Value.scalar 100])",
            "two distinct elements: gold rebuilds in order, the rival reverses them"),
    },
    {
        "id": "weak-special-kind-drops-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_ELEM,
        "refinement": (
            "nagini's partial-domain rival ported to the same sub-domain: correct on "
            "every other container kind and on the empty sequence, but one element short "
            "for a non-empty sequence of the individually-supplied kind. Its faithful "
            "counterpart rebuilds that container from one fewer sub-value, so its "
            "constructor either raises for too few arguments or produces the wrong "
            "bounds; the F2P test_range_lookup_namedtuple asserts the query returns "
            "exactly the one matching row and does NOT pass either way."
        ),
        "rationale": (
            "REJECTED by the LENGTH half of clause (d): the postcondition pins the "
            "rebuilt sequence to the element-wise image of the WHOLE input list, hence "
            "to the same length. Note the kind is preserved and a result IS produced, so "
            "clauses (a) and (c) are satisfied — this rival isolates length. It is a "
            "PARTIAL-DOMAIN rival (correct everywhere except non-empty sequences of one "
            "kind), so its witness is stated on exactly that sub-domain. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # Non-empty sequence of the individually-supplied kind: gold => 2 elements,
        # rival => 1. (On the empty sequence and on other kinds the rival agrees, so the
        # witness must sit here.)
        "witness": _wit_value(
            "(fun _ => Value.scalar 0)", _V_SPECIAL_2,
            "a two-element sequence of the individually-supplied kind: gold rebuilds "
            "both elements, the rival drops one"),
    },
    {
        "id": "weak-expression-unresolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EXPR_UNRESOLVED,
        "refinement": (
            "A resolvable value is returned as-is instead of being replaced by its "
            "resolved form. Its faithful counterpart hands the caller the unresolved "
            "object, so a filter argument that is itself resolvable is never resolved "
            "and compiles to the wrong SQL — it breaks the P2P "
            "test_expressions_in_lookups_join_choice and "
            "test_complex_expressions_do_not_introduce_sql_injection_via_untrusted_string_inclusion "
            "(both rely on the resolution of a resolvable filter argument). Does NOT "
            "resolve. (AUDIT NOTE: the shipped prose also claimed the F2P test; removed "
            "for the same reason as weak-elements-unresolved — the F2P filter argument "
            "is a sequence whose elements carry no sub-structure, so it never reaches "
            "this rival's arm at all.)"
        ),
        "rationale": (
            "REJECTED by the DISPATCH clause (b): the postcondition pins a resolvable "
            "value to `resolveExpr` of its identifier, not to itself. This is the only "
            "clause stated purely in terms of the `resolveExpr` binder, so the witness "
            "varies that binder AGAIN and differently from every other case — it uses a "
            "resolver depending on the identifier, so no coincidence of a constant "
            "resolver can make the rival agree. Moves `v` onto the third constructor, "
            "the one no other rival probes. If it VERIFIES => SPEC-TOO-WEAK (the "
            "resolution of a resolvable value would be unpinned)."
        ),
        # The bare resolvable constructor, with an identifier-DEPENDENT resolver:
        # gold => scalar 4, rival => the unresolved value.
        "witness": _wit_value(
            "(fun k => Value.scalar (Int.ofNat k + 1))", "(Value.expr 3)",
            "a resolvable value under an identifier-dependent resolver: gold returns "
            "its resolved form, the rival returns it unchanged"),
    },

    # ------------------------------------------------- rivals added by the AUDIT
    {
        "id": "weak-bundle-kinds-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KIND_SWAP,
        "refinement": (
            "The two container kinds that SHARE a rebuild convention are swapped for "
            "each other: a sequence of the first bundle-taking kind comes back tagged as "
            "the second. Its faithful counterpart hands the caller a container of the "
            "wrong concrete type, so a filter argument of the first kind is rebuilt as "
            "the second; the P2P "
            "test_in_lookup_allows_F_expressions_and_expressions_for_integers filters "
            "with arguments of the first kind and receives the wrong type back. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the KIND-PRESERVATION clause (c), at the kind PAIR the shipped "
            "battery never separated. Every other kind-sensitive rival moves the "
            "`.special` arm, so all of them are refuted by an input carrying that kind — "
            "which means the distinction between the two kinds that share a rebuild "
            "convention was attested by no case at all, even though pinning exactly that "
            "distinction is the stated reason the kind enumeration is three-valued rather "
            "than two-valued. This case supplies the missing attestation. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the exact rebuilt type would be unpinned between the two "
            "kinds that are easiest to confuse)."
        ),
        # A sequence of the first bundle-taking kind: gold keeps that kind, the rival
        # re-tags it as the second. The .special arm is untouched, so the refutation has
        # to sit on this kind.
        "witness": _wit_value(
            "(fun _ => Value.scalar 0)",
            "(Value.seq Container.plain [Value.scalar 51, Value.scalar 100])",
            "one bundle-taking kind: gold preserves it, the rival re-tags the rebuilt "
            "sequence as the other bundle-taking kind"),
    },
    {
        "id": "weak-elements-resolved-one-level",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SHALLOW_DEPTH,
        "refinement": (
            "The element-wise step resolves each element only ONE level deep: a "
            "resolvable element is replaced by its resolved form, but an element that is "
            "itself a sequence is copied over whole, with its own sub-elements left "
            "unresolved. Its faithful counterpart recurses one level instead of fully, so "
            "a NESTED filter argument compiles with its inner resolvable sub-values "
            "unresolved and the query selects the wrong rows. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ELEMENT-WISE CONTENT clause (d), at the DEPTH the shipped "
            "battery left unattacked. `weak-elements-unresolved` deletes the resolution "
            "step outright, so it is already refuted at depth one and says nothing about "
            "whether the step must RECURSE; the spec's reference resolution is a "
            "structural recursion, and this rival is the near-miss that performs the step "
            "but stops descending — the likeliest honest slip, and the one a rival "
            "attacking only depth one cannot distinguish. Its witness therefore needs a "
            "sequence nested inside a sequence, which no other case in the battery uses. "
            "If it VERIFIES => SPEC-TOO-WEAK (the recursion depth would be unpinned)."
        ),
        # A sequence whose element is ITSELF a sequence over a resolvable sub-expression.
        # At depth one the rival agrees with gold, so the witness must nest: gold
        # resolves the inner element, the rival leaves the inner sequence untouched.
        "witness": _wit_value(
            "(fun _ => Value.scalar 7)",
            "(Value.seq Container.plain [Value.seq Container.plain [Value.expr 1]])",
            "a sequence nested inside a sequence: gold resolves the inner "
            "sub-expression, the rival copies the inner sequence over unresolved"),
    },
]


# No consumed axiom and no opaque callee: the single-expression resolution is a
# universally-quantified PARAMETER, and the rebuild is modeled deeply over a
# transparent inductive carrier. The axiom lane is G-AX's job regardless, and this gate
# ignores it — see the nagini sibling's AXIOM_TESTS, which are deliberately not ported.
AXIOM_TESTS = []
