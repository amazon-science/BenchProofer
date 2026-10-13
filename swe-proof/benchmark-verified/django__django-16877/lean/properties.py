"""PBT falsification battery for django__django-16877 (lean backend).

Ported from the nagini sibling's battery; the ARGUMENTS carry over, the
mechanics are re-expressed against this backend's carrier.

## The defended surface

This bundle models ONE obligation, `correct_escapeEach`, over the single
postcondition clause

    result = value.map condEscape

where `value : List Elem`, `Elem = { isSafe : Bool, text : String }`, and
`condEscape : Elem -> String` is the shared per-element escaping decision,
referenced OPAQUELY (the spec pins each entry to its value but assumes no
property of it).

That one equation is not one thing to attack, it is four, and the reject lane
below takes each in turn:

  * **length** — one entry per input element (`List.length_map`), probed in BOTH
    directions (a result one entry SHORT and a result one entry LONG);
  * **order** — the i-th entry corresponds to the i-th input element;
  * **the argument each entry is computed from** — entry i is the escaper applied
    to `value[i]` *as given*, not to a reconstructed element with a different
    safe-marking;
  * **whether the escaper is applied at all** — an entry may not be the raw
    element text.

## Attacking an opaque carrier

`condEscape` has no computable value, so no literal input `decide`s anything and
the reject witnesses cannot compute the expected answer. Three of the five
therefore CONDITION on the carrier instead: they assume exactly one inequality
about `condEscape` (never two facts about the same term) and derive that the
rival's output differs from `value.map condEscape` at a concrete two- or
one-element input. The claim each makes is the sub-domain where the rival is
wrong: *whenever the escaper distinguishes these two elements, the rival's answer
differs from the specified one.* Each such hypothesis is satisfiable on its own
(a single disequality between two distinct opaque applications), so no witness
proves its refutation from a contradiction.

The other three attack what IS transparent: the LENGTH of the returned list (too
short and too long) and the fact that an entry is the raw `text` field rather than
any application of the escaper. None needs to know anything about the escaper at
all.

## The admissibility lane on a total carrier

The frozen obligation is universally quantified over `value` and carries no
precondition, so there is no precondition to find too strong in the literal
sense. The analogue that IS testable here is the obligation being UNSATISFIABLE
at an F2P-shaped input, and the positive below tests it directly: it discharges
`problem_spec_escapeEach` at the two concrete two-element inputs the behavior is
pinned on — ordinary text, and the same texts already marked safe — BY
EVALUATION, as `have`s, before closing the frozen obligation verbatim. If the
specified result were unreachable at either concrete point (an over-constrained
equation no impl could satisfy there), those `have`s would not close even though
the universally-quantified theorem might still be provable vacuously elsewhere.

## Binder coverage

The spec's only input binder is `value`, and the five reject witnesses move it
across five distinct points: a singleton not-marked-safe element, a singleton
marked-safe element, and three two-element lists whose safe-markings and texts
differ. Length (1 vs 2), the per-element `isSafe` field (false, true, and mixed
in both orders) and the `text` field ("x&y", "<p>") are all varied, so no rival
that mishandled only one of those observables could slip through unprobed.

## Known hole: the divergence lane

A rival whose `implementation_escapeEach` is a `partial def` that recurses on
itself unchanged carries no decreasing measure. This bundle's carrier discharges
no termination obligation (`loom.semantics.termination` is a velvet solver flag;
the lean backend has none), so such an impl is not rejected for diverging -- and
it cannot be refuted by a witness either: a `partial def` is opaque to the
kernel, so `implementation_escapeEach [..]` never reduces and the refutation's
`False` goal cannot be closed from the spec equation. Measured: the rival's
witness build leaves `hh : implementation_escapeEach [..] = [condEscape .., ..]`
and the goal `False` unsolved. So this is recorded as a KNOWN HOLE in the spec,
not as a vacuous class -- there is nothing shippable to add, and the reason is
the absent termination obligation rather than any weakness the reject lane below
could close.

## Authoring discipline

Every variant is built by region surgery on `Solution.lean`: `_swap` edits text
lying strictly inside the `impl` region (and, for one positive, the `proof`
region), so the spec view is byte-identical (`same_spec` holds) and the
`theorem correct_escapeEach` STATEMENT is preserved verbatim. No case adds an
axiom, a helper lemma, a `sorry`/`admit`, or `native_decide`.
"""
from pathlib import Path

