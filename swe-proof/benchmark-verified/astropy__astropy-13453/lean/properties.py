# properties.py — G-PBT falsification battery for astropy__astropy-13453 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a soundness positive that reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against
# the rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   formattedCells (formats : List (String × String)) (cols : List Column)
#                  : List (List String)
#   A tabular renderer: given a per-name display-format request map and a list of
#   columns (each a name, a pre-existing display format, and a value sequence), it
#   returns one list of rendered cell-strings per column. The SINGLE postcondition
#   `problem_spec_formattedCells` pins the whole result to ONE equation:
#     result = cols.map (fun c => c.values.map (renderCell (effFormat formats c)))
#   which bundles several independent obligations:
#     (S1) STRUCTURE / FRAME: one output list per input column, IN THE SAME ORDER,
#          same length as `cols`; within a column the per-value order and count are
#          preserved (the outer/inner `List.map` shape).
#     (S2) EFFECTIVE FORMAT: each value is rendered under `effFormat formats c` —
#          the by-name requested format when one exists for the column's name
#          (the OVERRIDE branch, the behaviour the writer previously omitted),
#          otherwise the column's OWN pre-existing format (the KEEP branch).
#   `renderCell : Option String → CellValue → String` and `CellValue` are OPAQUE
#   (a real value→string primitive, unchanged by the fix — mapping.md A-reference).
#   There is NO transparent value to compute, so a value-level rejection cannot be
#   `decide`d at a literal; it is CONDITIONED on the carrier instead — the witness
#   assumes only that `renderCell` DISTINGUISHES the two formats it is handed
#   (`renderCell (some "P") v ≠ renderCell none v`), which is exactly the sub-domain
#   where the rival's format choice is observable. A single such hypothesis per
#   witness keeps the assumptions jointly satisfiable (the gate's consistency probe
#   checks this). Purely STRUCTURAL rivals (length/order) need no conditioning:
#   with empty value lists every cell list is `[]`, so `decide` closes the shape
#   disequality with no opaque term in sight.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `_RIVAL_FRAME_MUTATE`: `prior_formats` was
#     Acc(list_pred(prior_formats),1/2) read-only and the rival wrote back into it).
#     Lean is referentially transparent — no aliasing, no fractional permission —
#     so a "store into a read-only input" rival is not expressible. The frame
#     obligation instead lives in clause S1 (the result is pinned to `cols.map …`,
#     so column order/count and per-value order/count are all fixed); it is attacked
#     structurally by `weak-drop-last-column` (count), `weak-reverse-columns` (column
#     order) and `weak-reverse-values` (per-value order). See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. On lean `implementation_formattedCells` is a
#     total Lean `def`; a non-terminating implementation cannot be written at all,
#     so the class is genuinely VACUOUS here (this is the lean disposition, NOT the
#     velvet-partial known-spec-hole one). The nagini sibling carries no divergence
#     case either. See 'assessment'.
#   * AUDIT CORRECTION — ADMISSIBILITY IS NOT N/A, AND IS NOW CARRIED.
#     This block previously dropped nagini's `_ADMISS` on the ground that "the lean
#     obligation has NO precondition hypothesis, so nothing could be
#     PRECOND-TOO-STRONG". That reasoning is the known-bad one: on a TOTAL carrier
#     the analogue of an unsatisfiable precondition is the obligation being
#     UNSATISFIABLE AT A CONCRETE F2P-SHAPED INPUT — a spec that is `∀`-quantified
#     but vacuous/contradictory at the very inputs the real test exercises would
#     still record `verified` for the frozen file while being unusable. A positive
#     that DISCHARGES the obligation at that concrete input BY EVALUATION, as a
#     `have`, before closing the frozen obligation verbatim, tests exactly that.
#     Landed as `admiss-f2p-shaped-input` below and machine-verified (exit 0).
#   * AXIOM_TESTS (nagini's `ax-resolution-sound` / `ax-resolution-containment`).
#     The axiom lane is G-AX's job; this gate ignores them. `renderCell` is the sole
#     opaque callee and carries no constraining axiom, so there is nothing for this
#     spec lane to test there anyway.
#
# CARRIER CORRESPONDENCE vs nagini: nagini modeled the per-column-format RESOLUTION
# as a list-of-tokens function `resolve_column_formats` and attacked the resolution
# at the token level (present-name -> supplied token; absent-name -> prior token),
# with partial-domain rivals keyed off the INDEX (skip-first, proxy-mask-odd). This
# backend models the observable RENDER directly, and the per-column decision the
# frozen impl makes is keyed off the column's NAME/FORMAT rather than its position.
#
# AUDIT CORRECTION (this block previously claimed the opaque carrier "COLLAPSES the
# index-partitioned rivals (skip-first / proxy-mask-odd)" into the two format rivals,
# and dropped both). That claim is FALSE and was measured false: a rival may key its
# per-column decision off POSITION even though the frozen impl does not — by
# matching on the head of `cols` (`| c0 :: rest =>`) or by `cols.mapIdx` — and both
# such rivals are same-spec, are rejected, and carry a witness that ELABORATES
# against the rival and FAILS on the frozen solution AND on both correct positives.
# They are therefore reinstated as `weak-skip-first-column` and
# `weak-proxy-mask-odd-columns`, and they attack a genuinely distinct thing from the
# format rivals: a PARTIAL-DOMAIN impl that renders the correct effective format on
# SOME columns and the wrong one on others, which a rival that is uniformly wrong on
# every column never probes. The `∀ cols` binder is what carries this: the two
# position-keyed rivals disagree with gold at COMPLEMENTARY positions, which was
# measured by cross-building each one's witness against the other's rival (each
# fails, exit 1, while each refutes its own rival, exit 0). NOTE the weaker true
# statement: a one-column witness DOES reach the head-keyed rival (a length-1 input
# is a head column, measured exit 0), so what the pair establishes is that the
# override holds at EVERY position, not that either is unreachable at length 1.
#
# Two further clauses are attacked here that nagini's carrier could not see as
# sharply: the STRUCTURAL frame (column count/order, per-value order) via
# `weak-drop-last-column` / `weak-reverse-columns` / `weak-reverse-values`, and the
# OVERRIDE-vs-PRIOR PRECEDENCE via `weak-prior-format-wins` (a column that carries a
# prior format AND is named in the request — the corner where the two branches of
# `effFormat` disagree, which neither format rival binds). Details per case below.
from pathlib import Path

