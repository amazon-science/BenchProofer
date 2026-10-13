"""properties.py — G-PBT falsification battery for django__django-12155 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_normalizeIndent``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect="reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single input binder ``lines``). The
routine normalizes the indentation of a block of text already split into lines:

  normalizeIndent (lines : List (List Char)) : List (List Char)

The result is pinned by the postcondition ``result = normalizeIndentSpec lines``,
whose reference unfolds into FIVE independent structural stages, each attacked by
some rival:

  (C1) the common indentation amount is the least leading-whitespace count taken
       over the non-blank lines AFTER THE FIRST — not over every line;
  (C2) a *blank* line (all-whitespace) does NOT contribute to that amount;
  (C3) the first line is stripped of all its leading whitespace (flushed left);
  (C4) every line after the first has exactly the common amount removed;
  (C5) completely empty lines are removed from the end, then from the beginning
       of the block.

The single binder ``lines`` is varied along the axes each stage reads: whether
the FIRST line is indented or flush, whether later lines are indented, whether a
blank (whitespace-only) line sits among them, and whether a completely-empty line
sits at an end. The six reject witnesses probe six distinct input points so that
no clause is defended only at a point every rival shares.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the input at
    a half-permission (read-only) and makes its MANDATORY frame-mutation rival
    WRITE to it, expecting rejection for insufficient permission. Lean is
    referentially transparent: ``lines`` carries no heap permission, there is no
    read-only fraction to overwrite and no aliasing to exploit. That class has no
    expressible instance here and NO substitute is fabricated for it (see
    ``assessment``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the input
    (``normalizeIndentSpec`` is a total pure function of ``lines`` alone, fully
    unfolded from the whitespace table and the fold helpers); the bundle declares
    no ``opaque``/``axiom``, so there is no answer key to echo. In its place the
    battery carries honest POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN — APPLIES. The nagini partial-domain rivals (the literal
    pre-patch all-lines margin, the un-flushed first line, the un-dedented body,
    the mishandled blank line) map directly onto stages C1/C3/C4/C2 here. Two
    further rivals (C5) attack the end-trimming stages, which the Lean carrier
    models but the nagini carrier did not, so they are new coverage of a clause
    the nagini battery never reached.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen fold-congruence proof is tuned to the
frozen ``for``/``mut`` shape — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet proving the
rival CONTRADICTS the spec at one concrete, all-literal input. Each was checked
(two real builds) to ELABORATE against its rival and to FAIL against the frozen
solution, so it is a genuine discriminator, not a tautology. The imperative
``Id.run do`` impl reduces fully under ``decide`` at a ground ``List (List Char)``
input, so each witness ``unfold``s the spec predicate and closes the negated
equality by ``decide``.

AXIOM lane: EMPTY. meta.json axioms == [] and the normalization is modeled deeply
(deep_model_references validated == real inspect.cleandoc by G-CONF, not by an
axiom the proof consumes). The axiom-soundness/containment obligations are G-AX's
job, not this gate's; AXIOM_TESTS is therefore omitted.
"""
from pathlib import Path

INSTANCE = "django__django-12155"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The margin-measurement loop, restricted to the lines after the first and
# skipping blank lines. C1 (scope) and C2 (blank-skip) both live here.
_MARGIN_LOOP = (
    "  for line in lines.drop 1 do\n"
    "    if !isBlank line then\n"
    "      let ind := leadingWs line\n"
    "      margin := some (match margin with\n"
    "                      | none   => ind\n"
    "                      | some m => Nat.min m ind)\n"
)

# The first-line seed of the output accumulator: strip its leading whitespace.
_FLUSH = (
    "    | first :: _  => [lstripWs first]\n"
    "  for line in lines.drop 1 do\n"
    "    match margin with"
)

# The per-following-line dedent step.
_DEDENT = "    | some m => out := out ++ [line.drop m]\n"

# The end-trimming stage: drop empty lines from the tail, then the head.
_TRIM = (
    "  out := dropTrailingEmpty out\n"
    "  out := dropLeadingEmpty out\n"
)