INSTANCE = "django__django-16877"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (verbatim text strictly inside the regions being edited).
# ---------------------------------------------------------------------------

# The whole impl-region body: the in-order accumulator loop.
_IMPL = """  let mut acc := []
  for obj in value do
    acc := acc ++ [condEscape obj]
  return acc"""

# The tactic body of the frozen obligation (proof region). Only used by the
# positive that reshapes the impl into a form the frozen script no longer
# matches; the theorem STATEMENT above it is untouched.
_PROOF_TAIL = """  intro value
  unfold problem_spec_escapeEach implementation_escapeEach
  show (Id.run (forIn value [] (fun obj r => do
          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
  rw [helper_escapeEach value []]
  simp"""

# ---------------------------------------------------------------------------
# Concrete elements the witnesses probe. Two texts (one containing a character
# the escaper rewrites, one an entire bracketed fragment) x both safe-markings.
# ---------------------------------------------------------------------------
_UNSAFE_A = '{ isSafe := false, text := "x&y" }'
_SAFE_A = '{ isSafe := true, text := "x&y" }'
_UNSAFE_B = '{ isSafe := false, text := "<p>" }'
_SAFE_B = '{ isSafe := true, text := "<p>" }'


SPEC_TESTS = []

# ===========================================================================
# SOUNDNESS POSITIVES (expect="verify")
# ===========================================================================

# ---------------------------------------------------------------------------
# (1) A structurally different CORRECT impl: state the element-wise application
#     directly instead of accumulating it in a loop. The obligation statement is
#     byte-identical; the tactic body is REPROVEN for the new shape (the frozen
#     script's `show ... forIn ...` no longer matches, so it is replaced by the
#     `rfl` that closes for this shape). The frozen helper lemma is kept exactly
#     as-is -- no new lemma is introduced. If a faithful correct impl could not
#     verify, the spec would be SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_DIRECT_MAP = "  return value.map condEscape"

_PROOF_DIRECT_MAP = """  intro value
  unfold problem_spec_escapeEach implementation_escapeEach
  rfl"""

SPEC_TESTS.append({
    "id": "pos-direct-elementwise",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_swap(_BASE, _IMPL, _POS_DIRECT_MAP),
                    _PROOF_TAIL, _PROOF_DIRECT_MAP),
    "rationale": (
        "The same length-, order- and entry-preserving element-wise application, "
        "written as a direct traversal rather than an accumulator loop. It "
        "satisfies `result = value.map condEscape` definitionally, so the "
        "obligation closes by `rfl` with the theorem statement unchanged and the "
        "frozen helper lemma untouched (no new lemma, no weakened goal). A "
        "correct restructure that could not verify would mean SPEC-TOO-STRONG. "
        "This is the lean counterpart of the nagini branch-reorder positive: a "
        "different executable shape for the same map."),
})

# ---------------------------------------------------------------------------
# (2) Bind the per-element result to a local before appending it, instead of
#     appending the call directly. Same accumulator loop, same order, one extra
#     `let`. The frozen proof body is kept VERBATIM (the `let` is transparent to
#     the loop-fold reasoning), so this positive cannot pass for a proof reason.
#     This is the direct port of nagini's `pos-control-local-bind`.
# ---------------------------------------------------------------------------
_POS_LOCAL_BIND = """  let mut acc := []
  for obj in value do
    let e := condEscape obj
    acc := acc ++ [e]
  return acc"""

SPEC_TESTS.append({
    "id": "pos-local-bind",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _IMPL, _POS_LOCAL_BIND),
    "rationale": (
        "Binding the per-element escaping decision to a local and appending the "
        "local is the same length/order-preserving element-wise application; the "
        "frozen proof body is carried over verbatim and still closes, so the "
        "verify is attributable to the impl being correct and not to a reproof. "
        "A correct restructure must verify (else SPEC-TOO-STRONG)."),
})

