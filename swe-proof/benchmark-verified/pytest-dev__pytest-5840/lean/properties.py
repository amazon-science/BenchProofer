# properties.py — G-PBT falsification battery (spec lane) for
# pytest-dev__pytest-5840, PORTED to the `lean` bundle.
#
# NOT a solution module; a record of adversarially-reasoned cases the G-PBT gate
# executes. Every SPEC_TESTS case is a FULL Solution.lean variant that shares the
# frozen spec byte-identically — region surgery edits ONLY the impl body (and,
# where a correct positive needs it, the proof tactic body). same_spec therefore
# holds by construction and any rejection is attributable to the postcondition,
# not to a tampered spec.
#
# ------------------------------------------------------------------------------
# Defended surface (read from Solution.lean + mapping.md + instance.json):
#
#   problem_spec_cacheKey (resolved : List Char) (result : List Char) : Prop :=
#       result = resolved
#
#   implementation_cacheKey (resolved : List Char) : List Char
#
#   theorem correct_cacheKey :
#       ∀ (resolved : List Char),
#         problem_spec_cacheKey resolved (implementation_cacheKey resolved)
#
# The obligation pins ONE top-level clause: the derived key equals the input
# path character-for-character — the identity on `resolved`, letter case
# retained. Its single input binder is `resolved`. The load-bearing content is
# that the transformation is EXACTLY the identity: any transform that alters even
# one character (a case fold, a reorder, a drop) on some input violates the
# clause. There is no precondition — the obligation quantifies over every
# `resolved` unconditionally.
#
# ------------------------------------------------------------------------------
# Carrier note vs the nagini sibling.
#
# The nagini design document models this behavior with an UNFORGEABLE capability
# token: the key-value string is identical across the two rival conventions, and
# only an abstract predicate (granted solely by the recognised constructor)
# separates them. That is nagini's answer to a change with "no value-level
# discriminator" — it manufactures one out of a fractional-permission predicate.
#
# This lean bundle models the SAME behavior with a genuine VALUE-level
# discriminator instead: the resolved path is a `List Char`, and the changed
# transformation is a per-character map. The pre-change behavior folds letter
# case; the post-change behavior is the identity. The two DISAGREE on any path
# carrying an upper-case letter — the configuration the reported failure
# describes (a path "converted to lower case", breaking a qualified name whose
# package segment contains upper-case). So on this carrier the discriminator is a
# concrete character, not an abstract token, and the reject witnesses can exhibit
# it at literal inputs.
#
# ACCURACY NOTE on which harness tests pin the case sub-domain (measured, not
# assumed — an earlier revision of this file overclaimed here). The two
# FAIL_TO_PASS tests are parameterized on all-lower-case subdirectory names and
# run under an all-lower-case temporary directory, so the resolved paths they
# exercise carry NO upper-case character. On those inputs a pure case fold is
# POINTWISE EQUAL to the identity, and the recomputed-key lookup those tests
# perform therefore succeeds under a folding key exactly as it does under gold.
# The upper-case scenario from the issue is exercised by a separate casing test,
# which this harness counts in its PASS_TO_PASS set (and which is skipped
# outright on case-sensitive file systems). So the case sub-domain is pinned by
# the ISSUE plus that P2P casing test — NOT by the F2P pair. Per-case
# `refinement` prose below is stated against the sub-domain each rival actually
# corrupts, and only the order-reversal rival claims an F2P consequence (that one
# was measured to hold: a reordered key misses the recomputed-key lookup on both
# F2P parameters).
#
# Consequences for the port (detailed per-case and in the submit `assessment`):
#   * the nagini "unrecognised-convention echo" rival ports to the case-FOLD
#     rival (this bundle's prepatch), refuted at an upper-case input;
#   * the nagini "partial-domain" rival ports to a fold applied on a value
#     sub-domain and the identity elsewhere;
#   * the nagini "value-launder" rival (return a value-equal copy that lacks the
#     token) is VACUOUS here: this spec is a pure value equality with no
#     capability token, so a value-equal copy SATISFIES it — there is nothing to
#     launder and no discriminating witness exists. Dropped; DEMONSTRATED, not
#     asserted: a variant that rebuilds the key as a fresh cons-by-cons copy of
#     the input (`resolved.foldr (fun c acc => c :: acc) []`) and returns the copy
#     VERIFIES against the frozen spec (built: exit 0). A laundered copy is
#     accepted, so no witness could refute it and the case has no content here;
#   * the nagini "frame-mutation" rival is VACUOUS here: Lean is referentially
#     transparent, there is no aliasable input to overwrite, so the mutation
#     cheat has no expression. Dropped; DEMONSTRATED: the strongest mutation this
#     carrier expresses is a `let mut` local seeded from the input — writing it
#     and then restoring it VERIFIES (built: exit 0), because the write is
#     invisible to the caller's value. A `let mut` shadow of the input binder
#     that keeps the corrupting write is rejected, but that is just the case-fold
#     rival (A) re-spelled through a mutable local: same refutation point, no new
#     content. Neither spelling adds a discriminator;
#   * the nagini "admissibility" case tests that the half-permission precondition
#     admits an F2P-shaped input. A SECOND audit pass RESTORED it as
#     `admissibility-ground-f2p-shaped`. The port's stated reason for dropping it
#     ("this obligation has no precondition, so PRECOND-TOO-STRONG is
#     unreachable") is NOT a sufficient reason: on a total carrier the analogue of
#     PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, which a positive that discharges the obligation at that
#     concrete input BY EVALUATION — as a `have`, before closing the frozen
#     obligation verbatim — tests directly. Measured: the restored case verifies
#     (exit 0) and its ground `have`s are load-bearing, failing against all three
#     value rivals (exit 1 each, with `decide` refuting the concrete evaluation
#     rather than merely the trailing `rfl`);
#   * the nagini "pos-control-branch-reshape" positive was dropped by the port
#     WITHOUT being recorded as an omission. It is fully expressible here and has
#     been RESTORED by audit as `soundness-branch-reshape`: an always-true guard
#     whose both arms return the path verbatim. It is not redundant with the two
#     existing positives — those reshape the data path, this one adds control
#     flow, and the `if` blocks definitional unfolding so the frozen `rfl` no
#     longer closes.
#
# A third reject rival (order reversal) is added — not a nagini port but coverage
# of the modeled surface: it is refuted at a lower-case, non-palindromic input,
# where the fold rivals AGREE with gold and would not be caught. It therefore
# probes the binder `resolved` at an input point the fold rivals cannot, keeping
# the reject lane from discriminating only upper-case paths. A fourth
# (`uniqueness-empty-path-sub-domain`) is added by audit to restore the nagini
# partial-domain rival's actual sub-domain, the empty path, which no other case
# in the battery reaches.
#
# LANE COMPLETENESS. All three kind lanes are now represented: `uniqueness` (4
# rivals, at four genuinely distinct discriminating points — measured, see the
# cross-witness matrix note below), `soundness` (3 correct reshapes: data-path
# inline, data-path map, control-flow branch), and `admissibility` (1 ground
# satisfiability positive, restored by a second audit pass). Dropping the third
# lane removes one of the three directions this gate exists to test, and the
# coverage reporter flags its absence as a finding.
#
# CROSS-WITNESS MATRIX (measured, all 16 builds, one per rival x point). Each
# rival is refuted at its OWN witness point and at no other case's point, which
# is what makes the four reject cases four cases rather than four spellings of
# one. Rows are rivals, columns the four witness points; 0 = the witness
# elaborates (rival refuted there), 1 = it does not:
#              ['A']  ['A','B']  ['a','b']  []
#   fold          0        0          1      1
#   partial       1        0          1      1
#   reverse       1        0          0      1
#   empty         1        1          1      0
# Note the ['A','B'] column: three rivals are refuted there, so that point alone
# would NOT separate them — the separating points are ['A'] (fold only, since the
# partial rival's own branch exempts length-1), ['a','b'] (reverse only, where
# both fold rivals agree with gold) and [] (empty only). The battery's four
# points are therefore meaningfully distinct, not two spellings of one.
#
# SPEC STRENGTH, re-measured independently by a second audit pass (attacks D/E).
# Six NEW wrong impls the battery does not contain were all REJECTED by the
# frozen spec, each with a witness that elaborates against it (exit 0) and fails
# on gold (exit 1): drop the last character; duplicate the path; upper-case only
# the head character; strip a separator character; fold only paths of length >= 3;
# and map every digit to '0'. Five NEW correct reshapes were all ACCEPTED (exit
# 0): `filter (fun _ => true)`, an `isEmpty` guard with both arms the identity,
# `foldl (acc ++ [c]) []`, and `map (fun c => Char.ofNat c.toNat)`. So the spec is
# neither too weak nor too strong on the surface probed here; no spec hole was
# found and nothing is escalated.
#
# WITNESS ADMISSIBILITY, re-derived (the forgery test). Every reject case's
# gold-side failure was confirmed to CARRY INFORMATION ABOUT THE CLAIM rather
# than to be a syntactic artifact: for each case a second file differing from the
# witness ONLY in what it claims (the leading `¬` dropped, so it asserts the impl
# is CORRECT at that point) was built against both sides. Against the frozen
# solution the flipped claim ELABORATES (exit 0) — gold really does satisfy the
# spec there — and against the rival it FAILS (exit 1) with `decide` refuting the
# flipped proposition. The gold-side error text also changes with the claim
# (`¬(have key := ['A']; pure key).run = ['A']` vs the rival's
# `(have key := List.map Char.toLower ['A']; pure key).run = ['A']`), so each
# exit code is a semantic refutation of the concrete claim and not a stuck
# reduction, unknown identifier, or type error.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-5840"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()

