# properties.py — G-PBT falsification battery for django__django-14089 (lean lane).
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
#   implementation_reversed : List Int → List Int
#   Given an ordered collection's members in their existing order (`xs`), produce the
#   same members in the opposite order. The single postcondition pins the result to
#   the exact reversal of the input order (`result = xs.reverse`), grounded entirely
#   in the input list — the last member first, the first member last, every member
#   visited exactly once.
#
# CARRIER NOTE: the nagini sibling holds the input list at half permission (read-only)
# and pins the result via a @Pure front-recursive sequence-reversal oracle applied to
# the input, defended by framing Asserts and a loop invariant. This backend models the
# purely functional core: the modeled function is the total map `List Int → List Int`
# and the postcondition is the transparent, input-grounded relation `result =
# xs.reverse`. There is a single obligation (`theorem correct_reversed`) and a single
# spec clause over a single input binder `xs`.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's #1 class, `frame-mutate-elements`: the input list was
#     Acc(list_pred(elements), 1/2) read-only, and the mandatory attack wrote through
#     that half reference). Lean is referentially transparent — no aliasing, no
#     fractional permissions — so a "write-back into a read-only input" rival is not
#     expressible and the whole lane is VACUOUS here. See 'assessment'.
#   * ADMISSIBILITY does port, and `admiss-f2p-shape` below carries it. (An earlier
#     revision of this file recorded the lane as N/A because the lean obligation
#     `∀ xs, problem_spec_reversed xs (implementation_reversed xs)` has no
#     precondition hypothesis. That reason is WRONG: the analogue on a total carrier
#     is the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#     positive that discharges the obligation at that concrete input by evaluation —
#     as a `have`, before closing the frozen obligation verbatim — tests directly.
#     An independent audit built it and it verifies; see 'admiss-f2p-shape'.)
#   * AXIOM_TESTS (nagini's ax-rev-ref-sound / ax-rev-containment). The axiom lane is
#     G-AX's job; this gate ignores them. The reversal is modeled DEEPLY here (an
#     accumulator prepend-fold, no opaque callee), so there is no consumed axiom.
from pathlib import Path

INSTANCE = "django__django-14089"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). ------------------------------------------------------------

# The full impl body (accumulator prepend-fold). Replaced wholesale by the
# structurally-different positive controls (which also reprove).
_IMPL_DEF = (
    "def implementation_reversed (xs : List Int) : List Int := Id.run do\n"
    "  let mut acc : List Int := []\n"
    "  for x in xs do\n"
    "    acc := x :: acc\n"
    "  return acc\n"
)
assert _BASE.count(_IMPL_DEF) == 1, "impl-def anchor drifted"

# The single accumulator-update line: prepend (build reverse order). The forward
# rival appends instead; the empty rival leaves the accumulator untouched.
_PREPEND = "    acc := x :: acc\n"
assert _BASE.count(_PREPEND) == 1, "prepend anchor drifted"

# The loop header. The drop-first rival iterates the tail, never visiting the head.
_LOOP = "  for x in xs do\n"
assert _BASE.count(_LOOP) == 1, "loop anchor drifted"

# The `return` that hands the accumulator back. The permutation rival post-processes
# the accumulator here (a transposition), keeping the loop itself gold-shaped.
_RETURN = "  return acc\n"
assert _BASE.count(_RETURN) == 1, "return anchor drifted"

# The first tactic line of the frozen proof. The admissibility positive prepends a
# ground `have` in front of it, leaving the theorem STATEMENT byte-identical and
# adding no declaration.
_P_INTRO = "  intro xs\n"
assert _BASE.count(_P_INTRO) == 1, "intro anchor drifted"

