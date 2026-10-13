"""PBT manifest for django__django-13933 (lean backend) — an adversarial
falsification battery PORTED from the nagini sibling's design.

THE DEFENDED SURFACE (this carrier)
-----------------------------------
The nagini sibling models the *rendered text* of the invalid-choice message via
an interpolation fold (`render_invalid_choice` / `_render`). This lean bundle
narrows the carrier to the purely functional core one level up: the COERCION
OUTCOME of a submitted value against a stored collection, an
`Except ChoiceError (Option Resolved)` pinned by `problem_spec_coerceChoice`
over four inputs — `invalidMessage`, `emptyValues`, `value`, `lookup`. The
postcondition has three independent top-level clauses:

  * `value ∈ emptyValues → result = Except.ok none` (sentinel branch);
  * `value ∉ emptyValues → ∀ r, lookup = some r → result = Except.ok (some r)`
    (resolved branch);
  * `value ∉ emptyValues → lookup = none → result = Except.error {template,
    code, params := [(valueParamName, value)]}` (rejection branch — the load-
    bearing clause the fix adds: the report must carry the offending value under
    the value-placeholder name).

CARRIER NARROWING vs NAGINI
---------------------------
The nagini battery's cases attack the interpolation fold: FRAME-MUTATION of the
read-only `template`/`value` lists, PARTIAL-DOMAIN verbatim-copy (placeholder not
recognised), and value-truncation (dropping value[0] in the prepend loop). None
of those mechanics exist on this carrier:

  * FRAME-MUTATION (nagini's mandatory class) has no falsifying rival here, but
    NOT because the rival is inexpressible — that reason was measured wrong.
    A shadow-and-mutate rival IS expressible on this carrier (`let mut ev :=
    emptyValues; ev := ev ++ [value]` before gold's returns) and it BUILDS
    (verifies, exit 0). It verifies because the mutation is unobservable: the
    inputs are immutable values, so a local rebinding cannot be read back by the
    result, and there is no permission system for the write to violate. So the
    class is vacuous for a stronger reason than "cannot be written" — every
    expressible member of it is BEHAVIOURALLY IDENTICAL to gold, hence a correct
    impl, hence one the spec must (and does) accept. Shipping it as
    `expect="reject"` would be a false case; shipping it as `expect="verify"`
    would duplicate the positives. No substitute is fabricated.
  * The verbatim-copy PARTIAL-DOMAIN rival maps to the PREPATCH bug on this
    carrier: dropping the parameter binding on the rejection branch
    (`params := []`). Ported as `reject-prepatch-no-binding`.
  * The value-truncation rival (interpolate value[1:]) maps to binding a
    truncated value into the report (`value.drop 1`). Ported as
    `reject-truncated-value`.
  * The positive controls (structurally-different-but-correct impls that MUST
    verify) port directly, with proofs that close for the new impl shape.

  * ADMISSIBILITY ports directly and is CARRIED (`admiss-f2p-shaped-input`).
    The frozen obligation has no precondition, so the analogue on this total
    carrier is the obligation being SATISFIABLE at exactly an F2P-shaped
    concrete input: a rejected textual submission against a nonempty sentinel
    list with a template that names the value-placeholder. The case discharges
    the spec predicate at that input by evaluation, as a `have`, before closing
    the frozen obligation verbatim. Measured load-bearing: the same `have`,
    stated standalone, builds against the frozen impl (exit 0) and FAILS against
    three of this battery's rivals (exit 1), so it is not a tautology.

The rejection branch is transparent (concrete `String`/`Nat`/`List`), so every
reject rival is refutable by stating the spec predicate at a concrete input and
`decide`-ing — no opaque callee blocks the lane. Both positives keep the frozen
`theorem correct_coerceChoice` STATEMENT byte-identical and reprove for the new
impl body.

WITNESS DISCRIMINATION (measured, not argued)
--------------------------------------------
Every reject case's witness was rebuilt on both sides and, additionally, subject
to a FLIPPED-CLAIM forgery: the same concrete input with the `¬` dropped, i.e.
asserting the spec HOLDS there. For all reject cases the forgery builds against
the frozen impl (exit 0) and FAILS against the rival (exit 1) — the exact
mirror of the witness's own (rival 0 / frozen 1). So the frozen-side exit code
TRACKS the claim rather than being a constant tactic failure, which is what makes
each rejection attributable to the spec.

SPEC STRENGTH IS EXHAUSTIVE, NOT SAMPLED
----------------------------------------
`problem_spec_coerceChoice` pins `result` UNIQUELY at every input: its three
clauses are jointly total and each fixes the result outright, so the spec is
functional. Machine-checked as a standalone lemma against the frozen spec:

    ∀ im ev v l r1 r2, problem_spec_coerceChoice im ev v l r1 →
        problem_spec_coerceChoice im ev v l r2 → r1 = r2      -- builds, exit 0

Consequence: no impl that differs observably from the frozen one at ANY input can
satisfy this spec (SPEC-TOO-WEAK is unreachable), and every impl agreeing with it
everywhere does (SPEC-TOO-STRONG can only ever be a proof-shape artifact, never a
spec defect). The reject rivals below therefore probe COMPONENT COVERAGE — that
each named component of each clause is separately load-bearing — rather than
searching for a hole the determinism lemma has already excluded.

AXIOM LANE: empty (this bundle consumes no axiom; G-AX's job, not this gate's).
"""
from pathlib import Path

