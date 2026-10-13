"""properties.py — G-PBT falsification battery for astropy__astropy-12907 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_direct_sum`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the combinator over a ``PSeq[PSeq[int]]`` carrier and pins each row
against a GROUNDED pure deep model (nagini's ``expected_row``). This Lean bundle
models the SAME single purely-functional core — the block-diagonal (direct-sum)
arrangement of two independent correlation matrices placed side by side — over a
``List (List Nat)`` carrier, and the SAME grounding: the postcondition relates
``result`` to the inputs structurally (length + a per-row equation for each of
the two blocks), with no opaque answer key to echo. Every nagini case carries
over as an attack on one of the three top-level postcondition clauses, or as a
faithful correct positive; the nagini frame/permission-mutation class is VACUOUS
here (referential transparency — see ``assessment``).

DEFENDED SURFACE (one modeled behavior; three independent top-level clauses).
``problem_spec_direct_sum lin rin left right result`` pins EXACTLY:

  * (C0 length)  ``result.length = left.length + right.length`` — one output row
    per output of the two blocks together;
  * (C1 upper)   ``∀ i < left.length, result[i] = left[i] ++ zeroRow rin`` — the
    first block's own row followed by ``rin`` zeros (the right block contributes
    nothing to the first block's outputs);
  * (C2 lower)   ``∀ i, left.length ≤ i < left.length+right.length,
    result[i] = zeroRow lin ++ right[i-left.length]`` — ``lin`` zeros then the
    second block's corresponding row (the left block contributes nothing to the
    second block's outputs).

The BEHAVIOURAL DISCRIMINATOR (the fix): the lower rows must COPY the second
block's own row into the bottom-right quadrant, not fill it with a constant. The
pre-fix behavior filled that quadrant with a constant dependent-block; the
``weak-ones-block`` rival below IS that pre-fix behavior, and on the reported
nested-combination inputs it makes independent outputs spuriously appear
coupled.

BINDER STRUCTURE. The spec predicate has FOUR input binders: ``lin`` (left
block's input width), ``rin`` (right block's input width), ``left`` (the first
matrix), ``right`` (the second matrix). All four are load-bearing and all four
are varied across the reject witnesses (see the point-spread block at the
bottom): ``lin ∈ {1,2}``, ``rin ∈ {0,1,2}``, and ``left``/``right`` each range
over several distinct shapes. The eight reject witnesses probe eight DISTINCT
input tuples (``pts=8``).

Two of those points were added by the SECOND independent audit, which found the
original six all varied ``lin``/``rin`` only in ways the rivals could not
observe: every witness touching an UPPER row used ``lin = rin``, and every point
had ``lin ≥ 1`` and ``rin ≥ 1``. So the battery pinned each pad's CONTENTS but
never its WIDTH, and never reached the degenerate width-0 block.
``weak-pads-swapped`` (pads' widths exchanged; observable only at ``lin ≠ rin``)
and ``weak-empty-pad-entry`` (a phantom entry when ``rin = 0``, correct on all of
``lin,rin ≥ 1``) close both, each measured with the full six-build discrimination
set below.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling notes that its
    inputs are pure ``PSeq`` values carrying no heap permission, so its
    frame-mutation class is already vacuous THERE; on this referentially
    transparent carrier it is doubly so — ``left``/``right`` are immutable
    values, there is no ``mut`` input binder, no aliasing, and no read-only cell
    to overwrite. No substitute probe is fabricated (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by structural equations over the two input matrices (length +
    per-row concatenation with ``zeroRow``). There is no opaque answer key an
    implementation could echo — producing each row from its own block IS doing
    the work. In its place the battery carries honest cheapest-implementation
    POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: a constant dependent-block in the bottom-right
    quadrant (the pre-fix bug); dropping the first lower row; reversing the second
    block's row order; leaking the first block's row into the bottom-left
    quadrant (should be zeros); and putting a constant into the TOP-right quadrant
    (should be zeros — this last one attacks C1, which the nagini rivals left
    untouched, see ``assessment``); the two pads' WIDTHS exchanged (visible only
    at ``lin ≠ rin``); and a phantom pad entry at the degenerate ``rin = 0``
    boundary (correct everywhere else on the domain).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that assumes the spec predicate at ground
inputs, instantiates the offending universally-quantified clause at one concrete
index (or destructs the length clause), reduces the implementation INSIDE the
resulting hypothesis, and closes by ``simp``. Each witness binds NOTHING in its
head (all inputs are ground list literals), so there are no hypotheses whose
consistency could be in question.

The witness asserts nothing about either implementation's VALUE — see the
AUDIT REPAIR note on the scaffolds below for why an earlier ``have himpl :
implementation_direct_sum ... = <literal>`` formulation made all six rejections
hollow, and how the current shape was measured to track the claim instead. On
the frozen solution ``simp`` PROVES the instantiated spec equation, leaving
``h : True ⊢ False`` (``unsolved goals``); on each rival it REFUTES the same
equation and closes the goal.

Every case was re-checked by the SECOND independent audit with six real ``lake env
lean`` builds apiece, using two instruments rather than one, because the cruder of
the two carries no information here:

  * TYPE-REVEAL (decisive). Force the closing hypothesis's type into view with
    ``exact (h : Nat)``. Gold prints ``h has type True`` — ``simp`` PROVED the
    spec equation for the frozen impl — while the rival prints ``No goals to be
    solved``, i.e. ``simp`` had already closed the goal by REFUTING it. Measured on
    all eight cases.
  * CONCRETE FLIP (decisive). Assert the spec's own equation at the same index as a
    standalone claim. It VERIFIES on gold (exit 0) and FAILS on every rival with
    ``unsolved goals ⊢ False`` (exit 1): the exit codes invert with the claim, which
    is what the forgery test demands.
  * NAIVE FLIP (rejected as evidence). Merely dropping the ``¬`` from the witness
    head fails on BOTH sides with the byte-identical ``Tactic `introN` failed``,
    because ``rintro`` then has nothing to introduce — the scaffold breaks before
    the claim is ever consulted. An earlier note in this file cited that
    experiment as if it discriminated; it does not, and the two instruments above
    are what the discrimination actually rests on.

Also measured: the reduction set is minimal-ish and load-bearing. Dropping
``pure, Id.instMonad`` breaks the rival build on all eight cases; dropping
``List.range'`` breaks it on four (the nested-``if`` shapes). And a
value-identical impl (an unused extra ``let``) VERIFIES while its witness FAILS
against it, so the witness reports a value divergence, not a syntactic edit.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
combinator that mis-places one of the two blocks, so on the reported nested
combination the emitted correlation matrix has a True where an independent
output/input pair demands False (or vice versa), and the F2P expected matrices
(the nested-combination cases the fix adds) would mismatch — so the faithful
patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed operation is modeled deeply); the axiom lane belongs to
G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-12907"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The per-row construction of the impl loop body. The two `let` lines choose the
# left-quadrant and right-quadrant contents for row `i`; the append line records
# the row. Every impl reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_I_CLEFT = "    let cleftRow := if i < lout then left.getD i [] else zeroRow lin"
_I_CRIGHT = ("    let crightRow := if lout ≤ i then right.getD (i - lout) [] "
             "else zeroRow rin")
_I_APPEND = "    result := result ++ [cleftRow ++ crightRow]"
_I_NOUTP = "  let noutp := lout + rout"

# The frozen proof's intro line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro lin rin left right hleft hright"

# Frozen proof anchors used by the branch-reorder positive to re-prove for the
# reshaped (single-`if`, lower-branch-first) impl. Each lies wholly inside
# `-- proof-start`/`-- proof-end`, so same_spec is untouched and the
# `correct_direct_sum` STATEMENT stays byte-identical; no new axiom/theorem.
_P_IMPLEQ = (
    "  have impl_eq : implementation_direct_sum lin rin left right =\n"
    "      (List.range (left.length + right.length)).map (fun i =>\n"
    "        (if i < left.length then left.getD i [] else zeroRow lin) ++\n"
    "        (if left.length ≤ i then right.getD (i - left.length) [] "
    "else zeroRow rin)) := by")
_P_B1 = "    rw [if_pos hi, if_neg (by omega)]"
_P_B2 = "    rw [if_neg (by omega), if_pos hle]"

# The WHOLE frozen impl region body, and the `impl_eq` proof block that reduces
# the `Id.run do` loop to a `List.range ... |>.map`. The loop-free positive added
# by the audit replaces both: with the impl already in map form, `impl_eq` is
# `unfold; rfl` and the whole `key`-lemma loop-reduction becomes unnecessary.
_I_REGION = (
    "-- impl-start\n"
    "def implementation_direct_sum\n"
    "    (lin rin : Nat) (left right : List (List Nat)) : List (List Nat) "
    ":= Id.run do\n"
    "  let lout := left.length\n"
    "  let rout := right.length\n"
    "  let noutp := lout + rout\n"
    "  let mut result : List (List Nat) := []\n"
    "  for i in [0:noutp] do\n"
    "    let cleftRow := if i < lout then left.getD i [] else zeroRow lin\n"
    "    let crightRow := if lout ≤ i then right.getD (i - lout) [] "
    "else zeroRow rin\n"
    "    result := result ++ [cleftRow ++ crightRow]\n"
    "  return result\n")
_I_REGION_MAP = (
    "-- impl-start\n"
    "def implementation_direct_sum\n"
    "    (lin rin : Nat) (left right : List (List Nat)) : List (List Nat) :=\n"
    "  (List.range (left.length + right.length)).map (fun i =>\n"
    "    (if i < left.length then left.getD i [] else zeroRow lin) ++\n"
    "    (if left.length ≤ i then right.getD (i - left.length) [] "
    "else zeroRow rin))\n")
_P_IMPLEQ_BODY = (
    "    unfold implementation_direct_sum Id.run\n"
    "    simp only [Std.Range.forIn_eq_forIn_range', Std.Range.size, "
    "Nat.div_one]\n"
    "    rw [key]\n"
    "    simp only [List.nil_append, List.range_eq_range', "
    "Nat.add_sub_cancel]\n"
    "    rfl")


# ---------------------------------------------------------------------------
# witness scaffolds.
#
# AUDIT REPAIR (2026-08-13). The scaffolds these replace opened with a standalone
# `have himpl : implementation_direct_sum ... = <literal> := by simp [...]; rfl`
# that asserted the RIVAL's concrete output, and only then instantiated the
# offending clause. Both halves of the discrimination check were decided by that
# `have`, not by the spec: on the frozen solution the build died at the `himpl`
# line with `Tactic 'rfl' failed: ... pure [[0, 0, 0]] is not definitionally
# equal to ... [[0, 1, 1]]` — a report that the two IMPLS differ, which is
# exactly the inference the witness rule exists to replace. Re-measured with the
# mandatory flipped-claim experiment (attack B'): asserting the OPPOSITE of the
# witness (dropping the `¬`, i.e. claiming the spec HOLDS at that input) failed
# on the frozen solution at the SAME line with the SAME `rfl` error, the flipped
# claim's own `introN` failure appearing only afterwards as a second diagnostic.
# So gold's exit code was reached before the claim was ever consulted, and the
# gate would have recorded `rejected` for a witness asserting gold is CORRECT
# there. Measured on all six cases, 24 real builds.
#
# SECOND AUDIT on that last experiment: the `¬`-dropping flip is not by itself
# evidence in EITHER direction. On the CURRENT scaffold it fails identically on
# gold and on the rival (`Tactic `introN` failed`, since `rintro` then has nothing
# to introduce), so it distinguishes nothing; above, it appeared to carry a
# verdict only because the old `himpl` line failed before it. The current shape's
# discrimination was therefore re-established with two sharper instruments —
# type-reveal (`h has type True` on gold vs `No goals to be solved` on the rival)
# and a concrete flipped EQUATION (verifies on gold, `⊢ False` on the rival). See
# the WITNESSES section of the module docstring; measured on all eight cases.
#
# The repair drops the value assertion entirely: the offending clause is
# instantiated at a concrete index and the implementation is reduced INSIDE the
# resulting hypothesis. `simp` then either refutes the hypothesis, closing the
# goal (the rival), or PROVES the spec equation, leaving `h : True ⊢ False`
# (gold). That makes the gold-side failure track the claim: it is now `unsolved
# goals` with `h : True` — simp discharged the spec's own equation for the frozen
# impl — while the flipped claim fails with a different error entirely. Verified
# on all six cases with real builds: rival exit 0, gold exit 1 with `h : True`,
# flipped-claim-on-gold exit 1 with a DIFFERENT first error.
#
# `pure, Id.instMonad` and `List.range'` are load-bearing in the reduction set.
# Without the first pair the `Id.run` wrapper survives as `pure [...]` and simp
# cannot see through it to the list; without `List.range'` a nested-`if` loop
# body leaves an unreduced `forIn (List.range' 0 n)` term in the hypothesis. Both
# were established by build (six reduction sets tried per shape).
# ---------------------------------------------------------------------------
_RED = ("implementation_direct_sum, Id.run, Std.Range.forIn_eq_forIn_range', "
        "Std.Range.size, zeroRow, pure, Id.instMonad, List.range'")


def _w_head(lin, rin, left, right):
    return (
        f"example : ¬ problem_spec_direct_sum {lin} {rin} {left} {right}\n"
        f"    (implementation_direct_sum {lin} {rin} {left} {right}) := by\n"
        "  unfold problem_spec_direct_sum\n")


def _w_lower(lin, rin, left, right, i):
    """Refute the lower-block clause (C2) at index `i`."""
    return _w_head(lin, rin, left, right) + (
        "  rintro ⟨_, _, hlower⟩\n"
        f"  have h := hlower {i} (by decide) (by decide)\n"
        f"  simp [{_RED}] at h\n")


def _w_upper(lin, rin, left, right, i):
    """Refute the upper-block clause (C1) at index `i`."""
    return _w_head(lin, rin, left, right) + (
        "  rintro ⟨_, hupper, _⟩\n"
        f"  have h := hupper {i} (by decide)\n"
        f"  simp [{_RED}] at h\n")


def _w_len(lin, rin, left, right):
    """Refute the length clause (C0)."""
    return _w_head(lin, rin, left, right) + (
        "  rintro ⟨hlen, _, _⟩\n"
        f"  simp [{_RED}] at hlen\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_direct_sum` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-inline-row",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: drop the two named `let`
        # bindings and build each row from a single append of the two inline
        # conditionals. Definitionally identical to the frozen loop body, so the
        # frozen proof (`impl_eq`'s `rfl` + the two `rw`s) still closes — no proof
        # authoring, no helper lemma, no assumption token. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_CLEFT, ""),
            (_I_CRIGHT, ""),
            (_I_APPEND,
             "    result := result ++ [(if i < lout then left.getD i [] "
             "else zeroRow lin) ++ (if lout ≤ i then right.getD (i - lout) [] "
             "else zeroRow rin)]"),
        ),
        "rationale": "correct reshape that inlines the two per-row `let` bindings "
                     "into one append; it computes the SAME row on every input, so "
                     "C0/C1/C2 all still hold — else SPEC-TOO-STRONG. The result "
                     "is definitionally the frozen loop body, so the frozen proof "
                     "(the `impl_eq` `rfl` and the two branch `rw`s) still closes; "
                     "statement byte-identical, no new axiom/lemma. Ports the "
                     "nagini pos-expected-row-call positive (there: call the pure "
                     "row oracle directly; here the row placement IS inlined, no "
                     "separate oracle def exists on this carrier).",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-REORDER positive control: compute the whole row with a single
        # if/else that tests the LOWER case (left.length ≤ i) first, upper in the
        # else. Same values, different control-flow shape. The proof region is
        # re-proved: `impl_eq`'s map function is re-stated in the reordered shape
        # and the two per-clause `rw`s drop the now-absent conjunct. The
        # `correct_direct_sum` STATEMENT is byte-identical; no new axiom/lemma.
        # (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_CLEFT, ""),
            (_I_CRIGHT, ""),
            (_I_APPEND,
             "    let row := if lout ≤ i then zeroRow lin ++ "
             "right.getD (i - lout) [] else left.getD i [] ++ zeroRow rin\n"
             "    result := result ++ [row]"),
            (_P_IMPLEQ,
             "  have impl_eq : implementation_direct_sum lin rin left right =\n"
             "      (List.range (left.length + right.length)).map (fun i =>\n"
             "        if left.length ≤ i then zeroRow lin ++ "
             "right.getD (i - left.length) []\n"
             "        else left.getD i [] ++ zeroRow rin) := by"),
            (_P_B1, "    rw [if_neg (by omega)]"),
            (_P_B2, "    rw [if_pos hle]"),
        ),
        "rationale": "branch-REORDER positive control: the lower case is tested "
                     "first in a single row conditional, upper in the else — "
                     "identical values, different control flow. A faithful reshape "
                     "MUST verify, else SPEC-TOO-STRONG. Re-proved by re-stating "
                     "`impl_eq`'s map function in the reordered shape and dropping "
                     "the now-absent branch from each per-clause `rw` (statement "
                     "byte-identical, no new axiom/lemma). Ports nagini's "
                     "pos-branch-reorder.",
    },
    {
        "id": "pos-loopfree-map",
        "kind": "soundness",
        "expect": "verify",
        # ADDED by the independent audit. The two positives above both KEEP the
        # frozen `Id.run do` ranged-`for` loop and only rearrange its body, and
        # `pos-inline-row` is definitionally the frozen body — so neither tests
        # whether the spec admits an impl of a genuinely different SHAPE. This one
        # abandons the loop entirely for a loop-free
        # `(List.range (lout + rout)).map`, which changes the impl's whole
        # elaboration: the `key` loop-reduction lemma in the frozen proof becomes
        # dead and `impl_eq` collapses to `unfold; rfl`. Same values on every
        # input, so it MUST verify. (Verified: real build, exit 0.)
        "module": _swaps(
            _BASE,
            (_I_REGION, _I_REGION_MAP),
            (_P_IMPLEQ_BODY,
             "    unfold implementation_direct_sum\n    rfl"),
        ),
        "rationale": "loop-free positive control: the ranged `for`/`Id.run do` "
                     "accumulator is replaced by a direct "
                     "`(List.range (left.length + right.length)).map` over the "
                     "same per-row expression — identical values on every input, "
                     "but a different impl SHAPE rather than a rearrangement of "
                     "the frozen loop body (unlike the two positives above, one of "
                     "which is definitionally the frozen body). A faithful reshape "
                     "MUST verify, else SPEC-TOO-STRONG. Re-proved inside the proof "
                     "region by collapsing `impl_eq` to `unfold "
                     "implementation_direct_sum; rfl` (the frozen `key` "
                     "loop-reduction lemma is simply unused); statement "
                     "byte-identical, no new axiom/lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries only the rectangularity
    # preconditions, so the nagini precondition-admission self-call re-expresses
    # as: discharge the spec predicate by evaluation at a concrete 2×2 direct-sum
    # of two 1×1 dependent blocks (the smallest F2P-shaped combination) as a
    # `have`, then close the frozen obligation verbatim. Nothing is assumed: no new
    # declaration, statement byte-identical, ground instance is a `have` prepended
    # to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_direct_sum 1 1 [[1]] [[1]]\n"
            "      (implementation_direct_sum 1 1 [[1]] [[1]]) := by\n"
            "    have himpl : implementation_direct_sum 1 1 [[1]] [[1]] "
            "= [[1, 0], [0, 1]] := by\n"
            "      simp [implementation_direct_sum, Id.run, "
            "Std.Range.forIn_eq_forIn_range', Std.Range.size, zeroRow]\n"
            "      rfl\n"
            "    rw [himpl]\n"
            "    refine ⟨by decide, ?_, ?_⟩\n"
            "    · intro i hi\n"
            "      simp only [List.length_cons, List.length_nil] at hi\n"
            "      interval_cases i <;> decide\n"
            "    · intro i hle hlt\n"
            "      simp only [List.length_cons, List.length_nil] at hle hlt\n"
            "      interval_cases i <;> decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the smallest F2P-shaped "
                     "combination (a 2×2 direct sum of two 1×1 dependent blocks, "
                     "producing the diagonal [[1,0],[0,1]]) by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable at "
                     "exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, ground instance is a `have` in the "
                     "existing tactic body. Ports nagini's admiss-f2p-grid.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: constant dependent-block in the bottom-right quadrant ----
    {
        "id": "weak-ones-block",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: fill the bottom-right quadrant with a CONSTANT
        # dependent block (all ones) instead of copying the second block's own row.
        "module": _swap(
            _BASE, _I_CRIGHT,
            "    let crightRow := if lout ≤ i then List.replicate rin 1 "
            "else zeroRow rin"),
        "refinement": "this IS the pre-fix behavior: the bottom-right quadrant is "
                      "set to a constant all-dependent block instead of the second "
                      "block's own correlation rows. A faithful real patch keeping "
                      "the constant block makes every output of the second block "
                      "appear dependent on every one of its inputs, so a nested "
                      "combination whose second block is itself separable is "
                      "reported as fully coupled — exactly the reported defect. The "
                      "F2P nested-combination cases assert the correct "
                      "block-diagonal, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C2 (lower): the spec pins "
                     "`zeroRow lin ++ right[i-left.length]` but the rival emits "
                     "`zeroRow lin ++ replicate rin 1`, which differ whenever the "
                     "second block's row has any 0 entry. Refuted at a lower row "
                     "with right=[[0,0]] (all-independent), rin=2.",
        "witness": _w_lower(1, 2, "[]", "[[0,0]]", 0),
    },

    # ---- drop the first lower row to all-zeros ----
    {
        "id": "weak-firstrow-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every lower row EXCEPT the first (i == left.length), which is
        # blanked to all zeros instead of the second block's first row.
        "module": _swap(
            _BASE, _I_CRIGHT,
            "    let crightRow := if lout ≤ i then (if i = lout then zeroRow rin "
            "else right.getD (i - lout) []) else zeroRow rin"),
        "refinement": "blanks the second block's FIRST output row to all-zeros "
                      "while copying the rest. A faithful patch that zeroed the "
                      "first post-left row would make the second block's first "
                      "output appear independent of ALL inputs (a wrong all-zero "
                      "separability row), so a nested combination whose second "
                      "block's first output is genuinely dependent is misreported. "
                      "The F2P matrices assert that row, so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C2 (lower) at i == left.length: the spec pins "
                     "`zeroRow lin ++ right[0]` but the rival emits "
                     "`zeroRow lin ++ zeroRow rin`, differing whenever right[0] has "
                     "a 1. Refuted at right=[[1],[0]] (first row dependent), the "
                     "single-row divergence violating the ∀-quantified clause.",
        "witness": _w_lower(1, 1, "[]", "[[1],[0]]", 0),
    },

    # ---- reverse the second block's row order ----
    {
        "id": "weak-reverse-rows",
        "kind": "uniqueness",
        "expect": "reject",
        # Copies the second block but with its ROWS reversed
        # (right[rout-1-(i-lout)] instead of right[i-lout]).
        "module": _swap(
            _BASE, _I_CRIGHT,
            "    let crightRow := if lout ≤ i then right.getD "
            "(rout - 1 - (i - lout)) [] else zeroRow rin"),
        "refinement": "copies the second block but with its output rows REVERSED. "
                      "Equal to gold only when that block's row sequence is a "
                      "palindrome. A faithful patch flipping the second block's row "
                      "order permutes which of its outputs each row describes, so a "
                      "nested combination reports the second block's dependence "
                      "pattern transposed — the F2P matrices pin the exact "
                      "row-to-output correspondence, so the faithful patch would "
                      "NOT resolve.",
        "rationale": "REJECT from C2 (lower): the spec pins "
                     "`zeroRow lin ++ right[i-left.length]` but the rival emits "
                     "`zeroRow lin ++ right[rout-1-(i-left.length)]`; for a "
                     "non-palindromic block (rout≥2) these disagree. Refuted at "
                     "i == left.length+1 with left=[[0]], right=[[1],[0]] (a "
                     "distinct point exercising a non-empty left block).",
        "witness": _w_lower(1, 1, "[[0]]", "[[1],[0]]", 1),
    },

    # ---- leak the first block's row into the bottom-left quadrant ----
    {
        "id": "weak-left-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual of the gold bug: lower rows put the first block's row into the
        # bottom-LEFT quadrant (should be zeros) then the second block's row.
        "module": _swap(
            _BASE, _I_CLEFT,
            "    let cleftRow := if i < lout then left.getD i [] "
            "else left.getD (i - lout) []"),
        "refinement": "the dual of the gold bug: the bottom-left quadrant carries "
                      "the first block's row (should be zeros) then the correct "
                      "second-block row. A faithful patch leaving that quadrant "
                      "non-zero makes the second block's outputs spuriously depend "
                      "on the FIRST block's inputs — a false coupling in the "
                      "bottom-left quadrant, which the F2P matrices require to be "
                      "all-independent, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C2 (lower): the spec pins "
                     "`zeroRow lin ++ right[i-left.length]` but the rival emits "
                     "`left[i-left.length] ++ right[i-left.length]`; the bottom-left "
                     "block differs from `zeroRow lin` whenever that left row has a "
                     "1. Refuted at left=[[1,0]], right=[[1]], lin=2 (the only "
                     "witness with lin=2 and a non-empty left row).",
        "witness": _w_lower(2, 1, "[[1,0]]", "[[1]]", 1),
    },

    # ---- constant block in the TOP-right quadrant (attacks C1, upper) ----
    {
        "id": "weak-upper-right-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED rival (see assessment): fill the TOP-right quadrant with a constant
        # dependent block instead of zeros, so the FIRST block's outputs appear to
        # depend on the SECOND block's inputs. This is the ONLY rival attacking the
        # upper clause C1 — the nagini rivals all kept the upper block correct, but
        # the coverage tool requires every top-level clause attacked.
        "module": _swap(
            _BASE, _I_CRIGHT,
            "    let crightRow := if lout ≤ i then right.getD (i - lout) [] "
            "else List.replicate rin 1"),
        "refinement": "fills the TOP-right quadrant with a constant all-dependent "
                      "block instead of zeros. A faithful patch initializing that "
                      "quadrant non-zero makes the first block's outputs spuriously "
                      "depend on the second block's inputs — a false coupling in "
                      "the top-right quadrant, which the F2P nested-combination "
                      "matrices require to be all-independent, so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C1 (upper): the spec pins "
                     "`left[i] ++ zeroRow rin` for i < left.length, but the rival "
                     "emits `left[i] ++ replicate rin 1`, differing whenever rin>0. "
                     "Refuted at an upper row i=0 with left=[[1],[0]], right=[[1]]. "
                     "This is the sole rival exercising the upper clause.",
        "witness": _w_upper(1, 1, "[[1],[0]]", "[[1]]", 0),
    },

    # ---- the two zero-pad WIDTHS swapped (observable only when lin ≠ rin) ----
    {
        "id": "weak-pads-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED by the independent audit. Every rival above pins the pad CONTENTS
        # (zeros vs a constant, or which row is copied); none pins the pad WIDTHS,
        # and each shipped witness that touches an upper row happens to use
        # lin = rin, where swapping the two `zeroRow` arguments is invisible. This
        # rival swaps them, so the top-right pad is `lin` wide and the bottom-left
        # pad is `rin` wide: every emitted row still has width lin+rin, so the row
        # LENGTHS are unchanged and C0 still holds — the divergence is observable
        # only at an input with lin ≠ rin, which is why it needs its own witness
        # point.
        "module": _swaps(
            _BASE,
            (_I_CLEFT,
             "    let cleftRow := if i < lout then left.getD i [] "
             "else zeroRow rin"),
            (_I_CRIGHT,
             "    let crightRow := if lout ≤ i then right.getD (i - lout) [] "
             "else zeroRow lin"),
        ),
        "refinement": "swaps the two blocks' pad WIDTHS: the first block's outputs "
                      "get a pad sized by their OWN input width instead of the "
                      "second block's, and vice versa. A faithful patch sizing each "
                      "zero pad from the wrong block emits a matrix whose columns no "
                      "longer correspond to the concatenated inputs — for a "
                      "combination whose two blocks have different input widths the "
                      "reported dependence of each output is read off at shifted "
                      "column positions, so the F2P nested-combination matrices "
                      "(whose sub-blocks have unequal widths) mismatch and the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C1 (upper): the spec pins `left[i] ++ zeroRow rin` "
                     "but the rival emits `left[i] ++ zeroRow lin`; these differ "
                     "exactly when lin ≠ rin. Refuted at an upper row i=0 with "
                     "lin=1, rin=2, left=[[1]], right=[[0,0]] — the only witness "
                     "point in the battery with lin ≠ rin, which is what makes this "
                     "rival observable at all.",
        "witness": _w_upper(1, 2, "[[1]]", "[[0,0]]", 0),
    },

    # ---- degenerate rin = 0: a phantom entry where the pad is empty ----
    {
        "id": "weak-empty-pad-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED by the independent audit. Every witness point above has lin ≥ 1 and
        # rin ≥ 1, so nothing in the battery exercises a block with NO inputs — the
        # degenerate width-0 boundary, where `zeroRow 0 = []` and the spec demands
        # the pad contribute nothing at all. This rival agrees with the frozen impl
        # on every input with rin > 0 and diverges only at rin = 0, emitting a
        # phantom dependent entry where the spec requires an empty pad. A rival
        # correct on all of lin,rin ≥ 1 is the sharpest partial-domain probe the
        # carrier allows.
        "module": _swap(
            _BASE, _I_CRIGHT,
            "    let crightRow := if lout ≤ i then right.getD (i - lout) [] "
            "else (if rin = 0 then [1] else zeroRow rin)"),
        "refinement": "emits a phantom dependent entry in the top-right pad exactly "
                      "when the second block has NO inputs. A faithful patch that "
                      "appended an entry for an input-less block would widen every "
                      "upper row past the true input count, reporting a dependence "
                      "on a column that does not exist; the F2P matrices pin the "
                      "column count to the combination's real input total, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C1 (upper) at the degenerate boundary rin=0: the "
                     "spec pins `left[i] ++ zeroRow 0 = left[i]` but the rival emits "
                     "`left[i] ++ [1]`. Refuted at i=0 with lin=1, rin=0, "
                     "left=[[1]], right=[] — the only witness point in the battery "
                     "with a width-0 block, and one where the rival is correct on "
                     "the whole rest of the domain.",
        "witness": _w_upper(1, 0, "[[1]]", "[]", 0),
    },

    # ---- short result: emit one fewer output row (attacks C0, length) ----
    {
        "id": "weak-short-length",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit only the first block's outputs (noutp = lout), dropping the second
        # block's rows entirely — the result is shorter than left.length +
        # right.length. Attacks the length clause C0.
        "module": _swap(_BASE, _I_NOUTP, "  let noutp := lout"),
        "refinement": "emits one output row per output of the FIRST block only, "
                      "dropping the second block's outputs entirely. A faithful "
                      "patch producing a matrix with too few rows returns a "
                      "separability matrix of the wrong shape, so the caller reads "
                      "back fewer output rows than the combination has — the F2P "
                      "matrices pin the full row count, so the faithful patch would "
                      "NOT resolve.",
        "rationale": "REJECT from C0 (length): the spec pins "
                     "`result.length = left.length + right.length` but the rival "
                     "produces only `left.length` rows. Refuted at left=[[1]], "
                     "right=[[1]] where the result has length 1 ≠ 2.",
        "witness": _w_len(1, 1, "[[1]]", "[[1]]"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness/partial-domain rivals) plus an EMPTY
# AXIOM lane. This bundle models the SAME single purely-functional core (the
# block-diagonal combinator) and re-expresses every sibling case; it ADDS two
# rivals the sibling did not need, to satisfy this backend's per-clause coverage
# requirement, plus one positive added by the first independent audit and two
# rivals added by the second. This bundle carries 12 cases (3 soundness,
# 1 admissibility, 8 rivals). Every sibling case is recorded below.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-expected-row-call        -> pos-inline-row            RE-EXPRESSED
#   pos-branch-reorder           -> pos-branch-reorder        PORTED (re-proved)
#   (none)                       -> pos-loopfree-map          ADDED (audit)
#   admiss-f2p-grid              -> admiss-ground-grid        RE-EXPRESSED
#   weak-prepatch-ones-block     -> weak-ones-block           PORTED
#   weak-firstrow-dropped        -> weak-firstrow-dropped     PORTED
#   weak-reverse-right-rows      -> weak-reverse-rows         PORTED
#   weak-left-leak-block         -> weak-left-leak            PORTED
#   (none)                       -> weak-upper-right-leak     ADDED (attacks C1)
#   (none)                       -> weak-pads-swapped         ADDED (audit 2: lin≠rin)
#   (none)                       -> weak-empty-pad-entry      ADDED (audit 2: rin=0)
#   (none)                       -> weak-short-length         ADDED (attacks C0)
#   AXIOM_TESTS (0)              -> (none)                    DROPPED (G-AX)
#
# RE-EXPRESSED (pos-inline-row): the sibling's structurally-different positive
#   calls the pure row oracle `expected_row(...)` directly. This carrier has no
#   separate row-oracle def — the row placement is inlined in the loop body — so
#   the analogous "structurally different but correct" reshape inlines the two
#   `let` bindings into a single append. It is definitionally the frozen body, so
#   the frozen proof still closes (verified with a real build).
# RE-EXPRESSED (admiss-ground-grid): the sibling asserts is_grid holds of a
#   concrete 2×2 grid (its precondition is a grid-shape predicate). This bundle's
#   precondition is rectangularity (∀ r ∈ left/right, length = lin/rin), which is
#   not the interesting admission target; the honest analogue is to discharge the
#   POSTCONDITION at the smallest F2P-shaped combination (a 2×2 direct sum) as a
#   `have`, proving the modeled behavior is satisfiable at a normal input, then
#   close the frozen obligation verbatim.
# ADDED (pos-loopfree-map): the two ported positives both KEEP the frozen
#   `Id.run do` ranged-`for` loop and only rearrange its body, and pos-inline-row
#   is definitionally the frozen body — so neither establishes that the spec
#   admits a different impl SHAPE, only a different spelling of the same one. The
#   audit's loop-free `List.range ... |>.map` reshape does (its proof drops the
#   frozen `key` loop-reduction lemma entirely) and it verifies, so the soundness
#   lane now covers shape as well as spelling.
# ADDED (weak-upper-right-leak, weak-short-length): the four nagini rivals all
#   keep the length correct (P1/shape) AND the upper block correct, attacking only
#   the lower-block clause. This backend's coverage tool requires EVERY top-level
#   postcondition clause to be attacked by some reject rival, and the spec has
#   three: C0 (length), C1 (upper rows), C2 (lower rows). So two rivals are added
#   — a top-right constant leak (attacks C1) and a short-length impl (attacks C0)
#   — each with the same refinement structure (a faithful patch mis-shaping the
#   matrix would fail the F2P). They are not fabricated for an unmodeled behavior;
#   they attack real, load-bearing clauses of the SAME modeled spec that the
#   nagini rivals happened not to target individually.
# VACUOUS (frame/permission mutation): the sibling itself notes this class is
#   vacuous on its pure PSeq carrier (no heap permission to overwrite); on this
#   referentially transparent carrier it is doubly vacuous — no `mut` input, no
#   aliasing, no read-only cell. No substitute probe is fabricated.
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT input tuples
# (pts=8):
#   (lin,rin,left,right) =
#     (1,2,[],[[0,0]])          weak-ones-block        C2
#     (1,1,[],[[1],[0]])        weak-firstrow-dropped  C2
#     (1,1,[[0]],[[1],[0]])     weak-reverse-rows      C2
#     (2,1,[[1,0]],[[1]])       weak-left-leak         C2
#     (1,1,[[1],[0]],[[1]])     weak-upper-right-leak  C1
#     (1,2,[[1]],[[0,0]])       weak-pads-swapped      C1  (the only lin ≠ rin
#                                                           point at an UPPER row)
#     (1,0,[[1]],[])            weak-empty-pad-entry   C1  (the only width-0 block)
#     (1,1,[[1]],[[1]])         weak-short-length      C0
#   Across them lin ∈ {1,2}, rin ∈ {0,1,2}, and left/right each take several
#   distinct shapes (empty, singleton, two-row), so no input binder is pinned.
#
#   The variation is MEANINGFUL, not two spellings of one point, and the last two
#   entries are why. Before they were added the tool already reported binders=4 /
#   pts=6 "ok", but every witness that instantiated the UPPER clause had lin = rin
#   and every point had both widths ≥ 1 — so a rival that exchanged the two pads'
#   widths, or that misbehaved only at a width-0 block, was unobservable at all
#   six points while still being a genuinely wrong combinator. A clean coverage
#   report is advisory: it counts distinct tuples, not whether varying a binder
#   changes any clause's verdict.
#
# AUDIT PROBES, recorded but NOT shipped as cases. Two independent audits wrote
# further wrong impls and further correct reshapes and built each against the
# frozen spec, to test the spec from both directions beyond what the shipped cases
# reach. Two of the SPEC-TOO-WEAK probes are no longer listed here because the
# second audit PROMOTED them to shipped cases (weak-pads-swapped and
# weak-empty-pad-entry): each was found to close a real observability gap rather
# than merely to re-confirm the spec, so each was given the full six-build
# discrimination treatment and landed.
#
# SPEC-TOO-WEAK probes (new wrong impls; every one was REJECTED, exit 1 — no
# spec hole found). Each attacks something the shipped rivals leave alone:
#   - the lower rows read `right.getD (i - lout + 1)` (off-by-one INTO the second
#     block, vs the shipped reversal of it);
#   - one EXTRA output row (`noutp := lout + rout + 1`) — the C0 length clause
#     attacked in the opposite direction from the shipped short-length rival;
#   - the FIRST block's rows reversed — C1 attacked by a permutation rather than
#     by the shipped constant fill;
#   - the two quadrants emitted right-then-left (block ANTI-diagonal);
#   - every entry zeroed (correct shape, all-independent matrix).
# For each, the corresponding witness was also built against the rival and holds
# (exit 0), so each rejection is attributable to the spec and not to a tactic gap.
#
# A deliberate NEGATIVE control was run alongside them: an impl differing from
# the frozen one only by an unused `let _pad := (0:Nat)` (value-identical). It
# VERIFIED (exit 0) and its witness FAILED against it (exit 1) — confirming the
# witness shape reports a value divergence rather than any syntactic edit, which
# is the property attack C turns on.
#
# SPEC-TOO-STRONG probes (new correct reshapes; all VERIFIED, exit 0 — no
# soundness hole). Each abandons the `Id.run do` loop the shipped positives keep,
# so they exercise genuinely different impl shapes:
#   - a loop-free `(List.range (left.length + right.length)).map (fun i => ...)`,
#     whose `impl_eq` collapses to `unfold; rfl` (since shipped as
#     pos-loopfree-map);
#   - the same map with the row extracted into a named impl-region helper `def`
#     (`dsRow`), closed by `unfold implementation_direct_sum dsRow; rfl`;
#   - furthest from the frozen form: `left.map (fun r => r ++ zeroRow rin) ++
#     right.map (fun r => zeroRow lin ++ r)` — no range, no index arithmetic, the
#     two blocks built independently and concatenated. Its proof shares no tactic
#     with the frozen one (per-clause `List.getElem?_append_left/right` plus a
#     case split on the row lookup) and it verifies, which is the strongest
#     available evidence that the spec pins the block-diagonal VALUE rather than
#     the frozen impl's shape.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the combinator is modeled deeply), so there is nothing to probe and the
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
