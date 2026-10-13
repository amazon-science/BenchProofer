"""properties.py — G-PBT falsification battery for psf__requests-1766 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves or discharges a ground instance, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the ``theorem correct_digestAuthHeader`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect="reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` HOLDS of the rival while FAILING
on the frozen solution).

DEFENDED SURFACE (one total function; ``String`` ↔ Python ``str`` identity):

  digestAuthHeader
      (username realm nonce uri respdig opaqueVal algorithm entdig qop
       ncvalue cnonce : String) : String
      result = <the assembled header value>

  The result is the literal prefix followed by a comma-separated directive list:
  the five mandatory directives (each carrying a double-quoted-string parameter),
  then the optional directives — each APPENDED exactly when its component value
  is non-empty, in canonical order — and, when a quality-of-protection value is
  in effect, the quality-of-protection directive together with the nonce-count
  and client-nonce directives. Per the scheme, a directive whose value is a
  quoted-string parameter is wrapped in double quotes; the quality-of-protection
  value is one such quoted-string parameter, while the nonce-count value is a
  bare token.

  The single top-level clause is a FULL equality pinning the whole output to a
  function of the eleven inputs (no output component is left free). It folds
  several inseparable sub-decisions, each pinned to distinct binders:

    * QUOTING OF THE QUALITY-OF-PROTECTION VALUE — the discriminating decision.
      Its value is the double-quoted token; a bare / single-quoted / unbalanced
      rendering differs. Pinned by ``qop`` (present) and the fixed token.
    * ORDER AND VALUES of the nonce-count and client-nonce directives — the
      nonce-count value is bare, the client-nonce value is quoted; interchanging
      them yields the wrong rendering. Pinned by ``ncvalue`` and ``cnonce``.
    * QUOTING OF THE MANDATORY quoted-string parameters (username, realm, nonce,
      uri, response). Pinned by those five binders.
    * PRESENCE of each optional directive — appended iff its component value is
      non-empty. Pinned by ``opaqueVal`` / ``algorithm`` / ``entdig``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY: its inputs are held at fractional (read-only)
    permission and a rival that overwrites one is rejected for insufficient
    permission. Lean is referentially transparent — the inputs are plain
    immutable ``String`` values, there is no half-permission to violate and no
    aliasing to exploit — so this class has NO expressible instance here and no
    substitute is fabricated for it. (nagini "frame-mutate-base" omitted.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the eleven inputs by fully-unfolded
    concatenation and present-iff-non-empty branching. The bundle declares no
    ``opaque`` / ``axiom`` (meta.json axioms == [], deep_model_references == []),
    so there is no answer key an implementation could echo. The honest analogue
    is the cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN (the pre-patch bug) — APPLIES, and is the load-bearing rival.
    The pre-fix rendered the quality-of-protection value as a BARE token; it is
    correct on every configuration except the one byte-pair the fix is about, so
    it is refuted precisely at a present-value input. (nagini "weak-bare-value".)

  * NEAR-MISS QUOTING and VALUE rivals — APPLY: single-quoting the value, an
    unbalanced (missing-closing-quote) value, and interchanging the nonce-count
    and client-nonce values. Each violates the one clause on a distinct
    sub-domain and is refuted at a distinct input. (nagini "weak-single-quote",
    "weak-missing-close-quote", "weak-swap-nc-cnonce".)

  * CARRIER-WIDENING rivals — the lean model assembles the WHOLE header (eleven
    inputs, three optional directives), where the nagini sibling modeled only the
    quality-of-protection tail (three inputs). Two rivals exercise the extra
    surface so its binders are not left un-attacked: one drops the double quotes
    from a mandatory quoted-string parameter, and one omits an optional directive
    that its non-empty component value requires. These have no nagini counterpart
    (that carrier did not model these binders) — they are added, not ported.

  * AUDIT-ADDED rivals — five further rivals aimed at clauses the ported lane
    pinned but never attacked, each refuted at a point the existing rivals do not
    reach: the emitted quality-of-protection value is the FIXED token rather than
    an echo of the supplied component value (every ported rival varies the
    QUOTING while holding the token fixed, so none of them discriminates an
    echo); the directive SEPARATOR carries its space; the scheme PREFIX is
    present (no ported rival touches it); the present-iff-non-empty guard has the
    right POLARITY at an ABSENT value (the drop-optional rival is refuted only at
    a PRESENT value, so 'absent ⇒ omitted' was un-probed); and the nonce-count
    and client-nonce DIRECTIVES are in canonical order with each value still in
    its own bare/quoted slot (distinct from interchanging the two VALUES, which
    is refuted only when they differ).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked to HOLD of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).
All witnesses use SHORT string literals so ``decide`` reduces the concatenations
without hitting the recursion limit.

BINDER COVERAGE. All eleven input binders are varied across the reject witnesses
(no binder is held at a single value across the lane): the quality-of-protection
rivals move ``qop``/``ncvalue``/``cnonce`` and toggle the optional flags, the
mandatory-quoting rival moves ``respdig`` with ``qop`` ABSENT, and the
drop-optional rival supplies a non-empty ``opaqueVal``. The audit-added rivals
add the points the lane was missing on the VERDICT side rather than merely on the
spelling side: a ``qop`` component value that DIFFERS from the emitted token
(which is what separates an echo from the fixed token), an ABSENT optional value
under an inverted guard, and the emptiest configuration in the lane (no optional
directive, no quality-of-protection value) for the prefix clause. ``pts`` = 11
distinct input points.

POSITIVE-CONTROL DISCIPLINE. The spec's top-level clause is an equality against a
pure helper, so a "different shape" that is DEFINITIONALLY equal to that helper
closes by ``rfl`` and tests nothing — it would verify against any spec of that
form. Both soundness controls are therefore reshapes whose proof must go through
a real rewriting step (associativity of concatenation over the free component
parameters, which is not definitional; unfolding a factored helper ``def``), each
confirmed not to close by ``rfl`` or by the frozen script.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
assembly is pure string concatenation over free component-string parameters, so
there is no in-model axiom obligation for the PBT axiom lane to re-discharge (and
that lane is G-AX's job regardless). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "psf__requests-1766"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean, verified at load) ----

# The single impl line that renders the quality-of-protection directive with its
# double-quoted value plus the bare nonce-count and quoted client-nonce values.
_QOP_LINE = (
    '    base := base ++ ", qop=\\"auth\\", nc=" ++ ncvalue '
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""'
)

# The mandatory-directive assembly block (opens `base` with the five mandatory
# double-quoted-string parameters).
_MANDATORY_BLOCK = (
    '  let mut base :=\n'
    '    "username=\\"" ++ username ++ "\\", realm=\\"" ++ realm '
    '++ "\\", nonce=\\"" ++ nonce\n'
    '      ++ "\\", uri=\\"" ++ uri ++ "\\", response=\\"" ++ respdig ++ "\\""'
)

# The optional `opaque` directive block (appended iff opaqueVal is non-empty).
_OPAQUE_BLOCK = (
    '  if opaqueVal ≠ "" then\n'
    '    base := base ++ ", opaque=\\"" ++ opaqueVal ++ "\\""\n'
)

# The impl head (used by a positive control that factors out a helper `def`).
_IMPL_HEAD = (
    'def implementation_digestAuthHeader\n'
    '    (username realm nonce uri respdig opaqueVal algorithm entdig qop '
    'ncvalue cnonce : String) :\n'
    '    String := Id.run do'
)

# The `Digest ` scheme-prefix return line.
_PREFIX_LINE = '  return "Digest " ++ base'

# The optional `algorithm` directive block (appended iff algorithm is non-empty).
_ALGORITHM_BLOCK = (
    '  if algorithm ≠ "" then\n'
    '    base := base ++ ", algorithm=\\"" ++ algorithm ++ "\\""'
)

# The whole gold impl body.
_IMPL_GOLD = (
    'def implementation_digestAuthHeader\n'
    '    (username realm nonce uri respdig opaqueVal algorithm entdig qop '
    'ncvalue cnonce : String) :\n'
    '    String := Id.run do\n'
    '  let mut base :=\n'
    '    "username=\\"" ++ username ++ "\\", realm=\\"" ++ realm '
    '++ "\\", nonce=\\"" ++ nonce\n'
    '      ++ "\\", uri=\\"" ++ uri ++ "\\", response=\\"" ++ respdig ++ "\\""\n'
    '  if opaqueVal ≠ "" then\n'
    '    base := base ++ ", opaque=\\"" ++ opaqueVal ++ "\\""\n'
    '  if algorithm ≠ "" then\n'
    '    base := base ++ ", algorithm=\\"" ++ algorithm ++ "\\""\n'
    '  if entdig ≠ "" then\n'
    '    base := base ++ ", digest=\\"" ++ entdig ++ "\\""\n'
    '  if qop ≠ "" then\n'
    '    -- the quality-of-protection directive carries a quoted-string parameter\n'
    '    base := base ++ ", qop=\\"auth\\", nc=" ++ ncvalue '
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""\n'
    '  return "Digest " ++ base'
)

# The frozen tactic body (byte-for-byte).
_PROOF_BODY = (
    '  intro username realm nonce uri respdig opaqueVal algorithm entdig qop '
    'ncvalue cnonce\n'
    '  unfold problem_spec_digestAuthHeader implementation_digestAuthHeader '
    'assembledDigestHeader\n'
    '  simp only [Id.run, bind, pure]\n'
    '  split <;> split <;> split <;> split <;> rfl'
)

# sanity: every anchor present exactly once
assert _BASE.count(_QOP_LINE) == 1, "impl qop line drifted"
assert _BASE.count(_MANDATORY_BLOCK) == 1, "mandatory block drifted"
assert _BASE.count(_OPAQUE_BLOCK) == 1, "opaque block drifted"
assert _BASE.count(_ALGORITHM_BLOCK) == 1, "algorithm block drifted"
assert _BASE.count(_IMPL_HEAD) == 1, "impl head drifted"
assert _BASE.count(_PREFIX_LINE) == 1, "prefix line drifted"
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


# ---------------------------------------------------------------------------
# Rival impls (each replaces exactly one impl fragment; spec + theorem STATEMENT
# stay byte-identical). Each edit lies strictly inside # impl-start/# impl-end.
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN (= the pre-fix bug): render the quality-of-protection value as a
# BARE token instead of a double-quoted string parameter.
_BARE_VALUE = _swap(
    _BASE, _QOP_LINE,
    '    base := base ++ ", qop=auth, nc=" ++ ncvalue '
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""')

# NEAR-MISS: single-quote the value.
_SINGLE_QUOTE = _swap(
    _BASE, _QOP_LINE,
    "    base := base ++ \", qop='auth', nc=\" ++ ncvalue "
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""')

# NEAR-MISS: open the value quote but never close it (unbalanced).
_NO_CLOSE = _swap(
    _BASE, _QOP_LINE,
    '    base := base ++ ", qop=\\"auth, nc=" ++ ncvalue '
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""')

# VALUE: interchange the nonce-count and client-nonce values (bare vs quoted
# slots swapped).
_SWAP_NC = _swap(
    _BASE, _QOP_LINE,
    '    base := base ++ ", qop=\\"auth\\", nc=" ++ cnonce '
    '++ ", cnonce=\\"" ++ ncvalue ++ "\\""')

# CARRIER-WIDENING: drop the double quotes from a mandatory quoted-string
# parameter (the response value emitted bare).
_UNQUOTED_RESPDIG = _swap(
    _BASE, _MANDATORY_BLOCK,
    '  let mut base :=\n'
    '    "username=\\"" ++ username ++ "\\", realm=\\"" ++ realm '
    '++ "\\", nonce=\\"" ++ nonce\n'
    '      ++ "\\", uri=\\"" ++ uri ++ "\\", response=" ++ respdig')

# CARRIER-WIDENING: never append the optional `opaque` directive, even when its
# component value is non-empty.
_DROP_OPAQUE = _swap(_BASE, _OPAQUE_BLOCK, '')

# VALUE-ECHO: emit the SUPPLIED quality-of-protection component value as the
# directive's value instead of the fixed token the scheme mandates. Correct on
# every input whose component value happens to BE that token, so it is refuted
# only at a component value that differs from it — the sharpest probe of "the
# emitted value is the fixed token, not whatever came in".
_ECHO_QOP_INPUT = _swap(
    _BASE, _QOP_LINE,
    '    base := base ++ ", qop=\\"" ++ qop ++ "\\", nc=" ++ ncvalue '
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""')

# SEPARATOR: omit the space after the directive separator comma.
_NO_SPACE_SEP = _swap(
    _BASE, _QOP_LINE,
    '    base := base ++ ",qop=\\"auth\\", nc=" ++ ncvalue '
    '++ ", cnonce=\\"" ++ cnonce ++ "\\""')

# PREFIX: drop the scheme prefix from the assembled value. Refuted on EVERY
# input, including one with no optional directive and no quality-of-protection
# value in effect, so it probes the prefix clause alone.
_DROP_PREFIX = _swap(_BASE, _PREFIX_LINE, '  return base')

# GUARD POLARITY: append an optional directive exactly when its component value
# is EMPTY (the guard inverted). Refuted at an absent component value, the half
# of the present-iff-non-empty clause the drop-optional rival leaves unattacked
# (that one is refuted only at a PRESENT value).
_INVERTED_OPTIONAL_GUARD = _swap(
    _BASE, _ALGORITHM_BLOCK,
    '  if algorithm = "" then\n'
    '    base := base ++ ", algorithm=\\"" ++ algorithm ++ "\\""')

# DIRECTIVE ORDER: emit the client-nonce directive BEFORE the nonce-count
# directive. Distinct from the value-interchange rival: the VALUES stay in their
# own (bare / quoted) slots and only the two directives' ORDER changes, so this
# probes the canonical-order clause rather than the value binding.
_REORDER_NC_CNONCE = _swap(
    _BASE, _QOP_LINE,
    '    base := base ++ ", qop=\\"auth\\", cnonce=\\"" ++ cnonce '
    '++ "\\", nc=" ++ ncvalue')

# POSITIVE CONTROL 1 (soundness): a CORRECT reshape that RE-ASSOCIATES the
# mandatory-directive concatenation to the right. Concatenation of the free
# component parameters is associative but NOT definitionally so — with the
# parameters symbolic, neither side reduces, and the reshaped term is provably
# equal to the frozen one only via the associativity lemma. (Machine-checked:
# closing this by the frozen script, or by `rfl`, does not elaborate — `rfl`
# exhausts the whnf heartbeat budget — so the case genuinely re-proves the
# obligation for a shape the spec has to accept on its own terms rather than by
# reducing to the frozen one.) MUST VERIFY, else SPEC-TOO-STRONG.
_POS_REASSOC_IMPL = (
    '  let mut base :=\n'
    '    "username=\\"" ++ (username ++ ("\\", realm=\\"" ++ (realm '
    '++ ("\\", nonce=\\"" ++\n'
    '      (nonce ++ ("\\", uri=\\"" ++ (uri ++ ("\\", response=\\"" ++ '
    '(respdig ++ "\\"")))))))))'
)
_POS_REASSOC_PROOF = (
    '  intro username realm nonce uri respdig opaqueVal algorithm entdig qop '
    'ncvalue cnonce\n'
    '  unfold problem_spec_digestAuthHeader implementation_digestAuthHeader '
    'assembledDigestHeader\n'
    '  simp only [Id.run, bind, pure]\n'
    '  split <;> split <;> split <;> split <;> '
    'simp only [String.append_assoc]'
)
_POS_REASSOC = _swap(
    _swap(_BASE, _MANDATORY_BLOCK, _POS_REASSOC_IMPL),
    _PROOF_BODY, _POS_REASSOC_PROOF)

# POSITIVE CONTROL 2 (soundness): a CORRECT reshape that FACTORS the rendering of
# a quoted-string-parameter directive into an impl-region helper `def` and calls
# it for each optional directive, instead of inlining the concatenation three
# times. The helper is a new `def` (admissible: `variant_scope` bans new
# theorems/axioms, not impl-region helpers) whose applications must be unfolded
# and re-associated before the two sides meet, so the frozen script does not
# apply and the obligation is genuinely re-proved for the factored shape.
# MUST VERIFY, else SPEC-TOO-STRONG.
_POS_HELPER_HEAD = (
    '/-- render one directive whose value is a quoted-string parameter -/\n'
    'def quotedDirective (key value : String) : String :=\n'
    '  ", " ++ key ++ "=\\"" ++ value ++ "\\""\n'
    '\n'
    + _IMPL_HEAD
)
_POS_HELPER = _swap(_BASE, _IMPL_HEAD, _POS_HELPER_HEAD)
for _key, _var in (('opaque', 'opaqueVal'), ('algorithm', 'algorithm'),
                   ('digest', 'entdig')):
    _POS_HELPER = _swap(
        _POS_HELPER,
        f'    base := base ++ ", {_key}=\\"" ++ {_var} ++ "\\""',
        f'    base := base ++ quotedDirective "{_key}" {_var}')
_POS_HELPER_PROOF = (
    '  intro username realm nonce uri respdig opaqueVal algorithm entdig qop '
    'ncvalue cnonce\n'
    '  have hopaque : ∀ v : String, quotedDirective "opaque" v '
    '= ", opaque=\\"" ++ v ++ "\\"" := by\n'
    '    intro v; unfold quotedDirective; rfl\n'
    '  have halgorithm : ∀ v : String, quotedDirective "algorithm" v '
    '= ", algorithm=\\"" ++ v ++ "\\"" := by\n'
    '    intro v; unfold quotedDirective; rfl\n'
    '  have hdigest : ∀ v : String, quotedDirective "digest" v '
    '= ", digest=\\"" ++ v ++ "\\"" := by\n'
    '    intro v; unfold quotedDirective; rfl\n'
    '  unfold problem_spec_digestAuthHeader implementation_digestAuthHeader '
    'assembledDigestHeader\n'
    '  simp only [Id.run, bind, pure, hopaque, halgorithm, hdigest]\n'
    '  split <;> split <;> split <;> split <;>\n'
    '    simp only [String.append_assoc]'
)
_POS_HELPER = _swap(_POS_HELPER, _PROOF_BODY, _POS_HELPER_PROOF)

# ADMISSIBILITY: discharge the obligation at a normal, F2P-shaped ground input
# (quality-of-protection in effect, no optional directives) INSIDE the proof
# region, alongside the frozen obligation. If that ground instance could not be
# discharged, the modeled behavior would be unsatisfiable at exactly the input
# the F2P exercises. STATEMENT byte-identical; no new declaration/axiom/sorry.
_ADMISS_GROUND = (
    '  have _ground : problem_spec_digestAuthHeader\n'
    '      "usr" "rlm" "nnc" "/u" "rd" "" "" "" "auth" "01" "cn"\n'
    '      (implementation_digestAuthHeader\n'
    '        "usr" "rlm" "nnc" "/u" "rd" "" "" "" "auth" "01" "cn") := by\n'
    '    unfold problem_spec_digestAuthHeader implementation_digestAuthHeader '
    'assembledDigestHeader\n'
    '    decide\n'
)
_ADMISS = _swap(_BASE, _PROOF_BODY, _ADMISS_GROUND + _PROOF_BODY)


def _witness(args, comment):
    """A witness `example` asserting the spec fails of the rival at `args`."""
    return (
        f"{comment}\n"
        f"example : ¬ problem_spec_digestAuthHeader {args}\n"
        f"    (implementation_digestAuthHeader {args}) := by\n"
        f"  unfold problem_spec_digestAuthHeader implementation_digestAuthHeader "
        f"assembledDigestHeader\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — CORRECT impls that MUST verify (else
    # SPEC-TOO-STRONG). The theorem STATEMENT is byte-identical in each; the
    # tactic body is re-proved for the new shape.
    #
    # Both reshapes are chosen so the reshaped term is NOT definitionally equal
    # to the frozen one: the spec's own top-level equality is against a pure
    # helper, so a reshape that merely spells that helper's body a second way
    # collapses to it by `rfl` and tests only that `rfl` is reflexive — it would
    # verify against ANY spec of the form `result = <helper>` and so attests to
    # nothing. Each control below instead forces the proof through a real
    # rewriting step (associativity of concatenation over the free component
    # parameters; unfolding a factored helper `def`), which is what makes
    # "the spec accepts a differently-shaped correct impl" a claim with content.
    # =====================================================================
    {
        "id": "pos-reassociated-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REASSOC,
        "rationale": (
            "a correct reshape that RE-ASSOCIATES the mandatory-directive "
            "concatenation to the right must satisfy the frozen equality `result "
            "= assembledDigestHeader …`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Concatenation of the free component parameters is "
            "associative but NOT definitionally so — with the parameters symbolic "
            "neither side reduces, and `rfl` on the reshaped goal exhausts the "
            "whnf heartbeat budget (measured), so the frozen script does not "
            "apply and the obligation is genuinely re-proved via "
            "`String.append_assoc`. No new declaration, axiom, or assumption "
            "token; the theorem STATEMENT is byte-identical."
        ),
    },
    {
        "id": "pos-factored-directive-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HELPER,
        "rationale": (
            "a correct reshape that FACTORS the rendering of a "
            "quoted-string-parameter directive into an impl-region helper `def` "
            "and calls it for each optional directive must satisfy the frozen "
            "equality `result = assembledDigestHeader …`; if it cannot, the spec "
            "is SPEC-TOO-STRONG. The helper's applications must be unfolded and "
            "the result re-associated before the two sides meet, so the frozen "
            "script does not apply and the obligation is re-proved for the "
            "factored shape. A new impl-region helper `def` is admissible (the "
            "variant scope bans new theorems/axioms, not helper definitions); no "
            "axiom or assumption token is introduced and the theorem STATEMENT is "
            "byte-identical."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input. The frozen theorem carries
    # NO precondition hypothesis (the behavior is total, so `∀` is unguarded), so
    # nagini's precondition-admission probe has no binder to attack; the honest
    # analogue is to discharge the spec predicate at the F2P ground input inside
    # the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-qop-present-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is discharged at an F2P-shaped ground input (a "
            "quality-of-protection value in effect, no optional directives), where "
            "the spec requires the quality-of-protection value be rendered as a "
            "double-quoted parameter, by `decide`; then the frozen obligation is "
            "closed verbatim. Verifies (else the spec is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the STATEMENT is byte-identical, the ground instance is a "
            "`have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-bare-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _BARE_VALUE,
        "refinement": (
            "this is exactly the pre-fix behavior: the quality-of-protection value "
            "is rendered as a BARE token. Its faithful real patch emits the bare "
            "value and FAILS the F2P observable, which asserts the double-quoted "
            "value substring is present in the assembled header — the bare "
            "rendering does not contain it, so it would not resolve. This is the "
            "leg's prepatch."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: with the "
            "quality-of-protection value in effect, the spec's rendering wraps the "
            "value in double quotes, but the rival emits it bare, so the two "
            "strings differ. Refuted at a present-value input; `qop='auth'`, no "
            "optional directives."
        ),
        "witness": _witness(
            '"u1" "r1" "n1" "/a" "rd1" "" "" "" "auth" "01" "c1"',
            "-- Refuted where the quality-of-protection value is in effect: the\n"
            "-- spec renders it as a double-quoted parameter; a bare token differs."),
    },
    {
        "id": "weak-single-quote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SINGLE_QUOTE,
        "refinement": (
            "wrapping the value in SINGLE quotes emits a single-quoted rendering; "
            "the F2P asserts the DOUBLE-quoted value substring is present, which a "
            "single-quoted rendering does not satisfy, and the scheme requires the "
            "double-quoted string — so it would not resolve."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec's rendering uses the double-quote glyph around the value; the "
            "single-quote glyph makes the two strings differ. Refuted at a "
            "quality-of-protection input (`qop='authb'`) with the optional "
            "`opaque` directive present, varying those binders off the values the "
            "other rivals use."
        ),
        "witness": _witness(
            '"u2" "r2" "n2" "/b" "rd2" "op" "" "" "authb" "02" "c2"',
            "-- Refuted where the value is single-quoted rather than double-quoted:\n"
            "-- the required rendering wraps it in double quotes."),
    },
    {
        "id": "weak-missing-close-quote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NO_CLOSE,
        "refinement": (
            "emitting only the opening quote produces an unbalanced, malformed "
            "value; the double-quoted value is no longer a contiguous balanced run "
            "(the following separator abuts the token), so the F2P substring is "
            "absent — it would not resolve, and the credential is malformed."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec's rendering closes the value quote; without the closing quote the "
            "assembled string differs. Refuted with the optional `algorithm` "
            "directive present (`algorithm='MD5'`), varying that flag."
        ),
        "witness": _witness(
            '"u3" "r3" "n3" "/c" "rd3" "" "MD5" "" "auth" "03" "c3"',
            "-- Refuted where the value quote is opened but never closed: the\n"
            "-- rendering must be a balanced double-quoted string."),
    },
    {
        "id": "weak-swap-nc-cnonce",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SWAP_NC,
        "refinement": (
            "interchanging the nonce-count and client-nonce values renders the "
            "nonce-count value in the (quoted) client-nonce slot and vice versa; "
            "the credential the server validates would be malformed and the "
            "request would fail on the endpoint the F2P exercises — so it would "
            "not resolve."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the spec "
            "renders the nonce-count value bare and the client-nonce value quoted; "
            "swapping them makes the two strings differ for any distinct "
            "nonce-count / client-nonce pair. Refuted with the optional `digest` "
            "directive present (`entdig='e4'`) and distinct `ncvalue`/`cnonce`, "
            "varying both value binders and that flag."
        ),
        "witness": _witness(
            '"u4" "r4" "n4" "/d" "rd4" "" "" "e4" "auth" "0A" "0B"',
            "-- Refuted where the nonce-count value ('0A') and client-nonce value\n"
            "-- ('0B') differ: each must appear in its own slot (bare vs quoted)."),
    },
    # --- carrier-widening rivals (no nagini counterpart; added, not ported) ---
    {
        "id": "weak-unquoted-mandatory-param",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNQUOTED_RESPDIG,
        "refinement": (
            "dropping the double quotes from a mandatory quoted-string parameter "
            "(the response value) emits it as a bare token; per the scheme that "
            "parameter is a quoted string, so a server would reject the malformed "
            "credential and the request would fail — it would not resolve. This "
            "attacks the mandatory-quoting sub-clause the nagini carrier did not "
            "model."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec's rendering wraps the response value in double quotes; emitting "
            "it bare makes the two strings differ. Refuted with the "
            "quality-of-protection value ABSENT (`qop=''`), so this witness holds "
            "the discriminating quoting binder at a different value than every "
            "quality-of-protection rival and varies `respdig` and the optional "
            "flags."
        ),
        "witness": _witness(
            '"u5" "r5" "n5" "/e" "rd5" "o5" "SHA" "e5" "" "05" "c5"',
            "-- Refuted on a mandatory quoted-string parameter (the response\n"
            "-- value) rendered bare; the quality-of-protection value is absent."),
    },
    {
        "id": "weak-drop-optional-directive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_OPAQUE,
        "refinement": (
            "never appending an optional directive whose component value is "
            "non-empty drops that directive from the assembled header; the pinned "
            "present-iff-non-empty behavior requires it to appear, so the "
            "assembled credential is missing a directive the input demands — it "
            "would not resolve. This attacks the optional-presence sub-clause the "
            "nagini carrier did not model."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec appends the optional directive exactly when its component value "
            "is non-empty; the rival omits it even for a non-empty value, so the "
            "two strings differ. Refuted with a non-empty `opaqueVal` "
            "(`opaqueVal='op6'`), varying that optional binder off the empty value "
            "the quality-of-protection rivals hold it at."
        ),
        "witness": _witness(
            '"u6" "r6" "n6" "/f" "rd6" "op6" "" "" "auth" "06" "c6"',
            "-- Refuted where an optional directive's component value is non-empty:\n"
            "-- the directive must be appended, but the rival omits it."),
    },
    # --- rivals added by audit, aimed at clauses the lane left un-probed ------
    {
        "id": "weak-echo-supplied-qop-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ECHO_QOP_INPUT,
        "refinement": (
            "emitting the SUPPLIED quality-of-protection component value as the "
            "directive's value, rather than the fixed token the scheme mandates, "
            "renders a value the scheme does not define whenever the supplied "
            "value is anything but that token — and a supplied value that is a "
            "comma-separated option list is exactly the case in play. The "
            "assembled credential then carries a value the server does not "
            "accept, so the request fails and it would not resolve. This attacks "
            "the sub-clause the other quality-of-protection rivals leave "
            "un-probed: they all vary the QUOTING of the value while keeping the "
            "token fixed, so none of them would notice a value that is echoed "
            "from the input instead of fixed."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec renders the fixed token as the directive's value regardless of "
            "the component value that put the directive in effect; echoing the "
            "component value instead makes the two strings differ for every "
            "component value other than that token. Refuted at a "
            "quality-of-protection component value that differs from the emitted "
            "token, which is what distinguishes this rival from a correct impl."
        ),
        "witness": _witness(
            '"u7" "r7" "n7" "/g" "rd7" "" "" "" "authq" "07" "c7"',
            "-- Refuted where the supplied quality-of-protection component value\n"
            "-- ('authq') differs from the fixed token the directive must carry:\n"
            "-- the rival echoes the input, the spec emits the fixed token."),
    },
    {
        "id": "weak-missing-separator-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NO_SPACE_SEP,
        "refinement": (
            "omitting the space after the directive separator emits a directive "
            "list whose separator is not the one the scheme's grammar writes; the "
            "assembled credential differs byte-for-byte from the required "
            "rendering, so a strict server parses a different directive list and "
            "the request fails — it would not resolve. This probes the separator "
            "sub-clause, which no other rival varies."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec's rendering separates directives with a comma followed by a "
            "space; dropping the space makes the two strings differ. Refuted at a "
            "quality-of-protection input with no optional directive present."
        ),
        "witness": _witness(
            '"u8" "r8" "n8" "/h" "rd8" "" "" "" "auth" "08" "c8"',
            "-- Refuted where the directive separator loses its space: the\n"
            "-- rendering separates directives with a comma AND a space."),
    },
    {
        "id": "weak-drop-scheme-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_PREFIX,
        "refinement": (
            "returning the directive list without the scheme prefix emits a "
            "header value that does not name the authentication scheme at all; a "
            "server cannot dispatch it and the request fails, so it would not "
            "resolve. No other rival touches the prefix — every one of them edits "
            "the directive list — so without this case the prefix clause is "
            "pinned by the spec but never attacked."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec's rendering is the scheme prefix followed by the directive "
            "list; dropping the prefix makes the two strings differ on EVERY "
            "input. Refuted at an input with the quality-of-protection value "
            "ABSENT and no optional directive present — the emptiest "
            "configuration in the lane, so this witness holds every optional "
            "binder at a point that isolates the prefix clause."
        ),
        "witness": _witness(
            '"u9" "r9" "n9" "/i" "rd9" "" "" "" "" "09" "c9"',
            "-- Refuted with no optional directive and no quality-of-protection\n"
            "-- value in effect: the rendering still begins with the scheme\n"
            "-- prefix, which the rival omits."),
    },
    {
        "id": "weak-inverted-optional-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _INVERTED_OPTIONAL_GUARD,
        "refinement": (
            "appending an optional directive exactly when its component value is "
            "EMPTY inverts the present-iff-non-empty behavior: the credential "
            "carries an empty-valued directive the input never supplied, and "
            "loses the directive when one WAS supplied. A server reading the "
            "spurious empty directive rejects the credential, so it would not "
            "resolve. This attacks the half of the present-iff-non-empty clause "
            "the drop-optional rival cannot reach: that rival is refuted only at "
            "a PRESENT component value, so a spec that pinned only 'present ⇒ "
            "appended' and left 'absent ⇒ omitted' free would still reject it "
            "while admitting this one."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec appends the optional directive exactly when its component value "
            "is non-empty, so for an EMPTY component value it must be omitted; the "
            "rival appends it precisely then, and the two strings differ. Refuted "
            "at an ABSENT optional component value — the polarity no other reject "
            "case pins."
        ),
        "witness": _witness(
            '"uA" "rA" "nA" "/j" "rdA" "" "" "" "auth" "0C" "cA"',
            "-- Refuted where an optional directive's component value is EMPTY:\n"
            "-- the directive must be omitted, but the rival appends it."),
    },
    {
        "id": "weak-reorder-nc-cnonce-directives",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REORDER_NC_CNONCE,
        "refinement": (
            "emitting the client-nonce directive before the nonce-count directive "
            "renders the directive list out of canonical order; the credential a "
            "strict server validates is malformed and the request fails, so it "
            "would not resolve. This is NOT the value-interchange rival: there "
            "each value lands in the other's slot, so that case is refuted only "
            "when the two values DIFFER and is really about the value binding. "
            "Here each value keeps its own slot (the nonce-count value stays "
            "bare, the client-nonce value stays quoted) and only the two "
            "directives' ORDER changes, so this is refuted even when the two "
            "values are equal and it pins the canonical-order clause on its own."
        ),
        "rationale": (
            "REJECT from the equality `result = assembledDigestHeader …`: the "
            "spec renders the nonce-count directive before the client-nonce "
            "directive; interchanging the two directives makes the two strings "
            "differ. Refuted at a quality-of-protection input, with the values "
            "left in their own bare/quoted slots so the divergence is the order "
            "and nothing else."
        ),
        "witness": _witness(
            '"uB" "rB" "nB" "/k" "rdB" "" "" "" "auth" "0D" "cB"',
            "-- Refuted on directive ORDER alone: each value keeps its own\n"
            "-- (bare / quoted) slot and only the nonce-count and client-nonce\n"
            "-- directives are interchanged."),
    },
]


# No consumed axioms and no deep-model references: the assembly is pure string
# concatenation over free component-string parameters (meta.json axioms == [],
# deep_model_references == []), so there is no in-model axiom obligation for the
# PBT axiom lane to re-discharge.
AXIOM_TESTS = []
