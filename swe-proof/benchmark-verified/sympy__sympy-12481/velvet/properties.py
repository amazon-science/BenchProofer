"""properties.py — G-PBT falsification battery for sympy__sympy-12481 (velvet).

NOT a Velvet module; a record of the adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (ONE contracted method). ``buildExplicitForm (entries)
(grouped)`` builds the explicit list form of a rearrangement of the points
``0, 1, …`` from an argument written in either of the two ways the public
constructor accepts. ``grouped`` is a GENUINELY FREE Bool — both readings are in
the contracted domain — and the only ``require`` frames the grouped reading
(``grouped = true → eachValid entries``: some point is named, and no single group
names a point twice). THREE load-bearing top-level ``ensures`` clauses:

    grouped = true  →  result = Except.ok (arrayForm entries)
    grouped = false → explicitForm entries.flatten = true
                        → result = Except.ok entries.flatten
    grouped = false → explicitForm entries.flatten = false
                        → result = Except.error ()

Clause 1 is doubly load-bearing: the SUCCESS constructor (``Except.ok``, not the
rejection ``Except.error``) — the definedness facet, the behaviour at issue for
groups that share a point — and the VALUE ``arrayForm entries``, the
left-to-right composite (position ``i`` holds the image of ``i``). Clauses 2 and
3 pin the OTHER reading in both directions: a flat argument that really is an
explicit list form (each point below its own count named exactly once) is handed
back unchanged, and one that is not is REFUSED. Because ``grouped`` is free,
those two clauses are reachable, and the interaction between the readings — a
repeat is refused for the flat reading and composed for the grouped one — is a
consequence of clauses 1 and 3 rather than of any precondition.

WHY THE FLAT READING IS MODELED AS ``entries.flatten``. The real argument list
enters the routine as a flat list of points on that reading; the two places that
consume it (the repeat/coverage screen and the returned explicit form) depend on
the flattened points only, so every ``entries`` with the same ``entries.flatten``
behaves identically and the single-group encoding ``[ps]`` is the canonical
representative. Carrying the flat reading through the SAME binder is what makes
``grouped`` free without adding a second argument the real routine does not have.

Because the whole composition is encapsulated in the frozen ``pure`` region
(``arrayForm`` / ``composePoint`` / ``cycleStep``), a rival that "computes the
wrong permutation" is expressed here NOT by re-implementing the fold (that region
is frozen) but by returning a DIFFERENT list — a reordering, truncation, or
identity fill of the frozen ``arrayForm`` — or by returning the rejection
constructor. Each such rival contradicts a load-bearing clause on a concrete
input, refuted by a machine-checked ``witness``.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * COMPOSITION-PIN attacks (nagini's drop-second-swap, wrong-order, skip-first,
    skip-last, identity-fill) — ALL apply. On the nagini carrier each is a
    per-point mis-computation of ``swap_val(swap_val(i,a,b),c,d)``; here the
    frozen ``arrayForm`` IS that composite, so each rival returns a list that
    differs from ``arrayForm entries`` on the mishandled point(s). Ported as
    list-level reshapes of the frozen ``arrayForm`` (reverse the group order,
    drop a group, set a boundary position back to the identity, return the raw
    identity range).
  * PREPATCH / rejected-composition (nagini's rej-disjoint-only, which mirrors
    model_prepatch) — applies and is one of the two sharpest DEFINEDNESS attacks.
    The pre-existing code refuses any argument whose flattened points repeat,
    even across distinct groups; modeled here as returning ``Except.error ()``
    there, which clause 1's SUCCESS-constructor demand forbids.
  * PARTIAL-DOMAIN / DEAD-GUARD attacks on the OTHER reading — apply, and this is
    the family the battery is now built around (see the REJECT-LANE note below).
    A rival may keep clause 1 satisfied and yet refuse nothing on the flat
    reading, refuse it only for long arguments, refuse it under a conjunct that
    is unsatisfiable, or refuse EVERY flat argument. Clauses 2 and 3 are what
    close each of those, and each is attacked here.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini surface has
    no read-only fractional-permission input in any event (its docstring says so);
    Lean and Velvet are referentially transparent — no heap, no aliasing, no
    fractional permission, no ``mut`` binder. Not fabricated.
  * DIVERGENCE / non-termination - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
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
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.
  * UNGROUNDED-ORACLE ECHO — applies in ONE direction only. The ``axioms`` region
    is EMPTY (the composition is modeled DEEPLY: ``arrayForm`` is an A-reference
    validated == the real library routine by G-AX, not a consumed axiom), so
    there is no opaque answer-key to echo. What a rival CAN do is answer BOTH
    readings with the grouped reading's answer, discharging clause 1 while doing
    none of the other reading's work; two rivals below do exactly that
    (``rej-grouped-answer-always``, ``rej-flat-composed-echo``).

REJECT-LANE NOTE (why the flat-reading rivals dominate the battery). Six of the
rivals below (``rej-repeat-guard-dead-conjunct``, ``-only-when-long``,
``-deleted``, ``-polarity``, ``rej-refuse-every-flat``,
``rej-grouped-answer-always``) are impls that an EARLIER form of this spec — one
that pinned the grouped reading only and fenced the other reading off behind a
precondition — ACCEPTED. Each was measured: its faithful refined patch is applied
to the gold-patched worktree and the official FAIL_TO_PASS test ``test_args`` is
run. All six FAIL it (see each case's ``refinement`` for the observed failure),
so each was a genuine ``verify ⇏ correct`` hole. Clauses 2 and 3 are what reject
them now, which is why the reject lane is weighted toward that facet rather than
toward more value-reshapes of the composite.

WITNESS PLACEMENT. Each reject case carries a Lean ``witness`` proving the rival
violates a load-bearing clause at ONE concrete input, checked in a file whose
``prove_correct`` block is stripped (so no tactic script can mask the verdict).
The spec is a ``method`` CONTRACT, not a bare predicate, so the witness reaches
the post-image through Velvet's own tester machinery:
``buildExplicitFormTester entries grouped = false`` says the extracted program's
result violates the postcondition at that concrete input. Each witness was
independently rebuilt during the repair: against the rival (exit 0), against the
frozen solution (exit 1, failing with ``Tactic `decide` proved that the
proposition ... is false`` — a SEMANTIC refutation, not a missing identifier or a
stuck reduction), and, as a control, the OPPOSITE claim
(``buildExplicitFormTester [[0,1],[0,2]] true = true``) against the frozen
solution, which BUILDS (exit 0) — so ``decide`` genuinely reduces on this carrier
and gold's exit code carries information rather than being the stuck-reduction
artifact the gate screens for. The tester short-circuits to ``true`` when the
``require`` is false, so every ``grouped = true`` witness input satisfies
``eachValid``; the ``grouped = false`` witnesses satisfy the require vacuously
(it is guarded by ``grouped = true``), which is exactly the freedom the repair
introduced — under the earlier spec those inputs were inexpressible. The result
carrier ``Except Unit (List Nat)`` needs a ``DecidableEq`` that
``prove_postcondition_decidable_for`` does not synthesize on its own, so each
witness first ``deriving instance DecidableEq for Except`` — an instance, not an
assumption (no ``axiom`` / ``sorry`` / ``native_decide``), so the frozen solution
still rejects each witness. The precondition (a guarded bounded ∀) needs its own
decidability tactic (``unfold eachValid; infer_instance``), supplied in the
tester preamble. Every witness input is concrete and small, so both testers
reduce under ``decide``. The reject witnesses probe TWELVE DISTINCT inputs across
BOTH values of ``grouped`` (see the per-case ``rationale``), so neither binder is
pinned across the reject lane.

ADVERSARIAL AUDIT (independent, post-port). An earlier audit pass wrote seven new
wrong impls the battery did not contain, aimed at what the shipped rivals leave
unattacked — a length truncation (``(arrayForm entries).take (listSize entries -
1)``), a length extension (``arrayForm entries ++ [0]``), a group FILTER that
drops singleton groups (so the largest mentioned point loses its slot), an order
error conditioned on group count (correct for ``≤ 2`` groups, reversed above
that), and three on the definedness facet (error when the input has more than one
group; error unconditionally; error when the composite is the identity). ALL
SEVEN were REJECTED; the last is shipped below as
``rej-error-on-identity-composite``. Five NEW correct reshapes were also written
and all were provable, two of which are shipped below as positives. The
admissibility case was probed by rebuilding it with a FALSE arithmetic claim
(``arrayForm [[0,1],[0,2]] = [2,0,1]``): it FAILED to verify, so the shipped
assert is load-bearing rather than decoration cleared by its retuned proof.

AXIOM lane: dropped (the gate ignores ``AXIOM_TESTS``). The nagini sibling ships
two G-AX probes for the ``arrayForm`` A-reference; that obligation belongs to
G-AX and is discharged by this bundle's ``axiom_check.py``, not here.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12481"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the ENTIRE frozen impl region (both markers inclusive),
# ---- unique in Solution.lean. Every variant replaces it wholesale, so edits are
# ---- confined to the impl region and same_spec holds by construction. The
# ---- markers are re-emitted by each builder so the region stays well-formed.
_CANON = (
    "    let temp := entries.flatten\n"
    "    if !pointsDistinct temp && !grouped then\n"
    "      return Except.error ()\n"
    "    else\n"
    "      if !grouped && !rangeCovered temp then\n"
    "        return Except.error ()\n"
    "      else\n"
    "        if grouped then\n"
    "          return Except.ok (arrayForm entries)\n"
    "        else\n"
    "          return Except.ok temp"
)
_IMPL = "    -- impl-start\n" + _CANON + "\n    -- impl-end"
assert _BASE.count(_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- proof-region anchor. Correct reshapes that change the impl's syntactic form
# ---- may retune THIS block (it is elided from the spec view); rivals leave it as
# ---- the frozen script. The witness, not the module build, is what attributes a
# ---- rejection to the spec.
_PROOF = ("prove_correct buildExplicitForm by\n"
          "  loom_solve\n"
          "  all_goals simp_all [explicitForm]")
assert _BASE.count(_PROOF) == 1, "frozen proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with the impl region replaced by `body`
    (markers re-emitted). Edits confined to the impl region => same_spec."""
    new = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_BASE, _IMPL, new)


