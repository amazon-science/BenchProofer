"""properties.py — G-PBT falsification battery for django__django-16255 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct latestLastmod`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against its ``witness_reference`` — see the CARRIER NOTE for why the reference,
and not the frozen solution, is the witness's second subject here).

DEFENDED SURFACE — ONE contracted method over ONE read-only input:

  latestLastmod (stamps : List Int) return (out : Option Int)
    ensures out = latestStamp stamps                              -- (C1)
    ensures stamps.length = 0 → out = none                        -- (C2)
    ensures stamps.length > 0 → ∃ v, out = some v                 -- (C3)
    ensures ∀ k, k < stamps.length →
      ∃ v, out = some v ∧ stamps[k]! ≤ v                          -- (C4)
    ensures ∀ v, out = some v →
      ∃ k, k < stamps.length ∧ stamps[k]! = v                     -- (C5)

The method reports the most recent per-entry modification stamp across a
section's entries. The already-collected per-entry stamps are the single input
(``List Int``, comparable values); the reported value is ``Option Int``, whose
``none`` is the absent marker meaning "there is no stamp to report".

  * (C1) pins ``out`` to ``latestStamp stamps`` — the front-recursive running
    maximum over the method's OWN argument. It is a transparent ``def`` (the
    ``axioms`` region declares no ``axiom`` and no ``opaque`` leaf), so there is
    no answer-key oracle a wrong impl could echo: pinning ``out`` to it is
    grounded in the input, not an appeal to an external authority.
  * (C2) the EMPTY collection reports the absent marker. This is the clause the
    failing test turns on: a section that enumerates no entries must report
    nothing at all rather than failing.
  * (C3) a NON-EMPTY collection reports a real stamp (never the absent marker).
  * (C4) DOMINANCE — the reported stamp is ≥ every collected stamp.
  * (C5) MEMBERSHIP — the reported stamp IS one of the collected stamps, not a
    synthesised value.

C2..C5 are not decoration on C1: they are the four independently-attackable
facets of "the greatest of the collected stamps, or the absent marker when there
are none", and each is attacked below by its own rival. C4 ∧ C5 together are what
make the reported value the MAXIMUM rather than merely some stamp or merely some
upper bound.

ONE INPUT BINDER (``stamps``). It carries everything: its LENGTH selects the
empty/non-empty split (C2 vs C3), its ELEMENTS and their ORDER select which value
dominates (C4) and which values are admissible answers (C5). So "vary every input
binder" here means: vary the length across the empty/singleton/multi split, vary
WHERE the greatest stamp sits, and vary the SIGN — since a rival that seeded its
accumulator with a concrete zero is correct on every all-positive list and wrong
on an all-negative one. The five reject witnesses probe FIVE distinct points
doing exactly that (pts = 5; see the coverage accounting at the foot of the file).

CARRIER NOTE — HOW A WITNESS REACHES THE POST-IMAGE, AND WHAT THE FROZEN-SIDE
FAILURE IS ACTUALLY WORTH.

The spec is a ``method`` contract, not a bare predicate. The tester route
(``derive_tester_for``) is UNAVAILABLE on this bundle: three of the five clauses
are existentials over an unbounded ``Int`` (``∃ v, out = some v ∧ …``), so
``prove_postcondition_decidable_for latestLastmod`` cannot be discharged
(measured: ``unsolved goals … ⊢ Decidable (stamps.length > 0 → ∃ v, out = some
v)``, with the derived tester then resting on ``sorryAx``) and no usable
``latestLastmodTester`` exists to ``decide``.

So each witness instead ``extract_program_for``s the method — extraction needs no
decidability, it just names ``latestLastmodExec = NonDetT.run ∘ latestLastmod`` —
and states, at a CONCRETE literal input, the NEGATION of the single spec clause
its rival breaks, with ``latestLastmodExec`` standing in the ``out`` position:

    example : ¬ (([] : List Int).length = 0 →
        latestLastmodExec ([] : List Int) = DivM.res none) := by
      unfold latestLastmodExec latestLastmod
      simp [NonDetT.run, pure, latestStamp]

Every input is a small integer-literal list, so a loop-free rival's program
kernel-reduces and the residual is a decidable arithmetic fact about literals —
closed by ``simp`` alone, or by ``simp`` then ``decide`` where the residual is a
bounded quantifier over indices. No witness binds a hypothesis (the carrier is
fully transparent, so nothing needs conditioning), hence no consistency probe
arises and there are no assumptions that could be jointly unsatisfiable. No
banned token (sorry/sorryAx/admit/native_decide/axiom/opaque) appears in any
witness, and no witness names anything the frozen solution does not declare
besides the ``…Exec`` its own preamble extracts.

READ THE FROZEN-SIDE HALF HONESTLY — THIS IS THE LOAD-BEARING CAVEAT. The frozen
impl keeps a ``while`` loop under ``loom.semantics.choice "demonic"``; its
extracted ``latestLastmodExec`` is a ``forIn Lean.Loop.mk … invariantGadget …``
term the kernel will not unfold, so the witness script cannot reduce it and the
build fails with the un-normalised loop still in the goal. That is a STUCK
REDUCTION, not a refuted claim: gold's build would fail exactly that way for a
TAUTOLOGOUS witness too, so gold's exit code ALONE attests nothing about
discrimination. Every reject case therefore names a ``witness_reference`` —
``pos-direct-model``, the loop-free ``return latestStamp stamps``, which VERIFIES
against the frozen spec and whose ``…Exec`` DOES reduce. The gate checks that
reference (shares the frozen spec; verifies) and refutes each witness against IT.
Measured, and this is the substance of the attestation: against the reference
each of the five witnesses is refuted SEMANTICALLY, not stuck —

    weak-empty-concrete-stamp   ⊢ False                (goal reduced, unprovable)
    weak-nonempty-absent        ⊢ False
    weak-skip-first-entry       ⊢ False
    weak-first-not-greatest     ⊢ False
    weak-nonmember-dominator    `decide` proved `False` is false

Each clause is stated at the CONCRETE index (or output value) where its rival
breaks — ``[7,3][0]!``, ``[2,8,5][1]!``, ``some (-3)`` — rather than left
universally quantified. That is deliberate on both counts: naming the offending
witness point is strictly stronger than asserting one exists, and it keeps the
claim positionally readable so the coverage reader can see the probed input
rather than reporting the battery as unreadable and falling back to a by-name
signal.

— so each witness holds of its rival and PROVABLY fails of a machine-checked
correct impl at the same input on the same carrier shape. (Each was also built
against the frozen solution: exit 1, stuck as described. Recorded, not relied
on.) All three builds per case were run with ``scripts/lean_verify.sh``.

PROOF-SHAPE CONTROL — why each rejection is attributable to the VALUE and not to
a tactic. Every reject rival is a loop-free ``return <expr>`` whose proof body is
a bare ``loom_solve``, NOT the frozen script (which peels the loop invariant via
``latestStamp_drop_step`` and would fail on ``Unknown identifier i`` the moment
the loop is gone — a rejection that would attest nothing about the spec). And
that bare body is not merely "not the frozen one": ``pos-direct-model`` is the
SAME loop-free shape under the SAME bare ``loom_solve`` and it VERIFIES (exit 0).
So a rival failing under it fails because its expression violates a clause. The
witnesses then say WHICH clause, and at which input.

ADVERSARIAL READ of the nagini sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally-different but
    behaviourally identical correct impls must verify, else the spec is
    SPEC-TOO-STRONG (over-fit to the frozen code shape): return the grounded
    model with no loop; split the empty/non-empty cases explicitly before
    returning it; and keep the whole backward loop but write the per-step update
    as an explicit comparison instead of the order's ``max``. The three force
    three different proofs (bare ``loom_solve``; ``loom_solve`` plus a
    ``simp_all``/``grind`` arm for the branch; the frozen loop peel plus a
    ``max_def`` case split), so none is a definitional twin whose difference the
    elaborator silently erases.
  * ADMISSIBILITY — the sibling asserts that an F2P/P2P-shaped non-empty stamp
    list establishes its fractional-permission ``Requires``. This method has NO
    ``require`` clause at all (the ``pre-conditions`` region is empty) and there
    is no permission surface, so "a normal input is admitted" is degenerate here:
    no input could be excluded. The residual admissibility risk on a total domain
    is a DEGENERATE POST-IMAGE — a spec no impl can distinguish reads exactly
    like one every impl meets — so the case is re-aimed at that, via a live
    in-region ``assert`` that the modeled reduction genuinely SEPARATES the
    outcomes the rest of the battery relies on, at concrete F2P/P2P-shaped inputs.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling's
    MANDATORY frame-mutation rival writes the running maximum back into a
    ``List[int]`` held at half permission and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: ``stamps`` is an
    immutable value declared read-only (not ``mut``; only the loop-locals
    ``result``/``i`` are mutable), there is no heap, no aliasing, no ``Old`` and
    no permission system. There is nothing to overwrite and no frame clause to
    violate, so the class has no carrier analogue and no witness could state
    anything about it. Not ported, and no substitute fabricated — see the
    accounting for what the nearest expressible analogue actually does.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. C1 is pinned to
    ``latestStamp stamps``, a transparent ``def`` over the method's own argument,
    not to an ``@ContractOnly``/``opaque`` answer key; the sibling's
    "cheapest-impl positive control" counterpart is ``pos-direct-model``, which
    returns that model and is correct BECAUSE computing it is the real work.
  * CONTROL-FLOW-EFFECT (raise vs return) — the real empty-section path RAISES
    rather than returning a wrong value, and the sibling notes its value
    abstraction captures that as "a concrete stamp vs the absent marker". Same
    here: this carrier has no exception channel, and C2 pins the absent marker, so
    the raise/return difference is already fully absorbed into the
    ``none``-vs-``some`` distinction ``weak-empty-concrete-stamp`` attacks. No
    separate capability-token rival is needed or expressible.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, and NOT a known spec
    hole. The sibling carries no ``diverge-*`` / ``nonterm-*`` / ``weak-diverge``
    case, so there is nothing to port; and this bundle runs under ``set_option
    loom.semantics.termination "total"`` (Solution.lean line 7). Under ``total`` a
    postcondition is claimed of ALL runs, not only terminating ones, so the
    verifier demands a decreasing measure on every loop AND discharges its
    descent. Against the frozen ``while`` a diverging rival is refused outright
    (``Decreasing annotations are required in total correctness semantics``), and
    the sharper shape is refused too: a loop that CARRIES a ``decreasing`` clause
    whose measure the body never shrinks fails on the measure's OWN goal, under
    that clause's own name. So nothing is admitted vacuously. (An earlier version
    of this bullet set the result against a corpus census of ``partial`` bundles
    versus ``total`` ones, taken from an internal findings doc. That census is
    withdrawn: all 500 velvet bundles set ``"total"``, and the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so there is no split to be
    on a side of.) No reject case is written for it, and none is claimed dropped:
    the rejection fires at the ``method``, so no witness can elaborate against a
    diverging rival.
  * PARTIAL-DOMAIN / VALUE — carries the whole reject lane, five rivals deep:
    each gets most of the domain right and diverges on one sub-domain (the empty
    section; a section whose latest entry is the first; a section reduced to
    nothing; a synthesised stamp newer than every entry; a member that is not the
    greatest).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle consumes no ``axiom`` —
the reduction is an A-REFERENCE deep model (``latestStamp``), validated == the
real callee out-of-band by ``axiom_check.py`` / G-AX (mapping.md §3.1), not a
contract the proof consumes — so there is nothing here for this gate to probe,
and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16255"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS. Each lies wholly inside a region a variant may edit (the impl block
# between the markers, or the `prove_correct` tactic body) and is unique in the
# file — both facts asserted at load, so the manifest breaks loudly rather than
# silently mis-editing if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The frozen impl block (backward scan with the running-maximum update), WITHOUT
# the markers, so any replacement stays strictly inside the impl region.
_IMPL = """    let mut result : Option Int := none
    let mut i := stamps.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ stamps.length
      invariant result = latestStamp (stamps.drop i)
      done_with i = 0
      decreasing i
    do
      let c := stamps[i - 1]!
      result := some (match result with | none => c | some m => max c m)
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# The two loop-body lines the reshaping positive rewrites (inside _IMPL).
_STEP = """      let c := stamps[i - 1]!
      result := some (match result with | none => c | some m => max c m)"""
