"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25102 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC_TESTS entry is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
``theorem correct_transform`` STATEMENT stays byte-identical). ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled observable of a column-reduction step):

  transform (isDataFrame outputPandas : Bool) (cols : List Column)
            (nRows commonDtype : Nat) (mask : List Bool) : TransformResult
      result.nRows = nRows
      ∧ result.cols =
          selectByMask
            (if isDataFrame && outputPandas then cols else castAll cols commonDtype)
            mask

  A column-reduction step takes a sequence of columns (each with its own
  identity ``name`` and element type ``dtype``) plus a per-column selection
  vector ``mask``, and returns the surviving columns and the row count. The
  output row count is ALWAYS the input row count. The surviving columns are the
  by-flag selection taken from EITHER the columns exactly as given (when the
  input is a native container AND native-container output is requested — the two
  gate booleans both hold) OR from a homogenised block in which every column has
  been coerced to one common element type ``commonDtype`` (otherwise). The two
  helpers are fully-grounded pure ``def``s: ``selectByMask`` pairs each column
  with its flag and keeps the flagged ones in input order; ``castAll`` maps every
  column's element type to ``commonDtype`` while preserving identities.

  The single conjunctive clause pins FOUR independent behavioral faces:
    (row-count)     ``result.nRows = nRows`` — the row count is preserved, for
                    any selected-count including zero.
    (per-column)    on the native-container path a surviving column keeps its OWN
                    element type ``dtype`` — never coerced to the shared
                    ``commonDtype``; the gate boolean pair decides which of the
                    two blocks the selection is taken from.
    (keep-set)      a column contributes to the output iff its selection flag is
                    set; a dropped column contributes nothing.
    (order)         surviving columns appear in INPUT column order.

  Nothing in the result is left unconstrained: both output components are pinned
  entirely to the inputs (``cols``, ``mask``, ``commonDtype``, ``nRows``, and the
  two gate booleans). The post-image is a total function of those inputs — there
  is no opaque callee and no answer-key to echo (``axioms`` region empty, no
  ``opaque``), so the carrier is fully transparent and every reject witness is a
  plain ``decide`` at a concrete input.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's MANDATORY
    frame-mutation rival wrote into the read-only input container
    (``df.descs[i-1] = d``) held at half permission (``Acc(list_pred(df.descs),
    1/2)``) and relied on Viper to reject the store for INSUFFICIENT PERMISSION.
    Lean is referentially transparent: ``cols``/``mask`` are passed by value,
    there is no heap, no aliasing, and no fractional permission to overflow. The
    class has no expressible instance here and no substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS as a spec defect. The postcondition equates
    the result to terms built ONLY from the inputs and two pure ``def``s
    (``selectByMask``, ``castAll``); the bundle declares no ``opaque``/``axiom``
    (both the homogenise-or-keep decision and the by-flag selection are modeled
    deeply, not axiomatized), so there is no opaque answer-key an impl could echo.
    Its slot is filled by the honest positive controls.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not vacuous. Measured on audit,
    because "a non-terminating implementation cannot be written at all" is not
    quite true: a diverging impl IS writable here as ``partial def spin (n : Nat)
    : TransformResult := spin (n + 1)`` once ``TransformResult`` is given an
    ``Inhabited`` instance (without one, ``partial`` is refused outright — exit 1,
    ``failed to compile 'partial' definition``). With the instance the file
    elaborates as far as the obligation and is REJECTED (exit 1) — but the
    rejection is not attributable to the spec, and no witness can make it so: a
    ``partial def`` is compiled to an opaque constant with no equation lemmas, so
    the refutation does not reduce. Measured, four tactics against the diverging
    rival, all exit 1: ``decide`` -> ``Tactic `decide` failed for proposition``;
    ``decide +kernel`` -> same; ``unfold … spin`` -> ``Tactic `unfold` failed to
    unfold `spin```; ``simp [spin]`` -> ``unsolved goals``. So the class is
    recorded as a HOLE (the spec does not itself refute divergence; the carrier's
    totality discipline is what does) rather than as vacuous, and no case is
    shipped for it. Note the ``partial`` route is independently barred from a
    witness by ``pbt_witness``, which bans the token.

  * PARTIAL-DOMAIN / VALUE — the real attacks, and they port directly. The nagini
    per-column HOMOGENISATION rival (stamp every kept column with column 0's
    descriptor) re-expresses as the always-homogenise rival on the (per-column)
    face; the nagini MASK-SUBDOMAIN force-keep rival re-expresses as force-keep on
    the (keep-set) face. One rival is ADDED for the (order) face and one for the
    (row-count) face (the nagini positional-reindex rival's counterpart — see
    below).

  * GATE-SHAPE — added on audit. The (per-column) face is decided by a
    CONJUNCTION of the two gate booleans, and a rival that reads it as a
    DISJUNCTION agrees with the spec at both flag pairs the other witnesses sit
    at (`true true`, `false false`), diverging only on the MIXED pairs. Without a
    witness on a mixed pair, nothing in the battery attests that the gate is `&&`
    rather than `||` — the `disjunctive-gate` rival closes that.

  * COLUMN IDENTITY — added on audit. Every other witness leaves each column's
    `name` at its input value (mostly 0), so the identity half of a retained
    column is never observable: an impl that discarded `name` while keeping
    `dtype` was unattacked. The `clobber-column-identity` rival closes that, with
    the only witness placing a `name` at a non-zero value.

  * SHAPE CONFLATION and MASK/COLUMN LENGTH — added on a second audit pass, both
    from wrong impls the battery did not previously contain. (i) The (row-count)
    face was probed only on the all-clear-mask branch, so an impl recomputing
    `nRows` from the surviving-column count on the branch that RETURNS columns
    verified against every existing witness; `nrows-from-selected-count` closes
    it. (ii) Every existing witness passes `mask.length = cols.length`, so the
    truncating `zip` inside `selectByMask` was never load-bearing and an impl
    that defaulted an unflagged column to KEPT was unattacked;
    `pad-mask-keep-unflagged` closes it with the battery's only ragged input.

