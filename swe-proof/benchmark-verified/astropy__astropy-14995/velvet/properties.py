"""properties.py — G-PBT falsification battery for astropy__astropy-14995 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives). It is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, ``resolveMask``):

  resolveMask (selfMask operandMask : Option (List Int))
              (handleMaskNone operandPresent : Bool)
              (combine : List Int → List Int → List Int)
    -> out : Option (List Int)
  require operandPresent = true
  ensures  handleMaskNone = true                                   → out = none
  ensures (¬handle ∧ selfMask = none ∧ operandMask = none)         → out = none
  ensures (¬handle ∧ selfMask = none ∧ operandMask ≠ none)         → out = operandMask
  ensures (¬handle ∧ selfMask ≠ none ∧ operandMask = none)         → out = selfMask
  ensures (¬handle ∧ selfMask ≠ none ∧ operandMask ≠ none)         → out = some (combine …)

The result is a five-way case split on which operand carries a mask
(``some``/``none``) and whether the caller declined mask handling. Each operand
mask is modelled DEEPLY over ``Option (List Int)`` (no opaque oracle to echo;
the ``axioms`` region is empty). ``combine`` is the caller-supplied elementwise
merger — a FUNCTION PARAMETER, applied only in the both-present arm; the tester
below feeds a concrete lambda, so the both-present output is observable.

The postcondition has FIVE independent top-level clauses; the rivals attack each
in turn:
  * clause 1 (handling declined ⇒ ``none``)                — R-decline
  * clause 2 (neither mask present ⇒ ``none``)             — R-both-absent
  * clause 3 (only second mask present ⇒ carry it over)    — R-swap-carry
  * clause 4 (only first mask present ⇒ carry it over)     — R-carry-vs-combine  (THE FIX)
  * clause 5 (both present ⇒ combiner applied)             — R-drop-combine

The load-bearing clause is clause 4: when the FIRST operand carries a mask and
the SECOND does not, the result must be the first mask carried over unchanged —
NEVER the combiner applied against an absent mask. That is exactly the behaviour
the failing scenario exercises (a masked operand combined with a mask-less one);
the pre-patch skeleton routed it to the combiner and raised.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini class exists because an
    input may carry a fractional heap permission an impl can overwrite in place
    (``self.mask.append`` / rebinding ``operand.mask``). Lean and Velvet are
    referentially transparent: ``selfMask`` / ``operandMask`` are immutable
    values (the method declares NO ``mut`` parameter), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe to
    build. Not fabricated — reported N/A in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. Every clause pins ``out`` to the method's own
    inputs (``none`` / ``operandMask`` / ``selfMask`` / ``combine`` applied to
    the present masks); the ``axioms`` region is empty, so there is no opaque
    answer-key an impl could echo without doing the work.
  * PARTIAL-DOMAIN / VALUE — the main class. Each rival is right on part of the
    case split and wrong on one sub-domain, refuted at a concrete input in that
    sub-domain.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``): ``resolveMaskTester args =
false`` says the extracted program's result violates the method postcondition at
that concrete input. It is checked in a file whose ``prove_correct`` block has
been stripped, so no tactic script can mask the verdict. The frozen impl is a
loop-free ``if`` ladder, so every witness ``decide``s: it ELABORATES against the
reshaped/wrong rival (a genuine counterexample) and, because the frozen solution
satisfies the spec at every input, ``decide`` proves ``… = false`` FALSE against
gold — the discrimination half. Each witness passes a concrete ``combine``
lambda so the both-present arm is fully evaluated.

WITNESS PLACEMENT. The five reject witnesses probe FIVE DISTINCT input points,
moving every input binder the precondition permits:
  R-carry-vs-combine   (some[1], none,    false, true)   selfMask present, opMask absent
  R-swap-carry         (none,    some[5], false, true)   selfMask absent,  opMask present
  R-drop-combine       (some[3], some[4], false, true)   both present, combine=λ_ _.[8]
  R-decline            (some[1], some[2], true,  true)    handling declined
  R-both-absent        (none,    none,    false, true)    neither present
``selfMask`` takes some/none, ``operandMask`` takes some/none, ``handleMaskNone``
takes both truth values. ``operandPresent`` is pinned ``true`` by the precondition
(the modelled domain — a real second operand always present), so no witness can
or should vary it; ``combine`` is exercised as a concrete function in the two
arms whose output depends on it (R-drop-combine, R-decline). pts = 5.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the changed
behaviour is modelled deeply, with no unchanged library callee whose contract
the proof assumes). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14995"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors (each unique within _BASE, each strictly inside the impl
# region). The load-bearing whole-body region is asserted present so the
# manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------
_GOLD_BODY = (
    "    let out : Option (List Int) :=\n"
    "      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then\n"
    "        none\n"
    "      else\n"
    "        if selfMask = none then\n"
    "          operandMask\n"
    "        else\n"
    "          if operandMask = none then\n"
    "            selfMask\n"
    "          else\n"
    "            some (combine (selfMask.getD []) (operandMask.getD []))\n"
    "    return out")
assert _GOLD_BODY in _BASE, "gold impl body drifted from Solution.lean"

# clause-4 arm (first present / second absent -> combiner), and its combiner leg
_C4_ARM = (
    "          if operandMask = none then\n"
    "            selfMask\n"
    "          else\n"
    "            some (combine (selfMask.getD []) (operandMask.getD []))")

# clause-3 arm (second present / first absent -> carry second over)
_C3_ARM = (
    "        if selfMask = none then\n"
    "          operandMask\n"
    "        else")

# the outer decline/both-absent guard and its `none` result
_OUTER_GUARD = (
    "      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then")
_OUTER_GUARD_RESULT = (
    "      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then\n"
    "        none\n"
    "      else")

# the two single-mask branches, for the reorder positive control
_SINGLE_MASK_LADDER = (
    "        if selfMask = none then\n"
    "          operandMask\n"
    "        else\n"
    "          if operandMask = none then\n"
    "            selfMask\n"
    "          else\n"
    "            some (combine (selfMask.getD []) (operandMask.getD []))")

# start of the impl body, for the admissibility in-region assert
_IMPL_HEAD = (
    "    -- impl-start\n"
    "    let out : Option (List Int) :=")


# ---- witness preamble: reach the method contract through Velvet's tester. ----
def _tester():
    m = "resolveMask"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


def _witness(args):
    return _tester() + (
        f"example : resolveMaskTester {args} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation
    # (`prove_correct resolveMask by loom_solve`) and reshapes only the
    # executable case split; the contract is point-wise, so the frozen tactic
    # closes for each.
    # =====================================================================
    {
        "id": "pos-flatten-decline-first",
        "kind": "soundness",
        "expect": "verify",
        # Split the fused outer disjunction into two nested guards: handling
        # declined -> none FIRST, then neither-present -> none, then the two
        # single-mask carry-overs, then the combiner. Same value in every case;
        # a distinct control shape from the frozen fused guard.
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    let out : Option (List Int) :=\n"
            "      if handleMaskNone = true then\n"
            "        none\n"
            "      else\n"
            "        if selfMask = none ∧ operandMask = none then\n"
            "          none\n"
            "        else\n"
            "          if selfMask = none then\n"
            "            operandMask\n"
            "          else\n"
            "            if operandMask = none then\n"
            "              selfMask\n"
            "            else\n"
            "              some (combine (selfMask.getD []) (operandMask.getD []))\n"
            "    return out"),
        "rationale": "REPRODUCES the gold value in every one of the five cases "
                     "via a different control shape (the fused decline/both-"
                     "absent guard is split into two nested guards, decline "
                     "tested first). Each ensures clause is an independent point "
                     "claim, so all five discharge and the frozen `loom_solve` "
                     "closes; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-reorder-single-mask",
        "kind": "soundness",
        "expect": "verify",
        # Swap the order of the two single-mask tests: check operand-absent
        # before self-absent. Inside the else both cannot be none (outer guard),
        # so the result is identical on every input; the branch order differs.
        "module": _swap(
            _BASE, _SINGLE_MASK_LADDER,
            "        if operandMask = none then\n"
            "          selfMask\n"
            "        else\n"
            "          if selfMask = none then\n"
            "            operandMask\n"
            "          else\n"
            "            some (combine (selfMask.getD []) (operandMask.getD []))"),
        "rationale": "REORDERS the two single-mask carry-over branches (test "
                     "second-mask-absent before first-mask-absent). Under the "
                     "outer guard the two masks are never both absent, so each "
                     "input lands on the same result as gold; the two carry-over "
                     "clauses and the combiner clause all discharge and the "
                     "frozen proof closes. Must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition is `operandPresent = true`, which any
    # F2P-shaped input trivially meets, so the usual "a normal input satisfies
    # the precondition" probe is near-vacuous. RE-AIMED at the residual risk:
    # that the post-image collapses the present-vs-absent distinction the whole
    # fix turns on. The case discharges a live in-region assert that a carried-
    # over present mask (an F2P-shaped bitmask) is observably DISTINCT from the
    # no-mask `none` result; the impl is kept verbatim so all five ensures
    # clauses still discharge for the frozen body.
    # =====================================================================
    {
        "id": "admiss-present-distinct-from-absent",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_HEAD,
            "    -- impl-start\n"
            "    assert (with_name_prefix `assert\n"
            "      ((some [0, 1, 64] : Option (List Int)) ≠ none))\n"
            "    let out : Option (List Int) :="),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: a present carried-over mask "
                     "(some [0,1,64]) is observably distinct from the no-mask "
                     "`none` result, so the spec does not collapse the present-"
                     "vs-absent distinction the case split turns on. The "
                     "in-region assert discharges (else PRECOND/POST-degenerate); "
                     "the impl is kept verbatim so the five ensures clauses "
                     "discharge as well.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "rival-carry-vs-combine",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FIX, inverted. When the first operand carries a mask and the
        # second does not, route to the combiner (applied against an absent
        # second mask) instead of carrying the first mask over. Attacks clause 4.
        "module": _swap(
            _BASE, _C4_ARM,
            "          some (combine (selfMask.getD []) (operandMask.getD []))"),
        "refinement": "the faithful counterpart hands a present first mask and an "
                      "absent second mask to the elementwise combiner. In the "
                      "real code the absent side is not an empty array but a "
                      "missing value, so the combiner cannot operate on it — the "
                      "very failure the scenario reports; and where the second "
                      "mask happens to be all-zero the combiner still fails to "
                      "carry the first mask through unchanged. The failing test "
                      "pins the result to the first operand's mask, so the "
                      "counterpart still fails. It would NOT resolve.",
        "rationale": "REJECT from clause 4 (selfMask ≠ none ∧ operandMask = none "
                     "⇒ out = selfMask): the rival yields the combiner applied to "
                     "(selfMask, []) instead of selfMask. Refuted at "
                     "(some[1], none, false, true) — a present first mask with an "
                     "absent second mask, the load-bearing sub-domain no other "
                     "rival probes.",
        "witness": _witness("(some [1]) none false true (fun _ _ => [7])"),
    },
    {
        "id": "rival-swap-carry",
        "kind": "uniqueness",
        "expect": "reject",
        # Second present / first absent: carry the (absent) FIRST mask over
        # instead of the present second mask. Attacks clause 3.
        "module": _swap(
            _BASE, _C3_ARM,
            "        if selfMask = none then\n"
            "          selfMask\n"
            "        else"),
        "refinement": "the faithful counterpart returns the absent first mask "
                      "when only the second operand carries one, dropping the "
                      "present mask entirely. The failing test's commutative "
                      "companion (mask-less operand combined with a masked one) "
                      "pins the result to the present mask, so a dropped mask "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from clause 3 (selfMask = none ∧ operandMask ≠ none "
                     "⇒ out = operandMask): the rival yields selfMask (= none) "
                     "where the present operandMask is required. Refuted at "
                     "(none, some[5], false, true) — an absent first mask with a "
                     "present second mask.",
        "witness": _witness("none (some [5]) false true (fun _ _ => [9])"),
    },
    {
        "id": "rival-drop-combine",
        "kind": "uniqueness",
        "expect": "reject",
        # Both present: carry the second operand's mask over instead of applying
        # the combiner. Attacks clause 5, the combiner arm.
        "module": _swap(
            _BASE, _C4_ARM,
            "          if operandMask = none then\n"
            "            selfMask\n"
            "          else\n"
            "            operandMask"),
        "refinement": "the faithful counterpart returns the second operand's mask "
                      "unchanged when both operands carry masks, never invoking "
                      "the combiner. The failing test's both-masked scenario pins "
                      "the result to the combiner applied to the two masks (e.g. "
                      "the bitwise merge), so returning one operand's mask "
                      "verbatim still fails. It would NOT resolve.",
        "rationale": "REJECT from clause 5 (selfMask ≠ none ∧ operandMask ≠ none "
                     "⇒ out = some (combine …)): the rival yields operandMask "
                     "where the combiner output is required. Refuted at "
                     "(some[3], some[4], false, true) with combine = λ_ _.[8] — "
                     "gold yields some[8], the rival some[4]; the concrete "
                     "combiner makes the divergence decidable and separates this "
                     "near-miss from the carry-over rivals.",
        "witness": _witness("(some [3]) (some [4]) false true (fun _ _ => [8])"),
    },
    {
        "id": "rival-ignore-decline",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the decline disjunct from the outer guard: when handling is
        # declined but both masks are present, fall through to the combiner
        # instead of returning none. Attacks clause 1.
        "module": _swap(
            _BASE, _OUTER_GUARD,
            "      if (selfMask = none ∧ operandMask = none) then"),
        "refinement": "the faithful counterpart ignores the caller's decision to "
                      "decline mask handling and still merges the masks. The "
                      "failing test expects no resulting mask when handling is "
                      "declined, so producing one still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause 1 (handleMaskNone = true ⇒ out = none): "
                     "with the decline disjunct dropped, a declined call with "
                     "both masks present falls through to the combiner. Refuted "
                     "at (some[1], some[2], true, true) with combine = λ_ _.[0] — "
                     "gold yields none, the rival some[0]. This is the only rival "
                     "that varies handleMaskNone to true.",
        "witness": _witness("(some [1]) (some [2]) true true (fun _ _ => [0])"),
    },
    {
        "id": "rival-empty-not-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Neither present / declined: return an empty present mask (some []) in
        # place of no mask (none). Attacks clause 2 (the both-absent leg), the
        # present-vs-absent (`none`) abstraction.
        "module": _swap(
            _BASE, _OUTER_GUARD_RESULT,
            "      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then\n"
            "        some []\n"
            "      else"),
        "refinement": "the faithful counterpart returns an empty mask array where "
                      "there should be no mask at all. The failing test asserts "
                      "the result carries NO mask (a `None` result) when neither "
                      "operand has one, and an empty array is not the same object "
                      "as absence, so the assertion still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause 2 (selfMask = none ∧ operandMask = none "
                     "⇒ out = none): the rival yields some [] where none is "
                     "required — flipping the present/absent abstraction. Refuted "
                     "at (none, none, false, true).",
        "witness": _witness("none none false true (fun _ _ => [0])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1
# soundness positive, 1 admissibility, 2 frame-mutation rivals, 3 partial-
# domain/value rivals). The sibling contracts `result_mask(...) -> MaskResult`
# over a `List[int]` carrier under fractional-permission framing; this bundle
# contracts the SAME behaviour as `resolveMask(...) -> Option (List Int)`, with
# no heap, no `mut`, and the postcondition unfolded into FIVE independent
# clauses. The per-clause discrimination argument is preserved in every ported
# case; only the carrier and the permission machinery change.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder              -> pos-flatten-decline-first
#                                       + pos-reorder-single-mask        PORTED
#   admiss-precond-consistent        -> admiss-present-distinct-from-absent  RE-AIMED
#   frame-mutate-self-mask           -> (none)                           VACUOUS
#   frame-rebind-operand-mask        -> (none)                           VACUOUS
#   prepatch-case3-combine           -> rival-carry-vs-combine           PORTED (THE FIX)
#   swap-case2-wrong-array           -> rival-swap-carry                 PORTED
#   present-flag-flip-case1          -> rival-empty-not-absent
#                                       + rival-ignore-decline           PORTED (split)
#
# 5 ported (one positive split into two reshapes; the present-flag rival split
# into its two velvet clauses), 1 re-aimed, 2 vacuous.
#
# PORTED (positives): the sibling ships ONE structurally-different correct impl
#   (branch order reshaped, present-cases via reshaped locals). Carried by TWO
#   honest cheapest-reshape positives: pos-flatten-decline-first (split the
#   fused outer guard, decline first) and pos-reorder-single-mask (swap the two
#   single-mask carry-over branches). Both are correct on every input and both
#   verify with the frozen `loom_solve`; the structural-difference intent is
#   preserved.
# PORTED (rivals): prepatch-case3-combine IS the differential the issue reports
#   (a present first mask combined against an absent second mask) -> rival-
#   carry-vs-combine, attacking clause 4 (the fix). swap-case2-wrong-array ->
#   rival-swap-carry, attacking clause 3. present-flag-flip-case1 fused two
#   velvet clauses (handling declined AND both-absent) under one nagini
#   "present flag"; here they are DISTINCT ensures clauses, so it is split:
#   rival-empty-not-absent attacks clause 2 (both-absent -> none) and rival-
#   ignore-decline attacks clause 1 (handling declined -> none).
# ADDED (1, no direct sibling counterpart): rival-drop-combine. The velvet
#   postcondition pins the both-present arm to the combiner output as an
#   independent clause 5; the sibling grounded case 4 in an opaque
#   combine_masks/apply_combiner axiom, so it had no value-level rival for that
#   arm. Here `combine` is a concrete function parameter, so a rival that
#   returns one operand's mask instead of the combiner output is refutable at a
#   concrete point (combine = λ_ _.[8]). Every one of the five clauses is thus
#   attacked by some rival.
# RE-AIMED (admissibility): the sibling re-derives the precondition's length-
#   equality inside the body. The velvet spec has NO length precondition (the
#   carrier is `Option (List Int)`, presence-only), and its only require is
#   `operandPresent = true`, which any F2P input trivially meets. The probe is
#   re-aimed at the residual risk: that the post-image collapses the present-vs-
#   absent distinction. The case discharges a live in-region assert that a
#   present carried mask is observably distinct from the no-mask `none`.
# VACUOUS (frame-mutation, x2): the sibling's two frame rivals overwrite the
#   half-permission `self_mask` (append) and rebind the `operand.mask` field to
#   prove the read-only frame holds. This backend is referentially transparent
#   and the method declares NO `mut` binder, so there is no read-only input to
#   overwrite and no substitute probe to build. Not fabricated.
#
# WITNESS DISTINCTNESS. The reject witnesses probe FIVE distinct input points:
#   (some[1], none, F, T) / (none, some[5], F, T) / (some[3], some[4], F, T) /
#   (some[1], some[2], T, T) / (none, none, F, T). selfMask and operandMask each
#   take some AND none; handleMaskNone takes T (rival-ignore-decline) AND F.
#   operandPresent is pinned true by the precondition (the modelled domain), so
#   no witness varies it — stated here, not left unexplained. `combine` is a
#   function binder exercised concretely in the two arms whose output depends on
#   it (rival-drop-combine, rival-ignore-decline). pts = 5.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle has no `axiom`
# (the changed behaviour is modelled deeply and the one callable it delegates to
# is a function parameter, not an axiomatized library callee).
AXIOM_TESTS = []
