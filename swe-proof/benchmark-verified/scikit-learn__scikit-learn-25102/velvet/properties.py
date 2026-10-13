"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25102 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct projectColumns`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single per-column sequence):

  projectColumns (cols : List (Int × Bool)) return (out : List Int)
    ensures out = selectMasked cols          -- THE load-bearing (and only) clause

with ``selectMasked`` a fully-unfolded front-recursive ``def`` in the ``pure``
region, built from the per-column contribution ``keptCol``:

  keptCol (p : Int × Bool)      = if p.2 then [p.1] else []
  selectMasked []               = []
  selectMasked (p :: ps)        = keptCol p ++ selectMasked ps

Each list element models one column of a 2D container: the ``Int`` first
component is that column's element-type identity (distinct dtypes ↔ distinct
codes, mapping.md §2) and the ``Bool`` second component is that column's
selection bit. So the single clause pins THREE independent sub-behaviours of the
column projection:

  * KEEP-SET: a column contributes to the output iff its selection bit is set
    (``keptCol`` emits ``[p.1]`` only when ``p.2``); a dropped column contributes
    nothing;
  * PER-COLUMN IDENTITY: a kept column carries its OWN element-type code ``p.1``
    unchanged — never a single coerced shared value (the homogenisation the
    issue describes, where per-column types collapse to one);
  * ORDER: contributions are concatenated in INPUT column order (front-recursive
    ``++``), so the retained codes appear in the same order as their columns.

``selectMasked`` is GROUNDED in the input (a total fold over ``cols``); the
``axioms`` region is empty (``selectMasked`` is a deep A-reference validated ==
the real container-level masked column projection by axiom_check.py, NOT a
consumed answer key), so there is no wrong echo to build and the
ungrounded-oracle probe is replaced by two honest positive controls. The sole
INPUT BINDER is ``cols``; its two per-column components (``.1`` type code,
``.2`` selection bit) and its length are each varied by the reject witnesses.

THE CARRIER IS FULLY TRANSPARENT. ``selectMasked`` / ``keptCol`` compute on
``Int``/``Bool`` literals, so a witness reaches the impl through Velvet's
extractor (``extract_program_for projectColumns`` gives ``projectColumnsExec
cols = NonDetT.run (projectColumns cols)``) and states ``projectColumnsExec c ≠
DivM.res (selectMasked c)`` at a concrete ``c`` — with ``decide`` closing the
residual literal (no opaque leaf, no carrier conditioning needed, so no witness
binds a hypothesis and there is no joint-satisfiability obligation). Each reject
rival is a straight-line loop-free CLOSED FORM whose extracted program DOES
reduce to a literal, so the witness ELABORATES against the rival (exit 0).

THE FROZEN SOLUTION CANNOT SERVE AS THE WITNESS'S REFUTATION SUBJECT, and the
distinction matters, so it is stated precisely rather than glossed. Its ``while``
loop elaborates to an ``forIn Lean.Loop.mk`` term for which no ``Decidable``
instance can be synthesised at all, so the gold-side build fails with

    error: failed to synthesize
      Decidable ¬(NonDetT.run do let r ← forIn Lean.Loop.mk ...)

BEFORE any claim is evaluated. That exit code carries NO information about the
claim: the FORGERY that drops the ``≠`` (i.e. asserts gold is CORRECT at that
input — the opposite of a refutation) fails with the same synthesis error, so
"gold failed" cannot be read as "gold satisfies the spec here". Measured, not
inferred: for all three reject cases the witness and its flipped-claim forgery
both exit 1 against the frozen solution with a byte-identical
``failed to synthesize Decidable`` head.

So every reject case carries an explicit ``witness_reference``: ``_WITNESS_REF``,
a loop-free ``foldr`` implementation of the SAME frozen spec that VERIFIES (the
gate re-checks both facts) and, being loop-free, DOES reduce in the kernel. There
the refutation is decided rather than blocked, and the exit code tracks the claim:
the witness fails (exit 1) with a SEMANTIC refutation naming the concrete input,
e.g.

    Tactic `decide` proved that the proposition
      ¬keptCol (1, true) ++ keptCol (2, true) = selectMasked [(1, true), (2, true)]
    is false