assert _BASE.count(_STEP) == 1, "loop-step anchor drift"

# The frozen proof body (tactic script only; elided from the spec view). Any
# variant that reshapes the impl retunes it — without touching the spec and
# without dropping the `prove_correct latestLastmod` obligation.
_PROOF = """prove_correct latestLastmod by
  loom_solve
  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
  rw [‹result = latestStamp (stamps.drop i)›]"""
assert _BASE.count(_PROOF) == 1, "proof anchor drift"

# A loop-free impl needs no invariant peel: `loom_solve` alone is the HONEST body
# for that shape. Keeping the frozen script instead would make every loop-free
# rival fail on `Unknown identifier i` — a rejection with no spec content. And
# `pos-direct-model` MEASURES that this bare body suffices for a CORRECT loop-free
# impl (exit 0), so a rival failing under it fails on its expression.
_PROOF_FLAT = """prove_correct latestLastmod by
  loom_solve"""


def _flat(expr, proof=_PROOF_FLAT):
    """A loop-free variant: return `expr` directly, under `proof`."""
    return _swap(_swap(_BASE, _IMPL, f"    return {expr}"), _PROOF, proof)


# ---- THE WITNESS REFERENCE. The loop-free direct return of the grounded model:
# ---- a machine-checked-correct impl of the frozen spec whose extracted
# ---- `latestLastmodExec` REDUCES. Shipped as a positive control in its own right
# ---- (`pos-direct-model`) and named by every reject case as its
# ---- `witness_reference`, because the FROZEN impl cannot serve as the witness's
# ---- second subject here: gold's `while` extracts to a `forIn`/`invariantGadget`
# ---- term the kernel will not unfold, so a witness script cannot reduce it and
# ---- its build fails with the loop un-normalised for EVERY claim, true or false.
# ---- Refuting each witness against THIS impl instead is a real discrimination:
# ---- an impl the verifier ACCEPTS cannot violate its own spec, so a witness that
# ---- fails here fails on the spec's content, not on the kernel's inability to
# ---- look inside a loop.
_REFERENCE = _flat("latestStamp stamps")


