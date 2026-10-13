# properties.py — G-PBT falsification battery for pydata__xarray-3151 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive reproves, the proof body — is edited), checked by
# variant_scope before the verifier runs. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the postcondition rather than
# to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#
#   implementation_monotonicCheck (dims : List Dim) : Except String Unit
#
#   `Dim` records four observations per dimension of a freshly combined object:
#   `name`, `isCoordDim` (it carries a coordinate index), `variesBetweenInputs` (the
#   inputs were combined across it, as opposed to a bystander dimension identical in
#   every input) and `isMonotonic` (its global index is monotonic in either
#   direction).
#
#   The single obligation is
#       theorem correct_monotonicCheck : ∀ (dims : List Dim),
#         problem_spec_monotonicCheck dims (implementation_monotonicCheck dims)
#   with the one load-bearing postcondition clause
#       result = (match firstNonMonotonicVarying dims with
#                 | some n => Except.error n | none => Except.ok ())
#   where `firstNonMonotonicVarying` is a front-recursive fold FULLY GROUNDED in the
#   input carrier (no opaque callee, no answer-key oracle). It pins FIVE separable
#   decisions at once, and the rival lane attacks each:
#     (1) WHICH dimensions are subjected to the requirement — exactly those with
#         `variesBetweenInputs`; `isCoordDim` is read by NO clause, so a bystander
#         coordinate dimension must never affect the outcome;
#     (2) THAT the requirement is monotonicity — a dimension combined across the
#         inputs is reported only when `!isMonotonic`;
#     (3) WHICH offender is reported when several qualify — the FIRST in carrier
#         order;
#     (4) WHICH label the report carries — the offending dimension's own `name`;
#     (5) the success case — every dimension of the carrier is examined (no
#         position skipped) and an empty carrier succeeds.
#
#   There is no precondition: the obligation binds `dims` universally, so the spec is
#   total over every `List Dim`. The carrier is fully TRANSPARENT (a list of a
#   `deriving DecidableEq` record of `String`/`Bool` fields), so every witness states
#   its refutation at a concrete literal input and needs no conditioning on an opaque
#   term.
#
# CARRIER NOTE (how the nagini rivals become these): the nagini sibling abstracted
# the same decision to a bool-valued existential over TWO parallel `List[int]` flag
# vectors (`is_joined` / `is_monotonic`) behind fractional read permission, answering
# only "would this be rejected at all". This backend models the SAME decision over
# one `List Dim` of records returning `Except String Unit`, which is strictly RICHER:
# the outcome carries WHICH dimension is reported, and each dimension's coordinate-
# ness is a third observation the flag-vector model did not carry. So every nagini
# value rival has a direct counterpart here, and the extra structure admits three
# rivals nagini's carrier could not express at all (report-ordering, report-label,
# and the coordinate-vs-combined discrimination).
#
# LANES THAT DO NOT PORT (see 'assessment' for the full accounting):
#   * FRAME-MUTATION — nagini's MANDATORY class (both inputs were held at half
#     permission and the rival wrote back into one). Lean is referentially
#     transparent: no aliasing, no fractional permission, and `dims` cannot be
#     stored into. The class is genuinely VACUOUS here, not omitted.
#   * DIVERGENCE / NON-TERMINATION — nagini's `vacuous-nonterminating-loop` rival
#     spun forever so that every value clause held vacuously, and was rejected by the
#     total-correctness obligation. Recorded here as a KNOWN HOLE, not as a vacuous
#     class. An earlier revision of this file claimed "a diverging implementation
#     cannot be WRITTEN at all"; that claim is FALSE and was corrected by an audit
#     that measured it. The frozen impl is an `Id.run do` block, and an unbounded
#     `while true do pure ()` prefixed to it is accepted by `variant_scope` (no
#     `partial`, no new axiom) and VERIFIES against the frozen obligation with the
#     frozen proof script unchanged (built: exit 0). The reason is not that the
#     obligation discharges a termination measure — it is that `Lean.Loop.mk`'s
#     `forIn` in the `Id` monad is DEFINITIONALLY ERASED when its result is
#     discarded: `example : (Id.run do while true do pure (); return 5) = 5 := rfl`
#     closes, and `#eval` of the loop-prefixed impl returns the ordinary answer
#     rather than hanging. So the rival is not observably diverging on this carrier
#     — it is `rfl`-equal to the frozen impl, which makes the case VACUOUS in the
#     attack-C sense rather than shippable, and no witness can refute it.
#     A loop whose value IS consumed (`let mut spin := 0; while true do spin := spin
#     + 1; if spin = 0 then …`) is instead REJECTED (built: exit 1, `Tactic 'rfl'
#     failed` on the unreduced `forIn Lean.Loop.mk` term) — but that rejection is a
#     tactic mismatch, and the refutation cannot be witnessed: a hypothesis-
#     conditioned witness `(h : impl input = Except.ok ()) : ¬ problem_spec …`
#     elaborates against BOTH the rival AND the frozen solution (both exit 0),
#     because the hypothesis is equally unrefutable on either side, so it
#     discriminates nothing. There is therefore nothing shippable in this lane on
#     this carrier; the disposition is a hole in what the obligation can observe,
#     recorded rather than papered over.
#   * AXIOM_TESTS — the axiom lane is G-AX's job and this gate ignores them. The
#     decision is modeled DEEPLY over the grounded per-dimension observations, so the
#     axioms region is empty and there is no consumed contract to probe.
from pathlib import Path

