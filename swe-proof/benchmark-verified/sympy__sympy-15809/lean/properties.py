# properties.py — G-PBT falsification battery for sympy__sympy-15809 (lean).
#
# NOT a Lean file: a manifest the G-PBT gate parses. Each SPEC_TEST is a full
# `Solution.lean` variant built by region surgery that edits ONLY the impl
# region (and, for the positives, TACTIC BODIES inside the proof region — a
# bridging helper's, and for the admissibility case the obligation theorem's own
# body, which a variant may legitimately reprove), so the frozen spec — the
# module docstring, `EVal`, both `problem_spec_*` predicates and both
# `theorem correct_*` STATEMENTS — is byte-identical and `same_spec` holds by
# construction. Every rejection is therefore attributable to the postcondition,
# never to a tampered spec.
#
# Ported from the nagini sibling battery for this instance. The per-case
# correspondence and the omissions are recorded inline at the bottom of this
# file (NAGINI CORRESPONDENCE), so they are readable from the artifact alone.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE
#
# Two independent obligations over the same carrier `EVal` (a finite rational,
# the top element `⊤`, or the bottom element `⊥`), each a reduction of a
# `List EVal` given in call order to a single `Except Unit EVal`:
#
#   correct_min : ∀ args, problem_spec_min args (implementation_min args)
#   correct_max : ∀ args, problem_spec_max args (implementation_max args)
#
# There is NO precondition: both obligations bind `∀ args : List EVal` with no
# hypothesis, so every list of every length is in-domain. Each postcondition is
# an existential over the produced value `v` with four INDEPENDENT top-level
# clauses; the battery attacks each of them separately on each obligation:
#
#   (C-ok)     result = Except.ok v
#              — the reduction is always DEFINED: it produces a value on every
#                collection, and in particular never takes the failure branch.
#   (C-neutral) args = [] → v = <neutral element>
#              — the empty collection reduces to the reduction's neutral element
#                (`⊤` for the minimum, `⊥` for the maximum). THE LOAD-BEARING
#                CLAUSE: it is the behavior the F2P assertions newly demand.
#   (C-bound)  ∀ x ∈ args, v ≤ x        (min)
#              ∀ x ∈ args, x ≤ v        (max)
#              — the value bounds every operand in the declared direction. This
#                is what pins the reduction DIRECTION and forbids any operand
#                from being skipped.
#   (C-attained) args ≠ [] → v ∈ args
#              — on a non-empty collection the bound is ATTAINED: the value is
#                itself one of the operands, so an unattained (merely valid)
#                bound is not an admissible answer.
#
# Only ONE binder is an input: `args`. (`result` is the result position, which
# the obligation instantiates with `implementation_*`, so no case can vary it
# independently.) The reject witnesses accordingly vary `args` over the
# cardinality classes the reduction's control flow distinguishes and over the
# value classes the carrier distinguishes — the empty collection, a singleton,
# a pair, and a pair containing the absorbing element — so no rival can hide
# behind a binder every witness held fixed. The empty collection is additionally
# probed at THREE distinct returned-value classes (the failure branch, the
# opposite extreme, and a finite value), which is what keeps (C-neutral) pinned
# to a value rather than to a class of values.
#
# Note on what the four clauses jointly amount to, since the rationales below
# name them one at a time: together they determine the result UNIQUELY. Any two
# results satisfying `problem_spec_min args` are equal — on the empty collection
# both equal ⊤ by (C-neutral), and otherwise each is a lower bound of the other
# by (C-bound) applied to the other's (C-attained) membership, so antisymmetry of
# the order closes it. (Machine-checked during the audit of this battery, on both
# obligations, over the frozen spec.) That is the strongest statement of
# SPEC-TOO-WEAK's absence available: there is no room for a wrong-but-verifying
# impl of the modeled reduction, because the spec leaves no result free to
# differ. The rivals below are therefore not a sampling of a large space of
# possible wrongness — they are the demonstration that each individual clause is
# load-bearing in that determination, which is what an ablation must show.
#
# Oracle-grounding note: there are no `opaque` callees and no axioms in this
# bundle's carrier at all, so no clause can be discharged by ECHOING an
# answer-key. Every clause is a structural relation between the produced value
# and the input list (membership, order, emptiness), and `EVal` literals are
# fully decidable — which is why every witness below states its refutation at
# CONCRETE inputs and needs no hypothesis binders (and so no consistency
# question arises about them).
#
# ---------------------------------------------------------------------------
# WHY EVERY REJECT CASE CARRIES A WITNESS
#
# On this backend "did not verify" does NOT mean "the spec refutes the impl":
# the frozen tactic script is tuned to the frozen impl's syntactic form, and
# reshaping the impl is exactly what a rival does — so a merely RESHAPED but
# correct impl breaks the build identically to a wrong one. Each reject case
# therefore ships a Lean snippet proving the rival CONTRADICTS the spec at one
# concrete input. Each was built against the rival (must elaborate) and against
# the frozen solution (must fail) before shipping; none uses
# `sorry`/`admit`/`native_decide`, and none introduces a helper of its own.
#
# What makes the gold-side failure ADMISSIBLE evidence here, and not merely an
# exit code: every witness's discriminating step is
# `rw [show implementation_* <input> = <literal> from rfl]`, so on the frozen
# solution it fails with `Type mismatch: rfl has type ?m = ?m but is expected to
# have type implementation_* <input> = <literal>` — an error naming the concrete
# claim. That error TRACKS the claim rather than the file: substituting the frozen
# impl's own value at that input makes the same `rfl` step SUCCEED and the build
# then fails somewhere else entirely, at the refutation (`decide` reporting the
# proposition is false, or `unsolved goals ⊢ False`). Both directions were built
# during the audit of this battery for all twelve original cases. So gold's exit
# code carries information about WHAT is claimed, which is precisely what
# distinguishes a refutation from a witness that merely fails to elaborate.
# Since no witness binds a hypothesis — every one states its refutation at
# literal inputs — no consistency question arises for any of them.

from pathlib import Path

INSTANCE = "sympy__sympy-15809"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it edits and is unique in the
# frozen file, so a change to the frozen solution breaks this manifest loudly
# rather than silently retargeting a swap.
# ---------------------------------------------------------------------------

