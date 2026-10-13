"""properties.py — G-PBT falsification battery for django__django-11066 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL, BY
DECIDING, against a subject known to satisfy the spec).

DEFENDED SURFACE (one contracted method over a store-handle carrier,
``List Char`` of code points):

  resolveTarget (db : List Char) (routed : List Char) return (out : List Char)
    require db.length > 0                 -- the explicitly named handle is present
    require routed.length > 0             -- the fallback handle is present
    ensures aliasEq out db                -- THE load-bearing (and only) clause

``aliasEq a b := a = b`` is a transparent identity on the input carrier — plain
``List Char`` equality of the result against the input ``db``. It is NOT an
opaque answer key: the post-image is GROUNDED in a method input (directive 8),
so there is no wrong echo of an oracle that could verify. The one echo an
adversary reaches for is ``return routed`` — the inherited (pre-image) behaviour
— and it is genuinely caught, because the spec pins the result to ``db``
REGARDLESS of ``routed``.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on EXACTLY ONE input — ``db``. ``routed`` is DELIBERATELY free: it is the
handle a separate, independent routing policy would otherwise pick, an arbitrary
present handle unconstrained to equal ``db``. The whole POINT of the modeled
behaviour is that when an explicit handle is named the resolution IGNORES
``routed`` entirely; ``routed`` exists in the surface so the rivals can state the
WRONG answer (echo, or splice in, the routing policy's choice) and so the
pre-image skeleton is expressible while the spec stays byte-identical.

So no rival can be wrong in a way distinguished ONLY by ``routed``: an impl that
returns ``db`` on every ``routed`` VERIFIES (correctly — the spec is independent
of it), and one that lets ``routed`` leak into the result is caught by the
``aliasEq out db`` clause whenever ``routed`` differs from ``db``. The reject
witnesses below vary BOTH binders across five distinct input points, while the
DISCRIMINATION always comes from the result diverging from ``db``.

Because the single clause is an exact equality, "attacking every independent
top-level clause" means attacking every FACET that a weaker spec could have
pinned instead. The five rivals are chosen so that each would survive a
different weakening of the clause:

  * ``weak-echo-routed``     — survives a spec that said only "out is some
                               present handle" (the pre-image bug itself)
  * ``weak-drop-all``        — survives a spec with no presence/non-emptiness
                               requirement on the result
  * ``weak-partial-last``    — survives a spec pinning only a PREFIX of ``db``
  * ``weak-append-routed``   — survives a spec pinning only that ``out`` STARTS
                               WITH ``db`` (length left free)
  * ``weak-reverse-handle``  — survives a spec pinning only the MULTISET/length
                               of code points (order left free)

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION (nagini's #4/#5, MANDATORY there) — VACUOUS here. The nagini
    sibling holds both inputs at a fractional heap permission (``Acc(.,1/2)``) an
    impl can illegally overwrite, and carries two rivals that mutate the
    read-only inputs. Lean/Velvet are referentially transparent: every input is
    an immutable value, no binder is ``mut``, there is no heap and no aliasing —
    so there is no read-only field to mutate and no substitute probe to build.
    Not fabricated (per the porting map: this class is vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a method input, not an
    axiomatized oracle; the ``axioms`` region is empty.
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS PLACEMENT, and why every reject case carries a ``witness_reference``.
The spec is a ``method`` CONTRACT, not a bare predicate, so a witness reaches the
postcondition through Velvet's own tester machinery:
``resolveTargetTester db routed = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. Because ``aliasEq`` is a transparent ``def`` (not auto-``Decidable``),
each witness first supplies the obvious ``Decidable (aliasEq a b)`` instance so
the tester's postcondition check reduces.

The FROZEN impl keeps a back-to-front copy ``while`` loop, and under
``set_option loom.semantics.choice "demonic"`` that loop's fixpoint elaborates
through ``Classical.choice``, which the kernel cannot unfold. Measured on this
bundle: the witness build against the frozen solution fails with

    reduction got stuck at the `Decidable` instance
      match resolveTargetTester ['o'] ['d'], false with ...

for EVERY claim, true or false — so the frozen-side exit code carries no
information and a forged witness asserting the rival is *correct* would clear
both halves. That is ``witness-undecided``, and it is exactly what a previous
authoring of this battery recorded on all three of its reject cases
(``G-PBT=error :: MALFORMED-TESTS``). The repair is the documented one: every
reject case names ``witness_reference = _LOOPFREE``, a loop-free impl of the same
frozen spec that DOES kernel-reduce, and the gate refutes each witness against
that instead. The gate independently re-checks that the reference shares the
frozen spec and VERIFIES before trusting it. ``pos-loopfree-reference`` ships the
same source as an ``expect="verify"`` case, so the battery itself records that
loop-freeness is not what any rival is being rejected for.

Every reject witness below was run against both subjects with real builds and was
SEEN to discriminate: exit 0 against the rival, and exit 1 against the reference
with ``Tactic `decide` proved that the proposition ... is false`` — a genuine
refutation, not a stuck reduction.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the routing
policy's choice is a directive-7 free input ``routed``, validated as an
A-reference by axiom_check.py / G-AX, not a consumed contract). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11066"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region (the
# ---- resolution + back-to-front copy loop) and is unique in Solution.lean (both
# ---- facts asserted at load by _swap). Anchoring on the whole block keeps the
# ---- surgery within the elided region. ----
_IMPL = (
    "    -- The write target is `explicit or routing_policy_choice`: an explicit\n"
    "    -- (present, non-empty) handle is used directly; the routing-policy fallback\n"
    "    -- is reached only when no explicit handle is given. An explicit handle (db)\n"
    "    -- is always present here, so the resolution short-circuits to it.\n"
    "    let src : List Char := if db.length > 0 then db else routed\n"
    "    -- Copy the resolved handle into a fresh result carrier (the write commits to\n"
    "    -- the store this handle names).\n"
    "    let mut result : List Char := []\n"
    "    let mut i := src.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ src.length\n"
    "      invariant result = src.drop i\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := src[i - 1]!\n"
    "      result := c :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# ---- the frozen proof body (everything under the `prove_correct` header). The
# ---- reject rivals keep it verbatim — their rejection is carried by the witness,
# ---- never by whether the frozen loop script happens to break on the reshape.
# ---- The positives retune it, since a reshaped impl changes the goals
# ---- `loom_solve` leaves. The `prove_correct resolveTarget by` HEADER survives
# ---- in every variant, so the obligation is never dropped. ----
_PROOF = (
    "prove_correct resolveTarget by\n"
    "  loom_solve\n"
    "  · -- loop-body step: the resolution `if` reduces to the explicit handle `db`,\n"
    "    -- then the copy peels one code point off the front.\n"
    "    simp only [require_2, if_true] at *\n"
    "    rw [drop_copy_step db i (by omega) (by omega), invariant_2]\n"
    "  · -- exit: `result = db.drop 0 = db`, so `aliasEq result db` holds.\n"
    "    simp only [require_2, if_true, aliasEq] at *\n"
    "    simp_all"
)

# ---- impl-start anchor for the in-region admissibility assert. ----
_IMPL_START = "    -- impl-start\n"

# ---- the loop-keeping copy tail, shared by the two loop-shaped positives. ----
_COPY_LOOP = (
    "    let mut result : List Char := []\n"
    "    let mut i := src.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ src.length\n"
    "      invariant result = src.drop i\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := src[i - 1]!\n"
    "      result := c :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# ---- the retuned proof for a positive that resolves to `db` WITHOUT the
# ---- resolution `if` (so no `require_2`/`if_true` rewrite is needed). ----
_PROOF_NOIF = (
    "prove_correct resolveTarget by\n"
    "  loom_solve\n"
    "  · rw [drop_copy_step db i (by omega) (by omega), invariant_2]\n"
    "  · simp only [aliasEq] at *\n"
    "    simp_all"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ===========================================================================
# THE WITNESS REFERENCE. A loop-free impl of the frozen spec: the explicitly
# named handle is always present (`require db.length > 0`), so the resolution is
# just that handle and no copy loop is needed. Correct, and — crucially — its
# extracted program kernel-reduces, so `decide` DECIDES against it where the
# frozen loop's `Classical.choice` fixpoint leaves `decide` stuck for every claim.
# The gate re-checks that this shares the frozen spec and VERIFIES (measured:
# exit 0) before refuting any witness against it, and `pos-loopfree-reference`
# below ships the identical source as an `expect="verify"` case.
# ===========================================================================
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL,
          "    -- The explicitly named handle is always present, so the resolved\n"
          "    -- target IS that handle; no copy loop is needed to name it.\n"
          "    return db"),
    _PROOF,
    "prove_correct resolveTarget by\n"
    "  loom_solve\n"
    "  simp only [aliasEq]\n")


# ---- witness preamble. Supply the `aliasEq` Decidable instance (a transparent
# ---- `def`, not auto-decidable), then reach the method contract through
# ---- Velvet's tester machinery. `resolveTargetTester db routed = false` says the
# ---- extracted program's result violates `aliasEq out db` at that input. Both
# ---- `require` clauses (both handles present) are satisfied by every non-empty
# ---- literal below, so no witness is refuting the rival at an input the
# ---- precondition excludes — nothing is vacuously admitted. Every witness states
# ---- its refutation at CONCRETE literals and binds nothing, so there are no
# ---- hypotheses that could be jointly unsatisfiable (the gate's
# ---- witness-inconsistent probe has nothing to find). ----
_TESTER = (
    "instance (a b : List Char) : Decidable (aliasEq a b) := by\n"
    "  unfold aliasEq; infer_instance\n\n"
    "extract_program_for resolveTarget\n"
    "prove_precondition_decidable_for resolveTarget\n"
    "prove_postcondition_decidable_for resolveTarget\n"
    "derive_tester_for resolveTarget\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # `ensures aliasEq out db` obligation and only reshapes the executable
    # surface; the proof is retuned because the reshape changes the goals
    # `loom_solve` leaves. All three verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-loopfree-reference",
        "kind": "soundness",
        "expect": "verify",
        # The witness reference, shipped as a positive in its own right. Two jobs:
        # (a) a genuine SPEC-TOO-STRONG probe — the most direct correct impl,
        # resolving straight to the named handle with no copy at all; (b) it puts
        # on the record that this source VERIFIES, so when the reject lane is
        # refuted against it, loop-freeness is demonstrably not what any rival is
        # being rejected for.
        "module": _LOOPFREE,
        "rationale": "the most direct correct impl: `db.length > 0` holds by "
                     "precondition, so the resolved target IS the named handle and "
                     "the copy loop is unnecessary — `aliasEq out db` holds "
                     "immediately. A faithful correct impl MUST verify, else "
                     "SPEC-TOO-STRONG. This is also the `witness_reference` every "
                     "reject case is refuted against, so shipping it as a positive "
                     "records that the reference satisfies the spec (the gate "
                     "re-checks this independently) and that loop-freeness is not "
                     "the property any rival is rejected for. (Sibling: "
                     "pos-control-direct.)",
    },
    {
        "id": "pos-direct-explicit",
        "kind": "soundness",
        "expect": "verify",
        # Same resolution as the reference but KEEPING the frozen copy loop: this
        # is the sibling's cheapest-correct-impl argument (drop the resolution
        # indirection) without also dropping the loop, so a reader can see the two
        # reshapes are independent.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- The explicit handle is always present, so the resolved target is\n"
                  "    -- the named handle itself; copy it directly into a fresh carrier.\n"
                  "    let src : List Char := db\n" + _COPY_LOOP),
            _PROOF, _PROOF_NOIF),
        "rationale": "REORDER/SIMPLIFY of the resolution: since `db.length > 0` "
                     "holds by precondition the resolved handle is `db` itself, so "
                     "dropping the `if` while keeping the copy loop still satisfies "
                     "`aliasEq out db`. A faithful correct impl MUST verify, else "
                     "SPEC-TOO-STRONG. Distinct from pos-loopfree-reference in that "
                     "it retains the loop, isolating the resolution reshape from the "
                     "copy reshape. (Sibling: pos-control-direct.)",
    },
    {
        "id": "pos-branch-on-routed",
        "kind": "soundness",
        "expect": "verify",
        # INSPECT the free input `routed` (branch on its length) yet return `db`
        # on both arms — a direct demonstration that the spec is correctly
        # independent of `routed`: the resolution forwards the named handle
        # regardless of what the routing policy would pick.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- Branch on the (free) fallback handle's presence but resolve to the\n"
                  "    -- named handle on BOTH arms: the resolution ignores the routing\n"
                  "    -- policy's choice whenever an explicit handle is named.\n"
                  "    let src : List Char := if routed.length > 0 then db else db\n"
                  + _COPY_LOOP),
            _PROOF, _PROOF_NOIF),
        "rationale": "structurally different CORRECT reshape: it branches on the "
                     "free input `routed` but resolves to `db` on both arms, so "
                     "`aliasEq out db` holds regardless of `routed`. A faithful "
                     "reshape MUST verify (else SPEC-TOO-STRONG); it also witnesses "
                     "that the spec is correctly independent of `routed`, which is "
                     "the modeled behaviour's whole point. (Sibling: "
                     "pos-control-reorder.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries two `require` clauses (both handles
    # present). The interesting residual risk is not that a normal input is
    # excluded (it plainly is not) but that the post-image is DEGENERATE at the
    # shaped point where the named and routed handles DIFFER. This case
    # discharges an in-region assert (auto-solved by loom_solve, checked
    # out-of-band) that at a differing pair the two handles are both present and
    # `aliasEq` genuinely distinguishes them — the named handle matches itself
    # and does NOT match the routing policy's differing choice. The rest of the
    # impl and the frozen proof are kept verbatim, so the ensures still discharges.
    # =====================================================================
    {
        "id": "admiss-differing-handles",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START +
            "    assert (with_name_prefix `adm\n"
            "      (['o','t','h','e','r'].length > 0 ∧ ['d','e','f'].length > 0 ∧\n"
            "       (['o','t','h','e','r'] : List Char) ≠ ['d','e','f']))\n"),
        "rationale": "the precondition admits the shaped input where the named "
                     "handle and the routing policy's choice DIFFER (both present, "
                     "unequal) — the only input shape at which the modeled "
                     "behaviour is observable at all. The in-region assert must "
                     "discharge (else the post-image would be degenerate / "
                     "PRECOND-TOO-STRONG at the point that matters); the impl and "
                     "frozen proof are kept verbatim so `aliasEq out db` still "
                     "discharges. (Sibling: admiss-fshaped-input.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each keeps the frozen proof body VERBATIM, so the
    # rejection is never a tactic-shape artifact, and each is refuted at a
    # concrete input by a witness that ELABORATES against the rival and is
    # DECIDED false against `_LOOPFREE` (the frozen loop cannot decide anything —
    # see the module docstring). Each carries the refinement argument for why its
    # faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-echo-routed",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack — the inherited (pre-image) behaviour: no explicit
        # handle is used, so the result echoes the routing policy's choice.
        "module": _with_impl("    return routed"),
        "refinement": "this IS the inherited pre-image behaviour: with no explicit "
                      "handle supplied, the persistence step resolves its write "
                      "target through the independent routing policy and lands the "
                      "write in the store that policy names. When that policy names "
                      "a store DIFFERENT from the one this step is operating on "
                      "(exactly the scenario the failing test sets up: the policy "
                      "names one store while the step operates on another), the row "
                      "lands in the wrong store, the renamed row never appears in "
                      "the intended one, and the test FAILS — it would NOT resolve.",
        "rationale": "REJECT from `aliasEq out db`: the rival returns `routed`, "
                     "which differs from `db` whenever the two handles are unequal. "
                     "The spec pins the result to `db` REGARDLESS of `routed`, so a "
                     "free `routed ≠ db` refutes it. If it verified, the spec would "
                     "admit the pre-image bug => SPEC-TOO-WEAK. Survives a spec that "
                     "said only 'out is some present handle', which is the weakening "
                     "this rival exists to rule out. Refuted at db=['o'], "
                     "routed=['d'] (differing single-code-point handles). "
                     "(Sibling: weak-prepatch-routed.)",
        "witness": _witness("resolveTargetTester ['o'] ['d']"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Contribute NOTHING: resolve to the empty handle. Names neither the
        # explicit store nor the routing choice.
        "module": _with_impl("    return []"),
        "refinement": "resolving the write target to the empty handle names no "
                      "store at all: the single-field write would not land in the "
                      "explicitly named store, so the renamed row never appears "
                      "there and the failing test FAILS — it would NOT resolve.",
        "rationale": "REJECT from `aliasEq out db`: the rival returns `[]`, which "
                     "differs from `db` for every present (non-empty) `db`. Survives "
                     "a spec with no presence requirement on the result. Its "
                     "wrongness is independent of `routed` entirely, so it also "
                     "demonstrates the result must be pinned to `db` and not merely "
                     "'some present handle'. Refuted at db=['x'], routed=['y'] — a "
                     "DIFFERENT input point from the echo rival, moving both binders.",
        "witness": _witness("resolveTargetTester ['x'] ['y']"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-partial-last",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: correct on the prefix but splice the LAST code point from the
        # routing policy's choice. Equals `db` only when the two handles agree on
        # their last code point; diverges otherwise. Forces the spec to pin every
        # position, not just a prefix.
        "module": _with_impl(
            "    return db.dropLast ++ [routed[routed.length - 1]!]"),
        "refinement": "resolving to the named handle on all but its last code "
                      "point, with the final code point taken from the routing "
                      "policy's choice, names a store whose handle differs from the "
                      "named one precisely when the two disagree on that last code "
                      "point — so the write lands in a different store than "
                      "intended, the renamed row does not appear in the intended "
                      "store, and the failing test FAILS. It is not any faithful "
                      "edit and would NOT resolve.",
        "rationale": "REJECT from `aliasEq out db` (element-wise, full `List Char` "
                     "equality): the rival equals `db` only when the named and "
                     "routed handles share a last code point; it diverges at the "
                     "final index otherwise. Survives a spec pinning only a PREFIX "
                     "of `db` => that weakening is what this rival rules out. A "
                     "near-miss that agrees with gold on more of the domain than "
                     "weak-drop-all (wrong at every index), so it gets its own "
                     "witness at the point that distinguishes it: db=['a','b'], "
                     "routed=['a','c'] — the handles agree on the PREFIX and differ "
                     "only at the last index, so result=['a','c'] ≠ ['a','b']. "
                     "(Sibling: partial-domain-last-elem.)",
        "witness": _witness("resolveTargetTester ['a','b'] ['a','c']"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-append-routed",
        "kind": "uniqueness",
        "expect": "reject",
        # LENGTH attack: keep ALL of the named handle (so every prefix claim about
        # `db` still holds) but append the routing policy's choice after it. The
        # dual of weak-partial-last: that one corrupts a position inside `db`'s
        # length, this one leaves `db` wholly intact and only overruns it.
        "module": _with_impl("    return db ++ routed"),
        "refinement": "concatenating the named handle with the routing policy's "
                      "choice names a store that is neither of them — no such store "
                      "is configured, so the single-field write does not land in the "
                      "explicitly named store, the renamed row never appears there, "
                      "and the failing test FAILS. It is not any faithful edit and "
                      "would NOT resolve.",
        "rationale": "REJECT from `aliasEq out db`: the rival returns `db ++ "
                     "routed`, which is strictly longer than `db` for every present "
                     "`routed`, so it can never equal `db`. This rival keeps `db` as "
                     "an intact PREFIX of the result, so it would SURVIVE a spec "
                     "pinning only 'out starts with db' (length left free) — the "
                     "weakening no other rival here rules out, and the exact dual of "
                     "weak-partial-last (which corrupts a position within `db`'s "
                     "length while preserving the length). Refuted at db=['q'], "
                     "routed=['r','s'] — a fourth distinct input point, and the only "
                     "witness whose `routed` is longer than its `db`.",
        "witness": _witness("resolveTargetTester ['q'] ['r','s']"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-reverse-handle",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER attack: return exactly the named handle's code points, with the
        # right length and the right multiset, in the WRONG order. Refutable only
        # because `aliasEq` is ordered list equality.
        "module": _with_impl("    return db.reverse"),
        "refinement": "resolving the write target to the named handle's code points "
                      "in reverse order names a different store than the one "
                      "intended (for any handle that is not a palindrome) — no such "
                      "store is configured, so the write does not land in the "
                      "explicitly named store, the renamed row never appears there, "
                      "and the failing test FAILS. It would NOT resolve.",
        "rationale": "REJECT from `aliasEq out db`: the rival returns `db.reverse`, "
                     "which differs from `db` for every non-palindromic handle. It "
                     "preserves the result's LENGTH and its MULTISET of code points "
                     "exactly, so it would SURVIVE any spec pinning only those — "
                     "which is the weakening this rival alone rules out, and it "
                     "establishes that `aliasEq` must be ORDERED list equality. "
                     "Refuted at db=['m','n'], routed=['z']: result=['n','m'] ≠ "
                     "['m','n'] — a fifth distinct input point, and the only witness "
                     "whose refutation is independent of `routed` at a MULTI-code-"
                     "point `db` (weak-drop-all's is at a single-code-point one).",
        "witness": _witness("resolveTargetTester ['m','n'] ['z']"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation, 2 value/uniqueness rivals) plus
# an EMPTY AXIOM lane. This bundle models a NARROWER surface: nagini contracts
# `persisted_db` over a fractional-permission list carrier; velvet models the
# purely functional resolution (`aliasEq out db`) over an immutable `List Char`
# and folds the routing policy's choice into the free input `routed`. The
# accounting below records every sibling case.
#
#   sibling case (nagini)           -> here
#   ---------------------------------------------------------------------
#   pos-control-direct              -> pos-loopfree-reference       PORTED
#                                      + pos-direct-explicit        PORTED (split)
#   pos-control-reorder             -> pos-branch-on-routed         RE-EXPRESSED
#   admiss-fshaped-input            -> admiss-differing-handles     RE-EXPRESSED
#   frame-mut-db                    -> (none)                       VACUOUS (no heap)
#   frame-mut-routed                -> (none)                       VACUOUS (no heap)
#   weak-prepatch-routed            -> weak-echo-routed             PORTED (central)
#   partial-domain-last-elem        -> weak-partial-last            PORTED
#   (no sibling)                    -> weak-drop-all                ADDED
#   (no sibling)                    -> weak-append-routed           ADDED
#   (no sibling)                    -> weak-reverse-handle          ADDED
#   AXIOM_TESTS (empty)             -> (none)                       DROPPED (G-AX)
#
# PORTED (pos-control-direct, SPLIT INTO TWO): the sibling's grounded-oracle
#   cheapest correct impl drops the resolution indirection and copies `db`. That
#   argument lands here twice, deliberately: pos-direct-explicit drops the
#   resolution `if` but keeps the copy loop, and pos-loopfree-reference drops both.
#   The split is not padding — the loop-free one is the `witness_reference` the
#   whole reject lane is refuted against, and shipping it as a positive is what
#   records (in this battery, not just in the gate's internals) that it satisfies
#   the spec, so no rival is being rejected merely for being loop-free.
# RE-EXPRESSED (pos-branch-on-routed): nagini reorders the resolution ternary
#   (`routed if len(db)==0 else db`). On this carrier the same ARGUMENT ("a
#   structurally different faithful impl must verify") is carried by branching on
#   the free input `routed` yet returning `db` on both arms; it doubly witnesses
#   that the spec is independent of `routed`. Both loop-keeping positives retune
#   the frozen proof (the reshape removes the `require_2`/`if_true` rewrite the
#   frozen script needs) and were verified to build.
# RE-EXPRESSED (admiss-differing-handles): the sibling self-calls persisted_db on
#   a shaped input to prove the precondition admits it. Here the analogous probe
#   is an in-region assert that at a differing (named, routed) pair both handles
#   are present and `aliasEq` distinguishes them — i.e. the post-image is
#   non-degenerate at the point that matters. loom_solve discharges the assert VC
#   automatically; the impl and frozen proof are kept verbatim.
# VACUOUS (frame-mut-db, frame-mut-routed): the sibling carries these MANDATORY
#   because its inputs are held at Acc(.,1/2) an impl can illegally write, and it
#   ships one rival per read-only input. This backend is referentially
#   transparent and declares no `mut` binder — every input is an immutable value
#   with no heap footprint — so there is no read-only field to overwrite and no
#   substitute probe. Not fabricated (porting map: this class is vacuous here).
# PORTED (weak-echo-routed): the central pre-image echo (`return routed`) ports
#   directly and is the rival that matters most. PORTED (weak-partial-last): the
#   partial-domain rival ports as a prefix-correct/last-code-point-spliced
#   resolution. ADDED (weak-drop-all, weak-append-routed, weak-reverse-handle):
#   three rivals with no sibling, each chosen to be the ONLY one that survives a
#   particular weakening of the single `aliasEq out db` clause (result presence,
#   result length given an intact `db` prefix, and code-point ORDER respectively).
#   Because the clause is one exact equality rather than several independent
#   conjuncts, "attack every independent clause" can only mean "attack every facet
#   a weaker clause could have left unpinned", and that is what these three add.
#
# WITNESS ACCOUNTING. The five reject witnesses probe five DISTINCT input tuples:
#   db over {['o'], ['x'], ['a','b'], ['q'], ['m','n']} and routed over
#   {['d'], ['y'], ['a','c'], ['r','s'], ['z']} — so pts=5. The load-bearing
#   binder `db` is varied across handle lengths (1 and 2 code points) and contents
#   (including a case where db and routed share a prefix, and a case where routed
#   is the LONGER handle). The free binder `routed` is varied too, though per the
#   BINDER STRUCTURE note the spec is genuinely independent of it: no rival CAN be
#   wrong in a way distinguished only by `routed`, since any impl returning `db` on
#   every `routed` verifies — correctly. Two of the five rivals (weak-drop-all,
#   weak-reverse-handle) are wrong independently of `routed` and the other three
#   let `routed` leak into the result, so both roles of that binder are exercised.
#   No two rivals share a witness: each is refuted at its own distinguishing
#   point, so no rationale claims a sub-domain the manifest does not demonstrate.
#
# WHY EVERY REJECT CASE NAMES A `witness_reference`. Not a convenience: the frozen
#   impl's `while` loop elaborates through `Classical.choice` under
#   `loom.semantics.choice "demonic"`, so a `decide` against it is stuck for EVERY
#   claim and the frozen-side exit code discriminates nothing. A previous
#   authoring of this battery shipped three reject cases without a reference and
#   the gate recorded `witness-undecided` on all three -> MALFORMED-TESTS. Each
#   witness here was checked by hand against BOTH subjects before shipping: exit 0
#   against its rival, and exit 1 against `_LOOPFREE` with `Tactic `decide` proved
#   that the proposition ... is false` — a decided refutation, not a stuck
#   reduction. The frozen solution's own stuck error was reproduced too, which is
#   what makes the reference necessary rather than optional.
#
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
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
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the routing policy's choice is a directive-7 free input `routed`, an
# A-reference validated by axiom_check.py, not a consumed oracle), so there is
# nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
