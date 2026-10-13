# properties.py — G-PBT falsification battery for pydata__xarray-6599 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Every SPEC case
# is a FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the
# impl region — and, for the one positive that reproves, the proof body — differs),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the spec and not to a frozen
# tactic script that merely stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean, mapping.md, instance.json)
#
#   implementation_coerceToFloat (x : ArrayView) : List Float
#
#   One obligation, `theorem correct_coerceToFloat : ∀ x, problem_spec_coerceToFloat
#   x (implementation_coerceToFloat x)`, over the single equation
#
#       result = coerceResult x
#
#   which bundles THREE independent, kind-selected clauses — the whole
#   postcondition is a case split on `x.kind`, so each arm is separately
#   falsifiable and each is separately attacked below:
#
#     (C1) datetime arrays  → the epoch-relative datetime reduction of `x.raw`
#          (`datetimeToFloat x.raw`). The reduction itself is an UNCHANGED callee,
#          carried as `opaque datetimeToFloat` and used identically by spec and
#          impl, so no property of it is consumed — but WHICH inputs reach it, and
#          what is done with its result, are fully pinned. Both halves are now
#          attacked: `weak-datetime-branch-omitted` drops the arm (its result is
#          discarded) and `weak-datetime-reduction-arg-reversed` keeps the call but
#          corrupts its ARGUMENT. Before the audit only the first existed, so the
#          "which inputs reach it" half of this claim was undemonstrated.
#     (C2) duration arrays  → the underlying integer counts cast element-wise to
#          float (`x.raw.map Float.ofInt`). This is the changed rule, modeled
#          deeply, and the clause the FAIL_TO_PASS case observes.
#     (C3) numeric arrays   → `x.data`, unchanged.
#
#   The DECISIVE behavioural fact (the discriminator the frozen prepatch file also
#   pins): a duration array must follow its OWN rule and must NOT be routed
#   through the datetime epoch reduction. The two time-related kinds are coerced
#   by DIFFERENT rules even though both originate from time values. Clause C2 is
#   therefore the load-bearing one, and it is attacked five ways below (routed
#   through the epoch reduction; branch omitted entirely; every magnitude shifted;
#   only the head magnitude corrupted; element order reversed) so that no single
#   sub-domain carries the whole battery.
#
#   FRAME DISCIPLINE (the lean analogue of nagini's read-only obligation): the
#   postcondition pins the ENTIRE result list, with no component left free — the
#   numeric arm is pinned to the input `data` (the unchanged-component framing),
#   the duration arm to the element-wise cast of `raw`, the datetime arm to the
#   carried reduction of `raw`. It is attacked structurally (element ORDER and
#   element COUNT) and by an arm reading the WRONG input view (`raw` where the
#   spec says `data`, and vice versa).
#
# ---------------------------------------------------------------------------
# THE CARRIER, AND WHY MOST WITNESSES CONDITION
#
#   `Float` is opaque to the Lean kernel: `decide` cannot even reduce
#   `Float.ofInt 1000 ≠ Float.ofInt 2000` (measured: "failed to synthesize
#   Decidable"), and `simp`/`rfl`/a `toString` detour all leave the goal open. So a
#   VALUE-level refutation cannot be `decide`d at a literal here, and the datetime
#   arm additionally passes through an `opaque` callee with no constraining axiom.
#   Both are handled by CONDITIONING on the carrier rather than computing it: the
#   refutation is stated at a point described by hypothesis — exactly the sub-domain
#   where the rival's answer is observably different — with ONE hypothesis per
#   witness, kept as weak as the refutation needs so the assumptions are jointly
#   satisfiable (each was probed with `example <binders> : False := by first | omega
#   | simp_all | decide | (simp_all; omega)`; all six failed to derive False).
#
#   Three rivals need NO conditioning at all, because they disagree with the spec
#   STRUCTURALLY (the result has the wrong LENGTH), and length is transparent even
#   when the elements are not: `weak-duration-branch-omitted`,
#   `weak-numeric-arm-reads-counts` and `weak-datetime-branch-omitted` are refuted
#   at inputs whose two candidate views have different lengths.
#
# ---------------------------------------------------------------------------
# NAGINI CASES AND THEIR DISPOSITION HERE (full accounting in 'assessment')
#
#   ported:   weak-duration-via-measurement  -> weak-duration-via-epoch-reduction
#             weak-duration-subtract-reference -> weak-duration-magnitudes-shifted
#             weak-duration-first-element-wrong -> weak-duration-head-magnitude-const
#             weak-duration-constant         -> weak-duration-branch-omitted +
#                                               weak-duration-magnitudes-shifted
#             weak-other-constant            -> weak-numeric-arm-values-zeroed
#             pos-span-local-reshape         -> pos-duration-accumulator-loop
#             pos-point-local-reshape        -> pos-pure-match / pos-guard-order-swapped
#             admiss-f2p-timedelta           -> admiss-f2p-duration-ground (see the
#                                               AUDIT note below)
#   new here: weak-numeric-arm-reads-counts, weak-datetime-branch-omitted,
#             weak-duration-order-reversed  (clauses C1/C3 and the structural frame,
#             which nagini's per-branch list carrier could not state as sharply),
#             weak-datetime-reduction-arg-reversed (added by the audit; see below)
#   dropped:  frame-mutate-readonly-values-span / -other  (fractional permission —
#             not expressible on a referentially transparent carrier)
#             AXIOM_TESTS                   (G-AX's lane; this gate ignores them)
#   divergence lane: the nagini sibling carries none, and on lean the class is
#             genuinely vacuous — `implementation_coerceToFloat` is a total Lean
#             `def`, so a diverging implementation cannot be written at all. MEASURED
#             by the audit, not asserted: a `partial def` self-call makes the frozen
#             proof's `unfold` fail ("Tactic `unfold` failed to unfold
#             `implementation_coerceToFloat`") and a plain recursive `def` self-call
#             is refused by the elaborator itself ("fail to show termination for
#             implementation_coerceToFloat / no parameters suitable for structural
#             recursion"). Neither is a SPEC verdict — the impl never becomes a term
#             — so there is no witness to state and nothing to ship. This is the lean
#             disposition, NOT the velvet `partial` known-spec-hole one.
#
# ---------------------------------------------------------------------------
# AUDIT (independent, adversarial; every claim below is a real `lake env lean`
# exit code, and the scratch builds were run outside the bundle)
#
#   Confirmed, on 64 builds: all 12 original cases earn their recorded outcome.
#   Every variant's `theorem correct_coerceToFloat` STATEMENT and whole spec view
#   are byte-identical to the frozen file (checked programmatically, not by eye).
#   All four positives build (exit 0). All eight original reject witnesses
#   discriminate — exit 0 against the rival, exit 1 against the frozen solution —
#   and every conditioned witness's satisfiability probe FAILS to derive `False`
#   (exit 1), so no refutation rests on a contradiction.
#
#   FORGERY TEST (attack B'), which is what actually establishes the gold-side
#   errors as semantic. Two instruments, one decisive:
#     * CONCRETE FLIP (decisive). Assert the spec's own equation — not the
#       negation — at each witness's own input, with `pure` in the reduction set.
#       It VERIFIES on the frozen solution (exit 0) and FAILS on every rival
#       (exit 1) with the rival's wrong value printed in the residual goal
#       (`⊢ pure [0.0, Float.ofInt 8] = [Float.ofInt 7, Float.ofInt 8]`,
#       `⊢ pure [7.0] = [Float.ofInt 1000, Float.ofInt 2000]`,
#       `⊢ pure (datetimeToFloat [1000]) = [Float.ofInt 1000]`, ...). The exit
#       codes INVERT with the claim, so gold's exit code carries information
#       about what is being claimed.
#     * TYPE REVEAL (decisive). Replacing the closing step with `exact (heq : Nat)`
#       prints the hypothesis's real type. Gold: `heq has type True` — `simp`
#       PROVED the instantiated spec equation for the frozen impl. Rival: the
#       concrete equation (`0.0 = 2.5`, `0.0 = Float.ofInt 7`,
#       `datetimeToFloat [5] = []`, `Float.ofInt 999 = Float.ofInt 1000 ∧ ...`).
#       That pair is a genuine refutation, not a syntactic accident.
#     * NAIVE FLIP (rejected as evidence). Dropping the `¬` WITHOUT `pure` in the
#       reduction set fails on both sides, because `simp [Id.run]` leaves the
#       monadic wrapper standing and the claim is never consulted. Cited here so
#       nobody re-runs it as if it discriminated; the two instruments above are
#       what the discrimination rests on.
#
#   REPAIRED by the audit:
#     (1) The admissibility lane was dropped with the reason "the obligation
#         carries no precondition hypothesis, so nothing can be
#         PRECOND-TOO-STRONG". That reason is not admissible: on a total carrier
#         the analogue is the obligation being UNSATISFIABLE at an F2P-shaped
#         input, which a ground discharge tests directly — and it is expressible
#         here (measured: exit 0). Landed as `admiss-f2p-duration-ground`.
#     (2) Two witnesses reduced with `simp [Id.run]` only, leaving `pure`
#         standing, so their gold-side residue read `¬pure [] = []` /
#         `¬pure [Float.ofInt 1000] = [Float.ofInt 1000]` — informative (the
#         flip proves it) but cosmetically indistinguishable from "the wrapper
#         did not reduce". Adding `pure` to both reduction sets makes the
#         gold-side residue a bare `⊢ False` / `expected to have type False`,
#         i.e. unambiguously "this negation does not hold of the frozen impl",
#         with the same discrimination (rival exit 0, gold exit 1).
#     (3) The header claimed the datetime arm's INPUTS to the carried reduction
#         are "fully pinned", but no case attacked them: every C1 rival dropped
#         the arm wholesale. `weak-datetime-reduction-arg-reversed` closes that,
#         and it is the only case that refutes at the callee's ARGUMENT.
#     (4) Three `refinement` fields asserted that named polyval cases are
#         PASS_TO_PASS. instance.json's PASS_TO_PASS list contains no polyval
#         case at all, so the claim named a lane the manifest cannot demonstrate.
#         Rewritten to argue only from the F2P case and from the unchanged-arm
#         behaviour the fix must preserve.
#
#   Attack D (SPEC-TOO-WEAK, five NEW wrong impls the battery did not contain):
#   duration correct except at magnitude zero; duration falling through when its
#   count buffer is empty; duration wrong only on singleton buffers; the numeric
#   arm emitting one extra element; and the datetime reduction fed a reversed
#   buffer. ALL FIVE were rejected (exit 1) with the residual goal naming exactly
#   the divergence. No spec hole.
#
#   Attack E (SPEC-TOO-STRONG, four NEW correct reshapes): the duration arm via
#   `foldr` instead of `map`; the duration arm casting `n * 1`; the numeric arm
#   round-tripped through `reverse.reverse`; and the whole dispatch via
#   `ValKind.rec`. The first three VERIFY (exit 0), so the spec is not over-fit.
#   The `ValKind.rec` one fails for a TOOLING reason and not a spec one — "code
#   generator does not support recursor `ValKind.rec` yet" — i.e. the impl never
#   becomes an executable term and the postcondition is never consulted. Not a
#   soundness hole.
#
#   The carrier claims in the next section were re-measured verbatim:
#   `decide` on `Float.ofInt 1000 ≠ Float.ofInt 2000` gives "failed to synthesize
#   Decidable", and `simp`/`norm_num` leave `¬0.0 = 2.5` open.
from pathlib import Path