# The exact gold impl body (between the impl markers). Every rival / positive
# rewrites ONLY this block, so same_spec is guaranteed.
_GOLD_IMPL = """  -- The cache key is the resolved path used as-is, preserving its letter case.
  let key := resolved
  return key"""

# The exact gold proof tactic body (between the proof markers). The `theorem
# correct_cacheKey` STATEMENT above it is never touched — only this body may
# differ, and only for a positive whose reshaped impl needs a matching script.
_GOLD_PROOF = """  intro resolved
  rfl"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body, new_proof=None):
    """Full Solution.lean with the impl body replaced by `new_body` (and, if
    given, the proof tactic body replaced by `new_proof`). Spec, theorem
    statement, and all marker regions are otherwise untouched."""
    src = _swap(_BASE, _GOLD_IMPL, new_body)
    if new_proof is not None:
        src = _swap(src, _GOLD_PROOF, new_proof)
    return src


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS (expect="reject") — each carries a discriminating witness.
# ---------------------------------------------------------------------------

# (A) CASE-FOLD rival — the central uniqueness attack, this bundle's prepatch.
# Derive the key by folding every character to lower case instead of returning
# the resolved path verbatim. On any lower-case-only path the fold agrees with
# the identity, so it is INDISTINGUISHABLE by value there; on a path carrying an
# upper-case letter it produces a different key. This is the nagini
# "unrecognised-convention echo" ported to the value carrier: the location
# STRING is the same on the lower-case sub-domain, yet the transformation is
# wrong on the upper-case sub-domain the issue reports (and the harness's
# upper-case casing test, a PASS_TO_PASS entry here, exercises).
_IMPL_FOLD = """  -- rival: fold the resolved path to lower case before using it as the key.
  let key := resolved.map Char.toLower
  return key"""

# (B) PARTIAL-DOMAIN fold — the recognised (identity) behavior on part of the
# value domain, the case fold elsewhere. Branch on the path length: paths of
# length >= 2 fall to the fold, shorter ones stay the identity. The identity
# clause must hold for EVERY input; on the length->=2, upper-case sub-domain the
# result is folded and the clause fails. Ported from the nagini partial-domain
# rival (there pinned to the empty-location sub-domain; here to a length-driven
# value sub-domain, the analogue on this carrier).
_IMPL_PARTIAL = """  -- rival: identity on short paths, but fold longer ones to lower case.
  let key := if resolved.length ≥ 2 then resolved.map Char.toLower else resolved
  return key"""

# (C) ORDER-REVERSAL — not a nagini port; coverage of the modeled surface. The
# key is the resolved path reversed. This attacks the identity clause on its
# ORDER content rather than its case content, so it is refutable at a lower-case
# input (where the two fold rivals agree with gold and are NOT caught). Probes
# the binder `resolved` at an input point neither fold rival can, so the reject
# lane discriminates more than just upper-case paths.
_IMPL_REVERSE = """  -- rival: return the resolved path reversed rather than verbatim.
  let key := resolved.reverse
  return key"""

# (C2) EMPTY-PATH SUB-DOMAIN — added by audit. The nagini partial-domain rival is
# pinned to the EMPTY-location sub-domain; the port moved it to a length-driven
# sub-domain (B) instead, which measured out to coincide with the plain fold (A)
# on every path longer than one character, and left the empty path unprobed by
# any case in the battery. This restores the nagini sub-domain faithfully: the
# identity everywhere EXCEPT the empty path, where a placeholder key is
# substituted. It is refutable ONLY at `[]` — a point at which all three rivals
# above agree with gold — so it is the case that pins the clause at the boundary
# of the binder's domain rather than in its interior.
_IMPL_EMPTY = """  -- rival: identity on non-empty paths, a placeholder key on the empty path.
  let key := if resolved.isEmpty then ['x'] else resolved
  return key"""


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVES (expect="verify") — structurally different, still correct.
# ---------------------------------------------------------------------------

# (D) INLINE — drop the intermediate `key` local and return `resolved` directly.
# Semantically identical to the gold; the gold `rfl` proof still closes, so it
# MUST verify (else SPEC-TOO-STRONG / over-fitted to the two-line gold shape).
_IMPL_POS_INLINE = """  -- positive: inline the identity, no intermediate local.
  return resolved"""

# (E) MAP-IDENTITY — build the key with an explicit `List.map id`, an equivalent
# form of the identity that is SYNTACTICALLY different (it goes through a map,
# like the fold rival, but with the identity function). The proof needs
# `List.map_id` to discharge, so the tactic body is swapped accordingly — the
# theorem STATEMENT is byte-identical. MUST verify: a correct impl of the modeled
# behavior in a different shape, closed honestly with no new lemma / no sorry.
_IMPL_POS_MAPID = """  -- positive: the identity expressed as a map of the identity function.
  let key := resolved.map id
  return key"""
_PROOF_POS_MAPID = """  intro resolved
  simp [problem_spec_cacheKey, implementation_cacheKey, List.map_id]"""

# (F) BRANCH-RESHAPE — added by audit; the port of the nagini
# "pos-control-branch-reshape" positive, which the port dropped without recording
# it as an omission. An always-true guard whose BOTH arms are the identity. This
# is the positive that specifically guards against a spec/proof over-fitted to a
# straight-line impl: the impl now has a branch the gold does not, and the
# obligation must still close. Needs a `simp` body rather than the gold `rfl`
# because the `if` blocks definitional unfolding, so it also demonstrates the
# spec accepts a reshape whose proof is NOT the frozen script.
_IMPL_POS_BRANCH = """  -- positive: branch-reshape; every arm returns the path verbatim.
  let key := if resolved.length ≥ 0 then resolved else resolved
  return key"""
_PROOF_POS_BRANCH = """  intro resolved
  simp [problem_spec_cacheKey, implementation_cacheKey]"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY (expect="verify") — added by a second audit pass. The lane the
