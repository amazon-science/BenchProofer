# properties.py — PBT falsification battery for pydata__xarray-4695 (lean backend).
#
# PORT of the nagini sibling's spec lane onto this bundle's carrier. NOT a Lean
# source file: a manifest the G-PBT gate parses, executes and stamps a verdict
# onto. Each spec case is a FULL Solution.lean variant built by region surgery —
# only the `impl` body and the `proof` body are edited, so the spec view
# (imports, module docstring, axioms region, pure helpers, post-conditions, and
# the `theorem correct_<name>` STATEMENT) is byte-identical and `same_spec` holds
# by construction. Every case is additionally screened by `variant_scope`
# (obligation preserved, no new axiom/theorem, no `sorry`/`admit`/
# `native_decide`), and every reject case carries a `witness` the gate builds
# TWICE: it must elaborate against the rival and FAIL against the frozen
# solution.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read Solution.lean)
# ---------------------------------------------------------------------------
# ONE modeled function, one obligation:
#
#   implementation_labelSelection (key : List (String × Label)) : SelArgs
#   problem_spec_labelSelection key result := result = canonicalSelArgs key
#   correct_labelSelection : ∀ key, problem_spec_labelSelection key (impl key)
#
# `canonicalSelArgs key = { indexers := key, method := none, tolerance := none,
# drop := none }`, so the single structure equality decomposes into FOUR
# independent top-level clauses, each of which a rival can attack in isolation:
#
#   (C1) indexers = key  — the WHOLE incoming mapping becomes the dimension→label
#        selection, every entry preserved and in order; no entry is diverted out
#        of the selection because of what its dimension happens to be named.
#   (C2) method    = none — the inexact-match parameter is never populated from
#        the mapping.
#   (C3) tolerance = none — the matching-tolerance parameter likewise.
#   (C4) drop      = none — the coordinate-dropping flag likewise.
#
# The discriminating sub-domain is a mapping one of whose dimension names
# coincides with the name of an optional matching parameter ("method" /
# "tolerance" / "drop"). The behavior under attack routes such an entry OUT of
# the selection and INTO the matching parameter — which is exactly the F2P
# `test_loc_dim_name_collision_with_sel_params` failure (the selection loses the
# colliding dimension, and the matcher is then handed a label it rejects).
# There is NO precondition: the obligation is unconditionally quantified over
# every `List (String × Label)`.
#
# ---------------------------------------------------------------------------
# Carrier narrowing vs the nagini sibling (recorded so the omissions audit)
# ---------------------------------------------------------------------------
# The nagini model contracts TWO functions over a parallel pair of half-permission
# integer list carriers (`forward_axis_names` -> the forwarded selector sequence,
# `bound_reserved_option` -> the single reserved option slot), with axis names and
# labels encoded as ints and ONE reserved name/option pair. This bundle models the
# same behavior as ONE function returning the whole argument bundle, over the real
# string-keyed mapping and all THREE optional matching parameters. Consequences:
#
#   * nagini's two contracted functions FUSE into one obligation here, so its two
#     positive controls (`pos-control-forward-localreshape`,
#     `pos-control-option-direct`) fuse into `pos-direct` / `pos-reverse-accum`
#     below — two structurally different CORRECT impls, each with a proof that
#     actually closes for its own shape (no weakened statement, no helper lemma
#     beyond the frozen `labelSelection_loop`, whose NAME is preserved).
#   * nagini's `oracle-echo-option-namekeyed` and
#     `partial-domain-option-conditional` both attack the SAME single clause
#     (`Result() == DEFAULT_OPTION()`) and differ only in whether the wrong value
#     is returned unconditionally or only on the colliding sub-domain. On this
#     carrier that distinction collapses: because the spec pins the whole bundle,
#     "echo the diverted value" and "default unless a collision occurs" are the
#     same impl. They port as the single `weak-leak-matching-params` rival, whose
#     witness is placed on the matching-parameter clause the fused pair was about.
#     `weak-populate-drop-flag` then attacks the remaining flag clause on a
#     NON-colliding input, which nagini's single-option model could not express.
#   * the FRAME-MUTATION lane (`frame-mutation-names-append`,
#     `frame-mutation-values-write`) is VACUOUS on lean: the carrier is
#     referentially transparent — no aliasing, no fractional permission — so
#     "write into a read-only input" is not expressible. No substitute is
#     fabricated. The frame obligation itself is discharged structurally: the spec
#     pins every one of the four output components, so no component is left
#     unconstrained for a rival to fill freely (that is what C2/C3/C4 are for, and
#     `weak-populate-drop-flag` is the case that proves C4 is load-bearing).
#   * the DIVERGENCE lane. This bundle carries no
#     `set_option loom.semantics.termination` line at all, so the carrier is the
#     plain total one: the verifier will not accept a definition without a
#     decreasing measure, and a diverging rival is therefore REJECTED by the
#     carrier rather than by the spec. Measured, not assumed — two diverging impls
#     were built by this audit: `partial def implementation_labelSelection key :=
#     implementation_labelSelection key` fails at the DEFINITION (`failed to
#     compile 'partial' definition … could not prove that the type … is nonempty`),
#     and an impl appending a `while true do` after the frozen loop leaves the
#     obligation unclosable but its refutation is not decidable either — a witness
#     over it fails with `Tactic 'decide' failed` on the unreduced
#     `forIn Lean.Loop.mk` term, on the RIVAL side, which is the half a shippable
#     reject case needs to succeed. So the class is vacuous by the carrier and no
#     rival is fabricated: rejection here would attest to Lean's termination
#     checker, not to `result = canonicalSelArgs key`.
#   * nagini's ADMISSIBILITY case (`admiss-colliding-input`) argued from the
#     `Requires`. There is no precondition region here, so the precondition-binder
#     form of PRECOND-TOO-STRONG has nothing to attack — but the analogue on a
#     total carrier is the obligation being UNSATISFIABLE at an F2P-shaped input,
#     which IS expressible and is what `admiss-collision-aware` now tests: the impl
#     stays frozen and the spec predicate is discharged by EVALUATION at the F2P
#     mapping and at a saturated mapping whose every dimension name collides.
#   * the AXIOM lane (`ax-sound-routing`, `ax-cover-routing`) is DROPPED: the
#     frozen bundle's `axioms` region is empty (the behavior is modeled deeply and
#     structurally over the mapping, so there is no `opaque`/`axiom` callee), and
#     the axiom lane is G-AX's job, which this gate ignores.
#
# ---------------------------------------------------------------------------
# What replaces case-count parity: coverage of the surface THIS bundle models
# ---------------------------------------------------------------------------
#   * the obligation is DEFENDED by three `expect="verify"` cases (two
#     structurally different correct impls plus the admissibility probe) and
#     ATTACKED by six rivals;
#   * every one of the four independent postcondition clauses is attacked, and C1
#     is attacked on BOTH of its halves separately: C1/preservation by
#     `weak-drop-last` (via the mapping's length), C1/order by
#     `weak-order-reverse` (right length, wrong sequence), C1+C2 jointly by
#     `weak-splat-divert` and, deeper in the domain, by `weak-late-divert`,
#     C3 by `weak-leak-matching-params`, C4 by `weak-populate-drop-flag`;
#   * the single input binder `key` is VARIED across five distinct witness points
#     — a two-entry mapping with a colliding name, a one-entry mapping whose only
#     name collides with a DIFFERENT matching parameter, a one-entry mapping with
#     NO colliding name at all, a two-entry mapping with no colliding name, and a
#     THREE-entry mapping with a colliding name — so the battery probes the spec's
#     dependence on the mapping's length, on its entry order, and on both the
#     colliding and the collision-free sub-domain. `weak-order-reverse` shares its
#     input point with `weak-drop-last` deliberately: same mapping, different
#     clause half refuted, which is what shows the two halves of C1 are
#     independently load-bearing at one input rather than confounded across two.
#   * the deepest agreement any rival achieves is `weak-late-divert`'s: correct on
#     the whole zero-/one-/two-entry sub-domain, so the battery's refutations are
#     not all clustered on the smallest inputs.
from pathlib import Path

