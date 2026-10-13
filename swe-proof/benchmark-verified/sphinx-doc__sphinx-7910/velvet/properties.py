"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7910 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct inclusionDecisionM`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  inclusionDecisionM (ctx : Context) (name : List Char) (target : DocTarget)
      (incInit incSpecial incPrivate : Bool) return (out : Decision)
    ensures out = inclusionDecision ctx name target incInit incSpecial incPrivate

The method decides, for one documentable target, whether the builder is told to
FORCE its inclusion (``Decision.forceInclude``) or to leave the default
disposition in place (``Decision.noOverride``). The single load-bearing
``ensures`` pins ``out`` to the deep, fully-unfolded ``inclusionDecision`` (the
``axioms`` region is empty — no opaque answer key to echo). That model composes
several independently-attackable gates, all transparent on this carrier:

  * CONSIDERED gate — the target is examined only when its leaf name is not the
    weak-reference slot AND it carries documentation text (``hasDoc``) AND its
    context is one of the considered kinds (``isConsidered ctx``); otherwise the
    default stands.
  * OWNERSHIP gate — for a bodied context (class / exception) ownership is
    established against the scope in which the target is genuinely DEFINED
    (``resolvedScope``, which sees through a wrapper standing in for an
    underlying object), NOT the scope of the target exactly as presented
    (``directScope``). A whole-unit context needs no owner. For a multi-segment
    container path the single-scope lookup defers to the recorded attribute-chain
    walk (``ownerViaPathWalk``).
  * CATEGORY gate — with ownership established, an ENABLED inclusion category for
    the leaf (initializer / dunder-special / single-underscore-private, each
    gated by its ``inc*`` flag) forces inclusion; otherwise the default stands.

