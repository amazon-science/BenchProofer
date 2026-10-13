"""properties.py — G-PBT falsification battery for django__django-16454 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct nestedParserErrorConfig`` obligation survives) and swaps in a
candidate implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, no ``require``):

  nestedParserErrorConfig (nestedAcceptsConfig : Bool) (config : Option Bool)
      return (out : Option Bool)
    ensures out = inheritedErrorConfig nestedAcceptsConfig config

  inheritedErrorConfig accepts config := if accepts then config else none

The method decides the error-presentation configuration a freshly-spawned nested
parser is constructed with. TWO INPUT BINDERS, and the sole ``ensures`` clause
composes TWO independently-attackable top-level outcomes:

  * GATE — ``nestedAcceptsConfig`` selects the branch. When it holds the parent's
    configuration is threaded through; when it does not, the nested parser is
    left UNSET (``none``) regardless of what the parent carries.
  * PASS-THROUGH — on the gated-in branch the WHOLE parent ``config`` passes
    through UNCHANGED, including the unset case. The model deliberately does not
    collapse an unset-but-compatible parent to anything else, and does not
    normalise, invert, or constant-fold the three-valued configuration.

``config : Option Bool`` is three-valued (``none`` / ``some true`` /
``some false``), which is the whole reason PASS-THROUGH is a real obligation
rather than a boolean copy: a rival can be right on two of the three values and
wrong on the third. The reject witnesses therefore drive ``config`` across ALL
THREE values and ``nestedAcceptsConfig`` across BOTH, at six distinct input
points (pts = 6 — the WHOLE domain), so no binder is pinned at a single value
across the reject set and neither the gate nor the pass-through is demonstrated
only at one point. The sixth point was added by the audit, which measured that a
rival can be wrong there and nowhere else; see the BINDER / CLAUSE COVERAGE
footer for the build that refuted the port's contrary argument.

CARRIER NOTE — HOW A WITNESS REACHES THE POST-IMAGE. The spec is a ``method``
CONTRACT, not a bare predicate, so a witness goes through Velvet's own tester
machinery: ``nestedParserErrorConfigTester accepts config = false`` says the
extracted program's result violates the method's postcondition at that concrete
input. It is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict, and it closes by ``decide`` — every
argument is a concrete literal over ``Bool`` / ``Option Bool``, the carrier is
fully transparent (the ``axioms`` region is EMPTY — no opaque callee, so none of
the four conditioning routes was needed and no witness binds anything, hence no
consistency probe applies). Both halves of every witness below were checked with
``scripts/lean_verify.sh``: each elaborates green against its rival and fails on
the frozen solution with ``Tactic `decide` proved that the proposition ... is
false``.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY, and are cheap here: the postcondition
    pins a VALUE, not a code shape, so a correct impl that reshapes the branch
    (test the negated gate, or dispatch on the configuration first) must still
    verify. Three are shipped, including a direct return of the grounded model.
  * ADMISSIBILITY — RE-AIMED. The sibling's probe is "a normal input can satisfy
    the fractional-permission ``Requires``". This method has NO ``require`` at
    all and there is no permission surface, so that probe is degenerate. The
    sharper residual risk on a two-binder boolean domain is a DEGENERATE
    post-image — a spec no impl distinguishes reads exactly like one every impl
    meets — so the case is re-aimed to a live in-region ``assert`` pinning three
    genuinely DISTINCT outcomes. Its liveness was controlled: substituting a
    deliberately false conjunct breaks the build, so the assert is discharged
    rather than trivial.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend, NOT ported. The
    sibling carries two such rivals because a read-only input is held at a
    fractional heap permission an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: both inputs are immutable values declared
    read-only (neither ``mut``), there is no heap, no aliasing, no ``Old``, and
    no permission system — there is no read-only input to overwrite and no frame
    clause to violate. Fabricating a substitute would test nothing.
  * FRAME / GARBAGE-WRITE ON THE PLAIN PATH — this one DOES port, because on this
    carrier it is not a frame property at all: the sibling states it as
    ``Implies(not injects_flag, inherited_style is Old(inherited_style))`` over a
    mutable field, whereas here the gated-out path's value is pinned directly in
    the returned post-image (``... else none``). It becomes an ordinary
    value-level rival (``weak-plain-path-binds-config``), attacked below.
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
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to
    ``inheritedErrorConfig nestedAcceptsConfig config``, a fully-unfolded ``def``
    over the method's own two arguments; there is no answer-key term to echo.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane. Every rival below is right
    on part of the domain and wrong on a named sub-domain, and each is refuted at
    a point inside that sub-domain.
"""
from pathlib import Path

