"""properties.py — G-PBT falsification battery for pydata__xarray-3151 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct validateOrdering`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a spec-satisfying subject — here a declared ``witness_reference`` rather
than the frozen solution, whose tester cannot decide; see WITNESS MECHANICS).

DEFENDED SURFACE (one contracted method over a single ``List Dimension`` binder):

  validateOrdering (dims : List Dimension)   return (ok : Bool)
      ensures ok = allDimsOK dims             -- THE load-bearing clause

Each ``Dimension`` carries two fields: ``varies`` (the axis is joined — its
values differ across the combined inputs) and ``index`` (the axis's resulting
ordered values, modelled as order-ranks). ``allDimsOK`` is a total,
fully-unfolded pure function of the method's own input (a front-recursive
conjunction of ``dimOK`` over the axes) in the ``pure`` region; the ``axioms``
region is empty, so there is no opaque answer-key to echo (directive 8). The
method has NO ``require`` clause: every ``dims : List Dimension`` is in scope, so
the partial-domain rivals below are refutable at a concrete input.

The clause ``ok = allDimsOK dims`` decomposes, per axis, into
``dimOK d = !d.varies || isMonotonic d.index`` and ``isMonotonic = isMonoInc ||
isMonoDec``, giving three independently-attackable sub-behaviours:

  * VARIES-GUARD — a non-varying (bystander) axis imposes NO ordering
                   obligation (``!d.varies`` short-circuits ``dimOK`` to true);
                   the discriminating content of the change. A rival that drops
                   the guard rejects a bystander axis the spec exempts.
  * ORDER-TEST   — a varying axis is acceptable iff monotonic in EITHER
                   direction (``isMonoInc || isMonoDec``); a rival that keeps
                   only one direction rejects a genuinely-decreasing joined axis.
  * CONJUNCTION / SHAPE — the result is the conjunction over EVERY axis; rivals
                   that collapse it to a constant, or that skip an axis, break
                   the per-axis pinning.

ONE input binder, free: ``dims``. The reject witnesses vary its length (1 and 2
axes), each axis's ``varies`` flag (both values), and its ``index`` contents
(increasing / decreasing / non-monotonic order-ranks), so no sub-behaviour of
the clause is probed at a single frozen point.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling makes this class
    MANDATORY because ``is_joined`` / ``is_monotonic`` carry a fractional heap
    permission (``Acc(list_pred(x), 1/2)``) a rival can try to overwrite. Lean
    and Velvet are referentially transparent: ``dims`` is an immutable value, the
    method declares no ``mut`` binder, there is no heap and no aliasing. There is
    no read-only field to overwrite and no substitute probe. Not fabricated
    (porting map: vacuous here).
  * NON-TERMINATION: CLOSED BY THE SEMANTICS, not a hole and not a vacuous class.
    An earlier revision of this bullet recorded it as a KNOWN SPEC HOLE, reasoning
    that although this bundle carries
    ``set_option loom.semantics.termination "total"``, a rival that never
    terminates satisfies ``ensures ok = allDimsOK dims`` VACUOUSLY, because no run
    reaches an exit, and so VERIFIES. That inference is exactly backwards. Vacuous
    satisfaction on an unreachable exit is the ``partial`` disposition; under
    ``total`` a postcondition is claimed of ALL runs rather than only terminating
    ones, so the verifier demands a decreasing measure on every loop and discharges
    its descent. The mechanism is in Loom, not in a tactic:
    ``TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop``
    (``Loom/MonadAlgebras/NonDetT/Basic.lean:544``) takes ``measure : β -> Nat``
    and emits the goal ``measure b' < measure b``, while only the
    ``PartialCorrectness`` twin (same file, :211) takes an ``Option ℕ`` and
    DISCARDS it. Measured on this cell, proof reduced to a bare ``loom_solve``: a
    spliced loop that CARRIES a measure its body never changes
    (``let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q do q := q``) is REJECTED at exit 1 on the measure's own goal,
    ``case «decreasing_1: q»``, residual ``⊢ q < q``; one carrying no measure is
    refused earlier by the elaborator. So the velvet spec DOES close what the
    nagini sibling closes with ``Requires(MustTerminate(2))``. Nothing is shipped
    as a reject case, but for a witness-contract reason rather than a spec one: the
    refusal fires on the ``method`` command, so the rival's module never compiles
    and no witness derived from it can elaborate.
  * UNGROUNDED-ORACLE ECHO — N/A. ``allDimsOK`` is a concrete ``def`` over the
    method's own argument (empty ``axioms`` region); the only satisfier is the
    grounded conjunction itself, so there is nothing to echo.
  * PARTIAL-DOMAIN / VALUE — the main class here. Each rival gets the shape right
    and is correct on part of the domain, diverging on one sub-behaviour above.

WITNESS MECHANICS. Each witness reaches the method contract through Velvet's own
tester machinery (``extract_program_for`` / ``derive_tester_for``), in a file
whose ``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``validateOrderingTester dims`` decides POSTCONDITION CONFORMANCE at
``dims``, so ``... = false`` says "this impl violates ``ok = allDimsOK dims``
here". Every rival below is written LOOP-FREE (a ``foldr`` / ``allDimsOK`` /
constant expression) so that its extracted program is kernel-reducible and the
claim decides.

The FROZEN impl is a backward ``while`` fold under
``loom.semantics.choice "demonic"``, and its tester does NOT reduce in the
kernel. That is a carrier limit, NOT a source of discrimination, and it must not
be mistaken for one: measured with real builds, the gold-side ``decide`` fails
with

    Tactic `decide` failed for proposition ... because its `Decidable` instance
    ... did not reduce to `isTrue` or `isFalse`

for the witness's claim AND, byte-identically modulo the claim token, for a
FORGERY asserting the exact OPPOSITE (``... = true``, i.e. that the frozen impl
is CORRECT at that input). Gold's exit code therefore carries NO information
about the claim, and "half 2 holds by construction against gold" would be a
hollow argument — exactly the defect class the gate's stuck-reduction screen
refuses.

So each reject case names an explicit ``witness_reference`` instead: the
loop-free ``return allDimsOK dims`` impl of this same spec, which shares the
frozen spec byte-for-byte and VERIFIES (it is also shipped as the
``pos-alldims-direct`` positive, and the gate re-checks both properties before
using it). An impl the verifier accepts cannot violate its own spec, so a
genuine refutation must still fail there — and against that subject the exit
code TRACKS THE CLAIM, which is what makes it evidence:

    subject                       ``= false`` (spec violated)   ``= true`` (spec holds)
    the rival                     rc 0  (decides: violated)     rc 1
    the reference (verifying)     rc 1                          rc 0  (decides: holds)
    the frozen impl               rc 1  stuck                   rc 1  stuck (no info)

All three columns were measured out-of-band with ``scripts/lean_verify.sh`` for
every case below. The method has no ``require`` clause, so no witness input is
vacuously excluded, and no witness binds a hypothesis (every refutation is stated
at a literal input), so there is no consistency-probe surface.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed axioms; the one library
predicate (pandas monotonicity) is modelled DEEPLY (``isMonoInc`` / ``isMonoDec``)
and validated == the real callee by axiom_check.py (an A-reference, a G-AX
concern). Nothing in the proof rests on an ``axiom``, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3151"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim (between -- impl-start and -- impl-end).
# ---- Full-replacement rivals swap THIS for a loop-free body; the fragment lies
# ---- wholly inside the impl region and is unique (asserted at load). ----
_GOLD_IMPL = (
    "    let mut acc : Bool := true\n"
    "    let mut i := dims.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ dims.length\n"
    "      invariant acc = allDimsOK (dims.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let d := dims[i - 1]!\n"
    "      acc := dimOK d && acc\n"
    "      i := i - 1\n"
    "    return acc"
)
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl region drifted from Solution.lean"

# ---- the loop-body combine step, for the in-loop reshape positive ----
_LOOP_STEP = (
    "      let d := dims[i - 1]!\n"
    "      acc := dimOK d && acc\n"
)
assert _BASE.count(_LOOP_STEP) == 1, "loop body drifted from Solution.lean"

# ---- the accumulator-init line, for prepending an admissibility assert ----
_ACC_INIT = "    let mut acc : Bool := true\n"
assert _BASE.count(_ACC_INIT) == 1, "acc init drifted from Solution.lean"

# ---- the frozen proof block (a tactic body is elided from the consumer spec
# ---- view, so a positive control may retune it without touching the spec or
# ---- dropping the obligation). Unique in the file. ----
_PROVE = (
    "prove_correct validateOrdering by\n"
    "  loom_solve\n"
    "  rw [allDimsOK_drop_step dims i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROVE) == 1, "frozen proof block drifted from Solution.lean"


def _module(body):
    """Full-replacement variant: swap the whole loop body for `body`, keeping
    the frozen proof (which then fails to elaborate against a reshaped impl —
    the module-level rejection; the witness is what attributes it to the spec)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble: reach the method contract through Velvet's tester.