# Frozen proof entry (unique); the admissibility case prepends a ground `have`.
_PROOF_INTRO = "  intro lines\n  unfold problem_spec_normalizeIndent\n"

# Whole impl def block — anchor for the functional-reshape positive.
_FULL_IMPL = _BASE[
    _BASE.index("def implementation_normalizeIndent"):
    _BASE.index("  return out\n") + len("  return out\n")
]
assert _BASE.count(_FULL_IMPL) == 1, "IMPL anchor drift"


SPEC_TESTS = [
    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # The six witnesses spread the single `lines` binder across the input
    # settings each postcondition stage reads.
    # =====================================================================
    {
        "id": "margin-over-all-lines",
        "kind": "uniqueness",
        "expect": "reject",
        # C1: measure the common amount over EVERY line (drop `.drop 1`),
        # including the first — the literal pre-patch behavior.
        "module": _swap(
            _BASE, _MARGIN_LOOP,
            "  for line in lines do\n"
            "    if !isBlank line then\n"
            "      let ind := leadingWs line\n"
            "      margin := some (match margin with\n"
            "                      | none   => ind\n"
            "                      | some m => Nat.min m ind)\n",
        ),
        "refinement": "measuring the common amount over ALL lines instead of the "
                      "lines after the first is exactly the code the gold change "
                      "deletes. On a block whose first line is flush-left (leading "
                      "amount 0) the all-lines minimum collapses to 0, so the body "
                      "is left indented; the F2P input is precisely such a block, "
                      "and its indented body makes the downstream renderer emit an "
                      "error to stderr, so the F2P assertion on empty stderr fails. "
                      "A patch that keeps the all-lines scope would NOT resolve.",
        "rationale": "REJECT from C1 (result = normalizeIndentSpec lines, whose "
                     "margin is taken over lines.drop 1): at a flush-first block "
                     "with an indented body the rival dedents by 0 and keeps the "
                     "body indented, but the spec dedents by the body's own amount. "
                     "Refuted at [['a'], [' ','b']] — flush first line, one-space "
                     "body.",
        "witness": (
            "example : ¬ problem_spec_normalizeIndent [['a'], [' ', 'b']]\n"
            "    (implementation_normalizeIndent [['a'], [' ', 'b']]) := by\n"
            "  unfold problem_spec_normalizeIndent\n"
            "  decide\n"
        ),
    },
    {
        "id": "blank-line-contributes-margin",
        "kind": "uniqueness",
        "expect": "reject",
        # C2: drop the `!isBlank` guard so a whitespace-only line's leading
        # count is folded into the common amount.
        "module": _swap(
            _BASE, _MARGIN_LOOP,
            "  for line in lines.drop 1 do\n"
            "    let ind := leadingWs line\n"
            "    margin := some (match margin with\n"
            "                    | none   => ind\n"
            "                    | some m => Nat.min m ind)\n",
        ),
        "refinement": "letting a blank (whitespace-only) line contribute its "
                      "leading count to the common amount makes a shallowly-"
                      "indented blank line drag the common amount below the real "
                      "body indentation, so the body is under-dedented. A faithful "
                      "patch that dropped the 'blank lines do not count' rule would "
                      "leave residual indentation on the body of any block with a "
                      "short blank line, diverging from the standard algorithm the "
                      "fix adopts → would NOT resolve on such a block.",
        "rationale": "REJECT from C2: at [['a'], [' '], [' ',' ',' ',' ','b']] the "
                     "spec ignores the one-space blank line and dedents the body by "
                     "4 (→ empty tail-content that end-trimming removes), while the "
                     "rival takes the minimum with the blank's count 1 and dedents "
                     "by 1, leaving the body at indent 3. Refuted at an input with "
                     "a blank line strictly shallower than the body.",
        "witness": (
            "example : ¬ problem_spec_normalizeIndent [['a'], [' '], [' ', ' ', ' ', ' ', 'b']]\n"
            "    (implementation_normalizeIndent [['a'], [' '], [' ', ' ', ' ', ' ', 'b']]) := by\n"
            "  unfold problem_spec_normalizeIndent\n"
            "  decide\n"
        ),
    },
    {
        "id": "first-line-not-flushed",
        "kind": "uniqueness",
        "expect": "reject",
        # C3: seed the accumulator with the first line UNCHANGED instead of
        # stripped of its leading whitespace.
        "module": _swap(
            _BASE, _FLUSH,
            "    | first :: _  => [first]\n"
            "  for line in lines.drop 1 do\n"
            "    match margin with",
        ),
        "refinement": "keeping the first line's original indentation instead of "
                      "flushing it left leaves leading whitespace on the block's "
                      "title. A faithful patch that skipped the first-line strip "
                      "would render a differently-indented title on any block whose "
                      "first line is indented, diverging from the standard "
                      "algorithm's output → would NOT resolve on an indented-first "
                      "block.",
        "rationale": "REJECT from C3 (dedentSpec strips the first line via "
                     "lstripWs): at [[' ',' ','a'], [' ','b']] the spec flushes the "
                     "first line to ['a'] while the rival keeps [' ',' ','a']. "
                     "Refuted at an input whose first line is indented — the only "
                     "setting C3 constrains.",
        "witness": (
            "example : ¬ problem_spec_normalizeIndent [[' ', ' ', 'a'], [' ', 'b']]\n"
            "    (implementation_normalizeIndent [[' ', ' ', 'a'], [' ', 'b']]) := by\n"
            "  unfold problem_spec_normalizeIndent\n"
            "  decide\n"
        ),
    },
    {
        "id": "body-not-dedented",
        "kind": "uniqueness",
        "expect": "reject",
        # C4: measure the common amount but never subtract it (keep each
        # following line unchanged).
        "module": _swap(
            _BASE, _DEDENT,
            "    | some _ => out := out ++ [line]\n",
        ),
        "refinement": "measuring the common amount but never removing it from the "
                      "following lines leaves the body at its original indentation. "
                      "A faithful patch that computed the amount and forgot to apply "
                      "it produces the same over-indented body as the pre-patch bug "
                      "on the F2P input, so the downstream renderer again errors to "
                      "stderr → would NOT resolve.",
        "rationale": "REJECT from C4 (dedentSpec maps `·.drop m` over the following "
                     "lines): at [['a'], [' ',' ','b']] the spec removes the common "
                     "amount 2 to yield ['b'] while the rival keeps [' ',' ','b']. "
                     "Refuted at a flush-first block with an indented body; distinct "
                     "from margin-over-all-lines, which mis-SCOPES rather than "
                     "drops the removal.",
        "witness": (
            "example : ¬ problem_spec_normalizeIndent [['a'], [' ', ' ', 'b']]\n"
            "    (implementation_normalizeIndent [['a'], [' ', ' ', 'b']]) := by\n"
            "  unfold problem_spec_normalizeIndent\n"
            "  decide\n"
        ),
    },
    {
        "id": "no-trailing-empty-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # C5a: skip the tail empty-line removal.
        "module": _swap(
            _BASE, _TRIM,
            "  out := dropLeadingEmpty out\n",
        ),
        "refinement": "omitting the removal of completely-empty lines from the end "
                      "of the block leaves trailing empty lines in the normalized "
                      "output. A faithful patch that dropped the tail-trim step "
                      "would leave a trailing blank paragraph that the downstream "
                      "paragraph split reads as extra content, diverging from the "
                      "standard algorithm's trimmed output → would NOT resolve on a "
                      "block ending in an empty line.",
        "rationale": "REJECT from C5 (dropTrailingEmpty): at [['a'], []] the spec "
                     "trims the trailing empty line to [['a']] while the rival "
                     "returns [['a'], []]. Refuted at a block ending in a "
                     "completely-empty line — a clause the nagini carrier never "
                     "modeled.",
        "witness": (
            "example : ¬ problem_spec_normalizeIndent [['a'], []]\n"
            "    (implementation_normalizeIndent [['a'], []]) := by\n"
            "  unfold problem_spec_normalizeIndent\n"
            "  decide\n"
        ),
    },
    {
        "id": "no-leading-empty-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # C5b: skip the head empty-line removal.
        "module": _swap(
            _BASE, _TRIM,
            "  out := dropTrailingEmpty out\n",
        ),
        "refinement": "omitting the removal of completely-empty lines from the "
                      "beginning of the block leaves leading empty lines in the "
                      "normalized output. A faithful patch that dropped the "
                      "head-trim step would emit a leading blank line where the "
                      "standard algorithm emits none, shifting the block's title "
                      "and diverging from the fixed output → would NOT resolve on a "
                      "block beginning with an empty line.",
        "rationale": "REJECT from C5 (dropLeadingEmpty): at [[], ['a']] the first "
                     "line strips to [] (empty) and the spec then removes it to "
                     "yield [['a']], while the rival returns [[], ['a']]. Refuted "
                     "at a block whose first line is completely empty — the head "
                     "half of the end-trim clause, and a point no other rival "
                     "probes.",
        "witness": (
            "example : ¬ problem_spec_normalizeIndent [[], ['a']]\n"
            "    (implementation_normalizeIndent [[], ['a']]) := by\n"
            "  unfold problem_spec_normalizeIndent\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally-different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps
    # the `theorem correct_normalizeIndent` statement byte-identical; the
    # tactic body is re-authored (only the proof region changes) with no new
    # axiom/theorem/lemma and no assumption token.
    # =====================================================================
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Drop the `Id.run do`/`let mut`/`for` scaffold and return the pure
        # reference directly. Observationally identical on every input, so the
        # obligation closes by `rfl` after unfolding both sides.
        "module": _swap(
            _swap(
                _BASE, _FULL_IMPL,
                "def implementation_normalizeIndent (lines : List (List Char)) :\n"
                "    List (List Char) :=\n"
                "  normalizeIndentSpec lines\n",
            ),
            "-- proof-start\n" + _BASE[
                _BASE.index("-- proof-start\n") + len("-- proof-start\n"):
                _BASE.index("-- proof-end\n")
            ] + "-- proof-end\n",
            "-- proof-start\n"
            "theorem correct_normalizeIndent :\n"
            "    ∀ (lines : List (List Char)),\n"
            "      problem_spec_normalizeIndent lines\n"
            "        (implementation_normalizeIndent lines) := by\n"
            "  intro lines\n"
            "  unfold problem_spec_normalizeIndent implementation_normalizeIndent\n"
            "  rfl\n"
            "-- proof-end\n",
        ),
        "rationale": "a functional reshape that returns the pure reference "
                     "directly computes the same block on every input, so it must "
                     "satisfy result = normalizeIndentSpec lines; if it cannot the "
                     "spec is SPEC-TOO-STRONG. Proof: after unfolding both sides the "
                     "goal is `normalizeIndentSpec lines = normalizeIndentSpec "
                     "lines`, closed by `rfl`. No helper lemma, axiom, or "
                     "assumption token is "
                     "introduced and the theorem statement is byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), so the
    # nagini precondition-admission probe has no binder to attack; the honest
    # analogue is to discharge the spec predicate at the ground F2P-shaped
    # input by `decide`, as a `have` INSIDE the existing tactic body, then close
    # the frozen obligation verbatim. If that ground instance could not be
    # discharged the modeled behavior would be unsatisfiable at the input the
    # F2P asserts about (the analogue of PRECOND-TOO-STRONG).
    # =====================================================================
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # F2P-shaped input: 'firstline' / '' / '    second line' → the flushed
        # first line, a dropped empty line, and a body dedented by 4.
        "module": _swap(
            _BASE, _PROOF_INTRO,
            "  have _ground : problem_spec_normalizeIndent "
            "[['a'], [], [' ', ' ', ' ', ' ', 'b']]\n"
            "      (implementation_normalizeIndent "
            "[['a'], [], [' ', ' ', ' ', ' ', 'b']]) := by\n"
            "    unfold problem_spec_normalizeIndent; decide\n"
            + _PROOF_INTRO,
        ),
        "rationale": "the obligation is discharged at the ground F2P-shaped input "
                     "(a flush first line, an empty line, an indented body) by "
                     "`decide`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal input, "
                     "the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
                     "ground instance is a `have` inside the existing tactic body, "
                     "the theorem statement is byte-identical, and no new "
                     "declaration or assumption token appears.",
    },
]