CASE-COUNT vs NAGINI. The nagini sibling contracts ONE procedure
(``select_columns``) returning a whole ``Frame`` and pins TWO postcondition
clauses (per-column descriptors AND the row index) over a ``List[int]`` carrier
with fractional-permission framing. This lean bundle models the SAME single
observable — the column-reduction transform — but its ``TransformResult`` carries
the per-column list AND a row COUNT (``nRows``), and adds the two gate booleans
that decide the preserve-vs-homogenise mode (the actual content of the fix). So
the nagini descriptor clause maps onto the (per-column)+(keep-set)+(order) faces
of ``result.cols``, and the nagini index clause maps onto the (row-count) face of
``result.nRows`` (this backend models the ROW COUNT, not per-row labels — see
``assessment``). Carrier remodeling, not effort gaps.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate at one concrete,
``decide``-able input; each was checked (``scripts/lean_verify.sh``) to ELABORATE
against its rival (the rival provably contradicts the spec there) and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). The carrier is fully transparent, so no witness binds a hypothesis
and there is no joint-satisfiability obligation. No ``sorry``/``admit``/
``native_decide``/``axiom`` appears in any variant or witness.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``;
there is no consumed axiom and no deep-model reference to validate against a real
callee here. The axiom lane belongs to G-AX in any case and this gate ignores
nagini's AXIOM_TESTS.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25102"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region def (the `implementation_transform` body) and the FULL
# proof-region tactic body. Every replacement lands entirely inside the region it
# means to edit, so `same_spec` holds and the theorem STATEMENT is untouched.
_IMPL = (
    "def implementation_transform\n"
    "    (isDataFrame outputPandas : Bool)\n"
    "    (cols : List Column) (nRows commonDtype : Nat) (mask : List Bool)\n"
    "    : TransformResult := Id.run do\n"
    "  -- Keep the input as a native container when it already is one and native\n"
    "  -- output is requested; otherwise homogenise it into one numeric block first.\n"
    "  let keepNative := isDataFrame && outputPandas\n"
    "  let mut block := cols\n"
    "  if !keepNative then\n"
    "    block := castAll cols commonDtype\n"
    "  -- Select the flagged columns.\n"
    "  let selected := selectByMask block mask\n"
    "  if !(mask.any id) then\n"
    "    -- Nothing selected: zero columns, row count preserved.\n"
    "    return { cols := [], nRows := nRows }\n"
    "  return { cols := selected, nRows := nRows }"
)

