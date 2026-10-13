"""properties.py — G-PBT falsification battery for sympy__sympy-16792 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the whole redundant-argument reconstruction loop as a function over a
LIST of arguments (``pointer_flags(kinds, present)``), with fractional-permission
read-only contracts on both inputs. This Lean bundle models only the purely
functional core: the per-argument decision that turns ONE redundant argument's
array-ness and shape into its index-bound metadata — a total function
``arrayArgBounds(isArrayLike, shape)`` returning the per-axis bound list. Most
nagini cases therefore carry over as attacks on the ONE modeled obligation over
a SINGLE argument; the mapping of each nagini case to its Lean counterpart (or
its principled omission) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior). The obligation pins ``result`` to a
single grounded computation over the two inputs:

    result = if isArrayLike then boundsOf shape else []

where ``boundsOf`` maps each axis size ``d`` to the inclusive index range
``(0, d - 1)``. There is one independent top-level clause (a Boolean branch), so
the adversarial surface is:

  * the ARRAY branch — an array-valued argument must carry the per-axis bound
    list of its shape (this is the CHANGED clause: pre-fix, an array-valued
    redundant argument carried NO bounds and was treated as a scalar);
  * the SCALAR branch — a scalar argument must carry NO bounds;
  * the per-axis bound ARITHMETIC — each axis of ``size`` spans ``(0, size-1)``,
    and the bound list has exactly one entry per axis of the shape.

The BEHAVIOURAL DISCRIMINATOR (the fix): when the argument is array-valued,
attach the shape-derived bound list rather than leaving it empty; that bound
metadata is exactly what later causes the argument to be emitted as a
pointer/array rather than a plain scalar. The F2P scenario is an array-valued
argument of shape ``[2, 1]`` (``isArrayLike = true``, two axes) that does not
occur in the wrapped expression; pre-fix it carried no bounds. The
partial-domain rivals below attack precisely this array branch and its bound
arithmetic.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The two nagini frame-mutation rivals
    (write into a read-only input list) have no expressible instance here; no
    substitute is fabricated. (nagini cases 4, 4b.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the two inputs. There is no opaque
    answer key an implementation could echo, and no ``opaque`` callee on this
    carrier at all — the whole computation is transparent. In its place the
    battery carries honest positive controls (soundness + admissibility) that
    must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: leaving an array-valued argument with no
    bounds (the pre-fix behavior); over-promoting a scalar to carry bounds;
    computing the wrong per-axis range at either endpoint (upper and lower are
    attacked separately); and dropping an axis from the bound list.

AUDIT NOTE 2 (second independent audit, adversarial re-derivation). One further
gap was found by builds and is closed above:

  * every array rival was refuted at an axis of size >= 2 (``[2]``, ``[5]``,
    ``[3]``, ``[2,3]``), so the DEGENERATE-axis sub-domain — an axis of size 1 or
    0 — was unattacked, even though the F2P scenario's own shape ``[2, 1]`` has a
    unit axis. ``weak-unit-axis-clamped-below`` closes it, and its two-sided
    behavior was measured rather than argued: the spec predicate is REFUTABLE
    against the rival at ``(true,[1])`` and at the F2P point ``(true,[2,1])``,
    and VERIFIES against it at ``(true,[2,3])`` — a genuine partial-domain miss.

That audit also re-derived the discrimination of every reject witness by the
FORGERY test rather than by reading error text: for each of the six, the witness
fails on the frozen solution (exit 1) while the SAME file with only the claim
flipped (``¬`` dropped) SUCCEEDS on the frozen solution (exit 0) and fails on the
rival (exit 1). Gold's exit code therefore tracks what is claimed, so it is not a
syntactic artifact. It further confirmed by build that the divergence class is
genuinely unshippable here (below) and that the statement of every case's
``theorem correct_arrayArgBounds`` is byte-identical to the frozen one.

DIVERGENCE / NON-TERMINATION lane: VACUOUS on this carrier, demonstrated by
build rather than asserted. This bundle sets no ``loom.semantics.termination``
option — it is plain Lean, where every ``def`` must be shown total at
ELABORATION time. A rival whose impl recurses without a decreasing measure does
not verify-vacuously, it fails to elaborate at all (``fail to show termination
for implementation_arrayArgBounds``), and — decisively — the failure is in the
IMPL region, so the same error breaks the witness file too: no witness can be
built against it (measured: exit 1 on the rival side, ``Tactic `unfold` failed``,
the half that must SUCCEED). Marking it ``partial def`` does not rescue it: the
impl becomes opaque to ``unfold``, so again the witness cannot be stated. So this
class can be neither shipped as a reject case nor recorded as a spec hole; there
is no diverging impl this spec admits.

AUDIT NOTE (first audit, independent re-derivation of this port). Two gaps were
found and are closed above:

  * the only soundness positive was DEFINITIONALLY EQUAL to the frozen impl, so
    the frozen `cases … <;> rfl` closed it and it could not detect a spec that
    rejects a correct impl needing a propositional re-proof. A second positive
    (`pos-control-reverse-map-nondefeq`) was added: measured to FAIL under the
    frozen tactic body and to verify only with a real `List.map_reverse` proof.
  * no rival moved the per-axis LOWER endpoint, so a one-based index range was
    unattacked. `weak-lower-bound-one-based` closes that.

The audit also re-derived, with builds, that the frame/permission omission is
genuine rather than convenient: the closest expressible analogue (an impl that
locally rebinds and rewrites its `shape` input before use) VERIFIES, because an
input on this carrier carries no permission there could be insufficient of. It
further confirmed each reject witness fails on the frozen solution by `decide`
PROVING the negation false — a semantic refutation at the named input, not a
stuck reduction, unknown identifier, or type error.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases … <;> rfl`` is tuned to the
frozen ``Id.run do`` form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. The carrier is fully
transparent (small integer shapes, no opaque term), so each witness closes by
plain ``decide`` after unfolding. Each was checked to HOLD of its rival and to
FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

BINDER / POINT SPREAD. The two spec binders are ``isArrayLike : Bool`` and
``shape : List Int``. The reject witnesses move both: ``isArrayLike`` takes
``true`` (the array rivals) and ``false`` (the scalar-over-promote rival);
``shape`` ranges over length-1 shapes of differing value (``[2]``, ``[5]``,
``[3]``, ``[1]``) and a length-2 shape (``[2, 3]``). The six reject witnesses
probe six DISTINCT inputs — ``(true,[2])``, ``(false,[2])``, ``(true,[5])``,
``(true,[3])``, ``(true,[1])``, ``(true,[2,3])`` — so no rival is refuted at
another's point.

The ``shape`` spread is deliberately not just "several different numbers". Axis
SIZE is load-bearing in a way pure value-variation does not capture: the bound
arithmetic ``d - 1`` behaves differently in kind at a degenerate axis (size 1
gives the single-index range ``(0,0)``; size 0 gives the empty range ``(0,-1)``)
than at a sized axis (size ``d >= 2`` gives a multi-index range). Four of the
array rivals sit in the ``d >= 2`` region, so ``weak-unit-axis-clamped-below``
carries the degenerate point ``(true,[1])`` — the sub-domain the F2P's own shape
``[2, 1]`` actually lands in, via its unit second axis.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` callee; the per-axis bound operation is modeled deeply (an
A-reference validated by G-AX/G-CONF), not axiomatized. The axiom lane belongs
to G-AX; this gate ignores it, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16792"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive that re-proves, the proof region) so same_spec stays byte-identical.

# The whole frozen imperative impl body (impl region).
_I_BODY = (
    "Id.run do\n"
    "  let mut metadata : List (Int × Int) := []\n"
    "  if isArrayLike then\n"
    "    metadata := boundsOf shape\n"
    "  else\n"
    "    metadata := []\n"
    "  return metadata"
)

# The array-branch assignment of the impl (shared anchor for the array rivals;
# each _swap runs against the pristine _BASE, so uniqueness holds per case).
_I_ARRAY = "    metadata := boundsOf shape"

# The scalar-branch assignment (+ trailing lines) of the impl.
_I_SCALAR = "  else\n    metadata := []\n  return metadata"

# The first line of the frozen proof body (proof region).
_P_HEAD = "  intro isArrayLike shape"

# The WHOLE frozen proof body (proof region) — the anchor for a positive that
# legitimately RE-PROVES the obligation because its impl is not definitionally
# equal to the frozen one (the frozen `cases … <;> rfl` would not close it).
_P_BODY = (
    "  intro isArrayLike shape\n"
    "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds\n"
    "  cases isArrayLike <;> rfl"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. The
    # theorem statement stays byte-identical; the reshape is definitionally
    # equal to the frozen impl so the frozen tactic body still closes (no helper
    # lemma, no axiom, no assumption token introduced).
    #
    # Ports nagini case 1 (pos-control-branch-reorder): the nagini positive
    # reshaped the decision block into an equivalent branch order. Here the
    # analogous reshape collapses the imperative `Id.run do` / `let mut` /
    # if-assign shape into the pure conditional expression it computes.
    # =====================================================================
    {
        "id": "pos-control-pure-conditional",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the mutable-accumulator loop into the pure conditional it
        # denotes. Same value on every input; the frozen `cases … <;> rfl`
        # closes because the two forms are definitionally equal.
        "module": _swap(
            _BASE, _I_BODY,
            "if isArrayLike then boundsOf shape else []",
        ),
        "rationale": "the modeled clause is reshaped from the imperative "
                     "`Id.run do` / `let mut metadata` / if-assign form into the "
                     "pure conditional `if isArrayLike then boundsOf shape else "
                     "[]` it denotes; the returned value is identical on every "
                     "(isArrayLike, shape), so `result = (if isArrayLike then "
                     "boundsOf shape else [])` still holds. Must verify, else the "
                     "one modeled clause is SPEC-TOO-STRONG. Proof: the frozen "
                     "tactic body is retained (both forms are definitionally "
                     "equal, `cases isArrayLike <;> rfl` closes). Ports nagini's "
                     "branch-reorder positive to the single modeled function.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness), NON-DEFINITIONAL. The reshape above is
    # definitionally equal to the frozen impl, so the frozen `cases … <;> rfl`
    # closes it and it only witnesses that the spec accepts a def-equal form.
    # This second positive is a correct impl that is NOT definitionally equal:
    # it builds the bound list by mapping over the REVERSED shape and reversing
    # back. Measured: with the frozen tactic body retained this reshape FAILS
    # (`Tactic 'rfl' failed: … is not definitionally equal to …`), so closing it
    # requires a genuine re-proof (`List.map_reverse`). That makes it a real
    # SPEC-TOO-STRONG probe — the spec must admit a faithful correct impl whose
    # equality to the spec term is propositional rather than by reduction.
    # =====================================================================
    {
        "id": "pos-control-reverse-map-nondefeq",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_ARRAY,
                "    metadata := (shape.reverse.map "
                "(fun d => ((0 : Int), d - 1))).reverse",
            ),
            _P_BODY,
            "  intro isArrayLike shape\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  cases isArrayLike <;> simp [List.map_reverse]",
        ),
        "rationale": "a CORRECT impl that is NOT definitionally equal to the "
                     "frozen one: each axis bound is computed by mapping over the "
                     "reversed shape and reversing the result, which yields the "
                     "identical list on every (isArrayLike, shape) but only up to "
                     "`List.map_reverse` + `List.reverse_reverse`, not by "
                     "reduction. Retaining the frozen tactic body makes this "
                     "reshape FAIL (`rfl` reports the two sides are not "
                     "definitionally equal), so the case re-proves the obligation "
                     "honestly (`cases isArrayLike <;> simp [List.map_reverse]`); "
                     "no new declaration, no axiom, statement byte-identical. "
                     "Must verify, else the spec rejects a faithful correct impl "
                     "merely for computing the bound list in a different order — "
                     "SPEC-TOO-STRONG. Complements the def-equal positive above, "
                     "which the frozen tactic closes and which therefore cannot "
                     "detect that failure mode.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe has no binder to attack here; the honest
    # analogue is to discharge the spec predicate by evaluation at the ground
    # F2P input (an array-valued argument of shape [2, 1]) alongside the frozen
    # obligation. Ports nagini case 2 (admiss-f2p-shape).
    # =====================================================================
    {
        "id": "admiss-f2p-array-shape",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped array input (isArrayLike =
        # true, a two-axis shape) by `decide` in a `have`, then close the frozen
        # obligation verbatim. Nothing is assumed: no new declaration, statement
        # byte-identical, the ground instance is a `have` inside the tactic body.
        "module": _swap(
            _BASE, _P_HEAD,
            "  have _ground : problem_spec_arrayArgBounds true [2, 1]\n"
            "      (implementation_arrayArgBounds true [2, 1]) := by\n"
            "    unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "    decide\n"
            + _P_HEAD,
        ),
        "rationale": "the obligation is discharged at the F2P-shaped input (an "
                     "array-valued argument of shape [2, 1] — the "
                     "MatrixSymbol('x', 2, 1) scenario the F2P exercises) by "
                     "`decide`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instance is a `have` inside the existing tactic "
                     "body. Ports nagini's F2P-shape admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================

    # ---- the fix itself: array argument left with NO bounds (nagini 3a) ----
    {
        "id": "weak-array-no-bounds-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: leave an array-valued argument with empty bound
        # metadata, so it is treated as a scalar.
        "module": _swap(_BASE, _I_ARRAY, "    metadata := []"),
        "refinement": "this IS the pre-fix behavior: an array-valued redundant "
                      "argument is left with no bound metadata, so it is emitted "
                      "as a plain scalar rather than a pointer/array. This is "
                      "exactly the reported defect (the F2P array-valued argument "
                      "renders with the wrong scalar signature). The F2P test "
                      "asserts the pointer/array signature that the shape-derived "
                      "bounds produce, so the faithful real patch — which is this "
                      "very pre-fix code — does NOT resolve.",
        "rationale": "REJECT from the array branch of the modeled clause: for an "
                     "array-valued argument the spec pins `result = boundsOf "
                     "shape` (non-empty for a non-empty shape) while the rival "
                     "yields `[]`, so `result` differs. Binder spread: "
                     "isArrayLike=true, shape=[2] (length 1).",
        "witness": (
            "-- Refuted at an array-valued argument of shape [2]: the spec\n"
            "-- demands the one-axis bound list [(0,1)], the rival yields [].\n"
            "-- Fully concrete, decidable.\n"
            "example : ¬ problem_spec_arrayArgBounds true [2]\n"
            "    (implementation_arrayArgBounds true [2]) := by\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  decide\n"
        ),
    },

    # ---- scalar over-promoted to carry bounds (nagini 3b analogue) ----
    {
        "id": "weak-scalar-overpromote",
        "kind": "uniqueness",
        "expect": "reject",
        # A scalar argument is wrongly given the shape-derived bound list, so it
        # would be emitted as a pointer/array instead of a plain scalar.
        "module": _swap(
            _BASE, _I_SCALAR,
            "  else\n    metadata := boundsOf shape\n  return metadata",
        ),
        "refinement": "an argument that is NOT array-valued is wrongly given the "
                      "shape-derived bound list. On this carrier the nagini "
                      "absent-indexed-array case collapses here: an indexed "
                      "argument on the modeled path is first normalised to its "
                      "plain scalar label, so the only observable non-array case "
                      "is a scalar, and over-promoting it would emit "
                      "`double *x` where gold emits `double x`. A faithful patch "
                      "that promoted a scalar would produce the wrong signature "
                      "for every scalar argument, so the scalar P2P scenarios "
                      "break and it does NOT resolve.",
        "rationale": "REJECT from the scalar branch of the modeled clause: for a "
                     "non-array argument the spec pins `result = []` while the "
                     "rival yields `boundsOf shape` (non-empty for a non-empty "
                     "shape), so `result` differs. Moves the isArrayLike binder "
                     "to false (the only rival that does) and demonstrates that "
                     "shape is load-bearing on the scalar branch too.",
        "witness": (
            "-- Refuted at a scalar argument (isArrayLike = false) with a\n"
            "-- non-empty shape present: the spec demands [], the rival yields\n"
            "-- the shape-derived bounds [(0,1)]. Fully concrete, decidable.\n"
            "example : ¬ problem_spec_arrayArgBounds false [2]\n"
            "    (implementation_arrayArgBounds false [2]) := by\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  decide\n"
        ),
    },

    # ---- wrong per-axis bound arithmetic ----
    {
        "id": "weak-bound-arith-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Compute the wrong per-axis upper bound: (0, d) instead of (0, d - 1),
        # so the inclusive index range spans one index too many.
        "module": _swap(
            _BASE, _I_ARRAY,
            "    metadata := shape.map (fun d => ((0 : Int), d))",
        ),
        "refinement": "a faithful real patch that emitted the per-axis range as "
                      "`(0, size)` rather than `(0, size - 1)` would declare each "
                      "axis one index too large, so the generated array bounds "
                      "disagree with gold on every array argument. The P2P/F2P "
                      "signature the tests assert uses the inclusive `size - 1` "
                      "upper bound, so the arithmetic mismatch would NOT resolve. "
                      "It agrees with gold only on the scalar branch and on empty "
                      "shapes — a partial-domain miss on exactly the sized-axis "
                      "path.",
        "rationale": "REJECT from the per-axis bound arithmetic of the array "
                     "clause: the spec pins each axis to `(0, d - 1)` while the "
                     "rival yields `(0, d)`, so for any axis of size ≥ 1 the bound "
                     "pair — hence `result` — differs. Distinct point (shape=[5], "
                     "a length-1 shape of a different value) from the other array "
                     "rivals.",
        "witness": (
            "-- Refuted at an array of shape [5]: the spec's axis bound is\n"
            "-- (0,4), the rival's is (0,5). Fully concrete, decidable.\n"
            "example : ¬ problem_spec_arrayArgBounds true [5]\n"
            "    (implementation_arrayArgBounds true [5]) := by\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  decide\n"
        ),
    },

    # ---- wrong per-axis LOWER bound (the other endpoint of the range) ----
    # The off-by-one rival above moves only the UPPER endpoint, so nothing in the
    # battery pinned the lower one: an impl that started every axis at index 1
    # was unattacked. Added by audit.
    {
        "id": "weak-lower-bound-one-based",
        "kind": "uniqueness",
        "expect": "reject",
        # Start each axis at index 1 rather than 0: a one-based index range.
        "module": _swap(
            _BASE, _I_ARRAY,
            "    metadata := shape.map (fun d => ((1 : Int), d - 1))",
        ),
        "refinement": "a faithful real patch that emitted each axis range as "
                      "`(1, size - 1)` would declare every array axis to start at "
                      "index 1 instead of 0, so the generated bound metadata is "
                      "off at the low end for every array argument and the emitted "
                      "signature/indexing disagrees with gold. The asserted "
                      "signature depends on the zero-based inclusive range, so it "
                      "would NOT resolve. It agrees with gold on the scalar branch "
                      "and on empty shapes — a partial-domain miss on exactly the "
                      "sized-axis path, and one no other rival covers (the "
                      "off-by-one rival moves only the UPPER endpoint).",
        "rationale": "REJECT from the per-axis bound arithmetic of the array "
                     "clause, LOWER endpoint: the spec pins each axis to "
                     "`(0, d - 1)` while the rival yields `(1, d - 1)`, so the "
                     "bound pair — hence `result` — differs for any non-empty "
                     "shape. Distinct point (shape=[3]) from every other rival, so "
                     "it is not refuted at another's input.",
        "witness": (
            "-- Refuted at an array of shape [3]: the spec's axis bound is\n"
            "-- (0,2), the rival's is (1,2). Fully concrete, decidable.\n"
            "example : ¬ problem_spec_arrayArgBounds true [3]\n"
            "    (implementation_arrayArgBounds true [3]) := by\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  decide\n"
        ),
    },

    # ---- the DEGENERATE / UNIT axis: an axis of size 1 (or 0) ----
    # Every other rival is refuted at an axis of size >= 2 ([2], [5], [3], [2,3]),
    # so an impl that is correct on "large" axes and wrong only where an axis has
    # size 1 or 0 was entirely unattacked — even though the F2P scenario's own
    # shape [2, 1] HAS a unit axis, so this sub-domain is the one the modeled
    # behavior is actually exercised on. Added by audit.
    {
        "id": "weak-unit-axis-clamped-below",
        "kind": "uniqueness",
        "expect": "reject",
        # Clamp the per-axis upper bound BELOW at 1, so a degenerate axis (size 1
        # or 0) is declared to span two indices instead of one (or none).
        "module": _swap(
            _BASE, _I_ARRAY,
            "    metadata := shape.map (fun d => ((0 : Int), max (d - 1) 1))",
        ),
        "refinement": "a faithful real patch that clamped each axis's inclusive "
                      "upper bound below at 1 would declare a degenerate axis — "
                      "one of size 1, or the empty size-0 axis — to span two "
                      "indices rather than one (or none), so the emitted bound "
                      "metadata is too large for exactly those axes. This is NOT a "
                      "corner the tests skip: the F2P scenario's argument has shape "
                      "[2, 1], whose SECOND axis is a unit axis, so the clamp is "
                      "wrong at the very input the F2P exercises (measured: the "
                      "refutation of the spec predicate at (true, [2, 1]) holds of "
                      "this rival). It agrees with gold on every axis of size >= 2 "
                      "(measured: the spec predicate VERIFIES against this rival at "
                      "(true, [2, 3])), so it is a genuine partial-domain miss on "
                      "the degenerate-axis path and would NOT resolve.",
        "rationale": "REJECT from the per-axis bound arithmetic of the array "
                     "clause, DEGENERATE axis: the spec pins each axis to "
                     "`(0, d - 1)` while the rival yields `(0, max (d - 1) 1)`, so "
                     "the two agree only where `d - 1 >= 1`, i.e. on axes of size "
                     ">= 2, and differ on every axis of size 1 or 0. No other rival "
                     "moves the shape binder off the size->=2 region: the four "
                     "array rivals use shapes [2], [5], [3] and [2, 3]. Distinct "
                     "point (shape=[1]), so it is not refuted at another's input.",
        "witness": (
            "-- Refuted at an array-valued argument with a UNIT axis, shape [1]:\n"
            "-- the spec's axis bound is (0,0), the rival's clamp yields (0,1).\n"
            "-- Fully concrete, decidable.\n"
            "example : ¬ problem_spec_arrayArgBounds true [1]\n"
            "    (implementation_arrayArgBounds true [1]) := by\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  decide\n"
        ),
    },

    # ---- drop an axis from the bound list (cardinality within the shape) ----
    {
        "id": "weak-drop-axis",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit bounds for only the FIRST axis of a multi-axis shape, dropping the
        # remaining axes' bound entries.
        "module": _swap(
            _BASE, _I_ARRAY,
            "    metadata := (boundsOf shape).take 1",
        ),
        "refinement": "a faithful real patch that emitted bounds for only the "
                      "leading axis of a multi-axis shape would declare a "
                      "lower-rank array than the argument actually has, so the "
                      "generated signature disagrees with gold for any argument "
                      "of rank ≥ 2. The nagini length-class case attacked the "
                      "cardinality of the whole argument LIST; on this "
                      "single-argument carrier the analogous cardinality clause "
                      "is the bound list's one-entry-per-axis requirement, and "
                      "dropping an axis breaks it, so it would NOT resolve. It "
                      "agrees with gold on rank-0 and rank-1 arguments — a "
                      "partial-domain miss on exactly the multi-axis path.",
        "rationale": "REJECT from the array clause: for a multi-axis shape the "
                     "spec pins one bound pair per axis (`boundsOf shape`) while "
                     "the rival keeps only the first, so `result` has too few "
                     "entries and differs. Moves the shape binder to length 2 "
                     "([2, 3]) — the only rival probing a multi-axis shape.",
        "witness": (
            "-- Refuted at a two-axis shape [2, 3]: the spec demands\n"
            "-- [(0,1),(0,2)], the rival keeps only [(0,1)]. Concrete, decidable.\n"
            "example : ¬ problem_spec_arrayArgBounds true [2, 3]\n"
            "    (implementation_arrayArgBounds true [2, 3]) := by\n"
            "  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds boundsOf\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# callee (the per-axis bound operation is modeled deeply, an A-reference
# validated by G-AX/G-CONF, not a consumed contract). The nagini AXIOM_TESTS
# re-ran the deep-model-vs-real-callee obligation, which is G-AX's job here;
# dropped from this lane.
AXIOM_TESTS = []
