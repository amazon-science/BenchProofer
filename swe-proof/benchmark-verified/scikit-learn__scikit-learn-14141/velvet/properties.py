"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14141 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct collectDependencyVersions`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the discriminating subject — the frozen solution, or the declared
``witness_reference`` on the cells where the frozen impl cannot decide anything.
Every reject case here uses a ``witness_reference``; the measurement that forced
that is in "WHY EVERY REJECT CASE CARRIES A ``witness_reference``" below).

DEFENDED SURFACE (one contracted method, NO input binders):

  collectDependencyVersions   return (out : List (List Char × Option (List Char)))
    ensures out = depEntries dependencyNames                 -- C1
    ensures "joblib".toList ∈ out.map Prod.fst               -- C2

The method assembles a diagnostic report: for every dependency in a fixed roster
(``dependencyNames``, nine ordered names) it pairs the name with its reported
version. The report is modeled as an association list ``List (List Char × Option
(List Char))`` (the repo dict, insertion-ordered, no duplicate names — the
bijection is exact, mapping.md §2). ``depEntries`` is a total, front-recursive
``def`` over the roster; the per-name version is the ONLY opaque part, the
uninterpreted callee ``lookupVersion : List Char → Option (List Char)`` (an
environment query, ``none`` when the dependency is absent). ``depEntries_keys``
proves the report's key-projection recovers exactly the roster, so the KEY-SET,
LENGTH, and ORDER are fully transparent; only the version VALUES are opaque.

Two independently-attackable top-level clauses:
  * C1 pins the ENTIRE report as ``depEntries dependencyNames`` — the exact roster
    as keys, in order, each paired with its own ``lookupVersion`` value. It has a
    transparent facet (which names are keys, in what order, how many) and one
    opaque facet (the per-name version value).
  * C2 pins the DISCRIMINATOR: the parallel-execution dependency ``"joblib"`` is a
    key of the report. This is the behaviour the public issue asks for and the
    F2P asserts (that ``"joblib"`` is a key of the report). Although C2 is
    entailed by C1, it is
    an independent top-level ``ensures``, so it is attacked in its own right.

ADVERSARIAL READ of the nagini classes on THIS carrier (see footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling notes this class is
    N/A even there (the routine takes no parameters, so there is no
    ``Acc(x,1/2)`` reference to overwrite). On this backend it is doubly vacuous:
    Lean/Velvet are referentially transparent, the method declares no ``mut``
    binder, and it has no inputs at all. No read-only input to mutate, no
    permission system, no substitute fabricated.
  * TERMINATION / VACUITY — the bundle sets ``loom.semantics.termination
    "total"`` (read it off the frozen file, line 4), so the verifier DOES
    discharge a termination obligation and a measure-free loop is genuinely
    rejected. Measured: an impl whose ``while`` carries no ``decreasing`` clause
    fails with ``Decreasing annotations are required in total correctness
    semantics`` (exit 1). That rejection is real but it is NOT witnessable on this
    carrier: the same missing-measure error makes the module UNCOMPILABLE, so a
    witness appended to it cannot elaborate either (measured: the witness build
    against the diverging rival exits 1 with the same decreasing-annotation error
    plus ``declaration uses 'sorry'`` — the surgery leaves nothing to refute
    against). A reject case whose witness cannot elaborate on the rival is
    recorded ``witness-unproven`` by this gate, i.e. inconclusive, so shipping it
    would make the battery fail rather than test anything. Recorded as a
    TOOLING-BLOCKED class, not as vacuous and not as a spec hole: the frozen spec
    does reject divergence, and the ``decreasing i`` clause in the frozen impl is
    what carries it.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense, exactly as the sibling
    records. C1 is pinned to ``depEntries dependencyNames``, a total ``def`` over
    the roster and the per-name callee; the version value is stored per-name via
    ``lookupVersion n`` inside ``depEntries`` structurally (directive 8: grounded,
    not an opaque answer-key the impl could echo without populating each key). The
    positive controls stand in for the ungrounded-echo probe.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the rivals sit. There is no
    input domain to partition (no binders), but the report has several
    independently-attackable facets: the key-set completeness (drop a roster
    name), the discriminating key (drop joblib), the key-set upper bound (add a
    non-roster key), the order, and the opaque per-name value.

THE WITNESS ON THIS CARRIER. ``lookupVersion`` is a genuine ``axiom`` (no
executable code), so Velvet's tester path (``extract_program_for`` →
``derive_tester_for`` → ``…Tester = false := by decide``) is DEAD: the extracted
``…Exec`` fails its IR compile because it depends on an axiom with no code
(measured). So each witness speaks DIRECTLY to the method's Hoare triple
(the astropy-14508 idiom): ``¬ (triple True collectDependencyVersions (fun out =>
<clause>))``, reducing the weakest precondition with ``rw [wp_pure]`` and refuting
the resulting concrete fact with the roster lemmas.