# port dropped, and the only detector of PRECOND-TOO-STRONG.
#
# The frozen obligation is unconditional (`∀ (resolved : List Char), ...` with no
# hypothesis), so there is no precondition binder to weaken. That does NOT make
# the lane vacuous: the analogue on a total carrier is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input — an obligation can be
# unfalsifiable-but-also-unwitnessable if the modeled behavior cannot actually be
# EVALUATED at a normal input. So the case discharges the spec predicate at
# concrete, F2P-shaped and issue-shaped ground inputs by evaluation (`decide`) as
# `have`s, and only then closes the frozen obligation verbatim. Nothing is
# assumed: no new declaration, no sorry, statement byte-identical, and the frozen
# tactic body is kept intact as the final two lines.
#
# The three ground points, and why each is there:
#   ['t','e','s','t'] — the shape of the FAIL_TO_PASS parameters (all lower-case),
#       so the admission is pinned at the inputs the harness's F2P pair exercises;
#   ['F','o','o']     — the issue-shaped mixed-case path, the sub-domain the
#       modeled clause is actually about, discharged both as an evaluation and as
#       the spec predicate itself;
#   []                — the boundary point of the binder's domain.
#
# MEASURED LOAD-BEARING (this is what keeps it from being a restatement of the
# frozen proof): carried against each of the three value rivals the module FAILS
# at the ground `have`s themselves, with `decide` refuting the concrete
# evaluation — not merely at the trailing `rfl`. Against the fold rival the
# ['F','o','o'] evaluation and the `_ground` predicate both refute; against the
# reversal rival the ['t','e','s','t'] and ['F','o','o'] evaluations both refute;
# against the empty-path rival the `[]` boundary evaluation refutes. So the
# ground instances genuinely test satisfiability at those points rather than
# riding on the frozen script.
_PROOF_ADMISS = """  have _f2p : implementation_cacheKey ['t', 'e', 's', 't'] = ['t', 'e', 's', 't'] := by decide
  have _mixed : implementation_cacheKey ['F', 'o', 'o'] = ['F', 'o', 'o'] := by decide
  have _boundary : implementation_cacheKey ([] : List Char) = [] := by decide
  have _ground : problem_spec_cacheKey ['F', 'o', 'o']
      (implementation_cacheKey ['F', 'o', 'o']) := by
    unfold problem_spec_cacheKey
    decide
  intro resolved
  rfl"""


