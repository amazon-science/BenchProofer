"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-12682 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_codingSolverArgs`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts THREE functions (``encode_iteration_budget``, ``coder_solver_budget``,
``estimator_encode_budget``) that thread an integer iteration budget from the
estimator's stored configuration down to the underlying sparse-solver, and pins
each to ``Result() == max_iter`` (or the configured field). This Lean bundle
narrows that surface to the SINGLE purely-functional core the Lean family models:
one map ``codingSolverArgs`` from the construction-time options to the bundle of
arguments the estimator hands the solver, ``SolverArgs``. The two composed steps
(record every option into the stored configuration; assemble the argument bundle
from it) are one pure ``config -> solver-args`` function. So the three nagini
budget-propagation functions collapse into ONE modeled behavior here, and the
nagini cases keyed on nagini-only machinery (the algorithm selector's two arms,
the read-only half-permission field) have no counterpart — see ``assessment`` at
the bottom for the full accounting.

DEFENDED SURFACE (one modeled behavior; SIX independent top-level clauses).
``problem_spec_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha
splitSign nJobs positive maxIter result`` pins EXACTLY, field for field, that the
assembled argument bundle reproduces the configured options it draws from:

  * (C-alg)  ``result.algorithm = algorithm``;
  * (C-nnzc) ``result.nNonzeroCoefs = nNonzeroCoefs``;
  * (C-alpha)``result.alpha = alpha``;
  * (C-iter) ``result.maxIter = maxIter``    — the LOAD-BEARING clause: the
    solver's iteration budget is the configured budget, never replaced by a
    constant standard amount. This is the exact bit the fix restores;
  * (C-jobs) ``result.nJobs = nJobs``;
  * (C-pos)  ``result.positive = positive``.

