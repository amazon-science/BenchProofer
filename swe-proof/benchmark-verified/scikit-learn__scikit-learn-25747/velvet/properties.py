"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25747 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct wrapContainer`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable labelled container plus
two read-only optional label sets:

  wrapContainer (mut frame : Frame) (colSupplied : Option (List Lbl))
                (rowSupplied : Option (List Lbl))
      return (out : Except WrapErr Frame)
    ensures frame = frameAfter frameOld colSupplied
    ensures frame.rowLabels = frameOld.rowLabels
    ensures out = wrapResult frameOld colSupplied

The method models the branch that handles a value ALREADY carrying its own two
label axes. ``Frame`` exposes only the two axes a wrapping request can touch
(``colLabels``, ``rowLabels``); ``out`` reports COMPLETION (``Except.ok`` with the
adjusted container) or the size-mismatch FAILURE (``Except.error
WrapErr.sizeMismatch``). There is no ``require`` clause, so the admitted domain is
total. ``frameAfter`` / ``wrapResult`` / ``sizeFits`` / ``resolvedCols`` are
fully-unfolded ``def``s over the method's own arguments (the ``axioms`` region is
empty — no opaque answer key to echo), so every reject rival is refutable at a
concrete ``decide``-able input.

THREE independent top-level clauses, each load-bearing:
  (1) ``frame = frameAfter frameOld colSupplied`` — the container's FINAL state:
      when a fitting column-label set is supplied the column axis is replaced,
      when an ill-fitting one is supplied nothing is written, and when none is
      supplied the column axis is kept.
  (2) ``frame.rowLabels = frameOld.rowLabels`` — the row axis is left EXACTLY as
      the container already had it. This is the DISCRIMINATING clause: the whole
      content of the change is that a caller-offered row-label set does NOT apply
      to a container that already owns one. The prepatch skeleton
      (``Solution_prepatch.lean``) re-introduces the row write and fails exactly
      this clause; the F2P test fits a transformer that re-indexes its container
      output, passes the original row labels to the wrapper, and asserts the
      container KEEPS its own (re-indexed) row labels rather than being
      overwritten with the originals.
  (3) ``out = wrapResult frameOld colSupplied`` — the OUTCOME: a fitting (or
      absent) column-label set completes; an ill-fitting one fails with the
      size-mismatch error and leaves the container untouched.

INPUT BINDERS of the spec predicates: ``frame`` (its ``colLabels`` and
``rowLabels``), ``colSupplied``, ``rowSupplied``. Each is varied by the reject
witnesses so no binder is pinned at a single value across the battery — in
particular ``rowSupplied`` (whose only observable effect is via clause (2)) is
driven off ``none`` by the row-write rival, the sole rival that abuses it.