# ---------------------------------------------------------------------------
# (2b) ADMISSIBILITY. On this total carrier the frozen obligation has no
#      precondition, so PRECOND-TOO-STRONG cannot arrive as an unprovable
#      `require`. Its analogue is the obligation being UNSATISFIABLE at a
#      concrete F2P-shaped input, and that is what this case tests: the impl is
#      the frozen one and the frozen tactic body is kept VERBATIM, with two
#      `have`s prepended that discharge `problem_spec_escapeEach` BY EVALUATION
#      at the two concrete two-element inputs the pinned behavior is stated over
#      -- ordinary not-marked-safe text, and the same two texts already marked
#      safe -- plus the concrete length. The `have`s are `clear`ed before the
#      frozen script runs, so they cannot help it close: the frozen obligation is
#      still discharged exactly as it is in the frozen file, and this case's
#      verify is attributable to the two concrete points being SATISFIABLE.
#      If either `have` failed, the spec would pin an unreachable result at an
#      input the behavior is actually exercised at.
# ---------------------------------------------------------------------------
_PROOF_ADMISS = f"""  -- admissibility: the specified result is REACHABLE at the concrete inputs the
  -- pinned behavior is stated over -- a two-element sequence of ordinary text,
  -- and the same two texts already marked safe -- discharged by evaluation
  -- BEFORE the frozen obligation is closed verbatim below.
  have adm_ordinary :
      problem_spec_escapeEach [{_UNSAFE_A}, {_UNSAFE_B}]
        (implementation_escapeEach [{_UNSAFE_A}, {_UNSAFE_B}]) := by
    unfold problem_spec_escapeEach implementation_escapeEach
    rfl
  have adm_marked_safe :
      problem_spec_escapeEach [{_SAFE_A}, {_SAFE_B}]
        (implementation_escapeEach [{_SAFE_A}, {_SAFE_B}]) := by
    unfold problem_spec_escapeEach implementation_escapeEach
    rfl
  have adm_len : (implementation_escapeEach [{_UNSAFE_A}, {_UNSAFE_B}]).length = 2 :=
    rfl
  -- discarded so the frozen script below closes on its own, unaided
  clear adm_ordinary adm_marked_safe adm_len
{_PROOF_TAIL}"""

SPEC_TESTS.append({
    "id": "admiss-f2p-shaped-input-satisfiable",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _PROOF_TAIL, _PROOF_ADMISS),
    "rationale": (
        "The lean analogue of the nagini sibling's admissibility positive. There "
        "is no precondition on this carrier, so the testable form of "
        "PRECOND-TOO-STRONG is the obligation being unsatisfiable at a concrete "
        "input the pinned behavior is actually exercised at. Two `have`s "
        "discharge `problem_spec_escapeEach` by EVALUATION at the two-element "
        "sequence of ordinary text and at the same two texts already marked safe, "
        "and a third pins the concrete length 2; all three are then `clear`ed so "
        "the frozen tactic body closes the obligation unaided and verbatim. A "
        "spec that over-constrained the result at either point -- pinning a value "
        "no impl could produce there -- would fail these `have`s while the "
        "quantified theorem might still go through, which is exactly the "
        "direction the other two lanes cannot see."),
})

# ===========================================================================
# UNIQUENESS RIVALS (expect="reject")
# ===========================================================================

# ---------------------------------------------------------------------------
# (3) RAW PASSTHROUGH on all but the first element. The nagini
#     `partial-domain-skip-escape-unsafe` argument (mark everything, escape
#     nothing) re-expressed as a PARTIAL-domain rival so it is a near-miss rather
#     than a restatement of the prepatch: element 0 gets the real escaping
#     decision, every later element is emitted as its raw text.
#     Attacks: "whether the escaper is applied at all", at index >= 1.
# ---------------------------------------------------------------------------
_RIV_RAW_TAIL = """  let mut acc := []
  let mut i := 0
  for obj in value do
    if i = 0 then
      acc := acc ++ [condEscape obj]
    else
      acc := acc ++ [obj.text]
    i := i + 1
  return acc"""

