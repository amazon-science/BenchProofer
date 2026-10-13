"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7205 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method,
``renderParameterDisplay (param : ParamValue) return (out : List Char)``, which
builds the bracketed display token for a recorded fixture parameter value. The
payload has two shapes, distinguished by the ``ParamValue`` constructor: a text
value (``textVal s``) and a byte-string value (``bytesVal s``). ``param`` is a
FREE, read-only value; the only ``require`` is ``simpleParam param`` (short,
printable content), which admits every value the observed behaviour concerns.

Three postcondition clauses pin the observable:

  (1) out = bracket (quotedRepr param)
        the exact token: the size-limited SAFE representation of the value,
        wrapped in the surrounding square brackets. On the admitted domain the
        safe representation is the content surrounded by apostrophes — plus a
        one-character byte-string marker on the byte shape.
  (2) ∀ s, param = textVal s → out = bracket ('\'' :: (s ++ ['\'']))
        the text shape re-stated structurally: an apostrophe, then the verbatim
        content, then a closing apostrophe, all bracketed. This is the
        DISCRIMINATING clause the fix introduces — the pre-change rendering
        emitted the bare content with NO apostrophes.
  (3) ∀ s, param = bytesVal s → out = bracket ('b' :: '\'' :: (s ++ ['\'']))
        the byte shape re-stated structurally: the byte-string marker, an
        apostrophe, the decoded content, a closing apostrophe, all bracketed.
        The pre-change rendering took the plain textual form of a byte value,
        which is not even well-defined and errors out under the observed config.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input may carry a fractional heap permission an impl can overwrite. Lean
    and Velvet are referentially transparent: ``param`` is an immutable value
    (no ``mut`` binder anywhere in this bundle), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe to
    build. Reported vacuous, not fabricated (see the module footer).
  * UNGROUNDED-ORACLE ECHO — N/A. Every clause is a total, fully unfolded
    function of the method's own argument (``quotedRepr`` / ``bracket`` are
    concrete ``def``s in the ``pure`` region; the ``axioms`` region declares
    nothing). There is no opaque answer key to echo — the cheapest honest impl
    (``return bracket (quotedRepr param)``) is the CORRECT answer, so it is
    carried as a positive control, matching the nagini bundle's own note that
    the grounded-oracle echo is the right answer here, not a wrong one.
  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals right on part of the input domain
    but diverging on a sub-domain: the pre-change plain rendering (both shapes),
    a one-sided delimiter (open apostrophe only), a first-character corruption,
    and a byte-shape-only plain rendering. Each attacks a specific clause and is
    refuted at a concrete input on the sub-domain where it diverges.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT whose two structural
clauses quantify over ``∀ s : List Char`` — an INFINITE domain, so the standard
``derive_tester_for`` machinery cannot synthesize a ``Decidable`` instance for
the postcondition and no tester is available. Instead each witness names the
program EXTRACTED from the variant (``renderParameterDisplayExec``, produced by
``extract_program_for``) and states, at ONE concrete input, that its result
disagrees with the value clause (1) demands there:

    (match renderParameterDisplayExec <input> with | DivM.res r => r | _ => [])
      ≠ bracket (quotedRepr <input>)

``decide`` reduces the extracted program on a concrete input, so the witness
ELABORATES against a rival whose output diverges from the spec value there, and
is FALSE (fails to build) against the frozen solution, whose output equals it —
exactly the two-halves discrimination the gate requires. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can interfere. No
``sorry`` / ``admit`` / ``native_decide`` is used; the discrimination is genuine.

BINDER / CLAUSE COVERAGE. ``param`` is the single input binder, but it ranges
over BOTH constructors and over varying content. The reject witnesses probe five
distinct inputs and move ``param`` across both shapes: ``textVal`` at three
distinct contents (``foo`` / ``bar`` / ``foo`` corrupted) and ``bytesVal`` at
``Hello World``. Clause (2) (text shape) is attacked by the plain-text,
one-sided, and first-char rivals; clause (3) (byte shape) by the bytes-plain and
all-plain rivals; clause (1) subsumes both.

