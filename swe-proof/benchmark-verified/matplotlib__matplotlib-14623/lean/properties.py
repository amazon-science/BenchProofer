"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-14623 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or discharges
a ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_setLim``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over two ordered rational endpoints):

  setLim (a b : Rat) : Rat × Rat
      let n := normalizeRange a b          -- singularity-avoiding expander,
                                              returns its pair in increasing order
      let p := clampToDomain n.1 n.2       -- domain limiter, order-preserving
      result = if a > b then (p.2, p.1) else p

  The single top-level clause is an exact equality against a term built from the
  two inputs and two opaque pass-through callees. It folds two decisions, each
  pinned to the ORDER of the inputs (`a` vs `b`):

    * WHICH ORDER the committed pair takes — the requested direction, captured by
      `a > b`, decides whether the conditioned pair `p` is committed as-is or
      with its endpoints exchanged. This is the load-bearing decision and the one
      the F2P observable exercises (a descending request must stay descending).
    * WHAT MAGNITUDES are committed — exactly the two values of `p`, the
      pass-through of the two conditioning callees; only their order may change.

  `normalizeRange` and `clampToDomain` are `opaque` (meta.json axioms == [];
  deep_model_references validated by G-CONF as A-references). They have no
  constraining axiom, so `p` has no computable value — witnesses therefore
  CONDITION on the carrier (see WITNESSES).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling reports
    has_readonly_input=False (grep confirms zero `Acc`): `lo`/`hi` are int VALUE
    parameters, no aliased read-only reference to overwrite. Lean is referentially
    transparent besides: `a b : Rat` are plain immutable values, no half-permission
    to violate. This class has NO expressible instance here; no substitute is
    fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS as a wrong-echo. The postcondition is
    GROUNDED in the input order (the `a > b` split) and pins the committed
    magnitudes by EXACT equality to the two callee pass-throughs; there is no
    axiomatized answer-key an implementation could echo without doing the order
    reassembly. The honest analogue is the cheapest-correct POSITIVE CONTROL.

  * NO-RESTORE (the pre-patch regression) — APPLIES, load-bearing. Committing the
    always-ascending conditioned pair WITHOUT restoring the requested direction is
    exactly the pre-fix behavior; refuted on any descending request.

  * COMPARISON-MUTANT rivals (`<` instead of `>`; `>` relaxed to `≥`) and
    ALWAYS-SWAP — APPLY. Each mishandles the direction decision on a distinct
    sub-domain (ascending / equal / all) and is refuted with a witness there.

  * PARTIAL-DOMAIN (raw passthrough, no conditioning) — APPLIES, but NOT as a
    partial-domain rival on THIS carrier. In nagini the conditioning callee was
    axiomatized as exact min/max on distinct inputs, so passthrough satisfied the
    contract everywhere except the equal sub-domain. Here the postcondition pins
    the committed pair by EXACT equality to an `opaque` pass-through with no
    axiom, so passthrough is refutable at ANY input — the ascending request
    `(1, 10)` included (re-derived by build: witness holds of the rival, fails on
    gold). The case is kept, at the equal point it was ported at, as the rival
    that drops the normalizing steps entirely; the "only the equal sub-domain
    falsifies it" claim the nagini design carried is NOT reproduced.

  * MAGNITUDE LEG (conditioning HALF applied) — APPLIES, added by audit. Every
    ported rival attacks the ORDER decision (or drops conditioning wholesale);
    none attacked the clause's other half, that the committed magnitudes are the
    pass-through of BOTH normalizing steps. `reject-drop-clamp` keeps the
    direction decision and the first normalizing step verbatim and drops only the
    second, so it is refuted by the magnitude leg alone, at a fourth probe point.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input. Because the committed magnitudes flow from `opaque` callees, the
snippets CONDITION on the carrier with a single, jointly-satisfiable hypothesis —
either that the conditioned pair for the probed input is non-degenerate
(`p.1 ≠ p.2`), or (for the passthrough rival) that the singular expansion for an
equal request actually moved the endpoints off `(v, v)`. Each hypothesis names ONE
opaque term, so it cannot be internally contradictory. Each witness was checked to
ELABORATE against its rival and to FAIL on the frozen solution (so it discriminates
rather than asserting a tautology).

Each snippet reduces the direction guard inside the ASSUMED equation
(`intro hc` + `simp only [… decide_true, decide_false …] at hc`) rather than
rewriting the goal under a one-branch simp set. That is deliberate and is what
makes the gold-side exit code carry information about the CLAIM: on the frozen
solution `simp` discharges the committed-pair equation outright, so `hc` becomes
`True` and the final projection/`symm` step has nothing to act on, whereas on each
rival `hc` remains a concrete equation the hypothesis contradicts. Verified by
revealing the hypothesis type on both sides (see AUDIT).

