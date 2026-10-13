"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10323 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_assembleLines`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the assembly over a ``PSeq[PSeq[int]]`` carrier where a "line" is its
content ``PSeq[int]`` and the per-line margin trim of width ``n`` is
``PSeq.drop(n)`` — a TRANSPARENT, per-line, index-addressable operation. This
Lean bundle models the SAME single purely-functional core — the assembly tail of
the include reader: select the file content, de-indent it, then place the
author-supplied prepend/append lines — over a ``List String`` carrier. The
crucial carrier difference: here the de-indentation routine (``dedentCore``) and
the content-selection pass (``selectContent``) are OPAQUE callees (they are
unchanged by the fix and appear identically in spec and impl; the behaviour of
interest is only the ORDER in which de-indentation runs relative to the added
lines, not its internals). So no discriminator here COMPUTES a per-line
``.drop(n)``: what the rivals vary is where and how far the opaque pass reaches in
the composition, and the witnesses CONDITION on the opaque callee rather than
compute it (see WITNESSES). This does NOT cost the sibling's per-line sub-domain
rival — opacity blocks computing the pass, not reshaping the step that applies it
nor stating a hypothesis about it, so ``rival-partial-first-line`` is ported here
rather than dropped (see the accounting block at the bottom).

DEFENDED SURFACE (one modeled behavior; one top-level clause).
``problem_spec_assembleLines opts lines result`` pins EXACTLY one equality:

    result = addAppend opts (addPrepend opts (applyDedent opts (selectContent lines)))

i.e. the result is the exact post-patch composition — select, then de-indent the
selected content, then prepend, then append. The de-indent pass sees ONLY the
selected file content; the prepend/append lines are placed afterwards and so
keep their leading whitespace verbatim. Because the RHS is a total function of
the inputs, the spec is DETERMINISTIC: exactly one satisfying ``result`` per
input, so any same-spec impl whose ``correct_assembleLines`` closes cleanly is
extensionally identical to gold.

The BEHAVIOURAL DISCRIMINATOR (the fix): the de-indentation must run BEFORE the
prepend/append steps, not after. The pre-fix behavior ran de-indent LAST, so it
also stripped the leading whitespace of the author-supplied lines. The
``rival-prepatch`` case below IS that pre-fix behavior.

BINDER STRUCTURE. The spec predicate reads FOUR observable inputs: ``opts.dedent``
(is the de-indent pass requested), ``opts.prepend`` (the optional prepend line),
``opts.append`` (the optional append line), and ``lines`` (the file's line list).
All four are load-bearing and all four are varied across the reject witnesses
(see the point-spread block at the bottom): ``dedent ∈ {true,false}``,
``prepend ∈ {some non-empty, some EMPTY, none}``,
``append ∈ {some non-empty, some EMPTY, none}``, and ``lines`` takes four
distinct shapes. The seven reject witnesses probe seven DISTINCT input tuples
(``pts=7``). Both author-line options are varied across BOTH sides of their own
non-empty guard, not merely between present and absent.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling notes its inputs
    are pure ``PSeq`` values carrying no heap permission, so its frame-mutation
    class is already vacuous THERE; on this referentially transparent carrier it
    is doubly so — ``opts``/``lines`` are immutable values, there is no aliasing
    and no read-only cell to overwrite. No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by an equality to a composition of the actual input carrier (the
    opaque callees applied to ``lines``, wrapped by the transparent
    prepend/append steps). There is no opaque ANSWER KEY to echo — producing the
    result means running the modeled composition. In its place the battery
    carries honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class. An earlier
    revision of this manifest recorded it as vacuous because "a diverging impl
    cannot be written at all". That reason is FALSE and an independent audit
    measured it: ``partial def spin (opts) (ls) := spin opts ls`` with
    ``implementation_assembleLines := spin`` passes ``same_spec`` and
    ``variant_problems`` returns ``[]``, so a non-terminating rival IS
    expressible and scope-legal on this carrier. What makes the class
    unshippable is the WITNESS side, not the impl side. A ``partial def`` gets no
    equation lemmas, so its application is irreducible: the rival module itself
    fails (``unfold`` cannot unfold it), and every witness shape fails too —
    a ground refutation fails against the RIVAL as well (nothing reduces, so the
    half that must succeed does not); a refutation conditioned on the diverging
    helper's own name is rejected by ``witness_scope_problems`` (a variant-only
    name, whose gold-side failure would be an unknown identifier rather than a
    satisfied spec); and one conditioned on ``implementation_assembleLines``
    itself is a tautology that ELABORATES against the frozen solution too, i.e.
    ``witness-vacuous``. So there is no admissible discriminator to ship and the
    honest disposition is a known hole in the spec: the frozen obligation says
    nothing about termination, and this bundle carries no ``set_option
    loom.semantics.termination`` line (that setting is velvet-side here). Stated
    as a hole rather than as vacuity because a vacuous class would claim the
    battery is complete, and it is not.

  * ORDER / PLACEMENT — APPLIES. The rivals attack WHERE the opaque de-indent
    pass runs and WHICH author line is emitted verbatim: de-indent applied LAST
    over the whole assembled block (the pre-fix bug), de-indent applied after the
    prepend but before the append (trims the lead only), the de-indent pass
    dropped entirely, and the prepend/append author lines transposed.

  * SUB-DOMAIN / GUARD — APPLIES. Two further rivals attack the composition at
    points the order rivals leave intact: the de-indent pass's EXTENT over the
    selected block (applied to every selected line but the first) and the
    author-line steps' own non-empty GUARD (a present-but-empty ``prepend``
    inserting a bare-newline line instead of adding nothing).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that reduces the rival's ``Id.run do`` fold
