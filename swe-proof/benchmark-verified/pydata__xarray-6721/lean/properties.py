# properties.py — PBT falsification battery for pydata__xarray-6721 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region surgery — it edits ONLY the impl region
# (and, for the reshaped soundness positive, the proof body), so the frozen spec
# (docstring / axioms / pure / post-conditions) stays byte-identical, same_spec
# holds by construction, and the `theorem correct_getChunksizes` STATEMENT is
# preserved verbatim. No case introduces sorry/admit/native_decide/axiom or any
# new top-level theorem or lemma beyond the frozen set.
#
# ---------------------------------------------------------------------------
# PORT NOTE — carrier narrowing vs the nagini sibling
# ---------------------------------------------------------------------------
# The nagini sibling models the SAME behavior over a very different carrier. It
# contracts a walk over a list of array-bearing entries returning a flat list of
# (axis, length) pairs plus a trailing "loads forced" tally, and it carries the
# whole discriminator in a CONSUMABLE capability token: two abstract views of an
# entry's payload, one of which requires-but-does-not-return the token, so an
# implementation that reads the materialising view can never re-establish the
# postcondition. That machinery is a fractional-permission construction; it has
# no counterpart on a referentially transparent carrier and is NOT what this
# bundle models.
#
# Here the observable properties of a variable are supplied directly as INPUTS
# (`XVar.hasChunks`, `.chunksizes`, `.isDuckArray`, `.materializeRaises`), and
# the single load-bearing clause is the master relation
#
#     result = mergeVars vars []
#
# i.e. the collected mapping is EXACTLY the reference fold over the variables'
# chunk metadata. Because the reference fold consults only `hasChunks` and
# `chunksizes`, the clause has a second, decisive consequence: the outcome is
# independent of `isDuckArray` and `materializeRaises`. So the side-effect
# attack that nagini spends a capability token to express becomes, on this
# carrier, an ordinary VALUE divergence — an implementation that lets a
# variable's loadability influence the answer disagrees with the fold at a
# concrete input, and can be refuted by a witness rather than by a token.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (what every rival attacks)
# ---------------------------------------------------------------------------
# The master clause `result = mergeVars vars []`, and specifically these
# independent consequences of it:
#   * INDEPENDENCE — neither `isDuckArray` nor `materializeRaises` may influence
#     the result, for a variable that is not chunked AND for one that is;
#   * the REPEAT rule — a dimension re-recorded with the SAME block lengths
#     leaves the mapping unchanged (it is not an inconsistency);
#   * the INCONSISTENCY rule — a dimension re-recorded with DIFFERENT block
#     lengths rejects the whole operation (it does not silently overwrite);
#   * TOTALITY over the collection — every variable is folded in, not just the
#     first chunked one, and not every one BUT the first;
#   * ORDER — dimensions appear in first-seen order;
#   * FIDELITY of the recorded value — the block lengths stored against a
#     dimension are the ones the variable exposes, unreordered;
#   * the SKIP rule — a variable that is not chunked contributes NOTHING, not a
#     placeholder entry.
#
#   * WITHIN-VARIABLE consistency — a single variable that exposes the same
#     dimension twice with DIFFERENT block lengths rejects too; the agreement test
#     is against everything recorded so far, not only against earlier variables.
#
# The spec predicate has ONE input binder, `vars : List XVar`, so binder
# variation means varying the collection and its variables' fields. The ten
# reject witnesses probe TEN distinct points and between them hold `hasChunks`
# at both values, `isDuckArray` at both values, `materializeRaises` at both
# values, `chunksizes` at empty / one entry / two entries, a single dimension's
# block lengths at length 1 and length 2, and the collection length at 1 and 2 —
# so no field of the modeled carrier is pinned across all rivals.
#
# The rival-by-point agreement matrix was machine-computed (each rival's impl
# evaluated against `mergeVars vars []` at all nine points): the diagonal
# diverges everywhere and the frozen impl agrees everywhere, so no rival is
# definitionally equal to the frozen one on this carrier and each witness is
# refuted at a point its own rival actually gets wrong.
#
# ---------------------------------------------------------------------------
# OMITTED nagini cases and why (repeated in the payload `assessment`)
# ---------------------------------------------------------------------------
#   * The two FRAME / permission-mutation rivals (writing a read-only input
#     field to satisfy a value clause vacuously) are VACUOUS on this backend:
#     Lean is referentially transparent, there is no aliasing and no fractional
#     permission to violate, so no counterpart rival exists to author.
#   * The nagini ADMISSIBILITY positive asserts, inside the impl region, that the
#     precondition's structural facts hold of a normal input. It is NOT omitted
#     any more: an audit found the recorded reason ("`correct_getChunksizes` is an
#     UNCONDITIONAL `∀ vars` with no precondition hypothesis, so
#     PRECOND-TOO-STRONG is unreachable") is the wrong test on a total carrier.
#     The obligation is indeed an unconditional universal, so there is no
#     hypothesis to be over-strong — but the analogue here is the obligation being
#     UNSATISFIABLE at exactly a behaviour-pinning input, which is directly
#     testable: discharge the spec predicate at that concrete collection, by
#     evaluation, as a `have`, before closing the frozen obligation verbatim. It
#     is ported as the `admiss-pinned-input` positive below.
#   * The three nagini PARTIAL-DOMAIN rivals (emit the per-dimension pair with
#     its components transposed; force the empty marker on the FIRST entry;
#     emit a wrong empty marker for a non-contributing entry) are NOT omitted —
#     an audit found they had been dropped without a recorded reason and are all
#     expressible here. They are ported as rivals 7, 8 and 9 below: this carrier
#     has no positional (axis, length) pair and no (-1,-1) marker, but the
#     ARGUMENTS they carry (a recorded dimension's block lengths must be the ones
#     the variable exposes; every variable is folded, including the first; a
#     variable that is not chunked contributes NOTHING) are all consequences of
#     the master clause and are each refuted at a concrete collection.
#   * The two nagini "echo" rivals (materialise, then write a literal 0 into the
#     trailing tally slot) and the two tally/length rivals (nonzero trailing
#     slot; truncated result) attack a RESULT SHAPE this bundle does not have:
#     the trailing forced-loads counter is nagini-carrier scaffolding, and the
#     result here is an `Except Unit (List (String × List Nat))` with no such
#     slot. The ARGUMENT they carry — that an implementation must not let a
#     variable's loadability change the answer — is ported instead as the two
#     independence rivals below, where it is a value divergence.
#   * Divergence / non-termination is a KNOWN HOLE, not a vacuous class — an
#     audit corrected the earlier claim that "a diverging implementation cannot be
#     written at all". The frozen `implementation_getChunksizes` is a total Lean
#     `def`, but a rival may reach for `partial def`, which the variant scope does
#     not ban, and a self-calling `partial def` with no decreasing measure IS
#     writable. It is nevertheless not shippable as a reject case, and this was
#     measured rather than argued: the variant fails to build (exit 1, so the
#     gate would read "rejected"), but the witness cannot refute it either —
#     the recursive term does not reduce, so the witness's own build fails with
#     `Tactic 'injection' failed: equality of constructor applications expected`
#     on an unevaluated `spin … = Except.ok [("a", [1])]` (exit 1). That is
#     `witness-unproven`, i.e. inconclusive, which the gate scores as
#     MALFORMED-TESTS rather than as a rejection. So the class is recorded as a
#     hole in what this battery can attest, not as a class that does not exist.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job, and this bundle
#     ships no consumed axiom (the accumulation and its rejection rule are
#     modeled structurally over the inputs, not over an opaque callee).
from pathlib import Path

