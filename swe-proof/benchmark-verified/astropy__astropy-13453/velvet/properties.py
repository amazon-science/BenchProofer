"""properties.py — G-PBT falsification battery for astropy__astropy-13453 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct effectiveFormats`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against the witness SUBJECT — which on this cell is the declared
``witness_reference``, not the frozen solution, because gold cannot decide the
claim in either direction. See the CARRIER NOTE.

DEFENDED SURFACE (one contracted method):

  effectiveFormats (cols : List (String × Option String))
      (formats : List (String × String)) return (out : List (Option String))
    ensures out = effFormats formats cols

The method computes each column's EFFECTIVE display format after the writer
applies a supplied per-column format association. A column is a
``(name, current-format)`` pair; ``formats`` is a ``(name, format)`` association
(unique names). The single load-bearing ``ensures`` pins ``out`` element-wise to
the fully-unfolded pure model ``effFormats``:

  ``effFormats m [] = []``
  ``effFormats m (c :: cs) = effFmt m c :: effFormats m cs``
  ``effFmt m (nm, cur) = (lookupFormat m nm).getD cur``  (some-of-supplied ⟶
      override; none ⟶ keep the column's current format)

There is NO opaque answer-key to echo: the ``axioms`` region is empty and
``effFormats`` / ``effFmt`` / ``lookupFormat`` are fully-unfolded ``def``s over
the method's own two arguments, so the unique satisfier IS the honestly-resolved
per-column format list. The single top-level clause combines several
independently-attackable sub-obligations:

  * OVERRIDE (name present in ``formats``): the supplied format wins over the
    column's current one — the direction the fix restores (the pre-change writer
    never applied the supplied formats, so every column kept its current one);
  * KEEP (name ABSENT from ``formats``): the column's current format is retained
    (a supplied-format lookup must NOT be forced onto an unmapped column);
  * ELEMENT-WISE / POSITIONAL: the override/keep decision is per column across
    the whole sequence — no column position is special-cased, and ``out`` has
    the same length as ``cols`` (the length clause is implied by the recursive
    ``effFormats`` shape).

Both input binders are load-bearing: ``formats`` selects override-vs-keep and
supplies the override value; ``cols`` supplies the name that keys the lookup, the
current format used on the keep branch, and the length/order of the result.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY EVERY REJECT CASE NAMES A
``witness_reference``. The gold impl is a backward ``while`` loop under
``loom.semantics.choice "demonic"``, so its extracted ``effectiveFormatsExec``
elaborates through ``Classical.choice`` and does NOT reduce in the kernel. A
witness stated against the FROZEN impl therefore gets STUCK rather than refuted:
``decide`` reports the tester instance "did not reduce to `isTrue` or `isFalse`".

That is NOT a discriminator, and this file previously claimed it was. Re-measured
under audit with real builds, per reject case, on the frozen solution:

  * the witness's own claim (``tester … = false``)      -> exit 1, stuck reduction
  * the FORGED opposite claim (``tester … = true``)     -> exit 1, the SAME error

Gold's exit code is byte-identical for a claim and its negation, so it carried no
information about either: a witness asserting gold is CORRECT at that input would
have been recorded as a refutation just as readily. Loop-freeness of the RIVAL is
not the property the two-build check needs; kernel-reducibility of the SUBJECT is.

So each reject case below carries an explicit ``witness_reference``: the
``pos-return-model`` source, a loop-free impl of this same byte-identical spec
that the gate independently checks (a) shares the frozen spec and (b) VERIFIES,
before refuting the witness against it. An impl the verifier accepts cannot
violate its own spec, so a genuine "the spec is violated here" statement must
still fail against it — and against THAT subject the exit code tracks the claim
(re-measured, per case):

  * the witness's claim (``tester … = false``) -> exit 1, "Tactic ``decide``
    PROVED that the proposition … is false" — a semantic refutation by evaluation
  * the FORGED opposite (``tester … = true``)  -> exit 0, green

Every rival is a loop-free straight-line closed form whose extracted program
reduces by kernel computation, so ``effectiveFormatsTester cols formats`` (from
``derive_tester_for effectiveFormats``) evaluates to a literal ``Bool`` and each
witness closes by ``decide`` at fully-concrete literal inputs. Discrimination is
by VALUE at that input. The carrier at every witness is concrete (``List (String
× Option String)`` / ``List (String × String)`` literals), so no hypothesis is
assumed and there is no joint-satisfiability obligation. Every half was re-run
under audit with real ``scripts/lean_verify.sh`` builds: witness-on-rival exit 0,
witness-on-reference exit 1 (semantic), forgery-on-reference exit 0.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical correct impls (return the grounded pure model
    ``effFormats formats cols`` directly with no loop; and the loop with the
    per-column effective format bound to a local before prepending) must verify,
    else the spec is SPEC-TOO-STRONG on the impl shape. The direct-model form
    reproves with a bare ``loom_solve``; the local-reshape keeps the frozen
    ``loom_solve; rw [effFormats_drop_step …]; simp_all`` proof (only the tactic
    body — elided from the spec view — is retuned where needed).
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame rival that WRITES through a read-only input held at a fractional heap
    permission (``Acc(list_pred(prior_formats), 1/2)``). Lean and Velvet are
    referentially transparent: ``cols`` and ``formats`` are immutable values,
    this bundle declares NO ``mut`` binder for them, and there is no heap and no
    aliasing — so there is no read-only input to overwrite and no permission
    system to trip. Not fabricated (per the porting map, this class is vacuous on
    a referentially-transparent backend). See the footer for the accounting.
  * DIVERGENCE / NON-TERMINATION: the nagini sibling carries NO ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case, so there is nothing to port. The class
    is NOT vacuous here, and the earlier claim that "a diverging impl cannot be
    written in the modeled core" is withdrawn: a rival may rewrite the whole impl
    region and splice a diverging loop ahead of the frozen body, so the class is
    expressible. What closes it is the VERIFIER, not inexpressibility. This bundle
    sets ``loom.semantics.termination "total"``, under which a postcondition is
    claimed of ALL runs, not only terminating ones, so the verifier demands a
    decreasing measure on every loop AND discharges its descent. The setting
    cannot drift from the file's ``open TotalCorrectness DemonicChoice``, because
    the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured on this cell with
    each proof reduced to a bare ``loom_solve``: a spliced loop with NO measure is
    refused at the ``method`` declaration itself
    (``Decreasing annotations are required in total correctness semantics``), and
    the sharper shape that CARRIES a measure which does not decrease
    (``while k > 0 / invariant k > 0 / done_with k = 0 / decreasing k``, body
    ``k := k + 1``) is refused on the measure's own goal: ``case «decreasing_1: k»``,
    residual ``⊢ k + 1 < k``. So the class is closed by the descent obligation and
    there is no hole to record.
  * ADMISSIBILITY — RE-AIMED and now PORTED (``admiss-override-nondegenerate``).
    The sibling's control asserts an F2P-shaped input satisfies its
    half-permission ``Requires``; this method has no ``require`` clause, so that
    exact probe is vacuous. But "no precondition" is NOT a reason to drop the
    lane: the analogue on a total carrier is the obligation being UNSATISFIABLE or
    DEGENERATE at an F2P-shaped input — a spec no impl can meet reads exactly like
    a spec every impl meets. The ported case discharges an in-region ``assert``,
    BY EVALUATION at a concrete F2P-shaped input, that the post-image is
    non-degenerate there, before closing the frozen obligation verbatim. The
    assert is live, not decoration: the same case with a FALSE claim about the
    same point leaves an unsolved goal (measured — exit 1).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a fully-unfolded pure function
    of the two input binders; there is no answer-key term a wrong impl could echo.
    The cheapest correct impl computes the per-column format honestly, which the
    positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the override dropped everywhere;
    the current format discarded on an unmapped column; the first column special-
    cased; the override masked on the tail columns; the last column dropped).
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13453"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the ENTIRE frozen loop body (between and INCLUDING
# ---- the markers). Lies wholly inside the single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap / the assert below).
_IMPL = """    -- impl-start
    let mut result : List (Option String) := []
    let mut i := cols.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cols.length
      invariant result = effFormats formats (cols.drop i)
      done_with i = 0
      decreasing i
    do
      let c := cols[i - 1]!
      result := effFmt formats c :: result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen loop
