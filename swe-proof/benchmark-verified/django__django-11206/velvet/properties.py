"""properties.py — G-PBT falsification battery for django__django-11206 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed, which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct formatDecimal`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies). ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

Every case below keeps the frozen ``prove_correct formatDecimal by loom_solve
<;> simp_all [clampSmall, plainZero, renderDecimal]`` script BYTE-IDENTICAL — no
positive is admitted by reproving, so no positive can pass by having had its
obligation reshaped, and no reject is admitted on a tactic-shape mismatch alone
(each ships a witness). THREE cases EXTEND the script (the frozen steps are kept
verbatim as a PREFIX and followed by extra ones), and each has to for a reason
that is not a reshaping of the frozen obligation:

  * ``admiss-f2p-shaped`` and ``admiss-precond-satisfiable`` each add an
    in-region ``assert``, which is a NEW obligation the frozen script never had
    to close;
  * ``pos-domain-restricted`` is the one positive whose body READS the
    ``require`` clause — it is deliberately unconstrained OUTSIDE the clause's
    domain — so closing its obligation needs the clause unfolded, which the
    frozen script never had to do (the frozen body ignores the clause entirely).

In all three the ``ensures`` obligation is untouched in statement and still
discharged, and every case whose job is to catch SPEC-TOO-STRONG on the SHAPE of
an implementation — the five soundness positives — plus every rival keeps the
script byte-identical.

AUDIT NOTE — the admissibility lane is carried TWICE here and neither half is
vacuous. ``admiss-precond-satisfiable`` is PRECOND-TOO-STRONG in its literal
form: the ``require`` clause has to ADMIT the requested position counts this
instance grades, and it is discharged in-region at the method's OWN binder and
at ``none``, ``some 0``, ``some 3`` and the largest admitted count, together
with a NEGATIVE conjunct one count further out — so the clause is available,
satisfiable, AND not trivially true. Five negative controls, one per conjunct,
were measured and all five fail.
``admiss-f2p-shaped`` covers the half no precondition can: the ``ensures``
itself being UNSATISFIABLE, or degenerate, at exactly an F2P-shaped input, which
a positive that discharges it at that concrete input by evaluation tests
directly. Its four negative controls were measured.

DEFENDED SURFACE (one contracted method, one ``require``, one ``ensures``):

  formatDecimal (number : DecVal) (decimalPos : Option Nat) return (out : List Char)
      require positionsInExponentRange decimalPos
      ensures out = renderDecimal (clampSmall number decimalPos) decimalPos

over the carrier

  opaque zeroRender : Option Nat → List Char
  structure DecVal where amount : Rat; render : Option Nat → List Char

with the transparent ``pure`` layer

  renderDecimal d dp  = d.render dp
  plainZero           = { amount := 0, render := zeroRender }
  ratAbs n            = max n (-n)
  workingDigits       = 28
  resolution p        = 1 / 10 ^ (max p 1)
  guardCutoff p       = resolution p - resolution p / (2 * 10 ^ workingDigits)
  belowResolution d dp = match dp with
                         | none   => false
                         | some p => decide (ratAbs d.amount < guardCutoff p)
  clampSmall d dp     = if belowResolution d dp then plainZero else d

and the transparent ``pre-conditions`` layer the ``require`` clause is stated in

  leastExponentMagnitude = 1000026
  positionsInExponentRange dp = match dp with
                                | none   => True
                                | some p => max p 1 + workingDigits
                                              ≤ leastExponentMagnitude

CARRIER — the input is carried as TWO facets, and BOTH are load-bearing for this
battery rather than incidental.

  * ``amount`` — the exact amount the input denotes, as a rational. The one
    decision the operation makes compares magnitudes, and a magnitude is a
    property of the amount alone, so ``belowResolution`` reads this facet and
    nothing else.
  * ``render`` — the display string THIS VERY VALUE produces at a requested
    number of visible fractional positions. The operation hands its input on to
    a display step it does not itself change, and two inputs that denote one
    amount can still display differently, so that behaviour travels WITH the
    value instead of being reconstructible from a description of it.

Carrying the display behaviour as a facet of the value is what makes the
pass-through case of ``clampSmall`` a claim about the input ITSELF: a value
assembled from a DESCRIPTION of the input satisfies the clause only when it
displays exactly as the input does. Two rivals pin this and neither is
expressible on a carrier that holds only a description of the input:

  * ``reject-value-rebuilt-not-input`` rebuilds the value from the input's
    amount and hands the display step a value that displays the way the plain
    zero does. On a description-only carrier this rival's argument and the
    spec's are the SAME point, so the spec admits it — and its faithful real
    counterpart does not resolve the instance (see its ``refinement``).
  * ``reject-zero-loses-plain-form`` zeroes the amount but retains the input's
    own display behaviour, so the display step receives a value that denotes
    zero without displaying as the plain zero does.

``pos-facet-round-trip`` is the positive that keeps the pair honest: an
implementation that reassembles the value from the input's OWN two facets is
the input, and must still verify. axiom_check.py measures the necessity of the
``render`` facet directly (pairs of real inputs with equal amount — three of
them with equal ``as_tuple()`` as well — whose displayed strings differ).

``zeroRender`` is an ``opaque`` free constant with NO constraining ``axiom``: it
stands for the display step applied to the one plain zero value, and the
operation never inspects the characters of a display string (mapping.md §3 — the
weakest sufficient contract asserts nothing about the character list).

THRESHOLD — why ``guardCutoff`` and not ``resolution``. The magnitude the real
comparison sees is first materialized at the ambient working precision
(``workingDigits`` = 28 significant digits, ties to even) and only then
compared, so a magnitude strictly under ``resolution p`` can still materialize
AT it and compare not-under. Comparing the EXACT magnitude against
``resolution p`` is therefore a different predicate from the real one, on the
whole half-ulp window ``[guardCutoff p, resolution p)``.
``reject-threshold-exact-compare`` is the rival that pins this, and its witness
point sits inside that window; mapping.md §2 carries the derivation and
axiom_check.py checks the equivalence executably over the whole window.

TWO input binders: ``number`` (a ``DecVal``) and ``decimalPos`` (``Option Nat``,
whose ``none`` arm means "no position count was requested"). The domain is TOTAL
in the FIRST binder — no input magnitude is excluded, and none needs to be
(refinement.md §A0(iii)) — and restricted in the second one only: ``require
positionsInExponentRange decimalPos`` admits every count up to
``leastExponentMagnitude - workingDigits`` = 999998, which is exactly where the
threshold ``guardCutoff`` names stops being the threshold a real comparison
applies. So the partial-DOMAIN lane is live here and is carried from both sides:
``admiss-precond-satisfiable`` (the clause ADMITS every count this instance
grades, and is not trivially true) and ``pos-domain-restricted`` (the clause
really is a DOMAIN restriction — an implementation correct inside it and
arbitrary outside still verifies, so the obligation claims nothing out of range,
which is what makes the restriction sound rather than a hidden extra premise).

CARRIER NOTE — where the obligation is transparent and where it is opaque. The
post-image is ``renderDecimal (clampSmall number decimalPos) decimalPos`` =
``(clampSmall number decimalPos).render decimalPos``: a display facet applied to
a FULLY TRANSPARENT argument. So:

  * the ARGUMENT (``clampSmall number decimalPos``) is decidable at literal
    inputs — ``belowResolution`` bottoms out in a ``Rat`` comparison between the
    literal ``amount`` facet and ``guardCutoff p``, and that reduces under
    ``simp [belowResolution, guardCutoff, resolution, ratAbs, workingDigits,
    Rat.div_def, Rat.inv_def, Rat.normalize, Rat.mul_def, Rat.sub_def,
    max_def]`` followed by ``decide`` (bare ``decide`` alone gets stuck: it
    unfolds the ``Decidable`` instance for ``Rat`` order rather than the values,
    so it never reaches ``isTrue`` / ``isFalse``). ``Rat.sub_def`` is in that
    set because ``guardCutoff`` is a DIFFERENCE: without it the right-hand side
    is left as an unreduced ``{…} - {…}`` between two structure literals and
    every witness here lands ``witness-undecided`` (measured);
  * the RESULT is not. Nothing is claimed about any value's display facet, so no
    literal ``List Char`` is derivable and a rival cannot be refuted by
    computing an expected output. It can still be refuted STRUCTURALLY — see
    ROUTE 2 below; "no literal output is derivable" is not the same as "the
    result side is undefended".

Every witness head binds a fresh display function ``rho : Option Nat → List
Char`` and states its input as ``{ amount := <literal>, render := rho }``. That
is not decoration: it is what keeps the conditioning hypotheses SATISFIABLE. A
witness that spelled the input's display facet as ``zeroRender`` would, for
every rival whose argument differs from the spec's only in the AMOUNT, state
``zeroRender dp ≠ zeroRender dp`` — inconsistent, and the gate's
``consistency_probe`` would derive ``False`` from it. With ``rho`` free the same
hypothesis reads ``rho dp ≠ zeroRender dp``, which is satisfiable for an
unconstrained function and is the weakest assumption the refutation needs.

The reject lane therefore has TWO routes, and both are used.

ROUTE 1 — attack the ARGUMENT. Each such witness pins the two carried values
(rival's argument vs the spec's argument) DECIDABLY on their ``amount`` facet,
and CONDITIONS on the display step separating those two values via a single
satisfiable hypothesis

    hr : renderDecimal <rival's argument> dp ≠ renderDecimal <spec's argument> dp

which is exactly the "condition on the carrier instead of computing it" route.
One hypothesis per witness, about ONE term, so the binders are jointly
satisfiable; an unconditional claim that two display applications differ would
be the inconsistent shape and is avoided. Note this makes each argument-route
reject case ALSO an implicit injectivity-boundary claim: the rival is refuted at
a point where the display step is assumed to distinguish the two arguments.
For ``reject-value-rebuilt-not-input`` and ``reject-zero-loses-plain-form`` the
hypothesis is not merely satisfiable but FACTUAL: the two values each separates
are two real inputs whose displayed strings the real code genuinely differs on
(a ``Decimal`` subclass that displays itself with a prefix in the first case; a
zero written at the input's own place, which the unchanged tail routes to its
``abs(exponent) + len(digits) > 200`` branch, in the second) — axiom_check.py
measures a pair of each shape.

ROUTE 2 — attack the OUTER EQUALITY, with no conditioning hypothesis at all.
The clause pins ``out`` to the display result up to equality, so a rival that
perturbs the STRUCTURE of that result rather than its argument is refutable
without knowing a single character of it: ``c :: l ≠ l`` and ``l ++ [c] ≠ l``
follow from a length argument for every ``c`` and every unknown ``l``. These
witnesses bind only ``rho`` (no ``hr``), so there is nothing to be inconsistent
and the consistency probe has nothing to work with. This route is what makes the
result side attackable despite the display step being opaque, and it is why the
character-level rivals the sibling ships are NOT inexpressible here (see the
ACCOUNTING footer: two of them are carried, recovered during audit).

WHY ``NonDetT.bind, bind`` ARE IN EVERY SIMP SET (the load-bearing line of the
whole reject lane, so it is spelled out). The frozen body ASSIGNS to a mutable
local. In the extracted program that assignment is a monadic ``bind``, so
``formatDecimalExec`` normalizes to ``NonDetT.run do NonDetT.pure PUnit.unit;
NonDetT.pure (renderDecimal …)`` — a ``bind`` of a unit-valued ``pure`` onto the
result. ``simp [NonDetT.run, pure, …]`` does NOT collapse that: the residual term
is not syntactically ``DivM.res _``, so ``DivM.res.inj`` fails to UNIFY and the
build errors with ``Application type mismatch … in the application
DivM.res.inj h``. That error is a carrier artifact, not a refutation, and an
earlier version of this battery rested six of its eight reject cases on it: the
witness and a FORGERY that flips the claim to ``=`` — i.e. asserts the frozen
impl is CORRECT at that very point — both failed against the frozen solution, so
its exit code carried no information about the claim. Adding ``NonDetT.bind,
bind`` (see ``_EXEC_NORM``) reduces the block, after which the gold-side exit
code tracks the claim.

GOLD-SIDE EVIDENCE. The finding above was made on an earlier carrier, so it is
re-derived on each carrier rather than inherited. Every reject case is rebuilt
with the gate's own file construction and paired with the flipped-claim control:
the same file with the claim's ``≠`` replaced by ``=`` and every closing step
after the ``simp`` DROPPED, so that the file's exit code is exactly "did simp
alone prove the equation for this impl". Measured, every rival: witness 0 on the
rival and 1 on the frozen solution; flipped claim 0 on the frozen solution and 1
on the rival. So the frozen side's failure is simp reporting "gold satisfies the
clause here" rather than a tactic artifact, and a witness asserting gold is right
there would NOT have been recorded as a rejection. What the gold-side failure
looks like: ``simp`` proves the pinned equation for the frozen impl, rewriting
the goal ``formatDecimalExec … ≠ DivM.res …`` to ``False``, so the closing step
then has nothing to work on and the build fails over a residual ``⊢ False`` with
the conditioning hypothesis intact — verbatim, for an argument-route case:
``error: Tactic `introN` failed: There are no additional binders or `let`
bindings in the goal to introduce``, over a context printing ``hr :`` and
``⊢ False``. That is a visibly different failure from the carrier artifact above
(which reports an ``Application type mismatch`` on ``DivM.res.inj``), which is
how the two are told apart on inspection. The two ROUTE 2 witnesses need
``_LEN_TAIL`` for the same reason: their reduced goal is closed by simp itself.

REFINEMENT GROUND-TRUTH (what makes a reject a TRUE
verify-does-not-imply-resolve break rather than a resolve-preserving artifact).
The behaviour being modelled normalizes an input whose magnitude cannot affect
any visible position at the requested number of them — and normalizes it to the
PLAIN zero value — and leaves every other input alone, unchanged, with its own
display behaviour intact. Reconstructing each rival's faithful real patch and
running it against every row of the failing-plus-passing suite (out-of-band) is
what decided each case's disposition; the per-case ``refinement`` field records
the measured outcome.

One rival — ``reject-threshold-no-floor`` — is shipped even though its faithful
patch is measured resolve-PRESERVING (zero suite failures). That is deliberate,
and it corrects an earlier reading of this test. Resolve-preservation says the
SUITE does not catch the rival; it does not say the rival is right. This one is
observably wrong on this carrier at a concrete input the suite never exercises,
and a uniqueness case's claim is "the spec pins this clause", not "the suite
catches this patch". So its ``refinement`` field records the zero-failure
measurement plainly and rests the case on uniqueness alone, rather than the case
being dropped or the measurement being dressed up as a break.

DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE SEMANTICS
against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Measured on
this bundle with real builds: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal — ``case
«decreasing_1: spin» … if_pos : 0 < spin ⊢ False``, i.e. the descent goal for the
named measure, already reduced to ``False`` because ``spin < spin`` has no
proof. Dropping the clause rather than faking it is refused even earlier, by the
elaborator's own check (``Decreasing annotations are required in total
correctness semantics``). So divergence neither applies to this impl nor
discharges the ``ensures`` clauses vacuously if a rival introduces it. No case is
shipped for the class, and the reason is a WITNESS-side limit rather than a
spec-side one: an ``expect="reject"`` case needs a witness that ELABORATES
against the rival, and a diverging rival's module does not compile at all (the
descent obligation fails at the ``method`` itself, upstream of any appended
tester), while a rival that carries a measure which does not decrease is refused
at the ``prove_correct`` site the witness file strips — so that module does
elaborate, but its post-image is then an unreduced ``forIn Lean.Loop.mk`` term
carrying ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
kernel will not normalise to a value a concrete-input tester can decide. Both
shapes land ``witness-unproven`` / ``witness-undecided``, which is a measurement
about the tester, not about the spec.

AXIOM lane: the sibling's three ``AXIOM_TESTS`` are dropped — that lane is
G-AX's job, and there is no ``axiom`` here at all (``zeroRender`` is an
``opaque`` free constant with nothing asserted about it, so there is no axiom to
validate; what G-AX checks instead is the A-reference, the guard's equivalence
to the real comparison, and the necessity of each carrier facet, see
axiom_check.py). This gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11206"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen body, verbatim — the four code lines
# ---- strictly inside formatDecimal's -- impl-start / -- impl-end. It lies
# ---- wholly inside the elided impl region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so every variant's edit leaves the spec
# ---- regions (axioms / pure / pre-conditions / post-conditions, the method
# ---- signature, the `ensures`) and the `prove_correct` block untouched.
_IMPL = ("    let mut num : DecVal := number\n"
         "    if belowResolution number decimalPos then\n"
         "      num := { amount := 0, render := zeroRender }\n"
         "    return renderDecimal num decimalPos")
assert _BASE.count(_IMPL) == 1, "formatDecimal impl region drifted from expected text"

# The plain zero value, spelled as the frozen body spells it (a record literal
# rather than `plainZero`, so the mutation gate has behavioural tokens to flip).
_ZERO = "{ amount := 0, render := zeroRender }"


def _impl(new_impl):
    """Full Solution.lean with ONLY formatDecimal's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- the frozen proof script, verbatim. Every case but one keeps this