# The frozen proof body (everything after the `theorem correct_reversed` STATEMENT,
# from the first tactic line onward). Swapped only by positives that reprove; the
# theorem statement itself is left byte-identical (obligation survives).
_PROOF = (
    "  intro xs\n"
    "  unfold problem_spec_reversed implementation_reversed\n"
    "  have helper : ∀ (ys : List Int) (init : List Int),\n"
    "      Id.run (forIn ys init\n"
    "        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))\n"
    "        = ys.reverse ++ init := by\n"
    "    intro ys\n"
    "    induction ys with\n"
    "    | nil => intro init; rfl\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      rw [ih]\n"
    "      simp [List.reverse_cons]\n"
    "  show Id.run (forIn xs [] _) = xs.reverse\n"
    "  rw [helper xs []]\n"
    "  simp\n"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-direct-reverse: structurally DIFFERENT but behaviourally identical — the
# accumulator prepend-loop is replaced by the direct closed form `xs.reverse`, which
# is the shape a faithful patch could equally take (it computes the identical result
# on every input). The `theorem correct_reversed` STATEMENT is kept byte-identical;
# only the proof body is reproven (`rfl`, since impl unfolds definitionally to the
# spec's RHS). If it FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected).
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL_DEF,
          "def implementation_reversed (xs : List Int) : List Int := xs.reverse\n"),
    _PROOF,
    "  intro xs\n"
    "  unfold problem_spec_reversed implementation_reversed\n"
    "  rfl\n",
)

# pos-foldl-prepend: a second structurally-different CORRECT impl — the imperative
# accumulator loop is re-expressed as a pure left fold that prepends each element
# (`xs.foldl (fun acc x => x :: acc) []`). Same result on every input; the frozen
# theorem STATEMENT is preserved and the proof reproven via a fold-orientation
# rewrite. If it FAILS => SPEC-TOO-STRONG.
_POS_FOLDL = _swap(
    _swap(_BASE, _IMPL_DEF,
          "def implementation_reversed (xs : List Int) : List Int :=\n"
          "  xs.foldl (fun acc x => x :: acc) []\n"),
    _PROOF,
    "  intro xs\n"
    "  unfold problem_spec_reversed implementation_reversed\n"
    "  simp [List.foldl_eq_foldr]\n",
)