# The accumulating body of each impl region (the `def` header line is left in
# place, so the swap cannot escape the impl region).
_MIN_BODY = """  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc"""

_MAX_BODY = """  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc"""

# The tactic body of the impl/fold bridging helper inside each proof region.
# Only the POSITIVES touch these (a reshaped impl needs the bridge reproved);
# the `theorem correct_*` statements and bodies are never edited by any case.
_MIN_BRIDGE = """  unfold implementation_min
  simp only [Id.run, bind]
  rw [← min_fold_eq args ⊤]
  rfl"""

_MAX_BRIDGE = """  unfold implementation_max
  simp only [Id.run, bind]
  rw [← max_fold_eq args ⊥]
  rfl"""

for _a in (_MIN_BODY, _MAX_BODY, _MIN_BRIDGE, _MAX_BRIDGE):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift ({_BASE.count(_a)}x): {_a!r}")


# ---------------------------------------------------------------------------
# 1. SOUNDNESS POSITIVE — structurally DIFFERENT, still CORRECT.
#
# The frozen impl seeds the accumulator with the neutral element and folds the
# WHOLE collection. This variant instead case-splits on the collection, seeds
# the accumulator with the FIRST operand, and folds only the remainder — the
# empty collection still yielding the neutral element. Observationally
# identical (the neutral element is absorbed by the reduction), but a different
# executable shape, so the bridging helper is reproved for the new shape while
# `theorem correct_min` / `correct_max` keep their frozen statements AND their
# frozen tactic bodies. MUST verify; if it cannot, the postcondition rejects a
# faithful correct implementation (SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------

_POS_MIN_BODY = """  match args with
  | [] => return Except.ok ⊤
  | a :: rest =>
    let mut acc : EVal := a
    for x in rest do
      acc := min acc x
    return Except.ok acc"""

_POS_MIN_BRIDGE = """  unfold implementation_min
  cases args with
  | nil => rfl
  | cons a as =>
    simp only [Id.run, bind]
    rw [List.foldl_cons, min_top_left]
    rw [← min_fold_eq as a]
    rfl"""

_POS_MAX_BODY = """  match args with
  | [] => return Except.ok ⊥
  | a :: rest =>
    let mut acc : EVal := a
    for x in rest do
      acc := max acc x
    return Except.ok acc"""

_POS_MAX_BRIDGE = """  unfold implementation_max
  cases args with
  | nil => rfl
  | cons a as =>
    simp only [Id.run, bind]
    rw [List.foldl_cons, max_bot_left]
    rw [← max_fold_eq as a]
    rfl"""

_POS = _swap(_BASE, _MIN_BODY, _POS_MIN_BODY)
_POS = _swap(_POS, _MIN_BRIDGE, _POS_MIN_BRIDGE)
_POS = _swap(_POS, _MAX_BODY, _POS_MAX_BODY)
_POS = _swap(_POS, _MAX_BRIDGE, _POS_MAX_BRIDGE)


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY POSITIVE — every input CLASS is in-domain.
#
# The obligations bind `∀ args : List EVal` with no hypothesis, so the claim to
# check is that no input class is excluded. This variant makes the three input
# classes the reduction's documented behavior distinguishes EXPLICIT and
# separate branches — the empty collection, a one-operand collection, and a
# many-operand collection — and proves the obligation for all three. If any
# class were out of domain (or the postcondition inconsistent on it), this
# cannot verify: PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------

_ADM_MIN_BODY = """  match args with
  | [] => return Except.ok ⊤
  | [a] => return Except.ok a
  | a :: rest =>
    let mut acc : EVal := a
    for x in rest do
      acc := min acc x
    return Except.ok acc"""

_ADM_MIN_BRIDGE = """  unfold implementation_min
  cases args with
  | nil => rfl
  | cons a as =>
    cases as with
    | nil =>
      simp only [Id.run, List.foldl_cons, List.foldl_nil, min_top_left]
      rfl
    | cons b bs =>
      simp only [Id.run, bind]
      rw [List.foldl_cons, min_top_left]
      rw [← min_fold_eq (b :: bs) a]
      rfl"""

_ADM_MAX_BODY = """  match args with
  | [] => return Except.ok ⊥
  | [a] => return Except.ok a
  | a :: rest =>
    let mut acc : EVal := a
    for x in rest do
      acc := max acc x
    return Except.ok acc"""

_ADM_MAX_BRIDGE = """  unfold implementation_max
  cases args with
  | nil => rfl
  | cons a as =>
    cases as with
    | nil =>
      simp only [Id.run, List.foldl_cons, List.foldl_nil, max_bot_left]
      rfl
    | cons b bs =>
      simp only [Id.run, bind]
      rw [List.foldl_cons, max_bot_left]
      rw [← max_fold_eq (b :: bs) a]
      rfl"""

_ADM = _swap(_BASE, _MIN_BODY, _ADM_MIN_BODY)
_ADM = _swap(_ADM, _MIN_BRIDGE, _ADM_MIN_BRIDGE)
_ADM = _swap(_ADM, _MAX_BODY, _ADM_MAX_BODY)
_ADM = _swap(_ADM, _MAX_BRIDGE, _ADM_MAX_BRIDGE)

# The branch structure above shows the input classes are all REACHABLE, but on a
# total carrier that alone is weak evidence: `∀ args` quantifies over every list
# whether or not any branch mentions it. What PRECOND-TOO-STRONG looks like here
# is the obligation being UNSATISFIABLE at a concrete input the new behavior
# names — a postcondition whose clauses cannot jointly hold at the argument-free
# call, say, because they demand both the neutral element and membership in an
# empty collection. So each obligation's own tactic body first DISCHARGES the
# postcondition at the concrete inputs the new assertions exercise (the
# argument-free call, a one-operand collection, and a two-operand collection),
# by evaluation, as a `have` — the existential witness supplied explicitly and
# every clause closed at that literal input. A clause set that could not be
# satisfied there makes these `have`s unprovable and the case fails, which is
# exactly the reading PRECOND-TOO-STRONG needs. The `have`s are then `clear`ed
# so nothing downstream can lean on them, and the frozen obligation is closed by
# its own frozen tactic script VERBATIM after `intro args`.
_ADM_MIN_OBLIGATION_HEAD = """theorem correct_min : ∀ args : List EVal,
    problem_spec_min args (implementation_min args) := by
  intro args"""