# ---- body. A positive control that drops the loop entirely retunes it to a bare
# ---- `loom_solve`; both the impl region and the `prove_correct` body are elided
# ---- from the spec view, so same_spec still holds and the `prove_correct
# ---- effectiveFormats` obligation survives with an identical header. Unique.
_PROOF = """prove_correct effectiveFormats by
  loom_solve
  rw [effFormats_drop_step formats cols i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl_block(body):
    return "    -- impl-start\n" + body + "\n    -- impl-end"


def _rewrite_impl(body):
    """Full variant: impl body replaced, spec + frozen proof left intact. For
    rivals (expected NOT to verify) and for positive controls the frozen proof
    still closes."""
    return _swap(_BASE, _IMPL, _impl_block(body))


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `effectiveFormatsTester cols formats = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped, so no tactic
# ---- script can mask the verdict.
def _tester(body):
    return ("extract_program_for effectiveFormats\n"
            "prove_precondition_decidable_for effectiveFormats\n"
            "prove_postcondition_decidable_for effectiveFormats\n"
            "derive_tester_for effectiveFormats\n\n" + body)


# ---- the witness SUBJECT for every reject case. The frozen impl's backward
# ---- `while` under `choice "demonic"` goes through `Classical.choice`, which the
# ---- kernel cannot unfold, so a witness stated against gold fails by STUCK
# ---- REDUCTION for a claim AND for its negation alike (measured — see the
# ---- CARRIER NOTE). Refuting against gold would therefore attest to nothing.
# ---- This is the `pos-return-model` impl: loop-free (so it reduces), and the
# ---- gate re-checks that it shares the frozen spec and VERIFIES before using it,
# ---- so it is a subject that cannot violate the spec it satisfies.
_WITNESS_REF = _swap(_rewrite_impl("    return effFormats formats cols"),
                     _PROOF, "prove_correct effectiveFormats by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded pure model `effFormats formats cols` directly. `effFormats` is
        # a total function of the two inputs (no opaque answer-key), so this is a
        # correct impl, not an echo. The residual goal is definitional, closed by
        # a bare `loom_solve` (the frozen loop-specific rewrite is not needed and
        # is dropped — the tactic body is elided from the spec view, so same_spec
        # and the obligation header are untouched).
        "module": _WITNESS_REF,
        "rationale": (
            "the cheapest honest correct impl returns the grounded pure model "
            "`effFormats formats cols` directly (no loop at all — maximally "
            "different from the gold backward `while`). The ensures is literally "
            "`out = effFormats formats cols`, so it holds on the whole domain and "
            "a bare `loom_solve` discharges the definitional residual. If this "
            "failed the spec would be over-fit to the loop shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: the "
            "model IS the real per-column format work, so returning it is correct, "
            "not a cheat. (Sibling: pos-local-reshape / pos-branch-reorder — a "
            "structurally-different correct impl.)"),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keep the backward loop but compute the per-column effective format into
        # a typed local `e` before prepending (a distinct data shape from the
        # inline `effFmt formats c :: result`). Observationally identical to gold;
        # the frozen `loom_solve; rw [effFormats_drop_step …]; simp_all` proof
        # still closes.
        "module": _rewrite_impl(
            "    let mut result : List (Option String) := []\n"
            "    let mut i := cols.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ cols.length\n"
            "      invariant result = effFormats formats (cols.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := cols[i - 1]!\n"
            "      let e := effFmt formats c\n"
            "      result := e :: result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "structurally-different CORRECT impl: the per-column effective format "
            "is bound to a typed local `e` before prepending, instead of the "
            "inline `effFmt formats c :: result`. Same behaviour, different data "
            "shape; the loop invariants are kept verbatim so the frozen proof "
            "(`loom_solve; rw [effFormats_drop_step …]; simp_all`) still "
            "discharges. Must verify, else the spec is over-fit to the inline "
            "prepend form => SPEC-TOO-STRONG. (Sibling: pos-local-reshape — a "
            "typed-local reshape.)"),
    },

    # =====================================================================
    # ADMISSIBILITY (ported from the sibling's admiss-selfcall, RE-AIMED). This
    # method has no `require` clause, so "a normal input satisfies the
    # precondition" is vacuous — nothing could exclude an F2P-shaped input. The
    # residual admissibility risk on a total domain is that the obligation is
    # UNSATISFIABLE / DEGENERATE at exactly the interesting point, which is what
    # PRECOND-TOO-STRONG looks like here. This case discharges an in-region
    # `assert`, BY EVALUATION at a concrete F2P-shaped input, that the post-image
    # is non-degenerate there, and only then closes the frozen obligation with the
    # frozen impl and the frozen proof (plus a `decide` arm for the extra assert
    # goal — the tactic body is elided from the spec view, so same_spec and the
    # obligation header are untouched).
    #
    # The point is chosen to be the one the reject lane does NOT reach: a column
    # that HAS a current format AND is overridden by a supplied one. The assert
    # pins three things there at once: the resolved image is exactly
    # [some "d", some "c"] (override applied to the first column, current format
    # kept on the second); it is NOT the keep-everything image [some "o", some "c"]
    # (so the override direction is live); and NOT the override-everything image
    # [some "d", some "d"] (so the keep direction is live). A post-image that
    # collapsed either way would fail this.
    #
    # LIVE, not decoration: the identical case with the FIRST conjunct changed to
    # the keep-everything image leaves an unsolved goal (measured, exit 1).
    # =====================================================================
    {
        "id": "admiss-override-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _rewrite_impl(
                "    assert (with_name_prefix `admiss\n"
                "      (effFormats [(\"n\", \"d\")] [(\"n\", some \"o\"), (\"k\", some \"c\")]\n"
                "          = [some \"d\", some \"c\"]\n"
                "        ∧ effFormats [(\"n\", \"d\")] [(\"n\", some \"o\"), (\"k\", some \"c\")]\n"
                "          ≠ [some \"o\", some \"c\"]\n"
                "        ∧ effFormats [(\"n\", \"d\")] [(\"n\", some \"o\"), (\"k\", some \"c\")]\n"
                "          ≠ [some \"d\", some \"d\"]))\n"
                + _IMPL[len("    -- impl-start\n"):-len("\n    -- impl-end")]),
            _PROOF,
            "prove_correct effectiveFormats by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [effFormats_drop_step formats cols i (by omega) (by omega)];\n"
            "       simp_all)"),
        "rationale": (
            "ADMISSIBILITY on a total carrier: the obligation must be SATISFIABLE "
            "and non-degenerate at an F2P-shaped input, else it is "
            "PRECOND-TOO-STRONG in the only sense this backend can express (a "
            "post-image no impl can meet is indistinguishable from one every impl "
            "meets). Discharged by EVALUATION as an in-region `assert` at "
            "cols=[(\"n\", some \"o\"), (\"k\", some \"c\")], formats=[(\"n\", "
            "\"d\")] — a column that HAS a current format and IS overridden, plus "
            "one that keeps its own — before the frozen obligation is closed "
            "verbatim. The assert pins the resolved image to [some \"d\", some "
            "\"c\"] and pins it AWAY from both degenerate collapses "
            "(keep-everything [some \"o\", some \"c\"], override-everything "
            "[some \"d\", some \"d\"]). This is also the ONLY case in the battery "
            "at the override-a-present-current-format point, which the whole "
            "reject lane leaves untouched. (Sibling: admiss-selfcall, re-aimed "
            "from a half-permission Requires probe to post-image non-degeneracy, "
            "since this method has no precondition.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE);
    # the frozen spec and obligation header are untouched.
    # =====================================================================
    {
        "id": "r1-keep-current-ignore-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # Refute against the loop-free verifying reference, not against gold:
        # gold cannot decide either the claim or its negation (CARRIER NOTE).
        "witness_reference": _WITNESS_REF,
        # The pre-change behaviour: never consult the supplied formats; return
        # each column's CURRENT format. Wrong precisely on any column whose name
        # is in `formats` (the override is dropped).
        "module": _rewrite_impl("    return cols.map (fun c => c.2)"),
        "refinement": (
            "this is the base-commit behaviour: the writer never applies the "
            "supplied per-column formats, so every column keeps its current "
            "format. The failing scenario supplies a format for a column whose "
            "current format is unset; the exact-output assertion requires the "
            "supplied format to be applied, but this rival leaves the column "
            "unformatted — the test FAILS, so it does NOT resolve. This IS the "
            "modeled bug and the prepatch discriminator (G-DIFF). Correct on every "
            "column whose name is absent from the supplied formats (a true "
            "partial-domain break, not a blanket wrong impl)."),
        "rationale": (
            "REJECT from the OVERRIDE sub-obligation: on a column whose name is in "
            "`formats` the spec requires the supplied format, but this returns the "
            "current one. If it verified => SPEC-TOO-WEAK (the supplied-format "
            "override unenforced). Refuted at cols=[(\"a\", none)], "
            "formats=[(\"a\", \"x\")]: gold resolves [some \"x\"], the rival "
            "[none]. (Sibling: rival-prepatch-keep-prior.)"),
        "witness": _tester(
            'example : effectiveFormatsTester [("a", (none : Option String))] '
            '[("a", "x")] = false := by\n  decide\n'),
    },
    {
        "id": "r2-force-supplied-drop-current",
        "kind": "uniqueness",
        "expect": "reject",
        # Refute against the loop-free verifying reference, not against gold:
        # gold cannot decide either the claim or its negation (CARRIER NOTE).
        "witness_reference": _WITNESS_REF,
        # Mirror error on the KEEP branch: always take the supplied-format lookup
        # (`lookupFormat formats c.1`, which is `none` for an unmapped column)
        # instead of falling back to the column's current format. Wrong precisely
        # on a column whose name is ABSENT from `formats` but has a current
        # format — the current format is discarded.
        "module": _rewrite_impl("    return cols.map (fun c => lookupFormat formats c.1)"),
        "refinement": (
            "a counterpart that overwrote every column's format with the supplied "
            "lookup — clearing the format of any column NOT named in the supplied "
            "association (the lookup yields nothing there) instead of leaving it "
            "untouched. A PASS_TO_PASS scenario carrying a column with a "
            "pre-existing format but no supplied override asserts that column "
            "keeps its format; this rival clears it — that case FAILS, so it does "
            "NOT resolve. Correct on every column whose name IS in the supplied "
            "formats."),
        "rationale": (
            "REJECT from the KEEP sub-obligation: on a column whose name is absent "
            "from `formats` the spec requires its current format "
            "(`(lookupFormat m nm).getD cur = cur` when the lookup is none), but "
            "this returns the `none` lookup. If it verified => SPEC-TOO-WEAK (the "
            "keep-current fallback unpinned — the ONLY rival on which a column's "
            "CURRENT format is the deciding value). Refuted at "
            "cols=[(\"a\", some \"z\")], formats=[]: gold resolves [some \"z\"], "
            "the rival [none]. This witness also varies `formats` to empty and "
            "`cols` to a present current format, values no other witness uses."),
        "witness": _tester(
            'example : effectiveFormatsTester [("a", (some "z" : Option String))] '
            '[] = false := by\n  decide\n'),
    },
    {
        "id": "r3-skip-first-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Refute against the loop-free verifying reference, not against gold:
        # gold cannot decide either the claim or its negation (CARRIER NOTE).
        "witness_reference": _WITNESS_REF,
        # PARTIAL-DOMAIN (first element): keep the FIRST column's current format
        # (ignore the supplied override for it) and resolve the rest correctly.
        # Diverges only on the first-column sub-domain.
        "module": _rewrite_impl(
            "    return (match cols with\n"
            "      | [] => []\n"
            "      | c :: cs => c.2 :: effFormats formats cs)"),
        "refinement": (
            "a faithful patch that skipped the first output column of the "
            "sequence (e.g. began applying supplied formats from the second "
            "column) would leave the first column unformatted whenever it carried "
            "a supplied override. The failing scenario's FIRST column carries a "
            "supplied format and must render formatted; this rival leaves it with "
            "its current (unset) format, so the exact-output assertion FAILS — it "
            "would NOT resolve. Correct on every non-first column, so it agrees "
            "with gold over more of the domain than r1 and is refuted at the "
            "distinguishing first-column input."),
        "rationale": (
            "REJECT from the OVERRIDE sub-obligation at the FIRST column: when the "
            "leading column's name is in `formats` the spec requires the supplied "
            "format there, but this keeps its current one. If it verified => "
            "SPEC-TOO-WEAK (the first-column sub-domain unpinned). Refuted at "
            "cols=[(\"e\", none), (\"f\", none)], formats=[(\"e\", \"x\")]: gold "
            "resolves [some \"x\", none], the rival [none, none]. (Sibling: "
            "rival-skip-first-column.)"),
        "witness": _tester(
            'example : effectiveFormatsTester [("e", (none : Option String)), '
            '("f", (none : Option String))] [("e", "x")] = false := by\n  decide\n'),
    },
    {
        "id": "r4-mask-override-on-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Refute against the loop-free verifying reference, not against gold:
        # gold cannot decide either the claim or its negation (CARRIER NOTE).
        "witness_reference": _WITNESS_REF,
        # PARTIAL-DOMAIN (tail columns): resolve the FIRST column correctly but
        # keep every subsequent column's current format (mask the override on the
        # tail). The value-proxy analogue of the sibling's odd-index mask.
        "module": _rewrite_impl(
            "    return (match cols with\n"
            "      | [] => []\n"
            "      | c :: cs => effFmt formats c :: cs.map (fun d => d.2))"),
        "refinement": (
            "a counterpart that applied the supplied override only to the leading "
            "column and left the rest with their current formats (a partial sweep "
            "of the column sequence) — the demoted-override bug on the tail. A "
            "scenario supplying a format for a NON-leading column asserts that "
            "column renders formatted; this rival leaves it unformatted, so the "
            "exact-output assertion FAILS — it would NOT resolve. Correct on the "
            "leading column and on any tail column whose name is absent from the "
            "supplied formats; refuted at the distinguishing tail-override input "
            "(a different sub-domain from r3, which special-cases the FIRST "
            "column)."),
        "rationale": (
            "REJECT from the OVERRIDE sub-obligation on a NON-leading column: when "
            "a tail column's name is in `formats` the spec requires the supplied "
            "format there, but this keeps its current one. If it verified => "
            "SPEC-TOO-WEAK (the override masked on the tail sub-domain). Refuted "
            "at cols=[(\"b\", none), (\"c\", none)], formats=[(\"c\", \"y\")]: "
            "gold resolves [none, some \"y\"], the rival [none, none]. (Sibling: "
            "rival-proxy-mask-odd-present.)"),
        "witness": _tester(
            'example : effectiveFormatsTester [("b", (none : Option String)), '
            '("c", (none : Option String))] [("c", "y")] = false := by\n  decide\n'),
    },
    {
        "id": "r5-drop-last-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Refute against the loop-free verifying reference, not against gold:
        # gold cannot decide either the claim or its negation (CARRIER NOTE).
        "witness_reference": _WITNESS_REF,
        # PARTIAL-DOMAIN (length): resolve every column correctly but DROP THE
        # LAST one, returning a list one element short. Attacks the length clause
        # implied by the recursive `effFormats` shape.
        "module": _rewrite_impl("    return (effFormats formats cols).dropLast"),
        "refinement": (
            "a writer that resolved all but the final output column (an off-by-one "
            "over the column sequence) would render HTML missing the last column's "
            "cell entirely. The F2P/P2P exact-output assertions compare the full "
            "rendered table, so a missing final column FAILS them — it would NOT "
            "resolve. Element-wise correct on every column it DOES emit; the break "
            "is purely the dropped tail element (the length clause)."),
        "rationale": (
            "REJECT from the length/element-wise clause: `effFormats formats cols` "
            "has one entry per column, but `.dropLast` returns one fewer, so `out` "
            "≠ the model whenever `cols` is non-empty. If it verified => "
            "SPEC-TOO-WEAK (result length not pinned). Refuted at "
            "cols=[(\"a\", none), (\"d\", none)], formats=[(\"d\", \"w\")]: gold "
            "resolves [none, some \"w\"], the rival [none] (last entry dropped). "
            "(Sibling: rival-drop-last-column.)"),
        "witness": _tester(
            'example : effectiveFormatsTester [("a", (none : Option String)), '
            '("d", (none : Option String))] [("d", "w")] = false := by\n  decide\n'),
    },
    {
        "id": "r6-override-only-when-unset",
        "kind": "uniqueness",
        "expect": "reject",
        # Refute against the loop-free verifying reference, not against gold:
        # gold cannot decide either the claim or its negation (CARRIER NOTE).
        "witness_reference": _WITNESS_REF,
        # ADDED UNDER AUDIT. The whole shipped reject lane probes the override
        # direction only at columns whose current format is UNSET (r1/r3/r4/r5 all
        # use `none` there), and probes a PRESENT current format only where no
        # override applies (r2, empty `formats`). So the precedence question —
        # when a column ALREADY has a format and one is also supplied, which
        # wins? — was pinned by no rejection at all. This rival treats the current
        # format as taking precedence: it consults the supplied formats ONLY for a
        # column whose current format is unset. Wrong precisely on the untested
        # sub-domain (current present AND supplied present), and correct
        # everywhere else — including on every input the other five rivals are
        # refuted at.
        "module": _rewrite_impl(
            "    return cols.map (fun c => match c.2 with\n"
            "      | some f => some f\n"
            "      | none   => lookupFormat formats c.1)"),
        "refinement": (
            "a counterpart that applied a supplied format only to columns that "
            "did not already carry one — i.e. treated an existing column format "
            "as taking precedence over the supplied one, rather than being "
            "overridden by it. A scenario that supplies a format for a column "
            "which already carries a different one asserts the SUPPLIED format is "
            "what renders; this rival renders the pre-existing one instead, so "
            "the exact-output assertion FAILS — it would NOT resolve. Correct on "
            "every column whose current format is unset, and on every column with "
            "no supplied override, so it agrees with gold strictly more widely "
            "than r1 and is refuted only at the precedence point."),
        "rationale": (
            "REJECT from the OVERRIDE sub-obligation at its PRECEDENCE edge: the "
            "model is `(lookupFormat m nm).getD cur`, so a supplied format wins "
            "even when the column already has one. This rival inverts that "
            "precedence. If it verified => SPEC-TOO-WEAK (override-vs-existing "
            "precedence unpinned — the spec would admit both directions whenever "
            "the column already carries a format). Refuted at "
            "cols=[(\"n\", some \"o\")], formats=[(\"n\", \"d\")]: the spec "
            "resolves [some \"d\"], the rival [some \"o\"]. This is the ONLY "
            "reject case where a column's current format AND a supplied override "
            "are both present, the sub-domain the other five leave unattacked. "
            "(No sibling: the nagini rivals attack the override direction only "
            "where the prior token is the fallback, so this edge is new here.)"),
        "witness": _tester(
            'example : effectiveFormatsTester [("n", (some "o" : Option String))] '
            '[("n", "d")] = false := by\n  decide\n'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals — one of which is a mandatory
# frame-mutation rival; AXIOM_TESTS present but this gate ignores them). The
# sibling contracts `resolve_column_formats(names, prior_formats, formats)` over
# two index-aligned `List[int]` inputs + a `Dict` under fractional read-only
# permissions and partial correctness. This backend models the SAME per-column
# effective-format selection DEEPLY and CONCRETELY (`effFormats` over
# `List (String × Option String)` with `(name, current)` columns and a
# `List (String × String)` supplied association), pins it with a single
# element-wise `ensures`, runs under TOTAL termination semantics, and has NO
# precondition and NO permission surface. Those carrier facts make two sibling
# classes vacuous/degenerate here.
#
#   nagini case                       kind          -> here                         disposition
#   -----------------------------------------------------------------------------------------------
#   pos-branch-reorder                soundness     -> pos-return-model             RE-SHAPED
#   pos-local-reshape                 soundness     -> pos-local-reshape            PORTED
#   admiss-selfcall                   admissibility -> admiss-override-nondegenerate PORTED (re-aimed)
#   rival-frame-mutate-prior          uniqueness    -> (none)                       VACUOUS
#   rival-prepatch-keep-prior         uniqueness    -> r1-keep-current-ignore-supplied  PORTED
#   rival-proxy-mask-odd-present      uniqueness    -> r4-mask-override-on-tail     PORTED (re-shaped)
#   rival-skip-first-column           uniqueness    -> r3-skip-first-column         PORTED
#   rival-drop-last-column            uniqueness    -> r5-drop-last-column          PORTED
#   (no sibling)                      uniqueness    -> r2-force-supplied-drop-current   ADDED
#   (no sibling)                      uniqueness    -> r6-override-only-when-unset   ADDED (audit)
#   AXIOM_TESTS                       axiom         -> (none)                       N/A (G-AX)
#
# 4 uniqueness ported (one re-shaped) + 2 added; 1 soundness re-shaped + 1 ported;
# 1 admissibility ported (re-aimed), 1 frame-mutation vacuous; axiom lane dropped.
# 9 SPEC cases (2 soundness, 1 admissibility, 6 uniqueness).
#
# RE-SHAPED (pos-branch-reorder -> pos-return-model): the sibling's positive is a
#   branch reorder (absent-name case tested first). On this carrier the
#   maximally-different correct impl drops the loop entirely and returns the
#   grounded model `effFormats formats cols`; it also serves as the no-ungrounded-
#   echo control (the model is the real work, not an answer-key). PORTED
#   (pos-local-reshape -> pos-local-reshape): the sibling's local-reshape positive
#   (resolved token computed into a typed local `chosen` then appended once) maps
#   directly to binding the per-column `effFmt` into a local `e` before
#   prepending; the loop invariants are kept verbatim and the frozen proof closes.
# PORTED (the four value/branch/length rivals):
#   rival-prepatch-keep-prior -> r1-keep-current-ignore-supplied (the verbatim
#     pre-change behaviour: never apply the supplied formats; the F2P
#     discriminator). rival-skip-first-column -> r3-skip-first-column (keep the
#     first column's current format; refuted at the distinguishing first-column
#     input). rival-proxy-mask-odd-present -> r4-mask-override-on-tail (mask the
#     override on the tail columns; the value-proxy partial-domain rival re-shaped
#     from the sibling's odd-index mask to a tail mask, which the front-recursive
#     carrier expresses cleanly). rival-drop-last-column -> r5-drop-last-column
#     (drop the last emitted column, attacking the length/element-wise clause).
# ADDED (r2-force-supplied-drop-current): the mirror error on the KEEP branch —
#   force the supplied-format lookup onto every column, discarding the current
#   format of any column NOT named in the supplied association. It is the ONLY
#   rival on which a column's CURRENT format is the deciding value, and the only
#   one probing an EMPTY `formats`; the sibling's rivals all attack the override
#   direction, leaving the keep-current fallback otherwise untested here.
# PORTED, RE-AIMED (admiss-selfcall -> admiss-override-nondegenerate): the
#   sibling's control asserts an F2P-shaped input establishes its half-permission
#   `Requires` (two index-aligned lists + a Dict). This method has NO `require`
#   clause, so that exact probe is vacuous — but the LANE is not, and dropping it
#   would remove the only direction of this gate that tests PRECOND-TOO-STRONG.
#   The analogue on a total carrier is the obligation being UNSATISFIABLE or
#   DEGENERATE at exactly an F2P-shaped input: a post-image no impl can meet reads
#   identically to one every impl meets, and the reject lane cannot tell the
#   difference (a rival fails either way). So the ported case discharges, BY
#   EVALUATION, an in-region `assert` that the post-image at a concrete F2P-shaped
#   input is exactly the resolved list AND is distinct from both degenerate
#   collapses (keep-everything, override-everything), then closes the frozen
#   obligation verbatim with the frozen impl. Measured live: the same case
#   asserting the keep-everything image instead leaves an unsolved goal (exit 1),
#   so the assert carries the claim rather than decorating it.
# VACUOUS (rival-frame-mutate-prior): the sibling's MANDATORY frame rival writes
#   the selected spec back onto the read-only input `prior_formats[i]`, held at
#   `Acc(list_pred(prior_formats), 1/2)`, rejected by the insufficient-permission
#   check. This backend is referentially transparent: `cols` and `formats` are
#   immutable values, no `mut` binder is declared for them, and there is no heap,
#   no aliasing, and no permission system. There is no read-only input to
#   overwrite and no frame clause to violate, so the class has no carrier
#   analogue. Omitted as a genuine carrier fact, NOT fabricated (porting map: this
#   class is vacuous on a referentially-transparent backend).
# DIVERGENCE / NON-TERMINATION: the sibling carries NO diverge-*/nonterm-*/
#   weak-diverge case, so there is nothing to port. The class is EXPRESSIBLE
#   (a rival may splice a diverging loop ahead of the frozen body) and is closed
#   by the verifier, not by inexpressibility: this bundle sets
#   `loom.semantics.termination "total"`, so a postcondition is claimed of ALL
#   runs and every loop owes a decreasing measure AND its descent. Measured with
#   the proof reduced to `loom_solve`: no measure -> refused at the `method`
#   ("Decreasing annotations are required in total correctness semantics");
#   measure supplied but non-decreasing (`decreasing k`, body `k := k + 1`) ->
#   refused on `case «decreasing_1: k»`, residual `k + 1 < k`.
#
# BINDER / CLAUSE COVERAGE. The single `ensures out = effFormats formats cols`
#   binds `out`, `cols`, and `formats`; the element-wise model combines an
#   OVERRIDE sub-obligation (name in `formats` -> supplied wins), a KEEP
#   sub-obligation (name absent -> current retained), the POSITIONAL/element-wise
#   guarantee, and the result LENGTH. All are attacked:
#     * OVERRIDE (name present -> supplied): r1 (all columns), r3 (first column),
#       r4 (tail columns) — three distinct sub-domains of the same direction.
#     * OVERRIDE PRECEDENCE (supplied beats an EXISTING current format): r6. Added
#       under audit; see below.
#     * KEEP (name absent -> current): r2 (discards the current format on an
#       unmapped column).
#     * LENGTH / element-wise: r5 (drops the last emitted column).
#   The six reject witnesses probe six DISTINCT input points:
#     * r1  cols=[("a", none)]                 formats=[("a", "x")]
#     * r2  cols=[("a", some "z")]             formats=[]
#     * r3  cols=[("e", none), ("f", none)]    formats=[("e", "x")]
#     * r4  cols=[("b", none), ("c", none)]    formats=[("c", "y")]
#     * r5  cols=[("a", none), ("d", none)]    formats=[("d", "w")]
#     * r6  cols=[("n", some "o")]             formats=[("n", "d")]
#   plus the admissibility point cols=[("n", some "o"), ("k", some "c")],
#   formats=[("n", "d")], which is the only 2-column input combining an overridden
#   present format with a kept present format.
#   So `formats` ranges over {override-of-present, EMPTY, override-of-first,
#   override-of-tail, override-of-last, override-of-an-already-formatted-column},
#   and `cols` over current formats {none, some "z", some "o", some "c"} and
#   lengths {1, 2}. No binder is pinned at a single value across the reject set.
#
#   AUDIT NOTE on what the shipped five did NOT cover. r1/r3/r4/r5 all set the
#   current format to `none` wherever an override applies, and r2 exercises a
#   PRESENT current format only where `formats` is empty. So no rejection pinned
#   the PRECEDENCE question — when a column already carries a format and one is
#   also supplied, which wins — even though the model (`(lookupFormat m nm).getD
#   cur`) answers it and the OVERRIDE direction is exactly the modeled change.
#   The `some`-vs-`none` variation across the old five was therefore two spellings
#   of the same point rather than a meaningful spread. r6 and the admissibility
#   case close it: r6 is refuted at that point by evaluation, and the
#   admissibility assert pins the resolved image there away from both collapses.
# WITNESS DISCRIMINATION (re-run under audit, three real builds per reject case).
#   Each witness ELABORATES against its loop-free rival (exit 0: the extracted
#   program's result provably violates the ensures at the probed input,
#   `effectiveFormatsTester … = false` closing by `decide`) and is REFUTED against
#   the declared `witness_reference` (exit 1 with "Tactic `decide` PROVED that the
#   proposition … is false" — a semantic refutation by evaluation, not a stuck
#   term). The FORGERY control per case — the same witness with its claim flipped
#   to `= true` — builds GREEN (exit 0) against that reference, so the reference's
#   exit code demonstrably tracks the claim.
#   The frozen solution is NOT the subject and could not be: measured, its
#   backward loop under `choice "demonic"` leaves `decide` stuck, and the flipped
#   claim produces the byte-identical error, so a gold-side exit code here attests
#   to nothing. See the CARRIER NOTE. The carrier is fully concrete at every
#   witness, so each closes by `decide` with no hypothesis and there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (the sibling's AXIOM_TESTS
#   drive the real per-column format-selection helper, an A-reference validated by
#   G-AX, not a consumed axiom — mapping.md §3.1), and this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
