"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14894 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a positive that legitimately re-proves, inside
the ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_dualCoef`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

This battery is PORTED from the nagini sibling (``../nagini/properties.py``),
whose per-case ``rationale``/``refinement`` are the adversarial arguments carried
over; the mechanics are re-expressed against this backend's carrier and every
reject case additionally carries a machine-checked refutation witness (a concept
with no nagini counterpart).

DEFENDED SURFACE (one modeled behavior; one obligation ``correct_dualCoef``). A
coefficient-matrix assembly from a support-set size ``width``, a per-class repeat
count ``rows`` (precondition ``1 ≤ rows`` in the theorem binder), and a stored
buffer ``data``. It must ALWAYS succeed (``∃ m, result = Except.ok m`` — never
abort) and pin every output component to the inputs:

  * width = 0 (empty support set)  →  m = the canonical empty matrix EXACTLY:
      data = [] ∧ indices = [] ∧ indptr = [0, 0] ∧ nrows = 1 ∧ ncols = 0
  * width ≠ 0 (non-empty)          →  the full block matrix:
      data = data ∧ indices = tileRange width rows ∧
      indptr = rowOffsets rows width ∧ nrows = rows ∧ ncols = width

BINDER STRUCTURE (read before judging binder coverage). The spec predicate's
INPUT binders are ``width``, ``rows``, ``data`` (and the type ``α``). The empty
branch fires exactly on ``width = 0``; the block branch on ``width ≠ 0``. The
result's dependence on each binder differs by branch, and the reject witnesses
vary them so no rival is refuted only at a pinned point:

  * ``width`` — THE discriminator (empty vs block branch). Witnesses take it at
    0 (the empty-branch rivals) and at 1 (the five block-branch rivals).
  * ``rows`` — controls the block branch's shape (``indptr = rowOffsets rows
    width``, ``nrows = rows``) and, through ``[0,0]`` vs a longer offset vector,
    separates the empty pin from any padded/shifted rival. Witnesses take it at
    1, 2, 3 (all satisfying the ``1 ≤ rows`` precondition). It is also the sole
    varying factor in ``indices = tileRange width rows``, probed by
    rival-block-wrong-repeat-count.
  * ``data`` — forwarded by identity on the block branch (``m.data = data``) and
    forced empty on the empty branch. The block-branch witnesses use a NON-empty
    buffer ``[7]`` so the identity-forward is live; the empty-branch witnesses
    use ``[]`` except rival-empty-forwards-buffer, which takes ``[7]`` AT
    width = 0 — the spec is total in ``data``, so that is the only input at which
    the empty branch's ``m.data = []`` is demonstrably a constant pin rather than
    an echo of an already-empty input.

Every independent top-level clause of the postcondition is attacked:
  - the ALWAYS-succeeds clause (``∃ m, result = Except.ok m``) by rival-abort;
  - the empty-branch ``indptr = [0,0]`` by rival-empty-nonzero-tail (final
    boundary 5), rival-wrong-open (opens at 1), and rival-empty-padded (length 3);
    ``indices = []`` by rival-empty-wrong-indices; ``nrows = 1`` by
    rival-empty-wrong-nrows; ``ncols = 0`` by rival-empty-wrong-ncols;
    ``data = []`` by rival-empty-forwards-buffer;
  - the block-branch ``indptr = rowOffsets rows width`` by
    rival-block-wrong-row-offsets (that conjunct ALONE) and, jointly with
    ``ncols = width``, by rival-flat-nonempty (returns the empty matrix for
    width ≥ 1); ``nrows = rows`` by rival-block-transposed-shape; ``data = data``
    by rival-block-drops-buffer; ``indices = tileRange width rows`` by
    rival-block-wrong-repeat-count.

ADVERSARIAL READ of the nagini classes on this carrier (see the accounting block
at the bottom for the full nagini→lean map):

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling notes it already:
    both parameters are plain immutable ints passed by value, there is no
    ``Acc(x,1/2)`` frame to overwrite. Lean is referentially transparent — every
    input is an immutable value with no heap footprint and no ``mut`` binder — so
    the class is vacuous here too. NOT fabricated.
  * CAPABILITY-TOKEN / CONTROL-FLOW EFFECT — VACUOUS. The only control-flow
    difference (empty vs block guard) IS observable through the returned value
    (``Except.ok`` vs an abort, and the empty/block shape), which the spec pins.
    No side-effect channel exists.
  * UNGROUNDED-ORACLE ECHO — N/A. The nagini consumed axiom ``range_step``
    (numpy.arange) is a DEEP model here (``rowOffsets`` / ``tileRange`` spelled
    out); the ``axioms`` region declares no ``opaque``/``axiom``. The result is
    grounded structurally in the inputs, not equated to an answer key. Hence
    there is no "wrong oracle-echo that verifies" reject case, mirroring the
    nagini note, and the AXIOM lane is empty (G-AX's job).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen impl's
syntactic form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete, ``decide``-able input. Each was checked with
two real ``lake env lean`` builds to ELABORATE against its rival and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). The carrier is fully transparent (``CSRMatrix`` fields are ground
lists/nats), so no witness needs to condition on an opaque term; all witnesses
bind nothing (no consistency-probe risk).

GOLD-SIDE FAILURE MODES, RE-DERIVED (independent audit; every number below is an
observed ``lean_verify.sh`` exit code, not an expectation). Rebuilding all 13
witnesses twice reproduces rival 0 / gold 1 throughout. Because "gold's build
failed" is only evidence if the exit code TRACKS THE CLAIM, each case was also
run against a FORGERY — the same input, with the refutation flipped to assert the
spec HOLDS there.

Twelve of the thirteen forgeries invert (gold 0, rival 1). ONE did not, and the
earlier revision of this docstring was wrong to report otherwise:
rival-abort-on-empty closed with a bare ``simp [Id.run]``, and that shape leaves
``Id``'s ``pure`` unreduced on the frozen solution, so the specification was
never applied to the solution's value at all. Measured, four builds, 5.3–7.7 s
each, none timing out:

  * the refutation on the frozen solution — exit 1, ``unsolved goals ⊢ ∀ (x :
    CSRMatrix ℕ), pure (Except.ok (emptyCSR ℕ)) = Except.ok x → … → ¬x.ncols = 0``;
  * the SAME tactic body with the ``¬`` dropped, i.e. claiming the spec HOLDS
    there (which it does) — exit 1 as well, ``unsolved goals ⊢ ∃ m, pure
    (Except.ok (emptyCSR ℕ)) = Except.ok m ∧ …``.

Byte-for-byte the same unreduced ``pure (Except.ok (emptyCSR ℕ)) = Except.ok _``
carrier in both, and the same exit code: the solution's build did not depend on
what was claimed, so that exit code attested to a refutation the kernel never
performed. The witness was therefore RE-AUTHORED to decide the clause it
attacks. It now takes the ALWAYS-succeeds clause's own ``hm : result =
Except.ok m``, projects it to the decidable ``(implementation_dualCoef 0 2
[]).toOption.isSome = true``, and closes by ``decide`` on the opposite Boolean —
so the kernel EVALUATES the implementation at (width=0, rows=2, data=[]).
Re-measured: rival exit 0; frozen solution exit 1 with ``Tactic `decide` proved
that the proposition (implementation_dualCoef 0 2 []).toOption.isSome = false is
false`` — the kernel reporting the witness's claim FALSE of the solution, not a
tactic running out of road. The opposite-claim control now inverts, which is the
whole point: ``… .toOption.isSome = true := by decide`` is exit 0 on the frozen
solution and exit 1 on this rival (mirror message), and the full positive spec
claim at that same input is exit 0 on the solution and exit 1 on the rival. Gold
therefore demonstrably SATISFIES the clause the rival violates, at the witness's
own point.

Two further gold-side signature classes are not plain evaluations, so both were
probed rather than read:

  * the five empty-branch witnesses that closed with a bare ``simp at h<field>``
    recorded the uninformative signature ```simp` made no progress``. Replacing
    the closing step with a deliberate type error (``exact (hx : Nat)``) reveals
    WHY: on gold the hypothesis is ``(emptyCSR ℕ).indptr = [0, 0]``, on the rival
    it is ``{ …, indptr := [0, 5], … }.indptr = [0, 0]`` — i.e. the concrete
    equation on each side, which is a real refutation and not a tactic mismatch.
    Bare ``simp`` could not see it only because ``emptyCSR`` is not unfolded, so
    those five witnesses now close with ``simp [emptyCSR] at h<field>`` (matching
    the two empty-branch witnesses that always did). Gold still fails, but now on
    its own reduced goal (``hx : True ⊢ False``) rather than on a no-progress
    tactic, so the recorded signature reports the refutation instead of hiding it.
  * the five block-branch witnesses fail on gold at the value-pinning
    ``have hred … := by rfl`` step. That step is EVALUATIVE, not syntactic: the
    same ``rfl`` pinning gold's OWN correct record at (1, 2, [7]) elaborates
    against gold (exit 0) and fails against all four record-corrupting rivals
    (exit 1). So the step decides the record's contents and its failure on gold
    is a decided definitional inequality about the impl's value.

The whole ``simp only [Id.run, pure]`` + ``rw [Except.ok.injEq]`` shape warned
about in the accounting block was re-measured and remains the wrong shape for the
block branch; nothing in the battery uses it.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14894"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full gold impl body (everything between the impl markers). Positive-control
# reshapes replace it wholesale; the whole-impl rivals (abort / flat) also.
_GOLD_IMPL = (
    "def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :\n"
    "    Except String (CSRMatrix α) := Id.run do\n"
    "  -- the column indices: the support ramp repeated once per class\n"
    "  let indices := tileRange width rows\n"
    "  -- empty support set ⇒ return the canonical empty matrix instead of building\n"
    "  -- evenly spaced row offsets (which would require stepping by the support size)\n"
    "  if width = 0 then\n"
    "    return Except.ok (emptyCSR α)\n"
    "  -- non-empty: evenly spaced row offsets and the full block matrix\n"
    "  let indptr := rowOffsets rows width\n"
    "  return Except.ok\n"
    "    { data := data, indices := indices, indptr := indptr,\n"
    "      nrows := rows, ncols := width }"
)

# The empty-branch return line alone (unique). Empty-branch rivals swap ONLY this
# so they stay correct on the entire non-empty domain (gold build) and diverge
# only on width = 0.
_EMPTY_RETURN = "    return Except.ok (emptyCSR α)"

# Frozen tactic body (wholly inside the proof region). Positive controls that
# reshape the impl retune this; reject rivals leave it frozen (they are judged by
# their witness, not by whether this script happens to break).
_PROOF_BODY = (
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  by_cases h : width = 0\n"
    "  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩\n"
    "    · simp only [Id.run, h, if_true]; rfl\n"
    "    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩\n"
    "    · intro hne; exact absurd h hne\n"
    "  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :\n"
    "        CSRMatrix α), ?_, ?_, ?_⟩\n"
    "    · simp only [Id.run, h, if_false]; rfl\n"
    "    · intro h0; exact absurd h0 h\n"
    "    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩"
)


# =====================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT
# implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
# `theorem correct_dualCoef` statement byte-identical; only impl + proof body
# change, no new axiom/lemma, no sorry.
# =====================================================================

# (1) Inverted branch order: build the block matrix FIRST under `if width ≠ 0`,
# empty layout as the fall-through. Same domain partition (width ≠ 0 vs width = 0)
# and same returned values as gold; only the executable control-flow shape
# changes. Proof retuned to close the reordered conditional (`if_pos`/`if_neg`).
_POS_INVERTED_IMPL = (
    "def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :\n"
    "    Except String (CSRMatrix α) := Id.run do\n"
    "  let indices := tileRange width rows\n"
    "  if width ≠ 0 then\n"
    "    let indptr := rowOffsets rows width\n"
    "    return Except.ok\n"
    "      { data := data, indices := indices, indptr := indptr,\n"
    "        nrows := rows, ncols := width }\n"
    "  return Except.ok (emptyCSR α)"
)
_POS_INVERTED_PROOF = (
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  by_cases h : width = 0\n"
    "  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩\n"
    "    · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]; rfl\n"
    "    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩\n"
    "    · intro hne; exact absurd h hne\n"
    "  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :\n"
    "        CSRMatrix α), ?_, ?_, ?_⟩\n"
    "    · simp only [Id.run, if_pos h]; rfl\n"
    "    · intro h0; exact absurd h0 h\n"
    "    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩"
)
_POS_INVERTED_MOD = _swap(
    _swap(_BASE, _GOLD_IMPL, _POS_INVERTED_IMPL), _PROOF_BODY, _POS_INVERTED_PROOF)

# (2) Pure-functional reshape: drop the `Id.run do` scaffold entirely and pattern
# match on `width` (0 vs succ). Same values on every input; proof retuned to the
# `cases width` shape. No loop / no induction lemma.
_POS_MATCH_IMPL = (
    "def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :\n"
    "    Except String (CSRMatrix α) :=\n"
    "  match width with\n"
    "  | 0 => Except.ok (emptyCSR α)\n"
    "  | Nat.succ w =>\n"
    "    Except.ok\n"
    "      { data := data, indices := tileRange (w + 1) rows,\n"
    "        indptr := rowOffsets rows (w + 1), nrows := rows, ncols := w + 1 }"
)
_POS_MATCH_PROOF = (
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  cases width with\n"
    "  | zero =>\n"
    "    refine ⟨emptyCSR α, rfl, ?_, ?_⟩\n"
    "    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩\n"
    "    · intro hne; exact absurd rfl hne\n"
    "  | succ w =>\n"
    "    refine ⟨_, rfl, ?_, ?_⟩\n"
    "    · intro h0; exact absurd h0 (by simp)\n"
    "    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩"
)
_POS_MATCH_MOD = _swap(
    _swap(_BASE, _GOLD_IMPL, _POS_MATCH_IMPL), _PROOF_BODY, _POS_MATCH_PROOF)


# =====================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected, each with a machine-checked refutation witness at a concrete
# input and the refinement argument for why its faithful real counterpart would
# NOT resolve the F2P. Witnesses were built twice (rival: elaborates; gold:
# fails).
# =====================================================================

# (DISCRIMINATOR — the actual bug) Build the offsets UNCONDITIONALLY: on the
# empty support set the construction aborts (modeled as `Except.error`) instead
# of returning a matrix — exactly the pre-patch `np.arange(0, size+1, 0)`
# ZeroDivisionError. Rejected by the ALWAYS-succeeds clause (`∃ m, result =
# Except.ok m`) at width = 0.
_RIVAL_ABORT_IMPL = (
    "def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :\n"
    "    Except String (CSRMatrix α) := Id.run do\n"
    "  let indices := tileRange width rows\n"
    "  if width = 0 then\n"
    "    return Except.error \"row-offset construction aborted: zero spacing step\"\n"
    "  let indptr := rowOffsets rows width\n"
    "  return Except.ok\n"
    "    { data := data, indices := indices, indptr := indptr,\n"
    "      nrows := rows, ncols := width }"
)
_RIVAL_ABORT_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_ABORT_IMPL)
_WIT_ABORT = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 2 []\n"
    "    (implementation_dualCoef 0 2 []) := by\n"
    "  unfold problem_spec_dualCoef\n"
    "  rintro ⟨m, hm, -⟩\n"
    "  -- the ALWAYS-succeeds clause hands over `hm : result = Except.ok m`, which\n"
    "  -- forces this Boolean projection of the result to be `true`\n"
    "  have hok : (implementation_dualCoef (α := Nat) 0 2 []).toOption.isSome = true := by\n"
    "    rw [hm]; rfl\n"
    "  -- and HERE the kernel evaluates the implementation at that input: this rival\n"
    "  -- aborts, so the projection is in fact `false`\n"
    "  have hno : (implementation_dualCoef (α := Nat) 0 2 []).toOption.isSome = false := by\n"
    "    decide\n"
    "  rw [hok] at hno\n"
    "  exact Bool.noConfusion hno\n"
)

