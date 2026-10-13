"""properties.py — G-PBT falsification battery for django__django-16569 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct deletionFieldDecision`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation, checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted decision over four read-only scalar inputs):

  deletionFieldDecision (enabled offerOnExtra : Bool)
                        (position : Option Nat) (initialCount : Nat)
    return (out : Except ControlErr Bool)
    ensures out = shouldOfferDeletion enabled offerOnExtra position initialCount   -- (C1)
    ensures ∃ b, out = Except.ok b                                                 -- (C2)
    ensures position = none → out = Except.ok (enabled && offerOnExtra)            -- (C3)

The modeled behaviour is the per-row decision WHETHER a removal control should be
offered on one row of a collection of repeated rows. The control is offered
exactly when it is enabled AND (it is also offered on surplus rows OR the row's
ordinal position lies strictly within the pre-populated rows). An ABSENT position
contributes nothing to the position test and — crucially — must NOT abandon the
decision: the decision always produces a verdict (``Except.ok``), never the
undefined-comparison error. ``shouldOfferDeletion`` / ``positionWithinInitial``
are grounded pure functions of the four inputs (no opaque answer-key), so pinning
``out`` to them is grounded, not an echo.

  Load-bearing clauses:
    (C1) out = shouldOfferDeletion …  — the EXACT decision as a total function of
         all four inputs. Pins: whether ``enabled`` gates the whole decision,
         whether ``offerOnExtra`` short-circuits the position test, and the
         STRICT ``<`` boundary of the position test.
    (C2) ∃ b, out = Except.ok b       — every input yields a VERDICT, never the
         undefined-comparison error (the definiteness/total facet).
    (C3) position = none → out = Except.ok (enabled && offerOnExtra)  — the
         ABSENT-position reduction: with no position to compare, the decision
         reduces to "enabled and offered-on-surplus", NOT to the error and NOT
         to a spurious ``true``. This is the exact facet the gold fix turns on.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts a RICHER routine over the same four scalars plus an ordering flag,
which mutates a row object in place and decides THREE independent flags: the
ordering-control presence (its clause O), the ordering-prefill (its clause P),
AND the removal-control presence (its clause D). This bundle models ONLY the
purely-functional core the behaviour under spec turns on — the removal-control
DECISION (nagini clause D) — as a pure
function of four scalar inputs returning ``Except ControlErr Bool``. The
ordering-control behaviour (nagini O/P) is a separate, unchanged decision the
gold patch does not touch and this bundle does not model (mapping.md §1).

Consequently the nagini rivals attached to the ORDERING clauses (O and P) have
NO counterpart on this carrier: there is no ordering flag to abuse, no prefill
sub-domain to special-case. Those are reported as omissions in the footer, not
faked. Carrier narrowing, not a gap in coverage of what IS modeled.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. Lean and Velvet are referentially transparent:
    no heap, no aliasing, no fractional permission. Every input is a read-only
    scalar (none is ``mut``), and the decision is a returned value. The nagini
    sibling ALSO records this class as inapplicable (its only object input is
    held at FULL permission because it IS the mutated output; every other param
    is a pass-by-value scalar). No substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region is empty;
    ``shouldOfferDeletion`` and ``positionWithinInitial`` are fully-unfolded pure
    functions of the inputs, not an opaque answer-key. An impl that "echoes"
    them is computing the correct value (see pos-direct). The nagini sibling
    reached the same conclusion (its (P)/(D) are pinned to the @Pure
    ``at_initial_position``, fully unfolded).
  * PARTIAL-DOMAIN / VALUE-BOUNDARY / CONTROL-DECISION — APPLY to the deletion
    decision and are the whole reject surface below: the absent-position bug
    (C2/C3), treating an absent position as initial (C3), the ``<``-vs-``<=``
    boundary (C1), dropping the surplus-rows disjunct (C1 on ``offerOnExtra``),
    dropping the enabled gate (C1 on ``enabled``), and dropping the
    position-within test (C1 on ``position``).

DIVERGENCE LANE — this bundle runs under
``set_option loom.semantics.termination "total"`` (Solution.lean line 4), NOT
``"partial"``, so the disposition is neither "vacuous class" nor the old
``partial`` "the spec admits it": it is UNSHIPPABLE-BY-TOOLING, demonstrated
below. The frozen impl is straight-line (no loop, no self-call), so a divergence
rival has to INTRODUCE a loop, and under ``"total"`` there are exactly two shapes
it can take. Both were built (audit block at the footer records the exit codes):

  * NO decreasing measure — the verifier does reject it, which is what makes the
    class look shippable. But it is rejected by a LINTER error raised on the
    ``method`` itself (``Decreasing annotations are required in total correctness
    semantics``), not inside the ``prove_correct`` block. ``witness_file`` strips
    only the proof, so that error survives into the witness build and the witness
    CANNOT elaborate against the rival (exit 1 where the gate requires 0). The
    gate would record ``witness-unproven`` => MALFORMED-TESTS, i.e. a gate ERROR,
    not a passing reject case. Shipping it would break the battery, so it is not
    shipped — a TOOLING reason, machine-checked, not "the proof was hard".
  * WITH a measure that does not decrease (``decreasing spin`` while
    ``spin := spin + 1``) is also REJECTED (exit 1), on the measure's OWN goal
    rather than on a missing annotation: ``unsolved goals case
    «decreasing_1: spin» ... ⊢ spin + 1 < spin``. A constant measure behaves the
    same way (``decreasing (0 : Nat)`` leaves ``⊢ 0 < 0``). An earlier revision of
    this lane recorded this shape as VERIFYING at exit 0 and escalated it as a
    corpus-wide spec hole; that is RETRACTED here on re-measurement.

So no divergence reject case is shippable on this carrier, and no spec hole is
escalated from it either. Both shapes are rejected, and the mechanism is in the
frozen header: ``set_option loom.semantics.termination "total"`` itself opens the
``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``), the file
opens that scope explicitly as well, and
``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and emits
``⌜measure b' < measure b⌝`` as a goal the proof must discharge. Only the
``PartialCorrectness`` twin takes a measure and drops it. The first shape cannot
carry a witness (its own file will not compile); the second is an ordinary spec
rejection whose attribution is the termination obligation, not the deletion
decision this bundle defends, and its own witness build also cannot elaborate
past the unsolved descent goal.

WITNESS MACHINERY. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``deletionFieldDecisionTester enabled offerOnExtra position initialCount``): the
value ``… = false`` says the extracted program's result violates the method's
postcondition at that concrete input. Checked in a file whose ``prove_correct``
block has been stripped, so no tactic script can mask the verdict. There is no
``require`` clause, so every input reaches the postcondition. The return type
``Except ControlErr Bool`` has no synthesizable ``DecidableEq``/existential
``Decidable`` instance in scope, so each witness FIRST supplies two computable
instances (structural ``match``, so the kernel reduces them for ``decide``);
these are declared INSIDE the witness snippet, hence present in BOTH the rival
and the gold build by construction (they are the witness's own vocabulary, not
the variant's). Each reject witness fires at a DISTINCT concrete input, chosen so
the rival's decision disagrees with the frozen decision there (machine-checked
both halves: elaborates against the rival, fails on gold).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the decision is a
language-level boolean expression modeled deeply, no foreign callee consumed —
mapping.md §3). There is no axiom-soundness obligation, and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16569"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl region (verbatim from Solution.lean). Every variant replaces text
# lying WHOLLY inside the single `-- impl-start`/`-- impl-end` region, so
# same_spec holds by construction. The anchor is unique in the file (asserted by
# _swap at load).
# ---------------------------------------------------------------------------
_IMPL_OLD = """    let mut decision : Bool := false
    if enabled = true then
      if offerOnExtra = true then
        decision := true
      else
        decision := positionWithinInitial position initialCount
    return Except.ok decision"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1, "impl region drift"

