"""properties.py — G-PBT falsification battery for sympy__sympy-13480 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_cothReduce`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``); the adversarial ARGUMENTS are carried over, the
mechanics re-expressed against this backend's carrier. The nagini bundle models
the reduction as ``periodic_part_simplification(x, m) -> int`` over two bare int
handles; this Lean bundle models the SAME single purely-functional core — one
total function over the remaining part ``x`` and the nonzero multiple part ``m``,
returning an ``Except``-carried outcome. Every nagini case therefore carries over
as an attack on the one modeled obligation; the mapping of each nagini case to
its Lean counterpart (or its principled omission) is in the module
``assessment``.

DEFENDED SURFACE (one modeled behavior). The reduction always completes with a
value (``Except.ok …``); WHICH value is decided by the evaluator applied to the
periodic multiple part ``m``:

  * if that evaluator's result on ``m`` is the distinguished point at infinity,
    the result is the first evaluator applied to the remaining part ``x``;
  * otherwise the result is the second evaluator applied to ``x``.

The postcondition pins ``result`` to exactly this single grounded computation. It
therefore has THREE independent things to defend: the two exhaustive,
mutually-exclusive arms of the dispatch (WHICH value, selected by the value
computed off the PERIODIC part ``m``), and — a clause this carrier has that
nagini's does not — the OUTCOME CHANNEL: the reduction always completes carrying
a value, and the no-value outcome never occurs. Each of the three is attacked by
at least one rival below.

The BEHAVIOURAL DISCRIMINATOR (the fix): the branch is governed by the value
computed from the periodic part ``m`` and by NO OTHER quantity, and the two arms
map to the two evaluators in exactly the pinned direction. The pre-fix bug
discriminated on an unrelated quantity (computed off the remaining part), so the
wrong-discriminator rival below IS that pre-fix behavior; the swapped-returns and
constant rivals attack the arm→evaluator mapping.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing. The nagini frame-mutation stand-in (nagini case 7,
    the value-corrupting rebind of the governing input) is NOT vacuous, though —
    it re-expresses cleanly as shadowing the periodic binder with the remaining
    part before computing the dispatch, and is carried below as a reject rival.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The spec carries no pure helper/oracle at
    all: the postcondition is stated directly over the inputs through the two
    evaluators. There is nothing an implementation could echo. (The two
    evaluators and the sentinel are left ``opaque`` because they are unchanged
    outside operations the fix never touches — NOT an oracle for the modeled
    decision; the impl still has to select the branch and return the right
    evaluator's result.) In its place the battery carries honest positive
    controls that must verify.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this carrier. ``implementation_*``
    is a total Lean ``def``; a diverging implementation cannot be written at all.
    (The nagini sibling carries no divergence case either.)

  * WRONG-DISCRIMINATOR / SWAPPED / CONSTANT / REBIND — APPLY. Rivals that decide
    the branch off the wrong quantity, invert the arm→evaluator mapping, ignore
    the dispatch entirely, or clobber the governing input.

  * NON-COMPLETION — APPLIES, and is CARRIER-SPECIFIC (no nagini counterpart).
    Nagini's modeled function returns a bare int, so "completed with a value" is
    not observable there and no nagini case attacks it. Here the outcome is
    carried in a two-constructor channel and the spec pins that channel, so a
    rival can decline to produce a value on one arm. That is also the behavior
    the issue actually reports — the reduction escaping instead of answering — so
    leaving it unattacked would leave the clause closest to the real defect
    untested. Added as a rival below rather than inferred from the nagini list.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``by_cases``/``rfl`` script is tuned to
the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. Each was checked to
HOLD of its rival and to FAIL on the frozen solution, so it discriminates rather
than asserting a tautology.

CONDITIONING ON THE CARRIER. The two evaluators and the sentinel are ``opaque``,
so a witness cannot COMPUTE ``cothFn ⟨"m"⟩``. Instead each witness QUANTIFIES over
the carrier: it assumes just enough about the opaque terms at the chosen input to
separate the rival from the spec — e.g. that the dispatch lands on a given arm
(``cothFn ⟨"m"⟩ = complexInfinity`` or ``≠``) and that the two evaluators disagree
on the remaining part (``cothFn ⟨"x"⟩ ≠ tanhFn ⟨"x"⟩``). These are the two
distinct properties the real ``coth``/``tanh`` exhibit on the F2P witnesses
(``coth(m)=zoo`` vs finite; ``coth ≠ tanh``), and — crucially — each witness's
hypotheses are about DISTINCT opaque terms (or the same term on distinct arms),
so they are jointly satisfiable (no witness assumes both ``t = c`` and ``t ≠ c``).

BINDER / POINT SPREAD. The reject witnesses move both input binders rather than
fixing them at one convenient point. The DISPATCH binder (the value off ``m``)
takes both settings: the sentinel arm (``cothFn m = complexInfinity``, exercised
by wrong-discriminator, swapped, sentinel-arm non-completion, const-sibling,
rebind) AND the finite arm (``cothFn m ≠ complexInfinity``, exercised by
const-primary and finite-arm non-completion) are each attacked, so both
value-selecting clauses are refuted; the completion clause is refuted on BOTH
arms by the two non-completion rivals. The two carrier points ``x`` and ``m`` are
moved to distinct fresh handles per witness; the seven reject witnesses probe
seven distinct inputs.

AUDIT NOTE (independent re-derivation of every case; see the two mechanics fixed
below). Each reject witness was rebuilt three ways: against the rival (must
elaborate), against the frozen solution (must fail), and against the frozen
solution with the final projection step replaced by a deliberate type error, to
make Lean PRINT the type the tactic prefix left on the hypothesis. On a healthy
case that reveal prints ``True`` on the frozen side — ``simp`` PROVED the spec's
equation for the frozen impl — and the concrete false equation on the rival side;
that pair, not the exit code, is what makes the frozen-side failure semantic. Two
witnesses (the two constant rivals) originally omitted ``Id.run``/``pure`` from
their rewrite list because their own rivals have no do-block; against the FROZEN
impl the spec side then stayed an unreduced ``(pure _).run`` term and the frozen
build failed on that syntax rather than on the claim. Both now carry the rewrites
and both reveal ``True`` on the frozen side. A flipped-claim forgery (the same
hypotheses and prefix, asserting the spec HOLDS at that input) was also built
against the frozen solution for every reject case, to confirm the frozen-side
exit code tracks WHAT is claimed rather than being constant.

AXIOM lane: EMPTY here. The three ``opaque`` declarations (the two evaluators and
the sentinel) are A-reference callees validated executably by G-AX/G-CONF, and
the proof consumes no ``axiom``. The axiom lane belongs to G-AX; this gate
ignores it, and the nagini ``AXIOM_TESTS`` (the determinism/singleton and
containment probes) are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13480"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positives/
# admissibility that re-prove, the proof region) so same_spec stays
# byte-identical.

# The whole gold impl body (impl region).
_I_GOLD = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let cothm := cothFn m\n"
    "  if cothm = complexInfinity then\n"
    "    return Except.ok (cothFn x)\n"
    "  else\n"
    "    return Except.ok (tanhFn x)"
)

# The frozen proof body (proof region).
_P_GOLD = (
    "  intro x m\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  by_cases h : cothFn m = complexInfinity\n"
    "  · simp only [Id.run, h, if_true]; rfl\n"
    "  · simp only [Id.run, h, if_false]; rfl"
)


# =====================================================================
# POSITIVE CONTROL 1 (soundness) — De-Morgan-equivalent control flow:
# negate the dispatch test and SWAP the two branch BODIES to match. Still
# anchored to the value off the periodic part `m`; returns the identical value
# on every input. Straight-line two-way branch, no induction/lemma. Reproves
# with an honest tactic body (the negated test needs `if_neg`/`if_pos` bridging).
# MUST verify — else the dispatch clause is SPEC-TOO-STRONG.
# Ports nagini case 1 (pos-control-demorgan-reorder).
# =====================================================================
_POS_DEMORGAN_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let cothm := cothFn m\n"
    "  if cothm ≠ complexInfinity then\n"
    "    return Except.ok (tanhFn x)\n"
    "  else\n"
    "    return Except.ok (cothFn x)"
)
_POS_DEMORGAN_PROOF = (
    "  intro x m\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, ne_eq, pure]\n"
    "  by_cases h : cothFn m = complexInfinity\n"
    "  · rw [if_pos h, if_neg (by simp [h])]\n"
    "  · rw [if_neg h, if_pos (by simp [h])]"
)


# =====================================================================
# POSITIVE CONTROL 2 (soundness) — inline the dispatch call into the test (no
# `cothm` temporary). Determinism makes the inlined call denote the same value,
# so the result is unchanged on every input and the FROZEN proof body still
# closes (the `let` is gone but the `by_cases`/`simp`/`rfl` shape is agnostic to
# it). MUST verify — else the spec pins the temporary, not the behavior.
# Ports nagini case 1b (pos-control-inline-discriminator).
# =====================================================================
_POS_INLINE_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  if cothFn m = complexInfinity then\n"
    "    return Except.ok (cothFn x)\n"
    "  else\n"
    "    return Except.ok (tanhFn x)"
)


# =====================================================================
# ADMISSIBILITY — the frozen theorem carries NO precondition hypothesis (the
# modeled behavior is total, so `∀` is unguarded), so the nagini
# empty-precondition admission probe (case 2) has no binder to attack. The
# honest analogue: discharge the obligation at a ground input as a `have` (both
# arms covered by `by_cases`) alongside the frozen obligation, confirming the
# obligation is satisfiable at a normal input rather than only in the abstract.
# Nothing is assumed: no new declaration, statement byte-identical.
# Ports nagini case 2 (admiss-empty-precond).
# =====================================================================
_ADMISS_PROOF = (
    "  have _ground : problem_spec_cothReduce ⟨\"a\"⟩ ⟨\"b\"⟩\n"
    "      (implementation_cothReduce ⟨\"a\"⟩ ⟨\"b\"⟩) := by\n"
    "    unfold problem_spec_cothReduce implementation_cothReduce\n"
    "    by_cases h : cothFn ⟨\"b\"⟩ = complexInfinity\n"
    "    · simp only [Id.run, h, if_true]; rfl\n"
    "    · simp only [Id.run, h, if_false]; rfl\n"
) + _P_GOLD


# =====================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals. Each shares the frozen spec, keeps the
# frozen proof body (which no longer closes against the reshaped impl, so the
# module does NOT verify), and carries a refutation witness pinning the
# violation at one concrete input, checked to hold of the rival and fail on gold.
# =====================================================================

# WRONG-DISCRIMINATOR (the literal pre-patch bug): decide the branch off the
# value computed from the REMAINING part x instead of the periodic part m.
_WRONG_DISCR_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let cothx := cothFn x\n"
    "  if cothx = complexInfinity then\n"
    "    return Except.ok (cothFn x)\n"
    "  else\n"
    "    return Except.ok (tanhFn x)"
)
_WRONG_DISCR_WITNESS = (
    "-- Refuted where the dispatch off the PERIODIC part fires (cothFn m = ∞) but\n"
    "-- the value off the REMAINING part does not (cothFn x ≠ ∞): the spec then\n"
    "-- demands cothFn x, while the rival — branching off x — takes its else arm\n"
    "-- and returns tanhFn x. The two evaluators disagree on x. All three\n"
    "-- hypotheses are about DISTINCT opaque terms (or x on the finite side),\n"
    "-- so they are jointly satisfiable — matching the real coth(1+I*pi/2) leg.\n"
    "example (h1 : cothFn ⟨\"x1\"⟩ ≠ complexInfinity)\n"
    "        (h2 : cothFn ⟨\"m1\"⟩ = complexInfinity)\n"
    "        (h3 : cothFn ⟨\"x1\"⟩ ≠ tanhFn ⟨\"x1\"⟩) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"x1\"⟩ ⟨\"m1\"⟩\n"
    "      (implementation_cothReduce ⟨\"x1\"⟩ ⟨\"m1\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, h2, if_pos, if_neg h1, pure]\n"
    "  intro h\n"
    "  exact h3 (Except.ok.inj h).symm\n"
)

# SWAPPED RETURNS: keep the correct dispatch off m but return the wrong
# evaluator on each arm (bodies swapped).
_SWAP_RET_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let cothm := cothFn m\n"
    "  if cothm = complexInfinity then\n"
    "    return Except.ok (tanhFn x)\n"
    "  else\n"
    "    return Except.ok (cothFn x)"
)
_SWAP_RET_WITNESS = (
    "-- Refuted on the sentinel arm (cothFn m = ∞), where the spec demands\n"
    "-- cothFn x but the swapped rival returns tanhFn x. The two evaluators\n"
    "-- disagree on x. Distinct opaque terms → jointly satisfiable.\n"
    "example (h1 : cothFn ⟨\"ms\"⟩ = complexInfinity)\n"
    "        (h3 : cothFn ⟨\"xs\"⟩ ≠ tanhFn ⟨\"xs\"⟩) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"xs\"⟩ ⟨\"ms\"⟩\n"
    "      (implementation_cothReduce ⟨\"xs\"⟩ ⟨\"ms\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, h1, if_pos, pure]\n"
    "  intro h\n"
    "  exact h3 (Except.ok.inj h).symm\n"
)

# NON-COMPLETION: take the sentinel arm but yield no value — the outcome channel
# reports a computation that did not complete instead of the pinned value. This
# rival exists only on this carrier: the nagini sibling returns a bare int and
# has no outcome channel to abuse, so there is no nagini case to port here (see
# the module `assessment`).
_NO_COMPLETE_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let cothm := cothFn m\n"
    "  if cothm = complexInfinity then\n"
    "    return Except.error ()\n"
    "  else\n"
    "    return Except.ok (tanhFn x)"
)
_NO_COMPLETE_WITNESS = (
    "-- Refuted on the sentinel arm (cothFn m = ∞), where the spec demands the\n"
    "-- reduction COMPLETE with cothFn x, but the rival reports a computation that\n"
    "-- did not complete. `Except.noConfusion` separates the two outcome\n"
    "-- constructors without needing to know either evaluator's value, so this\n"
    "-- witness assumes only the arm selection — a single hypothesis about a single\n"
    "-- opaque term, hence trivially satisfiable.\n"
    "example (h1 : cothFn ⟨\"mn\"⟩ = complexInfinity) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"xn\"⟩ ⟨\"mn\"⟩\n"
    "      (implementation_cothReduce ⟨\"xn\"⟩ ⟨\"mn\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, h1, if_pos, pure]\n"
    "  exact fun h => Except.noConfusion h\n"
)

# NON-COMPLETION on the OTHER arm: take the finite arm but yield no value. The
# completion clause has to hold on BOTH arms, and the sentinel-arm non-completion
# rival above leaves the finite arm's half of it unattacked — a rival that
# completes correctly whenever the dispatch fires and declines only on the
# complementary arm would otherwise go unnoticed. Added by audit (no nagini
# counterpart, for the same carrier reason as its sibling).
_NO_COMPLETE_FIN_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let cothm := cothFn m\n"
    "  if cothm = complexInfinity then\n"
    "    return Except.ok (cothFn x)\n"
    "  else\n"
    "    return Except.error ()"
)
_NO_COMPLETE_FIN_WITNESS = (
    "-- Refuted on the FINITE arm (cothFn m ≠ ∞), where the spec demands the\n"
    "-- reduction COMPLETE with tanhFn x, but the rival reports a computation that\n"
    "-- did not complete. `Except.noConfusion` separates the two outcome\n"
    "-- constructors without knowing either evaluator's value, so the witness\n"
    "-- assumes only the arm selection — one hypothesis about one opaque term,\n"
    "-- hence trivially satisfiable. Against the frozen impl the same script\n"
    "-- reduces the spec side to `True` (the equation is PROVED there), which is\n"
    "-- why the frozen build fails for a SEMANTIC reason and not a syntactic one.\n"
    "example (h1 : cothFn ⟨\"mq\"⟩ ≠ complexInfinity) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"xq\"⟩ ⟨\"mq\"⟩\n"
    "      (implementation_cothReduce ⟨\"xq\"⟩ ⟨\"mq\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, if_neg h1, pure]\n"
    "  exact fun h => Except.noConfusion h\n"
)


# CONSTANT / always-first-evaluator: ignore the dispatch, always return cothFn x.
_CONST_PRIMARY_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr :=\n"
    "  Except.ok (cothFn x)"
)
_CONST_PRIMARY_WITNESS = (
    "-- Refuted on the FINITE arm (cothFn m ≠ ∞), where the spec demands tanhFn x\n"
    "-- but the constant rival returns cothFn x. This is the ONLY reject witness\n"
    "-- exercising the finite arm, so it attacks the second top-level clause.\n"
    "-- The two evaluators disagree on x; distinct opaque terms → satisfiable.\n"
    "-- The rewrite list carries `Id.run`/`pure` even though THIS rival has no\n"
    "-- do-block: the same snippet is elaborated against the FROZEN impl too, and\n"
    "-- there the spec side must be reduced past `Id.run` before the outcome\n"
    "-- constructor can be projected. Without them the frozen build fails on an\n"
    "-- unreduced `(pure _).run` term — a SYNTACTIC failure that would attest to\n"
    "-- nothing. With them the frozen build's hypothesis reduces to `True` (the\n"
    "-- equation is PROVED for the frozen impl) while against the rival it stays\n"
    "-- the concrete false equation `Except.ok (cothFn xf) = Except.ok (tanhFn xf)`.\n"
    "example (h2 : cothFn ⟨\"mf\"⟩ ≠ complexInfinity)\n"
    "        (h3 : cothFn ⟨\"xf\"⟩ ≠ tanhFn ⟨\"xf\"⟩) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"xf\"⟩ ⟨\"mf\"⟩\n"
    "      (implementation_cothReduce ⟨\"xf\"⟩ ⟨\"mf\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, if_neg h2, pure]\n"
    "  intro h\n"
    "  exact h3 (Except.ok.inj h)\n"
)

# CONSTANT / always-second-evaluator: ignore the dispatch, always return tanhFn x.
_CONST_SIBLING_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr :=\n"
    "  Except.ok (tanhFn x)"
)
_CONST_SIBLING_WITNESS = (
    "-- Refuted on the SENTINEL arm (cothFn m = ∞), where the spec demands\n"
    "-- cothFn x but the constant rival returns tanhFn x. The two evaluators\n"
    "-- disagree on x; distinct opaque terms → satisfiable.\n"
    "-- `Id.run`/`pure` are in the rewrite list for the frozen side's benefit (see\n"
    "-- the sibling constant rival): the snippet is elaborated against the FROZEN\n"
    "-- impl as well, and there the spec side has to reduce past `Id.run` before\n"
    "-- the outcome constructor can be projected. With them the frozen build's\n"
    "-- hypothesis reduces to `True` (PROVED for the frozen impl) while against\n"
    "-- the rival it stays the concrete false equation\n"
    "-- `Except.ok (tanhFn xc) = Except.ok (cothFn xc)`.\n"
    "example (h1 : cothFn ⟨\"mc\"⟩ = complexInfinity)\n"
    "        (h3 : cothFn ⟨\"xc\"⟩ ≠ tanhFn ⟨\"xc\"⟩) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"xc\"⟩ ⟨\"mc\"⟩\n"
    "      (implementation_cothReduce ⟨\"xc\"⟩ ⟨\"mc\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, if_pos h1, pure]\n"
    "  intro h\n"
    "  exact h3 (Except.ok.inj h).symm\n"
)

# VALUE-CORRUPTING REBIND: shadow the periodic binder m with the remaining part
# x before computing the dispatch — the value-typed analogue of clobbering the
# governing input; the branch then reads off x (same wrong data source as
# wrong-discriminator).
_REBIND_IMPL = (
    "def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do\n"
    "  let m := x\n"
    "  let cothm := cothFn m\n"
    "  if cothm = complexInfinity then\n"
    "    return Except.ok (cothFn x)\n"
    "  else\n"
    "    return Except.ok (tanhFn x)"
)
_REBIND_WITNESS = (
    "-- Refuted where the dispatch off the ORIGINAL periodic part fires\n"
    "-- (cothFn m = ∞) but the clobbered binder (now x) does not (cothFn x ≠ ∞):\n"
    "-- the spec — stated over the ORIGINAL m — demands cothFn x, while the rival\n"
    "-- tests x and returns tanhFn x. All hypotheses concern distinct opaque\n"
    "-- terms (or x on the finite side), so they are jointly satisfiable.\n"
    "example (h1 : cothFn ⟨\"mr\"⟩ = complexInfinity)\n"
    "        (h2 : cothFn ⟨\"xr\"⟩ ≠ complexInfinity)\n"
    "        (h3 : cothFn ⟨\"xr\"⟩ ≠ tanhFn ⟨\"xr\"⟩) :\n"
    "    ¬ problem_spec_cothReduce ⟨\"xr\"⟩ ⟨\"mr\"⟩\n"
    "      (implementation_cothReduce ⟨\"xr\"⟩ ⟨\"mr\"⟩) := by\n"
    "  unfold problem_spec_cothReduce implementation_cothReduce\n"
    "  simp only [Id.run, h1, if_pos, if_neg h2, pure]\n"
    "  intro h\n"
    "  exact h3 (Except.ok.inj h).symm\n"
)


SPEC_TESTS = [
    # ---------------- POSITIVE CONTROLS (soundness) ----------------
    {
        "id": "pos-control-demorgan-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _I_GOLD, _POS_DEMORGAN_IMPL),
            _P_GOLD, _POS_DEMORGAN_PROOF,
        ),
        "rationale": (
            "structurally-different but CORRECT impl: negates the dispatch test "
            "and swaps the two branch BODIES to match (De-Morgan-equivalent "
            "control flow), still anchored to the value off the periodic part m. "
            "Returns the identical value on every input, so both top-level "
            "clauses discharge. Straight-line two-way branch — no induction/lemma; "
            "the proof re-proves honestly (the negated test bridges via "
            "if_pos/if_neg, no axiom/sorry/helper introduced). Must verify; if it "
            "cannot, the dispatch clause is SPEC-TOO-STRONG. Ports nagini "
            "pos-control-demorgan-reorder."
        ),
    },
    {
        "id": "pos-control-inline-discriminator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _I_GOLD, _POS_INLINE_IMPL),
        "rationale": (
            "same gold behavior with the dispatch call inlined into the test (no "
            "cothm temporary). Determinism makes the inlined call denote the same "
            "value, so both clauses discharge and the FROZEN proof body still "
            "closes (the by_cases/simp/rfl shape is agnostic to the removed let). "
            "Must verify; if it cannot, the spec pins the temporary rather than "
            "the behavior (SPEC-TOO-STRONG). Ports nagini "
            "pos-control-inline-discriminator."
        ),
    },
    # ---------------- ADMISSIBILITY ----------------
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the frozen theorem carries no precondition hypothesis (the modeled "
            "behavior is total), so the honest analogue of the empty-precondition "
            "admission probe is to discharge the obligation at a ground input as a "
            "`have` (both dispatch arms covered) before closing the frozen "
            "obligation verbatim. Verifies (else the modeled behavior is "
            "unsatisfiable at a normal input — the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: no new declaration, statement byte-identical, the "
            "ground instance is a `have` inside the existing tactic body. Ports "
            "nagini admiss-empty-precond."
        ),
    },
    # ---------------- UNIQUENESS / SPEC-TOO-WEAK rivals ----------------
    {
        "id": "wrong-discriminator-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _WRONG_DISCR_IMPL),
        "refinement": (
            "this IS the pre-patch behavior: decide the branch off the value "
            "computed from the REMAINING part x instead of the periodic part m — "
            "the one-token data-source bug the patch fixes. On the F2P witness "
            "whose periodic part sends the dispatch to the sentinel arm while the "
            "remaining part's value is finite (coth(1+I*pi/2): the periodic part "
            "gives the sentinel, coth(1) is finite), the correct result is the "
            "first evaluator on x but this rival takes the else arm and returns "
            "the second — the wrong value. The F2P test asserts the correct value, "
            "so the faithful real patch would NOT resolve (the base commit does "
            "not even run — it NameErrors)."
        ),
        "rationale": (
            "REJECT from the dispatch clause: the postcondition pins result to the "
            "branch keyed on the value off m; a rival keyed on the value off x "
            "cannot satisfy it wherever those two values disagree on being the "
            "sentinel. If it verifies, the spec does not pin the discriminator's "
            "data source (SPEC-TOO-WEAK). Binder spread: dispatch on the SENTINEL "
            "arm (cothFn m = ∞), value off x finite."
        ),
        "witness": _WRONG_DISCR_WITNESS,
    },
    {
        "id": "swapped-returns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _SWAP_RET_IMPL),
        "refinement": (
            "keeps the correct dispatch off m but returns the wrong evaluator on "
            "each arm (bodies swapped). This inverts BOTH F2P witnesses: the "
            "sentinel-arm input would return the second evaluator instead of the "
            "first, and the finite-arm input the first instead of the second. The "
            "F2P test asserts the pinned direction, so a real patch that swapped "
            "the two returns would NOT resolve."
        ),
        "rationale": (
            "REJECT from the arm→evaluator mapping of both clauses: on the "
            "sentinel arm the spec demands the first evaluator on x but the rival "
            "returns the second; since the two evaluators are distinct opaque "
            "functions the implication fails. If it verifies, the branch-to-output "
            "mapping is unpinned (SPEC-TOO-WEAK). Refuted on the SENTINEL arm at "
            "an input distinct from every other rival."
        ),
        "witness": _SWAP_RET_WITNESS,
    },
    {
        "id": "non-completion-sentinel-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _NO_COMPLETE_IMPL),
        "refinement": (
            "on the sentinel arm the reduction reports that it did not complete "
            "and yields no value, instead of the pinned first-evaluator result. "
            "This is precisely the observable behavior the issue reports: for the "
            "arguments that route through this arm the reduction did not produce a "
            "value at all but escaped, which is why the reported call failed rather "
            "than returning a wrong answer. The F2P test asserts an equality "
            "between values, so a reduction that yields no value on that arm makes "
            "the assertion fail outright — the faithful real patch would NOT "
            "resolve. This rival has no nagini counterpart: nagini's carrier "
            "returns a bare int with no outcome channel, so non-completion is not "
            "even expressible there."
        ),
        "rationale": (
            "REJECT from the completion clause — the independent part of the "
            "postcondition that pins the OUTCOME CHANNEL (the result is a "
            "completed reduction carrying a value; the no-value outcome never "
            "occurs), as distinct from the two clauses that pin WHICH value. Every "
            "other rival here completes and is refuted only on the value it "
            "carries, so without this case the completion clause is attacked by "
            "nothing and a rival that simply declined to produce a value on one arm "
            "would go unnoticed. If it verifies, the spec does not actually forbid "
            "the no-value outcome (SPEC-TOO-WEAK). Refuted on the SENTINEL arm at "
            "an input distinct from every other rival's."
        ),
        "witness": _NO_COMPLETE_WITNESS,
    },
    {
        "id": "non-completion-finite-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _NO_COMPLETE_FIN_IMPL),
        "refinement": (
            "the complementary half of the completion clause: on the FINITE arm "
            "the reduction reports that it did not complete and yields no value, "
            "instead of the pinned second-evaluator result. The sentinel-arm "
            "non-completion rival leaves this half unattacked, so without this "
            "case a rival that answers correctly whenever the dispatch fires and "
            "escapes only on the complementary arm is unprobed — and the F2P "
            "witness that routes through the finite arm asserts an equality "
            "between values, which a reduction yielding no value fails outright, "
            "so the faithful real patch would NOT resolve. Added by audit; like "
            "its sibling it has no nagini counterpart, because nagini's carrier "
            "returns a bare int and has no outcome channel to decline on."
        ),
        "rationale": (
            "REJECT from the completion clause on the arm the sibling rival does "
            "not reach: the postcondition pins the outcome channel to a completed "
            "reduction on EVERY input, and this rival satisfies it on the sentinel "
            "arm while producing the no-value outcome on the finite arm. If it "
            "verifies, the spec forbids the no-value outcome only where the "
            "dispatch fires (SPEC-TOO-WEAK). Binder spread: the FINITE arm "
            "(cothFn m ≠ ∞) at an input distinct from every other rival's."
        ),
        "witness": _NO_COMPLETE_FIN_WITNESS,
    },
    {
        "id": "constant-always-primary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _CONST_PRIMARY_IMPL),
        "refinement": (
            "ignore the dispatch and always return the first evaluator on x. On "
            "the finite-arm F2P witness (whose result must be the second "
            "evaluator) it returns the first — the wrong value; the F2P test "
            "FAILS. A real patch dropping the else arm would not resolve."
        ),
        "rationale": (
            "REJECT from the FINITE-arm clause: the spec demands the second "
            "evaluator on x there, but the rival returns the first (distinct "
            "opaque functions), so the implication is violated. The only reject "
            "witness exercising the finite arm — it attacks the second top-level "
            "clause. If it verifies, the finite arm is unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _CONST_PRIMARY_WITNESS,
    },
    {
        "id": "constant-always-sibling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _CONST_SIBLING_IMPL),
        "refinement": (
            "the complementary degenerate rival: ignore the dispatch and always "
            "return the second evaluator on x. On the sentinel-arm F2P witness "
            "(whose result must be the first evaluator) it returns the second; the "
            "F2P test FAILS. A real always-second-evaluator patch would not "
            "resolve."
        ),
        "rationale": (
            "REJECT from the SENTINEL-arm clause: the spec demands the first "
            "evaluator on x there, but the rival returns the second (distinct "
            "opaque functions), violating the implication. Complements "
            "constant-always-primary. If it verifies, the sentinel arm is unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _CONST_SIBLING_WITNESS,
    },
    {
        "id": "value-corrupting-rebind-m",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GOLD, _REBIND_IMPL),
        "refinement": (
            "the value-typed analogue of a frame mutation: shadow the governing "
            "periodic binder m with the remaining part x before computing the "
            "dispatch, so the branch is decided off x (identical wrong data source "
            "to wrong-discriminator). On the sentinel-arm F2P witness it returns "
            "the wrong arm's value; the F2P test FAILS. A real patch overwriting "
            "the periodic part with the remaining part before the test would not "
            "resolve."
        ),
        "rationale": (
            "REJECT from the dispatch clause, which is stated over the ORIGINAL "
            "argument m: shadowing the local m does not change what the "
            "postcondition means, so the rival effectively tests the value off x "
            "and cannot prove the m-keyed clauses. Confirms a 'mutate the "
            "governing input' trick is rejected by the value abstraction (no "
            "vacuous satisfaction). If it verifies, SPEC-TOO-WEAK."
        ),
        "witness": _REBIND_WITNESS,
    },
]


# No AXIOM lane here: the bundle consumes no `axiom`. The three `opaque`
# declarations (the two evaluators and the sentinel) are A-reference callees
# validated executably by G-AX/G-CONF, not consumed contracts. The nagini
# AXIOM_TESTS (determinism/singleton soundness + callee-domain containment)
# belong to G-AX; this gate ignores them and they are dropped.
AXIOM_TESTS = []
