# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7757 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for the positive, the proof body — is edited), checked by
# variant_scope + the Lean verifier. Every expect="reject" case carries a refutation
# `witness`: a self-contained snippet that ELABORATES against the rival and FAILS on
# the frozen solution, so the rejection is attributable to the spec and not to a
# tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   positionalDefaults : Nat → Nat → List String → List (Option String)
#   Given the two consecutive positional-parameter group sizes (nPosonly, then
#   nArgs) and a flat list of supplied default expressions, reports the default
#   carried by each of the nPosonly + nArgs positional parameters, in order. By the
#   usual positional rule the supplied defaults fill the RIGHTMOST parameters across
#   the whole positional run; every earlier parameter has none. The single
#   postcondition pins the result to
#     replicate (nPosonly + nArgs − defaults.length) none  ++  defaults.map some
#   grounded entirely in the function's own inputs.
#
#   Independent aspects of that one clause (the spec's teeth):
#     C1  length == nPosonly + nArgs                       (one slot / parameter)
#     C2  the supplied defaults occupy the rightmost slots, IN ORDER, each `some`
#     C3  the positional-only prefix is NOT exempt: a default landing on one of the
#         rightmost slots is kept even when that slot is a positional-only parameter
#         (the exact behaviour the change introduces)
#
# CARRIER NOTE: the nagini sibling modeled a richer surface (a padded index loop
# with fractional-permission read-only inputs and a grounded @Pure alignment helper).
# This backend models only the pure alignment as a single transparent list equation
# over Nat / List String / List (Option String) — no opaque callees. So every
# aspect above is refutable at a concrete input.
#
# WITNESS TACTIC — read `_wit` before touching it. The obvious `unfold …; decide`
# does NOT discriminate on this carrier: the frozen impl is an `Id.run do` whose
# `for _ in [a:b]` elaborates to a `Std.Range` `forIn` the kernel will not unfold,
# so `decide` gets STUCK against the frozen impl for every claim regardless of
# truth, and a gold-side failure of that shape attests to nothing. Each witness
# therefore closes by `simp [<spec>, <impl>]`, which normalizes the loop to closed
# form before the equality is decided, so the frozen-impl build fails by DECIDING
# the claim false (`unsolved goals |- False`). Every witness below was rebuilt both
# ways: rival exit 0, frozen-impl exit 1 with `unsolved goals`.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY class: `provided` was Acc(.,1/2) read-only,
#     so a write-back rival was rejected for INSUFFICIENT PERMISSION). Lean is
#     referentially transparent — no aliasing, no fractional permission, and no way
#     for an impl to observe a mutation of its own argument — so a "write a
#     read-only input" rival is not expressible and the whole lane is VACUOUS here.
#     The frame OBLIGATION the permission system carried (pin the parts that do not
#     change) has no residue either: the modeled function returns one freshly-built
#     value and the spec pins that value in full, so there is no output component
#     left unconstrained for a wrong impl to fill freely. See 'assessment'; no
#     substitute is fabricated.
#   * AXIOM_TESTS. The bundle declares no @ContractOnly axiom / opaque callee (the
#     rendering and parsing are subsumed into the List String input); the axiom lane
#     is G-AX's job and this gate ignores it.
#
# LANE THAT DOES PORT (dropped in the first pass, restored here):
#   * ADMISSIBILITY — see `admiss-normal-shape`. The lean obligation carries its
#     precondition as a binder HYPOTHESIS (`defaults.length ≤ nPosonly + nArgs → …`)
#     rather than a spec conjunct, but that does not make the lane N/A: a hypothesis
#     can be unsatisfiable at the shapes the modeled behavior actually presents, and
#     a theorem discharged over a vacuous hypothesis proves nothing about them. The
#     probe is expressible on this carrier and costs four `example`s: two
#     establishing the hypothesis, and — the load-bearing half, added by audit —
#     two discharging the whole OBLIGATION by evaluation at those same inputs.
#
# DIVERGENCE LANE (F′) — a demonstrated non-class, not a dropped one. This bundle
#     sets NO `loom.semantics.termination` option: it is plain Lean, where every
#     `def` is total by elaboration and a non-terminating impl cannot be written at
#     all without `partial`. Measured both escapes: a `partial def spin n := spin
#     (n+1)` rival and a `partial def` pad loop each build to module exit 1, but
#     their witnesses FAIL too (exit 1, `simp made no progress` / an unreduced
#     `¬ spin 2 = [some "1"]`) — `partial` makes the function opaque to the kernel
#     and to `simp`, so nothing can be refuted at any input. So a diverging rival
#     is neither shippable (no witness can hold of it) nor a spec hole (the frozen
#     obligation still cannot be discharged for it). There is nothing to add.
#
# ATTACK-E RESULTS worth recording (both were left UNCERTAIN by the previous pass
#     and are now settled, by build): a right-appending pad loop
#     (`acc := acc ++ [none]`, the opposite accumulation direction from the frozen
#     impl) VERIFIES, closed by `simp [Std.Range.forIn_eq_forIn_range',
#     Std.Range.size, List.forIn_pure_yield_eq_foldl]`; and the index-mapped walk
#     over `List.range (nPosonly + nArgs)` VERIFIES, closed by
#     `List.ext_getElem?` plus `List.getElem?_range` / `_append_left` /
#     `_append_right` / `_replicate` and an in-bounds `omega` fact. Neither is a
#     SPEC-TOO-STRONG hole. Not added as cases: `pos-recursive-pad` already
#     carries the lane with a non-definitional proof.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7757"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchor: the ENTIRE impl body (lies inside impl-start/impl-end and
# is unique in the file). Every value-rival replaces this whole definition; the spec
# and the `theorem correct_*` STATEMENT are untouched. ------------------------------
_IMPL = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
  let positionals := nPosonly + nArgs
  -- Start from the supplied defaults and left-pad with "no default" until there
  -- is one entry per positional parameter; the defaults thus land on the
  -- rightmost positions across the whole positional run.
  let mut padded : List (Option String) := defaults.map some
  for _ in [padded.length:positionals] do
    padded := none :: padded
  return padded"""
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# --- proof-region anchor: the frozen tactic body (unique; only the positive edits
# it, to reprove its restated impl). ------------------------------------------------
_PROOF = """  simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
    Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
    List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
    bind_pure, Id.run_pure]"""
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------
# Structurally different but behaviourally identical: the frozen impl BUILDS the
# result imperatively (start from the defaults, prepend "no default" until one entry
# per parameter). This control states the SAME value as the direct functional
# expression the spec names — a shape a faithful patch could equally take. Because it
# is now definitionally the spec's right-hand side, the reproof closes by `rfl`; the
# `theorem correct_positionalDefaults` STATEMENT is kept byte-identical. If it FAILS
# => SPEC-TOO-STRONG (a faithful, structurally-different correct impl rejected).
_POS_IMPL = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  List.replicate (nPosonly + nArgs - defaults.length) none ++ defaults.map some"""
POS = _swap(_swap(_BASE, _IMPL, _POS_IMPL), _PROOF, "  rfl")