# The frozen proof obligation. Some reshapes retune the tactic body; the
# `prove_correct deletionFieldDecision by` HEADER (and the method statement) stay
# byte-identical, so the obligation survives.
_PROOF_OLD = """prove_correct deletionFieldDecision by
  loom_solve <;>
    simp_all [shouldOfferDeletion, positionWithinInitial]"""

assert _PROOF_OLD in _BASE and _BASE.count(_PROOF_OLD) == 1, "proof region drift"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced."""
    return _swap(_BASE, _IMPL_OLD, new_body)


# ---------------------------------------------------------------------------
# Witness preamble. The method returns `Except ControlErr Bool`, whose equality
# and the existential `∃ b, out = Except.ok b` have no instance in scope; both are
# supplied here as COMPUTABLE instances (structural `match`, not tactic-built), so
# the kernel reduces the derived tester and `decide` can evaluate it. These
# instances are the witness's OWN declarations — appended to both the rival and
# the gold build, so they exist on both sides and reference only spec-region names
# (`ControlErr`, `Except`). The tester directives extract the method to an
# executable and derive `deletionFieldDecisionTester`.
# ---------------------------------------------------------------------------
_WITNESS_PREAMBLE = r"""instance instDecEqExc : DecidableEq (Except ControlErr Bool) := fun a b =>
  match a, b with
  | .ok x, .ok y => if h : x = y then isTrue (by rw [h]) else isFalse (by simp [h])
  | .error .positionComparisonUndefined, .error .positionComparisonUndefined => isTrue rfl
  | .ok _, .error _ => isFalse (by simp)
  | .error _, .ok _ => isFalse (by simp)

