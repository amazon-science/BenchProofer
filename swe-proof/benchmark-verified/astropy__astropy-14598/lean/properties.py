# properties.py — PBT falsification battery for astropy__astropy-14598 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, for a reshaped-but-correct positive, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_segmentValue` STATEMENT is preserved
# verbatim. No case introduces sorry/admit/native_decide/axiom or any new
# theorem/lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts TWO functions over List[int] code points — a full
# payload recovery and a single un-escape pass — each with read-only half-
# permission inputs. This Lean bundle models the SAME behavior on a single purely
# functional carrier: one function taking the value/comment substring of a
# (sub)card as `List Char` and returning `Option (List Char)` — `some v` = the
# segment is in the expected quoted shape and `v` is its contributed text, `none`
# = it is not (the caller keeps the segment verbatim). The whole cleanup pipeline
# the nagini pair split across two functions (token capture, trailing-whitespace
# trim, single trailing continuation-marker trim, and the preservation of
# interior doubled quotes) is fused into the single load-bearing clause
#     result = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s))
# so every nagini rival maps to a mis-step of ONE stage of that fused pipeline.
#
# DEFENDED SURFACE (what every rival attacks) — the single master relation above,
# and its independent consequences:
#   * the none/some SELECTION: `none` exactly when the segment is not in the
#     quoted shape, `some` otherwise;
#   * FULL token recovery: no trailing code point is dropped (the anchoring fix);
#   * interior doubled-quote PRESERVATION: an embedded `''` stays `''`, never
#     collapsed to `'` (the removed second-pass un-escape);
#   * trailing-whitespace trim (`dropTrailingWs`);
#   * single trailing continuation-marker trim (`dropTrailingAmp`).
#   * the ORDER of the two trim stages, and the MULTIPLICITY of the marker trim
#     (each stage being present does not pin either).
# Input binder of the spec predicate: the single `vc : List Char`. The reject
# witnesses vary it across EIGHT distinct points (non-quoted segment; embedded
# `''`; two-char token; token with an interior trailing space; token with a
# trailing marker; single-char token; marker followed by whitespace; two
# trailing markers) so every stage above is exercised, and both the `none` and
# `some` halves of the result are attacked in BOTH directions.
#
# AUDIT NOTE — what the first port left open, and what closed it.
# An independent audit re-derived all six original witnesses (each elaborates
# against its rival and fails on gold with `decide` COMPUTING the frozen value,
# i.e. a semantic refutation, not a tactic gap) and found the outcomes earned but
# the surface under-covered on three axes, each now carrying its own rival:
#   * stage ORDER (R7) — R4/R5 show each trim stage is present, neither pins the
#     sequence, so a spec fixing the set but not the order would have passed;
#   * marker-trim MULTIPLICITY (R8) — R5 only omits the stage, so trimming the
#     marker repeatedly went unattacked;
#   * the `some` half of the SELECTION (R9) — R6 attacks only the `none` half.
# The audit also found both original positives close by a bare `rfl`, so they are
# definitionally equal to the frozen impl and test the obligation only up to
# reduction; POS 3 adds a correct reshape that `rfl` does NOT close.
#
# A SECOND independent audit re-ran every build rather than reading outcomes:
#   * all 9 reject witnesses rebuilt — each elaborates against its rival (exit 0)
#     and fails on gold (exit 1) with `decide` COMPUTING the frozen value, i.e. a
#     semantic refutation, and the FORGERY test confirms gold's exit code tracks
#     the CLAIM: dropping the `¬` flips gold to exit 0 and the rival to exit 1 on
#     all 9, so no case is hollow. Every rival was also confirmed observably
#     different from gold at its witness point by an independent value model, so
#     none is a mere reshape.
#   * POS 3's non-defeq claim was checked directly: its impl under the FROZEN
#     bare-`rfl` proof fails (`Option.map cleanTailRev` not defeq to the spec's
#     right-hand side), so the case really does test the obligation as a
#     proposition.
#   * SPEC-TOO-WEAK probe: three NEW wrong impls not in the battery — a third
#     whitespace trim after the marker trim, an UNBOUNDED trailing-marker strip,
#     and a marker trim guarded by `length > 1` — all REJECT. No spec hole found.
#   * SPEC-TOO-STRONG probe: two NEW correct reshapes — whitespace trim applied
#     twice (idempotent) and `Option.bind`/`pure` in place of `Option.map` — both
#     VERIFY. The spec is not over-fit to the frozen combinator.
#   * The one real defect found: the ADMISSIBILITY lane was dropped for a reason
#     that does not hold on a total carrier. `admiss-ground-f2p-shape` lands it.
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * the FRAME / permission-mutation class (nagini `frame-mutate-segment`,
#     `frame-mutate-witness`) is VACUOUS on this backend: Lean is referentially
#     transparent — there is no aliasing or fractional permission to violate, so
#     there is no counterpart rival to author.
#   * the ADMISSIBILITY positive (nagini `admiss-recover-fshape`) DOES have a
#     counterpart and now carries one. The first port dropped it because
#     `correct_segmentValue` is an unconditional `∀ vc` with no precondition
#     hypothesis — but "no precondition" is not the analogue on a total carrier.
#     The analogue is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, and a positive that discharges the obligation at that
#     concrete input BY EVALUATION — as a `have`, before closing the frozen
#     obligation verbatim — tests that directly. `admiss-ground-f2p-shape` does
#     that at the one input shape that fuses every stage of the pipeline at once.
#   * DIVERGENCE / non-termination: nothing to ship here, and the reason is the
#     settled one recorded in `the corpus-wide termination-semantics finding` — the known spec hole
#     is scoped to the 401 velvet bundles carrying
#     `set_option loom.semantics.termination "partial"`, and lean is unaffected.
#     This bundle sets no such option and `implementation_segmentValue` is a
#     total Lean `def` checked by the equation compiler, so there is no partial-
#     correctness escape to attack. Not re-derived, not re-reported as a new hole.
#     (The nagini sibling carries no such case regardless.)
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job and this bundle ships
#     no consumed axiom (the parse/cleanup pipeline is modeled structurally, not
#     over an opaque callee — the axioms region is intentionally empty).
from pathlib import Path

INSTANCE = "astropy__astropy-14598"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each strictly INSIDE the impl / proof region of the frozen
# Solution.lean, and unique in the file.
# ---------------------------------------------------------------------------

# The frozen impl (whole def, impl region body).
_GOLD_IMPL = """def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
  match matchToken vc with
  | none => return none
  | some token =>
      let mut value := token
      value := dropTrailingWs value
      value := dropTrailingAmp value
      return some value"""

# The frozen proof body (only touched by a reshaped-but-correct positive, which
# needs a proof that closes for the new impl shape).
_GOLD_PROOF = """  intro vc
  unfold problem_spec_segmentValue implementation_segmentValue
  cases matchToken vc with
  | none => rfl
  | some token => rfl"""

assert _BASE.count(_GOLD_IMPL) == 1, "impl anchor drift"
assert _BASE.count(_GOLD_PROOF) == 1, "proof anchor drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls of
# the same fused pipeline. Each keeps the frozen `theorem correct_segmentValue`
# STATEMENT and reproves it for the new shape. If a faithful correct reshape
# cannot satisfy the master clause the spec would be SPEC-TOO-STRONG.
# ===========================================================================

# POS 1 — collapse the `let mut` chain into a single composed expression inside
# the same `do`/`match` control shape. Same value, no mutable local.
_POS1_IMPL = """def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
  match matchToken vc with
  | none => return none
  | some token =>
      return some (dropTrailingAmp (dropTrailingWs token))"""
_POS1_PROOF = """  intro vc
  unfold problem_spec_segmentValue implementation_segmentValue
  cases matchToken vc with
  | none => rfl
  | some token => rfl"""

# POS 2 — drop the imperative `do` entirely and express the pipeline as a pure
# `Option.map`, mirroring the spec's own right-hand side but arrived at by a
# different (non-monadic) construction. Proof closes by `rfl` after unfolding.
_POS2_IMPL = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token => dropTrailingAmp (dropTrailingWs token))"""
_POS2_PROOF = """  intro vc
  unfold problem_spec_segmentValue implementation_segmentValue
  rfl"""

# POS 3 — a correct reshape that is NOT definitionally equal to the frozen impl.
# POS 1 and POS 2 both close by a bare `rfl`, i.e. they reduce to the frozen
# right-hand side, so they exercise the obligation only up to defeq. This one
# FUSES the two cleanup stages into a single pass over the REVERSED token: it
# drops trailing whitespace and a trailing marker while the list is reversed and
# reverses back once, so the two `.reverse` round-trips of the frozen shape never
# appear. Extensionally the same value at every input, but `rfl` does NOT close
# it — the proof has to go through `List.getLast?_reverse` and case on the
# marker test. That makes it the only positive that tests the obligation as a
# PROPOSITION rather than as a reduction; if the spec could not be reproven for
# it the spec would be SPEC-TOO-STRONG for a faithful correct impl.
_POS3_IMPL = """def cleanTailRev (cs : List Char) : List Char :=
  match cs.reverse.dropWhile isWs with
  | [] => []
  | c :: t => if c == '&' then t.reverse else (c :: t).reverse
