"""properties.py — G-PBT falsification battery for django__django-13512 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct serializeStringValue`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single code-point sequence):

  serializeStringValue (text : List Char) return (out : List Char)
    ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])   -- THE (only) clause

so the single clause pins THREE independent structural sub-behaviours of the
rendered text:

  * OPEN + CLOSE FRAMING: the result is a leading delimiter, then the escaped
    body, then a trailing delimiter (``'"' :: … ++ ['"']``);
  * PER-CODE-POINT BODY: the body is ``jsonEscapedSeq text`` — a front-recursive
    fold applying ``jsonChar`` to every code point, where ``jsonChar`` is a
    FROZEN pure ``def``. Its arms pin, independently:
      - the two-character backslash form for the delimiter code point (34) and
        the escape code point (92);
      - the short/control forms for the low code points (< 32);
      - and — the whole behaviour at issue — the LITERAL pass-through of every
        code point at or above 128 (``else [c]``).

``jsonEscapedSeq`` is GROUNDED in the input (a total fold over ``text``); the
``axioms`` region is empty (``jsonEscapedSeq`` is a deep A-reference validated ==
the real standard-library string renderer by axiom_check.py, NOT a consumed
answer key), so there is no wrong echo to build and the ungrounded-oracle probe
is replaced by two honest positive controls plus an admissibility case. The sole
INPUT BINDER is ``text``.

THE CARRIER IS FULLY TRANSPARENT. ``jsonEscapedSeq`` / ``jsonChar`` / ``hexDigit``
all compute on ``Char`` literals, so a witness reaches the impl through Velvet's
extractor (``extract_program_for serializeStringValue`` gives
``serializeStringValueExec text = NonDetT.run (serializeStringValue text)``) and
states ``serializeStringValueExec s ≠ DivM.res ('"' :: (jsonEscapedSeq s ++
['"']))`` at a concrete ``s`` — with ``decide`` closing the residual literal (no
opaque leaf, no carrier conditioning needed, so no witness binds a hypothesis and
there is no joint-satisfiability obligation). Each reject rival is a straight-line
loop-free CLOSED FORM whose extracted program DOES reduce to a literal, so the
witness ELABORATES against the rival (exit 0, machine-checked).

THE FROZEN SOLUTION CANNOT SERVE AS THE SECOND SUBJECT, and this is the one place
where a naive reading of the exit codes would be wrong. The frozen impl carries a
``while`` loop whose extracted program does NOT reduce, so ``decide`` cannot even
be instantiated against it: the gold-side build fails with

    error: failed to synthesize
      Decidable ¬(NonDetT.run do let r ← forIn Lean.Loop.mk ...) = DivM.res ...

which is the ``_STUCK_INSTANCE`` shape — a MISSING DECIDABLE INSTANCE, not a
refutation. Measured here (audit attack B′, two real builds per case): a FORGERY
differing from the witness ONLY in dropping the ``¬`` — i.e. asserting the frozen
impl is CORRECT at that input, the opposite of a refutation — fails against the
frozen solution with the SAME ``failed to synthesize Decidable`` error. So gold's
nonzero exit carries NO information about the claim, and "the witness fails on
gold" is NOT evidence of discrimination on this cell.

Every reject case therefore carries an explicit ``witness_reference``: the
loop-free ``jsonEscapedSeq text`` impl, which shares the frozen spec and VERIFIES
(it is this battery's ``pos-control-direct``), and whose extracted program DOES
reduce. An impl the verifier accepts cannot violate its own spec, so a genuine
witness must still fail there — and against THAT subject the exit code tracks the
claim, which is what makes the rejection attributable to the spec:

    witness (¬-form) vs reference  -> exit 1, `decide` proved `False` is false
    forgery (=-form) vs reference  -> exit 0   (claim flipped => verdict flipped)

Both directions were measured with ``scripts/lean_verify.sh`` for all four reject
cases. The rival-side forgery is the same evidence read from the other end: it
prints the rival's CONCRETE output against the spec body, e.g.
``['\\', 'u', '"'] = jsonEscapedSeq ['你'] ++ ['"'] is false``, so each rival is
observably — not merely syntactically — wrong at its probed input.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as a
    MANDATORY rival (store ``text[i-1] := 97`` through a reference held at
    ``Acc(list_pred(text), 1/2)``) because a store needs full permission. Lean
    and Velvet are referentially transparent: ``text`` is an immutable value,
    this bundle declares NO ``mut`` binder over any input (the only ``mut``
    locals are the fresh accumulator ``result`` and the counter ``i``), and there
    is no heap and no aliasing — so there is no read-only input to overwrite and
    no substitute probe to build. Not fabricated (per the porting map: this class
    is vacuous on Lean/Velvet).
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each nagini
    partial-domain rival re-expresses directly onto one arm of the frozen
    ``jsonChar`` fold (or the framing), plus one added rival for the escape
    code-point arm the nagini sibling does not attack separately.
  * BRANCH-REORDER positive control — NOT PORTABLE. The nagini sibling reorders
    the ``if c==34 / elif c==92`` branches, but on this carrier that branch logic
    lives in the FROZEN ``jsonChar`` pure ``def`` (outside the impl region), not
    in the impl; the impl merely calls ``jsonChar c``. There is no branch inside
    the impl region to reorder, so the split-assembly reshape (below) is the
    structural-reshape positive control instead.
  * ADMISSIBILITY — APPLIES, re-aimed. The nagini sibling admits an F2P-shaped
    input against a permission precondition; this bundle's pre-conditions region
    is empty, which is NOT on its own a reason to drop the lane. On a total
    carrier the same lane detects an obligation that is UNSATISFIABLE or only
    degenerately satisfiable at exactly the input class at issue, which
    ``admiss-f2p-nonascii`` discharges by evaluation at a concrete
    two-code-point non-ASCII input before closing the frozen obligation verbatim.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; ``jsonEscapedSeq``
is a deep A-reference validated == the real compiled string renderer by
axiom_check.py — that is G-AX's job, and this gate ignores ``AXIOM_TESTS``).
"""
from pathlib import Path