THE BEHAVIOURAL DISCRIMINATOR (the fix). The pre-fix behavior left the iteration
budget at a CONSTANT standard amount (the solver's own parameter default)
regardless of what the caller configured, so a caller asking for more (or fewer)
iterations silently got the constant. The ``weak-echo-coder-default`` rival below
IS that pre-fix behavior (``maxIter`` pinned to the constant 1000), and the
``weak-echo-lars-default`` rival is the sibling constant (500, the alternate
solver class's built-in default) the nagini battery calls out as the second
canonical wrong answer. The F2P test drives one configuration expecting the
solver to fail to converge (a small budget) and another expecting it to converge
(a large budget); a constant budget decouples convergence from the configured
value and the F2P assertion fails.

BINDER STRUCTURE. The spec predicate has EIGHT input binders. SIX of them appear
in an output clause and are load-bearing (``algorithm``, ``nNonzeroCoefs``,
``alpha``, ``maxIter``, ``nJobs``, ``positive``); each is attacked by a reject
rival and varied across the reject witnesses (see the point-spread block at the
bottom); ``algorithm``, ``nNonzeroCoefs``, ``alpha`` and ``maxIter`` are each
additionally attacked at the VALUE or PAIRING level, not only by a constant. The
remaining two (``nComponents`` — the dictionary-atom count, not a
solver argument — and ``splitSign`` — applied to the code AFTER encoding, not
part of the argument bundle) are NOT part of the modeled output at all, so no
rival can be built to abuse them; they are nonetheless varied across the
witnesses so no position is pinned. (Measured, not assumed: a rival drawing
``positive`` from ``splitSign`` and a rival gating ``maxIter`` on
``nComponents = 0`` are both REJECTED with discriminating witnesses, which is
what "not part of the modeled output" has to mean here — the spec pins the
output to the CORRESPONDING binder, so sourcing a field from an unconstrained
binder violates that field's clause like any other mis-sourcing.)

THE SPEC PINS ITS OUTPUT UNIQUELY, and this is machine-checked rather than
argued: from the six clauses alone, any two results satisfying the predicate at
the same inputs are equal (destruct both conjunctions, ``cases`` both records,
``simp_all``; elaborated as a scratch theorem outside the bundle, exit 0). So
SPEC-TOO-WEAK is structurally unreachable on this carrier — the spec is a
functional graph, not a partial constraint — and the value of the reject lane is
therefore ATTRIBUTION (each clause is load-bearing and separately refutable),
not hole-hunting. The two attacks a per-field drop rival cannot see are covered
explicitly, on BOTH carrier types rather than one: ``weak-scale-alpha`` and
``weak-bump-nnzc`` corrupt a carried VALUE while preserving option shape and
source (the ``Rat`` payload and the ``Option Nat`` payload respectively), and
``weak-swap-nnzc-njobs`` / ``weak-swap-alg-iter`` draw each field from the
OTHER's configured option (the ``Option Nat`` pair and the ``Nat`` pair
respectively), so every field is individually well-sourced and only the pairing
is wrong.

The twelve reject witnesses probe twelve DISTINCT input tuples (``pts=12``).

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini ``weak-frame-mutation``
    rival overwrites a READ-ONLY input field held at half permission and is
    rejected for INSUFFICIENT PERMISSION. Lean is referentially transparent:
    ``nComponents``/``algorithm``/... are immutable values, there is no ``mut``
    input binder, no aliasing, and no read-only cell to overwrite. The class is
    inexpressible here; no substitute probe is fabricated (porting map: vacuous
    on lean).

  * TERMINATION / DIVERGENCE — KNOWN HOLE (not a vacuous class), and the
    disposition is MEASURED, not argued. This backend's frozen file sets no
    ``loom.semantics.termination``, so the carrier is plain Lean: a ``def`` is
    total by construction and the obligation contains no termination clause. Two
    ways to write a diverging rival, both built:
      - a recursive ``def`` with NO decreasing measure does not elaborate at all
        (``fail to show termination for spin2 ... failed to infer structural
        recursion``, exit 1). That is a TOOLING rejection — the file is
        uncompilable — so it attributes nothing to the spec and is not shippable
        as a reject case;
      - a ``partial def`` (plus the ``Inhabited SolverArgs`` instance it
        requires) DOES elaborate and IS rejected (exit 1), but its value is an
        opaque term, and no admissible witness exists for it. Both witness
        shapes were built: stated in the RIVAL's vocabulary (``(spin 0).maxIter
        ≠ 999``) it holds of the rival (exit 0) but fails on the frozen solution
        for a SYNTACTIC reason (``Function expected at spin``, i.e. a missing
        identifier — exactly the non-discriminator this battery's witness
        discipline exists to reject); restated in the FROZEN vocabulary it
        elaborates against the frozen solution too (exit 0, ``witness-vacuous``).
    So the class is a hole in what this bundle can attest, not a distinction the
    carrier collapses; it is recorded rather than papered over, and no
    unfalsifiable case is fabricated to fill it.

  * UNGROUNDED-ORACLE ECHO — the nagini ``@Pure`` answer-key constants
    (``lars_builtin_default()==500``, ``coder_param_default()==1000``) are not
    modeled as oracles here; the postcondition is GROUNDED, relating each output
    field structurally to its configured input. So there is no opaque answer key
    an impl could echo to verify. The two nagini echo rivals are re-expressed as
    what they concretely ARE on this carrier: constant-``maxIter`` rivals
    (``weak-echo-coder-default`` == 1000, ``weak-echo-lars-default`` == 500) that
    violate C-iter for every configured budget other than the constant.

  * PARTIAL-DOMAIN / VALUE — APPLIES. The nagini ``weak-partial-domain-lasso-lars``
    is correct on the arm the literal F2P exercises but wrong elsewhere in the
    modeled domain. There is no algorithm-selector arm on this carrier (the
    solver choice is an opaque ``Nat`` code, not two modeled branches), so its
    faithful re-expression is a rival correct on part of the ``maxIter`` domain
    and wrong on the rest: ``weak-cap-budget`` caps the budget at the constant
    1000, so it AGREES with gold for every configured budget <= 1000 (including
    the F2P's small-budget case) yet diverges for a larger configured budget
    (the F2P's large-budget case). The nagini ``weak-const-coder-ignores-arg``
    (a coder hard-coding a single iteration) is the same class and is subsumed by
    the two constant-``maxIter`` echoes and this cap rival.

  * PER-FIELD DROP — ADDED for this carrier's wider surface. The Lean spec pins
    SIX output fields where nagini modeled only the budget propagation. Coverage
    on this backend requires every top-level clause be attacked, so one rival per
    remaining field drops/overwrites that field to a constant while keeping the
    others correct (``weak-const-algorithm``, ``weak-drop-nnzc``,
    ``weak-drop-alpha``, ``weak-drop-njobs``, ``weak-flip-positive``). Each is a
    faithful "one argument not drawn from its configured option" bug of exactly
    the family the fix repairs for ``maxIter``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``refine ⟨rfl, rfl, rfl, rfl,
rfl, rfl⟩``) is tuned to the frozen form — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet that states the spec predicate at one CONCRETE input tuple, negated, and
closes by ``decide`` (the config and the assembled bundle are ground, so the
whole conjunction reduces) — except ``weak-scale-alpha``, whose claim is over
``Rat`` and needs ``simp [Rat.mul_def, Rat.normalize]`` because ``decide``
reduces the ``Decidable`` instance rather than computing and is stuck on ``Rat``
multiplication. Each witness binds NOTHING in its head (all inputs are ground
literals), so there are no hypotheses whose consistency could be in question.
Each was checked with two real ``lake env lean`` builds to HOLD of its rival
(exit 0) and to FAIL on the frozen solution (exit 1), so it discriminates rather
than asserting a tautology — and the gold-side failure was read, not just
counted: every one is ``decide``/``simp`` SEMANTICALLY refuting the concrete
claim (``proved that the proposition ¬(...) is false`` / ``unsolved goals ⊢
False``), never a missing identifier, a type error, or a stuck reduction.

And the gold-side exit code was shown to CARRY INFORMATION ABOUT THE CLAIM rather
than merely to be nonzero, which reading the error text cannot establish: for
every reject case a THIRD build was made against the frozen solution from a file
differing from the witness in nothing but dropping the ``¬`` — i.e. asserting
that the frozen solution SATISFIES the spec at that same input. All twelve of
those elaborate (exit 0) where the witness itself fails (exit 1). So gold's
verdict flips with the claim at every one of these points, and none of these
cases could have recorded ``rejected`` for a witness asserting gold is correct
there.

POSITIVE CONTROLS ARE NOT DEFINITIONALLY THE FROZEN IMPL, and this is the
property that makes them worth running. A reshape the frozen all-``rfl`` proof
still closes UNCHANGED is definitionally the frozen bundle, so it re-proves
nothing and passes honestly while testing nothing. Both positives here break at
least one clause's ``rfl`` and re-discharge it (``simp`` / ``cases ... <;> rfl``);
each was checked to FAIL under the frozen proof body (exit 1, ``Application type
mismatch``) before being accepted as a control.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
supplies an argument to the underlying solver that is NOT drawn from the
corresponding configured option, so on the F2P configurations the solver runs
with the wrong parameter and the convergence-vs-warning behavior the test asserts
is decoupled from the configuration — so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the two composed steps are modeled deeply as field storage + field
reads); the axiom lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` (also
empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12682"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Per-field assignments in the argument-bundle assembly (all strictly inside
# `-- impl-start`/`-- impl-end`). Each draws one output field from the stored
# configuration; a rival replaces exactly one with a constant / wrong source.
_A_ALG = "algorithm := cfg.algorithm"
_A_NNZC = "nNonzeroCoefs := cfg.nNonzeroCoefs"
_A_ALPHA = "alpha := cfg.alpha"
_A_ITER = "maxIter := cfg.maxIter"
_A_JOBS = "nJobs := cfg.nJobs"
_A_POS = "positive := cfg.positive"

# The frozen TACTIC BODY (strictly inside `-- proof-start`/`-- proof-end`; the
# theorem STATEMENT above it is never touched, so `lean_obligations` still
# matches byte-for-byte). The two soundness positives re-prove the clause their
# reshape breaks by `rfl`, which is the whole point of a positive control: a
# reshape that the frozen proof still closes unchanged is definitionally the
# frozen impl and tests nothing.
_PROOF_BODY = (
    "  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter\n"
    "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩")


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one ground input tuple, negated,
# and closes by `decide` (the config record and the assembled bundle are ground,
# so every conjunct reduces). `argstr` is the eight space-separated input atoms.
#
# `tac` overrides the closing tactic for the one clause `decide` cannot reach.
# `decide` reduces the `Decidable` instance rather than computing, so it gets
# STUCK on `Rat` arithmetic: the value-level `alpha` rival below multiplies a
# `Rat`, and its witness under `decide` fails with `Tactic 'decide' failed`
# (measured) even though the claim is true. `simp [Rat.mul_def, Rat.normalize]`
# closes it. Every other witness here is over `Nat`/`Option Nat`/`Bool` and
# `decide` reduces those fine.
# ---------------------------------------------------------------------------
def _w(argstr, tac="decide"):
    return (
        f"example : ¬ problem_spec_codingSolverArgs {argstr}\n"
        f"    (implementation_codingSolverArgs {argstr}) := by\n"
        "  unfold problem_spec_codingSolverArgs implementation_codingSolverArgs\n"
        f"  {tac}\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_codingSolverArgs` statement byte-identical and re-uses the
    # frozen proof (`refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩`), which still closes
    # because each reshape is definitionally the frozen bundle. (Verified: real
    # builds.)
    # =====================================================================
    {
        "id": "pos-local-budget",
        "kind": "soundness",
        "expect": "verify",
        # Draw the iteration budget through `max cfg.maxIter 0` — extensionally
        # the configured budget on `Nat` (every `Nat` is >= 0) but NOT
        # definitionally it: `Nat.max` is defined by `if a <= b then b else a`,
        # so the field no longer reduces to `maxIter` by `rfl` and C-iter has to
        # be RE-PROVEN (`simp`) rather than inherited. Measured: this impl under
        # the frozen all-`rfl` proof FAILS (`Application type mismatch`, exit 1),
        # so the case genuinely re-discharges C-iter for a new impl shape.
        # Ports the nagini pos-control-local-reshape (there: bind the configured
        # field to a local before forwarding through the coder).
        "module": _swap(
            _swap(_BASE, _A_ITER, "maxIter := max cfg.maxIter 0"),
            _PROOF_BODY,
            "  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter\n"
            "  refine ⟨rfl, rfl, rfl, ?_, rfl, rfl⟩\n"
            "  simp [implementation_codingSolverArgs]"),
        "rationale": "structurally-different CORRECT reshape: the iteration budget "
                     "reaches the bundle through `max cfg.maxIter 0`, which equals "
                     "the configured budget for every `Nat` but is NOT "
                     "definitionally equal to it — `Nat.max` unfolds to a branch on "
                     "`<=`, so the frozen `rfl` for C-iter no longer closes and the "
                     "clause is re-proven by `simp` (verified: the same impl under "
                     "the frozen all-`rfl` proof fails to elaborate). Every output "
                     "field is still its configured option, so C-alg / C-nnzc / "
                     "C-alpha / C-iter / C-jobs / C-pos all hold and the case MUST "
                     "verify (statement byte-identical, no new axiom/lemma) — else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-direct-assembly",
        "kind": "soundness",
        "expect": "verify",
        # Route the two Option/Bool fields through a case-split that rebuilds the
        # same value: `match cfg.nNonzeroCoefs with | none => none | some k =>
        # some k` and `!(!cfg.positive)`. Extensionally the configured options,
        # but NOT definitionally them — neither reduces under an OPEN binder, so
        # C-nnzc and C-pos must be re-proven by case analysis (`cases ... <;>
        # rfl`) instead of inherited from the frozen `rfl`. Measured: this impl
        # under the frozen all-`rfl` proof FAILS (`Application type mismatch`,
        # exit 1). Ports the nagini pos-control-branch-reorder (there: reshape
        # the impl's control flow while both arms still return the configured
        # budget) — a genuine branch reshape, which the previous version of this
        # case (a field-write REORDER inside one record literal) was not, since
        # record-literal field order is definitionally irrelevant.
        "module": _swap(
            _swap(
                _swap(_BASE, _A_NNZC,
                      "nNonzeroCoefs :=\n"
                      "        (match cfg.nNonzeroCoefs with\n"
                      "         | none => none\n"
                      "         | some k => some k)"),
                _A_POS, "positive := !(!cfg.positive)"),
            _PROOF_BODY,
            "  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter\n"
            "  refine ⟨rfl, ?_, rfl, rfl, rfl, ?_⟩\n"
            "  · cases nNonzeroCoefs <;> rfl\n"
            "  · cases positive <;> rfl"),
        "rationale": "structurally-different CORRECT reshape: the non-zero-coef cap "
                     "is rebuilt by a `match` on its own constructors and the "
                     "positivity flag by a double negation. Both equal the "
                     "configured option at every input, but neither reduces under an "
                     "open binder, so C-nnzc and C-pos are RE-PROVEN by case "
                     "analysis rather than inherited (verified: the same impl under "
                     "the frozen all-`rfl` proof fails to elaborate). A faithful "
                     "reshape MUST verify, else SPEC-TOO-STRONG (statement "
                     "byte-identical, no new axiom/lemma).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input: discharge the spec predicate by evaluation at a
    # concrete configuration whose iteration budget is the F2P's large value
    # (2000, the "expect convergence" case) as a `have`, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, ground instance is a `have` prepended to the existing tactic
    # body. Ports the nagini admiss-self-call (there: forward the configured field
    # through the coder for an F2P-shaped input and assert the end-to-end pin).
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter\n"
            "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩",
            "  have _ground : problem_spec_codingSolverArgs 64 1 (some 2) none false (some 2) true 2000\n"
            "      (implementation_codingSolverArgs 64 1 (some 2) none false (some 2) true 2000) := by\n"
            "    unfold problem_spec_codingSolverArgs implementation_codingSolverArgs\n"
            "    decide\n"
            "  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter\n"
            "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩"),
        "rationale": "the obligation is discharged at a normal F2P-shaped "
                     "configuration (iteration budget 2000, the F2P's "
                     "expect-convergence value) by evaluation as a `have`, then the "
                     "frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior would be unsatisfiable at exactly a normal "
                     "F2P input — the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, statement byte-identical, ground "
                     "instance is a `have` in the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input. The first three attack C-iter (the fix);
    # the rest attack one remaining output clause each.
    # =====================================================================

    # ---- the fix itself: constant iteration budget (the coder's own default) ----
    {
        "id": "weak-echo-coder-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: the solver's iteration budget is left at the constant
        # standard amount (1000) instead of the configured budget.
        "module": _swap(_BASE, _A_ITER, "maxIter := 1000"),
        "refinement": "this IS the pre-fix behavior: the iteration budget handed "
                      "to the solver is the constant standard amount (1000) rather "
                      "than the configured budget. A faithful real patch leaving "
                      "the budget at that constant makes the solver run the same "
                      "number of iterations no matter what the caller configured, "
                      "so the F2P's small-budget configuration (which must fail to "
                      "converge and emit the warning) instead runs the full "
                      "constant budget and does NOT warn — the F2P assertion fails "
                      "and the patch would NOT resolve.",
        "rationale": "REJECT from C-iter: the spec pins `result.maxIter = maxIter` "
                     "but the rival emits the constant 1000, differing whenever the "
                     "configured maxIter != 1000. Refuted at the F2P's small-budget "
                     "configuration (maxIter=1).",
        "witness": _w("64 2 none none false none false 1"),
    },

    # ---- the sibling canonical wrong answer: the other solver class's default ----
    {
        "id": "weak-echo-lars-default",
        "kind": "uniqueness",
        "expect": "reject",
        # The nagini battery's second canonical wrong answer: the alternate solver
        # class's built-in default (500) rather than the configured budget.
        "module": _swap(_BASE, _A_ITER, "maxIter := 500"),
        "refinement": "the sibling pre-fix constant: the iteration budget is left "
                      "at the alternate solver class's built-in default (500) "
                      "instead of the configured budget. A faithful patch pinning "
                      "the budget to that class default (the nagini "
                      "weak-echo-lars-default) runs a constant 500 iterations "
                      "regardless of configuration, so the F2P's convergence-vs-"
                      "warning behavior is decoupled from the configured budget and "
                      "the patch would NOT resolve.",
        "rationale": "REJECT from C-iter: the spec pins `result.maxIter = maxIter` "
                     "but the rival emits the constant 500, differing whenever the "
                     "configured maxIter != 500. Refuted at the F2P's large-budget "
                     "configuration (maxIter=2000).",
        "witness": _w("10 1 none none true (some 4) false 2000"),
    },

    # ---- partial-domain: cap the budget at the constant (correct only <= 1000) ----
    {
        "id": "weak-cap-budget",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on part of the maxIter domain: caps the configured budget at the
        # constant 1000, so it AGREES with gold for every configured budget <= 1000
        # (including the F2P's small-budget case) yet diverges above it.
        "module": _swap(_BASE, _A_ITER, "maxIter := min cfg.maxIter 1000"),
        "refinement": "caps the iteration budget at the constant 1000, so it "
                      "matches gold for every configured budget <= 1000 (the F2P's "
                      "small-budget case still fails to converge and warns) but "
                      "silently clamps any larger configured budget. A faithful "
                      "patch capping the budget makes the F2P's large-budget "
                      "configuration (which must converge WITHOUT a warning) run "
                      "only the clamped constant, so it still warns — the F2P "
                      "assertion `assert not record.list` fails and the patch would "
                      "NOT resolve. This is the partial-domain re-expression of the "
                      "nagini weak-partial-domain rival (correct on the F2P-exercised "
                      "sub-domain, wrong on a reachable in-domain remainder).",
        "rationale": "REJECT from C-iter: the spec pins `result.maxIter = maxIter` "
                     "but the rival emits `min maxIter 1000`, which differs "
                     "whenever the configured maxIter > 1000. Refuted at the F2P's "
                     "large-budget configuration (maxIter=2000): min 2000 1000 = "
                     "1000 != 2000.",
        "witness": _w("20 0 none none false (some 1) true 2000"),
    },

    # ---- per-field drops: attack each remaining output clause -----------------
    {
        "id": "weak-const-algorithm",
        "kind": "uniqueness",
        "expect": "reject",
        # Overwrite the solver-selection code with a constant instead of drawing it
        # from the configured option.
        "module": _swap(_BASE, _A_ALG, "algorithm := 0"),
        "refinement": "hands the solver a constant selection code (0) instead of "
                      "the configured one. A faithful patch not drawing the "
                      "algorithm from its configured option would run a different "
                      "solver than the caller asked for, so a configuration "
                      "selecting one solver silently gets another — every F2P and "
                      "PASS_TO_PASS case pinned to the chosen solver's behavior "
                      "would mismatch, so the patch would NOT resolve.",
        "rationale": "REJECT from C-alg: the spec pins `result.algorithm = "
                     "algorithm` but the rival emits the constant 0, differing "
                     "whenever the configured algorithm != 0. Refuted at "
                     "algorithm=3.",
        "witness": _w("5 3 none none false none false 100"),
    },
    {
        "id": "weak-drop-nnzc",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the configured non-zero-coefficient cap to absent.
        "module": _swap(_BASE, _A_NNZC, "nNonzeroCoefs := none"),
        "refinement": "drops the configured non-zero-coefficient cap to absent "
                      "instead of forwarding it. A faithful patch omitting that "
                      "argument lets the solver use its own unbounded default, so a "
                      "caller who configured a cap silently gets none — the "
                      "PASS_TO_PASS cases pinned to the configured cap would "
                      "mismatch, so the patch would NOT resolve.",
        "rationale": "REJECT from C-nnzc: the spec pins `result.nNonzeroCoefs = "
                     "nNonzeroCoefs` but the rival emits `none`, differing whenever "
                     "the configured nNonzeroCoefs is `some`. Refuted at "
                     "nNonzeroCoefs=some 7.",
        "witness": _w("5 1 (some 7) none false none false 100"),
    },
    {
        "id": "weak-drop-alpha",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the configured sparsity parameter to absent.
        "module": _swap(_BASE, _A_ALPHA, "alpha := none"),
        "refinement": "drops the configured sparsity-controlling parameter to "
                      "absent instead of forwarding it. A faithful patch omitting "
                      "that argument lets the solver fall back to its own default "
                      "penalty, so a caller who configured a sparsity level silently "
                      "gets another — the PASS_TO_PASS cases pinned to the "
                      "configured value would mismatch, so the patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C-alpha: the spec pins `result.alpha = alpha` but "
                     "the rival emits `none`, differing whenever the configured "
                     "alpha is `some`. Refuted at alpha=some 4.",
        "witness": _w("5 1 none (some 4) false none false 100"),
    },
    {
        "id": "weak-scale-alpha",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-level attack on C-alpha. Every other alpha rival only collapses
        # `some` to `none` (a presence bug); this one keeps the option shape and
        # corrupts the carried VALUE, so it is the only case that probes the
        # `Rat` payload rather than the `Option` wrapper.
        "module": _swap(_BASE, _A_ALPHA, "alpha := cfg.alpha.map (· * 2)"),
        "refinement": "hands the solver a sparsity-controlling parameter scaled by "
                      "a constant factor instead of the configured one. A faithful "
                      "patch that rescaled that argument on its way to the solver "
                      "would run every configuration at a different penalty than "
                      "the caller asked for, so the PASS_TO_PASS cases pinned to a "
                      "configured sparsity level get a different code and the patch "
                      "would NOT resolve. Distinct from the drop rival: presence is "
                      "preserved, so a patch that merely forwarded the argument "
                      "would still be wrong here.",
        "rationale": "REJECT from C-alpha at the VALUE level: the spec pins "
                     "`result.alpha = alpha` but the rival emits `alpha.map (· * 2)`, "
                     "differing for every configured alpha other than 0. Refuted at "
                     "alpha=some 1. NOTE the witness closes by "
                     "`simp [Rat.mul_def, Rat.normalize]`, not `decide`: `decide` "
                     "reduces the `Decidable` instance rather than computing, so it "
                     "is stuck on `Rat` multiplication (measured: `Tactic 'decide' "
                     "failed` against the rival even though the claim is true).",
        "witness": _w("5 1 none (some 1) false none false 100",
                      "simp [Rat.mul_def, Rat.normalize]"),
    },
    {
        "id": "weak-swap-nnzc-njobs",
        "kind": "uniqueness",
        "expect": "reject",
        # CROSS-FIELD attack: both `Option Nat` arguments are still drawn from
        # the stored configuration, and both are still `some`/`none` faithfully —
        # they are just drawn from EACH OTHER'S option. No per-field drop rival
        # catches this, because each field in isolation looks well-sourced; only
        # the pairing is wrong. Guards against a spec that pinned "every output
        # field equals SOME configured input" rather than the CORRESPONDING one.
        "module": _swap(
            _swap(_BASE, _A_NNZC, "nNonzeroCoefs := cfg.nJobs"),
            _A_JOBS, "nJobs := cfg.nNonzeroCoefs"),
        "refinement": "hands the solver the configured parallelism selection as its "
                      "non-zero-coefficient cap and vice versa — each argument is "
                      "drawn from a configured option, just not its own. A faithful "
                      "patch that crossed those two keyword arguments would cap the "
                      "code's sparsity at the job count and parallelize by the "
                      "sparsity cap, so every PASS_TO_PASS case that configures "
                      "either one gets a different solver call and the patch would "
                      "NOT resolve.",
        "rationale": "REJECT from C-nnzc and C-jobs jointly: the spec pins each "
                     "output field to its CORRESPONDING configured option, so "
                     "drawing each from the other's violates both clauses whenever "
                     "the two configured options differ. Refuted at "
                     "nNonzeroCoefs=some 7 with nJobs=some 2.",
        "witness": _w("5 1 (some 7) none false (some 2) false 100"),
    },
    {
        "id": "weak-bump-nnzc",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-level attack on C-nnzc, the `Option Nat` analogue of
        # weak-scale-alpha. Every other nNonzeroCoefs rival either collapses
        # `some` to `none` (weak-drop-nnzc, a PRESENCE bug) or re-sources the
        # whole option (weak-swap-nnzc-njobs, a PAIRING bug); both leave the
        # carried `Nat` PAYLOAD untested, so a spec pinning only the option's
        # shape would survive them. This one keeps presence and source and
        # corrupts the payload by one.
        "module": _swap(_BASE, _A_NNZC,
                        "nNonzeroCoefs := cfg.nNonzeroCoefs.map (· + 1)"),
        "refinement": "hands the solver a non-zero-coefficient cap one greater "
                      "than the configured one. A faithful patch that adjusted "
                      "that argument on its way to the solver would let every "
                      "configuration keep one more non-zero coefficient than the "
                      "caller asked for, so the PASS_TO_PASS cases pinned to a "
                      "configured cap get a different code and the patch would "
                      "NOT resolve. Distinct from the drop rival: presence is "
                      "preserved, so a patch that merely forwarded the argument "
                      "would still be wrong here.",
        "rationale": "REJECT from C-nnzc at the VALUE level: the spec pins "
                     "`result.nNonzeroCoefs = nNonzeroCoefs` but the rival emits "
                     "`nNonzeroCoefs.map (· + 1)`, differing for every configured "
                     "`some k`. Refuted at nNonzeroCoefs=some 7.",
        "witness": _w("7 1 (some 7) none true (some 3) false 100"),
    },
    {
        "id": "weak-swap-alg-iter",
        "kind": "uniqueness",
        "expect": "reject",
        # CROSS-FIELD attack on the two `Nat` fields, the analogue of
        # weak-swap-nnzc-njobs one type over. Both arguments are still drawn from
        # the stored configuration and both are still `Nat`s — they are just
        # drawn from EACH OTHER's configured option, so each field in isolation
        # looks well-sourced and only the pairing is wrong. Without this, the
        # `Nat` half of the surface is attacked only by constant rivals, so a
        # spec pinning "every `Nat` output equals SOME configured `Nat` input"
        # rather than the CORRESPONDING one would survive the whole lane.
        "module": _swap(
            _swap(_BASE, _A_ALG, "algorithm := cfg.maxIter"),
            _A_ITER, "maxIter := cfg.algorithm"),
        "refinement": "hands the solver the configured iteration budget as its "
                      "algorithm selection and the configured algorithm code as "
                      "its iteration budget — each argument is drawn from a "
                      "configured option, just not its own. A faithful patch that "
                      "crossed those two keyword arguments would both run a "
                      "solver the caller did not select and run it for a budget "
                      "taken from the selection code, so the F2P's "
                      "convergence-vs-warning behavior is decoupled from the "
                      "configured budget and the patch would NOT resolve.",
        "rationale": "REJECT from C-alg and C-iter jointly: the spec pins each "
                     "output field to its CORRESPONDING configured option, so "
                     "drawing each from the other's violates both clauses "
                     "whenever the two configured values differ. Refuted at "
                     "algorithm=2 with maxIter=2000.",
        "witness": _w("30 2 none none true none true 2000"),
    },
    {
        "id": "weak-drop-njobs",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the configured parallelism selection to absent.
        "module": _swap(_BASE, _A_JOBS, "nJobs := none"),
        "refinement": "drops the configured parallelism selection to absent instead "
                      "of forwarding it. A faithful patch omitting that argument "
                      "runs the solver with a different parallelism than configured; "
                      "a caller who configured a job count silently gets the "
                      "default, so the PASS_TO_PASS cases pinned to the configured "
                      "selection would mismatch and the patch would NOT resolve.",
        "rationale": "REJECT from C-jobs: the spec pins `result.nJobs = nJobs` but "
                     "the rival emits `none`, differing whenever the configured "
                     "nJobs is `some`. Refuted at nJobs=some 2.",
        "witness": _w("5 1 none none false (some 2) false 100"),
    },
    {
        "id": "weak-flip-positive",
        "kind": "uniqueness",
        "expect": "reject",
        # Overwrite the configured positivity constraint with a constant.
        "module": _swap(_BASE, _A_POS, "positive := true"),
        "refinement": "hands the solver a constant positivity flag (true) instead "
                      "of the configured one. A faithful patch pinning that flag "
                      "would enforce (or drop) a positivity constraint the caller "
                      "did not ask for, so a configuration with the opposite setting "
                      "gets the wrong code — the PASS_TO_PASS positivity cases "
                      "(parameterized over both settings) would mismatch, so the "
                      "patch would NOT resolve.",
        "rationale": "REJECT from C-pos: the spec pins `result.positive = positive` "
                     "but the rival emits the constant `true`, differing whenever "
                     "the configured positive is `false`. Refuted at positive=false.",
        "witness": _w("5 1 none none false none false 100"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus an EMPTY AXIOM lane. This
# bundle narrows the sibling's THREE budget-propagation functions to the SINGLE
# purely-functional core the Lean family models (the config->solver-args map),
# then attacks each of its six output clauses.
#
#   sibling case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-branch-reorder      -> pos-direct-assembly       RE-EXPRESSED
#   pos-control-local-reshape       -> pos-local-budget          PORTED
#   admiss-self-call                -> admiss-f2p-input          RE-EXPRESSED
#   weak-echo-coder-default (1000)  -> weak-echo-coder-default   PORTED
#   weak-echo-lars-default (500)    -> weak-echo-lars-default    PORTED
#   weak-partial-domain-lasso-lars  -> weak-cap-budget           RE-EXPRESSED
#   weak-const-coder-ignores-arg    -> (subsumed)                SUBSUMED
#   weak-frame-mutation             -> (none)                    VACUOUS
#   (none)                          -> weak-const-algorithm      ADDED (attacks C-alg)
#   (none)                          -> weak-drop-nnzc            ADDED (attacks C-nnzc)
#   (none)                          -> weak-drop-alpha           ADDED (attacks C-alpha)
#   (none)                          -> weak-drop-njobs           ADDED (attacks C-jobs)
#   (none)                          -> weak-flip-positive        ADDED (attacks C-pos)
#   (none)                          -> weak-scale-alpha          ADDED (C-alpha, value level)
#   (none)                          -> weak-bump-nnzc            ADDED (C-nnzc, value level)
#   (none)                          -> weak-swap-nnzc-njobs      ADDED (C-nnzc x C-jobs)
#   (none)                          -> weak-swap-alg-iter        ADDED (C-alg x C-iter)
#   (diverge/nonterm: absent there) -> (none)                    KNOWN HOLE (see above)
#   AXIOM_TESTS (0)                 -> (none)                    DROPPED (G-AX)
#
# RE-EXPRESSED (pos-direct-assembly): the sibling's branch-reorder positive
#   reshapes the algorithm-selector control flow while both arms still return the
#   configured budget. This carrier has no algorithm-selector branch (the solver
#   choice is an opaque Nat code, not two modeled arms), so the analogous
#   "structurally different but correct" reshape routes two output fields through
#   a constructor case-split / double negation that equals the configured option
#   at every input but does NOT reduce under an open binder — a genuine branch
#   reshape whose broken clauses are re-proven by `cases ... <;> rfl`.
#   An earlier revision of this case merely REORDERED the field writes inside one
#   record literal, which record-literal semantics make definitionally
#   irrelevant: that variant was accepted by the frozen all-`rfl` proof unchanged,
#   so it re-proved nothing and was a vacuous control. Same for the earlier
#   pos-local-budget, which bound the budget to a local (`let budget :=
#   cfg.maxIter`) — also definitionally the frozen bundle. Both now perturb the
#   term so at least one clause's `rfl` genuinely fails first (verified: each new
#   impl under the frozen proof body exits 1 with `Application type mismatch`,
#   and verifies only with its own re-proof).
# RE-EXPRESSED (weak-cap-budget): the sibling's partial-domain rival is correct on
#   the lasso_cd arm the literal F2P exercises but off-by-one on the lasso_lars
#   arm. There is no algorithm arm on this carrier, so the partial-domain idea is
#   re-expressed over the maxIter DOMAIN: cap the budget at the constant 1000, so
#   it agrees with gold for every configured budget <= 1000 (the F2P's small-budget
#   case) and diverges above it (the F2P's large-budget case). Same class (correct
#   on the F2P-exercised sub-domain, wrong on a reachable remainder), same
#   refinement (a faithful cap fails the large-budget F2P assertion).
# SUBSUMED (weak-const-coder-ignores-arg): the sibling's supporting near-miss (the
#   coder hard-codes a single iteration, ignoring its budget argument) is the same
#   "constant iteration budget" class as the two echo rivals plus the cap rival,
#   all of which violate C-iter. Rather than a fourth constant-budget rival at yet
#   another literal it is folded into those three.
# VACUOUS (weak-frame-mutation): the sibling overwrites a READ-ONLY input field
#   held at half permission and is rejected for INSUFFICIENT PERMISSION. Lean is
#   referentially transparent — the inputs are immutable values, there is no `mut`
#   binder, no aliasing, no read-only cell — so the class is inexpressible here.
#   No substitute probe is fabricated.
# ADDED (weak-scale-alpha, weak-swap-nnzc-njobs): two attacks NO per-field drop
#   rival can see. The drop rivals all collapse a `some` to `none`, so they test
#   only PRESENCE; weak-scale-alpha keeps the option shape and corrupts the
#   carried `Rat` VALUE, which is the only probe of the alpha payload (and the
#   only witness on this carrier that needs a non-`decide` closer). The per-field
#   rivals also each leave one field wrong in ISOLATION, so a spec pinning "every
#   output field equals SOME configured input" rather than the CORRESPONDING one
#   would survive all of them; weak-swap-nnzc-njobs draws each `Option Nat` field
#   from the other's configured option, so every field is individually
#   well-sourced and only the pairing is wrong. Both were confirmed rejected with
#   discriminating witnesses (real builds, rival exit 0 / gold exit 1 semantic).
# ADDED (weak-const-algorithm ... weak-flip-positive): the Lean spec pins SIX
#   output fields where the nagini battery modeled only the budget propagation.
#   This backend's coverage tool requires EVERY top-level postcondition clause be
#   attacked by some reject rival, so one rival per remaining field drops or
#   overwrites that field while keeping the others correct. They are not fabricated
#   for an unmodeled behavior: each attacks a real, load-bearing clause of the SAME
#   modeled spec (every solver argument must be its configured option — the exact
#   property the fix repairs for maxIter), and each carries the same refinement
#   structure (a faithful "argument not drawn from its configured option" patch
#   feeds the solver a wrong parameter and fails the F2P / PASS_TO_PASS cases).
#
# BINDERS. The spec predicate has eight input binders. SIX appear in an output
#   clause and are load-bearing (algorithm, nNonzeroCoefs, alpha, maxIter, nJobs,
#   positive); each is attacked by a rival and varied across the witnesses. The
#   other two (nComponents, splitSign) are NOT part of the modeled output at all
#   — nComponents is the dictionary-atom count, not a solver argument; splitSign
#   is applied to the code AFTER encoding — so no rival can be built to abuse them
#   (a rival mishandling either would still satisfy all six output clauses and
#   verify, correctly, because they do not constrain the output). They are
#   nonetheless varied across the witnesses so no position reads as pinned.
#
# POINT SPREAD. The twelve reject witnesses probe twelve DISTINCT input tuples
#   (pts=12). Transcribed from the `_w(...)` calls above, not restated from
#   memory: an earlier revision of this table listed weak-flip-positive at
#   `positive=true`, which is the value at which that rival AGREES with gold —
#   the witness actually stands at `positive=false`, as it must, and the table
#   was the thing that was wrong. (nComponents, algorithm, nNonzeroCoefs, alpha,
#   splitSign, nJobs, positive, maxIter) =
#     (64, 2, none,   none,   false, none,   false, 1)     weak-echo-coder-default  C-iter
#     (10, 1, none,   none,   true,  some 4, false, 2000)  weak-echo-lars-default   C-iter
#     (20, 0, none,   none,   false, some 1, true,  2000)  weak-cap-budget          C-iter
#     (5,  3, none,   none,   false, none,   false, 100)   weak-const-algorithm     C-alg
#     (5,  1, some 7, none,   false, none,   false, 100)   weak-drop-nnzc           C-nnzc
#     (5,  1, none,   some 4, false, none,   false, 100)   weak-drop-alpha          C-alpha
#     (5,  1, none,   some 1, false, none,   false, 100)   weak-scale-alpha         C-alpha (value)
#     (7,  1, some 7, none,   true,  some 3, false, 100)   weak-bump-nnzc           C-nnzc (value)
#     (5,  1, some 7, none,   false, some 2, false, 100)   weak-swap-nnzc-njobs     C-nnzc+C-jobs
#     (30, 2, none,   none,   true,  none,   true,  2000)  weak-swap-alg-iter       C-alg+C-iter
#     (5,  1, none,   none,   false, some 2, false, 100)   weak-drop-njobs          C-jobs
#     (5,  1, none,   none,   false, none,   false, 100)   weak-flip-positive       C-pos
#   Across them every binder takes >= 2 distinct values, so no input position is
#   pinned. Note the spread is deliberately NOT uniform per clause: C-alpha and
#   C-nnzc are each probed at BOTH the option level (some -> none) and the value
#   level (some k -> some (k+1) / some 2k), because a drop rival alone leaves the
#   carried payload untested; and the two pairing rivals cover both typed pairs
#   the surface has (`Option Nat` x `Option Nat`, `Nat` x `Nat`), because a
#   per-field rival leaves each field wrong only in ISOLATION.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the composed steps are modeled deeply), so there is nothing to probe and
# the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