INSTANCE = "astropy__astropy-13453"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  -- First, fix up the columns' display formats from the requested mapping\n"
    "  -- (the step the writer previously omitted).\n"
    "  let mut updated : Array Column := #[]\n"
    "  for c in cols do\n"
    "    updated := updated.push (applyFormat formats c)\n"
    "  -- Then render each column's values using its (now effective) format.\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in updated do\n"
    "    out := out.push (c.values.map (renderCell c.format))\n"
    "  return out.toList"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-map positive, whose different impl shape needs an (equally cheap, honest)
# reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro formats cols\n"
    "  simp only [problem_spec_formattedCells, implementation_formattedCells, Id.run, effFormat, applyFormat]\n"
    "  simp\n"
    "  apply List.map_congr_left\n"
    "  intro c _\n"
    "  cases h : lookupFormat formats c.name <;> simp [Function.comp, h]"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-fused-loop: structurally DIFFERENT but behaviourally identical. The two
# sequential loops (fix up formats into `updated`, then render `updated`) are FUSED
# into one loop that applies the format and renders each column in a single pass via
# a local `c'`. Output equals the frozen impl's on every input. The theorem STATEMENT
# is byte-identical and the FROZEN proof body still closes (the fused form reduces to
# the same `cols.map …` after the same unfolding). No reproof, no new axiom/lemma/
# sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to the two-loop shape).
_POS_FUSED = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols do\n"
    "    let c' := applyFormat formats c\n"
    "    out := out.push (c'.values.map (renderCell c'.format))\n"
    "  return out.toList",
)

# pos-pure-map: a structurally different CORRECT impl written as a pure double
# `List.map` (no `Id.run do`, no `Array`, no early return), rendering each column
# directly under `effFormat formats c`. Semantics identical on every input. The
# theorem STATEMENT is byte-identical; its proof is reproven honestly with `rfl`
# inside proof-start/proof-end (the impl is now definitionally the spec's RHS) — no
# new axiom/lemma/sorry, just the cheapest tactic for the new shape. If it FAILS =>
# SPEC-TOO-STRONG (the postcondition is bound to the monadic/array impl shape).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_formattedCells\n"
        "    (formats : List (String × String)) (cols : List Column) :\n"
        "    List (List String) :=\n"
        "  cols.map (fun c => c.values.map (renderCell (effFormat formats c)))",
    ),
    _PROOF,
    "  intro formats cols\n"
    "  rfl",
)

# admiss-f2p-shaped-input: the ADMISSIBILITY positive (see the header correction).
# The impl region is the FROZEN one byte-for-byte — this case does not reshape the
# implementation at all. It prepends to the proof a `have f2p` that discharges the
# postcondition AT A CONCRETE F2P-SHAPED INPUT: two columns, both named in the
# request map with the two format strings the real test supplies, each carrying NO
# pre-existing format and two cell values apiece. That `have` is closed BY
# EVALUATION (`simp [...]` then `rfl`), so it certifies the obligation is genuinely
# SATISFIABLE at that concrete input rather than merely `∀`-true by vacuity; the
# frozen obligation is then closed verbatim by the unchanged frozen tactic body. No
# new axiom/lemma/sorry, statement byte-identical. If it FAILS =>
# PRECOND-TOO-STRONG (the obligation cannot be met at an input the exported
# behaviour must handle).
_POS_ADMISS = _swap(
    _BASE,
    _PROOF,
    "  have f2p : ∀ v1 v2 v3 v4 : CellValue,\n"
    '      problem_spec_formattedCells [("C1", "04d"), ("C2", ".2e")]\n'
    '        [{ name := "C1", format := none, values := [v1, v2] },\n'
    '         { name := "C2", format := none, values := [v3, v4] }]\n'
    '        (implementation_formattedCells [("C1", "04d"), ("C2", ".2e")]\n'
    '          [{ name := "C1", format := none, values := [v1, v2] },\n'
    '           { name := "C2", format := none, values := [v3, v4] }]) := by\n'
    "    intro v1 v2 v3 v4\n"
    "    simp [problem_spec_formattedCells, implementation_formattedCells, effFormat,\n"
    "      lookupFormat, applyFormat, Id.run]\n"
    "    rfl\n" + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-prepatch-keep-prior: renders every column with its OWN pre-existing format and
# never consults the requested mapping — exactly the pre-patch writer that omitted
# the format fix-up step. Correct on the KEEP sub-domain (absent name) but WRONG on
# every column whose name IS requested: it keeps the prior format instead of applying
# the override. Attacks clause S2, OVERRIDE branch.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols do\n"
    "    out := out.push (c.values.map (renderCell c.format))\n"
    "  return out.toList",
)