(``List.forIn_cons``/``forIn_nil``), unfolds the transparent
``applyDedent``/``addPrepend``/``addAppend`` steps, and refutes the spec
equality at one concrete configuration.

Because the de-indent pass is an OPAQUE callee, four of the seven witnesses
CONDITION on the carrier instead of computing it, taking a hypothesis of the
shape ``dedentCore (line :: rest) ≠ line :: dedentCore rest`` — the pass does not
commute with re-attaching a line at the front. For the three ORDER rivals that
line is the author-supplied prepend, and the hypothesis names the exact
sub-domain where de-indenting AFTER the prepend disagrees with de-indenting the
selected content alone; for ``rival-partial-first-line`` it is the selected
block's own first line, with a second hypothesis fixing the selection to a
two-line block. Those hypotheses are about opaque terms, so they are jointly
satisfiable (no axiom constrains ``dedentCore`` or ``selectContent``) and the
gate's consistency probe correctly fails to derive ``False`` from them.

The other two witnesses are fully GROUND: the transposed author lines differ by
the concrete literal head (closed by ``decide`` after ``injection``), and the
empty-guard rival's result is a strict ``cons`` over gold's (closed by
``List.cons_ne_self``). Each witness was checked with real ``lake env lean``
builds — to HOLD of its rival and to FAIL on the frozen solution — so it
discriminates rather than asserting a tautology. On the frozen solution the
shared reduction prefix collapses the spec equality to ``True``, leaving the goal
``¬True``: the gold-side failure is the spec being SATISFIED at that input, not a
tactic mismatch.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
reader whose assembly pipeline mis-orders the de-indent pass or transposes the
author lines, so on the F2P scenario (de-indent + prepend + append together) it
emits a mangled first/last line and the F2P
``test_LiteralIncludeReader_dedent_and_append_and_prepend`` would mismatch — so
the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The two ``opaque`` callees carry NO consumed
``axiom … _prop`` (the changed operation — the step order — is modeled deeply and
structurally); the axiom lane belongs to G-AX, and the nagini ``AXIOM_TESTS``
(also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10323"
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
# The post-patch filter list line — the ORDER the fix installs. It lies wholly
# inside `-- impl-start`/`-- impl-end`; the reorder rivals swap only this line.
_I_FILTERS = "    [selectContent, applyDedent opts, addPrepend opts, addAppend opts]"

# The two-line filter-list declaration (decl + list). The swap rival replaces
# this block to introduce a local with the two author options transposed; the
# partial-domain and empty-guard rivals replace it to introduce a local step
# function that stands in for one of the four gold steps.
_I_FILTERS_DECL = (
    "  let filters : List (List String → List String) :=\n"
    "    [selectContent, applyDedent opts, addPrepend opts, addAppend opts]"
)

# The whole gold impl body (inside the impl region) — replaced wholesale by the
# structurally-different positive control so no stale intermediate lingers.
_GOLD_IMPL = (
    "def implementation_assembleLines\n"
    "    (opts : IncludeOptions) (lines : List String) : List String := Id.run do\n"
    "  let filters : List (List String → List String) :=\n"
    "    [selectContent, applyDedent opts, addPrepend opts, addAppend opts]\n"
    "  let mut acc := lines\n"
    "  for f in filters do\n"
    "    acc := f acc\n"
    "  return acc"
)

# The frozen proof body (inside the proof region) — the tactic script only. The
# STATEMENT above it is untouched, so `correct_assembleLines` stays byte-identical.
_GOLD_PROOF = (
    "  intro opts lines\n"
    "  unfold problem_spec_assembleLines implementation_assembleLines\n"
    "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]"
)

# sanity: landmarks present exactly once.
for _lm in (_I_FILTERS, _I_FILTERS_DECL, _GOLD_IMPL, _GOLD_PROOF):
    assert _BASE.count(_lm) == 1, f"landmark drift: {_lm!r}"


# ---------------------------------------------------------------------------
# witness scaffolds.
# ---------------------------------------------------------------------------
def _wit(opts_lit, lines_lit, hyp, tail):
    """A refutation `example`. `hyp` is an optional conditioning hypothesis on
    the opaque de-indent pass (empty string for a fully-ground witness); `tail`
    is the tactic block after the shared reduction that closes `¬ (spec eq)`."""
    head = f"example {hyp}:\n" if hyp else "example :\n"
    return (
        f"{head}"
        f"    ¬ problem_spec_assembleLines\n"
        f"        {opts_lit} {lines_lit}\n"
        f"        (implementation_assembleLines\n"
        f"          {opts_lit} {lines_lit}) := by\n"
        "  unfold problem_spec_assembleLines implementation_assembleLines\n"
        "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]\n"
        "  simp only [applyDedent, addPrepend, addAppend]\n"
        f"{tail}"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_assembleLines` STATEMENT byte-identical.
    # =====================================================================
    {
        "id": "pos-inline-sequential",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: drop the `filters`-list `for`
        # fold and apply the four steps as an explicit sequential chain of `let`s.
        # It computes the SAME composition on every input, so the single spec
        # equality still holds. The proof simplifies (no `forIn` to unfold), so it
        # is re-proved with the reduced `simp only [Id.run, pure]`; STATEMENT
        # byte-identical, no new axiom/lemma. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_GOLD_IMPL,
             "def implementation_assembleLines\n"
             "    (opts : IncludeOptions) (lines : List String) : List String := Id.run do\n"
             "  let selected := selectContent lines\n"
             "  let dedented := applyDedent opts selected\n"
             "  let withPrepend := addPrepend opts dedented\n"
             "  let withAppend := addAppend opts withPrepend\n"
             "  return withAppend"),
            (_GOLD_PROOF,
             "  intro opts lines\n"
             "  unfold problem_spec_assembleLines implementation_assembleLines\n"
             "  simp only [Id.run, pure]"),
        ),
        "rationale": "correct reshape that replaces the `filters`-list fold with an "
                     "explicit sequential `let` chain of the same four steps in the "
                     "same order; it computes the SAME composition on every input, so "
                     "the single spec equality still holds — else SPEC-TOO-STRONG. "
                     "Re-proved with the reduced `simp only [Id.run, pure]` (no "
                     "`forIn` to unfold); statement byte-identical, no new "
                     "axiom/lemma. Ports the nagini pos-control-reshape positive "
                     "(there: a named-intermediate reshape of the backward fold; here "
                     "the fold is unrolled into a named-intermediate chain). "
                     "CALIBRATION (measured, so the strength of this control is not "
                     "overstated): the reshape is DEFINITIONALLY equal to the frozen "
                     "impl — the frozen tactic script closes it unchanged, and the "
                     "frozen impl itself closes by bare `rfl`. So this case attests "
                     "that the spec is not over-fit to one SYNTACTIC layout; it does "
                     "NOT attest that the spec admits a reshape the kernel must work "
                     "to identify. pos-commute-added-lines is the control that does "
                     "the latter (the frozen script alone does not close it).",
    },
    {
        "id": "pos-commute-added-lines",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two INDEPENDENT tail steps: add the append line BEFORE the
        # prepend line. addPrepend acts on the front and addAppend on the back, so
        # they commute — the same function is computed. Re-proved by unfolding the
        # two steps and case-splitting the option guards. STATEMENT byte-identical,
        # no new axiom/lemma. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_FILTERS,
             "    [selectContent, applyDedent opts, addAppend opts, addPrepend opts]"),
            (_GOLD_PROOF,
             "  intro opts lines\n"
             "  unfold problem_spec_assembleLines implementation_assembleLines\n"
             "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]\n"
             "  unfold addPrepend addAppend\n"
             "  cases opts.prepend <;> cases opts.append <;> simp_all <;>\n"
             "    split <;> split <;> simp_all"),
        ),
        "rationale": "reorder the two INDEPENDENT tail steps — append the trailing "
                     "line before prepending the leading one. The prepend step acts "
                     "on the front and the append step on the back, so they commute "
                     "and the SAME function is computed; a faithful reshape MUST "
                     "verify, else SPEC-TOO-STRONG. Re-proved by unfolding the two "
                     "steps and case-splitting the `Option` guards (statement "
                     "byte-identical, no new axiom/lemma). This is exactly the "
                     "commuting variant the spec's own reviewer note calls a positive "
                     "control.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so the
    # nagini precondition-admission self-call re-expresses as: discharge the spec
    # predicate by reduction at the concrete F2P configuration (de-indent + a
    # prepend + an append together, over a one-line file) as a `have`, then close
    # the frozen obligation verbatim. Nothing is assumed: no new declaration,
    # statement byte-identical, ground instance is a `have` prepended to the
    # existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_PROOF,
            "  have _ground : problem_spec_assembleLines\n"
            "      { dedent := true, prepend := some \"class Foo:\","
            " append := some \"# comment\" } [\"  def baz():\\n\"]\n"
            "      (implementation_assembleLines\n"
            "        { dedent := true, prepend := some \"class Foo:\","
            " append := some \"# comment\" } [\"  def baz():\\n\"]) := by\n"
            "    unfold problem_spec_assembleLines implementation_assembleLines\n"
            "    simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]\n"
            "  intro opts lines\n"
            "  unfold problem_spec_assembleLines implementation_assembleLines\n"
            "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]"),
        "rationale": "the obligation is discharged at the F2P-shaped configuration "
                     "(de-indent requested together with a prepend and an append line "
                     "over a one-line file) by reduction as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input — "
                     "the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, statement byte-identical, ground instance is a "
                     "`have` in the existing tactic body. Ports nagini's "
                     "admiss-f2p-shape.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: de-indent applied LAST, over the whole assembled block --
    {
        "id": "rival-prepatch-dedent-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behavior (== Solution_prepatch.lean): the de-indent pass is the
        # LAST step, so it strips leading whitespace from the prepend/append lines
        # too, not only the selected content.
        "module": _swap(
            _BASE, _I_FILTERS,
            "    [selectContent, addPrepend opts, addAppend opts, applyDedent opts]"),
        "refinement": "this IS the pre-fix behaviour: the de-indent pass runs LAST, "
                      "after the prepend/append lines were inserted, so it strips "
                      "leading whitespace from the author-supplied lines too. Its "
                      "faithful real patch is precisely the UN-patched reader "
                      "pipeline, which FAILS the F2P "
                      "test_LiteralIncludeReader_dedent_and_append_and_prepend (it "
                      "emits a de-indented prepend line instead of the verbatim one). "
                      "So it would NOT resolve.",
        "rationale": "the discriminating bug the patch fixes. REJECT from the single "
                     "spec equality: gold pins de-indent applied to the selected "
                     "content BEFORE the prepend, so the leading line is verbatim; the "
                     "rival de-indents after prepending, so the leading line is "
                     "de-indented. Refuted at dedent+prepend over an empty file, "
                     "conditioning on the opaque pass not commuting with prepending an "
                     "author line. If it verified => SPEC-TOO-WEAK (admits the "
                     "un-patched code).",
        "witness": _wit(
            '{ dedent := true, prepend := some "p", append := none }', "[]",
            '(h : dedentCore (("p" ++ "\\n") :: selectContent []) ≠ '
            '("p" ++ "\\n") :: dedentCore (selectContent []))\n    ',
            "  intro heq\n"
            "  exact h heq\n"),
    },

    # ---- de-indent after prepend but before append: trims the LEAD only ----
    {
        "id": "rival-trim-lead-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest discriminator: the de-indent pass runs AFTER the prepend but
        # BEFORE the append, so the leading author line is de-indented while the
        # trailing one is verbatim.
        "module": _swap(
            _BASE, _I_FILTERS,
            "    [selectContent, addPrepend opts, applyDedent opts, addAppend opts]"),
        "refinement": "the de-indent pass runs after the prepend but before the "
                      "append, so only the LEADING author line is de-indented. A "
                      "faithful real patch that moves the de-indent step ahead of the "
                      "append but leaves it reaching the prepend line would emit a "
                      "de-indented leading line and FAIL the F2P (which expects the "
                      "leading line verbatim). So it would NOT resolve.",
        "rationale": "REJECT from the single spec equality: gold applies de-indent to "
                     "the selected content only (leading line verbatim); the rival "
                     "de-indents the prepend line too. Refuted at "
                     "dedent+prepend+append over a one-line file, conditioning on the "
                     "opaque pass not commuting with prepending an author line (the "
                     "trailing append cancels off both sides). If it verified => "
                     "SPEC-TOO-WEAK (verbatim-lead behaviour hollow).",
        "witness": _wit(
            '{ dedent := true, prepend := some "p", append := some "a" }',
            '["x" ++ "\\n"]',
            '(h : dedentCore (("p" ++ "\\n") :: selectContent ["x" ++ "\\n"]) ≠ '
            '("p" ++ "\\n") :: dedentCore (selectContent ["x" ++ "\\n"]))\n    ',
            "  intro heq\n"
            "  apply h\n"
            "  exact List.append_cancel_right heq\n"),
    },

    # ---- de-indent dropped entirely ----
    {
        "id": "rival-no-dedent",
        "kind": "uniqueness",
        "expect": "reject",
        # The de-indent step is removed from the pipeline entirely, so the selected
        # content is emitted un-dedented even when de-indentation is requested.
        "module": _swap(
            _BASE, _I_FILTERS,
            "    [selectContent, addPrepend opts, addAppend opts]"),
        "refinement": "the de-indent step is dropped from the pipeline, so the "
                      "selected content is emitted un-dedented even when "
                      "de-indentation is requested. A faithful real patch that "
                      "removed the dedent_filter entirely would leave the included "
                      "text un-dedented and FAIL the F2P (which expects the dedented "
                      "body). So it would NOT resolve.",
        "rationale": "REJECT from the single spec equality: gold applies de-indent to "
                     "the selected content; the rival never applies it. Refuted at "
                     "dedent requested, no prepend/append, empty file, conditioning on "
                     "the opaque pass actually changing the selected content (its "
                     "presence is exactly what `dedent := true` demands). If it "
                     "verified => SPEC-TOO-WEAK (interior de-indent unpinned).",
        "witness": _wit(
            '{ dedent := true, prepend := none, append := none }', "[]",
            '(h : selectContent [] ≠ dedentCore (selectContent []))\n    ',
            "  intro heq\n"
            "  exact h heq\n"),
    },

    # ---- transpose the prepend/append author lines ----
    {
        "id": "rival-swap-prepend-append",
        "kind": "uniqueness",
        "expect": "reject",
        # The two author lines are transposed: the append value is prepended and the
        # prepend value is appended (prepend/append filters swapped). Interior
        # de-indent correct, but the first/last author lines are exchanged.
        "module": _swap(
            _BASE, _I_FILTERS_DECL,
            "  let optsSwap : IncludeOptions :="
            " { opts with prepend := opts.append, append := opts.prepend }\n"
            "  let filters : List (List String → List String) :=\n"
            "    [selectContent, applyDedent opts, addPrepend optsSwap, addAppend optsSwap]"),
        "refinement": "transposes the prepend/append author lines: the append value "
                      "is placed first and the prepend value last. A faithful real "
                      "patch swapping the prepend and append filters would emit the "
                      "append line first and the prepend line last, FAILING the F2P "
                      "(which pins the leading line to the prepend value and the "
                      "trailing line to the append value). So it would NOT resolve.",
        "rationale": "REJECT from the single spec equality: gold prepends the prepend "
                     "value and appends the append value; the rival exchanges them, so "
                     "the leading line is the append value. Refuted at a concrete "
                     "config with dedent OFF (so the opaque pass drops out) and two "
                     "distinct literal author lines — the leading elements differ by "
                     "`decide`. If it verified => SPEC-TOO-WEAK (author-line order "
                     "unpinned).",
        "witness": _wit(
            '{ dedent := false, prepend := some "p", append := some "a" }',
            '["y" ++ "\\n"]',
            "",
            "  intro heq\n"
            "  injection heq with h1 _\n"
            "  exact absurd h1 (by decide)\n"),
    },

    # ---- partial domain: de-indent every selected line EXCEPT the first ----
    {
        "id": "rival-partial-first-line",
        "kind": "uniqueness",
        "expect": "reject",
        # The de-indent pass is applied to the TAIL of the selected content only:
        # the first selected line is emitted verbatim while the rest are
        # de-indented. Correct on any file whose selected block is empty or a
        # single line the pass fixes, WRONG as soon as the selected block has a
        # first line the pass would have changed. This is the sub-domain rival the
        # nagini sibling carries as `rival-partial-first-line`; it IS expressible
        # here (see the accounting note below) even though `dedentCore` is an
        # opaque whole-list callee, because the witness conditions on the pass not
        # commuting with re-attaching the first selected line rather than
        # computing it per line.
        "module": _swap(
            _BASE, _I_FILTERS_DECL,
            "  let dedentTail : List String → List String := fun ls =>\n"
            "    match ls with\n"
            "    | []     => applyDedent opts []\n"
            "    | h :: t => h :: applyDedent opts t\n"
            "  let filters : List (List String → List String) :=\n"
            "    [selectContent, dedentTail, addPrepend opts, addAppend opts]"),
        "refinement": "the de-indent pass reaches only the TAIL of the selected "
                      "content: the first selected line is emitted verbatim. A "
                      "faithful real patch with an off-by-one in the de-indent "
                      "routine's line walk (start at the second selected line) "
                      "would leave the first line of the included body at its "
                      "original indentation and FAIL the F2P "
                      "test_LiteralIncludeReader_dedent_and_append_and_prepend "
                      "(which pins the whole included body de-indented, first "
                      "line included). So it would NOT resolve.",
        "rationale": "SUB-DOMAIN rival: correct whenever the selected block is "
                     "empty or its first line is one the pass leaves alone, wrong "
                     "as soon as the first selected line would have been "
                     "de-indented. REJECT from the single spec equality: gold "
                     "applies the pass to the WHOLE selected content, the rival "
                     "exempts its head. Refuted at dedent requested with no "
                     "author lines, conditioning on the selection yielding a "
                     "two-line block and on the pass not commuting with "
                     "re-attaching that block's first line. If it verified => "
                     "SPEC-TOO-WEAK (the first-line sub-domain of the de-indent "
                     "pass unpinned). Ports the nagini rival-partial-first-line.",
        "witness":
            'example (hs : selectContent ["  a\\n"] = ["  a\\n", "  b\\n"])\n'
            '    (hd : dedentCore ["  a\\n", "  b\\n"] ≠ '
            '"  a\\n" :: dedentCore ["  b\\n"]) :\n'
            "    ¬ problem_spec_assembleLines\n"
            '        { dedent := true, prepend := none, append := none } ["  a\\n"]\n'
            "        (implementation_assembleLines\n"
            '          { dedent := true, prepend := none, append := none } ["  a\\n"]) := by\n'
            "  unfold problem_spec_assembleLines implementation_assembleLines\n"
            "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]\n"
            "  simp only [applyDedent, addPrepend, addAppend, hs, if_true]\n"
            "  intro heq\n"
            "  exact hd heq.symm\n",
    },

    # ---- the author-line guard: insert even when the value is EMPTY ----
    {
        "id": "rival-prepend-empty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepend step drops the non-empty test: a PRESENT-but-EMPTY prepend
        # value inserts a bare newline line instead of adding nothing. Attacks the
        # truthiness guard the modeled step carries (`some p => if p = "" then …`),
        # which no other rival in this battery touches: every other rival keeps
        # `addPrepend` intact and moves it around.
        "module": _swap(
            _BASE, _I_FILTERS_DECL,
            "  let addPrependAlways : List String → List String := fun ls =>\n"
            "    match opts.prepend with\n"
            "    | some p => (p ++ \"\\n\") :: ls\n"
            "    | none   => ls\n"
            "  let filters : List (List String → List String) :=\n"
            "    [selectContent, applyDedent opts, addPrependAlways, addAppend opts]"),
        "refinement": "the prepend step inserts unconditionally whenever the "
                      "option is PRESENT, dropping the non-empty test. A faithful "
                      "real patch that tested only for the option's presence "
                      "rather than for a non-empty value would emit a spurious "
                      "blank leading line for a present-but-empty value, so the "
                      "assembled block gains a line the reader never adds — the "
                      "surrounding directive tests that pin the exact emitted "
                      "line list would mismatch. So it would NOT resolve.",
        "rationale": "REJECT from the single spec equality, at the GUARD rather "
                     "than at the step order: gold's prepend step inserts only "
                     "for a NON-EMPTY value (the reader's truthiness test), so a "
                     "present-but-empty value adds nothing; the rival inserts a "
                     "bare-newline line. Refuted fully ground at "
                     "`prepend := some \"\"` with dedent off — the rival's result "
                     "is a strict cons over gold's, closed by "
                     "`List.cons_ne_self`. This is the only rival that probes the "
                     "empty-value sub-domain of the author-line guard; the other "
                     "four keep the step intact and permute its position. If it "
                     "verified => SPEC-TOO-WEAK (the non-empty guard hollow).",
        "witness":
            "example :\n"
            "    ¬ problem_spec_assembleLines\n"
            '        { dedent := false, prepend := some "", append := none } []\n'
            "        (implementation_assembleLines\n"
            '          { dedent := false, prepend := some "", append := none } []) := by\n'
            "  unfold problem_spec_assembleLines implementation_assembleLines\n"
            "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]\n"
            "  simp only [applyDedent, addPrepend, addAppend]\n"
            "  exact List.cons_ne_self _ _\n",
    },

    # ---- the same guard on the TRAILING author line ----
    {
        "id": "rival-append-empty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the case above, on the OTHER author-line step: the append step
        # drops its non-empty test, so a PRESENT-but-EMPTY append value adds a
        # bare-newline line at the END instead of adding nothing. Added by the
        # independent audit: every other rival in this battery leaves `addAppend`
        # structurally intact (they permute WHERE it runs, or attack `addPrepend`),
        # so the trailing step's own guard was the one clause with no rival at all
        # — and `append := some ""` was the one value of `append` the point spread
        # never reached. Refuted fully ground. (Verified: real builds — witness
        # holds of the rival, fails on the frozen solution, rival module rejected.)
        "module": _swap(
            _BASE, _I_FILTERS_DECL,
            "  let addAppendAlways : List String → List String := fun ls =>\n"
            "    match opts.append with\n"
            "    | some a => ls ++ [a ++ \"\\n\"]\n"
            "    | none   => ls\n"
            "  let filters : List (List String → List String) :=\n"
            "    [selectContent, applyDedent opts, addPrepend opts, addAppendAlways]"),
        "refinement": "the append step inserts unconditionally whenever the option "
                      "is PRESENT, dropping the non-empty test. A faithful real "
                      "patch that tested only for the option's presence rather "
                      "than for a non-empty value would emit a spurious blank "
                      "trailing line for a present-but-empty value, so the "
                      "assembled block gains a line the reader never adds and the "
                      "surrounding directive tests that pin the exact emitted line "
                      "list would mismatch. So it would NOT resolve.",
        "rationale": "REJECT from the single spec equality, at the TRAILING "
                     "author-line guard: gold's append step inserts only for a "
                     "NON-EMPTY value (the reader's truthiness test), so a "
                     "present-but-empty value adds nothing; the rival appends a "
                     "bare-newline line. Refuted fully ground at "
                     "`append := some \"\"` with dedent off and no prepend — the "
                     "rival's result is gold's with one extra element, so the two "
                     "differ in LENGTH. Complements rival-prepend-empty-guard: "
                     "together they pin the non-empty guard on BOTH author-line "
                     "steps, and this case is what brings `append := some \"\"` "
                     "into the point spread. If it verified => SPEC-TOO-WEAK (the "
                     "trailing step's non-empty guard hollow).",
        "witness":
            "example :\n"
            "    ¬ problem_spec_assembleLines\n"
            '        { dedent := false, prepend := none, append := some "" } []\n'
            "        (implementation_assembleLines\n"
            '          { dedent := false, prepend := none, append := some "" } []) := by\n'
            "  unfold problem_spec_assembleLines implementation_assembleLines\n"
            "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure]\n"
            "  simp only [applyDedent, addPrepend, addAppend]\n"
            "  intro heq\n"
            "  simpa using congrArg List.length heq\n",
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus an EMPTY AXIOM lane. This
# bundle models the SAME single purely-functional core (the include-reader
# assembly tail) and re-expresses EVERY sibling SPEC case — no nagini case is
# dropped for a carrier reason — plus one rival with no sibling counterpart that
# an audit added to cover the author-line guard.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reshape          -> pos-inline-sequential      RE-EXPRESSED
#   echo-honest                  -> pos-commute-added-lines     RE-EXPRESSED
#   admiss-f2p-shape             -> admiss-f2p-shape            RE-EXPRESSED
#   rival-prepatch-trim-all      -> rival-prepatch-dedent-last  PORTED
#   rival-trim-lead-only         -> rival-trim-lead-only        PORTED
#   rival-no-trim-included       -> rival-no-dedent             PORTED
#   rival-swap-lead-trail        -> rival-swap-prepend-append   PORTED
#   rival-partial-first-line     -> rival-partial-first-line     PORTED
#   (no sibling counterpart)     -> rival-prepend-empty-guard    ADDED (audit)
#   (no sibling counterpart)     -> rival-append-empty-guard     ADDED (audit 2)
#   AXIOM_TESTS (0)              -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED (pos-inline-sequential): the sibling's structurally-different
#   positive keeps the backward fold but binds a named per-line local and splits
#   the assembly via a named `head`. This carrier has no fold to preserve (the
#   trim is an opaque whole-list callee, not a per-line `.drop(n)`); the analogous
#   "structurally different but correct" reshape unrolls the `filters` `for` fold
#   into an explicit sequential `let` chain of the same four steps in the same
#   order. Definitionally the same composition; re-proved with the reduced tactic.
# RE-EXPRESSED (pos-commute-added-lines): the sibling's echo-honest control adds
#   a redundant assertion that the built value equals the grounded pin, proving
#   the pin is not echo-vulnerable. On this carrier the grounding is the same (the
#   equality is to a composition of the inputs, no opaque answer key), so the
#   honest positive here is instead the COMMUTING reshape the frozen spec's own
#   reviewer note names — append before prepend — which computes the same function
#   and must verify. Both are honest positive controls demonstrating the spec
#   admits the cheapest correct restructurings; the specific reshape differs
#   because this carrier has no separate oracle term to assert equality against.
# PORTED (rival-partial-first-line): the nagini partial-domain rival leaves the
#   FIRST included LINE untrimmed while trimming the rest. An earlier revision of
#   this manifest recorded the case as INEXPRESSIBLE here, reasoning that the
#   distinction is PER-LINE while `dedentCore : List String → List String` is an
#   OPAQUE whole-list callee that the model never applies line by line. That
#   reasoning was WRONG on both halves and an audit landed the case with real
#   builds:
#     * The impl side does not need per-line application. The rival exempts the
#       head of the selected block by `match ls with | h :: t => h :: applyDedent
#       opts t`, i.e. it applies the SAME whole-list pass to the TAIL — an
#       ordinary reshape of the pipeline's de-indent step, no per-line access
#       required. The rival does not verify (`unsolved goals`, re-checked under an
#       aggressive case-splitting script as well as under the frozen one).
#     * The witness side does not need to COMPUTE the pass. It conditions on the
#       carrier, exactly as the three order rivals already do here: one hypothesis
#       fixes the selection to a two-line block and one states that the pass does
#       not commute with re-attaching that block's first line. Both are about
#       opaque terms, so they are jointly satisfiable (the gate's consistency
#       probe fails to derive `False`, as it must).
#   So the sub-domain the sibling probes IS pinned on this carrier, and the
#   omission was a gap rather than a carrier narrowing. Recorded here because the
#   general claim it rested on — "an opaque whole-list callee cannot carry a
#   per-line sub-domain rival" — is the reasoning to distrust, not to reuse.
# ADDED (rival-prepend-empty-guard): no sibling counterpart; found by the audit's
#   spec-too-weak probe as the clause the ported battery left unattacked. All four
#   ported rivals keep `addPrepend`/`addAppend` intact and permute WHERE the steps
#   run, so none of them tests the steps' own truthiness guard — the modeled
#   `some p => if p = "" then lines else …` that mirrors the reader inserting only
#   for a non-empty value. The rival drops that test (present-but-empty inserts a
#   bare-newline line); it is refuted fully ground at `prepend := some ""`, and it
#   extends the battery's point spread to the empty-string value of `prepend`.
# ADDED (rival-append-empty-guard): no sibling counterpart; found by a SECOND,
#   independent audit's spec-too-weak probe. The rival above closed the guard gap
#   on the LEADING author line only — every other case in the battery, that one
#   included, left `addAppend` structurally intact, so the trailing step's own
#   non-empty test was still unattacked and `append := some ""` was a value the
#   point spread never reached. The mirror rival (present-but-empty `append`
#   appends a bare-newline line) is refuted fully ground: the rival's result is
#   gold's with one extra element, so the two differ in LENGTH and
#   `congrArg List.length` closes it without touching either opaque callee.
# VACUOUS (frame/permission mutation): the sibling itself notes this class is
#   vacuous on its pure PSeq carrier; on this referentially transparent carrier it
#   is doubly vacuous — no `mut` input, no aliasing, no read-only cell. No
#   substitute probe is fabricated.
# KNOWN HOLE (divergence/non-termination): NOT vacuous. An audit measured the
#   claim this block used to make ("a diverging impl cannot be written"): a
#   `partial def` self-call installed as `implementation_assembleLines` clears
#   `same_spec` and `variant_problems == []`, so the rival is expressible and
#   in scope. It is unshippable for a WITNESS reason instead — a `partial def`
#   has no equation lemmas, so nothing reduces on either side: a ground witness
#   fails against the rival too, a witness conditioned on the diverging helper's
#   name is out of the shared vocabulary (`witness_scope_problems`), and one
#   conditioned on `implementation_assembleLines` holds of the frozen solution
#   as well (`witness-vacuous`). No admissible discriminator exists, so the
#   class is recorded as a known hole in the frozen spec (which pins only the
#   value equality, never termination) rather than as a complete lane.
#
# CLAUSE COVERAGE. The spec has a SINGLE top-level clause (one equality to the
# post-patch composition). All seven rivals attack that clause, each at a
# different structural point of the composition: the de-indent pass's POSITION
# relative to the author lines (rival-prepatch-dedent-last,
# rival-trim-lead-only), its PRESENCE (rival-no-dedent), its EXTENT over the
# selected block (rival-partial-first-line), the author lines' ORDER
# (rival-swap-prepend-append), and the author-line steps' own non-empty GUARD on
# each end (rival-prepend-empty-guard for the leading line,
# rival-append-empty-guard for the trailing one).
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input tuples
# (pts=7):
#   (dedent, prepend, append, lines) =
#     (true,  some "p", none,      [])           rival-prepatch-dedent-last
#     (true,  some "p", some "a",  ["x\n"])      rival-trim-lead-only
#     (true,  none,     none,      [])           rival-no-dedent
#     (false, some "p", some "a",  ["y\n"])      rival-swap-prepend-append
#     (true,  none,     none,      ["  a\n"])    rival-partial-first-line
#     (false, some "",  none,      [])           rival-prepend-empty-guard
#     (false, none,     some "",   [])           rival-append-empty-guard
#   Across them dedent ∈ {true,false}, prepend ∈ {some non-empty, some EMPTY,
#   none}, append ∈ {some non-empty, some EMPTY, none}, and lines takes four
#   distinct shapes, so no input binder is pinned to one value and BOTH author-line
#   options are varied across both sides of their own non-empty guard rather than
#   only between present and absent.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
# `axiom … _prop` (the step order is modeled deeply), so there is nothing to probe
# and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
