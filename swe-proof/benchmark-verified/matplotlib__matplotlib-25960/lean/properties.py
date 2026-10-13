"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25960 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_subfigureGrid`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the file elaborates with the obligation closed
(no ``sorry``/``admit``/``native_decide``, no new ``axiom``/``theorem``);
``expect="reject"`` passes iff it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts ``grid_cell_placement(...)`` — one cell's rectangle — over ``float``
scalars, pinning all four extents to grounded closed forms
(``col_left``/``col_right``/``row_top``/``row_bottom``) plus grid-fill edge and
strictly-positive-gap clauses. This Lean bundle models the SAME purely-functional
core, but over the WHOLE grid at once: ``problem_spec_subfigureGrid`` pins the
entire ``List (List Rect)`` to the grounded oracle ``gridRects``, which assembles
each panel rectangle from the same four grounded extents (``colLeft``/``colRight``
for columns, ``rowTop``/``rowBottom`` for rows) under the equal-extent /
proportional-gap tiling. Coordinates are exact ``ℚ`` (not ``float``), so the
refutation search is decidable — the concrete-grid GUARDS the nagini rivals
needed to keep Z3 from diverging under ``--float-encoding=real`` are UNNECESSARY
here, and the rivals are stated in their clean unbranched form.

DEFENDED SURFACE (one modeled behavior; a single grounded top-level clause).
``problem_spec_subfigureGrid nrows ncols wspace hspace result`` pins EXACTLY:

  result = gridRects nrows ncols wspace hspace

i.e. row-major (row 0 topmost), one panel rectangle per ``(j,i)`` whose
left/right are column ``i``'s edges ``colLeft``/``colRight`` and whose
bottom/top are row ``j``'s edges ``rowBottom``/``rowTop``. The clause is a single
equality but it constrains FOUR independent extents of every panel; a rival is
refuted whenever ANY extent of ANY panel disagrees, so the four nagini
sub-clauses (the four extents) and its grid-fill edges (``i=0 => left=0``,
``j=0 => top=1``, …) are all subsumed by this one grounded equality — the edges
are the ``i=0`` / ``j=0`` instances of the column/row closed forms.

That subsumption was MACHINE-CHECKED rather than asserted (audit): all four
nagini grid-fill edge clauses and its strictly-positive-gap clause were derived
as theorems from these closed forms alone, for arbitrary ``nrows``/``ncols`` ≥ 1
and spacing ≥ 0 — ``colLeft nc s 0 = 0``, ``rowTop nr s 0 = 1``,
``colRight nc s (nc-1) = 1``, ``rowBottom nr s (nr-1) = 0``, and
``colRight nc s i < colLeft nc s (i+1)`` for ``s > 0`` (the last three need
``field_simp``/``div_self`` and ``nlinarith``, the first two are ``norm_num``).
So nothing the sibling's extra clauses said about the layout is lost by folding
them into the single equality.

The oracle is GROUNDED, not an answer-key: ``gridRects`` is spelled out as linear
``ℚ`` arithmetic on the inputs (``panelExtent k s = 1/(k+s·(k-1))``,
``panelGap = s·panelExtent``, cumulative column/row offsets), so echoing it IS
doing the correct work. There is no wrong echo to build; in its place the battery
carries honest cheapest-impl POSITIVE CONTROLS that must verify.

BINDER STRUCTURE. The spec predicate has FOUR input binders: ``nrows``, ``ncols``,
``wspace``, ``hspace``. All four are load-bearing (the fix's whole point is that
``wspace``/``hspace`` visibly move panels) and all four are varied across the
reject witnesses (see the point-spread block at the bottom): ``nrows ∈ {1,2,3}``,
``ncols ∈ {1,2,3}``, ``wspace ∈ {0,1,2}``, ``hspace ∈ {0,1,2}``. The eight reject
witnesses probe six DISTINCT input tuples; where two rivals share an input they
break DIFFERENT clauses of the equality (see the distinguishing notes).

The equality pins TWO independent things, and the battery attacks both. The six
VALUE rivals corrupt the extent arithmetic (which rectangle each panel gets); the
two SHAPE rivals (``weak-short-rows``, ``weak-transposed``) leave every extent
correct and corrupt the result's outer LENGTH / row-major NESTING instead. Shape
is a property only this bundle can state — the nagini sibling contracts one cell,
so it has no grid shape to get wrong — and it is therefore attacked here rather
than ported.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini file itself records this
    class as N/A: ``grid_cell_placement`` takes only float scalars by value and
    constructs a fresh result, so there is no caller-supplied mutable object and
    ``has_readonly_input = False``. On this referentially transparent carrier it
    is doubly vacuous — the inputs are immutable ``Nat``/``ℚ`` values, there is no
    aliasing and no read-only cell to overwrite. No substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE here, and the earlier reading of
    this class as "vacuous because a diverging impl cannot be written" was WRONG.
    Corrected by measurement (audit): the impl region admits
    ``partial def implementation_subfigureGrid ... := implementation_subfigureGrid
    ...``, a genuinely non-terminating rival with no decreasing measure, and it is
    REJECTED (build exit 1: ``rfl`` cannot show the opaque ``partial`` constant
    equals ``gridRects``). So the rival exists and the spec does reject it. What
    does NOT exist is a WITNESS that discriminates it, and that is a property of
    ``partial`` rather than of the battery: Lean compiles a ``partial def`` to an
    opaque constant with no equation lemmas, so (a) the by-evaluation witness the
    value rivals use FAILS on the rival itself (exit 1 — nothing reduces), and
    (b) the hypothesis-conditioned form
    ``example (hdiv : implementation_subfigureGrid 1 2 1 0 ≠ gridRects 1 2 1 0) : ¬ ...``
    ELABORATES ON BOTH SIDES (rival 0, gold 0 — measured), i.e. the gate scores it
    ``witness-vacuous``, because the hypothesis is exactly the conclusion and
    nothing about gold can refute it. A witness would have to prove the opaque
    constant differs from ``gridRects``, which is precisely what ``partial``
    makes unprovable. Recorded as a KNOWN HOLE in the reject lane (the spec does
    not distinguish "diverges" from "wrong value" in a witnessable way), NOT as a
    vacuous class — this bundle sets no ``loom.semantics.termination`` option and
    discharges no termination obligation, so it behaves like the ``partial``
    disposition. No case is shipped for it and none is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS (grounded oracle, as above). Replaced by the
    honest positive controls below.

  * PARTIAL-DOMAIN / VALUE — the real attack surface. Rivals correct on part of
    the domain but diverging where the gap factor / cell width / row orientation
    matters, each rejected by the grounded equality.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that (a) reduces the rival's ``Id.run do`` loop
