# properties.py — G-PBT falsification battery for django__django-11820 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each SPEC case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, for the reshaped soundness positives, the proof region body), so the
# frozen spec view (imports / axioms / pure / post-conditions) stays
# byte-identical, `markers.same_spec` holds by construction, and the single
# `theorem correct_lookupPathValid` STATEMENT is preserved verbatim. No case
# introduces sorry / admit / native_decide / a new axiom or any new
# theorem/lemma beyond the frozen set.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts a whole path-validation procedure over a
# permission-carrying integer-id list (`Requires(Acc(list_pred(path),1/2))`,
# `MustTerminate(2)`), pinning its boolean result to a deep @Pure fold and
# consuming five @ContractOnly graph accessors as range-only axioms. This lean
# bundle models the SAME behavioral fix on a purely functional carrier: the
# left-to-right walk of one dotted lookup path through a model graph, with the
# graph supplied AS DATA (`models : Nat → ModelInfo`, `FieldInfo`) rather than
# through opaque callees. There is a single obligation
#     result = pathValid models startModel parts
# and `pathValid` is a total, fully-unfolded fold of `stepPath` — a grounded
# oracle computed entirely from the inputs (there is no wrong value to echo; the
# cheapest honest impl IS the correct one). The nagini axiom lane therefore has
# no consumed counterpart here (the accessors are FREE DATA the fold reads), and
# the ungrounded-oracle-echo class does not apply.
#
# The one clause `result = pathValid …` composes four independently-attackable
# sub-behaviors of `stepPath`, each the target of one reject rival:
#   * the alias segment "pk" resolves against the current model's `primaryKey`
#     field DIRECTLY, not through the by-name resolver `getField` (which returns
#     `none` for it); attacked by R1.
#   * after a SUCCESSFUL non-relation resolution the walk steps off the graph
#     (`cur := none`), so a following segment has no current model and the path
#     is invalid unless a transform rescues it — the walk is NOT left at the same
#     model, which would let a following segment spuriously resolve; attacked by
#     R2.
#   * an unresolved segment is tolerated ONLY when the last resolved field
#     accepts it as a registered transform (`acceptsTransform`); the escape hatch
#     is NOT dropped; attacked by R3.
#   * a resolved field that IS a relation moves the walk onto the model it points
#     at (`cur := some f.target`) — the walk advances to the RELATED model, not
#     to some other index, so a following segment is resolved against the target
#     model's fields; attacked by R4.
#
# AUDIT NOTE (R4 added). The three ported rivals R1-R3 all state their witness
# over a graph whose every field has `isRelation := false`, so no shipped witness
# exercised the relation-descent arm of `stepPath` at all: the `f.isRelation =
# true` branch was live code no reject case discriminated at. An independently
# written rival that keeps the relation test but advances to the CURRENT model
# instead of `f.target` was confirmed to verify-reject with a semantically
# discriminating witness (rival build exit 0, gold build exit 1, gold's failure
# being `decide` proving the claim false), so the gap was a real hole in the
# battery rather than an inexpressible one. R4 closes it and is the only case
# whose witness graph contains a relation field.
#
# BINDER STRUCTURE. `problem_spec_lookupPathValid` has three input binders:
# `models` (the model graph), `startModel` (the seed model index), and `parts`
# (the segment list). All three are load-bearing and all three are VARIED across
# the reject witnesses: `startModel ∈ {0, 1, 2, 3}`, `models` ranges over four
# distinct index-keyed graphs, and `parts` over `["pk"]`, `["a","b"]` and
# `["r","b"]`. The four reject witnesses probe four DISTINCT input tuples.
# The variation is MEANINGFUL rather than two spellings of one point: each
# witness's graph is built so that gold and its rival return OPPOSITE booleans at
# that tuple, which is what the two witness builds machine-check. R4's graph is
# additionally the only one containing a field with `isRelation := true`, so the
# `startModel = 3` point is not a re-spelling of R1-R3's non-relation graphs.
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * FRAME / PERMISSION MUTATION (nagini `frame-mutation-write-path`) —
#     VACUOUS. Lean is referentially transparent: `models`/`parts` are immutable
#     values, there is no fractional heap permission to overwrite and no aliasing
#     to exploit. The nagini write-to-read-only-input rival has no expressible
#     instance here; no substitute is fabricated (per the porting map).
#   * DIVERGENCE / NON-TERMINATION (nagini `diverge-nonempty-path`) — VACUOUS on
#     lean, but not for the reason "a diverging impl cannot be written". It can:
#     `partial def implementation_lookupPathValid ... := implementation_...` is
#     accepted by Lean (`partial` supplies an `Inhabited` witness rather than a
#     termination proof). What makes the class vacuous here is that such an impl
#     is OPAQUE to reduction, so the frozen obligation cannot be discharged
#     against it — built as an audit probe it fails with a single error,
#     `Tactic 'rfl' failed`, and no vacuous verify is available. So the omission
#     is right and the disposition (nothing to ship) stands: on the lean backend
#     the obligation is a total-correctness equation with no divergence escape.
#     Contrast velvet under `set_option loom.semantics.termination "partial"`,
#     where the same rival VERIFIES vacuously — a KNOWN hole recorded in
#     the corpus-wide termination-semantics finding, not re-reported here.
#   * AXIOM_TESTS (nagini `ax-sound-*`, `ax-cover-*`) — dropped: the axiom lane
#     is G-AX's job and this bundle consumes no axiom. The graph accessors are
#     FREE DATA read by the grounded fold (an A-reference validated == the real
#     callees by G-AX), not a consumed contract.
#   * ADMISSIBILITY (nagini `admiss-normal-related-path`) — NOT omitted; see the
#     `admiss-multihop-relation-path` case below. An earlier revision of this
#     battery dropped the lane on the ground that the frozen obligation carries
#     no precondition, so PRECOND-TOO-STRONG had "no instance". That reason is
#     insufficient on a total carrier: the analogue is the obligation being
#     unsatisfiable at a concrete input of the shape under spec, which a positive
#     that discharges the spec predicate at that input by evaluation tests
#     directly. The lane is expressible here and is now carried.
from pathlib import Path

