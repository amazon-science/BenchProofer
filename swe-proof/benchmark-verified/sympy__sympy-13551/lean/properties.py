"""properties.py — G-PBT falsification battery for sympy__sympy-13551 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a four-input domain):

  finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ
      result = ((List.range n).map (fun k => c + r k)).prod / q
    preconditions (binders of correct_*, NOT spec conjuncts):
      q ≠ 0                        — the divisor is nonzero
      ∀ k, k < n → c + r k ≠ 0     — every factor over the range is nonzero
                                     (a zero factor takes the real construct
                                      off the modeled slice, mapping.md)

  The single top-level clause pins the result to the GENUINE product of the
  additive term ``c + r k`` taken over EVERY position ``k < n`` of the range,
  divided by ``q``. There is no opaque callee and no answer-key: the product is
  spelled out structurally as ``List.map`` then ``List.prod`` over the actual
  inputs, so the result must be PRODUCED by the modeled reduction. The clause
  couples four inseparable sub-decisions, each pinned to a distinct binder:

    * the constant summand ``c`` enters every factor            (binder ``c``);
    * the range EXTENT — every position below ``n`` contributes, none beyond
                                                                (binder ``n``);
    * the position-dependent remainder ``r k`` enters each factor
                                                                (binder ``r``);
    * the final division is by the evaluated divisor            (binder ``q``).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its modeled list inputs are held at
    fractional (read-only) permission and a rival that overwrites one is
    rejected for insufficient permission. Lean is referentially transparent:
    the inputs are plain immutable values (``ℚ`` / ``ℕ`` / ``ℕ → ℚ``), there is
    no half-permission to violate and no aliasing to exploit, so this class has
    NO expressible instance here. No substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini refinement notes the model's
    reference fold (``prod_of_totals``) is GROUNDED in the args, not an opaque
    answer-key, so echoing it IS the correct answer. Same here: the spec's RHS
    is the structural product over the inputs, there is no opaque wrapper to
    echo (the bundle declares NO ``opaque``/``axiom``; mapping.md: none
    consumed). The honest analogue is the cheapest-correct POSITIVE CONTROL
    below (returning the product expression directly).

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE as a reject case, and the
    reason is narrower than "it cannot be written". A self-calling
    ``partial def implementation_finiteProduct`` IS writable and does pass the
    mechanical variant-scope check (measured: ``variant_problems`` returns []).
    What it cannot do is either half of a shippable reject case:
      - it does not verify — a ``partial def`` has no defining equation, so the
        frozen obligation cannot be discharged against it; and
      - it cannot be REFUTED by a witness either, for the same reason: the
        witness's ``unfold implementation_finiteProduct`` fails with
        ``Tactic `unfold` failed to unfold `implementation_finiteProduct``` —
        a TOOLING failure that attributes nothing to the spec, so the gate would
        record ``witness-unproven`` rather than a rejection.
    So there is nothing to attest here, but the class is not a spec hole either:
    this bundle carries NO ``set_option loom.semantics.termination`` line (the
    obligation is an ordinary Lean equation, not a Hoare triple with a
    termination side-condition), so an opaque ``partial`` impl gains no vacuous
    verification — it simply fails to verify. Recorded as an unattestable class
    rather than as a vacuous or a hole.

  * SUM-OF-PART-PRODUCTS (the pre-patch bug) — APPLIES, load-bearing. The
    pre-fix behavior assumes ``∏(c + r k) = c^n + ∏ r k`` (the buggy
    summand-wise shortcut the issue calls out). It is refuted directly on the
    F2P-shaped observable (product of a non-degenerate additive term), where it
    understates the true product.

  * PARTIAL-DOMAIN (empty-product constant; drop-first-index) — APPLY. An impl
    that returns the empty product regardless of the range, and one that skips
    the first range position, each violate the one clause on a strict
    sub-domain and are refuted with witnesses at distinct inputs.

  * REMAINDER MISALIGNMENT (shift-remainder-index) — APPLIES; added by audit,
    with no nagini analogue. Nagini's carrier passes the two multiplicand parts
    as index-ALIGNED lists, so "read the remainder at the wrong position" is not
    naturally expressible there; on this carrier ``r`` is a FUNCTION of the
    position, which makes the alignment a separately attackable sub-decision.
    Without it every rival either changed the range extent or the arithmetic
    shape, leaving ``r``'s argument the least-probed part of the clause.

  * DROP-DIVISOR — APPLIES, and is the binder-``q`` attacker. An impl that
    computes the genuine product but omits the final ``/ q`` division agrees
    with gold on the whole ``q = 1`` slice; it is refuted at ``q ≠ 1``, the
    only sub-domain where the divisor is observable.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input; each was built (against the rival) and rebuilt (against the
frozen solution) to confirm it HOLDS of its rival and FAILS on gold (so it
discriminates rather than asserting a tautology). ``decide`` stalls on ``Rat``
normalization, so each witness unfolds the spec + impl, reduces the range map
with ``List.range'`` / ``List.range_succ`` (and the ``List.prod`` cons lemmas),
then closes the concrete ``ℚ`` (in)equality with ``norm_num``.

Reducing the range map is what makes gold's failure a REFUTATION rather than a
stuck term, and it is checked, not assumed. The frozen impl's ``for k in [0:n]``
folds over ``List.range' 0 n``; a witness tactic that does not unfold that
leaves gold's goal at an unevaluated ``List.foldl … (List.range' 0 2)``, and
gold's build then fails because the fold was never computed — an exit code that
attributes nothing. The litmus for each witness is a TRUE refutation-shaped
claim about gold at the SAME input (``¬ spec … (impl … + 1)``, which gold does
satisfy): under a tactic that genuinely evaluates, that litmus ELABORATES, and
under a stalling one it fails with the same error as the witness. Every witness
below is confirmed on the evaluating side: gold's goal closes to a clean
``⊢ False`` and the litmus at the same input builds (exit 0).

Both halves of that litmus were RE-MEASURED during audit, and the second half
failed until the tactic was fixed, so it is recorded concretely:

  * the stalling direction is real. Dropping ``List.range'`` and reducing with
    ``List.range_succ`` alone leaves gold's goal at
    ``⊢ ¬List.foldl (fun b a => b * (1 + (↑a + 1))) 1 (List.range' 0 2) = 6``
    and the TRUE-claim litmus fails at the same unreduced fold — so that
    spelling discriminates nothing, exactly as claimed.
  * the OVER-shooting direction was also real, and was a defect. With a bare
    trailing ``norm_num``, the reducing ``simp`` had already closed the litmus
    goal and ``norm_num`` then errored ``No goals to be solved`` — the litmus
    "failed" for tactic-bookkeeping reasons rather than because of what it
    claimed. Guarding it as ``try norm_num`` fixes this: the litmus now
    elaborates (exit 0) while each real witness still fails on gold with
    ``unsolved goals ⊢ False``.

BINDER COVERAGE. All four input binders are varied across the reject witnesses:
  * ``c`` — refuted at ``c = 1`` (sum-of-parts) AND ``c = 2`` (empty-product,
    drop-first) AND ``c = 3`` (shift-remainder) AND ``c = 1`` at ``q = 2``
    (drop-divisor).
  * ``n`` — refuted at ``n = 1`` (empty-product, shift-remainder, drop-divisor)
    AND ``n = 2`` (sum-of-parts, drop-first), so the range extent is exercised
    at the single-position and the general step.
  * ``r`` — refuted at ``r k = k + 1`` (sum-of-parts), ``r k = 0``
    (empty-product, drop-divisor) AND ``r k = k`` (drop-first,
    shift-remainder): the remainder's contribution is exercised both for its
    VALUE and, via shift-remainder, for the POSITION it is read at.
  * ``q`` — refuted at ``q = 2`` (drop-divisor), varying it off the ``q = 1``
    value the other rivals hold, so the divisor clause is not pinned to 1.
``pts`` = 5 distinct input points.

OMITTED nagini cases (see assessment): the frame/permission-mutation rival
(VACUOUS on a referentially-transparent carrier — no fractional permission and
no aliasing exist to violate), the divergence lane (UNATTESTABLE here, see the
class note above: writable but neither verifiable nor refutable, and not a hole
because this bundle sets no ``loom.semantics.termination``), and the AXIOM_TESTS
lane (this bundle declares no axiom / deep-model reference — G-AX is a skip stub
— and the axiom lane is not this gate's job). The nagini "partial-domain
empty-only" and "partial-domain drop-first" rivals are BOTH ported; the nagini
sum-of-part-products rival is ported as the load-bearing pre-patch attacker.
Beyond the nagini design document this battery adds a ``r``-alignment rival
(shift-remainder-index) that the list-carrier sibling could not express.

SPEC PROBES run during audit and recorded here because a battery should say what
it FAILED to break. Seven wrong impls the battery does not contain were built
against the frozen spec — remainder shifted, constant summand dropped, divisor
MULTIPLIED instead of divided, one extra range position, the SUM of the factors
instead of the product, and two guard-shaped impls returning 0 on a degenerate
input — and all seven were REJECTED (none verified), so no spec hole was found
from that direction. Three faithful CORRECT reshapes (reversed multiplication
order, a `foldr` over the range, a `Finset.range` product) were each PROVEN
against the frozen obligation, and so were two guard-shaped correct impls whose
guard is unreachable under the preconditions (`if q = 0 then 0 else …`, and a
zero-product guard), so the spec is not too strong on that boundary either.

AXIOM lane: EMPTY. mapping.md records none consumed and no deep-model reference;
the range-product is modeled DEEPLY over the inputs, so there is no
axiom-soundness / axiom-containment obligation to probe here. AXIOM_TESTS is
empty.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13551"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do\n"
    "  let mut acc : ℚ := 1\n"
    "  for k in [0:n] do\n"
    "    acc := acc * (c + r k)\n"
    "  return acc / q"
)

_PROOF_BODY = (
    "  intro c n r q _ _\n"
    "  unfold problem_spec_finiteProduct implementation_finiteProduct\n"
    "  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Positive-control / rival impl bodies (each a full impl region; only the impl
# changes, so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL 1 (soundness) — cheapest honest impl: return the product
# expression directly (the spec RHS is grounded in the args, not an answer key,
# so this IS the correct value). Proof: after unfold the goal is `x = x`.
_POS_CHEAPEST_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ :=\n"
    "  ((List.range n).map (fun k => c + r k)).prod / q"
)
_POS_CHEAPEST_PROOF = (
    "  intro c n r q _ _\n"
    "  unfold problem_spec_finiteProduct implementation_finiteProduct\n"
    "  rfl"
)

# POSITIVE CONTROL 2 (soundness) — structurally-different but CORRECT, and the
# difference is OBSERVABLE TO THE VERIFIER, which is the whole point of a reshape
# control. It multiplies the factors in the OPPOSITE ORDER (the range map is
# reversed before the product), so closing the obligation genuinely requires the
# commutativity content — `List.prod_reverse` — rather than reduction alone.
#
# This replaced an earlier "bind the factor to a local `t`" reshape, which was
# measured DEFINITIONALLY EQUAL to the frozen impl: a standalone probe closed
# `goldImpl = localFactorImpl` by `rfl` (exit 0), i.e. `let t := c + r k;
# acc * t` and `acc * (c + r k)` are the same term after zeta-reduction. A
# variant that is defeq to gold re-runs the frozen proof against the frozen
# term, so it tests nothing while passing honestly. The reversed-order impl is
# NOT defeq (probe: `rfl` on `goldImpl = revImpl` fails with
# "is not definitionally equal to"), and the FROZEN proof body does NOT close it
# (measured: `unsolved goals … List.foldr … = List.foldl …`), so its own proof
# has to supply the commutativity step — a real re-proof of the obligation
# against a new impl shape.
_POS_RESHAPE_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ :=\n"
    "  (((List.range n).map (fun k => c + r k)).reverse.prod) / q"
)
_POS_RESHAPE_PROOF = (
    "  intro c n r q _ _\n"
    "  unfold problem_spec_finiteProduct implementation_finiteProduct\n"
    "  simp [List.prod_reverse]"
)

# ADMISSIBILITY — the frozen impl+proof, with a ground instance discharged at
# the F2P-shaped input (c=2, n=2, r k = (1/2)^k, q=1 → (2+1)*(2+1/2) = 15/2)
# BEFORE the frozen obligation, proving the modeled behavior is satisfiable at
# exactly the value the F2P exercises. The `have` lives inside the existing
# tactic body; no new declaration/axiom/sorry.
_ADMISS_PROOF = (
    "  have _ground : implementation_finiteProduct 2 2 (fun k => ((1:ℚ)/2)^k) 1 = 15/2 := by\n"
    "    unfold implementation_finiteProduct\n"
    "    simp [List.range']\n"
    "    norm_num\n"
    + _PROOF_BODY
)

# SUM-OF-PART-PRODUCTS (= the pre-patch bug): assumes ∏(c + r k) = c^n + ∏ r k.
_UNIQ_SUMPARTS_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ :=\n"
    "  (c ^ n + ((List.range n).map r).prod) / q"
)

# EMPTY-PRODUCT CONSTANT: ignore the range entirely, return the empty product / q.
_UNIQ_EMPTY_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ :=\n"
    "  1 / q"
)

# DROP-FIRST-INDEX: start the range at 1, never multiplying in the factor at k=0.
_UNIQ_DROPFIRST_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do\n"
    "  let mut acc : ℚ := 1\n"
    "  for k in [1:n] do\n"
    "    acc := acc * (c + r k)\n"
    "  return acc / q"
)

# SHIFT-REMAINDER-INDEX: read the remainder one position too far along
# (`r (k+1)` instead of `r k`) while keeping the range extent, the constant and
# the division all correct. Added by audit: the existing rivals attack the
# EXTENT of the range (empty-product, drop-first) and the arithmetic shape
# (sum-of-parts), but none of them keeps the extent right and misreads the
# remainder AT a position, so the `r` binder's per-position alignment was the
# least-probed sub-decision.
_UNIQ_SHIFTR_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do\n"
    "  let mut acc : ℚ := 1\n"
    "  for k in [0:n] do\n"
    "    acc := acc * (c + r (k+1))\n"
    "  return acc / q"
)

# DROP-DIVISOR: compute the genuine product but omit the final `/ q` division.
_UNIQ_NODIV_IMPL = (
    "def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do\n"
    "  let mut acc : ℚ := 1\n"
    "  for k in [0:n] do\n"
    "    acc := acc * (c + r k)\n"
    "  return acc"
)


def _witness(c, n, r, q, tac):
    return (
        f"example : ¬ problem_spec_finiteProduct {c} {n} {r} {q}\n"
        f"    (implementation_finiteProduct {c} {n} {r} {q}) := by\n"
        "  unfold problem_spec_finiteProduct implementation_finiteProduct\n"
        + tac
    )


# range-succ unfold + norm_num (decide stalls on Rat normalization).
#
# `List.range'` is load-bearing and NOT decoration. The frozen impl's
# `for k in [0:n]` elaborates to a fold over `List.range' 0 n`, which
# `List.range_succ` alone does NOT touch: without the `List.range'` unfolding
# the goal against the FROZEN solution stalls at
# `⊢ ¬List.foldl (fun b a => b * (c + r a)) 1 (List.range' 0 2) = v`
# — gold's build then fails because the fold was never EVALUATED, not because
# the concrete claim was refuted. Measured: with `simp [List.range_succ]` alone
# a TRUE claim about gold at these same inputs (`… (impl … + 1)`, which gold
# genuinely satisfies) fails with the identical unreduced-fold error, so that
# exit code discriminated nothing. With `List.range'` added, gold's fold
# reduces and the goal closes to a clean `⊢ False` — a SEMANTIC refutation of
# the concrete equality — while the same true-claim litmus elaborates (exit 0).
#
# `norm_num` is guarded by `try`. Without the guard, the reducing `simp` step
# sometimes closes the goal outright and the bare `norm_num` that follows then
# errors with `No goals to be solved` — a failure caused by the tactic script
# having nothing left to do, NOT by the claim being false. Measured on gold at
# these very inputs: the TRUE-claim litmus (`… (impl … + 1)`, which gold does
# satisfy) failed with `No goals to be solved` under the bare form, i.e. that
# exit code did not track the claim, while under `try norm_num` the same litmus
# ELABORATES (exit 0) and the real witness still fails on gold with `unsolved
# goals ⊢ False`. The guard is what makes the gold-side exit code carry
# information about WHAT is claimed rather than about tactic bookkeeping.
_WIT_TAC = "  simp [List.range', List.range_succ]\n  try norm_num\n"
# variant that reduces the map/prod explicitly then norm_num (used where `simp`
# alone would close the rival goal and leave norm_num with no goals)
_WIT_TAC_EXPLICIT = (
    "  simp only [List.range_succ, List.range_zero, List.map_cons, List.map_nil,\n"
    "    List.prod_cons, List.prod_nil, List.nil_append, List.cons_append]\n"
    "  norm_num\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — correct impls that MUST verify. If a
    # faithful correct impl cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_CHEAPEST_IMPL), _PROOF_BODY, _POS_CHEAPEST_PROOF),
        "rationale": (
            "the spec RHS is GROUNDED in the args (a structural product over the "
            "range, not an opaque answer-key), so returning it directly is the "
            "correct value. An honest cheapest impl MUST verify; if it cannot the "
            "postcondition is SPEC-TOO-STRONG. After `unfold` the goal is `x = x`, "
            "closed by `rfl`. This also serves as the grounded-oracle positive "
            "control: there is no WRONG echo because the RHS is a function of the "
            "inputs, not an answer key. No new declaration/axiom; STATEMENT "
            "byte-identical."
        ),
    },
    {
        "id": "pos-reshape-reversed-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_RESHAPE_IMPL), _PROOF_BODY, _POS_RESHAPE_PROOF),
        "rationale": (
            "structurally-different CORRECT impl whose difference is OBSERVABLE "
            "to the verifier: it multiplies the range factors in the OPPOSITE "
            "order (the mapped range is reversed before the product). Same value "
            "on every input (multiplication on ℚ is commutative), so it must "
            "verify — else SPEC-TOO-STRONG. It is NOT definitionally equal to the "
            "frozen impl (a standalone `rfl` on the two impls fails: 'is not "
            "definitionally equal to'), and the FROZEN proof body does NOT close "
            "it (`unsolved goals … List.foldr … = List.foldl …`), so the case "
            "supplies the commutativity step itself (`List.prod_reverse`) and "
            "genuinely RE-PROVES the obligation against a new shape rather than "
            "re-running the frozen proof on the frozen term. Theorem STATEMENT "
            "byte-identical; only the impl and tactic regions differ; no new "
            "declaration/axiom/assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the exact
    # value the F2P exercises. The frozen theorem's binders are preconditions
    # (q ≠ 0; every factor nonzero), both met at the F2P input, so this is the
    # honest analogue of nagini's precondition-admission probe.
    # =====================================================================
    {
        "id": "admiss-f2p-value",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the impl is discharged at the F2P ground input (c=2, n=2, "
            "r k = (1/2)^k, q=1) to the exact value 15/2 by `norm_num` over the "
            "reduced range fold, confirming the modeled behavior is satisfiable at "
            "the value the F2P test asserts (and the preconditions q ≠ 0 and every "
            "factor nonzero hold there); then the frozen obligation is closed "
            "verbatim. Verifies (else the spec is unsatisfiable at the normal "
            "input, the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
            "theorem STATEMENT is byte-identical, the ground instance is a `have` "
            "inside the existing tactic body, no new declaration/axiom/sorry. The "
            "ground `have` is DISCRIMINATING, not decorative, and this was "
            "measured rather than argued: replacing 15/2 with the summand-wise "
            "value the pre-fix shortcut would give at this input makes the case "
            "FAIL (`unsolved goals ⊢ False`), and so does keeping 15/2 while "
            "moving the input off the F2P shape to n=1. So the `have` pins this "
            "exact value at this exact input; it cannot be satisfied by a wrong "
            "one."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input,
    # confirmed to hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "uniq-sum-of-part-products",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNIQ_SUMPARTS_IMPL),
        "refinement": (
            "this is the pre-patch behavior: it assumes the product of an "
            "additive term equals the summand-wise shortcut c^n + ∏ r k — exactly "
            "the false identity the issue calls out (and which the gold change "
            "exists to remove). On the F2P observable (a non-degenerate additive "
            "term over the range) it understates the true product, so it does NOT "
            "resolve — it is the literal bug, not the fix."
        ),
        "rationale": (
            "REJECT from the clause result = (∏_{k<n}(c + r k)) / q. At c=1, n=2, "
            "r k = k+1, q=1 the genuine product is (1+1)*(1+2)=6, but the rival "
            "computes 1^2 + (1*2) = 3. The Ensures cannot hold. Refuted with "
            "c=1, n=2, r k = k+1 — exercising c, the general range step, and a "
            "position-dependent remainder. If it verifies, the spec permits the "
            "summand-wise shortcut (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("1", "2", "(fun k => (k:ℚ)+1)", "1", _WIT_TAC),
    },
    {
        "id": "uniq-empty-product-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNIQ_EMPTY_IMPL),
        "refinement": (
            "returns the empty product (1) over q regardless of the range, doing "
            "no work — exactly the nonsense the issue hints at (a finite product "
            "of a non-polynomial additive term collapsing to 1). It is correct "
            "only on the empty range (n=0); for any non-empty input it is wrong. "
            "A real patch returning the empty product would not resolve (F2P needs "
            "15/2, this gives 1/2)."
        ),
        "rationale": (
            "REJECT from the clause result = (∏_{k<n}(c + r k)) / q. At c=2, n=1, "
            "r k = 0, q=1 the spec demands the single factor (2+0)=2, but the "
            "rival returns 1. Refuted with n=1 (the general non-empty step, off "
            "the empty sub-domain where it agrees) and r k = 0. If it verifies, "
            "the spec does not force the range factors into the result "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness("2", "1", "(fun _ => (0:ℚ))", "1", _WIT_TAC_EXPLICIT),
    },
    {
        "id": "uniq-drop-first-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNIQ_DROPFIRST_IMPL),
        "refinement": (
            "off-by-one lower bound: the range starts at 1 instead of 0, so the "
            "factor at position k=0 is never multiplied in — it drops one factor "
            "of the genuine product. Correct only when that first factor is 1 (a "
            "measure-zero sub-domain); on the F2P shape it omits a real factor. A "
            "real patch that skipped the first range position would not resolve."
        ),
        "rationale": (
            "REJECT from the clause result = (∏_{k<n}(c + r k)) / q. At c=2, n=2, "
            "r k = k, q=1 the spec multiplies positions 0 and 1: (2+0)*(2+1)=6, but the "
            "rival starts at 1 and returns (2+1)=3, omitting the k=0 factor. "
            "Refuted with r k = k (a distinct remainder from the other witnesses) "
            "at the general two-position range. If it verifies, the spec leaves "
            "the first range position unpinned (partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": _witness("2", "2", "(fun k => (k:ℚ))", "1", _WIT_TAC),
    },
    {
        "id": "uniq-shift-remainder-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNIQ_SHIFTR_IMPL),
        "refinement": (
            "misaligns the remainder against the range position: it evaluates the "
            "position-dependent remainder one step further along than the position "
            "being multiplied in, so every factor is drawn from the wrong point of "
            "the range while the extent, the constant summand and the final "
            "division all stay right. A patch shaped this way reports the product "
            "of a shifted term rather than of the term the construct names, so it "
            "does not resolve: on the F2P shape the very first factor is already "
            "wrong."
        ),
        "rationale": (
            "REJECT from the clause result = (∏_{k<n}(c + r k)) / q — specifically "
            "from `r k` being evaluated AT the multiplied position. At c=3, n=1, "
            "r k = k, q=1 the spec demands the single factor (3 + r 0) = 3, but "
            "the rival multiplies in (3 + r 1) = 4. Refuted at n=1, which pins the "
            "misalignment on a single position with no cancellation available. "
            "This is the `r`-binder ALIGNMENT attacker: the other rivals vary the "
            "range extent or the arithmetic shape, none keeps the extent correct "
            "while reading the remainder at the wrong position. If it verifies, "
            "the spec does not tie r's argument to the range position "
            "(SPEC-TOO-WEAK on the r binder)."
        ),
        "witness": _witness("3", "1", "(fun k => (k:ℚ))", "1", _WIT_TAC),
    },
    {
        "id": "uniq-drop-divisor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNIQ_NODIV_IMPL),
        "refinement": (
            "computes the genuine range-product correctly but omits the final "
            "division by the evaluated divisor q. It agrees with gold on the whole "
            "q=1 slice and diverges only when q ≠ 1 — but the real construct's "
            "final step IS the division p / q, so a patch that dropped it would "
            "report the un-divided numerator and not resolve (F2P divides by the "
            "collapsed denominator)."
        ),
        "rationale": (
            "REJECT from the division in result = (∏_{k<n}(c + r k)) / q. At c=1, "
            "n=1, r k = 0, q=2 the spec demands (1+0)/2 = 1/2, but the rival "
            "returns 1. Refuted with q=2 — varying the divisor off the q=1 value "
            "every other rival holds, so the divisor sub-decision is demonstrably "
            "pinned. If it verifies, the spec does not force the final division "
            "(SPEC-TOO-WEAK on the q binder)."
        ),
        "witness": _witness("1", "1", "(fun _ => (0:ℚ))", "2", _WIT_TAC_EXPLICIT),
    },
]


# No consumed axioms and no deep-model references: the range-product is modeled
# directly over the inputs (List.map then List.prod), so there is no in-model
# axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