INSTANCE = "pydata__xarray-3151"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside one region of the frozen file and is
# unique there, so every variant is attributable to the impl (plus, for a
# reproving positive, the proof body). The frozen spec view is never touched.
# ---------------------------------------------------------------------------
_IMPL_HEAD = ("def implementation_monotonicCheck (dims : List Dim) : "
              "Except String Unit := Id.run do\n")
_CARRIER = "  for d in dims do\n"
_GUARD = ("    if d.variesBetweenInputs && !d.isMonotonic then\n"
          "      return Except.error d.name\n")
_TAIL = "  return Except.ok ()\n"
_IMPL_BODY = _CARRIER + _GUARD + _TAIL

_PROOF = """  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck
  induction dims with
  | nil => rfl
  | cons d rest ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (d.variesBetweenInputs && !d.isMonotonic) = true
    · simp only [h, if_true, firstNonMonotonicVarying, pure]
    · simp only [h, firstNonMonotonicVarying, ih, if_false, reduceCtorEq]
"""

for _a in (_IMPL_HEAD, _CARRIER, _GUARD, _TAIL, _IMPL_BODY, _PROOF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted (count={_BASE.count(_a)}): {_a!r}")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
#
# Each is a structurally DIFFERENT but behaviourally IDENTICAL implementation, i.e.
# a shape a faithful real change could equally have taken. On this backend a
# reshaped impl generally breaks the frozen tactic script, so where that happens
# the proof is honestly RE-CLOSED inside proof-start/proof-end: the
# `theorem correct_monotonicCheck` STATEMENT stays byte-identical, and no new
# axiom / lemma / `sorry` / `native_decide` is introduced. All four were built and
# observed to verify.
# ===========================================================================

# pos-nested-guard: the single conjunctive test is split into two nested tests —
# first "was this dimension combined across the inputs", then "is its index
# non-monotonic". Same carrier, same order, same verdict on every input; only the
# branch FORM changes. The frozen script's single `by_cases` on the conjunction no
# longer matches the two-level branch tree, so the proof is re-closed by casing on
# each observation separately (still the same induction, no new lemma).
_POS_NESTED = _swap(
    _swap(_BASE, _GUARD,
          "    if d.variesBetweenInputs then\n"
          "      if !d.isMonotonic then\n"
          "        return Except.error d.name\n"),
    _PROOF,
    """  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck
  induction dims with
  | nil => rfl
  | cons d rest ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases hv : d.variesBetweenInputs = true
    · by_cases hm : d.isMonotonic = true
      · simp only [hv, hm, firstNonMonotonicVarying, ih, if_false, if_true,
          Bool.not_true, Bool.and_false, reduceCtorEq, Bool.true_and]
      · simp only [hv, hm, firstNonMonotonicVarying, if_true, pure,
          Bool.not_false, Bool.and_true, Bool.true_and,
          Bool.not_eq_true, Bool.eq_false_iff]
    · simp only [hv, firstNonMonotonicVarying, ih, if_false, Bool.false_and,
        Bool.not_eq_true, reduceCtorEq]
""",
)

# pos-bind-observations: the two observations are bound to locals before the test
# (the local-variable reshape the nagini sibling's `pos-head-locals` used). Purely
# a naming change, so even the frozen proof script still closes — the cleanest
# possible check that the postcondition is not over-fit to one spelling.
_POS_LOCALS = _swap(
    _BASE, _GUARD,
    "    let varies := d.variesBetweenInputs\n"
    "    let mono := d.isMonotonic\n"
    "    if varies && !mono then\n"
    "      return Except.error d.name\n",
)

# pos-filter-carrier: the STRUCTURALLY most distant correct shape — instead of
# walking every dimension and testing whether it was combined across the inputs,
# first narrow the carrier to the combined dimensions and then test only
# monotonicity. Order-preserving, so the same offender is reported first; this is
# the very equivalence recorded in refinement.md for the modeled loop, tested here
# as an implementation rather than assumed. Needs a genuine reproof (the induction
# now steps a `List.filter`), closed without any new lemma.
_POS_FILTER = _swap(
    _swap(_BASE, _IMPL_BODY,
          "  for d in dims.filter (fun d => d.variesBetweenInputs) do\n"
          "    if !d.isMonotonic then\n"
          "      return Except.error d.name\n"
          + _TAIL),
    _PROOF,
    """  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck
  induction dims with
  | nil => rfl
  | cons d rest ih =>
    simp only [List.filter_cons] at ih ⊢
    by_cases hv : d.variesBetweenInputs = true
    · simp only [hv, if_true, List.forIn_cons, Id.run, bind] at ih ⊢
      by_cases hm : d.isMonotonic = true <;>
        simp_all [firstNonMonotonicVarying, pure]
    · simp_all [firstNonMonotonicVarying]
""",
)

# pos-direct-oracle: the cheapest HONEST implementation — read the grounded fold
# and translate its answer. This is not an ungrounded-oracle echo:
# `firstNonMonotonicVarying` is a total transparent recursion over the argument
# (SPEC_GUIDE §0.8), so returning its answer IS doing the work, and any wrong
# constant still fails the postcondition. Proof collapses to `rfl`.
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL_HEAD + _IMPL_BODY,
          "def implementation_monotonicCheck (dims : List Dim) : "
          "Except String Unit :=\n"
          "  match firstNonMonotonicVarying dims with\n"
          "  | some n => Except.error n\n"
          "  | none => Except.ok ()\n"),
    _PROOF,
    "  intro dims\n"
    "  unfold problem_spec_monotonicCheck implementation_monotonicCheck\n"
    "  rfl\n",
)