INSTANCE = "pydata__xarray-4695"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen regions every variant edits. Each anchor lies ENTIRELY inside the
# region it names and is unique in the file, so no _swap can reach the spec view.
# ---------------------------------------------------------------------------

# The whole `impl` region definition (header + body).
_IMPL_FULL = """\
def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
  let mut indexers : List (String × Label) := []
  for entry in key do
    indexers := indexers ++ [entry]
  return { indexers := indexers, method := none, tolerance := none, drop := none }"""
assert _BASE.count(_IMPL_FULL) == 1, "impl region drifted from expected text"

# The `proof` region's accumulator lemma, docstring included. Swapped ONLY by the
# imperative-reshape positive, whose loop has a different body; the declaration
# NAME is preserved, so `variant_scope` sees no new theorem.
_LOOP_LEMMA = """\
/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
over the accumulator so the induction goes through. -/
theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
    (forIn key init
        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
      : Id (List (String × Label)))
      = pure (init ++ key) := by
  induction key generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [pure_bind] at ih ⊢
    rw [ih]
    simp"""
assert _BASE.count(_LOOP_LEMMA) == 1, "loop lemma drifted"

# The `correct_labelSelection` tactic body (everything after `:= by`). The
# theorem STATEMENT above it is never touched by any variant.
_PROOF_BODY = """\
  intro key
  unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
  simp only [Id.run]
  rw [labelSelection_loop]
  rfl"""
