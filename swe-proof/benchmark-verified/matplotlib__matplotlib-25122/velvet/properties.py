"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25122 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct windowSum`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it ELABORATES against the rival and FAILS against the
frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  windowSum (ulp : Rat) (maxMag : Rat) (coeffs : List Rat) return (out : Rat)
    require RealArith ulp maxMag
    require Accumulable maxMag ulp coeffs
    ensures WithinRoundoff ulp coeffs out                -- the WHOLE pin (C1)

The method reports the order-preserving total of a finite sequence of
real-valued coefficients, with each coefficient's own sign preserved, to within
the accumulation error of the arithmetic that carries it. The reference total of
one whole sequence is the pure front-recursive fold ``listSum`` (``listSum (x ::
xs) = x + listSum xs``), a TRANSPARENT ``def`` over the method's own input —
there is no opaque answer-key oracle and the ``axioms`` region is empty, so
pinning ``out`` to that fold is grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``WithinRoundoff ulp coeffs out``, i.e.
``|out - listSum coeffs| <= coeffs.length * 2*ulp * magSum coeffs``) is the sole
clause and the sole obligation. It is a total function of ``ulp`` and ``coeffs``
and pins the result at every admissible input: which coefficients are summed,
that each contributes with its own sign, and that none is dropped or reflected
to its magnitude. Every uniqueness rival therefore targets C1.

THE TWO ``require``s ARE DOMAIN, NOT SLACK (G-PANEL-2 repair). ``ulp`` is the
relative rounding of the accumulating arithmetic and ``maxMag`` its finite range,
both chosen by the caller ALONG WITH the coefficients — the real reduction
accumulates in the coefficient array's own format, so the accuracy it guarantees
scales with THAT format's rounding rather than with a fixed binary64 constant.
``require RealArith ulp maxMag`` says the pair is one a real binary format
actually offers -- each format fixes its rounding AND its range together, so the
two are not independently dialable, and in particular the rounding cannot be
driven toward zero (which would demand exactness no rounding accumulation has).
``require Accumulable maxMag ulp coeffs`` (``magSum coeffs + roundoffBound ulp
coeffs <= maxMag``) says the sequence AND the error the same arithmetic incurs on
it both sit inside that range, which is what makes "the reduction returns a real
value with this accuracy" true rather than saturating. Neither weakens the sign discrimination: every witness below
instantiates ``ulp`` at the TIGHTEST real rounding (2**-53), where the bound is
smallest, and the signed/magnitude gap on the discriminating windows exceeds the
bound even at the LOOSEST real rounding (2**-11, a float16 significand). There
are three input binders now (``ulp``, ``maxMag``, ``coeffs``); the rivals vary
``coeffs``, which is the binder the fix is about.

THE LOAD-BEARING DISTINCTION is the SIGN of each coefficient. The pre-change
reading folded each coefficient in by its MAGNITUDE (a magnitude total), which
agrees with the signed total on every all-nonnegative sequence and DIVERGES
exactly on a sequence containing a negative coefficient — the domain the failing
test drives (a coefficient pattern with negative lobes). C1 pins the signed
total, so the magnitude rival contradicts it at every negative-coefficient
input.

CARRIER NOTE (decisive for this port). The carrier is Mathlib ``Rat`` (mapping.md
§2 — the exact signed value is the behaviour, and it is order/value exact and
computable). ``listSum`` is a transparent computable ``def``, so a rival's
disagreement with C1 is DECIDABLE at a concrete input — no conditioning on an
opaque term, hence no witness binds a hypothesis and the gate's consistency
probe is a no-op. But the tester+``decide`` path IS DEAD here: the postcondition
mentions ``listSum`` over ``Rat`` and ``prove_postcondition_decidable_for`` /
``derive_tester_for`` yield a tester on which ``decide`` gets stuck —
re-measured at audit, the exact error is ``Tactic `decide` failed for
proposition windowSumTester [-1] = false because its `Decidable` instance
instDecidableEqBool (windowSumTester [-1]) false did not reduce to `isTrue` or
`isFalse``` (the stall is at the ``Bool`` equality wrapping the stuck ``Rat``
tester body, NOT at ``instDecidableEqRat`` as an earlier revision of this note
claimed). So each witness
instead EXTRACTS the executable program and refutes C1 directly on the
transparent ``listSum``: every rival is written LOOP-FREE (a ``coeffs.map`` /
``coeffs.drop`` expression), so its extracted ``windowSumExec`` REDUCES under
``simp only [windowSumExec, windowSum, NonDetT.run, …, listSum_cons,
listSum_nil]`` to a concrete ``Rat`` (in)equality the closer discharges.

THE SECOND SUBJECT IS NOT GOLD — AND MUST NOT BE (audit correction). The frozen
impl is a ``while`` loop, so its extracted ``windowSumExec`` elaborates through
``forIn``/``NonDetT`` gadget terms the kernel does not evaluate. Building any of
these witnesses against the frozen solution therefore fails with

    Tactic `decide` failed … because its `Decidable` instance `instDecidableNot`
    did not reduce to `isTrue` or `isFalse`.

That is a STUCK REDUCTION, not a refutation: the kernel never evaluated the
claim, so the exit code discriminates NOTHING — the identical error appears for a
claim that is TRUE of gold. (An earlier revision of this file asserted the
opposite, that the witness "FAILS on gold — the discrimination the gate
requires". That reasoning is exactly the defect class ``gates/pbt.py``'s
``_STUCK_REDUCTION`` screen exists to catch, and it is retracted here.) The real
discriminator is a LOOP-FREE VERIFYING impl of the same spec, whose ``…Exec``
does reduce, so ``decide`` returns a verdict. Each reject case therefore names
one explicitly via ``witness_reference`` (``_REF``, the loop-free direct fold —
which the gate independently checks shares the frozen spec AND verifies before
using it). Against ``_REF`` each witness fails SEMANTICALLY, by the closer
proving the negation false — measured, e.g. ``decide proved that the proposition
-1 ≠ -1 is false`` and ``… 8 ≠ 8 is false``. That is a real refutation of the
concrete claim, and it is sound for the same reason gold would have been: an impl
the verifier ACCEPTS cannot violate its own spec.

