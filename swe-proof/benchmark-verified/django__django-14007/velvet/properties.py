"""properties.py — G-PBT falsification battery for django__django-14007 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct transformedResultRows`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  transformedResultRows (rows : List (List Int)) (convs : List (Int → Int))
      return (out : List (List Int))
    ensures out = convertRows convs rows

The method takes the rows assembled from the data source and returns them with
each column's per-column transformer applied. ``convertRows`` is a total,
fully-unfolded pure ``def`` over the method's own arguments (the ``axioms``
region is empty — there is NO opaque answer key to echo): it maps ``convertRow``
over every row, and ``convertRow`` walks a row in lock-step with the transformer
list, applying transformer ``j`` to column ``j`` and passing every column past
the end of the transformer list through unchanged. The single load-bearing
``ensures`` therefore pins several independently-attackable behaviors:

  * PER-COLUMN TRANSFORM (F) — column ``j`` of every row equals transformer
    ``j`` applied to that column's raw value; a column with no transformer is an
    identity. This is the delta the change adds: pre-change the raw source
    values were returned verbatim, never run through the per-column transform.
  * ROW COUNT (N) — ``out`` has exactly one row per input row (``convertRows`` is
    structurally length-preserving on the row list).
  * POSITIONAL LOCK-STEP — transformer ``j`` lands on column ``j`` specifically
    (not a shifted / truncated slice of the transformer list).

TWO INPUT BINDERS, both load-bearing and both varied by the reject witnesses:
  * ``rows``  — the assembled source rows; its length drives (N) and each
                element's per-column values drive (F). Witnesses move both the
                row COUNT (1 vs 2 rows) and the row WIDTH (1 vs 2 columns).
  * ``convs`` — the per-column transformer chain; which transformer lands on
                which column drives (F) and POSITIONAL LOCK-STEP. Witnesses move
                its length (a one-transformer chain and a two-transformer chain)
                and, via the rivals, which slice of it is applied.

CARRIER NOTE — THE OPAQUE-TRANSFORMER + DECIDABLE BOUNDARY. A transformer is an
arbitrary ``Int → Int``; in the abstract spec it is opaque, but a witness pins a
CONCRETE transformer literal (e.g. ``fun x => x + 1``) at a concrete input, so the
claim reduces by kernel computation and ``decide`` closes. Each witness refutes
the method's Hoare TRIPLE at that input (see ``_witness``), checked in a file
whose ``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Each reject rival is expressed as a LOOP-FREE closed form over the pure
helpers so ``unfold`` + ``simp only [triple_pure …]`` exposes the rival's actual
returned value for ``decide`` to evaluate. This is a witnessing convenience, not
a weakening: the frozen spec is untouched and each rival's divergence from
``convertRows`` is real at the witnessed input.

  DISCRIMINATION, MEASURED (``scripts/lean_verify.sh``, exit codes observed).
  For all four rivals: witness against the rival exits 0; against the frozen
  solution exits 1; and — the calibration that makes the exit-1 meaningful —
  against a CORRECT loop-free impl (``return convertRows convs rows``) it also
  exits 1, with ``decide`` reporting ``proved that the proposition ¬True is
  false``. So the witness fails wherever the postcondition actually HOLDS, and
  it is tracking wrongness rather than the shape of the impl. Every rival
  additionally fails to verify with a genuine unsolved ``out = convertRows convs
  rows`` goal, not a mechanical tactic mismatch.

  WHY NOT ``derive_tester_for``. Recorded because it is the trap on this carrier
  and the earlier form of this battery fell into it. Stating the witness as
  ``transformedResultRowsTester rows convs = false`` does NOT discriminate here:
  the frozen impl is a ``while`` loop whose ``forIn``/``Classical.choice``
  fixpoint the kernel cannot unfold, so the gold-side ``decide`` never evaluates
  the claim — it fails with ``did not reduce to isTrue or isFalse`` for the
  refutation, for its exact logical OPPOSITE (``… = true``), and for a trivially
  TRUE claim about empty inputs alike (three builds, one error). Gold's exit 1
  would then attest to nothing about the spec.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical impls (return the grounded model directly with no
    loop; keep the backward loop but bind the converted row through an extra
    local) must verify, else the spec is SPEC-TOO-STRONG on the shape of the
    impl.
  * ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    region is empty), so the sibling's "an F2P-shaped input satisfies the
    precondition" probe is degenerate here (every input is in-domain). Re-aimed
    at the residual total-domain risk — that the post-image is DEGENERATE at the
    interesting point — via an in-region ``assert`` pinning that ``convertRows``
    genuinely distinguishes its behaviors (a non-empty transformer TRANSFORMS a
    column; an empty transformer list is an IDENTITY; the transform applies to
    EVERY row). The impl is kept verbatim so the method's own obligation still
    discharges; the proof gains a ``decide`` arm to clear the assert VC.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    this because a read-only sequence input is held at a fractional heap
    permission an impl can illegally overwrite. Lean/Velvet are referentially
    transparent: ``rows`` and ``convs`` are immutable values declared read-only
    (no ``mut`` binder), there is no heap and no aliasing, so there is no
    read-only input to overwrite and no permission system to trip. The class has
    no carrier analogue; NOT ported (fabricating a substitute would test
    nothing). See the footer accounting.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``convertRows convs rows``, a fully-unfolded ``def`` over the
    method's own arguments (empty ``axioms`` region); there is no answer-key term
    a wrong impl could echo. The cheapest correct impl computes the model
    honestly, which the positive controls cover.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (no transform at all, only the
    first column transformed, a shifted transformer slice, or one dropped row).
"""
from pathlib import Path

