"""properties.py — G-PBT falsification battery for sympy__sympy-13480 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region is changed — the consumer spec view
elides that region, so ``markers.same_spec`` holds and the
``prove_correct cothEvalPeriodic`` obligation survives). ``expect="verify"``
passes iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND
does NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  cothEvalPeriodic (x : Int) (m : Int) return (out : Int)
    ensures out = (if primaryEval m = directedInfinity
                   then primaryEval x else siblingEval x)

TWO INPUT binders, both opaque expression handles. ``m`` is the periodic part:
the branch is governed SOLELY by the value obtained by evaluating the function
on ``m`` (``primaryEval m``), compared against the distinguished sentinel
handle. ``x`` is the remainder part: it is what the two branch outputs are
computed from. Three opaque callees carry the behaviour — ``primaryEval`` (the
function under simplification), ``siblingEval`` (the reciprocal-family sibling),
and the sentinel constant ``directedInfinity``; a fourth opaque callee
``cofamilyEval`` (a DISTINCT family function) exists in the frozen axioms region
only to express the wrong-data-source rival. None carries an ``ensures`` — they
are A-referenced free symbols whose only relied-upon property is determinism.

The single load-bearing clause is one equality whose right side is an
if-then-else. It pins THREE independent sub-decisions:

  (discriminator)  the branch is decided by ``primaryEval m`` — the value
                   computed from the PERIODIC part — and by NO OTHER quantity
                   (not ``x``, not a different family function of ``m``);
  (branch->fn)     the sentinel branch applies ``primaryEval`` and the finite
                   branch applies ``siblingEval`` — the mapping is not swapped
                   and not collapsed to a constant;
  (branch->arg)    BOTH branches evaluate their function on the REMAINDER part
                   ``x``, not on the periodic part ``m``. Independent of the
                   other two: an impl can pick the right branch and the right
                   function and still feed it the wrong handle. The audit added
                   the two rivals that pin this arm; see BINDER COVERAGE below.

The discriminating behaviour the public issue reports is the discriminator one:
the reported defect inspects an UNRELATED quantity instead of the value just
computed from the periodic part, so any impl whose branch is decided by a
different value cannot satisfy the clause on the sub-domain where the two
quantities straddle the sentinel differently.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how a witness reaches the post-image.
The result flows through opaque ``primaryEval`` / ``siblingEval`` and the opaque
``directedInfinity`` sentinel, so a ``decide`` on a literal cannot COMPUTE it.
Two facts make the reject lane expressible anyway:

  * A witness states the refutation directly over
    ``NonDetT.run (cothEvalPeriodic …)`` — a ``Prop``, never IR-compiled — which
    reduces cleanly for this straight-line (loop-free) method.
  * Each witness CONDITIONS on the opaque carrier. It hypothesises just enough
    about the opaque terms at a concrete literal input to separate the rival's
    value from the spec's (e.g. ``primaryEval m = directedInfinity`` to select
    the sentinel branch, plus a ``≠`` witnessing that the rival's returned handle
    differs from the spec's there), then concludes the program's output differs
    from the spec's. Against the FROZEN impl the same goal reduces to a residual
    ``≠`` the hypothesis cannot close (gold agrees with the spec at every input),
    so the witness FAILS on gold. Both halves verified with real builds during
    authoring AND independently re-run by the adversarial audit.

  * A witness's hypothesis must be ORIENTED the way the reduced goal leaves it.
    The audit measured the failure mode: stating the separation backwards and
    repairing it with ``fun hh => h2 hh.symm`` makes the GOLD build fail with
    ``Invalid field notation: Type of hh is not known; cannot resolve field
    `symm` `` — a syntactic elaboration error, not a refutation, so the
    gold-side exit code would attest to nothing. Written in the goal's own
    direction, gold instead fails with ``Type mismatch: h2 has type <the
    hypothesised ≠> but is expected to have type False``, which is the semantic
    signal the two-build check is supposed to read.

Every reject witness carries only hypotheses about DISTINCT opaque terms and is
jointly satisfiable (the gate's ``consistency_probe`` cannot derive ``False``
from any of them — checked with real builds during authoring and re-run by the
audit: all 7 probes left an unsolved ``⊢ False`` goal). No
``sorry``/``admit``/``native_decide``/``axiom``.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION (nagini's value-corrupting-rebind supporting case) — has a
    faithful counterpart here as a VALUE rebind, ``value-corrupting-rebind-m``,
    NOT as a permission trick. The nagini note itself records that this instance
    has NO read-only heap input (``x``/``m`` are value ints, no ``Acc(...)``), so
    the mandatory permission-rejection case does not apply; the rebind is kept as
    a supporting rival showing that overwriting the governing input before the
    test cannot vacuously satisfy the clause. On this backend ``x``/``m`` are
    immutable values too, so the rebind is a genuine wrong-data-source impl
    (``let m := x``), refutable at a point where ``m ≠ x`` on the sentinel.
  * PARTIAL-DOMAIN / CONTROL-FLOW — APPLIES, and carries the reject lane. The
    discriminator and branch->output decisions are transparent structure over
    the opaque callees, so a rival right on part of the input space but wrong on
    a sub-region is the natural falsifier.
  * UNGROUNDED-ORACLE ECHO — N/A. The spec carries NO pure helper/oracle: the
    postcondition is stated directly over the opaque callees via the
    if-then-else. There is nothing an impl could echo — "return <oracle>(x, m)"
    is not expressible under this spec — so the harmful echo class is inexpressible
    (mirrors the nagini oracle-grounding note).
  * DIVERGENCE / NON-TERMINATION - INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it; nothing to ship. The frozen
    impl is LOOP-FREE and non-recursive, so there is no control flow here to make
    diverge: a diverging rival has to bring a loop of its own. When it does, the
    semantics refuse it. This bundle sets ``loom.semantics.termination "total"``
    and its only correctness ``open`` is ``open TotalCorrectness DemonicChoice``,
    so a postcondition is claimed of ALL runs and not only of terminating ones.
    An earlier revision of this entry recorded the disposition as
    "setting-dependent" and carried a second branch describing what would happen
    under ``termination "partial"``; THAT BRANCH IS WITHDRAWN, because the setting
    is not unstable and the file has one setting only.

    Both forms of the rival are refused, measured on this cell:

      - the measure-LESS form (splicing ``while true do pure ()`` ahead of the
        body and returning a wrong constant handle) is REJECTED (exit 1) with
        ``error: Decreasing annotations are required in total correctness
        semantics``, raised by the ``decreasing`` elaborator, which reads the
        option;

      - the measure-CARRYING form, which cannot be dismissed as merely missing
        the annotation, is REJECTED on the measure's own descent goal. Loom's
        total loop rule
        (``TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop``,
        ``Loom/MonadAlgebras/NonDetT/Basic.lean:544``) takes
        ``measure : β → Nat`` and emits ``measure b' < measure b`` as
        ``decreasing_<n>``; the ``PartialCorrectness`` twin at :211 takes
        ``measure : β → Option ℕ`` and drops it, and that is the rule this file
        does not use. The ``set_option`` itself opens the total scope
        (``Loom/MonadAlgebras/WP/Options.lean:169-186``:
        ``| `("total") => openScope `TotalCorrectness``), so the two lines cannot
        disagree.

    It is still NOT shippable, for a mechanical reason rather than any spec
    weakness: the diverging rival's module does not elaborate AT ALL, so the
    witness build against the RIVAL also fails (exit 1), carrying the rejection
    plus a residual ``⊢ ¬(NonDetT.run do forIn Lean.Loop.mk … sorry () …) = …``
    where the loop term never reduces. A reject case requires its witness to
    ELABORATE against the rival, and none can when the rival is uncompilable
    rather than merely wrong. So there is no ``expect="reject"`` case to add, and
    the nagini sibling carries no ``diverge-*`` / ``nonterm-*`` case to port, so
    nothing is dropped from the design document here.

WITNESS PLACEMENT / BINDER COVERAGE. Two input binders, ``x`` and ``m``. The
seven reject rivals partition the clause across its THREE sub-decisions and move
BOTH binders: ``x`` across {0,1,2,3,4,6} and ``m`` across {0,1,2,3,5,7}.

  * discriminator (×2) — ``wrong-discriminator-prepatch``,
    ``value-corrupting-rebind-m`` attack ``m``'s role as the branch source;
  * branch->FUNCTION (×3) — ``swapped-returns``, ``constant-always-primary``,
    ``constant-always-sibling`` attack WHICH function each branch applies;
  * branch->ARGUMENT (×2) — ``output-arg-from-periodic-sentinel``,
    ``output-arg-from-periodic-finite`` attack ``x``'s role as the output's data
    source, one per arm.

The last pair was added by the audit, which found the original five all held
``x`` fixed as the output argument and varied only the function applied: a rival
with the correct discriminator and the correct function per branch, but applied
to ``m``, violated no sub-decision any of them probed. Three witnesses now hold
``x ≠ m`` (x=4/m=5, and x=6/m=7 twice) — the points that separate "branch on m"
from "branch on x" and "output of x" from "output of m". No unattacked binder;
no unattacked clause arm.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13480"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The gold impl's CODE block (the five lines strictly
# ---- inside -- impl-start / -- impl-end, after the descriptive comment). It
# ---- lies wholly inside the single impl region and is unique in Solution.lean
# ---- (both facts asserted at load by _swap). Every variant replaces exactly
# ---- this block; the spec, the method signature and the `prove_correct` header
# ---- are untouched, so same_spec holds and the obligation survives (its frozen
# ---- tactic script no longer closes a reshaped impl — which is the point; the
# ---- rejection is attributed to the spec by the witness, not to the broken
# ---- tactic). ---------------------------------------------------------------
_GOLD_CODE = (
    "    let computed := primaryEval m\n"
    "    if computed = directedInfinity then\n"
    "      return primaryEval x\n"
    "    else\n"
    "      return siblingEval x"
)
assert _BASE.count(_GOLD_CODE) == 1, "impl-body anchor drift — re-sync _GOLD_CODE"


def _variant(body):
    return _swap(_BASE, _GOLD_CODE, body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the `ensures` obligation and the frozen
    # `prove_correct … by loom_solve` body; the straight-line branch reshapes
    # leave the returned handle definitionally identical on every input, so
    # `loom_solve` closes unchanged (both verified with real builds).
    # =====================================================================
    {
        "id": "pos-control-demorgan-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Negate the discriminator test and swap the two branch BODIES to match
        # (De-Morgan-equivalent control flow). Still anchored to primaryEval m;
        # returns the identical handle on every input.
        "module": _variant(
            "    let computed := primaryEval m\n"
            "    if computed ≠ directedInfinity then\n"
            "      return siblingEval x\n"
            "    else\n"
            "      return primaryEval x"),
        "rationale": (
            "structurally-different but CORRECT impl: negates the discriminator "
            "test and swaps the two branch BODIES to match (De-Morgan-equivalent "
            "control flow), still anchored to primaryEval m, so out equals the "
            "if-then-else on every input. Straight-line two-way branch — no "
            "induction/lemma — so the frozen `loom_solve` obligation still "
            "discharges. Must verify; if it cannot, the clause is SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-inline-discriminator",
        "kind": "soundness",
        "expect": "verify",
        # Same gold behavior with the discriminator call inlined into the test
        # (no `computed` local). Determinism of the opaque callee makes the
        # inlined `primaryEval m` denote the same value.
        "module": _variant(
            "    if primaryEval m = directedInfinity then\n"
            "      return primaryEval x\n"
            "    else\n"
            "      return siblingEval x"),
        "rationale": (
            "same gold behavior with the discriminator call inlined into the test "
            "(no `computed` temporary). The opaque callee is a deterministic map, "
            "so the inlined primaryEval m denotes the same value and out equals "
            "the if-then-else on every input; the frozen `loom_solve` obligation "
            "discharges. Must verify; if it cannot, the spec pins the temporary "
            "rather than the behavior (SPEC-TOO-STRONG)."),
    },

    # =====================================================================
    # ADMISSIBILITY — this method has no `require` clause, so the classic
    # "a normal input satisfies the precondition" probe has nothing to fail.
    # The analogue on a TOTAL carrier is the obligation being unsatisfiable at
    # an F2P-shaped input, so this case discharges, as an in-region `assert`
    # BEFORE the frozen body runs, that the post-image is actually reachable at
    # a concrete point on BOTH arms: the if-then-else really does reduce to the
    # function on the remainder when the periodic-part evaluation is the
    # sentinel, and to the sibling on the remainder when it is not. An earlier
    # revision omitted this lane, arguing the only forms available here were a
    # `p ∨ ¬p` tautology or an unprovable non-degeneracy claim
    # (`primaryEval x ≠ siblingEval x`, which is indeed unprovable since the
    # opaque callees carry no `ensures`). Both of those are true and both miss
    # the shippable form: the claim below is IMPLICATIONAL, conditioning each
    # arm on its own guard, so it needs no separation between the opaque
    # callees and is not a tautology either.
    #
    # The assert is LIVE, not decoration — verified by a control: the same
    # assert with one arm's conclusion falsified (sentinel guard concluding the
    # sibling) is REJECTED (exit 1), leaving the unsolved goal
    # `⊢ primaryEval 0 = directedInfinity → primaryEval 0 = siblingEval 0`.
    # The frozen `prove_correct … by loom_solve` body is kept VERBATIM (it
    # discharges the added goal unaided), so the obligation is reproven, not
    # retuned.
    # =====================================================================
    {
        "id": "admiss-postimage-reachable-both-arms",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    assert (with_name_prefix `admiss\n"
            "      (primaryEval 0 = directedInfinity →\n"
            "        (if primaryEval 0 = directedInfinity then primaryEval 0 else siblingEval 0)\n"
            "          = primaryEval 0))\n"
            "    assert (with_name_prefix `admiss\n"
            "      (primaryEval 0 ≠ directedInfinity →\n"
            "        (if primaryEval 0 = directedInfinity then primaryEval 0 else siblingEval 0)\n"
            "          = siblingEval 0))\n"
            + _GOLD_CODE),
        "rationale": (
            "the admitted domain is total (no `require`), so the residual "
            "admissibility risk is an UNSATISFIABLE post-image rather than an "
            "over-strong precondition. This discharges, at a concrete "
            "F2P-shaped point and before the frozen body runs, that the "
            "obligation's right side is reachable on BOTH arms: it reduces to "
            "the function on the remainder under the sentinel guard, and to the "
            "sibling on the remainder under its negation. Each arm is "
            "conditioned on its own guard, so the claim needs no separation "
            "between the opaque callees (which carry no `ensures`) and is not a "
            "`p ∨ ¬p` tautology. Must verify; if it cannot, the obligation is "
            "unsatisfiable at that input (PRECOND-TOO-STRONG). Liveness "
            "control: falsifying one arm's conclusion leaves an unsolved goal."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each straight-line (so its `NonDetT.run` term
    # reduces) with a machine-checked refutation witness conditioning on the
    # opaque carrier, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test (test_coth).
    # =====================================================================

    # ---- discriminator: the branch source must be primaryEval m, not an
    # ---- unrelated family function of m (the LITERAL pre-patch bug) ----
    {
        "id": "wrong-discriminator-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch defect: decide the branch on cofamilyEval m — a DISTINCT
        # family function on the periodic part — instead of primaryEval m. This
        # is the wrong-data-source failure the one-token fix repairs. Correct
        # only where cofamilyEval m and primaryEval m straddle the sentinel the
        # same way; wrong where they disagree.
        "module": _variant(
            "    let computed := cofamilyEval m\n"
            "    if computed = directedInfinity then\n"
            "      return primaryEval x\n"
            "    else\n"
            "      return siblingEval x"),
        "refinement": (
            "this is the pre-patch routine: the branch is decided by an unrelated "
            "family function of the periodic part rather than the value just "
            "computed from it. On the reported reproducer the periodic-part "
            "evaluation is the sentinel (so the result must be the function on the "
            "remainder), but the unrelated quantity is finite there, so this impl "
            "takes the other branch and returns the sibling — the wrong value; "
            "test_coth stays RED (the base_commit code in fact NameErrors before "
            "returning). A faithful patch using this data source would NOT resolve."),
        "rationale": (
            "REJECT from the clause: it pins the branch to primaryEval m, and this "
            "impl branches on cofamilyEval m, so the two disagree wherever the two "
            "quantities straddle the sentinel differently. Refuted at x=0, m=0, "
            "where primaryEval 0 is the sentinel (spec -> primaryEval 0) but "
            "cofamilyEval 0 is finite (rival -> siblingEval 0), and the two handles "
            "differ. If it verifies, the spec does not pin the discriminator's "
            "data source (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : primaryEval 0 = directedInfinity)\n"
            "        (h2 : cofamilyEval 0 ≠ directedInfinity)\n"
            "        (h3 : siblingEval 0 ≠ directedInfinity) :\n"
            "    NonDetT.run (cothEvalPeriodic 0 0)\n"
            "      ≠ DivM.res (if primaryEval 0 = directedInfinity then primaryEval 0 else siblingEval 0) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1, h2]\n"
            "  exact h3\n"),
    },

    # ---- discriminator: overwriting the governing input before the test ----
    {
        "id": "value-corrupting-rebind-m",
        "kind": "uniqueness",
        "expect": "reject",
        # The value analogue of a frame mutation: rebind the governing input
        # m := x before computing the discriminator, so the branch is decided by
        # primaryEval x (a wrong data source, keyed to the REMAINDER). The clause
        # is stated over the ORIGINAL m, so the rebind cannot vacuously satisfy
        # it. Correct only where primaryEval x and primaryEval m straddle the
        # sentinel the same way; wrong where they differ (x ≠ m).
        "module": _variant(
            "    let m := x\n"
            "    let computed := primaryEval m\n"
            "    if computed = directedInfinity then\n"
            "      return primaryEval x\n"
            "    else\n"
            "      return siblingEval x"),
        "refinement": (
            "rebinding the governing input to the remainder before the test makes "
            "the branch decided by the remainder's evaluation instead of the "
            "periodic part's — the same wrong data source as the pre-patch bug, "
            "reached a different way. On an input whose periodic part evaluates to "
            "the sentinel while its remainder does not, this returns the sibling "
            "where the result must be the function on the remainder; test_coth "
            "stays RED. A real patch overwriting the periodic part with the "
            "remainder before the test would NOT resolve."),
        "rationale": (
            "REJECT from the clause, which is stated over the ORIGINAL argument m: "
            "rebinding the local m does not change what primaryEval m means in the "
            "postcondition, so the impl effectively branches on primaryEval x and "
            "cannot prove the primaryEval-m-keyed equality. Refuted at x=4, m=5 "
            "(the only witness with x ≠ m, separating 'branch on m' from 'branch "
            "on x'): primaryEval 5 is the sentinel (spec -> primaryEval 4) but "
            "primaryEval 4 is finite (rival -> siblingEval 4), and the two handles "
            "differ. If it verifies, SPEC-TOO-WEAK."),
        "witness": (
            "example (h1 : primaryEval 5 = directedInfinity)\n"
            "        (h2 : primaryEval 4 ≠ directedInfinity)\n"
            "        (h3 : siblingEval 4 ≠ primaryEval 4) :\n"
            "    NonDetT.run (cothEvalPeriodic 4 5)\n"
            "      ≠ DivM.res (if primaryEval 5 = directedInfinity then primaryEval 4 else siblingEval 4) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1, h2]\n"
            "  exact h3\n"),
    },

    # ---- branch->output: the two outputs must not be swapped ----
    {
        "id": "swapped-returns",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the correct discriminator primaryEval m but return the sibling on
        # the sentinel branch and the function on the finite branch — the two
        # outputs swapped. Inverts the branch->output mapping on every input.
        "module": _variant(
            "    let computed := primaryEval m\n"
            "    if computed = directedInfinity then\n"
            "      return siblingEval x\n"
            "    else\n"
            "      return primaryEval x"),
        "refinement": (
            "keeps the correct discriminator but returns the sibling on the "
            "sentinel branch and the function on the finite branch — outputs "
            "swapped. This inverts the result on every input that reaches either "
            "branch, so a reproducer on the sentinel branch (whose result must be "
            "the function on the remainder) comes back as the sibling; test_coth "
            "stays RED. A real patch swapping the two branch returns would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the clause: on the sentinel branch it demands out = "
            "primaryEval x but this returns siblingEval x. Refuted at x=1, m=1, "
            "where primaryEval 1 is the sentinel (spec -> primaryEval 1) but the "
            "rival returns siblingEval 1; the witness hypothesises siblingEval 1 "
            "differs from the sentinel (= the spec's value there). If it verifies, "
            "the branch-to-output mapping is unpinned (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : primaryEval 1 = directedInfinity)\n"
            "        (h2 : siblingEval 1 ≠ directedInfinity) :\n"
            "    NonDetT.run (cothEvalPeriodic 1 1)\n"
            "      ≠ DivM.res (if primaryEval 1 = directedInfinity then primaryEval 1 else siblingEval 1) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- branch->output: the finite branch must yield the sibling ----
    {
        "id": "constant-always-primary",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the discriminator entirely and always return primaryEval x. On
        # the finite branch (where the spec demands the sibling) it returns the
        # function instead. Correct only on the sentinel branch.
        "module": _variant("    return primaryEval x"),
        "refinement": (
            "always returns the function on the remainder, ignoring the "
            "discriminator. On the finite branch (where the result must be the "
            "sibling on the remainder) it returns the function instead, so a "
            "reproducer whose periodic-part evaluation is finite comes back wrong; "
            "test_coth stays RED. A real patch dropping the else branch and always "
            "returning the function would NOT resolve."),
        "rationale": (
            "REJECT from the clause on the finite branch: out must be siblingEval "
            "x but the impl returns primaryEval x. Refuted at x=2, m=2, where "
            "primaryEval 2 is NOT the sentinel (spec -> siblingEval 2) but the "
            "rival returns primaryEval 2, and the two handles differ. If it "
            "verifies, the finite branch is unpinned (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : primaryEval 2 ≠ directedInfinity)\n"
            "        (h2 : primaryEval 2 ≠ siblingEval 2) :\n"
            "    NonDetT.run (cothEvalPeriodic 2 2)\n"
            "      ≠ DivM.res (if primaryEval 2 = directedInfinity then primaryEval 2 else siblingEval 2) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- branch->output: the sentinel branch must yield the function ----
    {
        "id": "constant-always-sibling",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary degenerate rival: always return siblingEval x,
        # ignoring the discriminator. On the sentinel branch (where the spec
        # demands the function) it returns the sibling instead.
        "module": _variant("    return siblingEval x"),
        "refinement": (
            "always returns the sibling on the remainder, ignoring the "
            "discriminator. On the sentinel branch (where the result must be the "
            "function on the remainder) it returns the sibling instead, so a "
            "reproducer whose periodic-part evaluation is the sentinel comes back "
            "wrong; test_coth stays RED. Complementary degenerate rival to "
            "constant-always-primary; a real always-sibling patch would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the clause on the sentinel branch: out must be primaryEval "
            "x but the impl returns siblingEval x. Refuted at x=3, m=3, where "
            "primaryEval 3 is the sentinel (spec -> primaryEval 3 = the sentinel "
            "here) but the rival returns siblingEval 3; the witness hypothesises "
            "siblingEval 3 differs from the sentinel. If it verifies, the sentinel "
            "branch is unpinned (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : primaryEval 3 = directedInfinity)\n"
            "        (h2 : siblingEval 3 ≠ directedInfinity) :\n"
            "    NonDetT.run (cothEvalPeriodic 3 3)\n"
            "      ≠ DivM.res (if primaryEval 3 = directedInfinity then primaryEval 3 else siblingEval 3) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- branch->output: the OUTPUT ARGUMENT must be the remainder part `x`,
    # ---- not the periodic part `m`. Added by the audit: the five rivals above
    # ---- all keep `x` as the output argument and vary only WHICH function is
    # ---- applied (swap / collapse), so none of them pins the output's data
    # ---- source. A rival keeping the correct discriminator AND the correct
    # ---- function per branch, but applying it to `m`, satisfies every
    # ---- sub-decision the battery previously attacked. Both rivals below need
    # ---- x ≠ m to be refutable, so they also broaden the x≠m coverage that
    # ---- rested on value-corrupting-rebind-m alone. -----------------------
    {
        "id": "output-arg-from-periodic-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct discriminator, correct FUNCTION on each branch, but the
        # sentinel branch applies it to the periodic part instead of the
        # remainder. Wrong wherever primaryEval m ≠ primaryEval x.
        "module": _variant(
            "    let computed := primaryEval m\n"
            "    if computed = directedInfinity then\n"
            "      return primaryEval m\n"
            "    else\n"
            "      return siblingEval x"),
        "refinement": (
            "keeps the correct branch source and returns the same FUNCTION the "
            "sentinel branch demands, but evaluates it on the periodic part "
            "instead of the remainder part. The simplified result must be the "
            "function of the REMAINDER; on a reproducer whose periodic-part "
            "evaluation is the sentinel this returns the sentinel itself rather "
            "than the remainder's evaluation, so test_coth stays RED. A real "
            "patch passing the periodic part to the returned call would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the clause: on the sentinel branch it demands out = "
            "primaryEval x, and this impl returns primaryEval m, so the two "
            "disagree wherever those handles differ. Refuted at x=6, m=7 (x ≠ m), "
            "where primaryEval 7 is the sentinel (spec -> primaryEval 6) while "
            "the rival returns primaryEval 7 = the sentinel; the witness "
            "hypothesises the sentinel differs from primaryEval 6. If it "
            "verifies, the output's data source is unpinned (SPEC-TOO-WEAK)."),
        # Orientation matters: the hypothesis is stated in the direction the
        # reduced goal leaves, so gold's failure is a semantic residual against
        # `False` rather than a field/`symm` elaboration error (which would make
        # the gold-side exit code attest to nothing).
        "witness": (
            "example (h1 : primaryEval 7 = directedInfinity)\n"
            "        (h2 : directedInfinity ≠ primaryEval 6) :\n"
            "    NonDetT.run (cothEvalPeriodic 6 7)\n"
            "      ≠ DivM.res (if primaryEval 7 = directedInfinity then primaryEval 6 else siblingEval 6) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },
    {
        "id": "output-arg-from-periodic-finite",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary arm: correct discriminator, correct function, but the
        # FINITE branch applies the sibling to the periodic part.
        "module": _variant(
            "    let computed := primaryEval m\n"
            "    if computed = directedInfinity then\n"
            "      return primaryEval x\n"
            "    else\n"
            "      return siblingEval m"),
        "refinement": (
            "the complementary arm: the finite branch returns the sibling "
            "function evaluated on the periodic part instead of the remainder "
            "part. On a reproducer whose periodic-part evaluation is finite the "
            "result must be the sibling of the REMAINDER, so this returns the "
            "wrong handle and test_coth stays RED. A real patch passing the "
            "periodic part to the sibling call would NOT resolve."),
        "rationale": (
            "REJECT from the clause on the finite branch: out must be siblingEval "
            "x but the impl returns siblingEval m. Refuted at x=6, m=7 (x ≠ m), "
            "where primaryEval 7 is NOT the sentinel (spec -> siblingEval 6) but "
            "the rival returns siblingEval 7, and the witness hypothesises those "
            "two handles differ. Together with "
            "output-arg-from-periodic-sentinel this pins the output ARGUMENT on "
            "both arms. If it verifies, SPEC-TOO-WEAK."),
        "witness": (
            "example (h1 : primaryEval 7 ≠ directedInfinity)\n"
            "        (h2 : siblingEval 7 ≠ siblingEval 6) :\n"
            "    NonDetT.run (cothEvalPeriodic 6 7)\n"
            "      ≠ DivM.res (if primaryEval 7 = directedInfinity then primaryEval 6 else siblingEval 6) := by\n"
            "  unfold cothEvalPeriodic\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus an AXIOM_TESTS lane that
# this gate ignores. Both carriers model the SAME function — the periodic-part
# branch of the simplifier — over opaque handles, so the port is nearly 1:1; the
# only structural difference is that this backend has no precondition and no
# fractional-permission machinery.
#
#   sibling case                     -> here                              status
#   ---------------------------------------------------------------------------
#   pos-control-demorgan-reorder     -> pos-control-demorgan-reorder      PORTED
#   pos-control-inline-discriminator -> pos-control-inline-discriminator  PORTED
#   admiss-empty-precond             -> admiss-postimage-reachable-both-arms
#                                                                          PORTED
#   wrong-discriminator-prepatch     -> wrong-discriminator-prepatch      PORTED
#   swapped-returns                  -> swapped-returns                   PORTED
#   constant-always-primary          -> constant-always-primary          PORTED
#   constant-always-sibling          -> constant-always-sibling          PORTED
#   value-corrupting-rebind-m        -> value-corrupting-rebind-m         PORTED
#   (no sibling case)                -> output-arg-from-periodic-sentinel ADDED
#   (no sibling case)                -> output-arg-from-periodic-finite   ADDED
#
# 5 uniqueness rivals ported + 2 positives ported + the admissibility case
# ported (re-expressed for a total carrier; see the case comment), 0 omitted,
# 2 ADDED by the adversarial audit (the branch->ARGUMENT sub-decision, which the
# nagini sibling does not attack either: its five rivals likewise all keep
# primary(x)/sibling(x) as the output and vary only the function or the branch).
# No case was dropped because its proof/witness was hard; every rival's witness
# was seen to discriminate with real builds.
#
# PORT NOTES (argument unchanged; mechanics re-expressed for the opaque carrier):
#  * wrong-discriminator-prepatch. Nagini expresses the cotm-vs-cothm typo as
#    branching on primary(x) [the remainder] — an unbound-name analogue. This
#    backend cannot host a literally-unbound name, and the FROZEN prepatch models
#    the same failure mode as branching on a DISTINCT family function of the
#    periodic part (cofamilyEval m, the model of cot m), which is what the frozen
#    axioms region declares for exactly this purpose. The rival mirrors the
#    prepatch, and its witness refutes it where cofamilyEval m and primaryEval m
#    straddle the sentinel differently.
#  * value-corrupting-rebind-m. The nagini "mutate the governing input" trick
#    (rebind m := x). On this referentially-transparent backend x/m are immutable
#    values and there is no heap frame, but `let m := x` is still a legal value
#    rebind that makes the branch key on the remainder. It is the sole rival with
#    x ≠ m, so it is the one that separates "branch on m" from "branch on x".
#  * the two positives and the swapped/constant rivals port directly: the branch
#    reshapes preserve the returned handle definitionally (positives verify under
#    the frozen loom_solve), and the wrong reshapes each violate one arm of the
#    if-then-else at a literal input.
#
# OMITTED (0). The admissibility lane is now PORTED as
# `admiss-postimage-reachable-both-arms`; the earlier revision omitted it and
# the reason it gave has been RETRACTED as measurably wrong. That reason ran:
# the only available forms are (a) the dichotomy
# `primaryEval m = directedInfinity ∨ … ≠ …`, which verifies but is a `p ∨ ¬p`
# tautology, and (b) the non-degeneracy claim `primaryEval x ≠ siblingEval x`,
# which is genuinely unprovable (the opaque callees carry no `ensures`, so
# nothing forbids primaryEval = siblingEval). Both halves of that are TRUE and
# both miss a third form the audit built and landed: an IMPLICATIONAL claim that
# conditions each arm on its own guard,
#   primaryEval 0 = directedInfinity → (if … then primaryEval 0 else siblingEval 0)
#                                        = primaryEval 0
# and the complementary arm under the negated guard. That needs no separation
# between the opaque callees, so (b)'s obstacle does not apply, and it is not a
# tautology, so (a)'s does not either. It VERIFIES (exit 0) with the frozen
# `loom_solve` body kept verbatim, and it is LIVE: the same assert with one
# arm's conclusion falsified is REJECTED (exit 1) leaving
# `⊢ primaryEval 0 = directedInfinity → primaryEval 0 = siblingEval 0`.
# So the lane was expressible here all along and its absence was a real gap in
# the PRECOND-TOO-STRONG direction, not a property of the carrier.
#
# NO frame/permission substitute was fabricated (the nagini frame-mutation note
# already records has_readonly_input=false for this instance; the value rebind is
# ported as a supporting uniqueness rival, which is where the nagini battery put
# it). NO divergence case is shipped; see the DIVERGENCE entry in the module
# docstring. That entry used to record the measurement under BOTH termination
# settings, on the belief that this bundle's setting was unstable in the working
# tree; the second branch has been WITHDRAWN. The frozen file sets
# `termination "total"` and opens `TotalCorrectness` only, so the diverging rival
# is REJECTED (measure-less at elaboration, measure-carrying on its own descent
# goal) and the class is closed rather than a frozen-spec hole. It remains
# unshippable because the rejected rival's module is uncompilable, so no witness
# can elaborate against it: a carrier limit, not a spec weakness.
#
# WITNESS DISCRIMINATION (verified during authoring AND independently re-run by
# the audit with real builds — for each of the 7 reject cases: rival exit 0, gold
# exit 1, consistency probe exit 1 (`⊢ False` left unsolved). Every gold-side
# failure was read, and each is a SEMANTIC residual — `Type mismatch: h has type
# <the hypothesised ≠> but is expected to have type False`, i.e. the goal reduced
# to False because gold agrees with the spec there — never an unknown identifier,
# type error, stuck reduction or timeout. Re-checked
# by the gate's two builds per reject case): each witness ELABORATES against its
# straight-line rival (its `NonDetT.run` term reduces under
# `simp [NonDetT.run, pure, …]` to the rival's returned handle, which the
# hypothesis separates from the spec's if-then-else value) and FAILS against the
# frozen solution (whose value equals the spec's, so the residual `≠` cannot be
# closed by the hypothesis). Each witness's hypotheses are about DISTINCT opaque
# terms and are jointly satisfiable — the gate's consistency_probe left an
# unsolved `⊢ False` for every one (checked with a real build). No
# `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# FORGERY CHECK (the gold-side exit code carries information about the CLAIM).
# Every reject case's gold-side failure here is a `Type mismatch … but is
# expected to have type False`, which is an elaboration error rather than a
# plain evaluation, so reading it as "semantic" is not enough on its own. The
# audit ran the two-build flip for ALL SEVEN: each witness was rebuilt with its
# conclusion INVERTED (`≠ DivM.res` -> `= DivM.res`, final `exact hN` dropped so
# the same `simp` closes it) against both impls. Result, uniformly: the flipped
# claim VERIFIES against the frozen solution (exit 0 — `simp` proves gold's
# output equals the spec's if-then-else at that input) and FAILS against the
# rival (exit 1, leaving the concrete residual, e.g.
# `⊢ siblingEval 1 = directedInfinity` for swapped-returns). Both sides invert
# when the claim inverts, so the exit codes track the claim and none of the
# seven is hollow.
#
# SPEC-TOO-WEAK / SPEC-TOO-STRONG probes (audit, beyond the shipped cases).
# Six NEW wrong impls were built against the frozen spec and ALL SIX were
# rejected: branch on siblingEval m; branch on primaryEval x; cofamily on the
# sentinel-branch output; cofamily on the finite-branch output; both branch
# outputs fed the periodic part; and the constant sentinel. No spec hole found.
# Four NEW correct reshapes were built and ALL FOUR verify under the frozen
# `loom_solve`: a single `return` of the if-then-else expression; the same via a
# `let`; a double-negated guard; and both branch values precomputed into locals
# before the test. No faithful correct impl is rejected, so the clause is
# neither too weak nor too strong on the probed surface.
#
# BINDER / CLAUSE COVERAGE. The single clause is attacked by all SEVEN rivals
# across its THREE sub-decisions — the discriminator (wrong family function, and
# the rebind), the branch->FUNCTION mapping (swap, and the two constants), and
# the branch->ARGUMENT mapping (the two output-arg rivals). Both input binders
# move: `x` across {0,1,2,3,4,6}, `m` across {0,1,2,3,5,7}. THREE witnesses hold
# x ≠ m — value-corrupting-rebind-m (x=4/m=5) and both output-arg rivals
# (x=6/m=7) — which are the points that separate "branch on m" from "branch on
# x" and "output of x" from "output of m". No unattacked binder; no unattacked
# clause arm. (An earlier revision of this paragraph still said "five rivals",
# `x` across {0,1,2,3,4}, and called the rebind the SOLE x ≠ m witness; that
# predated the two added output-arg cases and is corrected here.)
#
# AXIOM_TESTS: empty. The four opaque callees (primaryEval/siblingEval/
# cofamilyEval/directedInfinity) carry NO asserted ensures — they are A-referenced
# free symbols whose only relied-upon property is determinism (mapping.md;
# meta.json G-AX status=skip). There is no axiom lane to mirror, and this gate
# ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
