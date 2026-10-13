"""properties.py — G-PBT falsification battery for django__django-16899 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct readonlyItemCheck`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a fully-transparent carrier). The
modeled operation validates ONE entry of a model administrator's read-only
configuration and decides how it is reported:

  readonlyItemCheck (isCallable hasAttrAdmin hasAttrModel fieldUnknown : Bool)
                    (label name adminName modelLabel : List Char)
      return (out : Option (List Char))
    ensures out = readonlyItemReport isCallable hasAttrAdmin hasAttrModel
                                     fieldUnknown label name adminName modelLabel

``readonlyItemReport`` is a fully-grounded pure dispatch over the four boolean
observations, and ``itemDiagnostic`` (the reported text) is a flat ``List Char``
concatenation of the four quoted string inputs between five fixed prose pieces.
Neither is an opaque oracle / answer-key: pinning ``out = readonlyItemReport …``
is grounded in the inputs (directive 8), and the only value satisfying it is the
one produced by building the message from the actual carriers. So there is no
WRONG oracle-echo that could verify — the positive controls are the cheapest
faithful reshapes, not a wrong echo (the ungrounded-oracle-echo class does NOT
apply here; the nagini sibling reached the same conclusion — its
``diagnostic_message`` was a grounded @Pure concatenation, so echoing it was the
correct work).

THE modeled change. On the one branch that produces a diagnostic — an entry that
is not invokable, not an attribute of the administrator, not an attribute of the
administered model class, and NOT recognised by the model's field registry — the
reported text now NAMES the entry (``name``), as its own quoted piece
immediately after the entry's label. The frozen ``itemDiagnostic`` pins this
three ways at once (all folded into the single master equality above): the
name's presence, its position (its own contiguous slot after the intro + label +
the "refers to" piece), and — via the acceptance/emptiness routing of
``readonlyItemReport`` — that an acceptable entry reports NOTHING (``none``). Any
rival that drops the name, empties its slot, transposes it with another quoted
piece, or reports a diagnostic on an acceptance branch renders the wrong report
and does NOT resolve the F2P.

BINDER STRUCTURE (read before judging binder coverage). The method has EIGHT
input binders: four boolean observations
(``isCallable``/``hasAttrAdmin``/``hasAttrModel``/``fieldUnknown``) selecting the
branch, and four ``List Char`` pieces
(``label``/``name``/``adminName``/``modelLabel``) quoted by the diagnostic. The
reject witnesses move every one:

  * the four booleans select the acceptance-vs-diagnostic routing. The dispatch
    is a PRIORITY ladder, so moving a boolean to ``true`` is NOT the same as
    entering the branch it guards: an earlier ``true`` short-circuits ahead of
    it. A rival that corrupts a branch is caught only at an input that actually
    REACHES that branch, i.e. one where every earlier guard is false. So the
    reject witness set is chosen to reach each of the FIVE ladder outcomes
    exactly once, and the four accept-branch rivals are refuted at the
    minimal-``true`` point for their own branch:

      branch reached          witness (isCallable, hasAttrAdmin,
                                       hasAttrModel, fieldUnknown)
      ----------------------------------------------------------------
      accept-1 (callable)     T _ _ _   flip-accept-callable
      accept-2 (attr admin)   F T F _   flip-accept-admin
      accept-3 (attr model)   F F T _   flip-accept-model
      report   (unknown)      F F F T   the three message rivals
                                        + report-silent
      accept-4 (known field)  F F F F   flip-accept-field-known

    The reporting branch is attacked in BOTH polarities, which the four
    acceptance branches' rivals cannot supply between them: the three message
    rivals corrupt the diagnostic's TEXT while still emitting one, and
    ``report-silent`` suppresses it entirely. A spec that only forbade spurious
    diagnostics — without requiring the real one — would pass every other reject
    case in this battery, so that polarity is what makes the reporting branch's
    NON-emptiness attested rather than assumed.

    Each boolean therefore takes both values AT A POINT THAT DISCRIMINATES on
    it, which raw value-variation alone does not establish.
  * ``name`` is THE field the fix adds; attacked by every message rival
    (``drop-value``, ``omit-value-keep-prose``, ``swap-value-cls``) and, in the
    suppression polarity, by ``report-silent``.
  * ``label`` / ``adminName`` / ``modelLabel`` — the other quoted pieces; each is
    read by the diagnostic-branch rivals, and ``adminName`` is moved into the
    ``name`` slot by ``swap-value-cls`` (and vice-versa).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (``frame-mutate-value``) — VACUOUS. The nagini
    sibling carries a MANDATORY frame-mutation probe because its inputs are held
    at a fractional heap permission (``Acc(list_pred(value),1/2)``) an impl can
    illegally overwrite. Lean/Velvet are referentially transparent: the eight
    inputs are immutable values, this bundle declares NO ``mut`` binder, there is
    no heap and no aliasing — so there is no read-only input to mutate and no
    substitute probe to build. Per the porting map this class is vacuous here;
    NOT fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo (see the surface note above):
    the ``axioms`` region is empty (no callee axiomatized; the dispatch and the
    message are modeled deeply), and every post-image is a flat function of the
    inputs, so there is nothing to echo. The nagini ``pos-master-assert`` control
    (assert built == the grounded oracle) becomes ``pos-report-direct`` here:
    returning the grounded pure model directly.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each witness reaches it through Velvet's own tester machinery
(``readonlyItemCheckTester args = false`` says the extracted program's result
violates the postcondition at that concrete input). All carriers are concrete
``Bool`` / ``List Char``, so ``decide`` settles every equality at a literal
input. There are NO ``require`` clauses, so every input reaches the
postcondition (the tester never short-circuits). Each witness is checked in a
file whose ``prove_correct`` block has been stripped (so no tactic script can
mask the verdict), and was verified out-of-band with two real builds: it
ELABORATES against the rival and FAILS against the frozen solution. No two
rivals are refuted at the same input point (pts = 8), and each of the four
acceptance branches of the dispatch ladder is attacked at a point that actually
REACHES it (every earlier guard false), which is what makes its emptiness
attested rather than merely tallied.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the dispatch and
the message are modeled deeply, not delegated to an oracle). The gate ignores
``AXIOM_TESTS`` regardless. Nagini→velvet accounting is at the bottom of the file.
"""
from pathlib import Path

