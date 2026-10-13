"""properties.py — G-PBT falsification battery for django__django-13315 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct selectEligible`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a finite list of candidate items).
The single obligation is

    selectEligible (rows : List Candidate)
        ensures out = keepMatching rows

with ``keepMatching`` mapping, element by element and in order,
``keep c = if c.witnesses > 0 then [c.id] else []``: an eligible candidate
(``witnesses > 0``) contributes its identity EXACTLY ONCE, an ineligible one
contributes nothing, and — decisively — the contribution does NOT scale with
the candidate's witness multiplicity. The load-bearing content is that
multiplicity collapse: a candidate eligible along SEVERAL witnesses is still
offered once, where the pre-image emitted it once PER witness.

``rows`` is the sole input binder; each element carries ``id`` (the candidate's
stable identity) and ``witnesses`` (how many distinct ways it satisfies the
constraint). There is no ``require`` clause and no opaque answer key to echo:
``out = keepMatching rows`` grounds the result in the actual input via the
transparent ``pure``-region fold (directive 8).

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``Candidate`` is a two-field structure with ``DecidableEq`` and ``keep`` /
``keepMatching`` are concrete ``def``s in the ``pure`` region (the ``axioms``
region declares nothing). So each rival's violation reduces to a decidable
equality of concrete values, and a ``decide`` witness at a small literal input
discriminates. The reject lane is therefore fully expressible on this carrier —
no NO-REJECT-LANE collapse.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the loop collapsed to the closed form the
    post-image names; the per-candidate contribution bound to a local) must
    still verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries NO ``require`` clause, so the sibling's
    precondition-inhabitation probe has no precondition to admit. The residual
    risk on this transparent carrier is instead a DEGENERATE post-image: that it
    does not actually demand a SINGLE emission on a multiply-eligible candidate
    while dropping an ineligible one. ``admiss-grounded`` discharges an in-region
    assert pinning BOTH arms of the per-candidate decision at an F2P-shaped
    point; the impl is kept verbatim so the method's own obligation still
    discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only heap input may carry a fractional permission an impl
    overwrites. Lean and Velvet are referentially transparent: ``rows`` is an
    immutable value (declared read-only, not ``mut``), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe to
    build. Not fabricated — reported as an omission in the footer.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired behaviour on some sub-domain and MUST be rejected:
    the raw multiplicity emission (the literal pre-image bug), the inverted
    eligibility guard (drop singly-eligible candidates), the wrong-identity
    contribution, and the special-cased first element. Each is a loop-free
    closed form (so its tester kernel-reduces) with a machine-checked refutation
    witness.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``selectEligibleTester rows = false`` says the extracted
program's result violates the postcondition at that concrete input, checked in a
file whose ``prove_correct`` block has been stripped (no tactic script can mask
the verdict). Every reject rival is reshaped into a LOOP-FREE closed form, so
ITS tester kernel-reduces and the witness ``decide``s against it.

THE FROZEN IMPL CANNOT SERVE AS THE SECOND SUBJECT, and this battery says so
explicitly rather than banking the exit code. The frozen program keeps a
``while`` loop; under ``loom.semantics.choice "demonic"`` its fixpoint
elaborates through ``Classical.choice``, which the kernel cannot unfold, so
``decide`` against the frozen tester is stuck for EVERY claim regardless of
truth. Measured directly on this bundle — three builds, one identical error
(``... did not reduce to `isTrue` or `isFalse` ... reduction got stuck at the
`Decidable` instance``):

  * the real witness            ``selectEligibleTester [⟨7,2⟩] = false``  -> exit 1
  * the exact OPPOSITE claim    ``selectEligibleTester [⟨7,2⟩] = true``   -> exit 1
  * a trivial claim, empty list ``selectEligibleTester [] = true``        -> exit 1

So the frozen side's failure is not a refutation and would attest to a
discrimination never performed (a forged witness asserting a rival CORRECT would
clear both halves). Every reject case therefore names ``witness_reference``:
``_LOOPFREE``, the loop-free closed-form impl of the SAME frozen spec — the very
source shipped as the ``pos-closed-form`` positive, so the battery itself records
that loop-freeness is not what any rival is rejected for, and the gate
independently checks the reference shares the spec and VERIFIES before refuting
against it. An impl the verifier accepts cannot violate its own spec, so a
genuine witness must still fail there. Confirmed out of band, per witness: green
against its rival (exit 0), and against ``_LOOPFREE`` a REAL verdict — ``decide``
*proved the proposition false* — not a stuck reduction; and the agreement-point
control ``selectEligibleTester [⟨7,2⟩] = true`` exits 0 against ``_LOOPFREE``,
so the reference decides in BOTH directions.

WITNESS PLACEMENT. The four rejects probe four DISTINCT input points, so the
input binder ``rows`` — and the ``id`` / ``witnesses`` fields it carries — is
genuinely varied rather than pinned. ``witnesses`` ranges over the
multiply-eligible arm (≥ 2), the singly-eligible arm (= 1) and the ineligible
arm (= 0); ``rows.length`` ranges over 1 and 2; and both arms of ``keep``
(eligible → single id, ineligible → nothing) are attacked.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the collection-
narrowing primitive is modeled deeply as the ``keepMatching`` fold (an
A-reference, G-AX's job), not a consumed contract. The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13315"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the candidates. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`).
_IMPL = """    let mut result : List Int := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = keepMatching (rows.drop i)
      done_with i = 0
      decreasing i
    do
      let c := rows[i - 1]!
      result := keep c ++ result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "selectEligible impl region drifted from expected text"

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let c := rows[i - 1]!
      result := keep c ++ result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop body drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut result : List Int := []"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this to a bare `loom_solve`; the tactic body is