# weak-ignore-prior-format: renders every column under the LOOKED-UP format directly
# (`lookupFormat formats c.name`, which is `none` when the name is absent), dropping
# the fallback to the column's own pre-existing format. Correct on the OVERRIDE
# sub-domain (present name) but WRONG on the KEEP branch: an absent-name column that
# carried a prior format is rendered with `none` instead. Attacks clause S2, KEEP
# branch (the `c.format` fallback binder nagini's index-keyed carrier folded into the
# prior token).
_RIV_IGNORE_PRIOR = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols do\n"
    "    out := out.push (c.values.map (renderCell (lookupFormat formats c.name)))\n"
    "  return out.toList",
)

# weak-drop-last-column: renders every column correctly under its effective format
# but DROPS the final column (off-by-one over the column list), returning a result
# one element short. Element-wise correct on the columns it DOES emit, but violates
# the STRUCTURE clause S1 (one output per input column, same count/order). Attacks
# clause S1 (column count).
_RIV_DROP_LAST = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols.dropLast do\n"
    "    out := out.push (c.values.map (renderCell (effFormat formats c)))\n"
    "  return out.toList",
)

# weak-reverse-values: renders each column under the CORRECT effective format but
# REVERSES the per-value order within each column before emitting. Correct on the
# effective-format decision AND the column order/count, but violates the per-value
# order sub-clause of S1. Attacks clause S1 (within-column value order).
_RIV_REVERSE = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols do\n"
    "    out := out.push ((c.values.map (renderCell (effFormat formats c))).reverse)\n"
    "  return out.toList",
)


# weak-skip-first-column: renders every column correctly under its effective format
# EXCEPT the first, which is rendered under its own prior format (the by-name request
# is ignored for the head column only). Reinstates nagini's `rival-skip-first-column`
# on this carrier — the port had dropped it claiming the carrier collapses
# position-keyed rivals, which is false: matching on the head of `cols` keys off
# position with no index arithmetic. Attacks clause S2 on a PARTIAL sub-domain (the
# override holds for some columns and not others), which the uniformly-wrong format
# rivals never probe.
_RIV_SKIP_FIRST = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) :=\n"
    "  match cols with\n"
    "  | [] => []\n"
    "  | c0 :: rest =>\n"
    "      (c0.values.map (renderCell c0.format))\n"
    "        :: rest.map (fun c => c.values.map (renderCell (effFormat formats c)))",
)

# weak-proxy-mask-odd-columns: honours the by-name override on EVEN column positions
# and MASKS it on odd ones (rendering those under the column's own prior format).
# Reinstates nagini's `rival-proxy-mask-odd-present` via `cols.mapIdx`. A second,
# distinct partial-domain shape: the sub-domain where the override is dropped is
# selected by a position PROXY, so an impl can be correct on the first column (which
# a head-keyed witness probes) and still wrong later.
_RIV_PROXY_MASK = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) :=\n"
    "  cols.mapIdx (fun i c =>\n"
    "    if i % 2 = 0 then c.values.map (renderCell (effFormat formats c))\n"
    "    else c.values.map (renderCell c.format))",
)

# weak-prior-format-wins: inverts the PRECEDENCE of the two `effFormat` branches — a
# column that already carries a display format keeps it, and the by-name request is
# consulted only for a column that carries none. Correct on every column whose prior
# format is absent (which is where BOTH existing format rivals state their
# witnesses), and wrong exactly on the corner where the request and a pre-existing
# format disagree. Attacks clause S2's precedence.
_RIV_PRIOR_WINS = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols do\n"
    "    let f := if c.format.isSome then c.format else effFormat formats c\n"
    "    out := out.push (c.values.map (renderCell f))\n"
    "  return out.toList",
)