INSTANCE = "pydata__xarray-6721"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each lies entirely inside the impl or proof region of the
# frozen Solution.lean and is unique in the file.
# ---------------------------------------------------------------------------

# The frozen impl body (impl region).
_GOLD_BODY = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks"""

# The frozen impl DECLARATION (body included) — the soundness positive replaces
# the imperative loop with a functional shape, so it edits the whole `def`.
_GOLD_IMPL = """def implementation_getChunksizes (vars : List XVar) :
    Except Unit (List (String × List Nat)) := Id.run do
""" + _GOLD_BODY

# The frozen proof body, verbatim between the proof markers. Only the soundness
# positive touches it (it must reprove the identical obligation statement for a
# different impl shape); every reject case keeps it untouched.
_i = _BASE.index("-- proof-start\n") + len("-- proof-start\n")
_GOLD_PROOF = _BASE[_i:_BASE.index("-- proof-end")]
if "theorem correct_getChunksizes" not in _GOLD_PROOF:
    raise AssertionError("drift: proof region does not carry the obligation")


# ===========================================================================
# SOUNDNESS POSITIVE — a structurally different CORRECT implementation
# ===========================================================================
# The frozen implementation is imperative: a mutable accumulator threaded by two
# nested `for` loops with an early `return` on inconsistency. This positive
# replaces it with a purely FUNCTIONAL pair of front-recursive folds: a
# per-entry recorder returning `Option` (none = inconsistent) and two recursive
# folds over the pair list and the variable list, with the chunked test written
# in the opposite polarity (`if v.hasChunks = false then … else …`) and the
# agreement test written with its operands swapped (`p.2 = c'` rather than
# `c' ≠ p.2`). Same decision, same order, same result; no mutable state and no
# early return at all.
#
# The proof is reauthored for the new shape but stays cheap: the frozen `forIn`
# bridge lemmas are no longer needed (there is no `forIn` to bridge), so the two
# frozen bridging theorems are REPURPOSED — kept at their frozen names, since a
# variant may not declare a new theorem — to relate the functional folds to the
# spec's reference fold by the same two inductions. `correct_getChunksizes` is
# closed with its statement byte-identical.
#
# If a faithful correct implementation in a different shape could NOT satisfy
# `result = mergeVars vars []`, the spec would be SPEC-TOO-STRONG.
_POS_IMPL = """def recordPair (acc : List (String × List Nat)) (p : String × List Nat) :
    Option (List (String × List Nat)) :=
  match acc.lookup p.1 with
  | none    => some (acc ++ [p])
  | some c' => if p.2 = c' then some acc else none