WITNESS CLOSER (measured). After the unfold the goal is a concrete ``Rat``
(dis)equality. ``decide`` alone reduces the ``Decidable`` instance but not ``Rat``
ARITHMETIC (the spec_guide trap; a bare ``decide`` gets stuck on any surviving
``a + b``). Two shapes were SEEN to close and discriminate with real builds:
  * single-coefficient inputs leave no surviving addition (``x + 0`` folds away),
    so ``simp only [Rat.add_zero]`` then ``decide`` closes;
  * a multi-coefficient input leaves nested ``Rat`` sums, so ``simp only
    [Rat.add_zero]`` clears the accumulator seed and each surviving sum is
    normalised to its numeral by ``rw [show (a + b = n) by simp [Rat.add_def,
    Rat.normalize]]`` before ``decide``.
No banned token (``sorry``/``admit``/``native_decide``/``axiom``/``opaque``).
Every witness was checked out-of-band with ``scripts/lean_verify.sh``: it
ELABORATES against its rival (exit 0) and is REFUTED against the loop-free
verifying reference ``_REF`` (exit 1, by the closer deciding the negation FALSE —
a semantic verdict, not a stuck reduction).

ADVERSARIAL READ of the nagini classes on THIS carrier (full accounting in the
footer):
  * SOUNDNESS / positive controls — APPLY. Two structurally-different CORRECT
    reshapes (the cheapest direct fold; the gold backward loop with a renamed
    accumuland) MUST still verify, else the spec is SPEC-TOO-STRONG.
  * ADMISSIBILITY — APPLIES DIRECTLY. The method now carries two ``require``s
    (``RealArith ulp maxMag``, ``Accumulable maxMag ulp coeffs``), so the nagini "a normal input is
    admitted" probe is LIVE rather than vacuous: a precondition that excluded an
    ordinary window would read exactly like one every impl meets. Both cases
    below therefore pick inputs that SATISFY both ``require``s — the degenerate
    sequence and an F2P-shaped negative-lobe pattern — and show C1 is
    dischargeable there.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling holds ``window`` at
    a fractional heap permission a rival can illegally overwrite. Velvet is
    referentially transparent: ``coeffs`` is an immutable value, not ``mut``,
    with no heap, aliasing, or permission system. No read-only input to
    overwrite and no substitute probe fabricated.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS on this bundle. The
    nagini sibling carries a ``vacuous-nonterm-amp`` rival (spin forever, satisfy
    every value clause vacuously). This bundle runs under ``set_option
    loom.semantics.termination "total"``, under which a postcondition is claimed
    of ALL runs rather than only terminating ones, so the frozen ``while`` and any
    loop a rival splices each owe a strictly decreasing measure. A spun loop with
    no measure is refused at elaboration, and the sharper shape is refused too:
    supplying a ``decreasing`` clause whose measure the body never shrinks fails
    on the measure's OWN descent goal (see the footer entry for the builds). So
    nothing verifies vacuously. (An earlier version of this bullet contrasted the
    cell with a ``partial`` cohort that admits the hole, citing an internal
    findings doc. That cohort is withdrawn: all 500 velvet bundles set
    ``"total"``, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness``, so the option and the ``open`` cannot
    disagree.) No reject case is written and none is claimed dropped: the refusal
    fires at the ``method``, so no witness can elaborate against a diverging
    rival.
  * THE POWER / SQUARED SURFACE — CARRIER NARROWING. The nagini sibling contracts
    TWO functions (an amplitude signed-sum AND a power squared-sum) and carries
    power-branch rivals (frame-mutation-pwr, weak-linear-pwr) plus two power
    positives. This bundle models ONLY the signed linear total (mapping.md §2:
    the squared sites are mathematically identical to their pre-patch forms and
    the SINGLE discriminating primitive is the signed linear sum). There is no
    ``power`` method to attack, so those cases have no counterpart — carrier
    narrowing, not a dropped attack.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25122"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen windowSum impl body (the backward
