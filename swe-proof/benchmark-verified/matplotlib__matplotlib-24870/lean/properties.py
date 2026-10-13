"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24870 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a COMPLETE
``Solution.lean`` variant built by region surgery (``_swap``) that edits only text
inside ``-- impl-start``/``-- impl-end`` — or, for the admissibility case, inside
``-- proof-start``/``-- proof-end`` — so ``markers.same_spec`` holds by
construction and the single ``theorem correct_chooseLevels`` STATEMENT stays
byte-identical. ``expect:"verify"`` passes iff the variant elaborates with that
obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff it does NOT verify AND the
case's ``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``); that manifest is the design document and its
per-case reasoning is what carries over. The two bundles model the same decision
at DIFFERENT depths, and that difference — not any judgement about case count —
is what shapes this battery:

  * The nagini sibling models the decision's DOWNSTREAM CONSEQUENCE over a
    ``List[float]`` carrier: it contracts a function returning the concrete level
    VALUES, with the data extents ``zmin``/``zmax`` and a linearly-pinned midpoint
    ``mid`` as inputs, and pins the two-valued facets element-by-element
    (``len==1``/``len==3``, ``[0]==zmin``, ``[1]==mid``, ``[2]==zmax``, strict
    ordering, interiority ``zmin<[0]<zmax``). Its continuous-field arm is pinned
    to an axiomatized delegate for the automatic multi-level selection.
  * This bundle models the DECISION ITSELF, value-exactly: ``LevelsArg`` is either
    a ``count n`` to be expanded downstream or an ``explicit`` list of exact
    ``Rat`` values, and the routine that expands a count into concrete levels sits
    OUTSIDE the modeled function (no axiom, nothing to echo).

So the nagini element-pin rivals re-express as rivals on the explicit VALUE LIST
this carrier returns directly, and the nagini extent/midpoint inputs
(``zmin``/``zmax``/``mid``) have no counterpart here at all — the midpoint is the
exact rational ``1/2`` rather than a value derived from data extents, so nagini's
interiority and linear-pin machinery collapses. In exchange this carrier exposes
something nagini's does not model: the PRIORITY ORDER by which a caller-supplied
specification and a positional level argument override the data-dependent
default. Three rivals attack that order; it is part of the surface this bundle
DOES model, so leaving it unattacked would be the real gap.

DEFENDED SURFACE (one obligation, ``correct_chooseLevels``; four input binders).
``problem_spec_chooseLevels userLevels args zIsBool filled result`` resolves the
result in strict priority order:

  * (C0 caller override) ``userLevels = some lv`` ⟹ ``result = lv``, whatever
    ``args``/``zIsBool``/``filled`` say;
  * (C1 positional) ``userLevels = none``, ``args = a :: _`` ⟹ ``result = a``;
  * (C2 data-dependent, ``userLevels = none`` and ``args = []``) — for
    boolean-valued data, ``filled = true → result = explicit [0, 1/2, 1]`` and
    ``filled = false → result = explicit [1/2]`` (two INDEPENDENT implication
    arms, each attacked separately below); for other data,
    ``result = count 7``.

The DISCRIMINATING content is the C2 boolean arm: an unfilled plot takes the
single mid-value and a filled plot the three bracketing values, where previously
both took the preset count. Both arms are pinned to exact rational literals, so
there is no opaque answer key and no ungrounded oracle — every rival must be
refuted on the VALUE it returns, which this carrier computes.

BINDER STRUCTURE. All four input binders are load-bearing and all four are varied
by the reject witnesses: ``userLevels ∈ {none, some (count 3)}``,
``args ∈ {[], [count 5]}``, ``zIsBool ∈ {true, false}``,
``filled ∈ {true, false}``. The eight reject witnesses probe FIVE distinct input
points (see the point-spread block at the bottom); a binder held at one value
across every witness would be a binder no rival was built to abuse, and none is.

