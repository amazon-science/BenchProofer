"""PBT manifest for sympy__sympy-21379 (velvet) — adversarial falsification battery.

NOT a Lean module; a record of adversarial cases the G-PBT runner executes and
stamps with the recorded verdict. Every case is a full `Solution.lean` variant
that shares the FROZEN spec byte-for-byte — only the text strictly inside the
single `-- impl-start` / `-- impl-end` region is edited, so `markers.same_spec`
holds by construction and the `prove_correct extractCommonFactor` obligation
header survives untouched. No case introduces an axiom, a helper lemma, a new
theorem, `sorry`/`admit`, or `native_decide`.

This battery is a PORT of the nagini sibling's spec lane, re-expressed against
this backend's carrier. The nagini surface contracted a single function too
(`reduce_extract_common_factor(code, p, q)`), so the port is close to 1:1 in
argument — but the carrier differs in one way that reshapes every case, and in
one way that drops a case class entirely (see ASSESSMENT at the bottom).

DEFENDED SURFACE (read from Solution.lean / mapping.md / refinement.md):

  ONE modeled method, ONE obligation:

    extractCommonFactor (p : Int) (q : Int)
        return (out : Except PolyErr (Int × Int × Int))
      ensures out = Except.ok (extractSpec p q)

  There is NO `require`, so the precondition is `True` and every operand pair
  is in-domain. That removes the LITERAL nagini admissibility probe but NOT the
  admissibility class: on this total carrier the analogue of PRECOND-TOO-STRONG
  is the single `ensures` being unsatisfiable at an F2P-shaped input, which
  `admiss-recovery-point-satisfiable` tests at a concrete point. The bundle is
  compiled `set_option loom.semantics.termination "total"`, so a diverging impl
  is REJECTED (measured) rather than admitted vacuously.
  The single `ensures` is an equation against the pure spec
  `extractSpec`, whose body is a three-way case split on the outcome of the
  opaque callee `commonFactor p q`. Those three arms are the independent
  top-level clauses this battery must attack:

    (A) the RECOVERY arm — the callee fails: the result is the triple
        (1, p, q). Two independent pins live here: the factor component is the
        trivial factor `1`, and BOTH operands pass through UNCHANGED. Also
        load-bearing: `out` is on the `Except.ok` leg at all, i.e. the failure
        is never propagated out. That last pin is the discriminating content of
        the gold change and is exactly what `Solution_prepatch.lean` violates.
    (B) the TRIVIAL-FACTOR arm — the callee succeeds with `1`: the operands are
        again returned unchanged, no reduction is warranted.
    (C) the NON-TRIVIAL-FACTOR arm — the callee succeeds with `g ≠ 1`: the
        factor component is that same `g`, and EACH operand is separately
        mapped through the opaque per-operand reduction at that factor.

  Every one of A/B/C is attacked below, and A's three pins (leg, factor,
  operands) are attacked separately, because an impl can get any one of them
  right while failing another.

  THE CARRIER IS OPAQUE, AND THAT IS THE WHOLE DIFFICULTY. `commonFactor` and
  `reduceTerm` are declared `opaque` with NO asserted contract, so no literal
  operand pair decides anything: `decide` stalls on the un-reduced callee term
  and the velvet tester machinery (`derive_tester_for`) is dead here for the
  same reason — its `Decidable` instance cannot reduce past the opaque head.
  Every reject witness therefore CONDITIONS on the carrier instead of computing
  it: it names the callee's outcome at one concrete operand pair by hypothesis
  and derives the contradiction from that. The claim each witness makes is
  stronger than any literal input could make — "whenever the callee behaves so
  at this pair, the rival's answer differs from the spec's" — and it is the
  sub-domain on which the rival is actually wrong.

  Hypotheses are kept as weak as each refutation needs. A witness that must
  separate an opaque reduction from its own argument carries exactly one
  disequality about exactly one such term (never two facts about the same term,
  which would be the inconsistent-binder shape the gate probes for); a witness
  that refutes a literal factor clash carries only the outcome hypothesis and
  no disequality at all. Every hypothesis set here is satisfiable: it constrains
  `commonFactor` at a single pair and, at most, `reduceTerm` at a single
  argument pair, and these are independent opaque functions with no axiom
  relating them.

  BINDER COVERAGE. The spec binds `p` and `q`. Both are varied across the
  reject witnesses — no binder is held at one value by every rival, and no two
  rivals share an input point unless they genuinely fail there for the same
  reason. Because the operands enter clauses A/B/C ASYMMETRICALLY only through
  clause C (which reduces each of them separately), one rival attacks the
  second operand's reduction ALONE (`drop-second-reduction`) and is refuted at
  its own point, so the battery distinguishes an impl that mishandles `q` from
  one that mishandles both. The seven distinct operand pairs probed are
  (3,7) (4,9) (6,8) (9,16) (10,25) (12,18) (14,21) — no rival is refuted at
  another's point except the two that attack the identical pin.

  ORACLE GROUNDING. The `ensures` equates `out` to `extractSpec p q`, which is
  built FROM the modeled inputs and the callee applied to them — there is no
  answer-key literal an impl could echo. The opaque values are never pinned to
  any constant, so a rival that substitutes a literal for a callee result is
  refutable (`fabricate-factor`, `always-trivial`), and a rival that passes the
  wrong argument to the reduction is refutable too.

  FRAME / PERMISSION-MUTATION CLASS: VACUOUS on this backend. `p` and `q` are
  read-only `Int` parameters of a referentially-transparent Lean function; there
  is no aliasing, no heap, and no fractional permission to violate, so the
  nagini directive-5 probe has no counterpart here — not a hole, simply nothing
  to express. The nagini sibling reached the same disposition for its own (int,
  by-value) carrier and re-expressed the surface as postcondition attacks
  instead; this port keeps that substance: the "operand post-state" attacks
  (`reduce-on-recovery`, `reduce-on-trivial`) reject for a POSTCONDITION reason,
  because clauses A and B pin each operand to pass through unchanged.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21379"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchor — the executable core of the SINGLE impl region, strictly
# inside `-- impl-start` / `-- impl-end`. Editing only this text keeps the spec
# view (and the `prove_correct` header) byte-identical. The frozen leading
# comment inside the region is NOT part of the anchor, so each variant keeps a
# region comment describing only what that variant does.
# ---------------------------------------------------------------------------
_GOLD_BODY = (
    "    let result : Int × Int × Int :=\n"
    "      match commonFactor p q with\n"
    "      | Except.error _ => (1, p, q)\n"
    "      | Except.ok g =>\n"
    "          if g = 1 then (g, p, q)\n"
    "          else (g, reduceTerm p g, reduceTerm q g)\n"
    "    return Except.ok result"
)

# Every witness needs the executable projection of the method under test.
# `extract_program_for` is a directive INSIDE the witness, so `…Exec` exists in
# both the rival file and the gold file by construction — the witness never
# names anything only one side declares.
_EXTRACT = "extract_program_for extractCommonFactor\n\n"


def _witness(pair, hyps, use_hr=False):
    """A carrier-conditioned refutation at the concrete operand pair `pair`.

    States that the method's executable projection at `pair` differs from the
    value the single `ensures` clause demands there, under the hypotheses
    `hyps` naming the opaque callee's behaviour at that pair. `unfold` exposes
    the impl and the pure spec; `simp` discharges the monadic wrapper and
    rewrites with the outcome hypothesis, leaving either a literal clash (which
    `simp` closes outright) or a residual disequality about the opaque
    reduction.

    `use_hr` puts the witness's own disequality `hr` INTO the simp set, so the
    residual disequality is closed by rewriting rather than by a hand-written
    `exact fun hc => absurd …` tail. That difference is not cosmetic, and it is
    the repair this battery's audit landed. With a tail, the refutation is
    discharged by a term whose ELABORATION depends on the goal `simp` happens
    to leave: against the frozen solution `simp` closes the goal down to
    `False`, the tail's `fun hc => …` then has nothing to bind, and the build
    fails with `Type mismatch` / `Invalid field notation: … cannot resolve
    field 'symm'`. That is a gold-side failure for a SYNTACTIC reason — the
    tail term does not typecheck — and a gold-side failure that is not a
    semantic refutation of the concrete claim is not evidence that the witness
    discriminates. Folding `hr` into `simp` removes the tail entirely, and the
    gold-side failure becomes the semantic `unsolved goals … ⊢ False`: `simp`
    reduced the frozen impl's claim to `False`, i.e. it PROVED the equation the
    witness denies. Measured on all four affected cases (rival exit 0, gold
    exit 1) before this shape was adopted.
    """
    p, q = pair
    simp_args = "NonDetT.run, h, hr, pure" if use_hr else "NonDetT.run, h, pure"
    return (
        _EXTRACT
        + "example " + hyps + " :\n"
        f"    extractCommonFactorExec {p} {q} ≠ "
        f"DivM.res (Except.ok (extractSpec {p} {q})) := by\n"
        "  unfold extractCommonFactorExec extractCommonFactor extractSpec\n"
        f"  simp [{simp_args}]\n"
    )


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): inline the triple into the return -----
    # Structurally different: the frozen impl names the produced triple in a
    # `let` and returns it on the next statement; this variant builds it
    # directly inside the `return`, so there is no intermediate binding at all.
    # Same computation, different statement shape. `loom_solve` + the frozen
    # `simp_all [extractSpec]` still closes it (measured), so the obligation is
    # really re-discharged rather than dodged. MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-inline-triple",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Branch on the shared-factor computation's OUTCOME and build the\n"
            "    -- resulting triple directly in the returned value, with no\n"
            "    -- intermediate binding: a failure is recovered with the trivial\n"
            "    -- factor and the operands unchanged, a success either leaves the\n"
            "    -- operands alone or reduces each by the factor found.\n"
            "    return Except.ok (\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (1, p, q)\n"
            "      | Except.ok g =>\n"
            "          if g = 1 then (g, p, q)\n"
            "          else (g, reduceTerm p g, reduceTerm q g))"),
        "rationale": "a behaviourally-identical reshape — the produced triple is "
                     "built inside the `return` instead of being named by a `let` "
                     "first — computes the same value on all three arms of the "
                     "outcome split, so it discharges the single `ensures` and must "
                     "verify. If it were rejected the spec would be pinning the "
                     "impl's statement SHAPE rather than its behaviour "
                     "(SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): name the outcome, flip the guard ------
    # Two independent reshapes at once: the callee's outcome is bound to a local
    # before the `match` (instead of being matched in place), and the
    # trivial-factor test is written with the OPPOSITE polarity, so the two
    # success arms are emitted in the reverse order. `if g ≠ 1 then … else …`
    # computes the same function as `if g = 1 then … else …` with the arms
    # swapped; nothing about the produced value changes. MUST verify.
    {
        "id": "pos-named-outcome-flipped-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Name the shared-factor computation's outcome first, then branch on\n"
            "    -- it, testing for a NON-trivial factor and so emitting the two\n"
            "    -- success arms in the reverse order. A failure is still recovered\n"
            "    -- with the trivial factor and the operands unchanged.\n"
            "    let outcome : Except PolyErr Int := commonFactor p q\n"
            "    let result : Int × Int × Int :=\n"
            "      match outcome with\n"
            "      | Except.error _ => (1, p, q)\n"
            "      | Except.ok g =>\n"
            "          if g ≠ 1 then (g, reduceTerm p g, reduceTerm q g)\n"
            "          else (g, p, q)\n"
            "    return Except.ok result"),
        "rationale": "binding the callee's outcome to a local and inverting the "
                     "trivial-factor guard (so the success arms are written in the "
                     "reverse order) is the same function computed in a different "
                     "shape: each of the three arms still yields the triple the "
                     "single `ensures` demands. It must verify, else the spec "
                     "over-constrains the branch polarity (SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped input ---
    # The method has no `require`, so the nagini sibling's "a normal in-domain
    # input is admitted" probe has no literal counterpart. That does NOT make the
    # lane vacuous: on a total carrier the analogue of PRECOND-TOO-STRONG is the
    # single `ensures` being UNSATISFIABLE at exactly the input shape the public
    # problem statement exhibits — the one on which the shared-factor computation
    # FAILS. If the obligation could not be discharged there, the spec would be
    # unimplementable on the very sub-domain the change exists to serve, and every
    # reject case above would be rejecting against an empty target.
    #
    # This case discharges that obligation at a concrete point, by evaluation, as
    # a `have`, BEFORE closing the frozen obligation verbatim: under the
    # hypothesis that the computation fails at (3,7), the value the `ensures`
    # demands reduces to the concrete triple `Except.ok (1, 3, 7)` — on the
    # `Except.ok` leg, with the trivial factor and both operands unchanged. The
    # frozen impl body follows untouched, so the method's own obligation still
    # discharges with the frozen proof script.
    #
    # The `have` is LIVE, not decoration: measured during the audit, replacing the
    # claimed triple with `(2, 3, 7)` — the same shape, one component changed —
    # leaves `unsolved goals … ⊢ False` and the build fails (exit 1). So the case
    # cannot pass by ignoring what it asserts.
    {
        "id": "admiss-recovery-point-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- The obligation is satisfiable at an input on which the\n"
            "    -- shared-factor computation FAILS: there the demanded value is a\n"
            "    -- concrete triple on the success leg, carrying the trivial factor\n"
            "    -- with both operands unchanged. Discharged by evaluation here,\n"
            "    -- before the step's own obligation is closed below.\n"
            "    have _adm : commonFactor 3 7 = Except.error PolyErr.polynomialError →\n"
            "        Except.ok (extractSpec 3 7)\n"
            "          = (Except.ok (1, 3, 7) : Except PolyErr (Int × Int × Int)) := by\n"
            "      intro hfail\n"
            "      unfold extractSpec\n"
            "      simp [hfail]\n"
            + _GOLD_BODY),
        "rationale": "the single `ensures` is SATISFIABLE, and satisfiable with the "
                     "intended value, at the operand shape the public problem "
                     "statement exhibits — the one on which the shared-factor "
                     "computation fails. The in-region `have` evaluates the demanded "
                     "value at that concrete point to `Except.ok (1, 3, 7)`: the "
                     "success leg, the trivial factor, both operands unchanged. This "
                     "is the total-carrier analogue of the nagini precondition probe: "
                     "if it could not be discharged the obligation would be "
                     "unsatisfiable exactly where the change matters "
                     "(PRECOND-TOO-STRONG), and the uniqueness lane would be "
                     "attacking an empty target. Measured live: the same `have` "
                     "claiming `(2, 3, 7)` fails with `unsolved goals … ⊢ False`.",
    },

    # -- UNIQUENESS / clause A, the `Except.ok` leg (the prepatch shape) ------
    # The discriminating content of the change: on a failure the step must
    # RECOVER, not propagate. This rival propagates the failure out on the
    # error leg (it is exactly the frozen `Solution_prepatch.lean` impl), while
    # behaving identically to gold on both success arms — so it is the
    # value-invisible control-flow rival: no operand pair on which the callee
    # SUCCEEDS distinguishes it from gold at all.
    {
        "id": "propagate-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Let the shared-factor computation's failure escape instead of\n"
            "    -- recovering from it locally; the success arms are unchanged.\n"
            "    let result : Except PolyErr (Int × Int × Int) :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error e => Except.error e\n"
            "      | Except.ok g =>\n"
            "          if g = 1 then Except.ok (g, p, q)\n"
            "          else Except.ok (g, reduceTerm p g, reduceTerm q g)\n"
            "    return result"),
        "refinement": "the faithful real patch is the UNGUARDED shared-factor "
                      "computation — i.e. the pre-change code, with no local "
                      "recovery at all. On the operand shape the public problem "
                      "statement exhibits, that computation fails and the failure "
                      "propagates out of the enclosing evaluation, which is the "
                      "reported defect and precisely what the FAIL_TO_PASS test "
                      "exercises: the added lines evaluate that shape and merely "
                      "reaching them without an escaping failure is the test. "
                      "Measured against the real repo: gold makes the FAIL_TO_PASS test pass and "
                      "this variant makes it fail with the escaping error. So it "
                      "does NOT resolve.",
        "rationale": "rejected by the single `ensures` on clause A: the spec puts "
                     "`out` on the `Except.ok` leg for EVERY outcome of the callee, "
                     "so a propagated `Except.error` cannot equal "
                     "`Except.ok (extractSpec p q)`. SPEC-TOO-WEAK if it verifies — "
                     "the spec would then fail to sense the defect at all.",
        "witness": _witness(
            (3, 7),
            "(h : commonFactor 3 7 = Except.error PolyErr.polynomialError)"),
    },

    # -- UNIQUENESS / clause A, the FACTOR pin -------------------------------
    # Recover (so nothing escapes — this rival satisfies the leg pin that the
    # previous one violates) but recover with a NON-trivial factor. Isolates
    # clause A's factor component from its leg component.
    {
        "id": "wrong-factor-on-recovery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Recover from the shared-factor computation's failure, but take the\n"
            "    -- recovered factor to be a non-trivial one rather than the trivial\n"
            "    -- factor; the operands are left unchanged and the success arms are\n"
            "    -- unchanged.\n"
            "    let result : Int × Int × Int :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (2, p, q)\n"
            "      | Except.ok g =>\n"
            "          if g = 1 then (g, p, q)\n"
            "          else (g, reduceTerm p g, reduceTerm q g)\n"
            "    return Except.ok result"),
        "refinement": "NO VALID REFINEMENT ARGUMENT EXISTS FOR THIS RIVAL, and the "
                      "honest reason is worth more than a fabricated one. MEASURED "
                      "against the real repo at the base commit with the test patch "
                      "applied: the faithful real patch — recover with a non-unit "
                      "factor instead of the unit one — PASSES the FAIL_TO_PASS "
                      "test, and passes the entire enclosing test module with a "
                      "summary byte-identical to gold's. It therefore DOES resolve, "
                      "so this case is NOT a refinement defense. The cause is "
                      "structural, not a poor choice of rival: the lines the test "
                      "patch adds are BARE STATEMENTS with no assertion, so they "
                      "detect only whether an exception escapes, never what value "
                      "the recovery produces; and no pre-existing assertion in the "
                      "test exercises an operand shape that reaches the recovery "
                      "path at all. The recovered factor IS observable in the "
                      "library (it scales the result the step feeds downstream — "
                      "probed directly, this rival returns a value scaled by the "
                      "spurious factor), it is simply unobserved BY THIS TEST. So "
                      "this case measures something real that the F2P cannot: the "
                      "frozen spec is STRONGER than the F2P test on the recovery "
                      "path. It is retained for that reason, and is flagged here "
                      "rather than dressed up, because a rival whose patch resolves "
                      "is the opposite of a verify-does-not-imply-resolve break.",
        "rationale": "rejected by clause A's factor pin: on the failure outcome the "
                     "spec demands the triple `(1, p, q)`, and the literal `2` in "
                     "the first component is provably not `1`. Note this rival "
                     "SATISFIES the leg pin that `propagate-failure` violates, so "
                     "the two attack genuinely independent content of the same "
                     "clause and are refuted at different operand pairs. "
                     "SPEC-TOO-WEAK if it verifies.",
        "witness": _witness(
            (4, 9),
            "(h : commonFactor 4 9 = Except.error PolyErr.polynomialError)"),
    },

    # -- UNIQUENESS / clause A, the OPERAND pin ------------------------------
    # Recover with the correct trivial factor (so clause A's factor pin holds)
    # but REDUCE the operands on the way out, on a path where clause A pins
    # them to pass through unchanged. This is the port of nagini's
    # operand-overwrite / value-double-mask rival: there is no permission to
    # violate on this carrier, so it rejects for a POSTCONDITION reason.
    {
        "id": "reduce-on-recovery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Recover from the failure with the trivial factor, but pass both\n"
            "    -- operands through the per-operand reduction at a spurious factor\n"
            "    -- on the way out, on the very path where they are to be left as\n"
            "    -- they were. The success arms are unchanged.\n"
            "    let result : Int × Int × Int :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (1, reduceTerm p 7, reduceTerm q 7)\n"
            "      | Except.ok g =>\n"
            "          if g = 1 then (g, p, q)\n"
            "          else (g, reduceTerm p g, reduceTerm q g)\n"
            "    return Except.ok result"),
        "refinement": "NO VALID REFINEMENT ARGUMENT EXISTS FOR THIS RIVAL — same "
                      "structural cause as `wrong-factor-on-recovery`, which see. "
                      "MEASURED against the real repo: the faithful real patch — "
                      "recover with the unit factor but rewrite both operands by a "
                      "spurious factor on that path — PASSES the FAIL_TO_PASS test "
                      "and the entire enclosing test module, matching gold's "
                      "summary exactly. It DOES resolve. The rewritten operands are "
                      "genuinely observable in the library (probed directly, this "
                      "rival returns a result built over both operands divided by "
                      "the spurious factor), but the F2P test never observes the "
                      "recovery path's VALUE — its added lines are bare statements "
                      "checking only that no exception escapes. Retained because it "
                      "attacks a real and otherwise-unattacked pin of the spec "
                      "(clause A fixes each operand to pass through unchanged), and "
                      "flagged plainly because its patch resolving means this case "
                      "is a spec-stronger-than-F2P measurement, not a "
                      "verify-does-not-imply-resolve defense.",
        "rationale": "rejected by clause A's operand pin: the spec demands "
                     "`(1, p, q)` on the failure outcome, so the second component "
                     "must be `p` itself; the rival offers the opaque "
                     "`reduceTerm p 7`, which is not provably `p`. The witness "
                     "assumes exactly that separation at one argument pair (one "
                     "hypothesis about one opaque term) and nothing more. This is "
                     "where the nagini frame/read-only surface lands on a "
                     "referentially-transparent carrier: the postcondition, not a "
                     "permission, is what pins the operand post-state. "
                     "SPEC-TOO-WEAK if it verifies.",
        "witness": _witness(
            (6, 8),
            "(h : commonFactor 6 8 = Except.error PolyErr.polynomialError)\n"
            "    (hr : reduceTerm 6 7 ≠ 6)",
            use_hr=True),
    },

    # -- UNIQUENESS / clause B, the trivial-factor arm -----------------------
    # Drop the trivial-factor guard, so the reduction runs even when the factor
    # IS trivial. Clause B pins the operands to pass through unchanged there.
    # This is the only rival that attacks the middle arm, and it is the reason
    # the guard is load-bearing rather than a decoration.
    {
        "id": "reduce-on-trivial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Drop the trivial-factor test on the success path, so both operands\n"
            "    -- go through the per-operand reduction unconditionally — including\n"
            "    -- when the factor found is the trivial one and no reduction is\n"
            "    -- warranted. The recovery arm is unchanged.\n"
            "    let result : Int × Int × Int :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (1, p, q)\n"
            "      | Except.ok g => (g, reduceTerm p g, reduceTerm q g)\n"
            "    return Except.ok result"),
        "refinement": "the faithful real patch deletes the non-trivial-factor guard "
                      "and rewrites both operands unconditionally. That reaches far "
                      "beyond the reported defect: every reduction of this step with "
                      "a unit shared factor — the overwhelmingly common case — now "
                      "rewrites its operands where it previously passed them "
                      "straight through. Measured against the real repo, the FAIL_TO_PASS test "
                      "fails under this variant on pre-existing assertions, so it "
                      "does NOT resolve.",
        "rationale": "rejected by clause B: when the callee succeeds with the "
                     "trivial factor the spec demands `(g, p, q)` — the operands "
                     "unchanged — and the rival supplies the opaque "
                     "`reduceTerm p g`, unprovably equal to `p`. This is the middle "
                     "arm of the outcome split, independent of clauses A and C: an "
                     "impl can get both of those right and still be wrong here, "
                     "which is exactly this rival. SPEC-TOO-WEAK if it verifies.",
        "witness": _witness(
            (9, 16),
            "(h : commonFactor 9 16 = Except.ok 1)\n"
            "    (hr : reduceTerm 9 1 ≠ 9)",
            use_hr=True),
    },

    # -- UNIQUENESS / clause C, drop the reduction entirely ------------------
    # The canonical partial-domain rival: keep the recovery (so clause A's leg
    # pin holds) but never reduce either operand, so the non-trivial-factor arm
    # returns the untransformed pair. This is the port of nagini's
    # drop-operand-regroup / G-EQ closer.
    {
        "id": "drop-reduction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Recover from a failure as required, but never apply the\n"
            "    -- per-operand reduction: on every success the operands are handed\n"
            "    -- back exactly as they came in, whatever factor was found.\n"
            "    let result : Int × Int × Int :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (1, p, q)\n"
            "      | Except.ok g => (g, p, q)\n"
            "    return Except.ok result"),
        "refinement": "the faithful real patch keeps the local recovery but deletes "
                      "the per-operand reduction from the success path. It leaves a "
                      "shared factor un-extracted, so a reduction whose operands do "
                      "share a non-unit factor returns the un-reduced form instead "
                      "of the reduced one. Measured against the real repo, the FAIL_TO_PASS test "
                      "fails under this variant on a pre-existing assertion of that "
                      "exact behaviour — one that has nothing to do with the newly "
                      "added lines — so it does NOT resolve.",
        "rationale": "rejected by clause C: on a non-trivial factor the spec demands "
                     "`(g, reduceTerm p g, reduceTerm q g)` and the rival supplies "
                     "`(g, p, q)`; because the reduction is opaque, `p` is not "
                     "provably `reduceTerm p g`. Distinct from "
                     "`drop-second-reduction`: that rival still reduces the first "
                     "operand, so it agrees with gold over strictly more of the "
                     "domain and is refuted at its own point on the operand it "
                     "neglects. SPEC-TOO-WEAK if it verifies.",
        # The disequality is stated with the OPERAND on the left
        # (`10 ≠ reduceTerm 10 5`, not the reverse): this rival hands back the
        # un-reduced operand, so the residual equation `simp` leaves is oriented
        # operand-first, and `hr` only rewrites it in that orientation. Measured
        # both ways — the reverse orientation leaves the goal open on the rival.
        "witness": _witness(
            (10, 25),
            "(h : commonFactor 10 25 = Except.ok 5)\n"
            "    (hr : (10 : Int) ≠ reduceTerm 10 5)",
            use_hr=True),
    },

    # -- UNIQUENESS / clause C, drop only the SECOND operand's reduction -----
    # A NEAR-MISS of the previous rival: it reduces the first operand correctly
    # and neglects only the second, so it agrees with gold on strictly more of
    # the domain. Refuted at its OWN point, on the second operand, so the
    # manifest demonstrates the sub-domain its rationale claims. This is what
    # makes the battery sensitive to a per-binder error rather than only to a
    # wholesale one.
    {
        "id": "drop-second-reduction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Apply the per-operand reduction to the first operand only, leaving\n"
            "    -- the second one as it came in. The trivial-factor test and the\n"
            "    -- recovery arm are unchanged.\n"
            "    let result : Int × Int × Int :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (1, p, q)\n"
            "      | Except.ok g =>\n"
            "          if g = 1 then (g, p, q)\n"
            "          else (g, reduceTerm p g, q)\n"
            "    return Except.ok result"),
        "refinement": "the faithful real patch rewrites only the first operand and "
                      "leaves the second un-reduced, so a reduction over operands "
                      "sharing a non-unit factor is built from a reduced first "
                      "operand over an un-reduced second one. Measured against the "
                      "real repo, the FAIL_TO_PASS test fails under this variant on a "
                      "pre-existing assertion pinning the fully-reduced form, so it "
                      "does NOT resolve.",
        "rationale": "rejected by clause C on its THIRD component: the spec demands "
                     "`reduceTerm q g` there and the rival supplies `q`. The witness "
                     "is stated at its own operand pair and its disequality names "
                     "the SECOND operand's reduction, so this case demonstrates the "
                     "narrower sub-domain it claims rather than borrowing "
                     "`drop-reduction`'s point — a rival that mishandled only the "
                     "second operand would otherwise be invisible to the battery. "
                     "SPEC-TOO-WEAK if it verifies.",
        # Operand-first orientation, as in `drop-reduction` and for the same
        # reason; the disequality names the SECOND operand's reduction, which is
        # the component this rival neglects.
        "witness": _witness(
            (12, 18),
            "(h : commonFactor 12 18 = Except.ok 6)\n"
            "    (hr : (18 : Int) ≠ reduceTerm 18 6)",
            use_hr=True),
    },

    # -- UNIQUENESS / clause C, fabricate the factor (opacity attack) --------
    # Do all the real work — consult the callee, honour the guard, reduce both
    # operands at the factor found — but report a FABRICATED literal factor in
    # the first component. Attacks the opacity head-on: a literal cannot be
    # proven equal to an unpinned opaque value.
    {
        "id": "fabricate-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Consult the shared-factor computation and reduce both operands by\n"
            "    -- the factor it found, but report a fabricated literal factor in the\n"
            "    -- first component of the triple instead of the factor actually\n"
            "    -- found. The trivial-factor test and the recovery arm are unchanged.\n"
            "    let result : Int × Int × Int :=\n"
            "      match commonFactor p q with\n"
            "      | Except.error _ => (1, p, q)\n"
            "      | Except.ok g =>\n"
            "          if g = 1 then (g, p, q)\n"
            "          else (2, reduceTerm p g, reduceTerm q g)\n"
            "    return Except.ok result"),
        "refinement": "the faithful real patch reduces the operands by the factor it "
                      "found but reports a fixed non-unit factor alongside them. The "
                      "reported factor multiplies the result the step feeds "
                      "downstream, so every reduction whose shared factor is not "
                      "that literal returns a wrongly-scaled value. Measured against "
                      "the real repo, the FAIL_TO_PASS test fails under this variant on "
                      "pre-existing assertions, so it does NOT resolve.",
        "rationale": "rejected by clause C's factor component: the spec demands the "
                     "factor the callee returned, and the opaque callee's value is "
                     "nowhere pinned to any constant, so a fabricated literal `2` is "
                     "unprovably equal to it. This is the grounding attack — it "
                     "shows the `ensures` cannot be discharged by echoing a "
                     "constant. SPEC-TOO-WEAK if it verifies.",
        "witness": _witness(
            (14, 21), "(h : commonFactor 14 21 = Except.ok 7)"),
    },

    # -- UNIQUENESS / collapse to the recovery triple on every input ---------
    # The maximal cheat: ignore the callee entirely and always return the
    # trivial-recovery triple. It happens to be correct on clause A and on
    # clause B, and wrong on clause C — a rival that is right on two of three
    # arms, which is why the battery needs clause C attacked at all.
    {
        "id": "always-trivial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    -- Never consult the shared-factor computation at all: always report\n"
            "    -- the trivial factor with both operands unchanged, as though every\n"
            "    -- input were the trivial case.\n"
            "    let result : Int × Int × Int := (1, p, q)\n"
            "    return Except.ok result"),
        "refinement": "the faithful real patch removes the shared-factor extraction "
                      "outright, always taking the unit factor and leaving the "
                      "operands alone. It does silence the reported failure — "
                      "nothing can fail if the computation is never run — but it "
                      "abandons the extraction the step exists to perform. Measured "
                      "against the real repo, the FAIL_TO_PASS test fails under this variant on "
                      "the pre-existing assertions pinning the extracted form, so it "
                      "does NOT resolve. This is the sharpest "
                      "verify-does-not-imply-resolve shape in the battery: the rival "
                      "is right on two of the spec's three arms and its patch "
                      "genuinely stops the reported error, yet it does not resolve. "
                      "Measured detail: the assertion that actually catches it first "
                      "is in the enclosing test's float-handling section, not the "
                      "extraction section — the step's downstream behaviour depends "
                      "on the extracted factor more broadly than the extraction "
                      "assertions alone reveal.",
        "rationale": "rejected by clause C: with the callee never consulted, the "
                     "first component is the literal `1` where the spec demands the "
                     "opaque factor found, and the operands are un-reduced where the "
                     "spec demands them reduced. Correct on clauses A and B, so it "
                     "is refutable ONLY through clause C. SPEC-TOO-WEAK if it "
                     "verifies.",
        "witness": _witness(
            (15, 20), "(h : commonFactor 15 20 = Except.ok 5)"),
    },
]


# ===========================================================================
# ASSESSMENT — what ported, what did not, and why
# ===========================================================================
#
# REFINEMENT GROUND TRUTH — every reject case's claim was MEASURED, not argued.
# Each rival's faithful real patch was applied to the real repository at the base
# commit with the SWE-bench test patch applied, and the FAIL_TO_PASS test was
# run. Two claims I had drafted turned out to be FALSE and are corrected in the
# cases above rather than shipped:
#
#   rival                       F2P test   refinement defense holds?
#   propagate-failure           FAIL       yes  (this is the reported defect)
#   wrong-factor-on-recovery    PASS       NO  <- patch RESOLVES; flagged in case
#   reduce-on-recovery          PASS       NO  <- patch RESOLVES; flagged in case
#   reduce-on-trivial           FAIL       yes
#   drop-reduction              FAIL       yes
#   drop-second-reduction       FAIL       yes
#   fabricate-factor            FAIL       yes
#   always-trivial              FAIL       yes
#
# The two PASSes are one structural fact, not two accidents: the lines the test
# patch adds are BARE STATEMENTS with no assertion, so they detect only whether
# an exception ESCAPES, never what value the recovery produces — and no
# pre-existing assertion in that test reaches the recovery path. So ANY rival
# differing from gold only on the recovery path is invisible to the F2P, and no
# re-argument could rescue those two: re-arguing would mean asserting something
# the measurement contradicts. Both are RETAINED, because each attacks a real
# and otherwise-unattacked pin of clause A (its factor component and its operand
# components) and both were confirmed observably wrong in the library by direct
# probe — but each carries the correction in its own `refinement` field. What
# they establish is the converse of a refinement defense and is worth recording
# on its own: on the recovery path the FROZEN SPEC IS STRICTLY STRONGER THAN THE
# F2P TEST. The six rivals whose patches do NOT resolve carry the battery's
# verify-does-not-imply-resolve weight, and they cover all three arms of the
# outcome split, so no clause depends solely on a flagged case.
#
# PORTED from the nagini sibling (argument carried over, mechanics rewritten
# for this carrier):
#
#   nagini `drop-operand-regroup`      -> `drop-reduction`
#   nagini `drop-one-operand-transform`-> `drop-second-reduction`
#   nagini `hardcode-trivial-always`   -> `always-trivial`
#   nagini `fabricate-literal-factor`  -> `fabricate-factor`
#   nagini `unguarded-raise-escapes`   -> `propagate-failure`
#   nagini `wrong-factor-on-refusal`   -> `wrong-factor-on-recovery`
#   nagini `operand-overwrite-on-refusal` -> `reduce-on-recovery`
#   nagini `pos-result-local` / `pos-tuple-transform` -> `pos-inline-triple` /
#       `pos-named-outcome-flipped-guard` (two structurally distinct correct
#       impls; both verify with the frozen proof script, measured)
#
# ADDED beyond the nagini sibling: `reduce-on-trivial`. The nagini spec's clause
# 3b made the trivial-factor case a statement about the factor only, whereas
# this carrier's clause B independently pins the OPERANDS on that arm too. That
# arm was otherwise unattacked, and an impl wrong only there would have
# verified — the same shape as the two real failures this port class has already
# produced elsewhere.
#
# OMITTED, with reasons:
#
#   * nagini `admiss-incode-range` (admissibility). PORTED, not omitted — see
#     `admiss-recovery-point-satisfiable` above. An earlier revision of this
#     manifest recorded the class as VACUOUS on the reasoning that the method has
#     no `require`, so "there is nothing a rival could over-constrain". That
#     reasoning was WRONG and the audit corrected it. The absence of a
#     precondition removes the LITERAL nagini probe, not the class: on a total
#     carrier the analogue of PRECOND-TOO-STRONG is the single `ensures` being
#     unsatisfiable at exactly an F2P-shaped input, which a positive that
#     discharges the obligation at that concrete point — by evaluation, as a
#     `have`, before closing the frozen obligation verbatim — tests directly.
#     That is what the added case does, at the operand shape on which the
#     shared-factor computation fails, and its `have` was measured LIVE (the same
#     claim with one component changed fails with `⊢ False`).
#
#   * nagini's frame / permission-mutation surface. VACUOUS on this backend, as
#     the docstring records: no aliasing, no heap, no fractional permission, so
#     there is no permission to violate. The nagini sibling had already reached
#     this disposition for its own by-value int carrier and re-expressed the
#     surface as postcondition attacks on the operand post-state; that substance
#     IS ported, as `reduce-on-recovery` and `reduce-on-trivial`. No substitute
#     is fabricated for the permission mechanism itself.
#
#   * nagini `diverge-before-return` (non-termination). NOT a spec hole here. An
#     earlier revision of this manifest recorded it as a KNOWN SPEC HOLE on the
#     stated ground that "this bundle is compiled under `set_option
#     loom.semantics.termination "partial"`", so a diverging impl would verify
#     vacuously. That premise is FALSE and the audit corrected it by reading the
#     frozen file: this bundle sets `loom.semantics.termination "total"`. Under
#     `total` the verifier discharges a termination obligation, and the class is
#     REJECTED rather than admitted — measured, twice, on rivals that splice an
#     unbounded `while n ≥ 0 do n := n + 1` ahead of the impl body (once keeping
#     gold's value, once returning the unambiguously wrong `(0, 0, 0)`): both
#     fail, exit 1, with `error: Decreasing annotations are required in total
#     correctness semantics`. A THIRD rival closes the obvious gap in that pair,
#     since neither of the two carries a measure and their refusal could be read as
#     the annotation linter alone: `let mut k : Nat := 1` / `while k > 0` with
#     `invariant k > 0`, `done_with k = 0`, `decreasing k`, body `k := k + 1`,
#     spliced at the impl anchor with each proof reduced to a bare `loom_solve`, is
#     REJECTED at exit 1 on the measure's OWN descent goal,
#     `case decreasing_1: k ... |- k + 1 < k`, reported as `unsolved goals`. So the
#     annotation is required to be TRUE and not merely present, and the spec senses
#     divergence on a real proof obligation. The internal findings note this bullet
#     used to cite (scoping the hole to a cohort of `partial` bundles against a
#     smaller `total` one) has been withdrawn, and that cohort does not exist: all
#     500 velvet bundles set `"total"` and none sets `"partial"`. The mechanism is
#     cited directly instead: `TotalCorrectness.DemonicChoice.WPGen.
#     forWithInvariantLoop` takes `measure : β -> Nat` and emits
#     `measure b' < measure b`, where the `PartialCorrectness` twin takes an
#     `Option ℕ` and DISCARDS it; and the `set_option` is not inert, since its own
#     elaborator opens the matching scope
#     (`Loom/MonadAlgebras/WP/Options.lean`, `openScope`).
#
#     It nonetheless cannot SHIP as a reject case, for a mechanical reason rather
#     than a spec one, and this is the honest disposition: the witness protocol
#     requires the witness to ELABORATE against the rival, and the missing-measure
#     error fires at the loop site — which lives inside the impl region and so is
#     present in the witness file too. Measured: the rival-side witness build
#     fails (exit 1) with that same `Decreasing annotations are required` error
#     before the witness's own `example` is ever reached, so the case would be
#     recorded `witness-unproven` (a MALFORMED-TESTS error) rather than a
#     rejection. The class is therefore CLOSED BY THE SPEC but not expressible as
#     a witnessed case on this carrier — a tooling limit of the witness protocol,
#     recorded here with the error text rather than mis-recorded as a spec hole.
#
#   * nagini `AXIOM_TESTS` (3 cases). Dropped by instruction — the axiom lane is
#     G-AX's job and this gate ignores them. This bundle declares no consumed
#     axiom anyway (`meta.json "axioms": []`); both callees are A-reference deep
#     model references already validated against the real callees by G-AX.
#
# NO soundness positive was dropped for want of a proof: both positives above
# close with the frozen `prove_correct` script unmodified, verified by real
# builds before shipping. Nothing here reaches for `sorry`, a helper lemma, or a
# weakened obligation.
#
# WITNESS METHOD. The velvet tester machinery (`derive_tester_for` ->
# `…Tester args = false`) is DEAD on this bundle: the postcondition's
# `Decidable` instance cannot reduce past the opaque `commonFactor` head, so the
# tester is stuck identically for gold and for every rival and discriminates
# nothing. Every witness therefore conditions on the carrier instead, and every
# one was checked by hand before shipping — built against its rival (must
# elaborate) and against the frozen solution (must fail), plus the
# binder-satisfiability probe (must NOT derive `False`). All eight discriminate.
#
# INDEPENDENT AUDIT (post-port). Every claim above was re-derived with real
# builds by an auditor who did not write the battery. What it found and changed:
#
#   * REPAIRED, 4 cases (`reduce-on-recovery`, `reduce-on-trivial`,
#     `drop-reduction`, `drop-second-reduction`). As shipped, these four closed
#     their residual disequality with a hand-written
#     `exact fun hc => absurd hc[.symm] hr` tail. Each one DID discriminate by
#     exit code (rival 0, gold 1), but the gold-side failure was SYNTACTIC: the
#     recorded `gold_signature` was `Type mismatch` (two cases) and
#     `Invalid field notation: Type of hc is not known; cannot resolve field
#     'symm'` (two cases). Diagnosed by rebuilding each witness with the tail
#     REMOVED: against the frozen solution `simp` closes the goal all the way to
#     `⊢ False`, so the tail term has no hypothesis to bind and fails to
#     elaborate — a gold-side build failure that is not a refutation of anything.
#     The tail was therefore load-bearing for the wrong reason. Repaired by
#     folding `hr` into the simp set (see `_witness`), which deletes the tail;
#     the two `drop-*` disequalities additionally had to be reoriented
#     operand-first, because those rivals return the UN-reduced operand and the
#     residual equation is oriented accordingly. Re-measured after the repair,
#     all four: rival exit 0, gold exit 1 with the semantic
#     `unsolved goals … ⊢ False`. Same discrimination, now for a semantic reason.
#
#   * CONFIRMED, all 8 reject cases, by a check the gate does not run: an
#     AGREEMENT PROBE per case — the witness's own hypotheses and script with the
#     `≠` flipped to `=`, i.e. the claim that the FROZEN impl IS correct at that
#     point. All eight elaborate against the frozen solution (exit 0) and FAIL
#     against their rival (exit 1). That is the two-sided result the exit codes
#     alone cannot give: gold satisfies the spec at the witness's point, the
#     rival does not, so each rejection is attributable to the spec and not to a
#     tactic mismatch. The four `simp`-only witnesses were already semantic and
#     are unchanged.
#
#   * SPEC-TOO-WEAK probe (4 NEW wrong impls the battery does not contain, aimed
#     at the least-probed content): swap the two reduced operands in clause C;
#     guard on `g = 0` instead of `g = 1`; reduce at the literal `1` instead of
#     at the factor found; swap the operands on the RECOVERY arm. All four are
#     REJECTED by the frozen spec (exit 1). No spec hole found. The
#     operand-swap rival was additionally given a witness of its own
#     (`reduceTerm 27 4 ≠ reduceTerm 8 4` at (8,27)) and it discriminates
#     (rival 0, gold 1, semantic `⊢ False`), confirming the rejection is the
#     spec's and that clause C pins the two operands to their OWN reductions
#     rather than merely to the pair of them.
#
#   * SPEC-TOO-STRONG probe (3 NEW correct reshapes). Two verify with the frozen
#     proof script unchanged: rebuild the triple through its projections
#     (`(t.1, t.2.1, t.2.2)`) and write the guard as a DEPENDENT `if _hg : g = 1`.
#     The third — matching the error leg with the explicit constructor pattern
#     `| Except.error PolyErr.polynomialError =>` instead of the wildcard `_` —
#     is REJECTED by the frozen script, whose `simp_all` leaves the two `match`
#     forms un-unified. That is a TACTIC limit, not a spec hole, and it was
#     measured as such rather than assumed: the same impl VERIFIES (exit 0) once
#     the script is `simp only [extractSpec]; split <;> simp_all`. A variant may
#     reprove freely, so nothing here is a defect of the frozen spec — recorded
#     because "a correct impl the spec rejects" is the claim that would have been
#     a soundness hole had the stronger script also failed.
#
#   * The frame/permission class and the `admiss-incode-range` omission were
#     re-derived independently and both dispositions hold. The
#     `diverge-before-return` omission is NOT a divergence hole. That earlier
#     reading, and the internal findings note it deferred to, are both withdrawn:
#     the note no longer exists and the class is REJECTED BY THE SPEC here, as the
#     corrected divergence bullet above records with three measured rivals. The
#     omission is a WITNESS-protocol limit, since a rival that fails to elaborate
#     admits no witness at all.
#
# Unchanged by the audit: statement integrity (all 10 variants are byte-identical
# to the frozen file outside the impl region, diffed), the binder-satisfiability
# probes (all 8 correctly FAIL to derive `False`), the two positives, and the
# refinement ground-truth table above.
#
# ===========================================================================
# SECOND INDEPENDENT AUDIT — every claim re-derived with real builds by an
# auditor who wrote neither the battery nor the first audit. 74 builds.
# ===========================================================================
#
# Two of the dispositions above were FALSE AS SHIPPED, both traceable to one
# root cause, and the cause is NOT a misreading by the port. The frozen spec's
# termination semantics were CHANGED UNDER THIS BATTERY after it was written:
#
#   properties.py authored ....................... 02:27  (bundle was `partial`)
#   Solution.lean + Solution_prepatch.lean flipped
#     `partial` -> `total` by another lane ....... 03:38
#   G-PBT re-run and stamped SOUND ............... 03:39
#
# So every `partial`-premised sentence in this manifest was TRUE when written and
# became false 71 minutes later, and the gate that re-ran one minute after the
# flip could not see it — the gate re-runs cases, it does not re-read prose. The
# admissibility omission is independent of the flip and was a real gap from the
# start. Both are corrected in place above; the bullets below record what was
# measured.
#
# THE TRANSFERABLE LESSON, worth more than either local fix: a frozen-spec
# remediation landed without re-auditing the batteries that reason ABOUT that
# spec's semantics. Any battery whose prose cites `loom.semantics.termination`
# is stale wherever that flip was applied, and no gate in this lane detects it.
# This cell was NOT an isolated instance: a sweep for velvet bundles flipped
# `partial` -> `total` whose battery prose still argued from `partial` (recording
# the class as vacuous or as a known spec hole) returned 228 cells at the time this
# note was written. Every one of them UNDERSTATED its artifact in the same
# direction this one did, describing a divergence hole the `total` flip had
# actually closed. That follow-up has since been carried out corpus-wide: the flip
# is COMPLETE (500 of 500 velvet bundles set `"total"`, none `"partial"`) and the
# `partial`-premised prose has been corrected across the affected cells. Retained
# here for the lesson rather than as an open item.
#
#   * DEFECT 1, FIXED — the `admissibility` lane was MISSING, recorded as
#     "vacuous here". It is not vacuous: it is expressible on this carrier and is
#     now shipped as `admiss-recovery-point-satisfiable`. The battery previously
#     tested only soundness and uniqueness, dropping one of the three directions
#     this gate exists to test (PRECOND-TOO-STRONG). `scripts/pbt_coverage.py`
#     independently flags the same omission. Measured: the added case verifies
#     (exit 0, no warnings) and its `have` is live — the same `have` claiming
#     `(2, 3, 7)` instead of `(1, 3, 7)` fails with `unsolved goals … ⊢ False`.
#
#   * DEFECT 2, PROSE CORRECTED — the divergence class was recorded as a KNOWN
#     SPEC HOLE on an explicitly stated `"partial"` premise that the frozen file
#     contradicts. Under this bundle's actual `"total"` semantics the class is
#     REJECTED by the spec, so the battery was describing a hole that does not
#     exist in this cell — the inverse error, and the more dangerous direction,
#     since it understates the artifact. Re-measured on two diverging rivals;
#     both exit 1 with `Decreasing annotations are required in total correctness
#     semantics`. The corrected bullet above also records, with its error text,
#     the separate mechanical reason the class still cannot ship as a witnessed
#     reject case.
#
#   * CONFIRMED, all 8 reject cases, by rebuilding both halves independently:
#     rival exit 0 and gold exit 1 for every one, with a SEMANTIC gold-side
#     failure in all 8 — `unsolved goals … ⊢ False`, i.e. `simp` PROVED for the
#     frozen impl the equation each witness denies. All 8 `gold_signature`
#     records in meta.json reproduce byte-for-byte.
#
#   * CONFIRMED by the FORGERY test (attack B′), all 8: the witness with `≠`
#     flipped to `=` — the claim that the frozen impl IS correct at that point —
#     ELABORATES against the frozen solution (exit 0) and FAILS against the rival
#     (exit 1, `unsolved goals … ⊢ False`). Gold's exit code therefore tracks the
#     CLAIM and not the file, which is the two-sided result an exit code alone
#     cannot give. No case is hollow.
#
#   * CONFIRMED, the four `hr` witnesses: `hr` is load-bearing on the RIVAL side
#     and genuinely unused on gold. Rebuilding each with `hr` removed from the
#     simp set fails against its own rival (exit 1, all four), while gold's build
#     reports `hr` unused — so the disequality is doing the refutation work
#     exactly where it is supposed to and nowhere else.
#
#   * CONFIRMED, all 8 consistency probes: none derives `False` from its
#     witness's own hypotheses (exit 1 each, `simp_all made no progress` or
#     `unsolved goals`). No witness proves its refutation from a contradiction.
#
#   * SPEC-TOO-WEAK probe (attack D) — 9 NEW wrong impls beyond both the battery
#     and the first audit, aimed at the recovery arm's operand identity and at
#     the reduction's argument positions: swallow a non-trivial success factor
#     into the trivial triple; cross the two reduced operands; duplicate the
#     first operand on recovery; reduce at the literal `1`; INVERT the
#     trivial-factor guard; return literal `0` operands on recovery; consult the
#     callee twice with the arguments transposed; reduce each operand at the
#     OTHER operand rather than at the factor; return an operand as the recovered
#     factor. ALL NINE ARE REJECTED (exit 1). No spec hole found.
#
#   * SPEC-TOO-STRONG probe (attack E) — 6 NEW correct reshapes. Four verify with
#     the frozen proof script untouched: let-bound reduced operands, projection
#     rebuild, dependent `if`, and (reconfirming the first audit) the explicit
#     error-constructor pattern once reproved. Two are rejected by the frozen
#     script and BOTH are tactic limits, not spec holes, each demonstrated by
#     landing the same impl with a different script: the explicit
#     `Except.error PolyErr.polynomialError` pattern verifies under `simp only
#     [extractSpec]; split <;> simp_all`, and `return Except.ok (extractSpec p q)`
#     — definitionally the frozen body — fails the frozen tail with `No goals to
#     be solved` (the tail has nothing left to do) and verifies under a bare
#     `loom_solve`. A variant may reprove freely, so neither is a defect of the
#     frozen spec.
#
#   * STATEMENT INTEGRITY (attack A), re-derived: all 11 variants are
#     byte-identical to the frozen file everywhere outside the impl region. No
#     obligation header is reformatted, so no weakened hypothesis is hiding in a
#     reformatting.
#
# NOT re-measured, and flagged as the one claim in this manifest resting on
# argument rather than on a build the auditor ran: the REFINEMENT GROUND-TRUTH
# table (which rivals' faithful real patches do and do not pass the F2P). Those
# claims require the instance Docker image, which is outside the spec lane this
# audit ran in. They are internally coherent and the two self-flagged PASS rows
# are the kind of correction a port does not invent, so they are left standing —
# but they are prose, not evidence, and an auditor with the image should re-run
# them.