INSTANCE = "pydata__xarray-6599"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. `_IMPL` lies ENTIRELY inside impl-start/impl-end and `_PROOF` entirely
# inside proof-start/proof-end; both are unique in the frozen file (asserted), so
# every case edits only the regions a variant may edit and `same_spec` holds by
# construction.
# ---------------------------------------------------------------------------

_IMPL = (
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else if x.kind = ValKind.duration then\n"
    "    return x.raw.map Float.ofInt\n"
    "  else\n"
    "    return x.data"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

_PROOF = (
    "  intro x\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  cases x.kind <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================

# pos-pure-match: a structurally different CORRECT impl — the three-way dispatch
# written as a pure `match` on the value kind instead of a chain of equality tests
# inside `Id.run do` (no monad, no early return). Semantics identical on every
# input; the theorem STATEMENT is byte-identical and the FROZEN proof body still
# closes (both sides reduce to the same case split), so no reproof is needed and
# nothing is assumed. If this FAILED, the postcondition would be over-fit to the
# guard-chain shape rather than to the behaviour. Ports the nagini positives'
# argument (a behaviour-preserving reshape of the coercion must verify).
_POS_MATCH = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float :=\n"
    "  match x.kind with\n"
    "  | ValKind.datetime => datetimeToFloat x.raw\n"
    "  | ValKind.duration => x.raw.map Float.ofInt\n"
    "  | ValKind.numeric  => x.data",
)

# pos-guard-order-swapped: the SAME three rules, but the duration test is made
# FIRST and the datetime test second. Behaviourally identical (the kinds are
# mutually exclusive), and it is the positive control that pairs with the rival
# lane below: the battery must not "reject" an impl merely for testing the kinds in
# a different order, or the reject cases would be measuring branch order rather
# than the coercion rule. Frozen proof body still closes.
_POS_ORDER = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.duration then\n"
    "    return x.raw.map Float.ofInt\n"
    "  else if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else\n"
    "    return x.data",
)

