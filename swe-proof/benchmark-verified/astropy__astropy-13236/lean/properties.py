# properties.py — PBT falsification battery for astropy__astropy-13236 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, where a reshaped impl needs it, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_columnForTableData` STATEMENT is
# preserved verbatim. No case introduces sorry/admit/native_decide/axiom or any
# new theorem/lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts a class-selection decision returning an integer
# kind code over nine primitive boolean observations. This Lean bundle models the
# SAME decision on a purely functional carrier: a `ConvInput` structure of the
# observable flags/counts and the classes the unchanged upstream sub-decisions
# yield, mapped to a `ColClass` result (default column / masked column /
# array-backed mixin / other mixin). The single load-bearing clause is
#     result = convResultClass inp
# i.e. the selected class is EXACTLY the class assigned by the desired rule — a
# rule that never consults the field count on its own, so a multi-field
# (structured) array follows the same masked/default decision as any other plain
# array and is NOT diverted to the array-backed mixin class.
#
# DEFENDED SURFACE (what every rival attacks):
#   the master relation `result = convResultClass inp`, and in particular its
#   consequences on a non-column non-mixin multi-field array:
#     * an UNMASKED such array selects the default column class;
#     * a MASKED such array selects the masked column class;
#   plus the first-match precedence of the rule (the sequence-of-mixin case
#   outranks the masked case) and the dtype-less masked-coercion branch.
# Input binder of the spec predicate: the single `inp : ConvInput`. The reject
# witnesses vary it across FOUR distinct points — an unmasked multi-field array,
# a masked multi-field array, a masked sequence-of-mixin value, and a dtype-less
# masked-coercion value — so both settings of the masked flag, the multi-field
# count, the data0-is-mixin flag and the dtype flag are exercised.
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * the FRAME / permission-mutation class is VACUOUS on this backend: Lean is
#     referentially transparent, there is no aliasing or fractional permission to
#     violate, so there is no counterpart rival to author.
#   * the ADMISSIBILITY lane is PRESENT (`admiss-ground-f2p-multifield`). An
#     earlier revision of this manifest dropped it, reasoning that
#     `correct_columnForTableData` is an unconditional `∀ inp` with no
#     precondition hypothesis and therefore has no precondition to prove usable.
#     That reason is WRONG, and the case below is the correction: on a total
#     carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
#     discharges the spec predicate at that concrete input BY EVALUATION — as a
#     `have`, before closing the frozen obligation verbatim — tests directly.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job and this bundle ships
#     no consumed axiom (the decision is modeled structurally, not over an opaque
#     callee).
from pathlib import Path

INSTANCE = "astropy__astropy-13236"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the impl / proof regions of the frozen
# Solution.lean, each unique in the file.
# ---------------------------------------------------------------------------

# The frozen impl cascade (impl region body).
_GOLD_IMPL = """  if inp.isColumn then
    return inp.columnInputResult
  else if inp.isMixin then
    return inp.dataMixinClass
  else if inp.data0IsMixin then
    return inp.seqMixinResult
  else if inp.isMaskedArray then
    return inp.tableMaskedColumn
  else if inp.isNone then
    return inp.tableColumnClass
  else if !inp.hasDtype then
    if inp.seqConvMasked then
      return inp.tableMaskedColumn
    else
      return inp.tableColumnClass
  else
    return inp.tableColumnClass"""

# The frozen proof body (only touched by the soundness positive, which reshapes
# the impl and therefore needs a proof that closes for the new shape).
_GOLD_PROOF = """  intro inp
  unfold problem_spec_columnForTableData implementation_columnForTableData convResultClass
  rfl"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — structurally different but CORRECT.
# Replaces the first-match if/elif cascade with a single mutable result local
# assigned by a value-selecting cascade in REVERSE priority: the lowest-priority
# case is written first and each higher-priority guard OVERWRITES it, so the
# highest-priority match wins last. Same decision, different control shape. The
# proof reduces the `do` block and case-splits every relevant flag. Must verify;
# if a faithful correct reshape cannot satisfy `result = convResultClass inp`,
# the spec is SPEC-TOO-STRONG.
_POS_IMPL = """  -- structurally-different correct impl: one result local assigned by a
  -- value-selecting cascade in REVERSE priority, so the highest-priority guard
  -- overwrites last (same first-match semantics as the rule).
  let mut kind := inp.tableColumnClass
  if !inp.hasDtype then
    kind := (if inp.seqConvMasked then inp.tableMaskedColumn else inp.tableColumnClass)
  if inp.isNone then
    kind := inp.tableColumnClass
  if inp.isMaskedArray then
    kind := inp.tableMaskedColumn
  if inp.data0IsMixin then
    kind := inp.seqMixinResult
  if inp.isMixin then
    kind := inp.dataMixinClass
  if inp.isColumn then
    kind := inp.columnInputResult
  return kind"""

_POS_PROOF = """  intro inp
  unfold problem_spec_columnForTableData implementation_columnForTableData convResultClass
  simp only [Id.run, bind, pure]
  rcases inp with ⟨isColumn, isMixin, data0IsMixin, isNdarray, numDtypeFields, isMaskedArray, isNone, hasDtype, columnInputResult, dataMixinClass, seqMixinResult, seqConvMasked, tableColumnClass, tableMaskedColumn⟩
  cases isColumn <;> cases isMixin <;> cases data0IsMixin <;> cases isMaskedArray <;> cases isNone <;> cases hasDtype <;> cases seqConvMasked <;> rfl"""


# ---------------------------------------------------------------------------
# UNIQUENESS #1 — full multi-field override (the canonical attack).
# Re-adds the deleted leading guard that forces ANY non-column non-mixin
# multi-field array to the array-backed mixin class before the normal rule runs.
# Correct on the whole non-structured domain, wrong on both structured
# sub-domains.
_REJ_FULL = ("""  if !inp.isColumn && !inp.isMixin && inp.isNdarray && inp.numDtypeFields > 1 then
    return ColClass.ndarrayMixin
