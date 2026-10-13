"""properties.py — G-PBT falsification battery for sympy__sympy-24661 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct rewriteComparison`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

================================  DEFENDED SURFACE  ==========================

One contracted method rewrites a single comparison expression into its symbolic
form, over four FREE inputs: the operand rewrite ``visit : Node → Node`` (an
unchanged, universally-quantified callee — the spec asserts nothing about it),
the comparison kind ``k : CompareKind``, and the two operands ``l r : Node``.

  rewriteComparison (visit k l r) return (out : Node)
    (P0) ensures out = rewriteCompare visit k l r                    -- master
    (P1) ensures k = .lt → out = .relation .Lt false (visit l) (visit r)
    (P2) ensures k = .le → out = .relation .Le false (visit l) (visit r)
    (P3) ensures k = .gt → out = .relation .Gt false (visit l) (visit r)
    (P4) ensures k = .ge → out = .relation .Ge false (visit l) (visit r)
    (P5) ensures k = .eq → out = .relation .Eq false (visit l) (visit r)
    (P6) ensures k = .ne → out = .relation .Ne false (visit l) (visit r)
    (P7) ensures relOf k = none → out = .comparison k l r
    (P8) ensures ∀ rk b a c, out = .relation rk b a c → b = false

An ordered/equality comparison becomes the MATCHING symbolic relation
constructor applied to the two REWRITTEN operands (in source order l, r), held
UNEVALUATED — the only way the comparison survives as a symbolic relation rather
than collapsing to a truth value; any other comparison kind is preserved exactly.
``rewriteCompare`` / ``relOf`` are total, fully-unfolded ``def``s in the ``pure``
region; the ``axioms`` region declares NOTHING. There is no opaque answer key —
evaluating ``rewriteCompare`` IS the correct answer, and the six per-kind clauses
(P1..P6) plus the operator→constructor bijection are grounded in the method's own
``k`` input.

Load-bearing behaviours the six FAIL_TO_PASS input rows demand (each ordered /
equality comparison must parse to its own unevaluated relation constructor):
  * the operator→constructor BIJECTION (P1..P6): a strict-less comparison becomes
    Lt, less-or-equal becomes Le, greater becomes Gt, …, equal becomes Eq, not-
    equal becomes Ne. A rival that maps every kind to one fixed constructor is
    right on exactly one operator and wrong on the other five.
  * SOURCE ORDER (P0..P6): the constructor is applied to (visit l, visit r) in
    that order; a rival that swaps the operands produces the mirror relation.
  * UNEVALUATED (P8, and the ``false`` flag pinned in P1..P6): the relation is
    held unevaluated so it stays a symbolic relation. A rival that builds it
    EVALUATED reproduces the EXACT reported defect — the relation collapses to a
    concrete truth value.
  * PRESERVATION of unsupported kinds (P7): a comparison the rewrite does not
    support (identity / membership / …) is returned unchanged. A rival that
    converts EVERYTHING wraps those too.
  * SUPPORT of the whole ordered/equality set (P0, P5): dropping one supported
    kind leaves that comparison unconverted, so it collapses to a truth value.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as
    MANDATORY (two cases) because the source AST node's operator / operand tags
    are held at a fractional heap permission (``Acc(node.op,1/2)`` …) an impl can
    illegally WRITE. Lean and Velvet are referentially transparent: ``visit``,
    ``k``, ``l``, ``r`` are immutable values, this bundle declares NO ``mut``
    binder, there is no heap and no aliasing — so there is no read-only input to
    overwrite and no substitute probe to build. Reported vacuous, not fabricated;
    the sibling's read-only obligation is here structurally guaranteed by the
    absence of ``mut``, which the frozen spec already encodes.
  * UNGROUNDED-ORACLE ECHO — N/A. ``rewriteCompare`` / ``relOf`` are concrete,
    fully-unfolded ``def``s of the method's own inputs; the ``axioms`` region
    declares no ``axiom``. There is no opaque answer key to echo, so there is no
    wrong-echo reject to build. Honest cheapest-reshape positive controls stand
    in (a faithful correct impl of a different shape must verify).
  * CONTROL-FLOW-EFFECT — N/A. The rewrite is pure and total; no exception, no
    side effect, no early-return path distinguishable from the returned value —
    every observable of the produced node is in the value abstraction.
  * DIVERGENCE / NON-TERMINATION — BLOCKED BY THE CARRIER'S WITNESS ROUTE, and
    measured. This bundle runs under ``loom.semantics.termination "total"`` (NOT
    "partial"), so a rival whose loop carries no decreasing measure is genuinely
    REJECTED rather than verifying vacuously: an impl that wraps the correct value
    in a ``while`` loop with no ``decreasing`` clause fails with ``error:
    Decreasing annotations are required in total correctness semantics`` (measured,
    exit 1). So the class is NOT vacuous and NOT a spec hole — the spec does
    reject it. What blocks SHIPPING it as a reject case is the witness half: the
    gate requires the witness to ELABORATE against the rival, but stripping the
    ``prove_correct`` block does not remove the loop, and the loop's own
    weakest-precondition generation leaves an unproven goal in the rival's witness
    file (``Failed to prove assertion without names: WPGen (forIn Lean.Loop.mk …
    sorry …)``, plus ``declaration uses 'sorry'`` — measured, rival witness build
    exit 1 where the gate demands exit 0). The refutation is therefore unstateable
    on this carrier for a diverging rival, so the case cannot be landed without a
    witness the gate would reject as unproven. Recorded as a TOOLING BLOCK with the
    measured error text, not as vacuity and not as absence-in-the-design.
  * PARTIAL-DOMAIN / VALUE — the heart of this port. Rivals right on part of the
    input domain but diverging on a sub-domain: a fixed constructor for every
    kind (right on one operator), swapped operands, an evaluated relation, a
    dropped supported kind, and converting an unsupported kind. Each is refuted
    at a concrete input.

WITNESS MECHANICS on this carrier (decisive). ``prove_postcondition_decidable_for``
CANNOT synthesise a ``Decidable`` instance for the ∀-quantified clause P8 (over
the infinite ``Node`` type), so the tester route (``derive_tester_for`` →
``…Tester args = false``) is UNAVAILABLE (measured: it leaves an unsolved
``Decidable (∀ rk b a c, …)`` goal). Each witness instead refutes the method's
Hoare triple DIRECTLY at one concrete input, against the MASTER clause P0
(``out = rewriteCompare visit k l r``):
    ¬ triple True (rewriteComparison visit k l r)
        (fun out => out = rewriteCompare visit k l r)
closed by ``unfold rewriteComparison; simp [triple, pure] <;> decide``. Checked
in a file whose ``prove_correct`` block has been stripped, so no tactic script
can mask the verdict. ``triple`` / ``pure`` come from the frozen ``Velvet.Std``
import. Every witness head binds NOTHING (the refutation is stated at literal /
closed inputs — ``visit`` is instantiated at a concrete decidable lambda), so
there is no consistency obligation to satisfy, and ``decide`` reduces fully. Each
witness was SEEN to discriminate out of band — it ELABORATES against its rival
(exit 0) and FAILS against the frozen solution (exit 1, ``decide proved … is
false``), with two real builds per case.

WITNESS PLACEMENT. The seven reject witnesses sit at seven DISTINCT input points
and between them move all four binders: ``k`` takes ALL SEVEN kinds (le, lt, ge,
eq, other, gt, ne — the last two added by audit, which found P3 and P6 probed
only collaterally), ``visit`` takes two distinct lambdas (the identity and a
constant), ``l`` / ``r`` take distinct operand tags at every point. No binder is
pinned across the rivals. pts = 7.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` and there is no
A-reference deep model in the bundle (the operator→constructor correspondence is
modeled DEEPLY as ``relOf`` / ``rewriteCompare`` in the ``pure`` region). The
nagini file's single A-reference probe is G-AX's job (axiom_check.py), and this
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24661"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct rewriteComparison
# statement byte-identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: dispatch on the comparison kind and
# return either the matching unevaluated relation over the rewritten operands or
# the preserved comparison.
_IMPL = (
    "    let out : Node :=\n"
    "      match relOf k with\n"
    "      | some rk => Node.relation rk false (visit l) (visit r)\n"
    "      | none    => Node.comparison k l r\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the (retuned) proof without disturbing the obligation.
_IMPL_TOP = "    let out : Node :="
assert _BASE.count(_IMPL_TOP) == 1, "impl top-line drifted from expected text"

# The FULL frozen proof body. A case that adds an in-region assert retunes this
# to also close the ground assert goal; the tactic body is elided from the spec
# view, so this is a proof reshape, not a spec change.
_PROOF = (
    "prove_correct rewriteComparison by\n"
    "  loom_solve\n"
    "  all_goals cases k <;> simp_all [rewriteCompare, relOf]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- WITNESSES. The spec carries a ∀-quantified `ensures` clause (P8) over the
# ---- infinite `Node` type, so `prove_postcondition_decidable_for` cannot
# ---- synthesise the tester's Decidable instance and the tester route is
# ---- UNAVAILABLE (measured). Each witness instead refutes the method's Hoare
# ---- triple DIRECTLY, against the master clause P0, at one concrete input,
# ---- checked in a file whose `prove_correct` block has been stripped so no
# ---- tactic script can mask the verdict. The head binds nothing (literal /
# ---- closed inputs), so there is no consistency obligation.
def _witness(visit: str, k: str, l: str, r: str) -> str:
    return (
        f"example : ¬ triple (l := Prop) (True)\n"
        f"    (rewriteComparison ({visit}) ({k}) ({l}) ({r}))\n"
        f"    (fun out => out = rewriteCompare ({visit}) ({k}) ({l}) ({r})) := by\n"
        f"  unfold rewriteComparison\n"
        f"  simp [triple, pure] <;> decide\n"
    )


_ID = "fun x => x"                 # the identity operand rewrite
_CONST = "fun _ => Node.leaf 9"    # a constant operand rewrite (moves `visit`)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the nine `ensures` obligations and
    # only reshapes the executable surface; the frozen `cases k <;> simp_all`
    # proof closes regardless of the executable arm shape.
    # =====================================================================
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: permute the two match arms (the preserved-comparison arm
        # first, the relation arm second). `match` is order-independent on the
        # disjoint `some`/`none` constructors, so the returned value is unchanged
        # on every input.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match relOf k with\n"
            "      | none    => Node.comparison k l r\n"
            "      | some rk => Node.relation rk false (visit l) (visit r)\n"
            "    return out"),
        "rationale": "PASS SOURCE = P0..P8. Permuting the match arms over the "
                     "disjoint some/none constructors leaves `out` identical on "
                     "every kind, so `out = rewriteCompare visit k l r` and all "
                     "per-kind clauses still discharge; a structurally-different "
                     "faithful reshape MUST verify, else the postcondition is "
                     "over-fit to the exact impl FORM => SPEC-TOO-STRONG. Verified "
                     "to build.",
    },
    {
        "id": "pos-dispatch-on-kind",
        "kind": "soundness",
        "expect": "verify",
        # A maximally-different correct shape: dispatch directly on the comparison
        # kind, spelling out each supported arm's own relation constructor,
        # WITHOUT going through the relOf lookup at all. Same value on every kind;
        # confirms the spec is not over-fit to delegating through `relOf`.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match k with\n"
            "      | .lt    => Node.relation .Lt false (visit l) (visit r)\n"
            "      | .le    => Node.relation .Le false (visit l) (visit r)\n"
            "      | .gt    => Node.relation .Gt false (visit l) (visit r)\n"
            "      | .ge    => Node.relation .Ge false (visit l) (visit r)\n"
            "      | .eq    => Node.relation .Eq false (visit l) (visit r)\n"
            "      | .ne    => Node.relation .Ne false (visit l) (visit r)\n"
            "      | .other => Node.comparison k l r\n"
            "    return out"),
        "rationale": "PASS SOURCE = P0..P8. Dispatching directly on the comparison "
                     "kind — naming each supported constructor explicitly and "
                     "preserving the unsupported kind — reproduces `rewriteCompare "
                     "visit k l r` on every kind without calling `relOf`, so all "
                     "nine clauses discharge. Since the operator→constructor "
                     "correspondence is grounded in the input, a faithful "
                     "element-for-element dispatch IS the correct impl; a second "
                     "honest shape verifying confirms the spec is not "
                     "echo-vulnerable and not over-fit to the helper. Else "
                     "SPEC-TOO-STRONG. Verified to build.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The nagini sibling asserts its (fractional-
    # permission) precondition ADMITS a normal F2P-shaped comparison node. This
    # bundle carries NO `require` clause (the rewrite is total), so that
    # precondition-admission probe is degenerate — nothing could exclude an
    # F2P-shaped input. Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is DEGENERATE at the interesting point (that it
    # does not actually demand the matching UNEVALUATED relation on a supported
    # kind and preservation on an unsupported one). An in-region `assert` pins
    # BOTH F2P behaviours at concrete points AND that the produced relation is
    # unevaluated (differs from its evaluated mirror); the impl is kept verbatim
    # so the method's own obligation still discharges; the proof gains a `decide`
    # arm to close the ground assert. The assert is LIVE — a false claim (e.g.
    # strict-less maps to Le) leaves an unsolved `decide` goal (verified out of
    # band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `admiss\n"
                "      (rewriteCompare (fun x => x) CompareKind.lt "
                "(Node.leaf 0) (Node.leaf 1)\n"
                "          = Node.relation RelKind.Lt false "
                "(Node.leaf 0) (Node.leaf 1)\n"
                "        ∧ rewriteCompare (fun x => x) CompareKind.other "
                "(Node.leaf 0) (Node.leaf 1)\n"
                "          = Node.comparison CompareKind.other "
                "(Node.leaf 0) (Node.leaf 1)\n"
                "        ∧ rewriteCompare (fun x => x) CompareKind.lt "
                "(Node.leaf 0) (Node.leaf 1)\n"
                "          ≠ Node.relation RelKind.Lt true "
                "(Node.leaf 0) (Node.leaf 1)))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct rewriteComparison by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (cases k <;> simp_all [rewriteCompare, relOf])"),
        "rationale": "PASS SOURCE = the post-image is non-degenerate at F2P-shaped "
                     "points. The in-region assert pins a strict-less comparison to "
                     "the matching UNEVALUATED Lt relation, an unsupported "
                     "comparison to the preserved comparison, AND the produced "
                     "relation to the UNEVALUATED form (distinct from its evaluated "
                     "mirror) — the two behaviours the failing rows demand. The "
                     "assert must discharge (else the obligation is degenerate / "
                     "unsatisfiable at the interesting point) and the frozen body "
                     "keeps `out = rewriteCompare visit k l r` intact, so the "
                     "module verifies. Since the rewrite is total there is no "
                     "precondition to over-strengthen; this defends against a "
                     "hollow/degenerate post-image instead. Verified to build; the "
                     "assert is live (a false claim leaves an unsolved `decide` "
                     "goal, verified out of band).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each witness refutes the
    # master clause P0 directly (the tester route is unavailable — see header).
    # =====================================================================
    {
        "id": "weak-wrong-constructor",
        "kind": "uniqueness",
        "expect": "reject",
        # Map EVERY supported kind to one fixed constructor (Lt). Correct on
        # strict-less; wrong on the other five ordered/equality operators — the
        # operator→constructor bijection is broken.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match relOf k with\n"
            "      | some _  => Node.relation RelKind.Lt false (visit l) (visit r)\n"
            "      | none    => Node.comparison k l r\n"
            "    return out"),
        "refinement": "hard-coding the strict-less constructor for every supported "
                      "kind is correct only for strict-less. A faithful real patch "
                      "that emitted one fixed relation class for all six operators "
                      "would parse a less-or-equal comparison to a strict-less "
                      "relation (and likewise mis-map greater / greater-or-equal / "
                      "equal / not-equal), so the failing rows for those five "
                      "operators observe the WRONG relation class. It does NOT "
                      "resolve.",
        "rationale": "REJECT from P0 and the per-kind bijection P2..P6: at "
                     "less-or-equal the spec demands the Le relation but this "
                     "yields Lt. Refuted at (visit = identity, k = .le, l = leaf 3, "
                     "r = leaf 4) — the less-or-equal sub-domain, exactly one of "
                     "the five operators this fixed constructor mis-maps. This is "
                     "the only rival that moves `k` to .le and its operands to "
                     "leaf 3 / leaf 4. If it verified => SPEC-TOO-WEAK (the "
                     "operator→constructor bijection would be hollow).",
        "witness": _witness(_ID, "CompareKind.le", "Node.leaf 3", "Node.leaf 4"),
    },
    {
        "id": "weak-operand-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Build the relation with the operands SWAPPED (visit r, visit l).
        # Correct constructor and unevaluated flag, wrong operand order.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match relOf k with\n"
            "      | some rk => Node.relation rk false (visit r) (visit l)\n"
            "      | none    => Node.comparison k l r\n"
            "    return out"),
        "refinement": "applying the relation constructor to the operands in "
                      "REVERSED order yields the mirror relation. A faithful real "
                      "patch that built the call with the comparators swapped would "
                      "parse a strict-less comparison of two distinct operands to "
                      "the reversed relation, so the failing row for that "
                      "comparison observes the operands in the wrong order and does "
                      "NOT resolve (on every asymmetric operand pair).",
        "rationale": "REJECT from P0 and P1: at strict-less the spec demands the Lt "
                     "relation over (visit l, visit r) but this produces it over "
                     "(visit r, visit l). Refuted at (visit = identity, k = .lt, "
                     "l = leaf 0, r = leaf 1) — distinct operands so the swap is "
                     "observable, and the only rival that moves `k` to .lt. If it "
                     "verified => SPEC-TOO-WEAK (source order would be unpinned).",
        "witness": _witness(_ID, "CompareKind.lt", "Node.leaf 0", "Node.leaf 1"),
    },
    {
        "id": "weak-evaluate-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Build the relation EVALUATED (built = true). Correct constructor and
        # order, wrong flag — the EXACT reported defect: the relation collapses to
        # a truth value instead of surviving symbolically.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match relOf k with\n"
            "      | some rk => Node.relation rk true (visit l) (visit r)\n"
            "      | none    => Node.comparison k l r\n"
            "    return out"),
        "refinement": "building the relation EVALUATED reproduces the EXACT "
                      "reported defect: a comparison requested to be held "
                      "unevaluated instead collapses to a concrete truth value. A "
                      "faithful real patch that omitted the unevaluated flag would "
                      "make a strict-less comparison parse to a truth value rather "
                      "than a symbolic relation — precisely what the failing test "
                      "was written to catch — so it does NOT resolve.",
        "rationale": "REJECT from P8 (whenever a relation is produced it is held "
                     "unevaluated) and the `false` flag pinned in P1..P6: this "
                     "produces the relation with built = true. Also refutes P0. "
                     "Refuted at (visit = constant, k = .ge, l = leaf 2, r = leaf "
                     "2) — the only rival that moves `k` to .ge, exercises the "
                     "constant operand rewrite, and holds the operands equal. If it "
                     "verified => SPEC-TOO-WEAK (the unevaluated pin — the whole "
                     "point of the fix — would be hollow).",
        "witness": _witness(_CONST, "CompareKind.ge", "Node.leaf 2", "Node.leaf 2"),
    },
    {
        "id": "weak-drop-eq",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain over the kind: convert five supported operators but treat
        # equality as unsupported (return the comparison unchanged). Correct on
        # lt/le/gt/ge/ne, wrong on eq.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match k with\n"
            "      | .eq => Node.comparison k l r\n"
            "      | _   =>\n"
            "        match relOf k with\n"
            "        | some rk => Node.relation rk false (visit l) (visit r)\n"
            "        | none    => Node.comparison k l r\n"
            "    return out"),
        "refinement": "dropping equality from the supported set is correct on the "
                      "other five operators but leaves an equality comparison "
                      "unconverted. A faithful real patch that omitted equality "
                      "from the supported operators would leave an equality "
                      "comparison a bare comparison that collapses to a truth "
                      "value, so the failing equality row observes a truth value "
                      "instead of the symbolic Eq relation — it does NOT resolve.",
        "rationale": "REJECT from P0 and P5 (equality → Eq relation): at equality "
                     "the spec demands the unevaluated Eq relation but this returns "
                     "the preserved comparison. Refuted at (visit = identity, "
                     "k = .eq, l = leaf 5, r = leaf 6) — the equality sub-domain, "
                     "the only rival that moves `k` to .eq. If it verified => "
                     "SPEC-TOO-WEAK (equality would be an undefended arm).",
        "witness": _witness(_ID, "CompareKind.eq", "Node.leaf 5", "Node.leaf 6"),
    },
    {
        "id": "weak-over-convert",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-convert: build a (bogus) relation even for an UNSUPPORTED kind
        # instead of preserving the comparison. Correct on the six supported
        # operators; wrong on every unsupported (identity / membership / …) kind.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match relOf k with\n"
            "      | some rk => Node.relation rk false (visit l) (visit r)\n"
            "      | none    => Node.relation RelKind.Lt false (visit l) (visit r)\n"
            "    return out"),
        "refinement": "converting an UNSUPPORTED comparison kind into a symbolic "
                      "relation is wrong: an identity / membership comparison must "
                      "be returned unchanged. A faithful real patch that dropped "
                      "the supported-kind guard and wrapped every comparison would "
                      "change the parser's output for identity / membership "
                      "comparisons (which the pre-fix behaviour, and the "
                      "pass-to-pass parser suite, leave as ordinary comparisons), "
                      "so those pass-to-pass tests break and the harness does NOT "
                      "report resolved.",
        "rationale": "REJECT from P7 (an unsupported kind is preserved as a "
                     "comparison): at an unsupported kind the spec demands the "
                     "preserved comparison but this produces a relation. Also "
                     "refutes P0. Refuted at (visit = constant, k = .other, "
                     "l = leaf 7, r = leaf 8) — the only rival that moves `k` to "
                     ".other, the sole unsupported kind, with the constant operand "
                     "rewrite. If it verified => SPEC-TOO-WEAK (preservation of "
                     "unsupported kinds would be unpinned).",
        "witness": _witness(_CONST, "CompareKind.other",
                            "Node.leaf 7", "Node.leaf 8"),
    },
    # --- ADDED BY AUDIT. The five ported rivals leave the GREATER (.gt) and
    # --- NOT-EQUAL (.ne) arms of the bijection unprobed at their own point: no
    # --- witness in the battery instantiates `k` at either kind, so P3 and P6
    # --- were attacked only collaterally, by the fixed-constructor rival refuted
    # --- at .le. A near-miss confined to one of those two arms would therefore
    # --- have been rejected only by tactic breakage. Both rivals below were built
    # --- and both witnesses re-derived (rival exit 0, gold exit 1, plain
    # --- evaluation refutation).
    {
        "id": "weak-gt-to-ge",
        "kind": "uniqueness",
        "expect": "reject",
        # STRICTNESS near-miss confined to the greater arm: map the strict-greater
        # comparison to the non-strict Ge relation, leaving all five other kinds
        # exactly right. Attacks P3 at its own point.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match k with\n"
            "      | .gt    => Node.relation .Ge false (visit l) (visit r)\n"
            "      | _      =>\n"
            "        match relOf k with\n"
            "        | some rk => Node.relation rk false (visit l) (visit r)\n"
            "        | none    => Node.comparison k l r\n"
            "    return out"),
        "refinement": "mapping the strict-greater comparison to the non-strict "
                      "relation class is a STRICTNESS error, wrong on exactly the "
                      "boundary where the two differ. A faithful real patch that "
                      "looked up the non-strict class for the strict-greater "
                      "operator would parse that comparison to a relation that "
                      "holds when the two operands are equal, so the failing row "
                      "for the strict-greater operator observes the wrong relation "
                      "class. It does NOT resolve.",
        "rationale": "REJECT from P0 and P3 (strict-greater → Gt relation): at "
                     "strict-greater the spec demands Gt but this yields Ge. "
                     "Refuted at (visit = identity, k = .gt, l = leaf 10, "
                     "r = leaf 11) — the only rival that moves `k` to .gt, so P3 "
                     "is attacked at its own point rather than collaterally. If it "
                     "verified => SPEC-TOO-WEAK (the strict/non-strict distinction "
                     "on the greater arm would be unpinned).",
        "witness": _witness(_ID, "CompareKind.gt",
                            "Node.leaf 10", "Node.leaf 11"),
    },
    {
        "id": "weak-ne-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # POLARITY inversion confined to the not-equal arm: map the not-equal
        # comparison to the Eq relation — its logical complement — leaving the
        # other five kinds right. Attacks P6 at its own point.
        "module": _with_impl(
            "    let out : Node :=\n"
            "      match k with\n"
            "      | .ne    => Node.relation .Eq false (visit l) (visit r)\n"
            "      | _      =>\n"
            "        match relOf k with\n"
            "        | some rk => Node.relation rk false (visit l) (visit r)\n"
            "        | none    => Node.comparison k l r\n"
            "    return out"),
        "refinement": "mapping the not-equal comparison to the equality relation "
                      "INVERTS its polarity: the produced relation is the logical "
                      "complement of the requested one. A faithful real patch whose "
                      "operator table pointed the not-equal operator at the "
                      "equality class would parse that comparison to a relation "
                      "asserting the opposite of what was written, so the failing "
                      "row for the not-equal operator observes an inverted "
                      "relation. It does NOT resolve.",
        "rationale": "REJECT from P0 and P6 (not-equal → Ne relation): at not-equal "
                     "the spec demands the Ne relation but this produces its "
                     "complement Eq. Refuted at (visit = constant, k = .ne, "
                     "l = leaf 12, r = leaf 13) — the only rival that moves `k` to "
                     ".ne, so P6 is attacked at its own point. If it verified => "
                     "SPEC-TOO-WEAK (the not-equal arm's polarity would be "
                     "undefended).",
        "witness": _witness(_CONST, "CompareKind.ne",
                            "Node.leaf 12", "Node.leaf 13"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (1
# soundness positive, 1 admissibility, 2 MANDATORY frame-mutation rivals, 5
# uniqueness value rivals) plus 1 AXIOM_TESTS entry. The sibling contracts one
# function, `rewrite_comparison(node)`, over a comparison AST node held at
# fractional heap permissions, with the operator→constructor correspondence
# spelled out via @Pure helpers (is_relational / rel_class_of). This bundle
# contracts one method, `rewriteComparison`, over the SAME behaviour re-expressed
# for the Lean-family model: the node's operator becomes the free `k :
# CompareKind`, its operands the free `l r : Node`, the recursive operand rewrite
# the free `visit : Node → Node`, and the correspondence is modeled DEEPLY as
# `relOf` / `rewriteCompare` (no axiom). Every value-surface case carries across;
# the permission surface does not exist here.
#
#   sibling case                    kind          -> here                     disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-branch-reorder      soundness     -> pos-arm-reorder          PORTED
#                                                    + pos-dispatch-on-kind    ADDED
#   admiss-readonly-input           admissibility -> admiss-nondegenerate     RE-AIMED
#   frame-mut-op                    uniqueness    -> (none)                    VACUOUS
#   frame-mut-tag                   uniqueness    -> (none)                    VACUOUS
#   wrong-constructor               uniqueness    -> weak-wrong-constructor    PORTED
#   operand-order-swap              uniqueness    -> weak-operand-swap         PORTED
#   evaluate-true                   uniqueness    -> weak-evaluate-true        PORTED
#   partial-domain-drop-eq          uniqueness    -> weak-drop-eq              PORTED
#   over-convert-nonrelational      uniqueness    -> weak-over-convert         PORTED
#   aref-visit-compare              axiom         -> (none)                    G-AX
#   (no sibling)                    uniqueness    -> weak-gt-to-ge           ADDED/AUDIT
#   (no sibling)                    uniqueness    -> weak-ne-inverted        ADDED/AUDIT
#
# 5 uniqueness ported + 2 added by audit, 1 soundness ported + 1 added,
# 1 admissibility re-aimed, 2 vacuous, 1 axiom dropped = 10 velvet SPEC cases
# (3 verify, 7 reject).
#
# ADDED BY AUDIT (weak-gt-to-ge, weak-ne-inverted): the ported set instantiates `k`
#   at {le, lt, ge, eq, other} and never at .gt or .ne, so the two bijection
#   clauses P3 (greater → Gt) and P6 (not-equal → Ne) were attacked only
#   collaterally by the fixed-constructor rival refuted at .le. A near-miss
#   confined to either arm — strictness on greater, polarity on not-equal — would
#   have been rejected only by tactic breakage, which is exactly what the witness
#   requirement exists to rule out. Both rivals were built (module exit 1) and both
#   witnesses re-derived out of band (rival exit 0, gold exit 1, `decide proved …
#   is false` over a fully-evaluated match — a plain evaluation refutation).
#   `k` now takes all seven kinds and pts = 7.
#
# PORTED (pos-control-branch-reorder -> pos-arm-reorder): the sibling handles the
#   non-relational case first via an early return; here the two match arms are
#   permuted (preserved-comparison arm first). Same ARGUMENT (a faithful reshape
#   must verify). Verified to build.
# ADDED (pos-dispatch-on-kind): a second, maximally-different correct control that
#   dispatches directly on the comparison kind — naming each constructor
#   explicitly without the `relOf` lookup — confirming the grounded correspondence
#   is not echo-vulnerable and the spec is not over-fit to delegating through the
#   helper. Verified to build.
# RE-AIMED (admiss-readonly-input -> admiss-nondegenerate): the sibling asserts the
#   fractional-permission reads hold for an F2P-shaped node. This bundle has NO
#   `require` clause (the rewrite is total), so that probe is degenerate. Re-aimed
#   at the residual admissibility risk on a total domain — a DEGENERATE post-image
#   — via a live in-region assert pinning the two F2P behaviours (a supported
#   comparison → the matching UNEVALUATED relation; an unsupported comparison →
#   preserved) plus the unevaluated flag. Verified to build; the assert is live
#   (a false claim leaves an unsolved `decide` goal, verified out of band).
# VACUOUS (frame-mut-op, frame-mut-tag): the sibling carries these as MANDATORY
#   because the source AST node's operator / operand tags are held at
#   Acc(...,1/2) an impl can illegally WRITE, rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent, has no heap and no
#   aliasing, and this bundle declares NO `mut` binder on any input — there is no
#   read-only input to overwrite and no substitute probe. Omitted as vacuous, NOT
#   fabricated. The sibling's read-only obligation is here structurally guaranteed
#   by the absence of `mut`, which the frozen spec already encodes.
# PORTED (the five value rivals): each ports one-for-one and was SEEN to
#   discriminate with two real builds (rival build exit 0, gold build exit 1,
#   `decide proved … is false`):
#     wrong-constructor  -> weak-wrong-constructor (one fixed constructor for all,
#                           refuted on less-or-equal — one of the five mis-mapped);
#     operand-order-swap -> weak-operand-swap (swapped operands, refuted on a
#                           strict-less comparison of distinct operands);
#     evaluate-true      -> weak-evaluate-true (relation built evaluated, the exact
#                           reported defect, refuted on greater-or-equal);
#     partial-domain-drop-eq -> weak-drop-eq (equality treated as unsupported,
#                           refuted on equality);
#     over-convert-nonrelational -> weak-over-convert (an unsupported kind wrapped
#                           into a relation, refuted on the sole unsupported kind).
# AXIOM_TESTS (1): dropped. The axiom lane is G-AX's job (axiom_check.py); this
#   bundle declares no axiom and no A-reference deep model (the correspondence is
#   modeled deeply as `relOf` / `rewriteCompare`; meta.json axioms == [],
#   deep_model_references == []), and this gate ignores AXIOM_TESTS regardless.
# DIVERGENCE lane: the sibling ships NO diverge-* / nonterm-* / weak-diverge case
#   (its modeled behaviour is a single non-recursive dispatch), so there is nothing
#   to port. Independently re-derived for THIS bundle, which runs under
#   `loom.semantics.termination "total"` (an earlier revision of this file said
#   "partial" — that was wrong; the frozen Solution.lean line reads "total"). Under
#   `total` a diverging rival is genuinely REJECTED, so the class is neither
#   vacuous nor a spec hole. It is nevertheless unshippable here for a WITNESS
#   reason, measured with real builds: the rival module fails as required
#   (`Decreasing annotations are required in total correctness semantics`, exit 1),
#   but its WITNESS file — which the gate requires to elaborate, exit 0 — also
#   carries the loop, and the loop's WP generation leaves `Failed to prove
#   assertion without names: WPGen (forIn Lean.Loop.mk … sorry …)` plus
#   `declaration uses 'sorry'` (exit 1). The gate would record `witness-unproven`.
#   Recorded as a TOOLING BLOCK with that error text, not as vacuity.
#
# BINDER / CLAUSE COVERAGE. The obligation has four input binders — `visit`,
#   `k`, `l`, `r`. The five reject witnesses probe five DISTINCT input points
#   (pts=5) and between them move every binder: `k` ∈ {le, lt, ge, eq, other}
#   (5 kinds), `visit` ∈ {identity, constant} (2 lambdas), `l` ∈ {leaf 3, 0, 2,
#   5, 7}, `r` ∈ {leaf 4, 1, 2, 6, 8}. No binder is pinned across the rivals.
#   Clause coverage: the master P0 is attacked by every rival; the per-kind
#   bijection P2..P6 by weak-wrong-constructor (it mis-maps all five non-strict-
#   less operators; refuted at less-or-equal) with equality (P5) additionally
#   attacked by weak-drop-eq and strict-less (P1) by weak-operand-swap; greater
#   (P3) by weak-gt-to-ge and not-equal (P6) by weak-ne-inverted, each at its OWN
#   point (added by audit); the unevaluated pin (P8 and the `false` flag in
#   P1..P6) by weak-evaluate-true; preservation of an unsupported kind (P7) by
#   weak-over-convert. Every independent top-level clause is attacked by some
#   rival at a distinct point, and every supported kind is refuted at its own kind.
#
# AUDIT RECORD (independent re-derivation; no case relies on prose alone).
#   Statement integrity: all cases' spec views are BYTE-IDENTICAL to the frozen
#     one and the `method rewriteComparison` header (all nine `ensures`) matches
#     byte-for-byte — no case reformats or weakens the statement.
#   Witnesses: every reject witness rebuilt twice — rival exit 0, gold exit 1 with
#     `Tactic decide proved that the proposition ¬(…) = rewriteCompare … is false`,
#     a fully-evaluated PLAIN EVALUATION refutation (no missing identifier, no type
#     error, no unfolding failure, no timeout). Forgery test (attack B′) run on all
#     seven: dropping the `¬` makes the claim VERIFY on gold (exit 0) and FAIL on
#     the rival (exit 1) — a perfect inversion, so gold's exit code tracks the
#     claim and no case is hollow. All witness heads bind NOTHING, so there is no
#     consistency obligation and no room for a prove-from-contradiction forgery.
#   SPEC-TOO-WEAK probe (attack D): five NEW wrong impls the battery does not
#     contain were built and ALL were rejected — operands never rewritten (`visit`
#     dropped), left operand duplicated, equality/not-equal constructors
#     transposed, not-equal dropped from the supported set, and the preserved
#     comparison's operands rewritten. No spec hole found.
#   SPEC-TOO-STRONG probe (attack E): three NEW correct reshapes were built and ALL
#     verify — `Option.elim` in place of `match`, the visited operands hoisted into
#     locals before the dispatch, and the unsupported arm's kind spelled out as the
#     literal `.other` (definitionally equal, since only `.other` maps to `none`).
#     The spec accepts faithful reshapes; it is not over-fit to the frozen form.
#   Admissibility liveness: the in-region assert is LIVE, re-measured — replacing
#     its strict-less claim with the false `Le` claim leaves `error: unsolved goals
#     … ⊢ False` (exit 1), so the assert genuinely carries the post-image claim
#     rather than being discharged trivially.
#   Tester route: the header's claim that `prove_postcondition_decidable_for` is
#     unavailable was re-measured and is TRUE — it leaves `⊢ Decidable (∀ (rk :
#     RelKind) (b : Bool) (a c : Node), out = Node.relation rk b a c → b = false)`
#     unsolved, so the direct-triple witness route is the correct choice.
AXIOM_TESTS = []
