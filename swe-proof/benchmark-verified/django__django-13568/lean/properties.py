# properties.py — G-PBT falsification battery for django__django-13568 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   checkUserModel : String → Bool → Bool → Bool → Bool → Bool → Bool
#                    → List ConstraintInfo → List String
#   Accumulates, IN ORDER, the diagnostic codes emitted by several independent
#   sub-checks over a user model: a required-fields-shape code, a
#   required-fields-membership code, then — ONLY when the login field is neither
#   directly unique nor guaranteed unique by an unconditional uniqueness constraint
#   ranging over exactly that one field — a login-field-uniqueness code whose
#   severity is an error under the default authentication backend and a warning
#   otherwise, and finally the two attribute-method codes. The single postcondition
#   pins the result to the exact ordered concatenation of these five contributions,
#   each grounded in the function's own inputs.
#
# CARRIER NOTE (why this port is wider than nagini's): the nagini sibling abstracted
# the whole check to a single int code for the ONE login-field diagnostic (with the
# other sub-checks unmodeled and the read-only constraint lists behind fractional
# permissions). This backend models the FULL ordered result list over a transparent
# `ConstraintInfo` carrier, so every independent contribution (not just the login
# arm) is an attackable clause here. The port therefore attacks each arm directly —
# see the framing-drop rivals — which nagini's int-code carrier could not express.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's #1 class: the constraint lists were Acc(...,1/2)
#     read-only). Lean is referentially transparent — no aliasing, no permissions —
#     so a "write-back into a read-only input" rival is not expressible and the whole
#     lane is VACUOUS here. See 'assessment'.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them.
#
# LANE LANDED BY AUDIT:
#   * ADMISSIBILITY. The port dropped this lane claiming "the lean obligation has NO
#     precondition hypothesis, so nothing can be PRECOND-TOO-STRONG". That reason is
#     wrong: the analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at
#     exactly an F2P-shaped input, which is a real and testable failure mode — a
#     postcondition that pins the result list to something no impl can produce at the
#     input the change is about would still be an unconditional ∀, and would still be
#     over-strong. `admiss-f2p-shaped` tests it directly: it discharges the frozen
#     postcondition BY EVALUATION at the F2P-shaped input (and at its two near-miss
#     siblings) as `have`s, then closes the frozen obligation verbatim.
from pathlib import Path

INSTANCE = "django__django-13568"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). The login-field guard block, verbatim: --------------------
_GUARD = (
    "    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then\n"
    "      if usesDefaultBackend then\n"
    '        errors := errors ++ ["auth.E003"]\n'
    "      else\n"
    '        errors := errors ++ ["auth.W004"]'
)
assert _BASE.count(_GUARD) == 1, "login-guard impl anchor drifted"

# The four unchanged sub-check contribution blocks (framing arms), verbatim: ------
_E001 = ('    if reqFieldsBadShape then\n      errors := errors ++ ["auth.E001"]')
_E002 = ('    if usernameInRequired then\n      errors := errors ++ ["auth.E002"]')
_C009 = ('    if isAnonymousMethod then\n      errors := errors ++ ["auth.C009"]')
_C010 = ('    if isAuthenticatedMethod then\n      errors := errors ++ ["auth.C010"]')
for _a in (_E001, _E002, _C009, _C010):
    assert _BASE.count(_a) == 1, f"framing anchor drifted: {_a!r}"

