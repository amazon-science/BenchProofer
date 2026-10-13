"""properties.py — G-PBT falsification battery for django__django-15499 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct reduceManagers`` obligation survives) and swaps in a
candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method, one obligation):

  reduceManagers (self : ModelCreate) (op : AlterManagers)
      return (res : ReduceResult)
    -- no `require`: the step is total over its inputs
    ensures res = reduceManagersSpec self op                        -- (C1)

C1 is the single load-bearing clause and the only impl-constraining one. It
pins ``res`` to the TRANSPARENT ``def reduceManagersSpec``, a total function of
the method's own two arguments — the ``axioms`` region is EMPTY, so there is no
opaque answer key to echo and the pin is grounded (spec_guide directive 8).
Unfolded, C1 composes two independent top-level outcomes selected by the
same-model test ``self.nameLower = op.nameLower``:

  * COLLAPSE (same model) — ``res = replace [{ self with managers := op.managers }]``,
    a ONE-element list holding a creation that agrees with ``self`` on
    ``nameLower``/``fields``/``options``/``bases`` and takes ``managers`` from
    ``op``. Five independently-attackable component routings plus the list
    length plus the ``ReduceResult`` constructor tag.
  * THROUGH (different model) — ``res = reduceThrough``: the alteration is
    independent of this creation and may be reordered across. Distinct from the
    third constructor ``cannotReduce``, so the else-branch's VALUE is attackable
    separately from which branch fires.

INPUT BINDERS AND HOW THE WITNESSES VARY THEM. Two binders, ``self`` (five
components) and ``op`` (two). Every reject witness below sits at a distinct
input point, and the points were chosen so that no component is held at one
value across the battery — the failure mode the coverage tool calls a binder no
rival was built to abuse:

  binder component     | varied by (witness points)
  ---------------------+--------------------------------------------------------
  self.nameLower       | "foo"/"bar"/"zap"/"alpha"/"eps"/"qux"/"delta"/"gamma"
                       | /"iota"/"kappa", and EQUAL-vs-DIFFERENT against
                       | op.nameLower
  op.nameLower         | equal to self's (collapse arm) AND differing ("foo" vs
                       | "bar", "alpha" vs "beta") — both arms of the same-model
                       | test probed
  self.fields          | [] / [1] / [7] / [1, 2] / [11] / [13]
  self.options         | [] / [("o", 2)] / [("x", 1)] / [("o", 1)]
  self.bases           | [] / [3] / [2] / [5] / [22]
  self.managers        | [] / [("m", 4)] / [("a", 3)] / [("m", 7)] / [("old", 9)]
                       | / [("keep", 1)]
  op.managers          | [] (the "iota" point) / [("n", 5)] / [("objects", 1)]
                       | / [("objects",1),("things",2)] / [("m", 2)] /
                       | [("new", 1)] / [("n", 8)] / [("m", 1)] / and EQUAL to
                       | self.managers (the "zap" point, where a rival that keeps
                       | self's managers agrees with gold and must be caught
                       | elsewhere)

  The values above are the ones the witnesses BELOW literally contain; an audit
  re-derived them from the shipped witness text rather than from this table.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * SOUNDNESS positives — APPLY, and they are cheap here: ``loom_solve``
    discharges a correct reshape, so no proof authoring is needed and no
    obligation is weakened. Four shapes ship (direct model return, negated
    guard with swapped arms, component-by-component record literal, named
    local).
  * ADMISSIBILITY — RE-AIMED. The nagini case established a fractional-
    permission precondition on an F2P-shaped input. This method carries NO
    ``require`` (the pre-conditions region is empty) and there is no permission
    surface, so "a normal input is admitted" is vacuous. Re-aimed at the
    residual risk on a total domain: that BOTH outcomes of the post-image are
    reachable and non-degenerate. An in-region ``assert`` pins the collapse and
    the through-report at F2P-shaped inputs, with the gold body kept verbatim so
    the method's own obligation still discharges.
  * FRAME/PERMISSION-MUTATION — VACUOUS, no substitute fabricated. The nagini
    sibling carries TWO mandatory rivals (``frame-mutate-managers``,
    ``frame-mutate-options``) that write a facet held at a fractional read-only
    permission and are rejected for INSUFFICIENT PERMISSION before any value
    reasoning. Lean and Velvet are referentially transparent: ``self`` and ``op``
    are immutable values, neither is declared ``mut``, and there is no heap,
    aliasing, or permission system to subvert. There is no read-only input to
    overwrite, so the class has no carrier analogue. DEMONSTRATED, not asserted:
    an audit built the nagini write verbatim (``self.managers := op.managers``
    ahead of the gold body) and the carrier refuses it at ELABORATION —
    "`self.managers` cannot be mutated, only variables declared using `let mut`
    can be mutated". So the rejection would attest to the absence of a mutable
    binder, never to the spec, which is exactly what a vacuous case looks like.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the nagini sibling
    records. Every slot of the post-image is pinned to a concrete component of
    ``self`` or ``op``; there is no oracle term to echo. The honest cheapest
    correct impl (return the model directly) ships as a POSITIVE instead.
  * PARTIAL-DOMAIN / VALUE — the whole reject lane, all against C1.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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

WITNESS MECHANICS. The spec is a ``method`` contract, not a bare predicate, so
each witness reaches the post-image through Velvet's own tester machinery:
``reduceManagersTester self op = false`` says the extracted program's result
violates the method's postcondition at that concrete input, closed by ``decide``
in a file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. The carrier is FULLY TRANSPARENT — no opaque callee, every
component a concrete ``List``/``String`` literal — so ``decide`` reduces the
tester at every point used below and NO witness needs to condition on the
carrier. No witness binds a hypothesis, so there are no assumptions that could
be jointly unsatisfiable and the gate's consistency probe has nothing to check.
Every witness was checked out-of-band with ``scripts/lean_verify.sh``: each
ELABORATES against its own rival (exit 0) and FAILS against the frozen solution
(``decide`` proves the proposition false, exit 1).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini sibling already records
its axiom lane as vacuous (``meta.json axioms=[]``, no ``@ContractOnly`` axiom);
G-AX skips this bundle for the same reason and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15499"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim: everything strictly BETWEEN the method's
# ---- `-- impl-start` / `-- impl-end` markers. Every variant replaces exactly
# ---- this text, so each edit lies wholly inside the one impl region and
# ---- same_spec holds by construction (both facts asserted by _swap).
_IMPL = """    if self.nameLower = op.nameLower then
      return ReduceResult.replace [{ self with managers := op.managers }]
    else
      return ReduceResult.reduceThrough"""
assert _BASE.count(_IMPL) == 1, "impl-region anchor drift — re-sync _IMPL"

# ---- the frozen proof, verbatim (tactic body only; elided from the spec view).
# ---- Kept as-is by every case except the two whose impl is a single expression,
# ---- where the frozen script's `<;>` second branch has no goal left to run on.
_PROOF = """prove_correct reduceManagers by
  loom_solve <;> simp_all [reduceManagersSpec]"""
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"

_PROOF_FLAT = "prove_correct reduceManagers by\n  loom_solve"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body):
    """Impl body replaced AND the proof retuned to the single-expression shape.

    Only for the correct reshapes whose body is one expression: the frozen
    script's `<;> simp_all [...]` then has no residual goal and Lean reports
    `this tactic is never executed`. The `prove_correct reduceManagers` header
    is preserved, so the obligation survives with an identical statement.
    """
    return _swap(_impl(body), _PROOF, _PROOF_FLAT)


# ---- witness preamble: Velvet's tester machinery. `reduceManagersTester self op
# ---- = false` says the extracted program VIOLATES the method's postcondition at
# ---- that input. Appended to BOTH the rival and the frozen file, so the derived
# ---- names exist on both sides by construction.
_TESTER = ("\nextract_program_for reduceManagers\n"
           "prove_precondition_decidable_for reduceManagers\n"
           "prove_postcondition_decidable_for reduceManagers\n"
           "derive_tester_for reduceManagers\n\n")


def _mc(nlower, fields, options, bases, managers):
    """A concrete ModelCreate literal for a witness input point."""
    return ("{ nameLower := %s, fields := %s, options := %s, bases := %s, "
            "managers := %s }" % (nlower, fields, options, bases, managers))


def _am(nlower, managers):
    """A concrete AlterManagers literal for a witness input point."""
    return "{ nameLower := %s, managers := %s }" % (nlower, managers)


def _witness(self_lit, op_lit):
    return (_TESTER
            + "example : reduceManagersTester\n    %s\n    %s = false := by\n"
              "  decide\n" % (self_lit, op_lit))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, C1 is
    # SPEC-TOO-STRONG (over-fit to the frozen code shape). All four verified
    # out-of-band with scripts/lean_verify.sh (exit 0).
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest HONEST correct impl: report the grounded model directly, with
        # no branch at all — maximally different in shape from the frozen
        # two-armed dispatch. `res` IS `reduceManagersSpec self op`, so C1 holds
        # on the whole domain.
        "module": _impl_reproved("    return reduceManagersSpec self op"),
        "rationale": (
            "C1 is literally `res = reduceManagersSpec self op`, so returning "
            "that grounded model directly is the cheapest honest CORRECT impl "
            "and MUST verify, else C1 is SPEC-TOO-STRONG. Doubles as the "
            "no-ungrounded-echo control the nagini sibling records: the "
            "post-image is a transparent function of the two arguments (the "
            "axioms region is empty), so there is no answer key to echo — any "
            "wrong component routing fails C1, as the eleven rivals below "
            "demonstrate. The branch is gone, so the frozen script's second "
            "`<;>` branch has no goal left; the tactic body is retuned to "
            "`loom_solve` with the obligation header untouched."),
    },
    {
        "id": "pos-control-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the same-model test and SWAP the arms. Same decision
        # table on every input; the frozen proof closes unchanged.
        "module": _impl(
            "    if self.nameLower ≠ op.nameLower then\n"
            "      return ReduceResult.reduceThrough\n"
            "    else\n"
            "      return ReduceResult.replace "
            "[{ self with managers := op.managers }]"),
        "rationale": (
            "a correct impl that negates the same-model test and swaps the two "
            "arms: observationally identical on every input, so C1 still "
            "discharges and the frozen tactic body closes as-is. Ports the "
            "nagini pos-control-reorder (which reorders the two fold branches); "
            "on this carrier the dispatch is a single two-armed test rather "
            "than an if/elif chain, so negating the guard is the faithful "
            "branch-order analogue. If it failed => SPEC-TOO-STRONG (over-fit "
            "to the guard's polarity)."),
    },
    {
        "id": "pos-control-explicit-components",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: spell the collapsed creation out component-by-component
        # instead of using the structure-update shorthand. Every slot is bound
        # to the same value the shorthand produces.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ nameLower := self.nameLower, fields := self.fields,\n"
            "           options := self.options, bases := self.bases,\n"
            "           managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "rationale": (
            "the collapsed creation is built by naming all five components "
            "explicitly rather than by the structure-update shorthand; every "
            "slot takes the same value, so C1 discharges and the frozen proof "
            "closes unchanged. This is the positive that makes the component-"
            "routing rivals meaningful: it shows the spec accepts the CORRECT "
            "explicit routing, so each rival's rejection is attributable to the "
            "one slot it mis-routes and not to the explicit form itself. Ports "
            "the nagini pos-control-name-first (a constructor-shape reshape "
            "keeping every live slot identical). If it failed => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-named-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the collapsed creation to a local before reporting it.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      let collapsed := { self with managers := op.managers }\n"
            "      return ReduceResult.replace [collapsed]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "rationale": (
            "binds the collapsed creation to a named local before reporting it "
            "— a pure staging reshape with unchanged value flow, so C1 still "
            "discharges and the frozen proof closes as-is. Mirrors the nagini "
            "sibling's staging positive. If it failed the spec would be "
            "over-fit to the inline-literal code form (SPEC-TOO-STRONG)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-f2p-self-call. That case
    # established that a fractional read-only precondition ADMITS an F2P-shaped
    # input. This method has no `require` at all and no permission surface, so
    # nothing could exclude a normal input and that probe is vacuous here.
    # Re-aimed at the residual risk on a total domain: that the post-image is
    # NON-DEGENERATE — both outcomes reachable, and the collapse actually
    # carrying the alteration's managers rather than collapsing to some fixed
    # answer. The gold body is kept verbatim so the method's own obligation
    # still discharges honestly. Verified out-of-band (exit 0).
    # =====================================================================
    {
        "id": "admiss-both-outcomes-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (reduceManagersSpec\n"
            "         { nameLower := \"foo\", fields := [], options := [], "
            "bases := [], managers := [] }\n"
            "         { nameLower := \"foo\", managers := [(\"objects\", 1), "
            "(\"things\", 2)] }\n"
            "       = ReduceResult.replace\n"
            "           [{ nameLower := \"foo\", fields := [], options := [], "
            "bases := [],\n"
            "              managers := [(\"objects\", 1), (\"things\", 2)] }]\n"
            "       ∧ reduceManagersSpec\n"
            "           { nameLower := \"foo\", fields := [], options := [], "
            "bases := [], managers := [] }\n"
            "           { nameLower := \"bar\", managers := [(\"objects\", 1)] }\n"
            "         = ReduceResult.reduceThrough))\n"
            + _IMPL),
        "rationale": (
            "the method carries NO `require`, so it is total and the classic "
            "'a legitimate input is admitted' probe is vacuous; re-aimed at the "
            "residual total-domain risk that the post-image is DEGENERATE. An "
            "in-region `assert` (elided from the spec view, so same_spec holds) "
            "discharges BOTH outcomes at F2P-shaped inputs: a creation of one "
            "model followed by a same-model alteration supplying two managers "
            "collapses to a ONE-element list carrying exactly those managers "
            "with the creation's other components intact, AND the same creation "
            "against a DIFFERENT-model alteration reports the through-outcome. "
            "That the two sides are provably DIFFERENT rules out a post-image "
            "satisfiable by a constant. The gold body is kept verbatim so the "
            "method's own obligation still discharges. If the assert failed the "
            "post-image would be unsatisfiable or degenerate at exactly the "
            "shape the failing test exercises."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input, and each carrying the argument for why its faithful real
    # counterpart would not resolve. All attack C1. Every one was verified
    # out-of-band to (a) FAIL the verifier and (b) have a witness that
    # elaborates against it and fails against gold.
    #
    # A NOTE ON THE REFINEMENT ARGUMENTS, which is the substantive finding of
    # this port. The single failing test pairs a creation with NO options, NO
    # bases and NO fields against a same-model alteration supplying two
    # managers. Component-routing rivals were therefore checked by BUILDING each
    # faithful real counterpart and running the whole migrations suite (654
    # tests) against it, rather than assumed. Measured: rivals that mis-route a
    # component the failing test leaves EMPTY pass all 654 tests, so their
    # refinement claim would be FALSE and they are NOT shipped as reject cases
    # here — see the footer, which records them as a spec-STRENGTH observation
    # (the spec is stronger than the suite) rather than as verify-does-not-
    # resolve breaks. Every rival below is one whose real counterpart was
    # MEASURED to fail the suite.
    # =====================================================================
    {
        "id": "uniq-no-collapse-reports-blocked",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-IMAGE SKELETON (Solution_prepatch.lean's dispatch): a
        # same-model alteration is reported as un-combinable instead of
        # collapsing. Exactly the behaviour the fix replaces.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.cannotReduce\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "this is the PRE-IMAGE behaviour that Solution_prepatch.lean "
            "reproduces and G-DIFF already flags: a same-model manager "
            "alteration is reported as un-combinable, so the pair is left "
            "standing as two operations instead of collapsing to one. MEASURED "
            "by building the faithful real counterpart (the optimization arm "
            "absent entirely) and running the suite: the failing test fails "
            "(it asserts the pair optimizes to a SINGLE creation carrying the "
            "supplied managers, and gets two operations), while all 654 other "
            "migrations tests still pass. So it is the exact missing behaviour "
            "and it does NOT resolve."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm: when the names agree, "
            "`reduceManagersSpec` is `replace [...]`, but the rival reports "
            "`cannotReduce` — a different `ReduceResult` constructor, so C1 is "
            "violated for every same-model input. Ports the nagini "
            "uniq-prepatch-no-manager-fold (whose MANAGERS branch is absent so "
            "a same-keyed alter falls through). Refuted at a point where all "
            "five of `self`'s components are NON-EMPTY and distinct from "
            "`op`'s, so the rejection cannot be an artifact of an empty "
            "component. If it verified => SPEC-TOO-WEAK (the spec would admit "
            "the pre-image)."),
        "witness": _witness(
            _mc('"foo"', '[1]', '[("o", 2)]', '[3]', '[("m", 4)]'),
            _am('"foo"', '[("n", 5)]')),
    },
    {
        "id": "uniq-collapse-keeps-own-managers",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapses, but reports `self` UNCHANGED — the alteration's managers
        # are never installed. "Fold but forget the new managers."
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace [self]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "collapses the pair but keeps the CREATION's own managers, so the "
            "alteration's effect is silently discarded — the pair becomes one "
            "operation that has lost what the alteration was for. MEASURED: "
            "the faithful real counterpart (`managers=self.managers` in the "
            "routing) fails the failing test, which asserts the collapsed "
            "creation carries the two managers the alteration supplied and "
            "instead finds the creation's original empty list; all 654 other "
            "migrations tests pass. It does NOT resolve. This is the "
            "load-bearing routing — the one component the collapse must take "
            "from the alteration rather than preserve."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's `managers` routing: the "
            "post-image is `{ self with managers := op.managers }`, and the "
            "rival reports `self`, whose managers are its own. Ports the nagini "
            "uniq-mgr-carries-model-managers, the load-bearing newly-added "
            "clause. Refuted at a point where `self.managers` is EMPTY and "
            "`op.managers` is not — the F2P-shaped discriminator, and a "
            "different point from every other rival's."),
        "witness": _witness(
            _mc('"bar"', '[]', '[]', '[]', '[]'),
            _am('"bar"', '[("objects", 1)]')),
    },
    {
        "id": "uniq-collapse-ignores-model-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the same-model test entirely: collapses unconditionally, so a
        # creation is merged with an alteration naming a DIFFERENT model.
        "module": _impl(
            "    return ReduceResult.replace "
            "[{ self with managers := op.managers }]"),
        "refinement": (
            "collapses unconditionally, merging a creation with an alteration "
            "that names a DIFFERENT model: the other model's managers are "
            "installed onto this one AND the alteration is deleted from the "
            "sequence. MEASURED, and this is the sharpest result of the port: "
            "the faithful real counterpart (the same-model test dropped from "
            "the routing condition) passes the failing test AND all 654 other "
            "migrations tests — no existing test pairs a creation with a "
            "different-model manager alteration, so the guard is entirely "
            "untested by the suite. Direct reproduction confirms the "
            "corruption: a creation of one model followed by an alteration "
            "naming a second model yields ONE operation in which the first "
            "model has acquired the second's managers and the second "
            "operation has vanished. So this rival is a genuine "
            "verify-does-not-imply-resolve candidate whose real counterpart "
            "would ship silent cross-model data corruption while the harness "
            "reported success — precisely the break G-PBT exists to detect, "
            "and the frozen spec DOES reject it (the else-arm pins the "
            "through-report), which is the spec being stronger than the test "
            "suite. It does not resolve the ISSUE even though it passes the "
            "tests."),
        "rationale": (
            "REJECT from C1 on the THROUGH arm: when the names differ the "
            "post-image is `reduceThrough`, but the rival reports a collapse. "
            "Ports the nagini uniq-ignore-name. Refuted at the battery's only "
            "point with DIFFERING names on the collapse-shaped side "
            "(self.nameLower=\"foo\", op.nameLower=\"bar\") — so this witness "
            "is what varies the same-model test's outcome, the binder relation "
            "every other reject witness holds at EQUAL. If it verified => "
            "SPEC-TOO-WEAK on the whole different-model sub-domain."),
        "witness": _witness(
            _mc('"foo"', '[1]', '[]', '[]', '[]'),
            _am('"bar"', '[("n", 5)]')),
    },
    {
        "id": "uniq-never-collapses",
        "kind": "uniqueness",
        "expect": "reject",
        # Always reports the through-outcome: never collapses at all.
        "module": _impl("    return ReduceResult.reduceThrough"),
        "refinement": (
            "never collapses, reporting every alteration as independent of the "
            "creation — so the optimization the issue asks for never happens, "
            "and a same-model alteration is additionally declared reorderable "
            "when it is not. MEASURED: the faithful real counterpart fails the "
            "failing test (the pair is never collapsed, so two operations "
            "survive where one is expected). Supporting near-miss for the "
            "collapse-existence half of C1; it resolves nothing."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm: for same-model inputs the "
            "post-image is `replace [...]` and the rival reports "
            "`reduceThrough`. Ports the nagini uniq-skip-all (never fold). "
            "Refuted at a point deliberately chosen so `op.managers` EQUALS "
            "`self.managers` — the sub-domain where the "
            "keeps-own-managers rival would agree with gold, so this witness "
            "attributes the rejection purely to the missing collapse and not "
            "to any component routing. That makes it a genuinely distinct "
            "point rather than a duplicate of the pre-image rival's."),
        "witness": _witness(
            _mc('"zap"', '[7]', '[("x", 1)]', '[2]', '[("a", 3)]'),
            _am('"zap"', '[("a", 3)]')),
    },
    {
        "id": "uniq-through-reported-as-blocked",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapses correctly, but reports a DIFFERENT-model alteration as
        # un-combinable rather than as independent/reorderable.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace "
            "[{ self with managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.cannotReduce"),
        "refinement": (
            "HONEST MEASUREMENT, and it goes the other way: this rival's "
            "faithful real counterpart DOES resolve. The collapse is exactly "
            "right; only the DIFFERENT-model report is wrong — an independent "
            "alteration is declared un-combinable instead of reorderable, "
            "which blocks the optimizer from moving other operations across it "
            "and silently suppresses unrelated optimizations downstream. TWO "
            "independent real encodings of exactly that semantic loss (an "
            "explicit different-model arm returning the blocking answer, and "
            "the reorderability predicate returning the blocking answer for "
            "this operation kind alone) were built and run: BOTH pass the "
            "failing test and all 654 migrations tests. Nothing in the suite "
            "fails because a different-model manager alteration stopped being "
            "reorderable — that operation kind appears four times in the whole "
            "migrations test package and never in a reordering scenario. Only "
            "the BROAD form that loses ALL cross-model reduction is caught (14 "
            "collateral failures, none of them the failing test). So this case "
            "is NOT a verify-does-not-imply-resolve break, and claiming it "
            "were would be a fabrication; it is shipped because the frozen "
            "spec REJECTS it anyway, which makes the spec strictly stronger "
            "than the suite on the else-arm's value."),
        "rationale": (
            "REJECT from C1 on the THROUGH arm's VALUE (as distinct from which "
            "branch fires, which uniq-collapse-ignores-model-identity "
            "attacks): the post-image is `reduceThrough` and the rival reports "
            "the third constructor `cannotReduce`. This is the only rival that "
            "separates the two non-collapse constructors, so without it the "
            "else-arm's value is defended by no attacker. Refuted at a "
            "differing-name point with all components non-empty "
            "(\"alpha\"/\"beta\"), distinct from every other witness."),
        "witness": _witness(
            _mc('"alpha"', '[1, 2]', '[("o", 1)]', '[5]', '[("m", 7)]'),
            _am('"beta"', '[("n", 8)]')),
    },
    {
        "id": "uniq-collapse-appends-managers",
        "kind": "uniqueness",
        "expect": "reject",
        # Concatenates instead of replacing: the collapsed creation carries the
        # creation's managers followed by the alteration's.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ self with managers := self.managers ++ op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "HONEST MEASUREMENT: this rival's faithful real counterpart DOES "
            "resolve. It APPENDS the alteration's managers to the creation's "
            "instead of REPLACING them, so a manager the alteration removed "
            "survives the collapse and a re-declared manager appears twice. "
            "The real counterpart was built and run: it passes the failing "
            "test and all 654 migrations tests, because the failing test's "
            "creation declares NO managers and concatenation onto an empty "
            "list equals replacement. Direct reproduction outside the suite "
            "confirms the defect is real and severe on inputs the suite never "
            "constructs: against a creation that already declares a manager, "
            "the counterpart raises a duplicate-value error from the "
            "creation's own constructor check, and in the silent form it "
            "resurrects a manager the alteration had deleted (the alteration "
            "REPLACES the manager set; concatenation makes it additive). So "
            "this is not a verify-does-not-imply-resolve break and is not "
            "dressed up as one; it is shipped because the frozen spec rejects "
            "it, i.e. the spec is strictly stronger than the suite on the "
            "manager-replacement routing. Its witness accordingly sits at a "
            "point where the creation DOES declare a manager — the sub-domain "
            "the suite cannot reach."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's `managers` routing, at the "
            "sub-domain the keeps-own-managers rival cannot reach: the "
            "post-image REPLACES managers with `op.managers`, and "
            "`self.managers ++ op.managers` differs from that whenever "
            "`self.managers` is non-empty. Refuted at the battery's only point "
            "with a NON-EMPTY `self.managers` differing from `op.managers` — "
            "so this witness is what varies that component off both empty and "
            "equal. ADDED (no nagini sibling): the nagini rivals mis-select a "
            "whole token, while a concatenation is a routing error only a "
            "list-shaped carrier can express, and it leaves the length of the "
            "managers component attackable."),
        "witness": _witness(
            _mc('"eps"', '[]', '[]', '[]', '[("old", 9)]'),
            _am('"eps"', '[("new", 1)]')),
    },
    {
        "id": "uniq-collapse-duplicates-result",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct creation, but reported TWICE: the result list has length 2.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ self with managers := op.managers },\n"
            "         { self with managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "routes every component correctly but reports the collapsed "
            "creation TWICE, so the pair of operations is replaced by two "
            "duplicate creations instead of one — the same model created twice "
            "in the migration sequence. MEASURED: the faithful real "
            "counterpart fails the failing test on the resulting length "
            "mismatch (one operation expected, two produced); it terminates "
            "cleanly rather than looping, so this is an ordinary wrong answer "
            "and not a hang. All 654 other migrations tests pass, so the "
            "failing test is exactly what catches it. It does NOT resolve."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's LIST STRUCTURE, which no "
            "component-routing rival touches: the post-image is a ONE-element "
            "list and the rival's has two, so C1 fails even though every "
            "component inside is correct. ADDED (no nagini sibling): nagini's "
            "carrier returns a single optional creation, so the result's "
            "LENGTH is not expressible there; on this carrier the reducer "
            "reports a LIST and its length is an independent part of the "
            "post-image that would otherwise go unattacked. Refuted at its own "
            "point (\"qux\")."),
        "witness": _witness(
            _mc('"qux"', '[1]', '[]', '[]', '[]'),
            _am('"qux"', '[("m", 2)]')),
    },
    {
        "id": "uniq-collapse-clobbers-options-with-managers",
        "kind": "uniqueness",
        "expect": "reject",
        # The alteration's managers are routed into the OPTIONS slot as well as
        # the managers slot.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ self with options := op.managers, "
            "managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "installs the alteration's managers correctly but ALSO overwrites "
            "the creation's options with that same manager collection — a "
            "routing error that puts a manager list where the model's declared "
            "options belong. The alteration carries no options at all, so "
            "there is no sense in which this is a defensible reading. "
            "MEASURED: the faithful real counterpart fails, and it fails on "
            "the failing test's OWN input, because the alteration's manager "
            "collection is non-empty there while the creation's options are "
            "empty — so the collapsed creation acquires options it should not "
            "have. It does NOT resolve. Ports the nagini "
            "uniq-mgr-clobbers-options, whose rival routes the alter step's "
            "token into the option slot."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's `options` routing: the "
            "post-image PRESERVES `self.options`, and the rival replaces it "
            "with `op.managers`. Refuted at the F2P-shaped point where "
            "`self.options` is empty and `op.managers` holds the two supplied "
            "managers — the routing error is visible precisely because the "
            "alteration's token is non-empty, which is why this rival is "
            "shipped while the drop-a-component variants (which coincide with "
            "gold on that same input) are not: see the footer."),
        "witness": _witness(
            _mc('"foo"', '[]', '[]', '[]', '[]'),
            _am('"foo"', '[("objects", 1), ("things", 2)]')),
    },
    {
        "id": "uniq-collapse-transposes-fields-and-bases",
        "kind": "uniqueness",
        "expect": "reject",
        # fields and bases swapped in the collapsed creation.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ self with fields := self.bases, bases := self.fields,\n"
            "                     managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "installs the alteration's managers correctly but TRANSPOSES the "
            "creation's fields and bases in the collapsed creation, so the "
            "model's declared fields and its inheritance list are swapped. "
            "MEASURED: the faithful real counterpart does NOT resolve, and it "
            "fails harder than an assertion — it ERRORS on the failing test's "
            "OWN input with a type error raised inside the creation's own "
            "constructor, because the default inheritance list routed into the "
            "field slot cannot be read as a field pair at all. The optimizer "
            "cannot even run. A transposition rather "
            "than a drop is what makes this rival MEASURABLY wrong: it "
            "diverges from gold whenever fields and bases DIFFER, including on "
            "shapes the suite exercises, whereas simply omitting one component "
            "coincides with gold on the failing test's empty-component input "
            "(footer). It does NOT resolve. Ports the nagini "
            "uniq-mgr-clobbers-fields, re-expressed as a transposition so its "
            "refinement claim is one this carrier's suite actually "
            "demonstrates."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's `fields` AND `bases` "
            "routings, the two components no other shipped rival attacks: the "
            "post-image preserves both, and the rival crosses them. Refuted at "
            "the battery's only point where `self.fields` and `self.bases` are "
            "both non-empty and DIFFERENT ([11] vs [22]) — a point no other "
            "witness occupies, and the only one that can separate a "
            "transposition from the identity."),
        "witness": _witness(
            _mc('"delta"', '[11]', '[]', '[22]', '[]'),
            _am('"delta"', '[("m", 1)]')),
    },
    {
        "id": "uniq-collapse-fields-from-alteration",
        "kind": "uniqueness",
        "expect": "reject",
        # The fields slot is fed from the alteration's manager collection.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ self with fields := op.managers.map (fun p => p.2),\n"
            "                     managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "installs the alteration's managers correctly but ALSO derives the "
            "collapsed creation's FIELDS from that same manager collection, "
            "destroying the creation's declared field list and replacing it "
            "with entries derived from the managers. MEASURED: the faithful "
            "real counterpart fails on the failing test's own input, because "
            "the alteration supplies two managers while the creation declares "
            "no fields, so the collapsed creation acquires two fields it must "
            "not have. It does NOT resolve. This is the shipped form of the "
            "nagini uniq-mgr-clobbers-fields' argument: routing the alter "
            "step's token into the fields slot, at a point where that token is "
            "non-empty and so the error is observable."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's `fields` routing "
            "specifically: the post-image preserves `self.fields`, and the "
            "rival derives it from `op.managers`. Distinct from the "
            "transposition rival, which crosses two of `self`'s own components "
            "and is refuted where they differ; this one imports the "
            "ALTERATION's token into a preserved slot and is refuted at the "
            "F2P-shaped point where `self.fields` is empty and `op.managers` "
            "is not. Two different sub-domains for the same slot, so each "
            "carries its own witness."),
        "witness": _witness(
            _mc('"foo"', '[]', '[]', '[]', '[]'),
            _am('"foo"', '[("objects", 1), ("things", 2)]')),
    },
    {
        "id": "uniq-collapse-keeps-own-when-alteration-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Reads an EMPTY new manager collection as "no managers
        # supplied, so leave the creation's own alone". Agrees with gold on every
        # point the rest of the battery occupies, and diverges only where
        # `op.managers` is EMPTY — a sub-domain no other witness reaches.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      if op.managers.isEmpty then\n"
            "        return ReduceResult.replace [self]\n"
            "      else\n"
            "        return ReduceResult.replace "
            "[{ self with managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "treats an EMPTY supplied manager collection as 'nothing to "
            "install' and keeps the creation's own managers instead. That is a "
            "real semantic loss: emptying a model's manager set is a "
            "meaningful alteration, and this rival silently ignores exactly "
            "that request, so a model keeps managers the alteration removed. "
            "NOT claimed to be a verify-does-not-resolve break: the audit that "
            "added this case did not rebuild the real counterpart against the "
            "suite, and the F2P input supplies a NON-EMPTY manager collection, "
            "so on the evidence available this rival's real counterpart would "
            "very likely pass the suite — it is shipped because the frozen "
            "spec rejects it, i.e. the spec is stronger than the suite here, "
            "the same class (b) the footer describes."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's `managers` routing, in the "
            "one sub-domain the three other managers rivals leave open: the "
            "post-image REPLACES managers with `op.managers` unconditionally, "
            "including when `op.managers` is `[]`. The keeps-own-managers "
            "rival is refuted where `op.managers` is non-empty, appends-managers "
            "where `self.managers` is non-empty and different, and "
            "never-collapses where the two are EQUAL — none of them varies "
            "`op.managers` off non-empty. ADDED BY AUDIT: before this case no "
            "witness in the battery had an EMPTY `op.managers`, so a rival "
            "conditioned on that emptiness was unattacked."),
        "witness": _witness(
            _mc('"iota"', '[]', '[]', '[]', '[("keep", 1)]'),
            _am('"iota"', '[]')),
    },
    {
        "id": "uniq-collapse-drops-result",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Collapses to the EMPTY list: both operations vanish.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace []\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "collapses the pair into NOTHING: the creation is deleted along "
            "with the alteration, so the model is never created at all and "
            "every later operation and state rebuild that depends on it "
            "breaks. Strictly more destructive than the duplicate-result "
            "rival. Its real counterpart would fail the failing test on the "
            "resulting length mismatch (one operation expected, zero "
            "produced), the same way the duplicate rival fails on two — but "
            "the audit that added this case did NOT rebuild it against the "
            "suite, so that is stated as the expectation it is and not as a "
            "measured result."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's LIST LENGTH, on the side the "
            "duplicates-result rival cannot reach: the post-image is a "
            "ONE-element list, duplicates-result probes length TWO, and this "
            "probes length ZERO. Refuted at its own point ('kappa') whose "
            "`self.fields` is non-empty, so the emptied result is "
            "distinguishable from a creation that carried nothing anyway. "
            "ADDED BY AUDIT: length was previously attacked in one direction "
            "only."),
        "witness": _witness(
            _mc('"kappa"', '[13]', '[]', '[]', '[]'),
            _am('"kappa"', '[("m", 1)]')),
    },
    {
        "id": "uniq-collapse-renames-model",
        "kind": "uniqueness",
        "expect": "reject",
        # The collapsed creation's model identity is replaced by a constant.
        "module": _impl(
            "    if self.nameLower = op.nameLower then\n"
            "      return ReduceResult.replace\n"
            "        [{ self with nameLower := \"\", "
            "managers := op.managers }]\n"
            "    else\n"
            "      return ReduceResult.reduceThrough"),
        "refinement": (
            "collapses and routes every component correctly, but the collapsed "
            "creation loses the model's identity — it is emitted under an empty "
            "name. MEASURED: the faithful real counterpart fails the failing "
            "test, which compares the optimized output against a creation "
            "named for the model, and the name mismatch defeats that "
            "comparison; downstream, a creation with no name breaks "
            "deconstruction and state rebuilding. It does NOT resolve. This is "
            "the shippable remnant of the nagini "
            "uniq-fold-installs-lower-name — see the footer for why that "
            "rival's own form is NOT expressible on this carrier and is "
            "reported as a dropped case rather than quietly re-labelled."),
        "rationale": (
            "REJECT from C1 on the COLLAPSE arm's model-identity routing, "
            "which no other shipped rival attacks: the post-image preserves "
            "`self.nameLower` and the rival substitutes a constant. Refuted at "
            "a point whose `nameLower` is NON-EMPTY (\"gamma\"), which is what "
            "makes the constant distinguishable — a witness at an empty name "
            "would coincide with gold and discriminate nothing."),
        "witness": _witness(
            _mc('"gamma"', '[]', '[]', '[]', '[]'),
            _am('"gamma"', '[("m", 1)]')),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The nagini sibling ships 13 cases against 5
# contracted facets of a 6-component carrier; this bundle contracts ONE method
# over a 5-component creation and a 2-component alteration, with no permission
# system and no display-name component. 18 velvet cases: 4 soundness, 1
# admissibility, 13 uniqueness (11 as ported, +2 added by the audit below).
#
#   nagini case                        -> here
#   ----------------------------------------------------------------------
#   pos-control-reorder                -> pos-control-negated-guard      PORTED
#   pos-control-name-first             -> pos-control-explicit-components PORTED
#   (no sibling)                       -> pos-control-direct-model        ADDED
#   (no sibling)                       -> pos-control-named-local         ADDED
#   admiss-f2p-self-call               -> admiss-both-outcomes-f2p-shaped RE-AIMED
#   frame-mutate-managers              -> (none)                          VACUOUS
#   frame-mutate-options               -> (none)                          VACUOUS
#   uniq-prepatch-no-manager-fold      -> uniq-no-collapse-reports-blocked PORTED
#   uniq-mgr-carries-model-managers    -> uniq-collapse-keeps-own-managers PORTED
#   uniq-ignore-name                   -> uniq-collapse-ignores-model-identity PORTED
#   uniq-skip-all                      -> uniq-never-collapses            PORTED
#   uniq-mgr-clobbers-options          -> uniq-collapse-clobbers-options-with-managers PORTED
#   uniq-mgr-clobbers-fields           -> uniq-collapse-fields-from-alteration PORTED
#                                       + uniq-collapse-transposes-fields-and-bases
#   uniq-opt-carries-alter-managers    -> (none)                          NOT EXPRESSIBLE
#   uniq-fold-installs-lower-name      -> (none)                          NOT EXPRESSIBLE
#                                       (remnant: uniq-collapse-renames-model)
#   (no sibling)                       -> uniq-through-reported-as-blocked ADDED
#   (no sibling)                       -> uniq-collapse-appends-managers   ADDED
#   (no sibling)                       -> uniq-collapse-duplicates-result  ADDED
#   (no sibling)                       -> uniq-collapse-keeps-own-when-alteration-empty
#                                                                    ADDED BY AUDIT
#   (no sibling)                       -> uniq-collapse-drops-result   ADDED BY AUDIT
#   AXIOM_TESTS = []                   -> (none)                          N/A
#
# NOT EXPRESSIBLE (2) — the honest omissions, both because this carrier collapses
# a distinction nagini's keeps. Neither is dropped for being hard to prove.
#
#  * uniq-fold-installs-lower-name (nagini's P1 break: the collapse installs the
#    lower-cased comparison KEY as the new DISPLAY name). Nagini carries the
#    display name and the comparison key as two DISTINCT components, so a rival
#    can confuse them. This bundle's creation carries ONLY the case-folded name
#    (mapping.md §2 — the display name is not part of the modeled carrier,
#    because the optimization never reads it), so there is no second component to
#    confuse it with. MEASURED, not assumed: the rival that takes the collapsed
#    creation's name from the ALTERATION rather than the creation VERIFIES here,
#    and correctly so — inside the same-model arm the guard has PROVED the two
#    names equal, making the two readings provably identical. It is not a wrong
#    impl on this carrier and no witness can discriminate it, so shipping it as a
#    reject case would be a case that passes for the wrong reason. The attackable
#    remnant — that the collapsed creation must keep the model's identity at all
#    — ships as uniq-collapse-renames-model.
#    RE-DERIVED INDEPENDENTLY BY AUDIT and the claim holds: the impl
#    `{ self with nameLower := op.nameLower, managers := op.managers }` VERIFIES
#    (exit 0) against the frozen spec. Inside the collapse arm the guard has
#    proved `self.nameLower = op.nameLower`, so the two readings are the same
#    value and the rival is definitionally equal to gold on this carrier — the
#    textbook attack-C vacuous case. Dropping it was correct; had it been
#    shipped as a reject case it could only have failed for a tactic reason.
#  * uniq-opt-carries-alter-managers (the SYMMETRIC clobber on the pre-existing
#    OPTIONS-alteration branch). That branch is a DIFFERENT operation kind, and
#    this bundle models the reducer restricted to the manager-alteration kind
#    (mapping.md §1, meta.json carrier_type) — the options-alteration arm is
#    outside the modeled surface entirely, so there is no impl region in which to
#    express the rival. Carrier narrowing, not an omission of an attackable
#    behavior.
#
# EVERY REFINEMENT CLAIM WAS MEASURED, NOT ASSUMED — the port's substantive
# finding. Rather than assert "its faithful real patch would not resolve" from
# the armchair, each candidate rival was rebuilt as a faithful REAL patch in an
# isolated tree and run against the failing test and the whole 654-test
# migrations package (gold control: resolves; unpatched baseline: 653 tests, the
# test patch adds exactly one). The results split the rivals in two, and the
# manifest states which side each is on instead of flattening them:
#
#   (a) real counterpart FAILS the suite => a genuine
#       verify-does-not-imply-resolve break. Eight of the eleven shipped rivals:
#       the pre-image skeleton and the never-collapse rival (failing test only);
#       keeps-own-managers; duplicates-result; renames-model (empty name defeats
#       the comparison); clobbers-options-with-managers and
#       fields-from-alteration (both caught on the failing test's OWN input);
#       transposes-fields-and-bases (an ERROR, not an assertion failure — the
#       constructor raises a type error on the failing test's own input).
#   (b) real counterpart PASSES all 654 => NOT a resolve break. Three shipped
#       rivals are in this class and say so plainly in their `refinement`:
#       ignores-model-identity, through-reported-as-blocked, and
#       appends-managers. They are shipped because the FROZEN SPEC REJECTS THEM
#       ANYWAY, which is the spec being strictly STRONGER than the test suite —
#       a spec-strength observation, the opposite of the SPEC-TOO-WEAK failure
#       the reject lane hunts for. Their defects are real (verified by direct
#       reproduction outside the suite: one model acquiring another's managers
#       while the other operation vanishes; unrelated optimizations silently
#       suppressed; a deleted manager resurrected, or a duplicate-value error
#       from the creation's own constructor) but unreachable from the harness.
#
# WHY class (b) exists, and the rivals it made UNSHIPPABLE. The failing test's
# creation declares no fields, no options and default bases, declares no
# managers, and no test in the package pairs a creation with a different-model
# manager alteration (that operation kind appears four times in the whole
# package, never in a reordering scenario). So any defect confined to those
# empty slots, or to cross-model reorderability, is invisible. That directly
# rules out three otherwise-obvious rivals — "omit the options", "omit the
# bases", "empty the fields" — whose real counterparts pass all 654 tests
# because DROPPING AN EMPTY SLOT IS A NO-OP. They are not shipped, since their
# only honest refinement would be class (b) and they would add nothing the three
# class-(b) rivals above do not already record. Their clauses are attacked
# instead by forms measured to fail: OVERWRITING a slot with the alteration's
# NON-EMPTY token (options, fields) and TRANSPOSING two of the creation's own
# components (fields/bases). Overwriting is observable exactly where dropping is
# not.
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# RETRACTED (what stood in the lines below before). This footer used to continue
# with the opposite disposition: that the bundle sets
# `loom.semantics.termination "partial"`, "one of the many velvet bundles that do",
# that a non-terminating impl therefore satisfies C1 VACUOUSLY, and that a
# CONFIRMED build showed a spinning body followed by an unambiguously wrong
# `cannotReduce` report VERIFYING at exit 0, a genuine
# verify-does-not-imply-resolve break and a defect of the frozen spec. All of it is
# withdrawn. Line 4 of the frozen file reads "total" and line 7 opens
# TotalCorrectness; all 500 velvet bundles do, and NONE sets "partial", so the
# claimed `partial` cohort does not exist either.
# block above: a spin prefix carrying a constant `decreasing` clause is REJECTED on
# the measure's own descent goal, and one without the clause is refused earlier
# still by the elaborator. There is no break here to record and nothing to
# escalate. The notice is kept rather than the text simply deleted, so a reader who
# saw the earlier claim can see it withdrawn.
# CLAUSE / BINDER / POINT COVERAGE. The one obligation `prove_correct
# reduceManagers` is DEFENDED by 4 positives + 1 admissibility and ATTACKED by 13
# rivals. C1's two top-level outcomes are both attacked: the COLLAPSE arm by
# eleven rivals (constructor tag, list length in BOTH directions — zero and two
# against the correct one — and each of the five component routings: managers by
# four rivals covering the empty / equal / non-empty-and-different /
# empty-ALTERATION sub-domains, options, fields by two, bases, model identity)
# and the THROUGH arm by two (which branch fires, and the else-arm's constructor
# VALUE). Both binders are varied: `op.nameLower` sits EQUAL to `self.nameLower`
# on eleven witnesses and DIFFERENT on two, so the same-model test's outcome is
# not held fixed; `self.managers` is probed empty, equal to `op.managers`, and
# non-empty-and-different; `op.managers` is probed non-empty at seven values AND
# EMPTY (the "iota" point); `self.fields` and `self.bases` are each probed empty
# and non-empty, and are non-empty-and-mutually-different at four points
# (including the transposition rival's own [11]-vs-[22], the only point that can
# separate a transposition from the identity); `self.options` empty and non-empty;
# `self.nameLower` non-empty at ten distinct values.
#
# The thirteen witnesses occupy TWELVE distinct input points: every rival has its
# own point except the two that route the alteration's manager token into a
# PRESERVED slot (options, fields), which deliberately share the F2P-shaped
# point, because that is exactly where each is observable — the token is
# non-empty there while the slot it corrupts is empty. Their rationales say so,
# so neither claims a sub-domain the manifest does not demonstrate.
#
# The two audit-added rivals exist because the ported battery held one binder
# value fixed across all eleven of its witnesses: `op.managers` was NON-EMPTY at
# every single point, so an impl conditioned on its emptiness was unattacked, and
# the result LENGTH was attacked only from above (two) and never from below
# (zero). Both gaps are now closed with machine-checked witnesses. The coverage
# reporter called the ported battery clean at pts=10, which is why this is
# recorded here: a clean advisory report is not evidence that a varied binder is
# varied MEANINGFULLY.
#
# WITNESS MECHANICS: the carrier is fully transparent (empty `axioms` region, no
# opaque callee, every component a concrete literal), so Velvet's tester
# machinery + `decide` reduces at every point and NO witness needs to condition
# on the carrier. No witness binds a hypothesis, so none can be
# `witness-inconsistent`. All thirteen were checked out-of-band with
# scripts/lean_verify.sh: each elaborates against its rival (exit 0) and fails
# against the frozen solution (exit 1).
#
# INDEPENDENTLY RE-DERIVED. An audit rebuilt all 11 ported witness pairs itself
# (22 builds): rival exit 0 and gold exit 1 on every one, and — the half the gate
# records but does not inspect — every gold-side failure is the SEMANTIC form
# "Tactic `decide` proved that the proposition ... is false", naming the concrete
# input. None failed by stuck reduction, unknown identifier, type error or
# timeout, so no rejection here rests on a syntactic accident. The 2 audit-added
# witnesses were built the same way with the same outcome.
# ===========================================================================
AXIOM_TESTS = []