# pos-numeric-guarded-explicitly: the numeric arm is selected by an explicit test
# and the duration arm becomes the fall-through, i.e. the dispatch is restructured
# so that a DIFFERENT arm is the default. Behaviourally identical; guards which
# arm is "last" is not part of the specified behaviour. Frozen proof body closes.
_POS_NUMERIC_GUARD = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else if x.kind = ValKind.numeric then\n"
    "    return x.data\n"
    "  else\n"
    "    return x.raw.map Float.ofInt",
)

# pos-duration-accumulator-loop: the deepest reshape, and the direct counterpart of
# nagini's positive controls (which bound each element to a local before appending
# it). The duration arm's element-wise cast is computed by an ACCUMULATOR LOOP that
# pushes each cast magnitude in turn instead of by a single `map` — a different DATA
# FLOW, not just a different spelling. The theorem STATEMENT is byte-identical; its
# proof is reproven honestly inside proof-start/proof-end with the cheapest tactic
# that closes the new shape (`... <;> simp [h, Id.run] <;> rfl`) — no new
# axiom/lemma/sorry, no weakening of the obligation. If this FAILED, the
# postcondition would be pinned to the `map` spelling of the cast (SPEC-TOO-STRONG).
_POS_LOOP = _swap(
    _swap(
        _BASE, _IMPL,
        "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
        "  if x.kind = ValKind.datetime then\n"
        "    return datetimeToFloat x.raw\n"
        "  else if x.kind = ValKind.duration then\n"
        "    let mut acc : Array Float := #[]\n"
        "    for n in x.raw do\n"
        "      acc := acc.push (Float.ofInt n)\n"
        "    return acc.toList\n"
        "  else\n"
        "    return x.data",
    ),
    _PROOF,
    "  intro x\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  cases h : x.kind <;> simp [h, Id.run] <;> rfl",
)