# The frozen pure-region coverage helper and the frozen tactic body. Anchored so a
# Solution.lean edit fails loudly here instead of silently shipping a case whose
# obligation is closed some other way.
_INTRO = (
    "  intro usernameField reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend\n"
    "    isAnonymousMethod isAuthenticatedMethod constraints\n"
)
_GOLD_TAC = (
    _INTRO
    + "  unfold problem_spec_checkUserModel implementation_checkUserModel\n"
    "  cases reqFieldsBadShape <;> cases usernameInRequired <;> cases fieldUnique <;>\n"
    "    cases usesDefaultBackend <;> cases isAnonymousMethod <;> cases isAuthenticatedMethod <;>\n"
    "    cases coveredByUnconditionalUniqueConstraint constraints usernameField <;>\n"
    "    simp [Id.run] <;> rfl\n"
)
assert _BASE.count(_GOLD_TAC) == 1, "frozen tactic body anchor drifted"
# The closing half must survive verbatim in the admissibility variant: the probes go
# BETWEEN `intro` and it, so the gold discharge is reproven, never replaced.
_GOLD_TAC_CLOSE = _GOLD_TAC.split(_INTRO, 1)[1]


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-nested-guard: structurally DIFFERENT but behaviourally identical. The frozen
# impl decides the login arm with a single conjunctive guard; this control nests the
# two conditions into separate `if`s (the field's own uniqueness, then the declared
# constraints), which is the shape a faithful patch could equally take. The result
# value is identical on every input, and the carried proof (`cases … <;> simp <;>
# rfl`) still closes because the case split covers the nested branches. If it FAILS
# => SPEC-TOO-STRONG (a faithful, structurally-different correct impl rejected).
_POS_NESTED = (
    "    if !fieldUnique then\n"
    "      if !coveredByUnconditionalUniqueConstraint constraints usernameField then\n"
    "        if usesDefaultBackend then\n"
    '          errors := errors ++ ["auth.E003"]\n'
    "        else\n"
    '          errors := errors ++ ["auth.W004"]'
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (must VERIFY) — landed by audit; the lane was dropped for the
# wrong reason (see the header). The frozen obligation IS an unconditional ∀, so
# no HYPOTHESIS can be over-strong — but on a total carrier the analogue is the
# postcondition being UNSATISFIABLE at exactly the input the change is about. If
# `problem_spec` pinned the result to a list the impl cannot produce at the
# F2P-shaped input, the obligation would be unprovable there and the whole cell
# would be defective in a way no rival detects. These probes evaluate the frozen
# postcondition at that input, as `have`s, BEFORE closing the frozen obligation
# verbatim — so the case rests on the spec being satisfiable there, not on the
# proof script. Each probe is a `decide` on a closed Prop: it is a real
# evaluation, not a discharge of something put in front of it. (Checked: asserting
# the OPPOSITE result at the F2P input makes `decide` report the proposition `is
# false` and the case FAILS, so these steps genuinely evaluate the spec.)
# ---------------------------------------------------------------------------
_ADMISS_PROBES = (
    # (1) The F2P-shaped input: login field NOT directly unique, one UNCONDITIONAL
    # uniqueness constraint ranging over exactly that field => the accumulated
    # diagnostic list is EMPTY. This is the sub-domain the change introduces.
    "  have admissible_covered_default :\n"
    '      problem_spec_checkUserModel "username" false false false true false false\n'
    '        [⟨true, false, ["username"]⟩] [] := by\n'
    "    unfold problem_spec_checkUserModel\n"
    "    decide\n"
    # (2) The same model under a NON-default backend => still EMPTY (the F2P
    # asserts an empty list under both backend settings).
    "  have admissible_covered_custom_backend :\n"
    '      problem_spec_checkUserModel "username" false false false false false false\n'
    '        [⟨true, false, ["username"]⟩] [] := by\n'
    "    unfold problem_spec_checkUserModel\n"
    "    decide\n"
    # (3) The near-miss: a CONDITIONAL uniqueness constraint over the same field
    # does NOT cover, so the error code is due under the default backend.
    "  have admissible_conditional_default :\n"
    '      problem_spec_checkUserModel "username" false false false true false false\n'
    '        [⟨true, true, ["username"]⟩] ["auth.E003"] := by\n'
    "    unfold problem_spec_checkUserModel\n"
    "    decide\n"
    # (4) …and the warning arm of that same near-miss under a custom backend.
    "  have admissible_conditional_custom :\n"
    '      problem_spec_checkUserModel "username" false false false false false false\n'
    '        [⟨true, true, ["username"]⟩] ["auth.W004"] := by\n'
    "    unfold problem_spec_checkUserModel\n"
    "    decide\n"
    "  clear admissible_covered_default admissible_covered_custom_backend\n"
    "  clear admissible_conditional_default admissible_conditional_custom\n"
)
_ADMISS = _swap(_BASE, _GOLD_TAC, _INTRO + _ADMISS_PROBES + _GOLD_TAC_CLOSE)
assert _GOLD_TAC_CLOSE in _ADMISS, "admissibility case no longer closes with the gold body"


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness.
# ---------------------------------------------------------------------------

# weak-prepatch: the PRE-PATCH login guard — the diagnostic is suppressed ONLY by
# the field's own direct uniqueness; the declared constraints are never consulted.
_WEAK_PREPATCH = (
    "    if !fieldUnique then\n"
    "      if usesDefaultBackend then\n"
    '        errors := errors ++ ["auth.E003"]\n'
    "      else\n"
    '        errors := errors ++ ["auth.W004"]'
)

# weak-swap-regime: keeps the true suppression condition but INVERTS the severity —
# warning under the default backend, error otherwise.
_WEAK_SWAP = (
    "    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then\n"
    "      if usesDefaultBackend then\n"
    '        errors := errors ++ ["auth.W004"]\n'
    "      else\n"
    '        errors := errors ++ ["auth.E003"]'
)

# weak-always-error: drops the suppression condition — ALWAYS emits the login
# diagnostic (at the regime-selected severity), never suppresses.
_WEAK_ALWAYS_ERR = (
    "    if usesDefaultBackend then\n"
    '      errors := errors ++ ["auth.E003"]\n'
    "    else\n"
    '      errors := errors ++ ["auth.W004"]'
)

# weak-always-suppress: removes the login arm entirely — never emits the diagnostic.
_WEAK_ALWAYS_SUP = "    -- login-field uniqueness diagnostic suppressed unconditionally"


# --- framing-drop rivals: each removes ONE unchanged sub-check's contribution.
# These attack an independent arm of the ordered result that nagini's int-code
# carrier could not reach (see CARRIER NOTE). --------------------------------------
_DROP = "    -- unchanged sub-check contribution removed"


# --- coverage-clause rivals (landed by audit). Every rival above REUSES the frozen
# `coveredByUnconditionalUniqueConstraint` unchanged, so the three clauses INSIDE the
# coverage decision — the uniqueness filter, the unconditionality filter, and the
# exact single-field tuple match — were the least-probed part of the changed
# behaviour: a spec that pinned only "some constraint mentions the field" would have
# passed the whole battery. Each rival below INLINES a subtly wrong coverage decision
# into the guard (impl region only; the frozen pure-region helper is spec and is never
# touched), and each carries a witness at the input its clause gets wrong.
def _inline_guard(cover_expr):
    return (
        f"    if !fieldUnique && !({cover_expr}) then\n"
        "      if usesDefaultBackend then\n"
        '        errors := errors ++ ["auth.E003"]\n'
        "      else\n"
        '        errors := errors ++ ["auth.W004"]'
    )


# weak-cover-ignores-conditional: drops the unconditionality filter, so a CONDITIONAL
# (partial) uniqueness constraint wrongly counts as covering.
_WEAK_COVER_COND = _inline_guard(
    "constraints.any (fun c => c.isUnique && c.fields == [usernameField])")

# weak-cover-contains-not-exact: matches a constraint that merely INCLUDES the login
# field among its fields, instead of ranging over exactly that one field.
_WEAK_COVER_CONTAINS = _inline_guard(
    "constraints.any (fun c => c.isUnique && !c.isConditional "
    "&& c.fields.contains usernameField)")

# weak-cover-ignores-unique: drops the uniqueness filter, so a NON-uniqueness
# constraint over exactly the login field wrongly counts as covering.
_WEAK_COVER_NONUNIQUE = _inline_guard(
    "constraints.any (fun c => !c.isConditional && c.fields == [usernameField])")

# weak-cover-any-constraint: ignores WHICH field the constraint ranges over — any
# unconditional uniqueness constraint anywhere on the model wrongly suppresses.
_WEAK_COVER_ANY = _inline_guard(
    "constraints.any (fun c => c.isUnique && !c.isConditional)")


# weak-reorder-accumulation: emits the login arm FIRST, before the required-fields
# arms. Every rival above attacks whether a contribution is PRESENT; this one attacks
# the ORDER the postcondition pins, which nothing else probed.
_WEAK_REORDER_BASE = _swap(_BASE, _GUARD + "\n", "")
_IMPL_HEAD = "    let mut errors : List String := []\n"


def _wit(uf, r0, r1, fu, udb, an, au, cons):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    input, closed by `decide`. Elaborates against a rival that diverges from the
    frozen result there, and fails on gold (which satisfies the spec everywhere)."""
    args = f'"{uf}" {r0} {r1} {fu} {udb} {an} {au} {cons}'
    return (
        f"example : ¬ problem_spec_checkUserModel {args}\n"
        f"    (implementation_checkUserModel {args}) := by\n"
        f"  unfold problem_spec_checkUserModel implementation_checkUserModel\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "pos-nested-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GUARD, _POS_NESTED),
        "rationale": (
            "structurally-different but CORRECT impl: the login arm's conjunctive "
            "guard is re-expressed as two nested `if`s (direct uniqueness, then the "
            "declared constraints), producing the identical result on every input. "
            "The frozen `theorem correct_checkUserModel` statement is kept byte-"
            "identical and its case-split proof still closes over the nested "
            "branches. If it FAILS => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected)."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "landed by audit; the lane had been dropped for the wrong reason (\"the "
            "frozen obligation has no precondition\"). The obligation IS an "
            "unconditional universal, so no hypothesis can be over-strong — but the "
            "analogue on a total carrier is the postcondition being UNSATISFIABLE at "
            "an F2P-shaped input, and this case tests that directly. Four `have`s "
            "discharge the frozen postcondition BY EVALUATION (`decide` on a closed "
            "Prop) at the input the change is about — login field not directly "
            "unique, one unconditional uniqueness constraint over exactly that field, "
            "result the EMPTY diagnostic list — under both backend settings, plus the "
            "two near-miss inputs where a CONDITIONAL constraint over the same field "
            "leaves the error/warning code due. Only then is the frozen obligation "
            "closed with its gold tactic body verbatim (asserted above), so the case "
            "reproves rather than replaces. If it FAILS => PRECOND-TOO-STRONG: the "
            "spec would be pinning the result to something unreachable at exactly the "
            "input the change exists to handle."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-change behaviour: the login-field diagnostic is "
            "suppressed only by the field's own direct-uniqueness flag, with NO "
            "consultation of the declared unconditional single-field uniqueness "
            "constraints. Its faithful real counterpart is the unchanged repo, which "
            "still emits the error for a model whose login field is covered ONLY by "
            "such a constraint — exactly the FAIL_TO_PASS "
            "test_username_unique_with_model_constraint, which now asserts an empty "
            "diagnostic list. It does NOT resolve, so a verifying rival here would be "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition: on the discriminating sub-domain where "
            "the field is not directly unique yet a covering unconditional single-"
            "field constraint exists, the spec pins the login contribution to the "
            "EMPTY list, but the rival emits a code. Attacks the "
            "coveredByUnconditionalUniqueConstraint conjunct — the precise behaviour "
            "the change introduces. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # field not directly unique, but a covering unconditional constraint exists:
        # gold suppresses (login arm = []), rival emits ["auth.E003"].
        "witness": _wit("u", "false", "false", "false", "true", "false", "false",
                        '[⟨true, false, ["u"]⟩]'),
    },
    {
        "id": "weak-swap-regime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_SWAP),
        "refinement": (
            "a real patch that swapped the two severity branches (appending the "
            "warning code under the default backend and the error code otherwise) is "
            "correct on every input where no diagnostic is due but emits the WRONG "
            "code on every login-non-unique input. It fails the PASS_TO_PASS "
            "test_username_non_unique (asserts the error id under the default "
            "backend) and the warning arm of test_username_partially_unique. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's severity selection: on a login-non-"
            "unique input the spec pins the code to the error under the default "
            "backend and the warning otherwise; the rival returns the inverse. "
            "Attacks the usesDefaultBackend arm of the login contribution. If it "
            "VERIFIES => SPEC-TOO-WEAK on the severity sub-domain."
        ),
        # login-non-unique, custom backend: gold => ["auth.W004"], rival => ["auth.E003"].
        "witness": _wit("name", "true", "false", "false", "false", "true", "false",
                        "[]"),
    },
    {
        "id": "weak-always-error",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_ALWAYS_ERR),
        "refinement": (
            "always emitting the login diagnostic (dropping the suppression "
            "condition) is what a real patch that kept the append OUTSIDE its guard "
            "would do. It reports the code even for a genuinely-unique login field, "
            "failing every test that asserts an empty diagnostic list "
            "(test_username_unique_with_model_constraint). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: on a suppress input (field directly "
            "unique) the spec pins the login contribution to the EMPTY list, but the "
            "rival appends a code. Attacks the fieldUnique suppression arm from the "
            "over-emit side. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # field directly unique (suppress) + an authenticated-method code present:
        # gold => ["auth.C010"], rival => ["auth.E003","auth.C010"].
        "witness": _wit("x", "false", "false", "true", "true", "false", "true", "[]"),
    },
    {
        "id": "weak-always-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_ALWAYS_SUP),
        "refinement": (
            "always suppressing (removing the login arm) is what a real patch that "
            "deleted the append entirely would do — it never reports a non-unique "
            "login field. It fails the PASS_TO_PASS test_username_non_unique and "
            "test_username_partially_unique, both of which assert a diagnostic IS "
            "produced. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: on a login-non-unique input the spec "
            "requires the regime-selected code, but the rival returns the empty "
            "list. Attacks the fieldUnique suppression arm from the under-emit side. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # login-non-unique, no covering constraint, default backend:
        # gold => ["auth.E003"], rival => [].
        "witness": _wit("y", "false", "false", "false", "true", "false", "false",
                        '[⟨false, false, ["y"]⟩]'),
    },
    {
        "id": "weak-drop-reqfields-shape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _E001, _DROP),
        "refinement": (
            "dropping the required-fields-shape contribution is what a real patch "
            "that removed that unchanged sub-check would do; the shape diagnostic "
            "would no longer fire for a malformed required-fields declaration, "
            "diverging from the accumulated diagnostic list every caller observes. "
            "Does NOT resolve (this contribution is unchanged by the fix and must be "
            "preserved)."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins the FIRST arm of the ordered "
            "result to the required-fields-shape code. Attacks the reqFieldsBadShape "
            "arm — an independent contribution this carrier models explicitly (the "
            "nagini int-code carrier could not). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # only the shape flag set: gold => ["auth.E001"], rival => [].
        "witness": _wit("u", "true", "false", "true", "false", "false", "false", "[]"),
    },
    {
        "id": "weak-drop-reqfields-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _E002, _DROP),
        "refinement": (
            "dropping the required-fields-membership contribution removes an "
            "unchanged sub-check, so the membership diagnostic would no longer fire "
            "when the login field appears in the required-fields list, diverging from "
            "the observed diagnostic list. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins the SECOND arm to the "
            "membership code. Attacks the usernameInRequired arm — an independent "
            "modeled contribution. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # only the membership flag set: gold => ["auth.E002"], rival => [].
        "witness": _wit("u", "false", "true", "true", "false", "false", "false", "[]"),
    },
    {
        "id": "weak-drop-anonymous-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C009, _DROP),
        "refinement": (
            "dropping the anonymous-attribute contribution removes an unchanged "
            "sub-check, so its diagnostic would no longer fire, diverging from the "
            "observed diagnostic list. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins the fourth arm to the "
            "anonymous-attribute code. Attacks the isAnonymousMethod arm — an "
            "independent modeled contribution. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # only the anonymous-method flag set: gold => ["auth.C009"], rival => [].
        "witness": _wit("u", "false", "false", "true", "false", "true", "false", "[]"),
    },
    {
        "id": "weak-drop-authenticated-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C010, _DROP),
        "refinement": (
            "dropping the authenticated-attribute contribution removes an unchanged "
            "sub-check, so its diagnostic would no longer fire, diverging from the "
            "observed diagnostic list. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins the FINAL arm to the "
            "authenticated-attribute code. Attacks the isAuthenticatedMethod arm — an "
            "independent modeled contribution. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # only the authenticated-method flag set: gold => ["auth.C010"], rival => [].
        "witness": _wit("u", "false", "false", "true", "false", "false", "true", "[]"),
    },
    # --- coverage-clause rivals (landed by audit): the three clauses INSIDE the
    # coverage decision, which every rival above left unprobed by reusing the frozen
    # helper verbatim. -----------------------------------------------------------
    {
        "id": "weak-cover-ignores-conditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_COVER_COND),
        "refinement": (
            "a real patch that collected every uniqueness constraint over the login "
            "field, without restricting to the UNCONDITIONAL ones, would behave "
            "exactly this way: a constraint that only applies to a subset of rows "
            "cannot guarantee the field is unique, but this rival treats it as if it "
            "did and stays silent. It fails the PASS_TO_PASS "
            "test_username_partially_unique, which declares a conditional uniqueness "
            "constraint over the login field and asserts the diagnostic IS produced "
            "(error under the default backend, warning otherwise). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's coverage clause, which counts a "
            "constraint only when it is BOTH a uniqueness constraint AND "
            "unconditional. Attacks the unconditionality filter — a clause every "
            "other rival inherits unchanged from the frozen helper, so without this "
            "case a spec that ignored conditionality would pass the whole battery. "
            "If it VERIFIES => SPEC-TOO-WEAK on the conditional sub-domain."
        ),
        # not directly unique + a CONDITIONAL unique constraint over exactly the login
        # field: gold => ["auth.E003"] (it does not cover), rival => [] (suppresses).
        "witness": _wit("u", "false", "false", "false", "true", "false", "false",
                        '[⟨true, true, ["u"]⟩]'),
    },
    {
        "id": "weak-cover-contains-not-exact",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_COVER_CONTAINS),
        "refinement": (
            "a real patch that tested whether the login field appears AMONG a "
            "constraint's fields, rather than whether the constraint ranges over "
            "exactly that one field, would behave this way. A composite uniqueness "
            "constraint over several fields only makes the TUPLE unique, so the login "
            "field alone can still repeat; this rival suppresses the diagnostic "
            "anyway. Does NOT resolve — it reports no problem for a model whose login "
            "field is not uniquely constrained at all."
        ),
        "rationale": (
            "REJECTED by the postcondition's coverage clause, which requires the "
            "constraint's field list to equal the singleton list of the login field. "
            "Attacks the exact-tuple match — the second unprobed clause inside the "
            "coverage decision. If it VERIFIES => SPEC-TOO-WEAK on the multi-field "
            "sub-domain."
        ),
        # unconditional unique constraint over TWO fields including the login field:
        # gold => ["auth.E003"], rival => [].
        "witness": _wit("u", "false", "false", "false", "true", "false", "false",
                        '[⟨true, false, ["u", "v"]⟩]'),
    },
    {
        "id": "weak-cover-ignores-unique",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_COVER_NONUNIQUE),
        "refinement": (
            "a real patch that scanned every declared constraint instead of filtering "
            "to the uniqueness ones would behave this way: an ordinary "
            "non-uniqueness constraint naming the login field would be mistaken for a "
            "uniqueness guarantee and the diagnostic suppressed. Does NOT resolve — "
            "the field is not unique and no test-visible guarantee makes it so."
        ),
        "rationale": (
            "REJECTED by the postcondition's coverage clause, which counts only "
            "uniqueness constraints. Attacks the uniqueness filter — the third "
            "unprobed clause inside the coverage decision. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # unconditional NON-uniqueness constraint over exactly the login field:
        # gold => ["auth.E003"], rival => [].
        "witness": _wit("u", "false", "false", "false", "true", "false", "false",
                        '[⟨false, false, ["u"]⟩]'),
    },
    {
        "id": "weak-cover-any-constraint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _WEAK_COVER_ANY),
        "refinement": (
            "a real patch that checked merely whether the model declares ANY "
            "unconditional uniqueness constraint — without checking which field it "
            "ranges over — would behave this way. A uniqueness constraint on some "
            "unrelated field says nothing about the login field, yet this rival stays "
            "silent. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's coverage clause, which pins the "
            "constraint's field list to the login field specifically rather than "
            "accepting any constraint. Attacks the field-identity half of the exact "
            "match, from the widest side. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # unconditional unique constraint over a DIFFERENT field:
        # gold => ["auth.E003"], rival => [].
        "witness": _wit("u", "false", "false", "false", "true", "false", "false",
                        '[⟨true, false, ["other"]⟩]'),
    },
    {
        "id": "weak-reorder-accumulation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_WEAK_REORDER_BASE, _IMPL_HEAD, _IMPL_HEAD + _GUARD + "\n"),
        "refinement": (
            "a real patch that moved the login-field arm to the top of the function "
            "would emit exactly the same SET of diagnostics in a different ORDER. "
            "Callers observe the accumulated list, and the checks framework reports "
            "diagnostics in the order the check returns them, so the reordered list "
            "is a different observable result. Does NOT resolve — it changes what the "
            "tests that compare the returned list against an expected list observe."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins the result to the ordered "
            "CONCATENATION of the five contributions, not to their multiset. Attacks "
            "ordering — a property every other rival leaves untouched, since they all "
            "attack whether a contribution is present rather than where it sits. If "
            "it VERIFIES => SPEC-TOO-WEAK on ordering."
        ),
        # required-fields-shape AND the login arm both fire, so order is observable:
        # gold => ["auth.E001","auth.E003"], rival => ["auth.E003","auth.E001"].
        "witness": _wit("u", "true", "false", "false", "true", "false", "false", "[]"),
    },
]


# No @ContractOnly axioms and no opaque callees: the constraint-coverage decision is
# modeled DEEPLY over the transparent ConstraintInfo carrier, so the axiom lane is
# vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
