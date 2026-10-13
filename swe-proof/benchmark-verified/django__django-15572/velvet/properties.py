"""properties.py — G-PBT falsification battery for django__django-15572 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
each ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE. TWO contracted methods over a finite list of directory
entries, each entry a character sequence:

    collectConfiguredDirs (entries)  ensures out = collectConfigured entries
    collectLoaderDirs     (entries)  ensures out = collectLoader entries

``collectConfigured`` keeps an entry iff it is NON-EMPTY, normalises it, and
concatenates in order; ``collectLoader`` keeps an entry iff it is non-empty AND
not already owned by the framework. Both are front-recursive folds spelled out
in the ``pure`` region; ``entries`` is the sole input binder of each. The
load-bearing content is the EMPTINESS SKIP: an empty entry must contribute
nothing to either result — the behaviour the failing scenario demands (an empty
directory entry that must not expand into a spurious watched location). At the
loader site the emptiness test is INDEPENDENT of the ownership test (checked on
its own), which the second obligation's clauses pin.

CARRIER NOTE (decisive for the reject lane). The ``axioms`` region declares two
OPAQUE free functions the collections defer to: ``normalizePath`` (the per-entry
normaliser) and ``isFrameworkOwned`` (the ownership predicate). Neither has an
asserted contract, so no literal input COMPUTES them. But the reject lane is
still fully expressible on this carrier, two ways:

  * The configured obligation combines the opaque normaliser only under a
    TRANSPARENT emptiness filter. A rival that keeps an empty entry emits an
    extra ``normalizePath`` element, and the divergence is a LENGTH mismatch
    that needs no knowledge of ``normalizePath``'s value (``[normalizePath e]``
    is non-empty for any ``e``). So the configured rivals are refuted at literal
    inputs.
  * The loader obligation additionally keys on the opaque ``isFrameworkOwned``.
    Its rivals CONDITION on that opaque at one concrete entry — assuming only
    ``isFrameworkOwned [] = false`` (an empty entry is not framework-owned) or
    ``isFrameworkOwned ['a'] = true`` (a present entry that IS owned) — which is
    exactly the sub-domain where the rival diverges from the spec. Each witness
    binds ONE hypothesis about ONE opaque term, so the assumptions are jointly
    satisfiable (the gate's consistency probe confirms neither derives False).

WITNESS MECHANICS. The spec is a ``method`` contract, so a witness reaches it
through the extracted program: ``(collectConfiguredDirs xs).run`` is the
program's ``DivM`` result, and the refutation states it is ``≠ DivM.res
(collect… xs)`` — the program's output disagrees with the specified value at a
concrete ``xs``. Every reject rival is reshaped into a LOOP-FREE closed form, so
its ``.run`` reduces under ``simp [… , NonDetT.run, pure]`` and the witness
elaborates against the rival.

THE FROZEN SOLUTION CANNOT SERVE AS THE REFUTATION SUBJECT HERE, and an earlier
revision of this battery was wrong to treat its red build as the discriminator.
The frozen program's ``while`` fixpoint does not reduce under the kernel, so a
witness stated over it fails for a SYNTACTIC reason that is independent of the
claim's truth. Measured with ``scripts/lean_verify.sh``: the claim
``(collectConfiguredDirs [[], ['a']]).run = DivM.res (collectConfigured
[[], ['a']])`` — which is TRUE of the frozen solution, being exactly its own
first ``ensures`` at that input — ALSO fails against the frozen solution (exit
1, ``unsolved goals`` over an unreduced ``forIn`` term). A subject on which a
true claim and its negation both fail discriminates nothing, and the gate's
``_STUCK_REDUCTION`` screen does not catch it because these witnesses close by
``simp``/``congrArg`` rather than by ``decide``, so the give-away message never
appears.

So each reject case declares a ``witness_reference`` (``_REFERENCE`` below): a
LOOP-FREE impl of the same frozen spec that VERIFIES (``return (collectConfigured
entries)`` / ``return (collectLoader entries)``, whose ``ensures`` are then closed
by ``loom_solve <;> simp_all``). Its ``.run`` reduces, so a witness fails there by
real refutation — the goal state is ``heq : True ⊢ False``, i.e. the reference's
output genuinely EQUALS the specified value at that input, which is what "the
spec is satisfied here" looks like. That is sound for the reason the gate
documents: an impl the verifier ACCEPTS cannot violate its own spec, so a genuine
witness must still fail against it. The gate re-checks both facts (shares the
frozen spec; verifies) before using it, so nothing here is trusted.

(Measured per case, ``scripts/lean_verify.sh``: witness vs rival exit 0; witness
vs the reference exit 1 with ``heq : True ⊢ False``; the two conditioning
witnesses' consistency probes exit 1, i.e. no ``False`` follows from their
hypotheses. Each rival also fails full verification.) No ``sorry`` / ``admit`` /
``native_decide`` / ``axiom``.

FRAME / PERMISSION-MUTATION — VACUOUS on this backend (see footer).
AXIOM_TESTS — dropped (the axiom lane is G-AX's job; here both callees are
opaque with no asserted contract, so there is nothing for G-AX to validate).

DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and a
diverging rival is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (2 loops here, measures ``i``). A rival that loops without a
measure is refused outright (``Decreasing annotations are required in total
correctness semantics``), and a rival that supplies a CONSTANT measure to dodge
that is refused on the measure's own goal (``case «decreasing_1: spin» ... ⊢
spin < spin``), re-measured on this bundle with a real build. Divergence
therefore does not discharge the ``ensures`` clauses vacuously. It is still not
shipped as a G-PBT reject case, and the reason is the witness contract rather
than a spec weakness. A reject case must carry a witness that ELABORATES
against the rival, and neither diverging shape gets past that. With NO measure
the descent obligation fails at the ``method`` itself, ahead of any appended
tester, and the witness file retains the ``method`` (it strips only the
``prove_correct`` obligations), so the rival module does not compile at all. With
a measure that does not decrease the refusal moves to the ``prove_correct`` site,
which IS stripped, so that module does elaborate; but the rival's post-image is
then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise to a
value a concrete-input tester can decide. Either way the gate returns
``witness-unproven``, an inconclusive outcome.
Measured through the gate's own ``_check_witness``, even
``example : True := trivial`` comes back ``witness-unproven`` on this rival,
which is an INCONCLUSIVE outcome and would fail the whole battery rather than
pass a case. That is the right behavior: a diverging impl has no output at any
input, so there is no value for a witness to disagree with, and its rejection
is a judgement of the termination obligation rather than a postcondition
violation at a point. Recorded as REJECTED-BY-SPEC and not expressible as a
witnessed case, which is neither a spec hole nor a battery gap.
"""
from pathlib import Path