# (PARTIAL-DOMAIN — empty branch, final boundary) Correct on the entire non-empty
# domain (gold build) but for the empty case returns an indptr whose final entry
# is non-zero ([0, 5]). Rejected by the empty-branch `indptr = [0, 0]`.
_RIVAL_TAIL_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := [], indices := [], indptr := [0, 5], nrows := 1, ncols := 0 }")
_WIT_TAIL = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 3 []\n"
    "    (implementation_dualCoef 0 3 []) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨-, -, hptr, -, -⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hptr\n"
)

# (PARTIAL-DOMAIN — empty branch, opening boundary) Correct on the non-empty
# domain but for the empty case opens at boundary 1 ([1, 0]). A row-pointer MUST
# open at 0. Rejected by the empty-branch `indptr = [0, 0]`.
_RIVAL_OPEN_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := [], indices := [], indptr := [1, 0], nrows := 1, ncols := 0 }")
_WIT_OPEN = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 1 []\n"
    "    (implementation_dualCoef 0 1 []) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨-, -, hptr, -, -⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hptr\n"
)

# (PARTIAL-DOMAIN — empty branch, LENGTH) Correct on the non-empty domain but for
# the empty case returns a PADDED indptr [0, 0, 0] (final still 0, opening still
# 0). The canonical empty CSR indptr is EXACTLY [0, 0]; a 3-boundary indptr for a
# 1-row matrix is malformed. Rejected by the empty-branch `indptr = [0, 0]`.
_RIVAL_PADDED_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := [], indices := [], indptr := [0, 0, 0], nrows := 1, ncols := 0 }")
_WIT_PADDED = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 2 []\n"
    "    (implementation_dualCoef 0 2 []) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨-, -, hptr, -, -⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hptr\n"
)

