"""properties.py — G-PBT falsification battery for sympy__sympy-15017 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end``, or inside the elided ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct arrayLength`` header survives) and swaps in a candidate
implementation. It is checked by the real verifier: ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a single sequence carrier):

  arrayLength (dims : List Nat) return (n : Nat)
    ensures n = prodSeq dims                    -- THE load-bearing clause

``arrayLength`` reports how many elements an array of the given shape holds:
the product of its dimension sizes, and — when there are no dimensions at all —
the empty product, one. ``prodSeq`` is a total, fully-unfolded pure ``def`` over
the method's OWN argument (front-recursive: ``prodSeq [] = 1``,
``prodSeq (d :: ds) = d * prodSeq ds``) living in the ``pure`` region. The
``axioms`` region is EMPTY: there is no opaque callee and no answer key to echo
(directive 8), so the whole carrier is TRANSPARENT and every rival is refutable
by computation at a concrete input.

ONE INPUT BINDER, ``dims``, and it is fully load-bearing in three separable ways.
The single ``ensures`` clause has no independent top-level conjuncts, so the
attack surface is instead the clause's decomposition over that binder:

  * EMPTY CASE   — ``dims = []`` must fold to the multiplicative identity one,
                   not to a degenerate zero. The DISCRIMINATING sub-domain: the
                   only point at which the frozen behaviour and the pre-fix
                   behaviour differ at all.
  * EVERY FACTOR — every entry of ``dims`` participates; dropping the entry at
                   either END of the sequence, or ignoring the entries entirely,
                   must not satisfy the clause.
  * THE COMBINER — the entries are combined MULTIPLICATIVELY (with identity
                   one), not additively and not by a constant.

Because ``dims`` is the sole binder, "vary every input binder" means the reject
witnesses must vary its LENGTH and its CONTENTS rather than sit at one pinned
shape. They probe SIX distinct points — ``[]``, ``[0]``, ``[2,3]``, ``[7,1]``,
``[1,7]``, ``[3,3,3,3]`` — spanning lengths 0/1/2/4, a genuine zero entry, an
identity entry at each end, and two distinct non-unit entries (pts = 6). There
is no ``require`` clause, so no witness input can be vacuously excluded by a
false precondition.

CARRIER NOTE — THE DECIDABLE BOUNDARY (measured on this bundle). A witness
reaches the post-image through Velvet's tester machinery
(``arrayLengthTester dims = false`` says the extracted program's result violates
the postcondition at that concrete input) and closes by ``decide``, checked in a
file whose ``prove_correct`` block has been stripped so no tactic script can mask
the verdict. ``decide`` reduces the extracted program by kernel computation; the
frozen program is a BACKWARD ``while`` loop over the dimension sequence and its
fixpoint is opaque to the kernel, so a witness applied to the frozen solution
gets STUCK (``did not reduce to isTrue or isFalse``) — which supplies the
required FAIL-on-gold half. Each reject rival is therefore written as a LOOP-FREE
expression so its extracted tester ``decide``s over the concrete literal.

That is a witnessing convenience, and it was checked NOT to be the thing the
witnesses measure. The control: a loop-free but CORRECT impl (``return prodSeq
dims``) was built against ``arrayLengthTester <pt> = false`` at ALL SIX witness
points and FAILED at every one, while ``= true`` succeeded at every one. So a
loop-free tester reduces to ``true`` exactly when the impl satisfies the clause;
each ``= false`` below therefore records a genuine postcondition violation, not
the mere absence of a loop. Both halves of every witness were run out-of-band
with ``scripts/lean_verify.sh`` (rival build exit 0, gold build exit 1).

ADVERSARIAL READ of the sibling's classes on this carrier:
  * VALUE / PARTIAL-DOMAIN — heavily exercised; the whole battery. Each rival
    returns a well-typed count of the right type and is correct on part of the
    domain, diverging on one of the three sub-behaviours above.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``prodSeq dims``, a concrete ``def`` over the method's own
    argument, so the cheapest HONEST impl is to return it — and that is CORRECT,
    shipped as ``pos-direct-model``. There is no wrong echo to write.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    two of these because its input carries only a fractional read permission, so
    a write to it is rejected by the permission system. This backend is
    referentially transparent: ``dims`` is an immutable value, the method
    declares no ``mut`` binder, and there is no heap and no aliasing, so there is
    no read-only cell to overwrite. No substitute probe is fabricated (per the
    porting map, this class is legitimately dropped rather than replaced).
  * DIVERGENCE / NON-TERMINATION — ENFORCED by this spec, but UNWITNESSABLE on
    this carrier. ``termination "total"`` is set, and a diverging rival is
    measurably rejected (``Decreasing annotations are required in total
    correctness semantics``). It still ships no case: a reject case's witness
    must hold OF THE RIVAL, and a rival whose module does not elaborate derives
    no tester for the witness to be proven against. See the footer.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
— the computation is concrete natural-number arithmetic over the input — so there
is nothing to probe, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15017"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (both markers, and the comment lines, live inside the elided
# impl region). Every case edits ONLY this block and, where a reshape needs it,
# the elided `prove_correct` tactic body — so the spec view is untouched and
# same_spec holds by construction.
_IMPL = """    -- Fold the dimension sizes into a running product, seeded with the
    -- multiplicative identity one, so a shape with no dimensions yields one.
    let mut result : Nat := 1
    let mut i := dims.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dims.length
      invariant result = prodSeq (dims.drop i)
      done_with i = 0
      decreasing i
    do
      let d := dims[i - 1]!
      result := d * result
      i := i - 1
    return result"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. It is tuned to the frozen backward loop: it applies
