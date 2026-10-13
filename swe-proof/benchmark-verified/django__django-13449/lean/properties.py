"""properties.py — PBT falsification manifest for django__django-13449 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is byte-identical, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition rather than to a tampered spec. No case adds an
axiom, a lemma, a `sorry`/`admit`, or `native_decide`, and every
`theorem correct_renderWindowSql` statement is preserved verbatim.

DEFENDED SURFACE
----------------
One obligation, over three input binders:

    implementation_renderWindowSql (operand window : List Char) (isDecimal : Bool)
        : List Char

pinned by a single load-bearing clause, a flag-selected equality:

    result = if isDecimal then "CAST(" ++ windowedExpr operand window
                               ++ " AS NUMERIC)"
                          else windowedExpr operand window
    windowedExpr operand window = operand ++ " OVER (" ++ window ++ ")"

The clause is FULLY TRANSPARENT — `windowedExpr` is a concrete fixed-order
concatenation and the cast wrapper is a concrete literal-driven concatenation, so
there is no `opaque` callee anywhere in the carrier and no oracle a rival could
echo. Every rival is therefore refutable by `decide` at a concrete input; the
carrier-conditioning route (quantify over an opaque term and separate rival from
gold by hypothesis) is not needed here.

Unfolded, the clause pins FIVE independent things, and the reject lane attacks
each of them:

  1. WHAT the numeric cast spans on the flag-set branch — the whole windowed unit
     (operand together with its trailing clause) as one span, not the leading
     operand text alone. This is the discriminating content of the behavior
     change and the F2P-tied property.
  2. That the cast appears ONLY on the flag-set branch (no cast when the flag is
     clear).
  3. That the cast appears on the flag-set branch AT ALL (it is not optional),
     and that it is a function of the FLAG ALONE — not additionally conditioned
     on the window text (attacked at the empty window clause by
     `cast-skips-empty-window`) NOR on the operand text (attacked at a short
     operand by `cast-gated-on-operand`). Both halves of that claim are
     demonstrated by a rival rather than asserted here.
  4. That the operand text inside the cast carries no cast of its own — the
     wrapper is applied exactly once, not nested — and that the wrapper's own
     literals are spelled verbatim (`cast-literal-unterminated`), a defect
     distinct from misplacing a correctly-spelled wrapper.
  5. The unchanged structural components and their fixed order: the leading
     operand text, the ` OVER (` keyword run, the window-clause text, and the
     closing parenthesis. All FOUR slots are attacked individually
     (`drop-operand`, `drop-over-keyword`, `drop-window`, `drop-close-paren`).

Because Lean is referentially transparent, the frame obligation is discharged
STRUCTURALLY by (5): the equality names each unchanged component explicitly, so a
rival that drops or misplaces one is refuted without any notion of aliasing.

PORTING NOTES — which nagini cases ported, which did not
--------------------------------------------------------
Source of the adversarial reasoning: the nagini sibling's `SPEC_TESTS`. Case
count is deliberately NOT matched: nagini contracts a four-argument surface whose
fourth input (the operand's OWN declared type) is outside this bundle's carrier,
so the cases attached to it have no counterpart here.

Ported, argument carried over, mechanics rewritten for this carrier:

  * `uniq-cast-around-operand`   -> `cast-inside-over`     (the pre-gold shape)
  * `uniq-no-cast-decimal`       -> `no-outer-cast`
  * `uniq-always-cast`           -> `always-cast`
  * `uniq-swap-branches`         -> `inverted-flag`
  * `uniq-operand-decimal-double-cast` -> `double-cast`
  * `uniq-drop-over-keyword`     -> `drop-over-keyword`
  * `pos-control-branch-reorder` -> `pos-branch-reorder`   (proof re-closed)
  * `pos-control-inner-concat`   -> `pos-slot-assembly`    (proof re-closed)
  * `admiss-f2p-shaped-input`    -> `admiss-f2p-ground`    (re-expressed; see
    the reversal note below — an earlier revision dropped this lane in error)

Added at audit, with no nagini counterpart — each closes a gap the ported lane
left open, and each was built and SEEN to discriminate before being shipped:

  * `drop-close-paren` — the fourth structural slot of pinned fact (5). The port
    claimed the reject lane attacked the closing parenthesis and no rival did:
    the three structural rivals took the keyword run and the two text binders,
    leaving the terminator the one named component nothing probed.
  * `cast-skips-empty-window` — the tightest near-miss, and the only reject case
    at which a binder is EMPTY. Every ported rival is wrong on a broad set of
    inputs, so a defect confined to the carrier's boundary value was unprobed.
  * `cast-gated-on-operand` — the OPERAND half of pinned fact (3). The docstring
    claimed the wrapper was pinned to the flag alone and not conditioned on
    either text binder, but only the window half had a rival; a rendering that
    consulted the operand text was unprobed. Its witness is also the only
    reject-lane point with a SHORT operand text.
  * `cast-literal-unterminated` — the byte content of the wrapper's own literals.
    Every other rival either moves a correctly-spelled wrapper or removes it, so
    a wrapper emitted in the right place with the wrong text was unprobed.

Omitted, with reasons:

  * `uniq-nondecimal-ignore-operand-cast` — NO COUNTERPART ON THIS CARRIER. It
    attacks nagini's second postcondition arm, where the operand is re-rendered
    according to its OWN declared type, so stripping that inner rendering is
    observable. This bundle's carrier takes `operand` to be the already-rendered
    bare operand text (mapping.md, "Scope note"): there is no fourth binder to
    mishandle, and the rival's edit collapses to the identity on `operand`. It is
    not that the rival is hard to refute — it is not WRONG here, so no witness
    could discriminate it, and shipping it would claim a sub-domain this carrier
    does not distinguish. DEMONSTRATED at audit rather than argued: the rival's
    edit (emit the operand verbatim on the flag-clear branch) was written out as
    a full variant and VERIFIES against the frozen spec (exit 0), closing by the
    frozen `cases isDecimal <;> rfl` — i.e. it is definitionally the frozen impl
    on this carrier, so as an `expect="reject"` case it would be vacuous and as
    an `expect="verify"` case it is a duplicate of the frozen impl.
  * `frame-mut-operand-append`, `frame-mut-window-append` — VACUOUS CLASS. Both
    probe a write through a half-permission reference; Lean is referentially
    transparent, with no aliasing and no fractional permissions, so the rival
    cannot even be written. Their INTENT (the two read-only inputs must be
    reproduced verbatim in the result) is carried over structurally instead, by
    `drop-operand` and `drop-window`, which attack those two binders directly.
  * `AXIOM_TESTS` — dropped by design; the axiom lane is G-AX's job and this gate
    ignores it. (This bundle's axioms region is empty in any case.)

PORTED at a later audit, reversing an earlier wrong disposition:

  * `admiss-f2p-shaped-input` -> `admiss-f2p-ground` (see the admissibility case
    below). An earlier revision of this manifest recorded the lane as a VACUOUS
    CLASS on the reasoning that the frozen obligation carries NO precondition
    hypothesis, so there is no `Requires` to be too strong. That reasoning is
    wrong, and it is wrong in a way that silently removes one of the three
    directions this gate exists to test. On a TOTAL carrier the analogue of
    PRECOND-TOO-STRONG is not a rejected precondition — it is the obligation
    being UNSATISFIABLE at exactly an F2P-shaped input, which a `∀`-statement can
    perfectly well be while still being provable-looking, and which no soundness
    or uniqueness case detects: the positives vary the impl and the rivals vary
    the impl, but neither ever pins the spec to a concrete F2P-shaped point and
    asks whether a value satisfying it EXISTS there. The case below does exactly
    that, by evaluation, as a `have`, before closing the frozen obligation
    verbatim.

Divergence / non-termination: the nagini sibling carries NO `diverge-*` /
`nonterm-*` / `weak-diverge` case, so there is nothing to port. Independently,
the class is genuinely VACUOUS on this backend — `implementation_renderWindowSql`
is a total Lean `def`, so a non-terminating rival cannot be written at all. This
is the lean disposition, NOT the velvet one: under
`set_option loom.semantics.termination "partial"` a diverging impl satisfies every
clause vacuously and the spec ADMITS it (the corpus-wide termination-semantics finding, 401 of 500
velvet bundles). That known hole does not apply here.

WITNESSES
---------
Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input, checked in a file with the frozen obligation removed. Each
must (1) elaborate against the rival — the rival provably contradicts the spec —
and (2) FAIL against the frozen solution, so it is a real discriminator and not a
tautology. All TWELVE were built both ways with scripts/lean_verify.sh and were
SEEN to discriminate (rival exit 0, frozen exit 1), and on the frozen side each
failure is `decide` PROVING the negation false — a semantic refutation of the
concrete claim, not a missing identifier, a type error or a stuck reduction.

Each was additionally subjected to the FORGERY check, which is what establishes
that the frozen side's exit code carried information about the CLAIM rather than
about the file: the same witness with its negation DROPPED — i.e. asserting the
spec HOLDS at that point — was built on both sides, and it elaborates against the
frozen solution (exit 0) while failing against the rival (exit 1), the exact
mirror of the witness itself. So each error tracks what is being claimed, and no
case's rejection rests on an error that would have appeared regardless.

The twelve witnesses probe TWELVE DISTINCT input points, and every one of the
three binders is varied across them: `isDecimal` takes both values, `operand`
takes twelve distinct texts spanning both long and SHORT, and `window` takes
eleven distinct texts plus the EMPTY clause. Nothing is held fixed, so a rival
that mishandled only one input at one value cannot slip through unnoticed.

Eleven window-clause texts are written as single space-free tokens. Nothing in the
carrier cares (`window` is an arbitrary `List Char`, threaded through unchanged),
and it keeps each witness's argument list machine-readable so the per-binder audit
in scripts/pbt_coverage.py can SEE those points rather than take this paragraph's
word for it — an embedded space makes the splitter read one argument as three and
report the battery's probe points as unmeasurable. The tenth
(`cast-skips-empty-window`) passes the empty list directly, since no string
literal spells it; that is the one point the splitter cannot tokenize, and it is
deliberate — it is the carrier boundary the literal-text witnesses cannot reach.
"""
from pathlib import Path

