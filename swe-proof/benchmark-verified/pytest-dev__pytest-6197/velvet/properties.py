"""properties.py — G-PBT falsification battery for pytest-dev__pytest-6197 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct gatherEntries`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method that enumerates the child items of a
directory carrying an initialization file, reporting alongside them whether the
walk loaded the directory's own initialization file as a side effect:

  gatherEntries (initMatches : Bool) (initNode : Nat) (entries : List PkgEntry)
      return (out : List Nat × Bool)
    ensures out.2 = false                                             -- (C1)
    ensures out.1 = (if initMatches then [initNode] else [])
                      ++ walkEntries entries                          -- (C2)

TWO independent, load-bearing top-level ``ensures`` clauses over the three input
binders ``initMatches`` / ``initNode`` / ``entries`` (whose sub-fields
``PkgEntry.boundary`` / ``PkgEntry.isFile`` / ``PkgEntry.yields`` are the further
sub-inputs the reject witnesses vary):

  * (C1) ``out.2 = false`` — THE fix. The walk is a directory-structure
    operation and must NOT load the directory's own initialization file as a
    side effect; the load event is carried as the second result component and
    pinned to ``false`` unconditionally. This is the clause the failing tests
    behaviorally grade: whether merely scanning a directory imported its own
    initialization file (running its top-level code). SCOPE OF C1, as measured by
    this audit: C1 pins the REPORTED value of that component, which on a
    final-state-only WP is strictly weaker than pinning the EVENT. A body that
    performs the load and then reports ``false`` verifies (three real builds; see
    the fire-then-launder finding in the ADVERSARIAL READ above). So C1 rejects
    an enumeration that reports its eager load HONESTLY — which is what the
    pre-image does, and what ``rival-eager-load`` pins — but does not reject one
    that launders the report. That residual is a FROZEN-SPEC fragment limit,
    escalated rather than patched here.
  * (C2) ``out.1 = (if initMatches then [initNode] else []) ++ walkEntries
    entries`` — the produced sequence, pinned exactly to the walk of the given
    entries with the leading initialization-file item when it matches. This
    prevents trading correctness of the output for the loading obligation or
    vice versa: an enumeration cannot satisfy C1 by returning garbage. Both
    ``walkEntries`` and the ``if initMatches`` prefix are TRANSPARENT ``def``s /
    expressions over the method's own inputs — there is NO opaque answer-key
    oracle in either clause (the ``axioms`` region is empty), so both pins are
    grounded, not echoes.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
contracts TWO functions of a two-phase lazy-load state machine — ``access_object``
(the exactly-one-lazy-load transition) and ``enumerate_children`` (discovery
loads nothing) — over a mutable ``Container`` carrying ``loaded : bool`` and
``load_count : int``. This Lean-family bundle models only the discovery/
enumeration core (``gatherEntries``): one ``method``, one ``prove_correct``. The
``access_object`` phase and its ``load_count`` counter have NO counterpart here,
so the nagini rivals attached to that phase are carrier-narrowed away (see the
accounting footer). What DOES carry is discovery's load-bearing guarantee —
"the walk loads nothing" — now a single Boolean result component ``out.2``
rather than a mutable ``load_count``/``loaded`` pair.

  * FRAME / PERMISSION-MUTATION — the permission MECHANISM is vacuous, but the
    BEHAVIOUR it guards is NOT fully pinned on this carrier. The nagini sibling
    notes there is NO read-only ``Acc(.,1/2)`` input (both functions may
    legitimately mutate the full-permission container), so the classic
    insufficient-permission frame probe does not apply on EITHER backend. Velvet
    is referentially transparent: the inputs are immutable values, there is no
    ``mut`` binder, no heap, no aliasing, no permission system. The nagini file
    realizes its frame concern as a VALUE-frame rival (``enum-frame-write``, an
    eager load during discovery rejected by the value-level
    ``load_count == Old(...)`` clause); on this carrier the NAIVE form of that
    attack — report the load event honestly — is captured by C1
    (``out.2 = false``) and exercised by ``rival-eager-load`` below.

    AUDIT FINDING (escalated, NOT fixable in this lane). C1 pins the REPORTED
    value of the load-event component, and on a final-state-only WP that is
    strictly weaker than pinning the EVENT. A body that performs the load into a
    local and then reports ``false`` — the fire-then-launder family — satisfies
    both clauses and VERIFIES against the frozen spec. Measured here with three
    real builds, each a clean elaboration (exit 0, no error, no ``sorry``), all
    three inside ``variant_scope`` (no new axiom/theorem/``sorry``, spec view
    byte-identical): a discarded-local load, a load followed by resetting the
    reported flag to ``false``, and a load whose flag is laundered through
    ``loaded && !loaded``. Under the declared bijection each corresponds to a
    walk that DID load, so its faithful counterpart does not resolve — i.e.
    ``verify ⟹ correct`` fails. This is the fragment limit the backend spec guide
    records for effect-shaped fixes whose returned value is computable WITHOUT
    the effect: no final-state predicate over a freely-written output can pin an
    irreversible event. The repair needs a pre-state / framed-effect primitive
    the logic does not have, so it is a SPEC finding to escalate, not a battery
    edit — a rival that VERIFIES cannot be shipped as an ``expect="reject"``
    case, and re-aiming it as a positive would assert a wrong impl is correct.
    Recorded in the audit payload's ``spec_holes``; the six reject cases below
    are unaffected and each still earns its outcome.
  * DIVERGENCE / NON-TERMINATION — UNSHIPPABLE on this cell for a WITNESS
    reason, and NOT a known hole. The nagini sibling carries an explicit
    divergence rival (``enum-diverge-loop``, ``while True: pass`` at the head of
    discovery) rejected only by ``Requires(MustTerminate(2))``. This bundle sets
    ``loom.semantics.termination "total"``, as do all 500 velvet bundles; none
    reads ``partial``, so there is no cohort anywhere in this corpus for which
    divergence is a known hole. Under ``total`` a postcondition is claimed of ALL
    runs, so the verifier demands a decreasing measure on every loop. Three
    facts here are each MEASURED with real builds, not argued:

      1. a diverging body IS writable on this carrier and stays inside
         ``variant_scope`` (a ``while spin do spin := true`` head prefixed to the
         frozen body), and it IS rejected — ``error: Decreasing annotations are
         required in total correctness semantics``, exit 1;
      2. the ``total`` obligation is not merely a linter formality here: a loop
         carrying a NON-DECREASING measure (``while 0 < 1`` with
         ``decreasing (0 : Nat)``) that returns an unambiguously wrong answer is
         ALSO rejected on this cell, with ``unsolved goals / case «decreasing_1:
         (0 : Nat)» ⊢ False``, and so is the same shape over a live variable
         (``let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q / done_with q = 0
         / decreasing q do q := q``), which lands on ``case «decreasing_1: q»``
         with residual ``⊢ q < q``. There is no residual hole for non-decreasing
         measures to reach this bundle: an earlier revision of this file recorded
         one corpus-wide, and it does not reproduce anywhere it was rebuilt.
         Loom's ``TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop``
         (``Loom/MonadAlgebras/NonDetT/Basic.lean:544``) takes ``measure : β ->
         Nat`` and emits ``measure b' < measure b``; only the
         ``PartialCorrectness`` twin (:211) takes an ``Option ℕ`` and DISCARDS it;
      3. it nonetheless cannot SHIP as an ``expect="reject"`` case, because the
         gate requires a refutation witness and no witness can discriminate here.
         Measured: the ``decide``-style witness built against a diverging rival
         fails with ``Tactic `decide` failed ... its `Decidable` instance ... did
         not reduce to `isTrue` or `isFalse``` — the gate's own
         ``_STUCK_REDUCTION`` screen — and it fails with the BYTE-IDENTICAL
         message against a diverging rival that returns the unambiguously WRONG
         answer. The diverging loop is exactly the ``Classical.choice`` term the
         kernel cannot unfold, so the witness's exit code carries no information
         about the claim on EITHER side and the case would land
         ``witness-undecided`` (inconclusive => gate error), never a refutation.

    So the disposition is "nothing shippable", for the witness reason rather than
    for the reason an earlier draft of this file gave ("a non-terminating body
    cannot even be written"), which an audit build refuted. NO known hole to
    record: the spec does reject the class, the battery simply cannot attest to it
    through the witness channel this gate requires.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. C1 is attacked by the
    eager-load rival; C2 is attacked on every structural decision the walk makes
    (the init prefix's presence, its dependence on ``initMatches``, and — added
    by the a8 audit — its INDEPENDENCE from ``entries``; the boundary-skip
    predicate; the regular-file test; and the per-file contribution's presence,
    its MULTIPLICITY, and its ORDER, the last two also added by the a8 audit).

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``gatherEntriesTester initMatches initNode entries = false`` says the extracted
program's observable output violates the method's postcondition at that concrete
input. Checked in a file whose ``prove_correct`` block is stripped by the gate,
so no tactic script can mask the verdict. Every clause here is over TRANSPARENT
carriers (``Bool``, ``Nat``, ``List Nat``, ``List PkgEntry`` — all with decidable
equality; no opaque callee), so every witness closes by ``decide`` at concrete
literals and no witness binds a hypothesis — there is no joint-satisfiability
obligation. Each reject witness below was run against BOTH the rival (exit 0)
and the frozen solution (exit 1) with two real builds via
``scripts/lean_verify.sh`` and was SEEN to discriminate. No banned token
(sorry/admit/native_decide/axiom/opaque) appears in any witness.

Every witness was additionally FORGERY-tested (a8 audit), because "the gold-side
error looks semantic" is not evidence either way — only an error that CHANGES
when the claim changes is. For each of the nine, a second file differing from the
witness ONLY in what it claims (``= false`` flipped to ``= true``) was built
against both subjects, and the result is the exact inversion: the flipped claim
BUILDS against the frozen solution (exit 0) and FAILS against the rival (exit 1),
with the rival-side error naming the flipped proposition. So gold's exit code is
a function of the claim, not a constant property of the file, and none of the
gate's hollow-signature classes applies here: every gold-side failure is a plain
evaluation, ``Tactic `decide` proved that the proposition <tester call> = false
is false``, with no stuck reduction, no missing ``Decidable`` instance, no
unification failure on an unreduced loop term, and no type error.

Why a plain evaluation is available at all, when much of the corpus cannot get
one: the frozen impl is a straight-line ``foldl`` with NO loop, so nothing in the
tester elaborates through ``Classical.choice`` and the kernel reduces every claim
on both sides. That is also exactly why the divergence class below cannot ship —
the moment a rival introduces a loop, the same ``decide`` goes stuck for EVERY
claim (measured; see the DIVERGENCE bullet).

AXIOM lane: EMPTY. ``meta.json`` / mapping.md §3 declare no axioms and no
deep-model references (the walk calls no unchanged external operation; the
per-file resolution enters as the plain ``yields`` data of each entry, and the
load event is modeled deeply as the ``false`` result component). Nothing in the
proof rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-6197"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (marker lines and inline
# ---- comments included); lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both facts asserted
# ---- at load by _swap).
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    -- Walk the enumerated paths and gather the child items; the directory's\n"
    "    -- own initialization file is never loaded during the walk (the loaded\n"
    "    -- flag reported is false).\n"
    "    let mut collected : List Nat := []\n"
    "    if initMatches then\n"
    "      collected := collected ++ [initNode]\n"
    "    collected := entries.foldl\n"
    "      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)\n"
    "      collected\n"
    "    return (collected, false)\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script is elided from the consumer
# ---- spec view (only the obligation header is kept), so a case may retune the
# ---- tactic body without touching the spec statement or dropping the
# ---- obligation. Unique in the file.
_GOLD_PROOF = (
    "prove_correct gatherEntries by\n"
    "  loom_solve <;> simp_all [foldl_walkEntries]"
)
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"


def _impl(body, proof=None):
    """Full Solution.lean variant with the gold impl body replaced (and,
    optionally, the elided proof retuned for a loop-free reshape)."""
    src = _swap(_BASE, _GOLD_IMPL, body)
    if proof is not None:
        src = _swap(src, _GOLD_PROOF, proof)
    return src


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. `gatherEntriesTester im inn es = false` says the extracted
# ---- program's observable output violates the postcondition at that concrete
# ---- input. No `axiom`/`sorry`/`native_decide`; the frozen solution rejects
# ---- each witness (its extracted program satisfies both clauses at every input,
# ---- so the tester is `true` and the `= false` claim FAILS on gold).
def _witness(call):
    return (
        "extract_program_for gatherEntries\n"
        "prove_precondition_decidable_for gatherEntries\n"
        "prove_postcondition_decidable_for gatherEntries\n"
        "derive_tester_for gatherEntries\n\n"
        f"example : {call} = false := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG. Both verified
    # out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the produced sequence DIRECTLY as C2's transparent RHS,
        # no fold-into-accumulator loop. C2 is literally `out.1 = (if initMatches
        # then [initNode] else []) ++ walkEntries entries`, so this is the
        # cheapest HONEST correct impl — and, since both `walkEntries entries` and
        # the prefix are GROUNDED in the inputs (not an opaque answer key), it
        # doubles as proof the spec is not echo-vulnerable (any WRONG gathering
        # fails C2). The fold is gone, so the frozen proof's `foldl_walkEntries`
        # rewrite is unneeded and the residual goal closes under `loom_solve` alone.
        "module": _impl(
            "    -- impl-start\n"
            "    return ((if initMatches then [initNode] else []) ++ walkEntries entries, false)\n"
            "    -- impl-end",
            proof="prove_correct gatherEntries by\n  loom_solve"),
        "rationale": (
            "both clauses' post-images are GROUNDED in the inputs (a transparent "
            "front-recursive `walkEntries` fold and a literal `if initMatches` "
            "prefix, no opaque answer key), so returning them directly with the "
            "load flag `false` is the honest cheapest CORRECT impl; C1/C2 are "
            "literally what it returns, so it MUST verify, else SPEC-TOO-STRONG. "
            "Re-expresses the nagini pos-enum-readonly honest control (a discovery "
            "body that computes the answer with no spurious load), and shows the "
            "spec is not echo-vulnerable (any wrong gathering fails C2)."),
    },
    {
        "id": "pos-control-prefix-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the fold-into-accumulator shape but bind the leading
        # init-file prefix to a typed local `prefixItems` and seed the accumulator
        # with it, instead of the inline `if initMatches then collected := ...`.
        # Same value flow, different control shape; the frozen proof still closes.
        "module": _impl(
            "    -- impl-start\n"
            "    let prefixItems : List Nat := if initMatches then [initNode] else []\n"
            "    let mut collected : List Nat := prefixItems\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the leading "
            "init-file prefix to a typed local and seed the accumulator with it, "
            "rather than an inline mutation) must verify; the value flow is "
            "unchanged so C1/C2 still discharge and the frozen fold proof closes "
            "as-is. Ports the nagini pos-enum-readonly reshape idea: if it failed "
            "=> SPEC-TOO-STRONG (over-fit to the inline-prefix code form)."),
    },

    {
        "id": "pos-control-foldr",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E, SPEC-TOO-STRONG probe). Reshape: accumulate
        # with a RIGHT fold whose step prepends each entry's contribution, rather
        # than the frozen LEFT fold into an accumulator. This is the shape that
        # matches `walkEntries`'s own front-recursion, and it is the reshape most
        # likely to be rejected by a spec over-fit to the `foldl` form — the
        # frozen `foldl_walkEntries` lemma is useless for it, so the residual goal
        # must be closed by its own inline induction (no NEW top-level lemma: only
        # the elided tactic body changes, so the obligation and spec view survive
        # byte-identical). Verified with a real build (exit 0, clean elaboration).
        "module": _impl(
            "    -- impl-start\n"
            "    let gathered : List Nat := entries.foldr\n"
            "      (fun e acc => (if e.boundary || !e.isFile then [] else e.yields) ++ acc) []\n"
            "    return ((if initMatches then [initNode] else []) ++ gathered, false)\n"
            "    -- impl-end",
            proof="prove_correct gatherEntries by\n"
                  "  loom_solve <;>\n"
                  "    (induction entries with\n"
                  "     | nil => simp [walkEntries]\n"
                  "     | cons e es ih => simp only [List.foldr_cons, walkEntries]; simp_all)"),
        "rationale": (
            "a correct impl whose accumulation runs in the OPPOSITE direction "
            "(right fold prepending each contribution) must verify: it computes "
            "the same function as the frozen left fold, so C1/C2 hold. This is a "
            "sharper SPEC-TOO-STRONG probe than the two existing positives, both "
            "of which keep the frozen `foldl` (prefix-local) or drop the fold "
            "entirely (direct): neither would catch a post-image accidentally "
            "tied to left-fold associativity. If it failed => SPEC-TOO-STRONG "
            "(over-fit to the fold DIRECTION)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-fresh-container. That case
    # established that the precondition admits a normal fresh input. This method
    # carries NO `require` clause (the pre-conditions region is empty), so nothing
    # could exclude a normal input and the classic "a normal input is admitted"
    # probe is vacuous. The analogue on this require-free TOTAL carrier is the
    # post-image being UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input
    # — a post-image no computation can hit there reads exactly like one every
    # computation hits, and no uniqueness rival would notice — so the case
    # discharges the post-image BY EVALUATION at that concrete point.
    #
    # AUDIT REPAIR (wave a8). The previous form of this case set
    # `"module": _BASE` — the frozen impl VERBATIM. That passes honestly and
    # tests nothing beyond what the gate's own frozen build already establishes:
    # it carries no claim about any concrete input, so a post-image degenerate at
    # the F2P shape would still have recorded `verified`. Replaced with a case
    # that keeps the frozen impl region byte-identical and adds, inside the
    # ELIDED `prove_correct` tactic body, a `have` discharging the SPEC-SIDE pair
    # at the F2P-shaped input by `decide`, then `clear`s it so the frozen
    # obligation closes verbatim from an unchanged context under the unchanged
    # frozen tactic script. Only the elided proof body differs, so the spec view
    # and the obligation survive byte-identical (measured: same_spec True,
    # variant_problems []).
    #
    # LIVENESS was measured with four real negative-control builds rather than
    # asserted — the `have` is a live obligation, not decoration. Each control
    # differs from the shipped case ONLY in the claimed right-hand side, and each
    # FAILS (exit 1) with "`decide` proved that the proposition ... is false":
    #   ([7, 5], true)      flag claim flipped              -> exit 1
    #   ([7, 5, 9], false)  as if the directory contributed  -> exit 1
    #   ([7, 7, 5], false)  as if the boundary path did      -> exit 1
    #   ([5], false)        as if the leading item were lost -> exit 1
    # The shipped claim `([7, 5], false)` builds at exit 0. So the discharge
    # TRACKS the post-image's actual value at that point and cannot be satisfied
    # by a mis-stated or unsatisfiable obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-walk",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl region UNTOUCHED; only the elided tactic body is retuned.
        "module": _swap(
            _BASE, _GOLD_PROOF,
            "prove_correct gatherEntries by\n"
            "  have hadmiss :\n"
            "      (((if true then [7] else []) ++ walkEntries\n"
            "          [{ boundary := true,  isFile := true,  yields := [7] },\n"
            "           { boundary := false, isFile := true,  yields := [5] },\n"
            "           { boundary := false, isFile := false, yields := [9] }]),\n"
            "        (false : Bool))\n"
            "        = ([7, 5], false) := by\n"
            "    decide\n"
            "  clear hadmiss\n"
            "  loom_solve <;> simp_all [foldl_walkEntries]"),
        "rationale": (
            "the input carries no `require`, so the enumeration is total over "
            "every (initMatches, initNode, entries) triple and the literal "
            "precondition-admits-a-normal-input probe has nothing to test. The "
            "residual PRECOND-TOO-STRONG analogue on a total domain is the "
            "post-image being UNSATISFIABLE or DEGENERATE at an F2P-shaped "
            "input, which this case discharges directly: at the shape the "
            "failing scenario has — a directory whose own initialization file "
            "matches the configured pattern (initMatches=true, initNode=7) and "
            "whose walk visits that same initialization file as a BOUNDARY path, "
            "one ordinary non-boundary regular file, and one directory — the "
            "two-clause post-image evaluates to the NON-DEGENERATE pair "
            "`([7, 5], false)`: the leading item for the matching initialization "
            "file, then the one qualifying file's contribution, with the boundary "
            "path and the directory each contributing nothing, and the load flag "
            "false. Discharged by EVALUATION as a `have`, then `clear`ed so the "
            "frozen obligation closes verbatim underneath from an unchanged "
            "context. This is the lane the three soundness positives cannot "
            "cover: they discharge a universally-quantified equation every "
            "instance of which could in principle be degenerate, while a rival "
            "only shows some impl FAILS. If the obligation could not be "
            "discharged at this concrete in-domain point => PRECOND-TOO-STRONG. "
            "The `have` is LIVE, measured with four negative controls that each "
            "differ only in the claimed right-hand side and each FAIL with "
            "\"`decide` proved that the proposition ... is false\": the flag "
            "flipped to true, the directory's items included, the boundary "
            "path's items included, and the leading item dropped."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary the three
    # input binders and PkgEntry's sub-fields (see footer BINDER / CLAUSE
    # COVERAGE). rival-eager-load attacks C1; the five structural rivals attack C2.
    # =====================================================================
    {
        "id": "rival-eager-load",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Gather the sequence correctly but report that the walk loaded
        # the directory's own initialization file (`out.2 = true`) — the pre-patch
        # behaviour where merely scanning a directory eagerly imported its own
        # initialization file. C2 holds; only C1 (the load flag) fails.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, true)\n"
            "    -- impl-end"),
        "refinement": (
            "this IS the pre-patch behaviour: the enumeration eagerly loads the "
            "directory's own initialization file as a side effect of scanning it "
            "for entries (the leading eager-mount the fix removes). Its faithful "
            "real patch keeps that eager load, so the failing test — a package "
            "whose initialization file raises on import — ERRORS during collection "
            "instead of completing cleanly, and the run does NOT return success. "
            "It does NOT resolve. This is the exact defect the fix corrects."),
        "rationale": (
            "REJECT from C1 (`out.2 = false`): the walk must report that it did "
            "NOT load the directory's own initialization file; a rival reporting "
            "`true` violates C1 at every input. C2 is kept correct so C1 is the "
            "sole failing clause. Refuted at `(true, 7, [])`. If it verified => "
            "SPEC-TOO-WEAK (admits the pre-patch eager-load bug)."),
        "witness": _witness("gatherEntriesTester true 7 []"),
    },
    {
        "id": "rival-drop-init-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # C2: never prepend the leading initialization-file item, even when it
        # matches (`initMatches = true`). Correct on the load flag and on the walk
        # of the entries, wrong on the prefix whenever initMatches holds.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "drops the leading item for the directory's own initialization file "
            "when it matches the configured pattern. A faithful patch of this "
            "shape would fail to collect the matching initialization file's node, "
            "so a package whose own initialization file legitimately carries tests "
            "would silently lose them — the collection-behaviour tests that pin "
            "exactly which nodes such a package yields would FAIL, so it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from C2 (`out.1 = (if initMatches then [initNode] else []) ++ "
            "walkEntries entries`): dropping the prefix diverges from the "
            "post-image whenever `initMatches` holds. C1 kept correct. Refuted at "
            "`(true, 3, [<non-boundary regular file yielding [5]>])` — a DISTINCT "
            "point exercising both the prefix and a real walk contribution. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            "gatherEntriesTester true 3 "
            "[{ boundary := false, isFile := true, yields := [5] }]"),
    },
    {
        "id": "rival-always-init-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # C2: ALWAYS prepend the init item, ignoring `initMatches`. Correct when
        # initMatches holds; wrong when it does not (emits a spurious leading item).
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "prepends the initialization-file item unconditionally, ignoring "
            "whether it matches the configured pattern. A faithful patch of this "
            "shape would yield a collector node for an initialization file that "
            "does not match the test-file pattern, collecting an item that should "
            "not exist — the collection-behaviour tests pinning which nodes a "
            "package yields would FAIL, so it does NOT resolve."),
        "rationale": (
            "REJECT from C2: the prefix is `if initMatches then [initNode] else []`, "
            "so emitting `[initNode]` when `initMatches` is false diverges from the "
            "post-image. C1 kept correct. Refuted at `(false, 8, [])` — the "
            "initMatches=false sub-domain, a DISTINCT binder value from the drop "
            "rival. If it verified => SPEC-TOO-WEAK (ignores `initMatches`)."),
        "witness": _witness("gatherEntriesTester false 8 []"),
    },
    {
        "id": "rival-ignore-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # C2: drop the boundary-skip predicate, so boundary paths (the directory's
        # own initialization file, or paths already inside an accounted-for
        # sub-directory) wrongly contribute their items to the walk.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if !e.isFile then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "drops the boundary-skip test, so a boundary path — in particular the "
            "directory's own initialization file, which the walk must NOT re-enter "
            "— contributes its items. A faithful patch of this shape would re-walk "
            "the package's own initialization file during scanning; in the failing "
            "repro that file raises on realization, so collection ERRORS instead "
            "of completing, and the run does NOT return success. It does NOT "
            "resolve."),
        "rationale": (
            "REJECT from C2 via `walkEntries` (a boundary entry contributes `[]`): "
            "including a boundary entry's `yields` diverges from the post-image. "
            "C1 kept correct. Refuted at `(false, 0, [<boundary regular file "
            "yielding [9]>])`, a DISTINCT point isolating the `boundary` sub-field. "
            "If it verified => SPEC-TOO-WEAK (ignores the skip predicate)."),
        "witness": _witness(
            "gatherEntriesTester false 0 "
            "[{ boundary := true, isFile := true, yields := [9] }]"),
    },
    {
        "id": "rival-ignore-isfile",
        "kind": "uniqueness",
        "expect": "reject",
        # C2: drop the regular-file test, so non-file paths (directories) wrongly
        # contribute their items to the walk.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "drops the regular-file test, so a directory path contributes items as "
            "if it were a file. A faithful patch of this shape would resolve a "
            "directory through the per-file resolution it is not meant for, "
            "yielding items that do not belong in this directory's own enumeration "
            "— the collection-behaviour tests pinning which nodes are yielded would "
            "FAIL, so it does NOT resolve."),
        "rationale": (
            "REJECT from C2 via `walkEntries` (a non-file entry contributes `[]`): "
            "including a directory entry's `yields` diverges from the post-image. "
            "C1 kept correct. Refuted at `(false, 1, [<non-boundary directory "
            "yielding [9]>])`, a DISTINCT point isolating the `isFile` sub-field. "
            "If it verified => SPEC-TOO-WEAK (ignores the regular-file test)."),
        "witness": _witness(
            "gatherEntriesTester false 1 "
            "[{ boundary := false, isFile := false, yields := [9] }]"),
    },
    {
        "id": "rival-drop-yields",
        "kind": "uniqueness",
        "expect": "reject",
        # C2: a qualifying (non-boundary regular file) entry contributes NOTHING —
        # the walk gathers no child items even from paths it should resolve.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc _ => acc)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "gathers nothing from the qualifying paths: a non-boundary regular "
            "file contributes none of the child items it resolves to. A faithful "
            "patch of this shape would collect no items from the files a directory "
            "contains, so a directory that DOES contain tests would silently "
            "collect nothing — the collection-behaviour tests pinning the yielded "
            "nodes would FAIL, so it does NOT resolve."),
        "rationale": (
            "REJECT from C2: a non-boundary regular file's contribution is its "
            "`yields` (per `walkEntries`), so contributing `[]` diverges from the "
            "post-image whenever such an entry has non-empty `yields`. C1 kept "
            "correct. Refuted at `(false, 2, [<non-boundary regular file yielding "
            "[9]>])`, a DISTINCT point isolating the `yields` sub-field — the entry "
            "qualifies (boundary false, isFile true) yet contributes nothing. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            "gatherEntriesTester false 2 "
            "[{ boundary := false, isFile := true, yields := [9] }]"),
    },

    # =====================================================================
    # ADDED BY AUDIT (wave a8), attack D. The five pre-existing C2 rivals each
    # break one structural decision TOTALLY (the prefix is always dropped, always
    # emitted, the guard is always ignored, the contribution is always empty), so
    # every one of them diverges from the post-image at the very first input that
    # reaches its broken decision. That leaves three facets of C2 unattacked, and
    # each of the three below is refuted at an input the six existing witnesses
    # never reach:
    #   * a SUB-DOMAIN near-miss on the prefix (correct on every non-empty entry
    #     list, wrong only when the walk visits nothing);
    #   * the MULTIPLICITY of a single file's contribution (correct whenever a
    #     qualifying file resolves to at most one item);
    #   * the ORDER of a single file's contribution (correct whenever a
    #     qualifying file resolves to at most one item).
    # The last two need a `yields` list of LENGTH >= 2, which no existing witness
    # has: all six ship singleton or empty `yields`. Each was measured to
    # discriminate with four real builds (rival 0 / gold 1) plus the flipped-claim
    # forgery pair (gold 0 / rival 1), i.e. gold's exit code tracks the claim.
    # =====================================================================
    {
        "id": "rival-prefix-only-when-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        # C2 SUB-DOMAIN near-miss: emit the leading initialization-file item only
        # when the walk also visited at least one path. Correct on every non-empty
        # entry list; wrong exactly when the directory carries a matching
        # initialization file and the walk visits nothing else.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches && !entries.isEmpty then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "makes the leading item for the directory's own initialization file "
            "conditional on the walk having visited something else, so a "
            "directory whose only test-bearing file IS its own matching "
            "initialization file yields nothing at all. A faithful patch of this "
            "shape would silently collect no nodes from exactly that directory "
            "shape, so the collection-behaviour tests pinning which nodes such a "
            "package yields would FAIL, and it does NOT resolve."),
        "rationale": (
            "REJECT from C2: the prefix is `if initMatches then [initNode] else "
            "[]` with NO dependence on `entries`, so gating it on a non-empty "
            "entry list diverges from the post-image at `entries = []`. C1 kept "
            "correct. This is the only rival that is a proper SUB-DOMAIN "
            "near-miss on the prefix — it AGREES with gold on every non-empty "
            "entry list, so drop-init-prefix's and always-init-prefix's witness "
            "points cannot catch it (drop-init-prefix's has a non-empty list; "
            "always-init-prefix's has initMatches=false, where this rival is "
            "correct). Refuted at `(true, 4, [])`, a DISTINCT input tuple. If it "
            "verified => SPEC-TOO-WEAK (the prefix would depend on the walk)."),
        "witness": _witness("gatherEntriesTester true 4 []"),
    },
    {
        "id": "rival-first-item-only",
        "kind": "uniqueness",
        "expect": "reject",
        # C2 MULTIPLICITY: a qualifying regular file contributes only the FIRST
        # of the child items it resolves to, dropping the rest.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc\n"
            "                    else acc ++ e.yields.take 1)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "keeps only the first child item each qualifying regular file "
            "resolves to and discards the rest. A faithful patch of this shape "
            "would collect a single node from every file that legitimately "
            "yields several, so a file carrying more than one test silently "
            "loses all but the first — the collection-behaviour tests pinning "
            "the full yielded sequence would FAIL, so it does NOT resolve."),
        "rationale": (
            "REJECT from C2 via `walkEntries` (a qualifying entry contributes "
            "ALL of its `yields`, not a prefix of them): truncating to the first "
            "item diverges from the post-image whenever some qualifying entry "
            "resolves to two or more items. C1 kept correct. Attacks the "
            "MULTIPLICITY of the per-file contribution, which drop-yields cannot "
            "reach — drop-yields discards the contribution entirely, so it is "
            "already wrong at a singleton `yields`, and every existing witness "
            "ships a singleton or empty `yields`. Refuted at `(false, 6, "
            "[<non-boundary regular file yielding [3, 4]>])`, the first witness "
            "in this battery whose `yields` has length 2. If it verified => "
            "SPEC-TOO-WEAK (C2 would pin only the first item per file)."),
        "witness": _witness(
            "gatherEntriesTester false 6 "
            "[{ boundary := false, isFile := true, yields := [3, 4] }]"),
    },
    {
        "id": "rival-reverse-file-items",
        "kind": "uniqueness",
        "expect": "reject",
        # C2 ORDER: a qualifying regular file contributes its child items in
        # REVERSED order. Same multiset, same length, same per-entry membership.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut collected : List Nat := []\n"
            "    if initMatches then\n"
            "      collected := collected ++ [initNode]\n"
            "    collected := entries.foldl\n"
            "      (fun acc e => if e.boundary || !e.isFile then acc\n"
            "                    else acc ++ e.yields.reverse)\n"
            "      collected\n"
            "    return (collected, false)\n"
            "    -- impl-end"),
        "refinement": (
            "emits each qualifying regular file's child items in reversed order. "
            "A faithful patch of this shape would report a file's tests "
            "back-to-front, so the collection-behaviour tests that pin the "
            "ORDERED sequence of nodes a directory yields would FAIL even though "
            "the set of nodes is right. It does NOT resolve."),
        "rationale": (
            "REJECT from C2, which is an equation on a LIST and therefore pins "
            "ORDER, not just membership or multiplicity: reversing a qualifying "
            "entry's contribution diverges from the post-image whenever that "
            "entry resolves to two or more distinct items. C1 kept correct. This "
            "is the only rival that keeps the multiset, the length and the "
            "per-entry attribution all correct, so it is the sharpest test that "
            "C2 is a list equation rather than a set/count proxy — a facet no "
            "existing rival probes, since all six agree with gold on ordering "
            "within a file. Refuted at `(true, 9, [<non-boundary regular file "
            "yielding [1, 2]>])`, a DISTINCT input with a length-2 `yields`. If "
            "it verified => SPEC-TOO-WEAK (C2 would not pin intra-file order)."),
        "witness": _witness(
            "gatherEntriesTester true 9 "
            "[{ boundary := false, isFile := true, yields := [1, 2] }]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery has 8 SPEC cases (2 soundness positives, 1 admissibility,
# 5 uniqueness rivals — one of which is a divergence rival) plus an empty AXIOM
# lane, contracting TWO functions of a two-phase lazy-load state machine:
#   * access_object       — the exactly-one-lazy-load transition over a mutable
#                           Container (loaded : bool, load_count : int);
#   * enumerate_children  — discovery loads nothing (load_count / loaded frozen).
# This Lean-family bundle models the NARROWER discovery/enumeration core alone
# (`gatherEntries`): one `method`, one `prove_correct`. The "discovery loads
# nothing" guarantee carries across as C1 (`out.2 = false`), now a single Boolean
# result component; the produced-sequence structure is pinned by C2, a clause with
# no direct nagini counterpart (nagini's enumerate_children pinned only the load
# counter, not the yielded sequence). The access_object phase and its load_count
# counter have NO counterpart here. Every sibling case is accounted for below.
#
#   sibling case (nagini)       -> here                          disposition
#   ---------------------------------------------------------------------------
#   admiss-fresh-container      -> admiss-f2p-shaped-walk        RE-AIMED (a8)
#   pos-access-reshape          -> (none)                        NOT MODELED (access fn)
#   pos-enum-readonly           -> pos-control-direct            RE-EXPRESSED
#                                  + pos-control-prefix-local     ADDED (2nd shape)
#                                  + pos-control-foldr            ADDED BY AUDIT (3rd shape)
#   enum-frame-write            -> rival-eager-load              PORTED (central bug)
#   enum-diverge-loop           -> (none)                        UNSHIPPABLE (no witness)
#   enum-status-flip            -> (folded into rival-eager-load) COLLAPSED
#   access-partial-fresh-noop   -> (none)                        NOT MODELED (access fn)
#   access-double-load          -> (none)                        NOT MODELED (access fn)
#   access-plus-two             -> (none)                        NOT MODELED (access fn)
#   AXIOM_TESTS ([])            -> (none)                        DROPPED (G-AX lane)
#   + rival-drop-init-prefix / rival-always-init-prefix /
#     rival-ignore-boundary / rival-ignore-isfile /
#     rival-drop-yields                                          ADDED (C2 coverage)
#   + rival-prefix-only-when-nonempty / rival-first-item-only /
#     rival-reverse-file-items                                   ADDED BY AUDIT a8
#
# 13 velvet SPEC cases: 3 soundness, 1 admissibility, 9 uniqueness — the nine
# uniqueness rivals being rival-eager-load (attacking C1) plus eight C2 rivals.
# (Was 9 before the a7 audit added pos-control-foldr, and 10 before the a8 audit
# added the three C2 facet rivals and rebuilt the admissibility case.)
#
# RE-AIMED (admiss-fresh-container -> admiss-f2p-shaped-walk): the nagini case
#   shows the precondition admits a normal fresh Container. This method has NO
#   `require` (the pre-conditions region is empty), so that probe is vacuous;
#   re-aimed at the residual total-domain risk — the post-image being
#   UNSATISFIABLE or DEGENERATE at an F2P-shaped input. AUDIT a8 REPAIR: the
#   previous form of this case shipped the frozen impl VERBATIM
#   (`"module": _BASE`), which passes honestly but carries no claim about any
#   concrete input, so it duplicated the gate's own frozen build and could not
#   have detected a degenerate post-image. It now discharges the two-clause
#   post-image at the F2P-shaped input BY EVALUATION inside the elided tactic
#   body, `clear`s the `have`, and closes the frozen obligation verbatim
#   underneath — with four measured negative controls establishing the discharge
#   is live (see the case's own comment).
# RE-EXPRESSED / ADDED (pos-enum-readonly -> pos-control-direct +
#   pos-control-prefix-local + pos-control-foldr): the nagini honest control is a
#   discovery body that reads but performs no load. On this carrier the loop-free
#   honest impl is `return (<C2 RHS>, false)` (pos-control-direct, reproved under
#   `loom_solve`), and a second correct reshape stages the init prefix into a
#   typed local while keeping the fold and the frozen proof
#   (pos-control-prefix-local) — guarding the impl against being over-fit to the
#   inline-prefix form. The audit added a THIRD shape, pos-control-foldr, which
#   reverses the fold DIRECTION (right fold prepending each contribution): the
#   frozen `foldl_walkEntries` lemma does not apply to it, so it is the only
#   positive that would catch a post-image accidentally tied to left-fold
#   associativity. All three verified with real builds.
# PORTED (enum-frame-write -> rival-eager-load): the nagini value-frame rival is
#   the eager load during discovery (the pre-patch leading mount), rejected by the
#   value-level frame clause. It ports directly and is the headline reject here,
#   refuted by C1 (`out.2 = false`). Its faithful real patch keeps the eager load,
#   so the failing test errors during collection and does not resolve.
# COLLAPSED (enum-status-flip): the nagini rival flips `loaded` WITHOUT bumping
#   `load_count` — a distinction that exists only because nagini splits the load
#   event into TWO fields (a status bool and a counter). On this carrier the load
#   event is a SINGLE Boolean result component `out.2`, so "flip the status" and
#   "record a load" are the same act; the only C1 violation is `out.2 = true`,
#   already exercised by rival-eager-load. No separate rival is possible or
#   meaningful — this is carrier collapse, not an omission.
# UNSHIPPABLE (enum-diverge-loop): the nagini divergence rival is guarded by
#   `Requires(MustTerminate(2))`. This bundle sets `loom.semantics.termination
#   "total"`, as do all 500 velvet bundles, so a diverging rival is REJECTED
#   here and there is no `partial` cohort for which it would be a known spec
#   hole (an earlier revision of this line asserted one). Under `total` the class is in
#   principle shippable, so the a8 audit tried to LAND it rather than agreeing
#   with the prior disposition, and measured three things:
#     (a) a diverging body IS writable here and stays inside `variant_scope`
#         (`while spin do spin := true` prefixed to the frozen body); it is
#         rejected, `error: Decreasing annotations are required in total
#         correctness semantics`, exit 1. An earlier draft of this file claimed "a
#         non-terminating body cannot even be written on this straight-line
#         `foldl` carrier"; the a7 audit refuted that and the a8 audit reproduced
#         the refutation.
#     (b) the obligation is not a linter formality on this cell: a NON-DECREASING
#         measure is rejected on the measure's OWN goal. A `while 0 < 1` loop with
#         `decreasing (0 : Nat)` returning an unambiguously wrong answer is
#         REJECTED, exit 1, `unsolved goals / case «decreasing_1: (0 : Nat)» ⊢
#         False`, and the live-variable form (`while q > 0 / invariant 0 <= q /
#         done_with q = 0 / decreasing q`, body `q := q`) is REJECTED on `case
#         «decreasing_1: q»` with residual `q < q`. An earlier revision called
#         this a corpus-wide residual hole that merely "does not reach here";
#         there is no such hole, since it does not reproduce anywhere it was
#         rebuilt.
#     (c) but NO witness can discriminate, so it cannot ship. The `decide`-style
#         witness against the diverging rival fails with ``Tactic `decide` failed
#         ... its `Decidable` instance ... did not reduce to `isTrue` or
#         `isFalse``` — the gate's own `_STUCK_REDUCTION` screen — and fails with
#         the BYTE-IDENTICAL message against a diverging rival returning the
#         WRONG answer. The diverging loop is the `Classical.choice` term the
#         kernel cannot unfold, so the witness's exit code carries no information
#         on either side; the case would land `witness-undecided` (inconclusive
#         => gate error), never a recorded refutation. A `witness_reference`
#         cannot rescue it either: the reference replaces the GOLD side, and the
#         side that is stuck here is the RIVAL side, which must succeed.
#   So: nothing shippable, and NO known hole to record — the spec does reject the
#   class (a) and (b); the battery simply cannot attest to it through the witness
#   channel this gate requires. (Had this cell been `partial`, the disposition
#   would instead be a recorded known hole: a rival the spec vacuously ADMITS.)
# NOT MODELED (pos-access-reshape, access-partial-fresh-noop, access-double-load,
#   access-plus-two): the nagini `access_object` phase — the exactly-one-lazy-load
#   transition over `loaded`/`load_count` — is NOT part of this bundle's modeled
#   carrier. The Lean-family bundle models only the discovery/enumeration core
#   (`gatherEntries`); there is one `method`/one `prove_correct`, and the access
#   transition and its `load_count` counter have no counterpart here. This is
#   carrier narrowing (the porting map's "most nagini cases attached to an
#   unmodeled behaviour have no counterpart"), NOT an omission for difficulty:
#   fabricating an access rival would require a second method this bundle does not
#   contract, and a `load_count` this bundle does not carry.
# ADDED (rival-drop-init-prefix, rival-always-init-prefix, rival-ignore-boundary,
#   rival-ignore-isfile, rival-drop-yields): C2 (`out.1 = ...`) is a clause this
#   velvet bundle models that the nagini enumerate_children spec does not (nagini
#   pinned only the load counter/status, never the yielded sequence). C2 is an
#   independent top-level clause and MUST be attacked; each rival breaks one
#   structural decision of the walk — the prefix's presence (drop-init-prefix),
#   its dependence on `initMatches` (always-init-prefix), the boundary-skip
#   predicate (ignore-boundary), the regular-file test (ignore-isfile), and the
#   per-file contribution (drop-yields). Each is a real C2 divergence with a
#   machine-checked witness at a distinct input, not fabricated wrongness.
# ADDED BY AUDIT a8 (rival-prefix-only-when-nonempty, rival-first-item-only,
#   rival-reverse-file-items): all five rivals above break their structural
#   decision TOTALLY, so each is already wrong at the first input reaching it.
#   That left three C2 facets unattacked, and each new rival is a proper
#   near-miss that AGREES with gold across the sub-domain the existing witnesses
#   probe:
#     * prefix INDEPENDENCE from `entries` — gate the leading item on the walk
#       having visited something. Correct on every non-empty entry list, so
#       drop-init-prefix's witness (non-empty) and always-init-prefix's
#       (initMatches=false) both miss it; refuted only at `entries = []` with
#       initMatches=true.
#     * per-file MULTIPLICITY — contribute only the first item a qualifying file
#       resolves to. drop-yields cannot reach this: it discards the contribution
#       entirely and so is already wrong at a singleton `yields`.
#     * per-file ORDER — reverse a qualifying file's contribution, keeping the
#       multiset, the length and the per-entry attribution intact. The sharpest
#       test that C2 is a LIST equation and not a set/count proxy.
#   The last two require a `yields` of length >= 2, which no pre-a8 witness had
#   (all six ship empty or singleton `yields`) — so this is a genuine widening of
#   the probed input space, not two more spellings of an existing point. Each was
#   measured with four real builds: witness against the rival (exit 0) and gold
#   (exit 1), plus the flipped-claim forgery against gold (exit 0) and the rival
#   (exit 1), i.e. gold's exit code TRACKS the claim rather than being constant.
# DROPPED (AXIOM_TESTS): the nagini file's axiom lane is already empty (the load
#   primitive is modeled deeply, validated out-of-band by G-AX). This bundle
#   likewise declares no axioms and no deep-model references. Nothing to probe,
#   and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE. The obligation has THREE input binders
#   (`initMatches`, `initNode`, `entries`, the last with sub-fields `boundary` /
#   `isFile` / `yields`) and TWO independent top-level clauses. Both clauses are
#   DEFENDED (three positives verify, and the admissibility case discharges the
#   two-clause post-image by evaluation at an F2P-shaped input) and ATTACKED:
#   * C1 (`out.2 = false`) by rival-eager-load;
#   * C2 (`out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries`)
#     by drop-init-prefix / always-init-prefix / prefix-only-when-nonempty (the
#     prefix, its `initMatches` dependence, and its INDEPENDENCE from `entries`),
#     ignore-boundary / ignore-isfile (the `walkEntries` guard over `boundary` /
#     `isFile`), and drop-yields / first-item-only / reverse-file-items (the
#     per-file contribution's presence, MULTIPLICITY and ORDER).
#   The nine reject witnesses probe NINE DISTINCT input points (pts=9):
#     (true,  7, [])                              rival-eager-load     (C1)
#     (true,  3, [b=F,f=T,y=[5]])                 drop-init-prefix     (C2 prefix + walk)
#     (false, 8, [])                              always-init-prefix   (C2 prefix, im=F)
#     (false, 0, [b=T,f=T,y=[9]])                 ignore-boundary      (C2 boundary)
#     (false, 1, [b=F,f=F,y=[9]])                 ignore-isfile        (C2 isFile)
#     (false, 2, [b=F,f=T,y=[9]])                 drop-yields          (C2 yields present)
#     (true,  4, [])                              prefix-only-nonempty (C2 prefix vs entries)
#     (false, 6, [b=F,f=T,y=[3,4]])               first-item-only      (C2 multiplicity)
#     (true,  9, [b=F,f=T,y=[1,2]])               reverse-file-items   (C2 order)
#   `initMatches` is varied over {true, false}; `initNode` over
#   {7,3,8,0,1,2,4,6,9}; `entries` over the empty list, singletons whose
#   `boundary`/`isFile` sub-fields each take BOTH values, and — added by the a8
#   audit — singletons whose `yields` has LENGTH 2, which is what makes the
#   multiplicity and order facets of C2 reachable at all. The variation is
#   MEANINGFUL rather than two spellings of one point: each rival's verdict
#   genuinely flips on the binder its witness moves (drop-init-prefix needs
#   initMatches=true, always-init-prefix needs false, prefix-only-nonempty needs
#   entries=[] AND initMatches=true, and first-item-only / reverse-file-items are
#   both CORRECT at every singleton `yields`, so nothing shorter refutes them).
#   No binder is held fixed by every witness, and no two rivals share an input
#   tuple. Each witness was SEEN to discriminate: it ELABORATES against the rival
#   (exit 0) and FAILS against the frozen solution (exit 1), confirmed with two
#   real builds each. Each was additionally FORGERY-tested (the a8 audit): the
#   same claim with `= false` flipped to `= true` BUILDS against the frozen
#   solution (exit 0) and FAILS against the rival (exit 1) — the exact inversion —
#   so gold's exit code carries information about the CLAIM and not merely about
#   the file. Every gold-side failure is a plain evaluation, ``Tactic `decide`
#   proved that the proposition <the concrete tester call> = false is false``; no
#   witness hits a stuck reduction, a missing `Decidable` instance, a
#   unification failure on an unreduced loop term, or a type error. No witness
#   binds a hypothesis (the carrier is fully transparent — all fields are concrete
#   Bool/Nat/List Nat literals), so there is no joint-satisfiability obligation.
#   No sorry/admit/native_decide/axiom appears in any witness.
AXIOM_TESTS = []