assert _BASE.count(_PROOF_BODY) == 1, "proof body drifted"


def _impl(new_impl, new_proof=None, new_lemma=None):
    """Full Solution.lean variant: impl region replaced, proof body optionally
    reproven, accumulator lemma optionally restated (name preserved)."""
    src = _swap(_BASE, _IMPL_FULL, new_impl)
    if new_lemma is not None:
        src = _swap(src, _LOOP_LEMMA, new_lemma)
    if new_proof is not None:
        src = _swap(src, _PROOF_BODY, new_proof)
    return src


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS — must VERIFY (else SPEC-TOO-STRONG). Each reproves the
# byte-identical obligation for its own impl shape.
# ---------------------------------------------------------------------------

# pos-direct: drop the imperative accumulation entirely and build the argument
# bundle in one functional step — the whole mapping handed over as the
# dimension→label selection, every optional matching parameter left unset. This
# is the spec's `canonicalSelArgs` spelled out as an implementation, so the
# obligation closes by `rfl`.
_POS_DIRECT = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs :=\n"
    "  { indexers := key, method := none, tolerance := none, drop := none }",
    new_proof="  intro key\n  rfl",
)

# pos-reverse-accum: keep the imperative shape but accumulate the entries onto
# the FRONT and restore the order at the end (a cons-and-reverse traversal
# instead of a snoc traversal). Behaviourally identical; the accumulator lemma is
# restated so its induction matches the reshaped loop, and `correct_labelSelection`
# is reproven from it. Its passing is what shows the spec pins the CONTENT of the
# selection rather than one particular traversal.
_POS_REVERSE = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  let mut acc : List (String × Label) := []\n"
    "  for entry in key do\n"
    "    acc := entry :: acc\n"
    "  return { indexers := acc.reverse, method := none, tolerance := none, drop := none }",
    new_lemma=(
        "/-- The front-accumulating loop pushes each entry onto the accumulator, so\n"
        "it computes the reversed mapping in front of the initial list. Generalized\n"
        "over the accumulator so the induction goes through. -/\n"
        "theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :\n"
        "    (forIn key init\n"
        "        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (entry :: r)))\n"
        "      : Id (List (String × Label)))\n"
        "      = pure (key.reverse ++ init) := by\n"
        "  induction key generalizing init with\n"
        "  | nil => simp\n"
        "  | cons a as ih =>\n"
        "    rw [List.forIn_cons]\n"
        "    simp only [pure_bind] at ih ⊢\n"
        "    rw [ih]\n"
        "    simp"
    ),
    new_proof=(
        "  intro key\n"
        "  unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs\n"
        "  simp only [Id.run]\n"
        "  rw [labelSelection_loop]\n"
        "  simp\n"
        "  rfl"
    ),
)