def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map cleanTailRev"""
_POS3_PROOF = """  intro vc
  unfold problem_spec_segmentValue implementation_segmentValue
  cases h : matchToken vc with
  | none => rfl
  | some token =>
      simp only [Option.map_some]
      congr 1
      unfold cleanTailRev dropTrailingAmp dropTrailingWs
      cases hr : token.reverse.dropWhile isWs with
      | nil => simp
      | cons c t =>
          rw [List.getLast?_reverse]
          cases hc : (c == '&') with
          | true => simp [hc]
          | false => simp [hc]"""


# ===========================================================================
# ADMISSIBILITY (expect="verify") — the obligation is SATISFIABLE at a concrete
# F2P-shaped input, shown by discharging it there by EVALUATION before closing
# the frozen obligation verbatim.
#
# On a total carrier the frozen obligation carries no precondition hypothesis, so
# there is no `Requires` to prove admits a legitimate input. The analogue is the
# obligation being unsatisfiable at exactly an F2P-shaped point: if the modeled
# behavior and the master clause disagreed at the very input shape the failing
# test exercises, `decide` would refute the ground instance and this case would
# fail while every uniqueness rival still rejected — a PRECOND-TOO-STRONG-shaped
# defect the other two lanes cannot see. The `have` is a ground instance of the
# SAME predicate (no new declaration, no new hypothesis, statement byte-identical),
# followed by the frozen proof body unchanged.
#
# The input is the shape that loads every stage of the fused pipeline at once: a
# quoted token carrying an interior doubled quote AND a trailing continuation
# marker, so the ground evaluation simultaneously exercises the `some` half of
# the selection, full token recovery, doubled-quote preservation, and the
# marker trim. Gold's value there retains the doubled quote and loses exactly
# the marker.
_ADM_INPUT = ("[Char.ofNat 39, Char.ofNat 120, Char.ofNat 120, Char.ofNat 39, "
              "Char.ofNat 39, Char.ofNat 38, Char.ofNat 39]")
_ADM_PROOF = ("""  have _ground : problem_spec_segmentValue
      (%s)
      (implementation_segmentValue
        (%s)) := by
    unfold problem_spec_segmentValue implementation_segmentValue
    decide