# (PARTIAL-DOMAIN — empty branch, INDICES) Correct on the non-empty domain but
# for the empty case returns a non-empty column-index vector ([9]) where the
# canonical empty matrix stores no indices. Rejected by the empty-branch
# `indices = []`.
_RIVAL_IDX_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := [], indices := [9], indptr := [0, 0], nrows := 1, ncols := 0 }")
_WIT_IDX = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 2 []\n"
    "    (implementation_dualCoef 0 2 []) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨-, hidx, -, -, -⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hidx\n"
)

# (PARTIAL-DOMAIN — empty branch, ROW COUNT) Correct on the non-empty domain but
# for the empty case reports two logical rows (nrows = 2) where the canonical
# empty matrix has exactly one. Rejected by the empty-branch `nrows = 1`.
_RIVAL_NROWS_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := [], indices := [], indptr := [0, 0], nrows := 2, ncols := 0 }")
_WIT_NROWS = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 3 []\n"
    "    (implementation_dualCoef 0 3 []) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨-, -, -, hnr, -⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hnr\n"
)

# (PARTIAL-DOMAIN — non-empty collapse) Returns the empty matrix for EVERY input,
# including width ≥ 1. Correct only on width = 0. Rejected on the block branch by
# `indptr = rowOffsets rows width` / `ncols = width` (the empty matrix's
# `indptr = [0,0]` ≠ `rowOffsets rows width` and `ncols = 0 ≠ width`).
_RIVAL_FLAT_IMPL = (
    "def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :\n"
    "    Except String (CSRMatrix α) := Id.run do\n"
    "  return Except.ok (emptyCSR α)"
)
_RIVAL_FLAT_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_FLAT_IMPL)
# NOTE on the witness shape (block branch). The empty-branch witnesses can lead
# with `simp only [..., reduceIte]` because at `width = 0` the guard's condition
# is the literal `0 = 0`, which `reduceIte` discharges. At `width = 1` the guard
# is `1 = 0`: `reduceIte` does NOT fire on it, so the `Id.run do` term stays
# wrapped in an unreduced `if 1 = 0 then _ else _` and any `rw
# [Except.ok.injEq]` finds no `Except.ok _ = Except.ok _` pattern to rewrite.
# An earlier revision of this witness led with `simp only [Id.run, pure]` and
# then `rw [Except.ok.injEq] at hm`; that shape DID elaborate against this rival
# (whose impl has no guard at all, so its term reduces) and DID fail on the
# frozen solution — clearing both halves of the gate's discrimination check —
# but gold's failure was `Tactic 'rewrite' failed: Did not find an occurrence of
# the pattern`, i.e. the witness never reached its own refutation on gold. That
# is a SYNTACTIC failure, not a satisfied spec, so it discriminated nothing. The
# shape below instead pins the rival's concrete return value by `rfl` (a
# definitional-reduction step that gold decides and REFUTES: `implementation_
# dualCoef 1 2 [7] is not definitionally equal to Except.ok (emptyCSR ℕ)`), then
# derives the contradiction from the block-branch clause. Verified by hand:
# rival exit 0; gold exit 1 on the `rfl` step with a decided definitional
# inequality about the impl's own value.
_WIT_FLAT = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 1 2 [7]\n"
    "    (implementation_dualCoef 1 2 [7]) := by\n"
    "  unfold problem_spec_dualCoef\n"
    "  rintro ⟨m, hm, -, h1⟩\n"
    "  obtain ⟨-, -, -, -, hx⟩ := h1 (by decide)\n"
    "  have hred : implementation_dualCoef (α := Nat) 1 2 [7]\n"
    "      = Except.ok (emptyCSR Nat) := by\n"
    "    rfl\n"
    "  rw [hred, Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  exact absurd hx (by simp [emptyCSR])\n"
)