while the flipped-claim forgery ELABORATES (exit 0) against that same reference.
That pair — refutation fails, its negation succeeds — is what makes each
rejection attributable to the spec rather than to a carrier limit.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as a
    MANDATORY rival (an in-place store into a read-only input container held at
    half permission) because a store needs full permission. Lean and Velvet are
    referentially transparent: ``cols`` is an immutable value, this bundle
    declares NO ``mut`` binder over any input, and there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to build. Not fabricated (per the porting map: this class is vacuous on
    Lean/Velvet).
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. The nagini
    per-column homogenisation rival and the mask-subdomain force-keep rival
    re-express directly onto the PER-COLUMN-IDENTITY and KEEP-SET sub-behaviours;
    one rival is ADDED for the ORDER sub-behaviour.
  * POSITIONAL RE-INDEX — VACUOUS on this carrier. The nagini sibling attacks a
    second postcondition clause about the output keeping the input's own ROW
    labels. This bundle's carrier is per-COLUMN only (``List (Int × Bool)`` of
    dtype-codes + selection bits); the row index is explicitly OUT of the modeled
    behaviour (mapping.md §2: "the index ... unchanged by selection and not part
    of the modeled behavior"). There is no index clause to attack, so the rival
    has no counterpart. Not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. ``selectMasked`` is a total ``def`` over the
    method's own input; there is no answer key to echo. Replaced by the honest
    positive controls (the cheapest direct impl + a structurally different loop).

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; ``selectMasked``
is a deep A-reference validated == the real masked column projection by
axiom_check.py — that is G-AX's job, and this gate ignores ``AXIOM_TESTS``
regardless).
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25102"
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
# these keeps markers.same_spec True and the prove_correct projectColumns
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-column loop plus the
# final return). Reject rivals replace it with a loop-free closed form (so their
# extracted program reduces under decide); the direct positive control replaces
# it with `return selectMasked cols`.
_IMPL = (
    "    let mut result : List Int := []\n"
    "    let mut i := cols.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ cols.length\n"
    "      invariant result = selectMasked (cols.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := cols[i - 1]!\n"
    "      result := keptCol c ++ result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The per-column accumulation step (unfolds keptCol at its only use). The reorder
# positive control replaces `keptCol c` with its inline `if`-form.
_STEP = (
    "      let c := cols[i - 1]!\n"
    "      result := keptCol c ++ result\n"
    "      i := i - 1\n"
)

# The frozen prove_correct tactic body (the whole block, unique in the file and
# elided from the spec view). The direct positive control retunes it (the loop is
# gone, so `loom_solve` alone closes the residual goal); the reorder positive
# control adds one `keptCol` unfold; every reject rival keeps it as-is (it fails
# to close the wrong impl, which is exactly the intended rejection, but the
# witness — not the tactic failure — is what the gate scores).
_PROOF = (
    "prove_correct projectColumns by\n"
    "  loom_solve\n"
    "  rw [selectMasked_drop_step cols i (by omega) (by omega)]\n"
    "  simp_all\n"
)


def _rival(expr: str) -> str:
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`."""
    return _swap(_BASE, _IMPL, f"    return ({expr})\n")


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `projectColumnsExec c` is `NonDetT.run (projectColumns c)`;
# ---- `≠ DivM.res (selectMasked c)` says the impl's output contradicts the
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. The loop-free rival reduces under `decide`; gold's loop stays
# ---- stuck, so the same witness fails on gold — the required discrimination.
_EXTRACT = "extract_program_for projectColumns\n\n"


def _witness(inp: str) -> str:
    return _EXTRACT + (
        "example : projectColumnsExec " + inp + " ≠ "
        "DivM.res (selectMasked " + inp + ") := by\n"
        "  unfold projectColumnsExec projectColumns\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n"
    )


# ---------------------------------------------------------------------------
# WITNESS REFERENCE. The frozen `while` loop admits no `Decidable` instance, so a
# refutation built against it fails by failed SYNTHESIS rather than by being
# decided — the same error appears for the claim and for its negation, so gold's
# exit code discriminates nothing (see the module docstring; measured with real
# builds). Every reject case is therefore refuted against THIS impl instead: a
# loop-free `foldr` over the same input that shares the frozen spec byte-for-byte
# and VERIFIES (both re-checked by the gate before it is used as a subject).
# Because it is loop-free it reduces in the kernel, so `decide` reaches a verdict
# and the exit code tracks the claim.
#
# Sound for the same reason gold would have been: a witness says "the spec is
# violated at this input", and an impl the verifier ACCEPTS cannot violate its own
# spec, so a genuine witness must fail against it. The `foldr` fold is a
# structurally DIFFERENT shape from the frozen backward loop (it is not the frozen
# impl in disguise), and its proof discharges `out = selectMasked cols` through an
# induction that the front-recursive `selectMasked_cons` closes.
# ---------------------------------------------------------------------------
_WITNESS_REF = _swap(
    _swap(_BASE, _IMPL,
          "    return (cols.foldr (fun p acc => keptCol p ++ acc) [])\n"),
    _PROOF,
    "prove_correct projectColumns by\n"
    "  loom_solve\n"
    "  have h : ∀ ps : List (Int × Bool),\n"
    "      ps.foldr (fun p acc => keptCol p ++ acc) [] = selectMasked ps := by\n"
    "    intro ps\n"
    "    induction ps with\n"
    "    | nil => rfl\n"
    "    | cons p ps ih => simp [selectMasked_cons, ih]\n"
    "  simp [h]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `selectMasked cols` is GROUNDED in the argument (a
    # total fold), so `return selectMasked cols` is a correct fully-grounded
    # implementation, not an ungrounded-oracle echo — and it doubles as proof the
    # spec is not echo-vulnerable: any WRONG constant/echo fails `out =
    # selectMasked cols`. The loop is gone, so the frozen proof body's loop
    # reasoning is unneeded and the residual goal closes under `loom_solve` alone.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _rival("selectMasked cols"),
            _PROOF,
            "prove_correct projectColumns by\n  loom_solve\n"),
        "rationale": "the post-image `selectMasked cols` is GROUNDED in the input "
                     "(a total per-column fold, no opaque answer key), so `return "
                     "selectMasked cols` is the honest cheapest CORRECT impl. It "
                     "MUST verify — the clause is literally `out = selectMasked "
                     "cols` — else the single postcondition clause is "
                     "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable: "
                     "any wrong constant/echo would fail `out = selectMasked cols`.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that keeps the frozen backward loop and its invariants BYTE-IDENTICAL, only
    # reshaping the per-column accumulation step: the gold `keptCol c` is inlined
    # to its definitional `if c.2 then [c.1] else []` form. Semantically identical
    # (that IS the definition of keptCol), so every loop invariant and the `out =
    # selectMasked cols` obligation still discharge; the proof needs only one
    # extra `keptCol` unfold in its tactic body (the elided proof region — in
    # scope). A faithful correct reshape that could NOT verify would mean the
    # postcondition is over-fit to the exact syntactic FORM of the step =>
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-inline-keptcol",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _STEP,
                "      let c := cols[i - 1]!\n"
                "      result := (if c.2 then [c.1] else []) ++ result\n"
                "      i := i - 1\n"),
            _PROOF,
            "prove_correct projectColumns by\n"
            "  loom_solve\n"
            "  rw [selectMasked_drop_step cols i (by omega) (by omega)]\n"
            "  simp_all [keptCol]\n"),
        "rationale": "structurally different CORRECT reshape: the per-column step "
                     "`keptCol c` is inlined to its definitional `if c.2 then "
                     "[c.1] else []` form, keeping the backward loop and every "
                     "invariant byte-identical. `out = selectMasked cols` still "
                     "discharges (the proof adds one `keptCol` unfold in the elided "
                     "tactic body). A faithful reshape MUST verify, else the clause "
                     "is over-fit to the step's syntactic FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- PER-COLUMN IDENTITY clause: stamp every kept column with column 0's
    # ---- element-type code (the homogenisation the issue describes) ----
    {
        "id": "weak-homogenise-shared-type",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the RIGHT columns (filter on the selection bit) and the RIGHT count,
        # but map every retained column to column 0's element-type code — so all
        # kept columns collapse to one shared type.
        "module": _rival(
            "match cols with | [] => [] "
            "| c0 :: _ => (cols.filter (fun p => p.2)).map (fun _ => c0.1)"),
        "refinement": "stamping every retained column with column 0's element-type "
                      "code is exactly the pre-narrowing behaviour where the "
                      "projection coerces the container to one homogeneous element "
                      "type before selecting, so all kept columns emerge with a "
                      "single shared type. A faithful counterpart that homogenised "
                      "the retained columns would still collapse a heterogeneous "
                      "selection (e.g. the issue's mixed float precisions + a "
                      "categorical column) to one type, which the failing tests — "
                      "asserting each output column keeps its input element type — "
                      "require to be preserved, so it would NOT resolve.",
        "rationale": "REJECT from `out = selectMasked cols` (PER-COLUMN IDENTITY "
                     "half): `selectMasked` carries each kept column's OWN code "
                     "`p.1`; the rival plants column 0's code for all kept columns, "
                     "so they differ whenever two retained codes differ. Refuted at "
                     "`[(1, true), (2, true)]`: the rival returns `[1, 1]`, "
                     "`selectMasked` returns `[1, 2]`. Varies the `.1` component "
                     "across two kept columns.",
        "witness": _witness("[(1, true), (2, true)]"),
        # Refuted against the loop-free `foldr` reference, not gold: gold admits no
        # `Decidable` instance, so its build fails by failed synthesis for this
        # claim AND for its negation alike. Against the reference the witness fails
        # with the semantic `decide proved that ¬keptCol (1, true) ++ keptCol
        # (2, true) = selectMasked [(1, true), (2, true)] is false`, and the
        # flipped-claim forgery elaborates — so the exit code tracks the claim.
        "witness_reference": _WITNESS_REF,
    },

    # ---- KEEP-SET clause: force-keep the leading column regardless of its bit ----
    {
        "id": "weak-force-keep-col0",
        "kind": "uniqueness",
        "expect": "reject",
        # Always emit column 0's code, then project the rest correctly — so a
        # column whose selection bit is CLEAR is wrongly retained.
        "module": _rival(
            "match cols with | [] => [] "
            "| c0 :: cs => c0.1 :: selectMasked cs"),
        "refinement": "force-keeping the leading column regardless of its selection "
                      "bit retains a column the selector dropped, so the output "
                      "carries an extra leading column (with the wrong element type "
                      "and position). A faithful counterpart that ignored the "
                      "leading column's mask bit would emit a projection whose "
                      "column set does not match the selector's, which the failing "
                      "tests — checking the retained columns and their per-column "
                      "types — require to match, so it would NOT resolve.",
        "rationale": "REJECT from `out = selectMasked cols` (KEEP-SET half): "
                     "`keptCol` emits a column iff its bit `p.2` is set; the rival "
                     "includes column 0 even when its bit is clear, so the output "
                     "has an extra leading code on that sub-domain. Refuted at "
                     "`[(5, false), (6, true)]`: the rival returns `[5, 6]`, "
                     "`selectMasked` returns `[6]`. Varies the `.2` component to "
                     "`false` in the leading position (the one value the other "
                     "rivals never probe).",
        "witness": _witness("[(5, false), (6, true)]"),
        # See weak-homogenise-shared-type: refuted against the reducible `foldr`
        # reference because gold's loop blocks `Decidable` synthesis for any claim.
        "witness_reference": _WITNESS_REF,
    },

    # ---- ORDER clause: reverse the retained-column order ----
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Select the RIGHT columns with the RIGHT types, but emit them in reversed
        # column order — a positional re-ordering of the projection.
        "module": _rival("(selectMasked cols).reverse"),
        "refinement": "emitting the retained columns in reversed order keeps the "
                      "correct column set and per-column types but scrambles their "
                      "positions, so the projection's column order no longer "
                      "matches the input's. A faithful counterpart that reordered "
                      "the retained columns would produce an output whose columns "
                      "sit in the wrong positions, which the failing tests — "
                      "asserting the output columns line up, in order, with the "
                      "selected input columns — require to be preserved, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = selectMasked cols` (ORDER half): "
                     "`selectMasked` concatenates per-column contributions in "
                     "INPUT order; the rival reverses them, so they differ whenever "
                     "two or more distinct codes are retained. Refuted at "
                     "`[(7, true), (8, true), (9, true)]`: the rival returns "
                     "`[9, 8, 7]`, `selectMasked` returns `[7, 8, 9]`. Varies the "
                     "length to three and the `.1` codes so order is observable.",
        "witness": _witness("[(7, true), (8, true), (9, true)]"),
        # See weak-homogenise-shared-type: refuted against the reducible `foldr`
        # reference because gold's loop blocks `Decidable` synthesis for any claim.
        "witness_reference": _WITNESS_REF,
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG). This bundle declares no `require`, so
    # there is no precondition clause to admit — but the analogue on a TOTAL
    # carrier is not thereby vacuous: it is the obligation being UNSATISFIABLE at
    # an F2P-shaped input. `out = selectMasked cols` pins `out` to a single value
    # per input, so if `selectMasked` were mis-defined such that no reachable
    # output could equal it at an F2P-shaped `cols` (a mixed keep/drop frame with
    # distinct per-column type codes), the method would be unimplementable there
    # while the two positive controls — which discharge the clause SYMBOLICALLY,
    # never evaluating it at any point — still verified.
    #
    # So this case discharges the obligation at that CONCRETE input by EVALUATION,
    # as a `have` proved by `decide`, before closing the frozen obligation
    # verbatim: `selectMasked [(3,true), (5,false), (7,true)] = [3, 7]` — the
    # middle column dropped, the two retained codes distinct and in input order.
    # The kernel computes both sides and confirms a witness output exists at an
    # F2P-shaped point. The impl and every invariant stay BYTE-IDENTICAL to gold;
    # the added `have` lies inside the elided `prove_correct` tactic body.
    #
    # NOT decorative, and that was measured rather than assumed: the same case
    # with the `have` asserting the FALSE value `[3, 5, 7]` (the dropped column
    # wrongly retained) FAILS to build with `decide proved that ... is false`. So
    # the `have` is genuinely evaluated and a wrong post-image at this input would
    # be caught here.
    # =====================================================================
    {
        "id": "admissibility-f2p-shaped-frame",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct projectColumns by\n"
            "  have _f2p : selectMasked "
            "[((3 : Int), true), ((5 : Int), false), ((7 : Int), true)]\n"
            "      = [(3 : Int), (7 : Int)] := by decide\n"
            "  loom_solve\n"
            "  rw [selectMasked_drop_step cols i (by omega) (by omega)]\n"
            "  simp_all\n"),
        "rationale": "PRECOND-TOO-STRONG probe re-aimed for a TOTAL carrier: with "
                     "no `require` clause the analogue is the obligation being "
                     "unsatisfiable at an F2P-shaped input, so this case discharges "
                     "`out = selectMasked cols` at a concrete such input BY "
                     "EVALUATION — `selectMasked [(3,true),(5,false),(7,true)] = "
                     "[3, 7]` by `decide`, a mixed keep/drop frame whose two "
                     "retained codes are distinct and in input order — as a `have` "
                     "before closing the frozen obligation verbatim. The impl and "
                     "all invariants are byte-identical to gold. MUST verify: a "
                     "post-image no reachable output could meet at an F2P-shaped "
                     "point would leave the method unimplementable there while both "
                     "positive controls, which discharge the clause symbolically "
                     "without ever evaluating it, still verified. The `have` is "
                     "genuinely evaluated — asserting the false value `[3, 5, 7]` "
                     "instead makes the case FAIL to build.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 3 partial-domain rivals)
