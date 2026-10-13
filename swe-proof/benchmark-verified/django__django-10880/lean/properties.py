"""properties.py — PBT falsification manifest for django__django-10880 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
where a positive control needs it, the proof body); the spec view is untouched,
so `variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function renders a call fragment from three inputs:

    implementation_buildCallSql (function : List Char) (distinct : Bool)
        (expressions : List Char) : List Char

pinned by the single load-bearing clause

    result = function ++ ['('] ++ distinctKeyword distinct ++ expressions ++ [')']

This clause is FULLY TRANSPARENT: `distinctKeyword` is a concrete deep model
(`if distinct then "DISTINCT ".toList else []`), and the whole right-hand side is
a fixed-order concatenation of the three inputs and two literal delimiters. There
is no opaque callee, so every rival is refutable by `decide` at a concrete input
— no carrier conditioning is needed.

The clause pins FOUR independent components against their input binders:

  * the `function` component (the leading identifier text),
  * the `expressions` component (the trailing argument text),
  * the modifier component `distinctKeyword distinct` — the flag-dependent slot
    that is the entire content of the behavior change, carrying the keyword and,
    when the flag is set, exactly one trailing separator,
  * the fixed positions of the two literal delimiters and the whole ordering.

Because the spec names every component explicitly, the frame obligation (nagini's
read-only inputs held at 1/2 permission) is discharged here STRUCTURALLY: a rival
that drops or mangles any unchanged component fails the equality. Lean is
referentially transparent, so nagini's permission-mutation class
(`frame-mutate-operands`, a write through a 1/2 reference) is VACUOUS on this
carrier — there is no aliasing to abuse. It is replaced by the two
component-drop rivals below, which attack the `function` and `expressions`
binders directly.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
  * `pos-branch-reorder` -> `pos-branch-reorder` (structurally different but
    correct impl; proof re-closed).
  * `pos-master-assert` -> `pos-functional-form` (a second correct impl in a
    different shape; the nagini "no echo the oracle" argument is vacuous here
    because the model is transparent, so this stands purely as a soundness
    positive of a different impl shape).
  * `drop-separator`, `wrong-separator-comma`, `wrong-keyword` port directly as
    modifier-slot rivals, each with a discriminating witness. `always-modifier`
    is ADDED (no nagini analogue): those three and the two component-drop rivals
    between them never pin the modifier slot to being EMPTY on the flag-clear
    sub-domain, and it is the only rival refutable solely at a flag-clear point.
  * nagini's frame-mutation rival is VACUOUS (see above); replaced by
    `drop-function` and `drop-expressions`, which vary the two input binders the
    modifier rivals hold fixed.
  * `admiss-fshape` (nagini) tested that the read-only precondition
    `Acc(list_pred,1/2)` is establishable for an F2P-shaped self-call. It PORTS,
    as `admiss-fshape` below. The absence of a precondition hypothesis in the
    lean obligation does NOT make the class vacuous: the analogue on a total
    carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
    input, which a positive that discharges `problem_spec_buildCallSql` at that
    concrete input by evaluation — as a `have`, before closing the frozen
    obligation verbatim — tests directly. (An earlier revision of this manifest
    recorded the class as vacuous for the no-precondition reason; that was
    wrong and is corrected here.)
  * `AXIOM_TESTS` are dropped: the axiom lane is G-AX's job and this gate ignores
    them.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input. It is checked in a file with the frozen obligation removed
and must (1) elaborate against the rival (the rival provably contradicts the
spec) and (2) FAIL against the frozen solution (so it is a real discriminator).
All witnesses below were built both ways with scripts/lean_verify.sh.
"""
from pathlib import Path

INSTANCE = "django__django-10880"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region (and, for positives,
# the proof body) of Solution.lean.
# ---------------------------------------------------------------------------

# The gold impl body, from the `let mut` line through the `return`.
_GOLD_BODY = (
    "  let mut distinctSlot : List Char := []\n"
    "  if distinct then\n"
    '    distinctSlot := "DISTINCT ".toList\n'
    "  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']"
)

# The single separator-bearing keyword literal inside the modifier slot.
_GOLD_KW = '    distinctSlot := "DISTINCT ".toList\n'

# The `intro` line opening the frozen tactic body — the insertion point for the
# admissibility positive's ground `have`. Inside the proof region, which a
# variant may legitimately extend (the theorem STATEMENT is untouched).
_PROOF_INTRO = "  intro function distinct expressions\n"

# The F2P-shaped argument text: a conditional expression used as the operand of
# a DISTINCT-modified aggregate. This is the shape at which the two components
# meet, so it is the point the admissibility positive grounds at.
_F2P_EXPR = "CASE WHEN pages > 300 THEN rating END"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-branch-reorder) Structurally different but CORRECT: the modifier slot is
# initialized to the keyword and CLEARED on the negated flag, so the `if` tests
# `!distinct` first. Semantically identical, different source. If it fails to
# verify, the spec is over-fit to one branch order => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _GOLD_BODY,
    '  let mut distinctSlot : List Char := "DISTINCT ".toList\n'
    "  if !distinct then\n"
    "    distinctSlot := []\n"
    "  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']",
)