# ---------------------------------------------------------------------------
# WITNESSES — each SEEN to elaborate against the rival and fail on gold, in a
# file with the proof obligation removed (verified with scripts/lean_verify.sh).
# ---------------------------------------------------------------------------

# Refutes the fold rival at the single upper-case character 'A': the fold yields
# ['a'] != ['A'] = resolved, so the spec predicate is false of the rival; gold
# returns ['A'] and satisfies it, so the witness fails on gold.
_W_FOLD = """example : ¬ problem_spec_cacheKey ['A'] (implementation_cacheKey ['A']) := by
  unfold problem_spec_cacheKey implementation_cacheKey
  decide"""

# Refutes the partial-domain rival at ['A','B'] (length 2, upper-case): the rival
# takes the fold branch and yields ['a','b'] != ['A','B']; gold is the identity.
# A length-2 point is required — a length-1 upper-case input would fall to the
# identity branch and NOT discriminate this rival.
_W_PARTIAL = """example : ¬ problem_spec_cacheKey ['A', 'B'] (implementation_cacheKey ['A', 'B']) := by
  unfold problem_spec_cacheKey implementation_cacheKey
  decide"""

# Refutes the reversal rival at the lower-case, non-palindromic ['a','b']:
# reversed is ['b','a'] != ['a','b']. Lower-case on purpose — it shows the reject
# lane bites on a path where BOTH fold rivals agree with gold, so this witness
# probes a genuinely different sub-domain of the binder `resolved`.
_W_REVERSE = """example : ¬ problem_spec_cacheKey ['a', 'b'] (implementation_cacheKey ['a', 'b']) := by
  unfold problem_spec_cacheKey implementation_cacheKey
  decide"""

