"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-11445 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct countLeadingMetadataLines`` obligation survives
with a byte-identical statement) and swaps in a candidate implementation; it is
judged by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates — the witness must elaborate against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a document modeled as a finite list
of source lines (each line a finite list of characters). The single obligation
is

    countLeadingMetadataLines (content : List (List Char)) return (pos : Nat)
        ensures pos = leadingMetadata content

where ``leadingMetadata`` is the length of the leading RUN of lines classified
as metadata lines — count from the front, stop at the first line that is not a
metadata line. ``isMetadataLine`` is the strict line classifier (with its
forward scan ``metaScan``): a line qualifies when it opens with a colon
immediately followed by a non-colon, non-space character, and the forward scan
reaches a TERMINATING colon — a colon that is last or followed by a space, whose
preceding character is not a space. A colon immediately followed by a backtick
does NOT terminate the marker, so an inline cross-reference role marker
(``:role:`` followed by a backtick) is REJECTED. That backtick rule is the
LOAD-BEARING discriminator of this instance: the strict classifier declines a
leading role-marker heading, so the counted leading run stops before it and the
heading survives; a looser recogniser that accepts any ``:name:``-prefixed line
regardless of what follows the closing colon over-counts and swallows the
heading (the behaviour the issue reports).

The sole input binder is ``content : List (List Char)``. The reject witnesses
below vary it along every axis the modeled behaviour depends on: the LENGTH of
the leading run (0, 1, ≥ 2), the SHAPE of the boundary line that stops the run
(a body line vs. a role-marker heading), and whether a following line exists at
all — so no rival is refuted at an input that leaves a binder-dimension untested.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``isMetadataLine`` / ``metaScan`` / ``leadingMetadata`` are concrete ``def``s in
the ``pure`` region (the ``axioms`` region declares NOTHING — the classifier is
modeled deeply, validated ``== FIELD_NAME_RE.match`` by axiom_check.py as an
A-reference, not consumed as an axiom). So each rival's violation reduces to a
decidable equality of concrete values and a literal-input witness discriminates
it, with one caveat below.

REDUCTION NOTE (specific to this carrier). The obligation's post-image
``leadingMetadata content`` computes at a concrete literal input under
``simp <;> decide``, so a rival stated as a LOOP-FREE closed form has an
extracted program that also reduces and a literal witness closes. The FROZEN
impl is an accumulating ``while`` loop, however, and the loop's extracted
program does NOT reduce under ``decide`` (the monadic ``NonDetT.run`` stays
stuck) — which is exactly why each witness FAILS on gold, satisfying the
discrimination half by construction. Every reject rival below is therefore a
loop-free closed form, and each witness closes with
``simp [<tester + pure defs>] <;> decide``.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl must still verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl. Two shapes: the loop collapsed to
    the closed form the post-image names directly (a maximally different,
    loop-free control flow), and a loop reshape that binds the per-step
    increment to a local (loop + invariants + proof unchanged).
  * ADMISSIBILITY — the method carries NO ``require`` clause, so the domain is
    total and the precondition cannot be too strong; the residual risk on this
    transparent carrier is that the post-image is DEGENERATE (constant), which
    reads like a spec every impl meets. ``admiss-grounded`` discharges an
    in-region assert pinning BOTH directions of the classifier at F2P-shaped
    lines — a ``:a:``-style line IS a metadata line, and the ``:role:``-then-
    backtick line is NOT — establishing the classifier is not constant. The
    surrounding loop + proof are kept verbatim so the method's own obligation
    still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling battery's mandatory
    frame-mutation rival relies on a read-only heap input carrying a fractional
    permission an impl overwrites. Lean and Velvet are referentially
    transparent: ``content`` is an immutable value (declared read-only, not
    ``mut``), there is no heap and no aliasing, so there is no read-only input to
    mutate and no permission system to trip. Not fabricated — reported as a
    vacuous omission in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``leadingMetadata content``, computed entirely from the
    method's own argument by concrete ``def``s (the ``axioms`` region is empty;
    no opaque answer key). The unique satisfier IS the grounded count; the
    honest positive control is the cheapest faithful impl that returns it.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired behaviour on some sub-domain and MUST be rejected:
    the loose pre-image recogniser (accepts the role-marker heading), an
    over-count past the boundary, a cap at one leading line, and a constant
    zero. Each is refuted at a concrete input by a machine-checked witness that
    FAILS on the frozen solution.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``countLeadingMetadataLinesTester content = false`` says the extracted program's