# The block-branch record, isolated so the three block-branch rivals below can
# each corrupt ONE component of it while staying correct on the empty branch.
_BLOCK_RECORD = (
    "    { data := data, indices := indices, indptr := indptr,\n"
    "      nrows := rows, ncols := width }"
)

# Shared block-branch witness shape: pin the rival's concrete return value at
# (width=1, rows=2, data=[7]) by `rfl`, then contradict the block-branch clause.
# Gold refutes the `rfl` step by decided definitional inequality (see the note on
# _WIT_FLAT for why the empty-branch `reduceIte` shape cannot be reused here).
def _wit_block(record, projection, contra):
    return (
        "example : ¬ problem_spec_dualCoef (α := Nat) 1 2 [7]\n"
        "    (implementation_dualCoef 1 2 [7]) := by\n"
        "  unfold problem_spec_dualCoef\n"
        "  rintro ⟨m, hm, -, h1⟩\n"
        f"  obtain {projection} := h1 (by decide)\n"
        "  have hred : implementation_dualCoef (α := Nat) 1 2 [7] = Except.ok\n"
        f"      {record} := by\n"
        "    rfl\n"
        "  rw [hred, Except.ok.injEq] at hm\n"
        "  subst hm\n"
        f"  exact absurd hx (by {contra})\n"
    )


# (PARTIAL-DOMAIN — block branch, SHAPE TRANSPOSED) Correct on the empty branch
# and correct in every stored array, but reports the shape transposed: `nrows :=
# width, ncols := rows`. Rejected by the block-branch `m.nrows = rows`.
_RIVAL_TRANSPOSED_MOD = _swap(
    _BASE, _BLOCK_RECORD,
    "    { data := data, indices := indices, indptr := indptr,\n"
    "      nrows := width, ncols := rows }")
_WIT_TRANSPOSED = _wit_block(
    "{ data := [7], indices := tileRange 1 2, indptr := rowOffsets 2 1,"
    " nrows := 1, ncols := 2 }",
    "⟨-, -, -, hx, -⟩", "decide")

# (PARTIAL-DOMAIN — block branch, BUFFER DROPPED) Correct on the empty branch and
# in the index/offset vectors and the shape, but stores an EMPTY value buffer
# instead of forwarding the supplied one. Rejected by the block-branch
# identity-forward `m.data = data` — the one clause no other rival attacks.
_RIVAL_DROPDATA_MOD = _swap(
    _BASE, _BLOCK_RECORD,
    "    { data := [], indices := indices, indptr := indptr,\n"
    "      nrows := rows, ncols := width }")
_WIT_DROPDATA = _wit_block(
    "{ data := [], indices := tileRange 1 2, indptr := rowOffsets 2 1,"
    " nrows := 2, ncols := 1 }",
    "⟨hx, -, -, -, -⟩", "decide")

# (PARTIAL-DOMAIN — block branch, WRONG REPEAT COUNT) Correct on the empty branch,
# and its shape and row offsets are right, but the support ramp is repeated
# `width` times instead of once per class (`tileRange width width`). Agrees with
# gold exactly when width = rows, so it is a genuine near-miss. Rejected by the
# block-branch `m.indices = tileRange width rows`.
_RIVAL_TILECOUNT_MOD = _swap(
    _BASE, "  let indices := tileRange width rows\n",
    "  let indices := tileRange width width\n")
_WIT_TILECOUNT = _wit_block(
    "{ data := [7], indices := tileRange 1 1, indptr := rowOffsets 2 1,"
    " nrows := 2, ncols := 1 }",
    "⟨-, hx, -, -, -⟩", "simp [tileRange, tileCopies]")

# (PARTIAL-DOMAIN — block branch, ROW OFFSETS ALONE) Correct on the empty branch,
# and correct in the value buffer, the index vector AND the shape, but it appends
# one extra boundary to the row-offset vector (`rowOffsets rows width ++ [0]`).
# This is the block-branch `indptr` conjunct attacked IN ISOLATION, which the
# battery previously lacked: rival-flat-nonempty is the only other rival that
# perturbs the block offsets, and it collapses the whole record to the empty
# matrix, so it violates `ncols = width` at the same time. A spec that DROPPED the
# block-branch `m.indptr = rowOffsets rows width` conjunct therefore still passed
# every other case (rival-flat-nonempty stays rejected on `ncols`), which is
# exactly the SPEC-TOO-WEAK blind spot the uniqueness lane exists to find. Found
# by re-deriving the clause/rival matrix rather than by reading the accounting
# block, which had recorded this conjunct as covered "with ncols".
_RIVAL_BOFFS_MOD = _swap(
    _BASE, "  let indptr := rowOffsets rows width\n",
    "  let indptr := rowOffsets rows width ++ [0]\n")
