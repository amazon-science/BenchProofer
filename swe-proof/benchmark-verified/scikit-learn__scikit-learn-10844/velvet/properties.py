"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-10844 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct fowlkesCoeffSquared`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  fowlkesCoeffSquared (width : Nat) (agree spreadA spreadB : Word width)
      return (out : Option (RatPlan × Rat))
    require 2 ≤ width
    require inWord width agree.toExact
    require inWord width spreadA.toExact
    require inWord width spreadB.toExact
    require agree.toExact ≤ spreadA.toExact
    require agree.toExact ≤ spreadB.toExact
    require 0 ≤ agree.toExact
    require 0 ≤ spreadA.toExact
    require 0 ≤ spreadB.toExact
    ensures ∃ (p : RatPlan) (v : Rat), out = some (p, v)   -- (C1) always produced
              ∧ 0 ≤ v                                       -- (C2) nonnegative
              ∧ p.value width agree.toExact spreadA.toExact
                  spreadB.toExact = some v                  -- (CT) the TIE
              ∧ (agree.toExact = 0 → v = 0)                 -- (C3) zero, no agreement
              ∧ (agree.toExact ≠ 0 →                        -- (C4) exact value
                  v = (agree.toExact : Rat) * agree.toExact
                        / ((spreadA.toExact : Rat) * spreadB.toExact))
              ∧ (∀ (w : Nat) (a b c : Int), 2 ≤ w → 0 ≤ a → a ≤ b → a ≤ c →
                   inWord w a → inWord w b → inWord w c →   -- (C5) LOAD-BEARING
                   p.value w a b c = some (if a = 0 then 0
                     else (a : Rat) * a / ((b : Rat) * c)))

TWO observables, and BOTH carry this instance.

  * THE CARRIER. The three aggregates arrive as the contents of ``width``-bit
    machine REGISTERS (``Word width``), not as unbounded integers. The carrier
    offers exactly one arithmetic operation, ``instMulWord``, and it WRAPS
    (``truncW``): the exact product is truncated back into the register, so for
    two positive aggregates whose product outgrows the word the register holds a
    different -- possibly negative -- number. ``Word.toExact`` reads a register
    out into exact arithmetic; it is a PROMOTION, not a register operation.

    This is what makes the fix's delta OBSERVABLE. Over an exact-``Int`` carrier
    the wrap is unrepresentable, every guard on it is dead, and the two
    combinations are pointwise-equal functions -- which is why no postcondition
    over (inputs, value, plan) could separate them, and why the earlier revision
    of this bundle was refuted as too weak by an impl that branched on
    ``spreadA * spreadB < 0``. On the register carrier that proposition is
    SATISFIABLE, so the branch is live and C2/C4 reach it.

  * THE VALUE (C1..C4). ``v`` is an EXACT rational. C4 pins it to a closed
    arithmetic function of the integers the three registers HOLD, so there is no
    answer-key to echo. The value still does not name an evaluation ORDER -- over
    exact rationals ``agree*agree / (spreadA*spreadB)`` and
    ``(agree/spreadA) * (agree/spreadB)`` are the same NUMBER -- but it is no
    longer free of the machine: a routine that assembles it through a REGISTER
    product of two aggregates is dividing by a different quantity as soon as that
    product wraps, and C4 rejects it there.

  * THE COMBINATION PLAN (C5). ``p : RatPlan`` is a first-class record of HOW the
    coefficient is assembled: which integer quantities are materialised
    (``IntPlan.mul``) and where the exact ratios are taken. ``RatPlan.value w``
    evaluates a plan under a ``w``-bit machine word: a materialised integer
    product has a value only while it stays inside the word, so a plan that forms
    an aggregate product is PARTIAL. C5 demands the returned plan yield the exact
    coefficient at EVERY width that holds the three aggregates.

  * THE TIE (CT). The value slot and the plan are not independent observables:
    CT requires the returned number to BE the number the returned plan yields, at
    this call's own width and on this call's own aggregates. That is what makes
    the plan a statement about the routine rather than an annotation beside it,
    and it is what settles the one case the value slot cannot see. A spread of
    ZERO is admissible here -- the requires demand only ``0 ≤ spread``, and a
    partition that spreads its elements one to a group reaches this routine with a
    vanishing spread and a vanishing agreement count. Over exact rationals the
    quotient is TOTAL and reports 0 at a vanishing divisor, so a value expression
    that divides unconditionally denotes the same number as one that decides the
    zero-agreement case first, and NO clause about the returned number can
    separate the two: both value shapes were machine-checked pointwise identical
    to gold's returned pair across the admissible domain (refinement.md, the
    identity record). The PLAN
    separates them: ``.zeroThen`` answers 0 without evaluating the rest, while a
    plan that forms its quotients unconditionally yields NOTHING at a vanishing
    spread, and C5 pins the returned plan on every admissible triple. With CT in
    force the returned number IS that plan's number, so every implementation
    satisfying this contract has decided the degenerate case ahead of its
    quotients, and a refinement that divides there refines none of them. Two
    accept-lane controls below (``pos-control-unconditional-value-arithmetic``,
    ``pos-control-promoted-product-value``) record that the two value shapes
    which read as unguarded MUST still verify, precisely because each is the same
    routine as gold.

  Consequence (one half of the strength of the repair): C5 admits NO plan
  containing an ``IntPlan.mul``. At width ``w`` take
  ``a = b = c = 2^(w-1) - 1``; all three fit the word, and every integer product
  the plan can form is at least their square, which does not — so the plan has no
  value there and C5 fails. Only plans that divide first (ratios of single
  aggregates, multiplied as exact rationals) satisfy C5, and those are precisely
  the implementations whose faithful fixed-width counterpart never materialises
  ``spreadA * spreadB`` and therefore stays finite at the failing scale.

All three inputs are read-only immutable values (no ``mut`` binder).

WITNESS ROUTE. The method's ``do`` block is straight-line and deterministic, but
the postcondition existentially quantifies a plan and a ``Rat``, so the
tester+``decide`` route (``derive_tester_for`` → ``…Tester args = false := by
decide``) is UNAVAILABLE: the post-image is not a decidable equality the tester
can reduce. Each reject rival is refuted by stating the method's Hoare triple
DIRECTLY at one concrete literal input and reducing it: ``unfold`` the method,
``simp only [triple_pure, le_Prop_eq]`` collapses the straight-line ``do`` block
to ``pre ≤ post (return-value)``, feed the (decidable) precondition to obtain the
existential ``p`` and ``v`` bound to the rival's own returned pair, then observe
that pair violating one named clause:

  * a C5 rival is refuted by INSTANTIATING the plan clause at one concrete
    (width, aggregates) point and reducing ``RatPlan.value`` there — either to
    ``none`` (the plan materialises a product the word cannot hold) or to a
    different rational than the coefficient;
  * a C3/C4 rival is refuted by projecting the returned value and reducing the
    resulting numeric equation;
  * the C1 rival is refuted by reducing its returned ``none`` against
    ``some (p, v)``.

Every witness binds NOTHING in its head — concrete literals only — so there is
no consistency-probe obligation (no hypotheses that could be jointly
unsatisfiable), and every name a witness mentions (``fowlkesCoeffSquared``,
``inWord``, ``RatPlan.value``, ``IntPlan.value``) is declared by the FROZEN
solution, so a gold-side failure can never be an unknown name.

Every witness closes over a COMPUTABLE PROJECTION of the returned pair rather
than by rewriting a syntactic feature of the rival's own body. That distinction
is load-bearing and was measured, not assumed: a witness that closes by
``rw [if_neg ...]`` against a branch only the RIVAL has fails on the frozen
solution with ``Did not find an occurrence of the pattern``, which reports the
absence of that branch and not the truth of the claim — the same error appears
for a claim asserting the frozen solution is CORRECT at the input. The
projection form does not have that defect: on the frozen solution the
instantiated C5 hypothesis reduces to a TRUE equation (the gold plan does yield
the coefficient at that point), leaving the ``False`` goal unsolved, so the
gold-side failure tracks the claim.

INDEPENDENT MACHINE-CHECKED REFUTATIONS. Beyond the gate's two builds, each C5
rival's plan was refuted as a standalone arithmetic fact about
``RatPlan.value`` — e.g. the product-first plan yields ``none`` at width 4 on
aggregates (1, 7, 7), whose pairwise product 49 leaves a 4-bit word — so its
rejection cannot be an artifact of a weak tactic script: no script can discharge
a false goal. Those refutations, and the positive control that the shipped plan
satisfies C5 at every width, are recorded in verdict.md.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling records
    ``has_readonly_input=False`` (all four params are by-value floats, no
    fractional permission token anywhere). Vacuous here for the stronger backend
    reason too: Velvet is referentially transparent, the three inputs are
    immutable ``Int`` values, and this bundle declares NO ``mut`` binder — so
    there is no read-only input to overwrite and no substitute probe to build.
    Not fabricated.
  * PRE-PATCH OVERFLOW ORDER — PORTED as ``prepatch-product-first-plan``, the
    load-bearing G-DIFF rival, and it no longer needs a hand-written range check
    to be rejected: the rival returns the product-first PLAN (numerator
    ``agree*agree``, denominator ``spreadA*spreadB``) with the very same exact
    rational value as gold, and C5 refutes it on the plan alone.
  * SQUARED-INDEX (drop the roots) — N/A / COLLAPSES INTO GOLD. The nagini
    "no-square-roots" rival returns ``(tk/pk)*(tk/qk)``, i.e. the SQUARE of the
    index. This bundle models the SQUARED coefficient itself (the single root is
    peeled by squaring), so that rival is exactly gold here.
  * SINGLE-RATIO (drop one marginal) — PORTED as two rivals (drop spreadB / drop
    spreadA), each attacking C4 and each varying a different spread binder.
  * ZERO-BRANCH (wrong value on the no-agreement subdomain) — PORTED, attacks C3.
  * UNGROUNDED-ORACLE ECHO — PORTED as ``plan-lone-ratio-oracle-echo``: the
    rival reads the exact value straight off C4's closed form (so C1..C4 all
    hold) and returns a plan that does not compute it. C5 is what catches it.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10844"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- -- impl-start .. -- impl-end region and is unique in Solution.lean