# weak-reverse-columns: renders every column correctly under its effective format and
# preserves each column's per-value order, but emits the COLUMNS in reverse order.
# Attacks the column-ORDER sub-clause of S1, which `weak-drop-last-column` (count)
# and `weak-reverse-values` (per-value order) both leave unattacked — a permutation
# preserves the count, so the count probe cannot see it.
_RIV_REVERSE_COLS = _swap(
    _BASE,
    _IMPL,
    "def implementation_formattedCells\n"
    "    (formats : List (String × String)) (cols : List Column) :\n"
    "    List (List String) := Id.run do\n"
    "  let mut out : Array (List String) := #[]\n"
    "  for c in cols do\n"
    "    out := out.push (c.values.map (renderCell (effFormat formats c)))\n"
    "  return out.toList.reverse",
)


# --- witnesses ---------------------------------------------------------------------
# Each witness states `¬ problem_spec_formattedCells formats cols (impl formats cols)`
# at a concrete input, unfolds ONLY the spec, projects both sides of the resulting
# equation down to a single cell string with `congrArg`, and derives the disequality
# from the carrier hypothesis. It ELABORATES against the rival (which produces the
# wrong render there) and FAILS on gold (which satisfies the spec at every input).
# Value-level witnesses assume ONE inequality about `renderCell` — the sub-domain
# where the misrendered format is observable — kept as weak as the refutation needs so
# the assumption is satisfiable.
#
# AUDIT CORRECTION — WHY THE `congrArg` SHAPE, AND NOT THE `simp only` + `injection`
# ONE THIS FILE SHIPPED BEFORE. The seven value-level witnesses previously unfolded
# `implementation_formattedCells` and drove the goal with
#   simp only [List.find?, ..., List.forIn_cons, List.forIn_nil, List.map, Id.run]
#   simp only [pure] at heq; injection heq with h1; injection h1 with h2
#   exact h h2.symm
# and every one of them was recorded `rejected` with rival exit 0 / gold exit 1. The
# rival half was sound, but gold's half was NOT evidence about the spec, and it was
# measured so rather than argued:
#
#   * Gold's error was `Application type mismatch: the argument Eq.symm h2 has type
#     renderCell (some "A") v = renderCell (do let x ← do PUnit.unit ForInStep.yield
#     (#[].push (applyFormat [("C","A")] {...})) ...)[(Array.size ...) - 1 - 0].format
#     v`. The `simp only` set omits `applyFormat`, so on gold's two-pass `Array` form
#     the pushed element's `.format` projection never reduces: the do-block is still
#     sitting there UNREDUCED inside the type. That is an unfolding/unification
#     failure, not a satisfied spec — the same defect class the gate screens for as
#     `_STUCK_UNIFICATION` (`Application type mismatch` + an unreduced loop term),
#     whose pattern is pinned to velvet's `forIn Lean.Loop.mk` and so does not fire on
#     lean's `Id.run` do-block.
#   * The type-revealing probe (attack B′) confirms it from both sides. Replacing the
#     final step with `exact (h2 : Nat)` makes Lean print the hypothesis's real type:
#     against the RIVAL it is the concrete refutation `renderCell none v = renderCell
#     (some "A") v`, against GOLD it is the unreduced do-block term above — NOT `True`,
#     i.e. `simp` did not prove the equation for gold, it merely got stuck on it.
#   * And gold's exit code carried no information about the CLAIM. The same tactic
#     body restated at a genuine AGREEMENT point (a column the rival and gold render
#     identically, where `¬ problem_spec …` is FALSE) still fails on gold with an
#     unreduced-term error; the flipped claim (`¬` dropped) fails on gold and on the
#     rival with the byte-identical `introN failed`, because the tactic body opens
#     with `intro heq`.
#
# So the discrimination rested entirely on the rival side. The repair does not weaken
# any claim — the statements are unchanged at the same concrete inputs — it changes
# only HOW the refutation is extracted, from `simp`-driven reduction of the impl to a
# `congrArg` projection of the spec's own equation onto one cell. That makes gold's
# failure track the claim, which is checkable and was checked: for every one of the
# seven, the OPPOSITE claim (`problem_spec …` with the `¬` dropped, closed by `rfl`)
# now ELABORATES against gold (exit 0) while the witness itself fails (exit 1) — so
# gold's exit code is a verdict on the claim rather than on a tactic. Each repaired
# witness was additionally built against the two positives and against four further
# verifying correct reshapes (foldr / two-pass / structural recursion /
# reverse-reverse): exit 1 on all of them, and exit 1 on its own rival when restated
# at an agreement point. `weak-drop-last-column` is left as it was: its gold-side
# signature is already a plain kernel evaluation (`Tactic decide proved that the
# proposition ¬(…) is false`), which is a semantic refutation and needs no repair.
# That same evaluation is what shows gold IS kernel-reducible here, which is why the
# projection shape closes at all.

# OVERRIDE branch: name "C" IS requested ("A"); column carries prior format `none`.
# gold renders under `some "A"`; the prepatch rival renders under `none`.
_WIT_PREPATCH = (
    'example (v : CellValue) (h : renderCell (some "A") v ≠ renderCell none v) :\n'
    '    ¬ problem_spec_formattedCells [("C", "A")]\n'
    '        [{ name := "C", format := none, values := [v] }]\n'
    '      (implementation_formattedCells [("C", "A")]\n'
    '        [{ name := "C", format := none, values := [v] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    '  have h2 : renderCell none v = renderCell (some "A") v :=\n'
    '    congrArg (fun r => (r.headD []).headD "") heq\n'
    "  exact h h2.symm"
)