""" % (_ADM_INPUT, _ADM_INPUT)) + _GOLD_PROOF


# ===========================================================================
# UNIQUENESS rivals (expect="reject") — each mishandles ONE stage of the fused
# pipeline; each carries a witness SEEN to discriminate (elaborates against the
# rival, fails against gold, single input point).
# ===========================================================================

# R1 — DOUBLE UN-ESCAPE: re-adds a second collapse of interior `''`->`'` after
# the cleanup (the pre-patch second-pass un-escape). Correct on any recovered
# value with no surviving `''`; wrong wherever a doubled quote survives.
_REJ_COLLAPSE = """def collapseDoubled : List Char → List Char
  | [] => []
  | [c] => [c]
  | c1 :: c2 :: rest =>
      if c1 == quote && c2 == quote then quote :: collapseDoubled rest
      else c1 :: collapseDoubled (c2 :: rest)
def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token => collapseDoubled (dropTrailingAmp (dropTrailingWs token)))"""

# R2 — TRUNCATE TAIL: drop the last code point of the recovered value (a
# partially-fixed capture that still loses the final character).
_REJ_DROPLAST = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token => (dropTrailingAmp (dropTrailingWs token)).dropLast)"""

# R3 — EMPTY RECOVERY: return the empty value for every matched segment (the
# cheapest impl ignoring the captured token).
_REJ_EMPTY = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun _ => ([] : List Char))"""

# R4 — SKIP WHITESPACE TRIM: omit the trailing-whitespace-trim stage entirely
# (leaves padding on the recovered value).
_REJ_SKIPWS = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token => dropTrailingAmp token)"""