INSTANCE = "django__django-13933"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies ENTIRELY inside the impl or proof region and is unique in
# the frozen file (the spec region repeats `params := [(valueParamName, value)]`,
# so we anchor on the wider error block that only occurs in the impl).
# ---------------------------------------------------------------------------
_ERR_BLOCK = (
    "      return Except.error\n"
    "        { messageTemplate := invalidMessage,\n"
    "          code := invalidChoiceCode,\n"
    "          params := [(valueParamName, value)] }"
)

_SENTINEL_GUARD = (
    "  if value ∈ emptyValues then\n"
    "    return Except.ok none\n"
)

_SOME_BRANCH = "  | some r => return Except.ok (some r)"

# The frozen proof script, verbatim — anchor for prefixing an admissibility
# `have` while leaving the obligation's own closing script untouched.
_PROOF_HEAD = "  intro invalidMessage emptyValues value lookup\n"

_IMPL_BODY = (
    "  if value ∈ emptyValues then\n"
    "    return Except.ok none\n"
    "  match lookup with\n"
    "  | some r => return Except.ok (some r)\n"
    "  | none =>\n"
    "      return Except.error\n"
    "        { messageTemplate := invalidMessage,\n"
    "          code := invalidChoiceCode,\n"
    "          params := [(valueParamName, value)] }"
)

_PROOF_BODY = (
    "  intro invalidMessage emptyValues value lookup\n"
    "  unfold problem_spec_coerceChoice implementation_coerceChoice\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro hv; simp only [hv, if_true, Id.run]; rfl\n"
    "  · intro hv r hr; simp only [hv, if_false, Id.run, hr]; rfl\n"
    "  · intro hv hr; simp only [hv, if_false, Id.run, hr]; rfl"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = []

# --- POSITIVE CONTROL 1: let-bind the rejection report ----------------------
# Structurally different (the error record is bound to a local before being
# returned), behaviourally identical. The frozen proof still closes because the
# reduced impl is definitionally the same. A correct impl of this shape MUST
# verify; else SPEC-TOO-STRONG.
SPEC_TESTS.append({
    "id": "pos-let-bind-report",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _ERR_BLOCK,
        "      let err : ChoiceError :=\n"
        "        { messageTemplate := invalidMessage,\n"
        "          code := invalidChoiceCode,\n"
        "          params := [(valueParamName, value)] }\n"
        "      return Except.error err",
    ),
    "rationale": "A correct impl that only reshapes the rejection branch into a "
                 "let-bound local must verify against all three clauses; else the "
                 "spec over-constrains the executable shape. The frozen "
                 "theorem statement and proof body are untouched.",
})

# --- POSITIVE CONTROL 2: explicit if/else with nested match -----------------
# Reshape the sentinel test into an explicit `if … then … else`, moving the
# match into the else-branch. Same behaviour on every input; the proof body is
# adjusted (`if_neg hv` on the non-sentinel clauses) while keeping the
# `theorem correct_coerceChoice` STATEMENT byte-identical.
SPEC_TESTS.append({
    "id": "pos-if-else-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _swap(
            _BASE, _IMPL_BODY,
            "  if value ∈ emptyValues then\n"
            "    return Except.ok none\n"
            "  else\n"
            "    match lookup with\n"
            "    | some r => return Except.ok (some r)\n"
            "    | none =>\n"
            "        return Except.error\n"
            "          { messageTemplate := invalidMessage,\n"
            "            code := invalidChoiceCode,\n"
            "            params := [(valueParamName, value)] }",
        ),
        _PROOF_BODY,
        "  intro invalidMessage emptyValues value lookup\n"
        "  unfold problem_spec_coerceChoice implementation_coerceChoice\n"
        "  refine ⟨?_, ?_, ?_⟩\n"
        "  · intro hv; simp only [hv, if_true, Id.run]; rfl\n"
        "  · intro hv r hr; simp only [Id.run, if_neg hv, hr]; rfl\n"
        "  · intro hv hr; simp only [Id.run, if_neg hv, hr]; rfl",
    ),
    "rationale": "A structurally-different but correct impl (sentinel test as an "
                 "explicit if/else, match nested in the else) must verify; else "
                 "SPEC-TOO-STRONG. Only the impl body and the tactic script "
                 "change — the obligation statement is identical.",
})