INSTANCE = "django__django-16454"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The gold branch, verbatim: a single anchor lying wholly inside the impl
# ---- region and unique in the file (both facts asserted at load, so the
# ---- manifest breaks loudly if the frozen solution ever changes).
_IMPL = """    if nestedAcceptsConfig then
      return config
    else
      return none"""
assert _BASE.count(_IMPL) == 1, "impl anchor drift — re-sync _IMPL"

# ---- The impl-start marker line (unique). The admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body so
# ---- the method's own obligation still discharges.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- The frozen proof body (tactic script only; elided from the spec view).
_PROOF = "prove_correct nestedParserErrorConfig by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "proof anchor drift"


def _impl(body):
    """Variant with the gold branch replaced; frozen proof script untouched.

    Every rival below is a straight-line expression over the same two binders,
    so the frozen `loom_solve` remains the right script — a correct reshape
    still closes under it and a wrong one leaves the equality unsolved. No
    rival needs (or gets) a retuned proof, so no reject case can pass merely
    because a script stopped matching.

    AUDIT NOTE on the limit of that claim. It holds for every case shipped here
    (measured: each reject case fails with `unsolved goals` on the ensures
    itself, quoting its own returned expression, never with a tactic-shape
    error), but it is NOT a general property of the spec, so do not read the
    reject outcomes as "loom_solve decides correctness". Two CORRECT reshapes
    were found that the frozen script alone does NOT close — one routing the
    gate through `Option.filter`, one through `Option.bind` — each failing with
    `unsolved goals` on the ensures, i.e. indistinguishable in shape from a
    genuine rival's failure. Both are provable: adding
    `cases nestedAcceptsConfig <;> cases config <;> simp [...]` after the frozen
    script closes each (exit 0), which is why they are recorded as a
    proof-automation limit and NOT as a spec-too-strong finding — the spec
    admits them, the default tactic just does not find the proof. This is
    exactly why every reject case here carries a witness instead of resting on
    its exit code.
    """
    return _swap(_BASE, _IMPL, body)