# ---- The tester short-circuits nothing here (no `require` clause), so every
# ---- `validateOrderingTester dims = false` is a real post-image check at dims.
def _witness(call):
    m = "validateOrdering"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n"
            f"example : {call} = false := by\n  decide\n")


# ---- positive-control impls (loop-free / reshaped, MUST verify) ----
# Closed-form: return the modelled conjunction directly. Structurally different
# from the backward accumulator loop, still correct on every input. Retune the
# proof to the one-liner the reshaped impl needs (the `ensures` IS
# `ok = allDimsOK dims`, so the body is definitionally the RHS).
_POS_DIRECT_PROVE = "prove_correct validateOrdering by\n  loom_solve"


# ---- The refutation SUBJECT for every reject case (`witness_reference`).
# ---- The frozen impl's tester does not reduce in the kernel, so its exit code
# ---- discriminates nothing (see WITNESS MECHANICS). This loop-free impl of the
# ---- SAME spec does reduce, shares the frozen spec byte-for-byte, and VERIFIES
# ---- — the gate re-checks both before refuting any witness against it — so a
# ---- witness that fails HERE is refuting a spec-satisfying impl, which is the
# ---- property that makes it a discriminator rather than a tactic mismatch.
def _reference():
    return _swap(_module("    return allDimsOK dims"), _PROVE, _POS_DIRECT_PROVE)

