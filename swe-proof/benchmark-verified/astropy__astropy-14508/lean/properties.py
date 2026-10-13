"""properties.py — G-PBT falsification battery for astropy__astropy-14508 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_formatFloat`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no sorry/admit); ``expect="reject"``
passes iff (in scope AND it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a text carrier). Modeled: rendering a
numeric value's textual form into a field of at most 20 characters. The single
obligation is the equality

    result = truncate20 (normE inp.reprStr)

where ``inp.reprStr`` is the value's SHORTEST standard textual form, ``normE``
upper-cases the exponent marker, and ``truncate20`` shortens an over-long string
by one of two rules: with no exponent marker keep the first 20 characters; with
an exponent marker keep the exponent suffix intact and truncate the leading
significand so the whole string is 20 characters. The DISCRIMINATING content is
(a) WHICH textual form feeds the rule — the shortest form ``reprStr``, never a
fixed-precision expansion ``fixedStr`` — and (b) that over-cap shortening obeys
the two-rule structure exactly (bounded length; exponent suffix preserved).

CARRIER NOTE — this backend models only the purely functional core: the single
``formatFloat`` rendering rule. The nagini sibling additionally contracted the
grounded numeric theory (``shortest_field`` / ``shortest_seq`` / ``parse_dec`` /
``sig_count`` / ``min_sig`` / ``shortest_field_len``) as an AXIOM lane; here the
value's two textual observations are GROUNDED structure fields (``reprStr``,
``fixedStr``), not axiomatized callees, so there is no axiom lane on this
carrier. Nagini's ``AXIOM_TESTS`` are therefore dropped — the axiom lane is
G-AX's job and this gate ignores them (see OMITTED below).

ADVERSARIAL READ of the classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the sole input is a value (a record of two character lists), there is no
    read-only half-permission to overwrite and no aliasing. This class has no
    expressible instance here and no substitute is fabricated. (Nagini stated
    the same: the only argument is an interpreted value, nothing to
    over-permission.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the input (``truncate20 (normE
    inp.reprStr)``), fully unfolded; the bundle declares no ``opaque``/``axiom``,
    so there is no answer key an implementation could echo without doing the
    work. In its place the battery carries an honest cheapest-implementation
    POSITIVE CONTROL (``pos-*``) that must verify.

  * CARRIER-SELECTION DEFECT — APPLIES. One rival feeds the FIXED-PRECISION form
    to the rule instead of the shortest form (the pre-fix behavior): the
    headline break the issue is about.

  * SHORTENING-RULE DEFECT — APPLIES. Three rivals attack the over-cap
    shortening: never shortening at all (length bound broken), unconditional
    first-20 truncation that drops the exponent suffix (the with-exponent rule
    broken), and an off-by-one that keeps one extra significand character in the
    with-exponent arm (both length and content broken).

  * MARKER-NORMALIZATION DEFECT — APPLIES. One rival skips the exponent-marker
    upper-casing entirely (`normE` dropped). Added during audit: the other four
    rivals all leave `normE` in place and none of their witness points contains
    a lower-case `e`, so this half of the obligation was previously unprobed.

  * CONTROL-FLOW-EFFECT — DOES NOT APPLY. The behavior is total: it always
    returns a character list, never raises, has no side effect. The value
    abstraction (the returned string) fully captures the behavior, so there is
    no raise/no-raise discriminator.

BINDER VARIATION (why the reject witnesses sit where they do). The spec's only
INPUT binder is ``inp`` (the ``result`` binder is fixed to the applied
implementation output). Within ``inp`` only ``reprStr`` is load-bearing:
``fixedStr`` does NOT occur in the postcondition at all, so no admissible spec
predicate depends on it and no reject witness needs to move it — a rival that
mishandled ``fixedStr`` alone is INVISIBLE to the modeled behavior by
construction (that is exactly what the carrier-selection rival demonstrates: it
is caught only because it substitutes ``fixedStr`` WHERE ``reprStr`` was
required). The five reject witnesses therefore vary ``reprStr`` across the three
branches of ``truncate20`` plus the marker-normalization step — the value where
the two forms diverge (fits, ≤20), an over-cap string with NO exponent marker,
two over-cap strings WITH an exponent marker, and a fits-branch string carrying
a LOWER-CASE marker — so every arm of the shortening rule and the ``normE`` step
are each probed at a distinct input point:

  * ``reprStr = "0.009125"`` (8 chars, the FITS branch, ≤20) —
    ``weak-fixed-precision-carrier``. The value that separates the shortest form
    from the fixed-precision expansion.
  * ``reprStr = "12345678901234567890.5"`` (22 chars, over-cap, NO ``E``) —
    ``weak-echo-untrimmed``. Probes the length bound and the no-exponent arm.
  * ``reprStr = "1.23456789012345E+300"`` (21 chars, over-cap, WITH ``E``) —
    ``weak-trunc-first20`` and ``weak-offbyone-keep-plus1``. Probes the
    exponent-preserving arm. These two rivals are NEAR-MISSES on this arm (both
    keep an exponent but shorten it wrongly in different ways), yet they fail for
    DIFFERENT reasons at this point — the first drops the exponent entirely, the
    second keeps one significand character too many — so they legitimately share
    the input while attacking distinct facets of the same clause.
  * ``reprStr = "1.5e10"`` (6 chars, fits branch, LOWER-CASE marker) —
    ``weak-skip-marker-normalization``. The only witness point in the battery
    that carries a lower-case ``e``, and therefore the only one at which the
    ``normE`` step is observable at all.

POSITIVE CONTROLS (why there are two, and why neither is defeq to the frozen
impl). A positive whose "different shape" is DEFINITIONALLY EQUAL to the frozen
one passes honestly while testing nothing, so both positives here were checked
to FAIL under bare ``rfl`` (the tactic that closes the frozen obligation) and to
require a real re-proof: ``pos-complement-guard`` flips the guard's polarity and
must rewrite the frozen ``if`` with ``omega``-discharged side conditions;
``pos-keepcount-reassociated`` reassociates the exponent arm's keep-count into a
form ``omega`` cannot justify without first recovering ``idx < length`` from the
marker lookup. An earlier ``Id.run do`` → pure-``def`` reshape was dropped for
exactly this reason: it was defeq (``let mut``/``return`` under ``Id.run``
elaborates to the same term), so it probed nothing.

OMITTED nagini cases (legitimate, carrier-driven — NOT omitted for difficulty):

  * The six ``AXIOM_TESTS`` (axiom-soundness / axiom-containment probes over the
    grounded numeric theory) are DROPPED. This bundle axiomatizes nothing: the
    value's textual observations are grounded structure fields, so there is no
    ``opaque``/``axiom`` for the axiom lane to probe. The axiom lane is G-AX's
    responsibility; this gate ignores it. Reported, not silently skipped.

  * The frame/permission-mutation class is VACUOUS on a referentially
    transparent backend (see above); no substitute is fabricated.

  All six nagini SPEC_TESTS have faithful counterparts here: the hoist-decl
  positive control (re-expressed as TWO non-defeq correct reshapes — a
  complement-polarity guard and a reassociated keep-count; nagini's hoist itself
  is defeq on this carrier, since Lean has no statement order to permute), the
  gold-total admissibility positive (re-expressed as a ground F2P instance,
  since nagini's "frozen impl verifies" is the trivial case here), and the four
  uniqueness rivals (fixed-precision carrier, untrimmed echo, first-20
  truncation, keep-plus-one off-by-one). One rival has NO nagini ancestor and was
  added on this carrier: ``weak-skip-marker-normalization``, which nagini folded
  into its ``shortest_field`` axiom (``str(value).replace('e','E')`` is one
  callee there) and which is a separately attackable step here.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``simp only [...]`` + ``split``
tuned to the frozen ``if``/``match`` body) breaks on any reshape, wrong or right
— so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete, ``decide``-able input. Each was checked to (1) elaborate against
its rival and (2) FAIL on the frozen solution, so it discriminates rather than
asserting a tautology. Each witness unfolds ``problem_spec_formatFloat``,
``implementation_formatFloat``, ``truncate20`` and ``normE``, drives the
``Id.run do`` block through ``simp only [Id.run, bind, pure]``, then closes by
``decide`` on the concrete character lists.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14508"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each is a substring lying ENTIRELY inside the impl (or, for
# re-proving cases, the proof) region, and unique in Solution.lean.
# ---------------------------------------------------------------------------

# The whole frozen impl body (unique — the `Id.run do` shape appears once).
_IMPL_FULL = (
    "def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do\n"
    "  let mut valueStr := normE inp.reprStr\n"
    "  let strLen := valueStr.length\n"
    "  if strLen > 20 then\n"
    "    match valueStr.findIdx? (· = 'E') with\n"
    "    | none     => valueStr := valueStr.take 20\n"
    "    | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx\n"
    "  return valueStr\n"
)

# The single impl line selecting the textual carrier (the `let mut` binding is
# unique to the impl; the spec's own `normE inp.reprStr` is a different line and
# is NOT touched).
_I_CARRIER = "  let mut valueStr := normE inp.reprStr\n"

# The with-exponent shortening line, in its impl ASSIGNMENT form (`valueStr :=`),
# which is unique to the impl — truncate20's pure copy has no assignment.
_I_SCI = (
    "    | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx\n"
)

# The frozen proof body tail (unique — appears once, in the proof region).
_P_TAIL = (
    "  simp only [Id.run, bind, pure]\n"
    "  split\n"
    "  · split <;> rfl\n"
    "  · rfl\n"
)

# The intro line of the frozen proof (unique — the only `intro inp` in the file).
_P_INTRO = "  intro inp\n"


# ---- reject-witness builder ------------------------------------------------
# Pins the spec predicate at one concrete input, drives the loop to a concrete
# character list, and decides the disequality. The INPUT POINT is a parameter;
# each reject case picks the point that isolates its own rival (BINDER
# VARIATION in the module docstring).
def _witness(repr_lit, fixed_lit):
    return (
        "example : ¬ problem_spec_formatFloat\n"
        f"    {{ reprStr := {repr_lit}, fixedStr := {fixed_lit} }}\n"
        "    (implementation_formatFloat\n"
        f"      {{ reprStr := {repr_lit}, fixedStr := {fixed_lit} }}) := by\n"
        "  unfold problem_spec_formatFloat implementation_formatFloat truncate20 normE\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


# ===========================================================================
# (1) POSITIVE CONTROL (soundness) — CORRECT impl that is NOT definitionally
#     equal to the frozen one: the guard is written on the COMPLEMENT (`≤ 20`)
#     with the two arms SWAPPED, so the `if` scrutinee is a different decidable
#     proposition and the branches sit on the other side of it. `rfl` does NOT
#     close this (the two `if`s are not defeq — the kernel cannot identify
#     `decide (len ≤ 20)` with `decide (20 < len)`), so the obligation is
#     genuinely RE-PROVEN: each branch is reached by `by_cases` and the frozen
#     `if` is rewritten by `if_pos`/`if_neg` with the guard discharged by
#     `omega`. Statement byte-identical, no new declaration/axiom/sorry.
#     MUST verify (else SPEC-TOO-STRONG: the postcondition would be over-fit to
#     the frozen guard's polarity rather than to the rendered value).
#
#     AUDIT NOTE — this replaces an earlier `Id.run do` → pure-functional `def`
#     reshape. That reshape verified, but it was DEFINITIONALLY EQUAL to the
#     frozen impl (`let mut`/`return` inside `Id.run` elaborates to exactly the
#     `let`/`if`/`match` term), so it exercised nothing: bare `rfl` closes the
#     frozen obligation too, and the reshape's only complaint under the frozen
#     script was `No goals to be solved` — an over-long script, not a re-proof.
# ===========================================================================
_COMPL_IMPL = (
    "def implementation_formatFloat (inp : FmtInput) : List Char :=\n"
    "  let s := normE inp.reprStr\n"
    "  if s.length ≤ 20 then s\n"
    "  else\n"
    "    match s.findIdx? (· = 'E') with\n"
    "    | none     => s.take 20\n"
    "    | some idx => s.take (20 - (s.length - idx)) ++ s.drop idx\n"
)
_pos_complement = _swap(
    _swap(_BASE, _IMPL_FULL, _COMPL_IMPL), _P_TAIL,
    "  by_cases h : (normE inp.reprStr).length ≤ 20\n"
    "  · rw [if_pos h, if_neg (by omega)]\n"
    "  · rw [if_neg h, if_pos (by omega)]\n",
)


# ===========================================================================
# (1b) POSITIVE CONTROL (soundness) — CORRECT impl whose exponent-arm keep-count
#      is written as `idx - (strLen - 20)` instead of `20 - (strLen - idx)`.
#      On `Nat` these agree for every input the arm is REACHED at, but they are
#      not defeq and the identity is not even true unconditionally on truncated
#      subtraction: `omega` alone cannot prove it (checked — it reports the
#      counterexample `idx - (L-20) ≥ 21`, which needs `idx ≤ L` ruled in). So
#      the proof must EARN it: recover `idx < (normE inp.reprStr).length` from
#      `List.findIdx?_eq_some_iff_getElem` on the match hypothesis, then close by
#      `omega`. This is the strongest soundness probe in the battery — a real
#      mathematical re-derivation, not a re-spelling. MUST verify.
# ===========================================================================
_pos_keepform = _swap(
    _swap(_BASE, _I_SCI,
          "    | some idx => valueStr := valueStr.take (idx - (strLen - 20)) "
          "++ valueStr.drop idx\n"),
    _P_TAIL,
    "  simp only [Id.run, bind, pure]\n"
    "  split\n"
    "  · rename_i h\n"
    "    split\n"
    "    · rfl\n"
    "    · rename_i idx heq\n"
    "      have hlt : idx < (normE inp.reprStr).length := by\n"
    "        rw [List.findIdx?_eq_some_iff_getElem] at heq\n"
    "        obtain ⟨hi, _⟩ := heq\n"
    "        exact hi\n"
    "      congr 2\n"
    "      omega\n"
    "  · rfl\n",
)


# ===========================================================================
# (2) ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
#     F2P-shaped input. The theorem binds no precondition on `inp` (the float
#     input carries none), so the honest analogue of nagini's precondition
#     admission probe is to discharge the spec predicate at a ground F2P input
#     (reprStr "0.009125") by evaluation, INSIDE the proof body, alongside the
#     frozen obligation. Nothing is assumed: no new declaration, byte-identical
#     statement, the ground instance is a `have` in the existing tactic body.
#     MUST verify (else the spec is unsatisfiable at the F2P input — the
#     analogue of PRECOND-TOO-STRONG).
# ===========================================================================
_admiss = _swap(
    _BASE, _P_INTRO,
    _P_INTRO
    + '  have _ground : problem_spec_formatFloat\n'
      '      { reprStr := "0.009125".toList, fixedStr := [] }\n'
      '      (implementation_formatFloat { reprStr := "0.009125".toList, fixedStr := [] }) := by\n'
      "    unfold problem_spec_formatFloat implementation_formatFloat truncate20\n"
      "    simp only [Id.run, bind, pure]\n"
      "    decide\n",
)


# ===========================================================================
# (3) UNIQUENESS — fixed-precision carrier (the pre-fix behavior).
#     Feed the FIXED-PRECISION textual form to the rule instead of the shortest
#     form. This is the headline regression: a value whose shortest form already
#     fits is needlessly expanded. MUST reject.
# ===========================================================================
_weak_fixed = _swap(_BASE, _I_CARRIER, "  let mut valueStr := normE inp.fixedStr\n")


# ===========================================================================
# (4) UNIQUENESS — untrimmed echo (the length bound).
#     Return the textual form without ever shortening it. For inputs whose form
#     exceeds 20 characters this violates the bound the rule enforces. MUST
#     reject.
# ===========================================================================
_weak_echo = _swap(
    _BASE, _IMPL_FULL,
    "def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do\n"
    "  let mut valueStr := normE inp.reprStr\n"
    "  return valueStr\n",
)


# ===========================================================================
# (5) UNIQUENESS — unconditional first-20 truncation (drops the exponent).
#     Shorten every over-cap string to its first 20 characters, ignoring the
#     exponent marker. Correct on the no-exponent sub-domain, but for a string
#     WITH an exponent the rule requires the suffix be preserved, so the
#     exponent is lost. MUST reject. Partial-domain (scientific over-cap).
# ===========================================================================
_weak_trunc = _swap(
    _BASE, _IMPL_FULL,
    "def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do\n"
    "  let mut valueStr := normE inp.reprStr\n"
    "  let strLen := valueStr.length\n"
    "  if strLen > 20 then\n"
    "    valueStr := valueStr.take 20\n"
    "  return valueStr\n",
)


# ===========================================================================
# (6) UNIQUENESS — off-by-one keep in the exponent arm.
#     Keep one extra significand character before the preserved suffix
#     (20 - (len - idx) becomes 21 - (len - idx)), yielding a 21-character
#     result whose leading significand is one character too long. Breaks both
#     the length bound and the content of the exponent-preserving arm. MUST
#     reject. Partial-domain (scientific over-cap).
# ===========================================================================
_weak_offbyone = _swap(
    _BASE, _I_SCI,
    "    | some idx => valueStr := valueStr.take (21 - (strLen - idx)) ++ valueStr.drop idx\n",
)


# ===========================================================================
# (7) UNIQUENESS — the exponent-marker clause is skipped entirely.
#     Feed the shortest form to the rule WITHOUT upper-casing the exponent
#     marker (drop `normE`). Every other rival leaves `normE` in place, so
#     before this case the marker-normalization half of the obligation was
#     unprobed: no reject case moved a lower-case `e`, and the four witness
#     points contain no lower-case `e` at all (three have no exponent, the
#     fourth already spells it `E`). Observably different from the frozen impl:
#     at `reprStr = "1.5e10"` the frozen rule renders `1.5E10` and this one
#     renders `1.5e10`. Also breaks the shortening rule indirectly, since a
#     lower-case marker is invisible to the `findIdx? (· = 'E')` lookup. MUST
#     reject. Witness point carries the lower-case marker, which is exactly the
#     binder variation the other four cases do not reach.
# ===========================================================================
_weak_nonorm = _swap(_BASE, _I_CARRIER, "  let mut valueStr := inp.reprStr\n")


SPEC_TESTS = [
    {
        "id": "pos-complement-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_complement,
        "rationale": (
            "a CORRECT implementation that is NOT definitionally equal to the "
            "frozen one: the guard is written on the complement (`s.length ≤ 20`) "
            "with the arms swapped, so the `if` scrutinee is a different decidable "
            "proposition. `rfl` does not close it (checked: `Tactic `rfl` failed`), "
            "so the obligation is genuinely re-proven — `by_cases` on the "
            "complement, then `if_pos`/`if_neg` on the frozen guard with `omega` "
            "discharging the polarity. Must verify, else the postcondition is "
            "over-fit to the frozen guard's polarity rather than to the rendered "
            "value (SPEC-TOO-STRONG). Statement byte-identical, no new "
            "declaration/axiom/sorry."),
    },
    {
        "id": "pos-keepcount-reassociated",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_keepform,
        "rationale": (
            "a CORRECT implementation whose exponent-arm keep-count is written "
            "`idx - (strLen - 20)` rather than `20 - (strLen - idx)`. The two "
            "agree wherever the arm is reached, but not definitionally and not "
            "unconditionally on truncated `Nat` subtraction — `omega` alone "
            "REFUSES the identity (checked). So the proof must earn it: recover "
            "`idx < (normE inp.reprStr).length` from the match hypothesis via "
            "`List.findIdx?_eq_some_iff_getElem`, then close by `omega`. The "
            "strongest soundness probe here: a re-derivation, not a re-spelling. "
            "Must verify, else the spec rejects a faithful reassociation of its "
            "own arithmetic (SPEC-TOO-STRONG)."),
    },
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "the obligation is discharged at a ground F2P input (reprStr "
            "\"0.009125\", the fits branch) by evaluation, then the frozen "
            "obligation is closed verbatim. Verifies (else the modeled behavior is "
            "unsatisfiable at the F2P input, the analogue of PRECOND-TOO-STRONG). "
            "The float input carries no precondition, so this ground `have` is the "
            "honest admissibility witness; nothing is assumed — no new declaration, "
            "byte-identical statement, the instance is a `have` inside the existing "
            "tactic body."),
    },
    {
        "id": "weak-fixed-precision-carrier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_fixed,
        "refinement": (
            "feeding the fixed-precision form to the rule is exactly the pre-fix "
            "behavior: a value whose shortest form already fits (\"0.009125\", 8 "
            "chars) is needlessly expanded to its fixed-precision form "
            "(\"0.009124999999999999\", 20 chars), which overflows the budget and "
            "forces the trailing comment to be truncated. This is the regression "
            "the F2P case forbids — a faithful patch that kept the fixed-precision "
            "carrier would NOT resolve; it is the leg's prepatch."),
        "rationale": (
            "REJECT from `result = truncate20 (normE inp.reprStr)`: the rule is "
            "pinned to `reprStr`, so substituting `fixedStr` produces a different "
            "string whenever the two forms diverge. If it verified => SPEC-TOO-WEAK "
            "(the shortest-form-vs-expanded-form discriminator would be missing). "
            "This is the only rival that touches `fixedStr`; it is caught precisely "
            "because it uses `fixedStr` where `reprStr` was required."),
        "witness": _witness('"0.009125".toList', '"0.009124999999999999".toList'),
    },
    {
        "id": "weak-echo-untrimmed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_echo,
        "refinement": (
            "returning the textual form without shortening emits a field longer "
            "than 20 characters for any over-long value; the FITS value field "
            "cannot hold it — the 20-character cap is the whole reason the rule "
            "shortens — so a faithful patch that skipped the shortening would NOT "
            "resolve the over-cap value/complex-card cases."),
        "rationale": (
            "REJECT from `result = truncate20 (normE inp.reprStr)`: for an over-cap "
            "input `truncate20` shortens to 20 characters, so echoing the untrimmed "
            "form (22 chars here) violates the equality. Cheap supporting "
            "length-bound case; refuted on the no-exponent over-cap sub-domain."),
        "witness": _witness('"12345678901234567890.5".toList', "[]"),
    },
    {
        "id": "weak-trunc-first20",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_trunc,
        "refinement": (
            "unconditionally keeping the first 20 characters of a scientific value "
            "such as \"1.23456789012345E+300\" drops the exponent suffix entirely, "
            "yielding a different number; a faithful patch that shortened this way "
            "would mis-render the scientific over-cap value and would NOT resolve "
            "those cases."),
        "rationale": (
            "REJECT from `result = truncate20 (normE inp.reprStr)`: for an over-cap "
            "input WITH an exponent marker the rule keeps the exponent suffix and "
            "truncates the significand, but the unconditional first-20 copy keeps "
            "the first 20 characters and loses the suffix. Correct on the "
            "no-exponent sub-domain, so a genuine partial-domain break. If it "
            "verified => SPEC-TOO-WEAK on the exponent-preserving arm."),
        "witness": _witness('"1.23456789012345E+300".toList', "[]"),
    },
    {
        "id": "weak-offbyone-keep-plus1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_offbyone,
        "refinement": (
            "keeping one extra significand character in the exponent arm "
            "(21 - (len - idx) instead of 20 - (len - idx)) emits a 21-character "
            "field with an extra mantissa digit that overflows the 20-character "
            "value field; a faithful patch with this off-by-one would mis-render "
            "the scientific over-cap value and would NOT resolve those cases."),
        "rationale": (
            "REJECT from `result = truncate20 (normE inp.reprStr)`: the exponent "
            "arm must take `20 - (len - idx)` significand characters; taking "
            "`21 - (len - idx)` yields a 21-character result whose content differs "
            "from the rule's. Breaks both the length bound and the arm's content. "
            "Partial-domain (scientific over-cap); a near-miss of the first-20 "
            "truncation rival that keeps an exponent but shortens it wrongly."),
        "witness": _witness('"1.23456789012345E+300".toList', "[]"),
    },
    {
        "id": "weak-skip-marker-normalization",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_nonorm,
        "refinement": (
            "feeding the shortest form to the rule without upper-casing the "
            "exponent marker emits a value whose marker is lower-case, so the "
            "rendered field differs from the required one for every value whose "
            "shortest form uses a lower-case exponent (\"1.5e10\" renders as "
            "\"1.5e10\", not \"1.5E10\"). It also silently disables the shortening "
            "rule's exponent arm, since a lower-case marker is invisible to the "
            "marker lookup — an over-cap scientific value would then be cut by the "
            "no-exponent rule and lose its exponent. A faithful patch that skipped "
            "the marker normalization would mis-render those values."),
        "rationale": (
            "REJECT from `result = truncate20 (normE inp.reprStr)`: the `normE` "
            "application is part of the obligation, so omitting it differs "
            "observably wherever the shortest form carries a lower-case marker. "
            "This case exists because the other four rivals all leave `normE` in "
            "place and none of their witness points contains a lower-case `e` at "
            "all, leaving the marker-normalization half of the obligation "
            "unprobed; if it verified => SPEC-TOO-WEAK on that clause. Witness "
            "point `\"1.5e10\"` is the binder variation the other cases do not "
            "reach."),
        "witness": _witness('"1.5e10".toList', "[]"),
    },
]
