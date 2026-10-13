"""properties.py — G-PBT falsification battery for django__django-16950 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct prepareParentKey``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. One positive control (``pos-carrier-guarded-skip``) additionally
adjusts the ``prove_correct`` TACTIC body, which the same region surgery admits
and the consumer spec view elides equally; no case touches an ``ensures`` clause,
the method signature, or the obligation header. Each is checked by the real
verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable parent-object carrier
plus four read-only boolean observations:

  prepareParentKey (mut inst : ParentObject) (creatingNew keyHasDefault
                    keyIsPrimaryKey noDataSubmitted : Bool) return (u : Unit)
    ensures shouldClearKey … = true  → inst.keyValue = none
    ensures shouldClearKey … = false → inst.keyValue = instOld.keyValue

``inst.keyValue : Option Nat`` is the value held in the parent object's
auto-generated key attribute (``some v`` present, ``none`` cleared). The
discard decision is a GROUNDED pure predicate — fully unfolded over the four
boolean inputs, with no opaque callee and no answer-key oracle:

  shouldClearKey cn hd pk nd = cn && hd && (pk || nd)

There is no ``require`` clause, so the admitted domain is total over all 2^4
boolean configurations and every carrier value.

TWO independent top-level clauses, each load-bearing:
  (C) ``shouldClearKey … = true → inst.keyValue = none`` — the DISCARD clause.
      When the decision holds, the provisional value must actually be gone. A
      body that fails to clear on some genuine-discard configuration, or that
      stores any present value there, fails here.
  (P) ``shouldClearKey … = false → inst.keyValue = instOld.keyValue`` — the
      PRESERVE clause, and the one the failing test observes. When the decision
      does NOT hold, the attribute must be left EXACTLY as it was. Note this
      pins the post-state to the PRE-state ``instOld.keyValue``, not merely to
      "not none": writing a different present value is a violation too, which is
      what makes the mut-frame attack below refutable.

BINDER STRUCTURE (read before judging binder coverage). Both clauses are guarded
by ``shouldClearKey`` over all four boolean binders, and both constrain the
carrier binder ``inst.keyValue``; that is FIVE input binders, and a rival
mishandling only one of them would slip past a battery that pinned it. The
reject witnesses vary all five — ``creatingNew`` over {true,false},
``keyHasDefault`` over {true,false}, ``keyIsPrimaryKey`` over {true,false},
``noDataSubmitted`` over {true,false}, and ``inst.keyValue`` over
{some 7, some 5, some 3, some 8, some 2, none, some 4, some 6} — so no binder is
held at a single value across the battery. In particular ``keyValue = none`` is
probed at TWO different preserve configurations (the mut-frame rival and
``weak-fill-cleared-on-preserve-path``), because a preserve-clause rival that
only ever saw a PRESENT incoming value could hide a defect on the already-cleared
carrier — and the second of those two rivals is wrong ONLY there, so it is what
demonstrates that corner is genuinely load-bearing rather than merely visited.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — the nagini sibling reasons about heap
    permissions (the attribute is held at a FULL permission because the discard
    path genuinely writes it, and it notes there is therefore NO read-only
    half-permission input and no insufficient-permission attack). Lean and Velvet
    are referentially transparent: ``inst`` is a ``mut`` VALUE binder with no
    heap footprint, no aliasing and no fractional-permission system, so the
    permission-reasoning half of that class is VACUOUS here. What survives is the
    behavioural half — a body that WRITES the attribute on a path the spec pins
    unchanged — and that is refutable on this carrier because clause (P) pins the
    post-state to ``instOld.keyValue`` exactly. Ported as
    ``weak-write-on-preserve-path``; the permission-specific probe is not
    fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
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
  * UNGROUNDED-ORACLE ECHO — N/A. ``shouldClearKey`` is a transparent
    ``@[grind] def`` over four ``Bool`` inputs, not an opaque callee, so there is
    no answer-key for a rival to echo and no need to condition a witness on the
    carrier: every witness below closes by ``decide`` at literal inputs.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``prepareParentKeyTester inst cn hd pk nd = false`` says the extracted program's
observable (the mutated carrier) violates the method's postcondition at that
concrete input. Checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict — which matters here because
EVERY rival below also breaks the frozen ``loom_solve`` script, so tactic
breakage alone would attribute nothing to the spec. The carriers are
``Option Nat`` and ``Bool`` with decidable equality, so every witness closes by
``decide`` with no binders (hence no consistency question). Each reject witness
was run against BOTH the rival (exit 0) and the frozen solution (exit 1) with two
real builds and was SEEN to discriminate.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; mapping.md §3
records no axiomatized callee and no deep-model reference, and meta.json sets
``gates.G-AX.status = "skip"``). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16950"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap, so this
# ---- manifest breaks LOUDLY if the frozen solution ever changes.
_GOLD_IMPL = (
    "    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then\n"
    "      inst := { inst with keyValue := none }\n"
    "    else\n"
    "      return\n"
    "    return"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- the frozen proof body. `variant_scope` admits region surgery on the
# ---- `prove_correct` TACTIC body as well as on the impl region (both are
# ---- elided by the consumer spec view), so a positive control may reshape the
# ---- impl in a way the frozen script does not happen to close and supply the
# ---- extra step. That is a PROOF adjustment, not a spec adjustment: the
# ---- obligation header `prove_correct prepareParentKey` and both `ensures`
# ---- clauses stay byte-identical, so `markers.same_spec` still holds.
_GOLD_PROOF = "prove_correct prepareParentKey by\n  loom_solve"

assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


def _impl_proof(body, proof):
    """Variant with the impl body AND the `prove_correct` tactic body replaced."""
    return _swap(_impl(body), _GOLD_PROOF,
                 "prove_correct prepareParentKey by\n" + proof)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. The method returns `Unit` and mutates the carrier `inst`, so the
# ---- tester takes (inst, cn, hd, pk, nd) and reports whether the resulting
# ---- observable satisfies the postcondition. No `axiom`/`sorry`/
# ---- `native_decide`, and no binders — so nothing to be inconsistent about.
def _tester(body):
    return ("extract_program_for prepareParentKey\n"
            "prove_precondition_decidable_for prepareParentKey\n"
            "prove_postcondition_decidable_for prepareParentKey\n"
            "derive_tester_for prepareParentKey\n\n" + body)


def _witness(key_value, cn, hd, pk, nd):
    """`prepareParentKeyTester { keyValue := … } cn hd pk nd = false`, by decide."""
    b = lambda x: "true" if x else "false"
    return _tester(
        f"example : prepareParentKeyTester {{ keyValue := {key_value} }} "
        f"{b(cn)} {b(hd)} {b(pk)} {b(nd)} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG (over-fit to the
    # frozen code shape). Each keeps the byte-identical two-clause obligation;
    # the first two also keep the frozen `loom_solve` proof body verbatim and
    # reshape only the executable surface, while the third (added by the
    # independent audit) reshapes the impl in a way that needs ONE added tactic
    # step — see its rationale for why that is a proof gap and not a spec gap.
    # All three confirmed verifying with real builds.
    # =====================================================================
    {
        "id": "pos-flat-local",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the compound guard into a single boolean bound in a local,
        # then one conditional store. Same decision on all 16 configurations,
        # different executable shape (flatten + let-binding).
        "module": _impl(
            "    let clear := creatingNew && keyHasDefault && "
            "(keyIsPrimaryKey || noDataSubmitted)\n"
            "    if clear then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "rationale": (
            "structurally different CORRECT impl: the compound discard condition "
            "is computed once into a boolean local and the store is driven off "
            "that local, rather than being written inline in the branch "
            "condition. Identical truth value on all 16 boolean configurations "
            "and an identical carrier post-state, so both clauses (C) discard and "
            "(P) preserve still discharge under the frozen proof. If a faithful "
            "correct impl in this shape failed to verify the spec would be "
            "SPEC-TOO-STRONG. Ports the sibling pos-flat."),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the (keyIsPrimaryKey || noDataSubmitted) disjunct to the OUTER
        # branch and test creatingNew && keyHasDefault inside. De Morgan-free;
        # same truth value on all 16 configurations, nested rather than flat.
        "module": _impl(
            "    if keyIsPrimaryKey || noDataSubmitted then\n"
            "      if creatingNew && keyHasDefault then\n"
            "        inst := { inst with keyValue := none }\n"
            "      else\n"
            "        return\n"
            "    else\n"
            "      return\n"
            "    return"),
        "rationale": (
            "second structurally different CORRECT impl: the two-way disjunct is "
            "hoisted to the OUTER branch and the two mandatory conjuncts tested "
            "in the inner one — the opposite nesting order from the frozen body. "
            "Conjunction distributes over the disjunction, so the decision agrees "
            "on all 16 configurations and the carrier post-state is identical; "
            "both clauses still discharge under the frozen proof. Demonstrates "
            "the spec is not over-fit to the syntactic nesting of the guard "
            "(else SPEC-TOO-STRONG). Ports the sibling pos-reorder."),
    },
    {
        "id": "pos-carrier-guarded-skip",
        "kind": "soundness",
        "expect": "verify",
        # Skip the store when the attribute is ALREADY cleared: on the discard
        # path, test the carrier and store only when a value is actually present.
        # Observationally identical to the frozen body (storing `none` over `none`
        # is the identity), but it is the first positive whose reshape reads the
        # CARRIER rather than only the four boolean observations — the frozen
        # `loom_solve` alone does not close the extra branch, so the tactic body
        # carries one added `simp_all` (a proof adjustment; the obligation and
        # both `ensures` clauses are byte-identical).
        "module": _impl_proof(
            "    if creatingNew && keyHasDefault && "
            "(keyIsPrimaryKey || noDataSubmitted) then\n"
            "      if inst.keyValue.isSome then\n"
            "        inst := { inst with keyValue := none }\n"
            "      else\n"
            "        return\n"
            "    else\n"
            "      return\n"
            "    return",
            "  loom_solve\n  all_goals simp_all"),
        "rationale": (
            "third structurally different CORRECT impl, and the only positive "
            "whose reshape BRANCHES ON THE CARRIER instead of on the four "
            "boolean observations alone: on the discard path it stores `none` "
            "only when a value is actually present, skipping the write when the "
            "attribute is already cleared. Observationally identical to the "
            "frozen body — storing `none` over `none` is the identity — so both "
            "clauses (C) discard and (P) preserve hold at every one of the 16 "
            "configurations and at both carrier shapes. It is shipped because "
            "the frozen `loom_solve` does NOT close it on its own: the added "
            "`inst.keyValue.isSome` branch leaves the residual goal "
            "`shouldClearKey … = true → instOld.keyValue = none` under the "
            "hypothesis `¬instOld.keyValue.isSome = true`, which needs one "
            "`simp_all` to relate `¬isSome` to `= none`. That is a PROOF gap, "
            "not a spec gap, and distinguishing the two is the whole point of "
            "the case: without it a reader cannot tell whether the carrier-"
            "reading shape is rejected by the spec (SPEC-TOO-STRONG) or merely "
            "unclosed by a script tuned to a single-branch body. Beyond the "
            "sibling set, which reshapes only the guard."),
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's probe constructs a representative parent
    # object, establishes the precondition on it, and asserts the decision
    # predicate classifies the failing-test configuration and the genuine-discard
    # configurations as expected. There is no `require` clause here, so the
    # literal "a normal input satisfies the precondition" reading is vacuous.
    # The case is RE-AIMED at the two things that DO carry that lane's meaning on
    # a TOTAL carrier, both discharged by evaluation in one in-region `assert`
    # placed BEFORE the frozen obligation:
    #   (i) the OBLIGATION INSTANCE is satisfiable at exactly an F2P-shaped input
    #       — the total-carrier analogue of PRECOND-TOO-STRONG is not a rejected
    #       precondition but an obligation that cannot be met at the input the
    #       operation must handle, so the two clause guards are evaluated there
    #       and the state clause (P) demands is shown to be the incoming value,
    #       which the last conjunct pins is not `none`;
    #   (ii) the decision predicate is NON-DEGENERATE — not constantly true, not
    #       constantly false, and not collapsing the interesting corner, which
    #       would make both clauses agree with a rival everywhere.
    # The impl and the frozen proof are kept verbatim so the method's own
    # obligation still discharges. The assert is LIVE, re-measured by the audit:
    # rewriting the F2P preserve-demand conjunct to claim `= none` instead of
    # `= some 7` leaves the goal unproved and the build fails (exit 1), while the
    # shipped form builds clean (exit 0).
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      (shouldClearKey true true false false = false ∧\n"
            "       (shouldClearKey true true false false = true → "
            "(some 7 : Option Nat) = none) ∧\n"
            "       (shouldClearKey true true false false = false →\n"
            "         (some 7 : Option Nat) = some 7) ∧\n"
            "       shouldClearKey true true true true = true ∧\n"
            "       shouldClearKey true true false true = true ∧\n"
            "       shouldClearKey false true true true = false ∧\n"
            "       (some 7 : Option Nat) ≠ none))\n"
            + _GOLD_IMPL),
        "rationale": (
            "BOTH halves of the admissibility question are discharged BY "
            "EVALUATION at the concrete failing-test-shaped input, as a `have` "
            "before the frozen obligation is closed verbatim. (i) The OBLIGATION "
            "INSTANCE at that input is satisfiable rather than vacuous or "
            "contradictory: at (creatingNew, keyHasDefault, alternate key, data "
            "submitted) with a present incoming value, clause (C)'s guard is "
            "shown FALSE — so (C) imposes nothing there — while clause (P)'s "
            "guard is shown TRUE and the state it demands is shown to be the "
            "incoming value `some 7`, which the final conjunct pins is NOT "
            "`none`. So the two clauses do not jointly demand both `= none` and "
            "`≠ none` at the input the operation must handle, which is the "
            "analogue of PRECOND-TOO-STRONG on a total carrier: an obligation "
            "unsatisfiable at exactly an F2P-shaped input. (ii) The decision is "
            "NON-DEGENERATE over the corners that matter: it classifies the "
            "alternate-key-with-data configuration as PRESERVE (the one the "
            "failing test observes) while "
            "classifying BOTH the primary-key-with-data and the "
            "alternate-key-without-data configurations as DISCARD — so the "
            "predicate is neither constantly true nor constantly false, and the "
            "preserve corner is genuinely separated from the discard corners. The "
            "final conjunct pins that a present carrier value is distinguishable "
            "from a cleared one, so the discard is a real state transition rather "
            "than a no-op. The domain carries no `require`, so this replaces the "
            "sibling's precondition-admits-a-normal-input probe (vacuous here); "
            "the impl and frozen proof are verbatim so clauses (C) and (P) still "
            "discharge. If the assert failed, the interesting corner would be "
            "excluded or collapsed. Re-aims the sibling admiss-f2p."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input inside its OWN wrong sub-domain, plus the refinement
    # argument that its faithful real counterpart would NOT resolve. Every rival
    # also breaks the frozen tactic script (reshaping the impl is what a rival
    # does), which is exactly why each carries a witness: the witness is the only
    # evidence that the REJECTION comes from the spec and not from the tactic.
    # Witness points vary all five input binders (see BINDER STRUCTURE above).
    # =====================================================================
    {
        "id": "weak-drop-two-way-condition",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-CHANGE BEHAVIOUR. Discard whenever the parent is being created
        # and the attribute carries a default, ignoring the two-way condition
        # entirely. Correct on every other configuration; wrong exactly on the
        # sub-domain the failing test exercises.
        "module": _impl(
            "    if creatingNew && keyHasDefault then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": (
            "this is the pre-change decision: discard the provisional value on "
            "any parent being created whose attribute carries a default, with the "
            "two-way qualification absent. The failing test builds a parent whose "
            "auto-generated ALTERNATE key (not the parent's own primary key) "
            "carries a default, submits child-row field data referencing the "
            "parent through that attribute, and asserts both that the parent's "
            "key value is still present afterwards and that the child row "
            "resolves against exactly that value. With the qualification absent "
            "the value is discarded, the parent is left with no value for the "
            "attribute the submitted rows reference, and both assertions fail — "
            "so its faithful real counterpart is precisely what does NOT resolve."),
        "rationale": (
            "REJECT from clause (P) `shouldClearKey … = false → inst.keyValue = "
            "instOld.keyValue`: at (creatingNew, keyHasDefault, NOT "
            "keyIsPrimaryKey, data submitted) the decision is false (PRESERVE), "
            "yet this body stores `none`. The discard clause (C) is kept correct, "
            "so the ONLY failing clause is the preserve one. PRIMARY rival — it "
            "diverges from the frozen spec on exactly the failing-test "
            "sub-domain, so if it verified the spec would admit the pre-change "
            "behaviour => SPEC-TOO-WEAK. Refuted at keyValue = some 7, "
            "(true, true, false, false). Ports the sibling prepatch-bug."),
        "witness": _witness("some 7", True, True, False, False),
    },
    {
        "id": "weak-drop-primary-key-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the primary-key arm of the two-way condition: discard only when
        # no field data was submitted. A NEAR-MISS of the frozen decision — it
        # agrees on every alternate-key configuration, including the failing
        # test's — so it is refuted at its OWN distinguishing corner.
        "module": _impl(
            "    if creatingNew && keyHasDefault && noDataSubmitted then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": (
            "keeping only the no-data-submitted arm and dropping the "
            "is-the-parent's-own-primary-key arm means a parent's auto-generated "
            "PRIMARY key is no longer discarded when field data is submitted. A "
            "separately-tracked regression test covers exactly that "
            "configuration — adding a new parent whose own primary key is "
            "auto-generated, with child field data present — and asserts the "
            "provisional primary key is discarded so a fresh one is produced on "
            "persist. Leaving it populated reinstates the validation failure that "
            "test guards, so a faithful patch in this shape would NOT resolve."),
        "rationale": (
            "REJECT from clause (C) `shouldClearKey … = true → inst.keyValue = "
            "none`: at (creatingNew, keyHasDefault, keyIsPrimaryKey, data "
            "submitted) the decision is TRUE via the primary-key arm, but this "
            "body does not discard and the carrier keeps `instOld.keyValue`. "
            "NEAR-MISS: it agrees with the frozen decision on every "
            "alternate-key configuration — including the failing test's preserve "
            "corner — so it is refuted at the primary-key-with-data corner that "
            "actually distinguishes it, rather than sharing the primary rival's "
            "point. Refuted at keyValue = some 5, (true, true, true, false). "
            "Ports the sibling drop-pk-arm."),
        "witness": _witness("some 5", True, True, True, False),
    },
    {
        "id": "weak-drop-default-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the carries-a-default conjunct: discard whenever the parent is
        # being created and the two-way condition holds, even for an attribute
        # with no default at all.
        "module": _impl(
            "    if creatingNew && (keyIsPrimaryKey || noDataSubmitted) then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": (
            "dropping the carries-a-default conjunct discards the attribute's "
            "value even when it holds no model-level default — i.e. a value the "
            "caller actually supplied rather than a provisional generated one. "
            "The discard exists only to stop a provisional generated value from "
            "being taken as caller intent; a separately-tracked test pins the "
            "discard to the has-a-default case. Nulling a caller-supplied "
            "non-default value changes observable behaviour on inputs that "
            "previously round-tripped, so a faithful patch in this shape would "
            "NOT resolve."),
        "rationale": (
            "REJECT from clause (P): at (creatingNew, NOT keyHasDefault, "
            "keyIsPrimaryKey, data submitted) the decision is false because the "
            "default conjunct fails (PRESERVE), yet this body stores `none`. "
            "Isolates the `keyHasDefault` binder: it is the only rival whose "
            "witness holds that binder at false while the guard-level decision "
            "is what goes wrong there (weak-write-on-preserve-path also witnesses "
            "at keyHasDefault = false, but its guard is correct and its defect is "
            "the preserve-path write), so a decision defect confined to the "
            "no-default sub-domain could not hide behind the other cases. "
            "Refuted at keyValue = some 3, (true, false, true, false). Ports the "
            "sibling drop-hasdefault."),
        "witness": _witness("some 3", True, False, True, False),
    },
    {
        "id": "weak-ignore-creating-new",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the being-created conjunct: discard on an ALREADY-STORED parent
        # too, destroying a value that is not provisional at all.
        "module": _impl(
            "    if keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": (
            "dropping the being-created conjunct applies the discard to a parent "
            "that already exists in storage, whose key value is committed rather "
            "than provisional. Every test covering this behaviour discards only "
            "while the parent is being created; on an existing parent the value "
            "identifies the stored row, so clearing it whenever a child form is "
            "built would break editing an existing parent. A faithful patch in "
            "this shape would NOT resolve."),
        "rationale": (
            "REJECT from clause (P): at (NOT creatingNew, keyHasDefault, "
            "keyIsPrimaryKey, data submitted) the decision is false because the "
            "being-created conjunct fails (PRESERVE), yet this body stores "
            "`none`. Isolates the `creatingNew` binder: it is the only rival "
            "whose witness holds it at false while the guard-level decision is "
            "what goes wrong there (weak-write-on-preserve-path also witnesses at "
            "creatingNew = false, but its guard is correct and its defect is the "
            "preserve-path write), so a decision defect confined to the "
            "already-stored sub-domain is reachable. Refuted at keyValue = "
            "some 8, (false, true, true, false). Ports the sibling "
            "ignore-adding."),
        "witness": _witness("some 8", False, True, True, False),
    },
    {
        "id": "weak-conjoin-two-way-condition",
        "kind": "uniqueness",
        "expect": "reject",
        # Replace the two-way disjunction with a CONJUNCTION: require both the
        # primary-key property AND no submitted data. Strictly tighter discarding.
        "module": _impl(
            "    if creatingNew && keyHasDefault && "
            "(keyIsPrimaryKey && noDataSubmitted) then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": (
            "requiring BOTH halves of the two-way condition instead of either "
            "half discards strictly less often: a parent's auto-generated primary "
            "key with field data submitted is left populated, and so is an "
            "alternate key with no data submitted. Both configurations are "
            "covered by separately-tracked regression tests that assert the "
            "provisional value is discarded, so a faithful patch writing the "
            "conjunction would NOT resolve either of them."),
        "rationale": (
            "REJECT from clause (C): at (creatingNew, keyHasDefault, NOT "
            "keyIsPrimaryKey, NO data submitted) the decision is TRUE via the "
            "no-data arm, but the conjunction additionally demands the "
            "primary-key property, so this body does not discard and the carrier "
            "keeps `instOld.keyValue`. Refuted at a point where the `noData` arm "
            "alone licenses the discard — a DIFFERENT corner from "
            "weak-drop-primary-key-arm (which is refuted where the primary-key "
            "arm alone licenses it), so the two near-misses are separated rather "
            "than sharing a witness, and each demonstrates the arm it actually "
            "breaks. Refuted at keyValue = some 2, (true, true, false, true). "
            "Ports the sibling and-disjunct."),
        "witness": _witness("some 2", True, True, False, True),
    },
    {
        "id": "weak-write-on-preserve-path",
        "kind": "uniqueness",
        "expect": "reject",
        # The behavioural half of the sibling's frame class: the discard decision
        # is CORRECT, but on the preserve path the body writes a foreign present
        # value instead of leaving the carrier alone. Refutable here only because
        # clause (P) pins the post-state to `instOld.keyValue` exactly, not merely
        # to "not none".
        "module": _impl(
            "    if creatingNew && keyHasDefault && "
            "(keyIsPrimaryKey || noDataSubmitted) then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      inst := { inst with keyValue := some 999 }\n"
            "    return"),
        "refinement": (
            "the discard decision is exactly right; the defect is that the "
            "not-discarding path OVERWRITES the attribute with an unrelated value "
            "rather than leaving it untouched. The failing test asserts not just "
            "that the parent's key value is still present but that the submitted "
            "child row resolves against THAT SAME value; substituting any other "
            "value severs the relation just as surely as clearing it, and the "
            "equality assertion fails. A faithful patch that assigned on the "
            "not-discarding branch would NOT resolve."),
        "rationale": (
            "REJECT from clause (P): the preserve clause pins the post-state to "
            "the PRE-state `instOld.keyValue`, and `some 999` is neither `none` "
            "nor the incoming value. This is the surviving behavioural half of "
            "the sibling's frame-mutation class — a body that touches the carrier "
            "on a path the spec pins unchanged — with the "
            "permission-reasoning half vacuous on a referentially transparent "
            "carrier (see the module docstring). Its witness is the ONLY one "
            "holding the carrier at `none`: it refutes at an incoming "
            "keyValue = none, so `some 999 ≠ instOld.keyValue` is a "
            "present-vs-cleared violation and the already-cleared carrier is "
            "probed rather than assumed uninteresting. Refuted at "
            "keyValue = none, (false, false, false, true). Ports the sibling "
            "frame-preserve-write."),
        "witness": _witness("none", False, False, False, True),
    },
    {
        "id": "weak-never-discard",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror of the primary rival: never discard anything. Satisfies the
        # preserve clause everywhere and fails the discard clause on EVERY
        # genuine-discard configuration.
        "module": _impl("    return"),
        "refinement": (
            "removing the discard step entirely leaves every provisional "
            "auto-generated value in place. The separately-tracked tests for both "
            "genuine-discard configurations — a parent's own auto-generated "
            "primary key while adding, and an auto-generated alternate key with "
            "no field data submitted — assert the value is discarded so a fresh "
            "one is produced on persist. Leaving it populated reinstates the "
            "original validation failure in both, so a faithful patch that "
            "dropped the step would NOT resolve."),
        "rationale": (
            "REJECT from clause (C) `shouldClearKey … = true → inst.keyValue = "
            "none`: on a genuine-discard configuration the carrier keeps "
            "`instOld.keyValue`. The mirror of "
            "weak-drop-two-way-condition (never discards vs always discards), so "
            "it pins the OTHER clause. Refuted at the "
            "primary-key-AND-no-data corner (true, true, true, true) — a point "
            "where weak-drop-primary-key-arm and "
            "weak-conjoin-two-way-condition both AGREE with the frozen decision, "
            "confirmed by real builds, so this witness demonstrates a defect "
            "strictly broader than either near-miss instead of restating theirs. "
            "Refuted at keyValue = some 4, (true, true, true, true). Ports the "
            "sibling noop-never-clear."),
        "witness": _witness("some 4", True, True, True, True),
    },
    {
        "id": "weak-sentinel-instead-of-discard",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level attack with NO counterpart in the sibling: the branch
        # decision is exactly right, but the discard stores a present sentinel
        # instead of actually clearing the attribute.
        "module": _impl(
            "    if creatingNew && keyHasDefault && "
            "(keyIsPrimaryKey || noDataSubmitted) then\n"
            "      inst := { inst with keyValue := some 0 }\n"
            "    else\n"
            "      return\n"
            "    return"),
        "refinement": (
            "the decision of WHEN to discard is exactly right; the defect is WHAT "
            "is stored — a present zero sentinel instead of the absence of a "
            "value. The discard exists so that no value is carried into the "
            "persist step and a fresh one is generated there; storing a present "
            "zero instead means the parent is persisted with that zero as its "
            "key value, which is neither the generated value nor absent. The "
            "tests covering both discard configurations assert the value is "
            "absent afterwards, so a faithful patch assigning a sentinel would "
            "NOT resolve."),
        "rationale": (
            "REJECT from clause (C) at the VALUE level rather than the guard "
            "level: the guard agrees with `shouldClearKey` on all 16 "
            "configurations, so every guard-shaped rival above is satisfied here "
            "and only the stored value is wrong — `some 0 ≠ none`. Added beyond "
            "the sibling set because the discard clause pins the post-state to "
            "`none` specifically, and a battery attacking only the GUARD would "
            "leave that half of clause (C) undefended: a rival that decided "
            "perfectly and stored the wrong value would verify. Refuted at "
            "keyValue = some 6, (true, true, true, false)."),
        "witness": _witness("some 6", True, True, True, False),
    },
    {
        "id": "weak-fill-cleared-on-preserve-path",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the independent audit. The discard decision is exactly right
        # AND the preserve path leaves a PRESENT value alone — but it fills an
        # ALREADY-CLEARED carrier with a sentinel. So it is wrong at exactly one
        # kind of point: a preserve configuration whose incoming value is `none`.
        "module": _impl(
            "    if creatingNew && keyHasDefault && "
            "(keyIsPrimaryKey || noDataSubmitted) then\n"
            "      inst := { inst with keyValue := none }\n"
            "    else\n"
            "      inst := { inst with keyValue := "
            "inst.keyValue.orElse (fun _ => some 0) }\n"
            "    return"),
        "refinement": (
            "the decision of when to discard is exactly right, and a value that "
            "is actually present is preserved unchanged — so every "
            "present-carrier test still passes. The defect is that an attribute "
            "which was already empty gets populated with a sentinel instead of "
            "being left empty. That is observable precisely where the caller "
            "relies on the attribute still being empty so that a value is "
            "produced at persist time: a parent whose attribute was deliberately "
            "left unset is persisted carrying that sentinel instead, which is "
            "neither the value that would have been produced nor absent. A "
            "faithful patch that filled in a default on the not-discarding "
            "branch would NOT resolve."),
        "rationale": (
            "REJECT from clause (P) at the ALREADY-CLEARED carrier "
            "specifically: at (NOT creatingNew, keyHasDefault, keyIsPrimaryKey, "
            "data submitted) the decision is false (PRESERVE) and "
            "`instOld.keyValue = none`, so (P) demands the post-state be `none`, "
            "yet this body stores `some 0`. Added because it is the only rival "
            "whose wrong set is CONFINED to the `none` carrier: it agrees with "
            "the frozen decision at every present incoming value, confirmed by "
            "a real build (the same witness shape at keyValue = some 7 on the "
            "same configuration does NOT refute it, exit 1 — it matches gold "
            "there). weak-write-on-preserve-path witnesses AT keyValue = none "
            "but is wrong on the whole preserve path, so a defect reachable only "
            "on the already-cleared carrier could hide behind it; this case "
            "closes that. Refuted at keyValue = none, (false, true, true, "
            "false) — a preserve corner distinct from the one "
            "weak-write-on-preserve-path uses."),
        "witness": _witness("none", False, True, True, False),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 12 SPEC cases (2 soundness
# positives, 1 admissibility, 9 uniqueness rivals) and an EMPTY axiom lane,
# contracting `reset_default_related_key(instance, adding, key_has_default,
# key_is_primary, form_data_present)` over a permission-bearing heap object under
# a `MustTerminate(2)` obligation. This bundle models the same four-boolean
# decision over a referentially transparent `mut` value carrier, under
# `loom.semantics.termination "total"` — i.e. this bundle DOES ask for a
# termination obligation (see the weak-diverge entry for what it actually
# enforces). Every sibling case is accounted for below; one case is ADDED that
# the sibling lacks.
#
#   sibling case (nagini)   -> here                                status
#   ----------------------------------------------------------------------------
#   pos-flat                -> pos-flat-local                      PORTED
#   pos-reorder             -> pos-branch-reorder                   PORTED
#   admiss-f2p              -> admiss-decision-nondegenerate        RE-AIMED
#   prepatch-bug            -> weak-drop-two-way-condition          PORTED (primary)
#   drop-pk-arm             -> weak-drop-primary-key-arm            PORTED
#   drop-hasdefault         -> weak-drop-default-conjunct           PORTED
#   ignore-adding           -> weak-ignore-creating-new             PORTED
#   and-disjunct            -> weak-conjoin-two-way-condition       PORTED
#   frame-preserve-write    -> weak-write-on-preserve-path          PORTED (behavioural half)
#   noop-never-clear        -> weak-never-discard                   PORTED
#   weak-diverge            -> (none)                               SPEC-CLOSED (verifier)
#   weak-self-echo          -> (none)                               DROPPED (not spec-refuted)
#   (no counterpart)        <- weak-sentinel-instead-of-discard     ADDED
#   (no counterpart)        <- pos-carrier-guarded-skip              ADDED (audit)
#   (no counterpart)        <- weak-fill-cleared-on-preserve-path    ADDED (audit 2)
#   AXIOM_TESTS (empty)     -> (none)                               N/A (already empty)
#
# RE-AIMED (admiss-decision-nondegenerate): the sibling's probe constructs a
#   representative parent object and establishes `Requires(Acc(instance.key))` on
#   it, i.e. that the precondition admits a normal input. There is no `require`
#   clause here, so that reading is vacuous — nothing could exclude any input. The
#   case is re-aimed at the residual risk the sibling's probe ALSO covers with its
#   three `Assert(should_clear(...))` lines: that the decision predicate is
#   non-degenerate and separates the preserve corner from the discard corners.
#   The assert is live (the false variant fails to build) and the impl and proof
#   are verbatim.
#
# PORTED (weak-write-on-preserve-path), behavioural half only: the sibling frames
#   this as a frame/permission-flavour probe, while itself recording that the
#   attribute is held at FULL permission (the discard path genuinely writes it),
#   that there is consequently NO read-only half-permission input, and that the
#   rejection therefore comes from the preserve postcondition rather than from
#   insufficient permission. That reasoning transfers intact: on this carrier
#   there are no permissions at all, and the preserve clause pins the post-state
#   to `instOld.keyValue` exactly, which is what makes the write refutable. The
#   permission-specific probe has no counterpart and is NOT fabricated.
#
# SPEC-CLOSED (weak-diverge): NOT vacuous, NOT the partial-semantics story, and
#   NOT a hole in the verifier either. This entry has now been corrected TWICE and
#   both earlier versions are RETRACTED; what follows is the current
#   re-measurement, on scratch copies, with the bundle unmodified.
#
#     * FIRST RETRACTION. The original note claimed this bundle sets
#       `loom.semantics.termination "partial"`. FALSE: Solution.lean line 4 sets
#       "total" and line 7 opens `TotalCorrectness DemonicChoice`. The option
#       cannot be inert or disagree with the `open`, because its own elaborator
#       opens the matching scope (`Loom/MonadAlgebras/WP/Options.lean`,
#       `openScope`, where "total" opens `TotalCorrectness`).
#     * SECOND RETRACTION, the substantive one. The note that replaced it conceded
#       "total" but escalated a narrower defect located "in the VERIFIER, not in
#       the spec text": that the `decreasing` MEASURE is requested but not
#       discharged, so a loop whose measure increases or stays constant builds
#       CLEAN at exit 0 and makes the postcondition free in a never-taken exit.
#       That is FALSE, and its two quoted shapes were rebuilt verbatim here, each
#       spliced at the impl anchor with every proof reduced to a bare
#       `loom_solve`. Both are REJECTED at exit 1, on the measure's OWN descent
#       goal, reported as `unsolved goals`:
#         - `invariant 0 < q` / `done_with q = 0` / `decreasing q`, body
#           `q := q + 1` (a strictly INCREASING measure)
#           ->  `case decreasing_1: q ... |- q + 1 < q`;
#         - the same shape with a CONSTANT measure, body `q := 1`
#           ->  `case decreasing_1: q ... |- 1 < q`.
#       So the annotation is required to be TRUE and not merely present, and every
#       downstream claim of that note falls with its exit-0 builds: there is no
#       never-taken exit to exploit, because the build stops at the `method` before
#       any post-loop value goal is reached, and the control pair it offered (the
#       same loop with `i := i - 1` rejecting on the wrong store and verifying on
#       the gold store) shows only that a genuinely TERMINATING loop is checked
#       normally, which is not in dispute.
#
#   What holds, and is unchanged from both versions: a loop with NO `decreasing`
#   annotation is rejected outright ("Decreasing annotations are required in total
#   correctness semantics", exit 1), and loop INVARIANTS are genuinely discharged
#   (a false `invariant i = 99` fails with `unsolved goals ... case «invariant_1»`,
#   exit 1). Adding the measure obligation above, all three loop clauses are real
#   proof goals. Under `total` a postcondition is claimed of ALL runs and not only
#   of terminating ones, so nothing here is satisfied vacuously.
#
#   Nothing ships for the class, and the reason is the WITNESS contract rather than
#   difficulty or a spec weakness. A reject case needs a witness that ELABORATES
#   against the rival, and each diverging shape defeats that half differently.
#   Measured through the gate's own `_check_witness` on this cell:
#     * NO measure: the refusal is a module-level error at the `method` declaration
#       (line 75 of the spliced file), which the witness file RETAINS since it
#       strips only the `prove_correct` obligations, so the rival does not compile
#       and even `example : True := trivial` returns `witness-unproven`.
#     * MEASURE PRESENT BUT FALSE: the refusal moves to the `prove_correct` site,
#       which IS stripped, so the module elaborates and a trivial witness succeeds.
#       A real witness still fails: the rival keeps a `while`, so its post-image is
#       an unreduced `forIn Lean.Loop.mk ... invariantGadget ... decreasingGadget`
#       term the kernel will not normalise, and this battery's own witness against
#       that rival ends `unsolved goals` on it. `witness-unproven` again.
#   A `witness_reference` rescues neither, since it substitutes the GOLD subject
#   while the failure is on the RIVAL side. Both outcomes score `_INCONCLUSIVE` and
#   report MALFORMED-TESTS. Spec-side verdict: REJECT. Nothing is escalated, and no
#   fix is owed by the verifier or by a hand-written measure in the frozen
#   Solution.lean.
#
# DROPPED (weak-self-echo): the sibling discharges the contract by calling the
#   function under spec from inside its own body, and Nagini rejects it via the
#   obligation-leak check against `MustTerminate(2)`. The analogous variant here
#   (`let _u ← prepareParentKey inst creatingNew keyHasDefault keyIsPrimaryKey
#   noDataSubmitted`) IS rejected, but for a reason that has nothing to do with
#   the spec: Lean's own recursion checker refuses the definition
#   ("fail to show termination for prepareParentKey ... no parameters suitable
#   for structural recursion"), and the file does not elaborate at all. That
#   means no witness can be built against it either — the tester machinery needs
#   a rival that elaborates. Shipping it would be a reject case that passes for
#   the wrong reason (a front-end well-formedness error, not a refutation), which
#   is the failure mode this battery is written to avoid, so it is dropped rather
#   than banked. Not dropped for difficulty: the rival is simply not
#   spec-refutable on this carrier.
#
# ADDED (pos-carrier-guarded-skip), by the independent audit: all three sibling
#   positives and both ported ones reshape only the GUARD, i.e. they branch on the
#   four boolean observations and never read the carrier. That left one question
#   the battery could not answer: is a faithful impl that BRANCHES ON
#   `inst.keyValue` admitted? Built and measured during the audit — the shape
#   (skip the store when the attribute is already cleared) is observationally
#   identical to the frozen body, but the frozen `loom_solve` does NOT close it,
#   failing with the residual goal `shouldClearKey … = true → instOld.keyValue =
#   none` under `¬instOld.keyValue.isSome = true` (exit 1). One added `simp_all`
#   in the tactic body closes it (exit 0), and `variant_scope` admits tactic-body
#   surgery, so this is a PROOF gap and NOT a SPEC-TOO-STRONG hole. Shipped as a
#   positive so that distinction is machine-checked rather than argued: the case
#   now demonstrates the spec admits the carrier-reading shape.
#
# ADDED (weak-sentinel-instead-of-discard): every sibling rival attacks the GUARD
#   (which configurations discard). Clause (C) also pins WHAT is stored, to `none`
#   specifically, and on this carrier the stored value is an explicit
#   `Option Nat` write that a rival can get wrong independently of the guard. A
#   guard-only battery would leave that half of clause (C) undefended, so this
#   case decides perfectly and stores a present sentinel instead.
#
# CLAUSE / BINDER COVERAGE. The single obligation `prove_correct prepareParentKey`
# is DEFENDED by four verify cases (three soundness positives + admissibility) and
# ATTACKED by nine rejects. Both independent top-level clauses are attacked:
#   (C) discard  -> weak-drop-primary-key-arm, weak-conjoin-two-way-condition,
#                   weak-never-discard, weak-sentinel-instead-of-discard
#   (P) preserve -> weak-drop-two-way-condition, weak-drop-default-conjunct,
#                   weak-ignore-creating-new, weak-write-on-preserve-path,
#                   weak-fill-cleared-on-preserve-path
# The nine reject witnesses probe nine DISTINCT input points (pts=9):
#   keyValue   creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted  rival
#   some 7     true        true          false           false            drop-two-way
#   some 5     true        true          true            false            drop-pk-arm
#   some 3     true        false         true            false            drop-default
#   some 8     false       true          true            false            ignore-creating
#   some 2     true        true          false           true             conjoin-two-way
#   none       false       false         false           true             write-on-preserve
#   some 4     true        true          true            true             never-discard
#   some 6     true        true          true            false            sentinel
#   none       false       true          true            false            fill-cleared
# so every one of the five input binders takes BOTH values (or, for the carrier,
# distinct values including `none` at TWO different preserve configurations)
# across the battery: `creatingNew` {t,f}, `keyHasDefault` {t,f},
# `keyIsPrimaryKey` {t,f}, `noDataSubmitted` {t,f}, `inst.keyValue`
# {some 7, some 5, some 3, some 8, some 2, none, some 4, some 6}.
# No binder is pinned, and the two near-misses (drop-pk-arm, conjoin-two-way) are
# refuted at the corner each one actually breaks rather than sharing a point.
# Each witness was SEEN to discriminate: it ELABORATES against its rival (exit 0)
# and FAILS against the frozen solution (exit 1), confirmed with two real builds
# per case during authoring.
#
# INDEPENDENT AUDIT (attacks D and E), recorded so the probes are not re-paid.
# Three NEW wrong impls aimed at what the shipped rivals leave unattacked were
# built against the frozen spec; all three were REJECTED (exit 1), so no
# SPEC-TOO-WEAK hole was found beyond the known divergence one above:
#   * XOR for the two-way disjunction — agrees with the frozen decision on 15 of
#     16 configurations, differing ONLY at (creatingNew, keyHasDefault,
#     keyIsPrimaryKey, noDataSubmitted) all true, the tightest near-miss
#     available on this carrier. Refuted at keyValue = some 11 there.
#   * INCREMENT on the preserve path (`inst.keyValue.map (· + 1)`) rather than
#     the constant `some 999` the shipped frame rival writes: wrong at every
#     PRESENT incoming value rather than at one, so it cannot be satisfied by a
#     spec that merely pinned "still present". Refuted at some 7.
#   * CLEAR ONLY IF ALREADY CLEARED — the exact inverse of the added positive
#     `pos-carrier-guarded-skip`, and the reason that positive is worth having:
#     the two differ only in the sense of the carrier test, one is admitted and
#     one is refuted (at some 9), so the spec is shown to constrain the carrier
#     branch rather than to ignore it.
# Two further CORRECT reshapes (attack E) were built and VERIFY under the frozen
# proof body unchanged, so neither is a soundness hole: a branch-free single store
# of a conditional VALUE (`inst := { inst with keyValue := if … then none else
# inst.keyValue }`, re-confirmed exit 0), and a negated guard with the early
# return first (re-confirmed exit 0). The third reshape tried is shipped above as
# `pos-carrier-guarded-skip`.
#
# SECOND INDEPENDENT AUDIT (attacks D and E again, all builds re-run). Three
# further wrong impls were aimed at the value level and the guard's polarity, and
# all three were REJECTED under the frozen proof (exit 1), so no SPEC-TOO-WEAK
# hole was found beyond the termination one above:
#   * XOR for the two-way disjunction (`keyIsPrimaryKey != noDataSubmitted`) —
#     the tightest available near-miss, differing from the frozen decision only
#     at all-four-true.
#   * PRESERVE-PATH `orElse` — leaves a present value alone but fills an
#     already-cleared carrier with `some 0`, so it is wrong ONLY at the
#     `keyValue = none` preserve corner and cannot be caught by a battery that
#     only ever witnessed at a present incoming value.
#   * GUARD POLARITY INVERTED — discards exactly where the frozen decision
#     preserves and vice versa.
# One further CORRECT reshape was tried and could NOT be closed, and is recorded
# as UNCERTAIN rather than as a hole: driving the store off `match … with
# | true => … | false => return` instead of `if … then … else`. The frozen
# `loom_solve` fails on it with `Failed to parse an assertion without names:
# WPGen (match … )`, and neither `all_goals simp_all` nor `loom_solve <;>
# simp_all <;> grind` closes it (both exit 1). That error is the weakest-
# precondition generator declining to traverse a `match` on a `Bool` scalar — a
# front-end/TOOLING limitation about the shape of the generated assertion, NOT
# the spec rejecting the behaviour — so it is NOT evidence of SPEC-TOO-STRONG.
# It is reported as a tooling bug; the equivalent behaviour in `if` form is the
# frozen impl itself and in conditional-value form is the verifying reshape above.
AXIOM_TESTS = []