# admiss-collision-aware: the port of nagini's precondition-admissibility case.
#
# REWRITTEN by the audit. The previous shape was an impl that "recognised" the
# discriminating sub-domain with `if <name collides> then X else X` — the SAME
# branch on both sides. That distinction is definitionally void (its proof had to
# erase the test with `ite_self` before anything could be proven), no concrete
# input was ever evaluated, and so the case tested nothing about the
# collision-shaped input: it was a shape-reshuffle positive wearing an
# admissibility label. Measured: with the frozen proof body it fails, with
# `ite_self` it passes, and in neither build does any collision-shaped mapping
# get looked at.
#
# The honest analogue of PRECOND-TOO-STRONG on this TOTAL carrier is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input. So the impl
# region is kept FROZEN byte-for-byte — the only thing under test is
# satisfiability at a concrete point, not a reshape — and two ground instances of
# the spec predicate are discharged BY EVALUATION as `have`s before the frozen
# obligation is closed verbatim:
#
#   * the F2P mapping [("dim1","x"), ("method","a")] — one ordinary dimension and
#     one whose name coincides with the inexact-match parameter;
#   * the saturated mapping [("method","a"), ("tolerance","1"), ("drop","d")] —
#     EVERY dimension name coincides with an optional matching parameter, the
#     extreme point of the discriminating sub-domain.
#
# `decide` actually computes both, so each `have` is a machine-checked "the
# obligation HOLDS here", which is what makes the domain demonstrably non-vacuous
# at the shape the reported behavior is about.
_ADMISS = _impl(
    _IMPL_FULL,
    new_proof=(
        "  have _f2p : problem_spec_labelSelection [(\"dim1\", \"x\"), (\"method\", \"a\")]\n"
        "      (implementation_labelSelection [(\"dim1\", \"x\"), (\"method\", \"a\")]) := by\n"
        "    unfold problem_spec_labelSelection implementation_labelSelection "
        "canonicalSelArgs\n"
        "    decide\n"
        "  have _f2p_saturated : problem_spec_labelSelection\n"
        "      [(\"method\", \"a\"), (\"tolerance\", \"1\"), (\"drop\", \"d\")]\n"
        "      (implementation_labelSelection\n"
        "        [(\"method\", \"a\"), (\"tolerance\", \"1\"), (\"drop\", \"d\")]) := by\n"
        "    unfold problem_spec_labelSelection implementation_labelSelection "
        "canonicalSelArgs\n"
        "    decide\n"
        + _PROOF_BODY
    ),
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and carries the gold proof body verbatim, so the recorded
# rejection is never a rewritten obligation; attribution to the spec comes from
# the `witness`, which the gate builds against the rival (must elaborate) and
# against the frozen solution (must fail).
# ---------------------------------------------------------------------------

# weak-splat-divert: the behavior the issue reports. Each entry's dimension name
# is tested against the names of the optional matching parameters; a match is
# routed INTO that parameter and dropped from the dimension→label selection,
# while non-matching entries accumulate as selectors. Attacks C1 (an entry
# disappears from the selection) and C2 (a matching parameter is populated).
_WEAK_SPLAT_DIVERT = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  let mut indexers : List (String × Label) := []\n"
    "  let mut method : Option Label := none\n"
    "  let mut tolerance : Option Label := none\n"
    "  let mut drop : Option Label := none\n"
    "  for entry in key do\n"
    "    let (name, label) := entry\n"
    "    if name = \"method\" then\n"
    "      method := some label\n"
    "    else if name = \"tolerance\" then\n"
    "      tolerance := some label\n"
    "    else if name = \"drop\" then\n"
    "      drop := some label\n"
    "    else\n"
    "      indexers := indexers ++ [entry]\n"
    "  return { indexers := indexers, method := method, tolerance := tolerance, drop := drop }"
)

