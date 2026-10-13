# properties.py — G-PBT falsification battery for django__django-15695 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   applyIndexRenameForward
#     (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String)
#       : Option (Index × Index)
#   The forward-application decision of a relabel step: whether to emit the
#   underlying relabel action, and with which index pair. The single postcondition
#   pins the result to the verdict of a three-clause total case split, each clause
#   grounded in the inputs:
#     (1) if the step is NOT permitted, no action is emitted (result = none);
#     (2) if permitted but the starting index ALREADY bears the target name, no
#         action is emitted (result = none) — the load-bearing no-op guard;
#     (3) if permitted and the starting name DIFFERS from the target, exactly the
#         relabel of the starting index to the target index is emitted
#         (result = some (oldIndex, newIndex)).
#   The oracle is total and transparent (no opaque callee, no answer-key), so
#   `decide` computes it at any literal input — witnesses need no conditioning.
#
# CARRIER NOTE: the nagini sibling modeled the same decision as a MUTATION on an
# `editor`/`old_index` pair behind full fractional permission, with an observable
# `rename_issued` flag and a `renamed_to` target, and a deep-model callee
# `issue_rename` carrying the load-bearing DOMAIN restriction old != new. This
# backend models the identical decision as a referentially-transparent total
# function returning `Option (Index × Index)`: "which relabel is emitted, if any."
# The nagini "observable rename effect" (rename_issued True + renamed_to == target)
# becomes the returned `some (oldIndex, newIndex)`; the "no rename issued" state
# becomes `none`; the domain restriction is folded into clause (2). Every clause the
# nagini battery attacked has a counterpart here, and each is refutable at a concrete
# literal input.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME / RESETTABLE-WITNESS (nagini weak-resettable-witness, weak-direct-write):
#     these attack the observable rename FLAG independently of the final name — a
#     rival that writes the field directly but never sets the flag, or issues then
#     resets the flag. Lean is referentially transparent: there is no separate
#     mutable flag to reset or bypass; the emitted action IS the result. The
#     "issued the wrong / no observable action while the name looks right" cheat has
#     no separate carrier here, but its ESSENCE — emitting no action where the spec
#     demands one, or an action where it demands none — is covered directly by the
#     always-none and unconditional rivals below (clauses 2 and 3). The frame-write
#     mechanism itself is VACUOUS on this carrier.
#   * NON-TERMINATION (nagini nonterm-differ-branch-loop, nonterm-self-recursion):
#     these exploit Nagini's partial-correctness default, where a diverging body
#     satisfies every Ensures vacuously. This bundle is vanilla Lean 4 + Mathlib —
#     there is no `loom.semantics.termination` knob, and a plain `def` must be shown
#     total, i.e. the carrier is unconditionally "total"-semantics. The class is
#     VACUOUS here, and this is MEASURED rather than asserted (audit, 4 builds):
#       - a self-recursive `def` (no decreasing measure) does not build at all:
#         `error: fail to show termination for implementation_…`. The file is
#         rejected by the totality checker before the spec is ever consulted, so the
#         rejection is not attributable to the postcondition.
#       - the only escape hatch, `partial def`, builds the definition but is OPAQUE
#         to the kernel, so no witness can attest to it: a `decide` refutation at a
#         literal input fails with `Tactic \`unfold\` failed to unfold
#         implementation_…` against BOTH the partial rival and the plain one. A
#         witness that does not hold of the rival is `witness-unproven`, which the
#         gate scores MALFORMED-TESTS — an inconclusive, never a pass.
#     So a diverging rival is not merely unattacked here, it is unshippable: it
#     cannot carry the discriminating witness this backend requires. Recorded as a
#     VACUOUS class (not a known spec hole — that disposition is velvet's).
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. The decision
#     is modeled DEEPLY over transparent data, so there is no consumed axiom anyway
#     (mapping.md: empty axioms region, axiom_check.py is a skip stub).
from pathlib import Path

INSTANCE = "django__django-15695"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- frozen anchors (each lies ENTIRELY inside a region and is unique in the file) ---