# (pos-functional-form) A second CORRECT impl in a different shape: a pure
# functional expression (no `Id.run do`), with the modifier built as
# `"DISTINCT".toList ++ [' ']` (keyword and separator assembled separately). If
# it fails to verify, the spec is over-fit to one assembly form => SPEC-TOO-STRONG.
_POS_FUNCTIONAL = _swap(
    _BASE,
    "def implementation_buildCallSql\n"
    "    (function : List Char) (distinct : Bool) (expressions : List Char) :\n"
    "    List Char := Id.run do\n" + _GOLD_BODY,
    "def implementation_buildCallSql\n"
    "    (function : List Char) (distinct : Bool) (expressions : List Char) :\n"
    "    List Char :=\n"
    "  function ++ ['('] ++ (if distinct then \"DISTINCT\".toList ++ [' '] else [])"
    " ++ expressions ++ [')']",
)

# (admiss-fshape) ADMISSIBILITY. The lean analogue of nagini's precondition-
# establishability probe: the obligation is discharged, BY EVALUATION, at one
# concrete F2P-shaped input — the aggregate name, the modifier flag SET, and a
# conditional expression as the argument text — as a `have` inside the frozen
# tactic body, before the frozen obligation is closed verbatim below it. If the
# spec were unsatisfiable at exactly that input (the total-carrier analogue of
# PRECOND-TOO-STRONG) the `have` would not close. Nothing is assumed: no new
# declaration, no new axiom, and the theorem STATEMENT is byte-identical.
_POS_ADMISS = _swap(
    _BASE, _PROOF_INTRO,
    '  have _ground : problem_spec_buildCallSql "COUNT".toList true\n'
    f'      "{_F2P_EXPR}".toList\n'
    '      (implementation_buildCallSql "COUNT".toList true\n'
    f'        "{_F2P_EXPR}".toList) := by\n'
    "    unfold problem_spec_buildCallSql implementation_buildCallSql distinctKeyword\n"
    "    decide\n"
    + _PROOF_INTRO,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (drop-separator) THE discriminating bug: the modifier slot omits the trailing
# separator (`"DISTINCT"` with no space). Correct on the whole distinct=false
# sub-domain, WRONG on every distinct=true input.
_RIVAL_DROP_SEP = _swap(_BASE, _GOLD_KW, '    distinctSlot := "DISTINCT".toList\n')

# (wrong-separator-comma) The separator after the keyword is the wrong code
# point (a comma rather than a space).
_RIVAL_COMMA = _swap(_BASE, _GOLD_KW, '    distinctSlot := "DISTINCT,".toList\n')

# (wrong-keyword) The keyword bytes are wrong (final letter dropped) though a
# separator is present in the right relative place: `"DISTINC "` for `"DISTINCT "`.
_RIVAL_WRONG_KW = _swap(_BASE, _GOLD_KW, '    distinctSlot := "DISTINC ".toList\n')

# (drop-function) Drops the leading identifier component entirely. Attacks the
# `function` binder — a component the modifier rivals hold fixed. Wrong on every
# input with a non-empty function name, regardless of the flag.
_RIVAL_DROP_FN = _swap(
    _BASE,
    "  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']",
    "  return ['('] ++ distinctSlot ++ expressions ++ [')']",
)

# (always-modifier) The MIRROR of drop-separator: the modifier slot is emitted
# UNCONDITIONALLY, so the rival agrees with gold on every flag-set input and is
# wrong on every flag-clear one. Without this the reject battery only ever
# refutes on the flag-SET sub-domain (the three modifier rivals) or refutes
# flag-independently (the two component-drop rivals), so no case pins the
# modifier slot to being EMPTY when the flag is clear — an impl ignoring the
# flag in that direction would go unattacked.
_RIVAL_ALWAYS_MOD = _swap(
    _BASE, _GOLD_BODY,
    '  let mut distinctSlot : List Char := "DISTINCT ".toList\n'
    "  if distinct then\n"
    '    distinctSlot := "DISTINCT ".toList\n'
    "  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']",
)

# (drop-expressions) Drops the trailing argument component entirely. Attacks the
# `expressions` binder — the other component the modifier rivals hold fixed.
# Wrong on every input with non-empty argument text, regardless of the flag.
_RIVAL_DROP_EXPR = _swap(
    _BASE,
    "  return function ++ ['('] ++ distinctSlot ++ expressions ++ [')']",
    "  return function ++ ['('] ++ distinctSlot ++ [')']",
)


# --- witnesses (checked with obligation removed) ---------------------------
# Each negates the spec predicate at one concrete input. Shared preamble unfolds
# the three defs and discharges by `decide` (the carrier is fully transparent).

def _wit(function: str, distinct: str, expressions: str) -> str:
    return (
        f'example : ¬ problem_spec_buildCallSql "{function}".toList {distinct}'
        f' "{expressions}".toList\n'
        f'    (implementation_buildCallSql "{function}".toList {distinct}'
        f' "{expressions}".toList) := by\n'
        "  unfold problem_spec_buildCallSql implementation_buildCallSql distinctKeyword\n"
        "  decide"
    )


# distinct=true: the modifier rivals differ from gold only on this sub-domain.
_WIT_MODIFIER = _wit("COUNT", "true", "X")
# distinct=false: the component-drop rivals are wrong regardless of the flag, so
# their witnesses probe the OTHER flag value to vary that binder too. They also
# use DIFFERENT, multi-character `function` values (not "COUNT") so the reject
# battery varies the `function` binder rather than pinning it to one value —
# without that, a rival mishandling only `function` at some other value slips by.
_WIT_DROP_FN = _wit("SUM", "false", "X")
_WIT_DROP_EXPR = _wit("AVG", "false", "RATING")
# The flag-CLEAR refutation point: `always-modifier` agrees with gold on every
# flag-set input, so it can only be refuted here. Fourth distinct `function`
# value in the reject battery.
_WIT_ALWAYS_MOD = _wit("MAX", "false", "PRICE")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but correct impl (modifier slot initialized to the "
                  "keyword and cleared on the negated flag, so the branch order is inverted). "
                  "The equality clause is order-agnostic in the flag; if this fails to verify "
                  "the spec is over-fit to one branch order => SPEC-TOO-STRONG. Proof re-closed "
                  "with `cases distinct <;> rfl`."},
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a second correct impl in a different shape: a pure functional expression "
                  "(no imperative do-block) with the modifier assembled as keyword ++ [separator]. "
                  "The carrier is transparent so there is no oracle to echo; this stands purely as "
                  "a soundness positive of a different impl form. If it fails to verify the spec is "
                  "over-fit to one assembly form => SPEC-TOO-STRONG."},
    {"id": "admiss-fshape", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "ports nagini's `admiss-fshape`. The obligation is discharged BY EVALUATION at "
                  "one concrete F2P-shaped input — the aggregate name, the modifier flag SET, and "
                  "a conditional expression as the argument text — as a `have` inside the frozen "
                  "tactic body, before the frozen obligation is closed verbatim below it. This is "
                  "the total-carrier analogue of PRECOND-TOO-STRONG: if the spec were "
                  "unsatisfiable at exactly the input the F2P exercises, the `have` would not "
                  "close, and the obligation's `∀` would be discharging over a point the modeled "
                  "behavior cannot reach. It is NOT a tautology — the `have` applies "
                  "`problem_spec_buildCallSql` itself at that point, so `decide` must evaluate "
                  "both the impl and the spec's right-hand side and find them equal. Nothing is "
                  "assumed: no new declaration, no new axiom, and the theorem statement is "
                  "byte-identical."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "drop-separator", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_SEP,
     "witness": _WIT_MODIFIER,
     "refinement": "the modifier slot carries no trailing separator — the exact pre-gold "
                   "behaviour. Its faithful real patch fuses the keyword with the following "
                   "argument text, producing invalid SQL for the F2P (a distinct aggregate over a "
                   "conditional expression), so the F2P FAILS; it would NOT resolve. A verifying "
                   "rival here would be a true verify-does-not-imply-resolve break.",
     "rationale": "the discriminating bug on the distinct=true sub-domain. Rejection source: the "
                  "equality clause, whose modifier component `distinctKeyword true` carries the "
                  "separator the rival never emits. Witness at (COUNT, true, X): the rival yields "
                  "`COUNT(DISTINCTX)`, the spec demands `COUNT(DISTINCT X)`. Seen to elaborate "
                  "against the rival and fail against gold."},
    {"id": "wrong-separator-comma", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_COMMA,
     "witness": _WIT_MODIFIER,
     "refinement": "uses a comma as the delimiter after the keyword instead of a space. Its "
                   "faithful real patch renders invalid SQL for the F2P, so it FAILS; it would "
                   "NOT resolve.",
     "rationale": "targets the exact code point of the separator inside the modifier component "
                  "(`distinctKeyword true` ends in a space, not a comma) and the whole-sequence "
                  "equality. Witness at (COUNT, true, X). Seen to elaborate against the rival and "
                  "fail against gold. Shares the distinct=true point with drop-separator: both are "
                  "wrong precisely at that sub-domain and agree with gold everywhere else, so the "
                  "shared witness is honest (neither is a near-miss of the other)."},
    {"id": "wrong-keyword", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_KW,
     "witness": _WIT_MODIFIER,
     "refinement": "emits the keyword with its final letter dropped though the separator is "
                   "present in the right relative place. Its faithful real patch renders an "
                   "invalid SQL keyword for the F2P, so it FAILS; it would NOT resolve.",
     "rationale": "targets the keyword BYTES of the modifier component (they must be exactly the "
                  "full keyword) and the whole-sequence equality — distinct from the separator "
                  "code-point attack. Witness at (COUNT, true, X). Seen to elaborate against the "
                  "rival and fail against gold."},
    {"id": "always-modifier", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_MOD,
     "witness": _WIT_ALWAYS_MOD,
     "refinement": "emits the modifier slot unconditionally, ignoring the flag in the "
                   "flag-CLEAR direction. Its faithful real patch would decorate every "
                   "aggregate call with the modifier whether or not it was requested, changing "
                   "the rendered text — and the result set — for the un-modified aggregates the "
                   "P2P tests cover, so it FAILS; it would NOT resolve.",
     "rationale": "the MIRROR of drop-separator, closing the one direction the rest of the "
                  "battery leaves unattacked. The three modifier rivals refute on the flag-SET "
                  "sub-domain and the two component-drop rivals refute flag-independently, so "
                  "before this case NO rival pinned the modifier slot to being EMPTY when the "
                  "flag is clear. This rival agrees with gold on every flag-set input, so it can "
                  "only be refuted at a flag-clear point. Rejection source: the equality clause, "
                  "whose modifier component `distinctKeyword false` is `[]`. Witness at "
                  "(MAX, false, PRICE): the rival yields `MAX(DISTINCT PRICE)`, the spec demands "
                  "`MAX(PRICE)`. Built both ways: elaborates against the rival (exit 0), fails "
                  "against gold (exit 1, `decide` proved the negation false), and the "
                  "flipped-claim forgery inverts (gold 0 / rival 1), so the gold-side exit code "
                  "tracks the claim."},
    {"id": "drop-function", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FN,
     "witness": _WIT_DROP_FN,
     "refinement": "drops the leading identifier component. This is the lean carrier's analogue "
                   "of nagini's frame attack: the equality pins the `function` input explicitly, "
                   "so an impl that fails to reproduce it is refuted structurally. No resolving "
                   "patch omits the function name (the rendered call would be nameless), so a "
                   "verifying rival would be a pure verify-does-not-imply-resolve artifact.",
     "rationale": "attacks the `function` binder — held FIXED by the three modifier witnesses, so "
                  "a rival mishandling only this input would otherwise go unnoticed. Wrong "
                  "regardless of the flag; witness probes distinct=false to vary that binder too. "
                  "At (SUM, false, X) the rival yields `(X)`, the spec demands `SUM(X)`. Seen "
                  "to elaborate against the rival and fail against gold."},
    {"id": "drop-expressions", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_EXPR,
     "witness": _WIT_DROP_EXPR,
     "refinement": "drops the trailing argument component. The equality pins the `expressions` "
                   "input explicitly. No resolving patch drops the argument text (the aggregate "
                   "would have no operand), so a verifying rival would be a pure "
                   "verify-does-not-imply-resolve artifact.",
     "rationale": "attacks the `expressions` binder — the other component held fixed by the "
                  "modifier witnesses. Wrong regardless of the flag; witness probes "
                  "(AVG, false, RATING), where the rival yields `AVG()` and the spec demands "
                  "`AVG(RATING)`. Seen to elaborate against the rival and fail against gold."},
]