# ===========================================================================
# ADMISSIBILITY (added by the audit) — must VERIFY, else the obligation is
# unsatisfiable at exactly an F2P-shaped input.
#
# The port dropped nagini's admiss-f2p-timedelta on the ground that "the
# obligation carries no precondition hypothesis, so nothing can be
# PRECOND-TOO-STRONG". That is not a demonstration of vacuity: on a total carrier
# the analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at a
# normal, F2P-shaped input, which a GROUND DISCHARGE at that input tests directly
# — and it turns out to be perfectly expressible here.
#
# Two `have`s are prepended INSIDE the proof region, ahead of the frozen tactic
# body, which then closes the obligation verbatim:
#   * `_ground_result` discharges the spec predicate at the F2P duration counts
#     against the CONCRETE result list, with no reference to the impl at all — so
#     it shows the postcondition is satisfiable there by an exhibited value, not
#     merely by whatever the impl happens to return (an impl-only discharge would
#     be vacuous if the spec were pinned to the impl);
#   * `_ground_impl` then discharges it against the impl's own answer at the same
#     input, tying the exhibited value to the shipped computation.
# Nothing is assumed: no new axiom/lemma/sorry, no new declaration, the theorem
# STATEMENT stays byte-identical, and the frozen proof body is untouched below.
_ADMISS_GROUND = _swap(
    _BASE, _PROOF,
    "  have _ground_result : problem_spec_coerceToFloat\n"
    "      { kind := ValKind.duration, raw := [(1000:Int), (2000:Int), (3000:Int)],\n"
    "        data := [] }\n"
    "      [Float.ofInt (1000:Int), Float.ofInt (2000:Int),\n"
    "       Float.ofInt (3000:Int)] := by\n"
    "    unfold problem_spec_coerceToFloat coerceResult\n"
    "    simp\n"
    "  have _ground_impl : problem_spec_coerceToFloat\n"
    "      { kind := ValKind.duration, raw := [(1000:Int), (2000:Int), (3000:Int)],\n"
    "        data := [] }\n"
    "      (implementation_coerceToFloat\n"
    "        { kind := ValKind.duration, raw := [(1000:Int), (2000:Int),\n"
    "          (3000:Int)], data := [] }) := by\n"
    "    unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "    simp [Id.run, pure]\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly, edits only the impl region, and keeps the frozen proof body (which
# will not close for a false statement); the attribution comes from the `witness`,
# checked in a file with the obligation removed.
# ===========================================================================

# THE DISCRIMINATOR (clause C2): duration arrays are routed through the datetime
# epoch reduction instead of following their own cast rule — the single behaviour
# the frozen docstring singles out as forbidden, and the behaviour the frozen
# prepatch file pins.
_RIV_DURATION_VIA_EPOCH = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime ∨ x.kind = ValKind.duration then\n"
    "    return datetimeToFloat x.raw\n"
    "  else\n"
    "    return x.data",
)

# Clause C2, branch OMITTED: no duration rule at all, so a duration array falls
# through to the already-numeric view. Structurally refutable (the two views have
# different lengths at the witness input), so this rival needs no conditioning.
_RIV_DURATION_OMITTED = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else\n"
    "    return x.data",
)

# Clause C2, every magnitude WRONG BY A FIXED OFFSET: each underlying count is
# shifted by one before being cast, as if a span were measured against an origin.
# The counterpart of nagini's reference-subtraction rival, and (unlike a
# constant-fill) it is element-wise plausible — it preserves length, sign and
# ordering, so only a value-level refutation can see it.
_RIV_DURATION_SHIFTED = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else if x.kind = ValKind.duration then\n"
    "    return x.raw.map (fun n => Float.ofInt (n - 1))\n"
    "  else\n"
    "    return x.data",
)

# Clause C2, PARTIAL DOMAIN: correct on every duration magnitude except the FIRST,
# which is forced to a constant. Ports nagini's first-element rival. A rival that is
# right on the tail and wrong on the head is invisible to any witness stated at a
# single-element input whose one element happens to be correct, which is why this
# case is stated at a two-element input and pinned to the head position.
_RIV_DURATION_HEAD_CONST = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else if x.kind = ValKind.duration then\n"
    "    match x.raw with\n"
    "    | [] => return []\n"
    "    | _ :: rest => return (0.0 : Float) :: rest.map Float.ofInt\n"
    "  else\n"
    "    return x.data",
)

# Clause C2 / STRUCTURAL FRAME: every magnitude is cast correctly, but the elements
# are emitted in REVERSE order. Element-wise correct and length-correct, so neither
# a value rival nor a length rival can see it — this is the case that pins the
# per-element ORDER of the coerced result (the lean analogue of the frame obligation
# nagini defended with a read-only permission).
_RIV_DURATION_REVERSED = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else if x.kind = ValKind.duration then\n"
    "    return x.raw.reverse.map Float.ofInt\n"
    "  else\n"
    "    return x.data",
)

# Clause C1, branch OMITTED: no datetime rule, so a datetime array is returned as
# its already-numeric view instead of being reduced relative to the epoch. Attacks
# the arm that the discriminating rival above leaves untouched — a battery that only
# attacked the duration arm would admit an impl that broke the datetime one.
_RIV_DATETIME_OMITTED = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.duration then\n"
    "    return x.raw.map Float.ofInt\n"
    "  else\n"
    "    return x.data",
)

# Clause C3, WRONG INPUT VIEW: an already-numeric array is put through the
# duration cast rule, i.e. the arm reads the underlying integer counts where the
# spec says it must return the values unchanged. The mirror of the discriminating
# rival (there a time rule was applied too widely; here the duration rule is).
# Clause C1, the reduction's ARGUMENT corrupted (added by the audit). Every other
# C1 rival drops the datetime arm wholesale, so nothing tested the header's claim
# that "WHICH inputs reach [the reduction]" is pinned: this arm still calls the
# carried reduction, on the same array, but hands it the count buffer REVERSED.
# The only rival that refutes at the callee's argument rather than at its
# presence, and the sharpest available attack on an arm whose value is opaque.
_RIV_DATETIME_ARG_REVERSED = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw.reverse\n"
    "  else if x.kind = ValKind.duration then\n"
    "    return x.raw.map Float.ofInt\n"
    "  else\n"
    "    return x.data",
)