""" + _GOLD_IMPL)

# UNIQUENESS #2 — masked-only multi-field override. Diverts ONLY a MASKED
# multi-field array to the mixin class; the unmasked half is left correct.
_REJ_MASKED = ("""  if !inp.isColumn && !inp.isMixin && inp.isNdarray && inp.numDtypeFields > 1 && inp.isMaskedArray then
    return ColClass.ndarrayMixin
""" + _GOLD_IMPL)

# UNIQUENESS #3 — unmasked-only multi-field override. The complementary half:
# diverts ONLY an UNMASKED multi-field array to the mixin class; the masked half
# is left correct.
_REJ_UNMASKED = ("""  if !inp.isColumn && !inp.isMixin && inp.isNdarray && inp.numDtypeFields > 1 && !inp.isMaskedArray then
    return ColClass.ndarrayMixin
""" + _GOLD_IMPL)

# UNIQUENESS #4 — first-match ORDER flip. Tests the masked case BEFORE the
# sequence-of-mixin case, inverting the rule's precedence. Diverges on
# {not column, not mixin, data0-is-mixin, masked}: the rule selects the
# sequence-of-mixin class, this rival selects the masked column class.
_REJ_ORDER = """  if inp.isColumn then
    return inp.columnInputResult
  else if inp.isMixin then
    return inp.dataMixinClass
  else if inp.isMaskedArray then
    return inp.tableMaskedColumn
  else if inp.data0IsMixin then
    return inp.seqMixinResult
  else if inp.isNone then
    return inp.tableColumnClass
  else if !inp.hasDtype then
    if inp.seqConvMasked then
      return inp.tableMaskedColumn
    else
      return inp.tableColumnClass
  else
    return inp.tableColumnClass"""

# UNIQUENESS #5 — dropped dtype-less masked-coercion branch. Omits the branch
# that yields the masked column class when a dtype-less value's coercion produced
# a masked array; such inputs fall through to the default column class.
_REJ_NOSEQ = """  if inp.isColumn then
    return inp.columnInputResult
  else if inp.isMixin then
    return inp.dataMixinClass
  else if inp.data0IsMixin then
    return inp.seqMixinResult
  else if inp.isMaskedArray then
    return inp.tableMaskedColumn
  else if inp.isNone then
    return inp.tableColumnClass
  else
    return inp.tableColumnClass"""


# ---------------------------------------------------------------------------
# Concrete witness inputs (as Lean `ConvInput` literals). Each is `decide`-able.
# ---------------------------------------------------------------------------

def _inp(isColumn, isMixin, data0, isNd, ndf, isMasked, isNone, hasDtype,
         cir, dmc, smr, scm, tcc, tmc):
    return (
        "{ isColumn := %s, isMixin := %s, data0IsMixin := %s, isNdarray := %s, "
        "numDtypeFields := %s, isMaskedArray := %s, isNone := %s, hasDtype := %s, "
        "columnInputResult := ColClass.%s, dataMixinClass := ColClass.%s, "
        "seqMixinResult := ColClass.%s, seqConvMasked := %s, "
        "tableColumnClass := ColClass.%s, tableMaskedColumn := ColClass.%s }"
        % (isColumn, isMixin, data0, isNd, ndf, isMasked, isNone, hasDtype,
           cir, dmc, smr, scm, tcc, tmc))


# unmasked multi-field array: rule -> default column class; overrides -> mixin.
_W_UNMASKED_STRUCT = _inp("false", "false", "false", "true", "2", "false",
                          "false", "true", "column", "otherMixin", "otherMixin",
                          "false", "column", "maskedColumn")
# masked multi-field array: rule -> masked column class; overrides -> mixin.
_W_MASKED_STRUCT = _inp("false", "false", "false", "true", "2", "true",
                        "false", "true", "column", "otherMixin", "otherMixin",
                        "false", "column", "maskedColumn")
# not column, sequence-of-mixin, masked: rule -> sequence-of-mixin class (it
# outranks masked); order-flip rival -> masked column class.
_W_DATA0_MASKED = _inp("false", "false", "true", "false", "0", "true",
                       "false", "true", "column", "otherMixin", "otherMixin",
                       "false", "column", "maskedColumn")
# dtype-less value whose coercion produced a masked array: rule -> masked column
# class; dropped-branch rival -> default column class.
_W_SEQCONV_MASKED = _inp("false", "false", "false", "false", "0", "false",
                         "false", "false", "column", "otherMixin", "otherMixin",
                         "true", "column", "maskedColumn")


# ---------------------------------------------------------------------------
# ADMISSIBILITY proof body. Discharges the spec predicate BY EVALUATION at the
# two F2P-shaped points (an unmasked multi-field array and a masked one) as two
# `have`s, then closes the frozen obligation verbatim. Nothing is assumed: no new
# declaration, no assumption token, and the theorem STATEMENT is byte-identical —
# only the tactic body grows. If either `have` failed, the obligation would be
# unsatisfiable at exactly the input the failing tests exercise, which is this
# carrier's analogue of PRECOND-TOO-STRONG.
def _ground_have(name, lit):
    return (
        "  have %s : problem_spec_columnForTableData\n"
        "      (%s)\n"
        "      (implementation_columnForTableData\n"
        "        (%s)) := by\n"
        "    unfold problem_spec_columnForTableData "
        "implementation_columnForTableData\n"
        "    decide\n" % (name, lit, lit))


def _witness(lit):
    return (
        "example : ¬ problem_spec_columnForTableData\n"
        "    (%s)\n"
        "    (implementation_columnForTableData\n"
        "      (%s)) := by\n"
        "  unfold problem_spec_columnForTableData implementation_columnForTableData\n"
        "  decide" % (lit, lit))


_ADMISS_PROOF = (_ground_have("_ground_unmasked", _W_UNMASKED_STRUCT)
                 + _ground_have("_ground_masked", _W_MASKED_STRUCT)
                 + _GOLD_PROOF)


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness) ------------------------------------
    {
        "id": "pos-control-reversed-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_IMPL),
                        _GOLD_PROOF, _POS_PROOF),
        "rationale": (
            "A structurally-different but CORRECT impl: one mutable result local "
            "assigned by a value-selecting cascade in REVERSE priority (lowest "
            "case first, each higher-priority guard overwrites), which has the "
            "same first-match semantics as the rule. No loop over a collection, "
            "so no induction lemma is needed; the proof reduces the `do` block "
            "and case-splits the flags. It must verify against the master clause "
            "`result = convResultClass inp`; if a faithful correct reshape cannot "
            "satisfy it, the spec is SPEC-TOO-STRONG."
        ),
    },

    # --- ADMISSIBILITY (non-vacuity at the F2P-shaped inputs) ------------
    {
        "id": "admiss-ground-f2p-multifield",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF, _ADMISS_PROOF),
        "rationale": (
            "The frozen obligation is an unconditional `∀ inp`, so there is no "
            "precondition binder to attack directly; on a total carrier the "
            "analogue of PRECOND-TOO-STRONG is the obligation being "
            "UNSATISFIABLE at exactly an F2P-shaped input. This case tests that "
            "directly: it discharges `problem_spec_columnForTableData` BY "
            "EVALUATION (`decide`) at the two concrete F2P-shaped points — a "
            "non-column non-mixin MULTI-FIELD array, unmasked (which must select "
            "the default column class) and masked (which must select the masked "
            "column class) — as two `have`s, and only then closes the frozen "
            "obligation verbatim. So the master clause is shown SATISFIABLE at "
            "the very inputs the two failing tests observe, not merely provable "
            "in the abstract. Must verify; a failure of either `have` would mean "
            "the modeled decision is unsatisfiable at the F2P input. Nothing is "
            "assumed: no new declaration, no assumption token, the theorem "
            "statement is byte-identical, and the frozen tactic body is retained "
            "unchanged as the closing step."
        ),
    },

    # --- UNIQUENESS #1: full multi-field override ------------------------
    {
        "id": "weak-full-multifield-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_FULL),
        "refinement": (
            "A faithful patch keeping this leading guard would classify EVERY "
            "non-column non-mixin multi-field array as the array-backed mixin "
            "class instead of the default/masked column class — which is exactly "
            "the classification the two failing tests forbid (an unmasked "
            "multi-field array must become the default column class; a masked one "
            "the masked column class). It would therefore NOT resolve, so a "
            "verifying rival here would be a true verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause `result = convResultClass inp`: the "
            "rule never diverts a plain multi-field array, so on a non-column "
            "non-mixin multi-field input it demands the default (unmasked) or "
            "masked (masked) column class, whereas this rival returns the mixin "
            "class. Witness at the UNMASKED multi-field point."
        ),
        # Holds of the rival (mixin != column), fails on gold (column = column).
        "witness": _witness(_W_UNMASKED_STRUCT),
    },

    # --- UNIQUENESS #2: masked-only multi-field override -----------------
    {
        "id": "weak-masked-multifield-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_MASKED),
        "refinement": (
            "Diverts ONLY a MASKED multi-field array to the mixin class. A "
            "faithful patch guarding the override by masked-ness would still turn "
            "a masked multi-field array into the array-backed mixin class instead "
            "of the masked column class the failing masked-structured test "
            "requires — so it would NOT resolve. It is a genuine partial-domain "
            "rival: correct on the unmasked half (agrees with the rule there), "
            "wrong only on the masked half."
        ),
        "rationale": (
            "Rejected by the master clause on the masked multi-field point: the "
            "rule selects the masked column class, this rival the mixin class. "
            "Witness at the MASKED multi-field point — distinct from rival #3's "
            "point, which this rival handles correctly."
        ),
        # Holds of the rival (mixin != maskedColumn), fails on gold.
        "witness": _witness(_W_MASKED_STRUCT),
    },

    # --- UNIQUENESS #3: unmasked-only multi-field override ---------------
    {
        "id": "weak-unmasked-multifield-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_UNMASKED),
        "refinement": (
            "The complementary half: diverts ONLY an UNMASKED multi-field array "
            "to the mixin class. A faithful patch guarding the override by "
            "NOT-masked would still turn an unmasked multi-field array into the "
            "array-backed mixin class instead of the default column class the "
            "failing test requires — so it would NOT resolve. Partial-domain "
            "rival: correct on the masked half, wrong only on the unmasked half."
        ),
        "rationale": (
            "Rejected by the master clause on the unmasked multi-field point: the "
            "rule selects the default column class, this rival the mixin class. "
            "Shares the unmasked point with rival #1 (both are wrong there for the "
            "same reason); it is distinguished from #1 by the masked point, which "
            "this rival — unlike #1 — handles correctly."
        ),
        # Holds of the rival (mixin != column), fails on gold.
        "witness": _witness(_W_UNMASKED_STRUCT),
    },

    # --- UNIQUENESS #4: first-match order flip ---------------------------
    {
        "id": "weak-order-flip-masked-before-data0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ORDER),
        "refinement": (
            "Inverts the rule's precedence so the masked case is tested before "
            "the sequence-of-mixin case. A faithful patch reordering those two "
            "branches would build a masked sequence whose first element is a "
            "mixin scalar as the masked column class rather than a column of that "
            "element's own class — diverging from the behavior the passing "
            "mixin-column cases rely on, so it would NOT resolve them."
        ),
        "rationale": (
            "Rejected by the master clause: `convResultClass` evaluates "
            "`data0IsMixin` BEFORE `isMaskedArray`, so on {not column, not mixin, "
            "data0-is-mixin, masked} it demands the sequence-of-mixin class "
            "whereas this rival returns the masked column class. Witness holds "
            "`data0IsMixin` at TRUE and `isMaskedArray` at TRUE."
        ),
        # Holds of the rival (maskedColumn != otherMixin), fails on gold.
        "witness": _witness(_W_DATA0_MASKED),
    },

    # --- UNIQUENESS #5: dropped dtype-less masked-coercion branch --------
    {
        "id": "weak-dropped-dtypeless-masked-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_NOSEQ),
        "refinement": (
            "Drops the branch that yields the masked column class when a "
            "dtype-less value's coercion produced a masked array; such inputs "
            "fall through to the default column class. A faithful patch removing "
            "that branch would store a dtype-less value with masked entries as an "
            "ordinary column rather than a masked one — diverging from the "
            "behavior the passing masking cases rely on, so it would NOT resolve."
        ),
        "rationale": (
            "Rejected by the master clause on {not column, not mixin, not data0, "
            "not masked, not none, no dtype, coercion masked}: the rule demands "
            "the masked column class whereas this rival returns the default "
            "column class. Witness holds `hasDtype` at FALSE and "
            "`seqConvMasked` at TRUE — the only point that exercises those "
            "binders."
        ),
        # Holds of the rival (column != maskedColumn), fails on gold.
        "witness": _witness(_W_SEQCONV_MASKED),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# The class decision is modeled structurally over the observable flags/counts of
# the input and the classes the unchanged upstream sub-decisions yield; the proof
# reasons about none of them via an opaque contract.
AXIOM_TESTS = []
