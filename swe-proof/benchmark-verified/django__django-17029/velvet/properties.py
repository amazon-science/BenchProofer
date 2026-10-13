"""properties.py — G-PBT falsification battery for django__django-17029 (velvet).

NOT a Velvet module; a record of adversarially-reasoned cases the G-PBT gate
executes and stamps a verdict onto. Each SPEC case is a FULL ``Solution.lean``
variant that shares the FROZEN spec byte-for-byte — region surgery touches only
text strictly inside ``-- impl-start`` / ``-- impl-end`` (and, where noted, the
``prove_correct`` tactic body), both of which the consumer spec view elides — so
``markers.same_spec`` holds by construction and the ``prove_correct
clearAllCaches`` obligation survives with a byte-identical header. Every case is
judged by the real verifier: ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` DISCRIMINATES — elaborates against the rival, fails
against the frozen solution).

DEFENDED SURFACE. One contracted method over two mutable occupancy counters:

  clearAllCaches (mut modelsOccupancy : Nat) (mut swappableOccupancy : Nat)
      return (unit : Unit)
    ensures modelsOccupancy = 0
    ensures swappableOccupancy = 0

The registry's single cache-reset operation must discard the retained results of
EVERY memoizing lookup method, so afterwards each method's cache occupancy is
zero regardless of how full it was beforehand. Only the touched state is modeled:
one non-negative occupancy counter per memoizing method (the all-models lookup
and the swappable-settings-name lookup), both genuinely mutated (``mut``).

There is NO ``require`` clause, so the admitted domain is TOTAL: any pair of
non-negative starting occupancies is in-domain, including the all-zero corner.

TWO independent top-level clauses, both LOAD-BEARING and both pinned to the exact
literal 0 — there is no slack anywhere in the post-image:
  (Q1) ``modelsOccupancy = 0``    — the all-models lookup's retained results must
       be gone. A body that leaves this counter at its incoming value, or at any
       other non-zero value, fails here.
  (Q2) ``swappableOccupancy = 0`` — the DISCRIMINATING clause. The behaviour the
       issue reports is precisely a reset that empties one memoizing method's
       cache while leaving another method's retained results in place; a later
       observer then still sees stale memoized values for that method. A body
       that leaves this counter at its incoming value, decrements it, re-primes
       it, or pins it to a copy of the OTHER counter's pre-value fails here.

BINDER STRUCTURE (read before judging binder coverage). Each clause names exactly
one binder's post-state, but a rival is free to COUPLE them — to make the
swappable clause's outcome depend on the models binder, or to source one
counter's post-value from the other counter's PRE-value. Two of the rivals below
exist specifically to exercise that coupling in the swappable direction
(``weak-coupled-guard``, ``weak-proxy-prevalue``), and a third
(``weak-mirror-coupled-guard``) exercises it in the MODELS direction, because a
battery whose witnesses all held one binder fixed — or which only ever attacked
one clause unconditionally — would verify such a rival and never notice. The
nine reject witnesses probe nine DISTINCT input points and vary BOTH binders
across {0, 1, 2, 3, 4, 5, 6, 7}, including the all-zero boundary and BOTH
one-is-zero-the-other-is-not corners. Neither binder is pinned.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS here, and the nagini sibling reaches
    the same conclusion from the other direction. There it reasons over two FULL
    heap permissions on the occupancy fields and asks whether a read-only
    half-permission input could be overwritten to satisfy the post-image
    vacuously; it records that there is no such read-only input, since both
    fields are genuinely written by the operation. On this carrier the question
    cannot even be posed: Lean and Velvet are referentially transparent, the two
    counters are ``mut`` VALUE binders with no heap footprint, no aliasing and no
    fractional-permission system. The unchanged-frame obligation is discharged
    instead by pinning both post-states to the exact literal 0. Not fabricated
    (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — N/A on both backends, for the same reason. The
    ``pure`` region is empty: there is no opaque callee, no answer-key helper and
    no oracle in the contract. Both clauses are pinned to the concrete literal 0,
    grounded directly in the required post-state and independent of any input
    value, so there is no value an "echo" could carry that satisfies the
    post-image yet is wrong — the unique satisfier IS ``counter = 0``. The
    honest cheapest faithful body is therefore "assign 0", which is what the
    positive controls below are. Consequently every witness here is fully
    TRANSPARENT: the carrier is ``Nat``, so no witness needs to condition on an
    opaque term and none binds any hypothesis. (There is therefore no
    joint-satisfiability risk for the gate's consistency probe to find.)

  * DIVERGENCE / NON-TERMINATION — the frozen obligation REJECTS every diverging
    rival that can be built here, so the class is not a spec hole on this cell;
    it is unshippable for a WITNESS reason, which is a different disposition and
    is recorded as such. The previous text on this class was WRONG in its premise
    and is corrected here: it stated that this bundle sets
    ``loom.semantics.termination "partial"`` and that a spliced non-terminating
    prefix "elaborates and verifies (exit 0)". The frozen ``Solution.lean``
    actually sets ``termination "total"``, and re-measured in the audit lane with
    real builds, every diverging rival is REJECTED:

      - measure-less prefix (``while True do pure ()`` ahead of the frozen
        assignments) -> exit 1, ``Decreasing annotations are required in total
        correctness semantics``;
      - a diverging loop CARRYING a measure and a WRONG post-state
        (``modelsOccupancy := 7`` / ``swappableOccupancy := 9`` after
        ``while k > 0 ... decreasing (0 : Nat)``) -> exit 1 on the SPEC's own
        goals, ``ensures_1 ... ⊢ 9 = 0`` and ``ensures_2 ... ⊢ 7 = 0``, both with
        ``done_1`` in context. The same shape with ``done_with`` omitted, with
        ``done_with False``, and with a strictly INCREASING measure were each also
        rejected (exit 1), the latter two on ``done_1: False ⊢ False``.
      - and the measure itself is not taken on trust either. The same loop with a
        CORRECT continuation, so that nothing but the measure can be at fault, is
        STILL rejected at exit 1 on the measure's own descent goal:
        ``unsolved goals case «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``. So a
        constant measure does not launder a diverging rival through an
        unreachable exit on this cell: the strict-decrease side condition is a
        real goal here.

    THE MECHANISM, so none of this rests on one build.
    ``set_option loom.semantics.termination "total"`` itself opens the
    ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``, the
    ``openScope `TotalCorrectness`` arm), line 7 of the frozen file opens it again
    explicitly, and ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the
    ``measure`` and emits ``⌜measure b' < measure b⌝`` as a goal the proof must
    discharge. Only the ``PartialCorrectness`` twin takes a measure and drops it,
    which is why the two header lines have to move together and do here.

    What a diverging rival cannot carry here is a WITNESS. A rival whose loop
    fails to elaborate never defines the extracted program, so the witness build
    against the RIVAL, the half that must SUCCEED, fails at exit 1 with
    ``Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse```
    (gate screen ``reduction``), not by refutation. That is the whole reason the
    class does not ship: NOT that some diverging shape verifies. A previous
    revision of this paragraph claimed the ``decreasing (0 : Nat)`` loop spliced
    AHEAD of the frozen clears "does elaborate and verify", and read it as
    observationally correct; the build above RETRACTS that: it is rejected on
    ``⊢ 0 < 0``. Recorded as a witness-side carrier limit, and no spec hole is
    escalated from this class.

  * SELF-ECHO — the sibling's ``weak-self-echo`` (discharge the contract by
    calling the function under spec) is INEXPRESSIBLE here, and was dropped only
    after being built and run. On this carrier the rival is rejected by Lean's
    own totality checker before any spec reasoning happens ("fail to show
    termination for clearAllCaches ... no parameters suitable for structural
    recursion"), and the same error breaks the WITNESS build, whose success is
    the half that must hold. So no discriminating witness exists: the rejection
    is attributable to definability, not to the postcondition. Reported rather
    than shipped — see the footer.

  * AXIOM lane — DROPPED. The ``axioms`` region declares no ``axiom`` (the
    cache-reset is modeled deeply as two state writes; the standard-library
    memoization wrapper whose emptied-cache effect they refine is an A-reference
    validated out-of-band). The gate ignores ``AXIOM_TESTS`` regardless.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``clearAllCachesTester m s = false`` says the extracted program's observable (the
two mutated counters) violates the method's postcondition at that concrete pair
of starting occupancies. Checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict — which matters here, because
every rival RESHAPES the impl and the frozen ``loom_solve`` script would fail on
a merely-reshaped-but-correct body too. Both carriers are ``Nat`` with decidable
equality, so every witness closes by ``decide`` at literal inputs; none uses
``sorry`` / ``admit`` / ``native_decide`` and none introduces a declaration.
Every reject witness below was run against BOTH the rival (exit 0, elaborates)
and the frozen solution (exit 1, ``decide`` proves the tester TRUE there) with
two real builds each, and was SEEN to discriminate. Re-derived independently in a
SECOND audit pass: all nine rival builds exit 0 and all nine gold builds exit 1
with a SEMANTIC refutation (``Tactic `decide` proved that the proposition
clearAllCachesTester <m> <s> = false is false``), never a missing identifier, a
type error or a stuck reduction. Gold's exit code was additionally shown to
depend on the CLAIM and not merely on the file: the flipped claim
``clearAllCachesTester m s = true`` builds against the frozen solution at exit 0
for (4,3), (0,0), (5,0) and (0,4), so `decide` is genuinely evaluating the tester
on both sides. No witness binds anything, so ``consistency_probe`` is ``None``
and the gate's third build does not apply.
"""
from pathlib import Path

