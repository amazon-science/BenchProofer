"""properties.py — G-PBT falsification battery for sympy__sympy-18189 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled total function):

  implementation_diophantine (eq : Equation) (var syms : List Nat)
      (permute : Bool) : List (List Int)

  ``var`` is the equation's variables in canonical order; ``syms`` is the
  requested output order; ``permute`` selects the solution-generation mode
  (``false`` = the base family only; ``true`` = the additionally admissible
  solutions as well). The canonical solver ``solveCanonical eq permute`` is an
  UNCHANGED delegate declared ``opaque`` (no ``_prop`` axiom — the proof
  consumes no property of it); ``reindexTuple`` / ``reindexAll`` are the
  per-tuple coordinate re-arrangement (from canonical order into the requested
  order) and its front-recursive lift over a solution list.

  The single top-level postcondition clause pins the result by a case split on
  whether a reordering is requested:

    result =
      if syms ≠ var then reindexAll var syms (solveCanonical eq permute)
      else solveCanonical eq permute

  Two INDEPENDENT, load-bearing decisions live in that clause:

    * MODE PROPAGATION — the solution-generation mode fed to ``solveCanonical``
      is the caller's ``permute``, identically in BOTH arms. The reordering arm
      must NOT re-derive under a constant mode. Pinned by ``permute`` (and by
      the ``solveCanonical`` argument being exactly it).
    * RE-ARRANGEMENT — on the reordering arm every canonical tuple is threaded
      through ``reindexAll var syms``; on the matching arm it is returned as-is.
      Pinned by ``var``/``syms`` (their ordering relation selects the arm) and
      by the presence of the ``reindexAll`` wrapper.

  Input binders of the spec predicate: ``eq`` (the opaque equation),
  ``var`` / ``syms`` (the two orderings, whose relation selects the arm),
  ``permute`` (the mode), ``result``.

CONDITIONING ON THE CARRIER. ``Equation`` and ``solveCanonical`` are ``opaque``
— no literal input computes the solution set, so ``decide`` cannot separate a
rival from gold at any concrete input. The refutation witnesses therefore
QUANTIFY over the carrier: each binds an ``eq : Equation`` and ONE hypothesis
that separates the two terms the rival confuses (e.g. the mode genuinely
changes the family, ``solveCanonical eq false ≠ solveCanonical eq true`` — which
is a true property of the real solver: the two modes genuinely disagree on the
issue equation. Note on provenance, corrected by audit: it is G-CONF that
certifies this, by running the REAL callee in both modes and differentially
comparing the shadow against the post-patch oracle. G-AX is a declared SKIP for
this bundle — ``solveCanonical`` is an ``opaque`` signature with no consumed
``_prop`` axiom, so there is no callee contract for G-AX to validate — and an
earlier revision of this docstring wrongly credited the certification to it).
One hypothesis per witness, so the assumptions are jointly
satisfiable (the gate's consistency probe was run on each and could not derive
``False``). The witness then unfolds the spec + impl at that point, reduces the
``if`` on the concrete orderings, and closes with ``exact h``.

REDUCING GOLD'S LOOP IS PART OF THE WITNESS'S JOB. A witness is checked in a
file whose ``proof`` region has been emptied, so ``reindexAll_eq_map`` and
``loop_helper`` are not available; on the REORDERING arm the frozen impl is an
``Id.run do … for … mut`` loop that nothing then unfolds. A witness that stops at
``exact h`` therefore fails on gold because the loop never REDUCED, not because
gold satisfies the spec — a distinction the gate's exit codes cannot draw, and
one that a forgery asserting the OPPOSITE of a refutation was measured to clear.
So each reorder-arm witness re-proves the loop=map bridge inside its own
``example`` (see ``_loop_norm`` / ``_reduce_reorder``) and normalizes gold's loop
itself, making gold's failure the reduced, semantic ``¬True``.

THE SAME APPLIES TO THE MATCHING ARM, which the port wrongly exempted. There is
no ``for`` loop there, but ``Id.run do … return`` still leaves a residual
``do pure PUnit.unit; pure …`` that the arm-selecting ``simp only`` does not run,
so the un-normalized matching-arm witness had the identical defect and was
measured hollow the identical way (a forgery asserting gold is CORRECT there
cleared rival/gold/probe alike). ``_WIT_ELSE`` therefore discharges that residual
with a witness-local ``have hrun … := rfl`` before closing.

Every witness here was machine-checked to ELABORATE against its rival, to FAIL
SEMANTICALLY against the frozen solution, to have jointly satisfiable
hypotheses, AND to have its gold-side exit code TRACK THE CLAIM (the flipped
claim fails on gold too, and the un-negated spec claim with no closing tactic
SUCCEEDS on gold — so the tactic block really does reduce gold's obligation to
something the refutation contradicts). Real discriminators, not tautologies and
not unfolding artifacts.

BINDER COVERAGE. ``permute`` is refuted at ``true`` (weak-const-false,
weak-drop-relabel, weak-else-ignores-permute, weak-swap-orderings) AND at
``false`` (weak-const-true), so the mode is not pinned at a single value.
``var``/``syms`` are refuted on the REORDER arm at two variables
(``syms = [1,0] ≠ var = [0,1]``) and at THREE (``syms = [1,2,0] ≠ var =
[0,1,2]``, weak-swap-orderings — where the coordinate map is no longer its own
inverse, a distinction two variables cannot express) AND on the MATCHING arm
(``syms = var = [0,1]``, weak-else-ignores-permute), so both branches of the case
split are exercised. ``result`` is pinned only positionally (it is the spec's
subject, so every witness names it as the applied impl rather than by binder
name); the reporter's by-name note on it is a spelling artifact, not a gap.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The only nagini input is a value-type
    flag carrying no heap permission, and this carrier is referentially
    transparent besides (plain immutable ``Bool`` / ``List`` values, no
    aliasing). There is no read-only half-permission to overwrite; the class has
    no expressible instance here and no substitute is fabricated. See
    'assessment'.

  * PARTIAL-DOMAIN (nagini ``weak-prepatch-const-false`` /
    ``weak-const-true``) — PORTED. The prepatch bug re-derives the reordering arm
    under a CONSTANT mode, ignoring the caller's ``permute``. weak-const-false is
    the literal prepatch (mode forced ``false``); weak-const-true is its mirror
    (mode forced ``true``). Each attacks MODE PROPAGATION and is refuted where the
    two modes diverge. weak-else-ignores-permute moves the mode-drop onto the
    MATCHING arm so the OTHER branch of the case split is also attacked — an
    ADDITION on this carrier, not a port of the asymmetric nagini case.

  * ASYMMETRIC DISPATCH (nagini ``weak-asymmetric-true-uses-false``) — VACUOUS
    HERE, dropped with a machine-checked reason. Nagini's rival branches on the
    flag and re-derives under the wrong constant on the ``true`` branch only. On
    this carrier that impl is DEFINITIONALLY the ``weak-const-false`` rival: the
    ``else`` arm of its inner dispatch re-derives under ``permute`` where
    ``permute`` is already known ``false``, so both arms collapse to the constant
    ``false`` and ``cases permute <;> simp`` proves the two impls equal as
    functions (built and checked, exit 0). Landing it would add a case
    observationally identical to one already present — vacuous by attack C — so
    it is deliberately NOT shipped. The distinction it was meant to add (a rival
    that consults the mode yet still gets one direction wrong) is instead covered
    by having BOTH constant directions plus both arms of the case split.

  * DROP-THE-RELABELLING (nagini ``weak-drop-relabel``) — PORTED. Re-derive
    under the correct mode but return the canonical family WITHOUT
    ``reindexAll``. Attacks RE-ARRANGEMENT; refuted where the requested order
    differs from the canonical order. ADDITIONALLY, weak-swap-orderings attacks
    the same decision at finer grain — the wrapper is present but applied in the
    INVERSE direction — which the nagini battery had no analogue for (its
    relabelling was one opaque axiom with no direction to get wrong).

  * UNGROUNDED-ORACLE ECHO — VACUOUS (as in nagini). The postcondition is
    grounded in the inputs (``reindexAll var syms (solveCanonical eq permute)``,
    a function of ``eq``/``var``/``syms``/``permute``), so the cheapest correct
    impl returns it directly — that IS the positive control, not a cheat. There
    is no answer-key to echo.

  * DIVERGENCE / NON-TERMINATION — VACUOUS CLASS on this carrier, and the
    reason is a demonstrated property of the carrier rather than a difficulty.
    Recorded by audit; the port stated no disposition at all, which left the one
    lane whose two settings invert the correct answer unaddressed.

    This bundle sets NO ``set_option loom.semantics.termination`` (no lean
    bundle in the corpus does), so the disposition has to be MEASURED. What the
    builds show is that the carrier admits no diverging rival to ship:

      - A plain ``def`` that self-loops is REFUSED BY THE ELABORATOR, not by the
        spec: ``fail to show termination for implementation_diophantine /
        failed to infer structural recursion``. Same for a non-decreasing helper
        (``def spinUp (n : Nat) := spinUp (n + 1)``). So the file does not even
        reach the obligation, and the ``witness``'s RIVAL half — the build that
        MUST succeed — fails with that same termination error rather than with
        anything about the spec. Such a case can only ever record
        ``witness-unproven``; it is not shippable.
      - Marking it ``partial`` is what makes a diverging impl elaborate, and it
        is the tooling's own escape hatch: ``partial`` seals the constant behind
        an ``Inhabited`` witness so no equation lemma exists. The frozen script
        then fails with ``Tactic `unfold` failed to unfold
        `implementation_diophantine```. The rejection is real, but it is
        attributable to OPACITY, not to the postcondition, and the two-build
        check cannot repair that: the only witness shape available must
        hypothesize about the sealed constant itself
        (``implementation_diophantine eq [0,1] [0,1] true ≠ solveCanonical eq
        true``), and that claim was measured to ELABORATE AGAINST THE FROZEN
        SOLUTION TOO (exit 0 on both sides) — ``witness-vacuous``, because an
        opaque hypothesis about gold's own output is not contradictory.
        Independently, ``partial`` is on the witness lane's banned-token list,
        so the shape is inadmissible by rule as well.

    So there is no diverging impl on this carrier that a witness can refute:
    without ``partial`` the class is unreachable, with it the class is opaque
    and vacuous. This is a VACUOUS CLASS (the battery is complete without it),
    NOT a known spec hole — the distinction attack F′ turns on. Nothing is
    shipped for it and no ``spec_holes`` entry is filed.

  * SOUNDNESS + ADMISSIBILITY (nagini ``pos-control-*`` / ``admiss-*``) —
    PORTED IN FULL: THREE structurally-different CORRECT impls that must verify,
    and one ground-instance admissibility probe. The nagini
    ``pos-control-grounded-oracle-cheapest`` is ``pos-functional-direct`` and
    ``pos-control-bool-dispatch`` is ``pos-mode-dispatch`` (the latter landed by
    audit — the first port dropped it with no recorded reason, and it is the only
    positive whose arms do not thread the ``permute`` binder syntactically);
    ``pos-let-bound-callee`` is an addition on this carrier.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (solveCanonical mode-dependence
and reindex bijection) belong to G-AX, which the G-PBT spec lane ignores. Here
``solveCanonical`` is ``opaque`` with NO consumed ``_prop`` axiom and the
re-arrangement is modeled deeply, so there is no in-model axiom obligation for
this gate to re-discharge. ``AXIOM_TESTS`` is empty.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18189"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl or proof region and is
# unique in the file, so every replacement preserves same_spec by construction.
# ---------------------------------------------------------------------------

# The FULL frozen impl body (between the markers), verified verbatim.
_IMPL_GOLD = (
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) := Id.run do\n"
    "  if syms ≠ var then\n"
    "    let mut acc : List (List Int) := []\n"
    "    for t in solveCanonical eq permute do\n"
    "      acc := acc ++ [reindexTuple var syms t]\n"
    "    return acc\n"
    "  return solveCanonical eq permute"
)

# The FULL frozen tactic body of `correct_diophantine`.
_PROOF_BODY = (
    "  intro eq var syms permute\n"
    "  unfold problem_spec_diophantine implementation_diophantine\n"
    "  by_cases h : syms ≠ var\n"
    "  · rw [if_pos h, if_pos h]\n"
    "    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`\n"
    "    have hbridge :\n"
    "        Id.run (do\n"
    "          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))\n"
    "            (fun t r => do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))\n"
    "          pure r)\n"
    "        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))\n"
    "            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl\n"
    "    rw [hbridge, loop_helper, reindexAll_eq_map]\n"
    "    simp\n"
    "  · rw [if_neg h, if_neg h]\n"
    "    rfl"
)

# The frozen proof intro line (the admissibility case prepends a `have` here).
_PROOF_INTRO = "  intro eq var syms permute\n"

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"
assert _BASE.count(_PROOF_INTRO) == 1, "proof-intro anchor drifted"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. Each keeps the `theorem correct_diophantine` statement
# byte-identical, introduces no helper lemma / axiom / assumption token.
# ---------------------------------------------------------------------------

# pos-functional-direct: the cheapest correct impl written in pure FUNCTIONAL
# form (no `Id.run do` loop) — it returns the grounded oracle directly. Since
# the impl is now definitionally the spec's RHS, the loop-bridge proof is
# replaced by `unfold; rfl` (statement byte-identical; only the tactic body
# changes; no new declaration).
_POS_DIRECT_IMPL = (
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if syms ≠ var then reindexAll var syms (solveCanonical eq permute)\n"
    "  else solveCanonical eq permute"
)
_POS_DIRECT_PROOF = (
    "  intro eq var syms permute\n"
    "  unfold problem_spec_diophantine implementation_diophantine\n"
    "  rfl"
)
_POS_DIRECT = _swap(_impl(_POS_DIRECT_IMPL), _PROOF_BODY, _POS_DIRECT_PROOF)

# pos-let-bound-callee: bind the canonical solve to a local `sols` used in BOTH
# arms (a data-flow reshape) — same value, different shape. The frozen proof
# body still discharges (the local zeta-reduces to the frozen call).
_POS_LET_IMPL = (
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) := Id.run do\n"
    "  let sols := solveCanonical eq permute\n"
    "  if syms ≠ var then\n"
    "    let mut acc : List (List Int) := []\n"
    "    for t in sols do\n"
    "      acc := acc ++ [reindexTuple var syms t]\n"
    "    return acc\n"
    "  return sols"
)
_POS_LET = _impl(_POS_LET_IMPL)

# pos-mode-dispatch: the port of the nagini `pos-control-bool-dispatch`, which the
# original port DROPPED without recording a reason. Landed here by audit: the
# whole result is computed under a CONCRETE mode literal in each arm of an outer
# dispatch on `permute`, so no arm mentions the binder `permute` in its call to
# the canonical solver at all. That is a genuinely different control shape from
# gold's single mode-threading call — the spec-too-strong probe the two existing
# positives do not make, since both of them still pass `permute` through
# syntactically. Verified: `cases permute <;> rfl` closes it (exit 0).
_POS_DISPATCH_IMPL = (
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if permute then\n"
    "    (if syms ≠ var then reindexAll var syms (solveCanonical eq true)\n"
    "     else solveCanonical eq true)\n"
    "  else\n"
    "    (if syms ≠ var then reindexAll var syms (solveCanonical eq false)\n"
    "     else solveCanonical eq false)"
)
_POS_DISPATCH_PROOF = (
    "  intro eq var syms permute\n"
    "  unfold problem_spec_diophantine implementation_diophantine\n"
    "  cases permute <;> rfl"
)
_POS_DISPATCH = _swap(_impl(_POS_DISPATCH_IMPL), _PROOF_BODY, _POS_DISPATCH_PROOF)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation is discharged at a ground, F2P-shaped input (a
# reordering request `syms = [1,0] ≠ var = [0,1]` under `permute = true`) as a
# `have` prepended to the frozen tactic body, then the frozen obligation is
# closed verbatim. If that ground instance could not be discharged, the modeled
# behavior would be unsatisfiable at the shape the F2P exercises — the analogue
# of PRECOND-TOO-STRONG. The frozen theorem carries no precondition hypothesis
# (the behavior is total), so this ground-instance form is the honest analogue
# of the nagini precondition-admission probe. Nothing is assumed: no new
# declaration, the statement is byte-identical.
_ADMISS = _swap(
    _BASE, _PROOF_INTRO,
    _PROOF_INTRO +
    "  have _ground : ∀ (e : Equation),\n"
    "      problem_spec_diophantine e [0, 1] [1, 0] true\n"
    "        (implementation_diophantine e [0, 1] [1, 0] true) := by\n"
    "    intro e\n"
    "    unfold problem_spec_diophantine implementation_diophantine\n"
    "    simp only [ne_eq, List.cons.injEq, and_true, and_false,\n"
    "      reduceCtorEq, not_false_eq_true, if_true]\n"
    "    have hbridge :\n"
    "        Id.run (do\n"
    "          let r ← forIn (solveCanonical e true) ([] : List (List Int))\n"
    "            (fun t r => do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield (r ++ [reindexTuple [0, 1] [1, 0] t])))\n"
    "          pure r)\n"
    "        = Id.run (forIn (solveCanonical e true) ([] : List (List Int))\n"
    "            (fun t r => ForInStep.yield (r ++ [reindexTuple [0, 1] [1, 0] t]))) := rfl\n"
    "    rw [hbridge, loop_helper, reindexAll_eq_map]\n"
    "    simp\n",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each ships in FUNCTIONAL form (so the witness reduces the
# `if` by `simp`/`unfold` without the stripped-away loop lemmas) and carries the
# FROZEN proof body verbatim, so its rejection is the frozen script failing
# against the reshaped impl — which is exactly why the WITNESS, not the
# rejection, attributes the failure to the spec.
# ---------------------------------------------------------------------------

# weak-const-false (THE prepatch bug): reorder arm re-derives under the CONSTANT
# `false` mode, dropping the caller's `permute`. Attacks MODE PROPAGATION.
_RIVAL_CFALSE = _impl(
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if syms ≠ var then reindexAll var syms (solveCanonical eq false)\n"
    "  else solveCanonical eq permute"
)

# weak-const-true (mirror): reorder arm re-derives under the CONSTANT `true`
# mode. Attacks MODE PROPAGATION from the other side.
_RIVAL_CTRUE = _impl(
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if syms ≠ var then reindexAll var syms (solveCanonical eq true)\n"
    "  else solveCanonical eq permute"
)

# weak-drop-relabel: reorder arm re-derives under the correct mode but returns
# the canonical family WITHOUT `reindexAll`. Attacks RE-ARRANGEMENT.
_RIVAL_DROP = _impl(
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if syms ≠ var then solveCanonical eq permute\n"
    "  else solveCanonical eq permute"
)

# weak-else-ignores-permute: the MATCHING arm (syms = var) re-derives under the
# constant `false` mode, dropping the caller's `permute`. Attacks MODE
# PROPAGATION on the OTHER branch of the case split.
_RIVAL_ELSE = _impl(
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if syms ≠ var then reindexAll var syms (solveCanonical eq permute)\n"
    "  else solveCanonical eq false"
)

# weak-swap-orderings: thread the correct mode AND re-arrange, but hand
# `reindexAll` its two orderings the WRONG WAY ROUND, i.e. apply the INVERSE
# coordinate permutation. Attacks RE-ARRANGEMENT at a finer grain than
# weak-drop-relabel: the wrapper is present and non-trivial, only its direction
# is wrong, so a spec that merely demanded "some re-arrangement happened" would
# admit it. Stated over THREE variables on purpose: at two the swap is an
# involution (`reindexTuple [0,1] [1,0] t = reindexTuple [1,0] [0,1] t`), which
# would make the rival definitionally gold and the case VACUOUS. Machine-checked
# non-vacuous at three (`reindexTuple [0,1,2] [1,2,0] [7,8,9] ≠ reindexTuple
# [1,2,0] [0,1,2] [7,8,9]` by `decide`).
_RIVAL_SWAP = _impl(
    "def implementation_diophantine\n"
    "    (eq : Equation) (var syms : List Nat) (permute : Bool) :\n"
    "    List (List Int) :=\n"
    "  if syms ≠ var then reindexAll syms var (solveCanonical eq permute)\n"
    "  else solveCanonical eq permute"
)


# ---------------------------------------------------------------------------
# WITNESSES. Each is machine-checked to elaborate against its rival and to FAIL
# against the frozen solution.
#
# WHY THE REORDER-ARM WITNESSES CARRY A LOCAL NORMALIZER. A witness is checked
# in a file whose `proof` region has been emptied, so `reindexAll_eq_map` and
# `loop_helper` are GONE. On the reordering arm the frozen impl is an
# `Id.run do … for … mut` loop, and with those lemmas stripped no tactic here
# unfolds it: gold's side then fails with `Type mismatch … expected ¬(do let r ←
# forIn …).run = …`, i.e. the loop never reduced. That failure is an UNFOLDING
# failure, not a refutation, and it is worthless as evidence — measured: a
# FORGERY asserting gold IS CORRECT at that point (the exact opposite of a
# refutation, hypothesis `… false = … true`) elaborated against the rival, FAILED
# on gold with the same shape of message, and its consistency probe could not
# derive `False`, so it cleared all three checks. So each reorder-arm witness
# re-proves the loop=map bridge INSIDE its own `example` (witness-local `have`s —
# no new top-level declaration, nothing assumed) and normalizes gold's loop
# itself. The `try rw` steps are no-ops against the functional rivals, so one
# tactic block serves both subjects. Gold's failure is then `Type mismatch: h …
# but is expected to have type ¬True` — the spec is SATISFIED there, reduced to
# `True`, and the refutation is genuinely false of gold. Under the repaired
# technique the forgery above FAILS on gold, as it must.
#
# THE MATCHING ARM NEEDS THE SAME TREATMENT, and the port's claim that it did not
# was WRONG — measured, not argued. With `syms = var` the frozen impl has no
# `for` loop, but it is still `Id.run do … return`, which desugars to a residual
# `do pure PUnit.unit; pure (solveCanonical eq true)` that
# `simp only [ne_eq, not_true_eq_false, if_false]` does NOT run. Three builds:
#
#   * the true-claim control (the positive spec claim at that point with the
#     reduction block and NO closing tactic) FAILS on gold, leaving
#     `⊢ (do pure PUnit.unit; pure (solveCanonical eq true)).run
#          = solveCanonical eq true` — i.e. the `Id.run` never reduced;
#   * the shipped witness's gold-side error is a Type mismatch against that same
#     UNREDUCED term, not against `¬True`;
#   * a FORGERY asserting the OPPOSITE (that gold IS CORRECT there, hypothesis
#     `solveCanonical eq false = solveCanonical eq true`, goal un-negated)
#     elaborated against the rival (exit 0), FAILED on gold (exit 1) and its
#     consistency probe could not derive `False` (exit 1) — all three gate checks
#     cleared, so the gate would have recorded `rejected` for a witness claiming
#     gold is correct at that input. The exit code carried no information.
#
# So this witness now discharges the residual `Id.run` itself, as a witness-local
# `have hrun : … := rfl` (no new top-level declaration, nothing assumed), and
# `try rw [hrun]` — a no-op against the functional rival, whose matching arm has
# no `Id.run` at all. Gold's goal then REDUCES to `¬solveCanonical eq true =
# solveCanonical eq true` and gold's failure is the semantic one; under the
# repaired technique the forgery FAILS on gold (`No goals to be solved`: the
# reduced positive claim is closed by `rfl` inside the block, so `exact h` has
# nothing left), as it must.
# ---------------------------------------------------------------------------

def _loop_norm(var, syms):
    """Witness-local re-proof of `loop_helper` / `reindexAll_eq_map` at a
    CONCRETE pair of orderings, so a witness can reduce the frozen impl's
    `Id.run do … for` loop in a file where the proof region is stripped."""
    return (
        f"  have hloop : ∀ (xs init : List (List Int)),\n"
        f"      Id.run (forIn xs init\n"
        f"          (fun t r => ForInStep.yield (r ++ [reindexTuple {var} {syms} t])))\n"
        f"        = init ++ xs.map (reindexTuple {var} {syms}) := by\n"
        "    intro xs\n"
        "    induction xs with\n"
        "    | nil => intro init; simp\n"
        "    | cons a as ih =>\n"
        "      intro init\n"
        "      rw [List.forIn_cons]\n"
        "      simp only [Id.run, bind] at ih ⊢\n"
        "      rw [ih]\n"
        "      simp\n"
        f"  have hmap : ∀ (xs : List (List Int)),\n"
        f"      reindexAll {var} {syms} xs = xs.map (reindexTuple {var} {syms}) := by\n"
        "    intro xs\n"
        "    induction xs with\n"
        "    | nil => rfl\n"
        "    | cons a as ih => simp [reindexAll, ih]\n"
    )


def _reduce_reorder(var, syms, mode, by_decide=False):
    """Select the reordering arm at concrete orderings, then normalize the loop.
    `try` so the same block is a no-op against a functional rival."""
    pick = (f"  have hne : ({syms} : List Nat) ≠ {var} := by decide\n"
            "  unfold problem_spec_diophantine implementation_diophantine\n"
            "  rw [if_pos hne, if_pos hne]\n") if by_decide else (
        "  unfold problem_spec_diophantine implementation_diophantine\n"
        "  simp only [ne_eq, List.cons.injEq, and_true, and_false,\n"
        "    reduceCtorEq, not_false_eq_true, if_true]\n")
    return pick + (
        f"  try rw [show Id.run (do\n"
        f"      let r ← forIn (solveCanonical eq {mode}) ([] : List (List Int))\n"
        f"        (fun t r => do\n"
        f"          pure PUnit.unit\n"
        f"          pure (ForInStep.yield (r ++ [reindexTuple {var} {syms} t])))\n"
        "      pure r)\n"
        f"    = Id.run (forIn (solveCanonical eq {mode}) ([] : List (List Int))\n"
        f"        (fun t r => ForInStep.yield (r ++ [reindexTuple {var} {syms} t]))) from rfl]\n"
        "  try rw [hloop]\n"
        "  simp only [hmap, List.nil_append]\n"
    )


_WIT_CFALSE = (
    "example (eq : Equation)\n"
    "    (h : (solveCanonical eq false).map (reindexTuple [0, 1] [1, 0])\n"
    "         ≠ (solveCanonical eq true).map (reindexTuple [0, 1] [1, 0])) :\n"
    "    ¬ problem_spec_diophantine eq [0, 1] [1, 0] true\n"
    "        (implementation_diophantine eq [0, 1] [1, 0] true) := by\n"
    + _loop_norm("[0, 1]", "[1, 0]")
    + _reduce_reorder("[0, 1]", "[1, 0]", "true")
    + "  exact h"
)

_WIT_CTRUE = (
    "example (eq : Equation)\n"
    "    (h : (solveCanonical eq true).map (reindexTuple [0, 1] [1, 0])\n"
    "         ≠ (solveCanonical eq false).map (reindexTuple [0, 1] [1, 0])) :\n"
    "    ¬ problem_spec_diophantine eq [0, 1] [1, 0] false\n"
    "        (implementation_diophantine eq [0, 1] [1, 0] false) := by\n"
    + _loop_norm("[0, 1]", "[1, 0]")
    + _reduce_reorder("[0, 1]", "[1, 0]", "false")
    + "  exact h"
)

_WIT_DROP = (
    "example (eq : Equation)\n"
    "    (h : solveCanonical eq true\n"
    "         ≠ (solveCanonical eq true).map (reindexTuple [0, 1] [1, 0])) :\n"
    "    ¬ problem_spec_diophantine eq [0, 1] [1, 0] true\n"
    "        (implementation_diophantine eq [0, 1] [1, 0] true) := by\n"
    + _loop_norm("[0, 1]", "[1, 0]")
    + _reduce_reorder("[0, 1]", "[1, 0]", "true")
    + "  exact h"
)

# MATCHING arm: no `for` loop, but the frozen impl's `Id.run do … return` leaves a
# residual `do pure PUnit.unit; pure …` that the `simp only` does NOT run, so the
# witness discharges it locally (see the block above — the un-normalized form was
# measured HOLLOW by a forgery that cleared all three gate checks).
_WIT_ELSE = (
    "example (eq : Equation)\n"
    "    (h : solveCanonical eq false ≠ solveCanonical eq true) :\n"
    "    ¬ problem_spec_diophantine eq [0, 1] [0, 1] true\n"
    "        (implementation_diophantine eq [0, 1] [0, 1] true) := by\n"
    "  unfold problem_spec_diophantine implementation_diophantine\n"
    "  have hrun : Id.run (do\n"
    "      pure PUnit.unit\n"
    "      pure (solveCanonical eq true)) = solveCanonical eq true := rfl\n"
    "  simp only [ne_eq, not_true_eq_false, if_false]\n"
    "  try rw [hrun]\n"
    "  exact h"
)

# Three orderings, so the `if` is selected by `decide` on the concrete lists
# rather than by the two-element `List.cons.injEq` chain.
_WIT_SWAP = (
    "example (eq : Equation)\n"
    "    (h : reindexAll [1, 2, 0] [0, 1, 2] (solveCanonical eq true)\n"
    "         ≠ (solveCanonical eq true).map (reindexTuple [0, 1, 2] [1, 2, 0])) :\n"
    "    ¬ problem_spec_diophantine eq [0, 1, 2] [1, 2, 0] true\n"
    "        (implementation_diophantine eq [0, 1, 2] [1, 2, 0] true) := by\n"
    + _loop_norm("[0, 1, 2]", "[1, 2, 0]")
    + _reduce_reorder("[0, 1, 2]", "[1, 2, 0]", "true", by_decide=True)
    + "  exact h"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-functional-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the grounded oracle `reindexAll var syms (solveCanonical eq "
            "permute)` (matching arm: `solveCanonical eq permute`) is a function "
            "of the inputs, so the cheapest correct impl returns it directly in "
            "pure FUNCTIONAL form (no `Id.run do` loop). It is definitionally the "
            "spec's RHS, so `unfold; rfl` closes it — must verify (else "
            "SPEC-TOO-STRONG). The `correct_diophantine` statement is "
            "byte-identical; only the tactic body changes; no new lemma/axiom/"
            "assumption token."
        ),
    },
    {
        "id": "pos-let-bound-callee",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "a correct data-flow reshape: the canonical solve is bound to a local "
            "`sols` used in BOTH arms (vs gold's two inline calls). The value on "
            "every input is unchanged, so both decisions of the postcondition "
            "(mode propagation + re-arrangement) still hold; the frozen proof "
            "body discharges verbatim (the local zeta-reduces to the frozen "
            "call). Must verify, else SPEC-TOO-STRONG. No new lemma/axiom."
        ),
    },
    {
        "id": "pos-mode-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DISPATCH,
        "rationale": (
            "the nagini bool-dispatch positive, landed by audit (the original "
            "port dropped it silently). A correct impl whose CONTROL SHAPE differs "
            "from gold in the one way the other two positives do not: it "
            "dispatches on the mode first and calls the canonical solver with a "
            "concrete mode LITERAL in each arm, so no arm passes the `permute` "
            "binder through syntactically at all — yet on every input the value is "
            "gold's, since inside the `true` arm `permute` IS `true`. `cases "
            "permute <;> rfl` closes it. This is the real SPEC-TOO-STRONG probe "
            "for MODE PROPAGATION: a spec that demanded the caller's binder be "
            "threaded literally, rather than that the resulting VALUE agree, would "
            "reject this faithful impl. Statement byte-identical; only the tactic "
            "body changes; no new lemma/axiom/assumption token."
        ),
    },
    # =====================================================================
    # ADMISSIBILITY — must VERIFY, else PRECOND-TOO-STRONG analogue.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground input (a "
            "reordering request `syms = [1,0] ≠ var = [0,1]` under `permute = "
            "true`, the issue's full-family request) as a `have` prepended to the "
            "frozen tactic body; the frozen obligation is then closed verbatim. "
            "Verifies (else the modeled behavior would be unsatisfiable at the "
            "shape the F2P exercises — the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: no new declaration, the `correct_diophantine` "
            "statement is byte-identical."
        ),
    },
    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — must REJECT, each with a witness.
    # =====================================================================
    {
        "id": "weak-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CFALSE,
        "refinement": (
            "THIS IS the pre-patch bug: the reordering branch re-derives the "
            "canonical solution set under the DEFAULT (base-only) mode, dropping "
            "the caller's requested mode. For the issue equation in a "
            "non-canonical symbol ordering with the full-family mode requested, "
            "the re-arranged answer COLLAPSES to the single base solution instead "
            "of the full 8-element family the F2P demands, so the added F2P "
            "assertion MISMATCHES. The faithful real patch (= prepatch) does NOT "
            "resolve — this is the literal G-DIFF prepatch."
        ),
        "rationale": (
            "REJECT from MODE PROPAGATION on the reordering arm: at `syms = "
            "[1,0] ≠ var = [0,1]`, `permute = true` the spec demands `reindexAll "
            "var syms (solveCanonical eq true)`, but the rival computes it under "
            "`false`. Witness conditions on `eq` with the single hypothesis that "
            "the re-arranged families under the two modes differ (true wherever "
            "the modes diverge — the F2P sub-domain) and closes by `exact h`; it "
            "fails on gold, which uses `permute`. If it verifies, the spec does "
            "not force the caller's mode on the reordering arm (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_CFALSE,
    },
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CTRUE,
        "refinement": (
            "the symmetric error: the reordering branch hard-codes the "
            "full-family mode regardless of the caller. When a caller requests "
            "the base family in a non-canonical ordering (the common case across "
            "the un-permuted diophantine tests), the branch would over-enumerate "
            "the full sign/order family instead of the base one, so every such "
            "assertion MISMATCHES. The faithful real patch does NOT resolve. "
            "Guards against a spec that pins only the full-family direction and "
            "leaves the base direction free."
        ),
        "rationale": (
            "REJECT from MODE PROPAGATION on the reordering arm, at the OTHER "
            "mode: at `syms = [1,0] ≠ var = [0,1]`, `permute = false` the spec "
            "demands `reindexAll var syms (solveCanonical eq false)`, but the "
            "rival computes it under `true`. Witness conditions on `eq` with the "
            "single hypothesis that the two modes' re-arranged families differ "
            "and closes by `exact h`; fails on gold. Varies the `permute` binder "
            "to `false` (the other rivals hold it at `true`)."
        ),
        "witness": _WIT_CTRUE,
    },
    {
        "id": "weak-drop-relabel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP,
        "refinement": (
            "re-derive under the correct mode but return the canonical-ordering "
            "family DIRECTLY, omitting the per-tuple component re-arrangement. "
            "The whole point of the reordering branch is that the caller asked "
            "for a DIFFERENT symbol order, so every returned tuple would have its "
            "components in the wrong positions. The tests that supply a "
            "non-canonical order and assert the re-arranged tuples MISMATCH. The "
            "faithful real patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from RE-ARRANGEMENT on the reordering arm: at `syms = [1,0] ≠ "
            "var = [0,1]` the spec demands `reindexAll var syms (solveCanonical "
            "eq permute)`, but the rival returns the un-re-arranged canonical "
            "family. Witness conditions on `eq` with the single hypothesis that "
            "the canonical family differs from its re-arrangement under this "
            "ordering (`reindexAll` is not the identity for `[1,0] ≠ [0,1]`) and "
            "closes by `exact h`; fails on gold. If it verifies, the "
            "postcondition does not force the re-arrangement (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_DROP,
    },
    {
        "id": "weak-else-ignores-permute",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ELSE,
        "refinement": (
            "the mode-drop moved onto the MATCHING arm: when the requested order "
            "already equals the canonical order, this re-derives under the "
            "default (base-only) mode rather than the caller's mode. A caller "
            "requesting the full family with the canonical ordering would then "
            "receive only the base family, so those F2P/P2P assertions MISMATCH. "
            "The faithful real patch does NOT resolve. Guards against a spec that "
            "pins the mode only on the reordering arm and leaves the matching arm "
            "free."
        ),
        "rationale": (
            "REJECT from MODE PROPAGATION on the MATCHING arm (the other branch "
            "of the case split): at `syms = var = [0,1]`, `permute = true` the "
            "spec demands `solveCanonical eq true`, but the rival returns "
            "`solveCanonical eq false`. Witness conditions on `eq` with the "
            "single hypothesis `solveCanonical eq false ≠ solveCanonical eq true` "
            "and closes by `exact h`; fails on gold. Exercises the `syms = var` "
            "branch that the other three rivals never touch — so the case split "
            "is attacked on both arms."
        ),
        "witness": _WIT_ELSE,
    },
    {
        "id": "weak-swap-orderings",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SWAP,
        "refinement": (
            "the re-arrangement is performed in the WRONG DIRECTION: the two "
            "orderings handed to the per-tuple coordinate map are interchanged, "
            "so every tuple is permuted by the INVERSE of the requested "
            "rearrangement. With three or more variables in a genuinely "
            "non-canonical requested order, each returned tuple carries its "
            "components in the wrong positions (a different wrong set from "
            "omitting the rearrangement outright), so a test supplying such an "
            "order and asserting the re-arranged tuples MISMATCHES. The faithful "
            "real patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from RE-ARRANGEMENT at finer grain than weak-drop-relabel: "
            "the `reindexAll` wrapper is PRESENT and is not the identity, only "
            "its two ordering arguments are exchanged, so a spec that demanded "
            "merely 'some rearrangement was applied' would admit this rival "
            "while the frozen spec pins the exact `reindexAll var syms` "
            "direction. Stated at THREE variables deliberately: at two the "
            "exchange is an involution and the rival would be definitionally "
            "gold (a vacuous case); non-vacuity at three is machine-checked by "
            "`decide` on a concrete tuple. Witness conditions on `eq` with the "
            "single hypothesis that the two directions disagree on this "
            "solution family and closes by `exact h`; it fails on gold, which "
            "applies the requested direction."
        ),
        "witness": _WIT_SWAP,
    },
]


# No consumed axioms and no deep-model references for the PBT spec lane:
# `solveCanonical` is opaque with no `_prop` axiom the proof consumes, and the
# re-arrangement is modeled deeply. The axiom lane is G-AX's job; this gate
# ignores it.
AXIOM_TESTS = []
