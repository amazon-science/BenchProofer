# properties.py — G-PBT falsification battery for django__django-13212 (lean lane).
#
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Every SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl region
# — and, for a positive that reproves, the proof body — is edited), checked by
# variant_scope + the Lean verifier. Every expect="reject" case carries a refutation
# `witness`: a snippet that ELABORATES against the rival and FAILS on the frozen
# solution, so the rejection is attributable to the postcondition and not to a tactic
# script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#
#   checkOutcome (value : String) (accepted : Bool)
#                (baseParams : List (String × String))
#     : Option (List (String × String))
#
#   One obligation, `theorem correct_checkOutcome`, under the single precondition
#   `baseParams.lookup valueKey = none` (no check already supplies the substitution
#   name the contract is about). The postcondition has TWO independent top-level
#   clauses:
#
#     (C1) accepted = true  → result = none
#          An acceptable input produces NO error context at all.
#     (C2) accepted = false → result = some (baseParams ++ [(valueKey, value)])
#          A rejection's substitution-parameter SEQUENCE is pinned WHOLE: the
#          intrinsic parameters the check supplied come first, verbatim and in
#          position; the binding of `valueKey` to exactly the rejected input is
#          APPENDED as the final entry; nothing else appears anywhere.
#
#   C2 is a single equation but it constrains five separable things, and each is a
#   distinct attack surface: the PRESENCE of the value binding, its CONTENT, the
#   NAME it is bound under, the PRESERVATION of the intrinsic entries, and the
#   POSITION/CLOSURE of the sequence — where closure has two halves that need
#   separate rivals, a SPURIOUS foreign entry and a DUPLICATE/SHADOWED copy of the
#   contract's own binding. The rival set below attacks all five (closure in both
#   halves), plus C1.
#
#   The shadowing half is the one that shows the whole-sequence pin is load-bearing:
#   a duplicate `valueKey` entry satisfies every lookup-level fact the frozen
#   docstring lists as a corollary, so a lookup-view spec would admit it and only
#   the sequence equation rejects it. See weak-duplicate-shadowed-value-binding.
#
#   Nothing is opaque: `valueKey` is a literal `String` and the carrier is a
#   transparent `List (String × String)`, so `decide` computes the spec at any
#   literal input. No witness needs conditioning on the carrier, and there is no
#   ungrounded answer-key a wrong impl could echo — C2 equates the result to a term
#   built from the ARGUMENTS.
#
# CARRIER NOTE (how the nagini rivals become these rivals). The nagini sibling
# modeled three separate builders over `Dict[int, PSeq[int]]` keyed by two constant
# name tokens, behind fractional read permission, and pinned membership +
# per-key content + a "binds nothing else" closure. This bundle models the SAME
# behavior as one builder over an ORDERED association list, and pins the whole
# sequence rather than its lookup view. So:
#   * nagini's per-key content pin becomes the CONTENT component of C2;
#   * nagini's membership pin becomes the PRESENCE component of C2;
#   * nagini's "binds nothing else" closure becomes the CLOSURE component of C2 —
#     and the ordered carrier makes it STRICTLY stronger here: it additionally
#     rejects a reordering and a duplicate/shadowed entry, which the unordered dict
#     abstraction could not see. Three rivals below
#     (`weak-prepends-value-binding`, `weak-duplicate-shadowed-value-binding`,
#     `weak-binds-wrong-name`) exist only because of that strengthening and have no
#     nagini counterpart.
#   * nagini's three separate builders collapse into ONE modeled function whose
#     `baseParams` binder ranges over "no intrinsic parameters" (the bare-rejection
#     site) and "some intrinsic parameters" (a site that already supplies its own).
#     nagini's per-builder rivals therefore become sub-domain rivals over that
#     binder — hence the paired unguarded/guarded shapes below.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload for the full
# account):
#   * FRAME-MUTATION — nagini's MANDATORY class and 3 of its 13 cases (the rival
#     wrote into an input held at fractional read permission). Lean is
#     referentially transparent: there is no aliasing and no permission to be
#     insufficient, so a "store into a read-only input" rival is not expressible.
#     The class is VACUOUS here, not omitted. No substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling carries no such case, and on
#     this backend the class is genuinely vacuous anyway: `implementation_checkOutcome`
#     is a total Lean `def`, so a diverging implementation cannot be written at all.
#   * AXIOM_TESTS — the axiom lane is G-AX's job and this gate ignores it. This
#     bundle consumes no callee axiom regardless (the verdict and the intrinsic
#     parameters are carried as INPUTS; the changed construction is modeled deeply).
from pathlib import Path

