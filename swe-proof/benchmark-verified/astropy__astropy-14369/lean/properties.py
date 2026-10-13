"""properties.py — G-PBT falsification battery for astropy__astropy-14369 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``axiom``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior: combining an ordered chain of terms
under the quotient operator, over an arbitrary commutative group ``G``):

  divChain (head : G) (rest : List G) : G
    result = head / rest.prod

The whole content of the spec is that single closed form: the leading term
divided by the PRODUCT of every following term, in one flat left-associated
chain. There are two input binders — ``head`` (the leading term) and ``rest``
(the ordered list of following terms) — and no precondition hypothesis (the
behavior is total, so the ``∀`` in ``correct_divChain`` is unguarded).

ADVERSARIAL READ of the classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the inputs carry no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini frame-mutation rival
    (write back into the read-only input list) has no expressible instance here;
    no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    inputs (an equality against ``head / rest.prod``, built only from the two
    binders and the group operations, fully unfolded); the bundle declares no
    ``opaque``/``axiom`` (the group operations are Mathlib's ``CommGroup`` laws),
    so there is no answer key an implementation could echo without doing the
    work. In its place the battery carries an honest cheapest-reshape POSITIVE
    CONTROL (``pos-*``) that must verify, plus an ADMISSIBILITY control pinning
    satisfiability at the normal inputs the behavior is exercised on.

  * ASSOCIATIVITY / PARTIAL-DOMAIN / VALUE — APPLIES. The observable is the
    single combined group element. The reported defect is that a chain of three
    or more terms nested its quotients on the WRONG side; the rivals below attack
    the closed form directly — one reproduces the reported mis-association, two
    mis-handle a single boundary term (the trailing term / the leading term), and
    one mis-handles a single INTERIOR term, each agreeing with the spec everywhere
    else. The interior rival was added by audit: the other three are each refuted
    at an arity ≤ 2, where every chain position is a boundary, so none of them
    probes a term that is neither first nor last.

BINDER COVERAGE. Both input binders are varied across the reject witnesses:

  * ``rest`` — length 2 (``weak-right-assoc``), length 1
    (``weak-last-term-flip``), length 0 (``weak-head-inverted``) and length 3
    (``weak-interior-term-flip``). The associativity defect only becomes
    observable at length ≥ 2, the trailing-term defect at length ≥ 1, the
    leading-term defect is isolated at length 0 (where the other two rivals agree
    with the spec), and the INTERIOR-position defect is isolated at length 3
    (where all three of the others agree with the spec), so ``rest`` is
    load-bearing across its whole length domain rather than at one arity. The
    length-3 case matters on its own: a rival that mis-handles a term which is
    neither the leading nor the trailing one is invisible to every witness of
    length ≤ 2, since at those arities every position IS a boundary.
  * ``head`` — three DISTINCT non-identity values across the three rivals
    (``ofAdd 1``, ``ofAdd 2``, ``ofAdd 3``). ``head`` is made load-bearing by
    ``weak-head-inverted``, which is refuted at ``rest = []`` where the result
    depends on nothing BUT ``head`` — a rival that mishandled only the leading
    term would be invisible to any witness whose ``head`` were fixed at the
    identity, so the leading-term binder is abused at a point the closed form
    reads solely from it.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (an accumulator induction tuned
to the frozen ``for``-loop form) breaks on any reshape — so a rejection alone
attributes nothing to the spec. Every ``expect="reject"`` case therefore carries
a Lean snippet proving the rival CONTRADICTS the spec at one concrete input over
the small carrier ``Multiplicative (ZMod 5)`` (a finite commutative group, so
``decide`` closes it). Each was checked to ELABORATE against its rival and to
FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references records the
``CommGroup`` A-reference; the axiom-soundness / axiom-containment obligation
belongs to G-AX, not this gate.

PORTED FROM NAGINI. nagini case (1) pos-control-forward-fold →
``pos-mul-inverse-form``; (2) admissibility-f2p-shaped →
``admiss-ground-instances``; (4) prepatch-alternating-parity (the actual
differential — the un-fixed right-grouped reduction) → ``weak-right-assoc``;
(5) partial-domain-last-operand → ``weak-last-term-flip``; (6)
all-minus-one-head-flip → ``weak-head-inverted``. nagini case (3)
frame-mutation-write-units is VACUOUS here (see above) and is deliberately not
ported. See ``assessment`` in the submitted payload.

ADDED BY AUDIT (not a nagini port): ``weak-interior-term-flip``, covering the
interior-position sub-domain that all four ported cases leave unprobed. Also
corrected in audit: ``weak-right-assoc``'s rationale previously stated the
right-nesting closed form with the first following term as a FACTOR and the
second as a divisor (`head · rest₀ · rest₁⁻¹`). Evaluated over
``Multiplicative (ZMod 5)`` the rival is the other alternation
(`head · rest₀⁻¹ · rest₁`, i.e. `ofAdd 2` at the witness point, not `ofAdd 0`);
the case's OUTCOME was always correct and its witness always discriminated — only
the prose naming the divergence was wrong.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14369"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the one impl region and the FULL tactic body of the one proof
# region, so every replacement lands entirely inside the region it edits.
_IMPL = (
    "  let mut acc := head\n"
    "  for u in rest do\n"
    "    acc := acc / u\n"
    "  return acc"
)
_PROOF = (
    "theorem correct_divChain {G : Type*} [CommGroup G] :\n"
    "    ∀ (head : G) (rest : List G),\n"
    "      problem_spec_divChain head rest (implementation_divChain head rest) := by\n"
    "  have helper : ∀ (rest : List G) (acc : G),\n"
    "      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by\n"
    "    intro rest\n"
    "    induction rest with\n"
    "    | nil => intro acc; simp [Id.run, pure]\n"
    "    | cons a as ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      rw [ih]\n"
    "      simp [div_div]\n"
    "  intro head rest\n"
    "  unfold problem_spec_divChain implementation_divChain\n"
    "  exact helper rest head"
)

assert _IMPL in _BASE and _BASE.count(_IMPL) == 1, "impl anchor drift / not unique"
assert _PROOF in _BASE and _BASE.count(_PROOF) == 1, "proof anchor drift / not unique"


# Proof body re-authored for the `acc * u⁻¹` reshape (the frozen `simp [div_div]`
# is tuned to the `acc / u` update; the multiply-by-inverse form needs the
# `div_eq_mul_inv`/`mul_inv` rewrite + `group`, all Mathlib lemmas — no new
# declaration, no assumption, the theorem STATEMENT is byte-identical).
_PROOF_MULINV = (
    "theorem correct_divChain {G : Type*} [CommGroup G] :\n"
    "    ∀ (head : G) (rest : List G),\n"
    "      problem_spec_divChain head rest (implementation_divChain head rest) := by\n"
    "  have helper : ∀ (rest : List G) (acc : G),\n"
    "      Id.run (forIn rest acc (fun u r => (pure (.yield (r * u⁻¹)) : Id (ForInStep G)))) = acc / rest.prod := by\n"
    "    intro rest\n"
    "    induction rest with\n"
    "    | nil => intro acc; simp [Id.run, pure]\n"
    "    | cons a as ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      rw [ih, List.prod_cons]\n"
    "      simp only [div_eq_mul_inv, mul_inv]\n"
    "      group\n"
    "  intro head rest\n"
    "  unfold problem_spec_divChain implementation_divChain\n"
    "  exact helper rest head"
)

# Admissibility proof body: three ground instances discharged by evaluation over
# the finite carrier, THEN the frozen obligation closed verbatim. Nothing is
# assumed — the ground facts are `have`s inside the tactic body and the theorem
# statement is unchanged.
_PROOF_ADMISS = (
    "theorem correct_divChain {G : Type*} [CommGroup G] :\n"
    "    ∀ (head : G) (rest : List G),\n"
    "      problem_spec_divChain head rest (implementation_divChain head rest) := by\n"
    "  have _g_single : problem_spec_divChain (Multiplicative.ofAdd (1 : ZMod 5)) []\n"
    "      (implementation_divChain (Multiplicative.ofAdd (1 : ZMod 5)) []) := by\n"
    "    unfold problem_spec_divChain implementation_divChain; decide\n"
    "  have _g_inv : problem_spec_divChain (1 : Multiplicative (ZMod 5)) [Multiplicative.ofAdd (2 : ZMod 5)]\n"
    "      (implementation_divChain (1 : Multiplicative (ZMod 5)) [Multiplicative.ofAdd (2 : ZMod 5)]) := by\n"
    "    unfold problem_spec_divChain implementation_divChain; decide\n"
    "  have _g_long : problem_spec_divChain (Multiplicative.ofAdd (1 : ZMod 5))\n"
    "      [Multiplicative.ofAdd (2 : ZMod 5), Multiplicative.ofAdd (3 : ZMod 5), Multiplicative.ofAdd (4 : ZMod 5)]\n"
    "      (implementation_divChain (Multiplicative.ofAdd (1 : ZMod 5))\n"
    "        [Multiplicative.ofAdd (2 : ZMod 5), Multiplicative.ofAdd (3 : ZMod 5), Multiplicative.ofAdd (4 : ZMod 5)]) := by\n"
    "    unfold problem_spec_divChain implementation_divChain; decide\n"
    "  have helper : ∀ (rest : List G) (acc : G),\n"
    "      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by\n"
    "    intro rest\n"
    "    induction rest with\n"
    "    | nil => intro acc; simp [Id.run, pure]\n"
    "    | cons a as ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      rw [ih]\n"
    "      simp [div_div]\n"
    "  intro head rest\n"
    "  unfold problem_spec_divChain implementation_divChain\n"
    "  exact helper rest head"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct reshape cannot
    # satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps the
    # `theorem correct_divChain` statement byte-identical and re-proves for the
    # reshaped update; introduces no helper lemma beyond the in-body `have`, no
    # axiom, no assumption token. Ports nagini case (1) pos-control-forward-fold.
    # =====================================================================
    {
        "id": "pos-mul-inverse-form",
        "kind": "soundness",
        "expect": "verify",
        # Combine each following term by multiplying its inverse (`acc * u⁻¹`)
        # instead of dividing (`acc / u`). Identical value at every step
        # (`a / b = a * b⁻¹`), so the closed form is unchanged; the frozen
        # `simp [div_div]` is tuned to the division update, so the obligation is
        # re-proved with the inverse-form rewrite (Mathlib `div_eq_mul_inv` /
        # `mul_inv` + `group`), statement byte-identical.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "  let mut acc := head\n"
                "  for u in rest do\n"
                "    acc := acc * u⁻¹\n"
                "  return acc",
            ),
            _PROOF, _PROOF_MULINV,
        ),
        "rationale": "combining each following term as `acc * u⁻¹` rather than "
                     "`acc / u` is the same group value at every step "
                     "(`a / b = a * b⁻¹`), so the result equals `head / rest.prod` "
                     "exactly — the sole spec clause. A correct reshape must "
                     "verify, else the spec is SPEC-TOO-STRONG. Proof re-authored "
                     "because the frozen `simp [div_div]` keys on the division "
                     "update; the inverse form is closed with `div_eq_mul_inv` / "
                     "`mul_inv` + `group` (Mathlib lemmas, no new declaration).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal inputs the behavior is exercised
    # on. The frozen theorem carries NO precondition hypothesis (the behavior is
    # total), so the nagini precondition-admission probe has no binder to attack;
    # the honest analogue discharges the spec predicate at three ground inputs —
    # a single-term chain (empty `rest`), the leading-identity inverse case
    # (`head = 1`, one following term, i.e. the `/x` boundary), and a long chain
    # — by evaluation inside the proof region, alongside the frozen obligation.
    # If any ground instance could not be discharged, the behavior would be
    # unsatisfiable at an input it must admit (the analogue of PRECOND-TOO-STRONG).
    # Ports nagini case (2) admissibility-f2p-shaped.
    # =====================================================================
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _PROOF_ADMISS),
        "rationale": "the obligation is discharged at three ground inputs by "
                     "evaluation over a finite commutative group — a single-term "
                     "chain (empty following list), the leading-identity single "
                     "inverse case (the `/x` boundary), and a length-3 chain — "
                     "then the frozen obligation is closed verbatim. Verifies "
                     "(else the behavior is unsatisfiable at a normal input it "
                     "must admit). Nothing is assumed: the ground instances are "
                     "`have`s inside the tactic body and the theorem statement is "
                     "byte-identical.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one concrete
    # input over `Multiplicative (ZMod 5)`.
    # =====================================================================
    {
        "id": "weak-right-assoc",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ACTUAL DIFFERENTIAL: the un-fixed reduction nests the quotients on
        # the RIGHT — the following terms first combine among themselves
        # (rightmost innermost) and only that combined term divides the head. For
        # a chain of ≥ 2 following terms this is
        # `head / (rest₀ / (rest₁ / (rest₂ / …)))`, whose closed form is
        # `head · rest₀⁻¹ · rest₁ · rest₂⁻¹ · …` — the following terms ALTERNATE
        # in sign rather than all dividing, which is the sign-jumbling the report
        # describes. Ports nagini case (4) prepatch-alternating-parity, whose
        # `(-1)**i` parity is exactly this alternation.
        "module": _swap(
            _BASE, _IMPL,
            "  let mut acc := (1 : G)\n"
            "  for u in rest.reverse do\n"
            "    acc := u / acc\n"
            "  return head / acc",
        ),
        "refinement": "this is precisely the pre-fix behavior the issue reports "
                      "as 'jumbled': a chain of three or more terms nests the "
                      "quotients on the wrong side, so the trailing terms acquire "
                      "the wrong sign. On the F2P chain of length ≥ 2 (the "
                      "km/s/Mpc-shaped input) it produces the mis-associated value "
                      "the report shows, so a faithful patch retaining the "
                      "right-nesting reduction would still parse the chain wrongly "
                      "and NOT resolve the failing grammar test.",
        "rationale": "REJECT from the sole spec clause `result = head / "
                     "rest.prod`: the right-nesting reduction yields "
                     "`head / (rest₀ / (rest₁ / (rest₂ / …)))`, i.e. the closed "
                     "form `head · rest₀⁻¹ · rest₁ · rest₂⁻¹ · …` — the following "
                     "terms alternate in sign from the FIRST one onward instead of "
                     "all dividing. At head `ofAdd 1` and rest "
                     "`[ofAdd 2, ofAdd 3]` that is `head / rest₀ · rest₁`, which "
                     "differs from the required `head / (rest₀ · rest₁)` whenever "
                     "`rest₁ ≠ rest₁⁻¹`; over `Multiplicative (ZMod 5)` the rival "
                     "gives `ofAdd 2` where the spec requires `ofAdd 1`. This is "
                     "the discriminating clause the fix turns on; if it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_divChain\n"
            "    (Multiplicative.ofAdd (1 : ZMod 5))\n"
            "    [Multiplicative.ofAdd (2 : ZMod 5), Multiplicative.ofAdd (3 : ZMod 5)]\n"
            "    (implementation_divChain\n"
            "      (Multiplicative.ofAdd (1 : ZMod 5))\n"
            "      [Multiplicative.ofAdd (2 : ZMod 5), Multiplicative.ofAdd (3 : ZMod 5)]) := by\n"
            "  unfold problem_spec_divChain implementation_divChain\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-last-term-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss: divides by every following term EXCEPT the
        # last, which it MULTIPLIES instead (mis-signs the trailing term). Agrees
        # with the spec on the head and every interior term, so it passes the easy
        # sub-domain but mis-handles the trailing term of every chain of length
        # ≥ 1. Ports nagini case (5) partial-domain-last-operand.
        "module": _swap(
            _BASE, _IMPL,
            "  let mut acc := head\n"
            "  for u in rest.dropLast do\n"
            "    acc := acc / u\n"
            "  match rest.getLast? with\n"
            "  | some l => return acc * l\n"
            "  | none => return acc",
        ),
        "refinement": "multiplying by the trailing term instead of dividing "
                      "mis-signs the last term of the chain: on a chain whose "
                      "final term is a genuine divisor (the trailing `/kpc2`-style "
                      "term of the reported input) the result carries that term "
                      "with the wrong sign. The F2P oracle pins the trailing term "
                      "as a divisor, so a faithful patch that keeps the trailing "
                      "term as a factor reports the wrong unit and would NOT "
                      "resolve — even though it is correct on the head and all "
                      "interior terms.",
        "rationale": "REJECT from `result = head / rest.prod`: at head `ofAdd 2` "
                     "and the single-term rest `[ofAdd 3]` the rival returns "
                     "`head · rest₀` while the spec requires `head / rest₀`; these "
                     "differ whenever `rest₀ ≠ rest₀⁻¹`. Refuted at a chain where "
                     "the right-nesting rival AGREES with gold (a single trailing "
                     "term has nothing to re-associate), so this is a genuinely "
                     "distinct near-miss; if it verified => SPEC-TOO-WEAK "
                     "(partial-domain leak on the trailing term).",
        "witness": (
            "example : ¬ problem_spec_divChain\n"
            "    (Multiplicative.ofAdd (2 : ZMod 5))\n"
            "    [Multiplicative.ofAdd (3 : ZMod 5)]\n"
            "    (implementation_divChain\n"
            "      (Multiplicative.ofAdd (2 : ZMod 5))\n"
            "      [Multiplicative.ofAdd (3 : ZMod 5)]) := by\n"
            "  unfold problem_spec_divChain implementation_divChain\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-head-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss on the OTHER boundary: seeds the accumulator
        # with the INVERSE of the leading term, so the head is mis-signed while
        # every following term is combined correctly. Agrees with the spec on all
        # non-head structure but flips the leading term — visible even on a
        # single-term chain (empty `rest`, the `/x` boundary). Ports nagini case
        # (6) all-minus-one-head-flip.
        "module": _swap(
            _BASE, _IMPL,
            "  let mut acc := head⁻¹\n"
            "  for u in rest do\n"
            "    acc := acc / u\n"
            "  return acc",
        ),
        "refinement": "inverting the leading term flips the sign of the head unit "
                      "of the chain: the F2P/oracle pins the leading term as a "
                      "numerator, so a faithful patch that seeds the reduction "
                      "with the leading term's inverse reports it in the "
                      "denominator and would NOT resolve — including the "
                      "single-term chain boundary where the leading term is the "
                      "whole result.",
        "rationale": "REJECT from `result = head / rest.prod`: at head `ofAdd 3` "
                     "and empty rest the spec requires `result = head` but the "
                     "rival returns `head⁻¹`, which differ whenever `head ≠ "
                     "head⁻¹`. Refuted at `rest = []`, where the right-nesting and "
                     "trailing-term rivals both AGREE with gold (no following term "
                     "to mishandle) — so this isolates the leading-term binder "
                     "`head` and makes it load-bearing. If it verified => "
                     "SPEC-TOO-WEAK (leak on the leading term).",
        "witness": (
            "example : ¬ problem_spec_divChain\n"
            "    (Multiplicative.ofAdd (3 : ZMod 5))\n"
            "    ([] : List (Multiplicative (ZMod 5)))\n"
            "    (implementation_divChain\n"
            "      (Multiplicative.ofAdd (3 : ZMod 5))\n"
            "      ([] : List (Multiplicative (ZMod 5)))) := by\n"
            "  unfold problem_spec_divChain implementation_divChain\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-interior-term-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss on the INTERIOR, the sub-domain the other three
        # rivals leave unattacked. The three ported rivals are each refuted at a
        # BOUNDARY position (leading term at length 0, trailing term at length 1,
        # association at length 2) — and at every arity ≤ 2 every position of the
        # chain IS a boundary, so a defect that touches only a term which is
        # neither first nor last is invisible to all of them. This rival mis-signs
        # exactly chain position 2: it agrees with the spec on the leading term, on
        # the trailing term of every chain of length ≤ 2, and on the association of
        # every shorter chain, diverging first at length 3. Added by audit after
        # the interior sub-domain was found unprobed; the discrimination matrix was
        # measured (witness: rival 0 / gold 1; flipped claim: rival 1 / gold 0).
        "module": _swap(
            _BASE, _IMPL,
            "  let mut acc := head\n"
            "  for p in rest.zipIdx do\n"
            "    acc := if p.2 == 2 then acc * p.1 else acc / p.1\n"
            "  return acc",
        ),
        "refinement": "mis-signing one interior term of the chain reports that "
                      "single term on the wrong side of the quotient while every "
                      "boundary term is placed correctly. The oracle pins EVERY "
                      "following term as a divisor, not merely the first and last, "
                      "so a faithful patch that placed an interior term as a factor "
                      "would report the wrong combined result on any chain long "
                      "enough to have an interior — and would NOT resolve, despite "
                      "being correct on short chains and on both boundaries.",
        "rationale": "REJECT from `result = head / rest.prod`: at head `ofAdd 1` "
                     "and rest `[ofAdd 1, ofAdd 1, ofAdd 2]` the rival multiplies "
                     "by the third following term instead of dividing, giving "
                     "`ofAdd 1` where the spec requires `ofAdd 2`. Refuted at "
                     "length 3, where the right-nesting, trailing-term and "
                     "leading-term rivals ALL agree with gold — so this probes the "
                     "interior sub-domain none of them reaches and makes the spec's "
                     "quantification over every element of `rest` load-bearing "
                     "rather than only its endpoints. If it verified => "
                     "SPEC-TOO-WEAK (partial-domain leak on an interior term).",
        "witness": (
            "example : ¬ problem_spec_divChain\n"
            "    (Multiplicative.ofAdd (1 : ZMod 5))\n"
            "    [Multiplicative.ofAdd (1 : ZMod 5), Multiplicative.ofAdd (1 : ZMod 5),\n"
            "     Multiplicative.ofAdd (2 : ZMod 5)]\n"
            "    (implementation_divChain\n"
            "      (Multiplicative.ofAdd (1 : ZMod 5))\n"
            "      [Multiplicative.ofAdd (1 : ZMod 5), Multiplicative.ofAdd (1 : ZMod 5),\n"
            "       Multiplicative.ofAdd (2 : ZMod 5)]) := by\n"
            "  unfold problem_spec_divChain implementation_divChain\n"
            "  decide\n"
        ),
    },
]

# nagini case (3) frame-mutation-write-units is NOT ported: it exploits a
# read-only half-permission on the input list, which is a nagini-only
# (fractional-permission) construct. This backend's carrier is referentially
# transparent — the inputs carry no permission and there is no aliasing — so the
# rival has no expressible instance and no discriminating witness. Deliberately
# omitted rather than substituted; see the module docstring.
AXIOM_TESTS = []
