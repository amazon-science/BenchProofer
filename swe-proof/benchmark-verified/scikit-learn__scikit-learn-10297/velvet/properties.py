"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-10297 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct initEstimator`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single boolean input):

  initEstimator (storeCvValues : Bool)
      return (out : Except InitErr EstimatorState)
    ensures out = construct true storeCvValues            -- THE load-bearing clause

The method models the construction of a cross-validated estimator that gains an
optional flag requesting the per-alpha cross-validation values be retained for
later inspection. ``construct (acceptsStore) (storeCvValues)`` is a total,
fully-unfolded pure ``def`` over the method's own inputs (``pure`` region): when
retention is requested of an estimator that does NOT support it, construction is
refused (``Except.error``); otherwise the estimator is built and the requested
option is recorded on it UNCHANGED (``Except.ok { storeCvValues := ... }``). The
capability here is fixed by the desired behaviour: this estimator supports the
option, so the method's obligation is pinned at ``construct true storeCvValues``.
Because ``acceptsStore = true``, the obligation is equivalently
``out = Except.ok { storeCvValues := storeCvValues }`` for every input — i.e. the
construction always SUCCEEDS and the built estimator carries the requested flag
through verbatim (both legs of the desired behaviour: accept, and record
faithfully).

The ``axioms`` region is EMPTY; there is no opaque answer key to echo
(directive 8 — the post-image is grounded in the method's actual input, the
boolean flag). The clause decomposes into two independently-attackable
top-level sub-behaviours over the sole binder ``storeCvValues``:

  * ACCEPT   — construction must SUCCEED (``Except.ok``) for every requested
               value of the flag, including ``true`` (the pre-fix reality was a
               refusal when the option was requested);
  * RECORD   — the built estimator's ``storeCvValues`` field must equal the
               requested flag verbatim — not a constant, not the negation (a
               later fit reads the recorded option to decide whether to populate
               the retained-values attribute, so a corrupted record silently
               changes downstream behaviour).