_ADM_MIN_OBLIGATION_NEW = """theorem correct_min : ∀ args : List EVal,
    problem_spec_min args (implementation_min args) := by
  have h_empty : problem_spec_min ([] : List EVal) (implementation_min []) :=
    ⟨⊤, rfl, fun _ => rfl, by simp, by simp⟩
  have h_one : problem_spec_min [(0 : EVal)] (implementation_min [(0 : EVal)]) :=
    ⟨0, rfl, by simp, by simp, fun _ => by simp⟩
  have h_many : problem_spec_min [(1 : EVal), (0 : EVal)]
      (implementation_min [(1 : EVal), (0 : EVal)]) :=
    ⟨0, rfl, by simp, by simp, fun _ => by simp⟩
  clear h_empty h_one h_many
  intro args"""

_ADM_MAX_OBLIGATION_HEAD = """theorem correct_max : ∀ args : List EVal,
    problem_spec_max args (implementation_max args) := by
  intro args"""

_ADM_MAX_OBLIGATION_NEW = """theorem correct_max : ∀ args : List EVal,
    problem_spec_max args (implementation_max args) := by
  have h_empty : problem_spec_max ([] : List EVal) (implementation_max []) :=
    ⟨⊥, rfl, fun _ => rfl, by simp, by simp⟩
  have h_one : problem_spec_max [(0 : EVal)] (implementation_max [(0 : EVal)]) :=
    ⟨0, rfl, by simp, by simp, fun _ => by simp⟩
  have h_many : problem_spec_max [(0 : EVal), (1 : EVal)]
      (implementation_max [(0 : EVal), (1 : EVal)]) :=
    ⟨1, rfl, by simp, by simp, fun _ => by simp⟩
  clear h_empty h_one h_many
  intro args"""

_ADM = _swap(_ADM, _ADM_MIN_OBLIGATION_HEAD, _ADM_MIN_OBLIGATION_NEW)
_ADM = _swap(_ADM, _ADM_MAX_OBLIGATION_HEAD, _ADM_MAX_OBLIGATION_NEW)


# ---------------------------------------------------------------------------
# 3. RIVALS. Each perturbs exactly ONE impl region and leaves the other, plus
#    both proof regions, byte-identical — so the clause it violates and the
#    obligation it violates it on are both unambiguous.
# ---------------------------------------------------------------------------

# (a) The empty collection takes the FAILURE branch instead of reducing to the
#     neutral element. Attacks (C-ok) at `args = []`.
_MIN_EMPTY_FAIL = """  if args = [] then return Except.error ()
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc"""

_MAX_EMPTY_FAIL = """  if args = [] then return Except.error ()
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc"""

# (b) The empty collection reduces to the reduction's ABSORBING element instead
#     of its neutral element (the two are distinct, and swapped between the two
#     reductions). Attacks (C-neutral) alone at `args = []`: the value is
#     produced, and both remaining clauses are vacuous on the empty collection.
_MIN_EMPTY_ABSORB = """  if args = [] then return Except.ok ⊥
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc"""

_MAX_EMPTY_ABSORB = """  if args = [] then return Except.ok ⊤
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc"""

# (c) EVERY collection takes the failure branch — the reduction is never
#     defined. Attacks (C-ok) on the whole domain, and in particular at a
#     one-operand collection, where the frozen behavior is to return that
#     operand. A strict superset of (a)'s wrongness, so it gets its own witness
#     at an input where (a) is still correct.
_MIN_ALWAYS_FAIL = """  return Except.error ()"""
_MAX_ALWAYS_FAIL = """  return Except.error ()"""

# (d) The absorbing operand is SKIPPED by the accumulation, so a collection
#     containing it reduces to a value that does not bound it. Attacks
#     (C-bound) at a pair containing the absorbing element; (C-attained) still
#     holds (the returned value IS an operand), so the refutation isolates the
#     bound clause.
_MIN_SKIP_ABSORB = """  let mut acc : EVal := ⊤
  for x in args do
    if x ≠ ⊥ then
      acc := min acc x
  return Except.ok acc"""

_MAX_SKIP_ABSORB = """  let mut acc : EVal := ⊥
  for x in args do
    if x ≠ ⊤ then
      acc := max acc x
  return Except.ok acc"""

# (e) The reduction DIRECTION is inverted: the accumulation keeps the operand
#     at the opposite end of the order. Attacks (C-bound) at a two-operand
#     collection; (C-ok), (C-neutral) and (C-attained) all still hold, so the
#     direction clause is isolated.
_MIN_INVERT = """  match args with
  | [] => return Except.ok ⊤
  | a :: rest =>
    let mut acc : EVal := a
    for x in rest do
      acc := max acc x
    return Except.ok acc"""

_MAX_INVERT = """  match args with
  | [] => return Except.ok ⊥
  | a :: rest =>
    let mut acc : EVal := a
    for x in rest do
      acc := min acc x
    return Except.ok acc"""

# (f) A non-empty collection reduces to the reduction's ABSORBING element — a
#     value that genuinely bounds every operand in the required direction but is
#     not one of them. Attacks (C-attained) ALONE: (C-ok) holds, (C-neutral)
#     holds (the empty branch is untouched), and (C-bound) holds because the
#     absorbing element bounds everything. This is the clause that forbids a
#     merely-valid, unattained bound, and nothing else refutes it.
_MIN_UNATTAINED = """  if args = [] then return Except.ok ⊤
  return Except.ok ⊥"""

_MAX_UNATTAINED = """  if args = [] then return Except.ok ⊥
  return Except.ok ⊤"""

# (g) The empty collection reduces to an ORDINARY FINITE value instead of the
#     reduction's neutral element. Attacks (C-neutral) at `args = []` from the
#     INTERIOR of the order rather than from its far end, which is a distinct
#     probe: rivals (b) return the other EXTREME, so a postcondition that merely
#     required the empty result to be *some* extreme element — or that named the
#     neutral element only up to "an element no operand contradicts", which on
#     the empty collection is every element — would still admit this one. Both
#     reductions get the same finite value, so the same rival shape is wrong on
#     each obligation for its own reason.
_MIN_EMPTY_FINITE = """  if args = [] then return Except.ok 0
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc"""

