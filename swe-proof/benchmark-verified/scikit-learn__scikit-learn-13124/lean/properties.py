# properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13124 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   classOrders (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
#               -> List (List Nat)
#   Produces the per-class ORDER in which each class's own local index range
#   (spanning `max(count, nFolds)` positions) is laid out. The single
#   postcondition pins the result to an EXACT equality with a total function of
#   the inputs, split by the shuffle flag:
#     (OFF) shuffle = false -> each class keeps its natural ascending order,
#           `counts.map (fun c => List.range (max c nFolds))`.
#     (ON)  shuffle = true  -> the orders threaded from a SINGLE generator seeded
#           by `seed`, consumed once per class IN CLASS ORDER, the advanced
#           generator carried forward from each class to the next
#           (`perClassShuffleOrders nFolds counts (seedState seed)`). This is the
#           LOAD-BEARING clause: class k draws from the k-fold-advanced generator,
#           NOT from a generator re-initialised per class.
#
# CARRIER NOTE. The generator is taken OPAQUELY through `seedState : Nat -> RngState`
# and `shuffleN : RngState -> Nat -> (List Nat × RngState)`; the spec asserts NO
# property of either. What is pinned is purely the THREADING discipline. Because the
# ON-branch value lives behind these opaque callees, no literal input decides the
# per-class order, so the ON-branch rivals CONDITION on the carrier: each witness
# assumes only that the generator's next draw differs from the draw the rival
# substitutes (`shuffleN <advanced-state> m ≠ shuffleN <other-state> m`) — exactly
# the sub-domain where the rival is wrong, and a statement stronger than any single
# literal could make. The OFF branch and the length are fully transparent and are
# attacked with plain `decide` witnesses.
#
# LANES THAT DO NOT PORT (see 'assessment'):
#   * FRAME / PERMISSION-MUTATION (nagini's fractional-permission class). Lean is
#     referentially transparent — no aliasing, no permissions — so a
#     "write-back into a read-only input" rival is not expressible; the lane is
#     VACUOUS here. The nagini sibling itself records this class N/A for this
#     instance (both inputs pass-by-value ints).
#   * DIVERGENCE / NON-TERMINATION. On lean `implementation_classOrders` is a total
#     Lean `def`; a diverging implementation cannot be written at all, so the class
#     is genuinely VACUOUS (not a known spec hole — that disposition is velvet-only).
#   (NOTE: the ADMISSIBILITY lane is NOT among these. An earlier pass recorded it
#   N/A on the grounds that the lean obligation carries no precondition
#   hypothesis, so nothing could be PRECOND-TOO-STRONG. That reasoning is wrong:
#   the analogue on a TOTAL carrier is the obligation being unsatisfiable at
#   exactly an F2P-shaped input, which a positive that discharges the obligation
#   at that concrete input — before closing the frozen obligation verbatim —
#   tests directly. Landed as `admiss-f2p-ground-instance` below.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job (here G-CONF, as no `_prop` axiom is
#     consumed); this gate ignores them.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13124"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). ------------------------------------------------------------

# The ON-branch threading block, verbatim (the load-bearing region every ON rival
# reshapes).
_ON = (
    "  -- Obtain ONE generator from the seed and keep it as we go.\n"
    "  let mut st : RngState := seedState seed\n"
    "  let mut orders : List (List Nat) := []\n"
    "  for c in counts do\n"
    "    -- Shuffle this class's index range with the current generator, then carry\n"
    "    -- the advanced generator forward to the next class.\n"
    "    let res := shuffleN st (max c nFolds)\n"
    "    orders := orders ++ [res.1]\n"
    "    st := res.2\n"
    "  return orders"
)
assert _BASE.count(_ON) == 1, "ON threading anchor drifted"

# The OFF-branch, verbatim.
_OFF = (
    "  if !shuffle then\n"
    "    return counts.map (fun c => List.range (max c nFolds))"
)
assert _BASE.count(_OFF) == 1, "OFF anchor drifted"

# The whole impl region + proof region (for the reproven positive control).
_IMPL = _BASE[_BASE.index("-- impl-start"):
              _BASE.index("-- impl-end") + len("-- impl-end")]
