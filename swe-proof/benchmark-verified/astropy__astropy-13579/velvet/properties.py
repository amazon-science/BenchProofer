"""properties.py — G-PBT falsification battery for astropy__astropy-13579 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct assembleWorldVector`` obligation survives with a byte-
identical header) and swaps in a candidate implementation; it is checked by the
real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the discrimination subject. On this bundle that subject is NOT the frozen
solution but a named ``witness_reference`` — see THE DISCRIMINATION REFERENCE
below; the frozen ``while`` loop cannot decide these claims at all, so its
failure would attest to the loop's syntax rather than to the spec.

DEFENDED SURFACE. One contracted method that assembles a full-dimensional
coordinate vector from a sequence of per-axis descriptors and a stream of
caller-supplied values:

  assembleWorldVector (axes : List Axis) (supplied : List Float)
      return (out : List Float)
    require (axes.filter (·.1)).length = supplied.length
    ensures out = scatter axes supplied                                   (C1)

where ``Axis = Bool × Float`` — each descriptor pairs a PRESENT flag (``.1``,
whether the axis survives in the lower-dimensional view) with that axis's
REFERENCE COORDINATE (``.2``, the value the axis takes at the chosen reference
position). ``scatter``/``scatterStep`` are fully transparent front-recursive
``def``s over the two inputs (NOT opaque oracles; the ``axioms`` region is
empty). Threading the supplied values as a stream, ``scatter`` emits, per axis in
order:

  * a PRESENT axis (``a.1 = true``) emits the NEXT supplied value and CONSUMES it
    (``acc.2.headD 0`` then ``acc.2.tail``);
  * an ABSENT axis (``a.1 = false``) emits that axis's OWN reference coordinate
    ``a.2`` and consumes nothing.

The single top-level clause C1 pins several independently-attackable facets at
once: (a) the ABSENT-axis fill is the axis's reference coordinate ``a.2`` — this
is the load-bearing facet the fix restores (the pre-change assembly filled every
absent axis with a fixed placeholder constant regardless of the axis); (b) the
PRESENT-axis value is the next supplied value, not the reference coordinate; (c)
the supplied stream is CONSUMED left-to-right by present axes only, so ordering
and cursor advance are exact; (d) one output entry per axis, so ``out`` has the
same length as ``axes``. Both input binders are load-bearing: ``axes`` supplies
the present/absent flag (``.1``), the reference coordinate (``.2``) and the
length/order of the result; ``supplied`` supplies the per-present-axis values in
order.

CARRIER NOTE — WHY THE TESTER + ``decide`` ROUTE IS DEAD, AND WHAT REPLACES IT.
The carrier is ``List Float`` and the discriminating facet (a) is a VALUE
distinction between two ``Float``s (the reference coordinate vs a placeholder
constant). ``Float`` has no ``DecidableEq`` instance (IEEE-754 equality is not
propositional equality), so ``prove_postcondition_decidable_for
assembleWorldVector`` cannot be discharged, ``assembleWorldVectorTester`` cannot
be derived, and the ``…Tester args = false := by decide`` route used on
decidable carriers is UNAVAILABLE here. No ``Float`` literal is kernel-decidable
either (``some 1.0 ≠ some v`` is not a ``decide``-able proposition).

Instead each reject witness ``extract_program_for``s the rival (extraction needs
no decidability — it just names ``assembleWorldVectorExec``) and states, at a
concrete input, that the rival's RESULT differs from the transparent model
``scatter``:

    assembleWorldVectorExec axes supplied ≠ DivM.res (scatter axes supplied)

The refutation is CONDITIONED ON THE CARRIER: because no ``Float`` literal
decides the value facet, the witness QUANTIFIES over the reference coordinate /
supplied value as a free ``Float`` ``v`` (and a separation hypothesis such as
``v ≠ 1.0``, or ``s ≠ w``, at the point where the rival's fill diverges from
gold's), reduces the extracted ``…Exec`` by unfolding + ``simp only
[NonDetT.run, List.foldl]``, and closes on the residual ``Float`` inequality.
Read the claim it makes: *whenever the axis's reference coordinate differs from
the placeholder, the rival's output differs from the spec's* — the exact
sub-domain where the rival is wrong, a stronger statement than any single
literal input could make. Rivals that break a STRUCTURAL facet (length, cursor
advance) close via ``congrArg List.length`` or a decidable ``0 = s`` residual —
no ``Float`` fact needed there.

WHY GOLD IS NOT THE DISCRIMINATION SUBJECT (measured, not argued). The frozen
impl is a ``while`` loop whose extracted ``…Exec`` does NOT reduce under this
script: the term stays an un-normalised ``forIn``/``invariantGadget``
application and Lean reports ``Application type mismatch: … has type (NonDetT.run
do let r ← forIn Lean.Loop.mk …) = DivM.res … but is expected to have type
DivM.res ?m = DivM.res ?m in the application DivM.res.inj h``. That is a STUCK
REDUCTION — the claim was never evaluated, let alone refuted — so gold's exit 1
is a fact about the frozen loop's SYNTAX, and a merely RESHAPED correct rival
would break the same script identically. Refuting against gold would therefore
attest to a tactic mismatch, not to the spec.

So every reject case names a ``witness_reference``: a CORRECT impl in the rivals'
OWN straight-line ``foldl`` shape class, which the gate independently checks
shares the frozen spec AND VERIFIES before using it as the subject. Against it
the script reduces FULLY and the refutation COLLAPSES on the merits — the
residual becomes ``h2 : True`` (or an unprovable ``⊢ False``) — i.e. the claimed
disagreement is absent exactly when the impl is correct. Succeeding on the rival
while failing on a correct impl of the same shape is what makes each witness key
on WRONGNESS rather than on the frozen loop's syntax.

Each conditioned witness's binders are JOINTLY SATISFIABLE (a fresh ``Float``
``v`` distinct from a constant, or two distinct supplied/reference values, is the
F2P scenario itself — the coupled WCS's dropped spectral coordinate is ~1.05e-10,
not the placeholder 1), so the gate's consistency probe cannot derive ``False``
from them. Each witness was built every required way with
``scripts/lean_verify.sh``, exit codes observed: rival build elaborates (exit 0),
build against the verifying ``witness_reference`` fails by COLLAPSE (exit 1,
residual ``h2 : True`` / ``⊢ False``), consistency probe against that same subject
fails to derive ``False`` (exit 1). The reference itself verifies (exit 0); note
a bare ``loom_solve`` does NOT close it (it leaves ``(List.foldl scatterStep ([],
supplied) axes).1 = scatter axes supplied``), so it carries ``simp_all
[scatter]``. Gold-side builds also fail (exit 1) but by stuck reduction, which is
why they are not what the discrimination rests on. No banned token
(sorry/admit/native_decide/axiom/opaque).

ADVERSARIAL READ of the nagini sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally-different but
    correct impls must verify, else the spec is over-fit to the impl shape
    (SPEC-TOO-STRONG): return the grounded model ``scatter axes supplied`` with no
    loop; build the accumulator by PREPENDING and reversing at the end (gold
    appends); and negate the present-flag guard with both branches swapped. Each
    one is a real reshape: the direct-model form drops the loop entirely and
    reproves with a bare ``loom_solve``; the prepend form restates the framing
    invariant over ``acc.reverse``; the reordered form negates the guard, and its
    retune is LOAD-BEARING — measured, that impl under the FROZEN tactic script
    fails with ``unsolved goals case «invariant_2: result = …»`` (exit 1), and
    ``Bool.not_eq_true'`` plus a case split on the flag is what closes it. (The
    prepend form's ``List.reverse_cons`` argument is belt-and-braces rather than
    load-bearing: measured, that impl also verifies under the frozen script
    unchanged, exit 0. It still earns its place — ``v :: acc`` and ``result ++
    [v]`` are not definitionally equal and the invariant genuinely changes shape.)
    None of the three is a definitional twin of the frozen impl — a positive whose
    impl differs only by a spelling the elaborator erases would pass honestly
    while testing nothing.
  * ADMISSIBILITY — APPLIES (this bundle HAS a ``require`` clause). The sibling's
    admissibility control asserts a normal F2P-shaped input satisfies the
    assembly precondition. Here the analogue discharges an in-region ``assert``
    that a concrete two-axis input satisfies ``require`` (one present axis, one
    supplied value) AND that the modeled post-image is non-degenerate (its length
    is 2, so the selection genuinely varies), keeping the method's own obligation.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's MANDATORY frame
    rivals write through inputs held at ``Acc(list_pred(.), 1/2)`` (append to
    ``supplied`` / ``kept``) to trip INSUFFICIENT PERMISSION. Lean and Velvet are
    referentially transparent: ``axes`` and ``supplied`` are immutable values,
    this bundle declares NO ``mut`` binder for them (mapping.md §2, Solution.lean
    docstring: "read-only, not ``mut``"), and there is no heap, no aliasing, and
    no permission system. There is no read-only input to overwrite and no
    substitute probe to fabricate, so the class is vacuous — not fabricated (per
    the porting map, this class is vacuous on a referentially-transparent
    backend). Its ARGUMENT (mutating the shared input mid-loop corrupts later
    reads) has no value footprint the spec can force: ``out`` is a fresh list
    (``out = scatter axes supplied``).
  * DIVERGENCE / NON-TERMINATION: closed BY THE VERIFIER, not vacuous. This
    bullet's earlier "genuinely VACUOUS / a diverging impl cannot even be written
    in the modeled core" is withdrawn: a rival rewrites the whole impl region, so
    it can splice a diverging loop, and the frozen body itself is a ``while`` with
    a ``decreasing axes.length - i`` clause. What refuses the rival is the descent
    obligation. This bundle sets ``loom.semantics.termination "total"``, under
    which a postcondition is claimed of ALL runs, not only terminating ones, so
    the verifier demands a decreasing measure on every loop AND discharges its
    descent. The setting cannot drift from the file's
    ``open TotalCorrectness DemonicChoice``, because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with each proof
    reduced to a bare ``loom_solve``: a spliced loop with NO measure is refused at
    the ``method`` declaration
    (``Decreasing annotations are required in total correctness semantics``), and
    the sharper shape that CARRIES a measure which does not decrease
    (``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z``, body
    ``z := z + 1``) is refused on the measure's own goal:
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. (The nagini sibling
    carries no diverge-*/nonterm-*/weak-diverge case regardless, so there is
    nothing to port.)
  * UNGROUNDED-ORACLE ECHO — N/A as an unpinnable hole, but the sibling's
    value-level ``mask`` rivals (feed the WRONG vector to the downstream oracle)
    are re-expressed here directly as C1 value breaks: the downstream inverse
    transform is UNCHANGED and downstream of the assembly, so the spec stops at
    the assembled vector (mapping.md §3.2), and a rival that assembles the wrong
    vector is refuted by C1 itself (weak-present-echoes-ref covers the "fill with
    the wrong per-axis value" mask).
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: rivals right on part of the
    domain but wrong on the absent-axis fill (constant 1.0, constant 0.0, or the
    supplied value), on the present-axis value (echo the reference coordinate), on
    the cursor advance (absent axes also consume), or on the result length (drop
    absent axes).

AXIOM lane: EMPTY. mapping.md §3 records this bundle has NO axiom and NO
A-reference — the changed op (the absent-axis fill) is modeled DEEPLY by
``scatterStep``'s ``else a.2`` branch over read-only inputs, and both callees the
surrounding code touches are UNCHANGED (the reference-coordinate producer supplies
``a.2`` as a read-only input; the downstream inverse transform consumes the
assembled vector and is out of the modeled scope). ``AXIOM_TESTS = []``; the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13579"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean; both
# ---- facts asserted at load by _swap / the asserts below. Every variant
# ---- replaces text strictly inside the impl region (or the elided proof body),
# ---- so same_spec holds by construction and the `prove_correct
# ---- assembleWorldVector` obligation survives with a byte-identical statement.

# The ENTIRE frozen loop body (used for whole-body reject rivals and the
# straight-line positive control).
_IMPL_BODY = """    let mut result : List Float := []
    let mut remaining : List Float := supplied
    let mut i := 0
    while i < axes.length
      invariant i ≤ axes.length
      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1
      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2
      done_with i = axes.length
      decreasing axes.length - i
    do
      let a := axes[i]!
      let v : Float := if a.1 then remaining.headD 0 else a.2
      result := result ++ [v]
      remaining := if a.1 then remaining.tail else remaining
      i := i + 1
    return result"""
assert _BASE.count(_IMPL_BODY) == 1, "frozen impl body drifted; re-sync _IMPL_BODY"

# The first line of the impl body — for prepending the admissibility assert.
_IMPL_HEAD = "    -- impl-start\n    let mut result : List Float := []"
assert _BASE.count(_IMPL_HEAD) == 1, "impl-head anchor drifted"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward/forward-fold loop. A positive control that reshapes the impl away
# ---- from that loop retunes the tactic body; both the impl region and the
# ---- `prove_correct` body are elided from the spec view, so same_spec holds and
# ---- the obligation header survives. Unique in the file.
_PROOF = """prove_correct assembleWorldVector by
  loom_solve
  all_goals
    first
      | (rw [scatter_fold_step axes supplied i (by omega)]; simp_all [scatterStep])
      | simp_all [scatter, List.take_length]"""
assert _BASE.count(_PROOF) == 1, "frozen proof body drifted; update _PROOF"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a definitional
# residual that closes without the loop-body fold-step lemma; retune to the bare
# tactic.
_PROOF_STRAIGHT = "prove_correct assembleWorldVector by\n  loom_solve"

# ---- THE DISCRIMINATION REFERENCE (`witness_reference` on every reject case).
#
# Why this exists, measured rather than argued. Each reject witness reduces the
# extracted `…Exec` by `unfold` + `simp only [NonDetT.run, List.foldl]`, which
# works on a straight-line impl and does NOT work on the frozen `while` loop:
# against gold the term stays an un-normalised `forIn`/`invariantGadget`
# application and Lean reports
#
#   error: Application type mismatch: the argument h has type
#     (NonDetT.run do let r ← forIn Lean.Loop.mk … ) = DivM.res …
#   but is expected to have type DivM.res ?m = DivM.res ?m
#   in the application DivM.res.inj h
#
# That is a STUCK REDUCTION — the claim was never evaluated, let alone refuted —
# so gold's exit 1 is a fact about the frozen loop's SYNTAX, and a merely
# RESHAPED correct rival would break the same script the same way. Gold is
# therefore not a usable second subject for this battery's witnesses, and a
# reject case that leaned on it would attest to a tactic mismatch rather than to
# the spec. (The gate's own stuck-reduction screen keys on `decide`'s "did not
# reduce to isTrue/isFalse"; this cell's stuck term surfaces as an application
# type mismatch instead, so it passes that screen unseen. Recorded here so the
# artifact does not depend on a screen that cannot see it.)
#
# The repair is the mechanism `pbt.py::_check_witness` provides: name a
# `witness_reference` — a DIFFERENT impl of the same frozen spec that the gate
# independently checks (a) shares the spec and (b) VERIFIES — and refute each
# witness against THAT instead. Sound for the reason the gate documents: an impl
# the verifier accepts cannot violate its own spec, so a genuine "the spec is
# violated at this input" claim must fail there.
#
# The reference below is chosen to be the STRONGEST available discriminator: it
# is a CORRECT impl in the rivals' OWN straight-line `foldl` shape class,
# differing from each rival only in being right. So the witness script reduces
# FULLY against it and the refutation COLLAPSES on the merits — the residual
# becomes `h2 : True` (or an unprovable `⊢ False`) — i.e. the claimed
# disagreement is absent exactly when the impl is correct. Succeeding on the
# rival while failing on a correct impl of the same shape is what makes each
# witness key on WRONGNESS rather than on the frozen loop's syntax.
#
# NOTE the proof: a bare `loom_solve` does NOT close this impl (it leaves
# `(List.foldl scatterStep ([], supplied) axes).1 = scatter axes supplied`
# unsolved — measured, exit 1). Unfolding `scatter` is what discharges it. The
# reference must actually verify or the gate rejects it as
# `witness-reference-invalid`, which is the point of having the gate check it
# instead of a docstring asserting it.
_REF_PROOF = ("prove_correct assembleWorldVector by\n"
              "  loom_solve\n"
              "  all_goals simp_all [scatter]")
_REF_FOLDL = _swap(
    _swap(_BASE, _IMPL_BODY,
          "    return (axes.foldl scatterStep (([] : List Float), supplied)).1"),
    _PROOF, _REF_PROOF)


def _reject(impl_body):
    """Full Solution.lean variant with ONLY the impl-region body replaced by a
    straight-line rival (frozen tactic script kept — expected NOT to verify)."""
    return _swap(_BASE, _IMPL_BODY, impl_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and the carrier is `Float` (no DecidableEq), so a witness reaches the
# ---- rival's post-image through program extraction (which needs no
# ---- decidability). Checked in a file whose `prove_correct` block is stripped,
# ---- so no tactic script can mask the verdict. No `axiom`/`sorry`/
# ---- `native_decide`.
def _witness(head, tail):
    return "extract_program_for assembleWorldVector\n\n" + head + tail


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on impl shape.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded model `scatter axes supplied` directly. `scatter` is a total
        # function of the two inputs (no opaque answer key), so this is a correct
        # impl, not an echo. The residual goal is definitional, closed by a bare
        # `loom_solve` (the loop-body fold-step lemma is no longer needed and is
        # dropped — the tactic body is elided from the spec view, so same_spec and
        # the obligation header are untouched).
        "module": _swap(
            _swap(_BASE, _IMPL_BODY, "    return scatter axes supplied"),
            _PROOF, _PROOF_STRAIGHT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`scatter axes supplied` directly (no loop at all — maximally "
            "different from the gold `while`). The ensures is literally "
            "`out = scatter axes supplied`, so it holds on the whole domain and a "
            "bare `loom_solve` discharges the definitional residual. If this "
            "failed the spec would be over-fit to the loop shape "
            "(SPEC-TOO-STRONG). Also the no-ungrounded-echo control: the model IS "
            "the real per-axis assembly work, so returning it is correct, not a "
            "cheat. (Sibling: pos-assemble-branch-reorder / pos-recovered-inline.)"),
    },
    {
        "id": "pos-prepend-reverse",
        "kind": "soundness",
        "expect": "verify",
        # A correct impl with a genuinely DIFFERENT accumulator shape: build the
        # result by PREPENDING each per-axis value onto an accumulator (gold
        # APPENDS) and reverse once at the end. This is not a definitional twin of
        # gold — `v :: acc` and `result ++ [v]` are different terms, so the framing
        # invariant has to be restated over `acc.reverse` and the loop-body goal is
        # discharged only with the extra `List.reverse_cons` rewrite. The value
        # facet (which value each axis emits) is untouched, so it must verify.
        "module": _swap(
            _swap(
                _BASE, _IMPL_BODY,
                "    let mut acc : List Float := []\n"
                "    let mut remaining : List Float := supplied\n"
                "    let mut i := 0\n"
                "    while i < axes.length\n"
                "      invariant i ≤ axes.length\n"
                "      invariant acc.reverse = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1\n"
                "      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2\n"
                "      done_with i = axes.length\n"
                "      decreasing axes.length - i\n"
                "    do\n"
                "      let a := axes[i]!\n"
                "      let v : Float := if a.1 then remaining.headD 0 else a.2\n"
                "      acc := v :: acc\n"
                "      remaining := if a.1 then remaining.tail else remaining\n"
                "      i := i + 1\n"
                "    return acc.reverse"),
            _PROOF,
            "prove_correct assembleWorldVector by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "      | (rw [scatter_fold_step axes supplied i (by omega)]; "
            "simp_all [scatterStep, List.reverse_cons])\n"
            "      | simp_all [scatter, List.take_length]"),
        "rationale": (
            "structurally-different CORRECT impl: the accumulator is built by "
            "PREPENDING (`v :: acc`) and reversed once at the end, where gold "
            "APPENDS (`result ++ [v]`). The two accumulator terms are NOT "
            "definitionally equal, so the framing invariant must be restated over "
            "`acc.reverse` and the loop-body goal needs an extra `List.reverse_cons` "
            "rewrite — a real reshape of the data flow, not a spelling change. The "
            "per-axis value selection is identical, so the impl is faithful and MUST "
            "verify; if it did not, the spec would be over-fit to the append-shaped "
            "accumulator => SPEC-TOO-STRONG. (Sibling: pos-assemble-branch-reorder, "
            "re-shaped to the accumulator facet.)"),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The sibling's pos-assemble-branch-reorder, ported literally: NEGATE the
        # present-flag guard and SWAP both branches (the value select AND the cursor
        # advance). Behaviourally identical to gold, but the guard is now `!a.1`, so
        # the frozen tactic script no longer closes the loop-body invariant and the
        # proof must be retuned (`Bool.not_eq_true'` + a case split on the flag).
        # That retune is the point: it demonstrates the spec accepts the reordered
        # branch shape rather than only the frozen polarity.
        "module": _swap(
            _swap(
                _BASE, _IMPL_BODY,
                "    let mut result : List Float := []\n"
                "    let mut remaining : List Float := supplied\n"
                "    let mut i := 0\n"
                "    while i < axes.length\n"
                "      invariant i ≤ axes.length\n"
                "      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1\n"
                "      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2\n"
                "      done_with i = axes.length\n"
                "      decreasing axes.length - i\n"
                "    do\n"
                "      let a := axes[i]!\n"
                "      let v : Float := if !a.1 then a.2 else remaining.headD 0\n"
                "      result := result ++ [v]\n"
                "      remaining := if !a.1 then remaining else remaining.tail\n"
                "      i := i + 1\n"
                "    return result"),
            _PROOF,
            "prove_correct assembleWorldVector by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "      | (rw [scatter_fold_step axes supplied i (by omega)]\n"
            "         simp_all [scatterStep, Bool.not_eq_true']\n"
            "         split <;> simp_all [scatterStep])\n"
            "      | (rw [scatter_fold_step axes supplied i (by omega)]\n"
            "         cases h : (axes[i]!).1 <;> simp_all [scatterStep])\n"
            "      | simp_all [scatter, List.take_length]"),
        "rationale": (
            "the sibling's branch-reorder positive, ported literally: the "
            "present-flag guard is NEGATED and both branches SWAPPED (value select "
            "and cursor advance together), so absent axes are handled in the `then` "
            "arm. Behaviour is unchanged, but the guard polarity is not the frozen "
            "one, so the frozen tactic script no longer discharges the loop-body "
            "invariant and the proof is retuned with `Bool.not_eq_true'` plus a case "
            "split on the flag. It MUST verify: the spec constrains WHICH value each "
            "axis emits, not which polarity the impl tests the flag at; if the "
            "reordered form could not be proven the spec would be over-fit to the "
            "frozen branch order => SPEC-TOO-STRONG. (Sibling: "
            "pos-assemble-branch-reorder, ported not re-shaped.)"),
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). This bundle HAS a `require` clause
    # (`(axes.filter (·.1)).length = supplied.length`), so the sibling's "a normal
    # F2P-shaped input satisfies the precondition" probe has a real counterpart.
    # This case discharges an in-region `assert` that a concrete two-axis input
    # (one absent axis with reference coordinate 2.0, one present axis; one
    # supplied value 5.0) satisfies `require` AND that C1's post-image AT THAT
    # INPUT is the concrete vector `[2.0, 5.0]` — i.e. the obligation is
    # SATISFIABLE, by evaluation, at exactly an F2P-shaped input. If the
    # precondition could not be established for a legitimate input, or C1 were
    # unsatisfiable there, the assert would leave an unsolved goal
    # (PRECOND-TOO-STRONG / degenerate spec). The frozen loop and obligation are
    # kept verbatim so C1 still discharges; the assert is discharged as an extra
    # `all_goals` branch (the frozen proof body is elided from the spec view).
    #
    # AUDIT NOTE — why the second conjunct states a VALUE and not a length. The
    # earlier form asserted only `(scatter ..).length = 2` and its rationale
    # claimed that showed C1 "constrains the result rather than admitting a
    # constant". Measured, that claim was false: the length-2 conjunct is equally
    # true of the placeholder-fill model (a `scatterStep` whose absent branch
    # emits `1.0` gives `[1.0, 5.0]`, also length 2 — built, exit 0), so it
    # discriminated nothing about the fill facet the fix restores. The value form
    # is sensitive to exactly that facet: `[2.0, 5.0]` is provable of `scatter`
    # (`by rfl`, exit 0) and FALSE of the placeholder-fill model, whose image is
    # `[1.0, 5.0]`. So the assert now pins the reference-coordinate fill at a
    # concrete admissible input instead of restating its arity.
    # =====================================================================
    {
        "id": "admiss-precond-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_HEAD,
                "    -- impl-start\n"
                "    assert (with_name_prefix `adm\n"
                "      (([((false, (2.0:Float)) : Axis), ((true, (0.0:Float)) : Axis)].filter (·.1)).length = 1 ∧\n"
                "       scatter [((false, (2.0:Float)) : Axis), ((true, (0.0:Float)) : Axis)] [(5.0:Float)]\n"
                "         = [(2.0:Float), (5.0:Float)]))\n"
                "    let mut result : List Float := []"),
            _PROOF,
            "prove_correct assembleWorldVector by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "      | (rw [scatter_fold_step axes supplied i (by omega)]; simp_all [scatterStep])\n"
            "      | exact ⟨by decide, by rfl⟩\n"
            "      | simp_all [scatter, List.take_length]"),
        "rationale": (
            "the assembly precondition `(axes.filter (·.1)).length = "
            "supplied.length` is satisfiable by a normal input (one present axis, "
            "one supplied value; filter-present length 1 = supplied length 1), AND "
            "C1's obligation is satisfiable at that same concrete F2P-shaped input "
            "by evaluation: `scatter [(false, 2.0), (true, 0.0)] [5.0]` reduces to "
            "`[2.0, 5.0]` — the absent axis carries its OWN reference coordinate "
            "2.0 and the present axis the supplied 5.0. Both conjuncts must "
            "discharge (else PRECOND-TOO-STRONG, or C1 unsatisfiable at an "
            "admissible input). The value conjunct is what makes this "
            "discriminating rather than arithmetical: it is FALSE of the "
            "placeholder-fill model, which yields `[1.0, 5.0]` at this input, "
            "whereas a mere length claim holds of that model too. The frozen loop "
            "and obligation are kept verbatim so C1 still discharges. "
            "(Sibling: admiss-recovered-precond.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a straight-line impl carrying a machine-checked
    # refutation witness at a DISTINCT input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test
    # `test_coupled_world_slicing`. See the CARRIER NOTE for the witness method.
    # =====================================================================
    {
        "id": "weak-absent-constant-1",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: an absent axis is filled with the fixed placeholder
        # constant 1.0 instead of that axis's own reference coordinate `a.2`.
        # Correct on every present axis; wrong on the absent sub-domain whenever
        # the reference coordinate differs from 1.
        "module": _reject(
            "    return (axes.foldl (fun acc a => "
            "(acc.1 ++ [if a.1 then acc.2.headD 0 else 1.0], "
            "if a.1 then acc.2.tail else acc.2)) (([] : List Float), supplied)).1"),
        "refinement": (
            "this IS the pre-patch behaviour: a dropped/absent world axis filled "
            "with the fixed placeholder constant 1 instead of the reference "
            "coordinate that axis takes at the reference position. On the coupled "
            "issue configuration the dropped spectral coordinate is ~1.05e-10, not "
            "1, so the assembled vector is wrong, the downstream inverse transform "
            "recovers a spurious ~1.8e11 pixel instead of ~0, and "
            "test_coupled_world_slicing FAILS. It would NOT resolve (this is "
            "exactly the bug the change fixes). Correct on every present axis, so a "
            "true partial-domain break."),
        "rationale": (
            "REJECT from C1 facet (a) (the absent-axis fill): with an absent axis "
            "the spec emits its reference coordinate `a.2`, the rival emits the "
            "constant 1.0, so the two disagree whenever `a.2 ≠ 1.0`. If it "
            "verified => SPEC-TOO-WEAK (the discriminating fix unpinned). Refuted "
            "at `axes=[(false, v)]`, `supplied=[]`, conditioned on `v ≠ 1.0`: gold "
            "resolves `[v]`, the rival `[1.0]`. Abuses the reference-coordinate "
            "binder `.2` on the absent branch."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (v : Float) (hv : v ≠ 1.0) :\n"
            "    assembleWorldVectorExec [((false, v) : Axis)] []\n"
            "      ≠ DivM.res (scatter [((false, v) : Axis)] []) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := DivM.res.inj h\n"
            "  simp at h2\n"
            "  exact hv h2.symm\n"),
    },
    {
        "id": "weak-absent-constant-0",
        "kind": "uniqueness",
        "expect": "reject",
        # The boundary/other-constant variant: fill an absent axis with a DIFFERENT
        # fixed constant (0.0). Distinguishes the spec from "any fixed placeholder"
        # — a rival that happened to guess a constant other than 1 must also be
        # refuted. Wrong on the absent sub-domain whenever the reference
        # coordinate differs from 0.
        "module": _reject(
            "    return (axes.foldl (fun acc a => "
            "(acc.1 ++ [if a.1 then acc.2.headD 0 else 0.0], "
            "if a.1 then acc.2.tail else acc.2)) (([] : List Float), supplied)).1"),
        "refinement": (
            "a counterpart that filled absent axes with any fixed placeholder "
            "(here 0) rather than the axis's reference coordinate assembles the "
            "wrong vector on the coupled configuration — the dropped spectral "
            "coordinate is ~1.05e-10, not 0 — so the recovered pixel is wrong and "
            "test_coupled_world_slicing FAILS. It would NOT resolve."),
        "rationale": (
            "REJECT from C1 facet (a): with an absent axis the spec emits `a.2`, "
            "the rival emits the constant 0.0, so they disagree whenever "
            "`a.2 ≠ 0.0`. Pins the fill facet against a DIFFERENT constant than "
            "weak-absent-constant-1, so the spec is shown to reject the whole class "
            "of fixed-placeholder fills, not one literal. If it verified => "
            "SPEC-TOO-WEAK. Refuted at `axes=[(true, w), (false, v)]`, "
            "`supplied=[w]`, conditioned on `v ≠ 0.0`: gold resolves `[w, v]`, the "
            "rival `[w, 0.0]`. Deliberately probed at a DIFFERENT input point than "
            "weak-absent-constant-1 (present axis FIRST, absent axis SECOND, "
            "non-empty stream), so the two constant-fill rivals do not share a "
            "point: this one also exercises an absent axis reached after the cursor "
            "has already advanced."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (v w : Float) (hv : v ≠ 0.0) :\n"
            "    assembleWorldVectorExec [((true, w) : Axis), ((false, v) : Axis)] [w]\n"
            "      ≠ DivM.res (scatter [((true, w) : Axis), ((false, v) : Axis)] [w]) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := DivM.res.inj h\n"
            "  simp at h2\n"
            "  exact hv h2.symm\n"),
    },
    {
        "id": "weak-absent-uses-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # A subtler wrong fill: an absent axis takes the NEXT supplied value
        # (`acc.2.headD 0`) instead of its reference coordinate. Indistinguishable
        # from gold on a present axis, wrong on an absent one whenever the
        # reference coordinate differs from the head of the supplied stream. (The
        # value-carrier analogue of the sibling's partial-dropped-uses-supplied.)
        "module": _reject(
            "    return (axes.foldl (fun acc a => "
            "(acc.1 ++ [if a.1 then acc.2.headD 0 else acc.2.headD 0], "
            "if a.1 then acc.2.tail else acc.2)) (([] : List Float), supplied)).1"),
        "refinement": (
            "filling an absent axis with a caller-supplied per-axis value (rather "
            "than the axis's reference coordinate) feeds the wrong scalar into the "
            "downstream inverse; on the coupled configuration the recovered pixel "
            "is not ~0, so test_coupled_world_slicing FAILS. It would NOT resolve. "
            "Correct on every present axis and agrees with gold on the absent axis "
            "only when the supplied head happens to equal the reference coordinate "
            "— a genuine partial-domain break refuted at the distinguishing input."),
        "rationale": (
            "REJECT from C1 facet (a): on an absent axis the spec emits `a.2` but "
            "the rival emits the head of the supplied stream, which is not provably "
            "`a.2`. If it verified => SPEC-TOO-WEAK (the absent fill unpinned "
            "against the supplied stream). Refuted at "
            "`axes=[(false, v), (true, w)]`, `supplied=[w]`, conditioned on "
            "`v ≠ w`: gold resolves `[v, w]`, the rival `[w, w]`. Varies `supplied` "
            "to a non-empty stream and exercises both an absent and a present axis."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (v w : Float) (hv : v ≠ w) :\n"
            "    assembleWorldVectorExec [((false, v) : Axis), ((true, w) : Axis)] [w]\n"
            "      ≠ DivM.res (scatter [((false, v) : Axis), ((true, w) : Axis)] [w]) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := DivM.res.inj h\n"
            "  simp only [List.headD, List.cons_append, List.nil_append, List.cons.injEq] at h2\n"
            "  exact hv h2.1.symm\n"),
    },
    {
        "id": "weak-present-echoes-ref",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror error on the PRESENT branch (and the value-carrier
        # re-expression of the sibling's mask/ungrounded-echo rival): fill EVERY
        # axis with its reference coordinate `a.2`, ignoring the supplied stream
        # entirely. Correct on absent axes; wrong on a present axis whenever the
        # supplied value differs from the axis's reference coordinate.
        "module": _reject(
            "    return (axes.foldl (fun acc a => "
            "(acc.1 ++ [a.2], if a.1 then acc.2.tail else acc.2)) "
            "(([] : List Float), supplied)).1"),
        "refinement": (
            "a counterpart that filled every axis — including present ones — with "
            "its reference coordinate ignores the caller-supplied values on the "
            "kept axes, so the assembled vector carries the reference position's "
            "coordinate where it should carry the queried value. On the failing "
            "scenario the kept spatial coordinates are the query, not the "
            "reference, so the recovered pixel is wrong and "
            "test_coupled_world_slicing FAILS. It would NOT resolve."),
        "rationale": (
            "REJECT from C1 facet (b) (the present-axis value): on a present axis "
            "the spec emits the next supplied value but the rival emits the "
            "reference coordinate `a.2`, so they disagree whenever the supplied "
            "value differs from `a.2`. This is the ONLY rival keying on a PRESENT "
            "axis's supplied value. If it verified => SPEC-TOO-WEAK (the "
            "present-branch value unpinned). Refuted at `axes=[(true, w)]`, "
            "`supplied=[s]`, conditioned on `s ≠ w`: gold resolves `[s]`, the "
            "rival `[w]`. Abuses the `supplied` binder on the present branch."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (w s : Float) (hv : s ≠ w) :\n"
            "    assembleWorldVectorExec [((true, w) : Axis)] [s]\n"
            "      ≠ DivM.res (scatter [((true, w) : Axis)] [s]) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := DivM.res.inj h\n"
            "  simp at h2\n"
            "  exact hv h2.symm\n"),
    },
    {
        "id": "weak-absent-also-consumes",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW / cursor break: absent axes ALSO advance the supplied
        # cursor (`acc.2.tail` unconditionally) instead of consuming nothing. The
        # per-slot fill is correct, but the stream is mis-consumed, so a present
        # axis after an absent one takes the wrong supplied value. Attacks facet
        # (c) (the supplied stream is consumed by present axes ONLY).
        "module": _reject(
            "    return (axes.foldl (fun acc a => "
            "(acc.1 ++ [if a.1 then acc.2.headD 0 else a.2], acc.2.tail)) "
            "(([] : List Float), supplied)).1"),
        "refinement": (
            "a counterpart that advanced the supplied cursor on every axis "
            "(including absent ones) mis-aligns the per-present-axis values: after "
            "an absent axis the stream is short by one, so the following present "
            "axis takes the wrong (or missing) supplied value. The assembled vector "
            "is wrong on the coupled configuration and test_coupled_world_slicing "
            "FAILS. It would NOT resolve. Correct when no present axis follows an "
            "absent one — a genuine partial-domain break in the traversal."),
        "rationale": (
            "REJECT from C1 facet (c) (cursor advance): a present axis following an "
            "absent one should take supplied[0] but the rival has already consumed "
            "it on the absent axis, so it takes supplied[1] (here the empty tail's "
            "`headD 0`). If it verified => SPEC-TOO-WEAK (the stream-consumption "
            "discipline unpinned). Refuted at `axes=[(false, v), (true, w)]`, "
            "`supplied=[s]`, conditioned on `s ≠ 0`: gold resolves `[v, s]`, the "
            "rival `[v, 0]`. The only rival attacking the cursor/ordering facet; "
            "the residual `0 = s` is decidable, so no Float DecidableEq is needed."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (v w s : Float) (hs : s ≠ 0) :\n"
            "    assembleWorldVectorExec [((false, v) : Axis), ((true, w) : Axis)] [s]\n"
            "      ≠ DivM.res (scatter [((false, v) : Axis), ((true, w) : Axis)] [s]) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := DivM.res.inj h\n"
            "  simp at h2\n"
            "  exact hs h2.symm\n"),
    },
    {
        "id": "weak-return-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (length): return the supplied stream unchanged, dropping
        # every absent axis. The output is one entry short per absent axis, so it
        # differs from the full-dimensional vector in LENGTH. Attacks facet (d)
        # (one output entry per axis). (Sibling: partial-first-slot-wrong /
        # return-supplied family.)
        "module": _reject("    return supplied"),
        "refinement": (
            "returning only the supplied (kept-axis) values drops the absent axes "
            "from the assembled vector entirely, so the downstream inverse "
            "transform receives a lower-dimensional vector than it expects — the "
            "recovered pixels are wrong (or the transform is mis-shaped) and "
            "test_coupled_world_slicing FAILS. It would NOT resolve. This omits the "
            "reconstructed absent coordinates the fix depends on."),
        "rationale": (
            "REJECT from C1 facet (d) (one entry per axis / length): "
            "`scatter axes supplied` has one entry per axis, but `supplied` has one "
            "per PRESENT axis, so `out` is short by the number of absent axes and "
            "the two differ in LENGTH whenever some axis is absent. If it verified "
            "=> SPEC-TOO-WEAK (the result length not pinned). Refuted at "
            "`axes=[(false, v), (true, w), (false, u)]`, `supplied=[w]`: gold "
            "resolves the length-3 list `[v, w, u]`, the rival the length-1 list "
            "`[w]` — discriminated by `List.length`, no per-entry Float fact "
            "needed, and the witness head binds no separation hypothesis at all "
            "(the length break is unconditional). The only rival attacking LENGTH."
            "\n"
            "RE-POINTED IN AUDIT. The earlier point was `axes=[(false, v), "
            "(false, w)]`, `supplied=[]`, and its rationale claimed that was `an "
            "input point no other rival uses`. Measured, that claim was FALSE: "
            "weak-absent-wrong-axis-ref probes the same all-absent length-2 pair, "
            "so up to renaming the two coincided and the battery's advertised "
            "SEVEN pairwise-distinct points were only six. The point above is a "
            "genuinely new one — the battery's only LENGTH-3 input and its only "
            "absent/present/absent interleaving, so the length deficit is now "
            "pinned where the stream is also non-empty and a present axis sits "
            "BETWEEN two absent ones (the earlier all-absent pair never advanced "
            "the cursor at all). Rebuilt every required way: the witness "
            "elaborates against the rival (exit 0), FAILS against the "
            "witness_reference by collapse (exit 1), and its consistency probe "
            "fails to derive False (exit 1). Forgery pair on the new point: the "
            "type-reveal build prints `h2 has type True` against the reference and "
            "`No goals to be solved` against the rival (simp already closed the "
            "length contradiction), and the flipped claim ELABORATES against the "
            "reference (exit 0) while failing against the rival (exit 1) on "
            "`pure [w] = DivM.res [v, w, u]` — so the subject-side exit code "
            "tracks the claim. The point lies inside `require` "
            "(filter-present length 1 = supplied length 1, `by simp`, exit 0)."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (u v w : Float) :\n"
            "    assembleWorldVectorExec"
            " [((false, v) : Axis), ((true, w) : Axis), ((false, u) : Axis)] [w]\n"
            "      ≠ DivM.res (scatter"
            " [((false, v) : Axis), ((true, w) : Axis), ((false, u) : Axis)] [w]) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := congrArg List.length (DivM.res.inj h)\n"
            "  simp at h2\n"),
    },
    {
        "id": "weak-absent-wrong-axis-ref",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED IN AUDIT. Every shipped absent-fill rival replaces `a.2` with
        # something that is not a reference coordinate at all (a fixed constant, or
        # the supplied head), so all of them are refuted by "the fill is not from
        # `axes`". None of them pins that the fill must come from THIS axis. This
        # rival fills every absent axis with the FIRST axis's reference coordinate
        # — a per-axis crosstalk bug that is correct on the first axis and on any
        # input whose absent axes happen to share a reference coordinate, and
        # therefore invisible to every existing witness point. Attacks facet (a) at
        # the axis-INDEXING granularity rather than at the value-source granularity.
        "module": _reject(
            "    return (axes.foldl (fun acc a => "
            "(acc.1 ++ [if a.1 then acc.2.headD 0 else "
            "(axes.headD ((false, (0.0:Float)) : Axis)).2], "
            "if a.1 then acc.2.tail else acc.2)) (([] : List Float), supplied)).1"),
        "refinement": (
            "a counterpart that reconstructed every absent axis from ONE axis's "
            "reference coordinate rather than each axis's own reads the right "
            "quantity from the wrong axis. With two or more absent axes carrying "
            "different reference coordinates, every absent entry after the first is "
            "wrong, so the assembled vector is wrong, the downstream inverse "
            "recovers the wrong pixel and test_coupled_world_slicing FAILS. It would "
            "NOT resolve. Correct whenever the absent axes' reference coordinates "
            "coincide (and on every present axis), so a genuine partial-domain "
            "break — and one no fixed-placeholder rival can express, since the fill "
            "IS a reference coordinate, just not the right axis's."),
        "rationale": (
            "REJECT from C1 facet (a) at the AXIS-INDEX granularity: the spec's "
            "`scatterStep` emits `a.2` — the coordinate of the axis being emitted — "
            "whereas the rival emits the head axis's `.2` for every absent axis, so "
            "the two disagree whenever two absent axes differ in reference "
            "coordinate. The three shipped absent-fill rivals all break the fill's "
            "SOURCE (a constant, or the supplied stream) and so are all refuted by "
            "`a.2 ≠ <not-a-reference-coordinate>`; this one keeps the source and "
            "breaks the INDEX, which none of them pins. If it verified => "
            "SPEC-TOO-WEAK (the per-axis association of coordinate to axis "
            "unpinned, while every existing witness still passed). Refuted at "
            "`axes=[(false, u), (false, v)]`, `supplied=[]`, conditioned on "
            "`v ≠ u`: gold resolves `[u, v]`, the rival `[u, u]`. A seventh distinct "
            "input point, and the only one binding TWO free reference coordinates "
            "separated from each other rather than from a literal."),
        "witness_reference": _REF_FOLDL,
        "witness": _witness(
            "example (u v : Float) (hv : v ≠ u) :\n"
            "    assembleWorldVectorExec [((false, u) : Axis), ((false, v) : Axis)] []\n"
            "      ≠ DivM.res (scatter [((false, u) : Axis), ((false, v) : Axis)] []) := by\n",
            "  unfold assembleWorldVectorExec assembleWorldVector scatter scatterStep\n"
            "  simp only [NonDetT.run, List.foldl]\n"
            "  intro h\n"
            "  have h2 := DivM.res.inj h\n"
            "  simp at h2\n"
            "  exact hv h2.symm\n"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The nagini sibling ships 10 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals — two of which are MANDATORY
# frame-mutation rivals) plus 2 AXIOM_TESTS. The sibling contracts TWO functions
# over three read-only `List[int]` inputs under fractional half-permissions and
# partial correctness: `assemble_inverse_world(kept, supplied, world_at_slice,
# world_n_dim)` (the per-slot value selection) and `recovered_pixel(...)` (feed
# the assembled vector to an opaque deterministic oracle `full_world_to_pixel`).
# This velvet bundle models ONLY the purely-functional core — the per-axis scatter
# `assembleWorldVector (axes, supplied)` over `List Axis`/`List Float`, with the
# per-slot selection modeled DEEPLY by `scatter`/`scatterStep` — and pins it with
# a single element-wise `ensures out = scatter axes supplied` under TOTAL
# termination semantics. The downstream oracle and its whole `recovered_pixel`
# face are OUT OF SCOPE here: the oracle is unchanged and downstream of the
# assembly (mapping.md §3.2), so the spec stops at the assembled vector — which is
# exactly the data the patch changes. That carrier narrowing collapses the two
# `recovered_pixel` cases and makes the frame class vacuous.
#
#   nagini case                     kind          -> here                        disposition
#   ------------------------------------------------------------------------------------------------
#   pos-assemble-branch-reorder     soundness     -> pos-branch-reorder          PORTED (literal)
#   (no sibling)                    soundness     -> pos-prepend-reverse         ADDED (accumulator reshape)
#   pos-recovered-inline            soundness     -> pos-direct-model            RE-AIMED (assembly face)
#   admiss-recovered-precond        admissibility -> admiss-precond-nondegenerate PORTED (assembly face)
#   frame-mutate-supplied (MAND)    uniqueness    -> (none)                      VACUOUS
#   frame-mutate-kept (MAND)        uniqueness    -> (none)                      VACUOUS
#   partial-dropped-constant1       uniqueness    -> weak-absent-constant-1      PORTED (the prepatch bug)
#   partial-dropped-uses-supplied   uniqueness    -> weak-absent-uses-supplied   PORTED
#   partial-first-slot-wrong        uniqueness    -> weak-return-supplied        RE-SHAPED (length break)
#   mask-recovered-wrong-vector     uniqueness    -> weak-present-echoes-ref     RE-AIMED (assembly face)
#   mask-recovered-constant-vector  uniqueness    -> weak-absent-constant-1      MERGED (same defect/witness)
#   (no sibling)                    uniqueness    -> weak-absent-constant-0      ADDED
#   (no sibling)                    uniqueness    -> weak-absent-also-consumes   ADDED
#   (no sibling)                    uniqueness    -> weak-absent-wrong-axis-ref   ADDED (in audit)
#   AXIOM_TESTS x2                  axiom         -> (none)                      N/A (G-AX lane)
#
# 11 SPEC cases here (3 soundness, 1 admissibility, 7 uniqueness): 4 rivals
# ported/re-shaped from the sibling, 3 added, 2 frame rivals vacuous; the
# positives and the admissibility case ported/re-aimed onto the assembly face; the
# two recovered_pixel mask rivals fold onto the assembly (one merged, one
# re-aimed).
#
# PORTED / ADDED / RE-AIMED (positives): the sibling's
#   pos-assemble-branch-reorder negates the guard and swaps branches; it is ported
#   LITERALLY here as pos-branch-reorder. Under the FROZEN tactic script that form
#   does leave an unsolved loop-body invariant goal (`invariant_2: result = ...`),
#   but that is a tactic-tuning fact about the frozen script, NOT a fact about the
#   spec: retuning the elided proof body with `Bool.not_eq_true'` and a case split
#   on the flag closes it, so the case is carried rather than dropped. A second
#   positive, pos-prepend-reverse, is ADDED to attack the accumulator shape (build
#   by prepending and reverse at the end, where gold appends), which forces the
#   framing invariant to be restated over `acc.reverse`; that is a real data-flow
#   reshape, where merely inlining the per-axis value into the append (the earlier
#   choice here) differed from gold only by a `let` the elaborator erases and so
#   would have certified nothing. The sibling's pos-recovered-inline (inline the
#   oracle call) has no recovered_pixel counterpart here, so it is re-aimed to
#   pos-direct-model: drop the loop and return the grounded model `scatter axes
#   supplied` directly — the maximally-different correct impl AND the
#   no-ungrounded-echo control.
# PORTED (rivals): partial-dropped-constant1 -> weak-absent-constant-1 (the
#   verbatim pre-patch bug: absent axis filled with the placeholder constant 1;
#   the F2P discriminator and G-DIFF prepatch shape). partial-dropped-uses-supplied
#   -> weak-absent-uses-supplied (absent axis takes the supplied stream head
#   instead of its reference coordinate). partial-first-slot-wrong -> re-shaped to
#   weak-return-supplied, which drops absent axes entirely and attacks the LENGTH
#   facet (a corner the first-slot rival's index-0 corruption also touches, but
#   length is the clean decidable discriminator on this carrier).
# RE-AIMED to the assembly face (recovered_pixel mask rivals): the sibling's
#   mask-recovered-wrong-vector feeds the supplied-everywhere vector to the opaque
#   oracle; here that same "fill with the wrong per-axis value" defect is a C1
#   value break on the ASSEMBLY (the oracle is out of scope), captured by
#   weak-present-echoes-ref (fill every axis with its reference coordinate,
#   ignoring the supplied stream on present axes). mask-recovered-constant-vector
#   (feed a constant-1-filled vector to the oracle) is the SAME defect as
#   weak-absent-constant-1 on the assembly face and would share its witness at the
#   same input for the same reason, so it is MERGED (per the porting rule: two
#   rivals share a witness only if they fail at the same input for the same
#   reason).
# ADDED: (1) weak-absent-constant-0 — a DIFFERENT placeholder constant, so the
#   spec is shown to reject the whole fixed-placeholder class, not one literal.
#   (2) weak-absent-also-consumes — the cursor/consumption facet (absent axes also
#   advance the supplied stream), which no sibling rival attacks and which the
#   `scatterStep` stream carrier makes cleanly expressible; refuted via a decidable
#   `0 = s` residual.
# VACUOUS (frame-mutate-supplied, frame-mutate-kept; both MANDATORY on nagini):
#   the sibling's frame rivals append to a read-only input held at
#   Acc(list_pred(.), 1/2) to trip INSUFFICIENT PERMISSION before the postcondition
#   is considered. This backend is referentially transparent: `axes` and
#   `supplied` are immutable values, this bundle declares NO `mut` binder for them
#   (Solution.lean docstring / mapping.md §2), and there is no heap, no aliasing,
#   and no permission system. DEMONSTRATED rather than asserted: a variant whose
#   impl region opens with `supplied := supplied ++ [(1.0:Float)]` does not
#   elaborate, Lean reporting "`supplied` cannot be mutated, only variables
#   declared using `let mut` can be mutated" — the rival cannot be WRITTEN, so
#   there is nothing for a witness to discriminate and no substitute probe to
#   build. The class is vacuous (per the porting map, legitimately dropped, not
#   fabricated). Its ARGUMENT (mutating the shared input
#   mid-loop corrupts later reads) has no value footprint the spec can force: `out`
#   is a fresh list (`out = scatter axes supplied`).
# DIVERGENCE / NON-TERMINATION: the nagini sibling carries NO diverge-*/nonterm-*/
#   weak-diverge case, so there is nothing to port. On this bundle the class is
#   CLOSED BY THE SEMANTICS: `loom.semantics.termination "total"` (line 4) with a
#   `decreasing axes.length - i` clause on the frozen loop. Under total semantics a
#   postcondition is claimed of ALL runs, and the verifier demands a decreasing
#   measure on every loop, so a diverging rival is REJECTED rather than vacuously
#   admitted. Measured here, proofs reduced to a bare `loom_solve`: an unmeasured
#   spun loop is refused at elaboration (`Decreasing annotations are required in
#   total correctness semantics`), and the sharper shape carrying a non-decreasing
#   measure (`while q > 0 ... decreasing q`, body `q := q`) is rejected on the
#   measure's own goal -- `case «decreasing_1: q»`, residual `q < q`. So the class
#   is not a spec hole here. (An earlier revision closed this note by contrasting
#   the `partial`-semantics bundles "where it would be a known hole", citing an
#   internal findings doc. There are no such bundles: all 500 velvet bundles set
#   "total" and open TotalCorrectness, so the contrast had no referent and the
#   citation is withdrawn.)
# AXIOM_TESTS: dropped. mapping.md §3 records this bundle has NO axiom and NO
#   A-reference (the changed op — the absent-axis fill — is modeled deeply by
#   `scatterStep`'s `else a.2` branch; both callees the surrounding code touches
#   are unchanged and out of the modeled scope), so G-AX is a legitimate skip. The
#   sibling's AXIOM_TESTS drive the real oracle `full_world_to_pixel`; that is
#   G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single clause C1 (`out = scatter axes supplied`)
#   binds `out`, `axes` (per-axis present flag `.1` and reference coordinate `.2`),
#   and `supplied`; the element-wise model folds four facets — (a) absent-axis fill
#   = `a.2`, (b) present-axis value = next supplied, (c) supplied stream consumed
#   by present axes only (cursor/order), (d) one entry per axis (length). C1 is
#   DEFENDED by the three positive controls and the admissibility case and ATTACKED
#   by all seven rivals:
#     * facet (a) absent fill, by SOURCE : weak-absent-constant-1 (constant 1),
#       weak-absent-constant-0 (constant 0), weak-absent-uses-supplied (supplied
#       head) — three distinct wrong fills of the discriminating branch, abusing
#       the `.2` binder;
#     * facet (a) absent fill, by AXIS INDEX : weak-absent-wrong-axis-ref (added in
#       audit) — keeps the fill's source (it IS a reference coordinate) and breaks
#       WHICH axis it is read from, the granularity none of the three above pins;
#     * facet (b) present value : weak-present-echoes-ref (the ONLY rival keying on
#       a present axis's supplied value, abusing `supplied` on the present branch);
#     * facet (c) cursor/order : weak-absent-also-consumes (the ONLY rival attacking
#       stream consumption);
#     * facet (d) length : weak-return-supplied (the ONLY rival attacking length).
#   The seven reject witnesses probe SEVEN PAIRWISE-DISTINCT input points, distinct
#   in the (axes, supplied) pair itself and not merely in the separation hypothesis:
#     * weak-absent-constant-1   axes=[(false,v)]            supplied=[]     v≠1.0
#     * weak-absent-constant-0   axes=[(true,w),(false,v)]   supplied=[w]    v≠0.0
#     * weak-absent-uses-supplied axes=[(false,v),(true,w)]  supplied=[w]    v≠w
#     * weak-present-echoes-ref  axes=[(true,w)]             supplied=[s]    s≠w
#     * weak-absent-also-consumes axes=[(false,v),(true,w)]  supplied=[s]    s≠0
#     * weak-return-supplied     axes=[(false,v),(true,w),(false,u)] supplied=[w] (none)
#     * weak-absent-wrong-axis-ref axes=[(false,u),(false,v)] supplied=[]    v≠u
#   THIS TABLE WAS WRONG BEFORE THE AUDIT, and the error was exactly the kind the
#   distinctness claim exists to exclude. weak-return-supplied used to sit at
#   axes=[(false,v),(false,w)], supplied=[] — the SAME pair, up to renaming the two
#   bound Floats, as weak-absent-wrong-axis-ref's axes=[(false,u),(false,v)],
#   supplied=[]. So the advertised seven points were six, and each of those two
#   cases' own rationales asserted its point was one no other rival used. Renaming
#   is not distinctness: both witnesses bind fresh universally-quantified Floats, so
#   the two claims were about literally the same input shape and the length facet
#   was only ever pinned on an all-absent input whose cursor never advanced.
#   weak-return-supplied is RE-POINTED (see its rationale) to the battery's only
#   LENGTH-3 input and its only absent/present/absent interleaving, which restores
#   the count to seven genuinely distinct points and pins the length deficit where
#   the supplied stream is non-empty.
#   Every one of the seven (axes, supplied) points was additionally checked to lie
#   INSIDE `require` — `(axes.filter (·.1)).length = supplied.length` discharged by
#   `simp` at each concrete pair (one file, exit 0; the re-pointed length-3 pair
#   re-checked the same way, exit 0) — so no witness refutes the spec at an input
#   the contract never promises anything about.
#   So `axes` ranges over present/absent flags, lengths {1,2,3}, and BOTH orderings
#   of a mixed pair (present-then-absent for weak-absent-constant-0, absent-then-
#   present for weak-absent-uses-supplied / weak-absent-also-consumes) plus the
#   all-absent pair and an absent/present/absent interleaving; `.2` is separated
#   from {1.0, 0.0, the
#   supplied head}; and `supplied` ranges over {[], [w], [s]}. No binder is pinned
#   at a single value across the reject set: the present flag `.1` takes both true
#   and false, `.2` is abused on the absent branch, and `supplied` is abused on the
#   present branch and the cursor facet — a rival that mishandled any one input is
#   caught by a distinct witness. (The two constant-fill rivals and the length rival
#   deliberately do NOT share the one-absent-axis point: a shared point would make
#   the extra rivals restatements at the same input rather than independent probes,
#   which is what the advisory coverage reporter counts.)
# WITNESS DISCRIMINATION (every build re-run in audit; exit codes as observed):
#   each witness ELABORATES against its straight-line rival (exit 0 — the extracted
#   `assembleWorldVectorExec` reduces and the residual Float/Nat/length fact refutes
#   C1 at the probed point) and FAILS against the `witness_reference` (exit 1) —
#   the two-halves discriminator the gate requires, and the gate's own record now
#   reads `witness_subject: "the reference impl"`.
#   The SUBJECT IS NOT GOLD, deliberately. Gold's `…Exec` is a
#   `forIn`/`invariantGadget` term the witness script cannot reduce: Lean reports
#   an application type mismatch on the un-normalised loop, i.e. a STUCK REDUCTION
#   in which the claim was never evaluated. Gold's exit 1 would therefore be a fact
#   about the frozen loop's SYNTAX — any impl whose shape breaks the script fails
#   the same way, including a merely RESHAPED correct one — so it discriminates
#   nothing and is not what these cases rest on. (The gate's stuck-reduction screen
#   keys on `decide`'s "did not reduce to isTrue/isFalse" and does not see an
#   application type mismatch, so this had to be closed here rather than relied on.)
#   The reference is a CORRECT impl in the rivals' OWN `foldl` shape class, checked
#   by the gate to share the spec and to VERIFY (exit 0; it needs `simp_all
#   [scatter]` — a bare `loom_solve` leaves `(List.foldl scatterStep ([], supplied)
#   axes).1 = scatter axes supplied` unsolved). Against it every witness FAILS for
#   the RIGHT reason: the script reduces fully and the refutation collapses to
#   `h2 : True` (or an unprovable `⊢ False`), i.e. the claimed disagreement is
#   absent exactly when the impl is correct. So each witness keys on WRONGNESS, not
#   on the frozen loop's syntax. The value witnesses CONDITION on the carrier (a
#   free `Float` separated from a constant or from another value) because `Float`
#   has no DecidableEq; every such witness binds one or two fresh Floats with a
#   single separation hypothesis that is jointly satisfiable (a dropped coordinate
#   distinct from the placeholder is the F2P scenario) — re-confirmed by building
#   each consistency probe against the reference, all of which FAIL to derive
#   `False` (exit 1). The structural witnesses (length; cursor via `0 = s`) need no
#   Float fact. No `sorry`/`admit`/`native_decide`/`axiom` appears.
#
#   THE FORGERY TEST (audit; the reference-side exit codes above are admissible
#   evidence only because these two experiments were run). The subject-side errors
#   here are NOT plain evaluation failures — they read `Invalid field 'symm': The
#   environment does not contain 'True.symm'` and `Invalid projection: ... it has no
#   fields`, which by themselves could be a syntactic accident rather than a
#   refutation. Two builds settle it, per case:
#
#   (1) TYPE REVEAL. Replace the closing `exact hv h2.symm` with the deliberate
#   type error `exact (h2 : Nat)` and build both sides. Lean then prints h2's REAL
#   type. Against the reference, every case prints `h2 has type True` — `simp`
#   PROVED the equation, i.e. the rival's claimed disagreement is absent when the
#   impl is correct. Against the rival, the same file prints the CONCRETE residual
#   equation: `1.0 = v` (constant-1), `0.0 = v` (constant-0), `w = s`
#   (present-echo), `0 = s` (cursor), `u = v` (wrong-axis), and a conjunction whose
#   first component is `... = if false = true then w else v` (uses-supplied).
#   True-vs-a-real-equation is the genuine refutation pair; the `True.symm` error is
#   thus a COLLAPSE, not a syntax accident. The LENGTH case reads one notch
#   stronger and is recorded separately for that reason: at the re-pointed
#   length-3 point its type-reveal build prints `h2 has type True` against the
#   reference but fails with `No goals to be solved` against the rival — `simp`
#   had already DISCHARGED the length contradiction outright, so there is no
#   residual left for the deliberate type error to name. Re-measured in this
#   audit against the re-pointed witness now on disk, not inherited from the
#   retired all-absent point.
#
#   (2) FLIP THE CLAIM. Swap the witness's `≠` for `=` — asserting the OPPOSITE,
#   that the impl AGREES with the model at that point — and build against both
#   subjects under the same reduction script. Against the reference all seven flips
#   ELABORATE (exit 0): the equality genuinely holds there. Against the rival all
#   seven FAIL (exit 1) on residuals that name both sides concretely — `pure [1.0]
#   = DivM.res [v]`, `pure [w, 0.0] = DivM.res [w, v]`, `pure [w, w] = DivM.res
#   [v, w]`, `pure [w] = DivM.res [s]`, `pure [v, 0] = DivM.res [v, s]`,
#   `pure [w] = DivM.res [v, w, u]` (the re-pointed length case), and
#   `pure [u, u] = DivM.res [u, v]`. So the subject-side exit code TRACKS THE CLAIM
#   in both directions: flipping what is asserted flips which side builds. A hollow
#   case would have produced the byte-identical error for the flipped claim; none
#   did.
#
#   GOLD, for the record (not what the cases rest on): the witness built against
#   the frozen `while` loop fails with `Application type mismatch ... has type
#   (NonDetT.run do let r ← forIn Lean.Loop.mk (MProdWithNames.mk' 0 ...) ...) =
#   DivM.res ...` — the un-normalised loop term, confirming the STUCK REDUCTION the
#   witness_reference exists to route around. The type-reveal build against gold
#   prints the same un-normalised `forIn` term rather than `True` or an equation,
#   which is precisely why gold's exit 1 carries no information about the claim.
#
# SPEC-STRENGTH PROBES (attacks D and E). Exit codes below are from the
#   INDEPENDENT audit re-run; every file was built with scripts/lean_verify.sh.
#
#   ATTACK D — TEN NEW wrong impls aimed at facets the shipped rivals leave
#   thinner, ALL REJECTED (exit 1, each on an `unsolved goals` residual naming
#   C1's `ensures_1: out = scatter axes supplied`), each built BOTH under a bare
#   `loom_solve` and under the frozen script (20 builds, all exit 1): present axis
#   always reads `supplied.headD 0` so the cursor never advances; the whole result
#   REVERSED; drops the FIRST axis (`axes.tail`); drops the LAST axis
#   (`axes.dropLast`); the stream consumed in REVERSE (`supplied.reverse`); absent
#   axes consume only when the stream is non-empty (a data-dependent cursor bug);
#   one spurious trailing entry (`++ [0.0]`); the absent fill NEGATED (`-a.2`, a
#   sign bug that no fixed-constant rival catches); every absent axis filled from
#   the FIRST axis's reference coordinate rather than its own (a wrong-axis
#   crosstalk bug); and the present axis taking the LAST supplied value
#   (`getLast!`) rather than the next. No spec hole found — C1 pins all four
#   facets, including the two the shipped rivals do not reach (sign, wrong-axis).
#
#   ATTACK D, SECOND INDEPENDENT PASS (this audit; a different auditor, aimed at
#   what the ten above still leave unprobed — near-misses that AGREE on every
#   input the battery's own witnesses use, which is the shape a hollow battery
#   would miss). THIRTEEN more wrong impls, each built under the frozen script AND
#   under a bare `loom_solve`; all REJECTED (exit 1) on an `unsolved goals`
#   residual naming C1's `ensures_1: out = scatter axes supplied`:
#     * correct for axes.length ≤ 2 and reversed beyond it — i.e. correct at EVERY
#       one of the battery's seven witness points and wrong only from three axes
#       up. This is the sharpest probe of whether C1 is really universally
#       quantified rather than merely true where the battery looks; rejected.
#     * the absent fill special-cased at one Float value (`a.2 == 0.0 → 1.0`);
#     * a NaN-only divergence (`if a.2 == a.2 then a.2 else 0.0`) and the
#       IEEE-identity near-misses `a.2 + 0.0` and `if a.2 < 0.0 then -(-a.2)
#       else a.2` — all three agree with gold on every normal Float and differ
#       only at NaN/-0.0, so they test that C1 pins Float EQUALITY and not merely
#       numeric agreement; all rejected;
#     * a spurious trailing entry only when every axis is present;
#     * the all-absent output reversed; the LAST axis dropped; the stream padded
#       with an unreachable extra value; the fill read from `axes.getLast!`;
#     * the two literal nagini rivals this port MERGED or re-shaped away, checked
#       directly rather than by argument: constant-fill the whole vector
#       (`axes.map (fun _ => 1.0)`, the sibling's mask-recovered-constant-vector)
#       and corrupt only slot 0 (`(scatter axes supplied).set 0 0.0`, the
#       sibling's partial-first-slot-wrong). Both rejected, so the merge and the
#       re-shape lose no discriminating power.
#   ONE probe VERIFIED and is NOT a hole: `if (axes.filter (·.1)).length =
#   supplied.length then scatter axes supplied else []`. Its `else` arm is
#   unreachable under `require`, so the impl is CORRECT on the contract's whole
#   domain — a partial-identity reshape, i.e. an attack-E positive that happened
#   to be written as a D probe, not a wrong impl the spec admits. Recorded here
#   because "a probe verified" must not be read as a spec hole without checking
#   which arm the precondition selects.
#
#   ATTACK E — NEW correct reshapes. PROVEN (exit 0): the `foldl` shape-class impl
#   used as the reference; `scatter axes (supplied.take ((axes.filter (·.1)).length))`
#   (a reshape that leans on `require`); the index-map reshape
#   `((List.range axes.length).map (fun k => axes[k]!)).foldl …`, closed with a
#   `List.ext_getElem (by simp)` bridge plus
#   `simp [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem h2]`; a
#   `foldr`-over-reversed-axes reshape; and the rivals' own INLINE `fun acc a =>`
#   lambda shape (correct), which needs `all_goals rfl` or an explicit `show` —
#   `simp_all [scatter, scatterStep]` does NOT close it. Two reshapes are recorded
#   UNCERTAIN rather than as holes, because the residual each leaves is a fact the
#   audit could not discharge, not a refutation: `acc.2.head!` in place of
#   `acc.2.headD 0` (equal only via `require`, needing an induction that threads
#   the filter-length hypothesis through both branches), and padding the stream
#   with an unreachable extra value (`supplied ++ [0.0]`, likewise `require`-only).
#   Both residuals are `⊢ <rival fold>.1 = <gold fold>.1` with `require_1` in
#   context — a proof obligation left open, so no SPEC-TOO-STRONG claim is made.
#
#   ATTACK E, SECOND INDEPENDENT PASS (this audit). Four more faithful correct
#   reshapes, all PROVEN (exit 0), so the spec is not over-fit to the frozen
#   loop's local structure: the loop state PACKED into one `List Float × List
#   Float` variable stepped by `scatterStep` itself (one invariant over the whole
#   pair instead of two projections); `result.concat v` in place of `result ++ [v]`
#   (closed by adding `List.concat_eq_append`); the rivals' own inline `fun acc a
#   =>` lambda shape closed by `all_goals first | rfl | simp_all [scatter,
#   scatterStep]`; and `scatter axes (supplied.take ((axes.filter (·.1)).length))`.
#   No faithful correct impl was found that the spec rejects.
#
#   ATTACKS D AND E, THIRD INDEPENDENT PASS (this audit, a third auditor; every
#   exit code below observed via scripts/lean_verify.sh, each impl built under BOTH
#   the frozen script and a bare `loom_solve` unless noted).
#   D — ELEVEN more wrong impls, ALL REJECTED (exit 1, `unsolved goals` on
#   `ensures_1: out = scatter axes supplied`), aimed at the granularities the
#   earlier passes leave thinner:
#     * absent fill read from the LAST axis (`axes.getLastD`) — the mirror of the
#       shipped head-axis crosstalk rival, so the wrong-INDEX facet is pinned at
#       both ends of the list, not just at index 0;
#     * `supplied` indexed by ABSOLUTE axis position (`supplied.getD k 0` over
#       `List.range axes.length`) instead of by the present-count cursor — the
#       cursor facet attacked by re-indexing rather than by over-consuming, which
#       agrees with gold whenever no axis is absent before a present one;
#     * output entries 0 and 1 TRANSPOSED (`(r.set 0 (r.getD 1 0)).set 1 …`) —
#       right multiset, wrong order, so it attacks C1's positional content with
#       every value correct;
#     * correct for `axes.length ≤ 1` and constant-1-filling beyond it, and
#       (separately) correct for `axes.length ≤ 2` and corrupting index 2 beyond it
#       — the second is correct at EVERY one of the battery's seven witness points
#       and wrong only from three axes up, which is the sharpest available check
#       that C1 is universally quantified rather than merely true where the battery
#       looks. Rejected under both scripts;
#     * absent fill NEGATED (`-a.2`); present axis taking the LAST supplied value
#       (`getLastD`); FIRST axis dropped (`axes.tail`); LAST axis dropped
#       (`axes.dropLast`); one spurious trailing entry (`++ [0.0]`).
#   No spec hole: C1 rejected all eleven.
#   TOOLING NOTE, reported rather than worked around: the transposition probe
#   written with a DEPENDENT guard (`if h : 2 ≤ r.length then …`) does not reach
#   the obligation at all — the WP generator fails with `Failed to parse an
#   assertion without names: WPGen (if h : 2 ≤ … then …)`, an error about the
#   surgery's own shape and not about the spec. Rewriting the same defect with
#   total accessors (`r.getD`) built fine and was rejected, so nothing is lost
#   here, but a `dite` in the impl region is a carrier limitation worth knowing.
#   E — four more faithful reshapes. PROVEN (exit 0): `foldr` over the REVERSED
#   axis list (needs `simp_all [scatter]`, i.e. the reference's proof, not the
#   frozen script); the rivals' own inline-lambda shape (needs `first | rfl | …`,
#   confirming the earlier pass's finding that `simp_all [scatter, scatterStep]`
#   alone does not close it); and the `require`-guarded partial-identity
#   `if (axes.filter (·.1)).length = supplied.length then scatter … else []`,
#   which verifies under a bare `loom_solve` — correct on the contract's whole
#   domain, so an E positive and NOT a D hole (its `else` arm is unreachable under
#   `require`). UNCERTAIN, not a hole: the per-axis index-map reshape
#   `(List.range axes.length).map (fun k => if (axes[k]!).1 then
#   supplied.getD ((axes.take k).filter (·.1)).length 0 else (axes[k]!).2)` — a
#   faithful reshape that recomputes each present axis's cursor from scratch
#   instead of threading it. Three proofs tried (bare, `simp_all [scatter]`, a
#   `List.ext_getElem` bridge, and an induction on `axes` generalizing `supplied`),
#   all exit 1 leaving `⊢ List.map … = (List.foldl scatterStep …).1` with
#   `require_1` in context. That is an open obligation — the fold-vs-map bridge
#   needs the prefix-count lemma `((axes.take k).filter (·.1)).length` relates the
#   cursor after `k` steps — not a refutation, so NO SPEC-TOO-STRONG claim is made.
#
#   CARRIER claims re-verified: `DecidableEq Float` fails to synthesize;
#   `prove_postcondition_decidable_for assembleWorldVector` leaves
#   `⊢ Decidable (out = scatter axes supplied)` unsolved (so the Tester route is
#   genuinely dead); and even `(1.0:Float) = 1.0 := by decide` fails to synthesize
#   `Decidable (1.0 = 1.0)`. All seven reject witness inputs were also checked to lie
#   INSIDE the precondition (`require` discharged by `simp` at each of the seven
#   concrete (axes, supplied) pairs, one file, exit 0), so no witness refutes at an
#   inadmissible point.
#   A literal port of the sibling's first-slot-corruption rival was also confirmed
#   REJECTED (exit 1), and an attempt to WRITE a read-only input binder
#   (`supplied := supplied ++ [1.0]`, the frame-mutation analogue) does not
#   elaborate at all: "`supplied` cannot be mutated, only variables declared using
#   `let mut` can be mutated" — the carrier-level demonstration that the frame
#   class is vacuous here rather than merely asserted to be.
AXIOM_TESTS = []