INPUT BINDERS of the spec predicate: ``ctx``, ``name``, ``target`` (whose fields
``hasDoc`` / ``qualifiedName`` / ``ownerViaPathWalk`` / ``directScope`` /
``resolvedScope`` each feed a gate), ``incInit``, ``incSpecial``, ``incPrivate``.
The reject witnesses below drive these to nine DISTINCT input points so the
manifest demonstrates the post-image's dependence on WHICH scope settles
ownership (the fix's core), on the documentation gate, on the weak-reference
guard, on the multi-segment defer, and on each inclusion category and its flag —
not on a single pinned shape.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``inclusionDecisionMTester … = false`` says the
extracted program's result violates the postcondition at that concrete input)
and closes by ``decide``, checked in a file whose ``prove_correct`` block has
been stripped so no tactic script can mask the verdict. The postcondition is an
equality on ``Decision`` (a two-constructor enum with ``DecidableEq``), and both
the frozen impl and every rival below are LOOP-FREE branch decisions over the
pure helpers, so the extracted tester reduces to ``isTrue``/``isFalse`` on a
concrete literal input and ``decide`` closes. Every scope / name / flag argument
is a concrete literal (``List Char`` / ``List (List Char × Bool)`` / ``Bool``),
so no term is opaque and no conditioning on the carrier is required. Both halves
of every witness were checked with ``scripts/lean_verify.sh``: each elaborates
green against its rival and is refuted (``decide`` proves the tester equals
``true``, contradicting the ``= false`` claim) against the frozen solution.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical impls (return the grounded model directly; flatten
    the nested branches into a single conjunctive guard) MUST verify, else the
    spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method has NO ``require`` clause (total domain), so the
    sibling's "a normal input satisfies the precondition" probe is degenerate
    here. Re-aimed at the residual admissibility risk — a DEGENERATE post-image:
    an in-region ``assert`` pins three distinct outcomes at F2P-shaped inputs (a
    documented owned initializer with the init category enabled forces inclusion;
    the same with the category disabled leaves the default; the same with no
    owner leaves the default), proving the modeled behaviour genuinely varies.
    The impl is kept verbatim so the method's own obligation still discharges.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries a
    MANDATORY frame-mutation rival because its read-only member object is held at
    a fractional heap permission (``Acc(.,1/2)``) an impl can illegally overwrite.
    Lean/Velvet are referentially transparent: ``target`` is an immutable
    ``DocTarget`` value declared read-only (not ``mut``), there is no heap, no
    aliasing and no permission system, so there is no read-only input to
    overwrite and no frame clause to trip. The class has no carrier analogue and
    is NOT ported (fabricating a substitute would test nothing). See the footer.
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
  * AXIOM lane — EMPTY. The bundle declares no ``axiom`` (mapping.md §3: the
    changed op — the namespace consulted by the ownership lookup — is modeled
    deeply and structurally as the ``directScope`` vs ``resolvedScope`` fields
    and the ``scopeOwns`` / ``ownerIn`` helpers, validated by G-CONF, so G-AX is
    a documented skip). The sibling's ``AXIOM_TESTS`` are dropped: the axiom lane
    is G-AX's job and this gate ignores them regardless.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``inclusionDecision
    …``, a fully-unfolded ``def`` over the method's own arguments; there is no
    answer-key term a wrong impl could echo. The cheapest correct impl computes
    the decision honestly, which the positive controls cover.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7910"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): one anchor
# ---- lying wholly inside the impl region and unique in Solution.lean (both
# ---- facts asserted at load). Rivals and the direct/flattened positives swap on
# ---- this block; the loop-free branch shape is what makes each witness `decide`.
_IMPL = """    -- impl-start
    if (name != "__weakref__".toList) && target.hasDoc && isConsidered ctx then
      -- Ownership for a bodied context is settled against the scope where the
      -- target is genuinely DEFINED — its resolved scope, which sees through any
      -- wrapper standing in for the underlying object. A whole-unit context needs
      -- no owner.
      let owner := match ctx with
        | Context.classBody     => ownerIn target target.resolvedScope
        | Context.exceptionBody => ownerIn target target.resolvedScope
        | _                     => false
      if (ctx == Context.wholeUnit) || owner then
        if categoryEnabled name incInit incSpecial incPrivate then
          return Decision.forceInclude
        else
          return Decision.noOverride
      else
        return Decision.noOverride
    else
      return Decision.noOverride
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival's reshaped impl retunes it without touching the spec statement or
# ---- dropping the `prove_correct inclusionDecisionM` obligation. Unique.
_PROOF = ("prove_correct inclusionDecisionM by\n"
          "  loom_solve\n"
          "  all_goals simp_all [inclusionDecision]")
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"


def _rewrite_impl(new_block, proof=None):
    """Full variant: whole impl block replaced (proof optionally retuned)."""
    src = _swap(_BASE, _IMPL, new_block)
    return src if proof is None else _swap(src, _PROOF, proof)


# ---- reusable nested-branch skeleton for the branch rivals: only the CONSIDERED
# ---- guard, the OWNER expression and the CATEGORY test vary; the control-flow
# ---- shape is the gold one (so a reject is attributable to the wrong decision,
# ---- surfaced by the witness, not to a reshaped proof).
def _branch_impl(guard, owner_expr, category_expr):
    return ("    -- impl-start\n"
            f"    if {guard} then\n"
            "      let owner := match ctx with\n"
            f"        | Context.classBody     => {owner_expr}\n"
            f"        | Context.exceptionBody => {owner_expr}\n"
            "        | _                     => false\n"
            "      if (ctx == Context.wholeUnit) || owner then\n"
            f"        if {category_expr} then\n"
            "          return Decision.forceInclude\n"
            "        else\n"
            "          return Decision.noOverride\n"
            "      else\n"
            "        return Decision.noOverride\n"
            "    else\n"
            "      return Decision.noOverride\n"
            "    -- impl-end")


_G = '(name != "__weakref__".toList) && target.hasDoc && isConsidered ctx'
_CAT = "categoryEnabled name incInit incSpecial incPrivate"
_OWN = "ownerIn target target.resolvedScope"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `inclusionDecisionMTester … = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped. Every argument is a
# ---- concrete literal so `decide` reduces the (loop-free) extracted rival
# ---- program; no `sorry`/`admit`/`native_decide`.
def _tester(body):
    return ("extract_program_for inclusionDecisionM\n"
            "prove_precondition_decidable_for inclusionDecisionM\n"
            "prove_postcondition_decidable_for inclusionDecisionM\n"
            "derive_tester_for inclusionDecisionM\n\n" + body)


def _b(x):
    return "true" if x else "false"


def _scope(pairs):
    return "[" + ", ".join(f'("{k}".toList, {_b(v)})' for k, v in pairs) + "]"


def _target(has_doc, qn, owner_pw, direct, resolved):
    """A concrete DocTarget literal for a witness input point."""
    return ("{ hasDoc := %s, qualifiedName := \"%s\".toList, "
            "ownerViaPathWalk := %s, directScope := %s, resolvedScope := %s }"
            % (_b(has_doc), qn, _b(owner_pw), _scope(direct), _scope(resolved)))


def _witness(ctx, name, target, inc_init, inc_special, inc_private):
    return _tester(
        f'example : inclusionDecisionMTester {ctx} "{name}".toList {target} '
        f"{_b(inc_init)} {_b(inc_special)} {_b(inc_private)} = false := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on impl shape.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no branching at all — maximally structurally different from the gold
        # nested `if` ladder. `out` IS `inclusionDecision …`, so the ensures holds
        # trivially; `loom_solve` alone discharges it.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return inclusionDecision ctx name target incInit incSpecial incPrivate\n"
            "    -- impl-end",
            "prove_correct inclusionDecisionM by\n  loom_solve"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`inclusionDecision ctx name target incInit incSpecial incPrivate` "
            "directly (no branch ladder). `out` IS that model, so the single "
            "`ensures` holds on the whole domain; the reproof is `loom_solve`. If "
            "this failed to verify the spec would be over-fit to the branch code "
            "shape (SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: "
            "the model IS the real work, so a direct return is correct, not a "
            "cheat. (Sibling: pos-control-reshape — a structurally-different "
            "correct impl.)"),
    },
    {
        "id": "pos-control-flattened-guard",
        "kind": "soundness",
        "expect": "verify",
        # Flatten the three nested gates into one conjunctive guard with a single
        # pair of returns. Observationally identical for every input (the nested
        # `if`s only ever reach `forceInclude` when all three gates pass), so the
        # `ensures` still holds; the frozen `simp_all` proof closes unchanged.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let considered := "
            '(name != "__weakref__".toList) && target.hasDoc && isConsidered ctx\n'
            "    let owner := match ctx with\n"
            "      | Context.classBody     => ownerIn target target.resolvedScope\n"
            "      | Context.exceptionBody => ownerIn target target.resolvedScope\n"
            "      | _                     => false\n"
            "    let ownershipOK := (ctx == Context.wholeUnit) || owner\n"
            "    if considered && ownershipOK "
            "&& categoryEnabled name incInit incSpecial incPrivate then\n"
            "      return Decision.forceInclude\n"
            "    else\n"
            "      return Decision.noOverride\n"
            "    -- impl-end"),
        "rationale": (
            "a correct reshape: the three nested gates (considered / ownership / "
            "enabled category) are folded into ONE conjunctive guard with a single "
            "pair of returns. `forceInclude` is emitted on exactly the same inputs "
            "(all three gates pass) as the nested ladder, so `out = "
            "inclusionDecision …` still holds for every input; the frozen "
            "`simp_all` proof closes unchanged. If it failed to verify the spec "
            "would be SPEC-TOO-STRONG on the shape of the branch nesting. "
            "(Sibling: pos-control-reshape, reshaped to a flattened-guard form.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require`, so the sibling's "a normal
    # input satisfies the precondition" probe is degenerate here. Re-aimed at the
    # residual risk: a DEGENERATE post-image (a spec no impl distinguishes reads
    # exactly like one every impl meets). An in-region `assert`, at three fully
    # concrete F2P-shaped inputs, pins that the post-image is NON-DEGENERATE — a
    # documented owned initializer with the init category enabled forces
    # inclusion, the same with the category DISABLED leaves the default, and the
    # same with NO owner leaves the default: three genuinely distinct decisions.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `adm (\n"
                  '      inclusionDecision Context.classBody "__init__".toList '
                  + _target(True, "C.__init__", False, [], [("C", True)])
                  + " true false false = Decision.forceInclude ∧\n"
                  '      inclusionDecision Context.classBody "__init__".toList '
                  + _target(True, "C.__init__", False, [], [("C", True)])
                  + " false false false = Decision.noOverride ∧\n"
                  '      inclusionDecision Context.classBody "__init__".toList '
                  + _target(True, "C.__init__", False, [], [])
                  + " true false false = Decision.noOverride))\n"),
            _PROOF,
            "prove_correct inclusionDecisionM by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [inclusionDecision]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: a documented owned initializer with the init category enabled "
            "must FORCE inclusion, the same target with the category disabled must "
            "leave the DEFAULT, and the same target with no owner must leave the "
            "DEFAULT — three distinct outcomes turning on the category flag and on "
            "ownership. The in-region assert must discharge (else the obligation is "
            "degenerate / the modeled behaviour constant); the impl is kept "
            "verbatim so `out = inclusionDecision …` still verifies. (Sibling: "
            "admiss-f2p-shaped, re-aimed from precondition admissibility to "
            "post-image non-degeneracy since this backend has no `require` and no "
            "permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and (where the sibling ships one) the refinement
    # argument that its faithful real counterpart would NOT resolve the failing
    # test. Each rival is a loop-free branch decision so its extracted tester
    # `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-ownership-via-direct-scope",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling prepatch-obj-ns: settle ownership against the scope of
        # the target exactly as PRESENTED (directScope) instead of the scope of
        # the object it stands for (resolvedScope). This IS the pre-patch defect —
        # the one operand the change flips. Correct wherever the two scopes agree
        # (an unwrapped target); diverges precisely when a wrapper's own scope
        # misses the owner that the resolved scope recovers.
        "module": _rewrite_impl(
            _branch_impl(_G, "ownerIn target target.directScope", _CAT)),
        "refinement": (
            "this is the pre-change behaviour: ownership is read from the scope of "
            "the target as presented rather than the scope of the object it stands "
            "for. On the F2P member (a documented initializer presented through a "
            "metadata-preserving wrapper whose OWN scope does not contain the "
            "owning container, while the underlying object's scope does), the "
            "wrapper-scope lookup misses the owner, so ownership wrongly fails and "
            "the decision leaves the default (noOverride) — but the test expects "
            "the documented owned initializer to be FORCE-included. A faithful "
            "counterpart with this operand does NOT resolve — it is exactly the bug "
            "the change fixes."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the OWNERSHIP gate: the "
            "spec settles a bodied context's owner against `resolvedScope`, this "
            "rival uses `directScope`. Refuted at an input whose directScope MISSES "
            "the container ([]) while resolvedScope RECOVERS it ([(\"C\", true)]) — "
            "the sole binder distinguishing the fix, held identical to gold by "
            "every other rival. Verifying would be SPEC-TOO-WEAK (the resolved-"
            "scope requirement unpinned). (Sibling: prepatch-obj-ns.)"),
        "witness": _witness(
            "Context.classBody", "__init__",
            _target(True, "C.__init__", False, [], [("C", True)]),
            True, False, False),
    },
    {
        "id": "weak-always-nooverride",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling always-none: the cheapest impl satisfying nothing but
        # "leave the default" — never force inclusion. Fails whenever a
        # documented, owned, enabled-category target must be force-included.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return Decision.noOverride\n"
            "    -- impl-end",
            "prove_correct inclusionDecisionM by\n  loom_solve"),
        "refinement": (
            "always-leave-the-default: a documented owned member in an enabled "
            "category would never be force-included, so the test that expects such "
            "a member to be included FAILS. Does not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the force-inclusion "
            "outcome: when the considered / ownership / enabled-category gates all "
            "pass the spec requires `Decision.forceInclude`, but this returns "
            "`Decision.noOverride`. Refuted at a whole-unit documented dunder "
            "target with the special category enabled (all gates pass, so gold "
            "forces inclusion). Verifying would be SPEC-TOO-WEAK. (Sibling: "
            "always-none.)"),
        "witness": _witness(
            "Context.wholeUnit", "__special__",
            _target(True, "__special__", False, [], []),
            False, True, False),
    },
    {
        "id": "weak-include-if-considered",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling include-if-doc: over-include — force inclusion for ANY
        # considered documented target, dropping BOTH the ownership gate and the
        # enabled-category gate. Correct only where those gates happen to pass.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            f"    if {_G} then\n"
            "      return Decision.forceInclude\n"
            "    else\n"
            "      return Decision.noOverride\n"
            "    -- impl-end"),
        "refinement": (
            "forces inclusion for any considered documented target, including "
            "non-owned targets and targets whose inclusion category is disabled. "
            "The builder would document members it must leave alone (e.g. a "
            "documented member whose category config is off), so the cases that "
            "re-disable a category and expect the default disposition FAIL. Does "
            "not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the CATEGORY gate (and "
            "the ownership gate): when no inclusion category is enabled the spec "
            "requires `Decision.noOverride`, but this returns `Decision.force"
            "Include`. Refuted at an owned documented single-underscore-private "
            "target in an exception body with the private category DISABLED — gold "
            "leaves the default, the rival forces inclusion. Verifying would be "
            "SPEC-TOO-WEAK (the category gate unpinned). (Sibling: include-if-doc.)"),
        "witness": _witness(
            "Context.exceptionBody", "_helper",
            _target(True, "C._helper", False, [("C", True)], [("C", True)]),
            False, False, False),
    },
    {
        "id": "weak-special-only-category",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling partial-special-only: handle only the dunder-special
        # category, dropping init and private. Correct on the special sub-domain;
        # wrong on a documented owned initializer / private with its flag enabled.
        "module": _rewrite_impl(
            _branch_impl(_G, _OWN, "isSpecial name && incSpecial")),
        "refinement": (
            "handles only the dunder-special inclusion category. A documented, "
            "owned initializer with the initializer category enabled — the "
            "original report's exact scenario (a decorated `__init__` that should "
            "be documented) — is left at the default instead of being included. A "
            "faithful counterpart with this body fails the initializer / private "
            "inclusion cases. Does not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` on the initializer / private "
            "sub-domain: the spec forces inclusion there too (via the init / "
            "private conjuncts of `categoryEnabled`), but this returns "
            "`Decision.noOverride`. Refuted at a whole-unit documented initializer "
            "with the init category enabled (gold forces inclusion, the rival "
            "does not). Verifying would be SPEC-TOO-WEAK. (Sibling: "
            "partial-special-only.)"),
        "witness": _witness(
            "Context.wholeUnit", "__init__",
            _target(True, "__init__", False, [], []),
            True, False, False),
    },
    {
        "id": "weak-invert-doc-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling partial-invert-doc: invert the documentation gate —
        # consider a target only when it LACKS documentation text. Mirrors the
        # boundary: handles the documented domain (the only one that can force
        # inclusion) exactly wrong.
        "module": _rewrite_impl(
            _branch_impl(
                '(name != "__weakref__".toList) && !target.hasDoc && isConsidered ctx',
                _OWN, _CAT)),
        "refinement": (
            "inverts the documentation gate, so a target is examined only when it "
            "carries NO documentation text — exactly the members that can never be "
            "force-included — while every documented target is left at the "
            "default. The documented member the test expects to be included yields "
            "the default instead. Does not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the documentation gate: a "
            "documented owned enabled-category target must force inclusion, but the "
            "inverted gate leaves the default for every documented target. Refuted "
            "at a whole-unit UNDOCUMENTED initializer with the init category "
            "enabled: gold leaves the default (undocumented), the rival forces "
            "inclusion — so this witness varies `hasDoc` (held true by every other "
            "rival) and demonstrates it load-bearing. Verifying would be "
            "SPEC-TOO-WEAK. (Sibling: partial-invert-doc.)"),
        "witness": _witness(
            "Context.wholeUnit", "__init__",
            _target(False, "__init__", False, [], []),
            True, False, False),
    },
    {
        "id": "weak-drop-init-category",
        "kind": "uniqueness",
        "expect": "reject",
        # Added coverage (no direct sibling): keep special + private but DROP the
        # initializer conjunct. Isolates the init category, the one the F2P
        # scenario turns on — refuted where only init is enabled. Fields filled
        # by the post-processing loop below (kept out of the literal for clarity).
        "module": None,
        "rationale": None,
    },
    {
        "id": "weak-drop-private-category",
        "kind": "uniqueness",
        "expect": "reject",
        # Added coverage (no direct sibling): keep special + init but DROP the
        # private conjunct. Isolates the private category — refuted where only the
        # private category is enabled on an owned documented private target.
        "module": _rewrite_impl(
            _branch_impl(_G, _OWN,
                         "(isSpecial name && incSpecial) || (isInit name && incInit)")),
        "refinement": (
            "drops the single-underscore-private inclusion category while keeping "
            "special and initializer. A documented, owned private member with the "
            "private category enabled is left at the default instead of being "
            "included, so the private-inclusion case FAILS. Does not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` on the private sub-domain: "
            "the spec forces inclusion for an owned documented private target when "
            "the private category is enabled (the `isPrivate name && incPrivate` "
            "conjunct), but this returns `Decision.noOverride`. Refuted at exactly "
            "that input — held apart from every other rival's witness by varying "
            "`incPrivate` (true here, false or irrelevant elsewhere). Verifying "
            "would be SPEC-TOO-WEAK (the private conjunct unpinned). (Added "
            "coverage: per-category conjunct isolation, beyond the sibling's "
            "special-only rival.)"),
        "witness": _witness(
            "Context.classBody", "_helper",
            _target(True, "C._helper", False, [("C", True)], [("C", True)]),
            False, False, True),
    },
    {
        "id": "weak-drop-weakref-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Added coverage (no direct sibling): drop the weak-reference name guard,
        # so the weak-reference slot is considered like any other name. Isolates
        # that guard, an independent conjunct of the considered gate this carrier
        # models explicitly.
        "module": _rewrite_impl(
            _branch_impl("target.hasDoc && isConsidered ctx", _OWN, _CAT)),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the weak-reference guard: "
            "the spec never examines the weak-reference slot (`name != "
            "\"__weakref__\"` conjunct), so it leaves the default there, but this "
            "rival drops the guard and force-includes a documented owned "
            "weak-reference slot in an enabled category. Refuted at exactly that "
            "input — the only witness driving `name` to the weak-reference slot, so "
            "no other rival exercises this guard. Verifying would be SPEC-TOO-WEAK "
            "(the weak-reference exclusion unpinned). (Added coverage: this "
            "carrier models the weak-reference guard as an explicit conjunct.)"),
        "witness": _witness(
            "Context.classBody", "__weakref__",
            _target(True, "C.__weakref__", False, [("C", True)], [("C", True)]),
            False, True, False),
    },
    {
        "id": "weak-ignore-path-walk-defer",
        "kind": "uniqueness",
        "expect": "reject",
        # Added coverage (no direct sibling): for a multi-segment container path,
        # look the whole path up in the single-scope map directly instead of
        # deferring to the recorded attribute-chain walk. Isolates the
        # `ownerViaPathWalk` binder / the multi-segment branch of `ownerIn`.
        "module": _rewrite_impl(
            _branch_impl(
                _G,
                "scopeOwns target.resolvedScope (containerPath target.qualifiedName)",
                _CAT)),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the multi-segment "
            "ownership defer: for a dotted container path the spec defers to the "
            "recorded attribute-chain walk (`ownerViaPathWalk`), but this rival "
            "looks the whole dotted path up in the single-scope map (which does "
            "not carry the dotted key), wrongly finding no owner. Refuted at a "
            "documented owned initializer with a multi-segment qualified name whose "
            "`ownerViaPathWalk` is true but whose resolvedScope lacks the dotted "
            "key — the only witness driving `ownerViaPathWalk` and a multi-segment "
            "`qualifiedName`. Verifying would be SPEC-TOO-WEAK (the path-walk "
            "branch unpinned). (Added coverage: the `isMultiSegment` branch of "
            "`ownerIn` and the `ownerViaPathWalk` binder.)"),
        "witness": _witness(
            "Context.classBody", "__init__",
            _target(True, "Pkg.C.__init__", True, [], []),
            True, False, False),
    },
    {
        "id": "weak-wholeunit-needs-owner",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit (no sibling): drop the clause that makes a WHOLE-UNIT
        # context establish ownership UNCONDITIONALLY, requiring an owner there
        # too. No other rival attacks that disjunct: every existing witness
        # either sits in a bodied context (where the disjunct is irrelevant) or
        # keeps the disjunct intact, so `(ctx == Context.wholeUnit) || owner`
        # was pinned only on its `owner` side. A whole-unit target has no
        # container to own it, so the rival can never force inclusion there.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            f"    if {_G} then\n"
            "      let owner := match ctx with\n"
            f"        | Context.classBody     => {_OWN}\n"
            f"        | Context.exceptionBody => {_OWN}\n"
            "        | _                     => false\n"
            "      if owner then\n"
            f"        if {_CAT} then\n"
            "          return Decision.forceInclude\n"
            "        else\n"
            "          return Decision.noOverride\n"
            "      else\n"
            "        return Decision.noOverride\n"
            "    else\n"
            "      return Decision.noOverride\n"
            "    -- impl-end"),
        "refinement": (
            "requires an owning container even for a whole-compilation-unit "
            "context, which by construction has none. Every documented "
            "enabled-category target in a whole-unit context is then left at the "
            "default instead of being included, so the whole-unit inclusion "
            "cases FAIL. Does not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the unconditional-"
            "ownership disjunct: the spec establishes ownership for a whole-unit "
            "context WITHOUT consulting any scope (`(ctx == Context.wholeUnit) || "
            "owner`), but this rival demands an owner there too and so returns "
            "`Decision.noOverride`. Refuted at a documented whole-unit "
            "initializer with the init category enabled and no container path. "
            "Verifying would be SPEC-TOO-WEAK (the whole-unit disjunct unpinned — "
            "every other rival keeps it intact, so it was pinned only on its "
            "`owner` side). (Added by audit: the `wholeUnit` arm of the ownership "
            "gate.)"),
        "witness": _witness(
            "Context.wholeUnit", "__init__",
            _target(True, "__init__", False, [], []),
            True, False, False),
    },
    {
        "id": "weak-exceptionbody-still-direct-scope",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit (no sibling): a HALF-fix. Settle ownership against the
        # resolved scope for a class body but leave an exception body reading the
        # as-presented scope. `weak-ownership-via-direct-scope` refutes only at a
        # CLASS body, so a rival that fixes one bodied context and not the other
        # was unattacked — and this is the most plausible incomplete real patch.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            f"    if {_G} then\n"
            "      let owner := match ctx with\n"
            "        | Context.classBody     => ownerIn target target.resolvedScope\n"
            "        | Context.exceptionBody => ownerIn target target.directScope\n"
            "        | _                     => false\n"
            "      if (ctx == Context.wholeUnit) || owner then\n"
            f"        if {_CAT} then\n"
            "          return Decision.forceInclude\n"
            "        else\n"
            "          return Decision.noOverride\n"
            "      else\n"
            "        return Decision.noOverride\n"
            "    else\n"
            "      return Decision.noOverride\n"
            "    -- impl-end"),
        "refinement": (
            "an INCOMPLETE version of the change: ownership is settled against "
            "the scope of the object the target stands for in a class body, but "
            "an exception body still consults the scope of the target as "
            "presented. A documented initializer in an exception-bodied context, "
            "presented through a metadata-preserving wrapper, is still left at "
            "the default, so that half of the inclusion behaviour stays broken. "
            "Does not resolve."),
        "rationale": (
            "REJECT from `out = inclusionDecision …` via the OWNERSHIP gate on "
            "the exception-body arm: the spec settles BOTH bodied contexts "
            "against `resolvedScope`, this rival fixes only the class-body arm. "
            "Refuted in an EXCEPTION body whose directScope misses the container "
            "([]) while resolvedScope recovers it ([(\"C\", true)]) — the "
            "existing direct-scope rival is refuted at a CLASS body only, so a "
            "half-fixed rival was unattacked. Verifying would be SPEC-TOO-WEAK "
            "(the resolved-scope requirement pinned on only one bodied context). "
            "(Added by audit: per-context isolation of the ownership scope.)"),
        "witness": _witness(
            "Context.exceptionBody", "__init__",
            _target(True, "C.__init__", False, [], [("C", True)]),
            True, False, False),
    },
]

# ---- resolve the two placeholder-built rivals cleanly (kept out of the literal
# ---- above for readability). weak-drop-init-category isolates the initializer
# ---- conjunct: keep special + private, drop init.
for _c in SPEC_TESTS:
    if _c["id"] == "weak-drop-init-category":
        _c["module"] = _rewrite_impl(
            _branch_impl(_G, _OWN,
                         "(isSpecial name && incSpecial) "
                         "|| (isPrivate name && incPrivate)"))
        _c["refinement"] = (
            "drops the initializer inclusion category while keeping special and "
            "private. A documented, owned initializer with the initializer "
            "category enabled — the report's exact scenario — is left at the "
            "default instead of being included, so the initializer-inclusion case "
            "FAILS. Does not resolve.")
        _c["rationale"] = (
            "REJECT from `out = inclusionDecision …` on the initializer "
            "sub-domain: the spec forces inclusion for an owned documented "
            "initializer when the init category is enabled (the `isInit name && "
            "incInit` conjunct), but this returns `Decision.noOverride`. Refuted at "
            "exactly that input, with only `incInit` enabled — held apart from the "
            "special-only and private rivals by which flag is set. Verifying would "
            "be SPEC-TOO-WEAK (the init conjunct unpinned). (Added coverage: "
            "per-category conjunct isolation.)")
        _c["witness"] = _witness(
            "Context.classBody", "__init__",
            _target(True, "C.__init__", False, [("C", True)], [("C", True)]),
            True, False, False)


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (1
# soundness positive, 1 admissibility, 6 uniqueness rivals — two of which are
# frame-mutation rivals) plus an AXIOM lane (2 axiom probes). The sibling
# contracts `skip_decision` over a read-only `MemberObj` held at fractional heap
# permissions, with the ownership answer bridged through a `canonical` axiom
# modeling the unwrap callee. This backend models the SAME member-inclusion
# decision DEEPLY and CONCRETELY (`inclusionDecision` over the `Context` /
# `DocTarget` / `Decision` carriers): the wrapper-vs-underlying distinction the
# `canonical` axiom carried is refined into the `directScope` vs `resolvedScope`
# fields, so there is no axiom to consume and no permission surface.
#
#   sibling case            kind          -> here                            disposition
#   -----------------------------------------------------------------------------------------
#   frame-mutate-has_doc    uniqueness    -> (none)                          VACUOUS (frame)
#   frame-mutate-cls_name   uniqueness    -> (none)                          VACUOUS (frame)
#   prepatch-obj-ns         uniqueness    -> weak-ownership-via-direct-scope PORTED
#   always-none             uniqueness    -> weak-always-nooverride          PORTED
#   include-if-doc          uniqueness    -> weak-include-if-considered      PORTED
#   partial-special-only    uniqueness    -> weak-special-only-category      PORTED
#   partial-invert-doc      uniqueness    -> weak-invert-doc-gate            PORTED
#   pos-control-reshape     soundness     -> pos-control-direct-model        RE-SHAPED
#                                            (+ pos-control-flattened-guard  ADDED)
#   admiss-f2p-shaped       admissibility -> admiss-nondegenerate            RE-AIMED
#   AXIOM_TESTS (2 probes)  axiom         -> (none)                          DROPPED (G-AX lane)
#   -----------------------------------------------------------------------------------------
#   (added, no sibling)     uniqueness    -> weak-drop-init-category         ADDED
#   (added, no sibling)     uniqueness    -> weak-drop-private-category      ADDED
#   (added, no sibling)     uniqueness    -> weak-drop-weakref-guard         ADDED
#   (added, no sibling)     uniqueness    -> weak-ignore-path-walk-defer     ADDED
#   (added by audit)        uniqueness    -> weak-wholeunit-needs-owner      ADDED
#   (added by audit)        uniqueness    -> weak-exceptionbody-still-direct-scope ADDED
#
# 5 uniqueness ported, 1 admissibility re-aimed, 1 soundness re-shaped + 1 added,
# 6 uniqueness added (per-category / weak-ref / path-walk coverage this carrier
# models explicitly, plus the two the audit landed: the whole-unit ownership
# disjunct and the half-fixed exception-body arm); 2 frame-mutation rivals
# vacuous; axiom lane dropped.
#
# VACUOUS (frame-mutate-has_doc, frame-mutate-cls_name): the sibling's two
#   frame-mutation rivals WRITE to a read-only `MemberObj` field held at
#   `Acc(.,1/2)`, rejected by the permission system (a store needs full
#   permission), and are MANDATORY there because the member object is an external
#   library object the hook must not mutate. This backend is referentially
#   transparent: `target` is an immutable `DocTarget` value declared read-only
#   (not `mut`), there is no heap, no aliasing and no permission system. There is
#   no read-only input to overwrite and no frame clause to violate, so the class
#   has no carrier analogue. Omitted as a genuine carrier fact, NOT fabricated
#   (porting map: the frame/permission class is vacuous on a referentially-
#   transparent backend). The directive-5 read-only obligation is instead met
#   structurally: none of `ctx`/`name`/`target`/the flags is `mut`.
#
# PORTED (the five value/branch rivals): prepatch-obj-ns -> weak-ownership-via-
#   direct-scope (the literal pre-patch operand: read ownership from the
#   as-presented scope, not the resolved one; refuted at the input where the two
#   scopes disagree — the fix's sub-domain). always-none -> weak-always-nooverride
#   (never force inclusion). include-if-doc -> weak-include-if-considered
#   (force inclusion for any considered documented target, dropping ownership +
#   category). partial-special-only -> weak-special-only-category (handle only the
#   dunder-special category; refuted on the initializer sub-domain — the report's
#   scenario). partial-invert-doc -> weak-invert-doc-gate (invert the doc gate;
#   the witness that makes `hasDoc` load-bearing).
#
# RE-SHAPED / ADDED (positives): pos-control-reshape -> pos-control-direct-model
#   (maximally-different loop-free direct return of the grounded model) and an
#   ADDED pos-control-flattened-guard (a loop-free but branch-preserving fold of
#   the three gates into one conjunctive guard, keeping the frozen proof), so the
#   soundness surface is defended from both a trivial shape and a minimal edit.
# RE-AIMED (admiss-f2p-shaped -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped input satisfies its fractional-permission Requires. This backend
#   has NO `require` (total domain) and no permission surface, so that probe is
#   degenerate; the sharper residual risk is a DEGENERATE post-image, so the case
#   is re-aimed to a live in-region assert pinning three distinct outcomes
#   (force-include / default-by-category / default-by-ownership) at F2P-shaped
#   inputs.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless. Here the bundle also declares NO axiom (mapping.md
#   §3: the unwrap callee is modeled deeply as the directScope/resolvedScope
#   fields, validated by G-CONF, so G-AX is a documented skip), so there is
#   nothing an axiom probe could target on this carrier.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = inclusionDecision
#   ctx name target incInit incSpecial incPrivate` has seven binders, and
#   `inclusionDecision` composes three gates (considered / ownership / category)
#   with sub-structure inside each. The eleven reject witnesses probe eleven
#   DISTINCT input points:
#     * weak-ownership-via-direct-scope  classBody  __init__     direct=[] resolved=[(C,T)] incInit
#     * weak-always-nooverride           wholeUnit  __special__  (all gates pass) incSpecial
#     * weak-include-if-considered       exceptionBody _helper   owned, NO category enabled
#     * weak-special-only-category       wholeUnit  __init__     incInit (special-only rival)
#     * weak-invert-doc-gate             wholeUnit  __init__     hasDoc=FALSE, incInit
#     * weak-drop-init-category          classBody  __init__     owned, incInit only
#     * weak-drop-private-category       classBody  _helper      owned, incPrivate only
#     * weak-drop-weakref-guard          classBody  __weakref__  owned, incSpecial
#     * weak-ignore-path-walk-defer      classBody  Pkg.C.__init__ multi-seg, ownerViaPathWalk=T
#     * weak-wholeunit-needs-owner       wholeUnit  __init__     no container path, incInit
#     * weak-exceptionbody-still-direct-scope exceptionBody __init__ direct=[] resolved=[(C,T)]
#   So `ctx` ranges over {classBody, exceptionBody, wholeUnit}; `name` over
#   {__init__, __special__, _helper, __weakref__} and a multi-segment qualified
#   name; `hasDoc` over {T, F} (invert-doc-gate holds it false, demonstrated
#   load-bearing); `directScope`/`resolvedScope` DISAGREE at exactly the two
#   scope rivals — weak-ownership-via-direct-scope (class body) and
#   weak-exceptionbody-still-direct-scope (exception body), which between them
#   pin the resolved-scope requirement on BOTH bodied arms; every other witness
#   holds the two scopes equal so that rival is refuted for its OWN reason, not
#   the scope split. `ownerViaPathWalk` is exercised only by
#   weak-ignore-path-walk-defer; and each of `incInit`/`incSpecial`/`incPrivate`
#   is the SOLE enabled flag at some witness (drop-init / drop-private /
#   special-only isolate them). All three gates are attacked — considered
#   (invert-doc-gate on hasDoc, drop-weakref-guard on the name guard,
#   always-nooverride via the force-inclusion outcome), ownership
#   (via-direct-scope, exceptionbody-still-direct-scope, ignore-path-walk-defer,
#   wholeunit-needs-owner, include-if-considered), and category (special-only,
#   drop-init, drop-private, include-if-considered). Both arms of the ownership
#   disjunct `(ctx == Context.wholeUnit) || owner` are now pinned: the `owner`
#   side by the scope/path-walk rivals, the `wholeUnit` side by
#   weak-wholeunit-needs-owner. No binder is pinned at a single value across the
#   reject set (pts = 11).
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3), the sibling's
#   axiom probes target the G-AX lane which this gate ignores, and there is
#   nothing on this carrier for an axiom probe to check.
AXIOM_TESTS = []
