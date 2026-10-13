# properties.py — G-PBT falsification battery for matplotlib__matplotlib-26113 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried over,
# the mechanics re-expressed against THIS backend's carrier. Every SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte — only the impl region
# (and, for a soundness positive that legitimately reproves, the proof body) differs —
# so `markers.same_spec` holds by construction and any rejection is attributable to the
# postcondition rather than to a tampered spec. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the SPEC and not to a frozen
# tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
# ----------------------------------------------------------------------
#   hexbinAccum (cells : List (List Float)) (mincnt : Int) : List (Option Float)
#
# The per-cell reduce/leave-empty decision when binning points into grid cells with an
# auxiliary value array supplied. Each grid cell carries the collection of contributing
# values that fell into it; the shared count threshold `mincnt` decides which cells are
# summarised (their reduction value, `some v`) and which are left empty (`none`).
#
# The SINGLE postcondition is one equation:
#   problem_spec_hexbinAccum cells mincnt result  :=  result = cells.map (cellSummary mincnt)
# with  cellSummary mincnt acc = if (acc.length : Int) ≥ mincnt then some (reduceC acc)
#                               else none
# and it bundles several INDEPENDENT top-level obligations, which is what the battery
# partitions its rivals over:
#
#   (C1) THE THRESHOLD DECISION — the load-bearing clause. A cell is summarised exactly
#        when its point count is AT LEAST `mincnt`; a cell holding exactly `mincnt`
#        points is summarised, not skipped. This is the boundary the whole instance
#        turns on, and it lives entirely in exact `Int`/`Nat` arithmetic (mapping.md:
#        no opaque Float order is on the proof path), so it is refutable at literal
#        inputs with no conditioning at all.
#   (C2) THE SUMMARY VALUE — a summarised cell's entry is the reduction applied to THAT
#        cell's own collection. `reduceC` is opaque, so this clause is only attackable
#        where the reduction's ARGUMENT or the some/none TAG is observable structurally.
#   (C3) STRUCTURE / FRAME — one output entry per input cell, in the SAME ORDER and the
#        SAME COUNT (the `List.map` shape). This is where the lean analogue of nagini's
#        read-only-input obligation lives (see LANES THAT DO NOT PORT).
#
# BINDERS: `cells` (a list of per-cell value collections) and `mincnt` (the shared
# threshold). Both are VARIED across the reject witnesses: `mincnt` is probed at -1, 0, 1
# and 2 (a negative threshold, the unset-default regime, the headline threshold, and a
# threshold whose off-by-one neighbour is a positive count), and `cells` at length 1 and
# 2, with cells that are empty, that hold exactly `mincnt` points, and that hold more. A
# rival that mishandled only one of those regimes cannot hide behind a witness fixed
# elsewhere.
#
# Six of the eight original witnesses were rebuilt independently in an audit pass, each
# against its rival, against the frozen solution, and against a FORGERY asserting the
# opposite claim; all discriminate, and gold's failure is a plain evaluation
# (`unsolved goals ⊢ False`) that flips to exit 0 when the claim is flipped, so no
# rejection here rests on a tactic mismatch. The audit also measured that the two
# partial-domain rivals do NOT share a witness (each one's witness elaborates against
# the other rival, and the single-cell strict witness does not refute the
# after-first rival at all), confirming they are genuinely complementary sub-domains
# rather than two spellings of one.
#
# WHY THE OPAQUE CALLEE DOES NOT BLOCK THE REJECT LANE
# ---------------------------------------------------
# `reduceC : List Float → Float` is opaque with no constraining axiom, so no witness can
# COMPUTE a summary value. It does not need to: the discriminator this instance is about
# is the some/none TAG chosen by an exact integer comparison, and `some (reduceC acc)`
# vs `none` is a constructor disequality that `simp` closes without knowing anything
# whatever about `reduceC`. Most of the witnesses below turn on a cell whose
# collection is EMPTY (`[]`) or on the tag alone, so the opaque term never has to be
# evaluated; the two structural witnesses (order, count) mix an empty cell with a
# nonempty one so the two positions are distinguishable by tag. NO witness in this
# battery needs to condition on the carrier, and none binds a hypothesis — so there are
# no assumptions that could be jointly unsatisfiable.
#
# LANES THAT DO NOT PORT (and why — each is a deliberate disposition, not an oversight)
# -----------------------------------------------------------------------------------
#   * FRAME / PERMISSION MUTATION. The nagini sibling carries this as its MANDATORY
#     case: its input collection was held under a HALF permission that the postcondition
#     handed back, and a rival that WROTE into that input (clamping a sparse cell's count
#     up to the threshold, then reading it back so the comparison passes vacuously) was
#     rejected by the permission system before any postcondition was considered. Lean is
#     referentially transparent — no aliasing, no fractional permissions — so a
#     "store into a read-only input" rival is NOT EXPRESSIBLE here. The class is
#     genuinely VACUOUS on this carrier; no substitute has been fabricated. What survives
#     of that obligation is clause C3 (the result is pinned to `cells.map …`, fixing the
#     entry count and order and forbidding any entry to be sourced from a cell other than
#     its own), and C3 IS attacked, structurally, by `weak-drop-last-cell` (count) and
#     `weak-reverse-order` (order), plus C2's argument sourcing by the partial-domain
#     pair. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. A diverging impl IS writable here — `partial def
#     implementation_hexbinAccum … := implementation_hexbinAccum cells mincnt` — but it
#     is not SHIPPABLE as a reject case, and the reason was measured rather than assumed
#     (audit pass). A `partial def` is compiled to an opaque constant with no equation
#     lemmas, so `unfold implementation_hexbinAccum` fails on BOTH sides
#     (`Tactic `unfold` failed to unfold `implementation_hexbinAccum``) and every
#     literal-input witness dies on the RIVAL build — `witness-unproven`, an
#     inconclusive outcome, not a rejection. The conditioned form that the opaque
#     carrier does admit (`example (h : implementation_… = []) : ¬ problem_spec_… `)
#     was built too: it elaborates against the rival (exit 0) but ALSO against the
#     frozen solution (exit 0) — `witness-vacuous`, because `rw [h]` makes the claim a
#     statement about the hypothesis rather than about either impl. So there is no
#     witness shape that discriminates, and this is recorded as a KNOWN HOLE of the
#     spec (the obligation is stated over a total `def`, so it never constrains a
#     `partial` impl's fixpoint), NOT as a vacuous class. The nagini sibling carries no
#     divergence case for this instance either.
#   * FRAME / PERMISSION MUTATION — see above; the only class this battery records as
#     genuinely vacuous on this carrier.
#
# The ADMISSIBILITY lane is NOT dropped: an earlier revision recorded it "N/A" on the
# ground that the frozen obligation carries no precondition hypothesis, which is not a
# reason (a total carrier's analogue is the obligation being UNSATISFIABLE at an
# F2P-shaped input). It is landed below as `admiss-f2p-ground-instance`.
#   * AXIOM_TESTS. Dropped by instruction: the axiom lane is G-AX's job and this gate
#     ignores it. (`reduceC` carries no `_prop` axiom in the first place — mapping.md
#     records the callee as unchanged by the fix and asserts nothing about it — so G-AX
#     skips this bundle regardless.)
#
# CARRIER CORRESPONDENCE vs nagini
# --------------------------------
# Nagini abstracted each cell's value collection to its COUNT (an `int`) and each output
# entry to a `bool` populated-flag, so its postcondition was an index-`Forall` pinning
# `Result()[k]` to two grounded integer oracles. It also had to RESTRICT its modeled
# domain to a positive threshold, because at threshold 0 the empty-cell decision depends
# on the reduction's value on an empty collection — an effect a count-only abstraction
# cannot carry. This backend keeps the collections THEMSELVES (`List (List Float)`) and
# the entries as `Option Float`, so the empty-cell case is representable directly and the
# spec needs no threshold precondition; `weak-summarise-nothing` accordingly states its
# refutation at threshold 0, a point nagini's carrier had to exclude. Conversely nagini's
# cross-regime consistency conjunct (the value-supplied decision must equal the
# count-only one) has no counterpart: the count-only path is a separate, unmodeled code
# path here (mapping.md, flag dependencies), and its consistency with this one is the
# ISSUE's content rather than a second clause of this spec. The threshold-boundary
# argument itself ports directly and is the battery's centre of gravity.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26113"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors ------------------------------------------------------------------------
# `_IMPL` is the frozen loop body, lying ENTIRELY inside impl-start/impl-end and unique
# in the file. `_SIG` prefixes it with the `def` header (also entirely inside the impl
# region) for the rivals that abandon the monadic shape for a pure `match`. `_PROOF` is
# the whole proof region's content, swapped only by the positives that reprove.
_IMPL = (
    "  let mut accum : List (Option Float) := []\n"
    "  for acc in cells do\n"
    "    if (acc.length : Int) ≥ mincnt then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"
    "  return accum"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

_SIG = (
    "def implementation_hexbinAccum\n"
    "    (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do\n"
)
assert _BASE.count(_SIG + _IMPL) == 1, "impl header anchor drifted from expected text"

_PROOF_START, _PROOF_END = "-- proof-start\n", "-- proof-end"
_PROOF = _BASE[_BASE.index(_PROOF_START) + len(_PROOF_START):_BASE.index(_PROOF_END)]
assert "correct_hexbinAccum" in _PROOF, "proof anchor drifted from expected text"


def _loop(body):
    """The frozen monadic impl with a different per-cell loop body."""
    return ("  let mut accum : List (Option Float) := []\n"
            "  for acc in cells do\n" + body + "  return accum")


def _pure_impl(body):
    """Replace the whole impl (header included) with a pure, non-monadic `def`."""
    return _swap(
        _BASE, _SIG + _IMPL,
        "def implementation_hexbinAccum\n"
        "    (cells : List (List Float)) (mincnt : Int) : List (Option Float) :=\n"
        + body)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================

# pos-flipped-comparison — nagini's `pos-decision-count-form` ported directly. The
# per-cell test is written with the operands and the relation flipped
# (`mincnt ≤ length` rather than `length ≥ mincnt`): the SAME integer relation in a
# structurally different form, so the output is identical on every input. The theorem
# STATEMENT is byte-identical and the FROZEN proof body still closes, so this is a
# faithful restructure with no reproof and no new axiom/lemma/sorry. If it FAILS, the
# postcondition is over-fit to the literal operator form rather than to the behaviour
# => SPEC-TOO-STRONG.
#
# CALIBRATION (measured, audit pass; recorded so the case is not read as stronger
# evidence than it is). `≥` is NOTATION for the flipped `≤` in Lean, so this impl is
# DEFINITIONALLY the frozen one: an `example : @implFrozen = @implFlipped := rfl` over
# the two loop bodies elaborates (exit 0). So this positive is a RE-SPELLING, and its
# verification shows the spec is not keyed to the surface operator token — real, but
# weaker than "the spec admits a reshaped impl". The two positives below are what carry
# that stronger claim: `pos-swapped-branches` is measured NOT definitionally equal to
# the frozen impl (the same `rfl` probe FAILS on it, `Type mismatch … implFrozen =
# implSwapped`) and genuinely re-proves, and `pos-pure-map` abandons the monadic shape
# entirely.
_POS_FLIPPED = _swap(_BASE, _IMPL, _loop(
    "    if mincnt ≤ (acc.length : Int) then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"))

# pos-pure-map — nagini's `pos-oracle-local-reshape` ported. The impl drops the monadic
# accumulator loop entirely and maps the shared per-cell summary helper over the cells
# (a different DATA SHAPE: a direct helper application instead of an inlined comparison
# rebuilt per iteration). Semantics identical on every input. The theorem STATEMENT is
# byte-identical; the proof is reproven HONESTLY with `rfl` inside proof-start/proof-end,
# since the impl is now definitionally the spec's right-hand side — the cheapest tactic
# for the new shape, no new axiom/lemma/sorry, and the frozen loop-induction helper is
# simply no longer needed. If it FAILS => SPEC-TOO-STRONG (the spec would be bound to
# the monadic impl shape rather than to the behaviour).
_POS_PURE_MAP = _swap(
    _pure_impl("  cells.map (cellSummary mincnt)"),
    _PROOF,
    "theorem correct_hexbinAccum :\n"
    "    ∀ (cells : List (List Float)) (mincnt : Int),\n"
    "      problem_spec_hexbinAccum cells mincnt\n"
    "        (implementation_hexbinAccum cells mincnt) := by\n"
    "  intro cells mincnt\n"
    "  rfl\n")

# pos-swapped-branches — an additional positive with no nagini counterpart, covering the
# one restructure most likely to be confused with the pre-patch rival: the two arms of
# the per-cell conditional are EXCHANGED and the test negated (`mincnt > length` leaves
# the cell empty, otherwise summarise). Same decision on every input, but the strict `>`
# now appears literally in a CORRECT impl — so if the spec were secretly keyed to the
# operator token rather than to the decision, this is the case that catches it. The
# theorem STATEMENT is byte-identical; the proof body is the frozen one with the branch
# order tracked through and the two arithmetic side-goals closed by `omega` — no new
# axiom/lemma/sorry, no new top-level declaration. If it FAILS => SPEC-TOO-STRONG.
_POS_SWAPPED = _swap(
    _swap(_BASE, _IMPL, _loop(
        "    if mincnt > (acc.length : Int) then\n"
        "      accum := accum ++ [none]\n"
        "    else\n"
        "      accum := accum ++ [some (reduceC acc)]\n")),
    _PROOF,
    _PROOF
    .replace(
        "      (if (acc.length : Int) ≥ mincnt then\n"
        "        pure (ForInStep.yield (r ++ [some (reduceC acc)]))\n"
        "      else\n"
        "        pure (ForInStep.yield (r ++ [none])) : Id _)))",
        "      (if mincnt > (acc.length : Int) then\n"
        "        pure (ForInStep.yield (r ++ [none]))\n"
        "      else\n"
        "        pure (ForInStep.yield (r ++ [some (reduceC acc)])) : Id _)))")
    .replace(
        "    by_cases h : (a.length : Int) ≥ mincnt <;>\n"
        "      simp only [h, if_true, if_false, ih, cellSummary, List.map_cons,\n"
        "        List.append_assoc, List.cons_append, List.nil_append]",
        "    by_cases h : mincnt > (a.length : Int)\n"
        "    · have h' : ¬ ((a.length : Int) ≥ mincnt) := by omega\n"
        "      simp only [h, h', if_true, if_false, ih, cellSummary, List.map_cons,\n"
        "        List.append_assoc, List.cons_append, List.nil_append]\n"
        "    · have h' : (a.length : Int) ≥ mincnt := by omega\n"
        "      simp only [h, h', if_true, if_false, ih, cellSummary, List.map_cons,\n"
        "        List.append_assoc, List.cons_append, List.nil_append]")
    .replace(
        "            if (acc.length : Int) ≥ mincnt then do\n"
        "              pure PUnit.unit\n"
        "              pure (ForInStep.yield (r ++ [some (reduceC acc)]))\n"
        "            else do\n"
        "              pure PUnit.unit\n"
        "              pure (ForInStep.yield (r ++ [none]))",
        "            if mincnt > (acc.length : Int) then do\n"
        "              pure PUnit.unit\n"
        "              pure (ForInStep.yield (r ++ [none]))\n"
        "            else do\n"
        "              pure PUnit.unit\n"
        "              pure (ForInStep.yield (r ++ [some (reduceC acc)]))")
    .replace(
        "          (if (acc.length : Int) ≥ mincnt then\n"
        "            pure (ForInStep.yield (r ++ [some (reduceC acc)]))\n"
        "          else\n"
        "            pure (ForInStep.yield (r ++ [none])) : Id _))) := rfl",
        "          (if mincnt > (acc.length : Int) then\n"
        "            pure (ForInStep.yield (r ++ [none]))\n"
        "          else\n"
        "            pure (ForInStep.yield (r ++ [some (reduceC acc)])) : Id _))) := rfl"))
assert _POS_SWAPPED.count("omega") == 2, "swapped-branch reproof did not splice"


# ===========================================================================
# ADMISSIBILITY — the obligation is SATISFIABLE, and satisfiable at an
# F2P-SHAPED input rather than only in the abstract. Landed in an audit pass;
# the lane had been recorded "N/A" because the frozen theorem carries no
# precondition hypothesis, which is not a reason on a total carrier: the
# analogue of PRECOND-TOO-STRONG here is the obligation being unsatisfiable at
# exactly the input the failing test exercises, which a positive that
# discharges it at that concrete input — BY EVALUATION, as a `have`, before
# closing the frozen obligation verbatim — tests directly.
#
# The ground input mirrors the F2P scenario's cell shape: four grid cells, one
# holding two coincident points, two holding a single point each, and one
# empty, at the headline threshold of 1. Two `have`s, both inside the proof
# region, no new top-level declaration, statement byte-identical:
#   `_ground` discharges the spec predicate at that input;
#   `_eval` EVALUATES the modeled behaviour there down to a concrete four-entry
#           list, pinning WHICH cells are summarised — the single-point cells
#           among them, which is the decision the instance turns on. Without it
#           `_ground` would close by reflexivity without ever showing that the
#           input lands on the summarise side of the threshold.
# Measured load-bearing: the identical pair of `have`s spliced into the
# `weak-prepatch-strict-threshold` rival FAILS (exit 1, `unsolved goals ⊢ False`
# on `_eval`), so this positive is not something any impl would satisfy.
_ADM_CELLS = "[[(1.0 : Float), 1.0], [1.0], [1.0], ([] : List Float)]"
_ADM_HEAD = (
    "theorem correct_hexbinAccum :\n"
    "    ∀ (cells : List (List Float)) (mincnt : Int),\n"
    "      problem_spec_hexbinAccum cells mincnt\n"
    "        (implementation_hexbinAccum cells mincnt) := by\n")
_POS_ADMISS = _swap(
    _BASE, _ADM_HEAD,
    _ADM_HEAD
    + f"  have _ground : problem_spec_hexbinAccum {_ADM_CELLS} 1\n"
    f"      (implementation_hexbinAccum {_ADM_CELLS} 1) := by\n"
    "    unfold problem_spec_hexbinAccum implementation_hexbinAccum cellSummary\n"
    "    simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]\n"
    "    simp\n"
    f"  have _eval : implementation_hexbinAccum {_ADM_CELLS} 1\n"
    "      = [some (reduceC [1.0, 1.0]), some (reduceC [1.0]), some (reduceC [1.0]),"
    " none] := by\n"
    "    unfold implementation_hexbinAccum\n"
    "    simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]\n"
    "    simp\n")
assert _POS_ADMISS.count("_eval") == 1, "admissibility haves did not splice"


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for a reshaped impl, which is exactly why the gate reads the
# WITNESS — checked in a file with the obligation removed — and not the rival's build).
# ===========================================================================

# weak-prepatch-strict — THE pre-patch behaviour: the threshold test is STRICT, so a
# cell holding exactly `mincnt` points is left empty instead of summarised. Attacks C1
# at the boundary count == mincnt.
_RIV_STRICT = _swap(_BASE, _IMPL, _loop(
    "    if (acc.length : Int) > mincnt then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"))

# weak-over-inclusive — the off-by-one in the OTHER direction: the threshold is relaxed
# by one, so a cell one point SHORT of the threshold is wrongly summarised. Attacks C1
# on the count == mincnt - 1 sub-domain, which the strict rival gets right.
_RIV_OVER = _swap(_BASE, _IMPL, _loop(
    "    if (acc.length : Int) ≥ mincnt - 1 then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"))

# weak-summarise-everything — drops the threshold decision entirely: EVERY cell is
# summarised, however few points it holds (including none at all). Attacks C1 on the
# whole below-threshold sub-domain.
_RIV_ALL_SOME = _swap(_BASE, _IMPL, _loop(
    "    accum := accum ++ [some (reduceC acc)]\n"))

# weak-summarise-nothing — the mirror constant: EVERY cell is left empty, however many
# points it holds. Attacks C1 on the at-or-above-threshold sub-domain, and its witness
# is stated at threshold 0 — the regime where every cell, empty ones included, must be
# summarised, and the only witness in this battery that binds `mincnt` there.
_RIV_ALL_NONE = _swap(_BASE, _IMPL, _loop(
    "    accum := accum ++ [none]\n"))

# weak-drop-last-cell — decides every emitted cell correctly but omits the FINAL cell,
# returning one entry too few. Attacks C3 (entry count).
_RIV_DROP_LAST = _swap(
    _BASE, _IMPL,
    "  let mut accum : List (Option Float) := []\n"
    "  for acc in cells.dropLast do\n"
    "    if (acc.length : Int) ≥ mincnt then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"
    "  return accum")

# weak-reverse-order — decides every cell correctly and emits the right NUMBER of
# entries, but in reverse order, so each entry describes the wrong cell. Attacks C3
# (entry order) and, with it, C2's sourcing: a summarised entry must be the reduction of
# ITS OWN cell's collection. A permutation preserves the count, so the count probe
# cannot see it.
_RIV_REVERSE = _swap(
    _BASE, _IMPL,
    "  let mut accum : List (Option Float) := []\n"
    "  for acc in cells do\n"
    "    if (acc.length : Int) ≥ mincnt then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"
    "  return accum.reverse")

# weak-negative-threshold — added in an audit pass to close a measured gap: every rival
# above is refuted at a NON-NEGATIVE threshold (0, 1 or 2), so the spec's behaviour on
# the negative-`mincnt` sub-domain rested on no case at all. mapping.md records `Int`
# precisely so a negative threshold is expressible, and the modeled defaulting makes it
# reachable, so it is a real sub-domain rather than a carrier artefact. This rival is
# CORRECT on every non-negative threshold and additionally demands the threshold be
# non-negative, so at a negative threshold it leaves cells empty that gold summarises.
_RIV_NEG = _swap(_BASE, _IMPL, _loop(
    "    if (acc.length : Int) ≥ mincnt ∧ 0 ≤ mincnt then\n"
    "      accum := accum ++ [some (reduceC acc)]\n"
    "    else\n"
    "      accum := accum ++ [none]\n"))

# weak-strict-on-first-cell — nagini's `rival-partial-first-bin` ported. PARTIAL DOMAIN:
# correct on every cell except the FIRST, which uses the strict test. Attacks C1 on the
# leading-position sub-domain — a shape that no uniformly-wrong rival probes, and that a
# single-cell witness could never distinguish from the fully-strict rival.
_RIV_FIRST = _pure_impl(
    "  match cells with\n"
    "  | [] => []\n"
    "  | c0 :: rest =>\n"
    "      (if (c0.length : Int) > mincnt then some (reduceC c0) else none)\n"
    "        :: rest.map (cellSummary mincnt)")

# weak-strict-after-first-cell — the COMPLEMENTARY partial domain: correct on the first
# cell and strict on every later one. Deliberately the mirror of the case above, because
# that one is refuted at the leading position and this one AGREES with gold there; the
# two together pin that the threshold decision holds at EVERY position rather than at
# one probed position. Attacks C1 on the trailing sub-domain.
_RIV_AFTER_FIRST = _pure_impl(
    "  match cells with\n"
    "  | [] => []\n"
    "  | c0 :: rest =>\n"
    "      cellSummary mincnt c0\n"
    "        :: rest.map (fun acc =>\n"
    "             if (acc.length : Int) > mincnt then some (reduceC acc) else none)")


# --- witnesses ----------------------------------------------------------------------
# Each witness states `¬ problem_spec_hexbinAccum cells mincnt (implementation_… )` at a
# CONCRETE input, unfolds spec + impl + the per-cell summary helper, reduces the monadic
# loop, and lets `simp` close the resulting constructor/shape disequality. Each
# ELABORATES against its rival and FAILS on the frozen solution (measured: gold reduces
# the goal to `False`, i.e. the spec genuinely holds there). No witness binds a
# hypothesis, so none can be `witness-inconsistent`; none needs `reduceC` to be
# evaluated, since the discriminator is the some/none tag chosen by exact integer
# arithmetic.
_TAC = (
    "  unfold problem_spec_hexbinAccum implementation_hexbinAccum cellSummary\n"
    "  simp only [Id.run, List.forIn_cons, List.forIn_nil, List.dropLast, bind, pure]\n"
    "  simp\n")


def _wit(cells, mincnt):
    return (f"example : ¬ problem_spec_hexbinAccum {cells} {mincnt}\n"
            f"    (implementation_hexbinAccum {cells} {mincnt}) := by\n" + _TAC)


# C1 at the BOUNDARY: one cell holding exactly `mincnt` = 1 point. Gold summarises it;
# the strict rival leaves it empty. The headline threshold of the whole instance.
_WIT_STRICT = _wit("[[(1.0 : Float)]]", "1")

# C1 one point BELOW the threshold: a cell holding 1 point at threshold 2. Gold leaves
# it empty; the over-inclusive rival summarises it. Varies `mincnt` to 2 — the only
# witness here at a threshold whose off-by-one neighbour is still a positive count.
_WIT_OVER = _wit("[[(1.0 : Float)]]", "2")

# C1 well BELOW the threshold: an EMPTY cell at threshold 1. Gold leaves it empty; the
# summarise-everything rival summarises it. No opaque value is reachable on gold's side
# here, so the tag disequality is all that is needed.
_WIT_ALL_SOME = _wit("[([] : List Float)]", "1")

# C1 at threshold 0 — the regime where EVERY cell, empty ones included, must be
# summarised. Gold summarises the empty cell; the summarise-nothing rival leaves it
# empty. The only witness binding `mincnt` at 0.
_WIT_ALL_NONE = _wit("[([] : List Float), []]", "0")

# C3 (entry COUNT): two empty cells at threshold 1. Gold emits two entries, the
# drop-last rival one. Both cells are empty, so the shape disequality involves no opaque
# term at all.
_WIT_DROP_LAST = _wit("[([] : List Float), []]", "1")

# C3 (entry ORDER): an empty cell followed by a one-point cell at threshold 1. Gold
# emits empty-then-summarised; the reversing rival emits summarised-then-empty. The two
# positions are distinguishable by TAG, so the permutation is observable without
# evaluating the reduction.
_WIT_REVERSE = _wit("[([] : List Float), [1.0]]", "1")

# C1 at a NEGATIVE threshold: an empty cell at threshold -1, where gold summarises every
# cell unconditionally (a length is never below -1) and the non-negativity-demanding
# rival leaves it empty. The only witness in the battery binding `mincnt` below 0.
_WIT_NEG = _wit("[([] : List Float)]", "(-1)")

# C1 on the LEADING position: two cells each holding exactly `mincnt` = 1 point. Gold
# summarises both; the strict-on-first rival leaves the FIRST empty and gets the second
# right — so the refutation is pinned to position 0.
_WIT_FIRST = _wit("[[(1.0 : Float)], [1.0]]", "1")

# C1 on a TRAILING position: same shape, but here gold and the rival agree on the first
# cell and disagree on the second, so this probes the sub-domain the leading-position
# witness cannot reach. The two cells carry different values so the entries are not
# interchangeable.
_WIT_AFTER_FIRST = _wit("[[(2.0 : Float)], [1.0]]", "1")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-flipped-comparison",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLIPPED,
        "rationale": (
            "PORTS nagini's `pos-decision-count-form`. Structurally different but CORRECT "
            "impl: the per-cell threshold test is written with the operands and relation "
            "flipped (`mincnt ≤ count` instead of `count ≥ mincnt`) — the same integer "
            "relation in a different form, so the output is identical on every `cells`/"
            "`mincnt`. The theorem statement is byte-identical and the FROZEN proof body "
            "still closes, so no reproof and no new axiom/lemma/sorry. Defends clause C1 "
            "(the threshold decision). If it FAILS, the postcondition is over-fit to the "
            "literal operator form rather than to the behaviour => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE_MAP,
        "rationale": (
            "PORTS nagini's `pos-oracle-local-reshape`. A structurally different CORRECT "
            "impl: the monadic accumulator loop is dropped entirely in favour of mapping "
            "the shared per-cell summary helper over the cells — a different data shape "
            "(direct helper application vs an inlined comparison rebuilt per iteration) "
            "with identical semantics. The theorem STATEMENT is byte-identical; the proof "
            "is reproven honestly with `rfl` (the impl is now definitionally the spec's "
            "right-hand side), the cheapest tactic for the new shape, with no new axiom/"
            "lemma/sorry and no weakening of the obligation. Defends C1, C2 and C3 at "
            "once. If it FAILS => SPEC-TOO-STRONG (the spec would be bound to the monadic "
            "impl shape rather than to the behaviour)."
        ),
    },
    {
        "id": "pos-swapped-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SWAPPED,
        "rationale": (
            "No nagini counterpart; added because it covers the restructure most easily "
            "confused with the pre-patch rival. The two arms of the per-cell conditional "
            "are EXCHANGED and the test negated, so a cell is left empty when the "
            "threshold strictly exceeds its count and summarised otherwise: the same "
            "decision on every input, but with the strict operator now appearing "
            "literally inside a CORRECT impl. If the spec were secretly keyed to the "
            "operator token rather than to the decision, this is the case that catches "
            "it. The theorem STATEMENT is byte-identical; the proof body is the frozen "
            "one with the branch order tracked through and the two arithmetic side-goals "
            "closed by `omega` — no new axiom/lemma/sorry, no new declaration. If it "
            "FAILS => SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "The obligation is SATISFIABLE at an F2P-shaped ground input, not merely in "
            "the abstract. The frozen theorem carries no precondition hypothesis, so "
            "there is no binder for nagini's `admiss-selfcall` to attack; the analogue "
            "on this total carrier is the obligation being unsatisfiable at exactly the "
            "input the failing test exercises, which this case tests directly. Two "
            "`have`s inside the proof region — no new top-level declaration, statement "
            "byte-identical — discharge the spec predicate at a four-cell grid whose "
            "cells hold two, one, one and zero points at the headline threshold of 1, "
            "and then EVALUATE the modeled behaviour there to a concrete four-entry "
            "list. The second is what makes the admission load-bearing: it pins which "
            "cells are summarised (the single-point ones, the decision the instance "
            "turns on) rather than closing by reflexivity over an unexamined term. "
            "Measured: the identical pair spliced into the pre-patch strict rival FAILS. "
            "If it FAILS here => PRECOND-TOO-STRONG (the obligation would be "
            "unsatisfiable at a normal, in-domain input)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch-strict-threshold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STRICT,
        "refinement": (
            "THE pre-patch behaviour: the count test is STRICT, so a cell holding exactly "
            "the threshold number of points is left empty rather than summarised. Its "
            "faithful real patch is simply the UNCHANGED code. Under it, with a threshold "
            "of 1 the value-supplied path keeps only cells holding two or more points "
            "while the count-only path keeps every cell holding at least one, so the two "
            "renders differ. The F2P "
            "test_hexbin_mincnt_behavior_upon_C_parameter[png] compares exactly those two "
            "figures for equality at threshold 1 over a point set whose cells hold one "
            "point each, so it FAILS. It would NOT resolve — this is precisely the "
            "behaviour the fix changes (G-DIFF; Solution_prepatch.lean reproduces it and "
            "fails verification)."
        ),
        "rationale": (
            "REJECTED by clause C1 (the threshold decision) at the boundary count == "
            "mincnt. Witness: one cell holding exactly `mincnt` = 1 point — gold "
            "summarises it, the rival leaves it empty. The tag disequality closes with no "
            "reference to the opaque reduction. If it VERIFIED => SPEC-TOO-WEAK (the spec "
            "would admit the pre-patch off-by-one, which is the entire instance)."
        ),
        "witness": _WIT_STRICT,
    },
    {
        "id": "weak-over-inclusive-threshold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OVER,
        "refinement": (
            "The off-by-one in the OPPOSITE direction: the threshold is relaxed by one, so "
            "a cell one point short of it is wrongly summarised. Its faithful real patch "
            "is an over-relaxed count test. At a threshold of 2 it would summarise "
            "one-point cells that the count-only path leaves empty, so the two renders "
            "differ and the F2P figure-equality comparison FAILS; more generally it keeps "
            "cells the count-only path drops at every positive threshold, which is the "
            "same class of inconsistency the issue reports, merely mirrored. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on the count == mincnt - 1 sub-domain — precisely the "
            "sub-domain the strict rival handles CORRECTLY, so this is not a near-miss of "
            "that case but its complement. Witness: one cell holding 1 point at threshold "
            "2, where gold leaves it empty and the rival summarises it. This is the only "
            "witness binding `mincnt` at 2, i.e. at a threshold whose off-by-one "
            "neighbour is still a positive count. If it VERIFIED => SPEC-TOO-WEAK (the "
            "threshold could be relaxed without detection)."
        ),
        "witness": _WIT_OVER,
    },
    {
        "id": "weak-summarise-everything",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALL_SOME,
        "refinement": (
            "PORTS nagini's `rival-constant-true`. Drops the threshold decision entirely: "
            "every cell is summarised regardless of how few points it holds. Its faithful "
            "real patch removes the count test from the per-cell body, so no cell is ever "
            "marked absent and every grid cell is drawn — including the empty ones the "
            "threshold exists to suppress. The count-only path still suppresses them, so "
            "the value-supplied render shows spurious cells the reference render does not "
            "and the F2P figure-equality comparison FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on the whole below-threshold sub-domain. Witness: an "
            "EMPTY cell at threshold 1 — gold leaves it empty, the rival summarises it. "
            "Varies `cells` to a cell holding zero points, a regime no other C1 witness "
            "here binds (the two off-by-one witnesses both probe a one-point cell). If it "
            "VERIFIED => SPEC-TOO-WEAK (a constant impl would satisfy the postcondition)."
        ),
        "witness": _WIT_ALL_SOME,
    },
    {
        "id": "weak-summarise-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALL_NONE,
        "refinement": (
            "The mirror constant, with no nagini counterpart (its count-only carrier had "
            "to exclude the zero threshold, so it could not state this refutation): every "
            "cell is left empty however many points it holds. Its faithful real patch "
            "marks every cell absent, so the value-supplied render draws nothing at all "
            "while the reference render draws the populated cells — the F2P figure-"
            "equality comparison FAILS, as would every rendering assertion about this "
            "path. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on the at-or-above-threshold sub-domain — the "
            "complement of `weak-summarise-everything`, so the two together pin BOTH "
            "directions of the decision rather than one. Witness is stated at threshold "
            "0, the regime in which every cell including an empty one must be summarised: "
            "gold summarises, the rival does not. This is the ONLY witness in the battery "
            "binding `mincnt` at 0, which is also the unset-default regime and a point "
            "nagini's abstraction could not represent. If it VERIFIED => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_ALL_NONE,
    },
    {
        "id": "weak-drop-last-cell",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_LAST,
        "refinement": (
            "PORTS nagini's `rival-drop-last-bin`. Decides every emitted cell correctly "
            "but omits the FINAL cell, returning one entry too few. Its faithful real "
            "patch is an off-by-one over the per-cell collections that stops one short. "
            "The resulting entry sequence is shorter than the cell grid it indexes, so the "
            "downstream selection of which cells to draw is misaligned and the last cell "
            "is missing from the render; the F2P figure-equality comparison FAILS (and in "
            "the real code a length mismatch against the grid coordinates would not even "
            "render). It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (STRUCTURE — one entry per input cell, same count). "
            "This is the clause that carries what nagini enforced through its read-only "
            "input permission: the result is pinned to a map over `cells`, so the entry "
            "count cannot drift. Witness: two EMPTY cells at threshold 1, where gold "
            "emits two entries and the rival one — a purely structural probe with no "
            "opaque term in sight, and the only witness varying the `cells` LENGTH while "
            "holding every cell's content fixed. If it VERIFIED => SPEC-TOO-WEAK (the "
            "entry count would be unpinned)."
        ),
        "witness": _WIT_DROP_LAST,
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "Decides every cell correctly and emits the right NUMBER of entries, but in "
            "reverse order, so each entry describes a different cell than the one it is "
            "read against. Its faithful real patch walks the per-cell collections "
            "backwards. Each grid position then receives another cell's verdict and "
            "value, so the render is mirrored: cells that hold points are drawn empty and "
            "vice versa, and the F2P figure-equality comparison FAILS. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (entry ORDER) and with it C2's sourcing requirement — "
            "a summarised entry must be the reduction of ITS OWN cell's collection. "
            "Distinct from `weak-drop-last-cell`, which probes the entry COUNT and is "
            "blind to a permutation (the count is preserved). Witness: an empty cell "
            "followed by a one-point cell at threshold 1, so the two positions are "
            "distinguishable by their some/none tag and the permutation is observable "
            "without evaluating the opaque reduction. If it VERIFIED => SPEC-TOO-WEAK "
            "(the entry order, hence the cell-to-entry correspondence, would be unpinned)."
        ),
        "witness": _WIT_REVERSE,
    },
    {
        "id": "weak-negative-threshold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEG,
        "refinement": (
            "Correct at every non-negative threshold, but additionally demands the "
            "threshold be non-negative, so at a negative threshold it leaves every cell "
            "empty where the intended rule summarises every cell (no count is below a "
            "negative bound). Its faithful real patch guards the keep test with a "
            "non-negativity check on the threshold. The threshold reaches this path as a "
            "caller-supplied number, so a negative value is an in-domain input the "
            "modeled behaviour must handle; under this rival the value-supplied path "
            "would draw nothing there while the count-only path draws every cell, "
            "reintroducing exactly the cross-path disagreement the fix removes, so the "
            "F2P figure-equality comparison would FAIL on such a configuration. At the "
            "F2P's own threshold of 1 it agrees with gold, so this rival is NOT the "
            "instance's behaviour and it would NOT resolve — its defect is confined to "
            "the negative sub-domain."
        ),
        "rationale": (
            "REJECTED by clause C1 on the NEGATIVE-threshold sub-domain. Added in an "
            "audit pass to close a measured gap: every other rival here is refuted at a "
            "threshold of 0, 1 or 2, so the spec's behaviour below zero rested on no "
            "case at all, even though mapping.md chose `Int` precisely to make it "
            "expressible. Witness: an empty cell at threshold -1, where gold summarises "
            "and the rival does not — the only witness in the battery binding `mincnt` "
            "below 0. If it VERIFIED => SPEC-TOO-WEAK (the decision could be silently "
            "conditioned on the threshold's sign)."
        ),
        "witness": _WIT_NEG,
    },
    {
        "id": "weak-strict-on-first-cell",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRST,
        "refinement": (
            "PORTS nagini's `rival-partial-first-bin`. PARTIAL DOMAIN: the threshold "
            "decision is correct for every cell except the FIRST, which uses the strict "
            "test. Its faithful real patch special-cases the leading cell of the "
            "per-cell traversal (the leading entry handled by the old strict test, the "
            "rest by the intended one). Under it a leading cell holding exactly the "
            "threshold number of points is dropped from the value-supplied render but "
            "kept in the count-only reference render, so the F2P figure-equality "
            "comparison FAILS at that cell. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on the LEADING-position sub-domain. Genuinely distinct "
            "from `weak-prepatch-strict-threshold`: it is CORRECT on every non-leading "
            "cell, so it agrees with gold everywhere a single-cell witness could look and "
            "only the `cells` binder at length >= 2 exposes it. Witness: two cells each "
            "holding exactly `mincnt` = 1 point, where gold summarises both, the rival "
            "leaves the FIRST empty, and both agree on the second — pinning the "
            "refutation to position 0. If it VERIFIED => SPEC-TOO-WEAK (the threshold "
            "decision could be dropped on a positional sub-domain)."
        ),
        "witness": _WIT_FIRST,
    },
    {
        "id": "weak-strict-after-first-cell",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_AFTER_FIRST,
        "refinement": (
            "The COMPLEMENTARY partial domain: correct on the first cell and strict on "
            "every later one. Its faithful real patch applies the intended test only to "
            "the leading entry of the per-cell traversal and the old strict one "
            "thereafter. Under it every non-leading cell holding exactly the threshold "
            "number of points is dropped from the value-supplied render while the "
            "count-only reference render keeps it — over the F2P's point set, which "
            "places single-point cells at several distinct grid positions, the "
            "figure-equality comparison FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on the TRAILING sub-domain. Deliberately the mirror of "
            "`weak-strict-on-first-cell`, and NOT sharing its witness: this rival AGREES "
            "with gold at the leading position, so the position-0 witness does not refute "
            "it, and its own witness must state the refutation at position 1 instead "
            "(with the two cells carrying different values so the entries are not "
            "interchangeable). Together the pair pin that the threshold decision holds at "
            "EVERY position rather than at whichever one a witness happened to probe. If "
            "it VERIFIED => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_AFTER_FIRST,
    },
]


# The axiom lane is G-AX's job and this gate ignores it. `reduceC` is the sole opaque
# callee and carries no constraining property, so there is nothing for the spec lane to
# test there in any case.
AXIOM_TESTS = []
