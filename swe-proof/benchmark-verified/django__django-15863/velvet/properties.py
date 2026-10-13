"""properties.py — G-PBT falsification battery for django__django-15863 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct floatFormat`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against its ``witness_reference`` — a verifying impl of the same spec, used here
because the FROZEN impl cannot decide anything at all; see the CARRIER NOTE).

DEFENDED SURFACE (one contracted method over three read-only inputs):

  floatFormat (intDigits fracDigits : List Char) (p : Nat) return (out : List Char)
    require 1 ≤ p                             -- (P1)
    require fracDigits.length ≤ p             -- (P2) the kept-precision regime
    require intDigits ≠ []                    -- (P3)
    require ∀ c ∈ intDigits,  c.isDigit       -- (P4)
    require ∀ c ∈ fracDigits, c.isDigit       -- (P5)
    ensures out = renderFixed intDigits fracDigits p        -- (C1)

The method renders a non-negative decimal numeral — given as its integer-digit
run and its fractional-digit run — to exactly ``p`` fractional places, in the
regime where ``p`` is at least the numeral's own fractional length so nothing is
rounded away. C1 is the single ``ensures``, and it pins the whole output to
``renderFixed intDigits fracDigits p``, a TRANSPARENT ``def`` over the method's
own three arguments:

    intDigits ++ ['.'] ++ fracDigits ++ List.replicate (p - fracDigits.length) '0'

Read as an adversarial surface, that one clause is a CONJUNCTION of four
independent structural commitments, and a rival can violate any one of them
while honouring the other three:

  (a) the integer run is reproduced VERBATIM and in full, ahead of the point;
  (b) the separator is the decimal point, exactly one of them, in that position;
  (c) the fractional run is reproduced VERBATIM, in order, at FULL LENGTH —
      every significant digit the numeral carries survives. This is the
      load-bearing commitment: it is the one the issue is about, and the one a
      numeral that has been round-tripped through a lower-precision carrier
      cannot meet;
  (d) the fractional run is right-extended with exactly as many trailing '0' as
      are needed to reach the requested width ``p`` — no more, no fewer.

There is NO opaque callee anywhere in the spec: the ``axioms`` region is empty
and ``renderFixed`` is a concrete ``def`` (this bundle axiomatizes nothing —
mapping.md §3), so C1 is grounded in the inputs and there is no answer-key term
a wrong impl could echo (SPEC_GUIDE directive 8). The cheapest honest correct
impl therefore computes the render itself, which is what the positives carry.

THREE INPUT BINDERS, all load-bearing: ``intDigits`` (emitted verbatim ahead of
the point), ``fracDigits`` (emitted verbatim, and its LENGTH sets the pad width),
and ``p`` (the requested width). The reject witnesses drive all three across
SEVEN distinct input points — including the exact failing-test numeral, an EMPTY
fractional run, and the boundary ``p = fracDigits.length`` where the pad run is
empty — so the manifest demonstrates C1's dependence on each binder rather than
pinning any of them at one value (pts = 7).

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHAT THE GOLD-SIDE FAILURE IS WORTH.
A witness reaches the post-image through Velvet's tester machinery
(``floatFormatTester intDigits fracDigits p = false`` says the extracted
program's result violates the method's postcondition at that concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can interfere. ``decide`` reduces the extracted
program by kernel computation. Each reject rival is expressed LOOP-FREE (the
render written as one expression) so its extracted tester ``decide``s over the
concrete literals; the frozen program keeps a ``while`` pad loop under
``loom.semantics.choice "demonic"``, whose fixpoint elaborates through
``Classical.choice``, which the kernel will not unfold.

READ THAT HONESTLY, because it is the trap this backend sets. Measured against
the FROZEN solution, every witness below fails with

    Tactic `decide` failed ... its `Decidable` instance ... did not reduce to
    `isTrue` or `isFalse` ... reduction got stuck at the `Decidable` instance

That is ``witness-undecided``: the frozen side decided NOTHING, so its exit code
carries no information and a forged witness asserting the rival is CORRECT at an
agreement point would clear the same half. Every reject case therefore names a
``witness_reference`` — ``pos-control-direct-render``, the loop-free correct
render, which is ALSO shipped as an ``expect="verify"`` case in its own right so
the battery itself records that loop-freeness is not what any rival is rejected
for. Against that impl the tester reduces and ``decide`` refutes each witness
SEMANTICALLY:

    Tactic `decide` proved that the proposition
      floatFormatTester ['9'] ['5'] 2 = false
    is false

(exit 1, measured for all seven). So each witness holds of its rival and provably
FAILS of a correct impl at the same input on the same carrier shape. An impl the
verifier ACCEPTS cannot violate its own spec, so that failure is about the spec's
content and not about the kernel's inability to look.

Every carrier value is a concrete literal, so no witness binds a hypothesis and
no consistency probe is needed — no witness here can be a forgery derived from
contradictory assumptions. No banned token (sorry/admit/native_decide/axiom/
opaque). All seven checked out-of-band with ``scripts/lean_verify.sh``:
ELABORATES against its rival (exit 0), refuted against the reference (exit 1,
``decide`` proved it false), stuck against the frozen loop (exit 1).

PROOF-SHAPE CONTROL — why each rejection is attributable to the RENDER. A reject
rival must not fail under a tactic body that would also fail for a CORRECT impl
of the same shape, or the rejection attests to a script mismatch rather than to
the spec. Every loop-free rival here carries the same two-line body
(``loom_solve`` then ``simp_all [renderFixed]``), and that body is measured to
CLOSE for the loop-free CORRECT render — that is ``pos-control-direct-render``,
exit 0. So under it each rival's failure is its render's, and the residual goal
names the rival's own expression: e.g. ``⊢ List.replicate p '0' = fracDigits ++
List.replicate (p - fracDigits.length) '0'`` for the dropped fractional run,
``⊢ fracDigits.reverse = fracDigits`` for the reversal, ``⊢ intDigits.length ≤ 1``
for the clipped integer run. That residual goal IS the attribution.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY, and are the real work here. Two
    structurally different CORRECT impls must verify: the loop-free direct render
    (maximally different from the frozen backward pad loop, and the honest
    no-echo control) and a loop-PRESERVING reshape that stages the appended pad
    character in a local (keeping the frozen proof intact). Ports the sibling's
    ``pos-local-reshape``.
  * ADMISSIBILITY — the sibling probes that a normal digit list satisfies its
    read-only fractional-permission precondition. There is no permission surface
    here, but this method's precondition is NOT empty — it is a five-clause
    regime envelope (P1–P5) — so the probe is not degenerate, merely re-aimed:
    the risk is an envelope so tight, or a post-image so degenerate, that the
    modeled behaviour is never actually exercised.
    ``admiss-regime-nondegenerate`` discharges an in-region ``assert``, at
    concrete in-regime inputs, that the render genuinely pads when more places
    are asked for than the numeral carries, that it genuinely does NOT replace
    the numeral's own digits with that padding, and that an EMPTY fractional run
    is in-regime.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries a
    MANDATORY ``frame-mut-write`` rival that stores back into a read-only
    (fractionally-permissioned) input and must be rejected for INSUFFICIENT
    PERMISSION; the sibling calls it the project's #1 weakness class. Lean and
    Velvet are referentially transparent: all three inputs are immutable values,
    no parameter is declared ``mut`` (only the loop-locals ``digits`` / ``k``
    are), and there is no heap, no aliasing, no ``Old``, and no permission
    system. There is no read-only input to overwrite and no frame clause to
    violate. Fabricating a substitute would test nothing, so the class is
    reported absent rather than ported.
  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason the sibling gives: C1 pins
    ``out`` to a transparent function of the method's own arguments, with no
    opaque leaf in the whole file, so there is no value an echo could carry that
    satisfies C1 yet is wrong. The honest control is the cheapest faithful impl
    (``pos-control-direct-render``), not a wrong echo.
  * CONTROL-FLOW-EFFECT — N/A, exactly as on the sibling. The modeled behaviour
    is a single straight-line value render with no raise / early-return /
    side-effect fork, and C1 is a total value identity, so there is no effect
    invisible to the value abstraction for a rival to hide in.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane, and this is where the
    sibling's reasoning transfers most directly: a rival can be right on short
    numerals yet wrong exactly on the long-precision sub-domain the failing test
    pins.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``k``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own ``decreasing_1`` goal,
    re-measured on this bundle with a real build. Divergence therefore does not
    discharge the ``ensures`` clauses vacuously. It is still not shipped as a
    G-PBT reject case, and the reason is the witness contract rather than a
    spec weakness. A reject case must carry a witness that ELABORATES against
    the rival, and the rival's module does not compile at all: the descent
    obligation fails at the ``method`` itself, ahead of any appended tester.
    That is the shape with NO measure. A rival that CARRIES a measure which
    does not decrease is refused at the ``prove_correct`` site instead, which
    the witness file strips, so that module does elaborate; but its post-image
    is then an unreduced ``forIn Lean.Loop.mk`` term carrying
    ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
    kernel will not normalise to a value a concrete-input tester can decide.
    Both shapes therefore land ``witness-unproven``.
    Measured through the gate's own ``_check_witness``, even
    ``example : True := trivial`` comes back ``witness-unproven`` on this
    rival, which is an INCONCLUSIVE outcome and would fail the whole battery
    rather than pass a case. That is the right behavior: a diverging impl has
    no output at any input, so there is no value for a witness to disagree
    with, and its rejection is a judgement of the termination obligation rather
    than a postcondition violation at a point. Recorded as REJECTED-BY-SPEC and
    not expressible as a witnessed case, which is neither a spec hole nor a
    battery gap.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle is axiom-free (mapping.md
§3: no ``axiom`` declarations and no ``:|`` callee stubs — the changed behaviour
is modeled deeply by ``renderFixed`` and checked end-to-end by G-CONF rather than
assumed), so the sibling's two A-reference probes over the real stdlib callees
have no consumed axiom to probe here; that lane is G-AX's job and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15863"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl body: everything strictly BETWEEN the method's
# ---- `-- impl-start` / `-- impl-end`. A single anchor lying wholly inside the
# ---- impl region and unique in the file (both facts asserted at load), so every
# ---- variant's edit is guaranteed to leave the spec view untouched.
_IMPL = """    let mut digits : List Char := fracDigits
    let mut k : Nat := p - fracDigits.length
    while k > 0
      invariant k ≤ p - fracDigits.length
      invariant digits = fracDigits ++ List.replicate (p - fracDigits.length - k) '0'
      done_with k = 0
      decreasing k
    do
      digits := digits ++ ['0']
      k := k - 1
    return intDigits ++ ['.'] ++ digits"""
assert _BASE.count(_IMPL) == 1, "impl-region anchor drift — re-sync _IMPL"

# ---- The frozen loop-body lines, wholly inside the impl region and unique. The
# ---- loop-PRESERVING positive reshapes only these, leaving the loop, both
# ---- invariants and the frozen proof script intact.
_LOOP_BODY = "      digits := digits ++ ['0']\n      k := k - 1"
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift — re-sync _LOOP_BODY"

# ---- The frozen proof body (tactic script only; elided from the spec view). A
# ---- variant that reshapes the impl into a loop-free expression retunes THIS
# ---- block without touching the spec or dropping the `prove_correct floatFormat`
# ---- obligation, whose header and statement are byte-identical throughout.
_PROOF = """prove_correct floatFormat by
  loom_solve
  · rw [invariant_2]
    rw [pad_tail_step fracDigits (p - fracDigits.length) k (by omega) (by omega)]
  · simp_all [renderFixed]"""
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"

# ---- The tactic body for a LOOP-FREE impl. With no loop there is no invariant to
# ---- peel, so the residual goal is the render identity itself. This body is
# ---- MEASURED to close for the loop-free CORRECT render (that is
# ---- `pos-control-direct-render`, exit 0), which is what makes every reject
# ---- rival's failure under the same body attributable to its RENDER rather than
# ---- to a script tuned to a loop it no longer has.
_PROOF_FLAT = """prove_correct floatFormat by
  loom_solve
  simp_all [renderFixed]"""


def _flat(expr):
    """A loop-free variant: return `expr` in one step, under `_PROOF_FLAT`.

    Loop-freeness is what makes the variant's extracted tester REDUCE under
    `decide`, so its witness can be checked at all (see the CARRIER NOTE). It is
    NOT what any rival is rejected for: the same shape with the CORRECT render
    verifies and is shipped as `pos-control-direct-render`.
    """
    return _swap(_swap(_BASE, _IMPL, f"    return {expr}"), _PROOF, _PROOF_FLAT)


# ---- The CORRECT render written loop-free: the post-image C1 demands, spelled
# ---- out over the method's own three arguments.
_RENDER_CORRECT = ("intDigits ++ ['.'] ++ fracDigits "
                   "++ List.replicate (p - fracDigits.length) '0'")

# ---- THE WITNESS REFERENCE, and a positive control in its own right. The FROZEN
# ---- impl cannot serve as the witnesses' second subject on this bundle: its
# ---- `while` pad loop elaborates through `Classical.choice`, so `decide` on the
# ---- frozen tester is STUCK for every claim regardless of truth (measured: "did
# ---- not reduce to `isTrue` or `isFalse`") and its exit code discriminates
# ---- nothing. Refuting each witness against THIS impl instead is a real
# ---- discrimination: it shares the frozen spec, it VERIFIES, and an impl the
# ---- verifier accepts cannot violate its own spec — so a witness that fails here
# ---- fails on the spec's content.
_REFERENCE = _flat(_RENDER_CORRECT)


# ---- Witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `floatFormatTester i f p = false` says the extracted program's result
# ---- violates the method's postcondition (C1) at that concrete input. Checked in
# ---- a file whose `prove_correct` block is stripped. Every point below satisfies
# ---- all five `require` clauses, so the tester's precondition guard does not
# ---- short it to a vacuous `true` — a witness at an out-of-regime input would
# ---- say nothing, since the precondition would excuse the rival.
def _witness(int_digits, frac_digits, p):
    return ("\n"
            "extract_program_for floatFormat\n"
            "prove_precondition_decidable_for floatFormat\n"
            "prove_postcondition_decidable_for floatFormat\n"
            "derive_tester_for floatFormat\n\n"
            f"example : floatFormatTester {int_digits} {frac_digits} {p} = false := by\n"
            "  decide\n")


# ---- The exact failing-test numeral, as its two digit runs: a 6-digit integer
# ---- run and a 21-digit fractional run, rendered to 21 places. This is the
# ---- long-precision point the issue is about, and the point at which a numeral
# ---- that has been round-tripped through a lower-precision carrier loses its
# ---- low-order fractional digits.
_F2P_INT = "['1','2','3','4','5','6']"
_F2P_FRAC = ("['1','2','3','4','5','6','7','8','9','0','1','2','3','4','5','6',"
             "'7','8','9','0','1']")
_F2P_P = "21"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl is rejected, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen code shape).
    # =====================================================================
    {
        "id": "pos-control-direct-render",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest correct impl: compute the whole render in one
        # expression, no pad loop at all — maximally structurally different from
        # the frozen backward pad loop. Also this battery's INTERPRETIVE CONTROL,
        # on two counts measured out-of-band: (a) it verifies under `_PROOF_FLAT`,
        # the body every loop-free rival carries, so a rival's failure is its
        # render's and not the script's; (b) its extracted tester REDUCES, so it
        # is the `witness_reference` every reject case names — the subject against
        # which each witness was actually SEEN to be refuted.
        "module": _REFERENCE,
        "rationale": (
            "C1 is literally `out = renderFixed intDigits fracDigits p`, and "
            "`renderFixed` is a transparent `def` over the method's own three "
            "arguments, so spelling that render out in one expression is the "
            "cheapest HONEST correct impl and MUST verify — else C1 is "
            "SPEC-TOO-STRONG (over-fit to the pad-loop code shape). It doubles as "
            "the no-ungrounded-echo control: the post-image is grounded in the "
            "inputs rather than in an opaque answer key, so a correct impl must do "
            "the real work and any WRONG render fails C1 (the seven rivals below "
            "are exactly that, in this same shape). It is ALSO the battery's "
            "interpretive control: it verifies under the same two-line tactic body "
            "every loop-free rival carries (so each rejection is attributable to "
            "the rival's render, and the residual goal names it), and its extracted "
            "tester reduces (so it serves as the `witness_reference` against which "
            "every witness was measured to be refuted). Ports/merges the sibling "
            "pos-local-reshape into the maximally-different correct shape."),
    },
    {
        "id": "pos-control-staged-pad",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole pad loop, both invariants, the `done_with`, and the
        # frozen proof script; only stages the appended pad character in a typed
        # local before appending it. Observationally identical at every input —
        # the sibling's pos-local-reshape (a fresh named local used uniformly in
        # the loop body) on this carrier.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let z : List Char := ['0']\n"
            "      digits := digits ++ z\n"
            "      k := k - 1"),
        "rationale": (
            "staging the appended pad character in a typed local before appending "
            "it pads the same run by the same step, so C1 still holds on the whole "
            "in-regime domain; the loop, both invariants and the frozen proof "
            "script are untouched. A correct reshape must verify, else the spec is "
            "SPEC-TOO-STRONG (rejects a faithful impl over the shape of the loop "
            "body). Ports the sibling pos-local-reshape, which likewise keeps the "
            "gold loop direction and every proof obligation and only introduces a "
            "fresh named local used uniformly in the body."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The sibling asserts that a normal digit list
    # satisfies its read-only fractional-permission precondition; there is no
    # permission surface here. But this method's precondition is NOT empty (P1–P5
    # are a real regime envelope), so the probe is not degenerate either: the
    # residual risk is an envelope so tight, or a post-image so degenerate, that
    # the modeled behaviour is never actually exercised. The in-region assert is
    # LIVE (it must discharge for the case to pass) and the surrounding impl is
    # kept VERBATIM so the method's own obligation still discharges on its own
    # terms; only the tactic body gains an arm for the assert goal.
    # =====================================================================
    {
        "id": "admiss-regime-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    assert (with_name_prefix `admiss (\n"
                  "      renderFixed ['1','2'] ['3','4'] 4 "
                  "= ['1','2','.','3','4','0','0'] ∧\n"
                  "      renderFixed ['1','2'] ['3','4'] 2 ≠ ['1','2','.','0','0'] ∧\n"
                  "      renderFixed ['9'] [] 1 = ['9','.','0']))\n"
                  + _IMPL),
            _PROOF,
            "prove_correct floatFormat by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [invariant_2]\n"
            "       rw [pad_tail_step fracDigits (p - fracDigits.length) k "
            "(by omega) (by omega)])\n"
            "    | simp_all [renderFixed]"),
        "rationale": (
            "the regime envelope (P1–P5) must ADMIT the numerals the modeled "
            "behaviour is about, and the post-image must be NON-DEGENERATE on "
            "them. The in-region assert pins three facts at concrete in-regime "
            "inputs: asking for MORE places than the numeral carries genuinely "
            "right-extends the fractional run with trailing zeros; the numeral's "
            "own fractional digits are NOT replaced by that padding (the "
            "load-bearing precision commitment, stated as a DISEQUALITY so a "
            "degenerate all-zeros post-image could not satisfy it); and an EMPTY "
            "fractional run is in-regime and renders with a full pad run. The impl "
            "is kept verbatim so `out = renderFixed intDigits fracDigits p` still "
            "verifies on its own terms. If this fails => PRECOND-TOO-STRONG (the "
            "envelope excludes a legitimate numeral) or the obligation is "
            "degenerate. Re-aims the sibling admiss-reads, whose "
            "fractional-permission half has no counterpart on this "
            "referentially-transparent carrier."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is LOOP-FREE so
    # its extracted tester `decide`s (see the CARRIER NOTE) and each carries
    # `_PROOF_FLAT`, the body that CLOSES for the correct render of this same
    # shape — so the rejection is the render's, not the script's.
    #
    # Failing-test scenario grounding the refinements: a numeral with 27
    # significant digits (a 6-digit integer run and a 21-digit fractional run) is
    # rendered to 21 fractional places, and the test asserts every one of those
    # digits comes back verbatim.
    # =====================================================================
    {
        "id": "weak-truncate-precision-budget",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG, on this carrier. Keep the leading 17 fractional digits and
        # replace every later one with a pad zero — exactly what a numeral routed
        # through a lower-precision binary carrier before its fractional run is
        # read back produces, since that carrier holds only ~17 significant
        # digits. PARTIAL-DOMAIN: byte-identical to gold on every numeral with at
        # most 17 fractional digits (there `take 17` is the identity and `min 17
        # len` is `len`), wrong precisely on the long-precision sub-domain the
        # failing test pins. The output WIDTH is still right, so only the
        # verbatim-digits commitment refutes it.
        "module": _flat("intDigits ++ ['.'] ++ fracDigits.take 17 "
                        "++ List.replicate (p - min 17 fracDigits.length) '0'"),
        "refinement": (
            "this IS the pre-change behaviour: the numeral is routed through a "
            "lower-precision carrier before its fractional run is read back, and "
            "that carrier holds only about 17 significant digits, so every "
            "fractional position past the budget comes back as a padding artefact "
            "rather than the numeral's own digit. Its faithful real counterpart is "
            "the UNCHANGED repo. The failing test renders a numeral with 21 "
            "fractional digits to 21 places and asserts the full digit string comes "
            "back; under this behaviour the positions past the 17th are zeros "
            "instead, so it does NOT resolve. It is exactly the defect the change "
            "corrects, and the precise divergence the spec must sense (G-DIFF)."),
        "rationale": (
            "REJECT from C1 (`out = renderFixed intDigits fracDigits p`), "
            "commitment (c): `renderFixed` reproduces `fracDigits` VERBATIM at "
            "full length, so a rival that keeps only a leading budget of it and "
            "pads the rest diverges wherever the fractional run is longer than the "
            "budget. Refuted at the EXACT failing-test point — a 6-digit integer "
            "run, a 21-digit fractional run, `p = 21` — the only witness in the "
            "battery on the long-precision sub-domain, and the one that drives "
            "`fracDigits.length` and `p` to their extreme (21, versus 0–2 "
            "elsewhere). Verifying would be SPEC-TOO-WEAK: precision past the "
            "budget would not be pinned, which is the whole point of the change. "
            "Ports the sibling weak-truncate-budget."),
        "witness": _witness(_F2P_INT, _F2P_FRAC, _F2P_P),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-last-fractional-digit",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN one-element miss: drop the LAST fractional digit and pad
        # one place further, so the output has the right WIDTH but its final
        # fractional position is a zero instead of the numeral's own digit.
        # Correct only when the fractional run is empty. Sharper than the budget
        # rival on the short sub-domain: it agrees with gold on nothing non-empty,
        # and it diverges at a SHORT numeral where the budget rival agrees with
        # gold exactly — so the two cannot share a witness.
        "module": _flat("intDigits ++ ['.'] ++ fracDigits.dropLast "
                        "++ List.replicate (p - fracDigits.length + 1) '0'"),
        "refinement": (
            "corresponds to a reconstruction that loses one digit of precision — "
            "an off-by-one in the parse of the numeral's canonical decimal string "
            "— and then makes the width up with an extra padding zero. Every "
            "non-empty numeral renders one digit short of itself, including the "
            "failing test's, which would lose its trailing digit while still coming "
            "back at the right width; the test asserts the full digit string, so it "
            "does NOT resolve. Correct only on a numeral with no fractional part at "
            "all."),
        "rationale": (
            "REJECT from C1, commitment (c) ALONE: the output width still matches "
            "(one digit dropped, one pad zero added), so this rival is refutable "
            "only by the VERBATIM-digits half of the render and not by any length "
            "or shape argument — which is what makes it a sharper probe of that "
            "commitment than the budget rival. Refuted at a SHORT numeral (a "
            "2-digit integer run, a 2-digit fractional run, `p = 3`), a point in "
            "the sub-domain where weak-truncate-precision-budget agrees with gold "
            "EXACTLY, so the two rivals cannot share a witness and neither claims "
            "the other's sub-domain. If it verified => SPEC-TOO-WEAK. Ports the "
            "sibling weak-drop-last."),
        "witness": _witness("['4','2']", "['1','3']", "3"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-fractional-digits",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the numeral's fractional run ENTIRELY: emit the integer run, the
        # point, and `p` padding zeros. Correct only on a numeral with no
        # fractional part. This is the pre-patch skeleton's modeled regime (the
        # fractional content lost wholesale to padding), and the cheap supporting
        # near-miss for the precision commitment.
        "module": _flat("intDigits ++ ['.'] ++ List.replicate p '0'"),
        "refinement": (
            "corresponds to a reconstruction whose fractional content is lost "
            "wholesale — every fractional position comes back as padding rather "
            "than the numeral's own digit, so the rendered value reads as the "
            "integer part with an all-zero fraction for EVERY numeral that has "
            "one. It fails the failing test's assertion (and every other "
            "already-passing case with a fractional part), so it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from C1, commitment (c): `renderFixed` places `fracDigits` "
            "ahead of the pad run, and this rival emits pad zeros in their place, "
            "so it diverges on every numeral with a non-empty fractional run. "
            "Refuted at a minimal in-regime numeral (a 1-digit integer run, a "
            "1-digit fractional run, `p = 2`) — the cheapest point in the battery, "
            "and distinct from the other two precision rivals in both run lengths "
            "and `p`. If it verified => SPEC-TOO-WEAK (the fractional content "
            "would not be pinned to the input at all). Ports the sibling "
            "weak-empty (return none of the input's own digits), re-expressed "
            "against the fractional run — the part this carrier models. A bare "
            "empty return would be refutable by output LENGTH alone, which is a "
            "strictly weaker probe, so the attack is re-sited rather than "
            "transcribed."),
        "witness": _witness("['9']", "['5']", "2"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-clip-integer-run",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling counterpart — the sibling's carrier is a single digit
        # sequence with no integer/fractional split). Attacks commitment (a): emit
        # only the FIRST integer digit ahead of the point, dropping the rest.
        # Correct on every single-integer-digit numeral; wrong on every longer
        # one. Without it, `intDigits` would be pinned by no rival at all, so a
        # rival that mishandled only the integer run would verify unnoticed.
        "module": _flat("intDigits.take 1 ++ ['.'] ++ fracDigits "
                        "++ List.replicate (p - fracDigits.length) '0'"),
        "refinement": (
            "corresponds to a render that emits only the leading integer digit "
            "ahead of the separator — a truncation of the integer run rather than "
            "of the fraction. Every numeral whose integer part has more than one "
            "digit renders as a different number entirely; the failing test's "
            "numeral has a 6-digit integer part, so it does NOT resolve, and "
            "neither would any already-passing case on a multi-digit integer "
            "part."),
        "rationale": (
            "REJECT from C1, commitment (a): `renderFixed` emits `intDigits` "
            "verbatim and in full ahead of the point, so clipping it diverges "
            "whenever the integer run is longer than one digit. Refuted at a "
            "3-digit integer run with an EMPTY fractional run and `p = 1` — the "
            "only witness in the battery that drives `fracDigits` to `[]` and `p` "
            "to its minimum, so it is what moves those two binders off the values "
            "every other witness holds them near. Added because the three ported "
            "precision rivals all attack the fractional run and leave `intDigits` "
            "entirely unattacked: without this case a spec that pinned only the "
            "fraction would pass the whole battery. If it verified => "
            "SPEC-TOO-WEAK (the integer run unconstrained)."),
        "witness": _witness("['1','2','3']", "[]", "1"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-omit-trailing-pad",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling counterpart — the sibling's carrier has no requested
        # WIDTH, so the pad commitment does not exist there). Attacks commitment
        # (d): reproduce both digit runs verbatim but never pad, so the rendered
        # fraction is short of the requested width. Every one of the numeral's own
        # digits survives — this rival is the exact COMPLEMENT of the precision
        # rivals — and it is correct precisely on the boundary
        # `p = fracDigits.length`, where the pad run is empty.
        "module": _flat("intDigits ++ ['.'] ++ fracDigits"),
        "refinement": (
            "corresponds to a render that reproduces the numeral faithfully but "
            "never extends the fraction to the requested width — the zero-pad step "
            "is skipped. Asking for more places than the numeral carries then "
            "returns a shorter string than requested, whereas the contract is to "
            "render to exactly the requested number of places; the already-passing "
            "cases that request more places than their value carries would come "
            "back short, so it does NOT resolve. Correct exactly when the requested "
            "width equals the numeral's own fractional length."),
        "rationale": (
            "REJECT from C1, commitment (d) ALONE: `renderFixed` right-extends the "
            "fractional run with `p - fracDigits.length` trailing zeros, and this "
            "rival emits none. It is the exact COMPLEMENT of the three precision "
            "rivals — every digit of the input survives, so the verbatim-digits "
            "commitment is honoured and only the pad width refutes it — which is "
            "why it cannot share their witnesses. Refuted at a 1-digit integer "
            "run, a 2-digit fractional run and `p = 4` (a pad gap of two; the "
            "precision rivals sit at gaps of 0 or 1). Added because the pad "
            "commitment has no counterpart on the sibling's carrier (which has no "
            "requested width) yet is an independent half of this bundle's "
            "post-image. If it verified => SPEC-TOO-WEAK (the requested width "
            "unconstrained)."),
        "witness": _witness("['8']", "['0','7']", "4"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-reversed-fractional-run",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT of the coverage above. ORDER. Every digit of the numeral
        # is present, the counts are right, the pad width is right — only the
        # fractional run's ORDER is wrong. The five rivals above all diverge by
        # dropping, substituting or failing to add a digit, so C1's ordering
        # content was attacked by nothing: a rival emitting the right MULTISET of
        # digits at the right width would have passed the whole battery. Correct on
        # every numeral whose fractional run is a palindrome (including empty and
        # single-digit ones), so it is a genuine partial-domain break.
        "module": _flat("intDigits ++ ['.'] ++ fracDigits.reverse "
                        "++ List.replicate (p - fracDigits.length) '0'"),
        "refinement": (
            "corresponds to a render that walks the numeral's fractional digits in "
            "the opposite order — each digit is emitted, and the width is right, "
            "but the value rendered is a different number. The failing test asserts "
            "the exact digit string back; a reversed fraction is a different string "
            "for any non-palindromic fraction, including the test's, so it does NOT "
            "resolve. A pure ORDER break: no digit is dropped, substituted or "
            "invented."),
        "rationale": (
            "REJECT from C1, commitment (c)'s ORDER half ALONE: `renderFixed` "
            "reproduces `fracDigits` IN ORDER, and this rival returns the reversal "
            "— the same digits, the same count, the same pad width. It is the only "
            "rival whose output is a string gold produces at some OTHER input, so "
            "nothing but the order distinguishes it and no length or multiset "
            "argument refutes it. Refuted at a 1-digit integer run, the fractional "
            "run `['1','2']` and `p = 2` — the boundary `p = fracDigits.length` "
            "where the pad run is EMPTY, a point no other witness occupies. Added "
            "by audit: the five rivals above all diverge by a dropped, substituted "
            "or missing digit, leaving the ordering content of C1 unattacked. If it "
            "verified => SPEC-TOO-WEAK (digit order unconstrained)."),
        "witness": _witness("['6']", "['1','2']", "2"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Attacks commitment (b), the only structural piece of the
        # post-image no other rival touches: emit a different separator between
        # the two digit runs. Both digit runs and the pad are verbatim; only the
        # one character between them differs. Wrong on the WHOLE domain (there is
        # no in-regime input at which it agrees with gold — its residual proof goal
        # is `⊢ False`), so it is the battery's blunt control on that commitment
        # rather than a partial-domain probe. Recorded as such, not dressed up.
        "module": _flat("intDigits ++ [','] ++ fracDigits "
                        "++ List.replicate (p - fracDigits.length) '0'"),
        "refinement": (
            "corresponds to a render that separates the integer and fractional "
            "runs with a character other than the decimal point — the divergence a "
            "locale-formatting step introduces when applied where the contract "
            "expects the unlocalized form. Every rendered value then carries the "
            "wrong separator; the failing test asserts a string with a decimal "
            "point, and so do the already-passing cases, so it does NOT resolve."),
        "rationale": (
            "REJECT from C1, commitment (b): `renderFixed` places exactly one "
            "decimal point between the integer run and the fractional run, and "
            "this rival emits a different character there. Both digit runs and the "
            "pad are untouched, so the separator is the sole divergence — and it is "
            "the only structural commitment of the post-image that no other rival "
            "attacks. Blunt rather than partial-domain: the residual proof goal is "
            "`⊢ False`, i.e. the two renders cannot be equal at ANY in-regime "
            "input, which is stated here rather than claimed as a sub-domain the "
            "manifest does not demonstrate. Refuted at a 2-digit integer run, a "
            "1-digit fractional run and `p = 5`, a seventh distinct point (and the "
            "widest pad gap, four). Added by audit; without it the separator is "
            "pinned by no rival. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness("['3','0']", "['9']", "5"),
        "witness_reference": _REFERENCE,
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery ships 6 SPEC cases (1 soundness, 1 admissibility, 4
# uniqueness — one of which is the MANDATORY frame-mutation rival) plus an AXIOM
# lane of 2 probes. It contracts `reconstruct_digits(text: List[int])` over ONE
# read-only half-permission digit column, returning the reconstructed column,
# with the load-bearing clause `ToSeq(Result()) == ToSeq(text)` — the exact
# identity on the numeral's significant-digit sequence.
#
# This backend models the SAME behaviour at a DIFFERENT granularity, and the
# accounting below turns on that difference. The sibling's carrier is the
# numeral's significant-digit sequence as one column; here the numeral is split
# into its integer-digit run and its fractional-digit run, a requested WIDTH `p`
# is an input, and the post-image is the rendered character sequence — so the
# sibling's single identity clause becomes FOUR independent structural
# commitments (the integer run verbatim; the separator; the fractional run
# verbatim and in order; the pad to width `p`). Two of those have no sibling
# counterpart at all, which is where the ADDED cases come from — carrier
# WIDENING here, not the usual narrowing.
#
#   sibling case            kind          -> here                            disposition
#   ---------------------------------------------------------------------------------------
#   pos-local-reshape       soundness     -> pos-control-staged-pad          PORTED
#                                         + pos-control-direct-render        (also: no-echo
#                                                                             + interpretive
#                                                                             control)
#   admiss-reads            admissibility -> admiss-regime-nondegenerate     RE-AIMED
#   frame-mut-write         uniqueness    -> (none)                          VACUOUS
#   weak-truncate-budget    uniqueness    -> weak-truncate-precision-budget  PORTED
#   weak-drop-last          uniqueness    -> weak-drop-last-fractional-digit PORTED
#   weak-empty              uniqueness    -> weak-drop-fractional-digits     RE-EXPRESSED
#   (no sibling)            uniqueness    -> weak-clip-integer-run           ADDED
#   (no sibling)            uniqueness    -> weak-omit-trailing-pad          ADDED
#   (no sibling)            uniqueness    -> weak-reversed-fractional-run    ADDED (audit)
#   (no sibling)            uniqueness    -> weak-wrong-separator            ADDED (audit)
#   AXIOM_TESTS (2)         axiom         -> (none)                          DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 2 soundness, 1 admissibility, 7 uniqueness. NOTHING was
# omitted for being hard to prove: both positives verify (measured), and no
# soundness case was dropped because its proof would not close.
#
# PORTED (pos-local-reshape -> pos-control-staged-pad): the sibling reshapes the
#   gold loop body through a fresh named local used uniformly, keeping the loop
#   direction, every invariant and every framing obligation. The direct analogue
#   here stages the appended pad character in a typed local, keeping the pad loop,
#   both invariants and the frozen proof script intact. pos-control-direct-render
#   is carried ALONGSIDE rather than instead: it is the maximally-different
#   correct shape (no loop at all), it is the honest no-echo control the sibling
#   argues for in its UNGROUNDED-ORACLE-ECHO note, and it is load-bearing
#   MACHINERY for this battery (the `witness_reference` and the proof-shape
#   control — see the CARRIER NOTE).
# RE-AIMED (admiss-reads -> admiss-regime-nondegenerate): the sibling asserts,
#   under its half-permission, that the length and elements of a normal digit list
#   are readable. There is no permission surface here, but unlike most ports this
#   method's precondition is NOT empty — P1–P5 are a real regime envelope — so the
#   case is re-aimed rather than declared degenerate: it asserts, in-region, that
#   the envelope admits the numerals the behaviour is about and that the render is
#   non-degenerate on them (padding happens; the numeral's own digits are NOT
#   replaced by padding, stated as a disequality; an empty fractional run is
#   in-regime).
# PORTED (weak-truncate-budget, weak-drop-last): both carry across intact, with
#   their sibling refinement arguments unchanged — the ~17-significant-digit
#   budget truncation (the literal pre-change behaviour, its faithful counterpart
#   being the unchanged repo) and the one-digit-short reconstruction. Only the
#   carrier changes, from a digit column to the fractional-digit run of a rendered
#   numeral. The budget rival is now refuted at the EXACT failing-test numeral,
#   and the drop-last rival was re-shaped to pad one place further so its output
#   width still matches — otherwise it would be refutable by length alone, a
#   weaker probe than the sibling's, which attacks the digit identity.
# RE-EXPRESSED (weak-empty -> weak-drop-fractional-digits): the sibling returns
#   the empty sequence, i.e. NONE of the input's own digits. The structural
#   analogue here is not an empty output — C1 pins the output's WIDTH as well, so
#   an empty return is refutable by length alone — but a render that keeps none of
#   the numeral's own FRACTIONAL digits and fills the width with padding. Same
#   attack (the result is not pinned to the input's digits at all), expressed
#   against the run this carrier models, and it is also the regime the pre-patch
#   skeleton models.
# ADDED (weak-clip-integer-run, weak-omit-trailing-pad): these attack the two
#   commitments of C1 that have NO sibling counterpart, because the sibling's
#   carrier does not contain them. Its digit column has no integer/fractional
#   split (so the integer run is unattackable there) and no requested WIDTH (so
#   the pad commitment does not exist there). Both are independent halves of this
#   bundle's post-image, and both would otherwise be pinned by no rival: the three
#   ported rivals all attack the fractional run, so a spec constraining only the
#   fraction, or only the digits and not the width, would have passed the entire
#   battery. weak-omit-trailing-pad is the exact COMPLEMENT of the precision
#   rivals (every input digit survives; only the width is wrong).
# ADDED BY AUDIT (weak-reversed-fractional-run, weak-wrong-separator): the six
#   cases above all diverge by a dropped, substituted, clipped or missing digit,
#   so two of C1's commitments were still unattacked and the coverage claim would
#   have overstated the battery:
#   (1) ORDER. A rival emitting the right MULTISET of digits at the right width
#       would have passed everything. weak-reversed-fractional-run returns the
#       fractional run reversed — same digits, same count, same pad — so it is
#       refutable by no length or multiset argument, and it is correct on every
#       palindromic fraction, making it a genuine partial-domain probe.
#   (2) THE SEPARATOR. weak-wrong-separator emits a different character between
#       the two runs, with both runs and the pad verbatim. It is wrong on the whole
#       domain (residual goal `⊢ False`), so it is a blunt control rather than a
#       partial-domain probe — recorded as such, not dressed up.
# VACUOUS (frame-mut-write): the sibling's MANDATORY frame-mutation rival keeps
#   the gold body verbatim and adds a no-op STORE back into the read-only input,
#   which must be rejected for INSUFFICIENT PERMISSION; the sibling calls this the
#   project's #1 weakness class, on the grounds that a byte-fuzzer never thinks to
#   mutate the input. It has no analogue on this carrier. Velvet and Lean are
#   referentially transparent: all three inputs are immutable values, no parameter
#   is declared `mut` (only the loop-locals `digits`/`k` are), and there is no
#   heap, no aliasing, no `Old`, and no permission system — there is nothing to
#   overwrite and no frame clause to violate. The nearest expressible analogue is
#   assigning to a parameter inside the impl region, which the carrier refuses at
#   ELABORATION rather than at the postcondition ("cannot be mutated, only
#   variables declared using `let mut` can be mutated"), so a ported rival would
#   reject for a binder reason with NO spec content and there would be nothing for
#   a witness to state. NOT ported, and no substitute fabricated.
# DROPPED (AXIOM_TESTS, 2): the sibling's axiom-soundness and containment probes
#   drive the real stdlib callees. This bundle is axiom-free (mapping.md §3: no
#   `axiom`, no `:|` stub; the changed behaviour is modeled deeply by `renderFixed`
#   and validated end-to-end by G-CONF rather than assumed), so there is no
#   consumed axiom for this lane to probe; and the G-PBT gate ignores AXIOM_TESTS
#   regardless.
#
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``k``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own ``decreasing_1`` goal,
#   re-measured on this bundle with a real build. Divergence therefore does not
#   discharge the ``ensures`` clauses vacuously. It is still not shipped as a
#   G-PBT reject case, and the reason is the witness contract rather than a
#   spec weakness. A reject case must carry a witness that ELABORATES against
#   the rival, and the rival's module does not compile at all: the descent
#   obligation fails at the ``method`` itself, ahead of any appended tester.
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   Measured through the gate's own ``_check_witness``, even
#   ``example : True := trivial`` comes back ``witness-unproven`` on this
#   rival, which is an INCONCLUSIVE outcome and would fail the whole battery
#   rather than pass a case. That is the right behavior: a diverging impl has
#   no output at any input, so there is no value for a witness to disagree
#   with, and its rejection is a judgement of the termination obligation rather
#   than a postcondition violation at a point. Recorded as REJECTED-BY-SPEC and
#   not expressible as a witnessed case, which is neither a spec hole nor a
#   battery gap.
#
# CLAUSE / BINDER / POINT COVERAGE. ONE `ensures` clause (C1, `out = renderFixed
#   intDigits fracDigits p`), which is a conjunction of four independent
#   structural commitments. C1 is DEFENDED by both positives and the admissibility
#   case, and EVERY commitment is ATTACKED:
#     (a) integer run verbatim         -> weak-clip-integer-run
#     (b) the separator                -> weak-wrong-separator
#     (c) fractional run verbatim      -> weak-truncate-precision-budget,
#                                         weak-drop-last-fractional-digit,
#                                         weak-drop-fractional-digits
#         ...and its ORDER half        -> weak-reversed-fractional-run
#     (d) pad to the requested width   -> weak-omit-trailing-pad
#   The five `require` clauses are exercised by the admissibility case and by the
#   witness points, every one of which is in-regime (`1 ≤ p`, `fracDigits.length ≤
#   p`, `intDigits ≠ []`, all digit chars) — a witness at an out-of-regime input
#   would say nothing, since the precondition would excuse the rival.
#   All THREE binders are moved across SEVEN distinct input points (pts = 7):
#     * weak-truncate-precision-budget   int len 6  frac len 21  p 21  (the F2P point)
#     * weak-drop-last-fractional-digit  int len 2  frac len 2   p 3
#     * weak-drop-fractional-digits      int len 1  frac len 1   p 2
#     * weak-clip-integer-run            int len 3  frac len 0   p 1
#     * weak-omit-trailing-pad           int len 1  frac len 2   p 4
#     * weak-reversed-fractional-run     int len 1  frac len 2   p 2
#     * weak-wrong-separator             int len 2  frac len 1   p 5
#   So `intDigits` ranges over lengths {1,2,3,6}; `fracDigits` over lengths
#   {0,1,2,21} — INCLUDING the empty run and the 21-digit long-precision run; `p`
#   over {1,2,3,4,5,21} — including its minimum. The pad gap `p -
#   fracDigits.length` ranges over {0,1,2,4} — including 0, the boundary where the
#   pad run is EMPTY (weak-reversed-fractional-run). No two witnesses share a
#   digit string, and no binder is pinned at a single value across the reject set.
#   MEANINGFULNESS (not just distinctness): at each of the seven points a CORRECT
#   render differs from the rival's output, measured value-for-value by `decide`
#   against the reference impl — for all seven, `decide` proved the witness
#   proposition FALSE there (exit 1). No two points are two spellings of the same
#   discrimination: they split by which commitment is violated, by whether the
#   fractional run is empty / short / long, and by whether the pad run is empty,
#   narrow or wide.
#
# WITNESS MECHANICS: the post-image is fully TRANSPARENT (`renderFixed` is a
#   concrete `def`; the axioms region is empty and declares no opaque leaf), so
#   the tester + `decide` path is LIVE and every witness states its refutation at
#   concrete literals with NO bound hypothesis — hence no consistency probe is
#   needed and no witness can be a forgery from contradictory assumptions.
#   The FROZEN impl, however, cannot serve as the witnesses' second subject: its
#   `while` pad loop under `demonic` choice elaborates through `Classical.choice`,
#   so `decide` on the frozen tester is STUCK for every claim regardless of truth
#   ("did not reduce to `isTrue` or `isFalse`" — measured for every witness here),
#   and its exit code carries no information. Every reject case therefore names
#   pos-control-direct-render as its `witness_reference`: it shares the frozen
#   spec, it VERIFIES, and its tester REDUCES, so `decide` refutes each witness
#   there SEMANTICALLY. Measured with scripts/lean_verify.sh for all seven — rival
#   exit 0; reference exit 1 with "`decide` proved that the proposition ... is
#   false"; frozen exit 1 with a stuck reduction. The reference is also shipped as
#   an `expect="verify"` case, so the battery itself records that loop-freeness is
#   not what any rival is being rejected for.
AXIOM_TESTS = []