# SECOND POSITIVE CONTROL (soundness) — must VERIFY, and unlike POS it is NOT
# definitionally the spec's right-hand side, so it actually exercises the spec.
#
# POS above is an honest positive but a WEAK one: its impl is syntactically the
# spec's RHS, so `rfl` closes it and the only thing demonstrated is that the spec
# is reflexive at its own definition. This control pads by RECURSION on the
# pad count instead of by `List.replicate`, using an impl-region helper `def`
# (legal: the spec view elides the impl region). It is extensionally the same
# function, but proving it needs a real induction relating the recursive pad to
# `List.replicate` — no definitional shortcut. A faithful patch could equally
# build the padding by recursion, so if this FAILS => SPEC-TOO-STRONG.
_POS2_IMPL = """def padNoDefault : Nat → List (Option String) → List (Option String)
  | 0, xs => xs
  | k + 1, xs => none :: padNoDefault k xs

def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  padNoDefault (nPosonly + nArgs - defaults.length) (defaults.map some)"""
_POS2_PROOF = """  generalize nPosonly + nArgs - defaults.length = k
  induction k with
  | zero => simp [padNoDefault]
  | succ n ih => simp [padNoDefault, List.replicate_succ, ih]"""
POS2 = _swap(_swap(_BASE, _IMPL, _POS2_IMPL), _PROOF, _POS2_PROOF)