INSTANCE = "django__django-13449"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence, asserting it matched, so silent drift in
    the frozen Solution.lean breaks this manifest loudly instead of quietly
    producing a variant that edits nothing."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. `_IMPL_BODY` lies entirely inside the impl region and
# `_PROOF_BODY` entirely inside the proof region; both are unique in the file.
# ---------------------------------------------------------------------------

_IMPL_BODY = (
    "  -- Render the windowed expression first, as a single text unit.\n"
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  -- On a fixed-point decimal output type, wrap that whole unit in the numeric cast.\n"
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

_PROOF_BODY = (
    "  intro operand window isDecimal\n"
    "  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr\n"
    "  cases isDecimal <;> rfl"
)

assert _BASE.count(_IMPL_BODY) == 1
assert _BASE.count(_PROOF_BODY) == 1


def _impl(body, proof=None):
    """A full variant: `body` replaces the impl body, `proof` (when given) the
    tactic body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_BODY, body)
    if proof is not None:
        out = _swap(out, _PROOF_BODY, proof)
    return out


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify".
# Structurally DIFFERENT but CORRECT impls. Each reproves the identical
# obligation honestly inside the proof region; if one cannot verify, the spec is
# over-fit to the frozen impl's syntactic form => SPEC-TOO-STRONG.
# ===========================================================================

# (pos-branch-reorder) Handle the flag-CLEAR case first and return early, so the
# wrapping step is reached only by fall-through. Inverts the branch order of the
# frozen impl (the nagini `pos-control-branch-reorder` argument) while computing
# the same text on every input. Proof re-closed by the same case split.
_POS_BRANCH_REORDER = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  if !isDecimal then\n"
    "    return sql\n"
    '  sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql",
    "  intro operand window isDecimal\n"
    "  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr\n"
    "  cases isDecimal <;> rfl",
)

# (pos-slot-assembly) A different assembly shape, the analogue of nagini's
# `pos-control-inner-concat`: instead of building the windowed unit and then
# re-wrapping it, carry the wrapper's opening and closing literals in two
# flag-dependent slots and emit everything in one concatenation. The bracketing
# of the appends therefore differs from the frozen impl, so `rfl` alone no longer
# closes and the proof is re-discharged via associativity of concatenation. Same
# text on every input; if it fails to verify the spec is over-fit to one
# bracketing => SPEC-TOO-STRONG.
_POS_SLOT_ASSEMBLY = _impl(
    "  let mut castOpen : List Char := []\n"
    "  let mut castClose : List Char := []\n"
    "  if isDecimal then\n"
    '    castOpen := "CAST(".toList\n'
    '    castClose := " AS NUMERIC)".toList\n'
    '  return castOpen ++ operand ++ " OVER (".toList ++ window ++ [\')\'] ++ castClose',
    "  intro operand window isDecimal\n"
    "  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr\n"
    "  cases isDecimal <;> simp [List.append_assoc]",
)


# ===========================================================================
# ADMISSIBILITY (satisfiability at an F2P-shaped input) — expect "verify".
# The impl is the FROZEN one; the only edit is inside the proof region, where a
# ground `have` discharges the obligation at one concrete F2P-shaped point BY
# EVALUATION before the frozen tactic script closes the general statement
# verbatim. If the modeled behavior were unsatisfiable at exactly that input,
# this `have` would not elaborate — the total-carrier analogue of
# PRECOND-TOO-STRONG. Nothing is assumed: no new declaration, no lemma, and the
# theorem statement is byte-identical.
# ===========================================================================

_ADMISS_F2P_GROUND = _impl(
    _IMPL_BODY,
    '  have _ground : problem_spec_renderWindowSql\n'
    '      "LAG(amount,7)".toList "partitionByDeptOrderByHire".toList true\n'
    "      (implementation_renderWindowSql\n"
    '        "LAG(amount,7)".toList "partitionByDeptOrderByHire".toList true) := by\n'
    "    unfold problem_spec_renderWindowSql implementation_renderWindowSql"
    " windowedExpr\n"
    "    decide\n"
    "  intro operand window isDecimal\n"
    "  unfold problem_spec_renderWindowSql implementation_renderWindowSql windowedExpr\n"
    "  cases isDecimal <;> rfl",
)


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject". Each shares the spec exactly, changes only
# the impl region, and carries a witness seen to discriminate.
# ===========================================================================

# (cast-inside-over) THE discriminating defect, and the pre-gold shape: the
# numeric cast is applied to the leading operand text ALONE, so the ` OVER (…)`
# clause is appended OUTSIDE the cast. Attacks pinned fact (1).
_RIVAL_CAST_INSIDE = _impl(
    "  let mut inner : List Char := operand\n"
    "  if isDecimal then\n"
    '    inner := "CAST(".toList ++ operand ++ " AS NUMERIC)".toList\n'
    '  return inner ++ " OVER (".toList ++ window ++ [\')\']'
)

# (no-outer-cast) Never emit the numeric cast at all: return the bare windowed
# unit on both flag values. Attacks pinned fact (3).
_RIVAL_NO_CAST = _impl(
    '  let sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  return sql"
)

# (always-cast) Emit the numeric cast unconditionally, ignoring the flag. The
# flag-set branch is correct; the flag-clear branch gets a spurious wrapper.
# Attacks pinned fact (2).
_RIVAL_ALWAYS_CAST = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    '  sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (inverted-flag) The flag test is negated: the wrapper lands on exactly the
# inputs that must not have it and is missing from the ones that must. Attacks
# pinned facts (2) and (3) simultaneously, on both halves of the flag domain.
_RIVAL_INVERTED_FLAG = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  if !isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (double-cast) Wrap the whole windowed unit correctly, but ALSO leave a wrapper
# around the operand text inside it — the cast applied twice, nested. Attacks
# pinned fact (4).
_RIVAL_DOUBLE_CAST = _impl(
    "  let mut inner : List Char := operand\n"
    "  if isDecimal then\n"
    '    inner := "CAST(".toList ++ operand ++ " AS NUMERIC)".toList\n'
    '  let mut sql : List Char := inner ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (drop-over-keyword) Omit the ` OVER (` keyword run, concatenating the operand
# text straight onto the window-clause text. Attacks pinned fact (5) at the
# keyword slot; the wrapper logic itself is left correct.
_RIVAL_DROP_OVER = _impl(
    "  let mut sql : List Char := operand ++ window ++ [\')\']\n"
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (drop-operand) Drop the leading operand text entirely. Attacks the `operand`
# binder — the read-only input nagini probed with a permission write. Wrong on
# every input with non-empty operand text, on either flag value.
_RIVAL_DROP_OPERAND = _impl(
    '  let mut sql : List Char := " OVER (".toList ++ window ++ [\')\']\n'
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (drop-window) Drop the window-clause text entirely. Attacks the `window`
# binder — the other read-only input nagini probed with a permission write.
_RIVAL_DROP_WINDOW = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ [\')\']\n'
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (drop-close-paren) Omit the closing parenthesis that terminates the window
# clause, so the clause is left unterminated. Attacks pinned fact (5) at the
# FOURTH structural slot — the one the other three structural rivals leave
# untouched (`drop-over-keyword` attacks the keyword run, `drop-operand` and
# `drop-window` the two text binders). The wrapper logic is left correct, so the
# rejection is attributable to that slot alone.
_RIVAL_DROP_CLOSE_PAREN = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window\n'
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (cast-skips-empty-window) The TIGHTEST near-miss in the battery: the wrapper
# spans the whole windowed unit, on the right branch, with every structural
# component in place — but it is additionally gated on the window-clause text
# being non-empty. Agrees with the frozen impl on EVERY input except the empty
# window clause, where the flag-set branch still requires the wrapper. Attacks
# pinned fact (3) at the carrier's boundary value, which the other rivals all
# miss: each of them is wrong at texts a witness happens to pick, so a defect
# confined to the empty carrier would otherwise go unprobed.
_RIVAL_CAST_SKIPS_EMPTY_WINDOW = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  if isDecimal && !window.isEmpty then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (cast-gated-on-operand) The OTHER half of pinned fact (3): the wrapper is
# additionally conditioned on the OPERAND text rather than on the window text —
# emitted only when the operand text is longer than a short threshold. Correct on
# every long operand, so it agrees with the frozen impl over most of the domain
# and is wrong only on short ones. Pinned fact (3) claims the wrapper is a
# function of the FLAG ALONE, "not additionally conditioned on the operand or
# window text"; `cast-skips-empty-window` demonstrates the window half, and this
# case is what demonstrates the operand half rather than leaving it asserted.
_RIVAL_CAST_GATED_ON_OPERAND = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  if isDecimal && operand.length > 3 then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC)".toList\n'
    "  return sql"
)

# (cast-literal-unterminated) The wrapper is emitted on the right branch, spans
# the right text, and is applied exactly once — but its own TRAILING literal is
# spelled without the terminator that closes the cast. Attacks the byte content
# of the wrapper literals themselves, which every other rival leaves spelled
# correctly: the placement rivals move a correctly-spelled wrapper, and
# `no-outer-cast` removes it altogether. Distinct from `drop-close-paren`, which
# drops the parenthesis terminating the WINDOW clause (a different slot, inside
# the cast rather than closing it).
_RIVAL_CAST_LITERAL_UNTERMINATED = _impl(
    '  let mut sql : List Char := operand ++ " OVER (".toList ++ window ++ [\')\']\n'
    "  if isDecimal then\n"
    '    sql := "CAST(".toList ++ sql ++ " AS NUMERIC".toList\n'
    "  return sql"
)


# ---------------------------------------------------------------------------
# Witnesses. The carrier is fully transparent, so each states the negation of
# the spec predicate at one concrete input and closes by `decide`. Eight
# DISTINCT points; both flag values and eight distinct operand / window texts,
# so no binder is held fixed across the reject lane.
# ---------------------------------------------------------------------------

def _wit(operand, window, flag):
    return (
        f'example : ¬ problem_spec_renderWindowSql "{operand}".toList'
        f' "{window}".toList {flag}\n'
        f'    (implementation_renderWindowSql "{operand}".toList'
        f' "{window}".toList {flag}) := by\n'
        "  unfold problem_spec_renderWindowSql implementation_renderWindowSql"
        " windowedExpr\n"
        "  decide"
    )


_WIT_CAST_INSIDE = _wit("LAG(a)", "partitionByDept", "true")
_WIT_NO_CAST = _wit("SUM(b)", "orderByHire", "true")
_WIT_ALWAYS_CAST = _wit("AVG(c)", "orderByAge", "false")
_WIT_INVERTED_FLAG = _wit("MIN(g)", "partitionByTeam", "false")
_WIT_DOUBLE_CAST = _wit("MAX(i)", "orderByName", "true")
_WIT_DROP_OVER = _wit("RANK()", "partitionByRegion", "false")
_WIT_DROP_OPERAND = _wit("LEAD(l)", "orderBySalary", "false")
_WIT_DROP_WINDOW = _wit("NTILE(4)", "partitionByGrade", "true")
_WIT_DROP_CLOSE_PAREN = _wit("COUNT(z)", "orderByTenure", "true")
# A SHORT operand text, which is the sub-domain `cast-gated-on-operand` gets
# wrong; every other reject-lane point uses a long operand, so this is the point
# that rival needs and no shipped witness previously reached.
_WIT_CAST_GATED_ON_OPERAND = _wit("AB", "orderByCode", "true")
_WIT_CAST_LITERAL_UNTERMINATED = _wit("MIN(s)", "orderByStart", "true")


# The empty window clause is a carrier value no string literal spells, so this
# witness passes the list directly rather than through `_wit`. It is the point
# `cast-skips-empty-window` needs and the only input in the reject lane at which
# a binder is EMPTY, so it also widens the lane past the eight non-empty texts.
_WIT_CAST_SKIPS_EMPTY_WINDOW = (
    'example : ¬ problem_spec_renderWindowSql "SUM(v)".toList [] true\n'
    '    (implementation_renderWindowSql "SUM(v)".toList [] true) := by\n'
    "  unfold problem_spec_renderWindowSql implementation_renderWindowSql"
    " windowedExpr\n"
    "  decide"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH_REORDER,
        "rationale": "structurally-different but CORRECT impl: the flag-CLEAR case is "
                     "handled first with an early return, so the wrapping step is reached "
                     "only by fall-through — the inverse branch order of the frozen impl. "
                     "The flag-selected equality is order-agnostic, so a correct impl in "
                     "either branch order must satisfy it; failure to verify would mean the "
                     "spec is over-fit to one branch order => SPEC-TOO-STRONG. The "
                     "obligation is reproven honestly (same case split, no lemma added, no "
                     "assumption introduced) with its statement byte-identical.",
    },
    {
        "id": "pos-slot-assembly",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SLOT_ASSEMBLY,
        "rationale": "a second CORRECT impl in a different assembly shape: the wrapper's "
                     "opening and closing literals are carried in two flag-dependent slots "
                     "and everything is emitted in ONE concatenation, so the appends are "
                     "bracketed differently from the frozen impl and reflexivity alone no "
                     "longer closes the goal. The obligation is re-discharged honestly via "
                     "associativity of concatenation (no new lemma, no assumption). Same "
                     "text on every input; failure to verify would mean the spec is over-fit "
                     "to one bracketing of the concatenation => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (satisfiability at an F2P-shaped input) ----
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_F2P_GROUND,
        "rationale": "the obligation is discharged at one concrete F2P-shaped input — a "
                     "lag-style operand text over a partition-and-order window clause, with "
                     "the fixed-point-decimal flag SET, i.e. the flag value on which the "
                     "whole discriminating behavior lives — by EVALUATION as a `have`, and "
                     "only then is the frozen general obligation closed verbatim by its own "
                     "tactic script. This is the total-carrier analogue of "
                     "PRECOND-TOO-STRONG: the frozen statement carries no precondition "
                     "hypothesis, so no `Requires` can be too strong, but the modeled "
                     "behavior could still be UNSATISFIABLE at exactly an F2P-shaped point, "
                     "and neither the soundness nor the uniqueness lane would notice — both "
                     "vary the impl, and neither ever pins the spec to a concrete point and "
                     "asks whether a satisfying value exists there. If the ground `have` "
                     "failed to elaborate, the spec would be admitting nothing at the one "
                     "input the F2P actually exercises. Nothing is assumed: no new "
                     "declaration, no lemma, no `sorry`; the impl region is the FROZEN one "
                     "and the theorem statement is byte-identical. Ports nagini's "
                     "`admiss-f2p-shaped-input`, whose lane an earlier revision of this "
                     "manifest wrongly recorded as vacuous.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "cast-inside-over",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CAST_INSIDE,
        "witness": _WIT_CAST_INSIDE,
        "refinement": "this is the pre-gold behavior the issue reports: the numeric wrapper "
                      "is applied to the leading operand text alone, leaving the windowing "
                      "clause dangling outside it. The faithful real patch is the UNPATCHED "
                      "rendering, which produces exactly the invalid statement whose "
                      "`near \"OVER\": syntax error` the F2P observes, so the F2P still "
                      "fails and it does NOT resolve. A verifying rival here would be a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "rejected by the flag-selected equality on its flag-set branch, which "
                     "pins the cast to span the WHOLE windowed unit "
                     "(\"CAST(\" ++ windowedExpr operand window ++ \" AS NUMERIC)\"); this "
                     "rival emits the wrapper around `operand` only and appends the keyword "
                     "run, window text and closing parenthesis after it — a different "
                     "sequence, with the closing literal in a different position. Witness at "
                     "(LAG(a), partitionByDept, isDecimal=true): seen to elaborate against "
                     "the rival and to FAIL against the frozen solution.",
    },
    {
        "id": "no-outer-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NO_CAST,
        "witness": _WIT_NO_CAST,
        "refinement": "never emitting the numeric wrapper corresponds to a rendering that "
                      "never takes the fixed-point-decimal branch at all. The value is then "
                      "compared and returned untyped, so the F2P's assertion on the windowed "
                      "decimal results fails; it does NOT resolve. It is also the shape the "
                      "issue's reporter already had.",
        "rationale": "rejected by the flag-set branch of the equality, which REQUIRES the "
                     "wrapper: the rival returns the bare windowed unit on every input, so "
                     "the leading \"CAST(\" and trailing \" AS NUMERIC)\" literals are "
                     "absent. Attacks the fact that the wrapper is emitted at all, as "
                     "opposed to where it is placed. Witness at (SUM(b), orderByHire, "
                     "isDecimal=true) — a DIFFERENT point from cast-inside-over, since this "
                     "rival is a strictly larger deviation and should not borrow that "
                     "rival's sub-domain claim. Seen to elaborate against the rival and to "
                     "FAIL against the frozen solution.",
    },
    {
        "id": "always-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ALWAYS_CAST,
        "witness": _WIT_ALWAYS_CAST,
        "refinement": "wrapping unconditionally corresponds to a rendering that dropped the "
                      "output-type guard. The flag-set inputs are then right but every "
                      "flag-clear input gets a spurious numeric wrapper, changing the "
                      "rendered statement and the result typing across the non-decimal "
                      "windowing suite, which is where the great majority of this "
                      "instance's PASS_TO_PASS tests live (42 of its 46 are in the "
                      "windowing test module, and none of them declares a fixed-point "
                      "decimal output). Those tests regress, so it does NOT resolve.",
        "rationale": "rejected by the flag-CLEAR branch of the equality, which pins the "
                     "result to the bare windowed unit with NO wrapper. This is the only "
                     "rival whose flag-set branch agrees with gold, so its witness must sit "
                     "on the flag-clear side: at (AVG(c), orderByAge, isDecimal=false). Seen "
                     "to elaborate against the rival and to FAIL against the frozen "
                     "solution.",
    },
    {
        "id": "inverted-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_INVERTED_FLAG,
        "witness": _WIT_INVERTED_FLAG,
        "refinement": "negating the output-type guard corresponds to a patch whose condition "
                      "is inverted: the fixed-point-decimal inputs render unwrapped (so the "
                      "F2P still fails) and the others acquire a spurious wrapper (so the "
                      "non-decimal windowing PASS_TO_PASS tests regress). Neither half of "
                      "the domain resolves.",
        "rationale": "rejected by BOTH branches of the flag-selected equality — the flag-set "
                     "branch demands the wrapper the rival withholds, and the flag-clear "
                     "branch demands its absence where the rival adds it. Witness taken on "
                     "the flag-CLEAR side at (MIN(g), partitionByTeam, isDecimal=false), a "
                     "distinct point from always-cast even though both are wrong there: "
                     "keeping them at separate inputs keeps each rationale's sub-domain "
                     "claim independently demonstrated. Seen to elaborate against the rival "
                     "and to FAIL against the frozen solution.",
    },
    {
        "id": "double-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DOUBLE_CAST,
        "witness": _WIT_DOUBLE_CAST,
        "refinement": "this is the NEAR MISS: the wrapper does span the whole windowed unit, "
                      "but the operand text inside it keeps a wrapper of its own — the fix "
                      "applied without first suppressing the inner one. The nested inner "
                      "`AS NUMERIC)` still sits immediately before the windowing keyword, "
                      "which re-triggers the very syntax error in the issue, so the F2P "
                      "still fails and it does NOT resolve.",
        "rationale": "rejected by the flag-set branch of the equality, which pins the text "
                     "inside the wrapper to `windowedExpr operand window` — the operand "
                     "VERBATIM, so the wrapper is applied exactly once. This rival nests a "
                     "second wrapper around the operand, a strictly longer sequence. It "
                     "agrees with gold over more of the domain than cast-inside-over (it "
                     "gets the outer span right), so it gets its OWN witness rather than "
                     "sharing one: at (MAX(i), orderByName, isDecimal=true). Seen to "
                     "elaborate against the rival and to FAIL against the frozen solution.",
    },
    {
        "id": "drop-over-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_OVER,
        "witness": _WIT_DROP_OVER,
        "refinement": "omitting the windowing keyword run corresponds to a broken template "
                      "that concatenated the operand text straight onto the window-clause "
                      "text. Every windowing test — the F2P and the whole PASS_TO_PASS "
                      "windowing suite — then renders a statement with no windowing clause "
                      "and fails to execute; it does NOT resolve.",
        "rationale": "rejected by the equality's structural component (5): the ` OVER (` "
                     "keyword run is pinned at a fixed position by `windowedExpr`, and this "
                     "rival's result omits that token run entirely, matching neither branch. "
                     "The wrapper logic is left correct, so the rejection is attributable to "
                     "the keyword slot alone. Witness at (RANK(), partitionByRegion, "
                     "isDecimal=false) — probing the flag-clear side, since the defect is "
                     "flag-independent and the point should not duplicate a flag-set one. "
                     "Seen to elaborate against the rival and to FAIL against the frozen "
                     "solution.",
    },
    {
        "id": "drop-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_OPERAND,
        "witness": _WIT_DROP_OPERAND,
        "refinement": "dropping the operand text is this carrier's structural stand-in for "
                      "nagini's read-only-input probe. No resolving patch omits the "
                      "windowed expression itself — the rendered statement would have "
                      "nothing to window — so a verifying rival here would be a pure "
                      "verify-does-not-imply-resolve artifact, with every windowing test "
                      "failing.",
        "rationale": "attacks the `operand` binder, which the wrapper-placement rivals all "
                     "reproduce faithfully; without this case a rival mishandling only that "
                     "input would go unnoticed. Rejected by the equality, which pins the "
                     "operand text explicitly as the leading component of `windowedExpr` on "
                     "both branches. Wrong on either flag value; witness at (LEAD(l), "
                     "orderBySalary, isDecimal=false). Seen to elaborate against the rival and "
                     "to FAIL against the frozen solution.",
    },
    {
        "id": "drop-window",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_WINDOW,
        "witness": _WIT_DROP_WINDOW,
        "refinement": "dropping the window-clause text is the same structural probe on the "
                      "OTHER read-only input. No resolving patch discards the assembled "
                      "window clause — the partitioning and ordering it carries are what "
                      "the F2P's expected row values depend on — so the F2P and the "
                      "windowing PASS_TO_PASS tests all fail; it does NOT resolve.",
        "rationale": "attacks the `window` binder, the second input the wrapper-placement "
                     "rivals hold faithful. Rejected by the equality, which pins the window "
                     "text explicitly between the keyword run and the closing parenthesis. "
                     "Wrong on either flag value; witness taken on the flag-SET side at "
                     "(NTILE(4), partitionByGrade, isDecimal=true) so that this binder is "
                     "exercised under the wrapper as well. Seen to elaborate against the "
                     "rival and to FAIL against the frozen solution.",
    },
    {
        "id": "drop-close-paren",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_CLOSE_PAREN,
        "witness": _WIT_DROP_CLOSE_PAREN,
        "refinement": "leaving the window clause unterminated corresponds to a template "
                      "that lost its trailing delimiter. The rendered statement is then "
                      "unbalanced and fails to parse on the backend, so the F2P and the "
                      "windowing PASS_TO_PASS tests all fail to execute; it does NOT "
                      "resolve.",
        "rationale": "attacks the FOURTH structural slot of component (5) — the closing "
                     "parenthesis that `windowedExpr` pins after the window text. The "
                     "other three structural rivals leave it intact "
                     "(`drop-over-keyword` takes the keyword run, `drop-operand` and "
                     "`drop-window` the two text binders), so without this case a "
                     "rendering that dropped only the terminator would go unnoticed. "
                     "The wrapper logic is left correct, so the rejection is "
                     "attributable to that slot alone. Witness at (COUNT(z), "
                     "orderByTenure, isDecimal=true) — built against the rival (exit 0) "
                     "and against the frozen solution (exit 1, `decide` proving the "
                     "negation false).",
    },
    {
        "id": "cast-skips-empty-window",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CAST_SKIPS_EMPTY_WINDOW,
        "witness": _WIT_CAST_SKIPS_EMPTY_WINDOW,
        "refinement": "gating the numeric wrapper on a non-empty window clause "
                      "corresponds to a rendering that treats a windowed expression "
                      "carrying no partitioning, ordering or frame as not needing the "
                      "cast. A fixed-point-decimal windowed output over an empty window "
                      "clause then renders untyped and is filtered/compared as text, so "
                      "that input keeps the pre-existing wrong behavior; it does NOT "
                      "resolve.",
        "rationale": "the TIGHTEST near-miss in the lane: the wrapper spans the whole "
                     "windowed unit, on the correct branch, with every structural "
                     "component in place, and it agrees with the frozen impl on every "
                     "input EXCEPT an empty window clause. Rejected by the flag-set "
                     "branch of the equality, which requires the wrapper "
                     "unconditionally — it is a function of the flag alone, not of the "
                     "window text. Witness at (SUM(v), the EMPTY window clause, "
                     "isDecimal=true): the only reject-lane point where a binder is "
                     "empty, so it probes a carrier boundary the eight literal-text "
                     "witnesses cannot reach. Built against the rival (exit 0) and "
                     "against the frozen solution (exit 1, `decide` proving the "
                     "negation false).",
    },
    {
        "id": "cast-gated-on-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CAST_GATED_ON_OPERAND,
        "witness": _WIT_CAST_GATED_ON_OPERAND,
        "refinement": "gating the numeric wrapper on the operand text being longer than a "
                      "few characters corresponds to a rendering that decides whether the "
                      "value needs a numeric cast by inspecting the rendered operand text "
                      "rather than the declared output type. A fixed-point-decimal windowed "
                      "output over a short operand text then renders untyped and is "
                      "filtered/compared as text, so that input keeps the pre-existing "
                      "wrong behavior; it does NOT resolve.",
        "rationale": "the SECOND half of pinned fact (3), which claims the wrapper is a "
                     "function of the flag ALONE — 'not additionally conditioned on the "
                     "operand or window text'. `cast-skips-empty-window` demonstrates the "
                     "window half of that claim; before this case the OPERAND half was "
                     "asserted by the docstring and demonstrated by no rival, so a "
                     "rendering that consulted the operand text would have gone unprobed. "
                     "Rejected by the flag-set branch of the equality, which requires the "
                     "wrapper unconditionally. Witness at (AB, orderByCode, "
                     "isDecimal=true): a SHORT operand text, which is the sub-domain this "
                     "rival gets wrong and which no other reject-lane point reaches — every "
                     "other witness uses a long operand, where this rival agrees with gold. "
                     "Built against the rival (exit 0) and against the frozen solution "
                     "(exit 1, `decide` proving the negation false).",
    },
    {
        "id": "cast-literal-unterminated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CAST_LITERAL_UNTERMINATED,
        "witness": _WIT_CAST_LITERAL_UNTERMINATED,
        "refinement": "losing the terminator of the numeric-cast literal corresponds to a "
                      "wrapper template that lost its trailing delimiter. The rendered "
                      "statement is then unbalanced and fails to parse on the backend, so "
                      "the F2P fails to execute; it does NOT resolve.",
        "rationale": "attacks the BYTE CONTENT of the wrapper literals, which every other "
                     "rival leaves spelled correctly: the placement rivals "
                     "(`cast-inside-over`, `double-cast`) move a correctly-spelled wrapper "
                     "and `no-outer-cast` removes it entirely, so a rendering that emitted "
                     "the wrapper in the right place with the wrong text was unprobed. "
                     "Distinct from `drop-close-paren`, which drops the parenthesis "
                     "terminating the WINDOW clause — a different slot, sitting inside the "
                     "cast rather than closing it. Rejected by the flag-set branch, which "
                     "pins the trailing literal to \" AS NUMERIC)\" verbatim. Witness at "
                     "(MIN(s), orderByStart, isDecimal=true). Built against the rival "
                     "(exit 0) and against the frozen solution (exit 1, `decide` proving "
                     "the negation false).",
    },
]