_WIT_BOFFS = _wit_block(
    "{ data := [7], indices := tileRange 1 2, indptr := rowOffsets 2 1 ++ [0],"
    " nrows := 2, ncols := 1 }",
    "⟨-, -, hx, -, -⟩", "simp [rowOffsets]")

# (PARTIAL-DOMAIN — empty branch, COLUMN COUNT) Correct on the non-empty domain
# but for the empty case reports 5 logical columns where the canonical empty
# matrix has zero. Closes the one empty-branch component the ported battery left
# unattacked (`m.ncols = 0`).
_RIVAL_ENCOLS_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := [], indices := [], indptr := [0, 0], nrows := 1, ncols := 5 }")
_WIT_ENCOLS = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 2 []\n"
    "    (implementation_dualCoef 0 2 []) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨-, -, -, -, hx⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hx\n"
)

# (PARTIAL-DOMAIN — empty branch, BUFFER FORWARDED) For the empty support set the
# canonical empty matrix stores NOTHING, but this rival forwards whatever buffer
# it was handed. Its witness is the only one that takes a NON-empty `data` at
# width = 0, so it also demonstrates that the empty branch's `m.data = []` is a
# real constant pin and not an echo of an input that happens to be empty.
_RIVAL_EFWD_MOD = _swap(
    _BASE, _EMPTY_RETURN,
    "    return Except.ok { data := data, indices := [], indptr := [0, 0], nrows := 1, ncols := 0 }")
_WIT_EFWD = (
    "example : ¬ problem_spec_dualCoef (α := Nat) 0 2 [7]\n"
    "    (implementation_dualCoef 0 2 [7]) := by\n"
    "  unfold problem_spec_dualCoef implementation_dualCoef\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨m, hm, h0, -⟩\n"
    "  rw [Except.ok.injEq] at hm\n"
    "  subst hm\n"
    "  obtain ⟨hx, -, -, -, -⟩ := h0 trivial\n"
    "  simp [emptyCSR] at hx\n"
)