# ADMISSIBILITY — the obligation must be SATISFIABLE at a normal input, not merely
# discharged over a hypothesis that might be empty there.
#
# The port first recorded this lane as N/A because the precondition is a binder
# hypothesis rather than a spec conjunct. That reasoning is incomplete: a
# hypothesis can still be unsatisfiable at the shapes the modeled behavior
# actually presents, and a discharged theorem over a vacuous hypothesis proves
# nothing about them.
#
# AUDIT REPAIR: the previous version of this probe established ONLY the binder
# hypothesis (`defaults.length ≤ nPosonly + nArgs` at two concrete shapes). That
# is the weaker half and on its own it is nearly free — `2 ≤ 3` is true whatever
# the spec says, so the case would have verified even against a postcondition
# that no input can satisfy. The lane's actual question is whether the
# OBLIGATION — hypothesis AND conclusion together — holds at an F2P-shaped
# input, which is what distinguishes PRECOND-TOO-STRONG from a satisfiable
# precondition. So the probe now also discharges the postcondition BY EVALUATION
# at that concrete input, as a `have`-style `example`, before the frozen
# obligation is closed verbatim below it. The two shapes are: a normal signature
# whose trailing default block reaches into the positional-only prefix (two
# supplied defaults over three positional parameters), and the degenerate empty
# shape. If any of these could not be established the precondition or the
# postcondition rejects an input the modeled behavior must handle
# => PRECOND-TOO-STRONG.
_ADMISS_PROBE = _IMPL + """

-- The binder hypothesis is satisfiable at both shapes ...
example : (["0", "1"] : List String).length ≤ 2 + 1 := by decide
example : ([] : List String).length ≤ 0 + 0 := by decide

-- ... and, the load-bearing half, the OBLIGATION itself holds at each of them
-- by evaluation, so the frozen theorem below is not discharged over a hypothesis
-- that is empty at exactly the shapes the modeled behavior presents.
example : problem_spec_positionalDefaults 2 1 ["0", "1"]
    (implementation_positionalDefaults 2 1 ["0", "1"]) := by
  simp [problem_spec_positionalDefaults, implementation_positionalDefaults]

example : problem_spec_positionalDefaults 0 0 []
    (implementation_positionalDefaults 0 0 []) := by
  simp [problem_spec_positionalDefaults, implementation_positionalDefaults]"""
ADMISS = _swap(_BASE, _IMPL, _ADMISS_PROBE)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits only the impl region (keeping the frozen proof), and carries a
# witness proving it violates the spec at one concrete input.
# ---------------------------------------------------------------------------

# R1 — POSONLY-EXEMPT (the headline pre-change bug): force the positional-only prefix
# to carry no default, dropping the trailing slots that would have fallen into it.
_R1_POSONLY = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  List.replicate nPosonly none ++
    (List.replicate (nPosonly + nArgs - defaults.length) none ++ defaults.map some).drop nPosonly"""

# R2 — WRONG-END ALIGNMENT: fill the defaults into the LEFTMOST parameters and pad on
# the right, inverting the positional rule.
_R2_ALIGN_LEFT = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  defaults.map some ++ List.replicate (nPosonly + nArgs - defaults.length) none"""

# R3 — ALL-NONE: report every parameter as having no default (drop every supplied
# default). Satisfies C1 (length) but pins the wrong value wherever a default is due.
_R3_ALL_NONE = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  List.replicate (nPosonly + nArgs) none"""

# R4 — SHORT RESULT: drop the final position, so the result has one slot too few.
_R4_SHORT = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  (List.replicate (nPosonly + nArgs - defaults.length) none ++ defaults.map some).dropLast"""

# R5 — SCRAMBLED ORDER: assign the supplied defaults to the rightmost slots but in
# REVERSED order, breaking the order-preservation of the alignment.
_R5_REVERSE = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  List.replicate (nPosonly + nArgs - defaults.length) none ++ defaults.reverse.map some"""

# R6 — SHIFTED-BOUNDARY ALIGNMENT (the nagini sibling's off-by-posonly rival,
# transcribed to this carrier). A parameter gets a default only once its index
# clears BOTH the padding and the whole positional-only prefix, and the index into
# the supplied defaults is shifted by that prefix too — i.e. the defaults are lined
# up against the positional-or-keyword count alone, as if the positional-only group
# consumed no default slots. Unlike R1 this keeps the RESULT LENGTH correct and is
# written as a per-index walk, so it attacks the alignment arithmetic on its own
# rather than riding on a truncation.
_R6_SHIFTED = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  (List.range (nPosonly + nArgs)).map (fun p =>
    if p < nPosonly + nArgs - defaults.length + nPosonly then none
    else defaults[p - (nPosonly + nArgs - defaults.length) - nPosonly]?)"""

