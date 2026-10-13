"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-11310 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct recordRefitTime`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a mutable duration slot):

  recordRefitTime (refit : Bool) (startT : Rat) (endT : Rat)
      (mut refitTime : Option Rat) return (unit : Unit)
    require refitTime = none
    require startT ≤ endT
    ensures refit = true  → refitTime = some (endT - startT)              (E1)
    ensures refit = true  → (∃ t : Rat, refitTime = some t ∧ t ≥ 0)       (E2)
    ensures refit = false → refitTime = none                             (E3)

After a selection step optionally re-does one unit of work on the whole input,
the elapsed span of that re-do is a quantity a consumer reads back. A single
request flag governs whether the re-do (and its timing) happens. ``startT`` and
``endT`` are the two clock readings bracketing the work — read-only environment
inputs whose non-decrease is the second precondition. ``refitTime`` is the
recorded-duration slot: ``mut`` (genuinely written ``none``→``some``), coming in
absent and, when the request flag is set, pinned to EXACTLY the subtraction
``endT - startT`` (not merely "some non-negative value"); when the flag is
clear its post-state is pinned to its unchanged entry value ``none``. Durations
are exact rationals (``Rat``) — a single subtraction of two same-magnitude
readings, so an exact ordered carrier is faithful.

THREE top-level ``ensures`` clauses, of which two are independent:
  (E1) VALUE, on the request branch — the recorded span is EXACTLY
       ``endT - startT``. This is the load-bearing clause: the pre-change code
       recorded nothing, and a value-only F2P would accept any non-negative
       float, so E1 pins the genuine measurement.
  (E3) ABSENT, on the no-request branch — the slot stays ``none`` (directive-5
       frame discipline: ``refitTime`` is ``mut`` but conceptually unchanged on
       this branch, so its post-state is pinned exactly).
  (E2) SIGN, on the request branch — the recorded span is non-negative. E2 is
       NOT independent of E1: given E1 and the precondition ``startT ≤ endT`` it
       follows (``endT - startT ≥ 0``), so any impl meeting E1 meets E2, and any
       impl violating E2 on the request branch already violates E1 (it recorded
       something other than the exact span). No rival attacks E2 in isolation;
       the ``reject-swapped-orientation`` rival records a NEGATIVE span, which is
       simultaneously an E1 violation (wrong value) and an E2 violation (wrong
       sign) — so E2 is exercised as a corollary, not left undefended. See the
       footer accounting.

WITNESS ROUTE — the tester+``decide`` route is DEAD here; witnesses go DIRECT.
``derive_tester_for recordRefitTime`` DOES synthesise a decidable
``recordRefitTimeTester : Bool → Rat → Rat → Option Rat → Bool`` (measured), but
its ``decide`` gets STUCK on BOTH files: the postcondition mixes an
existential over ``Rat`` (E2) with exact ``Rat`` arithmetic (E1), and the
derived ``Decidable`` instance does not reduce (the ``…PostDecidable`` instance
stalls on ``Rat`` (in)equalities — measured, both rival and gold leave
``…Tester … = false`` unreduced). So each reject rival refutes the method's
Hoare triple DIRECTLY at one concrete literal input (the scikit-10844 route):
state ``¬ triple pre (recordRefitTime …) post`` at the input, ``unfold`` the
method, ``simp only [reduceIte, triple_pure, le_Prop_eq]`` reduces the
literal-guarded straight-line body to ``pre → post (final-state)``, feed the
(decidable) precondition to obtain the postcondition conjunction over the
rival's own final ``refitTime``, then observe the offending clause. The residual
``Rat`` (dis)equality is closed by ``simp only [Rat.sub_def, Rat.normalize]``
followed by ``decide`` — the measured normaliser pair (``decide`` alone is stuck
on ``Rat.mul``/``Rat.sub``, see the spec guide's Rat note; ``simp only`` with the
``_def``/normalizer lemmas then reduces the numerals so ``decide`` closes). The
witness is checked in a file whose ``prove_correct`` block has been stripped, so
no tactic script can mask the verdict, and every witness binds NOTHING in its
head — concrete literals only — so the gate's consistency probe is a no-op
(there are no hypotheses that could be jointly unsatisfiable). No
``sorry``/``admit``/``native_decide``/``axiom``. Every witness was SEEN to
discriminate with two real builds: EXIT 0 against the rival, nonzero against the
frozen solution.

GOLD-SIDE FAILURE MODE, established by the B′ forgery pair (audit ``a8``). Three
of the six witnesses fail on gold with ``` `simp` made no progress ``` rather
than with an evaluation, and that message alone does NOT say whether the claim
was refuted or the tactic merely missed. It was re-derived rather than argued,
twice, and both halves say the failure is SEMANTIC:

  * REVEAL. Replacing the closing step with a deliberate type ascription
    (``exact (hv : Nat)``) makes Lean print ``hv``'s real type on each side. On
    the frozen solution every one of the six prints ``hv has type True`` — the
    preceding ``simp only`` PROVED the equation, which is why there is nothing
    left for the next ``simp`` to make progress on. Against each rival the same
    build prints the CONCRETE unproven equation: ``some 0 = some (4 - 1)``
    (const-zero), ``some 8 = some (8 - 3)`` (echo-end),
    ``some (1 - 6) = some (6 - 1)`` (swapped), ``none = some (5 - 2)``
    (never-present), ``((), none).2 = some (3 - 3)`` (zero-boundary), and
    ``some (7 - 3) = none`` (always-present, whose gold side prints the TRUE
    ``((), none).2 = none`` instead of ``True``). ``True`` versus a concrete
    equation is the refutation.
  * FLIP. A claim-flipped witness — same script shape, asserting the OPPOSITE of
    each witness at the same input, i.e. that gold is WRONG in the other
    direction — ELABORATES against the frozen solution (EXIT 0) at all six
    points. Gold's exit code therefore tracks the claim; it is not a constant.

