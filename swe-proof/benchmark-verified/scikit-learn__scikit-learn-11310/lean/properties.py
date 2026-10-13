"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-11310 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS entry is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the admissibility case, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_refitTiming``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini sibling is
the design document: its DEFENDED-SURFACE prose and each case's
``rationale`` / ``refinement`` carry the adversarial argument, and every case
below re-expresses one of those arguments against this bundle's model. The
per-case correspondence — including the nagini cases that have NO counterpart
here, and why — is in ``assessment`` of the submitted payload and summarised in
the CARRIER NARROWING section below.

DEFENDED SURFACE (one modeled behavior, one obligation). The modeled function
maps a configuration flag and two wall-clock readings to an optional duration:

    problem_spec_refitTiming refitEnabled startClock endClock result :=
      result = (if refitEnabled then some (endClock - startClock) else none)

Read as two independent top-level obligations riding on one equation:

  * PRESENCE — the duration observable exists exactly when the final refit is
    performed, and is absent otherwise. (``some`` vs ``none``; the ``if``
    selects on ``refitEnabled``.)
  * VALUE — when present, the reported duration is pinned to the elapsed
    interval between the two readings: the later reading minus the earlier one,
    in that orientation, and nothing else.

The spec carries NO precondition: the ``correct_refitTiming`` binder is an
unguarded ``∀`` over both readings, so the VALUE clause is pinned pointwise on
EVERY pair — including a reversed pair. That is load-bearing here and drives one
rival the nagini sibling has no analogue for; see ``weak-clamp-negative``.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini sibling had already recorded
    this class as N/A for itself (all three of its inputs are pass-by-value
    primitives with no fractional-permission clause anywhere in its contract), so
    there was nothing to port and nothing is fabricated in its place.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. The
    distinction matters: a vacuous class says the battery is complete, a hole says
    the battery cannot reach something. An earlier revision recorded this class as
    VACUOUS on the ground that "``implementation_refitTiming`` is a total Lean
    ``def``, so a non-terminating rival cannot be written at all". The audit lane
    measured that and it is FALSE; the correction, and the reason nothing is
    shipped anyway, are both mechanical:

      - a diverging rival IS writable here, two ways, and both are IN SCOPE
        (measured: ``variant_problems`` clean for each — no ``axiom``, no
        ``sorry``, obligation statement byte-identical). Marking the signature
        ``partial def`` and self-recursing licenses non-termination outright; a
        plain ``def`` may also carry an unbounded ``for _ in Lean.Loop.mk do``
        loop, needing no ``partial`` marker and no ``termination_by``.
      - both are genuinely REJECTED, not vacuously accepted. This bundle sets no
        ``loom.semantics.termination`` option — the frozen solution carries no
        ``set_option`` line at all — so this is plain Lean, and the frozen script
        fails on each: the ``partial`` rival at ``Tactic `unfold` failed to unfold
        `implementation_refitTiming``` (``partial`` yields an opaque constant with
        no equation lemma), the loop rival at ``Tactic `rfl` failed`` on an
        un-normalised ``forIn Lean.Loop.mk`` term.
      - what BLOCKS the case is the witness half, and it was measured rather than
        assumed. A ``partial`` constant does not reduce, so no computing witness
        works: the unconditional witness leaves ``⊢ ¬implementation_refitTiming
        true 1 4 = some (4 - 1)`` under ``decide`` / ``simp`` / ``norm_num`` /
        ``decide +kernel`` alike (exit 1 on the RIVAL — it fails the half that
        must succeed). Conditioning on a hypothesis, the technique that makes an
        opaque carrier attackable, does not rescue it either, and this is the part
        worth recording: BOTH shapes tried — ``h : impl true 1 4 ≠ some (4 - 1)``
        (logically the goal itself) and ``h : impl true 1 4 = some 99`` (a
        concrete wrong value) — elaborate against the FROZEN SOLUTION too, exit 0.
        Against gold the value reduces, so the hypothesis is simply false there
        and a false hypothesis proves the goal; the witness is a tautology in the
        gate's sense and would be recorded ``witness-vacuous``. The consistency
        probe does not catch it (``simp_all made no progress``), which is exactly
        why it must be caught by hand.

    So this class is left UNSHIPPED with its blocker named, rather than papered
    over with a witness that discriminates nothing. Landing it needs a witness
    whose failure tracks the claim against a NON-REDUCING impl — the shape the
    other twelve rivals get for free by reducing. The nagini sibling has no
    ``diverge-*`` / ``nonterm-*`` counterpart, so nothing was dropped in porting;
    this is an addition the audit lane attempted and could not complete honestly.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is fully GROUNDED: the
    result is pinned to an arithmetic term built only from the two reading
    inputs. There is no ``opaque`` callee, no ``axiom``, and no answer key an
    implementation could echo instead of computing. (The nagini sibling reached
    the same conclusion about its ``elapsed_between`` model and said so.) In its
    place the battery carries honest positive controls plus VALUE rivals that are
    functions of the inputs but the WRONG functions.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole reject lane lives.

