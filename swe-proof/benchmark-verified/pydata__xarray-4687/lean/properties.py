# properties.py — PBT (G-PBT, spec lane) manifest for pydata__xarray-4687,
# LEAN backend. NOT a Lean module: a record of adversarial cases the gate parses
# and executes against the frozen Solution.lean.
#
# PORT NOTE. This battery is re-expressed from the nagini sibling
# (../nagini/properties.py); the nagini file is the design document, not a text
# to translate. The nagini carrier models an imperative index-1 copy loop over a
# length-3 positional operand list with fractional-permission frame discipline;
# this bundle models only the purely functional core: a conditional value
# selection plus a three-valued attribute-retention flag. Every nagini case that
# attacked permission/aliasing machinery is VACUOUS here (see `assessment` at
# the bottom for the full port ledger). Case-count parity with nagini is NOT the
# target — coverage of the surface THIS bundle models is.
#
# Defended surface of implementation_condSelect(cond, x, y, keepAttrs):
#   * problem_spec_condSelect has two independent top-level conjuncts:
#       (V) result.values = selVals cond x.values y.values
#       (A) result.attrs  = if keptAttrs keepAttrs then x.attrs else []
#     where keptAttrs resolves the caller's flag: `some b => b`, and on `none`
#     it consults the opaque ambient default `getKeepAttrsDefault`.
#   * (V) binders: cond, x.values, y.values — an elementwise per-position
#     choice. (A) binders: keepAttrs (three-valued), x.attrs.
#   * getKeepAttrsDefault is `opaque`: the `none` branch cannot be decided by a
#     literal, so its rival is refuted by CONDITIONING on the carrier (one weak
#     hypothesis fixing the default's value).
from pathlib import Path

INSTANCE = "pydata__xarray-4687"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Every edit is a substring that lies ENTIRELY inside the impl region
# (`-- impl-start` .. `-- impl-end`) or, for the positive control, inside the
# proof body (`-- proof-start` .. `-- proof-end`). The frozen spec view
# (structure/pure helpers/problem_spec + the correct_* STATEMENT) is never
# touched, so same_spec holds by construction and the obligation survives.
# ---------------------------------------------------------------------------

# The full frozen impl-region body.
_IMPL = """def implementation_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) : DataArr := Id.run do
  let mut ka : Option Bool := keepAttrs
  if ka == none then
    ka := some getKeepAttrsDefault
  let kept : Bool := match ka with
    | some true => true
    | _         => false
  let attrs := if kept then x.attrs else []
  return { values := selVals cond x.values y.values, attrs := attrs }"""

assert _IMPL in _BASE, "impl anchor drifted from Solution.lean"

# The frozen proof body (between `by` and `-- proof-end`).
_PROOF = """  intro cond x y keepAttrs
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  cases keepAttrs with
  | none =>
    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
    cases h : getKeepAttrsDefault <;> simp
  | some b =>
    cases b <;> simp [Id.run, bind, pure]"""

assert _PROOF in _BASE, "proof anchor drifted from Solution.lean"


# ===========================================================================
# SPEC LANE
# ===========================================================================

# --- POSITIVE CONTROL: structurally different but CORRECT ------------------
# Re-express the impl as a pure functional `def` (no `Id.run do`/`let mut`/early
# mutation): resolve the flag by a direct `match` on keepAttrs and build the
# record in one expression. Observationally identical to the frozen impl on
# every input, so it must verify (else SPEC-TOO-STRONG). The proof body is
# reshaped to match the new form; the `theorem correct_condSelect` STATEMENT is
# byte-identical.
_POS_IMPL = """def implementation_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) : DataArr :=
  let kept : Bool := match keepAttrs with
    | none   => getKeepAttrsDefault
    | some b => b
  { values := selVals cond x.values y.values,
    attrs := if kept then x.attrs else [] }"""

