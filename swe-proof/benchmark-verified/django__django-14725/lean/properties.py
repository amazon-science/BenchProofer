# properties.py — G-PBT falsification battery for django__django-14725 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive honestly reproves, the proof body — is
# edited), checked by variant_scope before the verifier runs. Every expect="reject"
# case carries a refutation `witness`: a self-contained snippet that ELABORATES
# against the rival and FAILS on the frozen solution, so the rejection is
# attributable to the spec and not to a tactic script that merely stopped matching a
# reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   problem_spec_saveFormset (editOnly : Bool) (existing new : List α)
#                            (result : List α) : Prop :=
#     result = if editOnly then existing else existing ++ new
#   ONE obligation: `theorem correct_saveFormset`, universally quantified over all
#   three inputs with NO precondition hypothesis.
#
# The single postcondition equation carries two independent top-level arms, and the
# battery attacks each separately:
#   * RESTRICTED arm (editOnly = true): result = existing EXACTLY — the
#     freshly-created list contributes NOTHING. This is the behavior the issue asks
#     for; a rival that still composes in `new` under the flag is refuted here.
#   * DEFAULT arm (editOnly = false): result = existing ++ new — the already-present
#     list FOLLOWED BY the freshly-created list. This pins the unchanged default
#     behavior twice over: the freshly-created list may not be DROPPED, and the two
#     components may not be REORDERED (nor either component internally reordered).
#
# CARRIER NOTE — how the nagini rivals become lean rivals. The nagini sibling
# abstracted the two collaborator results as OPAQUE deterministic report sequences
# of the commit flag, behind fractional read permission on the mode flag; there,
# "the verifier cannot prove new_report == existing_report" was the refutation. This
# backend models the same selection over TRANSPARENT `List α` inputs — the two
# collaborator results ARE the modeled inputs (an R refinement; mapping.md) — so
# every rival the nagini battery built has a direct counterpart, and each one is
# refutable at a CONCRETE literal input with `decide` at `α := Nat`. No opaque term
# appears in the spec, so no witness needs to condition on the carrier.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME-MUTATION — the nagini sibling's MANDATORY #1 class (frame-mut-write-flag,
#     frame-mut-self-assign) rejected a rival that WROTE the mode flag held at
#     half permission. Lean is referentially transparent: there is no aliasing, no
#     permission fraction, and an input cannot be written at all. The class is
#     genuinely VACUOUS here, not a hole; no substitute is fabricated.
#   * ADMISSIBILITY — LANDED IN AUDIT (adm-f2p-shaped-points below). The port had
#     recorded this lane N/A because the lean obligation quantifies over all
#     `(editOnly, existing, new)` with no hypothesis, so "there is no precondition
#     that could be too strong". That reason is wrong: on a TOTAL carrier the
#     analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at an
#     F2P-shaped input — a spec no admissible input can satisfy positively, or that
#     cannot REFUSE a genuinely wrong result at that same input, is unusable however
#     many rivals it rejects. The lane is tested directly by discharging the
#     postcondition at concrete F2P-shaped points by evaluation.
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling carries NO such case, and on
#     lean the class is vacuous regardless: `implementation_saveFormset` is a total
#     Lean `def`, so a diverging implementation cannot be written.
#   * AXIOM_TESTS — the axiom lane belongs to G-AX; this gate ignores it. The frozen
#     axioms region is empty here anyway (no opaque callee is consumed).
from pathlib import Path

INSTANCE = "django__django-14725"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- region anchors ---------------------------------------------------------------
# _IMPL lies ENTIRELY inside impl-start/impl-end and is unique in the file; _PROOF
# lies entirely inside proof-start/proof-end and is unique. Every case edits one or
# both, so same_spec holds by construction and the `theorem correct_saveFormset`
# STATEMENT is never touched.
_IMPL = """  if editOnly then
    return existing
  return existing ++ new
"""
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

_PROOF = """  intro editOnly existing new
  unfold problem_spec_saveFormset implementation_saveFormset
  cases editOnly <;> rfl
"""
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


