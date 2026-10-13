"""properties.py — G-PBT falsification battery for sympy__sympy-13974 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — the consumer spec view elides both, so
``markers.same_spec`` holds and BOTH ``prove_correct`` obligations survive with
their headers intact). ``expect="verify"`` passes iff (in scope AND
verifies); ``expect="reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the subject it is refuted on — for the ``distributePow``
rivals that subject is a verifying loop-free ``witness_reference`` rather than
the frozen solution, for the measured reason set out under THE DECISIVE CARRIER
FACT below; for the ``simplifyFactor`` rivals it is the FROZEN SOLUTION itself,
because that method's frozen impl is loop-free and its post-image reduces —
measured, see THE ROUTE LANE below).

DEFENDED SURFACE (TWO contracted methods over a shared purely-functional core):

  distributePow (factors : List Factor) (n : Factor) return (out : List Factor)
    ensures out = powAll n factors                            -- THE PIN

  simplifyFactor (isPowOfAggregate : Bool) (factors : List Factor)
      (n : Factor) return (out : List Factor)
    ensures out = factorImage isPowOfAggregate n factors       -- THE ROUTE
    ensures isPowOfAggregate = true → out = powAll n factors   --   raise arm
    ensures isPowOfAggregate = false → out = factors           --   passthrough arm

THE PIN's TWO INPUT binders, both load-bearing:

  * ``factors : List Factor`` — the ordered factor sequence of the aggregate.
    Its LENGTH and its ORDER are both pinned (``powAll`` is length- and
    order-preserving), and so is the identity of the factor at each POSITION.
  * ``n : Factor`` — the shared exponent, applied at every position and nowhere
    varied.

THE ROUTE's THIRD binder, and why it is a SEPARATE defended surface:

  * ``isPowOfAggregate : Bool`` — the routing flag. It says whether the factor
    being examined IS a power of the aggregate whose positions are ``factors``
    (so ``n`` is that power's exponent and the per-position raise is owed) or is
    the bare aggregate itself (so its positions are owed back untouched).

  THE PIN alone says what the per-position raise IS. It does not say WHERE the
  raise has to be reached. A rival can satisfy THE PIN completely and still only
  ever reach the raise when the power is the WHOLE expression, never when it
  occupies one factor position of a product — and such a rival leaves the
  reported behaviour unfixed at the product shapes. THE ROUTE is what closes
  that: it contracts the factor-position operation itself, with both arms pinned,
  so a rival must route a power-of-aggregate factor to the per-position raise and
  must hand a bare-aggregate factor back unchanged. The two obligations are
  independent — a rival can satisfy either while breaking the other, which is why
  each carries its own defend and attack lanes below.

``powAll`` is a transparent front-recursive ``def`` in the ``pure`` region:

    powAll n []        = []
    powAll n (b :: bs) = powF b n :: powAll n bs

so the pin decomposes into three independent structural commitments, each
attackable on its own:

  (length)    ``out.length = factors.length`` — one output factor per input
              factor, none dropped and none added;
  (order)     the k-th output factor is built from the k-th INPUT factor, so the
              sequence order survives;
  (per-pos)   the k-th output factor is ``powF factors[k] n`` — the per-factor
              operation applied to THAT position's own factor, with THAT
              exponent, in THAT argument order.

GROUNDING (why the pin is not an answer key). ``powAll`` is not an opaque
oracle: it is spelled out over the ACTUAL input list and bottoms out in one
``powF`` application per position. There is therefore no value an impl could
return that satisfies the pin without applying the per-factor operation to every
input factor — echoing ``powAll n factors`` verbatim IS doing the work, which is
exactly why ``pos-echo-direct-fold`` below is shipped as a POSITIVE control
rather than as a spec-too-weak rival. The nagini sibling reaches the same
conclusion for its own carrier by a different route (its fold has no executable
materialization at all); on this carrier the fold IS materializable, and the
grounding argument has to be made from ``powAll``'s transparency instead. That
substitution is the one place where the ported argument is genuinely re-reasoned
rather than re-spelled.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how each witness reaches the post-image.
``powF`` is ``opaque``: the specification assumes no algebraic fact about it, so
no literal input lets ``decide`` COMPUTE an output factor. Two routes make the
reject lane fully expressible anyway, and BOTH are used:

  * PER-POSITION and ORDER divergence lands inside a ``powF`` application, where
    no literal decides anything. Those six rivals are refuted by CONDITIONING ON
    THE CARRIER: the method's ``NonDetT.run`` post-image is refuted at a point
    described by hypothesis (``h : powF 5 3 ≠ 5``, ``h : powF 8 3 ≠ powF 9 3``,
    …), so the refutation holds exactly on the sub-domain where that rival
    diverges — a stronger claim than any single literal input could make.
  * STRUCTURAL divergence (a wrong output LENGTH) is a ``List`` constructor
    mismatch, settled by ``simp`` WITHOUT evaluating ``powF`` and therefore
    without any hypothesis at all — ``weak-drops-last-position`` binds nothing.

THE DECISIVE CARRIER FACT — WHY EVERY REJECT CASE NAMES A ``witness_reference``.
The frozen impl keeps a ``while`` loop and this bundle sets
``loom.semantics.choice "demonic"``, so the loop elaborates into a ``forIn`` over
``Lean.Loop.mk`` carrying gadget terms the kernel cannot unfold. A witness about
``NonDetT.run (distributePow …)`` therefore does NOT reduce against the frozen
solution for ANY claim, true or false, so the frozen-side exit code carries no
information and could not attribute a rejection to the spec.

This is stated as measurement, not inference. A deliberately NON-adversarial
claim — true of the frozen solution and of every rival alike (the empty aggregate
returns ``[]`` under both, so it asserts no rival is wrong) — ELABORATED against a
rival and FAILED against the frozen solution, leaving the unreduced loop term as
``unsolved goals``. That forgery would have cleared both halves of the gate's
discrimination check while refuting nothing. It fails with ``unsolved goals``
rather than the ``did not reduce to isTrue or isFalse`` text the gate's stuck-
reduction screen matches, so the screen does not catch this shape and the repair
had to be made in the manifest.

So every reject case names ``_LOOPFREE`` — a full variant implementing the frozen
spec correctly and loop-freely, which the gate checks shares the spec and
VERIFIES — as the subject its witness is refuted against. Re-measured against it,
the same forgery now ELABORATES (so it would be caught as ``witness-vacuous``)
while all seven real witnesses FAIL there, six leaving exactly ``⊢ False``. That
reversal is the evidence that discrimination is real rather than relabelled.
``_LOOPFREE`` is also shipped as the ``pos-echo-direct-fold`` positive, so the
battery records that loop-freeness is not what any rival is rejected for.

Every conditioning witness carries exactly ONE hypothesis about ONE ``powF``
application (or one pair of them), so its assumptions are jointly satisfiable —
the gate's ``consistency_probe`` was run on all six against ``_LOOPFREE`` during
authoring and left ``False`` unsolved in every case (exit 1), so none is a
contradiction-forgery. No ``sorry`` / ``admit`` / ``native_decide`` / new
``axiom``; no helper lemma is added and no obligation is weakened.

THE ROUTE LANE — WHY ITS REJECT CASES NAME NO ``witness_reference``. The carrier
fact above is about the ``while`` loop in ``distributePow``'s impl, and
``simplifyFactor``'s frozen impl has no loop: it is a single functional
``let out : List Factor := if …`` and its ``NonDetT.run`` post-image REDUCES
under ``simp [NonDetT.run, pure, powAll]``. So for the ROUTE rivals the frozen
solution can serve as the discriminating subject directly, and it does —
measured, all five: each ROUTE witness ELABORATES against its rival (exit 0) and
FAILS against the FROZEN solution (exit 1), four of them leaving exactly
``h : <hyp>`` and ``⊢ False`` and the structural one leaving ``⊢ False`` alone.
That is a STRONGER attestation than the PIN lane's, since it is refuted against
the shipped artifact rather than against a substitute, and it is the reason the
two lanes are recorded with different ``witness_subject`` values. The frozen
impl was WRITTEN in the functional form for exactly this reason: an earlier
``let mut out … if … then out := …`` spelling of the same behaviour left the
witness failing against frozen with ``Application type mismatch`` on an
unreduced ``NonDetT.run do NonDetT.pure PUnit.unit; …`` term — the
non-discriminating shape this file warns about — so the reducible spelling is a
deliberate, measured choice and not an accident of style.

Every case below was SEEN to behave as claimed with ``scripts/lean_verify.sh``:
each positive verifies (exit 0), each rival fails to verify (exit 1), and each
witness ELABORATES against its rival (exit 0) while FAILING against its
discriminating subject (exit 1) — the loop-free reference for the PIN lane, the
frozen solution for the ROUTE lane.

ADVERSARIAL READ of the nagini sibling's classes on THIS carrier:

  * SOUNDNESS positives — APPLY, and are the real work here (a tactic-proof
    backend needs a proof that actually closes). SIX are shipped. Three defend
    THE PIN: two loop-body reshapes that keep the frozen tactic script verbatim,
    and the direct-fold form, whose proof is retuned honestly (``loom_solve``
    alone closes it — the ``theorem`` statement and the ``prove_correct`` header
    are byte-identical). Three defend THE ROUTE: a mutable-accumulator reshape
    and an early-return reshape, BOTH of which keep the frozen ROUTE tactic
    script verbatim, and a ``List.map`` reshape whose proof prepends one
    honestly-proved pointwise induction ``have`` before the frozen script.
  * ADMISSIBILITY — RE-AIMED. The sibling's probe asserts that an F2P-shaped
    input satisfies its fractional-permission precondition. This method has NO
    ``require`` clause (the domain is total) and this backend has no permission
    surface, so that probe is degenerate: nothing could exclude any input. The
    residual admissibility risk on a total domain is that the post-image is
    DEGENERATE at the interesting point, so the case is re-aimed at exactly that.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling's
    MANDATORY ``frame-mutate-args`` rival writes the read-only input list, held
    at half permission, and is rejected for INSUFFICIENT PERMISSION rather than
    for a wrong value. Lean and Velvet are referentially transparent: ``factors``
    is an immutable ``List Factor`` declared read-only (not ``mut``), there is no
    heap, no aliasing and no fractional-permission system, so there is no
    read-only input to overwrite and no frame clause to violate. Not ported, and
    no substitute fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
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
  * AXIOM lane — dropped (G-AX's job, and this bundle declares no consumed
    axiom: ``powF`` carries no ``ensures``; see mapping.md §3).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13974"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Every one lies wholly inside the single `-- impl-start` /
# `-- impl-end` region (or is the `prove_correct` tactic body, likewise elided
# from the spec view) and is unique in Solution.lean — both facts asserted at
# load by `_swap`/`assert`, so a silent edit to the frozen file fails loudly here
# instead of quietly re-aiming a case at the wrong text.
# ---------------------------------------------------------------------------

# The whole gold impl body (the backward accumulate-and-prepend loop). Replaced
# wholesale by the loop-free reject rivals, whose `NonDetT.run` term reduces so
# their witnesses can condition on the opaque per-factor operation.
_IMPL_BODY = (
    "    let mut result : List Factor := []\n"
    "    let mut i := factors.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ factors.length\n"
    "      invariant result = powAll n (factors.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let b := factors[i - 1]!\n"
    "      result := powF b n :: result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

# The three loop-body lines. The two cheap positive controls reshape ONLY these,
# leaving the accumulated `result`/`i` definitionally identical so `loom_solve`
# leaves the same single loop-body goal and the frozen tactic script still closes.
_INNER = (
    "      let b := factors[i - 1]!\n"
    "      result := powF b n :: result\n"
    "      i := i - 1"
)
assert _BASE.count(_INNER) == 1, "inner-line anchor drift — re-sync _INNER"

# `distributePow`'s impl-start marker, anchored TOGETHER WITH its first gold body
# line so the anchor stays unique: `Solution.lean` declares two methods and
# therefore carries two `-- impl-start` markers, so the bare marker line is no
# longer a usable anchor and matching it alone would silently re-aim the
# admissibility insertion at whichever region came first. The admissibility case
# inserts a live in-region `assert` BETWEEN the marker and that line, so the whole
# gold body still follows below it.
_IMPL_START = (
    "    -- impl-start\n"
    "    let mut result : List Factor := []\n"
)
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"
# The count itself is asserted, so that if a third method is ever added (or one
# removed) this file fails at load rather than quietly under-covering.
assert _BASE.count("    -- impl-start\n") == 2, (
    "impl-start marker count drift — Solution.lean declares TWO methods")

# The frozen proof (tactic body only; the `prove_correct distributePow` header is
# preserved verbatim by every variant, as rule 2 requires). Only the direct-fold
# positive retunes it — the loop-body drop-step rewrite has no loop to apply to
# once the fold is written directly, so `loom_solve` alone is the honest script.
_PROOF = (
    "prove_correct distributePow by\n"
    "  loom_solve\n"
    "  rw [powAll_drop_step factors n i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"

# --- THE ROUTE anchors (`simplifyFactor`) ---
#
# The frozen ROUTE impl body. It is deliberately FUNCTIONAL (a single `let` bound
# to an `if`) rather than a mutable-accumulator form, because that is what makes
# its `NonDetT.run` post-image reduce and therefore makes the frozen solution
# usable as the discriminating subject for this lane's witnesses — see THE ROUTE
# LANE in the module docstring, where the measured failure of the `let mut`
# spelling is recorded. Replaced wholesale by every ROUTE variant below.
_SF_IMPL = (
    "    let out : List Factor :=\n"
    "      if isPowOfAggregate then powAll n factors else factors\n"
    "    return out"
)
assert _BASE.count(_SF_IMPL) == 1, "route impl anchor drift — re-sync _SF_IMPL"

# The frozen ROUTE proof (tactic body only; the `prove_correct simplifyFactor`
# header is preserved verbatim by every variant). `all_goals simp_all
# [factorImage]` closes all three ROUTE obligations for the gold impl and for
# both branch-shaped positives below.
#
# CORRECTED BY AUDIT. An earlier revision of this file claimed here (and in
# `route-pos-mutable-accumulator`'s rationale) that `all_goals` rather than a
# `<;>` chain is LOAD-BEARING — that with `loom_solve <;> simp_all [factorImage]`
# the two branch-shaped positives fail with the passthrough arm left open, so the
# frozen script would have rejected correct reshapes. That claim does not
# reproduce and is retracted. Re-measured with real builds, twice each and once
# more serially: `loom_solve <;> simp_all [factorImage]` VERIFIES (exit 0) on the
# frozen impl, on the mutable-accumulator reshape, on the early-return reshape,
# and on the `List.map` reshape (with its own `have` prepended). So the two
# spellings are interchangeable on all four impls measured here, and nothing in
# this battery rests on the choice. The shipped script keeps `all_goals` because
# it is what the frozen file carries and every variant must preserve the header
# and reproduce the obligation — not because a `<;>` chain was observed to fail.
# Recorded rather than quietly deleted: a false "this was measured" is the shape
# an auditor most needs to see retracted, since the next reader would otherwise
# inherit it as established fact.
_SF_PROOF = (
    "prove_correct simplifyFactor by\n"
    "  loom_solve\n"
    "  all_goals simp_all [factorImage]"
)
assert _BASE.count(_SF_PROOF) == 1, "route proof anchor drift — re-sync _SF_PROOF"


def _rival(body):
    """`_BASE` with the whole gold impl body replaced by a loop-free `body`.

    The spec regions, the method signature and the `prove_correct` header are
    untouched, so `same_spec` holds and the obligation survives. Its frozen
    tactic script no longer closes the reshaped impl — which is precisely why
    each of these carries a witness: the rejection is attributed to the spec by
    the witness, never to the broken tactic.
    """
    return _swap(_BASE, _IMPL_BODY, body)


def _sf_rival(body, proof=None):
    """`_BASE` with THE ROUTE's impl body replaced, `distributePow` untouched.

    Every ROUTE variant leaves `distributePow`'s impl, its `ensures` and its
    proof byte-identical, so a ROUTE case's verdict is attributable to THE ROUTE
    and to nothing else: whatever the gate reports, the PIN half of the file is
    the frozen half. The method signature, all three `ensures` clauses and the
    `prove_correct simplifyFactor` header are likewise untouched, so `same_spec`
    holds. `proof` is supplied only by the `List.map` positive, which needs one
    pointwise-induction `have` prepended to the frozen script — the frozen script
    itself still follows it verbatim.
    """
    src = _swap(_BASE, _SF_IMPL, body)
    return _swap(src, _SF_PROOF, proof) if proof else src


# ---------------------------------------------------------------------------
# Witness machinery.
# ---------------------------------------------------------------------------
# WHY EVERY REJECT CASE CARRIES A `witness_reference` (the load-bearing fact
# about this cell, established by measurement rather than assumed).
#
# The frozen impl keeps a `while` loop, and this bundle sets
# `loom.semantics.choice "demonic"`. The loop therefore elaborates into a `forIn`
# over `Lean.Loop.mk` carrying `invariantGadget` / `onDoneGadget` /
# `decreasingGadget` terms that the kernel cannot unfold. Consequence: a witness
# stated about `NonDetT.run (distributePow …)` does not REDUCE against the frozen
# solution — for ANY claim, true or false. The frozen-side build fails either way,
# so its exit code carries no information, and the two-build discrimination check
# would be satisfied by a witness that refutes nothing.
#
# Measured directly during authoring, which is the only reason this is stated as
# fact. A deliberately NON-adversarial claim — one that is TRUE of the frozen
# solution and of every rival alike (the empty aggregate returns `[]` under both,
# so it asserts no rival is wrong) —
#
#     example : NonDetT.run (distributePow [] 3) = DivM.res (powAll 3 []) := by
#       unfold distributePow; simp [NonDetT.run, pure, powAll]
#
# ELABORATED against a rival (exit 0) and FAILED against the frozen solution
# (exit 1), leaving `unsolved goals ⊢ (NonDetT.run do let r ← forIn Lean.Loop.mk
# …)` — the loop term, unreduced. That forgery would have cleared both halves of
# the check while attributing nothing to the spec. Note it fails with `unsolved
# goals`, NOT with the `did not reduce to isTrue or isFalse` text the gate's
# `_STUCK_REDUCTION` screen matches, so the screen does not catch this shape: on
# the `simp`-based route the non-reduction surfaces as a leftover goal instead of
# a stuck `Decidable` instance. Hence the repair has to be made HERE, in the
# manifest, rather than relied on from the gate.
#
# So every reject case names `_LOOPFREE` as its `witness_reference`: a full
# variant that implements the frozen spec CORRECTLY and loop-freely, so its
# post-image DOES reduce and refuting a witness against it is real evidence. The
# gate independently checks the reference shares the frozen spec and VERIFIES
# before using it. Re-measured against the reference, the same forgery above now
# ELABORATES (exit 0) — i.e. it would be caught as `witness-vacuous` — while all
# seven real witnesses FAIL there, six of them leaving exactly `⊢ False`. That
# reversal is what says discrimination has been restored rather than relabelled.
#
# `_LOOPFREE` is also shipped as the `pos-echo-direct-fold` positive, so the
# battery itself records that loop-freeness is not what any rival is rejected
# for: the same source that refutes the rivals verifies against the frozen spec.
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL_BODY, "    return powAll n factors"),
    _PROOF, "prove_correct distributePow by\n  loom_solve")


# `_cond(...)`: the CONDITIONING route. For a divergence that lands inside a
# `powF` application, no literal decides anything (the specification assumes no
# algebraic fact about the per-factor operation), so the refutation is stated at a
# point described by hypothesis: `h` separates the rival's output factor from the
# one the pin requires, and the conclusion is that the program's post-image
# differs from the spec's at that input. `simp [NonDetT.run, pure, powAll]`
# reduces the loop-free rival's term to its straight-line value and unfolds the
# fold on the spec side; the residual goal is exactly `h`'s content, so the
# closing step is a one-liner. Refuted against `_LOOPFREE`, where the same script
# leaves `⊢ False` — the claim genuinely does not hold of a correct impl.
def _cond(hyp, factors, n, close, extra_simp=""):
    return (f"example (h : {hyp}) :\n"
            f"    NonDetT.run (distributePow {factors} {n})"
            f" ≠ DivM.res (powAll {n} {factors}) := by\n"
            "  unfold distributePow\n"
            f"  simp [NonDetT.run, pure, powAll{extra_simp}]\n"
            "  intro heq\n"
            f"  {close}\n")


# `_uncond(...)`: the STRUCTURAL route, for a divergence in the output's SHAPE
# rather than in any factor's value. A wrong output LENGTH is a `List`
# constructor mismatch, which `simp` settles WITHOUT evaluating the opaque
# per-factor operation and therefore WITHOUT any hypothesis at all — so this
# witness binds nothing and carries no consistency-probe burden.
#
# This replaces a `derive_tester_for` / `decide` formulation that was tried
# first and DISCARDED: `distributePowTester` must compare the extracted
# program's output list against the postcondition's, and that comparison forces
# `Nat.decEq` on the opaque per-factor results, so `decide` got stuck
# (`did not reduce to isTrue or isFalse`) against the loop-free reference too,
# not just against the frozen solution. Stating the same structural divergence as
# a `≠` on the post-image keeps it inside `simp`'s reach.
def _uncond(factors, n):
    return (f"example :\n"
            f"    NonDetT.run (distributePow {factors} {n})"
            f" ≠ DivM.res (powAll {n} {factors}) := by\n"
            "  unfold distributePow\n"
            "  simp [NonDetT.run, pure, powAll]\n")


# `_sf_cond(...)` / `_sf_uncond(...)`: the same two routes, aimed at THE ROUTE.
# `flag` is the routing binder as written (`true` / `false`) and `rhs` is the
# post-image the spec's arm for THAT flag value requires, so the claim is always
# "at this flag value, at this aggregate, with this exponent, the rival's output
# is not the one the spec's arm for that flag demands". Because the frozen ROUTE
# impl is loop-free and reduces, these are refuted against the FROZEN SOLUTION —
# no `witness_reference` — which is the stronger of the two available
# attestations; see THE ROUTE LANE in the module docstring.
def _sf_cond(hyp, flag, factors, n, rhs, close):
    return (f"example (h : {hyp}) :\n"
            f"    NonDetT.run (simplifyFactor {flag} {factors} {n})"
            f" ≠ DivM.res {rhs} := by\n"
            "  unfold simplifyFactor\n"
            "  simp [NonDetT.run, pure, powAll]\n"
            "  intro heq\n"
            f"  {close}\n")


def _sf_uncond(flag, factors, n, rhs):
    return (f"example :\n"
            f"    NonDetT.run (simplifyFactor {flag} {factors} {n})"
            f" ≠ DivM.res {rhs} := by\n"
            "  unfold simplifyFactor\n"
            "  simp [NonDetT.run, pure, powAll]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # over-fit to the gold spelling => SPEC-TOO-STRONG. Each closes its
    # obligation honestly: the `prove_correct distributePow` header and the
    # method's `ensures` are byte-identical, nothing is assumed, and no helper
    # lemma is added.
    # =====================================================================
    {
        "id": "pos-control-local-raise",
        "kind": "soundness",
        "expect": "verify",
        # Bind the raised factor to a local `p` before prepending it, instead of
        # prepending the application inline. Same value flow; the accumulated
        # `result` is definitionally identical, so the frozen tactic body closes
        # the identical single loop-body goal.
        "module": _swap(
            _BASE, _INNER,
            "      let b := factors[i - 1]!\n"
            "      let p := powF b n\n"
            "      result := p :: result\n"
            "      i := i - 1"),
        "rationale": (
            "binding the per-position raised factor to a local `p` and "
            "prepending through that local computes the identical `result` on "
            "every iteration, so `out = powAll n factors` still holds on the "
            "whole domain; the loop, its invariants and the frozen tactic body "
            "are untouched. A correct reshape MUST verify, else the pin is "
            "over-fit to the exact gold spelling => SPEC-TOO-STRONG. (Ported "
            "from the sibling's pos-control-local-reshape, which binds the same "
            "handle to a local `p` on its carrier.)"),
    },
    {
        "id": "pos-control-inline-index",
        "kind": "soundness",
        "expect": "verify",
        # The mirror reshape: drop the intermediate `b` and index inline. Fewer
        # locals, same threaded values.
        "module": _swap(
            _BASE, _INNER,
            "      result := powF factors[i - 1]! n :: result\n"
            "      i := i - 1"),
        "rationale": (
            "inlining the positional read (dropping the intermediate `b`) leaves "
            "the prepended factor and the threaded counter definitionally "
            "unchanged, so the pin `out = powAll n factors` is unaffected and the "
            "frozen tactic body closes. Shipped alongside the local-binding "
            "reshape so the soundness surface is defended in BOTH directions — "
            "one reshape that adds a local and one that removes one — which is "
            "what rules out a pin sensitive to the number of intermediate "
            "bindings rather than to the value computed."),
    },
    {
        "id": "pos-echo-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl that satisfies the pin: apply the fold directly, no
        # loop. Its proof is RETUNED (not weakened): with no loop there is no
        # drop-step to rewrite, so `loom_solve` alone is the honest script. The
        # `prove_correct distributePow` header and the method's `ensures` are
        # byte-identical; nothing is assumed and no lemma is added.
        "module": _LOOPFREE,
        "rationale": (
            "This is the sibling's echo-attempt-honest control, re-argued for "
            "this carrier. The pin's right-hand side is a TRANSPARENT "
            "front-recursive fold over the ACTUAL input list, bottoming out in "
            "one per-factor application per position — not an opaque answer key. "
            "So returning it directly is not a cheat that skips the work: any "
            "value satisfying the pin has the per-factor operation applied to "
            "every input factor, with that position's own factor and that "
            "exponent. Shipping this as a VERIFY case (rather than as a "
            "spec-too-weak rival) is the claim that no WRONG echo exists here — "
            "the cheapest impl that satisfies the pin still does the real "
            "per-position work. The sibling reaches the same conclusion from the "
            "opposite premise (its fold has no executable materialization at "
            "all); here the fold IS materializable, so the grounding argument "
            "rests on its transparency instead. The proof is retuned to "
            "`loom_solve` because a loop-free impl leaves no loop-body goal for "
            "the drop-step rewrite to discharge — the obligation itself is "
            "unchanged."),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed from precondition admissibility (no `require`
    # clause exists on this method, and this backend has no permission surface,
    # so the sibling's probe is degenerate) to POST-IMAGE NON-DEGENERACY. A pin
    # no impl can distinguish reads exactly like one every impl meets, so this
    # case discharges a LIVE in-region assert, at an F2P-shaped input, that the
    # pin genuinely commits to something: the fold preserves the factor COUNT,
    # and it unfolds to the per-position applications rather than collapsing.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges, and the frozen tactic body discharges the assert too (no
    # retuning). The assert is live: a false claim at the same point leaves an
    # unsolved goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss (\n"
            "      (powAll 4 [10, 20]).length = 2 ∧\n"
            "      powAll 4 [10, 20] = [powF 10 4, powF 20 4]))\n"
            "    let mut result : List Factor := []\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at a two-factor "
            "aggregate with a non-identity exponent — the F2P-shaped input the "
            "sibling's admiss-f2p-shaped case probes. The assert pins that the "
            "fold (a) preserves the factor COUNT (length 2 in, length 2 out, so "
            "the length commitment is not vacuous) and (b) unfolds to exactly the "
            "two per-position applications, each carrying THAT position's own "
            "factor and the shared exponent — so the pin really does discriminate "
            "position from position, which is the property every reject rival "
            "below exploits. Re-aimed from the sibling's precondition probe: this "
            "method has no `require` clause and this backend has no "
            "fractional-permission surface, so 'a normal input satisfies the "
            "precondition' is unfalsifiable here; post-image non-degeneracy is "
            "the residual admissibility risk on a total domain. The assert is "
            "LIVE, and that is measured rather than asserted: the same insertion "
            "with the length claim falsified to `= 3` leaves `unsolved goals — "
            "case «admiss_1: ...»` with the false conjunction as the residual "
            "goal, so this case verifies because the claim is true of the fold "
            "and not because the surrounding tactic absorbs any assert."),
    },
    {
        "id": "admiss-obligation-at-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        # The second admissibility instrument, in the shape the lane's design
        # calls for on a total carrier: discharge the obligation AT the concrete
        # F2P-shaped input BY EVALUATION, as a `have`, and only then close the
        # frozen obligation verbatim. The impl region is untouched (this is the
        # gold impl), and the frozen tactic script follows the `have` unchanged,
        # so nothing is retuned and nothing is weakened.
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct distributePow by\n"
            "  have hf2p : powAll 4 [10, 20] = [powF 10 4, powF 20 4] := by\n"
            "    simp [powAll]\n"
            "  loom_solve\n"
            "  rw [powAll_drop_step factors n i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": (
            "PRECOND-TOO-STRONG has no direct analogue here (no `require` "
            "clause), so its analogue on a total carrier is the obligation being "
            "UNSATISFIABLE at exactly an F2P-shaped input. This case tests that "
            "directly and in the canonical shape: the pin's right-hand side is "
            "evaluated at the two-factor aggregate with a non-identity exponent — "
            "the TP(A,B)**n shape the failing test exercises — discharged by "
            "`simp [powAll]` as a `have`, BEFORE the frozen obligation is closed "
            "byte-for-byte verbatim. If the fold were degenerate or contradictory "
            "at that input, the `have` could not be discharged; if it were "
            "vacuous, the two per-position applications would not be what it "
            "reduces to. Complements admiss-nondegenerate, which makes the same "
            "commitment as an in-region `assert` instead: two independent "
            "instruments, one inside the impl and one inside the proof, so the "
            "lane does not rest on a single surgery point."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is LOOP-FREE (so its post-image reduces and its
    # witness can condition on the opaque per-factor operation), each carries a
    # machine-checked refutation witness at a concrete input, and each carries
    # the refinement argument for why its faithful real counterpart would NOT
    # resolve the failing test — so a verifying rival here would be a true
    # verify-does-not-imply-resolve break, not an artifact.
    # =====================================================================

    # ---- per-position: the exponent must actually reach every factor ----
    {
        "id": "weak-identity-fold",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: return the factor sequence unchanged, so the
        # shared exponent is never applied at any position. Correct only on the
        # empty aggregate.
        "module": _rival("    return factors"),
        "refinement": (
            "returning the factor sequence unchanged is EXACTLY the pre-image "
            "behaviour the issue reports: the shared exponent is left wrapping "
            "the aggregate as a whole and never distributed, so evaluating a "
            "power of an aggregate gives the aggregate back with the exponent "
            "still attached. Its faithful real counterpart is the UNPATCHED "
            "routine, which is what the failing test is red against in the first "
            "place — every one of that test's witnesses asserts the distributed "
            "form. Definitively non-resolving."),
        "rationale": (
            "REJECT from the pin `out = powAll n factors`: the impl returns "
            "`factors`, and the verifier cannot prove `factors = powAll n "
            "factors` because `powF` is opaque — no fixpoint of the per-factor "
            "operation is a theorem. Attacks the (per-pos) commitment at EVERY "
            "position. Refuted by CONDITIONING on `powF 5 3 ≠ 5` at the "
            "single-factor aggregate [5] with exponent 3 — the exact sub-domain "
            "where a raised factor differs from the raw one. (Ported from the "
            "sibling's identity-fold-prepatch, whose rejection likewise comes "
            "from the impossibility of a factor equalling its own power.)"),
        "witness": _cond("powF 5 3 ≠ 5", "[5]", "3", "exact h heq.symm"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-last-factor-unraised",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial domain: raise every factor EXCEPT the last, which is carried
        # through raw. Agrees with the pin at every position but the final one.
        # A strict NEAR-MISS of weak-identity-fold, so it gets its own witness at
        # its own distinguishing position rather than sharing one.
        "module": _rival(
            "    let raised := powAll n factors.dropLast\n"
            "    return raised ++ factors.drop (factors.length - 1)"),
        "refinement": (
            "a real counterpart that distributes the exponent to every factor of "
            "the aggregate except the last emits an aggregate whose final factor "
            "still carries no exponent. The failing test asserts the fully "
            "distributed aggregate — EVERY factor raised — so a result that is "
            "right in all but the last position is still unequal to the expected "
            "expression and the test stays red. Faithful but non-resolving."),
        "rationale": (
            "REJECT from the pin's (per-pos) commitment at the FINAL position "
            "only: `powAll` requires `powF factors[k] n` at every k, and this "
            "impl emits the raw factor at k = length-1. Correct at every earlier "
            "position (and on the empty aggregate), so it is a strictly narrower "
            "sub-domain than weak-identity-fold — which is why it carries its own "
            "witness rather than sharing that one: refuted by CONDITIONING on "
            "`powF 6 3 ≠ 6` at the TWO-factor aggregate [5, 6], where position 0 "
            "agrees with gold and only position 1 diverges. Sharing the "
            "identity rival's witness would claim a sub-domain this manifest "
            "never demonstrated. (Ported from the sibling's "
            "partial-domain-last-factor.)"),
        "witness": _cond("powF 6 3 ≠ 6", "[5, 6]", "3", "exact h heq.symm"),
        "witness_reference": _LOOPFREE,
    },

    # ---- per-position: the exponent binder must be the one supplied ----
    {
        "id": "weak-fixed-exponent",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the fold with a hardcoded exponent 2 instead of the supplied `n`.
        # Correct exactly on the sub-domain n = 2; wrong for every other
        # exponent. The ONLY rival attacking the `n` binder.
        "module": _rival("    return powAll 2 factors"),
        "refinement": (
            "a real counterpart that always squares each factor — ignoring the "
            "exponent actually carried by the input — emits the squared "
            "aggregate for every input power. The failing test raises an "
            "aggregate to a SYMBOLIC exponent and asserts each factor carries "
            "that same symbolic exponent; a hardcoded square produces a "
            "different expression entirely, so the test stays red. Faithful but "
            "non-resolving."),
        "rationale": (
            "REJECT from the pin's (per-pos) commitment in the EXPONENT argument: "
            "the pin requires `powF factors[k] n` and this impl emits `powF "
            "factors[k] 2`, which for a free `n` is not provably equal (`powF` is "
            "opaque — nothing constrains two applications differing in the second "
            "argument). This is the ONLY rival that attacks the `n` binder, and "
            "the only reason the battery can claim the pin depends on the "
            "exponent at all: a rival mishandling only `n` would otherwise "
            "verify unnoticed. Refuted by CONDITIONING on `powF 7 4 ≠ powF 7 2` "
            "at the aggregate [7] with exponent 4 — the sub-domain where the "
            "supplied exponent is not the hardcoded one. (Ported from the "
            "sibling's wrong-exponent-const.)"),
        "witness": _cond("powF 7 4 ≠ powF 7 2", "[7]", "4",
                         "exact h heq.symm"),
        "witness_reference": _LOOPFREE,
    },

    # ---- per-position: each position must read ITS OWN factor ----
    {
        "id": "weak-broadcast-first-factor",
        "kind": "uniqueness",
        "expect": "reject",
        # Raise the FIRST factor and broadcast that one result to every position.
        # Correct at position 0, on the empty aggregate, and on any single-factor
        # aggregate; wrong at any later position whose factor differs.
        "module": _rival(
            "    return factors.map (fun _ => powF (factors.headD 0) n)"),
        "refinement": (
            "a real counterpart that raises the aggregate's first factor and "
            "repeats that result across every position emits an aggregate all of "
            "whose factors come from the first one. The failing test raises an "
            "aggregate of DISTINCT factors and asserts each output factor is "
            "built from its own input factor; a broadcast collapses them and the "
            "test stays red. Faithful but non-resolving, and correct only at "
            "position 0 — a genuine partial-domain rival."),
        "rationale": (
            "REJECT from the pin's (per-pos) commitment in the FACTOR argument: "
            "for k >= 1 the impl emits `powF factors[0] n` where the pin requires "
            "`powF factors[k] n`; two applications of an opaque operation to "
            "distinct first arguments are not provably equal. Refuted by "
            "CONDITIONING on `powF 8 3 ≠ powF 9 3` at the TWO-factor aggregate "
            "[8, 9] — a distinct input point AND a distinct conditioning term "
            "from every other rival, so the positional dependence is "
            "demonstrated rather than assumed. (Ported from the sibling's "
            "wrong-factor-broadcast.)"),
        "witness": _cond("powF 8 3 ≠ powF 9 3", "[8, 9]", "3", "exact h heq",
                         extra_simp=", List.map, List.headD"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-swapped-arguments",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the per-factor operation with its two arguments transposed: raise
        # the exponent to the factor rather than the factor to the exponent.
        # Correct only where the operation happens to be symmetric at that point.
        # No sibling counterpart — see the accounting block.
        "module": _rival("    return factors.map (fun b => powF n b)"),
        "refinement": (
            "a real counterpart that transposes the two operands of the "
            "per-factor operation raises the exponent to the factor instead of "
            "the factor to the exponent. For an aggregate of non-commuting "
            "factors and a symbolic exponent this is a different expression at "
            "every position, so the failing test's expected distributed form is "
            "not produced and the test stays red. Faithful but non-resolving."),
        "rationale": (
            "REJECT from the pin's (per-pos) commitment in ARGUMENT ORDER: the "
            "pin requires `powF factors[k] n` and the impl emits `powF n "
            "factors[k]`. Because `powF` is opaque, nothing makes it symmetric, "
            "so the two are not provably equal. This rival exists because the "
            "carrier admits an attack the sibling's does not: the sibling's "
            "per-factor map is a Python `**` whose operands are positionally "
            "fixed by the surface syntax, whereas here both operands inhabit the "
            "SAME type (`Factor`), so a transposition type-checks and must be "
            "excluded explicitly. Refuted by CONDITIONING on "
            "`powF 4 6 ≠ powF 6 4` at the aggregate [6] with exponent 4 — the "
            "sub-domain where the operation is not symmetric at that pair."),
        "witness": _cond("powF 4 6 ≠ powF 6 4", "[6]", "4", "exact h heq",
                         extra_simp=", List.map"),
        "witness_reference": _LOOPFREE,
    },

    # ---- length: one output factor per input factor ----
    {
        "id": "weak-drops-last-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Raise every factor but DROP the last position entirely, so the result is
        # one factor short. Attacks the (length) commitment, not (per-pos) — the
        # surviving factors are all raised correctly. Correct only on the empty
        # aggregate.
        "module": _rival("    return powAll n factors.dropLast"),
        "refinement": (
            "a real counterpart that rebuilds the aggregate from one factor "
            "fewer than it received produces an aggregate of the wrong arity — a "
            "different expression from the expected one no matter how the "
            "surviving factors are raised, and for a two-factor aggregate it "
            "silently discards a factor entirely. The failing test compares "
            "against a same-arity distributed aggregate, so it stays red. "
            "Faithful but non-resolving."),
        "rationale": (
            "REJECT from the pin's (length) commitment: `powAll` is "
            "length-preserving, and this impl returns a list one element short "
            "for any non-empty input. The ONLY rival attacking length rather "
            "than a per-position value, and correspondingly the only one whose "
            "witness needs NO conditioning: the divergence is a `List` "
            "constructor mismatch (a one-element list against a two-element one), "
            "which `simp` settles WITHOUT evaluating the opaque per-factor "
            "operation, so the witness binds nothing and carries no "
            "consistency-probe burden. Refuted at the TWO-factor aggregate "
            "[7, 8] with exponent 1 — a two-factor input so the dropped position "
            "is a genuine discard rather than a collapse to the empty list, and "
            "the sole witness holding the exponent binder at 1, so `n` is probed "
            "at four distinct values across the reject set. A "
            "`derive_tester_for` / `decide` formulation was tried FIRST and "
            "discarded: the tester must compare the two output lists, which "
            "forces `Nat.decEq` on the opaque per-factor results, so `decide` got "
            "stuck against the loop-free reference too and the witness "
            "discriminated nothing."),
        "witness": _uncond("[7, 8]", "1"),
        "witness_reference": _LOOPFREE,
    },

    # ---- order: the k-th output factor comes from the k-th INPUT factor ----
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Raise every factor with the right exponent, but emit them in REVERSED
        # order. Right length, right multiset of per-factor applications, wrong
        # position for each. Correct on aggregates of fewer than two factors, and
        # on any palindromic one.
        "module": _rival("    return powAll n factors.reverse"),
        "refinement": (
            "a real counterpart that rebuilds the aggregate from its factors in "
            "reversed order produces a DIFFERENT aggregate: the factor sequence "
            "is ordered and its factors do not commute, so reversing them is not "
            "a no-op. The failing test asserts the distributed aggregate with its "
            "factors in the input order, so a reversed rebuild is unequal and the "
            "test stays red. Faithful but non-resolving."),
        "rationale": (
            "REJECT from the pin's (order) commitment — the one commitment no "
            "other rival attacks. Length is right and every emitted factor is "
            "`powF · n` for some input factor, so both the length clause and the "
            "per-factor SHAPE are satisfied; what fails is the tie between output "
            "position k and INPUT position k. Refuted by CONDITIONING on "
            "`powF 1 5 ≠ powF 3 5` at the THREE-factor aggregate [1, 2, 3] with "
            "exponent 5 — the only witness at length 3, chosen because reversal is "
            "invisible below length 2 and the middle position is a fixpoint of "
            "reversal, so the divergence has to be read off the endpoints. No "
            "sibling counterpart: the sibling's carrier pins order through a "
            "sequence-equality on a fold it never permutes, so a reversal rival "
            "was not among its cases; here the same commitment is separable and "
            "is attacked on its own."),
        "witness": _cond("powF 1 5 ≠ powF 3 5", "[1, 2, 3]", "5", "exact h"),
        "witness_reference": _LOOPFREE,
    },

    # =====================================================================
    # THE ROUTE — cases against the SECOND contracted method,
    # `simplifyFactor`, which pins the factor-position operation: for one
    # factor of a product, whether that factor is a power of the aggregate
    # whose positions are `factors` (raise arm: the per-position raise is owed)
    # or is the bare aggregate itself (passthrough arm: its positions are owed
    # back untouched).
    #
    # WHY THIS LANE EXISTS AT ALL, stated as the finding it answers. With THE
    # PIN as the only obligation, a rival could implement the per-position raise
    # perfectly and still reach it ONLY when the power is the whole expression —
    # never when the power sits at one factor position of a product. Such a
    # rival satisfies every clause of THE PIN, so this battery accepted it, and
    # its faithful real counterpart leaves the reported product-shape behaviour
    # unchanged. That is a verify-does-not-imply-resolve break located in the
    # SPEC, not in this battery's rivals, and the repair is THE ROUTE: an added
    # obligation, with its own defend and attack lanes here. Nothing in the PIN
    # lane above is weakened, deleted or re-aimed to accommodate it — all seven
    # PIN rivals and all three PIN positives are shipped unchanged, and
    # `distributePow`'s impl, `ensures` and proof are byte-identical in every
    # module below.
    #
    # Every ROUTE case edits ONLY `simplifyFactor`'s impl region (and, for one
    # positive, its tactic body), so `same_spec` holds and a ROUTE verdict is
    # attributable to THE ROUTE alone.
    # =====================================================================

    # ---- ROUTE positives (soundness): correct reshapes MUST verify ----
    {
        "id": "route-pos-mutable-accumulator",
        "kind": "soundness",
        "expect": "verify",
        # Seed a mutable accumulator with the passthrough value and overwrite it
        # in the raise arm, instead of binding one functional `if`. Same routing,
        # written as a statement rather than as an expression. The frozen ROUTE
        # tactic script is kept VERBATIM.
        "module": _sf_rival(
            "    let mut out : List Factor := factors\n"
            "    if isPowOfAggregate then\n"
            "      out := powAll n factors\n"
            "    return out"),
        "rationale": (
            "the accumulator form computes the identical output at both flag "
            "values — `factors` when the flag is false (never overwritten) and "
            "`powAll n factors` when it is true — so all three ROUTE clauses "
            "still hold on the whole domain, and the frozen tactic body closes "
            "them unchanged. A correct reshape MUST verify, else THE ROUTE is "
            "over-fit to the exact gold spelling => SPEC-TOO-STRONG. This is the "
            "counterpart of the sibling's routing-pos-control-local, which "
            "reshapes the same routing decision on its carrier. CORRECTED BY "
            "AUDIT: this rationale previously also claimed that the reshape FAILS "
            "under `loom_solve <;> simp_all [factorImage]` with the passthrough "
            "arm left open, and that the shipped `all_goals` spelling is "
            "load-bearing for that reason. Re-measured with real builds, the "
            "`<;>`-chain spelling VERIFIES (exit 0) on this reshape, on the "
            "early-return reshape and on the frozen impl alike, so the claim is "
            "retracted; see the note at _SF_PROOF. What this case actually "
            "attests is unchanged and is the point of it: a correct reshape of "
            "the routing verifies under the FROZEN script kept verbatim."),
    },
    {
        "id": "route-pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Return from inside the raise arm instead of joining both arms into one
        # bound value — two exits rather than one. Frozen ROUTE tactic verbatim.
        "module": _sf_rival(
            "    if isPowOfAggregate then\n"
            "      return powAll n factors\n"
            "    return factors"),
        "rationale": (
            "an early return out of the raise arm leaves the passthrough arm as "
            "the fallthrough. The routing decision, both arm values and the "
            "output type are unchanged, so `out = factorImage isPowOfAggregate n "
            "factors` and both arm clauses still hold; the frozen tactic body "
            "closes them verbatim. Shipped ALONGSIDE the accumulator reshape so "
            "the ROUTE soundness surface is defended in both directions — one "
            "reshape with a single exit and a mutable binding, one with two "
            "exits and no binding — which is what rules out an obligation "
            "sensitive to the control-flow SHAPE of the routing rather than to "
            "the value each arm produces."),
    },
    {
        "id": "route-pos-map-form",
        "kind": "soundness",
        "expect": "verify",
        # Spell the raise arm as a `List.map` of the per-factor operation rather
        # than as the `powAll` fold. Same value, different spelling, and the
        # equality between them is a THEOREM the positive must prove rather than
        # assume — so its proof prepends one honest pointwise induction and then
        # runs the frozen script verbatim.
        "module": _sf_rival(
            "    let out : List Factor :=\n"
            "      if isPowOfAggregate then factors.map (fun b => powF b n)"
            " else factors\n"
            "    return out",
            "prove_correct simplifyFactor by\n"
            "  have hmap : ∀ (m : Factor) (fs : List Factor),\n"
            "      fs.map (fun b => powF b m) = powAll m fs := by\n"
            "    intro m fs\n"
            "    induction fs with\n"
            "    | nil => simp [powAll]\n"
            "    | cons b bs ih => simp [powAll, ih]\n"
            "  loom_solve\n"
            "  all_goals simp_all [factorImage]"),
        "rationale": (
            "the raise arm written as a pointwise map is extensionally the "
            "`powAll` fold, so it satisfies all three ROUTE clauses — but the "
            "identity is not definitional (`powAll` is front-recursive, `map` is "
            "structural), so this positive is only admissible because the "
            "identity is PROVED: one `have` by induction on the factor list, "
            "assuming nothing about the opaque per-factor operation, followed by "
            "the frozen tactic body verbatim. It is the ROUTE analogue of the "
            "PIN lane's direct-fold positive: it establishes that THE ROUTE pins "
            "the per-position VALUE and not the recursion scheme used to reach "
            "it, which matters because a faithful real implementation is free to "
            "build the raised positions by any traversal."),
    },

    # ---- ROUTE rivals (uniqueness): wrong routing MUST be rejected ----
    # Refuted against the FROZEN SOLUTION (no `witness_reference`): this
    # method's frozen impl is loop-free and its post-image reduces, so the
    # discriminating subject is the shipped artifact itself.
    {
        "id": "route-weak-never-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image routing: hand the examined factor's positions straight
        # back whatever the flag says, so a power-of-aggregate factor is never
        # routed to the per-position raise. Correct exactly on the passthrough
        # arm.
        "module": _sf_rival("    return factors"),
        "refinement": (
            "this is EXACTLY the pre-image routing at a factor position: a "
            "factor of a product that is a power of an aggregate is handed back "
            "untouched, so the shared exponent stays wrapped around that factor "
            "and the per-position raise is never reached from a factor position. "
            "Its faithful real counterpart examines each factor of a product and "
            "passes a power-of-aggregate factor through unchanged — which is the "
            "state the failing test is red against: that test asserts the "
            "distributed form for a power of an aggregate appearing as one "
            "factor of a product as well as for one appearing alone. Measured, "
            "not asserted: a scope patch that implements THE PIN and leaves this "
            "routing at the pre-image behaviour was built and run against the "
            "real repository — FAIL_TO_PASS `test_tensor_product_simp` FAILS "
            "(PASS_TO_PASS all green), while the same patch plus the two routing "
            "edits RESOLVES (`resolved: true` from the official harness). "
            "Definitively non-resolving."),
        "rationale": (
            "REJECT from the raise arm `isPowOfAggregate = true → out = powAll n "
            "factors`: the impl returns `factors`, and the verifier cannot prove "
            "`factors = powAll n factors` because the per-factor operation is "
            "opaque — no fixpoint of it is a theorem. The passthrough arm and the "
            "output length are both satisfied, so the attribution is unambiguous. "
            "Refuted by CONDITIONING on `powF 5 3 ≠ 5` at flag=true, aggregate "
            "[5], exponent 3 — the sub-domain where a raised position differs "
            "from a raw one. This is the counterpart of the sibling's "
            "routing-dropped-prepatch."),
        "witness": _sf_cond("powF 5 3 ≠ 5", "true", "[5]", "3",
                            "(powAll 3 [5])", "exact h heq.symm"),
    },
    {
        "id": "route-weak-always-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror error: raise unconditionally, so a factor that is the BARE
        # aggregate has its positions raised too. Correct exactly on the raise
        # arm. This is the rival THE PIN alone could never have caught, since it
        # satisfies THE PIN's fold exactly.
        "module": _sf_rival("    return powAll n factors"),
        "refinement": (
            "a real counterpart that raises every examined factor's positions "
            "regardless of the routing flag applies the exponent to the "
            "positions of a factor that carries no exponent at all. That "
            "corrupts the already-correct product cases the PASS_TO_PASS tests "
            "cover — a bare aggregate factor comes back with a spurious exponent "
            "on every one of its positions — so it trades the failing test for "
            "passing ones and does not resolve. Faithful but non-resolving, and "
            "the reason THE ROUTE has to pin BOTH arms rather than only the one "
            "the failing test exercises."),
        "rationale": (
            "REJECT from the passthrough arm `isPowOfAggregate = false → out = "
            "factors`: the impl emits `powAll n factors` there, and `powAll n "
            "factors = factors` is not provable for an opaque per-factor "
            "operation. Note this rival satisfies THE PIN's obligation verbatim — "
            "it IS the fold — so it is invisible to every case in the PIN lane "
            "above; only the passthrough arm rejects it, which is the sharpest "
            "single demonstration that THE ROUTE is an independent obligation and "
            "not a restatement of THE PIN. Refuted by CONDITIONING on `powF 5 3 "
            "≠ 5` at flag=FALSE, aggregate [5], exponent 3 — the same carrier "
            "point as the never-raises rival but at the OPPOSITE flag value, "
            "which is what makes the pair jointly pin the routing rather than "
            "either arm alone."),
        "witness": _sf_cond("powF 5 3 ≠ 5", "false", "[5]", "3", "[5]",
                            "exact h heq"),
    },
    {
        "id": "route-weak-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Swap the two arms: raise the bare-aggregate factor and pass the
        # power-of-aggregate factor through. Both arms wrong at once, and correct
        # only where the two arm values coincide.
        "module": _sf_rival(
            "    let out : List Factor :=\n"
            "      if isPowOfAggregate then factors else powAll n factors\n"
            "    return out"),
        "refinement": (
            "a real counterpart that inverts the routing test raises the "
            "positions of a factor carrying no exponent and passes a "
            "power-of-aggregate factor through unchanged. It therefore breaks "
            "the already-correct cases AND leaves the reported one unfixed: the "
            "failing test stays red for the same reason the never-raises rival "
            "does, and the passing product cases go red as well. Faithful but "
            "non-resolving."),
        "rationale": (
            "REJECT from BOTH arms simultaneously — the only ROUTE rival that "
            "violates the two of them at once, so it is the case that shows the "
            "routing FLAG itself is load-bearing rather than either arm's value. "
            "The output length and the set of per-position values available at "
            "each flag are exactly gold's; what fails is the tie between the flag "
            "and the arm. Refuted by CONDITIONING on `powF 5 3 ≠ 5` at flag=true "
            "and the TWO-factor aggregate [5, 6] with exponent 3 — a distinct "
            "input point from either single-arm rival, and at length 2 so the "
            "claim is not readable off a single position. Counterpart of the "
            "sibling's routing-inverted."),
        "witness": _sf_cond("powF 5 3 ≠ 5", "true", "[5, 6]", "3",
                            "(powAll 3 [5, 6])", "exact fun _ => h heq.symm"),
    },
    {
        "id": "route-weak-fixed-exponent",
        "kind": "uniqueness",
        "expect": "reject",
        # Route correctly, but raise by a hardcoded 2 instead of by the exponent
        # the examined factor actually carries. Correct exactly on n = 2 and on
        # the passthrough arm; the ONLY ROUTE rival attacking the `n` binder.
        "module": _sf_rival(
            "    let out : List Factor :=\n"
            "      if isPowOfAggregate then powAll 2 factors else factors\n"
            "    return out"),
        "refinement": (
            "a real counterpart that squares each position of a "
            "power-of-aggregate factor — ignoring the exponent that factor "
            "actually carries — emits the wrong expression for every exponent "
            "but two. The failing test raises an aggregate to a SYMBOLIC "
            "exponent and asserts each position carries THAT exponent, so a "
            "hardcoded square keeps it red. Faithful but non-resolving."),
        "rationale": (
            "REJECT from the raise arm's EXPONENT argument: the arm requires "
            "`powAll n factors` and the impl emits `powAll 2 factors`, which for "
            "a free `n` is not provably equal (the per-factor operation is "
            "opaque, so nothing relates two applications differing in the second "
            "argument). This is the ONLY ROUTE rival that attacks `n`, and hence "
            "the only reason this lane can claim THE ROUTE depends on the "
            "exponent at all rather than merely on the flag: a rival mishandling "
            "only `n` would otherwise verify unnoticed. Refuted by CONDITIONING "
            "on `powF 7 4 ≠ powF 7 2` at flag=true, aggregate [7], exponent 4 — "
            "inside the sub-domain where the carried exponent is not the "
            "hardcoded one."),
        "witness": _sf_cond("powF 7 4 ≠ powF 7 2", "true", "[7]", "4",
                            "(powAll 4 [7])", "exact h heq.symm"),
    },
    {
        "id": "route-weak-drops-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Route correctly and raise correctly, but return one position short in
        # the raise arm. Attacks the raise arm's LENGTH commitment rather than
        # any position's value; the passthrough arm is untouched.
        "module": _sf_rival(
            "    let out : List Factor :=\n"
            "      if isPowOfAggregate then (powAll n factors).dropLast"
            " else factors\n"
            "    return out"),
        "refinement": (
            "a real counterpart that rebuilds a power-of-aggregate factor from "
            "one position fewer than it received emits an aggregate of the wrong "
            "arity at that factor position — silently discarding a position of "
            "the product's factor. The failing test compares against a "
            "same-arity distributed aggregate, so it stays red, and any product "
            "whose factor is a multi-position aggregate loses a position. "
            "Faithful but non-resolving. It is the ROUTE counterpart of the "
            "sibling's routing-passthrough-distorted: a rival that gets the "
            "routing DECISION right and the routed VALUE wrong."),
        "rationale": (
            "REJECT from the raise arm's length commitment: `powAll` is "
            "length-preserving and this impl returns a list one element short "
            "whenever the flag is set and the aggregate is non-empty. The ONLY "
            "ROUTE rival attacking length rather than a per-position value, and "
            "correspondingly the only one whose witness needs NO conditioning: "
            "the divergence is a `List` constructor mismatch (two elements "
            "against three), which `simp` settles WITHOUT evaluating the opaque "
            "per-factor operation, so this witness binds nothing and carries no "
            "consistency-probe burden. Refuted at flag=true, the THREE-factor "
            "aggregate [5, 6, 7] with exponent 2 — a third factor length and a "
            "fourth exponent value for this lane, and long enough that the "
            "dropped position is a genuine discard rather than a collapse."),
        "witness": _sf_uncond("true", "[5, 6, 7]", "2",
                              "(powAll 2 [5, 6, 7])"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING
# ===========================================================================
# The sibling battery ships 12 SPEC cases against TWO contracted functions
# (`power_of_collection`, the deep per-factor distribution; and
# `simp_pow_factor`, the per-factor ROUTING decision), plus a 2-probe AXIOM lane.
# This bundle now contracts BOTH: `distributePow` (THE PIN, the purely-functional
# distribution core) and `simplifyFactor` (THE ROUTE, the factor-position routing
# decision). The earlier revision of this file contracted only THE PIN and
# recorded the routing cases as NOT MODELED carrier narrowing. That disposition
# was WRONG, and it was wrong in the direction that matters: with the routing
# unmodeled, a rival implementing THE PIN perfectly and reaching the raise only
# for a whole-expression power satisfied the shipped spec, and its faithful real
# counterpart does NOT resolve the failing test (measured — see
# route-weak-never-raises' refinement note). The routing was not a behaviour this
# carrier lacks; it was a behaviour the modeled surface was missing. All four
# routing cases are therefore PORTED, and the sibling's own second contracted
# function is the shape they are ported from.
#
#   sibling case                      kind           -> here                         disposition
#   ----------------------------------------------------------------------------------------------
#   pos-control-local-reshape         soundness      -> pos-control-local-raise       PORTED
#   echo-attempt-honest               soundness      -> pos-echo-direct-fold          PORTED (re-argued)
#   admiss-f2p-shaped                 admissibility  -> admiss-nondegenerate          RE-AIMED
#   routing-pos-control-local         soundness      -> route-pos-mutable-accumulator PORTED
#   frame-mutate-args                 uniqueness     -> (none)                        VACUOUS
#   identity-fold-prepatch            uniqueness     -> weak-identity-fold            PORTED
#   partial-domain-last-factor        uniqueness     -> weak-last-factor-unraised     PORTED
#   wrong-exponent-const              uniqueness     -> weak-fixed-exponent           PORTED
#   wrong-factor-broadcast            uniqueness     -> weak-broadcast-first-factor   PORTED
#   routing-dropped-prepatch          uniqueness     -> route-weak-never-raises       PORTED
#   routing-inverted                  uniqueness     -> route-weak-inverted           PORTED
#   routing-passthrough-distorted     uniqueness     -> route-weak-drops-position     PORTED
#   AXIOM_TESTS (2 probes)            axiom          -> (none)                        N/A (G-AX)
#   (no counterpart)                  soundness      <- pos-control-inline-index      CARRIER-NEW
#   (no counterpart)                  soundness      <- route-pos-early-return        CARRIER-NEW
#   (no counterpart)                  soundness      <- route-pos-map-form            CARRIER-NEW
#   (no counterpart)                  uniqueness     <- weak-drops-last-position      CARRIER-NEW
#   (no counterpart)                  uniqueness     <- weak-swapped-arguments        CARRIER-NEW
#   (no counterpart)                  uniqueness     <- weak-reversed-order           CARRIER-NEW
#   (no counterpart)                  uniqueness     <- route-weak-always-raises      CARRIER-NEW
#   (no counterpart)                  uniqueness     <- route-weak-fixed-exponent     CARRIER-NEW
#
# 7 uniqueness ported + 5 carrier-new = 12 rivals; 3 soundness ported + 3
# carrier-new = 6 positives; 1 admissibility re-aimed + 1 carrier-new
# admissibility = 2. 1 uniqueness vacuous (frame); axiom lane dropped. 20 cases
# against 2 obligations carrying 4 `ensures` clauses in total.
#
# The two carrier-new ROUTE rivals are the ones the sibling has no counterpart
# for and that this carrier makes expressible: `route-weak-always-raises` (raise
# unconditionally — it satisfies THE PIN exactly, so ONLY the passthrough arm
# rejects it) and `route-weak-fixed-exponent` (route correctly, raise by a
# hardcoded exponent — the only ROUTE rival attacking the `n` binder).
#
# --- OMISSIONS, each with its reason ---
#
# RETRACTED OMISSION — the four routing cases (routing-pos-control-local,
#   routing-dropped-prepatch, routing-inverted, routing-passthrough-distorted).
#   This file previously recorded them as NOT MODELED, on the argument that
#   `Solution.lean` declared exactly one `method`/`prove_correct` pair and that
#   writing them "would mean inventing a second modeled behaviour, which the
#   porting map forbids". That argument is retracted. It was circular: the
#   absence of a routing obligation in the spec was offered as the reason not to
#   test routing, when the absence WAS the defect. The consequence was
#   measurable, not theoretical — an impl satisfying the single shipped `ensures`
#   need never reach the per-position raise from a factor position, so it
#   verified while its faithful real counterpart left the failing test red.
#   `Solution.lean` now declares TWO `method`/`prove_correct` pairs and all four
#   cases are shipped (see the table above). The porting map's prohibition is on
#   fabricating cases for behaviour the REPOSITORY does not have; the repository
#   has this behaviour at two routing sites, both of which the reference patch
#   edits, so modelling it is faithfulness rather than invention.
#
# VACUOUS (frame-mutate-args). The sibling's MANDATORY framing rival writes the
#   read-only input list to satisfy the pin in place, and is rejected by the
#   PERMISSION SYSTEM (a store needs full permission where only half is held) —
#   not by the postcondition. That rejection source does not exist here: Lean and
#   Velvet are referentially transparent, `factors` is an immutable `List Factor`
#   declared read-only (not `mut`), and there is no heap, no aliasing and no
#   fractional permission. There is no read-only input to overwrite and no frame
#   clause to violate, so the class has no carrier analogue and no substitute is
#   fabricated.
#
# DIVERGENCE / NON-TERMINATION — no sibling case to port (the sibling battery
#   has no divergence case at all), and NOT a spec hole here. This bundle sets
#   `loom.semantics.termination "total"`, and so does every other velvet bundle in
#   this corpus: the earlier "99 of 500 reject, 401 `partial` admit it" census is
#   RETRACTED, as is the internal findings note it cited, which has been withdrawn.
#   No bundle sets "partial", and the option cannot be inert, because the
#   `set_option` elaborator itself opens the matching scope
#   (Loom/MonadAlgebras/WP/Options.lean, `openScope`, where "total" opens
#   `TotalCorrectness`) and Velvet/Syntax.lean:386 opens the same scope by default.
#   Under total semantics a postcondition is claimed of ALL runs rather than only
#   terminating ones, so a diverging impl does NOT satisfy `ensures` vacuously:
#   `forWithInvariantLoop` takes `measure : β -> Nat` and emits a per-iteration goal
#   `measure b' < measure b`, where the `PartialCorrectness` twin takes
#   `measure : β -> Option Nat` and DISCARDS it. The `decreasing i` measure is
#   therefore a LIVE obligation here, re-measured by the audit in both of the two
#   shapes that can reach it:
#     * a loop carrying NO measure at all is refused outright, at the `method`
#       itself: `Decreasing annotations are required in total correctness
#       semantics` (exit 1) — and the file then does not compile at all, so no
#       appended tester can even be elaborated against it;
#     * a loop carrying a CONSTANT measure reaches the descent goal and fails ON
#       it: `unsolved goals — case «decreasing_1: spin»`, goal `⊢ 7 < 7` (exit 1).
#   AUDIT CORRECTION to an earlier revision of this block, which attributed the
#   descent failure to "an impl whose loop body never decrements the counter" and
#   quoted `case «decreasing_1: i»`, goal `⊢ i < i`. Re-measured: that particular
#   rival (`i := i` in the frozen loop) fails EARLIER and elsewhere — `Tactic
#   `rewrite` failed ... case «invariant_2: result = powAll n (factors.drop i)»` —
#   because the frozen invariant breaks before the measure goal is reached. The
#   substance is unchanged and is what the constant-measure build above shows
#   directly; only the rival the error was attributed to was wrong.
#
#   That the spec refutes such a rival is NOT by itself a reason to omit the
#   case — under `total` semantics a diverging rival is exactly the shape the
#   reject lane is for, so "the spec rejects it, hence nothing to port" would be
#   an UNDERPORT. The reason it is genuinely unshippable HERE is narrower and had
#   to be measured: on this backend an `expect="reject"` case must carry a
#   witness that ELABORATES against the rival, and a diverging rival is one that
#   KEEPS the `while` loop. Its `NonDetT.run` post-image is therefore exactly as
#   irreducible as the frozen solution's — the same unreduced `forIn
#   Lean.Loop.mk` / `invariantGadget` term described under THE DECISIVE CARRIER
#   FACT above. Measured on the non-decrementing rival: a conditioning witness
#   fails against it with `Application type mismatch` on the un-normalised loop
#   term (exit 1), and the structural `≠` form fails with `unsolved goals` (exit
#   1). Both halves of the discrimination check are therefore unreachable — the
#   witness cannot hold of the rival at all — so no admissible reject case for
#   this class can be constructed, whereas `_LOOPFREE` is available as a
#   `witness_reference` only for the loop-FREE rivals shipped above.
#
#   Disposition: VACUOUS CLASS on this carrier, for the witness-elaboration
#   reason just stated, not because the termination obligation is dead (it is
#   live) and not because the proof was hard. The spec-side verdict on a diverging
#   rival is REJECT, and only the witness half of the case is unavailable. Nothing
#   here is a spec hole: the earlier note that a `partial` setting "would have made
#   this a known SPEC HOLE instead" described a configuration this corpus does not
#   contain, and is retracted.
#
# AXIOM_TESTS — dropped. The axiom lane is G-AX's job and this gate ignores it;
#   independently, this bundle declares NO consumed axiom (mapping.md §3: `powF`
#   is an opaque I-leg primitive carrying no `ensures`, run for real on both sides
#   of G-CONF), so there is no contract for a soundness/containment probe to
#   check. meta.json records G-AX as `skip` for exactly this reason.
#
# No soundness positive was dropped: all six close their obligations with the
# frozen statement intact (four keep the frozen tactic body verbatim; the
# direct-fold one is retuned to `loom_solve`, which is the honest script for a
# loop-free impl and assumes nothing; the ROUTE map-form one PREPENDS a proved
# pointwise induction and then runs the frozen script verbatim).
#
# --- CLAUSE AND BINDER COVERAGE: THE PIN ---
#
# THE PIN is DEFENDED by three `expect="verify"` cases and ATTACKED by seven
# `expect="reject"` rivals. Its single `ensures` decomposes into three
# independent structural commitments, and EACH is attacked by a rival that leaves
# the other two intact — which is what makes the attribution readable:
#   (length)  weak-drops-last-position    (raises correctly, returns one short)
#   (order)   weak-reversed-order         (right length, right per-factor shape,
#                                          wrong position for each factor)
#   (per-pos) weak-identity-fold          (no position raised)
#             weak-last-factor-unraised   (all but the final position raised)
#             weak-fixed-exponent         (wrong EXPONENT argument)
#             weak-broadcast-first-factor (wrong FACTOR argument)
#             weak-swapped-arguments      (right operands, transposed)
#
# BOTH of THE PIN's input binders are varied by its reject witnesses — no binder
# is held at a single value across the set, so no rival mishandling only one input
# could slip through unnoticed. The seven witnesses sit at SEVEN DISTINCT input
# points:
#
#   weak-identity-fold            factors=[5]        n=3   (cond powF 5 3 ≠ 5)
#   weak-last-factor-unraised     factors=[5, 6]     n=3   (cond powF 6 3 ≠ 6)
#   weak-fixed-exponent           factors=[7]        n=4   (cond powF 7 4 ≠ powF 7 2)
#   weak-broadcast-first-factor   factors=[8, 9]     n=3   (cond powF 8 3 ≠ powF 9 3)
#   weak-swapped-arguments        factors=[6]        n=4   (cond powF 4 6 ≠ powF 6 4)
#   weak-drops-last-position      factors=[7, 8]     n=1   (structural, no binder)
#   weak-reversed-order           factors=[1, 2, 3]  n=5   (cond powF 1 5 ≠ powF 3 5)
#
# All seven are refuted against `_LOOPFREE` rather than against the frozen
# solution, for the measured reason in THE DECISIVE CARRIER FACT above: the frozen
# `while` loop does not reduce, so its side of the check would discriminate
# nothing. Six leave exactly `⊢ False` there; the structural one leaves the same.
#
#   * `factors` ranges over SIX distinct lists across THREE lengths — 1 ([5], [7],
#     [6]), 2 ([5, 6], [8, 9], [7, 8]) and 3 ([1, 2, 3]). Varying the length is what
#     separates the length rival from the per-position rivals, separates the
#     final-position rival from the every-position one, and is REQUIRED for the
#     order rival (reversal is invisible below length 2, and at length 2 the
#     endpoints are the only positions, so length 3 is what exhibits a fixed
#     middle with permuted ends).
#   * `n` ranges over FOUR distinct exponents — 1, 3, 4, 5. The value 1 appears
#     only in the length witness and 5 only in the order witness, so the exponent
#     binder is demonstrably not pinned to one probe value. weak-fixed-exponent is
#     the rival that attacks `n` directly, and it is refuted at n=4 against the
#     hardcoded 2, i.e. inside the sub-domain where the two differ.
#   * Every conditioning hypothesis is a SINGLE assumption about ONE `powF`
#     application or ONE pair of them — never two hypotheses about the same term,
#     the shape that signals a contradiction-forgery. All six were run through the
#     gate's `consistency_probe` against `_LOOPFREE` during authoring and none
#     yielded `False` (exit 1 in every case), so no rejection rests on a
#     non-existent input. The seventh (the length rival) binds nothing at all, so
#     it has no assumptions that could be inconsistent.
#   * No two rivals share a witness. weak-identity-fold and
#     weak-last-factor-unraised are the near-miss pair (the latter agrees with
#     gold at every position but the last), so the latter is refuted at the
#     two-factor point where position 0 matches gold and only position 1 diverges
#     — the sub-domain its rationale actually claims.
#
# --- CLAUSE AND BINDER COVERAGE: THE ROUTE ---
#
# THE ROUTE is DEFENDED by three `expect="verify"` cases and ATTACKED by five
# `expect="reject"` rivals. Its THREE `ensures` clauses are the joint statement
# (`out = factorImage isPowOfAggregate n factors`) and its two arms, and every
# clause is attacked by a rival that leaves the others intact:
#   (raise arm)        route-weak-never-raises     (passthrough arm untouched,
#                                                   raise arm never reached)
#                      route-weak-fixed-exponent   (raise arm reached with the
#                                                   WRONG exponent argument)
#                      route-weak-drops-position   (raise arm reached, correct
#                                                   per position, one position
#                                                   short — a LENGTH attack)
#   (passthrough arm)  route-weak-always-raises    (raise arm satisfied exactly;
#                                                   ONLY this arm rejects it)
#   (both arms /       route-weak-inverted         (each arm's value is gold's,
#    the flag itself)                               attached to the other flag)
#
# The `route-weak-always-raises` rival is the load-bearing one for this whole
# repair: it satisfies THE PIN's `ensures` verbatim (it IS `powAll n factors`),
# so the twelve PIN-lane cases cannot see it, and it is rejected only by the
# passthrough arm. A battery that pinned the raise arm alone would accept it.
#
# ALL THREE of THE ROUTE's input binders are varied across its reject witnesses,
# which sit at FIVE DISTINCT input points:
#
#   route-weak-never-raises      flag=true   factors=[5]        n=3
#                                            (cond powF 5 3 ≠ 5)
#   route-weak-always-raises     flag=FALSE  factors=[5]        n=3
#                                            (cond powF 5 3 ≠ 5)
#   route-weak-inverted          flag=true   factors=[5, 6]     n=3
#                                            (cond powF 5 3 ≠ 5)
#   route-weak-fixed-exponent    flag=true   factors=[7]        n=4
#                                            (cond powF 7 4 ≠ powF 7 2)
#   route-weak-drops-position    flag=true   factors=[5, 6, 7]  n=2
#                                            (structural, no binder)
#
#   * `isPowOfAggregate` takes BOTH of its values (true in four witnesses, false
#     in one), which is the minimum that can demonstrate the obligation depends
#     on the flag rather than on either arm's value alone. The true/false pair at
#     the SAME carrier point (`powF 5 3 ≠ 5`, factors=[5], n=3) is deliberate:
#     the two witnesses differ in the flag and in nothing else, so the pair
#     isolates the routing decision itself.
#   * `factors` ranges over THREE distinct lists across THREE lengths — 1 ([5],
#     [7]), 2 ([5, 6]) and 3 ([5, 6, 7]). Length 2 is what makes the inverted
#     rival's divergence unreadable from a single position, and length 3 is what
#     makes the dropped-position rival a genuine discard rather than a collapse.
#   * `n` takes THREE values — 2, 3 and 4. The value 4 appears only in the
#     fixed-exponent witness (against the hardcoded 2, i.e. inside the sub-domain
#     where they differ) and 2 only in the structural witness, so the exponent
#     binder is demonstrably not pinned to one probe value in this lane either.
#   * Each conditioning hypothesis is a SINGLE assumption about ONE `powF`
#     application or ONE pair of them. All four were run through the gate's
#     `consistency_probe` shape against the FROZEN solution during authoring and
#     each left `False` unsolved (exit 1), so no ROUTE rejection rests on a
#     non-existent input; the fifth binds nothing at all.
#   * No two ROUTE rivals share a witness, and no ROUTE witness is shared with
#     the PIN lane: the two lanes are stated over different methods, so a PIN
#     witness could not hold of a ROUTE rival at all.
#
# The ROUTE witnesses are refuted against the FROZEN SOLUTION, not against
# `_LOOPFREE` — THE ROUTE's frozen impl has no loop, so its post-image reduces
# and the shipped artifact is itself the discriminating subject. Measured on all
# five: ELABORATES against the rival (exit 0), FAILS against the frozen solution
# (exit 1), leaving `h : <hyp>` and `⊢ False` for the four conditioning ones and
# `⊢ False` for the structural one.
#
# --- INDEPENDENT AUDIT: WHY THE `introN` SIGNATURE IS NOT HOLLOW ---
#
# Six of the seven witnesses fail against `_LOOPFREE` with `Tactic `introN`
# failed`, which is not a plain evaluation, so the flip-the-claim experiment is
# owed on each. It was run on all seven, and the exit codes DO track the claim:
#
#   shipped witness (`≠`) vs `_LOOPFREE`  -> exit 1, leaving `h : <hyp>` and `⊢ False`
#   flipped claim  (`=`)  vs `_LOOPFREE`  -> exit 1, but `No goals to be solved`
#
# Different errors, so gold's exit code is not claim-independent. The reason the
# flipped form still exits 1 is diagnostic, not evasive: on the reference the
# `simp` PROVES the equation outright, which closes the goal and leaves the
# witness's trailing `intro heq` / `exact h …` steps with nothing to act on —
# hence `No goals`. Confirmed by truncating each witness to just its `simp` line
# and asserting the EQUATION (the type-revealing form):
#
#   `= DivM.res (powAll n factors)` by simp, vs `_LOOPFREE` -> exit 0  (simp PROVES it)
#   `= DivM.res (powAll n factors)` by simp, vs the RIVAL   -> exit 1  (`unsolved goals`)
#
# for all seven cases. That pair is the genuine refutation: the spec's equation
# holds of the reference at each witness's input and does NOT hold of the rival
# there, which is exactly what each rival is being rejected for. The `introN`
# text is thus a downstream artifact of a goal already closed semantically, not a
# tactic mismatch standing in for a refutation.
#
# The manifest's own load-bearing measurement was also re-run: the deliberately
# NON-adversarial claim about the empty aggregate ELABORATES against `_LOOPFREE`
# (exit 0 — so it WOULD be caught as `witness-vacuous`) and FAILS against the
# frozen solution (exit 1, `unsolved goals` on the unreduced `forIn Lean.Loop.mk`
# term). The carrier fact this battery's design rests on therefore reproduces.
#
# --- INDEPENDENT AUDIT: SPEC-TOO-WEAK PROBES (all REJECTED, no hole) ---
#
# Six wrong impls the battery does NOT contain, aimed at what the shipped rivals
# leave unattacked. Every one was rejected by the frozen spec:
#
#   length TOO LONG (an extra factor appended)        -> rejected
#   exponent SHIFTED (`n+1`, wrong at every n, so not
#     covered by the hardcoded-2 rival's n=2 hole)    -> rejected
#   only the FIRST TWO positions transposed (a strictly
#     smaller permutation than the full reversal)     -> rejected
#   drops the FIRST position (battery drops the LAST) -> rejected
#   wrong ONLY at the exponent n = 0, a value no
#     shipped witness probes                          -> rejected
#   off-by-one index, so each position reads its
#     neighbour and position 0 reads the Nat default  -> rejected
#
# --- INDEPENDENT AUDIT: SPEC-TOO-STRONG PROBES (correct reshapes VERIFY) ---
#
# Three further faithful correct impls, none in the battery, all VERIFY against
# the frozen spec — so the pin is not over-fit beyond the three shipped
# positives: a `List.map` reshape (proof `loom_solve` + a pointwise induction);
# a `factors.take factors.length` wrapping (`loom_solve` alone); and a
# reverse-twice reshape closed via the map characterisation. A forward-indexing
# loop (the mirror of the frozen backward loop) is correct and its residual goal
# reduces to a standard `List.take_succ`-on-a-mapped-list identity, but no proof
# was closed for it within the audit's build budget — recorded as UNCERTAIN, not
# as a soundness hole, since failing to find a script is not evidence the spec
# rejects the impl.
#
# --- INDEPENDENT AUDIT: THE ROUTE, both directions, all measured ---
#
# SPEC-TOO-WEAK probes (wrong routings the battery does NOT contain). Each was
# built and run against the frozen spec; each was REJECTED, and the residual goal
# names the clause it violates, so none of these is a hole the shipped five miss:
#
#   raise arm reverses the positions
#     (`(powAll n factors).reverse` in the true arm)   -> rejected, exit 1,
#     `⊢ isPowOfAggregate = true → (powAll n factors).reverse = powAll n factors`
#   passthrough arm drops a position
#     (`factors.dropLast` in the false arm)            -> rejected, exit 1,
#     `⊢ isPowOfAggregate = false → factors.dropLast = factors`
#   the routing FLAG ignored entirely, routing instead on whether the aggregate
#     is empty (`if factors.isEmpty then factors else powAll n factors`)
#                                                      -> rejected, exit 1, on
#     BOTH the passthrough arm and the joint clause — the case that shows the
#     obligation cannot be satisfied by any routing criterion other than the flag
#
# SPEC-TOO-STRONG probes (correct reshapes NOT in the battery). A `match
# isPowOfAggregate with | true => … | false => …` reshape of the frozen routing
# VERIFIES (exit 0, proof `loom_solve <;> cases isPowOfAggregate <;> simp_all
# [factorImage]` — retuned, nothing assumed), so THE ROUTE is not over-fit to the
# `if`-expression spelling beyond the three shipped positives.
#
# ASSERT LIVENESS at THE ROUTE's insertion point, so that a future admissibility
# case placed there cannot be absorbed by the surrounding tactic. With the frozen
# impl and the frozen tactic script kept verbatim and one in-region `assert`
# inserted immediately after `-- impl-start`:
#
#   assert ((powAll 4 [10, 20]).length = 2)   (TRUE)  -> exit 0
#   assert ((powAll 4 [10, 20]).length = 3)   (FALSE) -> exit 1, failing ON the
#     frozen tactic line with `simp_all made no progress`
#
# So the insertion point is live in both directions: the frozen script does not
# discharge a false claim there.
#
# ===========================================================================
# SECOND INDEPENDENT AUDIT (a different auditor, re-running rather than reading)
# ===========================================================================
# Everything above this line was re-derived from real builds rather than trusted.
# ~70 builds, all scratch under /tmp. Two prose defects were found and both are
# corrected IN PLACE above (at `_SF_PROOF`, in `route-pos-mutable-accumulator`'s
# rationale, and in the DIVERGENCE block) rather than only noted here, so a reader
# of the claim meets the retraction at the claim.
#
# ALL 20 MODULES REBUILT STANDALONE: 8 positives exit 0, 12 rivals exit 1, i.e.
# every case behaves as declared under an independent build. Each rival's residual
# goal was read and in every case it NAMES the clause the rationale claims:
# e.g. `⊢ factors = powAll n factors` (identity), `⊢ powAll 2 factors = powAll n
# factors` (fixed exponent), `⊢ powAll n factors.reverse = powAll n factors`
# (order), `⊢ powAll n factors.dropLast = powAll n factors` (length), and on the
# ROUTE side `case «ensures_1: isPowOfAggregate = false → out = factors»` for
# always-raises — the arm that rival's rationale says is the only one that sees
# it. So the attributions are not merely asserted.
#
# ALL 12 REJECT CASES: witness rebuilt on BOTH sides, plus the consistency probe,
# plus the two attack-B′ experiments. Every case: rival exit 0, declared subject
# exit 1, probe exit 1 (`h : <hyp>` / `⊢ False`, so no contradiction-forgery).
# The forgery pair is what settles the `introN` signature class, and it does track
# the claim in every case:
#
#   FLIP (assert `=` instead of `≠`, same subject): exit 1 with `No goals to be
#     solved` for the 10 conditioning witnesses — a DIFFERENT error from the
#     witness's own `introN failed`, so the subject's exit code is not
#     claim-independent. For the 2 STRUCTURAL witnesses the flip exits 0, which is
#     the strongest possible result: the forged claim would have been caught as
#     `witness-vacuous` rather than recorded as a rejection.
#   REVEAL (truncate to the `simp` line and assert the EQUATION): exit 0 against
#     the declared subject and exit 1 against the rival, for all 12. The residual
#     goal on the rival side is the concrete refuted equation — `⊢ 5 = powF 5 3`,
#     `⊢ powF 7 2 = powF 7 4`, `⊢ powF 8 3 = powF 9 3`, `⊢ 5 = powF 5 3 ∧ 6 =
#     powF 6 3` — never `True`. That is a genuine semantic refutation: `simp`
#     proves the spec's equation for the correct impl at that input and cannot for
#     the rival, which is exactly what the rival is rejected for.
#
# THE CARRIER FACT REPRODUCES, and it is the load-bearing claim of the PIN lane.
# The non-adversarial empty-aggregate claim ELABORATES against `_LOOPFREE`
# (exit 0) and FAILS against the frozen solution (exit 1) leaving the unreduced
# `forIn Lean.Loop.mk (MProdWithNames.mk' 0 [] …) … invariantGadget …` term
# verbatim. Independently: each PIN witness was ALSO built against the frozen
# solution directly, and every one fails there for a SYNTACTIC reason on that same
# unreduced term (`Application type mismatch: … Eq.symm heq has type DivM.res … =
# NonDetT.run do let r ← forIn Lean.Loop.mk …`, or `Type mismatch`) — which is why
# the `witness_reference` substitution is the correct repair and not a relabelling.
#
# THE ROUTE LANE's stronger attestation also reproduces, including the claim that
# the FUNCTIONAL frozen spelling is what makes it possible. All 5 ROUTE witnesses
# fail against the FROZEN solution with `h : <hyp>` / `⊢ False` (semantic), and
# re-measuring the manifest's own justification: the same witness against a
# `let mut out … if … then out := …` spelling of the SAME CORRECT behaviour fails
# with `Application type mismatch … NonDetT.run do NonDetT.pure PUnit.unit; …` —
# the non-discriminating shape. So the frozen impl's functional form really is
# load-bearing for this lane, as documented.
#
# ATTACK C (is each rival observably wrong, or just reshaped?) — every one of the
# 12 is observably wrong on this carrier, and none is definitionally equal to
# gold. `powF` is `opaque`, so no rival's divergence can be closed by any
# algebraic fact: no factor is a fixpoint of it (identity, never-raises), it is
# not symmetric (swapped arguments), and two applications differing in either
# argument are unrelated (fixed exponent, broadcast, reversal, inverted). The two
# length rivals differ from gold by a `List` constructor, which is not a carrier
# collapse either. No vacuous case, so nothing was dropped.
#
# ATTACK D, this audit's OWN new wrong impls (13, none in the battery). ALL
# REJECTED, so no spec hole: map (+1) over the fold's output; fold over
# `factors ++ factors`; `if n = 0 then factors else …` (PIN and ROUTE forms — the
# n=0 sub-domain no witness probes); `if factors.length ≤ 1 then … else factors`;
# raise only the head and pass the tail; `List.range`-indexed off-by-one reading
# the `getElem!` Nat default; ROUTE passthrough arm returning `powAll 1 factors`;
# ROUTE gated on `isPowOfAggregate && factors.length > 1`; ROUTE reversing both
# arms; ROUTE raising with transposed operands; ROUTE gated on `n = 0`. Each
# residual goal names the violated clause.
#
# ATTACK E, this audit's OWN new correct reshapes (5). ALL VERIFY (exit 0), so no
# soundness hole: PIN via `List.map` and via `List.foldr` (each with its pointwise
# induction proved as a `have`); ROUTE via a negated `if`, via `match
# isPowOfAggregate with`, and via `if isPowOfAggregate && !factors.isEmpty` (a
# guard that is extensionally the frozen routing, since the empty aggregate raises
# to itself). The forward-indexing loop the previous audit recorded UNCERTAIN was
# retried once more and still did not close (`simp` hit `maximum recursion depth`);
# that disposition stands, and an unclosed script is not evidence of over-strength.
#
# THE FRAME LANE's VACUOUS disposition is now DEMONSTRATED rather than argued.
# Assigning to the read-only input (`factors := []`) is refused by the backend
# itself, ahead of any obligation: `\`factors\` cannot be mutated, only variables
# declared using \`let mut\` can be mutated`. There is no permission to be
# insufficient and no frame clause to violate, so the sibling's rejection SOURCE
# genuinely does not exist here.
#
# ADMISSIBILITY LIVENESS re-measured independently, in both instruments and in a
# direction the previous audit did not try: falsifying the ORDER conjunct rather
# than the length. The in-impl assert with `[powF 20 4, powF 10 4]` fails, exit 1,
# `unsolved goals case «admiss_1: …»`; the in-proof `have` with the same falsified
# order fails, exit 1, `⊢ powF 10 4 = powF 20 4 ∧ powF 20 4 = powF 10 4`. So both
# admissibility instruments are live against a POSITIONAL falsification, which is
# the commitment they claim to pin, not only against an arity one.
AXIOM_TESTS = []