_POS_PROOF = """  intro cond x y keepAttrs
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  cases keepAttrs with
  | none => cases h : getKeepAttrsDefault <;> simp [h]
  | some b => cases b <;> simp"""


def _pos_module():
    src = _swap(_BASE, _IMPL, _POS_IMPL)
    return _swap(src, _PROOF, _POS_PROOF)


# --- ADMISSIBILITY: the obligation is SATISFIABLE at a concrete in-domain
# input, discharged by evaluation before the frozen obligation is closed
# verbatim.
#
# `correct_condSelect` binds four inputs under no hypothesis, so there is no
# precondition to over-constrain in the literal sense. That is NOT a reason to
# skip this lane: the analogue of PRECOND-TOO-STRONG on a total carrier is the
# obligation being UNSATISFIABLE at exactly a normal, representative input —
# a spec that no impl can meet there is over-constrained whether or not the
# over-constraint is spelled as a `→`. This case tests that directly.
#
# The ground point is the smallest input shaped like the scenario the modeled
# behavior exists to serve: a two-position condition that is true at one
# position and false at the other (so BOTH arms of the elementwise choice are
# exercised), two operands with distinct values AND distinct attributes, and the
# retention flag explicitly requested. Both conjuncts are then pinned by
# EVALUATION as separate `have`s — values = [1, 0] (one element drawn from each
# operand) and attrs = the first operand's — before the frozen proof body runs
# unchanged.
#
# Nothing is assumed: no new top-level declaration, the `correct_condSelect`
# STATEMENT is byte-identical, and the two `have`s are ordinary tactic steps
# inside the existing proof body that close by `decide` on closed terms. The
# `have`s are load-bearing rather than decorative, which was checked by
# falsifying each in turn: asserting values = [1, 1] (the un-selected shape) or
# attrs = the SECOND operand's makes the build FAIL, so `decide` is really
# evaluating the modeled behavior at this point and not proving a tautology.
_ADMISS_X = '{values := [1, 1], attrs := [("attr", "x")]}'
_ADMISS_Y = '{values := [0, 0], attrs := [("attr", "y")]}'

_ADMISS_PROOF = f"""  have _f2p_values :
      (implementation_condSelect [true, false] {_ADMISS_X} {_ADMISS_Y} (some true)).values
        = [1, 0] := by
    unfold implementation_condSelect selVals
    decide
  have _f2p_attrs :
      (implementation_condSelect [true, false] {_ADMISS_X} {_ADMISS_Y} (some true)).attrs
        = [("attr", "x")] := by
    unfold implementation_condSelect
    decide
  have _ground : problem_spec_condSelect [true, false] {_ADMISS_X} {_ADMISS_Y} (some true)
      (implementation_condSelect [true, false] {_ADMISS_X} {_ADMISS_Y} (some true)) := by
    unfold problem_spec_condSelect keptAttrs
    exact ⟨_f2p_values, _f2p_attrs⟩
{_PROOF}"""


# --- REJECT rivals. Each edits ONE substring strictly inside the impl region;
# the frozen proof body is left untouched, so the rival is REJECTED at build
# time — but the recorded rejection is attributed to the spec only via the
# `witness`, which is checked in a file with the obligation stripped.

# (A-clause) ALWAYS-KEEP: retain x.attrs regardless of the flag. Wrong whenever
# retention is NOT in effect (keepAttrs = some false, or none under a False
# default): the result carries attrs the spec says must be empty.
_R_ALWAYS_KEEP = _swap(
    _IMPL, "  let attrs := if kept then x.attrs else []",
    "  let attrs := x.attrs")

# (A-clause) ALWAYS-DROP: never retain. Wrong when retention IS requested
# (keepAttrs = some true): result.attrs = [] but the spec demands x.attrs.
_R_ALWAYS_DROP = _swap(_IMPL, "    | some true => true",
                       "    | some true => false")