# ---- (asserted by _swap at load), so each edit keeps same_spec by construction
# ---- and leaves the frozen `prove_correct fowlkesCoeffSquared` statement intact.
# The WHOLE frozen impl body (the plan, both ratios, the guarded combine, return):
_GOLD_IMPL = (
    "    let p : RatPlan :=\n"
    "      .zeroThen (.read .agree)\n"
    "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
    "              (.ratio (.read .agree) (.read .spreadB)))\n"
    "    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)\n"
    "    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)\n"
    "    let v : Rat := if agree.toExact = 0 then 0 else ra * rb\n"
    "    return some (p, v)"
)
# The PLAN alone (for rivals that keep gold's value and change only the plan):
_GOLD_PLAN = (
    "    let p : RatPlan :=\n"
    "      .zeroThen (.read .agree)\n"
    "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
    "              (.ratio (.read .agree) (.read .spreadB)))\n"
)
# The guarded-combine + return tail alone (for rivals that keep the plan + ra/rb):
_GOLD_INNER = (
    "    let v : Rat := if agree.toExact = 0 then 0 else ra * rb\n"
    "    return some (p, v)"
)
# First impl statement, the insertion anchor for an in-region admissibility assert:
_LETHEAD = "    let p : RatPlan :=\n"

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a positive control that reshapes the impl may
# ---- retune its tactic script without touching the spec or dropping the
# ---- obligation. Unique in the file. ----
_FROZEN_PROOF = (
    "prove_correct fowlkesCoeffSquared by\n"
    "  loom_solve\n"
    "  -- `require_5`/`require_4` are the two ordering facts; `require_3` is\n"
    "  -- `0 ≤ agree.toExact`.\n"
    "  have hab : agree.toExact ≤ spreadA.toExact := require_5\n"
    "  have hac : agree.toExact ≤ spreadB.toExact := require_4\n"
    "  have hta : (0:Int) ≤ agree.toExact := require_3\n"
    "  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩\n"
    "  · split\n"
    "    · rfl\n"
    "    · rename_i hne\n"
    "      have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)\n"
    "      have hpk : (0:Rat) < (spreadA.toExact:Rat) := by\n"
    "        exact_mod_cast lt_of_lt_of_le hta' hab\n"
    "      have hqk : (0:Rat) < (spreadB.toExact:Rat) := by\n"
    "        exact_mod_cast lt_of_lt_of_le hta' hac\n"
    "      have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta\n"
    "      exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))\n"
    "  · by_cases h0 : agree.toExact = 0\n"
    "    · simp [RatPlan.value, IntPlan.value, h0]\n"
    "    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)\n"
    "      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)\n"
    "      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)\n"
    "      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]\n"
    "  · intro h; simp [h]\n"
    "  · intro h\n"
    "    simp only [h, if_false]\n"
    "    rw [div_mul_div_comm]\n"
    "  · intro w a b c _ ha hab' hac' _ _ _\n"
    "    by_cases h0 : a = 0\n"
    "    · simp [RatPlan.value, IntPlan.value, h0]\n"
    "    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)\n"
    "      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')\n"
    "      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')\n"
    "      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,\n"
    "        Option.some.injEq]\n"
    "      rw [div_mul_div_comm]\n"
)
assert _BASE.count(_FROZEN_PROOF) == 1, "prove_correct body drifted"

# The C5 fragment of the frozen proof, reused verbatim by every rival that keeps
# the gold PLAN (only the value clauses change for those).
_C5_PROOF = (
    "  · intro w a b c _ ha hab' hac' _ _ _\n"
    "    by_cases h0 : a = 0\n"
    "    · simp [RatPlan.value, IntPlan.value, h0]\n"
    "    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)\n"
    "      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')\n"
    "      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')\n"
    "      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,\n"
    "        Option.some.injEq]\n"
    "      rw [div_mul_div_comm]\n"
)


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


def _plan(new_plan):
    """Replace only the returned PLAN, keeping gold's exact value."""
    return _swap(_BASE, _GOLD_PLAN, new_plan)


def _inner(new_inner):
    """Reshape only the guarded-combine + return tail (keep the plan and ra/rb)."""
    return _swap(_BASE, _GOLD_INNER, new_inner)