assert _BASE.count(_IMPL) == 1, "impl region anchor drifted"
_PROOF = _BASE[_BASE.index("-- proof-start"):
               _BASE.index("-- proof-end") + len("-- proof-end")]
assert _BASE.count(_PROOF) == 1, "proof region anchor drifted"

# The frozen `correct_classOrders` proof's opening `intro`, verbatim: the insertion
# point for a `have` that runs BEFORE the frozen script, inside the proof region
# and after the byte-identical theorem statement.
_INTRO = "  intro seed shuffle nFolds counts\n"
assert _BASE.count(_INTRO) == 1, "proof intro anchor drifted"


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness.
# ---------------------------------------------------------------------------

# weak-constant-state (THE PRE-PATCH bug, central discriminator): re-initialise the
# generator from the raw seed for every class — never thread it forward — so every
# class draws from `seedState seed`.
_R_CONST = (
    "  let mut orders : List (List Nat) := []\n"
    "  for c in counts do\n"
    "    let res := shuffleN (seedState seed) (max c nFolds)\n"
    "    orders := orders ++ [res.1]\n"
    "  return orders"
)

# weak-double-advance: thread the generator but advance it an EXTRA draw per class,
# so class k+1 draws from a state two draws (not one) beyond class k's.
_R_DOUBLE = (
    "  let mut st : RngState := seedState seed\n"
    "  let mut orders : List (List Nat) := []\n"
    "  for c in counts do\n"
    "    let res := shuffleN st (max c nFolds)\n"
    "    orders := orders ++ [res.1]\n"
    "    st := (shuffleN res.2 (max c nFolds)).2\n"
    "  return orders"
)

# weak-start-advanced: burn one throw-away draw BEFORE class 0, so every class is
# shifted by one draw relative to the seed's initial state.
_R_STARTADV = (
    "  let mut st : RngState := (shuffleN (seedState seed) nFolds).2\n"
    "  let mut orders : List (List Nat) := []\n"
    "  for c in counts do\n"
    "    let res := shuffleN st (max c nFolds)\n"
    "    orders := orders ++ [res.1]\n"
    "    st := res.2\n"
    "  return orders"
)

# weak-drop-last-class: correct threaded orders, but stop one class short (loop over
# `counts.dropLast`), so the last class is dropped — a strict prefix of the result.
_R_DROPLAST = (
    "  let mut st : RngState := seedState seed\n"
    "  let mut orders : List (List Nat) := []\n"
    "  for c in counts.dropLast do\n"
    "    let res := shuffleN st (max c nFolds)\n"
    "    orders := orders ++ [res.1]\n"
    "    st := res.2\n"
    "  return orders"
)

# weak-off-reverse: corrupt the shuffle=OFF branch — return each class's range
# REVERSED instead of in natural ascending order.
_R_OFFREV = (
    "  if !shuffle then\n"
    "    return counts.map (fun c => (List.range (max c nFolds)).reverse)"
)

# weak-off-no-clamp (AUDIT-ADDED): drop the `max c nFolds` CLAMP on the OFF
# branch — lay out only `c` positions per class instead of `max c nFolds`. The
# clamp is a distinct sub-clause of the spec that every pre-audit rival left
# intact (each keeps `max c nFolds` verbatim and attacks the order or the
# threading instead), so the width of each class's index range was pinned by the
# spec but never falsified by the battery.
_R_OFFNOCLAMP = (
    "  if !shuffle then\n"
    "    return counts.map (fun c => List.range c)"
)

# weak-on-no-clamp (AUDIT-ADDED): the same clamp omission on the LOAD-BEARING ON
# branch — each class consumes the generator for `c` positions rather than
# `max c nFolds`, so both the order and the state handed to the next class are
# drawn at the wrong width.
_R_ONNOCLAMP = (
    "  -- Obtain ONE generator from the seed and keep it as we go.\n"
    "  let mut st : RngState := seedState seed\n"
    "  let mut orders : List (List Nat) := []\n"
    "  for c in counts do\n"
    "    -- Shuffle this class's index range with the current generator, then carry\n"
    "    -- the advanced generator forward to the next class.\n"
    "    let res := shuffleN st c\n"
    "    orders := orders ++ [res.1]\n"
    "    st := res.2\n"
    "  return orders"
)