result violates the postcondition at that concrete input, checked in a file
whose ``prove_correct`` block has been stripped (no tactic script can mask the
verdict). Both halves were checked out of band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its rival and FAILS against the frozen solution.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the line
classifier is an A-reference validated by axiom_check.py (G-AX's job), not a
consumed contract. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-11445"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the accumulating while-loop that walks
# the leading run. Reject rivals and the oracle positive replace this with a
# loop-free closed form (so their extracted program reduces at a concrete input).
_IMPL = """    let mut i := 0
    while i < content.length ∧ isMetadataLine content[i]!
      invariant i ≤ content.length
      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
      decreasing content.length - i
    do
      i := i + 1
    return i"""
assert _BASE.count(_IMPL) == 1, "countLeadingMetadataLines impl region drifted from expected text"

# The single per-iteration increment; a positive control may reshape it while
# keeping the loop, guard, and invariants, so the frozen proof still closes.
_STEP = "      i := i + 1"
assert _BASE.count(_STEP) == 1, "loop increment drifted from expected text"

# The FULL frozen proof body (everything after `prove_correct ... by`). A
# positive control that collapses the loop to the closed form the post-image
# names retunes this to a bare `loom_solve`; the tactic body is elided from the
# spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct countLeadingMetadataLines by
  loom_solve
  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
      at invariant_2
    omega
  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
    omega"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the loop-bearing impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `countLeadingMetadataLinesTester content = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input.
_TESTER = (
    "extract_program_for countLeadingMetadataLines\n"
    "prove_precondition_decidable_for countLeadingMetadataLines\n"
    "prove_postcondition_decidable_for countLeadingMetadataLines\n"
    "derive_tester_for countLeadingMetadataLines\n\n"
)

# `simp` on the pure defs peels the tester guard and reduces the post-image
# `leadingMetadata`/`isMetadataLine`/`metaScan` on the loop-free extracted
# program; `decide` finishes the residual ground equality.
_WITNESS_TAC = (
    "  simp [countLeadingMetadataLinesTester, countLeadingMetadataLinesExec, "
    "leadingMetadata, isMetadataLine, metaScan] <;> decide"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n{_WITNESS_TAC}\n"


# A line literal from a Python str: each character becomes a Lean Char literal so
# the tester kernel-reduces (String.toList does not reduce under `decide`).
def _line(s):
    return "[" + ", ".join(f"'{c}'" for c in s) + "]"


def _doc(*lines):
    return "[" + ", ".join(_line(s) for s in lines) + "]"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps `ensures pos = leadingMetadata
    # content` and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-oracle-echo",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same count; the loop-specific proof is
        # retuned to a bare `loom_solve` since the impl now matches the
        # post-image syntactically. The count is grounded in the input by a
        # concrete `def`, NOT an opaque oracle, so echoing it IS the correct
        # answer — this is the honest cheapest faithful impl.
        "module": _impl_reproved(
            "    return (leadingMetadata content)",
            "prove_correct countLeadingMetadataLines by\n  loom_solve"),
        "rationale": "a loop-free impl returning the grounded leading count "
                     "directly must satisfy `pos = leadingMetadata content`; a "
                     "correct reshape of the modeled behaviour verifying is "
                     "exactly what SPEC-TOO-STRONG would deny. Exercises the "
                     "obligation from a maximally different (loop-free) "
                     "control-flow shape.",
    },
    {
        "id": "pos-loop-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-step increment to a local `step` before advancing
        # instead of writing `i := i + 1` directly. Same value flow; the loop,
        # guard, and front-recursive invariants are unchanged, so the frozen
        # proof closes untouched.
        "module": _swap(
            _BASE, _STEP,
            "      let step := 1\n      i := i + step"),
        "rationale": "binding the per-step increment to a local before advancing "
                     "walks the leading run identically, with the loop, guard, "
                     "and invariants unchanged, so the frozen proof closes and "
                     "`pos = leadingMetadata content` still holds; a correct "
                     "reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause (total domain), so
    # the precondition cannot be too strong; the residual risk is that the
    # post-image is DEGENERATE (constant). This case discharges an in-region
    # assert establishing that the classifier really does ACCEPT a `:a:`-style
    # metadata line and REJECT a `:role:`-then-backtick line — the two
    # directions of the per-line decision, at F2P-shaped inputs. The surrounding
    # loop + proof are kept verbatim so the method's own obligation still
    # discharges.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (isMetadataLine " + _line(":a:") + " = true ∧\n"
            "       isMetadataLine " + _line(":mod:`foo`") + " = false))\n"
            + _IMPL,
            "prove_correct countLeadingMetadataLines by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [leadingMetadata_step content i ‹i < content.length› "
            "‹isMetadataLine content[i]! = true›] at invariant_2; omega)\n"
            "    | (rw [leadingMetadata_stop content i invariant_1 done_1] "
            "at invariant_2; omega)"),
        "rationale":
            "the post-image is satisfiable AND non-degenerate: the classifier "
            "ACCEPTS a `:a:`-style metadata line and REJECTS a role marker "
            "followed by a backtick — the two directions of the per-line "
            "decision, at F2P-shaped inputs, so the leading count is not "
            "constant. The in-region assert must discharge (else the obligation "
            "is degenerate); the loop + proof are kept verbatim so "
            "`pos = leadingMetadata content` still verifies. The method has no "
            "`require` clause, so the domain is total — this defends against a "
            "DEGENERATE post-image, the residual admissibility risk on a "
            "referentially transparent carrier.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its extracted
    # program reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-loose-recogniser",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image bug: accept a line as a metadata line as long as it opens
        # with a colon, a non-colon non-space character, and contains ANY later
        # colon — regardless of what follows that closing colon. This accepts a
        # leading role marker (colon-name-colon-then-backtick), which the strict
        # classifier declines. Loop-free `takeWhile` so the extracted program
        # reduces.
        "module": _impl(
            "    return ((content.takeWhile (fun l =>\n"
            "      match l with\n"
            "      | a :: b :: rest => a = ':' && b ≠ ':' && b ≠ ' ' && rest.contains ':'\n"
            "      | _ => false)).length)"),
        "refinement": "this is the loose pre-image recogniser: it accepts a "
                      "leading cross-reference role marker (colon, name, closing "
                      "colon, then a backtick) as a countable leading line, "
                      "because it ignores what follows the closing colon. On a "
                      "document whose first heading is such a role marker it "
                      "over-counts the leading run and the prolog is inserted "
                      "AFTER the heading, swallowing it — precisely the reported "
                      "regression. A patch keeping the loose recogniser "
                      "reintroduces that failure, so it would NOT resolve "
                      "(test_prepend_prolog_with_roles_in_sections_with_newline / "
                      "…_without_newline stay red).",
        "rationale": "REJECT from `pos = leadingMetadata content`: on a "
                     "single-line document whose only line is a role marker "
                     "(colon, name, closing colon, backtick), the strict "
                     "classifier declines it so `leadingMetadata` is 0, while the "
                     "loose rival counts it as 1. Refuted on the backtick "
                     "sub-domain — the load-bearing discriminator of the whole "
                     "instance.",
        "witness": _witness(
            "countLeadingMetadataLinesTester "
            + _doc(":mod:`foo`")),
    },
    {
        "id": "weak-over-count",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-count by one whenever the run stops early (a following non-metadata
        # line exists): return the true count plus one. Loop-free closed form over
        # the grounded count. Correct only when the run reaches end-of-document.
        "module": _impl(
            "    let n := leadingMetadata content\n"
            "    return (if n < content.length then n + 1 else n)"),
        "refinement": "a counterpart that advanced one line past the true "
                      "boundary would insert the prolog one line too far — into "
                      "the body of the document rather than at the metadata "
                      "boundary — on any document with content after its leading "
                      "block, splitting the body. The failing tests pin the exact "
                      "insertion offset, so an off-by-one over-count leaves the "
                      "wrong layout and it would NOT resolve.",
        "rationale": "REJECT from `pos = leadingMetadata content`: on a two-line "
                     "document [metadata line, body line] the true leading count "
                     "is 1, but the rival returns 2 because a following "
                     "non-metadata line exists. Refuted at the run boundary — the "
                     "witness varies content.length beyond one and places a "
                     "non-metadata line after the run.",
        "witness": _witness(
            "countLeadingMetadataLinesTester "
            + _doc(":a:", "-")),
    },
    {
        "id": "weak-cap-at-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Cap the count at one leading metadata line: correct when the run has
        # length 0 or 1, wrong on any longer run. Loop-free closed form over the
        # grounded count.
        "module": _impl(
            "    let n := leadingMetadata content\n"
            "    return (if n ≥ 1 then 1 else 0)"),
        "refinement": "a counterpart that counted at most one leading metadata "
                      "line would insert the prolog between the first and second "
                      "lines of a multi-line leading block, splitting that block. "
                      "The failing tests' fixtures include documents whose "
                      "leading run is longer than one line; capping at one lands "
                      "the prolog inside the block, so it would NOT resolve.",
        "rationale": "REJECT from `pos = leadingMetadata content`: on a two-line "
                     "document of two metadata lines the true leading count is 2, "
                     "but the rival caps at 1. Refuted at a run of length ≥ 2 — "
                     "the witness varies the leading-run length past one, the "
                     "dimension the over-count and loose-recogniser witnesses do "
                     "not reach.",
        "witness": _witness(
            "countLeadingMetadataLinesTester "
            + _doc(":a:", ":b:")),
    },
    {
        "id": "weak-constant-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Never count any leading line: always return 0. Correct only when the
        # document opens with a non-metadata line; wrong on any document with a
        # leading metadata run.
        "module": _impl("    return 0"),
        "refinement": "always returning zero is what a patch that never counted "
                      "any leading line would do — the prolog is always inserted "
                      "at the very top, before any leading metadata block. On a "
                      "document that opens with a metadata line the prolog lands "
                      "before it rather than after the block, the wrong layout, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from `pos = leadingMetadata content`: on a "
                     "single-line document whose only line is a metadata line the "
                     "true count is 1, but the rival returns 0. Refuted whenever "
                     "the leading run is non-empty; the witness pins the "
                     "length-1 run, the minimal non-empty case.",
        "witness": _witness(
            "countLeadingMetadataLinesTester "
            + _doc(":a:")),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery (nagini) ships 7 SPEC cases (2 soundness positives, 1
# admissibility, 4 uniqueness) plus 1 AXIOM_TESTS entry. It contracts
# `count_leading_header_lines(content: PSeq[PSeq[int]]) -> int` with a rich
# postcondition of FOUR clauses over a pure mathematical sequence: (1)
# Result == leading_header_count(content); (2) 0 ≤ Result ≤ len; (3) the
# prefix-all-header clause Forall i<Result: is_header_line(content[i]); (4) the
# stop clause Result<len ⟹ ¬is_header_line(content[Result]).
#
# This velvet bundle contracts one method, `countLeadingMetadataLines`, over
# `List (List Char)` with a SINGLE ensures `pos = leadingMetadata content`.
# `leadingMetadata` is the grounded count computed by a concrete front-recursive
# `def`, so the sibling's clauses 1–4 are all IMPLIED by this one equation
# (clauses 2/3/4 are theorems about `leadingMetadata`, not independent
# obligations here) — the four-clause surface narrows to one clause, and the
# rivals that attacked clauses 2/3/4 individually collapse onto rivals against
# the single grounded equation. This is carrier narrowing, not weakening.
#
#   sibling case                  kind          -> here                    disposition
#   ------------------------------------------------------------------------------------
#   pos-oracle-echo               soundness     -> pos-oracle-echo          PORTED
#   pos-loop-reshape              soundness     -> pos-loop-reshape         PORTED (re-shaped)
#   admiss-f2p-shaped             admissibility -> admiss-grounded          RE-AIMED
#   reject-prepatch-predicate     uniqueness    -> weak-loose-recogniser    PORTED (headline)
#   reject-off-by-one-over        uniqueness    -> weak-over-count          PORTED
#   reject-cap-at-one             uniqueness    -> weak-cap-at-one          PORTED
#   reject-constant-zero          uniqueness    -> weak-constant-zero       PORTED
#   (frame-mutation)              —             -> (none)                   VACUOUS
#   ax-isheaderline-soundness     axiom         -> (none)                   G-AX
#
# 4 uniqueness ported, 2 soundness positives ported, 1 admissibility re-aimed;
# frame-mutation vacuous; axiom lane dropped. No nagini SPEC case was omitted for
# difficulty — all seven have counterparts.
#
# PORTED (reject-prepatch-predicate -> weak-loose-recogniser): the sibling
#   inlines the loose `:\w+:.*?` recogniser that accepts any colon-name-colon
#   prefix regardless of what follows the closing colon. Here the classifier is
#   modeled deeply, so the loose pre-image is expressed directly as a `takeWhile`
#   over a predicate that accepts a colon-name-colon-then-anything line; refuted
#   at the backtick discriminator (`:mod:`foo``), the load-bearing case of the
#   instance. The sibling's clause-1 + prefix-all-header attack both land on the
#   single grounded equation here.
# PORTED (reject-off-by-one-over -> weak-over-count): the sibling's rival returns
#   pos+1 when the run stops early (clauses 1 + the stop clause). Here the
#   stop clause is a theorem about `leadingMetadata`, so the rival is refuted on
#   the single equation at a [metadata, body] document — the only reject placing
#   a non-metadata line AFTER the run.
# PORTED (reject-cap-at-one -> weak-cap-at-one): direct port; refuted at a
#   two-metadata-line document (clause 1 when the true run length > 1). Sole
#   reject varying the leading-run length past one.
# PORTED (reject-constant-zero -> weak-constant-zero): direct port; refuted
#   whenever the leading run is non-empty (length-1 run).
# PORTED-SHAPE (pos-loop-reshape): the sibling reshapes the loop to a
#   while-True/explicit-break form. Velvet forbids early return inside a loop and
#   the frozen proof is tuned to the accumulating loop, so the reshape spirit is
#   carried by binding the per-step increment to a local (loop + guard +
#   invariants + proof unchanged) — a distinct executable surface that keeps the
#   obligation. The maximally-different loop-free shape is covered by
#   pos-oracle-echo.
# RE-AIMED (admiss-f2p-shaped): the sibling builds an F2P-shaped 2-line input and
#   self-calls to exercise the (vacuously-True) precondition. This method has no
#   `require` clause (total domain), so PRECOND-TOO-STRONG is unreachable; the
#   sharper residual risk — a DEGENERATE (constant) post-image — is attacked by
#   an in-region assert pinning BOTH directions of the classifier at F2P-shaped
#   lines, with the loop + proof kept verbatim.
# VACUOUS (frame-mutation): the sibling records the frame/permission class as N/A
#   because its `content` is a pure PSeq carrying no heap permission. This backend
#   is likewise referentially transparent: `content` is an immutable value, no
#   `mut` binder, no heap, no aliasing. Nothing to mutate, no permission to trip.
#   No substitute is fabricated.
# AXIOM_TESTS (1, ax-isheaderline-soundness): dropped. The axiom lane is G-AX's
#   job (axiom_check.py validates the deep classifier == the real docutils
#   `field_marker` recogniser); the classifier is modeled deeply here as an
#   A-reference with no consumed axiom, and this gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the one input binder
#   `content : List (List Char)` of the sole ensures (pts = 4 distinct input
#   points):
#     leading-run length     — 0 (loose-recogniser: the role marker yields a
#                              run of 0), 1 (constant-zero, over-count),
#                              ≥ 2 (cap-at-one): varied across all three, so a
#                              rival that mishandled only a particular run length
#                              is caught.
#     boundary line shape    — the run is stopped by a role-marker heading
#                              (loose-recogniser), a body line (over-count), and
#                              end-of-document (constant-zero at length 1): the
#                              stop condition is exercised on both a
#                              backtick-terminated role marker and an ordinary
#                              non-metadata line.
#     content.length         — 1 (loose-recogniser, constant-zero) AND 2
#                              (over-count, cap-at-one): varied, so the traversal
#                              past the first line is attacked.
#   The single top-level clause (the grounded equation `pos = leadingMetadata
#   content`) is attacked from every direction the sibling's four clauses
#   distinguished: the classifier's backtick rule (loose-recogniser), the stop
#   boundary (over-count), the run length (cap-at-one), and the empty-run base
#   case (constant-zero).
AXIOM_TESTS = []