def _impl_and_proof(new_impl, new_proof):
    """Reshape the impl region AND retune the (elided) tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, new_impl), _FROZEN_PROOF, new_proof)


# ---- WITNESS builder. The spec is a `method` CONTRACT over an existentially
# ---- quantified (plan, Rat) post-image (the tester+decide route is dead), so a
# ---- witness refutes the method's Hoare triple DIRECTLY at one concrete literal
# ---- input: unfold the method, collapse the straight-line `do` to
# ---- `pre ≤ post (p, v)` through `triple_pure`, feed the (decidable)
# ---- precondition to obtain the existential pair bound to the rival's own
# ---- return value, then observe that pair violating a named clause. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script can
# ---- mask the verdict. Every lemma used (`triple_pure`, `le_Prop_eq`) comes from
# ---- the frozen `Velvet.Std` import; nothing extra is imported.
def _witness(a, sa, sb, tail, w=64):
    """Refute the method's Hoare triple at one concrete admissible call.

    The three aggregates arrive in `w`-bit registers, so the witness builds
    those registers (`Word.mk`) and states the FROZEN postcondition over their
    promoted contents -- byte-for-byte the spec's `ensures`, with the literal
    aggregates substituted for the binders. The precondition instantiated here
    is likewise the spec's full require list at this call.
    """
    A = f"(Word.mk ({a}) : Word {w})"
    SA = f"(Word.mk ({sa}) : Word {w})"
    SB = f"(Word.mk ({sb}) : Word {w})"
    return (
        "example :\n"
        "    ¬ triple (l := Prop)\n"
        f"        (2 ≤ {w} ∧ inWord {w} ({a}:Int) ∧ inWord {w} ({sa}:Int)\n"
        f"         ∧ inWord {w} ({sb}:Int)\n"
        f"         ∧ ({a}:Int) ≤ ({sa}:Int) ∧ ({a}:Int) ≤ ({sb}:Int)\n"
        f"         ∧ 0 ≤ ({a}:Int) ∧ 0 ≤ ({sa}:Int) ∧ 0 ≤ ({sb}:Int))\n"
        f"        (fowlkesCoeffSquared {w} {A} {SA} {SB})\n"
        "        (fun out => ∃ (p : RatPlan) (v : Rat), out = some (p, v)\n"
        "            ∧ 0 ≤ v\n"
        f"            ∧ p.value {w} ({a}:Int) ({sa}:Int) ({sb}:Int) = some v\n"
        f"            ∧ (({a}:Int) = 0 → v = 0)\n"
        f"            ∧ (({a}:Int) ≠ 0 → v = (({a}:Int) : Rat) * ({a})"
        f" / ((({sa}:Int) : Rat) * ({sb})))\n"
        "            ∧ (∀ (w : Nat) (x y z : Int), 2 ≤ w → 0 ≤ x → x ≤ y → x ≤ z →\n"
        "                 inWord w x → inWord w y → inWord w z →\n"
        "                 p.value w x y z\n"
        "                   = some (if x = 0 then 0\n"
        "                           else (x : Rat) * x / ((y : Rat) * z)))) := by\n"
        "  unfold fowlkesCoeffSquared\n"
        "  simp only [triple_pure, le_Prop_eq]\n"
        "  intro hcon\n"
        f"{tail}"
    )


_OBTAIN = (
    "  obtain ⟨p, v, hv, hnn, htie, hz, hnz, hplan⟩ :=\n"
    "    hcon ⟨by decide, by unfold inWord; decide, by unfold inWord; decide,\n"
    "          by unfold inWord; decide, by decide, by decide,\n"
    "          by decide, by decide, by decide⟩\n"
    "  simp only [Option.some.injEq, Prod.mk.injEq] at hv\n"
    "  obtain ⟨hp, hvv⟩ := hv\n"
)


def _plan_tail(w, x, y, z):
    """Tail for a C5 rival: instantiate the plan clause at one concrete
    (width, aggregates) point and reduce `RatPlan.value` there."""
    return (
        _OBTAIN
        + "  subst hp\n"
        f"  have hw := hplan {w} {x} {y} {z} (by decide) (by decide) (by decide)\n"
        "      (by decide) (by unfold inWord; decide) (by unfold inWord; decide)\n"
        "      (by unfold inWord; decide)\n"
        "  simp [RatPlan.value, IntPlan.value, inWord] at hw\n"
    )


# tail for a VALUE rival (C4): project v, discharge agree≠0, reduce the equation.
_VAL_TAIL = (
    _OBTAIN
    + "  subst hvv\n"
    "  have hbad := hnz (by decide)\n"
    "  push_cast at hbad\n"
    "  first\n"
    "    | (field_simp at hbad\n"
    "       exact absurd hbad (by decide))\n"
    "    | norm_num at hbad\n"
    "    | simp at hbad\n"
)
# tail for a ZERO-branch rival (C3): project v, discharge agree=0, reduce.
_ZERO_TAIL = (
    _OBTAIN
    + "  subst hvv\n"
    "  have hbad := hz (by decide)\n"
    "  simp at hbad\n"
)
# tail for the C1 rival: the returned `Option` cannot be `some (p, v)`, stated over
# the COMPUTABLE PROJECTION `Option.isSome`. `congrArg Option.isSome` turns C1 into
# `(<the impl's returned Option>).isSome = true`; `Option.isSome_some` discharges
# the right-hand side, and `decide` then evaluates the LEFT side — the rival's own
# guarded expression — closing the goal exactly when that expression is `none`.
#
# AUDIT NOTE (this tail was REPLACED; the original is recorded here because the
# replacement is the whole substance of the repair). The first version closed with
#
#     norm_num at hv
#     exact absurd hv.1 (by decide)
#
# and it did not discriminate. `norm_num` shapes `hv` differently on the two
# subjects, so on gold `hv.1` is the PLAN equation `<gold plan> = p` with `p` still
# a local; `absurd` then fails to elaborate with
# `Expected type must not contain free variables`, which reports the SHAPE of
# gold's returned pair and not the truth of the claim. Measured with four builds:
#   * the same tail at (1, 2, 4) — an input where the RIVAL returns `some`, so the
#     claim is FALSE of the rival — fails on the rival by `decide` REFUTING
#     `¬2 * 4 ≤ 2^63 - 1`, i.e. by deciding (exit 1);
#   * the same tail against GOLD at that input fails with the byte-identical
#     `Expected type must not contain free variables` error as at the shipped
#     input (exit 1);
#   * a FORGERY differing from the witness ONLY in what it claims — the
#     nonnegativity conjunct replaced by `v = 1234`, which gold's returned value
#     VIOLATES, so `¬ triple …` is TRUE of gold and an honest witness must
#     elaborate — fails against gold with that same byte-identical error (exit 1).
# So gold's exit code carried no information about the claim: the gate would have
# recorded `rejected` for a witness asserting gold is CORRECT there.
#
# The projection form does track the claim, measured on the same four points:
#   * against the rival at (1, 2^62, 4): EXIT 0;
#   * against gold at that input: EXIT 1, `decide` REFUTING `True → False` — gold's
#     `some` reduced the projection to `True`, which is a decision about the claim;
#   * against the rival at (1, 2, 4), where the rival returns `some`: EXIT 1, and
#     `decide` refutes the goal by EVALUATING the rival's own guarded expression,
#     so the tail fails exactly when the claim is false;
#   * the `v = 1234` forgery against gold: EXIT 1 by `decide` on `True → False`,
#     i.e. by deciding rather than by an elaboration error.
# A type-reveal pair confirms the two sides differ in the hypothesis's real type:
# on gold `hs` has type `True` (the projection reduced), on the rival it is the
# rival's own un-reduced `(if 2^62 * 4 ≤ 2^63 - 1 then some … else none).isSome =
# true`. A CORRECT impl carrying an always-satisfied output guard
# (`if 2 ≤ width then some (p, v) else none`, which verifies) is refuted by
# neither tail, which is the control that the projection is not merely detecting
# the presence of an `if`.
_NONE_TAIL = (
    "  obtain ⟨p, v, hv, _⟩ :=\n"
    "    hcon ⟨by decide, by unfold inWord; decide, by unfold inWord; decide,\n"
    "          by unfold inWord; decide, by decide, by decide,\n"
    "          by decide, by decide, by decide⟩\n"
    "  have hs := congrArg (Option.isSome) hv\n"
    "  simp only [Option.isSome_some] at hs\n"
    "  revert hs\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Guard the non-zero case first (invert the condition), keeping the gold
        # plan and ra/rb. Observationally identical on every input; the tactic
        # body is retuned to select the reordered branches but the obligation
        # STATEMENT is byte-identical.
        "module": _impl_and_proof(
            "    let p : RatPlan :=\n"
            "      .zeroThen (.read .agree)\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
            "              (.ratio (.read .agree) (.read .spreadB)))\n"
            "    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)\n"
            "    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)\n"
            "    let v : Rat := if agree.toExact ≠ 0 then ra * rb else 0\n"
            "    return some (p, v)",
            "prove_correct fowlkesCoeffSquared by\n"
            "  loom_solve\n"
            "  have hab : agree.toExact ≤ spreadA.toExact := require_5\n"
            "  have hac : agree.toExact ≤ spreadB.toExact := require_4\n"
            "  have hta : (0:Int) ≤ agree.toExact := require_3\n"
            "  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩\n"
            "  · split\n"
            "    · rename_i hne\n"
            "      have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)\n"
            "      have hpk : (0:Rat) < (spreadA.toExact:Rat) := by\n"
            "        exact_mod_cast lt_of_lt_of_le hta' hab\n"
            "      have hqk : (0:Rat) < (spreadB.toExact:Rat) := by\n"
            "        exact_mod_cast lt_of_lt_of_le hta' hac\n"
            "      have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta\n"
            "      exact mul_nonneg (div_nonneg htk (le_of_lt hpk))\n"
            "        (div_nonneg htk (le_of_lt hqk))\n"
            "    · rfl\n"
            "  · by_cases h0 : agree.toExact = 0\n"
            "    · simp [RatPlan.value, IntPlan.value, h0]\n"
            "    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)\n"
            "      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)\n"
            "      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)\n"
            "      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]\n"
            "  · intro h; rw [if_neg (by simp [h])]\n"
            "  · intro h; rw [if_pos h, div_mul_div_comm]\n"
            + _C5_PROOF),
        "rationale": "PASS SOURCE = C1..C5. Guarding the non-zero case first "
                     "(condition inverted to `agree ≠ 0`) returns the SAME pair "
                     "as gold on every input: the same plan (C5 discharges with "
                     "the frozen fragment) and the same exact value, so C1..C4 "
                     "still hold. A structurally-different faithful reshape MUST "
                     "verify; else the postcondition over-constrains the "
                     "executable branch order (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-commuted-ratios",
        "kind": "soundness",
        "expect": "verify",
        # Take the ratios in the OTHER order and multiply them the other way
        # round, plan included: `(agree/spreadB) * (agree/spreadA)`. Still divides
        # first, so it is faithful; the plan is a different TERM from gold's, which
        # is the point — C5 must not pin the plan to one syntactic shape, only to
        # the property of yielding the coefficient at every width.
        "module": _impl_and_proof(
            "    let p : RatPlan :=\n"
            "      .zeroThen (.read .agree)\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadB))\n"
            "              (.ratio (.read .agree) (.read .spreadA)))\n"
            "    let v : Rat := if agree.toExact = 0 then 0\n"
            "                   else ((agree.toExact : Rat) / (spreadB.toExact : Rat))"
            " * ((agree.toExact : Rat) / (spreadA.toExact : Rat))\n"
            "    return some (p, v)",
            "prove_correct fowlkesCoeffSquared by\n"
            "  loom_solve\n"
            "  have hab : agree.toExact ≤ spreadA.toExact := require_5\n"
            "  have hac : agree.toExact ≤ spreadB.toExact := require_4\n"
            "  have hta : (0:Int) ≤ agree.toExact := require_3\n"
            "  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩\n"
            "  · split\n"
            "    · rfl\n"
            "    · rename_i hne\n"
            "      have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)\n"
            "      have hpk : (0:Rat) < (spreadA.toExact:Rat) := by\n"
            "        exact_mod_cast lt_of_lt_of_le hta' hab\n"
            "      have hqk : (0:Rat) < (spreadB.toExact:Rat) := by\n"
            "        exact_mod_cast lt_of_lt_of_le hta' hac\n"
            "      have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta\n"
            "      exact mul_nonneg (div_nonneg htk (le_of_lt hqk))\n"
            "        (div_nonneg htk (le_of_lt hpk))\n"
            "  · by_cases h0 : agree.toExact = 0\n"
            "    · simp [RatPlan.value, IntPlan.value, h0]\n"
            "    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)\n"
            "      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)\n"
            "      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)\n"
            "      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]\n"
            "  · intro h; simp [h]\n"
            "  · intro h\n"
            "    simp only [h, if_false]\n"
            "    rw [div_mul_div_comm,\n"
            "        mul_comm (spreadB.toExact:Rat) (spreadA.toExact:Rat)]\n"
            "  · intro w a b c _ ha hab' hac' _ _ _\n"
            "    by_cases h0 : a = 0\n"
            "    · simp [RatPlan.value, IntPlan.value, h0]\n"
            "    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)\n"
            "      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')\n"
            "      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')\n"
            "      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,\n"
            "                 Option.some.injEq]\n"
            "      rw [div_mul_div_comm, mul_comm (c:Rat) (b:Rat)]\n"),
        "rationale": "PASS SOURCE = C1..C5. Pairing the agreement count with the "
                     "OTHER spread first — value and plan both commuted — is a "
                     "faithful divide-first assembly with a plan term that is not "
                     "gold's. It MUST verify: C5 is a property (yield the exact "
                     "coefficient at every machine word width), not a syntactic "
                     "template, and if only gold's literal plan term could satisfy "
                     "it the clause would be SPEC-TOO-STRONG. Measured EXIT 0 "
                     "during authoring.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method HAS real preconditions (`require 2 ≤ width`, the
    # three `inWord` range facts, the two orderings `agree ≤ spreadA`,
    # `agree ≤ spreadB`, and `0 ≤ agree`, `0 ≤ spreadA`, `0 ≤ spreadB`). Note the
    # spreads are bounded BELOW BY ZERO, not by one: a vanishing spread is
    # ADMISSIBLE, which is exactly why the degenerate subdomain is reachable and
    # why the plan clause is load-bearing there. (Corrected by audit: an earlier
    # revision of this comment claimed `0 < spreadA`, `0 < spreadB`, which the
    # frozen require list does not contain.) The probe is NOT vacuous: it asserts, in
    # region, that the LARGE-COUNT regime that motivated the fix lies inside the
    # admitted domain, that the exact squared coefficient there is a well-defined
    # nonnegative rational, AND that all three aggregates of that regime fit a
    # 64-bit machine word while their pairwise product does NOT — i.e. the regime
    # is admitted and is exactly the regime where a materialised aggregate
    # product would have no value. `loom_solve` discharges the decidable
    # in-region assert automatically; the impl is otherwise gold so the method's
    # own obligation still closes with the FROZEN proof. MUST verify, else
    # PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-unconditional-value-arithmetic",
        "kind": "soundness",
        "expect": "verify",
        # Gold's plan and gold's two ratios, with the zero test DROPPED from the
        # value expression. Over exact rationals this is the same function: the
        # quotient is total and reports 0 at a vanishing spread, and a vanishing
        # spread forces a vanishing agreement count, so `ra * rb` already equals
        # the guarded value everywhere on the admissible domain.
        "module": _impl_and_proof(
            "    let p : RatPlan :=\n"
            "      .zeroThen (.read .agree)\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
            "              (.ratio (.read .agree) (.read .spreadB)))\n"
            "    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)\n"
            "    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)\n"
            "    let v : Rat := ra * rb\n"
            "    return some (p, v)",
            "prove_correct fowlkesCoeffSquared by\n"
            "  loom_solve\n"
            "  have hab : agree.toExact ≤ spreadA.toExact := require_5\n"
            "  have hac : agree.toExact ≤ spreadB.toExact := require_4\n"
            "  have hta : (0:Int) ≤ agree.toExact := require_3\n"
            "  have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta\n"
            "  have hpk : (0:Rat) ≤ (spreadA.toExact:Rat) := by\n"
            "    exact_mod_cast require_2\n"
            "  have hqk : (0:Rat) ≤ (spreadB.toExact:Rat) := by\n"
            "    exact_mod_cast require_1\n"
            "  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩\n"
            "  · exact mul_nonneg (div_nonneg htk hpk) (div_nonneg htk hqk)\n"
            "  · by_cases h0 : agree.toExact = 0\n"
            "    · simp [RatPlan.value, IntPlan.value, h0]\n"
            "    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)\n"
            "      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)\n"
            "      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)\n"
            "      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]\n"
            "  · intro h; simp [h]\n"
            "  · intro h; rw [div_mul_div_comm]\n"
            + _C5_PROOF),
        "rationale": "PASS SOURCE = C1..C5 + CT. Dropping the zero test from the "
                     "VALUE expression while keeping gold's plan returns the SAME "
                     "pair as gold on every admissible input, so it MUST verify: a "
                     "clause that rejected it would reject gold's own returned "
                     "number (SPEC-TOO-STRONG). Recorded in the accept lane to "
                     "state plainly which observable carries the short-circuit. Not "
                     "the value slot, which cannot see it -- the exact quotient is "
                     "total and reports 0 at a vanishing spread. The returned PLAN "
                     "carries it (C5, on every admissible triple), and CT makes the "
                     "returned number that plan's number, so this implementation "
                     "decides the zero-agreement case ahead of its quotients and "
                     "its only faithful refinement does too. Measured EXIT 0 during "
                     "authoring.",
    },
    {
        "id": "pos-control-promoted-product-value",
        "kind": "soundness",
        "expect": "verify",
        # Gold's plan, and a value reached through an exact PROMOTED product of
        # the two spreads (`spreadA.toExact * spreadB.toExact` : Int, unbounded
        # arithmetic -- NOT the registers' wrapping `instMulWord`), again with no
        # zero test in the value expression. Same pair as gold everywhere on the
        # admissible domain.
        "module": _impl_and_proof(
            "    let p : RatPlan :=\n"
            "      .zeroThen (.read .agree)\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
            "              (.ratio (.read .agree) (.read .spreadB)))\n"
            "    let prod : Int := spreadA.toExact * spreadB.toExact\n"
            "    let v : Rat := (agree.toExact : Rat) * agree.toExact / (prod : Rat)\n"
            "    return some (p, v)",
            "prove_correct fowlkesCoeffSquared by\n"
            "  loom_solve\n"
            "  have hab : agree.toExact ≤ spreadA.toExact := require_5\n"
            "  have hac : agree.toExact ≤ spreadB.toExact := require_4\n"
            "  have hta : (0:Int) ≤ agree.toExact := require_3\n"
            "  have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta\n"
            "  have hpk : (0:Rat) ≤ (spreadA.toExact:Rat) := by\n"
            "    exact_mod_cast require_2\n"
            "  have hqk : (0:Rat) ≤ (spreadB.toExact:Rat) := by\n"
            "    exact_mod_cast require_1\n"
            "  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩\n"
            "  · push_cast\n"
            "    exact div_nonneg (mul_nonneg htk htk) (mul_nonneg hpk hqk)\n"
            "  · by_cases h0 : agree.toExact = 0\n"
            "    · simp [RatPlan.value, IntPlan.value, h0]\n"
            "    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)\n"
            "      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)\n"
            "      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)\n"
            "      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0,\n"
            "        div_mul_div_comm]\n"
            "  · intro h; simp [h]\n"
            "  · intro _; push_cast; rfl\n"
            + _C5_PROOF),
        "rationale": "PASS SOURCE = C1..C5 + CT. Reaching the value through an "
                     "exact PROMOTED product of the two spreads, with no zero test "
                     "in the value expression, is once more the same pair as gold on "
                     "every admissible input, so it MUST verify. Promotion out of "
                     "the register into unbounded arithmetic is a legitimate route "
                     "to this number and C4 states the value in exactly that form; "
                     "what no implementation may do is form that product IN the "
                     "registers (`instMulWord` wraps -- see "
                     "`guarded-none-on-large-product`) or materialise it in the PLAN "
                     "(C5 has no value there, at any width). This control pins that "
                     "boundary from the accept side, and pairs it with the reading "
                     "CT forces: a refinement of this implementation performs the "
                     "promotion too AND keeps its plan's short-circuit. Measured "
                     "EXIT 0 during authoring.",
    },
    {
        "id": "admissibility-large-count-regime",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _LETHEAD,
            "    -- The large-count regime that motivated the fix is admitted: the\n"
            "    -- aggregate magnitudes at the reported failing scale satisfy the\n"
            "    -- input frame (the agreement count is nonnegative and both spreads\n"
            "    -- are strictly positive), the exact squared coefficient there is a\n"
            "    -- well-defined nonnegative rational, each aggregate fits a 64-bit\n"
            "    -- machine word, and the product of the two spreads does not — so\n"
            "    -- this is precisely the regime where a plan materialising that\n"
            "    -- product would have no value. (The word bound is spelled as the\n"
            "    --  literal 9223372036854775807 rather than through `inWord`, so\n"
            "    --  every conjunct is decidable numeral arithmetic the in-region\n"
            "    --  automation discharges without unfolding a definition.)\n"
            "    assert (with_name_prefix `assert\n"
            "      ((0 : Int) ≤ 3003497866 ∧ (0 : Int) < 5152663196"
            " ∧ (0 : Int) < 3294371982\n"
            "       ∧ (0 : Rat) ≤ (3003497866 : Rat) * 3003497866"
            " / ((5152663196 : Rat) * 3294371982)\n"
            "       ∧ (3003497866 : Int) ≤ 9223372036854775807\n"
            "       ∧ (5152663196 : Int) ≤ 9223372036854775807\n"
            "       ∧ (3294371982 : Int) ≤ 9223372036854775807\n"
            "       ∧ (9223372036854775807 : Int) < 5152663196 * 3294371982))\n"
            + _LETHEAD),
        "rationale": "the precondition admits the large-count regime "
                     "(agree≈3.0e9, spreadA≈5.15e9, spreadB≈3.29e9): the "
                     "agreement count is nonnegative and both spreads strictly "
                     "positive, so it is in-domain, and the exact squared "
                     "coefficient there is a well-defined nonnegative rational. "
                     "The assert also pins the modelling fact C5 turns on: all "
                     "three aggregates fit a 64-bit word while the product of the "
                     "two spreads does not, so on this admitted input a plan that "
                     "materialises that product has no value and a divide-first "
                     "plan does -- and, since that product exceeds the word, it is "
                     "also the regime where forming it IN the register wraps, which "
                     "is what the value clause now reaches. The in-region `assert` "
                     "is a live, decidable claim "
                     "(a false conjunct would leave an unsolved goal); the impl is "
                     "otherwise gold so C1..C5 still discharge with the frozen "
                     "proof. If it cannot verify ⇒ PRECOND-TOO-STRONG (the regime "
                     "the fix targets would be excluded from the domain).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and a refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- THE pre-patch order, now refuted on the PLAN alone, C5 ----
    {
        "id": "prepatch-product-first-plan",
        "kind": "uniqueness",
        "expect": "reject",
        # The faithful pre-patch skeleton (== Solution_prepatch.lean's impl
        # region): assemble the coefficient by materialising the two products
        # `agree*agree` and `spreadA*spreadB` and taking a single ratio. The exact
        # rational VALUE is identical to gold's — that is what makes this the
        # load-bearing rival: only the plan distinguishes it.
        "module": _impl(
            "    let p : RatPlan :=\n"
            "      .ratio (.mul (.read .agree) (.read .agree))\n"
            "             (.mul (.read .spreadA) (.read .spreadB))\n"
            "    let prod : Word width := spreadA * spreadB\n"
            "    let v : Rat :=\n"
            "      if agree.toExact = 0 then (0 : Rat)\n"
            "      else (agree.toExact : Rat) * agree.toExact / (prod.toExact : Rat)\n"
            "    return some (p, v)"),
        "refinement": "this is the pre-patch evaluation order exactly: form the "
                      "product of the two spreads first and divide the squared "
                      "agreement count into it. Under the fixed-width arithmetic "
                      "the original code ran, that product can leave the machine "
                      "word even when each aggregate fits it — at the reported "
                      "failing scale spreadA*spreadB ≈ 1.7e19 exceeds the signed "
                      "64-bit maximum ≈ 9.22e18 — so the faithful counterpart "
                      "wraps to a negative product and yields a non-finite "
                      "result. It fails the failing test `assert_all_finite(...)` "
                      "on the large-count input, so it would NOT resolve the F2P.",
        "rationale": "REJECT from C5 AND from C4 — the pre-patch order fails on "
                     "both observables. C5 rejects it on the plan: the returned "
                     "plan materialises `spreadA * spreadB`, and at width 4 on "
                     "aggregates (1, 7, 7) — all inside a 4-bit word — that "
                     "product is 49, which is not, so the plan yields `none` where "
                     "C5 demands `some (1/49)`. C4 rejects it independently on the "
                     "value: the rival forms that product in the REGISTER the "
                     "aggregates arrive in, and register multiplication wraps, so "
                     "on the aggregates where the product outgrows the word the "
                     "quantity it divides into is not their product and the number "
                     "returned is not the coefficient. Two independent rejection "
                     "routes on one rival. Refuted at input "
                     "(agree=1, spreadA=2, spreadB=3).",
        "witness": _witness(1, 2, 3, _plan_tail(4, 1, 7, 7)),
    },

    # ---- a plan that is value-correct but materialises squares, C5 ----
    {
        "id": "plan-materialises-squares",
        "kind": "uniqueness",
        "expect": "reject",
        # Denominator-cancelling dodge: assemble
        # (agree*agree / spreadA) * (spreadB / (spreadB*spreadB)), which is the
        # coefficient as an exact rational and never forms `spreadA * spreadB` —
        # but does materialise `agree*agree` and `spreadB*spreadB`. A
        # partial-domain rival: correct while the squares fit the word, valueless
        # above it, which is precisely the failure the F2P test reports.
        "module": _impl(
            "    let p : RatPlan :=\n"
            "      .mul (.ratio (.mul (.read .agree) (.read .agree)) (.read .spreadA))\n"
            "           (.ratio (.read .spreadB) (.mul (.read .spreadB) (.read .spreadB)))\n"
            "    let v : Rat :=\n"
            "      if agree.toExact = 0 then (0 : Rat)\n"
            "      else (agree.toExact : Rat) * agree.toExact\n"
            "             / ((spreadA.toExact : Rat) * (spreadB.toExact : Rat))\n"
            "    return some (p, v)"),
        "refinement": "squaring the agreement count and the second spread in "
                      "fixed-width arithmetic overflows at the failing scale just "
                      "as the pre-patch product does (agree ≈ 3.0e9 gives "
                      "agree*agree ≈ 9.0e18, spreadB ≈ 3.29e9 gives "
                      "spreadB*spreadB ≈ 1.1e19, both at or past the signed "
                      "64-bit maximum ≈ 9.22e18), so the faithful counterpart is "
                      "non-finite on the F2P input and would NOT resolve it. It is "
                      "the shape of a patch that avoided the ONE named product "
                      "while still materialising others.",
        "rationale": "REJECT from C5, and it is the partial-domain attack: the "
                     "plan yields the exact coefficient for every aggregate triple "
                     "small enough for the squares to fit the word, and no value "
                     "at all above that — so a spec that quantified the plan only "
                     "over some convenient width, or only over this call's inputs, "
                     "would admit it. C5 quantifies over EVERY width: at width 4 "
                     "on (1, 1, 7) the step `spreadB*spreadB = 49` leaves the "
                     "4-bit word, so the plan yields `none` where C5 demands "
                     "`some (1/7)`. Refuted at input (agree=2, spreadA=3, "
                     "spreadB=5) — a third distinct input point.",
        "witness": _witness(2, 3, 5, _plan_tail(4, 1, 1, 7)),
    },

    # ---- boundary token swap inside the plan, C5 ----
    {
        "id": "plan-reads-spreadA-twice",
        "kind": "uniqueness",
        "expect": "reject",
        # Boundary token swap: the plan pairs the agreement count with the FIRST
        # spread twice, so it denotes agree^2/spreadA^2 rather than
        # agree^2/(spreadA*spreadB). The returned VALUE is still gold's, so only
        # C5 can see the swap.
        "module": _plan(
            "    let p : RatPlan :=\n"
            "      .mul (.ratio (.read .agree) (.read .spreadA))\n"
            "           (.ratio (.read .agree) (.read .spreadA))\n"),
        "refinement": "a plan that reads the first spread in both factors is the "
                      "shape of a patch that duplicated one aggregate token when "
                      "splitting the single ratio into two — the exact "
                      "copy-paste slip the divide-first rewrite invites. Its "
                      "faithful counterpart computes "
                      "sqrt(tk/pk)*sqrt(tk/pk) = tk/pk, which is finite but wrong "
                      "whenever the two spreads differ, so the exact-value "
                      "regression tests fail and it would NOT resolve.",
        "rationale": "REJECT from C5 by a VALUE mismatch rather than by "
                     "partiality, which is a distinct rejection route: the plan is "
                     "total (it materialises no product at all), and at width 4 on "
                     "(1, 1, 2) it yields 1 where C5 demands 1/2. The returned "
                     "value v is gold's exact coefficient, so C1..C4 hold and only "
                     "the plan clause discriminates. Refuted at input "
                     "(agree=1, spreadA=4, spreadB=5).",
        "witness": _witness(1, 4, 5, _plan_tail(4, 1, 1, 2)),
    },

    # ---- oracle echo: right value, plan that does not compute it, C5 ----
    {
        "id": "plan-lone-ratio-oracle-echo",
        "kind": "uniqueness",
        "expect": "reject",
        # Read the value straight off C4's closed form and return a plan that
        # computes something else entirely (a single ratio). C1..C4 all hold —
        # this is the ORACLE ECHO on the new observable: satisfy the number,
        # misreport the computation.
        "module": _plan(
            "    let p : RatPlan := .ratio (.read .agree) (.read .spreadA)\n"),
        "refinement": "a routine whose reported assembly is a single ratio "
                      "agree/spreadA is the drop-one-marginal defect; its faithful "
                      "counterpart returns sqrt(tk/pk), which ignores the second "
                      "clustering entirely and fails the exact-value regression "
                      "tests, so it would NOT resolve. The rival is built to pass "
                      "every value clause by echoing C4's closed form, so if C5 "
                      "did not tie the plan to the coefficient the spec would "
                      "accept a routine that reports an assembly it does not "
                      "perform.",
        "rationale": "REJECT from C5. The echo is the point: v is literally C4's "
                     "right-hand side, so C1..C4 are satisfied by construction and "
                     "the ONLY clause left to reject the rival is the plan clause. "
                     "At width 4 on (1, 1, 2) the lone ratio yields 1 where C5 "
                     "demands 1/2. Refuted at input (agree=3, spreadA=7, "
                     "spreadB=7) — corrected by audit to the tuple the witness "
                     "below actually calls at.",
        "witness": _witness(3, 7, 7, _plan_tail(4, 1, 1, 2)),
    },

    # ---- per-input plan choice: exploits the freedom C5 leaves, C5 ----
    {
        "id": "plan-chosen-per-input",
        "kind": "uniqueness",
        "expect": "reject",
        # Exploits the freedom the repair leaves: the plan is returned PER CALL,
        # so a rival can report the product-first plan on the inputs where that
        # product happens to fit a 64-bit word and the divide-first plan only
        # above it. This is the rival a fixed-width C5 (one width, this call's
        # inputs) would admit; the ∀-width quantifier is what refuses it.
        "module": _impl(
            "    let pd : RatPlan :=\n"
            "      .ratio (.mul (.read .agree) (.read .agree))\n"
            "             (.mul (.read .spreadA) (.read .spreadB))\n"
            "    let pr : RatPlan :=\n"
            "      .mul (.ratio (.read .agree) (.read .spreadA))\n"
            "           (.ratio (.read .agree) (.read .spreadB))\n"
            "    let p : RatPlan :=\n"
            "      if spreadA.toExact * spreadB.toExact ≤ 2 ^ 63 - 1 then pd else pr\n"
            "    let v : Rat :=\n"
            "      if agree.toExact = 0 then (0 : Rat)\n"
            "      else (agree.toExact : Rat) * agree.toExact\n"
            "             / ((spreadA.toExact : Rat) * (spreadB.toExact : Rat))\n"
            "    return some (p, v)"),
        "refinement": "branching the assembly on whether the aggregate product "
                      "fits the machine word is the shape of a patch that guarded "
                      "the old order instead of replacing it. Its faithful "
                      "counterpart still forms `pk * qk` to evaluate the guard, so "
                      "the wrap has already happened when the comparison is made "
                      "and the guard cannot fire: it stays non-finite on the F2P "
                      "input and would NOT resolve.",
        "rationale": "REJECT from C5, exploiting exactly the freedom the repair "
                     "leaves — the plan is chosen per call, so on inputs where the "
                     "spreads' product fits a 64-bit word this rival reports the "
                     "product-first plan and elsewhere the divide-first one. A "
                     "clause that evaluated the plan at ONE width, or only at this "
                     "call's aggregates, would accept it. C5 asks the returned plan "
                     "to hold at EVERY width: on (agree=1, spreadA=2, spreadB=3) "
                     "the guard is true, so the plan returned IS the product-first "
                     "one, and at width 4 on (1, 7, 7) it yields `none` where C5 "
                     "demands `some (1/49)`. Refuted at input (agree=5, "
                     "spreadA=6, spreadB=6) — corrected by audit to the tuple the "
                     "witness below actually calls at; the guard is true there "
                     "(6 * 6 = 36 fits a 64-bit word), so the plan the rival "
                     "returns at the witness's own call IS the product-first one.",
        "witness": _witness(5, 6, 6, _plan_tail(4, 1, 7, 7)),
    },

    # ---- returns nothing on the large-product subdomain, C1 ----
    {
        "id": "guarded-none-on-large-product",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep gold's plan and value, but refuse to produce anything once the
        # spreads' product leaves a 64-bit word: a partial-domain rival that
        # narrows the OUTPUT instead of the plan. C1 is what catches it.
        "module": _impl(
            "    let p : RatPlan :=\n"
            "      .mul (.ratio (.read .agree) (.read .spreadA))\n"
            "           (.ratio (.read .agree) (.read .spreadB))\n"
            "    let v : Rat :=\n"
            "      if agree.toExact = 0 then (0 : Rat)\n"
            "      else (agree.toExact : Rat) * agree.toExact\n"
            "             / ((spreadA.toExact : Rat) * (spreadB.toExact : Rat))\n"
            "    let r : Option (RatPlan × Rat) :=\n"
            "      if spreadA.toExact * spreadB.toExact ≤ 2 ^ 63 - 1 then some (p, v)\n"
            "      else none\n"
            "    return r"),
        "refinement": "declining to produce a coefficient once the spreads' "
                      "product exceeds the machine word is the shape of a patch "
                      "that detected the condition and bailed out (raising, or "
                      "returning a sentinel) instead of reassociating the "
                      "arithmetic. Its faithful counterpart produces no finite "
                      "score at the failing scale, so `assert_all_finite(...)` "
                      "still fails and it would NOT resolve.",
        "rationale": "REJECT from C1 (`out = some (p, v)`, a coefficient is always "
                     "produced): on an input whose spread product exceeds the "
                     "64-bit word the rival returns `none`, which cannot equal "
                     "`some (p, v)` for any pair. This is the OUTPUT-narrowing "
                     "partial domain, distinct from the plan-partiality rivals "
                     "above. Refuted at (agree=1, spreadA=2^62, spreadB=4), where "
                     "the product 2^64 exceeds the bound; gold returns the exact "
                     "`some (p, 1/2^64)`.",
        "witness": _witness(1, "2^62", 4, _NONE_TAIL),
    },

    # ---- single-ratio: drop spreadB, C4 ----
    {
        "id": "single-ratio-drop-spreadB",
        "kind": "uniqueness",
        "expect": "reject",
        # Return only the first ratio `ra = agree/spreadA` as the value, keeping
        # gold's plan. Nonnegative and produced (C1/C2/C3 and C5 hold), but not
        # the product of the two ratios => wrong squared coefficient. Ports the
        # nagini single-ratio-drop-qk rival; abuses the `spreadB` binder.
        "module": _inner(
            "    let v : Rat := if agree.toExact = 0 then 0 else ra\n"
            "    return some (p, v)"),
        "refinement": "returning only `agree/spreadA` ignores the second "
                      "clustering's aggregate `spreadB`. It is finite and "
                      "nonnegative, but is not the geometric combination: e.g. "
                      "with agree/spreadA = 1 and agree/spreadB = 1/2 the correct "
                      "squared coefficient is 1/2 but this returns 1. A faithful "
                      "counterpart that dropped one marginal fails the exact-value "
                      "regression tests (the two clusterings are treated "
                      "asymmetrically), so it would NOT resolve.",
        "rationale": "REJECT from C4 (v = agree*agree / (spreadA*spreadB)): the "
                     "rival returns `agree/spreadA`, which equals the exact "
                     "squared coefficient only when agree = spreadB, not an "
                     "admissible invariant. Abuses the `spreadB` binder (it is "
                     "dropped from the VALUE while the plan still names it, so "
                     "this rival also shows C5 alone would not close the value "
                     "lane). Refuted at (1,1,2): rival returns 1, C4 demands 1/2.",
        "witness": _witness(1, 1, 2, _VAL_TAIL),
    },

    # ---- single-ratio: drop spreadA, C4 (varies the OTHER spread binder) ----
    {
        "id": "single-ratio-drop-spreadA",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the above; abuses the `spreadA` binder and varies it at a
        # distinct input.
        "module": _inner(
            "    let v : Rat := if agree.toExact = 0 then 0 else rb\n"
            "    return some (p, v)"),
        "refinement": "returning only `agree/spreadB` ignores the first "
                      "clustering's aggregate `spreadA` — the mirror defect. "
                      "Finite and nonnegative, but not the geometric combination: "
                      "with agree/spreadB = 1 and agree/spreadA = 1/2 the correct "
                      "squared coefficient is 1/2 but this returns 1. A faithful "
                      "counterpart dropping this marginal fails the exact-value "
                      "regression tests, so it would NOT resolve.",
        "rationale": "REJECT from C4: the rival returns `agree/spreadB`, which "
                     "equals the exact squared coefficient only when "
                     "agree = spreadA, not an admissible invariant. Abuses the "
                     "`spreadA` binder (dropped from the value). Refuted at "
                     "(1,2,1): rival returns 1, C4 demands 1/2 — a distinct input "
                     "from the drop-spreadB rival, moving the large-spread role "
                     "from spreadB to spreadA.",
        "witness": _witness(1, 2, 1, _VAL_TAIL),
    },

    # ---- linear-in-agree: drop one factor of agree, C4 ----
    {
        "id": "linear-in-agree",
        "kind": "uniqueness",
        "expect": "reject",
        # Return `agree / (spreadA*spreadB)` — linear in agree, not the squared
        # coefficient. Correct only when agree = 1; wrong for agree ≥ 2. Abuses
        # the `agree` binder (its square). Keeps gold's plan.
        "module": _inner(
            "    let v : Rat := if agree.toExact = 0 then 0"
            " else (agree.toExact : Rat)\n"
            "                     / ((spreadA.toExact : Rat) * spreadB.toExact)\n"
            "    return some (p, v)"),
        "refinement": "dividing a SINGLE factor of the agreement count into the "
                      "aggregate product (linear in agree, not its square) is the "
                      "shape of a patch that dropped one factor of the numerator. "
                      "It agrees with the squared coefficient only at agree = 1 "
                      "and diverges for larger counts (e.g. at agree = 2, "
                      "spreadA = spreadB = 1 it returns 2 vs the correct 4), so "
                      "the exact-value regression tests fail and it would NOT "
                      "resolve.",
        "rationale": "REJECT from C4 (v = agree*agree / (spreadA*spreadB)): the "
                     "rival returns agree / (spreadA*spreadB), differing whenever "
                     "agree ≠ 1. Abuses the `agree` binder (only one factor "
                     "used). Refuted at (2,3,3): rival returns 2/9, C4 demands "
                     "4/9 — a distinct input point that varies `agree` away from 1. "
                     "(Corrected by audit to the tuple the witness below actually "
                     "calls at; note (2,1,1) is NOT admissible here, since the "
                     "requires demand agree ≤ spreadA and agree ≤ spreadB.)",
        "witness": _witness(2, 3, 3, _VAL_TAIL),
    },

    # ---- the SHORT-CIRCUIT dropped from the PLAN, C5 (added by audit) ----
    {
        "id": "plan-no-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        # Gold's plan with the `.zeroThen` step REMOVED: the two ratios are formed
        # unconditionally. The returned VALUE is gold's (the value expression still
        # carries its own zero test), and the plan materialises no integer product,
        # so it is total at every width on every NON-degenerate triple. What it
        # loses is the one thing the tie clause exists to pin: on an admissible
        # DEGENERATE triple — one whose spread vanishes — a plan that forms its
        # quotients unconditionally yields nothing at all.
        #
        # This is the rival the battery's own prose says C5+CT are for, and it was
        # missing: the two accept-lane controls state that dropping the zero test
        # from the VALUE must still verify precisely because the PLAN carries the
        # short-circuit, and nothing demonstrated that dropping it from the plan is
        # rejected. Added by audit.
        "module": _plan(
            "    let p : RatPlan :=\n"
            "      .mul (.ratio (.read .agree) (.read .spreadA))\n"
            "           (.ratio (.read .agree) (.read .spreadB))\n"),
        "refinement": "forming both quotients without deciding the no-agreement "
                      "case first is the shape of a patch that reassociated the "
                      "arithmetic and dropped the guard along with the old "
                      "expression. A partition that spreads every element into a "
                      "group of its own reaches this routine with a vanishing "
                      "spread AND a vanishing agreement count, and its faithful "
                      "counterpart divides by zero there: it produces a non-finite "
                      "score on an ordinary admissible input, so the failing test "
                      "`assert_all_finite(...)` still fails and it would NOT "
                      "resolve.",
        "rationale": "REJECT from C5 on the DEGENERATE subdomain, which no other "
                     "rival probes: at width 4 on (0, 0, 5) — admissible "
                     "(0 ≤ 0 ≤ 5, all three inside a 4-bit word) — the plan's first "
                     "ratio has a vanishing divisor, so the plan yields `none` "
                     "where C5 demands `some 0`. Machine-checked as a standalone "
                     "arithmetic fact: gold's plan evaluates to `some 0` at that "
                     "point and this one to `none`, so the two plans are "
                     "OBSERVABLY different on this carrier and the case is not "
                     "vacuous. C1..C4 all hold (the returned value is gold's), so "
                     "the plan clause is the only discriminator. Refuted at input "
                     "(agree=0, spreadA=0, spreadB=5).",
        "witness": _witness(0, 0, 5, _plan_tail(4, 0, 0, 5)),
    },

    # ---- short-circuit guard on the WRONG aggregate, C5 (added by audit) ----
    {
        "id": "plan-guard-on-spreadA",
        "kind": "uniqueness",
        "expect": "reject",
        # The short-circuit is present but keyed on the FIRST SPREAD instead of the
        # agreement count. On every triple with a positive spread it agrees with
        # gold's plan exactly, so it is a near-miss: it answers zero on precisely
        # the wrong degenerate inputs. Varies which binder the `.zeroThen` step
        # reads, a distinction no other case moves. Added by audit.
        "module": _plan(
            "    let p : RatPlan :=\n"
            "      .zeroThen (.read .spreadA)\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
            "              (.ratio (.read .agree) (.read .spreadB)))\n"),
        "refinement": "keying the short-circuit on one spread rather than on the "
                      "agreement count is the shape of a patch that guarded the "
                      "wrong quantity when rewriting the expression. It answers "
                      "zero when the FIRST clustering's aggregate vanishes and "
                      "divides unconditionally when the SECOND one does, so on a "
                      "partition whose second aggregate vanishes it is non-finite "
                      "— the failing test still fails and it would NOT resolve.",
        "rationale": "REJECT from C5 at the MIRROR degenerate triple: at width 4 "
                     "on (0, 5, 0) — admissible (0 ≤ 5, 0 ≤ 0) — the guard reads "
                     "spreadA = 5, so it does NOT fire, and the second ratio then "
                     "has a vanishing divisor: the plan yields `none` where C5 "
                     "demands `some 0`. Machine-checked standalone: gold's plan is "
                     "`some 0` there and this one `none`, so the plans differ "
                     "observably on this carrier. Distinct from "
                     "`plan-no-short-circuit` in WHICH binder the guard reads and "
                     "at which degenerate point it fails. Refuted at input "
                     "(agree=0, spreadA=5, spreadB=0).",
        "witness": _witness(0, 5, 0, _plan_tail(4, 0, 5, 0)),
    },

    # ---- a PRODUCT materialised in the GUARD slot, C5 (added by audit 2) ----
    {
        "id": "plan-product-in-guard-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # The short-circuit is keyed on the agreement count SQUARED rather than on
        # the count itself. It fires on exactly the same triples gold's does
        # (a*a = 0 iff a = 0), so it answers zero on precisely the right degenerate
        # inputs and denotes gold's rational everywhere the square fits the word --
        # a genuine near-miss. What it adds is an `IntPlan.mul` in the one
        # structural position no other rival occupies: the `.zeroThen` GUARD. Every
        # shipped C5 rival materialises its product inside the RATIO steps (a
        # numerator or a divisor), so the guard slot's partiality was undefended,
        # and C5's `∀ w` quantifier reaches it exactly the same way.
        "module": _plan(
            "    let p : RatPlan :=\n"
            "      .zeroThen (.mul (.read .agree) (.read .agree))\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
            "              (.ratio (.read .agree) (.read .spreadB)))\n"),
        "refinement": "testing the SQUARE of the agreement count against zero, "
                      "rather than the count itself, is the shape of a patch that "
                      "reused an already-squared intermediate for the "
                      "no-agreement check. The test is mathematically equivalent, "
                      "but forming that square in fixed-width arithmetic overflows "
                      "at the failing scale (an agreement count of ≈3.0e9 squares "
                      "to ≈9.0e18, past the signed 64-bit maximum ≈9.22e18), so "
                      "the faithful counterpart computes its guard from a wrapped "
                      "-- possibly negative -- quantity and is non-finite on the "
                      "large-count input: the failing test still fails and it "
                      "would NOT resolve.",
        "rationale": "REJECT from C5, attacking the GUARD slot rather than a ratio "
                     "step. The plan is a near-miss on both halves of C5's "
                     "statement: the guard fires on exactly gold's degenerate "
                     "triples (a*a = 0 iff a = 0), and where the square fits the "
                     "word the plan denotes gold's rational -- machine-checked, "
                     "`RatPlan.value 4 1 1 2` agrees with gold's plan. It is "
                     "refuted only by the partiality the extra product introduces: "
                     "at width 4 on (7, 7, 7) -- all three inside a 4-bit word -- "
                     "the guard step 7*7 = 49 leaves the word, so the plan yields "
                     "`none` where C5 demands `some 1`, while gold's plan yields "
                     "`some 1` there. Instantiated at a THIRD kind of C5 point "
                     "(4; 7,7,7), with `agree` driven to 7 -- the largest "
                     "agreement value any case reaches, and the only C5 probe whose "
                     "three aggregates are equal and all at the word boundary. "
                     "Refuted at input (agree=4, spreadA=9, spreadB=11) — a "
                     "fourteenth distinct call, and the only one whose agreement "
                     "count is 4 and whose spreads are both odd and unequal.",
        "witness": _witness(4, 9, 11, _plan_tail(4, 7, 7, 7)),
    },

    # ---- plan keyed on the CALL'S OWN WIDTH, C5 (added by audit) ----
    {
        "id": "plan-keyed-on-call-width",
        "kind": "uniqueness",
        "expect": "reject",
        # The only rival that moves the `width` binder, which the coverage
        # reporter flags as pinned to 64 across every other reject witness. The
        # plan is chosen on the CALL's width: report the product-first assembly at
        # narrow widths and the divide-first one above. `plan-chosen-per-input`
        # branches on the AGGREGATES; this branches on the width itself, so a C5
        # instantiated only at the call's own width would admit it. Refuted from a
        # width-8 call, so the witness exercises `width` at a value no other case
        # reaches. Added by audit.
        "module": _impl(
            "    let pd : RatPlan :=\n"
            "      .ratio (.mul (.read .agree) (.read .agree))\n"
            "             (.mul (.read .spreadA) (.read .spreadB))\n"
            "    let pr : RatPlan :=\n"
            "      .zeroThen (.read .agree)\n"
            "        (.mul (.ratio (.read .agree) (.read .spreadA))\n"
            "              (.ratio (.read .agree) (.read .spreadB)))\n"
            "    let p : RatPlan := if width ≤ 8 then pd else pr\n"
            "    let v : Rat :=\n"
            "      if agree.toExact = 0 then (0 : Rat)\n"
            "      else (agree.toExact : Rat) * agree.toExact\n"
            "             / ((spreadA.toExact : Rat) * (spreadB.toExact : Rat))\n"
            "    return some (p, v)"),
        "refinement": "selecting the assembly by the register width the aggregates "
                      "arrive in is the shape of a patch that kept the old order "
                      "for the narrow-word path and rewrote only the wide one. The "
                      "old order overflows at every width once the aggregates are "
                      "large enough relative to it, so the counterpart is still "
                      "non-finite on the narrow path and would NOT resolve.",
        "rationale": "REJECT from C5, and it is the WIDTH attack: on a width-8 "
                     "call the guard fires, so the plan returned IS the "
                     "product-first one, and C5 must hold of it at EVERY width — "
                     "at width 4 on (1, 7, 7) it yields `none` where C5 demands "
                     "`some (1/49)`. Machine-checked standalone that the case is "
                     "not vacuous in either direction: the product-first plan DOES "
                     "have a value at width 8 on (1, 7, 7), so this rival is "
                     "value-correct at its own call width and only the ∀-width "
                     "quantifier refuses it. Refuted at (agree=1, spreadA=7, "
                     "spreadB=7) called at WIDTH 8 — the only reject witness whose "
                     "`width` is not 64.",
        "witness": _witness(1, 7, 7, _plan_tail(4, 1, 7, 7), w=8),
    },

    # ---- zero-branch corrupted, C3 ----
    {
        "id": "zero-branch-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        # Return a non-zero constant when agree = 0 (correct on every agree ≠ 0
        # input, diverges on the no-agreement subdomain). Attacks C3.
        "module": _inner(
            "    let v : Rat := if agree.toExact = 0 then 1 else ra * rb\n"
            "    return some (p, v)"),
        "refinement": "returning 1 when agree = 0 (no co-grouped pair) instead of "
                      "0 is the shape of a patch that mis-set the no-agreement "
                      "short-circuit. A clustering pair with zero agreement must "
                      "score 0; the counterpart would report a non-zero score on "
                      "the no-shared-pair inputs, so the exact-value tests fail "
                      "and it would NOT resolve. Partial-domain: diverges only on "
                      "the agree = 0 subdomain.",
        "rationale": "REJECT from C3 (agree = 0 → v = 0): on agree = 0 the rival "
                     "sets v = 1, so the zero clause cannot hold. (C1/C2/C5 still "
                     "hold since 1 is nonnegative and the plan is gold's.) Refuted "
                     "at (0,1,1) — the only input point on the agree = 0 "
                     "subdomain, which no other rival probes.",
        "witness": _witness(0, 1, 1, _ZERO_TAIL),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus 2 AXIOM_TESTS. This
# bundle models the purely-functional core — a single method
# `fowlkesCoeffSquared` returning the SQUARED similarity coefficient together
# with the PLAN by which it is assembled — where the sibling contracts one float
# function `pair_similarity_index` over three axiomatized numeric callees
# (ratio/root/mul) with an explicit representability precondition on the root.
# The value surface carries across; the axiom lane becomes G-AX's job and the
# float representability GATE becomes the plan clause C5.
#
#   nagini case                          -> here
#   -----------------------------------------------------------------------
#   prepatch-overflow-order              -> prepatch-product-first-plan     PORTED
#   no-square-roots-squared-index        -> (none)                          N/A (collapses to gold)
#   single-ratio-drop-qk                 -> single-ratio-drop-spreadB       PORTED
#                                           + single-ratio-drop-spreadA      ADDED (mirror)
#   zero-branch-nonzero-partial-domain   -> zero-branch-nonzero             PORTED
#   pos-control-branch-reorder           -> pos-control-branch-reorder      PORTED
#   pos-control-inline-cheapest          -> pos-control-commuted-ratios     PORTED (reshaped)
#   admissibility-large-count-regime     -> admissibility-large-count-regime PORTED
#   (new)                                -> linear-in-agree                 ADDED
#   (new)                                -> plan-materialises-squares       ADDED
#   (new)                                -> plan-reads-spreadA-twice        ADDED
#   (new)                                -> plan-lone-ratio-oracle-echo     ADDED
#   (new)                                -> plan-chosen-per-input           ADDED
#   (new)                                -> guarded-none-on-large-product   ADDED
#   (new)                                -> plan-no-short-circuit           ADDED BY AUDIT
#   (new)                                -> plan-guard-on-spreadA           ADDED BY AUDIT
#   (new)                                -> plan-keyed-on-call-width        ADDED BY AUDIT
#   (new)                                -> plan-product-in-guard-slot      ADDED BY AUDIT 2
#   AXIOM_TESTS (x2)                     -> (none)                          DROPPED
#
# 6 ported (2 positives, 1 admissibility, 3 rivals), 10 rivals added, 2 extra
# positives added, 1 rival N/A, 2 axiom tests dropped = 19 velvet cases
# (5 verify, 14 reject).
#
# N/A (no-square-roots-squared-index): the nagini rival returns
#   (tk/pk)*(tk/qk) = tk^2/(pk*qk), i.e. the SQUARE of the similarity index. This
#   bundle models the SQUARED coefficient itself (the single square root is
#   peeled by squaring — see mapping.md §3 / refinement.md), so that rival's
#   value is EXACTLY the gold value on this carrier. It is not a wrong impl here;
#   there is no discriminating witness because none exists (its abstraction and
#   gold's coincide). Legitimately omitted, not a dropped-because-hard case.
# PORTED (prepatch-product-first-plan): the load-bearing G-DIFF rival, and the
#   one this battery is organised around. It returns gold's exact value and is
#   rejected on the PLAN alone — no hand-written fixed-width range check inside
#   the rival's own impl region does the discriminating, which is what the
#   previous revision of this bundle was refuted for.
# PORTED + ADDED (single-ratio): the nagini rival drops the second marginal qk.
#   Ported as single-ratio-drop-spreadB; a mirror single-ratio-drop-spreadA is
#   ADDED so BOTH spread binders are abused, refuted at distinct inputs (1,1,2)
#   and (1,2,1).
# ADDED (linear-in-agree): divides a single factor of the agreement count into
#   the aggregate product (linear, not squared). Built to ABUSE the `agree`
#   binder. Refuted at (2,3,3).
# ADDED BY AUDIT (three plan rivals the port was missing, each machine-checked
#   rejected with a discriminating witness before being landed here):
#   plan-no-short-circuit (gold's plan with `.zeroThen` DROPPED — refuted on the
#   admissible DEGENERATE triple (0,0,5), the subdomain the whole CT+C5 argument
#   rests on and which no shipped rival probed); plan-guard-on-spreadA (the
#   short-circuit kept but keyed on the wrong aggregate — refuted at the mirror
#   degenerate triple (0,5,0), varying WHICH binder the guard reads); and
#   plan-keyed-on-call-width (the assembly selected by the call's own width —
#   refuted from a WIDTH-8 call, the only reject witness whose `width` is not 64,
#   which closes the coverage gap that every other reject witness pins `width`).
# ADDED BY AUDIT 2 (plan-product-in-guard-slot): every C5 rival above materialises
#   its integer product inside a RATIO step — a numerator or a divisor — so the
#   `.zeroThen` GUARD slot was the one structural position in a `RatPlan` whose
#   partiality nothing defended. This rival squares the agreement count in the
#   guard: the test is mathematically equivalent (a*a = 0 iff a = 0), so it fires
#   on exactly gold's degenerate triples and denotes gold's rational wherever the
#   square fits the word (machine-checked: it agrees with gold's plan at
#   width 4 on (1,1,2)), and it is refuted ONLY by the partiality the extra
#   product introduces — at width 4 on (7,7,7) the guard step 49 leaves the word
#   and the plan yields `none` where gold's yields `some 1`. Two sibling probes
#   in the same structural position were also measured rejected before this one
#   was chosen (a guard on `spreadA * spreadB`, and a value that drops `agree`
#   from the nonzero branch entirely).
# ADDED (the five plan rivals): one per family the repair must survive —
#   over-approximation (prepatch-product-first-plan: the association gold
#   removes), partial domain (plan-materialises-squares: value-correct while the
#   squares fit the word, valueless above it), boundary token swap
#   (plan-reads-spreadA-twice: the first spread read in both factors), oracle
#   echo (plan-lone-ratio-oracle-echo: C4's closed form echoed as the value with
#   a plan that computes something else), and the freedom the repair itself
#   leaves (plan-chosen-per-input: the plan chosen per call so that the
#   product-first assembly is reported exactly where its product happens to fit
#   a 64-bit word). guarded-none-on-large-product attacks C1 from the other
#   side, narrowing the OUTPUT rather than the plan.
# PORTED (zero-branch-nonzero): returns a non-zero constant on the agree = 0
#   subdomain, attacking C3; refuted at (0,1,1).
# PORTED (positives): pos-control-branch-reorder (guard the non-zero case first)
#   and pos-control-commuted-ratios (pair the agreement count with the other
#   spread first, plan included — a plan TERM that is not gold's, so C5 is shown
#   to be a property and not a template). The sibling's cheapest-inline positive
#   is reshaped into the latter: inlining the value alone would no longer be a
#   structurally different assembly, since the plan is what carries the
#   association. Each keeps the obligation STATEMENT byte-identical and retunes
#   only the elided tactic body; both verify EXIT 0.
# PORTED (admissibility): the method HAS real preconditions, so the probe is not
#   vacuous. It asserts in-region that the large-count regime motivating the fix
#   is in-domain, that its exact squared coefficient is a well-defined
#   nonnegative rational, and that each aggregate fits a 64-bit word while the
#   product of the two spreads does not — the modelling fact C5 turns on. A live
#   decidable assert `loom_solve` discharges; the impl is otherwise gold so
#   C1..C5 close with the frozen proof. Establishes PRECOND-NOT-TOO-STRONG on
#   the regime the fix targets.
#
# VACUOUS (frame / permission-mutation): the nagini sibling records
#   has_readonly_input=False (all four params are by-value floats — no
#   Acc(.,1/2) token anywhere). Vacuous here for the stronger backend reason too:
#   Velvet is referentially transparent and this bundle declares no `mut` binder —
#   the three inputs are immutable Int values with no heap footprint — so there is
#   no read-only input to overwrite and no substitute probe to build. Not
#   fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   the single square root peeled by squaring == the real numpy formula, that the
#   gold plan evaluated in fixed-width machine arithmetic never leaves the word
#   on admissible aggregates, and that the product-first plan does at F2P
#   scale), and this gate ignores AXIOM_TESTS regardless.
#
# KNOWN HOLE (divergence / non-termination), recorded by audit rather than
#   claimed as covered. This bundle sets
#   `set_option loom.semantics.termination "total"`, so a diverging impl is NOT
#   admitted by the obligation, and a rival whose body loops forever IS rejected
#   by the verifier — measured: the module fails with `Decreasing annotations are
#   required in total correctness semantics` plus `Failed to prove assertion
#   without names: WPGen … sorry`. The class is therefore not vacuous in
#   principle. It is NOT SHIPPED as a case because no discriminating WITNESS
#   could be built for it on this carrier: the witness route this battery uses
#   collapses the straight-line `do` block through `triple_pure`, which does not
#   apply to a looping body (measured: `rcases failed: 'right✝ : p' is not an
#   inductive datatype`), and an alternate `out ≠ out` route failed against the
#   frozen solution as well as the rival, so it discriminates nothing. A reject
#   case is only admissible with a witness that elaborates against the rival and
#   FAILS against gold; absent one, this is an honest gap and not a case.
#
# CLAUSE / BINDER COVERAGE. The one obligation (`prove_correct
#   fowlkesCoeffSquared`) is DEFENDED (four soundness positives + the
#   admissibility case) and ATTACKED (fourteen reject rivals). The independent
#   top-level postcondition clauses:
#     C1 (out = some (p, v))              — attacked by guarded-none-on-large-product.
#     C3 (agree = 0 → v = 0)              — attacked by zero-branch-nonzero.
#     C4 (agree ≠ 0 → exact value)        — attacked by single-ratio-drop-spreadB,
#                                           single-ratio-drop-spreadA, linear-in-agree.
#     C5 (the plan yields the coefficient — attacked by prepatch-product-first-plan,
#         at every machine word width)      plan-materialises-squares,
#                                           plan-reads-spreadA-twice,
#                                           plan-lone-ratio-oracle-echo,
#                                           plan-chosen-per-input,
#                                           plan-no-short-circuit,
#                                           plan-guard-on-spreadA,
#                                           plan-keyed-on-call-width,
#                                           plan-product-in-guard-slot.
#     C2 (0 ≤ v) is NOT an independent clause: it is derivable from C3 (v = 0 on
#         agree = 0) and C4 (v pinned to a nonnegative rational on agree ≠ 0), so
#         any impl violating C2 already violates C3 or C4. No dedicated C2 rival
#         is authored.
#   The nine C5 rivals are refuted by THREE different routes — plan partiality
#   from an overflowing integer product (`none` where a value is demanded:
#   product-first, squares, per-input, keyed-on-call-width, product-in-guard-slot
#   — the last of these in the `.zeroThen` GUARD step rather than in a ratio
#   step, so all three of a `RatPlan`'s structural positions are probed for
#   partiality), plan partiality from
#   a VANISHING DIVISOR on the admissible degenerate subdomain (no-short-circuit,
#   guard-on-spreadA), and plan VALUE mismatch (a total plan denoting the wrong
#   rational: spreadA twice, lone ratio) — so the clause is exercised on every
#   half of its statement, including the degenerate case that motivates it.
#   All FOUR binders — the three aggregates AND `width` — are varied across the
#   fourteen reject witnesses, which sit at FOURTEEN distinct calls:
#     (64; 1,2,3)      product-first plan
#     (64; 2,3,5)      materialises squares
#     (64; 1,4,5)      reads spreadA twice
#     (64; 3,7,7)      lone-ratio oracle echo
#     (64; 5,6,6)      plan chosen per input
#     (64; 1,2^62,4)   guarded `none` on the large product (C1)
#     (64; 1,1,2)      single-ratio drop spreadB (C4)
#     (64; 1,2,1)      single-ratio drop spreadA (C4)
#     (64; 2,3,3)      linear in agree (C4)
#     (64; 0,0,5)      short-circuit dropped from the plan — DEGENERATE
#     (64; 0,5,0)      short-circuit on the wrong aggregate — MIRROR DEGENERATE
#     ( 8; 1,7,7)      plan keyed on the call's own width — the only non-64 width
#     (64; 4,9,11)     product materialised in the plan's GUARD slot
#     (64; 0,1,1)      zero-branch nonzero (C3)
#   `agree` is moved off 1 (to 2, 3, 4, 5) and to 0 (four cases); each spread is
#   driven to 0 in one case and into the out-of-word regime (2^62) in another;
#   `width` is moved off 64. No binder is pinned across the rivals, so the
#   manifest demonstrates the post-image's dependence on each of the four. The
#   C5 witnesses additionally vary the (width, aggregates) point at which the
#   plan clause is INSTANTIATED — (4; 1,7,7), (4; 1,1,7), (4; 1,1,2),
#   (4; 0,0,5), (4; 0,5,0), (4; 7,7,7) — so the plan is probed where a product
#   overflows (in a numerator, in a divisor, and in the guard), where a divisor
#   vanishes, and where the plan is total but denotes the wrong number. The last
#   point drives all three aggregates to the 4-bit word's positive boundary at
#   once, which no other instantiation does.
AXIOM_TESTS = []