WHY EVERY REJECT CASE CARRIES A ``witness_reference`` (the audit repair). These
witnesses CANNOT be refuted against the frozen solution, and the original port's
claim that they were is false. The frozen body is the backward ``while`` loop, so
the ``triple`` contains an unreduced ``forIn Lean.Loop.mk`` term and
``rw [wp_pure]`` cannot fire — the build fails with ``Tactic `rewrite` failed: Did
not find an occurrence of the pattern wp (pure ?x) ?post``. That failure is a
SHAPE mismatch on the program term, and the asserted clause only ever lands in the
``?post`` metavariable, so it is claim-INDEPENDENT. Demonstrated by the forgery
test rather than argued: a witness asserting the ABSURD claim ``¬ (triple True
collectDependencyVersions (fun out => True))`` — i.e. that the frozen impl violates
the postcondition ``True`` — fails against the frozen solution with an error
byte-identical to the real witnesses' except for the echoed ``fun out => …`` text
(3 differing lines out of 73, all of them the pretty-printed claim). A flipped
witness asserting the frozen impl is CORRECT fails the same way. So gold's exit
code carried NO information about any claim, and all five rejections attested to a
tactic/shape mismatch rather than to the spec.

The repair is the mechanism the gate provides for exactly this: each reject case
names ``witness_reference = _REF_FOLD``, the loop-free ``return depEntries
dependencyNames`` impl. The gate checks that reference shares the frozen spec and
VERIFIES before using it, and an impl the verifier accepts cannot violate its own
spec — so a genuine witness must still fail there. Against that reference the wp
DOES reduce and the error becomes claim-SENSITIVE, which is the whole point:

  * real witness (key-projection) -> ``hc : depEntries dependencyNames =
    depEntries dependencyNames`` / ``this : True``, ``⊢ False`` unsolved: the
    reference SATISFIES the clause, so no refutation is available. Exit 1.
  * the absurd ``fun out => True`` forgery -> ```simp` made no progress``, a
    DIFFERENT error. Exit 1 for a different reason.
  * a claim genuinely false of the reference (``fun out => out = []``) -> ``hc``
    is the concrete nine-entry roster equation ``… = []``, i.e. the reduction
    happened and the claim survived as a real (unproven) equation.

That triple is the pair the audit protocol asks for: the error TRACKS the claim.

Most witnesses attack the TRANSPARENT facet of C1 (key-set / order / membership),
so they need no hypothesis and ``decide``-free ``simp`` over the roster closes
them. ONE rival (``weak-value-none``) attacks the OPAQUE per-name value; its
witness CONDITIONS on the carrier (``lookupVersion "pip".toList ≠ none`` — the
sub-domain where the real query returns a version) rather than pinning a value the
axiom cannot compute. The single hypothesis is jointly satisfiable (an axiom of
type ``List Char → Option (List Char)`` is not constrained to be constantly
``none``), so the gate's consistency probe leaves ``False`` unsolved — measured
against the reference impl, which is the subject the probe now runs on.
No ``sorry``/``admit``/``native_decide``/``axiom`` in any witness.