INSTANCE = "django__django-16899"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so a swap edits only the impl body and
# ---- `markers.same_spec` holds by construction, leaving the frozen
# ---- `prove_correct readonlyItemCheck` statement intact.

# The diagnostic-branch text (the message built on the sole reporting branch).
# This is the entire content of the modeled change: the quoted pieces spliced
# between the five fixed prose markers, with the entry's `name` named as its own
# piece after the label.
_DIAG = (
    '        some ("The value of \'".toList ++ label\n'
    '          ++ "\' refers to \'".toList ++ name\n'
    '          ++ "\', which is not a callable, an attribute of \'".toList ++ adminName\n'
    '          ++ "\', or an attribute of \'".toList ++ modelLabel\n'
    '          ++ "\'.".toList)\n'
)
assert _BASE.count(_DIAG) == 1, "diagnostic-branch text drifted from expected"

# The whole frozen impl body (the `let`-ladder), used by the reshape positive
# that replaces the entire dispatch.
_FULL = (
    "    let result : Option (List Char) :=\n"
    "      if isCallable then none\n"
    "      else if hasAttrAdmin then none\n"
    "      else if hasAttrModel then none\n"
    "      else if fieldUnknown then\n"
    + _DIAG +
    "      else none\n"
    "    return result\n"
)
assert _BASE.count(_FULL) == 1, "impl body drifted from expected text"

# The FIRST acceptance branch (an invokable entry -> acceptable). Unique.
_ACCEPT_CALLABLE = "      if isCallable then none\n"
assert _BASE.count(_ACCEPT_CALLABLE) == 1, "callable-accept branch drifted"

# The SECOND acceptance branch (the entry names an attribute of the
# administrator -> acceptable). Unique at this indentation (the same text
# indented by two spaces occurs in the pure model, which the surgery must not
# touch — hence the six-space anchor, asserted unique below).
_ACCEPT_ADMIN = "      else if hasAttrAdmin then none\n"
assert _BASE.count(_ACCEPT_ADMIN) == 1, "admin-attr-accept branch drifted"

# The THIRD acceptance branch (the entry names an attribute of the administered
# model class -> acceptable). Unique at this indentation, as above.
_ACCEPT_MODEL = "      else if hasAttrModel then none\n"
assert _BASE.count(_ACCEPT_MODEL) == 1, "model-attr-accept branch drifted"

# The FINAL acceptance branch (field recognised by the registry -> acceptable).
# Unique.
_ACCEPT_FIELD = "      else none\n"
assert _BASE.count(_ACCEPT_FIELD) == 1, "field-known-accept branch drifted"


def _diag(new_diag):
    """Solution.lean with only the diagnostic-branch text replaced."""
    return _swap(_BASE, _DIAG, new_diag)


def _full(new_body):
    """Solution.lean with the ENTIRE impl body replaced (spec view untouched)."""
    return _swap(_BASE, _FULL, new_body)


def _accept_callable(new_branch):
    return _swap(_BASE, _ACCEPT_CALLABLE, new_branch)