# (A-clause) WRONG OPERAND: retain the OTHER operand's attrs (y, the value
# chosen where cond is FALSE) instead of x's. The mode==1/PRESERVE
# wrong-operand attack ported from nagini's index-0/index-2 rivals — here the
# only rival operand carrying attrs in the model is y.
_R_WRONG_OPERAND = _swap(
    _IMPL, "  let attrs := if kept then x.attrs else []",
    "  let attrs := if kept then y.attrs else []")

# (A-clause, opaque branch) NONE-KEEPS: on the unset flag, retain
# unconditionally instead of consulting the ambient default. Wrong exactly when
# the ambient default resolves to False (its normal configuration). Refuted by
# conditioning on the opaque carrier.
_R_NONE_KEEPS = _swap(_IMPL, "some getKeepAttrsDefault", "some true")

# (V-clause) SWAP OPERANDS: select y where cond is true and x where false —
# the elementwise choice inverted. Wrong on any position/operand pair that
# differs.
_R_SWAP_VALS = _swap(
    _IMPL, "values := selVals cond x.values y.values, attrs := attrs",
    "values := selVals cond y.values x.values, attrs := attrs")

# (V-clause) IGNORE-Y: select from x at EVERY position (ignore y and, in
# effect, cond's False positions). A distinct V-clause defect from the swap:
# this one holds y's binder at "unused", so it is refuted at a cond=[false]
# point where the swap rival would (differently) also be wrong — giving the
# y.values binder its own discriminating input.
_R_IGNORE_Y = _swap(
    _IMPL, "values := selVals cond x.values y.values, attrs := attrs",
    "values := selVals cond x.values x.values, attrs := attrs")

# (A-clause, PARTIAL DOMAIN) TRUNCATE-ATTRS: under retention, keep only the
# FIRST retained entry instead of the whole attribute list. This is the
# partial-domain attack ported from the nagini `preserve-drops-first-element`
# rival: it AGREES with the frozen impl on every input whose attribute list has
# at most one entry, and diverges only from two entries up. Every other
# A-clause rival in this battery is refuted at a single-entry list, so without
# this case the spec's dependence on the retained list BEYOND its first element
# is never demonstrated and a truncating impl would be invisible to the whole
# battery. Refuted at a two-entry list.
_R_ATTRS_TAKE1 = _swap(
    _IMPL, "  let attrs := if kept then x.attrs else []",
    "  let attrs := if kept then x.attrs.take 1 else []")

# (A-clause, opaque branch) NONE-DROPS: on the unset flag, DROP
# unconditionally instead of consulting the ambient default — the opposite
# polarity to _R_NONE_KEEPS. Wrong exactly when the ambient default resolves to
# True. Together the two `none` rivals show the spec ties that branch to the
# default in BOTH directions: neither a constant-keep nor a constant-drop
# resolution of the unset flag satisfies it.
_R_NONE_DROPS = _swap(_IMPL, "some getKeepAttrsDefault", "some false")