CASE CLASSES on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling records this class
    as already N/A there (every parameter is a by-value scalar; the only
    permission is on the freshly built result the implementation owns outright).
    On this referentially transparent carrier it is doubly vacuous: the inputs are
    immutable values, there is no mutable binder, no aliasing, and no read-only
    cell an implementation could overwrite to satisfy the postcondition
    vacuously. No substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS HERE, and for the carrier's own
    reason rather than by analogy: ``implementation_chooseLevels`` is a total Lean
    ``def``, so a diverging implementation cannot be written at all and there is
    no rival to ship. (This is the lean disposition. On velvet under
    ``set_option loom.semantics.termination "partial"`` the same class is instead
    a KNOWN SPEC HOLE — a non-terminating implementation satisfies every clause
    vacuously — see ``the corpus-wide termination-semantics finding``. The nagini sibling carries no
    such case, so nothing is dropped on that account either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini sibling needs an
    ``echo-honest`` positive because its continuous-field arm is pinned to an
    axiomatized delegate, and it argues there is no WRONG echo of that delegate.
    Here the corresponding arm is pinned to the exact literal ``count 7`` and the
    bundle declares no axiom and no opaque callee at all, so there is nothing to
    echo and the concern does not arise. The nagini positive is re-expressed as a
    structural positive instead (see the accounting block).

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where every rival lives.

POSITIVES MUST NOT BE DEFEQ TO THE FROZEN IMPL. A positive control earns its
outcome only if its implementation is a genuinely different TERM, not a
re-spelling that reduces back to the frozen one: a defeq reshape verifies for
free and attests to nothing about the spec's tolerance for a different shape.
All three positives are checked against this by a real build of

    example : impl_alt = implementation_chooseLevels := by rfl

with the reshape renamed alongside the frozen definition. That probe must FAIL.
Measured: it fails for pos-branch-reorder and pos-joint-match, and (after the
audit repair recorded on the case) for pos-local-bounds — whose original
same-literal `let` bindings zeta-reduced away and made the probe SUCCEED.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating ``¬ problem_spec_chooseLevels <inputs>
(implementation_chooseLevels <inputs>)`` at one CONCRETE input, closed by
``unfold`` + ``simp``. Every witness binds NOTHING in its head (all inputs are
ground literals), so there are no hypotheses whose joint satisfiability could be
in question and no ``witness-inconsistent`` risk. Each was checked by two real
``lean_verify.sh`` builds: it HOLDS of its own rival and FAILS on the frozen
solution, so it discriminates rather than asserting a tautology.

REFINEMENT. Each rival's ``refinement`` argues that its faithful real counterpart
would NOT make the official harness report resolved — either because it breaks
the boolean-data assertions the F2P test ``test_bool_autolevel`` adds, or because
it breaks a PASS_TO_PASS assertion about the priority order (a rival that
resolved anyway would be an artifact, not a verify-does-not-imply-resolve break).
Two candidate rivals were DROPPED for failing exactly this test; see the
accounting block.

AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores it; the
nagini sibling's two ``auto_levels`` probes concern a delegate that has no
counterpart here (this bundle declares no axiom and no opaque callee — the
expansion of a count into concrete levels lies outside the modeled function and
is reconciled by the differential conformance check instead).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24870"
BACKEND = "lean"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the file (``_swap`` asserts both at import, so any drift in Solution.lean
# breaks this manifest loudly instead of silently mis-targeting a rival).
# ---------------------------------------------------------------------------

# (impl) the whole data-dependent arm — reached only when the caller supplied no
# specification and there is no positional level argument.
_I_DATA_ARM = """      if zIsBool then
        if filled then
          return LevelsArg.explicit [0, 1/2, 1]
        else
          return LevelsArg.explicit [1/2]
      else
        return LevelsArg.count 7"""

# (impl) the individual result expressions of the two boolean-data arms.
_I_FILLED = "          return LevelsArg.explicit [0, 1/2, 1]"
_I_UNFILLED = "return LevelsArg.explicit [1/2]"

# (impl) the caller-override arm.
_I_OVERRIDE = "| some lv => return lv"

# (impl) the complete dispatch, used where a rival restructures the priority
# order rather than one arm's value.
_I_ALL = """  match userLevels with
  | some lv => return lv
  | none =>
    match args with
    | a :: _ => return a
    | [] =>
      if zIsBool then
        if filled then
          return LevelsArg.explicit [0, 1/2, 1]
        else
          return LevelsArg.explicit [1/2]
      else
        return LevelsArg.count 7"""

# (proof) the frozen intro line — so the admissibility case can prepend ground
# `have`s without touching the theorem STATEMENT or the spec view.
_P_INTRO = "  intro userLevels args zIsBool filled\n"

# (proof) the frozen tactic body's final alternation — the only place a positive
# whose value literals are written in a non-normal form has to widen, since the
# frozen `first | rfl | simp_all` decides the two boolean arms by syntactic
# reduction alone. Replaced (never the STATEMENT, which stays byte-identical) by
# the one positive that needs it; `simp_all <;> norm_num` discharges both the
# `h`-contradiction subgoals and the residual rational-normalization goals.
_P_BOOL_TAIL = """      | true =>
        cases filled <;>
          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
            first | rfl | simp_all"""
_P_BOOL_TAIL_NORM = """      | true =>
        cases filled <;>
          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
            simp_all <;> norm_num"""


def _witness(userLevels, args, zIsBool, filled):
    """`¬ problem_spec_chooseLevels <inputs> (implementation_chooseLevels <inputs>)`.

    Stated at ground literals, so the head binds nothing: the refutation needs no
    hypothesis about the carrier (every value the spec pins is an exact rational
    or a Nat literal, all of which this carrier computes), and there is therefore
    nothing whose consistency could be in question.
    """
    ins = f"{userLevels} {args} {zIsBool} {filled}"
    return (f"example : ¬ problem_spec_chooseLevels {ins}\n"
            f"    (implementation_chooseLevels {ins}) := by\n"
            "  unfold problem_spec_chooseLevels implementation_chooseLevels\n"
            "  simp\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_chooseLevels` statement byte-identical; each was checked
    # with a real build.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Both nested tests are INVERTED: the non-boolean case is decided first,
        # and inside the boolean case the unfilled arm comes first. Same results
        # on every input, different control-flow shape. The frozen tactic body
        # still closes (the case split it performs is on the inputs, not on the
        # implementation's syntactic nesting), so no proof authoring is needed.
        "module": _swap(_BASE, _I_DATA_ARM, """      if zIsBool = false then
        return LevelsArg.count 7
      else
        if filled = false then
          return LevelsArg.explicit [1/2]
        else
          return LevelsArg.explicit [0, 1/2, 1]"""),
        "rationale": "a correct reshape that decides the non-boolean case first "
                     "and, within boolean data, the unfilled arm first — same "
                     "result on every input, inverted control flow. It must "
                     "verify, else the postcondition is over-fit to one branch "
                     "nesting (SPEC-TOO-STRONG). Ports the nagini "
                     "pos-control-reordered positive, whose reshape is the same "
                     "double inversion on its carrier.",
    },
    {
        "id": "pos-local-bounds",
        "kind": "soundness",
        "expect": "verify",
        # The two bracketing values of the filled arm are named by local `let`
        # bindings AND written in a non-normal rational form (0/1, 2/2) — a
        # different code shape AND a different elaborated term for the most
        # heavily pinned arm.
        #
        # AUDIT REPAIR. The earlier version of this case bound the SAME literals
        # (`let lo : Rat := 0` / `let hi : Rat := 1`) and was therefore
        # DEFINITIONALLY the frozen implementation: a `let` whose body is the
        # literal the frozen arm already uses zeta-reduces away, so
        # `example : impl_alt = implementation_chooseLevels := by rfl` CLOSED
        # (measured, exit 0). A positive that is defeq to gold verifies honestly
        # while testing nothing about the spec's tolerance for a different shape,
        # which is exactly the hollow-positive failure mode. Writing the two
        # outer values un-normalized fixes it: `0/1` and `2/2` are NOT
        # definitionally `0` and `1` on this carrier (`by rfl` on
        # `(2:Rat)/2 = 1` FAILS — measured), so the same defeq probe now fails
        # (exit 1) while the case still verifies. That makes this positive test
        # what it claims: the spec accepts a filled arm whose values are built
        # by a different term, not merely re-spelled at the source level.
        "module": _swap(
            _swap(_BASE, _I_FILLED, """          let lo : Rat := 0/1
          let hi : Rat := 2/2
          return LevelsArg.explicit [lo, 1/2, hi]"""),
            _P_BOOL_TAIL, _P_BOOL_TAIL_NORM),
        "rationale": "a correct implementation that builds the filled arm's "
                     "three values through named local bindings whose values are "
                     "written in a non-normal rational form (0/1, 2/2) rather "
                     "than as the inline normalized literals — so it is a "
                     "different code shape AND a genuinely different elaborated "
                     "term, not a re-spelling that reduces back to the frozen "
                     "one. It must verify, else the spec is over-fit to the "
                     "inline normalized literal form (SPEC-TOO-STRONG). The "
                     "frozen tactic body's final alternation is widened to "
                     "`simp_all <;> norm_num` to normalize the rationals; the "
                     "theorem STATEMENT is untouched and no new "
                     "declaration/assumption appears. Ports the nagini "
                     "pos-control-local positive.",
    },
    {
        "id": "pos-joint-match",
        "kind": "soundness",
        "expect": "verify",
        # The two independent booleans are decided by ONE match on the pair
        # rather than by nested ifs: three arms, no nesting at all. This is the
        # re-expression of the nagini echo-honest positive (see the accounting
        # block: there is no oracle to echo on this carrier, so the honest
        # cheapest-implementation control becomes a structural one).
        "module": _swap(_BASE, _I_DATA_ARM, """      match zIsBool, filled with
      | false, _     => return LevelsArg.count 7
      | true,  false => return LevelsArg.explicit [1/2]
      | true,  true  => return LevelsArg.explicit [0, 1/2, 1]"""),
        "rationale": "a correct implementation that decides the two independent "
                     "characteristics with a single match on the pair instead of "
                     "nested conditionals — three flat arms, identical results. "
                     "It must verify, else the spec is over-fit to a nested-if "
                     "shape (SPEC-TOO-STRONG). Re-expresses the nagini "
                     "echo-honest control, which on that carrier demonstrates "
                     "the axiomatized delegate is not echo-vulnerable; this "
                     "carrier has no delegate and no axiom, so the honest "
                     "counterpart is this structural positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE, non-vacuously, at
    # ordinary inputs covering all four arms. The frozen theorem carries no
    # precondition hypothesis (the relation is total), so the nagini
    # precondition-admission self-call re-expresses as: discharge the spec
    # predicate by evaluation at four concrete inputs as `have`s, then close the
    # frozen obligation verbatim. Nothing is assumed — no new declaration, no
    # assumption token, statement byte-identical.
    # =====================================================================
    {
        "id": "admiss-ground-arms",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _line : problem_spec_chooseLevels none [] true false\n"
            "      (implementation_chooseLevels none [] true false) := by\n"
            "    unfold problem_spec_chooseLevels implementation_chooseLevels\n"
            "    refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all\n"
            "  have _fill : problem_spec_chooseLevels none [] true true\n"
            "      (implementation_chooseLevels none [] true true) := by\n"
            "    unfold problem_spec_chooseLevels implementation_chooseLevels\n"
            "    refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all\n"
            "  have _cnt : problem_spec_chooseLevels none [] false false\n"
            "      (implementation_chooseLevels none [] false false) := by\n"
            "    unfold problem_spec_chooseLevels implementation_chooseLevels\n"
            "    rfl\n"
            "  have _usr : problem_spec_chooseLevels (some (LevelsArg.count 3))\n"
            "      [LevelsArg.count 5] false true\n"
            "      (implementation_chooseLevels (some (LevelsArg.count 3))\n"
            "        [LevelsArg.count 5] false true) := by\n"
            "    unfold problem_spec_chooseLevels implementation_chooseLevels\n"
            "    rfl\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged by evaluation at four ordinary "
                     "inputs — one per arm: boolean/unfilled and boolean/filled "
                     "(the two inputs the F2P assertions exercise), non-boolean "
                     "data, and a caller override presented alongside a "
                     "positional argument — then the frozen obligation is closed "
                     "verbatim. If any `have` failed, the modeled relation would "
                     "be unsatisfiable at exactly a normal input, the analogue of "
                     "PRECOND-TOO-STRONG. Nothing is assumed: no new "
                     "declaration, statement byte-identical, the ground "
                     "instances are `have`s inside the existing tactic body. "
                     "Ports the nagini admiss-f2p-bool-line self-call, widened "
                     "from one input to one per arm because this carrier's "
                     "relation is total (there is no precondition to admit).",
    },

    # =====================================================================
    # UNIQUENESS rivals (SPEC-TOO-WEAK probes) — wrong implementations sharing
    # the frozen spec, which MUST be rejected. Each carries the argument that
    # its faithful real counterpart would NOT resolve, plus a witness pinning
    # the violation at one concrete input (checked to hold of the rival and to
    # fail on the frozen solution).
    # =====================================================================
    {
        "id": "rival-filled-unfilled-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        # The filled/unfilled test is read inverted: an unfilled plot gets the
        # three bracketing values and a filled plot the single mid-value.
        "module": _swap(_BASE, _I_DATA_ARM, """      if zIsBool then
        if filled then
          return LevelsArg.explicit [1/2]
        else
          return LevelsArg.explicit [0, 1/2, 1]
      else
        return LevelsArg.count 7"""),
        "refinement": "a faithful counterpart reads the filled/unfilled "
                      "characteristic the wrong way round for boolean data: an "
                      "unfilled plot receives the three bracketing values and a "
                      "filled plot the single mid-value. F2P test_bool_autolevel "
                      "asserts the OPPOSITE for both (an unfilled plot's levels "
                      "are exactly [.5]; a filled plot's are [0, .5, 1]), and a "
                      "filled plot handed one level additionally trips the "
                      "downstream 'at least 2 levels' check, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from BOTH C2 boolean arms at once: the "
                     "filled = false arm requires result = LevelsArg.explicit "
                     "[1/2] but the rival returns explicit [0, 1/2, 1], and the "
                     "filled = true arm requires explicit [0, 1/2, 1] but the "
                     "rival returns explicit [1/2]. Refuted at the unfilled "
                     "boolean input (zIsBool = true, filled = false), where the "
                     "rival returns three values where one is pinned. Ports the "
                     "nagini rival-filled-line-confusion, whose refutation there "
                     "is the pair of length pins (1 vs 3) the value lists here "
                     "make directly.",
        "witness": _witness("none", "[]", "true", "false"),
    },
    {
        "id": "rival-filled-drops-midvalue",
        "kind": "uniqueness",
        "expect": "reject",
        # The subtlest value rival: a filled plot gets only the two OUTER
        # bracketing values, omitting the separating mid-value.
        "module": _swap(_BASE, _I_FILLED,
                        "          return LevelsArg.explicit [0, 1]"),
        "refinement": "a faithful counterpart emits only the two outer values "
                      "for a filled boolean plot — the reading that a filled "
                      "plot merely needs two levels, so the extremes suffice. "
                      "The resulting levels would be [0., 1.] with no boundary "
                      "between the two regions, while F2P test_bool_autolevel "
                      "asserts [0, .5, 1] for every filled boolean case it "
                      "covers, so it would NOT resolve. Note it satisfies the "
                      "downstream 'at least 2 levels' requirement and is "
                      "increasing, so nothing else rejects it — only the spec's "
                      "exact value list does.",
        "rationale": "REJECT from the C2 filled arm: it requires "
                     "result = LevelsArg.explicit [0, 1/2, 1] and the rival "
                     "returns explicit [0, 1], which is a strictly weaker "
                     "commitment (two levels, increasing) that a length-only or "
                     "'at least two levels' pin would admit. Refuted at the "
                     "filled boolean input (zIsBool = true, filled = true). "
                     "Ports the nagini rival-filled-drop-midpoint, whose "
                     "refutation there is len==3 plus the midpoint element pin.",
        "witness": _witness("none", "[]", "true", "true"),
    },
    {
        "id": "rival-unfilled-boundary-value",
        "kind": "uniqueness",
        "expect": "reject",
        # An unfilled boolean plot gets one of the two data values instead of the
        # value midway between them.
        "module": _swap(_BASE, _I_UNFILLED, "return LevelsArg.explicit [0]"),
        "refinement": "a faithful counterpart emits a single level sitting ON one "
                      "of the two data values rather than midway between them. "
                      "The downstream interior filter keeps only levels strictly "
                      "inside the data range, so that level is discarded and the "
                      "reported levels collapse to the range's lower end with a "
                      "warning; either way they are not [.5], which F2P "
                      "test_bool_autolevel asserts for every unfilled boolean "
                      "case, so it would NOT resolve.",
        "rationale": "REJECT from the C2 unfilled arm: it requires "
                     "result = LevelsArg.explicit [1/2] and the rival returns "
                     "explicit [0]. This is the VALUE pin as opposed to a "
                     "length pin — the rival's list has the right length, so "
                     "only the exact rational 1/2 refutes it. Refuted at the "
                     "unfilled boolean input (zIsBool = true, filled = false). "
                     "Ports the nagini rival-line-boundary-value, whose "
                     "refutation there is Result()[0]==mid plus strict "
                     "interiority; interiority has no counterpart on this "
                     "carrier (the mid-value is the exact literal 1/2, not a "
                     "quantity derived from data extents), so the exact-value "
                     "pin carries the whole refutation.",
        "witness": _witness("none", "[]", "true", "false"),
    },
    {
        "id": "rival-filled-decreasing-order",
        "kind": "uniqueness",
        "expect": "reject",
        # A filled boolean plot gets the three correct values in DECREASING
        # order.
        "module": _swap(_BASE, _I_FILLED,
                        "          return LevelsArg.explicit [1, 1/2, 0]"),
        "refinement": "a faithful counterpart emits the three correct values in "
                      "decreasing order for a filled boolean plot. The "
                      "downstream check requires levels to be increasing and "
                      "raises on a decreasing sequence, so the call fails "
                      "outright rather than producing [0, .5, 1]; F2P "
                      "test_bool_autolevel would NOT resolve. (A P2P case pins "
                      "that same increasing-order requirement independently.)",
        "rationale": "REJECT from the C2 filled arm: it requires "
                     "result = LevelsArg.explicit [0, 1/2, 1] and the rival "
                     "returns explicit [1, 1/2, 0] — the right length, the right "
                     "multiset of values, the right middle element, but the "
                     "wrong sequence. Only an ORDER-sensitive pin refutes it, "
                     "which the exact list equality supplies. Refuted at the "
                     "filled boolean input (zIsBool = true, filled = true). "
                     "Ports the nagini rival-filled-wrong-order, whose "
                     "refutation there is the [0]==zmin / [2]==zmax element pins "
                     "plus strict ordering.",
        "witness": _witness("none", "[]", "true", "true"),
    },
    {
        "id": "rival-data-characteristic-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # The data characteristic is never consulted: with no caller
        # specification and no positional argument the preset count is always
        # used. This is the pre-existing behavior (byte-for-byte the
        # Solution_prepatch.lean skeleton) and hence the G-DIFF witness.
        "module": _swap(_BASE, _I_DATA_ARM, "      return LevelsArg.count 7"),
        "refinement": "this is the behavior that predates the change: with no "
                      "caller specification and no positional argument the "
                      "preset count is used whatever the data is, so a boolean "
                      "plot's levels are the several piled-up automatic levels "
                      "the issue reports rather than [.5] (unfilled) or "
                      "[0, .5, 1] (filled). F2P test_bool_autolevel fails on "
                      "every one of its assertions, so this counterpart — the "
                      "unmodified routine — does NOT resolve; it is the same "
                      "witness G-DIFF uses.",
        "rationale": "REJECT from BOTH C2 boolean arms: each requires an "
                     "explicit value list and the rival returns "
                     "LevelsArg.count 7 in both. This is the supporting "
                     "pre-existing-behavior rival; if it verified the spec would "
                     "admit the very behavior the change replaces "
                     "(SPEC-TOO-WEAK). Refuted at the unfilled boolean input "
                     "(zIsBool = true, filled = false), the facet the issue "
                     "itself reports. Ports the nagini "
                     "rival-prepatch-multilevel.",
        "witness": _witness("none", "[]", "true", "false"),
    },
    {
        "id": "rival-data-characteristic-unguarded",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no nagini counterpart — see the accounting block): the boolean
        # test is dropped, so NON-boolean data also receives the explicit
        # two-valued defaults instead of the preset count. The dual of
        # rival-data-characteristic-ignored, and the only rival attacking the
        # non-boolean arm of C2.
        "module": _swap(_BASE, _I_DATA_ARM, """      if filled then
        return LevelsArg.explicit [0, 1/2, 1]
      else
        return LevelsArg.explicit [1/2]"""),
        "refinement": "a faithful counterpart applies the two-valued defaults "
                      "unconditionally, never testing what the data is. Ordinary "
                      "continuous data drawn with no explicit specification then "
                      "receives one or three fixed levels instead of the preset "
                      "count of automatically chosen ones — so its levels no "
                      "longer track the data range at all. Several PASS_TO_PASS "
                      "cases pin exactly that: one asserts the automatically "
                      "chosen levels equal a specific evenly spaced sequence "
                      "spanning the data, and the image-comparison cases render "
                      "the automatic multi-level default. Those break, so it "
                      "would NOT resolve — and it is a strictly worse trade than "
                      "the behavior it replaces, since it regresses the "
                      "continuous case to fix the boolean one.",
        "rationale": "REJECT from the non-boolean arm of C2: with "
                     "zIsBool = false the spec requires "
                     "result = LevelsArg.count 7, and the rival returns an "
                     "explicit value list. This is the ONLY rival attacking that "
                     "arm — every other boolean-arm rival leaves it correct, so "
                     "without this case a rival that mishandled non-boolean data "
                     "alone would verify. Refuted at a non-boolean filled input "
                     "(zIsBool = false, filled = true), the only witness at that "
                     "point.",
        "witness": _witness("none", "[]", "false", "true"),
    },
    {
        "id": "rival-positional-argument-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # The positional-argument arm is removed entirely: a positional level
        # argument is discarded and the data-dependent default is used instead.
        "module": _swap(_BASE, _I_ALL, """  match userLevels with
  | some lv => return lv
  | none =>
    if zIsBool then
      if filled then
        return LevelsArg.explicit [0, 1/2, 1]
      else
        return LevelsArg.explicit [1/2]
    else
      return LevelsArg.count 7"""),
        "refinement": "a faithful counterpart discards a positional level "
                      "argument and falls through to the data-dependent default. "
                      "PASS_TO_PASS pins this directly: one case passes a level "
                      "count positionally and asserts the result matches the "
                      "same count supplied by keyword, which fails once the "
                      "positional value is replaced by the preset count; another "
                      "renders a plot whose only level is supplied positionally, "
                      "and its image comparison fails when that level is "
                      "discarded. So it would NOT resolve even though the F2P "
                      "assertions, which pass no positional argument, are "
                      "untouched.",
        "rationale": "REJECT from C1: with userLevels = none and args = a :: _ "
                     "the spec requires result = a, and the rival ignores args "
                     "entirely, returning the data-dependent default. Refuted at "
                     "(userLevels = none, args = [LevelsArg.count 5], "
                     "zIsBool = false, filled = false), the only witness with a "
                     "non-empty args — so this is the case that keeps the args "
                     "binder from being pinned across the battery. No nagini "
                     "counterpart: the sibling's carrier does not model the "
                     "priority order (see the accounting block).",
        "witness": _witness("none", "[LevelsArg.count 5]", "false", "false"),
    },
    {
        "id": "rival-caller-override-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # The caller's own specification is accepted as present but its CONTENT
        # is discarded in favour of the preset count.
        "module": _swap(_BASE, _I_OVERRIDE,
                        "| some _ => return LevelsArg.count 7"),
        "refinement": "a faithful counterpart notices that the caller supplied a "
                      "specification but ignores what it says, substituting the "
                      "preset count. Every PASS_TO_PASS case that supplies "
                      "levels by keyword then draws the wrong levels: one "
                      "asserts a keyword count agrees with the same count given "
                      "positionally, several supply explicit level lists and "
                      "compare rendered output, and one expects a warning raised "
                      "only for an empty level list. So it would NOT resolve, "
                      "again while leaving the F2P assertions (which supply no "
                      "specification) untouched.",
        "rationale": "REJECT from C0, the highest-priority clause: "
                     "userLevels = some lv requires result = lv, and the rival "
                     "returns LevelsArg.count 7 regardless of lv. Refuted at "
                     "(userLevels = some (LevelsArg.count 3), args = [], "
                     "zIsBool = false, filled = false) — the only witness with a "
                     "non-none userLevels, so this is the case that keeps the "
                     "userLevels binder from being pinned across the battery. No "
                     "nagini counterpart (the sibling's carrier does not model "
                     "the priority order).",
        "witness": _witness("(some (LevelsArg.count 3))", "[]", "false", "false"),
    },
]

# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 9 SPEC cases (3 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus 2 AXIOM_TESTS. Every one
# is recorded below; nothing was dropped for being hard to prove.
#
#   sibling case                     -> here
#   -----------------------------------------------------------------------
#   pos-control-reordered            -> pos-branch-reorder        PORTED
#   pos-control-local                -> pos-local-bounds          PORTED
#   echo-honest                      -> pos-joint-match           RE-EXPRESSED
#   admiss-f2p-bool-line             -> admiss-ground-arms        RE-EXPRESSED
#   rival-filled-line-confusion      -> rival-filled-unfilled-confusion   PORTED
#   rival-filled-drop-midpoint       -> rival-filled-drops-midvalue       PORTED
#   rival-line-boundary-value        -> rival-unfilled-boundary-value     PORTED
#   rival-filled-wrong-order         -> rival-filled-decreasing-order     PORTED
#   rival-prepatch-multilevel        -> rival-data-characteristic-ignored PORTED
#   (none)                           -> rival-data-characteristic-unguarded ADDED
#   (none)                           -> rival-positional-argument-ignored   ADDED
#   (none)                           -> rival-caller-override-ignored       ADDED
#   AXIOM_TESTS (2, auto_levels)     -> (none)                    DROPPED (G-AX)
#
# RE-EXPRESSED (pos-joint-match, for echo-honest): the sibling's echo control
#   exists because its continuous-field arm is pinned to an axiomatized delegate,
#   and it argues no WRONG echo of that delegate can satisfy the pin. This bundle
#   declares no axiom and no opaque callee — the corresponding arm is pinned to
#   the literal `count 7`, and the routine that expands a count into concrete
#   levels lies outside the modeled function — so there is no oracle to echo and
#   the sibling's concern is vacuous here. Rather than fabricate a substitute, the
#   slot carries the honest cheapest-implementation positive the sibling's case
#   also is: a correct implementation in a third structural shape (one match on
#   both characteristics at once) that must verify.
# RE-EXPRESSED (admiss-ground-arms): the sibling's self-call must establish a
#   real PRECONDITION (well-resolved data extents plus a linearly pinned
#   midpoint). This carrier's relation is TOTAL — the frozen obligation binds no
#   hypothesis at all — so there is no precondition to admit, and the honest
#   analogue is to show the relation is satisfiable non-vacuously at ordinary
#   inputs: it is discharged by evaluation at one input per arm, including both
#   inputs the F2P assertions exercise.
# ADDED (3 rivals). The five sibling rivals all attack the two-valued facets,
#   which is where its carrier's discriminating content lives. This carrier ALSO
#   models the priority order (a caller specification and a positional argument
#   overriding the data-dependent default) and the non-boolean arm, and those are
#   independent top-level clauses of the SAME spec — a rival mishandling one of
#   them would otherwise verify unnoticed, and the two priority binders would be
#   pinned to one value across every witness. So the three additions attack real,
#   load-bearing clauses of the modeled surface; none is fabricated for an
#   unmodeled behavior, and each carries a PASS_TO_PASS-grounded argument that
#   its faithful counterpart would not resolve.
# DROPPED, with reason — two candidate priority-order rivals were built,
#   confirmed to be rejected by the verifier, and confirmed to have witnesses
#   that discriminate, and were then dropped anyway because their REFINEMENT
#   argument does not hold: their faithful counterparts would still resolve, so
#   shipping them would claim a verify-does-not-imply-resolve break that is not
#   there.
#     (a) `args` consulted at its LAST element rather than its first
#         (`(a :: rest).reverse.headD a`). This differs from the frozen behavior
#         only when the positional level list has two or more entries. CORRECTED
#         BY AUDIT: an earlier version of this note claimed such a list cannot
#         reach the decision at all, because every entry point slices the
#         positional arguments down to a single trailing element. That claim is
#         measurably FALSE on one of the two call paths. Instrumenting the real
#         decision point (a spy on the modeled selection recording `len(args)`)
#         shows the rectangular-grid path does cap the list at one — a longer
#         call raises on arity before the decision is reached — but the
#         unstructured-grid path forwards the ENTIRE remaining positional list
#         unsliced, so lists of length 2 and 3 both arrive intact, and the
#         frozen behavior takes the FIRST while the rival takes the last
#         (measured: frozen selects the leading level, the rival the trailing
#         one, on the same call). So the rival IS observably wrong on a
#         REACHABLE input and the `args` binder is genuinely two-sided here;
#         "unreachable" was the wrong reason and is withdrawn.
#         It is STILL not shipped, for reason (b)'s reason instead: no F2P or
#         PASS_TO_PASS case supplies more than one positional level argument, so
#         its faithful counterpart would still resolve and its refinement
#         argument would not hold. Reachable but unprobed by the shipped tests —
#         a residual gap of the same kind as (b), recorded rather than dressed
#         up as a resolve failure.
#     (b) the priority of the caller specification and the positional argument
#         SWAPPED (positional consulted first). This differs from the frozen
#         behavior only when BOTH are present, and no F2P or PASS_TO_PASS case
#         supplies both, so the counterpart would resolve. Recorded as a genuine
#         residual gap: the spec pins a priority the shipped tests never probe,
#         so a rival abusing it cannot be attributed a resolve failure. It is
#         reported here rather than shipped with an argument that does not hold.
#   Both are legitimately omitted, and — after the (a) correction above — both
#   are omitted for the SAME reason: the shipped tests never probe the input
#   where the rival differs, so its refinement claim is unfalsifiable. Neither
#   is omitted because a proof would not close, and neither is omitted for being
#   unreachable. No
#   soundness positive was dropped: all three shapes above, plus the
#   admissibility case, were confirmed to verify with real builds.
# VACUOUS classes (frame/permission mutation; divergence/non-termination) are
#   dispositioned in the module docstring: the first is already N/A in the
#   sibling and doubly so here; the second cannot be expressed at all because the
#   implementation is a total Lean `def`. Neither gets a fabricated substitute.
#
# POINT SPREAD. The eight reject witnesses probe FIVE distinct input points
# (userLevels, args, zIsBool, filled):
#   (none, [], true, false)                    rival-filled-unfilled-confusion
#                                              rival-unfilled-boundary-value
#                                              rival-data-characteristic-ignored
#   (none, [], true, true)                     rival-filled-drops-midvalue
#                                              rival-filled-decreasing-order
#   (none, [], false, true)                    rival-data-characteristic-unguarded
#   (none, [count 5], false, false)            rival-positional-argument-ignored
#   (some (count 3), [], false, false)         rival-caller-override-ignored
# Every input binder MOVES across them: userLevels takes none and some,
# args takes [] and a non-empty list, zIsBool takes true and false, filled takes
# true and false. Rivals sharing a point genuinely fail AT that point and for
# distinct reasons (a wrong length, a wrong value, a wrong order, the wrong arm
# entirely); the two rivals with the narrowest disagreement — the boundary value
# and the decreasing order, each of which agrees with the frozen behavior
# everywhere except one arm — are witnessed at exactly the arm where they differ.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores it. The
# sibling's two probes concern an axiomatized delegate for the automatic
# multi-level selection; this bundle axiomatizes nothing (that expansion is
# outside the modeled function and is reconciled by the differential conformance
# check), so there is no axiom to probe.
AXIOM_TESTS = []