def _wit(flag, existing, new, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a CONCRETE
    literal input, closed by `decide` at α := Nat.

    Elaborates against a rival whose result differs from the specified selection at
    that point, and FAILS on the frozen solution (which satisfies the spec at every
    input). Binds nothing, so there are no hypotheses that could be inconsistent."""
    a = f"{flag} ({existing} : List Nat) {new}"
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_saveFormset {a}\n"
        f"    (implementation_saveFormset {a}) := by\n"
        f"  unfold problem_spec_saveFormset implementation_saveFormset\n"
        f"  decide"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Each keeps the `theorem correct_saveFormset`
# statement byte-identical and, where the frozen tactic script no longer matches the
# reshaped impl, is HONESTLY re-closed inside the proof region — no new
# axiom/lemma/sorry, no weakened obligation.
# ===========================================================================

# pos-reorder — ports nagini's pos-control-reorder: branch on the NEGATED flag, the
# default (unrestricted) arm first. Behaviourally identical on every input; only the
# branch form changes, which is a shape a faithful patch could equally take. The
# frozen `cases editOnly <;> rfl` still closes it (both arms remain definitional).
_POS_REORDER = _swap(_BASE, _IMPL, """  if !editOnly then
    return existing ++ new
  return existing
""")

# pos-append-optional-tail — ports nagini's pos-control-call-once (compute a
# component ONCE into a local and reuse it across both arms). Here the flag selects
# the TAIL contributed by the freshly-created list — empty under restriction — and
# the single append is performed once, unconditionally. Behaviourally identical:
# `existing ++ [] = existing`. The reshape moves the branch inside the appended
# component, so the frozen `rfl` no longer closes the restricted arm; the proof is
# honestly re-closed with `simp` (which discharges `existing ++ [] = existing`).
# If this FAILS => SPEC-TOO-STRONG: the postcondition would be over-fit to one
# executable form of the same selection.
_POS_APPEND = _swap(
    _swap(_BASE, _IMPL, """  let extra := if editOnly then ([] : List α) else new
  return existing ++ extra
"""),
    _PROOF,
    """  intro editOnly existing new
  unfold problem_spec_saveFormset implementation_saveFormset
  cases editOnly <;> simp
""",
)

# adm-f2p-shaped-points — the ADMISSIBILITY lane, landed in AUDIT (the port had
# recorded it N/A for the wrong reason; see the header note). On this total carrier
# the obligation carries no hypothesis, so PRECOND-TOO-STRONG takes its total-carrier
# form: the obligation being UNSATISFIABLE at an F2P-shaped input. That is what these
# three `have`s measure, BY EVALUATION, before the frozen body closes the frozen
# obligation verbatim:
#   * the RESTRICTED F2P shape is SATISFIABLE at the value the fix must produce —
#     `problem_spec … true [1] [2] [1]` holds, i.e. the spec ADMITS omitting the
#     freshly-created list when the restriction is requested;
#   * the spec REFUSES the pre-change value at that SAME point —
#     `¬ problem_spec … true [1] [2] ([1] ++ [2])`, i.e. it is not vacuously true of
#     every result there;
#   * the DEFAULT shape is satisfiable at the unchanged behavior's value.
# Each is the postcondition APPLIED at a concrete point, not a definitional identity
# (the tautology trap: `some 511 = some 511`). Verified as discriminating in audit —
# flipping EITHER of the first two verdicts makes its `have` fail, with `decide`
# reporting the flipped equation false (`¬[1] = if true = true then [1] else …` /
# `[1] ++ [2] = if true = true then [1] else …`), so each measures the spec's verdict
# at that input rather than restating it. The impl region and the rest of the proof
# body are byte-identical to the frozen file, so the only thing this case can fail on
# is the obligation being unsatisfiable — or unfalsifiable — at a shape the fix must
# handle.
_POS_ADMISS = _swap(
    _BASE,
    _PROOF,
    """  intro editOnly existing new
  have _hAdmitRestricted : problem_spec_saveFormset true ([1] : List Nat) [2] [1] := by
    unfold problem_spec_saveFormset; decide
  have _hRefuseRestricted :
      ¬ problem_spec_saveFormset true ([1] : List Nat) [2] ([1] ++ [2]) := by
    unfold problem_spec_saveFormset; decide
  have _hAdmitDefault :
      problem_spec_saveFormset false ([1] : List Nat) [2] ([1] ++ [2]) := by
    unfold problem_spec_saveFormset; decide
  unfold problem_spec_saveFormset implementation_saveFormset
  cases editOnly <;> rfl
""",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits ONLY the impl region, leaving the frozen proof body in
# place. That proof will not close for a reshaped impl — which is precisely why the
# gate reads the WITNESS instead, in a file with the obligation removed.
# ===========================================================================

# THE BUG (ports uniq-always-concat): ignore the flag entirely and always compose in
# the freshly-created list. This is the pre-change behavior.
_RIV_ALWAYS_CONCAT = _swap(_BASE, _IMPL, "  return existing ++ new\n")

# The precise partial-domain rival (ports uniq-restrict-includes-new): the default
# arm stays CORRECT; only the restricted arm still appends the freshly-created list.
_RIV_RESTRICT_INCLUDES_NEW = _swap(_BASE, _IMPL, """  if editOnly then
    return existing ++ new
  return existing ++ new
""")

# Ignore the flag the OTHER way (ports uniq-always-existing): always return the
# already-present list alone, dropping the freshly-created list unconditionally.
_RIV_ALWAYS_EXISTING = _swap(_BASE, _IMPL, "  return existing\n")

# Inverted guard (ports uniq-flip-condition): both arms wrong at once.
_RIV_FLIP = _swap(_BASE, _IMPL, """  if editOnly then
    return existing ++ new
  return existing
""")

# Component order swapped in the default arm (ports uniq-swap-order).
_RIV_SWAP_ORDER = _swap(_BASE, _IMPL, """  if editOnly then
    return existing
  return new ++ existing
""")

# Degenerate near-miss (ports uniq-return-new-only): always return the
# freshly-created list alone, dropping the already-present list.
_RIV_NEW_ONLY = _swap(_BASE, _IMPL, "  return new\n")

# NEW ON THIS CARRIER (no nagini counterpart): the already-present component is
# emitted in REVERSED order in both arms. Nagini could not build this rival — its
# report sequences were opaque, so it had no handle on a component's INTERNAL order;
# this backend's transparent `List α` exposes it, and the spec pins it.
_RIV_REVERSE_EXISTING = _swap(_BASE, _IMPL, """  if editOnly then
    return existing.reverse
  return existing.reverse ++ new
""")

# ADDED IN AUDIT — the MULTIPLICITY clause. Every rival above either drops a
# component, reorders components, or reverses one's internal order; none changes how
# MANY times a component is contributed, so the "exactly once" content of
# `existing ++ new` was the least-probed part of the postcondition. This rival keeps
# the restricted arm correct, keeps both components present, and keeps them in the
# right order — it appends the freshly-created list TWICE in the default arm. Refuted
# only because the spec pins the result to a single concatenation.
_RIV_DOUBLE_NEW = _swap(_BASE, _IMPL, """  if editOnly then
    return existing
  return existing ++ new ++ new
""")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different CORRECT impl (ports nagini's pos-control-reorder): "
            "the selection branches on the NEGATED flag with the unrestricted arm "
            "first. Both arms of the postcondition equation still hold on every input "
            "— only the branch form changes, a shape a faithful patch could equally "
            "take. The `theorem correct_saveFormset` statement is byte-identical and "
            "the frozen tactic body still closes it (no new axiom/lemma/sorry). If it "
            "FAILS => SPEC-TOO-STRONG: the postcondition would be over-fit to one "
            "branch order rather than to the behavior."
        ),
    },
    {
        "id": "pos-append-optional-tail",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_APPEND,
        "rationale": (
            "structurally-different CORRECT impl (ports nagini's pos-control-call-once: "
            "compute a component once into a local, reuse it across both arms). Here "
            "the flag selects the TAIL contributed by the freshly-created list — empty "
            "under restriction — and the single append is performed once, "
            "unconditionally; correct because appending the empty list is the identity. "
            "This moves the branch INSIDE the appended component, so the frozen `rfl` "
            "no longer closes the restricted arm and the proof body is honestly "
            "re-closed with `simp`, keeping the obligation statement byte-identical and "
            "introducing no axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition would be pinned to one executable form of the selection, not "
            "to the selection itself)."
        ),
    },

    {
        "id": "adm-f2p-shaped-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADMISSIBILITY, landed in audit (the port recorded the lane N/A because "
            "the obligation has no precondition hypothesis — the wrong reason). On a "
            "TOTAL carrier PRECOND-TOO-STRONG takes the form of the obligation being "
            "UNSATISFIABLE at an F2P-shaped input, so the proof body discharges the "
            "postcondition at concrete F2P-shaped points BY EVALUATION before closing "
            "the frozen obligation verbatim: the restricted shape is SATISFIED at the "
            "value the fix must produce (result = existing exactly, the "
            "freshly-created list omitted), the SAME point REFUSES the pre-change "
            "value (existing ++ new) so the spec is not vacuously true of every "
            "result there, and the default shape is satisfied at the unchanged "
            "behavior's value. These are the postcondition APPLIED at those points, "
            "not definitional identities. The impl region is byte-identical to the "
            "frozen file and no axiom/lemma/sorry is introduced, so the only thing "
            "this case can fail on is the obligation being unsatisfiable — or "
            "unfalsifiable — at a shape the fix must handle => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-always-append-new",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_CONCAT,
        "refinement": (
            "this is the PRE-CHANGE behavior: the flag is ignored and the "
            "freshly-created list is always composed in. Its faithful real patch is the "
            "un-narrowed original, which is exactly what does NOT resolve. All three "
            "FAIL_TO_PASS tests submit extra forms with the restriction requested and "
            "then assert that the managed collection is UNCHANGED apart from the edits "
            "— no additional rows exist afterwards. Because this rival still persists "
            "the freshly-created group under the restriction, those additional rows do "
            "appear and every F2P assertion on the collection contents fails. A rival "
            "that VERIFIED here would therefore be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the RESTRICTED arm of the postcondition (editOnly = true => "
            "result = existing exactly). At editOnly = true the rival returns "
            "existing ++ new, which differs from `existing` whenever `new` is non-empty. "
            "Attacks the editOnly = true sub-domain and the `new` binder. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # (true, [1], [2]): gold => [1], rival => [1, 2].
        "witness": _wit("true", "[1]", "[2]",
                        "restricted mode with a non-empty freshly-created list: "
                        "gold omits it, the rival appends it"),
    },
    {
        "id": "weak-restricted-arm-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RESTRICT_INCLUDES_NEW,
        "refinement": (
            "the precise PARTIAL-DOMAIN rival: fully correct on the unrestricted "
            "sub-domain, wrong only where the restriction is requested. Its faithful "
            "real patch would thread the new flag everywhere and still compose in the "
            "freshly-created group when the flag is set — so it preserves every "
            "default-mode PASS_TO_PASS test while failing exactly the three "
            "FAIL_TO_PASS tests, which all request the restriction and then assert no "
            "additional rows were created. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the RESTRICTED arm (editOnly = true => result = existing). "
            "Same clause as weak-always-append-new but a strictly NARROWER rival — it "
            "agrees with gold on the whole editOnly = false sub-domain — so it is given "
            "its own witness at a different, more discriminating point: the "
            "already-present list is EMPTY there, so the entire divergence is the "
            "freshly-created component the restricted arm forbids. Attacks the "
            "editOnly = true sub-domain and the `existing` = [] boundary. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # (true, [], [7]): gold => [], rival => [7].
        "witness": _wit("true", "[]", "[7]",
                        "restricted mode, nothing already present: gold returns the "
                        "empty collection, the rival returns the freshly-created one"),
    },
    {
        "id": "weak-always-drop-new",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_EXISTING,
        "refinement": (
            "ignoring the flag the OTHER way — always dropping the freshly-created "
            "group — corresponds to a patch that applies the restriction "
            "unconditionally. It would resolve the three FAIL_TO_PASS tests but "
            "REGRESSES the unchanged default behavior the PASS_TO_PASS set pins: "
            "test_simple_save, test_inline_formsets and test_custom_save_method (among "
            "21 formset PASS_TO_PASS tests) submit extra forms WITHOUT the restriction "
            "and assert the freshly-created rows appear and are returned. Dropping that "
            "group makes them fail, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the DEFAULT arm (editOnly = false => result = existing ++ new). "
            "At editOnly = false the rival returns `existing` alone, which differs "
            "whenever `new` is non-empty. Attacks the editOnly = false sub-domain and "
            "the `new` binder — the mirror image of weak-always-append-new, which is "
            "what makes the flag binder genuinely discriminated in BOTH directions. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (false, [1], [2]): gold => [1, 2], rival => [1].
        "witness": _wit("false", "[1]", "[2]",
                        "default mode: gold appends the freshly-created list, the "
                        "rival drops it"),
    },
    {
        "id": "weak-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLIP,
        "refinement": (
            "the guard is INVERTED: the freshly-created group is composed in exactly "
            "when the restriction is requested, and dropped exactly when it is not. Its "
            "faithful real patch is the branch written the wrong way round, which fails "
            "in both directions at once — it creates additional rows under the "
            "restriction (failing all three FAIL_TO_PASS tests) and omits them by "
            "default (failing the default-mode PASS_TO_PASS saves). It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by BOTH arms simultaneously, which is what distinguishes this "
            "rival from the two single-arm rivals above: under editOnly = true it "
            "returns existing ++ new (violating the restricted arm) and under "
            "editOnly = false it returns existing alone (violating the default arm). "
            "The witness accordingly carries TWO refutations at the SAME "
            "(existing, new) pair and OPPOSITE flag values, so it demonstrates the "
            "double failure rather than sharing a single-arm point. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # (false, [3], [4]): gold => [3, 4], rival => [3].
        # (true,  [3], [4]): gold => [3],    rival => [3, 4].
        "witness": (
            _wit("false", "[3]", "[4]",
                 "default mode under the inverted guard: gold appends the "
                 "freshly-created list, the rival drops it")
            + "\n\n"
            + _wit("true", "[3]", "[4]",
                   "restricted mode under the inverted guard, same inputs: gold omits "
                   "the freshly-created list, the rival appends it")
        ),
    },
    {
        "id": "weak-swapped-component-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP_ORDER,
        "refinement": (
            "the restricted arm is left CORRECT; in the default arm the two components "
            "are emitted in the opposite order — freshly-created group first, "
            "already-present group second. Its faithful real patch composes the two "
            "collaborator results the wrong way round, and the returned collection is "
            "observed positionally: the default-mode PASS_TO_PASS saves assert the "
            "edited already-present objects come first and the freshly-created ones "
            "after (test_simple_save / test_inline_formsets compare the returned "
            "sequence). Reversing the components fails those sequence assertions, so it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ORDERING half of the DEFAULT arm (editOnly = false => "
            "result = existing ++ new, in that order). This is the clause no "
            "drop/append rival touches: the rival returns the right MULTISET of "
            "elements and only the order is wrong, so it is refutable only because the "
            "spec pins concatenation order. The witness uses a 2-element "
            "already-present list so the two components cannot coincide. Attacks the "
            "component-order clause and the `existing` binder at length 2. If it "
            "VERIFIES => SPEC-TOO-WEAK (the order guarantee would be hollow)."
        ),
        # (false, [1, 2], [3]): gold => [1, 2, 3], rival => [3, 1, 2].
        "witness": _wit("false", "[1, 2]", "[3]",
                        "default mode: gold emits the already-present list first, the "
                        "rival emits the freshly-created list first"),
    },
    {
        "id": "weak-drop-existing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEW_ONLY,
        "refinement": (
            "always returning the freshly-created group ALONE corresponds to a patch "
            "that dropped the already-present group entirely. It would fail to report "
            "the edited already-present objects that every save test observes "
            "(test_simple_save and the FAIL_TO_PASS edit submissions both assert the "
            "edited existing object is persisted and returned) while still creating "
            "additional rows under the restriction — failing both PASS_TO_PASS and "
            "FAIL_TO_PASS. It does NOT resolve. Supporting near-miss."
        ),
        "rationale": (
            "REJECTED by both arms: neither `existing` (restricted) nor "
            "`existing ++ new` (default) equals `new`. The witness is placed at "
            "(false, [5], []) — the freshly-created list is EMPTY there, so the "
            "refutation isolates the loss of the already-present component alone and "
            "does not double as one of the append/drop points above. Attacks the "
            "`existing` binder and the `new` = [] boundary, the only witness in this "
            "battery to probe an empty freshly-created list. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # (false, [5], []): gold => [5], rival => [].
        "witness": _wit("false", "[5]", "[]",
                        "default mode with nothing freshly created: gold returns the "
                        "already-present list, the rival returns the empty collection"),
    },
    {
        "id": "weak-reordered-existing-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE_EXISTING,
        "refinement": (
            "the already-present component is emitted in REVERSED internal order, in "
            "both modes. Its faithful real patch iterates the already-present forms "
            "back-to-front while persisting them, which changes the order in which the "
            "edits are applied and the order of the returned collection. The formset "
            "PASS_TO_PASS saves compare the returned sequence positionally "
            "(test_simple_save, test_inline_formsets), so a reversed group fails them; "
            "and it does nothing about the restriction the FAIL_TO_PASS tests demand, "
            "so it does not resolve those either."
        ),
        "rationale": (
            "REJECTED by the ORDER-PRESERVATION content of BOTH arms: each arm pins the "
            "already-present component to the input list itself, so its internal order "
            "is fixed. No nagini counterpart exists — that carrier abstracted the "
            "component to an opaque report sequence and had no handle on its internal "
            "order — so this rival is NEW work on this carrier, added because the "
            "transparent `List α` exposes a clause the ported rivals leave unattacked. "
            "The witness is stated in the RESTRICTED mode with an empty freshly-created "
            "list, so the refutation is attributable to the existing component's order "
            "alone and to no other clause. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (true, [1, 2], []): gold => [1, 2], rival => [2, 1].
        "witness": _wit("true", "[1, 2]", "[]",
                        "restricted mode: gold preserves the already-present order, "
                        "the rival reverses it"),
    },
    {
        "id": "weak-duplicated-new-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DOUBLE_NEW,
        "refinement": (
            "the freshly-created component is contributed TWICE in the default arm. "
            "Its faithful real patch composes that collaborator's result into the "
            "return value twice over, so every freshly-created object is reported "
            "twice by a default-mode save. The default-mode PASS_TO_PASS saves compare "
            "the returned sequence positionally and by length (test_simple_save, "
            "test_inline_formsets), so a doubled tail fails them; and it does nothing "
            "about the restriction the FAIL_TO_PASS tests demand, so it does not "
            "resolve those either."
        ),
        "rationale": (
            "REJECTED by the MULTIPLICITY content of the DEFAULT arm (editOnly = false "
            "=> result = existing ++ new — each component contributed EXACTLY ONCE). "
            "Added in audit: every other rival in this battery either drops a "
            "component, swaps the two components, or reverses one component's internal "
            "order, so none of them varies how MANY times a component appears — the "
            "'exactly once' clause was the least-probed part of the postcondition. "
            "This rival keeps both components present, in the correct order, with the "
            "restricted arm fully correct, so it is refutable ONLY by that clause. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (false, [1], [2]): gold => [1, 2], rival => [1, 2, 2].
        "witness": _wit("false", "[1]", "[2]",
                        "default mode: gold contributes the freshly-created list "
                        "exactly once, the rival contributes it twice"),
    },
]


# The frozen axioms region is empty — no opaque callee is consumed, since the two
# collaborator results ARE the modeled inputs. The axiom lane belongs to G-AX and is
# ignored by this gate regardless.
AXIOM_TESTS = []