INSTANCE = "django__django-15572"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside an impl region (between -- impl-start and
# -- impl-end) or inside a prove_correct tactic body, and each is unique in
# Solution.lean (both facts asserted at load time by _swap). Editing only these
# keeps markers.same_spec True and every prove_correct statement byte-identical
# (the spec view elides both regions). The two methods share the SAME loop
# shape; the fold/guard names (collectConfigured/keepConfigured vs
# collectLoader/keepLoader) are what make each anchor unique.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the CONFIGURED method: the backward accumulating
# loop. Reject rivals replace this with a loop-free closed form (so their .run
# reduces under simp while gold's loop does not).
_IMPL_C = """    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectConfigured (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if keepConfigured e then [normalizePath e] else []) ++ result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL_C) == 1, "collectConfiguredDirs impl region drifted"

# The WHOLE executable body of the LOADER method.
_IMPL_L = """    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectLoader (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if keepLoader e then [normalizePath e] else []) ++ result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL_L) == 1, "collectLoaderDirs impl region drifted"

# The three per-iteration loop lines of each method; a positive control may
# reshape them while keeping the loop and the invariant, so the frozen proof
# still closes.
_LOOP_C = """      let e := entries[i - 1]!
      result := (if keepConfigured e then [normalizePath e] else []) ++ result
      i := i - 1"""
assert _BASE.count(_LOOP_C) == 1, "configured loop body drifted"

_LOOP_L = """      let e := entries[i - 1]!
      result := (if keepLoader e then [normalizePath e] else []) ++ result
      i := i - 1"""
assert _BASE.count(_LOOP_L) == 1, "loader loop body drifted"

