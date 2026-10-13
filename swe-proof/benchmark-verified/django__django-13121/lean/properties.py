"""properties.py — G-PBT falsification battery for django__django-13121 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_expressionSqlStrategy`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. CARRIER NARROWING is
in force: the nagini bundle models TWO decision functions of the changed site —
``select_arithmetic_path`` (the strategy dispatch) AND ``operand_format_flag``
(the per-operand format decision). This Lean bundle models ONLY the purely
functional strategy-selection core (``expressionSqlStrategy``), the analogue of
nagini's ``select_arithmetic_path``. The second function and every nagini case
attached to it (the format positive control, the literal-exemption rival, and
the format-inversion near-miss) have NO counterpart here and are omitted as
carrier narrowing (see ``assessment``), NOT because they were hard.

DEFENDED SURFACE (one modeled behavior; three independent top-level clauses).
``problem_spec_expressionSqlStrategy nativeDurationSupport isSubtraction lhs rhs
result`` pins EXACTLY, over the two operand field types (each an
``Option FieldType``), whether the operator is subtraction, and whether the
backend natively supports durations:

  * (C_dur)  ``durationCond → result = durationArithmetic`` — the duration
    strategy is taken exactly when the backend lacks native duration support, at
    least one operand is a duration, and the two operands do NOT share a type;
  * (C_sub)  ``¬durationCond → dateSubCond → result = dateSubtraction`` — else
    the date-subtraction strategy iff the operator is subtraction and both
    operands share the very same date/time type;
  * (C_gen)  ``¬durationCond → ¬dateSubCond → result = genericArithmetic`` — else
    the ordinary strategy.

The three implications together pin ``result`` on EVERY input (the decision is
total), and each pin is a function of the ARGUMENTS (no opaque answer key to
echo), so any rival returning a wrong strategy on any input is refutable.

THE BEHAVIOURAL DISCRIMINATOR (the content the fix adds): the ``lhs ≠ rhs``
conjunct of ``durationCond``. Two operands that share the DURATION type must NOT
take the duration-arithmetic strategy — the pre-fix guard routed a
duration+duration arithmetic (a DurationField column plus a timedelta literal,
both DurationField) through the duration subclass, which re-raised on the F2P
scenario. The ``rival-prepatch-dur-dur`` rival below drops exactly that conjunct.

BINDER STRUCTURE. The spec predicate has FOUR input binders:
``nativeDurationSupport``, ``isSubtraction``, ``lhs``, ``rhs``. All four are
load-bearing and all four are varied across the reject witnesses (see the
point-spread block at the bottom): ``nativeDurationSupport`` and
``isSubtraction`` each take both boolean values, and ``lhs``/``rhs`` between them
range over EVERY kind the carrier has — duration, date, dateTime, time, other —
plus the ``none`` (no resolvable type) case, with both the ``lhs = rhs`` and
``lhs ≠ rhs`` cases exercised. The eight reject witnesses probe eight DISTINCT
input tuples (``pts=8``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling notes its inputs
    are pass-by-value primitives (int kind codes, bools) carrying no heap
    permission, so its frame-mutation class is already vacuous THERE; on this
    referentially transparent carrier it is doubly so — all four inputs are
    immutable values, there is no ``mut`` binder, no aliasing, no read-only cell.
    No substitute probe is fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def``; a diverging implementation cannot be written at all, so
    there is nothing to admit. (The nagini sibling carries no divergence case
    either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by three implications over the arguments themselves. There is no
    opaque answer key an implementation could echo. In its place the battery
    carries honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where a guard bites: the pre-fix duration+duration mis-route
    (drops ``lhs ≠ rhs``); dropping the native-duration gate; dropping the
    subtraction gate on the date-subtraction path; widening the date/time family
    to any same-type pair AND narrowing it by dropping one of its three kinds;
    admitting an operand with no resolvable type into that family; and two direct
    strategy-pin attacks (return the wrong strategy from the duration branch, and
    from the date-subtraction branch).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate at ONE concrete
input, with all four binders ground literals, and closes by ``decide`` (the
carrier is fully decidable — ``FieldType`` and ``ExprStrategy`` derive
``DecidableEq`` and every input is a literal, so nothing is opaque and no
hypothesis is bound: there is no consistency question). Each witness was checked
with two real ``lake env lean`` builds to HOLD of its rival and to FAIL on the
frozen solution, so it discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
mis-selects the SQL-generation strategy on a sub-domain the F2P (or the
cross-backend P2P) suite exercises, so the emitted SQL is wrong (or raises) and
the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the strategy decision is modeled deeply from plain data); the axiom
lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-13121"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole first (duration) branch of the impl, strictly inside
# `-- impl-start`/`-- impl-end`.
_I_DUR_GUARD = (
    "  if nativeDurationSupport = false ∧\n"
    "      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then\n"
    "    return ExprStrategy.durationArithmetic")
# The whole second (date-subtraction) branch.
_I_SUB_GUARD = (
    "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then\n"
    "    return ExprStrategy.dateSubtraction")

# The FULL impl body (for the single-return reshape positive control).
_I_FULL = """  -- A duration mixed with a value of a different type, on a backend without
  -- native duration support, uses the duration-arithmetic strategy.
  if nativeDurationSupport = false ∧
      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then
    return ExprStrategy.durationArithmetic
  -- Subtracting one date/time value from another of the same type yields a
  -- duration via the date-subtraction strategy.
  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then
    return ExprStrategy.dateSubtraction
  -- Everything else uses the ordinary arithmetic strategy.
  return ExprStrategy.genericArithmetic"""

# The FULL frozen proof body (for the branch-reorder positive control that
# re-proves, and for the admissibility prepend which targets the intro line).
_P_INTRO = "  intro nativeDurationSupport isSubtraction lhs rhs\n"
_P_FULL = """  intro nativeDurationSupport isSubtraction lhs rhs
  unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy
  simp only [Id.run]
  split_ifs with h1 h2
  · exact ⟨fun _ => rfl, fun h => absurd h1 h, fun h => absurd h1 h⟩
  · exact ⟨fun h => absurd h h1, fun _ _ => rfl, fun _ h => absurd h2 h⟩
  · exact ⟨fun h => absurd h h1, fun _ h => absurd h h2, fun _ _ => rfl⟩"""


# ---------------------------------------------------------------------------
# witness builder. States the spec predicate at one concrete (nat, sub, lhs, rhs)
# and closes by `decide`. All inputs are ground literals — nothing opaque, no
# bound hypothesis.
# ---------------------------------------------------------------------------
def _w(nat, sub, lhs, rhs):
    return (
        f"example : ¬ problem_spec_expressionSqlStrategy {nat} {sub} {lhs} {rhs}\n"
        f"    (implementation_expressionSqlStrategy {nat} {sub} {lhs} {rhs}) := by\n"
        f"  unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy\n"
        f"  decide\n")


_DUR = "(some FieldType.durationField)"
_DATE = "(some FieldType.dateField)"
_DATETIME = "(some FieldType.dateTimeField)"
_TIME = "(some FieldType.timeField)"
_OTHER = "(some FieldType.other)"
_NONE = "(none : Option FieldType)"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_expressionSqlStrategy` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-single-return",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different CORRECT reshape: replace the two early-`return`
        # branches with a single `let result := if … then … else if … else …`
        # and one return point (opposite of the fall-through form). Definitionally
        # the same value on every input, so the FROZEN proof still closes — no
        # proof authoring, no helper lemma, no assumption token. (Verified: real
        # build.)
        "module": _swap(
            _BASE, _I_FULL,
            "  let result : ExprStrategy :=\n"
            "    if nativeDurationSupport = false ∧\n"
            "        (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then\n"
            "      ExprStrategy.durationArithmetic\n"
            "    else if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then\n"
            "      ExprStrategy.dateSubtraction\n"
            "    else ExprStrategy.genericArithmetic\n"
            "  return result"),
        "rationale": "structurally-different but semantically identical "
                     "expressionSqlStrategy: the two fall-through early-return "
                     "branches are collapsed into a single if/else-if/else assigned "
                     "to one local with a single return point. It computes the SAME "
                     "strategy on every input, so C_dur/C_sub/C_gen all still hold — "
                     "else the postcondition is over-fit to the fall-through return "
                     "shape => SPEC-TOO-STRONG. The result is definitionally the "
                     "frozen body, so the frozen proof closes unchanged; statement "
                     "byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-control-path-single-return.",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-REORDER positive control: test the date-subtraction condition
        # FIRST, the duration condition second. Semantically identical because the
        # two conditions are mutually exclusive (durationCond requires lhs ≠ rhs;
        # dateSubCond requires lhs = rhs). The proof region is re-proved: after the
        # reorder `split_ifs` binds the subtraction guard first, so the tuple order
        # is permuted and the duration case is discharged from the shared-type
        # contradiction. The `correct_expressionSqlStrategy` STATEMENT is
        # byte-identical; no new axiom/lemma. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_FULL,
             "  -- Subtracting one date/time value from another of the same type yields a\n"
             "  -- duration via the date-subtraction strategy.\n"
             "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then\n"
             "    return ExprStrategy.dateSubtraction\n"
             "  -- A duration mixed with a value of a different type, on a backend without\n"
             "  -- native duration support, uses the duration-arithmetic strategy.\n"
             "  if nativeDurationSupport = false ∧\n"
             "      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then\n"
             "    return ExprStrategy.durationArithmetic\n"
             "  -- Everything else uses the ordinary arithmetic strategy.\n"
             "  return ExprStrategy.genericArithmetic"),
            (_P_FULL,
             "  intro nativeDurationSupport isSubtraction lhs rhs\n"
             "  unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy\n"
             "  simp only [Id.run]\n"
             "  split_ifs with h1 h2\n"
             "  · refine ⟨fun hd => absurd hd.2.2 (by simp [h1.2.2]), fun _ _ => rfl, fun _ h => absurd h1 h⟩\n"
             "  · exact ⟨fun _ => rfl, fun h _ => absurd h2 h, fun h => absurd h2 h⟩\n"
             "  · exact ⟨fun h => absurd h h2, fun _ h => absurd h h1, fun _ _ => rfl⟩"),
        ),
        "rationale": "branch-REORDER positive control: the date-subtraction "
                     "condition is tested first, the duration condition second — "
                     "identical values (the two conditions are mutually exclusive on "
                     "lhs = rhs vs lhs ≠ rhs), different control flow. A faithful "
                     "reshape MUST verify, else the spec is over-fit to one branch "
                     "order => SPEC-TOO-STRONG. Re-proved by permuting the "
                     "`split_ifs` tuple and discharging the duration case from the "
                     "shared-type contradiction (statement byte-identical, no new "
                     "axiom/lemma). Ports nagini's pos-control-path-single-return "
                     "family (structural reshape of the dispatch).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at the
    # F2P-shaped input. The frozen theorem carries NO precondition binder (the
    # decision is total over all inputs), so nagini's precondition-admission
    # self-call re-expresses as: discharge the spec predicate by evaluation at the
    # smallest F2P-shaped combination (a DurationField column plus a timedelta
    # literal — both DurationField, non-native backend, addition; the exact
    # duration+duration dispatch the fix repairs) as a `have`, then close the
    # frozen obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, ground instance is a `have` prepended to the tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_expressionSqlStrategy false false\n"
            "      (some FieldType.durationField) (some FieldType.durationField)\n"
            "      (implementation_expressionSqlStrategy false false\n"
            "        (some FieldType.durationField) (some FieldType.durationField)) := by\n"
            "    unfold problem_spec_expressionSqlStrategy implementation_expressionSqlStrategy\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the F2P-shaped input (a "
                     "DurationField column plus a timedelta literal — both "
                     "DurationField, non-native backend, addition, i.e. the exact "
                     "duration+duration dispatch the fix repairs, expecting the "
                     "generic strategy) by evaluation as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input "
                     "— the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, statement byte-identical, ground `have` in the "
                     "existing tactic body. Ports nagini's admiss-self-calls.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: drop the `lhs ≠ rhs` conjunct (pre-patch bug) ----
    {
        "id": "rival-prepatch-dur-dur",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then",
            "      (isDurationField lhs = true ∨ isDurationField rhs = true) then"),
        "refinement": "drops the added `lhs ≠ rhs` conjunct so EITHER operand being "
                      "a duration routes to the duration-arithmetic strategy — "
                      "exactly the pre-patch guard. Its faithful real patch is the "
                      "unchanged pre-patch dispatch, which routes a "
                      "duration+timedelta-literal arithmetic (both DurationField) "
                      "through the duration strategy and re-raises "
                      "decimal.InvalidOperation on the F2P test_duration_expressions "
                      "— it would NOT resolve.",
        "rationale": "the DISCRIMINATING bug this patch fixes. REJECT from C_gen: on "
                     "(native=false, sub=false, lhs=rhs=duration) the RIVAL's guard "
                     "holds (it no longer requires distinct types) so it returns "
                     "durationArithmetic, but the SPEC's durationCond is false there "
                     "(it does require lhs ≠ rhs) and dateSubCond is false too, so the "
                     "generic pin C_gen requires genericArithmetic — C_gen is the "
                     "clause the rival violates, and C_dur is vacuously satisfied at "
                     "this point. If it verified => SPEC-TOO-WEAK (admits the very "
                     "bug). Refuted at (false, false, duration, duration).",
        "witness": _w("false", "false", _DUR, _DUR),
    },

    # ---- drop the native-duration gate ----
    {
        "id": "rival-drop-native-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "  if nativeDurationSupport = false ∧\n"
            "      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then",
            "  if (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then"),
        "refinement": "removes `nativeDurationSupport = false` from the duration "
                      "guard, routing a mixed duration+datetime pairing to the "
                      "duration strategy even on a backend with native duration "
                      "support. The faithful real patch drops the native-support "
                      "check, so on a native-duration backend a duration+datetime "
                      "arithmetic wrongly takes the duration strategy instead of the "
                      "generic combination, changing rendered SQL on the "
                      "native-backend P2P scenarios — it would NOT resolve.",
        "rationale": "partial-domain: correct on non-native backends, wrong when "
                     "native support is present. REJECT from C_gen: on "
                     "(native=true, sub=false, lhs=duration, rhs=dateTime) durationCond "
                     "is false (native) and dateSubCond is false, so the generic pin "
                     "requires genericArithmetic, but the rival returns "
                     "durationArithmetic. If it verified => SPEC-TOO-WEAK (the "
                     "native gate is unconstrained). Refuted at "
                     "(true, false, duration, dateTime).",
        "witness": _w("true", "false", _DUR, _DATETIME),
    },

    # ---- drop the subtraction gate on the date-subtraction path ----
    {
        "id": "rival-drop-subtract-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then",
            "  if isDateTimeField lhs = true ∧ lhs = rhs then"),
        "refinement": "removes `isSubtraction = true` from the date-subtraction "
                      "guard, so same-type date/time operands take the "
                      "date-subtraction strategy for ANY operator. The faithful real "
                      "patch drops the subtraction check, so a date+date ADDITION (or "
                      "any non-subtraction same-date/time combination) wrongly takes "
                      "the date-subtraction strategy instead of the generic "
                      "combination, corrupting that rendered SQL across the P2P "
                      "expression suite — it would NOT resolve.",
        "rationale": "partial-domain: correct under subtraction, wrong on "
                     "same-date/time non-subtraction. REJECT from C_gen: on "
                     "(native=false, sub=false, lhs=rhs=date) durationCond is false "
                     "and dateSubCond requires isSubtraction so it is false, hence the "
                     "generic pin requires genericArithmetic, but the rival returns "
                     "dateSubtraction. If it verified => SPEC-TOO-WEAK (the subtraction "
                     "gate is unconstrained). Refuted at (false, false, date, date).",
        "witness": _w("false", "false", _DATE, _DATE),
    },

    # ---- widen the date/time family to any same-type pair ----
    {
        "id": "rival-widen-datetime-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then",
            "  if isSubtraction = true ∧ lhs = rhs then"),
        "refinement": "replaces the date/time-type membership with a bare same-type "
                      "test, so ANY same-type subtraction (including non-date/time "
                      "kinds like an integer field) takes the date-subtraction "
                      "strategy. The faithful real patch drops the date/time-family "
                      "membership, so an integer − integer subtraction wrongly takes "
                      "the date-subtraction strategy instead of the generic "
                      "combination, corrupting ordinary numeric-subtraction SQL "
                      "across the P2P suite — it would NOT resolve.",
        "rationale": "partial-domain: correct on date/time kinds, wrong on "
                     "non-date/time same-type subtraction. REJECT from C_gen: on "
                     "(native=false, sub=true, lhs=rhs=other) durationCond is false "
                     "and dateSubCond's isDateTimeField is false, so the generic pin "
                     "requires genericArithmetic, but the rival returns "
                     "dateSubtraction. If it verified => SPEC-TOO-WEAK (the date/time "
                     "family is unconstrained). Refuted at (false, true, other, "
                     "other).",
        "witness": _w("false", "true", _OTHER, _OTHER),
    },

    # ---- direct C_dur attack: wrong strategy from the duration branch ----
    {
        "id": "rival-dur-branch-wrong-strategy",
        "kind": "uniqueness",
        "expect": "reject",
        # The duration branch's guard is left EXACTLY correct, but it returns the
        # generic strategy instead of the duration strategy. Attacks C_dur directly
        # (the other rivals attack C_gen/C_sub), so the duration pin is defended.
        "module": _swap(
            _BASE, _I_DUR_GUARD,
            "  if nativeDurationSupport = false ∧\n"
            "      (isDurationField lhs = true ∨ isDurationField rhs = true) ∧ lhs ≠ rhs then\n"
            "    return ExprStrategy.genericArithmetic"),
        "refinement": "keeps the duration guard exactly right but emits the generic "
                      "strategy where the duration strategy is required. The faithful "
                      "real patch would, on a non-native backend, combine a "
                      "duration-with-a-different-type arithmetic through the ordinary "
                      "path instead of the duration strategy — the very case the "
                      "duration strategy exists to render correctly on SQLite/MySQL — "
                      "so that arithmetic renders wrong SQL and the faithful patch "
                      "would NOT resolve.",
        "rationale": "direct attack on C_dur (the pin no other rival targets). "
                     "REJECT from C_dur: on (native=false, sub=false, lhs=duration, "
                     "rhs=dateTime) durationCond holds, so the spec requires "
                     "durationArithmetic, but the rival returns genericArithmetic. If "
                     "it verified => SPEC-TOO-WEAK (the duration pin is "
                     "unconstrained). Refuted at (false, false, duration, dateTime).",
        "witness": _w("false", "false", _DUR, _DATETIME),
    },

    # ---- direct C_sub attack: wrong strategy from the date-subtraction branch ----
    {
        "id": "rival-sub-branch-wrong-strategy",
        "kind": "uniqueness",
        "expect": "reject",
        # The date-subtraction branch's guard is left EXACTLY correct, but it
        # returns the generic strategy instead of the date-subtraction strategy.
        # Attacks C_sub directly, so the date-subtraction pin is defended.
        "module": _swap(
            _BASE, _I_SUB_GUARD,
            "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then\n"
            "    return ExprStrategy.genericArithmetic"),
        "refinement": "keeps the date-subtraction guard exactly right but emits the "
                      "generic strategy where the date-subtraction strategy is "
                      "required. The faithful real patch would render a same-type "
                      "date/time subtraction (yielding the elapsed amount) through "
                      "the ordinary combination instead of the date-subtraction "
                      "strategy, producing the wrong SQL for those P2P scenarios — it "
                      "would NOT resolve.",
        "rationale": "direct attack on C_sub. REJECT from C_sub: on "
                     "(native=false, sub=true, lhs=rhs=date) durationCond is false and "
                     "dateSubCond holds, so the spec requires dateSubtraction, but the "
                     "rival returns genericArithmetic. If it verified => SPEC-TOO-WEAK "
                     "(the date-subtraction pin is unconstrained). Refuted at "
                     "(false, true, date, date).",
        "witness": _w("false", "true", _DATE, _DATE),
    },

    # ---- NARROW the date/time family: drop one of the three kinds ----
    # AUDIT-ADDED. The four ported rivals plus the two pin attacks all probe the
    # date/time family from ONE side — widening it (rival-widen-datetime-family)
    # — and none of them ever instantiates a binder at the third date/time kind.
    # So `isDateTimeField`'s membership was defended only against being too
    # LARGE, never against being too SMALL, and one whole constructor of the
    # carrier was untouched by every witness point. This rival drops exactly one
    # kind from the family, which is wrong on precisely the two inputs where that
    # kind is the shared operand type.
    {
        "id": "rival-narrow-datetime-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then",
            "  if isSubtraction = true ∧\n"
            "      (lhs = some FieldType.dateField ∨ lhs = some FieldType.dateTimeField) ∧ lhs = rhs then"),
        "refinement": "narrows the date/time membership to only two of the three "
                      "date/time kinds, so a same-type subtraction of the omitted kind "
                      "no longer takes the date-subtraction strategy. The faithful real "
                      "patch enumerates an incomplete date/time family, so subtracting "
                      "one time-of-day value from another renders the ordinary "
                      "combination instead of the elapsed-amount form — wrong SQL for "
                      "that P2P scenario, so it would NOT resolve.",
        "rationale": "partial-domain, the MIRROR of rival-widen-datetime-family: "
                     "correct on the two kinds it keeps, wrong on the one it drops. "
                     "REJECT from C_sub: on (native=false, sub=true, lhs=rhs=time) "
                     "durationCond is false and dateSubCond HOLDS (a time value is a "
                     "date/time kind), so the spec requires dateSubtraction, but the "
                     "rival returns genericArithmetic. If it verified => SPEC-TOO-WEAK "
                     "(the family would be pinned only from above, and any subset of "
                     "the three kinds would satisfy the spec). Refuted at "
                     "(false, true, time, time) — the only witness point in the battery "
                     "that instantiates the third date/time kind.",
        "witness": _w("false", "true", _TIME, _TIME),
    },

    # ---- treat an operand with NO resolvable type as a date/time kind ----
    # AUDIT-ADDED. `Option FieldType`'s `none` constructor — an operand whose type
    # does not resolve — was never instantiated by any witness point either, so
    # nothing in the battery pinned the spec's treatment of an untyped operand.
    # This rival counts `none` into the date/time family, wrong on exactly the two
    # inputs where BOTH operands are untyped.
    {
        "id": "rival-untyped-as-datetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "  if isSubtraction = true ∧ isDateTimeField lhs = true ∧ lhs = rhs then",
            "  if isSubtraction = true ∧ (isDateTimeField lhs = true ∨ lhs = none) ∧ lhs = rhs then"),
        "refinement": "counts an operand with no resolvable type as a date/time kind, "
                      "so subtracting two such operands takes the date-subtraction "
                      "strategy. The faithful real patch admits the unresolved-type "
                      "case into the date/time family, so an expression whose two "
                      "operand types both fail to resolve renders the elapsed-amount "
                      "form instead of the ordinary combination — wrong SQL wherever "
                      "an operand type is unresolvable, so it would NOT resolve.",
        "rationale": "attacks the boundary between `none` and the date/time kinds, "
                     "which no other case instantiates. REJECT from C_gen: on "
                     "(native=false, sub=true, lhs=rhs=none) durationCond is false (an "
                     "untyped operand is not a duration) and dateSubCond is false (an "
                     "untyped operand is not a date/time kind), so the generic pin "
                     "requires genericArithmetic, but the rival returns dateSubtraction. "
                     "If it verified => SPEC-TOO-WEAK (the untyped operand would be "
                     "free to join the date/time family). Refuted at "
                     "(false, true, none, none) — the only witness point in the battery "
                     "that instantiates the no-resolvable-type operand.",
        "witness": _w("false", "true", _NONE, _NONE),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals — 5 over select_arithmetic_path
# and 2 over operand_format_flag) plus an AXIOM lane. CARRIER NARROWING: this Lean
# bundle carries exactly ONE `theorem correct_*`, modeling only the strategy
# dispatch (nagini's select_arithmetic_path). The second modeled function
# (operand_format_flag) and every case attached to it have no counterpart here.
#
#   sibling case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-path-single-return  -> pos-single-return         RE-EXPRESSED
#   (structural reshape of dispatch)-> pos-branch-reorder        ADDED (re-proved)
#   admiss-self-calls               -> admiss-f2p-shape          RE-EXPRESSED
#   rival-prepatch-dur-dur          -> rival-prepatch-dur-dur    PORTED
#   rival-drop-native-gate          -> rival-drop-native-gate    PORTED
#   rival-drop-subtract-gate        -> rival-drop-subtract-gate  PORTED
#   rival-widen-temporal-family     -> rival-widen-datetime-family PORTED
#   (none — attacks C_dur pin)      -> rival-dur-branch-wrong-strategy ADDED
#   (none — attacks C_sub pin)      -> rival-sub-branch-wrong-strategy ADDED
#   (none — family from below)      -> rival-narrow-datetime-family AUDIT-ADDED
#   (none — untyped operand)        -> rival-untyped-as-datetime    AUDIT-ADDED
#   pos-control-format-inverted-test-> (none)  OMITTED — carrier narrowing
#   rival-literal-exemption         -> (none)  OMITTED — carrier narrowing
#   rival-format-inverted           -> (none)  OMITTED — carrier narrowing
#   AXIOM_TESTS (3)                 -> (none)  DROPPED (G-AX)
#
# OMITTED (operand_format_flag family): the nagini bundle models a SECOND decision
#   function (the per-operand format flag) with its own postcondition and three
#   cases (a format positive control, the literal-exemption discriminator rival,
#   and the format-inversion near-miss). This Lean bundle does NOT model that
#   function — it carries a single `theorem correct_expressionSqlStrategy` over the
#   strategy dispatch only — so those three cases have NO spec surface to attach to
#   here. This is carrier narrowing (451/500 lean bundles carry exactly one
#   theorem where the nagini sibling contracts several), NOT a proof that was too
#   hard: there is no `operand_format_flag` obligation in Solution.lean to defend
#   or attack. The one discriminator lost with it (the literal-exemption bug, the
#   second half of the gold patch) is a KNOWN GAP relative to nagini; the FIRST
#   discriminator (the duration+duration mis-route) is fully covered here by
#   rival-prepatch-dur-dur.
# ADDED (pos-branch-reorder, rival-dur-branch-wrong-strategy,
#   rival-sub-branch-wrong-strategy): the four PORTED rivals all attack the generic
#   pin C_gen (each mis-routes an input that should be generic). This backend's
#   coverage tool requires EVERY top-level postcondition clause to be attacked, and
#   the spec has three: C_dur, C_sub, C_gen. Two rivals are added that keep the
#   guard exactly right but return the wrong strategy from the duration branch
#   (attacks C_dur) and the date-subtraction branch (attacks C_sub). A second
#   positive control (branch reorder) is added to defend the dispatch against
#   branch-order over-fitting. None is fabricated for an unmodeled behavior; each
#   attacks a real, load-bearing clause of the SAME modeled spec.
# VACUOUS (frame/permission mutation; divergence/non-termination): frame mutation
#   is vacuous already in nagini (pass-by-value primitives, no heap permission) and
#   doubly so here (referential transparency, no `mut` binder). Divergence is
#   vacuous on lean (a total Lean `def` cannot diverge). No substitute is fabricated.
#
# AUDIT-ADDED (rival-narrow-datetime-family, rival-untyped-as-datetime): an
#   independent audit measured the witness POINTS, not just the binders, and found
#   that the six original reject witnesses between them never instantiated two of
#   the carrier's constructors — `FieldType.timeField` and `Option`'s `none`. Both
#   are load-bearing in the spec (`isDateTimeField` admits the time kind; `none`
#   is excluded from both `isDurationField` and `isDateTimeField`), so each was
#   pinned by the spec but attacked by nothing. The two rivals hit exactly those
#   points: the date/time family is now defended from BELOW (narrowing it is
#   caught) as well as from above, and the untyped-operand boundary is defended at
#   all. Neither is a reshape: each differs from the frozen decision on exactly
#   two of the 144 inputs, and each was checked with the two real builds.
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT input tuples
# (pts=8):
#   (native, sub, lhs, rhs) =
#     (false, false, duration, duration)   rival-prepatch-dur-dur         C_gen
#     (true,  false, duration, dateTime)   rival-drop-native-gate         C_gen
#     (false, false, date,     date)       rival-drop-subtract-gate       C_gen
#     (false, true,  other,    other)      rival-widen-datetime-family    C_gen
#     (false, false, duration, dateTime)   rival-dur-branch-wrong-strategy C_dur
#     (false, true,  date,     date)       rival-sub-branch-wrong-strategy C_sub
#     (false, true,  time,     time)       rival-narrow-datetime-family   C_sub
#     (false, true,  none,     none)       rival-untyped-as-datetime      C_gen
#   Across them nativeDurationSupport ∈ {false, true}, isSubtraction ∈
#   {false, true}, and lhs/rhs between them cover ALL FIVE FieldType kinds plus
#   `none` — duration, date, dateTime, time, other, none — with both lhs = rhs and
#   lhs ≠ rhs exercised, so no input binder is pinned to a single value and no
#   constructor of either carrier type is left uninstantiated. Each clause of the
#   spec is attacked: C_dur once, C_sub twice, C_gen five times.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
# (the strategy decision is modeled deeply), so there is nothing to probe and the
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
