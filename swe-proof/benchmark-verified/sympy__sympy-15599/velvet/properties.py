"""properties.py — G-PBT falsification battery for sympy__sympy-15599 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct reduceModFactors`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  reduceModFactors (factors : List Factor) (q : Int) return (out : List Factor)
    require q ≠ 0
    require q ≠ 1
    ensures out = reduced q factors

The method rewrites the list of non-modular factors of a product against a
modulus ``q``: each factor is reduced INDEPENDENTLY, preserving order and
length. The single load-bearing ``ensures`` pins ``out`` to the deep,
fully-unfolded ``reduced q factors`` (the ``axioms`` region is empty — no opaque
answer key to echo). ``reduced`` maps ``reduceFactor q`` over the list, and
``reduceFactor`` composes THREE independently-attackable per-factor outcomes:

  * SHRINK — an integer-literal factor (``.num n``) whose residue ``Int.fmod n q``
    is NON-ZERO collapses to that residue (``.num (Int.fmod n q)``). This is the
    discriminating content the failing scenario observes: an integer coefficient
    with a non-zero residue must SHRINK, not stay as it was.
  * KEEP-MULTIPLE — an integer-literal factor whose residue is ZERO (a multiple
    of ``q``) is left EXACTLY as it was (``.num n``), NOT collapsed to ``.num 0``.
  * KEEP-OPAQUE — a non-integer factor (``.sym k``) is left exactly as it was;
    the reduction never inspects or rewrites an opaque factor.

The residue uses the FLOORED (sign-of-divisor) remainder ``Int.fmod`` — matching
the repo's integer ``%`` — so on a negative ``q`` it differs from the
always-non-negative ``Int.emod``; that sign convention is part of the pinned
behaviour.

TWO INPUT BINDERS, both load-bearing: ``factors : List Factor`` (elements are
``.num`` or ``.sym``; selects which per-factor outcome fires, at which position)
and ``q : Int`` (the modulus, which fixes the residue and its sign). The reject
witnesses drive them to SIX distinct input points and between them move
``factors`` across ``.num``/``.sym``, across list length {1, 2}, across the
first and last positions, and move ``q`` across {2, 4, -3} (including a negative
divisor) — so a rival mishandling only one per-factor case, one position, or one
sign is caught, and no binder is pinned at a single value across the reject set.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHICH IMPL EACH WITNESS IS REFUTED
AGAINST. A witness reaches the post-image through Velvet's tester machinery
(``reduceModFactorsTester factors q = false`` says the extracted program's result
violates the postcondition at that concrete input) and closes by ``decide``,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. ``decide`` reduces the extracted program by kernel
computation, and each reject rival is expressed as a LOOP-FREE impl (a single
``return`` over ``reduced`` / ``List.map`` / a ``match``) so its extracted tester
``decide``s over the concrete literal. That is a witnessing convenience, not a
weakening: the frozen spec is untouched and each rival's divergence from
``reduced`` is real at the witnessed input.

The frozen impl, however, is a ``while`` loop under ``loom.semantics.choice
"demonic"``: it elaborates through ``Classical.choice``, which the kernel cannot
unfold, so ``decide`` against the FROZEN solution does not evaluate the claim at
all. Measured, all six witnesses, exit 1 with

    Tactic `decide` failed ... its `Decidable` instance ... did not reduce to
    `isTrue` or `isFalse`

That is a STUCK REDUCTION, and it must NOT be read as the FAIL-on-gold half: the
identical error appears for a TRUE claim about the frozen impl, so gold's exit
code here carries no information (the gate screens exactly this — see
``_STUCK_REDUCTION`` in ``swebench_unified.gates.pbt``, and the audit re-measured
it: a FORGERY asserting the rival is CORRECT at an agreement point
(``[Factor.sym 0]``, q=2, ``... = true``) also builds green on the rival and
fails on gold with the same stuck error).

What actually discriminates these witnesses is the gate's fallback subject: when
the frozen impl cannot decide, the witness is refuted instead against a
VERIFYING positive of this same spec — here ``pos-control-direct-model``, which
is loop-free and therefore reduces. The gate checks that subject shares the
frozen spec and verifies before using it, and an impl the verifier accepts cannot
violate its own spec, so a witness that fails there is a genuine refutation. Each
witness was rebuilt three ways by the audit: green on its rival (exit 0), stuck
on the frozen loop (exit 1, no verdict), and SEMANTICALLY refuted on the
loop-free positive (exit 1, ``Tactic `decide` proved that the proposition
... is false``) — the last being the real evidence. The forgery above is caught
on that same subject: it builds green there, so the gate records it
``witness-vacuous`` rather than a refutation. meta.json records this per case as
``witness_subject = "a verifying positive from this battery (gold cannot
decide)"``; the reject lane therefore DEPENDS on ``pos-control-direct-model``
continuing to verify, which is its own gate case.

The arguments are small ``Factor`` literals and integer literals; ``Int.fmod`` is
fully ``decide``-able (verified: ``Int.fmod 3 2 = 1``, ``Int.fmod 8 4 = 0``,
``Int.fmod 7 (-3) = -2``, and ``(7 : Int) % (-3) = 1`` for the sign contrast), so
no conditioning on an opaque term is needed.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl must verify, else the spec is SPEC-TOO-STRONG
    on the shape of the impl. Two are shipped: a loop-free direct return of the
    grounded model (maximally different control flow, reproved by bare
    ``loom_solve``), and a loop-PRESERVING reshape that names the reduced factor
    in a local ``let`` and keeps the frozen proof script intact.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    fractional-permission precondition. This backend's ``require`` is ``q ≠ 0 ∧
    q ≠ 1`` (met by every modeled ``q``) and there is no permission surface, so
    that probe is degenerate; the residual risk is a DEGENERATE post-image.
    ``admiss-nondegenerate`` discharges an in-region ``assert`` pinning all THREE
    per-factor outcomes (shrink / keep-multiple / keep-opaque) at F2P-shaped
    inputs; the impl is kept verbatim so the method's own obligation still
    discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries two frame
    rivals because its read-only inputs are held at a fractional heap permission
    (``Acc(.,1/2)``) an impl could illegally overwrite. Lean/Velvet are
    referentially transparent: ``factors`` is an immutable ``List Factor`` value
    declared read-only (NOT ``mut``), there is no heap, no aliasing, and no
    permission system. There is no read-only input to overwrite and no frame
    clause to trip, so the class has no carrier analogue. NOT ported (fabricating
    a substitute would test nothing). See the footer for the case-by-case
    accounting.
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE CARRIER, not a hole. This bundle
    sets ``loom.semantics.termination "total"`` (line 4 of the frozen file) and the
    frozen loop carries an explicit ``decreasing i``, so the verifier discharges a
    TERMINATION obligation in addition to the value clause. A diverging rival is
    therefore genuinely REJECTED rather than vacuously admitted, and it is rejected
    for the divergence itself: measured, the canonical diverging-prefix probe
    (``while True do pure ()`` spliced at the top of the frozen impl region, proof
    reduced to a bare ``loom_solve``) exits 1 with

        error: Decreasing annotations are required in total correctness semantics

    and a loop written WITHOUT a ``decreasing`` clause fails the same way. Supplying a
    measure that does not decrease does not help either, and it is the sharper probe
    because it cannot be dismissed as merely missing the annotation: a loop CARRYING
    such a measure (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q``, body ``q := q``) is REJECTED on the measure's OWN goal -
    ``case «decreasing_1: q»``, residual ``⊢ q_1 < q_1`` - alongside the ordinary
    value goal (``⊢ factors = reduced q factors``). So a postcondition here is claimed
    of ALL runs and recording a "known spec hole" for this class would misdescribe the
    artifact. (An earlier version of this passage reached the same disposition by
    excluding the cell from "the 401 velvet bundles set to ``"partial"``" in an
    internal findings doc. That cohort is withdrawn: all 500 velvet bundles set
    ``"total"`` and open ``TotalCorrectness``.)
    Nothing is shipped in the reject lane for the class all the same, and the
    reason is a WITNESS limit rather than a spec limit: a diverging rival's
    rejection is already attributable to the frozen ``decreasing`` obligation
    (the error above names it), and the witness machinery cannot add anything —
    measured, the tester witness against a diverging rival gets STUCK
    (``Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse```),
    which the gate screens as ``witness-undecided``, so such a case could only ever
    land as inconclusive MALFORMED-TESTS, never as a refutation. The sibling
    carries no ``diverge-*``/``nonterm-*`` case for this instance either.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``reduced q
    factors``, a fully-unfolded ``def`` over the method's own arguments; there is
    no answer-key term a wrong impl could echo. The cheapest correct impl
    computes the reduction honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (never shrink; collapse a
    multiple to zero; rewrite an opaque factor; use the wrong-sign residue; miss
    the first or the last position).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15599"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Rivals that reshape the executable surface into a
# ---- loop-free closed form, and the direct-return positive, swap on this block.
_IMPL = """    -- impl-start
    let mut result : List Factor := []
    let mut i := factors.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ factors.length
      invariant result = reduced q (factors.drop i)
      done_with i = 0
      decreasing i
    do
      let f := factors[i - 1]!
      result := reduceFactor q f :: result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the loop-body lines, wholly inside the impl region and unique. The