ONE input binder, free: ``storeCvValues : Bool``. The post-image must hold for
BOTH of its values; a rival correct at one value and wrong at the other is the
natural falsifier, so the reject witnesses below probe the binder at BOTH ``true``
and ``false`` — a rival that mishandled only one value would otherwise verify and
go uncaught.

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case accounting
in the footer):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling holds ``cfg`` at a
    fractional (1/2) permission, so a rival that WRITES ``cfg.retain_values`` is
    rejected for insufficient permission. This backend is referentially
    transparent and this bundle declares NO ``mut`` binder: ``storeCvValues`` is
    an immutable value, there is no heap and no aliasing, so there is no
    read-only input to overwrite and no substitute probe. Not fabricated (per the
    porting map, legitimately dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. ``construct`` is
    a total ``def`` in the ``pure`` region written directly over the method's own
    inputs; it is not an opaque axiomatized answer-key an impl could echo without
    doing the work (the impl must itself produce ``Except.ok`` with the right
    recorded field). The ``axioms`` region declares no ``axiom``.
  * PARTIAL-DOMAIN / VALUE — APPLIES to the modeled surface. The sole binder has
    two values; a rival right on one and wrong on the other partitions the domain
    exactly. The rivals below attack ACCEPT (refuse when requested) and RECORD
    (constant / negated flag).
  * DIVERGENCE / NON-TERMINATION — NOTHING TO SHIP, and the reason is the
    termination SEMANTICS, not inexpressibility. A diverging impl IS expressible
    in the impl region (a ``while`` with no decreasing measure elaborates
    syntactically), but this bundle declares
    ``set_option loom.semantics.termination "total"``, so such an impl is
    REJECTED rather than vacuously accepted — measured here with a real build:
    ``error: Decreasing annotations are required in total correctness
    semantics`` plus ``Failed to prove assertion without names: WPGen (forIn
    Lean.Loop.mk ...)``. The sharper shape is refused as well, which matters because
    it cannot be dismissed as merely missing the annotation: a loop CARRYING a measure
    that does not decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q``, body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. (An earlier version of this
    passage called that the ``total`` leg of a corpus measurement in an internal
    findings doc, "partial/VERIFIES 401, total/rejected 99", and described the known
    spec hole as a ``partial``-semantics one. Both are withdrawn: all 500 velvet
    bundles set ``"total"``, so no such hole is on file anywhere.) A rival here would
    therefore be rejected by the
    termination checker rather than by the ``ensures`` clause, attributing its
    rejection to the solver flag instead of to the spec, which is why none is
    shipped.

WITNESS MECHANICS ON THIS BUNDLE. The carrier is fully TRANSPARENT — the sole
input is a ``Bool`` and ``construct`` is a concrete ``def`` — so a witness pins the
refutation at a concrete boolean literal, no conditioning-on-an-opaque-term is
needed (so no witness binds any hypothesis, and the consistency probe is vacuous
by construction). The spec is a ``method`` CONTRACT, not a bare predicate, so the
witness reaches the impl through Velvet's own extractor: ``extract_program_for``
gives ``initEstimatorExec = NonDetT.run ∘ initEstimator``, which reduces to
``DivM.res <result>``; ``initEstimatorExec b ≠ DivM.res (construct true b)`` says
the extracted program's output contradicts the postcondition at the concrete
input ``b``. (A tester-based ``initEstimatorTester b`` witness does NOT work here:
the extracted postcondition-decidability instance for ``out = construct …`` over
``Except InitErr EstimatorState`` does not reduce under ``decide`` — measured — so
the extractor route is used, as on other ``Except``-returning velvet bundles.)
The snippet is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict, and it must (1) elaborate against the
rival and (2) FAIL against the frozen solution — both halves verified out-of-band
with ``scripts/lean_verify.sh`` for every rival below (against gold the same goal
reduces to ``⊢ False`` and is left unsolved). No ``sorry``/``admit``/
``native_decide``/``axiom``.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(the construction is a concrete ``def`` over the input, validated end-to-end
against the real patched class by G-CONF). Nothing in the proof rests on an
axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10297"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole capability + branch, wholly inside the one
# ---- `-- impl-start` / `-- impl-end` region and unique in the file (both facts
# ---- asserted at load by _swap). Every variant reshapes exactly this block. ----
_IMPL = (
    "    -- `acceptsStore` is this estimator's capability: it supports retaining the\n"
    "    -- per-alpha cross-validation values.\n"
    "    let acceptsStore : Bool := true\n"
    "    if storeCvValues && !acceptsStore then\n"
    "      return Except.error InitErr.storeNotAccepted\n"
    "    else\n"
    "      return Except.ok { storeCvValues := storeCvValues }"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the frozen `prove_correct` tactic body. A positive control that reshapes
# ---- the impl into a form the frozen script no longer closes may RETUNE this
# ---- body (it is elided from the consumer spec view) WITHOUT touching the spec
# ---- or dropping the obligation — the `prove_correct initEstimator by` header
# ---- statement stays byte-identical. Unique in the file. ----
_PROOF = "prove_correct initEstimator by\n  loom_solve\n  simp [construct]"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's extractor.
# ---- `initEstimatorExec b` is `NonDetT.run (initEstimator b)`, which reduces to
# ---- `DivM.res <result>`; `≠ DivM.res (construct true b)` says the impl's
# ---- output contradicts the postcondition at the concrete literal `b`. Checked
# ---- in a file whose `prove_correct` block is stripped, so no tactic script can
# ---- interfere. The carrier is transparent, so the witness binds NOTHING (no
# ---- hypothesis to be inconsistent — the consistency probe is vacuous).
def _witness(b):
    return ("extract_program_for initEstimator\n\n"
            f"example : initEstimatorExec {b} ≠ DivM.res (construct true {b}) := by\n"
            "  unfold initEstimatorExec initEstimator construct\n"
            "  simp [NonDetT.run, pure]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Since the estimator supports
    # the option, the refuse branch is DEAD (`acceptsStore = true` makes its
    # guard unsatisfiable), so an impl that unconditionally succeeds and records
    # the flag is observationally identical to gold on every input. The frozen
    # proof (`loom_solve; simp [construct]`) still closes the byte-identical
    # obligation. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-drop-dead-refuse-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return Except.ok { storeCvValues := storeCvValues }"),
        "rationale": "structurally different CORRECT impl: it drops the "
                     "(unreachable) refuse branch and unconditionally builds the "
                     "estimator recording the requested flag. Because the "
                     "capability is `true`, the refuse guard is unsatisfiable, so "
                     "this agrees with `construct true storeCvValues` on both "
                     "values of the input. A faithful reshape MUST verify, else "
                     "the postcondition is SPEC-TOO-STRONG (it would reject its "
                     "own model's output).",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — return the pure model directly. Keeps the
    # whole construction; the extracted result IS `construct true storeCvValues`
    # definitionally, so the obligation closes under `loom_solve` alone (the
    # frozen script's trailing `simp [construct]` would then see no goals, so the
    # proof body is retuned to `loom_solve` — elided from the spec view; the
    # `prove_correct initEstimator by` header stays byte-identical). Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-construct-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return construct true storeCvValues",
            "prove_correct initEstimator by\n  loom_solve"),
        "rationale": "statement-level positive control: it returns the pure "
                     "construction model directly rather than inlining the "
                     "branch. Observationally identical on every input, so "
                     "`out = construct true storeCvValues` holds on the whole "
                     "domain. Must verify.",
    },

    # =====================================================================
    # POSITIVE CONTROL 3 (soundness) — the reshape whose proof the FROZEN script
    # does NOT close. Both positives above happen to discharge under a script
    # very near the frozen one, so neither shows that the obligation is
    # independent of the impl's syntactic form. This one splits on the binder and
    # writes the recorded flag as a LITERAL in each branch, so `loom_solve`
    # leaves two per-branch goals the frozen trailing `simp [construct]` cannot
    # close (measured: `unsolved goals ... ⊢ storeCvValues = true` and
    # `⊢ Except.ok { storeCvValues := false } = construct true storeCvValues`).
    # It is nevertheless observationally identical to gold on the whole domain,
    # so it MUST verify once the (spec-view-elided) tactic body substitutes the
    # branch hypothesis. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-branch-on-flag-literals",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    if storeCvValues then\n"
            "      return Except.ok { storeCvValues := true }\n"
            "    else\n"
            "      return Except.ok { storeCvValues := false }",
            "prove_correct initEstimator by\n  loom_solve\n"
            "  all_goals simp_all [construct]"),
        "rationale": "CORRECT reshape that branches on the sole binder and "
                     "records a literal in each leg. Agrees with "
                     "`construct true storeCvValues` at both inputs, so it must "
                     "verify — but unlike the other two positives its goals are "
                     "NOT closed by the frozen tactic body, which is what makes "
                     "it evidence that the obligation is pinned by the `ensures` "
                     "clause rather than by one impl's syntactic shape. Rejecting "
                     "it would be SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe re-establishes that the
    # precondition admits a normal F2P-shaped input and the post-image is
    # reachable and non-degenerate there. This backend has NO `require` clause
    # (the domain is total, every value of `storeCvValues` is in scope), so the
    # residual admissibility risk is that the post-image is DEGENERATE at the
    # interesting point — e.g. only ever the refuse variant, or a constant field.
    # One in-region `assert` pins BOTH: at the F2P-relevant input (retention
    # REQUESTED, `true`) construction SUCCEEDS and records `true`, and at `false`
    # it succeeds and records `false` — so the two outcomes are DISTINCT (the
    # flag is genuinely carried, not collapsed) and neither is a refusal. The
    # impl is kept verbatim so the method's own obligation still discharges; the
    # proof is retuned only to clear the extra assert goal (`simp [construct]`),
    # which is elided from the spec view. The assert is LIVE (a false claim
    # leaves an unsolved goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-flag-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (construct true true = Except.ok { storeCvValues := true } ∧\n"
            "       construct true false = Except.ok { storeCvValues := false }))\n"
            "    let acceptsStore : Bool := true\n"
            "    if storeCvValues && !acceptsStore then\n"
            "      return Except.error InitErr.storeNotAccepted\n"
            "    else\n"
            "      return Except.ok { storeCvValues := storeCvValues }",
            "prove_correct initEstimator by\n  loom_solve\n  all_goals simp [construct]"),
        "rationale": "the total domain admits the F2P-shaped input (retention "
                     "REQUESTED) AND the post-image is non-degenerate there: "
                     "construction SUCCEEDS at both flag values and the recorded "
                     "field DIFFERS between them (`true`↦true, `false`↦false), so "
                     "the obligation is neither a forced refusal (else the accept "
                     "behaviour would be unreachable) nor a constant collapse of "
                     "the recorded flag. The in-region assert must discharge; the "
                     "impl is kept verbatim so the method's own `ensures` "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P test. Each rival is a
    # loop-free branch; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-refuse-when-requested",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix defect: the estimator does NOT support the option, so
        # requesting retention (`true`) is refused instead of accepted. Correct
        # when retention is not requested (`false` -> Except.ok either way); wrong
        # exactly at `true`, the F2P-relevant input. Attacks the ACCEPT
        # sub-behaviour.
        "module": _impl(
            "    let acceptsStore : Bool := false\n"
            "    if storeCvValues && !acceptsStore then\n"
            "      return Except.error InitErr.storeNotAccepted\n"
            "    else\n"
            "      return Except.ok { storeCvValues := storeCvValues }"),
        "refinement": "this IS the pre-fix reality: the constructor does not "
                      "expose the retention option, so requesting it raises rather "
                      "than building the estimator — the exact failure the public "
                      "issue reports. The failing F2P test constructs the "
                      "estimator WITH retention requested and then reads the "
                      "retained-values attribute after a fit; a patch that refused "
                      "that construction never gets past instantiation, so the "
                      "test still errors and it would NOT resolve.",
        "rationale": "REJECT from `out = construct true storeCvValues` via the "
                     "ACCEPT sub-behaviour: the post-image (capability `true`) "
                     "always succeeds, but the rival (capability `false`) refuses "
                     "when the flag is `true`, so `Except.error … ≠ Except.ok …`. "
                     "Refuted at storeCvValues = true (the F2P input). Verifying "
                     "would be SPEC-TOO-WEAK.",
        "witness": _witness("true"),
    },
    {
        "id": "weak-record-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Always succeeds (correct ACCEPT) but records a CONSTANT `true`,
        # ignoring the requested flag. Correct when the caller requested `true`;
        # wrong exactly at `false`. Attacks the RECORD sub-behaviour, and — being
        # correct at `true` — forces the witness to probe the binder at `false`,
        # the value the ACCEPT rival above cannot discriminate.
        "module": _impl(
            "    return Except.ok { storeCvValues := true }"),
        "refinement": "hard-coding the recorded option to `true` ignores the "
                      "caller's request, the mirror of the pre-fix constructor "
                      "that never recorded it at all. A later fit reads the "
                      "recorded option to decide whether to populate the "
                      "retained-values attribute; an estimator built WITHOUT "
                      "requesting retention would spuriously retain, and the "
                      "broader estimator contract (the requested value must echo "
                      "back on the instance, exercised by the estimator-check "
                      "suite / P2P) would break, so it would NOT resolve.",
        "rationale": "REJECT from `out = construct true storeCvValues` via the "
                     "RECORD sub-behaviour: the post-image records the requested "
                     "flag verbatim, but the rival records a constant `true`, so "
                     "at `false` the recorded fields differ "
                     "(`{storeCvValues := true} ≠ {storeCvValues := false}`). "
                     "Refuted at storeCvValues = false — the binder value the "
                     "ACCEPT rival cannot expose. Verifying would be "
                     "SPEC-TOO-WEAK (the recorded flag is unpinned).",
        "witness": _witness("false"),
    },
    {
        "id": "weak-record-negated",
        "kind": "uniqueness",
        "expect": "reject",
        # Always succeeds (correct ACCEPT) but records the NEGATION of the
        # requested flag. Wrong on BOTH inputs; refuted at `true` (records
        # `false`). Attacks the RECORD sub-behaviour from the other side — the
        # negation, not a constant.
        "module": _impl(
            "    return Except.ok { storeCvValues := !storeCvValues }"),
        "refinement": "recording the negation of the requested option is the "
                      "opposite of forwarding it unchanged: the estimator would "
                      "retain iff the caller asked it NOT to. The failing F2P test "
                      "requests retention (`true`) and asserts the retained-values "
                      "attribute is populated after a fit; with the flag negated "
                      "the fit reads `false` and never populates it, so the "
                      "attribute read fails and it would NOT resolve.",
        "rationale": "REJECT from `out = construct true storeCvValues` via the "
                     "RECORD sub-behaviour: the post-image records the requested "
                     "flag, the rival records its negation, so the recorded fields "
                     "differ for every input. Refuted at storeCvValues = true "
                     "(records `false` where the post-image demands `true`). "
                     "Verifying would be SPEC-TOO-WEAK.",
        "witness": _witness("true"),
    },
    {
        "id": "weak-capability-from-request",
        "kind": "uniqueness",
        "expect": "reject",
        # Consults the pure model but with the two arguments TRANSPOSED: it reads
        # the requested flag as the capability and the capability as the request.
        # This is the one rival that reaches the obligation through `construct`
        # itself rather than by inlining a branch, so it attacks the binding of
        # the binder to the request POSITION — the sub-behaviour the other three
        # rivals leave unattacked (they all keep the flag in the right slot and
        # corrupt its value). Wrong at `false`: it refuses (capability read as
        # `false` while the request is read as `true`) where the post-image
        # succeeds and records `false`.
        "module": _impl("    return construct storeCvValues true"),
        "refinement": "transposing the capability and the request makes the "
                      "construction consult the caller's own argument to decide "
                      "whether the option is supported, and then record the "
                      "capability instead of the request. A patch shaped like "
                      "that refuses construction whenever retention is NOT "
                      "requested, so the default-constructed estimator every "
                      "other test builds raises at instantiation; the failing "
                      "test would pass while a large part of the surrounding "
                      "suite (P2P) breaks, so it would NOT resolve.",
        "rationale": "REJECT from `out = construct true storeCvValues`: the "
                     "post-image fixes the capability at `true` and lets only the "
                     "REQUEST vary, but the rival makes the capability vary with "
                     "the request. At storeCvValues = false the rival yields "
                     "`Except.error …` where the post-image demands "
                     "`Except.ok { storeCvValues := false }`. Refuted at "
                     "storeCvValues = false. Verifying would be SPEC-TOO-WEAK "
                     "(the argument POSITIONS would be unpinned).",
        "witness": _witness("false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane. The
# sibling models TWO functions over a heap carrier with fractional permissions:
#   * configure_classifier_cv(flag) -> EngineConfig, whose load-bearing post is
#     `Result().retain_values == store_cv_values` (the flag-forwarding);
#   * stored_cv_values(cfg, n_samples, n_targets, n_alphas) -> Optional[CvRecord],
#     whose posts pin the None/not-None control flow to the flag AND the rank-3
#     shape with the three axes.
#
# This velvet bundle models ONLY the purely-functional CONSTRUCTION core (the
# single contracted method `initEstimator`, `ensures out = construct true
# storeCvValues`) — accept-when-supported + record-the-flag-faithfully. The
# rank/shape record behaviour (`stored_cv_values`, the `CvRecord` axes) is the
# downstream `fit`-side behaviour and is NOT modeled on this carrier (mapping.md
# §2: only the recorded option is behaviourally constrained; every other aspect
# is orthogonal). So the nagini cases attached to `stored_cv_values`'s
# rank/shape/None-flow clauses have NO counterpart here — this is carrier
# narrowing, not an omission of a modeled behaviour, and chasing parity would
# mean fabricating rivals for a behaviour this bundle does not contract.
#
#   sibling case                      -> here                            status
#   ---------------------------------------------------------------------------
#   pos-control-reordered-branch      -> pos-drop-dead-refuse-branch      PORTED
#   (no sibling)                      -> pos-construct-direct             ADDED
#   (no sibling)                      -> pos-branch-on-flag-literals      ADDED (audit)
#   admissibility-f2p-binary-boundary -> admiss-f2p-flag-reachable        PORTED (re-aimed)
#   uniqueness-ignore-requested-flag  -> weak-record-constant-true        PORTED
#   uniqueness-negate-requested-flag  -> weak-record-negated              PORTED
#   (no sibling)                      -> weak-refuse-when-requested        ADDED
#   (no sibling)                      -> weak-capability-from-request      ADDED (audit)
#   frame-mutation-write-cfg          -> (none, VACUOUS)                  DROPPED
#   partial-domain-binary-collapse    -> (none, unmodeled: rank/shape)    DROPPED
#   control-flow-retention-inverted   -> (none, unmodeled: None-flow)     DROPPED
#   uniqueness-rank-two-everywhere     -> (none, unmodeled: rank)          DROPPED
#   AXIOM_TESTS ([])                   -> (none)                           DROPPED (G-AX)
#
# PORTED (positive): pos-control-reordered-branch is a structurally-different
#   CORRECT reshape. Here the equivalent reshape drops the (dead, capability=true)
#   refuse branch and unconditionally builds+records; observationally identical,
#   frozen proof closes.
# PORTED-RE-AIMED (admissibility): the sibling calls stored_cv_values on the F2P
#   binary boundary and asserts the record is reachable/non-degenerate (non-None,
#   rank 3, axes pinned). This backend has no precondition to satisfy and no
#   record axes; the re-aimed probe asserts construction SUCCEEDS at the
#   F2P-relevant input (retention requested) AND the recorded flag differs between
#   the two inputs (genuine carry-through, not a constant collapse or a forced
#   refusal).
# PORTED (rivals): uniqueness-ignore-requested-flag (constant-True forwarding) ->
#   weak-record-constant-true; uniqueness-negate-requested-flag -> weak-record-
#   negated. Both port DIRECTLY — the flag-forwarding clause is exactly the RECORD
#   sub-behaviour of `construct true storeCvValues`. Each carries a machine-checked
#   witness that ELABORATES against the rival and FAILS against gold (two real
#   builds per case).
# ADDED (weak-refuse-when-requested): the sibling's flag-forwarding clause lives
#   in configure_classifier_cv and assumes construction always SUCCEEDS (the
#   sibling's `EngineConfig(...)` never refuses). On THIS carrier the construction
#   outcome itself (accept vs refuse) is the FIRST leg the desired behaviour pins,
#   and the pre-fix reality was a REFUSAL when the option was requested (the
#   TypeError the issue reports). A rival with capability=false is the faithful
#   model of that defect and the ONLY rival that attacks the ACCEPT
#   sub-behaviour; it is refuted at `true`, the exact F2P input. Not a fabricated
#   wrongness — it is the pre-patch behaviour with a machine-checked witness.
# ADDED (pos-construct-direct): a second honest positive control (return the pure
#   model directly) so the obligation is defended by more than one impl shape.
# ADDED-BY-AUDIT (pos-branch-on-flag-literals): the two positives above both close
#   under a script within one tactic of the frozen body, so neither demonstrates
#   that the obligation survives a reshape the frozen script genuinely does NOT
#   close. This one does (measured: `loom_solve; simp [construct]` leaves
#   `⊢ storeCvValues = true` and `⊢ Except.ok { storeCvValues := false } =
#   construct true storeCvValues`), and it verifies once the elided tactic body
#   substitutes the branch hypothesis. Two further correct reshapes (`match` on
#   the binder; a `:|` choice constrained to `v = storeCvValues`) were also built
#   and both VERIFY, so the SPEC-TOO-STRONG direction is clean on this carrier.
# ADDED-BY-AUDIT (weak-capability-from-request): all three ported/added rivals
#   keep the requested flag in the request POSITION and corrupt only its value
#   (constant, negated) or the capability constant. None probes the binding of the
#   binder to the argument it occupies in `construct true storeCvValues`. A rival
#   that transposes the capability and the request closes that gap and is refuted
#   at `false`. Its witness was built four times (rival 0 / gold 1 with
#   `unsolved goals ⊢ False`, and the flipped-claim forgery gold 0 / rival 1), so
#   gold's exit code tracks the CLAIM and not the tactic shape.
# DROPPED (frame-mutation-write-cfg): Nagini-specific (fractional heap
#   permission on `cfg`). This backend is referentially transparent and declares
#   no `mut` binder — `storeCvValues` is an immutable value with no heap footprint
#   — so there is no read-only field to overwrite and no substitute probe. VACUOUS;
#   not fabricated (porting map).
# DROPPED (partial-domain-binary-collapse, control-flow-retention-inverted,
#   uniqueness-rank-two-everywhere): all three attack `stored_cv_values`'s posts
#   (the rank-3 shape, the three axes, the None/not-None control flow). That
#   function and its record carrier are NOT modeled by this bundle — the velvet
#   surface contracts only the construction/record core, over a `Bool` with no
#   `CvRecord`, no rank, no axes, no Optional. There is no clause on this carrier
#   for these rivals to violate, and inventing a record model to host them would
#   mean specifying a behaviour this bundle does not contract. Dropped as carrier
#   narrowing, not because they were hard.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the construction is a concrete `def`),
#   so there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 2 distinct input
# points — the whole input domain, since the sole binder is a `Bool`):
#     storeCvValues — probed at BOTH true (weak-refuse-when-requested,
#       weak-record-negated) and false (weak-record-constant-true,
#       weak-capability-from-request), so no value of the sole binder is held
#       fixed across the battery.
#   Both top-level sub-behaviours of `out = construct true storeCvValues` are
#   attacked: ACCEPT (weak-refuse-when-requested) and RECORD
#   (weak-record-constant-true from the constant side, weak-record-negated from
#   the negation side), plus the ARGUMENT-POSITION binding of the binder to the
#   request slot (weak-capability-from-request). Three positive controls defend
#   the whole obligation, one of them (pos-branch-on-flag-literals) under a proof
#   the frozen script does not close; the admissibility case pins reachability +
#   non-degeneracy at the F2P input, and its assert is LIVE (falsifying the
#   asserted equations leaves `⊢ False` — measured). The binder domain being
#   {true, false}, pts=2 is the MAXIMUM attainable here — it is not a coverage
#   gap.
#
# AUDIT-LANE probes that did NOT find a hole (built, all behaved): wrong impls
#   `construct true true` (input ignored), `Except.ok { storeCvValues := false }`,
#   `Except.error` unconditionally, refuse-at-false, refuse-at-true, and a `:|`
#   choice left free over the recorded flag — every one REJECTED, so the
#   SPEC-TOO-WEAK direction found nothing beyond what the rivals above already
#   pin. The `derive_tester_for` witness route was re-measured and confirmed
#   unavailable here: the postcondition-decidability obligation over
#   `Except InitErr EstimatorState` is left unsolved and `decide` reports
#   `did not reduce to isTrue or isFalse` identically on BOTH the rival and the
#   frozen solution, which is why every witness uses `extract_program_for`.
AXIOM_TESTS = []