SPEC_TESTS = [
    {
        "id": "pos-control-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_module(),
        "rationale": (
            "A structurally-different but CORRECT impl: the imperative "
            "`Id.run do`/`let mut` flag resolution is re-expressed as a pure "
            "functional `match` building the record in one expression. "
            "Observationally identical to the frozen impl on every input; the "
            "proof body is reshaped to the new form while the "
            "`theorem correct_condSelect` statement stays byte-identical. Must "
            "verify (else SPEC-TOO-STRONG). Defends both conjuncts (V) and (A)."
        ),
    },
    {
        "id": "admiss-ground-selection",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _ADMISS_PROOF),
        "rationale": (
            "ADMISSIBILITY. The obligation is discharged at a concrete "
            "in-domain input BEFORE the frozen obligation is closed verbatim: a "
            "two-position condition true at one position and false at the other "
            "(both arms of the elementwise choice), two operands with distinct "
            "values and distinct attributes, retention explicitly requested. "
            "Both conjuncts are pinned by EVALUATION as separate `have`s — "
            "values = [1, 0], drawing one element from each operand, and attrs = "
            "the first operand's. Must verify, else the modeled behavior would "
            "be unsatisfiable at exactly a normal representative input, which is "
            "this total carrier's analogue of PRECOND-TOO-STRONG. "
            "`correct_condSelect` binds no hypothesis, so there is no `→` to "
            "over-constrain; that makes the literal precondition reading vacuous "
            "but NOT this lane — an over-constrained spec here shows up as a "
            "ground instance that cannot be discharged. Nothing is assumed: no "
            "new declaration, statement byte-identical, the `have`s are ordinary "
            "steps in the existing proof body closing by `decide` on closed "
            "terms. Checked load-bearing by falsification: asserting "
            "values = [1, 1] or the SECOND operand's attrs makes the build fail, "
            "so `decide` is evaluating the behavior rather than proving a "
            "tautology. Ports nagini's admiss-precond-usable, whose "
            "reachable-normal-return half survives on this carrier even though "
            "its permission-fact half does not."
        ),
    },
    {
        "id": "attrs-always-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_ALWAYS_KEEP),
        "refinement": (
            "A faithful patch that retained the chosen operand's attributes "
            "UNCONDITIONALLY (dropping the flag check) would keep metadata even "
            "when retention was not requested, changing the historical "
            "default-drop behavior of the modeled operation. It would fail the "
            "PASS_TO_PASS cases that assert the result carries no attributes "
            "under the default configuration, so a verifying rival here is a "
            "true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "Attacks conjunct (A): result.attrs is set to x.attrs regardless of "
            "the flag. Violates `result.attrs = if keptAttrs keepAttrs then "
            "x.attrs else []` on the retention-off sub-domain. Binder attacked: "
            "keepAttrs (witness holds it at `some false`, where the spec demands "
            "[])."
        ),
        "witness": r"""example : ¬ problem_spec_condSelect [] {values := [], attrs := [("a","1")]}
    {values := [], attrs := []} (some false)
    (implementation_condSelect [] {values := [], attrs := [("a","1")]}
      {values := [], attrs := []} (some false)) := by
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  decide""",
    },
    {
        "id": "attrs-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_ALWAYS_DROP),
        "refinement": (
            "This is the ORIGINAL reported defect: attributes are always "
            "dropped, so the retention request is ignored. A patch that never "
            "retained attributes is exactly the pre-fix behavior and fails the "
            "F2P test (which requests retention and asserts the result keeps the "
            "chosen operand's attributes)."
        ),
        "rationale": (
            "Attacks conjunct (A): the `some true` arm resolves to `false`, so "
            "result.attrs = [] even when retention is requested. Violates "
            "`result.attrs = ... x.attrs ...` on the retention-on sub-domain. "
            "Binder attacked: keepAttrs held at `some true`; x.attrs non-empty."
        ),
        "witness": r"""example : ¬ problem_spec_condSelect [] {values := [], attrs := [("a","1")]}
    {values := [], attrs := []} (some true)
    (implementation_condSelect [] {values := [], attrs := [("a","1")]}
      {values := [], attrs := []} (some true)) := by
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  decide""",
    },
    {
        "id": "attrs-wrong-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_WRONG_OPERAND),
        "refinement": (
            "The retention policy must carry the attributes of the operand "
            "chosen where the condition is TRUE. A patch that installed the "
            "other operand's attributes would return the wrong metadata and fail "
            "the F2P test, which pins the retained attrs to that specific "
            "operand — the wrong-operand attack carried over from the nagini "
            "index-0/index-2 rivals."
        ),
        "rationale": (
            "Attacks conjunct (A): result.attrs = y.attrs under retention, but "
            "the spec demands x.attrs. Refutable whenever x.attrs != y.attrs. "
            "Binder attacked: x.attrs vs the sibling operand (witness gives them "
            "distinct values under keepAttrs = some true)."
        ),
        "witness": r"""example : ¬ problem_spec_condSelect [] {values := [], attrs := [("a","x")]}
    {values := [], attrs := [("a","y")]} (some true)
    (implementation_condSelect [] {values := [], attrs := [("a","x")]}
      {values := [], attrs := [("a","y")]} (some true)) := by
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  decide""",
    },
    {
        "id": "attrs-none-keeps",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_NONE_KEEPS),
        "refinement": (
            "When the caller leaves the flag unset, retention is governed by the "
            "ambient default policy — normally OFF. A patch that retained by "
            "default on an unset flag would change the documented default-drop "
            "behavior and fail the PASS_TO_PASS cases exercising the unset flag "
            "under the default configuration."
        ),
        "rationale": (
            "Attacks conjunct (A) on the OPAQUE `none` branch: the rival returns "
            "x.attrs on `keepAttrs = none` unconditionally, but the spec ties "
            "that branch to `getKeepAttrsDefault`. The default is opaque, so the "
            "witness CONDITIONS on it (a single hypothesis fixing it to `false`) "
            "— the sub-domain where the ambient policy drops and the rival is "
            "wrong. Binder attacked: keepAttrs held at `none` (a value no other "
            "witness probes)."
        ),
        "witness": r"""example (h : getKeepAttrsDefault = false) :
    ¬ problem_spec_condSelect [] {values := [], attrs := [("a","1")]}
      {values := [], attrs := []} none
      (implementation_condSelect [] {values := [], attrs := [("a","1")]}
        {values := [], attrs := []} none) := by
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  simp [h]""",
    },
    {
        "id": "values-swap-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_SWAP_VALS),
        "refinement": (
            "The result values must be the elementwise choice: the first "
            "operand where the condition holds, the second otherwise. A patch "
            "that swapped the two operands would invert the selection and fail "
            "test_where and the many PASS_TO_PASS `where` cases, all of which "
            "pin the per-position value selection."
        ),
        "rationale": (
            "Attacks conjunct (V): result.values = selVals cond y.values x.values "
            "instead of selVals cond x.values y.values. Refutable at any "
            "condition/operand pair that differs. Binders attacked: cond (held "
            "at `[true]`, a True position), x.values and y.values (distinct)."
        ),
        "witness": r"""example : ¬ problem_spec_condSelect [true] {values := [1], attrs := []}
    {values := [2], attrs := []} (some false)
    (implementation_condSelect [true] {values := [1], attrs := []}
      {values := [2], attrs := []} (some false)) := by
  unfold problem_spec_condSelect implementation_condSelect selVals keptAttrs
  decide""",
    },
    {
        "id": "values-ignore-y",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_IGNORE_Y),
        "refinement": (
            "A patch that selected the first operand at every position — "
            "ignoring the second operand entirely — would return wrong values "
            "wherever the condition is False and fail test_where / the `where` "
            "PASS_TO_PASS cases that replace values on the False positions."
        ),
        "rationale": (
            "Attacks conjunct (V) distinctly from the swap rival: it holds the "
            "y.values binder at 'unused', so it is refuted at a cond=[false] "
            "point where the selection must draw from y. This gives y.values its "
            "OWN discriminating input (a False condition position), so the "
            "battery demonstrates the spec's dependence on the second operand, "
            "not just on the first."
        ),
        "witness": r"""example : ¬ problem_spec_condSelect [false] {values := [1], attrs := []}
    {values := [2], attrs := []} (some false)
    (implementation_condSelect [false] {values := [1], attrs := []}
      {values := [2], attrs := []} (some false)) := by
  unfold problem_spec_condSelect implementation_condSelect selVals keptAttrs
  decide""",
    },
    {
        "id": "attrs-truncate-to-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_ATTRS_TAKE1),
        "refinement": (
            "PARTIAL DOMAIN. A patch that installed only the first retained "
            "attribute — rather than the whole attribute mapping — would look "
            "correct on every single-attribute operand and lose metadata on any "
            "operand carrying two or more. It would pass the F2P case (whose "
            "operand carries one attribute) while still corrupting the retention "
            "behavior, and would fail the PASS_TO_PASS retention-strategy cases "
            "that compare the FULL attribute mapping."
        ),
        "rationale": (
            "Attacks conjunct (A) on a sub-domain no other case in this battery "
            "reaches. Every other A-clause rival is refuted at an attribute list "
            "of length <= 1, and this rival AGREES with the frozen impl on all of "
            "those inputs — so it is invisible to the rest of the manifest. "
            "Violates `result.attrs = if keptAttrs keepAttrs then x.attrs else []` "
            "only from two entries up. Binder attacked: x.attrs held at LENGTH 2 "
            "(the list-structure dimension of the retained value, as opposed to "
            "which operand it came from)."
        ),
        "witness": r"""example : ¬ problem_spec_condSelect []
    {values := [], attrs := [("a","1"),("b","2")]}
    {values := [], attrs := []} (some true)
    (implementation_condSelect [] {values := [], attrs := [("a","1"),("b","2")]}
      {values := [], attrs := []} (some true)) := by
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  decide""",
    },
    {
        "id": "attrs-none-drops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_NONE_DROPS),
        "refinement": (
            "The dual of the none-keeps rival. A patch that hard-coded the unset "
            "flag to DROP — rather than reading the ambient retention policy — "
            "would ignore a caller who had configured retention on globally, so "
            "the documented ability to turn retention on by ambient "
            "configuration would silently do nothing. It would fail the "
            "PASS_TO_PASS retention-strategy cases that set the ambient policy "
            "and then call with no explicit flag."
        ),
        "rationale": (
            "Attacks conjunct (A) on the OPAQUE `none` branch at the OPPOSITE "
            "polarity to attrs-none-keeps: the rival returns [] on "
            "`keepAttrs = none` unconditionally, but the spec ties that branch to "
            "`getKeepAttrsDefault`. Witness CONDITIONS the opaque default to "
            "`true` — the sub-domain where the ambient policy retains and this "
            "rival wrongly drops. This is the only case in the battery that "
            "exercises the default's `true` value; attrs-none-keeps pins it at "
            "`false`, so the two together show the `none` branch genuinely FOLLOWS "
            "the default rather than agreeing with it at one point."
        ),
        "witness": r"""example (h : getKeepAttrsDefault = true) :
    ¬ problem_spec_condSelect [] {values := [], attrs := [("a","1")]}
      {values := [], attrs := []} none
      (implementation_condSelect [] {values := [], attrs := [("a","1")]}
        {values := [], attrs := []} none) := by
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  simp [h]""",
    },
]