# R5 — SKIP MARKER TRIM: omit the single trailing continuation-marker-trim stage
# (leaves the marker on the recovered value).
_REJ_SKIPAMP = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token => dropTrailingWs token)"""

# R6 — NONE-BRANCH FLIP: signal a matched empty value on a segment that is NOT
# in the quoted shape (the caller would then discard the verbatim segment).
_REJ_NONECASE = """def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
  match matchToken vc with
  | none => return (some [])
  | some token =>
      return some (dropTrailingAmp (dropTrailingWs token))"""

# R7 — STAGE ORDER SWAP: both cleanup stages are present, but composed in the
# other order (marker trim first, then whitespace trim). R4/R5 only check that
# each stage is PRESENT; neither pins their ORDER, so without this rival a spec
# that fixed the set of stages but not their sequence would pass the battery.
# Observably wrong wherever whitespace follows the marker in the captured token.
_REJ_ORDERSWAP = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token => dropTrailingWs (dropTrailingAmp token))"""

# R8 — MARKER TRIM APPLIED TWICE: the spec pins the removal of at most ONE
# trailing marker; this strips two. Agrees with the frozen pipeline on every
# value carrying fewer than two trailing markers, so it is a genuine near-miss
# on the multiplicity of that stage — an axis no other rival varies.
_REJ_TWICEAMP = """def implementation_segmentValue (vc : List Char) : Option (List Char) :=
  (matchToken vc).map (fun token =>
    dropTrailingAmp (dropTrailingAmp (dropTrailingWs token)))"""

# R9 — SELECTION FLIP, other direction: report NO match for every segment. R6
# attacks the `none` half by claiming a match where there is none; this attacks
# the `some` half by denying a match for a segment that IS in the expected
# shape, so between them both directions of the selection are pinned.
_REJ_ALLNONE = """def implementation_segmentValue (_vc : List Char) : Option (List Char) := none"""


# ---------------------------------------------------------------------------
# Witness inputs, as `List Char` literals built from ASCII code points
# (39 = ' , 120 = 'x' , 121 = 'y' , 32 = space , 38 = '&' , 97 = 'a').
# Every witness states the spec predicate directly at a concrete, decide-able
# point; it holds of the rival and fails on gold.
# ---------------------------------------------------------------------------

# 'x'''  — recovered value has a surviving interior `''`; R1 collapses it.
_W_COLLAPSE = "[Char.ofNat 39, Char.ofNat 120, Char.ofNat 39, Char.ofNat 39, Char.ofNat 39]"
# 'xy'   — two-char token; R2 drops the final 'y'.
_W_DROPLAST = "[Char.ofNat 39, Char.ofNat 120, Char.ofNat 121, Char.ofNat 39]"
# 'x'    — single-char token; R3 returns empty.
_W_EMPTY = "[Char.ofNat 39, Char.ofNat 120, Char.ofNat 39]"
# 'x '   — token carries an interior trailing space; R4 keeps it.
_W_SKIPWS = "[Char.ofNat 39, Char.ofNat 120, Char.ofNat 32, Char.ofNat 39]"
# 'x&'   — token ends in a continuation marker; R5 keeps it.
_W_SKIPAMP = "[Char.ofNat 39, Char.ofNat 120, Char.ofNat 38, Char.ofNat 39]"
# a      — not a quoted segment (leading non-quote, no acceptable remainder);
#          gold yields `none`, R6 yields `some []`.
_W_NONECASE = "[Char.ofNat 97]"
# 'x& '  — marker then whitespace: gold trims the space, then the marker, giving
#          `x`; R7's reversed order trims nothing off the marker and keeps `x&`.
_W_ORDERSWAP = ("[Char.ofNat 39, Char.ofNat 120, Char.ofNat 38, Char.ofNat 32, "
                "Char.ofNat 39]")