# --- REJECT 1: prepatch — rejection report drops the value binding ----------
# The rejection branch returns `params := []` instead of the singleton binding.
# This is exactly the PREPATCH behaviour and the modeled bug.
SPEC_TESTS.append({
    "id": "reject-prepatch-no-binding",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _ERR_BLOCK,
        "      return Except.error\n"
        "        { messageTemplate := invalidMessage,\n"
        "          code := invalidChoiceCode,\n"
        "          params := [] }",
    ),
    "refinement": "A faithful real patch that raises the rejection with no "
                  "parameter bindings is the prepatch: a message template naming "
                  "the value-placeholder cannot render the offending submission, "
                  "so the F2P expectation ('\"invalid\" is not one of the "
                  "available choices.') is not produced => would NOT resolve.",
    "rationale": "Refuted by the rejection clause: with an empty binding list the "
                 "result differs from the required "
                 "`params := [(valueParamName, value)]` on every rejected, "
                 "non-sentinel submission.",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [] \"invalid\" none\n"
        "    (implementation_coerceChoice \"msg\" [] \"invalid\" none) := by\n"
        "  intro h; have h3 := h.2.2 (by decide) rfl\n"
        "  simp [implementation_coerceChoice] at h3\n"
    ),
})

# --- REJECT 2: rejection report carries a TRUNCATED value -------------------
# The binding uses `value.drop 1` — the offending value with its first code
# point removed. Correct only on the empty-value sub-domain; wrong on every
# nonempty submission.
SPEC_TESTS.append({
    "id": "reject-truncated-value",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _ERR_BLOCK,
        "      return Except.error\n"
        "        { messageTemplate := invalidMessage,\n"
        "          code := invalidChoiceCode,\n"
        "          params := [(valueParamName, value.drop 1)] }",
    ),
    "refinement": "A faithful real patch that binds a truncated submission "
                  "renders the F2P value 'invalid' as 'nvalid', so '\"nvalid\" is "
                  "not one of the available choices.' != the expected message => "
                  "would NOT resolve. Correct only when the value is empty.",
    "rationale": "Refuted by the rejection clause: the report must bind the WHOLE "
                 "submitted `value`; dropping its first character breaks the "
                 "required binding on any nonempty value (witness value "
                 "'invalid').",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [] \"invalid\" none\n"
        "    (implementation_coerceChoice \"msg\" [] \"invalid\" none) := by\n"
        "  intro h; have h3 := h.2.2 (by decide) rfl\n"
        "  simp [implementation_coerceChoice] at h3\n"
        "  exact absurd h3 (by decide)\n"
    ),
})

# --- REJECT 3: rejection report binds under the WRONG placeholder name ------
# The binding uses the literal "pk" instead of the value-placeholder name. A
# message naming the value-placeholder finds no binding for it and cannot render
# the submission. Attacks the `valueParamName` component of the rejection clause.
SPEC_TESTS.append({
    "id": "reject-wrong-param-name",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _ERR_BLOCK,
        "      return Except.error\n"
        "        { messageTemplate := invalidMessage,\n"
        "          code := invalidChoiceCode,\n"
        "          params := [(\"pk\", value)] }",
    ),
    "refinement": "A faithful real patch binding the value under a different "
                  "placeholder name leaves the value-placeholder unbound, so the "
                  "F2P template (which names the value-placeholder) renders "
                  "without the submission => would NOT resolve.",
    "rationale": "Refuted by the rejection clause: the binding key must be "
                 "`valueParamName`; binding under 'pk' differs from the required "
                 "`[(valueParamName, value)]`.",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [] \"v\" none\n"
        "    (implementation_coerceChoice \"msg\" [] \"v\" none) := by\n"
        "  intro h; have h3 := h.2.2 (by decide) rfl\n"
        "  simp [implementation_coerceChoice] at h3\n"
        "  exact absurd h3 (by decide)\n"
    ),
})

