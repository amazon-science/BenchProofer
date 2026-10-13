"""properties.py — G-PBT falsification battery for django__django-13449 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct windowNumericSql``
tactic body, is changed — both regions the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct`` obligation survives with a
byte-identical header) and swaps in a candidate implementation. It is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, three free input binders, no
precondition):

  windowNumericSql (isDecimal : Bool) (innerBase : List Char) (win : List Char)
      return (out : List Char)
    ensures out = windowSql isDecimal innerBase win            -- the sole clause

The method renders the SQL for a windowed expression on a backend whose
fixed-precision decimal results must be coerced by a numeric cast. The single
``ensures`` is the whole obligation, and it pins the rendering to the transparent
pure ``def windowSql``:

    windowSql isDecimal innerBase win
      = if isDecimal then numericCast (overClause innerBase win)
        else overClause innerBase win

``numericCast`` and ``overClause`` are likewise transparent ``def``s (concrete
``List Char`` concatenations) in the ``pure`` region, and the ``axioms`` region is
EMPTY. So the whole carrier computes: nothing here is ``opaque``, no witness has
to condition on an assumed term, and every rival below is refutable at literal
inputs.

WHICH CLAUSE, WHICH BINDER. There is exactly ONE top-level postcondition clause,
so every rival attacks it; what distinguishes the rivals is WHICH part of the
post-image they get wrong and on which sub-domain:

  * the CAST PLACEMENT relative to the window template — the discriminating
    content of the fix. The cast must wrap the ENTIRE windowed expression, not
    the operand alone (rivals ``cast-inside-clause``, ``double-cast``), and the
    operand is interpolated VERBATIM on BOTH arms (rival
    ``nondecimal-operand-cast`` for the non-decimal one);
  * WHETHER the cast fires at all, keyed on ``isDecimal`` (rivals
    ``no-cast-anywhere``, ``always-cast``, ``flag-inverted``,
    ``partial-empty-window``);
  * the STRUCTURE of the template that combines the two string inputs — the
    separator, the argument ORDER, and that the window text is interpolated at
    all (rivals ``drop-over-separator``, ``operands-exchanged``,
    ``window-text-dropped``).

All three INPUT binders are free (the ``pre-conditions`` region is empty, so the
post-image must hold at EVERY value of each) and all three are VARIED by the
reject witnesses: ``isDecimal`` is probed at BOTH ``true`` (5 rivals) and
``false`` (5 rivals); ``innerBase`` and ``win`` take a distinct value in every one
of the 10 witnesses, and ``win`` is additionally probed at its ``[]`` boundary. No
binder is held fixed across the battery, so a rival that mishandled only one
input could not slip through unprobed.

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case accounting
in the footer):

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's two MANDATORY
    probes write to an input it holds at half permission (its ``operand`` and its
    ``window``) and are rejected for insufficient permission. Lean and Velvet are
    referentially transparent: all three inputs here are immutable values, this
    bundle declares no ``mut`` PARAMETER, and there is no heap, aliasing or
    permission system to subvert. There is no read-only input a rival could
    overwrite. No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the sibling records.
    The post-image is a total function of the method's own arguments, fully
    unfolded to literal character sequences; there is no answer key to echo. The
    honest cheapest correct impl (report the post-image directly) is carried as a
    POSITIVE control instead, where it doubles as evidence the pin is not
    echo-vulnerable: any wrong placement still fails ``out = windowSql …``.

  * OPERAND'S OWN CAST — the sibling reaches this through a FOURTH input, the
    operand's own declared decimal-ness, and renders the operand through it on
    the non-cast branch; its ``uniq-nondecimal-ignore-operand-cast`` rival
    STRIPS that operand-level cast. Here ``innerBase`` is by definition the
    operand SQL already carrying no cast of its own (spec view: "WITHOUT any
    numeric cast of its own"), so there is no fourth binder and STRIPPING a cast
    that is not there is indeed a no-op: that rival's own direction is gold here
    and is not ported.

    But the CLASS survives, in the opposite direction, and is ported: the
    post-image interpolates ``innerBase`` VERBATIM on both arms, so an impl that
    ADDS a coercion around the operand alone on the NON-decimal arm is wrong on
    this carrier and is refutable at a literal input. That is
    ``uniq-nondecimal-operand-cast`` below. It matters because it is the only
    rival pinning the operand's verbatim-ness on the non-decimal arm — the arm
    where the sibling's spec deliberately does NOT render the operand verbatim —
    and no other rival in this battery attacks that point: every other rival
    either agrees with gold on the whole non-decimal arm or differs from this one
    there. So the carrier collapses ONE DIRECTION of the sibling's distinction,
    not the distinction.

  * PARTIAL-DOMAIN / VALUE — the whole reject surface. See ``partial-empty-window``
    for a rival correct on every non-empty window clause and wrong only at the
    ``win = []`` boundary.

  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so
each witness reaches it through Velvet's own tester machinery: after
``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for``, the proposition
``windowNumericSqlTester isDecimal innerBase win = false`` says the extracted
program's result VIOLATES the method's postcondition at that concrete input, and
``decide`` settles it — the carrier is all concrete ``List Char`` concatenation,
so the instance reduces. There is no ``require`` clause, so no probed input can
pass vacuously on an excluded domain. Every witness states its refutation at
LITERAL inputs and binds NO hypothesis, so no witness can be inconsistent and
the gate's consistency probe is a no-op (``consistency_probe`` returns ``None``).
No banned token (``sorry`` / ``admit`` / ``native_decide`` / ``axiom`` /
``opaque``) appears in any witness. Each was checked out-of-band with
``scripts/lean_verify.sh``: all 10 ELABORATE against their rival (exit 0) and all
10 FAIL against the frozen solution (``decide`` proves the tester is instead
``true``) — the discrimination the gate re-runs.

That gold-side failure is a REFUTATION and not a stuck reduction, checked
directly rather than inferred: the claim ``windowNumericSqlTester … = true``
ELABORATES against the frozen solution (exit 0) at three separate points — one
on each arm of the flag, plus the ``win = []`` boundary — so ``decide`` really
does decide this tester, and each witness's gold-side error is the kernel
reporting ``decide`` proved the proposition false.

AXIOM lane: dropped. There is no ``AXIOM_TESTS`` here. The sibling carries
axiom-soundness / containment probes for its ``compile_operand`` axiom, but this
bundle axiomatizes nothing (empty ``axioms`` region, ``meta.json`` ``axioms: []``,
no ``axiom_check.py``); that lane is G-AX's job and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13449"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- impl region and same_spec holds by construction (asserted at load by
# ---- _swap, so the manifest breaks loudly if the frozen solution drifts).
_IMPL = (
    "    let mut out : List Char := []\n"
    "    if isDecimal then\n"
    "      -- The operand carries no inner cast; the OVER template is assembled first,\n"
    "      -- and the numeric cast wraps the whole windowed expression.\n"
    "      let windowed := overClause innerBase win\n"
    "      out := numericCast windowed\n"
    "    else\n"
    "      out := overClause innerBase win\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. It is elided from the spec view, so a variant may
# retune it; the `prove_correct windowNumericSql` HEADER survives untouched in
# every case. Rivals leave it exactly as-is — their rejection is carried by the
# witness, never by a tactic script that stopped matching a reshaped impl.
_PROOF = ("prove_correct windowNumericSql by\n"
          "  loom_solve <;> simp only [windowSql] <;> split_ifs <;> simp_all")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the tactic body retuned, for a correct reshape
    whose residual goal no longer matches the frozen script. The
    `prove_correct windowNumericSql` header is byte-identical in both."""
    return _swap(_impl(body), _PROOF, proof)