# ---- Witness preamble. `extract_program_for` / `derive_tester_for` are
# ---- directives inside the witness itself, so the tester names exist in BOTH
# ---- the rival and the gold build by construction (nothing is referenced that
# ---- only one side declares). Every argument is a concrete literal so `decide`
# ---- reduces without getting stuck; no witness binds a hypothesis, so there
# ---- are no assumptions that could be jointly unsatisfiable.
def _witness(accepts, config):
    return ("extract_program_for nestedParserErrorConfig\n"
            "prove_precondition_decidable_for nestedParserErrorConfig\n"
            "prove_postcondition_decidable_for nestedParserErrorConfig\n"
            "derive_tester_for nestedParserErrorConfig\n\n"
            f"example : nestedParserErrorConfigTester {accepts} {config} "
            "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. The postcondition pins a value, not a code shape; if a
    # faithful correct impl cannot verify, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-negated-gate",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder: test the NEGATED gate and put the unset outcome first.
        # Same post-image at every one of the six input points.
        "module": _impl(
            "    if !nestedAcceptsConfig then\n"
            "      return none\n"
            "    else\n"
            "      return config"),
        "rationale": (
            "REORDERED but correct: testing the negated gate and returning the "
            "unset configuration on the leading branch computes the same "
            "post-image at every input, so `out = inheritedErrorConfig "
            "nestedAcceptsConfig config` still holds on the whole domain. Must "
            "verify, else the spec is over-fit to the branch ORDER of the frozen "
            "impl (SPEC-TOO-STRONG). (Sibling: pos-open-branch-reorder.)"),
    },
    {
        "id": "pos-dispatch-on-config",
        "kind": "soundness",
        "expect": "verify",
        # Restructure the other axis: dispatch on the CONFIGURATION first and
        # test the gate only on the set case. Correct because the unset parent
        # yields the unset nested configuration on BOTH sides of the gate — the
        # one case a careless reshape gets wrong, which is why this positive is
        # worth its build.
        "module": _impl(
            "    match config with\n"
            "    | none => return none\n"
            "    | some c =>\n"
            "      if nestedAcceptsConfig then\n"
            "        return (some c)\n"
            "      else\n"
            "        return none"),
        "rationale": (
            "RESTRUCTURED along the other binder: dispatching on the "
            "configuration first and consulting the gate only for a set "
            "configuration is behaviourally identical, because an unset parent "
            "configuration yields the unset nested configuration on both sides "
            "of the gate. A correct reshape of the boolean structure must "
            "verify, else SPEC-TOO-STRONG. This also exercises the shape a "
            "careless reshape gets wrong (the unset-and-gated-in case), so it is "
            "a positive that could plausibly have failed. (Sibling: "
            "pos-build-boolean-direct.)"),
    },
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no branching at all — maximally structurally different from the gold
        # conditional. Not an oracle echo: `inheritedErrorConfig` is a fully
        # unfolded def over this method's own two arguments (the axioms region is
        # empty), so returning it IS doing the work.
        "module": _impl("    return (inheritedErrorConfig nestedAcceptsConfig config)"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "directly, with no branching — maximally different in shape from the "
            "frozen conditional. `out` IS that model, so the ensures holds on the "
            "whole domain. Must verify, else the spec is over-fit to the "
            "existence of a branch (SPEC-TOO-STRONG). Also the "
            "no-ungrounded-echo control: `inheritedErrorConfig` is a fully "
            "unfolded def over this method's own arguments, not an opaque answer "
            "key, so a direct return is correct rather than a cheat."),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed from precondition admissibility (this method has
    # NO `require`, and there is no permission surface, so the sibling's probe is
    # degenerate) to POST-IMAGE NON-DEGENERACY. The in-region assert pins three
    # genuinely distinct outcomes at F2P-shaped inputs; the gold impl is kept
    # verbatim so the method's own obligation still discharges. LIVENESS
    # CONTROLLED: replacing any conjunct with a false one breaks the build
    # (checked — `grind` reports the goal unsolved), so the assert is really
    # discharged and not vacuously true.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      inheritedErrorConfig true (some true) = some true ∧\n"
                  "      inheritedErrorConfig true none = none ∧\n"
                  "      inheritedErrorConfig false (some true) = none))\n"),
            _PROOF,
            _PROOF + "\n  all_goals first | decide | grind"),
        "rationale": (
            "the post-image is satisfiable AND NON-DEGENERATE across the domain "
            "the behaviour cares about: a gated-in parent with a set "
            "configuration must yield that configuration, a gated-in parent with "
            "an UNSET configuration must yield unset (pass-through does not "
            "invent a value), and a gated-OUT parent with a set configuration "
            "must yield unset (the gate really gates). Three distinct outcomes "
            "over the same two binders, so the obligation distinguishes inputs "
            "rather than being met by any constant. The in-region assert must "
            "discharge and the gold impl is kept verbatim so `out = "
            "inheritedErrorConfig ...` still verifies. (Sibling: "
            "admiss-open-self-call, re-aimed: this backend has no `require` and "
            "no permission surface to probe.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and a refinement argument for why its faithful
    # real counterpart would NOT resolve. Each `refinement` below was checked by
    # actually building the corresponding real patch at base_commit and running
    # the failing scenario plus the whole surrounding suite — see the footer;
    # two candidate rivals were DROPPED because that check showed their real
    # patches DO resolve.
    # =====================================================================
    {
        "id": "weak-never-propagate",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-change shape: the nested parser is always left unset,
        # the parent's configuration is never threaded through. Correct on the
        # whole gated-OUT half of the domain and on the gated-in-but-unset point;
        # wrong exactly where the change matters.
        "module": _impl("    return none"),
        "refinement": (
            "this is the pre-change behaviour itself: nested parsers are spawned "
            "with no configuration threaded through, so a nested parser presents "
            "an argument error as an uncaught stack trace instead of the "
            "human-facing usage message the parent would have produced. The "
            "failing scenario asserts exactly that two-line human-facing output "
            "and gets the trace instead — CHECKED by building this shape at "
            "base_commit: the scenario fails with a 54-line stack trace where 2 "
            "lines are asserted. A faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from `out = inheritedErrorConfig nestedAcceptsConfig config` "
            "via the PASS-THROUGH outcome: when the gate holds the spec requires "
            "the parent's configuration, this returns unset. Verifying would be "
            "SPEC-TOO-WEAK (propagation entirely unpinned — the spec would admit "
            "the pre-change behaviour). Refuted on the gated-in sub-domain at a "
            "SET parent configuration, the only place it differs from gold. "
            "(Sibling: supp-open-drop-propagation / partial-open-hardcode-none.)"),
        "witness": _witness("true", "(some true)"),
    },
    {
        "id": "weak-drop-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the compatibility gate: always thread the parent's configuration
        # through, whatever kind the nested parser is. Correct on the ENTIRE
        # gated-in half of the domain — a true near-miss — and wrong only when
        # the nested kind does not understand the configuration.
        "module": _impl("    return config"),
        "refinement": (
            "a counterpart that threaded the configuration through "
            "unconditionally would hand it to a nested parser kind that does not "
            "accept it, so constructing that nested parser raises instead of "
            "reporting the argument error. CHECKED by building this shape at "
            "base_commit: the guarded scenario that exercises a foreign nested "
            "kind FAILS, while the scenario the change targets passes — so the "
            "instance does NOT resolve. This is the rival whose real patch is "
            "refuted by the surrounding suite rather than by the primary failing "
            "scenario."),
        "rationale": (
            "REJECT from `out = inheritedErrorConfig ...` via the GATE outcome: "
            "when `nestedAcceptsConfig` is false the spec requires unset, this "
            "returns the parent's configuration. Verifying would be "
            "SPEC-TOO-WEAK (the gate unpinned — the spec would not distinguish a "
            "compatible nested kind from a foreign one). This is the witness "
            "that proves `nestedAcceptsConfig` is LOAD-BEARING: it is refuted at "
            "`false`, and it AGREES with gold at every `true` point, so it "
            "cannot share a witness with any gated-in rival. (Sibling: "
            "partial-open-always-inject / partial-build-always-carry.)"),
        "witness": _witness("false", "(some true)"),
    },
    {
        "id": "weak-plain-path-binds-config",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's plain-path GARBAGE-WRITE class, re-expressed as a value
        # rival: the gated-OUT path records a configuration anyway. Correct on
        # the whole gated-in half AND on the gated-out points where the parent
        # happens to carry that same value; wrong on the rest of the gated-out
        # half. A NEAR-MISS relative to weak-drop-gate, which is why it gets its
        # own witness at an UNSET parent configuration — the point where
        # weak-drop-gate agrees with gold and this rival does not.
        "module": _impl(
            "    if nestedAcceptsConfig then\n"
            "      return config\n"
            "    else\n"
            "      return (some true)"),
        "refinement": (
            "a counterpart that stashed a configuration for the foreign nested "
            "kind as well would be a side effect the change does not have, and it "
            "hands the configuration to a kind that does not accept it — the same "
            "wall as dropping the gate. CHECKED by building this shape at "
            "base_commit: the guarded scenario exercising a foreign nested kind "
            "FAILS, so a faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from `out = inheritedErrorConfig ...` via the GATE outcome's "
            "VALUE (`... else none`): on the gated-out path the spec pins unset, "
            "this binds a configuration. Verifying would be SPEC-TOO-WEAK — this "
            "is precisely the sibling's plain-path garbage-write weakness, which "
            "on this carrier is pinned by the post-image directly rather than by "
            "a frame clause. Refuted at an UNSET parent configuration on the "
            "gated-out path: a DIFFERENT point from weak-drop-gate (which agrees "
            "with gold there, since gold and it both yield unset when the parent "
            "is unset), so the near-miss gets its own discriminator. (Sibling: "
            "frame-open-plain-garbage-style / frame-build-plain-garbage-style.)"),
        "witness": _witness("false", "none"),
    },
    {
        "id": "weak-normalise-unset",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest near-miss: gate correct, propagation correct for every SET
        # parent configuration, but an UNSET parent is normalised to a set value
        # on the way through. Wrong on exactly ONE of the six input points. This
        # is the rival the spec's docstring calls out ("the model does not
        # collapse an unset-but-compatible parent to anything else") and the one
        # a battery that probed only set configurations would miss entirely.
        "module": _impl(
            "    if nestedAcceptsConfig then\n"
            "      match config with\n"
            "      | none => return (some false)\n"
            "      | some c => return (some c)\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "a counterpart that normalised an unset parent configuration to a "
            "definite value before threading it would make a nested parser "
            "behave as if the parent had been configured, on the very path where "
            "the parent deliberately carries no configuration. NOT resolved-by-"
            "the-primary-scenario: CHECKED by building this shape at "
            "base_commit, the whole surrounding suite PASSES, because the "
            "scenarios exercise the configured path. This rival is therefore "
            "shipped on the strength of its SPEC violation, and its refinement "
            "claim is deliberately narrow — see the footer's REFINEMENT AUDIT, "
            "which records that this is the ONE rival here whose faithful patch "
            "was NOT observed to break the shipped scenarios, and why it is kept "
            "anyway (it violates the frozen post-image at a real input, so a "
            "spec that admitted it would be weaker than the behaviour the "
            "docstring states)."),
        "rationale": (
            "REJECT from `out = inheritedErrorConfig ...` via PASS-THROUGH at the "
            "UNSET configuration: the spec threads the WHOLE parent "
            "configuration, `none` included, but this substitutes a set value. "
            "Verifying would be SPEC-TOO-WEAK (the three-valued configuration "
            "collapsed to a boolean — the spec would stop distinguishing "
            "'unset' from 'configured off'). This is the witness that proves the "
            "`none` case of `config` is LOAD-BEARING: the rival agrees with gold "
            "at all four `some` points and at both gated-out points, so no other "
            "witness here can refute it."),
        "witness": _witness("true", "none"),
    },
    {
        "id": "weak-invert-config",
        "kind": "uniqueness",
        "expect": "reject",
        # Gate correct, unset case correct, but a SET parent configuration is
        # propagated inverted. Disjoint from weak-normalise-unset: this one is
        # right exactly where that one is wrong and vice versa, so the two pin
        # the `some` and `none` halves of pass-through independently.
        "module": _impl(
            "    if nestedAcceptsConfig then\n"
            "      match config with\n"
            "      | none => return none\n"
            "      | some c => return (some (!c))\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "a counterpart that propagated the parent's configuration INVERTED "
            "would make a nested parser render errors the opposite way from its "
            "parent — the parent's human-facing presentation becoming an uncaught "
            "propagation in the nested parser, and vice versa. CHECKED by "
            "building this shape at base_commit: the primary failing scenario "
            "still fails (it asserts the two-line human-facing output and gets "
            "the uncaught trace), so a faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from `out = inheritedErrorConfig ...` via PASS-THROUGH at a "
            "SET configuration: the spec passes the parent's value through "
            "unchanged, this flips it. Verifying would be SPEC-TOO-WEAK "
            "(pass-through pinned only up to negation). Refuted at `some false` "
            "— the third value of `config`, reached by NO other witness here, and "
            "the point that shows the spec constrains WHICH set value is threaded "
            "rather than merely that some set value is."),
        "witness": _witness("true", "(some false)"),
    },
    {
        "id": "weak-off-leaks-past-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The gated-out path leaks the parent's configuration
        # for exactly ONE of its two set values: a parent configured OFF passes
        # through even though the nested kind does not understand it, while a
        # parent configured ON is correctly dropped. Wrong at exactly ONE input
        # point — (accepts=false, config=some false) — and the audit MEASURED
        # that this is the one point no other rival here reaches: built against
        # this rival, the tester AGREES with the frozen post-image at all five
        # points the other five witnesses drive and disagrees only at the sixth
        # (one build, exit 0, asserting five `= true` and one `= false`). So
        # before this case the sixth point was genuinely unattacked, not
        # unobservable.
        "module": _impl(
            "    if nestedAcceptsConfig then\n"
            "      return config\n"
            "    else\n"
            "      match config with\n"
            "      | some false => return (some false)\n"
            "      | _ => return none"),
        "refinement": (
            "a counterpart that let one particular parent configuration slip "
            "past the compatibility gate would hand that configuration to a "
            "nested parser kind that does not understand it, so constructing "
            "that nested parser raises instead of reporting the argument error "
            "— the same wall the unconditional-propagation rival hits, and the "
            "guarded scenario that exercises a foreign nested kind is what "
            "catches it. NARROW, and deliberately stated as such: the value it "
            "leaks is the one a parent reached other than through the "
            "command-line entry point carries, and the shipped scenarios drive "
            "the foreign-kind path only from that entry point, so this rival's "
            "faithful patch is in the same position as weak-normalise-unset's "
            "— refuted by the frozen post-image at a real input rather than by "
            "an observed scenario break. Kept on that basis, with the claim "
            "narrow instead of overstated (see the REFINEMENT AUDIT footer)."),
        "rationale": (
            "REJECT from `out = inheritedErrorConfig ...` via the GATE outcome, "
            "at the input point the rest of this battery leaves untouched: when "
            "`nestedAcceptsConfig` is false the spec pins unset for EVERY parent "
            "configuration, and this returns the parent's value for one of them. "
            "Verifying would be SPEC-TOO-WEAK — the gate pinned only for SOME "
            "configurations, i.e. a gate that may be selectively bypassed. "
            "Distinct from weak-drop-gate (which bypasses the gate for every "
            "value, and so is already refuted at `some true`) and from "
            "weak-plain-path-binds-config (which INVENTS a value on the "
            "gated-out path rather than leaking the parent's): both of those "
            "AGREE with gold at `(false, some false)`, which is why this rival "
            "needs its own witness there."),
        "witness": _witness("false", "(some false)"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING
#
# The sibling battery ships 10 SPEC cases (2 soundness positives, 1
# admissibility, 7 uniqueness rivals — two of them mandatory frame-mutation
# rivals) plus an EMPTY axiom lane (AXIOM_TESTS = []). It contracts TWO
# functions over a MUTABLE-OBJECT carrier: `open_subcommand_group`, which
# records an injection policy onto a builder object under fractional heap
# permissions, and `build_subcommand_parser`, which consumes that recorded
# policy to construct the child. This backend models the purely functional CORE
# of the same behaviour as ONE method: the configuration a nested parser is
# constructed with, as a closed function of the kind-compatibility flag and the
# parent's configuration. The two-object handoff (policy recorded, then
# consumed) is not modeled — it is the same decision observed twice — so every
# sibling case that attacks the SECOND function collapses onto its counterpart
# on the first, and the whole permission dimension disappears. This is carrier
# narrowing, not thinning: 6 rivals against the sibling's 7, but the modeled
# post-image is attacked on both of its outcomes and at all six of its input
# points.
#
#   sibling case                    kind          -> here                        disposition
#   -----------------------------------------------------------------------------------------
#   pos-open-branch-reorder         soundness     -> pos-negated-gate            PORTED
#   pos-build-boolean-direct        soundness     -> pos-dispatch-on-config      PORTED
#                                                    (+ pos-direct-model         ADDED)
#   admiss-open-self-call           admissibility -> admiss-nondegenerate        RE-AIMED
#   frame-mut-open-parent           uniqueness    -> (none)                      VACUOUS
#   frame-mut-build-builder         uniqueness    -> (none)                      VACUOUS
#   partial-open-hardcode-true      uniqueness    -> (none)                      DROPPED (refinement)
#   partial-open-hardcode-none      uniqueness    -> weak-never-propagate        MERGED/PORTED
#   partial-open-always-inject      uniqueness    -> weak-drop-gate              PORTED
#   partial-build-always-carry      uniqueness    -> weak-drop-gate              MERGED
#   frame-open-plain-garbage-style  uniqueness    -> weak-plain-path-binds-config PORTED
#   frame-build-plain-garbage-style uniqueness    -> weak-plain-path-binds-config MERGED
#   supp-open-drop-propagation      uniqueness    -> weak-never-propagate        MERGED
#   (no sibling counterpart)                      -> weak-normalise-unset        ADDED
#   (no sibling counterpart)                      -> weak-invert-config          ADDED
#   (no sibling counterpart)                      -> weak-off-leaks-past-gate    ADDED (audit)
#   AXIOM_TESTS (empty)             axiom         -> (none)                      N/A (G-AX)
#
# VACUOUS — the two frame/permission-MUTATION rivals (frame-mut-open-parent,
#   frame-mut-build-builder). The sibling rejects these through the PERMISSION
#   system, not the postcondition: it holds `parent.error_style` and
#   `builder.inherited_style` at half permission and any WRITE is insufficient
#   permission. This backend is referentially transparent — both inputs are
#   immutable values declared read-only (neither `mut`), there is no heap, no
#   aliasing, no `Old`, and no permission system. There is no read-only input to
#   overwrite and no frame clause to violate, so the class has no carrier
#   analogue at all. Omitted as a genuine carrier fact per the porting map; a
#   fabricated substitute would test nothing. NOTE the sibling's OTHER frame
#   class (plain-path garbage-write) is a different animal and IS ported — see
#   weak-plain-path-binds-config — because on this carrier the gated-out path's
#   value is pinned directly in the returned post-image rather than by a frame
#   clause over a mutable field.
#
# MERGED — four sibling rivals have no independent counterpart because the
#   second contracted function does not exist here. partial-build-always-carry
#   is the same attack as partial-open-always-inject one hop later (ignore the
#   recorded policy vs never record it correctly) and both land on weak-drop-gate;
#   frame-build-plain-garbage-style is frame-open-plain-garbage-style one hop
#   later and both land on weak-plain-path-binds-config;
#   supp-open-drop-propagation and partial-open-hardcode-none both leave the
#   nested configuration at its default and both land on weak-never-propagate.
#   Shipping them separately would mean two variants with byte-identical impls
#   and the same witness — case-count parity bought with duplicates.
#
# DROPPED FOR REFINEMENT — partial-open-hardcode-true, and its analogue
#   "propagate a constant off value". THIS IS THE FINDING OF THIS PORT and it is
#   an OMISSION, not a pass: the sibling ships hardcode-TRUE as a full rival with
#   the refinement argument that "forcing human-facing formatting even for the
#   programmatic parent would not faithfully match gold across the runtime
#   settings the tests exercise". On this instance that argument does not hold up.
#   Its faithful real patch was BUILT at base_commit and the surrounding suite
#   RUN: threading a constant "configured" value instead of the parent's own
#   makes the primary failing scenario PASS and breaks nothing else in the
#   suite — the instance RESOLVES. The reason is that every scenario the change
#   ships drives the parent through the command-line entry point, where the
#   parent's configuration already IS that constant, so the constant and the
#   parent's value coincide at every point the tests probe. The rival is
#   genuinely wrong against the frozen post-image (it fails pass-through at a
#   parent configured OFF) and its witness discriminates, so it could have been
#   shipped as a passing reject case — but its `refinement` field would have
#   been FALSE, and a reject case whose refinement is false asserts a
#   verify-does-not-imply-resolve break that does not exist. Dropped rather than
#   shipped with a refinement the manifest cannot back. The sub-domain it
#   attacks (pass-through of a SET configuration) is still attacked, by
#   weak-invert-config, whose faithful patch WAS observed to leave the primary
#   scenario failing. Recorded here so the gap is closable: if a scenario is ever
#   added that drives a parent configured OFF, this rival becomes shippable with
#   a true refinement.
#
# KEPT WITH A NARROW REFINEMENT — weak-normalise-unset and (added by the audit)
#   weak-off-leaks-past-gate are the shipped rivals whose faithful patches were
#   NOT observed to break the suite. The audit did not re-run the harness, so it
#   makes no new resolve claim for its own case: weak-off-leaks-past-gate's
#   `refinement` is written narrow for exactly that reason, and the case is
#   shipped on the same basis as weak-normalise-unset — it violates the frozen
#   post-image at a real input, so a spec admitting it would be weaker than the
#   behaviour the spec view advertises. If the gate ever treats a narrow
#   refinement as insufficient, these are the two cases to drop, and the battery
#   still retains four rivals covering both outcomes.
#
#   On weak-normalise-unset specifically: it is a shipped rival
#   whose faithful patch was NOT observed to break the suite (same reason: the
#   scenarios never drive an UNSET-and-compatible parent, so normalising unset
#   is unobserved). It is kept, unlike the dropped rival above, because its
#   `refinement` field says so explicitly instead of claiming a break it does not
#   have, and because the sub-domain it attacks is the one the frozen spec's own
#   docstring puts front-and-center ("when the gate holds the WHOLE parent
#   configuration passes through unchanged, including the unset case"). A spec
#   that admitted it would be weaker than the behaviour the spec view advertises,
#   which is a real G-PBT finding even where the shipped scenarios are silent.
#   Flagged rather than buried: if the gate treats a narrow refinement as
#   insufficient, this is the case to drop, and the battery still has four rivals
#   covering both outcomes.
#
# ADDED — weak-normalise-unset and weak-invert-config have no sibling
#   counterpart because the sibling's carrier does not force them. The sibling's
#   propagation postcondition uses Python `is` IDENTITY against the parent's
#   field, so once a rival writes anything other than that exact field the
#   sibling's verifier stops it, and the sibling never needs to ask WHICH wrong
#   value was written. Here the post-image is a VALUE equation over a
#   three-valued `Option Bool`, so "wrong value" splits into genuinely
#   independent sub-domains: normalising the unset case (wrong at `none` only)
#   and inverting the set case (wrong at both `some` values only) are disjoint
#   defects, neither implied by the other, and a battery attacking only one of
#   them would leave the other verifiable.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
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
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = inheritedErrorConfig
#   nestedAcceptsConfig config` has TWO binders and its definition has TWO
#   independent top-level outcomes (the GATE, and PASS-THROUGH on the gated-in
#   branch). The domain has exactly SIX points; the six reject witnesses probe
#   ALL SIX (pts = 6):
#     * weak-never-propagate          accepts=true  config=some true
#     * weak-drop-gate                accepts=false config=some true
#     * weak-plain-path-binds-config  accepts=false config=none
#     * weak-normalise-unset          accepts=true  config=none
#     * weak-invert-config            accepts=true  config=some false
#     * weak-off-leaks-past-gate      accepts=false config=some false  (AUDIT)
#   So `nestedAcceptsConfig` ranges over BOTH values and `config` over ALL THREE
#   (`some true`, `some false`, `none`), and NO input point is left unprobed.
#
#   CORRECTED BY AUDIT. The sixth point was previously left unprobed, on the
#   written argument that it "is one where the gate makes the configuration
#   unobservable by construction, so no rival can be wrong there without also
#   being wrong at a probed point". That argument is FALSE, and the audit refuted
#   it with a build rather than an argument. The gate makes the configuration
#   unobservable in GOLD; that says nothing about a RIVAL, which is free to
#   branch on the very value gold ignores. `weak-off-leaks-past-gate` does
#   exactly that, and one build against it (exit 0) asserts, in the same file,
#   that its tester AGREES with the frozen post-image at all five
#   previously-probed points and DISAGREES only at (accepts=false,
#   config=some false). So a rival wrong at only the sixth point exists, none of
#   the five original witnesses refutes it, and the spec's rejection of that
#   whole shape was untested until this case was added — a hole in the BATTERY,
#   not in the spec (the frozen spec does reject it: exit 1, `unsolved goals`
#   with `some false = inheritedErrorConfig nestedAcceptsConfig config` under
#   `if_neg`). The lesson generalises past this cell: "gold cannot observe this
#   input" is never a reason to skip an input point, because the spec has to pin
#   the output there too. Both outcomes are attacked:
#   the GATE by weak-drop-gate (returns the configuration where unset is pinned)
#   and weak-plain-path-binds-config (binds a different configuration there),
#   and PASS-THROUGH on all three of its values by weak-never-propagate (drops
#   it entirely), weak-normalise-unset (the `none` value) and weak-invert-config
#   (the `some` values), and the GATE is additionally attacked in its
#   SELECTIVELY-BYPASSED form by weak-off-leaks-past-gate. The three gated-out
#   near-misses are separated as required: weak-drop-gate,
#   weak-plain-path-binds-config and weak-off-leaks-past-gate all attack the
#   gated-out path, but each disagrees with gold at a point where the other two
#   AGREE with it, so each carries its own witness rather than sharing one.
#
# AXIOM_TESTS: empty. The bundle declares NO axiom (mapping.md §3: the changed
#   behaviour is modeled deeply as a closed function of two abstracted inputs,
#   validated by G-CONF, so G-AX is skipped entirely); the sibling's AXIOM_TESTS
#   is likewise empty. This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
