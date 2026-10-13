"""properties.py — G-PBT falsification battery for astropy__astropy-14995 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file elaborates
with every obligation closed); ``expect="reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (one total decision over three observable inputs):

  maskPropagation (selfMask operandMask : Option Mask) (handleMask : Option Combine)
      : Except Unit (Option Mask)

  A result carrier records, per operand, whether it carries a flag grid
  (`some grid`) or not (`none`), plus an optional element-wise merge callback.
  The single load-bearing postcondition clause pins the result by exhaustive
  case on the three inputs:

    (D-merge) result =
        • no merge callback supplied            -> no result grid;
        • callback supplied, NEITHER carries    -> no result grid;
        • callback supplied, only the OTHER     -> the other's grid, copied over;
        • callback supplied, only THIS one       -> this one's grid, copied over;
        • callback supplied, BOTH carry          -> the callback applied to both.

    This one clause pins simultaneously: the routing (which of the five
    situations fires on which input), the value produced in each (which grid is
    copied, that the callback is consulted ONLY when both are present), and the
    no-grid / grid distinction (`Except.ok none` vs `Except.ok (some _)`).

  Each of the five situations is one arm of the frozen match, and every input
  binder is a genuine discriminator: the routing turns on all three of
  `selfMask`, `operandMask`, `handleMask`.

ADVERSARIAL READ of the nagini case classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the input grids carry no heap permission, there is no read-only half-
    permission to overwrite and no aliasing to exploit. The nagini frame-mutation
    rivals (an in-place append to a read-only input grid, or a rebind of the
    operand's grid field, each rejected for insufficient permission) have NO
    expressible instance here, and no substitute is fabricated for them. What
    those rivals defended — that the copied-over grid is a value copy — collapses
    to plain value equality on this carrier, which the (D-merge) clause already
    pins. See 'assessment'.

  * PREPATCH / PARTIAL-DOMAIN — APPLIES, and is the substantive attack. The bug
    the fix repairs is that, when only THIS operand carries a grid, the routine
    consulted the merge callback against a missing operand grid and crashed
    instead of copying the lone grid over. On this carrier the crash is modeled
    as an `Except.error` result, so the prepatch rival is exactly the
    only-this-carries arm returning `.error ()` (rival `only-self-errors`). The
    (D-merge) clause rejects it.

  * VALUE / ROUTING DISCRIMINATION — APPLIES. Rivals that fire the wrong value on
    one arm: drop the other operand's grid when only the other carries one;
    return a grid where none is due; echo an input where a fixed answer is due;
    ignore the callback when both carry a grid. Each attacks one arm of
    (D-merge) at an input that varies the responsible binder.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. (D-merge) is GROUNDED in the inputs: every
    arm's value is a structural function of the concrete `selfMask` /
    `operandMask` / `handleMask` (a copy of one, `none`, or the callback applied
    to both), fully case-reducible, not an opaque answer key. In its place the
    battery carries honest reshaped POSITIVE CONTROLS (`pos-*`).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the (D-merge)
clause at one concrete input. Each is stated directly against the spec predicate
at ``decide``-able integer-grid literals (the callback taken concretely as
list append, so the both-present arm reduces), and each was checked to hold of
its rival AND to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology).

ADMISSIBILITY: the nagini bundle re-derived its precondition to show it is
consistent. The lean obligation carries no precondition — ``correct_maskPropagation``
is quantified unconditionally — but that does NOT make the lane vacuous, and the
absence of a precondition is not the reason it would be. The analogue of
PRECOND-TOO-STRONG on a total carrier is the modeled decision being
UNSATISFIABLE at exactly an F2P-shaped input: the frozen obligation could be
quantified over everything and still be dischargeable only because some arm's
demanded value is unreachable by evaluation. ``admiss-f2p-lone-grid`` tests that
directly — it evaluates the modeled routine at the concrete F2P-shaped input
(this operand carries a flag grid, the other does not, a merge callback IS
supplied), pins the produced value by ``rfl``, and discharges (D-merge) at that
point as a ``have`` BEFORE closing the frozen obligation verbatim. If the arm the
fix repairs were unsatisfiable at that input the ``have`` could not close.

AXIOM lane: DROPPED. The nagini bundle's ``AXIOM_TESTS`` belong to G-AX, which
the G-PBT spec lane ignores; this bundle consumes no callee axiom (the merge
callback is an explicit INPUT parameter quantified over all `Combine`, not an
axiomatized callee — meta.json records G-AX skip).
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14995"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region: the positive reshapes land entirely inside
# it. The frozen proof closes both reshapes verbatim (the per-arm result values
# are unchanged and the theorem statement is byte-identical), so no proof-region
# surgery is needed.
_IMPL = (
    "-- impl-start\n"
    "def implementation_maskPropagation\n"
    "    (selfMask operandMask : Option Mask) (handleMask : Option Combine) :\n"
    "    Except Unit (Option Mask) := Id.run do\n"
    "  -- No combining requested, or neither operand carries a mask: no result mask.\n"
    "  match handleMask with\n"
    "  | none => return .ok none\n"
    "  | some hm =>\n"
    "    match selfMask, operandMask with\n"
    "    | none,    none    => return .ok none\n"
    "    -- Exactly one operand carries a mask: copy it over unchanged.\n"
    "    | none,    some om => return .ok (some om)\n"
    "    | some sm, none    => return .ok (some sm)\n"
    "    -- Both operands carry a mask: merge them with the combining function.\n"
    "    | some sm, some om => return .ok (some (hm sm om))\n"
    "-- impl-end"
)

# per-arm anchors (each a unique substring lying entirely inside the impl region)
_ARM_NOCOMB = "  | none => return .ok none"
_ARM_BOTH_NONE = "    | none,    none    => return .ok none"
_ARM_ONLY_OTHER = "    | none,    some om => return .ok (some om)"
_ARM_ONLY_SELF = "    | some sm, none    => return .ok (some sm)"
_ARM_BOTH = "    | some sm, some om => return .ok (some (hm sm om))"

# The frozen proof's intro line (proof region, unique in the file), so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec regions.
_P_INTRO = "  intro selfMask operandMask handleMask"


# === POSITIVE CONTROLS (soundness) — structurally different but CORRECT =======
# implementations that MUST verify. If a faithful correct implementation cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Both keep the same
# per-arm result values as gold, so the FROZEN proof closes them verbatim (the
# proof case-splits on the inputs and closes each arm by `rfl`, which is
# insensitive to the match layout); the `correct_maskPropagation` statement is
# byte-identical and no new declaration/axiom is introduced.

# --- pos-reorder-arms: same single `match`, arms written in reverse order. ----
_IMPL_REORDER = (
    "-- impl-start\n"
    "def implementation_maskPropagation\n"
    "    (selfMask operandMask : Option Mask) (handleMask : Option Combine) :\n"
    "    Except Unit (Option Mask) := Id.run do\n"
    "  match handleMask with\n"
    "  | some hm =>\n"
    "    match selfMask, operandMask with\n"
    "    | some sm, some om => return .ok (some (hm sm om))\n"
    "    | some sm, none    => return .ok (some sm)\n"
    "    | none,    some om => return .ok (some om)\n"
    "    | none,    none    => return .ok none\n"
    "  | none => return .ok none\n"
    "-- impl-end"
)
POS_REORDER = _swap(_BASE, _IMPL, _IMPL_REORDER)

# --- pos-nested-match: split the paired match into two nested single matches. -
# A different control-flow shape (nest on `selfMask`, then on `operandMask`)
# producing the identical per-arm values. Stands in for the nagini admissibility
# case: it confirms the decision is discharged across the FULL input domain.
_IMPL_NESTED = (
    "-- impl-start\n"
    "def implementation_maskPropagation\n"
    "    (selfMask operandMask : Option Mask) (handleMask : Option Combine) :\n"
    "    Except Unit (Option Mask) := Id.run do\n"
    "  match handleMask with\n"
    "  | none => return .ok none\n"
    "  | some hm =>\n"
    "    match selfMask with\n"
    "    | none =>\n"
    "      match operandMask with\n"
    "      | none    => return .ok none\n"
    "      | some om => return .ok (some om)\n"
    "    | some sm =>\n"
    "      match operandMask with\n"
    "      | none    => return .ok (some sm)\n"
    "      | some om => return .ok (some (hm sm om))\n"
    "-- impl-end"
)
POS_NESTED = _swap(_BASE, _IMPL, _IMPL_NESTED)


# === ADMISSIBILITY ===========================================================
# Confirm the modeled decision is SATISFIABLE (non-vacuous) at exactly an
# F2P-shaped input. The frozen obligation quantifies over everything, so there is
# no precondition to re-derive; the analogue on this total carrier is that the
# value (D-merge) DEMANDS at the discriminating input is actually reachable by
# evaluation. The `have` computes the routine's result at that input by `rfl`,
# rewrites (D-merge) with it, and closes — then the frozen tactic body runs
# verbatim. Nothing is assumed: no new declaration, no axiom, the
# `correct_maskPropagation` STATEMENT is byte-identical, and the ground instance
# is a `have` prepended inside the existing tactic body.
_ADMISS_HAVE = (
    "  -- admissibility: the modeled decision is SATISFIABLE at the F2P-shaped\n"
    "  -- input — THIS operand carries a flag grid, the OTHER does not, and a\n"
    "  -- merge callback IS supplied (the discriminating category). Discharged by\n"
    "  -- evaluation as a `have`, before the frozen obligation is closed verbatim.\n"
    "  have _ground : problem_spec_maskPropagation (some [1, 2]) none "
    "(some (fun a b => a ++ b))\n"
    "      (implementation_maskPropagation (some [1, 2]) none "
    "(some (fun a b => a ++ b))) := by\n"
    "    have hval : implementation_maskPropagation (some [1, 2]) none "
    "(some (fun a b => a ++ b))\n"
    "        = Except.ok (some [1, 2]) := by rfl\n"
    "    rw [problem_spec_maskPropagation, hval]\n"
)
ADMISS_F2P = _swap(_BASE, _P_INTRO, _ADMISS_HAVE + _P_INTRO)


# === UNIQUENESS / REJECT rivals ==============================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# corrupts exactly one arm of the (D-merge) clause and carries a refutation
# witness pinning the violation at one concrete input, checked to hold of the
# rival and to FAIL on the frozen solution.

# no-callback arm must yield the no-grid result irrespective of the grids;
# this rival echoes `selfMask` there instead.
RIVAL_NOCOMB = _swap(_BASE, _ARM_NOCOMB, "  | none => return .ok selfMask")

# neither-carries arm must yield the no-grid result; this rival returns an
# (empty) grid, flipping the no-grid / grid distinction.
RIVAL_PRESENT = _swap(_BASE, _ARM_BOTH_NONE,
                      "    | none,    none    => return .ok (some [])")

# only-the-other-carries arm must copy the OTHER operand's grid over; this rival
# drops it and returns the no-grid result.
RIVAL_DROP_OTHER = _swap(_BASE, _ARM_ONLY_OTHER,
                         "    | none,    some om => return .ok none")

# only-THIS-carries arm must copy THIS operand's grid over (THE FIX); the
# prepatch consulted the merge callback against the missing operand grid and
# crashed — modeled here as an `Except.error` result.
RIVAL_ONLY_SELF_ERR = _swap(_BASE, _ARM_ONLY_SELF,
                            "    | some sm, none    => return .error ()")

# both-carry arm must apply the merge callback; this rival ignores it and copies
# THIS operand's grid over instead.
RIVAL_IGNORE_CB = _swap(_BASE, _ARM_BOTH,
                        "    | some sm, some om => return .ok (some sm)")


# ---- witnesses (each checked: elaborates vs rival, FAILS vs frozen) ----------
_P = "problem_spec_maskPropagation"
_I = "implementation_maskPropagation"


def _wit(sm, om, hm):
    # State the negated spec predicate at a concrete input. `simp only [...]`
    # reduces the `Id.run`/`pure` wrapper and unfolds the two defs; `simp`
    # discharges the resulting concrete `Except`/`Option`/`List` disequality.
    # The callback (when present) is taken concretely as list append so the
    # both-present arm reduces.
    return (
        f"example : ¬ {_P} {sm} {om} {hm}\n"
        f"    ({_I} {sm} {om} {hm}) := by\n"
        f"  simp only [{_P}, {_I}, Id.run, pure]\n"
        f"  simp\n"
    )


_CB = "(some (fun a b => a ++ b))"
# no callback, self carries [1] -> spec .ok none; echo-self rival -> .ok (some [1]).
_WIT_NOCOMB = _wit("(some [1])", "none", "none")
# callback, neither carries -> spec .ok none; present-flip rival -> .ok (some []).
_WIT_PRESENT = _wit("none", "none", _CB)
# callback, only other carries [1] -> spec .ok (some [1]); drop-other rival -> .ok none.
_WIT_DROP_OTHER = _wit("none", "(some [1])", _CB)
# callback, only self carries [7] -> spec .ok (some [7]); prepatch rival -> .error ().
_WIT_ONLY_SELF = _wit("(some [7])", "none", _CB)
# callback, both carry [1]/[2] -> spec .ok (some [1,2]); ignore-cb rival -> .ok (some [1]).
_WIT_IGNORE_CB = _wit("(some [1])", "(some [2])", _CB)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different but CORRECT: the SAME single match, "
        "its five arms written in reverse order (both-present first, no-callback "
        "last). Every arm produces the identical per-input value, so (D-merge) "
        "still holds and the FROZEN proof — which case-splits and closes each arm "
        "by `rfl`, insensitive to arm order — discharges it verbatim; the "
        "`correct_maskPropagation` statement is byte-identical and no new "
        "declaration/axiom is added. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-nested-match",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_NESTED,
        "rationale": "structurally-different but CORRECT: split the paired "
        "`match selfMask, operandMask` into two nested single matches (on "
        "`selfMask`, then on `operandMask`). A different control-flow shape "
        "producing identical per-arm values, so (D-merge) holds and the frozen "
        "proof closes it verbatim. Must verify (else SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY (non-vacuity at an F2P-shaped input)
    # =====================================================================
    {
        "id": "admiss-f2p-lone-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_F2P,
        "rationale": "the modeled decision is SATISFIABLE at exactly the "
        "discriminating F2P-shaped input: THIS operand carries a flag grid "
        "([1,2]), the OTHER carries none, and a merge callback IS supplied. The "
        "routine's result at that input is computed by `rfl` "
        "(`Except.ok (some [1,2])`) and (D-merge) is discharged there as a "
        "`have`, before the frozen tactic body closes the obligation verbatim. "
        "This is the analogue of PRECOND-TOO-STRONG on a total carrier: the "
        "frozen obligation quantifies over all inputs, so there is no "
        "precondition to re-derive, but it could still be dischargeable while "
        "the value (D-merge) DEMANDS on this arm is unreachable by evaluation — "
        "which is precisely the arm the F2P exercises. Verifying shows the "
        "obligation is non-vacuous where it matters. Nothing is assumed: no new "
        "declaration or axiom, the `correct_maskPropagation` statement is "
        "byte-identical, and the ground instance is a `have` inside the existing "
        "tactic body. Ports nagini's admiss-precond-consistent.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals (each corrupts one arm of (D-merge))
    # =====================================================================
    {
        "id": "prepatch-only-self-errors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_ONLY_SELF_ERR,
        "refinement": "this is the literal pre-patch behaviour: when only THIS "
        "operand carries a grid, the routine consulted the merge callback against "
        "the missing operand grid and crashed (modeled as `.error ()`) instead of "
        "copying the lone grid over. The F2P multiplies a masked operand by a "
        "flag-less one with a bitwise-or callback and asserts the result grid "
        "equals the lone grid; a crash / error result fails that assertion, so a "
        "faithful patch keeping this arm's crash does NOT resolve.",
        "rationale": "REJECT from (D-merge): the only-self-carries arm must be "
        "`.ok (some sm)` (copy this grid over), but the rival yields `.error ()`. "
        "Attacks the `selfMask=some, operandMask=none` arm; witness varies "
        "`selfMask` to `some [7]` with `operandMask=none`: spec is .ok (some [7]), "
        "rival is .error ().",
        "witness": _WIT_ONLY_SELF,
    },
    {
        "id": "drop-other-operand-grid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_DROP_OTHER,
        "refinement": "when only the OTHER operand carries a grid the rival drops "
        "it and returns no grid. The F2P multiplies a flag-less operand by a "
        "masked one and asserts the masked operand's grid propagates to the "
        "result; returning no grid loses those flags, so it does NOT resolve.",
        "rationale": "REJECT from (D-merge): the only-other-carries arm must copy "
        "the OTHER operand's grid (`.ok (some om)`), but the rival returns "
        "`.ok none`. Attacks the `selfMask=none, operandMask=some` arm and "
        "demonstrates dependence on the `operandMask` binder: at "
        "`operandMask=some [1]` the spec is .ok (some [1]), the rival is .ok none.",
        "witness": _WIT_DROP_OTHER,
    },
    {
        "id": "no-grid-flipped-to-grid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PRESENT,
        "refinement": "when a callback is supplied but NEITHER operand carries a "
        "grid, the rival returns an (empty) grid where none is due, flipping the "
        "no-grid / grid distinction. The F2P asserts the no-mask * no-mask "
        "products carry NO mask (a `None` result); a non-None empty-grid result "
        "fails that assertion, so it does NOT resolve.",
        "rationale": "REJECT from (D-merge): the neither-carries arm must be "
        "`.ok none` (no result grid), but the rival returns `.ok (some [])`. "
        "Attacks the `selfMask=none, operandMask=none` arm — the no-grid vs grid "
        "boundary (the `Except.ok none` vs `Except.ok (some _)` distinction).",
        "witness": _WIT_PRESENT,
    },
    {
        "id": "no-callback-echoes-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_NOCOMB,
        "refinement": "when NO merge callback is supplied the result must carry no "
        "grid regardless of the operands; the rival echoes `selfMask` there. A "
        "faithful patch that propagated a grid when no callback was requested "
        "would attach a mask to products the caller asked to leave unmasked, "
        "breaking the no-callback contract the F2P relies on — does NOT resolve.",
        "rationale": "REJECT from (D-merge): the no-callback arm must be "
        "`.ok none` for ANY grids, but the rival returns `.ok selfMask`. Attacks "
        "the `handleMask=none` arm and demonstrates dependence on the `handleMask` "
        "binder: at `handleMask=none, selfMask=some [1]` the spec is .ok none, the "
        "rival is .ok (some [1]).",
        "witness": _WIT_NOCOMB,
    },
    {
        "id": "both-carry-ignores-callback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_IGNORE_CB,
        "refinement": "when BOTH operands carry a grid the result must be the merge "
        "callback applied to both; the rival ignores the callback and copies THIS "
        "operand's grid. The F2P multiplies two distinct masked operands with "
        "bitwise-or and asserts the result equals the bitwise-or of the two grids; "
        "returning one operand's grid unchanged differs whenever the grids differ, "
        "so it does NOT resolve.",
        "rationale": "REJECT from (D-merge): the both-carry arm must be "
        "`.ok (some (hm sm om))` (the callback applied to both), but the rival "
        "returns `.ok (some sm)`, ignoring the callback and `operandMask`. Attacks "
        "the `selfMask=some, operandMask=some` arm; at grids [1]/[2] with append "
        "as the callback the spec is .ok (some [1,2]) and the rival is .ok (some [1]).",
        "witness": _WIT_IGNORE_CB,
    },
]