_RIV_NUMERIC_READS_COUNTS = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else\n"
    "    return x.raw.map Float.ofInt",
)

# Clause C3, values DROPPED: the already-numeric arm returns the right NUMBER of
# values but replaces each with a constant. Ports nagini's constant-passthrough
# rival. Length-correct, so only a value-level refutation sees it.
_RIV_NUMERIC_ZEROED = _swap(
    _BASE, _IMPL,
    "def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do\n"
    "  if x.kind = ValKind.datetime then\n"
    "    return datetimeToFloat x.raw\n"
    "  else if x.kind = ValKind.duration then\n"
    "    return x.raw.map Float.ofInt\n"
    "  else\n"
    "    return x.data.map (fun _ => (0.0 : Float))",
)


# ---------------------------------------------------------------------------
# WITNESSES. Each states `¬ problem_spec_coerceToFloat x (implementation_... x)` at
# a concrete input, unfolds spec + impl, reduces the `Id.run` dispatch and derives
# the contradiction. Every one was built BOTH ways before shipping: it elaborates
# against its rival and FAILS on the frozen solution. Conditioned witnesses carry
# exactly ONE hypothesis, and each hypothesis set was probed for satisfiability
# (`... : False` did not close in any of them).
# ---------------------------------------------------------------------------

# Duration input; the hypothesis is precisely "the epoch reduction of these counts
# is not their direct cast" — the sub-domain where routing a span through the
# instant reduction is observable. Nothing is assumed about what the reduction IS.
#
# AUDIT: `pure` added to the reduction set. With `simp [Id.run]` alone the
# gold-side failure read `h ... but is expected to have type
# ¬pure [Float.ofInt 1000] = [Float.ofInt 1000]` — the monadic wrapper still
# standing, which is indistinguishable AT A GLANCE from "the reduction failed".
# With `pure` reduced, gold fails with `h ... but is expected to have type False`:
# the goal is fully evaluated and the negation simply does not hold there.
# Measured: rival exit 0, gold exit 1, both before and after.
_WIT_DURATION_VIA_EPOCH = (
    "example (h : datetimeToFloat [(1000:Int)] ≠ [Float.ofInt (1000:Int)]) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.duration, raw := [(1000:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.duration, raw := [(1000:Int)], data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  simp [Id.run, pure]\n"
    "  exact h"
)

# Duration input with TWO counts and a ONE-element numeric view: the omitted-branch
# rival returns the numeric view, whose length differs from the required cast, so
# the refutation is purely structural — no hypothesis, no opaque term.
_WIT_DURATION_OMITTED = (
    "example :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.duration, raw := [(1000:Int), (2000:Int)],\n"
    "          data := [(7.0 : Float)] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.duration, raw := [(1000:Int), (2000:Int)],\n"
    "            data := [(7.0 : Float)] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq"
)

# The three counts of the FAIL_TO_PASS duration case. The shifted rival emits the
# cast of 999 where the spec requires the cast of 1000; the hypothesis says only
# that those two casts differ.
_WIT_DURATION_SHIFTED = (
    "example (h : Float.ofInt (999:Int) ≠ Float.ofInt (1000:Int)) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.duration,\n"
    "          raw := [(1000:Int), (2000:Int), (3000:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.duration,\n"
    "            raw := [(1000:Int), (2000:Int), (3000:Int)], data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq\n"
    "  exact h heq.1"
)

# TWO counts, refutation pinned to the HEAD position: the rival's tail element is
# correct, so this witness demonstrates the partial-domain sub-claim its rationale
# makes rather than a uniform disagreement.
_WIT_DURATION_HEAD_CONST = (
    "example (h : (0.0 : Float) ≠ Float.ofInt (7:Int)) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.duration, raw := [(7:Int), (8:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.duration, raw := [(7:Int), (8:Int)],\n"
    "            data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq\n"
    "  exact h heq"
)

# THREE counts, so the reversal is observable at the ends; the hypothesis says only
# that the first and last casts differ (a two-element input would need the same
# assumption, and a one-element input could not see a reversal at all).
_WIT_DURATION_REVERSED = (
    "example (h : Float.ofInt (3000:Int) ≠ Float.ofInt (1000:Int)) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.duration,\n"
    "          raw := [(1000:Int), (2000:Int), (3000:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.duration,\n"
    "            raw := [(1000:Int), (2000:Int), (3000:Int)], data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq\n"
    "  exact h heq.1"
)

# Datetime input with a ONE-count buffer and an EMPTY numeric view: the rival
# returns the empty view where the spec requires the reduction of that buffer. The
# hypothesis is only that the reduction of a non-empty buffer is not the empty list
# — a statement about the callee's SHAPE, assuming nothing about its values.
_WIT_DATETIME_OMITTED = (
    "example (h : datetimeToFloat [(5:Int)] ≠ ([] : List Float)) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.datetime, raw := [(5:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.datetime, raw := [(5:Int)], data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq\n"
    "  exact h heq"
)