# ===========================================================================
# ADMISSIBILITY — must VERIFY, else PRECOND-TOO-STRONG / SPEC-TOO-STRONG.
# ===========================================================================

# admiss-bystander-shaped: the counterpart of the nagini sibling's `admiss-f2p-
# bystander`. There, a call-free probe built the F2P-shaped input, asserted every
# value clause of the read-permission precondition on it, and asserted the grounded
# oracle yields the F2P answer on it. Here the obligation binds `dims` universally
# with NO precondition hypothesis, so there is nothing that could REJECT an input
# and the "precondition admits it" half is vacuous. What remains — and what this
# case tests — is the half that still has content: the spec PINS the expected
# answer on the discriminating input shape.
#
# The probe is expressed as an in-region special case: on the single-dimension
# carrier whose one dimension is a non-monotonic BYSTANDER coordinate
# (isCoordDim=true, variesBetweenInputs=false, isMonotonic=false) the impl returns
# success DIRECTLY, without consulting the scan. The obligation then only closes if
# the spec independently pins that input's answer to `Except.ok ()`. The remaining
# domain keeps the frozen scan verbatim, discharged by the frozen induction lifted
# into a `have` over the general carrier (a proof-region reorganisation, not a new
# top-level lemma — `variant_scope` bans those and none is added).
#
# SENSITIVITY CHECKED: replacing the probe branch's `Except.ok ()` with
# `Except.error "y"` makes the case FAIL to verify (observed), so the case is not
# passing vacuously — it really is the spec that supplies the answer.
_ADMISS = _swap(
    _swap(_BASE, _CARRIER,
          "  if dims == [⟨\"y\", true, false, false⟩] then\n"
          "    return Except.ok ()\n"
          + _CARRIER),
    _PROOF,
    """  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck
  have key : ∀ (l : List Dim),
      (Id.run (do
        for d in l do
          if d.variesBetweenInputs && !d.isMonotonic then
            return Except.error d.name
        return Except.ok ())) =
      (match firstNonMonotonicVarying l with
       | some n => Except.error n
       | none => Except.ok ()) := by
    intro l
    induction l with
    | nil => rfl
    | cons d rest ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : (d.variesBetweenInputs && !d.isMonotonic) = true
      · simp only [h, if_true, firstNonMonotonicVarying, pure]
      · simp only [h, firstNonMonotonicVarying, ih, if_false, reduceCtorEq]
  by_cases hp : dims == [⟨"y", true, false, false⟩]
  · simp only [beq_iff_eq] at hp
    subst hp
    simp [Id.run, firstNonMonotonicVarying, pure]
  · simp only [hp, Bool.false_eq_true, if_false]
    exact key dims
""",
)