instance instDecExists (out : Except ControlErr Bool) : Decidable (∃ b, out = Except.ok b) :=
  match out with
  | .ok v => isTrue ⟨v, rfl⟩
  | .error _ => isFalse (by rintro ⟨b, h⟩; exact Except.noConfusion h)

extract_program_for deletionFieldDecision
prove_precondition_decidable_for deletionFieldDecision
prove_postcondition_decidable_for deletionFieldDecision
derive_tester_for deletionFieldDecision
"""


def _witness(call):
    """A refutation witness firing at one concrete input `call` (the four tester
    arguments). Asserts the extracted program VIOLATES the postcondition there."""
    return (_WITNESS_PREAMBLE
            + f"\nexample : deletionFieldDecisionTester {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. The decision is point-wise over four scalars (no loop /
    # fold), so no induction is needed and each reproof stays within the frozen
    # `loom_solve` script.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # Return the grounded spec decision directly. `shouldOfferDeletion` is a
        # total, fully-unfolded function of the four inputs (not an opaque
        # oracle), so returning it is the honest cheapest CORRECT impl, not an
        # echo — any WRONG constant/branch would fail C1.
        "module": _impl(
            "    return shouldOfferDeletion enabled offerOnExtra position initialCount"),
        "rationale": "C1 pins `out` to the grounded total function "
                     "`shouldOfferDeletion` of all four inputs, so directly "
                     "returning it is a fully-correct reshape that MUST verify "
                     "(else SPEC-TOO-STRONG, over-fit to the mutable-local "
                     "spelling). Maps nagini pos-control-flag-fold (collapse the "
                     "decision into its boolean and return it).",
    },
    {
        "id": "pos-collapse-branch",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the nested if into a single guarded boolean assignment: when
        # enabled, the decision is `offerOnExtra || positionWithinInitial …`.
        # Semantically identical to the frozen nested short-circuit; the frozen
        # tactic still closes the byte-identical obligation.
        "module": _impl(
            "    let mut decision : Bool := false\n"
            "    if enabled = true then\n"
            "      decision := offerOnExtra || positionWithinInitial position initialCount\n"
            "    return Except.ok decision"),
        "rationale": "the nested `if offerOnExtra then true else P` short-circuit "
                     "is definitionally `offerOnExtra || P`, so collapsing it "
                     "leaves the decision identical on every input; a "
                     "structurally-different correct reshape MUST verify (else "
                     "SPEC-TOO-STRONG, over-fit to the gold branch NESTING). Maps "
                     "nagini pos-control-helper-reorder (branch reshape into a "
                     "single guarded form).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause (nothing can be
    # PRECOND-TOO-STRONG), so the usual "a normal input satisfies the
    # precondition" probe is vacuous. The residual risk on a total domain is a
    # DEGENERATE/UNSATISFIABLE post-image at the F2P-shaped input. This case
    # discharges an in-region `assert` that the canonical bug configuration
    # (enabled, NOT offered on surplus, ABSENT position) classifies as the
    # NO-removal-control verdict `Except.ok false` — exactly what the failing
    # test observes on the standalone template row. The assert is LIVE (claiming
    # any other verdict leaves an unsolved goal — verified out-of-band); the
    # frozen body follows it so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-empty-form-config",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (shouldOfferDeletion true false none 0 = Except.ok false))\n"
            + _IMPL_OLD),
        "rationale": "the F2P-shaped configuration (enabled, not offered on "
                     "surplus rows, ABSENT position) classifies as the "
                     "no-removal-control verdict `Except.ok false` — the exact "
                     "behaviour the failing test exercises on the standalone "
                     "template row, and a definite VERDICT (not the "
                     "undefined-comparison error). The in-region assert is live (a "
                     "wrong claimed verdict leaves an unsolved goal) and the frozen "
                     "body keeps the ensures obligation intact, so the module "
                     "verifies; this witnesses the spec ADMITS the modeled F2P "
                     "behaviour rather than being vacuous or over-strong there. "
                     "Maps nagini admiss-empty-form.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "uniq-drop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Drop the absent-position guard: when enabled and not offered
        # on surplus rows, attempt the order comparison directly, yielding the
        # undefined-comparison error for an absent position. Violates C2 (every
        # input yields a verdict) and C3 (absent position reduces to a verdict).
        "module": _impl(
            "    let mut decision : Except ControlErr Bool := Except.ok false\n"
            "    if enabled = true then\n"
            "      if offerOnExtra = true then\n"
            "        decision := Except.ok true\n"
            "      else\n"
            "        decision := match position with\n"
            "          | some i => Except.ok (decide (i < initialCount))\n"
            "          | none   => Except.error ControlErr.positionComparisonUndefined\n"
            "    return decision"),
        "refinement": "this is the pre-change behaviour: the order comparison is "
                      "attempted without first checking a position is present. Its "
                      "faithful real patch is the unpatched repo, under which the "
                      "standalone template row (removal enabled, not offered on "
                      "surplus, absent position) raises at the comparison and the "
                      "row cannot even be rendered; the failing test never reaches "
                      "its assertion — so it would NOT resolve. This is the exact "
                      "defect the fix corrects.",
        "rationale": "REJECT from C2/C3: for an absent position the rival yields "
                     "the undefined-comparison ERROR, but C2 requires every input "
                     "to yield a verdict and C3 requires the absent-position case "
                     "to reduce to `Except.ok (enabled && offerOnExtra)` "
                     "(= `Except.ok false` here). If it verified => SPEC-TOO-WEAK "
                     "(the reported bug would go unnoticed). Maps nagini "
                     "uniq-drop-guard.",
        "witness": _witness("true false none 0"),
    },
    {
        "id": "uniq-none-counts-initial",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on C3. None-safe (short-circuits before `<`), so it can
        # verify on most inputs — but treats an ABSENT position as if it lay
        # within the pre-populated rows, offering the control there.
        "module": _impl(
            "    let mut decision : Bool := false\n"
            "    if enabled = true then\n"
            "      if offerOnExtra = true then\n"
            "        decision := true\n"
            "      else\n"
            "        decision := match position with\n"
            "          | some i => decide (i < initialCount)\n"
            "          | none   => true\n"
            "    return Except.ok decision"),
        "refinement": "a real patch whose guard reads `offered-on-surplus OR "
                      "absent-position OR within-initial` would give the "
                      "standalone template row a removal control; the failing test "
                      "asserts that row carries NO removal control, so it FAILS — "
                      "does NOT resolve.",
        "rationale": "REJECT from C1/C3: for an absent position C3 requires the "
                     "decision to reduce to `enabled && offerOnExtra` (FALSE when "
                     "surplus rows are not offered), but this rival sets it TRUE. "
                     "Distinct from uniq-drop-guard: that one produces the error "
                     "(C2 facet), this one produces a spurious TRUE verdict (the "
                     "wrong-value facet of the absent case). Maps nagini "
                     "uniq-none-counts-initial.",
        "witness": _witness("true false none 3"),
    },
    {
        "id": "uniq-boundary-le",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE / boundary. Use `<=` instead of the strict `<` in the position
        # test. None-safe, so it can verify on most inputs, but at the boundary
        # position == initialCount it offers the control when C1's strict test
        # forbids it.
        "module": _impl(
            "    let mut decision : Bool := false\n"
            "    if enabled = true then\n"
            "      if offerOnExtra = true then\n"
            "        decision := true\n"
            "      else\n"
            "        decision := match position with\n"
            "          | some i => decide (i <= initialCount)\n"
            "          | none   => false\n"
            "    return Except.ok decision"),
        "refinement": "a real counterpart comparing the position with `<=` "
                      "against the pre-populated count gives the "
                      "first surplus row (position == the pre-populated count) a "
                      "removal control when the control is enabled and NOT offered "
                      "on surplus rows — exactly what the failing test (which "
                      "disables offering the control on surplus rows) forbids at "
                      "the initial/surplus boundary; does NOT resolve.",
        "rationale": "REJECT from C1: off-by-one at the boundary position == "
                     "initialCount — C1's position test is STRICT `<` (false "
                     "there) but the rival's `<=` is true, so it offers the "
                     "control where the decision forbids it. Attacks the position "
                     "VALUE binder at the boundary. Maps nagini "
                     "uniq-delete-le-boundary.",
        "witness": _witness("true false (some 2) 2"),
    },
    {
        "id": "uniq-ignore-offer-on-extra",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL/decision attack. Drop the `offerOnExtra` disjunct entirely:
        # offer the control iff enabled and within the pre-populated rows.
        # Correct on the bug config (absent position => no control) but WRONG when
        # offering on surplus rows is enabled for a surplus/absent row.
        "module": _impl(
            "    let mut decision : Bool := false\n"
            "    if enabled = true then\n"
            "      decision := positionWithinInitial position initialCount\n"
            "    return Except.ok decision"),
        "refinement": "a real counterpart dropping the offered-on-surplus "
                      "disjunct removes the removal control from surplus rows even "
                      "when it is explicitly enabled for them; the sibling "
                      "regression test asserting the control IS present on surplus "
                      "rows under that configuration would fail — does NOT resolve.",
        "rationale": "REJECT from C1: when `offerOnExtra` is true for a "
                     "surplus/positionless row, C1 requires the control to be "
                     "offered (`enabled && (true || …)`), but this rival ignores "
                     "`offerOnExtra` and gives FALSE. Attacks the `offerOnExtra` "
                     "binder. Maps nagini uniq-delete-ignore-extra.",
        "witness": _witness("true true (some 5) 0"),
    },
    {
        "id": "uniq-ignore-enabled",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL/decision attack on the OUTER gate. Drop the `enabled` guard:
        # offer the control whenever offered-on-surplus or within the
        # pre-populated rows, regardless of whether the control is enabled at all.
        "module": _impl(
            "    let decision : Bool := offerOnExtra || positionWithinInitial position initialCount\n"
            "    return Except.ok decision"),
        "refinement": "a real counterpart dropping the control-enabled outer "
                      "gate would attach the removal control to collections where "
                      "it was never enabled; every test that omits the removal "
                      "control (the default) would suddenly find it present — does "
                      "NOT resolve.",
        "rationale": "REJECT from C1: the whole decision is gated by `enabled` "
                     "(`enabled && …`), so when the control is DISABLED C1 "
                     "requires FALSE regardless of the other inputs, but this "
                     "rival offers it whenever surplus rows are offered. Attacks "
                     "the `enabled` binder — a binder no other rival's witness "
                     "sets false. No direct nagini counterpart (nagini's D-rivals "
                     "all keep the can_delete gate); ADDED for enabled-binder "
                     "coverage.",
        "witness": _witness("false true none 0"),
    },
    {
        "id": "uniq-ignore-position",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN attack that DROPS the position test entirely: offer the
        # control iff enabled and offered-on-surplus. Correct on the bug config
        # but WRONG for a pre-populated row that is NOT offered on surplus.
        "module": _impl(
            "    let mut decision : Bool := false\n"
            "    if enabled = true then\n"
            "      decision := offerOnExtra\n"
            "    return Except.ok decision"),
        "refinement": "a real counterpart dropping the guarded position-within-"
                      "the-pre-populated-count disjunct removes the removal control "
                      "from PRE-POPULATED rows when it is enabled but not offered "
                      "on surplus rows; those rows must keep the control, so a "
                      "regression test on pre-populated forms fails — does NOT "
                      "resolve.",
        "rationale": "REJECT from C1: for a pre-populated row (position within the "
                     "count) with surplus rows NOT offered, C1 requires the "
                     "control (`enabled && (false || (pos < count))` = TRUE), but "
                     "this rival ignores the position test and gives FALSE. "
                     "Attacks the `position`/`initialCount` binders. No direct "
                     "nagini D-rival; ADDED for position-test coverage in the "
                     "surplus-off sub-domain.",
        "witness": _witness("true false (some 0) 1"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals; AXIOM_TESTS = 1 containment
# probe) over a richer in-place row mutator, whose
# postcondition has THREE clauses over TWO independent decisions: (O)/(P) the
# ordering-control presence and prefill, and (D) the removal-control presence.
# THIS bundle models ONLY the purely-functional core the gold fix turns on — the
# removal-control DECISION (nagini clause D) — as `deletionFieldDecision`
# returning `Except ControlErr Bool`. The ordering-control behaviour (O/P) is a
# separate unchanged decision the gold patch does not touch and this bundle does
# not model (mapping.md §1). Every nagini case is accounted for below.
#
#   nagini case                -> here
#   -----------------------------------------------------------------------
#   pos-control-helper-reorder -> pos-collapse-branch          RE-SHAPED
#   pos-control-flag-fold      -> pos-direct                   RE-EXPRESSED
#   admiss-empty-form          -> admiss-empty-form-config     RE-AIMED
#   uniq-drop-guard            -> uniq-drop-guard              PORTED (C2/C3)
#   uniq-none-counts-initial   -> uniq-none-counts-initial     PORTED (C3)
#   uniq-delete-le-boundary    -> uniq-boundary-le             PORTED (C1)
#   uniq-delete-ignore-extra   -> uniq-ignore-offer-on-extra   PORTED (C1)
#   uniq-prefill-always        -> (none)                       NO COUNTERPART (O/P)
#   uniq-order-iff-prefill     -> (none)                       NO COUNTERPART (O/P)
#   uniq-selfrec-diverge       -> (none)                       UNSHIPPABLE (tooling)
#                                 (+ uniq-ignore-enabled       ADDED, enabled binder)
#                                 (+ uniq-ignore-position      ADDED, position binder)
#
# 4 uniqueness rivals ported, 2 positives re-shaped/re-expressed, 1 admissibility
# re-aimed, 2 no-counterpart (ordering), 1 divergence case unshippable by tooling
# under `total` semantics; 2 rivals added for binder coverage.
#
# PORTED (4): the DELETION-decision rivals carry across intact — only the carrier
#   changes from an in-place form mutation to a returned `Except ControlErr Bool`
#   over four scalars. uniq-drop-guard is THE BUG (attempt the order comparison
#   with no position present): on nagini it fails the `<` precondition, here it
#   returns the undefined-comparison error, violating C2/C3. uniq-none-counts-
#   initial treats an absent position as initial (violates C3). uniq-delete-le-
#   boundary uses `<=` at the initial/surplus boundary (violates C1's strict
#   `<`). uniq-delete-ignore-extra drops the offer-on-surplus disjunct (violates
#   C1 on offerOnExtra). Each carries its nagini refinement argument (the same
#   F2P/sibling test fails for the faithful real patch).
# RE-EXPRESSED (pos-control-flag-fold -> pos-direct): the nagini positive
#   precomputed each flag's boolean then assigned it; on this carrier the decision
#   IS a single grounded boolean, so the analogue is returning
#   `shouldOfferDeletion …` directly (a value PRODUCED by the grounded spec fn,
#   not echoed from an opaque oracle).
# RE-SHAPED (pos-control-helper-reorder -> pos-collapse-branch): the nagini
#   positive reordered the delete/order branches and dropped a redundant else;
#   this carrier has only the delete decision, so the cheapest correct reshape
#   collapses the nested short-circuit `if offerOnExtra then true else P` into the
#   definitionally-equal `offerOnExtra || P`.
# RE-AIMED (admiss-empty-form -> admiss-empty-form-config): the nagini
#   admissibility control built a fresh row object and asserted the precondition
#   for the positionless-row config. This method has no `require` clause, so that probe is
#   vacuous; it is re-aimed at the residual total-domain risk (a degenerate
#   post-image) via a live in-region assert that the same canonical config
#   (enabled, not offered on surplus, absent position) classifies as the definite
#   no-control verdict `Except.ok false`.
# NO COUNTERPART (2): uniq-prefill-always attacks the ordering-PREFILL clause (P)
#   and uniq-order-iff-prefill attacks the ordering-PRESENCE clause (O). Both
#   concern the ordering control, a separate decision the gold patch does not
#   touch and this bundle does not model (mapping.md §1: only the removal-control
#   decision is modeled). There is no ordering flag on this carrier to abuse.
#   Omitted because the modeled surface does not include that behaviour, NOT
#   because it was hard to prove.
# UNSHIPPABLE BY TOOLING (1): uniq-selfrec-diverge — a bare self-recursion,
#   rejected on nagini ONLY by an explicit MustTerminate(2) obligation. This
#   bundle reads `termination "total"` (NOT "partial" — an earlier revision of
#   this file asserted "partial" and was WRONG; corrected by the second audit,
#   which read Solution.lean line 4 and re-ran both shapes). Under "total" the two
#   available divergence shapes were built:
#     * measure-less loop  -> variant exit 1, but the failure is a LINTER error on
#       the `method` (`Decreasing annotations are required in total correctness
#       semantics`) that `witness_file` does NOT strip, so the witness build
#       against the RIVAL is exit 1 where the gate requires 0 => the gate would
#       record witness-unproven => MALFORMED-TESTS (a gate ERROR). Confirmed by
#       building the witness against that rival.
#     * `decreasing spin` with `spin := spin + 1` -> variant exit 1 as well, and on
#       the MEASURE's own goal: `unsolved goals case «decreasing_1: spin» ... |-
#       spin + 1 < spin`. A constant measure leaves `|- 0 < 0`. This RETRACTS the
#       second audit's reading, which recorded this shape at exit 0 (VERIFIES) and
#       inherited the corpus-wide "obligation accepts a non-decreasing measure"
#       hole for it. Re-measured with a real build, that hole does not exist here:
#       `set_option ... "total"` itself opens the `TotalCorrectness` scope (Loom
#       `MonadAlgebras/WP/Options.lean`), the frozen file opens it explicitly too,
#       and `TotalCorrectness.WPGen.forWithInvariantLoop` emits
#       `measure b' < measure b` where the `PartialCorrectness` twin would drop it.
#   Neither is a shippable reject case, so none is written — a TOOLING reason with
#   the error text, not "the proof was hard": the first shape's own file will not
#   compile, so no witness can elaborate against it, and the second is rejected on
#   the termination obligation rather than on the deletion decision, so its
#   rejection is not attributable to the postcondition a witness would state. No
#   `spec_holes` entry is filed. Independently bounded on this cell: the
#   wrong-ANSWER laundering that makes that class severe elsewhere is BLOCKED here
#   too. `done_with False` + bogus measure + a wrong return (both `Except.error …`
#   and `Except.ok true`) is REJECTED, exit 1, on the loop's own goal
#   `case «done_1: False» ... |- False` — the frozen contract has no `require`, so
#   nothing supplies the falsity the unreachable-exit trick needs.
# ADDED (2, binder coverage): uniq-ignore-enabled drops the outer `enabled` gate
#   (attacks the `enabled` binder — the only witness that sets it false), and
#   uniq-ignore-position drops the position test in the surplus-off sub-domain
#   (attacks the `position`/`initialCount` binders on a pre-populated row). Both
#   are real divergences with machine-checked witnesses, not fabricated wrongness;
#   they close binder coverage the four ported rivals left thin.
# FRAME-MUTATION: VACUOUS. Referentially-transparent backend, no `mut` binder, no
#   heap, no aliasing, no permission system. All four inputs are read-only scalars
#   and the decision is a returned value. The nagini sibling itself records this
#   class as inapplicable (its object input is FULL-permission because it IS the
#   output; every other param is pass-by-value). No substitute fabricated.
#
# BINDER / CLAUSE / POINT COVERAGE.
#   * enabled       — false at uniq-ignore-enabled; true elsewhere.        VARIED
#   * offerOnExtra  — true at uniq-ignore-offer-on-extra / uniq-ignore-
#                     enabled; false elsewhere.                            VARIED
#   * position      — none (drop-guard, none-counts-initial, ignore-enabled),
#                     some 0/2/5 (ignore-position, boundary-le, ignore-extra). VARIED
#   * initialCount  — 0/1/2/3 across the witnesses.                        VARIED
#   Clauses: C1 attacked by boundary-le / ignore-offer-on-extra /
#   ignore-enabled / ignore-position (and none-counts-initial); C2 by drop-guard;
#   C3 by drop-guard and none-counts-initial. All three defended by both
#   positives and the admissibility assert.
#   Distinct witness points (pts): 6 —
#     true false none 0 / true false none 3 / true false (some 2) 2 /
#     true true (some 5) 0 / false true none 0 / true false (some 0) 1.
#
# INDEPENDENT AUDIT (post-port, adversarial re-derivation; all builds re-run).
#   Statement integrity: every case's edit lies WHOLLY inside the impl region
#   (frozen lines 88-95 by difflib opcode), so all 9 modules carry a
#   byte-identical method statement, ensures triple and `prove_correct` header.
#   Witnesses re-derived from scratch, 12 builds: every rival exit 0, every gold
#   exit 1, and every gold failure is the STRONGEST form of semantic refutation —
#   `Tactic 'decide' proved that the proposition ... is false` (a completed kernel
#   evaluation), never a stuck reduction, unknown name or timeout. No witness
#   binds a hypothesis, so `consistency_probe` is None for all six (nothing to be
#   inconsistent) and no third build is owed.
#   Rival wrongness confirmed OBSERVABLY, not just syntactically: exhaustive
#   model-check over enabled/offerOnExtra x position in {none,0..5} x
#   initialCount in 0..4 gives each rival 5/5/5/25/45/10 disagreement points with
#   the frozen decision, and each witness fires AT one of them. No rival is
#   definitionally equal to gold, so no case is vacuous.
#   Clause attribution audited against the actual residual goals: drop-guard
#   leaves ensures_1+2+3 unsolved, none-counts-initial / ignore-offer-on-extra /
#   ignore-enabled leave ensures_1+3, boundary-le and ignore-position leave
#   ensures_3 — matching each rationale as written.
#   admiss assert LIVENESS machine-checked (the port claimed this out-of-band):
#   claiming `Except.ok true` or the undefined-comparison error at the same config
#   both leave `case admiss_1 ... |- False` (exit 1). The assert is load-bearing.
#   Attack D (SPEC-TOO-WEAK), 6 NEW wrong impls the battery lacks — Nat-truncated
#   `i <= initialCount - 1`, `&&`/`||` precedence dropping the enabled gate,
#   error-when-disabled, any-present-position-counts, a NEEDLE correct everywhere
#   but one point (i=7, count=3), and a role-swap of the two Bool binders: ALL SIX
#   REJECTED with residual goals naming the violated clause. No spec hole found.
#   Attack E (SPEC-TOO-STRONG), 5 NEW correct reshapes: outer-match-on-position,
#   offer-on-surplus-tested-first, early-return-negated-gate and a nested-ite
#   expression all VERIFY under the frozen tactic script (exit 0). The fifth,
#   `enabled && offerOnExtra || enabled && P` (and-over-or distributed), leaves the
#   pure boolean identity as an unsolved goal under the FROZEN script, but closes
#   immediately with `Bool.and_or_distrib_left` added, or with `cases enabled <;>
#   cases offerOnExtra` (both exit 0). That is tactic tuning — which variant_scope
#   expressly permits — not the spec rejecting a faithful impl: NOT a soundness
#   hole in the spec.
#   Repaired by the audit: the refinement/footer prose quoted the gold diff's added
#   guard verbatim and named patched repo symbols. properties.py SHIPS and G-LEAK
#   does not screen it, so the arguments are restated abstractly (same force, no
#   diff text, no patched symbol, no fix narration). No case's logic changed.
#
# SECOND INDEPENDENT AUDIT (adversarial re-derivation; 40 builds, all re-run from
# scratch through the gate's OWN `witness_file`, so the files are byte-identical to
# what the gate builds). Confirms the block above on the 9 cases and CORRECTS its
# divergence-lane claim.
#   Attack A (statement integrity) CONFIRMED independently: difflib opcodes against
#   the frozen file put every case's only edit inside impl lines 88-95 (frozen
#   impl-start=82, impl-end=95, prove_correct=97). No case touches the method
#   statement, the ensures triple, or the `prove_correct` header. --validate-only:
#   9/9 scope-ok.
#   Attack B (witness discrimination) RE-DERIVED, 12 builds: all 6 rivals exit 0,
#   all 6 gold exit 1, every gold error a COMPLETED kernel evaluation
#   (`Tactic `decide` proved that the proposition deletionFieldDecisionTester <pt>
#   = false is false`) naming the case's own input point. No stuck reduction, no
#   unknown identifier, no timeout. consistency_probe is None for all six
#   (`all_witness_head_binders` = [] — nothing bound), so no third build is owed.
#   Attack B' (FORGERY) RUN, 12 further builds — the check the block above did not
#   do. Flipping ONLY the claim (`= false` -> `= true`) inverts every exit code:
#   forged claim on GOLD exits 0 with EMPTY output (gold's verdict really is the
#   value the witness denies), and on the RIVAL exits 1 with `Tactic `decide`
#   proved that the proposition ... = true is false`. So each gold-side exit code
#   TRACKS the claim and carries information about it; none of the six is hollow.
#   Attack C (observably wrong, not merely reshaped) re-derived by exhaustive model
#   check over 140 inputs: disagreement counts 5/5/5/25/45/10 and each witness
#   fires AT a disagreement point. No rival is definitionally equal to gold.
#   Attack D re-run with 6 DIFFERENT wrong impls (role-swap of the two Bools,
#   `||` as the outer connective, Nat-truncated `i <= initialCount - 1`, a needle
#   wrong only at position 7 / count 3, error-when-disabled, any-present-position-
#   counts): ALL SIX REJECTED, exit 1, each on a named ensures goal. No spec hole.
#   Attack E re-run with 4 correct reshapes (outer `match` on position, early-return
#   negated gate, a nested-`ite` expression, and the distributed
#   `(enabled && offerOnExtra) || (enabled && P)`): the first three VERIFY under the
#   FROZEN tactic script; the distributed one needs one added rewrite
#   (`Bool.and_or_distrib_left`, or `cases enabled <;> cases offerOnExtra`) and then
#   verifies (exit 0 both ways). Tactic tuning inside the `prove_correct` body is
#   expressly in variant_scope, so this is NOT a SPEC-TOO-STRONG hole.
#   Admissibility liveness re-confirmed: claiming `Except.ok true` OR the
#   undefined-comparison error at the same config each leaves
#   `case «admiss_1: ...» ... |- False` (exit 1). The assert is load-bearing, so the
#   positive is not neutered.
#   CORRECTED (the one defect this audit found): the divergence-lane prose asserted
#   `termination "partial"` at Solution.lean line 4 and derived a "KNOWN SPEC HOLE,
#   the spec ADMITS the rival" disposition from it. Line 4 actually reads
#   "total" — the opposite setting, which inverts the disposition. Under F' a
#   `total` bundle that records this class as a `partial`-style admitted hole is
#   misdescribed, so both the header and footer entries were rebuilt from
#   (see the DIVERGENCE LANE section and the UNSHIPPABLE BY TOOLING footer entry).
#   Net: the class is unshippable here for a TOOLING reason (measure-less rival's
#   linter error survives `witness_file`, so the witness cannot elaborate against
#   the rival => gate ERROR), and the non-decreasing-measure rival verifies but is
#   the already-escalated corpus-wide toolchain hole, not a defect of this spec.
#   Newly bounded for this cell: the wrong-ANSWER laundering is BLOCKED —
#   `done_with False` + bogus measure + wrong return is rejected on `|- False`
#   (exit 1) for both a wrong `Except.error` and a wrong `Except.ok true`.
#   No case's module, witness, expect or kind changed in this audit; prose only.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the decision is a language-level boolean expression modeled deeply, no
# foreign callee consumed — mapping.md §3), so there is nothing to probe.
AXIOM_TESTS = []