# ---- `while` fold), everything strictly BETWEEN the method's `-- impl-start`
# ---- and `-- impl-end`. Lies wholly inside the single impl region and is unique
# ---- in the file (both facts asserted at load by _swap), so each edit keeps
# ---- same_spec by construction and leaves the `prove_correct windowSum`
# ---- STATEMENT intact.
_IMPL = (
    "    let mut acc : Rat := 0\n"
    "    let mut i := coeffs.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ coeffs.length\n"
    "      invariant acc = listSum (coeffs.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let x := coeffs[i - 1]!\n"
    "      acc := x + acc\n"
    "      i := i - 1\n"
    "    return acc"
)
assert _BASE.count(_IMPL) == 1, "windowSum impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a loop-free correct reshape (whose residual goal no
# ---- longer needs the backward-fold step lemma) may retune it without touching
# ---- the spec or dropping the obligation. Unique.
_PROOF = (
    "prove_correct windowSum by\n"
    "  loom_solve\n"
    "  rw [listSum_drop_step coeffs i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "prove_correct windowSum body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a loop-free correct reshape
    whose residual goal no longer needs the backward-fold step lemma)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble + closers. The tester+`decide` path is DEAD (the Rat
# ---- postcondition's Decidable instance does not reduce), so every witness
# ---- EXTRACTS the executable program and refutes C1 directly on the transparent
# ---- `listSum` / `roundoffBound`. The unfold set below reduces a LOOP-FREE
# ---- rival's `…Exec` to a concrete Rat value; gold's `while`-loop `…Exec` stays
# ---- stuck, so the witness fails on gold. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script masks the verdict.
#
# ---- C1 IS A TOLERANCE CLAUSE, so a witness cannot merely exhibit `out ≠
# ---- listSum coeffs`: it must show the rival's output falls OUTSIDE the closed
# ---- interval `[listSum ∓ roundoffBound]`. Each witness therefore evaluates
# ---- three concrete numerals — the rival's output, the reference total, and the
# ---- bound at that input — and hands the resulting linear `Rat` comparison to
# ---- `grind` (which decides linear Rat arithmetic; a bare `decide` is stuck on
# ---- `Rat.instDecidableLe`, and unfolding `Rat.normalize` explodes the goal).
# ---- The three bounds are computed from the definition `n · 2·ulp · Σ|xᵢ|` at
# ---- the CONCRETE `ulp` each witness supplies. `ulp` is now a method PARAMETER
# ---- rather than a hardcoded constant (the relative rounding of the accumulating
# ---- arithmetic is chosen by the caller together with the coefficients), so each
# ---- witness instantiates it at the tightest rounding a real arithmetic has,
# ---- `ulp = 2⁻⁵³`, which makes the bound SMALLEST and the refutation hardest:
# ---- `1·2⁻⁵²·1 = 1/2⁵²` at `[-1]`, `2·2⁻⁵²·8 = 16/2⁵²` at `[3,5]`, and `0` at
# ---- `[]`. Every rival's error is astronomically larger than its bound (2 vs
# ---- 2⁻⁵², 3 vs 2⁻⁴⁸, 1 vs 0), which is exactly why the tolerance does not
# ---- blunt the battery. Each witness also supplies the `maxMag`
# ---- that PAIRS with that `ulp` in a real format (`2^1024 - 2^971`, the binary64
# ---- range), so `require RealArith ulp maxMag` holds, and each witness point is
# ---- far inside that range so `require Accumulable maxMag ulp coeffs` holds too.
# ---- Both preconditions hold and the refutation is of a claim the spec genuinely
# ---- makes at an admissible input.
_EXTRACT = "extract_program_for windowSum\n\n"
_UNFOLD_BASE = ("windowSumExec, windowSum, NonDetT.run, pure, NonDetT.bind,\n"
                "      ")

# The tightest relative rounding any real binary floating-point accumulator has
# (a binary64 significand): u = 2⁻⁵³. Instantiating `ulp` here makes
# `roundoffBound` as SMALL as the spec ever allows, so a witness that refutes the
# rival at this `ulp` refutes it at every coarser arithmetic too.
_ULP = "(1 / 2 ^ 53)"

# The finite range binary64 PAIRS with that rounding (`RealArith`'s third arm).
# `maxMag` is not free: the precondition admits only a real format's own pair, so
# a witness must supply this value rather than a convenient small one.
_MAXMAG = "(2 ^ 1024 - 2 ^ 971)"


def _witness(inp, out_val, extra_unfold, bound_lit, sum_lit, max_mag=None):
    """A refutation of the TOLERANCE clause C1 at one concrete input.

    ``out_val`` is the rival's extracted output, ``sum_lit`` the reference
    signed total and ``bound_lit`` the accuracy bound at ``ulp = 2⁻⁵³``, all as
    Rat numerals at ``inp``. ``max_mag`` defaults to the binary64 range that
    PAIRS with `ulp = 2⁻⁵³`, which is what `require RealArith ulp maxMag` admits;
    every witness point is far inside it, so `require Accumulable maxMag ulp
    coeffs` holds as well — a witness at a precondition-violating input would
    refute a claim the spec never made. The
    final `grind` decides ``¬(sum - bound ≤ out ∧ out ≤ sum + bound)`` — a linear
    Rat comparison between literals.
    """
    args = f"{_ULP} {max_mag or _MAXMAG} {inp}"
    return (
        _EXTRACT +
        "example :\n"
        f"    ¬ WithinRoundoff {_ULP} {inp}\n"
        f"      (match windowSumExec {args} with | DivM.res r => r | _ => 0) := by\n"
        f"  have hout : (match windowSumExec {args} with"
        f" | DivM.res r => r | _ => 0) = {out_val} := by\n"
        f"    simp only [{_UNFOLD_BASE}{extra_unfold}listSum_cons, listSum_nil]\n"
        "    grind\n"
        f"  have hb : roundoffBound {_ULP} {inp} = {bound_lit} := by\n"
        "    simp only [roundoffBound, magSum_cons, magSum_nil,"
        " List.length_cons,\n"
        "      List.length_nil]\n"
        "    grind\n"
        f"  have hs : listSum {inp} = {sum_lit} := by grind [listSum]\n"
        "  rw [WithinRoundoff, hout, hb, hs]\n"
        "  grind\n"
    )


# ---- THE WITNESS'S SECOND SUBJECT. The frozen impl cannot serve: its `…Exec` is
# ---- a `forIn`/`NonDetT` loop term the kernel does not evaluate, so `decide`
# ---- against it is STUCK for every claim, true or false, and its exit code
# ---- attributes nothing (measured: `instDecidableNot did not reduce to isTrue or
# ---- isFalse`). `_REF` is the loop-free direct fold — same frozen spec, and it
# ---- VERIFIES (exit 0, out-of-band and as pos-control-direct), which the gate
# ---- re-checks before using it. Its `…Exec` DOES reduce, so each witness is
# ---- refuted there by a real verdict (`decide proved … is false`). An impl the
# ---- verifier accepts cannot violate its own spec, so a genuine witness must
# ---- fail against it — the same soundness argument gold was supposed to carry.
_REF = _impl_reproved("    return (listSum coeffs)",
                      "prove_correct windowSum by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the total DIRECTLY via the transparent fold, no
        # per-coefficient loop. C1 pins `out` to `listSum coeffs` within the bound, so this is
        # the cheapest HONEST correct impl — and, since `listSum coeffs` is
        # GROUNDED in the argument (not an opaque answer key), it doubles as proof
        # the spec is not echo-vulnerable (any wrong fold fails C1). The loop is
        # gone, so the frozen proof's backward-fold step is unneeded and the
        # residual goal closes under `loom_solve` alone. Verified out-of-band.
        "module": _REF,
        "rationale": (
            "PASS SOURCE = C1 (`WithinRoundoff ulp coeffs out`). The post-image `listSum "
            "coeffs` is GROUNDED in the input (a total front-recursive fold, no "
            "opaque answer key), so `return listSum coeffs` is the honest cheapest "
            "CORRECT impl; C1 is literally that equality, so it MUST verify, else "
            "C1 is SPEC-TOO-STRONG. Ports the nagini echo-attempt-honest / "
            "pos-control-amp control (the cheapest impl satisfying the grounded "
            "pin), showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-loop-rename",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the gold backward `while` fold, invariant and decreasing
        # measure verbatim, but rename the per-coefficient accumuland `x` to `w`.
        # Same value flow, different surface; the frozen proof closes unchanged.
        # This is the direct port of the nagini pos-control-amp (fresh local
        # accumuland over the same backward loop). Verified out-of-band.
        "module": _impl(
            "    let mut acc : Rat := 0\n"
            "    let mut i := coeffs.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ coeffs.length\n"
            "      invariant acc = listSum (coeffs.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let w := coeffs[i - 1]!\n"
            "      acc := w + acc\n"
            "      i := i - 1\n"
            "    return acc"),
        "rationale": (
            "PASS SOURCE = C1. A correct impl with the SAME backward loop, "
            "invariant and `decreasing i` measure as gold but a renamed "
            "accumuland (`w := coeffs[i-1]!`, `acc := w + acc`) — same signed "
            "accumulation, different surface. The frozen loop proof closes as-is, "
            "so it MUST verify; else the spec over-fits the exact accumuland name "
            "(SPEC-TOO-STRONG). Ports the nagini pos-control-amp (structurally "
            "different but correct amplitude impl over the same backward fold)."
        ),
    },

    {
        "id": "pos-control-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the gold backward `while` with the accumulation COMMUTED
        # (`acc := acc + x` rather than `x + acc`). This is the nagini
        # pos-control-amp's actual reshape recipe, which the first port dropped in
        # favour of a mere identifier rename. It is a strictly stronger control:
        # the frozen tactic body does NOT close it (measured — `loom_solve` leaves
        # the residual `listSum (drop i) + coeffs[i-1]! = coeffs[i-1]! + listSum
        # (drop i)`, exit 1), so it exercises whether the SPEC accepts a correct
        # impl whose value flow the frozen script cannot handle verbatim. Retuned
        # with `Rat.add_comm` (the tactic body is elided from the spec view).
        # Verified out-of-band: exit 0.
        "module": _impl_reproved(
            "    let mut acc : Rat := 0\n"
            "    let mut i := coeffs.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ coeffs.length\n"
            "      invariant acc = listSum (coeffs.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let x := coeffs[i - 1]!\n"
            "      acc := acc + x\n"
            "      i := i - 1\n"
            "    return acc",
            "prove_correct windowSum by\n"
            "  loom_solve\n"
            "  rw [listSum_drop_step coeffs i (by omega) (by omega)]\n"
            "  simp_all [Rat.add_comm]"),
        "rationale": (
            "PASS SOURCE = C1. A CORRECT impl accumulating in the other operand "
            "order (`acc := acc + x`); `Rat` addition is commutative, so the value "
            "is identical at every input while the residual proof goal is NOT the "
            "frozen one. Unlike a rename, the frozen tactic body genuinely FAILS "
            "here (measured, exit 1), so this is the control that shows C1 accepts "
            "a correct impl on the strength of the SPEC rather than of the frozen "
            "script's shape. Direct port of the nagini pos-control-amp's commuted "
            "accumulation. If it could not be proven ⇒ SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-reverse",
        "kind": "soundness",
        "expect": "verify",
        # Reshape with the LARGEST semantic distance from gold that is still
        # faithful: total the coefficients in the OPPOSITE order. `Rat` addition is
        # associative and commutative, so `listSum coeffs.reverse = listSum coeffs`
        # at every input — but this is nowhere near the frozen proof, needing an
        # append lemma and an induction. Landed out-of-band (exit 0) after
        # `Rat.add_comm`/`Rat.add_assoc` (the generic `add_comm` fails to
        # synthesize `AddCommMagma Rat` on this carrier — noted so the next port
        # does not read the failure as a spec hole).
        "module": _impl_reproved(
            "    return (listSum coeffs.reverse)",
            "prove_correct windowSum by\n"
            "  loom_solve\n"
            "  have hap : ∀ (l : List Rat) (y : Rat), "
            "listSum (l ++ [y]) = y + listSum l := by\n"
            "    intro l y\n"
            "    induction l with\n"
            "    | nil => simp [listSum]\n"
            "    | cons c cs ihc =>\n"
            "      rw [List.cons_append, listSum_cons, ihc, listSum_cons,\n"
            "        ← Rat.add_assoc, Rat.add_comm c y, Rat.add_assoc]\n"
            # The reversed total EQUALS the reference total, so C1 then closes by
            # the exactness lemma: an exact answer is trivially within any
            # nonnegative tolerance. Proving the equality is still the whole
            # content of the control.
            "  have hrev : listSum coeffs.reverse = listSum coeffs := by\n"
            # `require_1 : Accumulable maxMag ulp coeffs` mentions `coeffs`, so the
            # induction would try to generalize it and leave an unprovable
            # `Accumulable maxMag ulp t` subgoal. The reversal identity does not
            # depend on the precondition, so clear it first (the recorded fix for
            # a `require` mentioning the induction target).
            "    clear require_1\n"
            "    induction coeffs with\n"
            "    | nil => simp [listSum]\n"
            "    | cons a t ih => rw [List.reverse_cons, hap, ih, listSum_cons]\n"
            "  rw [hrev]\n"
            "  exact withinRoundoff_exact ulp\n"
            "    (realArith_ulp_nonneg ulp maxMag require_2) coeffs"),
        "rationale": (
            "PASS SOURCE = C1. The strongest SPEC-TOO-STRONG probe available: the "
            "coefficients are totalled in REVERSE index order. C1 pins `out` to "
            "listSum coeffs`, and on the `Rat` carrier the total is order-"
            "insensitive, so this impl is CORRECT at every input while sharing "
            "almost nothing with the frozen proof. It verifies (exit 0), so C1 pins "
            "the VALUE of the total and not an accumulation order — the spec is not "
            "over-fitted to gold's traversal. Else SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — PORTED from nagini admiss-amp, now DIRECTLY rather than
    # re-aimed. That case established the read-only fractional-permission
    # precondition on an F2P-shaped window. This method carries two real
    # `require`s (`RealArith ulp maxMag`, `Accumulable maxMag ulp coeffs`), so the classic "a
    # normal input is admitted" probe is LIVE: a precondition that quietly
    # excluded ordinary windows would make C1 unfalsifiable where it matters.
    # These cases show C1 is jointly SATISFIABLE across the domain INCLUDING its
    # boundary, at inputs that satisfy both preconditions — a post-image no impl
    # can meet at some domain point reads exactly like one every impl meets.
    #
    # AUDIT CORRECTION. This case previously shipped `module=_BASE`: the frozen
    # file byte-for-byte. It verified because the frozen bundle verifies, which
    # G-VERIFY already establishes independently, so the case asserted nothing the
    # artifact did not already claim — an honest pass with no content, and the
    # `_BASE` module made it the one case whose outcome was guaranteed a priori.
    # Re-aimed at an impl that DISPATCHES on the domain boundary (the empty
    # coefficient sequence, where the total is the additive identity), so the case
    # now asserts C1 is dischargeable BRANCH-WISE across that boundary rather than
    # only at gold's shape.
    # =====================================================================
    {
        "id": "admiss-boundary-empty",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    if coeffs.length = 0 then\n"
            "      return 0\n"
            "    else\n"
            "      return (listSum coeffs)",
            # The empty branch returns the literal `0` rather than `listSum
            # coeffs`, so C1 does not close by `withinRoundoff_exact` alone: the
            # branch hypothesis must first be turned into `coeffs = []`. The
            # tactic body is elided from the spec view, so retuning it here
            # changes no spec text.
            "prove_correct windowSum by\n"
            "  loom_solve\n"
            "  have hnil : coeffs = [] := by simp_all\n"
            "  subst hnil\n"
            "  exact withinRoundoff_exact ulp\n"
            "    (realArith_ulp_nonneg ulp maxMag require_2) []"),
        "rationale": (
            "the empty sequence satisfies both `require`s (`magSum [] = 0 <= "
            "maxMag` for any nonnegative range), so C1 must be dischargeable "
            "there as at every other admissible sequence. This impl "
            "splits on the domain boundary (`coeffs.length = 0`) and must satisfy "
            "C1 in BOTH branches: on the empty sequence the total is the additive "
            "identity `0`, elsewhere the fold. It verifies (exit 0), so the "
            "post-image is satisfiable across the boundary and no domain point is "
            "excluded — in particular the empty-sequence point that "
            "reject-empty-nonzero attacks is admissible, not vacuous. Re-aimed "
            "from the nagini admiss-amp, whose read-only-permission half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE at the boundary."
        ),
    },

    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        # SECOND AUDIT ADDITION. admiss-boundary-empty establishes C1 is
        # dischargeable branch-wise across the DEGENERATE boundary, but the
        # prescribed total-carrier admissibility shape is the obligation being
        # SATISFIABLE at exactly an F2P-shaped input — the mixed-sign coefficient
        # pattern with negative lobes, which is the domain the failing test drives
        # and the only domain where the load-bearing distinction is observable.
        # This case keeps the frozen impl AND the frozen tactic body verbatim and
        # prepends a `have` that discharges C1's post-image at that concrete point
        # BY EVALUATION (`listSum [1,-3,5,-3,1] = 1`), before closing the frozen
        # obligation unchanged. So it asserts the F2P-shaped point is admissible —
        # not excluded by either `require`, not unsatisfiable — which is exactly
        # what PRECOND-TOO-STRONG would mean here now that the method HAS
        # preconditions: this negative-lobe pattern has `magSum = 13`, finite and
        # well inside any real arithmetic's range, so `Accumulable` admits it.
        #
        # The `have` is LOAD-BEARING, demonstrated rather than asserted: replacing
        # the value `1` with the MAGNITUDE total `13` (1+3+5+3+1, what the
        # pre-change reading would report at this very input) makes the case FAIL,
        # exit 1 with `unsolved goals ⊢ False` — so the step really evaluates the
        # signed total at the F2P point and is not a tautology. Verified out-of-band
        # at exit 0; the `have` must precede `loom_solve` (placing it after works
        # too, but `norm_num` is unavailable on this carrier — `simp [Rat.add_def,
        # Rat.normalize]` is what closes the concrete `Rat` arithmetic).
        "module": _impl_reproved(
            _IMPL,
            "prove_correct windowSum by\n"
            "  have hF2P : listSum [(1 : Rat), -3, 5, -3, 1] = 1 := by\n"
            "      simp only [listSum_cons, listSum_nil]\n"
            "      simp [Rat.add_def, Rat.normalize]\n"
            "  loom_solve\n"
            "  rw [listSum_drop_step coeffs i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": (
            "PRECOND-TOO-STRONG on this carrier means either `require` excluding an "
            "F2P-shaped input, or C1's post-image being UNSATISFIABLE there — both "
            "read exactly like a spec every impl meets. The mixed-sign pattern below "
            "has `magSum = 13`, finite and inside any real arithmetic's range, so "
            "`Accumulable` admits it. This case discharges C1's "
            "post-image at the mixed-sign coefficient pattern `[1,-3,5,-3,1]` (a "
            "negative-lobe sequence of the shape the failing test drives) BY "
            "EVALUATION as a `have`, then closes the frozen obligation verbatim. It "
            "verifies (exit 0), so the signed total is jointly satisfiable with C1 "
            "at exactly the point where the load-bearing distinction bites. The step "
            "is load-bearing, not decorative: asserting the MAGNITUDE total `13` "
            "there instead fails with `unsolved goals ⊢ False` (exit 1). Re-aimed "
            "from the nagini admiss-amp, whose read-only-permission half has no "
            "counterpart here. Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE at the "
            "F2P point."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Both attack C1 (`out = listSum
    # coeffs`); the input binder `coeffs` is varied across a single negative
    # coefficient and a two-element sequence.
    # =====================================================================
    {
        "id": "reject-magnitude-fold",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change bug: fold each coefficient in by its MAGNITUDE (|x|), so
        # a negative coefficient ADDS instead of subtracting. Correct on every
        # all-nonnegative sequence, WRONG on any sequence with a negative
        # coefficient. Loop-free (`coeffs.map`) so its `…Exec` reduces under the
        # unfold set. Refuted at the single negative coefficient `[-1]`.
        "module": _impl(
            "    return (listSum (coeffs.map (fun x => if x < 0 then -x else x)))"),
        "refinement": (
            "this IS the pre-change reading: each coefficient is folded in by its "
            "magnitude, so the normalization total is the magnitude sum rather "
            "than the signed sum. Its faithful real patch keeps the elementwise "
            "magnitude before the reduction; the failing test drives a coefficient "
            "pattern with negative lobes, where the magnitude total and the signed "
            "total differ, and asserts the identity that holds only for the signed "
            "total — so it FAILS and the instance is NOT resolved. This is the "
            "exact defect the fix corrects (mapping.md §2, refinement.md A)."
        ),
        "rationale": (
            "REJECT from C1 (`WithinRoundoff ulp coeffs out`): `listSum` sums the SIGNED "
            "coefficients, so a rival folding in the magnitude diverges from the "
            "post-image at every negative coefficient (`|x| ≠ x` when `x < 0`). "
            "Refuted at `[-1]` (the smallest negative-coefficient input): the "
            "rival returns `1`, C1 forces `-1`. Correct on all-nonnegative "
            "sequences (a genuine partial-domain break). If it verified ⇒ "
            "SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness(
            "[(-1 : Rat)]", "1", "List.map_cons, List.map_nil, ",
            "1 / 4503599627370496", "-1"),
        # Refuted against the loop-free VERIFYING reference, not gold: gold's
        # `…Exec` is an un-reducing loop term, so `decide` there is STUCK for every
        # claim and attributes nothing. Measured — rival exit 0; `_REF` exit 1 with
        # `decide proved that the proposition -1 ≠ -1 is false` (a semantic
        # refutation of this exact claim).
        "witness_reference": _REF,
    },
    {
        "id": "reject-skip-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: sum every coefficient EXCEPT the first (drop the head).
        # Correct on any sequence whose first coefficient is 0 (and vacuously on
        # the empty sequence), WRONG whenever the leading coefficient is nonzero.
        # Loop-free (`coeffs.drop 1`). Refuted at `[3, 5]` (leading coefficient
        # nonzero) — a DISTINCT input point and a distinct list shape from
        # reject-magnitude-fold, so the `coeffs` binder is varied.
        "module": _impl(
            "    return (listSum (coeffs.drop 1))"),
        "refinement": (
            "drops the leading coefficient from the total; its faithful real "
            "patch would compute the reduction over the tail of the coefficient "
            "sequence instead of the whole. On the failing test's coefficient "
            "pattern the leading coefficient is a nonzero lobe value, so the "
            "normalization total is short by that coefficient, the asserted "
            "identity breaks, and it is NOT resolved. A genuine partial-domain "
            "break — correct only when the first coefficient is 0."
        ),
        "rationale": (
            "REJECT from C1 (`WithinRoundoff ulp coeffs out`): C1 pins the total over the "
            "WHOLE sequence including index 0, so a rival summing only the tail is "
            "short by the leading coefficient whenever it is nonzero. Refuted at "
            "`[3, 5]`: the rival returns `listSum [5] = 5`, C1 forces `listSum "
            "[3,5] = 8`. A DISTINCT point (and list shape) from "
            "reject-magnitude-fold, so the `coeffs` binder is varied. Ports the "
            "nagini weak-skip-first-amp. If it verified ⇒ SPEC-TOO-WEAK "
            "(domain-incomplete)."
        ),
        "witness": _witness(
            "[(3 : Rat), 5]", "5", "List.drop, List.drop_succ_cons, ",
            "16 / 4503599627370496", "8"),
        # As above: measured rival exit 0; `_REF` exit 1 with `decide proved that
        # the proposition 8 ≠ 8 is false`.
        "witness_reference": _REF,
    },
    {
        "id": "reject-empty-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. Both ported rivals are wrong on a NONEMPTY sequence and
        # both agree with C1 on the empty one, so the battery left the domain
        # BOUNDARY entirely unattacked: nothing established that C1 pins the total
        # of the empty sequence rather than leaving it free. This rival is correct
        # at EVERY nonempty input and wrong ONLY at the empty sequence — the
        # tightest near-miss the clause admits, and the one a rival that merely
        # "looks wrong" would never reach. Loop-free, so its `…Exec` reduces.
        "module": _impl(
            "    return (if coeffs.length = 0 then 1 else listSum coeffs)"),
        "refinement": (
            "reports a nonzero total for an EMPTY coefficient sequence; its "
            "faithful real counterpart special-cases the degenerate sequence to a "
            "nonzero normalization factor instead of the additive identity the "
            "reduction returns. The reduction of an empty sequence is `0`, so any "
            "caller reducing over a degenerate coefficient sequence would scale by "
            "the wrong factor; the identity the failing test asserts is stated over "
            "the reduction's own value at every length, so it does NOT hold and the "
            "instance is not resolved. Correct on every nonempty sequence, which is "
            "precisely why it is the hardest near-miss to catch."
        ),
        "rationale": (
            "REJECT from C1 (`WithinRoundoff ulp coeffs out`): C1 is a TOTAL function of "
            "`coeffs` and so pins the boundary point too — `listSum [] = 0` by the "
            "`listSum_nil` equation, so a rival returning `1` there contradicts C1 "
            "at exactly one input. Refuted at `[]`, a THIRD distinct input point "
            "and a third list shape (length 0, vs length 1 in "
            "reject-magnitude-fold and length 2 in reject-skip-head), so the "
            "`coeffs` binder is varied across the empty/singleton/multi boundary. "
            "If it verified ⇒ SPEC-TOO-WEAK (C1 would not constrain the degenerate "
            "sequence)."
        ),
        "witness": _witness("([] : List Rat)", "1", "", "0", "0"),
        # Measured — rival exit 0; `_REF` exit 1 with `decide proved that the
        # proposition 0 ≠ 0 is false`.
        "witness_reference": _REF,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case              -> here
#   -----------------------------------------------------------------------
#   pos-control-amp          -> pos-control-commuted          PORTED (recipe)
#                            -> pos-control-loop-rename       PORTED (weaker)
#   pos-control-pwr          -> (none)                        CARRIER NARROWING
#   admiss-amp               -> admiss-boundary-empty         RE-AIMED
#                            -> admiss-f2p-point              RE-AIMED (F2P point)
#   frame-mutation-amp       -> (none)                        VACUOUS
#   weak-magnitude-amp       -> reject-magnitude-fold         PORTED (central)
#   weak-skip-first-amp      -> reject-skip-head              PORTED
#   frame-mutation-pwr       -> (none)                        VACUOUS + NARROWING
#   weak-linear-pwr          -> (none)                        CARRIER NARROWING
#   vacuous-nonterm-amp      -> (none)                        VACUOUS (total sem.)
#   (no sibling)             -> pos-control-direct            RE-EXPRESSED
#   (no sibling)             -> pos-control-reverse           AUDIT ADDITION
#   (no sibling)             -> reject-empty-nonzero          AUDIT ADDITION
#   AXIOM_TESTS (empty)      -> (none)                        n/a (already empty)
#
# 9 velvet SPEC cases: 4 soundness, 2 admissibility, 3 uniqueness. This is a
# CORRECTLY-NARROWED port, NOT case-count parity (which would push fabricating
# power-branch rivals for a `power` method this bundle does not model).
#
# CARRIER NARROWING (the power / squared surface): the nagini sibling contracts
#   TWO functions — an amplitude signed-sum (amplitude_loss_divisor) AND a power
#   squared-sum (power_loss_divisor) — and carries power positives
#   (pos-control-pwr), a power frame-mutation (frame-mutation-pwr) and a
#   power-vs-linear rival (weak-linear-pwr). This bundle models ONLY the signed
#   linear total as `windowSum`/`listSum`: mapping.md §2 records that the squared
#   sites the patch also touches are mathematically identical to their pre-patch
#   forms (`(|w|)² = w²`) and the SINGLE discriminating primitive is the signed
#   linear sum `Σwᵢ` vs `Σ|wᵢ|`. There is no `power` method here, so every
#   power-branch case has no counterpart. Attacking it would require fabricating a
#   modeled behavior this bundle does not carry — carrier narrowing, not a hidden
#   gap.
# PORTED (pos-control-commuted): the nagini pos-control-amp's ACTUAL reshape
#   recipe was "a fresh local, the operands of `+` commuted". The first port kept
#   only the fresh local (see pos-control-loop-rename) and dropped the commutation,
#   which is the half that carries the content: a pure rename leaves the frozen
#   tactic body closing verbatim, so it cannot distinguish "the spec accepts this"
#   from "the script happens to still work". The commuted accumulation does NOT
#   close under the frozen body (measured, exit 1: `loom_solve` leaves `listSum
#   (drop i) + coeffs[i-1]! = coeffs[i-1]! + listSum (drop i)`), and verifies once
#   retuned with `Rat.add_comm` (exit 0). Restored here as the primary positive.
# PORTED-BUT-WEAK (pos-control-loop-rename): kept, with its limit stated. Same
#   backward `while`, invariant and `decreasing i` measure, accumuland renamed
#   `x`→`w`. Verifies EXIT 0 under the frozen proof unchanged — which is precisely
#   why it is a WEAK control: alpha-renaming a `let`-bound local cannot change
#   either the value or the residual goal, so nothing about the SPEC is exercised.
#   It is retained as a cheap regression on the surgery mechanics, not counted as
#   the SPEC-TOO-STRONG probe (pos-control-commuted and pos-control-reverse are).
# AUDIT ADDITION (pos-control-reverse): the strongest faithful reshape available —
#   total the coefficients in REVERSE order. Correct at every input (`Rat` addition
#   is commutative and associative) but shares almost nothing with the frozen
#   proof, needing an append lemma plus induction. Verifies EXIT 0, so C1 pins the
#   VALUE of the total and not gold's traversal order. NOTE for the next port: the
#   generic `add_comm`/`add_assoc` fail here with `failed to synthesize
#   AddCommMagma Rat`; `Rat.add_comm`/`Rat.add_assoc` are what close it. That is a
#   tooling quirk, not a spec hole.
# RE-EXPRESSED (pos-control-direct): a second correct control with no direct
#   nagini sibling in the amplitude lane, expressing the honest-echo argument on
#   this carrier — C1 pins `out` to `listSum coeffs` within the bound, so the
#   cheapest honest impl is
#   `return listSum coeffs`. The grounded pin is satisfiable only by the real
#   signed total (any wrong fold fails C1), so it doubles as proof the spec is not
#   echo-vulnerable. The loop is gone, so its proof retunes to `loom_solve` (the
#   tactic body is elided from the spec view). Verifies EXIT 0.
# RE-AIMED (admiss-amp -> admiss-boundary-empty): the nagini case established the
#   read-only fractional-permission precondition on an F2P-shaped window. This
#   method has NO `require` and no heap permission, so that probe is vacuous;
#   re-aimed at the total-domain satisfiability risk (a degenerate/unsatisfiable
#   post-image reads like one every impl meets). AUDIT CORRECTION: the first port
#   witnessed this with `module=_BASE`, the frozen file byte-for-byte, whose
#   verification G-VERIFY already establishes — an a-priori pass asserting nothing.
#   Now witnessed by an impl that DISPATCHES on the domain boundary
#   (`coeffs.length = 0`) and must discharge C1 in BOTH branches. Verifies EXIT 0.
# SECOND AUDIT ADDITION (admiss-f2p-point): the boundary probe above covers the
#   DEGENERATE point, but the prescribed shape for this lane on a total carrier is
#   the obligation being satisfiable at an F2P-SHAPED input. Landed as a second
#   admissibility case: frozen impl and frozen tactic body verbatim, with a
#   prepended `have` discharging C1's post-image by EVALUATION at the mixed-sign
#   pattern `[1,-3,5,-3,1]` (`listSum ... = 1`). Verifies EXIT 0, and the step is
#   load-bearing by construction-check: substituting the MAGNITUDE total `13` fails
#   (exit 1, `unsolved goals ⊢ False`), so the `have` really evaluates the signed
#   total at the negative-lobe point rather than restating something free. NOTE:
#   `norm_num` is NOT available on this carrier (`unknown tactic`); `simp
#   [Rat.add_def, Rat.normalize]` closes the concrete Rat arithmetic.
# PORTED (rivals): weak-magnitude-amp -> reject-magnitude-fold (THE prepatch bug,
#   the G-DIFF discriminator: fold in the magnitude, refuted at the smallest
#   negative-coefficient input `[-1]`) and weak-skip-first-amp -> reject-skip-head
#   (drop the leading coefficient, refuted at the two-element `[3,5]` whose head
#   is nonzero). Each carries its nagini refinement argument (magnitude-total vs
#   signed-total on negative lobes; tail-sum short by the leading lobe) and is
#   backed by a machine-checked witness that refutes C1 directly on the
#   transparent `listSum`. Each was SEEN to discriminate with real builds:
#   ELABORATES against the rival (exit 0) and is REFUTED against the loop-free
#   verifying `_REF` (exit 1, `decide proved … -1 ≠ -1` / `… 8 ≠ 8` is false).
#   NOT against gold — see WITNESS MECHANICS below.
# AUDIT ADDITION (reject-empty-nonzero): both ported rivals AGREE with C1 on the
#   empty sequence, so the port left the domain boundary unattacked — nothing
#   established that C1 constrains the total of a degenerate sequence at all. This
#   rival is correct at every NONEMPTY input and wrong only at `[]` (returns `1`
#   where `listSum [] = 0`), the tightest near-miss C1 admits. Rejected; witness
#   elaborates on the rival (exit 0) and is refuted against `_REF` (exit 1,
#   `decide proved that the proposition 0 ≠ 0 is false`).
# VACUOUS (frame-mutation-amp, frame-mutation-pwr): the nagini rivals write
#   through a read-only (Acc(.,1/2)) reference to `window` and are rejected for
#   INSUFFICIENT PERMISSION. Velvet is referentially transparent, `coeffs` is an
#   immutable value, no `mut` binder, no heap, no aliasing, no permission system.
#   There is no read-only input to overwrite. No substitute fabricated.
#   DEMONSTRATED at audit rather than asserted: the closest expressible analogue —
#   binding a local `let mut c : List Rat := coeffs` and clobbering it (`c := []`)
#   before the fold — VERIFIES (exit 0). The write is unobservable because the
#   local is a copy of an immutable value, so there is no permission for a rival to
#   violate and no reject case to write. A rival built on it would be a positive
#   mislabelled `reject`.
# VACUOUS (vacuous-nonterm-amp): the nagini rival spins forever and satisfies
#   every value clause vacuously — the exact spec hole the MustTerminate
#   obligation closed on nagini. This bundle runs under `total` semantics (NOT
#   `partial`), so a non-terminating impl is REJECTED rather than admitted: the
#   frozen `while` owes a `decreasing i` obligation and any rival loop owes its own
#   descent. ("Cannot even be written" is withdrawn: a rival rewrites the whole
#   impl region, so the class is expressible and it is the verifier that closes it.
#   Measured with the proof reduced to `loom_solve`: a spliced `decreasing z` loop
#   whose body is `z := z + 1` is refused on `case «decreasing_1: z»`, residual
#   `z + 1 < z`; with the measure omitted entirely the refusal moves to the
#   `method` declaration, "Decreasing annotations are required in total
#   correctness semantics".) CORRECTED: an
#   earlier version of this entry contrasted the cell with a `partial` cohort that
#   admits a vacuous-verification hole, citing an internal findings doc; that
#   cohort is withdrawn, since all 500 velvet bundles set "total" and the
#   `set_option` elaborator itself runs `openScope `TotalCorrectness`. No reject
#   case written, none
#   claimed dropped. DEMONSTRATED at audit: a spinning loop (`i := i + 1`, no
#   decreasing measure) is refused BY THE SEMANTICS before any value clause is
#   reached — `error: Decreasing annotations are required in total correctness
#   semantics` — and supplying `decreasing i` anyway leaves the unprovable
#   `i + 1 < i`. So divergence is not admitted by this spec and cannot be staged
#   as a spec-strength case: the rejection is the language's, not C1's.
# AXIOM_TESTS: the nagini file's AXIOM_TESTS list is already empty (the reductions
#   are deep folds validated == numpy by G-AX / axiom_check.py, not consumed
#   axioms), and this gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole obligation (`prove_correct
#   windowSum`) is DEFENDED (pos-control-direct + pos-control-commuted +
#   pos-control-reverse + pos-control-loop-rename + admiss-boundary-empty +
#   admiss-f2p-point) and
#   ATTACKED (reject-magnitude-fold + reject-skip-head + reject-empty-nonzero).
#   The sole clause C1 (`WithinRoundoff ulp coeffs out`) is attacked on three independent
#   failure modes: the SIGN of a coefficient (magnitude fold), a DROPPED
#   coefficient (skip head), and the DEGENERATE sequence (empty-nonzero). The sole
#   input binder `coeffs` is varied across three DISTINCT witness points and all
#   three list shapes — `[]` (length 0), `[-1]` (length 1), `[3,5]` (length 2) — so
#   pts=3, the variation is MEANINGFUL (each point flips C1's verdict for its own
#   rival and for no other), and no binder is held fixed by every witness.
#   admiss-f2p-point adds a FOURTH concrete point on the defended side,
#   `[1,-3,5,-3,1]` (length 5, mixed-sign with negative lobes), which is the only
#   one of the four that is F2P-shaped: it is where the signed and magnitude totals
#   diverge (1 vs 13), so it pins the load-bearing distinction at a realistic
#   coefficient pattern rather than at a minimal one.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (the Rat postcondition's
#   Decidable instance does not reduce under `decide`, the spec_guide Rat trap).
#   Every witness instead extracts the executable program and refutes C1 directly
#   against the TRANSPARENT `listSum`: each rival is loop-free so its `…Exec`
#   reduces under the shared unfold set to a concrete Rat (in)equality. `decide`
#   does not compute Rat arithmetic, so surviving sums are normalised via `simp
#   only [Rat.add_zero]` (single-coefficient) and `rw [show a + b = n by simp
#   [Rat.add_def, Rat.normalize]]` (multi-coefficient) before `decide`. No witness
#   binds a hypothesis, so no consistency probe is needed.
#
#   THE SECOND SUBJECT IS `_REF`, NOT GOLD (audit correction; the single
#   substantive defect found). The frozen impl is a `while` loop, so its `…Exec`
#   elaborates to `forIn`/`NonDetT` gadget terms the kernel does not evaluate.
#   Building any of these witnesses against the frozen solution fails with
#   `Tactic decide failed … instDecidableNot did not reduce to isTrue or isFalse`
#   — a STUCK REDUCTION, which is evidence of nothing: the identical error appears
#   for a claim that is TRUE of gold, so the exit code discriminates nothing. The
#   first port's claim that the witness "FAILS against gold — the discrimination
#   the gate requires" was therefore false as a matter of mechanism, even though
#   the recorded outcome was correct: the gate's own `_STUCK_REDUCTION` screen
#   caught it and silently fell back to a battery positive (visible in the
#   pre-audit record as `witness_subject: "a verifying positive from this battery
#   (gold cannot decide)"`). Each reject case now names `_REF` explicitly, so what
#   the artifact SAYS matches what the gate DOES. Measured per case with
#   scripts/lean_verify.sh: rival EXIT 0; `_REF` EXIT 1 by a semantic verdict
#   (`decide proved that the proposition -1 ≠ -1 / 8 ≠ 8 / 0 ≠ 0 is false`);
#   gold EXIT 1 by stuck reduction, which is why it is not the subject.
AXIOM_TESTS = []
