"""properties.py — G-PBT falsification battery for django__django-13410 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and every ``prove_correct <name>`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation, checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted methods over the purely-functional core):

  acquireLock (outcome : LockOutcome) return (out : Bool)
    ensures out = acquiredOk outcome
      -- LOAD-BEARING: report the outcome of the underlying lock primitive as a
      --   DEFINITE boolean — `true` exactly when the primitive completed
      --   normally, `false` exactly when a non-blocking request found the
      --   resource already held. `acquiredOk` is a total, fully-unfolded pure
      --   function of the sole input `outcome` (`decide (outcome = succeeded)`),
      --   so the equality is grounded in the argument, not an opaque oracle.

  releaseLock return (out : Bool)
    ensures out = true
      -- LOAD-BEARING: a release reports success as a DEFINITE `true` (a real
      --   boolean, never the primitive's no-value normal-completion result).
      --   Zero inputs; the post-image is a single literal.

The ONE input binder is ``outcome : LockOutcome`` (values ``succeeded`` /
``contended``); ``releaseLock`` takes none. The post-image must hold for EVERY
value of ``outcome``.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling models
the fix over the RUNTIME EFFECT of invoking the OS lock primitive: it splits the
change into ``acquire(available: bool)`` and ``release()``, threads the primitive
through a body-less capability-token predicate (``lock_held()`` / ``lock_freed()``)
whose SOLE producer is the primitive's normal completion, and grounds each
helper's value postcondition against the ARGUMENT plus that token. Its two
A-consumed axioms (``primitive_lock`` / ``primitive_release`` over ``fcntl.flock``)
encode the control-flow signal (normal completion vs. raise) and the sentinel
fact (``EMPTY_RESULT != 0``, i.e. ``None != 0``).

This bundle models ONLY the purely-functional core the fix actually turns on —
WHAT boolean an acquisition/release reports given the primitive's OUTCOME. The
primitive's outcome is taken directly as the input ``LockOutcome`` (an
R-refinement: ``succeeded`` ↔ the call returns normally, ``contended`` ↔ a
non-blocking request raises ``BlockingIOError``; mapping.md §2). There is no
``available`` boolean distinct from "the primitive was actually invoked", no
heap, no capability token, and no axiomatized callee (the ``axioms`` region is
empty; mapping.md §3 — G-AX is skip). The gold patch's whole change is exactly
this outcome→boolean translation, and that is the entire modeled surface here.

ADVERSARIAL READ of the nagini classes on THIS carrier (see footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS. Lean and Velvet are referentially
    transparent: no heap, no aliasing, no fractional permission. Neither method
    declares a ``mut`` binder and ``acquireLock`` takes an immutable scalar,
    ``releaseLock`` nothing. There is no read-only input to overwrite and no
    permission system to trip. The nagini sibling ALSO records this class
    inapplicable (``has_readonly_input = False``: acquire takes a plain bool,
    release takes no parameters). No substitute is fabricated.
  * CONTROL-FLOW-EFFECT (nagini's primary uniqueness attack, the no-op that
    returns a value WITHOUT invoking the primitive so the missing side-effect is
    invisible to the value abstraction) — NO COUNTERPART on this carrier. The
    nagini spec closed that flank with a capability-token EFFECT clause because
    its abstraction could observe the side-effect of actually calling the
    primitive. This bundle does NOT model that side-effect at all: the
    primitive's outcome is a GIVEN input (``outcome : LockOutcome``), not
    something the impl chooses to invoke or bypass. There is no "return the
    argument without calling the primitive" move to make — the outcome is
    already the argument, and the impl's only freedom is which boolean it derives
    from it. The nagini no-op's VALUE facet (does the reported boolean match the
    real outcome?) DOES survive as the ordinary wrong-value surface, and is
    heavily attacked below (always-false / always-true / inverted). Its EFFECT
    facet is vacuous here — the irreversible side effect leaves no value
    footprint the spec can force (spec_guide directive 9 class), and this bundle
    deliberately does not attempt to model it. Reported as an omission in the
    footer, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to
    ``acquiredOk outcome`` (a concrete ``def`` in the ``pure`` region, computed
    from the sole argument; the ``axioms`` region is empty) and to the literal
    ``true``. There is no opaque answer-key an echo could carry; the unique
    satisfier IS the grounded decision. The nagini sibling reached the same
    conclusion (its postconditions are grounded in the argument / a literal, no
    ``@Pure`` answer-key oracle).
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. The decision is a
    two-point function of ``outcome``; a rival can get one point right and the
    other wrong (always-true / always-false), or invert both (inverted). Each is
    refuted at a concrete outcome by a machine-checked witness.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. Every frozen impl region is
LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS MECHANICS. Both frozen impls are STRAIGHT-LINE (no loop): the extracted
programs reduce fully under ``decide``. Each reject rival carries a
machine-checked refutation ``witness`` — a Velvet tester statement
(``acquireLockTester <outcome> = false`` / ``releaseLockTester = false``) at ONE
concrete input, checked in a file whose ``prove_correct`` blocks have been
stripped so no tactic script can mask the verdict. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
its rival (exit 0) and FAILS (``decide`` proves the proposition false, exit 1)
against the frozen solution, so each rejection is a genuine spec refutation and
not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` / mapping.md §3 declare no consumed ``axiom``
and no deep-model reference — the outcome→boolean translation is modeled deeply
over the concrete ``LockOutcome`` input, validated end-to-end by
``conformance_check.py`` (G-CONF). The nagini sibling's two A-consumed axioms
over ``fcntl.flock`` have no counterpart because this carrier does not
axiomatize the callee; the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13410"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen regions, verbatim. Every rival / reshape edits ONLY an impl body (and,
# for reshapes / admissibility, the elided proof body), so the spec view is
# untouched and same_spec holds by construction. Each anchor is UNIQUE in
# Solution.lean (asserted below and re-checked by _swap at load).
# ---------------------------------------------------------------------------
_ACQ_IMPL = """    -- impl-start
    if outcome = LockOutcome.succeeded then
      return true
    else
      return false
    -- impl-end"""

_REL_IMPL = """    -- impl-start
    return true
    -- impl-end"""

_ACQ_PROOF = """prove_correct acquireLock by
  loom_solve <;> cases outcome <;> simp_all [acquiredOk]"""

_REL_PROOF = """prove_correct releaseLock by
  loom_solve"""

for _name, _s in (("acq impl", _ACQ_IMPL), ("rel impl", _REL_IMPL),
                  ("acq proof", _ACQ_PROOF), ("rel proof", _REL_PROOF)):
    assert _BASE.count(_s) == 1, f"frozen region drifted: {_name}"


def _acq_impl(new_body):
    """Variant with ONLY the acquireLock impl body replaced."""
    return _swap(_BASE, _ACQ_IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _rel_impl(new_body):
    """Variant with ONLY the releaseLock impl body replaced."""
    return _swap(_BASE, _REL_IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _acq_impl_reproved(new_body, new_proof):
    """acquireLock impl body replaced AND its proof retuned (correct reshapes)."""
    return _swap(_acq_impl(new_body), _ACQ_PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `<name>Tester <args> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` blocks are stripped, so no tactic script can mask
# ---- the verdict.
def _acq_witness(outcome):
    return (
        "extract_program_for acquireLock\n"
        "prove_precondition_decidable_for acquireLock\n"
        "prove_postcondition_decidable_for acquireLock\n"
        "derive_tester_for acquireLock\n\n"
        f"example : acquireLockTester {outcome} = false := by\n  decide\n"
    )


_REL_WITNESS = (
    "extract_program_for releaseLock\n"
    "prove_precondition_decidable_for releaseLock\n"
    "prove_postcondition_decidable_for releaseLock\n"
    "derive_tester_for releaseLock\n\n"
    "example : releaseLockTester = false := by\n  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the decision value identical on every
    # input and only reshapes the executable surface; the reproof stays within
    # the frozen `loom_solve <;> cases … <;> simp_all` script (or plainly
    # `loom_solve`).
    # =====================================================================
    {
        "id": "pos-acquire-direct-pure",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the pure decision function directly instead of the
        # two-branch if/return. Same value on every `outcome`; the do-block no
        # longer needs the case split, so the reproof is a plain `loom_solve`.
        "module": _acq_impl_reproved(
            "    return acquiredOk outcome",
            "prove_correct acquireLock by\n  loom_solve"),
        "rationale": (
            "returning `acquiredOk outcome` directly is definitionally the same "
            "boolean the two-branch form produces on every `outcome`, so the "
            "ensures `out = acquiredOk outcome` still discharges; a structurally-"
            "different correct reshape must verify, else SPEC-TOO-STRONG (over-fit "
            "to the if/return spelling)."
        ),
    },
    {
        "id": "pos-acquire-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the contended branch first and swap the two arms. Same
        # value on every input (De Morgan on a two-point domain); the frozen
        # `cases outcome <;> simp_all` script closes it unchanged.
        "module": _acq_impl(
            "    if outcome = LockOutcome.contended then\n"
            "      return false\n"
            "    else\n"
            "      return true"),
        "rationale": (
            "guarding on `contended` and swapping the arms yields the identical "
            "boolean on both outcomes (`contended` ↔ `false`, otherwise `true`), "
            "so the ensures holds; a correct branch-reorder must verify, else "
            "SPEC-TOO-STRONG on branch order. The frozen `cases outcome <;> "
            "simp_all [acquiredOk]` proof closes it unchanged."
        ),
    },
    {
        "id": "pos-release-named-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the success boolean to a typed local, then return it
        # (instead of the bare `return true`). Same observable value; the frozen
        # `loom_solve` closes it.
        "module": _rel_impl(
            "    let ok : Bool := true\n"
            "    return ok"),
        "rationale": (
            "binding the reported success to a typed local `ok` before returning "
            "it leaves the returned value `true` unchanged, so the ensures "
            "`out = true` still discharges; a correct reshape must verify, else "
            "SPEC-TOO-STRONG on release (over-fit to the single-literal return)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — neither method carries a `require` clause (the
    # pre-conditions regions are empty), so the sibling's "a normal input
    # satisfies the precondition" probe is degenerate here (every input is
    # in-domain). The residual admissibility risk on a total-domain spec is that
    # the post-image is DEGENERATE — a `decide`-constant that reads exactly like
    # a spec every impl meets. This case discharges an in-region assert pinning
    # that `acquiredOk` genuinely DISTINGUISHES its two outcomes (`succeeded` ↦
    # true, `contended` ↦ false), so the decision is non-trivial. The rest of
    # the impl is kept verbatim so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-acquire-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _acq_impl(
            "    assert (with_name_prefix `assert\n"
            "      (acquiredOk LockOutcome.succeeded = true ∧\n"
            "       acquiredOk LockOutcome.contended = false))\n"
            "    if outcome = LockOutcome.succeeded then\n"
            "      return true\n"
            "    else\n"
            "      return false"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate: the decision "
            "`acquiredOk` really distinguishes the two outcomes it composes — a "
            "normal completion reports `true`, a non-blocking contention reports "
            "`false`. The in-region assert must discharge (else a constant "
            "decision would read as trivially met); the impl is kept verbatim so "
            "the ensures still discharges too. The nagini sibling's admissibility "
            "control likewise confirmed the success-path fact (available is True) "
            "and the contention-path fact (available is False) are both "
            "establishable."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete `outcome` by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-acquire-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-patch behaviour: report failure regardless of outcome.
        # (Pre-patch read `ret == 0` off the primitive's return value; since a
        # granted acquisition yields the no-value sentinel — modeled by the
        # `succeeded` outcome, mapping.md §2 — that comparison was always false,
        # so a successful acquisition was reported as failure.)
        "module": _acq_impl("    return false"),
        "refinement": (
            "this IS the pre-patch behaviour: a granted acquisition is reported as "
            "failure. Its faithful real counterpart is the unchanged repo, under "
            "which `test_exclusive_lock` / `test_shared_lock` assert "
            "`assertIs(lock(f1, LOCK_EX), True)` on a successful acquisition — an "
            "always-False helper returns False there, so the assertion fails and "
            "the patch does NOT resolve. This is the headline bug the issue files."
        ),
        "rationale": (
            "REJECT from `out = acquiredOk outcome`: on `outcome = succeeded` the "
            "post-image demands `true` (a normal completion is reported as "
            "acquired) but the rival returns `false`. If it verified => "
            "SPEC-TOO-WEAK (the always-False regression would go unnoticed). "
            "Refuted at `succeeded`."
        ),
        "witness": _acq_witness("LockOutcome.succeeded"),
    },
    {
        "id": "weak-acquire-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: report success regardless of outcome — a non-blocking
        # contention is wrongly reported as an acquired lock.
        "module": _acq_impl("    return true"),
        "refinement": (
            "always reporting success is what a helper that swallowed the "
            "contention signal would do — it reports an acquired lock even when a "
            "non-blocking request found the resource already held. "
            "`test_exclusive_lock` asserts `assertIs(lock(f2, LOCK_EX|LOCK_NB), "
            "False)` on that contended path; an always-True helper returns True "
            "there, so the assertion fails and the patch does NOT resolve. Anyone "
            "using LOCK_NB needs the False return to know they did NOT get the "
            "lock — exactly the behaviour the issue demands."
        ),
        "rationale": (
            "REJECT from `out = acquiredOk outcome`: on `outcome = contended` the "
            "post-image demands `false` (a non-blocking contention is reported as "
            "NOT acquired) but the rival returns `true`. If it verified => "
            "SPEC-TOO-WEAK (the contention outcome would be unpinned). Refuted at "
            "`contended` — the outcome value the always-false witness does not "
            "probe (so the sole binder is varied across both rivals)."
        ),
        "witness": _acq_witness("LockOutcome.contended"),
    },
    {
        "id": "weak-acquire-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Inversion: report a normal completion (acquired) as False and a
        # contention (not acquired) as True — the opposite of the faithful
        # translation.
        "module": _acq_impl(
            "    if outcome = LockOutcome.succeeded then\n"
            "      return false\n"
            "    else\n"
            "      return true"),
        "refinement": (
            "a real patch that inverted the two outcomes reports a successful "
            "acquisition as False and a contention as True — inverting the "
            "contract the issue demands ('a normal completion must never be "
            "reported as failure'). `test_exclusive_lock` asserts True for the "
            "success and False for the contention; an inverted helper fails both, "
            "so the patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = acquiredOk outcome`: the rival returns the "
            "negation of `acquiredOk outcome` on every input. Refuted at "
            "`contended`, where the post-image demands `false` but the inversion "
            "returns `true` (it also diverges at `succeeded`; both points refute "
            "it). Distinct rival from the constant always-true — it agrees with "
            "gold on NEITHER point, whereas each constant agrees on one. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _acq_witness("LockOutcome.contended"),
    },
    {
        "id": "weak-release-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # The release sibling of the pre-patch bug: report failure on a
        # successful release (`ret == 0` was always False since the release
        # yields the no-value sentinel).
        "module": _rel_impl("    return false"),
        "refinement": (
            "this IS the pre-patch release behaviour: a successful release is "
            "reported as failure. Its faithful real counterpart is the unchanged "
            "repo, under which `test_exclusive_lock` / `test_shared_lock` assert "
            "`assertIs(unlock(f1), True)`; an always-False release returns False "
            "there, so the assertion fails and the patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = true`: the constant `false` cannot satisfy the "
            "release post-image (a held release must report a definite `true`). "
            "If it verified => SPEC-TOO-WEAK (the always-False release regression "
            "would go unnoticed). `releaseLock` takes no input, so the single "
            "point is structural, not a coverage gap."
        ),
        "witness": _REL_WITNESS,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus 2 AXIOM_TESTS, over TWO
# helpers `acquire(available: bool)` / `release()` whose postconditions are
# grounded in the argument/literal AND in a body-less capability-token predicate
# (`lock_held()` / `lock_freed()`) closing the runtime-EFFECT flank, backed by
# two A-consumed axioms over `fcntl.flock`. THIS bundle models only the purely-
# functional core the fix turns on: the outcome→boolean translation, with the
# primitive's outcome taken directly as the input `LockOutcome` (mapping.md §2)
# and NO axiomatized callee (mapping.md §3, G-AX skip). Every nagini case is
# accounted for below.
#
#   nagini case                          -> here                          disposition
#   -----------------------------------------------------------------------------
#   pos-control-acquire-single-exit      -> pos-acquire-direct-pure       PORTED (reshaped)
#                                           + pos-acquire-negated-guard    ADDED reshape
#   pos-control-release-local            -> pos-release-named-local       PORTED
#   admissibility-acquire-indomain       -> admiss-acquire-nondegenerate  RE-AIMED
#   control-flow-effect-acquire-noop     -> (value facet: the always-*/   EFFECT FACET
#                                            inverted rivals)                NO COUNTERPART
#   control-flow-effect-release-noop     -> (none)                        NO COUNTERPART
#   inverted-value-acquire               -> weak-acquire-inverted         PORTED
#   always-false-acquire-prepatch        -> weak-acquire-always-false     PORTED
#   always-false-release-prepatch        -> weak-release-always-false     PORTED
#   (no sibling)                         -> weak-acquire-always-true      ADDED (binder cov.)
#   AXIOM_TESTS (2)                      -> (none)                        DROPPED (G-AX lane)
#
# 4 ported, 1 re-aimed, 2 reshape positives (1 added), 1 binder-coverage rival
# added; the effect-token no-op class has no counterpart; AXIOM_TESTS dropped.
#
# PORTED (4): the two prepatch always-False rivals and the inverted-value rival
#   carry across intact — only the carrier changes from a returned bool derived
#   from the primitive's control-flow signal to a returned Bool derived from the
#   `LockOutcome` input. weak-acquire-always-false / weak-release-always-false
#   are the exact pre-patch behaviours (model_prepatch.py / model_prepatch_2.py),
#   each carrying its refinement (the unchanged repo fails the True-assertion the
#   F2P tests now demand). weak-acquire-inverted ports the inverted-value rival.
# RE-AIMED (admissibility-acquire-indomain -> admiss-acquire-nondegenerate): the
#   nagini admissibility control asserted the success-path fact (available is
#   True) and contention-path fact (available is False) are establishable at the
#   primitive call site. Neither method here has a precondition or a call site to
#   admit, so that probe is degenerate; it is re-aimed at the residual
#   total-domain risk — a DEGENERATE (constant) post-image — via an in-region
#   assert that `acquiredOk` genuinely distinguishes its two outcomes.
# ADDED (1 reshape + 1 rival): pos-acquire-negated-guard is a second cheap correct
#   reshape (branch-reorder) exercising the frozen `cases outcome` proof.
#   weak-acquire-always-true has no nagini sibling because nagini's acquire echoes
#   its `available` argument (a rival that returns the wrong constant on the
#   contended path was folded into the no-op/echo class there); on this carrier
#   the contended outcome is an explicit input value, so the always-true rival
#   pins the `false`-side of the decision — moving the sole binder `outcome` to
#   `contended`, the value no other reject probes on its own.
# NO COUNTERPART (the two control-flow-effect no-ops): the nagini no-op rivals
#   (`return available` / `return True` WITHOUT invoking the primitive) attack the
#   runtime-EFFECT flank — the side-effect of actually taking/releasing the OS
#   lock, which nagini's abstraction observes via the capability token. This
#   bundle does not model that side-effect: the primitive's outcome is a GIVEN
#   input, not a call the impl elects to make or skip, so there is no
#   "return-without-invoking" move to make. The VALUE facet of those no-ops
#   (does the reported boolean match the real outcome?) DOES survive and is the
#   ordinary wrong-value surface, attacked by always-false / always-true /
#   inverted. Their EFFECT facet is an irreversible side effect with no value
#   footprint (spec_guide directive 9) — out of this fragment and deliberately
#   unmodeled, so no reject case is written for it and none is faked. Note the
#   release no-op `return True` is, on this carrier, definitionally IDENTICAL to
#   the frozen gold release (`return true`): there is nothing wrong to reject.
# FRAME / PERMISSION-MUTATION: VACUOUS. Referentially-transparent backend, no
#   `mut` binder, no heap, no aliasing, no permission system. The nagini sibling
#   itself records this class inapplicable (`has_readonly_input = False`; acquire
#   takes a plain bool, release no parameters). No substitute is fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# AXIOM_TESTS (2 dropped): the nagini axiom lane probes `primitive_lock` /
#   `primitive_release` over the real `fcntl.flock`. This carrier axiomatizes no
#   callee (mapping.md §3: the callee is unchanged; the outcome↔LockOutcome
#   correspondence is an R-refinement validated by G-CONF, and G-AX is skip), so
#   there is nothing there to probe. The axiom lane is G-AX's job and this gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE of the reject witnesses.
#   acquireLock's sole binder `outcome` is varied across BOTH values: `succeeded`
#     (weak-acquire-always-false) and `contended` (weak-acquire-always-true,
#     weak-acquire-inverted). So the two-point post-image is attacked at each
#     point — a rival mishandling only one outcome could not verify unnoticed.
#   releaseLock takes no input; its single witness point is structural (there is
#     no binder to vary), and the sole clause `out = true` is attacked by
#     weak-release-always-false.
#   Every independent top-level obligation is both DEFENDED (>=1 verify) and
#     ATTACKED (>=1 reject): acquireLock's `out = acquiredOk outcome` by two
#     positives + the admissibility assert vs. three rivals; releaseLock's
#     `out = true` by one positive vs. one rival. pts = 3 distinct input points
#     (succeeded, contended, the empty release input).
AXIOM_TESTS = []
