"""properties.py — G-PBT falsification battery for sympy__sympy-23413 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region is changed — the consumer spec view
elides that region, so ``markers.same_spec`` holds and the
``prove_correct hermiteNormalForm`` obligation survives). ``expect="verify"``
passes iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND
does NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  hermiteNormalForm (A) (numRows) (numCols) return (out : Mat)
    ensures out = hnfResult numCols numRows A

THREE INPUT binders. ``A : Mat`` is the OPAQUE matrix carrier (the datum the
reduction routes, never inspected); ``numRows`` and ``numCols`` are transparent
``Nat`` row/column counts. The single load-bearing clause pins ``out`` to
``hnfResult numCols numRows A``, which is the composition

    hnfResult nc nr A = let p := reduceRows nc nr A nc; slice p.1 p.2

of two structural decisions over the opaque callees ``stepRow`` (per-row
reduction) and ``slice`` (final column selection):

  (row-count)  reduce over ALL ``nr`` eligible rows from the bottom up, starting
               the pivot-count ``k`` at ``nc`` — NOT a truncated ``min(nr,nc)``
               window and NOT one row short;
  (early-stop) ``reduceRows`` stops as soon as ``k`` reaches 0 (every column has
               a pivot), which is what keeps ``k`` from over-decrementing on a
               tall matrix — the ``k > 0`` half of the loop guard mirrors it;
  (selection)  the kept columns are exactly those from the FINAL threaded ``k``
               (``slice p.1 p.2``), not a fixed column offset.

The discriminating behaviour the public issue reports is the row-count one: a
pivot in a TOP row of a tall matrix (more rows than columns) must still be
counted, so the loop must run over every row, not a ``min(m, n)`` prefix.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how a witness reaches the post-image.
The result flows through the opaque ``slice`` / ``stepRow`` (via ``reduceRows``),
so a ``decide`` on a literal cannot COMPUTE it. Two facts make the reject lane
expressible anyway:

  * ``extract_program_for hermiteNormalForm`` is unavailable here — the method
    is ``noncomputable`` (its callees are opaque), so the extractor's generated
    ``def`` fails the IR-compile check. A witness therefore states the refutation
    directly over ``NonDetT.run (hermiteNormalForm …)`` — a ``Prop``, never
    IR-compiled — which reduces cleanly for a straight-line (loop-free) rival.
  * Each rival is written LOOP-FREE, computing its (wrong) matrix directly from
    the pure spec helpers (``reduceRows`` / ``slice`` / ``hnfResult``) rather
    than from a ``while`` loop. So ``NonDetT.run (rival …)`` reduces under
    ``simp [NonDetT.run, pure]`` to the rival's straight-line value, and the
    witness then CONDITIONS on the opaque carrier: it hypothesises that the
    rival's value differs from the spec's value at the probed point (a ``≠``
    about opaque ``slice``/``reduceRows`` terms), and concludes the program's
    output differs from the spec's.

WHY THE FROZEN IMPL CANNOT BE THE WITNESS SUBJECT HERE, AND WHAT IS USED INSTEAD
(audit finding, machine-measured — read this before editing a witness).
Against the FROZEN impl the witness's goal does not reduce: the ``mut``/``while``
desugaring stays a ``forIn Lean.Loop.mk …`` term under ``NonDetT.run``, so the
build fails with a ``Type mismatch: After simplification, term heq has type
(NonDetT.run do let r ← forIn …) = … but is expected to have type …``. That is a
SYNTACTIC non-reduction, not a semantic refutation — gold fails here because it
is LOOPY, not because it is right. Consequence, verified with real builds: a
witness of this shape aimed at a *correct* loop-free rival (one that returns
``slice (reduceRows numCols numRows A numCols).1 … .2``, i.e. ``hnfResult``
unfolded) ALSO passes both halves — rival exit 0, gold exit 1 — because the
frozen tactic script cannot close that reshape either. So the two-build check
against gold cannot separate WRONG from merely RESHAPED on this carrier.

An earlier revision of this manifest claimed the gate's third build, the
``consistency_probe``, closed that gap provided both sides of the ``≠`` were
written in the same UNFOLDED vocabulary, so that a definitionally-equal impl
degenerates to ``X ≠ X`` and ``simp_all`` derives ``False``. THAT CLAIM IS FALSE
AND IS RETRACTED. It holds only for the one forgery whose two sides are
SYNTACTICALLY identical. Measured with real builds: a correct rival that
special-cases the no-column input (``if numCols = 0 then return slice A 0``) is
refuted by a witness whose hypothesis is ``slice A 0 ≠ slice (reduceRows 0 2 A
0).1 (reduceRows 0 2 A 0).2`` — both sides unfolded, not syntactically equal, yet
DEFINITIONALLY equal (``rfl`` proves the equation, exit 0). That forgery cleared
all three of the gate's builds — rival 0, gold 1, probe 1 — because ``simp_all``
does not unfold ``reduceRows`` at a ``Nat`` literal. The unfolded-vocabulary rule
is therefore necessary but NOT sufficient, and the probe is not the load-bearing
check.

What IS load-bearing is the ``witness_reference`` every reject case now carries:
``_REFERENCE``, a loop-free impl of this same frozen spec that the verifier
ACCEPTS, which the gate substitutes for gold as the second build's subject. Being
loop-free it REDUCES, so its exit code tracks the claim; being verified it cannot
violate its own spec, so a genuine refutation must still fail against it.
Measured: against ``_REFERENCE`` all five witnesses below fail with ``term heq has
type True`` — ``simp`` PROVED the equation for a correct impl and could not for
the rival, which is a semantic refutation of the concrete claim — while the
correct-reshape forgery ELABORATES there (exit 0), so the gate records it as
``witness-vacuous`` and the forgery is caught. The conclusion is transported to
the ``hnfResult`` form by ``simpa [hnfResult] using heq``.

Every reject witness carries at most ONE hypothesis, quantified over an ABSTRACT
``A : Mat`` (so the opaque carrier binder genuinely varies), and is jointly
satisfiable: for each one, the equality it negates was re-checked by the audit
against SEVEN tactics (``rfl``, ``simp [reduceRows]``, ``simp [hnfResult,
reduceRows, reduceRows_succ, reduceRows_zero]``, ``grind``, ``decide``,
``simp_all``, ``simp <;> grind``) and none proves it (all exit 1), so the two
sides are not definitionally equal and the refuted input exists. That check is
what attack C asks for and it is the reason these five differ from the forgery
above, whose equation ``rfl`` closes outright. No
``sorry``/``admit``/``native_decide``/``axiom``.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION (nagini's mandatory ``frame-mut-write-found``) — VACUOUS here.
    That class exists because the nagini input ``found`` carries a fractional
    heap permission an impl can overwrite (a value-no-op write only a permission
    system, not the value abstraction, rejects). This backend is referentially
    transparent and the method declares NO ``mut`` binder on an input: ``A``,
    ``numRows``, ``numCols`` are immutable values, there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe.
    Not fabricated; see the accounting block.
  * PARTIAL-DOMAIN / CONTROL-FLOW — APPLIES, and carries the reject lane. The
    row-count, early-stop and selection decisions are all transparent
    combinations of the opaque callees, so a rival right on part of the input
    space but diverging on a sub-region is the natural falsifier.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. ``hnfResult`` is a total
    ``def`` written directly over the transparent loop structure and the opaque
    callees; it is not an opaque answer-key the impl could echo without doing the
    work (the impl must reproduce the row iteration, the early stop and the final
    slice). The ``axioms`` region declares ``stepRow``/``slice`` as opaque with
    NO ``ensures`` — an A-reference validated by G-AX (mapping.md §3), not a
    consumed contract to attack. Honest positive controls stand in.

WITNESS PLACEMENT / BINDER COVERAGE. Three input binders ``A``, ``numRows``,
``numCols``. The five reject rivals partition the single clause across its
sub-decisions (row-count ×2, early-stop, selection, and the opaque-argument
abuse) and move the transparent binders: ``numRows`` across {3, 2}, ``numCols``
across {1, 2}. ``A`` is not pinned to ``matDefault`` in any witness: every one
QUANTIFIES over an abstract ``A : Mat``, which both moves the opaque binder off
the single closed ``Mat`` term and is what lets the consistency probe see the
definitional (in)equality — see the CARRIER NOTE. ``matDefault`` still appears on
one side of the ``weak-ignores-input-matrix`` hypothesis, because that rival's
whole defect is substituting the default for the caller's matrix.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23413"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Both lie wholly inside the single -- impl-start /
# ---- -- impl-end region and are unique in Solution.lean (both facts asserted at
# ---- load by _swap). The reject rivals replace the WHOLE body; the positive
# ---- controls reshape only the loop body's inner lines. ----------------------

# The whole gold impl body (text strictly between the marker lines). Replaced
# wholesale by the loop-free reject rivals, whose extracted `NonDetT.run` term
# reduces so their witnesses can condition on the opaque carrier.
_IMPL_BODY = (
    "    let mut mat : Mat := A\n"
    "    let mut k := numCols\n"
    "    let mut rowsLeft := numRows\n"
    "    while rowsLeft > 0 ∧ k > 0\n"
    "      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows\n"
    "      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k\n"
    "      done_with rowsLeft = 0 ∨ k = 0\n"
    "      decreasing rowsLeft\n"
    "    do\n"
    "      let p := stepRow numCols mat k (rowsLeft - 1)\n"
    "      mat := p.1\n"
    "      k := p.2\n"
    "      rowsLeft := rowsLeft - 1\n"
    "    return slice mat k"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

# The four loop-body lines that step one row then decrement the row counter. The
# positive controls reshape ONLY these — a data-flow reshape that leaves the
# accumulated `mat`/`k`/`rowsLeft` definitionally identical, so `loom_solve`
# leaves the same single loop-body goal and the frozen tactic script closes it.
_INNER = (
    "      let p := stepRow numCols mat k (rowsLeft - 1)\n"
    "      mat := p.1\n"
    "      k := p.2\n"
    "      rowsLeft := rowsLeft - 1"
)
assert _BASE.count(_INNER) == 1, "inner-line anchor drift — re-sync _INNER"

# The frozen tactic script, verbatim. Swapped only by `_REFERENCE` below (which
# needs a proof matching its own loop-free shape) and by the admissibility
# positive (which prepends a `have` and then re-emits this tail unchanged).
_GOLD_PROOF = (
    "prove_correct hermiteNormalForm by\n"
    "  loom_solve\n"
    "  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]\n"
    "    assumption\n"
    "  · simp only [hnfResult]\n"
    "    have hinv : reduceRows numCols numRows A numCols = "
    "reduceRows numCols rowsLeft mat k := by\n"
    "      assumption\n"
    "    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]\n"
    "    simp_all"
)
assert _BASE.count(_GOLD_PROOF) == 1, "proof anchor drift — re-sync _GOLD_PROOF"


def _rival(body):
    """`_BASE` with the whole gold impl body replaced by a loop-free `body`. The
    spec, the method signature and the `prove_correct` header are untouched, so
    same_spec holds and the obligation survives (its frozen tactic script no
    longer closes the reshaped impl — which is the point; the rejection is
    attributed to the spec by the witness, not to the broken tactic)."""
    return _swap(_BASE, _IMPL_BODY, body)


# ---- witness preamble. A witness reaches the post-image directly through
# ---- `NonDetT.run (hermiteNormalForm …)` (a Prop) rather than through the
# ---- `extract_program_for` extractor, which is unavailable here (the method is
# ---- noncomputable over opaque callees, so the generated Exec def fails the
# ---- IR-compile check). Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can interfere.


# ---- THE WITNESS SUBJECT (`witness_reference` on every reject case).
#
# The frozen impl cannot serve as the second build's subject on this carrier, and
# this was MEASURED, not argued (audit, real builds — the numbers are in the
# WITNESS DISCRIMINATION block below). Gold keeps the `mut`/`while` loop, whose
# desugaring stays an un-normalised `forIn Lean.Loop.mk …` term under
# `NonDetT.run`, so no claim about the post-image reduces there: gold's build
# fails for EVERY claim regardless of truth, and its exit code carries no
# information about what the witness asserts.
#
# So each reject case names this impl as its `witness_reference` instead. It is a
# LOOP-FREE impl of the same frozen spec that the verifier ACCEPTS (checked by
# the gate: `_reference_ok` requires it to share the spec view and to verify), so
# it cannot violate its own spec and a genuine refutation must still fail against
# it — while, being loop-free, it REDUCES, so the failure tracks the claim. What
# that buys, measured: against this subject each witness fails with `term heq has
# type True` — `simp` PROVED the equation for a correct impl and could not for the
# rival — which is a semantic refutation of the concrete claim rather than a
# syntactic non-reduction.
_REFERENCE = _swap(
    _swap(_BASE, _IMPL_BODY,
          "    -- loop-free: the row reduction and the pivot-column selection\n"
          "    -- stated directly over the pure helpers, no accumulator loop\n"
          "    let p := reduceRows numCols numRows A numCols\n"
          "    return slice p.1 p.2"),
    _GOLD_PROOF,
    "prove_correct hermiteNormalForm by\n  loom_solve\n  simp [hnfResult]")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the `ensures out = hnfResult …` obligation and
    # the frozen tactic body, reshaping only the loop-body data flow so `mat`,
    # `k` and `rowsLeft` are definitionally unchanged and `loom_solve` leaves the
    # identical single loop-body goal.
    # =====================================================================
    {
        "id": "pos-control-named-step",
        "kind": "soundness",
        "expect": "verify",
        # Name the per-row reduction result in a typed local `sr` before
        # projecting it, instead of the anonymous `p`. The three mutable updates
        # read the same components, so `mat`/`k`/`rowsLeft` are definitionally
        # identical and the frozen proof closes unchanged.
        "module": _swap(
            _BASE, _INNER,
            "      let sr : Mat × Nat := stepRow numCols mat k (rowsLeft - 1)\n"
            "      mat := sr.1\n"
            "      k := sr.2\n"
            "      rowsLeft := rowsLeft - 1"),
        "rationale": (
            "naming the per-row reduction result in a typed local before "
            "projecting it leaves the accumulated `mat`/`k`/`rowsLeft` "
            "definitionally identical, so `out = hnfResult numCols numRows A` "
            "still holds on the whole domain; the loop, invariants and frozen "
            "proof script are untouched. A correct reshape must verify (else "
            "SPEC-TOO-STRONG on the shape of the reduction step)."),
    },
    {
        "id": "pos-control-hoisted-index",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the processed row index into a local `i := rowsLeft - 1`, feed it
        # to the reduction, and set `rowsLeft := i`. Same forward-count-down
        # direction, same values threaded; the frozen tactic body closes.
        "module": _swap(
            _BASE, _INNER,
            "      let i := rowsLeft - 1\n"
            "      let p := stepRow numCols mat k i\n"
            "      mat := p.1\n"
            "      k := p.2\n"
            "      rowsLeft := i"),
        "rationale": (
            "hoisting the processed row index into a local `i := rowsLeft - 1` "
            "(so the reduction and the counter decrement read one shared value) "
            "computes the identical `mat`/`k`/`rowsLeft` on every iteration, so "
            "`out = hnfResult numCols numRows A` still holds; a correct reshape "
            "must verify."),
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the obligation must be SATISFIABLE,
    # and non-degenerately so, at exactly an F2P-shaped input. The frozen method
    # carries no `require`, so the nagini "a normal input meets the precondition"
    # probe has no analogue; the residual risk on a total carrier is the
    # POST-IMAGE being unsatisfiable or degenerate at the shape of input the
    # failing scenario drives. Discharged by evaluation as a `have` ahead of the
    # frozen obligation, which then closes verbatim (the frozen tactic tail is
    # re-emitted unchanged), so this tests the post-image WITHOUT weakening
    # anything. Added by audit: the port recorded this lane as inapplicable on
    # the strength of "there is no precondition", which is not the question.
    # =====================================================================
    {
        "id": "admiss-tall-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_PROOF,
            "prove_correct hermiteNormalForm by\n"
            "  have hAdm :\n"
            "      (∀ a : Mat,\n"
            "        hnfResult 1 3 a =\n"
            "            (let p := stepRow 1 a 1 2\n"
            "             if p.2 = 0 then slice p.1 p.2\n"
            "             else\n"
            "               let q := stepRow 1 p.1 p.2 1\n"
            "               if q.2 = 0 then slice q.1 q.2\n"
            "               else slice (stepRow 1 q.1 q.2 0).1"
            " (stepRow 1 q.1 q.2 0).2)\n"
            "          ∧ hnfResult 2 0 a = slice a 2\n"
            "          ∧ hnfResult 0 3 a = slice a 0) := by\n"
            "    refine fun a => ⟨by grind [hnfResult], rfl, rfl⟩\n"
            "  clear hAdm\n" + _GOLD_PROOF[len("prove_correct hermiteNormalForm by\n"):]),
        "rationale": (
            "PRECOND-TOO-STRONG in the only form a total domain admits: the "
            "obligation `out = hnfResult numCols numRows A` must be JOINTLY "
            "SATISFIABLE, and non-degenerate, at an F2P-shaped input — the TALL "
            "matrix (numRows=3 > numCols=1) whose top-row pivot is the reported "
            "behaviour. The first conjunct pins the post-image there to the "
            "three-row bottom-up reduction WITH the early stop, row indices 2, 1, "
            "0 in that order and the pivot count seeded at numCols; it is proven "
            "by evaluation over an ARBITRARY opaque `a : Mat`, so nothing is "
            "assumed about a particular matrix. The other two conjuncts pin the "
            "degenerate boundaries (no eligible rows: the reduction is a no-op and "
            "the selection starts at numCols; no columns: the k=0 guard stops "
            "immediately at offset 0). If the post-image could not be discharged "
            "at these inputs the modeled domain would exclude a legitimate one. "
            "LIVENESS measured with four negative controls, each falsifying one "
            "clause and each FAILING to build (exit 1): row order top-down "
            "instead of bottom-up (`grind` failed), the early stop dropped so all "
            "three rows reduce unconditionally (`grind` failed), the pivot count "
            "seeded at 0 rather than numCols (application type mismatch on `rfl`), "
            "and the zero-column selection offset moved off 0 (likewise). So the "
            "`have` is not a tautology the tactic would close regardless."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each LOOP-FREE (so its `NonDetT.run` term reduces)
    # with a machine-checked refutation witness conditioning on the opaque
    # carrier, and the refinement argument for why its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================

    # ---- row-count: reduce over ALL rows, not a min(nr,nc) window ----
    {
        "id": "weak-min-rows-window",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch defect: cap the reduction at min(numRows, numCols) rows,
        # so on a tall matrix (numRows > numCols) the top rows are never reduced
        # and a pivot there is undercounted. Correct when numRows <= numCols;
        # wrong on the tall-matrix sub-domain the issue reports.
        "module": _rival(
            "    -- reduce over only min(numRows, numCols) rows\n"
            "    let rows := if numCols < numRows then numCols else numRows\n"
            "    let p := reduceRows numCols rows A numCols\n"
            "    return slice p.1 p.2"),
        "refinement": (
            "this is the pre-patch routine (a min(m, n) row window). On a matrix "
            "with more rows than columns it never reduces the top rows, so a "
            "pivot living there is dropped and one column too few is retained — "
            "the exact reported defect (a rank-deficient result that removes a "
            "row). The failing test asserts the full retained submatrix for such "
            "a tall matrix, which the truncated window does not produce, so it "
            "stays RED. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = hnfResult numCols numRows A`: `hnfResult` reduces "
            "over ALL numRows rows, and this impl reduces over only "
            "min(numRows, numCols), so the two disagree whenever numRows > "
            "numCols. Refuted at numRows=3, numCols=1 (a tall matrix), where the "
            "window covers 1 row but the spec covers 3; the witness hypothesises "
            "the 1-row window reduction differs from the 3-row full reduction "
            "there, at an ABSTRACT A. Both sides of the `≠` are written unfolded "
            "(`slice (reduceRows …).1 … .2`), so a definitionally-equal impl would "
            "make the hypothesis `X ≠ X` and be caught by the consistency probe; "
            "here the two sides differ in the row count and the probe confirms the "
            "hypothesis is satisfiable."),
        "witness_reference": _REFERENCE,
        "witness": (
            "example (A : Mat) (h : slice (reduceRows 1 1 A 1).1 (reduceRows 1 1 A 1).2\n"
            "      ≠ slice (reduceRows 1 3 A 1).1 (reduceRows 1 3 A 1).2) :\n"
            "    NonDetT.run (hermiteNormalForm A 3 1) ≠ DivM.res (hnfResult 1 3 A) := by\n"
            "  unfold hermiteNormalForm\n"
            "  simp [NonDetT.run, pure]\n"
            "  intro heq\n"
            "  exact h (by simpa [hnfResult] using heq)\n"),
    },

    # ---- row-count, tail sub-domain: the LAST eligible row must be reduced ----
    {
        "id": "weak-drops-one-row",
        "kind": "uniqueness",
        "expect": "reject",
        # Reduce over one FEWER row (numRows - 1), so the top-most eligible row is
        # never processed. Correct on any matrix whose top row contributes no
        # pivot; wrong whenever that row would have. A tail-of-iteration
        # off-by-one the min-window rival does not exercise.
        "module": _rival(
            "    -- reduce over one fewer row (skip the top eligible row)\n"
            "    let p := reduceRows numCols (numRows - 1) A numCols\n"
            "    return slice p.1 p.2"),
        "refinement": (
            "reducing over numRows - 1 rows omits the top-most row from the "
            "reduction. A faithful counterpart that started the row range one "
            "step short would leave that row's pivot unplaced, so a matrix whose "
            "top row carries the distinguishing pivot comes back with the wrong "
            "retained columns. The failing scenario includes exactly such a "
            "top-row-pivot matrix, so its assertion stays RED. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = hnfResult numCols numRows A`: `hnfResult` reduces "
            "over numRows rows, this impl over numRows - 1, so the two disagree "
            "whenever the omitted top row would change the reduction. Refuted at "
            "numRows=2, numCols=2 (the impl reduces 1 row where the spec reduces "
            "2) at an ABSTRACT A; the witness hypothesises the short reduction "
            "differs from the full one there — the tail sub-domain no other rival "
            "probes. Both sides of the `≠` are unfolded so the consistency probe "
            "can see they are not definitionally equal (they differ in rowsLeft)."),
        "witness_reference": _REFERENCE,
        "witness": (
            "example (A : Mat) (h : slice (reduceRows 2 1 A 2).1 (reduceRows 2 1 A 2).2\n"
            "      ≠ slice (reduceRows 2 2 A 2).1 (reduceRows 2 2 A 2).2) :\n"
            "    NonDetT.run (hermiteNormalForm A 2 2) ≠ DivM.res (hnfResult 2 2 A) := by\n"
            "  unfold hermiteNormalForm\n"
            "  simp [NonDetT.run, pure]\n"
            "  intro heq\n"
            "  exact h (by simpa [hnfResult] using heq)\n"),
    },

    # ---- selection / early-stop: keep the columns from the FINAL threaded k ----
    {
        "id": "weak-wrong-selection-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Reduce over all rows correctly, but select columns from a FIXED offset
        # 0 instead of the final threaded pivot count. This is the velvet
        # re-expression of the nagini no-clamp rival: the returned pivot count is
        # what decides which columns survive, and ignoring it keeps every column
        # (never dropping the rank-deficient ones). Correct only when the final
        # k happens to be 0; wrong otherwise.
        "module": _rival(
            "    -- reduce over all rows, but keep every column (ignore the final\n"
            "    -- pivot count that selects the retained columns)\n"
            "    let p := reduceRows numCols numRows A numCols\n"
            "    return slice p.1 0"),
        "refinement": (
            "the final pivot count is the leftmost retained column; selecting "
            "from column 0 keeps every column regardless of how many pivots were "
            "placed, so the result is never trimmed to its Hermite form. A "
            "faithful counterpart that sliced from a fixed offset would return a "
            "wrongly-wide matrix on every input with at least one pivot, breaking "
            "the shape the passing and failing tests both pin. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = hnfResult numCols numRows A`: `hnfResult` selects "
            "columns from the FINAL threaded pivot count `p.2`, and this impl "
            "selects from the constant 0, so the two disagree whenever the final "
            "count is non-zero. Refuted at numRows=2, numCols=1 at an ABSTRACT A; "
            "the witness hypothesises `slice … 0` differs from `slice … "
            "(reduceRows 1 2 A 1).2`, attacking the column-selection sub-decision "
            "no other rival touches. Both sides share the same reduced matrix and "
            "differ ONLY in the selection index, which is exactly the sub-decision "
            "under attack; the probe confirms 0 and the threaded count are not "
            "definitionally equal."),
        "witness_reference": _REFERENCE,
        "witness": (
            "example (A : Mat) (h : slice (reduceRows 1 2 A 1).1 0\n"
            "      ≠ slice (reduceRows 1 2 A 1).1 (reduceRows 1 2 A 1).2) :\n"
            "    NonDetT.run (hermiteNormalForm A 2 1) ≠ DivM.res (hnfResult 1 2 A) := by\n"
            "  unfold hermiteNormalForm\n"
            "  simp [NonDetT.run, pure]\n"
            "  intro heq\n"
            "  exact h (by simpa [hnfResult] using heq)\n"),
    },

    # ---- early-stop: the pivot count must GATE each row, not just be threaded ----
    {
        "id": "weak-no-early-stop",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the per-row reduction to two rows unconditionally, threading the
        # pivot count through but never CONSULTING it between rows. The three
        # other rivals all keep `reduceRows` (which carries the `k = 0` guard
        # inside it) and vary its arguments, so none of them probes the early-stop
        # decision itself: the guard that keeps a tall matrix from over-reducing
        # once every column already holds a pivot. Correct only when the count
        # never reaches 0 mid-iteration; wrong on exactly the tall-matrix regime.
        "module": _rival(
            "    -- apply the per-row reduction to two rows unconditionally, without\n"
            "    -- consulting the threaded pivot count between them\n"
            "    let p := stepRow numCols A numCols (numRows - 1)\n"
            "    let q := stepRow numCols p.1 p.2 (numRows - 2)\n"
            "    return slice q.1 q.2"),
        "refinement": (
            "reducing a second row without first re-checking whether every column "
            "already holds a pivot is the omission of the early stop. A faithful "
            "counterpart would keep reducing rows past the point where no column "
            "is left to receive a pivot, so on a matrix with more rows than "
            "columns it drives the pivot count past its floor and selects the "
            "wrong columns. The failing scenario pins the retained submatrix for "
            "exactly such a tall matrix, so it stays RED. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = hnfResult numCols numRows A`: `hnfResult` goes "
            "through `reduceRows`, which stops as soon as the pivot count reaches "
            "0, whereas this impl reduces a fixed second row regardless. Refuted "
            "at numRows=2, numCols=1 at an ABSTRACT A — with a single column the "
            "spec can place at most one pivot and must then stop, while the rival "
            "reduces row 0 anyway. Attacks the (early-stop) sub-decision that the "
            "other three rivals leave untouched, since they all delegate to "
            "`reduceRows` and only vary its arguments."),
        "witness_reference": _REFERENCE,
        "witness": (
            "example (A : Mat) (h : slice (stepRow 1 (stepRow 1 A 1 1).1 (stepRow 1 A 1 1).2 0).1\n"
            "        (stepRow 1 (stepRow 1 A 1 1).1 (stepRow 1 A 1 1).2 0).2\n"
            "      ≠ slice (reduceRows 1 2 A 1).1 (reduceRows 1 2 A 1).2) :\n"
            "    NonDetT.run (hermiteNormalForm A 2 1) ≠ DivM.res (hnfResult 1 2 A) := by\n"
            "  unfold hermiteNormalForm\n"
            "  simp [NonDetT.run, pure]\n"
            "  intro heq\n"
            "  exact h (by simpa [hnfResult] using heq)\n"),
    },

    # ---- opaque-argument abuse: reduce the RIGHT matrix, not a default ----
    {
        "id": "weak-ignores-input-matrix",
        "kind": "uniqueness",
        "expect": "reject",
        # Reduce a fixed default matrix instead of the caller's `A`. Structurally
        # the whole computation is otherwise correct; the bug is that the result
        # does not depend on the input matrix at all. This is the ONLY rival that
        # attacks the opaque `A` binder — its witness must quantify over an
        # abstract A (the refutation only holds where A differs from matDefault).
        "module": _rival(
            "    -- reduce a fixed default matrix, ignoring the caller's input\n"
            "    let p := reduceRows numCols numRows matDefault numCols\n"
            "    return slice p.1 p.2"),
        "refinement": (
            "computing the Hermite form of a fixed placeholder matrix instead of "
            "the caller's matrix returns a result independent of the input. A "
            "faithful counterpart that read from the wrong matrix handle would "
            "return the same answer for every input, failing every scenario whose "
            "expected result depends on the actual matrix — including the failing "
            "test. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = hnfResult numCols numRows A`: the clause pins the "
            "result to the reduction of the INPUT `A`, and this impl reduces "
            "`matDefault`, so the two disagree at every A that differs from the "
            "default. Its witness QUANTIFIES over an abstract A and hypothesises "
            "that the default-matrix reduction differs from the A reduction, since "
            "the divergence exists precisely off the default. Both sides are "
            "written unfolded and differ ONLY in the matrix argument — the "
            "sub-decision under attack — so the probe can confirm they are not "
            "definitionally equal (A is a bound variable, not the default)."),
        "witness_reference": _REFERENCE,
        "witness": (
            "example (A : Mat) (h : slice (reduceRows 1 1 matDefault 1).1 (reduceRows 1 1 matDefault 1).2\n"
            "      ≠ slice (reduceRows 1 1 A 1).1 (reduceRows 1 1 A 1).2) :\n"
            "    NonDetT.run (hermiteNormalForm A 1 1) ≠ DivM.res (hnfResult 1 1 A) := by\n"
            "  unfold hermiteNormalForm\n"
            "  simp [NonDetT.run, pure]\n"
            "  intro heq\n"
            "  exact h (by simpa [hnfResult] using heq)\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals — 1 of them frame-mutation)
# plus an empty AXIOM_TESTS. The two carriers are NOT the same partition: the
# sibling models `leftmost_pivot_column(found, n)` returning an INT marker built
# by a fold `pivot_count` over a read-only `found` list under fractional heap
# permissions, whereas this bundle models the whole `hermiteNormalForm A numRows
# numCols` returning the opaque reduced `Mat`, with the row iteration and final
# column selection modeled deeply (`reduceRows`/`hnfResult`) over the opaque
# per-row `stepRow` and `slice`. The nagini rivals over the int-fold carrier
# re-site onto the sub-decisions of `hnfResult`.
#
#   sibling case                     -> here                             status
#   ---------------------------------------------------------------------------
#   frame-mut-write-found            -> (none, VACUOUS)                   OMITTED
#   partial-domain-min-rows          -> weak-min-rows-window              PORTED
#   partial-domain-skip-bottom-row   -> weak-drops-one-row                RE-SITED
#   uniqueness-no-clamp-negative-k   -> weak-wrong-selection-column       RE-SITED
#   pos-control-branchless           -> pos-control-named-step            RE-EXPRESSED
#   pos-control-hoisted-local        -> pos-control-hoisted-index         PORTED
#   admissibility-self-call     -> admiss-tall-postimage-nondegenerate  RE-SITED
#
#   plus two NET-NEW rivals with no direct sibling:
#   (n/a)                            -> weak-ignores-input-matrix          ADDED
#   (n/a)                            -> weak-no-early-stop                 ADDED
#
# 1 ported + 2 re-sited + 1 re-expressed rivals, 2 positives (1 ported + 1
# re-expressed), 1 re-sited admissibility positive, 2 net-new rivals, 1 omitted
# (frame-mutation, vacuous). No case was dropped because its proof was hard.
#
# DIVERGENCE / NON-TERMINATION (F'-class), measured against the semantics this
# bundle actually sets. `set_option loom.semantics.termination "total"`, so a
# diverging rival is genuinely REJECTED rather than verifying vacuously — the
# spec is NOT weak in this direction and there is no hole to escalate. Measured:
# a `while true` spin with no measure spliced ahead of an otherwise-correct
# loop-free body fails with `error: Decreasing annotations are required in total
# correctness semantics` (exit 1), and a spin carrying a bogus constant measure
# (`decreasing (0 : Nat)`) over a wrong body ALSO fails on this carrier (exit 1),
# so the documented `decreasing`-accepts-a-non-decreasing-measure hole does not
# reach this bundle's splice point.
#
# It is nonetheless NOT SHIPPABLE as a reject case, which is a mechanics limit and
# not a judgement about the spec: the termination error makes the whole FILE
# uncompilable, so no appended witness can elaborate against the rival. Measured
# directly — a witness of `example : (1:Nat) + 1 = 2 := by decide`, which cannot
# fail for any semantic reason, exits 1 against the diverging rival (same
# decreasing-annotation error) while exiting 0 against gold. The gate would record
# that as `witness-unproven`, an inconclusive outcome that FAILS the battery, for
# a rival the verifier in fact rejects correctly. A diverging impl also returns no
# wrong value at any concrete input, so there is nothing for a value-level witness
# to refute. Disposition: correctly rejected by the carrier, unshippable as a
# case — not a known hole and not a vacuous class.
#
# RE-SITED / RE-EXPRESSED (the ARGUMENT is unchanged; only the carrier is):
#  * partial-domain-min-rows attacks the nagini bug directly (only min(m, n) rows
#    examined). Here that IS the (row-count) decision of `hnfResult`; the rival
#    reduces over `min(numRows, numCols)` rows and undercounts a top-row pivot on
#    a tall matrix — the discriminating F2P behaviour the public issue reports.
#  * partial-domain-skip-bottom-row attacks the bottom-row sub-domain (the nagini
#    loop's first index). This carrier's loop counts rows DOWN, so the analogue is
#    "reduce over one fewer row" (`numRows - 1`), omitting the top eligible row —
#    same off-by-one-row attack, on the tail of the row iteration.
#  * uniqueness-no-clamp-negative-k attacks the k-clamp: on a tall matrix the
#    marker must stay clamped at 0 rather than under-decrement. Here the threaded
#    pivot count `k` is exactly what the final `slice p.1 p.2` selects on, so the
#    velvet re-expression ignores that count and slices from a fixed offset 0
#    (keeping every column) — the same "the pivot count is not honored" attack, on
#    the column-selection sub-decision.
#  * pos-control-branchless replaced `if c==1: k=k-1` by the branchless `k=k-c`.
#    Here the decrement lives inside the opaque `stepRow`, not in the impl, so the
#    structurally-different-but-correct reshape is re-expressed at the level this
#    carrier exposes: name the reduction result in a typed local before projecting
#    it, leaving `mat`/`k`/`rowsLeft` definitionally identical.
#
# ADDED (weak-ignores-input-matrix): the sibling never attacks the input carrier
#    directly (its `found` is the fold's subject and every rival reads it). Here
#    the opaque `A` binder would otherwise go unattacked — a binder no rival abuses
#    is a binder the battery says nothing about — so this rival reduces a fixed
#    default matrix instead of `A`. Its witness quantifies over an abstract `A`
#    because the divergence exists precisely where `A ≠ matDefault` (CARRIER NOTE).
#
# ADDED (weak-no-early-stop): raised by an audit probe of the (early-stop) clause.
#    The three other rivals all keep `reduceRows` and vary only its ARGUMENTS, so
#    the `k = 0` guard that lives inside it was never itself attacked — the clause
#    the manifest calls load-bearing was the least-probed of the three. This rival
#    applies `stepRow` to two rows directly, threading the pivot count but never
#    consulting it, so the early stop is the sole thing it gets wrong.
#
# OMITTED (2):
#  * frame-mut-write-found. Nagini-specific (a fractional-heap-permission write
#    the value abstraction cannot see but the permission system rejects). This
#    backend is referentially transparent and the method declares no `mut` binder
#    on an input — `A`, `numRows`, `numCols` are immutable values with no heap and
#    no aliasing — so there is no read-only input to overwrite and no permission
#    system to trip. Also DEMONSTRATED rather than argued: making the input
#    mutable (`method hermiteNormalForm (mut A : Mat) …`) is not even an
#    admissible variant, because the signature lives in the SPEC VIEW — the
#    surgery fails `same_spec` and variant_scope reports `spec view differs`, so
#    the case cannot be expressed without editing the frozen spec. VACUOUS; no
#    substitute fabricated (per the porting map's frame/permission row).
#  * admissibility-self-call -> admiss-tall-postimage-nondegenerate  RE-SITED
#    (was OMITTED; landed by audit). The sibling discharges a precondition
#    (`Acc(list_pred(found),1/2)` + `valid_flags` + `n >= 0`) at a representative
#    call site. That exact shape IS unavailable here, and for the demonstrated
#    reason: a velvet self-call variant (`let adm ← hermiteNormalForm A numRows
#    numCols` ahead of the frozen body) is in scope but cannot build, because the
#    method would then be recursive on arguments none of which decrease —
#    `fail to show termination for hermiteNormalForm / no parameters suitable for
#    structural recursion / well-founded recursion cannot be used`. Under
#    `termination "total"` a self-call at the same arguments is unstateable.
#
#    But the LANE is not vacuous, and the earlier reasoning for dropping it was
#    wrong on the point that matters. "There is no `require`, so no precondition
#    can fail" answers a different question: on a total carrier the analogue of
#    PRECOND-TOO-STRONG is the OBLIGATION being unsatisfiable or degenerate at an
#    F2P-shaped input, which a positive that discharges the post-image at that
#    concrete input — by evaluation, as a `have`, before closing the frozen
#    obligation verbatim — tests directly. The claim that this "does not arise
#    because `hnfResult` is total" is a claim about satisfiability alone and says
#    nothing about degeneracy, which is what the four negative controls measure.
#    So the case is now SHIPPED (see the admissibility block above), pinning the
#    post-image at the tall matrix (numRows=3 > numCols=1) plus the two
#    degenerate boundaries, with four falsified-clause controls each failing to
#    build. The nagini argument is re-sited, not padded.
#
# NO frame/permission substitute and NO parity padding were fabricated.
#
# WITNESS DISCRIMINATION. Each witness ELABORATES against its loop-free rival
# (its `NonDetT.run` term reduces to the rival's straight-line value, which the
# hypothesis separates from the spec's value) and FAILS against the frozen
# solution. But note WHY it fails on gold, because the reason is weaker than it
# looks and an earlier revision of this manifest over-claimed here: gold's build
# fails with a `Type mismatch: After simplification, term heq has type
# (NonDetT.run do let r ← forIn …) = …`, i.e. the `mut`/`while` desugaring simply
# does not reduce. That is SYNTACTIC. Measured with real builds: a witness of this
# shape aimed at a CORRECT loop-free reshape passes both halves too, so the
# two-build check alone does not separate wrong from reshaped on this carrier.
#
# An earlier revision named the gate's THIRD build, the `consistency_probe`, as
# the load-bearing check, on the argument that stating both sides of the `≠` in
# the same UNFOLDED vocabulary makes a definitionally-equal impl yield a literal
# `X ≠ X` that `simp_all` refutes. RETRACTED by audit: that works only when the
# two sides are SYNTACTICALLY identical. A correct rival special-casing the
# no-column input yields the hypothesis `slice A 0 ≠ slice (reduceRows 0 2 A 0).1
# (reduceRows 0 2 A 0).2` — unfolded on both sides, not syntactically equal, but
# `rfl`-provable — and cleared ALL THREE builds (rival 0, gold 1, probe 1). So the
# unfolded rule is necessary, not sufficient.
#
# The load-bearing check is the `witness_reference` (`_REFERENCE`) every reject
# case carries: a loop-free impl of this same spec that the verifier ACCEPTS,
# which the gate substitutes for gold as the refutation's subject after checking
# it shares the spec view and verifies. Measured: all five witnesses fail there
# with `term heq has type True` (a semantic refutation — `simp` proved the
# equation for a correct impl and could not for the rival), and the correct-reshape
# forgery ELABORATES there, so the gate records `witness-vacuous` and catches it.
# Independently, each shipped hypothesis's negated equality was re-checked against
# seven tactics (`rfl`/`simp [reduceRows]`/`simp [hnfResult, reduceRows,
# reduceRows_succ, reduceRows_zero]`/`grind`/`decide`/`simp_all`/`simp <;> grind`)
# and none proves it, so the refuted input exists and the rivals are observably
# different from gold on this carrier — not merely reshaped.
# No `sorry`/`admit`/`native_decide`/`axiom`.
#
# BINDER / CLAUSE COVERAGE. The single clause `out = hnfResult numCols numRows A`
# is attacked by all five rivals across distinct sub-decisions — the row-count
# (window and one-short), the early stop, the column selection, and the
# input-matrix argument. The transparent binders move: `numRows` across {3, 2},
# `numCols` across {1, 2}. The opaque `A` binder is no longer pinned to
# `matDefault` anywhere: every witness quantifies over an abstract `A`, which is
# both the stronger coverage position and what the probe needs.
#
# AXIOM_TESTS: empty. The changed operation (the row iteration + early stop + the
# final selection) is modeled DEEPLY (`reduceRows`/`hnfResult`), and the opaque
# `stepRow`/`slice` are A-references validated by G-AX (mapping.md §3), not
# consumed contracts. There is no axiom lane to mirror, and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