# ===========================================================================
# PORT LEDGER (the `assessment` the header refers to)
# ===========================================================================
# Per-nagini-case disposition. The nagini carrier models an imperative
# index-1 copy loop over a length-3 positional operand list under
# fractional-permission frame discipline; this bundle models the purely
# functional core (a conditional value selection plus a three-valued retention
# flag) over an immutable `structure DataArr`. Cases that attacked the
# permission machinery have no referent here; cases that attacked a VALUE
# clause were re-expressed and are all present above.
assessment = {
    "pos-control-branch-reorder": (
        "PORTED as pos-control-functional-reshape. Same intent (a correct impl "
        "in a different shape); the reshape here drops `Id.run do`/`let mut` for "
        "a pure functional `match`, which is this carrier's analogue of nagini's "
        "control-flow reorder."),
    "admiss-precond-usable": (
        "PORTED as admiss-ground-selection. This entry previously recorded the "
        "case as VACUOUS on the ground that `correct_condSelect` binds four "
        "inputs and no hypothesis, so there is no `→` to over-constrain. That "
        "reasoning was WRONG and a later audit landed the case instead. The "
        "no-precondition observation is true but does not make the LANE vacuous: "
        "on a total carrier the analogue of PRECOND-TOO-STRONG is the obligation "
        "being unsatisfiable at exactly a normal, representative input, which a "
        "positive that discharges it at a concrete such input — by evaluation, as "
        "a `have`, before closing the frozen obligation verbatim — tests "
        "directly. nagini's case had two halves: the usability of the "
        "half-permission `Requires` facts (genuinely inexpressible here, no "
        "permission system) and the reachability of a normal non-raising return "
        "for an in-domain input (fully expressible, and now ported). Dropping the "
        "whole case removed one of the three directions this gate tests."),
    "frame-mut-append-readonly": (
        "VACUOUS here. The nagini rival wrote through an input held at "
        "Acc(list_pred(attrs[1]), 1/2) and had to be rejected for INSUFFICIENT "
        "PERMISSION. `DataArr` is an immutable Lean structure and there is no "
        "permission system or aliasing to violate: an impl cannot mutate its "
        "argument, so the defect this case attacked cannot be written down. Not "
        "a proof-difficulty dodge — there is no such term."),
    "frame-mut-overwrite-readonly": (
        "VACUOUS here, same reason as frame-mut-append-readonly (in-place "
        "element overwrite of a read-only operand). No mutable state on this "
        "carrier."),
    "preserve-returns-cond-index0": (
        "PARTLY VACUOUS, and the expressible half is PORTED. nagini's operand "
        "list was positional and homogeneous, so `attrs[0]` (the CONDITION) "
        "carried an attribute payload that could be returned by mistake. Here "
        "`cond : List Bool` has no `.attrs` field at all, so the index-0 "
        "confusion is not typeable. The wrong-operand attack itself survives "
        "against the only other operand that carries attributes and is ported as "
        "attrs-wrong-operand."),
    "preserve-returns-y-index2": (
        "PORTED as attrs-wrong-operand (retain y.attrs instead of x.attrs)."),
    "preserve-drops-first-element": (
        "PORTED as attrs-truncate-to-first. This was MISSING from the original "
        "port and was added by audit: it is the partial-domain attack (correct on "
        "attribute lists of length <= 1, wrong from two entries up), and it is "
        "fully expressible on this carrier — `x.attrs.take 1` is the direct "
        "analogue of nagini's drop-a-boundary-element rival. Every other "
        "A-clause rival in this battery is refuted at a single-entry list, so "
        "before this case the spec's dependence on the retained list beyond its "
        "head was never demonstrated."),
    "(divergence lane — no nagini case, disposition recorded)": (
        "VACUOUS on this carrier, not a known hole. The divergence class asks "
        "whether a rival whose loop carries no decreasing measure is rejected, "
        "and its disposition is set by `loom.semantics.termination`. This "
        "bundle's frozen solution carries NO such option — it is a plain Lean "
        "file with no loom semantics block, so the setting does not apply. Every "
        "definition in the impl region is structurally total: `selVals` is a "
        "`zip`/`map` over a finite list and the flag resolution is a `match` on "
        "`Option Bool`, so a non-terminating rival cannot be written as a plain "
        "`def` at all (Lean's own termination checker rejects it before the spec "
        "is consulted, which is a carrier rejection and not a spec rejection, so "
        "it would attest nothing). nagini carried no `diverge-*`/`nonterm-*` case "
        "here either — its loop was a bounded index-1 copy with an explicit "
        "`0 <= i and i <= len(src)` invariant."),
    "default-keeps-instead-of-drops": (
        "PORTED, and split into the two polarities the opaque default admits: "
        "attrs-none-keeps (default resolves false, rival keeps) and "
        "attrs-none-drops (default resolves true, rival drops — added by audit). "
        "nagini could assert the default's value via a @ContractOnly axiom; here "
        "`getKeepAttrsDefault` is `opaque`, so each is refuted by CONDITIONING on "
        "it, and the gate's consistency probe confirms the hypothesis is "
        "satisfiable."),
}