# KEEP branch: empty request map; column "C" carries prior format `some "P"`.
# gold renders under `some "P"` (the fallback); the ignore-prior rival renders under
# `lookupFormat [] "C" = none`.
_WIT_IGNORE_PRIOR = (
    'example (v : CellValue) (h : renderCell (some "P") v ≠ renderCell none v) :\n'
    "    ¬ problem_spec_formattedCells []\n"
    '        [{ name := "C", format := some "P", values := [v] }]\n'
    "      (implementation_formattedCells []\n"
    '        [{ name := "C", format := some "P", values := [v] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    '  have h2 : renderCell none v = renderCell (some "P") v :=\n'
    '    congrArg (fun r => (r.headD []).headD "") heq\n'
    "  exact h h2.symm"
)

# STRUCTURE (column count): two columns with EMPTY value lists (every cell list is
# `[]`, so no opaque term appears). gold result `[[], []]`; the drop-last rival emits
# `[[]]`. `decide` closes the length/shape disequality.
_WIT_DROP_LAST = (
    "example :\n"
    "    ¬ problem_spec_formattedCells []\n"
    '        [{ name := "A", format := none, values := [] },\n'
    '         { name := "B", format := none, values := [] }]\n'
    "      (implementation_formattedCells []\n"
    '        [{ name := "A", format := none, values := [] },\n'
    '         { name := "B", format := none, values := [] }]) := by\n'
    "  unfold problem_spec_formattedCells implementation_formattedCells\n"
    "  decide"
)

# STRUCTURE (within-column value order): one column, two values whose renders differ.
# gold emits `[r1, r2]`; the reverse rival emits `[r2, r1]`. Conditioned on the two
# renders being distinct (else the reversal is unobservable).
_WIT_REVERSE = (
    "example (v1 v2 : CellValue) (h : renderCell none v1 ≠ renderCell none v2) :\n"
    "    ¬ problem_spec_formattedCells []\n"
    '        [{ name := "C", format := none, values := [v1, v2] }]\n'
    "      (implementation_formattedCells []\n"
    '        [{ name := "C", format := none, values := [v1, v2] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    "  have h2 : renderCell none v2 = renderCell none v1 :=\n"
    '    congrArg (fun r => (r.headD []).headD "") heq\n'
    "  exact h h2.symm"
)


# PARTIAL-DOMAIN (head column): TWO columns, both names requested, both carrying
# prior format `none`. gold renders column 0 under `some "A"`; the skip-first rival
# renders it under `none`. The second column is rendered correctly by BOTH, so the
# refutation is pinned to the head position specifically.
_WIT_SKIP_FIRST = (
    'example (v0 v1 : CellValue) (h : renderCell (some "A") v0 ≠ renderCell none v0) :\n'
    '    ¬ problem_spec_formattedCells [("C0", "A"), ("C1", "B")]\n'
    '        [{ name := "C0", format := none, values := [v0] },\n'
    '         { name := "C1", format := none, values := [v1] }]\n'
    '      (implementation_formattedCells [("C0", "A"), ("C1", "B")]\n'
    '        [{ name := "C0", format := none, values := [v0] },\n'
    '         { name := "C1", format := none, values := [v1] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    '  have h2 : renderCell none v0 = renderCell (some "A") v0 :=\n'
    '    congrArg (fun r => (r.headD []).headD "") heq\n'
    "  exact h h2.symm"
)

# PARTIAL-DOMAIN (odd position): same two requested columns. gold renders column 1
# under `some "B"`; the proxy-mask rival masks the override there and renders it under
# `none`. Refutation is pinned at position 1, so this probes the sub-domain the
# head-keyed witness above cannot reach.
_WIT_PROXY_MASK = (
    'example (v0 v1 : CellValue) (h : renderCell (some "B") v1 ≠ renderCell none v1) :\n'
    '    ¬ problem_spec_formattedCells [("C0", "A"), ("C1", "B")]\n'
    '        [{ name := "C0", format := none, values := [v0] },\n'
    '         { name := "C1", format := none, values := [v1] }]\n'
    '      (implementation_formattedCells [("C0", "A"), ("C1", "B")]\n'
    '        [{ name := "C0", format := none, values := [v0] },\n'
    '         { name := "C1", format := none, values := [v1] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    '  have h2 : renderCell none v1 = renderCell (some "B") v1 :=\n'
    '    congrArg (fun r => (r.getD 1 []).headD "") heq\n'
    "  exact h h2.symm"
)