# admiss-f2p-two-dim: the SECOND admissibility positive, added by the audit
# because `admiss-bystander-shaped` tests the obligation only at a SINGLE-dimension
# carrier — a shape the modeled scenario never actually presents. The scenario the
# F2P observes has TWO dimensions: one genuinely combined across the inputs whose
# global index IS monotonic, followed by the non-monotonic BYSTANDER coordinate.
# That two-element carrier is where the two decisions interact — the scan must
# accept the first dimension on its merits AND skip the second under the bystander
# rule — and no other case in this battery reaches it.
#
# The shape this lane calls for on a total carrier: discharge the obligation at
# that exact concrete input, BY EVALUATION, as a `have`, before closing the frozen
# obligation VERBATIM. Both `have`s are proof-region reorganisation — no new
# top-level lemma, no axiom, no sorry, no native_decide — and the frozen impl, the
# frozen `theorem correct_monotonicCheck` statement AND its frozen tactic script
# are all kept byte-identical. So this case cannot pass by weakening anything: the
# `have`s either evaluate to the spec's own answer at that input or they do not.
#
# SENSITIVITY MEASURED (both variants built, both exit 1):
#   * asserting the F2P input is REPORTED (`= Except.error "y"`) instead of
#     accepted => `Tactic 'rfl' failed`;
#   * flipping the bystander to variesBetweenInputs=true — so the spec then demands
#     a report — with the `= Except.ok ()` claim kept => `Tactic 'rfl' failed`.
# So a pass tracks the spec's answer at this input rather than the branch shape.
_F2P_CARRIER = "[⟨\"x\", true, true, true⟩, ⟨\"y\", true, false, false⟩]"
_ADMISS_F2P = _swap(
    _BASE, _PROOF,
    f"  have f2p_ok : implementation_monotonicCheck {_F2P_CARRIER}\n"
    "      = Except.ok () := by\n"
    "    unfold implementation_monotonicCheck\n"
    "    rfl\n"
    f"  have f2p : problem_spec_monotonicCheck {_F2P_CARRIER}\n"
    f"      (implementation_monotonicCheck {_F2P_CARRIER}) := by\n"
    "    unfold problem_spec_monotonicCheck\n"
    "    rw [f2p_ok]\n"
    "    simp [firstNonMonotonicVarying]\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK.
#
# Each shares the frozen spec exactly, edits only the impl region, and leaves the
# frozen proof body in place (it will not close for the reshaped impl — which is
# precisely why the gate reads the WITNESS instead). Every witness below was built
# BOTH ways and observed to discriminate: it elaborates against its rival and, on
# the frozen solution, reduces to `⊢ False`.
# ===========================================================================

# Subject every COORDINATE dimension to the requirement instead of only those
# combined across the inputs. Attacks clause (1) via `isCoordDim`.
_RIV_COORD_GUARD = _swap(
    _BASE, _GUARD,
    "    if d.isCoordDim && !d.isMonotonic then\n"
    "      return Except.error d.name\n")

# Subject EVERY dimension to the requirement — no membership test at all. Attacks
# clause (1) on the sub-domain a coordinate-based guard still gets right.
_RIV_NO_GUARD = _swap(
    _BASE, _GUARD,
    "    if !d.isMonotonic then\n"
    "      return Except.error d.name\n")

# Never report anything. Attacks clause (2)'s error side.
_RIV_ALWAYS_OK = _swap(_BASE, _IMPL_BODY, _TAIL)

# Report the first dimension unconditionally — both observations ignored.
_RIV_ALWAYS_ERR = _swap(_BASE, _GUARD, "    return Except.error d.name\n")

# Report the first COMBINED dimension whether or not its index is monotonic:
# the membership test is kept, the monotonicity test dropped. Attacks clause (2).
_RIV_IGNORE_MONO = _swap(
    _BASE, _GUARD,
    "    if d.variesBetweenInputs then\n"
    "      return Except.error d.name\n")

# Report the LAST qualifying dimension rather than the first. Attacks clause (3);
# has no nagini counterpart (that carrier's answer was a bare bool).
_RIV_LAST = _swap(
    _BASE, _IMPL_BODY,
    "  let mut found : Option String := none\n"
    "  for d in dims do\n"
    "    if d.variesBetweenInputs && !d.isMonotonic then\n"
    "      found := some d.name\n"
    "  match found with\n"
    "  | some n => return Except.error n\n"
    "  | none => return Except.ok ()\n")

# Never examine the first position of the carrier. Attacks clause (5); the
# counterpart of the nagini sibling's `weak-skip-head-dimension`.
_RIV_SKIP_FIRST = _swap(_BASE, _CARRIER, "  for d in dims.drop 1 do\n")

# Report a fixed label instead of the offending dimension's own name. Attacks
# clause (4); has no nagini counterpart.
_RIV_FIXED_LABEL = _swap(
    _BASE, _GUARD,
    "    if d.variesBetweenInputs && !d.isMonotonic then\n"
    "      return Except.error \"dim\"\n")

# Report when there is nothing to examine at all. Attacks clause (5)'s base case;
# the counterpart of the nagini sibling's `weak-const-true` empty-input argument.
_RIV_EMPTY_ERR = _swap(
    _BASE, _CARRIER,
    "  if dims.isEmpty then\n"
    "    return Except.error \"\"\n"
    + _CARRIER)


def _wit(dims, note):
    """A refutation witness: `¬ problem_spec_monotonicCheck dims (implementation…
    dims)` at one concrete literal carrier, discharged by computing both sides.

    The carrier is transparent (`Dim` derives `DecidableEq` over `String`/`Bool`),
    so no conditioning on an opaque term is needed and the witness head binds
    NOTHING — there are no hypotheses that could be jointly unsatisfiable.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_monotonicCheck {dims}\n"
        f"    (implementation_monotonicCheck {dims}) := by\n"
        f"  unfold problem_spec_monotonicCheck implementation_monotonicCheck\n"
        f"  simp [Id.run, firstNonMonotonicVarying]\n"
        f"  try simp [pure]"
    )


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-nested-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NESTED,
        "rationale": (
            "structurally-different but CORRECT impl: the single conjunctive "
            "per-dimension test is split into two nested tests (first whether the "
            "dimension was combined across the inputs, then whether its index is "
            "non-monotonic). Identical carrier, identical order, identical outcome "
            "on every input — a shape a faithful change could equally take. The "
            "frozen `theorem correct_monotonicCheck` STATEMENT is kept "
            "byte-identical and the proof body is honestly re-closed by casing on "
            "each observation separately (same induction, no new axiom/lemma/sorry). "
            "If it FAILS => SPEC-TOO-STRONG: the postcondition would be over-fit to "
            "one branch spelling of the same decision."
        ),
    },
    {
        "id": "pos-bind-observations",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCALS,
        "rationale": (
            "local-variable reshape (the nagini sibling's `pos-head-locals`): the "
            "two per-dimension observations are bound to locals before being "
            "tested. Behaviourally identical, and close enough in form that even the "
            "frozen tactic script still closes — so this case isolates SPEC strength "
            "from proof brittleness: it must verify on the postcondition's own "
            "terms. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-filter-carrier",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FILTER,
        "rationale": (
            "the structurally most distant CORRECT impl: narrow the carrier to the "
            "dimensions combined across the inputs FIRST, then test only "
            "monotonicity, rather than walking every dimension and testing "
            "membership per step. Order-preserving, so the same offender is reported "
            "first. refinement.md records exactly this equivalence for the modeled "
            "loop; shipping it as a positive TESTS that equivalence against the "
            "postcondition instead of assuming it. Needs a genuine reproof (the "
            "induction now steps a filtered carrier), closed with no new "
            "axiom/lemma/sorry and a byte-identical theorem statement. If it FAILS "
            "=> SPEC-TOO-STRONG (and the recorded refinement leg would be suspect)."
        ),
    },
    {
        "id": "pos-direct-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the cheapest HONEST impl: read the grounded fold the postcondition "
            "names and translate its answer into the result type; proof collapses to "
            "`rfl`. Not an ungrounded-oracle echo — the fold is a total transparent "
            "recursion over the argument with no opaque callee (SPEC_GUIDE §0.8), so "
            "computing it IS doing the work and every wrong constant still fails the "
            "postcondition (see the reject lane, which refutes two constant impls). "
            "Must verify, since the postcondition literally equates the result to "
            "that fold's answer; else SPEC-TOO-STRONG."
        ),
    },

    # ---------------- admissibility (must VERIFY) ----------------
    {
        "id": "admiss-bystander-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the counterpart of the nagini sibling's `admiss-f2p-bystander`. That "
            "case asserted (a) every value clause of the read-permission "
            "precondition holds of the discriminating input shape and (b) the "
            "grounded oracle yields the expected answer on it. Half (a) is vacuous "
            "here — the obligation binds `dims` universally with NO precondition "
            "hypothesis, so no input can be refused and PRECOND-TOO-STRONG is "
            "unreachable by construction. Half (b) still has content and is what "
            "this case checks: an in-region special case returns SUCCESS directly on "
            "the single-dimension carrier whose one dimension is a non-monotonic "
            "BYSTANDER coordinate (isCoordDim=true, variesBetweenInputs=false, "
            "isMonotonic=false), consulting no scan; the obligation therefore closes "
            "only if the spec INDEPENDENTLY pins that input's answer to "
            "`Except.ok ()`. The rest of the domain keeps the frozen scan verbatim, "
            "discharged by the frozen induction lifted into a proof-local `have` (a "
            "proof-region reorganisation; no new top-level lemma, axiom or sorry, "
            "theorem statement byte-identical). Sensitivity was checked by hand: "
            "with the probe branch returning an error instead, the case FAILS to "
            "verify — so a pass is attributable to the spec, not to the branch. If "
            "it FAILS => SPEC-TOO-STRONG on the very input shape the modeled "
            "behavior exists to get right."
        ),
    },

    {
        "id": "admiss-f2p-two-dim",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_F2P,
        "rationale": (
            "the admissibility lane at the carrier shape the modeled scenario "
            "actually presents, added by audit because the sibling admissibility "
            "case reaches only a SINGLE-dimension carrier. Here the carrier has "
            "TWO dimensions: one combined across the inputs whose global index IS "
            "monotonic, followed by the non-monotonic BYSTANDER coordinate. That is "
            "where the two decisions interact — the scan must accept the first "
            "dimension on its merits and skip the second under the bystander rule — "
            "and no other case in this battery reaches it. On this total carrier the "
            "obligation binds `dims` universally with no precondition, so nothing "
            "can REFUSE an input; the analogue with content is the obligation being "
            "unsatisfiable at an F2P-shaped input, which this case tests directly by "
            "discharging it at that concrete input BY EVALUATION as a `have` before "
            "closing the frozen obligation VERBATIM. The frozen impl, the frozen "
            "theorem statement and the frozen tactic script are all byte-identical, "
            "so no weakening is available to it. Sensitivity measured both ways "
            "(claiming the input is reported, and flipping the bystander to varying "
            "while keeping the success claim): both FAIL to verify, so the pass is "
            "attributable to the spec's answer at this input. If it FAILS => "
            "PRECOND/SPEC-TOO-STRONG at exactly the shape the modeled behavior "
            "exists to get right."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "weak-coordinate-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_COORD_GUARD,
        "refinement": (
            "This is the PRE-CHANGE decision: subject every dimension that carries a "
            "coordinate index to the monotonicity requirement, instead of only the "
            "dimensions actually combined across the inputs. Its faithful real "
            "counterpart validates a bystander coordinate — one identical in every "
            "input and therefore carried through rather than combined — and so "
            "rejects a combine that must succeed, raising on the non-monotonic "
            "bystander coordinate of the F2P scenario. "
            "test_combine_leaving_bystander_dimensions never reaches its "
            "assert_identical and FAILS, so a verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition clause fixing WHICH dimensions are "
            "subjected to the requirement: the result must equal the fold guarded on "
            "`variesBetweenInputs`, and NO clause of the spec reads `isCoordDim` at "
            "all. Attacks that clause on the sub-domain isCoordDim=true ∧ "
            "variesBetweenInputs=false ∧ isMonotonic=false. If it VERIFIES => "
            "SPEC-TOO-WEAK, and the modeled behavior would be undefended exactly "
            "where it matters."
        ),
        # A lone non-monotonic BYSTANDER coordinate: gold => ok (),
        # rival => error "y". Built both ways; gold's build reduces to ⊢ False.
        "witness": _wit('[⟨"y", true, false, false⟩]',
                        "lone non-monotonic bystander coordinate: the spec "
                        "demands success, the rival reports it"),
    },
    {
        "id": "weak-no-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_GUARD,
        "refinement": (
            "Drop the membership test entirely: subject EVERY dimension to the "
            "requirement, whether or not it carries a coordinate index and whether "
            "or not it was combined across the inputs. A faithful real counterpart "
            "rejects strictly more combines than the pre-change one already did, so "
            "it fails the F2P for the same reason and additionally over-rejects "
            "non-coordinate dimensions that were never validated at all — it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the same WHICH-dimensions clause, but on a DISJOINT "
            "sub-domain from weak-coordinate-guard: its witness dimension is not a "
            "coordinate dimension (isCoordDim=false), where a coordinate-based guard "
            "still agrees with the spec. Refuting it separately is what shows the "
            "spec pins `variesBetweenInputs` specifically rather than merely 'some "
            "membership test' — and it is why the two rivals do not share a witness "
            "(checked: this input does NOT refute weak-coordinate-guard). If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # A non-monotonic NON-coordinate dimension: gold => ok (), rival =>
        # error "z"; the coordinate-guard rival agrees with gold here.
        "witness": _wit('[⟨"z", false, false, false⟩]',
                        "non-monotonic non-coordinate dimension: the spec demands "
                        "success, the rival reports it"),
    },
    {
        "id": "weak-never-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_OK,
        "refinement": (
            "Never report anything — the counterpart of the nagini sibling's "
            "`weak-const-false`. A faithful real counterpart drops the rejection "
            "outright, so a genuinely non-monotonic COMBINED dimension is accepted "
            "silently. The post-change behavior must still reject that case, and a "
            "P2P test asserts the rejection with its dimension named "
            "(test_check_for_impossible_ordering), so this would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the error side of the postcondition: on a dimension both "
            "combined across the inputs and non-monotonic the spec pins the result "
            "to `Except.error` on that dimension's name, and the rival returns "
            "success. Attacks clause (2)'s error side / the "
            "variesBetweenInputs=true ∧ isMonotonic=false sub-domain. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the spec would be satisfiable by never rejecting "
            "anything)."
        ),
        # varying + non-monotonic: gold => error "x", rival => ok ().
        "witness": _wit('[⟨"x", true, true, false⟩]',
                        "a combined non-monotonic dimension: the spec demands it be "
                        "reported, the rival succeeds"),
    },
    {
        "id": "weak-report-first-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_ERR,
        "refinement": (
            "Report the first dimension unconditionally — both observations ignored. "
            "Its faithful real counterpart rejects every combine that has any "
            "dimension at all, so neither the F2P scenario nor the ordinary "
            "combines covered by the P2P suite return their expected object; it "
            "would NOT resolve. The over-strict opposite of the nagini sibling's "
            "`weak-const-true`."
        ),
        "rationale": (
            "REJECTED by the success side of the postcondition: on a carrier with no "
            "qualifying dimension the spec pins the result to `Except.ok ()`. "
            "Attacks clause (5) at a point where BOTH observations are individually "
            "'safe' (variesBetweenInputs=false, isMonotonic=true), which no other "
            "rival's witness probes. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # a clean bystander, nothing to report: gold => ok (), rival => error "b".
        "witness": _wit('[⟨"b", false, false, true⟩]',
                        "a monotonic bystander dimension: the spec demands success, "
                        "the rival reports it anyway"),
    },
    {
        "id": "weak-ignore-monotonicity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_MONO,
        "refinement": (
            "Keep the membership test but drop the monotonicity test: report the "
            "first dimension combined across the inputs regardless of its global "
            "index. A faithful real counterpart rejects every combine that "
            "concatenates along anything at all — including the F2P scenario, whose "
            "combined dimension IS monotonic — so assert_identical is never reached; "
            "it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the clause fixing WHAT is required of a combined dimension: "
            "the spec pins the result to success when every combined dimension is "
            "monotonic. Attacks clause (2)'s success side / the "
            "variesBetweenInputs=true ∧ isMonotonic=true sub-domain — a NEAR-MISS of "
            "weak-report-first-always that agrees with gold wherever nothing was "
            "combined, so it gets its own discriminating input (checked: this rival "
            "is NOT refuted at the bystander input above). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # combined AND monotonic: gold => ok (), rival => error "m".
        "witness": _wit('[⟨"m", true, true, true⟩]',
                        "a combined MONOTONIC dimension: the spec demands success, "
                        "the rival reports it"),
    },
    {
        "id": "weak-report-last-offender",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LAST,
        "refinement": (
            "Report the LAST qualifying dimension instead of the first. A faithful "
            "real counterpart scans on without stopping and rejects naming the final "
            "offender, so on an object with two offending combined dimensions the "
            "reported dimension differs from the post-change behavior. A P2P test "
            "matches the rejection message against a specific dimension name "
            "(test_check_for_impossible_ordering), so the mismatch is observed and "
            "it would NOT resolve. No nagini counterpart: that carrier's answer was "
            "a bare bool, so it could not express WHICH offender is named."
        ),
        "rationale": (
            "REJECTED by the clause fixing WHICH offender is reported — the FIRST in "
            "carrier order — which the spec's front-recursive fold makes explicit. "
            "Attacks clause (3); the only rival whose witness needs a carrier of "
            "length > 1 with two qualifying dimensions. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would leave the reported label free whenever "
            "several dimensions offend)."
        ),
        # two combined non-monotonic dims: gold => error "a", rival => error "b".
        "witness": _wit('[⟨"a", true, true, false⟩, ⟨"b", true, true, false⟩]',
                        "two offending combined dimensions: the spec names the "
                        "first, the rival names the last"),
    },
    {
        "id": "weak-skip-first-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP_FIRST,
        "refinement": (
            "Never examine the first position of the carrier — the counterpart of "
            "the nagini sibling's `weak-skip-head-dimension`. A faithful real "
            "counterpart begins the scan one dimension in, so an object whose ONLY "
            "offending combined dimension sits first is accepted where the "
            "post-change behavior must still reject it, and when a later dimension "
            "also offends the reported name is the wrong one. The rejection a P2P "
            "test asserts (with its dimension named) is then missed or misnamed, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the clause requiring EVERY position of the carrier to be "
            "examined: the spec's fold starts at the head, so the result on a "
            "carrier whose head qualifies is pinned to the head's name. Attacks "
            "clause (5) / the head-position sub-domain, and is the only rival that "
            "moves the OFFSET at which the carrier is read. If it VERIFIES => "
            "SPEC-TOO-WEAK on the boundary dimension."
        ),
        # head offends, tail is a bystander: gold => error "a", rival => ok ()
        # (the tail's non-monotonicity is a bystander's, so it is not reported).
        "witness": _wit('[⟨"a", true, true, false⟩, ⟨"b", true, false, false⟩]',
                        "the sole offender sits first: the spec names it, the rival "
                        "skips the position and succeeds"),
    },
    {
        "id": "weak-fixed-report-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIXED_LABEL,
        "refinement": (
            "Report a FIXED label rather than the offending dimension's own name. A "
            "faithful real counterpart rejects with a constant dimension name in its "
            "message, which a P2P test matches against the actual offending "
            "dimension (test_check_for_impossible_ordering expects the rejection to "
            "name dimension x), so the assertion fails and it would NOT resolve. No "
            "nagini counterpart: that carrier's answer was a bare bool and carried "
            "no label."
        ),
        "rationale": (
            "REJECTED by the clause fixing WHICH label the report carries — the "
            "offending dimension's own `name` binder, the only non-Bool field of the "
            "carrier and the only one no other rival attacks. Attacks clause (4); "
            "the rival's outcome agrees with the spec on WHETHER to report and on "
            "WHICH dimension qualifies, and differs only in the reported name, so "
            "the witness input is a single offending dimension whose name is not the "
            "constant. If it VERIFIES => SPEC-TOO-WEAK: the reported label would be "
            "left free."
        ),
        # gold => error "q", rival => error "dim".
        "witness": _wit('[⟨"q", true, true, false⟩]',
                        "one offending dimension: the spec names that dimension, "
                        "the rival reports a constant label"),
    },
    {
        "id": "weak-report-empty-carrier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY_ERR,
        "refinement": (
            "Report when there is NOTHING to examine — the empty-input half of the "
            "nagini sibling's `weak-const-true` argument. A faithful real "
            "counterpart rejects whenever no dimension was combined across the "
            "inputs, i.e. exactly the case where the inputs are merged rather than "
            "stacked. A P2P test covers that shape — it asserts the merged object "
            "comes back identical when no dimension needed combining — so the "
            "spurious rejection breaks it and it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the base case of the postcondition's fold: on the empty "
            "carrier the spec pins the result to `Except.ok ()`. Attacks clause (5) "
            "at the length-zero boundary, the one input point no other witness "
            "reaches (every other witness carries at least one dimension, so the "
            "carrier LENGTH is varied across 0, 1 and 2 by the reject lane). If it "
            "VERIFIES => SPEC-TOO-WEAK at the boundary."
        ),
        # the empty carrier: gold => ok (), rival => error "".
        "witness": _wit("([] : List Dim)",
                        "the empty carrier: the spec demands success, the rival "
                        "reports"),
    },
]


# The axioms region of the frozen solution is empty and `opaque_callees` is [] —
# the decision is modeled DEEPLY over the grounded per-dimension observations, so
# there is no consumed callee contract for an axiom probe to attack. The axiom lane
# belongs to G-AX regardless, which records `skip` for this bundle.
AXIOM_TESTS = []