INSTANCE = "django__django-14007"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every rival / reshape that changes the executable
# ---- surface swaps on this block.
_IMPL = """    -- impl-start
    -- Build the converted result by walking the source rows from the back and
    -- prepending each row's per-column transform; the accumulator is exactly
    -- the conversion of the as-yet-unconsumed tail.
    let mut result : List (List Int) := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = convertRows convs (rows.drop i)
      done_with i = 0
      decreasing i
    do
      let row := rows[i - 1]!
      result := convertRow convs row :: result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the loop-body accumulator line, wholly inside the impl region and unique.
# ---- The loop-preserving positive reshape edits only this line (binding the
# ---- converted row through an extra local), leaving the loop, invariants and
# ---- frozen proof intact.
_ACC_LINE = """      let row := rows[i - 1]!
      result := convertRow convs row :: result"""
assert _BASE.count(_ACC_LINE) == 1, "loop-body accumulator anchor drift"

# ---- the first impl line (unique); the admissibility case inserts an in-region
# ---- `assert` immediately before it, keeping the whole gold body.
_FIRST_IMPL_LINE = "    let mut result : List (List Int) := []"
assert _BASE.count(_FIRST_IMPL_LINE) == 1, "first-impl-line anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl into a single expression, the direct-model
# ---- positive, or the admissibility case retunes it without touching the spec
# ---- or dropping the `prove_correct transformedResultRows` obligation.
_PROOF_GOLD = """prove_correct transformedResultRows by
  loom_solve
  rw [convertRows_drop_step convs rows i (by omega) (by omega)]
  simp_all