def foldPairs : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match recordPair acc p with
    | none      => .error ()
    | some acc' => foldPairs acc' ps

def foldVars : List XVar → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | [],      acc => .ok acc
  | v :: vs, acc =>
    if v.hasChunks = false then foldVars vs acc
    else
      match foldPairs acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => foldVars vs acc'

def implementation_getChunksizes (vars : List XVar) :
    Except Unit (List (String × List Nat)) := foldVars vars []"""

_POS_PROOF = """theorem innerLoop_eq_mergePairs (acc pairs : List (String × List Nat)) :
    foldPairs acc pairs = mergePairs acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [foldPairs, mergePairs, insertChunk, recordPair]
    cases h : acc.lookup p.1 with
    | none => simp [ih]
    | some c' =>
      by_cases hc : p.2 = c'
      · simp [hc, ih]
      · simp [hc, Ne.symm hc]

theorem outerLoop_eq_mergeVars (acc : List (String × List Nat)) (vars : List XVar) :
    foldVars vars acc = mergeVars vars acc := by
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    unfold foldVars mergeVars
    cases h : v.hasChunks with
    | false => simp only [Bool.false_eq_true, if_false, if_true]; exact ih acc
    | true =>
      simp only [Bool.true_eq_false, if_false, if_true]
      rw [innerLoop_eq_mergePairs]
      cases mergePairs acc v.chunksizes with
      | error e => rfl
      | ok acc' => exact ih acc'

theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  intro vars
  unfold problem_spec_getChunksizes implementation_getChunksizes
  rw [outerLoop_eq_mergeVars]

"""


# ===========================================================================
# UNIQUENESS RIVALS — wrong implementations of the SAME frozen spec
# ===========================================================================

# --- 1. loadability aborts an UNCHUNKED variable ---------------------------
# A variable that contributes nothing to the mapping is nevertheless allowed to
# abort the whole operation when it holds no in-place handle and its contents
# cannot be loaded. Correct on every variable whose contents CAN be loaded and
# on every variable holding an in-place handle; wrong exactly on the sub-domain
# the spec's independence clause names.
_REJ_ABORT_UNCHUNKED = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if !v.hasChunks && !v.isDuckArray && v.materializeRaises then return .error ()
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks"""

# --- 2. loadability aborts ANY variable ------------------------------------
# The same abort, un-guarded by chunked-ness: it fires for a CHUNKED variable
# too, so it also discards contributions the mapping must contain. Strictly
# wider than rival 1 and refuted at a different point (a chunked variable),
# which rival 1 handles correctly.
_REJ_ABORT_ANY = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if !v.isDuckArray && v.materializeRaises then return .error ()
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks"""

# --- 3. every REPEATED dimension rejects -----------------------------------
# Drops the agreement test: a dimension already recorded rejects regardless of
# whether the block lengths agree. Correct on genuinely inconsistent
# collections and on collections with no repeated dimension; wrong exactly on
# the agreeing-repeat sub-domain.
_REJ_REJECT_REPEAT = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some _ => return .error ()
        | none   => chunks := chunks ++ [p]
  return .ok chunks"""

# --- 4. last writer wins ----------------------------------------------------
# The complementary error: never rejects at all, silently replacing a
# dimension's recorded block lengths with the newest ones. Correct on every
# consistent collection; wrong exactly where the inconsistency rule must fire.
_REJ_OVERWRITE = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        chunks := (chunks.filter (fun q => q.1 ≠ p.1)) ++ [p]
  return .ok chunks"""

# --- 5. stop after the first chunked variable ------------------------------
# Returns as soon as one chunked variable has been folded in, so later chunked
# variables contribute nothing. Correct on collections with at most one chunked
# variable; wrong as soon as a second one carries a dimension of its own.
_REJ_FIRST_ONLY = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
      return .ok chunks
  return .ok chunks"""

# --- 6. reversed first-seen order ------------------------------------------
# Prepends each new dimension instead of appending it. Value-identical as a
# mapping, and correct on any collection contributing at most one dimension;
# wrong on the ORDER the spec pins as soon as two dimensions are recorded.
_REJ_REVERSE_ORDER = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := [p] ++ chunks
  return .ok chunks"""

# --- 7. a recorded dimension's block lengths are transposed -----------------
# Records the right dimension NAMES in the right order, but reverses the block
# lengths it stores against each one. Correct on every dimension carrying at
# most one block length (and on any symmetric list); wrong as soon as a
# dimension carries two distinct block lengths. Ported from the sibling
# battery's transposed-pair rival: there the pair was positional, here the
# per-dimension VALUE is what gets corrupted.
_REJ_TRANSPOSE_LENGTHS = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [(p.1, p.2.reverse)]
  return .ok chunks"""