SPEC_TESTS.append({
    "id": "raw-text-after-first-element",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _IMPL, _RIV_RAW_TAIL),
    "refinement": (
        "A faithful real version emits the first element of the sequence through "
        "the per-element escaping decision and every subsequent element as its "
        "own raw text. The behavior the tests pin renders a two-element sequence "
        "of ordinary text with BOTH elements escaped, in both the escaping-on and "
        "escaping-off rendering contexts; this rival leaves the second element's "
        "special characters intact, so the rendered output differs from the "
        "expected one on all four FAIL_TO_PASS assertions. It would NOT resolve."),
    "rationale": (
        "Rejected by the entry clause of `result = value.map condEscape` at index "
        "1: the entry there is the element's `text` field, not the escaping "
        "decision applied to the element. The witness conditions on the ONE fact "
        "that makes the two differ -- the escaper does not return its input "
        "element's text verbatim for that element -- and probes a two-element "
        "input whose first element is marked safe and second is not, so the "
        "surviving index 0 agrees with gold and only index 1 refutes."),
    "witness": f"""
-- The rival's entry at index 1 is the element's raw `text`; the spec's is the
-- escaping decision applied to that element. Conditioning on the single fact
-- that separates them (the escaper does not echo this element's text) refutes
-- the rival there, while index 0 -- where the rival is still correct -- is left
-- agreeing with the spec.
example (h : condEscape {_UNSAFE_B} ≠ "<p>") :
    ¬ problem_spec_escapeEach [{_SAFE_A}, {_UNSAFE_B}]
      (implementation_escapeEach [{_SAFE_A}, {_UNSAFE_B}]) := by
  unfold problem_spec_escapeEach
  intro hh
  simp [implementation_escapeEach, Id.run] at hh
  injection hh with h1 h2
  injection h2 with h3
  exact h h3.symm
""",
})

# ---------------------------------------------------------------------------
# (4) FORCE-MARKED-SAFE: apply the escaping decision to a RECONSTRUCTED element
#     that is always marked safe, discarding the input element's own marking.
#     This is nagini's `partial-domain-reescape-safe` dual and its
#     `flag-result-not-marked-safe` argument fused into the shape this carrier
#     admits: on this backend the safe-marking is an INPUT observable the escaper
#     branches on, so the rival that ignores it is the one that must be refuted.
#     Attacks: "the argument each entry is computed from", on the not-safe
#     sub-domain.
# ---------------------------------------------------------------------------
_RIV_FORCE_SAFE = """  let mut acc := []
  for obj in value do
    acc := acc ++ [condEscape { isSafe := true, text := obj.text }]
  return acc"""

SPEC_TESTS.append({
    "id": "ignore-marking-treat-all-as-safe",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _IMPL, _RIV_FORCE_SAFE),
    "refinement": (
        "A faithful real version passes each element to the shared escaper "
        "already marked safe, so the escaper's leave-untouched branch always "
        "fires and ordinary text is never escaped. The tests pin that a sequence "
        "of ORDINARY text renders with its special characters escaped; this rival "
        "renders them raw, so it fails the ordinary-text half of every "
        "FAIL_TO_PASS assertion. It would NOT resolve."),
    "rationale": (
        "Rejected by the entry clause of `result = value.map condEscape`: the "
        "entry is the escaper applied to an element whose marking has been "
        "overwritten, not to `value[i]` as given. Refuted at a singleton input "
        "whose element is NOT marked safe -- the sub-domain where overwriting the "
        "marking changes the argument -- conditioned on the single fact that the "
        "escaper distinguishes the two markings of that text."),
    "witness": f"""
-- The rival computes the entry from an element whose marking has been forced;
-- the spec computes it from the element as given. On a not-marked-safe element
-- those are two different arguments, so assuming only that the escaper tells
-- them apart refutes the rival. (Gold's entry is the given element's own value,
-- so this same statement does not hold of it.)
example (h : condEscape {_SAFE_A} ≠ condEscape {_UNSAFE_A}) :
    ¬ problem_spec_escapeEach [{_UNSAFE_A}]
      (implementation_escapeEach [{_UNSAFE_A}]) := by
  unfold problem_spec_escapeEach
  intro hh
  simp [implementation_escapeEach, Id.run] at hh
  injection hh with hx
  exact h hx
""",
})

# ---------------------------------------------------------------------------
# (5) FORCE-NOT-MARKED-SAFE: the mirror sub-domain. Reconstruct each element as
#     NOT marked safe, so the escaper's escaping branch always fires and content
#     already marked safe is escaped a second time. This is nagini's
#     `partial-domain-reescape-safe` (the double-escape bug) on its own
#     sub-domain, and it is a genuinely different rival from (4): each is correct
#     exactly where the other is wrong, so they get witnesses at DIFFERENT
#     inputs (marked-safe vs not-marked-safe) rather than sharing one.
#     Attacks: "the argument each entry is computed from", on the safe sub-domain.
# ---------------------------------------------------------------------------
_RIV_FORCE_UNSAFE = """  let mut acc := []
  for obj in value do
    acc := acc ++ [condEscape { isSafe := false, text := obj.text }]
  return acc"""

