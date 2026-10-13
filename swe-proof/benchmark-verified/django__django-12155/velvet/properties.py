"""properties.py — G-PBT falsification battery for django__django-12155 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct normalizeIndentation`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it elaborates against the rival and FAILS against the
frozen solution).

DEFENDED SURFACE (one contracted method):

  normalizeIndentation (text : List Char) return (out : List Char)
    ensures out = cleanDocModel text

``cleanDocModel`` is a total, fully-unfolded pure function of the single input
``text``: split into lines, measure the common leading indentation shared by the
content lines AFTER the first, strip the first line's leading whitespace, remove
that common indentation from every subsequent line, then drop surrounding blank
lines and rejoin. There is no precondition and no free/ambient input — the whole
result is a function of ``text`` alone. The single load-bearing ``ensures``
clause pins the result to ``cleanDocModel text`` exactly.

The discriminating content the port must defend is the MARGIN-MEASUREMENT SCOPE:
the common indentation is taken over the lines AFTER the first, so a block whose
text begins on the very first line (at column zero) is dedented correctly rather
than being forced to a zero margin and left indented. The pre-patch behaviour
measured the common indentation over ALL lines including the first, so a
first-line-at-column-0 block kept its body indented — the failure the issue and
the FAIL_TO_PASS test pin.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer.)
  * PARTIAL-DOMAIN / MARGIN-SCOPE — APPLIES, and is the headline SPEC-TOO-WEAK
    probe: measuring the common indentation over ALL lines instead of the lines
    after the first. It agrees with the post-image only where the first line is
    already the least-indented content line; it diverges exactly on the shape the
    failing test constructs.
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the text domain but
    diverging on a sub-domain (body indentation never removed; first line's
    indentation never stripped; surrounding blank lines never dropped).
  * UNGROUNDED-ORACLE ECHO — N/A. ``cleanDocModel`` is a concrete ``def`` in the
    ``pure`` region (the ``axioms`` region is empty — no opaque answer key to
    echo); the cheapest correct impl simply evaluates it, which the positive
    controls cover honestly. The carrier is fully TRANSPARENT (``List Char`` over
    computable ``def``s), so every rival's violation is ``decide``-able and the
    reject lane is fully expressible — no NO-REJECT-LANE risk here.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. All
six witnesses were built against both the rival (must elaborate) and the frozen
solution (must fail); they sit at SIX DISTINCT inputs that vary
the single binder ``text`` — an ordinary two-line block, a block whose body is
indented more than one, a block whose FIRST line is itself indented, a block
with a leading blank line, a block ending in a line break, and a flush-first-line
block with a blank line before an indented body — so the manifest demonstrates
the post-image's dependence on the full shape of ``text`` (margin scope, the
content-line filter inside the measurement, body removal, first-line strip, and
BOTH halves of the surrounding-blank drop), not merely its value at a single
pinned point.

AUDIT NOTE (independent re-derivation). Every reject case's witness was rebuilt
against the rival and against the frozen solution, and each was additionally
subjected to a FORGERY probe: the same witness with its claim flipped
(``= false`` -> ``= true``) built against both sides. In every case the flipped
claim inverted both exit codes (gold 0, rival 1) where the true claim had them
the other way (gold 1, rival 0), so the gold-side exit code demonstrably tracks
the CLAIM and not the file — the rejections are semantic refutations by kernel
evaluation, not tactic-shape mismatches. The audit added
``weak-trailing-blank-kept``: the original four witness points all sat where the
trailing-blank drop is a no-op, so half of the surrounding-blank clause was
attested by nothing.
"""
from pathlib import Path