# weak-leak-matching-params: the NEAR-MISS of the rival above. Every entry is
# kept as a selector (C1 holds, so the selection no longer loses a dimension),
# but an entry whose name coincides with a matching parameter ALSO populates that
# parameter. Agrees with gold on strictly more of the domain than
# `weak-splat-divert` — on every mapping it agrees on the `indexers` component —
# so it gets its own witness, on a mapping whose only entry collides with the
# matching-TOLERANCE parameter, which isolates C3.
_WEAK_LEAK = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  let mut indexers : List (String × Label) := []\n"
    "  let mut method : Option Label := none\n"
    "  let mut tolerance : Option Label := none\n"
    "  let mut drop : Option Label := none\n"
    "  for entry in key do\n"
    "    let (name, label) := entry\n"
    "    indexers := indexers ++ [entry]\n"
    "    if name = \"method\" then\n"
    "      method := some label\n"
    "    if name = \"tolerance\" then\n"
    "      tolerance := some label\n"
    "    if name = \"drop\" then\n"
    "      drop := some label\n"
    "  return { indexers := indexers, method := method, tolerance := tolerance, drop := drop }"
)

# weak-populate-drop-flag: every entry is kept as a selector, and no name is
# treated specially — but the coordinate-dropping flag is fed from the mapping
# anyway (the last entry's label). Correct on the empty mapping and wrong on
# every non-empty one, INCLUDING mappings with no colliding name at all, so its
# witness sits on the collision-free sub-domain. Isolates C4, the clause no
# other rival touches.
_WEAK_DROP_FLAG = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  let mut indexers : List (String × Label) := []\n"
    "  let mut drop : Option Label := none\n"
    "  for entry in key do\n"
    "    indexers := indexers ++ [entry]\n"
    "    drop := some entry.2\n"
    "  return { indexers := indexers, method := none, tolerance := none, drop := drop }"
)

# weak-drop-last: no name is treated specially and no matching parameter is
# populated (C2/C3/C4 all hold), but the final entry of the mapping is left out
# of the selection — an off-by-one on the traversal. Correct on the empty mapping
# and on every proper prefix; wrong as soon as the mapping is non-empty. Isolates
# the "every entry preserved" half of C1 independently of any name collision.
_WEAK_DROP_LAST = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  let mut indexers : List (String × Label) := []\n"
    "  for entry in key do\n"
    "    indexers := indexers ++ [entry]\n"
    "  return { indexers := indexers.dropLast, method := none, tolerance := none, drop := none }"
)


# weak-order-reverse: ADDED by the audit. Every entry is preserved and no
# matching parameter is populated, so C2/C3/C4 hold and even the LENGTH of the
# selection is right — but the entries reach the selection in reverse ORDER. This
# is the one half of C1 no shipped rival attacked: `weak-drop-last` probes "every
# entry preserved" via the mapping's length, and nothing probed "in order". It is
# also the exact reshape `pos-reverse-accum` gets RIGHT (cons-and-reverse), so the
# pair pins that the positive earns its pass by restoring the order rather than by
# the traversal being unobservable.
_WEAK_ORDER_REVERSE = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  let mut indexers : List (String × Label) := []\n"
    "  for entry in key do\n"
    "    indexers := entry :: indexers\n"
    "  return { indexers := indexers, method := none, tolerance := none, drop := none }"
)

# weak-late-divert: ADDED by the audit. The DEEPEST partial-domain rival in the
# battery: it hands the whole mapping over untouched whenever the mapping has
# fewer than three entries, and only diverts a colliding dimension into the
# inexact-match parameter on mappings of three or more. So it agrees with the
# frozen behavior on the ENTIRE two-entry sub-domain — including the exact F2P
# mapping every other collision rival is refuted at — and is wrong only deeper in.
# Its refutation therefore has to be stated at a three-entry point, which is what
# shows the spec's `∀` is load-bearing beyond the small inputs the rest of the
# battery evaluates at, rather than being pinned only where a witness happens to
# be cheap.
_WEAK_LATE_DIVERT = _impl(
    "def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do\n"
    "  if key.length < 3 then\n"
    "    return { indexers := key, method := none, tolerance := none, drop := none }\n"
    "  let mut indexers : List (String × Label) := []\n"
    "  let mut method : Option Label := none\n"
    "  for entry in key do\n"
    "    if entry.1 = \"method\" then\n"
    "      method := some entry.2\n"
    "    else\n"
    "      indexers := indexers ++ [entry]\n"
    "  return { indexers := indexers, method := method, tolerance := none, drop := none }"
)