# Already-numeric input whose count buffer is NON-EMPTY and whose value view is
# EMPTY: reading the wrong view is refuted on length alone, unconditionally.
#
# AUDIT: `pure` added to the reduction set, same reason as the epoch witness — the
# gold-side residue was `⊢ ¬pure [] = []` and is now the bare `⊢ False`, so the
# error says "the frozen impl satisfies the spec here" rather than leaving the
# monadic wrapper to be read as an unfolding failure. Rival exit 0, gold exit 1
# both before and after.
_WIT_NUMERIC_READS_COUNTS = (
    "example :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.numeric, raw := [(500:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.numeric, raw := [(500:Int)], data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  simp [Id.run, pure]"
)

# Datetime input with TWO counts (added by the audit). The rival reduces the
# reversed buffer, so the refutation is stated over the reduction's ARGUMENT: the
# hypothesis says only that reducing [2,1] is not the same as reducing [1,2] — an
# assumption about nothing but the callee's sensitivity to its own input, which is
# the weakest thing that makes an argument corruption observable through an opaque
# callee. Nothing is assumed about what either reduction IS.
_WIT_DATETIME_ARG_REVERSED = (
    "example (h : datetimeToFloat [(2:Int), (1:Int)]\n"
    "             ≠ datetimeToFloat [(1:Int), (2:Int)]) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.datetime, raw := [(1:Int), (2:Int)], data := [] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.datetime, raw := [(1:Int), (2:Int)],\n"
    "            data := [] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq\n"
    "  exact h heq"
)

# Already-numeric input carrying one non-zero value: the zeroing rival keeps the
# length and loses the value, so the refutation is value-level and conditioned on
# that one value differing from the constant the rival substitutes.
_WIT_NUMERIC_ZEROED = (
    "example (h : (0.0 : Float) ≠ (2.5 : Float)) :\n"
    "    ¬ problem_spec_coerceToFloat\n"
    "        { kind := ValKind.numeric, raw := [], data := [(2.5 : Float)] }\n"
    "        (implementation_coerceToFloat\n"
    "          { kind := ValKind.numeric, raw := [], data := [(2.5 : Float)] }) := by\n"
    "  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult\n"
    "  intro heq\n"
    "  simp [Id.run, pure] at heq\n"
    "  exact h heq"
)