# admiss-f2p-shape: ADMISSIBILITY. On a total carrier the obligation carries no
# precondition hypothesis, so the analogue of PRECOND-TOO-STRONG is the obligation
# being UNSATISFIABLE at exactly an F2P-shaped input: the modeled behavior could be
# pinned so that no result value discharges the clause at a normal collection, and
# the ∀-obligation would then be closable only vacuously (or not at all). This
# positive discharges the obligation at the concrete F2P-shaped member sequence
# `[1, 2, 3]` BY EVALUATION, as a ground `have` prepended to the existing tactic
# body, and then closes the frozen obligation verbatim. Nothing is assumed: no new
# declaration, the `theorem correct_reversed` STATEMENT stays byte-identical, and
# the frozen proof script follows unchanged. If the ground `have` fails to close,
# the clause is unsatisfiable at a normal input => PRECOND-TOO-STRONG analogue.
# Ports nagini's `admiss-f2p-shape`.
_POS_ADMISS = _swap(
    _BASE, _P_INTRO,
    "  have _ground : problem_spec_reversed [1, 2, 3]\n"
    "      (implementation_reversed [1, 2, 3]) := by\n"
    "    unfold problem_spec_reversed implementation_reversed\n"
    "    decide\n"
    + _P_INTRO,
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; each carries a discriminating witness.
# Every witness probes a DIFFERENT input point so the battery demonstrates the spec's
# dependence on the single binder `xs` rather than refuting all rivals at one input.
# ---------------------------------------------------------------------------

def _wit(xs_literal):
    """A refutation witness: `¬ problem_spec_reversed xs (implementation_reversed xs)`
    at a concrete input, closed by `decide`. It ELABORATES against a rival that
    diverges from the reversal there, and FAILS on the frozen solution (which
    satisfies the spec at every input, so the negation is not provable)."""
    return (
        f"example : ¬ problem_spec_reversed {xs_literal}\n"
        f"    (implementation_reversed {xs_literal}) := by\n"
        f"  unfold problem_spec_reversed implementation_reversed\n"
        f"  decide"
    )


# forward-order: append each element to the END of the accumulator instead of the
# front, reproducing the input (forward / insertion) order — exactly the pre-patch
# behaviour where no reverse enumeration existed and iteration handed back forward
# order. Correct ONLY on the empty/singleton/palindromic sub-domain.
_RIVAL_FORWARD = _swap(_BASE, _PREPEND, "    acc := acc ++ [x]\n")

# drop-first: iterate the TAIL, so the first member is never emitted. The output is
# the reversal of all-but-the-first member — correct length-minus-one, correct on the
# empty sub-domain only, too short (missing the last reversed member) on every
# non-empty input.
_RIVAL_DROP = _swap(_BASE, _LOOP, "  for x in xs.tail do\n")

# always-empty: leave the accumulator untouched inside the loop, so the result is the
# empty list for every input. Correct ONLY on the empty collection.
_RIVAL_EMPTY = _swap(_BASE, _PREPEND, "    acc := acc\n")

# transpose-head: ADDED by the independent audit. The three rivals above all get the
# result's CONTENTS or LENGTH wrong (forward order is a different sequence of the same
# members, but the other two return a strictly shorter list), so a spec that pinned
# only "the same members, some order" plus a length would still reject all three. This
# rival isolates ORDER alone: it runs the gold loop verbatim and then transposes the
# first two members of the finished accumulator, so the result is always a PERMUTATION
# of the input of the same length, differing from the reversal only in the position of
# two adjacent members. It is the minimal order-only perturbation, and it is what
# demonstrates the clause pins the exact permutation rather than a multiset + length.
_RIVAL_TRANSPOSE = _swap(
    _BASE, _RETURN,
    "  match acc with\n"
    "  | a :: b :: rest => return b :: a :: rest\n"
    "  | other => return other\n",
)


SPEC_TESTS = [
    {
        "id": "pos-direct-reverse",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "structurally-different but CORRECT impl: the accumulator prepend-loop is "
            "replaced by the direct closed form of the reversal, producing the "
            "identical result on every input. The frozen `theorem correct_reversed` "
            "STATEMENT is kept byte-identical; only the proof body is reproven (the "
            "impl unfolds definitionally to the spec's RHS). Attacks the sole "
            "postcondition clause `result = xs.reverse` from the defence side. If it "
            "FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-foldl-prepend",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLDL,
        "rationale": (
            "a second structurally-different CORRECT impl: the imperative accumulator "
            "loop is re-expressed as a pure left fold that prepends each element, same "
            "result on every input. The frozen theorem STATEMENT is preserved and the "
            "proof reproven via a fold-orientation rewrite. Guards against the spec "
            "being over-fit to the one imperative source shape. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADMISSIBILITY. The obligation is discharged at the concrete F2P-shaped "
            "member sequence [1, 2, 3] BY EVALUATION, as a ground `have` prepended to "
            "the existing tactic body, and only then is the frozen obligation closed "
            "verbatim. On a total carrier this is the analogue of PRECOND-TOO-STRONG: "
            "the clause could be pinned so that NO result value satisfies it at a "
            "normal collection, leaving the ∀-obligation satisfiable only vacuously. "
            "Nothing is assumed — no new declaration, the `theorem correct_reversed` "
            "STATEMENT is byte-identical, the frozen script follows unchanged. If the "
            "ground `have` fails to close => the modeled behavior is unsatisfiable at "
            "exactly an F2P-shaped input. Ports nagini's `admiss-f2p-shape`."
        ),
    },
    {
        "id": "forward-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FORWARD,
        "refinement": (
            "prepends the WRONG way — appends to the accumulator's end — reproducing "
            "the input's forward (insertion) order. Its faithful real counterpart is a "
            "reverse-enumeration method that hands back forward order (equivalently, "
            "the pre-patch state where no such method existed), making "
            "`list(reversed(collection([1,2,3]))) == [1,2,3] != [3,2,1]`. The "
            "FAIL_TO_PASS reverse-enumeration test asserts the reversed order, so it "
            "FAILS; the rival does NOT resolve. This is precisely the behaviour class "
            "the change fixes (a traversal that PRESERVES rather than REVERSES order), "
            "so a verifying rival would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause `result = xs.reverse`: on any "
            "input whose reversal differs from itself the rival returns the forward "
            "order, which is not the reversal. Attacks the ORDER pinned by the clause "
            "over the binder `xs`. If it VERIFIES => SPEC-TOO-WEAK (admits forward "
            "order as a 'reversal')."
        ),
        # xs = [1,2,3]: gold => [3,2,1], rival => [1,2,3]. Differ.
        "witness": _wit("[1, 2, 3]"),
    },
    {
        "id": "drop-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP,
        "refinement": (
            "iterates the tail, so the first member is never emitted; the output is "
            "the reversal of all-but-the-first member. Its faithful real counterpart "
            "is a reverse-enumeration that omits the first inserted member, making "
            "`list(reversed(collection([1,2,3]))) == [3,2] != [3,2,1]` — the "
            "FAIL_TO_PASS reverse-enumeration test FAILS; it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = xs.reverse`: on any non-empty input the result is "
            "one element short (missing the last element of the reversal), so it "
            "cannot equal `xs.reverse`. Attacks the completeness of the clause — every "
            "member must be visited — over a DIFFERENT length/shape of the binder "
            "`xs` than the forward rival. If it VERIFIES => SPEC-TOO-WEAK (the "
            "reversal need not visit every element)."
        ),
        # xs = [4,5]: gold => [5,4], rival (tail [5] reversed) => [5]. Differ.
        "witness": _wit("[4, 5]"),
    },
    {
        "id": "always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EMPTY,
        "refinement": (
            "returns the empty list for every input (the accumulator is never "
            "updated). Its faithful real counterpart is a reverse-enumeration "
            "returning an empty iterator, making "
            "`list(reversed(collection([1,2,3]))) == [] != [3,2,1]` — the FAIL_TO_PASS "
            "reverse-enumeration test FAILS; it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = xs.reverse`: the empty list is the reversal only of "
            "the empty collection, so on any non-empty input the rival contradicts the "
            "clause. Attacks the clause at a THIRD distinct input point (a singleton, "
            "the minimal non-empty shape). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # xs = [9]: gold => [9], rival => []. Differ.
        "witness": _wit("[9]"),
    },
    {
        "id": "transpose-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TRANSPOSE,
        "refinement": (
            "runs the reversal correctly and then transposes the first two members "
            "produced. Its faithful real counterpart is a reverse enumeration that "
            "yields the two most-recently-inserted members the wrong way round, making "
            "`list(reversed(collection([1,2,3,4]))) == [3,4,2,1] != [4,3,2,1]` — the "
            "FAIL_TO_PASS reverse-enumeration test asserts the exact member order, so "
            "it FAILS; the rival does NOT resolve. It is a same-length permutation of "
            "the members, so it is the near-miss the other rivals do not cover: only "
            "the ORDER is wrong."
        ),
        "rationale": (
            "REJECTED by `result = xs.reverse`: the result is a permutation of the "
            "input with the correct length and the correct member multiset, differing "
            "from the reversal only in the position of two adjacent members, so it "
            "still fails the equality. This is the clause's ORDER content in "
            "isolation — the other three rivals each get the contents or the length "
            "wrong, so a spec pinning merely 'the same members, some order, same "
            "length' would reject them all and admit this one. Attacks the clause at a "
            "FOURTH distinct input point (length 4, the shortest input at which a "
            "head transposition is not itself the reversal). If it VERIFIES => "
            "SPEC-TOO-WEAK (any same-length permutation passes as a 'reversal')."
        ),
        # xs = [1,2,3,4]: gold => [4,3,2,1], rival => [3,4,2,1]. Same members, same
        # length, different order. Differ. (At length <= 2 a head transposition IS
        # the reversal of a reversal, so a shorter input would not discriminate.)
        "witness": _wit("[1, 2, 3, 4]"),
    },
]


# No @ContractOnly axioms and no opaque callees: the reversal is modeled DEEPLY over
# the transparent `List Int` carrier (an accumulator prepend-fold), so the axiom lane
# is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