# R7 — the PRE-CHANGE CONTROL FLOW itself, carried over verbatim from this
# bundle's own `Solution_prepatch.lean` impl region: build the positional-only
# group first with no default at all, then walk the positional-or-keyword group
# lining its defaults up only among themselves. Where R1 states the pre-change
# VALUE in closed form, this states the pre-change ALGORITHM — a two-loop
# imperative accumulation, the shape a faithful un-fixed patch actually has. That
# makes it the sharpest verify-does-not-imply-resolve control in the battery: the
# prepatch file is independently required to FAIL verification (G-DIFF), so a rival
# with this impl must be rejected here for the same reason.
_R7_PREV_FLOW = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
  let mut params : List (Option String) := []
  for _ in [0:nPosonly] do
    params := params ++ [none]
  for i in [0:nArgs] do
    if nArgs - i ≤ defaults.length then
      params := params ++ [some (defaults[defaults.length - (nArgs - i)]!)]
    else
      params := params ++ [none]
  return params"""

# R8 — WRONG DEFAULT TEXT, right slots: keep the result length, keep every `none`
# in the right place, keep every `some` in the right place, but put the FIRST
# supplied default's text in every defaulted slot. Nothing else in the battery
# probes per-slot value IDENTITY: R3 blanks the values, R5 permutes them, and both
# leave open a spec that only pinned "which slots are defaulted" plus the multiset
# of texts. This one is wrong purely in WHICH TEXT lands WHERE.
_R8_SAME_TEXT = """def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) :=
  List.replicate (nPosonly + nArgs - defaults.length) none ++
    defaults.map (fun _ => some (defaults.getD 0 ""))"""


def _wit(nPosonly, nArgs, defaults):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    input. Elaborates against a rival that diverges from the frozen result there,
    and must FAIL against the frozen impl by DECIDING the claim false.

    Closed by `simp [<spec>, <impl>]` rather than by `unfold … ; decide`. The
    difference is load-bearing and was measured on this cell.

    `decide` reduces the `Decidable` instance in the KERNEL. Against the frozen
    impl the result is an `Id.run do` whose `for _ in [a:b]` elaborates to a
    `Std.Range` `forIn` the kernel will not unfold, so `instDecidableEqList`
    reduction gets STUCK ("did not reduce to `isTrue` or `isFalse`") — for EVERY
    claim, true or false, at every input. A gold-side failure of that shape
    attests to nothing: it is a build that never evaluated the claim, so it
    cannot distinguish a real refutation from a tautology. (Measured: all five
    reject cases failed on the frozen impl this way, and the checker's own
    stuck-reduction screen then had to refute them against an alternative impl
    instead of the frozen one.)

    `simp` rewrites with the `Std.Range.forIn` / `Id.run` simp set that the
    frozen proof itself uses, so the loop is normalized to the closed-form list
    BEFORE the equality is decided. Against a rival the two sides then differ on
    a concrete `List (Option String)` literal and the negation closes; against
    the frozen impl the two sides normalize to the SAME literal, so `simp` turns
    the goal into `False` and reports `unsolved goals ⊢ False` — a semantic
    refutation of the concrete claim, which is exactly the discrimination the
    reject lane needs. Verified per case: rival exit 0, frozen-impl exit 1 with
    `unsolved goals`."""
    args = f"{nPosonly} {nArgs} {defaults}"
    return (
        f"example : ¬ problem_spec_positionalDefaults {args}\n"
        f"    (implementation_positionalDefaults {args}) := by\n"
        f"  simp [problem_spec_positionalDefaults, implementation_positionalDefaults]"
    )


