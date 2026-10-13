"""properties.py — G-PBT falsification battery for sympy__sympy-17318 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
each ``prove_correct <name>`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (``matchAddTerms (xs : List Addend) return (out : Outcome)``):
  Decide whether a sum of terms decomposes as ``a + b·√r``, returning one of two
  outcomes — a decomposition is produced (``matched``) or the sum has none
  (``empty``). The sum is abstracted term-by-term to a ``List Addend``, each
  addend carrying three observations: whether its square is rational
  (``sqRat``), whether its square is positive (``sqPos``), and its root-nesting
  depth (``depth``). The decision uses two pure predicates over that carrier:

    allPosRat xs = xs.all (a => a.sqRat && a.sqPos)   every term posit.-rat. sq.
    maxDepth  xs = xs.foldl (max · a.depth) 0         the deepest nesting

  ONE input binder, ``xs``, NO ``require`` clause, and THREE independent
  top-level postcondition clauses that PARTITION the input space:

    (Q1) allPosRat xs = true                 → out = matched   the fast regime
    (Q2) allPosRat xs = false → maxDepth = 0  → out = empty     no decomposition
    (Q3) allPosRat xs = false → maxDepth ≠ 0  → out = matched   general regime

  The three guards are jointly exhaustive and mutually exclusive, so the spec
  pins ``out`` at EVERY input to exactly one of the two outcomes — there is no
  under-specified sub-domain. Within the fast regime the value is produced by a
  subordinate contracted callee ``fastSplit`` (``require allPosRat``,
  ``ensures matched``): the structural decomposition routine the dispatch
  delegates to, defined ONLY on the fast regime's domain. Its obligation
  (``prove_correct fastSplit``) is defended by every variant (kept verbatim) but
  not independently attacked — it is the unchanged callee, not the operation
  under spec; see the ACCOUNTING footer.

COARSE-BUT-SOUND OUTCOME CARRIER — why the value-echo class is vacuous here.
  The nagini sibling pins the fast-path result to an OPAQUE helper output
  (``split_by_radicand_gcd(...)`` with its exact value deliberately unpinned),
  so a wrong impl can be caught ECHOing a literal that is provably ≠ that opaque
  value. On THIS carrier the result is the two-valued ``Outcome``, and the
  behaviour the issue + F2P pin is *which of the two* is produced, never the
  algebraic ``(a, b, r)`` (produced by unchanged code, mapping.md §2). The fast
  regime has exactly ONE correct outcome (``matched``), so returning ``matched``
  on it WITHOUT consulting the callee is not a wrong echo — it is correct, and
  its faithful refined patch resolves (recorded in the bundle's own G-EQ audit).
  There is therefore no wrong-yet-verifying value echo to ship on the fast leg;
  the echo class collapses under carrier narrowing (see the footer). What the
  spec DOES pin — which outcome each regime yields — is attacked directly.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, and
  every modeled operation is CONCRETE (``fastSplit`` is ``return matched``, the
  dispatch is a decidable ``if`` ladder), so ``matchAddTerms`` extracts to a
  computable program whose tester reduces under ``decide`` — the loop-free /
  django-13012 pattern, NOT a conditioning-on-opaque one. Each reject rival
  carries a machine-checked ``matchAddTermsTester <xs> = false`` at ONE concrete
  ``List Addend``, checked in a file whose ``prove_correct`` blocks have been
  stripped so no tactic script can mask the verdict. Both halves were confirmed
  out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
  its rival (the tester ``decide``s to ``false`` — the extracted program's
  outcome violates the postcondition there) and FAILS against the frozen
  solution (``decide`` proves gold's tester ``true``, so ``= false`` is refuted
  — the error printed is verbatim ``Tactic `decide` proved … is false``). No
  witness binds a hypothesis (every input is a decidable literal), so the gate's
  consistency probe is a no-op; no banned token
  (``sorry``/``admit``/``native_decide``/``axiom``).

WITNESS-POINT REALIZABILITY (the discipline an earlier revision of this battery
  got wrong; see the AUDIT footer). A witness point is only worth anything if it
  is the abstraction of an input the modeled operation can actually RECEIVE. Two
  constraints on this carrier are not visible in the ``List Addend`` type and
  must be respected by hand:

    (V1) the modeled surface is reached only for a SUM, and a sum has at least
         TWO terms — so a one-element ``xs`` abstracts nothing reachable;
    (V2) a term whose square is a positive rational and which carries no radical
         (``sqRat ∧ sqPos ∧ depth = 0``) is a plain rational, and a sum of two
         such terms collapses to a single term — so ``xs`` cannot consist
         exclusively of ``depth = 0`` fast-eligible addends. Every realizable
         fast-regime (``allPosRat``) sum therefore has ``maxDepth ≥ 1``.

  Neither is a spec defect: the frozen postcondition is stated over all of
  ``List Addend``, which is SOUND (it constrains more than it must, and G-CONF
  confirms it agrees with the real callee wherever the callee is defined). But a
  reject witness placed at an UNREALIZABLE point discriminates only there, so it
  attests to the spec at an input the operation never sees. Both defects found by
  this audit were exactly that, and both are repaired below.

BINDER / CLAUSE COVERAGE. The single binder ``xs`` is varied across the reject
  witnesses in every ``Addend`` field, at REALIZABLE points only (V1/V2):
    R1 [pos,surd]       sqRat t/t  sqPos t/t  depth 0/1   → Q1 attacked
    R2 [pos,imag]       sqRat t/t  sqPos t/f  depth 0/0   → Q2 attacked (the F2P)
    R3 [pos,imag]       sqRat t/t  sqPos t/f  depth 0/0   → Q2 domain-guard prepatch
    R5 [surd,pos]       sqRat t/t  sqPos t/t  depth 1/0   → Q1 attacked (realizable-only)
    R4 [flat,deep]      sqRat f/f  sqPos f/f  depth 0/2   → Q3 attacked
  ``sqRat`` ranges over true (R1/R2/R3/R5) and false (R4); ``sqPos`` over true
  (R1/R5) and false (R2/R3/R4); ``depth`` over 0, 1 (R1/R5) and 2 (R4). All three
  partition clauses Q1/Q2/Q3 are attacked; pts = 3 distinct realizable input
  points. R2 and R3 SHARE their point deliberately: it is the only realizable
  abstraction on which the loosened prepatch guard differs from ``allPosRat``
  (V2 forces every other such sum to ``maxDepth ≥ 1``, where both guards agree
  on the outcome), and the two rivals fail there for DIFFERENT reasons — R2
  hardwires the wrong outcome, R3 routes the point into the partial callee off
  its domain.

ADVERSARIAL READ of the nagini classes (case-by-case in the footer):
  * FRAME / PERMISSION-MUTATION — VACUOUS. Already recorded vacuous on nagini
    (the input is an immutable sequence carrying no heap permission). Vacuous
    here a fortiori: Velvet is referentially transparent, ``xs`` is an immutable
    value, and this bundle declares NO ``mut`` binder — no read-only cell to
    overwrite, no substitute probe. Not fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — VACUOUS under carrier narrowing (see above). The
    coarse ``Outcome`` has no value to echo wrongly on the single-outcome fast
    regime; the positive controls are cheapest faithful reshapes, not echoes.
  * PARTITION / OUTCOME rivals — the whole reject lane. Each rival sends some
    regime to the wrong outcome (or lets the prepatch weak guard invoke the
    partial callee out of its domain) and is refuted through the corresponding
    partition clause at the smallest point exposing it.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-17318"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen matchAddTerms impl body. It lies
# ---- entirely inside the single matchAddTerms -- impl-start / -- impl-end
# ---- region and is unique in Solution.lean (both asserted at load by _swap),
# ---- so each edit keeps same_spec by construction and leaves both
# ---- `prove_correct` STATEMENTS intact. The subordinate `fastSplit` impl and
# ---- its `prove_correct` are never touched. ----
_IMPL = (
    "    let r ← if allPosRat xs then\n"
    "        fastSplit xs\n"
    "      else\n"
    "        if maxDepth xs = 0 then\n"
    "          pure Outcome.empty\n"
    "        else\n"
    "          pure Outcome.matched\n"
    "    return r"
)
assert _BASE.count(_IMPL) == 1, "matchAddTerms impl region drifted from expected text"

# ---- the frozen matchAddTerms proof block. A tactic body is elided from the
# ---- consumer spec view, so the admissibility case may retune it (to clear an
# ---- extra in-region `assert` goal) without touching the spec or dropping the
# ---- obligation. Unique. ----
_PROVE = "prove_correct matchAddTerms by\n  loom_solve"
assert _BASE.count(_PROVE) == 1, "prove_correct matchAddTerms body drifted"


def _impl(new_impl):
    """Full Solution.lean with ONLY matchAddTerms' impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_and_proof(new_impl, new_proof):
    """Reshape the impl AND retune the (elided) matchAddTerms tactic body."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROVE, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, so a witness reaches
# ---- the postcondition through Velvet's own tester machinery:
# ---- `matchAddTermsTester xs = false` says the extracted program's outcome
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` blocks are stripped, so no tactic script can
# ---- mask the verdict; every modeled op is concrete, so the tester `decide`s.
def _witness(call):
    return ("extract_program_for matchAddTerms\n"
            "prove_precondition_decidable_for matchAddTerms\n"
            "prove_postcondition_decidable_for matchAddTerms\n"
            "derive_tester_for matchAddTerms\n\n"
            f"example : {call} = false := by\n  decide\n")


# concrete Addend fixtures (the three observations the dispatch depends on):
#   _POS  fast-eligible plain rational term (sqRat ∧ sqPos, no nesting)
#   _SURD fast-eligible RADICAL term (sqRat ∧ sqPos, depth 1) — what makes a
#         fast-regime sum realizable at all (V2: a fast-regime sum needs at least
#         one radical term, else it collapses to a single term and is not a sum)
#   _IMAG rational-but-not-positive square (an imaginary-unit-like term)
#   _FLAT non-rational-square atom, no nesting
#   _DEEP non-rational-square term carrying a nested radical
_POS = "{ sqRat := true, sqPos := true, depth := 0 }"
_SURD = "{ sqRat := true, sqPos := true, depth := 1 }"
_IMAG = "{ sqRat := true, sqPos := false, depth := 0 }"
_FLAT = "{ sqRat := false, sqPos := false, depth := 0 }"
_DEEP = "{ sqRat := false, sqPos := false, depth := 2 }"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Port the nagini `pos-control-
    # reorder` ARGUMENT (a faithful, structurally-different correct impl is not
    # rejected) onto this carrier. Both keep the whole dispatch, so the frozen
    # `loom_solve` closes the byte-identical obligation. Verified out-of-band
    # with real builds (EXIT 0).
    # =====================================================================
    {
        "id": "pos-fallback-first",
        "kind": "soundness",
        "expect": "verify",
        # Branch-REORDER: handle the general (non-fast) regime FIRST — invert the
        # top-level guard to `allPosRat xs = false` — and put the fast delegation
        # in the trailing else. Observationally identical to gold on every input,
        # so Q1/Q2/Q3 all still hold and `fastSplit` is still invoked only within
        # its domain.
        "module": _impl(
            "    let r ← if allPosRat xs = false then\n"
            "        if maxDepth xs = 0 then\n"
            "          pure Outcome.empty\n"
            "        else\n"
            "          pure Outcome.matched\n"
            "      else\n"
            "        fastSplit xs\n"
            "    return r"),
        "rationale": "PASS SOURCE = Q1/Q2/Q3. Inverting the top-level guard so the "
                     "general regime is handled first and the fast delegation "
                     "trails in the else yields the SAME outcome as gold on every "
                     "input (the guards partition the space), and still calls the "
                     "partial callee only under `allPosRat`. A structurally-"
                     "different faithful reshape MUST verify; else the "
                     "postcondition over-constrains the executable shape "
                     "(SPEC-TOO-STRONG). Defends all three clauses.",
    },
    {
        "id": "pos-pure-single-return",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different control flow: a single `return` of a pure nested
        # `if`, with NO monadic callee bind at all. Correct because the fast
        # regime's only correct outcome is `matched` (the coarse Outcome carrier),
        # so producing `matched` directly there is observationally identical to
        # delegating to `fastSplit`. Every clause still holds.
        "module": _impl(
            "    return (if allPosRat xs then Outcome.matched\n"
            "            else if maxDepth xs = 0 then Outcome.empty\n"
            "            else Outcome.matched)"),
        "rationale": "PASS SOURCE = Q1/Q2/Q3. Collapsing the dispatch to a single "
                     "pure `return` of a nested `if` produces `matched` on the "
                     "fast regime (its ONLY correct outcome on the two-valued "
                     "Outcome carrier), `empty` on the shallow non-eligible "
                     "domain, and `matched` on the deep regime — identical to gold "
                     "everywhere. A second faithful reshape that MUST verify; else "
                     "SPEC-TOO-STRONG on the executable staging.",
    },

    # =====================================================================
    # ADMISSIBILITY — ported (re-aimed) from nagini `admiss-both-branches`. That
    # probe re-established that the precondition admits a normal F2P-shaped input
    # on both branches. `matchAddTerms` has NO `require`, so the domain is
    # trivially total; the residual admissibility risk this bundle can pin is
    # PARTITION NON-DEGENERACY: the F2P-shaped input (a rational-but-not-positive-
    # square term, no nesting) is admitted and classifies into the `empty` leg
    # (Q2) — so the no-decomposition outcome is genuinely REACHABLE and the
    # partition is not a constant collapse to `matched`. One in-region `assert`
    # (a decidable arithmetic fact about that concrete input) pins it; the impl is
    # otherwise gold, so the method's own obligation still discharges. The proof
    # is retuned only to clear the extra `assert` goal (`decide`), elided from the
    # spec view. The assert is LIVE — a false claim leaves an unsolved goal
    # (verified during authoring). MUST verify, else the empty leg is unreachable
    # (a degenerate spec). Verified out-of-band (EXIT 0).
    # =====================================================================
    {
        "id": "admiss-empty-leg-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_and_proof(
            "    -- admissibility: the F2P-shaped input (a rational-but-not-positive-\n"
            "    -- square term with no nested radical) is admitted and classifies\n"
            "    -- into the no-decomposition leg — not every term has a positive-\n"
            "    -- rational square, and the sum carries no nested radical — so the\n"
            "    -- `empty` outcome is genuinely reachable (the partition is not a\n"
            "    -- constant collapse to `matched`).\n"
            "    assert (with_name_prefix `admiss\n"
            f"      (allPosRat [{_IMAG}] = false ∧\n"
            f"       maxDepth [{_IMAG}] = 0))\n"
            "    let r ← if allPosRat xs then\n"
            "        fastSplit xs\n"
            "      else\n"
            "        if maxDepth xs = 0 then\n"
            "          pure Outcome.empty\n"
            "        else\n"
            "          pure Outcome.matched\n"
            "    return r",
            "prove_correct matchAddTerms by\n  loom_solve\n  all_goals decide"),
        "rationale": "the F2P-shaped input (a term whose square is rational but "
                     "NOT positive, no nesting) is in-domain and lands on the "
                     "`empty` leg (`allPosRat = false`, `maxDepth = 0`), so the "
                     "no-decomposition outcome Q2 is reachable and the partition "
                     "is non-degenerate (not a constant collapse to `matched`). "
                     "The in-region `assert` is a live, decidable claim about that "
                     "point (a false claim leaves an unsolved goal); the impl is "
                     "otherwise gold, so `matchAddTerms`'s own obligation "
                     "discharges too. If it cannot verify ⇒ the empty leg is "
                     "unreachable (a degenerate spec).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at one
    # concrete `List Addend` and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a total
    # reshape whose extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "reject-fast-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Send the FAST regime to the wrong outcome: return `empty` where a
        # decomposition is always produced. Correct on the general regime, wrong
        # on every `allPosRat` sum. (Nagini `depth-marker-on-fastpath`: route a
        # fast-path input to the non-fast answer.)
        "module": _impl(
            "    let r ← if allPosRat xs then\n"
            "        pure Outcome.empty\n"
            "      else\n"
            "        if maxDepth xs = 0 then\n"
            "          pure Outcome.empty\n"
            "        else\n"
            "          pure Outcome.matched\n"
            "    return r"),
        "refinement": "a faithful counterpart returning the no-decomposition "
                      "result on a fast-eligible sum (all terms positive-rational-"
                      "square) would report NO decomposition for sums that DO "
                      "structurally decompose via the gcd split — the fast-split "
                      "regression legs (which exercise genuine decompositions) "
                      "assert a decomposition is produced there, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from Q1 (`allPosRat = true → matched`): the fast "
                     "regime's only correct outcome is `matched`, but the rival "
                     "returns `empty` there. Verifying would be SPEC-TOO-WEAK (the "
                     "fast leg's outcome unpinned). Refuted at [pos,surd] — a plain "
                     "fast-eligible rational plus a fast-eligible RADICAL term "
                     "(`allPosRat = true`, `maxDepth = 1`): gold's tester is `true`, "
                     "the rival's `false`. The point is REALIZABLE (V2): a "
                     "fast-regime sum must carry at least one radical term, so the "
                     "witness is placed where the operation is actually reached. "
                     "Discrimination comes from the `sqRat ∧ sqPos` (fast) "
                     "sub-domain, which only this rival and reject-fast-deep-empty "
                     "abuse.",
        "witness": _witness(f"matchAddTermsTester [{_POS}, {_SURD}]"),
    },
    {
        "id": "reject-shallow-matched",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FAIL_TO_PASS: on the shallow non-eligible domain (`allPosRat =
        # false`, `maxDepth = 0`) the correct outcome is `empty`, but this rival
        # collapses the whole general regime to `matched` — it never reports "no
        # decomposition". (Nagini `partial-domain-no-nomatch`.)
        "module": _impl(
            "    let r ← if allPosRat xs then\n"
            "        fastSplit xs\n"
            "      else\n"
            "        pure Outcome.matched\n"
            "    return r"),
        "refinement": "this is the FAIL_TO_PASS behaviour: on a sum that is NOT "
                      "fast-eligible and carries no nested radical (the "
                      "imaginary-square case the issue reports), the operation "
                      "must report NO decomposition. A faithful counterpart that "
                      "instead reported a decomposition there would return a "
                      "spurious match for exactly the input the failing test pins "
                      "to the no-decomposition result, so it does NOT resolve.",
        "rationale": "REJECT from Q2 (`allPosRat = false → maxDepth = 0 → empty`): "
                     "the shallow non-eligible domain must yield `empty`, but the "
                     "rival yields `matched`. Refuted at [pos,imag] — a fast-"
                     "eligible term plus a rational-but-not-positive-square term, "
                     "no nesting (`allPosRat = false`, `maxDepth = 0`): gold's "
                     "tester is `true`, the rival's `false`. This is the F2P shape "
                     "and the only witness that mixes a positive and a non-positive "
                     "square in one sum.",
        "witness": _witness(f"matchAddTermsTester [{_POS}, {_IMAG}]"),
    },
    {
        "id": "reject-weak-guard-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BUG at the spec level: dispatch to the fast regime under
        # the LOOSER guard `xs.all sqRat` (rational square, dropping the positive
        # requirement) instead of `allPosRat`. On a sum whose term has a rational-
        # but-not-positive square this invokes the partial callee OUTSIDE its
        # domain — the exact over-admission the fix removes.
        "module": _impl(
            "    let r ← if xs.all (fun a => a.sqRat) then\n"
            "        fastSplit xs\n"
            "      else\n"
            "        if maxDepth xs = 0 then\n"
            "          pure Outcome.empty\n"
            "        else\n"
            "          pure Outcome.matched\n"
            "    return r"),
        "refinement": "the loosened guard hands the partial structural-split "
                      "callee a sum outside its domain (a term whose square is "
                      "rational but not positive) — precisely the pre-fix "
                      "over-admission whose downstream effect is the crash the "
                      "FAIL_TO_PASS asserts is gone. A faithful counterpart with "
                      "this weak guard reproduces that crash on the reported "
                      "input, so it does NOT resolve.",
        "rationale": "REJECT from Q2 (`allPosRat = false → maxDepth = 0 → empty`): "
                     "on a rational-but-not-positive-square term the correct "
                     "outcome is `empty`, but the weak guard `xs.all sqRat` sends "
                     "the sum to the fast regime, which is pinned to `matched`. "
                     "(The rival also fails to VERIFY because `fastSplit`'s "
                     "`require allPosRat` is undischargeable off-domain, but the "
                     "witness attributes the rejection to the spec: the extracted "
                     "program's outcome violates Q2.) Refuted at [pos,imag] — a "
                     "fast-eligible rational plus a rational-but-not-positive-square "
                     "term, no nesting (`allPosRat = false`, `maxDepth = 0`): gold's "
                     "tester is `true`, the rival's `false`. This is a REALIZABLE "
                     "two-term point (V1: a sum has ≥ 2 terms), and it is the ONLY "
                     "realizable abstraction where the loosened prepatch guard "
                     "diverges from `allPosRat` — V2 forces every other "
                     "all-rational-square non-positive sum to `maxDepth ≥ 1`, where "
                     "both guards yield `matched` and nothing discriminates. Shares "
                     "its point with reject-shallow-matched by necessity; the two "
                     "rivals fail there for different reasons (that one hardwires "
                     "the wrong outcome, this one routes the point into the partial "
                     "callee off its domain).",
        "witness": _witness(f"matchAddTermsTester [{_POS}, {_IMAG}]"),
    },
    {
        "id": "reject-fast-deep-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The residual Q1 gap the realizability constraint (V2)
        # opens up: a rival that keeps the fast delegation ONLY on the
        # `maxDepth = 0` sub-case of the fast regime — which V2 says is
        # UNREALIZABLE — and returns `empty` on every REALIZABLE fast-regime sum.
        # So it is correct exactly where no input exists and wrong on the entire
        # reachable fast leg, which is the shape a Q1 rival witnessed at an
        # unrealizable point would have failed to distinguish from gold.
        "module": _impl(
            "    let r ← if allPosRat xs then\n"
            "        (if maxDepth xs = 0 then fastSplit xs else pure Outcome.empty)\n"
            "      else\n"
            "        if maxDepth xs = 0 then\n"
            "          pure Outcome.empty\n"
            "        else\n"
            "          pure Outcome.matched\n"
            "    return r"),
        "refinement": "a faithful counterpart delegating to the structural split "
                      "only for a fast-eligible sum carrying NO radical — a sum "
                      "that cannot occur, since such a sum collapses to a single "
                      "term — and reporting no decomposition for every fast-"
                      "eligible sum that DOES carry a radical would report no "
                      "decomposition for every genuine gcd-split input. The "
                      "fast-split regression legs assert a decomposition is "
                      "produced there, so it does NOT resolve.",
        "rationale": "REJECT from Q1 (`allPosRat = true → matched`). This rival is "
                     "the sharpest Q1 probe available: it agrees with gold on the "
                     "fast regime's UNREALIZABLE `maxDepth = 0` sub-case and "
                     "returns `empty` on the whole realizable remainder. Refuted at "
                     "[surd,pos] — a fast-eligible radical term plus a plain "
                     "fast-eligible rational (`allPosRat = true`, `maxDepth = 1`): "
                     "gold's tester is `true`, the rival's `false`. Distinct from "
                     "reject-fast-empty (which collapses the fast leg "
                     "unconditionally) and pinned at a distinct realizable point.",
        "witness": _witness(f"matchAddTermsTester [{_SURD}, {_POS}]"),
    },
    {
        "id": "reject-deep-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the DEEP general regime (the partition clause the two prepatch
        # rivals leave correct): on a non-fast sum that carries a nested radical
        # (`maxDepth ≠ 0`) the correct outcome is `matched`, but this rival
        # collapses the whole general regime to `empty` — reporting no
        # decomposition for a sum that decomposes via the general procedure.
        "module": _impl(
            "    let r ← if allPosRat xs then\n"
            "        fastSplit xs\n"
            "      else\n"
            "        pure Outcome.empty\n"
            "    return r"),
        "refinement": "a faithful counterpart returning the no-decomposition "
                      "result on a non-fast sum that carries a nested radical "
                      "would report NO decomposition for sums the general depth-"
                      "based procedure DOES decompose — the regression legs that "
                      "exercise nested-radical decompositions assert a match is "
                      "produced there, so it does NOT resolve. (Attacks the deep "
                      "regime the FAIL_TO_PASS itself leaves untouched.)",
        "rationale": "REJECT from Q3 (`allPosRat = false → maxDepth ≠ 0 → "
                     "matched`): a non-fast sum carrying a nested radical must "
                     "yield `matched`, but the rival yields `empty`. Verifying "
                     "would be SPEC-TOO-WEAK (the deep leg's outcome unpinned). "
                     "Refuted at [flat,deep] — a non-rational-square atom plus a "
                     "term carrying a depth-2 nested radical (`allPosRat = false`, "
                     "`maxDepth = 2`): gold's tester is `true`, the rival's "
                     "`false`. The only witness with `maxDepth ≠ 0`, so it abuses "
                     "the `depth` observation no other rival's input exercises.",
        "witness": _witness(f"matchAddTermsTester [{_FLAT}, {_DEEP}]"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals) plus 2 AXIOM_TESTS. This bundle
# models only the purely-functional CORE of the changed behaviour — the two-regime
# dispatch deciding whether a sum decomposes (`matchAddTerms`, three partition
# clauses) plus the unchanged partial callee stub (`fastSplit`) — over a
# `List Addend` carrier and a two-valued `Outcome`, where the sibling modeled a
# richer surface (a `PSeq[int]` carrier, an opaque `split_by_radicand_gcd` value
# oracle, a `NoMatch` exception, and a `k` surd-count parameter). Several sibling
# rivals attack machinery this bundle does not model; each is accounted for below.
#
#   sibling case (nagini)      -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder        -> pos-fallback-first
#                                 + pos-pure-single-return         PORTED (x2)
#   admiss-both-branches       -> admiss-empty-leg-reachable       PORTED (re-aimed)
#   frame-mutation             -> (none)                           VACUOUS
#   echo-literal-fastpath      -> (none)                           N/A (carrier)
#   depth-marker-on-fastpath   -> reject-fast-empty                PORTED
#   wrong-k-into-helper        -> (none)                           N/A (no `k`)
#   partial-domain-no-nomatch  -> reject-shallow-matched           PORTED (the F2P)
#   weak-guard-fastpath        -> reject-weak-guard-prepatch       PORTED
#   (no sibling)               -> reject-deep-empty                ADDED
#   (no sibling)               -> reject-fast-deep-empty           ADDED (audit)
#   AXIOM_TESTS (x2)           -> (none)                           DROPPED (G-AX)
#
# PORTED (positives): the sibling ships ONE structurally-different correct impl
#   (branch-reorder, fallback-first). It is carried here by TWO honest reshape
#   positives — pos-fallback-first (invert the top-level guard, general regime
#   first, fast delegation trailing) and pos-pure-single-return (collapse the
#   dispatch to a single pure `if`-ladder `return`, no monadic callee bind at
#   all). Both keep the whole dispatch and both verify (EXIT 0) under the frozen
#   `loom_solve`.
# PORTED-RE-AIMED (admissibility): the sibling asserts the precondition admits an
#   F2P/P2P-shaped input on both branches. `matchAddTerms` has no `require`, so the
#   domain is trivially total; the re-aimed probe pins PARTITION NON-DEGENERACY —
#   the F2P-shaped input is admitted and lands on the `empty` leg, so the
#   no-decomposition outcome is genuinely reachable (not a constant collapse to
#   `matched`). Live in-region `assert`, retuned proof; impl otherwise gold.
#   Verified EXIT 0.
# PORTED (rivals x3):
#   - depth-marker-on-fastpath -> reject-fast-empty: the sibling routes a fast-path
#     input to the non-fast answer (return 1); here the fast regime's only correct
#     outcome is `matched`, so the analogue routes it to `empty`. Attacks Q1.
#   - partial-domain-no-nomatch -> reject-shallow-matched: the sibling never raises
#     NoMatch on the shallow non-eligible domain; here `NoMatch`/`[]` is the `empty`
#     outcome, so the analogue returns `matched` on `allPosRat = false ∧ maxDepth =
#     0`. This IS the FAIL_TO_PASS (the imaginary-square case that must report no
#     decomposition). Attacks Q2.
#   - weak-guard-fastpath -> reject-weak-guard-prepatch: the exact pre-patch bug —
#     dispatch under the looser `xs.all sqRat` guard, invoking the partial callee
#     off its domain. Attacks Q2 (and separately fails to verify on `fastSplit`'s
#     undischargeable `require`, but the witness attributes the rejection to the
#     postcondition). This is the shape `Solution_prepatch.lean` reproduces (G-DIFF).
# ADDED (reject-deep-empty): the sibling's depth path was pinned to a single marker
#   value and had no dedicated rival for it; on THIS carrier the deep general regime
#   is its OWN partition clause Q3 (`allPosRat = false ∧ maxDepth ≠ 0 → matched`),
#   so a rival collapsing that regime to `empty` is a distinct SPEC-TOO-WEAK probe
#   and the ONLY rival that abuses the `depth` observation. Included so every
#   top-level partition clause is attacked.
# ADDED BY THE AUDIT (reject-fast-deep-empty): once witness-point realizability
#   (V1/V2 in the header) is respected, the fast regime splits into a REACHABLE
#   part (`maxDepth ≥ 1`) and an UNREACHABLE one (`maxDepth = 0`), and the ported
#   Q1 rival alone does not distinguish an impl that is wrong only on the reachable
#   part. This rival is exactly that impl: it delegates correctly on the
#   unreachable sub-case and returns `empty` on every realizable fast-regime sum.
#   Added so Q1 is attacked where the operation is actually reached.
# N/A (echo-literal-fastpath): CARRIER NARROWING. The sibling's fast-path
#   postcondition pins the result to an OPAQUE helper value (`split_by_radicand_gcd`,
#   value unpinned), so a literal echo (`return 2`) is provably ≠ it and must
#   reject. On this bundle the fast regime's result is the two-valued `Outcome`,
#   whose only correct fast value is `matched`; producing `matched` without
#   consulting the callee is CORRECT (the bundle's own G-EQ audit records this
#   "ungrounded echo" verifying AND its faithful patch resolving). There is no
#   wrong-yet-verifying value echo to ship — the class collapses. Reported as an
#   omission, NOT fabricated (a fabricated reject here would have no discriminating
#   witness, since the spec satisfies the "echo").
# N/A (wrong-k-into-helper): the sibling passes `k = num_surds + 1` to the helper,
#   violating its `Requires(k == num_surds)`. This carrier's `fastSplit` takes only
#   the sum (`xs : List Addend`); there is no surd-count parameter to corrupt, so
#   the rival has no counterpart. Reported, not fabricated. RE-DERIVED BY THE AUDIT
#   and the verdict stands, with the reason sharpened: the only corruptible argument
#   is the sum itself, and the two candidate corruptions (`fastSplit xs.tail`,
#   `fastSplit []`) are both OBSERVATIONALLY IDENTICAL to gold on this carrier —
#   `fastSplit` returns `matched` for every input in its domain, so passing it a
#   different in-domain sum changes nothing the spec can see. Confirmed with real
#   builds: each fails under the frozen `loom_solve` only because the tactic cannot
#   discharge the callee's `require` for the reshaped argument, and each VERIFIES
#   once the (elided) tactic body is retuned to prove it. They are therefore
#   CORRECT reshapes, not wrong impls — shipping either as a reject case would be
#   exactly the vacuous "reshaped, not wrong" rival the witness rule exists to
#   catch. Correctly omitted.
# VACUOUS (frame-mutation): the sibling records this class as vacuous already (its
#   input carries no heap permission). Vacuous here for the stronger backend reason
#   too: Velvet is referentially transparent and this bundle declares no `mut`
#   binder — `xs` is an immutable value with no heap footprint — so there is no
#   read-only input to overwrite and no substitute probe. Not fabricated.
# DROPPED (AXIOM_TESTS x2): the axiom lane is G-AX's job (axiom_check.py validates
#   the `fastSplit` domain stub == the real structural-split callee: succeeds on the
#   positive-rational-square domain, raises off it) and this gate ignores
#   AXIOM_TESTS regardless.
#
# COVERAGE. The operation-under-spec obligation (`prove_correct matchAddTerms`) is
# defended (two soundness positives + the admissibility case) and attacked (five
# reject rivals). Its three partition clauses are each attacked: Q1 by
# reject-fast-empty and reject-fast-deep-empty, Q2 by reject-shallow-matched (the
# F2P) and reject-weak-guard-prepatch, Q3 by reject-deep-empty. The single binder
# `xs` is varied in every Addend field (sqRat, sqPos each take both truth values
# and depth takes 0, 1 and 2 across the witnesses), at REALIZABLE points only —
# every witness is a two-element sum, since a one-element `xs` abstracts no input
# the operation receives (V1). pts = 3 distinct realizable input points;
# reject-shallow-matched and reject-weak-guard-prepatch share theirs by necessity
# (see V2 in the header) and fail there for different reasons. The subordinate
# `prove_correct fastSplit` obligation is defended by every variant (kept verbatim)
# but not independently attacked — it is the unchanged partial callee, not the
# operation under spec, and a rival reshaping it would attack a callee the fix does
# not change (directive 7 / porting map). A deliberate, reported non-attack.
#
# ===========================================================================
# AUDIT RECORD (independent adversarial re-derivation of the recorded SOUND).
# Every claim below was re-run with the real verifier; exit codes observed, not
# predicted. Two defects were found and repaired, both of the same kind: a reject
# witness pinned at a point that is NOT the abstraction of any input the modeled
# operation can receive, so its discrimination attested to the spec somewhere the
# operation is never reached.
#
#   DEFECT 1 (reject-fast-empty). Witness was at [pos,pos] — two fast-eligible
#     terms with no radical. Unrealizable (V2): each such term is a plain
#     rational and a sum of two rationals collapses to a single term, so no sum
#     abstracts to it. REPAIRED to [pos,surd] (`maxDepth = 1`), the realizable
#     fast-regime shape. Rebuilt: rival EXIT 0, gold EXIT 1 with the semantic
#     refutation ``Tactic `decide` proved … is false``.
#   DEFECT 2 (reject-weak-guard-prepatch). Witness was at [imag] — a ONE-element
#     sum. Unrealizable (V1): the modeled surface is reached only for a sum, which
#     has ≥ 2 terms. REPAIRED to [pos,imag], the realizable two-term abstraction
#     and the only one on which the loosened guard diverges from `allPosRat`.
#     Rebuilt: rival EXIT 0, gold EXIT 1, same semantic refutation.
#   ADDED reject-fast-deep-empty to attack Q1 on the realizable fast regime (see
#     above). Rival EXIT 0 / gold EXIT 1, semantic refutation.
#
# ATTACK A (statement integrity). Every case's module was diffed against the
#   frozen file with the impl regions elided: all seven pre-existing cases were
#   byte-identical outside the impl region except admiss-empty-leg-reachable,
#   whose only delta is the (spec-elided) tactic line `all_goals decide`. No
#   weakened hypothesis, no reformatted statement.
# ATTACK D (SPEC-TOO-WEAK). Five NEW wrong impls built and checked against the
#   frozen spec: fast-regime-deep-empty, an `any`-instead-of-`all` guard, a
#   head-depth-instead-of-max guard, an empty-list special case, and a
#   positivity-only guard (the mirror of the ported rival, dropping rationality
#   rather than positivity). ALL FIVE were REJECTED (EXIT 1), each with a witness
#   that discriminates against gold. No spec hole found; the three partition
#   clauses pin `out` at every point of `List Addend`, including the degenerate
#   empty list (`allPosRat [] = true`, so Q1 forces `matched` there).
# ATTACK E (SPEC-TOO-STRONG). Five NEW correct reshapes: depth-dispatched-first,
#   a commuted guard conjunction, early returns, a Bool-negation guard, and a
#   fast regime split into two in-domain delegations. Four verify under the
#   FROZEN tactic body (EXIT 0). The commuted-guard reshape needs a retuned
#   tactic body (the frozen `loom_solve` leaves `allPosRat xs = true` from
#   `xs.all (sqPos && sqRat)`); it VERIFIES once the elided tactic body is
#   retuned, so this is a tactic-shape sensitivity, NOT a soundness hole in the
#   spec. Confirmed with a real build.
# ADMISSIBILITY LIVENESS. The `assert` in admiss-empty-leg-reachable is LIVE:
#   negating its claim (`allPosRat [imag] = true`) makes the build FAIL (EXIT 1)
#   with `decide` reporting the proposition false. And the retuned tactic body is
#   not an escape hatch: appending `all_goals decide` to a WRONG impl does not
#   rescue it (EXIT 1). So the case neither restates a triviality nor neuters the
#   obligation.
# REALIZABILITY GROUND TRUTH. The V1/V2 constraints and the fixture bindings were
#   checked by running the real post-patch routine at the pinned base commit: the
#   F2P input abstracts to exactly [pos,imag] (its non-rational-square term has
#   nesting depth 0, being an atom) and yields the no-decomposition outcome, while
#   every realizable fast-regime sum tested carries a radical and yields a
#   decomposition. The `depth`-2 fixture [flat,deep] is realizable and yields a
#   decomposition, matching Q3.
# NOTE FOR ESCALATION (documentation only, NOT a defect in this battery or the
#   frozen spec). The recorded G-PANEL-2 narration asserts that the modeled
#   routine yields a decomposition for the issue's discriminating input, on the
#   ground that that input's non-rational-square term has root-nesting depth 1.
#   Re-run against the real post-patch routine, that term is an atom, so its depth
#   is 0, and the routine yields the NO-decomposition outcome there — which is
#   what the F2P test asserts and what the frozen spec predicts via Q2. So the
#   panel reached the right verdict (spec agrees with the repo) through a wrong
#   intermediate fact. The Lean spec is right and this battery is consistent with
#   it; only that panel sentence is wrong, and it sits in a gate record this lane
#   may not edit — hence a note, not a fix.
AXIOM_TESTS = []
