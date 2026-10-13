"""properties.py — G-PBT falsification battery for sympy__sympy-15349 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct toOrientationMatrix`` obligation survives with a
byte-identical STATEMENT) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  toOrientationMatrix (a b c d : Rat) (v : Option (Rat × Rat × Rat))
      return (out : List (List Rat))
    require a^2 + b^2 + c^2 + d^2 ≠ 0
    ensures out = rotMatrix a b c d v          ← LOAD-BEARING

``rotMatrix`` is a total, fully-unfolded ``def`` over the method's own
arguments: a scaling factor ``sFactor`` (reciprocal of the sum of squared
components) times an explicit closed-form rational function for each of the nine
3×3 entries, and — with a translation point — the 4×4 homogeneous extension
whose fourth column carries the point under the linear action of the block and
whose bottom row is ``[0,0,0,1]``. It is GROUNDED in the input (a function of
``a,b,c,d,v``, not an opaque answer key), so returning it directly IS the correct
value (it doubles as the cheapest honest positive control) and there is no
"wrong echo" to build — the ungrounded-oracle-echo class is N/A.

The wrong pre-change behaviour the fix repairs is the SIGN of the ``b*a`` term
in the row-1/column-2 entry ``m12``: the pre-fix source computes
``2*s*(c*d + b*a)`` where the orientation-preserving convention requires
``2*s*(c*d - b*a)``. On the issue's X-rotation witness the reported entry gets
``+sin`` where ``-sin`` is required. The postcondition must REJECT that sign (the
frozen ``Solution_prepatch.lean`` carries exactly it and its ``prove_correct``
fails — G-DIFF), and every rival below that reintroduces ``+b*a`` (or permutes /
transposes the off-diagonals so the negative sign lands on the wrong entry) must
be rejected; a verifying rival would be SPEC-TOO-WEAK, admitting a buggy patch
that does NOT resolve ``test_quaternion_conversions``.

FIVE INPUT BINDERS of the post-image: ``a, b, c, d`` (the four components) and
``v`` (the optional translation point — ``none`` selects the 3×3 branch, ``some``
the 4×4). The reject witnesses vary all five: the components range over several
nonzero values (so the ``b*a`` term is genuinely observable and the off-diagonal
entries are mutually distinct), and ``v`` ranges over both ``none`` and ``some``
so the 4×4 translation-column clause is probed and a rival that mishandled only
the homogeneous branch could not slip past.

WITNESS mechanics — THE Rat DECIDABLE BOUNDARY. The spec is a ``method``
contract, not a bare predicate. Velvet's tester machinery is available, but its
inner postcondition check is a ``decide`` over ``Rat`` equality, and ``decide``
reduces the ``Decidable`` instance rather than computing the value — over ``Rat``
it gets STUCK at ``(Rat.mul _ _).num`` and never yields ``isTrue``/``isFalse``
(measured on this bundle: ``toOrientationMatrixTester 1 1 0 0 none`` leaves
``decide`` stuck). So each witness states the refutation DIRECTLY over the
method's own executable ``.run``:

    (toOrientationMatrix <args>).run ≠ DivM.res (rotMatrix <args>)

``simp only`` unfolds the (straight-line) method executable and the pure
``rotMatrix``/``sFactor`` to a single matrix (dis)equality; ``DivM.res.injEq``
peels the monad constructor; ``simp [Rat.mul_def, Rat.add_def, Rat.sub_def,
Rat.normalize]`` (the guide's Rat-unfolding recipe — ``decide``/``rfl`` alone are
stuck on ``Rat``) reduces the differing entry to a concrete rational
(dis)equality, closed by ``exact absurd heq (by decide)``. Against the frozen
solution the SAME witness FAILS: gold's executable reduces to ``DivM.res
(rotMatrix <args>)`` definitionally, so the disequality is unprovable (``simp``
makes no progress / no contradiction) — exactly the discriminator half the gate
requires. No ``sorry``/``admit``/``native_decide``/``axiom`` is used, and every
witness is stated at fully concrete literal inputs (binds nothing), so the
binder-consistency probe is trivially satisfied.

Because the gold impl is STRAIGHT-LINE (no ``while`` loop), the witness needs no
loop-free reshaping of the rival: each rival edits only the closed-form entry (or
the branch assembly) inside the impl region, and its ``.run`` unfolds under
``simp only`` directly. The frozen spec is untouched by every case.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * VALUE / prepatch-sign — the load-bearing discriminator. Ported as
    ``rej-prepatch-sign-block`` (the exact ``+b*a`` sign the gold diff corrects,
    in the 3×3 block entry) and carried into the 4×4 branch by
    ``rej-translation-column`` (the block is correct but the translation column
    reuses a wrongly-signed copy — the SECOND load-bearing consequence, the
    inherited fourth-column entry).
  * STRUCTURAL / off-diagonal-permutation — the sibling's swap and transpose
    transcription rivals. Ported as ``rej-swap-cd`` (the negative sign put on the
    lower off-diagonal instead of the upper) and ``rej-transpose-3x3`` (the whole
    block returned transposed, which for a proper rotation is the inverse
    rotation). Both are invisible to any abstraction checking only the diagonal
    or a value multiset.
  * PARTIAL-DOMAIN — the sibling's a==0 rival: correct sign only when a==0, else
    the buggy ``+b*a``. Ported as ``rej-partial-domain-a0``; refuted on the a≠0
    sub-domain (the issue witness has a = cos(x/2) ≠ 0), demonstrating the clause
    pins the WHOLE domain, not a sampled subset.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling class
    exists because a read-only input may carry a fractional heap permission an
    impl can overwrite. Lean and Velvet are referentially transparent: every
    parameter (``a,b,c,d,v``) is an immutable value, this bundle declares NO
    ``mut`` binder among the inputs, there is no heap and no aliasing. There is no
    read-only input to mutate and no permission system to trip. Reported N/A, not
    fabricated.
  * DIVERGENCE / NON-TERMINATION — nothing shippable here, but NOT because the
    class is unwritable on this surface. NOTE ON A CHANGED PREMISE: this entry
    previously reasoned from ``set_option loom.semantics.termination "total"``,
    which is what the bundle carried at the time the battery was written and
    which made the "postcondition claimed only of terminating runs" vacuity route
    apply. The bundle now carries ``"total"`` (line 4 of Solution.lean), changed
    by a corpus-wide remediation outside this lane, so that route no longer
    applies and the old reasoning is superseded rather than wrong-as-authored.
    Re-measured against the semantics the bundle ACTUALLY sets, on the real
    verifier:
      - A loop with NO ``decreasing`` annotation fails at ELABORATION:
        ``error: Decreasing annotations are required in total correctness
        semantics``. So that shape is rejected — but it is also not shippable as
        a reject case, because the same elaboration error poisons the witness
        file (the witness build reports the annotation error plus ``declaration
        uses 'sorry'`` and so attributes nothing to the postcondition).
      - A loop WITH a present-but-BOGUS measure (``decreasing k`` while the body
        does ``k := k + 1``, guard ``k > 0`` never falsifiable) and the CORRECT
        return value VERIFIES (exit 0) under a bare ``loom_solve``. The same
        diverging loop with a WRONG return value is still rejected (``unsolved
        goals``), i.e. the value clause keeps its force; it is only the
        TERMINATION obligation that is not enforced - the class is INAPPLICABLE
        to this impl and CLOSED BY THE SEMANTICS against any rival that
        manufactures it. The frozen impl is LOOP-FREE (straight-line ``let``
        over immutable values, no loop and no recursion), so there is no
        control flow here to make diverge: a diverging rival cannot be obtained
        by mutating this body, it has to bring a loop of its own. When it does,
        the semantics refuse it. This bundle sets
        ``loom.semantics.termination "total"`` AND carries
        ``open TotalCorrectness``, and the ``open`` is the line that actually
        selects the semantics: both namespaces define
        ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
        ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so
        the two lines have to move together and they do here. Under the total
        scope a postcondition is claimed of ALL runs and not only of
        terminating ones, so a spliced loop owes a descent obligation
        ``measure b' < measure b``. Re-measured on this bundle with a real
        build: a ``while spin > 0 do spin := spin`` prefix carrying
        ``decreasing spin`` is REJECTED on the measure's own goal (``case
        «decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather
        than faking it is refused even earlier, by the elaborator's own check
        (``Decreasing annotations are required in total correctness
        semantics``). So divergence neither applies to this impl nor discharges
        the ``ensures`` clauses vacuously if a rival introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A: ``rotMatrix``/``sFactor`` are total,
    fully-unfolded ``def``s of the method's own arguments; the ``axioms`` region
    is empty. There is no answer key to echo. Replaced by honest cheapest /
    reshape POSITIVE CONTROLS.
  * ADMISSIBILITY — CARRIED, as ``pos-admissible-witness``. The method's one
    ``require`` (nonzero quaternion) is the reciprocal's well-posedness
    condition, exactly the repo's, so there is no PRECOND-TOO-STRONG rival to
    write in the sibling's shape. The analogue on this total carrier is a
    POSITIVE that discharges the obligation at a concrete F2P-shaped input BY
    EVALUATION, as a ``have``, before closing the frozen obligation verbatim:
    that is what the case does. It pins ``rotMatrix 1 1 0 0`` on BOTH branches
    (the 3×3 block, and the 4×4 homogeneous extension at the point (2,3,5)) to
    explicit literal matrices, so the post-image is shown INHABITED at an input
    admitted by the precondition, and shown to be the specific matrix the repo
    computes rather than merely "some" matrix. That the assert is load-bearing
    was measured: perturbing one pinned entry (the ``m12`` slot to ``+1``)
    turns the case from exit 0 to exit 1.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the matrix is
modeled DEEPLY as ``rotMatrix``; ``sFactor`` captures ``norm()**-2`` as the exact
rational ``(a²+b²+c²+d²)⁻¹`` with the square root cancelled — an R/I identity, not
a consumed axiom — see mapping.md §3). There is no axiom-soundness obligation to
probe here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15349"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- toOrientationMatrix impl region and is unique in Solution.lean (both facts
# ---- asserted at load by _swap), so every edit keeps same_spec by construction
# ---- and leaves the `prove_correct toOrientationMatrix` STATEMENT intact. ----

# The row-1/column-2 entry `m12` — the single line whose sign the gold diff
# corrects. Unique: the pure-region copy uses two leading spaces of indentation,
# the impl copy four (this anchor).
_A_M12 = "    let m12 := 2 * s * (c * d - b * a)\n"
assert _BASE.count(_A_M12) == 1, "m12 impl anchor drift"

# The lower (cd) off-diagonal `m21`.
_A_M21 = "    let m21 := 2 * s * (c * d + b * a)\n"
assert _BASE.count(_A_M21) == 1, "m21 impl anchor drift"

# The `none`-branch assembly of the 3×3 block (unique in the file).
_A_NONE = ("      | none => [[m00, m01, m02], [m10, m11, m12], "
           "[m20, m21, m22]]\n")
assert _BASE.count(_A_NONE) == 1, "none-branch anchor drift"

# The impl copy of the translation-column entry `m13` (four-space indent inside
# the `some` branch; unique — the pure-region copy has different indentation).
_A_M13 = "        let m13 := y - x * m10 - y * m11 - z * m12\n"
assert _BASE.count(_A_M13) == 1, "m13 impl anchor drift"

# The two diagonal entries whose inner sum the non-defeq positive distributes.
_A_M00 = "    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)\n"
assert _BASE.count(_A_M00) == 1, "m00 impl anchor drift"
_A_M11 = "    let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)\n"
assert _BASE.count(_A_M11) == 1, "m11 impl anchor drift"

# The nine 3×3 entry bindings, in declaration order (the whole block, unique).
_A_NINE = (
    "    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)\n"
    "    let m01 := 2 * s * (b * c - d * a)\n"
    "    let m02 := 2 * s * (b * d + c * a)\n"
    "    let m10 := 2 * s * (b * c + d * a)\n"
    "    let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)\n"
    "    let m12 := 2 * s * (c * d - b * a)\n"
    "    let m20 := 2 * s * (b * d - c * a)\n"
    "    let m21 := 2 * s * (c * d + b * a)\n"
    "    let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)\n")
assert _BASE.count(_A_NINE) == 1, "nine-entry block anchor drift"

# The impl copy of the 4×4 bottom row `[0, 0, 0, 1]` (nine-space continuation
# indent inside the `some` branch; unique — the pure-region copy is indented by
# five). The homogeneous-row rival edits this line.
_A_BOTTOM = "         [m20, m21, m22, m23], [0, 0, 0, 1]]\n"
assert _BASE.count(_A_BOTTOM) == 1, "bottom-row impl anchor drift"

# The impl-start marker line (unique); the cheapest positive replaces the whole
# entry-computation body between the markers.
_IMPL_START = "    -- impl-start\n"
_IMPL_END = "    -- impl-end"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"
assert _BASE.count(_IMPL_END) == 1, "impl-end anchor drift"

# The frozen proof body (tactic script only; elided from the spec view). Unique.
# A positive whose impl drops the intermediate `let`s (so `loom_solve` alone
# discharges the goal) retunes to `_PROOF_FLAT`; every reject rival keeps the
# frozen proof (which then fails to close — the rejection the case needs).
_PROOF_GOLD = ("prove_correct toOrientationMatrix by\n"
               "  loom_solve\n"
               "  simp_all [rotMatrix, sFactor]")
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"
_PROOF_FLAT = "prove_correct toOrientationMatrix by\n  loom_solve"

# Proof retuning for the admissibility positive. Adding an `assert` inside the
# impl region emits a SECOND goal beside the main obligation, and the two need
# different tactics on this carrier: the assert is a closed numeric claim that
# `decide +kernel` evaluates, while the main obligation still needs the frozen
# `simp_all [rotMatrix, sFactor]` (it has free `a b c d v`, on which
# `decide +kernel` errors with "Expected type must not contain free variables").
# An `all_goals first | ... | ...` alternation gives each goal the tactic that
# closes it, leaving the frozen obligation itself untouched and closed verbatim.
# Order matters and was measured: `decide +kernel` must come FIRST (leading with
# `simp_all` fails).
_PROOF_ADMISS = (_PROOF_GOLD.rsplit("\n", 1)[0]
                 + "\n  all_goals first\n"
                   "    | decide +kernel\n"
                   "    | simp_all [rotMatrix, sFactor]")


def _impl_region(new_body):
    """Return _BASE with the whole between-markers impl body replaced by
    `new_body` (which must include its own trailing newline). Used by the
    cheapest positive."""
    s = _BASE.index(_IMPL_START)
    e = _BASE.index(_IMPL_END)
    return _BASE[:s] + _IMPL_START + new_body + _BASE[e:]


# ---- witness builder. Reaches the post-image DIRECTLY over the method's own
# ---- `.run` (the tester's inner `decide` is stuck on `Rat` — see the docstring).
# ---- `simp only` unfolds the straight-line rival's executable and the pure
# ---- `rotMatrix`; `DivM.res.injEq` peels the monad constructor; the second
# ---- `simp` reduces the differing entry, closed by `absurd heq (by decide)`.
# ---- `all_goals` covers both shapes: whether the second `simp` fully derives
# ---- `False` or leaves a residual literal (dis)equality `heq`. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- masks the verdict; against gold the executable reduces definitionally to
# ---- `DivM.res (rotMatrix ...)` and the same witness FAILS. ----
def _witness(args):
    return (
        f"example : (toOrientationMatrix {args}).run\n"
        f"    ≠ DivM.res (rotMatrix {args}) := by\n"
        "  simp only [toOrientationMatrix, NonDetT.run, rotMatrix, sFactor, pure]\n"
        "  intro heq\n"
        "  simp only [DivM.res.injEq] at heq\n"
        "  simp [Rat.mul_def, Rat.add_def, Rat.sub_def, Rat.normalize] at heq\n"
        "  all_goals exact absurd heq (by decide)\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation STATEMENT and only reshapes the
    # executable surface (and, where the intermediate `let`s are dropped, retunes
    # the elided tactic body to the shape that closes for that impl).
    # =====================================================================
    {
        "id": "pos-reorder-entries",
        "kind": "soundness",
        "expect": "verify",
        # The nine entry bindings computed in REVERSED declaration order
        # (m22..m00). Each `let` is independent (none depends on another), so the
        # assembled `out` is DEFINITIONALLY identical and the frozen proof script
        # (`loom_solve; simp_all [rotMatrix, sFactor]`) closes unchanged.
        "module": _swap(
            _BASE, _A_NINE,
            "    let m22 := 1 - 2 * s * (b ^ 2 + c ^ 2)\n"
            "    let m21 := 2 * s * (c * d + b * a)\n"
            "    let m20 := 2 * s * (b * d - c * a)\n"
            "    let m12 := 2 * s * (c * d - b * a)\n"
            "    let m11 := 1 - 2 * s * (b ^ 2 + d ^ 2)\n"
            "    let m10 := 2 * s * (b * c + d * a)\n"
            "    let m02 := 2 * s * (b * d + c * a)\n"
            "    let m01 := 2 * s * (b * c - d * a)\n"
            "    let m00 := 1 - 2 * s * (c ^ 2 + d ^ 2)\n"),
        "rationale": "Computing the nine independent entry bindings in reversed "
                     "declaration order leaves the assembled `out` definitionally "
                     "identical, so `out = rotMatrix a b c d v` still holds on the "
                     "whole domain and the frozen proof script closes without "
                     "change. A correct reshape that failed to verify would mean "
                     "the postcondition is SPEC-TOO-STRONG over the order in which "
                     "the entries are bound.",
    },
    {
        "id": "pos-cheapest-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: `rotMatrix` is grounded in the arguments, so
        # returning it directly IS the correct value. No intermediate `let`s, so
        # `loom_solve` discharges the goal and the trailing `simp_all` is retuned
        # away (it would otherwise leave "no goals").
        "module": _swap(
            _impl_region("    let out := rotMatrix a b c d v\n    return out\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "rationale": "rotMatrix is GROUNDED in the arguments (a total, "
                     "fully-unfolded def), so returning it directly satisfies "
                     "`out = rotMatrix a b c d v` on the whole domain. An honest "
                     "cheapest impl MUST verify; if it cannot the postcondition is "
                     "SPEC-TOO-STRONG. Also the grounded-oracle positive control: "
                     "there is no WRONG echo because the oracle is a function of "
                     "the inputs, not an opaque answer key. The intermediate `let` "
                     "bindings are dropped, so `loom_solve` closes the goal alone "
                     "and the trailing tactic is retuned (proof body elided from "
                     "the spec view; STATEMENT unchanged).",
    },

    {
        "id": "pos-distribute-diagonal",
        "kind": "soundness",
        "expect": "verify",
        # A correct reshape that is RING-equal but NOT definitionally equal:
        # the two diagonal entries are distributed (`1 - 2*s*c^2 - 2*s*d^2`
        # instead of `1 - 2*s*(c^2 + d^2)`). Both other positives are defeq to
        # gold, so `loom_solve`/`simp_all` closes them without ever testing the
        # postcondition AS AN ALGEBRAIC CLAIM; this one does not reduce, and the
        # tactic body is retuned with `grind` to discharge the residual ring
        # identity (proof body elided from the spec view; STATEMENT unchanged).
        "module": _swap(
            _swap(
                _swap(_BASE, _A_M00,
                      "    let m00 := 1 - 2 * s * c ^ 2 - 2 * s * d ^ 2\n"),
                _A_M11, "    let m11 := 1 - 2 * s * d ^ 2 - 2 * s * b ^ 2\n"),
            _PROOF_GOLD, _PROOF_GOLD + "\n  all_goals grind"),
        "rationale": "Distributing the two diagonal entries over the inner sum "
                     "(and commuting one of them) yields values EQUAL to "
                     "rotMatrix's but not definitionally so: the goal survives "
                     "`simp_all [rotMatrix, sFactor]` as a residual ring "
                     "identity over Rat, closed by `grind`. This is the "
                     "SPEC-TOO-STRONG probe the other two positives cannot "
                     "make: both of those are defeq to the frozen impl, so they "
                     "verify by reduction alone and would still verify if the "
                     "postcondition were a syntactic rather than a semantic "
                     "equality. A faithful correct impl the spec rejected for "
                     "spelling its arithmetic differently would be a soundness "
                     "hole.",
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition is satisfiable and the obligation is
    # DISCHARGEABLE at a concrete F2P-shaped input, shown by evaluation.
    # =====================================================================
    {
        "id": "pos-admissible-witness",
        "kind": "admissibility",
        "expect": "verify",
        # The impl is the frozen one, verbatim; the only change is an `assert`
        # ahead of it pinning rotMatrix's value at a concrete admitted input on
        # BOTH branches. The frozen obligation is still closed verbatim after it
        # (see _PROOF_ADMISS: the alternation adds a branch for the assert goal
        # and leaves `simp_all [rotMatrix, sFactor]` to close the obligation).
        #
        # a=1,b=1,c=0,d=0 satisfies the `require` (1+1+0+0 = 2 ≠ 0) and is the
        # shape of the issue's own X-rotation quaternion (the component whose
        # sign the fix corrects is nonzero here: b*a = 1). At it, s = 1/2 and
        # the 3×3 block is the quarter-turn about x, whose row-1/column-2 entry
        # is -1 — the very entry the corrected clause pins. The `some` conjunct
        # additionally evaluates the homogeneous extension at the point (2,3,5),
        # so the fourth column (8, 2) and the bottom row are pinned too.
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START
                  + "    assert (with_name_prefix `admiss (\n"
                    "      rotMatrix 1 1 0 0 none = [[1, 0, 0], [0, 0, -1], "
                    "[0, 1, 0]] ∧\n"
                    "      rotMatrix 1 1 0 0 (some (2, 3, 5)) =\n"
                    "        [[1, 0, 0, 0], [0, 0, -1, 8], [0, 1, 0, 2], "
                    "[0, 0, 0, 1]]))\n"),
            _PROOF_GOLD, _PROOF_ADMISS),
        "rationale": "ADMISSIBILITY (the total-carrier analogue of "
                     "PRECOND-TOO-STRONG). The `require` is the reciprocal's "
                     "well-posedness condition — a ZERO quaternion, exactly the "
                     "input on which the repo's own reciprocal-of-the-squared-"
                     "norm divides by zero — so it cannot be weakened and there "
                     "is no PRECOND-TOO-STRONG rival to write: dropping it "
                     "would make the spec unprovable, not stronger. What CAN be "
                     "over-strong is a precondition that admits nothing useful, "
                     "and what can be vacuous is an obligation satisfiable only "
                     "abstractly. This case rules both out by EVALUATION: at "
                     "a=1,b=1,c=0,d=0 the precondition holds (sum = 2 ≠ 0) and "
                     "`rotMatrix` is pinned to explicit literal matrices on both "
                     "branches, so the post-image is inhabited at an admitted, "
                     "F2P-shaped input AND is the specific matrix the repo "
                     "computes (the quarter-turn about x, whose row-1/column-2 "
                     "entry is the -1 the corrected clause requires), not merely "
                     "`some` matrix. The assert is load-bearing, not decoration: "
                     "perturbing one pinned entry (the -1 to +1) turns this case "
                     "from verifying to rejected, so it could not pass by being "
                     "ignored. It also fails a spec whose entries were correct "
                     "only up to the sign the fix changes, which the positives "
                     "that merely reshape the frozen arithmetic cannot detect.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The gold impl is
    # straight-line, so each witness unfolds the rival's `.run` directly (no
    # loop-free reshaping needed); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "rej-prepatch-sign-block",
        "kind": "uniqueness",
        "expect": "reject",
        # The EXACT pre-change bug: the row-1/column-2 entry m12 gets +b*a where
        # the orientation-preserving convention requires -b*a. This is the single
        # line the gold diff edits.
        "module": _swap(_BASE, _A_M12,
                        "    let m12 := 2 * s * (c * d + b * a)\n"),
        "refinement": "This is the pre-change behaviour verbatim: the "
                      "row-1/column-2 entry computed with +b*a instead of -b*a. A "
                      "faithful real patch keeping this sign is the unpatched "
                      "method, which on the issue's X-rotation quaternion reports "
                      "+sin where -sin is required, so the failing test that pins "
                      "the corrected entry still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = rotMatrix a b c d v`: rotMatrix pins that "
                     "entry to 2*s*(c*d - b*a) and the rival computes "
                     "2*s*(c*d + b*a), which differ whenever b*a ≠ 0. Verifying "
                     "would be SPEC-TOO-WEAK (the clause would not pin the sign the "
                     "fix corrects). Refuted at a=1,b=1,c=0,d=0,v=none (b*a = 1, so "
                     "the two entries differ) via the row-1/column-2 entry.",
        "witness": _witness("1 1 0 0 none"),
    },
    {
        "id": "rej-homogeneous-bottom-row",
        "kind": "uniqueness",
        "expect": "reject",
        # The 3×3 block AND the whole translation column are correct; the only
        # error is the 4×4 bottom row, which carries [0,0,0,2] instead of the
        # homogeneous [0,0,0,1].
        #
        # This slot replaces a case (`rej-prepatch-sign-affine`) that the audit
        # found carried a module BYTE-IDENTICAL to rej-prepatch-sign-block —
        # both were `_swap(_BASE, _A_M12, "... c * d + b * a ...")`, differing
        # only in the witness input. It was not a second rival: the SAME wrong
        # impl was being rejected twice, so its rejection re-attested a fact
        # already established, and the `some`-branch reading it claimed to add is
        # what rej-translation-column and this case actually supply. The
        # bottom-row entry, by contrast, was attacked by nothing in the battery:
        # every other rival perturbs an ARITHMETIC entry, so an `ensures` that
        # pinned the nine block entries and the fourth column while leaving the
        # homogeneous row unconstrained would have passed the whole battery.
        "module": _swap(_BASE, _A_BOTTOM,
                        "         [m20, m21, m22, m23], [0, 0, 0, 2]]\n"),
        "refinement": "A real patch that assembled the homogeneous matrix with a "
                      "bottom row other than [0,0,0,1] does not produce a valid "
                      "affine transformation matrix at all — the point-carrying "
                      "form would not compose or apply correctly — so the failing "
                      "test's assertion on the 4×4 form fails on the last row "
                      "even though every rotation entry is right. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = rotMatrix a b c d v` on the `some` "
                     "branch: rotMatrix pins the fourth row to the literal "
                     "[0, 0, 0, 1] and this rival emits [0, 0, 0, 2], so the "
                     "matrices differ in that entry at EVERY input — the "
                     "disagreement is independent of the quaternion, unlike every "
                     "other rival here. Verifying would be SPEC-TOO-WEAK in a way "
                     "no other case detects: it would mean the clause pins the "
                     "rotation arithmetic but not the homogeneous structure that "
                     "makes the 4×4 an affine transform. Structural rather than "
                     "arithmetic, and confined to the `some` branch (the `none` "
                     "branch has no fourth row, so this rival is indistinguishable "
                     "from gold there — which is why the witness must bind `some`). "
                     "Refuted at a=1,b=1,c=0,d=0,v=some (2,3,5).",
        "witness": _witness("1 1 0 0 (some (2, 3, 5))"),
    },
    {
        "id": "rej-swap-cd",
        "kind": "uniqueness",
        "expect": "reject",
        # Swap which (cd) off-diagonal carries the minus sign: the upper entry m12
        # gets +b*a and the lower entry m21 gets -b*a (the two interchanged). The
        # natural "which one is negative?" transcription error.
        "module": _swap(
            _swap(_BASE, _A_M12, "    let m12 := 2 * s * (c * d + b * a)\n"),
            _A_M21, "    let m21 := 2 * s * (c * d - b * a)\n"),
        "refinement": "Interchanging the two (cd) off-diagonals puts the negative "
                      "sign on the LOWER entry instead of the upper one, producing "
                      "the transpose-like wrong matrix. A real patch with this "
                      "transcription fails the exact matrix equality the failing "
                      "test asserts. It would NOT resolve.",
        "rationale": "REJECT from `out = rotMatrix a b c d v`: rotMatrix pins the "
                     "upper entry to 2*s*(c*d - b*a) and the lower to "
                     "2*s*(c*d + b*a); the rival swaps them, so BOTH disagree "
                     "whenever b*a ≠ 0. Verifying would be SPEC-TOO-WEAK (the spec "
                     "would fail to pin WHICH off-diagonal is negative). Refuted at "
                     "a=1,b=2,c=3,d=4,v=none (all components distinct and nonzero, "
                     "so the swapped entries are observably wrong).",
        "witness": _witness("1 2 3 4 none"),
    },
    {
        "id": "rej-partial-domain-a0",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct sign only on the a==0 sub-domain; reintroduces the buggy +b*a
        # otherwise. The issue witness Quaternion(cos(x/2), sin(x/2), 0, 0) has
        # a = cos(x/2) ≠ 0, so this rival is STILL the buggy matrix there.
        "module": _swap(
            _BASE, _A_M12,
            "    let m12 := if a = 0 then 2 * s * (c * d - b * a) "
            "else 2 * s * (c * d + b * a)\n"),
        "refinement": "Correct sign only when a==0, else the buggy +b*a. The issue "
                      "witness has a = cos(x/2) ≠ 0, so this rival is the buggy "
                      "matrix on the very input the failing test checks — it would "
                      "NOT resolve. Even a rival correct on every literal F2P input "
                      "would be a verify-without-resolve break, since the fix must "
                      "hold for all quaternions.",
        "rationale": "REJECT from `out = rotMatrix a b c d v`, which the verifier "
                     "must establish for ALL a: the a≠0 branch yields "
                     "2*s*(c*d + b*a) ≠ 2*s*(c*d - b*a) when b*a ≠ 0. Demonstrates "
                     "the postcondition pins the ENTIRE domain, not a sampled "
                     "subset. Refuted at a=2,b=3,c=0,d=0,v=none (a≠0, so the buggy "
                     "branch fires and b*a = 6 ≠ 0) — a distinct point in the a-b "
                     "plane from the block-sign rival.",
        "witness": _witness("2 3 0 0 none"),
    },
    {
        "id": "rej-transpose-3x3",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the TRANSPOSE of the 3×3 block (rows and columns interchanged).
        # For a proper rotation M.T == M^-1 (rotation by the negated angle); it
        # coincides with gold only on symmetric matrices.
        "module": _swap(
            _BASE, _A_NONE,
            "      | none => [[m00, m10, m20], [m01, m11, m21], "
            "[m02, m12, m22]]\n"),
        "refinement": "Returning the transposed block gives the inverse rotation "
                      "(rotation by the negated angle), which coincides with gold "
                      "only on symmetric matrices. A real patch returning the "
                      "transpose fails the exact matrix equality the failing test "
                      "asserts on a quaternion with all components nonzero. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = rotMatrix a b c d v`: transposition swaps "
                     "every off-diagonal pair (the upper and lower entries of each "
                     "block position), so the result differs from rotMatrix "
                     "wherever the matrix is non-symmetric. A structural attack "
                     "(off-diagonal permutation) invisible to any abstraction "
                     "checking only the diagonal or a value multiset. Refuted at "
                     "a=2,b=1,c=3,d=5,v=none (all components distinct and nonzero, "
                     "so the block is non-symmetric).",
        "witness": _witness("2 1 3 5 none"),
    },
    {
        "id": "rej-translation-column",
        "kind": "uniqueness",
        "expect": "reject",
        # The 3×3 block is correct, but the 4×4 translation-column entry m13 is
        # built from a wrongly-signed local copy of m12 (+b*a). Targets the SECOND
        # load-bearing consequence — the inherited fourth-column entry — that the
        # block-only rivals never touch, and it lives only in the `some` branch.
        "module": _swap(
            _BASE, _A_M13,
            "        let m12t := 2 * s * (c * d + b * a)\n"
            "        let m13 := y - x * m10 - y * m11 - z * m12t\n"),
        "refinement": "The upper-left block is correct, but the translation column "
                      "reuses a wrongly-signed copy of the row-1/column-2 entry "
                      "(+b*a). A real patch that fixed the block entry but reused a "
                      "stale +b*a expression when forming the fourth column "
                      "produces a wrong homogeneous matrix, so the failing test's "
                      "point-translation assertion fails. It would NOT resolve.",
        "rationale": "REJECT from `out = rotMatrix a b c d v` on the `some` branch: "
                     "rotMatrix builds m13 from the corrected m12 (with -b*a), and "
                     "this rival uses +b*a, so the fourth-column entry differs "
                     "whenever z*b*a ≠ 0. Targets the SECOND load-bearing "
                     "consequence — the inherited translation entry — that the "
                     "block-only rivals never attack, and moves the v binder to "
                     "`some`. Refuted at a=1,b=1,c=0,d=0,v=some (1,1,1) (z=1, "
                     "b*a=1, so the entry differs).",
        "witness": _witness("1 1 0 0 (some (1, 1, 1))"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 5 uniqueness rivals) and an empty AXIOM_TESTS. This bundle models
# the changed operation DEEPLY (the orientation matrix `rotMatrix` via `sFactor`,
# spelled-out closed-form Rat arithmetic), so there is no axiom and no permission
# surface; the value / structural surface (the m12 sign and the off-diagonal
# layout) carries across intact. The nagini model splits the routine into a 3×3
# `rotation_matrix` and a 4×4 `rotation_matrix_affine`; this bundle unifies them
# under one method whose `v : Option ...` selects the branch, so the affine cases
# become `some`-branch rivals of the same method.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-helpers-3x3                 -> pos-cheapest-direct        RE-EXPRESSED
#                                       (return the grounded pure def directly —
#                                        the honest cheapest control)
#   pos-reversed-affine             -> pos-reorder-entries        PORTED
#                                       (reversed entry-binding order; correct,
#                                        proof-closing on this carrier)
#   rej-prepatch-sign-3x3           -> rej-prepatch-sign-block    PORTED
#   rej-prepatch-sign-affine        -> (subsumed; slot re-aimed at
#                                        rej-homogeneous-bottom-row)
#                                       A prior audit "restored" this as its own
#                                       case, but its module was BYTE-IDENTICAL
#                                       to rej-prepatch-sign-block (both
#                                       `_swap(_BASE, _A_M12, ...+b*a...)`),
#                                       differing only in the witness input. So
#                                       it was the same rival rejected twice: its
#                                       rejection attested nothing the block case
#                                       had not already established, which is
#                                       exactly the vacuous-rival shape. The
#                                       `some`-branch reading it claimed as its
#                                       distinguishing content is genuinely
#                                       supplied by rej-translation-column (the
#                                       inherited fourth-column entry) and by
#                                       rej-homogeneous-bottom-row (the
#                                       homogeneous row), both of which bind
#                                       `some` and carry impls that DIFFER from
#                                       every other module here. The slot was
#                                       therefore re-aimed at previously
#                                       unattacked surface rather than deleted,
#                                       keeping the rival count at 6.
#   rej-swap-cd-3x3                 -> rej-swap-cd                 PORTED
#   rej-partial-domain-a0           -> rej-partial-domain-a0      PORTED
#   rej-partial-domain-translation  -> rej-translation-column     PORTED
#                                       (block correct, m13 wrongly-signed —
#                                        the `some`-branch fourth-column clause)
#   rej-transpose-3x3               -> rej-transpose-3x3          PORTED
#   (no sibling counterpart)        -> rej-homogeneous-bottom-row  ADDED
#                                       (audit-added: the 4×4 homogeneous bottom
#                                        row was pinned by the spec but attacked
#                                        by nothing. Every other rival perturbs an
#                                        arithmetic entry, so a spec that pinned
#                                        the nine block entries and the fourth
#                                        column while leaving the last row free
#                                        would have passed the entire battery.
#                                        Both halves built: rival rejected
#                                        (exit 1), witness elaborates against the
#                                        rival (exit 0) and fails against the
#                                        frozen solution (exit 1).)
#   (no sibling counterpart)        -> pos-admissible-witness      ADDED
#                                       (audit-added admissibility positive; see
#                                        the ADMISSIBILITY bullet in the
#                                        docstring. Discharges the obligation by
#                                        evaluation at a concrete admitted,
#                                        F2P-shaped input on both branches,
#                                        before closing the frozen obligation
#                                        verbatim.)
#
# AFTER AUDIT: 3 soundness positives (2 ported/re-expressed + `pos-distribute-
# diagonal`, added because BOTH original positives are definitionally equal to
# the frozen impl and so verify by reduction without ever testing the
# postcondition as an algebraic claim), 1 admissibility positive, and 6 rivals
# (all 5 nagini uniqueness classes + the bottom-row structural rival). Nothing is
# dropped: every nagini adversarial argument has a counterpart here that was
# built and whose witness was rebuilt on both sides.
#
# VACUOUS (frame-mutation): the sibling has no explicit frame-mutation rival
#   (the nagini docstring already declares FRAME-MUTATION N/A — every input is a
#   pass-by-value int primitive and the only mutable object is a freshly
#   constructed Result). On this backend it is likewise vacuous: `a,b,c,d,v` are
#   immutable values, no `mut` binder among the inputs, no heap, no aliasing. No
#   substitute fabricated.
# UNSHIPPABLE, MEASURED (divergence/non-termination): NOT vacuous. This bundle
#   now carries `"total"` (it carried `"partial"` when the battery was authored;
#   a corpus-wide remediation outside this lane changed it), so the `partial`
#   vacuity route no longer applies. Gold being straight-line is irrelevant too
#   (a rival's impl need not resemble gold's).
#   Measured here, on the real verifier: a loop with no `decreasing` annotation
#   is REJECTED at elaboration ("Decreasing annotations are required in total
#   correctness semantics") but is unshippable as a case because that same error
#   poisons the witness build (annotation error + "declaration uses 'sorry'"), so
#   the rejection would attribute nothing to the postcondition; whereas a loop
#   with a present-but-BOGUS measure and the correct return value VERIFIES
#   (exit 0), while the same loop with a wrong return value is still rejected.
#   The value clause keeps its force; only the termination obligation is
#   unenforced. That is a carrier/tooling gap, not a defect of this method's
#   `ensures`, so it is escalated for the corpus (see the docstring) and NOT
#   recorded as a spec hole for this cell. No case fabricated either way.
# CARRIED (admissibility): landed as `pos-admissible-witness` — see that case and
#   the ADMISSIBILITY bullet in the docstring. The earlier note here claimed no
#   separate probe was meaningful because the `require` cannot be weakened; that
#   conflated "no PRECOND-TOO-STRONG rival exists" with "no admissibility case
#   exists". The analogue on a total carrier is a POSITIVE that discharges the
#   obligation by evaluation at a concrete admitted input, which is expressible
#   here and now landed.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = rotMatrix a b c d
#   v` is attacked by all SIX rivals across distinct sub-domains — the block
#   sign, the off-diagonal swap, the a==0 partial domain, the full transpose, the
#   `some`-branch translation column, and the 4×4 homogeneous bottom row —
#   refuted at FIVE distinct input points (the translation-column and bottom-row
#   rivals share a witness input but corrupt different entries of the matrix at
#   it, and no two rivals share a MODULE: all six impls are pairwise distinct,
#   which the audit checked by hashing them). The five components/point
#   binders are varied: `a` over {1,2}, `b` over {1,2,3}, `c` over {0,3}, `d`
#   over {0,4,5}, and `v` over BOTH `none` (the 3×3 branch) and `some` at two
#   different points, `(1,1,1)` and `(2,3,5)` (the 4×4 branch) — so a rival that
#   mishandled only the homogeneous branch, or held any component at a single
#   value, would be caught. The rivals diverge from gold on genuinely different
#   sub-domains (the a==0 rival agrees with gold when a=0; the block-sign rival is
#   wrong there too but at a different (a,b) point; the translation rival is
#   correct on the whole 3×3 branch; the bottom-row rival is wrong at EVERY input
#   but only in the `some` branch), so each carries an input that distinguishes
#   it — verified by rebuilding all six witnesses on both sides.
#
#   The variation is MEANINGFUL, not two spellings of one point (the coverage
#   reporter is advisory and cannot tell): each witness point was chosen so the
#   term the rival corrupts is nonzero there, and each was rebuilt against gold
#   to confirm gold's executable reduces to the spec value at that very point.
#   Where a probe point WOULD have been blind it was rejected rather than
#   recorded: a candidate rival dropping a term of the m03 translation entry is
#   invisible at a=1,b=1,c=0,d=0 (the term it drops is 0 there) and needed
#   a=0,b=1,c=0,d=1 to refute — which is why the `some`-branch points here carry
#   nonzero z and nonzero b*a.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep model; mapping.md §3);
#   this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