def _accept_admin(new_branch):
    return _swap(_BASE, _ACCEPT_ADMIN, new_branch)


def _accept_model(new_branch):
    return _swap(_BASE, _ACCEPT_MODEL, new_branch)


def _accept_field(new_branch):
    return _swap(_BASE, _ACCEPT_FIELD, new_branch)


# ---- The `let`-ladder opener and the frozen tactic body, used by the
# ---- ADMISSIBILITY positive. The assert is inserted BEFORE the ladder (still
# ---- wholly inside the impl region, so the spec view is untouched), and the
# ---- frozen `loom_solve` is extended — not replaced — with the `decide` that
# ---- discharges the added in-region assertion. Both anchors asserted unique.
_LADDER_OPEN = "    let result : Option (List Char) :=\n"
assert _BASE.count(_LADDER_OPEN) == 1, "let-ladder opener drifted"

_PROOF = "prove_correct readonlyItemCheck by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct tactic body drifted"


def _admiss(assertion):
    """Frozen impl with `assertion` prepended inside the impl region, and the
    frozen `loom_solve` extended by `decide` to discharge it. The obligation
    statement is untouched: only the tactic BODY (which the consumer spec view
    elides) gains a combinator."""
    return _swap(
        _swap(_BASE, _LADDER_OPEN, assertion + _LADDER_OPEN),
        _PROOF, _PROOF + " <;> decide")


# ---- witness preamble. Reaches the `method` CONTRACT through Velvet's tester
# ---- machinery: `readonlyItemCheckTester args = false` says the extracted
# ---- program's result violates the postcondition at the concrete input `args`.
# ---- Checked in a file whose `prove_correct` block has been stripped.
_TESTER = (
    "extract_program_for readonlyItemCheck\n"
    "prove_precondition_decidable_for readonlyItemCheck\n"
    "prove_postcondition_decidable_for readonlyItemCheck\n"
    "derive_tester_for readonlyItemCheck\n\n"
)