# The impl body proper (all guards + the final emit), inside impl-start/impl-end.
_IMPL_BODY = (
    "  if canMigrate = false then\n"
    "    return none\n"
    "  if oldIndex.name = newName then\n"
    "    return none\n"
    "  return some (oldIndex, newIndex)"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl body anchor drifted"

# The impl signature tail + body (used by the functional-form positive, which drops
# the `Id.run do`). Still entirely inside the impl region.
_IMPL_TAIL = (
    "    Option (Index × Index) := Id.run do\n"
    "  if canMigrate = false then\n"
    "    return none\n"
    "  if oldIndex.name = newName then\n"
    "    return none\n"
    "  return some (oldIndex, newIndex)"
)
assert _BASE.count(_IMPL_TAIL) == 1, "impl tail anchor drifted"

# The frozen proof body (tactic lines only, inside proof-start/proof-end).
_PROOF = (
    "  intro canMigrate oldIndex newIndex newName\n"
    "  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h\n"
    "    simp [Id.run, h, pure]\n"
    "  · intro h1 h2\n"
    "    simp [Id.run, h1, h2, pure, bind]\n"
    "  · intro h1 h2\n"
    "    simp [Id.run, h1, h2, pure, bind]"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG). Each is a
# structurally-different but behaviourally-IDENTICAL correct impl, reproven with a
# byte-identical `theorem correct_applyIndexRenameForward` STATEMENT and no new
# axiom/lemma/sorry.
# ===========================================================================

# pos-reorder: reframe the decision as a NESTED positive branch — emit the action
# only when permitted AND the names differ, and fall through to `none` otherwise —
# instead of the frozen two-early-return guard cascade. Same verdict on every input;
# only the branch shape changes (the shape a faithful patch could equally take). The
# frozen `simp`-style proof no longer closes the reshaped branch tree, so the proof
# body is honestly re-closed. Ports nagini's pos-control-reorder (there: the guard
# reframed as the negated `if old != new: issue_rename`).
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _IMPL_BODY,
        "  if canMigrate = true then\n"
        "    if oldIndex.name ≠ newName then\n"
        "      return some (oldIndex, newIndex)\n"
        "  return none",
    ),
    _PROOF,
    "  intro canMigrate oldIndex newIndex newName\n"
    "  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h\n"
    "    subst h\n"
    "    rfl\n"
    "  · intro h1 h2\n"
    "    subst h1\n"
    "    simp only [Id.run, ite_true]\n"
    "    rw [if_neg (by simp [h2])]\n"
    "    rfl\n"
    "  · intro h1 h2\n"
    "    subst h1\n"
    "    simp only [Id.run, ite_true]\n"
    "    rw [if_pos h2]\n"
    "    rfl",
)

# pos-functional: the same decision written as a single pure conditional expression
# (no `Id.run do`), collapsing the three-way case split into one `if … then … else`.
# Behaviourally identical; reproven with the appropriate `simp`. Ports the general
# "cheapest honest CORRECT impl of a different shape" idea; it also shows the spec is
# not over-fit to the imperative early-return form.
_POS_FUNC = _swap(
    _swap(
        _BASE,
        _IMPL_TAIL,
        "    Option (Index × Index) :=\n"
        "  if canMigrate = true && oldIndex.name ≠ newName then some (oldIndex, newIndex) else none",
    ),
    _PROOF,
    "  intro canMigrate oldIndex newIndex newName\n"
    "  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h\n"
    "    subst h\n"
    "    simp\n"
    "  · intro h1 h2\n"
    "    subst h1\n"
    "    simp [h2]\n"
    "  · intro h1 h2\n"
    "    subst h1\n"
    "    simp [h2]",
)


