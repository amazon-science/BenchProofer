"""properties.py — G-PBT falsification battery for sympy__sympy-11618 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct distanceSq`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  distanceSq (sameKind : Bool) (s : List Int) (q : List Int) return (out : Int)
    ensures out = distSq sameKind s q

The method reports the squared separation between two coordinate vectors,
measured in the ambient dimension the two are compared in: when the two are of
the same kind their coordinate counts already coincide, so the comparison runs
over the shared length; when they are of different kinds the comparison is
carried out in the LARGER ambient space, with the shorter vector embedded at the
origin (its missing coordinates contributing zero). The single load-bearing
``ensures`` pins ``out`` to ``distSq sameKind s q`` — align BOTH vectors to that
common dimension (zero-padding the shorter), then sum the squared per-coordinate
differences, dropping NO coordinate. The discriminating content lives entirely
in which coordinate set is summed: a rival that sums a different axis set
produces a different value and cannot equal ``distSq``.

THREE INPUT BINDERS, all free: ``sameKind`` (which ambient dimension —
shared-length vs larger), ``s`` and ``q`` (the two coordinate vectors). The
reject witnesses must vary ``sameKind`` across both truth values and drive ``s``
/ ``q`` to lengths that make the surplus tail non-zero, since a rival that
mishandled only the ``sameKind = false`` (larger-ambient) branch, or only one
vector-length regime, would slip past a battery that pinned those binders.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHAT THE GOLD-SIDE BUILD DOES *NOT*
PROVE. A witness reaches the post-image through Velvet's tester machinery
(``distanceSqTester ... = false`` says the extracted program's result violates
the postcondition at that concrete input) and closes by ``decide``, checked in a
file whose ``prove_correct`` block has been stripped so no tactic script can mask
the verdict. ``decide`` reduces the extracted program by kernel computation; a
program shaped as a ``while`` loop over the coordinate stream does NOT reduce to
``isTrue``/``isFalse``. Under ``loom.semantics.choice "demonic"`` the loop's
fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold: ``#reduce distanceSqExec false [1,0,2] [2,0]`` on the frozen solution
returns a term still containing ``Classical.choice``. So each reject rival is
expressed as a LOOP-FREE impl that computes its (wrong) value directly from the
pure helpers ``sumSqZip`` / ``alignTo`` — still a wrong implementation sharing
the frozen spec, but one whose extracted tester ``decide``s.

MEASURED CONSEQUENCE, recorded here because it bounds what these cases attest.
The frozen solution keeps the loop, so ``decide`` is STUCK against it for EVERY
claim, true or false alike: ``distanceSqTester false [1,0,2] [2,0] = true`` is
the true statement about the frozen impl (``#eval`` returns ``true``) and it also
fails to elaborate, with the same "did not reduce to ``isTrue``/``isFalse``"
error. The gate's second half ("the witness must FAIL against the frozen
solution") is therefore satisfied here by a REDUCTION failure, not by a semantic
refutation, and it would be satisfied by any claim whatsoever — including a
forged witness asserting a rival is CORRECT at a point where it happens to agree
with gold. That forgery was built and measured: rival exit 0, gold exit 1.
So the gold-side build is NOT what earns the rejections on this cell.

What earns them instead, and what the cases below are constructed to make
checkable, is that each witness is semantically FALSE of a CORRECT impl of the
same loop-free shape. Each of the three reject witnesses was rebuilt against a
loop-free impl that computes ``distSq`` faithfully, and each failed there with
``decide`` proved that the proposition ... is false — i.e. the claim is a real
statement about the summed VALUE, not an artifact of dropping the loop. The
``pos-control-loopfree-correct`` case below pins that same fact inside the
battery: a loop-free impl VERIFIES, so loop-freeness is not what any rival is
rejected for.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: every parameter is an
    immutable value (this bundle declares no ``mut`` binder among the inputs;
    ``s`` and ``q`` are pure ``List Int`` arguments), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe.
    Not fabricated. (See footer.)
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane: the single
    clause pins the summed axis set on EVERY input, so a rival that walks only
    the shorter vector's coordinates (min-truncation), or drops the terminal
    axis of the common dimension (off-by-one), or does no work at all, diverges
    from ``distSq`` at a concrete input.
  * UNGROUNDED-ORACLE ECHO — N/A. ``distSq`` is a fully unfolded ``def`` over the
    method's own arguments (the ``axioms`` region is empty — no opaque answer key
    to echo); the only way to satisfy the postcondition is to build the padded
    squared sum correctly, which the positive control does honestly.

WITNESS PLACEMENT. Rivals share a refutation point only when they fail there for
the same reason. The FOUR reject witnesses sit at FOUR DISTINCT input points and
between them move ``sameKind`` across BOTH values (``false`` for the
larger-ambient rivals, ``true`` for the equal-length off-by-one rival and for the
same-kind/unequal-length rival) and drive ``s`` / ``q`` to lengths whose surplus
tail is non-zero, so the manifest demonstrates the post-image's dependence on
``sameKind`` and on the full coordinate set rather than on a single pinned shape.

The four points are pairwise necessary, measured with ``#eval`` of the extracted
tester on each rival at each point (frozen values 5 / 50 / 25 / 16):

  point                     gold  min-trunc  drop-last  const-0  ignores-kind
  false [1,0,2] [2,0]         5      1          1         0          5
  true  [3,4,5] [0,0,0]      50     50         25         0         50
  false [0,0,5] [0,0]        25     25          0         0         25
  true  [5]     [1,2,3,4]    16     16          0         0         45

Each rival diverges from gold at its OWN point and at least one other rival
agrees with gold there, so no point is redundant and none could be dropped. The
last row is the regime the ported battery missed entirely: three of the four
rivals agree with gold at it, so without ``weak-ignores-samekind`` nothing forced
the ``sameKind`` binder to be read.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-11618"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl body: a single anchor lying wholly inside the impl
# ---- region and unique in the file (both facts asserted at load by _swap).
# ---- Rivals that reshape the executable surface entirely swap on this block.
_IMPL_BODY = (
    "    let L := if sameKind then min s.length q.length else max s.length q.length\n"
    "    let mut acc : Int := 0\n"
    "    let mut i := L\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ L\n"
    "      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc\n"
    "      i := i - 1\n"
    "    return acc\n"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

# ---- (An `_ACC_LINE` anchor for the single loop-body accumulation line was
# ---- dropped by the audit along with the definitionally-equal positive control
# ---- that used it: reshaping only that line leaves an impl the FROZEN proof
# ---- script still closes verbatim, which is the signal that nothing was
# ---- reproven. The replacement positive control reshapes `_IMPL_BODY` instead,
# ---- so the accumulation-step reshape is retained on top of a change the frozen
# ---- script does NOT close.)

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, may retune it without
# ---- touching the spec or dropping the `prove_correct distanceSq` obligation).
_PROOF_GOLD = (
    "prove_correct distanceSq by\n"
    "  loom_solve\n"
    "  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]\n"
    "    simp_all\n"
    "  · simp only [distSq, commonLen]\n"
    "    simp_all\n"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the pointwise
# ---- equality (or leaves nothing — for the reject rivals it FAILS, which is the
# ---- point). Reject rivals retune the proof to this shape so the rejection is
# ---- attributable to the spec (the witness), not to a proof script tuned to a
# ---- loop that no longer exists.
_PROOF_FLAT = "prove_correct distanceSq by\n  loom_solve\n"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `distanceSqTester sameKind s q = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped. Every
# ---- argument is a concrete integer-coordinate literal so `decide` reduces the
# ---- (loop-free) extracted program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for distanceSq\n"
            "prove_precondition_decidable_for distanceSq\n"
            "prove_postcondition_decidable_for distanceSq\n"
            "derive_tester_for distanceSq\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    #
    # AUDIT NOTE. The earlier form of this case named the per-coordinate
    # difference in a local `let d` and left the frozen proof script untouched.
    # That reshape is DEFINITIONALLY equal to the frozen impl — the frozen
    # tactic script closes it verbatim, which is exactly the signal that nothing
    # new was reproven. Replaced with a reshape that is NOT definitionally equal:
    # the common dimension is computed with the min/max arguments COMMUTED
    # (`min q.length s.length` / `max q.length s.length`). `Nat.min`/`Nat.max` are
    # commutative but not definitionally so on open terms, so the frozen proof
    # script FAILS on this impl (measured: exit 1, `unsolved goals` on
    # `ensures_1`) and the obligation has to be re-established with an explicit
    # `rw [Nat.min_comm, Nat.max_comm]`. The named-difference reshape is kept on
    # top of it, so this case subsumes the old one. Both the loop and every
    # invariant are retained, so the loop obligation is still discharged.
    # =====================================================================
    {
        "id": "pos-control-commuted-dimension",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_BODY,
                "    let L := if sameKind then min q.length s.length else max q.length s.length\n"
                "    let mut acc : Int := 0\n"
                "    let mut i := L\n"
                "    while i > 0\n"
                "      invariant 0 ≤ i ∧ i ≤ L\n"
                "      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)\n"
                "      done_with i = 0\n"
                "      decreasing i\n"
                "    do\n"
                "      let d : Int := (alignTo s L)[i-1]! - (alignTo q L)[i-1]!\n"
                "      acc := d ^ 2 + acc\n"
                "      i := i - 1\n"
                "    return acc\n"),
            _PROOF_GOLD,
            "prove_correct distanceSq by\n"
            "  loom_solve\n"
            "  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]\n"
            "    simp_all\n"
            "  · simp only [distSq, commonLen]\n"
            "    rw [Nat.min_comm, Nat.max_comm]\n"
            "    simp_all\n"),
        "rationale": (
            "a CORRECT reshape that is not definitionally equal to the frozen "
            "impl: the common ambient dimension is computed with the min/max "
            "arguments commuted, and the per-coordinate difference is named in a "
            "local `let` before squaring. Both compute the same value on the whole "
            "domain (`min`/`max` are commutative), so `out = distSq sameKind s q` "
            "still holds — but not by `rfl`: the FROZEN proof script fails on this "
            "impl (exit 1, unsolved `ensures_1` goal), so the obligation is "
            "genuinely re-established via `Nat.min_comm`/`Nat.max_comm` rather "
            "than restated. A faithful correct impl must verify, else the "
            "postcondition is SPEC-TOO-STRONG (rejecting an impl over the argument "
            "order of a commutative operation)."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the loop-free CONTROL for the reject lane.
    #
    # AUDIT-ADDED. Every reject rival below is loop-free (the CARRIER NOTE
    # explains why: only a loop-free program's tester `decide`s). That leaves an
    # unattested assumption the battery previously relied on — that loop-freeness
    # is not itself what the rejections attribute to. This case discharges it: a
    # loop-free impl that computes `distSq` FAITHFULLY, in the same single-return
    # shape as the rivals, and which MUST verify. With it in the battery, the
    # three rejections below are attributable to the summed VALUE, since the only
    # thing separating them from this case is which coordinate set they sum.
    # =====================================================================
    {
        "id": "pos-control-loopfree-correct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    let L := if sameKind then min s.length q.length else max s.length q.length\n"
                  "    return sumSqZip (alignTo s L) (alignTo q L)\n"),
            _PROOF_GOLD,
            "prove_correct distanceSq by\n"
            "  loom_solve\n"
            "  simp [distSq, commonLen]\n"),
        "rationale": (
            "the loop-free CONTROL for the reject lane: computes the padded "
            "squared sum over the common dimension directly, with no loop, and so "
            "satisfies `out = distSq sameKind s q` on the whole domain. It MUST "
            "verify. This is what makes the loop-free rivals below attributable: "
            "they differ from this case ONLY in which coordinate set they sum, so "
            "their rejection is about the summed value and not about having "
            "dropped the loop. (If this failed, the spec would be SPEC-TOO-STRONG "
            "over program shape and every reject case below would be suspect.)"
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing could
    # exclude an F2P-shaped input. The residual admissibility risk on a total
    # domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads exactly like one every
    # impl meets. This case discharges an in-region `assert`, at a fully concrete
    # F2P-shaped input (a 3-coordinate vector compared with a 2-coordinate vector
    # of a different kind), that the post-image is NON-DEGENERATE: the squared
    # separation there is exactly 5, i.e. the surplus third coordinate is
    # genuinely counted. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned only to clear the extra
    # assert goal by `decide` (allowed — the tactic body is elided from the spec
    # view). The assert is live: a false claim about that point leaves an
    # unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (distSq false [1,0,2] [2,0] = 5))\n"),
            _PROOF_GOLD,
            "prove_correct distanceSq by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]; simp_all)\n"
            "    | (simp only [distSq, commonLen]; simp_all)\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "input: for a 3-coordinate vector compared with a differently-kinded "
            "2-coordinate vector it demands the squared separation be exactly 5, "
            "which counts the surplus third coordinate (2^2 + (1-2)^2 = 5) rather "
            "than dropping it. The in-region assert must discharge (else the "
            "obligation is unsatisfiable / degenerate at the point the fix cares "
            "about); the impl is kept verbatim so the method's own `ensures` "
            "still discharges."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is expressed as
    # a LOOP-FREE impl (single expression over the pure helpers) so its extracted
    # tester `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-min-truncation",
        "kind": "uniqueness",
        "expect": "reject",
        # Always sum over the SHORTER vector's length (min), ignoring the
        # larger-ambient branch entirely. This is the literal truncating-zip
        # shape: every coordinate present only in the longer vector is dropped.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return sumSqZip (alignTo s (min s.length q.length)) (alignTo q (min s.length q.length))\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "this walks the two coordinate streams only as far as the shorter one "
            "reaches, dropping every coordinate present only in the longer vector "
            "— the pre-fix truncating co-iteration. For a 3-coordinate vector "
            "compared with a differently-kinded 2-coordinate vector it sums only "
            "the first two axes (squared separation 1) where the correct answer "
            "counts all three (squared separation 5), so the failing scenario — "
            "which pins the full-dimension separation — still fails. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from `out = distSq sameKind s q`: `distSq` aligns to the "
            "COMMON dimension (the larger, when the kinds differ), and this impl "
            "aligns to the min, so the two disagree whenever the longer vector has "
            "a non-zero tail. Verifying would be SPEC-TOO-WEAK (the clause does "
            "not force summation over the larger ambient dimension). Refuted at "
            "sameKind=false, s=[1,0,2], q=[2,0] (unequal lengths, the "
            "larger-ambient branch)."
        ),
        "witness": _tester(
            "example : distanceSqTester false ([1,0,2] : List Int) ([2,0] : List Int) = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-drop-last-axis",
        "kind": "uniqueness",
        "expect": "reject",
        # Sum over one fewer than the common dimension (commonLen - 1): correct on
        # most of the domain but loses the FINAL axis of the ambient space. Abuses
        # the equal-length regime (sameKind=true), where min-truncation would
        # AGREE with gold — so this near-miss needs its own discriminating input.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    let L := (if sameKind then min s.length q.length else max s.length q.length) - 1\n"
                  "    return sumSqZip (alignTo s L) (alignTo q L)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "an off-by-one upper bound: sums every coordinate of the common "
            "dimension EXCEPT the last, dropping the terminal axis. For two "
            "same-kind 3-coordinate vectors it sums axes 0,1 and drops axis 2, so "
            "the reported squared separation omits the terminal coordinate's "
            "contribution and the failing scenario — which pins the full separation "
            "— still fails. A real `range(n-1)` / `max-1` bound would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = distSq sameKind s q`: `distSq` sums over the full "
            "common dimension and this impl sums over one fewer, so the two "
            "disagree whenever the last axis contributes. Verifying would leave "
            "the terminal axis unpinned (partial-domain SPEC-TOO-WEAK). Refuted at "
            "sameKind=true, s=[3,4,5], q=[0,0,0] (equal lengths — the regime where "
            "the min-truncation rival AGREES with gold, so this near-miss carries "
            "its own discriminating input and moves the sameKind binder to true)."
        ),
        "witness": _tester(
            "example : distanceSqTester true ([3,4,5] : List Int) ([0,0,0] : List Int) = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-constant-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the constant 0 for EVERY input, doing no work. Satisfies nothing
        # but the trivial zero-separation case.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY, "    return 0\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "returning a constant zero separation for every input reports "
            "coincident points always, so any scenario with a genuine separation "
            "(e.g. the F2P pair, whose squared separation is 5) still fails. The "
            "degenerate 'no work done' rival — a real patch returning a constant "
            "zero distance would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = distSq sameKind s q`: a constant 0 disagrees with "
            "`distSq` on every input whose padded squared sum is non-zero. "
            "Verifying would mean the postcondition does not pin the summed value "
            "to the actual coordinates (SPEC-TOO-WEAK / hollow). Refuted at "
            "sameKind=false, s=[0,0,5], q=[0,0] (the surplus fifth-unit third "
            "coordinate gives a non-zero separation the constant 0 cannot match)."
        ),
        "witness": _tester(
            "example : distanceSqTester false ([0,0,5] : List Int) ([0,0] : List Int) = false := by\n"
            "  decide\n"),
    },

    # =====================================================================
    # AUDIT-ADDED rival. The three rivals above leave one regime of the
    # `commonLen` clause entirely unattacked: `sameKind = true` with UNEQUAL
    # coordinate counts, where the clause demands the SHARED-length (min)
    # comparison. Every rival above either agrees with `distSq` there or is
    # already refuted elsewhere, so nothing in the battery forced the `sameKind`
    # discriminator to be READ — an impl that ignores `sameKind` and always uses
    # the larger ambient dimension satisfied every witness above.
    #
    # Measured on the frozen solution vs this rival (`#eval` of the extracted
    # tester): at sameKind=true, s=[5], q=[1,2,3,4] the frozen impl returns 16
    # (the shared-length comparison, min = 1) and this rival returns 45 (the
    # larger dimension, max = 4). At all three witness points of the rivals above
    # this rival AGREES with gold (5, 50, 25) — which is precisely why it needs
    # its own input, and why its absence was a real gap rather than a duplicate.
    # =====================================================================
    {
        "id": "weak-ignores-samekind",
        "kind": "uniqueness",
        "expect": "reject",
        # Always compare in the LARGER ambient dimension, never reading
        # `sameKind`: correct whenever the kinds differ, wrong for a same-kind
        # pair whose coordinate counts do not coincide.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    let L := max s.length q.length\n"
                  "    return sumSqZip (alignTo s L) (alignTo q L)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "drops the same-kind discriminator and always zero-pads to the larger "
            "coordinate count. For a SAME-KIND pair whose counts differ this pads "
            "and counts axes the shared-length comparison does not reach: for "
            "s=[5] against q=[1,2,3,4] it reports 45 where the shared-length "
            "comparison reports 16. A real patch that unconditionally padded to "
            "the larger dimension would change the same-kind path's answer, so a "
            "scenario pinning the shared-length comparison still fails. It would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = distSq sameKind s q`: `distSq` routes through "
            "`commonLen sameKind`, which is the SHARED length (min) when "
            "`sameKind` holds and the larger (max) otherwise; this impl uses the "
            "larger unconditionally, so the two disagree on every same-kind pair "
            "with unequal counts and a contributing surplus tail. Verifying would "
            "mean the clause does not force the `sameKind` binder to be read at "
            "all (SPEC-TOO-WEAK on the branch selector) — the one regime the other "
            "three rivals leave untested, since all three agree with `distSq` at "
            "this input. Refuted at sameKind=true, s=[5], q=[1,2,3,4]."
        ),
        "witness": _tester(
            "example : distanceSqTester true ([5] : List Int) ([1,2,3,4] : List Int) = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 3 partial-domain uniqueness
# rivals) plus 2 AXIOM_TESTS. This bundle models the changed operation DEEPLY
# (the squared distance `distSq` via `alignTo`/`sumSqZip`, spelled-out
# arithmetic), so there is no axiom and no permission surface; the value surface
# (which coordinate set is summed) carries across intact.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder           -> pos-control-commuted-dimension PORTED
#   admiss-f2p-shaped                    -> admiss-postimage-nondegenerate RE-AIMED
#   frame-mutate-readonly-u              -> (none)                         VACUOUS
#   partial-domain-min-truncation        -> weak-min-truncation           PORTED
#   partial-domain-drop-last-axis        -> weak-drop-last-axis           PORTED
#   ungrounded-constant-root-zero        -> weak-constant-zero            PORTED
#   ax-root-soundness / ax-root-cont.    -> (none)                        DROPPED (G-AX lane)
#   (no sibling)                         -> pos-control-loopfree-correct   AUDIT-ADDED
#   (no sibling)                         -> weak-ignores-samekind          AUDIT-ADDED
#
# 4 ported, 1 re-aimed, 1 vacuous, 2 axiom-lane dropped, 2 audit-added.
#
# AUDIT REVISIONS (independent audit of the port; frozen artifact untouched):
#   * pos-control-named-difference -> pos-control-commuted-dimension. The ported
#     positive control reshaped only the accumulation line and kept the FROZEN
#     proof script, i.e. it was definitionally equal to the frozen impl and the
#     frozen tactics closed it verbatim. It passed honestly while reproving
#     nothing. The replacement commutes the min/max arguments of the common
#     dimension — provably equal, not definitionally so: the frozen script fails
#     on it (exit 1, unsolved `ensures_1`) and the obligation is re-established
#     with `Nat.min_comm`/`Nat.max_comm`. The named-difference reshape is kept on
#     top, so the old case is subsumed.
#   * pos-control-loopfree-correct ADDED. All reject rivals are loop-free; nothing
#     in the ported battery showed that loop-freeness is not what they are
#     rejected for. This case shows a loop-free FAITHFUL impl verifies.
#   * weak-ignores-samekind ADDED. See the case comment and the WITNESS PLACEMENT
#     table: the `sameKind = true` / unequal-length regime was unattacked, and an
#     impl that never reads `sameKind` satisfied all three ported witnesses.
#
# VACUOUS (frame-mutate-readonly-u): the sibling writes to a read-only input that
#   carries only a fractional heap permission (`Acc(list_pred(u),1/2)`) and is
#   rejected for INSUFFICIENT PERMISSION before any value reasoning. This backend
#   is referentially transparent: `s` and `q` are immutable `List Int` values,
#   this bundle declares no `mut` binder among the inputs, and there is no heap or
#   aliasing. There is no read-only input to overwrite and no permission system to
#   trip, so the class is vacuous. No substitute is fabricated (per the porting
#   map, this class is legitimately dropped here rather than replaced).
#   AUDIT-CONFIRMED by construction, not by argument alone. Two routes were built
#   and measured: (1) assigning to a parameter inside the impl region is a
#   COMPILE error, not a spec rejection — "`s` cannot be mutated, only variables
#   declared using `let mut` can be mutated" — so it cannot serve as a rival
#   whose rejection attributes to the spec; (2) redeclaring the binder as
#   `(mut s : List Int)` puts the change in the method signature, which is part of
#   the consumer spec view, so `variant_problems` reports "spec view differs
#   (same_spec failed)" and the case is out of scope. There is no in-scope
#   frame-mutation rival on this carrier. Verdict: inexpressible.
# RE-AIMED (admissibility): the sibling establishes that the half-permission input
#   is readable and a normal return is reachable. There is no precondition and no
#   permission here, so that probe is vacuous. It is re-aimed at the residual
#   admissibility risk on a total domain: that the post-image is unsatisfiable or
#   degenerate at the interesting point. The case discharges an in-region assert
#   pinning the squared separation of the F2P-shaped input (a differently-kinded
#   3-vs-2 coordinate pair) to exactly 5 — counting the surplus axis, not dropping
#   it.
# DROPPED (ax-root-*): the sibling's two AXIOM_TESTS probe the `root` (= sqrt)
#   oracle's determinism/non-negativity and containment. This bundle has NO axiom
#   (mapping.md §3: the squared value is modeled deeply; `sqrt` is not
#   axiomatized, the observable is the squared distance `distSq` over `Int`), so
#   there is no axiom lane to mirror. The axiom lane is G-AX's job and this gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = distSq sameKind s
#   q` is attacked by FOUR rivals across distinct sub-domains — the larger-ambient
#   min-truncation, the equal-length drop-last-axis near-miss, the do-nothing
#   constant, and the same-kind/unequal-length branch-selector rival — refuted at
#   FOUR DISTINCT input points (pts=4). The `sameKind` binder is moved across BOTH
#   values (false for min-truncation and constant-zero, true for drop-last-axis
#   and ignores-samekind), and it is now DISCRIMINATED rather than merely varied:
#   `weak-ignores-samekind` fails only because it does not read `sameKind`, so the
#   binder's variation changes the spec's verdict instead of being two spellings
#   of one point. `s` and `q` are driven to lengths whose surplus tail is non-zero
#   so the dependence of the summed value on the full coordinate set (not merely
#   the shared prefix) is demonstrated. No two rivals share a witness point; the
#   pairwise-necessity table in the module docstring records the measured tester
#   values that show why.
#
# WHAT THESE REJECTIONS DO AND DO NOT ATTEST (audit, measured). The gate's
#   gold-side build on this cell fails by STUCK REDUCTION, not semantic
#   refutation: the frozen impl keeps a `while` loop whose fixpoint elaborates
#   through `Classical.choice`, so `decide` cannot reduce its tester for ANY
#   claim — the TRUE claim about the frozen impl fails identically. A forged
#   witness asserting a rival is CORRECT at an agreement point was built and
#   passed both gate halves (rival exit 0, gold exit 1). So the discrimination
#   evidence for this cell is NOT the gold-side exit code; it is (a) each witness
#   being semantically FALSE of a correct loop-free impl (rebuilt: `decide` proved
#   the proposition false, exit 1, for all four), and (b) the
#   `pos-control-loopfree-correct` case verifying. Both are recorded above. This
#   is a limitation of the witness harness on a demonic-choice loop carrier, not
#   of the frozen spec, and it is escalated as an audit finding rather than
#   patched here.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep model); this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