# The head of the CONFIGURED impl region (impl-start marker + first two lets +
# the two invariants that name collectConfigured); unique because of the
# collectConfigured invariant. An in-region assert prepended right after the
# marker is discharged without disturbing the method's own obligation.
_HEAD_C = """    -- impl-start
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectConfigured (entries.drop i)"""
assert _BASE.count(_HEAD_C) == 1, "configured impl head drifted"

# The head of the LOADER impl region — the mirror of _HEAD_C, unique because of
# the collectLoader invariant. Same use: an in-region assert prepended right
# after the marker is discharged without disturbing the method's obligation.
_HEAD_L = """    -- impl-start
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectLoader (entries.drop i)"""
assert _BASE.count(_HEAD_L) == 1, "loader impl head drifted"

# The FULL frozen proof body of the configured method.
_PROOF_C = """prove_correct collectConfiguredDirs by
  loom_solve
  rw [collectConfigured_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectConfigured (entries.drop i)›]"""
assert _BASE.count(_PROOF_C) == 1, "configured prove_correct body drifted"

# The FULL frozen proof body of the loader method.
_PROOF_L = """prove_correct collectLoaderDirs by
  loom_solve
  rw [collectLoader_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectLoader (entries.drop i)›]"""
assert _BASE.count(_PROOF_L) == 1, "loader prove_correct body drifted"


