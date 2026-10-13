"""properties.py — G-PBT falsification battery for django__django-11551 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct listDisplayItemCheck`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  listDisplayItemCheck
      (isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M : Bool)
      return (out : CheckResult)
    ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises
                                         modelAttrRaises fieldIsM2M

The method classifies ONE entry of a model-administration display configuration
into ``ok`` / ``e108`` / ``e109`` as a pure decision over five boolean
observations passed by value. There is NO heap state, NO ``mut`` binder, and NO
opaque answer-key: the sole ``ensures`` pins the output to the concrete ``pure``
function ``listDisplayItemOutcome``, which is fully unfolded over the five
inputs, so there is no ungrounded oracle to echo. The decision reads (with
``early = isCallable || hasAttrObj``):

  (A) early                                              => ok
  (C) not early and not getFieldRaises                   => e109 if fieldIsM2M else ok   (registry route)
  (D) not early and getFieldRaises and not modelAttrRaises => e109 if fieldIsM2M else ok (attr route)
  (E108) not early and getFieldRaises and modelAttrRaises  => e108

So this spec is exhaustive and pins the output UNIQUELY on every one of the 2^5
reachable combinations. The live attack surface is therefore PARTIAL-DOMAIN and
CONTROL-FLOW rivals that get one sub-domain wrong (the F2P sub-domain above all):
an early-accept dropped, a resolution route gated behind the wrong observation,
the E109 m2m test dropped on one route, or the E108 route collapsed. Each reject
rival carries the refinement argument that its faithful real counterpart would
NOT resolve the F2P.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):

  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. Lean and Velvet are
    referentially transparent: every parameter is an immutable value, this
    bundle declares no ``mut`` binder, there is no heap and no aliasing. There
    is no read-only input to overwrite and no permission system to trip, so the
    sibling's directive-5 frame-mutation class has no counterpart. No substitute
    is fabricated.
  * TERMINATION / NON-TERMINATION - the class is INAPPLICABLE to this impl and
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
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``listDisplayItemOutcome`` applied to the method's own five arguments, a
    concrete ``def`` in the ``pure`` region (the ``axioms`` region is empty;
    there is no opaque callee). The unique satisfier IS the grounded decision,
    so there is no wrong echo to build; the honest controls are the cheapest
    faithful reshapes (the ``pos-*`` cases).
  * CARRIER COLLAPSE — the sibling separates the many-to-many observation into
    TWO independent flags, one per resolution route (``structural_is_relation``
    for the registry hit, ``attribute_is_relation`` for the attribute fallback).
    This backend collapses them into the SINGLE ``fieldIsM2M`` observation,
    because the real code applies one shared ``isinstance(field, ...)`` test to
    whichever field was resolved (mapping.md §2). So the sibling's
    ``reject-wrong-source-relation-C`` (which reads the OTHER route's relation
    flag) is not expressible here — there is no other flag to read; it is
    VACUOUS on this carrier (see footer). Its adversarial intent — that the
    E109 verdict must be driven by the resolved field on EACH route — is carried
    instead by two rivals that drop the m2m test on each route separately.
  * PARTIAL-DOMAIN / CONTROL-FLOW — heavily exercised. A rival can be correct on
    most of the observation cube yet diverge on a sub-domain: the pre-image gate
    is right whenever the model-class attribute resolves but wrong exactly on the
    F2P shape (registry hit, attribute access fails); the route-collapse rivals
    are right on their own route but drop the other.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE: its
extracted program reduces fully under ``decide``. Each reject rival carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``listDisplayItemCheckTester <5 bools> = false`` at ONE concrete input, checked
in a file whose ``prove_correct`` block has been stripped so no tactic script
can mask the verdict. ``CheckResult`` already ``deriving DecidableEq`` in the
frozen spec, so the tester derivation needs no added instance and the witnesses
introduce no ``axiom`` / ``sorry`` / ``native_decide``. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
its rival and FAILS (``decide`` proves the proposition false) against the frozen
solution, so each rejection is a genuine spec refutation and not mechanical
tactic breakage. Every witness states its refutation at literal booleans, so no
witness binds a hypothesis and the consistency probe is vacuous for all of them.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; the five boolean inputs are R-refinements of the real observations
(callable / hasattr / field-registry lookup / attribute access / relation kind),
validated by ``conformance_check.py`` (G-CONF), not axiomatized. Nothing in the
proof rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11551"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes, the elided `prove_correct`
# tactic body), so the spec view is untouched and same_spec holds by
# construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- An invokable entry, or one that is an attribute of the administrator, is\n"
    "    -- acceptable outright. Otherwise resolve the entry to a model field: the\n"
    "    -- field registry first, then attribute access on the model class; only\n"
    "    -- when both fail is the entry unresolvable (E108). Whenever a field is\n"
    "    -- resolved by either route, it is acceptable unless it is a many-to-many\n"
    "    -- relation (E109).\n"
    "    let result : CheckResult :=\n"
    "      if isCallable then CheckResult.ok\n"
    "      else if hasAttrObj then CheckResult.ok\n"
    "      else if getFieldRaises then\n"
    "        (if modelAttrRaises then CheckResult.e108\n"
    "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
    "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
    "    return result\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. Every soundness reshape below re-verifies with the
# SAME `loom_solve` (checked out-of-band), so no case retunes it; rivals leave it
# as-is (the rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct listDisplayItemCheck by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `listDisplayItemCheckTester <5 bools> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. `CheckResult`
# ---- already derives `DecidableEq` in the frozen spec, so no instance is added.
_TESTER = (
    "extract_program_for listDisplayItemCheck\n"
    "prove_precondition_decidable_for listDisplayItemCheck\n"
    "prove_postcondition_decidable_for listDisplayItemCheck\n"
    "derive_tester_for listDisplayItemCheck\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the ok/e108/e109 value identical on
    # every input and only reshapes the executable surface; the reproof stays
    # the frozen `loom_solve` (checked out-of-band), so the proof body is left
    # byte-identical.
    # =====================================================================
    {
        "id": "pos-control-fused-early",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: fuse the two early-accept branches into one disjunction
        # (`isCallable || hasAttrObj`), then resolve exactly as the frozen impl.
        # Same outcome on every input.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable || hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108\n"
            "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "rationale": "fusing the two mutually-independent early-accept branches "
                     "into one disjunction computes the SAME ok/e108/e109 verdict "
                     "on every input (either accept short-circuits to `ok`, and "
                     "the resolution below is untouched), so "
                     "`out = listDisplayItemOutcome ...` still holds; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on early-accept "
                     "structure.",
    },
    {
        "id": "pos-control-shared-m2m-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist the shared many-to-many verdict into one typed local
        # `m2m` and reuse it on BOTH resolution routes, mirroring the real code's
        # single shared isinstance test. Same value flow on every input.
        "module": _impl(
            "    let m2m : CheckResult :=\n"
            "      if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108 else m2m)\n"
            "      else m2m\n"
            "    return result"),
        "rationale": "hoisting the many-to-many verdict into one shared local "
                     "reused on both resolution routes leaves the ok/e108/e109 "
                     "output identical on every input (the m2m test is the same "
                     "on whichever route resolved the field), so "
                     "`out = listDisplayItemOutcome ...` is unchanged; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on how the two "
                     "routes' m2m test is factored.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the decision is
    # DEGENERATE at the interesting point — a decision that never separated the
    # F2P accept-case from the neighbouring E108 case would read like a live one.
    # This case discharges an in-region assert pinning that the modeled decision
    # genuinely forks on the F2P boundary: an entry whose registry lookup
    # succeeds (non-m2m) but whose model-class attribute access fails is `ok`,
    # while the neighbouring case where the registry ALSO fails is `e108`. The
    # rest of the impl is kept verbatim so the method's own obligation still
    # discharges; the frozen `loom_solve` closes the assert VC too (checked
    # out-of-band).
    # =====================================================================
    {
        "id": "admiss-f2p-shape-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (listDisplayItemOutcome false false false true false = CheckResult.ok ∧\n"
            "       listDisplayItemOutcome false false true true false = CheckResult.e108))\n"
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108\n"
            "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "rationale": "the decision is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: an entry the registry resolves "
                     "(non-relation) whose model-class attribute access fails is "
                     "accepted (`= ok`), yet the neighbouring case where the "
                     "registry ALSO fails is `= e108`, so the resolution really "
                     "does fork on that boundary — exactly the F2P observation. "
                     "The in-region assert must discharge (else the boundary would "
                     "be degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that ELABORATES against
    # the rival and FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # Argument order of every tester call:
    #   isCallable  hasAttrObj  getFieldRaises  modelAttrRaises  fieldIsM2M
    # =====================================================================
    {
        "id": "reject-prepatch-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # THE F2P BUG. Gate the field-registry consultation behind
        # `not modelAttrRaises`: when model-class attribute access fails the
        # entry is condemned `e108` WITHOUT ever consulting the registry. This is
        # the pre-image skeleton (Solution_prepatch.lean).
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if modelAttrRaises then CheckResult.e108\n"
            "      else if getFieldRaises then CheckResult.ok\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "refinement": "this IS the pre-patch behaviour: the entry is only "
                      "considered for field resolution when model-class attribute "
                      "access succeeds, so an entry whose registry lookup would "
                      "have succeeded but whose class-level attribute access fails "
                      "(the issue's field descriptor that raises on class access) "
                      "is wrongly condemned instead of accepted. Its faithful real "
                      "counterpart is the unchanged repo, which reports E108 on "
                      "that field, so the F2P test — which reports exactly that "
                      "field and asserts it is ACCEPTED — still fails. It would "
                      "NOT resolve; the precise change the spec senses (G-DIFF).",
        "rationale": "REJECT from the ensures on the F2P sub-domain "
                     "{not early, not getFieldRaises, modelAttrRaises}: the "
                     "post-image demands `ok`/`e109` from the registry-resolved "
                     "field, but the rival returns `e108`. Refuted at the F2P "
                     "shape (registry hit, non-m2m, attribute access fails), the "
                     "point where the fix changes the verdict.",
        "witness": _witness(
            "listDisplayItemCheckTester false false false true false"),
    },
    {
        "id": "reject-registry-miss-to-108",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse the attribute-fallback route: whenever the registry lookup
        # fails, return `e108` immediately, ignoring the attribute fallback
        # entirely. Correct only when BOTH routes fail; wrong when the registry
        # misses but attribute access resolves the entry.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then CheckResult.e108\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "refinement": "dropping the attribute-access fallback is what a real "
                      "patch that condemned E108 on the first (registry) failure "
                      "would do — it REVERSES the very addition being tested (the "
                      "fallback that resolves an entry the registry does not "
                      "know). Any entry resolvable only via class-level attribute "
                      "access is then wrongly condemned, diverging from gold on "
                      "the attribute-resolved sub-domain, so it would NOT resolve.",
        "rationale": "REJECT from the ensures on {not early, getFieldRaises, "
                     "not modelAttrRaises}: the post-image resolves the entry via "
                     "the attribute route (`ok`/`e109`), but the rival returns "
                     "`e108`. Refuted at (registry miss, attribute access "
                     "succeeds, non-m2m) — the attribute-resolved cell the "
                     "fallback is for.",
        "witness": _witness(
            "listDisplayItemCheckTester false false true false false"),
    },
    {
        "id": "reject-drop-e109-registry-route",
        "kind": "uniqueness",
        "expect": "reject",
        # ROUTE-SPECIFIC E109 drop (registry hit). On the registry-resolved route
        # the many-to-many test is dropped: a field the registry resolves as a
        # many-to-many relation is accepted instead of reported E109. Carries the
        # sibling's wrong-source-relation intent on the registry route.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108\n"
            "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
            "      else CheckResult.ok\n"
            "    return result"),
        "refinement": "skipping the isinstance(field, ManyToManyField) test on "
                      "the registry-resolved field would accept a many-to-many "
                      "field reachable via the registry (emit [] instead of "
                      "admin.E109), diverging from gold on the E109 sub-domain of "
                      "the registry route, so it would NOT resolve.",
        "rationale": "REJECT from the ensures on {not early, not getFieldRaises, "
                     "fieldIsM2M}: the post-image demands `e109` for a registry-"
                     "resolved many-to-many field, but the rival returns `ok`. "
                     "Refuted at (registry hit, fieldIsM2M) — varies `fieldIsM2M` "
                     "true, the binder the decision rivals hold false.",
        "witness": _witness(
            "listDisplayItemCheckTester false false false false true"),
    },
    {
        "id": "reject-drop-e109-attr-route",
        "kind": "uniqueness",
        "expect": "reject",
        # ROUTE-SPECIFIC E109 drop (attribute fallback). On the attribute-resolved
        # route the many-to-many test is dropped: a field reachable only via
        # class-level attribute access that is a many-to-many relation is accepted
        # instead of reported E109. Carries the sibling's wrong-source-relation
        # intent on the attribute route — the counterpart the carrier collapse
        # merged with the registry route in the sibling's SINGLE rival, split here
        # so BOTH routes' m2m dependence is demonstrated.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108 else CheckResult.ok)\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "refinement": "the real patch hoists the isinstance(field, "
                      "ManyToManyField) test so it applies to the field obtained "
                      "from EITHER route; skipping it on the attribute-resolved "
                      "field would accept a many-to-many field reachable only via "
                      "class-level attribute access (emit [] instead of "
                      "admin.E109), diverging from gold on the attribute-m2m "
                      "sub-domain, so it would NOT resolve.",
        "rationale": "REJECT from the ensures on {not early, getFieldRaises, "
                     "not modelAttrRaises, fieldIsM2M}: the post-image demands "
                     "`e109` for an attribute-resolved many-to-many field, but the "
                     "rival returns `ok`. Refuted at (registry miss, attribute "
                     "access succeeds, fieldIsM2M) — the attribute route's m2m "
                     "cell, distinct from the registry route's above.",
        "witness": _witness(
            "listDisplayItemCheckTester false false true false true"),
    },
    {
        "id": "reject-drop-hasattr-accept",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the hasAttrObj early accept. An entry naming an attribute of the
        # administrator itself, otherwise unresolvable, is then wrongly condemned
        # E108 instead of accepted. Attacks clause (A) via the `hasAttrObj` binder.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108\n"
            "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "refinement": "the real code returns [] immediately when the entry names "
                      "an attribute of the administrator instance (a method / "
                      "custom-callable display entry); dropping that early accept "
                      "would emit admin.E108 for a valid administrator attribute "
                      "that resolves to no model field, failing the P2P valid "
                      "cases that exercise such entries. It would NOT resolve.",
        "rationale": "REJECT from the ensures on clause (A) via `hasAttrObj`: "
                     "the post-image demands `ok` whenever `hasAttrObj` holds, but "
                     "on an administrator attribute that is otherwise unresolvable "
                     "the rival returns `e108`. Refuted at (hasAttrObj, both "
                     "resolution routes fail) — varies `hasAttrObj` true, the "
                     "binder every other rival holds false.",
        "witness": _witness(
            "listDisplayItemCheckTester false true true true false"),
    },
    {
        "id": "reject-drop-callable-accept",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the isCallable early accept. An invokable entry, otherwise
        # unresolvable, is then wrongly condemned E108 instead of accepted.
        # Attacks clause (A) via the `isCallable` binder — the only rival that
        # varies it.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then CheckResult.e108\n"
            "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "refinement": "the real code returns [] immediately when the entry is "
                      "itself an invokable object; dropping that early accept "
                      "would emit admin.E108 for a valid callable display entry "
                      "that resolves to no model field, failing the P2P valid "
                      "cases that exercise callable entries. It would NOT resolve.",
        "rationale": "REJECT from the ensures on clause (A) via `isCallable`: "
                     "the post-image demands `ok` whenever `isCallable` holds, but "
                     "on a callable entry that is otherwise unresolvable the rival "
                     "returns `e108`. Refuted at (isCallable, both resolution "
                     "routes fail) — the only witness that varies `isCallable` "
                     "true.",
        "witness": _witness(
            "listDisplayItemCheckTester true false true true false"),
    },
    {
        "id": "reject-unresolvable-reads-m2m",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult the relation observation on the UNRESOLVABLE path. When both
        # resolution routes fail there is no field, so the relation observation is
        # immaterial there and the entry must be reported `e108` regardless of it.
        # This rival reads it anyway and reports `e109` when it happens to hold.
        # No other rival attacks this clause: the two E109-drop rivals both hold
        # `modelAttrRaises` false (a field IS resolved), and the three rivals that
        # reach the unresolvable cell all hold `fieldIsM2M` false, so the cell
        # {both routes fail, fieldIsM2M} was reached by no witness at all.
        "module": _impl(
            "    let result : CheckResult :=\n"
            "      if isCallable then CheckResult.ok\n"
            "      else if hasAttrObj then CheckResult.ok\n"
            "      else if getFieldRaises then\n"
            "        (if modelAttrRaises then\n"
            "           (if fieldIsM2M then CheckResult.e109 else CheckResult.e108)\n"
            "         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)\n"
            "      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok\n"
            "    return result"),
        "refinement": "on the unresolvable path no field object exists — both "
                      "the registry lookup and the attribute access failed — so "
                      "there is nothing to apply the relation test to. A real "
                      "counterpart would have to test the relation kind of a "
                      "value it never obtained; reporting admin.E109 there "
                      "instead of admin.E108 changes the reported error id for an "
                      "entry that names nothing at all, diverging from gold on "
                      "the unresolvable sub-domain. It would NOT resolve.",
        "rationale": "REJECT from the ensures on the E108 clause "
                     "{not early, getFieldRaises, modelAttrRaises, fieldIsM2M}: "
                     "the post-image demands `e108` on the unresolvable path "
                     "irrespective of the relation observation, but the rival "
                     "returns `e109`. This pins that the relation observation is "
                     "genuinely IMMATERIAL on that path (mapping.md §2) rather "
                     "than merely unread by the frozen impl — the one cell of the "
                     "cube no other witness reaches.",
        "witness": _witness(
            "listDisplayItemCheckTester false false true true true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness) and an empty AXIOM lane. Every one
# is accounted for below. The sibling models the same pure decision over SIX
# booleans (its two early-accepts plus a PER-ROUTE relation flag pair,
# structural_is_relation / attribute_is_relation); this backend models the same
# decision over FIVE booleans, collapsing the two relation flags into the single
# `fieldIsM2M` (the real code's one shared isinstance test, mapping.md §2). The
# decision surface carries across intact; the only sibling case that does not
# survive the collapse is the wrong-source-relation rival, and its intent is
# re-expressed as two route-specific E109-drop rivals.
#
#   sibling case                     -> here                             disposition
#   ------------------------------------------------------------------------------
#   pos-control-fused-early          -> pos-control-fused-early          PORTED
#   pos-control-inline-m2m           -> pos-control-shared-m2m-local     PORTED (reshaped)
#   admiss-f2p-shape                 -> admiss-f2p-shape-nondegenerate   RE-AIMED
#   reject-prepatch-gate             -> reject-prepatch-gate             PORTED
#   reject-wrong-source-relation-C   -> (none)                          VACUOUS (carrier collapse)
#   reject-drop-e109-on-attr-path    -> reject-drop-e109-attr-route      PORTED
#   reject-structural-absent-to-108  -> reject-registry-miss-to-108      PORTED
#   reject-drop-presenter-accept     -> reject-drop-hasattr-accept       PORTED
#   (no sibling)                     -> reject-drop-e109-registry-route  ADDED (route coverage)
#   (no sibling)                     -> reject-drop-callable-accept      ADDED (isCallable binder)
#   (no sibling)                     -> reject-unresolvable-reads-m2m    ADDED (E108-path immateriality)
#
# 5 ported, 1 re-aimed, 1 vacuous; 3 rivals added for binder / route / clause
# coverage.
#
# VACUOUS (reject-wrong-source-relation-C): the sibling's rival reads the OTHER
#   resolution route's relation flag (attribute_is_relation on the structural
#   branch), which is only wrong when the two flags DISAGREE. This backend has a
#   SINGLE relation observation `fieldIsM2M` — the real code applies one shared
#   isinstance test to whichever field was resolved, so there is no second flag
#   to read and no disagreement to exploit. DEMONSTRATED, not asserted: perform
#   the sibling's substitution on this carrier (on the registry branch, replace
#   the relation flag it reads with "the other route's" relation flag) and the
#   substitution is the IDENTITY — the resulting impl text is byte-identical to
#   the frozen impl region, so the "rival" is the frozen solution and would have
#   to VERIFY. It is therefore not merely hard to land, it is not a rival at all
#   on this carrier: an expect="reject" case built from it would be vacuous, and
#   the honest disposition is to drop it. Its adversarial intent, that the E109
#   verdict must be driven by the resolved field on EACH route, is carried
#   instead by reject-drop-e109-registry-route and reject-drop-e109-attr-route,
#   which drop the m2m test on each route separately.
# FRAME/PERMISSION-MUTATION: the sibling has no frame-mutation rival (the
#   defended-surface prose records the class as N/A there too — pure scalar
#   decision, no heap, no Acc). Referential transparency makes it vacuous here
#   as well; nothing to port.
# TERMINATION / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
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
# RE-AIMED (admissibility): the sibling's admissibility case discharges an Assert
#   that the (trivial) precondition admits a normal F2P-shaped input. This
#   backend's method has NO precondition, so that probe is degenerate (every
#   input is in-domain). It is re-aimed at the residual total-domain risk — that
#   the decision is DEGENERATE at the F2P boundary — via an in-region assert that
#   the modeled decision genuinely forks there (registry hit + attr-access-fails
#   => ok; registry-also-fails => e108).
# PORTED-RESHAPED (pos-control-shared-m2m-local): the sibling's second positive
#   inlines the m2m test PER branch (no shared local). This backend instead
#   hoists the m2m verdict into ONE shared local reused on both routes — the
#   dual reshape, and the one that mirrors the real code's single shared
#   isinstance test. Same outcome on every input; the reproof is the frozen
#   `loom_solve`.
# ADDED (reject-drop-e109-registry-route): the registry-route half of the
#   split-out wrong-source-relation intent (see VACUOUS above). Demonstrates the
#   spec's E109 dependence on `fieldIsM2M` via the registry route specifically,
#   varying `fieldIsM2M` true where the decision rivals hold it false.
# ADDED (reject-drop-callable-accept): the sibling never drops the isCallable
#   early accept (only the presenter/hasattr one), so no sibling rival varies the
#   isCallable observation. Without this rival `isCallable` would be held false by
#   every witness — a binder no rival was built to abuse. This rival drops the
#   callable accept and is refuted at (isCallable, otherwise unresolvable), the
#   only witness with `isCallable = true`.
#
# BINDER / CLAUSE COVERAGE of the seven reject witnesses over the five input
#   binders of the sole ensures (pts = 7 distinct input points):
#     isCallable      — true only in reject-drop-callable-accept; false in the
#                       other six: VARIED (the sole rival attacking it).
#     hasAttrObj      — true only in reject-drop-hasattr-accept; false in the
#                       other six: VARIED (the sole rival attacking it).
#     getFieldRaises  — false (prepatch, drop-e109-registry) / true (registry-
#                       miss-to-108, drop-e109-attr, drop-hasattr, drop-callable,
#                       unresolvable-reads-m2m): VARIED.
#     modelAttrRaises — true (prepatch, drop-hasattr, drop-callable,
#                       unresolvable-reads-m2m) / false (registry-miss-to-108,
#                       drop-e109-registry, drop-e109-attr): VARIED.
#     fieldIsM2M      — true (drop-e109-registry, drop-e109-attr,
#                       unresolvable-reads-m2m) / false (the other four): VARIED,
#                       and all three of those rivals' divergence from the spec
#                       DEPENDS on it being true.
#   Every independent clause of the post-image is attacked: both early accepts
#   (drop-callable / drop-hasattr, clause A), each resolution route's E109 test
#   (drop-e109-registry / drop-e109-attr, clauses C/D), the E108 route
#   (registry-miss-to-108), the E108 path's INDEPENDENCE from the relation
#   observation (unresolvable-reads-m2m, the E108 clause), and the F2P pre-image
#   gate (prepatch).
#
#   The variation is MEANINGFUL, not two spellings of one point: each of the
#   seven witness points is a cell where the frozen decision and that rival
#   disagree (verified by enumerating the 32-point cube for every rival — each
#   rival differs from the frozen decision on 1-5 cells and its witness sits on
#   one of them), and each rival's witness is the ONLY witness in the battery at
#   that point.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (the five inputs are R-refinements checked by
# G-CONF), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