# --- REJECT 4: rejection report uses a CONSTANT template ---------------------
# The report's messageTemplate is replaced by the fixed rejection code instead
# of the configured `invalidMessage`. Attacks the messageTemplate component and
# varies the `invalidMessage` binder (witness uses "tmpl", distinct from "msg").
SPEC_TESTS.append({
    "id": "reject-constant-template",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _ERR_BLOCK,
        "      return Except.error\n"
        "        { messageTemplate := invalidChoiceCode,\n"
        "          code := invalidChoiceCode,\n"
        "          params := [(valueParamName, value)] }",
    ),
    "refinement": "A faithful real patch that reports a fixed template rather "
                  "than the caller-configured one ignores the custom message "
                  "entirely, so the F2P (which configures a custom template) "
                  "cannot render it => would NOT resolve.",
    "rationale": "Refuted by the rejection clause: the report's template must be "
                 "the configured `invalidMessage`; substituting the constant code "
                 "differs whenever `invalidMessage` is not that constant (witness "
                 "invalidMessage 'tmpl'). Varies the invalidMessage binder.",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"tmpl\" [] \"v\" none\n"
        "    (implementation_coerceChoice \"tmpl\" [] \"v\" none) := by\n"
        "  intro h; have h3 := h.2.2 (by decide) rfl\n"
        "  simp [implementation_coerceChoice, invalidChoiceCode] at h3\n"
    ),
})

# --- REJECT 5: sentinel branch dropped --------------------------------------
# The sentinel guard is removed, so a recognised "no answer" sentinel that would
# otherwise yield the empty result instead falls through and is rejected.
# Attacks the FIRST clause and varies the `emptyValues`/`value` binders (witness
# uses a nonempty emptyValues with the value a member of it).
SPEC_TESTS.append({
    "id": "reject-drop-sentinel-branch",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SENTINEL_GUARD, ""),
    "refinement": "A faithful real patch that stops treating the recognised "
                  "sentinels as 'no answer' would reject a blank/None submission "
                  "instead of returning the empty result, changing the field's "
                  "accepted-input behavior => would NOT resolve (and regresses "
                  "the sentinel handling the F2P suite depends on).",
    "rationale": "Refuted by the sentinel clause (clause 1): for a submission "
                 "among `emptyValues` the result must be `Except.ok none`; "
                 "without the guard it becomes an error. Varies emptyValues "
                 "(nonempty) and value (a member).",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [\"x\"] \"x\" none\n"
        "    (implementation_coerceChoice \"msg\" [\"x\"] \"x\" none) := by\n"
        "  intro h; have h1 := h.1 (by decide)\n"
        "  simp [implementation_coerceChoice] at h1\n"
    ),
})

# --- REJECT 6: resolved branch drops the answer -----------------------------
# The success branch yields the empty result instead of the resolved answer.
# Attacks the SECOND clause and varies the `lookup` binder (witness uses
# `some 5`, the only rival probing a successful resolution).
SPEC_TESTS.append({
    "id": "reject-resolved-drops-answer",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SOME_BRANCH, "  | some r => return Except.ok none"),
    "refinement": "A faithful real patch that discards the resolved answer and "
                  "returns the empty result for a valid submission would stop the "
                  "field from accepting any legitimate choice => would NOT resolve "
                  "(and breaks the base acceptance behavior).",
    "rationale": "Refuted by the resolved clause (clause 2): when the submission "
                 "resolves to `some r` the result must be `Except.ok (some r)`; "
                 "returning `Except.ok none` differs. Varies the lookup binder "
                 "(some).",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [] \"v\" (some 5)\n"
        "    (implementation_coerceChoice \"msg\" [] \"v\" (some 5)) := by\n"
        "  intro h; have h2 := h.2.1 (by decide) 5 rfl\n"
        "  simp [implementation_coerceChoice] at h2\n"
    ),
})

# --- REJECT 7: the resolved answer is perturbed ONLY when the sentinel list is
# nonempty. Every other rival that probes the resolved clause does so at
# `emptyValues = []`, so this rival AGREES with the frozen impl on the whole
# slice the rest of the battery observes and diverges only off it. Varies the
# emptyValues and lookup binders JOINTLY (nonempty sentinels × a successful
# resolution), a point no other case reaches.
SPEC_TESTS.append({
    "id": "reject-resolved-perturbed-off-slice",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _SOME_BRANCH,
        "  | some r => if emptyValues.isEmpty then return Except.ok (some r)\n"
        "              else return Except.ok (some (r + 1))",
    ),
    "refinement": "A faithful real patch that returns a neighbouring stored "
                  "answer instead of the resolved one whenever the field "
                  "recognises any 'no answer' sentinel would accept a valid "
                  "submission and hand back the WRONG record — silent data "
                  "corruption on the accepting path => would NOT resolve.",
    "rationale": "Refuted by the resolved clause (clause 2): the result must be "
                 "`Except.ok (some r)` for the SAME `r` the submission resolved "
                 "to. Off-slice rival: it is definitionally gold whenever "
                 "`emptyValues` is empty, so the witness must move the "
                 "emptyValues binder off `[]` (uses `[\"z\"]` with `some 5`) — "
                 "the only case in this battery whose refutation point needs two "
                 "binders varied at once.",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [\"z\"] \"v\" (some 5)\n"
        "    (implementation_coerceChoice \"msg\" [\"z\"] \"v\" (some 5)) := by\n"
        "  intro h; have h2 := h.2.1 (by decide) 5 rfl\n"
        "  simp [implementation_coerceChoice] at h2\n"
    ),
})

