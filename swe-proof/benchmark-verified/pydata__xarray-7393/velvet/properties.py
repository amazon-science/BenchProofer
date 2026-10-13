"""properties.py — G-PBT falsification battery for pydata__xarray-7393 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct arrayDispatch`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over an opaque view handle):

  arrayDispatch (adapter : Int) (dtype : Option Dtype) return (out : MatArray)
      ensures out = arrayMaterialize adapter dtype

where ``arrayMaterialize`` is a fully-unfolded ``def`` in the ``pure`` region:

  arrayMaterialize adapter dtype =
    let d := dtype.getD (recordedDtype adapter)
    if isComponent adapter then toDtype (componentValues adapter) d
    else baseMaterialize adapter dtype

The method materializes a view as an array of a definite element data type. The
single load-bearing ``ensures`` pins ``out`` to that grounded model, which pins
THREE independent sub-behaviours:

  * DEFAULT RESOLUTION: a missing requested data type resolves to the view's
    recorded data type — ``d = dtype.getD (recordedDtype adapter)``;
  * COMPONENT RETAG (the discriminating clause): when the view exposes a single
    component of a composite index, its stored values are RETAGGED to the
    resolved data type ``d`` (``toDtype (componentValues adapter) d``), NOT
    returned with the storage's native (possibly promoted) data type. This is
    exactly the reported behaviour — building a composite index must not change
    the element data type of the views it is built from;
  * BRANCH + DELEGATION: the ``isComponent`` branch selects the component path;
    the other path delegates to ``baseMaterialize`` (the inherited non-component
    materialization), and the content (``elems``) rides through unchanged.

THE CARRIER IS LARGELY OPAQUE. ``recordedDtype`` / ``isComponent`` /
``componentValues`` / ``toDtype`` / ``baseMaterialize`` are ``opaque`` free
functions with NO constraining ``axiom`` (mapping.md §3: each is an UNCHANGED
callee the operation invokes but never redefines, so the weakest sufficient
contract asserts nothing about its return; directives 7/8). So no literal input
COMPUTES the post-image, and a witness cannot reduce a concrete result to a
literal. Every reject witness therefore CONDITIONS ON THE CARRIER: it states the
refutation at a point described by a satisfiable hypothesis about the opaque
terms (e.g. ``isComponent 0 = true`` selects the component branch;
``toDtype (componentValues 0) 7 ≠ componentValues 0`` is the sub-domain where
the retag genuinely changes the array). A witness reaches the post-image through
Velvet's monad: ``(arrayDispatch a d).run`` is ``DivM.res (<impl at a,d>)`` and
the witness asserts it differs from ``DivM.res (arrayMaterialize a d)``. It is
checked in a file whose ``prove_correct`` block is stripped, so no tactic script
can mask the verdict. Each single/double hypothesis is JOINTLY SATISFIABLE (the
gate's consistency probe cannot derive ``False`` from them — verified
out-of-band); one hypothesis per opaque term, never two about the same term.

TWO INPUT BINDERS: ``adapter`` (the opaque view handle — all five observations
are functions of it) and ``dtype`` (the optionally-requested data type). Both
are load-bearing and both are VARIED by the reject witnesses (pts = 5):
``dtype`` ranges over ``{some 7, none}`` and ``isComponent adapter`` over
``{true, false}``, so the battery demonstrates the spec's dependence on the
requested-vs-default resolution AND on the component-vs-delegate branch, rather
than pinning either. (Directive on ``getD``-masking: because on the modeled
domain a component view's materialization is only ever requested with the
DEFAULT — see the DROPPED footer — a rival that merely mis-resolves the explicit
request arm is resolve-preserving and dropped; the ``some 7`` point is instead
probed by the storage-leak rival, which ignores the resolved data type ENTIRELY
and so is a true break at both ``some`` and ``none``.)

WHICH VALUE the missing request resolves to is pinned SEPARATELY, by
``weak-default-from-storage`` (added by audit). Dropping the explicit-request
rival as resolve-preserving is right, but it left the DEFAULTED arm — the one
the failing tests actually drive — attacked by nothing: ``weak-storage-leak``
omits the retag entirely, so it cannot distinguish a retag aimed at the wrong
resolution from one aimed at the right one. A rival that retags CORRECTLY but
defaults to the stored values' own data type instead of the view's recorded one
was measured to be REJECTED, closing that gap.

ADVERSARIAL READ of the nagini classes on this carrier:

  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded model directly; or reorder
    the branch to test the delegate path first) must still verify against the
    byte-identical obligation, else the spec is SPEC-TOO-STRONG on the shape of
    the impl. Both reshapes were verified out-of-band with real builds.

  * ADMISSIBILITY — APPLIES, and is now PORTED (``admiss-component-defaulted``,
    added by the second audit). The nagini sibling self-asserts that a normal
    F2P-shaped input satisfies the read-only half-permission precondition. It is
    true that this backend has NO ``require`` clause (pre-conditions region
    empty), so the literal "the precondition admits this input" probe has no
    analogue. But the analogue ON A TOTAL CARRIER is the obligation being
    UNSATISFIABLE or DEGENERATE at an F2P-shaped input, and that is directly
    testable here — the earlier claim that "an in-region assert could only pin an
    un-decidable claim about the opaque terms" is FALSE and is retracted. An
    assert may condition on the carrier exactly as the reject witnesses do, and
    ``simp_all [arrayMaterialize]`` then discharges it by UNFOLDING the post-image
    rather than by deciding anything about the opaque values. Measured: the case
    verifies (EXIT 0) and each of its three conjuncts is load-bearing — replacing
    any one with a claim false on this carrier leaves an unsolved goal (EXIT 1).

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries this MANDATORY: its ``level_values`` input is held at a fractional
    heap permission (``Acc(list_pred(.),1/2)``), and a rival that WRITES it
    (``level_values.append(0)`` / an in-place index store) must be rejected for
    INSUFFICIENT PERMISSION. Lean/Velvet are referentially transparent:
    ``adapter`` and ``dtype`` are immutable values declared read-only (none
    ``mut``), there is no heap, no aliasing, no ``Old``, and no permission
    system. There is no read-only input to overwrite and no frame clause to
    violate, so the class has no carrier analogue. Not fabricated (porting map:
    this class is vacuous on a referentially-transparent backend).

  * DIVERGENCE / non-termination - the class is INAPPLICABLE to this impl and
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

  * UNGROUNDED-ORACLE ECHO — N/A. ``arrayMaterialize`` is a total ``def`` over
    the method's own inputs (the ``axioms`` region declares no answer key); a
    wrong impl cannot echo an opaque term to pass without doing the work. The
    cheapest correct impl computes the model honestly (the direct positive
    control), which is correct, not a cheat.

  * UNIQUENESS / SPEC-TOO-WEAK rivals — EXPRESSIBLE despite the opaque carrier
    (the load-bearing finding of this port). Conditioning on the carrier makes
    the component-retag and delegation clauses attackable: the FIVE reject cases
    below re-express the nagini storage-leak, value-corruption, and (added)
    delegation and default-resolution rivals, each refuted at a distinct
    conditioned point.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's
job, and this bundle declares NO consumed ``axiom`` (the five callees are opaque
A-reference deep-model references validated == the real callees by
axiom_check.py; mapping.md §3 records the G-AX pass). This gate ignores
``AXIOM_TESTS`` regardless. See the footer.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7393"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct arrayDispatch
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the default-resolve `let`, the
# component/delegate branch, and the return). Every variant swaps on this block.
_IMPL = (
    "    let d : Dtype := dtype.getD (recordedDtype adapter)\n"
    "    let result : MatArray :=\n"
    "      if isComponent adapter then\n"
    "        toDtype (componentValues adapter) d\n"
    "      else\n"
    "        baseMaterialize adapter dtype\n"
    "    return result")
assert _BASE.count(_IMPL) == 1, "arrayDispatch impl region drifted from expected text"

# The frozen prove_correct tactic body (elided from the spec view; unique).
_PROOF = (
    "prove_correct arrayDispatch by\n"
    "  loom_solve\n"
    "  simp_all [arrayMaterialize]")
assert _BASE.count(_PROOF) == 1, "prove_correct arrayDispatch tactic body drifted"


def _impl(new_impl, proof=_PROOF):
    """Full Solution.lean with the impl body (and optionally the proof) replaced."""
    src = _swap(_BASE, _IMPL, new_impl)
    if proof != _PROOF:
        src = _swap(src, _PROOF, proof)
    return src


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on the SHAPE of the impl. Both verified out-of-band with
    # real builds (EXIT 0).
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no intermediate `let`/branch bindings — maximally different from the
        # gold two-step build. `out` IS `arrayMaterialize adapter dtype`, so the
        # ensures holds by reflexivity. The branch is gone, so the frozen proof's
        # `simp_all [arrayMaterialize]` line is unneeded (it would report "No
        # goals"); the residual closes under `loom_solve` alone.
        "module": _impl(
            "    return arrayMaterialize adapter dtype",
            proof="prove_correct arrayDispatch by\n  loom_solve"),
        "rationale": "the post-image `arrayMaterialize adapter dtype` is GROUNDED "
                     "in the inputs (a total def, no opaque answer key), so "
                     "`return arrayMaterialize adapter dtype` is the honest "
                     "cheapest CORRECT impl. It MUST verify — the clause is "
                     "literally `out = arrayMaterialize adapter dtype` — else the "
                     "single postcondition clause is SPEC-TOO-STRONG. Also shows "
                     "the spec is not echo-vulnerable: any wrong constant/echo "
                     "fails `out = arrayMaterialize adapter dtype`. (Nagini: "
                     "pos-effective-type-direct — compute the resolution via the "
                     "grounded model directly.)",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the DELEGATE path first (via `!isComponent`) and put the
        # component-retag arm second — semantically identical to the gold branch
        # order, different source. Keeps the default-resolve `let` verbatim. The
        # proof adds a `cases isComponent adapter <;> simp_all` arm to close the
        # reshaped branch. Verified out-of-band (EXIT 0).
        "module": _impl(
            "    let d : Dtype := dtype.getD (recordedDtype adapter)\n"
            "    let result : MatArray :=\n"
            "      if !isComponent adapter then\n"
            "        baseMaterialize adapter dtype\n"
            "      else\n"
            "        toDtype (componentValues adapter) d\n"
            "    return result",
            proof="prove_correct arrayDispatch by\n"
                  "  loom_solve\n"
                  "  simp_all [arrayMaterialize]\n"
                  "  cases isComponent adapter <;> simp_all"),
        "rationale": "structurally different CORRECT reshape: test the delegate "
                     "path first (`!isComponent`) and put the component-retag arm "
                     "second — the two branches are the same two sub-domains in "
                     "the opposite textual order, so `out = arrayMaterialize "
                     "adapter dtype` still holds on the whole domain. The proof "
                     "adds a `cases isComponent adapter` arm (elided tactic body, "
                     "in scope). A faithful reshape MUST verify, else the "
                     "postcondition is over-fit to the branch order => "
                     "SPEC-TOO-STRONG. (Nagini: pos-branch-reorder — resolve the "
                     "branch in the opposite order.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE and NON-DEGENERATE at an
    # F2P-shaped input. There is no `require` clause here, so the nagini
    # "precondition admits this input" probe has no literal analogue; the analogue
    # on a TOTAL carrier is the obligation being unsatisfiable or degenerate at
    # exactly an F2P-shaped point, which this case discharges as an in-region
    # `assert` BEFORE closing the frozen obligation verbatim. The point is the one
    # the failing tests drive: a component view, request DEFAULTED. The assert
    # conditions on the carrier the same way the reject witnesses do, and
    # `simp_all [arrayMaterialize]` discharges it by UNFOLDING the post-image, not
    # by deciding anything about the opaque values. All three conjuncts are LIVE
    # (measured: replacing any one with a claim false on this carrier leaves an
    # unsolved goal, EXIT 1); the impl is kept BYTE-VERBATIM so the method's own
    # `ensures` still discharges, and only the elided tactic body is retuned.
    # =====================================================================
    {
        "id": "admiss-component-defaulted",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      ((isComponent adapter = true →\n"
            "          arrayMaterialize adapter none\n"
            "            = toDtype (componentValues adapter) (recordedDtype adapter)) ∧\n"
            "       (isComponent adapter = true →\n"
            "          toDtype (componentValues adapter) (recordedDtype adapter)\n"
            "            ≠ componentValues adapter →\n"
            "          arrayMaterialize adapter none ≠ componentValues adapter) ∧\n"
            "       (isComponent adapter = false →\n"
            "          arrayMaterialize adapter dtype = baseMaterialize adapter dtype)))\n"
            + _IMPL,
            proof="prove_correct arrayDispatch by\n"
                  "  loom_solve\n"
                  "  all_goals simp_all [arrayMaterialize]"),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at the "
                     "F2P-shaped input — a component view with the request "
                     "DEFAULTED — and the assert pins that at three independent "
                     "points, each measured LIVE. (i) SATISFIABLE / correctly "
                     "AIMED: on `isComponent adapter = true`, `dtype = none`, the "
                     "post-image really is `toDtype (componentValues adapter) "
                     "(recordedDtype adapter)`, i.e. the retag aimed at the view's "
                     "RECORDED data type — so the clause the failing tests drive "
                     "is reachable, not an obligation no impl can meet. (ii) "
                     "NON-DEGENERATE: on the sub-domain where the retag genuinely "
                     "changes the array, the post-image is NOT the bare stored "
                     "values, so the spec does not collapse to the identity on the "
                     "very sub-domain the change is about. (iii) the delegate arm "
                     "is likewise reachable and is exactly `baseMaterialize "
                     "adapter dtype`. If any conjunct failed, the obligation would "
                     "be unsatisfiable or degenerate at an in-domain input => "
                     "PRECOND-TOO-STRONG in the total-carrier sense. The impl is "
                     "kept byte-verbatim so the `ensures` discharges too; only the "
                     "elided tactic body is retuned (`all_goals`) to clear the "
                     "extra assert goal. (Nagini: admiss-precond-halfperm — "
                     "re-derived as satisfiability+non-degeneracy, since the "
                     "half-permission precondition itself has no analogue.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT conditioned input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing tests. Each witness
    # CONDITIONS on the opaque carrier (no literal computes the post-image) and
    # reaches the post-image via `(arrayDispatch a d).run = DivM.res (…)`. Every
    # hypothesis set is jointly satisfiable (consistency probe: EXIT nonzero).
    # =====================================================================
    {
        "id": "weak-storage-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported bug: in the component branch return the stored values
        # DIRECTLY, escaping with the storage's native (promoted) data type
        # instead of retagging to the resolved `d`. This is the pre-patch level
        # branch verbatim. Correct on the delegate sub-domain; WRONG on every
        # component view whose stored values' data type differs from the resolved
        # one — the exact behaviour the fix repairs.
        "module": _impl(
            "    let result : MatArray :=\n"
            "      if isComponent adapter then\n"
            "        componentValues adapter\n"
            "      else\n"
            "        baseMaterialize adapter dtype\n"
            "    return result"),
        "refinement": "this is exactly the pre-patch behaviour: on a single "
                      "component of a composite index, return the stored values "
                      "as-is, tagged with the storage's native (promoted) data "
                      "type rather than retagged to the resolved recorded/"
                      "requested type. It is the reported defect: building a "
                      "composite index changes the element data type of the "
                      "component views. Its faithful real counterpart is the empty "
                      "change — precisely the state the failing tests fail on "
                      "(they assert the materialized component keeps its declared "
                      "sub-64-bit data type, but the promoted storage yields the "
                      "wider one), so it would NOT resolve. A verifying rival is a "
                      "genuine verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `out = arrayMaterialize adapter dtype` via the "
                     "COMPONENT-RETAG clause: the spec forces `toDtype "
                     "(componentValues adapter) d`, the rival returns the bare "
                     "`componentValues adapter`, which differ on the sub-domain "
                     "where the retag changes the array. Refuted at `adapter = 0`, "
                     "`dtype = some 7`, conditioned on the satisfiable "
                     "`isComponent 0 = true` (selects the component branch) and "
                     "`toDtype (componentValues 0) 7 ≠ componentValues 0` (the "
                     "retag genuinely changes the array). This probes the `dtype = "
                     "some` point AND varies the binder: the rival ignores the "
                     "resolved data type ENTIRELY, so it is a true break whether "
                     "the request is explicit or defaulted. If it VERIFIES => "
                     "SPEC-TOO-WEAK (the storage-leak the fix repairs left "
                     "unpinned). (Nagini: weak-storage-leak.)",
        "witness":
            "example (h1 : isComponent 0 = true)\n"
            "    (h2 : toDtype (componentValues 0) (7 : Int) ≠ componentValues 0) :\n"
            "    (arrayDispatch 0 (some 7)).run ≠ DivM.res (arrayMaterialize 0 (some 7)) := by\n"
            "  simp only [arrayDispatch, arrayMaterialize, Option.getD, h1, if_true]\n"
            "  intro heq\n"
            "  injection heq with hh\n"
            "  exact h2 hh.symm\n",
    },
    {
        "id": "weak-delegate-instead-of-base",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the BRANCH + DELEGATION clause: in the NON-component branch,
        # return `componentValues adapter` instead of delegating to
        # `baseMaterialize adapter dtype`. Correct on every component view; WRONG
        # on the delegate sub-domain (where the two callees disagree). Drives
        # `isComponent = false` — the branch value the storage-leak rival never
        # exercises.
        "module": _impl(
            "    let d : Dtype := dtype.getD (recordedDtype adapter)\n"
            "    let result : MatArray :=\n"
            "      if isComponent adapter then\n"
            "        toDtype (componentValues adapter) d\n"
            "      else\n"
            "        componentValues adapter\n"
            "    return result"),
        "refinement": "delegating the non-component path to the component's stored "
                      "values instead of the inherited base materialization "
                      "returns the wrong array whenever the view is the whole "
                      "composite index rather than one of its components: the base "
                      "path already resolves the default and casts correctly, "
                      "while the component values carry the storage's native data "
                      "type and a different content. A faithful counterpart that "
                      "short-circuited the inherited path would break "
                      "materialization of the non-component views the P2P suite "
                      "reads (stack/unstack/sel/copy over the whole index), so it "
                      "would NOT resolve. Correct on every component view.",
        "rationale": "REJECT from `out = arrayMaterialize adapter dtype` via the "
                     "DELEGATION clause: on `isComponent adapter = false` the spec "
                     "forces `baseMaterialize adapter dtype`, the rival returns "
                     "`componentValues adapter`, which differ when the two callees "
                     "disagree. Refuted at `adapter = 2`, `dtype = none`, "
                     "conditioned on `isComponent 2 = false` (selects the delegate "
                     "branch) and `componentValues 2 ≠ baseMaterialize 2 none` "
                     "(the callees disagree there). Drives `isComponent = false`, "
                     "the branch value no other rival probes, so the branch binder "
                     "is varied. If it VERIFIES => SPEC-TOO-WEAK (the delegation "
                     "left unpinned). (ADDED: this bundle models the "
                     "component-vs-delegate dispatch as an explicit clause the "
                     "nagini sibling — which modeled only the component branch — "
                     "had no counterpart for.)",
        "witness":
            "example (h1 : isComponent 2 = false)\n"
            "    (h2 : componentValues 2 ≠ baseMaterialize 2 none) :\n"
            "    (arrayDispatch 2 none).run ≠ DivM.res (arrayMaterialize 2 none) := by\n"
            "  simp only [arrayDispatch, arrayMaterialize, Option.getD, h1, if_false,\n"
            "             Bool.false_eq_true]\n"
            "  intro heq\n"
            "  injection heq with hh\n"
            "  exact h2 hh\n",
    },
    {
        "id": "weak-default-from-storage",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the DEFAULT RESOLUTION clause at its LOAD-BEARING arm. The
        # retag IS applied (so the storage-leak rival's defect is absent) but the
        # value it resolves the MISSING request to is taken from the stored
        # values' own native data type instead of the view's RECORDED one. On
        # `dtype = none` — the arm the failing tests drive — this reproduces the
        # reported symptom through a subtler route than weak-storage-leak: the
        # result is correctly retagged, just retagged to the wrong resolution.
        # Correct wherever the request is explicit, and correct on the delegate
        # sub-domain; wrong exactly on the defaulted component arm.
        "module": _impl(
            "    let d : Dtype := dtype.getD (componentValues adapter).dtype\n"
            "    let result : MatArray :=\n"
            "      if isComponent adapter then\n"
            "        toDtype (componentValues adapter) d\n"
            "      else\n"
            "        baseMaterialize adapter dtype\n"
            "    return result"),
        "refinement": "resolving a MISSING request to the data type the stored "
                      "values happen to be held under, rather than to the view's "
                      "recorded data type, reproduces the reported symptom on the "
                      "exact domain the failing tests drive (no explicit request, "
                      "a component view whose storage is held at a wider data "
                      "type): the materialized array comes back tagged with the "
                      "storage's data type. Its faithful real counterpart "
                      "therefore does NOT resolve — the failing tests assert the "
                      "materialized component keeps its declared sub-64-bit data "
                      "type and would still observe the wider one. Distinct from "
                      "the storage-leak rival: that one omits the retag, this one "
                      "performs it and mis-resolves its target, so a fix that "
                      "only added a retag without fixing the default would still "
                      "be caught here.",
        "rationale": "REJECT from `out = arrayMaterialize adapter dtype` via the "
                     "DEFAULT RESOLUTION clause: the spec forces `d = dtype.getD "
                     "(recordedDtype adapter)`, so on `dtype = none` the resolved "
                     "data type is `recordedDtype adapter`; the rival resolves it "
                     "to `(componentValues adapter).dtype`, which the carrier "
                     "constrains in no way and which the modeled behaviour says "
                     "may differ. Refuted at `adapter = 4`, `dtype = none`, "
                     "conditioned on the satisfiable `isComponent 4 = true` "
                     "(selects the component branch) and `toDtype (componentValues "
                     "4) (componentValues 4).dtype ≠ toDtype (componentValues 4) "
                     "(recordedDtype 4)` (the two resolutions genuinely disagree "
                     "there — one hypothesis per opaque term). This is the ONLY "
                     "rival that pins WHICH value the missing request resolves "
                     "to: if it VERIFIES the default-resolution clause is unpinned "
                     "=> SPEC-TOO-WEAK. (ADDED by audit: the nagini "
                     "`partial-ignore-requested` was dropped as resolve-preserving "
                     "on the EXPLICIT-request arm, which is correct, but that left "
                     "the DEFAULTED arm — the one the failing tests actually "
                     "drive — with no rival at all.)",
        "witness":
            "example (h1 : isComponent 4 = true)\n"
            "    (h2 : toDtype (componentValues 4) (componentValues 4).dtype ≠\n"
            "          toDtype (componentValues 4) (recordedDtype 4)) :\n"
            "    (arrayDispatch 4 none).run ≠ DivM.res (arrayMaterialize 4 none) := by\n"
            "  simp only [arrayDispatch, arrayMaterialize, Option.getD, h1, if_true]\n"
            "  intro heq\n"
            "  injection heq with hh\n"
            "  exact h2 hh\n",
    },
    {
        "id": "weak-value-extra-element",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct data type, but the materialized content carries one extra
        # trailing element. Attacks the value-copy facet (the `elems` carried
        # through unchanged): the retag is applied, then a stray element is
        # appended. Refuted at a component view with `dtype = none`.
        "module": _impl(
            "    let d : Dtype := dtype.getD (recordedDtype adapter)\n"
            "    let result : MatArray :=\n"
            "      if isComponent adapter then\n"
            "        let base := toDtype (componentValues adapter) d\n"
            "        { base with elems := base.elems ++ [0] }\n"
            "      else\n"
            "        baseMaterialize adapter dtype\n"
            "    return result"),
        "refinement": "the materialization preserves the content and length of the "
                      "stored values; a component path that emits an extra "
                      "trailing element produces an array of the wrong length. The "
                      "P2P suite reads the materialized values (shape / "
                      "element-equality checks over the stacked coordinate), so an "
                      "over-long array diverges from gold and would NOT resolve. "
                      "Correct on the delegate sub-domain and on the data type; "
                      "the divergence is purely in the carried content.",
        "rationale": "REJECT from `out = arrayMaterialize adapter dtype` via the "
                     "value-copy facet: the spec forces the component result to be "
                     "exactly `toDtype (componentValues adapter) d`, whose `elems` "
                     "are carried through unchanged; the rival appends `[0]`, so "
                     "the `elems` differ by one element. Refuted at `adapter = 1`, "
                     "`dtype = none`, conditioned on `isComponent 1 = true` "
                     "(selects the component branch — the sole hypothesis, so "
                     "trivially satisfiable). `(elems ++ [0]) ≠ elems` is a pure "
                     "list fact needing no assumption about the opaque content. If "
                     "it VERIFIES => SPEC-TOO-WEAK (the content-preservation left "
                     "unpinned). (Nagini: value-extra-element.)",
        "witness":
            "example (h1 : isComponent 1 = true) :\n"
            "    (arrayDispatch 1 none).run ≠ DivM.res (arrayMaterialize 1 none) := by\n"
            "  simp only [arrayDispatch, arrayMaterialize, Option.getD, h1, if_true]\n"
            "  intro heq\n"
            "  injection heq with hh\n"
            "  have he := congrArg MatArray.elems hh\n"
            "  simp at he\n",
    },
    {
        "id": "weak-value-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct data type, but the materialized content drops its last element.
        # A distinct value-corruption shape from weak-value-extra-element (a
        # different content defect), refuted at a distinct component view. Needs a
        # conditioning hypothesis that the content is non-empty at the probed
        # point (dropLast changes it) — one hypothesis per opaque term.
        "module": _impl(
            "    let d : Dtype := dtype.getD (recordedDtype adapter)\n"
            "    let result : MatArray :=\n"
            "      if isComponent adapter then\n"
            "        let base := toDtype (componentValues adapter) d\n"
            "        { base with elems := base.elems.dropLast }\n"
            "      else\n"
            "        baseMaterialize adapter dtype\n"
            "    return result"),
        "refinement": "dropping the last element of the materialized content emits "
                      "an array shorter than the stored values, so the component "
                      "view would be missing its last label. The P2P suite reads "
                      "the materialized values (shape / element-equality over the "
                      "stacked coordinate), so a truncating counterpart diverges "
                      "from gold and would NOT resolve. Correct on the delegate "
                      "sub-domain and on the data type; a distinct content defect "
                      "from the extra-element rival.",
        "rationale": "REJECT from `out = arrayMaterialize adapter dtype` via the "
                     "value-copy facet: the spec forces the component `elems` to "
                     "be `(toDtype (componentValues adapter) d).elems`; the rival "
                     "returns `.dropLast`. Refuted at `adapter = 3`, `dtype = "
                     "none`, conditioned on the satisfiable `isComponent 3 = true` "
                     "(selects the component branch) and `elems ≠ elems.dropLast` "
                     "(the content is non-empty there, so dropLast changes it — "
                     "the only sub-domain where the truncation is observable). A "
                     "DISTINCT input point from the extra-element rival (different "
                     "adapter, opposite content defect). If it VERIFIES => "
                     "SPEC-TOO-WEAK. (Nagini: value-drop-last.)",
        "witness":
            "example (h1 : isComponent 3 = true)\n"
            "    (h2 : (toDtype (componentValues 3) (recordedDtype 3)).elems ≠\n"
            "          (toDtype (componentValues 3) (recordedDtype 3)).elems.dropLast) :\n"
            "    (arrayDispatch 3 none).run ≠ DivM.res (arrayMaterialize 3 none) := by\n"
            "  simp only [arrayDispatch, arrayMaterialize, Option.getD, h1, if_true]\n"
            "  intro heq\n"
            "  injection heq with hh\n"
            "  have he := congrArg MatArray.elems hh\n"
            "  simp only at he\n"
            "  exact h2 he.symm\n",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The nagini sibling ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 2 MANDATORY frame-mutation rivals, 3
# uniqueness/partial-domain rivals) plus a 1-case AXIOM lane. The nagini surface
# contracts `materialize_level(requested, declared, storage_type, level_values)`
# — the whole level-materialization with an explicit dense value-copy loop over a
# read-only `List[int]` held at a fractional permission. This bundle contracts
# ONE method `arrayDispatch (adapter : Int) (dtype : Option Dtype)`, pinning
# `out = arrayMaterialize adapter dtype` over an OPAQUE view handle whose five
# observations are opaque callees with no axiom. Both surfaces model the SAME
# behaviour (materialize a component view to the resolved recorded/requested data
# type, never the storage's native one); this backend refines the per-label value
# loop into an opaque `componentValues`/`toDtype`/`elems` observation (mapping.md
# §2) and folds nagini's `requested`/`declared`/`storage_type` int-codes into the
# `Option Dtype` request + the opaque `recordedDtype adapter`.
#
#   nagini case                 kind          -> here                          disposition
#   ------------------------------------------------------------------------------------------
#   pos-branch-reorder          soundness     -> pos-branch-reorder            PORTED
#   pos-effective-type-direct   soundness     -> pos-direct-model              PORTED
#   admiss-precond-halfperm     admissibility -> admiss-component-defaulted    PORTED (audit 2)
#   frame-mutate-append         uniqueness    -> (none)                        VACUOUS
#   frame-mutate-index-store    uniqueness    -> (none)                        VACUOUS
#   weak-storage-leak           uniqueness    -> weak-storage-leak             PORTED
#   partial-ignore-requested    uniqueness    -> (none)                        DROPPED (resolve-preserving)
#   value-extra-element         uniqueness    -> weak-value-extra-element      PORTED
#   value-drop-last             uniqueness    -> weak-value-drop-last          PORTED
#   (added, delegation clause)  uniqueness    -> weak-delegate-instead-of-base ADDED
#   (added, default resolution) uniqueness    -> weak-default-from-storage     ADDED (audit)
#   AXIOM_TESTS (1 A-reference) axiom         -> (none)                        N/A (G-AX)
#
# 2 soundness ported + 1 admissibility ported + 3 uniqueness ported + 2 uniqueness
# added = 8 velvet cases (2 soundness, 1 admissibility, 5 uniqueness).
#
# PORTED — soundness (2): pos-effective-type-direct -> pos-direct-model (return
#   the grounded `arrayMaterialize adapter dtype` directly; the branch is gone so
#   the proof closes under `loom_solve` alone). pos-branch-reorder ->
#   pos-branch-reorder (test the delegate path first via `!isComponent`; the
#   proof adds a `cases isComponent adapter` arm). Both build against a real
#   `lake env lean` (EXIT 0).
# PORTED — uniqueness (3): weak-storage-leak -> weak-storage-leak (the pre-patch
#   level branch: return `componentValues adapter` raw, escaping with the
#   storage's native data type). Refuted at (adapter 0, some 7) by conditioning on
#   `isComponent 0 = true` and `toDtype (componentValues 0) 7 ≠ componentValues 0`
#   — it ignores the resolved data type entirely, so it also serves as the `dtype
#   = some` probe. value-extra-element -> weak-value-extra-element (append a
#   trailing element to the component content). value-drop-last ->
#   weak-value-drop-last (drop the last element). Both value rivals attack the
#   content-preservation facet at distinct component views (adapter 1 with a
#   single sat hypothesis; adapter 3 conditioned on non-empty content). All three
#   witnesses verified out-of-band: rival ELABORATES (EXIT 0), gold FAILS (EXIT
#   1), hypotheses jointly satisfiable (consistency probe EXIT nonzero).
# ADDED — uniqueness (1): weak-delegate-instead-of-base. This bundle models the
#   component-vs-delegate dispatch as an explicit clause (`if isComponent … else
#   baseMaterialize …`, mapping.md §1) that the nagini `materialize_level` — which
#   modeled ONLY the level (component) branch — had no counterpart for. A rival
#   that returns `componentValues` on the delegate path attacks that clause;
#   refuted at (adapter 2, none) by conditioning on `isComponent 2 = false` and
#   `componentValues 2 ≠ baseMaterialize 2 none`. This is the ONLY witness driving
#   `isComponent = false`, so it makes the branch binder load-bearing.
# ADDED — uniqueness (1), by AUDIT: weak-default-from-storage. Pins WHICH value the
#   MISSING request resolves to: the rival applies the retag correctly but aims it
#   at `(componentValues adapter).dtype` instead of `recordedDtype adapter`.
#   Refuted at (adapter 4, none) by conditioning on `isComponent 4 = true` and
#   `toDtype (componentValues 4) (componentValues 4).dtype ≠ toDtype
#   (componentValues 4) (recordedDtype 4)`. Rebuilt during the audit: rival
#   ELABORATES (EXIT 0), gold FAILS semantically (EXIT 1, an Application type
#   mismatch on the two distinct resolutions — not a missing name), consistency
#   probe cannot derive False (EXIT 1), and the rival itself is REJECTED by the
#   frozen spec (EXIT 1, unsolved `getD (componentValues adapter).dtype = getD
#   (recordedDtype adapter)`). Closes the gap the DROPPED note below left open:
#   dropping the explicit-request rival is correct, but it is NOT true that the
#   default-resolution facet was covered by the `dtype = none` witnesses — every
#   pre-audit `none` witness holds the resolution fixed and varies something else.
# DROPPED — uniqueness (1), recorded not silently omitted: partial-ignore-requested
#   (nagini `res.etype = declared` unconditionally, ignoring the explicit
#   `requested`). On this carrier the analogue is a rival that resolves the
#   component data type to `recordedDtype adapter` REGARDLESS of an explicit
#   `dtype = some d`. It is refutable by conditioning at (isComponent = true, dtype
#   = some d, `toDtype _ d ≠ toDtype _ (recordedDtype …)`) — BUT its faithful real
#   counterpart is RESOLVE-PRESERVING: measured against the real adapter, a single
#   component of a composite index has its materialization requested ONLY with the
#   DEFAULT on the F2P and P2P domains — the materialization is never requested
#   with an explicit data type on a component view — so a patch that mishandled
#   ONLY the explicit-request arm still resolves. Rejecting it would be a break in
#   the WRONG direction (an artifact of the carrier discretising a distinction the
#   real behaviour is invariant under, not evidence of SPEC-TOO-WEAK). DROPPED. The
#   `dtype` binder is instead varied HONESTLY by weak-storage-leak, whose rival
#   ignores the resolved data type entirely and so is a true break at `dtype = some`
#   as well as `none`.
# PORTED — admissibility (1), by AUDIT 2: admiss-component-defaulted. The nagini
#   case relied on the half-permission Requires `Acc(list_pred(level_values),1/2)`
#   admitting a normal F2P-shaped input, and that MECHANISM has no analogue: no
#   method here has a `require` clause (pre-conditions region empty), so there is
#   no precondition to admit. The port stopped there and recorded the whole lane
#   VACUOUS. That was WRONG, and its stated reason — "an in-region assert could
#   only pin an un-decidable claim about the opaque observations" — is measurably
#   false and is retracted. The analogue on a TOTAL carrier is the obligation being
#   UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input, and an in-region
#   assert tests that directly without deciding anything about the opaque values:
#   it CONDITIONS on the carrier exactly as the reject witnesses do (`isComponent
#   adapter = true`, and for the non-degeneracy conjunct a hypothesis that the
#   retag changes the array), and `simp_all [arrayMaterialize]` discharges it by
#   UNFOLDING the post-image. Measured: the case VERIFIES (EXIT 0), the frozen impl
#   is kept byte-verbatim so the `ensures` still discharges, and each of the three
#   conjuncts is LIVE — replacing (i) the resolution target with the bare stored
#   values, (ii) the non-degeneracy `≠` with `=`, or (iii) the delegate arm's callee
#   each leaves an unsolved goal (EXIT 1). So the lane is not vacuous here; it was
#   an effort gap, and it is the lane that detects PRECOND-TOO-STRONG.
# VACUOUS — frame/permission-mutation (2): frame-mutate-append and
#   frame-mutate-index-store write to the read-only `level_values` held at a
#   fractional permission (`level_values.append(0)` / an in-place index store),
#   rejected by Nagini for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent, has no heap and no aliasing, and declares NO `mut` binder —
#   `adapter`/`dtype` are immutable values with no heap footprint. There is no
#   read-only input to overwrite and no substitute probe (the per-label values are
#   folded into the opaque `componentValues`/`elems` observation, not a mutable
#   container). No substitute fabricated (porting map: vacuous on a
#   referentially-transparent backend).
# AXIOM_TESTS (1): dropped. The axiom lane is G-AX's job. This bundle consumes NO
#   axiom `ensures` — the five callees are opaque A-reference deep-model references
#   validated == their real counterparts (the conversion, the component-values
#   read, and the inherited base materialization) by
#   axiom_check.py (mapping.md §3, G-AX pass recorded in meta.json). This gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = arrayMaterialize
#   adapter dtype` has TWO input binders — `adapter : Int` (the opaque view; its
#   five observations are functions of it) and `dtype : Option Dtype` — over three
#   independently-attackable facets (DEFAULT RESOLUTION / COMPONENT RETAG /
#   BRANCH + DELEGATION + value copy). The five reject witnesses probe five DISTINCT
#   input points (pts = 5):
#     * weak-storage-leak             adapter 0, dtype = some 7  (component retag,
#                                       dtype = some)
#     * weak-delegate-instead-of-base adapter 2, dtype = none    (delegation,
#                                       isComponent = false)
#     * weak-value-extra-element      adapter 1, dtype = none    (value copy)
#     * weak-value-drop-last          adapter 3, dtype = none    (value copy, other
#                                       defect)
#     * weak-default-from-storage     adapter 4, dtype = none    (DEFAULT RESOLUTION
#                                       — which value `getD` selects)
#   So `dtype` ranges over {some 7, none} and is shown load-bearing by
#   weak-storage-leak (the `some` point, where the rival ignores the resolved
#   type entirely — a true break). `isComponent adapter` ranges over {true, false}
#   and is shown load-bearing by weak-delegate-instead-of-base (the sole `false`
#   point). The COMPONENT RETAG facet is attacked by weak-storage-leak, the
#   DELEGATION facet by weak-delegate-instead-of-base, and the value-copy facet by
#   both value rivals. The DEFAULT RESOLUTION facet is attacked by
#   weak-default-from-storage, the only rival that varies WHICH value `getD`
#   selects. (Pre-audit this facet was claimed to be "exercised through the `dtype
#   = none` witnesses"; that claim was FALSE and is retracted — merely evaluating
#   `getD` at `none` does not attack it, since every one of those rivals resolves
#   to `recordedDtype adapter` exactly as the spec demands and diverges elsewhere.)
#   Both positive controls defend the whole obligation. No binder is pinned at a
#   single value across the reject set, and no two rivals share an input point.
#
# AUDIT 3 — INDEPENDENT RE-DERIVATION (36 real builds; nothing shipped changed
#   except the two prose corrections below: a STALE divergence citation that the
#   tree-wide total-correctness migration invalidated, and a stale reject count).
#   * All 8 modules rebuilt: 3 positives EXIT 0, 5 rivals EXIT 1, frozen control
#     EXIT 0. Attack A re-run: every case's statement lines (method header,
#     `ensures`, `prove_correct` header) are byte-identical to frozen; scope ok.
#   * All 5 witnesses rebuilt (rival 0 / gold 1 / probe 1), signatures matching
#     the recorded `gold_signature`s exactly.
#   * FORGERY (B′) re-run independently for all five, BOTH halves. FLIP: gold
#     EXIT 0 (the `=` claim is provable there, closed by `rfl`) while each rival
#     EXIT 1 with `Tactic 'rfl' failed: NonDetT.run (pure <rival term>) is not
#     definitionally equal to DivM.res <spec term>` — the two sides answer
#     OPPOSITELY, so the exit code carries information about the claim. REVEAL
#     (`exact (hh : Nat)`): on gold the hypothesis prints reflexive (`toDtype
#     (componentValues 0) 7 = toDtype (componentValues 0) 7`) or `True` for the
#     two value rivals, i.e. `simp` PROVED the equation for gold; against each
#     rival it prints the CONCRETE unproven equation (`componentValues 0 =
#     toDtype (componentValues 0) 7`; `componentValues 2 = baseMaterialize 2
#     none`; `toDtype … (componentValues 4).dtype = toDtype … (recordedDtype 4)`;
#     `….elems ++ [0] = ….elems`; `….elems.dropLast = ….elems`). No case is
#     hollow; every rejection tracks its claim.
#   * ADMISSIBILITY re-measured (the case the previous audit payload never
#     examined — it recorded only 7 cases and omitted this one). Verifies EXIT 0,
#     and all three conjuncts confirmed LIVE by independent mutation: aiming (i)
#     at the bare stored values, flipping (ii)'s `≠` to `=`, and swapping (iii)'s
#     callee each leave an unsolved `admiss_1` goal (EXIT 1).
#   * NEW attack-D wrong impls, all REJECTED (EXIT 1), aimed at what the shipped
#     rivals leave alone: retag the DELEGATE's output in the component arm;
#     double-retag through the storage dtype; branch on the REQUEST instead of
#     `isComponent`; component arm drops an explicit request; correct tag with
#     the delegate's `elems`; content REVERSED (a permutation, not a length
#     change — the facet both value rivals miss, since each changes length). No
#     new spec hole in the too-weak direction.
#   * NEW attack-E correct reshapes: `Option.elim` in place of `getD` (EXIT 0),
#     two `return`s with no `let` (EXIT 0), and the branch routed through a local
#     `Bool → MatArray` lambda (EXIT 0 once the proof splits the branch —
#     `split <;> simp_all [arrayMaterialize]`; a first attempt failed and was a
#     PROOF gap of mine, not a spec hole, which is why it is reported as verified
#     rather than as a finding).
# AUDIT NOTE — the delegate branch is pinned INTENSIONALLY, not extensionally.
#   Measured: an impl whose ONLY change is passing the already-resolved data type
#   to the delegate (`baseMaterialize adapter (some d)` in place of
#   `baseMaterialize adapter dtype`) is REJECTED (EXIT 1, residual goal
#   `baseMaterialize adapter (some (recordedDtype adapter)) = baseMaterialize
#   adapter none`). That residual is not provable here because `baseMaterialize`
#   is `opaque` and NOTHING asserts it resolves a missing request to the recorded
#   data type — a fact the axioms region documents in PROSE (and mapping.md §3.3
#   records against the real callee) but never states as an obligation. The
#   modeled behaviour holds the two calls equal, so this is a spec that rejects a
#   faithful reshape. It is recorded as a SPEC finding by the audit rather than
#   patched here: closing it means asserting that fact about `baseMaterialize`,
#   which is an edit to the frozen axioms region and must re-clear the equivalence
#   and leakage gates. It does not make any shipped case unsound — every case
#   above earns its outcome — and it does not affect the component branch, which
#   is where the modeled change lives.
# WITNESS DISCRIMINATION (verified during authoring, and INDEPENDENTLY REBUILT for
#   all five reject cases during the audit — rival EXIT 0, gold EXIT 1, consistency
#   probe EXIT 1, for every one): each witness ELABORATES against its rival (EXIT 0)
#   and FAILS against the frozen solution (EXIT 1). Each gold-side failure was read
#   and is a SEMANTIC refutation of the concrete claim (an Application type mismatch
#   between the rival's and the spec's terms, or an unsolved `False` goal) — not a
#   missing identifier, a type error in the statement, an unfolding failure, or a
#   timeout. Each conditioning hypothesis set is
#   jointly satisfiable (the `False`-from-hypotheses probe cannot close: EXIT
#   nonzero); at most one hypothesis per opaque term, never two about the same
#   term. No `sorry`/`admit`/`native_decide`/`axiom`/`opaque` appears in any
#   witness.
# FORGERY TEST (audit 2). None of the five gold-side signatures is a plain
#   evaluation, so each was additionally subjected to the two-build forgery test —
#   reading an error and judging it "semantic" is not evidence. Both halves were
#   run for all five, and both say the gold exit code TRACKS THE CLAIM:
#     * FLIP the claim (assert `=` where the witness asserts `≠`). On the frozen
#       solution the flipped claim is PROVABLE (EXIT 0, closed by `simp only […] ;
#       rfl`): gold's post-image reduces to `run (pure X) = res X` for the very X
#       the witness said it differed from. Against each rival the SAME flipped
#       claim is NOT provable (EXIT 1), the residual being gold's term vs the
#       rival's. So the two sides answer OPPOSITELY on the flipped claim — the
#       exit code carries information about what is claimed, and a witness
#       asserting gold is CORRECT there would NOT have been recorded as a
#       rejection.
#     * REVEAL the type (replace the closing step with a deliberate type ascription
#       on the load-bearing hypothesis, so Lean prints its REAL type). On the frozen
#       solution the hypothesis is reflexive (`toDtype … 7 = toDtype … 7`,
#       `baseMaterialize 2 none = baseMaterialize 2 none`, …) or `True` for the two
#       value rivals — i.e. `simp` PROVED the equation for gold. Against each rival
#       the same hypothesis is the CONCRETE unproven equation (`componentValues 0 =
#       toDtype (componentValues 0) 7`; `componentValues 2 = baseMaterialize 2
#       none`; `toDtype … (componentValues 4).dtype = toDtype … (recordedDtype 4)`;
#       `{elems := … ++ [0], …}.elems = ….elems`; `….elems.dropLast = ….elems`).
#       That pair is a genuine refutation, not a syntactic accident: the two
#       largest signature classes here (`Application type mismatch … reflexive
#       hypothesis` and `Invalid field symm … has type True`) are established real
#       by exactly this contrast.
AXIOM_TESTS = []