CARRIER NARROWING. Case-count parity with nagini is not the target and is not
met: nagini ships 9 cases (2 soundness, 2 admissibility, 5 uniqueness) plus 3
AXIOM_TESTS; this port ships 14 SPEC cases and no axiom lane. The differences are
principled, not cosmetic:

  * nagini's two admissibility cases both establish its ``Requires(end >= start)``
    for a normal input by a self-call. This spec has NO precondition, so there is
    no ``Requires`` to admit and no binder to attack. The honest analogue — one
    case — discharges the obligation by evaluation at three ground inputs
    (including nagini's two: the F2P-shaped ordered pair and its zero-length
    boundary), which is why the two collapse into one.
  * nagini's ``weak-swapped-args`` rejects for a reason that does not exist here:
    on nagini it violates the ORACLE's own ``Requires(later >= earlier)`` at the
    call site. There is no oracle and no precondition on this carrier, so the
    same rival must be — and is — refuted purely on the VALUE clause instead.
  * nagini's 3 AXIOM_TESTS are dropped: the axiom lane is G-AX's job and this
    gate ignores it. This bundle consumes no ``axiom`` and declares no ``opaque``
    callee at all, so there is nothing for that lane to probe (its
    ``axiom_check.py`` is a skip stub).
  * five rivals are ADDED because this carrier exposes attack surface nagini's
    does not. Two came with the port: ``weak-clamp-negative`` (see below) and
    ``weak-echo-start``. Three more were added by adversarial audits of this
    battery, each closing a sub-domain that every other witness — nagini's and the
    port's alike — leaves unvisited: ``weak-floor-duration`` (the only NON-INTEGER
    interval), ``weak-negative-reading`` (the only reading below zero) and
    ``weak-zero-length-absent`` (the only point where the two readings are EQUAL
    with the refit performed — the boundary where the PRESENCE and VALUE clauses
    meet, and the one corner the admissibility case's equal-readings point does
    not cover, since it takes the refit-DISABLED arm where the answer is ``none``
    either way). All three were landed the way the audit lane requires: the rival
    built and seen to fail, its witness built against the rival (exit 0) and
    against the frozen solution (exit 1, ``unsolved goals ⊢ False`` — a semantic
    refutation, not a missing identifier or a stalled tactic), and the FORGERY
    pair built too — flipping the claim inverts both exit codes, so gold's
    failure tracks what is claimed rather than being a fixed tactic artifact.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases refitEnabled <;> rfl`` is tuned
to the frozen impl's syntactic form — so a rejection ALONE attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating
the spec predicate directly at one concrete input and refuting it. Each was built
against its rival (elaborates) and against the frozen solution (fails), so it
discriminates rather than asserting a tautology.

Every witness states its refutation at LITERAL inputs, so no witness binds a
hypothesis and the inconsistent-binder forgery has no foothold here: there are no
assumptions to be jointly unsatisfiable. Conditioning on the carrier is not
needed because the carrier is fully transparent (``Bool`` and ``ℚ``, no opaque
term anywhere in the spec).

A tactic note for whoever revisits these. ``decide`` is the wrong tool for the
VALUE clause on this carrier and its failure must not be read as "this input is
not decidable": it reduces the ``Decidable`` instance rather than computing, and
gets stuck at ``match ↑0, (Rat.sub 8 3).num with ...`` on a goal as simple as
``¬(0 : ℚ) = 8 - 3``. ``norm_num`` closes every such goal. Conversely the
PRESENCE clause needs no arithmetic — the divergence is ``none`` vs ``some _``,
a constructor clash — and there ``simp`` closes while ``norm_num`` stalls. So
value rivals use ``norm_num`` and presence rivals use ``simp``, deliberately.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point.

  * ``refitEnabled`` takes BOTH settings: ``false`` in ``weak-always-present``
    (the only rival whose violation lives on the refit-disabled sub-domain) and
    ``true`` in the nine value/presence rivals.
  * ``startClock`` takes -3, 0, 1, 2, 3, 4, 5 and ``endClock`` takes 2, 3, 4,
    5/2, 5, 6, 7, 8, 9 across the ten rivals — ten DISTINCT input points, no two
    rivals sharing a refutation point.
  * the ORDER of the two readings is varied, not just their values, and so is
    their EQUALITY: eight rivals sit on a strictly ordered pair
    (``startClock < endClock``, the physically realisable regime),
    ``weak-clamp-negative`` sits on a REVERSED pair (the only sub-domain where
    that rival is wrong at all), and ``weak-zero-length-absent`` sits on an EQUAL
    pair — so all three orderings of the two readings are represented rather than
    just the realisable one.
  * the result's dependence on EACH reading is demonstrated separately rather
    than assumed: ``weak-echo-end`` ignores ``startClock`` and
    ``weak-echo-start`` ignores ``endClock``, and both are refuted. A battery
    with only one of them would leave the other reading a binder no rival was
    built to abuse.
  * the two readings are NOT all drawn from the small positive integers. Two
    rivals added by the audit lane sit on sub-domains every other witness misses:
    ``weak-floor-duration`` is refuted at a NON-INTEGER interval (0 → 5/2, the
    only fractional point in the battery) and ``weak-negative-reading`` at a
    NEGATIVE reading (-3 → 4, the only point where a reading is below zero). ℚ is
    the carrier precisely because the modeled readings are not integers, so a
    battery whose every point was a small positive integer would leave the rest
    of the carrier — the part that motivated choosing it — unprobed.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-11310"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file, so a variant can only differ there and `same_spec` holds by