SPEC_TESTS.append({
    "id": "ignore-marking-treat-all-as-unsafe",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _IMPL, _RIV_FORCE_UNSAFE),
    "refinement": (
        "A faithful real version strips each element's safe-marking before "
        "handing it to the shared escaper, so the escaping branch fires even for "
        "content already marked safe and that content is escaped a SECOND time. "
        "The tests pin that a sequence of already-marked-safe elements renders "
        "UNCHANGED alongside the ordinary-text half; this rival renders those "
        "elements with their special characters replaced, so it fails the "
        "marked-safe half of the assertions that exercise it. It would NOT "
        "resolve."),
    "rationale": (
        "Rejected by the same entry clause as (4) but on the COMPLEMENTARY "
        "sub-domain, so it needs its own witness input: refuted at a singleton "
        "whose element IS marked safe, where stripping the marking changes the "
        "argument. Conditioned on the single fact that the escaper distinguishes "
        "the two markings of that text."),
    "witness": f"""
-- Mirror of (4): here the rival strips the marking, so the disagreement is on
-- the marked-safe sub-domain. Probed at a marked-safe singleton -- the input at
-- which the previous rival is CORRECT -- so this witness demonstrates the
-- sub-domain its rationale claims.
example (h : condEscape {_SAFE_A} ≠ condEscape {_UNSAFE_A}) :
    ¬ problem_spec_escapeEach [{_SAFE_A}]
      (implementation_escapeEach [{_SAFE_A}]) := by
  unfold problem_spec_escapeEach
  intro hh
  simp [implementation_escapeEach, Id.run] at hh
  injection hh with hx
  exact h hx.symm
""",
})

# ---------------------------------------------------------------------------
# (6) ARITY: drop the last element. The direct port of nagini's
#     `arity-drop-last-element`. Every surviving entry is exactly right, so this
#     rival is refutable ONLY through the length half of the clause -- which is
#     fully transparent even though the entries are opaque.
#     Attacks: "length".
# ---------------------------------------------------------------------------
_RIV_TRUNCATE = """  let mut acc := []
  let mut i := 0
  for obj in value do
    if i + 1 < value.length then
      acc := acc ++ [condEscape obj]
    i := i + 1
  return acc"""

SPEC_TESTS.append({
    "id": "arity-drop-last-element",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _IMPL, _RIV_TRUNCATE),
    "refinement": (
        "A faithful real version returns one entry short of the input sequence. "
        "The tests render two-element sequences joined by a separator and pin the "
        "full joined text; a result missing its final entry renders only the "
        "first element and drops both the separator and the second element, so "
        "every FAIL_TO_PASS assertion sees a shorter string than expected. It "
        "would NOT resolve."),
    "rationale": (
        "Rejected by the LENGTH half of `result = value.map condEscape`: "
        "`(value.map condEscape).length = value.length`, so a result of length 1 "
        "cannot equal the specified value at a two-element input. Needs no "
        "assumption about the escaper at all -- the surviving entry is correct, "
        "and the refutation is purely structural. Probed at a two-element input "
        "mixing a not-marked-safe and a marked-safe element."),
    "witness": f"""
-- Purely structural: the rival returns one entry for a two-element input, and
-- the specified result has one entry per element. No property of the escaper is
-- assumed, and the witness binds nothing.
example : ¬ problem_spec_escapeEach [{_UNSAFE_A}, {_SAFE_B}]
    (implementation_escapeEach [{_UNSAFE_A}, {_SAFE_B}]) := by
  unfold problem_spec_escapeEach
  intro hh
  have hl : (implementation_escapeEach [{_UNSAFE_A}, {_SAFE_B}]).length = 1 := rfl
  rw [hh] at hl
  simp at hl
""",
})

