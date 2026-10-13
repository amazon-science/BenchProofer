"""properties.py — G-PBT falsification battery for sympy__sympy-13551 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct productOverRange`` obligation survives with a
byte-identical STATEMENT) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the witness SUBJECT — which on this cell is the declared
``witness_reference``, NOT the frozen solution, because gold cannot decide the
claim in either direction. See the CARRIER NOTE.

DEFENDED SURFACE (one contracted method):

  productOverRange (M : List (List Rat)) (width : Nat) return (out : Rat)
    require ∀ r ∈ M, r.length = width      ← rectangularity (all positions
                                               contribute the same set of parts)
    require ∀ r ∈ M, rowSum r ≠ 0          ← MODELING BOUNDARY: a position whose
                                               total is 0 makes the repository's
                                               closed form an undefined value
                                               with no rational image, so no
                                               ``Rat`` output is claimed there
    ensures  out = prodOfSums M            ← LOAD-BEARING

``prodOfSums`` is a total, fully-unfolded front-recursive ``def`` over the
method's own argument ``M``: the running product, across all index positions, of
each position's total ``rowSum`` (``rowSum`` sums the additive part-values
contributed at one position). It is GROUNDED in the input — a function of ``M``,
not an opaque answer key — so returning it directly IS the correct value (it
doubles as the cheapest honest positive control), and there is no "wrong echo"
to build; the ungrounded-oracle-echo class is therefore N/A here.

The wrong pre-change behaviour the fix repairs is the TRANSPOSE aggregation:
for each additive part (column), take the product of that part's values across
all positions, then SUM those per-part products. That is ``sumOfProds`` —
equal to the genuine product of positional totals only when at most one part is
nonzero at each position, and wrong in general. On the issue's F2P shape (two
positions, part-values [1,2] and [1,4]) the genuine product is (1+2)*(1+4)=15
while the transpose gives (1*1)+(2*4)=9 — the 15/2 vs 9/2 of the reported issue.
The postcondition must REJECT it (the frozen ``Solution_prepatch.lean`` is
exactly this transpose skeleton and its ``prove_correct`` fails — G-DIFF).

THE INPUT BINDER of the post-image is ``M`` (``width`` appears only in the
``require`` clauses, not the ``ensures``, so it is not a postcondition binder to
attack). The reject witnesses below vary ``M`` across position-count (0, 1 and 2)
and part-width (1 and 2), with positional totals driven away from 1 so the
surplus factor is genuinely observable — no rival is refuted at an input another
rival already pins. The EMPTY range (``M = []``) is carried by its own rival
(``weak-empty-range-zero``): it is the one point of the domain the value and
partial-domain rivals structurally cannot reach, since each of them is refuted at
a non-empty input and the constant-1 rival is deliberately CORRECT there.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * VALUE / prepatch-transpose — the load-bearing discriminator. Ported as
    ``weak-sum-of-part-products`` (this IS the pre-change behaviour: product per
    column, summed over columns), refuted at the F2P shape.
  * PARTIAL-DOMAIN — the sibling's ``partial-domain-empty-only`` and
    ``partial-domain-drop-first`` rivals both attack the post-image's VALUE on a
    strict sub-domain. Ported as ``weak-constant-one`` (right only on the empty
    range, where the empty product is 1) and ``weak-drop-first-position`` (right
    only when the first position's total is 1; drops one factor otherwise).
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling class
    exists because a read-only input may carry a fractional heap permission an
    impl can overwrite (``Acc(list_pred(base), 1/2)``). Lean and Velvet are
    referentially transparent: ``M`` is an immutable ``List (List Rat)`` value,
    this bundle declares NO ``mut`` binder among the inputs, there is no heap and
    no aliasing, so there is no read-only input to mutate and no substitute probe
    to build. Reported as N/A, not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A (see above): ``prodOfSums`` is a total,
    fully-unfolded ``def`` of the method's own argument; the ``axioms`` region is
    empty. There is no answer key to echo. Replaced by honest cheapest / reshape
    POSITIVE CONTROLS and one admissibility positive.
  * DIVERGENCE / NON-TERMINATION — the frozen bundle sets
    ``loom.semantics.termination "total"``, so the verifier DOES discharge a
    termination obligation and a diverging rival is genuinely rejected. Measured
    under audit, two shapes, both exit 1: a loop with the ``decreasing`` clause
    REMOVED fails at elaboration (``Decreasing annotations are required in total
    correctness semantics``), and a loop that keeps ``decreasing i`` but never
    shrinks ``i`` in its body fails on the ``ensures`` goal. Neither is shipped as
    a case: the first is rejected by the LINTER before the spec is consulted (so
    its rejection attributes nothing to the postcondition), and the second cannot
    carry a discriminating witness — its ``.run`` is a ``while`` that does not
    reduce in the kernel, which is the same carrier limit the CARRIER NOTE
    documents, and ``_WITNESS_REF`` cannot serve as the subject because the claim
    to be refuted is about a term that never normalises. Measured: a witness
    against the non-terminating rival fails (exit 1, ``unsolved goals ⊢ ¬(…
    forIn Lean.Loop.mk 1 …)``), i.e. the witness does not even hold of the rival,
    so the case would be recorded ``witness-unproven``. Recorded as a limit of the
    WITNESS carrier, not as a spec hole and not as a vacuous class: under
    ``termination "total"`` a postcondition is claimed of ALL runs rather than only
    of terminating ones, the termination obligation is a real proof goal here, and
    only the machine-checked refutation is unbuildable. Spec-side verdict on a
    diverging rival: REJECT.

WITNESS mechanics — THE Rat DECIDABLE BOUNDARY. The spec is a ``method``
contract, not a bare predicate. Velvet's tester machinery
(``productOverRangeTester``) is available, but its inner postcondition check is a
``decide`` over ``Rat`` equality, and ``decide`` reduces the ``Decidable``
instance rather than computing the value — over ``Rat`` it gets STUCK at
``(Rat.mul a b).num`` and never yields ``isTrue``/``isFalse`` (measured), so a
tester-based witness cannot close by ``decide`` here. Instead each witness states
the refutation DIRECTLY over the method's own executable ``.run``:

    (productOverRange <input> <width>).run ≠ DivM.res (prodOfSums <input>)

unfolds the (loop-free) rival with ``simp only`` and discharges the residual
``Rat`` (dis)equality with ``simp [Rat.mul_def, Rat.add_def, Rat.normalize]``
(the guide's Rat-unfolding recipe — ``decide``/``rfl`` alone are stuck on
``Rat``). Each reject rival is written LOOP-FREE (an expression over the pure
helpers, or a branch on one) so its ``.run`` unfolds under ``simp only``; this
is a witnessing convenience, not a weakening — the frozen spec is untouched and
each rival's divergence from ``prodOfSums`` is real at the witnessed input. No
``sorry``/``admit``/``native_decide``/``axiom`` is used, and every witness
carries NO hypotheses (fully concrete inputs), so the binder-consistency check
is trivial.

CARRIER NOTE — WHY EVERY REJECT CASE NAMES A ``witness_reference``. This file
previously justified the gold-side failure by "gold's ``while`` loop is opaque to
the kernel, so the disequality cannot be proven", and offered as the stronger
fact that each witness ALSO fails against a loop-free correct impl. The first
half is a statement about loop shape, not about the claim, and re-measured under
audit with real builds it turns out to carry no information at all. Per reject
case, against the FROZEN solution:

  * the witness's own claim (``… .run ≠ DivM.res …``)  -> exit 1,
    ``unsolved goals ⊢ ¬(NonDetT.run do let r ← forIn Lean.Loop.mk …)``
  * the FORGED opposite claim (``… .run = DivM.res …``) -> exit 1, the SAME
    ``unsolved goals`` on the SAME un-normalised ``forIn Lean.Loop.mk`` term

Gold's exit code is identical for a claim and its negation, so it discriminated
neither: a witness asserting gold is CORRECT at that input would have been
recorded as a refutation just as readily. Confirmed a third way — a claim that is
plainly TRUE of gold (``(productOverRange [[2,3]] 2).run = DivM.res (prodOfSums
[[2,3]])``) also fails against gold with that same error. The frozen ``while``
never reduces, so nothing stated over gold's ``.run`` is decided in either
direction. Note this failure shape is ``unsolved goals``, which matches NONE of
the gate's stuck-reduction screens, so the gate could not see it.

Loop-freeness of the RIVAL is not the property the two-build check needs;
kernel-reducibility of the SUBJECT is. So each reject case below carries an
explicit ``witness_reference``: the ``pos-cheapest-direct`` source, a loop-free
impl of this same byte-identical spec that the gate independently checks (a)
shares the frozen spec and (b) VERIFIES, before refuting the witness against it.
An impl the verifier accepts cannot violate its own spec, so a genuine "the spec
is violated here" statement must still fail against it — and against THAT subject
the exit code TRACKS the claim (re-measured per case with real builds):

  * the witness's claim      -> exit 1, residual goal ``⊢ False`` — a semantic
    refutation: ``simp`` fully evaluated the rival's ``.run`` and the alleged
    disequality is FALSE of a correct impl
  * the FORGED opposite      -> exit 0, green (and ``No goals to be solved``
    once the now-redundant trailing ``Rat`` simp is reached)

That pair is the genuine discriminator, and it is what makes each rejection
attributable to the spec rather than to a tactic mismatch: a merely
reshaped-but-correct rival could carry none of these witnesses, because each
disequality is refutable against a verifying impl of the same spec.

A branching rival needs its ``ite`` reduced (``if_true``/``ite_true``) before the
residual ``Rat`` (dis)equality is even reachable: without that the goal stalls at
``Decidable (… (if True then … else …) ≠ …)``, which no tactic here can
synthesize. Hence the separate unfold set for the empty-range witness.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the changed
product is modeled DEEPLY as ``prodOfSums`` — mapping.md §3: no A-reference, no
consumed axiom, ``exp``/``log``/``Sum`` are not axiomatized). There is no
axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13551"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single productOverRange
# ---- impl region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap), so every edit keeps same_spec by construction and leaves the
# ---- `prove_correct productOverRange` STATEMENT intact. ----

# The WHOLE gold impl body (the backward `while` fold). Rivals that reshape the
# executable surface entirely swap on this block.
_IMPL_BODY = (
    "    let mut acc : Rat := 1\n"
    "    let mut i := M.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ M.length\n"
    "      invariant acc = prodOfSums (M.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let r := M[i - 1]!\n"
    "      acc := rowSum r * acc\n"
    "      i := i - 1\n"
    "    return acc"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

# The single loop-body accumulation line, wholly inside the impl region and
# unique. The reshape positive names the per-position total in a local `let`,
# leaving the surrounding loop, invariants and the frozen proof script intact.
_ACC_STEP = (
    "      let r := M[i - 1]!\n"
    "      acc := rowSum r * acc\n"
)
assert _BASE.count(_ACC_STEP) == 1, "acc-step anchor drift"

# The impl-start marker line (unique); the admissibility case inserts an
# in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, may retune it without
# ---- touching the spec or dropping the obligation). Unique. ----
_PROOF_GOLD = (
    "prove_correct productOverRange by\n"
    "  loom_solve\n"
    "  rw [prodOfSums_drop_step M i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# A loop-free proof body: when the impl is a single expression there is no loop
# invariant to peel, so `loom_solve` alone either closes (a correct reshape) or
# FAILS (a reject rival — which is the point). Reject rivals retune to this shape
# so the rejection is attributable to the spec (the witness), not to a proof
# script tuned to a loop that no longer exists.
_PROOF_FLAT = "prove_correct productOverRange by\n  loom_solve"

# The retuned proof for the admissibility case: it discharges the extra in-region
# assert (a decidable-looking Rat equality, closed by the Rat-unfolding recipe)
# AND the loop-step goal (the frozen `rw`/`simp_all`), via a `first` that tries
# the loop-step branch before the assert branch. `done` forces each branch to
# fully close so `first` cannot leave a half-solved goal open.
_PROOF_ADMISS = (
    "prove_correct productOverRange by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | (rw [prodOfSums_drop_step M i (by omega) (by omega)]; simp_all; done)\n"
    "    | (simp only [prodOfSums, rowSum, List.foldr]; "
    "simp [Rat.mul_def, Rat.add_def, Rat.normalize]; done)"
)


def _variant_flat(body):
    """Reshape the impl into a single loop-free expression AND retune the
    (elided) tactic body to the loop-free shape so the rejection is attributable
    to the spec, not to a proof script tuned to a loop that no longer exists."""
    return _swap(_swap(_BASE, _IMPL_BODY, body), _PROOF_GOLD, _PROOF_FLAT)


# ---- THE WITNESS SUBJECT. `return prodOfSums M` under a bare `loom_solve`: a
# ---- loop-free impl of the byte-identical frozen spec, which the gate checks
# ---- both shares that spec and VERIFIES before refuting any witness against it
# ---- (it is also shipped as the `pos-cheapest-direct` positive, so the battery
# ---- independently requires it to verify). It replaces the frozen solution as
# ---- the second build's subject because gold's `while` never reduces in the
# ---- kernel and its exit code is therefore identical for a claim and its
# ---- negation — see the CARRIER NOTE in the module docstring. This impl DOES
# ---- reduce, so the exit code tracks the claim: honest witness -> 1 with
# ---- residual `⊢ False`, forged opposite -> 0.
_WITNESS_REF = _variant_flat("    return prodOfSums M")


# ---- witness builder. Reaches the post-image DIRECTLY over the method's own
# ---- `.run` (the tester's inner `decide` is stuck on `Rat` — see the module
# ---- docstring). `simp only` unfolds the loop-free rival's executable; the
# ---- second `simp` discharges the residual Rat (dis)equality. Checked in a file
# ---- whose `prove_correct` block has been stripped, so no tactic script can
# ---- mask the verdict. The refutation is checked against `_WITNESS_REF`, not
# ---- against the frozen solution: gold's `while` never reduces in the kernel, so
# ---- a claim and its negation fail there identically (CARRIER NOTE). Against the
# ---- reference the honest claim leaves `⊢ False` and the forged opposite goes
# ---- green, so the exit code carries the claim. ----
_W_UNFOLD = (
    "  simp only [productOverRange, NonDetT.run, prodOfSums, rowSum, "
    "List.range, List.range.loop, List.drop, List.foldr, pure]\n"
)
_W_RAT = "  simp [Rat.mul_def, Rat.add_def, Rat.normalize]\n"


def _witness(inp, width):
    return (
        f"example : (productOverRange ({inp} : List (List Rat)) {width}).run\n"
        f"    ≠ DivM.res (prodOfSums ({inp} : List (List Rat))) := by\n"
        + _W_UNFOLD + _W_RAT
    )


# A rival that BRANCHES needs its `ite` reduced before the residual Rat
# (dis)equality is reachable: without `if_true`/`ite_true` the goal stalls at
# `Decidable (… (if True then … else …) ≠ …)` and `decide`/`simp` cannot
# synthesize the instance (measured — three tactic shapes failed on the rival
# before the `ite` reduction was added). The empty-range witness therefore uses
# its own unfold set rather than `_W_UNFOLD`.
_W_UNFOLD_ITE = (
    "  simp only [productOverRange, prodOfSums, List.isEmpty, if_true, ite_true,\n"
    "    NonDetT.run, NonDetT.pure, pure]\n"
)


def _witness_empty():
    """Refutation at the EMPTY range — stated over `M = []`, the one sub-domain
    the value/partial-domain rivals cannot reach (each of them is refuted at a
    NON-empty input, and the constant-1 rival is deliberately CORRECT there)."""
    return (
        "example : (productOverRange ([] : List (List Rat)) 0).run\n"
        "    ≠ DivM.res (prodOfSums ([] : List (List Rat))) := by\n"
        + _W_UNFOLD_ITE + _W_RAT
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the executable
    # surface (and, where the loop is dropped, retunes the elided tactic body).
    # =====================================================================
    {
        "id": "pos-cheapest-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: `prodOfSums` is grounded in `M`, so returning it
        # directly IS the correct value. No loop, so the proof is loop-free.
        "module": _variant_flat("    return prodOfSums M"),
        "rationale": "prodOfSums is GROUNDED in the argument M (a total, "
                     "fully-unfolded front-recursive def), so returning it "
                     "directly satisfies `out = prodOfSums M` on the whole "
                     "domain. An honest cheapest impl MUST verify; if it cannot "
                     "the postcondition is SPEC-TOO-STRONG. This also serves as "
                     "the grounded-oracle positive control: there is no WRONG "
                     "echo because the oracle is a function of the input, not an "
                     "opaque answer key.",
    },
    {
        "id": "pos-reshape-named-total",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different CORRECT impl: same backward loop and invariants,
        # but the per-position total is bound to a local `let t` AND the
        # accumulation is COMMUTED (`acc * t`, not `t * acc`). The commutation is
        # what makes this a real reshape: a bare `let` leaves the accumulation
        # term syntactically identical, so the frozen proof script closes it
        # unchanged and the case tests nothing beyond name-binding. Commuting the
        # multiplication genuinely changes the term `loom_solve` presents, so the
        # (elided) tactic body must be retuned with `Rat.mul_comm` — measured:
        # with the frozen script this variant FAILS (`unsolved goals` on
        # `invariant_2: acc = prodOfSums (M.drop i)`), and it verifies only once
        # commutativity is supplied. That is the SPEC-TOO-STRONG question worth
        # asking — the spec must admit either multiplication order.
        "module": _swap(
            _swap(
                _BASE, _ACC_STEP,
                "      let r := M[i - 1]!\n"
                "      let t : Rat := rowSum r\n"
                "      acc := acc * t\n"),
            _PROOF_GOLD,
            "prove_correct productOverRange by\n"
            "  loom_solve\n"
            "  rw [prodOfSums_drop_step M i (by omega) (by omega)]\n"
            "  simp_all [Rat.mul_comm]"),
        "rationale": "naming the per-position total in a local `let t` and "
                     "COMMUTING the accumulation (`acc * t`) multiplies the same "
                     "factors in the opposite order, so `out = prodOfSums M` "
                     "still holds — `Rat` multiplication is commutative. The "
                     "commuted order is a genuinely different accumulation term "
                     "(the frozen tactic script does NOT close it; the retuned "
                     "one supplies `Rat.mul_comm`), so this probes whether the "
                     "postcondition is insensitive to the order in which the "
                     "positional totals are combined. A correct reshape MUST "
                     "verify (else SPEC-TOO-STRONG over the shape of the "
                     "accumulation step).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method DOES carry `require` clauses, but the residual
    # admissibility risk that also matters on this total-Rat domain is that the
    # post-image is UNSATISFIABLE / DEGENERATE at the interesting point (a spec no
    # impl can meet reads exactly like one every impl meets). This case discharges
    # an in-region `assert`, at the F2P-shaped input (two positions, part-values
    # [1,2] and [1,4]), that the post-image is NON-DEGENERATE: the product of
    # positional totals there is exactly 15, i.e. the genuine product (3*5), NOT
    # the transpose 9. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned only to clear the extra
    # assert goal (allowed — the tactic body is elided from the spec view). The
    # assert is LIVE: replacing 15 with a false value (e.g. 16) leaves an unsolved
    # goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss "
                  "(prodOfSums ([[1,2],[1,4]] : List (List Rat)) = 15))\n"),
            _PROOF_GOLD, _PROOF_ADMISS),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped input: for two positions with part-values [1,2] "
                     "and [1,4] it demands the product of positional totals be "
                     "exactly 15 = (1+2)*(1+4), the genuine product — NOT the "
                     "transpose 9 = (1*1)+(2*4) the pre-change behaviour gives. "
                     "The in-region assert must discharge (else the obligation is "
                     "unsatisfiable / degenerate at the point the fix cares "
                     "about); the impl is kept verbatim so `out = prodOfSums M` "
                     "still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is LOOP-FREE so
    # its `.run` unfolds under the witness `simp only`; the frozen spec is
    # untouched.
    # =====================================================================
    {
        "id": "weak-sum-of-part-products",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change TRANSPOSE aggregation: for each additive part (column j),
        # take the product of that part's values across all positions, then SUM
        # those per-part products. This is the load-bearing discriminator the
        # bundle exists to defend (== the frozen prepatch skeleton, sumOfProds).
        "module": _variant_flat(
            "    return (List.range width).foldr "
            "(fun j s => (M.foldr (fun r p => r[j]! * p) 1) + s) 0"),
        "refinement": "this is the pre-change behaviour exactly: it distributes "
                      "the iterated multiplication over the additive parts — for "
                      "each part the product across every position is taken and "
                      "those are summed (the transpose aggregation). For the "
                      "issue's shape (two positions, part-values [1,2] and [1,4]) "
                      "it yields (1*1)+(2*4)=9 where the genuine product of "
                      "positional totals is (1+2)*(1+4)=15, so the failing test — "
                      "which pins the genuine product (15/2, not 9/2) — still "
                      "fails. It would NOT resolve.",
        "rationale": "REJECT from `out = prodOfSums M`: `prodOfSums` is the "
                     "product of the per-position totals, and this impl computes "
                     "the sum of the per-part products, which differ whenever "
                     "more than one part is nonzero at some position. Verifying "
                     "would be SPEC-TOO-WEAK (the clause would not force the "
                     "genuine product). Refuted at M=[[1,2],[1,4]] (two positions "
                     "of width 2 — the F2P shape, 15 vs 9).",
        "witness": _witness("[[1,2],[1,4]]", 2),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-constant-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: return the empty product (1) unconditionally. Correct
        # ONLY on the empty range (prodOfSums [] = 1); wrong on every non-empty
        # input.
        "module": _variant_flat("    return 1"),
        "refinement": "returning the empty product (1) regardless of the input "
                      "makes every non-empty finite product collapse to 1 — the "
                      "degenerate 'no product taken' behaviour. It resolves "
                      "nothing: the failing test needs the genuine product "
                      "(15/2), this gives 1/2. A real patch shaped this way would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = prodOfSums M`: a constant 1 satisfies "
                     "the clause only on the empty range (where the empty product "
                     "is 1); for any non-empty M whose product of positional "
                     "totals is not 1 the two disagree. Verifying would leave the "
                     "post-image unpinned on the whole non-empty domain "
                     "(partial-domain SPEC-TOO-WEAK). Refuted at M=[[2,3]] (a "
                     "single position of width 2 whose total 5 ≠ 1 — a "
                     "position-count and total axis the F2P rival does not "
                     "probe).",
        "witness": _witness("[[2,3]]", 2),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-drop-first-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain / off-by-one: take the product over every position EXCEPT
        # the first, dropping one positional total. Correct only when the first
        # position's total is 1 (a measure-zero sub-domain).
        "module": _variant_flat("    return prodOfSums (M.drop 1)"),
        "refinement": "dropping the first position computes the product over "
                      "positions 1..n instead of 0..n — it omits one factor. On "
                      "any input whose first positional total is not 1 the "
                      "reported product is short by that factor, so the failing "
                      "test — which pins the full product over the whole range — "
                      "still fails. A real `range(a+1, n)` / skip-first bound "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = prodOfSums M`: `prodOfSums` multiplies "
                     "the total at EVERY position and this impl skips position 0, "
                     "so the two disagree whenever the first total ≠ 1. Verifying "
                     "would leave the leading position unpinned (partial-domain "
                     "SPEC-TOO-WEAK). Refuted at M=[[3],[2]] (two positions of "
                     "width 1: full product 3*2=6, drop-first 2 — a width axis "
                     "and a first-total ≠ 1 that no other rival probes).",
        "witness": _witness("[[3],[2]]", 1),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-empty-range-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # BOUNDARY sub-domain: correct on every NON-empty input, wrong only at the
        # empty range, where it reports 0 instead of the empty product 1. The three
        # rivals above are each refuted at a non-empty input and the constant-1
        # rival is deliberately RIGHT at the empty range, so without this case the
        # empty range is the one point of the domain no witness pins — a rival
        # could get the boundary wrong and every other case would still pass.
        "module": _variant_flat(
            "    if M.isEmpty then\n"
            "      return 0\n"
            "    else\n"
            "      return prodOfSums M"),
        "refinement": "special-casing the empty range to 0 is the classic "
                      "empty-product error: an iterated multiplication over an "
                      "EMPTY range must be the multiplicative identity 1, not the "
                      "additive identity 0. A real patch shaped this way would "
                      "make every product over a vacuous range collapse to zero, "
                      "and because that zero then propagates through the "
                      "surrounding division and any enclosing product, it "
                      "corrupts the degenerate-range behaviour the existing "
                      "range-convention tests pin. It resolves nothing: the "
                      "failing test needs the genuine product over a non-empty "
                      "range, and a patch wrong at the boundary is not the fix. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = prodOfSums M`: `prodOfSums [] = 1` by "
                     "definition (the empty product is the multiplicative "
                     "identity), so returning 0 there contradicts the clause at "
                     "M = []. Verifying would leave the EMPTY-RANGE boundary "
                     "unpinned while every non-empty input stayed correct — the "
                     "narrowest partial-domain SPEC-TOO-WEAK available here, and "
                     "the only sub-domain the other three rivals cannot reach "
                     "(each is refuted at a non-empty input, and the constant-1 "
                     "rival is deliberately CORRECT at the empty range). Refuted "
                     "at M = [] (0 vs the empty product 1).",
        "witness": _witness_empty(),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals — 1 of them a
# permission-frame-mutation rival) plus 2 AXIOM_TESTS. This bundle models the
# changed operation DEEPLY (the product of positional totals `prodOfSums` via
# `rowSum`, spelled-out arithmetic over `Rat`), so there is no axiom and no
# permission surface; the value surface (product-of-totals vs the transpose)
# carries across intact.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-cheapest (echo prod_of_totals) -> pos-cheapest-direct            PORTED
#   pos-reshape-commute                -> pos-reshape-named-total        PORTED
#   admiss-fshape                      -> admiss-postimage-nondegenerate RE-AIMED
#   frame-mutate-base                  -> (none)                         VACUOUS
#   uniq-sum-of-part-products          -> weak-sum-of-part-products      PORTED
#   partial-domain-empty-only          -> weak-constant-one              PORTED
#   partial-domain-drop-first          -> weak-drop-first-position       PORTED
#   ax-ref-soundness / ax-ref-cont.    -> (none)                         DROPPED (G-AX lane)
#   (no sibling)                       -> weak-empty-range-zero          ADDED
#
# 5 ported, 1 re-aimed, 1 added, 1 vacuous, 2 axiom-lane dropped.
#
# ADDED (weak-empty-range-zero): the sibling has no empty-range rival — on that
#   carrier the empty case is covered incidentally, because its `partial-domain-
#   empty-only` rival is refuted only at non-empty inputs while nothing pins the
#   boundary itself. Audited here: with the three ported rivals alone, an impl
#   that is correct everywhere EXCEPT the empty range (returning the additive
#   identity 0 instead of the empty product 1) is refuted by NO witness in the
#   battery, so the boundary was the one unpinned point of the domain. The rival
#   closes it; measured rival exit 0 / reference exit 1, the reference's residual
#   goal being `⊢ False`. (The earlier record here read "gold exit 1, gold's
#   residual goal being the un-evaluated `while` over `prodOfSums []`" — that
#   build did happen, but the un-evaluated `while` is exactly why it proved
#   nothing: see the CARRIER NOTE. The subject is now `_WITNESS_REF`.)
#
# PORT NOTE — `pos-reshape-named-total` was strengthened during audit. As first
#   ported it only bound the per-position total to a local `let t` and kept
#   `t * acc`, leaving the accumulation term SYNTACTICALLY identical to gold's;
#   the frozen tactic script closed it verbatim, so the case verified without
#   testing anything beyond name-binding. It now also COMMUTES the accumulation
#   (`acc * t`), which is a genuinely different term: measured, the commuted body
#   FAILS under the frozen script (`unsolved goals` on
#   `invariant_2: acc = prodOfSums (M.drop i)`) and verifies only once the elided
#   tactic body supplies `Rat.mul_comm`. That is the reshape the sibling's
#   `pos-reshape-commute` actually performs, so the port now matches it.
#
# VACUOUS (frame-mutate-base): the sibling writes into a read-only input that
#   carries only a fractional heap permission (`Acc(list_pred(base), 1/2)`) and is
#   rejected for INSUFFICIENT PERMISSION before any value reasoning. This backend
#   is referentially transparent: `M` is an immutable `List (List Rat)` value,
#   this bundle declares no `mut` binder among the inputs, and there is no heap or
#   aliasing. There is no read-only input to overwrite and no permission system to
#   trip, so the class is vacuous. No substitute is fabricated (per the porting
#   map, this class is legitimately dropped here rather than replaced).
# RE-AIMED (admissibility): the sibling establishes that the half-permission
#   inputs are readable and a normal F2P-shaped input is admitted. There is no
#   permission here; the re-aimed probe covers the residual total-domain risk that
#   the post-image is unsatisfiable / degenerate at the interesting point, by
#   asserting the product of positional totals of the F2P-shaped input (two
#   positions, part-values [1,2] and [1,4]) is exactly 15 — the genuine product,
#   NOT the transpose 9. The assert is live (a false value leaves an unsolved goal
#   — verified against gold).
# DROPPED (ax-ref-*): the sibling's two AXIOM_TESTS validate its deep A-reference
#   for the positional-total product against the real library routine, and that
#   routine's caller-domain containment. This bundle has NO axiom (mapping.md §3:
#   the modeled operation is spelled out deeply as `prodOfSums`, and the library
#   routines it stands for are not axiomatized), so there is no axiom lane to
#   mirror. The axiom lane is G-AX's job and this gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = prodOfSums M` is
#   attacked by all four rivals across distinct sub-domains — the prepatch
#   transpose (product-of-totals vs sum-of-part-products), the do-nothing constant
#   (right only on the empty range), the drop-first off-by-one (right only when
#   the first total is 1), and the empty-range zero (right EVERYWHERE except the
#   boundary) — refuted at FOUR DISTINCT input points. The post-image's only
#   binder `M` is varied across position-count (0, 1 and 2) and part-width (1 and
#   2), with positional totals driven away from 1 so the surplus factor is
#   genuinely observable. `width` appears only in the `require` clauses (not the
#   `ensures`), so it is not a postcondition binder to attack. The four rivals do
#   NOT share a witness: they agree with gold on disjoint regimes (the transpose
#   at single-part positions, the constant at the empty range, drop-first when the
#   first total is 1, the empty-range zero on the whole non-empty domain), so each
#   carries the input that distinguishes it. Note the last two are complementary
#   by construction: the constant-1 rival is CORRECT exactly where the
#   empty-range rival is wrong, so neither subsumes the other and together they
#   pin both the empty boundary and the non-empty interior.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (deep model); this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