# ===========================================================================
# ADMISSIBILITY (must VERIFY, else PRECOND-TOO-STRONG). The frozen obligation is
# universally quantified with NO precondition hypothesis, so the naive reading is
# "nothing could be too strong here". That reading is wrong, and it is what the
# earlier revision of this battery recorded. The analogue of PRECOND-TOO-STRONG on a
# TOTAL carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input — a spec whose three clauses jointly contradict each other at the
# configuration the F2P actually presents would still let the frozen file build
# (`∀ x, P x` is discharged over the shape the impl happens to have) while pinning a
# behaviour no implementation can exhibit. The positive below settles that by
# EVALUATION: before closing the frozen obligation verbatim, it discharges the
# obligation as a `have` at two concrete literal inputs, the re-application-shaped
# one (permitted, starting entry ALREADY bearing the target name — the configuration
# a second forward application presents, which is exactly what the F2P exercises)
# and a genuine forward change (permitted, names differing). `decide` computes both
# sides, so each `have` is a real inhabitant of the spec at that point, not a
# restatement of it. Ports nagini admiss-fshaped-reapply, whose witness constructed
# the same equal-names re-apply input on the mutable carrier.
#
# The `have`s are inside the PROOF region (the only region a positive may edit
# besides impl), the impl is the frozen one byte-for-byte, and the
# `theorem correct_…` STATEMENT is untouched — so variant_scope sees a legitimate
# reprove. They are `clear`ed before the frozen tactics run, so the frozen proof
# body closes the obligation exactly as it does in the frozen file.
_ADMISS = _swap(
    _BASE,
    _PROOF,
    "  -- The obligation is SATISFIABLE at a concrete re-application-shaped input:\n"
    "  -- permitted, with the starting entry already bearing the target name (the\n"
    "  -- configuration a second forward application presents). Discharged by\n"
    "  -- evaluation, so this is a real inhabitant of the spec at that point.\n"
    "  have admissible_at_reapply :\n"
    "      problem_spec_applyIndexRenameForward true { name := \"idx_t\" }\n"
    "        { name := \"idx_t\" } \"idx_t\"\n"
    "        (implementation_applyIndexRenameForward true { name := \"idx_t\" }\n"
    "          { name := \"idx_t\" } \"idx_t\") := by\n"
    "    unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward\n"
    "    decide\n"
    "  -- ... and at a genuine forward change (permitted, names differing), so the\n"
    "  -- clauses do not jointly exclude the emitting sub-domain either.\n"
    "  have admissible_at_change :\n"
    "      problem_spec_applyIndexRenameForward true { name := \"idx_s\" }\n"
    "        { name := \"idx_t\" } \"idx_t\"\n"
    "        (implementation_applyIndexRenameForward true { name := \"idx_s\" }\n"
    "          { name := \"idx_t\" } \"idx_t\") := by\n"
    "    unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward\n"
    "    decide\n"
    "  clear admissible_at_reapply admissible_at_change\n" + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; each carries a witness that elaborates
# against the rival and FAILS on the frozen solution. The rivals collectively vary
# every input binder: canMigrate (both values), the oldIndex.name vs newName equality
# (both branches), and the identity/order of the emitted index pair.
# ===========================================================================

# weak-unconditional: drop the equal-names no-op guard — emit the relabel whenever
# the step is permitted, EVEN when the starting index already bears the target name.
# This IS the prepatch bug. Attacks clause (2).
_RIV_UNCOND = _swap(
    _BASE,
    _IMPL_BODY,
    "  if canMigrate = false then\n"
    "    return none\n"
    "  return some (oldIndex, newIndex)",
)

# weak-always-none: never emit any action. Correct only on the not-permitted and
# equal-names sub-domains; on the permitted-and-differing sub-domain it emits none
# where the spec demands the relabel. Attacks clause (3). Ports nagini
# partial-domain-always-noop / weak-direct-write (the "final name pinned but no
# observable action emitted" cheat, which on this carrier is simply `none`).
_RIV_NONE = _swap(
    _BASE,
    _IMPL_BODY,
    "  return none",
)

# weak-ignore-canmigrate: drop the not-permitted guard — decide purely on the name
# comparison. Emits the relabel on the differing-names branch even when the step is
# NOT permitted. Attacks clause (1) / the canMigrate binder (which every other rival
# holds at a value where clause (1) is vacuous). No nagini counterpart in the modeled
# surface (nagini fixed canMigrate upstream); added so the canMigrate=false binder is
# actually varied by a reject witness rather than left unprobed.
_RIV_IGNORE_MIG = _swap(
    _BASE,
    _IMPL_BODY,
    "  if oldIndex.name = newName then\n"
    "    return none\n"
    "  return some (oldIndex, newIndex)",
)

# weak-swapped-pair: emit the relabel with the index pair REVERSED — the target index
# as the "from" and the starting index as the "to". Satisfies clauses (1) and (2)
# exactly, but on the differing-names branch emits `some (newIndex, oldIndex)` where
# the spec pins `some (oldIndex, newIndex)`. Attacks the PAIR-IDENTITY component of
# clause (3): the spec sees not just THAT an action is emitted but WHICH pair. Ports
# nagini's target-pin (renamed_to == new_name) attack onto the transparent carrier.
_RIV_SWAP = _swap(
    _BASE,
    _IMPL_BODY,
    "  if canMigrate = false then\n"
    "    return none\n"
    "  if oldIndex.name = newName then\n"
    "    return none\n"
    "  return some (newIndex, oldIndex)",
)


# weak-guard-wrong-operand: keep a no-op guard, but compare the TARGET entry's name
# against the target name instead of the STARTING entry's name. The guard is then a
# tautology on every faithful input (the target entry is the one resolved BY that
# name, so its name always equals it), which means the no-op case can never fire and
# the rival collapses to the unconditional emit — while LOOKING like it has the
# guard. Added by the audit: every pre-existing rival either has the guard verbatim
# or has no guard at all, so the battery never probed WHICH operand the guard reads,
# and that operand is the whole content of clause (2).
_RIV_WRONG_OPERAND = _swap(
    _BASE,
    _IMPL_BODY,
    "  if canMigrate = false then\n"
    "    return none\n"
    "  if newIndex.name = newName then\n"
    "    return none\n"
    "  return some (oldIndex, newIndex)",
)


def _wit(args, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal input, closed by `decide`. `args` is the argument tuple as Lean literal
    text. Elaborates against a rival that diverges from the frozen verdict there, and
    fails on gold (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_applyIndexRenameForward {args}\n"
        f"    (implementation_applyIndexRenameForward {args}) := by\n"
        f"  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the decision is reframed as a "
            "nested positive branch (emit only when permitted AND names differ; fall "
            "through to none) rather than the frozen two-early-return cascade. The "
            "verdict is identical on every input; only the branch shape changes. The "
            "frozen `theorem correct_applyIndexRenameForward` statement is kept "
            "byte-identical and the proof body is honestly re-closed (no new "
            "axiom/lemma/sorry). If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to one branch order). Ports nagini pos-control-reorder."
        ),
    },
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNC,
        "rationale": (
            "the same decision as a single pure conditional expression (no Id.run do), "
            "collapsing the three-way split into one if/then/else. Behaviourally "
            "identical; reproven with the frozen theorem statement intact and no new "
            "assumption. Shows the postcondition is not over-fit to the imperative "
            "early-return form. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-fshaped-reapply",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The frozen obligation carries no precondition hypothesis, so the "
            "PRECOND-TOO-STRONG analogue on this total carrier is the obligation "
            "being UNSATISFIABLE at an F2P-shaped input: a spec whose clauses "
            "jointly contradict each other at the configuration a second forward "
            "application presents would still let the frozen file build while "
            "pinning behaviour nothing can exhibit. This positive discharges the "
            "obligation BY EVALUATION as a `have` at two concrete literal inputs — "
            "the re-application-shaped one (permitted, starting entry already "
            "bearing the target name) and a genuine forward change (permitted, "
            "names differing) — before closing the frozen obligation verbatim. Each "
            "`have` is computed by `decide`, so it is a real inhabitant of the spec "
            "at that point rather than a restatement. Audit-measured: negating the "
            "re-apply `have` fails with `Tactic decide proved that the proposition "
            "... is false`, and pinning the WRONG result there also fails, so the "
            "`have`s track their claims. If this FAILS => PRECOND-TOO-STRONG (the "
            "spec is unsatisfiable at the input the F2P exercises). Ports nagini "
            "admiss-fshaped-reapply."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-unconditional-rename",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNCOND,
        "refinement": (
            "This IS the prepatch behaviour: dropping the no-op guard so the step "
            "emits the relabel unconditionally when permitted. The F2P re-applies the "
            "forward step when the starting entry is already AT the target name, so "
            "the unconditional emit asks the backend to relabel a name to a name "
            "already in use, and the operation fails. The faithful real patch "
            "therefore does NOT resolve the F2P — a verifying rival here is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (2): with the step permitted and the starting name "
            "equal to the target, the spec pins result = none, but the rival emits "
            "some (oldIndex, newIndex). Attacks clause (2) / the oldIndex.name = "
            "newName sub-domain of the equality binder. If it VERIFIES => SPEC-TOO-WEAK "
            "(the spec would admit the prepatch bug)."
        ),
        # canMigrate=true, oldIndex.name == newName == "x": gold => none, rival => some.
        "witness": _wit(
            'true { name := "x" } { name := "y" } "x"',
            "permitted + equal names: gold emits none, rival emits the relabel",
        ),
    },
    {
        "id": "weak-always-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NONE,
        "refinement": (
            "A step that NEVER emits the relabel is correct only when it is not "
            "permitted or the name already matches; on the permitted-and-differing "
            "sub-domain it performs no relabel at all, so a genuine forward name change "
            "leaves the entry under its old name and the rename tests asserting the "
            "target name FAIL — it does not resolve. Ports nagini "
            "partial-domain-always-noop and the direct-write-no-observable-action "
            "cheat (which on this carrier is just returning none)."
        ),
        "rationale": (
            "REJECTED by clause (3): with the step permitted and the starting name "
            "differing from the target, the spec pins result = some (oldIndex, "
            "newIndex), but the rival returns none. Attacks clause (3) / the "
            "oldIndex.name ≠ newName sub-domain. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # canMigrate=true, names differ ("a" vs "b"): gold => some, rival => none.
        "witness": _wit(
            'true { name := "a" } { name := "b" } "b"',
            "permitted + differing names: gold emits the relabel, rival emits none",
        ),
    },
    {
        "id": "weak-ignore-permitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_MIG,
        "refinement": (
            "A step that decides purely on the name comparison, ignoring whether the "
            "operation is permitted on the connection, emits the relabel even when it "
            "is NOT permitted. The faithful real patch would perform the schema change "
            "on a connection where the migration must be a no-op, diverging from the "
            "guarded behaviour the operation requires — it does not resolve."
        ),
        "rationale": (
            "REJECTED by clause (1): with the step not permitted, the spec pins result "
            "= none regardless of the names, but the rival emits some (oldIndex, "
            "newIndex) on the differing-names branch. Attacks clause (1) / the "
            "canMigrate = false binder — the ONE binder every other rival holds at a "
            "value where clause (1) is vacuous. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # canMigrate=false, names differ: gold => none, rival => some.
        "witness": _wit(
            'false { name := "a" } { name := "b" } "b"',
            "not permitted + differing names: gold emits none, rival emits the relabel",
        ),
    },
    {
        "id": "weak-guard-wrong-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_OPERAND,
        "refinement": (
            "A step that keeps a no-op guard but tests the TARGET entry's name "
            "against the target name has a guard that is a tautology on every "
            "faithful input: the target entry is the one resolved BY that name, so "
            "its name always equals it and the no-op branch can never fire. The "
            "faithful real transliteration therefore behaves exactly like the "
            "unguarded prepatch step — it re-emits the relabel when the starting "
            "entry is already at the target name, asking the backend to relabel a "
            "name to a name already in use, and the operation fails. It does NOT "
            "resolve, while presenting a guard that looks right on inspection."
        ),
        "rationale": (
            "REJECTED by clause (2): with the step permitted and the starting name "
            "equal to the target, the spec pins result = none; the rival's guard "
            "reads the wrong operand, does not fire, and it emits "
            "some (oldIndex, newIndex). Attacks WHICH operand clause (2) compares — "
            "the whole content of that clause, and the one thing no other rival "
            "probes (each either has the guard verbatim or has none at all). If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # canMigrate=true, oldIndex.name = "b" = newName, newIndex.name = "c".
        # gold: the starting entry is already at the target name, so its guard fires
        #   => none.
        # rival: its guard compares newIndex.name ("c") to newName ("b"), which
        #   DIFFER, so the guard misses => some (oldIndex, newIndex).
        # The differing newIndex.name is what separates the two guards at this point.
        "witness": _wit(
            'true { name := "b" } { name := "c" } "b"',
            "permitted + starting entry already at the target name: gold's guard "
            "fires (none), the rival's reads the target entry instead and misses",
        ),
    },
    {
        "id": "weak-swapped-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP,
        "refinement": (
            "A step that emits the relabel with the index pair REVERSED (target as the "
            "'from', starting entry as the 'to') fires the schema relabel in the wrong "
            "direction: the real backend would attempt to rename the target index to "
            "the old name rather than the reverse, so the forward operation does not "
            "produce the target name and the rename tests FAIL — it does not resolve."
        ),
        "rationale": (
            "REJECTED by the PAIR-IDENTITY component of clause (3): the spec pins "
            "result = some (oldIndex, newIndex), but the rival returns some (newIndex, "
            "oldIndex). Attacks the WHICH-pair content of clause (3), not merely THAT "
            "an action is emitted (the oldIndex/newIndex binders). Ports nagini's "
            "target-pin attack. If it VERIFIES => SPEC-TOO-WEAK (the spec would fail to "
            "pin the relabel direction)."
        ),
        # canMigrate=true, distinct names + distinct indices: gold => some(old,new),
        # rival => some(new,old); the two differ because oldIndex ≠ newIndex.
        "witness": _wit(
            'true { name := "old" } { name := "new" } "new"',
            "permitted + differing names: gold emits (old,new), rival emits (new,old)",
        ),
    },
]


# No @ContractOnly axioms and no opaque callees: the forward-application decision is
# modeled DEEPLY over transparent data, so the axiom lane is vacuous here and belongs
# to G-AX regardless.
AXIOM_TESTS = []
