"""properties.py — G-PBT falsification battery for django__django-11951 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct effectiveBatchSize`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method deriving a single effective chunk size
from two read-only counts:

  effectiveBatchSize (batchSize maxBatchSize : Nat)
      require  maxBatchSize ≥ 1
      ensures  (batchSize = 0 → n = maxBatchSize)
             ∧ (batchSize > 0 → n = min batchSize maxBatchSize)

Both inputs are plain ``Nat`` value binders — there is no heap, no aliasing, no
``mut`` frame — and the postcondition is TOTAL/functional: it pins ``n`` to a
unique value on the whole domain. ``batchSize = 0`` is the "unspecified" branch
(the caller made no request); ``batchSize > 0`` is the explicit-request branch,
where the request is CAPPED at the store maximum (the smaller of the two wins).
The ``require maxBatchSize ≥ 1`` clause IS the store's floor-at-one guarantee —
the maximum is never reported as zero.

The postcondition has two independent top-level clauses joined by ``∧``:

  * clause A — ``batchSize = 0 → n = maxBatchSize`` (the unspecified branch pins
    the result to the store maximum);
  * clause B — ``batchSize > 0 → n = min batchSize maxBatchSize`` (the explicit
    branch pins the result to the capped minimum).

Both INPUT BINDERS (``batchSize``, ``maxBatchSize``) are varied across the reject
witnesses below, and BOTH clauses are attacked by some rival. Clause B is attacked
on BOTH sides of the cap: above it (the request must be tightened) and strictly
below it (the request must be honoured unchanged).

The failing test issues an explicit over-large request (``batchSize = max + 1``)
and asserts a fixed, small query count: the effective size must be capped at the
store maximum, so ``ceil(len(objs) / max)`` chunks are produced, not
``ceil(len(objs) / (max + 1))``. In carrier terms that is exactly clause B at
``batchSize > maxBatchSize`` — any rival that returns ``batchSize`` (or
``max + 1``) there does NOT resolve.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries this class
    because a read-only input may hold a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: both parameters are
    immutable ``Nat`` values, no ``mut`` binder is declared, there is no heap and
    no aliasing — so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated (see footer).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. Both clauses are pinned to ``maxBatchSize`` and
    ``min batchSize maxBatchSize`` — total, fully-transparent functions of the
    method's own inputs. There is no opaque answer key to echo; evaluating
    ``min`` IS the correct answer, so there is no WRONG echo to build. Honest
    cheapest-reshape positive controls stand in.
  * PARTIAL-DOMAIN / VALUE — APPLIES: each rival is right on part of the domain
    and diverges on exactly one sub-domain the F2P/P2P inputs reach.

WITNESS MECHANICS on this carrier. The spec is a ``method`` CONTRACT, not a bare
predicate, so a witness reaches the postcondition through Velvet's own tester
machinery: ``effectiveBatchSizeTester b m = false`` says the extracted program's
result violates the method's postcondition at the concrete input ``(b, m)``. It
is checked in a file whose ``prove_correct`` block has been stripped (so no
tactic script can interfere), and both halves are enforced by the gate: the
witness ELABORATES against the rival (its result provably violates the spec at
that point) and FAILS against the frozen solution (``decide`` proves the frozen
tester is NOT false there — a real discriminator, not a tautology). Every impl
here is straight-line, so its extracted tester reduces and ``decide`` settles it;
inputs are small concrete ``Nat`` literals inside the domain (``maxBatchSize ≥
1``), so no conditioning on an opaque carrier is needed. No
``sorry``/``admit``/``native_decide``/``axiom``.
"""
from pathlib import Path

INSTANCE = "django__django-11951"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole executable body: the two-branch derivation
# ---- (unspecified → store maximum; explicit → capped minimum). It lies wholly
# ---- inside the one impl region and is unique in the file (both facts asserted
# ---- at load by _swap). Every variant replaces exactly this block. ----
_IMPL = (
    "    if batchSize = 0 then\n"
    "      return maxBatchSize\n"
    "    else\n"
    "      return min batchSize maxBatchSize\n"
)