INSTANCE = "django__django-12155"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_IMPL = (
    "    let lines := splitLines text\n"
    "    let margin := commonIndent (lines.drop 1)\n"
    "    let dedented := dedentLines margin lines\n"
    "    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)\n"
    "    return joinNL trimmed"
)

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. Unique in the file.
_PROOF = (
    "prove_correct normalizeIndentation by\n"
    "  loom_solve\n"
    "  unfold cleanDocModel\n"
    "  rfl"
)


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `normalizeIndentationTester text = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for normalizeIndentation\n"
            "prove_precondition_decidable_for normalizeIndentation\n"
            "prove_postcondition_decidable_for normalizeIndentation\n"
            "derive_tester_for normalizeIndentation\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the contract is point-wise (`out = cleanDocModel
    # text`), so the reproof stays close to the frozen script.
    # =====================================================================
    {
        "id": "pos-control-inline-composition",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the intermediate `margin`/`dedented`/`trimmed`
        # bindings into a single nested composition. Observationally
        # `cleanDocModel text` for every input.
        "module": _swap(
            _BASE, _IMPL,
            "    let lines := splitLines text\n"
            "    let dedented := dedentLines (commonIndent (lines.drop 1)) lines\n"
            "    return joinNL (dropLeadingBlank (dropTrailingBlank dedented))"),
        "rationale": "an inlined but definitionally identical composition must "
                     "satisfy `out = cleanDocModel text` on the whole domain; if "
                     "it failed to verify the post-image would be SPEC-TOO-STRONG "
                     "on the composition's shape. Verifies with the frozen proof.",
    },
    {
        "id": "pos-control-split-blank-trim",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: split the fused surrounding-blank trim into two named steps
        # (drop trailing, then drop leading). Same value, different surface.
        "module": _swap(
            _BASE, _IMPL,
            "    let lines := splitLines text\n"
            "    let margin := commonIndent (lines.drop 1)\n"
            "    let dedented := dedentLines margin lines\n"
            "    let noTrail := dropTrailingBlank dedented\n"
            "    let trimmed := dropLeadingBlank noTrail\n"
            "    return joinNL trimmed"),
        "rationale": "naming the trailing-blank drop as its own step before the "
                     "leading-blank drop computes the same result, so "
                     "`out = cleanDocModel text` still holds; a correct reshape "
                     "must verify (else SPEC-TOO-STRONG on binding structure).",
    },

    # =====================================================================
    # ADMISSIBILITY — there is NO precondition on this method (`text` is any
    # `List Char`), so the sibling's "a normal input satisfies the
    # precondition" probe is trivially discharged and not where the risk sits.
    # The residual admissibility risk on this surface is that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like one every impl meets. This case discharges an
    # in-region `assert` pinning the post-image's value at the FAIL_TO_PASS
    # shape: a block whose first line begins at column zero and whose body is
    # indented is normalized to a flushed body (the very behaviour the issue
    # demands), NOT left indented. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live (a false
    # claim about the same point leaves an unsolved goal — checked during
    # authoring).
    # =====================================================================
    {
        "id": "admiss-flush-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL,
            "    assert (with_name_prefix `assert\n"
            "      (cleanDocModel \"firstline\\n\\n    second line\".toList\n"
            "        = \"firstline\\n\\nsecond line\".toList))\n" + _IMPL,
            _PROOF,
            "prove_correct normalizeIndentation by\n"
            "  loom_solve <;> (try decide) <;> (unfold cleanDocModel; rfl)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "FAIL_TO_PASS shape: a first-line-at-column-zero block with "
                     "an indented body normalizes to a FLUSHED body, not one left "
                     "indented. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable / degenerate at the interesting "
                     "point); the impl is kept verbatim so the method's own "
                     "`ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-margin-all-lines",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-patch behaviour: measure the common indentation over
        # ALL lines (commonIndent lines) instead of the lines AFTER the first
        # (commonIndent (lines.drop 1)). On a block whose first line is at the
        # least indentation, the all-lines minimum pins the margin low and the
        # body is never fully dedented.
        "module": _swap(
            _BASE, _IMPL,
            _IMPL.replace("commonIndent (lines.drop 1)", "commonIndent lines")),
        "refinement": "a counterpart that measures the common indentation over "
                      "ALL lines (the pre-patch behaviour) forces the margin to "
                      "the first line's indentation whenever the first line is the "
                      "least-indented content line — the F2P shape, whose first "
                      "line sits at column zero. The body then stays indented, so "
                      "the downstream renderer emits the 'no content permitted' "
                      "error the failing test asserts is absent. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = cleanDocModel text`: cleanDocModel "
                     "measures the margin over the lines AFTER the first, so a "
                     "body de-indented by the all-lines margin (which is pinned "
                     "low by a flush first line) cannot equal it. Verifying would "
                     "be SPEC-TOO-WEAK — it would admit the exact pre-patch bug. "
                     "Refuted at a two-line block whose body is indented more than "
                     "the flush first line.",
        "witness": _tester(
            'example : normalizeIndentationTester ("x\\n    y".toList) = false '
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-body-not-dedented",
        "kind": "uniqueness",
        "expect": "reject",
        # Compute nothing: pin the margin to `none`, so the subsequent lines
        # keep their original indentation (the first line is still stripped).
        # The behaviour of an impl that measured but never applied the margin.
        "module": _swap(
            _BASE, _IMPL,
            _IMPL.replace("let margin := commonIndent (lines.drop 1)",
                          "let margin : Option Nat := none")),
        "refinement": "a counterpart that never removes the common indentation "
                      "from the subsequent lines leaves the whole body indented; "
                      "on the F2P shape the body stays at its original column, so "
                      "the renderer again emits the error the failing test "
                      "forbids. Distinct from the all-lines-margin rival (which "
                      "mis-SCOPES the measurement); this one drops the removal "
                      "entirely. It would NOT resolve.",
        "rationale": "REJECT from `out = cleanDocModel text`: cleanDocModel "
                     "removes the measured common indentation from every "
                     "subsequent line; a body left at its original indentation "
                     "cannot equal it whenever that common indentation is "
                     "positive. Refuted at a two-line block with an indented "
                     "body, a distinct input from the other rivals.",
        "witness": _tester(
            'example : normalizeIndentationTester ("a\\n  b".toList) = false '
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-first-line-not-flushed",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct margin scope and body removal, but the first line keeps its
        # original leading whitespace (emit `lines.headD []` instead of
        # stripping it). Diverges on any block whose first line is indented.
        "module": _swap(
            _BASE, _IMPL,
            "    let lines := splitLines text\n"
            "    let margin := commonIndent (lines.drop 1)\n"
            "    let tail := match margin with\n"
            "      | none   => lines.drop 1\n"
            "      | some m => (lines.drop 1).map (fun l => l.drop m)\n"
            "    let dedented := (lines.headD []) :: tail\n"
            "    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)\n"
            "    return joinNL trimmed"),
        "refinement": "a counterpart that keeps the first line's leading "
                      "whitespace instead of stripping it leaves leading "
                      "whitespace on the title of any block whose first line is "
                      "indented, so the parsed title diverges and the rendered "
                      "output differs from the gold output on that sub-domain. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = cleanDocModel text`: cleanDocModel always "
                     "strips the first line's leading spaces; an impl that emits "
                     "the raw first line yields a leading-whitespace prefix where "
                     "the post-image demands none. Refuted at a block whose FIRST "
                     "line is itself indented — the sub-domain no other rival "
                     "probes.",
        "witness": _tester(
            'example : normalizeIndentationTester ("  a\\n    b".toList) = false '
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-margin-counts-blank-lines",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct margin SCOPE (the lines after the first) but the minimum is
        # taken over ALL of those lines rather than only the lines that have
        # content: a blank line, whose leading-space count is zero, pins the
        # margin to zero and the body is never dedented. Attacks the
        # content-line filter inside the margin measurement — the clause the
        # other four rivals leave untouched (they vary the scope, the removal,
        # the first-line strip and the surrounding drop, all with the filter
        # intact). Diverges on any block with a blank line among the lines
        # after the first — including the shape the failing test constructs.
        "module": _swap(
            _BASE, _IMPL,
            "    let lines := splitLines text\n"
            "    let margin : Option Nat := match lines.drop 1 with\n"
            "      | []      => none\n"
            "      | l :: ls => some (ls.foldl (fun a x => Nat.min a (leadingSpaces x))\n"
            "                                  (leadingSpaces l))\n"
            "    let dedented := dedentLines margin lines\n"
            "    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)\n"
            "    return joinNL trimmed"),
        "refinement": "a counterpart that measures the common indentation over "
                      "every line after the first, instead of only the lines that "
                      "carry content, lets a blank line force the measured amount "
                      "to zero — and a blank second line is the ordinary shape for "
                      "the blocks this surface normalizes. The body is then left at "
                      "its original column exactly as in the unfixed behaviour, so "
                      "the downstream renderer emits the error the failing test "
                      "asserts is absent. It would NOT resolve.",
        "rationale": "REJECT from `out = cleanDocModel text`: cleanDocModel's "
                     "margin is the minimum over the CONTENT lines after the first "
                     "(`hasContent` filters the blank ones out), so an impl whose "
                     "minimum also ranges over blank lines measures zero wherever a "
                     "blank line follows the first and cannot equal the post-image "
                     "there. Verifying would be SPEC-TOO-WEAK on the content-line "
                     "filter. Refuted at a first-line-flush block with a blank line "
                     "and an indented body — a fifth distinct input, and the one "
                     "sub-domain the other rivals do not reach.",
        "witness": _tester(
            'example : normalizeIndentationTester ("x\\n\\n    y".toList) = false '
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-no-surrounding-blank-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct margin, body removal and first-line strip, but the surrounding
        # blank-line drop is omitted (emit `dedented` directly). A leading blank
        # line survives into the output. This is the carrier's counterpart of the
        # sibling's blank-handling rival: here a "blank line" is an empty
        # `List Char`, and the modeled blank handling is the surrounding drop.
        "module": _swap(
            _BASE, _IMPL,
            _IMPL.replace(
                "    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)\n",
                "    let trimmed := dedented\n")),
        "refinement": "a counterpart that omits the surrounding blank-line drop "
                      "leaves a leading (or trailing) blank line in the "
                      "normalized text; downstream the paragraph split on blank "
                      "lines then yields a different (title, body) partition, so "
                      "the parsed parts diverge from the gold output. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = cleanDocModel text`: cleanDocModel drops "
                     "surrounding blank lines; an impl that keeps them carries a "
                     "leading empty segment where the post-image has none. Refuted "
                     "at a block that begins with a blank line — a distinct input "
                     "exercising the surrounding-blank-drop clause.",
        "witness": _tester(
            'example : normalizeIndentationTester ("\\na".toList) = false '
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-trailing-blank-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct margin, body removal, first-line strip AND the LEADING blank
        # drop — but the TRAILING blank drop is omitted. Added by audit: the
        # `weak-no-surrounding-blank-drop` rival above drops BOTH ends at once,
        # and all four original witness points sit at inputs where the trailing
        # drop is a no-op (measured: it fires at none of them), so the trailing
        # half of the surrounding-blank clause was pinned by no case. This rival
        # isolates it — it agrees with the post-image everywhere the text does
        # not end in a blank line, and diverges exactly when it does.
        "module": _swap(
            _BASE, _IMPL,
            _IMPL.replace(
                "    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)\n",
                "    let trimmed := dropLeadingBlank dedented\n")),
        "refinement": "a counterpart that trims only the leading blank lines "
                      "leaves a trailing empty segment on any block whose text "
                      "ends with a line break — the ordinary shape of a block "
                      "written across several lines. The normalized text then "
                      "carries a trailing blank the post-image does not, so the "
                      "downstream paragraph split yields a different final "
                      "segment and the rendered output diverges from the gold "
                      "output on that sub-domain. It would NOT resolve.",
        "rationale": "REJECT from `out = cleanDocModel text`: cleanDocModel drops "
                     "the trailing blank lines as well as the leading ones "
                     "(`dropTrailingBlank` then `dropLeadingBlank`); an impl that "
                     "keeps them carries a trailing empty segment where the "
                     "post-image has none. Distinct from "
                     "`weak-no-surrounding-blank-drop`, which omits BOTH drops and "
                     "is refuted at a LEADING blank: this one keeps the leading "
                     "drop and is refuted at a block ending in a line break, the "
                     "sub-domain no other rival reaches.",
        "witness": _tester(
            'example : normalizeIndentationTester ("a\\n".toList) = false '
            ":= by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals; AXIOM_TESTS dropped). This
# bundle models the purely-functional core — a single method `normalizeIndentation`
# whose contract is `out = cleanDocModel text` — where the sibling contracts one
# function `dedent_block(eff)` over a permission-bearing List[int] carrier. The
# value surface carries across intact; the permission surface does not exist here.
# Every sibling case is accounted for below.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-control-inline-composition  RE-AIMED
#                                            (+ pos-control-split-blank-trim  ADDED)
#   admissibility                         -> admiss-flush-nondegenerate      RE-AIMED
#   frame-mutation                        -> (none)                          VACUOUS
#   prepatch-all-lines-margin             -> weak-margin-all-lines           PORTED
#   body-not-dedented                     -> weak-body-not-dedented          PORTED
#   first-line-not-flushed                -> weak-first-line-not-flushed     PORTED
#   blank-body-line-emitted-nonblank      -> weak-no-surrounding-blank-drop  RE-AIMED
#                                            (+ weak-trailing-blank-kept   ADDED/audit)
#
# 3 ported, 3 re-aimed, 1 vacuous; 1 positive control added; 1 rival added by audit.
#
# VACUOUS (frame-mutation): the sibling's mandatory frame-mutation rival writes
#   to a read-only input carrying a fractional heap permission and is rejected
#   for INSUFFICIENT PERMISSION. This backend is referentially transparent: every
#   parameter is an immutable value, this bundle declares no `mut` binder, there
#   is no heap and no aliasing. There is no read-only input to overwrite and no
#   permission system to trip, so the class is vacuous. No substitute is
#   fabricated (per the porting map, this class is legitimately dropped here).
# RE-AIMED (pos-control): the sibling reorders the two value-producing branches;
#   this carrier has no per-line blank/non-blank branch to reorder (blank lines
#   are structural empty segments, and the first-line/body split is expressed by
#   `dedentLines` position, not a value branch). The soundness surface is instead
#   defended by two distinct value-preserving reshapes of the composition.
# RE-AIMED (admissibility): the sibling recurses on a concrete in-domain summary
#   to show the precondition admits a normal input. There is NO precondition
#   here, so that probe is trivial. It is re-aimed at the residual admissibility
#   risk — that the post-image is unsatisfiable/degenerate at the interesting
#   point — via an in-region assert pinning the FAIL_TO_PASS value.
# RE-AIMED (blank-body): the sibling turns a blank body line into a non-blank
#   zero-indent line, attacking a per-line blank MARKER (-1) in its List[int]
#   carrier. This carrier has no such marker — a blank line is an empty
#   `List Char` — so the modeled blank behaviour is the SURROUNDING blank-line
#   drop (`dropLeadingBlank`/`dropTrailingBlank`), which the re-aimed rival
#   omits. Same intent (mishandle blank lines), expressed on this carrier.
# ADDED (1): pos-control-split-blank-trim — a second, structurally-different
#   correct impl (the fused surrounding-blank trim split into two named steps),
#   so the soundness surface is defended by two distinct reshapes rather than one.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = cleanDocModel
#   text` is attacked by all six rivals across six distinct sub-domains — the
#   margin-measurement SCOPE (the load-bearing behavior), the CONTENT-LINE FILTER
#   inside that measurement, the body-removal step, the first-line strip, the
#   LEADING blank drop and the TRAILING blank drop — refuted at SIX DISTINCT input
#   points (pts=6). The single binder `text` is varied across the six witnesses
#   (an ordinary indented body; a body indented more than one; a block whose FIRST
#   line is indented; a block with a leading blank line; a block ending in a line
#   break; a flush-first-line block with a blank line before an indented body), so
#   the manifest demonstrates the post-image's dependence on every modeled facet
#   of `text`. There is no free/ambient input to hold fixed. The rivals are
#   pairwise EXTENSIONALLY DISTINCT functions (verified by brute force over all
#   1093 strings of length <= 6 in {' ', 'a', '\n'}), so no case duplicates
#   another.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the deep model
#   (`cleanDocModel` and its constituents) is an A-reference validated there, and
#   this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