# --- 8. the FIRST variable is skipped --------------------------------------
# An off-by-one at the front of the collection: the first variable is passed
# over whatever its chunk metadata says, every later one folded normally.
# Correct on every collection whose first variable is not chunked; wrong as soon
# as it is. Complements rival 5 (which drops the TAIL) at the other end.
_REJ_SKIP_FIRST = """  let mut chunks : List (String × List Nat) := []
  let mut seenFirst : Bool := false
  for v in vars do
    if !seenFirst then
      seenFirst := true
    else if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks"""

# --- 9. a non-chunked variable contributes an entry ------------------------
# Injects a spurious entry for a variable that is not chunked, instead of
# skipping it. Correct on every collection in which every variable is chunked;
# wrong exactly on the "contributes nothing" clause. Ported from the sibling
# battery's wrong-empty-marker rival: there the skip was spelled as a sentinel
# pair, here it is the absence of an entry.
_REJ_UNCHUNKED_CONTRIBUTES = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if !v.hasChunks then
      chunks := chunks ++ [("", [])]
    else
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks"""

# --- 10. one variable's own entries are not checked against each other ------
# Added by audit. Every rival above tests the agreement rule ACROSS variables:
# each stages its newly seen dimensions in a side list and merges them only after
# the variable is finished, so entries contributed by the SAME variable are never
# looked up against one another. Correct on every collection whose variables each
# expose a dimension at most once — which is every witness point above — and wrong
# exactly when one variable exposes the same dimension twice with different block
# lengths. This is the clause the reference fold gets by threading ONE accumulator
# through the inner fold, and no other rival here disturbs it.
_REJ_WITHIN_VAR_UNCHECKED = """  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      let mut fresh : List (String × List Nat) := []
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => fresh := fresh ++ [p]
      chunks := chunks ++ fresh
  return .ok chunks"""


# ---------------------------------------------------------------------------
# Witness inputs — concrete `XVar` collections, one distinct point per rival.
# ---------------------------------------------------------------------------

def _v(has_chunks, chunksizes, is_duck, raises):
    return ("{ hasChunks := %s, chunksizes := %s, isDuckArray := %s, "
            "materializeRaises := %s }"
            % (has_chunks, chunksizes, is_duck, raises))


def _coll(*vs):
    return "[" + ", ".join(vs) + "]"


# P1 — one UNCHUNKED variable with no in-place handle whose contents cannot be
# loaded. The fold yields the empty mapping; rival 1 (and 2) rejects.
_W_UNCHUNKED_UNLOADABLE = _coll(_v("false", "[]", "false", "true"))
# P2 — one CHUNKED variable with no in-place handle whose contents cannot be
# loaded. The fold yields its one dimension; rival 2 rejects. Rival 1 is correct
# here, which is what separates the two.
_W_CHUNKED_UNLOADABLE = _coll(_v("true", '[("d", [2, 3])]', "false", "true"))
# P3 — the SAME dimension recorded twice with the SAME block lengths. The fold
# leaves the mapping unchanged; rival 3 rejects.
_W_AGREEING_REPEAT = _coll(_v("true", '[("d", [2])]', "true", "false"),
                           _v("true", '[("d", [2])]', "true", "false"))
# P4 — the same dimension with DIFFERENT block lengths. The fold rejects; rival
# 4 silently returns the overwritten mapping.
_W_INCONSISTENT = _coll(_v("true", '[("d", [2])]', "true", "false"),
                        _v("true", '[("d", [5])]', "true", "false"))
# P5 — two chunked variables carrying DISTINCT dimensions. The fold records
# both; rival 5 records only the first.
_W_TWO_CHUNKED = _coll(_v("true", '[("a", [1])]', "true", "false"),
                       _v("true", '[("b", [2])]', "true", "false"))
# P6 — one chunked variable carrying TWO dimensions. The fold records them in
# first-seen order; rival 6 records them reversed.
_W_TWO_DIMS = _coll(_v("true", '[("a", [1]), ("b", [2])]', "true", "false"))
# P7 — one chunked variable whose single dimension carries TWO DISTINCT block
# lengths. The fold records them in the order the variable exposes them; rival 7
# records them reversed. The only witness here that varies a dimension's block
# lengths to length 2, and a point at which rivals 1-6, 8 and 9 all agree with
# the fold.
_W_TWO_LENGTHS = _coll(_v("true", '[("d", [2, 3])]', "true", "false"))
# P8 — a SINGLE chunked variable, which is therefore the first. The fold records
# its dimension; rival 8 skips it and reports the empty mapping. The only
# witness here whose collection length is 1 with a chunked, loadable variable,
# which is what separates rival 8 from rival 5 (correct on a one-element
# collection) and from rivals 1/2 (whose abort needs an unloadable variable).
_W_FIRST_CHUNKED = _coll(_v("true", '[("a", [1])]', "true", "false"))
# P9 — a single variable that is NOT chunked and IS loadable. The fold yields
# the empty mapping; rival 9 reports a spurious entry. Distinct from P1: there
# the variable is unloadable (which is what rivals 1/2 need), here it is
# ordinary, so rivals 1 and 2 are both correct at this point.
_W_UNCHUNKED_LOADABLE = _coll(_v("false", "[]", "true", "false"))
# P10 — a SINGLE chunked variable exposing the same dimension TWICE with
# DIFFERENT block lengths. The fold rejects (the accumulator carries the first
# entry into the lookup for the second); rival 10, which stages a variable's own
# new entries aside and merges them only afterwards, returns both. Distinct from
# P4, where the disagreement is spread across two variables and which rival 10
# therefore handles correctly.
_W_WITHIN_VAR_CONFLICT = _coll(_v("true", '[("d", [2]), ("d", [5])]',
                                  "true", "false"))
# The behaviour-pinning input for the admissibility positive: the one point at
# which the modeled distinction bites — a variable that is not chunked, holds no
# in-place handle, and whose contents cannot be loaded. That is the shape of the
# collection this bundle's behaviour is pinned at, so it is where an obligation
# that were unsatisfiable would show up first.
_W_PINNED_INPUT = _W_UNCHUNKED_UNLOADABLE


# The witness states the spec predicate directly at a concrete collection and
# refutes it. `decide` cannot be used: `Except Unit (List (String × List Nat))`
# has no `DecidableEq` instance in this workspace, so the equality is reduced by
# `simp` over the reference fold's own unfolding lemmas instead, and the residual
# constructor equality is discharged by injection. Both builds were run for every
# rival: the witness ELABORATES against the rival (exit 0) and FAILS against the
# frozen solution (exit 1). The gold-side failure is a SEMANTIC refutation, not a
# syntactic one — `simp` reduces the spec equality at that point to `True`, so the
# residual goal is `h : True ⊢ False`, i.e. the frozen implementation really does
# agree with the fold there. The witness head binds nothing, so there are no
# hypotheses to be inconsistent and the gate's consistency probe does not apply.
def _witness(point):
    return (
        "example : ¬ problem_spec_getChunksizes\n"
        "    %s\n"
        "    (implementation_getChunksizes\n"
        "      %s) := by\n"
        "  unfold problem_spec_getChunksizes implementation_getChunksizes\n"
        "  simp +decide [Id.run, mergeVars, mergePairs, insertChunk, List.lookup]\n"
        "  all_goals (intro h; injection h with h; simp at h)\n"
        % (point, point))


# ===========================================================================
# ADMISSIBILITY POSITIVE — the obligation is SATISFIABLE at the pinned input
# ===========================================================================
# Added by audit; the lane was previously dropped. The frozen obligation is an
# unconditional `∀ vars`, so there is no precondition hypothesis to be too
# strong — but the analogue on a total carrier is the obligation being
# UNSATISFIABLE at exactly the input the modeled behaviour is pinned at, and that
# is testable directly: discharge `problem_spec_getChunksizes` at that concrete
# collection, BY EVALUATION, as a `have`, before closing the frozen obligation
# with its statement and tactic body verbatim.
#
# Nothing is assumed: no new declaration, no axiom, no sorry, and the frozen
# three-line body (`intro vars; unfold …; rw [impl_eq_outerLoop,
# outerLoop_eq_mergeVars]`) follows the `have` unchanged.
#
# The `have` is INFORMATIVE, not a tautology the tactic would close regardless —
# audited by control: the same `have` shape asserting the spec of a WRONG result
# (`.ok [("x", [7])]` in place of the implementation's own result) does NOT close;
# `simp` reduces the equation to `False` and the build fails with
# `Tactic 'rfl' failed: Expected the goal to be a binary relation ⊢ False`. So the
# step really does evaluate the postcondition at this input rather than
# discharging anything put in front of it.
_ADMISS_PROOF = _GOLD_PROOF.replace(
    """theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  intro vars""",
    """theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  have admissible : problem_spec_getChunksizes
      %s
      (implementation_getChunksizes
        %s) := by
    unfold problem_spec_getChunksizes
    simp +decide [implementation_getChunksizes, Id.run, mergeVars,
      insertChunk, List.lookup]
    rfl
  intro vars""" % (_W_PINNED_INPUT, _W_PINNED_INPUT), 1)
if _ADMISS_PROOF == _GOLD_PROOF:
    raise AssertionError("drift: admissibility anchor not found in proof region")


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- SOUNDNESS POSITIVE ----------------------------------------------
    {
        "id": "pos-control-functional-folds",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_IMPL),
                        _GOLD_PROOF, _POS_PROOF),
        "rationale": (
            "A structurally different but CORRECT implementation: the mutable "
            "accumulator threaded by two nested loops with an early return is "
            "replaced by two purely functional front-recursive folds plus an "
            "`Option`-valued per-entry recorder, with the chunked test written "
            "in the opposite polarity and the agreement test with its operands "
            "swapped. Same decision, same order, same result, no mutable state. "
            "It must satisfy the master clause `result = mergeVars vars []`; if "
            "a faithful correct reshape could not, the spec would be "
            "SPEC-TOO-STRONG. The proof is reauthored for the new shape (the "
            "frozen loop-bridging lemmas are unnecessary once there is no loop, "
            "so they are repurposed at their frozen names — a variant may not "
            "declare a NEW theorem) and closes `correct_getChunksizes` with its "
            "statement byte-identical, no sorry/admit/native_decide and no new "
            "axiom."
        ),
    },

    # --- UNIQUENESS 1: loadability aborts an unchunked variable ----------
    {
        "id": "weak-unloadable-unchunked-aborts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_ABORT_UNCHUNKED),
        "refinement": (
            "This is the ported form of the sibling battery's central attack. Its "
            "faithful real patch decides chunked-ness through the accessor that "
            "returns the variable's in-place contents, which for a variable "
            "holding no in-place handle forces the whole array into memory — so "
            "on a collection backed by an unreachable store the operation aborts "
            "instead of reporting the (empty) mapping. That is precisely the "
            "regression the failing test pins: it asserts the mapping is reported "
            "as empty with no data access at all. Such a patch therefore does NOT "
            "resolve, and a rival that verified here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause `result = mergeVars vars []`: the "
            "reference fold consults only `hasChunks` and `chunksizes`, so the "
            "result is independent of `isDuckArray` and `materializeRaises`. On a "
            "single unchunked variable with no in-place handle whose contents "
            "cannot be loaded the fold yields the empty mapping, whereas this "
            "rival rejects. Witness holds `hasChunks` FALSE, `isDuckArray` FALSE "
            "and `materializeRaises` TRUE — the only point that exercises the "
            "unchunked half of the independence clause."
        ),
        "witness": _witness(_W_UNCHUNKED_UNLOADABLE),
    },

    # --- UNIQUENESS 2: loadability aborts any variable -------------------
    {
        "id": "weak-unloadable-any-aborts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_ABORT_ANY),
        "refinement": (
            "The un-guarded form of the same defect: loadability aborts a CHUNKED "
            "variable too, so a faithful patch would additionally lose "
            "contributions the mapping must contain. It fails the same failing "
            "test as rival 1 (the collection is reported as aborting rather than "
            "as an empty mapping) and, on a lazily-backed chunked collection, "
            "also loses the block lengths the passing chunk tests require — so it "
            "resolves neither."
        ),
        "rationale": (
            "Rejected by the same independence consequence of the master clause, "
            "at a DIFFERENT point: a single CHUNKED variable with no in-place "
            "handle whose contents cannot be loaded. The fold records that "
            "variable's dimension; this rival rejects. Rival 1 is correct at this "
            "point (its abort is guarded by not-chunked), which is exactly what "
            "separates the two, so the witness must be at the chunked point and "
            "not shared. Witness holds `hasChunks` TRUE, `isDuckArray` FALSE, "
            "`materializeRaises` TRUE."
        ),
        "witness": _witness(_W_CHUNKED_UNLOADABLE),
    },

    # --- UNIQUENESS 3: every repeated dimension rejects ------------------
    {
        "id": "weak-agreeing-repeat-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_REJECT_REPEAT),
        "refinement": (
            "A faithful patch dropping the agreement test would reject every "
            "collection in which two variables share a dimension — including the "
            "consistent ones. Ordinary collections share dimensions across "
            "variables with identical block lengths, so the passing chunk tests "
            "(which read the collected mapping off such collections) would raise "
            "instead of returning it; it would NOT resolve."
        ),
        "rationale": (
            "Rejected by the REPEAT consequence of the master clause: the "
            "reference fold leaves the mapping unchanged when a dimension is "
            "re-recorded with the SAME block lengths, and only rejects on "
            "DIFFERENT ones. Witness is a two-variable collection recording the "
            "same dimension twice with equal block lengths — the fold succeeds, "
            "this rival rejects. Distinct from rival 4's point, which this rival "
            "handles correctly."
        ),
        "witness": _witness(_W_AGREEING_REPEAT),
    },

    # --- UNIQUENESS 4: last writer wins ---------------------------------
    {
        "id": "weak-inconsistency-overwritten",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_OVERWRITE),
        "refinement": (
            "The complementary defect: a faithful patch that overwrites instead "
            "of rejecting would report a mapping for a collection whose chunking "
            "genuinely disagrees along a dimension, silently picking one "
            "variable's block lengths. The behavior the repository's own chunk "
            "tests rely on is that such a collection is REJECTED, so the mapping "
            "can be trusted; a patch that returns a made-up mapping there does "
            "NOT resolve them."
        ),
        "rationale": (
            "Rejected by the INCONSISTENCY consequence of the master clause: two "
            "chunked variables recording the same dimension with DIFFERENT block "
            "lengths must make the whole operation reject, whereas this rival "
            "returns the overwritten mapping. Witness varies only the second "
            "variable's block lengths relative to rival 3's point, isolating the "
            "agree/disagree distinction."
        ),
        "witness": _witness(_W_INCONSISTENT),
    },

    # --- UNIQUENESS 5: stop after the first chunked variable ------------
    {
        "id": "weak-first-chunked-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_FIRST_ONLY),
        "refinement": (
            "A faithful patch returning after the first chunked variable would "
            "report a mapping missing every dimension carried only by later "
            "variables. The passing chunk tests compare the collected mapping "
            "against one holding several dimensions contributed by different "
            "variables, so a truncated mapping fails them; it would NOT resolve."
        ),
        "rationale": (
            "Rejected by the TOTALITY consequence of the master clause: the "
            "reference fold threads the accumulator through EVERY variable, so a "
            "collection of two chunked variables carrying distinct dimensions "
            "must record both, whereas this rival records only the first. Witness "
            "holds the collection length at 2 with two distinct dimension names. "
            "Rivals 1-4, 8 and 9 all agree with the fold at this point; rival 6 "
            "also diverges here (it reverses the two recorded dimensions), so "
            "this point separates rival 5 from every rival except 6, and rival "
            "6's own witness (P6, a single variable carrying two dimensions, "
            "where rival 5 is correct) is what separates those two."
        ),
        "witness": _witness(_W_TWO_CHUNKED),
    },

    # --- UNIQUENESS 6: reversed first-seen order ------------------------
    {
        "id": "weak-reversed-first-seen-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_REVERSE_ORDER),
        "refinement": (
            "A NEAR-MISS: prepending rather than appending records exactly the "
            "same dimension/block-length associations, and the mapping the real "
            "code returns compares equal under mapping equality — so a faithful "
            "patch of this shape plausibly still resolves. It is shipped anyway "
            "because it probes an INDEPENDENT top-level consequence of the frozen "
            "spec (dimensions in first-seen order, which the spec pins as an "
            "ordered list rather than as a set of associations) that no other "
            "rival touches, and because a genuinely order-sensitive consumer "
            "downstream of the collected mapping would observe the difference. "
            "Read as a spec-coverage rival: if the spec did NOT pin the order it "
            "would admit this rival, and the omission would be invisible to every "
            "other case here."
        ),
        "rationale": (
            "Rejected by the ORDER consequence of the master clause: the "
            "reference fold appends a newly seen dimension, so its result lists "
            "dimensions in first-seen order, whereas this rival lists them "
            "reversed. Witness is a SINGLE chunked variable carrying TWO "
            "dimensions — a point at which every other rival is correct, and the "
            "only witness here that varies `chunksizes` to length 2."
        ),
        "witness": _witness(_W_TWO_DIMS),
    },

    # --- UNIQUENESS 7: transposed block lengths -------------------------
    {
        "id": "weak-transposed-block-lengths",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_TRANSPOSE_LENGTHS),
        "refinement": (
            "A faithful patch that reordered a dimension's block lengths while "
            "recording them would report a mapping whose keys are right and whose "
            "values are wrong for every dimension split into two or more unequal "
            "blocks — the ordinary case for a chunked variable. The passing chunk "
            "tests compare the reported block lengths against the expected tuple "
            "in order, so it would NOT resolve. It also breaks the inconsistency "
            "rule's premise: two variables exposing the SAME block lengths for a "
            "dimension would still be recorded consistently, but the value handed "
            "to a consumer is not the one the variable exposes."
        ),
        "rationale": (
            "Rejected by the FIDELITY consequence of the master clause: the "
            "reference fold records against each newly seen dimension exactly the "
            "block-length list the variable exposes, so a rival that reverses that "
            "list disagrees as soon as a dimension carries two distinct block "
            "lengths. Witness is one chunked variable whose single dimension "
            "carries two distinct block lengths — the only witness here that "
            "varies a dimension's VALUE rather than the set of dimension names, "
            "and a point at which every other rival agrees with the fold."
        ),
        "witness": _witness(_W_TWO_LENGTHS),
    },

    # --- UNIQUENESS 8: the first variable is skipped --------------------
    {
        "id": "weak-first-variable-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_SKIP_FIRST),
        "refinement": (
            "A faithful patch that passed over the leading variable would report a "
            "mapping missing every dimension that variable alone carries — wrong "
            "for any collection whose first variable is chunked, which the passing "
            "chunk tests exercise directly. It would NOT resolve. Complements "
            "rival 5 at the opposite end of the collection: that one drops the "
            "tail, this one drops the head, and a patch could plausibly do either "
            "while looking like a loop-bounds adjustment."
        ),
        "rationale": (
            "Rejected by the TOTALITY consequence of the master clause read at the "
            "FRONT of the collection: the reference fold threads the accumulator "
            "through every variable including the first. Witness is a SINGLE "
            "chunked, loadable variable, so the fold records its dimension and "
            "this rival reports the empty mapping. That point separates it from "
            "rival 5 (correct on a one-element collection) and from rivals 1 and 2 "
            "(whose abort needs an unloadable variable, which this witness is "
            "not)."
        ),
        "witness": _witness(_W_FIRST_CHUNKED),
    },

    # --- UNIQUENESS 9: a non-chunked variable contributes an entry ------
    {
        "id": "weak-unchunked-contributes-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_UNCHUNKED_CONTRIBUTES),
        "refinement": (
            "A faithful patch that recorded a placeholder for a variable carrying "
            "no chunk metadata would inject a spurious dimension into the reported "
            "mapping. The failing test asserts the mapping for such a collection "
            "is reported as EMPTY, and the passing chunk tests read mappings that "
            "hold only genuinely chunked dimensions, so it resolves neither. Note "
            "this is a different defect from rivals 1 and 2: those let a "
            "non-contributing variable ABORT the operation, this one lets it "
            "CONTRIBUTE."
        ),
        "rationale": (
            "Rejected by the SKIP consequence of the master clause: the reference "
            "fold consults `chunksizes` only when `hasChunks` holds, so a variable "
            "that is not chunked contributes nothing at all and the mapping is "
            "unchanged across it. Witness is a single variable that is not chunked "
            "and IS loadable — deliberately distinct from P1, where the variable "
            "is unloadable, so rivals 1 and 2 are both correct at this point and "
            "the rejection is attributable to the skip clause alone."
        ),
        "witness": _witness(_W_UNCHUNKED_LOADABLE),
    },

    # --- UNIQUENESS 10: a variable's own entries are not cross-checked ---
    {
        "id": "weak-within-variable-unchecked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BODY, _REJ_WITHIN_VAR_UNCHECKED),
        "refinement": (
            "Added by audit. Every other rival here tests the agreement rule "
            "ACROSS variables, so nothing pinned that it also holds WITHIN one: a "
            "faithful patch that collected a variable's newly seen dimensions "
            "into a staging list and merged them only after finishing that "
            "variable would report a mapping holding a dimension twice, with two "
            "different block-length tuples, for a variable whose own chunk "
            "metadata disagrees along that dimension. A consumer reading the "
            "reported mapping by dimension then gets whichever copy it finds "
            "first, and the operation does not raise where it must — so it "
            "resolves neither the failing test's collection nor the passing chunk "
            "tests' consistency guarantee."
        ),
        "rationale": (
            "Rejected by the WITHIN-VARIABLE consequence of the master clause: "
            "the reference fold threads ONE accumulator through the inner fold, "
            "so the second of two entries for the same dimension is looked up "
            "against the first regardless of which variable contributed it. "
            "Witness is a single chunked variable exposing the same dimension "
            "twice with DIFFERENT block lengths — the fold rejects, this rival "
            "returns both entries. Distinct from rival 4's point (P4), where the "
            "disagreement is spread across two variables and which this rival "
            "handles correctly; and at every witness point above this rival "
            "agrees with the fold, since no variable there exposes a dimension "
            "more than once."
        ),
        "witness": _witness(_W_WITHIN_VAR_CONFLICT),
    },

    # --- ADMISSIBILITY: the obligation is satisfiable at the pinned input ---
    {
        "id": "admiss-pinned-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF, _ADMISS_PROOF),
        "rationale": (
            "Added by audit; this lane was previously dropped with the reason "
            "'the frozen obligation has no precondition, so PRECOND-TOO-STRONG "
            "is unreachable'. That is the wrong test on a total carrier. The "
            "obligation IS an unconditional `∀ vars`, so no hypothesis can be "
            "over-strong — but the analogue is the obligation being UNSATISFIABLE "
            "at exactly the input the modeled behaviour is pinned at, and this "
            "case tests that directly: it discharges "
            "`problem_spec_getChunksizes` at the concrete collection holding one "
            "variable that is not chunked, holds no in-place handle, and whose "
            "contents cannot be loaded — BY EVALUATION, as a `have` — before "
            "closing the frozen obligation with its statement byte-identical and "
            "its tactic body verbatim. The impl region is untouched. The `have` "
            "is informative rather than a tautology: audited by control, the same "
            "shape asserting the spec of a WRONG result at that input does NOT "
            "close (`simp` reduces the equation to `False`), so the step really "
            "evaluates the postcondition there. No sorry/admit/native_decide, no "
            "new axiom, no new theorem."
        ),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# The observable properties of each variable are supplied as inputs and the
# accumulation, its agreement test and its rejection rule are all modeled
# structurally, so the proof consumes no opaque callee contract.
AXIOM_TESTS = []
