"""properties.py — G-PBT falsification battery for pydata__xarray-6744 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region of one method, or inside that method's ``prove_correct``
tactic body — both of which the consumer spec view elides, so
``markers.same_spec`` holds and every ``prove_correct`` obligation survives with
a byte-identical statement) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: it elaborates against the rival and FAILS
against the discrimination subject — the frozen solution, or the case's
``witness_reference`` where the frozen impl cannot decide anything; see WITNESS
MECHANICS below, which on this cell is the load-bearing part).

DEFENDED SURFACE (two contracted methods over the binders n, w, center):

  blockEnds  (n : Nat) (w : Int) (center : Bool) return (out : List Int)
    require w > 0
    ensures out = endsSeq w center (positions n)

  blockBegins (n : Nat) (w : Int) (center : Bool) return (out : List Int)
    require w > 0
    ensures out = beginsSeq w center (positions n)

Both model the per-position index ranges of a one-dimensional moving-window
traversal. ``positions n`` is the labels 0..n-1; ``endsSeq``/``beginsSeq`` are
total, fully-unfolded pure folds (the ``axioms`` region is EMPTY, so there is no
opaque answer key to echo). Each element is pinned to a closed form:
  endAt i   = i + endShift w center,  endShift w center = (w+1)/2 if center else 1
  beginAt i = max(0, endAt i - w)   (the leading clamp).

The DISCRIMINATING content the port must defend is the ``center``-dependence of
``endShift``: a centred window shifts every block end forward by ceil(w/2), an
uncentred window by 1; the two coincide only at w = 1. The begins side
additionally defends the leading clamp ``max(0, .)``. The single load-bearing
``ensures`` on each method pins EVERY position independently, which is what makes
the partial-domain rivals below refutable at a concrete point.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: n/w/center are
    immutable values (no method declares a ``mut`` parameter), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated — reported N/A in the footer.
  * CONTROL-FLOW / RAISE / SIDE-EFFECT — VACUOUS. Both methods are total over
    their precondition (w > 0; every Nat n admitted): each returns a List Int of
    length n, never raises, has no side effect. The returned index list fully
    captures the behaviour, so there is no capability-token discriminator to
    build. Reported N/A in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. ``endsSeq``/``beginsSeq`` are concrete ``def``s
    over ``def`` helpers (empty ``axioms`` region); the cheapest correct impl
    just evaluates them, which the positive controls cover honestly.
  * PARTIAL-DOMAIN / VALUE — the main class. Each rival is right on part of the
    (n, w, center) domain and diverges on a sub-domain: the centred branch, the
    odd-window centred sub-domain, every position (off-by-one), the clamped
    leading positions.

WITNESS MECHANICS. The frozen impl of each method is a ``while`` loop, whose
extracted program does NOT reduce in the kernel (it compiles to
``forIn Lean.Loop.mk`` / well-founded recursion). Every rival below is therefore
written LOOP-FREE, so its extracted program reduces and ``<name>Tester n w center
= false`` decides. Each witness reaches the method contract through Velvet's own
tester machinery (``extract_program_for`` / ``derive_tester_for``); it is checked
in a file whose ``prove_correct`` blocks have been stripped, so no tactic script
can mask the verdict.

WHY EACH REJECT CASE CARRIES ``witness_reference`` (corrected under audit; the
earlier claim in this docstring was BACKWARDS and is withdrawn). The port's
original argument was that gold's inability to reduce is what makes the witness a
discriminator — "half 2 (fails on gold) holds by construction". That is precisely
what makes a witness HOLLOW, not what makes it sound: an exit code the kernel
never derived from the claim carries no information about the claim. Measured on
this cell with real builds, per reject case:

  * the witness against the FROZEN solution: exit 1, but the error is
    ``Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse` ...
    reduction got stuck at the `Decidable` instance`` — a stuck reduction, not a
    refutation;
  * the FORGERY that asserts the OPPOSITE (``... = true``, i.e. that gold is
    WRONG-shaped there): exit 1 with the byte-identical stuck-reduction error.

So gold's exit code is the same for the claim and its negation, and gold cannot
serve as the second subject at all. Confirmed to be a property of the frozen
loop rather than of the tactic: ``decide``, ``decide +kernel``, ``rfl``,
``unfold ...; decide`` and ``simp [<name>Tester]`` all fail on gold at
(3,3,true), every one of them stuck on ``blockEndsExec``.

The repair is the mechanism the gate provides for exactly this carrier: each
reject case names a ``witness_reference`` — the loop-free closed-form positive
for the SAME method, which shares the frozen spec and independently VERIFIES, and
whose extracted program DOES reduce. Against that reference every witness
genuinely decides:

  rival exit 0 | reference exit 1 with
  ``Tactic `decide` proved that the proposition <name>Tester ... = false is
  false`` — a plain evaluation of the concrete claim | forgery exit 0.

The forgery flipping to 0 is the whole point: the subject's exit code now TRACKS
the claim, so the rejection attests to the spec instead of to an irreducible term.
An impl the verifier accepts cannot violate its own spec, so refuting against the
reference is as strong as refuting against gold, and unlike gold it is decidable.
The reference must be the SAME method's positive: a ``blockEnds`` witness against
a ``blockBegins`` positive is stuck again (that positive keeps the frozen
``blockEnds`` loop), which was measured too.

WITNESS PLACEMENT / BINDER COVERAGE. The three binders n, w, center are moved
across the reject witnesses so the battery probes distinct input points rather
than pinning any binder:
  blockEnds  rivals: (n,w,center) = (3,3,true), (2,3,true), (1,1,false), (2,4,false)
  blockBegins rivals: (n,w,center) = (1,2,false), (4,3,true), (6,5,true)
covering center ∈ {true,false}, w ∈ {1,2,3,4,5}, and n ∈ {1,2,3,4,6} on each
method's own predicate. Seven distinct input points in all.

DIVERGENCE / NON-TERMINATION (attack F′; class closed by the verifier, no hole).
This bundle sets ``loom.semantics.termination "total"``, under which the
postcondition is claimed of ALL runs and every loop owes a decreasing measure AND
its descent. Measured on this cell with the ends proof reduced to a bare
``loom_solve``: dropping ``decreasing i`` is refused at the ``method`` declaration
itself (``Decreasing annotations are required in total correctness semantics``),
and keeping the measure while the body does ``i := i + 1`` is refused on the
loop's own goals (residual ``0 ≤ i + 1 ∧ i + 1 ≤ (positions n).length``). Both
exit 1. Not shipped as a reject case for a MEASURED reason, not a judgement call:
a diverging rival keeps the frozen loop, so its extracted program does not reduce
either and its witness is stuck against the rival too (exit 1 on the half that
must SUCCEED => ``witness-unproven``, an inconclusive outcome). Measured on both
shapes above. So the class is closed by the descent obligation, and there is no
shippable witness-bearing case in it. The nagini sibling carries no
``diverge-*``/``nonterm-*`` case either, so nothing was dropped in the port.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the changed
behaviour is modelled deeply, and its soundness against the real callee is a
G-AX concern checked by axiom_check.py). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6744"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl bodies (each lies wholly inside one method's impl region and is
# unique in Solution.lean; both facts asserted at load by _swap). A whole-body
# swap keeps every other method + the frozen proof scaffolding in place, so a
# rejection is a genuine postcondition failure of the reshaped method.
# ---------------------------------------------------------------------------
_ENDS_BODY = (
    "    -- impl-start\n"
    "    let labels := positions n\n"
    "    let mut result : List Int := []\n"
    "    let mut i := labels.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ labels.length\n"
    "      invariant result = endsSeq w center (labels.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := labels[i - 1]!\n"
    "      result := endAt p w center :: result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)

_BEGINS_BODY = (
    "    -- impl-start\n"
    "    let labels := positions n\n"
    "    let mut result : List Int := []\n"
    "    let mut i := labels.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ labels.length\n"
    "      invariant result = beginsSeq w center (labels.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := labels[i - 1]!\n"
    "      let raw := endAt p w center - w\n"
    "      let s : Int := if raw > 0 then raw else 0\n"
    "      result := s :: result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)

# in-loop step / clamp anchors for the reshape positives
_ENDS_STEP = (
    "      let p := labels[i - 1]!\n"
    "      result := endAt p w center :: result\n"
)
_BEGINS_CLAMP = "      let s : Int := if raw > 0 then raw else 0\n"

# frozen proof blocks (a tactic body is elided from the consumer spec view, so a
# positive control may retune it without touching the spec or dropping the
# obligation). Each unique in the file.
_ENDS_PROOF = (
    "prove_correct blockEnds by\n"
    "  loom_solve\n"
    "  rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]\n"
    "  simp_all"
)
_BEGINS_PROOF = (
    "prove_correct blockBegins by\n"
    "  loom_solve\n"
    "  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]\n"
    "  simp_all [beginAt]"
)

# ends full-loop anchor (for prepending an admissibility assert; unique)
_ENDS_LOOP_PREFIX = (
    "    -- impl-start\n"
    "    let labels := positions n\n"
    "    let mut result : List Int := []\n"
    "    let mut i := labels.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ labels.length\n"
    "      invariant result = endsSeq w center (labels.drop i)"
)

for _s in (_ENDS_BODY, _BEGINS_BODY, _ENDS_STEP, _BEGINS_CLAMP,
           _ENDS_PROOF, _BEGINS_PROOF, _ENDS_LOOP_PREFIX):
    assert _BASE.count(_s) == 1, f"anchor drift / not unique: {_s[:40]!r}"


def _ends_mod(body):
    return _swap(_BASE, _ENDS_BODY, "    -- impl-start\n" + body + "\n    -- impl-end")


def _begins_mod(body):
    return _swap(_BASE, _BEGINS_BODY, "    -- impl-start\n" + body + "\n    -- impl-end")


def _tester(method, call):
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n"
            f"example : {call} = false := by\n  decide\n")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG.
# ===========================================================================

# ENDS closed-form direct: return the modelled sequence directly instead of the
# backward accumulator loop. Observationally `endsSeq w center (positions n)` on
# every input. Retune the proof to the one-liner the loop-free impl needs.
_POS_ENDS_DIRECT = _swap(
    _ends_mod("    let out : List Int := endsSeq w center (positions n)\n    return out"),
    _ENDS_PROOF, "prove_correct blockEnds by\n  loom_solve")

# ENDS in-loop local-variable reshape: bind the per-position end into a fresh
# typed local `e` and prepend it instead of inlining `endAt p w center`. Same
# backward accumulator loop, same value flow; the frozen proof still closes.
_POS_ENDS_LOCAL = _swap(
    _BASE, _ENDS_STEP,
    "      let p := labels[i - 1]!\n"
    "      let e : Int := endAt p w center\n"
    "      result := e :: result\n")

# BEGINS closed-form direct.
_POS_BEGINS_DIRECT = _swap(
    _begins_mod("    let out : List Int := beginsSeq w center (positions n)\n    return out"),
    _BEGINS_PROOF, "prove_correct blockBegins by\n  loom_solve")

# BEGINS clamp branch-reorder: rewrite `if raw > 0 then raw else 0` as the
# logically-equivalent `if raw ≤ 0 then 0 else raw`. Same value on every
# position; retune the proof to fold the reordered branch back.
_POS_BEGINS_REORDER = _swap(
    _swap(_BASE, _BEGINS_CLAMP,
          "      let s : Int := if raw ≤ 0 then (0:Int) else raw\n"),
    _BEGINS_PROOF,
    "prove_correct blockBegins by\n"
    "  loom_solve\n"
    "  rw [beginsSeq_drop_step w center (positions n) i (by omega) (by omega)]\n"
    "  simp_all [beginAt]\n"
    "  split_ifs <;> omega")

# ADMISSIBILITY (re-aimed): the methods' only precondition is w > 0, which no
# F2P-shaped input violates, so the sibling's "a normal input satisfies the
# precondition" probe is trivial. Re-aimed at the residual risk on this surface:
# that the post-image is UNSATISFIABLE / DEGENERATE at the interesting point. The
# case discharges an in-region assert pinning the issue's worked example
# (n=9, w=3, center=true): position 1's block is [0, 3) — beginAt 1 = 0,
# endAt 1 = 3 — and the ends sequence has length 9 (the non-degenerate, centred
# behaviour the issue demands). The surrounding impl is kept verbatim so the
# method's own obligation still discharges; the extra proof bullet discharges the
# assert.
_ADMISS = _swap(
    _swap(_BASE, _ENDS_LOOP_PREFIX,
          "    -- impl-start\n"
          "    assert (with_name_prefix `assert\n"
          "      (beginAt 1 3 true = 0 ∧ endAt 1 3 true = 3 ∧ "
          "(endsSeq 3 true (positions 9)).length = 9))\n"
          "    let labels := positions n\n"
          "    let mut result : List Int := []\n"
          "    let mut i := labels.length\n"
          "    while i > 0\n"
          "      invariant 0 ≤ i ∧ i ≤ labels.length\n"
          "      invariant result = endsSeq w center (labels.drop i)"),
    _ENDS_PROOF,
    "prove_correct blockEnds by\n"
    "  loom_solve\n"
    "  · decide\n"
    "  · rw [endsSeq_drop_step w center (positions n) i (by omega) (by omega)]\n"
    "    simp_all")


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the frozen
# spec that MUST be rejected, each with a machine-checked refutation witness at a
# concrete input and the argument that its faithful real counterpart would NOT
# resolve the failing tests.
# ===========================================================================

# ENDS ignore-center (the pre-patch regression): shift hardcoded to 1, ignoring
# `center`. Loop-free `p + 1`.
_RIVAL_ENDS_IGNORE = _ends_mod(
    "    let out : List Int := (positions n).map (fun p => p + 1)\n    return out")

# ENDS floor-shift: centred shift `w / 2` instead of `(w + 1) / 2`. Agrees with
# gold only for even w; diverges for odd w.
_RIVAL_ENDS_FLOOR = _ends_mod(
    "    let out : List Int := (positions n).map "
    "(fun p => p + (if center then w / 2 else 1))\n    return out")

# ENDS off-by-one: every end shifted forward by one extra, on BOTH center flags.
_RIVAL_ENDS_OFFBYONE = _ends_mod(
    "    let out : List Int := (positions n).map "
    "(fun p => p + endShift w center + 1)\n    return out")

# BEGINS drop-clamp: always emit `endAt p w center - w`, never clamp to 0.
_RIVAL_BEGINS_NOCLAMP = _begins_mod(
    "    let out : List Int := (positions n).map "
    "(fun p => endAt p w center - w)\n    return out")

# BEGINS ignore-center (pre-patch regression on the starts site): shift 1 always.
_RIVAL_BEGINS_IGNORE = _begins_mod(
    "    let out : List Int := (positions n).map "
    "(fun p => let r := p + 1 - w; if r > 0 then r else 0)\n    return out")

# BEGINS floor-shift (ADDED under audit). The floor/ceil near-miss was attacked on
# the ENDS side only; the begins side saw the shift distinction solely through the
# all-or-nothing `shift = 1` rival, so a starts site that got the centred shift
# nearly right (off by the parity of w) was unattacked. Centred shift `w / 2`
# instead of `(w + 1) / 2`, then the clamp: agrees with gold for EVEN w, diverges
# for ODD w, and the clamp is still exercised at the leading positions.
_RIVAL_BEGINS_FLOOR = _begins_mod(
    "    let out : List Int := (positions n).map "
    "(fun p => let r := p + (if center then w / 2 else 1) - w; if r > 0 then r else 0)"
    "\n    return out")

# ENDS always-centred (ADDED under audit). Every existing ends rival that touches
# `center` errs by giving the CENTRED branch the uncentred shift. The opposite
# direction — handing the UNCENTRED branch the centred shift — was unattacked, so
# a rival that ignores `center` by collapsing to `(w+1)/2` rather than to `1` had
# no separating input in the battery. Diverges when center=false and w > 1.
_RIVAL_ENDS_ALWAYS_CENTER = _ends_mod(
    "    let out : List Int := (positions n).map (fun p => p + (w + 1) / 2)\n    return out")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-ends-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_ENDS_DIRECT,
     "rationale": "a loop-free block-ends impl that produces the modelled "
                  "sequence directly is observationally `endsSeq w center "
                  "(positions n)` on every (n, w, center), so the single ensures "
                  "clause discharges; a correct reshape must verify (else the "
                  "post-image is over-fit to the accumulator-loop spelling => "
                  "SPEC-TOO-STRONG)."},
    {"id": "pos-ends-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_ENDS_LOCAL,
     "rationale": "binding the per-position end into a fresh typed local `e` and "
                  "prepending it computes the same value as inlining `endAt p w "
                  "center`; the backward accumulator loop and the front-recursive "
                  "invariant are kept verbatim so `out = endsSeq w center "
                  "(positions n)` still holds and the frozen proof closes. Must "
                  "verify."},
    {"id": "pos-begins-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_BEGINS_DIRECT,
     "rationale": "a loop-free block-begins impl that produces `beginsSeq w center "
                  "(positions n)` directly satisfies the ensures clause on every "
                  "input; a correct reshape must verify (else SPEC-TOO-STRONG)."},
    {"id": "pos-begins-clamp-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_BEGINS_REORDER,
     "rationale": "rewriting the clamp `if raw > 0 then raw else 0` as the "
                  "equivalent `if raw ≤ 0 then 0 else raw` yields the same value "
                  "on every position (raw > 0 -> raw; raw ≤ 0 -> 0); the loop and "
                  "invariant are kept verbatim and the proof folds the reordered "
                  "branch back. Must verify; else the spec is over-fit to the "
                  "branch spelling => SPEC-TOO-STRONG."},
    {"id": "admiss-worked-example", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the post-image is satisfiable AND non-degenerate at the "
                  "F2P-shaped point: at n=9, w=3, center=true the centred block "
                  "for position 1 is [0, 3) (beginAt 1 = 0, endAt 1 = 3) and the "
                  "ends sequence has length 9 — the very behaviour the issue "
                  "demands. The in-region assert must discharge (else the "
                  "obligation is unsatisfiable / degenerate at the interesting "
                  "point => PRECOND-TOO-STRONG); the impl is kept verbatim so the "
                  "method's own ensures discharges too."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-ends-ignore-center", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_IGNORE,
     "refinement": "PREPATCH BUG: the block-end shift hardcoded to 1, ignoring "
                   "`center` — the exact pre-patch behaviour. The failing centred "
                   "cases assert manual centred iteration equals the reduced "
                   "result; with a shift of 1 the centred blocks are mis-justified "
                   "(a centred window of size 3 at position 1 becomes [0,2) not "
                   "[0,3), masking a value that must contribute), so the failing "
                   "test still fails. Its faithful real patch would NOT resolve.",
     "rationale": "REJECT from `out = endsSeq w center (positions n)`: endsSeq "
                  "pins each end to i + (w+1)/2 when centred, so a constant "
                  "shift of 1 cannot equal it when center=true and w>1. If it "
                  "verified => SPEC-TOO-WEAK (admits the center-ignoring "
                  "regression). Refuted at (n,w,center)=(3,3,true).",
     "witness": _tester("blockEnds", "blockEndsTester 3 3 true"),
     "witness_reference": _POS_ENDS_DIRECT},
    {"id": "rival-ends-floor-shift", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_FLOOR,
     "refinement": "PARTIAL-DOMAIN (floor vs ceil): centred shift `w / 2` instead "
                   "of `(w + 1) / 2`. Agrees with gold only for EVEN w; diverges "
                   "for ODD w (w=3: 1 vs 2). Its faithful real patch gives the "
                   "buggy pre-patch offset for an odd centred window, so the "
                   "manual-iteration mean is mis-aligned and the failing centred "
                   "test still fails. It would NOT resolve.",
     "rationale": "REJECT from `out = endsSeq w center (positions n)` on the odd-w "
                  "centred sub-domain: endsSeq uses (w+1)/2 = ceil(w/2), which "
                  "differs from w/2 for odd w. If it verified => SPEC-TOO-WEAK on "
                  "that sub-domain. Refuted at (n,w,center)=(2,3,true)."
                  " Distinct from ignore-center: it is a near-miss correct for "
                  "even w, so it carries its own separating (odd-w) input.",
     "witness": _tester("blockEnds", "blockEndsTester 2 3 true"),
     "witness_reference": _POS_ENDS_DIRECT},
    {"id": "rival-ends-offbyone", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_OFFBYONE,
     "refinement": "OFF-BY-ONE on every position: shift = endShift w center + 1. "
                   "Its faithful real patch overshoots the block ends by one on "
                   "BOTH center flags, so even the uncentred cases read the wrong "
                   "half-open block and the reduced result disagrees with manual "
                   "iteration. It would NOT resolve.",
     "rationale": "REJECT from `out = endsSeq w center (positions n)` at every "
                  "position: endAt i = i + endShift w center, with no +1. If it "
                  "verified => SPEC-TOO-WEAK (admits a uniformly-shifted block). "
                  "Refuted at (n,w,center)=(1,1,false) — the uncentred branch, "
                  "which the other ends rivals leave untouched.",
     "witness": _tester("blockEnds", "blockEndsTester 1 1 false"),
     "witness_reference": _POS_ENDS_DIRECT},
    {"id": "rival-begins-drop-clamp", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BEGINS_NOCLAMP,
     "refinement": "DROP THE CLAMP: always emit endAt p w center - w, never "
                   "max(0, .). Its faithful real patch leaves NEGATIVE start "
                   "indices; a negative slice start indexes from the END of the "
                   "dimension, so the leading windows select the wrong (tail) "
                   "data and the reduced result diverges from manual iteration. "
                   "It would NOT resolve.",
     "rationale": "REJECT from `out = beginsSeq w center (positions n)`: beginsSeq "
                  "clamps each start to max(0, endAt i - w); an unclamped start is "
                  "negative on the leading positions of any window with w > shift, "
                  "so it cannot equal beginsSeq there. If it verified => "
                  "SPEC-TOO-WEAK (admits negative, unclamped starts). Refuted at "
                  "(n,w,center)=(1,2,false), where position 0's raw start is "
                  "1 - 2 = -1 but the clamp demands 0.",
     "witness": _tester("blockBegins", "blockBeginsTester 1 2 false"),
     "witness_reference": _POS_BEGINS_DIRECT},
    {"id": "rival-begins-ignore-center", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BEGINS_IGNORE,
     "refinement": "PREPATCH BUG on the starts site: shift 1 always (loop-free "
                   "`max(0, p + 1 - w)`). Its faithful real patch mis-justifies "
                   "the centred-window starts exactly as the pre-patch bug, so the "
                   "failing centred test still fails. It would NOT resolve.",
     "rationale": "REJECT from `out = beginsSeq w center (positions n)`: beginsSeq "
                  "uses endAt i = i + (w+1)/2 when centred, so a start built from a "
                  "shift of 1 cannot equal it when center=true and w>1. If it "
                  "verified => SPEC-TOO-WEAK (center-ignoring on starts). Refuted "
                  "at (n,w,center)=(4,3,true), whose centred shift is 2 not 1.",
     "witness": _tester("blockBegins", "blockBeginsTester 4 3 true"),
     "witness_reference": _POS_BEGINS_DIRECT},

    # ---- ADDED under audit: the two directions the ported rivals left open ----
    {"id": "rival-begins-floor-shift", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BEGINS_FLOOR,
     "refinement": "PARTIAL-DOMAIN (floor vs ceil) on the STARTS site: centred "
                   "shift `w / 2` instead of `(w + 1) / 2`, then the clamp. Agrees "
                   "with gold for EVEN w, diverges for ODD w (w=5: 2 vs 3). Its "
                   "faithful real patch under-shifts the centred window starts by "
                   "one for an odd window, so each block is mis-justified and the "
                   "reduced result disagrees with manual centred iteration. It "
                   "would NOT resolve.",
     "rationale": "REJECT from `out = beginsSeq w center (positions n)` on the "
                  "odd-w centred sub-domain: beginsSeq is built from endAt i = "
                  "i + (w+1)/2 = i + ceil(w/2), which exceeds i + w/2 for odd w, "
                  "and the clamp cannot absorb the difference at a position whose "
                  "raw start is already positive. If it verified => SPEC-TOO-WEAK "
                  "on that sub-domain. Refuted at (n,w,center)=(6,5,true), where "
                  "gold's shift is 3 and the rival's is 2. ADDED under audit: the "
                  "floor/ceil near-miss was attacked on the ENDS side only, so the "
                  "begins site saw the shift distinction solely through the "
                  "all-or-nothing `shift = 1` rival and a starts computation off "
                  "by exactly the parity of w was unattacked.",
     "witness": _tester("blockBegins", "blockBeginsTester 6 5 true"),
     "witness_reference": _POS_BEGINS_DIRECT},
    {"id": "rival-ends-always-center", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_ALWAYS_CENTER,
     "refinement": "IGNORES `center` IN THE OTHER DIRECTION: the shift is "
                   "`(w + 1) / 2` unconditionally, so an UNCENTRED window is given "
                   "the centred justification. Its faithful real patch shifts every "
                   "uncentred block end forward by ceil(w/2) - 1, so the plain "
                   "(uncentred) rolling cases read a block that is not the one "
                   "ending at their own position; those cases pass before the "
                   "change and would break, so it would NOT resolve.",
     "rationale": "REJECT from `out = endsSeq w center (positions n)`: endsSeq pins "
                  "the shift to 1 when center=false, so `(w + 1) / 2` cannot equal "
                  "it for w > 1. If it verified => SPEC-TOO-WEAK (the ensures would "
                  "not pin the uncentred branch at all). Refuted at "
                  "(n,w,center)=(2,4,false), whose gold shift is 1 and rival shift "
                  "is 2. ADDED under audit: every ported ends rival that touches "
                  "`center` errs by giving the CENTRED branch the uncentred shift; "
                  "the opposite direction had no separating input in the battery, "
                  "so a rival collapsing `center` to the centred value rather than "
                  "to 1 went unattacked.",
     "witness": _tester("blockEnds", "blockEndsTester 2 4 false"),
     "witness_reference": _POS_ENDS_DIRECT},
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals; the frame-mutation class is
# absent there because all inputs are primitives passed by value) plus 2
# AXIOM_TESTS. This bundle contracts the SAME two functions — block_ends /
# block_begins (here blockEnds / blockBegins) over the (n, w, center) carrier —
# so the port is near-parallel; the permission machinery, the framing Asserts,
# and the @Pure-helper spelling do not exist here and their bookkeeping falls
# away. Every sibling SPEC case is accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-ends-local-reshape          -> pos-ends-local-reshape        PORTED
#                                      (+ pos-ends-direct            ADDED)
#   pos-begins-clamp-reorder        -> pos-begins-clamp-reorder      PORTED
#                                      (+ pos-begins-direct          ADDED)
#   admiss-selfcall                 -> admiss-worked-example         RE-AIMED
#   rival-ends-ignore-center        -> rival-ends-ignore-center      PORTED
#   rival-ends-floor-shift          -> rival-ends-floor-shift        PORTED
#   rival-ends-offbyone             -> rival-ends-offbyone           PORTED
#   rival-begins-drop-clamp         -> rival-begins-drop-clamp       PORTED
#   rival-begins-ignore-center      -> rival-begins-ignore-center    PORTED
#   (no sibling counterpart)        -> rival-begins-floor-shift      ADDED (audit)
#   (no sibling counterpart)        -> rival-ends-always-center      ADDED (audit)
#
# 5 rivals + 2 positives ported (each positive split-mirrored by an extra
# closed-form-direct control on the same method, so both methods carry two
# independent reshape positives), 1 admissibility re-aimed, 2 rivals added under
# audit. 12 SPEC cases here.
#
# EVERY nagini SPEC case is accounted for above and NONE was dropped, so the
# omission review (attack F) has no `inexpressible` entry to defend: the port is
# 8-for-8 on the sibling's cases. The classes the sibling itself reports N/A
# (frame-mutation, control-flow/raise/side-effect) are re-derived as vacuous below
# on carrier facts, not inherited.
#
# RE-AIMED (admissibility): the sibling's case is a SELF-CALL that establishes
#   the callee's Requires from the caller's own (n>=0, w>0, primitives by value).
#   Velvet has no permission to consume and the self-call adds no strength beyond
#   the trivial `w > 0` precondition, so that probe is vacuous. It is re-aimed at
#   the residual admissibility risk on this surface — that the post-image is
#   UNSATISFIABLE / DEGENERATE at the interesting point — via an in-region assert
#   pinning the issue's worked example (n=9,w=3,center=true: block [0,3) at
#   position 1, ends length 9).
# ADDED (2 positives): pos-ends-direct and pos-begins-direct. The sibling ships
#   ONE reshape positive per method (a local-var reshape / a branch reorder). We
#   keep those AND add a closed-form-direct control per method, so each method's
#   soundness surface is defended by two structurally-distinct correct impls (an
#   in-loop reshape and a loop-free direct evaluation) rather than one.
#
# VACUOUS (frame-mutation): the sibling explicitly reports this class N/A — all
#   inputs are primitives passed by value, so there is nothing to overwrite. It
#   is likewise vacuous here: n/w/center are immutable values, no `mut` binder,
#   no heap, no aliasing. Not fabricated.
# VACUOUS (control-flow / raise / side-effect): the sibling reports this class
#   N/A — both functions are total over their precondition, never raise, have no
#   side effect, and the returned index list fully captures the behaviour. Same
#   here: no capability-token discriminator to build.
#
# ADMISSIBILITY IS LOAD-BEARING, not decorative (checked under audit rather than
#   asserted). Two vacuity controls were built and both FAIL to verify, so the
#   assert is genuinely discharged by evaluation and not skipped: replacing the
#   worked example's `endAt 1 3 true = 3` with the pre-image-shaped `= 4` exits 1
#   (``decide` proved that the proposition ... is false`), and replacing the whole
#   conjunction with `False` exits 1 likewise. An assert that a `decide` bullet
#   could close regardless would have passed both.
#
# BINDER / CLAUSE COVERAGE. Each method's single top-level ensures clause is
#   attacked: blockEnds by four ends rivals (constant-shift, floor-shift,
#   off-by-one, always-centred) and blockBegins by three begins rivals
#   (drop-clamp, ignore-center, floor-shift). The three input binders n, w, center
#   are all VARIED by the witnesses — center ∈ {true,false}, w ∈ {1,2,3,4,5},
#   n ∈ {1,2,3,4,6} — across SEVEN distinct input points, so no binder is pinned,
#   and the variation is verdict-CHANGING at every point rather than two spellings
#   of one input (each rival's value was evaluated against gold's at its own
#   witness point and differs there: e.g. ends @ (3,3,true) gold [2,3,4] vs rival
#   [1,2,3]; begins @ (1,2,false) gold [0] vs rival [-1]). Both DIRECTIONS of the
#   `center` dependence are now attacked — the centred branch given the uncentred
#   shift (ignore-center, floor-shift on both methods) and the uncentred branch
#   given the centred shift (always-center) — and the clamp is probed both at a
#   genuine underflow (raw = -1) and at a position where it does NOT fire
#   (begins-floor-shift @ (6,5,true)). There is no free/ambient input to hold
#   fixed.
#
# SPEC-TOO-WEAK PROBE (attack D, run under audit; no hole found). Seven NEW wrong
#   impls beyond the shipped rivals were built and every one FAILS to verify:
#   a centred shift of `w/2 + 1` (wrong only for even w, the complement of
#   floor-shift), a last-position-only overshoot, a clamp firing one position too
#   far (`r > 1`), the begins floor-shift, the ends always-centred shift, the
#   result REVERSED (right multiset, wrong order), and the result one element
#   SHORT (`dropLast`, wrong length). The last two matter because order and length
#   are pinned only through the single list equality; both are refused. The two
#   that probe an unattacked DIRECTION rather than a re-spelling were promoted to
#   shipped rivals above.
# SPEC-TOO-STRONG PROBE (attack E, run under audit; no hole found). Three NEW
#   correct reshapes were built and all three VERIFY: `foldr` over the positions
#   in place of `map`, the clamp spelled `max 0 (endAt p w center - w)`, and the
#   shift inlined as `if center then (w+1)/2 else 1` inside the frozen loop. Each
#   needed its own proof retune (`induction positions n` / `split <;> omega` /
#   `simp_all [endAt, endShift]`), which is the expected cost on a tactic-proof
#   backend and not evidence of over-fitting: the obligation statement is
#   untouched in all three.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the changed behaviour is
#   modelled deeply (no `axiom` in the bundle) and its soundness against the real
#   callee lives in axiom_check.py. This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