# plus a 2-case AXIOM lane. This velvet bundle models a NARROWER core than the
# nagini sibling: nagini's `select_columns` returns a whole `Frame` and its spec
# pins TWO clauses (per-column descriptors AND the row index); this backend's
# carrier is per-COLUMN only (`List (Int × Bool)` of dtype-codes + selection
# bits), so only the descriptor/projection clause has a counterpart. Carrier
# narrowing, not effort gaps.
#
#   sibling case                    -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder-and-reshape -> pos-control-inline-keptcol   PORTED
#   pos-control-cheapest-inline     -> pos-control-direct           PORTED
#   admissibility-f2p-shaped-frame  -> admissibility-f2p-shaped-... PORTED (re-aimed)
#   frame-mutation-write-descs      -> (none)                       VACUOUS
#   homogenise-shared-descriptor    -> weak-homogenise-shared-type  PORTED
#   mask-subdomain-force-keep-col0  -> weak-force-keep-col0         PORTED
#   positional-reindex-drop-labels  -> (none)                       VACUOUS
#   (no sibling)                    -> weak-reverse-order           ADDED
#   AXIOM_TESTS (2)                 -> (none)                       DROPPED (G-AX)
#
# 5 ported, 1 added, 2 vacuous, 2 dropped = 6 SPEC cases (2 soundness,
# 3 uniqueness, 1 admissibility).
#
# PORTED (2 positive controls): the sibling's branch-reorder/reshape port as an
#   inline of the per-column step `keptCol c` to its definitional `if`-form,
#   keeping every loop invariant byte-identical (the proof adds one `keptCol`
#   unfold in the elided tactic body). The sibling's cheapest control (`return`
#   the grounded fold) ports as `return selectMasked cols`; the loop is gone, so
#   its residual goal closes under `loom_solve` alone. Both verified to build.
# PORTED (2 partial-domain rivals): homogenise-shared-descriptor and
#   mask-subdomain-force-keep-col0 re-express DIRECTLY onto the PER-COLUMN
#   IDENTITY conjunct (each kept column keeps its own type code) and the KEEP-SET
#   conjunct (a column contributes iff its selection bit is set). Each refinement
#   argument carries over: a faithful counterpart with that defect still produces
#   a projection the narrowed matcher rejects (a homogenised type collapse; an
#   extra force-kept column), so it would NOT resolve the failing tests.
# ADDED (1): weak-reverse-order attacks the ORDER sub-behaviour (`selectMasked`
#   concatenates in input column order). The nagini sibling has no dedicated
#   order rival — its two prepatch-derived rivals attack the descriptor-value and
#   the index — but here the single `out = selectMasked cols` clause pins column
#   ORDER independently, so a rival that reverses the retained order is a real
#   spec-strength probe (and the only witness whose distinguishing feature is
#   position, at the length-three input).
# PORTED, RE-AIMED (admissibility-f2p-shaped-frame): the sibling self-calls on an
#   F2P-shaped input to prove its half-permission precondition admits it. This
#   bundle declares NO `require` clause, so there is no precondition clause to
#   admit — but that is NOT a reason to drop the lane, which is the one that
#   detects PRECOND-TOO-STRONG. The analogue on a TOTAL carrier is the obligation
#   being UNSATISFIABLE at an F2P-shaped input, and a positive that discharges the
#   obligation at that concrete input BY EVALUATION tests it directly. That is what
#   the case does: a `have selectMasked [(3,true),(5,false),(7,true)] = [3, 7] := by
#   decide` — a mixed keep/drop frame, two distinct retained codes, input order —
#   before closing the frozen obligation verbatim, with impl and invariants
#   byte-identical to gold. The earlier "satisfiable everywhere by construction, so
#   vacuous" reading was wrong in an auditable way: it rests on reading
#   `selectMasked`'s totality off its definition, which is exactly the symbolic
#   argument the two positive controls already make, and neither of them ever
#   EVALUATES the clause at any input. This case does, and the evaluation is
#   load-bearing: the same case asserting the false value `[3, 5, 7]` fails to
#   build with `decide proved that ... is false`.
# VACUOUS (frame-mutation-write-descs): the sibling carries this MANDATORY because
#   the input container is held at half permission and a rival can illegally store
#   into it. This backend is referentially transparent and declares no `mut`
#   binder over any input — `cols` is an immutable value with no heap footprint —
#   so there is no read-only input to overwrite and no substitute probe. Not
#   fabricated.
# VACUOUS (positional-reindex-drop-labels): the sibling attacks a SECOND
#   postcondition clause about the output keeping the input's own ROW labels. The
#   velvet carrier is per-COLUMN only; the row index is explicitly outside the
#   modeled behaviour (mapping.md §2), so there is no index clause to attack and
#   the rival has no counterpart. Not fabricated.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `selectMasked` == the real masked column projection); this
#   bundle consumes no axiom `ensures`, and the gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `cols : List (Int × Bool)`, and a single top-level clause,
#   `out = selectMasked cols`, with three independent sub-obligations (keep-set,
#   per-column identity, order). The three reject witnesses probe three DISTINCT
#   input points — `[(1,true),(2,true)]` (identity: two kept, distinct codes),
#   `[(5,false),(6,true)]` (keep-set: leading bit false), `[(7,true),(8,true),
#   (9,true)]` (order: three kept, distinct codes) — so both per-column
#   components are genuinely varied (`.1` takes distinct values across kept
#   columns; `.2` takes both `true` and `false`, including in the leading
#   position) and the length varies (2, 2, 3). Each sub-obligation is attacked by
#   exactly one rival. The two positive controls defend the whole obligation
#   symbolically; the admissibility case additionally pins it by EVALUATION at a
#   fourth, F2P-shaped point `[(3,true),(5,false),(7,true)]` (mixed keep/drop,
#   distinct retained codes) — the only case that computes the clause rather than
#   discharging it symbolically. No two rivals are refuted at the same input.
#   pts = 4 distinct input points (3 witnesses + the admissibility evaluation).
# WITNESS DISCRIMINATION. Each witness ELABORATES against its loop-free rival (the
#   extracted program reduces to a literal that provably differs from
#   `selectMasked` at the probed input) and is refuted against `_WITNESS_REF`, the
#   loop-free `foldr` impl of the same spec, NOT against the frozen solution. The
#   frozen `while` loop admits no `Decidable` instance for the extracted
#   proposition, so a gold-side build fails by failed SYNTHESIS before evaluating
#   anything: the witness and the FORGERY that drops its `≠` (asserting gold is
#   CORRECT there) fail with the same `failed to synthesize Decidable` head, so
#   gold's exit code carries no information about the claim. Against the reference
#   the claim IS decided — the witness fails with a semantic `decide proved that
#   ¬... is false` naming the concrete input, and the flipped-claim forgery
#   ELABORATES — so the exit code tracks the claim, which is what makes the
#   rejection attributable to the spec. No witness binds a hypothesis (the carrier
#   is fully transparent), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
# DIVERGENCE / NON-TERMINATION lane: VACUOUS on this bundle, and demonstrated
#   rather than asserted. The frozen solution sets
#   `loom.semantics.termination "total"`, so a rival whose loop carries no
#   decreasing measure IS genuinely rejected and the class would be shippable —
#   except that on this carrier no such rival is a well-formed VARIANT. Dropping
#   the `decreasing i` annotation does not produce an impl the verifier merely
#   refuses to prove: the frontend rejects the FILE with `Decreasing annotations
#   are required in total correctness semantics` and elaborates the loop body to
#   `sorry`, which `variant_scope` bans as a new assumption token. The witness
#   file inherits that same `sorry`, so the rival build cannot be the clean exit-0
#   half the gate requires (measured: the witness against such a rival exits 1 with
#   the annotation error, and `decide` reports "does nothing"). The other route —
#   keeping `decreasing i` but never decreasing `i` in the body — is rejected for
#   the ORDINARY reason (the measure obligation, or `out = selectMasked cols`,
#   fails), which is not a divergence probe at all: it duplicates the value lane.
#   So the class is genuinely inexpressible here, not a known hole in the spec.
AXIOM_TESTS = []