# ---- BYTE-IDENTICAL (see the docstring). The single exception is the
# ---- admissibility positive, which adds an in-region `assert` that the frozen
# ---- script cannot discharge on its own — the `assert` is a NEW obligation, not
# ---- a reshaping of the frozen one, so closing it needs extra steps. The
# ---- `ensures` obligation itself is untouched, and `prove_correct
# ---- formatDecimal` is still present (which is what variant_scope checks on
# ---- velvet: the header, since the obligation lives in the spec view and the
# ---- tactic body is elided from it).
_PROOF = ("prove_correct formatDecimal by\n"
          "  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]")
assert _BASE.count(_PROOF) == 1, "formatDecimal proof script drifted"


def _impl_reproved(new_impl, new_proof):
    """Impl-region body replaced AND the tactic body extended."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness scaffolding ----------------------------------------------------
# Every reject witness has the same four-part shape:
#   0. a fresh display function `rho` in the head, and the probe input stated as
#      `{ amount := <literal>, render := rho }`. This is what makes `hr` below
#      satisfiable rather than contradictory — see the docstring's paragraph on
#      it; spelling the display facet as `zeroRender` instead would make every
#      amount-side rival's hypothesis read `zeroRender dp ≠ zeroRender dp`.
#   1. `have hb… : belowResolution <lit> <lit> = true/false` — the decidable
#      part, discharged by the simp-then-decide chain described in the CARRIER
#      NOTE. Nothing here is assumed; it is computed.
#   2. `hr` in the example head — the ONE conditioning hypothesis, that the
#      display step separates the rival's argument from the spec's at this
#      input. Satisfiable (a function may distinguish two distinct points), and
#      the only assumption the refutation needs.
#   3. unfold the extracted program, `simp` it down with the computed facts,
#      then close with `hr`. The `first | … | …` tail covers both goal shapes
#      simp can leave (with or without the `DivM.res` wrapper stripped) — a
#      tactic-robustness measure only; it assumes nothing.
# No `sorry`/`admit`/`native_decide`/`axiom`/`opaque` appears in any witness.
#
# `Rat.sub_def` is in the arithmetic set because `guardCutoff` is a DIFFERENCE
# of two rationals: without it `belowResolution` stops at a comparison against
# an unreduced `{…} - {…}` between structure literals and nothing decides
# (measured: a 16-fact probe with the same set minus `Rat.sub_def` fails with
# `unsolved goals` on every fact; with it, all 16 reduce in 8s).
# `plainZero` joins the reduction set because `clampSmall` returns it by name
# while the impl-region bodies write the record literal, and the two have to
# meet; `renderDecimal` joins it because the post-image applies it to that
# record and the display facet has to be projected out.
_RAT_NORM = ("Rat.div_def, Rat.inv_def, Rat.normalize, Rat.mul_def, "
             "Rat.sub_def, max_def")
# The guard's own unfolding set: everything between `belowResolution` and the
# bare rational comparison.
_GUARD_NORM = "belowResolution, guardCutoff, resolution, ratAbs, workingDigits"
# The monadic-normalization set every witness needs, for the reason above.
_EXEC_NORM = ("NonDetT.run", "NonDetT.bind", "bind", "pure")

# Two option raises that every literal-evaluating step here is wrapped in.
# NOT tuning: without them the cases stated at the FAILING TEST's own magnitude
# cannot be decided at all, and the reason is a guard rather than a budget.
# That input's magnitude is ~1e-300, so the guard evaluates `10 ^ 303`, and
# Lean's default `exponentiation.threshold` of 256 makes `simp` REFUSE to
# evaluate a power that large (it warns "exponentiation operation was not
# evaluated"). The refusal leaves the comparison half-unfolded, after which the
# `Rat` normalization lemmas rewrite in a cycle and `simp` dies on `maximum
# recursion depth`. Raising the threshold past 303 lets the power evaluate; the
# recursion depth is raised with it because the resulting 304-digit
# numerator/denominator normalization nests deeper than the default 512.
# Measured: with both raises the F2P-shaped guard facts reduce in a few seconds,
# and every case stated at a small literal is unaffected. `decide` CANNOT
# substitute for `simp` here at any depth -- `Rat`'s order instance bottoms out
# in `Nat.gcd`, whose well-founded recursion the kernel does not reduce, so
# `decide` reports "did not reduce to isTrue or isFalse" even on the small
# literals (which is why every guard fact is `simp`-then-`try decide`, not
# `decide`).
_SETOPT = ("set_option exponentiation.threshold 400 in\n"
           "set_option maxRecDepth 100000 in\n")

# ROUTE 2's closing tail. Once `_EXEC_NORM` actually reduces the `do` block, the
# two structural rivals' goals come out already contradictory — simp discharges
# `'0' :: l = l` / `l ++ ['.'] = l` by its own length reasoning — so an
# `intro h; …` step would then run on no goal at all and fail with `No goals to be
# solved`. `first | done | (intro h; <length argument>)` keeps BOTH shapes
# closable: whichever way simp leaves it, the refutation is by a length argument
# against an unknown list and nothing is assumed.
_LEN_TAIL = ("  first\n"
             "    | done\n"
             "    | (intro h\n"
             "       have hl := congrArg List.length (DivM.res.inj h)\n"
             "       simp at hl)\n")


def _val(amount, render="rho"):
    """A carried input: an exact amount and a display function."""
    return "{ amount := " + amount + ", render := " + render + " }"


def _below(name, val, dp, truth):
    return (f"  have {name} : belowResolution ({val}) ({dp}) "
            f"= {'true' if truth else 'false'} := by\n"
            + "".join("    " + ln + "\n" for ln in _SETOPT.splitlines())
            + f"    simp [{_GUARD_NORM}, {_RAT_NORM}]\n"
            "    try decide\n")


def _extra(name, claim):
    """A second decidable arithmetic fact (the rival's own threshold test)."""
    return (f"  have {name} : {claim} := by\n"
            + "".join("    " + ln + "\n" for ln in _SETOPT.splitlines())
            + f"    simp [guardCutoff, resolution, ratAbs, workingDigits, "
              f"{_RAT_NORM}]\n"
            "    try decide\n")


def _witness(num, dp, facts, rival_arg, spec_arg, extra_simp=(), extra_haves=()):
    """`formatDecimalExec num dp ≠ DivM.res (post-image num dp)`, conditioned on
    the display step separating the rival's argument from the spec's."""
    haves, names = [], []
    for i, (val, d, truth) in enumerate(facts):
        names.append(f"hb{i}")
        haves.append(_below(f"hb{i}", val, d, truth))
    for j, (nm, claim) in enumerate(extra_haves):
        names.append(nm)
        haves.append(_extra(nm, claim))
    simps = ", ".join(_EXEC_NORM + ("clampSmall", "plainZero", "renderDecimal")
                      + tuple(extra_simp) + tuple(names))
    return ("extract_program_for formatDecimal\n\n"
            "example (rho : Option Nat → List Char)\n"
            f"    (hr : renderDecimal ({rival_arg}) ({dp})\n"
            f"      ≠ renderDecimal ({spec_arg}) ({dp})) :\n"
            f"    formatDecimalExec ({num}) ({dp})\n"
            f"      ≠ DivM.res (renderDecimal (clampSmall ({num}) ({dp})) "
            f"({dp})) := by\n"
            + "".join(haves)
            + "  unfold formatDecimalExec formatDecimal\n"
            + "  (set_option exponentiation.threshold 400 in\n"
            + "   set_option maxRecDepth 100000 in\n"
            + f"   simp [{simps}])\n"
            + "  first\n"
            + "    | exact hr\n"
            + "    | (intro h; exact hr (DivM.res.inj h))\n")


def _witness_len(num, dp, facts, extra_simp=()):
    """ROUTE 2: no conditioning hypothesis, closed by a length argument."""
    haves, names = [], []
    for i, (val, d, truth) in enumerate(facts):
        names.append(f"hb{i}")
        haves.append(_below(f"hb{i}", val, d, truth))
    simps = ", ".join(_EXEC_NORM + ("clampSmall", "plainZero", "renderDecimal")
                      + tuple(extra_simp) + tuple(names))
    return ("extract_program_for formatDecimal\n\n"
            "example (rho : Option Nat → List Char) :\n"
            f"    formatDecimalExec ({num}) ({dp})\n"
            f"      ≠ DivM.res (renderDecimal (clampSmall ({num}) ({dp})) "
            f"({dp})) := by\n"
            + "".join(haves)
            + "  unfold formatDecimalExec formatDecimal\n"
            + f"  simp [{simps}]\n"
            + _LEN_TAIL)


# ---- the amounts the cases probe -------------------------------------------
# Each is the exact amount of a concrete decimal input (mapping.md §2):
_A_F2P = "(1234 : Rat) / 10 ^ 303"        # 0.0…01234, the F2P row's own input
_A_THOU = "(1 : Rat) / 10 ^ 3"            # 0.001
_A_NEG_THOU = "-((1 : Rat) / 10 ^ 3)"     # -0.001
# 0.0001 — below the threshold at a requested count of 3, and above it at a
# count of 2, so a rival that stops normalizing past a self-chosen count is
# separated from the spec here while both agree at every smaller count.
_A_TENTHOU = "(1 : Rat) / 10 ^ 4"         # 0.0001
_A_FIVE = "(5 : Rat)"                     # 5
_A_NEG_HALF = "-((1 : Rat) / 2)"          # -0.5
# The materialization boundary at a requested count of 2: `guardCutoff 2`
# EXACTLY (= 0.00999…95, 29 significant digits). The real comparison
# materializes this magnitude UP to 0.01 and so does NOT normalize it.
_A_TIE = "((10 : Rat) ^ 29 - 5) / 10 ^ 31"
# Strictly inside the half-ulp window `[guardCutoff 2, resolution 2)`: an exact
# magnitude BELOW 0.01 that the real comparison still does not normalize,
# because it materializes to 0.01. This is the point that separates the real
# predicate from an exact comparison against `resolution 2`.
_A_WINDOW = "(4 * (10 : Rat) ^ 28 - 1) / (4 * 10 ^ 30)"

_F2P = _val(_A_F2P)
_THOU = _val(_A_THOU)
_NEG_THOU = _val(_A_NEG_THOU)
_TENTHOU = _val(_A_TENTHOU)
_FIVE = _val(_A_FIVE)
_NEG_HALF = _val(_A_NEG_HALF)
_TIE = _val(_A_TIE)
_WINDOW = _val(_A_WINDOW)

# The two values a rival can hand on that DENOTE the right amount while
# displaying wrongly — the pair the `render` facet exists to separate.
_ZERO_OWN_RENDER = "{ amount := 0, render := rho }"        # zero, input's display
_REBUILT = _val(_A_FIVE, "zeroRender")                     # input's amount only


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on the SHAPE of the impl rather than on its behaviour.
    # Each keeps the frozen `prove_correct` script byte-identical, so each one
    # really is the frozen obligation being re-discharged over a reshaped body
    # (all five confirmed with real builds).
    # =====================================================================
    {
        "id": "pos-collapsed-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the mutable local and the branch entirely, returning the
        # post-image's own argument expression in one step. The frozen body
        # decides-then-assigns; this one delegates the decision to the shared
        # pure layer. Definitionally identical, maximally different in shape.
        # (Sibling: pos-control-grounded-guard.)
        "module": _impl(
            "    return renderDecimal (clampSmall number decimalPos) decimalPos"),
        "rationale": "structurally different CORRECT impl: the mutable local and "
                     "the guard are collapsed into a single delegating return. "
                     "Defends the sole `ensures` obligation against being tied "
                     "to the frozen body's branch-and-assign shape.",
        "refinement": None,
        "witness": None,
    },
    {
        "id": "pos-let-ladder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the decision in a Bool local, name the normalized value
        # in an immutable DecVal local via a conditional expression, then return.
        # Same decision, no mutation, three statements instead of a branch, and
        # the plain zero is written by NAME here where the frozen body writes the
        # record literal — so this positive also checks the spec is indifferent
        # to which spelling of that value an impl uses.
        # (Sibling: pos-control-reorder-decision.)
        "module": _impl(
            "    let flagged : Bool := belowResolution number decimalPos\n"
            "    let num : DecVal := if flagged then plainZero else number\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "structurally different CORRECT impl: the decision is bound "
                     "to a Bool local and the normalized value to an immutable "
                     "DecVal local via a conditional expression, replacing the "
                     "mutable-local-plus-branch form, and naming the plain zero "
                     "value instead of spelling it out. Defends the obligation "
                     "against mutation-shape sensitivity and against being tied "
                     "to one spelling of that value.",
        "refinement": None,
        "witness": None,
    },
    {
        "id": "pos-guard-negated",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: invert the polarity — initialize the local to the normalized
        # value and overwrite it with the input when the guard does NOT fire.
        # Every branch of the frozen body is taken in the opposite order.
        "module": _impl(
            f"    let mut num : DecVal := {_ZERO}\n"
            "    if !belowResolution number decimalPos then\n"
            "      num := number\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "structurally different CORRECT impl: the guard's polarity "
                     "and the initial/overwritten values are swapped, so the "
                     "same two outcomes are produced by the mirror-image "
                     "control flow. Defends the obligation against guard-"
                     "polarity sensitivity.",
        "refinement": None,
        "witness": None,
    },
    {
        "id": "pos-if-else",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: two independent returns under a total if/else, so the
        # display step is applied at two distinct syntactic sites rather than
        # one.
        "module": _impl(
            "    if belowResolution number decimalPos then\n"
            f"      return renderDecimal {_ZERO} decimalPos\n"
            "    else\n"
            "      return renderDecimal number decimalPos"),
        "rationale": "structurally different CORRECT impl: a total if/else with a "
                     "separate return in each arm, applying the display step at "
                     "two syntactic sites and never assigning a local. Defends "
                     "the obligation against single-exit-point sensitivity.",
        "refinement": None,
        "witness": None,
    },
    {
        "id": "pos-facet-round-trip",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: reassemble the pass-through value from the input's OWN two
        # facets instead of naming the input. This positive is the counterweight
        # to reject-value-rebuilt-not-input, and the pair is the whole point of
        # the `render` facet: reassembling a value from the input's own amount
        # AND its own display behaviour IS the input (structure eta), and must
        # verify; reassembling it from the amount alone is not, and must not.
        # Without this positive, a reader could suspect the spec of rejecting
        # every rebuild rather than only the lossy one.
        "module": _impl(
            "    let mut num : DecVal := "
            "{ amount := number.amount, render := number.render }\n"
            "    if belowResolution number decimalPos then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "structurally different CORRECT impl: the pass-through "
                     "value is reassembled from the input's own amount and its "
                     "own display behaviour rather than named. Defends the "
                     "obligation against rejecting reassembly as such — what it "
                     "must reject is reassembly that DROPS a facet, which "
                     "reject-value-rebuilt-not-input pins.",
        "refinement": None,
        "witness": None,
    },

    # =====================================================================
    # DOMAIN POSITIVE (soundness, expect verify) — the `require` clause is a
    # DOMAIN RESTRICTION and not a hidden extra premise. This is the sixth
    # soundness positive and the only one that extends the frozen script; it has
    # to, because it is the only positive whose body reads the clause.
    # =====================================================================
    {
        "id": "pos-domain-restricted",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: correct on every input the `require` clause admits, and
        # deliberately WRONG — it returns the empty display string — on every
        # requested position count past it. Such an implementation must verify,
        # because a `require` clause means the obligation says NOTHING outside
        # its domain. The out-of-range test is spelled as the exact negation of
        # the clause (`leastExponentMagnitude < max p 1 + workingDigits`), so
        # the two branches partition the input space at precisely the clause's
        # boundary and nothing in between is left correct by accident.
        #
        # WHY IT IS SHIPPED. `require positionsInExponentRange decimalPos` was
        # added to this spec because the `guardCutoff` derivation of the THRESHOLD
        # (see THRESHOLD above) only holds while the threshold's own exponent is
        # one the ambient environment can place a digit at; past that count the
        # modeled guard and the real one part company in BOTH directions
        # (measured in axiom_check.py's `check_position_range_boundary`, and
        # written up in refinement.md §A0(iii)). A `require` is the honest way to
        # say so, but it is also the one edit that can quietly buy verification
        # with a premise, so the battery has to pin what it does and does not do:
        #   * this case pins that it is a genuine restriction of the DOMAIN — an
        #     impl may do anything out of range and still verify, i.e. the clause
        #     is CONSUMABLE and the obligation really is silent there;
        #   * `admiss-precond-satisfiable` pins that the domain it leaves is not
        #     too small — it still contains every count this instance grades;
        #   * `reject-invented-domain-bound` pins that an impl may NOT draw a
        #     domain bound of its own INSIDE the admitted range, which is the
        #     way a domain restriction turns into a hole if the bound is loose.
        # The five positives above keep the frozen script byte-identical and all
        # five still verify with the clause in place, so the clause costs no
        # correct implementation its proof.
        "module": _impl_reproved(
            "    let mut num : DecVal := number\n"
            "    let mut res : List Char := []\n"
            "    if belowResolution number decimalPos then\n"
            f"      num := {_ZERO}\n"
            "    res := renderDecimal num decimalPos\n"
            "    if decimalPos.any (fun p => decide "
            "(leastExponentMagnitude < max p 1 + workingDigits)) then\n"
            "      res := []\n"
            "    return res",
            _PROOF + "\n"
            "  all_goals try (\n"
            "    simp_all [positionsInExponentRange, Option.any, workingDigits,\n"
            "              leastExponentMagnitude, max_def]\n"
            "    rcases decimalPos with _ | p <;> simp_all <;> omega)"),
        "rationale": "a correct-inside-the-domain, arbitrary-outside-it impl "
                     "must verify: `require positionsInExponentRange decimalPos` "
                     "restricts the DOMAIN of the obligation, so the clause is "
                     "consumable and nothing is claimed past the admitted "
                     "position counts. Defends the `require` against being read "
                     "as an extra premise that buys verification for impls that "
                     "are wrong in range — the five byte-identical-script "
                     "positives are what show it costs no correct impl its "
                     "proof, and this case is what shows the restriction it "
                     "makes is exactly the stated one.",
        "refinement": None,
        "witness": None,
    },

    # =====================================================================
    # ADMISSIBILITY (expect verify) — the `require` clause ADMITS the inputs
    # this instance grades, and the obligation is SATISFIABLE, and
    # non-degenerately so, at an F2P-shaped input.
    # =====================================================================
    {
        "id": "admiss-precond-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        # PRECOND-TOO-STRONG in its literal form. The frozen body verbatim,
        # preceded by an in-region `assert` whose six conjuncts are, in order:
        #   * `positionsInExponentRange decimalPos` — the clause is AVAILABLE in
        #     region at the method's own binder, i.e. it is a real premise an
        #     implementation can consume (`pos-domain-restricted` is the case
        #     that consumes it);
        #   * it HOLDS at `none` (the count `test_decimal_subclass` passes), at
        #     `some 0` and `some 3` (every graded row's `decimal_pos` is in
        #     {None, 0, 1, 2, 3, 8} — refinement.md §A0(iii)), and at
        #     `some 999998`, the largest count it admits;
        #   * it FAILS at `some 999999`, one count further out.
        #
        # The negative conjunct is what keeps this case from passing on a
        # vacuously-true clause: a `require` that had collapsed to `True` would
        # satisfy the first five conjuncts and fail the sixth, so this one file
        # distinguishes "admits everything graded" from "admits everything".
        # Nothing here is assumed — the conjunction is closed by unfolding the
        # clause and its two constants and deciding the resulting `Nat`
        # inequalities, so no input, and no property of `number`, is involved.
        # That the boundary sits at 999999 rather than anywhere else is a
        # MEASURED fact about the repository (axiom_check.py
        # `check_position_range_boundary`: the modeled and real guards agree on
        # 27 threshold-straddling probes at counts 999996-999998 and disagree at
        # 999999, and again in the other direction at 1000027), not a choice this
        # battery makes.
        #
        # LOAD-BEARING, measured. Five NEGATIVE controls were built, each the
        # same file with exactly ONE conjunct negated. All five fail (exit 1,
        # `unsolved goals` on `case «pdom_1: …»`) while this case verifies
        # (exit 0). As in `admiss-f2p-shaped` the step after the frozen prefix is
        # `try`-guarded, so the only possible failure is the false claim itself.
        #
        # WHY THE FIRST CONJUNCT IS ALSO A MECHANICAL NECESSITY, stated so a
        # reader who rebuilds this file without it is not surprised: the frozen
        # prefix is `loom_solve <;> simp_all […]`, and `<;>` runs `simp_all` on
        # the assert's goal too. With only the literal-count conjuncts that goal
        # mentions nothing in the frozen simp set, `simp_all` reports `simp_all
        # made no progress`, and the file fails on a TACTIC error carrying no
        # information about the claim (measured). The `decimalPos` conjunct is
        # discharged by `require_1` itself, so the frozen prefix always has
        # something to do and the residual goal is exactly the numeric facts.
        "module": _impl_reproved(
            "    assert (with_name_prefix `pdom\n"
            "      (positionsInExponentRange decimalPos ∧\n"
            "       positionsInExponentRange none ∧\n"
            "       positionsInExponentRange (some 0) ∧\n"
            "       positionsInExponentRange (some 3) ∧\n"
            "       positionsInExponentRange (some 999998) ∧\n"
            "       ¬ positionsInExponentRange (some 999999)))\n"
            + _IMPL,
            _PROOF + "\n"
            "  all_goals try (simp [positionsInExponentRange,\n"
            "    leastExponentMagnitude, workingDigits])"),
        "rationale": "the `require` clause is AVAILABLE in region and "
                     "SATISFIABLE at every requested position count this "
                     "instance grades (`none`, `some 0`, `some 3`) and up to the "
                     "largest count it admits (`some 999998`), and is NOT "
                     "trivially true (it fails at `some 999999`) — all "
                     "discharged by evaluation in-region before the frozen "
                     "obligation closes. Without the negative conjunct a clause "
                     "that had collapsed to `True` would pass this lane; without "
                     "the positive ones a clause tightened past the graded rows "
                     "would. Five negative controls, one per conjunct, were "
                     "measured and all five fail.",
        "refinement": None,
        "witness": None,
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen impl body verbatim, preceded by an in-region `assert` that
        # discharges the obligation BY EVALUATION at concrete F2P-shaped inputs
        # before the frozen `ensures` is closed. Both binders are pinned to
        # literals, so nothing here is assumed — the four conjuncts are computed.
        # The small input's amount is the F2P row's own: 1234e-303, i.e.
        # `Decimal('0.' + '0'*299 + '1234')`. Both probe values carry the
        # method's OWN input as their display facet (`number.render`), so the
        # assert is stated over values of the same shape a caller supplies.
        #
        # WHAT THIS CASE ADDS OVER `admiss-precond-satisfiable`. That case is
        # PRECOND-TOO-STRONG proper: it shows the `require` clause admits the
        # counts this instance grades. Admitting the input is not the same as
        # the obligation SAYING anything there, and the second failure mode is
        # the `ensures` being UNSATISFIABLE (or degenerate — satisfiable only by
        # a constant collapse) at exactly an F2P-shaped input, which no
        # statement about the precondition can rule out. A positive that
        # discharges the obligation at that concrete input, by evaluation, tests
        # that directly. Both halves are needed and both are carried.
        #
        # The two conjunct PAIRS are what make it non-degenerate. At the F2P
        # magnitude the guard must FIRE and the display step's argument must be
        # exactly the PLAIN zero value — not merely a value denoting zero, which
        # is the distinction the `render` facet exists to make; at an ordinary
        # input at the SAME requested position count the guard must NOT fire and
        # the argument must be the input unchanged, display facet included. So
        # the obligation is satisfiable at the F2P point AND the pure layer is
        # not the constant-plainZero function there — an `ensures` satisfiable
        # only by collapsing everything would fail the second pair.
        #
        # LOAD-BEARING, measured. Four NEGATIVE controls were built, each the
        # same file with exactly ONE conjunct falsified: guard-false,
        # clamp-false, large-guard-false, large-clamp-false. All four fail
        # (exit 1, `unsolved goals`) while this case verifies (exit 0), so the
        # assert is checked, not decoration. Every step after the frozen prefix
        # is `try`-guarded, so the ONLY possible failure is the false claim
        # itself (an unguarded `all_goals simp [...]` errors with `` `simp` made
        # no progress `` on a goal it cannot move, which is a TACTIC failure and
        # no evidence about the conjunct — an earlier version of this case
        # shipped that shape and two of its four controls failed for that reason
        # rather than for the falsified conjunct). The extra steps establish the
        # two guard facts FIRST and only then rewrite `clampSmall` with them: a
        # single `simp` over the whole conjunction instead leaves the clamp
        # conjuncts stuck on an unreduced 300-digit `Rat` comparison (measured),
        # which would have been a tactic artifact rather than a claim.
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            f"      (belowResolution {_val(_A_F2P, 'number.render')} (some 3) "
            "= true ∧\n"
            f"       clampSmall {_val(_A_F2P, 'number.render')} (some 3) "
            f"= {_ZERO} ∧\n"
            f"       belowResolution {_val(_A_FIVE, 'number.render')} (some 3) "
            "= false ∧\n"
            f"       clampSmall {_val(_A_FIVE, 'number.render')} (some 3) "
            f"= {_val(_A_FIVE, 'number.render')}))\n"
            + _IMPL,
            "prove_correct formatDecimal by\n"
            "  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]\n"
            "  all_goals try (set_option exponentiation.threshold 400 in\n"
            "    set_option maxRecDepth 100000 in\n"
            "    (have hb0 : belowResolution "
            f"{_val(_A_F2P, 'number.render')} (some 3) = true := by\n"
            f"       simp [{_GUARD_NORM}, {_RAT_NORM}]\n"
            "       try decide\n"
            "     have hb1 : belowResolution "
            f"{_val(_A_FIVE, 'number.render')} (some 3) = false := by\n"
            f"       simp [{_GUARD_NORM}, {_RAT_NORM}]\n"
            "       try decide\n"
            "     simp [clampSmall, plainZero, hb0, hb1]))"),
        "rationale": "the sole `ensures` is SATISFIABLE, and non-degenerately, "
                     "at an F2P-shaped input: at the F2P row's own magnitude the "
                     "guard fires and the display step's argument is pinned to "
                     "exactly the PLAIN zero value, while at an ordinary input "
                     "at the SAME requested count the guard does not fire and "
                     "the argument is the input unchanged, display facet "
                     "included. Both pairs are discharged by evaluation "
                     "in-region before the frozen obligation closes, so the "
                     "obligation is neither unsatisfiable at the input the "
                     "change is about nor satisfiable only by collapsing every "
                     "input to a constant. The `require` clause admits that "
                     "input's requested count, which is the complementary half "
                     "and is `admiss-precond-satisfiable`'s job; being admitted "
                     "is not the same as being spoken about, which is why both "
                     "cases are carried.",
        "refinement": None,
        "witness": None,
    },

    # =====================================================================
    # UNIQUENESS RIVALS (expect reject) — WRONG impls the spec MUST refuse.
    # Between them they attack every independent decision the sole `ensures`
    # clause pins: whether to normalize at all (both directions), WHICH value
    # the normalization produces (two ways of getting the amount right and the
    # display wrong), whether the pass-through value is the INPUT or only a
    # rebuild of it, the strictness of the threshold, the threshold's
    # materialization, its exponent, its floor, the `none` arm's meaning, the
    # DOMAIN the `require` clause leaves (reject-invented-domain-bound, the
    # counterweight to pos-domain-restricted), and — via the three
    # output-perturbing rivals — the outer equality that pins `out` to the
    # display result, in all three directions a list can be perturbed:
    # lengthened (reject-render-output-perturbed), lengthened on a single point
    # of the second binder (reject-dp-zero-output-perturbed), and PERMUTED with
    # the length preserved (reject-output-reversed, which the length-argument
    # refutation style of the other two cannot reach).
    # Their witnesses probe ten distinct input points and vary BOTH binders,
    # including `decimalPos = none`, `some 0` and `some 3`.
    # =====================================================================
    {
        "id": "reject-never-normalize",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: keep the input untouched — never normalize. This is the
        # behaviour of the operation before the change.
        # (Sibling: rival-never-collapse.)
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "the sole `ensures` pins the display step's argument to "
                     "`clampSmall number decimalPos`; this rival passes `number` "
                     "through unchanged, so at any input whose magnitude is below "
                     "the threshold for the requested count the argument is "
                     "`number` where the spec demands the plain zero value. "
                     "Attacks the normalize-when-below half of the clause.",
        "refinement": "faithful real patch = no change at all, so the failing "
                      "row that motivated this instance still fails. Measured "
                      "under the resolve harness with a semantically no-op "
                      "patch: resolved=False, FAIL_TO_PASS 0/2, PASS_TO_PASS "
                      "4/4. (Exactly one row's assertion actually fails, the "
                      "one the change targets; the second FAIL_TO_PASS row is "
                      "recorded as failing for the parsing reason described "
                      "under `reject-zero-loses-plain-form`.) A real "
                      "verify-does-not-imply-resolve break.",
        "witness": _witness(_NEG_THOU, "some 2",
                            [(_NEG_THOU, "some 2", True)],
                            _NEG_THOU, _ZERO),
    },
    {
        "id": "reject-value-rebuilt-not-input",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: hand the display step a value REBUILT from the input's amount,
        # displaying the way the plain zero value displays, instead of the input
        # itself. The guard and the normalized branch are exactly the spec's;
        # only the pass-through value is a reconstruction.
        #
        # WHY IT IS SHIPPED, and what it costs an earlier carrier. This is the
        # faithful model of round-tripping the input through a DESCRIPTION of it
        # — reading the input's facets and building a fresh value from them —
        # and it is the shape the recorded attack on this bundle took. On a
        # carrier that holds only a description of the input (a written triple,
        # or the amount alone) the rebuild is provably the identity by structure
        # eta, so the spec ADMITS it, while its faithful real counterpart
        # `Decimal(number.as_tuple())` discards the input's runtime type and the
        # unchanged tail then displays it via the base class. That is a
        # verify-does-not-imply-resolve break and it is unreachable by any rival
        # on such a carrier: the rival's argument and the spec's are the same
        # point there. The `render` facet is what makes the two points differ,
        # and this is the rival that pins it.
        #
        # Its conditioning hypothesis is FACTUAL rather than merely satisfiable:
        # the two values it separates are a `Decimal` subclass instance and the
        # plain `Decimal` of the same amount, whose displayed strings the real
        # code genuinely differs on (`'{:f}'.format(number)` dispatches on
        # `type(number).__format__`), which axiom_check.py measures — including
        # three pairs whose `as_tuple()` agrees as well, so no description-only
        # carrier separates them either.
        "module": _impl(
            "    let mut num : DecVal := "
            f"{{ amount := number.amount, render := zeroRender }}\n"
            "    if belowResolution number decimalPos then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`clampSmall` pins the display step's argument to the INPUT "
                     "itself on the pass-through branch, display behaviour "
                     "included. This rival rebuilds a value from the input's "
                     "amount alone, so at every input at or above the threshold "
                     "the display step receives a value that denotes the right "
                     "amount and displays like the plain zero instead of like "
                     "the input. Attacks whether the pass-through value is the "
                     "input or a reconstruction of it — the decision no "
                     "description-only carrier can express.",
        "refinement": "faithful real patch replaces `number` by "
                      "`Decimal(number.as_tuple())` before the unchanged tail "
                      "displays it. Measured against the instance's own suite: "
                      "resolved=False, FAIL_TO_PASS 1/2, PASS_TO_PASS 4/4 — the "
                      "row the change targets now PASSES and the subclass row "
                      "FAILS with `'1,23' != '€ 1,23'`, because the rebuild "
                      "keeps the amount and drops the type, so the display step "
                      "uses the base class's formatting instead of the "
                      "subclass's. A real verify-does-not-imply-resolve break, "
                      "and the sharpest one on this instance: it is the only "
                      "rival measured here that breaks a row the gold patch "
                      "leaves untouched, so its failure is visible with the "
                      "targeted row green and cannot be an artifact of that "
                      "row's own failure.",
        "witness": _witness(_FIVE, "some 3", [(_FIVE, "some 3", False)],
                            _REBUILT, _FIVE),
    },
    {
        "id": "reject-zero-loses-plain-form",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: normalize the AMOUNT to zero but retain the input's own display
        # behaviour, so the value handed onward denotes zero without displaying
        # as the plain zero value does. This is the faithful model of
        # normalizing by multiplying the input by zero: decimal multiplication
        # keeps the sign and adds the exponents, so `number * 0` is a zero
        # written at the input's own place and the unchanged tail displays it
        # accordingly.
        #
        # WHY IT IS SHIPPED. It is the mirror of the previous rival on the OTHER
        # branch: that one gets the amount right and the display wrong on the
        # pass-through branch, this one on the normalized branch. Together they
        # pin both facets on both branches. On an amount-only carrier this
        # rival's argument and the spec's are the same point, and its faithful
        # patch does not resolve the instance (see `refinement`).
        #
        # Its witness is stated at the F2P row's own magnitude, and its
        # conditioning hypothesis is FACTUAL: the two zeros it separates are
        # `0E-303` and `0`, whose displayed strings the real code genuinely
        # differs on (the unchanged tail branches on `abs(exponent) +
        # len(digits) > 200`), which axiom_check.py measures.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number decimalPos then\n"
            "      num := { amount := 0, render := number.render }\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`clampSmall` pins the display step's argument to "
                     "`plainZero` — the plain zero value, which displays as a "
                     "single zero digit in the units place — not merely to some "
                     "value that DENOTES zero. This rival zeroes the amount "
                     "while retaining the input's own display behaviour, so at "
                     "any input below the threshold the display step receives a "
                     "zero that displays the way the input would where the spec "
                     "demands the plain one. Attacks WHICH value the "
                     "normalization produces — the decision an amount-only "
                     "carrier cannot express at all.",
        "refinement": "faithful real patch replaces the value by `number * 0` "
                      "instead of by a plain zero. Measured under the resolve "
                      "harness: resolved=False, FAIL_TO_PASS 0/2, PASS_TO_PASS "
                      "4/4. The behavioural cause is one row: it asks for "
                      "'0.000' at three requested positions and gets the "
                      "scientific display of a zero written at the input's own "
                      "place instead, because the retained place keeps the "
                      "value on the >200-digit branch of the unchanged tail. "
                      "(Run directly, only that row's assertion fails; the "
                      "second FAIL_TO_PASS row requests no position count, so "
                      "the guard never fires and it passes. It is *recorded* as "
                      "failing because the runner emits its verbose status on "
                      "the same output line as the first row whenever that "
                      "row's subtest fails, so the status is unparseable — "
                      "which is also why a row that passes pre-patch is in the "
                      "FAIL_TO_PASS list at all: the no-op measurement above "
                      "records 0/2 too.) A real "
                      "verify-does-not-imply-resolve break.",
        "witness": _witness(_F2P, "some 3", [(_F2P, "some 3", True)],
                            _ZERO_OWN_RENDER, _ZERO),
    },
    {
        "id": "reject-always-normalize",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: normalize unconditionally, dropping the guard. Over-application
        # of the change instead of omission.
        # (Sibling: rival-over-collapse.)
        "module": _impl(
            "    let mut num : DecVal := number\n"
            f"    num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`clampSmall` normalizes only when `belowResolution` holds; "
                     "this rival normalizes always, so at any input whose "
                     "magnitude is at or above the threshold the argument is the "
                     "plain zero value where the spec demands `number`. Attacks "
                     "the leave-alone-when-not-below half of the same clause, "
                     "the opposite direction from reject-never-normalize.",
        "refinement": "faithful real patch normalizes every value regardless of "
                      "magnitude, destroying the ordinary display path "
                      "(measured: 16 suite failures, including rows the "
                      "instance must keep passing). A real break.",
        "witness": _witness(_FIVE, "some 3", [(_FIVE, "some 3", False)],
                            _ZERO, _FIVE),
    },
    {
        "id": "reject-non-strict-threshold",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: compare with `≤` instead of `<`, so a magnitude exactly ON the
        # threshold is normalized away. Off-by-one at the boundary. Written with
        # the shared pure layer's own pieces (`ratAbs`, `guardCutoff`) so nothing
        # but the comparison differs.
        # The probe point is the threshold itself: `guardCutoff 2` exactly. That
        # is the ONLY magnitude at which the two comparisons differ, and it is a
        # real 29-significant-digit input, not an artificial one — the real
        # comparison materializes it UP to the resolution (ties to even, and the
        # resolution's last kept digit is even) and so does not normalize it.
        # (Sibling: rival-non-strict-cutoff.)
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if decimalPos.any (fun p => decide "
            "(ratAbs number.amount ≤ guardCutoff p)) then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`belowResolution` is a STRICT comparison against "
                     "`guardCutoff p`; this rival makes it non-strict, so a "
                     "magnitude exactly equal to the threshold is normalized "
                     "away where the spec keeps the input. Attacks the boundary "
                     "of the threshold predicate, which neither the never- nor "
                     "the always-normalize rival touches.",
        "refinement": "faithful real patch normalizes a magnitude that "
                      "materializes exactly onto the smallest visible step, "
                      "which the operation must still display faithfully "
                      "(measured: 2 suite failures on rows the instance must "
                      "keep passing). A real break.",
        "witness": _witness(_TIE, "some 2", [(_TIE, "some 2", False)],
                            _ZERO, _TIE, extra_simp=("Option.any",),
                            extra_haves=(("hb1", f"ratAbs ({_A_TIE}) "
                                                 "≤ guardCutoff 2"),)),
    },
    {
        "id": "reject-threshold-exact-compare",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: compare the EXACT magnitude against `resolution p` instead of
        # against `guardCutoff p` — i.e. model the real comparison as if it were
        # taken on the exact magnitude rather than on the magnitude the ambient
        # environment materializes at its working precision.
        #
        # WHY IT IS SHIPPED. This is the faithfulness defect the `guardCutoff`
        # lowering exists to close, and it is invisible on any carrier that
        # models the comparison exactly: `resolution p` LOOKS like the literal
        # threshold the real code writes down, so a spec stating it reads as the
        # more faithful of the two. It is not. The real comparison materializes
        # the magnitude at `workingDigits` significant digits, ties to even,
        # BEFORE comparing, so on the whole half-ulp window
        # `[guardCutoff p, resolution p)` the exact comparison says "below" and
        # the real one says "not below". Its witness point sits strictly inside
        # that window, so the two implementations genuinely differ there.
        # mapping.md §2 carries the derivation; axiom_check.py checks the
        # equivalence of `belowResolution` to the real comparison executably
        # over the window, at the boundary, and on both signs.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if decimalPos.any (fun p => decide "
            "(ratAbs number.amount < resolution p)) then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`belowResolution` compares against `guardCutoff p`, the "
                     "resolution lowered by half a unit in the last significant "
                     "digit the ambient environment keeps — because the "
                     "magnitude a real comparison sees is materialized at that "
                     "precision before being compared. This rival compares the "
                     "exact magnitude against `resolution p` itself, so every "
                     "magnitude in the half-ulp window below the resolution is "
                     "normalized away where the spec keeps the input. Attacks "
                     "the MATERIALIZATION of the threshold — the one component "
                     "that distinguishes the modelled predicate from a naive "
                     "reading of the literal the real code writes.",
        "refinement": "faithful real patch compares an exactly-computed "
                      "magnitude against the threshold instead of the "
                      "context-rounded one — e.g. by taking the magnitude "
                      "through `Decimal.copy_abs()` (which is exact) rather "
                      "than through `abs()` (which is a context operation). "
                      "Measured over the window: the two disagree on every "
                      "magnitude in `[guardCutoff p, resolution p)`, i.e. on "
                      "inputs with more significant digits than the ambient "
                      "precision, and NO suite row lands there — measured under "
                      "the resolve harness with `number.copy_abs() < cutoff` "
                      "substituted for `abs(number) < cutoff`: resolved=True, "
                      "FAIL_TO_PASS 2/2, PASS_TO_PASS 4/4, i.e. ZERO suite "
                      "failures. So this rival is NOT a "
                      "verify-does-not-imply-resolve break and is shipped on "
                      "uniqueness and "
                      "FAITHFULNESS grounds — it is the shape an auditor "
                      "reproduces from the source and finds the spec admits, "
                      "which is what made the earlier spec fail its "
                      "faithfulness review.",
        "witness": _witness(_WINDOW, "some 2", [(_WINDOW, "some 2", False)],
                            _ZERO, _WINDOW, extra_simp=("Option.any",),
                            extra_haves=(("hb1", f"ratAbs ({_A_WINDOW}) "
                                                 "< resolution 2"),)),
    },
    {
        "id": "reject-threshold-one-coarser",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: shift the requested position count down by one before deciding,
        # so the threshold is a factor of ten coarser than the spec's. Attacks
        # the MAGNITUDE of the threshold rather than its strictness or its
        # presence.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number (decimalPos.map (fun p => p - 1)) then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "the threshold is fixed by the REQUESTED position count; "
                     "this rival decides against the count minus one, a "
                     "threshold one order of magnitude coarser, so magnitudes "
                     "strictly between the two thresholds are normalized away "
                     "where the spec keeps their inputs. Attacks how the "
                     "threshold depends on `decimalPos`, a dependency no other "
                     "rival probes.",
        "refinement": "faithful real patch normalizes magnitudes that DO affect "
                      "a visible position at the requested count, discarding "
                      "significant digits the operation must display; that is a "
                      "strictly wider normalization than the instance calls for "
                      "and breaks currently-passing rows. A real break.",
        "witness": _witness(_THOU, "some 3",
                            [(_THOU, "some 3", False),
                             (_THOU, "some 2", True)],
                            _ZERO, _THOU),
    },
    {
        "id": "reject-normalize-when-unrequested",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: when no position count is requested, substitute a default and
        # decide anyway — so the `none` arm normalizes instead of passing
        # through. This is the ONLY rival that attacks the `none` arm, and the
        # only one whose witness drives `decimalPos = none`.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number (some (decimalPos.getD 1)) then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`belowResolution` is `false` on the `none` arm by "
                     "definition, so when no position count is requested the "
                     "spec pins the argument to `number` unchanged; this rival "
                     "invents a default count and normalizes small magnitudes "
                     "anyway. Attacks the `none` arm of the threshold "
                     "predicate — the second input binder's other "
                     "constructor, which no other rival reaches.",
        "refinement": "faithful real patch normalizes small magnitudes even when "
                      "the caller requested no position count, where full "
                      "precision must be preserved (measured: 1 suite failure on "
                      "a row the instance must keep passing). A real break.",
        "witness": _witness(_THOU, "none",
                            [(_THOU, "none", False),
                             (_THOU, "some 1", True)],
                            _ZERO, _THOU),
    },
    {
        "id": "reject-threshold-no-floor",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: drop the `max p 1` floor from the threshold, keeping the
        # materialization lowering exactly as the spec has it, so ONLY the floor
        # differs: at a requested count of ZERO the boundary becomes one whole
        # unit instead of the first fractional position. Attacks the FLOOR of
        # the threshold, which no other rival touches: never/always-normalize
        # ignore the threshold's value, non-strict attacks its comparison,
        # exact-compare attacks its materialization, one-coarser attacks its
        # exponent for p ≥ 1, and normalize-when-unrequested attacks the `none`
        # arm. The floor is only observable at `some 0`, so this is the only
        # rival that drives that point.
        #
        # AUDIT NOTE (this case was recovered, not ported). The sibling's
        # counterpart was dropped by the original port on two stated grounds,
        # both of which measurement contradicts. (a) "Its faithful patch
        # resolves the instance, so a reject would be resolve-preserving": the
        # suite indeed stays green (see `refinement` for the measured reason).
        # But resolve-preservation is a statement about the SUITE, not about the
        # spec: the rival is observably WRONG on this carrier (see the witness
        # point below), and a uniqueness rival's job is to pin the clause, not
        # to be caught by the suite. (b) "At the natural probe point the display
        # step maps both arguments to the same output, so no honest conditioning
        # hypothesis exists": false. The two thresholds disagree on the WHOLE
        # sub-unit window at a zero requested count — for every input whose
        # magnitude satisfies `1/10 ≤ |n| < 1` the spec keeps it while the rival
        # replaces it with the plain zero, so the two arguments genuinely differ
        # and the conditioning hypothesis is satisfiable there. The window is
        # symmetric in sign, since the guard compares `ratAbs`; the negative
        # probe point below is one admissible choice among many, kept because it
        # additionally exercises an input whose sign must survive into the
        # display.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if decimalPos.any (fun p => decide (ratAbs number.amount <\n"
            "        (1 : Rat) / 10 ^ p - (1 : Rat) / 10 ^ p "
            "/ (2 * (10 : Rat) ^ workingDigits))) then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "`resolution p` is `1 / 10 ^ (max p 1)` — the `max p 1` "
                     "floor keeps the boundary at the first fractional position "
                     "even when zero positions are requested. This rival uses "
                     "`1 / 10 ^ p` unfloored (lowered by the same half unit, so "
                     "only the floor differs), so at a requested count of zero "
                     "its boundary is a whole unit and every magnitude below "
                     "one is normalized away, where the spec keeps every input "
                     "at or above the first fractional position. Attacks the "
                     "threshold's FLOOR, the one component of `resolution` no "
                     "other rival probes.",
        "refinement": "faithful real patch normalizes magnitudes in the "
                      "sub-unit window at a zero requested count, discarding a "
                      "value the operation must still display. Measured against "
                      "the whole reconstructed suite it costs ZERO failures, "
                      "and the reason is COVERAGE, not agreement: the suite "
                      "exercises a zero requested count on exactly one row, "
                      "whose magnitude is ~1e-12 — far below BOTH the floored "
                      "and the unfloored boundary, so both normalize it to the "
                      "same value and the row cannot tell them apart. No suite "
                      "row lands in the window where they differ "
                      "(1/10 ≤ |n| < 1 at a zero requested count) at all. So "
                      "this rival is NOT a verify-does-not-imply-resolve break "
                      "and is shipped on uniqueness grounds only: it is "
                      "observably wrong on this carrier at every sub-unit "
                      "magnitude with a zero requested count, one of which its "
                      "witness refutes it at.",
        # `hb1` is the rival's own guard condition at the probe point, stated in
        # the shape the reduction leaves it: the rival writes `1 / 10 ^ p`, and
        # at `p = 0` the ambient `pow_zero` collapses `10 ^ 0` to `1`, so the
        # condition standing in the goal reads `1 / 1 - 1 / 1 / (2 * 10 ^ 28)`.
        # Stating it as `1 / 10 ^ 0` instead leaves nothing for simp to rewrite
        # and the rival's `if` survives undischarged.
        "witness": _witness(
            _NEG_HALF, "some 0", [(_NEG_HALF, "some 0", False)],
            _ZERO, _NEG_HALF, extra_simp=("Option.any", "pow_zero"),
            extra_haves=(("hb1", f"ratAbs ({_A_NEG_HALF}) < (1 : Rat) / 1 "
                                 "- (1 : Rat) / 1 "
                                 "/ (2 * (10 : Rat) ^ workingDigits)"),)),
    },
    {
        "id": "reject-invented-domain-bound",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: normalize exactly as the spec says, but only while the requested
        # position count stays under a bound OF ITS OWN — one drawn strictly
        # INSIDE the range `require positionsInExponentRange decimalPos` admits
        # (it stops at `max p 1 + workingDigits > 30`, i.e. from a requested
        # count of 3 upward, where the clause admits every count up to 999998).
        # Past its own bound it hands the input through untouched.
        #
        # WHY IT IS SHIPPED, and what it guards. This spec carries a `require`
        # clause, and a precondition is the one edit that can turn a faithfulness
        # repair into a NEW hole: whatever counts the clause excludes, the
        # obligation says nothing about, so an implementation is free to be wrong
        # there — `pos-domain-restricted` is the positive that measures exactly
        # that freedom. The hole would be an implementation reading the clause as
        # licence to pick its OWN, tighter cut-off and go wrong on counts the
        # clause still admits. This rival is that shape at its most plausible:
        # its cut-off is stated in the very same arithmetic as the clause
        # (`max p 1 + workingDigits` against a numeral), so it differs from the
        # spec's domain only in WHERE the numeral sits. The spec must refuse it,
        # and it does — the frozen script is kept byte-identical here, so the
        # refusal is the `ensures` obligation going unclosed on the in-range
        # counts the rival abandoned, not a tactic mismatch.
        #
        # The witness point is `0.0001` at a requested count of 3: below the
        # threshold, so the spec pins the display step's argument to the plain
        # zero value, while the rival's own bound has already stopped firing at
        # that count and passes `0.0001` through. Note the rival AGREES with the
        # spec at every count of 2 or less, which is what makes it a domain-bound
        # attack rather than another threshold attack: no smaller-count probe can
        # tell the two apart.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number decimalPos && !(decimalPos.any\n"
            "        (fun p => decide (30 < max p 1 + workingDigits))) then\n"
            f"      num := {_ZERO}\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "the sole `ensures` pins the display step's argument to "
                     "`clampSmall number decimalPos` for EVERY requested "
                     "position count the `require` clause admits, which is every "
                     "count up to 999998. This rival normalizes only up to a "
                     "self-chosen count of 2 and passes below-threshold inputs "
                     "through above it, so at a count of 3 the argument is "
                     "`number` where the spec demands the plain zero value. "
                     "Attacks the DOMAIN of the clause rather than any of its "
                     "components — it is the rival that would be admitted if the "
                     "`require` clause were read as licence for an impl to pick "
                     "its own cut-off, and it is the counterweight to "
                     "`pos-domain-restricted`.",
        "refinement": "faithful real patch = the gold block guarded by "
                      "`if decimal_pos is not None and decimal_pos <= 2:`, so "
                      "every call with three or more requested positions keeps "
                      "the pre-patch behaviour. That is exactly the shape of the "
                      "row the instance exists to fix ("
                      "`Decimal('0.' + '0'*299 + '1234')` at `decimal_pos=3`, "
                      "which must display `'0.000'` and instead reaches the "
                      "scientific-notation branch), so the targeted assertion "
                      "still fails. Measured under the resolve harness: "
                      "resolved=False, FAIL_TO_PASS 0/2, PASS_TO_PASS 4/4 "
                      "(exactly one row's assertion actually fails, the one the "
                      "change targets; the second FAIL_TO_PASS row is recorded "
                      "as failing for the parsing reason described under "
                      "`reject-zero-loses-plain-form`). A real "
                      "verify-does-not-imply-resolve break.",
        # The rival's own bound has to be REDUCED for the witness to see that it
        # does not fire: `Option.any` gets the `some 3` under the applied
        # function, `max_def` turns `max 3 1` into the decidable branch, and
        # `workingDigits` supplies the 28 — after which `30 < 31` decides and the
        # conjunction collapses to `false`, leaving the rival's argument as the
        # input itself. Without the three the `if` survives unreduced and the case
        # lands `witness-undecided` rather than refuting.
        "witness": _witness(_TENTHOU, "some 3",
                            [(_TENTHOU, "some 3", True)],
                            _TENTHOU, _ZERO,
                            extra_simp=("Option.any", "max_def",
                                        "workingDigits")),
    },
    {
        "id": "reject-render-output-perturbed",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: normalize correctly, then prepend one extra character to what
        # the display step produced. Attacks the `ensures` clause's OUTER
        # equality — that `out` is exactly what the display step returns on the
        # normalized value — which every other rival leaves alone (they all
        # perturb that step's ARGUMENT and return its result verbatim).
        #
        # AUDIT NOTE (recovered, not ported). The original port dropped the
        # sibling's two character-level rivals as inexpressible, reasoning that
        # an `opaque` display step with no asserted property leaves "no
        # character-level structure to perturb". That conflates two different
        # things. It is true that no LITERAL output is derivable, so a rival
        # cannot be refuted by computing an expected string. But the
        # postcondition still pins `out` to that step's result up to EQUALITY,
        # and a structural perturbation of an unknown list is refutable without
        # knowing any of its characters: `c :: l ≠ l` holds for every `c` and
        # every `l` by a length argument alone. So this witness needs no
        # conditioning hypothesis at all — it binds only the display function
        # its input carries.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number decimalPos then\n"
            f"      num := {_ZERO}\n"
            "    return '0' :: renderDecimal num decimalPos"),
        "rationale": "the sole `ensures` is an EQUALITY, `out = renderDecimal "
                     "(clampSmall number decimalPos) decimalPos`: it pins not "
                     "only which value reaches the display step but that the "
                     "method returns that step's result unchanged. This rival "
                     "normalizes exactly as the spec demands and then prepends "
                     "one character, so `out` is one longer than the pinned "
                     "value at every input. Attacks the outer equality of the "
                     "clause — one of only three rivals that perturb the RESULT "
                     "rather than the display step's argument.",
        "refinement": "faithful real patch emits a spurious leading character "
                      "on every displayed value, so every row of the "
                      "reconstructed suite that displays a decimal at all "
                      "disagrees (measured: fails the very row the change "
                      "targets as well as rows the instance must keep "
                      "passing). A real break.",
        "witness": _witness_len(_THOU, "some 2", [(_THOU, "some 2", True)]),
    },
    {
        "id": "reject-dp-zero-output-perturbed",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: correct everywhere except that at a requested count of ZERO it
        # appends one extra character to the displayed result. A PARTIAL-DOMAIN
        # version of the previous case: the outer equality is broken on exactly
        # one point of the second binder, so a spec that pinned the output only
        # "for most inputs" would admit it.
        #
        # AUDIT NOTE (recovered, not ported) — the sibling's dp==0 rendering
        # rival, which the original port dropped as inexpressible. Same
        # reasoning as reject-render-output-perturbed: the perturbation is
        # refuted by a length argument against an unknown list, so the opaque
        # display step is no obstacle.
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number decimalPos then\n"
            f"      num := {_ZERO}\n"
            "    if decimalPos = some 0 then\n"
            "      return (renderDecimal num decimalPos) ++ ['.']\n"
            "    return renderDecimal num decimalPos"),
        "rationale": "the `ensures` pins `out` to the display step's result at "
                     "EVERY input, not at most of them. This rival satisfies "
                     "the clause everywhere except at a requested count of "
                     "zero, where it appends one character to the displayed "
                     "value. Attacks the outer equality on a single point of "
                     "the `decimalPos` binder, so it also probes that the "
                     "clause is quantified over the whole domain rather than "
                     "holding generically.",
        "refinement": "faithful real patch appends a stray character to every "
                      "value displayed at a zero requested count, where the "
                      "correct display carries no fractional part at all "
                      "(measured: 1 suite failure, on a row the instance must "
                      "keep passing). A real break.",
        "witness": _witness_len(_THOU, "some 0", [(_THOU, "some 0", True)]),
    },
    {
        "id": "reject-output-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: normalize exactly as the spec demands, then REVERSE the
        # displayed result. Added by a later audit to close a real gap, not to
        # re-confirm a clause an existing rival already pins.
        #
        # WHAT GAP. Both other output-side rivals
        # (reject-render-output-perturbed, reject-dp-zero-output-perturbed)
        # change the displayed list's LENGTH, and both of their witnesses close
        # by the same length argument (`_LEN_TAIL`: `c :: l ≠ l`, `l ++ [c] ≠
        # l`). That technique is blind to any perturbation that PRESERVES
        # length, so without this case the battery's whole defence of the outer
        # equality would rest on one refutation style with a known blind spot. A
        # reversal is the smallest perturbation in that spot: same characters,
        # same length, different list.
        #
        # WHY IT NEEDS ROUTE 1 rather than ROUTE 2. `l.reverse ≠ l` is FALSE in
        # general — every palindrome is a counterexample, and the empty list is
        # one — so no unconditional length-free argument refutes this rival, and
        # that is precisely why the shipped tail cannot reach it. The refutation
        # is instead stated at a point described by HYPOTHESIS, exactly as the
        # argument-route witnesses do: `hr` assumes the display step's output at
        # the probe point is not its own reverse. One hypothesis, about one term,
        # trivially satisfiable for an opaque constant (the gate's consistency
        # probe cannot derive `False` from it).
        "module": _impl(
            "    let mut num : DecVal := number\n"
            "    if belowResolution number decimalPos then\n"
            f"      num := {_ZERO}\n"
            "    return (renderDecimal num decimalPos).reverse"),
        "rationale": "the sole `ensures` pins `out` to the display step's result "
                     "itself, not merely to a list with the same characters or "
                     "the same length. This rival normalizes exactly as the "
                     "clause demands and then reverses the displayed result, so "
                     "it agrees with the spec on that step's ARGUMENT and on "
                     "the output's LENGTH and disagrees only on the order of "
                     "what it returns. It is the only rival whose perturbation "
                     "is length-preserving, so it is the only one the battery's "
                     "length-argument refutation style cannot reach; it pins "
                     "the outer equality against permutation rather than "
                     "against lengthening or shortening.",
        "refinement": "faithful real patch reverses every displayed value, so "
                      "the display disagrees on every row whose expected text "
                      "is not its own reverse (measured against the "
                      "reconstructed suite: 25 of 27 Decimal rows fail; the two "
                      "survivors are the rows whose expected text happens to be "
                      "a palindrome). The row the change targets is among the "
                      "failures. A real verify-does-not-imply-resolve break.",
        "witness": ("extract_program_for formatDecimal\n\n"
                    "example (rho : Option Nat → List Char)\n"
                    f"    (hr : (renderDecimal ({_ZERO}) (some 2)).reverse\n"
                    f"      ≠ renderDecimal ({_ZERO}) (some 2)) :\n"
                    f"    formatDecimalExec ({_THOU}) (some 2)\n"
                    "      ≠ DivM.res (renderDecimal "
                    f"(clampSmall ({_THOU}) (some 2)) (some 2)) := by\n"
                    + _below("hb0", _THOU, "some 2", True)
                    + "  unfold formatDecimalExec formatDecimal\n"
                    + "  simp [NonDetT.run, NonDetT.bind, bind, pure, "
                      "clampSmall, plainZero, renderDecimal, hb0]\n"
                    + "  first\n"
                    + "    | exact hr\n"
                    + "    | (intro h; exact hr (DivM.res.inj h))\n"),
    },
]

# The axiom lane belongs to G-AX, and this bundle declares no `axiom` (the
# display step is an `opaque` free constant with nothing asserted about it, so
# there is nothing to validate). The sibling's three AXIOM_TESTS have no
# counterpart; this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 6 uniqueness rivals) plus 3 AXIOM_TESTS.
# Every one is accounted for below.
#
# The sibling contracts a helper returning `Optional[List[int]]` — a nullable
# list of code points it ASSEMBLES itself — under a precondition, with two
# @Pure oracles and a PSeq-valued postcondition made of four independent
# clauses. This bundle contracts ONE method over a coarser carrier: the display
# step is a facet of the carried value, the return is an unconstrained
# `List Char`, the `require` clause bounds only the SECOND binder (the requested
# position count, DOMAIN REPAIR below) and never the input, and the whole
# obligation is a SINGLE `ensures` pinning that step's ARGUMENT. Both surfaces
# model the same behaviour
# — normalize an input whose magnitude cannot affect any visible position at the
# requested count to a plain zero, leave everything else alone — but here only
# the argument is transparent, so the argument-route witnesses condition on the
# display step (CARRIER NOTE above).
#
# AUDIT CORRECTION. An earlier version of this footer recorded three of the
# sibling's rivals as dropped-because-inexpressible on this carrier. An
# independent audit landed all three with real builds, so all three are now
# carried and the "inexpressible" claims are withdrawn:
#   * the two character-level rivals were said to have "no character-level
#     structure to perturb" because the display step assembles nothing here. But
#     the `ensures` is an EQUALITY on that step's RESULT, and perturbing the
#     structure of an unknown list is refutable by a length argument with no
#     hypothesis at all (ROUTE 2 in the CARRIER NOTE). Carried as
#     reject-render-output-perturbed and reject-dp-zero-output-perturbed.
#   * the threshold-floor rival was said to have no available conditioning
#     hypothesis because "the display step maps both arguments to the same
#     output at the natural probe point". That holds only at non-negative
#     magnitudes; at a negative sub-unit magnitude the two arguments genuinely
#     differ. Carried as reject-threshold-no-floor.
# Recorded here rather than silently rewritten, because "the carrier collapses
# this distinction" is a claim a later reader must be able to check.
#
#   sibling case                  kind            -> here
#   -----------------------------------------------------------------------
#   pos-control-grounded-guard    soundness       -> pos-collapsed-direct   PORTED
#   pos-control-reorder-decision  soundness       -> pos-let-ladder         PORTED
#   (added)                       soundness       -> pos-guard-negated      ADDED
#   (added)                       soundness       -> pos-if-else            ADDED
#   (added)                       soundness       -> pos-facet-round-trip   ADDED
#   (added)                       soundness       -> pos-domain-restricted  ADDED
#   (added)                       admissibility   -> admiss-precond-satisfiable
#                                                                           ADDED
#                                   (the two DOMAIN REPAIR cases; see that note.)
#   admiss-f2p-shaped             admissibility   -> admiss-f2p-shaped
#                                                              PORTED (recovered)
#                                   (An earlier port recorded this as VACUOUS
#                                    because the method had no `require` at the
#                                    time, so "there is no precondition an
#                                    F2P-shaped input could be shown to be
#                                    inside". Two things are wrong with that.
#                                    Even on a total domain the lane is live:
#                                    what it detects is the obligation being
#                                    UNSATISFIABLE, or degenerate, at exactly an
#                                    F2P-shaped input, which is what this case
#                                    tests — it discharges the obligation at that
#                                    concrete input by evaluation, in-region,
#                                    before closing the frozen `ensures`, and
#                                    four negative controls with one falsified
#                                    conjunct each all fail by `unsolved goals`
#                                    under the try-guarded script, so the assert
#                                    is load-bearing. And the premise no longer
#                                    holds either: the spec now carries `require
#                                    positionsInExponentRange decimalPos`, so the
#                                    literal PRECOND-TOO-STRONG lane exists too
#                                    and is carried separately by
#                                    admiss-precond-satisfiable.)
#   rival-never-collapse          uniqueness      -> reject-never-normalize PORTED
#   rival-over-collapse           uniqueness      -> reject-always-normalize PORTED
#   rival-non-strict-cutoff       uniqueness      -> reject-non-strict-threshold
#                                                                           PORTED
#   rival-no-threshold-floor      uniqueness      -> reject-threshold-no-floor
#                                                              PORTED (recovered)
#   rival-dp0-stray-separator     uniqueness      -> reject-dp-zero-output-perturbed
#                                                              PORTED (recovered)
#   rival-extra-leading-zero      uniqueness      -> reject-render-output-perturbed
#                                                              PORTED (recovered)
#   (added)                       uniqueness      -> reject-threshold-one-coarser
#                                                                           ADDED
#   (added)                       uniqueness      -> reject-normalize-when-unrequested
#                                                                           ADDED
#   (added)                       uniqueness      -> reject-output-reversed   ADDED
#   (added)                       uniqueness      -> reject-value-rebuilt-not-input
#                                                                           ADDED
#   (added)                       uniqueness      -> reject-zero-loses-plain-form
#                                                                           ADDED
#   (added)                       uniqueness      -> reject-threshold-exact-compare
#                                                                           ADDED
#                                   (the three carrier/threshold rivals: they
#                                    exist with the facets and the lowering they
#                                    need; see the two notes below.)
#   (added)                       uniqueness      -> reject-invented-domain-bound
#                                                                           ADDED
#                                   (the third DOMAIN REPAIR case: the rival the
#                                    `require` clause would admit if it were read
#                                    as licence for an impl to pick its own,
#                                    tighter cut-off.)
#   ax-below-cutoff-sound         axiom           -> (none)  G-AX / no axiom
#   ax-zero-render-sound          axiom           -> (none)  G-AX / no axiom
#   ax-below-cutoff-containment   axiom           -> (none)  G-AX / no axiom
#
# 9 ported (4 of them recovered during audit) + 12 added = 21 velvet cases
# (6 soundness, 2 admissibility, 13 uniqueness). The last three added are the
# DOMAIN REPAIR trio below.
#
# CARRIER REPAIR — why the `render` facet exists and what it cost. Earlier
# versions of this bundle carried the input as a DESCRIPTION of itself: first as
# a bare `Rat` (the amount alone), then as a written triple (sign, digits,
# ten's place). Both are descriptions, and both admitted an implementation that
# round-trips the input through its own description before handing it on —
# provably the identity on a description-only carrier by structure eta, and NOT
# the identity in the real code, where the unchanged tail displays the value via
# `'{:f}'.format(number)` and that dispatches on the input's runtime TYPE. A
# `Decimal` subclass that displays itself with a prefix is such an input, one of
# the instance's own failing rows uses exactly that shape, and no description of
# a value records its type. So the carrier now holds the input's DISPLAY
# BEHAVIOUR as a facet, which makes the pass-through branch a claim about the
# input itself, and the two rebuild rivals
# (reject-value-rebuilt-not-input, reject-zero-loses-plain-form) are shipped and
# refused. What it cost the positives: nothing measurable — all five soundness
# reshapes still verify under the frozen script, including `pos-let-ladder`
# (which writes the plain zero by NAME where the frozen body spells out the
# record) and `pos-facet-round-trip` (which reassembles the pass-through value
# from BOTH of the input's own facets), so the spec is neither over-fit to a
# spelling of the zero nor hostile to reassembly as such.
#
# THRESHOLD REPAIR — why `guardCutoff` and not `resolution`. The comparison the
# real code makes is taken on the magnitude the ambient environment MATERIALIZES
# at its working precision (28 significant digits, ties to even), not on the
# exact magnitude. An earlier version of this spec compared exactly against
# `resolution p`, which reads as the more faithful of the two because
# `resolution p` is the literal the real code writes down; it is not, and the
# two predicates differ on the whole half-ulp window `[guardCutoff p,
# resolution p)`. The spec now compares against the lowered threshold, the
# equivalence is checked executably by axiom_check.py over the window and at the
# boundary in both signs, and the exact-comparison reading is shipped as a rival
# (reject-threshold-exact-compare) so that the distinction cannot silently
# regress. Cost to the positives: none — the threshold is a shared pure
# definition and every positive reaches it through `belowResolution`.
#
# DOMAIN REPAIR — why `require positionsInExponentRange decimalPos` exists, and
# the three cases that fence it. The THRESHOLD REPAIR above is a DERIVATION: the
# real comparison materializes the magnitude at 28 significant digits, so
# comparing the exact magnitude against `guardCutoff p` is the same predicate.
# That derivation places the lowered threshold at exponent
# `-(max p 1 + workingDigits)`, and it silently assumes the ambient environment
# can hold a digit there. Past a requested count of
# `leastExponentMagnitude - workingDigits` = 999998 it cannot, and the two
# readings part company in BOTH directions (measured in axiom_check.py
# `check_position_range_boundary`; the write-up with both witnesses is
# refinement.md §A0(iii)). An earlier version of this spec stated the `ensures`
# with no domain at all, which made it FALSE of the repository at those counts —
# a faithfulness defect rather than a spec-too-weak one, and the reason the
# clause was added. A precondition is also the one edit that can buy verification
# with a premise, so the battery fences it from all three sides and each side is
# a separate case:
#   * admiss-precond-satisfiable — the domain still CONTAINS everything this
#     instance grades (`none`, `some 0`, `some 3`) and everything up to the
#     stated boundary, and is not trivially true (it fails one count further
#     out). Without the negative conjunct a clause collapsed to `True` would
#     pass this lane.
#   * pos-domain-restricted — the clause is a DOMAIN restriction and is
#     CONSUMABLE: an impl correct inside it and returning the wrong thing
#     outside it verifies, which is what "the obligation says nothing there"
#     means operationally. This is the one positive that extends the frozen
#     script, and it has to: the frozen body ignores the clause, so the frozen
#     script never had to unfold it.
#   * reject-invented-domain-bound — an impl may NOT draw its own, tighter
#     cut-off inside the admitted range. Its cut-off is stated in the same
#     arithmetic as the clause, so it differs from the spec's domain only in
#     where the numeral sits, and the frozen script still refuses it.
# Cost to the positives: none measurable — all five byte-identical-script
# positives still verify with the clause in place, and the clause mentions
# neither binder's value beyond the requested count, so no positive had to be
# reshaped to satisfy it. Cost to the rivals: none — every shipped witness
# probes a count in {none, 0, 1, 2, 3}, all of which the clause admits, so no
# rival is refuted by the precondition instead of by the `ensures`.
#
# SPEC-TOO-WEAK PROBES RUN DURING AUDIT AND NOT SHIPPED. Wrong impls in these
# directions were built and judged against the frozen spec; all were REJECTED, so
# none is a spec hole and none is carried as a case (a rival that only
# re-confirms a clause an existing rival already pins would add builds without
# adding discrimination). Recorded so a later reader knows these directions were
# tried, not overlooked:
#   * drop `ratAbs` and compare the SIGNED amount           -> rejected
#   * clamp to a value whose amount is the threshold instead
#     of to a plain zero (right guard, wrong value)         -> rejected
#   * base 2 instead of base 10 in the threshold
#     (attacks resolution's BASE, not its exponent)         -> rejected
#   * `min p 1` (a cap where the spec has a floor)          -> rejected
#   * threshold one order FINER (the mirror of the shipped
#     one-coarser rival)                                    -> rejected
#   * lower the threshold by a FULL unit in the last kept
#     digit instead of by half of one (the mirror of the
#     shipped exact-compare rival, on the other side)       -> rejected
#   * normalize only when the input is negative             -> rejected
#   * hand the display step a value carrying the input's
#     amount magnitude with the sign discarded              -> rejected
#   * perturb the display step's SECOND argument, +1        -> rejected
#   * default the display step's second argument on `none`  -> rejected
#   * PARTIAL DOMAIN on either binder: exempt exactly one
#     requested count (`some 5`); exempt exactly one input   -> rejected
#   * the OUTER equality in the shortening direction: return
#     the displayed list's tail; return a constant `[]`      -> rejected
# The second-argument and partial-domain probes matter most: every shipped rival
# passes `decimalPos` through to the display step verbatim, so that argument
# position is the least-probed part of the clause, and the single-point probes
# confirm the `ensures` is pinned pointwise over BOTH binders rather than
# generically.
#
# SPEC-TOO-STRONG PROBES. Correct reshapes beyond the five shipped positives were
# built and measured against this spec. Four verify under the frozen script
# unchanged, and are recorded here rather than shipped only because they add no
# discrimination the five positives above do not already have:
#   * an early-return form with no local at all          -> verifies, frozen script
#   * a zero-amount special case ahead of the body       -> verifies, frozen script
#   * a doubly-negated guard                             -> verifies, frozen script
#   * a Bool round-trip with an explicit `= true` test   -> verifies, frozen script
# Three more are correct and are ACCEPTED, but only with a raised elaboration
# budget in addition to extra tactic steps, and the distinction matters enough to
# state exactly:
#   * a doubled-normalization form relying on idempotence
#   * a `cond` form with no `if` in it
#   * an `Option`-destructuring form that names NEITHER `clampSmall` NOR
#     `belowResolution` and spells the threshold out inline as a Prop-valued `if`
# Under the DEFAULT budget all three fail before any tactic runs, with
# `(deterministic) timeout at «tactic execution», maximum number of heartbeats
# (200000)` reported at the impl line itself — the weakest-precondition
# generation for these shapes exhausts the budget during ELABORATION, so no proof
# script could have rescued them. With `set_option maxHeartbeats 2000000` the
# obligation is generated and then closed: the first two by the frozen steps
# followed by `rcases decimalPos` and `simp_all`, the third by the frozen steps
# followed by `rcases decimalPos … <;> simp_all [… decide_eq_true_eq]` (that last
# lemma is the whole content of the gap — the reshape writes the threshold as a
# Prop-valued `if` where `belowResolution` produces `decide … = true`).
# So the spec accepts a faithful impl that shares none of the frozen body's
# vocabulary, which is the strongest available evidence it is not over-fit to the
# frozen shape, and no SPEC-TOO-STRONG hole was found. These three are PROBES and
# not shipped cases for a mechanical reason rather than a judgement call: raising
# `maxHeartbeats` needs a top-level `set_option`, which would appear in the spec
# view and break `markers.same_spec`, so a case needing it cannot be expressed in
# this battery at all. Needing extra tactic steps or a bigger elaboration budget
# is a proof-automation cost, not a spec defect.
# Two shapes are worth naming because they are the ones the earlier carriers
# admitted and this one refuses: round-tripping the input through a description
# of itself, and comparing the exact magnitude against the literal threshold.
# Neither is a correct reshape on this carrier and neither is listed here — both
# are shipped rivals (reject-value-rebuilt-not-input,
# reject-threshold-exact-compare), for the reasons in the two REPAIR notes.
#
# Classes the sibling itself records as N/A (FRAME-MUTATION, CONTROL-FLOW-EFFECT,
# UNGROUNDED-ORACLE-ECHO) are vacuous here as well: the method takes no mutable
# parameter and both languages are referentially transparent over these inputs,
# so there is no frame to violate and no observable effect to reorder. No
# substitute is fabricated for them. The termination class is NOT vacuous and is
# NOT dropped as such — the spec rejects a diverging rival; what blocks a case is
# the WITNESS side, measured and spelled out in the DIVERGENCE paragraph of the
# module docstring.
# ---------------------------------------------------------------------------