INSTANCE = "django__django-13212"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it names and is unique in the
# file, so every variant edits ONLY the impl region (plus, for the admissibility
# positive, the proof BODY) and same_spec holds by construction.
# ---------------------------------------------------------------------------

# impl region: the acceptance branch (establishes C1).
_ACCEPT = (
    "  if accepted then\n"
    "    -- Input is acceptable: succeed, no error context.\n"
    "    return none\n"
)

# impl region: the rejection branch's returned sequence (establishes C2).
_REJECT = "  return some (baseParams ++ [(valueKey, value)])"

# impl region: the whole body (both branches), for shape-level reshapes.
_BODY = (
    _ACCEPT
    + "  -- Input is rejected: build the error context, binding `value` to the rejected\n"
    + "  -- input alongside the intrinsic parameters this check already supplies.\n"
    + _REJECT
)

# proof region: the first tactic line, used only to PREPEND to the frozen script.
_PROOF_HEAD = "  intro value accepted baseParams _hbase\n"

for _a in (_ACCEPT, _REJECT, _BODY, _PROOF_HEAD):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a!r}")


def _rej(new):
    """Replace ONLY the rejection branch's returned sequence."""
    return _swap(_BASE, _REJECT, new)


def _wit(value, accepted, base_params, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at one CONCRETE
    literal input, closed by `decide`.

    The carrier is fully transparent (a literal `String` key over an association
    list), so `decide` computes both sides — no conditioning on an opaque term is
    needed and there are no hypotheses that could be jointly unsatisfiable. Holds
    of a rival that diverges from the pinned outcome at this input; fails on the
    frozen solution, which satisfies the postcondition at EVERY input.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_checkOutcome {value} {accepted} {base_params}\n"
        f"    (implementation_checkOutcome {value} {accepted} {base_params}) := by\n"
        f"  unfold problem_spec_checkOutcome implementation_checkOutcome\n"
        f"  decide"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# Each is a structurally DIFFERENT but behaviourally IDENTICAL impl. The frozen
# `theorem correct_checkOutcome` STATEMENT is byte-identical in every one, and no
# new axiom / lemma / sorry / native_decide is introduced anywhere.
# ===========================================================================

# The rejection context is routed through an intermediate local before being
# returned. Identical sequence on every input; single return path per branch.
# Ports nagini's pos-invalid-local-reshape (the local-variable reshape).
_POS_LOCAL = _rej(
    "  let ctx := baseParams ++ [(valueKey, value)]\n"
    "  return some ctx"
)

# The two branches are COMMUTED: the guard is negated so the REJECTION arm is the
# early return and acceptance is the fall-through. Identical outcome on both
# verdicts. Ports nagini's pos-limit-reorder (a statement/branch reorder, not a
# fold-direction flip, so no new lemma is needed).
_POS_NEGATED = _swap(
    _BASE, _BODY,
    "  if !accepted then\n"
    "    -- Input is rejected: build the error context, binding the rejected input\n"
    "    -- alongside the intrinsic parameters this check already supplies.\n"
    "    return some (baseParams ++ [(valueKey, value)])\n"
    "  -- Input is acceptable: succeed, no error context.\n"
    "  return none",
)

# The verdict is dispatched by `match` on the Boolean rather than by `if`, with
# both arms returning directly. Identical outcome on both verdicts; a third
# independent shape defending the same obligation.
_POS_MATCH = _swap(
    _BASE, _BODY,
    "  match accepted with\n"
    "  | true =>\n"
    "    -- Input is acceptable: succeed, no error context.\n"
    "    return none\n"
    "  | false =>\n"
    "    -- Input is rejected: build the error context, binding the rejected input\n"
    "    -- alongside the intrinsic parameters this check already supplies.\n"
    "    return some (baseParams ++ [(valueKey, value)])",
)

# ADMISSIBILITY: the frozen obligation carries a real precondition hypothesis
# (`baseParams.lookup valueKey = none`). This variant leaves the gold impl intact
# and PREPENDS two `have`s to the tactic body: (a) the precondition genuinely holds
# of an F2P-shaped input that already supplies its own intrinsic parameter, so the
# hypothesis is not vacuously false and does not exclude the tested domain; (b) the
# postcondition is establishable at that same input by evaluation, so the
# obligation is non-vacuously satisfiable there. Then the frozen script closes the
# obligation verbatim. Ports nagini's admiss-invalid-input.
_ADMISS = _swap(
    _BASE, _PROOF_HEAD,
    '  have _precondition_admits :\n'
    '      ([("max", "2")] : List (String × String)).lookup valueKey = none := by decide\n'
    '  have _establishable : problem_spec_checkOutcome "123" false [("max", "2")]\n'
    '      (implementation_checkOutcome "123" false [("max", "2")]) := by\n'
    '    unfold problem_spec_checkOutcome implementation_checkOutcome\n'
    '    decide\n'
    + _PROOF_HEAD,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly, edits only the impl region, and carries a witness SEEN to elaborate
# against the rival and FAIL on the frozen solution.
# ===========================================================================

# (A) PRESENCE of the value binding — attacks C2. The pre-change behavior: a
# rejection publishes only the intrinsic parameters it already supplied.
_RIV_OMITS = _rej("  return some baseParams")

# (A') PRESENCE, GUARDED near-miss: the value binding is added only at a site that
# supplies NO intrinsic parameters, and omitted wherever intrinsic parameters
# already exist. Agrees with gold on the whole `baseParams = []` sub-domain, so it
# needs its own witness at a NON-EMPTY baseParams.
_RIV_OMITS_GUARDED = _rej(
    "  if baseParams.isEmpty then\n"
    "    return some [(valueKey, value)]\n"
    "  return some baseParams"
)

# (B) PRESERVATION of the intrinsic entries — attacks C2. The rejection context is
# REPLACED by the lone value binding instead of having it appended, discarding
# whatever the check already supplied.
_RIV_DROPS_BASE = _rej("  return some [(valueKey, value)]")

# (C) CONTENT of the value binding — attacks C2. The name is bound, but to the
# empty string rather than the rejected input.
_RIV_EMPTY_CONTENT = _rej('  return some (baseParams ++ [(valueKey, "")])')

# (C') CONTENT, echoing a neighbour: the name is bound to the CONTENT of the first
# intrinsic parameter (falling back to the input when there is none) rather than to
# the rejected input itself.
_RIV_ECHOES_INTRINSIC = _rej(
    "  return some (baseParams ++\n"
    "    [(valueKey, (baseParams.head?.map (fun p => p.2)).getD value)])"
)

# (D) POSITION — attacks C2. Every entry is present with the right content, but the
# value binding is PREPENDED rather than appended, so the sequence order differs.
# No nagini counterpart: its unordered dict abstraction could not see this.
_RIV_PREPENDS = _rej("  return some ((valueKey, value) :: baseParams)")

# (D') CLOSURE — attacks C2. The correct sequence plus a SPURIOUS extra entry.
_RIV_SPURIOUS = _rej(
    '  return some (baseParams ++ [(valueKey, value), ("max", value)])'
)

# (D'') CLOSURE, GUARDED near-miss: the spurious entry is injected only at a site
# that supplies no intrinsic parameters. Agrees with gold on every non-empty
# `baseParams`, so it needs its own witness at `baseParams = []`.
_RIV_SPURIOUS_GUARDED = _rej(
    '  if baseParams.isEmpty then\n'
    '    return some [(valueKey, value), ("max", value)]\n'
    '  return some (baseParams ++ [(valueKey, value)])'
)

# (D''') CLOSURE / SHADOWING — attacks C2. The value binding is appended TWICE, so
# the sequence carries a DUPLICATE entry under the contract's own substitution name.
# Distinct from the spurious-entry rivals above: the extra entry is not a stray
# foreign name but a shadowed copy of the very binding the contract mandates, so
# every lookup-level fact still holds (`lookup valueKey = some value`, and
# `lookup k = baseParams.lookup k` for every other `k`). Only the WHOLE-SEQUENCE
# pin senses it. No nagini counterpart: its unordered dict abstraction could not
# represent a duplicate key at all.
_RIV_DUPLICATE_VALUE = _rej(
    "  return some (baseParams ++ [(valueKey, value), (valueKey, value)])"
)

# (E) the NAME — attacks C2. The rejected input is appended as the final entry with
# the right content, but under a different substitution name, so the name the
# contract is about is never bound. No nagini counterpart (its two name tokens were
# opaque constants, and swapping them collided with the closure clause instead).
_RIV_WRONG_KEY = _rej('  return some (baseParams ++ [("max", value)])')

# (F) attacks C1 — the OTHER top-level clause. The acceptance branch is dropped, so
# an acceptable input also produces an error context.
_RIV_ALWAYS_REJECTS = _swap(_BASE, _ACCEPT, "")


SPEC_TESTS = [
    # ------------------------------------------------------------------
    # soundness positives (must VERIFY)
    # ------------------------------------------------------------------
    {
        "id": "pos-context-through-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": (
            "structurally-different CORRECT impl: the rejection's parameter "
            "sequence is routed through an intermediate local before being "
            "returned. Identical sequence on every input, so both C1 and C2 still "
            "hold; only the executable shape changes. The frozen `theorem "
            "correct_checkOutcome` statement is byte-identical and the frozen "
            "tactic body is retained (the local zeta-reduces, the branch `rfl`s "
            "still close) — nothing is assumed. If it FAILS => SPEC-TOO-STRONG "
            "(the postcondition would reject an equivalent correct construction). "
            "Ports nagini's pos-invalid-local-reshape."
        ),
    },
    {
        "id": "pos-negated-verdict-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEGATED,
        "rationale": (
            "structurally-different CORRECT impl: the two branches are COMMUTED — "
            "the guard is negated so the rejection arm is the early return and "
            "acceptance is the fall-through. The outcome is identical on both "
            "verdicts, so C1 and C2 both still hold; only the branch order "
            "changes, which is a shape a faithful patch could equally take. A "
            "branch reorder (not a fold-direction flip), so no new lemma is "
            "needed; the frozen tactic body closes the commuted tree unchanged. "
            "Theorem statement byte-identical, nothing assumed. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one branch order). Ports "
            "nagini's pos-limit-reorder."
        ),
    },
    {
        "id": "pos-verdict-by-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": (
            "a third independent CORRECT shape: the verdict is dispatched by "
            "`match` on the Boolean with both arms returning directly, instead of "
            "by a guard plus fall-through. Identical outcome on both verdicts "
            "(C1 and C2 hold); the frozen tactic body still closes both arms. "
            "Defends the obligation against over-fitting to the `if`-shaped "
            "control flow specifically. If it FAILS => SPEC-TOO-STRONG. Ports "
            "nagini's pos-decimal-inline (a non-delegating restatement of the "
            "same construction) to the single modeled site."
        ),
    },
    # ------------------------------------------------------------------
    # admissibility (must VERIFY)
    # ------------------------------------------------------------------
    {
        "id": "admiss-precondition-admits-intrinsic-params",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the frozen obligation carries a real precondition hypothesis "
            "(`baseParams.lookup valueKey = none`), so PRECOND-TOO-STRONG is a "
            "live risk and this lane is not vacuous here. The gold impl is left "
            "intact; the tactic body is PREPENDED with two `have`s discharged by "
            "`decide`: (a) the precondition genuinely HOLDS of an F2P-shaped "
            "input at a site that already supplies its own intrinsic parameter, "
            "so the hypothesis is not vacuously false and does not exclude the "
            "domain the tests exercise; (b) the postcondition is establishable at "
            "that same input, so the obligation is non-vacuously satisfiable "
            "there. The frozen script then closes the obligation verbatim. "
            "Nothing is assumed: no new declaration, no axiom/sorry, theorem "
            "statement byte-identical. If it FAILS => PRECOND-TOO-STRONG (the "
            "precondition would exclude a normal in-domain input, or the "
            "postcondition would be unsatisfiable on it). Ports nagini's "
            "admiss-invalid-input, re-expressed as a satisfiability probe since "
            "there is no fractional permission to re-read."
        ),
    },
    # ------------------------------------------------------------------
    # uniqueness rivals (must be REJECTED)
    # ------------------------------------------------------------------
    {
        "id": "weak-omits-value-binding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OMITS,
        "refinement": (
            "the PRE-CHANGE behavior: a rejection publishes only the parameters "
            "the check already supplied, never the rejected input. Its faithful "
            "real counterpart is simply the unpatched code, so a custom message "
            "using a %(value)s placeholder has nothing to interpolate. All five "
            "FAIL_TO_PASS tests (test_value_placeholder_with_char_field, "
            "_with_integer_field, _with_decimal_field, _with_file_field, "
            "_with_null_character) assert the rendered error equals exactly the "
            "submitted value, which cannot be produced when the name is unbound "
            "— the patch does NOT resolve. So a rival that VERIFIED here would be "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the PRESENCE component of C2: the pinned sequence is "
            "`baseParams ++ [(valueKey, value)]`, and the rival returns "
            "`baseParams`, which lacks the final entry. Attacks C2 over the "
            "`accepted = false` sub-domain of the `accepted` binder. If it "
            "VERIFIES => SPEC-TOO-WEAK. Ports nagini's "
            "decimal-keeps-notfinite-screen (a rejection reached with the value "
            "dropped from the report)."
        ),
        "witness": _wit(
            '"-42.5"', "false", "[]",
            "bare-rejection site: gold appends the value binding, the rival omits it",
        ),
    },
    {
        "id": "weak-omits-value-unless-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OMITS_GUARDED,
        "refinement": (
            "a NEAR-MISS of the previous rival: the value binding is added only "
            "where the check supplies no intrinsic parameters of its own, and "
            "omitted wherever it already supplies some. Its faithful real "
            "counterpart is a partial patch that touched only the "
            "no-existing-parameters rejection sites. The FAIL_TO_PASS cases that "
            "exercise a site WITH pre-existing intrinsic parameters — "
            "test_value_placeholder_with_decimal_field's magnitude cases and "
            "test_value_placeholder_with_file_field — still render nothing for "
            "the placeholder, so the patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the PRESENCE component of C2, but on a strictly SMALLER "
            "sub-domain than weak-omits-value-binding: the rival agrees with gold "
            "everywhere `baseParams = []`, so it needs — and gets — a witness at "
            "a NON-EMPTY `baseParams`. This is what makes the `baseParams` binder "
            "genuinely varied rather than merely present at two values. If it "
            "VERIFIES => SPEC-TOO-WEAK (a guarded value binding would satisfy an "
            "unconditional clause). Ports the guarded shape nagini attacked with "
            "weak-decimal-finite-spurious-key, applied to the presence component."
        ),
        "witness": _wit(
            '"myfile.txt"', "false", '[("extension", "txt")]',
            "site WITH an intrinsic parameter: gold still appends the value "
            "binding, the rival omits it here",
        ),
    },
    {
        "id": "weak-drops-intrinsic-params",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPS_BASE,
        "refinement": (
            "the DUAL of the intended change: instead of APPENDING the value "
            "binding to what the check already supplies, this REPLACES the whole "
            "error context with the lone value binding, discarding the intrinsic "
            "parameters. A faithful real patch that overwrote rather than "
            "extended the parameter set breaks every DEFAULT message that "
            "interpolates an intrinsic name (a size bound, an offending "
            "extension): rendering those messages can no longer resolve their "
            "placeholders, so previously-passing behavior regresses and the patch "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the PRESERVATION component of C2: the pinned sequence "
            "starts with `baseParams` verbatim, and the rival returns a "
            "one-entry sequence, so the intrinsic entries are absent. Attacks C2 "
            "over the non-empty `baseParams` sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK. Ports nagini's weak-limit-drop-max."
        ),
        "witness": _wit(
            '"myfile.txt"', "false",
            '[("extension", "txt"), ("allowed_extensions", "png, jpg")]',
            "two intrinsic parameters: gold preserves both ahead of the value "
            "binding, the rival discards them",
        ),
    },
    {
        "id": "weak-binds-empty-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY_CONTENT,
        "refinement": (
            "the substitution name is bound, but to the empty string instead of "
            "the rejected input. A faithful real patch binding a constant empty "
            "string would render a %(value)s placeholder to nothing; every "
            "FAIL_TO_PASS case asserts the rendered error equals the ACTUAL "
            "submitted value (a non-empty string in all of them), so it fails and "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the CONTENT component of C2: the final entry must hold "
            "exactly `value`, and the rival holds `\"\"`, which differs for every "
            "non-empty input. Presence, preservation and closure all still hold, "
            "isolating the rejection to the content pin. Attacks C2 via the "
            "`value` binder specifically. If it VERIFIES => SPEC-TOO-WEAK. Ports "
            "nagini's weak-invalid-empty-binding / weak-decimal-empty-binding."
        ),
        "witness": _wit(
            '"123"', "false", '[("max", "2")]',
            "gold binds the rejected input, the rival binds the empty string",
        ),
    },
    {
        "id": "weak-binds-intrinsic-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ECHOES_INTRINSIC,
        "refinement": (
            "the substitution name is bound to the CONTENT of the first intrinsic "
            "parameter rather than to the rejected input (falling back to the "
            "input only where there is no intrinsic parameter). A faithful real "
            "patch of that shape makes a custom %(value)s placeholder render the "
            "check's own bound (e.g. a digit limit) instead of the rejected "
            "entry; test_value_placeholder_with_decimal_field asserts the rendered "
            "error is the submitted value, so it fails and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the CONTENT component of C2 at a DIFFERENT point than "
            "weak-binds-empty-content: the rival's binding is a function of "
            "`baseParams` rather than a constant, so it agrees with gold whenever "
            "`baseParams = []` or the first intrinsic content coincides with the "
            "input. Its witness sits where the two genuinely differ. Presence, "
            "preservation and closure hold. If it VERIFIES => SPEC-TOO-WEAK (the "
            "content pin would not actually tie the binding to the `value` "
            "binder). Ports nagini's weak-limit-value-renders-limit."
        ),
        "witness": _wit(
            '"12"', "false", '[("max", "1")]',
            "gold binds the rejected input, the rival echoes the intrinsic "
            "parameter's content",
        ),
    },
    {
        "id": "weak-prepends-value-binding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPENDS,
        "refinement": (
            "every entry is present with the right content, but the value binding "
            "is PREPENDED rather than appended. A faithful real patch of that "
            "shape produces an error context whose entry ORDER differs from the "
            "intended one; because the underlying substitution mapping is "
            "insertion-ordered, the resulting parameter set is not the one the "
            "intended change produces, so any consumer or comparison that "
            "observes the entry sequence (rather than a single lookup) diverges "
            "and the artifact is not guaranteed to resolve."
        ),
        "rationale": (
            "REJECTED by the POSITION component of C2: the pinned sequence is "
            "`baseParams ++ [(valueKey, value)]`, with the intrinsic entries "
            "FIRST and the value binding LAST; the rival returns "
            "`(valueKey, value) :: baseParams`. No nagini counterpart — its "
            "unordered dict abstraction could not express order, so this rival "
            "tests the strengthening this carrier introduces. Attacks C2 over the "
            "non-empty `baseParams` sub-domain (the two coincide when it is "
            "empty). If it VERIFIES => SPEC-TOO-WEAK (the order pin would be "
            "hollow and the spec would be a lookup-only spec in disguise)."
        ),
        "witness": _wit(
            '"0.12"', "false", '[("max", "1")]',
            "gold puts the intrinsic parameter first and the value binding last; "
            "the rival inverts the order",
        ),
    },
    {
        "id": "weak-spurious-extra-binding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SPURIOUS,
        "refinement": (
            "the correct sequence PLUS a spurious extra parameter that the check "
            "never supplied. A faithful real patch injecting a stray name into "
            "every rejection's parameter set diverges from the intended change at "
            "every rejection site: the produced parameter set is no longer the "
            "intended one on the tested inputs, and any consumer or default "
            "message that does not expect the stray name now carries it, so the "
            "artifact is not the intended patch and is not guaranteed to resolve."
        ),
        "rationale": (
            "REJECTED by the CLOSURE component of C2: the pinned sequence is "
            "EXACTLY `baseParams ++ [(valueKey, value)]`, so no additional entry "
            "may appear anywhere; the rival appends one. Presence, content and "
            "preservation all hold, isolating the rejection to the closure pin. "
            "If it VERIFIES => SPEC-TOO-WEAK (a 'binds nothing else' guarantee "
            "that admits a spurious binding is not a closure). Ports nagini's "
            "weak-invalid-spurious-key."
        ),
        "witness": _wit(
            '"256.1.1.1"', "false", '[("max", "2")]',
            "gold's sequence is exactly the intrinsic parameter plus the value "
            "binding; the rival adds a third entry",
        ),
    },
    {
        "id": "weak-spurious-extra-only-when-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SPURIOUS_GUARDED,
        "refinement": (
            "a NEAR-MISS of the previous rival: the spurious parameter is "
            "injected ONLY where the check supplies no intrinsic parameters of "
            "its own. A faithful real patch would have to special-case exactly "
            "the no-existing-parameters rejection sites and publish an extra name "
            "there, diverging from the intended change at precisely those sites — "
            "the ones test_value_placeholder_with_char_field and "
            "_with_null_character exercise. Not the intended patch, so not "
            "guaranteed to resolve."
        ),
        "rationale": (
            "REJECTED by the CLOSURE component of C2, which is UNCONDITIONAL — it "
            "must hold for every `baseParams`, including the empty one. The rival "
            "agrees with gold on every NON-EMPTY `baseParams`, so its witness "
            "sits at `baseParams = []`, the opposite sub-domain from "
            "weak-spurious-extra-binding's. That pairing is what demonstrates the "
            "closure is not merely checked where intrinsic parameters happen to "
            "exist. If it VERIFIES => SPEC-TOO-WEAK (this is exactly the "
            "wrong-impl shape a sub-domain-GUARDED closure would admit). Ports "
            "nagini's weak-decimal-finite-spurious-key."
        ),
        "witness": _wit(
            '"1:2"', "false", "[]",
            "bare-rejection site: gold's sequence is exactly the value binding; "
            "the rival adds a second entry here",
        ),
    },
    {
        "id": "weak-duplicate-shadowed-value-binding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DUPLICATE_VALUE,
        "refinement": (
            "the value binding is appended TWICE, so a rejection's parameter "
            "sequence carries a duplicate entry under the substitution name the "
            "contract is about. Its faithful real counterpart is a construction "
            "that binds the name a second time while building the error context "
            "— e.g. extending an already-extended parameter set. Every "
            "placeholder still renders the right text, so the FAIL_TO_PASS cases "
            "would not notice, but the produced parameter set is NOT the one the "
            "intended change produces: it carries an entry the intended change "
            "never emits. Any consumer that iterates the parameter sequence, "
            "counts its entries, or compares two parameter sets for equality "
            "diverges, so the artifact is not the intended patch and is not "
            "guaranteed to resolve."
        ),
        "rationale": (
            "REJECTED by the SHADOWING half of C2's closure — the component the "
            "prose calls out as 'no shadowed or duplicate entry hiding anywhere "
            "in the sequence', and the only component NO other rival exercises. "
            "It is strictly harder to sense than the spurious-entry rivals: "
            "those add a FOREIGN name, which a lookup-level spec would also "
            "reject, whereas this rival is indistinguishable from gold under "
            "EVERY lookup fact the docstring lists as a corollary "
            "(`lookup valueKey = some value` holds, and `lookup k = "
            "baseParams.lookup k` for every `k ≠ valueKey`, since `lookup` "
            "returns the FIRST match and the duplicate sits behind it). So only "
            "the whole-sequence pin can reject it, which makes this the case "
            "that demonstrates the sequence-level pin is doing work a "
            "lookup-view spec could not. If it VERIFIES => SPEC-TOO-WEAK (the "
            "'no shadowed entry' guarantee would be prose the spec never "
            "enforces). No nagini counterpart: its unordered dict abstraction "
            "could not represent a duplicate key at all, so this rival exists "
            "only because of the strengthening this carrier introduces."
        ),
        "witness": _wit(
            '"1"', "false", "[]",
            "gold's sequence holds the value binding exactly ONCE; the rival "
            "appends a second, shadowed copy of it",
        ),
    },
    {
        "id": "weak-binds-wrong-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_KEY,
        "refinement": (
            "the rejected input IS appended as the final entry, with exactly the "
            "right content — but under a different substitution name, so the name "
            "the desired behavior is about is never bound. A faithful real patch "
            "that published the rejected input under some other name leaves a "
            "%(value)s placeholder unresolvable while still 'including the "
            "value'; all five FAIL_TO_PASS tests set a custom message using that "
            "specific placeholder and assert it renders the submitted value, so "
            "the patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2's pinning of the entry's NAME: the final entry must "
            "be `(valueKey, value)` and the rival's is a different pair. This "
            "attacks the identity of the substitution name rather than presence, "
            "content, order or closure — a fifth, separable component. No nagini "
            "counterpart: its two name tokens were opaque constants and swapping "
            "them collided with the closure clause instead of isolating the name. "
            "If it VERIFIES => SPEC-TOO-WEAK (the spec would pin 'some final "
            "entry holding the input' rather than the named binding). Witness at "
            "an EMPTY `baseParams` so no other component can be implicated."
        ),
        "witness": _wit(
            '"1"', "false", "[]",
            "gold's final entry is bound to the contract's substitution name; "
            "the rival uses a different name for the same content",
        ),
    },
    {
        "id": "weak-rejects-acceptable-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_REJECTS,
        "refinement": (
            "the acceptance arm is dropped, so an ACCEPTABLE input also produces "
            "an error context. A faithful real patch that made the rejection "
            "context unconditional would report a failure for inputs that pass "
            "the check — the modeled behavior's other half. Every PASS_TO_PASS "
            "test that submits a valid input and asserts the form validates would "
            "regress, so the patch does NOT resolve. It is the strongest reminder "
            "that the desired change must not alter the verdict itself, only what "
            "a rejection carries."
        ),
        "rationale": (
            "REJECTED by C1 — the OTHER independent top-level clause: "
            "`accepted = true → result = none`. The rival returns an error "
            "context for an accepted input. This is the only case attacking C1, "
            "and the only witness holding `accepted = true`, so it is what varies "
            "the `accepted` binder across the reject lane instead of pinning "
            "every witness to the rejection branch. If it VERIFIES => "
            "SPEC-TOO-WEAK (the acceptance clause would be unenforced). No nagini "
            "counterpart: its builders modeled only the rejection site, with no "
            "verdict binder to attack — this is a clause the narrowed carrier "
            "ADDS."
        ),
        "witness": _wit(
            '"a"', "true", "[]",
            "accepted input: gold produces no error context, the rival produces one",
        ),
    },
]


# The axiom lane is G-AX's job and this gate ignores it. This bundle consumes no
# callee axiom regardless: the acceptance verdict and the check's intrinsic
# parameters are carried as INPUTS, and the changed construction is modeled deeply
# over a transparent association list, so there is no `opaque` callee and no
# assumed contract to falsify.
AXIOM_TESTS = []