def _impl_reproved(body, new_proof):
    """Impl region replaced AND the proof retuned (for correct reshapes whose new
    impl form the frozen script alone does not close, or that add an in-region
    assert)."""
    return _swap(_impl(body), _PROOF, new_proof)


def _grouped_answer(expr):
    """The frozen body with ONLY the grouped reading's returned VALUE changed.
    Used by the composition-pin rivals: the other reading stays correct, so the
    rejection is attributable to clause 1 and not to collateral damage."""
    return _swap(_CANON, "Except.ok (arrayForm entries)", f"Except.ok ({expr})")


def _flat_answer(expr):
    """The frozen body with ONLY the flat reading's returned VALUE changed."""
    return _swap(_CANON, "Except.ok temp", f"Except.ok ({expr})")


def _repeat_guard(cond):
    """The frozen body with ONLY the repeat screen's CONDITION changed. Used by
    the partial-domain / dead-conjunct / polarity rivals."""
    return _swap(_CANON, "if !pointsDistinct temp && !grouped then",
                 f"if {cond} then")


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; derives DecidableEq for the `Except` result carrier and the
# ---- decidability of the guarded `eachValid` precondition. Checked in a file
# ---- whose `prove_correct` block has been stripped.
_WITNESS_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for buildExplicitForm\n"
    "prove_precondition_decidable_for buildExplicitForm by\n"
    "  unfold eachValid; infer_instance\n"
    "prove_postcondition_decidable_for buildExplicitForm\n"
    "derive_tester_for buildExplicitForm\n\n"
)