# 'x&&'  — two trailing markers: gold removes exactly one (`x&`), R8 removes both.
_W_TWICEAMP = ("[Char.ofNat 39, Char.ofNat 120, Char.ofNat 38, Char.ofNat 38, "
               "Char.ofNat 39]")
# 'x'    — a segment that IS in the expected shape; gold yields `some [x]`,
#          R9 yields `none`.
_W_ALLNONE = "[Char.ofNat 39, Char.ofNat 120, Char.ofNat 39]"


def _witness(lit):
    return (
        "example : ¬ problem_spec_segmentValue\n"
        "    (%s)\n"
        "    (implementation_segmentValue\n"
        "      (%s)) := by\n"
        "  unfold problem_spec_segmentValue implementation_segmentValue\n"
        "  decide" % (lit, lit))


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL 1 (soundness) ----------------------------------
    {
        "id": "pos-control-composed-expr",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS1_IMPL),
                        _GOLD_PROOF, _POS1_PROOF),
        "rationale": (
            "A structurally-different but CORRECT impl: the imperative `let mut` "
            "cleanup chain is collapsed into a single composed expression inside "
            "the same do/match shape. Same value, no mutable local. It must "
            "verify against the master clause "
            "`result = (matchToken vc).map (dropTrailingAmp ∘ dropTrailingWs)`; if "
            "a faithful correct reshape cannot, the spec is SPEC-TOO-STRONG."
        ),
    },

    # --- POSITIVE CONTROL 2 (soundness) ----------------------------------
    {
        "id": "pos-control-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS2_IMPL),
                        _GOLD_PROOF, _POS2_PROOF),
        "rationale": (
            "A second correct reshape that abandons the imperative `do` block "
            "entirely and constructs the result as a pure `Option.map` of the "
            "cleanup pipeline. A genuinely different construction reaching the "
            "same value; the proof closes by `rfl`. Defends the single obligation "
            "from a non-monadic control shape as well."
        ),
    },

    # --- POSITIVE CONTROL 3 (soundness, NOT defeq) ------------------------
    {
        "id": "pos-control-fused-reverse-trim",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS3_IMPL),
                        _GOLD_PROOF, _POS3_PROOF),
        "rationale": (
            "The only positive that is NOT definitionally equal to the frozen "
            "impl. POS 1 and POS 2 both close by a bare `rfl`, so they reduce to "
            "the spec's own right-hand side and test the obligation only up to "
            "defeq. This one fuses both cleanup stages into a single pass over "
            "the REVERSED token and reverses back once, so the frozen shape's "
            "two `.reverse` round-trips never appear: `rfl` does not close it and "
            "the proof must go through `List.getLast?_reverse` plus a case split "
            "on the marker test. Extensionally the same value at every input, so "
            "if the spec could not be reproven for it the spec would be "
            "SPEC-TOO-STRONG for a faithful correct impl."
        ),
    },

    # --- ADMISSIBILITY (PRECOND-TOO-STRONG lane) --------------------------
    {
        "id": "admiss-ground-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF, _ADM_PROOF),
        "rationale": (
            "The third lane: neither positives nor rivals can see an obligation "
            "that is UNSATISFIABLE at the input shape that matters. This case "
            "discharges the frozen predicate by EVALUATION (`decide`) at a "
            "concrete F2P-shaped segment — a quoted token holding an interior "
            "doubled quote AND a trailing continuation marker — as a `have`, "
            "then closes the frozen obligation verbatim. It must verify: if the "
            "modeled behavior and the master clause disagreed at that point, "
            "`decide` would refute the ground instance while every uniqueness "
            "rival still rejected, which is the PRECOND-TOO-STRONG analogue on a "
            "total carrier. The obligation has no precondition hypothesis, so "
            "this ground instance is the honest form of the lane; nothing is "
            "assumed — no new declaration, no new axiom, and the "
            "`theorem correct_segmentValue` statement is byte-identical."
        ),
    },

    # --- UNIQUENESS R1: double un-escape ---------------------------------
    {
        "id": "weak-double-unescape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_COLLAPSE),
        "refinement": (
            "A faithful patch re-adding a second collapse of interior doubled "
            "quotes to single quotes is exactly the pre-patch behavior the issue "
            "reports: a recovered value with a surviving `''` is wrongly turned "
            "into `'`, so a round-tripped value ending in or containing `''` no "
            "longer equals the original — the failing test forbids precisely "
            "this, so the patch would NOT resolve. A verifying rival here would "
            "be a true verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause's doubled-quote-preservation "
            "consequence: `matchToken` captures the doubled quote and the cleanup "
            "pipeline leaves it intact, so the recovered value must retain `''`, "
            "whereas this rival collapses it. Witness at a segment whose recovered "
            "value carries a surviving interior `''`."
        ),
        # Holds of the rival (value collapsed), fails on gold (value preserved).
        "witness": _witness(_W_COLLAPSE),
    },

    # --- UNIQUENESS R2: truncated tail -----------------------------------
    {
        "id": "weak-truncate-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_DROPLAST),
        "refinement": (
            "Drops the final code point of the recovered value — the unfixed / "
            "partially-fixed capture that still loses the last character. The "
            "issue shows this drops the trailing quote so the round-tripped value "
            "differs from the original; the patch would NOT resolve."
        ),
        "rationale": (
            "Rejected by the full-recovery consequence: the recovered value is "
            "the captured token cleaned, with no code point dropped, so on a "
            "two-char token the rival (which drops the last) contradicts the "
            "spec. Witness at a two-char token."
        ),
        # Holds of the rival (last char lost), fails on gold (full value).
        "witness": _witness(_W_DROPLAST),
    },

    # --- UNIQUENESS R3: empty recovery -----------------------------------
    {
        "id": "weak-empty-recovery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_EMPTY),
        "refinement": (
            "Returns the empty value for every matched segment. No faithful "
            "capture patch loses the whole token; every non-trivial value would "
            "round-trip to empty, so the failing test — and the passing "
            "string-value tests — would NOT resolve. (Supporting near-miss; still "
            "carries a real refinement.)"
        ),
        "rationale": (
            "Rejected by the master clause, which forces a non-empty recovered "
            "value for a non-empty captured token. Witness at a single-char "
            "token, where the spec demands a one-char value and the rival returns "
            "empty."
        ),
        # Holds of the rival (empty), fails on gold (one-char value).
        "witness": _witness(_W_EMPTY),
    },

    # --- UNIQUENESS R4: skip whitespace trim -----------------------------
    {
        "id": "weak-skip-ws-trim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_SKIPWS),
        "refinement": (
            "Omits the trailing-whitespace-trim stage of the cleanup pipeline — "
            "a stage the spec pins and the gold patch leaves unchanged. A patch "
            "removing it would leave padding on recovered values, changing the "
            "output on space-carrying fields and regressing the passing "
            "string-value tests; it would NOT resolve the suite."
        ),
        "rationale": (
            "Rejected by the trailing-whitespace-trim consequence: the recovered "
            "value has trailing whitespace removed, so on a token carrying an "
            "interior trailing space the rival (which keeps it) contradicts the "
            "spec. Witness holds a token with a surviving trailing space — the "
            "only witness that exercises this stage."
        ),
        # Holds of the rival (space kept), fails on gold (space trimmed).
        "witness": _witness(_W_SKIPWS),
    },

    # --- UNIQUENESS R5: skip marker trim ---------------------------------
    {
        "id": "weak-skip-marker-trim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_SKIPAMP),
        "refinement": (
            "Omits the single trailing continuation-marker-trim stage — again a "
            "stage the spec pins and the gold patch leaves unchanged. A patch "
            "removing it would retain the marker in recovered values, regressing "
            "the passing continuation-card tests; it would NOT resolve the suite."
        ),
        "rationale": (
            "Rejected by the marker-trim consequence: the recovered value has a "
            "single trailing marker removed, so on a token ending in that marker "
            "the rival (which keeps it) contradicts the spec. Witness holds a "
            "token ending in the marker — the only witness that exercises this "
            "stage."
        ),
        # Holds of the rival (marker kept), fails on gold (marker trimmed).
        "witness": _witness(_W_SKIPAMP),
    },

    # --- UNIQUENESS R6: none/some selection flip -------------------------
    {
        "id": "weak-none-branch-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_NONECASE),
        "refinement": (
            "Signals a matched empty value on a segment that is NOT in the "
            "expected quoted shape, where the caller must instead keep the raw "
            "segment verbatim. A patch that reported a match on a non-quoted "
            "segment would discard the verbatim text, regressing the passing "
            "parse tests; it would NOT resolve the suite."
        ),
        "rationale": (
            "Rejected by the none/some SELECTION consequence: the result is "
            "`none` exactly when the segment is not in the quoted shape, so on a "
            "non-quoted segment the rival (which returns `some []`) contradicts "
            "the spec. Witness at a non-quoted segment — the only witness that "
            "exercises the `none` half of the result."
        ),
        # Holds of the rival (some []), fails on gold (none).
        "witness": _witness(_W_NONECASE),
    },

    # --- UNIQUENESS R7: cleanup stages composed in the wrong order --------
    {
        "id": "weak-swap-trim-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ORDERSWAP),
        "refinement": (
            "Keeps BOTH cleanup stages but composes them in the other order. A "
            "patch that reordered the cleanup would leave the marker on any "
            "recovered value whose captured token carries whitespace after the "
            "marker — the padded-record case the continuation-card tests cover — "
            "so it would regress those passing tests and would NOT resolve the "
            "suite."
        ),
        "rationale": (
            "Rejected by the ORDER the master clause fixes: the spec composes "
            "marker-trim AFTER whitespace-trim, so on a token whose marker is "
            "followed by whitespace the spec demands both be gone while the rival "
            "removes neither. This is the axis R4 and R5 leave open — each of "
            "those only shows a stage is PRESENT, neither pins the sequence. "
            "Witness at a token holding a marker followed by a space."
        ),
        # Holds of the rival (marker kept), fails on gold (both trimmed).
        "witness": _witness(_W_ORDERSWAP),
    },

    # --- UNIQUENESS R8: marker trim applied twice ------------------------
    {
        "id": "weak-double-marker-trim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_TWICEAMP),
        "refinement": (
            "Strips TWO trailing continuation markers where the spec pins the "
            "removal of at most one. A patch that trimmed the marker repeatedly "
            "would eat a marker that is part of the value itself, so a value "
            "whose text legitimately ends in that character would no longer "
            "round-trip; it would NOT resolve the suite."
        ),
        "rationale": (
            "Rejected by the marker-trim clause's MULTIPLICITY: the recovered "
            "value has a SINGLE trailing marker removed, so on a token ending in "
            "two markers the spec demands one survive and the rival drops both. "
            "No other rival varies this axis — R5 only omits the stage. Witness "
            "at a token ending in two markers."
        ),
        # Holds of the rival (both dropped), fails on gold (one survives).
        "witness": _witness(_W_TWICEAMP),
    },

    # --- UNIQUENESS R9: selection flip, `some` half ----------------------
    {
        "id": "weak-always-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ALLNONE),
        "refinement": (
            "Reports NO match for every segment, so the caller would keep every "
            "segment verbatim and no quoted text would ever be recovered. Every "
            "value-carrying test would regress; it would NOT resolve the suite."
        ),
        "rationale": (
            "Rejected by the other direction of the none/some SELECTION "
            "consequence: R6 claims a match where the segment is not in the "
            "expected shape, this one denies a match for a segment that IS, so "
            "between them both directions are pinned rather than just the `none` "
            "half. Witness at a well-shaped single-char-token segment, where the "
            "spec demands `some` and the rival yields `none`."
        ),
        # Holds of the rival (none), fails on gold (some one-char value).
        "witness": _witness(_W_ALLNONE),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# The parse + cleanup pipeline is modeled structurally over the input carrier;
# the proof reasons about no opaque callee via an assumed contract.
AXIOM_TESTS = []