SPEC_TESTS = [
    # --- positives ---------------------------------------------------------
    {
        "id": "pos-pure-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": "structurally different CORRECT impl: the three-way dispatch "
                     "on the value kind written as a pure `match` rather than a "
                     "guard chain inside `Id.run do`, with the same rule per arm. "
                     "The single postcondition `result = coerceResult x` holds at "
                     "every input and the byte-identical obligation closes with the "
                     "frozen tactic body (no reproof, nothing assumed). If it were "
                     "rejected, the spec would be pinned to the guard-chain SHAPE "
                     "rather than to the coercion behaviour => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-guard-order-swapped",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ORDER,
        "rationale": "the same three rules with the duration test made FIRST and "
                     "the datetime test second. The kinds are mutually exclusive so "
                     "behaviour is unchanged; this is the control that keeps the "
                     "reject lane honest — the postcondition must react to WHICH "
                     "rule an arm applies (clauses C1/C2/C3), not to the order the "
                     "kinds are examined in. Rejection here would be "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-numeric-guarded-explicitly",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NUMERIC_GUARD,
        "rationale": "the dispatch is restructured so the ALREADY-NUMERIC case is "
                     "selected by an explicit test and the duration case becomes "
                     "the fall-through — a different arm is the default, with every "
                     "arm's rule unchanged. Behaviour is identical on all three "
                     "kinds, so `result = coerceResult x` still holds and the frozen "
                     "proof body closes. Defends the spec against being read as a "
                     "constraint on which arm is written last.",
    },
    {
        "id": "pos-duration-accumulator-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOOP,
        "rationale": "the deepest correct reshape and the direct counterpart of the "
                     "nagini positives (which bound each element to a local before "
                     "appending it): the duration arm's element-wise cast is "
                     "computed by an accumulator LOOP that pushes each cast "
                     "magnitude in turn instead of by a single `map`, i.e. a "
                     "different data flow rather than a different spelling. The "
                     "theorem statement is byte-identical and is reproven honestly "
                     "in the proof region with `cases h : x.kind <;> simp [h, "
                     "Id.run] <;> rfl` — no new axiom/lemma, no sorry, no weakening. "
                     "If it were rejected, clause C2 would be over-fit to the `map` "
                     "spelling of the cast => SPEC-TOO-STRONG.",
    },

    # --- admissibility -----------------------------------------------------
    {
        "id": "admiss-f2p-duration-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_GROUND,
        "rationale": "the obligation is DISCHARGED BY EVALUATION at an "
                     "F2P-shaped duration input (the three counts the "
                     "FAIL_TO_PASS case observes) before the frozen obligation is "
                     "closed verbatim, so the manifest demonstrates that the "
                     "specified behaviour is satisfiable at exactly that input — "
                     "the total-carrier analogue of PRECOND-TOO-STRONG, which on a "
                     "carrier with no precondition hypothesis is the obligation "
                     "being unsatisfiable at a normal input. Two `have`s: the "
                     "first discharges `result = coerceResult x` against the "
                     "CONCRETE result list with no reference to the impl (so "
                     "satisfiability is shown by an exhibited value, not by "
                     "whatever the impl returns), the second against the impl's "
                     "own answer at the same input. Statement byte-identical, no "
                     "new axiom/lemma/sorry, frozen proof body untouched. Ports "
                     "nagini's admiss-f2p-timedelta, whose omission here was a "
                     "silent drop of one of the three directions this gate tests.",
    },

    # --- rivals ------------------------------------------------------------
    {
        "id": "weak-duration-via-epoch-reduction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DURATION_VIA_EPOCH,
        "witness": _WIT_DURATION_VIA_EPOCH,
        "rationale": "THE discriminator. A single guard sends BOTH time-related "
                     "kinds through the epoch-relative datetime reduction, so a "
                     "duration array never reaches its own cast rule — exactly what "
                     "the frozen docstring forbids. Clause C2 requires "
                     "`x.raw.map Float.ofInt`; this returns `datetimeToFloat x.raw`. "
                     "The witness is stated at a duration array and conditions ONLY "
                     "on those two results differing at that input, which is the "
                     "sub-domain where the misrouting is observable; it elaborates "
                     "against the rival and fails on the frozen solution. If this "
                     "verified, the spec would not sense the kind-applicability "
                     "defect at all => SPEC-TOO-WEAK.",
        "refinement": "this is the faithful model of the buggy behaviour, and its "
                      "real-code counterpart does NOT resolve "
                      "test_polyval[timedelta-False]: with a duration coordinate "
                      "the epoch-relative reduction subtracts an instant from a "
                      "span, which the underlying array library does not define — "
                      "the evaluation raises instead of returning the expected "
                      "[1000.0, 2000.0, 3000.0], and even where it does not raise "
                      "the epoch reduction is the wrong rule for a span, so the "
                      "assert_allclose in the F2P case fails either way.",
    },
    {
        "id": "weak-duration-branch-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DURATION_OMITTED,
        "witness": _WIT_DURATION_OMITTED,
        "rationale": "the duration rule is missing entirely: a duration array is "
                     "returned as its already-numeric value view instead of the "
                     "element-wise cast of its underlying counts. Attacks clause C2 "
                     "by OMISSION (the mirror of the misrouting rival, which "
                     "attacks it by substitution). The witness needs no hypothesis: "
                     "at an input whose count buffer and value view have different "
                     "lengths the two candidate results disagree structurally, so "
                     "the refutation goes through even though `Float` is opaque.",
        "refinement": "a real patch that added no duration rule leaves the duration "
                      "coordinate uncoerced, so the polynomial evaluation either "
                      "operates on span values (the pre-existing wrong behaviour "
                      "the F2P case was added to catch) or errors on the mismatched "
                      "value type; either way it does not produce "
                      "[1000.0, 2000.0, 3000.0] and the F2P case does not resolve.",
    },
    {
        "id": "weak-duration-magnitudes-shifted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DURATION_SHIFTED,
        "witness": _WIT_DURATION_SHIFTED,
        "rationale": "the duration arm shifts every underlying count by a fixed "
                     "offset before casting, as if a span were measured against an "
                     "origin — the port of nagini's reference-subtraction rival. It "
                     "preserves length, order and sign, so ONLY a value-level "
                     "refutation can see it: the witness is stated at the three "
                     "counts of the FAIL_TO_PASS case and conditions on the cast of "
                     "the shifted count differing from the cast of the required one. "
                     "Attacks clause C2's element-wise VALUE, which the omission and "
                     "order rivals leave untouched.",
        "refinement": "measuring a span against an origin is a category error for a "
                      "duration array: every coerced value is off by the offset, so "
                      "the evaluated polynomial is shifted and the F2P case's "
                      "assert_allclose against [1000.0, 2000.0, 3000.0] fails. A "
                      "faithful real patch of this shape therefore verifies-but-does-"
                      "not-resolve if the spec admits it.",
    },
    {
        "id": "weak-duration-head-magnitude-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DURATION_HEAD_CONST,
        "witness": _WIT_DURATION_HEAD_CONST,
        "rationale": "PARTIAL DOMAIN: every duration magnitude is cast correctly "
                     "except the FIRST, which is forced to a constant. Ports "
                     "nagini's first-element rival. It agrees with the frozen "
                     "solution on strictly more of the domain than the shifted "
                     "rival, so it gets its own witness at its own input — a "
                     "two-element duration array, with the refutation pinned to the "
                     "head position (the tail element is emitted correctly by both), "
                     "which is the sub-domain the rationale claims.",
        "refinement": "a real patch correct on all but the leading value still "
                      "mis-coerces the first coordinate value; the polynomial is "
                      "evaluated over the whole array, so the F2P case's elementwise "
                      "comparison fails on the first element and does not resolve.",
    },
    {
        "id": "weak-duration-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DURATION_REVERSED,
        "witness": _WIT_DURATION_REVERSED,
        "rationale": "the STRUCTURAL frame: every magnitude is cast correctly and "
                     "the length is right, but the coerced values are emitted in "
                     "reverse order. Neither the value rivals (element-wise wrong) "
                     "nor the omission rivals (length wrong) can see this, so it is "
                     "the case that pins the per-element ORDER of the result — the "
                     "lean analogue of the frame obligation nagini defended with a "
                     "read-only permission on the input. Stated at a three-element "
                     "input, conditioned only on the first and last casts differing "
                     "(a reversal is unobservable otherwise).",
        "refinement": "a real patch that reordered the coerced values while casting "
                      "would pair each coordinate value with the wrong position, so "
                      "the evaluated polynomial is permuted relative to the "
                      "expected [1000.0, 2000.0, 3000.0] and the F2P comparison "
                      "fails. (AUDIT: an earlier version of this field also claimed "
                      "the datetime and simple polyval cases are PASS_TO_PASS. "
                      "instance.json's PASS_TO_PASS list contains no polyval case, "
                      "so that half named a lane the manifest cannot demonstrate "
                      "and is removed; the F2P argument alone carries the case.)",
    },
    {
        "id": "weak-datetime-branch-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DATETIME_OMITTED,
        "witness": _WIT_DATETIME_OMITTED,
        "rationale": "attacks clause C1, the arm every duration rival leaves alone: "
                     "the datetime rule is dropped, so a datetime array is returned "
                     "as its already-numeric view instead of being reduced relative "
                     "to the epoch. Without this case a rival that fixed the "
                     "duration behaviour by DESTROYING the datetime behaviour would "
                     "pass the battery. The witness assumes only that the reduction "
                     "of a non-empty count buffer is not the empty list — a "
                     "statement about the callee's shape, not its values, so no "
                     "property of the opaque reduction is smuggled in.",
        "refinement": "the datetime coercion is unchanged upstream behaviour that a "
                      "faithful patch is required to leave intact; dropping it "
                      "leaves a datetime coordinate uncoerced, so the polynomial is "
                      "evaluated over instants rather than their numeric reduction "
                      "and the datetime polyval behaviour breaks. Such a patch "
                      "resolves the F2P case's duration rule not at all while "
                      "regressing an arm the fix does not touch. (AUDIT: this field "
                      "previously named two polyval cases as PASS_TO_PASS; "
                      "instance.json's PASS_TO_PASS list contains no polyval case, "
                      "so the named-lane claim is removed.)",
    },
    {
        "id": "weak-datetime-reduction-arg-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DATETIME_ARG_REVERSED,
        "witness": _WIT_DATETIME_ARG_REVERSED,
        "rationale": "added by the audit, which found the header's claim that the "
                     "datetime arm's INPUTS to the carried reduction are pinned "
                     "demonstrated by no case: every other C1 rival drops the arm "
                     "wholesale, so all of them would be passed by an impl that "
                     "still calls the reduction on the wrong data. This arm calls "
                     "it on the same array but hands it the count buffer REVERSED "
                     "— the only rival in the battery that is refuted at the "
                     "callee's ARGUMENT rather than at its presence or its result. "
                     "The witness assumes only that the reduction distinguishes "
                     "[2,1] from [1,2], i.e. that the callee is sensitive to its "
                     "own input; nothing about what either reduction IS, so no "
                     "property of the opaque callee is smuggled in.",
        "refinement": "the datetime coercion is unchanged behaviour that a faithful "
                      "patch must preserve, and permuting the buffer it reduces "
                      "pairs each instant with the wrong position: the evaluated "
                      "polynomial comes back permuted for every datetime "
                      "coordinate, so a patch of this shape regresses the datetime "
                      "polyval behaviour the fix is required to leave alone while "
                      "resolving nothing.",
    },
    {
        "id": "weak-numeric-arm-reads-counts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NUMERIC_READS_COUNTS,
        "witness": _WIT_NUMERIC_READS_COUNTS,
        "rationale": "attacks clause C3 by reading the WRONG INPUT VIEW: an "
                     "already-numeric array is put through the duration cast rule, "
                     "i.e. the arm returns the cast of the underlying integer counts "
                     "where the spec requires the array's values unchanged. The "
                     "mirror image of the discriminating rival — there a time rule "
                     "was applied too widely, here the duration rule is. Refuted "
                     "unconditionally on length at an input whose two views have "
                     "different lengths.",
        "refinement": "applying the duration cast to arrays that are already "
                      "numeric replaces their values with whatever their raw buffer "
                      "reinterprets to. The F2P case's own coefficient arrays are "
                      "already numeric and go through this arm, so its expected "
                      "[1000.0, 2000.0, 3000.0] is not produced and the case does "
                      "not resolve — quite apart from every other already-numeric "
                      "polyval input the patch would corrupt. (AUDIT: this field "
                      "previously named specific polyval parametrisations as "
                      "PASS_TO_PASS; instance.json's PASS_TO_PASS list contains no "
                      "polyval case, so the named-lane claim is removed and the "
                      "argument now rests on the F2P case, which is demonstrable.)",
    },
    {
        "id": "weak-numeric-arm-values-zeroed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NUMERIC_ZEROED,
        "witness": _WIT_NUMERIC_ZEROED,
        "rationale": "ports nagini's constant-passthrough rival: the "
                     "already-numeric arm emits the right NUMBER of values but "
                     "replaces each with a constant. Length-correct, so it survives "
                     "every structural probe and is caught only by a value-level "
                     "refutation — the witness is stated at a one-value numeric "
                     "array and conditions on that value differing from the "
                     "constant. Attacks clause C3's VALUE where "
                     "`weak-numeric-arm-reads-counts` attacks its SOURCE.",
        "refinement": "constant-filling the already-numeric pass-through discards "
                      "the caller's values, so any evaluation whose coordinate or "
                      "coefficients are already numeric returns the constant "
                      "polynomial instead of the expected result. The F2P case's own "
                      "coefficients take this arm, so its expected "
                      "[1000.0, 2000.0, 3000.0] is not produced and it does not "
                      "resolve. (AUDIT: the earlier 'numeric PASS_TO_PASS cases "
                      "regress' half is removed — instance.json's PASS_TO_PASS list "
                      "contains no polyval case, so the manifest cannot demonstrate "
                      "it.)",
    },
]