BINDER COVERAGE. The spec's input binders are the two endpoints `a`, `b`; the
behavioral pivots are their ORDER (which order the pair is committed in) and the
pass-through of the two normalizing steps (what magnitudes are committed). The
reject witnesses probe all three order regimes — descending `a > b` (no-restore),
ascending `a < b` (cmp-lt, always-swap, drop-clamp), and equal `a = b` (cmp-ge,
partial) — at four distinct input points `(10,1)`, `(1,10)`, `(5,5)`, `(-5,7)`,
and both pivots: three rivals are refuted by the ORDER leg, two (partial,
drop-clamp) by the MAGNITUDE leg. The variation is behavioral, not two spellings
of one point: each point flips the `a > b` guard or the conditioning
pass-through, and `(-5,7)` additionally sits where the domain restriction is
non-trivial in the real system rather than an identity. `a` takes four values and
`b` three across the lane, so neither binder is pinned. ``pts`` = 4 distinct
input points.

AUDIT (independent re-derivation, all claims below re-run on the real verifier):
  * every `theorem correct_setLim` STATEMENT diffed byte-for-byte against the
    frozen file — identical in all cases; the only edits are inside impl/proof.
  * all reject witnesses rebuilt twice: exit 0 against the rival, exit 1 on the
    frozen solution.
  * WITNESS FORM HARDENED (second audit pass). The witnesses previously rewrote
    the GOAL with a simp set that reduced only the taken branch, so gold's failure
    was an `Application type mismatch` whose printed type still carried an
    UNREDUCED `if decide _ = true then … else …`. That shape does not by itself
    show the kernel evaluated the claim. Each witness is now stated as
    `intro hc` + `simp only [… decide_true, decide_false …] at hc`, reducing the
    direction guard in the ASSUMED equation. Re-derived by build, and the two
    sides now invert on the CLAIM rather than on the script: revealing `hc`'s type
    (`exact (hc : Nat)`) prints `has type True` on the frozen solution — simp
    PROVED the committed pair there — and a concrete unmet equation on every
    rival. That `True` vs concrete-equation pair is the discrimination evidence;
    gold's own error is now `Invalid projection … hc has type True` /
    `Invalid field symm … True.symm`. Independently, the positive spec claim
    `problem_spec_setLim x y (implementation_setLim x y)` was PROVED on gold at
    all four probe points (10,1), (1,10), (5,5), (-5,7) — exit 0 — and FAILS on
    each rival at its own probe point (exit 1), under a multi-tactic closer so the
    failure is not a script gap.
  * each witness was additionally built against TWO correct reshaped impls (the
    componentwise `(if a > b then p.2 else p.1, …)` form and the `¬ (a ≤ b)`
    guard form): all six FAILED against both (exit 1), so no witness fires on a
    merely-reshaped correct impl. Every consistency probe still fails (exit 1),
    so no witness's hypotheses are contradictory.
  * the `no-restore` witness previously closed via `Prod.mk.injEq` + `rintro`; on
    gold that failed with `Unknown identifier h1` — a downstream naming artifact
    rather than a refuted claim. Restated (see WITNESS FORM HARDENED above).
  * POSITIVE-CONTROL STRENGTH, stated precisely. `pos-branch-select` is a
    genuinely different SYNTACTIC shape (no `Id.run do` / `let mut` / temp-swap):
    the frozen tactic body does NOT close it (exit 1, `No goals to be solved`),
    which is why it re-proves with `unfold` + `rfl`. But it is NOT independent of
    the spec's own form — its body is `rfl`-equal to the spec's RHS (built and
    confirmed: exit 0), so it is the CHEAPEST honest positive and on its own does
    not exclude SPEC-TOO-STRONG. What excludes that is the set of correct reshapes
    that are not `rfl`-equal to the RHS and still verify (see below), each needing
    real order reasoning rather than reflexivity.
  * SPEC-TOO-WEAK probes that did NOT verify (so no hole): capture the direction
    AFTER conditioning; an extra swap on the `a = 7` ascending fibre (correct at
    all three originally-probed points); the two normalizing steps composed in
    the wrong order; drop the second step; apply it twice; collapse the equal
    case to `(p.1, p.1)`.
  * SPEC-TOO-STRONG probes that DID verify (so no hole): the complementary
    `if a ≤ b then p else Prod.swap p` form (two independent proof scripts), the
    componentwise form (two scripts), and the eta-expanded `(p.1, p.2)` and
    `if b < a` forms. A faithful correct reshape is provable here, and the frozen
    tactic script is genuinely form-tuned — `if a ≤ b then p else Prod.swap p`
    with the frozen proof body fails, which is exactly why rejection alone
    attributes nothing and the witnesses carry the lane.
  * `reject-cmp-lt` vs `reject-always-swap` share a probe point but are distinct
    rivals (a wrong guard vs no guard), and neither subsumes the other: cmp-lt is
    correct nowhere on distinct inputs while always-swap is correct on the
    descending fibre.
  * NEW probes added by the second audit pass, all re-run:
      - SPEC-TOO-WEAK, rejected (so no hole): a rival wrong ONLY at `(3, 4)` and
        therefore correct at all four points this battery probes — the spec still
        rejects it, so the obligation is genuinely universally quantified and not
        merely pinned at the probed points; the domain limiter applied to the
        REVERSED normalized pair (`clampToDomain n.2 n.1`), which the opaque
        callee gives no symmetry to excuse; a rival duplicating one component
        (`(p.2, p.2)` / `(p.1, p.1)`); and the branches exchanged
        (`if a > b then q else (q.2, q.1)`).
      - SPEC-TOO-STRONG, verified (so no hole): the `¬ (a ≤ b)` guard (landed as
        `pos-notle-guard`), `if b < a`, and a `match decide (a > b)` form.
  * DIVERGENCE lane, measured rather than assumed. The frozen file sets no
    `loom.semantics.termination` (that option is velvet-only; G-HYGIENE requires
    it only for that backend), so this is a TOTAL Lean carrier: a rival with no
    decreasing measure does not merely fail its obligation, it fails to
    ELABORATE — `error: fail to show termination for implementation_setLim`.
    Built both shapes: a self-recursive `def` (exit 1, termination error) and a
    `partial def` (exit 1). Neither can carry a witness, because the witness file
    inherits the same uncompilable impl (built: exit 1, and the failure is the
    termination/`unsolved goals` artifact, not a refutation of any claim). So the
    class is not shippable as a reject case here: the rejection would attest to
    the elaborator refusing the definition, not to the spec. Recorded as a
    VACUOUS class on this carrier, with the error text above as the reason.