# In-loop reshape: bind the per-axis decision to a typed local before combining
# it into the accumulator. Same backward loop, same value flow; the frozen proof
# still closes (the local is definitionally `dimOK d`).
_POS_LOCALS_STEP = (
    "      let d := dims[i - 1]!\n"
    "      let ok : Bool := dimOK d\n"
    "      acc := ok && acc\n"
)

# Admissibility: keep the frozen impl verbatim and discharge, at entry, a live
# assertion that the post-image is satisfiable AND non-degenerate at an
# F2P-shaped point — the issue's case: a joined+monotonic axis alongside a
# bystander+non-monotonic axis must be ACCEPTED (true), while a joined axis that
# is genuinely non-monotonic must be REJECTED (false). The extra proof bullet
# discharges the assert (`decide`); the rest of the frozen proof is unchanged so
# the `ensures` clause still discharges for the frozen impl.
_ADMISS_INIT = (
    "    assert (with_name_prefix `admiss\n"
    "      (allDimsOK [ {varies := true, index := [1,2,3]},\n"
    "                   {varies := false, index := [1,3,2]} ] = true ∧\n"
    "       allDimsOK [ {varies := true, index := [1,3,2]} ] = false))\n"
    "    let mut acc : Bool := true\n"
)
_ADMISS_PROVE = (
    "prove_correct validateOrdering by\n"
    "  loom_solve\n"
    "  · decide\n"
    "  · rw [allDimsOK_drop_step dims i (by omega) (by omega)]\n"
    "    simp_all"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-alldims-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_module("    return allDimsOK dims"),
                        _PROVE, _POS_DIRECT_PROVE),
        "rationale": "a loop-free impl that returns the modelled per-axis "
                     "conjunction directly is observationally `allDimsOK dims` "
                     "on every input, so `ok = allDimsOK dims` holds on the "
                     "whole domain and the reshaped `loom_solve` closes the "
                     "byte-identical obligation; a correct reshape MUST verify, "
                     "else the postcondition is SPEC-TOO-STRONG (it would reject "
                     "its own model's output).",
    },
    {
        "id": "pos-perdim-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the loop body: bind the per-axis decision to a typed local
        # before combining. Same backward accumulator loop, same value flow;
        # the frozen proof still closes (the local is definitionally `dimOK d`).
        "module": _swap(_BASE, _LOOP_STEP, _POS_LOCALS_STEP),
        "rationale": "binding the per-axis decision `dimOK d` to a typed local "
                     "before folding it into the accumulator computes the same "
                     "conjunction as the frozen body, so `ok = allDimsOK dims` "
                     "still holds and the frozen proof closes unchanged; a "
                     "local-variable reshape of a correct impl must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so no precondition
    # could exclude an F2P-shaped input; the nagini sibling's "a normal input
    # satisfies the precondition" probe is vacuous here. RE-AIMED at the
    # residual risk on a total domain: that the post-image is UNSATISFIABLE /
    # degenerate at the interesting point. The case discharges a live in-region
    # assert that pins the issue's discriminating sub-domain BOTH ways — a
    # bystander+non-monotonic axis alongside a joined+monotonic axis is ACCEPTED
    # (the exact behaviour the fix restores), while a joined axis that is truly
    # non-monotonic is REJECTED. The impl is kept verbatim so the `ensures`
    # clause still discharges too. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "admiss-bystander-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _ACC_INIT, _ADMISS_INIT),
                        _PROVE, _ADMISS_PROVE),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: a bystander (non-varying) axis whose "
                     "values are non-monotonic ALONGSIDE a joined axis that is "
                     "monotonic must be ACCEPTED (true) — the bystander is "
                     "exempt — while a joined axis that is genuinely "
                     "non-monotonic must be REJECTED (false). The in-region "
                     "assert pins both directions (else the obligation would be "
                     "unsatisfiable / degenerate: PRECOND-TOO-STRONG); the impl "
                     "is kept verbatim so the `ensures` clause discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the
    # frozen spec that MUST be rejected, each with a machine-checked refutation
    # witness at a concrete input and the argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is refuted at
    # the smallest/most-specific `dims` that exposes its divergence.
    # =====================================================================
    {
        "id": "weak-drop-varies-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: require monotonicity on EVERY axis, ignoring the
        # `varies` flag. Correct on every joined axis and on a monotonic
        # bystander, but rejects a non-monotonic bystander the spec exempts.
        "module": _module(
            "    return dims.foldr (fun d acc => isMonotonic d.index && acc) true"),
        "refinement": "this IS the pre-fix behaviour: the ordering requirement is "
                      "imposed on every coordinate axis, not only the joined "
                      "ones. On the F2P input the non-monotonic bystander axis "
                      "(varies = false, values ['a','c','b']) is spuriously "
                      "rejected, so the combine raises the ordering error and "
                      "test_combine_leaving_bystander_dimensions FAILS (the "
                      "expected combined result is never returned) — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `ok = allDimsOK dims` via the VARIES-GUARD "
                     "sub-behaviour: `dimOK` short-circuits a non-varying axis to "
                     "true, but the rival still tests its monotonicity, so the "
                     "two disagree on a bystander axis with non-monotonic values. "
                     "Verifying would be SPEC-TOO-WEAK (the exemption is "
                     "unpinned). Refuted at dims=[{varies:=false, "
                     "index:=[1,3,2]}]: gold accepts (true), the rival rejects.",
        "witness": _witness(
            "validateOrderingTester [{varies := false, index := [1,3,2]}]"),
        # Refute against the verifying loop-free impl of this same spec,
        # not against the frozen loop (whose tester cannot decide, so its
        # exit code would track nothing). See WITNESS MECHANICS.
        "witness_reference": _reference(),
    },
    {
        "id": "weak-increasing-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the `varies` guard but reads the order test as ascending-only,
        # dropping the descending disjunct. Correct on every non-varying axis and
        # on every ascending joined axis; wrong on a joined axis whose values are
        # genuinely DECREASING (which pandas — and the spec — accept).
        "module": _module(
            "    return dims.foldr "
            "(fun d acc => (!d.varies || isMonoInc d.index) && acc) true"),
        "refinement": "a counterpart that tested only ascending order would raise "
                      "the ordering error on a joined axis whose combined "
                      "coordinate is monotonically DECREASING — a valid ordering "
                      "the library accepts — so combine would reject a "
                      "well-ordered input and the tests comparing against the "
                      "expected combined result would still fail. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `ok = allDimsOK dims` via the ORDER-TEST "
                     "sub-behaviour: `isMonotonic = isMonoInc || isMonoDec` "
                     "accepts either direction, but the rival keeps only "
                     "`isMonoInc`, so it rejects a joined descending axis the "
                     "spec accepts. Refuted at dims=[{varies:=true, "
                     "index:=[3,2,1]}]: gold accepts (monotonic decreasing), the "
                     "rival rejects. Discrimination comes from the descending "
                     "`index` — the sub-domain no other rival abuses.",
        "witness": _witness(
            "validateOrderingTester [{varies := true, index := [3,2,1]}]"),
        # Refute against the verifying loop-free impl of this same spec,
        # not against the frozen loop (whose tester cannot decide, so its
        # exit code would track nothing). See WITNESS MECHANICS.
        "witness_reference": _reference(),
    },
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Never rejects. Wrong on any joined non-monotonic axis (spec false).
        "module": _module("    return true"),
        "refinement": "a counterpart that never raised would drop the ordering "
                      "error the fix must STILL raise for a genuinely "
                      "non-monotonic JOINED axis, so combine would silently "
                      "accept a mis-ordered join and the tests pinning that error "
                      "would fail. It would NOT resolve.",
        "rationale": "REJECT from `ok = allDimsOK dims`: on a joined axis with "
                     "non-monotonic values the post-image demands false and the "
                     "rival yields true. Refuted at dims=[{varies:=true, "
                     "index:=[1,3,2]}]: gold rejects (false), the rival accepts.",
        "witness": _witness(
            "validateOrderingTester [{varies := true, index := [1,3,2]}]"),
        # Refute against the verifying loop-free impl of this same spec,
        # not against the frozen loop (whose tester cannot decide, so its
        # exit code would track nothing). See WITNESS MECHANICS.
        "witness_reference": _reference(),
    },
    {
        "id": "weak-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Always rejects — the over-strict opposite. Wrong on any all-acceptable
        # input (a joined MONOTONIC axis -> spec true) and on the empty input.
        "module": _module("    return false"),
        "refinement": "a counterpart that always raised would reject valid "
                      "combines — including the intended result whose joined axes "
                      "ARE monotonic — so the expected combined Dataset is never "
                      "returned and the tests fail. It would NOT resolve.",
        "rationale": "REJECT from `ok = allDimsOK dims`: on a joined MONOTONIC "
                     "axis the post-image demands true and the rival yields "
                     "false. Refuted at dims=[{varies:=true, index:=[1,2,3]}]: "
                     "gold accepts (monotonic increasing), the rival rejects. "
                     "Discrimination comes from an ascending joined `index` — a "
                     "point distinct from every other rival's.",
        "witness": _witness(
            "validateOrderingTester [{varies := true, index := [1,2,3]}]"),
        # Refute against the verifying loop-free impl of this same spec,
        # not against the frozen loop (whose tester cannot decide, so its
        # exit code would track nothing). See WITNESS MECHANICS.
        "witness_reference": _reference(),
    },
    {
        "id": "weak-skip-head-axis",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every axis EXCEPT the head (position 0): it drops the first
        # axis by conjoining over `dims.drop 1`. Pins the shape and is correct on
        # the rest of the domain; diverges only when the head axis would fail.
        "module": _module("    return allDimsOK (dims.drop 1)"),
        "refinement": "a counterpart that never inspected the first visited axis "
                      "would miss a genuinely non-monotonic JOINED axis when it "
                      "happens to be first, so combine would fail to raise where "
                      "the fix still must — the tests pinning the ordering error "
                      "on that axis would fail. It would NOT resolve.",
        "rationale": "REJECT from `ok = allDimsOK dims`: `allDimsOK` conjoins "
                     "over EVERY axis, but the rival drops the head, so the two "
                     "disagree whenever the head axis is a joined non-monotonic "
                     "one. Refuted at dims=[{varies:=true, index:=[1,3,2]}, "
                     "{varies:=false, index:=[1]}]: gold rejects (the joined head "
                     "is non-monotonic), the rival accepts (it skips the head). "
                     "Discrimination comes from a 2-axis input pinning EVERY "
                     "axis, not most — the CONJUNCTION/SHAPE sub-behaviour.",
        "witness": _witness(
            "validateOrderingTester [{varies := true, index := [1,3,2]}, "
            "{varies := false, index := [1]}]"),
        # Refute against the verifying loop-free impl of this same spec,
        # not against the frozen loop (whose tester cannot decide, so its
        # exit code would track nothing). See WITNESS MECHANICS.
        "witness_reference": _reference(),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane. The
# sibling contracts a boolean guard `guard_rejects(is_joined, is_monotonic)` over
# two parallel `List[int]` 0/1 flag carriers under fractional-permission framing
# and a MustTerminate obligation. This bundle contracts the SAME modelled core —
# the post-concatenation ordering decision — as `validateOrdering(dims)` over a
# richer `List Dimension` carrier (each axis pairs the `varies` flag with its
# ordered `index` values, so the monotonicity test is modelled DEEPLY here rather
# than passed in as a pre-computed 0/1 flag). The adversarial argument of every
# ported case carries across intact; there is no permission surface here and the
# termination obligation is not expressible.
#
#   sibling case                    -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-flatten-inner-if            -> pos-alldims-direct             PORTED
#   pos-head-locals                 -> pos-perdim-local              PORTED
#   admiss-f2p-bystander            -> admiss-bystander-nondegenerate PORTED (re-aimed)
#   frame-mutate-readonly-is_joined -> (none)                         VACUOUS
#   vacuous-nonterminating-loop     -> (none)                         SPEC-CLOSED
#   weak-drop-is_joined-guard       -> weak-drop-varies-guard         PORTED
#   weak-skip-head-dimension        -> weak-skip-head-axis            PORTED
#   weak-const-false                -> weak-const-true                PORTED (re-aimed)
#   weak-const-true                 -> weak-const-false               PORTED (re-aimed)
#   (no sibling)                    -> weak-increasing-only           ADDED
#   AXIOM_TESTS ([])                -> (none)                          DROPPED (G-AX)
#
# 8 of the 9 sibling SPEC cases PORTED (2 positives, 1 admissibility, 5 rivals);
# one rival added; frame-mutation vacuous; the termination case SPEC-CLOSED (an
# earlier revision recorded it as a known hole; see the DIVERGENCE block below for
# the retraction and the builds); the empty axiom lane dropped.
#
# PORTED (positives): pos-flatten-inner-if collapsed two nested ifs into one
#   conjunction — here the per-axis decision is already one `dimOK`, so the
#   analogous cheapest reshape returns the modelled conjunction `allDimsOK dims`
#   directly (pos-alldims-direct). pos-head-locals bound the head flags to typed
#   locals before testing — here the loop body binds the per-axis decision to a
#   typed local before folding it (pos-perdim-local). Both keep the whole
#   decision, so the frozen/retuned proof closes the byte-identical obligation
#   (both verified out-of-band with real builds).
# PORTED-RE-AIMED (admissibility): the sibling builds the F2P-shaped flag input
#   (is_joined=[1,0], is_monotonic=[1,0]) and asserts the precondition ADMITS it
#   and the grounded oracle yields False. This method has NO `require` clause and
#   no permission surface, so the "precondition admits it" half is vacuous; the
#   re-aimed probe asserts the post-image is NON-DEGENERATE at the F2P-shaped
#   input BOTH ways — a joined+monotonic axis alongside a bystander+non-monotonic
#   axis is ACCEPTED (the fix's content), while a truly non-monotonic joined axis
#   is REJECTED.
# PORTED (rivals): weak-drop-is_joined-guard -> weak-drop-varies-guard (the exact
#   pre-patch bug: test monotonicity on every axis, ignoring `varies`).
#   weak-skip-head-dimension -> weak-skip-head-axis (drop the head axis from the
#   conjunction). weak-const-false/weak-const-true port to the two constant
#   near-misses; the labels are swapped only because this spec returns `ok`
#   (accept) where the sibling returned `rejected` (its logical negation), so the
#   sibling's "always False" cheat maps to this bundle's "always true" accept and
#   vice-versa — the adversarial content (over-permissive vs over-strict) is
#   preserved. Each carries a machine-checked witness that ELABORATES against the
#   rival (rc 0) and FAILS against the declared `witness_reference` (rc 1), whose
#   exit code TRACKS THE CLAIM — the flipped claim `= true` decides the other way
#   there (rc 0), which is what makes the rc 1 a refutation. Refuting against GOLD
#   instead would attest to nothing: its tester is stuck for either claim.
# ADDED (weak-increasing-only): the sibling's `is_monotonic` is a pre-computed
#   0/1 flag, so it has no rival attacking the two-directional order test. Here
#   the order test is modelled DEEPLY (`isMonoInc || isMonoDec`), so a rival that
#   keeps only the ascending disjunct is a distinct SPEC-TOO-WEAK probe — the
#   ONLY rival that abuses a descending `index` — and pins the ORDER-TEST
#   sub-behaviour the deep model introduces.
# VACUOUS (frame-mutation): the sibling makes this MANDATORY (its inputs carry
#   Acc(...,1/2) half-permission a write must fail on). This backend is
#   referentially transparent and the method declares NO `mut` binder — every
#   input is an immutable value with no heap footprint — so there is no read-only
#   field to overwrite and no substitute probe. Not fabricated.
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
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   consumed axioms (the monotonicity callee is modelled deeply — an A-reference
#   validated by axiom_check.py), so there is nothing to probe and the gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 5 distinct input points):
#   dims — [{F,[1,3,2]}], [{T,[3,2,1]}], [{T,[1,3,2]}], [{T,[1,2,3]}],
#          [{T,[1,3,2]},{F,[1]}]: length (1 and 2 axes), `varies` (both values),
#          and `index` (ascending / descending / non-monotonic) all varied. No
#          two rivals share an input tuple.
#   Every sub-behaviour of `ok = allDimsOK dims` is attacked: VARIES-GUARD
#   (weak-drop-varies-guard), ORDER-TEST both directions (weak-increasing-only),
#   the two constant collapses (weak-const-true / weak-const-false), and the
#   per-axis CONJUNCTION/SHAPE (weak-skip-head-axis).
#
# INDEPENDENT AUDIT (adversarial re-derivation with real builds; not the port's
# own self-report). Every case above was rebuilt: 3 positives verify (rc 0), 5
# rivals fail (rc 1), 5 witnesses elaborate against their rival (rc 0) and fail
# against the reference (rc 1) while the FLIPPED claim decides the other way
# there (rc 0) — so each rc 1 tracks the claim. Attack C: each rival's witness
# input was evaluated in both semantics; gold and rival disagree at all 5 points
# (no vacuous case). The admissibility assert is LIVE, not decorative: flipping
# its second conjunct to a false claim makes the variant FAIL with `decide`
# proving the conjunction false, so it is discharged by real evaluation.
#
# Attack D (SPEC-TOO-WEAK probe) — 5 NEW wrong impls the battery does not
# contain, aimed at the least-probed corners; ALL 5 correctly failed to verify,
# so no spec hole was found: strict-increasing (rejects the equal-neighbour
# `[1,1,2]` pandas accepts), any-instead-of-all, empty-input-rejected,
# inverted varies-guard, drop-LAST-axis (the mirror of weak-skip-head-axis).
# Attack E (SPEC-TOO-STRONG probe) — 4 NEW correct reshapes, ALL verify:
# `dims.all dimOK`, `!dims.any (!dimOK ·)`, an explicit `foldr`, and the frozen
# loop with the accumulator conjunction COMMUTED (`acc && dimOK d`). So the spec
# admits its faithful reshapes and rejects the near-misses in both directions.
AXIOM_TESTS = []