# PRECEDENCE: name "C" IS requested ("A") AND the column already carries `some "P"`.
# gold renders under the REQUEST `some "A"`; the prior-wins rival renders under the
# pre-existing `some "P"`. Conditioned on `renderCell` distinguishing the two
# FORMATS — note both are `some`, so this binds a carrier point neither existing
# format witness reaches (they each compare a `some` against `none`).
_WIT_PRIOR_WINS = (
    'example (v : CellValue) (h : renderCell (some "A") v ≠ renderCell (some "P") v) :\n'
    '    ¬ problem_spec_formattedCells [("C", "A")]\n'
    '        [{ name := "C", format := some "P", values := [v] }]\n'
    '      (implementation_formattedCells [("C", "A")]\n'
    '        [{ name := "C", format := some "P", values := [v] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    '  have h2 : renderCell (some "P") v = renderCell (some "A") v :=\n'
    '    congrArg (fun r => (r.headD []).headD "") heq\n'
    "  exact h h2.symm"
)

# STRUCTURE (column order): two one-value columns whose renders differ. gold emits
# `[[r1], [r2]]`; the reverse-columns rival emits `[[r2], [r1]]`. Conditioned on the
# two renders being distinct (else the permutation is unobservable).
_WIT_REVERSE_COLS = (
    "example (v1 v2 : CellValue) (h : renderCell none v1 ≠ renderCell none v2) :\n"
    "    ¬ problem_spec_formattedCells []\n"
    '        [{ name := "A", format := none, values := [v1] },\n'
    '         { name := "B", format := none, values := [v2] }]\n'
    "      (implementation_formattedCells []\n"
    '        [{ name := "A", format := none, values := [v1] },\n'
    '         { name := "B", format := none, values := [v2] }]) := by\n'
    "  unfold problem_spec_formattedCells\n"
    "  intro heq\n"
    "  have h2 : renderCell none v2 = renderCell none v1 :=\n"
    '    congrArg (fun r => (r.headD []).headD "") heq\n'
    "  exact h h2.symm"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-fused-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUSED,
        "rationale": (
            "structurally-different but CORRECT impl: the two sequential passes (fix up "
            "formats, then render) are FUSED into one loop applying the format and rendering "
            "each column via a local, so the output equals the frozen impl's on every input. "
            "The theorem statement is byte-identical and the FROZEN proof body still closes "
            "(the fused form reduces to the same `cols.map …` after the same unfolding) — a "
            "faithful restructure with no reproof and no new axiom/lemma/sorry. If it FAILS "
            "=> SPEC-TOO-STRONG (postcondition over-fit to the two-loop impl shape)."
        ),
    },
    {
        "id": "pos-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure double `List.map` (no "
            "`Id.run do`, no `Array`, no early return), rendering each column directly under "
            "its effective format. Semantics identical on every input. The theorem STATEMENT "
            "is byte-identical; its proof is reproven honestly with `rfl` (the impl is now "
            "definitionally the spec's RHS) — no new axiom/lemma/sorry, just the cheapest "
            "tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition is "
            "bound to the monadic/array impl shape rather than the behaviour)."
        ),
    },

    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADMISSIBILITY on a total carrier. The frozen obligation is `∀ formats cols, "
            "problem_spec … (impl …)` with no precondition hypothesis, and the port had "
            "dropped this lane on the ground that 'nothing could be PRECOND-TOO-STRONG'. "
            "That reason is wrong: the analogue here is the obligation being UNSATISFIABLE "
            "AT A CONCRETE INPUT of the shape the exported behaviour must actually handle. "
            "This case keeps the impl region FROZEN byte-for-byte and prepends a `have "
            "f2p` that discharges the postcondition, BY EVALUATION, at two columns both "
            "named in the request map (with the two format strings the real test supplies) "
            "and both carrying no pre-existing format — so the effective format on each is "
            "the requested one and every cell reduces to a concrete `renderCell (some …) v` "
            "term. Closing it needs `rfl` past the `Id.run` residue, i.e. the do-loop "
            "really is evaluated at that input rather than reasoned about abstractly. The "
            "frozen obligation is then closed verbatim by the unchanged frozen tactic "
            "body, so the case adds a check and weakens nothing. If it FAILS => "
            "PRECOND-TOO-STRONG (the spec cannot be met at an in-domain input)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch-keep-prior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "renders every column with its OWN pre-existing format and never consults the "
            "requested mapping — this IS the pre-patch behaviour (the writer omitted the "
            "format fix-up step). Its faithful real patch is the UNCHANGED writer, under which "
            "the F2P test_write_table_formatted_columns renders the requested column with its "
            "default format (e.g. the integer column as 1/2 rather than the requested "
            "zero-padded 0001/0002, and the float column unformatted rather than in the "
            "requested exponential form): the exact-output assertion FAILS. It would NOT "
            "resolve — this is precisely the bug the patch fixes (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause S2 (OVERRIDE branch). For a column whose name IS requested "
            "the spec renders under the requested format `effFormat = some f`, but the rival "
            "renders under the column's prior format. Witness probes a present-name column "
            "carrying a DIFFERENT prior format, conditioned on `renderCell` distinguishing "
            "the requested format from the prior — the sub-domain where the override is "
            "observable. If it VERIFIES => SPEC-TOO-WEAK (the override is unpinned)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "weak-ignore-prior-format",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_PRIOR,
        "refinement": (
            "renders every column under the LOOKED-UP requested format directly, dropping the "
            "fallback to the column's own pre-existing format when no format is requested for "
            "its name. Its faithful real patch is a fix-up that OVERWRITES every column's "
            "format from the map — clobbering the display format of columns absent from the "
            "request to the empty/default. A column that carried its own format but was not "
            "named in `formats={...}` would render with the wrong (dropped) format. "
            "AUDIT-MEASURED SCOPE OF THE BREAK, so the claim is not overstated: this rival "
            "AGREES with the frozen spec at the F2P-shaped input (all requested columns carry "
            "no pre-existing format, so `lookupFormat` and `effFormat` coincide there — "
            "machine-checked, the frozen postcondition is satisfied by this rival at that "
            "concrete input, exit 0), and it agrees at every listed P2P input too, since none "
            "of the 9 exercises a per-column display format. So it would NOT be caught by THIS "
            "instance's own test set; it is a break of the exported KEEP behaviour on the "
            "sub-domain of a column that carries its own format and is not named in the "
            "request, which the spec's clause S2 fallback pins and any table carrying a "
            "pre-set per-column format would expose. Rejected on the SPEC, not on the F2P."
        ),
        "rationale": (
            "REJECTED by clause S2 (KEEP branch). For a column whose name is ABSENT from the "
            "request the spec falls back to the column's own `c.format`, but the rival renders "
            "under `none`. Witness probes an absent-name column carrying a prior format, "
            "conditioned on `renderCell` distinguishing that prior format from `none` — the "
            "sub-domain where the dropped fallback is observable. This varies the "
            "`Column.format` binder (a present prior format), which the prepatch witness holds "
            "at `none`. If it VERIFIES => SPEC-TOO-WEAK (the keep fallback is unpinned)."
        ),
        "witness": _WIT_IGNORE_PRIOR,
    },
    {
        "id": "weak-drop-last-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_LAST,
        "refinement": (
            "renders every emitted column correctly but DROPS the final column (an off-by-one "
            "over the column list), returning one output list too few. Its faithful real patch "
            "is a writer that iterates all but the last column; the rendered table would be "
            "missing its last column entirely, so the F2P/P2P exact-output assertions FAIL. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause S1 (STRUCTURE — one output per input column, same count). "
            "Witness uses two columns with empty value lists so the shape disequality (`[[],"
            " []]` vs `[[]]`) is decidable with no opaque term — a purely structural probe "
            "that needs no carrier conditioning. If it VERIFIES => SPEC-TOO-WEAK (the column "
            "count/frame is unpinned)."
        ),
        "witness": _WIT_DROP_LAST,
    },
    {
        "id": "weak-reverse-values",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "renders each column under the CORRECT effective format but REVERSES the per-value "
            "(per-row) order within each column. Its faithful real patch is a writer that "
            "emits each column's cells in reversed row order; the rendered table would show "
            "the rows upside-down, so the F2P/P2P exact-output assertions FAIL. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause S1 (STRUCTURE — within-column value order/count). The spec "
            "pins each column's cells to `c.values.map …` in order, but the rival reverses "
            "them. Witness uses one column with two values, conditioned on the two renders "
            "being distinct (else the reversal is unobservable) — a distinct probe point from "
            "the format rivals (varies the number/order of the `values` binder). If it "
            "VERIFIES => SPEC-TOO-WEAK (the per-value order is unpinned)."
        ),
        "witness": _WIT_REVERSE,
    },
    {
        "id": "weak-skip-first-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP_FIRST,
        "refinement": (
            "PARTIAL-DOMAIN (head column): resolves the requested format correctly for every "
            "column except the first, which keeps its own pre-existing format. Its faithful "
            "real patch is a fix-up that iterates the column list from the SECOND entry "
            "onward, so the leading column's requested format is never applied. Under it the "
            "F2P test_write_table_formatted_columns — whose FIRST column carries a requested "
            "zero-padded integer format and must render 0001/0002 rather than 1/2 — produces "
            "the wrong cell text and the exact-output assertion FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause S2 (OVERRIDE branch) on the HEAD sub-domain. Reinstates "
            "nagini's `rival-skip-first-column`, which this port had dropped claiming the "
            "carrier collapses position-keyed rivals; it does not — matching on `c0 :: rest` "
            "keys off position with no index. Distinct from the format rivals because it is "
            "CORRECT on every non-head column: it is a PARTIAL-DOMAIN impl, wrong only at "
            "one position, where the format rivals are wrong uniformly. Its witness refutes "
            "at column 0 while column 1 is rendered identically by rival and gold, so the "
            "refutation is pinned to the head position. AUDIT CORRECTION: this rationale "
            "previously claimed the rival 'survives any witness stated at a single-column "
            "input'. That is FALSE and was measured false — a one-column input IS a head "
            "column, so `weak-prepatch-keep-prior`'s single-column witness ELABORATES "
            "against this rival (exit 0). What actually distinguishes it is the converse, "
            "which was measured: `weak-proxy-mask-odd-columns`'s position-1 witness FAILS "
            "against this rival (exit 1) and this rival's head witness FAILS against that "
            "one (exit 1), so the two pin complementary positional sub-domains and neither "
            "subsumes the other. If it VERIFIES => SPEC-TOO-WEAK (the override is unpinned "
            "on a positional sub-domain)."
        ),
        "witness": _WIT_SKIP_FIRST,
    },
    {
        "id": "weak-proxy-mask-odd-columns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PROXY_MASK,
        "refinement": (
            "PARTIAL-DOMAIN (position proxy): honours the requested format on even-positioned "
            "columns and masks it on odd-positioned ones, which then keep their pre-existing "
            "format. Its faithful real patch is a fix-up that conditions the assignment on a "
            "column-position proxy (overriding only every other column). Under it a requested "
            "column sitting at an odd position renders with its default rather than requested "
            "format — the F2P/P2P exact-output assertions FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause S2 (OVERRIDE branch) on the ODD-position sub-domain. "
            "Reinstates nagini's `rival-proxy-mask-odd-present`, dropped by this port on the "
            "same false carrier-collapse claim; `cols.mapIdx` expresses it directly. A second "
            "and genuinely different partial-domain shape from `weak-skip-first-column`: this "
            "rival is CORRECT on the head column, so the head-keyed witness above does not "
            "refute it, and its witness must state the refutation at position 1 instead. "
            "Together the two pin that the override holds at EVERY position, not merely at "
            "one. If it VERIFIES => SPEC-TOO-WEAK (the override is maskable on a sub-domain)."
        ),
        "witness": _WIT_PROXY_MASK,
    },
    {
        "id": "weak-prior-format-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PRIOR_WINS,
        "refinement": (
            "inverts the PRECEDENCE of the two effective-format branches: a column that "
            "already carries a display format keeps it, and the by-name request is consulted "
            "only for a column carrying none. Its faithful real patch is a fix-up guarded on "
            "the column's format being unset, so a requested format never displaces a format "
            "the column already had. AUDIT CORRECTION — this refinement previously claimed the "
            "F2P exact-output assertion FAILS under it. That is FALSE and was measured false: "
            "the F2P-shaped input's columns carry NO pre-existing display format, so the guard "
            "`c.format.isSome` is false on every one of them and the rival takes the request "
            "branch exactly as the frozen impl does — machine-checked, this rival SATISFIES the "
            "frozen postcondition at that concrete input (exit 0). It also agrees at all 9 "
            "listed P2P inputs, none of which sets a per-column format. So this rival would "
            "PASS this instance's own test set; it is caught by the SPEC and not by the tests, "
            "which is exactly what a uniqueness rival is for — it breaks the exported "
            "precedence on the sub-domain where a request and a pre-existing format both exist "
            "and disagree (a table whose columns were given formats before writing)."
        ),
        "rationale": (
            "REJECTED by clause S2 (PRECEDENCE). `effFormat` consults the by-name request "
            "FIRST and falls back to `c.format` only when no request exists; the rival "
            "reverses that order. Both existing format rivals state their witnesses at a "
            "column whose prior format and lookup result differ in PRESENCE (a `some` against "
            "a `none`), and this rival agrees with gold at every such point — it is wrong only "
            "where a request and a pre-existing format BOTH exist and disagree. The witness "
            "therefore binds `Column.format := some \"P\"` together with a request for the "
            "same name and conditions on `renderCell` distinguishing the two `some` formats, a "
            "carrier point no other witness in this battery reaches. If it VERIFIES => "
            "SPEC-TOO-WEAK (the branch precedence is unpinned)."
        ),
        "witness": _WIT_PRIOR_WINS,
    },
    {
        "id": "weak-reverse-columns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE_COLS,
        "refinement": (
            "renders every column under the CORRECT effective format and preserves each "
            "column's per-value order, but emits the COLUMNS in reverse order. Its faithful "
            "real patch is a writer that walks the column list backwards; the rendered table "
            "would show its columns right-to-left, so the F2P/P2P exact-output assertions "
            "FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause S1 (STRUCTURE — column ORDER). The spec pins the result to "
            "`cols.map …`, fixing the column sequence, but the rival permutes it. Distinct "
            "from `weak-drop-last-column`, which probes column COUNT and cannot see a "
            "permutation (the count is preserved), and from `weak-reverse-values`, which "
            "reverses WITHIN a column while keeping column order. Witness uses two "
            "single-value columns whose renders differ, so the permutation is observable. If "
            "it VERIFIES => SPEC-TOO-WEAK (the column order is unpinned)."
        ),
        "witness": _WIT_REVERSE_COLS,
    },
]


# No @ContractOnly axioms are consumed by this spec: `renderCell` is opaque with no
# constraining property, and the format-resolution decision (`effFormat` / `lookupFormat`
# / `applyFormat`) is modeled DEEPLY over transparent carriers. The axiom lane is
# therefore empty here and belongs to G-AX regardless.
AXIOM_TESTS = []