# Refutes the empty-path rival at `[]`: the rival substitutes ['x'] there while
# gold returns []. The ONLY input that discriminates this rival — every other
# path takes its identity branch — and an input at which all three rivals above
# agree with gold, so this witness reaches the one boundary point of the binder
# `resolved` that the rest of the lane leaves untouched. The type ascription is
# required: a bare `[]` has no inferable element type at this position.
_W_EMPTY = """example : ¬ problem_spec_cacheKey ([] : List Char) (implementation_cacheKey ([] : List Char)) := by
  unfold problem_spec_cacheKey implementation_cacheKey
  decide"""


SPEC_TESTS = [
    {
        "id": "uniqueness-case-fold-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_FOLD),
        "rationale": (
            "Attacks the sole postcondition clause (result = resolved) on its "
            "letter-case content, via the input binder `resolved`. The rival "
            "folds every character to lower case, so on any path carrying an "
            "upper-case letter the derived key differs from the resolved path "
            "and the clause fails. Agrees with the identity on lower-case-only "
            "paths, so value equality is NOT the discriminator — the exact "
            "transformation is."),
        "refinement": (
            "The faithful real patch of this rival is the UNCHANGED key "
            "derivation: it canonicalizes the path and then applies the "
            "platform case-normalization, which on a case-insensitive "
            "(case-preserving) file system folds the result to lower case. A "
            "loaded hook module is stored under the derived key and later looked "
            "up with an independently-recomputed key that PRESERVES the path's "
            "true on-disk casing; on a path with an upper-case package segment "
            "the folded key no longer matches, the lookup misses, and the "
            "qualified name is derived from a lower-cased path — the exact "
            "import failure the issue reports. MEASURED SCOPE (do not overstate "
            "this): the resolved paths the two FAIL_TO_PASS parameters exercise "
            "are entirely lower-case, so the fold is pointwise equal to the "
            "identity there and those two tests pass under this rival. The test "
            "this rival actually leaves red is the harness's upper-case casing "
            "test, which this instance counts in PASS_TO_PASS — so the break is "
            "a P2P regression on the very scenario the issue reports, not an F2P "
            "failure. The rival is still genuinely WRONG (it corrupts the key on "
            "every path bearing an upper-case letter, which is the behavior the "
            "issue is about and the clause the spec pins), and it is still this "
            "bundle's prepatch; only the which-test bookkeeping is corrected."),
        "witness": _W_FOLD,
    },
    {
        "id": "uniqueness-partial-domain-fold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PARTIAL),
        "rationale": (
            "Attacks the same clause on a value SUB-DOMAIN via `resolved`: the "
            "identity on short paths, the case fold on paths of length >= 2. The "
            "clause must hold for EVERY input; on the length->=2, upper-case "
            "sub-domain the folded key differs from the resolved path, so the "
            "obligation cannot hold. Ports the nagini partial-domain rival "
            "(there the empty-location sub-domain) to a length-driven value "
            "sub-domain, the analogue on this carrier."),
        "refinement": (
            "Faithful real patch: preserve the resolved path's casing for most "
            "paths but re-apply the platform case fold on a sub-domain (e.g. "
            "longer paths). The cache key for that sub-domain is then the "
            "lower-cased string, so a recomputed-key lookup misses there and the "
            "hook file is re-imported under a lower-cased qualified name the "
            "import machinery rejects. MEASURED SCOPE (same correction as case "
            "A): every real path is longer than one character, so this rival "
            "coincides with the plain case fold on all realistic input — it is "
            "refuted only where the fold is, i.e. on paths bearing an upper-case "
            "letter. Those are not the FAIL_TO_PASS inputs (whose resolved paths "
            "are all lower-case and which therefore pass under this rival); the "
            "test it leaves red is the harness's upper-case casing test, counted "
            "in PASS_TO_PASS. The rival is genuinely wrong on that sub-domain, "
            "which is what the clause forbids. Its distinct CONTENT versus case A "
            "is the branch: the identity clause is universally quantified, so a "
            "transform correct on part of the domain and corrupting elsewhere "
            "must still be rejected — verified below at a length-2 point, where "
            "a length-1 upper-case point provably does NOT discriminate it."),
        "witness": _W_PARTIAL,
    },
    {
        "id": "uniqueness-order-reversal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_REVERSE),
        "rationale": (
            "Attacks the identity clause on its ORDER content rather than its "
            "case content, via `resolved`. The rival reverses the path, so on "
            "any non-palindromic path the key differs from the resolved path. "
            "Refuted at a LOWER-CASE input, where both fold rivals agree with "
            "gold and are not caught — so this rival exercises a different "
            "sub-domain of the binder and keeps the reject lane from testing "
            "only the upper-case discriminator."),
        "refinement": (
            "Faithful real patch: derive the key from the resolved path under a "
            "transformation that reorders its characters (any non-identity "
            "permutation of the path string). The stored key then bears no "
            "resemblance to the path the F2P test recomputes, so every "
            "recomputed-key lookup misses and the hook-module cache never hits — "
            "the membership assertion fails and the qualified name derived from "
            "the mangled path is wrong. It does not resolve. This F2P claim was "
            "MEASURED against the real recomputed-key membership on both "
            "FAIL_TO_PASS parameters: a reordered key misses on each, so unlike "
            "the case-content rivals above this rival really does leave the F2P "
            "pair red. That is exactly why it belongs in the lane — it is the "
            "reject case whose refutation point lies inside the F2P inputs."),
        "witness": _W_REVERSE,
    },
    {
        "id": "uniqueness-empty-path-sub-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_EMPTY),
        "rationale": (
            "Added by audit. Attacks the identity clause at the BOUNDARY of the "
            "binder `resolved` rather than in its interior: the rival is the "
            "identity on every non-empty path and substitutes a placeholder key "
            "on the empty one. The clause is universally quantified with no "
            "precondition, so a single corrupted point refutes it. This is the "
            "faithful port of the nagini partial-domain rival, which is pinned to "
            "the EMPTY-location sub-domain; the existing length-driven case (B) "
            "moved off that point and was measured to coincide with the plain "
            "fold (A) on every path of length >= 2, leaving `[]` — the one input "
            "at which all three other rivals AGREE with gold — unprobed by the "
            "whole battery. Its witness is refutable only at `[]`, so it adds a "
            "genuinely new discriminating point rather than a second spelling of "
            "an existing one."),
        "refinement": (
            "Faithful real patch: derive the key from the resolved path verbatim "
            "except when that path renders empty, where a placeholder or sentinel "
            "key is substituted instead. Any input whose resolved path is empty "
            "is then stored under a key unrelated to it, so a recomputed-key "
            "lookup for that input misses and the hook module is loaded a second "
            "time under a key the cache never matches — the de-duplication the "
            "modeled step exists to provide is lost on that sub-domain. Scope "
            "stated honestly: the FAIL_TO_PASS inputs have non-empty resolved "
            "paths, so this rival does not flip the F2P pair; it is a "
            "spec-strength case, pinning that the clause admits no exempt point, "
            "which is the property that makes the identity claim total."),
        "witness": _W_EMPTY,
    },
    {
        "id": "soundness-inline-identity",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_INLINE),
        "rationale": (
            "Structurally different but correct: drop the intermediate local and "
            "return `resolved` directly. Semantically identical to the gold; the "
            "sole clause result = resolved is discharged by the same `rfl`. MUST "
            "verify, else the spec is over-fitted to the two-line gold shape "
            "(SPEC-TOO-STRONG)."),
    },
    {
        "id": "soundness-map-identity",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_MAPID, _PROOF_POS_MAPID),
        "rationale": (
            "Structurally different but correct: express the identity as a map "
            "of the identity function over the path — the same map SHAPE the "
            "fold rival uses, but with `id`, so the derived key equals the input "
            "character-for-character. The proof closes with `List.map_id` (no new "
            "lemma, no sorry); the `theorem correct_cacheKey` statement is "
            "byte-identical. MUST verify, else SPEC-TOO-STRONG. Confirmed "
            "non-trivial by audit: this impl is NOT definitionally equal to the "
            "gold one — carrying the frozen `rfl` script over to it FAILS to "
            "close, so the case genuinely exercises a reshape the frozen proof "
            "does not cover, rather than passing because nothing changed."),
    },
    {
        "id": "soundness-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_BRANCH, _PROOF_POS_BRANCH),
        "rationale": (
            "Added by audit: the port of the nagini "
            "`pos-control-branch-reshape` positive, which was dropped without "
            "being recorded as an omission and is fully expressible here. A "
            "correct impl whose CONTROL FLOW differs from the gold's straight "
            "line — an always-true guard whose both arms return the path verbatim "
            "— so the key equals the input on every path. MUST verify, else the "
            "spec/obligation is over-fitted to a branch-free impl shape "
            "(SPEC-TOO-STRONG). Distinct in content from the inline and "
            "map-identity positives: those reshape the DATA path, this one "
            "introduces a branch, and the `if` blocks definitional unfolding so "
            "the frozen `rfl` no longer closes — the case therefore also confirms "
            "the spec accepts a correct impl whose proof is not the frozen "
            "script."),
    },
    {
        "id": "admissibility-ground-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_GOLD_IMPL, _PROOF_ADMISS),
        "rationale": (
            "Added by a second audit pass; restores the lane the port dropped, "
            "which is the ONLY detector of PRECOND-TOO-STRONG. The frozen "
            "obligation is unconditional, so there is no precondition binder to "
            "weaken — but that is not a reason for the lane to be vacuous. The "
            "analogue on a total carrier is the obligation being UNSATISFIABLE at "
            "exactly an F2P-shaped input, so this case DISCHARGES the obligation "
            "at concrete ground inputs by evaluation (`decide`) as `have`s, then "
            "closes the frozen obligation verbatim. Three points: an F2P-shaped "
            "all-lower-case path, the issue-shaped mixed-case path (both as an "
            "evaluation and as the spec predicate itself), and the empty-path "
            "boundary. MUST verify, else the modeled behavior is not satisfiable "
            "at a normal input. Nothing is assumed: no new declaration, no sorry, "
            "statement byte-identical, frozen tactic body retained as the final "
            "two lines. Measured load-bearing rather than a restatement of the "
            "frozen proof: carried against each of the three value rivals the "
            "module fails AT THE GROUND `have`s, with `decide` refuting the "
            "concrete evaluation, not merely at the trailing `rfl`."),
    },
]