"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equality (for
# ---- a correct reshape) or leaves exactly the `out = convertRows convs rows`
# ---- goal unsolved (for the reject rivals, which is the point — the rejection
# ---- is attributable to the spec via the witness, not to a proof script tuned
# ---- to a loop that no longer exists).
_PROOF_FLAT = "prove_correct transformedResultRows by\n  loom_solve\n"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned to the flat shape."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness form. The spec is a `method` CONTRACT, so a witness must reach the
# ---- post-image at a concrete input. It refutes the method's Hoare TRIPLE
# ---- directly:
# ----
# ----   ¬ (triple True (transformedResultRows <rows> <convs>)
# ----        (fun out => out = convertRows <convs> <rows>))
# ----
# ---- i.e. "at THIS input the method does not establish its own postcondition".
# ---- `unfold` exposes the rival's (loop-free) body, `simp only [triple_pure …]`
# ---- collapses the triple over a `pure` computation to the postcondition
# ---- instance itself, and `decide` then evaluates it over the concrete literals
# ---- (with concrete Int→Int transformer lambdas), so the refutation is a KERNEL
# ---- COMPUTATION on the rival's actual returned value.
# ----
# ---- Why NOT the `derive_tester_for` route. An earlier form of this battery
# ---- stated each witness as `transformedResultRowsTester <rows> <convs> = false`.
# ---- That form is NOT a discriminator on this bundle: the frozen impl is a
# ---- `while` loop, which elaborates through a `forIn`/`Classical.choice` fixpoint
# ---- the kernel cannot unfold, so the gold-side `decide` never evaluates the
# ---- claim at all — it fails with
# ---- `did not reduce to isTrue or isFalse`. Measured directly: that error is
# ---- returned verbatim for the refutation, for its exact LOGICAL OPPOSITE
# ---- (`… = true`), and for a trivially TRUE claim about empty inputs
# ---- (`Tester [] [] = true`) — three builds, one error. Gold's exit 1 therefore
# ---- attested to nothing about the spec, which is exactly the `witness-undecided`
# ---- class G-PBT screens for.
# ----
# ---- The triple form is calibrated the other way round: its gold-side failure is
# ---- semantic, and it correctly REFUSES to refute a CORRECT loop-free impl
# ---- (`return convertRows convs rows`), where `decide` evaluates and reports
# ---- `decide proved that the proposition ¬True is false` — i.e. the postcondition
# ---- genuinely holds there. So the witness tracks WRONGNESS, not impl shape.
def _witness(rows_literal, convs_literal):
    return (
        f"example : ¬ (triple (l := Prop) True "
        f"(transformedResultRows {rows_literal} {convs_literal})\n"
        f"    (fun out => out = convertRows {convs_literal} {rows_literal})) := by\n"
        "  unfold transformedResultRows\n"
        "  simp only [triple_pure, le_Prop_eq, true_implies]\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold backward
        # scan. `out` IS `convertRows convs rows`, so the ensures holds trivially;
        # the reproof is a bare `loom_solve` (no loop invariant to peel).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return convertRows convs rows\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`convertRows convs rows` directly (no loop). `out` IS that model, so "
            "the ensures holds on the whole domain; the reproof is `loom_solve`. "
            "If this fails to verify the spec is over-fit to the loop code shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: the "
            "model IS the real work, so a direct return is correct, not a cheat. "
            "(Sibling: pos-control-apply-row-reshape / pos-control-exec-reshape, "
            "collapsed to one function's model on this carrier.)"),
    },
    {
        "id": "pos-control-loop-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole backward loop, both invariants and the frozen proof
        # script; only binds the converted row through an extra local `conv`
        # before prepending. Observationally identical for every input.
        "module": _swap(
            _BASE, _ACC_LINE,
            "      let row := rows[i - 1]!\n"
            "      let conv := convertRow convs row\n"
            "      result := conv :: result"),
        "rationale": (
            "binding the per-row transform through a local `conv` before "
            "prepending walks the same row stream with the same step, so "
            "`out = convertRows convs rows` still holds on the whole domain; the "
            "loop, both invariants and the frozen proof script are untouched. A "
            "correct reshape must verify, else the postcondition is SPEC-TOO-STRONG "
            "(rejects a faithful impl over the shape of the loop body). (Sibling: "
            "pos-control-*-reshape — the extra-typed-local reshape, ported.)"),
    },
    {
        "id": "pos-control-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        # Added by audit. The two positives above are both close to the frozen
        # impl: `direct-model` returns the model term itself and `loop-reshape`
        # is DEFINITIONALLY equal to gold (an extra `let`), so neither forces the
        # obligation to be re-proven for a genuinely different traversal. This one
        # does: it walks the rows FORWARD and appends, so the loop invariant is
        # over `rows.take i` instead of `rows.drop i` and the frozen backward
        # drop-step lemma does not apply at all. The reproof has to establish that
        # `convertRows` distributes over `++` and that `take (i+1)` peels an
        # element off the END — the mirror image of the frozen argument, obtained
        # only inside the tactic body (no new top-level theorem).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let mut result : List (List Int) := []\n"
            "    let mut i := 0\n"
            "    while i < rows.length\n"
            "      invariant 0 ≤ i ∧ i ≤ rows.length\n"
            "      invariant result = convertRows convs (rows.take i)\n"
            "      done_with i = rows.length\n"
            "      decreasing rows.length - i\n"
            "    do\n"
            "      result := result ++ [convertRow convs rows[i]!]\n"
            "      i := i + 1\n"
            "    return result\n"
            "    -- impl-end",
            "prove_correct transformedResultRows by\n"
            "  loom_solve\n"
            "  have happ : ∀ (xs ys : List (List Int)),\n"
            "      convertRows convs (xs ++ ys)\n"
            "        = convertRows convs xs ++ convertRows convs ys := by\n"
            "    intro xs ys\n"
            "    induction xs <;> simp_all [convertRows_cons, convertRows_nil]\n"
            "  have hlt : i < rows.length := by omega\n"
            "  have hx : rows.take (i+1) = rows.take i ++ [rows[i]!] := by\n"
            "    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt,\n"
            "      Option.getD_some]\n"
            "    exact List.take_succ_eq_append_getElem hlt\n"
            "  rw [hx, happ]\n"
            "  simp_all [convertRows_cons, convertRows_nil]\n"),
        "rationale": (
            "the same per-row transform accumulated in the OPPOSITE traversal "
            "order: forward over `rows` with an append, so the invariant is over "
            "`rows.take i` and the frozen backward `convertRows_drop_step` lemma "
            "is inapplicable. `out = convertRows convs rows` still holds on the "
            "whole domain, and the obligation is genuinely RE-PROVEN for the new "
            "shape (the append-distribution and take-peel steps are established "
            "inside the tactic body). This is the positive that would catch a spec "
            "over-fit to the backward-scan direction rather than to the transform "
            "itself — neither existing positive can, since one returns the model "
            "term and the other is definitionally equal to gold. Verified: exit 0."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO precondition (the pre-conditions region is
    # empty), so the sibling's "an F2P-shaped input satisfies the precondition"
    # probe (admiss-self-call) is degenerate here (every input is in-domain). The
    # residual admissibility risk on this domain is that the post-image is
    # DEGENERATE at the interesting point — a spec no impl distinguishes reads
    # exactly like one every impl meets. This case discharges an in-region
    # `assert`, at fully concrete F2P-shaped inputs, that the post-image is
    # NON-DEGENERATE: a non-empty transformer chain TRANSFORMS a column (the
    # converted-vs-raw delta the fix adds), an EMPTY transformer list is an
    # IDENTITY (the no-converter passthrough), and the transform applies to EVERY
    # row (the row-map). The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm to clear the
    # assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _FIRST_IMPL_LINE,
                  "    assert (with_name_prefix `admiss (\n"
                  "      convertRows [fun x => x + 1] [[(5:Int)]] = [[6]] ∧\n"
                  "      convertRows ([] : List (Int → Int)) [[(5:Int)]] = [[5]] ∧\n"
                  "      convertRows [fun x => x + 1] [[(1:Int)], [(2:Int)]] = [[2], [3]]))\n"
                  + _FIRST_IMPL_LINE),
            _PROOF_GOLD,
            "prove_correct transformedResultRows by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [convertRows_drop_step convs rows i (by omega) (by omega)]; simp_all)\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: a non-empty single-transformer chain must turn column value 5 "
            "into 6 (the transform is genuinely APPLIED — the converted-vs-raw delta "
            "the fix adds), an EMPTY transformer list must leave the value 5 "
            "unchanged (the no-converter identity passthrough), and the transform "
            "must apply to EVERY row of a two-row input. The in-region assert must "
            "discharge (else the model would be constant / the obligation "
            "degenerate); the impl is kept verbatim so `out = convertRows convs "
            "rows` still verifies. (Sibling: admiss-self-call, re-aimed from "
            "precondition admissibility to post-image non-degeneracy since this "
            "backend has no precondition and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a LOOP-FREE
    # closed form (single expression over the pure helpers) so its extracted
    # tester `decide`s (see the CARRIER NOTE); the frozen spec is untouched, and
    # each rival fails to verify with a genuine unsolved `out = convertRows convs
    # rows` goal.
    # =====================================================================
    {
        "id": "weak-raw-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug delta: return the source rows unchanged, never running them
        # through the per-column transform. This is the pre-change behaviour (raw
        # fetched values returned verbatim). Wrong on every input whose transformer
        # chain is non-empty and non-identity on the raw value.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return rows\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-change shape: the assembled source rows are returned "
            "verbatim, never run through the per-column transform. The failing "
            "scenario asserts a returned identity value carries the type tag its "
            "field's value-transform produces (a wrapper), i.e. the transform WAS "
            "applied; raw passthrough leaves a plain untransformed value, so a "
            "faithful counterpart that skipped the transform would NOT resolve — it "
            "is exactly the behaviour the change removes."),
        "rationale": (
            "REJECT from `out = convertRows convs rows` via the PER-COLUMN "
            "TRANSFORM (F): with a non-empty transformer on column 0 the spec "
            "demands the transformed value, but the rival returns the raw value. "
            "Verifying would be SPEC-TOO-WEAK (the transform is unenforced). "
            "Refuted at one row of one column with a `+1` transformer (raw 5 vs "
            "transformed 6). (Sibling: weak-exec-raw-passthrough / "
            "weak-row-raw-passthrough — the two raw-passthrough attacks collapse "
            "into one on this single-function carrier.)"),
        "witness": _witness("[[(5:Int)]]", "[fun x => x + 1]"),
    },
    {
        "id": "weak-first-column-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Transform only the first column (apply the truncated one-element
        # transformer list to every row), leaving every column p >= 1 raw. Correct
        # for one-column rows (the single-PK create case) but wrong for any row
        # whose column p >= 1 has a non-identity transformer.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return rows.map (fun r => convertRow (convs.take 1) r)\n"
            "    -- impl-end"),
        "refinement": (
            "a counterpart that transformed only the first returning column and "
            "left the rest raw would keep a transform-bearing NON-first column a "
            "plain untransformed value; a multi-column returning set whose later "
            "column carries a value-transform would then read back a plain value "
            "where the tagged one is asserted — it would NOT resolve. Correct on "
            "every single-column input (a true partial-domain break, over the row "
            "WIDTH binder)."),
        "rationale": (
            "REJECT from `out = convertRows convs rows` via POSITIONAL LOCK-STEP: "
            "the spec applies transformer `p` to column `p` for EVERY p < len(convs), "
            "but truncating to the first transformer leaves column 1 raw where a "
            "non-identity transformer is defined. Verifying would be SPEC-TOO-WEAK "
            "(the later columns' transform unpinned). Refuted at a TWO-column row "
            "with a `+10`,`+1` chain — column 1 must become 6 (5+1) but the rival "
            "leaves it 5, and this is the only witness moving the row WIDTH and the "
            "transformer-chain length to 2. (Sibling: weak-row-first-col-only.)"),
        "witness": _witness("[[(5:Int), 5]]", "[fun x => x + 10, fun x => x + 1]"),
    },
    {
        "id": "weak-shift-transformer",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the head transformer of the chain, so every column is transformed by
        # the WRONG (shifted / truncated) transformer: column 0 gets convs[1],
        # column 1 gets nothing. The structure (a per-column transform) is present
        # but applied off-by-one. Wrong on every non-empty chain.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return rows.map (fun r => convertRow (convs.drop 1) r)\n"
            "    -- impl-end"),
        "refinement": (
            "a counterpart that dropped the head of each column's transformer "
            "chain would apply the wrong (shifted) transform to every column and "
            "leave the last column untransformed. For a single-transformer chain "
            "it drops the transform entirely; for longer chains it applies a "
            "misaligned one — the returned value is not what the field's transform "
            "produces, so the tagged-value assertion fails. It would NOT resolve. "
            "Distinguished from `weak-first-column-only`: that rival keeps column 0 "
            "correct and drops later columns; this one MISALIGNS column 0 itself, "
            "so it is refuted at an input where column 0's transformer differs from "
            "column 1's."),
        "rationale": (
            "REJECT from `out = convertRows convs rows` via POSITIONAL LOCK-STEP: "
            "the spec lands transformer `j` on column `j`, this rival lands "
            "transformer `j+1` on column `j` (and nothing on the last). Verifying "
            "would be SPEC-TOO-WEAK (the transformer alignment unpinned). Refuted at "
            "a two-column row with a `+2`,`+3` chain: column 0 must become 9 (7+2) "
            "but the shifted rival gives 10 (7+3). This drives the transformer-slice "
            "sub-domain no other witness probes. (Sibling: "
            "weak-row-drop-head-converter.)"),
        "witness": _witness("[[(7:Int), 7]]", "[fun x => x + 2, fun x => x + 3]"),
    },
    {
        "id": "weak-drop-last-row",
        "kind": "uniqueness",
        "expect": "reject",
        # Transform every row correctly but emit one fewer row (drop the last).
        # Correct on the per-element transform for the rows it emits, but violates
        # the row-count clause (N). Cheap supporting case with a real refinement
        # (a bulk operation returns one result per input row).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (rows.dropLast).map (fun r => convertRow convs r)\n"
            "    -- impl-end"),
        "refinement": (
            "this returns one fewer transformed row than it received (drops the "
            "last). A bulk operation on a backend that returns rows assigns one "
            "result per input row; dropping the last row loses a result — a "
            "faithful counterpart that emitted len-1 rows would fail any scenario "
            "reading back the full set of created objects. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = convertRows convs rows` via the ROW COUNT (N): "
            "`convertRows` is length-preserving on the row list, but the rival "
            "emits len(rows)-1 rows. Verifying would be SPEC-TOO-WEAK (the row "
            "count unpinned). Refuted at a TWO-row input (each one column) — this "
            "is the only witness moving the row COUNT binder above one, so it is "
            "what demonstrates the spec's dependence on len(rows). (Sibling: "
            "weak-exec-drop-last-row.)"),
        "witness": _witness("[[(1:Int)], [(2:Int)]]", "[fun x => x + 1]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness) plus 1 AXIOM_TESTS case. Every one is
# accounted for below. The sibling models TWO functions over PURE sequence inputs
# (`PSeq`, carrying no heap permission): `apply_row` (per-row per-column fold) and
# `execute_returning` (per-row map), with the fold computed by verified `while`
# loops. This backend models the SAME behaviour in ONE method
# `transformedResultRows` whose spec is `out = convertRows convs rows` — the
# per-row map of the per-column transform. The two-function surface collapses to
# one modeled function (carrier narrowing), so the sibling's apply_row-level and
# execute-level attacks that share a defect merge into a single rival here.
#
#   sibling case                    -> here                         disposition
#   -----------------------------------------------------------------------
#   pos-control-apply-row-reshape   -> pos-control-loop-reshape      PORTED (extra
#                                                                    local, loop kept)
#   pos-control-exec-reshape        -> pos-control-direct-model      PORTED (the
#                                                                    two-fn reshape
#                                                                    collapses; the
#                                                                    second positive
#                                                                    is the direct
#                                                                    grounded model)
#   admiss-self-call                -> admiss-nondegenerate           RE-AIMED
#   weak-exec-raw-passthrough       -> weak-raw-passthrough           PORTED (merged)
#   weak-row-raw-passthrough        -> weak-raw-passthrough           MERGED into it
#   weak-row-first-col-only         -> weak-first-column-only         PORTED
#   weak-row-drop-head-converter    -> weak-shift-transformer         PORTED
#   weak-exec-drop-last-row         -> weak-drop-last-row             PORTED
#   AXIOM_TESTS[ax-apply-converters]-> (none)                        DROPPED (G-AX)
#
# 2 positives ported, 1 admissibility re-aimed, 5 uniqueness ported (two raw-
# passthrough attacks merged into one on the single-function carrier), 1 axiom
# case dropped (this gate ignores the axiom lane). No case was omitted for being
# hard to prove.
#
# MERGED (weak-row-raw-passthrough into weak-raw-passthrough): the sibling attacks
#   raw passthrough at BOTH the inner (apply_row, clause F) and outer
#   (execute_returning, clause Fjp) function. This backend models only the
#   combined `transformedResultRows`, so both defects are the SAME wrong impl here
#   (`return rows`) and are refuted by the same clause of the single ensures. A
#   second rival would be a duplicate at the same input for the same reason (the
#   porting map forbids sharing a witness across rivals unless they truly fail
#   identically — here they would, so they are one rival, not two).
#
# VACUOUS (frame/permission-mutation): the sibling's own docstring already records
#   this class as N/A — its inputs are immutable `PSeq` sequences carrying no heap
#   permission, so there is no half-permission input to overwrite. On this backend
#   the same holds a fortiori: `rows`/`convs` are immutable values, no `mut`
#   binder, no heap, no aliasing. No substitute fabricated.
#
# UNGROUNDED-ORACLE ECHO: N/A. The post-image is `convertRows convs rows`, a
#   fully-unfolded pure `def` over the method's own arguments (empty `axioms`
#   region). There is no answer-key to echo; the only "echo" (return the inputs)
#   is exactly `weak-raw-passthrough`, which the grounded model rightly rejects on
#   any non-identity transformer. The honest stand-in is the cheapest correct
#   positive (pos-control-direct-model) computing the model directly.
#
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (pts = 4 distinct input points):
#     rows  — COUNT: 1 row (raw-passthrough, first-column-only, shift-transformer),
#             2 rows (drop-last-row); WIDTH: 1 column (raw-passthrough,
#             drop-last-row), 2 columns (first-column-only, shift-transformer).
#             Both the length (drives N) and the per-column values (drive F) are
#             moved.
#     convs — LENGTH: 1 transformer (raw-passthrough, drop-last-row), 2
#             transformers (first-column-only, shift-transformer); which SLICE is
#             applied is moved by the rivals (full / take 1 / drop 1). Column 0's
#             transformer differs from column 1's in shift-transformer so the
#             misalignment is observable.
#   Every independent top-level behavior of the post-image is attacked: the
#   per-column transform F (raw-passthrough), positional lock-step
#   (first-column-only, shift-transformer), and the row count N (drop-last-row).
#
# AUDIT ADDENDA (independent re-derivation of the port; properties.py only, the
# frozen artifact untouched).
#
#   1. WITNESS FORM REPLACED — the load-bearing repair. Every reject witness was
#      stated as `transformedResultRowsTester … = false`, which does not
#      discriminate against a loop-carrying frozen impl: gold's `decide` is stuck
#      (`did not reduce to isTrue or isFalse`) for the refutation, for its exact
#      opposite, and for a trivially true claim alike, so its exit 1 attested to
#      nothing. All four now refute the method's Hoare TRIPLE instead; see
#      `_witness` for the measured exit codes, including the correct-loop-free-impl
#      control that confirms the new form tracks wrongness and not impl shape.
#
#   2. POSITIVE ADDED (pos-control-forward-loop) — the two ported positives are
#      both near-gold (one returns the model term; one is definitionally equal),
#      so neither re-proves the obligation for a different traversal. The added
#      forward-scan positive does.
#
#   3. SPEC-TOO-WEAK PROBE (attack D), 6 NEW wrong impls beyond the four rivals,
#      each aimed at an unattacked corner. NONE verified; each was rejected with a
#      genuine unsolved `out = convertRows convs rows` goal (exit 1):
#        row-truncated-to-convs-length, rows reversed, transformer chain doubled
#        (convs ++ convs), first row only, an extra empty row appended, and the
#        transform applied TWICE. So no spec hole was found in this direction; in
#        particular `convertRows` is not idempotent on the carrier, which the
#        double-apply probe confirms rather than assumes.
#
#   4. SPEC-TOO-STRONG PROBE (attack E), 3 NEW correct reshapes. All three
#      VERIFY (exit 0): `rows.map (convertRow convs)`, a `foldr` accumulation,
#      and the forward loop now shipped as a positive. No faithful correct impl
#      was found that the spec rejects.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the one deep model
# (`convertRows`) is an A-reference validated there (meta.json G-AX: pass), and
# this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