_MAX_EMPTY_FINITE = """  if args = [] then return Except.ok 0
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc"""

# (h) A collection CONTAINING the absorbing element collapses to the reduction's
#     NEUTRAL element instead of to the absorbing one. Attacks (C-bound) at that
#     collection, and it is a genuinely different wrongness from (d): (d) merely
#     SKIPS the absorbing operand and so returns another operand of the
#     collection (leaving (C-attained) true), whereas this rival returns a value
#     that is in the collection at all only by accident — it inverts the
#     collapse, returning the extreme at the WRONG end of the order. The
#     refutation is stated on (C-bound), which both (C-attained) and the skip
#     rival leave untouched at this input.
_MIN_ABSORB_TO_NEUTRAL = """  if (⊥ : EVal) ∈ args then return Except.ok ⊤
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc"""

_MAX_ABSORB_TO_NEUTRAL = """  if (⊤ : EVal) ∈ args then return Except.ok ⊥
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc"""


# ---------------------------------------------------------------------------
# Witness snippets. Each states the spec predicate directly at one concrete
# input and derives a contradiction from the clause named in the rationale. The
# `show <impl> = <literal> from rfl` step is what makes each a DISCRIMINATOR:
# it is `rfl`-true of the rival and false of the frozen solution, so the same
# snippet cannot elaborate against gold.
# ---------------------------------------------------------------------------

_W_MIN_EMPTY_FAIL = """
example : ¬ problem_spec_min [] (implementation_min []) := by
  unfold problem_spec_min
  rw [show implementation_min ([] : List EVal) = Except.error () from rfl]
  simp
"""

_W_MAX_EMPTY_FAIL = """
example : ¬ problem_spec_max [] (implementation_max []) := by
  unfold problem_spec_max
  rw [show implementation_max ([] : List EVal) = Except.error () from rfl]
  simp
"""

_W_MIN_EMPTY_ABSORB = """
example : ¬ problem_spec_min [] (implementation_min []) := by
  rintro ⟨v, hv, hneutral, -, -⟩
  rw [show implementation_min ([] : List EVal) = Except.ok ⊥ from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hneutral rfl) (by decide)
"""

_W_MAX_EMPTY_ABSORB = """
example : ¬ problem_spec_max [] (implementation_max []) := by
  rintro ⟨v, hv, hneutral, -, -⟩
  rw [show implementation_max ([] : List EVal) = Except.ok ⊤ from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hneutral rfl) (by decide)
"""

_W_MIN_ALWAYS_FAIL = """
example : ¬ problem_spec_min [(0 : EVal)] (implementation_min [(0 : EVal)]) := by
  unfold problem_spec_min
  rw [show implementation_min [(0 : EVal)] = Except.error () from rfl]
  simp
"""

_W_MAX_ALWAYS_FAIL = """
example : ¬ problem_spec_max [(0 : EVal)] (implementation_max [(0 : EVal)]) := by
  unfold problem_spec_max
  rw [show implementation_max [(0 : EVal)] = Except.error () from rfl]
  simp
"""

_W_MIN_SKIP_ABSORB = """
example : ¬ problem_spec_min [(⊥ : EVal), (0 : EVal)]
    (implementation_min [(⊥ : EVal), (0 : EVal)]) := by
  rintro ⟨v, hv, -, hbound, -⟩
  rw [show implementation_min [(⊥ : EVal), (0 : EVal)] = Except.ok 0 from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hbound ⊥ (by simp)) (by decide)
"""

_W_MAX_SKIP_ABSORB = """
example : ¬ problem_spec_max [(⊤ : EVal), (0 : EVal)]
    (implementation_max [(⊤ : EVal), (0 : EVal)]) := by
  rintro ⟨v, hv, -, hbound, -⟩
  rw [show implementation_max [(⊤ : EVal), (0 : EVal)] = Except.ok 0 from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hbound ⊤ (by simp)) (by decide)
"""

_W_MIN_INVERT = """
example : ¬ problem_spec_min [(1 : EVal), (0 : EVal)]
    (implementation_min [(1 : EVal), (0 : EVal)]) := by
  rintro ⟨v, hv, -, hbound, -⟩
  rw [show implementation_min [(1 : EVal), (0 : EVal)] = Except.ok 1 from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hbound 0 (by simp)) (by decide)
"""

_W_MAX_INVERT = """
example : ¬ problem_spec_max [(0 : EVal), (1 : EVal)]
    (implementation_max [(0 : EVal), (1 : EVal)]) := by
  rintro ⟨v, hv, -, hbound, -⟩
  rw [show implementation_max [(0 : EVal), (1 : EVal)] = Except.ok 0 from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hbound 1 (by simp)) (by decide)
"""

_W_MIN_UNATTAINED = """
example : ¬ problem_spec_min [(1 : EVal)] (implementation_min [(1 : EVal)]) := by
  rintro ⟨v, hv, -, -, hattained⟩
  rw [show implementation_min [(1 : EVal)] = Except.ok ⊥ from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hattained (by simp)) (by decide)
"""

_W_MAX_UNATTAINED = """
example : ¬ problem_spec_max [(1 : EVal)] (implementation_max [(1 : EVal)]) := by
  rintro ⟨v, hv, -, -, hattained⟩
  rw [show implementation_max [(1 : EVal)] = Except.ok ⊤ from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hattained (by simp)) (by decide)
"""

_W_MIN_EMPTY_FINITE = """
example : ¬ problem_spec_min [] (implementation_min []) := by
  rintro ⟨v, hv, hneutral, -, -⟩
  rw [show implementation_min ([] : List EVal) = Except.ok 0 from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hneutral rfl) (by decide)
"""

_W_MAX_EMPTY_FINITE = """
example : ¬ problem_spec_max [] (implementation_max []) := by
  rintro ⟨v, hv, hneutral, -, -⟩
  rw [show implementation_max ([] : List EVal) = Except.ok 0 from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hneutral rfl) (by decide)
"""