ADVERSARIAL READ of the sibling classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally-different but correct
    frame-branch impl (hoist the fit test into a local boolean; settle the column
    axis via the pure ``frameAfter`` model instead of an inline record update)
    must verify, else the spec is SPEC-TOO-STRONG on impl shape. Both keep the
    frozen proof.
  * ADMISSIBILITY — the method has NO ``require`` clause, so the sibling's "a
    normal input satisfies the precondition" probe is degenerate (nothing could
    exclude an F2P-shaped input). Re-aimed at the residual admissibility risk on
    a total domain: that the post-image is DEGENERATE at the interesting point.
    ``admiss-nondegenerate`` discharges an in-region ``assert`` pinning all three
    observable outcomes (a fitting column-label set replaces the column axis and
    keeps the row axis; an absent one keeps the column axis; an ill-fitting one
    fails) at concrete F2P-shaped inputs. The impl is kept verbatim so the
    method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries mandatory
    frame-mutation rivals because a read-only label set is lent at a fractional
    heap permission an impl can illegally overwrite. Lean and Velvet are
    referentially transparent: ``colSupplied`` and ``rowSupplied`` are immutable
    ``Option (List Lbl)`` values declared read-only (NOT ``mut``); there is no
    heap, no aliasing, and no permission system to trip. There is no read-only
    input to overwrite and no substitute probe to fabricate. Reported vacuous,
    not fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to the fully-unfolded
    ``frameAfter`` / ``wrapResult`` over the method's own arguments; there is no
    answer-key term a wrong impl could echo. The cheapest honest impl still
    settles the right axis per the fit test, which the positive controls cover.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
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
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival is correct on
    part of the domain and diverges on one sub-domain (the row axis overwritten,
    the column axis never applied, the offered set routed to the WRONG axis, an
    ill-fitting set applied instead of failing, or a completion turned into a
    failure).

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``wrapContainerTester frame colSupplied rowSupplied = false`` says the extracted
program's observable (the mutated container's two axes and the returned outcome)
violates the method's postcondition at that concrete input. Checked in a file
whose ``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The outcome clause needs equality on ``Except WrapErr Frame`` to be
decidable, which the tester machinery cannot synthesize alone, so the instance is
DERIVED first (``deriving instance DecidableEq for Except``) — an instance, not an
assumption (no ``axiom``/``sorry``/``native_decide``), and the frozen solution
rejects these witnesses all the same. Every witness closes by ``decide`` at small
concrete literals.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the operation is
modeled directly over the carrier; the pandas length check is modeled deeply as
``sizeFits``, a G-CONF/G-AX A-reference, not a consumed contract). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25747"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block: a single anchor lying wholly inside the impl
# ---- region and unique in Solution.lean (both facts asserted at load). ------
_GOLD_IMPL = (
    "    if sizeFits colSupplied frame.colLabels then\n"
    "      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }\n"
    "      return Except.ok frame\n"
    "    else\n"
    "      return Except.error WrapErr.sizeMismatch"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body. ---
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- case that introduces an in-region `assert` may retune it without touching
# ---- the spec statement or dropping the `prove_correct wrapContainer`
# ---- obligation. Unique in the file. -----------------------------------------
_GOLD_PROOF = (
    "prove_correct wrapContainer by\n"
    "  loom_solve <;> simp_all [wrapResult, frameAfter, sizeFits, resolvedCols]"
)
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Full variant: replace the gold impl block, keep the frozen proof."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. --
def _tester(body):
    return ("deriving instance DecidableEq for Except\n\n"
            "extract_program_for wrapContainer\n"
            "prove_precondition_decidable_for wrapContainer\n"
            "prove_postcondition_decidable_for wrapContainer\n"
            "derive_tester_for wrapContainer\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # frame-branch impls that MUST verify; else the post-image is
    # SPEC-TOO-STRONG on impl shape. Both keep the frozen proof script (the
    # reshape adds no new obligation).
    # =====================================================================
    {
        "id": "pos-fit-test-hoisted",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the fit test into a local boolean before branching on it. Same
        # control flow (replace the column axis iff the offered set fits, else
        # report the size-mismatch failure), same final container and outcome.
        "module": _impl(
            "    let fits := sizeFits colSupplied frame.colLabels\n"
            "    if fits then\n"
            "      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }\n"
            "      return Except.ok frame\n"
            "    else\n"
            "      return Except.error WrapErr.sizeMismatch"),
        "rationale": "naming the fit test in a local `let fits` before branching "
                     "settles the same column axis on the same condition and "
                     "reports the same outcome, so all three clauses (final "
                     "container, row axis pinned, outcome) still hold on the whole "
                     "domain and the frozen proof discharges unchanged. If it "
                     "failed to verify the spec would be SPEC-TOO-STRONG on the "
                     "shape of the fit test.",
    },
    {
        "id": "pos-settle-via-model",
        "kind": "soundness",
        "expect": "verify",
        # On the fitting branch, settle the container through the pure `frameAfter`
        # model rather than an inline record update. `frameAfter` on the fitting
        # branch IS the same record update, so the final container is identical;
        # the outcome and row-axis clauses are unchanged.
        "module": _impl(
            "    if sizeFits colSupplied frame.colLabels then\n"
            "      frame := frameAfter frame colSupplied\n"
            "      return Except.ok frame\n"
            "    else\n"
            "      return Except.error WrapErr.sizeMismatch"),
        "rationale": "settling the container via the grounded `frameAfter` model on "
                     "the fitting branch yields the same final container (on that "
                     "branch `frameAfter` reduces to the inline column-axis "
                     "update), so the final-state, row-axis, and outcome clauses "
                     "all still hold; the frozen proof discharges it. A correct "
                     "reshape must verify, else SPEC-TOO-STRONG on impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause, so the sibling's "a normal input
    # satisfies the precondition" probe is degenerate. Re-aimed at the residual
    # admissibility risk on a total domain: a DEGENERATE post-image. This case
    # discharges an in-region `assert` pinning all three observable outcomes at
    # concrete F2P-shaped inputs (a fitting column-label set replaces the column
    # axis and keeps the row axis; an absent one keeps the column axis; an
    # ill-fitting one fails). The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the proof gains a `decide` arm to
    # clear the extra assert goal. The assert is live: a false claim about the
    # same point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_START,
                _IMPL_START +
                "    assert (with_name_prefix `admiss (\n"
                "      wrapResult { colLabels := [0], rowLabels := [7] } (some [5])\n"
                "        = Except.ok { colLabels := [5], rowLabels := [7] } ∧\n"
                "      wrapResult { colLabels := [0], rowLabels := [7] } none\n"
                "        = Except.ok { colLabels := [0], rowLabels := [7] } ∧\n"
                "      wrapResult { colLabels := [0], rowLabels := [7] } (some [5, 6])\n"
                "        = Except.error WrapErr.sizeMismatch))\n"),
            _GOLD_PROOF,
            "prove_correct wrapContainer by\n"
            "  loom_solve <;> first\n"
            "    | decide\n"
            "    | simp_all [wrapResult, frameAfter, sizeFits, resolvedCols]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at F2P-shaped "
                     "points: a fitting single-label set must REPLACE the column "
                     "axis while KEEPING the row axis, an absent set must keep the "
                     "column axis, and an ill-fitting set must FAIL with the "
                     "size-mismatch error — three genuinely distinct outcomes, so "
                     "the modeled behaviour really discriminates the cases the fix "
                     "cares about. The in-region assert must discharge (else the "
                     "obligation is degenerate); the impl is kept verbatim so the "
                     "method's own `ensures` still verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # (impl-only swap; the frozen proof is kept, and each rival leaves it with an
    # unsolved goal — but the rejection is ATTRIBUTED to the spec by the
    # machine-checked witness, not by the stale proof failing to match). Each
    # carries the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test, and a witness at a DISTINCT concrete input.
    # =====================================================================
    {
        "id": "rival-prepatch-row-write",
        "kind": "uniqueness",
        "expect": "reject",
        # THE DISCRIMINATING BUG (the prepatch skeleton verbatim): after settling
        # the column axis, ALSO overwrite the row axis with a caller-offered
        # row-label set when one is present and fits. Correct on every input where
        # no fitting row-label set is offered; wrong the moment a fitting
        # `rowSupplied` differs from what the container already had.
        "module": _impl(
            "    if sizeFits colSupplied frame.colLabels then\n"
            "      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }\n"
            "      if sizeFits rowSupplied frame.rowLabels then\n"
            "        frame := { frame with rowLabels := rowSupplied.getD frame.rowLabels }\n"
            "        return Except.ok frame\n"
            "      else\n"
            "        return Except.error WrapErr.sizeMismatch\n"
            "    else\n"
            "      return Except.error WrapErr.sizeMismatch"),
        "refinement": "this re-introduces the deleted row-axis write: a faithful "
                      "counterpart applies the caller-offered row labels to a "
                      "container that already owns its own. That is exactly the bug "
                      "the F2P test asserts against — it fits a transformer that "
                      "re-indexes its container output, calls the wrapper with the "
                      "original row labels, and asserts the container KEEPS its "
                      "re-indexed labels; the row write overwrites them with the "
                      "originals (and in the reporter's aggregation scenario raises "
                      "a length-mismatch error). It would NOT resolve.",
        "rationale": "REJECT from clause (2) `frame.rowLabels = frameOld.rowLabels`: "
                     "overwriting the row axis with a fitting offered set makes the "
                     "final row labels the supplied ones, not the container's prior "
                     "ones. Refuted at `frame = {colLabels:[0], rowLabels:[0]}`, "
                     "`colSupplied = none`, `rowSupplied = some [9]` (a fitting "
                     "single-label offer that differs from the kept row axis) — the "
                     "only witness that drives `rowSupplied` off `none`. If it "
                     "verified => SPEC-TOO-WEAK (admits the very bug the change "
                     "deletes).",
        "witness": _tester(
            "example : wrapContainerTester "
            "{ colLabels := [0], rowLabels := [0] } none (some [9]) = false := by\n"
            "  decide\n"),
    },
    {
        "id": "rival-no-column-refresh",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: never apply the supplied column-label set — hand the
        # container back untouched. Accidentally correct when no column-label set
        # is supplied (the axis is kept anyway) and on the ill-fitting sub-domain
        # (nothing is written there either), but wrong on the (fitting, differing)
        # sub-domain: the refreshed column labels are never applied.
        "module": _impl(
            "    return Except.ok frame"),
        "refinement": "a counterpart that never applies the supplied column labels "
                      "leaves an already-a-container output with its stale column "
                      "labels instead of the estimator's feature names. The P2P "
                      "path that supplies a replacement column set and asserts the "
                      "container reports it back would observe the stale labels — "
                      "it would NOT resolve.",
        "rationale": "REJECT from clause (1) `frame = frameAfter frameOld "
                     "colSupplied`: a fitting supplied set must replace the column "
                     "axis, and this returns the container untouched. Refuted at "
                     "`frame = {colLabels:[0], rowLabels:[7]}`, `colSupplied = some "
                     "[5]` (fitting, differs from [0]), `rowSupplied = none`, where "
                     "the column axis must become [5] and stays [0]. If it verified "
                     "=> SPEC-TOO-WEAK (the column refresh unpinned).",
        "witness": _tester(
            "example : wrapContainerTester "
            "{ colLabels := [0], rowLabels := [7] } (some [5]) none = false := by\n"
            "  decide\n"),
    },
    {
        "id": "rival-ignore-size-mismatch",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the fit test: apply the supplied column labels
        # UNCONDITIONALLY and always report completion — never check that the set
        # fits. Correct whenever the supplied set fits (or is absent); wrong on the
        # ill-fitting sub-domain, where the spec fails with a size-mismatch error
        # and leaves the container untouched.
        "module": _impl(
            "    frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }\n"
            "    return Except.ok frame"),
        "refinement": "a counterpart that assigns the offered column labels without "
                      "the length check would force a mismatched label set onto the "
                      "column axis instead of letting the assignment fail; the "
                      "validation P2P path that supplies an ill-fitting column set "
                      "and expects the size-mismatch failure would instead see a "
                      "silent (wrong-length) success — it would NOT resolve.",
        "rationale": "REJECT from clause (3) `out = wrapResult frameOld colSupplied` "
                     "AND clause (1): on an ill-fitting set the spec demands "
                     "`Except.error WrapErr.sizeMismatch` and an untouched "
                     "container, and this returns `Except.ok` with the mismatched "
                     "set applied. Refuted at `frame = {colLabels:[0], "
                     "rowLabels:[7]}`, `colSupplied = some [5, 6]` (length 2 vs 1 — "
                     "ill-fitting), `rowSupplied = none`. If it verified => "
                     "SPEC-TOO-WEAK (the size check unenforced).",
        "witness": _tester(
            "example : wrapContainerTester "
            "{ colLabels := [0], rowLabels := [7] } (some [5, 6]) none = false := by\n"
            "  decide\n"),
    },
    {
        "id": "rival-always-fail",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the size-mismatch failure UNCONDITIONALLY — never complete, never
        # touch the container. Correct only on the genuinely ill-fitting
        # sub-domain (where the spec also fails); wrong the moment a fitting or
        # absent column set should complete.
        "module": _impl(
            "    return Except.error WrapErr.sizeMismatch"),
        "refinement": "a counterpart that always reports the failure never installs "
                      "any container through the public entry point — the "
                      "successful-wrap paths that must return an adjusted container "
                      "would all raise instead, so the failing test observes no "
                      "wrapped output. It would NOT resolve.",
        "rationale": "REJECT from clause (3) `out = wrapResult frameOld colSupplied` "
                     "AND clause (1): on a fitting (or absent) column set the spec "
                     "demands `Except.ok` with the settled container, and this "
                     "returns `Except.error WrapErr.sizeMismatch` with the "
                     "container untouched. Refuted at `frame = {colLabels:[3], "
                     "rowLabels:[7]}`, `colSupplied = some [8]` (fitting, differs "
                     "from [3]), `rowSupplied = none`, where the spec completes and "
                     "the rival fails. If it verified => SPEC-TOO-WEAK (completion "
                     "unpinned).",
        "witness": _tester(
            "example : wrapContainerTester "
            "{ colLabels := [3], rowLabels := [7] } (some [8]) none = false := by\n"
            "  decide\n"),
    },
    {
        "id": "rival-axis-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        # AXIS CONFUSION: settle the offered column-label set onto the ROW axis and
        # leave the column axis as it stands (the fit test still guards on the
        # column axis, so completion-vs-failure is unchanged). Accidentally correct
        # whenever no column-label set is offered (nothing is written either way);
        # wrong the moment a fitting set is offered — it lands on the wrong axis,
        # violating BOTH the final-container clause and the row-axis pin at once.
        # This is the sub-domain no other rival reaches: the existing row-axis
        # attack drives `rowSupplied`, whereas this one mis-routes `colSupplied`.
        "module": _impl(
            "    if sizeFits colSupplied frame.colLabels then\n"
            "      frame := { frame with rowLabels := resolvedCols colSupplied frame.rowLabels }\n"
            "      return Except.ok frame\n"
            "    else\n"
            "      return Except.error WrapErr.sizeMismatch"),
        "refinement": "a counterpart that routes the offered replacement label set "
                      "to the row axis instead of the column axis relabels the wrong "
                      "axis of an already-a-container output: the column axis keeps "
                      "its stale labels while the row labels the container owns are "
                      "destroyed. That fails the very assertion the failing test "
                      "makes about the container keeping its own row labels, and "
                      "also fails the paths that read the refreshed column labels "
                      "back — it would NOT resolve.",
        "rationale": "REJECT from clause (1) `frame = frameAfter frameOld "
                     "colSupplied` AND clause (2) `frame.rowLabels = "
                     "frameOld.rowLabels`: a fitting offered set must land on the "
                     "COLUMN axis and the row axis must be left alone, and this does "
                     "the opposite. Refuted at `frame = {colLabels:[0], "
                     "rowLabels:[7]}`, `colSupplied = some [5]`, `rowSupplied = "
                     "none`, where the column axis must become [5] (stays [0]) and "
                     "the row axis must stay [7] (becomes [5]). If it verified => "
                     "SPEC-TOO-WEAK (the two axes not pinned to their own roles). "
                     "Added by audit: this is the expressible frame-branch residue "
                     "of the sibling's axis-swap rival, which the port had recorded "
                     "as wholly narrowed away with the array branch.",
        "witness": _tester(
            "example : wrapContainerTester "
            "{ colLabels := [0], rowLabels := [7] } (some [5]) none = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY axiom
# lane, contracting ONE function `wrap_in_container(data_is_frame, df, columns,
# index, nrows, ncols)` that routes labels across BOTH the already-a-container
# (frame) branch AND the fresh-array branch, over full/half-permission
# `List[int]` label sets.
#
# This velvet bundle models a NARROWER surface: only the already-a-container
# (frame) branch, over the `Frame` carrier plus two read-only `Option (List
# Lbl)` label sets — and it ADDS an outcome observable the sibling's value
# abstraction did not carry (the size-mismatch FAILURE of an ill-fitting column
# set, `Except WrapErr Frame` / `sizeFits`). The `data_is_frame` split, the whole
# array branch, `nrows`/`ncols`, and the default RangeIndex labelling are OUTSIDE
# the modeled surface, so every sibling case attached to the array branch has no
# counterpart here (carrier narrowing, not an omission to be back-filled).
#
#   sibling case                      kind          -> here                        disposition
#   -------------------------------------------------------------------------------------------
#   pos-array-axes-reordered          soundness     -> (none)                      NARROWED (array branch)
#   pos-frame-branch-reshaped         soundness     -> pos-fit-test-hoisted        PORTED
#                                                      (+ pos-settle-via-model      ADDED)
#   admiss-self-call-frame-input      admissibility -> admiss-nondegenerate        RE-AIMED
#   rival-prepatch-index-write        uniqueness    -> rival-prepatch-row-write    PORTED
#   rival-frame-mutate-columns        uniqueness    -> (none)                      VACUOUS (frame-mutation)
#   rival-frame-mutate-index          uniqueness    -> (none)                      VACUOUS (frame-mutation)
#   rival-frame-no-column-refresh     uniqueness    -> rival-no-column-refresh     PORTED
#   rival-array-index-wrong-size      uniqueness    -> (none)                      NARROWED (array branch)
#   rival-array-axes-swapped          uniqueness    -> rival-axis-confusion        PORTED (frame-branch residue)
#   (no sibling counterpart)          uniqueness    -> rival-ignore-size-mismatch  ADDED (carrier)
#   (no sibling counterpart)          uniqueness    -> rival-always-fail           ADDED (carrier)
#   AXIOM_TESTS (none)                axiom         -> (none)                      N/A (G-AX)
#
# 3 uniqueness + 1 soundness ported, 1 admissibility re-aimed; 1 soundness added,
# 2 uniqueness added (the outcome observable this carrier introduces); 2
# frame-mutation rivals vacuous, 2 array-branch cases narrowed away. 8 cases:
# 2 soundness + 1 admissibility + 5 uniqueness.
#
# PORTED (rival-prepatch-index-write -> rival-prepatch-row-write): the sibling's
#   headline bug re-introduces the deleted `data_to_wrap.index = index` write in
#   the frame branch. It ports DIRECTLY — the discriminating clause survives the
#   narrowing as clause (2) `frame.rowLabels = frameOld.rowLabels`, and the rival
#   is the prepatch skeleton verbatim. Refuted at a fitting differing rowSupplied.
# PORTED (rival-frame-no-column-refresh -> rival-no-column-refresh): the sibling's
#   frame-branch partial-domain rival (never apply the supplied columns) lives
#   entirely inside the modeled branch and ports directly, refuted on the
#   (fitting, differing) column sub-domain via clause (1).
# RE-AIMED (admissibility): the sibling establishes an F2P-shaped input satisfies
#   its half-permission Requires via a self-call. This backend has no `require`
#   clause and no permission surface, so that probe is degenerate; it is re-aimed
#   at a live in-region assert pinning all THREE observable outcomes at F2P-shaped
#   inputs (fitting-replace-keep-row / absent-keep / ill-fitting-fail).
# ADDED (pos-settle-via-model): a second correct frame-branch reshape (settle via
#   the pure `frameAfter` model) so the soundness surface is defended from more
#   than the single literal shape the sole ported positive covers. The sibling's
#   other positive (pos-array-axes-reordered) is on the array branch and cannot be
#   ported.
# ADDED (rival-ignore-size-mismatch, rival-always-fail): the outcome observable
#   `out = wrapResult frameOld colSupplied` — the completion-vs-size-mismatch
#   failure — has no sibling counterpart (the sibling's value abstraction had no
#   raise/return observable on this branch; its `assessment` calls the
#   control-flow-effect class N/A). On this carrier the failure IS a tagged value,
#   so clause (3) is directly attackable: ignore-size-mismatch applies an
#   ill-fitting set and reports success (refuted on the ill-fitting sub-domain),
#   always-fail reports the failure unconditionally (refuted on the fitting
#   sub-domain). Each has a machine-checked witness.
# VACUOUS (rival-frame-mutate-columns, rival-frame-mutate-index): the sibling's
#   two MANDATORY frame-mutation rivals write through a read-only label set held
#   at `Acc(list_pred(.), 1/2)` to trip INSUFFICIENT PERMISSION. This backend is
#   referentially transparent: `colSupplied`/`rowSupplied` are immutable values
#   declared read-only (NOT `mut`); there is no heap, no aliasing, no fractional
#   permission. There is no read-only input to overwrite and no substitute probe.
#   Not fabricated.
# NARROWED (pos-array-axes-reordered, rival-array-index-wrong-size): both attack
#   the fresh-array branch (the default RangeIndex sizing of an axis from the
#   payload shape). That branch, `nrows`/`ncols`, and the `data_is_frame` split
#   are OUTSIDE this bundle's modeled surface (mapping.md §1 restricts the model
#   to the already-a-container branch), and the default positional labelling has
#   no carrier here to mis-size — there is no `nrows`/`ncols` binder to get
#   wrong. Carrier narrowing, not a difficulty dodge: fabricating array-branch
#   rivals would attack behaviour this bundle does not model.
# PORTED (rival-array-axes-swapped -> rival-axis-confusion): the sibling states
#   its axis swap on the array branch, but the DISTINCTION it attacks — each
#   supplied label set belongs to its OWN axis — survives the narrowing, because
#   this carrier still has two label axes and one offered set that must land on
#   exactly one of them. So the axis-confusion attack is expressible on the frame
#   branch after all (route `colSupplied` to `rowLabels`), and it is refuted at a
#   fitting offered set by clauses (1) and (2) jointly. Recorded as PORTED rather
#   than narrowed: only the array-branch STATEMENT was inexpressible, not the
#   defect class.
#
# DIVERGENCE / NON-TERMINATION lane - the class is INAPPLICABLE to this impl
#   and CLOSED BY THE SEMANTICS against any rival that manufactures it. The
#   frozen impl is LOOP-FREE (straight-line ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
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
# BINDER / CLAUSE COVERAGE. All three independent top-level clauses are attacked:
#   (1) final container by rival-no-column-refresh (and rival-ignore-size-mismatch,
#   rival-always-fail on the container half); (2) row axis pinned by
#   rival-prepatch-row-write; (3) outcome by rival-ignore-size-mismatch (ok where
#   the spec fails) and rival-always-fail (fail where the spec completes).
#   rival-axis-confusion attacks (1) and (2) JOINTLY — the only rival that tests
#   that the offered set lands on the column axis RATHER THAN the row axis, a
#   claim neither a pure clause-(1) nor a pure clause-(2) rival isolates. All
#   three are defended by the two positive controls and the admissibility case.
#   The five reject witnesses probe four DISTINCT inputs (pts=4):
#     frame={col:[0],row:[0]}, colSupplied=none,     rowSupplied=some[9]  prepatch-row-write
#     frame={col:[0],row:[7]}, colSupplied=some[5],  rowSupplied=none     no-column-refresh
#                                                                        AND axis-confusion
#                              (same point, opposite defects: one fails to write
#                               the column axis, the other writes the row axis)
#     frame={col:[0],row:[7]}, colSupplied=some[5,6],rowSupplied=none     ignore-size-mismatch
#     frame={col:[3],row:[7]}, colSupplied=some[8],  rowSupplied=none     always-fail
#   so `colSupplied` ranges over none, a fitting single-label set, an ill-fitting
#   two-label set, and a fitting set differing from the current axis;
#   `rowSupplied` ranges over some[9] and none (the row-write rival is the only
#   one that drives it off none — clause (2) is the only place rowSupplied is
#   load-bearing, so this is exactly the binder it must move); `frame.colLabels`
#   ranges over [0] and [3]; `frame.rowLabels` over [0] and [7]. No binder is
#   pinned at a single value across the reject set.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom (the pandas length check is modeled deeply as `sizeFits`, a G-CONF/G-AX
#   A-reference, not a consumed contract), so there is nothing here to probe.
AXIOM_TESTS = []