Also checked, because a rival-side EXIT 0 can be as hollow as a gold-side
EXIT 1: each value witness's SCRIPT was re-run against its own rival at an input
where that rival AGREES with gold (const-zero and swapped at ``(true,3,3)``,
echo-end at ``(true,0,5)``, zero-boundary at ``(true,1,4)``). All four FAIL
(EXIT 1) — const-zero and echo-end with ``Tactic `decide` proved that the
proposition … is false``, i.e. the kernel evaluating the agreement and refusing
the refutation. So the rival-side successes are pinned to the disagreement
points the rationales name, not to the script's shape.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally-different but CORRECT
    reshapes (guard the absent case first with an early return; compute the span
    into a typed local then select) must verify under the frozen ``loom_solve``
    proof, else the spec is SPEC-TOO-STRONG on the branch/data shape.
  * ADMISSIBILITY — RE-AIMED + MERGED. The nagini sibling ships two admissibility
    self-calls (a true-branch F2P input; a false-branch + zero-length boundary).
    A literal self-call is INEXPRESSIBLE here — ``recordRefitTime`` calling
    itself makes the method recursive and the elaborator cannot infer a
    termination argument for this signature (measured: ``fail to show
    termination for recordRefitTime``, ``the type Rat does not have a `.brecOn`
    recursor``). The two are RE-AIMED and MERGED into one case whose in-region
    ``assert``s pin the METHOD'S OWN POST-STATE non-degenerate on BOTH branches
    at the SYMBOLIC inputs: present-and-non-negative on the request branch,
    still-absent on the no-request branch. Asserting over closed literals
    instead would be a decidable arithmetic tautology that constrains no
    execution of the method (it would discharge whatever the body wrote), which
    is why the assert names ``refitTime`` after the write. Both halves are live:
    negating either leaves an unsolved goal (measured, EXIT 1).
  * UNGROUNDED-ORACLE ECHO — N/A. E1 pins the value to ``some (endT - startT)``,
    a transparent function of the two reading inputs (the ``axioms`` region is
    empty — no opaque answer key). Any impl that "echoes" ``endT - startT`` IS
    the gold value, so there is no wrong-echo to build; the honest cheapest
    correct impl routes the value through that subtraction, which the positive
    controls cover. In its place the VALUE clause is attacked by constants /
    wrong functions of the inputs that are NOT equal to the grounded span.
  * FRAME / PERMISSION-MUTATION — VACUOUS as a permission attack (Lean/Velvet are
    referentially transparent — ``startT``/``endT``/``refit`` are immutable
    values, no heap, no aliasing, no fractional permission). The nagini sibling
    itself records the frame class N/A (all inputs pass-by-value, no
    ``Acc(x,1/2)`` reference). But the frame ARGUMENT is not lost: ``refitTime``
    IS a ``mut`` slot and E3 pins it unchanged (``none``) on the no-request
    branch (directive-5), so a body that writes it there violates a genuine
    postcondition clause — attacked by ``reject-always-present``.
  * DIVERGENCE / NON-TERMINATION — the nagini sibling carries NO
    ``diverge-*``/``nonterm-*``/``weak-diverge`` case, so there is nothing to
    port. This bundle runs under
    ``set_option loom.semantics.termination "total"`` (read from Solution.lean
    line 4). An earlier revision of this file asserted ``"partial"`` and rested
    a "known spec hole" disposition on it; BOTH halves of that were wrong and
    are corrected here (audit ``a8``).

    Under ``"total"`` the NAIVE diverging rival is genuinely REJECTED: splicing
    ``while True do pure ()`` ahead of the gold body fails with
    ``error: Decreasing annotations are required in total correctness
    semantics`` (measured, EXIT 1, with the frozen proof and with a bare
    ``loom_solve``). So the class is not the corpus-wide ``partial`` hole.

    It is also NOT shippable as a reject case, for a reason that is itself a
    finding. The ``while`` macro's termination check is discharged from the
    ``decreasing`` ANNOTATION, and a rival supplies its own annotations: a loop
    written

        let mut k : Nat := 1
        while k > 0
          invariant k ≥ 1
          done_with k = 0
          decreasing k
        do
          k := k

    diverges (the measure never changes, and ``k ≥ 1`` is preserved) yet
    elaborates, because ``done_with k = 0`` is taken as an ASSUMPTION about the
    exit state rather than an obligation. Together with the invariant it makes
    the post-loop context contradictory (``k ≥ 1 ∧ k = 0``), so every
    ``ensures`` discharges vacuously — measured: this body records
    ``some 999`` on both branches and still VERIFIES under the frozen
    ``loom_solve`` (EXIT 0), as does ``assert False`` placed after the loop.
    A rival the spec ACCEPTS admits no refutation witness, so there is nothing
    to ship in the reject lane; it is escalated as a SPEC/CARRIER finding
    instead (see the FROZEN-SPEC FINDING block in the footer). Not a battery
    gap: no edit to this manifest can close it.