INSTANCE = "django__django-13512"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct serializeStringValue
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-code-point loop plus
# the final assembly). Reject rivals replace it with a loop-free closed form (so
# their extracted program reduces under decide); the direct positive control
# replaces it with the grounded one-liner.
_IMPL = (
    "    let mut result : List Char := []\n"
    "    let mut i := text.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ text.length\n"
    "      invariant result = jsonEscapedSeq (text.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := text[i - 1]!\n"
    "      result := jsonChar c ++ result\n"
    "      i := i - 1\n"
    "    return '\"' :: (result ++ ['\"'])\n"
)

# The final assembly line alone (unique in the file). The split-assembly positive
# control reshapes ONLY this, keeping the loop and its invariants byte-identical.
_RET = "    return '\"' :: (result ++ ['\"'])\n"

# The frozen prove_correct tactic body (unique in the file, elided from the spec
# view). The direct positive control retunes it (the loop is gone, so `loom_solve`
# alone closes the residual goal); the split-assembly positive keeps it verbatim
# (an associativity rewrite the frozen `simp_all` still discharges); every reject
# rival keeps it as-is (it fails to close the wrong impl — the intended rejection —
# but the witness, not the tactic failure, is what the gate scores).
_PROOF = (
    "prove_correct serializeStringValue by\n"
    "  loom_solve\n"
    "  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]\n"
    "  simp_all\n"
)