# elided from the spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct selectEligible by
  loom_solve
  rw [keepMatching_drop_step rows i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---------------------------------------------------------------------------
# THE WITNESS SUBJECT. `_LOOPFREE` collapses the accumulating loop to the closed
# form the post-image names directly, and retunes the loop-specific proof to a
# bare `loom_solve` (the impl now matches the post-image syntactically). It is a
# CORRECT impl of the frozen spec — shipped below, unchanged, as the
# `pos-closed-form` positive, so the battery itself records that loop-freeness is
# not what any rival is being rejected for.
#
# It exists because the FROZEN impl cannot serve as the reject lane's second
# subject: its `while` loop elaborates through `Classical.choice` under
# `loom.semantics.choice "demonic"`, so `decide` against the frozen tester is
# stuck for every claim, true or false (measured — see the module docstring), and
# its exit code discriminates nothing. Every reject case names this as its
# `witness_reference`; the gate checks it shares the frozen spec and VERIFIES
# before refuting a witness against it, and an impl the verifier accepts cannot
# violate its own spec.
# ---------------------------------------------------------------------------
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL, "    return (keepMatching rows)"),
    _PROOF, "prove_correct selectEligible by\n  loom_solve")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `selectEligibleTester rows = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
_TESTER = (
    "extract_program_for selectEligible\n"
    "prove_precondition_decidable_for selectEligible\n"
    "prove_postcondition_decidable_for selectEligible\n"
    "derive_tester_for selectEligible\n\n"
)


def _witness(rows_literal):
    return _TESTER + f"example : selectEligibleTester {rows_literal} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = keepMatching rows`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same narrowed identity list; the loop-
        # specific proof is retuned to a bare `loom_solve` since the impl now
        # matches the post-image syntactically. This is the SAME source every
        # reject case names as its `witness_reference` — shipped here as a
        # first-class positive so the battery records that loop-freeness verifies
        # and is therefore not what any rival is being rejected for.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that returns the narrowed identity list "
                     "directly must satisfy `out = keepMatching rows`; a correct "
                     "reshape of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Exercises the obligation from a "
                     "maximally different (loop-free) control-flow shape. Doubles "
                     "as the reject lane's `witness_reference`: because this impl "
                     "verifies, it cannot violate its own spec, so a witness that "
                     "fails against it is refuting the RIVAL and not loop-freeness. "
                     "(Sibling: pos-reorder.)",
    },
    {
        "id": "pos-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-candidate contribution to a local `k` inside the
        # loop instead of prepending the expression directly. Same value flow;
        # the loop and the front-recursive invariant are unchanged, so the frozen
        # proof still closes untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let c := rows[i - 1]!\n"
            "      let k : List Int := keep c\n"
            "      result := k ++ result\n"
            "      i := i - 1"),
        "rationale": "binding the per-candidate contribution to a local before "
                     "prepending it computes the same list element-for-element, "
                     "with the loop and invariant unchanged, so the frozen proof "
                     "closes and `out = keepMatching rows` still holds; a correct "
                     "reshape must verify. (Sibling: pos-reshape.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so the sibling's
    # precondition-inhabitation probe has nothing to admit. The residual risk on
    # this transparent carrier is that the post-image is DEGENERATE at the
    # interesting point (a spec no impl can meet reads like a spec every impl
    # meets). This case discharges an in-region assert at an F2P-shaped point,
    # establishing that the post-image really does demand a SINGLE emission on a
    # multiply-eligible candidate AND nothing on an ineligible one — the two arms
    # of the per-candidate decision. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live (a false claim
    # about the same point leaves an unsolved goal), and the proof's alternation
    # gains one `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `assert\n"
                "      (keepMatching [{id := 7, witnesses := 2}] = [7] ∧\n"
                "       keepMatching [{id := 9, witnesses := 0}] = []))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct selectEligible by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [keepMatching_drop_step rows i (by omega) (by omega)]; simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: it demands a candidate eligible along "
                     "SEVERAL witnesses be offered EXACTLY ONCE (not once per "
                     "witness) and an ineligible candidate be dropped. The in-region "
                     "assert must discharge (else the obligation is degenerate / "
                     "PRECOND-TOO-STRONG-analogue); the impl is kept verbatim so "
                     "`out = keepMatching rows` still verifies. (Sibling: "
                     "admiss-stream, re-aimed — no `require` clause to inhabit.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "raw-multiplicity",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: emit each candidate ONCE PER witness rather
        # than once. Correct on every candidate with 0 or 1 witnesses; diverges
        # exactly on the multiply-eligible sub-domain — the case the desired
        # behaviour collapses. This is the literal pre-patch skeleton
        # (identical to Solution_prepatch.lean's do-block, closed form).
        "module": _swap(
            _BASE, _IMPL,
            "    return (rows.flatMap (fun c => List.replicate c.witnesses c.id))"),
        "refinement": "this is the LITERAL pre-image: narrowing the candidate "
                      "collection by the inner-join constraint emits one identity "
                      "per satisfying witness (no deduplication), so a candidate "
                      "satisfying the constraint along several witnesses is offered "
                      "MULTIPLE times. The failing test compares the offered "
                      "identities as a multiset against each-candidate-once and "
                      "would FAIL — it is exactly the duplicate-options bug the fix "
                      "removes, so it would NOT resolve. (Sibling: "
                      "keep-all-raw-stream.)",
        "rationale": "REJECT from `out = keepMatching rows`: at a one-element list "
                     "whose candidate has ≥ 2 witnesses, the post-image demands a "
                     "single-element contribution `[id]` while the impl emits `id` "
                     "repeated `witnesses` times. Refuted on the multiply-eligible "
                     "sub-domain (`witnesses ≥ 2`).",
        "witness": _witness("[⟨7, 2⟩]"),
        # gold's `while` loop cannot decide this (or any) claim; refute against
        # the verifying loop-free impl instead. Confirmed: `decide` PROVED the
        # proposition false against `_LOOPFREE` — a real verdict, not a stuck
        # reduction.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "invert-guard-drop-singly",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the eligibility guard: offer a candidate ONLY when it satisfies
        # the constraint along ≥ 2 witnesses, dropping singly-eligible ones.
        # Correct on ineligible (0) and multiply-eligible (≥ 2) candidates;
        # diverges on the singly-eligible sub-domain, which it drops.
        "module": _swap(
            _BASE, _IMPL,
            "    return (rows.flatMap (fun c => if c.witnesses ≥ 2 then [c.id] else []))"),
        "refinement": "a counterpart that offered a candidate only when it "
                      "satisfied the constraint along MORE THAN ONE witness would "
                      "DROP a genuinely-eligible candidate that satisfies it along "
                      "exactly one — the failing test expects EVERY eligible "
                      "candidate offered (each satisfying the constraint at least "
                      "once); a singly-eligible one would vanish and the test would "
                      "FAIL — it would NOT resolve. (Sibling: "
                      "invert-guard-drop-singletons.)",
        "rationale": "REJECT from `out = keepMatching rows`: at a one-element list "
                     "whose candidate has exactly one witness, the post-image "
                     "demands the single contribution `[id]` while the impl drops "
                     "it. Refuted on the singly-eligible sub-domain (`witnesses = "
                     "1`) — the arm raw-multiplicity agrees with gold on.",
        "witness": _witness("[⟨5, 1⟩]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Right SHAPE (eligible → one contribution, ineligible → none), wrong
        # identity: contribute a DIFFERENT identity (a shifted id) for each
        # eligible candidate. Correct count, wrong objects — attacks whether the
        # post-image pins the EXACT contributed identity.
        "module": _swap(
            _BASE, _IMPL,
            "    return (rows.flatMap (fun c => if c.witnesses > 0 then [c.id + 1] else []))"),
        "refinement": "a counterpart that offered the RIGHT NUMBER of options but "
                      "with the wrong identity (a shifted primary key) would offer "
                      "candidates that were never eligible and omit the eligible "
                      "ones; the failing test reads back the eligible candidates by "
                      "identity and would get different objects — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = keepMatching rows`: for an eligible "
                     "candidate the post-image pins the contributed value to `c.id`, "
                     "and the impl contributes `c.id + 1`. Refuted at an eligible "
                     "candidate (with a distinct multiplicity, `witnesses = 3`, so "
                     "`witnesses` is not held fixed) — a near-miss the "
                     "raw-multiplicity rival (wrong COUNT) does not subsume.",
        "witness": _witness("[⟨8, 3⟩]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "keep-first-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # Special-case the FIRST candidate: offer its identity unconditionally
        # (even when ineligible) and narrow the rest correctly. Correct on every
        # input whose first candidate is eligible; wrong when the first candidate
        # is ineligible — it re-introduces an option that should not appear.
        # Refuted at a two-element list beginning with an ineligible candidate
        # (so `rows.length` is varied beyond one).
        "module": _swap(
            _BASE, _IMPL,
            "    return (match rows with\n"
            "      | [] => []\n"
            "      | c :: cs => c.id :: keepMatching cs)"),
        "refinement": "a counterpart that special-cased the first candidate — "
                      "offering it unconditionally even when it does not satisfy the "
                      "constraint — would put an ineligible candidate into the "
                      "offered options on exactly a collection that begins with one; "
                      "the failing test asserts only eligible candidates are offered "
                      "and would FAIL — it would NOT resolve.",
        "rationale": "REJECT from `out = keepMatching rows`: at the head position "
                     "the rival always contributes `[id]` where `keep` contributes "
                     "`[]` for an ineligible candidate. Refuted at a two-element "
                     "list whose first candidate is ineligible (`witnesses = 0`) — "
                     "the only reject varying `rows.length` beyond one, exercising "
                     "the ineligible (drop) arm of `keep` and the traversal head. "
                     "(Sibling: partial-keep-first.)",
        "witness": _witness("[⟨9, 0⟩, ⟨5, 1⟩]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (2
# soundness positives, 1 admissibility, 1 frame-mutation rival, 3
# uniqueness/partial-domain rivals) plus a 2-case AXIOM lane. The sibling
# contracts one function, `offered_options`, over a raw match STREAM (a
# List[int] holding one occurrence per satisfying join path) held at a
# fractional heap permission, and its postcondition is a duplicate-free image,
# `ToSeq(Result()) == dedup(ToSeq(matches))`. This bundle contracts one method,
# `selectEligible`, over a List of candidates each carrying its witness
# multiplicity, and its postcondition is the per-candidate fold
# `out = keepMatching rows` (eligible -> [id] once, ineligible -> []). The two
# surfaces model the SAME multiplicity-collapse: nagini folds "how many times a
# row recurs" into repeated stream elements, velvet folds it into the
# `witnesses` count. The port is near-1:1 with two carrier consequences: the
# frame-mutation rival is vacuous here, and the admissibility case is re-aimed
# because this method declares no `require` clause.
#
#   sibling case              kind          -> here                    disposition
#   ---------------------------------------------------------------------------
#   pos-reorder               soundness     -> pos-closed-form         RE-EXPRESSED
#   pos-reshape               soundness     -> pos-letbind             PORTED
#   admiss-stream             admissibility -> admiss-grounded         RE-AIMED
#   frame-write-matches       uniqueness    -> (none)                  VACUOUS
#   keep-all-raw-stream       uniqueness    -> raw-multiplicity        PORTED
#   invert-guard-drop-singletons uniqueness -> invert-guard-drop-singly PORTED
#   partial-keep-first        uniqueness    -> keep-first-unconditional PORTED
#   (—)                       uniqueness    -> wrong-identity          ADDED
#   AXIOM_TESTS (2)           axiom         -> (none)                  G-AX
#
# RE-EXPRESSED (pos-reorder -> pos-closed-form): the sibling's branch reorder
#   keeps the backward scan and every loop invariant. On this carrier the closest
#   "maximally different but correct" reshape is the loop-free closed form the
#   post-image names directly (`keepMatching rows`); the loop-specific proof
#   collapses to a bare `loom_solve`. The ARGUMENT (a faithful correct impl must
#   verify, else SPEC-TOO-STRONG) is carried unchanged.
# PORTED (pos-reshape -> pos-letbind): the sibling hoists the membership test into
#   a typed local; here we bind the per-candidate contribution `keep c` to a local
#   before prepending it, keeping the loop and the front-recursive invariant so the
#   frozen proof closes untouched.
# RE-AIMED (admiss-stream -> admiss-grounded): the sibling's admissibility case
#   builds an F2P-shaped raw stream and shows the fractional-permission Requires
#   admits it. This method declares NO `require` clause (pre-conditions region
#   empty), so there is no precondition to inhabit. The sharper residual risk on
#   this transparent carrier is a DEGENERATE post-image, so the case is re-aimed to
#   a live in-region assert pinning BOTH arms of the per-candidate decision (single
#   emission on a multiply-eligible candidate, nothing on an ineligible one) at the
#   F2P point. Reported as a re-aim, not a straight port.
# VACUOUS (frame-write-matches): the sibling's MANDATORY frame-mutation rival
#   writes to the half-permission read-only `matches`. This backend is referentially
#   transparent and `rows` is declared read-only (not `mut`), so there is no
#   read-only input to overwrite and no substitute probe. Omitted as vacuous per the
#   porting map, NOT fabricated.
# PORTED (the three value rivals): keep-all-raw-stream ports directly to
#   raw-multiplicity (emit each candidate once per witness — the literal pre-image,
#   refuted on the multiply-eligible sub-domain). invert-guard-drop-singletons ports
#   to invert-guard-drop-singly (offer only candidates with >= 2 witnesses, dropping
#   singly-eligible ones — refuted on the singly-eligible sub-domain). partial-keep-
#   first ports to keep-first-unconditional (offer the first candidate always, even
#   when ineligible — refuted at a two-element list beginning with an ineligible
#   candidate).
# ADDED (wrong-identity): a near-miss that emits the RIGHT count with the WRONG
#   identity (a shifted id), attacking whether the post-image pins the EXACT
#   contributed value rather than merely its multiplicity. Refuted at an eligible
#   candidate; the mutation gate (G-MUT killed 15/15) exercises this class on the
#   sibling implicitly, and it fills the "right shape, wrong value" slot the three
#   ported multiplicity/guard rivals leave open.
# DROPPED (weak-reversed candidate — NOT shipped): a rival resolving each candidate
#   correctly but reversing the traversal order was considered and REJECTED as an
#   illegitimate reject. The failing test compares the offered identities as a
#   MULTISET (order-insensitive, `assertCountEqual`), so a faithful order-reversing
#   patch WOULD still resolve the F2P; a reject case for it would claim a
#   verify-does-not-imply-resolve break that does not exist. The order clause is
#   genuinely NOT part of the observed behaviour on this instance, so it is dropped
#   rather than shipped — `rows.length` is instead varied by keep-first-unconditional
#   (length 2), which attacks a real defect.
# DIVERGENCE LANE - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job (the sibling's
#   dedup/occurs A-reference is validated against the real distinct-matching
#   semantics there); the multiplicity-collapse is modeled deeply here as the
#   `keepMatching` fold (an A-reference with no consumed axiom), and this gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `rows : List Candidate`, whose elements carry `id` and `witnesses`, and one
#   top-level clause, `out = keepMatching rows`, which internally branches on
#   `witnesses > 0` and pins the contributed value to `c.id`. The four reject
#   witnesses probe four DISTINCT input points (pts=4): a single multiply-eligible
#   candidate (⟨7,2⟩), a single singly-eligible candidate (⟨5,1⟩), a single
#   eligible candidate at a third multiplicity (⟨8,3⟩), and a two-element list led
#   by an ineligible candidate (⟨9,0⟩,⟨5,1⟩). Thus `witnesses` ranges over
#   {0,1,2,3}, `id` over {5,7,8,9}, and `rows.length` over {1,2} — none held fixed.
#   Both arms of `keep` are attacked (the eligible arm by raw-multiplicity /
#   invert / wrong-identity, the ineligible arm by keep-first-unconditional), the
#   exact contributed identity is pinned (wrong-identity), and the multiplicity
#   collapse — the load-bearing content — is attacked directly (raw-multiplicity).
#   No rival that mishandled only a fixed-value binder could slip through.
#
# WITNESS-SUBJECT REPAIR (why every reject case carries `witness_reference`).
#   An earlier revision of this battery stated the same four witnesses and let the
#   gate refute them against the FROZEN solution. All four came back
#   `witness-undecided` (recorded verdict MALFORMED-TESTS): the frozen impl's
#   `while` loop elaborates through `Classical.choice`, so the kernel's `decide`
#   is stuck on the frozen tester for EVERY claim and its exit code attests to a
#   refutation never performed. Diagnosed by three hand-run builds against gold —
#   the real witness, the exact opposite claim, and a trivial claim about `[]` —
#   which all failed with the identical `did not reduce to `isTrue` or `isFalse``.
#   The witnesses themselves were never the defect: each already built green
#   against its rival.
#
#   The gate's preferred repair — restate the refutation over a COMPUTABLE
#   PROJECTION — is not available on this carrier. The postcondition is reached
#   only through the extracted `selectEligibleExec`/`selectEligibleTester`, and
#   the loop sits UPSTREAM of every observable: there is no sum, length or single
#   coordinate of the result whose reduction bypasses the loop's fixpoint, so
#   every projection is stuck at the same `Classical.choice`. Hence the documented
#   second route, `witness_reference` = `_LOOPFREE`. Re-confirmed by hand, per
#   witness: exit 0 against the rival, and against `_LOOPFREE` a REAL verdict
#   (`decide` *proved the proposition false*) rather than a stuck reduction —
#   plus an agreement-point control (`... [⟨7,2⟩] = true`) that exits 0 against
#   `_LOOPFREE`, establishing the reference decides in BOTH directions and so is
#   not an impl that merely fails everything. The rival sources, the witnesses and
#   the input points are UNCHANGED from the revision that was gated; only the
#   subject the second half is checked against moved.
AXIOM_TESTS = []