AXIOM lane: the sibling ships two axiom cases for ``version_of`` (its
``lookupVersion``). Those are G-AX's job (axiom soundness/containment against the
real callee, in Docker) and this gate ignores ``AXIOM_TESTS`` regardless, so they
are dropped here. ``AXIOM_TESTS = []``.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14141"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole backward `while` loop body, wholly inside
# ---- the one `-- impl-start` / `-- impl-end` region and unique in the file
# ---- (both facts asserted at load by _swap). Every variant reshapes exactly
# ---- this block. ----
_IMPL = """    -- impl-start
    let mut result : List (List Char × Option (List Char)) := []
    let mut i := dependencyNames.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
      invariant result = depEntries (dependencyNames.drop i)
      done_with i = 0
      decreasing i
    do
      let n := dependencyNames[i - 1]!
      let ver :| ver = lookupVersion n
      result := (n, ver) :: result
      i := i - 1
    return result
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the frozen `prove_correct` tactic body. A positive that reshapes the impl
# ---- into a form the frozen script no longer closes may RETUNE this body (it is
# ---- elided from the consumer spec view) WITHOUT touching the spec or dropping
# ---- the obligation — the `prove_correct collectDependencyVersions by` header
# ---- statement stays byte-identical. Rivals swap it for the flat body below so
# ---- the failure is a genuine unsolved postcondition (not a stale reference to
# ---- the loop variable the frozen script names); the WITNESS, not the module
# ---- build, is what attributes the rejection to the spec. Unique in the file. --
_PROOF = ("prove_correct collectDependencyVersions by\n"
          "  loom_solve\n"
          "  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]\n"
          "  simp_all")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# A loop-free rival needs no drop-step: `loom_solve` reduces the (concrete) body
# and leaves the unsolved postcondition. Retuning to this flat body is in scope
# (the tactic body is elided from the spec view).
_PROOF_FLAT = "prove_correct collectDependencyVersions by\n  loom_solve"


def _impl(body, proof=None):
    """Full Solution.lean variant with the impl body replaced (and optionally
    the prove_correct tactic body retuned)."""
    m = _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")
    if proof is not None:
        m = _swap(m, _PROOF, proof)
    return m


# ---- witness builder. Reaches the FROZEN method obligation directly (the axiom
# ---- carrier kills the tester path — see the module docstring). `triple True
# ---- collectDependencyVersions (fun out => <clause>)` is the partial-correctness
# ---- Hoare triple; for a rival whose body is `return <concrete>`, `wp_pure`
# ---- reduces the wp to a fact about that concrete report and the roster lemmas
# ---- refute it. The frozen loop body BLOCKS `wp_pure` for every claim alike, so
# ---- gold cannot serve as the discriminating subject (measured; see docstring) —
# ---- each reject case names `witness_reference` = `_REF_FOLD` instead. No tester,
# ---- no banned token.
_WIT_JOBLIB = (
    'example : ¬ (triple True collectDependencyVersions\n'
    '    (fun out => "joblib".toList ∈ out.map Prod.fst)) := by\n'
    '  simp only [collectDependencyVersions, triple]\n'
    '  intro h\n'
    '  have hc := h trivial\n'
    '  rw [wp_pure] at hc\n'
    '  simp [depEntries_keys, dependencyNames] at hc\n')

# Attacks C1 via the KEY-PROJECTION: whatever the opaque values, projecting the
# names out of the produced report must equal the roster (`depEntries_keys`); a
# rival with the wrong key-set (or wrong order) contradicts that, oracle-free.
_WIT_C1_KEYS = (
    'example : ¬ (triple True collectDependencyVersions\n'
    '    (fun out => out = depEntries dependencyNames)) := by\n'
    '  simp only [collectDependencyVersions, triple]\n'
    '  intro h\n'
    '  have hc := h trivial\n'
    '  rw [wp_pure] at hc\n'
    '  have := congrArg (List.map Prod.fst) hc\n'
    '  simp [depEntries_keys, dependencyNames] at this\n')

# CONDITIONED witness for the opaque VALUE facet of C1. The transparent key-set is
# right, so a key-projection refutation cannot fire; instead condition on the
# carrier where the real query returns a version (`lookupVersion "pip".toList ≠
# none`) — the sub-domain the rival's constant-`none` value is wrong on. The
# single hypothesis is jointly satisfiable (the axiom is unconstrained), so the
# refuting environment exists; the gate's consistency probe confirms it.
_WIT_VALUE = (
    'example (h : lookupVersion "pip".toList ≠ none) :\n'
    '    ¬ (triple True collectDependencyVersions\n'
    '        (fun out => out = depEntries dependencyNames)) := by\n'
    '  simp only [collectDependencyVersions, triple]\n'
    '  intro hh\n'
    '  have hc := hh trivial\n'
    '  rw [wp_pure] at hc\n'
    '  simp [depEntries, dependencyNames] at hc\n'
    '  exact h hc.1.symm\n')


# ---- WITNESS REFERENCE (audit repair). The loop-free `return depEntries
# ---- dependencyNames` impl: shares the frozen spec, and VERIFIES (it is
# ---- `pos-control-direct-fold`'s module, independently required to verify for
# ---- this battery to pass at all). Every reject case refutes its witness
# ---- against THIS instead of against the frozen solution, because the frozen
# ---- loop leaves `wp` unreduced and its exit code is claim-independent — see
# ---- the module docstring's forgery measurement. The gate re-checks both
# ---- properties (shares spec, verifies) before accepting it as the subject.
_REF_FOLD = _impl("    return depEntries dependencyNames", _PROOF_FLAT)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — MUST verify. If a faithful
    # correct impl cannot verify, the spec is SPEC-TOO-STRONG / UNSATISFIABLE.
    # =====================================================================
    {
        "id": "pos-control-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: drop the whole backward `while`
        # loop and its invariants; return the report as the single fold
        # expression `depEntries dependencyNames` directly. Observationally
        # identical to the loop on every environment (the loop's invariant IS
        # `result = depEntries (dependencyNames.drop i)`, so at i=0 it equals the
        # fold). The frozen drop-step proof no longer applies to a loop-free body,
        # so the tactic body is retuned to `loom_solve` (which now closes both
        # obligations outright); the `ensures` statements are byte-identical.
        "module": _impl("    return depEntries dependencyNames", _PROOF_FLAT),
        "rationale": "REVERSE of the sibling's pos-control (which reordered the "
                     "population loop): here the whole loop is collapsed to the "
                     "fold expression `depEntries dependencyNames`, computing the "
                     "identical report, so both C1 (`out = depEntries "
                     "dependencyNames`) and C2 (joblib ∈ keys) still hold. A "
                     "correct reshape must verify, else SPEC-TOO-STRONG over the "
                     "loop shape. Confirmed EXIT 0.",
    },
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT REPAIR: this case was `_BASE` verbatim — the frozen file, which
        # G-VERIFY already builds, so it duplicated an existing gate and tested
        # nothing of its own. The analogue of admissibility on a total,
        # input-free carrier is the obligation being UNSATISFIABLE at exactly an
        # F2P-shaped point, so the case now DISCHARGES that point concretely, by
        # evaluation, as a `have`, BEFORE closing the frozen obligation verbatim:
        #   * `hF2P` establishes the F2P-shaped fact (the parallel-execution
        #     dependency is among the report's keys) by `rw [depEntries_keys]`
        #     then `decide` — a real kernel evaluation over the roster, not an
        #     appeal to the frozen `joblib_mem_roster` lemma's statement;
        #   * `hlen` evaluates the report's length to the concrete 9, pinning
        #     that the roster the obligation ranges over is the full one.
        # Both `have`s are inside the `prove_correct` tactic body (elided from the
        # spec view, so `same_spec` holds and no new top-level lemma is declared —
        # `variant_problems` returns clean), and the frozen tactic sequence then
        # runs unchanged. If the post-image were unsatisfiable at the F2P point,
        # `decide` would fail here rather than somewhere inside `loom_solve`.
        "module": _impl(
            _IMPL[len("    -- impl-start\n"):-len("\n    -- impl-end")],
            "prove_correct collectDependencyVersions by\n"
            "  have hF2P : \"joblib\".toList ∈\n"
            "      (depEntries dependencyNames).map Prod.fst := by\n"
            "    rw [depEntries_keys]\n"
            "    decide\n"
            "  have hlen : (depEntries dependencyNames).length = 9 := by\n"
            "    simp [depEntries, dependencyNames]\n"
            "  loom_solve\n"
            "  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "the method takes no inputs and carries no `require`, so the "
                     "classic PRECOND-TOO-STRONG probe (a normal input excluded by "
                     "a precondition) has no surface. The analogue on a total "
                     "carrier is the obligation being UNSATISFIABLE at an "
                     "F2P-shaped point, which this case tests directly: it "
                     "discharges the F2P-shaped membership fact at the concrete "
                     "roster BY EVALUATION (`rw [depEntries_keys]; decide`) and "
                     "evaluates the report length to 9, as `have`s, before closing "
                     "the frozen obligation verbatim. A spec whose post-image were "
                     "empty at that point would fail on the `decide`, not deep "
                     "inside `loom_solve`. Confirmed EXIT 0 (audit-measured). Else "
                     "SPEC-UNSATISFIABLE / PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at the
    # facet it violates, and the refinement argument for its faithful real
    # counterpart. Each rival is LOOP-FREE (a single `return <expr>`) so its wp
    # reduces under `wp_pure`; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-omit-joblib",
        "kind": "uniqueness",
        "expect": "reject",
        # THE DISCRIMINATOR. Build the report over the roster MINUS its last entry
        # (the parallel-execution dependency): `depEntries dependencyNames.dropLast`
        # — the exact pre-gold behaviour. Correct on the other eight names; the
        # discriminating key is absent.
        "module": _impl("    return depEntries (dependencyNames.dropLast)",
                        _PROOF_FLAT),
        "refinement": "this is the pre-gold behaviour: the report is built over "
                      "the roster WITHOUT the parallel-execution dependency, so "
                      "that name never becomes a key. The failing test asserts "
                      "exactly that that name is a key of the report, so a "
                      "faithful patch "
                      "with this roster FAILS the F2P and would NOT resolve — a "
                      "verifying rival here would be a true verify⇏resolve break.",
        "rationale": "REJECT from C2 (`\"joblib\".toList ∈ out.map Prod.fst`), the "
                     "discriminating clause the fix adds: the eight-name report has "
                     "no such key. If it verified ⇒ SPEC-TOO-WEAK (the "
                     "discriminator is hollow). Witness attacks C2 directly via the "
                     "key-projection over the truncated roster. Rival exit 0; "
                     "refuted against `witness_reference` (the verifying "
                     "loop-free fold), exit 1 with the claim REDUCED — the "
                     "frozen loop blocks `wp_pure` claim-independently, so it "
                     "cannot be the subject (audit-measured).",
        "witness": _WIT_JOBLIB,
        "witness_reference": _REF_FOLD,
    },
    {
        "id": "weak-omit-preexisting",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the key-set. Build the report over an eight-name roster
        # that keeps joblib but DROPS a long-standing member (matplotlib). Correct
        # on eight of nine names incl. the discriminator; one pre-existing key
        # missing.
        "module": _impl(
            '    return depEntries [ "pip".toList, "setuptools".toList, '
            '"sklearn".toList, "numpy".toList, "scipy".toList, "Cython".toList, '
            '"pandas".toList, "joblib".toList ]',
            _PROOF_FLAT),
        "refinement": "correct on eight roster members (including the "
                      "discriminator) but drops a long-standing member's entry. "
                      "The failing test also asserts that pre-existing name is a "
                      "key (a P2P-side assertion carried into the F2P), so a "
                      "faithful patch whose roster omits it FAILS the test and "
                      "would NOT resolve.",
        "rationale": "REJECT from C1 (`out = depEntries dependencyNames`) via the "
                     "key-set: projecting the produced report's names yields the "
                     "eight-name list, which is ≠ the nine-name roster. If it "
                     "verified ⇒ SPEC-TOO-WEAK (domain-incomplete on the "
                     "long-standing roster). Witness attacks C1 via the "
                     "key-projection. Rival exit 0; refuted against "
                     "`witness_reference` (the verifying loop-free fold), exit "
                     "1 with the claim REDUCED — the frozen loop blocks "
                     "`wp_pure` claim-independently (audit-measured).",
        "witness": _WIT_C1_KEYS,
        "witness_reference": _REF_FOLD,
    },
    {
        "id": "weak-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        # UPPER-BOUND on the key-set. Build the correct nine-name report AND append
        # a tenth entry whose name is NOT a roster member. Every roster clause is
        # satisfied; the key-set is a strict superset of the roster.
        "module": _impl(
            '    return depEntries dependencyNames ++ '
            '[("zzz".toList, (none : Option (List Char)))]',
            _PROOF_FLAT),
        "refinement": "populates every roster key correctly AND adds a non-roster "
                      "key. HONEST NUANCE (carried from the sibling): the failing "
                      "test only asserts key PRESENCE, not exact key-set, so a "
                      "lenient real patch with an extra name could still pass it — "
                      "this is a SUPPORTING fidelity case for C1's upper bound "
                      "(the frozen spec pins the report to EXACTLY the roster, "
                      "which is behavioural equivalence to gold beyond the lenient "
                      "test), not an F2P-failing discriminator. The two rivals "
                      "above are the test-failing ones.",
        "rationale": "REJECT from C1 (`out = depEntries dependencyNames`) via the "
                     "key-set UPPER bound: the produced report's key-projection is "
                     "the roster plus a spurious name, ≠ the roster. If it "
                     "verified ⇒ SPEC-TOO-WEAK (the upper bound on the key-set is "
                     "hollow). Witness attacks C1 via the key-projection. Rival "
                     "exit 0; refuted against `witness_reference` (the verifying "
                     "loop-free fold), exit 1 with the claim REDUCED — the frozen "
                     "loop blocks `wp_pure` claim-independently (audit-measured).",
        "witness": _WIT_C1_KEYS,
        "witness_reference": _REF_FOLD,
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER. Build the report over the roster in REVERSED order. Every roster
        # name is a key (both C-clauses' membership facts hold) and the key-SET is
        # identical — only the ORDER differs. This is the CARRIER-NARROWING
        # inversion of the sibling's reorder POSITIVE: nagini's dict makes order
        # irrelevant (reorder verifies), but this backend models the report as an
        # ordered assoc-list, so C1 pins the order and a reorder must REJECT.
        "module": _impl("    return depEntries dependencyNames.reverse",
                        _PROOF_FLAT),
        "refinement": "the report carries the same names but in reversed order. "
                      "The lenient failing test checks only membership, so a "
                      "faithful patch that merely reordered the roster could still "
                      "pass it — SUPPORTING fidelity case for C1's ORDER facet "
                      "(the diagnostic report prints in roster order; the frozen "
                      "spec pins that order as part of behavioural equivalence to "
                      "gold), not an F2P-failing discriminator.",
        "rationale": "REJECT from C1 (`out = depEntries dependencyNames`) via "
                     "ORDER: the reversed report's key-projection is the reversed "
                     "roster, ≠ the roster (the two lists share a set but differ as "
                     "ordered lists). If it verified ⇒ SPEC-TOO-WEAK (order "
                     "unpinned). Witness attacks C1 via the key-projection. Rival "
                     "exit 0; refuted against `witness_reference` (the verifying "
                     "loop-free fold), exit 1 with the claim REDUCED — the frozen "
                     "loop blocks `wp_pure` claim-independently (audit-measured).",
        "witness": _WIT_C1_KEYS,
        "witness_reference": _REF_FOLD,
    },
    {
        "id": "weak-value-none",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE (the opaque facet). Build a report with the exact roster as keys,
        # in order, but pair EVERY name with the constant `none` instead of its own
        # `lookupVersion` value. Correct on the whole transparent surface (key-set,
        # order, length, joblib membership) and wrong only on the per-name value —
        # the one facet the opaque carrier governs.
        "module": _impl(
            "    return dependencyNames.map (fun n => (n, (none : Option (List Char))))",
            _PROOF_FLAT),
        "refinement": "pins the report to the right names but reports no version "
                      "for any of them. GROUNDED-ORACLE nuance (directive 8): the "
                      "lenient failing test checks only key presence, not the "
                      "version value, so a faithful patch that reported the wrong "
                      "value could still pass it — SUPPORTING fidelity case "
                      "demonstrating C1 pins the per-name value to the grounded "
                      "callee (`lookupVersion n`, not a constant), so there is no "
                      "ungrounded answer-key an echo could satisfy. Not an "
                      "F2P-failing discriminator; the value facet is what the "
                      "grounded oracle defends.",
        "rationale": "REJECT from C1 (`out = depEntries dependencyNames`) via the "
                     "opaque VALUE slot: `depEntries` pairs each name with "
                     "`lookupVersion n`; the constant-`none` rival disagrees "
                     "wherever the real query returns a version. If it verified ⇒ "
                     "SPEC-TOO-WEAK (the per-name value is unpinned / an echo of a "
                     "constant satisfies it). The only rival on the OPAQUE facet, "
                     "so its witness CONDITIONS on the carrier (`lookupVersion "
                     "\"pip\".toList ≠ none` — the sub-domain the rival is wrong "
                     "on) rather than a value the axiom cannot compute; the single "
                     "hypothesis is satisfiable (consistency probe: `False` "
                     "unsolved, measured against the reference). Rival exit 0; "
                     "refuted against `witness_reference` (the verifying "
                     "loop-free fold), exit 1 — the frozen loop blocks "
                     "`wp_pure` claim-independently (audit-measured).",
        "witness": _WIT_VALUE,
        "witness_reference": _REF_FOLD,
    },
    {
        "id": "weak-swapped-adjacent",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION (attack D). The ORDER facet was probed only by a FULL
        # reversal, which is the easiest order violation there is: it moves every
        # one of the nine names. A minimal transposition is the case a spec that
        # pins order only loosely (e.g. by first/last element, or by multiset) would
        # let through, so it probes the same clause at a strictly harder point.
        # Swaps two ADJACENT long-standing names, leaving the first six and the last
        # (the discriminator) in place: key-SET identical, length identical, joblib
        # still a key, first and last entries unchanged — only one adjacent pair is
        # transposed. Verified REJECTED with the key-projection witness (rival exit
        # 0).
        "module": _impl(
            '    return depEntries [ "pip".toList, "setuptools".toList, '
            '"sklearn".toList, "numpy".toList, "scipy".toList, "Cython".toList, '
            '"matplotlib".toList, "pandas".toList, "joblib".toList ]',
            _PROOF_FLAT),
        "refinement": "the report carries every roster name, in a nearly-correct "
                      "order: one adjacent pair of long-standing names is "
                      "transposed. The lenient failing test checks only membership, "
                      "so a faithful patch with this ordering would still pass it — "
                      "SUPPORTING fidelity case for C1's ORDER facet at its "
                      "MINIMAL violation (the report prints in roster order; the "
                      "frozen spec pins that order as part of behavioural "
                      "equivalence to gold), not an F2P-failing discriminator.",
        "rationale": "REJECT from C1 (`out = depEntries dependencyNames`) via ORDER "
                     "at a MINIMAL perturbation — a single adjacent transposition, "
                     "which the existing full-reversal rival does not probe (a spec "
                     "pinning order only by endpoints or as a multiset would admit "
                     "this and reject the reversal). If it verified ⇒ SPEC-TOO-WEAK "
                     "(order pinned only coarsely). Witness attacks C1 via the "
                     "key-projection. Rival exit 0; refuted against "
                     "`witness_reference` (the verifying loop-free fold), exit 1 "
                     "with the claim REDUCED (audit-measured).",
        "witness": _WIT_C1_KEYS,
        "witness_reference": _REF_FOLD,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus 2 AXIOM cases. Every one
# is accounted for below. The sibling models the SAME report but as a Python
# `dict` built by nine explicit population assignments under a totality
# (`MustTerminate`) obligation, over the callee `version_of`; this backend models
# the same report as an ORDERED association list built by a backward `while` loop
# over the front-recursive fold `depEntries`, with the same callee as the axiom
# `lookupVersion`. The value/key surface carries across; the permission surface
# does not exist here, and the termination surface exists as a real reject channel
# (this bundle is `termination "total"`) but is not WITNESSABLE — see below.
#
#   sibling case                 -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-control-reordered        -> pos-control-direct-fold        PORTED (reshaped)
#   pos-control-cheapest         -> pos-control-direct-fold        MERGED (same reshape)
#   admiss-roster-constructible  -> admiss-gold-total              RE-AIMED
#   rival-omit-joblib            -> weak-omit-joblib               PORTED (the discriminator)
#   rival-omit-matplotlib        -> weak-omit-preexisting          PORTED
#   rival-spurious-key           -> weak-spurious-key              PORTED
#   rival-diverge                -> (none)                         TOOLING-BLOCKED (see below)
#   (no sibling)                 -> weak-reversed-order            ADDED (order facet)
#   (no sibling)                 -> weak-value-none                ADDED (opaque value)
#   (no sibling)                 -> weak-swapped-adjacent         ADDED (order, minimal; audit)
#   ax-version-of-totality       -> (none)                         DROPPED (G-AX lane)
#   ax-version-of-containment    -> (none)                         DROPPED (G-AX lane)
#
# 5 SPEC cases ported/re-aimed (2 positive-shaped merged into 1 + 1 admiss + 3
# rivals), 3 rivals added (one by the audit), 1 rival tooling-blocked, 2 axiom
# cases dropped. Net 8 SPEC cases (2 verify, 6 reject).
#
# PORTED-RESHAPED (pos-control-reordered): the sibling reorders the population
#   loop and shows the dict is unchanged (order-independent). This backend's C1
#   is an ORDERED assoc-list, so a REORDER is NOT a valid positive here (it is a
#   reject — see weak-reversed-order). The reshape SPIRIT — "structurally
#   different construction, behaviourally identical report" — is carried by
#   pos-control-direct-fold, which collapses the whole loop to the fold
#   expression. This also absorbs pos-control-cheapest (the sibling's
#   "scaffold-free cheapest correct impl"): the direct fold IS the cheapest
#   correct impl and shows C1 is satisfiable without the loop scaffold.
# RE-AIMED (admiss-roster-constructible): the sibling asserts the empty
#   precondition admits building the real roster. This backend has NO precondition
#   AND no inputs, so the residual risk is that the post-image is unsatisfiable at
#   an F2P-shaped point. The AUDIT rewrote this case: it had been the frozen file
#   verbatim (duplicating G-VERIFY, testing nothing of its own) and now discharges
#   the F2P-shaped membership fact at the concrete roster BY EVALUATION, as a
#   `have`, before closing the frozen obligation verbatim.
# TOOLING-BLOCKED (rival-diverge). The original port recorded this VACUOUS on the
#   stated ground that the bundle runs `termination "partial"`, so a diverging impl
#   would verify vacuously and could not be a reject case. That ground is FALSE:
#   the frozen file sets `loom.semantics.termination "total"` (line 4), the
#   verifier discharges a termination obligation, and the frozen impl carries a
#   `decreasing i` clause precisely to meet it. The audit built the rival and
#   measured the truth: an impl whose `while` has no `decreasing` clause is
#   REJECTED (exit 1, `Decreasing annotations are required in total correctness
#   semantics`). So the class is a live reject channel, not a vacuous one.
#   It is nevertheless not SHIPPABLE, for a tooling reason rather than a semantic
#   one: that same error makes the whole module fail to ELABORATE, so a witness
#   appended to the rival cannot build either. Measured — the witness build against
#   the diverging rival exits 1 with the decreasing-annotation error, two
#   `declaration uses 'sorry'` warnings, and `'rw [wp_pure] at hc' tactic does
#   nothing`: there is no elaborated method term for the witness to speak about.
#   The gate reads a witness that fails on the RIVAL as `witness-unproven`, an
#   inconclusive outcome that forces MALFORMED-TESTS, so shipping the case would
#   make the battery FAIL rather than demonstrate the channel. Recorded as a known
#   TOOLING limitation of witness-on-uncompilable-module, with the measured error
#   text, rather than as vacuous (which would falsely say the battery is complete)
#   or as a spec hole (the spec does reject it).
# ADDED (weak-reversed-order): the CARRIER-NARROWING inverse of the sibling's
#   reorder positive. Because C1 pins the report as an ordered list, order is an
#   independently-attackable facet with no sibling counterpart; added so the ORDER
#   sub-behaviour of C1 is defended. Real, witnessed, refinement-honest
#   (supporting fidelity case: the lenient F2P would not catch it, stated plainly).
# ADDED by the AUDIT (weak-swapped-adjacent): attack D found the ORDER facet
#   probed only by a FULL reversal, the coarsest possible order violation. A single
#   adjacent transposition keeps the key-set, the length, the first six entries and
#   the discriminator in place, so it is the point a spec pinning order only by
#   endpoints or as a multiset would admit. Verified rejected, witnessed by the
#   key-projection against the reference.
# ADDED (weak-value-none): the OPAQUE per-name value facet of C1, the sibling's
#   grounded-oracle concern made into a rival. No sibling rival attacks the value
#   (the sibling instead argued no echo exists); on this carrier the value is the
#   one opaque facet, so a rival that reports a constant value is the direct probe
#   of C1's grounding, refuted by conditioning on the carrier. Real, witnessed,
#   refinement-honest (supporting fidelity case, as the F2P is value-blind).
# DROPPED (ax-version-of-*): the two axiom cases are G-AX's job (axiom
#   soundness/containment against the real callee in Docker) and this gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The method has NO input binders (it is nullary), so
#   "vary every input binder" is vacuous — there is no input a rival could
#   mishandle at a held-fixed value. The analogue here is coverage of the report's
#   independently-attackable FACETS, and every one is attacked by some rival:
#     * C2 discriminating key            -> weak-omit-joblib
#     * C1 key-set completeness (lower)   -> weak-omit-preexisting
#     * C1 key-set upper bound            -> weak-spurious-key
#     * C1 order                          -> weak-reversed-order
#     * C1 opaque per-name value          -> weak-value-none
#   Both top-level clauses (C1, C2) are attacked. Four rivals attack the
#   transparent facet of C1 at distinct structural points (drop-last, drop-mid,
#   append, reverse) and one conditions on the opaque carrier, so the witnesses do
#   not all collapse to one probe: they refute at four distinct roster shapes plus
#   one carrier hypothesis. (There is no numeric input point to tally as `pts=`;
#   the distinct-shape/hypothesis count is the carrier analogue.)
#
# WITNESS DISCRIMINATION (verified during authoring with scripts/lean_verify.sh,
#   and re-checked by the gate's two builds per reject case): each witness
#   elaborates against its rival (the concrete `return` reduces under `wp_pure`
#   and the roster lemmas refute the clause) and FAILS against the frozen solution
#   (the backward `while` blocks `wp_pure`, leaving `False` unsolved). The axiom
#   carrier forbids the tester path (`extract_program_for` fails its IR compile on
#   an axiom with no executable code), so every witness speaks directly to the
#   method's Hoare triple. No `sorry`/`admit`/`native_decide`/`axiom` appears; the
#   one conditioning hypothesis is jointly satisfiable (consistency probe leaves
#   `False` unsolved).
#
# AXIOM_TESTS: dropped (G-AX lane; this gate ignores them regardless).
AXIOM_TESTS = []