# =====================================================================
# ADMISSIBILITY — the nagini sibling's `admiss-empty-support-vectors`, ported
# after all. The port's accounting block called it VACUOUS on the ground that a
# self-call "would assert only the post-image the spec already pins"; that is
# true of a self-call, but the case's actual content — that the F2P-shaped input
# is IN the modeled domain, i.e. the precondition binder admits it — is
# expressible here and is NOT implied by the positives (a positive quantifies
# over all `rows` satisfying `1 ≤ rows` but never exhibits an instance, so a
# precondition that had accidentally excluded the F2P point would still let both
# positives verify). Instantiating `correct_dualCoef` at the F2P-shaped input
# (empty support set, one class) discharges `1 ≤ rows` by `decide` and applies
# the obligation. If the binder could not be discharged for this normal input,
# that is PRECOND-TOO-STRONG. Stated inside the proof region, so the spec view
# and the `correct_dualCoef` statement stay byte-identical.
_ADMISS_PROOF = _PROOF_BODY + (
    "\n\n"
    "-- admissibility: the F2P-shaped input (empty support set, one class) lies\n"
    "-- inside the modeled domain — the precondition binder admits it and the\n"
    "-- obligation applies there.\n"
    "example : problem_spec_dualCoef (α := Nat) 0 1 []\n"
    "    (implementation_dualCoef 0 1 []) :=\n"
    "  correct_dualCoef 0 1 [] (by decide)"
)
_ADMISS_MOD = _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-inverted-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INVERTED_MOD,
        "rationale": "structurally-different but CORRECT: the branch order is inverted "
                     "(build the block matrix first under `if width ≠ 0`, empty layout as "
                     "the fall-through). Same domain partition and same returned values as "
                     "gold; only the executable control-flow shape changes. Proof retuned to "
                     "close the reordered conditional (`if_pos`/`if_neg`); no new axiom/lemma, "
                     "no sorry, `theorem correct_dualCoef` statement byte-identical. If a "
                     "faithful inverted-branch impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-functional-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH_MOD,
        "rationale": "structurally-different but CORRECT: drops the `Id.run do` scaffold and "
                     "pattern-matches on `width` (0 vs succ), computing the same value on "
                     "every input. Proof retuned to the `cases width` shape (no induction "
                     "lemma). A faithful functional reshape MUST verify, else SPEC-TOO-STRONG; "
                     "statement unchanged, no new axiom/lemma.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "rival-abort-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ABORT_MOD,
        "refinement": "this is the EXACT pre-gold behaviour: the row-offset vector is built "
                      "unconditionally, and on the empty support set the spacing step collapses "
                      "to zero so the construction aborts (modeled as `Except.error`) instead of "
                      "returning a matrix — the `ZeroDivisionError` the issue reports. Its "
                      "faithful real patch is the pre-patch, which on the F2P input (empty "
                      "support_vectors_) raises and FAILS the F2P (the regression test that "
                      "fits an SVR with an empty support set) — so it would NOT resolve; a "
                      "verifying rival here would be a true verify⇏resolve break.",
        "rationale": "the discriminator. REJECT from the ALWAYS-succeeds clause `∃ m, result = "
                     "Except.ok m`: for width = 0 the rival returns `Except.error _`, so no `m` "
                     "witnesses the existential. Witness at (width=0, rows=2, data=[]): it "
                     "takes the clause's own `result = Except.ok m`, projects it to the "
                     "decidable `(implementation_dualCoef 0 2 []).toOption.isSome = true`, "
                     "and DECIDES the opposite Boolean, so the kernel evaluates the impl at "
                     "that input rather than stopping at an unreduced `pure`. If it "
                     "verified => SPEC-TOO-WEAK (the abort the fix removes would be admissible).",
        "witness": _WIT_ABORT,
    },
    {
        "id": "rival-empty-nonzero-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TAIL_MOD,
        "refinement": "correct on the entire non-empty domain (gold build) but for the empty "
                      "case returns an indptr whose final boundary is 5, not 0. A faithful real "
                      "patch that produces a CSR with a non-zero final indptr for an empty "
                      "support set yields a matrix with stored entries — where the F2P asserts "
                      "the assembled matrix stores nothing. That patch FAILS the F2P, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from the empty-branch clause `m.indptr = [0, 0]`. Witness at "
                     "(width=0, rows=3, data=[]): the rival's `indptr = [0, 5]` ≠ [0, 0]. "
                     "Attacks the stored-count observable on the empty case the bug is about. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_TAIL,
    },
    {
        "id": "rival-wrong-open",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OPEN_MOD,
        "refinement": "correct on the non-empty domain but for the empty case opens at boundary "
                      "1 instead of 0 ([1, 0]). A CSR row-pointer MUST open at 0 (the start of "
                      "flat storage); a faithful patch producing indptr[0] ≠ 0 builds a "
                      "malformed matrix whose first row is ill-defined, diverging from the "
                      "canonical empty layout — not behaviourally equal to gold.",
        "rationale": "REJECT from the empty-branch clause `m.indptr = [0, 0]`. Witness at "
                     "(width=0, rows=1, data=[]): the rival's `indptr = [1, 0]` ≠ [0, 0], which "
                     "differs from the tail rival at the OPENING boundary (a distinct component "
                     "of the same list-equality clause). If it verified, the opening-boundary "
                     "invariant would be hollow.",
        "witness": _WIT_OPEN,
    },
    {
        "id": "rival-empty-padded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PADDED_MOD,
        "refinement": "correct on the entire non-empty domain (gold build) but for the empty "
                      "case returns the padded indptr [0, 0, 0] (final still 0, opening still 0 "
                      "— a near-miss the tail/open rivals do not subsume). The canonical empty "
                      "CSR indptr is EXACTLY [0, 0] (a one-row matrix: nrows+1 = 2 boundaries); "
                      "a faithful patch handing a 3-boundary indptr to a one-row matrix builds "
                      "a malformed CSR (indptr length must be rows+1), so its assembled matrix "
                      "diverges from gold — not behaviourally equal.",
        "rationale": "REJECT from the empty-branch clause `m.indptr = [0, 0]`, which pins the "
                     "empty layout's LENGTH (not just its endpoints). Witness at (width=0, "
                     "rows=2, data=[]): the rival's `indptr = [0, 0, 0]` ≠ [0, 0]. This is the "
                     "length near-miss that endpoint-only pins would miss; it carries its own "
                     "distinguishing input. If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_PADDED,
    },
    {
        "id": "rival-empty-wrong-indices",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_IDX_MOD,
        "refinement": "correct on the entire non-empty domain (gold build) but for the empty "
                      "case returns a non-empty column-index vector where the canonical empty "
                      "matrix stores no indices. A faithful patch emitting stored column "
                      "indices for an empty support set builds a CSR that references columns it "
                      "has no data for — a malformed matrix diverging from the canonical empty "
                      "layout; it would NOT resolve.",
        "rationale": "REJECT from the empty-branch clause `m.indices = []`. Witness at "
                     "(width=0, rows=2, data=[]): the rival's `indices = [9]` ≠ []. Attacks the "
                     "empty-branch index vector, a clause the boundary/length rivals leave "
                     "untouched. If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_IDX,
    },
    {
        "id": "rival-empty-wrong-nrows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NROWS_MOD,
        "refinement": "correct on the non-empty domain but for the empty case reports two "
                      "logical rows where the canonical empty matrix has exactly one "
                      "(sp.csr_matrix([]) is a one-by-zero matrix). A faithful patch reporting "
                      "the wrong row count builds a matrix of the wrong shape, diverging from "
                      "gold; it would NOT resolve.",
        "rationale": "REJECT from the empty-branch clause `m.nrows = 1`. Witness at (width=0, "
                     "rows=3, data=[]): the rival's `nrows = 2` ≠ 1. Note the rival sets nrows "
                     "= 2 while the input `rows = 3`, so it is not merely echoing an input — "
                     "the empty layout's row count is pinned to the constant 1 regardless of "
                     "`rows`. If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_NROWS,
    },
    {
        "id": "rival-flat-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FLAT_MOD,
        "refinement": "collapses EVERY input to the canonical empty matrix, ignoring the "
                      "support-set size; correct only on the width = 0 sub-domain. A faithful "
                      "real patch that always emits an empty CSR would, for a non-empty model "
                      "(support set present, ≥1 class), produce zero stored entries where gold "
                      "produces the full block — failing the P2P fit/predict tests that "
                      "exercise non-trivial support sets. That patch would NOT resolve.",
        "rationale": "REJECT from the block-branch clauses (`m.ncols = width`, and equally "
                     "`m.indptr = rowOffsets rows width`). Witness at (width=1, rows=2, "
                     "data=[7]): the rival returns the empty matrix, whose `ncols = 0` ≠ "
                     "width = 1 (its `indptr = [0, 0]` likewise ≠ `rowOffsets 2 1 = "
                     "[0, 1, 2]`). Probed on the block branch (width ≥ 1) with a non-empty "
                     "`data`, so it varies the discriminator `width` and the forwarded "
                     "`data` away from the empty-branch witnesses. If it verified => "
                     "SPEC-TOO-WEAK (the non-empty progression would be hollow).",
        "witness": _WIT_FLAT,
    },
    {
        "id": "rival-block-transposed-shape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TRANSPOSED_MOD,
        "refinement": "correct on the empty branch and correct in every stored array, but "
                      "reports the shape TRANSPOSED (`nrows := width, ncols := rows`). A "
                      "faithful patch handing the assembler a transposed shape builds a "
                      "matrix whose row count is the support-set size and whose column count "
                      "is the per-class repeat — for any model where those differ the stored "
                      "arrays no longer describe the declared shape, so the assembled matrix "
                      "diverges from gold and the fit/predict tests that consume it break. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the block-branch clause `m.nrows = rows`. Witness at "
                     "(width=1, rows=2, data=[7]): the rival reports nrows = 1 where the "
                     "spec pins nrows = rows = 2. This isolates the SHAPE clause, which the "
                     "flat rival collapses together with the storage arrays. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _WIT_TRANSPOSED,
    },
    {
        "id": "rival-block-drops-buffer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROPDATA_MOD,
        "refinement": "correct on the empty branch, and its index vector, row offsets and "
                      "shape are all right, but it stores an EMPTY value buffer instead of "
                      "forwarding the coefficients it was handed. A faithful patch that "
                      "assembles the matrix with no stored values produces a matrix of the "
                      "right shape but numerically all-zero, so every downstream prediction "
                      "depending on those coefficients is wrong while the shape assertions "
                      "still pass. It would NOT resolve.",
        "rationale": "REJECT from the block-branch identity-forward clause `m.data = data`. "
                     "Witness at (width=1, rows=2, data=[7]): the rival stores [] where the "
                     "spec pins the supplied buffer [7]. This is the ONLY rival attacking the "
                     "identity-forward — every other rival leaves `data` untouched on the "
                     "block branch, so without it a spec missing the `m.data = data` conjunct "
                     "would still pass the whole battery. If it verified => SPEC-TOO-WEAK.",
        "witness": _WIT_DROPDATA,
    },
    {
        "id": "rival-block-wrong-repeat-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TILECOUNT_MOD,
        "refinement": "correct on the empty branch, with the right shape and the right row "
                      "offsets, but it repeats the support ramp once per SUPPORT VECTOR "
                      "instead of once per class (`tileRange width width`). It agrees with "
                      "gold exactly on the diagonal width = rows, which is what makes it a "
                      "near-miss rather than an obvious break. A faithful patch tiling the "
                      "ramp the wrong number of times yields a column-index vector whose "
                      "length disagrees with the value buffer, so the assembled matrix is "
                      "malformed (or silently mis-indexed) for every model with more than one "
                      "class and a differing support-set size. It would NOT resolve.",
        "rationale": "REJECT from the block-branch clause `m.indices = tileRange width rows`. "
                     "Witness at (width=1, rows=2, data=[7]): the rival builds `tileRange 1 1 "
                     "= [0]` where the spec pins `tileRange 1 2 = [0, 0]`. This probes the "
                     "index vector's REPEAT COUNT — the one place the binders `width` and "
                     "`rows` are combined — which no other rival varies. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _WIT_TILECOUNT,
    },
    {
        "id": "rival-block-wrong-row-offsets",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_BOFFS_MOD,
        "refinement": "correct on the empty branch, and its value buffer, index vector and "
                      "shape are all right, but the row-offset vector carries one extra "
                      "boundary beyond the last row. A CSR row-pointer must have exactly "
                      "rows+1 boundaries; a faithful patch handing the assembler an "
                      "over-long offset vector builds a matrix whose declared row count "
                      "disagrees with its own offset array, so the assembled matrix is "
                      "malformed for every non-empty support set — it would NOT resolve.",
        "rationale": "REJECT from the block-branch clause `m.indptr = rowOffsets rows width`, "
                     "attacked ALONE. Witness at (width=1, rows=2, data=[7]): the rival's "
                     "offsets are `rowOffsets 2 1 ++ [0] = [0, 1, 2, 0]` where the spec pins "
                     "`rowOffsets 2 1 = [0, 1, 2]`. This is the isolation the battery lacked: "
                     "rival-flat-nonempty is the only other rival perturbing the block "
                     "offsets and it breaks `ncols = width` simultaneously, so a spec "
                     "dropping this conjunct alone would have passed every other case. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _WIT_BOFFS,
    },
    {
        "id": "rival-empty-wrong-ncols",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ENCOLS_MOD,
        "refinement": "correct on the non-empty domain but for the empty case reports five "
                      "logical columns where the canonical empty matrix has zero. A faithful "
                      "patch declaring a non-zero column count for a matrix with no stored "
                      "values builds a shape that disagrees with its own storage arrays, "
                      "diverging from the canonical empty layout; it would NOT resolve.",
        "rationale": "REJECT from the empty-branch clause `m.ncols = 0`. Witness at (width=0, "
                     "rows=2, data=[]): the rival's `ncols = 5` ≠ 0. This closes the last "
                     "empty-branch component the ported battery left unattacked (its "
                     "accounting block had recorded it as \"a further add\"). If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _WIT_ENCOLS,
    },
    {
        "id": "rival-empty-forwards-buffer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EFWD_MOD,
        "refinement": "correct on the non-empty domain but for the empty support set it "
                      "forwards whatever value buffer it was handed instead of storing "
                      "nothing. A faithful patch emitting stored values for an empty support "
                      "set produces a matrix whose storage arrays disagree with its own "
                      "one-by-zero shape and which reports stored entries where the empty "
                      "case must report none — the exact observable the empty-support "
                      "regression asserts. It would NOT resolve.",
        "rationale": "REJECT from the empty-branch clause `m.data = []`. Witness at (width=0, "
                     "rows=2, data=[7]): the rival stores [7] where the spec pins []. This is "
                     "the only witness in the battery taking a NON-empty `data` at width = 0, "
                     "which is what makes `m.data = []` demonstrably a CONSTANT pin rather "
                     "than an echo of an input that happened to be empty — the ported battery "
                     "declined this input as out-of-domain, but the spec is total in `data` "
                     "and the clause is only load-bearing at a non-empty buffer. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _WIT_EFWD,
    },
    {
        "id": "admiss-empty-support-set",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_MOD,
        "rationale": "the nagini sibling's admissibility case, ported (this port had recorded "
                     "it VACUOUS). Instantiates `correct_dualCoef` at the F2P-shaped input "
                     "(empty support set, one class) and discharges the `1 ≤ rows` binder by "
                     "`decide`, witnessing that this normal input lies INSIDE the modeled "
                     "domain. Not implied by the positives: they quantify over all `rows` "
                     "satisfying the binder but never exhibit an instance, so a precondition "
                     "that accidentally excluded the empty-support point would still let both "
                     "positives verify. Stated inside the proof region, so the spec view and "
                     "the obligation statement stay byte-identical. If the binder could not "
                     "be discharged for this normal input => PRECOND-TOO-STRONG.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive `pos-control-inverted-branch`, 1 admissibility, 5 uniqueness rivals)
# plus a 2-case AXIOM lane. This bundle models the SAME single functional core
# (the dual_coef_ assembly tail), so the port is close to 1:1 on the SPEC lane;
# the differences are carrier-driven, recorded below.
#
#   sibling case                 -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-inverted-branch  -> pos-inverted-branch           PORTED
#                                   (+ pos-functional-match)      ADDED positive
#   admiss-empty-support-vectors -> admiss-empty-support-set       PORTED (see below)
#   rival-drop-guard             -> rival-abort-on-empty          RE-EXPRESSED
#   rival-empty-nonzero-tail     -> rival-empty-nonzero-tail      PORTED
#   rival-wrong-open             -> rival-wrong-open              PORTED
#   rival-empty-padded           -> rival-empty-padded            PORTED
#   rival-flat-nonempty          -> rival-flat-nonempty          PORTED
#   (no sibling)                 -> rival-empty-wrong-indices     ADDED
#   (no sibling)                 -> rival-empty-wrong-nrows       ADDED
#   (no sibling)                 -> rival-empty-wrong-ncols       ADDED
#   (no sibling)                 -> rival-empty-forwards-buffer   ADDED
#   (no sibling)                 -> rival-block-transposed-shape  ADDED
#   (no sibling)                 -> rival-block-drops-buffer      ADDED
#   (no sibling)                 -> rival-block-wrong-repeat-count ADDED
#   (no sibling)                 -> rival-block-wrong-row-offsets  ADDED (audit)
#   AXIOM_TESTS (2)              -> (none)                        DROPPED (G-AX)
#
# RE-EXPRESSED (rival-drop-guard -> rival-abort-on-empty): nagini expresses the
#   bug as a call to the partial `range_step` whose `Requires(step >= 1)` a
#   width=0 (step=0) call cannot discharge — a precondition-failure rejection.
#   This bundle has no consumed axiom: `np.arange` is a DEEP model (`rowOffsets`),
#   so there is no callee precondition to violate. The SAME argument (the
#   pre-patch builds the offsets unconditionally and cannot produce a matrix for
#   the empty support set) is re-expressed as an ABORT: the empty branch returns
#   `Except.error`, refuted by the spec's ALWAYS-succeeds clause `∃ m, result =
#   Except.ok m`. This is exactly the prepatch skeleton (Solution_prepatch.lean).
# PORTED (admissibility, after an earlier revision recorded it VACUOUS): that
#   revision argued a self-call "asserts only the post-image the spec already
#   pins", and that the scenario is covered because the positives verify at
#   width = 0. Both halves are wrong on this carrier. The positives verify a
#   ∀-statement over every `rows` satisfying `1 ≤ rows`; they never EXHIBIT an
#   instance, so a precondition that had accidentally excluded the F2P-shaped
#   point would leave both positives verifying unchanged. And the case is
#   expressible: `example : problem_spec_dualCoef (α := Nat) 0 1 []
#   (implementation_dualCoef 0 1 []) := correct_dualCoef 0 1 [] (by decide)`
#   elaborates inside the proof region, keeping the spec view and the obligation
#   statement byte-identical (checked: variant admissible, module builds). What it
#   adds over the positives is precisely the nagini case's content — the normal
#   input is IN the modeled domain and the binder discharges there.
# VACUOUS (frame/permission-mutation, capability-token): the nagini sibling
#   itself records these as N/A (both inputs are immutable ints by value; the
#   guard's effect is observable through the returned value). Lean is
#   referentially transparent, so they remain vacuous — not fabricated.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this bundle declares no
#   axiom (`np.arange`/`np.tile` are deep models, not consumed axioms — see
#   refinement.md), so there is nothing to probe and the gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE: the thirteen reject witnesses probe distinct input
# tuples. `width` takes {0 (×8), 1 (×5)}; `rows` takes {1, 2, 3}; `data` takes
# {[], [7]} on BOTH branches. Every top-level conjunct of the postcondition now
# has at least one rival that violates that conjunct alone:
#
#   ∃ m, result = Except.ok m      rival-abort-on-empty
#   empty: indptr = [0, 0]         rival-empty-nonzero-tail (final entry),
#                                  rival-wrong-open (opening entry),
#                                  rival-empty-padded (length)
#   empty: indices = []            rival-empty-wrong-indices
#   empty: nrows = 1               rival-empty-wrong-nrows
#   empty: ncols = 0               rival-empty-wrong-ncols
#   empty: data = []               rival-empty-forwards-buffer
#   block: indptr = rowOffsets     rival-block-wrong-row-offsets (ALONE),
#                                  rival-flat-nonempty (jointly with ncols)
#   block: indices = tileRange     rival-block-wrong-repeat-count
#   block: nrows = rows            rival-block-transposed-shape
#   block: ncols = width           rival-flat-nonempty (jointly with indptr)
#   block: data = data             rival-block-drops-buffer
#
# The block-branch `indptr` row was the LAST co-attack in the table and an audit
# closed it. Before rival-block-wrong-row-offsets, the only rival perturbing the
# block offsets was rival-flat-nonempty, which collapses the whole record to the
# empty matrix and so violates `ncols = width` at the same time — meaning a spec
# that DROPPED the block-branch `m.indptr = rowOffsets rows width` conjunct still
# passed all fourteen other cases. That is the same "co-attack is not attack"
# error this block already calls out for the empty branch, one clause further on;
# the new rival perturbs the offset vector and nothing else.
#
# An earlier revision left four of these unattacked (`m.data = []` and
# `m.ncols = 0` on the empty branch; the identity-forward, shape and repeat count
# on the block branch) and argued the empty-branch pair was "co-attacked by the
# sibling empty rivals". Co-attack is not attack: a spec DROPPING one of those
# conjuncts would have passed the whole battery, which is the SPEC-TOO-WEAK
# outcome the uniqueness lane exists to detect. In particular that revision held
# every empty-branch witness at `data = []` on the ground that a non-empty buffer
# at width = 0 is "out of the F2P domain" — but the spec quantifies over all
# `data` with no such restriction, and at `data = []` the conjunct `m.data = []`
# is indistinguishable from an identity-forward. rival-empty-forwards-buffer
# takes `data = [7]` at width = 0 for exactly that reason.
#
# WITNESS SHAPE, block branch (recorded because the natural shape silently does
# not discriminate). A witness that unfolds the impl with `simp only [Id.run,
# pure]` and then `rw [Except.ok.injEq] at hm` elaborates against a block-branch
# rival, and FAILS on the frozen solution — so it passes both halves of the
# gate's check — but its gold-side failure is `Tactic 'rewrite' failed: Did not
# find an occurrence of the pattern`. At width = 1 the guard's condition is the
# literal `1 = 0`, on which `reduceIte` does NOT fire (it does fire on `0 = 0`,
# which is why the empty-branch witnesses may lead with `simp only [...,
# reduceIte]`), so the term stays wrapped in an unreduced `if 1 = 0 then _ else _`
# and there is no `Except.ok _ = Except.ok _` to rewrite. That is a SYNTACTIC
# failure: the witness never reaches its own refutation on gold, so it
# discriminates nothing, and the two-build check cannot tell it from a satisfied
# spec. All four block-branch witnesses therefore pin the impl's concrete value
# with `have hred : implementation_dualCoef .. = Except.ok <record> := by rfl`,
# whose gold-side failure is `Tactic 'rfl' failed: .. is not definitionally equal
# to ..` — a decided definitional inequality, i.e. a real refutation.
AXIOM_TESTS = []