# --- ON-branch reduction recipe (shared by every ON-branch witness). Unfolds the
# spec + impl, reduces the `Id.run do`/`forIn` loop to a plain `pure (…)` list, and
# collapses the front-recursive `perClassShuffleOrders` fold, leaving a list equality
# whose element positions can be injected. ---------------------------------------
_ON_SIMP = (
    "  simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte,\n"
    "    List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, pure_bind,\n"
    "    List.nil_append, perClassShuffleOrders, List.cons_append]\n"
)


SPEC_TESTS = [

    # ================================================= soundness (positive control)
    # pos-direct-restatement: a structurally DIFFERENT but CORRECT impl that returns
    # the spec's right-hand side directly (a pure functional `if`, no `Id.run do`
    # loop). This is the honest cheapest impl — it materialises the grounded spec
    # fold (`perClassShuffleOrders`), which IS the work — standing in for the nagini
    # ungrounded-oracle slot (there is no wrong echo to build: the fold is the spec's
    # own transparent structure over seedState/shuffleN). The frozen `theorem
    # correct_classOrders` STATEMENT is kept byte-identical; only the proof body is
    # reproven (`cases shuffle <;> rfl` closes for this shape). If it FAILS =>
    # SPEC-TOO-STRONG.
    {
        "id": "pos-direct-restatement",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "-- impl-start\n"
                "def implementation_classOrders\n"
                "    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat) :\n"
                "    List (List Nat) :=\n"
                "  if shuffle then\n"
                "    perClassShuffleOrders nFolds counts (seedState seed)\n"
                "  else\n"
                "    counts.map (fun c => List.range (max c nFolds))\n"
                "-- impl-end",
            ),
            _PROOF,
            "-- proof-start\n"
            "theorem correct_classOrders :\n"
            "    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat),\n"
            "      problem_spec_classOrders seed shuffle nFolds counts\n"
            "        (implementation_classOrders seed shuffle nFolds counts) := by\n"
            "  intro seed shuffle nFolds counts\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            "  cases shuffle <;> rfl\n"
            "\n"
            "theorem spec_classOrders_deterministic :\n"
            "    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)\n"
            "      (r : List (List Nat)),\n"
            "      problem_spec_classOrders seed shuffle nFolds counts r →\n"
            "        r = implementation_classOrders seed shuffle nFolds counts := by\n"
            "  intro seed shuffle nFolds counts r h\n"
            "  have h2 := correct_classOrders seed shuffle nFolds counts\n"
            "  unfold problem_spec_classOrders at h h2\n"
            "  rw [h, h2]\n"
            "-- proof-end",
        ),
        "rationale": (
            "a structurally-different but CORRECT impl (a pure functional `if` "
            "returning the spec's total function directly, no `Id.run do` loop) MUST "
            "verify: it is extensionally the gold threaded-generator behavior on every "
            "input. The frozen `theorem correct_classOrders` statement is kept byte-"
            "identical and reproven by `cases shuffle <;> rfl`; the determinism lemma "
            "is carried over. This defends BOTH clauses (the ON `perClassShuffleOrders` "
            "arm and the OFF `List.range` arm). If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # pos-rename-locals: a second CORRECT positive — the imperative gold shape with
    # every local renamed (st/orders/res -> gen/acc/draw). The threading is identical,
    # so the frozen proof body (tuned to the loop's syntactic form) still closes
    # verbatim. A low-risk soundness control that keeps the `Id.run do` loop. If it
    # FAILS => SPEC-TOO-STRONG.
    {
        "id": "pos-rename-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ON,
            "  -- Obtain ONE generator from the seed and keep it as we go.\n"
            "  let mut gen : RngState := seedState seed\n"
            "  let mut acc : List (List Nat) := []\n"
            "  for c in counts do\n"
            "    -- Shuffle this class's index range with the current generator, then carry\n"
            "    -- the advanced generator forward to the next class.\n"
            "    let draw := shuffleN gen (max c nFolds)\n"
            "    acc := acc ++ [draw.1]\n"
            "    gen := draw.2\n"
            "  return acc",
        ),
        "rationale": (
            "a correct impl with renamed locals (st/orders/res -> gen/acc/draw) keeps "
            "the gold `Id.run do` threading loop unchanged in meaning, so the frozen "
            "`correct_classOrders` proof closes verbatim. Defends the ON "
            "`perClassShuffleOrders` threading clause. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # ==================================================== admissibility (AUDIT-ADDED)
    # admiss-f2p-ground-instance: the obligation is SATISFIABLE at exactly the
    # F2P-shaped input, established by EVALUATION rather than in the abstract.
    #
    # A previous pass recorded this whole lane N/A because the frozen obligation
    # has no precondition hypothesis. That is the reason this lane may NOT be
    # dropped for: on a total carrier the PRECOND-TOO-STRONG analogue is the
    # obligation being unsatisfiable at a concrete, real-shaped input, and the
    # honest test is a positive that discharges it THERE, by evaluation, as a
    # `have`, before closing the frozen obligation verbatim.
    #
    # The input is the F2P configuration: two equal-sized classes over 5 folds
    # under shuffle=true (5 folds, per-class counts [5,5]) — the shape whose
    # per-class orders must genuinely differ between two seeds.
    #
    # TWO `have`s, because the first alone would be too weak to mean anything:
    #   `_ground` discharges the spec predicate at that input, but the spec pins
    #   `result` to a term over those same inputs, so it would close even if the
    #   input landed in a degenerate branch;
    #   `_thread` EVALUATES the modeled behavior at that input down to the
    #   concrete two-element threaded list, pinning the admission to the
    #   THREADED arm the F2P actually exercises — class 0 drawn from
    #   `seedState 0` and class 1 from the ADVANCED state.
    # Measured load-bearing: `_thread` FAILS against the weak-constant-state
    # rival ("Tactic `rfl` failed: pure [(shuffleN (seedState 0) 5).1,
    # (shuffleN (seedState 0) 5).1] is not definitionally equal to
    # [(shuffleN (seedState 0) 5).1, (shuffleN (shuffleN (seedState 0) 5).2 5).1]"),
    # so it is not a restatement that any impl would satisfy.
    #
    # Scope: both `have`s live inside the proof region, after a BYTE-IDENTICAL
    # theorem statement; no declaration, lemma, axiom or assumption token is
    # added, and the frozen tactic script follows verbatim.
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _INTRO,
            _INTRO +
            "  have _ground : problem_spec_classOrders 0 true 5 [5, 5]\n"
            "      (implementation_classOrders 0 true 5 [5, 5]) := by\n"
            "    unfold problem_spec_classOrders implementation_classOrders\n"
            "    simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte,\n"
            "      List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, pure_bind,\n"
            "      List.nil_append, perClassShuffleOrders, List.cons_append, Nat.max_self]\n"
            "    rfl\n"
            "  have _thread : implementation_classOrders 0 true 5 [5, 5]\n"
            "      = [(shuffleN (seedState 0) 5).1,\n"
            "         (shuffleN (shuffleN (seedState 0) 5).2 5).1] := by\n"
            "    unfold implementation_classOrders\n"
            "    simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte,\n"
            "      List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, pure_bind,\n"
            "      List.nil_append, List.cons_append, Nat.max_self]\n"
            "    rfl\n",
        ),
        "rationale": (
            "the obligation must be SATISFIABLE at the F2P-shaped input (5 folds, "
            "two equal classes of 5 under shuffle=true), and satisfiable by "
            "EVALUATION rather than in the abstract: `_ground` discharges "
            "`problem_spec_classOrders 0 true 5 [5, 5]` at that concrete point, and "
            "`_thread` reduces the modeled behavior there to the explicit "
            "two-element threaded list — class 0 from `seedState 0`, class 1 from "
            "the ADVANCED state — so the admission is pinned to the threaded arm "
            "the F2P exercises rather than to a degenerate branch. The frozen "
            "theorem statement is byte-identical and the frozen script follows "
            "verbatim; no declaration or assumption token is added. If it FAILS => "
            "the obligation is unsatisfiable at a real input (the total-carrier "
            "analogue of PRECOND-TOO-STRONG)."
        ),
    },

    # ====================================================== uniqueness (attacks)

    # weak-constant-state — the PRE-PATCH bug, attacking the ON threading clause.
    {
        "id": "weak-constant-state",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ON, _R_CONST),
        "refinement": (
            "this IS the pre-change data flow: the generator is re-initialised from "
            "the raw seed inside every class instead of being threaded, so every class "
            "draws from the identical initial state. Its faithful real counterpart is "
            "the unchanged repo, where classes of equal size receive the IDENTICAL "
            "order and the seed has no power to differentiate the collection of orders. "
            "The FAIL_TO_PASS asserts two distinct seeds yield DIFFERENT sorted per-fold "
            "test sets, which fails under identical per-class draws. So a verifying "
            "rival here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the ON clause `perClassShuffleOrders nFolds counts (seedState "
            "seed)`: at seed 0, nFolds 1, counts [1,1], class 1's order is pinned to a "
            "draw from the ADVANCED state, but the rival draws it from `seedState 0` "
            "again. Attacks the threading (state-carry-forward) sub-domain. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # class 1: gold draws from the advanced state, rival re-draws from seedState 0.
        "witness": (
            "example (h : (shuffleN (shuffleN (seedState 0) 1).2 1).1 "
            "≠ (shuffleN (seedState 0) 1).1) :\n"
            "    ¬ problem_spec_classOrders 0 true 1 [1, 1]\n"
            "      (implementation_classOrders 0 true 1 [1, 1]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            + _ON_SIMP.replace(
                "List.nil_append,", "List.nil_append, Nat.max_self,") +
            "  intro heq\n"
            "  injection heq with h1 h2\n"
            "  injection h2 with h3 h4\n"
            "  exact h h3.symm"
        ),
    },

    # weak-double-advance — attacks the ADVANCE-step granularity of the ON clause.
    {
        "id": "weak-double-advance",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ON, _R_DOUBLE),
        "refinement": (
            "this advances the shared generator by TWO draws between classes instead of "
            "one (an extra spurious consume per class). Every class beyond the first "
            "then draws from the wrong generator state, so the real patched splitter's "
            "per-fold test sets diverge from the gold's — the exact sorted assignments "
            "the FAIL_TO_PASS and the fold-coverage PASS_TO_PASS tests depend on change. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ON clause: at seed 3, nFolds 2, counts [1,1], class 1's "
            "order is pinned to the state ONE draw beyond class 0, but the rival draws "
            "it from the state TWO draws beyond. Attacks the per-step advance "
            "granularity; correct only on counts of length <= 1. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # nFolds 2 so `max 1 2 = 2` (varies nFolds vs the other witnesses); norm_num
        # reduces the max before the ON reduction recipe runs.
        "witness": (
            "example (h : (shuffleN (shuffleN (shuffleN (seedState 3) 2).2 2).2 2).1\n"
            "           ≠ (shuffleN (shuffleN (seedState 3) 2).2 2).1) :\n"
            "    ¬ problem_spec_classOrders 3 true 2 [1, 1]\n"
            "      (implementation_classOrders 3 true 2 [1, 1]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            "  norm_num only\n"
            + _ON_SIMP +
            "  intro heq\n"
            "  injection heq with h1 h2\n"
            "  injection h2 with h3 h4\n"
            "  exact h h3"
        ),
    },

    # weak-start-advanced — attacks the ANCHOR of the ON clause (which state class 0
    # draws from).
    {
        "id": "weak-start-advanced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ON, _R_STARTADV),
        "refinement": (
            "this burns one throw-away draw from the shared generator BEFORE class 0, "
            "so every class's order is shifted by one draw relative to the gold. The "
            "real patched splitter then produces a different (still seed-dependent) "
            "per-fold assignment than the gold on the F2P input, and the deterministic "
            "fold layout the coverage/index PASS_TO_PASS tests assume changes. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the ON clause: at seed 7, nFolds 1, counts [1], class 0's "
            "order is pinned to a draw from `seedState 7`, but the rival draws it from "
            "the once-advanced state. Attacks the stream anchor; correct only on empty "
            "counts. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # class 0: gold draws from seedState 7, rival from the advanced state.
        "witness": (
            "example (h : (shuffleN (shuffleN (seedState 7) 1).2 1).1 "
            "≠ (shuffleN (seedState 7) 1).1) :\n"
            "    ¬ problem_spec_classOrders 7 true 1 [1]\n"
            "      (implementation_classOrders 7 true 1 [1]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            + _ON_SIMP.replace(
                "List.nil_append,", "List.nil_append, Nat.max_self,") +
            "  intro heq\n"
            "  injection heq with h1 h2\n"
            "  exact h h1"
        ),
    },

    # weak-drop-last-class — attacks the LENGTH (and P3's prefix) of the result.
    {
        "id": "weak-drop-last-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ON, _R_DROPLAST),
        "refinement": (
            "this processes one fewer class than there are classes (an off-by-one in "
            "the per-class loop bound), so the last class never receives an order and "
            "is dropped from the stratified split. The real splitter would fail to "
            "assign that class's samples to folds — the fold-coverage / shape "
            "PASS_TO_PASS tests and the F2P diverge from the gold. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED because the result must equal the full threaded list: at seed 2, "
            "nFolds 1, counts [2] the spec pins a length-1 result but the rival returns "
            "the empty list (a strict prefix). Attacks the result LENGTH; correct only "
            "on empty counts. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # counts [2] so `dropLast` yields [] (rival) vs a length-1 gold; `max 2 1 = 2`
        # varies counts vs the other witnesses.
        #
        # The refutation is closed by `simp` on the reduced list equation, NOT by
        # `decide`. AUDIT NOTE: a `decide` here is a false discriminator. The
        # mismatch it is asked to settle is `[] = [(shuffleN (seedState 2) 2).1]`
        # against the RIVAL — decidable, because a nil/cons clash needs no element
        # comparison — but against the FROZEN solution the same script leaves
        # `[x] = [x]` over an OPAQUE element, and `decide` cannot reduce
        # `List.hasDecEq` on it ("reduction got stuck at the Decidable instance").
        # Gold then fails by STUCK REDUCTION rather than by refutation, which
        # carries no information: the identical error appears for a true claim
        # about gold. Measured: gold exit 1 with "did not reduce to `isTrue` or
        # `isFalse`". `simp` instead closes the rival by `List.nil_eq`/cons
        # injectivity (no element decision needed) and, on gold, reduces the goal
        # to `¬ ([x] = [x])` and leaves `heq : pure [x] = [x] ⊢ False` UNSOLVED —
        # a semantic refusal, so the two exit codes now discriminate on the spec.
        "witness": (
            "example :\n"
            "    ¬ problem_spec_classOrders 2 true 1 [2]\n"
            "      (implementation_classOrders 2 true 1 [2]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            "  simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte,\n"
            "    List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, pure_bind,\n"
            "    List.nil_append, perClassShuffleOrders, List.dropLast]\n"
            "  intro heq\n"
            "  simp at heq"
        ),
    },

    # weak-off-reverse — attacks the OFF clause (shuffle = false).
    {
        "id": "weak-off-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _OFF, _R_OFFREV),
        "refinement": (
            "this corrupts the shuffle=OFF path: each class's range is returned "
            "REVERSED rather than in natural ascending order. A real splitter with the "
            "no-shuffle branch reversed would lay out every class's positions backwards, "
            "diverging from the deterministic no-shuffle fold layout the PASS_TO_PASS "
            "no-shuffle tests (test_stratified_kfold_no_shuffle, the fold-index checks) "
            "assert. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the OFF clause `counts.map (fun c => List.range (max c "
            "nFolds))`: at shuffle false, seed 5, nFolds 1, counts [3] the spec pins "
            "[[0,1,2]] but the rival returns [[2,1,0]]. Attacks the shuffle=false arm — "
            "the OTHER top-level clause, held at `true` by every ON rival. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # shuffle = false: fully transparent, plain `decide`.
        "witness": (
            "example :\n"
            "    ¬ problem_spec_classOrders 5 false 1 [3]\n"
            "      (implementation_classOrders 5 false 1 [3]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            "  simp only [Id.run, Bool.not_false, reduceIte]\n"
            "  decide"
        ),
    },

    # weak-off-no-clamp (AUDIT-ADDED) — attacks the `max c nFolds` RANGE WIDTH on
    # the OFF branch. Every pre-audit rival carried the clamp verbatim, so this
    # sub-clause was pinned by the spec but unfalsified by the battery.
    {
        "id": "weak-off-no-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _OFF, _R_OFFNOCLAMP),
        "refinement": (
            "this drops the per-class range WIDTH clamp: a class is laid out over "
            "only its own sample count instead of over `max(count, nFolds)` "
            "positions. A real splitter losing that clamp gives a class with fewer "
            "samples than folds too few positions to deal out, so the per-fold "
            "layout the deterministic no-shuffle PASS_TO_PASS tests "
            "(test_stratified_kfold_no_shuffle, test_stratified_kfold_ratios) "
            "assert changes for exactly those classes. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the OFF clause's range width: at shuffle false, seed 5, "
            "nFolds 3, counts [1] the spec pins `List.range (max 1 3)` = [[0,1,2]] "
            "but the rival returns `List.range 1` = [[0]]. Attacks the CLAMP "
            "sub-clause — correct only when every count is >= nFolds, which is why "
            "it needs a count STRICTLY BELOW nFolds (the other OFF rival holds "
            "nFolds at 1, where the clamp is inert). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # shuffle = false: fully transparent, plain `decide`. nFolds 3 > count 1 is
        # the sub-domain where the clamp is load-bearing.
        "witness": (
            "example :\n"
            "    ¬ problem_spec_classOrders 5 false 3 [1]\n"
            "      (implementation_classOrders 5 false 3 [1]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            "  simp only [Id.run, Bool.not_false, reduceIte]\n"
            "  decide"
        ),
    },

    # weak-on-no-clamp (AUDIT-ADDED) — the same clamp omission on the LOAD-BEARING
    # ON branch: the generator is consumed at the wrong WIDTH per class, so both
    # the order and the state carried forward are wrong.
    {
        "id": "weak-on-no-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ON, _R_ONNOCLAMP),
        "refinement": (
            "this consumes the shared generator over a class's own count instead of "
            "`max(count, nFolds)` positions. For any class with fewer samples than "
            "folds the real splitter both arranges too few positions AND advances "
            "the shared generator by a differently-sized draw, so every LATER "
            "class's order shifts too. The F2P's seed-dependent per-fold test sets "
            "and the deterministic layout the fold PASS_TO_PASS tests assume both "
            "diverge from the gold. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ON clause's range width: at seed 1, nFolds 3, counts "
            "[1] class 0's order is pinned to `shuffleN (seedState 1) (max 1 3)` — "
            "a draw of THREE positions — but the rival draws only `shuffleN "
            "(seedState 1) 1`. Attacks the CLAMP sub-clause inside the threaded "
            "arm; correct only when every count is >= nFolds. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # nFolds 3 > count 1: the clamp is load-bearing here, and the two draws
        # differ only through the opaque `shuffleN`, so the witness CONDITIONS on
        # the carrier exactly at the width the rival gets wrong. `norm_num only`
        # reduces `max 1 3` before the ON reduction recipe runs.
        "witness": (
            "example (h : (shuffleN (seedState 1) 1).1 ≠ (shuffleN (seedState 1) 3).1) :\n"
            "    ¬ problem_spec_classOrders 1 true 3 [1]\n"
            "      (implementation_classOrders 1 true 3 [1]) := by\n"
            "  unfold problem_spec_classOrders implementation_classOrders\n"
            "  norm_num only\n"
            + _ON_SIMP +
            "  intro heq\n"
            "  injection heq with h1 h2\n"
            "  exact h h1"
        ),
    },
]


# No consumed @ContractOnly axiom: seedState/shuffleN are opaque and taken
# structurally, so the axiom lane belongs to G-CONF (the A-reference) regardless.
AXIOM_TESTS = []