def _wit_idx(nPosonly, nArgs, defaults):
    """As `_wit`, for a rival whose impl is an INDEX-MAPPED walk over
    `List.range (nPosonly + nArgs)`. Reducing that shape needs the `range`
    successor unfolding and the list-index lemma in the simp set as well; the
    plain `_wit` form leaves a `List.range`/`getElem?` residue and does not
    close against the rival. Same discrimination contract: it holds of the rival
    and reports `unsolved goals ⊢ False` against the frozen impl."""
    args = f"{nPosonly} {nArgs} {defaults}"
    return (
        f"example : ¬ problem_spec_positionalDefaults {args}\n"
        f"    (implementation_positionalDefaults {args}) := by\n"
        f"  simp [problem_spec_positionalDefaults, implementation_positionalDefaults,\n"
        f"    List.range_succ, List.getElem?_cons_succ]"
    )


SPEC_TESTS = [
    {
        "id": "pos-functional-form",
        "kind": "soundness",
        "expect": "verify",
        "module": POS,
        "rationale": (
            "structurally-different but CORRECT impl: the frozen impl BUILDS the "
            "result by prepending 'no default' entries until there is one per "
            "parameter; this control states the identical value as the direct "
            "right-alignment expression a faithful patch could equally write. The "
            "frozen `theorem correct_positionalDefaults` STATEMENT is byte-identical "
            "and the reproof closes by `rfl` (the impl is now definitionally the "
            "spec's RHS). If it FAILS => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected). NOTE its limit: being definitionally the RHS, it certifies "
            "little on its own — `pos-recursive-pad` below is the load-bearing "
            "soundness control."
        ),
    },
    {
        "id": "pos-recursive-pad",
        "kind": "soundness",
        "expect": "verify",
        "module": POS2,
        "rationale": (
            "the load-bearing soundness control: a CORRECT impl that is NOT "
            "definitionally the spec's right-hand side. It builds the 'no default' "
            "padding by RECURSION on the pad count (an impl-region helper `def`, "
            "which the elided impl region permits) instead of by `List.replicate`, "
            "so no definitional shortcut is available and the reproof must run a "
            "real induction relating the two. A faithful patch could equally pad by "
            "recursion, so if it FAILS => SPEC-TOO-STRONG. The frozen `theorem "
            "correct_positionalDefaults` STATEMENT is byte-identical."
        ),
    },
    {
        "id": "admiss-normal-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": (
            "the obligation carries its precondition as a binder HYPOTHESIS "
            "(`defaults.length ≤ nPosonly + nArgs → …`); a theorem discharged over "
            "an unsatisfiable hypothesis proves nothing about the inputs the "
            "modeled behavior must handle. Two `example`s inside the elided impl "
            "region establish the hypothesis at the shape a normal signature "
            "presents (two supplied defaults over three positional parameters) and "
            "at the degenerate empty shape. If either could not be established the "
            "precondition rejects a normal input => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "r1-posonly-exempt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R1_POSONLY),
        "refinement": (
            "this IS the pre-change bug: positional-only parameters were built with "
            "no default at all, so a default landing on the positional-only prefix "
            "was dropped. Its faithful real counterpart is the unchanged repo, which "
            "on '(a, b=0, /, c=1)' produces the positional-only `b` with no default — "
            "exactly the FAIL_TO_PASS test_signature_from_str_positionaly_only_args, "
            "which now asserts `b`'s default is '0'. It does NOT resolve, so a "
            "verifying rival here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by C3 (positional-only-not-exempt) and C2 (right-alignment): on "
            "an input whose trailing default block reaches into the positional-only "
            "prefix, the spec keeps that default `some`, but the rival forces the "
            "prefix slot to `none` and drops the corresponding trailing default. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # nPosonly=2, nArgs=1, defaults=["0","1"] (models '(a, b=0, /, c=1)'):
        # gold => [none, some"0", some"1"]; rival => [none, none, some"1"].
        "witness": _wit(2, 1, '["0", "1"]'),
    },
    {
        "id": "r2-align-left",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R2_ALIGN_LEFT),
        "refinement": (
            "a real patch that aligned the supplied defaults to the LEFTMOST "
            "parameters (padding the tail) instead of the rightmost would attach `c`'s "
            "default to `a` and leave the trailing parameter empty; the F2P test reads "
            "the defaults slot-by-slot and FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2 (the supplied defaults occupy the RIGHTMOST slots): on any "
            "input with fewer defaults than parameters the spec puts the `none`s "
            "first, but the rival puts them last. If it VERIFIES => SPEC-TOO-WEAK on "
            "the alignment-end sub-domain."
        ),
        # nPosonly=0, nArgs=2, defaults=["1"]:
        # gold => [none, some"1"]; rival => [some"1", none].
        "witness": _wit(0, 2, '["1"]'),
    },
    {
        "id": "r3-all-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R3_ALL_NONE),
        "refinement": (
            "a real patch that never attached any default (omitted the alignment "
            "entirely) reports every parameter with no default; the F2P test reads "
            "b='0', c='1' and FAILS. The cheapest impl that satisfies the length "
            "clause but not the value pin. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2 (the value pin): wherever a default is due the spec "
            "requires `some d`, which `none` cannot satisfy. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # nPosonly=0, nArgs=1, defaults=["1"]:
        # gold => [some"1"]; rival => [none].
        "witness": _wit(0, 1, '["1"]'),
    },
    {
        "id": "r4-short-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R4_SHORT),
        "refinement": (
            "a real patch with an off-by-one over the positional parameters omits the "
            "final parameter's entry entirely; the F2P test's parameter list would be "
            "missing its last element and FAIL. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1 (length == nPosonly + nArgs): the rival returns one slot "
            "too few. If it VERIFIES => SPEC-TOO-WEAK on the length clause."
        ),
        # nPosonly=1, nArgs=2, defaults=["9"]:
        # gold => [none, none, some"9"]; rival => [none, none] (dropLast).
        "witness": _wit(1, 2, '["9"]'),
    },
    {
        "id": "r5-scrambled-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R5_REVERSE),
        "refinement": (
            "a real patch that indexed the supplied defaults in the wrong direction "
            "would attach them to the correct (rightmost) parameters but in reversed "
            "order — e.g. `b` gets `c`'s default and vice versa; the F2P test reads "
            "each default position-by-position and FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2 (the defaults occupy the rightmost slots IN ORDER): the "
            "spec pins `defaults.map some`, the rival pins `defaults.reverse.map "
            "some`. If it VERIFIES => SPEC-TOO-WEAK on the order sub-domain."
        ),
        # nPosonly=0, nArgs=2, defaults=["0","1"]:
        # gold => [some"0", some"1"]; rival => [some"1", some"0"].
        "witness": _wit(0, 2, '["0", "1"]'),
    },
    {
        "id": "r6-shifted-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R6_SHIFTED),
        "refinement": (
            "a real patch that lined the supplied defaults up against the "
            "positional-or-keyword count ALONE — as if the positional-only group "
            "consumed no default slots — shifts both the boundary and the index by "
            "the size of that prefix. It reports the right NUMBER of parameters "
            "but attaches the defaults at the wrong positions: on a signature with "
            "one positional-only and one positional-or-keyword parameter, both "
            "defaulted, the positional-only one comes out with no default at all "
            "and the other takes its neighbour's expression. The F2P test reads "
            "the defaults slot-by-slot and FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C3 (the positional-only prefix is not exempt) and C2 (the "
            "supplied defaults occupy the rightmost slots, in order). Distinct from "
            "r1: this rival keeps C1 (the length is exactly nPosonly + nArgs) and is "
            "written as a per-index walk, so it isolates the ALIGNMENT ARITHMETIC "
            "instead of riding on a truncation — the sub-domain r1 leaves open is a "
            "spec that pinned only 'how many slots' plus 'the prefix is blank'. "
            "NOTE, corrected by audit: this rival does NOT preserve gold's number "
            "of defaulted slots. Because the offset is applied twice (once to the "
            "boundary, once to the index) it always emits FEWER defaults than are "
            "supplied, and once nPosonly is large enough relative to nArgs it emits "
            "none at all — at nPosonly=2, nArgs=1 it is observably identical to "
            "r3's all-none impl. The witness is therefore stated at nPosonly=1, "
            "nArgs=1, where it still emits a default and so is distinct from every "
            "other rival in the battery. If it VERIFIES => SPEC-TOO-WEAK on the "
            "boundary/offset sub-domain."
        ),
        # AUDIT REPAIR — the witness input was moved. It used to be
        # nPosonly=2, nArgs=1, defaults=["0","1"], where this rival evaluates to
        # [none, none, none]: at that shape the doubled `nPosonly` offset pushes
        # the boundary past the END of the result, so the rival degenerates to
        # ALL-NONE and is observably identical to r3's impl there. Refuting it at
        # that point therefore attested only to the value pin r3 already covers,
        # not to the boundary/offset arithmetic this case exists for — and the
        # in-comment expectation `rival => [none, none, some"0"]` was itself
        # wrong. (Measured by evaluation: at 2 1 ["0","1"] this rival = r3's impl;
        # searching nPosonly,nArgs<7 found NO input where it keeps gold's
        # defaulted-slot count, so the shape below is the sharpest available.)
        #
        # nPosonly=1, nArgs=1, defaults=["0","1"] (models '(a=0, /, b=1)'):
        # gold => [some"0", some"1"]; rival => [none, some"0"].
        # At this input the rival still EMITS a default, so the refutation lands
        # on the misalignment itself: the slot that should carry "0" carries
        # nothing (C3 — the positional-only prefix is not exempt) and the slot
        # that should carry "1" carries "0" (C2 — wrong index into the supplied
        # defaults). It is also distinct from every other rival's value here.
        "witness": _wit_idx(1, 1, '["0", "1"]'),
    },
    {
        "id": "r7-prev-control-flow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R7_PREV_FLOW),
        "refinement": (
            "this is the pre-change ALGORITHM rather than its closed-form value: "
            "build the positional-only group first with no default at all, then walk "
            "the positional-or-keyword group lining its defaults up only among "
            "themselves. It is the control flow an un-fixed patch actually has — the "
            "impl this bundle independently ships as its FAILING prepatch skeleton — "
            "so on '(a, b=0, /, c=1)' the positional-only `b` carries no default and "
            "the FAIL_TO_PASS test_signature_from_str_positionaly_only_args, which "
            "now asserts `b`'s default is '0', FAILS. Does NOT resolve; a verifying "
            "rival here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by C3 (positional-only-not-exempt) and C2 (right-alignment "
            "across the whole positional run). Distinct from r1 and r6 in SHAPE, not "
            "just in value: those state the wrong result as a closed-form list "
            "expression, while this is a two-loop imperative accumulation with a "
            "`getElem!` index into the supplied defaults. That matters because the "
            "frozen obligation is discharged by a tactic script tuned to a "
            "loop-shaped impl, so a rival in loop form is the case where 'the script "
            "stopped matching' and 'the spec is violated' are hardest to tell apart "
            "— and the witness separates them. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # nPosonly=2, nArgs=1, defaults=["0","1"]:
        # gold => [none, some"0", some"1"]; rival => [none, none, some"1"].
        "witness": _wit(2, 1, '["0", "1"]'),
    },
    {
        "id": "r8-wrong-default-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R8_SAME_TEXT),
        "refinement": (
            "a real patch that resolved WHICH parameters are defaulted correctly but "
            "read the wrong element when rendering each one — e.g. by holding the "
            "index fixed across the loop — reports every defaulted parameter with "
            "the first supplied expression. On '(a, b=0, /, c=1)' `c` would come out "
            "with '0' instead of '1'; the F2P test asserts both defaults by value and "
            "FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2, on the sub-clause the rest of the reject lane leaves "
            "unattacked: which TEXT lands in which slot. This rival satisfies C1 "
            "(length), satisfies C3 (the positional-only prefix keeps its default), "
            "puts every `none` and every `some` in exactly the right position, and "
            "even carries the right multiset of expressions when the defaults happen "
            "to be equal — it is wrong only in the per-slot value identity. r3 blanks "
            "the values and r5 permutes them, so both would still be rejected by a "
            "spec that pinned only the defaulted-slot PATTERN plus the multiset of "
            "texts; this one would not. If it VERIFIES => SPEC-TOO-WEAK on the "
            "value-identity sub-domain."
        ),
        # nPosonly=0, nArgs=2, defaults=["0","1"]:
        # gold => [some"0", some"1"]; rival => [some"0", some"0"].
        "witness": _wit(0, 2, '["0", "1"]'),
    },
]


# No @ContractOnly axioms and no opaque callees: the alignment is modeled DEEPLY as a
# transparent list equation, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