AXIOM lane: EMPTY. meta.json axioms == [] (the direction-restoring reassembly is
modeled deeply; the two callees are A-references validated by G-CONF, not consumed
axioms). No axiom-soundness / axiom-containment obligation lives in this model;
that lane belongs to G-AX regardless. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-14623"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL frozen impl def and the FULL frozen tactic BODY (everything after
# `:= by`), so every replacement lands entirely inside the region it edits and
# the `theorem correct_setLim` STATEMENT is preserved byte-for-byte.
_IMPL_GOLD = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  let swapped : Bool := decide (a > b)\n"
    "  let n := normalizeRange a b\n"
    "  let c := clampToDomain n.1 n.2\n"
    "  let mut lo : Rat := c.1\n"
    "  let mut hi : Rat := c.2\n"
    "  if swapped then\n"
    "    let t := lo\n"
    "    lo := hi\n"
    "    hi := t\n"
    "  return (lo, hi)"
)

_PROOF_BODY = (
    "  intro a b\n"
    "  simp only [problem_spec_setLim, implementation_setLim, Id.run]\n"
    "  by_cases h : a > b\n"
    "  · simp only [h, decide_true, if_true]; rfl\n"
    "  · simp only [h, decide_false, Bool.false_eq_true, if_false]; rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing ONLY the gold impl def."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Positive-control impl + its re-proof (statement byte-identical, no new
# declaration/axiom/assumption token).
# ---------------------------------------------------------------------------

# Structurally different but CORRECT: a pure functional branch-select (no
# `Id.run do` / `let mut` / temp-swap). It commits the exchanged conditioned pair
# on a descending request and the conditioned pair as-is otherwise — the same
# value on every input, so it satisfies the exact-equality clause. The frozen
# tactic (tuned to the `Id.run do` mutable form) no longer applies, so the
# obligation is re-proved for the new shape by `unfold` + `rfl`.
_POS_IMPL = (
    "def implementation_setLim (a b : Rat) : Rat × Rat :=\n"
    "  let n := normalizeRange a b\n"
    "  let p := clampToDomain n.1 n.2\n"
    "  if a > b then (p.2, p.1) else p"
)
_POS_PROOF = (
    "  intro a b\n"
    "  unfold problem_spec_setLim implementation_setLim\n"
    "  rfl"
)

# SECOND positive control, added by AUDIT to close a real gap: `_POS_IMPL` above
# is a different syntactic shape but its body is `rfl`-equal to the spec's own RHS
# (confirmed by build), so it is the cheapest honest positive and cannot by itself
# exclude SPEC-TOO-STRONG. This one commits the SAME value on every input while
# spelling the direction guard as `¬ (a ≤ b)` rather than `a > b`. That is not the
# spec's term: closing it needs the order facts (`not_le`, `not_lt`) rather than
# reflexivity, so a faithful correct impl whose guard is written differently is
# demonstrated to be admitted. Verified: exit 0.
_POS2_IMPL = (
    "def implementation_setLim (a b : Rat) : Rat × Rat :=\n"
    "  let n := normalizeRange a b\n"
    "  let q := clampToDomain n.1 n.2\n"
    "  if ¬ (a ≤ b) then (q.2, q.1) else q"
)
_POS2_PROOF = (
    "  intro a b\n"
    "  unfold problem_spec_setLim implementation_setLim\n"
    "  by_cases h : a > b <;> simp [h, not_le, lt_of_not_le] <;>\n"
    "    simp_all [not_lt, le_of_lt]"
)

# Admissibility: keep the gold impl and proof, but first discharge the obligation
# at the exact F2P-shaped descending input (10, 1) as a `have` inside the tactic
# body, then close the frozen obligation verbatim. Confirms the modeled behavior
# is satisfiable at the input the F2P exercises (the descending-orientation leg).
_ADMISS_PROOF = (
    "  have _ground : problem_spec_setLim 10 1 (implementation_setLim 10 1) := by\n"
    "    simp only [problem_spec_setLim, implementation_setLim, Id.run]\n"
    "    simp only [show ((10 : Rat) > 1) by norm_num, decide_true, if_true]\n"
    "    rfl\n"
    + _PROOF_BODY
)


# ---------------------------------------------------------------------------
# Rival impl defs (each is a full impl def; only the impl changes, so the spec
# and the theorem STATEMENT stay byte-identical; the frozen proof body no longer
# closes → non-verify).
# ---------------------------------------------------------------------------

# NO-RESTORE (= the pre-patch regression): commit the always-ascending
# conditioned pair without restoring the requested direction.
_NO_RESTORE = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  let n := normalizeRange a b\n"
    "  let c := clampToDomain n.1 n.2\n"
    "  let lo : Rat := c.1\n"
    "  let hi : Rat := c.2\n"
    "  return (lo, hi)"
)

# COMPARISON FLIPPED to `<`: restore on the WRONG branch — swap on ascending,
# leave descending alone.
_CMP_LT = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  let swapped : Bool := decide (a < b)\n"
    "  let n := normalizeRange a b\n"
    "  let c := clampToDomain n.1 n.2\n"
    "  let mut lo : Rat := c.1\n"
    "  let mut hi : Rat := c.2\n"
    "  if swapped then\n"
    "    let t := lo\n"
    "    lo := hi\n"
    "    hi := t\n"
    "  return (lo, hi)"
)