_W_MIN_ABSORB_TO_NEUTRAL = """
example : ¬ problem_spec_min [(⊥ : EVal), (0 : EVal)]
    (implementation_min [(⊥ : EVal), (0 : EVal)]) := by
  rintro ⟨v, hv, -, hbound, -⟩
  rw [show implementation_min [(⊥ : EVal), (0 : EVal)] = Except.ok ⊤ from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hbound ⊥ (by simp)) (by decide)
"""

_W_MAX_ABSORB_TO_NEUTRAL = """
example : ¬ problem_spec_max [(⊤ : EVal), (0 : EVal)]
    (implementation_max [(⊤ : EVal), (0 : EVal)]) := by
  rintro ⟨v, hv, -, hbound, -⟩
  rw [show implementation_max [(⊤ : EVal), (0 : EVal)] = Except.ok ⊥ from rfl] at hv
  injection hv with h
  subst h
  exact absurd (hbound ⊤ (by simp)) (by decide)
"""


# ---------------------------------------------------------------------------
# Shared refinement arguments. Every rival's faithful real counterpart changes
# an OBSERVABLE outcome of the reduction that the F2P assertions pin, so a rival
# that VERIFIED would be a true verify-does-not-imply-resolve break rather than
# an artifact of the model.
# ---------------------------------------------------------------------------

_REF_EMPTY_FAIL = (
    "the faithful real counterpart is a reduction that still rejects the "
    "argument-free call instead of reducing it to the neutral element. That is "
    "precisely the behavior the F2P assertions were added to forbid: they "
    "assert that both argument-free reductions produce their neutral element, "
    "and a rejecting call raises instead of producing anything, so both F2P "
    "tests fail. A verifying rival here would mean the spec does not see the "
    "behavior change at all."
)

_REF_EMPTY_ABSORB = (
    "the faithful real counterpart reduces the argument-free call to the "
    "reduction's ABSORBING element rather than its neutral element — the two "
    "are the opposite ends of the order and are swapped between the two "
    "reductions. The F2P assertions pin the argument-free result of each "
    "reduction to its own neutral element, so each would observe the opposite "
    "extreme and fail. A real patch wiring the argument-free case to the "
    "absorbing element would not resolve."
)

_REF_ALWAYS_FAIL = (
    "the faithful real counterpart rejects EVERY call, not just the "
    "argument-free one — a strict superset of the pre-change defect. Beyond the "
    "new argument-free assertions, every existing assertion about a "
    "one-operand or many-operand reduction would raise instead of producing a "
    "value, so both F2P tests and essentially all the accompanying P2P "
    "assertions fail. A real patch that kept or broadened the rejection would "
    "not resolve."
)

_REF_SKIP_ABSORB = (
    "the faithful real counterpart drops the absorbing operand from the "
    "accumulation, so a collection containing it no longer collapses to it. The "
    "F2P/P2P assertions pin exactly that collapse — a reduction over a "
    "collection containing the absorbing element equals that element — so a "
    "collection mixing it with an ordinary operand would return the ordinary "
    "operand instead and the assertions fail. A real patch skipping the "
    "absorbing operand would not resolve."
)

_REF_INVERT = (
    "the faithful real counterpart accumulates in the opposite order "
    "direction, so a many-operand reduction returns the operand at the wrong "
    "end. The F2P/P2P assertions pin the numeric outcome of many-operand "
    "reductions in both directions, so each would observe the opposite extreme "
    "and fail. A real patch inverting the accumulation would not resolve."
)

_REF_EMPTY_FINITE = (
    "the faithful real counterpart reduces the argument-free call to an "
    "ordinary finite value rather than to the reduction's neutral element. The "
    "F2P assertions pin each argument-free reduction to its own neutral "
    "element — an infinite extreme — so a finite result fails them outright. "
    "This is a distinct real defect from returning the opposite extreme: a "
    "patch that wired the argument-free case to a concrete default operand, "
    "rather than to the reduction's own neutral element, lands here and would "
    "not resolve."
)

_REF_ABSORB_TO_NEUTRAL = (
    "the faithful real counterpart INVERTS the absorbing collapse: a collection "
    "containing the absorbing element returns the reduction's neutral element "
    "instead of collapsing to the absorbing one. The P2P assertions pin that "
    "collapse in both directions over many mixed collections, so a collection "
    "containing the absorbing element would return the opposite extreme and "
    "those assertions fail. Distinct from merely skipping the absorbing "
    "operand, which returns an ordinary operand instead; a real patch that "
    "swapped the short-circuit's return value would not resolve."
)

_REF_UNATTAINED = (
    "the faithful real counterpart returns the reduction's absorbing element "
    "for every non-empty collection: a value that is a valid bound of every "
    "operand but is not one of them. The F2P/P2P assertions pin a one-operand "
    "reduction to that very operand and a many-operand reduction to a numeric "
    "operand of the collection, so every such assertion would observe the "
    "extreme element instead and fail. A real patch returning an unattained "
    "bound would not resolve."
)


