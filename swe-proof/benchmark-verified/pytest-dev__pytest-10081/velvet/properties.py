"""properties.py — G-PBT falsification battery for pytest-dev__pytest-10081 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the elided
``prove_correct`` tactic body, is changed — both regions the consumer spec view
elides, so ``markers.same_spec`` holds and the ``prove_correct
shouldDeferCleanup`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method that decides, for a single test about to
run, whether its post-run cleanup step is deferred so an active interactive
debugger can inspect state:

  shouldDeferCleanup (debuggerActive unitSkipped groupSkipped : Bool)
      return (out : Bool)
    ensures out = shouldDefer debuggerActive unitSkipped groupSkipped   -- (C1)

where the transparent pure ``def`` is

  shouldDefer d u g := d && !(u || g)

ONE load-bearing top-level clause C1, a total function of the three ``Bool``
input binders. Everything in the post-image is GROUNDED in the method's own
arguments via the transparent ``def shouldDefer`` (the ``axioms`` region is
empty; there is no opaque answer key to echo, directive 8). Reading C1 back:
defer the cleanup EXACTLY when the debugger is active AND the test is not being
skipped, where "skipped" is the OR of the unit's own skip and its enclosing
group's skip. The discriminating fix is the ADDED group disjunct: the failing
test exercises the group-only-skip case (``unitSkipped=false, groupSkipped=true``
under ``debuggerActive=true``), where the pre-change guard consulted only the
unit and therefore deferred (then force-ran) the cleanup of a group-skipped
test — the bug. C1 pins ``out=false`` at exactly that point.

WHICH BINDERS C1 DEPENDS ON. C1 is symmetric in ``unitSkipped`` and
``groupSkipped`` (either suppresses via the OR) and gated by ``debuggerActive``
(false forces ``out=false`` regardless). All three binders are load-bearing, so
the reject witnesses must vary all three — a rival that mishandled only the
binder every witness held fixed would slip through.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS positives — APPLY. Structurally different but CORRECT impls that
    MUST verify, else C1 is SPEC-TOO-STRONG (over-fit to the frozen impl's
    single-``if`` form). One is a De Morgan single expression under the frozen
    proof; one is a cascade of early-return guards whose residual goal needs a
    retuned (still honest — no new lemma / axiom / sorry) tactic body.
  * ADMISSIBILITY — RE-AIMED. The method carries NO ``require`` (the
    pre-conditions region is empty), so the classic nagini "a normal F2P-shaped
    input satisfies the precondition" probe is vacuous — nothing could exclude
    an input. Re-aimed at the residual total-domain risk: an in-region ``assert``
    that the F2P-shaped inputs are non-degenerate (the group-only-skip input
    yields ``false`` AND a runnable input yields ``true``), witnessing that C1 is
    jointly satisfiable and discriminates the two directions. The impl and the
    single obligation are kept verbatim so C1 still discharges; the assert is
    LIVE — an audit re-ran it with the claim flipped to
    ``shouldDefer true false true = true`` and the build FAILED (exit 1,
    ``unsolved goals ... ⊢ False`` under the ``adm_1`` name prefix), so a false
    claim in this slot cannot pass.
  * FRAME / PERMISSION-MUTATION (the nagini MANDATORY class) — VACUOUS. The
    nagini sibling holds each skip facet at a half-permission ``Acc(.,1/2)``
    read-only reference and rejects an impl that WRITES one for INSUFFICIENT
    PERMISSION. Velvet is referentially transparent: the three inputs are
    immutable ``Bool`` VALUES, this bundle declares no ``mut`` parameter, and
    there is no heap, aliasing, or permission system to subvert. There is no
    read-only input to overwrite, so both nagini frame-mutation probes
    (``frame-mutate-obj-skip`` / ``frame-mutate-class-skip``) have no
    counterpart. No substitute is fabricated (see footer).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``shouldDeferCleanupTester d u g = false`` says the extracted program's
observable output violates the method's postcondition at that concrete input.
Checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. All three inputs are ``Bool`` literals with
decidable equality, so every witness closes by ``decide``. There is no
``require``, so the tester is never vacuously true and no precondition need be
pinned. Each reject witness below was run against BOTH the rival (exit 0) and
the frozen solution (exit 1) with two real builds and was SEEN to discriminate.
No witness binds a hypothesis (the carrier is fully transparent — every input is
a concrete literal), so there is no joint-satisfiability obligation.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(mapping.md §3: the decision consumes two unchanged boolean-valued helpers as
R-identity inputs; there is no consumed axiom and no ``:|`` stub). The nagini
sibling's single axiom-lane probe over the real ``_is_skipped`` is G-AX's job
(there it validates the A-reference; here G-CONF carries the R/I burden) and
this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10081"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (marker lines and the
# ---- inline comment included); lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both facts asserted
# ---- at load by _swap). Every variant replaces exactly this text, so each edit
# ---- lies inside the elided impl region and same_spec holds by construction.
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    -- A test is \"skipped\" if it is skipped directly or its enclosing group is.\n"
    "    let skipped : Bool := unitSkipped || groupSkipped\n"
    "    if debuggerActive && !skipped then\n"
    "      return true\n"
    "    else\n"
    "      return false\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- the `-- impl-start` marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- proof-body anchor. The frozen tactic script is elided from the consumer
# ---- spec view (only the obligation header is kept), so a case may retune the
# ---- tactic body without touching the spec statement or dropping the
# ---- obligation. Unique in the file. Rivals leave it AS-IS (the rejection is
# ---- carried by the witness, not the tactic script); a loop-free correct
# ---- reshape whose residual goal no longer matches may retune it (honestly —
# ---- no new lemma / axiom / sorry).
_GOLD_PROOF = (
    "prove_correct shouldDeferCleanup by\n"
    "  loom_solve <;>\n"
    "    cases debuggerActive <;> cases unitSkipped <;> cases groupSkipped <;>\n"
    "      simp_all [shouldDefer]"
)
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (for a correct reshape whose
    residual goal no longer matches the frozen script; the retuned script uses
    only core tactics — no new lemma, axiom, sorry, or native_decide)."""
    return _swap(_impl(body), _GOLD_PROOF, proof)