# Sub-anchors WITHIN the impl body (each unique in the file), used by the rivals
# so the surrounding gold reasoning is otherwise preserved.
_HOMOG_GATE = (
    "  let keepNative := isDataFrame && outputPandas\n"
    "  let mut block := cols\n"
    "  if !keepNative then\n"
    "    block := castAll cols commonDtype"
)
_SELECT = "  let selected := selectByMask block mask"
_RET_EMPTY = "    return { cols := [], nRows := nRows }"
_RET_SELECTED = "  return { cols := selected, nRows := nRows }"

_PROOF = (
    "  intro isDataFrame outputPandas cols nRows commonDtype mask\n"
    "  unfold problem_spec_transform implementation_transform\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : mask.any id\n"
    "  · -- something selected: both sides agree\n"
    "    by_cases hk : isDataFrame && outputPandas <;>\n"
    "      simp [h, hk]\n"
    "  · -- nothing selected: selectByMask block mask = []\n"
    "    have hempty : ∀ block : List Column, selectByMask block mask = [] := by\n"
    "      intro block\n"
    "      unfold selectByMask\n"
    "      have hfm : ∀ p ∈ block.zip mask, (if p.2 then some p.1 else none) = (none : Option Column) := by\n"
    "        intro p hp\n"
    "        have hp2 : p.2 ∈ mask := (List.of_mem_zip hp).2\n"
    "        have hpf : p.2 = false := by\n"
    "          by_contra hne\n"
    "          have htrue : p.2 = true := by cases p.2 <;> simp_all\n"
    "          rw [List.any_eq_true] at h\n"
    "          exact h ⟨p.2, hp2, by simp [htrue]⟩\n"
    "        simp [hpf]\n"
    "      rw [List.filterMap_eq_nil_iff.mpr hfm]\n"
    "    by_cases hk : isDataFrame && outputPandas <;>\n"
    "      simp [h, hk, hempty]"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"
assert _BASE.count(_HOMOG_GATE) == 1, "homogenise-gate anchor drifted"
assert _BASE.count(_SELECT) == 1, "select anchor drifted"
assert _BASE.count(_RET_EMPTY) == 1, "empty-return anchor drifted"
assert _BASE.count(_RET_SELECTED) == 1, "selected-return anchor drifted"


# Reject witnesses state the spec predicate directly at a concrete input; the
# carrier computes, so `decide` closes the residual after unfolding.
def _witness(args: str) -> str:
    return (
        f"example : ¬ problem_spec_transform {args}\n"
        f"    (implementation_transform {args}) := by\n"
        f"  unfold problem_spec_transform implementation_transform\n"
        f"  simp only [Id.run, bind, pure]\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations / proofs that MUST verify. If a faithful
    # correct implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-control-direct-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest HONEST impl: drop the imperative `Id.run do` scaffolding and
        # return the grounded post-image directly as a record literal. Genuinely
        # performs the modeled preserve-or-homogenise decision then the by-flag
        # selection (the empty-mask early return is subsumed — `selectByMask`
        # already yields `[]` when every flag is clear). The loop is gone, so the
        # residual goal closes under `exact ⟨rfl, rfl⟩`.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def implementation_transform\n"
                "    (isDataFrame outputPandas : Bool)\n"
                "    (cols : List Column) (nRows commonDtype : Nat) (mask : List Bool)\n"
                "    : TransformResult :=\n"
                "  { cols := selectByMask\n"
                "              (if isDataFrame && outputPandas then cols else castAll cols commonDtype) mask,\n"
                "    nRows := nRows }",
            ),
            _PROOF,
            "  intro isDataFrame outputPandas cols nRows commonDtype mask\n"
            "  unfold problem_spec_transform implementation_transform\n"
            "  exact ⟨rfl, rfl⟩",
        ),
        "rationale": "the post-image is GROUNDED in the inputs (both output "
                     "components are total functions of `cols`, `mask`, "
                     "`commonDtype`, `nRows`, and the gate booleans — no opaque "
                     "answer key), so the closed-form record literal is the honest "
                     "cheapest CORRECT impl. It MUST verify — the clause is "
                     "literally `result.nRows = nRows ∧ result.cols = selectByMask "
                     "(if …) mask` — else the postcondition is SPEC-TOO-STRONG. Also "
                     "shows the spec is not echo-vulnerable: any wrong "
                     "constant/echo fails the equality. Proof is `exact ⟨rfl, rfl⟩` "
                     "with no new lemma, axiom, or `sorry`.",
    },
    {
        "id": "pos-control-if-block-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT reshape that keeps the imperative
        # `Id.run do` skeleton and the empty-mask early return byte-identical:
        # the mutable "start from cols, conditionally overwrite" block is
        # rewritten as a single `let block := if … then cols else castAll …`
        # expression. Same value on every input; the frozen proof discharges the
        # identical obligation unchanged (both compute `block` to the same term
        # the gold `by_cases hk` split reasons about).
        "module": _swap(
            _BASE, _HOMOG_GATE,
            "  let block := if isDataFrame && outputPandas then cols "
            "else castAll cols commonDtype",
        ),
        "rationale": "a correct reshape (the mutable homogenise-or-keep block "
                     "rewritten as one `if`-expression, keeping the `Id.run do` "
                     "loop and the empty-mask early return byte-identical) computes "
                     "the same `block` on every input, so both conjuncts still "
                     "discharge under the frozen proof. A faithful reshape MUST "
                     "verify, else the clause is over-fit to the imperative FORM of "
                     "the decision => SPEC-TOO-STRONG. Theorem statement "
                     "byte-identical; no new lemma, axiom, or `sorry`.",
    },
    {
        "id": "pos-control-commuted-gate",
        "kind": "soundness",
        "expect": "verify",
        # The reshape-not-wrong trap in its sharpest form: the gate's two
        # conjuncts are COMMUTED (`outputPandas && isDataFrame`). Observationally
        # identical to the frozen impl on every input, but NOT definitionally so
        # — the frozen tactic script fails on it (measured: `unsolved goals`,
        # residual `if outputPandas = true ∧ isDataFrame = true …`), which is
        # exactly how a merely-reshaped correct rival is indistinguishable from a
        # wrong one on this backend. It is admitted here as a POSITIVE, with the
        # gate split rewritten to case on both booleans so the reshaped condition
        # reduces; the empty-mask reasoning is carried over verbatim.
        "module": _swap(
            _swap(
                _BASE, _HOMOG_GATE,
                "  let block := if outputPandas && isDataFrame then cols "
                "else castAll cols commonDtype",
            ),
            _PROOF,
            "  intro isDataFrame outputPandas cols nRows commonDtype mask\n"
            "  unfold problem_spec_transform implementation_transform\n"
            "  simp only [Id.run, bind, pure]\n"
            "  by_cases h : mask.any id\n"
            "  · cases isDataFrame <;> cases outputPandas <;> simp [h]\n"
            "  · have hempty : ∀ block : List Column, selectByMask block mask = [] := by\n"
            "      intro block\n"
            "      unfold selectByMask\n"
            "      have hfm : ∀ p ∈ block.zip mask, (if p.2 then some p.1 else none) = (none : Option Column) := by\n"
            "        intro p hp\n"
            "        have hp2 : p.2 ∈ mask := (List.of_mem_zip hp).2\n"
            "        have hpf : p.2 = false := by\n"
            "          by_contra hne\n"
            "          have htrue : p.2 = true := by cases p.2 <;> simp_all\n"
            "          rw [List.any_eq_true] at h\n"
            "          exact h ⟨p.2, hp2, by simp [htrue]⟩\n"
            "        simp [hpf]\n"
            "      rw [List.filterMap_eq_nil_iff.mpr hfm]\n"
            "    cases isDataFrame <;> cases outputPandas <;> simp [h, hempty]",
        ),
        "rationale": "a CORRECT reshape whose difference from the frozen impl is "
                     "not definitional: commuting the gate's two conjuncts breaks the "
                     "frozen `by_cases hk : isDataFrame && outputPandas` split, so the "
                     "frozen script leaves the residual goal open even though the impl "
                     "agrees with the spec everywhere. Re-proven by casing on both "
                     "booleans instead. This is the positive control that matters most "
                     "on a tactic-proof backend: if a faithful impl differing only in "
                     "the ORDER of a commutative test could not be proven at all, the "
                     "obligation would be over-fit to the frozen syntactic form => "
                     "SPEC-TOO-STRONG. Statement byte-identical; no new lemma, axiom, "
                     "or `sorry` — only the tactic body differs.",
    },
    {
        "id": "admiss-ground-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen theorem has no precondition hypothesis to admit (every input
        # is total by typing); the honest analogue of the nagini
        # precondition-admission probe is to discharge the spec at a ground,
        # F2P-shaped input — a native-container/pandas-output frame of two
        # distinct-dtype columns with a mixed mask, the exact mixed-dtype case the
        # issue reports — by evaluation, alongside the frozen obligation closed
        # verbatim.
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_transform true true\n"
            "      [{ name := 0, dtype := 1 }, { name := 1, dtype := 2 }] 3 9 [true, false]\n"
            "      (implementation_transform true true\n"
            "        [{ name := 0, dtype := 1 }, { name := 1, dtype := 2 }] 3 9 [true, false]) := by\n"
            "    unfold problem_spec_transform implementation_transform\n"
            "    simp only [Id.run, bind, pure]\n"
            "    decide\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input "
                     "(a native-container frame with pandas output, two "
                     "distinct-element-type columns and a mixed selection vector — "
                     "the mixed-dtype case the issue reports) by `decide`, then the "
                     "frozen obligation is closed verbatim. Verifies (else the spec "
                     "is unsatisfiable at the normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, the ground instance "
                     "is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete, decide-able input. The frozen (gold) proof body is retained
    # in each rival; against the reshaped/wrong impl it fails to close, so the
    # case does NOT verify — the witness is what attributes the rejection to the
    # spec rather than to tactic breakage.
    # =====================================================================
    {
        "id": "always-homogenise",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix baseline: drop the gate entirely and ALWAYS homogenise the
        # block to the common element type before selecting, so even on the
        # native-container/pandas-output path every surviving column carries
        # `commonDtype` rather than its own type. Correct on every path EXCEPT
        # `isDataFrame && outputPandas` with a retained column whose type differs
        # from `commonDtype`.
        "module": _swap(
            _BASE, _HOMOG_GATE,
            "  let block := castAll cols commonDtype",
        ),
        "refinement": "unconditionally homogenising the block to one common "
                      "element type is exactly the pre-fix behaviour where the "
                      "input is always coerced to a single homogeneous numeric "
                      "block before selection, so every surviving column emerges "
                      "with the shared common type. On a native container with "
                      "native output requested (the case the fix adds) a "
                      "heterogeneous selection (e.g. the issue's mixed float "
                      "precisions + a categorical column) collapses to one type; "
                      "the failing tests assert each output column keeps its input "
                      "element type, so it would NOT resolve.",
        "rationale": "REJECT from `result.cols = selectByMask (if isDataFrame && "
                     "outputPandas then cols else castAll cols commonDtype) mask` "
                     "(per-column face): the gate selects `cols` (own types) on the "
                     "preserve path, but the rival always takes `castAll cols "
                     "commonDtype` (shared type), so they differ whenever a retained "
                     "column's type differs from `commonDtype`. Refuted at "
                     "`true true [col(name 0,dtype 1)] 3 2 [true]`: the rival yields "
                     "a column with dtype 2, the spec keeps dtype 1. Varies "
                     "`isDataFrame`/`outputPandas` to the preserve mode and puts a "
                     "retained dtype distinct from `commonDtype`.",
        "witness": _witness("true true [{ name := 0, dtype := 1 }] 3 2 [true]"),
    },
    {
        "id": "force-keep-leading-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Force-keep the leading column regardless of its selection flag, then
        # select the rest correctly — so a column whose flag is CLEAR is wrongly
        # retained in the leading position. Attacks the keep-set face.
        "module": _swap(
            _BASE, _SELECT,
            "  let selected := match block, mask with\n"
            "    | c :: cs, _ :: ms => c :: selectByMask cs ms\n"
            "    | _, _ => selectByMask block mask",
        ),
        "refinement": "force-keeping the leading column regardless of its "
                      "selection flag retains a column the selector dropped, so the "
                      "output carries an extra leading column (with the wrong "
                      "element type and position). On a fixture where the selector "
                      "drops the first feature, the output columns and their "
                      "per-column types no longer match the selected set; the "
                      "failing tests check exactly the retained columns and their "
                      "types, so it would NOT resolve.",
        "rationale": "REJECT from `result.cols = selectByMask … mask` (keep-set "
                     "face): `selectByMask` keeps a column iff its flag is set; the "
                     "rival includes the leading column even when its flag is clear, "
                     "so the output has an extra leading column on that sub-domain. "
                     "Refuted at `true true [col(0,5),col(1,6)] 5 9 [false, true]`: "
                     "the rival yields two columns, the spec yields one. Puts the "
                     "leading `mask` entry at `false` while a LATER entry is `true` — "
                     "the only witness on a mask that is mixed (partly set, partly "
                     "clear), which is what makes a wrongly-retained leading column "
                     "observable alongside a correctly-retained trailing one.",
        "witness": _witness(
            "true true [{ name := 0, dtype := 5 }, { name := 1, dtype := 6 }] "
            "5 9 [false, true]"),
    },
    {
        "id": "reverse-selected-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Select the RIGHT columns with the RIGHT types, but emit them in reversed
        # input order — a positional re-ordering of the projection. Attacks the
        # order face.
        "module": _swap(
            _BASE, _SELECT,
            "  let selected := (selectByMask block mask).reverse",
        ),
        "refinement": "emitting the surviving columns in reversed order keeps the "
                      "correct column set and per-column types but scrambles their "
                      "positions, so the projection's column order no longer matches "
                      "the input's. The failing tests assert the output columns line "
                      "up, in order, with the selected input columns (e.g. an "
                      "expected `[petal length, petal width, …]` ordering), so a "
                      "faithful counterpart that reordered the retained columns "
                      "would NOT resolve.",
        "rationale": "REJECT from `result.cols = selectByMask … mask` (order face): "
                     "`selectByMask` emits contributions in INPUT column order; the "
                     "rival reverses them, so they differ whenever two or more "
                     "distinct columns are retained. Refuted at "
                     "`true true [col(0,7),col(1,8)] 2 4 [true, true]`: the rival "
                     "yields dtypes `[8,7]`, the spec `[7,8]`. Varies the retained "
                     "types across two kept columns so order is observable.",
        "witness": _witness(
            "true true [{ name := 0, dtype := 7 }, { name := 1, dtype := 8 }] "
            "2 4 [true, true]"),
    },
    {
        "id": "drop-row-count-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # On the no-features-selected branch, return a row count of 0 instead of
        # the preserved input row count — the counterpart of the nagini
        # positional-reindex rival, which dropped the input's own row labels.
        # Attacks the row-count face on the empty-mask sub-domain.
        "module": _swap(
            _BASE, _RET_EMPTY,
            "    return { cols := [], nRows := 0 }",
        ),
        "refinement": "returning a zeroed row count on the no-features-selected "
                      "branch drops the input's own row dimension — the counterpart "
                      "of dropping the DataFrame's row index on the empty selection. "
                      "The failing empty-selection case asserts the output keeps the "
                      "input row dimension (its shape is `(n_rows, 0)`, the row "
                      "index preserved); a zeroed row count fails that assertion, so "
                      "it would NOT resolve.",
        "rationale": "REJECT from `result.nRows = nRows` (row-count face): the "
                     "output row count must equal the input's for ANY selected "
                     "count including zero, but the rival returns 0 on the empty "
                     "branch. Refuted at `false false [col(0,1)] 7 2 [false]` — the "
                     "empty-mask sub-domain with a non-zero input row count: the "
                     "rival yields `nRows = 0`, the spec `nRows = 7`. The only "
                     "witness on the all-clear mask, and the only one in the "
                     "homogenise mode with BOTH gate booleans clear — the sub-domain "
                     "where the result must still carry the input row count with zero "
                     "surviving columns.",
        "witness": _witness("false false [{ name := 0, dtype := 1 }] 7 2 [false]"),
    },
    {
        "id": "disjunctive-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Preserve the columns' own element types whenever EITHER gate boolean
        # holds, instead of only when BOTH do. Agrees with the spec on the two
        # points every other rival's witness sits at (`true true` and
        # `false false`) and diverges exactly on the MIXED flag combinations, so
        # it is the rival that makes the conjunction itself load-bearing.
        "module": _swap(
            _BASE, _HOMOG_GATE,
            "  let keepNative := isDataFrame || outputPandas\n"
            "  let mut block := cols\n"
            "  if !keepNative then\n"
            "    block := castAll cols commonDtype",
        ),
        "refinement": "preserving each column's own element type when only ONE of "
                      "the two conditions holds skips the homogenisation on inputs "
                      "that are not native containers, or whose requested output is "
                      "not the native container form. Those paths are the unchanged "
                      "ones: they must still go through the coercion to a single "
                      "homogeneous numeric block, and a caller on them receives "
                      "columns typed differently from what that path guarantees. Only "
                      "the both-conditions case may skip it, so a faithful "
                      "counterpart with a disjunctive gate would NOT resolve.",
        "rationale": "REJECT from `result.cols = selectByMask (if isDataFrame && "
                     "outputPandas then cols else castAll cols commonDtype) mask`: the "
                     "spec's gate is the CONJUNCTION, so the preserve block is taken "
                     "only when both booleans hold; the rival takes it when either "
                     "does. Refuted at `true false [col(0,1)] 3 2 [true]` — a MIXED "
                     "flag pair, the sub-domain no other witness reaches: the rival "
                     "keeps dtype 1, the spec homogenises to dtype 2. This is the case "
                     "that attests the `&&` is not a `||`; the two flag pairs the other "
                     "rivals probe (`true true`, `false false`) agree under both gates.",
        "witness": _witness("true false [{ name := 0, dtype := 1 }] 3 2 [true]"),
    },
    {
        "id": "clobber-column-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Select the right columns, in the right order, with the right element
        # types, but zero out every surviving column's IDENTITY. Attacks the
        # per-column NAME half of the keep-set face, which no other rival moves
        # (every other witness leaves `name` at its input value).
        "module": _swap(
            _BASE, _SELECT,
            "  let selected := (selectByMask block mask).map "
            "(fun c => { c with name := 0 })",
        ),
        "refinement": "discarding each surviving column's identity while keeping its "
                      "element type returns the right number of columns, in the right "
                      "order, carrying the right types — but labelled wrongly. The "
                      "failing tests match the output's column labels against the "
                      "selected input labels, and pair each label with its expected "
                      "element type, so a counterpart that relabelled the retained "
                      "columns would NOT resolve.",
        "rationale": "REJECT from `result.cols = selectByMask … mask` (keep-set face, "
                     "identity half): `selectByMask` carries each retained column "
                     "through WHOLE, so its `name` survives alongside its `dtype`; the "
                     "rival rewrites every `name` to 0. Refuted at "
                     "`true true [col(name 4, dtype 1)] 3 2 [true]`: the rival yields a "
                     "column named 0, the spec one named 4. This witness is the one that "
                     "isolates the identity face: it is the only input in the battery "
                     "whose retained column carries a NON-ZERO `name`, so a `name` clobber "
                     "is the ONLY thing it can be detecting — at every other witness's "
                     "input the retained leading column already has `name := 0` and a "
                     "clobber there is invisible on that column. (Measured, so the claim "
                     "is bounded honestly: this rival is ALSO refuted at the "
                     "`force-keep-leading-column` and `reverse-selected-order` inputs, "
                     "exit 0 both, because those carry a second column at `name := 1` "
                     "which the clobber does move. Those cases are aimed elsewhere and "
                     "their own rivals leave `name` alone, so the identity face still "
                     "needs this dedicated rival — it is what pins the clobber to the "
                     "identity half rather than to the keep-set or order half.)",
        "witness": _witness("true true [{ name := 4, dtype := 1 }] 3 2 [true]"),
    },
    {
        "id": "nrows-from-selected-count",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the row count as the number of SURVIVING COLUMNS on the
        # non-empty branch — conflating the two dimensions of the result's shape.
        # Added on audit: `drop-row-count-on-empty` moves the row count only on
        # the all-clear-mask branch, so the (row-count) face was entirely
        # unprobed on the branch that actually returns columns. Every other
        # witness sits at an input where the row count happens to be correct.
        "module": _swap(
            _BASE, _RET_SELECTED,
            "  return { cols := selected, nRows := selected.length }",
        ),
        "refinement": "reporting the row count as the number of surviving columns "
                      "conflates the result's two independent dimensions: the "
                      "selection reduces the column count and must leave the row "
                      "count alone. A caller receives a shape whose row dimension "
                      "tracks how many features were kept, so any fixture with a "
                      "row count differing from its kept-column count reports the "
                      "wrong shape. The failing tests read the output's shape and "
                      "its row dimension against the input's, so a counterpart that "
                      "recomputed the row count from the projection would NOT resolve.",
        "rationale": "REJECT from `result.nRows = nRows` (row-count face) on the "
                     "NON-EMPTY branch: the output row count must equal the input's "
                     "regardless of how many columns survive, but the rival returns "
                     "the surviving-column count. Refuted at "
                     "`true true [col(0,1)] 3 9 [true]`: one column survives so the "
                     "rival yields `nRows = 1`, the spec `nRows = 3`. This is the "
                     "only witness that puts the row count and the kept-column count "
                     "at DIFFERENT values on a branch that returns columns — "
                     "`drop-row-count-on-empty` probes the same face but only where "
                     "the mask is all-clear and no column survives.",
        "witness": _witness("true true [{ name := 0, dtype := 1 }] 3 9 [true]"),
    },
    {
        "id": "pad-mask-keep-unflagged",
        "kind": "uniqueness",
        "expect": "reject",
        # Treat a column with NO corresponding selection flag as selected, by
        # padding the selection vector with set flags. Added on audit: every
        # other witness passes a `mask` exactly as long as `cols`, so the
        # length relation between the two was never load-bearing — an impl that
        # invented flags for unflagged columns was unattacked. `selectByMask`
        # pins this via `zip`, which stops at the shorter list.
        "module": _swap(
            _BASE, _SELECT,
            "  let selected := selectByMask block (mask ++ [true, true, true])",
        ),
        "refinement": "keeping a column for which the selector supplied no decision "
                      "invents a selection the selector never made: the surviving set "
                      "is defined only by the flags actually produced, and a column "
                      "beyond them is not selected. A caller whose selection vector is "
                      "shorter than the column list receives extra columns it never "
                      "asked for, with their own element types. The failing tests "
                      "assert the output columns are exactly the selected ones, so a "
                      "counterpart that defaulted unflagged columns to kept would NOT "
                      "resolve.",
        "rationale": "REJECT from `result.cols = selectByMask … mask` (keep-set face, "
                     "length relation): `selectByMask` zips `cols` against `mask` and "
                     "`zip` stops at the shorter list, so a column with no flag "
                     "contributes NOTHING; the rival pads the vector with set flags and "
                     "so retains it. Refuted at "
                     "`true true [col(0,1),col(1,2)] 3 9 [true]` — two columns, a "
                     "ONE-element mask, the only input in the battery where `mask` and "
                     "`cols` differ in length: the rival yields two columns, the spec "
                     "one. Every other witness passes `mask.length = cols.length`, "
                     "which leaves the truncating `zip` untested.",
        "witness": _witness(
            "true true [{ name := 0, dtype := 1 }, { name := 1, dtype := 2 }] "
            "3 9 [true]"),
    },
]