# ---------------------------------------------------------------------------
# (6b) ARITY, THE OTHER DIRECTION: emit one entry TOO MANY by repeating the
#      final element's escaping decision. `(6)` probes a result one entry SHORT;
#      nothing in the battery probed a result one entry LONG, and the two are
#      independent halves of `(value.map condEscape).length = value.length` --
#      a spec that pinned only a lower bound on the length would reject `(6)` and
#      accept this. Every entry present is correct and in the right order, so
#      like `(6)` this is refutable ONLY through the length half, and needs no
#      assumption about the escaper. Attacks: "length", from above.
# ---------------------------------------------------------------------------
_RIV_DUPLICATE_LAST = """  let mut acc := []
  for obj in value do
    acc := acc ++ [condEscape obj]
  match acc.getLast? with
  | some z => return acc ++ [z]
  | none => return acc"""

SPEC_TESTS.append({
    "id": "arity-duplicate-last-element",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _IMPL, _RIV_DUPLICATE_LAST),
    "refinement": (
        "A faithful real version returns one entry MORE than the input sequence, "
        "repeating the last element's escaped value. The tests render two-element "
        "sequences joined by a separator and pin the full joined text; a result "
        "carrying a third, duplicated entry renders an extra separator and an "
        "extra copy of the final element, so the rendered string is longer than "
        "the expected one on every FAIL_TO_PASS assertion. It would NOT resolve."),
    "rationale": (
        "Rejected by the LENGTH half of `result = value.map condEscape`, from the "
        "opposite side to `arity-drop-last-element`: "
        "`(value.map condEscape).length = value.length`, so a result of length 3 "
        "cannot equal the specified value at a two-element input. Needs no "
        "assumption about the escaper -- every entry present is the correct one in "
        "the correct position, and the refutation is purely structural. Probed at "
        "the same two-element input as (6) so the two length directions are "
        "compared at one point."),
    "witness": f"""
-- Purely structural, and the mirror of (6): the rival returns THREE entries for
-- a two-element input, and the specified result has one entry per element. No
-- property of the escaper is assumed, and the witness binds nothing.
example : ¬ problem_spec_escapeEach [{_UNSAFE_A}, {_SAFE_B}]
    (implementation_escapeEach [{_UNSAFE_A}, {_SAFE_B}]) := by
  unfold problem_spec_escapeEach
  intro hh
  have hl : (implementation_escapeEach [{_UNSAFE_A}, {_SAFE_B}]).length = 3 := rfl
  rw [hh] at hl
  simp at hl
""",
})

# ---------------------------------------------------------------------------
# (7) ORDER: build the result back-to-front. No nagini counterpart names this
#     directly (nagini's per-index Forall covers it, and its sequence rivals
#     attacked arity instead), but the frozen clause pins ORDER as an independent
#     property of the same equation, and an order-reversing rival keeps both the
#     length and the multiset of entries exactly right -- so no other rival here
#     would catch it. Attacks: "order".
# ---------------------------------------------------------------------------
_RIV_REVERSE = """  let mut acc := []
  for obj in value do
    acc := [condEscape obj] ++ acc
  return acc"""

SPEC_TESTS.append({
    "id": "order-reversed",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _IMPL, _RIV_REVERSE),
    "refinement": (
        "A faithful real version returns the escaped elements in the opposite "
        "order from the input sequence. The tests join a two-element sequence and "
        "pin the joined text with the first input element FIRST; this rival "
        "renders the elements swapped, so the joined string differs from the "
        "expected one on every FAIL_TO_PASS assertion (each uses a two-element "
        "input whose elements are distinct). It would NOT resolve."),
    "rationale": (
        "Rejected by the ORDER half of `result = value.map condEscape`: the map "
        "puts the escaping decision for `value[0]` at index 0. Length and the set "
        "of entries are both untouched by this rival, so only the positional "
        "clause refutes it. Conditioned on the single fact that the escaper "
        "distinguishes the two (distinct-text) elements of the probed input, "
        "which is what makes the swap observable."),
    "witness": f"""
-- Length and entry multiset are both correct here; only the positions differ.
-- Assuming the escaper separates the two elements (necessary -- if it mapped
-- both to the same string the swap would be unobservable and the rival would
-- not be wrong at this input) refutes the rival at index 0.
example (h : condEscape {_UNSAFE_B} ≠ condEscape {_UNSAFE_A}) :
    ¬ problem_spec_escapeEach [{_UNSAFE_A}, {_UNSAFE_B}]
      (implementation_escapeEach [{_UNSAFE_A}, {_UNSAFE_B}]) := by
  unfold problem_spec_escapeEach
  intro hh
  simp [implementation_escapeEach, Id.run] at hh
  injection hh with hx
  exact h hx
""",
})