to its concrete list literal with a ``have himpl`` (``simp`` with the
range-unfolding lemmas + ``rfl``), then (b) rewrites the goal and refutes the
resulting extent equality over ``ℚ`` by ``norm_num`` on the unfolded
``colLeft``/``colRight``/``rowTop``/``rowBottom``. Each witness binds NOTHING in
its head (all inputs are ground literals), so there are no hypotheses whose
consistency could be in question. Each was checked with two real ``lake env
lean`` builds to HOLD of its rival and to FAIL on the frozen solution (the
frozen impl does not reduce to the rival's gap-less/reflected/inflated/transposed
literal, so ``himpl`` fails on gold), so it discriminates rather than asserting a
tautology. ALL EIGHT use this scaffold, ``weak-transposed`` included — see the
measured reason at ``_W8``; an earlier form of that one witness skipped ``himpl``
and was hollow.

That each gold-side failure is a real REFUTATION, and not merely a scaffold that
cannot reduce gold, was checked separately — "``himpl`` fails on gold" is also
what an UNREDUCIBLE impl would look like, and the gate cannot tell those apart
(it screens stuck ``decide`` reductions, not a stuck ``rfl``). The FORGERY test:
for each of the five distinct witness inputs, the same ``simp ...; rfl`` scaffold
was built against gold asserting the FLIPPED claim (gold IS correct there, with
gold's true literal). All five ELABORATED (exit 0) while the corresponding
witnesses FAIL on gold (exit 1), so the scaffold does reduce
``implementation_subfigureGrid`` and each gold-side exit code TRACKS the claim
rather than reporting a stuck term. The failures are legible as such: Lean prints
both sides fully reduced, differing exactly in the spacing argument
(``colLeft 2 1 i`` vs ``colLeft 2 0 i``), in the list's length, or in the nesting.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
The F2P test ``test_subfigures_wspace_hspace`` reads each subfigure's
``bbox.min``/``bbox.max`` on the ``subfigures(2, 3, wspace=1/6, hspace=1/2)``
grid, where the correct layout has column lefts ``[0, 7/20, 7/10]``, rights
``[3/10, 13/20, 1]``, row tops ``[1, 2/5]``, bottoms ``[3/5, 0]``. Each reject
rival's faithful real counterpart mis-computes one of those extents on that grid
(drops the spacing factor, inflates a cell, or reflects the rows), so the
observed bbox mismatches the asserted value and the F2P would NOT resolve — a
verifying rival would be a genuine verify⇏resolve break.

AXIOM lane: EMPTY here. ``meta.axioms == []``; the grid geometry is modeled
deeply (``gridRects`` is closed-form arithmetic, an A-reference validated == the
real ``get_grid_positions`` by G-AX/G-CONF, not a consumed axiom). The nagini
``AXIOM_TESTS`` (the A-reference deep-model soundness probe) belong to G-AX, not
this spec-lane gate, and are dropped. ``AXIOM_TESTS = []``.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25960"
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


# ---- region anchors (each unique inside Solution.lean, verified at load) ----
# The four grid-line arrays the impl builds before the nested row/col loop. Each
# line is a full, unique substring lying wholly inside `-- impl-start`/`-- impl-end`,
# so every reshape below leaves the spec view (and the `correct_subfigureGrid`
# STATEMENT) byte-identical.
_A_LEFTS = "  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)"
_A_RIGHTS = "  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)"
_A_BOTTOMS = "  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)"
_A_TOPS = "  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)"

# The outer (row) loop header, for the grid-shape rival.
_A_FORJ = "  for j in [0:nrows] do"

# The inner loop body's two `let`s + the row append (for the inline positive).
_A_INNER = ("      let left := lefts[i]!\n"
            "      let right := rights[i]!\n"
            "      row := row ++ [Rect.ofExtents left bottom right top]")

# The whole frozen impl def (for the functional positive) and the whole frozen
# proof body after the theorem STATEMENT (re-proved for the functional shape).
_A_IMPL = _BASE[_BASE.index("def implementation_subfigureGrid"):_BASE.index("-- impl-end")]
_A_PROOF = _BASE[_BASE.index("  intro nrows ncols wspace hspace h1 h2 h3 h4"):_BASE.index("-- proof-end")]


# ---------------------------------------------------------------------------
# witness scaffold. Reduce the rival's ranged `for` loop to its concrete list
# literal (`himpl`), rewrite the goal, then refute the resulting extent equality
# over ℚ. `himpl` is the discriminator: it holds of the rival by construction and
# FAILS on gold (gold's impl does not reduce to this gap-less/reflected/inflated
# literal), so the witness fails on gold at the `himpl` step.
# ---------------------------------------------------------------------------
def _w(nr, nc, ws, hs, lit):
    return (
        f"example : ¬ problem_spec_subfigureGrid {nr} {nc} {ws} {hs}\n"
        f"    (implementation_subfigureGrid {nr} {nc} {ws} {hs}) := by\n"
        "  unfold problem_spec_subfigureGrid\n"
        f"  have himpl : implementation_subfigureGrid {nr} {nc} {ws} {hs} =\n"
        f"      {lit} := by\n"
        "    simp [implementation_subfigureGrid, Id.run, "
        "Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
        "    rfl\n"
        "  rw [himpl]\n"
        "  intro h\n"
        "  simp only [gridRects, List.range, List.range.loop, List.map, "
        "Rect.ofExtents,\n"
        "    List.cons.injEq, Rect.mk.injEq, and_true, and_self] at h\n"
        "  norm_num [colLeft, colRight, rowTop, rowBottom, panelExtent, panelGap] at h")


# ============================================================================
# UNIQUENESS / PARTIAL-DOMAIN rivals — same spec, wrong impl. MUST be rejected.
# ============================================================================

# R1: gap-less on BOTH axes = the pre-fix behavior (drops the (1+wspace)/(1+hspace)
# separation; equivalently computes as though wspace=hspace=0). Cells abut.
_R1 = _swaps(
    _BASE,
    (_A_LEFTS, _A_LEFTS.replace("colLeft ncols wspace i", "colLeft ncols 0 i")),
    (_A_RIGHTS, _A_RIGHTS.replace("colRight ncols wspace i", "colRight ncols 0 i")),
    (_A_BOTTOMS, _A_BOTTOMS.replace("rowBottom nrows hspace j", "rowBottom nrows 0 j")),
    (_A_TOPS, _A_TOPS.replace("rowTop nrows hspace j", "rowTop nrows 0 j")),
)
_W1 = _w(1, 2, 1, 0,
         "[[Rect.ofExtents (colLeft 2 0 0) (rowBottom 1 0 0) (colRight 2 0 0) (rowTop 1 0 0),\n"
         "        Rect.ofExtents (colLeft 2 0 1) (rowBottom 1 0 0) (colRight 2 0 1) (rowTop 1 0 0)]]")

# R2: horizontal-only gap drop (columns laid out gap-less, rows correct).
_R2 = _swaps(
    _BASE,
    (_A_LEFTS, _A_LEFTS.replace("colLeft ncols wspace i", "colLeft ncols 0 i")),
    (_A_RIGHTS, _A_RIGHTS.replace("colRight ncols wspace i", "colRight ncols 0 i")),
)
_W2 = _w(1, 3, 1, 0,
         "[[Rect.ofExtents (colLeft 3 0 0) (rowBottom 1 0 0) (colRight 3 0 0) (rowTop 1 0 0),\n"
         "        Rect.ofExtents (colLeft 3 0 1) (rowBottom 1 0 0) (colRight 3 0 1) (rowTop 1 0 0),\n"
         "        Rect.ofExtents (colLeft 3 0 2) (rowBottom 1 0 0) (colRight 3 0 2) (rowTop 1 0 0)]]")

# R3: vertical-only gap drop (rows laid out gap-less, columns correct).
_R3 = _swaps(
    _BASE,
    (_A_BOTTOMS, _A_BOTTOMS.replace("rowBottom nrows hspace j", "rowBottom nrows 0 j")),
    (_A_TOPS, _A_TOPS.replace("rowTop nrows hspace j", "rowTop nrows 0 j")),
)
_W3 = _w(2, 1, 0, 1,
         "[[Rect.ofExtents (colLeft 1 0 0) (rowBottom 2 0 0) (colRight 1 0 0) (rowTop 2 0 0)],\n"
         "       [Rect.ofExtents (colLeft 1 0 0) (rowBottom 2 0 1) (colRight 1 0 0) (rowTop 2 0 1)]]")

# R4: cell WIDTH inflated to swallow the gap (right = left + extent·(1+wspace)).
# Left edges correct, right edges overrun into the gap.
_R4 = _swap(
    _BASE, _A_RIGHTS,
    _A_RIGHTS.replace("colRight ncols wspace i",
                      "colLeft ncols wspace i + panelExtent ncols wspace * (1 + wspace)"))
_W4 = _w(1, 2, 2, 0,
         "[[Rect.ofExtents (colLeft 2 2 0) (rowBottom 1 0 0) (colLeft 2 2 0 + panelExtent 2 2 * (1 + 2)) (rowTop 1 0 0),\n"
         "        Rect.ofExtents (colLeft 2 2 1) (rowBottom 1 0 0) (colLeft 2 2 1 + panelExtent 2 2 * (1 + 2)) (rowTop 1 0 0)]]")

# R5: rows counted from the BOTTOM (vertical reflection): row j uses row
# (nrows-1-j)'s extents. Columns correct.
_R5 = _swaps(
    _BASE,
    (_A_BOTTOMS, _A_BOTTOMS.replace("rowBottom nrows hspace j", "rowBottom nrows hspace (nrows - 1 - j)")),
    (_A_TOPS, _A_TOPS.replace("rowTop nrows hspace j", "rowTop nrows hspace (nrows - 1 - j)")),
)
_W5 = _w(3, 1, 0, 2,
         "[[Rect.ofExtents (colLeft 1 0 0) (rowBottom 3 2 (3 - 1 - 0)) (colRight 1 0 0) (rowTop 3 2 (3 - 1 - 0))],\n"
         "       [Rect.ofExtents (colLeft 1 0 0) (rowBottom 3 2 (3 - 1 - 1)) (colRight 1 0 0) (rowTop 3 2 (3 - 1 - 1))],\n"
         "       [Rect.ofExtents (colLeft 1 0 0) (rowBottom 3 2 (3 - 1 - 2)) (colRight 1 0 0) (rowTop 3 2 (3 - 1 - 2))]]")

# R7: SHAPE attack — the row loop stops one short, so the grid is MISSING its last
# row entirely. Every extent it does emit is correct; the grid DIMENSIONS are wrong.
# (Added by audit: R1-R6 all preserve the nrows x ncols shape and corrupt only
# extent VALUES, so nothing in the ported set attacked the result's shape. This
# axis exists only on this carrier — the nagini sibling contracts ONE cell, so it
# has no grid shape to get wrong.)
_R7 = _swap(_BASE, _A_FORJ, _A_FORJ.replace("[0:nrows]", "[0:nrows - 1]"))
_W7 = (
    "example : ¬ problem_spec_subfigureGrid 2 1 0 1\n"
    "    (implementation_subfigureGrid 2 1 0 1) := by\n"
    "  unfold problem_spec_subfigureGrid\n"
    "  have himpl : implementation_subfigureGrid 2 1 0 1 =\n"
    "      [[Rect.ofExtents (colLeft 1 0 0) (rowBottom 2 1 0) (colRight 1 0 0) "
    "(rowTop 2 1 0)]] := by\n"
    "    simp [implementation_subfigureGrid, Id.run, "
    "Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
    "    rfl\n"
    "  rw [himpl]\n"
    "  intro h\n"
    "  simp [gridRects, List.range, List.range.loop, List.map, Rect.ofExtents] at h")

# R8: SHAPE attack #2 — the grid is TRANSPOSED (column-major outer list). Every
# panel rectangle is individually correct and the multiset of rectangles is right;
# only the NESTING order is wrong, so it is refuted wherever nrows ≠ ncols.
# (Added by audit: the sharpest near-miss on the row-major clause, and the one a
# per-cell contract cannot express at all.)
_R8 = _swap(
    _BASE, _A_IMPL,
    "def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :\n"
    "    List (List Rect) :=\n"
    "  (List.range ncols).map (fun i =>\n"
    "    (List.range nrows).map (fun j =>\n"
    "      Rect.ofExtents (colLeft ncols wspace i) (rowBottom nrows hspace j)\n"
    "                     (colRight ncols wspace i) (rowTop nrows hspace j)))\n")
# _W8 uses the SAME `himpl`-reduction scaffold as the value rivals, and does so
# for a measured reason. Its first form skipped `himpl` (the transposed impl is a
# plain nested `map`, so the goal reduces without the loop-unfolding step) and
# instead unfolded gold's `Id.run do` in the goal and left it to `simp`. That form
# passed both halves of the gate's check — rival 0, gold 1 — but its gold-side
# exit code carried NO information about the claim: gold failed with
# `unsolved goals ⊢ ¬(List.map ... ).flatten = [...]`, i.e. `simp` could not
# normalise gold's ranged-`for` term either way. Rebuilding a FORGERY that
# differs only in dropping the `¬` — asserting gold is CORRECT at (1,2,1,0) —
# produced the byte-identical error under the same scaffold, so the gate would
# have recorded `rejected` for a witness claiming gold satisfies the spec there.
# The `himpl` form below fixes that: it states the rival's concrete transposed
# literal, so gold's failure is `rfl` reporting gold's OWN reduced grid against
# that literal — and the corresponding flipped claim (gold's TRUE literal in the
# same scaffold) ELABORATES against gold, which is what makes the exit code track
# the claim rather than the scaffold.
_W8 = (
    "example : ¬ problem_spec_subfigureGrid 1 2 1 0\n"
    "    (implementation_subfigureGrid 1 2 1 0) := by\n"
    "  unfold problem_spec_subfigureGrid\n"
    "  have himpl : implementation_subfigureGrid 1 2 1 0 =\n"
    "      [[Rect.ofExtents (colLeft 2 1 0) (rowBottom 1 0 0) (colRight 2 1 0) "
    "(rowTop 1 0 0)],\n"
    "       [Rect.ofExtents (colLeft 2 1 1) (rowBottom 1 0 0) (colRight 2 1 1) "
    "(rowTop 1 0 0)]] := by\n"
    "    simp [implementation_subfigureGrid, Id.run, "
    "Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
    "    rfl\n"
    "  rw [himpl]\n"
    "  intro h\n"
    "  simp [gridRects, List.range, List.range.loop, List.map, Rect.ofExtents] at h")

# R6: one extra horizontal gap baked into every column edge (col 0 no longer at 0).
_R6 = _swaps(
    _BASE,
    (_A_LEFTS, _A_LEFTS.replace("colLeft ncols wspace i", "colLeft ncols wspace i + panelGap ncols wspace")),
    (_A_RIGHTS, _A_RIGHTS.replace("colRight ncols wspace i", "colRight ncols wspace i + panelGap ncols wspace")),
)
_W6 = _w(1, 2, 1, 0,
         "[[Rect.ofExtents (colLeft 2 1 0 + panelGap 2 1) (rowBottom 1 0 0) (colRight 2 1 0 + panelGap 2 1) (rowTop 1 0 0),\n"
         "        Rect.ofExtents (colLeft 2 1 1 + panelGap 2 1) (rowBottom 1 0 0) (colRight 2 1 1 + panelGap 2 1) (rowTop 1 0 0)]]")


# ============================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each keeps the theorem STATEMENT identical.
# ============================================================================

# P1: purely FUNCTIONAL reshape — the whole grid as a single nested `map`
# (no `Id.run do`, no `mut`, no ranged `for`). Definitionally equal to `gridRects`,
# so the obligation closes by `rfl` after unfolding. Re-proved inside the proof
# region; STATEMENT byte-identical, no new axiom/lemma. (Verified: real build.)
_POS_FUNC = _swaps(
    _BASE,
    (_A_IMPL,
     "def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :\n"
     "    List (List Rect) :=\n"
     "  (List.range nrows).map (fun j =>\n"
     "    (List.range ncols).map (fun i =>\n"
     "      Rect.ofExtents (colLeft ncols wspace i) (rowBottom nrows hspace j)\n"
     "                     (colRight ncols wspace i) (rowTop nrows hspace j)))\n"),
    (_A_PROOF,
     "  intro nrows ncols wspace hspace h1 h2 h3 h4\n"
     "  unfold problem_spec_subfigureGrid implementation_subfigureGrid gridRects\n"
     "  rfl\n\n"),
)

# P2: inline the inner loop's two `let`s directly into the rectangle constructor
# (drop the named `left`/`right` bindings). Definitionally the same loop body, so
# the frozen imperative proof still closes unchanged. (Verified: real build.)
_POS_INLINE = _swap(
    _BASE, _A_INNER,
    "      row := row ++ [Rect.ofExtents lefts[i]! bottom rights[i]! top]")


# ============================================================================
# ADMISSIBILITY — the obligation is SATISFIABLE at a normal F2P-shaped input.
# Discharge the spec predicate by evaluation at a concrete grid (2 columns,
# wspace=1 — the smallest instance where the spacing factor bites) as a `have`,
# then close the frozen obligation verbatim. Nothing is assumed: no new
# declaration, STATEMENT byte-identical, the ground instance is a `have`
# prepended to the existing tactic body. (Verified: real build.)
# ============================================================================
_ADMISS = _swap(
    _BASE, "  intro nrows ncols wspace hspace h1 h2 h3 h4",
    "  have _ground : problem_spec_subfigureGrid 1 2 1 0\n"
    "      (implementation_subfigureGrid 1 2 1 0) := by\n"
    "    have himpl : implementation_subfigureGrid 1 2 1 0 =\n"
    "        [[Rect.ofExtents (colLeft 2 1 0) (rowBottom 1 0 0) (colRight 2 1 0) (rowTop 1 0 0),\n"
    "          Rect.ofExtents (colLeft 2 1 1) (rowBottom 1 0 0) (colRight 2 1 1) (rowTop 1 0 0)]] := by\n"
    "      simp [implementation_subfigureGrid, Id.run, "
    "Std.Range.forIn_eq_forIn_range', Std.Range.size]\n"
    "      rfl\n"
    "    unfold problem_spec_subfigureGrid\n"
    "    rw [himpl]\n"
    "    simp [gridRects, List.range, List.range.loop, List.map, Rect.ofExtents]\n"
    "  intro nrows ncols wspace hspace h1 h2 h3 h4")


SPEC_TESTS = [
    # ---- positive controls ------------------------------------------------
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNC,
        "rationale": "Structurally different CORRECT impl: the whole grid as a "
                     "single nested `map` (no `Id.run do`/`mut`/`for`), "
                     "definitionally equal to the grounded oracle `gridRects`. "
                     "Re-proved by `unfold ...; rfl`; the `correct_subfigureGrid` "
                     "STATEMENT is byte-identical, no new axiom/lemma. Must verify, "
                     "else SPEC-TOO-STRONG. Ports the nagini pos-helpers positive "
                     "(there: call the grounded @Pure helpers directly; here the "
                     "functional map IS a direct application of the same helpers).",
    },
    {
        "id": "pos-inline-row",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": "Correct reshape that inlines the inner loop's two named "
                     "`let` bindings into the rectangle constructor; it computes "
                     "the SAME row on every input, definitionally the frozen loop "
                     "body, so the frozen imperative proof still closes unchanged. "
                     "STATEMENT byte-identical, no new axiom/lemma. Must verify, "
                     "else SPEC-TOO-STRONG. Ports the nagini pos-factored positive "
                     "(a structurally-different-but-equal executable shape).",
    },
    # ---- admissibility ----------------------------------------------------
    {
        "id": "admiss-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "The obligation is discharged at a concrete F2P-shaped input "
                     "(2 columns, wspace=1 — the smallest instance where the "
                     "spacing factor moves a panel) by evaluation as a `have`, then "
                     "the frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior would be unsatisfiable at a normal input — "
                     "the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, STATEMENT byte-identical. Ports nagini's "
                     "admiss-grid self-call.",
    },
    # ---- uniqueness / partial-domain rivals -------------------------------
    {
        "id": "weak-gapless-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R1,
        "refinement": "This IS the pre-fix behavior (Solution_prepatch.lean): the "
                      "(1+wspace)/(1+hspace) separation is dropped on both axes so "
                      "cells abut, as though the requested spacing were zero. The "
                      "faithful real patch (instantiate the panels from the gridspec "
                      "but never recompute their rectangles from the spacing) is "
                      "exactly the unfixed code — on the F2P grid column 1 lands at "
                      "1/3 of the width, not the required 7/20, so the F2P bbox "
                      "assertions fail. A verifying rival here would be verify⇏resolve.",
        "rationale": "REJECT from the grounded equality: the spec pins column "
                     "lefts to `colLeft ncols wspace i` (carrying the (1+wspace) "
                     "factor) but the rival emits `colLeft ncols 0 i`, which differ "
                     "for any i>0, wspace>0. Refuted at (nrows,ncols,wspace,hspace)="
                     "(1,2,1,0), column 1 (rival 1/2, spec 2/3).",
        "witness": _W1,
    },
    {
        "id": "weak-hdrop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R2,
        "refinement": "Rows correct, columns laid out gap-less (drops the (1+wspace) "
                      "factor on the horizontal axis only). A faithful patch that "
                      "honored vertical but not horizontal spacing would place the "
                      "second/third columns at the wrong x on the F2P grid "
                      "(column 1 at w·1/3 not w·7/20), so the F2P "
                      "sub_figs[*,1]/[*,2] x-coordinate assertions fail — NOT "
                      "resolution.",
        "rationale": "REJECT from the grounded equality on the column extents: the "
                     "spec pins `colLeft/colRight ncols wspace i` but the rival "
                     "emits the wspace=0 forms, differing for any i>0, wspace>0. "
                     "Refuted at (1,3,1,0), column 1.",
        "witness": _W2,
    },
    {
        "id": "weak-vdrop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R3,
        "refinement": "Columns correct, rows laid out gap-less (drops the (1+hspace) "
                      "factor on the vertical axis only). A faithful patch honoring "
                      "horizontal but not vertical spacing would place row 1 at the "
                      "wrong y on the F2P grid (top of row 1 at 1/2 not 2/5), so the "
                      "F2P y-coordinate assertions fail — NOT resolution. This rival "
                      "exercises the hspace/nrows binders the horizontal rivals hold "
                      "fixed.",
        "rationale": "REJECT from the grounded equality on the row extents: the "
                     "spec pins `rowTop/rowBottom nrows hspace j` but the rival "
                     "emits the hspace=0 forms, differing for any j>0, hspace>0. "
                     "Refuted at (2,1,0,1), row 1.",
        "witness": _W3,
    },
    {
        "id": "weak-fatcell",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R4,
        "refinement": "Left edges correct (col 0 at 0), but each cell's width "
                      "swallows the gap (right = left + extent·(1+wspace)). A "
                      "faithful patch using the wrong cell width makes cells overrun "
                      "into the gaps — on the F2P grid col 0's right would be "
                      "0.3·(7/6)=0.35 not 0.3, so sub_figs[*,0].bbox.max[0] mismatches "
                      "and the F2P fails.",
        "rationale": "REJECT from the grounded equality on the right extent: the "
                     "spec pins `colRight = colLeft + panelExtent` but the rival "
                     "emits `colLeft + panelExtent·(1+wspace)`, differing whenever "
                     "wspace>0. Refuted at (1,2,2,0), column 0: `panelExtent 2 2` "
                     "= 1/(2+2·1) = 1/4, so the spec's right edge is 1/4 while the "
                     "rival's is (1/4)·3 = 3/4.",
        "witness": _W4,
    },
    {
        "id": "weak-row-reflect",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R5,
        "refinement": "Columns correct; rows counted from the BOTTOM (row j takes "
                      "row (nrows-1-j)'s extents — a vertical reflection). A faithful "
                      "patch indexing the grid positions bottom-up would put the top "
                      "row's panels at the bottom of the figure — on the F2P grid "
                      "cell (0,*)'s top becomes 2/5 not 1, so the F2P top-row "
                      "assertions (bbox.max[1]=h) fail.",
        "rationale": "REJECT from the grounded equality on the row extents: the "
                     "spec pins `rowTop/rowBottom nrows hspace j` but the rival "
                     "emits `... (nrows-1-j)`, disagreeing for a non-palindromic "
                     "row index (nrows≥2). Refuted at (3,1,0,2), row 0 (rival "
                     "top = row 2's top ≠ 1).",
        "witness": _W5,
    },
    {
        "id": "weak-extra-gap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R6,
        "refinement": "An extra horizontal gap is baked into every column edge "
                      "(off-by-one gap count), so even column 0 is pushed right by "
                      "one gap. A faithful patch with this off-by-one breaks the "
                      "grid-fill (first column no longer at 0) and shifts every F2P "
                      "x-coordinate — sub_figs[*,0].bbox.min[0] ≠ 0 — so the F2P "
                      "fails. Cheap near-miss supporting case (still resolution-false).",
        "rationale": "REJECT from the grounded equality: the spec pins column 0's "
                     "left to `colLeft ncols wspace 0` = 0, but the rival adds "
                     "`panelGap ncols wspace` > 0. Refuted at (1,2,1,0), column 0 "
                     "(rival left = panelGap 2 1 > 0, spec 0). Same input as "
                     "weak-gapless-prepatch but corrupts a DIFFERENT extent (the "
                     "gapless rival is correct at column 0; this one is wrong there), "
                     "so the two are distinct rivals refuted by distinct facts.",
        "witness": _W6,
    },
    # ---- grid-SHAPE rivals (added by audit) -------------------------------
    {
        "id": "weak-short-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R7,
        "refinement": "The row walk stops one short, so the grid is missing its "
                      "LAST row: a 2x3 request yields a 1x3 result. A faithful "
                      "patch that iterated the row positions off-by-one would "
                      "build one row fewer than requested, so the F2P's "
                      "`sub_figs[1, *]` reads would be out of bounds (an IndexError "
                      "rather than a bbox mismatch) — plainly NOT resolution. "
                      "Every extent this rival DOES emit is correct, so only the "
                      "result's shape is at fault.",
        "rationale": "REJECT from the grounded equality on the OUTER list length: "
                     "the spec pins `result = gridRects nrows ncols ...`, whose "
                     "outer list is `List.range nrows` (length nrows), but the "
                     "rival's is length nrows-1. Refuted at (2,1,0,1), where the "
                     "spec demands 2 rows and the rival returns 1. This is the "
                     "SHAPE axis: rivals R1-R6 all preserve the nrows x ncols "
                     "shape and corrupt extent VALUES only, so the row/column "
                     "COUNTS were pinned by the spec but unattacked until now. "
                     "The axis is lean-only — the nagini sibling contracts a "
                     "single cell and so has no grid shape to get wrong.",
        "witness": _W7,
    },
    {
        "id": "weak-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R8,
        "refinement": "The grid is transposed: the outer list walks COLUMNS and "
                      "the inner list walks ROWS, so a 1x2 request returns a 2x1 "
                      "result. Every panel rectangle is individually correct and "
                      "the multiset of rectangles is exactly right — only the "
                      "row-major nesting is wrong. A faithful patch that assembled "
                      "the panel array in column-major order would hand the F2P a "
                      "transposed `sub_figs`, so `sub_figs[0, 1]` would read the "
                      "panel belonging to row 1 column 0 and its bbox assertions "
                      "would fail (and on a non-square grid the indexing would "
                      "raise) — NOT resolution.",
        "rationale": "REJECT from the grounded equality on the result's NESTING: "
                     "the spec pins the outer list to `List.range nrows` and the "
                     "inner to `List.range ncols` (row-major, row 0 topmost), but "
                     "the rival swaps them. Refuted at (1,2,1,0): the spec demands "
                     "one row of two panels, the rival returns two rows of one. "
                     "The sharpest near-miss in the battery — no extent value is "
                     "corrupted at all, so it isolates the row-major clause that "
                     "the value rivals R1-R6 leave untested, and it is a "
                     "distinction a per-cell contract cannot express. The witness "
                     "was REWRITTEN by audit onto the `himpl` scaffold: the "
                     "original skipped `himpl` and its gold-side failure was "
                     "claim-invariant (the flipped claim produced the "
                     "byte-identical error), so the case passed the gate while "
                     "attesting nothing. See the note at `_W8`.",
        "witness": _W8,
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 1-case AXIOM lane. This
# bundle models the SAME single purely-functional core (the per-direction
# equal-extent / proportional-gap tiling), lifted from ONE cell to the WHOLE grid,
# and re-expresses every sibling SPEC case. It adds one rival (weak-vdrop) so the
# vertical binders (nrows/hspace) are attacked in isolation, not only jointly.
#
#   sibling case                 -> here                    disposition
#   -----------------------------------------------------------------------
#   pos-helpers                  -> pos-functional          RE-EXPRESSED (re-proved)
#   pos-factored                 -> pos-inline-row          RE-EXPRESSED
#   admiss-grid                  -> admiss-grid             RE-EXPRESSED
#   weak-gapless-prepatch (R1)   -> weak-gapless-prepatch   PORTED
#   weak-hdrop-partial (R2)      -> weak-hdrop              PORTED (unbranched)
#   weak-row-reflect (R3)        -> weak-row-reflect        PORTED (unbranched)
#   weak-fatcell-gap (R4)        -> weak-fatcell            PORTED
#   weak-extra-gap (R5)          -> weak-extra-gap          PORTED
#   (none)                       -> weak-vdrop              ADDED (nrows/hspace)
#   (none)                       -> weak-short-rows         ADDED by audit (shape)
#   (none)                       -> weak-transposed         ADDED by audit (shape)
#   AXIOM_TESTS (1, A-reference) -> (none)                  DROPPED (G-AX's job)
#
# RE-EXPRESSED (positives): the nagini positives are two structurally-different
#   correct one-cell impls (call the @Pure helpers; an algebraically-factored
#   form). Here the analogues are a purely FUNCTIONAL whole-grid `map` (re-proved
#   by `rfl`) and an inline-loop reshape (frozen proof unchanged) — both compute
#   `gridRects` on every input, verified with real builds.
# UNBRANCHED (weak-hdrop, weak-row-reflect): the nagini rivals GUARD the defect to
#   the F2P grid because the unbranched form made Z3 diverge under
#   --float-encoding=real (1200s timeouts => MALFORMED-TESTS). This carrier is
#   exact ℚ and the witness reduces the loop concretely, so the guard is
#   unnecessary; the rivals are stated in their clean everywhere-wrong form.
# ADDED (weak-vdrop): the nagini horizontal rivals (R1/R2/R5) and R4 all vary the
#   column axis; only R3 touches rows, and it does so jointly with a grid guard.
#   weak-vdrop drops the vertical gap in isolation so nrows>1 / hspace>0 are
#   attacked directly, ensuring no input binder is pinned across the reject set.
#   It attacks the SAME grounded equality (the row extents), not an unmodeled
#   behavior.
# ADDED BY AUDIT (weak-short-rows, weak-transposed): the SHAPE axis. Lifting the
#   model from one cell (nagini) to the whole grid (here) introduced a property
#   the sibling could not state — the result's row/column COUNTS and its
#   row-major NESTING — and the ported rival set left it unattacked: R1-R6 all
#   preserve the nrows x ncols shape and corrupt extent VALUES only. So the
#   ported set could not distinguish the spec's shape clause from a spec that
#   pinned extents alone. weak-short-rows drops the last row (right extents,
#   wrong length); weak-transposed swaps the nesting (every rectangle correct,
#   wrong order). Both refuted from the same grounded equality, both confirmed by
#   real builds (rival 0 / gold 1 on each witness) AND by the forgery test (the
#   flipped claim elaborates against gold, so gold's exit code tracks the claim).
# RE-AUDITED (weak-transposed witness): its FIRST witness form passed the gate
#   hollowly — gold's error was byte-identical for the flipped claim — and was
#   replaced with the `himpl` scaffold the other seven use. See `_W8`.
# SPEC PROBES RUN BY AUDIT, no hole found. Attack D (tuned wrong impls that might
#   still verify): an impl returning garbage exactly where the four hypotheses
#   FAIL (wspace<0 ∨ hspace<0 ∨ nrows=0 ∨ ncols=0) and the grounded oracle
#   elsewhere VERIFIES (exit 0) — expected, not a hole: the obligation is
#   explicitly guarded by `1 ≤ nrows → 1 ≤ ncols → 0 ≤ wspace → 0 ≤ hspace`, so
#   off-domain behavior lies outside the modeled contract and the real callee is
#   unreachable there. Attack E (correct reshapes the spec might wrongly reject):
#   an algebraically FACTORED impl (explicit `stepW`/`stepH`, NOT definitionally
#   equal — needs `ring` per extent) VERIFIES, and so does one whose panel extent
#   uses the Nat-truncated `((k-1 : Nat) : ℚ)` cast, correct only under `1 ≤ k`
#   and therefore consuming h1/h2 via `Nat.cast_sub`. So the spec is neither too
#   weak nor too strong on either probed axis.
# DROPPED (AXIOM_TESTS): the nagini axiom lane re-runs the REAL
#   get_grid_positions to validate the deep geometry model (A-reference
#   soundness). That is G-AX's job; this spec-lane gate ignores AXIOM_TESTS, and
#   the model is closed-form here (no `opaque` callee, meta.axioms == []).
# VACUOUS (frame/permission mutation, divergence): see the module docstring —
#   both classes are inapplicable on this referentially transparent, total
#   carrier; no substitute probe is fabricated.
#
# POINT SPREAD. The eight reject witnesses probe six DISTINCT input tuples:
#   (nrows,ncols,wspace,hspace) =
#     (1,2,1,0)   weak-gapless-prepatch   colLeft factor dropped
#     (1,3,1,0)   weak-hdrop              column extents (wspace=0)
#     (2,1,0,1)   weak-vdrop              row extents (hspace=0)
#     (1,2,2,0)   weak-fatcell            colRight width inflated
#     (3,1,0,2)   weak-row-reflect        row orientation
#     (1,2,1,0)   weak-extra-gap          column 0 offset (shares input w/ R1,
#                                         corrupts a different extent)
#     (2,1,0,1)   weak-short-rows         outer list LENGTH (shape; shares input
#                                         w/ weak-vdrop, wrong shape not value)
#     (1,2,1,0)   weak-transposed         NESTING order (shape; shares input w/ R1,
#                                         every extent value correct)
#   Across them nrows ∈ {1,2,3}, ncols ∈ {1,2,3}, wspace ∈ {0,1,2},
#   hspace ∈ {0,1,2}, so no input binder is held fixed by the reject set.
#   Two ATTACKED DIMENSIONS, not one: the six value rivals corrupt extent
#   arithmetic; the two shape rivals leave every extent correct and corrupt the
#   result's length / nesting. A rival sharing an input tuple with another always
#   breaks a different clause, so no case is a respelling of its neighbour.
AXIOM_TESTS = []
