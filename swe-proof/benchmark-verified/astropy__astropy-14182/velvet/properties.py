"""properties.py — G-PBT falsification battery for astropy__astropy-14182 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery replaces text lying wholly inside one method's
``-- impl-start`` / ``-- impl-end`` region, the region the consumer spec view
elides, so ``markers.same_spec`` holds by construction and both
``prove_correct`` obligations survive — and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted methods, one obligation each):

  surroundWithRuler (lines : List (List Char)) (headerRowCount : Nat)
    require headerRowCount < lines.length
    ensures out = [lines[headerRowCount]!] ++ lines ++ [lines[headerRowCount]!]

  dataStartOffset (headerRowCount : Nat)
    ensures out = 2 + headerRowCount

Both model an index that must track the number of header rows requested for a
constant-width rendering rather than assuming a single one. The first frames a
rendering by copying its column-extent ruler line — the line sitting immediately
after the header lines, i.e. at position ``headerRowCount`` — to the top and the
bottom, leaving the rendering otherwise verbatim. The second reports the position
of the first data line when such a rendering is parsed back: two ruler lines plus
however many header lines sit above it.

Neither postcondition mentions an opaque callee: both are stated entirely over
the method's own inputs (a positional pick and two concatenations; an arithmetic
expression), so both are GROUNDED and every witness can pin its inputs to
concrete literals and close by ``decide``. There is no answer-key oracle a rival
could echo.

The framing equation decomposes into four independently-attackable parts, and
every uniqueness rival targets one:

  (P) the POSITION the framing line is read from must be ``headerRowCount``;
  (T) the TOP element must be that line;
  (B) the BOTTOM element must be that same line;
  (M) the MIDDLE must be ``lines`` verbatim — same elements, same order, and the
      result must carry both framing elements (so the length is ``.length + 2``).

The offset equation is a single affine relation in the one binder, attacked at
three grains: the wrong constant, the wrong intercept, and the wrong slope, plus
one rival that is affine-correct on all but a single point.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling models
the same two observable behaviours, but over ``List[int]`` row tags with three
``@Pure`` helpers, an explicit per-block framing value carried as a separate
opaque parameter, and fractional read permissions on both inputs. Here the
framing value is not a parameter at all — it is the positional pick
``lines[headerRowCount]!``, read straight out of the input — and there are no
helpers to route an index through. So the nagini cases split as follows (full
accounting in the footer):

  * FRAME/PERMISSION-MUTATION — VACUOUS, and this is the largest block of nagini
    cases with no counterpart. Both nagini probes (write through the rendering,
    write through the header list) are MANDATORY there because both inputs are
    held at a fractional read permission an implementation can overwrite. This
    backend is referentially transparent: there is no heap, no aliasing, no
    fractional permission, and NEITHER method declares a ``mut`` binder, so every
    input is an immutable value. There is no read-only input to mutate, hence no
    substitute probe. Not fabricated.
  * UNGROUNDED-ORACLE ECHO — PORTED and still meaningful. The nagini sibling
    records this as its historical hole: an earlier revision pinned the framing
    line to a fixed sentinel, letting an implementation echo that constant
    without ever reading the input. ``weak-frame-synthesised-ruler`` re-runs the
    attack on this carrier: it frames with a synthesised constant line instead of
    the one at ``headerRowCount``. Because the postcondition names
    ``lines[headerRowCount]!`` — a positional pick into the input, not a
    constant — the constant cannot discharge it, and the rival is refuted at a
    rendering whose line at that position is not the synthesised one.
  * PARTIAL-DOMAIN — PORTED, both halves. ``weak-frame-fixed-second-line`` and
    ``weak-offset-fixed-three`` are the two pre-image behaviours: each is correct
    only where exactly one header row was requested, and each is refuted at the
    three-header-row shape the failing regression exercises.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. Every frozen impl region
    is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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
  * CONTROL-FLOW-EFFECT and VALUE-DOUBLE-MASK — N/A for the same reasons the
    nagini sibling records: both methods are pure value/index computations with no
    exception path, and each postcondition pins its result COMPLETELY (the whole
    framed sequence; a scalar), not through a proxy that could drop disagreeing
    positions.

WITNESS MECHANICS. Every input type here is fully decidable — ``Nat`` and
``List (List Char)`` — and every postcondition is grounded in those inputs, so no
witness needs to condition on an opaque carrier and none binds a hypothesis
(hence no consistency probe applies: there are no assumptions that could be
jointly unsatisfiable). Each witness pins the inputs to concrete literals and
reaches the method CONTRACT through Velvet's own tester machinery:
``<name>Tester args = false`` says the extracted program's result violates the
method's postcondition at that input (the tester returns ``true`` vacuously when
the precondition fails, so a ``= false`` witness also attests its point is
in-domain), closed by ``decide``. Each is checked in a file whose
``prove_correct`` blocks have been stripped, so no tactic script can mask the
verdict. All ten were checked out-of-band with ``scripts/lean_verify.sh``: each
ELABORATES against its rival (exit 0) and FAILS against the frozen solution
(exit 1) with a SEMANTIC error — ``Tactic `decide` proved that the proposition
<name>Tester … = false is false``, i.e. gold's tester ACCEPTS the point — never
an unknown identifier, a type error, an unfolding failure or a timeout. No
banned token (``sorry`` / ``admit`` / ``native_decide`` / ``axiom``).

AXIOM lane: EMPTY, and nothing was dropped to get there. The ``axioms`` region
declares no ``axiom`` and the nagini sibling's ``AXIOM_TESTS`` is likewise empty
(``meta.axioms == []`` on both sides: both modeled behaviours are closed-form
expressions of their inputs, and the surrounding rendering and parsing machinery
is unchanged and supplies those inputs rather than being a callee whose contract
the proof assumes). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14182"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgery anchors: the two frozen impl bodies, verbatim. Each is the COMPLETE
# text strictly between one method's `-- impl-start` and `-- impl-end`, so every
# variant's edit lies wholly inside that region — `same_spec` holds by
# construction and both `prove_correct` headers survive untouched. `_swap`
# asserts at import that each anchor is present and unique, so any drift in the
# frozen solution breaks this manifest loudly instead of silently retargeting.
# ---------------------------------------------------------------------------
_IMPL_FRAME = (
    "    let ruler := lines[headerRowCount]!\n"
    "    let out := [ruler] ++ lines ++ [ruler]\n"
    "    return out\n"
)
_IMPL_OFFSET = (
    "    let out := 2 + headerRowCount\n"
    "    return out\n"
)

assert _BASE.count(_IMPL_FRAME) == 1, "framing impl region drifted"
assert _BASE.count(_IMPL_OFFSET) == 1, "offset impl region drifted"


def _frame(body):
    """Full Solution.lean variant with ONLY the framing impl body replaced."""
    return _swap(_BASE, _IMPL_FRAME, body)


def _offset(body):
    """Full Solution.lean variant with ONLY the offset impl body replaced."""
    return _swap(_BASE, _IMPL_OFFSET, body)


# The frozen tactic body for the framing obligation. A soundness POSITIVE may
# retune its own proof — `variant_scope` requires the `prove_correct <name>`
# header to survive, not the tactic script, because reproving the SAME
# obligation for a differently-shaped impl is exactly what a positive does. The
# reject cases never touch this: a rival that retuned its proof would be
# attributing its rejection to a tactic gap, which is what the witness exists to
# rule out.
_PROVE_FRAME = "prove_correct surroundWithRuler by\n  loom_solve\n"

assert _BASE.count(_PROVE_FRAME) == 1, "framing proof region drifted"


def _frame_retuned(body, tactics):
    """Framing variant with the impl body replaced AND the proof retuned."""
    return _swap(_frame(body), _PROVE_FRAME,
                 "prove_correct surroundWithRuler by\n" + tactics)


# ---------------------------------------------------------------------------
# Witness builders. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches it through Velvet's own tester machinery: extract the
# executable, derive decidability of the pre/postcondition, derive the tester,
# then assert the tester REJECTS a concrete input. Every input type is decidable
# (Nat, List (List Char)) so the default `prove_*_decidable_for` tactics suffice
# — instances, not assumptions. No `axiom`/`sorry`/`native_decide` anywhere.
# ---------------------------------------------------------------------------
_PRE_FRAME = (
    "extract_program_for surroundWithRuler\n"
    "prove_precondition_decidable_for surroundWithRuler\n"
    "prove_postcondition_decidable_for surroundWithRuler\n"
    "derive_tester_for surroundWithRuler\n\n"
)
_PRE_OFFSET = (
    "extract_program_for dataStartOffset\n"
    "prove_precondition_decidable_for dataStartOffset\n"
    "prove_postcondition_decidable_for dataStartOffset\n"
    "derive_tester_for dataStartOffset\n\n"
)


def _wit_frame(lines, count):
    return (_PRE_FRAME +
            f"example : surroundWithRulerTester {lines} {count} = false := by\n"
            "  decide\n")


def _wit_offset(count):
    return (_PRE_OFFSET +
            f"example : dataStartOffsetTester {count} = false := by\n"
            "  decide\n")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot verify, the spec is SPEC-TOO-STRONG. Each keeps its obligation and
    # only reshapes the executable computation. The first three are
    # DEFINITIONALLY equal to the frozen impl and so verify under the frozen
    # `loom_solve` untouched; `pos-frame-middle-split-rejoined` is only
    # PROPOSITIONALLY equal and retunes its own tactic body (permitted — the
    # `prove_correct` header survives, and reproving the same obligation for a
    # differently-shaped impl is what a positive is for). That last one is the
    # one that tests the SPEC-TOO-STRONG direction rather than tolerance of a
    # re-spelling.
    # =====================================================================
    {
        "id": "pos-frame-cons",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the framed rendering by CONSING the framing line onto
        # the front and associating the trailing concatenation the other way,
        # instead of concatenating a one-element list on each side. `a :: (b ++ c)`
        # and `[a] ++ b ++ c` are the same list; the construction shape differs.
        "module": _frame(
            "    let ruler := lines[headerRowCount]!\n"
            "    let out := ruler :: (lines ++ [ruler])\n"
            "    return out\n"),
        "rationale": "structurally different but CORRECT: `ruler :: (lines ++ "
                     "[ruler])` is definitionally the same list as `[ruler] ++ "
                     "lines ++ [ruler]`, so the framing equation still holds at "
                     "every (lines, headerRowCount) in the precondition. A "
                     "correct reshape of the list CONSTRUCTION must verify, else "
                     "SPEC-TOO-STRONG on construction shape. Ports the nagini "
                     "pos-frame-direct-n positive (a reshaped list build).",
    },
    {
        "id": "pos-frame-inline-pick",
        "kind": "soundness",
        "expect": "verify",
        # The honest CHEAPEST correct implementation: no intermediate binding at
        # all, the positional pick written inline on both sides. This is the
        # grounded-oracle positive control — because the framing line is
        # `lines[headerRowCount]!`, a positional pick into the input rather than a
        # constant, even the cheapest faithful implementation must still CONSULT
        # the rendering at that position. There is no echo shortcut, which is what
        # `weak-frame-synthesised-ruler` confirms from the other side.
        "module": _frame(
            "    let out := [lines[headerRowCount]!] ++ lines ++ "
            "[lines[headerRowCount]!]\n"
            "    return out\n"),
        "rationale": "the grounded positive control: the framing value is a "
                     "positional pick into `lines`, so the cheapest honest "
                     "implementation still reads `lines[headerRowCount]!` — "
                     "inlining it twice and dropping the intermediate binding "
                     "computes the same result and MUST verify, else "
                     "SPEC-TOO-STRONG. Ports the nagini honest-cheapest control: "
                     "it demonstrates the spec is satisfiable by honest work and "
                     "that no constant shortcut exists for a grounded pin.",
    },
    {
        "id": "pos-offset-reassoc",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same integer reached by a different arithmetic form —
        # incrementing twice from the count instead of adding the literal 2 on
        # the left. Same value, different expression shape.
        "module": _offset(
            "    let out := headerRowCount + 1 + 1\n"
            "    return out\n"),
        "rationale": "structurally different but CORRECT: `headerRowCount + 1 + "
                     "1` is the same Nat as `2 + headerRowCount`, so the offset "
                     "equation still holds for every count. Must verify, else "
                     "SPEC-TOO-STRONG on arithmetic form. Direct port of the "
                     "nagini pos-offset-reassoc.",
    },

    {
        "id": "pos-frame-middle-split-rejoined",
        "kind": "soundness",
        "expect": "verify",
        # ADDED by the audit of this port. Every other positive here is
        # DEFINITIONALLY equal to the frozen impl — `ruler :: (lines ++ [ruler])`
        # and the inlined pick both reduce to the frozen term by `rfl`, so the
        # frozen `loom_solve` closes them unchanged and they only ever probe
        # whether the spec tolerates a different SPELLING of the same term. That
        # leaves the SPEC-TOO-STRONG direction almost untested: a spec is too
        # strong when it rejects a correct impl whose equality to the postcondition
        # needs an actual list-theory step, not when it rejects a re-spelling.
        # This positive supplies that: the middle is taken apart at the framing
        # position and rejoined, which is `lines` only via
        # `List.take_append_drop` — propositionally equal, NOT definitionally. It
        # therefore needs one retuning step (permitted for a positive: the
        # obligation header survives, only the tactic body differs), and its
        # verifying is the real evidence that the framing equation admits any
        # faithful construction rather than just the frozen syntax.
        "module": _frame_retuned(
            "    let ruler := lines[headerRowCount]!\n"
            "    let out := [ruler] ++ (lines.take headerRowCount ++ "
            "lines.drop headerRowCount) ++ [ruler]\n"
            "    return out\n",
            "  loom_solve\n  simp [List.take_append_drop]\n"),
        "rationale": "the only positive here whose correctness is NOT "
                     "definitional. The other three reshapes reduce to the frozen "
                     "term by `rfl`, so the frozen `loom_solve` closes them "
                     "untouched and they attest only that the spec tolerates a "
                     "re-spelling. This one splits the preserved middle at the "
                     "framing position and rejoins it: equal to `lines` by "
                     "`List.take_append_drop`, a propositional step, so it "
                     "exercises the SPEC-TOO-STRONG direction for real. Verified "
                     "with one retuning step (the `prove_correct` header is "
                     "preserved; only the tactic body differs, which is what a "
                     "positive reproving the same obligation is entitled to). If "
                     "it could NOT be proven, the framing equation would be "
                     "pinned to the frozen construction's syntax rather than to "
                     "the sequence it denotes.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the two nagini admiss-*-n3 cases. Those
    # self-called each function on a representative shape to establish that the
    # precondition ADMITS it (else PRECOND-TOO-STRONG). On this carrier
    # `dataStartOffset` carries NO `require` at all, so nothing could exclude any
    # count and that half is vacuous. `surroundWithRuler` does carry one
    # (`headerRowCount < lines.length`), and the live admissibility question is
    # whether it is EXACTLY strong enough: strong enough to make the positional
    # pick well-defined, yet weak enough to admit real renderings. The case below
    # witnesses both directions with a computation that is deliberately NOT the
    # frozen impl — resubmitting the frozen impl would re-run the gold build and
    # attest nothing this manifest is responsible for.
    # =====================================================================
    {
        "id": "admiss-require-exactly-carries-the-pick",
        "kind": "admissibility",
        "expect": "verify",
        # An INDEPENDENT total accessor with a NON-DEFAULT fallback. Out of range
        # it yields `['?']`, which is not what the postcondition's positional pick
        # yields, so this implementation can only satisfy the framing equation if
        # the `require` genuinely rules the index out-of-range case out. It
        # verifying is therefore a two-sided admissibility result: the
        # precondition is strong enough to pin the pick in range (the fallback is
        # unreachable), and it is satisfiable on real renderings (the post-image
        # is jointly achievable, not a contract no computation can meet). A spec
        # no implementation can satisfy reads exactly like a spec every
        # implementation satisfies; this separates the two.
        "module": _frame(
            "    let ruler := lines.getD headerRowCount ['?']\n"
            "    let out := [ruler] ++ lines ++ [ruler]\n"
            "    return out\n"),
        "rationale": "re-aims the nagini admiss-frame-n3 / admiss-offset-n3 pair. "
                     "The offset method has no `require`, so its half is vacuous; "
                     "the framing method's `require headerRowCount < lines.length` "
                     "is probed by an independent total accessor whose "
                     "out-of-range fallback `['?']` does NOT agree with the "
                     "postcondition's positional pick. It can only verify if the "
                     "precondition makes the fallback unreachable, so verifying "
                     "shows the precondition is exactly load-bearing AND that the "
                     "framing equation is jointly satisfiable on in-domain "
                     "renderings. Else PRECOND-TOO-STRONG or SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing regression, so
    # a rival that VERIFIED would be a true verify-does-not-imply-resolve break
    # rather than an artifact of the tactic script.
    #
    # ---- surroundWithRuler: part (P), the framing POSITION ----
    # =====================================================================
    {
        "id": "weak-frame-fixed-second-line",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: the framing line is read from a hard-wired
        # second position instead of tracking the requested header-row count.
        # Correct exactly where one header row was requested; wrong for every
        # other count whose line at that position differs.
        "module": _frame(
            "    let ruler := lines[1]!\n"
            "    let out := [ruler] ++ lines ++ [ruler]\n"
            "    return out\n"),
        "refinement": "this is the pre-image behaviour, and its faithful real "
                      "counterpart is the unpatched renderer: it frames with a "
                      "fixed second line of the rendering regardless of how many "
                      "header rows were requested. With more than one header row "
                      "requested that line is a HEADER line, not the "
                      "column-extent ruler, so the emitted rendering is framed "
                      "with header text. The failing regression requests three "
                      "header rows and asserts the emitted lines equal the exact "
                      "expected rendering, which a header-framed rendering does "
                      "not — so it would NOT resolve.",
        "rationale": "REJECT from part (P) of the framing equation: the "
                     "postcondition frames with `lines[headerRowCount]!`, and "
                     "this reads position 1 unconditionally. PARTIAL-DOMAIN — it "
                     "pins only the one-header-row sub-domain. Refuted at "
                     "`(lines = [['a'],['b'],['c'],['=']], headerRowCount = 3)`, "
                     "the three-header-row shape the failing regression "
                     "exercises, where position 3 holds the ruler and position 1 "
                     "does not. If it verified => SPEC-TOO-WEAK (admits the "
                     "pre-image behaviour). Ports the nagini frame-const-1.",
        "witness": _wit_frame("[['a'], ['b'], ['c'], ['=']]", "3"),
    },
    {
        "id": "weak-frame-position-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # A supporting near-miss on the SAME part but with the opposite defect:
        # the position DOES track the header-row count, just one line too far
        # down — the first data line rather than the ruler. Wrong for every count
        # (not only for counts other than one), so it is refuted at the
        # one-header-row point where weak-frame-fixed-second-line COINCIDES with
        # gold. That is what makes the pair informative rather than redundant:
        # between them they show the spec pins the position at count 1 as well as
        # at count 3.
        "module": _frame(
            "    let ruler := lines[headerRowCount + 1]!\n"
            "    let out := [ruler] ++ lines ++ [ruler]\n"
            "    return out\n"),
        "refinement": "framing one line further down copies the first DATA line "
                      "to the top and bottom instead of the column-extent ruler. "
                      "A real counterpart of this shape emits a rendering whose "
                      "outer lines are table data, so the round-trip in the "
                      "failing regression neither matches the expected rendering "
                      "on the way out nor parses back to the same table — it "
                      "would NOT resolve. It is also wrong for a single header "
                      "row, so it additionally breaks the unchanged tests that "
                      "pin the default rendering.",
        "rationale": "REJECT from part (P): an off-by-one on the framing "
                     "position. Refuted at `(lines = [['x'],['='],['1']], "
                     "headerRowCount = 1)` — the one-header-row point where "
                     "weak-frame-fixed-second-line agrees with gold, so this "
                     "rival probes a binder value that rival cannot reach and "
                     "the battery varies `headerRowCount` rather than pinning it "
                     "at the regression's count. If it verified => SPEC-TOO-WEAK "
                     "(the position would be unpinned up to a shift).",
        "witness": _wit_frame("[['x'], ['='], ['1']]", "1"),
    },

    # ---- surroundWithRuler: UNGROUNDED-ORACLE ECHO (the nagini historical hole)
    {
        "id": "weak-frame-synthesised-ruler",
        "kind": "uniqueness",
        "expect": "reject",
        # Frames with a SYNTHESISED constant line, never consulting the rendering
        # at all. This is the nagini sibling's historical directive-8 hole
        # re-run on this carrier: when the framing value was pinned to a fixed
        # sentinel, an implementation could echo that sentinel without reading the
        # input. Here the postcondition names a positional pick into `lines`, so a
        # constant cannot discharge it for any rendering whose line at that
        # position differs from the constant.
        "module": _frame(
            "    let ruler := ['=']\n"
            "    let out := [ruler] ++ lines ++ [ruler]\n"
            "    return out\n"),
        "refinement": "a synthesised constant framing line ignores the rendering "
                      "entirely, so the emitted outer lines bear no relation to "
                      "the actual column extents — they would not even have the "
                      "right width. A real counterpart of this shape emits "
                      "garbage frame lines, so the failing regression's assertion "
                      "that the emitted lines equal the exact expected rendering "
                      "fails, and the round-trip does not parse back — it would "
                      "NOT resolve.",
        "rationale": "UNGROUNDED-ORACLE ECHO, ported from the nagini "
                     "wrong-const-echo. The framing value in the postcondition is "
                     "`lines[headerRowCount]!` — GROUNDED in the input carrier, "
                     "not a constant — so a synthesised line cannot satisfy parts "
                     "(T) or (B). Refuted at `(lines = [['a'],['b'],['#','#']], "
                     "headerRowCount = 2)`, a rendering whose line at that "
                     "position is neither the constant nor a single character, so "
                     "the echo diverges in both content and width; it also adds a "
                     "third distinct `headerRowCount`. If it verified => "
                     "SPEC-TOO-WEAK, and the directive-8 hole the nagini sibling "
                     "closed would be open again here.",
        "witness": _wit_frame("[['a'], ['b'], ['#', '#']]", "2"),
    },

    # ---- surroundWithRuler: part (B), the BOTTOM framing element alone ----
    {
        "id": "weak-frame-bottom-only-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest near-miss on the framing equation. It reads the framing
        # line correctly for the TOP, preserves the middle verbatim, and produces
        # a result of exactly the right length — it is wrong ONLY in the bottom
        # element, which it takes from the hard-wired second position. Every other
        # framing rival is wrong in the position used for BOTH ends or in the
        # overall shape; nothing else tests that the two framing elements must be
        # the SAME line. Without this, an implementation that framed the top
        # correctly and the bottom from a stale index would pass the battery.
        "module": _frame(
            "    let out := [lines[headerRowCount]!] ++ lines ++ [lines[1]!]\n"
            "    return out\n"),
        "refinement": "this frames the top with the column-extent ruler but the "
                      "bottom with a fixed second line, so with more than one "
                      "header row requested the emitted rendering closes with a "
                      "HEADER line where a ruler belongs. A real counterpart of "
                      "this shape produces a rendering that is not a well-formed "
                      "constant-width table — the failing regression's emitted "
                      "lines differ from the expected rendering on the last line, "
                      "and parsing it back does not recover the table, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from part (B) alone: the postcondition demands the "
                     "SAME line `lines[headerRowCount]!` at both ends, and this "
                     "supplies it only at the top. A NARROW near-miss — correct "
                     "position for the top element, middle verbatim, correct "
                     "length — so it agrees with gold on strictly more of the "
                     "framing equation than any other rival here. Refuted at "
                     "`(lines = [['h'],['u'],['=','=']], headerRowCount = 2)`, "
                     "where the ruler at position 2 differs from the header line "
                     "at position 1. If it verified => SPEC-TOO-WEAK (the two "
                     "framing elements would not be forced to agree).",
        "witness": _wit_frame("[['h'], ['u'], ['=', '=']]", "2"),
    },

    # ---- surroundWithRuler: part (M), the preserved middle and the shape ----
    {
        "id": "weak-frame-omits-bottom",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the SHAPE: frames only the top, so the result is one element
        # short. Reads the framing line from the right position and preserves the
        # middle verbatim — the defect is purely that the closing framing element
        # is absent, which no other rival probes (the others all return a result
        # of the correct length).
        "module": _frame(
            "    let ruler := lines[headerRowCount]!\n"
            "    let out := [ruler] ++ lines\n"
            "    return out\n"),
        "refinement": "omitting the closing framing element emits a rendering "
                      "with no bottom border. A real counterpart of this shape "
                      "produces one line fewer than expected, so the failing "
                      "regression's line-by-line comparison against the expected "
                      "rendering fails immediately on length, and the result is "
                      "not a parseable constant-width table — it would NOT "
                      "resolve. It also breaks every unchanged test that pins the "
                      "default rendering, which likewise needs both borders.",
        "rationale": "REJECT from part (M): the postcondition pins the ENTIRE "
                     "sequence, so the result must carry both framing elements "
                     "and have length `lines.length + 2`; this yields "
                     "`lines.length + 1`. The only rival attacking the structural "
                     "SHAPE rather than the content of an element. Refuted at "
                     "`(lines = [['='],['d']], headerRowCount = 0)` — the "
                     "boundary count, a fourth distinct `headerRowCount` and the "
                     "smallest in-domain rendering, so the battery probes the "
                     "precondition's edge as well as its typical case. If it "
                     "verified => SPEC-TOO-WEAK (the result length would be "
                     "unpinned).",
        "witness": _wit_frame("[['='], ['d']]", "0"),
    },
    {
        "id": "weak-frame-middle-reordered",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks part (M) from the other side: both framing elements are correct
        # and the length is correct, but the rendering between them is not
        # verbatim — its lines come back in the opposite order. Nothing else in
        # the battery tests that the middle is preserved AS GIVEN rather than
        # merely preserved as a multiset of the right size.
        "module": _frame(
            "    let ruler := lines[headerRowCount]!\n"
            "    let out := [ruler] ++ lines.reverse ++ [ruler]\n"
            "    return out\n"),
        "refinement": "reversing the rendering between the borders emits the "
                      "data lines before the header lines. A real counterpart of "
                      "this shape emits a rendering whose rows are in the wrong "
                      "order, so the failing regression's comparison against the "
                      "expected rendering fails and parsing it back recovers the "
                      "wrong header metadata and the wrong rows — it would NOT "
                      "resolve.",
        "rationale": "REJECT from part (M): the postcondition requires the "
                     "middle to be `lines` VERBATIM, same order. This rival "
                     "honours the framing position, both framing elements and the "
                     "result length, and corrupts only the order of the preserved "
                     "rendering — the one aspect of the equation that a "
                     "length-and-borders check would miss. Refuted at `(lines = "
                     "[['n'],['=','='],['1']], headerRowCount = 1)`, an "
                     "asymmetric rendering (so reversing is observable) at a "
                     "`lines` value distinct from every other witness. If it "
                     "verified => SPEC-TOO-WEAK (the rendering's order would be "
                     "unpinned).",
        "witness": _wit_frame("[['n'], ['=', '='], ['1']]", "1"),
    },

    # ---- dataStartOffset: the affine relation, at three grains ----
    {
        "id": "weak-offset-fixed-three",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: the offset is the hard-wired constant that is
        # correct only when a single header row was requested.
        "module": _offset(
            "    let out := 3\n"
            "    return out\n"),
        "refinement": "this is the pre-image behaviour: the first data line is "
                      "assumed to sit at a fixed position, correct only when one "
                      "header row was requested. With three requested it points "
                      "two lines too early, so parsing begins inside the header "
                      "block: the failing regression recovers the wrong rows and "
                      "the wrong per-column units and dtypes, and its assertions "
                      "on those fail — it would NOT resolve.",
        "rationale": "REJECT from the offset equation `out = 2 + "
                     "headerRowCount`: a constant cannot equal an affine function "
                     "of the count except at one point. PARTIAL-DOMAIN — it pins "
                     "only the one-header-row sub-domain. Refuted at "
                     "`headerRowCount = 3`, the count the failing regression "
                     "exercises. If it verified => SPEC-TOO-WEAK (admits the "
                     "pre-image behaviour). Ports the nagini offset-const-3.",
        "witness": _wit_offset("3"),
    },
    {
        "id": "weak-offset-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: the offset tracks the count with the right slope
        # but the wrong intercept — one line too early for EVERY count, so it is
        # refuted at the one-header-row point where weak-offset-fixed-three
        # coincides with gold.
        "module": _offset(
            "    let out := 1 + headerRowCount\n"
            "    return out\n"),
        "refinement": "one line too early lands on the ruler line closing the "
                      "header block rather than the first data line, for every "
                      "requested count. A real counterpart of this shape begins "
                      "parsing at a border line, so the recovered table has a "
                      "spurious leading row and mis-parsed values — the failing "
                      "regression's assertions fail and it would NOT resolve. "
                      "Being wrong for a single header row too, it also breaks "
                      "the unchanged tests that read a default rendering.",
        "rationale": "REJECT from the offset equation on the INTERCEPT: `1 + "
                     "headerRowCount != 2 + headerRowCount` for every count. "
                     "Refuted at `headerRowCount = 1` — precisely the point where "
                     "weak-offset-fixed-three agrees with gold, so the pair "
                     "together shows the spec pins the offset at the "
                     "one-header-row count as well as at the regression's count, "
                     "and `headerRowCount` is varied rather than pinned. Ports "
                     "the nagini offset-off-by-one. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit_offset("1"),
    },
    {
        "id": "weak-offset-wrong-slope",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the SLOPE rather than the intercept: it counts the header rows
        # twice. Agrees with gold at a count of zero, so neither of the two rivals
        # above nor this one is refuted where another is: this one needs a count
        # of at least one, and it is refuted at two — the count no other offset
        # witness probes.
        "module": _offset(
            "    let out := 2 + 2 * headerRowCount\n"
            "    return out\n"),
        "refinement": "counting the requested header rows twice skips past the "
                      "start of the data whenever more than one was requested. A "
                      "real counterpart of this shape begins parsing partway into "
                      "the data, so the recovered table is missing leading rows "
                      "and the failing regression's assertions on the recovered "
                      "values fail — it would NOT resolve.",
        "rationale": "REJECT from the offset equation on the SLOPE: the "
                     "postcondition adds the count ONCE. This rival has the right "
                     "intercept and the right value at a count of zero, so it is "
                     "a different grain of wrongness from the constant and the "
                     "intercept rivals. Refuted at `headerRowCount = 2`, a count "
                     "no other offset witness probes. If it verified => "
                     "SPEC-TOO-WEAK (the count's coefficient would be unpinned).",
        "witness": _wit_offset("2"),
    },
    {
        "id": "weak-offset-boundary-only-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest near-miss in the battery: affine-correct on the whole
        # domain EXCEPT a single point, where it falls back to the pre-image
        # constant. Every other offset rival diverges from gold on a wide set of
        # counts, so a spec that pinned the offset only for counts of at least one
        # would reject all three and admit this. That would leave the modeled
        # behaviour uncertified at the boundary the precondition does not exclude
        # (the offset method carries no `require`, so a count of zero is in
        # domain).
        "module": _offset(
            "    let out := if headerRowCount = 0 then 3 else 2 + headerRowCount\n"
            "    return out\n"),
        "refinement": "this reports the correct offset for every requested count "
                      "except the boundary one, where it reverts to the pre-image "
                      "constant. A real counterpart of this shape special-cases "
                      "the no-requested-header-rows configuration to the old "
                      "hard-wired position, so a rendering with no header lines "
                      "is parsed starting one line past its first data row and "
                      "silently loses that row; the unchanged tests that read "
                      "such renderings fail, so it would NOT resolve.",
        "rationale": "REJECT from the offset equation on a NARROW sub-domain: the "
                     "postcondition is unconditional over every count and this "
                     "deviates only at zero. The method declares no `require`, so "
                     "the boundary count is in domain and the equation must hold "
                     "there too. Refuted at `headerRowCount = 0` — the fourth "
                     "distinct count in the offset lane, and the only point this "
                     "rival is wrong at, so its witness sits exactly on the "
                     "sub-domain its rationale claims. If it verified => "
                     "SPEC-TOO-WEAK (the spec would be blind to a "
                     "boundary-conditional regression to the pre-image "
                     "constant).",
        "witness": _wit_offset("0"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING
#
# The nagini sibling ships 11 SPEC cases (3 soundness, 2 admissibility, 6
# uniqueness) and 0 AXIOM_TESTS. It models the same two observable behaviours,
# but over `List[int]` row tags with three `@Pure` helpers, an explicit opaque
# per-block framing VALUE carried as a separate parameter, and fractional read
# permissions on both inputs. This bundle models the framing value as the
# positional pick `lines[headerRowCount]!` — read out of the input directly —
# and has no helpers and no heap.
#
#   nagini case              -> here                                status
#   ---------------------------------------------------------------------------
#   pos-frame-direct-n       -> pos-frame-cons                      RE-SHAPED
#   honest-cheapest          -> pos-frame-inline-pick                RE-EXPRESSED
#   pos-offset-reassoc       -> pos-offset-reassoc                   PORTED
#   admiss-frame-n3          -> admiss-require-exactly-carries-      RE-AIMED
#   admiss-offset-n3         ->   the-pick (both merged)             RE-AIMED
#   frame-mutate-block       -> (none)                               VACUOUS
#   frame-mutate-headers     -> (none)                               VACUOUS
#   wrong-const-echo         -> weak-frame-synthesised-ruler         PORTED
#   frame-const-1            -> weak-frame-fixed-second-line         PORTED
#   offset-const-3           -> weak-offset-fixed-three              PORTED
#   offset-off-by-one        -> weak-offset-off-by-one               PORTED
#   AXIOM_TESTS (0)          -> (none)                               N/A (empty)
#   (no nagini source)       -> weak-frame-position-off-by-one       ADDED
#   (no nagini source)       -> weak-frame-bottom-only-wrong         ADDED
#   (no nagini source)       -> weak-frame-omits-bottom              ADDED
#   (no nagini source)       -> weak-frame-middle-reordered          ADDED
#   (no nagini source)       -> weak-offset-wrong-slope              ADDED
#   (no nagini source)       -> weak-offset-boundary-only-wrong      ADDED
#   (no nagini source)       -> pos-frame-middle-split-rejoined      ADDED
#
# 15 velvet SPEC cases: 4 soundness, 1 admissibility, 10 uniqueness.
#
# PORTED (5). The four attacks that carry over with only the mechanics rewritten
#   — the two pre-image partial-domain rivals (fixed second line / fixed
#   constant offset), the off-by-one offset near-miss, and the ungrounded-oracle
#   echo — plus the arithmetic-reassociation positive. Each keeps the nagini
#   refinement ARGUMENT, restated over this carrier's vocabulary: none of them
#   can be expressed as a nagini row-tag list, an `Acc`, or a `@Pure` helper
#   call, and the echo case is re-derived against a positional pick rather than a
#   fixed sentinel.
# RE-SHAPED / RE-EXPRESSED (2 positives). pos-frame-direct-n indexed the block
#   with the raw count instead of routing through a `@Pure` helper; there are no
#   helpers here (the frozen impl already indexes directly), so the equivalent
#   "structurally different but correct" reshape is the list CONSTRUCTION —
#   consing rather than concatenating a singleton. honest-cheapest becomes
#   pos-frame-inline-pick: the same argument (a grounded framing value leaves no
#   echo shortcut, so even the cheapest faithful implementation must read the
#   input at that position), re-expressed as the inline positional pick with no
#   intermediate binding.
# RE-AIMED (the two admissibility cases, MERGED into one). Both nagini cases
#   self-called a function to show its `Requires` admits a representative shape.
#   `dataStartOffset` here carries NO `require`, so its half is vacuous — nothing
#   could exclude any count. `surroundWithRuler`'s `require headerRowCount <
#   lines.length` is live, so the merged case probes it from both sides at once
#   with an INDEPENDENT total accessor whose out-of-range fallback disagrees with
#   the postcondition's pick: it can verify only if the precondition makes the
#   fallback unreachable (not too weak for the pick) while still admitting real
#   renderings (not too strong, and the post-image jointly satisfiable). The
#   witness is deliberately not the frozen impl, which would only re-run the gold
#   build.
# VACUOUS (2, the whole frame-mutation class). Both nagini probes are MANDATORY
#   there because each input is held at a fractional read permission a store can
#   violate. This backend is referentially transparent: no heap, no aliasing, no
#   fractional permission, and NEITHER method declares a `mut` binder — all
#   inputs are immutable values. There is no read-only input to write through and
#   no substitute probe, so nothing is fabricated. This is a genuine carrier
#   collapse, not a spec hole: an implementation CANNOT mutate its input here.
# ADDED (7, by the adversarial audit of this port — no nagini counterpart). The
#   ported rivals left most of the framing equation's structure unattacked,
#   because nagini's framing value was a separate scalar parameter while here it
#   is a positional pick whose result is spliced into a sequence:
#  * weak-frame-position-off-by-one and weak-offset-wrong-slope. The two ported
#    partial-domain rivals are both correct at a count of one, so with only those
#    the battery would probe the position and the offset ONLY away from that
#    count. These two are wrong at counts where the ported rivals are right,
#    which is what makes `headerRowCount` genuinely varied instead of pinned.
#  * weak-frame-bottom-only-wrong. Nothing ported tested that the TOP and BOTTOM
#    framing elements must be the SAME line: every ported framing rival gets the
#    position wrong for both ends at once. A rival that frames the top correctly
#    and the bottom from a stale index honours the position, the middle and the
#    length, and would have passed the battery.
#  * weak-frame-omits-bottom. The only rival attacking the result's SHAPE. All
#    others return a sequence of the correct length, so nothing pinned that the
#    result carries both framing elements.
#  * weak-frame-middle-reordered. Nothing pinned that the rendering between the
#    borders is preserved VERBATIM rather than merely present with the right
#    length — the aspect a length-and-borders check would miss.
#  * weak-offset-boundary-only-wrong. All three other offset rivals diverge from
#    gold on a wide set of counts, so a spec pinning the offset only for counts
#    of at least one would have rejected them all and admitted a
#    boundary-conditional regression to the pre-image constant. The offset method
#    carries no `require`, so the boundary count is in domain.
#  * pos-frame-middle-split-rejoined (a POSITIVE, not a rival). The three ported
#    positives are all definitionally equal to the frozen impl, so the frozen
#    `loom_solve` closes each one untouched and the whole SPEC-TOO-STRONG lane
#    only ever attested that the spec tolerates a different SPELLING of the frozen
#    term. That is the weakest form of the soundness direction. This positive is
#    equal to the postcondition only PROPOSITIONALLY (`List.take_append_drop`), so
#    it is the first evidence that the framing equation admits a faithful
#    construction reached by a real proof step rather than by `rfl`.
# N/A (AXIOM_TESTS): the nagini sibling's is EMPTY (`meta.axioms == []`), and so
#   is this bundle's `axioms` region — both modeled behaviours are closed-form
#   expressions of their inputs, and the surrounding rendering and parsing
#   machinery is unchanged and SUPPLIES those inputs rather than being a callee
#   whose contract a proof assumes. Nothing was dropped to reach an empty axiom
#   lane, and the gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
# NO SOUNDNESS POSITIVE WAS DROPPED. Three of the four positives and the
#   admissibility case verify under the frozen `loom_solve` with the proof bodies
#   left byte-identical, because each is DEFINITIONALLY equal to the frozen impl.
#   `pos-frame-middle-split-rejoined` (added by the audit of this port) is not:
#   its middle is equal to `lines` by `List.take_append_drop`, a propositional
#   step, so it carries one extra `simp` in its own tactic body. That is what
#   makes it the positive that actually exercises SPEC-TOO-STRONG — a spec is too
#   strong when it rejects a correct impl needing a real proof step, not when it
#   rejects a re-spelling — and retuning is admissible for a positive
#   (`variant_scope` preserves the `prove_correct` header, not the script). No
#   obligation was neutered, no helper lemma was added at module level, and no
#   reject case retunes anything: a rival that changed its proof would be
#   attributing its rejection to a tactic gap, which the witness exists to
#   exclude.
#
# CLAUSE / BINDER / POINT COVERAGE (the part the gate does not check).
#   Both obligations are DEFENDED and ATTACKED. `prove_correct surroundWithRuler`
#   is defended by pos-frame-cons, pos-frame-inline-pick,
#   pos-frame-middle-split-rejoined and the admissibility
#   case, and attacked by six rivals; `prove_correct dataStartOffset` is defended
#   by pos-offset-reassoc and attacked by four.
#   Every independent part of the framing equation is attacked: the POSITION by
#   weak-frame-fixed-second-line and weak-frame-position-off-by-one, the framing
#   value's GROUNDING by weak-frame-synthesised-ruler, the BOTTOM element alone by
#   weak-frame-bottom-only-wrong, the result SHAPE by weak-frame-omits-bottom, and
#   the preserved MIDDLE by weak-frame-middle-reordered. The offset equation is
#   attacked at its constant, its intercept, its slope, and one isolated point.
#   Every INPUT BINDER is varied by the reject witnesses, so no binder is one a
#   rival could mishandle unnoticed:
#     `headerRowCount` (framing lane) at {0, 1, 2, 3} — the precondition's
#       boundary, the count the pre-image behaviour happens to get right, and the
#       count the failing regression exercises;
#     `headerRowCount` (offset lane) at {0, 1, 2, 3} — likewise, and the method
#       has no `require`, so zero is genuinely in domain;
#     `lines` at six DISTINCT values, varying length (2, 3, 3, 3, 3, 4), the
#       position of the ruler-shaped line within the rendering, per-line width
#       (one and two characters, so a width-blind echo is caught), and symmetry
#       under reversal.
#   The ten reject witnesses probe TEN DISTINCT input points, and each near-miss
#   is refuted at a point where the wider rivals agree with gold rather than
#   riding on another rival's counterexample: weak-frame-position-off-by-one and
#   weak-offset-off-by-one at the one-header-row count (where the two pre-image
#   rivals are CORRECT), weak-offset-wrong-slope at a count no other offset
#   witness visits, weak-offset-boundary-only-wrong at the single point it is
#   wrong at, and weak-frame-bottom-only-wrong at a rendering where the top
#   element it gets right and the bottom element it gets wrong differ. No two
#   rivals share a witness.
#
# WITNESS MECHANICS: every input type is decidable (`Nat`, `List (List Char)`)
#   and every postcondition is grounded in the inputs, so each witness pins its
#   inputs to concrete literals and closes `<name>Tester … = false` by `decide` —
#   no conditioning on an opaque carrier is needed, no witness binds a hypothesis,
#   and therefore no consistency probe applies (there are no assumptions that
#   could be jointly unsatisfiable). All ten were checked out-of-band with
#   scripts/lean_verify.sh in files with the `prove_correct` blocks stripped: each
#   ELABORATES against its rival (exit 0) and FAILS against the frozen solution
#   (exit 1) with the SEMANTIC error `Tactic `decide` proved that the proposition
#   <name>Tester … = false is false` — gold's tester accepts the point — never an
#   unknown identifier, type error, unfolding failure or timeout. No banned token
#   (sorry / admit / native_decide / axiom / opaque) appears in any witness.
AXIOM_TESTS = []