SPEC_TESTS = [
    # -------------------------------------------------------------- positives
    {
        "id": "pos-control-head-seeded-reduction",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "structurally-different but CORRECT reduction on BOTH obligations: "
            "instead of seeding the accumulator with the neutral element and "
            "folding the whole collection, it case-splits, seeds with the first "
            "operand and folds the remainder, with the empty collection still "
            "yielding the neutral element. All four clauses of both "
            "postconditions — (C-ok), (C-neutral), (C-bound), (C-attained) — "
            "hold of exactly the same value as the frozen impl, because the "
            "neutral element is absorbed by the reduction. Only the tactic body "
            "of the impl/fold bridging helper is reproved for the new shape; "
            "both `theorem correct_*` statements AND their frozen tactic bodies "
            "are untouched, so what verifies is the frozen obligation itself. "
            "Must verify; if it cannot, the postcondition rejects a faithful "
            "correct implementation (SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-input-classes-explicit",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "both obligations bind `∀ args : List EVal` with NO hypothesis, so "
            "no input is excluded by a guard; on a TOTAL carrier that is not by "
            "itself the admissibility question, because PRECOND-TOO-STRONG "
            "shows up instead as the postcondition being UNSATISFIABLE at a "
            "concrete input the new behavior names — clauses that cannot "
            "jointly hold there, e.g. demanding both a specific value and "
            "membership in an empty collection. This case tests that directly "
            "and at two levels. (i) The impl makes the three classes the "
            "reduction distinguishes into explicit separate branches — the "
            "empty collection, a one-operand collection, and a many-operand "
            "collection — the one-operand branch returning that operand "
            "directly, which is what (C-attained) demands there. (ii) Each "
            "obligation's tactic body then DISCHARGES its own postcondition at "
            "the concrete inputs the new assertions exercise (the "
            "argument-free call, a one-operand collection, a two-operand "
            "collection) by EVALUATION, as a `have` — the existential witness "
            "given explicitly and all four clauses closed at that literal "
            "input — before `clear`ing those facts and closing the frozen "
            "obligation with its frozen script verbatim. If the clause set were "
            "unsatisfiable at any of those inputs, or any class were "
            "out-of-domain, this cannot verify: PRECOND-TOO-STRONG. Note the "
            "empty-collection `have` is the one that matters most: it is the "
            "input whose behavior is new, and (C-neutral) and (C-attained) pull "
            "in opposite directions there — the former names a value, the "
            "latter would demand membership in `[]` if it were not guarded by "
            "`args ≠ []`."
        ),
    },
    # ------------------------------------------------- (C-ok), empty argument
    {
        "id": "weak-min-empty-takes-failure-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_EMPTY_FAIL),
        "rationale": (
            "REJECT comes from (C-ok) `result = Except.ok v` on `correct_min` "
            "at `args = []`: the postcondition asserts a value is produced for "
            "EVERY collection, and this rival takes the failure branch on the "
            "empty one, so no `v` exists to witness the existential. This is the "
            "load-bearing clause pair of the whole bundle — (C-ok) together with "
            "(C-neutral) is what makes the empty collection reduce rather than "
            "fail. If it verifies, the definedness of the empty reduction is "
            "not pinned (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_EMPTY_FAIL,
        "witness": _W_MIN_EMPTY_FAIL,
    },
    {
        "id": "weak-max-empty-takes-failure-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_EMPTY_FAIL),
        "rationale": (
            "the same attack on the OTHER obligation: REJECT comes from (C-ok) "
            "on `correct_max` at `args = []`. The two reductions are "
            "independently observable behaviors with independent obligations, so "
            "a rival that fails the empty case on only one of them must be "
            "caught by that one's postcondition; a battery attacking only the "
            "minimum would leave the maximum's empty case undefended. If it "
            "verifies, the definedness of the empty reduction is not pinned on "
            "this obligation (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_EMPTY_FAIL,
        "witness": _W_MAX_EMPTY_FAIL,
    },
    {
        "id": "weak-min-reject-every-collection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_ALWAYS_FAIL),
        "rationale": (
            "REJECT comes from (C-ok) on `correct_min` across the WHOLE domain, "
            "not only the empty collection. Witnessed at a one-operand "
            "collection — an input where the empty-only rival above is still "
            "correct — so this case demonstrates a strictly larger wrong "
            "sub-domain and does not lean on the other's witness. If it "
            "verifies, the postcondition does not require the reduction to be "
            "defined anywhere (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_ALWAYS_FAIL,
        "witness": _W_MIN_ALWAYS_FAIL,
    },
    {
        "id": "weak-max-reject-every-collection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_ALWAYS_FAIL),
        "rationale": (
            "REJECT comes from (C-ok) on `correct_max` across the whole domain, "
            "witnessed at a one-operand collection. The mirror of the previous "
            "case on the independently-obligated maximum reduction. If it "
            "verifies, definedness is not required anywhere on this obligation "
            "(SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_ALWAYS_FAIL,
        "witness": _W_MAX_ALWAYS_FAIL,
    },
    # -------------------------------------- (C-neutral), the load-bearing fix
    {
        "id": "weak-min-empty-to-absorbing-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_EMPTY_ABSORB),
        "rationale": (
            "REJECT comes from (C-neutral) `args = [] → v = ⊤` on "
            "`correct_min`, and from that clause ALONE: the rival does produce a "
            "value so (C-ok) holds, and on the empty collection both (C-bound) "
            "and (C-attained) are vacuous, so the only clause left to do the "
            "work is the one naming the neutral element. It returns the opposite "
            "end of the order instead. If it verifies, the empty reduction's "
            "VALUE is unpinned even though its definedness is (SPEC-TOO-WEAK) — "
            "the residual hole a definedness-only postcondition would leave."
        ),
        "refinement": _REF_EMPTY_ABSORB,
        "witness": _W_MIN_EMPTY_ABSORB,
    },
    {
        "id": "weak-max-empty-to-absorbing-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_EMPTY_ABSORB),
        "rationale": (
            "REJECT comes from (C-neutral) `args = [] → v = ⊥` on "
            "`correct_max`, and from that clause alone, for the same reason as "
            "its minimum-side twin. Note the two rivals return the SAME carrier "
            "element as each other's frozen answer, so a spec that merely "
            "required 'one of the two extremes' would admit both; each "
            "obligation must name its own neutral element. If it verifies, the "
            "empty reduction's value is unpinned here (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_EMPTY_ABSORB,
        "witness": _W_MAX_EMPTY_ABSORB,
    },
    # ------------------------------------------------------------- (C-bound)
    {
        "id": "weak-min-skip-absorbing-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_SKIP_ABSORB),
        "rationale": (
            "REJECT comes from (C-bound) `∀ x ∈ args, v ≤ x` on `correct_min`: "
            "the rival skips the absorbing operand during accumulation, so on a "
            "collection containing it the result does not bound that operand. "
            "The refutation isolates (C-bound) — the returned value IS an "
            "operand of the collection, so (C-attained) still holds, and the "
            "collection is non-empty so (C-neutral) is vacuous. Probed at a "
            "pair containing the absorbing element, a value class no other "
            "witness reaches. If it verifies, the absorbing operand may be "
            "ignored (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_SKIP_ABSORB,
        "witness": _W_MIN_SKIP_ABSORB,
    },
    {
        "id": "weak-max-skip-absorbing-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_SKIP_ABSORB),
        "rationale": (
            "the mirror on `correct_max`: REJECT comes from (C-bound) "
            "`∀ x ∈ args, x ≤ v`, probed at a pair containing THIS reduction's "
            "absorbing element (the opposite carrier extreme from the "
            "minimum-side twin, so the two witnesses probe genuinely different "
            "inputs). (C-attained) and (C-neutral) still hold, isolating the "
            "bound clause. If it verifies, the absorbing operand may be ignored "
            "on this obligation (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_SKIP_ABSORB,
        "witness": _W_MAX_SKIP_ABSORB,
    },
    {
        "id": "weak-min-invert-reduction-direction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_INVERT),
        "rationale": (
            "REJECT comes from (C-bound) on `correct_min` via the ORDER "
            "DIRECTION rather than via a skipped operand: the rival accumulates "
            "toward the opposite end, so on a two-operand collection it returns "
            "the greater operand. Every other clause survives — a value is "
            "produced, the empty branch is untouched, and the returned value is "
            "an operand — so only the direction of `v ≤ x` refutes it. Probed at "
            "an ordered pair of finite operands, a value class the "
            "absorbing-element witnesses do not reach. If it verifies, the "
            "reduction direction is unpinned (SPEC-TOO-WEAK) and a spec that "
            "confused the two reductions would still pass."
        ),
        "refinement": _REF_INVERT,
        "witness": _W_MIN_INVERT,
    },
    {
        "id": "weak-max-invert-reduction-direction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_INVERT),
        "rationale": (
            "the mirror on `correct_max`: REJECT comes from the direction of "
            "(C-bound) `x ≤ v`, probed at a two-operand collection given in the "
            "OPPOSITE call order from the minimum-side twin (so the two "
            "witnesses differ in the argument order as well as the obligation, "
            "and neither could be satisfied by an order-insensitive accident). "
            "If it verifies, the reduction direction is unpinned here "
            "(SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_INVERT,
        "witness": _W_MAX_INVERT,
    },
    # ---------------------------------------------------------- (C-attained)
    {
        "id": "weak-min-unattained-bound",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_UNATTAINED),
        "rationale": (
            "REJECT comes from (C-attained) `args ≠ [] → v ∈ args` on "
            "`correct_min`, and from that clause ALONE — this is the only rival "
            "that can refute it. The rival returns the absorbing element for "
            "every non-empty collection: a value that is produced (C-ok), leaves "
            "the empty branch correct (C-neutral), and genuinely bounds every "
            "operand (C-bound holds, since the absorbing element is below "
            "everything). Only the attainment requirement rules it out. Probed "
            "at a one-operand collection, where the frozen behavior is to return "
            "that operand. If it verifies, the postcondition accepts a merely "
            "VALID bound instead of the reduced value (SPEC-TOO-WEAK) — the "
            "weakest-plausible-spec hole."
        ),
        "refinement": _REF_UNATTAINED,
        "witness": _W_MIN_UNATTAINED,
    },
    {
        "id": "weak-max-unattained-bound",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_UNATTAINED),
        "rationale": (
            "the mirror on `correct_max`: REJECT comes from (C-attained) alone, "
            "the rival returning this reduction's absorbing element (a genuine "
            "upper bound of everything) for every non-empty collection, so "
            "(C-ok), (C-neutral) and (C-bound) all hold. Probed at a one-operand "
            "collection. If it verifies, this obligation accepts a merely valid "
            "bound in place of the reduced value (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_UNATTAINED,
        "witness": _W_MAX_UNATTAINED,
    },
    # ------------------- (C-neutral) from the INTERIOR of the order, not its end
    {
        "id": "weak-min-empty-to-finite-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_EMPTY_FINITE),
        "rationale": (
            "REJECT comes from (C-neutral) `args = [] → v = ⊤` on `correct_min`, "
            "at the same input as the absorbing-element twin but from a "
            "DIFFERENT value class: an ordinary finite operand rather than the "
            "opposite carrier extreme. That distinction is the point. Every "
            "other empty-collection rival in this battery returns an EXTREME "
            "element, so a postcondition that pinned the empty result only up to "
            "'one of the two extremes' would still reject them all while "
            "admitting this one; and on the empty collection (C-bound) and "
            "(C-attained) are vacuous, so nothing but the clause naming the "
            "neutral element ELEMENT-WISE can do the work. If it verifies, the "
            "empty reduction's value is pinned only to a class, not to a value "
            "(SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_EMPTY_FINITE,
        "witness": _W_MIN_EMPTY_FINITE,
    },
    {
        "id": "weak-max-empty-to-finite-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_EMPTY_FINITE),
        "rationale": (
            "the mirror on `correct_max`: REJECT comes from (C-neutral) "
            "`args = [] → v = ⊥` at a finite value in the order's interior. "
            "Worth having on BOTH obligations even though the rival text is the "
            "same finite value in each: the two obligations name DIFFERENT "
            "neutral elements, so the same returned value is wrong for a "
            "different reason on each, and a battery carrying it on only one "
            "side would leave open that the other obligation's (C-neutral) is "
            "satisfied by any non-extreme value. If it verifies, this "
            "obligation's empty result is not pinned element-wise "
            "(SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_EMPTY_FINITE,
        "witness": _W_MAX_EMPTY_FINITE,
    },
    # -------------- (C-bound) via an INVERTED collapse, not a skipped operand
    {
        "id": "weak-min-absorbing-collapses-to-neutral",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MIN_BODY, _MIN_ABSORB_TO_NEUTRAL),
        "rationale": (
            "REJECT comes from (C-bound) `∀ x ∈ args, v ≤ x` on `correct_min` at "
            "a collection containing the absorbing element, which the rival "
            "collapses to the reduction's NEUTRAL element instead — the extreme "
            "at the wrong end of the order. Distinct from the skip rival at the "
            "same input: that one returns another OPERAND of the collection, so "
            "its result is merely not a bound, while this one returns the "
            "greatest element of the carrier, which fails (C-bound) against "
            "every operand at once and also fails (C-attained) generically. The "
            "refutation is stated on (C-bound), so what the case attests to is "
            "the direction of the collapse rather than attainment. If it "
            "verifies, the absorbing operand's collapse may be inverted "
            "(SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_ABSORB_TO_NEUTRAL,
        "witness": _W_MIN_ABSORB_TO_NEUTRAL,
    },
    {
        "id": "weak-max-absorbing-collapses-to-neutral",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MAX_BODY, _MAX_ABSORB_TO_NEUTRAL),
        "rationale": (
            "the mirror on `correct_max`: REJECT comes from (C-bound) "
            "`∀ x ∈ args, x ≤ v` at a collection containing THIS reduction's "
            "absorbing element, which the rival collapses to this reduction's "
            "neutral element — again the opposite carrier extreme from the "
            "minimum-side twin, so the two witnesses probe genuinely different "
            "inputs. If it verifies, the collapse may be inverted on this "
            "obligation (SPEC-TOO-WEAK)."
        ),
        "refinement": _REF_ABSORB_TO_NEUTRAL,
        "witness": _W_MAX_ABSORB_TO_NEUTRAL,
    },
]


# ---------------------------------------------------------------------------
# NAGINI CORRESPONDENCE — every case of the sibling battery, and where it went.
#
# The nagini model is a SENTINEL model: `lattice_reduce` returns one of four
# pairwise-distinct opaque int sentinels (identity/zero/single/aggregate) chosen
# by three @ContractOnly classifier axioms over the input. This carrier has no
# sentinels and no axioms at all — the reduction is modeled DEEPLY as a fold over
# `WithTop (WithBot ℚ)` — so a nagini clause that pins "which sentinel" maps to a
# clause pinning "which VALUE", and the branch a sentinel stood for becomes a
# concrete input class. That is a strengthening, not a loss: a value-level rival
# can be wrong in ways a four-way sentinel choice cannot express, which is what
# the direction/attainment/finite-value rivals here exploit.
#
#   pos-control-branch-reorder      -> pos-control-head-seeded-reduction.
#       Same intent (reshape the executable form, keep behavior). The nagini
#       reshape reorders branches over an opaque count; the analogue here reseeds
#       the fold from the first operand, which is the shape change this carrier
#       makes available and it additionally forces the impl/fold bridge to be
#       REPROVED — a stronger positive than a branch permutation.
#
#   admiss-f2p-shaped               -> admiss-input-classes-explicit.
#       Nagini's version asserts a 1/4 read share is derivable from the 1/2 held.
#       Permissions do not exist on a referentially transparent carrier, so that
#       exact assertion is inexpressible; the ADMISSIBILITY QUESTION is not. It
#       is re-landed as satisfiability of the postcondition at the concrete
#       F2P-shaped inputs, discharged by evaluation inside each obligation's own
#       tactic body. See that case's rationale.
#
#   frame-mutate-readonly-operands  -> DROPPED, inexpressible.
#       The rejection there comes from the PERMISSION SYSTEM: `operands[0] = zero`
#       needs full permission and only 1/2 is held. Lean has no fractional
#       permissions and no mutable aliasing — `args : List EVal` is an immutable
#       value, a rebinding inside `Id.run do` cannot be observed by the caller,
#       and there is consequently no impl expressible on this carrier that
#       mutates its input. The distinction the case tests does not exist here;
#       this is a carrier collapse, demonstrated by the type, not a hard proof.
#       The frame concern it stands for is discharged structurally instead: every
#       clause of both postconditions relates `v` to `args` by membership or
#       order, so there is no unconstrained output component for a rival to fill.
#
#   weak-drop-noncomparable-raise   -> DROPPED, inexpressible on this carrier.
#       (P-oblig) obligates the raise on a non-comparable collection. Non-
#       comparable operands are OUT OF MODEL SCOPE by construction (mapping.md:
#       the model covers the comparable-argument case; `EVal` is a linear order,
#       so every value it can hold is comparable with every other). There is no
#       inhabitant of `List EVal` at which the dropped raise is observable, so no
#       witness can discriminate. This is a documented scope boundary of the
#       FROZEN model, recorded here rather than silently dropped; the definedness
#       clause (C-ok) is still attacked, by the two failure-branch rival pairs.
#
#   weak-empty-to-zero              -> weak-{min,max}-empty-to-absorbing-element.
#       Direct port: "empty yields the annihilator" becomes "the empty collection
#       yields the absorbing element". Landed on BOTH obligations, where nagini
#       had one, because the two reductions have independent obligations here.
#
#   weak-empty-to-single            -> weak-{min,max}-empty-to-finite-value.
#       `single` is an opaque sentinel standing for "a concrete survivor"; the
#       value-level analogue of returning a survivor on a collection that has
#       none is returning an ordinary finite value, which is what these cases do.
#       ADDED BY AUDIT — the initial port dropped it, and it is not redundant:
#       it is the only probe of (C-neutral) from the order's interior rather than
#       from its opposite extreme.
#
#   weak-absorbing-to-identity      -> weak-{min,max}-absorbing-collapses-to-neutral.
#       Direct port: the absorbing branch returning the identity element becomes
#       a collection containing the absorbing element collapsing to the neutral
#       one. ADDED BY AUDIT — the initial port covered the absorbing operand only
#       via the SKIP rival, which is a different wrongness (skipping returns
#       another operand of the collection; this inverts the collapse).
#
#   weak-swap-single-aggregate      -> weak-{min,max}-unattained-bound
#                                      + weak-{min,max}-invert-reduction-direction.
#       The swapped survivor branches pin "a one-operand collection returns that
#       operand" and "a many-operand collection returns the reduced value". Both
#       halves are value-level here rather than sentinel-level: the first is
#       exactly what the unattained-bound rivals violate at a one-operand
#       collection, the second what the direction rivals violate at a pair. The
#       sentinel `aggregate` (an unevaluated Min/Max OBJECT) has no counterpart
#       on this carrier — the fold always produces a value — so the case splits
#       rather than transfers.
#
#   weak-over-raise-on-comparable   -> weak-{min,max}-reject-every-collection.
#       Direct port: raise unconditionally becomes take the failure branch on
#       every collection, witnessed at a one-operand collection.
#
#   AXIOM_TESTS (4 cases)           -> not applicable, and not silently absent.
#       All four probe @ContractOnly classifier axioms. This bundle declares NO
#       axioms and NO opaque callees (meta.json `axioms: []`, `opaque_callees:
#       []`): the reduction is modeled deeply, so there is nothing to consume as
#       an axiom and no answer-key an impl could echo. The faithfulness check the
#       axiom lane carries on the nagini side is carried here by G-CONF, which
#       differential-tests the fold against the real reduction over comparable
#       inputs (mapping.md, seed 15809). Nothing to port.