INSTANCE = "django__django-17029"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies WHOLLY inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both facts asserted
# ---- at load), so every variant's edit is confined to the impl region and
# ---- same_spec holds by construction.
_GOLD_IMPL = (
    "    swappableOccupancy := 0\n"
    "    modelsOccupancy := 0\n"
    "    return ()"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case may retune the tactic script without
# ---- touching the obligation's statement or dropping the obligation itself.
# ---- Unique in the file. (Only the admissibility case uses this, and only to
# ---- add a tactic; the header is never touched.)
_GOLD_PROOF = "prove_correct clearAllCaches by\n  loom_solve"

assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl-region body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method CONTRACT through Velvet's tester
# ---- machinery, in a file whose `prove_correct` block the gate strips.
# ---- `clearAllCachesTester m s = false` says the extracted program's observable
# ---- (the two mutated counters after the reset) violates the postcondition at
# ---- that concrete pair of starting occupancies. The tester names come from
# ---- directives inside the witness itself, so they exist in BOTH builds.
def _tester(body):
    return ("extract_program_for clearAllCaches\n"
            "prove_precondition_decidable_for clearAllCaches\n"
            "prove_postcondition_decidable_for clearAllCaches\n"
            "derive_tester_for clearAllCaches\n\n" + body)


def _witness(models, swappable):
    """Refutation at a literal starting-occupancy pair. Binds nothing."""
    return _tester(
        f"example : clearAllCachesTester {models} {swappable} = false := by\n"
        f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT bodies
    # that MUST verify, else the post-image is SPEC-TOO-STRONG (over-fit to the
    # frozen body's syntactic shape). Each keeps the byte-identical two-clause
    # obligation and the frozen `loom_solve` script; all three were confirmed to
    # verify with real builds.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Write the two counters in the OPPOSITE textual order. They are
        # independent value binders, so the final state is identical.
        "module": _impl(
            "    modelsOccupancy := 0\n"
            "    swappableOccupancy := 0\n"
            "    return ()"),
        "rationale": (
            "structurally-different but CORRECT: the two INDEPENDENT counter "
            "assignments are written in the opposite textual order (all-models "
            "first, then swappable-settings-name). No loop, no new lemma, no "
            "coupling — the post-state of both counters is 0 on every input, so "
            "Q1 (`modelsOccupancy = 0`) and Q2 (`swappableOccupancy = 0`) both "
            "still discharge under the frozen script. If it FAILS => "
            "SPEC-TOO-STRONG: a faithful, differently-shaped correct reset is "
            "being rejected for its textual order. (Sibling: pos-reorder.)"),
    },
    {
        "id": "pos-control-localzero",
        "kind": "soundness",
        "expect": "verify",
        # Route the cleared value through a typed local instead of two inline
        # literals (bind-once, store-twice). Same post-state.
        "module": _impl(
            "    let zero : Nat := 0\n"
            "    swappableOccupancy := zero\n"
            "    modelsOccupancy := zero\n"
            "    return ()"),
        "rationale": (
            "structurally-different but CORRECT: the cleared value flows through "
            "a typed local `let zero : Nat := 0` (bind once, store twice) rather "
            "than two inline literals. Definitionally the same post-state, so Q1 "
            "and Q2 both discharge under the frozen script. Confirms the spec is "
            "not over-fit to the literal appearing syntactically at each store. "
            "If it FAILS => SPEC-TOO-STRONG. (Sibling: pos-localvar.)"),
    },
    {
        "id": "pos-control-copy-cleared",
        "kind": "soundness",
        "expect": "verify",
        # CORRECT-by-construction, and the exact dual of the
        # weak-proxy-prevalue rival below: clear the all-models counter FIRST,
        # then source the swappable counter from that ALREADY-CLEARED value. The
        # copied value is 0, so both clauses hold on every input. Included
        # precisely to show the spec rejects the proxy rival for the RIGHT
        # reason (copying a non-zero PRE-value) rather than for copying at all.
        "module": _impl(
            "    modelsOccupancy := 0\n"
            "    swappableOccupancy := modelsOccupancy\n"
            "    return ()"),
        "rationale": (
            "structurally-different but CORRECT-by-construction: the all-models "
            "counter is cleared first, then the swappable counter is sourced "
            "from that already-cleared value (which is 0), so both Q1 and Q2 "
            "hold on every input. This is the exact DUAL of the "
            "weak-proxy-prevalue rival, which copies the same counter's "
            "PRE-value; shipping both pins that the spec rejects the rival for "
            "reading a stale non-zero value, not for the copy shape itself. If "
            "it FAILS => SPEC-TOO-STRONG. (Sibling: pos-copy-other.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the contract carries NO `require` clause, so the sibling's
    # "a normal input satisfies the precondition" probe is vacuous here: nothing
    # could exclude the failing-test-shaped input. Re-aimed at the residual
    # total-domain risk — that the post-image is DEGENERATE at the corner that
    # matters. The failing test primes BOTH caches non-empty before the reset, so
    # the interesting corner is two strictly-positive starting occupancies, where
    # clearing is a REAL transition rather than a no-op.
    #
    # The probe is an in-region ROUNDTRIP over the CONTRACT'S OWN BINDERS: prime
    # both counters to a positive pair, assert (on the binders, not on numerals)
    # that the primed state is the non-empty corner, apply the frozen clears, and
    # assert (again on the binders) that the post-state really is all-zero. Both
    # asserts therefore SPEAK ABOUT the modeled state and the SECOND one DEPENDS
    # on the clears — which a probe stated purely over literals does not, and
    # that distinction is the whole content of the case. All three liveness
    # directions were run: falsifying the post assert (`modelsOccupancy = 1`),
    # falsifying the pre assert (`modelsOccupancy > 5`), and moving one clear
    # BELOW the post assert each leave an unsolved goal (exit 1, the verifier
    # naming `admPost_1` / `admPre_1` and showing the residual `0 = 1` / `5 > 5`
    # / `3 = 0`), while the case as shipped verifies (exit 0).
    # =====================================================================
    {
        "id": "admiss-nonempty-start-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    modelsOccupancy := 5\n"
            "    swappableOccupancy := 3\n"
            "    assert (with_name_prefix `admPre\n"
            "      (modelsOccupancy > 0 ∧ swappableOccupancy > 0))\n"
            "    swappableOccupancy := 0\n"
            "    modelsOccupancy := 0\n"
            "    assert (with_name_prefix `admPost\n"
            "      (modelsOccupancy = 0 ∧ swappableOccupancy = 0))\n"
            "    return ()"),
        "rationale": (
            "the modeled behaviour is admissible AND non-degenerate at the corner "
            "the failing test exercises: both memoizing methods' caches are "
            "primed NON-EMPTY before the reset, so a genuinely positive pair of "
            "starting occupancies must be in-domain and clearing each to 0 must "
            "be a REAL state transition rather than a no-op that would hold "
            "trivially. Stated as a ROUNDTRIP on the contract's own binders: "
            "prime them to (5, 3), assert `modelsOccupancy > 0 ∧ "
            "swappableOccupancy > 0` of that primed state, apply the frozen "
            "clears, then assert `modelsOccupancy = 0 ∧ swappableOccupancy = 0` "
            "of the post-state. Both asserts name the BINDERS, so the case cannot "
            "be satisfied by an arithmetic truth about numerals that never "
            "mentions the modeled state; and the second assert is discharged only "
            "BECAUSE the clears ran, so it witnesses the transition rather than "
            "restating a tautology. Both are LIVE: falsifying either, or moving "
            "one clear below the post assert, leaves an unsolved goal. If the "
            "case FAILED, the interesting input would be excluded or the "
            "post-image degenerate where it matters. Re-aimed from the sibling "
            "admiss-roundtrip, whose construct-a-fresh-registry / "
            "precondition-admission half has no counterpart on a carrier with no "
            "`require` and no heap; the roundtrip SHAPE is what carries over."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong bodies sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete starting-occupancy pair, and the refinement argument that its
    # faithful counterpart would NOT resolve the failing test. Witnesses probe
    # eight DISTINCT points and vary BOTH binders (see BINDER STRUCTURE above).
    # =====================================================================
    {
        "id": "weak-models-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported defect: empty one memoizing method's cache and leave the
        # other method's retained results at whatever they were on entry.
        # Isolates Q2 — Q1 is kept correct.
        "module": _impl(
            "    modelsOccupancy := 0\n"
            "    return ()"),
        "refinement": (
            "this is the pre-change behaviour the issue reports and the failing "
            "test observes: the registry's single cache-reset empties the "
            "all-models lookup's retained results but never touches the "
            "swappable-settings-name lookup's, so that method keeps serving "
            "stale memoized values after a reset that documents itself as "
            "clearing ALL internal caches. Its faithful counterpart is the "
            "un-changed reset; the failing test primes that second cache and "
            "then asserts its occupancy is zero after the reset, which FAILS "
            "because the entry primed for it is still retained. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from Q2 (`swappableOccupancy = 0`): the body never assigns "
            "that counter, so at return it still holds its arbitrary non-negative "
            "on-entry value, which the verifier cannot prove is 0 (the domain is "
            "total — every starting occupancy is admitted). Q1 is kept correct, "
            "isolating Q2 as the ONLY failing clause. If this VERIFIED the spec "
            "would admit the reported defect => SPEC-TOO-WEAK, and the "
            "discriminating content of the required behaviour would be unpinned. "
            "Refuted at (models=4, swappable=3) — the second counter starts "
            "non-empty, so leaving it untouched is observable. (Sibling: "
            "weak-models-only.)"),
        "witness": _witness(4, 3),
    },
    {
        "id": "weak-swappable-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The DUAL omission: empty the second method's cache and leave the
        # first's. Isolates Q1 — Q2 is kept correct.
        "module": _impl(
            "    swappableOccupancy := 0\n"
            "    return ()"),
        "refinement": (
            "the dual omission — a change that REPLACED the existing reset of "
            "one memoizing method's cache with a reset of the other, instead of "
            "adding it. The failing test asserts the occupancy of BOTH memoizing "
            "lookups is zero after the reset, having primed each; leaving the "
            "all-models lookup's retained results in place FAILS the assertion "
            "about that cache. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 (`modelsOccupancy = 0`): that counter is left at its "
            "on-entry value and is not provably 0. Q2 is kept correct, isolating "
            "Q1. This is the mirror of weak-models-only and is what pins that "
            "the spec requires EVERY memoizing method's cache to be emptied, not "
            "just the one the issue names — if it VERIFIED, half the post-image "
            "would be dead => SPEC-TOO-WEAK. Refuted at (models=5, "
            "swappable=2): a DIFFERENT point from weak-models-only, and one "
            "where the surviving counter is the OTHER binder, so the two "
            "witnesses jointly show the post-image constrains both. (Sibling: "
            "weak-swappable-only.)"),
        "witness": _witness(5, 2),
    },
    {
        "id": "weak-neither",
        "kind": "uniqueness",
        "expect": "reject",
        # A no-op reset: return without clearing anything. Fails Q1 AND Q2.
        "module": _impl("    return ()"),
        "refinement": (
            "a no-op reset is what an operation whose body short-circuited (an "
            "early return, or a body that was never wired up) would do: neither "
            "memoizing method's retained results are discarded, so both "
            "occupancies stay at the values the failing test primed. The test "
            "asserts BOTH are zero, so both assertions FAIL. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 AND Q2 simultaneously: both counters keep their "
            "on-entry values and neither is provably 0. The floor case — if it "
            "VERIFIED the spec would not require ANY cache to be emptied => "
            "SPEC-TOO-WEAK, and every other case in this battery would be "
            "meaningless. Refuted at (models=1, swappable=7): both counters "
            "start non-zero (and at yet another pair of values), so a body that "
            "clears neither is observably wrong on both clauses at once. "
            "(Sibling: weak-neither.)"),
        "witness": _witness(1, 7),
    },
    {
        "id": "weak-decrement",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN by value: evict ONE retained entry per cache instead of
        # discarding all of them, guarded to stay non-negative. Correct only
        # where a counter started at 0 or 1.
        "module": _impl(
            "    if modelsOccupancy > 0 then\n"
            "      modelsOccupancy := modelsOccupancy - 1\n"
            "    else\n"
            "      modelsOccupancy := modelsOccupancy\n"
            "    if swappableOccupancy > 0 then\n"
            "      swappableOccupancy := swappableOccupancy - 1\n"
            "    else\n"
            "      swappableOccupancy := swappableOccupancy\n"
            "    return ()"),
        "refinement": (
            "evicting a single retained entry per cache models a reset that pops "
            "one memoization entry (e.g. the least-recently-used head) instead of "
            "discarding the whole cache. Whenever a cache retained two or more "
            "results on entry it stays populated, so a later observer still gets "
            "stale memoized values. The failing test primes the caches and then "
            "asserts each occupancy is zero; a single-eviction reset leaves a "
            "positive occupancy for any cache holding more than one entry, which "
            "FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 AND Q2 on the >= 2 sub-domain: for an on-entry value "
            "v >= 2 the body leaves v-1 > 0, and the domain is total so the "
            "verifier must prove == 0 for EVERY admitted starting occupancy. A "
            "genuine PARTIAL-DOMAIN-by-value break — the body is correct exactly "
            "where a counter started at 0 or 1, which is the sub-domain on which "
            "clearing is nearly a no-op anyway. If it VERIFIED the post-state "
            "would not actually be pinned to 0 => SPEC-TOO-WEAK on an "
            "occupancy-class boundary no byte-fuzzer targets. Refuted at "
            "(models=2, swappable=6): BOTH counters are on the >= 2 sub-domain, "
            "so the decrement leaves both positive. (Sibling: weak-decrement.)"),
        "witness": _witness(2, 6),
    },
    {
        "id": "weak-reprime-swappable",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: clear one cache correctly, then re-prime the other to a
        # fixed non-zero occupancy. Wrong at EVERY input, so its witness is
        # placed at the all-zero boundary — the one point at which every other
        # rival here happens to be RIGHT.
        "module": _impl(
            "    modelsOccupancy := 0\n"
            "    swappableOccupancy := 1\n"
            "    return ()"),
        "refinement": (
            "clearing one memoizing method's cache but leaving the other at a "
            "fixed non-zero occupancy models a reset that discards the first "
            "cache and then immediately re-populates the second (or never fully "
            "empties it — one canonical lookup is re-memoized on the way out). "
            "The failing test asserts that second occupancy is zero after the "
            "reset; a retained single entry FAILS that assertion just as the "
            "un-changed behaviour does. Does NOT resolve."),
        "rationale": (
            "REJECT from Q2 (`swappableOccupancy = 0`): the body pins that "
            "counter to 1, and the clause demands exactly 0 — there is no slack "
            "in the post-image, so a single retained entry is as wrong as a full "
            "cache. Q1 is kept correct, isolating Q2. Refuted at (models=0, "
            "swappable=0): deliberately the ALL-ZERO boundary, the unique point "
            "at which weak-models-only, weak-decrement and weak-coupled-guard "
            "are all accidentally correct — so this witness demonstrates the "
            "post-image bites even on an already-empty registry, where the "
            "operation should be a no-op and this body instead CREATES retained "
            "state. (Sibling: weak-stale-swappable.)"),
        "witness": _witness(0, 0),
    },
    {
        "id": "weak-conditional-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: clear the second cache ONLY when it was already
        # nearly-empty (< 2 retained entries); leave a fuller one stale. Correct
        # on the small-occupancy class, wrong exactly where the defect matters.
        "module": _impl(
            "    modelsOccupancy := 0\n"
            "    if swappableOccupancy < 2 then\n"
            "      swappableOccupancy := 0\n"
            "    else\n"
            "      swappableOccupancy := swappableOccupancy\n"
            "    return ()"),
        "refinement": (
            "emptying the second memoizing method's cache only when it was "
            "already nearly-empty models a mis-guarded size optimisation that "
            "skips the discard on a fuller cache. The failing test primes that "
            "cache and asserts its occupancy is zero afterwards; on any run "
            "where two or more results were retained the cache stays populated "
            "and the assertion FAILS — and 'the cache is full' is precisely the "
            "situation in which a stale-memoization defect is observable at all. "
            "A genuine partial-domain break on the occupancy-class boundary. "
            "Does NOT resolve."),
        "rationale": (
            "REJECT from Q2 (`swappableOccupancy = 0`): on the sub-domain where "
            "that counter started at >= 2 the body leaves it untouched and "
            "non-zero, so the clause cannot be proven for all admitted inputs. "
            "Q1 is kept correct, isolating Q2. Distinct from weak-decrement, "
            "which is wrong on the same sub-domain but by leaving v-1 rather "
            "than v, so each is refuted by its own reasoning; and distinct from "
            "weak-models-only, which is wrong on the WHOLE domain rather than "
            "just this class. Refuted at (models=3, swappable=2) — swappable "
            "sits exactly ON the guard's boundary (the least value the guard "
            "excludes), which is the strongest point to place it. (Sibling: "
            "weak-conditional-skip.)"),
        "witness": _witness(3, 2),
    },

    # ---- The two BINDER-COUPLING rivals. No nagini counterpart: they exist
    # ---- because each clause names one binder's post-state, and a rival is
    # ---- free to make one clause's outcome depend on the OTHER binder. A
    # ---- battery whose witnesses all held one binder at a single value would
    # ---- verify these and never notice.
    {
        "id": "weak-coupled-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Clear the second cache only when the FIRST one was non-empty on entry:
        # makes Q2's outcome depend on the models binder. Correct on the whole
        # sub-domain where the first cache started non-empty — which includes
        # every input at which weak-models-only is refuted.
        "module": _impl(
            "    if modelsOccupancy > 0 then\n"
            "      swappableOccupancy := 0\n"
            "    else\n"
            "      swappableOccupancy := swappableOccupancy\n"
            "    modelsOccupancy := 0\n"
            "    return ()"),
        "refinement": (
            "gating one memoizing method's discard on whether the OTHER method's "
            "cache currently holds anything models a reset that treats a single "
            "cache as the trigger for the whole clean-up — the second discard "
            "runs only when the first cache happened to be populated. Whenever "
            "the first cache is already empty and the second is not (e.g. the "
            "second lookup was consulted but the first was not, which is exactly "
            "how the reported behaviour was noticed on repeated runs) the second "
            "cache is never discarded, and the failing test's assertion that its "
            "occupancy is zero FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q2 (`swappableOccupancy = 0`): on the sub-domain where "
            "the all-models counter starts at 0, the guard is false and the "
            "swappable counter is left at its on-entry value, so Q2 is not "
            "provable for all admitted inputs. Q1 is kept correct, isolating "
            "Q2. THE BINDER-COUPLING CASE: this rival makes Q2's outcome depend "
            "on the OTHER clause's binder, so it is correct at every input where "
            "weak-models-only is refuted and would be missed by a battery that "
            "held the all-models binder positive throughout. Refuted at "
            "(models=0, swappable=4) — the first counter is zero (its own clause "
            "holds trivially) while the second is non-empty, the one corner that "
            "separates this rival from the frozen behaviour. If it VERIFIED, the "
            "spec would let one cache's discard be conditioned on the other's "
            "state => SPEC-TOO-WEAK."),
        "witness": _witness(0, 4),
    },
    {
        "id": "weak-proxy-prevalue",
        "kind": "uniqueness",
        "expect": "reject",
        # Source the second counter from the FIRST counter's PRE-value, then
        # clear the first. Looks like the correct pos-control-copy-cleared but
        # reads the value BEFORE the clear, so the second cache inherits the
        # first's stale occupancy. Wrong exactly where the first cache started
        # non-empty.
        "module": _impl(
            "    swappableOccupancy := modelsOccupancy\n"
            "    modelsOccupancy := 0\n"
            "    return ()"),
        "refinement": (
            "'synchronising' one memoizing method's occupancy to the other's, "
            "read BEFORE the other is discarded, models a reset that reports the "
            "second cache as matching the first while never actually discarding "
            "the second cache's retained results. It only ever looks right when "
            "the first cache was already empty. The failing test primes both "
            "caches and asserts each occupancy is zero; the second inherits the "
            "first's primed occupancy and FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q2 (`swappableOccupancy = 0`): the counter is set to "
            "the OTHER counter's PRE-value, which the total domain admits at any "
            "non-negative value, so it is not provably 0. Q1 is kept correct, "
            "isolating Q2. The NEAR-MISS of pos-control-copy-cleared, which "
            "performs the same copy AFTER the clear and is correct: the two ship "
            "together so the reject is attributable to reading a stale non-zero "
            "value rather than to the copy shape. Second binder-coupling case — "
            "here Q2's post-value is SOURCED from the other binder rather than "
            "merely guarded by it. Refuted at (models=6, swappable=1): the first "
            "counter is non-empty (so the inherited value is non-zero) while the "
            "second starts at 1, a point no other witness uses. If it VERIFIED, "
            "the spec would accept one cache's occupancy standing in for the "
            "other's => SPEC-TOO-WEAK. (Sibling: the value-proxy reading of "
            "weak-copy-other, which the nagini carrier could only express in its "
            "already-cleared — and therefore CORRECT — order.)"),
        "witness": _witness(6, 1),
    },
    {
        "id": "weak-mirror-coupled-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR of weak-coupled-guard, and the case that closes the last
        # unattacked corner. Every other rival here keeps Q1 correct or breaks it
        # unconditionally; none makes Q1's outcome depend on the OTHER binder, and
        # no witness above sits at (models > 0, swappable = 0). This rival gates
        # the all-models discard on whether the swappable cache was non-empty, so
        # it is correct on the whole sub-domain where swappable started positive —
        # which is EVERY point the other reject witnesses occupy except (0,0),
        # where its own clause holds trivially.
        "module": _impl(
            "    if swappableOccupancy > 0 then\n"
            "      modelsOccupancy := 0\n"
            "    else\n"
            "      modelsOccupancy := modelsOccupancy\n"
            "    swappableOccupancy := 0\n"
            "    return ()"),
        "refinement": (
            "gating the all-models discard on whether the OTHER memoizing "
            "method's cache currently holds anything models a reset that treats "
            "the second cache as the trigger for the whole clean-up. Whenever the "
            "second lookup was never consulted (its cache empty) while the "
            "all-models lookup was, the all-models cache is never discarded and "
            "keeps serving stale memoized values — and a reset documenting itself "
            "as clearing ALL internal caches must not depend on which lookups "
            "happened to run first. The failing test primes both caches and "
            "asserts each occupancy is zero afterwards; on a run where only the "
            "all-models cache was primed, that assertion FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 (`modelsOccupancy = 0`): on the sub-domain where the "
            "swappable counter starts at 0 the guard is false and the all-models "
            "counter is left at its on-entry value, so Q1 is not provable for all "
            "admitted inputs. Q2 is kept correct, isolating Q1. The MIRROR of "
            "weak-coupled-guard, and the case that makes the coupling probe "
            "symmetric: without it Q1 is only ever attacked UNCONDITIONALLY "
            "(weak-swappable-only, weak-neither, weak-decrement) and a rival that "
            "conditions Q1 on the swappable binder would be missed. Refuted at "
            "(models=5, swappable=0) — the sign combination no other witness in "
            "this battery occupies: the first counter non-empty while the second "
            "is empty, the one corner that separates this rival from the frozen "
            "behaviour. If it VERIFIED, the spec would let the all-models discard "
            "be conditioned on the other cache's state => SPEC-TOO-WEAK. (No "
            "sibling counterpart: added by the audit lane.)"),
        "witness": _witness(5, 0),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING
#
# The sibling battery has 12 SPEC cases (3 soundness positives, 1 admissibility,
# 8 uniqueness rivals) plus a two-case AXIOM lane — counted from the sibling
# manifest in the audit lane; the ported footer said "11 SPEC cases / 7 rivals",
# which undercounted by one and is corrected here (the per-case table below was
# already complete, so no case was actually unaccounted for). Contracting
# `clear_all_caches(registry)` over a permission-bearing heap object with a
# three-clause precondition (two FULL permissions plus a total-correctness
# obligation) and a four-clause postcondition (two framing plus two
# load-bearing). This bundle models the SAME two load-bearing clauses on a
# narrower, referentially-transparent carrier: two `mut Nat` value binders, no
# permissions to return and no precondition at all. So the two framing
# postconditions and both permission preconditions have no counterpart. The
# sibling's total-correctness precondition DOES have a counterpart here — this
# bundle's `set_option loom.semantics.termination "total"` — so that clause is
# carried, not dropped; what is missing is only a shippable reject CASE for it,
# for the witness-side reason recorded below.
#
#   sibling case (nagini)      -> here
#   ---------------------------------------------------------------------
#   pos-reorder                -> pos-control-reorder             PORTED
#   pos-localvar               -> pos-control-localzero           PORTED
#   pos-copy-other             -> pos-control-copy-cleared        PORTED
#   admiss-roundtrip           -> admiss-nonempty-start-nondegen. RE-AIMED
#   weak-models-only           -> weak-models-only                PORTED (headline)
#   weak-swappable-only        -> weak-swappable-only             PORTED
#   weak-neither               -> weak-neither                    PORTED
#   weak-decrement             -> weak-decrement                  PORTED
#   weak-stale-swappable       -> weak-reprime-swappable          PORTED
#   weak-conditional-skip      -> weak-conditional-skip           PORTED
#   weak-diverge               -> (none)                          NO WITNESS POSSIBLE
#   weak-self-echo             -> (none)                          INEXPRESSIBLE
#   (no counterpart)           -> weak-coupled-guard              NEW (binder coupling)
#   (no counterpart)           -> weak-proxy-prevalue             NEW (binder coupling)
#   (no counterpart)           -> weak-mirror-coupled-guard       NEW (audit lane)
#   AXIOM_TESTS (2)            -> (none)                          DROPPED (G-AX's lane)
#
# PORTED (9 of 12; the other 3 are the re-aimed admiss plus the two accounted
#   omissions below). All three positives and all six value-level rivals carry over
#   directly: the sibling's field stores become `mut Nat` assignments and every
#   argument survives intact, because the clauses being attacked (`== 0` on each
#   occupancy) are identical on both carriers. Each positive was confirmed to
#   VERIFY with a real build under the frozen `loom_solve` script; each rival was
#   confirmed NOT to verify, with the verifier naming the expected clause in its
#   unsolved goal (`ensures_1: swappableOccupancy = 0` / `ensures_2:
#   modelsOccupancy = 0`), and each carries a witness SEEN to discriminate over
#   two real builds. Two Velvet mechanics differ from the sibling and are handled
#   in the bodies rather than reported as blockers: a `Unit`-returning method
#   needs an explicit `else` arm on every `if` (a bare one-armed `if` is a type
#   error, not a spec verdict), and the no-op body is `return ()` rather than a
#   bare `return`.
#
# RE-AIMED (admiss). The sibling's admissibility case constructs a fresh
#   registry, asserts the precondition admits it, applies the reset in-line, and
#   asserts the result — a probe aimed at three `Requires` clauses. This contract
#   has NO `require` clause, so "a normal input is admitted" is vacuous here:
#   nothing could exclude it. The case is re-aimed at the residual total-domain
#   risk, that the post-image is degenerate at the corner the failing test
#   exercises (both caches primed NON-EMPTY, so each clear is a real transition
#   rather than a no-op).
#
#   REPAIRED IN THE AUDIT LANE. The ported form stated its assert entirely over
#   NUMERALS (`(5 : Nat) > 0 ∧ (3 : Nat) > 0 ∧ ...`), which mentions neither
#   binder and is closed by arithmetic alone — measured: substituting the
#   unrelated tautology `(1 : Nat) + 1 = 2` for the whole conjunction leaves the
#   case verifying at exit 0, so the assert carried no case-specific content and
#   the "non-degenerate at the corner that matters" claim in the rationale was
#   not demonstrated. (The port's liveness check was real but proved only that a
#   FALSE numeral claim fails, which any false claim does.) Replaced with an
#   in-region ROUNDTRIP over the contract's own binders: prime them to (5, 3),
#   assert `modelsOccupancy > 0 ∧ swappableOccupancy > 0`, apply the frozen
#   clears, assert `modelsOccupancy = 0 ∧ swappableOccupancy = 0`. Both asserts
#   now name the MODELED STATE, and the post assert is discharged only because
#   the clears ran. Liveness measured in three directions, each exit 1 with an
#   unsolved goal: falsify the post assert (`admPost_1`, residual `0 = 1`),
#   falsify the pre assert (`admPre_1`, residual `5 > 5`), and move one clear
#   below the post assert (`admPost_1`, residual `3 = 0`). As shipped: exit 0.
#
# UNSHIPPABLE FOR A WITNESS REASON (weak-diverge) — NOT a spec hole on this cell,
#   and the previous entry here was WRONG on its premise. It said this bundle sets
#   `loom.semantics.termination "partial"` and that a spliced non-terminating
#   prefix "elaborates at exit 0". The frozen Solution.lean sets `"total"`, and
#   re-measured in the audit lane the spec REJECTS the whole class:
#     - measure-less `while True do pure ()` prefix -> exit 1, `Decreasing
#       annotations are required in total correctness semantics`;
#     - `while k > 0 ... decreasing (0 : Nat)` (a measure that does not decrease)
#       followed by a WRONG post-state -> exit 1 on the spec's own goals,
#       `ensures_1 ... ⊢ 9 = 0` / `ensures_2 ... ⊢ 7 = 0` with `done_1` in
#       context, so the continuation after the loop is still verified against both
#       clauses here.
#     - `done_with` omitted; `done_with False`; a strictly INCREASING measure
#       (`decreasing k` with `k := k + 1`) -> each exit 1 as well.
#     - the SAME loop with a CORRECT continuation, so only the measure can be at
#       fault -> STILL exit 1, on the measure's own descent goal:
#           unsolved goals
#           case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#   RETRACTION. A previous revision of this row claimed that this last shape "DOES
#   elaborate and verify (exit 0)", read it as observationally correct because both
#   counters still end at 0, and pointed at a corpus-wide non-decreasing-measure
#   hole. The build above contradicts that and the claim is withdrawn: the
#   strict-decrease side condition is a real goal here and a constant measure fails
#   it. Mechanism: line 4's `set_option loom.semantics.termination "total"` itself
#   opens the `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`,
#   `openScope `TotalCorrectness`), line 7 opens it again, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#   `measure b' < measure b` as a goal; only the `PartialCorrectness` twin drops it.
#   Nor can the class ship as a reject case, for a reason on the WITNESS side
#   rather than the spec side: a rival whose loop does not elaborate never defines
#   the extracted program, so the witness build against the RIVAL (the half that
#   must SUCCEED) fails at exit 1 with ``Tactic `decide` failed ... did not reduce
#   to `isTrue` or `isFalse``` , the gate's `reduction` screen, i.e.
#   `witness-unproven`/`witness-undecided`, never a refutation. Recorded as a
#   carrier/witness limit on this cell, not as a defect of the frozen spec, and no
#   spec hole is escalated from the class.
#
# INEXPRESSIBLE (weak-self-echo) — built, run, and dropped on the evidence.
#   The sibling discharges the contract by calling the function under spec, and
#   is rejected there by an obligation-leak check. Here the analogous body
#   (`let _ ← clearAllCaches modelsOccupancy swappableOccupancy`) is rejected by
#   Lean's own totality checker before the contract is ever consulted: "fail to
#   show termination for clearAllCaches ... no parameters suitable for structural
#   recursion", because a `method` is elaborated to a total Lean definition and
#   this one recurses on unchanged arguments. That would make the case pass for
#   entirely the wrong reason (definability, not the postcondition), and the same
#   error breaks the WITNESS build — whose success is the half that must hold —
#   so no discriminating witness exists. Dropped as genuinely inexpressible on
#   this carrier, not for proof difficulty. RE-DERIVED INDEPENDENTLY in the audit
#   lane and CONFIRMED: the rival module exits 1 on the termination error alone
#   (`fail to show termination for clearAllCaches ... it is unchanged in the
#   recursive calls ... no parameters suitable for structural recursion`), and the
#   witness build against that same rival ALSO exits 1 — not by refutation but by
#   stuck reduction (`Tactic `decide` failed ... did not reduce to `isTrue` or
#   `isFalse``), because the undefinable constant never unfolds. So the half that
#   must SUCCEED cannot, and the gate would record `witness-unproven`. Genuinely
#   inexpressible; not a tooling bug either, since the error is Lean's totality
#   checker refusing the rival's own definition rather than surgery damage.
#
# NEW (3). None has a sibling counterpart; all were added for binder coverage,
#   which case-count parity would not have produced. Each clause names exactly
#   one binder's post-state, so a rival can make one clause's outcome depend on
#   the OTHER binder — either by GUARDING the discard on it (weak-coupled-guard,
#   and its audit-lane mirror weak-mirror-coupled-guard) or by SOURCING the
#   post-value from it (weak-proxy-prevalue). The first two are correct on the
#   entire sub-domain where the all-models counter starts positive, so a battery
#   that held that binder positive across all its witnesses would verify them and
#   report SOUND; their witnesses sit at (0, 4) and (6, 1) precisely to break
#   that pinning. weak-mirror-coupled-guard closes the remaining asymmetry found
#   by the audit: Q1 was attacked only UNCONDITIONALLY, so a rival conditioning
#   Q1 on the swappable binder was unattacked, and no witness occupied the
#   (models > 0, swappable = 0) corner. Its witness sits at (5, 0).
#
# DROPPED (AXIOM_TESTS). The axiom lane belongs to G-AX, which this gate ignores,
#   and this bundle declares no `axiom` in any case: the cache-reset is modeled
#   deeply as two state writes and the standard-library memoization wrapper whose
#   emptied-cache effect they refine is an A-reference validated out-of-band.
#
# CLAUSE / BINDER COVERAGE (the part the gate does not check).
#   Both independent top-level clauses are DEFENDED and ATTACKED, and each is
#   attacked both UNCONDITIONALLY and under COUPLING to the other binder:
#     Q1 `modelsOccupancy = 0`    — defended by all 3 positives + the
#        admissibility case; attacked unconditionally by weak-swappable-only,
#        weak-neither, weak-decrement, and under coupling by
#        weak-mirror-coupled-guard.
#     Q2 `swappableOccupancy = 0` — defended by all 3 positives + the
#        admissibility case; attacked unconditionally by weak-models-only,
#        weak-neither, weak-decrement, weak-reprime-swappable,
#        weak-conditional-skip, and under coupling by weak-coupled-guard
#        (guarded) and weak-proxy-prevalue (sourced).
#   The NINE reject witnesses probe NINE DISTINCT points (pts=9):
#     (4,3) weak-models-only        (5,2) weak-swappable-only
#     (1,7) weak-neither            (2,6) weak-decrement
#     (0,0) weak-reprime-swappable  (3,2) weak-conditional-skip
#     (0,4) weak-coupled-guard      (6,1) weak-proxy-prevalue
#     (5,0) weak-mirror-coupled-guard
#   `modelsOccupancy` is varied over {0, 1, 2, 3, 4, 5, 6} and
#   `swappableOccupancy` over {0, 1, 2, 3, 4, 6, 7}. Both include 0 and several
#   positive values, and the pairs cover all FOUR sign combinations: both zero
#   (0,0), first zero only (0,4), SECOND zero only (5,0), both positive (several).
#   The audit lane found the third of those genuinely MISSING before (5,0) was
#   added — the previous footer claimed it "via (3,2)/(6,1)-style positives",
#   which are both-positive pairs, so the claim was false and the corner where a
#   models-side coupling is observable was unprobed. The occupancy-class boundary
#   (< 2 vs >= 2) is probed from both sides. So neither binder is pinned, and no
#   rival's refutation rests on a value another rival's refutation also needs.
#   Every witness is stated at LITERAL inputs and binds NOTHING, so
#   `consistency_probe` is `None` and no witness can be
#   inconsistent-by-hypothesis; each was run against the rival (exit 0) and the
#   frozen solution (exit 1, `decide` proving the tester TRUE there) and was SEEN
#   to discriminate.
#
# AUDIT-LANE PROBES THAT FOUND NOTHING (recorded so the next reader need not
# re-spend the builds). Eight NEW rivals aimed at what the shipped set leaves
# alone were built against the frozen spec and ALL were correctly REJECTED, each
# with the verifier naming the expected clause: a zero-point flip (clear unless
# already empty, then set 1 — residual `1 = 0` under `if_pos`), a `Nat`-truncating
# clamp (`counter - 1000000`), `counter % 2`, an outright SWAP of the two
# counters (both clauses unsolved at once), `min counter 1`, a post-clear copy of
# a non-zero literal, a guard on the counter's OWN pre-value, and the mirror
# rival now shipped above. So the two `Nat`-specific traps a truncating carrier
# invites — saturating subtraction and a clamp that is definitionally 0 on part
# of the domain — do not slip past the post-image. Four NEW correct reshapes were
# also built and ALL VERIFY under the frozen `loom_solve`: `counter - counter`
# paired with `counter * 0`, both stores wrapped in a both-arms-zero `if`, a
# self-subtract followed by a copy, and a terminating `while counter > 0 do
# counter := counter - 1` drain loop. So the spec is neither too weak on those
# points nor over-fit to the frozen body's shape; the drain loop in particular
# shows a loop-shaped faithful reset is provable here.
#
# SECOND AUDIT PASS — probes re-run independently, plus new ones. All 31 builds of
# the shipped battery were re-derived from scratch: all 9 rival variants exit 1
# with the verifier naming exactly the clause each rationale claims (checked
# mechanically — `ensures_1: swappableOccupancy = 0` for weak-models-only,
# weak-conditional-skip, weak-coupled-guard, weak-proxy-prevalue,
# weak-reprime-swappable; `ensures_2: modelsOccupancy = 0` for
# weak-swappable-only and weak-mirror-coupled-guard; BOTH for weak-neither and
# weak-decrement), all 9 witnesses exit 0 against their rival and exit 1 against
# gold with a plain evaluation refutation, and all 4 positives exit 0.
#
#   FORGERY TEST (attack B'), which the gold signatures here did not strictly
#   require (they are plain evaluations) but which was run anyway on four of the
#   nine points: flipping the claim to `clearAllCachesTester m s = true` and
#   building it against the FROZEN solution exits 0 at (4,3), (0,0), (5,0) and
#   (0,4). So gold's exit code tracks the CLAIM rather than being constant — the
#   `decide` really evaluates the tester on each side, and the nine rejections are
#   genuine refutations, not a constant-failure artifact.
#
#   Seven further NEW rivals were built against the frozen spec and ALL rejected:
#   a cross-binder `min modelsOccupancy swappableOccupancy` (residual
#   `min modelsOccupancyOld swappableOccupancyOld = 0`), a guard on the counter's
#   own parity (`if modelsOccupancy % 2 = 0`, residual `modelsOccupancyOld = 0`
#   under `if_neg`), plus re-runs of the swap / `min counter 1` / `- 1000000` /
#   `% 2` traps. Two further correct reshapes VERIFY (`counter % 1`; a
#   both-arms-zero `if`). Admissibility liveness re-measured in all three
#   directions the case claims (exit 1 with residuals `0 = 1`, `5 > 5 ∧ 3 > 0`,
#   and `5 = 0` respectively) and confirmed live; the shipped case exits 0. Note
#   the pre-assert alone is NOT sufficient to carry the case — substituting the
#   numeral tautology `(1 : Nat) + 1 = 2` for it still verifies (exit 0) — which
#   is why the POST assert, discharged only because the clears ran, is the half
#   that gives this case its content.
AXIOM_TESTS = []