# COMPARISON `>` relaxed to `≥`: on an EQUAL request `swapped` becomes true, so
# the ascending expanded pair is flipped to descending.
_CMP_GE = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  let swapped : Bool := decide (a ≥ b)\n"
    "  let n := normalizeRange a b\n"
    "  let c := clampToDomain n.1 n.2\n"
    "  let mut lo : Rat := c.1\n"
    "  let mut hi : Rat := c.2\n"
    "  if swapped then\n"
    "    let t := lo\n"
    "    lo := hi\n"
    "    hi := t\n"
    "  return (lo, hi)"
)

# ALWAYS-SWAP: commit the conditioned pair exchanged unconditionally.
_ALWAYS_SWAP = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  let n := normalizeRange a b\n"
    "  let c := clampToDomain n.1 n.2\n"
    "  return (c.2, c.1)"
)

# PASSTHROUGH: raw passthrough of the requested endpoints — it never runs either
# normalizing step, so the committed magnitudes are the raw request rather than
# the pass-through the clause pins by exact equality.
_PARTIAL = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  return (a, b)"
)

# MAGNITUDE LEG: keep the direction decision and the FIRST normalizing step
# verbatim, drop the SECOND. Orientation is always right; only the committed
# magnitudes are wrong, and only when the dropped step actually moves an endpoint.
_DROP_CLAMP = (
    "def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do\n"
    "  let swapped : Bool := decide (a > b)\n"
    "  let n := normalizeRange a b\n"
    "  let mut lo : Rat := n.1\n"
    "  let mut hi : Rat := n.2\n"
    "  if swapped then\n"
    "    let t := lo\n"
    "    lo := hi\n"
    "    hi := t\n"
    "  return (lo, hi)"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The theorem STATEMENT is byte-
    # identical; the tactic body is re-proved for the new (pure functional) shape.
    # No helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-branch-select",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a structurally-different (pure functional branch-select, no `Id.run "
            "do` / mutable temp-swap) but behaviourally-identical correct impl must "
            "verify: it commits the exchanged conditioned pair on `a > b` and the "
            "conditioned pair as-is otherwise, i.e. exactly `if a > b then (p.2, "
            "p.1) else p`. After `unfold` both sides are the same let/if term, so "
            "the goal closes by `rfl` — no new declaration, axiom, or assumption "
            "token. If it cannot verify => SPEC-TOO-STRONG. NOTE (audit): the "
            "frozen tactic body does NOT close this shape (built: exit 1, `No goals "
            "to be solved`), so the reshape is real; but its body IS `rfl`-equal to "
            "the spec's RHS (built: exit 0), so this is the CHEAPEST honest "
            "positive. `pos-notle-guard` below carries the weight of excluding "
            "SPEC-TOO-STRONG, being correct without being the spec's own term."
        ),
    },

    # =====================================================================
    # SECOND POSITIVE CONTROL (soundness) — added by AUDIT. The case above is a
    # different syntactic shape but is `rfl`-equal to the spec's RHS, so on its own
    # it does not show the spec admits a correct impl it cannot see through by
    # reflexivity. This one spells the direction guard as `¬ (a ≤ b)`: the same
    # function on every input, but the obligation now needs the order facts
    # (`not_le` / `not_lt`) instead of `rfl`.
    # =====================================================================
    {
        "id": "pos-notle-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS2_IMPL), _PROOF_BODY, _POS2_PROOF),
        "rationale": (
            "a correct impl whose direction guard is spelled `¬ (a ≤ b)` rather "
            "than the spec's `a > b` must verify: on a linear order the two agree "
            "at every pair, so it commits exactly `if a > b then (q.2, q.1) else q` "
            "— the same value as the frozen impl on every input. Unlike "
            "`pos-branch-select` its body is NOT the spec's RHS up to `rfl`, so the "
            "proof must actually relate the two guards (`not_le`, `not_lt`) rather "
            "than close by reflexivity. This is what excludes SPEC-TOO-STRONG: the "
            "clause constrains the committed VALUE, not the spelling of the test "
            "that selects it. If it cannot verify => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the frozen `∀ (a b : Rat)` obligation carries NO precondition
    # hypothesis (the behavior is total), so nagini's precondition-admission probe
    # has no binder to attack; the honest analogue discharges the spec predicate at
    # the exact F2P ground input inside the proof region, alongside the frozen
    # obligation. If that ground instance could not be discharged, the modeled
    # behavior would be unsatisfiable at the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-f2p-descending",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the exact F2P-shaped descending input "
            "`(10, 1)` (the `set_ylim(10, 1)` request) as a `have` — there `a > b`, "
            "so the spec demands the committed pair be the conditioned pair with "
            "endpoints exchanged (descending kept), closed by `simp`/`rfl` — then "
            "the frozen obligation is closed verbatim. Verifies (else the spec is "
            "unsatisfiable at the normal input, the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: the theorem STATEMENT is byte-identical, the ground "
            "instance is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # carrier-conditioned refutation witness pinning the violation at one input.
    # =====================================================================
    {
        "id": "reject-no-restore",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_RESTORE),
        "refinement": (
            "this is byte-for-byte the pre-patch behaviour: it drops the captured "
            "direction flag and the direction-restoring exchange, so a descending "
            "request `(10, 1)` is committed ascending. The faithful real patch (the "
            "endpoint handling WITHOUT the restore) fails the F2P observable — a "
            "descending request on a nonlinear axis is expected to stay descending "
            "but is stored ascending — so it does NOT resolve the F2P."
        ),
        "rationale": (
            "REJECT from the clause `result = if a > b then (p.2, p.1) else p`: at "
            "the descending request `(10, 1)` the spec demands the exchanged pair "
            "`(p.2, p.1)`, but the rival commits the conditioned pair `(p.1, p.2)`. "
            "These differ whenever the conditioned endpoints are distinct — the "
            "generic case — so the rival contradicts the spec on the descending "
            "sub-domain. Probes the `a > b` order regime."
        ),
        "witness": (
            "-- Descending request (10, 1): the spec commits the EXCHANGED\n"
            "-- conditioned pair, the no-restore rival commits it as-is. They differ\n"
            "-- whenever the conditioned endpoints are distinct (p.1 ≠ p.2).\n"
            "-- The direction guard is REDUCED (decide_true/decide_false in the simp\n"
            "-- set, rewriting the assumed equation rather than the goal), so on the\n"
            "-- frozen impl `hc` collapses to `True` -- simp PROVES the committed pair\n"
            "-- there -- while on the rival it stays a concrete unmet equation.\n"
            "example (h : (clampToDomain (normalizeRange 10 1).1 (normalizeRange 10 1).2).1\n"
            "           ≠ (clampToDomain (normalizeRange 10 1).1 (normalizeRange 10 1).2).2) :\n"
            "    ¬ problem_spec_setLim 10 1 (implementation_setLim 10 1) := by\n"
            "  intro hc\n"
            "  simp only [problem_spec_setLim, implementation_setLim, Id.run, pure, bind,\n"
            "    gt_iff_lt, decide_true, decide_false, Bool.false_eq_true, if_true, if_false,\n"
            "    Prod.ext_iff, show ((1:Rat) < 10) by norm_num] at hc\n"
            "  exact h hc.1\n"
        ),
    },
    {
        "id": "reject-cmp-lt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CMP_LT),
        "refinement": (
            "capturing the direction flag as `a < b` restores orientation on the "
            "WRONG branch: an ascending request is flipped to descending and a "
            "descending request is left ascending. The faithful real patch (the "
            "comparison written the wrong way round) fails the F2P observable on "
            "the descending leg AND the ascending PASS_TO_PASS legs — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = if a > b then (p.2, p.1) else p`: at "
            "the ascending request `(1, 10)` the spec demands the conditioned pair "
            "as-is `(p.1, p.2)`, but the rival (swapped = `a < b` = true) commits "
            "the exchanged pair `(p.2, p.1)`. These differ whenever the conditioned "
            "endpoints are distinct. Probes the `a < b` order regime."
        ),
        "witness": (
            "-- Ascending request (1, 10): the spec commits the conditioned pair\n"
            "-- as-is, but the flipped-comparison rival exchanges it. They differ\n"
            "-- whenever the conditioned endpoints are distinct (p.1 ≠ p.2).\n"
            "-- The direction guard is REDUCED (decide_true/decide_false), so on the\n"
            "-- frozen impl `hc` collapses to `True` while on the rival it stays a\n"
            "-- concrete unmet equation -- the failure tracks the CLAIM, not the script.\n"
            "example (h : (clampToDomain (normalizeRange 1 10).1 (normalizeRange 1 10).2).1\n"
            "           ≠ (clampToDomain (normalizeRange 1 10).1 (normalizeRange 1 10).2).2) :\n"
            "    ¬ problem_spec_setLim 1 10 (implementation_setLim 1 10) := by\n"
            "  intro hc\n"
            "  simp only [problem_spec_setLim, implementation_setLim, Id.run, pure, bind,\n"
            "    gt_iff_lt, decide_true, decide_false, Bool.false_eq_true, if_true, if_false,\n"
            "    Prod.ext_iff, show ¬((10:Rat) < 1) by norm_num] at hc\n"
            "  exact h hc.1.symm\n"
        ),
    },
    {
        "id": "reject-cmp-ge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CMP_GE),
        "refinement": (
            "relaxing the comparison to `a ≥ b` makes an EQUAL request capture the "
            "direction flag as true, so the singular expansion (which returns its "
            "two endpoints in increasing order) is flipped to descending. The "
            "faithful real patch stores a singular `set_*lim(v, v)` request as a "
            "descending range instead of the ascending auto-expanded range "
            "matplotlib documents — a behaviour regression on the equal sub-domain; "
            "it does NOT match gold."
        ),
        "rationale": (
            "REJECT from the clause `result = if a > b then (p.2, p.1) else p`: at "
            "the equal request `(5, 5)` `a > b` is false, so the spec demands the "
            "conditioned pair as-is `(p.1, p.2)`, but the rival (swapped = `a ≥ b` "
            "= true) commits the exchanged pair `(p.2, p.1)`. These differ whenever "
            "the expanded endpoints are distinct — which the singular expansion "
            "guarantees. Probes the `a = b` order regime, admitted precisely so "
            "this equal-case behaviour is pinned."
        ),
        "witness": (
            "-- Equal request (5, 5): a > b is false so the spec commits the\n"
            "-- expanded pair as-is; the `≥` rival flips it. They differ whenever the\n"
            "-- singular expansion made the endpoints distinct (p.1 ≠ p.2).\n"
            "-- The direction guard is REDUCED (decide_true/decide_false), so on the\n"
            "-- frozen impl `hc` collapses to `True` while on the rival it stays a\n"
            "-- concrete unmet equation -- the failure tracks the CLAIM, not the script.\n"
            "example (h : (clampToDomain (normalizeRange 5 5).1 (normalizeRange 5 5).2).1\n"
            "           ≠ (clampToDomain (normalizeRange 5 5).1 (normalizeRange 5 5).2).2) :\n"
            "    ¬ problem_spec_setLim 5 5 (implementation_setLim 5 5) := by\n"
            "  intro hc\n"
            "  simp only [problem_spec_setLim, implementation_setLim, Id.run, pure, bind,\n"
            "    gt_iff_lt, decide_true, decide_false, Bool.false_eq_true, if_true, if_false,\n"
            "    Prod.ext_iff, show ¬((5:Rat) < 5) by norm_num] at hc\n"
            "  exact h hc.1.symm\n"
        ),
    },
    {
        "id": "reject-always-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_SWAP),
        "refinement": (
            "committing the conditioned pair exchanged unconditionally stores EVERY "
            "request descending; an ascending request `(1, 10)` is stored `(10, 1)`. "
            "The faithful real patch fails the ascending PASS_TO_PASS assertions of "
            "the inverted-limits observable — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = if a > b then (p.2, p.1) else p`: at "
            "the ascending request `(1, 10)` the spec demands `(p.1, p.2)`, but the "
            "rival always commits `(p.2, p.1)`. These differ whenever the "
            "conditioned endpoints are distinct. Shares the `a < b` order regime "
            "with cmp-lt but is a distinct rival (unconditional, no direction flag) "
            "refuted at the same ascending point where it too is wrong."
        ),
        "witness": (
            "-- Ascending request (1, 10): the spec commits the conditioned pair\n"
            "-- as-is, but the always-swap rival exchanges it. They differ whenever\n"
            "-- the conditioned endpoints are distinct (p.1 ≠ p.2).\n"
            "-- The direction guard is REDUCED (decide_true/decide_false), so on the\n"
            "-- frozen impl `hc` collapses to `True` while on the rival it stays a\n"
            "-- concrete unmet equation -- the failure tracks the CLAIM, not the script.\n"
            "example (h : (clampToDomain (normalizeRange 1 10).1 (normalizeRange 1 10).2).1\n"
            "           ≠ (clampToDomain (normalizeRange 1 10).1 (normalizeRange 1 10).2).2) :\n"
            "    ¬ problem_spec_setLim 1 10 (implementation_setLim 1 10) := by\n"
            "  intro hc\n"
            "  simp only [problem_spec_setLim, implementation_setLim, Id.run, pure, bind,\n"
            "    gt_iff_lt, decide_true, decide_false, Bool.false_eq_true, if_true, if_false,\n"
            "    Prod.ext_iff, show ¬((10:Rat) < 1) by norm_num] at hc\n"
            "  exact h hc.1.symm\n"
        ),
    },
    {
        "id": "reject-partial-no-expand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL),
        "refinement": (
            "raw passthrough keeps the requested orientation on every input, so the "
            "direction observable the F2P checks survives, but it runs NEITHER "
            "normalizing step: an equal request `set_*lim(v, v)` is stored as the "
            "degenerate range `(v, v)` instead of the auto-expanded non-degenerate "
            "ascending range, and an endpoint outside the axis's permitted domain is "
            "stored unrestricted. The faithful real patch breaks the "
            "singular-expansion contract on the equal sub-domain — it does NOT match "
            "gold there."
        ),
        "rationale": (
            "REJECT from the clause `result = if a > b then (p.2, p.1) else p`: at "
            "the equal request `(5, 5)` `a > b` is false, so the spec demands the "
            "conditioned pair `p` (the expanded, non-degenerate pair), but the rival "
            "commits the raw `(5, 5)`. These differ whenever the singular expansion "
            "actually moved the endpoints off `(5, 5)`. NOTE (audit): unlike its "
            "nagini ancestor this is NOT a partial-domain rival on this carrier — the "
            "clause pins the magnitudes by exact equality to an unaxiomatized "
            "`opaque` pass-through, so passthrough is refutable at ANY input, "
            "including ascending `(1, 10)` (re-derived by build). It is kept at the "
            "equal point as the drops-both-steps rival; `reject-drop-clamp` is the "
            "rival that isolates the magnitude leg with the direction leg intact."
        ),
        "witness": (
            "-- Equal request (5, 5): the spec commits the EXPANDED conditioned pair,\n"
            "-- the passthrough rival commits the raw (5, 5). They differ whenever the\n"
            "-- singular expansion moved the endpoints off (5, 5).\n"
            "-- The direction guard is REDUCED (decide_true/decide_false), so on the\n"
            "-- frozen impl `hc` collapses to `True` while on the rival it stays a\n"
            "-- concrete unmet equation -- the failure tracks the CLAIM, not the script.\n"
            "example (h : (clampToDomain (normalizeRange 5 5).1 (normalizeRange 5 5).2)\n"
            "           ≠ ((5 : Rat), (5 : Rat))) :\n"
            "    ¬ problem_spec_setLim 5 5 (implementation_setLim 5 5) := by\n"
            "  intro hc\n"
            "  simp only [problem_spec_setLim, implementation_setLim, Id.run, pure, bind,\n"
            "    gt_iff_lt, decide_true, decide_false, Bool.false_eq_true, if_true, if_false,\n"
            "    show ¬((5:Rat) < 5) by norm_num] at hc\n"
            "  exact h hc.symm\n"
        ),
    },
    # Added by AUDIT: the ported lane attacked only the ORDER decision (or dropped
    # the normalizing steps wholesale). This rival keeps the direction decision and
    # the first normalizing step byte-for-byte and drops ONLY the second, so it can
    # be refuted by the MAGNITUDE half of the clause alone, with the order half
    # satisfied everywhere. Probed at a fourth input point where the dropped step
    # is non-trivial in the real system rather than an identity.
    {
        "id": "reject-drop-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_CLAMP),
        "refinement": (
            "the requested direction is captured and restored exactly as gold does, "
            "so every direction observable — the F2P descending request included — "
            "still holds; what is dropped is the restriction of the endpoints to the "
            "values the axis permits. The faithful real patch commits an endpoint "
            "outside the axis's permitted domain whenever the request reaches "
            "outside it (an axis that accepts only a limited domain then holds a "
            "range it cannot represent), so it does NOT match gold on that "
            "sub-domain even though it resolves the direction observable. This is "
            "the sharpest near-miss in the lane: correct on the whole load-bearing "
            "leg, wrong only on the pass-through leg."
        ),
        "rationale": (
            "REJECT from the MAGNITUDE half of the clause `result = if a > b then "
            "(p.2, p.1) else p`: `p` is the pair produced by BOTH normalizing steps, "
            "and the rival commits the pair produced by only the first. At the "
            "ascending request `(-5, 7)` `a > b` is false, so the spec demands "
            "`clampToDomain n.1 n.2` while the rival commits `n` — different whenever "
            "the domain restriction moved an endpoint. Probes the pass-through pivot, "
            "which every other rival leaves intact or destroys wholesale."
        ),
        "witness": (
            "-- Ascending request (-5, 7): the spec commits the pair produced by BOTH\n"
            "-- normalizing steps; this rival commits the pair after only the first, so\n"
            "-- the two differ whenever the domain restriction moved an endpoint.\n"
            "-- The direction guard is REDUCED (decide_true/decide_false), so on the\n"
            "-- frozen impl `hc` collapses to `True` while on the rival it stays a\n"
            "-- concrete unmet equation -- the failure tracks the CLAIM, not the script.\n"
            "example (h : clampToDomain (normalizeRange (-5) 7).1 (normalizeRange (-5) 7).2\n"
            "           ≠ normalizeRange (-5) 7) :\n"
            "    ¬ problem_spec_setLim (-5) 7 (implementation_setLim (-5) 7) := by\n"
            "  intro hc\n"
            "  simp only [problem_spec_setLim, implementation_setLim, Id.run, pure, bind,\n"
            "    gt_iff_lt, decide_true, decide_false, Bool.false_eq_true, if_true, if_false,\n"
            "    show ¬((7:Rat) < -5) by norm_num] at hc\n"
            "  exact h hc.symm\n"
        ),
    },
]


# No consumed axioms and no deep-model references to re-discharge here: the
# direction-restoring reassembly is modeled directly and the two conditioning
# callees are opaque A-references validated by G-CONF, so there is no in-model
# axiom obligation for the PBT axiom lane.
AXIOM_TESTS = []