def _impl_assert(assert_block):
    """Insert an in-region assert right after `-- impl-start`, keep the gold body
    and the frozen proof (its `simp_all [shouldDefer]` arm discharges the extra
    decidable VC)."""
    return _swap(_BASE, _IMPL_START, _IMPL_START + assert_block)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. `shouldDeferCleanupTester d u g = false` says the extracted
# ---- program's observable output violates the postcondition at that input. No
# ---- `axiom`/`sorry`/`native_decide`; the frozen solution rejects each witness.
def _tester(dbg, unit, grp):
    return (
        "extract_program_for shouldDeferCleanup\n"
        "prove_precondition_decidable_for shouldDeferCleanup\n"
        "prove_postcondition_decidable_for shouldDeferCleanup\n"
        "derive_tester_for shouldDeferCleanup\n\n"
        f"example : shouldDeferCleanupTester {dbg} {unit} {grp} = false := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else C1 is SPEC-TOO-STRONG (over-fit to the frozen
    # single-`if` form). Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-demorgan",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report C1's truth value DIRECTLY as a conjunction of negations
        # (De Morgan of `!(u || g)`), no intermediate `skipped` binding and no
        # branch. Logically identical to `shouldDefer`, so C1 discharges and the
        # frozen `simp_all [shouldDefer]` script still closes.
        "module": _impl(
            "    -- impl-start\n"
            "    return (debuggerActive && !unitSkipped && !groupSkipped)\n"
            "    -- impl-end"),
        "rationale": (
            "a CORRECT impl in a DIFFERENT surface syntax (a single De Morgan "
            "conjunction `d && !u && !g` instead of gold's `d && !(u || g)` guard "
            "with an intermediate `skipped` binding) must verify; the value is "
            "unchanged so C1 (`out = shouldDefer ...`) discharges and the frozen "
            "proof closes as-is. Ports the nagini pos-control-demorgan. Else C1 is "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-nested-if",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a CASCADE of early-return guards (branch on debuggerActive
        # first, then the two skip facets separately), the opposite control shape
        # to gold's single combined boolean. Computes exactly `shouldDefer`. The
        # residual goal no longer matches the frozen `cases ... simp_all` script
        # (which overflows `simp`'s recursion on the nested `if`), so the proof is
        # retuned to a case split + `decide` — core tactics only, no new lemma /
        # axiom / sorry.
        "module": _impl_reproved(
            "    -- impl-start\n"
            "    if !debuggerActive then\n"
            "      return false\n"
            "    else\n"
            "      if unitSkipped then\n"
            "        return false\n"
            "      else\n"
            "        if groupSkipped then\n"
            "          return false\n"
            "        else\n"
            "          return true\n"
            "    -- impl-end",
            "prove_correct shouldDeferCleanup by\n"
            "  loom_solve <;>\n"
            "    revert debuggerActive unitSkipped groupSkipped <;> decide"),
        "rationale": (
            "a CORRECT impl with the OPPOSITE control flow — a cascade of "
            "early-return guards (debugger first, then each skip facet nested) "
            "instead of gold's single combined boolean — must verify. It returns "
            "true iff the debugger is active and neither facet is skipped, "
            "identical to C1. The frozen `simp_all` overflows on the nested `if`, "
            "so the proof is HONESTLY retuned to a `revert ... <;> decide` case "
            "split (core tactics only; no new lemma, axiom, or sorry). Ports the "
            "nagini pos-control-nested-if. Else C1 is SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-self-call. That case established
    # the read-only fractional-permission precondition on an F2P-shaped input.
    # This method has NO `require` (empty pre-conditions region) and no heap
    # permission, so the "a normal input is admitted" probe is vacuous — nothing
    # could exclude it. Re-aimed at the residual total-domain risk: that C1 is
    # jointly satisfiable AND discriminates the two directions the F2P exercises.
    # An in-region `assert` pins that the group-only-skip input yields `false`
    # (the fixed behaviour) AND a runnable input yields `true` (non-degenerate,
    # not a constant), witnessing C1 is a genuine two-valued function on the F2P
    # domain. Impl and the obligation kept verbatim so C1 still discharges; the
    # assert is LIVE (a false claim leaves an unsolved goal, confirmed out-of-band).
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_assert(
            "    assert (with_name_prefix `adm\n"
            "      (shouldDefer true false true = false ∧ shouldDefer true false false = true))\n"),
        "rationale": (
            "the total domain admits the F2P-shaped inputs and C1 is "
            "non-degenerate there: with the debugger active, the group-only-skip "
            "input (unit not skipped, group skipped) yields `false` — the fixed "
            "behaviour — while the fully-runnable input (neither skipped) yields "
            "`true`. The in-region assert must discharge (else the interesting "
            "sub-domain is excluded / the post-image would be a constant); the "
            "impl and the obligation are kept verbatim so C1 still discharges too. "
            "Re-aimed from the nagini admiss-self-call, whose read-only-precondition "
            "half has no counterpart on this referentially-transparent carrier with "
            "no `require`. Else PRECOND-/SPEC-degenerate."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. All attack the single clause
    # C1; the three `Bool` binders are varied across the witnesses (see footer).
    # =====================================================================
    {
        "id": "rival-drop-group-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Consider only the unit's own skip, dropping the enclosing
        # group's disjunct entirely (the exact pre-change guard). CORRECT on every
        # input where the group is not the sole skip; WRONG precisely on the
        # group-only-skip case under the debugger.
        "module": _impl(
            "    -- impl-start\n"
            "    let skipped : Bool := unitSkipped\n"
            "    if debuggerActive && !skipped then\n"
            "      return true\n"
            "    else\n"
            "      return false\n"
            "    -- impl-end"),
        "refinement": (
            "this IS the pre-change guard: it consults only the unit's own skip "
            "marker, not the enclosing group's. For a group decorated to skip "
            "whose individual unit is NOT decorated (unitSkipped=false, "
            "groupSkipped=true) under the debugger, it still defers (then "
            "force-runs) the cleanup of a group-skipped test. That is exactly the "
            "behaviour the failing test asserts must NOT happen, so the faithful "
            "real patch (the un-patched guard) does NOT resolve — this is the "
            "defect the fix corrects."),
        "rationale": (
            "REJECT from C1 (`out = shouldDefer ...`): shouldDefer ORs both skip "
            "facets, so dropping the group disjunct returns `true` where C1 pins "
            "`false` on the group-only-skip case. Refuted at (debuggerActive=true, "
            "unitSkipped=false, groupSkipped=true) — the F2P discriminator. If it "
            "verified => SPEC-TOO-WEAK (admits the bug)."),
        "witness": _tester("true", "false", "true"),
    },
    {
        "id": "rival-drop-unit-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the bug: consider only the enclosing group, dropping the
        # unit's own disjunct. CORRECT wherever the unit is not the sole skip;
        # WRONG on the unit-only-skip case under the debugger. Guards against a
        # spec that pinned only the group side.
        "module": _impl(
            "    -- impl-start\n"
            "    let skipped : Bool := groupSkipped\n"
            "    if debuggerActive && !skipped then\n"
            "      return true\n"
            "    else\n"
            "      return false\n"
            "    -- impl-end"),
        "refinement": (
            "drops the unit's own skip and keeps only the enclosing group's. For "
            "a unit decorated to skip inside a NON-skipped group (unitSkipped=true, "
            "groupSkipped=false) under the debugger it defers and force-runs the "
            "cleanup of a unit that is itself skipped — the pre-existing "
            "function-level skip behaviour (a sibling passing test) forbids this, "
            "so the faithful real patch does NOT resolve."),
        "rationale": (
            "REJECT from C1: shouldDefer ORs both facets, so dropping the unit "
            "disjunct returns `true` where C1 pins `false` on the unit-only-skip "
            "case. Refuted at (debuggerActive=true, unitSkipped=true, "
            "groupSkipped=false) — a DISTINCT point from rival-drop-group-skip "
            "(the two single-skip facets are mirror images), varying the "
            "unitSkipped/groupSkipped binders. If it verified => SPEC-TOO-WEAK "
            "(pinned only the group side)."),
        "witness": _tester("true", "true", "false"),
    },
    {
        "id": "rival-and-connective",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG CONNECTIVE: treat a test as skipped only when BOTH facets are
        # marked (AND where the spec demands OR). WRONG on every single-skip case
        # under the debugger — it defers when it must not.
        "module": _impl(
            "    -- impl-start\n"
            "    let skipped : Bool := unitSkipped && groupSkipped\n"
            "    if debuggerActive && !skipped then\n"
            "      return true\n"
            "    else\n"
            "      return false\n"
            "    -- impl-end"),
        "refinement": (
            "AND-combining the two facets only treats a test as skipped when BOTH "
            "the unit and its enclosing group carry the marker. The real guard ORs "
            "them, so a group-only skip (or a unit-only skip) must suppress the "
            "deferral. Under AND, a unit-only-skip test (unitSkipped=true, "
            "groupSkipped=false) under the debugger is NOT seen as skipped, so its "
            "cleanup is deferred and force-run — the pre-existing function-level "
            "skip behaviour forbids this, so the faithful real patch does NOT "
            "resolve."),
        "rationale": (
            "REJECT from C1: shouldDefer uses OR, so AND returns `true` where C1 "
            "pins `false` on any single-skip case. Refuted at (debuggerActive=true, "
            "unitSkipped=true, groupSkipped=false) where rival-drop-unit-skip also "
            "fails but for a DIFFERENT reason (it drops a disjunct; this one keeps "
            "both but conjoins them) — a genuinely distinct rival attacking the "
            "CONNECTIVE. Its wrong-set is BOTH single-skip points "
            "{(true,true,false), (true,false,true)}, so it is a strict extension of "
            "each drop rival's single wrong point and coincides with neither; it is "
            "correct at the both-skipped point (true,true,true) where "
            "rival-ignore-skip breaks. If it verified => SPEC-TOO-WEAK (wrong "
            "connective)."),
        "witness": _tester("true", "true", "false"),
    },
    {
        "id": "rival-ignore-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Always-defer-under-debugger: ignore both skip facets entirely. CORRECT
        # on every non-skipped input; WRONG on every skipped input under the
        # debugger. The strongest "ignore the work" rival — it satisfies the
        # debugger-off and fully-runnable directions trivially.
        "module": _impl(
            "    -- impl-start\n"
            "    return debuggerActive\n"
            "    -- impl-end"),
        "refinement": (
            "this restores the unconditional deferral whenever the debugger is "
            "active, dropping the entire skip guard. Every skipped test under the "
            "debugger — both the group-only-skip F2P case AND the pre-existing "
            "function-level skip behaviour — would then have its cleanup deferred "
            "and force-run. The faithful real patch keeps the skip guard and does "
            "NOT resolve without it."),
        "rationale": (
            "REJECT from C1: with the debugger active and BOTH facets skipped, "
            "shouldDefer pins `false` but the rival returns `true`. Refuted at "
            "(debuggerActive=true, unitSkipped=true, groupSkipped=true) — a "
            "both-skipped point no other rival uses, exercising both skip binders "
            "at `true`. If it verified => SPEC-TOO-WEAK (ignores skip entirely)."),
        "witness": _tester("true", "true", "true"),
    },
    {
        "id": "rival-ignore-debugger",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the debugger gate: defer whenever NEITHER facet is skipped,
        # regardless of the debugger. WRONG on every non-skipped input when the
        # debugger is OFF — it defers the cleanup with no debugger to inspect
        # state. Attacks the `debuggerActive` binder that the other rivals hold
        # at `true`.
        "module": _impl(
            "    -- impl-start\n"
            "    return (!(unitSkipped || groupSkipped))\n"
            "    -- impl-end"),
        "refinement": (
            "drops the debugger gate: it defers the cleanup for any runnable test "
            "even with no interactive debugger active. A real patch of this shape "
            "would postpone (and reshape the timing of) the cleanup step "
            "unconditionally, changing when the test-case instance interacts with "
            "the results object for EVERY runnable test — breaking the "
            "pre-existing teardown-timing behaviour a sibling passing test pins — "
            "so it does NOT resolve."),
        "rationale": (
            "REJECT from C1: shouldDefer is `false` whenever the debugger is off "
            "(the `d &&` gate), but the rival returns `true` on any non-skipped "
            "input regardless. Refuted at (debuggerActive=false, unitSkipped=false, "
            "groupSkipped=false) — the ONLY witness exercising debuggerActive=false, "
            "so the battery varies all three binders and the debugger gate is not "
            "left unattacked. If it verified => SPEC-TOO-WEAK (drops the debugger "
            "gate)."),
        "witness": _tester("false", "false", "false"),
    },
    {
        "id": "rival-never-defer",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every other rival errs by OVER-deferring (each returns
        # `true` where C1 pins `false`), so the whole battery left the POSITIVE
        # direction of C1 unattacked: an impl that never defers at all agreed with
        # every existing reject witness. This rival keeps the gold guard's shape
        # and control flow verbatim but returns `false` in BOTH arms, so it is
        # wrong exactly at the fully-runnable point where C1 pins `true`. Without
        # it, a spec that only forbade deferral (an implication rather than the
        # two-sided equality C1 actually states) would pass this battery.
        "module": _impl(
            "    -- impl-start\n"
            "    let skipped : Bool := unitSkipped || groupSkipped\n"
            "    if debuggerActive && !skipped then\n"
            "      return false\n"
            "    else\n"
            "      return false\n"
            "    -- impl-end"),
        "refinement": (
            "this never postpones the cleanup at all — it drops the postponement "
            "even for a test that is actually going to run under an active "
            "interactive debugger. The whole point of the guarded block is that "
            "with the debugger active, a runnable test's cleanup is held back so "
            "the debugger can inspect instance state before it is torn down; a "
            "sibling passing test pins that the held-back cleanup is nonetheless "
            "eventually run for every runnable test under the debugger (it is "
            "tracked to avoid leaking instances). An impl that never defers leaves "
            "that cleanup to run in its normal place, so the deferred-cleanup hook "
            "is never armed and the ordering that sibling test observes is gone. "
            "The faithful real patch keeps the postponement for runnable tests and "
            "narrows only the skipped case, so this does NOT resolve."),
        "rationale": (
            "REJECT from C1: shouldDefer is `true` at the fully-runnable point "
            "(debugger active, neither facet skipped), but the rival returns "
            "`false` there. Refuted at (debuggerActive=true, unitSkipped=false, "
            "groupSkipped=false) — a FIFTH distinct input point, and the ONLY "
            "witness in the battery that pins the `true` direction of C1; every "
            "other rival is refuted at a point where C1 pins `false`. If it "
            "verified => SPEC-TOO-WEAK (C1 would be a one-sided prohibition on "
            "deferring rather than the two-sided equality it states)."),
        "witness": _tester("true", "false", "false"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-nested-if      -> pos-control-nested-if         PORTED (proof retuned)
#   pos-control-demorgan       -> pos-control-demorgan          PORTED
#   admiss-self-call           -> admiss-f2p-shape              RE-AIMED
#   frame-mutate-obj-skip      -> (none)                        VACUOUS
#   frame-mutate-class-skip    -> (none)                        VACUOUS
#   weak-drop-class-skip       -> rival-drop-group-skip         PORTED (central bug)
#   weak-drop-obj-skip         -> rival-drop-unit-skip          PORTED
#   weak-and-connective        -> rival-and-connective          PORTED
#   weak-ignore-skip           -> rival-ignore-skip             PORTED
#   (no sibling)               -> rival-ignore-debugger         ADDED (debugger gate)
#   (no sibling)               -> rival-never-defer             ADDED BY AUDIT
#                                                               (positive direction)
#   AXIOM_TESTS (1)            -> (none)                        DROPPED (G-AX lane)
#
# 9 velvet SPEC cases: 2 soundness, 1 admissibility, 6 uniqueness. Every nagini
# uniqueness rival that attacks the modeled clause C1 is ported; two rivals are
# ADDED — one so the `debuggerActive` binder (held at true by every ported rival)
# has a dedicated attacker, and one (by the independent audit) because every
# ported rival errs by OVER-deferring, leaving the `true` direction of C1 with no
# attacker at all.
#
# PORTED (pos-control-demorgan, pos-control-nested-if): the two nagini positive
#   controls carry across intact — the De Morgan single expression under the
#   frozen proof, and the early-return cascade whose residual goal needs a
#   retuned (honest) tactic body. Both verified with real builds.
# RE-AIMED (admiss-self-call -> admiss-f2p-shape): the nagini case established a
#   read-only fractional-permission precondition on an F2P-shaped input via a
#   self-call. This method has NO `require` and no heap permission, so that probe
#   is vacuous; re-aimed at the residual total-domain risk — an in-region `assert`
#   witnessing C1 is a genuine two-valued function that pins `false` on the
#   group-only-skip case and `true` on the runnable case. loom_solve's
#   `simp_all [shouldDefer]` arm discharges the VC; the impl and obligation are
#   kept verbatim. The assert is LIVE (a false claim fails, confirmed out-of-band).
# PORTED (rival-drop-group-skip): the central pre-change bug (consult only the
#   unit, drop the enclosing group) ports directly and is the headline reject,
#   refuted by C1 at the group-only-skip F2P discriminator. PORTED
#   (rival-drop-unit-skip, rival-and-connective, rival-ignore-skip): the
#   symmetric drop, the wrong-connective, and the ignore-skip rivals all port
#   directly, each refuted by C1 at a concrete input with a machine-checked
#   tester witness.
# ADDED (rival-ignore-debugger): the nagini P-pdb direction ("never defer off the
#   debugger") is implied by its P-main but has no dedicated rival; here it is a
#   first-class attacker so the `debuggerActive` binder — held at `true` by every
#   ported rival — is varied to `false` by at least one witness. Drops the
#   debugger gate; refuted by C1 at debuggerActive=false. A real divergence with a
#   machine-checked witness, not fabricated wrongness.
# FRAME-MUTATION (frame-mutate-obj-skip, frame-mutate-class-skip): VACUOUS, and
#   the audit DEMONSTRATED it rather than asserting it. The nagini rivals write
#   through half-permission read-only references to the skip facets and are
#   rejected for insufficient permission. Velvet is referentially transparent:
#   the three inputs are immutable Bool VALUES, no `mut` binder, no heap, no
#   aliasing, no permission system. Two real builds pin the collapse:
#     * the LITERAL analogue `unitSkipped := true` in the impl region does not
#       ELABORATE — "`unitSkipped` cannot be mutated, only variables declared
#       using `let mut` can be mutated" — a PARSE/elaboration error, not a spec
#       verdict, so it could never be a legitimate reject case (its witness
#       would attribute nothing to C1);
#     * adding `mut` to the binder to make the write legal is out of scope by
#       construction: it changes the method signature, which lives in the spec
#       view, so `variant_problems` reports "spec view differs (same_spec
#       failed)". The permission class is therefore not expressible here at all.
#   The nearest EXPRESSIBLE thing — value-level shadowing (`let unitSkipped :=
#   true`, build exit 1, unsolved goal at `.true.false.false`) — is rejected for
#   a plain VALUE mismatch, i.e. it is just another wrong-value rival and already
#   subsumed by rival-ignore-skip's class. No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness/containment probe over
#   the real skip-marker helper is G-AX's job (here there is no consumed axiom;
#   mapping.md §3 models the helpers as R-identity Bool inputs and G-CONF carries
#   the R/I burden). The G-PBT gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE. The obligation has ONE top-level clause C1
#   (`out = shouldDefer debuggerActive unitSkipped groupSkipped`) — attacked by
#   ALL six rivals — and THREE Bool input binders. Every binder is DISCRIMINATED
#   by the reject witnesses:
#     * unitSkipped   varied over {false, true, true, true, false, false};
#     * groupSkipped  varied over {true, false, false, true, false, false};
#     * debuggerActive varied over {true, true, true, true, false, true}
#                      — rival-ignore-debugger is the sole witness at `false`, so
#                      the debugger gate is not left unattacked.
#   The six reject witnesses probe FIVE DISTINCT input points (pts=5):
#     (true,  false, true)   rival-drop-group-skip   (group-only skip; the F2P bug)
#     (true,  true,  false)  rival-drop-unit-skip    (unit-only skip)
#     (true,  true,  false)  rival-and-connective    (unit-only skip; different
#                                                     mechanism — attacks the
#                                                     connective, not a disjunct)
#     (true,  true,  true)   rival-ignore-skip       (both skipped)
#     (false, false, false)  rival-ignore-debugger   (debugger off, runnable)
#     (true,  false, false)  rival-never-defer       (runnable under the debugger —
#                                                     the only point where C1 pins
#                                                     `true`; added by the audit)
#   DIRECTIONS. Five of the six rivals err by OVER-deferring (they return `true`
#   where C1 pins `false`); rival-never-defer is the sole UNDER-deferring rival
#   and the sole witness at a point where C1 pins `true`. Both directions of the
#   equality are therefore attacked, which is what stops a one-sided
#   "never defer when skipped" implication from passing as C1.
#   Only rival-drop-unit-skip and rival-and-connective share a point: the two
#   single-skip facets are exhausted by the drop-group / drop-unit rivals, so the
#   third single-skip attacker (the connective) necessarily reuses one — but it
#   is a genuinely different rival: it keeps both facets and conjoins them, so its
#   wrong-set is BOTH single-skip points {(true,true,false),(true,false,true)}
#   (a strict superset of either drop rival's single wrong point, and equal to
#   neither), while it is CORRECT at the both-skipped point (true,true,true) where
#   rival-ignore-skip breaks. Verified by an audit build: the connective rival's
#   witness re-stated at (true,false,true) ALSO elaborates (exit 0), so its
#   disagreement with gold is strictly wider than the point it is refuted at —
#   not a near-miss reusing another's point to hide a wider agreement. C1 and
#   all three binders are DEFENDED by the two positives and the admissibility case
#   (all discharge on gold across the debugger-on/off and skip/no-skip directions).
#   Each witness was SEEN to discriminate: it ELABORATES against the rival (exit 0)
#   and FAILS against the frozen solution (exit 1), confirmed with two real builds
#   each; an independent audit REBUILT all of them from scratch and observed the
#   same split (rival exit 0 / gold exit 1, six pairs), with every gold-side
#   failure being the SEMANTIC refutation "`decide` proved that the proposition
#   shouldDeferCleanupTester <d> <u> <g> = false is false" — not a missing
#   identifier, type error, unfolding failure, or timeout.
#   AUDIT SPEC-STRENGTH PROBES (attacks D and E, real builds, none shipped as a
#   case). Four NEW correct reshapes all VERIFY (exit 0), so C1 is not
#   over-fit: skip-tested-first (`if u || g then false else d`), the
#   double-negation form `!(!d || u || g)`, a three-way `match` on the tuple, and
#   a `notSkipped` intermediate binding. Five NEW wrong impls are all REJECTED
#   (exit 1): constant `false`, constant `true`, XOR-of-the-skip-facets, a
#   sign-flipped debugger gate `!d && !(u||g)`, and a skip-only guard that drops
#   the debugger. No wrong impl verified => no SPEC-TOO-WEAK hole found on the
#   value lane; no correct reshape was rejected => no SPEC-TOO-STRONG hole.
#   WHY THE WITNESS REQUIREMENT IS LOAD-BEARING HERE, measured: the
#   pos-control-nested-if impl is CORRECT, yet under the FROZEN tactic script it
#   fails to build with `simp` "maximum recursion depth has been reached" — the
#   same exit 1 a wrong rival produces. So on this cell "did not verify" alone
#   attests nothing, and each rejection rests on its witness.
#   No witness binds a hypothesis (the carrier is fully transparent — every
#   input is a concrete Bool literal), so there is no joint-satisfiability
#   obligation. No `sorry`/`admit`/`native_decide`/`axiom` appears in any witness.
AXIOM_TESTS = []