# construction. If the frozen solution is ever re-authored, `_swap` raises at
# import and the manifest breaks loudly instead of silently testing nothing.
# ---------------------------------------------------------------------------

# The whole body of the impl region (everything below the signature line).
_I_BODY = (
    "  let mut refitDuration : Option ℚ := none\n"
    "  if refitEnabled then\n"
    "    let s := startClock\n"
    "    -- (the best model is refit on the whole dataset between the two readings)\n"
    "    let e := endClock\n"
    "    refitDuration := some (e - s)\n"
    "  return refitDuration"
)

# The frozen tactic body of the proof region (the obligation STATEMENT above it
# is never touched by any case).
_P_BODY = (
    "  intro refitEnabled startClock endClock\n"
    "  unfold problem_spec_refitTiming implementation_refitTiming\n"
    "  cases refitEnabled <;> rfl"
)


def _impl(new_body):
    """A variant differing from frozen ONLY inside the impl region."""
    return _swap(_BASE, _I_BODY, new_body)


# Every reject witness refutes the spec predicate at one literal input. The
# `unfold` is the same two definitions in every case; only the point and the
# closing tactic differ (see the tactic note in the module docstring).
def _witness(flag, start, end, tactic, note):
    args = f"{flag} {start} {end}"
    return (f"{note}"
            f"example : ¬ problem_spec_refitTiming {args}\n"
            f"    (implementation_refitTiming {args}) := by\n"
            f"  unfold problem_spec_refitTiming implementation_refitTiming\n"
            f"  {tactic}\n")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS (positive controls) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG.
    #
    # Ports nagini's two soundness positives (pos-early-return,
    # pos-compute-then-select) and adds a third shape this carrier makes
    # available. Each keeps the theorem statement byte-identical AND retains the
    # frozen tactic body verbatim — no reproof, no helper lemma, no assumption
    # token — so nothing about the obligation is weakened to make them pass.
    # =====================================================================
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Guard the ABSENT case first with an early return, then fall through to
        # the recording. Opposite branch order from the frozen impl.
        "module": _impl(
            "  if !refitEnabled then\n"
            "    return none\n"
            "  let s := startClock\n"
            "  -- (the best model is refit on the whole dataset between the two readings)\n"
            "  let e := endClock\n"
            "  return some (e - s)"
        ),
        "rationale": (
            "PRESENCE and VALUE are both re-derived by an implementation whose "
            "branch order is the OPPOSITE of the frozen one: the absent case is "
            "guarded by an early return and the recording falls through. The "
            "reported value is identical on every input, so "
            "`result = if refitEnabled then some (endClock - startClock) else "
            "none` still holds and the frozen tactic body still closes it "
            "(retained verbatim). Must verify, else the obligation is "
            "SPEC-TOO-STRONG on the branch-order axis. Ports nagini's "
            "pos-early-return."
        ),
    },
    {
        "id": "pos-compute-then-select",
        "kind": "soundness",
        "expect": "verify",
        # Bind the elapsed interval unconditionally to a local, then select
        # between it and the absent marker: compute-then-select rather than
        # guard-then-assign. A different data shape, identical observable.
        "module": _impl(
            "  let elapsed := endClock - startClock\n"
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    refitDuration := some elapsed\n"
            "  return refitDuration"
        ),
        "rationale": (
            "A DATA-SHAPE reshape rather than a control-flow one: the elapsed "
            "interval is bound unconditionally to a local and the flag then "
            "selects between that local and the absent marker. Computing the "
            "interval unconditionally is sound precisely because the spec puts "
            "no side condition on the two readings — the subtraction is total — "
            "so the VALUE clause is unaffected and PRESENCE is still decided by "
            "the flag alone. Must verify. Ports nagini's "
            "pos-compute-then-select, whose argument was the same reshape "
            "discharged against its precondition."
        ),
    },
    {
        "id": "pos-gate-then-map",
        "kind": "soundness",
        "expect": "verify",
        # A third shape: let the flag build the optional carrier first, then map
        # the subtraction across it. The subtraction is applied INSIDE the
        # optional rather than before it, so presence and value are produced by
        # two separate steps.
        "module": _impl(
            "  let mut gate : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    gate := some startClock\n"
            "  return gate.map (fun s => endClock - s)"
        ),
        "rationale": (
            "The strongest available structural separation on this carrier: the "
            "flag decides PRESENCE alone (building the optional carrier), and "
            "the VALUE is applied afterwards by mapping the subtraction across "
            "it, so the two clauses are produced by two independent steps "
            "instead of one assignment. Still equal to the spec term on every "
            "input, so it must verify. Added for this carrier (nagini has no "
            "optional-mapping analogue); it defends the obligation against a "
            "reading that would demand presence and value be pinned by the same "
            "syntactic step."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at concrete, normal inputs
    # rather than only in the abstract. The frozen theorem carries NO
    # precondition hypothesis, so nagini's two self-call probes (which existed to
    # establish its `Requires(end >= start)`) have no binder to attack here; the
    # honest analogue is to discharge the spec predicate by evaluation at ground
    # inputs. Nothing is assumed: no new declaration, the theorem statement stays
    # byte-identical, the ground instances are `have`s inside the existing tactic
    # body, and the frozen body then closes the obligation verbatim.
    # =====================================================================
    {
        "id": "admiss-ground-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_BODY,
            "  have _performed : problem_spec_refitTiming true 1 2\n"
            "      (implementation_refitTiming true 1 2) := rfl\n"
            "  have _absent : problem_spec_refitTiming false 3 3\n"
            "      (implementation_refitTiming false 3 3) := rfl\n"
            "  have _reversed : problem_spec_refitTiming true 5 2\n"
            "      (implementation_refitTiming true 5 2) := rfl\n"
            + _P_BODY,
        ),
        "rationale": (
            "The obligation is discharged by evaluation at three ground inputs "
            "before the frozen body closes it in general: (a) the F2P-shaped "
            "point — refit performed, two ordered readings — where the duration "
            "must be PRESENT; (b) the refit-disabled point at the zero-length "
            "boundary (equal readings), where it must be ABSENT; (c) a REVERSED "
            "pair, which this spec admits because it has no ordering "
            "precondition. If any of the three could not be discharged the "
            "modeled behavior would be unsatisfiable at exactly the inputs it is "
            "meant to describe — the analogue of PRECOND-TOO-STRONG. Folds "
            "nagini's admiss-true-branch and admiss-false-and-zero (its (1.0,2.0) "
            "and (3.0,3.0) points are (a) and (b) here) into one case, since "
            "there is no `Requires` for a self-call to establish, and adds (c), "
            "which nagini's precondition excluded from its domain entirely."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument about whether its faithful real patch would resolve the F2P, so a
    # verifying rival can be read correctly, and (b) a refutation witness pinning
    # the violation at one concrete input, seen to hold of the rival and to fail
    # on the frozen solution.
    # =====================================================================

    # ---- PRESENCE class: never produce the observable (ports nagini
    # ---- weak-never-present; this is the pre-patch behavior) ----
    {
        "id": "weak-never-present",
        "kind": "uniqueness",
        "expect": "reject",
        # The refit is performed but its duration is never recorded.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let _s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let _e := endClock\n"
            "    refitDuration := none\n"
            "  return refitDuration"
        ),
        "refinement": (
            "This is the PRE-FIX behavior: the final refit runs and no duration "
            "observable is produced for it. The F2P test's first assertion is "
            "that the observable EXISTS after fitting with refit enabled, so a "
            "faithful real patch of this shape fails that assertion outright and "
            "does NOT resolve. A verifying rival here would therefore be a true "
            "verify-does-not-imply-resolve break, not an artifact — and it is "
            "exactly the state the prepatch sibling encodes, so G-DIFF sees the "
            "same divergence."
        ),
        "rationale": (
            "REJECT from the PRESENCE clause: with the flag set the spec pins "
            "the result to `some (endClock - startClock)` and the rival leaves it "
            "`none`, so the equation fails. Refuted at (true, 1, 4). `simp` "
            "closes it because the divergence is a constructor clash "
            "(`none = some 3`) and needs no arithmetic."
        ),
        "witness": _witness(
            "true", "1", "4", "simp",
            "-- The refit is performed, so the spec demands a PRESENT duration\n"
            "-- (some 3) while the rival reports none: a constructor clash, so no\n"
            "-- arithmetic is needed and `simp` closes it. Fails on the frozen\n"
            "-- solution, which reports some 3 here.\n",
        ),
    },

    # ---- PRESENCE class: produce it unconditionally (ports nagini
    # ---- weak-always-present) ----
    {
        "id": "weak-always-present",
        "kind": "uniqueness",
        "expect": "reject",
        # Report a duration even when no final refit was performed: the recording
        # escapes the flag guard entirely.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  let s := startClock\n"
            "  -- (the best model is refit on the whole dataset between the two readings)\n"
            "  let e := endClock\n"
            "  refitDuration := some (e - s)\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch of this shape performs the recording OUTSIDE "
            "the guard, so the duration observable is produced even when no final "
            "model was fit and there is no refit whose duration it could be. "
            "Being honest about the F2P: the test exercises the enabled "
            "configuration only, and the observable it looks for is still present "
            "and still a non-negative float, so this patch WOULD resolve the "
            "current F2P — and no PASS_TO_PASS test asserts the observable's "
            "absence either (the refit-disabled test in that suite checks other "
            "artifacts). So this is a SUPPORTING case rather than a clean "
            "verify-not-resolve break: it demonstrates that the spec deliberately "
            "pins the documented presence contract — the observable exists only "
            "when the final refit is performed — more tightly than the shipped "
            "tests do, which is the whole point of the PRESENCE clause. The "
            "nagini sibling asserted this rival would break a specific "
            "refit-disabled PASS_TO_PASS test; that claim does not hold up on "
            "inspection of the test body, and it is corrected here rather than "
            "carried over."
        ),
        "rationale": (
            "REJECT from the PRESENCE clause on the OTHER arm: with the flag "
            "clear the spec pins the result to `none` and the rival reports "
            "`some (endClock - startClock)`, so the equation fails. The only "
            "rival whose refutation lives on the refit-disabled sub-domain, and "
            "so the only one that moves the `refitEnabled` binder to `false` — "
            "without it, a rival mishandling only that setting would go "
            "unnoticed. Refuted at (false, 2, 5) by `simp` (constructor clash)."
        ),
        "witness": _witness(
            "false", "2", "5", "simp",
            "-- No refit is performed, so the spec demands the ABSENT marker while\n"
            "-- the rival reports some 3. Constructor clash; `simp` closes it, and\n"
            "-- it fails on the frozen solution, which reports none here.\n",
        ),
    },

    # ---- VALUE class: a constant instead of the measurement (ports nagini
    # ---- weak-const-zero) ----
    {
        "id": "weak-const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Report a constant instead of the genuine elapsed interval.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let _s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let _e := endClock\n"
            "    refitDuration := some 0\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch reporting a constant stand-in produces an "
            "observable that is present, is of the right type, and is "
            "non-negative — which is everything the F2P asserts about it — so it "
            "WOULD resolve the current F2P. This is therefore a VALUE-FIDELITY "
            "supporting case: it proves the spec is deliberately stronger than "
            "the F2P, pinning the genuine measurement rather than merely a "
            "well-typed non-negative number. Ported from nagini, which shipped "
            "it with the same honest disposition."
        ),
        "rationale": (
            "REJECT from the VALUE clause: the spec pins the reported duration to "
            "`endClock - startClock`, which equals the constant only on a "
            "zero-length interval; at (true, 3, 8) the interval is 5 and the "
            "equation fails. Closed by `norm_num` — `decide` gets stuck reducing "
            "the rational `Decidable` instance, which is a tactic limitation and "
            "not a statement about the input."
        ),
        "witness": _witness(
            "true", "3", "8", "norm_num",
            "-- On a non-zero-length interval the constant is not the elapsed\n"
            "-- value: the spec demands some 5 and the rival reports some 0.\n"
            "-- `norm_num` decides the rational arithmetic (`decide` stalls on the\n"
            "-- Rat instance). Fails on the frozen solution, which reports some 5.\n",
        ),
    },

    # ---- VALUE class: echo the later reading (ports nagini weak-echo-end) ----
    {
        "id": "weak-echo-end",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the later reading itself rather than the elapsed interval:
        # input-derived, but the WRONG function of the inputs, and one that
        # ignores the earlier reading entirely.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let _s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let e := endClock\n"
            "    refitDuration := some e\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch reporting the post-fit reading itself, rather "
            "than the interval, produces a present non-negative float of the "
            "right type — so it WOULD resolve the current F2P — while the number "
            "it reports is a clock instant, not a duration, and is wildly "
            "unrelated to how long the refit took. A VALUE-FIDELITY supporting "
            "case, and the specific one that defeats a lax "
            "'any input-derived non-negative number will do' reading of the value "
            "clause. Ported from nagini's weak-echo-end with the same "
            "disposition."
        ),
        "rationale": (
            "REJECT from the VALUE clause: the spec pins the result to the "
            "DIFFERENCE of the two readings and the rival reports one reading, "
            "and the two coincide only when the earlier reading is zero. At "
            "(true, 2, 7) the spec demands 5 and the rival reports 7. This rival "
            "IGNORES `startClock`, so refuting it is what demonstrates the "
            "result genuinely depends on the earlier reading; its mirror "
            "(`weak-echo-start`) does the same for the later one. `norm_num`."
        ),
        "witness": _witness(
            "true", "2", "7", "norm_num",
            "-- The rival reports the later reading (7) where the spec pins the\n"
            "-- elapsed interval (5); they differ whenever the earlier reading is\n"
            "-- non-zero. Fails on the frozen solution, which reports some 5.\n",
        ),
    },

    # ---- VALUE class: echo the earlier reading (added for this carrier; the
    # ---- mirror of weak-echo-end, so the result's dependence on BOTH readings
    # ---- is demonstrated rather than assumed) ----
    {
        "id": "weak-echo-start",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the earlier reading itself: the mirror wrong function, ignoring
        # the later reading entirely.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let _e := endClock\n"
            "    refitDuration := some s\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch reporting the pre-fit reading instead of the "
            "interval likewise produces a present, well-typed, non-negative "
            "number and WOULD resolve the current F2P, while reporting a clock "
            "instant that says nothing about the refit's cost. A VALUE-FIDELITY "
            "supporting case whose distinct job is the BINDER it isolates: it is "
            "the only rival that ignores the LATER reading, so it is the only one "
            "whose rejection shows the reported duration must actually depend on "
            "the post-fit reading. Added for this carrier; nagini attacked only "
            "the later-reading direction."
        ),
        "rationale": (
            "REJECT from the VALUE clause, on the binder axis its mirror leaves "
            "untouched: the rival is a function of `startClock` alone, so it "
            "would satisfy any spec that failed to pin the result's dependence on "
            "`endClock`. At (true, 4, 9) the spec demands 5 and the rival reports "
            "4. Refuted at a point distinct from every other rival's, since it "
            "agrees with gold nowhere except when the later reading is twice the "
            "earlier one. `norm_num`."
        ),
        "witness": _witness(
            "true", "4", "9", "norm_num",
            "-- The rival reports the earlier reading (4) where the spec pins the\n"
            "-- elapsed interval (5), so the result's dependence on the LATER\n"
            "-- reading is what is being demonstrated. Fails on the frozen\n"
            "-- solution, which reports some 5.\n",
        ),
    },

    # ---- VALUE class: reversed orientation (ports nagini weak-swapped-args) ----
    {
        "id": "weak-reversed-orientation",
        "kind": "uniqueness",
        "expect": "reject",
        # Subtract in the wrong orientation: the earlier reading minus the later
        # one, i.e. the negated interval.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let e := endClock\n"
            "    refitDuration := some (s - e)\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch subtracting in the reversed orientation "
            "reports the NEGATED interval. On a real, monotonically advancing "
            "wall clock the readings are ordered, so the reported value is "
            "non-positive — and negative whenever the refit took any measurable "
            "time at all. The F2P asserts the observable is greater than or equal "
            "to zero, so that assertion fails and the patch does NOT resolve. A "
            "clean verify-does-not-imply-resolve break, alongside "
            "weak-never-present. Ports nagini's weak-swapped-args, but the REASON "
            "for rejection had to be re-derived: on nagini that rival was caught "
            "at least partly by violating its value oracle's own ordering "
            "precondition at the call site, and this carrier has neither an "
            "oracle nor a precondition, so it must be refuted purely on the value "
            "clause — which it is."
        ),
        "rationale": (
            "REJECT from the VALUE clause alone (no precondition is involved on "
            "this carrier): the spec pins the later-minus-earlier orientation, "
            "and at (true, 1, 6) it demands 5 while the rival reports -5. The two "
            "orientations agree only on a zero-length interval. `norm_num`."
        ),
        "witness": _witness(
            "true", "1", "6", "norm_num",
            "-- Reversed orientation: the spec pins some 5 (later minus earlier)\n"
            "-- and the rival reports some (-5). They agree only on a zero-length\n"
            "-- interval, and this point is not one. Fails on the frozen solution.\n",
        ),
    },

    # ---- VALUE class: the NEAR MISS this carrier makes expressible ----
    {
        "id": "weak-clamp-negative",
        "kind": "uniqueness",
        "expect": "reject",
        # Clamp the reported duration up to zero. Agrees with the spec on EVERY
        # ordered pair of readings; diverges only when the readings are reversed.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let e := endClock\n"
            "    refitDuration := some (max (e - s) 0)\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch clamping the reported duration up to zero "
            "would, on a real monotonically advancing wall clock, report exactly "
            "the same number as the correct one on every execution — so it WOULD "
            "resolve the F2P, and indeed would be indistinguishable from correct "
            "by any test that only reads the observable. It is nonetheless a "
            "different function, and it is the rival this bundle's spec was "
            "deliberately shaped to catch: the obligation carries NO ordering "
            "precondition on the two readings, precisely so that the value clause "
            "is pinned pointwise on reversed pairs too. A spec that guarded on "
            "`startClock ≤ endClock` would ADMIT this rival — that slack is a "
            "known weakness this spec closed, and this case is the standing "
            "regression test for it. No nagini counterpart exists: nagini's "
            "contract does carry that ordering precondition, so on that carrier "
            "this rival is not refutable at all."
        ),
        "rationale": (
            "REJECT from the VALUE clause on the sub-domain no other rival "
            "touches: this is a NEAR MISS that agrees with the spec everywhere "
            "the readings are ordered (checked: it satisfies the predicate at "
            "(true, 2, 7)), so it must be refuted at a REVERSED pair or not at "
            "all. At (true, 5, 2) the spec demands -3 and the rival reports 0. "
            "This is the only witness where `startClock > endClock`, which is why "
            "it is what demonstrates the obligation's unguarded `∀` over the two "
            "readings is load-bearing rather than decorative. `norm_num` closes "
            "it; plain `simp` does NOT (it reduces the goal only to `2 < 5`), so "
            "the arithmetic really is being decided here."
        ),
        "witness": _witness(
            "true", "5", "2", "norm_num",
            "-- The ONLY reject point with the readings reversed, which is the only\n"
            "-- sub-domain where this near-miss rival is wrong: the spec pins\n"
            "-- some (-3) and the clamp reports some 0. On every ordered pair the\n"
            "-- rival agrees with the spec, so a weaker obligation guarded by\n"
            "-- `startClock ≤ endClock` would admit it. Fails on the frozen\n"
            "-- solution, which reports some (-3) here.\n",
        ),
    },

    # ---- VALUE class: the NON-INTEGER sub-domain (added by the audit lane) ----
    {
        "id": "weak-floor-duration",
        "kind": "uniqueness",
        "expect": "reject",
        # Truncate the reported duration to a whole number of seconds. Agrees
        # with the spec on every pair whose interval is already an integer —
        # which is every point the rest of the battery visits — and diverges
        # only on a FRACTIONAL interval.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let e := endClock\n"
            "    refitDuration := some ((e - s).floor)\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch truncating the reported duration to whole "
            "seconds produces an observable that is present, well-typed and "
            "non-negative on an ordered pair — everything the F2P asserts — so it "
            "WOULD resolve the current F2P. It is nonetheless the wrong number "
            "for every refit that does not take an exact whole number of "
            "seconds, which is essentially every refit: a sub-second refit is "
            "reported as a duration of zero, losing the whole measurement the "
            "observable exists to carry. A VALUE-FIDELITY supporting case whose "
            "distinct job is the CARRIER: it is wrong only where the interval is "
            "fractional. Added by the audit lane; no nagini counterpart, and no "
            "shipped rival reached this sub-domain."
        ),
        "rationale": (
            "REJECT from the VALUE clause on the sub-domain the rest of the "
            "battery never visits. Every other witness sits on an integer "
            "interval, where truncation is the IDENTITY — so this rival agrees "
            "with the spec at all nine of the other rivals' refutation points and "
            "could only be caught at a fractional one. At (true, 0, 5/2) the spec demands "
            "5/2 and the rival reports 2. This is what shows the obligation pins "
            "the duration over the whole rational carrier rather than merely on "
            "integer-valued intervals — which matters because ℚ was chosen for "
            "exactly the readings that are not integers. Needs "
            "`norm_num [Rat.floor_def]`: bare `norm_num` leaves "
            "`¬↑(5 / 2).floor = 5 / 2` (the floor does not reduce on its own) and "
            "`decide` stalls on the `Rat` instance as everywhere else here."
        ),
        "witness": _witness(
            "true", "0", "(5/2)", "norm_num [Rat.floor_def]",
            "-- The ONLY reject point with a NON-INTEGER interval, and the only\n"
            "-- sub-domain where truncation is wrong at all: the spec pins\n"
            "-- some (5/2) and the rival reports some 2. On every integer interval\n"
            "-- — i.e. at every other witness's point — this rival AGREES with the\n"
            "-- spec, so nothing else in the battery could refute it. Fails on the\n"
            "-- frozen solution, which reports some (5/2) here.\n",
        ),
    },

    # ---- VALUE class: the NEGATIVE-READING sub-domain (added by the audit lane) ----
    {
        "id": "weak-negative-reading",
        "kind": "uniqueness",
        "expect": "reject",
        # Special-case a reading below zero, reporting nothing measured. Agrees
        # with the spec whenever both readings are non-negative, which is every
        # point the rest of the battery visits.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let e := endClock\n"
            "    refitDuration := some (if s < 0 then 0 else e - s)\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch special-casing a reading below zero — "
            "reporting a zero duration rather than the measured interval when the "
            "pre-refit reading is negative — agrees with the correct one on every "
            "execution whose readings are non-negative, so it WOULD resolve the "
            "F2P and would be invisible to any test that only reads the "
            "observable on a conventional clock. It is a different function all "
            "the same, and the spec's binder is an unguarded `∀` over ℚ with no "
            "sign condition on either reading, so the value clause is pinned "
            "there too. A VALUE-FIDELITY supporting case; added by the audit lane "
            "to cover the SIGN axis, which no shipped rival moved."
        ),
        "rationale": (
            "REJECT from the VALUE clause on the SIGN axis. Every other witness "
            "in the battery — including the reversed-pair one — uses two "
            "non-negative readings, so this rival agrees with the spec at all "
            "nine of their points and is refutable only where a reading is below "
            "zero. At (true, -3, 4) the spec demands 7 and the rival reports 0. "
            "It is the companion to `weak-clamp-negative`: that one shows the "
            "obligation carries no ORDERING guard on the pair, this one that it "
            "carries no SIGN guard on either reading. `norm_num`."
        ),
        "witness": _witness(
            "true", "(-3)", "4", "norm_num",
            "-- The ONLY reject point where a reading is NEGATIVE, which is the\n"
            "-- only sub-domain where this rival is wrong: the spec pins some 7\n"
            "-- and the rival reports some 0. Wherever both readings are\n"
            "-- non-negative — every other point in the battery — it agrees with\n"
            "-- the spec. Fails on the frozen solution, which reports some 7 here.\n",
        ),
    },

    # ---- PRESENCE class: the ZERO-LENGTH boundary (added by the audit lane) ----
    {
        "id": "weak-zero-length-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Suppress the observable when the measured interval is zero: treat "no
        # measurable time elapsed" as "nothing to report". Agrees with the spec on
        # every pair whose readings DIFFER — which is every point the rest of the
        # battery visits — and diverges only at the boundary where they coincide.
        "module": _impl(
            "  let mut refitDuration : Option ℚ := none\n"
            "  if refitEnabled then\n"
            "    let s := startClock\n"
            "    -- (the best model is refit on the whole dataset between the two readings)\n"
            "    let e := endClock\n"
            "    let d := e - s\n"
            "    if d ≠ 0 then\n"
            "      refitDuration := some d\n"
            "  return refitDuration"
        ),
        "refinement": (
            "A faithful real patch that only records the duration when the "
            "measured interval is non-zero produces the observable on every "
            "execution the F2P exercises — a refit of a real model takes "
            "measurable time, so the interval is positive there — and so it WOULD "
            "resolve the current F2P. It is nonetheless wrong on exactly the "
            "boundary the observable most needs to survive: a refit fast enough "
            "that the two readings coincide at the clock's resolution reports "
            "NOTHING rather than a zero duration, and a consumer reading the "
            "observable then cannot distinguish 'the refit was instantaneous' "
            "from 'no refit was performed'. That is the PRESENCE contract "
            "collapsing precisely where the two clauses meet. Added by the audit "
            "lane; no nagini counterpart."
        ),
        "rationale": (
            "REJECT from the PRESENCE clause at the ZERO-LENGTH boundary, which "
            "no other rival attacks. The battery's two other presence rivals move "
            "the `refitEnabled` binder (`weak-never-present` at `true`, "
            "`weak-always-present` at `false`) and both are wrong on a whole "
            "sub-domain; this one keeps presence correct everywhere except at the "
            "single point where `endClock = startClock`, so it is the only rival "
            "whose presence violation is VALUE-DEPENDENT. It also closes the one "
            "gap the admissibility case leaves: that case discharges the "
            "obligation at equal readings with the refit DISABLED (false 3 3), "
            "where the answer is `none` either way, so nothing in the battery "
            "previously pinned the enabled/equal-readings corner. At (true, 3, 3) "
            "the spec demands `some 0` and the rival reports `none`. `simp` closes "
            "it — a constructor clash, as with the other presence rivals."
        ),
        "witness": _witness(
            "true", "3", "3", "simp",
            "-- The ONLY reject point where the two readings are EQUAL and the\n"
            "-- refit is performed: the spec demands a PRESENT zero duration\n"
            "-- (some 0) and the rival suppresses the observable entirely.\n"
            "-- Wherever the readings differ — every other point in the battery —\n"
            "-- this rival agrees with the spec. Constructor clash, so `simp`\n"
            "-- closes it; fails on the frozen solution, which reports some 0.\n",
        ),
    },

]


# The axiom lane is G-AX's job and this gate ignores it. This bundle consumes no
# `axiom` and declares no `opaque` callee — the two wall-clock readings are
# environment-provided DATA modeled directly as rational inputs, not callees with
# axiomatized behavior — so there is nothing for that lane to probe here and the
# bundle's `axiom_check.py` is a skip stub. nagini's three AXIOM_TESTS (clock
# monotonicity soundness, ordered-difference non-negativity soundness, and the
# containment of the caller-reachable inputs in that axiom's domain) are dropped
# accordingly: two of the three are statements about a value oracle that has no
# counterpart in this model, and the third is a precondition-containment argument
# for a precondition this spec does not have.
AXIOM_TESTS = []