# ---------------------------------------------------------------------------
# THE REFUTATION SUBJECT (see WITNESS MECHANICS). Both methods return their
# specified value DIRECTLY — no loop at all — so the extracted program's `.run`
# REDUCES and a witness stated over it is decided on its merits instead of
# getting stuck on an unreduced `forIn`. Each `ensures` is then closed by
# `loom_solve <;> simp_all [<the fold>]`.
#
# This is loop-free, not spec-weakening: the pure folds `collectConfigured` /
# `collectLoader` are TRANSPARENT `def`s over the method's own `entries` binder
# (spelled out in the frozen `pure` region), not an opaque answer key, so
# returning one is an honest correct impl rather than an oracle echo — every
# wrong result still fails clause 1 at some input, which is exactly what the four
# rivals below demonstrate against this same subject. It is region surgery like
# every other case (impl regions + `prove_correct` bodies only), so it shares the
# frozen spec byte-for-byte; the gate independently re-checks that AND that it
# verifies before refuting any witness against it.
_REFERENCE = _swap(
    _swap(
        _swap(
            _swap(_BASE, _IMPL_C, "    return (collectConfigured entries)"),
            _IMPL_L, "    return (collectLoader entries)"),
        _PROOF_C,
        "prove_correct collectConfiguredDirs by\n"
        "  loom_solve <;> simp_all [collectConfigured]"),
    _PROOF_L,
    "prove_correct collectLoaderDirs by\n"
    "  loom_solve <;> simp_all [collectLoader]")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Port the nagini positive
    # reshapes ("a faithful, structurally-different correct impl is not
    # rejected"): hoist the per-entry keep-decision into a local, keeping the
    # backward loop and the front-recursive invariant so the frozen proof still
    # closes untouched. One per contracted obligation.
    # =====================================================================
    {
        "id": "pos-configured-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Bind the configured keep-decision to a local `keep` before the branch.
        # Same value flow element-for-element; the loop and invariant are
        # unchanged, so the frozen configured proof closes verbatim.
        "module": _swap(
            _BASE, _LOOP_C,
            "      let e := entries[i - 1]!\n"
            "      let keep := keepConfigured e\n"
            "      result := (if keep then [normalizePath e] else []) ++ result\n"
            "      i := i - 1"),
        "rationale": "binding the configured keep-decision to a local before the "
                     "branch computes the same collection element-for-element, with "
                     "the loop and invariant unchanged, so the frozen proof closes "
                     "and `out = collectConfigured entries` still holds; a correct "
                     "reshape MUST verify, else SPEC-TOO-STRONG. Defends the "
                     "collectConfiguredDirs obligation.",
    },
    {
        "id": "pos-loader-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Same reshape at the loader site: bind the loader keep-decision to a
        # local. Frozen loader proof closes verbatim.
        "module": _swap(
            _BASE, _LOOP_L,
            "      let e := entries[i - 1]!\n"
            "      let keep := keepLoader e\n"
            "      result := (if keep then [normalizePath e] else []) ++ result\n"
            "      i := i - 1"),
        "rationale": "binding the loader keep-decision to a local computes the same "
                     "collection element-for-element, loop and invariant unchanged, "
                     "so the frozen proof closes and `out = collectLoader entries` "
                     "still holds; a correct reshape MUST verify, else "
                     "SPEC-TOO-STRONG. Defends the collectLoaderDirs obligation.",
    },

    # =====================================================================
    # ADMISSIBILITY — the methods carry NO `require` clause (the pre-conditions
    # region is empty), so the domain is total and the nagini "a normal
    # F2P-shaped input satisfies the precondition" probe is degenerate (every
    # input is in-domain). It is RE-AIMED at the residual total-domain risk — a
    # DEGENERATE obligation — via a live in-region assert pinning BOTH sides of
    # the emptiness skip at an F2P-shaped point: an empty entry contributes
    # nothing AND a present entry contributes its normalisation. The surrounding
    # impl is kept verbatim so the method's own obligation still discharges; the
    # assert is live (a false claim leaves an unsolved goal), and the proof's
    # alternation gains one arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-emptiness-skip-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _HEAD_C,
                "    -- impl-start\n"
                "    assert (with_name_prefix `assert\n"
                "      (collectConfigured [([] : List Char), ['a']] = [normalizePath ['a']]))\n"
                "    let mut result : List (List Char) := []\n"
                "    let mut i := entries.length\n"
                "    while i > 0\n"
                "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
                "      invariant result = collectConfigured (entries.drop i)"),
            _PROOF_C,
            "prove_correct collectConfiguredDirs by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | (rw [collectConfigured_drop_step entries i (by omega) (by omega)];\n"
            "       rw [‹result = collectConfigured (entries.drop i)›])\n"
            "    | (simp [collectConfigured, keepConfigured])"),
        "rationale": "the obligation is non-degenerate at the F2P-shaped point: the "
                     "in-region assert pins BOTH sides of the emptiness skip — an "
                     "empty entry contributes nothing and a present entry contributes "
                     "its normalisation (collectConfigured [[], ['a']] = "
                     "[normalizePath ['a']]) — so the modeled behaviour actually "
                     "fires at the interesting cell. The impl is kept verbatim so "
                     "`out = collectConfigured entries` still discharges; the assert "
                     "is live (a false claim would leave an unsolved goal). "
                     "(Sibling: admiss-direct, re-aimed — no precondition surface.)",
    },
    {
        # ADDED UNDER AUDIT. The case above grounds only the CONFIGURED
        # obligation, so the loader obligation carried no admissibility probe at
        # all — and it is the loader obligation whose emptiness test has to be
        # INDEPENDENT of the ownership test, which is the strictly harder claim
        # (the configured site has no second conjunct to be entangled with).
        # This asserts exactly that independence at the F2P-shaped point: the
        # empty head contributes nothing to the loader collection WITHOUT the
        # ownership predicate being decided anywhere, i.e. prepending an empty
        # entry leaves the collection unchanged. A degenerate loader obligation —
        # one whose emptiness skip only fired because the ownership test happened
        # to exclude the entry — could not discharge this.
        "id": "admiss-loader-emptiness-independent",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _HEAD_L,
                "    -- impl-start\n"
                "    assert (with_name_prefix `assert\n"
                "      (collectLoader [([] : List Char), ['a']]\n"
                "        = collectLoader [(['a'] : List Char)]))\n"
                "    let mut result : List (List Char) := []\n"
                "    let mut i := entries.length\n"
                "    while i > 0\n"
                "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
                "      invariant result = collectLoader (entries.drop i)"),
            _PROOF_L,
            "prove_correct collectLoaderDirs by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | (rw [collectLoader_drop_step entries i (by omega) (by omega)];\n"
            "       rw [‹result = collectLoader (entries.drop i)›])\n"
            "    | (simp [collectLoader, keepLoader])"),
        "rationale": "the LOADER obligation is non-degenerate at the F2P-shaped "
                     "point, and specifically its emptiness test is INDEPENDENT of "
                     "the ownership test: the in-region assert pins that prepending "
                     "an empty entry leaves the loader collection unchanged "
                     "(collectLoader [[], ['a']] = collectLoader [['a']]) — a claim "
                     "that holds for ANY value of the opaque ownership predicate at "
                     "['a'], so the empty entry is dropped on emptiness alone and "
                     "not because ownership happened to exclude it. The impl is kept "
                     "verbatim so `out = collectLoader entries` still discharges. "
                     "LIVE, and measured: weakening the claim to "
                     "`collectLoader [[], ['a']] = collectLoader [[]]` (which asserts "
                     "the empty entry contributes and the present one does not) leaves "
                     "the unsolved goal `isFrameworkOwned ['a'] = true` — i.e. a false "
                     "claim here is NOT provable, so the assert really does carry the "
                     "independence content. Companion to "
                     "admiss-emptiness-skip-grounded, which grounds only the "
                     "configured obligation.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its .run reduces)
    # with a machine-checked refutation witness at a concrete input, plus the
    # refinement argument that its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================

    # ---- configured: drop the emptiness guard (the pre-patch site #1) ----
    {
        "id": "reject-configured-unguarded",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep EVERY entry (normalise all, no emptiness filter) — the pre-patch
        # behaviour at the first collection site. Correct on lists with no empty
        # entry; wrong exactly on a list containing an empty entry.
        "module": _swap(_BASE, _IMPL_C, "    return (entries.map normalizePath)"),
        "refinement": "this is the pre-patch site #1 behaviour: the unguarded "
                      "per-entry expansion with no emptiness filter. On a "
                      "configuration carrying an empty directory entry it emits the "
                      "normalisation of the empty entry (which expands to the project "
                      "base) where the fix emits nothing, so the watched set is "
                      "non-empty where it must be empty — exactly the failing "
                      "scenario. It would NOT resolve (G-DIFF).",
        "rationale": "REJECT from `out = collectConfigured entries`: on an entry "
                     "list containing an empty entry the rival keeps it while the "
                     "spec drops it, so the two lists differ in LENGTH. Refuted at "
                     "[[], ['a']]: gold = [normalizePath ['a']] (len 1), rival = "
                     "[normalizePath [], normalizePath ['a']] (len 2); the length "
                     "mismatch needs no knowledge of the opaque normaliser.",
        # Refuted against _REFERENCE, not the loop-bearing frozen impl: see
        # WITNESS MECHANICS. `intro heq` FIRST, then reduce the rival's `.run`
        # and the fold together — against the reference the two sides converge
        # and `heq` collapses to `True`, leaving `⊢ False` unprovable (the
        # semantic signal that the spec IS satisfied there); against the rival
        # the lengths differ (1 vs 2) and `simp` closes it.
        "witness":
            "example : (collectConfiguredDirs [([] : List Char), ['a']]).run\n"
            "    ≠ DivM.res (collectConfigured [([] : List Char), ['a']]) := by\n"
            "  intro heq\n"
            "  simp [collectConfiguredDirs, NonDetT.run, pure, collectConfigured,\n"
            "    keepConfigured] at heq\n",
        "witness_reference": _REFERENCE,
    },

    # ---- configured: INVERTED emptiness guard ----
    {
        "id": "reject-configured-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard the wrong way: keep an entry iff it IS empty; drop present
        # entries. Correct only on the degenerate all-empty list; wrong on any
        # present entry.
        "module": _swap(
            _BASE, _IMPL_C,
            "    return (entries.filterMap (fun e => if keepConfigured e then none else some (normalizePath e)))"),
        "refinement": "inverting the emptiness test keeps the empty entry and drops "
                      "every real directory, so the watched set omits the configured "
                      "template directories entirely; the pre-existing behaviour that "
                      "expects the configured directories to be watched would break. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = collectConfigured entries`: on a present "
                     "entry the spec keeps it (`keepConfigured ['a'] = true`) while "
                     "the rival drops it. Refuted at [['a']]: gold = "
                     "[normalizePath ['a']] (len 1), rival = [] (len 0). Separated "
                     "from reject-configured-unguarded, which AGREES with gold at "
                     "[['a']] — this is the opposite side of the guard.",
        # Refuted against _REFERENCE (WITNESS MECHANICS). At [['a']] the rival
        # returns [] where the spec returns [normalizePath ['a']].
        "witness":
            "example : (collectConfiguredDirs [['a']]).run\n"
            "    ≠ DivM.res (collectConfigured [['a']]) := by\n"
            "  intro heq\n"
            "  simp [collectConfiguredDirs, NonDetT.run, pure, collectConfigured,\n"
            "    keepConfigured] at heq\n",
        "witness_reference": _REFERENCE,
    },

    # ---- loader: drop the emptiness conjunct (keep only the ownership test) ----
    {
        "id": "reject-loader-drop-emptiness",
        "kind": "uniqueness",
        "expect": "reject",
        # The documented pre-patch site #2 defect: keep an entry iff it is not
        # framework-owned, WITHOUT the added emptiness conjunct. Diverges on an
        # empty entry that is not framework-owned (kept where the spec drops it).
        "module": _swap(
            _BASE, _IMPL_L,
            "    return (entries.filterMap (fun e => if !isFrameworkOwned e then some (normalizePath e) else none))"),
        "refinement": "this is the pre-patch site #2 filter — the ownership "
                      "exclusion WITHOUT the added emptiness conjunct. A loader that "
                      "supplies an empty entry (not owned by the framework) would have "
                      "it expanded to the project base and added to the watched set, "
                      "the same empty-entry leak the fix closes at the second site. "
                      "It would NOT resolve (G-DIFF).",
        "rationale": "REJECT from `out = collectLoader entries`: collectLoader keeps "
                     "an entry only when it is non-empty AND not framework-owned; on "
                     "an empty entry that is not framework-owned the spec drops it "
                     "while the rival keeps it. Refuted at [[]], conditioned on "
                     "`isFrameworkOwned [] = false` (the opaque is not computable, so "
                     "the divergence is stated at that sub-domain): gold = [] (len 0), "
                     "rival = [normalizePath []] (len 1).",
        # Refuted against _REFERENCE (WITNESS MECHANICS). Conditions on ONE
        # opaque term (`isFrameworkOwned [] = false`); the gate's consistency
        # probe confirms no `False` follows from it (measured: exit 1).
        "witness":
            "example (h : isFrameworkOwned ([] : List Char) = false) :\n"
            "    (collectLoaderDirs [([] : List Char)]).run\n"
            "    ≠ DivM.res (collectLoader [([] : List Char)]) := by\n"
            "  intro heq\n"
            "  simp [collectLoaderDirs, NonDetT.run, pure, collectLoader, keepLoader, h]\n"
            "    at heq\n",
        "witness_reference": _REFERENCE,
    },

    # ---- loader: drop the ownership conjunct (keep only the emptiness test) ----
    {
        "id": "reject-loader-drop-ownership",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep an entry iff it is non-empty, dropping the ownership exclusion —
        # i.e. use the configured rule at the loader site. Diverges on a present
        # entry that IS framework-owned (kept where the spec drops it).
        "module": _swap(
            _BASE, _IMPL_L,
            "    return (entries.filterMap (fun e => if keepConfigured e then some (normalizePath e) else none))"),
        "refinement": "dropping the ownership exclusion re-adds the framework's own "
                      "bundled-template entries to the watched set; the pre-existing "
                      "behaviour that relies on framework-owned entries being excluded "
                      "would break. It would NOT resolve.",
        "rationale": "REJECT from `out = collectLoader entries`: collectLoader "
                     "excludes framework-owned entries; on a present, framework-owned "
                     "entry the spec drops it while the rival keeps it. Refuted at "
                     "[['a']], conditioned on `isFrameworkOwned ['a'] = true` (the "
                     "opaque is not computable): gold = [] (len 0), rival = "
                     "[normalizePath ['a']] (len 1). Separated from "
                     "reject-loader-drop-emptiness by varying the ownership bit — "
                     "this rival abuses the ownership conjunct, that one the "
                     "emptiness conjunct.",
        # Refuted against _REFERENCE (WITNESS MECHANICS). Conditions on ONE
        # opaque term (`isFrameworkOwned ['a'] = true`) — the sub-domain where
        # the ownership conjunct is load-bearing; consistency probe exits 1.
        "witness":
            "example (h : isFrameworkOwned (['a'] : List Char) = true) :\n"
            "    (collectLoaderDirs [(['a'] : List Char)]).run\n"
            "    ≠ DivM.res (collectLoader [(['a'] : List Char)]) := by\n"
            "  intro heq\n"
            "  simp [collectLoaderDirs, NonDetT.run, pure, collectLoader, keepLoader,\n"
            "    keepConfigured, h] at heq\n",
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 2 MANDATORY frame-mutation rivals, 4
# partial-domain uniqueness rivals) plus 2 AXIOM_TESTS entries. It contracts
# collect_direct_locations / collect_provider_locations over one read-only
# List[int] held at Acc(list_pred, 1/2), with the retained-entry collection
# built by a verified backward `while` loop; the two guard lines
# (`if d != 0` and `if d != 0 and not beneath_framework(d)`) are the modeled
# behaviour. This bundle contracts the SAME two collection sites as
# collectConfiguredDirs / collectLoaderDirs over `List (List Char)` (each entry
# a str/Path directory entry), with deep front-recursive folds
# collectConfigured/collectLoader, keepConfigured/keepLoader, and the two
# unchanged callees left OPAQUE (normalizePath <- `cwd / to_path`,
# isFrameworkOwned <- `is_django_path`). The partial-domain rivals port near-1:1;
# the carrier consequences are that both frame-mutation rivals are vacuous and
# the two axiom entries are dropped.
#
#   sibling case                   kind          -> here                              disposition
#   ---------------------------------------------------------------------------------------------
#   pos-direct-localreshape        soundness     -> pos-configured-letbind            PORTED
#   pos-provider-localreshape      soundness     -> pos-loader-letbind                PORTED
#   admiss-direct                  admissibility -> admiss-emptiness-skip-grounded    RE-AIMED
#   (no sibling)                   admissibility -> admiss-loader-emptiness-independent  ADDED (audit)
#   frame-mut-direct               uniqueness    -> (none)                            VACUOUS
#   frame-mut-provider             uniqueness    -> (none)                            VACUOUS
#   pd-direct-unguarded            uniqueness    -> reject-configured-unguarded       PORTED
#   pd-direct-inverted             uniqueness    -> reject-configured-inverted        PORTED
#   pd-provider-drop-present       uniqueness    -> reject-loader-drop-emptiness      PORTED
#   pd-provider-drop-framework     uniqueness    -> reject-loader-drop-ownership      PORTED
#   ax-sound-beneath_framework     axiom         -> (none)                            DROP (G-AX)
#   ax-contain-beneath_framework   axiom         -> (none)                            DROP (G-AX)
#
# PORTED (positives): the sibling hoists each guard into a typed boolean local,
#   keeping the backward loop, framing asserts and loop invariants verbatim so
#   the gold proof obligations still hold. Transliterated directly: bind the
#   per-entry keep-decision (keepConfigured / keepLoader) to a `let keep` before
#   the branch, loop and front-recursive invariant unchanged, so each frozen
#   proof closes untouched. One per contracted obligation, defending both.
# RE-AIMED (admiss-direct -> admiss-emptiness-skip-grounded): the sibling's
#   admissibility case asserts the 1/2 precondition permission admits a normal
#   F2P-shaped input. This backend's methods have NO `require` clause and no
#   permission surface, so that probe is degenerate (every input is in-domain).
#   It is re-aimed at the residual total-domain risk — a degenerate obligation —
#   via a live in-region assert pinning BOTH sides of the emptiness skip (empty
#   entry contributes nothing; present entry contributes its normalisation) at
#   the F2P cell, with the impl kept verbatim so the method's own obligation
#   still discharges.
# ADDED under audit (admiss-loader-emptiness-independent): the re-aimed case
#   above grounds only the CONFIGURED obligation, leaving the loader obligation
#   with no admissibility probe — and the loader is the harder half, since its
#   emptiness test must hold INDEPENDENTLY of the ownership conjunct. The added
#   case asserts that independence directly (prepending an empty entry leaves the
#   loader collection unchanged, for ANY value of the opaque ownership predicate),
#   so the admissibility lane now covers both obligations rather than one.
# VACUOUS (both frame-mutation probes): the sibling's MANDATORY probes overwrite
#   an input held at half heap permission (`entries[i-1] = d`) and are rejected
#   for INSUFFICIENT PERMISSION. This backend is referentially transparent —
#   there is no heap, no aliasing, and `entries` is declared read-only (not
#   `mut`) — so there is no read-only input to overwrite and no substitute probe
#   exists. Not fabricated (spec_guide directive 5: the frame obligation here is
#   discharged by the ABSENCE of a `mut` binder, which the frozen spec encodes).
#   RE-DERIVED UNDER AUDIT rather than accepted on the argument: the write was
#   actually attempted (`entries := entries.set (i - 1) e` inside the configured
#   impl region) and it is rejected at the LANGUAGE level, before any spec
#   obligation is reached — "`entries` cannot be mutated, only variables declared
#   using `let mut` can be mutated" (scripts/lean_verify.sh, exit 1). There is no
#   permission surface to attack, so the class is inexpressible here, not merely
#   hard; a case that "rejected" on that parse error would attribute nothing to
#   the spec.
# PORTED (the four value rivals): pd-direct-unguarded -> reject-configured-
#   unguarded (drop the emptiness filter at site #1; refuted where an empty entry
#   leaks — the F2P cell). pd-direct-inverted -> reject-configured-inverted
#   (keep empties, drop present entries; refuted at a present entry, the opposite
#   side of the guard). pd-provider-drop-present -> reject-loader-drop-emptiness
#   (drop the emptiness conjunct at site #2, keeping only the ownership test;
#   refuted at an empty non-owned entry). pd-provider-drop-framework ->
#   reject-loader-drop-ownership (drop the ownership conjunct; refuted at a
#   present framework-owned entry).
# DROP (both AXIOM_TESTS): the sibling's beneath_framework is @ContractOnly with
#   no value Ensures; here BOTH callees (normalizePath, isFrameworkOwned) are
#   OPAQUE free functions with no asserted contract, so there is nothing for G-AX
#   to validate (meta.json records G-AX = skip, "no axioms in bundle"), and this
#   gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (2 loops here, measures ``i``). A rival that loops without
#   a measure is refused outright (``Decreasing annotations are required in
#   total correctness semantics``), and a rival that supplies a CONSTANT
#   measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# BINDER / CLAUSE COVERAGE. TWO obligations, each with sole input binder
#   `entries : List (List Char)` whose entries carry (emptiness, framework-
#   ownership). Each obligation is DEFENDED (a positive) and ATTACKED (two
#   rivals):
#     collectConfiguredDirs: defended by pos-configured-letbind and
#       admiss-emptiness-skip-grounded; attacked by reject-configured-unguarded
#       (drop guard) and reject-configured-inverted (invert guard).
#     collectLoaderDirs: defended by pos-loader-letbind and
#       admiss-loader-emptiness-independent; attacked by
#       reject-loader-drop-emptiness (drop emptiness conjunct) and
#       reject-loader-drop-ownership (drop ownership conjunct).
#   The four reject witnesses probe FOUR DISTINCT input points (pts=4):
#     entries      : len 2 [[],['a']], len 1 [['a']], len 1 [[]], len 1 [['a']]
#                    — `entries.length` over 1 and 2, never fixed.
#     emptiness    : both an empty entry ([] — unguarded / drop-emptiness) and a
#                    present entry (['a'] — inverted / drop-ownership) are abused.
#     ownership    : varied via opaque conditioning — false at [] (drop-emptiness)
#                    and true at ['a'] (drop-ownership), each the sub-domain where
#                    that conjunct is load-bearing; the loader emptiness rival
#                    DEPENDS on the ownership bit being false there (else the entry
#                    would be dropped for ownership), and the ownership rival
#                    DEPENDS on it being true, so the decoy conjunct is genuinely
#                    abused rather than held fixed.
#   Both directions of the configured emptiness guard are attacked (keep-empty vs
#   drop-present), and each loader conjunct is attacked independently, so no rival
#   that mishandled only a fixed-value binder could slip through. Near-misses are
#   separated: reject-configured-unguarded AGREES with gold at [['a']] where
#   reject-configured-inverted fails, and vice-versa at an empty entry, so each
#   carries its own separating input.
AXIOM_TESTS = []