# --- REJECT 8: the rejection code is wrong -----------------------------------
# `code` is set to the value-placeholder name instead of the constant rejection
# code. The ONLY case attacking the `code` component of the rejection clause —
# every other rival leaves it at `invalidChoiceCode`, so without this case that
# component of the report is unprobed.
SPEC_TESTS.append({
    "id": "reject-wrong-error-code",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _ERR_BLOCK,
        "      return Except.error\n"
        "        { messageTemplate := invalidMessage,\n"
        "          code := valueParamName,\n"
        "          params := [(valueParamName, value)] }",
    ),
    "refinement": "A faithful real patch that stamps a different machine-readable "
                  "code on the rejection breaks every caller that dispatches on "
                  "it — including the per-code message-template override the F2P "
                  "expectation configures, which is keyed by that code, so the "
                  "custom template is never selected => would NOT resolve.",
    "rationale": "Refuted by the rejection clause: the report's `code` must be "
                 "`invalidChoiceCode`. Substituting the placeholder name differs "
                 "from the required record, and this is the only case that varies "
                 "the code component at all.",
    "witness": (
        "example : ¬ problem_spec_coerceChoice \"msg\" [] \"v\" none\n"
        "    (implementation_coerceChoice \"msg\" [] \"v\" none) := by\n"
        "  intro h; have h3 := h.2.2 (by decide) rfl\n"
        "  simp [implementation_coerceChoice, invalidChoiceCode,\n"
        "        valueParamName] at h3\n"
    ),
})

# --- ADMISSIBILITY: the obligation is satisfiable at an F2P-shaped input -----
# The frozen obligation carries no precondition, so PRECOND-TOO-STRONG shows up
# on this total carrier as the obligation being UNSATISFIABLE at exactly the
# input shape the F2P expectation exercises: a textual submission that resolves
# to nothing, against a field that DOES recognise sentinels (nonempty
# emptyValues), with a template naming the value-placeholder. The case discharges
# the spec predicate at that concrete input by evaluation, as a `have`, and only
# then closes the frozen obligation verbatim. If the spec were unsatisfiable
# there, the `have` fails and the case is rejected => PRECOND-TOO-STRONG.
#
# Load-bearing, not a tautology: this same `have`, stated standalone, builds
# against the frozen impl and FAILS against three of the rivals above.
SPEC_TESTS.append({
    "id": "admiss-f2p-shaped-input",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _PROOF_HEAD,
        "  have _admissible :\n"
        "      problem_spec_coerceChoice \"bad: %(value)s\" [\"\", \"none\"]\n"
        "        \"invalid\" none\n"
        "        (implementation_coerceChoice \"bad: %(value)s\" [\"\", \"none\"]\n"
        "          \"invalid\" none) := by\n"
        "    refine ⟨?_, ?_, ?_⟩\n"
        "    · intro hv; exact absurd hv (by decide)\n"
        "    · intro hv r hr; exact absurd hr (by simp)\n"
        "    · intro _ _; rfl\n"
        + _PROOF_HEAD,
    ),
    "rationale": "The obligation must be SATISFIABLE at an F2P-shaped concrete "
                 "input — a submission that is not among the recognised "
                 "sentinels and resolves to nothing, with a nonempty sentinel "
                 "list and a template naming the value-placeholder. Discharged "
                 "by evaluation as a `have` before the frozen obligation is "
                 "closed verbatim; if the spec admitted no such input the case "
                 "would be rejected => PRECOND-TOO-STRONG. This is the lane that "
                 "detects an over-strong obligation, and on a total carrier "
                 "satisfiability-at-the-F2P-input is its analogue.",
})


# ===========================================================================
# AXIOM LANE — empty: this bundle consumes no axiom (G-AX's lane, not this gate's).
# ===========================================================================
AXIOM_TESTS = []