# The initial line of the impl region (unique). Anchor for the admissibility
# in-region assert, which is prepended before the frozen body.
_IMPL_HEAD = "    if batchSize = 0 then\n"


# ---- witness preamble. Reaches the method's postcondition through Velvet's
# ---- tester machinery. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. ----
_TESTER = (
    "\n"
    "extract_program_for effectiveBatchSize\n"
    "prove_precondition_decidable_for effectiveBatchSize\n"
    "prove_postcondition_decidable_for effectiveBatchSize\n"
    "derive_tester_for effectiveBatchSize\n\n"
)


def _witness(batch, mx):
    return (_TESTER +
            f"example : effectiveBatchSizeTester {batch} {mx} = false := by\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the identical theorem statement;
    # only the executable surface moves and the proof stays `loom_solve`.
    # =====================================================================
    {
        "id": "pos-explicit-branch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: spell the cap as an explicit two-way comparison instead of the
        # `min` combinator. On the explicit branch, return `batchSize` when it is
        # within the store maximum and the maximum otherwise — which IS
        # `min batchSize maxBatchSize` by cases, so clause B still holds and clause
        # A is untouched. loom_solve closes it.
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize = 0 then\n"
            "      return maxBatchSize\n"
            "    else\n"
            "      if batchSize ≤ maxBatchSize then\n"
            "        return batchSize\n"
            "      else\n"
            "        return maxBatchSize\n"),
        "rationale": "a correct reshape that computes the cap by an explicit "
                     "`≤` comparison rather than `min`: on the explicit branch it "
                     "returns `batchSize` when within the maximum and the maximum "
                     "otherwise, which equals `min batchSize maxBatchSize` by "
                     "cases, so clause B (`batchSize > 0 → n = min batchSize "
                     "maxBatchSize`) still discharges and clause A is unchanged. "
                     "Must verify else SPEC-TOO-STRONG (spec over-fit to the `min` "
                     "shape).",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: flip the branch order — test the explicit case (batchSize > 0)
        # FIRST, unspecified case in the else. Same value on every input; pure
        # branching, no loop/lemma, so no proof-gap risk. loom_solve closes it.
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize > 0 then\n"
            "      return min batchSize maxBatchSize\n"
            "    else\n"
            "      return maxBatchSize\n"),
        "rationale": "a structurally-different CORRECT impl: branch order flipped "
                     "(explicit `batchSize > 0` case first, unspecified in the "
                     "else). Same value on every input, so both clauses still "
                     "discharge; pure branching with no loop or lemma. Must verify "
                     "else SPEC-TOO-STRONG (spec over-constrains the branch shape).",
    },

    # =====================================================================
    # ADMISSIBILITY. The sibling's admissibility case self-calls the function on
    # an F2P-shaped over-large explicit request (501, 500) and asserts the capped
    # outcome. Here the method's only `require` (maxBatchSize ≥ 1) is met by every
    # F2P-shaped input, so the "a normal input satisfies the precondition" reading
    # is degenerate. The residual admissibility risk on a total domain is that the
    # post-image is UNSATISFIABLE / DEGENERATE at the interesting point — a spec no
    # impl can meet reads exactly like a spec every impl meets. This case
    # discharges an in-region `assert`, at the F2P-shaped point (501, 500), that
    # states the OBLIGATION ITSELF rather than a fact about `min`:
    #
    #   (a) the precondition ADMITS the point                — `500 ≥ 1`;
    #   (b) the frozen `ensures`, instantiated at that point, IS SATISFIABLE —
    #       the conjunction holds with `n := 500`, so the post-image is non-empty
    #       (a spec no impl can meet at the input the fix cares about would read
    #       exactly like a spec every impl meets);
    #   (c) the post-image is a PROPER subset of the domain — the same
    #       conjunction is FALSE at `n := 501`, so the obligation actually
    #       excludes the uncapped answer at this input.
    #
    # (c) is what makes the case load-bearing: an assert that only says `min 501
    # 500 = 500` is a true arithmetic fact about literals that mentions neither
    # binder nor either clause of the `ensures`, so it would discharge against a
    # spec with NO postcondition at all. Stating the instantiated clauses, and
    # their failure one above the cap, ties the assert to the frozen contract.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges. Liveness re-verified by build: replacing conjunct (c) with the
    # negation of a TRUE claim about the same point leaves `unsolved goals`.
    # =====================================================================
    {
        "id": "admiss-cap-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_HEAD,
            "    assert (with_name_prefix `admiss (\n"
            "      (500 : Nat) ≥ 1 ∧\n"
            "      ((501 = 0 → (500:Nat) = 500) ∧ (501 > 0 → (500:Nat) = min 501 500)) ∧\n"
            "      ¬((501 = 0 → (501:Nat) = 500) ∧ (501 > 0 → (501:Nat) = min 501 500))))\n"
            + _IMPL_HEAD),
        "rationale": "the precondition ADMITS the F2P-shaped point (`500 ≥ 1`) and "
                     "the frozen `ensures`, instantiated at an over-large explicit "
                     "request one above the store maximum, is SATISFIABLE there "
                     "(both clauses hold at `n = 500`) yet PROPER (the same "
                     "conjunction is false at `n = 501`, so the obligation excludes "
                     "the uncapped answer). Together: the post-image at the point "
                     "the fix cares about is non-empty but not everything — a spec "
                     "no impl can meet, or one every impl meets, both fail this. "
                     "Stated over the instantiated clauses rather than a fact about "
                     "`min` literals, so it could not discharge against an empty "
                     "postcondition. Failure => PRECOND-TOO-STRONG or a degenerate "
                     "post-image; the impl is verbatim so the `ensures` still "
                     "discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is straight-line
    # so its extracted tester reduces under `decide`. Witness points are distinct
    # so both binders and both clauses are exercised (see footer).
    # =====================================================================
    {
        "id": "rival-no-cap",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG (pre-fix behaviour): an explicit request is used as-is, ignoring
        # the store maximum. Diverges on batchSize > maxBatchSize.
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize = 0 then\n"
            "      return maxBatchSize\n"
            "    else\n"
            "      return batchSize\n"),
        "refinement": "this is exactly the pre-fix behaviour: an explicit request "
                      "is used verbatim with no cap. Its faithful real counterpart "
                      "is the UNCHANGED pre-fix line, which does NOT resolve the "
                      "failing test — a request larger than the store maximum is "
                      "sliced into `ceil(len/request)` chunks instead of the "
                      "`ceil(len/max)` the test fixes, issuing the wrong query "
                      "count. It would NOT resolve.",
        "rationale": "REJECT from clause B (`batchSize > 0 → n = min batchSize "
                     "maxBatchSize`): on `batchSize > maxBatchSize` the rival "
                     "returns `batchSize` where the clause demands the capped "
                     "minimum. Verifying would be SPEC-TOO-WEAK (the cap is "
                     "unpinned). Refuted at `(3, 2)` — an over-large explicit "
                     "request, both binders positive and distinct.",
        "witness": _witness(3, 2),
    },
    {
        "id": "rival-off-by-one-cap",
        "kind": "uniqueness",
        "expect": "reject",
        # Caps at max+1 instead of max: wrong on EVERY over-large explicit
        # request (batchSize > maxBatchSize), where it returns max+1 rather than
        # max. Its witness is aimed at the F2P-shaped boundary batchSize = max+1
        # because that is the input the failing test issues, not because it is
        # the only divergent point (checked by build: it is also refuted at
        # (5, 3), two above the maximum).
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize = 0 then\n"
            "      return maxBatchSize\n"
            "    else\n"
            "      if batchSize ≤ maxBatchSize then\n"
            "        return batchSize\n"
            "      else\n"
            "        return maxBatchSize + 1\n"),
        "refinement": "caps one above the store maximum. Its faithful real "
                      "counterpart tightens an over-large request to `max + 1` "
                      "rather than `max`, so at the failing test's exact input "
                      "(a request one above the maximum) it slices into "
                      "`ceil(len/(max+1))` chunks — a DIFFERENT, larger-batch query "
                      "count than the `ceil(len/max)` the test fixes. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause B on any over-large explicit request, "
                     "where the rival returns `maxBatchSize + 1` and the clause "
                     "demands `min batchSize maxBatchSize = maxBatchSize`. A "
                     "near-miss that agrees with gold on the whole "
                     "`batchSize ≤ maxBatchSize` half of clause B (unlike "
                     "rival-no-cap, which over-returns by an unbounded amount), so "
                     "it is refuted at `(4, 3)` — the exact `batchSize = max + 1` "
                     "shape the failing test issues.",
        "witness": _witness(4, 3),
    },
    {
        "id": "rival-auto-uses-request",
        "kind": "uniqueness",
        "expect": "reject",
        # In the unspecified (batchSize = 0) branch returns `batchSize` (which is 0)
        # instead of the store maximum. Diverges only on batchSize == 0.
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize = 0 then\n"
            "      return batchSize\n"
            "    else\n"
            "      return min batchSize maxBatchSize\n"),
        "refinement": "in the unspecified branch it returns the (zero) request "
                      "instead of the store maximum. Its faithful real counterpart "
                      "passes the unspecified sentinel through as the slice step, "
                      "which crashes every no-request call at runtime (a zero/None "
                      "slice step is not iterable), breaking the dominant "
                      "no-explicit-request path. It would NOT resolve.",
        "rationale": "REJECT from clause A (`batchSize = 0 → n = maxBatchSize`): on "
                     "`batchSize = 0` the rival returns 0 where the clause demands "
                     "`maxBatchSize`. Verifying would be SPEC-TOO-WEAK (the "
                     "unspecified branch is unpinned). Refuted at `(0, 5)` — the "
                     "only shape on which clause A bites, and the sole point where "
                     "batchSize is zero.",
        "witness": _witness(0, 5),
    },
    {
        "id": "rival-equal-under",
        "kind": "uniqueness",
        "expect": "reject",
        # At the equal boundary batchSize == maxBatchSize returns maxBatchSize - 1
        # (an under-cap). Diverges only on batchSize == maxBatchSize (> 0), a
        # single-point partial-domain miss at the equality edge.
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize = 0 then\n"
            "      return maxBatchSize\n"
            "    else\n"
            "      if batchSize < maxBatchSize then\n"
            "        return batchSize\n"
            "      else\n"
            "        if batchSize = maxBatchSize then\n"
            "          return maxBatchSize - 1\n"
            "        else\n"
            "          return maxBatchSize\n"),
        "refinement": "at an explicit request exactly equal to the store maximum "
                      "it under-caps by one. Its faithful real counterpart slices a "
                      "caller who asked for exactly the maximum into "
                      "`ceil(len/(max-1))` chunks — MORE queries than the "
                      "`ceil(len/max)` the equal-request scenario expects — so it "
                      "regresses the explicit-request-equals-maximum path and does "
                      "NOT resolve.",
        "rationale": "REJECT from clause B at the single equality point `batchSize "
                     "= maxBatchSize` (> 0), where the rival returns `maxBatchSize "
                     "- 1` and the clause demands `min batchSize maxBatchSize = "
                     "maxBatchSize`. A genuinely-wrong single-point miss (the "
                     "value-equivalent `<`→`≤` swap is NOT this — that keeps gold's "
                     "value). Refuted at `(3, 3)` — the equality edge, distinct "
                     "from every other witness point.",
        "witness": _witness(3, 3),
    },
    {
        "id": "rival-ignores-request",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit. The four rivals above all agree with gold on the
        # sub-domain 0 < batchSize < maxBatchSize — an explicit request STRICTLY
        # WITHIN the store maximum — so no case pinned the "an honoured request
        # is returned unchanged" half of clause B. This rival always returns the
        # store maximum, ignoring the request entirely: it satisfies clause A and
        # agrees with gold at and above the cap, and is wrong exactly on that
        # previously-unattacked interior sub-domain.
        "module": _swap(
            _BASE, _IMPL,
            "    if batchSize = 0 then\n"
            "      return maxBatchSize\n"
            "    else\n"
            "      return maxBatchSize\n"),
        "refinement": "ignores the caller's explicit request whenever it is below "
                      "the store maximum, always chunking at the store maximum "
                      "instead. Its faithful real counterpart discards the "
                      "caller-supplied size on the path where that size is the "
                      "binding one, so a caller who explicitly asks for a SMALLER "
                      "chunk than the store could take is nonetheless chunked at the "
                      "store maximum — `ceil(len/max)` queries instead of the "
                      "`ceil(len/request)` an explicit smaller request fixes. That "
                      "regresses the existing explicit-request scenarios (a request "
                      "well under the maximum is the ordinary explicit case), so it "
                      "would NOT resolve.",
        "rationale": "REJECT from the other half of clause B (`batchSize > 0 → n = "
                     "min batchSize maxBatchSize`): on `0 < batchSize < "
                     "maxBatchSize` the clause demands `min batchSize maxBatchSize = "
                     "batchSize`, the request honoured unchanged, and the rival "
                     "returns `maxBatchSize`. Verifying would be SPEC-TOO-WEAK — the "
                     "spec would pin only the CAP and not the honouring, i.e. it "
                     "would admit an impl that always chunks at the store maximum. "
                     "Refuted at `(2, 5)`, an explicit request strictly inside the "
                     "maximum: a sub-domain no other rival diverges on (all four "
                     "return gold's value there), and a fifth distinct witness "
                     "point.",
        "witness": _witness(2, 5),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals; the sibling explicitly records
# the frame-mutation class as VACUOUS because both params are pass-by-value ints).
# The sibling contracts the SAME single function — effective_batch_size(requested,
# raw_backend_limit) -> int — but keeps the store-floor as a grounded @Pure helper
# `clamped_max(raw)` (raw≥1 => raw, else 1). This bundle abstracts that floor into
# the precondition `require maxBatchSize ≥ 1` (mapping.md §2: the `max(…, 1)` floor
# IS the require), so `maxBatchSize` enters already floored. The carrier is
# otherwise identical (Nat ↔ non-negative int; `min` ↔ min; 0 ↔ unspecified).
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-grounded-oracle              -> pos-explicit-branch            RE-EXPRESSED
#   pos-reorder                      -> pos-reorder                    PORTED
#   admiss-selfcall                  -> admiss-cap-nondegenerate       RE-AIMED
#   rival-no-cap                     -> rival-no-cap                   PORTED
#   rival-off-by-one-cap             -> rival-off-by-one-cap           PORTED
#   rival-auto-zero-uses-request     -> rival-auto-uses-request        PORTED
#   rival-equal-under                -> rival-equal-under              PORTED
#   rival-no-clamp                   -> (none)                         OUT OF DOMAIN
#   (frame-mutation)                 -> (none)                         VACUOUS
#   (no sibling counterpart)         -> rival-ignores-request          ADDED BY AUDIT
#
# 5 ported, 2 re-expressed/re-aimed, 1 out of domain, frame class vacuous,
# 1 added by audit.
#
# ADDED BY AUDIT (rival-ignores-request): the ported set left the sub-domain
#   `0 < batchSize < maxBatchSize` unattacked — all four rivals return gold's
#   value for an explicit request strictly BELOW the store maximum, so only the
#   capping half of clause B was pinned and not the honouring half. Verified by
#   build that an impl returning `maxBatchSize` unconditionally is refuted at
#   `(2, 5)` and that gold is correct there, so the gap was real and closeable.
#
# RE-EXPRESSED (pos-grounded-oracle -> pos-explicit-branch): the sibling's
#   grounded-oracle positive computes `clamped_max(raw)` then a single min
#   selection. Here the floor is already the `require`, so the honest cheapest
#   reshape is the explicit two-way `≤` comparison that equals `min` by cases —
#   the same "compute the capped value directly" argument on this carrier.
# RE-AIMED (admiss-selfcall -> admiss-cap-nondegenerate): the sibling self-calls
#   the function on (501, 500) and asserts the precondition admits it and the post
#   gives the capped value 500. Here the precondition (maxBatchSize ≥ 1) is met by
#   every F2P input, so that reading is degenerate; the case is re-aimed at the
#   residual total-domain risk (a degenerate post-image) by discharging an
#   in-region assert at the sibling's exact F2P point (501, 500) that the
#   precondition admits it and the INSTANTIATED `ensures` is satisfiable there
#   (holds at n = 500) yet proper (fails at n = 501). Strengthened during audit:
#   the case originally asserted only `min 501 500 = 500 ∧ min 500 500 = 500`,
#   true arithmetic about literals that names neither binder nor either clause and
#   so would have discharged against a spec with NO postcondition at all. It was
#   an honest pass that tested nothing. The current form is stated over the frozen
#   clauses themselves; liveness confirmed by build (negating a true conjunct
#   about the same point leaves `unsolved goals`).
# OUT OF DOMAIN (rival-no-clamp): the sibling's rival drops the `max(.,1)` clamp
#   and returns `raw_backend_limit` on the auto path, diverging ONLY at
#   raw_backend_limit == 0. On this carrier that floor is the precondition `require
#   maxBatchSize ≥ 1`, so maxBatchSize == 0 is OUTSIDE the modeled domain: no
#   in-domain input distinguishes a "no-clamp" rival from gold, and no
#   discriminating witness exists (the point it would fail at is excluded by the
#   require). DEMONSTRATED during audit, not asserted: transliterating the
#   sibling's rival onto this carrier yields text byte-identical to the frozen
#   impl (the floor lives in the require, so there is nothing left to drop), and
#   the frozen tester is vacuously `true` at both (0, 0) and (7, 0) — a witness
#   there elaborates against GOLD, so it discriminates nothing. Both facts by
#   build. This is carrier narrowing, not a dropped-for-proof-cost omission —
#   the clamp is captured by the precondition rather than the impl, so the sibling
#   rival that attacks the clamp has no counterpart. Reported here as a KNOWN gap
#   with its exact cause, per the guide.
# VACUOUS (frame-mutation): the sibling already records this class as inapplicable
#   (both params are pass-by-value ints, has_readonly_input = False). This backend
#   is likewise referentially transparent with no `mut` binder on either input, no
#   heap and no aliasing — there is no read-only input to overwrite and no
#   substitute probe. Not fabricated. The "inputs are not mutated" obligation is
#   structurally guaranteed by the absence of `mut`, which the frozen spec encodes.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# WITNESS DISTINCTNESS. The five rivals probe five DISTINCT points of the two
#   binders (batchSize, maxBatchSize): rival-no-cap at (3, 2) (over-large explicit
#   request, clause B), rival-off-by-one-cap at (4, 3) (the exact F2P boundary
#   batchSize = max+1, clause B — the near-miss's discriminating point, above
#   no-cap's), rival-auto-uses-request at (0, 5) (batchSize = 0, clause A — the
#   only shape on which clause A bites), rival-equal-under at (3, 3) (the equality
#   edge batchSize = max, clause B), rival-ignores-request at (2, 5) (an explicit
#   request strictly INSIDE the maximum — clause B's honouring half, the
#   sub-domain the ported set left unattacked). So batchSize ranges over
#   {0, 2, 3, 4} and maxBatchSize over {2, 3, 5}, BOTH clauses A and B are
#   attacked, clause B is attacked on BOTH sides of the cap, and each rival is
#   refuted at the point that separates it from the others. pts = 5.
#
# AUDIT ATTACK RECORD (all by real build; no spec hole found). 8 NEW wrong impls
#   beyond the shipped rivals were checked against the frozen spec and ALL were
#   rejected: return max unconditionally, min with no unspecified branch, `max`
#   for `min`, an under-cap by one, the two branches' answers swapped, constant 1,
#   clause B pinned to 1, and a single-interior-point miss at batchSize = 2. 5 NEW
#   correct reshapes were checked and ALL verified: `min` commuted, the cap
#   let-bound before the branch, a `maxBatchSize ≤ batchSize`-first shape, a
#   `≥`-first shape, and a `match batchSize with | 0 | k+1` destructuring. So the
#   spec is neither too weak nor too strong on this carrier within the probes run.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no A-reference deep model (mapping.md §3: the unchanged DB callee is
# abstracted as the plain input `maxBatchSize`, not axiomatized), so there is
# nothing there to probe, and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