See the footer for the full nagini→velvet accounting.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-11310"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen executable body (the gate/subtract/
# ---- return-else lines strictly inside the single -- impl-start / -- impl-end
# ---- region). Lies wholly inside the impl region and is unique in Solution.lean
# ---- (both facts asserted at load by _swap), so every rewrite keeps same_spec by
# ---- construction and leaves the `prove_correct recordRefitTime` STATEMENT
# ---- intact. The impl comment block above it is left untouched by the rivals
# ---- (it lies inside the region too, but the anchor is the code lines only).
_GOLD_IMPL = (
    "    if refit then\n"
    "      refitTime := some (endT - startT)\n"
    "      return ()\n"
    "    else\n"
    "      return ()"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body and
# ---- the frozen proof (`loom_solve` discharges the decidable assert too).
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- frozen proof body. Elided from the consumer spec view; every rival keeps
# ---- it verbatim (a reject rival is expected NOT to verify and its witness
# ---- carries the evidence). Unique in the file.
_PROOF = "prove_correct recordRefitTime by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "frozen proof body drifted; update _PROOF"

def _impl(new_body):
    """Full Solution.lean variant with ONLY the frozen impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---- witness builder. States the method's Hoare triple at one concrete literal
# ---- input and refutes it; checked in a file whose `prove_correct` block is
# ---- stripped (mirrored here via _STRIPPED for the local sanity builds). The
# ---- post-image is written out verbatim over the literal inputs so the witness
# ---- is self-contained. `refit`/`startT`/`endT` are literals; `refitTime` comes
# ---- in `none` (the precondition). Closes by the direct-triple route.
def _witness(refit, s, e, tail):
    r = "true" if refit else "false"
    return (
        "example :\n"
        "    ¬ triple (l := Prop)\n"
        f"        ((none : Option Rat) = none ∧ ({s}:Rat) ≤ {e})\n"
        f"        (recordRefitTime {r} {s} {e} none)\n"
        "        (fun out =>\n"
        f"            ({r} = true  → out.2 = some (({e}:Rat) - {s}))\n"
        f"            ∧ ({r} = true  → (∃ t : Rat, out.2 = some t ∧ t ≥ 0))\n"
        f"            ∧ ({r} = false → out.2 = none)) := by\n"
        "  unfold recordRefitTime\n"
        "  simp only [reduceIte, triple_pure, le_Prop_eq]\n"
        "  intro hcon\n"
        + tail
    )


# tail for a VALUE rival on the request branch (E1): pull the request-branch
# conjunct, feed the trivial antecedent, inject through `some`, observe the
# recorded value ≠ the grounded span. The residual `Rat` disequality is closed by
# the measured normaliser pair + `decide` (see the module docstring's WITNESS
# ROUTE note on why `decide` alone is stuck on `Rat` arithmetic).
_TAIL_VALUE = (
    "  obtain ⟨h1, _, _⟩ := hcon ⟨trivial, by decide⟩\n"
    "  have hv := h1 trivial\n"
    "  simp only [Option.some.injEq] at hv\n"
    "  revert hv\n"
    "  simp only [Rat.sub_def, Rat.normalize]\n"
    "  decide\n"
)
# tail for the NEVER-PRESENT rival (E1, request branch): the slot stays `none`,
# so the conjunct is `none = some (…)` — refuted by `simp` (no Rat arithmetic).
_TAIL_NEVER = (
    "  obtain ⟨h1, _, _⟩ := hcon ⟨trivial, by decide⟩\n"
    "  have hv := h1 trivial\n"
    "  simp at hv\n"
)
# tail for the ALWAYS-PRESENT rival (E3, no-request branch): the slot is written
# `some (…)`, so the absent conjunct is `some (…) = none` — refuted by `simp`.
_TAIL_ALWAYS = (
    "  obtain ⟨_, _, h3⟩ := hcon ⟨trivial, by decide⟩\n"
    "  have hv := h3 trivial\n"
    "  simp at hv\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify (frozen `loom_solve` kept verbatim). If a faithful correct
    # impl cannot verify, the spec is SPEC-TOO-STRONG. Both keep the value routed
    # through the grounded span `endT - startT`.
    # =====================================================================
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Guard the ABSENT case first with an early return, then fall through to
        # the recording. Opposite branch order from gold; same final state on
        # every input. Verified out-of-band (EXIT 0) under the frozen proof.
        "module": _impl(
            "    if !refit then\n"
            "      return ()\n"
            "    else\n"
            "      refitTime := some (endT - startT)\n"
            "      return ()"),
        "rationale": (
            "structurally-different CORRECT reshape: guard the no-request case "
            "with an early return, then record the grounded span `endT - startT` "
            "on the request branch. Branch order is the opposite of gold; the "
            "final state is identical on every input, so E1 (value), E2 (sign, a "
            "corollary of E1 + `startT ≤ endT`) and E3 (absent) all still "
            "discharge and the frozen `loom_solve` closes unchanged. Must verify, "
            "else SPEC-TOO-STRONG on the branch order. (Sibling: POS_EARLY_RETURN.)"),
    },
    {
        "id": "pos-compute-then-select",
        "kind": "soundness",
        "expect": "verify",
        # Bind the span unconditionally to a typed local, then select between it
        # and the absent marker on the request flag. Different data shape
        # (compute-then-select vs guard-then-assign), identical observable value.
        "module": _impl(
            "    let measured : Option Rat := some (endT - startT)\n"
            "    if refit then\n"
            "      refitTime := measured\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "rationale": (
            "local-variable reshape: compute the span `endT - startT` "
            "unconditionally into a typed `Option Rat` local, then select between "
            "it and the untouched absent slot on the request flag. Different data "
            "shape (compute-then-select), identical value on every input, so "
            "E1/E2/E3 still discharge under the frozen proof. Must verify, else "
            "SPEC-TOO-STRONG on the data shape. (Sibling: POS_COMPUTE_THEN_SELECT.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the preconditions (`refitTime = none`, `startT ≤ endT`) are
    # met by every F2P-shaped input, and a genuine self-call probe (the sibling's
    # shape) is INEXPRESSIBLE here: `recordRefitTime` calling itself makes the
    # method recursive, and the elaborator demands a termination argument it
    # cannot infer on this signature — measured, `fail to show termination for
    # recordRefitTime / the type Rat does not have a `.brecOn` recursor`. So the
    # two sibling self-calls MERGE into one re-aimed case whose in-region
    # `assert`s pin the METHOD'S OWN POST-STATE non-degenerate on BOTH branches,
    # at the symbolic inputs (not at closed literals — an assert over literals
    # alone would be a decidable arithmetic tautology that constrains no
    # execution of this method, and would still discharge if the body wrote
    # anything at all). Both asserts are live: flipping the present-branch claim
    # to `refitTime = none` leaves `⊢ some (endT - startT) = none` unsolved, and
    # flipping the absent-branch claim to `refitTime ≠ none` leaves
    # `⊢ refitTimeOld ≠ none` unsolved (both measured, EXIT 1). The recorded
    # value/orientation is left to the frozen `ensures` and the reject rivals.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-all-outcomes",
        "kind": "admissibility",
        "expect": "verify",
        # The gold body with a post-state `assert` on EACH branch. The request
        # branch asserts the slot is genuinely present AND carries a
        # non-negative value (E2's existential, re-derived in-body from the
        # precondition rather than assumed); the no-request branch asserts the
        # slot is still absent. Both are claims about `refitTime` AFTER the
        # body's own write, so they are non-degenerate: they fail if the body
        # writes the wrong marker on either branch.
        "module": _impl(
            "    if refit then\n"
            "      refitTime := some (endT - startT)\n"
            "      assert (with_name_prefix `admissPresent\n"
            "        (refitTime ≠ none ∧ (∃ t : Rat, refitTime = some t ∧ t ≥ 0)))\n"
            "      return ()\n"
            "    else\n"
            "      assert (with_name_prefix `admissAbsent (refitTime = none))\n"
            "      return ()"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate on BOTH branches, "
            "pinned on the METHOD'S OWN post-state at the symbolic inputs: on "
            "the request branch the slot is genuinely PRESENT and carries a "
            "non-negative value (`refitTime ≠ none ∧ ∃ t, refitTime = some t ∧ "
            "t ≥ 0` — E2's existential re-derived in-body from `startT ≤ endT`, "
            "which also covers the zero-length boundary `startT = endT`, where "
            "the span is exactly `0` and still admissible); on the no-request "
            "branch the slot is still ABSENT (`refitTime = none`). These are "
            "asserts about `refitTime` AFTER the body's write, not decidable "
            "arithmetic over closed literals, so they constrain THIS execution: "
            "flipping either one to its negation leaves an unsolved goal "
            "(measured). If it cannot verify ⇒ PRECOND-TOO-STRONG / degenerate "
            "post-image. (Siblings: ADMISS_TRUE and ADMISS_FALSE_AND_ZERO, "
            "merged and re-aimed; the literal self-call they use is "
            "inexpressible here — it makes the method recursive.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses move every input
    # binder: `refit` over {true, false}, `startT` over {2,3,1,3,1,3}, `endT`
    # over {5,7,4,8,6,3}; `refitTime` comes in `none` (pinned by the
    # precondition). SIX DISTINCT input points (pts=6), one of which sits on the
    # CLOSED end of the precondition domain (`startT = endT`).
    # =====================================================================
    {
        "id": "reject-never-present",
        "kind": "uniqueness",
        "expect": "reject",
        # Missing presence (the pre-change behaviour): perform the request branch
        # but never record the span. Violates E1 on the request branch (the slot
        # stays `none`).
        "module": _impl(
            "    if refit then\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "the faithful counterpart takes the request branch but never sets the "
            "recorded-duration slot — the exact pre-change behaviour. The failing "
            "test drives the public entry point with the request flag set and "
            "asserts the duration slot is PRESENT (a float ≥ 0); a slot that "
            "stays absent leaves that assertion failing, so it does NOT resolve "
            "(it is the exact bug the fix removes). A verifying rival here would "
            "be a true verify-not-resolve break."),
        "rationale": (
            "REJECT from E1 (`refit = true → refitTime = some (endT - startT)`): "
            "on the request branch the slot stays `none`, so the equality "
            "`none = some (…)` fails. E2/E3 hold (nothing recorded), so the ONLY "
            "failing clause is presence-with-value. Refuted at (refit=true, "
            "startT=2, endT=5). If it verified ⇒ SPEC-TOO-WEAK. "
            "(Sibling: WEAK_NEVER_PRESENT.)"),
        "witness": _witness(True, 2, 5, _TAIL_NEVER),
    },
    {
        "id": "reject-always-present",
        "kind": "uniqueness",
        "expect": "reject",
        # Extra presence: record the span unconditionally, even on the no-request
        # branch. Violates E3 (the mut frame clause) on that branch.
        "module": _impl(
            "    refitTime := some (endT - startT)\n"
            "    return ()"),
        "refinement": (
            "the faithful counterpart records the duration UNCONDITIONALLY "
            "(outside the request gate), so the slot is present even when the "
            "re-do did not run. This breaks the documented contract (the recorded "
            "duration is present only when the request flag is set) and the "
            "no-request invariant a pass-to-pass test relies on (a cleared flag "
            "must not produce the timing artifact). A verifying rival is a "
            "verify-not-resolve break on the frame clause."),
        "rationale": (
            "REJECT from E3 (`refit = false → refitTime = none`): on the "
            "no-request branch the body writes `some (…)`, so the slot disagrees "
            "with its pinned unchanged post-state `none`. This is the directive-5 "
            "`mut`-frame clause (the recorded-duration slot must stay absent when "
            "the flag is clear); E1/E2 are vacuous there. Refuted at (refit=false, "
            "startT=3, endT=7). If it verified ⇒ SPEC-TOO-WEAK (the frame would be "
            "hollow). (Sibling: WEAK_ALWAYS_PRESENT.)"),
        "witness": _witness(False, 3, 7, _TAIL_ALWAYS),
    },
    {
        "id": "reject-const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant zero: record `0` on the request branch instead of the span.
        # Equal to the grounded span only on a zero-length interval; on any
        # positive interval `0 ≠ endT - startT`. Violates E1.
        "module": _impl(
            "    if refit then\n"
            "      refitTime := some 0\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "the faithful counterpart records a fixed constant (zero) rather than "
            "the genuine elapsed span. A value-only failing test that merely "
            "checks the slot is a float ≥ 0 WOULD accept zero — which is exactly "
            "why the spec is deliberately stronger than that test: it pins the "
            "genuine measurement. A faithful patch that always reported zero "
            "seconds would report a semantically wrong duration (the actual "
            "re-do took non-zero time), diverging from the intended observable. "
            "This is the VALUE-FIDELITY supporting rival."),
        "rationale": (
            "REJECT from E1 (`refit = true → refitTime = some (endT - startT)`): "
            "the rival records `some 0`, which equals the grounded span only on a "
            "zero-length interval, not in general. Refuted at (refit=true, "
            "startT=1, endT=4) where the span is 3 ≠ 0. If it verified ⇒ "
            "SPEC-TOO-WEAK on the recorded value. (Sibling: WEAK_CONST_ZERO.)"),
        "witness": _witness(True, 1, 4, _TAIL_VALUE),
    },
    {
        "id": "reject-echo-end",
        "kind": "uniqueness",
        "expect": "reject",
        # Echo the later reading `endT` instead of the span. An input-derived but
        # WRONG function: `endT ≠ endT - startT` whenever `startT ≠ 0`. Violates
        # E1; guards against a "any function of the inputs is fine" reading.
        "module": _impl(
            "    if refit then\n"
            "      refitTime := some endT\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "the faithful counterpart records the post-work clock READING itself "
            "rather than the elapsed span. For a real epoch reading the value is "
            "enormous and unrelated to the re-do duration; it is still a "
            "non-negative float so a value-only test would pass, but the reported "
            "number is not seconds-of-work — semantically wrong. A "
            "verify-not-resolve break against the exact-value clause; the "
            "input-derived-but-WRONG supporting rival."),
        "rationale": (
            "REJECT from E1: the rival records `some endT`, and `endT ≠ endT - "
            "startT` in general (they coincide only when startT = 0). Refuted at "
            "(refit=true, startT=3, endT=8) where `endT = 8` but the span is 5. "
            "Guards against reading E1 as 'any function of the inputs is fine'. "
            "If it verified ⇒ SPEC-TOO-WEAK. (Sibling: WEAK_ECHO_END.)"),
        "witness": _witness(True, 3, 8, _TAIL_VALUE),
    },
    {
        "id": "reject-swapped-orientation",
        "kind": "uniqueness",
        "expect": "reject",
        # Swapped orientation: record `startT - endT` (earlier minus later), the
        # NEGATED span. Wrong value (E1) and, on a strict interval, wrong sign
        # (E2) — the one rival that exercises E2 as a corollary of the E1 break.
        "module": _impl(
            "    if refit then\n"
            "      refitTime := some (startT - endT)\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "the faithful counterpart records the NEGATED span (earlier reading "
            "minus later). With the readings ordered this is ≤ 0, so the failing "
            "test's non-negativity assertion on the recorded duration fails "
            "outright — it does NOT resolve. A clean verify-not-resolve break, "
            "and the shape that also violates the sign guarantee."),
        "rationale": (
            "REJECT from E1 (`refit = true → refitTime = some (endT - startT)`): "
            "the rival records `some (startT - endT)`, the negated span, which "
            "differs from `endT - startT` on every strict interval. This is also "
            "the rival that exercises E2 (`… ≥ 0`) as a corollary — the recorded "
            "value is NEGATIVE on a strict interval — so the sign clause is not "
            "left undefended even though E2 is subordinate to E1. Refuted at "
            "(refit=true, startT=1, endT=6): rival records -5, spec demands 5. "
            "If it verified ⇒ SPEC-TOO-WEAK. (Sibling: WEAK_SWAPPED.)"),
        "witness": _witness(True, 1, 6, _TAIL_VALUE),
    },
    {
        "id": "reject-absent-on-zero-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # Sub-domain attack on the CLOSED end of the precondition domain: record
        # the span only when the interval is STRICTLY positive, and leave the
        # slot absent on the zero-length boundary `startT = endT`. Agrees with
        # gold on every strict interval — the whole region the other four value
        # rivals are refuted in — and differs ONLY at `startT = endT`, which no
        # other witness in this battery reaches. Violates E1 (and E2) there.
        "module": _impl(
            "    if refit then\n"
            "      if startT < endT then\n"
            "        refitTime := some (endT - startT)\n"
            "        return ()\n"
            "      else\n"
            "        return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "the faithful counterpart records the duration only when the two "
            "readings differ, treating an interval that measures as zero as "
            "'nothing to report' and leaving the slot absent. On a coarse clock "
            "(or a fast unit of work) two readings bracketing the work can come "
            "back equal, and the consumer then finds NO recorded duration at all "
            "— the same absent-slot failure the never-recording shape produces, "
            "just on a narrower sub-domain. The failing test asserts the "
            "duration is PRESENT whenever the request flag is set, with no "
            "exception for a zero measurement, so it does NOT resolve. A "
            "verifying rival here would mean the spec's value clause is only "
            "enforced on the interior of its own domain."),
        "rationale": (
            "REJECT from E1 (`refit = true → refitTime = some (endT - startT)`): "
            "at the zero-length boundary `startT = endT` (in-domain — the "
            "precondition is `startT ≤ endT`, closed) the rival takes the "
            "request branch but leaves the slot `none`, so `none = some 0` "
            "fails; E2 fails there too (no value to be non-negative). Refuted at "
            "(refit=true, startT=3, endT=3) — the ONLY witness point in this "
            "battery on the closed end of the precondition domain, where the "
            "other four value rivals all agree with gold. Closes the sub-domain "
            "gap those rivals leave: they pin the value on strict intervals, "
            "this pins that the boundary is not silently exempt. If it verified "
            "⇒ SPEC-TOO-WEAK on the domain boundary. (No sibling — added by "
            "audit; the nagini battery has no boundary rival, only the "
            "ADMISS_FALSE_AND_ZERO positive at `(3.0, 3.0)`.)"),
        "witness": _witness(True, 3, 3, _TAIL_NEVER),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The sibling battery ships 9 SPEC cases (2 soundness
# positives, 2 admissibility, 5 uniqueness rivals) plus a 3-entry AXIOM lane. It
# contracts one function `recorded_refit_duration(do_final_fit, start, end)` over
# three pass-by-value primitives, with an Optional[float] result. This bundle
# models the SAME behaviour over the `Rat` carrier as the mutable slot
# `recordRefitTime(refit, startT, endT, mut refitTime)`; the value surface
# carries across one-for-one. Every sibling case is accounted for.
#
#   nagini case                    kind          -> here                              disposition
#   ------------------------------------------------------------------------------------------------
#   pos-early-return               soundness     -> pos-early-return                  PORTED
#   pos-compute-then-select        soundness     -> pos-compute-then-select          PORTED
#   admiss-true-branch             admissibility -> admiss-nondegenerate-all-outcomes RE-AIMED+MERGED
#   admiss-false-and-zero          admissibility -> admiss-nondegenerate-all-outcomes RE-AIMED+MERGED
#   weak-never-present             uniqueness    -> reject-never-present             PORTED
#   weak-always-present            uniqueness    -> reject-always-present            PORTED
#   weak-const-zero                uniqueness    -> reject-const-zero                PORTED
#   weak-echo-end                  uniqueness    -> reject-echo-end                  PORTED
#   weak-swapped-args              uniqueness    -> reject-swapped-orientation       PORTED
#   (no sibling)                   uniqueness    -> reject-absent-on-zero-boundary   ADDED (audit)
#   AXIOM_TESTS (x3)               axiom         -> (none)                           DROPPED (G-AX)
#
# 2 positives ported, 2 admissibility merged+re-aimed to 1, 5 uniqueness ported,
# 1 uniqueness ADDED by audit, 3 axiom tests dropped = 9 velvet cases (3 verify,
# 6 reject).
#
# ADDED BY AUDIT (reject-absent-on-zero-boundary): the five ported value rivals
#   are all refuted on STRICT intervals, so none of them exercises the closed end
#   of the precondition domain (`startT ≤ endT` admits `startT = endT`). A rival
#   that records the span only when `startT < endT` and leaves the slot absent at
#   the boundary therefore agreed with gold at every point the battery tested.
#   Its witness at (true,3,3) was built and SEEN to discriminate: EXIT 0 against
#   the rival, EXIT 1 against the frozen solution with a semantic residual
#   (`hcon` instantiated, `⊢ False` unsolved), not a missing identifier or a
#   stuck reduction.
#
# PORTED (2 positives): pos-early-return (guard the absent case first with an
#   early return) and pos-compute-then-select (bind the span to a typed local,
#   then select) port one-for-one. Both keep the byte-identical obligation and the
#   frozen `loom_solve`, and both were verified to build (EXIT 0).
# RE-AIMED + MERGED (admissibility): the sibling's two self-call admissibility
#   cases assert an F2P-shaped input satisfies the fractional-permission Requires.
#   This backend's preconditions (`refitTime = none`, `startT ≤ endT`) are met by
#   every F2P input and there is no permission surface, so that probe is
#   degenerate; the sharper residual risk is a DEGENERATE post-image. The two are
#   merged into one live in-region assert pinning all three outcomes at F2P-shaped
#   inputs — a present non-negative span, the zero-length boundary `(3,3)` span
#   equal to 0 (the sibling's ADMISS_FALSE_AND_ZERO boundary), and the absent
#   marker — so the post-image is proven non-degenerate. Verified EXIT 0; a false
#   conjunct leaves an unsolved goal.
# PORTED (5 rivals): weak-never-present -> reject-never-present (the pre-change
#   shape; E1 presence, refuted at (true,2,5)). weak-always-present ->
#   reject-always-present (unconditional record; E3 mut-frame, refuted at
#   (false,3,7)). weak-const-zero -> reject-const-zero (E1 value, refuted at
#   (true,1,4)). weak-echo-end -> reject-echo-end (E1 value, input-derived-wrong,
#   refuted at (true,3,8)). weak-swapped-args -> reject-swapped-orientation (E1
#   value + E2 sign corollary, refuted at (true,1,6)).
# DROPPED (AXIOM_TESTS, 3 entries): the sibling's clock_after + elapsed_between
#   soundness/containment probes belong to the G-AX lane. Here the clock
#   monotonicity is captured by the precondition `startT ≤ endT` (mapping.md §3)
#   and the elapsed span is modeled directly as the exact `Rat` subtraction
#   `endT - startT` (no axiom declared — the `axioms` region is empty), so there
#   is nothing to probe. This gate ignores AXIOM_TESTS regardless.
#
# FRAME / PERMISSION-MUTATION: VACUOUS as a permission attack (the sibling itself
#   records the class N/A — all inputs pass-by-value, no `Acc(x,1/2)` reference).
#   Velvet is referentially transparent: `refit`/`startT`/`endT` are immutable
#   values, no heap, no aliasing, no permission system. But the frame ARGUMENT is
#   not lost — `refitTime` IS a `mut` slot and E3 pins it unchanged (`none`) on
#   the no-request branch (directive-5), so a body writing it there violates a
#   genuine postcondition clause, attacked by reject-always-present. Not
#   fabricated; re-expressed as a value attack on the mut-frame clause.
#
# DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
#
# FROZEN-SPEC FINDING (escalated, NOT patched here — closing it would require
#   editing Solution.lean, which must re-clear the equivalence/differential/
#   conformance/panel gates outside this lane).
#
#   A wrong impl that shares this spec byte-for-byte VERIFIES under the frozen
#   `loom_solve`. It is in variant scope (`variant_problems == []`), introduces
#   no axiom/sorry, and keeps the obligation statement intact:
#
#       let mut k : Nat := 1
#       while k > 0
#         invariant k ≥ 1
#         done_with k = 0
#         decreasing k
#       do
#         k := k
#       refitTime := some 999
#       return ()
#
#   Measured EXIT 0. It records a CONSTANT on both branches — violating E1, E2's
#   grounding and E3 simultaneously — and its loop never terminates. Two
#   independent defects compose to let it through:
#
#     (1) `done_with` is assumed, not proven. The `while` macro emits it as
#         `onDoneGadget`, which the WP generator treats as a HYPOTHESIS about the
#         exit state. Pairing `invariant k ≥ 1` with `done_with k = 0` therefore
#         hands the continuation a contradictory context, and every postcondition
#         clause after the loop discharges vacuously. Confirmed directly: an
#         `assert (with_name_prefix `x (False))` placed after that loop VERIFIES
#         (EXIT 0). A terminating loop with the same contradictory pair is
#         REJECTED (EXIT 1), so the divergence is load-bearing, not incidental.
#     (2) The `decreasing` VC does not reach the user. With `invariant True` and
#         `done_with True` (no contradiction available) and a body `k := k + 1`
#         whose measure strictly INCREASES, the gold body still verifies (EXIT 0);
#         `loom_solve` leaves no goal at all (a deliberate junk tactic after it
#         reports `No goals to be solved`). So `"total"` rejects only a loop with
#         NO `decreasing` annotation — the syntactic check in the macro — not one
#         whose annotation is false.
#
#   Why no reject case: the witness for such a rival must ELABORATE against it,
#   and the spec ACCEPTS it, so no refutation exists (measured: the value witness
#   at (true,1,4) fails against this rival with `Function expected at h1 … this
#   term has type Prop`, i.e. the triple never reduced to the clause conjunction).
#   Attack F′'s "shippable under total" disposition therefore does not apply to
#   THIS bundle, and the honest record is a spec finding, not a manifest entry.
#
#   Scope note, RETRACTED AND RE-MEASURED. This paragraph used to say that (2) is
#   a property of the shared Velvet/Loom `while` elaboration, so that the velvet
#   bundles an internal findings doc recorded as "total/rejected" are rejected only
#   for the MISSING-annotation shape that doc's probe splices (a bare
#   `while True do pure ()`), and that re-probing them with an ANNOTATED diverging
#   loop was an unattempted measurement. It has now been attempted, on THIS cell,
#   and it refutes the conjecture: an annotated diverging loop
#   (`while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q`, body
#   `q := q`, proof reduced to a bare `loom_solve`) is REJECTED on the measure's
#   OWN descent goal, `case «decreasing_1: q»` with residual `q < q` unsolved. So
#   the annotation is not taken on faith and the rejection is not merely the
#   missing-annotation linter. The mechanism is in the Loom source:
#   `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop` takes
#   `measure : β -> Nat` and emits the `measure b' < measure b` conjunct, while the
#   `PartialCorrectness` twin is the one that takes a measure and DISCARDS it, and
#   the `set_option` elaborator itself opens the total scope
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`). The cohort the note cited does
#   not exist either: all 500 velvet bundles set "total".
#
# CLAUSE / BINDER COVERAGE. The obligation `prove_correct recordRefitTime` is
#   DEFENDED (two soundness positives + the admissibility case) and ATTACKED (five
#   reject rivals). The independent top-level ensures clauses:
#     E1 (refit=true → refitTime = some (endT - startT), the VALUE pin) — attacked
#        by reject-never-present (presence), reject-const-zero (constant),
#        reject-echo-end (wrong function), reject-swapped-orientation (negated),
#        and reject-absent-on-zero-boundary (presence, but ONLY on the closed end
#        of the precondition domain `startT = endT` — the sub-domain the other
#        four all agree with gold on).
#     E3 (refit=false → refitTime = none, the mut-FRAME clause) — attacked by
#        reject-always-present.
#     E2 (refit=true → ∃ t, refitTime = some t ∧ t ≥ 0, SIGN) is NOT independent:
#        given E1 and `startT ≤ endT` it follows, so any impl meeting E1 meets E2
#        and any impl violating E2 on the request branch already violates E1. No
#        rival attacks E2 in isolation; reject-swapped-orientation records a
#        NEGATIVE span, simultaneously an E1 and an E2 violation, so E2 is
#        exercised as a corollary rather than left undefended. A hypothetical
#        E2-only rival (record a positive constant on the request branch) would
#        satisfy E2 while violating E1 — i.e. it collapses into reject-const-zero
#        / reject-echo-end and adds no independent coverage.
#   The input binders of the spec predicate are all varied across the reject
#   witnesses:
#     refit    at {true, false, true, true, true, true}   (both branch values)
#     startT   at {2, 3, 1, 3, 1, 3}
#     endT     at {5, 7, 4, 8, 6, 3}
#     refitTime at none (pinned by the precondition `refitTime = none`, so it is
#               not a free binder to vary — every admissible input has it none).
#   The six witnesses sit at SIX distinct input points (pts=6): (true,2,5),
#   (false,3,7), (true,1,4), (true,3,8), (true,1,6), (true,3,3). `refit` is moved
#   off true (to false in reject-always-present, the only rival that reaches the
#   no-request branch), and startT/endT vary across all six so the manifest
#   demonstrates the post-image's dependence on the reading pair (the value clause
#   diverges from gold at a different span at each point). The sixth point
#   (true,3,3) is the DEGENERATE reading pair `startT = endT`: the precondition
#   `startT ≤ endT` is closed, so the boundary is in-domain, and it is the one
#   input where the span is `0` and the four constant/wrong-function rivals stop
#   discriminating (const-zero, notably, is CORRECT there). No binder is pinned
#   across the reject set, and the domain is probed at both its interior and its
#   closed edge.
#
#   `refitTime` remains pinned to `none` across every reject witness. That is
#   forced, not a gap: `require refitTime = none` means any other entry value is
#   OUT of the admissible domain, so a witness binding it elsewhere would refute
#   the rival from an unsatisfiable precondition (the gate's own consistency
#   probe exists to catch exactly that). The coverage reporter flags it as a
#   pinned binder; it is unpinnable by construction. Verified: a rival mishandling
#   `refitTime` on the no-request branch IS caught — that is
#   reject-always-present, refuted via E3 at (false,3,7).
#
#   Re-measured independently (audit `a8`): a witness entered at
#   `refitTime = some 9` cannot be stated at all. Its precondition conjunct
#   becomes `some 9 = none`, and the build fails with `Application type mismatch:
#   The argument trivial has type True but is expected to have type some 9 = none
#   in the application And.intro trivial` — the unsatisfiable-precondition
#   failure the coverage finding would otherwise invite. Confirms the finding is
#   advisory-only here and not a gap to close.
#
# CARRIER NOTE. The tester+decide route is DEAD (the mixed existential/`Rat`
#   post-image leaves `recordRefitTimeTester … = false` unreduced on both files —
#   measured), so every witness refutes the method's Hoare triple DIRECTLY at
#   concrete literals via `simp only [reduceIte, triple_pure, le_Prop_eq]`, then
#   closes the residual `Rat` (dis)equality by `simp only [Rat.sub_def,
#   Rat.normalize]; decide` (the measured normaliser pair — `decide` alone is
#   stuck on `Rat` arithmetic). Each witness binds NOTHING in its head (concrete
#   literals only), so the consistency probe is a no-op. Each was SEEN to
#   discriminate with two real builds: ELABORATES against the rival (EXIT 0),
#   FAILS against the frozen solution (nonzero).
#
#   Correction (audit `a8`): the `simp only [Rat.sub_def, Rat.normalize]; decide`
#   pair is what closes the residual on the RIVAL side. On the GOLD side those
#   tactics are never reached — the earlier `simp only [Option.some.injEq]`
#   already discharges the equation (`hv : True`), and the `simp` at that line is
#   what reports `made no progress`. The `Option.some.injEq` argument is flagged
#   UNUSED on gold for the same reason. See the docstring's GOLD-SIDE FAILURE
#   MODE block for the reveal/flip evidence that this is a refutation and not a
#   tactic mismatch.
#
# ATTACKS RUN BY AUDIT `a8` (all builds re-run independently; none landed a new
#   case, and none found a hole in E1/E2/E3):
#   D (wrong impls, all REJECTED, EXIT 1): half-span `some ((endT-startT)/2)`;
#     `some startT` (echo the EARLIER reading); `some 0` on the no-request branch
#     only (a second, distinct E3 shape); `some (if endT - startT < 0 then
#     startT - endT else endT - startT)` (an abs-clamp — rejected on E2's
#     existential, so its residual is a real goal and not a tactic artifact).
#     A demonic sign-only rival (`let v : Rat :| v ≥ 0`) is INEXPRESSIBLE in the
#     do-block fragment: `unexpected token ':|'; expected ':=' or '|'` — a
#     TOOLING limit, reported rather than claimed as coverage.
#   E (correct reshapes, all VERIFY): `some (-(startT - endT))` and
#     `some (endT + (-startT))` need an honest proof tail (`simp [Rat.neg_sub]` /
#     `rw [← Rat.sub_eq_add_neg]` plus `rw [Rat.le_iff_sub_nonneg] at require_1`),
#     which a rival is allowed to supply; the single-assignment if-EXPRESSION form
#     `refitTime := if refit then some (endT - startT) else none` likewise
#     (EXIT 0). Write-then-retract (assign the span unconditionally, then clear to
#     `none` on the no-request branch) verifies under the FROZEN proof with no
#     help at all (EXIT 0) — strong evidence against SPEC-TOO-STRONG on control
#     shape. No faithful correct impl was found that the spec rejects.
#   Admissibility degeneracy re-check: replacing the request-branch write with
#     `refitTime := some 0` while KEEPING both asserts is REJECTED (EXIT 1) with
#     `⊢ refit = true → some 0 = some (endT - startT)` — so the case's asserts sit
#     on a body whose own writes are still pinned by the frozen ensures, and the
#     asserts themselves are live (flipping either leaves an unsolved goal:
#     `⊢ some (endT - startT) = none` / `⊢ refitTimeOld ≠ none`).
AXIOM_TESTS = []