def _witness(call):
    return _WITNESS_PREAMBLE + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Every clause is now reachable
    # (`grouped` is free), so a positive can no longer be "drop the guard": it
    # has to answer both readings. These three restructure the body around the
    # same observable behaviour — hand the flat reading its own list back through
    # a different expression, merge the two screens into one, and dispatch on the
    # reading first. The nagini positives are a single-loop direct-compose build
    # and a fused-two-phase build ("restructure the body, keep the composed
    # value"); this carrier has no loop (the composition is the frozen
    # `arrayForm`), so these are the analogous cheapest reshapes.
    # =====================================================================
    {
        "id": "pos-flat-dedup",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            _flat_answer("temp.dedup"),
            "prove_correct buildExplicitForm by\n"
            "  loom_solve\n"
            "  all_goals simp_all [explicitForm, pointsDistinct, "
            "List.dedup_eq_self]",
        ),
        "rationale": (
            "CORRECT reshape of the flat reading: return `temp.dedup` instead of "
            "`temp`. On every input the flat clauses reach, `pointsDistinct temp` "
            "already holds, and de-duplicating a list with no duplicates is the "
            "identity — so the returned value is `entries.flatten` exactly and "
            "clause 2 still discharges. The proof needs `List.dedup_eq_self` to "
            "see that (in-region retune, elided from the spec view). This is the "
            "port of nagini's single-loop direct-compose positive: same "
            "observable answer computed by a different expression. If it fails "
            "=> SPEC-TOO-STRONG (the spec would be demanding a particular "
            "syntactic form of the returned list rather than its value)."
        ),
    },
    {
        "id": "pos-merged-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    if !grouped && !explicitForm temp then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if grouped then\n"
            "        return Except.ok (arrayForm entries)\n"
            "      else\n"
            "        return Except.ok temp"
        ),
        "rationale": (
            "CORRECT reshape that FUSES the two screens into the single test "
            "`!grouped && !explicitForm temp` (the conjunction of the repeat and "
            "coverage screens is exactly `!explicitForm`), turning a two-stage "
            "cascade into one branch. Same refusal set, same answers, so all "
            "three clauses discharge under the frozen proof script. The port of "
            "nagini's fused-two-phase positive (same computation, different "
            "control shape). If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-dispatch-on-grouped",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if grouped then\n"
            "      return Except.ok (arrayForm entries)\n"
            "    else\n"
            "      if explicitForm entries.flatten then\n"
            "        return Except.ok entries.flatten\n"
            "      else\n"
            "        return Except.error ()"
        ),
        "rationale": (
            "CORRECT reshape that dispatches on the READING first and screens "
            "second — the opposite nesting order to the frozen body, and it never "
            "binds the flat list to a local at all. It also states the flat "
            "screen POSITIVELY (`if explicitForm ... then ok`) where the frozen "
            "body states it negatively, so the polarity of the branch is not "
            "something the spec can be depending on. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini admissibility control asserts, in-region on the
    # gold body, that the precondition ADMITS a normal F2P-shaped input and that a
    # non-degenerate in-range composed image is reachable (so the postcondition is
    # satisfiable, not vacuous). Ported the same way, and EXTENDED to the second
    # reading: the earlier form of this spec admitted only the grouped reading, so
    # an admissibility control that probes only that reading would not notice a
    # precondition that had quietly re-excluded the other one.
    # =====================================================================
    {
        "id": "admiss-both-readings",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (eachValid ([[0,1],[0,2]] : List (List Nat)) ∧\n"
            "       arrayForm [[0,1],[0,2]] = [1,2,0] ∧\n"
            "       arrayForm [[0,1],[0,2]]\n"
            "         ≠ List.range (listSize ([[0,1],[0,2]] : List (List Nat))) ∧\n"
            "       explicitForm [0,2,1] = true ∧\n"
            "       explicitForm [1,1,0] = false ∧\n"
            "       explicitForm [4,5] = false))\n"
            + _CANON,
            "prove_correct buildExplicitForm by\n"
            "  loom_solve\n"
            "  all_goals simp_all [explicitForm, eachValid]\n"
            "  all_goals decide",
        ),
        "rationale": (
            "positive-control admissibility on BOTH readings. Grouped: the "
            "precondition admits the discriminating input `[[0,1],[0,2]]` (two "
            "groups that SHARE a point — the input at issue) AND its composite is "
            "the concrete non-degenerate `[1,2,0]`, which is NOT the identity "
            "range `[0,1,2]`, so clause 1 pins a genuine reachable non-identity "
            "rearrangement there rather than collapsing to the identity. Flat: "
            "`explicitForm [0,2,1] = true` witnesses that clause 2's hypothesis "
            "is SATISFIABLE (so the hand-it-back obligation is reachable and not "
            "vacuous), while `explicitForm [1,1,0] = false` and "
            "`explicitForm [4,5] = false` witness that clause 3's hypothesis is "
            "satisfiable in its two distinct ways (a repeated point, and a gap "
            "below the count of distinct points) — so the refusal obligation is "
            "reachable on both. The gold body is kept verbatim so the method's own "
            "obligations also discharge; the proof clears only the extra assert "
            "goal. If the assert cannot discharge => PRECOND-TOO-STRONG."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real counterpart
    # would NOT resolve the F2P test. For the six flat-reading rivals the
    # refinement argument is not an argument but a MEASUREMENT: the refined patch
    # was applied to the gold-patched worktree and `test_args` was run.
    # =====================================================================

    # ---- (1) THE HOLE, in its plainest form: a repeat screen whose second
    # ---- conjunct cannot hold, so nothing is ever refused on the flat reading.
    {
        "id": "rej-repeat-guard-dead-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_repeat_guard("!pointsDistinct temp && !grouped && grouped")),
        "refinement": (
            "the faithful real patch adds a conjunct to the repeat screen that "
            "cannot hold together with the one already there (`and not is_cycle "
            "and is_cycle`), so no argument is ever refused for repeating a "
            "point. MEASURED: with that patch applied to the gold-patched "
            "worktree, `test_args` FAILS — `AssertionError: DID NOT RAISE` on the "
            "retained assertion that a flat argument with a repeated point is "
            "rejected. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 3: on `[[1,1,0]]` with `grouped = false` the "
            "flattened argument repeats a point, so `explicitForm = false` and "
            "the clause demands `Except.error ()`; the rival's screen is dead and "
            "it returns `Except.ok [1,1,0]`. If it verified => SPEC-TOO-WEAK, and "
            "this is the exact shape of the hole the repair closes: an earlier "
            "form of this spec fenced this reading off behind a precondition and "
            "ACCEPTED this rival."
        ),
        "witness": _witness("buildExplicitFormTester [[1,1,0]] false"),
    },

    # ---- (2) PARTIAL-DOMAIN: the screen bites only on long arguments.
    {
        "id": "rej-repeat-guard-only-when-long",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_repeat_guard(
            "!pointsDistinct temp && !grouped && decide (3 < temp.length)")),
        "refinement": (
            "the faithful real patch refuses a repeated point only once the "
            "argument is longer than three positions (`and 3 < len(temp)`), so "
            "short arguments with a repeat are accepted. MEASURED: `test_args` "
            "FAILS with `AssertionError: DID NOT RAISE` (the retained assertion "
            "uses a 3-element argument). It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 3, refuted at `[[1,1,0]] false` — a "
            "PARTIAL-DOMAIN attack: the rival agrees with gold on every long "
            "argument and diverges only on the short sub-domain, so a spec that "
            "pinned the refusal only asymptotically would miss it. Clause 3 is "
            "unconditional in the argument's length, so it bites. If it verified "
            "=> SPEC-TOO-WEAK (the refusal would hold only above a length "
            "threshold)."
        ),
        "witness": _witness("buildExplicitFormTester [[1,1,0]] false"),
    },

    # ---- (3) The screen deleted outright.
    {
        "id": "rej-repeat-guard-deleted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    if !grouped && !rangeCovered temp then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if grouped then\n"
            "        return Except.ok (arrayForm entries)\n"
            "      else\n"
            "        return Except.ok temp"
        ),
        "refinement": (
            "the faithful real patch DELETES the repeat screen and keeps only the "
            "coverage screen, so an argument that repeats a point but still names "
            "every point below its distinct count is accepted. MEASURED: "
            "`test_args` FAILS with `AssertionError: DID NOT RAISE`. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause 3 at `[[1,1,0]] false`: the flattened argument "
            "`[1,1,0]` PASSES the coverage screen (its two distinct points are "
            "`{0,1}` and both are named), so the surviving screen does not catch "
            "it and the rival returns `Except.ok [1,1,0]` where the clause "
            "demands refusal. Distinguishes the two conjuncts of `explicitForm`: "
            "coverage alone is not enough. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("buildExplicitFormTester [[1,1,0]] false"),
    },

    # ---- (4) BOUNDARY TOKEN SWAP: the screen's reading test negated.
    {
        "id": "rej-repeat-guard-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_repeat_guard("!pointsDistinct temp && grouped")),
        "refinement": (
            "the faithful real patch drops one token: `and not is_cycle` becomes "
            "`and is_cycle`, so the repeat refusal lands on the grouped reading "
            "instead of the flat one — the transcription slip closest to the gold "
            "edit. MEASURED: `test_args` FAILS with `ValueError: there were "
            "repeated elements.` raised on the very assertion that a grouped "
            "argument with a shared point must CONSTRUCT. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 1 at `[[0,1],[0,2]] true` (the discriminating "
            "input): the two groups share point 0, so the flattened argument "
            "repeats and the swapped screen fires, returning `Except.error ()` "
            "where clause 1 demands `Except.ok [1,2,0]`. A ONE-TOKEN rival, so it "
            "measures whether the two readings are pinned SEPARATELY rather than "
            "symmetrically. If it verified => SPEC-TOO-WEAK (the polarity of the "
            "reading test would be free)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,1],[0,2]] true"),
    },

    # ---- (5) OVER-REFUSAL on the other reading: every flat argument refused.
    {
        "id": "rej-refuse-every-flat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    let _ := temp\n"
            "    if !grouped then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      return Except.ok (arrayForm entries)"
        ),
        "refinement": (
            "the faithful real patch refuses EVERY argument on the flat reading "
            "(`if not is_cycle: raise`), keeping only the grouped one. MEASURED: "
            "the patched library does not even IMPORT — "
            "`sympy/combinatorics/polyhedron.py` builds its module-level "
            "permutations from flat arguments and gets `ValueError: there were "
            "repeated elements.` at import, so `test_args` and all seven "
            "PASS_TO_PASS tests are unrunnable. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 2 at `[[0,2,1]] false`: the flattened argument "
            "`[0,2,1]` IS an explicit list form (three distinct points, all of "
            "`0,1,2` named), so the clause demands `Except.ok [0,2,1]` and the "
            "rival returns `Except.error ()`. The OVER-REFUSAL direction — the "
            "one a spec that only ever demands refusals cannot see. Under the "
            "earlier form of this spec this input was not even expressible. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("buildExplicitFormTester [[0,2,1]] false"),
    },

    # ---- (6) ORACLE ECHO across the readings: answer everything the grouped way.
    {
        "id": "rej-grouped-answer-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return Except.ok (arrayForm entries)"),
        "refinement": (
            "the faithful real patch treats every argument as grouped: no screen "
            "at all, and the answer is always the composite of the argument read "
            "as groups. MEASURED: `test_args` FAILS with `AssertionError: DID NOT "
            "RAISE`. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 3 at `[[1,1,0]] false`: the rival discharges "
            "clause 1 perfectly and answers the OTHER reading with the grouped "
            "reading's answer, doing none of that reading's work — the echo "
            "family, and the cheapest impl that an earlier form of this spec "
            "accepted. Clause 3 demands refusal for `[1,1,0]`, the rival returns "
            "`Except.ok`. If it verified => SPEC-TOO-WEAK (only one of the two "
            "readings would be specified at all)."
        ),
        "witness": _witness("buildExplicitFormTester [[1,1,0]] false"),
    },

    # ---- (7) OVER-APPROXIMATION: the coverage obligation dropped.
    {
        "id": "rej-coverage-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    if !pointsDistinct temp && !grouped then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if grouped then\n"
            "        return Except.ok (arrayForm entries)\n"
            "      else\n"
            "        return Except.ok temp"
        ),
        "refinement": (
            "the faithful real patch keeps the repeat screen but DELETES the "
            "coverage screen (`Integers 0 through n must be present`), so a flat "
            "argument that names points with a gap below its distinct count is "
            "accepted as if it were an explicit list form. MEASURED: `test_args` "
            "FAILS with `AssertionError: DID NOT RAISE` on the retained "
            "assertion that such an argument is rejected. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 3 at `[[4,5]] false`: `[4,5]` has no repeat, so "
            "the surviving screen passes it, but it names neither 0 nor 1 and so "
            "`explicitForm = false` — the clause demands refusal and the rival "
            "returns `Except.ok [4,5]`. An OVER-APPROXIMATION attack: the rival's "
            "accepted set strictly contains gold's. It also shows the second "
            "conjunct of `explicitForm` is load-bearing on its own. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("buildExplicitFormTester [[4,5]] false"),
    },

    # ---- (8) EXPLOITS THE REPAIR'S OWN NEW FREEDOM: the coverage screen, which
    # ---- only the repaired spec mentions at all, applied to BOTH readings.
    {
        "id": "rej-coverage-on-grouped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    if !pointsDistinct temp && !grouped then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if !rangeCovered temp then\n"
            "        return Except.error ()\n"
            "      else\n"
            "        if grouped then\n"
            "          return Except.ok (arrayForm entries)\n"
            "        else\n"
            "          return Except.ok temp"
        ),
        "refinement": (
            "the faithful real patch drops the `not is_cycle` qualifier from the "
            "COVERAGE screen, applying it to both readings, so a grouped argument "
            "whose points do not start at 0 is refused. MEASURED: `test_args` "
            "FAILS with `ValueError: Integers 0 through 2 must be present.` — "
            "raised where a grouped argument should have composed. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause 1 at `[[4,5]] true`: the grouped reading of "
            "`[[4,5]]` is a well-formed group (the precondition admits it) whose "
            "composite is `[0,1,2,3,5,4]`, but its flattened points skip 0..3 so "
            "the un-qualified coverage screen fires and the rival returns "
            "`Except.error ()`. This rival targets the freedom the REPAIR itself "
            "introduced — `rangeCovered` is a new spec-view symbol, and a repair "
            "that had pinned it for only one reading, or had pinned it as a "
            "global well-formedness condition, would accept this. Clause 1's "
            "unconditional success demand is what refuses it. If it verified => "
            "SPEC-TOO-WEAK (the repair would have imported a NEW over-refusal)."
        ),
        "witness": _witness("buildExplicitFormTester [[4,5]] true"),
    },

    # ---- (9) ORACLE ECHO in the other direction: the flat reading answered with
    # ---- the composite of its own argument.
    {
        "id": "rej-flat-composed-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    if !pointsDistinct temp && !grouped then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if !grouped && !rangeCovered temp then\n"
            "        return Except.error ()\n"
            "      else\n"
            "        return Except.ok (arrayForm entries)"
        ),
        "refinement": (
            "the faithful real patch keeps both screens exactly but computes the "
            "answer the same way on both readings: it composes the argument "
            "(`c = Cycle(); c = c(*args); aform = c.list()`) instead of taking "
            "the flat argument as the explicit form it already is. MEASURED: the "
            "patched library does not IMPORT — `polyhedron.py` builds its "
            "module-level permutations from flat arguments and gets "
            "`KeyError: (0, 3, 2, 5)` once they come back permuted, so "
            "`test_args` and all seven PASS_TO_PASS tests are unrunnable. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 2 at `[[0,2,1]] false`: `[0,2,1]` passes both "
            "screens, so clause 2 demands it back UNCHANGED; the rival returns "
            "the composite `[2,0,1]` instead. The echo family in its sharpest "
            "form — the rival's answer is a total function of the argument and "
            "agrees with gold whenever the flat argument happens to be an "
            "involution, so only a clause that pins the flat answer as the "
            "argument ITSELF rejects it. If it verified => SPEC-TOO-WEAK (clause "
            "2's value would be unpinned)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,2,1]] false"),
    },

    # ---- (10) TRUNCATION on the flat reading.
    {
        "id": "rej-flat-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_flat_answer("temp.dropLast")),
        "refinement": (
            "the faithful real patch returns the flat argument one position short "
            "(`aform = list(args)[:-1]`) — the off-by-one on the reading the "
            "screens do not touch. MEASURED: the patched library does not IMPORT "
            "— `polyhedron.py` raises `ValueError: Permutation size unequal to "
            "number of corners.` at module level, so `test_args` and all seven "
            "PASS_TO_PASS tests are unrunnable. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 2 at `[[0,2,1]] false`: the clause pins the "
            "returned list to `entries.flatten` exactly, so dropping its last "
            "position (`[0,2]`) contradicts it — the LENGTH facet of clause 2, "
            "which no other rival attacks. If it verified => SPEC-TOO-WEAK (the "
            "flat answer's length would be free)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,2,1]] false"),
    },

    # ---- (11) PREPATCH / rejected-composition (nagini rej-disjoint-only ==
    # ---- model_prepatch): refuse a repeat on BOTH readings.
    {
        "id": "rej-prepatch-refuse-any-repeat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_repeat_guard("!pointsDistinct temp")),
        "refinement": (
            "this IS the pre-existing behaviour (the exact skeleton of "
            "Solution_prepatch.lean): a point repeated anywhere in the flattened "
            "argument is refused, even when the repeat only spans distinct groups "
            "of the grouped reading. Its faithful real counterpart is the "
            "unpatched routine. MEASURED: `test_args` FAILS with `ValueError: "
            "there were repeated elements.` raised on the added assertion that "
            "two groups sharing a point must construct the composite. It would "
            "NOT resolve — this is the behaviour at issue."
        ),
        "rationale": (
            "REJECT from clause 1 at `[[0,1],[0,2]] true`: the groups share point "
            "0, so `pointsDistinct (flatten) = false` and the rival returns "
            "`Except.error ()` where the clause demands `Except.ok [1,2,0]` — the "
            "DEFINEDNESS facet, and the G-DIFF discriminator. If it verified => "
            "SPEC-TOO-WEAK (the whole point of the change would go unnoticed)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,1],[0,2]] true"),
    },

    # ---- WRONG ORDER (nagini rej-wrong-order): compose the groups right-to-left --
    {
        "id": "rej-wrong-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_grouped_answer("arrayForm entries.reverse")),
        "refinement": (
            "the faithful real patch composes the grouped mappings in reverse "
            "(right-to-left) order. For the discriminating input `[[0,1],[0,2]]` "
            "this yields the composite `[2,0,1]` instead of `[1,2,0]`, so the "
            "failing equality assertion that pins the constructed permutation "
            "observes the wrong array and still fails — it would NOT resolve. "
            "(The two groups do not commute.)"
        ),
        "rationale": (
            "REJECT from clause 1: the impl proves `... (arrayForm "
            "entries.reverse)`, which differs whenever the group order matters "
            "(left-to-right composition is the load-bearing VALUE). Refuted at "
            "`[[0,1],[0,2]] true` (gold `[1,2,0]` vs rival `[2,0,1]`). If it "
            "verified => SPEC-TOO-WEAK (composition order unpinned)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,1],[0,2]] true"),
    },

    # ---- DROP A GROUP (nagini rej-drop-second-swap) ----
    {
        "id": "rej-drop-last-group",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_grouped_answer("arrayForm entries.dropLast")),
        "refinement": (
            "the faithful real patch composes only the leading groups, never "
            "applying the trailing one — the analogue of nagini's "
            "drop-the-second-swap. For `[[0,2],[1,2]]` it composes only `(0 2)` "
            "giving `[2,1,0]` instead of the full `[1,2,0]`, so the failing "
            "equality assertion observes the wrong array and does NOT resolve. "
            "Correct only when the trailing group moves nothing already displaced."
        ),
        "rationale": (
            "REJECT from clause 1: the impl yields `... (arrayForm "
            "entries.dropLast)`, dropping the last group's contribution. Refuted "
            "at `[[0,2],[1,2]] true` (gold `[1,2,0]` vs rival `[2,1,0]`) — a "
            "DISTINCT input from the order rival, so the `entries` binder is "
            "varied across the reject lane. If it verified => SPEC-TOO-WEAK (a "
            "group is ignored)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,2],[1,2]] true"),
    },

    # ---- SKIP THE FIRST POSITION (nagini rej-skip-first-pos) ----
    {
        "id": "rej-skip-first-pos",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_grouped_answer("(arrayForm entries).set 0 0")),
        "refinement": (
            "the faithful real patch is an off-by-one that leaves the first point "
            "at its identity image while composing the rest. For `[[0,2]]` point "
            "0 should map to 2 but stays 0, giving `[0,1,0]` instead of "
            "`[2,1,0]`, so the failing equality assertion observes the wrong "
            "first entry and does NOT resolve. Correct only when the composite "
            "already fixes point 0."
        ),
        "rationale": (
            "REJECT from clause 1: the impl yields `(arrayForm entries).set 0 0`, "
            "wrong at position 0 whenever the composite moves point 0 "
            "(partial-domain: first element). Refuted at `[[0,2]] true` (gold "
            "`[2,1,0]` vs rival `[0,1,0]` — only position 0 is overwritten, so "
            "position 2 still carries the composed image 0). If it verified => "
            "SPEC-TOO-WEAK (the first position is unpinned)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,2]] true"),
    },

    # ---- SKIP THE LAST POSITION (nagini rej-skip-last-pos) ----
    {
        "id": "rej-skip-last-pos",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_grouped_answer(
            "(arrayForm entries).set (listSize entries - 1) (listSize entries - 1)")),
        "refinement": (
            "the faithful real patch is an off-by-one truncating the fill one "
            "short, leaving the last point at its identity image. For `[[1,2]]` "
            "point 2 should map to 1 but stays 2, giving `[0,2,2]` instead of "
            "`[0,2,1]`, so the failing equality assertion observes the wrong last "
            "entry and does NOT resolve. Correct only when the composite already "
            "fixes the last point."
        ),
        "rationale": (
            "REJECT from clause 1: the impl yields `(arrayForm entries).set "
            "(listSize entries - 1) (listSize entries - 1)`, wrong at the last "
            "position whenever the composite moves it (partial-domain: last "
            "element). Refuted at `[[1,2]] true` (gold `[0,2,1]` vs rival "
            "`[0,2,2]`) — a distinct point from skip-first. If it verified => "
            "SPEC-TOO-WEAK (the last position is unpinned)."
        ),
        "witness": _witness("buildExplicitFormTester [[1,2]] true"),
    },

    # ---- IDENTITY / SHAPE-ONLY FILL (nagini rej-identity-range-fill) ----
    {
        "id": "rej-identity-fill",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_grouped_answer("List.range (listSize entries)")),
        "refinement": (
            "the faithful real patch returns the identity list of the right size "
            "regardless of the groups. For `[[0,1]]` it returns `[0,1]` (the "
            "identity) instead of `[1,0]`, so the failing equality assertion "
            "observes the identity where the exchange was expected and does NOT "
            "resolve. Correct only when the composite is itself the identity."
        ),
        "rationale": (
            "REJECT from clause 1: probes whether the SHAPE facet (right length, "
            "values in range — which `List.range (listSize entries)` satisfies) "
            "could be mistaken for the spec. The clause pins the VALUE, so the "
            "identity is forbidden whenever the composite is non-trivial. Refuted "
            "at `[[0,1]] true` (gold `[1,0]` vs rival `[0,1]`). If it verified => "
            "SPEC-TOO-WEAK (supporting case: the composition, not just the shape, "
            "is load-bearing)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,1]] true"),
    },

    # ---- DEFINEDNESS on a predicate ORTHOGONAL to either screen ----
    # The grouped reading's definedness facet is otherwise attacked only through
    # the repeat screen — the same predicate the frozen body's own screen
    # mentions. This rival rejects on the composite happening to be the identity,
    # at an input whose flattened form ALSO repeats, so it reaches a sub-domain no
    # other case in the battery touches.
    {
        "id": "rej-error-on-identity-composite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let temp := entries.flatten\n"
            "    if !pointsDistinct temp && !grouped then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if !grouped && !rangeCovered temp then\n"
            "        return Except.error ()\n"
            "      else\n"
            "        if grouped then\n"
            "          if arrayForm entries = List.range (listSize entries) then\n"
            "            return Except.error ()\n"
            "          else\n"
            "            return Except.ok (arrayForm entries)\n"
            "        else\n"
            "          return Except.ok temp"
        ),
        "refinement": (
            "the faithful real patch keeps a refusal branch for grouped input "
            "whose composite turns out to be the identity mapping — it declines "
            "to build the trivial permutation instead of returning it. For "
            "`[[0,1],[0,1]]` (a group repeated, whose composite is the identity — "
            "the exact input named in the report) it raises where the post-change "
            "behaviour constructs the identity permutation, so the failing "
            "assertion — which compares a constructed permutation against an "
            "expected one rather than expecting a raise — observes an exception "
            "and does NOT resolve. Correct only on inputs whose composite moves "
            "at least one point."
        ),
        "rationale": (
            "REJECT from clause 1: it demands the SUCCESS constructor on the "
            "WHOLE grouped domain, including the sub-domain where the composite "
            "is the identity. The rival returns `Except.error` exactly there. "
            "Refuted at `[[0,1],[0,1]] true` (gold returns `Except.ok [0,1]`, the "
            "rival errors) — the only input in the battery where the composite is "
            "the identity, so the definedness facet is attacked on a predicate "
            "ORTHOGONAL to either screen rather than only through one. If it "
            "verified => SPEC-TOO-WEAK (the success constructor would be pinned "
            "only on the non-degenerate sub-domain)."
        ),
        "witness": _witness("buildExplicitFormTester [[0,1],[0,1]] true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The nagini sibling has 9 SPEC cases over ONE function `compose_cycles(n, a, b,
# c, d) -> List[int]` (2 soundness positives, 1 admissibility, 6 uniqueness
# rivals) plus 2 AXIOM_TESTS. Its carrier is the array form of the composition of
# TWO fixed two-element swaps `(a b)` then `(c d)` over `n` points, under a PSeq
# value abstraction; its load-bearing clause is the per-point composition pin
# `ToSeq(Result())[i] == swap_val(swap_val(i,a,b),c,d)`.
#
# This velvet bundle models the SAME behavior at a more general and more faithful
# level: `buildExplicitForm (entries) (grouped)` composes an ARBITRARY grouped
# argument `entries : List (List Nat)` left-to-right (the real repo shape) OR
# takes the same argument as the flat explicit form it already is, and
# encapsulates the composition in the frozen `pure` region as `arrayForm` (an
# A-reference validated == the real library routine by G-AX). The nagini
# "composition pin" + "range clause" + "shape/len clause" collapse into clause 1
# `result = Except.ok (arrayForm entries)`, which pins the success constructor
# (definedness) AND the exact composite list (value+shape) at once; clauses 2 and
# 3 have no nagini counterpart because the nagini surface has no second reading.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-single-loop             -> pos-flat-dedup            RE-SHAPED
#   pos-fused-two-phase         -> pos-merged-guard          RE-SHAPED
#   (no nagini source)          -> pos-dispatch-on-grouped   ADDED
#   admiss-f2p-witness          -> admiss-both-readings      PORTED + EXTENDED
#   rej-drop-second-swap        -> rej-drop-last-group       PORTED
#   rej-wrong-order             -> rej-wrong-order           PORTED
#   rej-skip-first-pos          -> rej-skip-first-pos        PORTED
#   rej-skip-last-pos           -> rej-skip-last-pos         PORTED
#   rej-disjoint-only           -> rej-prepatch-refuse-any-repeat  PORTED
#   rej-identity-range-fill     -> rej-identity-fill         PORTED
#   (no nagini source)          -> rej-error-on-identity-composite ADDED
#   (no nagini source)          -> the SEVEN second-reading rivals ADDED
#   AXIOM_TESTS (2)             -> (none)                    DROPPED (G-AX's lane)
#
# 6 uniqueness rivals PORTED, admissibility PORTED and EXTENDED, 2 positives
# RE-SHAPED, 2 axiom probes DROPPED, and 9 cases ADDED (a third positive, the
# orthogonal-predicate definedness rival, and the seven rivals that attack the
# SECOND reading — the facet with no nagini counterpart at all).
#
# PORTED (6 rivals + admiss): each nagini rival is a per-point mis-computation of
#   the swap composition. Because the velvet composition is frozen inside the
#   `pure` region (a rival may not re-implement it — that would leave the impl
#   region and touch a frozen def), each is re-expressed as a LIST-LEVEL reshape
#   of the frozen `arrayForm` that produces the same wrong array on the same
#   sub-domain:
#     * drop-second-swap  -> drop the last GROUP (`arrayForm entries.dropLast`);
#     * wrong-order        -> compose groups reversed (`arrayForm entries.reverse`);
#     * skip-first / skip-last -> `.set` that boundary position back to identity;
#     * identity-range-fill -> return `List.range (listSize entries)`;
#     * disjoint-only (== model_prepatch) -> refuse any repeated point on BOTH
#       readings (the pre-existing screen), refuted by clause 1's success demand.
#   Each ported rival leaves the OTHER reading correct, so its rejection is
#   attributable to clause 1 rather than to collateral damage on clauses 2-3.
#   admiss is re-expressed as an in-region assert covering both readings.
# RE-SHAPED (2 positives): nagini's positives are a single-loop direct compose and
#   a fused-two-phase build ("restructure the body, keep the composed value"). The
#   velvet composition is a frozen def, not a loop, so the analogous cheapest
#   correct reshapes keep the observable answers and restructure the body: return
#   the flat reading's list through `.dedup` (identity where the clause applies),
#   or fuse the two screens into one `!explicitForm` test.
# DROPPED (2): the AXIOM_TESTS. The gate ignores AXIOM_TESTS; the `arrayForm`
#   A-reference soundness/containment obligation is G-AX's job and is discharged
#   by this bundle's axiom_check.py, not the G-PBT battery.
# VACUOUS classes (none present in nagini, so none fabricated):
#   * FRAME / permission-mutation — the nagini surface has no read-only fractional
#     input (its docstring states frame-mutation is N/A: every parameter is a
#     plain int and the only Acc is on the freshly-built Result). Referential
#     transparency here confirms it: no heap, no aliasing, no `mut` binder.
# DIVERGENCE / non-termination - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
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
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
#
# BINDER / CLAUSE / POINT COVERAGE. All THREE load-bearing clauses are DEFENDED
# (3 soundness positives + the two-reading admissibility control) and ATTACKED:
#   * clause 1 (grouped) — on its VALUE facet by five rivals (wrong-order,
#     drop-group, skip-first, skip-last, identity-fill) and on its
#     DEFINEDNESS/constructor facet by four (prepatch-refuse-any-repeat,
#     repeat-guard-polarity, coverage-on-grouped, error-on-identity-composite);
#   * clause 2 (flat, accept) — by three rivals (refuse-every-flat,
#     flat-composed-echo, flat-truncate), covering the refusal, value and length
#     facets of the hand-it-back obligation;
#   * clause 3 (flat, refuse) — by five rivals (repeat-guard dead-conjunct,
#     only-when-long, deleted, grouped-answer-always, coverage-dropped), covering
#     both conjuncts of `explicitForm` and three distinct ways a screen can fail
#     to bite.
# The `entries` binder is VARIED across TWELVE DISTINCT inputs (`[[0,1],[0,2]]`,
# `[[0,2],[1,2]]`, `[[0,2]]`, `[[1,2]]`, `[[0,1]]`, `[[0,1],[0,1]]`, `[[1,1,0]]`,
# `[[0,2,1]]`, `[[4,5]]` — the last three under both values of `grouped` where
# applicable) and the `grouped` binder takes BOTH values in the reject lane (8
# witnesses at `true`, 9 at `false`), which is the freedom the repair introduced:
# under the earlier form of this spec `grouped` was pinned by a `require` and
# every `false` witness above was vacuous. Coverage spans single-group and
# two-group inputs, disjoint / shared-point / COINCIDENT group pairs, boundary
# positions, the degenerate identity composite, a repeated point, and a gap below
# the count of distinct points (pts = 12).
#
# AXIOM_TESTS: dropped (the gate ignores this lane; see accounting above).
AXIOM_TESTS = []