# ---- witness preamble. `extract_program_for` needs no decidability (the tester
# ---- route is dead on this bundle — see the CARRIER NOTE); it just names
# ---- `latestLastmodExec = NonDetT.run ∘ latestLastmod`, the extracted program,
# ---- which stands in the `out` position of the clause being negated. The
# ---- directive lives inside the witness text, so it is appended to BOTH builds
# ---- and the name exists on both sides by construction.
def _witness(statement, tactics):
    return ("\n"
            "extract_program_for latestLastmod\n\n"
            + statement
            + "  unfold latestLastmodExec latestLastmod\n"
            + tactics)


_SIMP = "  simp [NonDetT.run, pure, latestStamp]\n"
# One witness (weak-nonmember-dominator) leaves an equality between integer
# literals under a hypothesis that `simp` normalises but does not close, so it
# needs `decide` after. Measured: against the reference `decide` reports "proved
# that the proposition False is false", i.e. a SEMANTIC refutation of the witness
# — exactly the discrimination the stuck frozen-side build cannot supply. The
# other four close on `simp` alone with the goal reduced to `False`; adding
# `decide` there would fail with "No goals to be solved", so it is not added.
_SIMP_DECIDE = _SIMP + "  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen code shape).
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest correct impl: return the grounded model directly,
        # no loop at all — maximally different from the frozen backward scan. C1
        # holds by definition; C2..C5 are the frozen lemmas about `latestStamp`
        # applied to the whole input, which `loom_solve` discharges via their
        # `@[grind]` attributes. Also THIS BATTERY'S WITNESS REFERENCE and its
        # proof-shape control (see the CARRIER NOTE).
        "module": _REFERENCE,
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`latestStamp stamps` directly (no loop). `out` IS that model, so C1 "
            "holds on the whole domain and C2..C5 are the frozen `latestStamp` "
            "lemmas (nil / eq_none_iff / dominates / member) applied to the full "
            "input. If this failed to verify the spec would be over-fit to the "
            "loop code shape (SPEC-TOO-STRONG). It is also the honest "
            "no-ungrounded-echo control the sibling's pos-reshape stands in for: "
            "`latestStamp` is a transparent def over the method's own argument, "
            "not an answer key, so computing it IS the work and any WRONG "
            "expression fails C1 — which is what the five rivals demonstrate. "
            "Finally it is the battery's INTERPRETIVE CONTROL: it is the reject "
            "rivals' exact loop-free shape under the same bare `loom_solve` body, "
            "so (a) their rejection is attributable to their expression rather "
            "than to a tactic tuned to a loop they no longer have, and (b) their "
            "witnesses are refutable against a CORRECT impl whose extracted "
            "program actually reduces. Measured with scripts/lean_verify.sh."),
    },
    {
        "id": "pos-explicit-empty-split",
        "kind": "soundness",
        "expect": "verify",
        # Correct, and structurally different again: decide the empty/non-empty
        # split EXPLICITLY before reporting, instead of letting the reduction's
        # own base case produce the absent marker. Observationally identical for
        # every input (the model is `none` exactly on the empty collection), and
        # it forces a different proof: `loom_solve` leaves two branch arms, closed
        # by `simp_all` / `grind`.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    let e := stamps.length = 0\n"
                  "    if e then\n"
                  "      return none\n"
                  "    else\n"
                  "      return latestStamp stamps"),
            _PROOF,
            "prove_correct latestLastmod by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (simp_all)\n"
            "    | grind"),
        "rationale": (
            "branching on the empty/non-empty split explicitly and reporting the "
            "absent marker on the empty arm is observationally identical to the "
            "frozen behaviour (the model is `none` exactly on the empty "
            "collection, by the frozen eq_none_iff lemma), so C1..C5 still hold "
            "on the whole domain. A correct impl that makes the C2 split "
            "syntactically visible must verify, else the spec rejects a faithful "
            "impl over its branch structure (SPEC-TOO-STRONG). Distinct from "
            "pos-direct-model rather than a spelling of it: it introduces a "
            "control-flow branch the elaborator does not erase, and its proof "
            "needs branch arms `loom_solve` alone does not close. Ports the "
            "sibling pos-reshape's intent (a correct reshape of the same "
            "reduction) in the form this carrier makes meaningful."),
    },
    {
        "id": "pos-compare-update",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the ENTIRE frozen loop — backward scan, both invariants,
        # `done_with`/`decreasing` — and rewrites only the per-step update, from
        # the order's `max` to an explicit comparison, binding the new value to a
        # local. Equivalent by `max_def`, which is what the retuned proof tail
        # supplies on top of the frozen invariant peel.
        "module": _swap(
            _swap(_BASE, _STEP,
                  "      let c := stamps[i - 1]!\n"
                  "      let nxt : Int := match result with "
                  "| none => c | some m => if m < c then c else m\n"
                  "      result := some nxt"),
            _PROOF,
            _PROOF + "\n"
            "  cases h : latestStamp (List.drop i stamps) with\n"
            "  | none => simp [h]\n"
            "  | some m => simp only [h]; congr 1; rw [max_def]; split_ifs "
            "<;> omega"),
        "rationale": (
            "writing the running-maximum step as an explicit comparison (`if the "
            "running value is older than this entry's stamp then this entry's "
            "stamp else the running value`), bound to a local, computes the same "
            "value at every step as the order-theoretic form — they agree by "
            "`max_def` — so C1..C5 hold on the whole domain. The loop, both "
            "invariants and the termination measure are untouched; only the "
            "update expression and the proof tail (elided from the spec view) "
            "change. A correct impl in an equivalent arithmetic form must verify, "
            "else the spec is over-fit to how the comparison is spelled "
            "(SPEC-TOO-STRONG). This is the direct port of the sibling's "
            "pos-reshape, which hoists the update test into a local and writes "
            "the comparison the other way round while keeping every invariant "
            "verbatim; unlike the other two positives it keeps the LOOP, so the "
            "loop-carried invariant is exercised by a positive too."),
    },

    # =====================================================================
    # ADMISSIBILITY — this method has NO `require` clause (the pre-conditions
    # region is empty), so the sibling's "an F2P-shaped input satisfies the
    # precondition" probe is degenerate here: nothing could exclude a normal
    # input and there is no permission surface. The residual admissibility risk
    # on a total domain is a DEGENERATE POST-IMAGE, so the case is re-aimed to a
    # live in-region `assert` that the modeled reduction genuinely SEPARATES the
    # outcomes the rest of the battery relies on, at concrete F2P/P2P-shaped
    # inputs. The surrounding impl is kept VERBATIM so the method's own obligation
    # still discharges; the proof gains arms for the assert goal and for the
    # reshaped goal order (the tactic body is elided from the spec view). The
    # assert is live, not decoration: a false claim about the same points leaves
    # an unsolved goal (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    assert (with_name_prefix `admiss (\n"
                  "      latestStamp ([] : List Int) = none ∧\n"
                  "      latestStamp [7, 3] = some 7 ∧\n"
                  "      latestStamp [3, 7] = some 7 ∧\n"
                  "      latestStamp [(-4), (-9)] = some (-4)))\n"
                  + _IMPL),
            _PROOF,
            "prove_correct latestLastmod by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [latestStamp_drop_step stamps i (by omega) (by omega)]\n"
            "       rw [‹result = latestStamp (stamps.drop i)›])\n"
            "    | (clear a a_1 a_2 a_3; grind)"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at F2P/P2P-shaped "
            "inputs: the EMPTY collection resolves to the absent marker (the "
            "failing test's own scenario — a section with no entries reports "
            "nothing rather than failing), a two-entry collection resolves to its "
            "greatest stamp whether that stamp sits FIRST or LAST (so the "
            "reduction is not position-blind, and the P2P 'the most recent stamp' "
            "behaviour is genuinely exercised), and an all-negative collection "
            "resolves to its greatest NEGATIVE stamp (so the reduction is not "
            "secretly anchored at zero — the sub-domain where a concretely-seeded "
            "accumulator would agree with the correct answer on every positive "
            "input and still be wrong). If these cannot discharge, the obligation "
            "is degenerate on the very domain the tests exercise. The impl is kept "
            "verbatim so C1..C5 still verify for the frozen loop. The sibling's "
            "admiss-nonempty re-aimed: it asserts a normal non-empty list "
            "establishes its fractional-permission Requires, but this method "
            "declares no `require` at all and has no permission surface, so that "
            "probe could not fail; post-image non-degeneracy is the sharper "
            "residual risk on a total domain."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, plus the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a loop-free
    # `return <expr>` so its extracted program reduces under the witness script;
    # each carries the bare `loom_solve` body that pos-direct-model measures to
    # SUFFICE for a correct impl of that same shape, so the rejection is the
    # expression's and not a stale tactic's. The frozen spec is untouched.
    #
    # F2P scenario grounding the refinements: a section that supports a per-entry
    # modification stamp but enumerates NO entries must report no stamp at all
    # (emit no Last-Modified header) instead of failing. Key P2P: the reported
    # value on a non-empty section is the MOST RECENT of its entries' stamps.
    # =====================================================================
    {
        "id": "weak-empty-concrete-stamp",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Report a concrete stamp instead of the absent marker when there
        # is nothing to report: force the result into `some`, substituting a
        # concrete zero for the absent marker. Still the true greatest stamp on
        # EVERY non-empty section; diverges ONLY on the empty sub-domain.
        "module": _flat(
            "some (match latestStamp stamps with | none => 0 | some m => m)"),
        "refinement": (
            "the faithful pre-change code reduces the collected stamps with NO "
            "absent-marker fallback, so on a section that enumerates no entries "
            "the reduction over an empty collection FAILS outright (the real "
            "runtime raises rather than returning a value). The failing test "
            "asserts that such a section reports no stamp at all — a clean absent "
            "marker, no header — not an error, so the pre-change code FAILS it and "
            "does NOT resolve; this is the very defect the change corrects. The "
            "value abstraction captures the raise as `a concrete stamp instead of "
            "the absent marker`, and either way the empty section stops reporting "
            "'nothing to report'. On every non-empty section this rival is "
            "correct, so it is a genuine partial-domain break rather than a "
            "wholesale wrong answer."),
        "rationale": (
            "REJECT from C2 (`stamps.length = 0 → out = none`): the empty "
            "collection must report the absent marker and this rival reports "
            "`some 0`. It also breaks C1 and C5 there (0 is not one of the "
            "collected stamps when there are none). Refuted at the EMPTY list — "
            "the only point in the battery where the length is 0, and the input "
            "the failing test itself exercises; the reference resolves `none` and "
            "the rival `some 0`. If it VERIFIED the spec would be SPEC-TOO-WEAK, "
            "admitting the exact bug under repair. Ports the sibling "
            "w1-empty-concrete."),
        "witness": _witness(
            "example : ¬ (([] : List Int).length = 0 →\n"
            "    latestLastmodExec ([] : List Int) = DivM.res none) := by\n",
            _SIMP),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-skip-first-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the FRONT: reduce over the collection with its first entry
        # dropped. Keeps C2 (an empty collection still reports the absent marker)
        # and is correct whenever the first entry is not the unique greatest;
        # diverges when the latest stamp is the first entry.
        "module": _flat("latestStamp (stamps.drop 1)"),
        "refinement": (
            "corresponds to an off-by-one slice of the collected stamps (reduce "
            "over all entries but the first). For a section whose latest entry is "
            "the first one it reports an OLDER stamp, and for a single-entry "
            "section it reports no stamp at all. The P2P behaviour that the "
            "reported value is the most recent of the section's entries asserts "
            "the EXACT latest value, so such a patch would FAIL it and does NOT "
            "resolve. Correct on every section whose first entry is not the unique "
            "latest, so a partial-domain break."),
        "rationale": (
            "REJECT from C4 (dominance, `∀ k < stamps.length → … stamps[k]! ≤ "
            "v`): index 0 is left unbounded by the reported value, so a collection "
            "whose greatest stamp sits FIRST refutes it. (It also breaks C1 "
            "wherever the first entry is the unique maximum, and C3 on a "
            "single-entry section.) Refuted at `[7, 3]` — descending, so the "
            "greatest stamp is at index 0 and the rival reports `some 3` where the "
            "reference reports `some 7`. The witness states C4 at the offending "
            "index k=0 specifically, so against the reference the goal reduces to "
            "`False` — a semantic refutation, not a stuck term. This is the "
            "only witness whose maximum sits at the FRONT, and it moves "
            "`stamps.length` to 2. Ports the sibling w2-skip-first."),
        # C4 INSTANTIATED at the index where it fails (k = 0, the entry the
        # rival skips) rather than left universally quantified: a strictly
        # stronger refutation (it names the offending index instead of merely
        # asserting one exists) and one a reader can locate positionally.
        "witness": _witness(
            "example : ¬ (∃ v, latestLastmodExec [7, 3] = DivM.res (some v) ∧\n"
            "    ([7, 3] : List Int)[0]! ≤ v) := by\n",
            _SIMP),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-nonempty-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the BACK: reduce over the collection with its last entry
        # dropped. Keeps C2, and on a section with two or more entries still
        # reports a real (if possibly stale) stamp — but on a SINGLE-entry section
        # it reports the absent marker, i.e. a section that HAS an entry reports
        # nothing to report. The dual of weak-empty-concrete-stamp: that one
        # reports a stamp where none exists, this one reports none where a stamp
        # exists.
        "module": _flat("latestStamp stamps.dropLast"),
        "refinement": (
            "corresponds to an off-by-one slice at the other end (reduce over all "
            "entries but the last). A single-entry section would then report NO "
            "stamp at all and emit no Last-Modified header, and a multi-entry "
            "section whose latest entry is the last one would report an older "
            "stamp. The P2P behaviour that a section WITH entries reports the most "
            "recent of them asserts a concrete header value, so such a patch would "
            "FAIL it and does NOT resolve. Note it passes the failing "
            "empty-section test — it is wrong on the opposite sub-domain, which is "
            "what makes it an independent probe rather than a restatement."),
        "rationale": (
            "REJECT from C3 (`stamps.length > 0 → ∃ v, out = some v`): a non-empty "
            "collection must report a real stamp, and this rival reports the absent "
            "marker on a single-entry collection. (It also breaks C1 and C4 "
            "there.) C3 is attacked by NO other rival: the other four all report "
            "`some` on non-empty input, so without this case the 'non-empty ⇒ a "
            "real stamp' clause would be defended and never attacked, and a rival "
            "that silently dropped an entry would go unnoticed. Refuted at the "
            "SINGLETON `[3]` — the only length-1 point in the battery — where the "
            "reference reports `some 3` and the rival `none`. ADDED (no sibling "
            "counterpart): the sibling covers the front off-by-one only, and on "
            "this carrier the clause its rival set leaves unattacked is C3."),
        "witness": _witness(
            "example : ¬ (([3] : List Int).length > 0 →\n"
            "    ∃ v, latestLastmodExec [3] = DivM.res (some v)) := by\n",
            _SIMP),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-nonmember-dominator",
        "kind": "uniqueness",
        "expect": "reject",
        # Report a stamp strictly NEWER than every collected one. Keeps C2 (the
        # absent marker maps to the absent marker), keeps C3, and satisfies
        # DOMINANCE by construction — it violates MEMBERSHIP alone. The only rival
        # that isolates C5, which is what makes C4 ∧ C5 (rather than C4 alone)
        # load-bearing.
        "module": _flat("(latestStamp stamps).map (fun m => m + 1)"),
        "refinement": (
            "corresponds to a reduction that reports a synthesised stamp strictly "
            "newer than every entry (e.g. the maximum advanced by a fixed "
            "interval). The section would then advertise a modification time LATER "
            "than any of its entries actually has. The P2P behaviour pins the "
            "reported value to the exact stamp of the section's most recent entry, "
            "so such a patch would FAIL it and does NOT resolve. It resolves the "
            "empty-section test correctly, so it is wrong only on non-empty "
            "sections — and wrong there in a way DOMINANCE alone cannot see."),
        "rationale": (
            "REJECT from C5 (membership, `∀ v, out = some v → ∃ k < stamps.length "
            "∧ stamps[k]! = v`): the reported value must BE one of the collected "
            "stamps, and a strictly-greater synthetic value is not. This is the "
            "only rival that satisfies C4 (it dominates every stamp by "
            "construction) while breaking C5, so it is what makes membership "
            "load-bearing rather than merely implied — without it, a spec carrying "
            "only the dominance half would look fully attacked. Refuted at `[(-4), "
            "(-9)]`: the only ALL-NEGATIVE point in the battery, so the witness "
            "also demonstrates the spec does not secretly permit an "
            "anchored-at-zero answer; the reference reports `some (-4)` and the "
            "rival `some (-3)`. The witness states C5 at the rival's own reported "
            "value, so against the reference `decide` reports the residual `False` "
            "is false — a semantic refutation, not a stuck term. Ports the "
            "sibling w3-nonmember-dominator."),
        # C5 INSTANTIATED at the value the rival actually reports (`some (-3)`,
        # the true maximum -4 advanced by one) rather than left universally
        # quantified over `v`: it names the offending output instead of merely
        # asserting one exists, and it is positionally readable.
        "witness": _witness(
            "example : ¬ (latestLastmodExec [(-4), (-9)] = "
            "DivM.res (some (-3)) →\n"
            "    ∃ k, k < ([(-4), (-9)] : List Int).length ∧ "
            "([(-4), (-9)] : List Int)[k]! = (-3)) := by\n",
            _SIMP_DECIDE),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-first-not-greatest",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the FIRST collected stamp: a genuine member, and correct on the
        # empty section (absent marker) and on every single-entry section, so it
        # satisfies C2, C3 and C5 on the WHOLE domain. It breaks DOMINANCE alone,
        # and only when a later entry is newer. The near-miss counterpart of
        # weak-nonmember-dominator: that one is an upper bound that is not a
        # member, this one a member that is not an upper bound.
        "module": _flat("(match stamps with | [] => none | c :: _ => some c)"),
        "refinement": (
            "corresponds to a reduction that reports the first collected stamp "
            "rather than the greatest (e.g. indexing the collection instead of "
            "reducing it, or reducing with the wrong extremum). The section would "
            "advertise an OLDER modification time than its most recent entry. The "
            "P2P behaviour asserts the MOST RECENT stamp, so such a patch would "
            "FAIL it and does NOT resolve. It reports the absent marker correctly "
            "on an empty section (so it resolves the failing test) and is correct "
            "on single-entry sections and on sections already ordered "
            "newest-first — a genuinely partial-domain break, and the subtlest of "
            "the five since every value it reports IS a real entry's stamp."),
        "rationale": (
            "REJECT from C4 (dominance) ALONE: the first collected stamp is always "
            "a genuine member (so C5 holds honestly, not incidentally) and is "
            "always `some` on non-empty input (C3) and `none` on empty input (C2), "
            "so nothing but the dominance clause distinguishes it. That is what "
            "makes it the sharpest attack on C4 and the near-miss partner of "
            "weak-nonmember-dominator, which breaks C5 while satisfying C4. It is "
            "given its OWN input rather than sharing weak-skip-first-entry's: "
            "refuted at `[2, 8, 5]`, the only length-3 point and the only one "
            "whose greatest stamp sits in the MIDDLE (so neither a front nor a back "
            "off-by-one would produce the same answer), where the reference reports "
            "`some 8` and the rival `some 2`. The witness states C4 at the "
            "offending index k=1 specifically, so against the reference the goal "
            "reduces to `False` — a semantic refutation. Ports the sibling "
            "w4-first-member."),
        # C4 INSTANTIATED at the index where it fails (k = 1, the mid-list
        # greatest stamp the rival reports past): names the offending index
        # rather than asserting one exists, and is positionally readable.
        "witness": _witness(
            "example : ¬ (∃ v, latestLastmodExec [2, 8, 5] = DivM.res (some v) ∧\n"
            "    ([2, 8, 5] : List Int)[1]! ≤ v) := by\n",
            _SIMP),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness, 1 admissibility, 5 uniqueness — one of which is the MANDATORY
# frame-mutation rival) plus an empty AXIOM lane. Both bundles contract exactly
# ONE function over exactly ONE input, so this is an unusually TIGHT port: the
# sibling's `latest_stamp(stamps: List[int]) -> Optional[int]` and this bundle's
# `latestLastmod (stamps : List Int) return (out : Option Int)` are the same
# surface, and the sibling's four load-bearing postcondition clauses map
# one-to-one onto C2..C5, with C1 (`out = latestStamp stamps`) added on top as the
# deep model of the whole reduction. So no case is lost to carrier narrowing —
# only the frame/permission rival, for which this carrier has no analogue.
#
#   sibling case              kind          -> here                       disposition
#   -----------------------------------------------------------------------------------
#   pos-reshape               soundness     -> pos-compare-update         PORTED
#   (no sibling)              soundness     -> pos-direct-model           ADDED
#   (no sibling)              soundness     -> pos-explicit-empty-split   ADDED
#   admiss-nonempty           admissibility -> admiss-nondegenerate       RE-AIMED
#   frame-write               uniqueness    -> (none)                     VACUOUS
#   w1-empty-concrete         uniqueness    -> weak-empty-concrete-stamp  PORTED
#   w2-skip-first             uniqueness    -> weak-skip-first-entry      PORTED
#   w3-nonmember-dominator    uniqueness    -> weak-nonmember-dominator   PORTED
#   w4-first-member           uniqueness    -> weak-first-not-greatest    PORTED
#   (no sibling)              uniqueness    -> weak-nonempty-absent       ADDED
#   AXIOM_TESTS (0)           axiom         -> (none)                     N/A
#
# 9 velvet SPEC cases: 3 soundness, 1 admissibility, 5 uniqueness rivals.
#
# PORTED (pos-reshape, w1, w2, w3, w4): five of the sibling's seven carry across
#   intact. pos-reshape's local-variable / rewritten-comparison reshape becomes
#   pos-compare-update (the same edit: hoist the update into a local, write the
#   comparison the other way round, keep every invariant verbatim); w1's
#   concretely-seeded accumulator, w2's front off-by-one, w3's strictly-greater
#   synthetic value and w4's first-member each keep their sibling refinement
#   argument intact in substance (unpatched empty-section behaviour / an older
#   stamp reported / a stamp newer than any entry / an older stamp reported), now
#   each backed by a machine-checked witness at a DISTINCT input point.
# ADDED (pos-direct-model, pos-explicit-empty-split): the sibling ships ONE
#   positive because a Viper impl need only satisfy the contract, whereas here a
#   positive additionally has to REPROVE — so the shapes a positive can take are
#   themselves worth probing. Three shapes with three different proofs (bare
#   `loom_solve`; branch arms needing `simp_all`/`grind`; the frozen loop peel plus
#   a `max_def` case split) test that the spec is not over-fit to any one of them.
#   pos-direct-model additionally carries two loads the sibling has no need of: it
#   is the PROOF-SHAPE CONTROL (its bare `loom_solve` body is the one every reject
#   rival uses, and it VERIFIES under it, so a rival's failure is its expression's)
#   and the WITNESS REFERENCE (see the CARRIER NOTE).
# ADDED (weak-nonempty-absent): the sibling's rivals leave `non-empty ⇒ a real
#   stamp` (C3) attacked by nothing — w1 breaks the empty case, w2/w3/w4 all report
#   `some` on non-empty input. A rival that silently drops an entry and reports the
#   absent marker for a section that HAS one would therefore have gone unnoticed.
#   It is also the exact dual of weak-empty-concrete-stamp (a stamp where none
#   exists / no stamp where one exists), and the only case probing the SINGLETON,
#   so it moves `stamps.length` off {0, 2, 3}.
# RE-AIMED (admiss-nonempty -> admiss-nondegenerate): the sibling builds an
#   F2P-shaped non-empty list and asserts its half-permission `Requires` predicate
#   holds on it. This method declares NO `require` clause at all (the
#   pre-conditions region is empty) and there is no permission surface, so the
#   probe could not fail and would attest nothing. Re-aimed at the sharper
#   residual risk — a DEGENERATE post-image — via a live in-region assert that the
#   reduction separates the empty case from the non-empty one, is not
#   position-blind (the greatest stamp is found whether it sits first or last), and
#   is not anchored at zero (an all-negative collection resolves to its greatest
#   negative stamp). Verified live out-of-band: a false claim at the same points
#   leaves an unsolved goal.
# VACUOUS (frame-write): the sibling's MANDATORY frame-mutation rival computes the
#   correct running maximum but writes it back into the read-only `stamps` (held at
#   half permission), and is rejected by the PERMISSION SYSTEM for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: `stamps` is an immutable
#   value declared read-only (not `mut`; only the loop-locals `result`/`i` are
#   mutable), there is no heap, no aliasing, no `Old` and no permission system.
#   There is no read-only input to overwrite and no frame clause to violate, so the
#   class has NO carrier analogue. The nearest expressible thing — assigning to the
#   parameter itself inside the impl region — is refused by the carrier at
#   ELABORATION ("cannot be mutated, only variables declared using `let mut` can be
#   mutated"), i.e. for a binder/parse reason with no spec content whatever, and
#   there would be nothing for a witness to state. Not ported, and no substitute
#   fabricated: a rival "rejected" for a parse error would record a G-PBT pass
#   while testing nothing about the postcondition. The sibling's own refinement
#   argument for it (a patch clamping each entry's stamp to the running maximum
#   would corrupt the per-entry values the section renders) has no counterpart
#   either, since nothing here can corrupt an input.
# N/A (AXIOM_TESTS): the sibling's axiom lane is already EMPTY (its axioms region
#   is empty and its single A-reference is validated out-of-band). Same here: this
#   bundle consumes no `axiom`, `latestStamp` is an A-reference deep model checked
#   == the real callee by axiom_check.py / G-AX (mapping.md §3.1), and the G-PBT
#   gate ignores AXIOM_TESTS regardless.
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
# CLAUSE / BINDER / POINT COVERAGE. FIVE `ensures` clauses. ALL FIVE are DEFENDED
#   (the three positives and the admissibility case each discharge every clause).
#   ALL FIVE are ATTACKED, and each of C2..C5 has a rival that isolates it:
#     C1 (out = latestStamp stamps)  — all five rivals
#     C2 (empty -> absent marker)    — weak-empty-concrete-stamp
#     C3 (non-empty -> a real stamp) — weak-nonempty-absent (only this one)
#     C4 (dominance)                 — weak-skip-first-entry, weak-first-not-greatest
#                                      (the latter satisfies C2/C3/C5 on the WHOLE
#                                       domain, so it isolates C4 exactly)
#     C5 (membership)                — weak-nonmember-dominator (only this one; it
#                                      satisfies C4 by construction, so it isolates
#                                      C5 exactly)
#   The two near-miss pairs are deliberate: C4-without-C5 (an upper bound that is
#   not a member) and C5-without-C4 (a member that is not an upper bound) are
#   attacked SEPARATELY, so neither half of "the maximum" can be dropped from the
#   spec unnoticed. The single input binder `stamps` is moved across FIVE distinct
#   points (pts = 5):
#     * weak-empty-concrete-stamp   []            len 0
#     * weak-nonempty-absent        [3]           len 1
#     * weak-skip-first-entry       [7, 3]        len 2, maximum FIRST
#     * weak-nonmember-dominator    [-4, -9]      len 2, all NEGATIVE
#     * weak-first-not-greatest     [2, 8, 5]     len 3, maximum in the MIDDLE
#   So `stamps.length` ranges over {0, 1, 2, 3} (both sides of the empty/non-empty
#   split and both sides of the singleton boundary); the POSITION of the greatest
#   stamp ranges over first / middle / last-is-not-it; and the SIGN ranges over
#   all-positive and all-negative — the last being the point a concretely-seeded
#   accumulator would otherwise hide, since seeding at zero agrees with the correct
#   answer on every all-positive input. No facet of the only binder is held fixed
#   across the reject set. Every witness states its refutation at concrete literals
#   and binds NO hypothesis, so no consistency probe arises and no assumption could
#   be vacuous.
#   MEANINGFULNESS (not merely distinctness): at each of the five points the
#   reference's own output differs from the rival's, value for value — `none` vs
#   `some 0`; `some 3` vs `none`; `some 7` vs `some 3`; `some (-4)` vs `some (-3)`;
#   `some 8` vs `some 2`. No two are two spellings of one discrimination: they split
#   by the empty/non-empty boundary, by the singleton boundary, by where the maximum
#   sits, by member-vs-dominator, and by sign.
#
# WITNESS MECHANICS: the tester route is DEAD here (three clauses are existentials
#   over an unbounded Int, so `prove_postcondition_decidable_for` cannot be
#   discharged and no usable `latestLastmodTester` exists), so each witness
#   `extract_program_for`s the method and negates the ONE clause its rival breaks,
#   with `latestLastmodExec <literal>` in the `out` position, INSTANTIATED at the
#   concrete index or output value where that clause fails rather than left
#   universally quantified (a stronger claim, and a positionally readable one).
#   Each rival is loop-free so its `…Exec` kernel-reduces; the frozen `while` (a
#   `forIn`/`invariantGadget` term the kernel will not unfold) does NOT, which is
#   why every case names `pos-direct-model` as its `witness_reference` rather than
#   resting on the frozen build's exit code — gold's build fails for a tautologous
#   witness too, so that code alone attests nothing. All three builds per case were
#   run with scripts/lean_verify.sh: rival exit 0; reference exit 1 by SEMANTIC
#   refutation (four with the goal reduced to `⊢ False` by `simp`, one with
#   "`decide` proved that the proposition False is false"); frozen exit 1 by stuck
#   reduction, recorded but not relied on.
AXIOM_TESTS = []