def _witness(key_lit, tactics="  decide"):
    """A refutation stated at a concrete mapping literal: the spec predicate is
    FALSE of what the rival returns there. All inputs are closed literals, so no
    hypothesis is introduced and there is nothing for the consistency probe to
    find inconsistent."""
    return (
        f"example : ¬ problem_spec_labelSelection {key_lit}\n"
        f"    (implementation_labelSelection {key_lit}) := by\n"
        f"  unfold problem_spec_labelSelection implementation_labelSelection "
        f"canonicalSelArgs\n"
        f"{tactics}"
    )


SPEC_TESTS = [
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "structurally different but CORRECT impl: the imperative accumulation "
            "is replaced by a single functional step that hands the whole mapping "
            "over as the dimension→label selection and leaves every optional "
            "matching parameter unset. That is the spec's own `canonicalSelArgs` "
            "spelled out as the implementation, so the byte-identical obligation "
            "`result = canonicalSelArgs key` closes by `rfl` — no weakened "
            "statement, no added lemma. If it FAILS => SPEC-TOO-STRONG: a faithful "
            "correct construction of the argument bundle is being rejected for its "
            "shape rather than its behavior."
        ),
    },
    {
        "id": "pos-reverse-accum",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REVERSE,
        "rationale": (
            "the imperative shape is kept but the traversal is reshaped: each entry "
            "is pushed onto the FRONT of the accumulator and the order restored at "
            "the end, instead of being appended. Behaviourally identical. The "
            "frozen accumulator lemma is RESTATED (same declaration name, so no new "
            "theorem is introduced) so its induction matches the reshaped loop, and "
            "`correct_labelSelection` is reproven from it with its statement "
            "untouched. If it FAILS => SPEC-TOO-STRONG: the postcondition would be "
            "pinning one particular traversal rather than the resulting selection. "
            "Together with pos-direct this defends the obligation from two "
            "genuinely different impl shapes."
        ),
    },
    {
        "id": "admiss-collision-aware",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADMISSIBILITY on a TOTAL carrier. The obligation is quantified over "
            "EVERY mapping with no hypothesis, so there is no precondition binder "
            "to attack; the analogue of PRECOND-TOO-STRONG here is the obligation "
            "being UNSATISFIABLE at a concrete input of the shape the exported "
            "behavior must handle. So the impl region is kept FROZEN byte-for-byte "
            "and the spec predicate is discharged BY EVALUATION (`decide`, which "
            "genuinely computes) at two ground points inside the discriminating "
            "sub-domain: the F2P mapping [(\"dim1\",\"x\"), (\"method\",\"a\")], and "
            "the saturated mapping [(\"method\",\"a\"), (\"tolerance\",\"1\"), "
            "(\"drop\",\"d\")] whose EVERY dimension name coincides with an optional "
            "matching parameter. Both `have`s must close before the frozen "
            "obligation is closed verbatim, so the case attests that the "
            "collision-shaped input is genuinely in-domain and the obligation there "
            "holds rather than being vacuously quantified. If it FAILS => the "
            "modeled domain excludes the very input the issue is about. (An earlier "
            "shape of this case used an impl branching `if <name collides> then X "
            "else X`; that test is definitionally void — its proof had to erase it "
            "with `ite_self` — and evaluated no input, so it was replaced.)"
        ),
    },
    {
        "id": "weak-splat-divert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_SPLAT_DIVERT,
        "refinement": (
            "this IS the reported behavior: a dimension whose name coincides with "
            "one of the optional matching parameters is consumed by that parameter "
            "instead of being used to select along its dimension, and disappears "
            "from the selection entirely. Its faithful real patch is the unchanged "
            "code — the selection request is assembled by spreading the mapping "
            "into the named optional parameters — under which a selection along a "
            "dimension named like the inexact-match parameter loses that dimension "
            "and hands the matcher a label it rejects, raising instead of "
            "selecting. That is exactly the F2P collision test, so this rival does "
            "NOT resolve: if it VERIFIED it would be a genuine "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by `result = canonicalSelArgs key` on the two-entry mapping "
            "[(\"dim1\",\"x\"), (\"method\",\"a\")] — the F2P shape. The spec demands "
            "indexers = the whole mapping and method = none; the rival returns "
            "indexers = [(\"dim1\",\"x\")] and method = some \"a\". Attacks C1 (every "
            "entry preserved) and C2 (the inexact-match parameter stays unset) "
            "simultaneously. If it VERIFIES => SPEC-TOO-WEAK: the spec would permit "
            "diverting a selector into a matching parameter."
        ),
        "witness": _witness('[("dim1", "x"), ("method", "a")]'),
    },
    {
        "id": "weak-leak-matching-params",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_LEAK,
        "refinement": (
            "the NEAR-MISS: every dimension is forwarded as a selector (so no "
            "dimension is lost from the selection any more), but a dimension whose "
            "name coincides with a matching parameter ALSO sets that parameter. Its "
            "faithful real patch passes the mapping as the selection AND "
            "re-supplies the colliding entries under their reserved names. On a "
            "selection along a dimension named like the inexact-match parameter the "
            "matcher is still handed a label it rejects and still raises, so the "
            "F2P collision test still fails; a selection along a dimension named "
            "like the tolerance parameter is likewise rejected, because a matching "
            "tolerance is only accepted together with an inexact-match mode. This "
            "rival does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = canonicalSelArgs key` on the one-entry mapping "
            "[(\"tolerance\",\"1\")]. The spec demands tolerance = none; the rival "
            "returns tolerance = some \"1\". Isolates C3 — the indexers component "
            "AGREES with the spec here, so the refutation is attributable to the "
            "matching-parameter clause alone and to nothing about entry loss. "
            "Deliberately a DIFFERENT input point from weak-splat-divert (which "
            "agrees with gold on strictly less of the domain), so this rival's "
            "narrower sub-domain claim is demonstrated rather than asserted. If it "
            "VERIFIES => SPEC-TOO-WEAK: populating a matching parameter from the "
            "mapping would be permitted as long as no selector is lost."
        ),
        "witness": _witness('[("tolerance", "1")]'),
    },
    {
        "id": "weak-populate-drop-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DROP_FLAG,
        "refinement": (
            "no dimension name is treated specially and no dimension is lost, but "
            "the coordinate-dropping flag is nevertheless fed from the mapping. Its "
            "faithful real patch supplies a mapping-derived value for that flag on "
            "EVERY label selection, so every such selection silently discards the "
            "coordinate it selected on. The F2P collision test asserts the selected "
            "block WITH its coordinates intact, and the broad body of label-based "
            "selection tests assert the same, so this rival fails them and does NOT "
            "resolve — the strongest kind of non-resolution, since it is wrong on "
            "the whole non-empty domain rather than on a corner of it."
        ),
        "rationale": (
            "REJECTED by `result = canonicalSelArgs key` on the one-entry mapping "
            "[(\"dim1\",\"x\")] — a mapping with NO colliding name. The spec demands "
            "drop = none; the rival returns drop = some \"x\". Isolates C4, the "
            "clause no other rival touches, and does so on the COLLISION-FREE "
            "sub-domain, which is what makes the clause's independence from the "
            "collision story visible. If it VERIFIES => SPEC-TOO-WEAK: the "
            "coordinate-dropping flag would be left unconstrained, the referentially"
            "-transparent analogue of an unpinned output component."
        ),
        "witness": _witness('[("dim1", "x")]'),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DROP_LAST,
        "refinement": (
            "no name is treated specially and no matching parameter is populated, "
            "but the final entry of the mapping is left out of the selection. Its "
            "faithful real patch forwards all but the last entry of the mapping, so "
            "every label selection over a non-empty mapping silently omits one "
            "dimension — the F2P collision test selects along two dimensions and "
            "would get the wrong block, and the broad body of label-based selection "
            "tests would break with it. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = canonicalSelArgs key` on the two-entry mapping "
            "[(\"dim1\",\"x\"), (\"dim2\",\"a\")] — again with NO colliding name. The "
            "spec demands indexers = the whole mapping; the rival returns "
            "[(\"dim1\",\"x\")]. Isolates the 'every entry preserved' half of C1 "
            "independently of the name-collision story, and probes the spec's "
            "dependence on the mapping's LENGTH (correct on the empty mapping and "
            "on every proper prefix, wrong as soon as it is non-empty). If it "
            "VERIFIES => SPEC-TOO-WEAK: the spec would not pin that the whole "
            "mapping reaches the selection."
        ),
        "witness": _witness('[("dim1", "x"), ("dim2", "a")]'),
    },
    {
        "id": "weak-order-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_ORDER_REVERSE,
        "refinement": (
            "no name is treated specially, no matching parameter is populated, and "
            "not one entry is lost — the selection is the whole mapping, but "
            "back-to-front. Its faithful real patch hands the selection routine the "
            "dimension→label pairs in reversed order. The F2P collision test selects "
            "along two dimensions and asserts a specific block, and the broad body "
            "of label-based selection tests assert theirs, so wherever the order of "
            "the pairs is observable to the routine the selected block is wrong. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = canonicalSelArgs key` on the two-entry mapping "
            "[(\"dim1\",\"x\"), (\"dim2\",\"a\")]. The spec demands indexers = the "
            "whole mapping IN ORDER; the rival returns [(\"dim2\",\"a\"), "
            "(\"dim1\",\"x\")]. Isolates the 'in order' half of C1 — the half no "
            "other rival attacks, since weak-drop-last probes preservation via the "
            "mapping's LENGTH and this rival has the right length. It is also the "
            "exact traversal `pos-reverse-accum` performs and then corrects, so the "
            "pair pins that the positive earns its pass by restoring the order "
            "rather than by the order being unobservable. If it VERIFIES => "
            "SPEC-TOO-WEAK: the spec would pin the selection's CONTENTS as a "
            "multiset and leave its sequence free."
        ),
        "witness": _witness('[("dim1", "x"), ("dim2", "a")]'),
    },
    {
        "id": "weak-late-divert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_LATE_DIVERT,
        "refinement": (
            "the DEEPEST near-miss: mappings of fewer than three entries are handed "
            "over whole and untouched, and only from three entries on is a dimension "
            "named like the inexact-match parameter diverted into it and dropped "
            "from the selection. Its faithful real patch spreads the mapping into "
            "the named optional parameters only once the selection spans three or "
            "more dimensions — so it happens to get the two-dimensional collision "
            "right while reintroducing the reported behavior on any wider selection, "
            "where the matcher is again handed a label it rejects and raises. The "
            "broad body of label-based selection tests covers such selections, so "
            "this rival does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = canonicalSelArgs key` on the THREE-entry mapping "
            "[(\"dim1\",\"x\"), (\"dim2\",\"y\"), (\"method\",\"a\")]. The spec demands "
            "indexers = the whole mapping and method = none; the rival returns "
            "indexers = [(\"dim1\",\"x\"), (\"dim2\",\"y\")] and method = some \"a\". "
            "Its point is the DEPTH of its agreement: it matches the frozen behavior "
            "on the entire zero-, one- and two-entry sub-domain, including the exact "
            "input weak-splat-divert is refuted at, so refuting it requires a "
            "strictly larger mapping than any other case in the battery uses. That is "
            "what demonstrates the obligation's `∀` binds beyond the small inputs the "
            "other witnesses evaluate at. If it VERIFIES => SPEC-TOO-WEAK: the spec "
            "would constrain only the short mappings and leave wider selections free "
            "to divert a dimension."
        ),
        "witness": _witness('[("dim1", "x"), ("dim2", "y"), ("method", "a")]'),
    },
]