INSTANCE = "django__django-11820"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Every anchor below lies wholly inside the impl region (between
# `-- impl-start` and `-- impl-end`) or is the whole proof-region body, and each
# is unique in the frozen file; _swap asserts both at load time. The reject
# rivals swap ONLY the loop body, keeping the whole spec AND the frozen proof
# verbatim, so the rejection is attributable solely to the impl defect. The
# soundness positives replace the impl def and the proof body TOGETHER (both
# regions are elided from the consumer spec view), keeping the
# `theorem correct_lookupPathValid` statement byte-identical.
# ---------------------------------------------------------------------------

# The full executable loop body of the frozen impl (inside the impl region).
_IMPL_BODY = (
    "  let mut cur : Option Nat := some startModel\n"
    "  let mut fld : Option FieldInfo := none\n"
    "  let mut invalid : Bool := false\n"
    "  for part in parts do\n"
    "    match cur with\n"
    "    | some c =>\n"
    '        let resolved := if part == "pk" then some (models c).primaryKey\n'
    "                        else (models c).getField part\n"
    "        match resolved with\n"
    "        | some f =>\n"
    "            fld := some f\n"
    "            if f.isRelation then\n"
    "              cur := some f.target\n"
    "            else\n"
    "              cur := none\n"
    "        | none =>\n"
    "            match fld with\n"
    "            | some pf => if !(pf.acceptsTransform part) then invalid := true\n"
    "            | none => invalid := true\n"
    "    | none =>\n"
    "        match fld with\n"
    "        | some pf => if !(pf.acceptsTransform part) then invalid := true\n"
    "        | none => invalid := true\n"
    "  return !invalid"
)

# The full frozen impl definition (impl region), replaced wholesale by the
# soundness positives with a structurally different but correct shape.
_IMPL_DEF = (
    "def implementation_lookupPathValid\n"
    "    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do\n"
    "  -- Walk the path one segment at a time from the start model, remembering the\n"
    "  -- last resolved field; a non-relation field ends the walk, the \"pk\" alias\n"
    "  -- resolves to the primary-key field, and an unresolved segment is tolerated\n"
    "  -- only if the last field accepts it as a transform.\n"
    + _IMPL_BODY
)

# The whole proof-region BODY (between the markers), replaced by the soundness
# positives with a proof that closes for the reshaped impl. The frozen helper
# lemmas (`loopBody`, `implLoop`, the bridging theorems) exist only to relate the
# imperative loop to the fold; a positive that returns the fold directly does not
# need them, so it drops them and reproves the SAME obligation in two lines.
_PROOF_BODY = _BASE.split("-- proof-start\n", 1)[1].split("-- proof-end", 1)[0]

# The obligation, kept byte-identical by every positive (only its tactic body
# and the surrounding helper defs change).
_CORRECT_THM = (
    "theorem correct_lookupPathValid :\n"
    "    ∀ (models : Nat → ModelInfo) (startModel : Nat) (parts : List String),\n"
    "      problem_spec_lookupPathValid models startModel parts\n"
    "        (implementation_lookupPathValid models startModel parts) := by\n"
    "  intro models startModel parts\n"
)


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVES — structurally different but CORRECT impls that MUST
# verify. If a faithful correct reshape of the modeled behavior cannot satisfy
# `result = pathValid …`, the spec is SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------

# POS1 — return the grounded walk verdict directly. Maximally different control
# flow (no mutable loop, no accumulator): the impl IS the value the postcondition
# names. `rfl` closes after unfolding both sides.
_POS_CHEAPEST_IMPL = (
    "def implementation_lookupPathValid\n"
    "    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool :=\n"
    "  -- structurally different: return the grounded walk verdict directly\n"
    "  pathValid models startModel parts"
)
_POS_CHEAPEST_PROOF = (
    "\n" + _CORRECT_THM +
    "  unfold problem_spec_lookupPathValid implementation_lookupPathValid\n"
    "  rfl\n"
)
_pos_cheapest = _swap(
    _swap(_BASE, _IMPL_DEF, _POS_CHEAPEST_IMPL),
    "-- proof-start\n" + _PROOF_BODY + "-- proof-end",
    "-- proof-start" + _POS_CHEAPEST_PROOF + "-- proof-end",
)

# POS2 — a different-but-equivalent functional form: fold the step function
# directly over the whole path (the same recursion `pathValid` performs,
# spelled inline) instead of running the imperative loop. Reproves the SAME
# obligation; `rfl` closes after unfolding the spec, the impl, and `pathValid`.
_POS_FOLD_IMPL = (
    "def implementation_lookupPathValid\n"
    "    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool :=\n"
    "  -- structurally different: fold the step function directly over the path,\n"
    "  -- no mutable loop\n"
    "  !((parts.foldl (stepPath models) (some startModel, none, false)).2.2)"
)
_POS_FOLD_PROOF = (
    "\n" + _CORRECT_THM +
    "  unfold problem_spec_lookupPathValid implementation_lookupPathValid pathValid\n"
    "  rfl\n"
)
_pos_fold = _swap(
    _swap(_BASE, _IMPL_DEF, _POS_FOLD_IMPL),
    "-- proof-start\n" + _PROOF_BODY + "-- proof-end",
    "-- proof-start" + _POS_FOLD_PROOF + "-- proof-end",
)


# The "nothing declared here" filler model, used both by the admissibility case
# below and by every reject witness's graph.
_DEFAULT_MODEL = (
    "{ getField := fun _ => none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } }"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation must be SATISFIABLE at concrete inputs of the
# shape the reported failure is about, and must not be constantly true there.
#
# AUDIT NOTE (added). The port dropped this whole lane on the ground that "the
# frozen obligation has no precondition, so PRECOND-TOO-STRONG has no instance".
# That reason is not sufficient: on a TOTAL carrier the analogue of an
# over-strong precondition is the obligation being UNSATISFIABLE at exactly an
# F2P-shaped input, which a positive that discharges the obligation at that
# concrete input — by evaluation, as a `have`, before closing the frozen
# obligation verbatim — tests directly. This case does that, and it is not a
# restatement of the two soundness positives: those two reshape the IMPL and
# re-close the universally-quantified equation, which is a statement about impl
# shape; this one leaves impl and proof byte-identical to frozen and instead
# pins the spec's VALUE at two concrete points, one accepting and one rejecting.
#
# The two points are chosen as a matched pair so the case cannot pass by the
# spec being constantly true: a multi-hop path through a relation onto a value
# field is ACCEPTED (`["r","v"]` => true), and that same path continued one
# segment past the value field is REJECTED (`["r","v","v"]` => false). Both
# `have`s were forgery-tested during the audit: flipping either asserted
# verdict makes the build FAIL with `decide` proving the flipped claim false, so
# each `have` tracks the value it asserts rather than holding vacuously.
_ADMISS_GRAPH = (
    'fun m => if m = 0 then '
    '{ getField := fun s => if s = "r" then '
    "some { isRelation := true, target := 1, acceptsTransform := fun _ => false } else none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else if m = 1 then "
    '{ getField := fun s => if s = "v" then '
    "some { isRelation := false, target := 0, acceptsTransform := fun _ => false } else none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else " + _DEFAULT_MODEL
)

_ADMISS_HAVES = (
    "  -- ADMISSIBILITY: the obligation is SATISFIABLE at two concrete inputs of\n"
    "  -- the shape under spec, discharged here by evaluation before the frozen\n"
    "  -- obligation is closed verbatim below. A multi-hop path that descends a\n"
    "  -- relation onto a value field is ACCEPTED; the same path continued one\n"
    "  -- segment past that value field is REJECTED. So the spec is neither\n"
    "  -- unsatisfiable nor constantly true at these shapes.\n"
    "  have _hAcceptMultiHop :\n"
    "      problem_spec_lookupPathValid\n"
    "        (%s)\n"
    '        0 ["r", "v"] true := by\n'
    "    unfold problem_spec_lookupPathValid pathValid stepPath\n"
    "    decide\n"
    "  have _hRejectPastValueField :\n"
    "      problem_spec_lookupPathValid\n"
    "        (%s)\n"
    '        0 ["r", "v", "v"] false := by\n'
    "    unfold problem_spec_lookupPathValid pathValid stepPath\n"
    "    decide\n"
) % (_ADMISS_GRAPH, _ADMISS_GRAPH)

# Inserted at the head of the frozen impl body: impl logic and the whole frozen
# proof stay byte-identical, so the case tests satisfiability and nothing else.
_admiss = _swap(
    _BASE,
    "  let mut cur : Option Nat := some startModel\n",
    _ADMISS_HAVES + "  let mut cur : Option Nat := some startModel\n",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / REJECT rivals — each swaps ONLY the loop body, keeping the whole
# spec and the frozen proof verbatim, so the defect is attributable solely to
# the impl.
# ---------------------------------------------------------------------------

# R1 — the pk-alias fix reverted. Route the alias segment "pk" through the
# by-name resolver `getField` with NO special case, so "pk" (which `getField`
# never resolves) is wrongly treated as unresolved. Correct on every path
# containing no alias segment; diverges the moment "pk" appears.
_R1_BODY = _IMPL_BODY.replace(
    '        let resolved := if part == "pk" then some (models c).primaryKey\n'
    "                        else (models c).getField part",
    "        let resolved := (models c).getField part",
)
_r1 = _swap(_BASE, _IMPL_BODY, _R1_BODY)

# R2 — the non-relation descent-termination reverted. After a SUCCESSFUL
# non-relation resolution leave the current model in place instead of stepping
# off the graph, so a following segment spuriously resolves against the same
# model. Correct on any path of length <= 1 or that never follows a
# non-relation field with a further segment; diverges on the multi-hop-through-
# a-non-relation-field sub-domain.
_R2_BODY = _IMPL_BODY.replace(
    "            if f.isRelation then\n"
    "              cur := some f.target\n"
    "            else\n"
    "              cur := none",
    "            if f.isRelation then\n"
    "              cur := some f.target",
)
_r2 = _swap(_BASE, _IMPL_BODY, _R2_BODY)

# R3 — the transform-rescue escape hatch dropped. In BOTH resolution-failure
# arms flag the path unconditionally, ignoring whether the last resolved field
# accepts the segment as a registered transform. Correct on every path whose
# trailing segment is not a registered transform; diverges on a transform tail
# (e.g. ordering by a registered lookup), which is legitimately valid.
_R3_BODY = _IMPL_BODY.replace(
    "        | none =>\n"
    "            match fld with\n"
    "            | some pf => if !(pf.acceptsTransform part) then invalid := true\n"
    "            | none => invalid := true",
    "        | none =>\n"
    "            invalid := true",
).replace(
    "    | none =>\n"
    "        match fld with\n"
    "        | some pf => if !(pf.acceptsTransform part) then invalid := true\n"
    "        | none => invalid := true\n"
    "  return !invalid",
    "    | none =>\n"
    "        invalid := true\n"
    "  return !invalid",
)
_r3 = _swap(_BASE, _IMPL_BODY, _R3_BODY)

# R4 — the relation descent mis-targeted. Keep the relation test and keep the
# walk ON the graph, but advance to the CURRENT model index instead of the
# resolved field's `target`, so a following segment is resolved against the
# starting model's fields rather than the related model's. Correct on any path
# that never follows a relation field with a further segment, and correct even on
# a multi-hop path whenever the relation happens to point back at the model it
# was resolved on; diverges as soon as a relation leads somewhere else. This is
# the descent-TARGET sub-behavior, which R1-R3 leave unattacked: every one of
# their witness graphs has `isRelation := false` everywhere, so none of them
# reaches this arm of `stepPath` at all.
_R4_BODY = _IMPL_BODY.replace(
    "            if f.isRelation then\n"
    "              cur := some f.target",
    "            if f.isRelation then\n"
    "              cur := some c",
)
_r4 = _swap(_BASE, _IMPL_BODY, _R4_BODY)


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate directly at a concrete input over a
# fully-constructed model graph (an index-keyed `fun m => if m = k then … else …`
# so `startModel` is genuinely varied), and `decide` closes because every field
# — `getField`, `primaryKey`, `isRelation`, `acceptsTransform` — reduces on the
# concrete literals. Each witness ELABORATES against its rival (the rival's
# result differs from `pathValid …`) and FAILS against the frozen solution (gold
# agrees, so the negation is false). No witness binds a hypothesis, so there is
# no consistency obligation. Checked out of band with scripts/lean_verify.sh:
# each rival build exits 0, each gold build exits 1.
# ---------------------------------------------------------------------------
# (`_DEFAULT_MODEL`, the "nothing declared here" filler, is defined above — it is
# shared with the admissibility case's graph.)


def _witness(models, start, parts):
    return (
        "example : ¬ problem_spec_lookupPathValid\n"
        "    (%s)\n"
        "    (%s)\n"
        "    (%s)\n"
        "    (implementation_lookupPathValid\n"
        "      (%s)\n"
        "      (%s)\n"
        "      (%s)) := by\n"
        "  unfold problem_spec_lookupPathValid implementation_lookupPathValid\n"
        "  decide" % (models, start, parts, models, start, parts)
    )


# R1 graph: at model 0, `getField` resolves nothing and `primaryKey` is a
# non-relation field. Gold: "pk" resolves to `primaryKey` (found, non-relation,
# ends the walk) => valid. Rival: "pk" routes through `getField` => none, no
# prior field => invalid. Probes startModel = 0, parts = ["pk"].
_W1 = _witness(
    "fun m => if m = 0 then "
    "{ getField := fun _ => none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else " + _DEFAULT_MODEL,
    "0", '["pk"]')

# R2 graph: at model 1, `getField "a"` and `getField "b"` are both non-relation
# fields. Gold: after "a" (non-relation) the walk steps off (`cur = none`), so
# "b" is unresolved and "a" does not accept it => invalid. Rival: stays at model
# 1, so "b" resolves via `getField` => valid. Probes startModel = 1,
# parts = ["a","b"].
_W2 = _witness(
    "fun m => if m = 1 then "
    '{ getField := fun s => if s = "a" then '
    "some { isRelation := false, target := 0, acceptsTransform := fun _ => false } "
    'else if s = "b" then '
    "some { isRelation := false, target := 0, acceptsTransform := fun _ => false } "
    "else none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else " + _DEFAULT_MODEL,
    "1", '["a", "b"]')

# R3 graph: at model 2, `getField "a"` is a non-relation field that ACCEPTS "b"
# as a transform. Gold: after "a" the walk steps off; "b" is unresolved but the
# last field accepts it as a transform => valid. Rival: drops the rescue and
# flags "b" unconditionally => invalid. Probes startModel = 2, parts = ["a","b"]
# — a distinct graph and seed from R2.
_W3 = _witness(
    "fun m => if m = 2 then "
    '{ getField := fun s => if s = "a" then '
    "some { isRelation := false, target := 0, acceptsTransform := fun t => t = \"b\" } "
    "else none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else " + _DEFAULT_MODEL,
    "2", '["a", "b"]')

# R4 graph: model 3 resolves "r" as a RELATION field pointing at model 4, and
# model 4 resolves "b" as a plain value field; model 3 itself does NOT declare
# "b". Gold: "r" advances the walk to model 4, where "b" resolves => valid.
# Rival: "r" leaves the walk at model 3, where "b" is not declared and "r" does
# not accept it as a transform => invalid. Probes startModel = 3,
# parts = ["r","b"] — the only witness graph containing a relation field, so the
# only one that reaches the relation-descent arm of `stepPath`.
_W4 = _witness(
    "fun m => if m = 3 then "
    '{ getField := fun s => if s = "r" then '
    "some { isRelation := true, target := 4, acceptsTransform := fun _ => false } "
    "else none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else if m = 4 then "
    '{ getField := fun s => if s = "b" then '
    "some { isRelation := false, target := 0, acceptsTransform := fun _ => false } "
    "else none, "
    "primaryKey := { isRelation := false, target := 0, acceptsTransform := fun _ => false } } "
    "else " + _DEFAULT_MODEL,
    "3", '["r", "b"]')


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- SOUNDNESS POSITIVE #1: return the grounded verdict directly --------
    {
        "id": "pos-cheapest-return-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_cheapest,
        "rationale": (
            "`pathValid` is a total fold grounded in the inputs, so the cheapest "
            "honest correct impl returns it directly. A maximally different "
            "control-flow shape (no mutable loop, no accumulator) computing the "
            "same decision; the proof drops the loop-bridging helpers and closes "
            "by `rfl` after unfolding the spec and the impl — no new lemma, the "
            "`correct_lookupPathValid` statement byte-identical. Must verify "
            "against `result = pathValid …`; if a faithful correct impl cannot, "
            "the spec is SPEC-TOO-STRONG. Doubles as proof the postcondition is "
            "satisfiable."
        ),
    },

    # --- SOUNDNESS POSITIVE #2: inline fold, no imperative loop -------------
    {
        "id": "pos-inline-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_fold,
        "rationale": (
            "A structurally-different but behaviourally-identical impl: fold the "
            "step function directly over the whole path (the same recursion, "
            "spelled inline) instead of running the imperative `for` loop. "
            "Reproves the SAME obligation; `rfl` closes after unfolding the spec, "
            "the impl, and the grounded fold. A correct structural variant must "
            "verify (else SPEC-TOO-STRONG on the impl shape). Sibling of the "
            "nagini branch-reorder positive."
        ),
    },

    # --- ADMISSIBILITY: the obligation is satisfiable at the shapes under spec -
    {
        "id": "admiss-multihop-relation-path",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "The frozen obligation carries no precondition hypothesis, so the "
            "PRECOND-TOO-STRONG analogue on this total carrier is the obligation "
            "being UNSATISFIABLE at a concrete input of the shape under spec. "
            "This case tests that directly: impl logic and the entire frozen "
            "proof are byte-identical to frozen, and two `have`s discharge the "
            "spec predicate BY EVALUATION at two concrete points before the "
            "frozen obligation is closed verbatim. The points are a matched "
            "accept/reject pair over one graph — a path descending a relation "
            "onto a value field is accepted (`[\"r\",\"v\"]` => true), and the "
            "same path continued one segment past that value field is rejected "
            "(`[\"r\",\"v\",\"v\"]` => false) — so the case cannot pass by the "
            "spec being constantly true at these shapes, and if the spec were "
            "over-constrained at either point `decide` would fail. Distinct in "
            "purpose from the two soundness positives: those vary the IMPL shape "
            "and re-close the universally-quantified equation, whereas this one "
            "leaves impl and proof untouched and pins the spec's VALUE at "
            "concrete inputs."
        ),
    },

    # --- UNIQUENESS #1: pk-alias fix reverted -------------------------------
    {
        "id": "pk-alias-reverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r1,
        "refinement": (
            "This is the pre-fix behaviour: the identity alias segment is "
            "resolved through the by-name resolver with no special case. The "
            "by-name resolver has no entry for the alias, so the path is wrongly "
            "flagged invalid; the failing test asserts that a related reference "
            "whose trailing segment is the identity alias raises NO error, so a "
            "faithful patch keeping this behaviour reports one and would NOT "
            "resolve — it is exactly the regression the issue reports. A "
            "verifying rival here would be a true verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by `result = pathValid …` at the alias sub-behavior: the "
            "frozen `stepPath` resolves the alias segment via the model's "
            "`primaryKey` (which succeeds), but the rival routes it through the "
            "by-name resolver, which yields `none`, so the path is flagged where "
            "gold leaves it valid. Witness at startModel=0, parts=[\"pk\"], over "
            "a graph whose model 0 resolves nothing by name and has a "
            "non-relation primary-key field."
        ),
        "witness": _W1,
    },

    # --- UNIQUENESS #2: non-relation descent-termination reverted -----------
    {
        "id": "non-relation-reset-reverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r2,
        "refinement": (
            "This is the pre-fix behaviour: after resolving a non-relation field "
            "the walk does NOT step off the model graph, so a following segment "
            "is re-resolved against the same model and spuriously succeeds. The "
            "failing test constructs a reference that hops through a non-relation "
            "field into a further segment and asserts an error IS raised; this "
            "rival leaves it unflagged, so a faithful patch keeping it would NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by `result = pathValid …` at the descent-termination "
            "sub-behavior: the frozen `stepPath` sets `cur := none` after a "
            "non-relation resolution, so a following segment has no current model "
            "and the path is invalid; the rival keeps the current model, so the "
            "segment resolves and the path is valid. Witness at startModel=1, "
            "parts=[\"a\",\"b\"], over a graph whose model 1 resolves both "
            "segments as non-relation fields."
        ),
        "witness": _W2,
    },

    # --- UNIQUENESS #3: transform-rescue escape hatch dropped ---------------
    {
        "id": "transform-rescue-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r3,
        "refinement": (
            "Drops the escape hatch that tolerates an unresolved trailing segment "
            "when the last resolved field accepts it as a registered lookup, "
            "flagging every resolution failure unconditionally. A trailing "
            "registered transform is a legitimate target the fixed validator "
            "accepts; a faithful patch that dropped the guard would raise a "
            "spurious error on any valid registered-lookup tail (a regression on "
            "the ordering-allows-registered-lookups behaviour) and would NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by `result = pathValid …` at the transform-rescue "
            "sub-behavior: the frozen `stepPath` flags an unresolved segment only "
            "when the last field does NOT accept it as a transform, whereas this "
            "rival flags it unconditionally, so the two disagree on a transform "
            "tail. Witness at startModel=2, parts=[\"a\",\"b\"], over a graph "
            "whose model 2 resolves \"a\" as a non-relation field that accepts "
            "\"b\" as a transform — a distinct graph and seed from the other "
            "rivals."
        ),
        "witness": _W3,
    },

    # --- UNIQUENESS #4: relation descent mis-targeted -----------------------
    {
        "id": "relation-descent-mistargeted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r4,
        "refinement": (
            "Following a relation segment must continue the walk at the model the "
            "relation POINTS AT; this rival keeps walking at the model the "
            "relation was resolved on. A faithful patch with this defect resolves "
            "each later segment against the wrong model's field set, so a "
            "multi-segment reference through a relation is judged against fields "
            "that belong to the referring model: references that name a genuine "
            "field of the related model are reported as errors, and names that "
            "exist only on the referring model are wrongly accepted. Both the "
            "multi-hop and the related-target behaviours the failing tests pin "
            "would break, so it would NOT resolve."
        ),
        "rationale": (
            "Rejected by `result = pathValid …` at the relation-descent "
            "sub-behavior: the frozen `stepPath` sets `cur := some f.target` for a "
            "relation field, so the next segment is resolved against the related "
            "model; the rival sets `cur := some c`, keeping the current model, so "
            "the two disagree whenever a relation points somewhere other than "
            "where it was resolved. Witness at startModel=3, parts=[\"r\",\"b\"], "
            "over a graph where model 3 declares \"r\" as a relation onto model 4 "
            "and only model 4 declares \"b\" — the sole witness graph containing a "
            "relation field, hence the only case reaching this arm."
        ),
        "witness": _W4,
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle consumes no axiom. The
# graph accessors (`getField` / `primaryKey` / `isRelation` / `target` /
# `acceptsTransform`) are FREE DATA read by the grounded `pathValid` fold (an
# A-reference validated == the real callees by G-AX), not a consumed contract.
AXIOM_TESTS = []