def _witness(ic, ha, hm, fu, label, name, admin, model):
    """A tester application at a concrete input; booleans as Lean literals,
    strings as `.toList` of a literal so `decide` computes the List Char."""
    return (
        _TESTER
        + "example : readonlyItemCheckTester "
        + f"{ic} {ha} {hm} {fu} "
        + f'"{label}".toList "{name}".toList "{admin}".toList "{model}".toList'
        + " = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # `pos-one-expr` / `pos-master-assert` ARGUMENT: instead of the inlined
    # `let`-ladder, return the grounded pure model directly. The ensures IS
    # `out = readonlyItemReport …`, so the body is definitionally the RHS and the
    # frozen `loom_solve` closes the byte-identical obligation. Verified EXIT 0.
    # =====================================================================
    {
        "id": "pos-report-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _full(
            "    return readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown\n"
            "                              label name adminName modelLabel\n"
        ),
        "rationale": (
            "PASS SOURCE = the master clause `out = readonlyItemReport …`. "
            "Returning the grounded pure model directly rather than re-inlining "
            "the priority `let`-ladder is observationally identical on every "
            "input, so the postcondition still discharges. There is no executable "
            "materialization of an opaque oracle here — the model is a flat "
            "function of the inputs — so the cheapest impl that satisfies the "
            "clause still builds the message from the real carriers. A "
            "structurally different faithful reshape MUST verify; if it cannot, "
            "the postcondition is over-fit to one concatenation shape "
            "(SPEC-TOO-STRONG). Ports the nagini pos-one-expr / pos-master-assert."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — reshape the diagnostic branch to call the
    # grounded pure text-builder `itemDiagnostic` (definitionally the same
    # concatenation) rather than re-spelling it inline. Same value on the
    # reporting branch, reshaped executable form; every branch preserved. MUST
    # verify. Verified EXIT 0.
    # =====================================================================
    {
        "id": "pos-diag-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _diag(
            "        some (itemDiagnostic label name adminName modelLabel)\n"
        ),
        "rationale": (
            "PASS SOURCE = the master clause. The diagnostic-branch text is "
            "rebuilt by the grounded pure helper `itemDiagnostic label name "
            "adminName modelLabel` (definitionally the same concatenation the "
            "frozen impl spells inline), leaving every acceptance branch "
            "unchanged. A faithful reshape of the reporting branch MUST verify, "
            "else SPEC-TOO-STRONG (the postcondition would reject its own model's "
            "text)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — ported from the nagini
    # `admiss-fshape`, re-aimed at the analogue this carrier actually has.
    #
    # The nagini case discharges four `Acc(list_pred(.),1/2)` PRECONDITIONS at an
    # F2P-shaped input. This method declares no `require`, so a
    # precondition-satisfiability probe would indeed be vacuous — but that is NOT
    # a reason to drop the lane, because on a TOTAL carrier the same defect
    # arrives as the post-image being UNSATISFIABLE or DEGENERATE at exactly an
    # F2P-shaped input. That is what this case tests, by evaluation, as an
    # in-region `have`/`assert` discharged BEFORE the frozen obligation closes
    # verbatim.
    #
    # Both conjuncts are load-bearing and NON-degenerate at the F2P shape:
    #   1. at the reporting point (not invokable, not an attribute of the
    #      administrator or of the model, registry does NOT recognise the name)
    #      the post-image demands a `some` carrying the FULL literal diagnostic
    #      text — spelled out here as one flat string literal, independent of
    #      `itemDiagnostic`'s concatenation shape, so this pins the rendered
    #      characters rather than restating the model;
    #   2. at the SAME eight-input point except that the registry DOES recognise
    #      the name, the post-image demands `none`.
    # So the obligation is satisfiable at the F2P input AND discriminates there:
    # a spec whose post-image were unsatisfiable, or which collapsed those two
    # points, fails this case. Negative control run out-of-band: replacing the
    # `none` conjunct's expected value with `some "bogus".toList` makes the very
    # same file FAIL (`decide` proved the proposition false), so the assertion is
    # doing work rather than being closed by the tactic regardless.
    # =====================================================================
    {
        "id": "admiss-f2p-report-and-accept",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss(
            "    assert (with_name_prefix `assert\n"
            "      (readonlyItemReport false false false true\n"
            '         "readonly_fields[1]".toList "nonexistent".toList\n'
            '         "SongAdmin".toList "admin_checks.Song".toList\n'
            '       = some ("The value of \'readonly_fields[1]\' refers to \'nonexistent\', "\n'
            '               ++ "which is not a callable, an attribute of \'SongAdmin\', "\n'
            '               ++ "or an attribute of \'admin_checks.Song\'.").toList\n'
            "       ∧ readonlyItemReport false false false false\n"
            '           "readonly_fields[1]".toList "nonexistent".toList\n'
            '           "SongAdmin".toList "admin_checks.Song".toList = none))\n'
        ),
        "rationale": (
            "PRECOND-TOO-STRONG lane, re-aimed for a total carrier. The frozen "
            "method has no `require`, so the nagini probe's literal subject (four "
            "half-permission preconditions) has no analogue; the analogue that "
            "DOES exist is the post-image being unsatisfiable or degenerate at an "
            "F2P-shaped input, and that is what the in-region assert discharges "
            "by evaluation before the frozen obligation closes verbatim. It pins "
            "two points at once: at the reporting point the post-image demands the "
            "full rendered diagnostic (given as a flat literal, so it constrains "
            "the CHARACTERS and not merely the model's concatenation shape), and "
            "at the same input with the registry recognising the name it demands "
            "`none`. If the assert failed to discharge, the obligation would be "
            "unsatisfiable or collapsed at exactly the input the failing test "
            "exercises => PRECOND-TOO-STRONG. Ports nagini admiss-fshape."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "drop-value",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating rival: on the sole reporting branch, omit the
        # entry's name (and the "refers to '…'" piece) entirely — exactly the
        # pre-change behaviour (Solution_prepatch.lean).
        "module": _diag(
            '        some ("The value of \'".toList ++ label\n'
            '          ++ "\' is not a callable, an attribute of \'".toList ++ adminName\n'
            '          ++ "\', or an attribute of \'".toList ++ modelLabel\n'
            '          ++ "\'.".toList)\n'
        ),
        "refinement": (
            "this is the pre-change behaviour: the reported text names the entry's "
            "POSITION but never the entry's name. On the F2P (a configuration "
            "entry named 'nonexistent' at position 'readonly_fields[1]') the "
            "report reads 'The value of \\'readonly_fields[1]\\' is not a "
            "callable, …' — MISSING the 'refers to \\'nonexistent\\'' piece the "
            "failing assertion now demands — so test_nonexistent_field / "
            "test_nonexistent_field_on_inline stay RED and it would NOT resolve. "
            "This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from the master clause `out = readonlyItemReport …`: the "
            "reporting branch must equal `some (itemDiagnostic label name "
            "adminName modelLabel)`, whose `name` piece is absent here. Refuted at "
            "the F2P input (diagnostic branch, name='nonexistent'). If it verified "
            "=> SPEC-TOO-WEAK (the spec would admit the un-fixed report)."
        ),
        "witness": _witness(
            "false", "false", "false", "true",
            "readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song"),
    },
    {
        "id": "omit-value-keep-prose",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the "refers to '…'" prose piece but drop the name carrier: the
        # report reads "…refers to '', which is not…". The name is not there.
        "module": _diag(
            '        some ("The value of \'".toList ++ label\n'
            '          ++ "\' refers to \'".toList\n'
            '          ++ "\', which is not a callable, an attribute of \'".toList ++ adminName\n'
            '          ++ "\', or an attribute of \'".toList ++ modelLabel\n'
            '          ++ "\'.".toList)\n'
        ),
        "refinement": (
            "keeps the inserted 'refers to \\'…\\'' prose but leaves its slot "
            "empty, rendering '…refers to \\'\\', which is not…'. Its faithful "
            "counterpart interpolates an EMPTY string at the new slot, still "
            "MISSING 'i_dont_exist' — so the F2P assertion, which pins the entry's "
            "name inside that slot, FAILS and it would NOT resolve. Targets the "
            "name-POSITION facet specifically (the prose is present but the entry "
            "is not named)."
        ),
        "rationale": (
            "REJECT from the master clause: the reporting text must place `name` "
            "in its own slot after the intro + label + 'refers to' piece; here "
            "that slot is empty, so `out` differs from the model at every "
            "diagnostic input with a non-empty `name`. Refuted at the second F2P "
            "input (name='i_dont_exist') — a distinct point from drop-value. If it "
            "verified => SPEC-TOO-WEAK (the name-position would be satisfiable "
            "without the name present)."
        ),
        "witness": _witness(
            "false", "false", "false", "true",
            "readonly_fields[0]", "i_dont_exist", "CityInline", "admin_checks.City"),
    },
    {
        "id": "swap-value-cls",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose the entry-name slot and the administrator-name slot: the
        # entry IS named, but at the administrator's interpolation point and
        # vice-versa. Defeats a naive name-PRESENCE check by putting the name
        # somewhere wrong.
        "module": _diag(
            '        some ("The value of \'".toList ++ label\n'
            '          ++ "\' refers to \'".toList ++ adminName\n'
            '          ++ "\', which is not a callable, an attribute of \'".toList ++ name\n'
            '          ++ "\', or an attribute of \'".toList ++ modelLabel\n'
            '          ++ "\'.".toList)\n'
        ),
        "refinement": (
            "transposes the entry-name and administrator-name slots: the entry IS "
            "named, but at the administrator's interpolation point and "
            "vice-versa. Its faithful counterpart renders 'refers to "
            "\\'<admin>\\', … an attribute of \\'<entry-name>\\'' — the two quoted "
            "pieces swapped — so the F2P assertion (which pins the entry's name "
            "immediately after 'refers to' and the administrator name in the "
            "'attribute of' slot) FAILS and it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause: the model places `name` in the slot "
            "after 'refers to' and `adminName` in the 'attribute of' slot; the "
            "rival swaps them, so `out` differs from the model whenever "
            "name != adminName. Refuted at name='V', adminName='C' (distinct) — a "
            "distinct input point that moves `adminName` into the name slot. If it "
            "verified => SPEC-TOO-WEAK (the name-position would be unpinned)."
        ),
        "witness": _witness(
            "false", "false", "false", "true", "lbl", "V", "C", "M"),
    },
    {
        "id": "report-silent",
        "kind": "uniqueness",
        "expect": "reject",
        # The MISSING half of the emptiness/routing attack. All four
        # flip-accept-* rivals report a diagnostic where the model reports
        # NOTHING; this one reports nothing where the model MUST report — the
        # sole diagnostic-producing branch is silenced. No shipped rival covered
        # this direction: the three message rivals all still emit a `some` on that
        # branch and only corrupt its text, so a rival that suppresses the report
        # entirely was unattested.
        "module": _diag("        none\n"),
        "refinement": (
            "silences the report on the one branch that must produce it: an entry "
            "that is not invokable, not an attribute of the administrator, not an "
            "attribute of the administered model class, and NOT recognised by the "
            "field registry is accepted with no diagnostic at all. Its faithful "
            "counterpart reports zero problems for an unresolvable read-only "
            "entry, so the failing tests — which assert that such an entry "
            "produces exactly one diagnostic carrying the entry's name — get an "
            "EMPTY result instead and stay RED; it would NOT resolve. It also "
            "regresses the pre-change behaviour, which at least reported "
            "something."
        ),
        "rationale": (
            "REJECT from the master clause `out = readonlyItemReport …`, whose "
            "fourth branch returns `some (itemDiagnostic …)` when the registry "
            "does not recognise the entry. The rival returns `none` there, so "
            "`out` differs from the model at every reporting input. Refuted at a "
            "reporting-branch point distinct from all three message rivals "
            "(name='vanished'). This is the opposite polarity from the four "
            "flip-accept-* rivals: they add a report where none is due, this one "
            "withholds a report that is. If it verified => SPEC-TOO-WEAK (the "
            "reporting branch's NON-emptiness would be unpinned, and a spec that "
            "only forbids spurious diagnostics without requiring the real one "
            "cannot distinguish the fix from doing nothing)."
        ),
        "witness": _witness(
            "false", "false", "false", "true",
            "readonly_fields[4]", "vanished", "AdminThree", "app_three.Gamma"),
    },
    {
        "id": "flip-accept-callable",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow / emptiness discriminator: emit a diagnostic on the FIRST
        # acceptance branch (an invokable entry, which is acceptable and must
        # report `none`). A spurious diagnostic for an acceptable entry.
        "module": _accept_callable(
            "      if isCallable then some (itemDiagnostic label name adminName modelLabel)\n"
        ),
        "refinement": (
            "emits a diagnostic for an INVOKABLE entry, which is acceptable and "
            "must report nothing. Its faithful counterpart would report a "
            "configuration error for a well-formed read-only entry (a callable), "
            "so every P2P config that expects zero errors for such an entry "
            "(e.g. the readonly-callable / readonly-method configurations) would "
            "then report a spurious error and FAIL; it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause `out = readonlyItemReport …`, whose "
            "first branch returns `none` when `isCallable`. The rival returns "
            "`some …` there, so `out` differs from the model on every "
            "callable-entry input. Refuted at isCallable=true (the only witness "
            "that enters this acceptance branch), fieldUnknown=true. If it "
            "verified => SPEC-TOO-WEAK (the acceptance-path emptiness unpinned)."
        ),
        "witness": _witness(
            "true", "true", "true", "true", "p", "q", "r", "s"),
    },
    {
        "id": "flip-accept-admin",
        "kind": "uniqueness",
        "expect": "reject",
        # Emptiness discriminator on the SECOND acceptance branch (the entry
        # names an attribute of the administrator -> acceptable, must report
        # `none`). This branch is REACHED only when isCallable is false, so the
        # witness holds isCallable=false and sets hasAttrAdmin=true — the only
        # point in the battery that discriminates on hasAttrAdmin, since at an
        # input where isCallable is also true the first branch short-circuits
        # ahead of this one and a corruption here is invisible.
        "module": _accept_admin(
            "      else if hasAttrAdmin then some (itemDiagnostic label name adminName modelLabel)\n"
        ),
        "refinement": (
            "emits a diagnostic for an entry that names an attribute of the "
            "ADMINISTRATOR, which is acceptable and must report nothing. Its "
            "faithful counterpart would report a configuration error for a "
            "read-only entry supplied by an attribute of the administrator "
            "itself, so the P2P configurations whose read-only entry resolves "
            "that way (the administrator-attribute and administrator-method "
            "read-only configurations that expect zero errors) would report a "
            "spurious error and FAIL; it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause `out = readonlyItemReport …`, whose "
            "second branch returns `none` when the entry is not invokable but "
            "does name an attribute of the administrator. The rival returns "
            "`some …` there. Refuted at isCallable=false, hasAttrAdmin=true "
            "(hasAttrModel=false) — the minimal-true point that actually REACHES "
            "this branch, and the battery's only discriminating point for "
            "hasAttrAdmin. If it verified => SPEC-TOO-WEAK (this acceptance "
            "branch's emptiness would be unpinned)."
        ),
        "witness": _witness(
            "false", "true", "false", "true",
            "readonly_fields[2]", "shadowed", "AdminOne", "app_one.Alpha"),
    },
    {
        "id": "flip-accept-model",
        "kind": "uniqueness",
        "expect": "reject",
        # Emptiness discriminator on the THIRD acceptance branch (the entry names
        # an attribute of the administered model class -> acceptable, must report
        # `none`). Reached only when isCallable and hasAttrAdmin are both false,
        # so the witness holds both false and sets hasAttrModel=true — the only
        # point in the battery that discriminates on hasAttrModel.
        "module": _accept_model(
            "      else if hasAttrModel then some (itemDiagnostic label name adminName modelLabel)\n"
        ),
        "refinement": (
            "emits a diagnostic for an entry that names an attribute of the "
            "administered MODEL CLASS, which is acceptable and must report "
            "nothing. Its faithful counterpart would report a configuration "
            "error for a read-only entry resolved by a method or attribute on "
            "the administered model, so the P2P configurations whose read-only "
            "entry resolves that way (the model-method read-only configurations "
            "that expect zero errors) would report a spurious error and FAIL; it "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause: the third branch returns `none` when "
            "the entry is neither invokable nor an attribute of the "
            "administrator but does name an attribute of the administered model "
            "class. The rival returns `some …` there. Refuted at "
            "isCallable=false, hasAttrAdmin=false, hasAttrModel=true — the "
            "minimal-true point that actually REACHES this branch, and the "
            "battery's only discriminating point for hasAttrModel. If it "
            "verified => SPEC-TOO-WEAK (this acceptance branch's emptiness would "
            "be unpinned)."
        ),
        "witness": _witness(
            "false", "false", "true", "true",
            "readonly_fields[3]", "inherited", "AdminTwo", "app_two.Beta"),
    },
    {
        "id": "flip-accept-field-known",
        "kind": "uniqueness",
        "expect": "reject",
        # Emptiness discriminator on the FINAL acceptance branch: emit a
        # diagnostic when the field IS recognised by the registry (acceptable ->
        # must report `none`). Distinct branch and distinct input from
        # flip-accept-callable, and it moves `fieldUnknown` to false.
        "module": _accept_field(
            "      else some (itemDiagnostic label name adminName modelLabel)\n"
        ),
        "refinement": (
            "emits a diagnostic for an entry the model's field registry DOES "
            "recognise (fieldUnknown=false), which is acceptable and must report "
            "nothing. Its faithful counterpart would report a configuration error "
            "for a valid model field, so every P2P config with a well-formed "
            "read-only field referencing a real model field would report a "
            "spurious error and FAIL; it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause: the final branch returns `none` when "
            "the entry is not callable, not an attribute of the administrator or "
            "model, and the registry recognises it (fieldUnknown=false). The rival "
            "returns `some …` there. Refuted at all-false (fieldUnknown=false too) "
            "— the only witness that moves `fieldUnknown` to false and reaches "
            "this branch. If it verified => SPEC-TOO-WEAK (the resolve-path "
            "emptiness unpinned)."
        ),
        "witness": _witness(
            "false", "false", "false", "false", "x", "y", "z", "w"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation reject, 4 uniqueness
# rejects) plus 2 AXIOM_TESTS, over `check_reference(label, value, cls,
# model_label, resolves) -> List[int]` modeled with a @Pure `diagnostic_message`
# oracle and fractional-permission (`Acc(list_pred(.),1/2)`) read-only inputs.
# THIS bundle models the SAME operation over a fully-transparent, referentially
# transparent carrier: `readonlyItemCheck` returns `Option (List Char)` (none <->
# the acceptable/empty result, some msg <-> the reported diagnostic), the four
# runtime observations are the four boolean inputs, and the message is a deeply
# modeled `List Char` concatenation. The single master clause `out =
# readonlyItemReport …` folds nagini's CLAUSE-2 (emptiness/routing), CLAUSE-3
# (whole-message equality) and CLAUSE-4 (value-position) into one grounded
# equality, so each nagini rival maps to a violation of that clause.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-one-expr                -> pos-report-direct           PORTED (re-shaped)
#   pos-master-assert           -> pos-report-direct / pos-diag-helper  PORTED
#   admiss-fshape               -> admiss-f2p-report-and-accept PORTED (re-aimed)
#   frame-mutate-value          -> (none)                      VACUOUS (ref. transparent)
#   drop-value                  -> drop-value                  PORTED
#   omit-value-keep-prose       -> omit-value-keep-prose       PORTED
#   swap-value-cls              -> swap-value-cls              PORTED
#   discriminator-flip          -> flip-accept-callable        PORTED (+ split)
#                               -> flip-accept-admin           PORTED (added branch)
#                               -> flip-accept-model           PORTED (added branch)
#                               -> flip-accept-field-known     PORTED (added branch)
#   AXIOM_TESTS (x2)            -> (none)                       DROPPED
#
# PORTED (8 rejects). drop-value (omit the entry's name — the pre-patch shape),
#   omit-value-keep-prose (keep the prose piece, empty the name slot), and
#   swap-value-cls (transpose the name and administrator-name slots) carry across
#   intact — only the carrier changes from `List[int]` + a @Pure oracle to a
#   deeply-modeled `List Char` concatenation. Each keeps its nagini refinement
#   argument (a report missing / mis-placing the entry name fails the same F2P).
#   nagini's single `discriminator-flip` (emit a message on the resolve/accept
#   path) is SPLIT into FOUR rivals here — flip-accept-callable,
#   flip-accept-admin, flip-accept-model and flip-accept-field-known — because
#   this carrier exposes FOUR acceptance branches where nagini folded the accept
#   decision into one `resolves` bool. The split must be exhaustive, not
#   representative: the dispatch is a PRIORITY ladder, so a corruption of the
#   admin-attr or model-attr branch is invisible at every input the other rivals
#   use (an earlier guard short-circuits ahead of it), and attacking only the
#   first and last branches would leave those two silently unattested while the
#   binder tally still read "all four booleans take both values". Each of the
#   four is refuted at the minimal-true point that actually REACHES its own
#   branch, so the four acceptance outcomes plus the reporting outcome give five
#   distinct ladder outcomes. Each reject now carries a
#   machine-checked tester witness — the new work with no nagini counterpart
#   (nagini relied on Viper to discharge the contract; a tactic-proof backend
#   cannot infer wrongness from a build failure).
# RE-SHAPED (2 positives). nagini pos-one-expr rewrote the append chain as one
#   combined expression; here the cheapest structurally-different correct impl is
#   `return readonlyItemReport …` (the grounded pure model, definitionally the
#   ensures RHS) = pos-report-direct. nagini pos-master-assert asserted the built
#   result == the grounded oracle right before return; on velvet the ensures IS
#   that equality, so its analogue is a reshape that rebuilds the reporting text
#   via the grounded helper `itemDiagnostic` = pos-diag-helper. Both verify under
#   the frozen `loom_solve` (two real builds).
# PORTED admissibility (admiss-fshape -> admiss-f2p-report-and-accept). The
#   nagini case discharges four `Acc(list_pred(.),1/2)` preconditions at an
#   F2P-shaped input. This method declares no `require`, so that literal subject
#   has no analogue here — but the LANE does, and "no precondition" is NOT a
#   reason to drop it: on a total carrier PRECOND-TOO-STRONG arrives as the
#   post-image being unsatisfiable or DEGENERATE at exactly an F2P-shaped input.
#   The ported case tests that directly, by evaluation, as an in-region assert
#   discharged before the frozen obligation closes verbatim, pinning two points:
#   the reporting point must demand the full rendered diagnostic text (given as a
#   flat literal, so it constrains characters rather than restating the model's
#   concatenation shape), and the same input with the registry recognising the
#   name must demand `none`. Load-bearing, not decoration: with the second
#   conjunct's expected value corrupted the identical file FAILS (`decide` proved
#   the proposition false).
# VACUOUS frame-mutation (frame-mutate-value): the nagini MANDATORY probe writes
#   through a read-only input held at Acc(list_pred(value),1/2). Lean/Velvet are
#   referentially transparent — the eight inputs are immutable values, no `mut`
#   binder, no heap, no aliasing, no permission system — so there is no read-only
#   input to overwrite and no substitute probe to build. Per the porting map this
#   class is vacuous here; NOT fabricated.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and per mapping.md §3 this
#   bundle axiomatizes NO callee (the message is modeled deeply, the four
#   observations are free inputs), so gate_ax reports skip; this gate ignores
#   AXIOM_TESTS regardless.
#
# CLAUSE COVERAGE: the single master clause is attacked by every reject — its
#   message half by drop-value / omit-value-keep-prose / swap-value-cls (name
#   presence, name position, name/admin ordering) and its emptiness/routing half
#   in BOTH polarities: by all FOUR flip-accept-* rivals, one per acceptance
#   branch of the priority ladder (a report where none is due), and by
#   report-silent (no report where one IS due). Both positives defend it, and
#   admiss-f2p-report-and-accept additionally shows it is satisfiable and
#   non-degenerate at the F2P-shaped input.
# BINDER COVERAGE: all EIGHT input binders are varied across the reject
#   witnesses, and each of the four booleans is varied AT A POINT THAT
#   DISCRIMINATES ON IT — the distinction that matters on a priority ladder,
#   where merely setting a guard true proves nothing if an earlier guard
#   short-circuits ahead of it:
#     isCallable    — true only in flip-accept-callable, whose branch it is the
#                     sole guard of; false in all six others.
#     hasAttrAdmin  — true with isCallable=false ONLY in flip-accept-admin, the
#                     rival whose branch it guards.
#     hasAttrModel  — true with isCallable=hasAttrAdmin=false ONLY in
#                     flip-accept-model, the rival whose branch it guards.
#     fieldUnknown  — true for the three message rivals and for report-silent
#                     (reaching the reporting branch), false in
#                     flip-accept-field-known (reaching the final acceptance
#                     branch); the two outcomes it selects between are therefore
#                     both attacked, and the reporting one in BOTH polarities
#                     (corrupted text vs. suppressed report).
#   The four strings each take distinct values across rivals, with `name`
#   attacked by all three message rivals and `adminName` moved into the name slot
#   by swap-value-cls. EIGHT DISTINCT reject witness points (pts=8), covering all
#   five outcomes of the dispatch ladder.
AXIOM_TESTS = []