# the drop-step unfold at the loop's own `i`. A rival that is LOOP-FREE has no
# such goal, so leaving this block in place would fail for a reason having
# nothing to do with the spec ("Unknown identifier `i`"). Every loop-free variant
# below therefore retunes the proof to the bare `loom_solve` that its own shape
# needs. That retune is INSIDE the elided proof region and keeps the
# `prove_correct arrayLength` header, so the obligation survives intact — and for
# the rivals it is the WITNESS, never the module build, that attributes the
# rejection to the spec.
_PROOF = """prove_correct arrayLength by
  loom_solve
  rw [prodSeq_drop_step dims i (by omega) (by omega)]
  simp_all"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# The proof a LOOP-FREE impl needs: `loom_solve` alone discharges the single
# postcondition goal, with no loop-body goal left to unfold.
_PROOF_FLAT = "prove_correct arrayLength by\n  loom_solve"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (inside the elided region)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


def _flat(expr):
    """A loop-free variant returning `expr`, with the proof retuned to match."""
    return _impl_reproved(f"    return {expr}", _PROOF_FLAT)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `arrayLengthTester dims = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script can
# ---- mask the verdict. The argument is a concrete literal and each rival is
# ---- loop-free, so `decide` reduces the extracted program without getting stuck.
# ---- No binders are introduced: the carrier is fully transparent (no opaque
# ---- callee), so no witness needs to CONDITION on it and none can be
# ---- inconsistent.
def _witness(dims_literal):
    return ("extract_program_for arrayLength\n"
            "prove_precondition_decidable_for arrayLength\n"
            "prove_postcondition_decidable_for arrayLength\n"
            "derive_tester_for arrayLength\n\n"
            f"example : arrayLengthTester {dims_literal} = false := by\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the clause is
    # over-fit to the frozen loop's spelling => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest HONEST impl: return the grounded pure model directly, no loop
        # at all — maximally different in shape from the frozen backward fold,
        # and observationally identical on every input. `loom_solve` alone closes
        # the byte-identical obligation (the ensures IS `n = prodSeq dims`, so the
        # body is definitionally the RHS). Verified out-of-band, exit 0.
        "module": _flat("prodSeq dims"),
        "rationale": "structurally different CORRECT impl: it returns the pure "
                     "product model directly instead of accumulating it with a "
                     "loop. Observationally identical on the whole domain, so "
                     "`n = prodSeq dims` holds everywhere. Because the model is "
                     "GROUNDED in the method's own argument (not an opaque "
                     "answer key), returning it is the cheapest honest impl and "
                     "is correct — which is also what makes the "
                     "UNGROUNDED-ORACLE-ECHO class N/A on this bundle: there is "
                     "no wrong echo to write. Must verify, else the clause is "
                     "SPEC-TOO-STRONG (it would reject its own model's output).",
    },
    {
        "id": "pos-commuted-factor-order",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the frozen backward loop and both invariants, but multiplies the
        # running total by the exposed dimension on the OTHER side
        # (`result * d` rather than `d * result`) and inlines the `let d`. Same
        # values (the product commutes), different executable shape. The proof is
        # retuned only to supply that commutation — the frozen script otherwise
        # leaves exactly one goal, `prodSeq .. * d = d * prodSeq ..`. Verified
        # out-of-band, exit 0.
        "module": _impl_reproved(
            "    let mut result : Nat := 1\n"
            "    let mut i := dims.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ dims.length\n"
            "      invariant result = prodSeq (dims.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      result := result * dims[i - 1]!\n"
            "      i := i - 1\n"
            "    return result",
            "prove_correct arrayLength by\n"
            "  loom_solve\n"
            "  rw [prodSeq_drop_step dims i (by omega) (by omega)]\n"
            "  simp_all [Nat.mul_comm]"),
        "rationale": "faithful reshape that accumulates each factor on the "
                     "opposite side of the running total and inlines the "
                     "per-step binding. Identical values on every input, so "
                     "`n = prodSeq dims` still holds; the proof is retuned "
                     "inside the elided region to discharge the one commutation "
                     "goal this shape leaves, with the obligation statement "
                     "byte-identical. Must verify, else the clause is pinned to "
                     "the frozen factor order => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-single-exit-local",
        "kind": "soundness",
        "expect": "verify",
        # The sibling's single-exit reshape: rename the accumulator and bind the
        # answer to a distinct typed local before the sole return. Same loop,
        # same invariants, same step — so the FROZEN proof closes it unchanged.
        # Verified out-of-band, exit 0.
        "module": _impl(
            "    let mut acc : Nat := 1\n"
            "    let mut i := dims.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ dims.length\n"
            "      invariant acc = prodSeq (dims.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let d := dims[i - 1]!\n"
            "      acc := d * acc\n"
            "      i := i - 1\n"
            "    let out : Nat := acc\n"
            "    return out"),
        "rationale": "single-exit / local-rename reshape (the sibling's "
                     "structurally-different-but-correct control): the running "
                     "total is bound to a renamed accumulator and the answer to "
                     "a distinct typed local returned once at the end. Every "
                     "proof obligation the frozen body needs is KEPT (both "
                     "invariants and the same fold step), so no proof gap is "
                     "introduced and the frozen script closes it unchanged. Must "
                     "verify, else the clause is over-fit to the frozen "
                     "variable spelling => SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's probe self-asserts that a normal input is
    # in-domain under its fractional-permission precondition. This backend has
    # NO `require` clause at all and no permission surface, so "is a normal
    # input admitted" is degenerate here: every input is. The residual
    # admissibility risk on this domain is instead a DEGENERATE post-image — a
    # clause that is satisfiable only by a collapsed answer. This probe
    # discharges an in-region `assert` pinning the post-image at three
    # F2P-shaped points at once: a shape with no dimensions (one element), a
    # shape with a genuinely empty axis (no elements), and a rank-4 shape (the
    # full product). The frozen impl is kept verbatim so the method's own
    # obligation still discharges; only the assert is added. The assert is LIVE
    # — the same case with one conjunct falsified leaves an unsolved goal
    # (checked out-of-band during authoring, exit 1).
    # =====================================================================
    {
        "id": "admiss-nondegenerate-post-image",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (prodSeq [] = 1 ∧ prodSeq [0] = 0 ∧ prodSeq [3, 3, 3, 3] = 81))\n"
            + _IMPL,
            _PROOF),
        "rationale": "the method carries no `require` clause and no permission "
                     "surface, so the sibling's \"is a normal input admitted\" "
                     "probe is degenerate (every input is in-domain); the live "
                     "risk is a DEGENERATE post-image. The in-region assert "
                     "pins it at three F2P-shaped points: a shape with no "
                     "dimensions maps to one element, a shape with an empty "
                     "axis to none, and a rank-4 shape to the full product — so "
                     "the clause is neither unsatisfiable (PRECOND-TOO-STRONG) "
                     "nor a constant collapse. The frozen impl is kept verbatim "
                     "so the method's own obligation discharges too; a false "
                     "conjunct leaves an unsolved goal, so the assert is live.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is written
    # loop-free so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-empty-shape-collapses-to-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # THE headline rival — the exact pre-fix behaviour, and the sub-domain
        # the reported defect lives on. Correct on EVERY shape with at least one
        # dimension; on a shape with none it reports no elements instead of one.
        "module": _flat("if dims.length = 0 then 0 else prodSeq dims"),
        "refinement": "this is the pre-fix behaviour: an array whose shape has "
                      "no dimensions — a scalar — is reported as holding no "
                      "elements. That is exactly the defect the issue reports "
                      "(`len` of a rank-0 array coming back 0 where iterating "
                      "it yields one element, and where the corresponding numpy "
                      "size is 1), and the failing initiation test now asserts "
                      "that count is 1. Its faithful counterpart keeps the "
                      "special case for the dimensionless shape, so that count "
                      "stays 0 and the downstream single-element access keeps "
                      "being refused — it would NOT resolve. Every shape with "
                      "at least one dimension is unaffected, so the "
                      "PASS_TO_PASS counts are untouched and this is a true "
                      "partial-domain divergence, not a broken build.",
        "rationale": "REJECT from `n = prodSeq dims` via the EMPTY-CASE "
                     "sub-behaviour: `prodSeq [] = 1` (the empty product is the "
                     "multiplicative identity), but the rival returns 0 there, "
                     "and 0 ≠ 1. Verifying would be SPEC-TOO-WEAK — the clause "
                     "would not pin the one point at which the frozen and "
                     "pre-fix behaviours differ at all, i.e. the entire defect. "
                     "Refuted at dims = [] (the length-0 point; no other "
                     "witness sits there).",
        "witness": _witness("[]"),
    },
    {
        "id": "weak-constant-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the dimensions entirely and always reports one element.
        # Correct on the dimensionless shape and on any shape whose dimensions
        # all have size one — so it gets the headline sub-domain RIGHT and is a
        # near-miss from the other side. Wrong wherever the product is not one.
        "module": _flat("1"),
        "refinement": "reporting one element unconditionally would make every "
                      "array claim to hold exactly one element regardless of "
                      "its dimensions. The failing initiation test asserts both "
                      "that a scalar holds one element AND that an array "
                      "declared with a single empty axis holds none; the second "
                      "assertion would come back 1, and the retained "
                      "multi-dimensional counts (a rank-4 shape holding 81 "
                      "elements) would also come back 1. It would NOT resolve.",
        "rationale": "REJECT from `n = prodSeq dims` via the EVERY-FACTOR "
                     "sub-behaviour: the rival ignores `dims` entirely. It is a "
                     "NEAR-MISS of the headline rival from the opposite side — "
                     "it gets the dimensionless shape RIGHT — so it needs its "
                     "own witness at a point where the product is not one. "
                     "Refuted at dims = [0]: the product is 0, the rival "
                     "returns 1. This moves the binder to length 1 and to a "
                     "genuinely empty axis, the only witness that exercises a "
                     "zero factor.",
        "witness": _witness("[0]"),
    },
    {
        "id": "weak-identity-seed-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Seeds the fold at the ADDITIVE identity instead of the multiplicative
        # one, so the running total is annihilated and every shape reports no
        # elements. Correct only where the product is genuinely 0.
        "module": _flat("0"),
        "refinement": "seeding the running total at zero annihilates the "
                      "product, so every array reports holding no elements. "
                      "Both halves of the failing initiation test break (a "
                      "scalar would report 0 where 1 is required) and so do the "
                      "retained multi-dimensional counts (a rank-4 shape would "
                      "report 0 where 81 is required). It would NOT resolve.",
        "rationale": "REJECT from `n = prodSeq dims` via the EVERY-FACTOR and "
                     "COMBINER sub-behaviours at once: seeding at the additive "
                     "identity makes the fold constant, so the result is "
                     "independent of `dims`. Refuted at dims = [3, 3, 3, 3]: "
                     "the product is 81, the rival returns 0. Witnessed at the "
                     "length-4 point — the only witness with more than two "
                     "dimensions, and the one that shows the clause pins a "
                     "large product rather than only the small boundary cases. "
                     "(It also diverges at [], but it is deliberately NOT "
                     "witnessed there: the headline rival owns that point, and "
                     "co-locating them would leave the binder's length "
                     "unvaried.)",
        "witness": _witness("[3, 3, 3, 3]"),
    },
    {
        "id": "weak-drops-leading-dimension",
        "kind": "uniqueness",
        "expect": "reject",
        # Omits the FIRST dimension from the product. Correct on the
        # dimensionless shape, on any single-dimension shape whose one size is
        # ignored to 1, and whenever the leading size is 1 — a genuine
        # partial-domain rival, and a near-miss of the trailing-drop rival.
        "module": _flat("prodSeq (dims.drop 1)"),
        "refinement": "omitting the leading dimension from the product "
                      "under-counts every array whose first dimension is larger "
                      "than one: a rank-4 shape of sizes 3,3,3,3 would report "
                      "27 elements rather than 81, so the retained "
                      "multi-dimensional count assertion fails. It would NOT "
                      "resolve. (It happens to get the dimensionless shape "
                      "right, so it is a rival that passes the headline "
                      "sub-domain and still must be rejected.)",
        "rationale": "REJECT from `n = prodSeq dims` via the EVERY-FACTOR "
                     "sub-behaviour at the FRONT of the sequence: the clause "
                     "multiplies in every entry, the rival skips the leading "
                     "one, so they differ whenever that entry is not 1. Refuted "
                     "at dims = [7, 1]: the product is 7, the rival returns 1. "
                     "This witness is NOT shared with the trailing-drop rival — "
                     "checked out-of-band, the trailing-drop rival is NOT "
                     "refuted at [7, 1] (it returns 7 there), which is exactly "
                     "why each end of the sequence needs its own point.",
        "witness": _witness("[7, 1]"),
    },
    {
        "id": "weak-drops-trailing-dimension",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror rival: omits the LAST dimension. Distinct from the
        # leading-drop rival — each is correct exactly where the other is wrong,
        # so neither subsumes the other and they cannot share a witness.
        "module": _flat("prodSeq dims.dropLast"),
        "refinement": "omitting the trailing dimension under-counts every array "
                      "whose last dimension is larger than one — a rank-4 shape "
                      "of sizes 3,3,3,3 would again report 27 rather than 81 — "
                      "so the retained multi-dimensional count assertion fails "
                      "and it would NOT resolve. Shipped alongside the "
                      "leading-drop rival because the clause must pin the "
                      "entries at BOTH ends of the sequence; a spec that pinned "
                      "only one end would admit the other rival.",
        "rationale": "REJECT from `n = prodSeq dims` via the EVERY-FACTOR "
                     "sub-behaviour at the END of the sequence. Refuted at "
                     "dims = [1, 7]: the product is 7, the rival returns 1. "
                     "This is the MIRROR point of the leading-drop witness and "
                     "cannot be shared with it — checked out-of-band, the "
                     "leading-drop rival is NOT refuted at [1, 7] (it returns 7 "
                     "there). Two near-misses, two points, so each rival's "
                     "claimed sub-domain is actually demonstrated.",
        "witness": _witness("[1, 7]"),
    },
    {
        "id": "weak-additive-combiner",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the COMBINER rather than the operands: reads every dimension,
        # in order, and combines them by addition instead of multiplication.
        # Agrees with the clause on a broad slice (any single-dimension shape,
        # and [2,2]), so it is not a coarse rival.
        "module": _flat("dims.sum"),
        "refinement": "combining the dimension sizes additively rather than "
                      "multiplicatively reports the wrong element count for "
                      "essentially every multi-dimensional array: a rank-4 "
                      "shape of sizes 3,3,3,3 would report 12 rather than 81, "
                      "failing the retained multi-dimensional count assertion. "
                      "It also reports one element too many for a shape with a "
                      "single empty axis, breaking the failing initiation "
                      "test's zero-count assertion. It would NOT resolve.",
        "rationale": "REJECT from `n = prodSeq dims` via the COMBINER "
                     "sub-behaviour: this rival honours EVERY entry and their "
                     "order (so the drop rivals do not subsume it) but folds "
                     "them with the wrong operation. It is the only rival that "
                     "attacks how the entries are combined rather than which "
                     "ones are read. Refuted at dims = [2, 3]: the product is "
                     "6, the rival returns 5. This is the only witness with two "
                     "distinct non-unit entries — a point where sum and product "
                     "necessarily disagree, unlike the unit-carrying points the "
                     "drop rivals use.",
        "witness": _witness("[2, 3]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 value rivals, 1
# non-termination rival) plus an EMPTY axiom lane. This bundle models the SAME
# purely-functional core — the element count folded from a shape — over
# `List Nat` instead of the sibling's permission-carrying list carrier with a
# prefix-recursive deep oracle. The value surface carries across intact; the
# permission surface does not exist here.
#
#   sibling case                       -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-control-single-exit            -> pos-single-exit-local         PORTED
#   honest-grounded-oracle-return      -> pos-direct-model              PORTED
#   admiss-reads                       -> admiss-nondegenerate-post-image
#                                                                       PORTED (re-aimed)
#   prepatch-empty-zero-firstseed      -> weak-empty-shape-collapses-to-zero
#                                                                       PORTED (merged)
#   partial-domain-empty-zero          -> weak-empty-shape-collapses-to-zero
#                                                                       PORTED (merged)
#   partial-domain-skip-first-axis     -> weak-drops-leading-dimension  PORTED
#   constant-one                       -> weak-constant-one             PORTED
#   acc-seed-zero                      -> weak-identity-seed-zero       PORTED
#   frame-mutation-index-write         -> (none)                        VACUOUS
#   frame-mutation-append              -> (none)                        VACUOUS
#   weak-nonterminating                -> (none)                        UNWITNESSABLE
#                                        (spec ENFORCES it; rival derives no tester)
#   AXIOM_TESTS ([])                   -> (none)                        DROPPED (G-AX)
#   (no sibling)                       -> pos-commuted-factor-order     ADDED
#   (no sibling)                       -> weak-drops-trailing-dimension ADDED
#   (no sibling)                       -> weak-additive-combiner        ADDED
#
# Net: 10 cases here (3 soundness, 1 admissibility, 6 uniqueness) against the
# sibling's 10. Seven sibling SPEC cases ported (two of them merging into one),
# two vacuous, one enforced-but-unwitnessable; three cases added for coverage
# this carrier newly exposes.
#
# WITHDRAWN FINDING (the measure is checked after all). An earlier revision of
# this footer carried a finding against the FROZEN SPEC, claiming that the
# `decreasing` clause is accepted WITHOUT its descent obligation being enforced,
# so that a diverging impl which merely *annotates* a measure is admitted while an
# unannotated one is rejected. Every measurement it rested on has been rebuilt and
# NONE reproduces. The finding is retracted in full; nothing is open on this axis
# and nothing needs escalating.
#
#   Rebuilt (a), its central shape, with the proof reduced to a bare `loom_solve`:
#     let mut k : Nat := 0
#     while k ≥ 0
#       invariant 0 ≤ k
#       done_with False
#       decreasing k          -- k strictly INCREASES
#     do
#       k := k + 1
#   spliced at the impl anchor -> exit 1, `unsolved goals`,
#   `case «decreasing_1: k»`, residual `k + 1 < k`. The earlier note recorded this
#   same impl as VERIFYING at exit 0.
#
#   Rebuilt (b), the form the earlier note called its sharpest, because it isolates
#   the annotation from every other edit: take the FROZEN impl and the FROZEN proof
#   verbatim and change ONLY the measure expression, `decreasing i` to
#   `decreasing dims.length` (constant) or to `decreasing (dims.length - i)`
#   (increasing as the loop runs). The earlier note recorded both as exit 0. Both
#   are in fact REJECTED, each on its own descent goal and named after its own
#   measure expression:
#     * `decreasing dims.length`      -> exit 1, `case «decreasing_1: dims.length»`,
#                                        residual `dims.length < dims.length`
#     * `decreasing (dims.length - i)` -> exit 1,
#                                        `case «decreasing_1: (dims.length - i)»`,
#                                        residual
#                                        `dims.length - (i - 1) < dims.length - i`
#   A one-token anti-monotone edit to the measure is therefore NOT accepted, and
#   `decreasing_1` is surfaced to the proof, contrary to the earlier note.
#
#   The mechanism is visible in Loom and explains why no such hole can exist under
#   this configuration. `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`
#   (`Loom/MonadAlgebras/NonDetT/Basic.lean:544`) takes `measure : β -> Nat` and
#   emits `with_name_prefix `decreasing (measure b' < measure b)`. Only the
#   `PartialCorrectness` twin (same file, :211) takes `measure : β -> Option ℕ` and
#   DISCARDS it. This bundle opens `TotalCorrectness`, and the two lines cannot
#   drift apart: the `set_option` elaborator itself runs
#   `openScope `TotalCorrectness` (`Loom/MonadAlgebras/WP/Options.lean:169-186`).
#   So annotating a measure buys nothing an impl has to be able to prove anyway.
#   The earlier claim that the splice "reproduces on one other sampled `total`
#   bundle" is withdrawn too: rebuilt across many bundles, every one rejects it on
#   the descent goal.
#
# PORTED (positives): honest-grounded-oracle-return returned the deep oracle
#   directly — here that is `return prodSeq dims`, which is loop-free, so its
#   proof is retuned to the bare `loom_solve` its own shape needs (inside the
#   elided region; the obligation header is unchanged). pos-control-single-exit
#   renamed the accumulator and returned through a typed local — that ports
#   literally, and the frozen proof closes it unchanged.
# PORTED-RE-AIMED (admissibility): the sibling probes that its fractional-
#   permission precondition admits a normal input. This method has NO `require`
#   clause and no permission surface, so that probe is degenerate here (every
#   input is in-domain) and re-aiming it at the residual risk — a degenerate
#   post-image — is what keeps it informative. It now pins the post-image at
#   three F2P-shaped points and was checked LIVE (falsifying one conjunct leaves
#   an unsolved goal).
# PORTED-MERGED (the two empty-shape rivals): the sibling ships the prepatch
#   (first-entry seed + empty special case) and a leaner variant (identity seed +
#   empty special case) as separate cases, because on its carrier the two differ
#   in the fold's seeding and therefore in which invariant they can honestly
#   maintain. On THIS carrier both denote the same total function — the product,
#   with the dimensionless shape sent to 0 — so shipping them separately would be
#   two ids for one rival refuted at one point for one reason. They are merged
#   into the single headline rival; nothing is lost, since the sub-domain and the
#   refutation are identical.
# ADDED (pos-commuted-factor-order): the sibling has no factor-order positive
#   because its fold spelling was not at issue. Here the frozen loop multiplies
#   the exposed dimension on a particular side of the running total, and the
#   frozen proof is tuned to that side — so a correct impl that commutes it is a
#   real SPEC-TOO-STRONG probe, and the one positive that exercises retuning the
#   proof rather than reusing it.
# ADDED (weak-drops-trailing-dimension): the sibling attacks only the FIRST
#   entry. On this carrier the fold runs from the far end, so the trailing entry
#   is a separately-attackable position: a spec pinning only one end would admit
#   the other rival. Checked out-of-band that neither rival's witness refutes the
#   other, so these are two genuine near-misses and not one case twice.
# ADDED (weak-additive-combiner): every sibling rival attacks WHICH entries are
#   folded; none attacks HOW. Since `prodSeq` is transparent here, a rival that
#   reads every entry in order and combines them additively is a distinct
#   SPEC-TOO-WEAK probe and the only one aimed at the combining operation.
# DROPPED (a reversed fold): considered and REJECTED as a rival, because it is
#   not actually wrong on this carrier. Folding the dimensions in the opposite
#   order denotes the SAME value (the product over `Nat` commutes), so
#   `prodSeq dims.reverse = prodSeq dims` and no witness can discriminate — the
#   attempt was built and its witness FAILED against the rival, as it should.
#   Reported rather than shipped: a reject case whose witness does not
#   discriminate would pass for the wrong reason.
# VACUOUS (the two frame-mutation rivals): the sibling's input carries only a
#   fractional read permission, so a write to it (an indexed store, an append) is
#   rejected by the permission system — a mandatory class there. This backend is
#   referentially transparent: `dims` is an immutable value, the method declares
#   no `mut` binder, and there is no heap and no aliasing, so there is no
#   read-only cell to overwrite and the class collapses. No substitute is
#   fabricated (porting map: vacuous here, not replaced).
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job. This bundle declares no
#   axioms and no deep-model references — the computation is concrete
#   natural-number arithmetic over the input — so there is nothing to probe, and
#   the gate ignores AXIOM_TESTS regardless.
#
# UNWITNESSABLE (the sibling's weak-nonterminating) — the spec REJECTS this
#   class; an earlier revision of this footer claimed the opposite and was wrong.
#   The sibling's contract carries an explicit termination obligation, so its
#   spinning rival is rejected by the obligation system. That obligation is
#   present HERE TOO: the frozen solution sets
#   `set_option loom.semantics.termination "total"`, under which a postcondition is
#   claimed of ALL runs and not only terminating ones, so the verifier demands a
#   decreasing measure on every loop AND discharges its descent. Both halves were
#   measured, with the proof reduced to a bare `loom_solve`:
#     (a) spins with NO `decreasing` clause -> REJECTED, exit 1,
#         `error: Decreasing annotations are required in total correctness
#         semantics`. Three spellings, same error.
#     (b) the SAME spinning impl with a bogus measure added (`decreasing k`,
#         where `k := k + 1` strictly increases), returning the unambiguously
#         wrong 0 -> ALSO REJECTED, exit 1, and on the measure's OWN goal:
#         `unsolved goals`, `case «decreasing_1: k»`, residual `k + 1 < k`.
#   An earlier revision of this footer recorded (b) as VERIFYING at exit 0 and
#   concluded that the hole survives, gated behind an annotation that is never
#   checked. That is RETRACTED: (b) is rejected, so no annotation launders the
#   obligation and no hole survives. Case (b) is the important half to have
#   measured, because it is the shape that cannot be dismissed as merely the
#   missing-annotation linter. See the withdrawn descent-enforcement finding
#   below for the full rebuild, including the frozen-measure-only variants.
#
#   This class is therefore NOT a verify-does-not-imply-resolve break, and nothing
#   is escalated. It is separately not
#   shippable as an expect="reject" case on this carrier, for a mechanical reason
#   that was measured rather than assumed: a reject case must carry a witness
#   that HOLDS OF THE RIVAL, and the gate builds that witness in a file
#   containing the rival's own module. The diverging rival's module does not
#   elaborate at all (it is rejected before any tester is derived), so
#   `arrayLengthTester` never reduces there and the witness build fails against
#   the rival — `witness-unproven`, which the gate correctly refuses. A
#   `witness_reference` cannot rescue it either: that substitutes the SUBJECT
#   side of the refutation, not the rival side. The argument covers BOTH cases,
#   since both are rejected: (a) is refused at elaboration by the annotation
#   requirement and (b) on its own descent goal, and in either shape the rival's
#   module fails to build, so the witness derived from it never elaborates. No
#   case is shippable, and there is no break to escalate.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct points):
#     dims — [] (length 0), [0] (length 1, zero entry), [2,3] (length 2, two
#            distinct non-unit entries), [7,1] (length 2, non-unit LEADING),
#            [1,7] (length 2, non-unit TRAILING), [3,3,3,3] (length 4).
#   Distinctness is MEASURED, not asserted: each rival's witness was built
#   against the OTHER end's rival, and each survives there (the leading-drop
#   rival is not refuted at [1,7], the trailing-drop rival is not refuted at
#   [7,1] — both exit 1, `decide` proving the tester claim false only at the
#   rival's own point). So the two end-attacks are genuinely two near-misses and
#   not one point spelled twice.
#   `dims` is the SOLE input binder and no two rivals share a point, so the
#   battery demonstrates the clause's dependence on the sequence's length, on the
#   presence of a zero entry, on the entry at each END, and on a large product —
#   rather than pinning one shape. All three sub-behaviours of the single
#   top-level clause are attacked: EMPTY CASE
#   (weak-empty-shape-collapses-to-zero), EVERY FACTOR (weak-constant-one,
#   weak-identity-seed-zero, weak-drops-leading-dimension,
#   weak-drops-trailing-dimension), and THE COMBINER (weak-additive-combiner,
#   weak-identity-seed-zero).
AXIOM_TESTS = []
