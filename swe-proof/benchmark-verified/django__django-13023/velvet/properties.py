"""properties.py — G-PBT falsification battery for django__django-13023 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the ``-- impl-start``
/ ``-- impl-end`` region — which the consumer spec view elides — and, for the
soundness positives, the elided ``prove_correct toDecimal`` tactic body, are
changed, so ``markers.same_spec`` holds and the ``prove_correct toDecimal``
obligation survives with a byte-identical ``method``/``ensures`` header) and
swaps in a candidate implementation, checked by the real verifier.
``expect="verify"`` passes iff (in scope AND verifies); ``expect="reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method):

  toDecimal (isNone isFloat : Bool) (floatRes : DecimalVal) (conv : ConvResult)
      return (out : PyResult)
    ensures out = toDecimalResult isNone isFloat floatRes conv          [C1]
    ensures isNone = true → out = retNone                              [C2]
    ensures (isNone = false ∧ isFloat = true) → out = ret floatRes     [C3]
    ensures ∀ d, (¬none ∧ ¬float ∧ conv = converted d) → out = ret d   [C4]
    ensures ∀ e, (¬none ∧ ¬float ∧ conv = raised e ∧ recoverable e)
              → out = validationError                                  [C5]
    ensures ∀ e, (¬none ∧ ¬float ∧ conv = raised e ∧ ¬recoverable e)
              → out = propagated e                                     [C6]

The operation interprets an arbitrary input as a fixed-precision decimal. Two
fast paths (a null input, a float input) short-circuit; otherwise the outcome of
the interpretation attempt (``conv``) decides: a produced value is returned, a
recoverable interpretation failure is normalised to the field's invalid-value
error, and any non-recoverable failure propagates.

WHICH CLAUSE CONSTRAINS THE IMPL, AND HOW IT IS GROUNDED. C1 pins the WHOLE
result to the transparent total function ``toDecimalResult`` of the method's own
inputs (``isNone``/``isFloat``/``floatRes``/``conv``); C2–C6 restate the same
decision case-by-case. Both ``toDecimalResult`` and ``isRecoverable`` are plain
``def``s over the input carrier and the ``axioms`` region is EMPTY (mapping.md
§3), so the post-image is grounded in the inputs — there is no opaque answer-key
to echo. Every uniqueness rival therefore diverges from ``toDecimalResult`` at a
CONCRETE input, and the witness refutes it there directly.

  THE BEHAVIOURAL DISCRIMINATOR. The pre-change body normalised only ONE failure
  kind (``invalidOperation``); the other two recoverable kinds (``typeError``,
  ``valueError``) escaped raw. The fix widens the normalised family to all three
  recoverable kinds (``isRecoverable`` returns true for exactly
  {invalidOperation, typeError, valueError}). The failing test hands the field a
  batch of inputs whose interpretation fails with a recoverable kind and asserts
  each surfaces as the field's invalid-value error rather than a raw exception.
  C1/C5/C6 sense it: for every recoverable ``e``, ``out`` must be
  ``validationError``, never ``propagated e``.

WITNESS MECHANICS ON THIS BUNDLE. The tester+``decide`` path
(``derive_tester_for`` → ``…Tester args = false``) is DEAD here, re-measured by
the audit: ``prove_postcondition_decidable_for toDecimal`` leaves one unsolved
``Decidable`` goal per quantified clause, and the binding one is
``Decidable (∀ d : DecimalVal, …)`` — ``DecimalVal`` wraps an ``Int``, so its
domain is infinite and no instance is derivable. (The ``∀ e : ExcKind`` goals are
NOT the obstruction: ``ExcKind`` is a four-constructor ``DecidableEq`` enum and
is finitely decidable; the original note credited them too, which the audit
corrected.) But C1's post-image ``toDecimalResult`` is a TRANSPARENT total ``def``.
So each witness extracts the executable program (``extract_program_for
toDecimal`` → ``toDecimalExec``) and refutes C1 directly at one concrete input:

    (match toDecimalExec <ins> with | DivM.res r => r | _ => <filler>)
        ≠ toDecimalResult <ins>

i.e. the rival's own output DIFFERS from what C1 demands — a direct C1 violation
the elaborator sees by ``decide`` (the input is a concrete literal over the
finite-shape carrier reachable arms). Against the FROZEN solution the same
statement is provably FALSE (gold's ``…Exec`` reduces to exactly
``toDecimalResult`` at that input), so ``decide`` proves the ``≠`` false and the
witness FAILS on gold — the required discrimination. No witness binds a
hypothesis (every input is a concrete literal), so the gate's consistency probe
is a no-op. No banned token (sorry/admit/native_decide/axiom/opaque). Every
witness below was run against both its rival (ELABORATES, exit 0) and the frozen
solution (FAILS, exit 1) with two real ``scripts/lean_verify.sh`` builds.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling explicitly records
    the class as inapplicable (its DEFENDED SURFACE note: ``kind`` is a PLAIN
    integer acceptance tag with NO heap permission anywhere, ``has_readonly_input
    = False``). Lean/Velvet are referentially transparent: every input is an
    immutable value, no ``mut`` binder, no heap, no aliasing, no permission
    system. No read-only input to overwrite; no substitute probe fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image is the transparent
    ``toDecimalResult`` over the method's own inputs, not an axiomatized oracle;
    the ``axioms`` region is empty. The cheapest correct impls are carried as
    positive controls; the value-pin rivals (echo-const-*, echo-fromfloat-kind2)
    port the nagini GROUNDED-ORACLE attacks (a fabricated / cross-source token
    for the produced value cannot equal what C1/C4/C3 force).
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

INDEPENDENT AUDIT PROBES (no spec hole found, recorded so the next reader need
not re-spend the builds). Four NEW wrong impls were built against the frozen
spec and all four were REJECTED with a semantic unsolved goal on the expected
clause: normalising the non-recoverable kind too (a blanket catch-all, residual
``ensures_1``/C6); making the produced-value leg wrong only on a SUB-DOMAIN of
the payload (``d.payload < 0`` → the field error, residual ``ensures_3``/C4 with
goal ``0 ≤ d.payload``, so C4's ``∀ d`` is genuinely quantified and not
witness-shaped); relabelling the propagated kind (kept, see
weak-propagate-wrong-kind); and checking the float path first WITHOUT re-guarding
on null, which diverges from gold only on the ``isNone ∧ isFloat`` overlap
(residual ``ensures_5``/C2 — so the spec does pin that overlap). Three NEW
CORRECT reshapes were built and all three VERIFIED, so the spec is not
over-strong on them: naming the escaping kind concretely as ``ExcKind.other``
(observationally equal to gold since ``¬isRecoverable e → e = other``); a single
``match isNone, isFloat with`` over the flag pair instead of nested ``if``; and
the recoverable guard NEGATED with its arms swapped.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real CPython ``decimal`` stdlib; this
bundle is axiom-free (mapping.md §3: the fix is an exception-classification
decision modeled deeply in the ``pure`` region, no callee to axiomatize, G-AX
auto-skips), and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13023"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole frozen impl body (text strictly between the
# ---- method's -- impl-start and -- impl-end, comments EXCLUDED — the anchor is
# ---- the `let result … return result` expression, which is unique in the file
# ---- and lies wholly inside the single impl region). Every variant replaces
# ---- exactly this text, so each edit is confined to the elided impl region and
# ---- same_spec holds by construction (both facts asserted at load by _swap).
_GOLD_IMPL = (
    "    let result : PyResult :=\n"
    "      if isNone then PyResult.retNone\n"
    "      else\n"
    "        if isFloat then PyResult.ret floatRes\n"
    "        else\n"
    "          match conv with\n"
    "          | ConvResult.converted d => PyResult.ret d\n"
    "          | ConvResult.raised e =>\n"
    "              if isRecoverable e then PyResult.validationError\n"
    "              else PyResult.propagated e\n"
    "    return result"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- the frozen proof, verbatim. Reject rivals KEEP it unchanged (their
# ---- rejection is carried by the witness, not by whether the frozen tactic
# ---- happens to break on the reshape). The soundness positives retune only
# ---- THIS elided tactic body (the `method`/`ensures` header — the obligation —
# ---- is byte-identical), because their reshaped impl splits the goal on a
# ---- different scrutinee than the frozen `simp_all` closes on.
_PROOF = (
    "prove_correct toDecimal by\n"
    "  loom_solve\n"
    "  simp_all [toDecimalResult, isRecoverable]"
)

assert _BASE.count(_PROOF) == 1, "frozen proof region drifted; update _PROOF"


def _impl(body):
    """Full Solution.lean variant with only the impl body replaced (spec view and
    frozen proof untouched)."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the (elided) prove_correct tactic body retuned, for
    correct reshapes whose residual goal needs a different case split. The
    `method`/`ensures` obligation header is untouched, so same_spec holds and the
    obligation survives byte-identically."""
    return _swap(_impl(body), _PROOF, proof)


# ---- witness builder. The tester+`decide` path is dead (the postcondition
# ---- quantifies over the infinite-domain `DecimalVal` and over `ExcKind`, so
# ---- `prove_postcondition_decidable_for` cannot build a Decidable instance).
# ---- Instead extract the executable program and refute C1 directly against the
# ---- TRANSPARENT `toDecimalResult` at one concrete input. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. Binds nothing (literal input), so the consistency probe is a no-op.
def _witness(ins, filler="PyResult.retNone"):
    return (
        "extract_program_for toDecimal\n\n"
        "example :\n"
        f"    (match toDecimalExec {ins} with\n"
        f"     | DivM.res r => r | _ => {filler})\n"
        f"    ≠ toDecimalResult {ins} := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the clause is SPEC-TOO-STRONG. Each keeps the
    # byte-identical obligation header; only the elided impl and prove_correct
    # tactic body are reshaped. Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-explicit-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: instead of the `isRecoverable e` membership test, match the
        # failure kind EXPLICITLY, normalising each of the three recoverable kinds
        # to the field error and propagating only the non-recoverable one. Same
        # decision as gold, spelled arm-by-arm; C1–C6 still discharge. The residual
        # goal now splits on `conv`/`e`, so the tactic body is retuned to case on
        # them before `simp_all` (the obligation header is untouched).
        "module": _impl_reproved(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              match e with\n"
            "              | ExcKind.invalidOperation => PyResult.validationError\n"
            "              | ExcKind.typeError => PyResult.validationError\n"
            "              | ExcKind.valueError => PyResult.validationError\n"
            "              | ExcKind.other => PyResult.propagated e\n"
            "    return result",
            "prove_correct toDecimal by\n"
            "  loom_solve <;>\n"
            "    (try rcases conv with d | e) <;>\n"
            "    (try cases e) <;>\n"
            "    simp_all [toDecimalResult, isRecoverable]"),
        "rationale": (
            "structurally different CORRECT reshape: replace the recoverable-family "
            "membership test with an explicit per-kind match that normalises each "
            "of the three recoverable kinds and propagates only the non-recoverable "
            "one — the SAME decision as gold, arm-by-arm. C1 (`out = "
            "toDecimalResult …`) and C2–C6 all discharge; the tactic body is "
            "retuned to case on `conv`/`e` (the obligation header is byte-identical, "
            "same_spec holds). Ports the nagini pos-control-combined-except "
            "soundness point — that catching every recoverable failure and "
            "re-reporting the uniform field error is observationally the fix — "
            "re-expressed as the carrier's explicit kind match. Must verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-reorder-fastpaths",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: check the float fast path BEFORE the null fast path (nesting the
        # null test inside the non-float branch's mirror, since Velvet forbids
        # `else if`). Reordering the two disjoint fast-path guards preserves every
        # clause; the reject decision is kept verbatim. The residual goal splits on
        # the two Bools, so the tactic body cases on them before `simp_all`.
        "module": _impl_reproved(
            "    let result : PyResult :=\n"
            "      if isFloat then\n"
            "        (if isNone then PyResult.retNone else PyResult.ret floatRes)\n"
            "      else\n"
            "        if isNone then PyResult.retNone\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              if isRecoverable e then PyResult.validationError\n"
            "              else PyResult.propagated e\n"
            "    return result",
            "prove_correct toDecimal by\n"
            "  loom_solve <;>\n"
            "    (try cases isNone) <;> (try cases isFloat) <;>\n"
            "    simp_all [toDecimalResult, isRecoverable]"),
        "rationale": (
            "second correct shape: check the float fast path before the null fast "
            "path (the null test guards the float branch too, so the null-input "
            "outcome `retNone` is preserved even when reordered). Reordering the two "
            "disjoint fast-path guards preserves every value-pin (C2/C3) and the "
            "reject decision is kept verbatim (C5/C6), so C1 still discharges. Ports "
            "the nagini pos-control-reorder-fastpaths. Must verify, else "
            "SPEC-TOO-STRONG (over-fit to the null-first spelling)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-accepted-shape. That case
    # made an in-region self-call to discharge the precondition on a normal
    # F2P-shaped input. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude a normal input and
    # the classic probe is vacuous. Re-aimed at the residual total-domain risk:
    # that the six-clause post-image is jointly SATISFIABLE by a gold-shaped
    # computation. The frozen impl discharging all six ensures IS that witness.
    # MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the operation is total over every "
            "combination of the two fast-path flags, the produced value, and the "
            "interpretation outcome; the gold impl discharging all six ensures is "
            "the admissibility witness that the post-image (C1 plus the five "
            "case-wise pins C2–C6) is jointly satisfiable. Near-trivial precisely "
            "because the precondition is empty. Re-aimed from the nagini "
            "admiss-accepted-shape, whose precondition-admits-a-normal-input "
            "self-call has no counterpart on this referentially-transparent carrier "
            "with no require clause. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. The witnesses vary all four
    # input binders: `conv` (converted vs raised, and every ExcKind arm),
    # `isNone` (weak-drop-none), `isFloat` (echo-const-kind1), and `floatRes`
    # (echo-fromfloat-kind2) — so no binder is held fixed across the battery.
    # =====================================================================
    {
        "id": "weak-prepatch-only-invalidop",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: normalise ONLY the invalidOperation failure;
        # every other reported failure (incl. the recoverable typeError/valueError)
        # propagates raw. Correct on invalidOperation and on `other`; WRONG on
        # typeError and valueError.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              if e = ExcKind.invalidOperation then PyResult.validationError\n"
            "              else PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "this IS the pre-change behaviour: only the invalid-numeric-operation "
            "failure is normalised to the field error; the other two recoverable "
            "interpretation failures escape raw to the caller. Its faithful real "
            "patch is the unpatched repo, whose narrow handler re-raises a raw "
            "exception on those inputs; the failing test hands the field values "
            "whose interpretation fails recoverably and asserts each surfaces as the "
            "field's invalid-value error, which the raw escape does not produce — so "
            "it would NOT resolve. This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1/C6 (`out = toDecimalResult …`): on a recoverable "
            "non-invalidOperation failure the spec forces `validationError` while "
            "the rival yields `propagated e`. Refuted at a `valueError` "
            "interpretation outcome (conv = raised valueError, both fast-path flags "
            "false). If it verified => SPEC-TOO-WEAK (admits the pre-patch bug)."
        ),
        "witness": _witness(
            "false false { payload := 0 } (ConvResult.raised ExcKind.valueError)"),
    },
    {
        "id": "partial-domain-typeerror-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: normalise invalidOperation and valueError but NOT
        # typeError. Correct on two of the three recoverable kinds; on typeError
        # (the exact kind the problem statement reports) the failure escapes raw.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              match e with\n"
            "              | ExcKind.invalidOperation => PyResult.validationError\n"
            "              | ExcKind.valueError => PyResult.validationError\n"
            "              | _ => PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "a patch widening the normalised family to two of the three recoverable "
            "kinds but OMITTING the wrong-operand-type kind still lets that failure "
            "escape raw — precisely the case the problem statement reports (an "
            "unexpected object type produces a raw type error instead of the field's "
            "invalid-value error). The failing test includes such inputs and asserts "
            "the field error, so the faithful real patch FAILS the F2P on that "
            "sub-domain and does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1/C5 (`out = toDecimalResult …`): the type-error failure "
            "is recoverable, so C5 forces `validationError`, while the rival yields "
            "`propagated typeError`. A genuine partial-domain break — correct on the "
            "other two recoverable kinds. Refuted at conv = raised typeError (a "
            "DISTINCT ExcKind arm from the prepatch rival's valueError witness, so "
            "the `conv` binder is varied). If it verified => SPEC-TOO-WEAK "
            "(domain-incomplete)."
        ),
        "witness": _witness(
            "false false { payload := 0 } (ConvResult.raised ExcKind.typeError)"),
    },
    {
        "id": "cflow-swallow-recoverable",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow-effect: on a recoverable failure, SWALLOW it and return the
        # null token instead of reporting the field error. No raw escape, but a
        # silent accept — the field would treat an invalid value as absent.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              if isRecoverable e then PyResult.retNone\n"
            "              else PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "a patch that catches the recoverable failure and RETURNS the null token "
            "instead of reporting the field error would silently accept an invalid "
            "value: the failing test asserts the field's invalid-value error is "
            "reported, which a silent null-return does not produce, so it would NOT "
            "resolve — and it also corrupts every downstream consumer expecting "
            "either a value or the error."
        ),
        "rationale": (
            "REJECT from C1/C5 (`out = toDecimalResult …`): on a recoverable failure "
            "C5 forces `validationError`, while the rival yields `retNone` — a "
            "report-vs-swallow difference the value-and-outcome carrier senses. "
            "Refuted at conv = raised invalidOperation. If it verified => "
            "SPEC-TOO-WEAK (the reporting outcome would be unpinned)."
        ),
        "witness": _witness(
            "false false { payload := 0 } (ConvResult.raised ExcKind.invalidOperation)",
            filler="PyResult.ret { payload := 99 }"),
    },
    {
        "id": "cflow-reraise-raw",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow-effect / literal anti-fix: drop the handler entirely — every
        # reported failure propagates raw, even the recoverable ones. This is the
        # behaviour the fix eliminates.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e => PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "dropping the normalisation entirely (re-raise every reported failure "
            "raw) is the literal anti-fix: the caller sees a raw exception for every "
            "recoverable interpretation failure, exactly the behaviour the fix "
            "eliminates. The failing test asserts the field's invalid-value error, "
            "not a raw exception, so it would NOT resolve on any recoverable input."
        ),
        "rationale": (
            "REJECT from C1/C5 (`out = toDecimalResult …`): every recoverable "
            "failure must normalise to `validationError`, but this rival propagates "
            "it raw. Refuted at conv = raised invalidOperation. Distinct from "
            "cflow-swallow (which returns the null token) in the WRONG outcome it "
            "produces (raw propagation vs silent null), both refuted from C5 but "
            "attributing a different failure. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "false false { payload := 0 } (ConvResult.raised ExcKind.invalidOperation)"),
    },
    {
        "id": "weak-drop-none-fastpath",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the null fast path: a null input falls through to the interpretation
        # branch. ADDED to VARY the `isNone` binder — every other reject witness
        # holds isNone=false, so without this case a rival mishandling only the
        # null input would verify and the battery would never notice. On a null
        # input this rival returns the interpretation branch's value, not retNone.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isFloat then PyResult.ret floatRes\n"
            "      else\n"
            "        match conv with\n"
            "        | ConvResult.converted d => PyResult.ret d\n"
            "        | ConvResult.raised e =>\n"
            "            if isRecoverable e then PyResult.validationError\n"
            "            else PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "dropping the null fast path makes a null input fall through to the "
            "interpretation attempt, so the field would try to interpret the null as "
            "a decimal instead of returning it unchanged. A real patch of this shape "
            "would change the accepted-null behaviour the passing tests depend on "
            "(a null input must be returned unchanged), so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1/C2 (`out = toDecimalResult …`): C2 forces `retNone` when "
            "`isNone = true`, but with the fast path gone the rival returns the "
            "interpretation branch's value. Refuted at isNone = true (with a "
            "converted outcome) — the ONLY witness varying the `isNone` binder, so "
            "the null sub-domain is not left unpinned. If it verified => "
            "SPEC-TOO-WEAK (the null fast path would be free)."
        ),
        "witness": _witness(
            "true false { payload := 0 } (ConvResult.converted { payload := 5 })",
            filler="PyResult.ret { payload := 5 }"),
    },
    {
        "id": "weak-echo-const-converted",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-pin: on a produced-value outcome return a FABRICATED constant token
        # instead of the produced value. Ports the nagini weak-echo-const-kind2.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret { payload := 1 }\n"
            "          | ConvResult.raised e =>\n"
            "              if isRecoverable e then PyResult.validationError\n"
            "              else PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "a faithful real patch whose success branch returns a FABRICATED constant "
            "decimal (not the value the interpretation attempt produced) returns the "
            "wrong number for every accepted value, so the passing to-python test "
            "(which observes the produced value's exact content) FAILS and it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C1/C4 (`out = toDecimalResult …`): C4 pins the returned "
            "value to the produced token `d`, but the rival returns a fabricated "
            "constant not provably equal to it. Refuted at conv = converted "
            "{payload := 5} (the produced value differs from the constant 1). Ports "
            "the nagini weak-echo-const-kind2 (grounded-oracle value pin). If it "
            "verified => SPEC-TOO-WEAK (a wrong produced value would slip through)."
        ),
        "witness": _witness(
            "false false { payload := 0 } (ConvResult.converted { payload := 5 })"),
    },
    {
        "id": "weak-echo-fromfloat-converted",
        "kind": "uniqueness",
        "expect": "reject",
        # Cross-source value-pin: on a produced-value outcome return the FLOAT
        # path's value instead of the produced value. Ports the nagini
        # weak-echo-fromfloat-kind2. Refuted where floatRes ≠ the produced value.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret floatRes\n"
            "          | ConvResult.raised e =>\n"
            "              if isRecoverable e then PyResult.validationError\n"
            "              else PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "returning the FLOAT path's produced value (a precision-rounded decimal) "
            "for a non-float accepted input yields a different number than the "
            "interpretation attempt produced, so the passing to-python test (which "
            "observes the accepted value's exact content) FAILS and it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1/C4 (`out = toDecimalResult …`): C4 pins the returned "
            "value to the interpretation-produced token `d`; `floatRes` is a DISTINCT "
            "input with no proven equality to it. Refuted at conv = converted "
            "{payload := 5} with floatRes = {payload := 7} — the ONLY witness "
            "varying the `floatRes` binder to a value distinct from the produced "
            "token. Ports the nagini weak-echo-fromfloat-kind2 (cross-callee echo). "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "false false { payload := 7 } (ConvResult.converted { payload := 5 })"),
    },
    {
        "id": "weak-echo-const-float",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-pin on the FLOAT branch: return a FABRICATED constant instead of
        # the float path's produced value. Ports the nagini weak-echo-const-kind1.
        # VARIES the `isFloat` binder (isFloat = true).
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret { payload := 1 }\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              if isRecoverable e then PyResult.validationError\n"
            "              else PyResult.propagated e\n"
            "    return result"),
        "refinement": (
            "a faithful real patch whose float branch returns a FABRICATED constant "
            "decimal (not the float path's produced value) returns the wrong number "
            "for every float input, so the passing to-python test (which observes the "
            "float result's exact rounded content) FAILS and it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1/C3 (`out = toDecimalResult …`): C3 pins the float-branch "
            "result to `floatRes`, but the rival returns a fabricated constant not "
            "provably equal to it. Refuted at isFloat = true with floatRes = "
            "{payload := 5} — the ONLY witness varying the `isFloat` binder to true, "
            "so the float fast path is not left unpinned. Ports the nagini "
            "weak-echo-const-kind1 (float-branch value pin). If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "false true { payload := 5 } (ConvResult.converted { payload := 0 })"),
    },
    {
        "id": "weak-propagate-wrong-kind",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. C6 is the ONLY independent post-image clause no rival
        # above actually breaks: measured, every one of the eight rivals fails on
        # `ensures_6` (C1) plus exactly one of `ensures_2..5` (C5/C4/C3/C2), and
        # NONE fails `ensures_1` (C6). Each of them agrees with gold on the whole
        # non-recoverable leg, so the identity of the kind C6 forces to be
        # propagated was unpinned by the battery. This rival keeps the
        # recoverable/non-recoverable SPLIT verbatim and gold's whole
        # value-and-fast-path behaviour, and diverges only in WHICH kind it
        # reports on the non-recoverable leg: it collapses the escaping failure to
        # the invalid-numeric-operation kind. Measured: the residual goal is
        # `ensures_1` (C6) — the clause no other case reaches.
        "module": _impl(
            "    let result : PyResult :=\n"
            "      if isNone then PyResult.retNone\n"
            "      else\n"
            "        if isFloat then PyResult.ret floatRes\n"
            "        else\n"
            "          match conv with\n"
            "          | ConvResult.converted d => PyResult.ret d\n"
            "          | ConvResult.raised e =>\n"
            "              if isRecoverable e then PyResult.validationError\n"
            "              else PyResult.propagated ExcKind.invalidOperation\n"
            "    return result"),
        "refinement": (
            "a patch that lets the non-recoverable failure escape but RELABELS it "
            "as the invalid-numeric-operation kind on the way out corrupts the "
            "identity of every exception it does not handle: a caller catching the "
            "kind it actually expects no longer sees it, and a caller catching the "
            "numeric-operation kind now swallows an unrelated failure. It reports "
            "an escaping failure where the desired behaviour reports one, so the "
            "failing test's recoverable inputs are untouched — but it silently "
            "rewrites the kind of everything outside the recoverable family, which "
            "the passing tests' propagate-unchanged behaviour depends on, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1/C6 (`out = toDecimalResult …`): C6 forces "
            "`out = propagated e` for the SAME `e` the interpretation attempt "
            "reported, not merely some escaping failure, and the rival substitutes "
            "a fixed kind. Refuted at conv = raised other — the ONLY witness "
            "reaching the non-recoverable `ExcKind.other` arm, and the only case in "
            "the battery whose residual goal is `ensures_1` (C6). If it verified "
            "=> SPEC-TOO-WEAK (the propagated kind's identity would be free, and a "
            "kind-rewriting impl would slip through)."
        ),
        "witness": _witness(
            "false false { payload := 0 } (ConvResult.raised ExcKind.other)"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling has 10 SPEC cases (2 soundness, 1 admissibility, 7
# uniqueness) plus a 4-entry AXIOM lane, over ONE contracted function
# `coerce_to_numeric(kind : int)` whose `kind` tag classifies the input into
# {0 absent, 1 float, 2 accepted, 3 invalid-op, 4 type-err, 5 value-err}. THIS
# bundle models the SAME operation on a RICHER carrier: instead of an integer
# tag it models the interpretation OUTCOME directly (`conv : ConvResult` =
# converted d | raised e, with `ExcKind` = {invalidOperation, typeError,
# valueError, other}), plus the two fast-path flags and the float value. Every
# nagini distinction survives: nagini kind 0 <-> isNone=true (C2), kind 1 <->
# isFloat=true (C3), kind 2 <-> conv=converted (C4), kinds 3/4/5 <-> conv=raised
# {invalidOperation,typeError,valueError} (C5), and the carrier ADDS a
# non-recoverable `other` kind (C6). So this port is NOT narrowed — nearly every
# nagini case has a counterpart.
#
#   nagini case                  -> here
#   -----------------------------------------------------------------------
#   pos-control-combined-except  -> pos-control-explicit-match     RE-EXPRESSED
#   pos-control-reorder-fastpaths-> pos-control-reorder-fastpaths  PORTED
#   admiss-accepted-shape        -> admiss-gold-total              RE-AIMED
#   weak-prepatch-only-malformed -> weak-prepatch-only-invalidop   PORTED
#   partial-domain-kind4-escape  -> partial-domain-typeerror-escape PORTED
#   cflow-swallow-reject         -> cflow-swallow-recoverable      PORTED
#   cflow-reraise-raw            -> cflow-reraise-raw              PORTED
#   weak-echo-const-kind2        -> weak-echo-const-converted      PORTED
#   weak-echo-fromfloat-kind2    -> weak-echo-fromfloat-converted  PORTED
#   weak-echo-const-kind1        -> weak-echo-const-float          PORTED
#   (new, no sibling)            -> weak-drop-none-fastpath        ADDED (binder)
#   (new, no sibling)            -> weak-propagate-wrong-kind      ADDED (audit, C6)
#   AXIOM_TESTS (4 entries)      -> (none)                         DROPPED (G-AX)
#
# 12 velvet SPEC cases: 2 soundness, 1 admissibility, 9 uniqueness.
#
# RE-EXPRESSED (pos-control-combined-except -> pos-control-explicit-match): the
#   nagini positive funnels every rejection class through a SINGLE `except
#   Exception:` handler (its note explains a literal multi-class except tuple is
#   not Nagini-translatable). A blanket catch-all does NOT port faithfully here:
#   the carrier adds a NON-recoverable `other` kind, and catching it too would
#   VIOLATE C6 (`out = propagated other`) — that impl is genuinely WRONG on this
#   carrier and verified as a reject, NOT a positive (measured: an
#   `_ => validationError` catch-all fails to verify). The soundness POINT the
#   nagini case makes — normalising the whole recoverable family through one
#   uniform report is the fix — is preserved as the explicit per-kind match,
#   which normalises exactly the three recoverable kinds and propagates `other`.
#   (The gold multi-class tuple's real analogue on this carrier is precisely
#   `isRecoverable`, whose family is the three recoverable kinds, not all four.)
# PORTED (reorder + 7 uniqueness): each carries its nagini refinement argument
#   intact — only the carrier changes from an integer `kind` tag to the
#   ConvResult/ExcKind outcome. The three control-flow / prepatch rivals
#   (weak-prepatch, partial-domain, cflow-swallow, cflow-reraise) attack C5/C6
#   (the recoverable-failure normalisation, the fix's behavioural delta); the
#   three value-pin rivals (echo-const-converted, echo-fromfloat-converted,
#   echo-const-float) attack C4/C3 (the produced-value pins), porting the nagini
#   GROUNDED-ORACLE value attacks. Each is backed by a machine-checked witness
#   SEEN to discriminate (rival exit 0, gold exit 1).
# RE-AIMED (admiss-accepted-shape -> admiss-gold-total): the nagini case made an
#   in-region self-call to discharge the precondition on a normal input. This
#   method has no `require` clause, so that probe is vacuous; re-aimed at the
#   residual total-domain risk (six-clause post-image joint satisfiability),
#   witnessed by the frozen impl discharging all six ensures.
# ADDED (weak-propagate-wrong-kind): no nagini sibling — the nagini carrier has
#   no non-recoverable kind at all (its `kind` tag runs 0..5, all of whose
#   rejection legs are recoverable), so C6 is a clause this RICHER carrier adds
#   and the nagini file had nothing to port for it. Added by the audit after
#   measuring that C6 (`ensures_1`) was the one independent clause no rival's
#   residual goal reached. A real C6 divergence with a machine-checked witness at
#   `ExcKind.other`.
# ADDED (weak-drop-none-fastpath): no nagini sibling (the nagini kind-0 leg is
#   covered by its integer-tag structure); added HERE to VARY the `isNone` binder,
#   which every other reject witness holds at false. A rival mishandling only the
#   null input would otherwise verify unnoticed. A real C2 divergence with a
#   machine-checked witness, not fabricated wrongness.
# DROPPED (AXIOM_TESTS, 4): the nagini bundle's axiom-soundness / containment
#   probes over the real CPython `decimal` stdlib belong to the G-AX lane. This
#   bundle is AXIOM-FREE (mapping.md §3: the fix is an exception-classification
#   decision modeled deeply in the `pure` region — no library callee to
#   axiomatize; axiom_check.py is absent and G-AX auto-skips), so there is nothing
#   even to drop from a G-AX perspective; and the G-PBT gate ignores AXIOM_TESTS
#   regardless.
#
# FRAME-MUTATION: VACUOUS, and the nagini sibling itself records the class as
#   inapplicable (`kind` is a plain integer acceptance tag, no heap permission,
#   has_readonly_input=False). Referentially-transparent backend, no `mut` binder,
#   no heap, no aliasing, no permission system. No read-only input to overwrite;
#   no substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE / POINT COVERAGE. Four input binders, ALL varied by the reject
#   witnesses: `conv` (converted vs raised, and the invalidOperation / typeError /
#   valueError arms of raised), `isNone` (true only in weak-drop-none-fastpath;
#   false elsewhere), `isFloat` (true only in weak-echo-const-float; false
#   elsewhere), `floatRes` (distinct from the produced token only in
#   weak-echo-fromfloat-converted). No binder is held fixed across the battery.
#   Every independent post-image clause is attacked. Measured per rival, by
#   reading which `ensures_N` goal is left unsolved (the elaborator numbers them
#   in REVERSE source order: ensures_6 = C1, ensures_5 = C2, ensures_4 = C3,
#   ensures_3 = C4, ensures_2 = C5, ensures_1 = C6):
#     C1 (ensures_6) — every rival, and defended by the two positives + admiss
#     C2 (ensures_5) — weak-drop-none-fastpath
#     C3 (ensures_4) — weak-echo-const-float
#     C4 (ensures_3) — weak-echo-const-converted, weak-echo-fromfloat-converted
#     C5 (ensures_2) — weak-prepatch, partial-domain, cflow-swallow, cflow-reraise
#     C6 (ensures_1) — weak-propagate-wrong-kind
#   AUDIT CORRECTION: an earlier revision of this footer credited C6 to
#   weak-prepatch / partial-domain / cflow-reraise on the argument that they
#   "yield propagated-on-a-recoverable-kind, i.e. violate the split C5+C6 jointly
#   pin". That was wrong, and measurably so: a recoverable kind falls in C5's
#   hypothesis and NOT in C6's (C6 is guarded by `isRecoverable e = false`), so
#   those three rivals satisfy C6 vacuously — their residual goals are ensures_2
#   and ensures_6 only, never ensures_1. All eight original rivals agree with gold
#   on the entire non-recoverable leg, leaving the identity of the propagated kind
#   unpinned. weak-propagate-wrong-kind was ADDED to close it and is the only case
#   whose residual goal is ensures_1, and the only witness reaching
#   `ExcKind.other`. The nine reject witnesses probe distinct input points spanning
#   all four binders and every ExcKind arm; no point is pinned across the battery.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD, re-measured by the audit:
#   `prove_postcondition_decidable_for toDecimal` leaves an unsolved
#   `Decidable (∀ d : DecimalVal, …)` goal, because `DecimalVal` wraps an `Int`
#   and so has an infinite domain. (The `∀ e : ExcKind` goals are NOT part of the
#   obstruction — `ExcKind` is a four-constructor `DecidableEq` enum and is
#   finitely decidable. An earlier revision of this note credited them as well;
#   corrected.) Every witness instead extracts the executable program
#   (`toDecimalExec`) and refutes C1 directly against the TRANSPARENT
#   `toDecimalResult` at a concrete input: each rival's `…Exec` reduces under
#   `decide` and the `≠` elaborates, while gold's `…Exec` reduces to exactly
#   `toDecimalResult` so `decide` proves the `≠` FALSE and the witness fails on
#   gold. No witness binds a hypothesis (all literal inputs over reachable finite
#   arms), so the consistency probe is a no-op. All NINE re-checked by the audit
#   with scripts/lean_verify.sh: rival exit 0, gold exit 1, and every gold-side
#   failure read to confirm it is the SEMANTIC refutation ("`decide` proved that
#   the proposition … is false"), never an unknown identifier or a type error.
AXIOM_TESTS = []