# ---- witness preamble. The spec is a `method` contract, so the witness reaches
# ---- the postcondition through Velvet's tester machinery rather than by
# ---- unfolding a predicate. Checked in a file whose `prove_correct` block has
# ---- been stripped, so no tactic script can mask the verdict.
_TESTER = ("extract_program_for windowNumericSql\n"
           "prove_precondition_decidable_for windowNumericSql\n"
           "prove_postcondition_decidable_for windowNumericSql\n"
           "derive_tester_for windowNumericSql\n\n")


def _witness(call):
    """`<tester> args = false` — the extracted program violates the
    postcondition at that literal input. No binder, so no consistency risk."""
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation intact and reproves honestly;
    # none introduces a helper lemma and none weakens the statement.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the rendering DIRECTLY via the transparent post-image
        # function, with no branch of its own. The sole `ensures` is literally
        # `out = windowSql isDecimal innerBase win`, so this is the cheapest
        # HONEST correct impl; the branch is gone, so the frozen script's
        # `split_ifs` has nothing to split and `loom_solve` alone closes.
        "module": _impl_reproved(
            "    let mut out : List Char := []\n"
            "    out := windowSql isDecimal innerBase win\n"
            "    return out",
            "prove_correct windowNumericSql by\n  loom_solve"),
        "rationale": (
            "the post-image is GROUNDED in the three inputs (a total function of "
            "the method's own arguments, no opaque answer key), so reporting it "
            "directly is the honest cheapest CORRECT impl and MUST verify — else "
            "the sole ensures is SPEC-TOO-STRONG, over-fit to the branch-and-"
            "assemble code form. Doubles as evidence the pin is not echo-"
            "vulnerable: because the post-image computes from the inputs, any "
            "WRONG cast placement or template shape still fails it (the nine "
            "rivals below are exactly that). Carries over the sibling's honest "
            "cheapest-impl positive control."),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: invert the outer branch so the CAST-LESS case is handled first
        # and the cast case second. The two arms are independent and each keeps
        # its own value flow, so the frozen tactic script still closes the
        # byte-identical obligation with no retuning.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if !isDecimal then\n"
            "      out := overClause innerBase win\n"
            "    else\n"
            "      let windowed := overClause innerBase win\n"
            "      out := numericCast windowed\n"
            "    return out"),
        "rationale": (
            "a correct impl in the OPPOSITE branch order must verify: the two "
            "arms are independent and the value assigned in each is unchanged, so "
            "the sole ensures still discharges and the frozen script closes as-is. "
            "Ports the sibling's pos-control-branch-reorder. If it cannot verify "
            "=> SPEC-TOO-STRONG (pinned to the branch polarity of the frozen "
            "code rather than to its behaviour)."),
    },
    {
        "id": "pos-control-inline-templates",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: assemble both templates INLINE as raw character-sequence
        # concatenations instead of calling the two pure helpers, and hoist the
        # shared windowed fragment above the branch. Same characters in the same
        # order; the proof unfolds the two helper defs so the residual goal
        # closes. Ports the sibling's pos-control-inner-concat (a local-variable /
        # construction reshape that keeps the contents identical).
        "module": _impl_reproved(
            "    let mut out : List Char := []\n"
            "    let windowed := innerBase ++ \" OVER (\".toList ++ win ++ \")\".toList\n"
            "    if isDecimal then\n"
            "      out := \"CAST(\".toList ++ windowed ++ \" AS NUMERIC)\".toList\n"
            "    else\n"
            "      out := windowed\n"
            "    return out",
            "prove_correct windowNumericSql by\n"
            "  loom_solve <;> simp only [windowSql, numericCast, overClause]"
            " <;> split_ifs <;> simp_all"),
        "rationale": (
            "a correct impl that assembles both templates inline as raw "
            "character-sequence concatenations (rather than through the two pure "
            "helpers) and hoists the shared windowed fragment above the branch "
            "must verify: the emitted characters and their order are identical, so "
            "the sole ensures holds. The proof additionally unfolds the two helper "
            "defs — an honest reproof of the SAME obligation, no new lemma, no "
            "weakening. Ports the sibling's pos-control-inner-concat. If it cannot "
            "verify => SPEC-TOO-STRONG (pinned to the helper-call spelling)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the sibling's admiss-f2p-shaped-input. That
    # case established that a normal input satisfies the sibling's read-only
    # half-permission precondition. This method carries NO `require` clause at
    # all (the pre-conditions region is empty), so nothing could exclude any
    # input and the classic "a normal input is admitted" probe is vacuous here.
    # Re-aimed at the residual admissibility risk on a precondition-free domain:
    # that the post-image is SATISFIABLE by a real computation on every input.
    # The frozen impl discharging the ensures IS that witness. MUST verify.
    # =====================================================================
    {
        "id": "admiss-total-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,
        "rationale": (
            "the method carries no `require`, so the rendering is total over "
            "every (flag, operand text, window text) triple; the frozen impl "
            "discharging the sole ensures is the admissibility witness that the "
            "post-image is satisfiable across that whole domain, on BOTH arms of "
            "the flag. Near-trivial precisely BECAUSE the precondition is empty — "
            "which is the finding: there is no precondition that could be "
            "PRECOND-TOO-STRONG. Re-aimed from the sibling's admiss-f2p-shaped-"
            "input, whose half-permission half has no counterpart on this "
            "referentially-transparent carrier. If it failed => SPEC-"
            "UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (seen to elaborate against the rival and fail on gold) and
    # the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test. All attack the sole ensures; the sub-domain and
    # the probed point differ per rival, so no two lean on the same evidence.
    # =====================================================================
    {
        "id": "uniq-cast-inside-clause",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-CHANGE PLACEMENT, and the discriminating content of the fix:
        # the numeric cast wraps the OPERAND ALONE, so the cast closes before the
        # window template rather than around the whole windowed expression.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if isDecimal then\n"
            "      out := overClause (numericCast innerBase) win\n"
            "    else\n"
            "      out := overClause innerBase win\n"
            "    return out"),
        "refinement": (
            "this is the pre-change rendering: on a fixed-precision decimal "
            "result the numeric cast is placed around the operand alone, so the "
            "cast closes immediately before the window keyword and the windowed "
            "syntax is split. The reported symptom is exactly that — the backend "
            "refuses the statement with a syntax error at the window keyword — so "
            "a faithful counterpart of this shape is the UNPATCHED behaviour and "
            "the failing decimal windowed-aggregate test still errors out. It "
            "would NOT resolve."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: on the "
            "decimal arm the post-image is `numericCast (overClause innerBase "
            "win)` — the cast around the ENTIRE windowed expression — and this "
            "rival produces `overClause (numericCast innerBase) win`, the cast "
            "INSIDE the clause. Distinct character sequences, refuted at "
            "isDecimal=true. If it verified => SPEC-TOO-WEAK (the spec would "
            "admit the very defect the fix corrects)."),
        "witness": _witness(
            'windowNumericSqlTester true ("L".toList) ("p".toList)'),
    },
    {
        "id": "uniq-no-cast-anywhere",
        "kind": "uniqueness",
        "expect": "reject",
        # Forget the numeric cast entirely: return the bare window template on
        # every input, ignoring the flag.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    out := overClause innerBase win\n"
            "    return out"),
        "refinement": (
            "rendering a fixed-precision decimal windowed result with NO numeric "
            "coercion anywhere corresponds to a counterpart that never takes the "
            "decimal arm. The decimal value is then never coerced to a numeric "
            "type, so the backend hands back the wrong value type for the "
            "windowed decimal and the failing test's assertion on the decimal "
            "windowed result does not hold. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the decimal "
            "arm requires the cast wrapper, and this rival emits the bare window "
            "template — the wrapper is missing entirely. Refuted at "
            "isDecimal=true, at operand/window values distinct from every other "
            "witness. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            'windowNumericSqlTester true ("M".toList) ("q".toList)'),
    },
    {
        "id": "uniq-always-cast",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary over-application: wrap the window template in the
        # numeric cast on EVERY input, dropping the flag guard. Correct on the
        # decimal arm, wrong on the other.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    out := numericCast (overClause innerBase win)\n"
            "    return out"),
        "refinement": (
            "always applying the numeric coercion, even for a result that is not "
            "a fixed-precision decimal, corresponds to a counterpart that dropped "
            "the result-type guard. Every non-decimal windowed expression — the "
            "bulk of the passing window suite, over integer and float results — "
            "would then render with a spurious numeric coercion, changing its SQL "
            "and its result type and breaking those currently-passing tests. It "
            "would NOT resolve."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: on the "
            "non-decimal arm the post-image is the BARE window template with no "
            "wrapper, and this rival wraps it. Refuted at isDecimal=FALSE — the "
            "arm the cast-placement rivals do not probe — so the battery "
            "demonstrates the spec's dependence on the flag rather than assuming "
            "it. If it verified => SPEC-TOO-WEAK on the non-decimal sub-domain."),
        "witness": _witness(
            'windowNumericSqlTester false ("N".toList) ("r".toList)'),
    },
    {
        "id": "uniq-flag-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Both arms exchanged: the cast fires when the result is NOT a decimal
        # and is omitted when it is. Each arm is individually well-formed but on
        # the wrong side of the guard, so the rival is wrong on BOTH sub-domains.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if isDecimal then\n"
            "      out := overClause innerBase win\n"
            "    else\n"
            "      out := numericCast (overClause innerBase win)\n"
            "    return out"),
        "refinement": (
            "a counterpart that consulted the result-type guard with the wrong "
            "polarity coerces exactly the windowed results that must NOT be "
            "coerced and leaves the fixed-precision decimal one un-coerced. The "
            "failing decimal test still observes an un-coerced decimal, and the "
            "passing non-decimal window tests all acquire a spurious coercion, so "
            "NEITHER sub-domain resolves."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the decimal "
            "arm must carry the wrapper and the non-decimal arm must not, and the "
            "inverted guard violates both. Refuted at isDecimal=false at a point "
            "distinct from uniq-always-cast (with which it agrees on that arm but "
            "differs on the other), so the guard's polarity is demonstrated at "
            "both values. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            'windowNumericSqlTester false ("O".toList) ("s".toList)'),
    },
    {
        "id": "uniq-double-cast",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS on the decimal arm: it does wrap the whole windowed
        # expression (getting the outer placement right) but ALSO coerces the
        # operand inside the clause, so the coercion appears twice. Agrees with
        # gold on the whole non-decimal arm, hence its own probed point.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if isDecimal then\n"
            "      out := numericCast (overClause (numericCast innerBase) win)\n"
            "    else\n"
            "      out := overClause innerBase win\n"
            "    return out"),
        "refinement": (
            "coercing the operand as well as the whole windowed expression "
            "corresponds to a counterpart that wrapped the entire expression "
            "correctly but FORGOT to render the operand without a coercion of its "
            "own first. The result carries the coercion twice, and the inner one "
            "again closes immediately before the window keyword — re-triggering "
            "the very syntax error the report describes. The failing decimal test "
            "still errors out, so it would NOT resolve. This is the near-miss "
            "that shows the fix needs BOTH halves, not just the outer placement."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the decimal "
            "arm pins the windowed expression to `overClause innerBase win`, "
            "whose operand is `innerBase` VERBATIM — the spec view states the "
            "operand carries no coercion of its own — so a rival substituting "
            "`numericCast innerBase` there yields a distinct character sequence "
            "even though its outer wrapper is right. Refuted at isDecimal=true on "
            "its own operand/window values: it is a strict near-miss of "
            "uniq-cast-inside-clause (correct outer placement, extra inner "
            "coercion) so it gets a point of its own rather than sharing one. "
            "Ports the sibling's uniq-operand-decimal-double-cast."),
        "witness": _witness(
            'windowNumericSqlTester true ("P".toList) ("t".toList)'),
    },
    {
        "id": "uniq-drop-over-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Mechanical structural near-miss: omit the window template's leading
        # separator, concatenating the operand text directly onto the window
        # text. The cast decision itself is kept correct.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    let windowed := innerBase ++ win ++ \")\".toList\n"
            "    if isDecimal then\n"
            "      out := numericCast windowed\n"
            "    else\n"
            "      out := windowed\n"
            "    return out"),
        "refinement": (
            "omitting the template's separator corresponds to a broken template "
            "that ran the operand text straight into the window text with no "
            "window keyword, producing a statement with no window clause at all. "
            "Every windowed test, failing and passing alike, would fail to "
            "compile or execute, so it would NOT resolve. Supporting near-miss "
            "for the structural-shape attack, kept because it is cheap and it "
            "pins a part of the post-image the cast rivals leave untouched."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the "
            "post-image interpolates the operand text, the separator, the window "
            "text and the closing bracket in that order; dropping the separator "
            "yields a sequence equal to neither arm's post-image. Refuted at "
            "isDecimal=true on its own values. Ports the sibling's "
            "uniq-drop-over-keyword."),
        "witness": _witness(
            'windowNumericSqlTester true ("Q".toList) ("u".toList)'),
    },
    {
        "id": "uniq-operands-exchanged",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the ARGUMENTS rather than the result: fill the template's two
        # slots in the wrong order, so the window text is rendered where the
        # operand belongs and vice versa. The cast decision is kept correct.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if isDecimal then\n"
            "      out := numericCast (overClause win innerBase)\n"
            "    else\n"
            "      out := overClause win innerBase\n"
            "    return out"),
        "refinement": (
            "a counterpart that filled the template's two named slots in the "
            "wrong order renders the assembled window clause where the operand "
            "belongs and the operand inside the window parentheses. That is not a "
            "valid windowed expression on any backend, so every windowed test "
            "fails to execute and it would NOT resolve. ADDED beyond the sibling "
            "set: the sibling's carrier reaches the template through positional "
            "concatenation of two same-typed sequences, so its battery never "
            "probes the slot ORDER; this carrier makes the two arguments "
            "independent inputs and the order becomes attackable."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the "
            "post-image is asymmetric in its two string inputs (the operand text "
            "leads, the window text sits inside the parentheses), so exchanging "
            "them yields a different sequence for any pair of distinct values. "
            "Refuted at isDecimal=false on its own values, covering the ARGUMENT "
            "structure rather than the cast decision. If it verified => "
            "SPEC-TOO-WEAK (the ensures would not pin which input goes where)."),
        "witness": _witness(
            'windowNumericSqlTester false ("R".toList) ("v".toList)'),
    },
    {
        "id": "uniq-window-text-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage rival for `win`: IGNORE the window-clause input
        # entirely, emitting empty parentheses. The cast decision and the operand
        # placement are both kept correct, so this isolates the `win` binder.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if isDecimal then\n"
            "      out := numericCast (overClause innerBase [])\n"
            "    else\n"
            "      out := overClause innerBase []\n"
            "    return out"),
        "refinement": (
            "a counterpart that never interpolated the assembled window clause "
            "renders every windowed expression over an empty frame, discarding "
            "the partitioning and ordering the caller asked for. The rows come "
            "back computed over the wrong frame, so the failing test's expected "
            "per-partition values do not appear and the passing partition/order "
            "window tests break too. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the "
            "post-image interpolates `win` inside the parentheses on BOTH arms, "
            "so an impl that discards it violates the ensures at every non-empty "
            "window text. This is the binder-coverage rival for `win` — it is the "
            "rival that would slip through if no witness varied that input — and "
            "it is refuted at isDecimal=false on its own values. If it verified "
            "=> SPEC-TOO-WEAK (the ensures would not force the window text to be "
            "used at all)."),
        "witness": _witness(
            'windowNumericSqlTester false ("S".toList) ("w".toList)'),
    },
    {
        "id": "uniq-nondecimal-operand-cast",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's OPERAND-LEVEL coercion class, ported in the direction
        # that IS wrong on this carrier: keep the decimal arm exactly right, and
        # on the NON-decimal arm coerce the operand alone. This is the only rival
        # that pins `innerBase`'s verbatim-ness on the non-decimal arm — every
        # other rival either agrees with gold across that whole arm or differs
        # from this one on it, so the point is otherwise unattacked.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    if isDecimal then\n"
            "      out := numericCast (overClause innerBase win)\n"
            "    else\n"
            "      out := overClause (numericCast innerBase) win\n"
            "    return out"),
        "refinement": (
            "a counterpart that coerced the operand on the arm where the "
            "windowed result is NOT a fixed-precision decimal renders a "
            "coercion no caller asked for, and renders it INSIDE the window "
            "syntax, where it closes immediately before the window keyword. "
            "Every currently-passing non-decimal windowed test — the bulk of the "
            "window suite, over integer and float results — acquires that "
            "coercion and errors out at the window keyword, so it would NOT "
            "resolve. Ports the sibling's uniq-nondecimal-ignore-operand-cast "
            "class in the direction that is observably wrong here: the sibling "
            "renders its operand through a FOURTH input on this arm, so its "
            "rival STRIPS a coercion; here the operand is verbatim by "
            "definition, so the wrong move is to ADD one."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: on the "
            "non-decimal arm the post-image is `overClause innerBase win`, whose "
            "operand is `innerBase` VERBATIM, so substituting `numericCast "
            "innerBase` there yields a distinct character sequence. Refuted at "
            "isDecimal=false on its own operand/window values. It is the "
            "non-decimal-arm counterpart of uniq-double-cast (which adds the "
            "same inner coercion on the DECIMAL arm) and the only rival pinning "
            "the operand's verbatim-ness on this arm. If it verified => "
            "SPEC-TOO-WEAK on the non-decimal sub-domain."),
        "witness": _witness(
            'windowNumericSqlTester false ("U".toList) ("x".toList)'),
    },
    {
        "id": "uniq-partial-empty-window",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN rival: correct on EVERY input with a non-empty window
        # clause, and wrong only at the `win = []` boundary, where it drops the
        # numeric cast. Agrees with gold everywhere the other rivals are probed,
        # so it can only be caught at the boundary point.
        "module": _impl(
            "    let mut out : List Char := []\n"
            "    let windowed := overClause innerBase win\n"
            "    if isDecimal && win != [] then\n"
            "      out := numericCast windowed\n"
            "    else\n"
            "      out := windowed\n"
            "    return out"),
        "refinement": (
            "a counterpart that applied the numeric coercion only when the "
            "assembled window clause is non-empty leaves a fixed-precision "
            "decimal windowed expression un-coerced whenever the frame text comes "
            "out empty — a windowed aggregate with neither partitioning nor "
            "ordering. The decimal value is then returned un-coerced on that "
            "input shape, so the decimal windowed assertion does not hold there. "
            "It would NOT resolve. ADDED beyond the sibling set: the sibling's "
            "rivals all split on the two flags, never on the window text's own "
            "emptiness, and this carrier exposes that boundary as a free input."),
        "rationale": (
            "REJECT from `out = windowSql isDecimal innerBase win`: the ensures "
            "is unconditional in `win`, so the decimal arm must carry the wrapper "
            "even when the window text is empty. Refuted at the "
            "`win = []` BOUNDARY with isDecimal=true — a point no other witness "
            "probes, and the only point at which this rival differs from gold at "
            "all, so it demonstrates a genuine partial-domain sub-domain instead "
            "of claiming one. If it verified => SPEC-TOO-WEAK (domain-"
            "incomplete)."),
        "witness": _witness(
            'windowNumericSqlTester true ("T".toList) ([])'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery carries 12 SPEC cases
# (2 soundness, 1 admissibility, 9 uniqueness — of which 2 are frame-mutation)
# plus 2 AXIOM_TESTS. Every one is accounted for below. Case-count parity is NOT
# the target: the sibling contracts a FOUR-input function (its operand text, its
# window text, the windowed result's decimal-ness, and the OPERAND's own declared
# decimal-ness) whose model also carries a `compile_operand` axiom, while this
# bundle models the purely functional three-input core with no axioms and folds
# the operand's own coercion into the definition of `innerBase`. That narrowing
# is what retires both frame probes. It retires NO uniqueness rival: the one
# rival whose sibling form is a no-op here (uniq-nondecimal-ignore-operand-cast)
# is ported with its direction inverted, since folding the operand's coercion
# into `innerBase` makes ADDING one the wrong move where STRIPPING one was.
#
#   sibling case                          -> here                        disposition
#   ------------------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-control-branch-reorder  PORTED
#   pos-control-inner-concat              -> pos-control-inline-templates PORTED
#                                            (reshaped: the sibling's fresh-copy
#                                            construction has no counterpart on an
#                                            immutable carrier, so the reshape is
#                                            re-aimed at the template assembly)
#   (none)                                -> pos-control-direct          ADDED
#                                            (honest cheapest correct impl; the
#                                            grounded-pin / echo control)
#   admiss-f2p-shaped-input               -> admiss-total-domain         RE-AIMED
#                                            (no `require` clause exists here, so
#                                            the precondition-establishability half
#                                            is vacuous; re-aimed at post-image
#                                            satisfiability over the total domain)
#   frame-mut-operand-append              -> (none)                      VACUOUS
#   frame-mut-window-append               -> (none)                      VACUOUS
#                                            (both: referential transparency — no
#                                            heap, no aliasing, no permission, no
#                                            `mut` parameter, so no read-only input
#                                            to overwrite. No substitute fabricated.)
#   uniq-cast-around-operand              -> uniq-cast-inside-clause     PORTED
#   uniq-no-cast-decimal                  -> uniq-no-cast-anywhere       PORTED
#   uniq-always-cast                      -> uniq-always-cast            PORTED
#   uniq-swap-branches                    -> uniq-flag-inverted          PORTED
#   uniq-operand-decimal-double-cast      -> uniq-double-cast            PORTED
#   uniq-drop-over-keyword                -> uniq-drop-over-separator    PORTED
#   uniq-nondecimal-ignore-operand-cast   -> uniq-nondecimal-operand-cast PORTED,
#                                            DIRECTION INVERTED. The sibling's rival
#                                            STRIPS the operand's own coercion on the
#                                            non-cast arm, which needs its fourth
#                                            input (the operand's own declared
#                                            decimal-ness). Here `innerBase` is by
#                                            definition the operand text already
#                                            carrying no coercion, so stripping one is
#                                            a no-op and that DIRECTION is gold. The
#                                            CLASS is still attackable, and is
#                                            attacked: the post-image interpolates
#                                            `innerBase` VERBATIM on the non-decimal
#                                            arm, so ADDING a coercion around the
#                                            operand alone there is observably wrong
#                                            and refutable at a literal input.
#                                            Measured: rival build exit 1, witness
#                                            exit 0 against the rival, exit 1 against
#                                            gold by `decide` proving the tester true.
#                                            An earlier revision of this manifest
#                                            recorded the whole class as collapsed by
#                                            the carrier; that was wrong — only one
#                                            direction collapses — and no other rival
#                                            pins the operand on this arm.
#   (none)                                -> uniq-operands-exchanged     ADDED
#   (none)                                -> uniq-window-text-dropped    ADDED
#   (none)                                -> uniq-partial-empty-window   ADDED
#                                            (three attacks the sibling's carrier
#                                            cannot express: it reaches the template
#                                            by positional concatenation of code-
#                                            point lists, so slot ORDER, whether the
#                                            window text is used at all, and the
#                                            empty-window boundary are not
#                                            attackable there. Here all three inputs
#                                            are free and independent.)
#   AXIOM_TESTS (ax-sound / ax-cover
#     for compile_operand)                -> (none)                      DROPPED
#                                            (this bundle axiomatizes nothing — empty
#                                            `axioms` region, no axiom_check.py — and
#                                            the axiom lane is G-AX's job; G-PBT
#                                            ignores AXIOM_TESTS regardless.)
#
# INDEPENDENT AUDIT (adversarial re-derivation of this port; every case rebuilt).
# All 10 witnesses were rebuilt twice from the frozen file: rival exit 0, gold
# exit 1, every gold-side error the kernel's `decide` proved the proposition
# false — a semantic refutation, not a missing name, type error or stuck
# reduction. Three `= true` controls against gold elaborate (exit 0), so the
# tester demonstrably decides on this carrier.
#
# Beyond the shipped rivals, three NEW wrong impls were probed against the frozen
# spec and ALL were rejected with discriminating witnesses, so none is a spec
# hole: a coercion around the operand alone on the non-decimal arm (now shipped
# as uniq-nondecimal-operand-cast); a rival correct except at the
# `innerBase = []` boundary; and a lowercase spelling of the coercion keywords.
# Three NEW correct reshapes were probed for SPEC-TOO-STRONG: a fully
# left-associated raw concatenation and a `String`-round-trip assembly both
# VERIFY (exit 0), so the sole ensures is not over-fit to the frozen code's
# shape. A third — the outer branch written as `match isDecimal with` — could not
# be landed for a TOOLING reason, not a spec one: the surgery is rejected before
# any obligation is considered, with `Failed to parse an assertion without names:
# WPGen (match isDecimal with ...)`, i.e. the weakest-precondition generator does
# not accept a `match` whose arms assign to a `mut` local. Recorded as a backend
# limitation; the two `if`-shaped reshapes cover the same soundness question.
#
# CLOSED BY THE SEMANTICS, and NOT a hole: the divergence class. The sibling
# carries no divergence case, so nothing was omitted from the port. An earlier
# revision of this block recorded an OPEN HOLE here, on the ground that this bundle
# runs under `partial` termination semantics and MEASURABLY admits a
# non-terminating rival that returns the wrong value on every input at exit 0.
# Both halves are withdrawn. The frozen file sets
# `set_option loom.semantics.termination "total"` and opens `TotalCorrectness`, as
# do all 500 velvet bundles; none sets `partial`, and the `set_option` elaborator
# itself runs `openScope `TotalCorrectness`
# (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the `open`
# cannot disagree. Under `total` a postcondition is claimed of ALL runs, so the
# verifier demands a decreasing measure on every loop and discharges its descent.
# Two further facts about THIS cell make the class doubly inapplicable. The frozen
# impl contains no loop and no recursion at all, so there is no repetition site a
# diverging rival could occupy without replacing the implementation wholesale. And
# when a loop is spliced in anyway, it is rejected: `let mut q : Nat := 1;
# while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q do q := q` at the
# impl anchor, proof reduced to a bare `loom_solve`, exits 1 on the measure's own
# goal, `case «decreasing_1: q»`, residual `q < q`. That is the decisive shape,
# since a measure-less loop could be dismissed as tripping only the annotation
# linter. So there is no verify-does-not-imply-resolve break, and nothing to
# escalate. No reject case is shipped, for a witness-contract reason rather than a
# spec one: the refusal fires on the `method` command, so the rival's module never
# compiles and the witness the gate builds from it cannot elaborate.
# ---------------------------------------------------------------------------