for _a in (_IMPL, _RET, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


def _rival(body_expr: str) -> str:
    """Solution.lean whose impl body is a single loop-free grounded return, the
    escaped body computed as a closed-form `flatMap`/identity over `text` framed
    by the two delimiters."""
    return _swap(_BASE, _IMPL, f"    return '\"' :: ({body_expr} ++ ['\"'])\n")


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `serializeStringValueExec s` is `NonDetT.run (serializeStringValue s)`;
# ---- `≠ DivM.res ('"' :: (jsonEscapedSeq s ++ ['"']))` says the impl's output
# ---- contradicts the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. The loop-free rival reduces under `decide`; gold's loop stays
# ---- stuck, so the same witness fails on gold — the required discrimination.
_EXTRACT = "extract_program_for serializeStringValue\n\n"


def _witness(inp: str) -> str:
    return _EXTRACT + (
        "example : serializeStringValueExec " + inp + " ≠ "
        "DivM.res ('\"' :: (jsonEscapedSeq " + inp + " ++ ['\"'])) := by\n"
        "  unfold serializeStringValueExec serializeStringValue\n"
        "  simp [NonDetT.run, pure] <;> decide\n"
    )


# The SECOND SUBJECT every witness is refuted against, in place of the frozen
# solution. See the module docstring: the frozen impl's extracted program carries
# an un-reduced `forIn Lean.Loop.mk`, so `decide` has no `Decidable` instance to
# synthesize against it and the gold-side build fails with the SAME error for a
# claim and for its exact negation — an exit code that attests to nothing. This
# reference is the loop-free grounded closed form: it shares the frozen spec
# byte-for-byte, it VERIFIES (it is `pos-control-direct`'s module, and the gate
# re-checks both facts before using it), and its extracted program reduces, so a
# witness refuted against it is refuted against an impl KNOWN to satisfy the spec.
_WITNESS_REF = _swap(
    _rival("jsonEscapedSeq text"),
    _PROOF,
    "prove_correct serializeStringValue by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `jsonEscapedSeq text` is GROUNDED in the argument (a
    # total fold), so `return '"' :: (jsonEscapedSeq text ++ ['"'])` is a correct
    # fully-grounded implementation, not an ungrounded-oracle echo — and it
    # doubles as proof the spec is not echo-vulnerable: any WRONG constant/echo
    # fails the single clause. The loop is gone, so the frozen proof body's loop
    # reasoning is unneeded and the residual goal closes under `loom_solve` alone.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _rival("jsonEscapedSeq text"),
            _PROOF,
            "prove_correct serializeStringValue by\n  loom_solve"),
        "rationale": "the post-image body `jsonEscapedSeq text` is GROUNDED in the "
                     "input (a total fold, no opaque answer key), so returning the "
                     "framed body is the honest cheapest CORRECT impl. It MUST "
                     "verify — the clause is literally `out = '\"' :: (jsonEscapedSeq "
                     "text ++ ['\"'])` — else the single postcondition clause is "
                     "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable: "
                     "any wrong constant/echo would fail the clause. Verified to "
                     "build (loom_solve closes the loop-free goal).",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that keeps the frozen backward loop and its invariants BYTE-IDENTICAL, only
    # reshaping the final assembly: instead of `'"' :: (result ++ ['"'])`, prepend
    # the opening delimiter first (`let opened := '"' :: result`) then append the
    # closing one (`opened ++ ['"']`). Cons/append-associativity equal, so every
    # loop invariant and the single obligation still discharge under the frozen
    # proof script with NO retune. A faithful correct reshape that could NOT verify
    # would mean the postcondition is over-fit to the one-expression assembly FORM
    # => SPEC-TOO-STRONG. (This replaces the nagini sibling's branch-reorder
    # positive, which is not portable: the branch logic lives in the frozen
    # `jsonChar` pure def, not the impl region.)
    # =====================================================================
    {
        "id": "pos-control-split-assembly",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RET,
            "    let opened := '\"' :: result\n"
            "    return opened ++ ['\"']\n"),
        "rationale": "structurally different CORRECT reshape of the final assembly: "
                     "prepend the opening delimiter then append the closing one, "
                     "cons/append-associativity equal to the frozen one-expression "
                     "form, keeping the loop and every invariant byte-identical. The "
                     "single obligation still discharges under the frozen proof "
                     "script. A faithful reshape MUST verify, else the clause is "
                     "over-fit to the assembly FORM => SPEC-TOO-STRONG. Verified to "
                     "build under the frozen proof.",
    },

    # =====================================================================
    # ADMISSIBILITY — LANDED (the port had recorded this lane as vacuous because
    # the `pre-conditions` region is empty; that reason is not sufficient). On a
    # TOTAL carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    # UNSATISFIABLE, or satisfiable only degenerately, at exactly an input of the
    # shape the failing tests exercise — and a spec no impl can meet at that input
    # reads exactly like a spec every impl meets. "The post-image is a total
    # function, so it is satisfiable everywhere by construction" is an ARGUMENT;
    # this case is the machine-checked version of it, aimed at the concrete input
    # class at issue (a sequence of code points at or above 128) rather than at the
    # empty-precondition fact.
    #
    # Three `have`s discharge, BY EVALUATION, before the frozen obligation is
    # closed verbatim:
    #   * hsat        — the post-image at a two-code-point non-ASCII input is a
    #                   definite, fully-evaluated value: the two code points framed
    #                   by the delimiters, so the obligation IS satisfiable there;
    #   * hliteral    — the body at that input is the two code points THEMSELVES
    #                   (the literal pass-through), i.e. the post-image is
    #                   non-degenerate and pins the behaviour at issue;
    #   * hnotescaped — the body is NOT the six-character escaped form, so the
    #                   obligation is not satisfiable by the pre-narrowing mode at
    #                   this input — the admissible point is the RIGHT one.
    # The impl and the frozen tactic script are kept byte-identical (the `have`s
    # are inserted ahead of them), so the method's own obligation still discharges
    # and a failure here would be attributable to the admissibility claim alone.
    # The `have`s are LIVE, not scaffolding: replacing hsat's right-hand side with
    # the escaped form makes the build FAIL semantically (`decide` proved ... is
    # false) — measured, not assumed.
    # =====================================================================
    {
        "id": "admiss-f2p-nonascii",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct serializeStringValue by\n"
            "  have hsat : '\"' :: (jsonEscapedSeq ['\\u4e2d', '\\u56fd'] ++ ['\"'])\n"
            "      = ['\"', '\\u4e2d', '\\u56fd', '\"'] := by decide\n"
            "  have hliteral : ('\\u4e2d' :: ['\\u56fd']).flatMap jsonChar\n"
            "      = ['\\u4e2d', '\\u56fd'] := by decide\n"
            "  have hnotescaped : jsonEscapedSeq ['\\u4e2d']\n"
            "      ≠ ['\\\\', 'u', '4', 'e', '2', 'd'] := by decide\n"
            "  loom_solve\n"
            "  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]\n"
            "  simp_all\n"),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at an input of "
                     "the shape the failing tests exercise — a sequence of code "
                     "points at or above 128. Discharged by evaluation, at that "
                     "concrete input, before the frozen obligation is closed "
                     "verbatim: the post-image is a definite value (the two code "
                     "points framed by the delimiters), its body is the code points "
                     "THEMSELVES (literal pass-through, so not a constant/empty "
                     "collapse), and it is NOT the six-character escaped form (so the "
                     "admissible point is the discriminating one, not a point both "
                     "output modes agree on). If any of these failed, the single "
                     "clause would be unmeetable at exactly the input class at issue "
                     "=> PRECOND-TOO-STRONG, which on a total carrier is the "
                     "unsatisfiable-obligation direction. The nagini sibling's "
                     "admiss-selfcall establishes the SAME thing through its "
                     "permission precondition; this is its analogue on a carrier "
                     "whose pre-conditions region is empty. Verified to build; and "
                     "the claim is live — the escaped-form variant of `hsat` fails.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- PER-CODE-POINT BODY / non-ASCII pass-through arm (the behaviour at
    # ---- issue): a code point >= 128 is emitted as a short escape rather than
    # ---- passed through literally (the legacy all-ASCII output mode). ----
    {
        "id": "weak-nonascii-escaped",
        "kind": "uniqueness",
        "expect": "reject",
        # Body: pass ASCII through jsonChar, but emit a two-character escape for
        # any code point >= 128 instead of the literal pass-through.
        "module": _rival(
            "text.flatMap (fun c => if c.val < 128 then jsonChar c else ['\\\\', 'u'])"),
        "refinement": "escaping a code point at or above 128 instead of passing it "
                      "through literally is EXACTLY the legacy all-ASCII output "
                      "mode — the pre-narrowing behaviour. A faithful counterpart "
                      "keeping that mode renders a value carrying non-ASCII code "
                      "points as an escaped form instead of the literal characters, "
                      "which is the precise class the failing tests now require to "
                      "render literally, so it would NOT resolve.",
        "rationale": "REJECT from the single clause (non-ASCII pass-through arm of "
                     "`jsonChar`, `else [c]`): the frozen body keeps a code point "
                     ">= 128 LITERAL, so the rival's escaped body diverges. Refuted "
                     "at `['你']` (one code point >= 128): the rival emits an escape, "
                     "the spec body is the literal character. Varies `text` to a "
                     "single non-ASCII code point. If it verified => SPEC-TOO-WEAK "
                     "(the literal-pass-through discriminator hollow).",
        "witness": _witness("['你']"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- PER-CODE-POINT BODY / delimiter-escape arm: the delimiter code point
    # ---- (34) is emitted literally instead of in its two-character form. ----
    {
        "id": "weak-quote-not-escaped",
        "kind": "uniqueness",
        "expect": "reject",
        # Body: emit the delimiter code point (34) literally; everything else via
        # jsonChar.
        "module": _rival(
            "text.flatMap (fun c => if c.val = 34 then [c] else jsonChar c)"),
        "refinement": "emitting the delimiter code point literally (its correct "
                      "rendering is the two-character backslash form) produces "
                      "malformed output for any value containing that code point — "
                      "the delimiter would close the literal early. A faithful "
                      "counterpart shipping this diverges from the real string "
                      "renderer the A-reference pins and produces malformed text on "
                      "delimiter-bearing values, so it would NOT resolve.",
        "rationale": "REJECT from the single clause (delimiter-escape arm of "
                     "`jsonChar`, code point 34 -> two-char form): the rival's "
                     "literal-[34] body cannot match the frozen escaped body on a "
                     "delimiter code point. Refuted at `['\"']`: the rival emits the "
                     "bare delimiter, the spec body is its two-character form. Varies "
                     "`text` to a single delimiter code point. Correct on every "
                     "delimiter-free input. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("['\"']"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- PER-CODE-POINT BODY / escape-char arm: the escape code point (92) is
    # ---- emitted literally instead of doubled. ADDED — attacks the SECOND
    # ---- two-character arm the nagini sibling does not probe separately. ----
    {
        "id": "weak-backslash-not-escaped",
        "kind": "uniqueness",
        "expect": "reject",
        # Body: emit the escape code point (92) literally; everything else via
        # jsonChar.
        "module": _rival(
            "text.flatMap (fun c => if c.val = 92 then [c] else jsonChar c)"),
        "refinement": "emitting the escape code point literally (its correct "
                      "rendering is the doubled two-character form) produces "
                      "malformed output for any value containing it — a lone escape "
                      "would consume the following character. A faithful counterpart "
                      "shipping this diverges from the real string renderer the "
                      "A-reference pins and produces malformed text on "
                      "escape-bearing values, so it would NOT resolve.",
        "rationale": "REJECT from the single clause (escape-char arm of `jsonChar`, "
                     "code point 92 -> doubled form): the rival's literal-[92] body "
                     "cannot match the frozen escaped body on the escape code point. "
                     "Refuted at `['\\\\']` (one escape code point): the rival emits "
                     "a single character, the spec body is the doubled form. Varies "
                     "`text` to a single escape code point — a code point no other "
                     "rival probes. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("['\\\\']"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- OPEN + CLOSE FRAMING: the closing delimiter is dropped. ----
    {
        "id": "weak-no-closing-quote",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct (loop-free, closed-form) body, but the trailing delimiter is
        # dropped from the framing. Loop-free so the extracted program reduces
        # under the witness's `decide` (gold's loop stays stuck).
        "module": _swap(_BASE, _IMPL, "    return '\"' :: jsonEscapedSeq text\n"),
        "refinement": "dropping the closing delimiter renders every value missing "
                      "its trailing delimiter — malformed output for EVERY input, "
                      "not a partial-domain defect. A faithful counterpart doing "
                      "this fails on every value the failing tests assert, so it "
                      "would NOT resolve. (A cheap structural near-miss included "
                      "alongside the reasoned partial-domain arm attacks; probed at "
                      "the empty input, isolating the framing defect from any body "
                      "content and adding the only length-zero witness.)",
        "rationale": "REJECT from the single clause (CLOSE-FRAMING half): the "
                     "frozen clause is `out = '\"' :: (jsonEscapedSeq text ++ ['\"'])`, "
                     "so the result must end in the closing delimiter; the rival's "
                     "`'\"' :: jsonEscapedSeq text` omits it. Refuted at the empty "
                     "input `([] : List Char)` — the body is empty there, so ONLY "
                     "the missing trailing delimiter distinguishes the rival "
                     "(`['\"']`) from the spec (`['\"','\"']`). Varies `text` to "
                     "length zero, the one input the other three rivals never probe. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("([] : List Char)"),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives — a branch reorder and a split assembly — 1 admissibility, 1
# frame-mutation rival, 3 partial-domain rivals) plus a 1-case AXIOM lane. This
# bundle models the SAME purely-functional core — how a string value renders to
# its JSON text — over the SAME carrier shape (`List Char`, a backward
# per-code-point fold), so the split-assembly positive and the partial-domain
# rivals port near 1:1; the branch-reorder positive is NOT portable (its branch
# logic is frozen in the pure region here), the frame case is genuinely vacuous,
# the admissibility case IS PORTED (re-aimed at the unsatisfiable-obligation
# direction, which is what the lane detects on a total carrier), and one rival is
# ADDED to cover the escape-code-point arm the sibling folds together with the
# delimiter arm.
#
#   sibling case                  -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder (5a)      -> (none)                         NOT PORTABLE
#   pos-control-split-assembly(5b)-> pos-control-split-assembly     PORTED
#   (cheapest honest positive)    -> pos-control-direct             PORTED (idiom)
#   admiss-selfcall (6)           -> admiss-f2p-nonascii            PORTED (re-aimed)
#   frame-mutate-text (1)         -> (none)                         VACUOUS
#   weak-nonascii-escaped (3a)    -> weak-nonascii-escaped          PORTED
#   weak-quote-not-escaped (3b)   -> weak-quote-not-escaped         PORTED
#   weak-no-closing-quote (3c)    -> weak-no-closing-quote          PORTED
#   (no sibling)                  -> weak-backslash-not-escaped     ADDED
#   AXIOM_TESTS (1)               -> (none)                         DROPPED (G-AX)
#
# 5 ported, 1 added, 2 not-portable/vacuous, 1 dropped = 7 SPEC cases
# (2 soundness, 1 admissibility, 4 uniqueness).
#
# PORTED (positive control, split-assembly): the sibling builds the result in two
#   steps (`result = [34]+body`, then `result = result+[34]`); here the analogous
#   reshape prepends the opening delimiter (`opened := '"' :: result`) then
#   appends the closing one, cons/append-associativity equal, keeping the loop and
#   every invariant byte-identical so the frozen proof closes with no retune.
#   Verified to build.
# PORTED (positive control, direct): the sibling's "cheapest honest positive" is
#   `return oracle`-shaped where the oracle is grounded; here `return '"' ::
#   (jsonEscapedSeq text ++ ['"'])` is the grounded one-liner (jsonEscapedSeq is a
#   total fold over the input, not an ungrounded answer key). The loop is gone, so
#   its residual goal closes under `loom_solve` alone. Verified to build.
# NOT PORTABLE (pos-control-reorder): the sibling flips the `if c==34 / elif
#   c==92` branch ORDER inside its impl. On this carrier that branch logic lives
#   in the FROZEN `jsonChar` pure def (outside the impl region); the impl merely
#   calls `jsonChar c`, so there is no in-impl branch to reorder. The
#   split-assembly reshape is the structural-reshape positive control instead —
#   the reorder is not omitted for difficulty, it has no in-region counterpart.
# PORTED (3 partial-domain rivals): weak-nonascii-escaped, weak-quote-not-escaped,
#   and weak-no-closing-quote re-express DIRECTLY onto one behaviour the single
#   clause pins — the non-ASCII literal-pass-through arm of `jsonChar` (the
#   behaviour at issue), the delimiter-escape arm, and the close-framing half.
#   Each refinement argument carries over: a faithful counterpart with that defect
#   renders a value the narrowed behaviour now forbids (non-ASCII escaped,
#   delimiter un-escaped, closing delimiter missing), so it would NOT resolve the
#   failing tests.
# ADDED (1): weak-backslash-not-escaped attacks the escape-code-point arm of
#   `jsonChar` (code point 92 -> doubled form). The sibling attacks only the
#   delimiter arm (code point 34); the frozen `jsonChar` pins TWO independent
#   two-character arms, and a rival that mishandles only the escape code point
#   verifies against a spec that never probes it, so this is a real spec-strength
#   probe at a code point (92) no other rival exercises.
# PORTED, RE-AIMED (admiss-selfcall -> admiss-f2p-nonascii): the sibling self-calls
#   on an F2P-shaped input to prove its permission precondition `Acc(list_pred(text),
#   1/2)` admits it. This bundle's pre-conditions region IS empty — but that fact
#   alone does NOT make the lane vacuous, and an earlier revision of this manifest
#   dropped the case on exactly that reasoning. The lane detects
#   PRECOND-TOO-STRONG; its analogue on a TOTAL carrier is the obligation being
#   UNSATISFIABLE, or satisfiable only degenerately, at exactly an input of the
#   shape the failing tests exercise — and a spec no impl can meet there reads
#   exactly like a spec every impl meets. "The post-image is total, so it is
#   satisfiable everywhere by construction" is the right intuition but it is an
#   ARGUMENT, and nothing mechanically checks an argument. admiss-f2p-nonascii is
#   its machine-checked form: three `have`s discharge BY EVALUATION at a
#   two-code-point non-ASCII input (satisfiable; body is the literal code points,
#   so non-degenerate; body is NOT the escaped form, so the point discriminates)
#   before the frozen obligation closes verbatim. Verified to build, and the claim
#   is LIVE — substituting the escaped form for `hsat`'s right-hand side makes the
#   build fail with `decide` proved ... is false.
# VACUOUS (frame-mutate-text): the sibling carries this MANDATORY because `text`
#   is held at Acc(list_pred(text), 1/2) and a rival can illegally store into it.
#   This backend is referentially transparent and declares no `mut` binder over
#   any input — `text` is an immutable value with no heap footprint; the only
#   `mut` locals are the fresh accumulator and the loop counter — so there is no
#   read-only input to overwrite and no substitute probe. Not fabricated.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `jsonEscapedSeq` == the real compiled string renderer); this
#   bundle consumes no axiom `ensures`, and the gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `text : List Char`, and a single top-level clause with three independent
#   sub-obligations (open+close framing, delimiter/escape two-char arms, non-ASCII
#   literal pass-through). The four reject witnesses probe four DISTINCT input
#   points — `[]` (framing, length 0), `['你']` (non-ASCII arm, code point >=128),
#   `['"']` (delimiter arm, code point 34), `['\\']` (escape arm, code point 92) —
#   so `text` is genuinely varied in length (0, 1) and, at length 1, across four
#   DISTINCT code points hitting four distinct `jsonChar` arms plus the framing.
#   The two positive controls defend the whole obligation, and the admissibility
#   case adds a fifth, LENGTH-2 point (two code points at or above 128) — the only
#   multi-code-point input in the battery, which is also where the fold composes
#   more than one `jsonChar` application. No two rivals are refuted at the same
#   input. pts = 5 distinct input points (4 witnesses + 1 admissibility).
# WITNESS DISCRIMINATION (re-measured under audit with FOUR real builds per reject
#   case via scripts/lean_verify.sh — the two the gate runs plus the two-line
#   forgery experiment). Each witness ELABORATES against its loop-free rival
#   (exit 0 — the extracted program reduces to a literal that provably differs
#   from the spec body at the probed input). The second subject is the
#   `witness_reference`, NOT the frozen solution: see the module docstring for the
#   measurement that forced this — against gold, a witness and its exact negation
#   fail with the SAME `failed to synthesize Decidable` error, so gold's exit code
#   carries no information about the claim, whereas against the reference the exit
#   code FLIPS when the claim flips (witness -> 1, flipped claim -> 0). No witness
#   binds a hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness.
# SPEC STRENGTH, probed under audit beyond the shipped cases. Five ADDITIONAL wrong
#   impls were built against the frozen spec and ALL were rejected (no spec hole):
#   every code point below 32 rendered as the newline short form; the two
#   two-character arms SWAPPED with each other; no escaping at all (`return text`);
#   the control-escape hex nibbles in UPPERCASE; and the boundary code point 127
#   escaped. Two additional CORRECT reshapes were built and both VERIFY, so the
#   single clause is not over-fit to the frozen loop's shape: the `flatMap jsonChar`
#   closed form and the `foldr` closed form, each closed with an in-tactic
#   induction `have` (no new top-level declaration, so still in variant scope).
AXIOM_TESTS = []