AXIOM lane: EMPTY. The only callee is modeled DEEPLY as ``quotedRepr`` (an
A-reference validated by G-AX, not consumed as an axiom); the ``axioms`` region
declares no ``axiom``. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7205"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region (everything the variants replace). It lies wholly
# ---- inside the single method's `-- impl-start` / `-- impl-end` region and is
# ---- unique in Solution.lean (the `let r := quotedRepr param` line occurs
# ---- nowhere else); both facts are asserted at load by _swap.
_GOLD_IMPL = (
    "    let r := quotedRepr param\n"
    "    return bracket r"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# The frozen proof body (the `prove_correct` tactic script). Elided from the
# consumer spec view, so a variant that adds an in-region `assert` (which raises
# an extra side goal `loom_solve` leaves open) may retune it to discharge that
# goal — the obligation STATEMENT and the `prove_correct` header are untouched,
# so same_spec still holds. Anchored on the exact frozen script.
_GOLD_PROOF = "prove_correct renderParameterDisplay by\n  loom_solve"

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The postcondition quantifies over `∀ s : List Char`
# ---- (infinite), so `derive_tester_for` cannot build a decidable tester. A
# ---- witness instead extracts the program and evaluates it at a concrete
# ---- input, comparing against the value clause (1). Checked in a file whose
# ---- `prove_correct` block has been stripped.
_EXTRACT = "extract_program_for renderParameterDisplay\n\n"


def _witness(input_expr):
    """A refutation witness at one concrete `ParamValue` input.

    States that the extracted program's result disagrees with the value the
    postcondition demands there. Elaborates (by `decide`) against a rival that
    diverges at that input; false against the frozen solution, whose result
    matches — the required discrimination.
    """
    return (
        _EXTRACT +
        "example :\n"
        f"    (match renderParameterDisplayExec ({input_expr}) with\n"
        "     | DivM.res r => r\n"
        "     | _ => []) ≠ bracket (quotedRepr "
        f"({input_expr})) := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify; else the post-image is SPEC-TOO-STRONG. The
    # obligation statement is preserved and only the executable surface is
    # reshaped.
    # =====================================================================
    {
        "id": "pos-inline-oracle",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest impl: the grounded oracle materialized directly,
        # with no intermediate `let`. Observationally identical to gold on every
        # input; the single equality clause still discharges under the frozen
        # `loom_solve`.
        "module": _impl("    return bracket (quotedRepr param)"),
        "rationale": "a correct reshape that inlines the safe-representation "
                     "oracle (dropping the intermediate binding) computes the "
                     "identical token on every input and adds no new proof "
                     "obligation, so clause (1) `out = bracket (quotedRepr "
                     "param)` and the two structural clauses (2)-(3) still "
                     "discharge under the frozen `loom_solve`; else "
                     "SPEC-TOO-STRONG on impl shape.",
    },
    {
        "id": "pos-per-shape-match",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely different shape: split on the payload constructor and
        # spell out each rendering with the explicit apostrophe/marker form of
        # clauses (2)-(3), instead of routing through `quotedRepr`. Same value
        # flow on both shapes; must verify.
        "module": _impl(
            "    match param with\n"
            "    | .textVal s => return bracket ('\\'' :: (s ++ ['\\'']))\n"
            "    | .bytesVal s => return bracket ('b' :: '\\'' :: (s ++ ['\\'']))"),
        "rationale": "a correct reshape that branches on the payload shape and "
                     "constructs each rendered token with the explicit "
                     "apostrophe (and byte marker) form matching clauses (2) and "
                     "(3) computes the same token as `quotedRepr` on both shapes, "
                     "so all three clauses still discharge; a faithful correct "
                     "variant must verify (else SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY. The `require simpleParam param` clause admits every value
    # the observed behaviour concerns, but the "a normal input satisfies the
    # precondition" probe is vacuous to state directly here (`simpleParam` is
    # not decidable at a literal without an instance). It is re-aimed at the
    # residual admissibility risk: that the postcondition is UNSATISFIABLE /
    # DEGENERATE at the two F2P corners (a text id and a byte-string parameter).
    # The case discharges an in-region `assert` pinning the value clause at
    # those corners symbolically; the impl is kept verbatim so the method's own
    # three obligations discharge too. The assert is live, not decoration: a
    # false claim about the same point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-f2p-corners",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (bracket (quotedRepr (ParamValue.textVal ['f','o','o']))\n"
            "         = '[' :: '\\'' :: 'f' :: 'o' :: 'o' :: '\\'' :: ']' :: [] ∧\n"
            "       bracket (quotedRepr (ParamValue.bytesVal "
            "['s','p','a','m']))\n"
            "         = '[' :: 'b' :: '\\'' :: 's' :: 'p' :: 'a' :: 'm' :: '\\'' "
            ":: ']' :: []))\n"
            "    let r := quotedRepr param\n"
            "    return bracket r",
            "prove_correct renderParameterDisplay by\n  loom_solve <;> decide"),
        "rationale": "the value clause is satisfiable AND non-degenerate at both "
                     "F2P corners: a text id `foo` must render as the bracketed "
                     "apostrophe-quoted `['foo']`, and a byte-string parameter "
                     "must render with its one-character byte marker as "
                     "`[b'spam']`. The in-region assert must discharge (else the "
                     "obligation is degenerate at the point the fix targets); the "
                     "impl is verbatim so the three ensures clauses still "
                     "discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-plain-no-delimiters",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: render the bare content with NO surrounding
        # apostrophes on either shape (the implicit plain-text form). Wrong on
        # every non-empty content.
        "module": _impl(
            "    match param with\n"
            "    | .textVal s => return bracket s\n"
            "    | .bytesVal s => return bracket s"),
        "refinement": "this IS the pre-change behaviour (the bare content with "
                      "no apostrophes). The failing test requests a text "
                      "parameter and asserts the display shows it "
                      "apostrophe-quoted; this rival shows the bare content "
                      "(`foo` not `'foo'`), so the pinned display line still does "
                      "not match. And on the byte shape the plain textual form is "
                      "not well-defined under the observed strict config, which "
                      "is the crash the fix removes. It would NOT resolve.",
        "rationale": "REJECT from clause (2) (and clause (1)): for a text value "
                     "the token must be `bracket ('\\'' :: s ++ ['\\''])` "
                     "(apostrophe-delimited), but the bare-content rival emits "
                     "`bracket s`, missing both delimiters. Refuted at "
                     "`param = textVal ['f','o','o']`.",
        "witness": _witness("ParamValue.textVal ['f','o','o']"),
    },
    {
        "id": "weak-open-quote-only",
        "kind": "uniqueness",
        "expect": "reject",
        # One-sided delimiter: the opening apostrophe is present, the closing
        # one omitted. Correct on the prefix but the token is one code point
        # short and does not end in the apostrophe.
        "module": _impl(
            "    match param with\n"
            "    | .textVal s => return bracket ('\\'' :: s)\n"
            "    | .bytesVal s => return bracket ('b' :: '\\'' :: s)"),
        "refinement": "a counterpart that emitted the opening apostrophe but "
                      "omitted the closing one would render `foo` as `['foo]` "
                      "(missing the trailing apostrophe before the bracket), so "
                      "the test that pins the display line with BOTH apostrophes "
                      "would observe the one-sided form and still fail. It would "
                      "NOT resolve.",
        "rationale": "REJECT from clause (2) (and clause (1)): the token must be "
                     "`bracket ('\\'' :: s ++ ['\\''])`, but omitting the closing "
                     "apostrophe yields `bracket ('\\'' :: s)`, one code point "
                     "short and not apostrophe-terminated. Refuted at "
                     "`param = textVal ['b','a','r']` — a distinct text content "
                     "from the plain-text rival.",
        "witness": _witness("ParamValue.textVal ['b','a','r']"),
    },
    {
        "id": "weak-first-char-corrupt",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct delimiters and length, but the first content code point is
        # forced to a fixed letter. Right on the whole domain EXCEPT content
        # whose first character is not that letter.
        "module": _impl(
            "    match param with\n"
            "    | .textVal s =>\n"
            "        return bracket ('\\'' :: ('X' :: s.tail ++ ['\\'']))\n"
            "    | .bytesVal s => return bracket ('b' :: '\\'' :: (s ++ ['\\'']))"),
        "refinement": "a counterpart that mangled the first content character of "
                      "every text parameter would render `foo` as `'Xoo'`, so "
                      "the test pinning the display value to the verbatim quoted "
                      "content would observe the corrupted first character and "
                      "still fail. It would NOT resolve.",
        "rationale": "REJECT from clause (2) (and clause (1)): the delimited "
                     "content must be the verbatim `s`, but forcing the first "
                     "code point to `'X'` diverges wherever `s` does not begin "
                     "with `X`. Refuted at `param = textVal ['f','o','o']` — the "
                     "content is corrupted to `'Xoo'`. (Shares the `foo` content "
                     "with the plain-text rival but diverges for a different "
                     "reason — a body corruption, not a missing delimiter — and "
                     "at a different output, so its witness is genuine, not "
                     "shared.)",
        "witness": _witness("ParamValue.textVal ['f','o','o']"),
    },
    {
        "id": "weak-bytes-plain",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the text shape, but renders a byte value as its bare
        # content — no byte marker, no apostrophes. Attacks clause (3) alone: a
        # rival that handled text correctly (so the text clauses pass) but
        # dropped the byte-shape rendering.
        "module": _impl(
            "    match param with\n"
            "    | .textVal s => return bracket ('\\'' :: (s ++ ['\\'']))\n"
            "    | .bytesVal s => return bracket s"),
        "refinement": "a counterpart correct on text parameters but rendering a "
                      "byte-string value as its bare content would drop the byte "
                      "marker and apostrophes AND, in the real code, take the "
                      "plain textual form of a byte value — the very operation "
                      "that errors out under the observed strict config. The "
                      "byte-parameter regression test would still fail. It would "
                      "NOT resolve.",
        "rationale": "REJECT from clause (3) (and clause (1)): a byte value's "
                     "token must be `bracket ('b' :: '\\'' :: s ++ ['\\''])` (the "
                     "byte marker and apostrophes), but the rival emits "
                     "`bracket s`, dropping all three. Refuted at "
                     "`param = bytesVal ['H','e','l','l','o',' ','W','o','r',"
                     "'l','d']` — the byte shape, which the text-only rivals "
                     "never probe.",
        "witness": _witness(
            "ParamValue.bytesVal "
            "['H','e','l','l','o',' ','W','o','r','l','d']"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 3 uniqueness rivals, 1 frame-mutation) plus 2 AXIOM_TESTS. The
# sibling models the SAME behaviour (rendering the bracketed parameter token via
# the size-limited safe representation) but over a `List[int]` code-point carrier
# and TEXT payloads only. This bundle models the same rendering over a
# `ParamValue` carrier that ALSO distinguishes the byte-string shape (the F2P
# `b'Hello World'` regression), so the port carries the sibling's text rivals AND
# adds a byte-shape rival that the sibling's carrier cannot express.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   S1 pos-control-reshape          -> pos-per-shape-match           PORTED
#   S2 pos-control-concat           -> pos-inline-oracle             PORTED
#   FM1 frame-mutation-write-param  -> (none)                        VACUOUS
#   U1 plain-text-no-delimiters     -> weak-plain-no-delimiters      PORTED
#   U2 open-quote-only              -> weak-open-quote-only          PORTED
#   U3 first-char-wrong             -> weak-first-char-corrupt       PORTED
#   (no sibling counterpart)        -> weak-bytes-plain              ADDED
#   AXIOM_TESTS (ax-sound / ax-cover) -> (none)                      DROPPED
#
# VACUOUS (frame-mutation): the sibling rejects an impl that WRITES to a
#   read-only input held at Acc(list_pred(param), 1/2). This backend is
#   referentially transparent, has no heap and no aliasing, and this bundle
#   declares no `mut` binder — there is no read-only input to overwrite and no
#   substitute probe to build. Not fabricated (per the porting map: this class
#   is vacuous on Lean/Velvet).
# ADMISSIBILITY: the sibling folds its admissibility witness into S1 (an embedded
#   `Assert(len(param)+2 <= maxsize)`). It is broken out here as a dedicated
#   case (admiss-f2p-corners) re-aimed at the residual admissibility risk on this
#   backend — that the value clause is degenerate at the F2P corners — via an
#   in-region assert pinning the rendering of a text id and a byte parameter.
# ADDED (1): weak-bytes-plain — a rival correct on the text shape but rendering a
#   byte value as its bare content, attacking clause (3) (the byte shape) alone.
#   The sibling's `List[int]` carrier has a single payload shape and cannot
#   express the byte/text split, so it has no counterpart; the F2P
#   `test_show_fixture_action_with_bytes` observes exactly this shape, so a
#   battery that never moved `param` onto the `bytesVal` constructor would say
#   nothing about clause (3). Refuted by a machine-checked witness on
#   `bytesVal 'Hello World'`.
# DROPPED (AXIOM_TESTS): the sibling's ax-sound-saferepr / ax-cover-saferepr
#   belong to G-AX. This bundle models the callee deeply as `quotedRepr` (an
#   A-reference validated by axiom_check.py) and declares no consumed axiom, so
#   there is nothing for THIS gate to probe.
#
# WITNESS DISCRIMINATION. The postcondition quantifies over `∀ s : List Char`
#   (infinite), so `derive_tester_for` cannot synthesize a decidable tester. Each
#   witness instead extracts the program (`renderParameterDisplayExec`) and, at a
#   concrete input, states its result diverges from the value clause (1) demands
#   there. `decide` reduces the extracted program: the witness elaborates against
#   a rival diverging at that input and is FALSE against the frozen solution
#   (whose result matches), so every rejection is attributed to the spec, not a
#   tactic gap. Verified during authoring: rival build exit 0, gold build exit
#   != 0, for each rival.
#
# BINDER / POINT COVERAGE. The single input binder `param` is moved across BOTH
#   constructors and varying content by the four reject witnesses:
#     (textVal ['f','o','o'])                weak-plain-no-delimiters
#     (textVal ['b','a','r'])                weak-open-quote-only
#     (textVal ['f','o','o'])                weak-first-char-corrupt
#     (bytesVal 'Hello World')               weak-bytes-plain
#   so `param` is not pinned to one shape or one content; clause (2) (text) is
#   attacked by three rivals, clause (3) (bytes) by one, and clause (1) by all.
#   weak-plain-no-delimiters and weak-first-char-corrupt share the `foo` content
#   but diverge from gold for DIFFERENT reasons (missing delimiter vs body
#   corruption) and produce different outputs, so each carries a genuine witness.
AXIOM_TESTS = []