# ---- loop-preserving positive reshapes only these (naming the reduced factor in
# ---- a local `let`), leaving the loop, invariants and frozen proof intact.
_LOOP_BODY = """    do
      let f := factors[i - 1]!
      result := reduceFactor q f :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, retunes it without
# ---- touching the spec or dropping the `prove_correct reduceModFactors`
# ---- obligation.
_PROOF_GOLD = """prove_correct reduceModFactors by
  loom_solve
  rw [reduced_drop_step q factors i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equality (for
# ---- a correct reshape) or leaves it unsolved (for the reject rivals, which is
# ---- the point). Reject rivals retune the proof to this shape so the rejection
# ---- is attributable to the spec (via the witness), not to a proof script tuned
# ---- to a loop that no longer exists.
_PROOF_FLAT = "prove_correct reduceModFactors by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned to the flat shape."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `reduceModFactorsTester factors q = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped. Every argument is
# ---- a concrete literal so `decide` reduces the (loop-free) extracted rival
# ---- program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for reduceModFactors\n"
            "prove_precondition_decidable_for reduceModFactors\n"
            "prove_postcondition_decidable_for reduceModFactors\n"
            "derive_tester_for reduceModFactors\n\n" + body)


def _witness(factors_literal, q):
    return _tester(
        f"example : reduceModFactorsTester ({factors_literal} : List Factor) "
        f"({q} : Int) = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold backward
        # scan. `out` IS `reduced q factors`, so the ensures holds trivially; the
        # reproof is a bare `loom_solve` (no loop invariant to peel).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return reduced q factors\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`reduced q factors` directly (no loop). `out` IS that model, so the "
            "ensures holds on the whole domain; the reproof is `loom_solve`. If "
            "this fails to verify the spec is over-fit to the scan code shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: the "
            "model IS the reduction work, so a direct return is correct, not a "
            "cheat. (Sibling: pos-control-echo-reduced-factor — the same "
            "cheapest-correct shape, which binds v = reduced_factor(...) directly.)"),
    },
    {
        "id": "pos-control-named-factor",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, the invariants and the FROZEN proof script; only
        # names the reduced factor in a local `let` before prepending it.
        # Observationally identical for every input, so the frozen proof still
        # closes (verified during authoring).
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    do\n"
            "      let f := factors[i - 1]!\n"
            "      let g := reduceFactor q f\n"
            "      result := g :: result\n"
            "      i := i - 1"),
        "rationale": (
            "naming the reduced factor in a local `let g := reduceFactor q f` "
            "before prepending it prepends the same value in the same order, so "
            "`out = reduced q factors` still holds on the whole domain; the loop, "
            "invariants and frozen proof script are untouched. A correct reshape "
            "must verify, else the postcondition is SPEC-TOO-STRONG (rejects a "
            "faithful impl over the shape of the loop body). (Sibling: "
            "pos-control-guard-inversion, re-shaped to a loop-preserving form that "
            "keeps the frozen proof intact.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's `require` (`q ≠ 0 ∧ q ≠ 1`) is met by every
    # F2P-shaped modulus, so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here. The residual admissibility risk on
    # this domain is that the post-image is DEGENERATE at the interesting point.
    # This case discharges an in-region `assert`, at fully concrete F2P-shaped
    # inputs, that the per-factor reduction is NON-DEGENERATE: an integer
    # coefficient with non-zero residue SHRINKS (3 mod 2 -> 1), a multiple of the
    # modulus is KEPT (8 mod 4 -> 8, not 0), and an opaque factor is KEPT. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      reduceFactor 2 (Factor.num 3) = Factor.num 1 ∧\n"
                  "      reduceFactor 4 (Factor.num 8) = Factor.num 8 ∧\n"
                  "      reduceFactor 2 (Factor.sym 3) = Factor.sym 3 ∧\n"
                  # ...and the WHOLE post-image at F2P-shaped inputs, not just the
                  # per-factor outcomes: the obligation `out = reduced q factors`
                  # must be SATISFIABLE at the concrete points the reject lane
                  # witnesses at, discharged here by evaluation before the frozen
                  # obligation closes verbatim. An obligation unsatisfiable at an
                  # F2P-shaped input is the total-carrier analogue of
                  # PRECOND-TOO-STRONG, which the three per-factor conjuncts alone
                  # do not reach (they never mention `reduced`).
                  "      reduced 2 [Factor.num 3, Factor.sym 0]\n"
                  "        = [Factor.num 1, Factor.sym 0] ∧\n"
                  "      reduced 4 [Factor.num 8, Factor.sym 0]\n"
                  "        = [Factor.num 8, Factor.sym 0] ∧\n"
                  "      reduced (-3) [Factor.num 7] = [Factor.num (-2)]))\n"),
            _PROOF_GOLD,
            "prove_correct reduceModFactors by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [reduced_drop_step q factors i (by omega) (by omega)]\n"
            "       simp_all)\n"),
        "rationale": (
            "TWO obligations, both discharged by evaluation at concrete F2P-shaped "
            "inputs before the frozen obligation closes verbatim. (i) The per-factor "
            "reduction is NON-DEGENERATE: an integer coefficient with non-zero "
            "residue must SHRINK (3 mod 2 -> 1, the issue's exact discriminator), a "
            "multiple of the modulus must be KEPT unchanged (8 mod 4 -> 8, NOT 0), "
            "and an opaque factor must be KEPT — three distinct outcomes. (ii) The "
            "method's own post-image `reduced q factors` is SATISFIABLE at the "
            "points the reject lane witnesses at — `reduced 2 [.num 3, .sym 0] = "
            "[.num 1, .sym 0]`, `reduced 4 [.num 8, .sym 0] = [.num 8, .sym 0]`, "
            "`reduced (-3) [.num 7] = [.num (-2)]` (both signs of `q`). That second "
            "group is the real admissibility content on a TOTAL carrier: the "
            "analogue of PRECOND-TOO-STRONG here is the obligation being "
            "UNSATISFIABLE at exactly an F2P-shaped input, which the three "
            "per-factor conjuncts cannot detect because they never mention "
            "`reduced`. If any conjunct fails to discharge, the obligation is "
            "degenerate or unsatisfiable where it matters; the impl is kept verbatim "
            "so `out = reduced q factors` still verifies for the whole domain. "
            "Measured LIVE on the truth of its conjuncts, not their shape: flipping "
            "the keep-multiple conjunct to `= Factor.num 0` FAILS (exit 1), swapping "
            "it for a different TRUE claim of the same shape "
            "(`reduceFactor 4 (Factor.num 12) = Factor.num 12`) still verifies, and "
            "flipping the post-image conjunct to the un-shrunk "
            "`reduced 2 [.num 3, .sym 0] = [.num 3, .sym 0]` FAILS (exit 1). "
            "(Sibling: admiss-f2p-shaped, re-aimed from permission admissibility — "
            "this backend's require is `q ≠ 0 ∧ q ≠ 1` and there is no permission "
            "surface — to post-image non-degeneracy AND satisfiability.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a LOOP-FREE
    # closed form (single expression / match over the pure helpers) so its
    # extracted tester `decide`s (see the CARRIER NOTE); the frozen spec is
    # untouched.
    # =====================================================================
    {
        "id": "reject-prepatch-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # The LITERAL pre-patch behaviour: every factor passes through unchanged,
        # no residue is ever taken. Correct on opaque factors and on multiples of
        # the modulus; WRONG on any integer coefficient with a non-zero residue.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return factors\n"
            "    -- impl-end"),
        "refinement": (
            "this is the exact pre-change behaviour (the factor list is passed "
            "through unchanged, no per-factor residue is taken). On the reported "
            "scenario an integer coefficient with a non-zero residue stays as it "
            "was instead of shrinking to its residue, so the product does not "
            "collapse the way the issue requires — the failing test still fails. A "
            "faithful patch that never reduced any factor would NOT resolve; this "
            "is the canonical verify-not-resolve rival."),
        "rationale": (
            "REJECT from `out = reduced q factors` via the SHRINK outcome: on an "
            "integer-literal factor whose residue is non-zero the spec demands "
            "`.num (Int.fmod n q)`, this rival returns `.num n`. Verifying would "
            "mean the coefficient reduction is unpinned (partial-domain "
            "SPEC-TOO-WEAK). Refuted at factors=[.num 3], q=2 (gold shrinks 3 to "
            "1). (Sibling: partial-domain-prepatch-passthrough.)"),
        "witness": _witness("[Factor.num 3]", "2"),
    },
    {
        "id": "reject-drop-residue-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `Int.fmod n q ≠ 0` guard: an integer factor is ALWAYS collapsed
        # to its residue, even when that residue is 0 (a multiple of the modulus).
        # Correct on non-zero-residue coefficients and on opaque factors; WRONG on
        # any integer multiple of q whose value is itself non-zero.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (factors.map (fun f => match f with\n"
            "      | .num n => .num (Int.fmod n q)\n"
            "      | .sym k => .sym k))\n"
            "    -- impl-end"),
        "refinement": (
            "dropping the non-zero-residue guard rewrites an integer factor that "
            "is a multiple of the modulus to its residue 0 instead of keeping it, "
            "collapsing a non-zero coefficient (e.g. a factor of 8 against modulus "
            "4 becomes 0). The surrounding tests require such multiples to be "
            "preserved (a product carrying that coefficient must not become 0), so "
            "a patch dropping the guard would NOT resolve. Correct on every "
            "non-zero-residue coefficient and every opaque factor (a true "
            "partial-domain break on the keep-multiple sub-domain)."),
        "rationale": (
            "REJECT from `out = reduced q factors` via the KEEP-MULTIPLE outcome: "
            "on an integer factor whose residue is zero but whose value is non-zero "
            "the spec demands `.num n`, this rival returns `.num 0`. Verifying "
            "would leave the keep-multiple case unpinned (SPEC-TOO-WEAK). Refuted "
            "at factors=[.num 8], q=4 (gold keeps 8; residue is 0). (Sibling: "
            "partial-domain-drop-residue-guard.)"),
        "witness": _witness("[Factor.num 8]", "4"),
    },
    {
        "id": "reject-reduce-opaque",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the is-integer guard: reduce EVERY factor to its residue, even
        # opaque ones (treat a `.sym k` code as if it were an integer literal).
        # Correct on integer factors; WRONG on any opaque factor whose code has a
        # non-zero residue — the spec keeps every opaque factor unchanged.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (factors.map (fun f => match f with\n"
            "      | .num n => (if Int.fmod n q ≠ 0 then .num (Int.fmod n q) else .num n)\n"
            "      | .sym k => (if Int.fmod k q ≠ 0 then .sym (Int.fmod k q) else .sym k)))\n"
            "    -- impl-end"),
        "refinement": (
            "the spec reduces only integer-literal factors and leaves every "
            "opaque (non-integer) factor exactly as it was. A patch that applied "
            "the residue rewrite to a non-integer factor would corrupt the "
            "symbolic part of the product — the opaque factors the surrounding "
            "assertions rely on surviving would be rewritten — so it would NOT "
            "resolve. Correct on every integer factor (a partial-domain break on "
            "the keep-opaque sub-domain)."),
        "rationale": (
            "REJECT from `out = reduced q factors` via the KEEP-OPAQUE outcome: on "
            "an opaque factor `.sym k` with a non-zero residue the spec demands "
            "`.sym k`, this rival returns `.sym (Int.fmod k q)`. Verifying would "
            "mean opaque factors are not pinned as preserved (SPEC-TOO-WEAK). "
            "Refuted at factors=[.sym 3], q=2 (gold keeps .sym 3; the rival "
            "rewrites it — moving the factor binder onto the .sym constructor no "
            "other rival exercises). (Sibling: partial-domain-drop-is-int-guard.)"),
        "witness": _witness("[Factor.sym 3]", "2"),
    },
    {
        "id": "reject-wrong-residue-sign",
        "kind": "uniqueness",
        "expect": "reject",
        # Use the always-non-negative `Int.emod` (Lean's `%`) instead of the
        # floored `Int.fmod`. Identical on a positive modulus; WRONG on a negative
        # modulus, where the spec's sign-of-divisor residue differs. This is the
        # binder-attack on `q`: the only rival that drives the modulus negative.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (factors.map (fun f => match f with\n"
            "      | .num n => (if n % q ≠ 0 then .num (n % q) else .num n)\n"
            "      | .sym k => .sym k))\n"
            "    -- impl-end"),
        "refinement": (
            "the modeled residue is the FLOORED (sign-of-divisor) remainder, "
            "matching the repo's integer `%`: on a negative modulus it is "
            "negative, whereas the always-non-negative remainder is not. A patch "
            "using the wrong-sign remainder would give the wrong reduced "
            "coefficient for a negative modulus, so the scenarios that exercise a "
            "negative divisor (mapping.md §4 pins both signs) would NOT resolve. "
            "Correct on every positive modulus (a partial-domain break on the "
            "negative-`q` sub-domain)."),
        "rationale": (
            "REJECT from `out = reduced q factors`: the spec's residue is "
            "`Int.fmod n q`, this rival uses `n % q` (Int.emod). They agree for "
            "q > 0 but differ in sign for q < 0 (Int.fmod 7 (-3) = -2 vs "
            "7 % -3 = 1). Verifying would mean the residue sign convention is "
            "unpinned (SPEC-TOO-WEAK). Refuted at factors=[.num 7], q=-3 — the "
            "witness that makes the `q` binder load-bearing by driving the modulus "
            "negative, which no other rival does. (Sibling: no direct sibling — "
            "the sign convention is a carrier-specific clause the deep model pins "
            "explicitly, mapping.md §2; added to defend the `q` binder.)"),
        "witness": _witness("[Factor.num 7]", "-3"),
    },
    {
        "id": "reject-first-factor-unreduced",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct EVERYWHERE except the first factor, which is passed through
        # unreduced. A near-miss that pins every position but the head; refuted at
        # a length-2 list whose head is a reducible coefficient.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    match factors with\n"
            "    | [] => return []\n"
            "    | f :: fs => return (f :: fs.map (reduceFactor q))\n"
            "    -- impl-end"),
        "refinement": (
            "special-casing the first factor to pass through unreduced leaves a "
            "leading integer coefficient un-shrunk while reducing the rest, so a "
            "product whose leading factor is a reducible coefficient would not "
            "collapse it — the failing scenario (leading coefficient) still fails. "
            "A real first-element bug would NOT resolve. Correct on every trailing "
            "factor (a single-position partial-domain break)."),
        "rationale": (
            "REJECT from `out = reduced q factors` at position 0: the head is "
            "returned unchanged where the spec demands `reduceFactor q` of it. "
            "Verifying would leave the first position unpinned (partial-domain "
            "SPEC-TOO-WEAK). Refuted at factors=[.num 3, .sym 0], q=2 (gold shrinks "
            "the head 3 to 1; the rival keeps it) — a length-2 list exercising the "
            "head position and the traversal. (Sibling: "
            "partial-domain-first-factor-zero.)"),
        "witness": _witness("[Factor.num 3, Factor.sym 0]", "2"),
    },
    {
        "id": "reject-last-factor-unreduced",
        "kind": "uniqueness",
        "expect": "reject",
        # Symmetric near-miss: correct EVERYWHERE except the last factor, which is
        # passed through unreduced. Refuted at a length-2 list whose tail is a
        # reducible coefficient — the opposite position from the head rival, so
        # the two do not share a witness.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    match factors.reverse with\n"
            "    | [] => return []\n"
            "    | f :: fs => return ((fs.map (reduceFactor q)).reverse ++ [f])\n"
            "    -- impl-end"),
        "refinement": (
            "special-casing the LAST factor to pass through unreduced leaves a "
            "trailing integer coefficient un-shrunk while reducing the rest, so a "
            "product whose trailing factor is a reducible coefficient would not "
            "collapse it. A real last-element bug would NOT resolve. Correct on "
            "every leading factor (the dual single-position break, disjoint from "
            "the first-factor rival)."),
        "rationale": (
            "REJECT from `out = reduced q factors` at the last position: the tail "
            "factor is returned unchanged where the spec demands `reduceFactor q` "
            "of it. Verifying would leave the last position unpinned (partial-"
            "domain SPEC-TOO-WEAK). Refuted at factors=[.sym 0, .num 3], q=2 (gold "
            "shrinks the trailing 3 to 1; the rival keeps it) — the trailing "
            "position, which the first-factor rival gets right, so the two rivals "
            "do NOT share a witness. (Sibling: partial-domain-last-factor-zero.)"),
        "witness": _witness("[Factor.sym 0, Factor.num 3]", "2"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 10 SPEC cases (2
# soundness positives, 1 admissibility, 7 uniqueness — two of which are mandatory
# frame-mutation rivals) plus a THREE-probe AXIOM lane (residue soundness /
# containment, reduced_factor fidelity). The sibling contracts
# `reduce_coefficients(is_int: List[int], value: List[int], m: int)` over TWO
# read-only permission-carrying list inputs (a parallel is-integer tag list and a
# value list) plus the modulus.
#
# This velvet bundle models the SAME per-factor residue rewrite DEEPLY and
# CONCRETELY (`reduceFactor` / `reduced` over the `Factor` carrier). The sibling's
# two parallel inputs (`is_int[k]`, `value[k]`) are FUSED into one `Factor` per
# position: `.num n` is the (is_int=1, value=n) integer-literal case and `.sym k`
# is the (is_int=0) opaque case. That fusion is faithful (the reduction observes
# only whether a factor is an integer literal and, if so, its residue —
# mapping.md §2) and it is what collapses the two sibling frame rivals into the
# vacuous class and re-expresses the two guard-drop rivals over one carrier.
#
#   sibling case                          kind          -> here                        disposition
#   -------------------------------------------------------------------------------------------------
#   pos-control-echo-reduced-factor       soundness     -> pos-control-direct-model    PORTED
#   pos-control-guard-inversion           soundness     -> pos-control-named-factor    RE-SHAPED
#   admiss-f2p-shaped                      admissibility -> admiss-nondegenerate        RE-AIMED
#   frame-mutate-readonly-value           uniqueness    -> (none)                       VACUOUS
#   frame-mutate-readonly-is-int          uniqueness    -> (none)                       VACUOUS
#   partial-domain-prepatch-passthrough   uniqueness    -> reject-prepatch-passthrough  PORTED
#   partial-domain-drop-is-int-guard      uniqueness    -> reject-reduce-opaque         PORTED
#   partial-domain-drop-residue-guard     uniqueness    -> reject-drop-residue-guard    PORTED
#   partial-domain-first-factor-zero      uniqueness    -> reject-first-factor-unreduced PORTED
#   partial-domain-last-factor-zero       uniqueness    -> reject-last-factor-unreduced  PORTED
#   (no sibling — sign convention)        uniqueness    -> reject-wrong-residue-sign     ADDED
#   AXIOM_TESTS (residue / reduced_factor) axiom         -> (none)                        DROPPED (G-AX)
#
# 5 uniqueness ported + 1 added, 2 soundness ported/re-shaped, 1 admissibility
# re-aimed; 2 uniqueness vacuous; axiom lane dropped.
#
# PORTED (pos-control-echo-reduced-factor -> pos-control-direct-model): the
#   sibling's cheapest correct shape binds v = reduced_factor(...) directly. Here
#   the maximally-different correct impl is a loop-free direct return of the
#   grounded model `reduced q factors`; a second loop-PRESERVING correct reshape
#   (pos-control-named-factor) re-shapes the sibling's guard-inversion positive to
#   name the reduced factor in a local `let` — keeping the frozen proof intact, so
#   the soundness surface is defended from a completely different control-flow
#   shape AND from a minimal in-loop edit.
# RE-AIMED (admiss-f2p-shaped -> admiss-nondegenerate): the sibling asserts the
#   permission precondition admits an F2P-shaped input. This backend's require is
#   `q ≠ 0 ∧ q ≠ 1` (met by every modeled modulus) and there is no permission
#   surface, so that probe is degenerate; the sharper residual risk is a
#   DEGENERATE post-image, so the case is re-aimed to a live in-region assert
#   pinning all THREE per-factor outcomes (shrink / keep-multiple / keep-opaque)
#   at F2P-shaped inputs, including the issue's exact 3-mod-2 -> 1 discriminator.
# PORTED (the four value/branch rivals): prepatch-passthrough ports directly
#   (pass every factor through — the literal regression; refuted on a reducible
#   coefficient). drop-is-int-guard ports to reject-reduce-opaque (reduce opaque
#   factors too; refuted on a .sym factor with non-zero residue). drop-residue-
#   guard ports directly (always take the residue, even for multiples; refuted on
#   a multiple of the modulus). first/last-factor-zero port to the two
#   single-position near-misses (head/tail passed through unreduced; refuted on
#   length-2 lists at opposite positions, so they do not share a witness). The
#   sibling forces the missed position to a fixed 0; here the equivalent single-
#   position miss is "pass through unreduced", which is refutable at the same
#   reducible-coefficient input and is the natural carrier shape.
# ADDED (reject-wrong-residue-sign): mapping.md §2 pins the residue to the FLOORED
#   remainder `Int.fmod` (the repo's integer `%`), explicitly noting the
#   always-non-negative `Int.emod` would be WRONG for a negative modulus. That
#   sign convention is a carrier-specific clause with no single sibling rival
#   (nagini's `residue` primitive is validated by its AXIOM lane instead); it is
#   attacked here so the `q` binder is demonstrated load-bearing across sign, the
#   one dimension the ported rivals (all at q ∈ {2,4}) leave un-probed.
# VACUOUS (frame-mutate-readonly-value, frame-mutate-readonly-is-int): the two
#   sibling frame rivals write into a read-only permission-carrying input
#   (`value[0] = 0` / `is_int[0] = 0`) and are rejected for insufficient
#   fractional permission. This backend is referentially transparent: `factors`
#   is an immutable `List Factor` value declared read-only (NOT `mut`), there is
#   no heap, no aliasing, no `Old`, and no permission system. There is no read-
#   only input to overwrite and no frame clause to violate, so the class has no
#   carrier analogue. Omitted as a genuine carrier fact, NOT fabricated (the
#   porting map marks the frame/permission class VACUOUS on a referentially-
#   transparent backend).
#
#   DEMONSTRATED rather than asserted — the two ways such a rival could be
#   written are both unavailable, and each was measured:
#     (a) assigning to the input inside the impl region (`factors := []` before
#         returning) does not express a frame violation, it fails to ELABORATE:
#           error: `factors` cannot be mutated, only variables declared using
#           `let mut` can be mutated
#         so there is no admissible rival here to reject — the surgery yields an
#         uncompilable file, not a wrong impl. A case built on it would be
#         `witness-unproven` (the rival build is the half that must succeed), an
#         inconclusive MALFORMED-TESTS, never a refutation.
#     (b) making the input writable at all requires `mut` on the METHOD
#         SIGNATURE, which lives in the consumer spec view: checked with
#         `variant_scope.variant_problems`, that variant is rejected before any
#         build with `['spec view differs (same_spec failed)']`. So the mutation
#         the sibling rivals perform is not merely absent from this battery — it
#         is not expressible by ANY admissible same-spec variant.
#   The directive-5 concern it maps to (that `factors` survives unchanged) is
#   therefore discharged structurally by the two facts above, and the ensures
#   pins `out` to `reduced q factors` computed from the intact input.
# DROPPED (AXIOM_TESTS): the sibling's three AXIOM_TESTS validate its
#   @ContractOnly `residue` primitive and its A-reference `reduced_factor` deep
#   model against the real sympy callee. This bundle has NO axiom and NO A-
#   reference oracle (mapping.md §1: "There are no axioms in this bundle and no
#   axiom_check.py"; the residue rewrite is modeled deeply by reduceFactor/reduced
#   over Int.fmod, carried by G-CONF). There is no axiom lane to mirror, and this
#   gate ignores AXIOM_TESTS regardless. AXIOM_TESTS is empty below.
#
# DIVERGENCE lane: the sibling carries NO diverge-*/nonterm-*/weak-diverge case
#   for this instance, so there is nothing to port — and on THIS carrier there is
#   also no hole to record. This bundle sets
#   `set_option loom.semantics.termination "total"` (frozen file line 4), not
#   "partial", and the frozen loop carries `decreasing i`, so the verifier
#   discharges a termination obligation and a diverging impl is REJECTED rather
#   than vacuously admitted. An earlier revision of this footer placed the cell inside
#   a cohort of "401 `partial` bundles" from an internal findings doc; that cohort is
#   withdrawn, since all 500 velvet bundles now read "total" and open
#   TotalCorrectness. The refusal is also not just the annotation linter: a loop
#   CARRYING a measure that does not decrease (`while q > 0 ... decreasing q`, body
#   `q := q`) is rejected on the measure's own goal -- `case «decreasing_1: q»`,
#   residual `q_1 < q_1`. Re-measured with real builds against the CURRENT
#   frozen file:
#     * canonical diverging prefix (`while True do pure ()` at the top of the impl
#       region, bare `loom_solve`)          exit 1, "Decreasing annotations are
#                                           required in total correctness semantics"
#     * a `while` loop with no `decreasing` clause at all, wrong return
#                                           exit 1, same decreasing-annotation error
#     * a loop WITH `decreasing` whose measure never decreases, wrong return
#                                           exit 1, unsolved `⊢ factors = reduced q
#                                           factors` (the ordinary value goal)
#   So the class is closed by the carrier. Nothing is shipped in the reject lane
#   for it anyway, and the reason is a WITNESS limit, not a spec limit: the
#   rejection above is already attributable to the frozen `decreasing` obligation,
#   and a tester witness cannot corroborate it — measured, the witness against a
#   diverging rival gets STUCK (`Tactic `decide` failed ... did not reduce to
#   `isTrue` or `isFalse``), which the gate screens as `witness-undecided`, so the
#   case could only land as inconclusive MALFORMED-TESTS.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = reduced q factors`
#   has TWO binders — `factors : List Factor` (elements are `.num`/`.sym`) and
#   `q : Int` — and `reduceFactor` has THREE independent per-factor outcomes
#   (shrink / keep-multiple / keep-opaque) plus the residue sign convention. The
#   six reject witnesses probe six DISTINCT input points (pts=6):
#     * reject-prepatch-passthrough    [.num 3]           q=2   (shrink)
#     * reject-drop-residue-guard      [.num 8]           q=4   (keep-multiple)
#     * reject-reduce-opaque           [.sym 3]           q=2   (keep-opaque)
#     * reject-wrong-residue-sign      [.num 7]           q=-3  (residue sign)
#     * reject-first-factor-unreduced  [.num 3, .sym 0]   q=2   (position 0 / traversal)
#     * reject-last-factor-unreduced   [.sym 0, .num 3]   q=2   (last position / traversal)
#   So the `factors` binder ranges over both constructors (.num and .sym), over
#   list length {1, 2}, and over the first and last positions; the `q` binder
#   ranges over {2, 4, -3} INCLUDING a negative divisor (reject-wrong-residue-
#   sign is the sole point that makes the sign of `q` load-bearing — every other
#   point holds q > 0). All THREE per-factor outcomes are attacked (shrink /
#   keep-multiple / keep-opaque) plus the sign convention and the per-position
#   traversal. No binder is pinned at a single value across the reject set. Both
#   the clause and the per-factor outcomes are also DEFENDED by two verifying
#   soundness positives and the admissibility non-degeneracy assert.
#
# INDEPENDENT AUDIT PROBES (not shipped as cases — recorded so the next reader
#   knows what was already tried and need not re-spend the builds). All were run
#   with `scripts/lean_verify.sh` against the FROZEN spec.
#
#   SPEC-TOO-WEAK probes (new WRONG impls aimed at what the six rivals leave
#   un-probed). Every one was REJECTED, each on the `ensures_1: out = reduced q
#   factors` goal — so no spec hole was found:
#     * order-only break: `return (reduced q factors).reverse`            reject
#     * length-only break: drop the last element after a correct map      reject
#     * `q`-blind: reduce against a hardcoded 2, ignoring the argument    reject
#     * duplicate the (correctly reduced) head — length + multiplicity    reject
#     * correct on EVERY singleton, swaps the first two otherwise (aimed
#       at the four length-1 witnesses)                                   reject
#     * correct except at index 2 (no shipped witness exceeds length 2)   reject
#     * wrong ONLY at q = 5, a modulus no shipped witness uses            reject
#   The last three matter most: they target exactly the gaps the shipped witness
#   set has (list length ≤ 2, q ∈ {2,4,-3}), and the spec still catches them —
#   the `ensures` is an extensional equality on the whole list, so it does not
#   depend on the reject lane happening to sample a given length or modulus.
#
#   SPEC-TOO-STRONG probes (new CORRECT reshapes; each MUST verify, and did):
#     * `return (factors.map (reduceFactor q))` — a fold shape the frozen
#       front-recursive `reduced` is only propositionally equal to; needs one
#       `induction` bridge lemma, then verifies                           verify
#     * front-recursive match `f :: fs => reduceFactor q f :: reduced q fs`,
#       reproved by bare `loom_solve`                                     verify
#     * a FORWARD `while` loop appending with a `take`-based invariant — the
#       opposite traversal direction from the frozen backward scan, needing its
#       own take-step lemma                                               verify
#   So the spec is not over-fit to the frozen backward-scan shape, in either
#   control flow or fold direction.
#
#   ADMISSIBILITY LIVENESS. `admiss-nondegenerate`'s in-region assert was probed
#   for decorativeness: flipping ONE conjunct to a FALSE claim
#   (`reduceFactor 4 (Factor.num 8) = Factor.num 0`) makes the case FAIL to
#   verify, while swapping the same conjunct for a DIFFERENT TRUE claim of the
#   same shape (`reduceFactor 4 (Factor.num 12) = Factor.num 12`) still verifies.
#   The assert is therefore live on the TRUTH of its conjuncts, not merely on
#   their syntactic shape. Re-measured by the independent audit after the
#   post-image conjuncts were added: the strengthened assert verifies (exit 0) and
#   flipping the post-image conjunct to the un-shrunk `reduced 2 [.num 3, .sym 0]
#   = [.num 3, .sym 0]` FAILS (exit 1), so the new group is live too.
#
#   WITNESS DISCRIMINATION, RE-DERIVED BY AN INDEPENDENT AUDIT (36 builds; the
#   numbers below are observed exit codes, not expectations). For each of the six
#   reject cases the witness was built THREE ways and the claim was FORGED twice:
#     rival 0 / frozen-gold 1 / verifying-positive 1   — all six, uniformly
#   Gold's failure is the STUCK reduction (`Tactic `decide` failed ... did not
#   reduce to `isTrue` or `isFalse``, reduction stuck at the `Decidable` instance),
#   which carries NO information about the claim, and the forgery pair proves it:
#   flipping `= false` to `= true` (asserting the rival is CORRECT at that input)
#   fails against gold with the BYTE-IDENTICAL error, differing only in the `true`
#   that appears inside the quoted proposition. The real evidence is therefore the
#   third build, against the loop-free verifying positive, where the error is
#   SEMANTIC and tracks the claim exactly:
#     real witness   -> exit 1, "Tactic `decide` proved that the proposition
#                       reduceModFactorsTester <input> <q> = false is false"
#     forged witness -> exit 0 (the positive SATISFIES its spec there)
#   That asymmetry — the same subject accepting the flipped claim and refuting the
#   real one — is what makes each rejection attributable to the spec rather than to
#   a tactic mismatch, and it is why the forgery is caught as `witness-vacuous`
#   instead of being recorded as a refutation. Independently reconfirmed for the
#   manifest's own agreement-point forgery (`[Factor.sym 0]`, q=2, `= true`):
#   rival 0, gold 1 (stuck), verifying positive 0 -> `witness-vacuous`.
#
#   ATTACK C (is each rival WRONG, or merely reshaped?). Checked by evaluation in
#   the real verifier at each rival's own witness point — gold value vs rival
#   value, all six observably DIFFERENT, so no case is vacuous:
#     prepatch-passthrough    [.num 1]            vs [.num 3]
#     drop-residue-guard      [.num 8]            vs [.num 0]
#     reduce-opaque           [.sym 3]            vs [.sym 1]
#     wrong-residue-sign      [.num (-2)]         vs [.num 1]
#     first-factor-unreduced  [.num 1, .sym 0]    vs [.num 3, .sym 0]
#     last-factor-unreduced   [.sym 0, .num 1]    vs [.sym 0, .num 3]
#   The sign case is the one that could have collapsed on this carrier and does
#   not: `Int.fmod 7 (-3) = -2` while `(7 : Int) % (-3) = 1` (both #eval'd), so
#   fmod and emod are genuinely distinguished at a negative modulus.
#
#   FRAME-MUTATION VACUITY, RE-DERIVED. Both halves of the claim below were
#   rebuilt independently and both reproduce verbatim: (a) `factors := []` inside
#   the impl region fails to ELABORATE with "`factors` cannot be mutated, only
#   variables declared using `let mut` can be mutated" (so the surgery yields an
#   uncompilable file, not an admissible wrong impl); (b) adding `mut` to the
#   method signature is rejected by `variant_scope.variant_problems` as
#   `['spec view differs (same_spec failed)']` before any build. The class really
#   is inexpressible by any admissible same-spec variant here.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §1: the changed op
#   is modeled deeply and concretely over Int.fmod, validated by G-CONF, so G-AX
#   reports skip); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
