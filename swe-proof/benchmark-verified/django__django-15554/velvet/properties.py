"""properties.py — G-PBT falsification battery for django__django-15554 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct computeEligible`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a second subject that satisfies the spec). On this bundle that second
subject is NOT the frozen solution — its ``while`` loop makes ``decide``
unreducible, so its exit code discriminates nothing — but the declared
``witness_reference``; see the CARRIER NOTE, which measures why.

DEFENDED SURFACE (one contracted method):

  computeEligible (registry : List (Nat × EntryId)) (req : EntryId)
      (allowed : Option (List Nat)) (restricted : Bool) return (out : List Nat)
    ensures out = eligibleEntries req allowed restricted registry

The method walks an ordered registry of existing entries and returns the ids of
those the requested entry may SHARE, in registry order. The single load-bearing
``ensures`` pins ``out`` to the deep, fully-unfolded ``eligibleEntries`` — a
front-recursive fold over the registry whose per-entry decision is the pure
``entryEligible``. The ``axioms`` region is EMPTY: ``entryEligible`` /
``matchesStructural`` / ``matchesExact`` / ``allowedMember`` / ``restrictedMode``
are all transparent ``def``s over the method's own arguments, so there is NO
opaque answer-key oracle in the load-bearing clause — pinning ``out =
eligibleEntries …`` is grounded, not an echo.

WHICH CLAUSE / WHICH BINDERS. There is exactly one clause, C1 (``out =
eligibleEntries req allowed restricted registry``). It is a function of ALL FOUR
input binders — ``registry`` (each entry carries a ``structKey``, a ``refineTag``
and an id), ``req`` (the requested structKey/refineTag), ``allowed`` (the
allowance — ``none`` = all permitted, ``some l`` = only ids in ``l``), and
``restricted`` (the restricted-selection flag). The per-entry decision
``entryEligible`` composes two independently-attackable behaviours that the fix
turns on:

  * MODE SELECTION — restricted mode fires only when ``restricted`` AND a
    non-empty allowance is supplied (``restrictedMode``); otherwise the default
    mode is in force.
  * MATCH GRANULARITY — the DEFAULT mode requires an EXACT match (structural
    identity AND refinement tag), so two entries structurally identical but
    carrying different refinement tags are kept DISTINCT; the RESTRICTED mode
    requires only a STRUCTURAL match (refinement tag ignored). Plus the
    permission gate: default mode permits an entry when the allowance is absent
    OR lists its id; restricted mode requires the allowance to list its id.

The discriminating delta the F2P observes: in default mode the fixed behaviour
matches on the FULL identity (exact), where the pre-change behaviour matched
structurally only. With two structurally-identical entries carrying distinct
refinement tags under default selection, the request must share only the
exactly-matching one; structural-only matching would wrongly merge both
(FAIL_TO_PASS: ``test_multiple``).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but CORRECT
    impl (return the grounded fold directly, no loop; or inline the per-entry
    decision into the loop keeping the frozen proof) must verify, else the spec
    is SPEC-TOO-STRONG over the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    fractional-permission ``Requires``. This backend's ``pre-conditions`` region
    is EMPTY (the method is total over every input) and there is no permission
    surface, so that probe is degenerate. The residual admissibility risk on a
    total domain is a DEGENERATE post-image; ``admiss-nondegenerate`` discharges
    an in-region ``assert`` pinning THREE distinct outcomes (exact match keeps
    the entry, distinct-tag entry is dropped in default mode, structural match is
    kept in restricted mode) at F2P-shaped inputs. The impl is kept verbatim so
    the method's own obligation still discharges.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this carrier. The nagini sibling's
    MANDATORY frame-mutation rival writes through a read-only (``Acc(.,1/2)``)
    reference to a registry input and is rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: ``registry`` / ``req`` /
    ``allowed`` are immutable values declared read-only (no ``mut``), there is no
    heap, no aliasing and no permission system to subvert. There is no read-only
    input to overwrite, so the class has no carrier analogue. No substitute is
    fabricated (footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1 is pinned to ``eligibleEntries
    …``, a fully-unfolded fold over the method's own arguments; there is no
    answer key to echo. The cheapest correct impl computes the fold honestly and
    is carried as the positive control ``pos-control-direct``.
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
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. Each rival
    gets most of the domain right and diverges on one sub-domain of the per-entry
    decision (default-mode granularity, permission gate, restricted-mode
    granularity, mode-branch swap, or a wholesale polarity flip).

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY GOLD CANNOT BE THE SECOND SUBJECT.
The post-image ``eligibleEntries`` is a fold over ``Nat``/``Bool``/``EntryId``
(all ``DecidableEq``) with no opaque term, so the tester path is LIVE here: a
witness reaches the post-image through Velvet's own tester machinery
(``computeEligibleTester registry req allowed restricted = false`` says the
extracted program's result violates the method's postcondition at that concrete
input) and closes by ``decide``, checked in a file whose ``prove_correct`` block
has been stripped so no tactic script can mask the verdict. Each reject rival is
a LOOP-FREE closed form, so its extracted tester ``decide``s over the concrete
literal and the ELABORATES-against-the-rival half is a real computation.

The FAIL-on-the-other-subject half CANNOT be taken against the frozen solution
here, and an earlier revision of this file wrongly claimed it could. The frozen
program is a ``while`` loop under ``loom.semantics.choice "demonic"``; it
elaborates through ``Classical.choice``, which the kernel cannot unfold, so
``decide`` against the frozen tester is STUCK ("did not reduce to ``isTrue`` or
``isFalse``") for EVERY claim regardless of truth. Measured, three builds:

  * the real refutation ``…Tester [(0,(5,1)),(1,(5,2))] (5,1) none false = false``
    -> exit 1, stuck reduction;
  * the OPPOSITE claim ``… = true`` (which is TRUE of the frozen impl)
    -> exit 1, the SAME stuck reduction;
  * a trivially true claim about the empty registry, ``…Tester [] (0,0) none
    false = true`` -> exit 1, the SAME stuck reduction.

So gold's exit code carries no information at all, and "it failed on gold" is
evidence of nothing — a forged witness asserting the rival is CORRECT at an
agreement point would clear both halves. This is the ``witness-undecided``
condition the gate documents (swebench_unified/gates/pbt.py ``_STUCK_REDUCTION``).

Therefore every reject case here declares an explicit ``witness_reference``:
``_POS_DIRECT``, the loop-free ``return (eligibleEntries …)`` impl that is also
shipped as ``pos-control-direct``. The gate independently checks a reference
shares the frozen spec AND VERIFIES before refuting a witness against it, and an
impl the verifier accepts cannot violate its own spec — so a genuine refutation
must still fail there, and it fails by DECIDING rather than by getting stuck.
Measured for all reject cases with ``scripts/lean_verify.sh``: rival exit 0;
reference exit 1 with ``Tactic `decide` proved that the proposition … is false``
— a semantic refutation of the concrete claim, naming the witnessed input.
Declaring the reference rather than leaning on the gate's own positives-fallback
is the point: it makes the attestation a property of the ARTIFACT instead of a
rescue the record does not explain.

No witness binds a hypothesis (every input is a concrete literal that decides
C1), so no consistency probe is needed.

WHY THE WITNESSES ARE LOAD-BEARING, MEASURED. A loop-free but fully CORRECT impl
(``registry.filterMap`` with the gold ``entryEligible``) does NOT verify under the
flat ``loom_solve`` proof body the reject rivals carry: it fails with ``unsolved
goals`` on C1, byte-for-byte the same failure MODE as every wrong rival. It does
verify once its proof is retuned to peel the fold by induction (measured, exit 0
— see ``pos-control-filtermap`` below, which now ships that retuned proof as a
third positive control). So on this carrier "the rival did not verify" genuinely
attributes NOTHING to the spec, and the witnesses are the whole substance of the
reject lane. The spec is not too strong: the reshape is provable.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries an
axiom-soundness/containment probe over the real comparison callees; that is
G-AX's job (axiom_check.py / mapping.md §3) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15554"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE frozen impl body (backward `while` fold), everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- impl region and same_spec holds by construction (both facts asserted at
# ---- load by _swap / the count assert below).
_IMPL = (
    "    let mut result : List Nat := []\n"
    "    let mut i := registry.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ registry.length\n"
    "      invariant result = eligibleEntries req allowed restricted (registry.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := registry[i - 1]!\n"
    "      let keep := entryEligible req allowed restricted e\n"
    "      result := (if keep then [e.1] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- loop-free reshape retunes THIS block; the loop-keeping positive leaves it
# ---- as-is. Reject rivals retune it to the flat shape so the rejection is
# ---- carried by the witness, not by a tactic script tuned to a loop that no
# ---- longer exists.
_PROOF = (
    "prove_correct computeEligible by\n"
    "  loom_solve\n"
    "  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# ---- a flat proof body: with a loop-free impl there is no invariant to peel, so
# ---- `loom_solve` alone discharges the equality (for a correct reshape) or
# ---- leaves it unsolved (for the reject rivals — the point).
_PROOF_FLAT = "prove_correct computeEligible by\n  loom_solve"


def _impl(new_body):
    """Full variant with ONLY the impl body replaced (frozen proof kept)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof=_PROOF_FLAT):
    """Impl body replaced AND the proof retuned to the flat shape (loop-free)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- a loop-free rival: decide each entry with a custom per-entry predicate.
# ---- Being loop-free (`registry.filterMap`), its extracted `…Exec` reduces
# ---- under `decide` so its witness discriminates; gold's `while`-loop `…Exec`
# ---- stays stuck.
def _filtermap(keep_expr):
    return _impl_reproved(
        "    return (registry.filterMap (fun e => if "
        + keep_expr + " then some e.1 else none))")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery.
# ---- Every argument is a concrete literal so `decide` reduces the (loop-free)
# ---- extracted rival program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for computeEligible\n"
            "prove_precondition_decidable_for computeEligible\n"
            "prove_postcondition_decidable_for computeEligible\n"
            "derive_tester_for computeEligible\n\n" + body)


def _E(struct, refine):
    """A concrete EntryId literal."""
    return "{structKey := %d, refineTag := %d}" % (struct, refine)


def _reg(entries):
    """A concrete registry literal from (id, struct, refine) triples."""
    return "[" + ", ".join(
        "(%d, %s)" % (i, _E(s, r)) for (i, s, r) in entries) + "]"


def _witness(registry_literal, req_literal, allowed_literal, restricted_literal):
    return _tester(
        f"example : computeEligibleTester {registry_literal} {req_literal} "
        f"{allowed_literal} {restricted_literal} = false := by\n  decide\n")


# ---- THE WITNESS REFERENCE. The frozen impl is a `while` loop under demonic
# ---- choice, so `decide` against its extracted tester is STUCK for every claim
# ---- and its exit code discriminates nothing (see the CARRIER NOTE — measured on
# ---- the real refutation, on the OPPOSITE claim, and on a trivially true claim:
# ---- all three exit 1 with the identical stuck reduction). Every reject case is
# ---- therefore refuted against THIS impl instead: loop-free (so it reduces) and
# ---- an impl of the SAME frozen spec that VERIFIES (shipped independently as the
# ---- `pos-control-direct` positive, and re-checked by the gate before use). An
# ---- impl the verifier accepts cannot violate its own spec, so a genuine witness
# ---- must still fail here — and it fails by DECIDING the claim false, not by
# ---- getting stuck. That is what makes each rejection attributable to the spec.
_POS_DIRECT = _impl_reproved(
    "    return (eligibleEntries req allowed restricted registry)")

# ---- the retuned proof that closes a loop-free CORRECT reshape. The flat
# ---- `loom_solve` body the reject rivals carry leaves C1 as an `unsolved goals`
# ---- for a correct filterMap impl too, so the reshape needs the fold peeled by
# ---- induction on the registry. Measured: exit 0.
_PROOF_FOLD = (
    "prove_correct computeEligible by\n"
    "  loom_solve\n"
    "  induction registry with\n"
    "  | nil => simp [eligibleEntries]\n"
    "  | cons e es ih =>\n"
    "    rw [List.filterMap_cons, eligibleEntries_cons, ← ih]\n"
    "    by_cases h : entryEligible req allowed restricted e <;> simp [h]")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded fold directly, no
        # loop at all — maximally structurally different from the gold backward
        # scan. `out` IS `eligibleEntries req allowed restricted registry`, so
        # the ensures holds trivially; the reproof is a bare `loom_solve` (no
        # loop invariant to peel). Since the post-image is GROUNDED in the args
        # (not an opaque answer key), this doubles as proof the spec is not
        # echo-vulnerable: any WRONG per-entry decision fails `out =
        # eligibleEntries …`.
        "module": _POS_DIRECT,
        "rationale": (
            "the post-image `eligibleEntries req allowed restricted registry` is "
            "GROUNDED in the inputs (a total front-recursive fold, no opaque "
            "answer key), so returning it directly is the honest cheapest CORRECT "
            "impl; C1 is literally `out = eligibleEntries …`, so it MUST verify, "
            "else C1 is SPEC-TOO-STRONG. Ports the nagini cheapest-grounded "
            "positive control, showing the spec is not echo-vulnerable (any wrong "
            "per-entry decision fails the pin)."),
    },
    {
        "id": "pos-control-inline-keep",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole backward `while` fold, the invariants and the frozen
        # proof script; only inlines the per-entry decision (drop the `keep`
        # local, test `entryEligible …` directly in the `if`). Observationally
        # identical for every input; the frozen loop proof closes unchanged.
        "module": _impl(
            "    let mut result : List Nat := []\n"
            "    let mut i := registry.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ registry.length\n"
            "      invariant result = eligibleEntries req allowed restricted (registry.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let e := registry[i - 1]!\n"
            "      result := (if entryEligible req allowed restricted e then [e.1] else []) ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "inlining the per-entry decision into the `if` (dropping the `keep` "
            "local) scans the same registry with the same step, so `out = "
            "eligibleEntries …` still holds on the whole domain; the loop, "
            "invariants and frozen proof script are untouched. A correct reshape "
            "must verify, else the postcondition is SPEC-TOO-STRONG (over-fit to "
            "the let-bound code form). Ports the nagini pos-control-reorder as a "
            "loop-preserving reshape."),
    },
    {
        "id": "pos-control-filtermap",
        "kind": "soundness",
        "expect": "verify",
        # THE CONTROL THAT MAKES THE REJECT LANE MEANINGFUL. This is exactly the
        # shape every reject rival has — a loop-free `registry.filterMap` — but
        # with the GOLD per-entry decision, so it is fully CORRECT. Under the flat
        # `loom_solve` body the rivals carry it does NOT verify: it fails with
        # `unsolved goals` on C1, the same failure MODE as every wrong rival. That
        # is the measurement proving "did not verify" attributes nothing to the
        # spec on this carrier, which is why the witnesses (not the outcomes) are
        # the reject lane's evidence. With the proof retuned to peel the fold by
        # induction it verifies, so the spec is NOT too strong over this shape.
        "module": _impl_reproved(
            "    return (registry.filterMap (fun e => "
            "if entryEligible req allowed restricted e then some e.1 else none))",
            _PROOF_FOLD),
        "rationale": (
            "a loop-free `registry.filterMap` carrying the GOLD per-entry decision "
            "is observationally identical to the frozen backward scan on the whole "
            "domain, so `out = eligibleEntries …` holds and it MUST verify — else "
            "C1 is SPEC-TOO-STRONG over the impl's shape. It is also the negative "
            "control for the reject lane: this CORRECT impl fails identically "
            "(`unsolved goals` on C1) to every WRONG rival under the flat "
            "`loom_solve` body, which is precisely why each rejection is carried by "
            "its machine-checked witness and not by the verifier's verdict. Closing "
            "it needs only the fold peeled by induction on `registry` — the frozen "
            "spec is untouched and no obligation is weakened."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` (the pre-conditions region
    # is empty), so the sibling's "a normal input satisfies the read-only
    # fractional-permission precondition" probe is degenerate here. The residual
    # admissibility risk on a total domain is a DEGENERATE post-image — a spec no
    # impl distinguishes reads exactly like one every impl meets. This case
    # discharges an in-region `assert`, at three fully concrete F2P-shaped
    # inputs, that the post-image is NON-DEGENERATE: an EXACT match keeps the
    # entry, a structurally-identical DISTINCT-tag entry is dropped in default
    # mode (the fix's behaviour), and a structural match is kept in restricted
    # mode — three genuinely distinct outcomes. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the proof gains a
    # `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      eligibleEntries " + _E(5, 1) + " none false "
                  + _reg([(0, 5, 1), (1, 5, 2)]) + " = [0] ∧\n"
                  "      eligibleEntries " + _E(5, 1) + " (some [0]) true "
                  + _reg([(0, 5, 2)]) + " = [0] ∧\n"
                  "      eligibleEntries " + _E(5, 1) + " none false "
                  + _reg([(0, 9, 9)]) + " = []))\n"),
            _PROOF,
            "prove_correct computeEligible by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]\n"
            "       simp_all)\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: in default mode an EXACT match keeps the entry (id 0), a "
            "structurally-identical DISTINCT-tag entry is DROPPED (the fix's "
            "behaviour — the request shares only the exact match), and in "
            "restricted mode a structural match with a permitted id is kept — "
            "three distinct outcomes. The in-region assert must discharge (else "
            "the obligation is degenerate / the precondition too strong); the "
            "impl is kept verbatim so `out = eligibleEntries …` still verifies. "
            "Re-aimed from the nagini admiss-self-call, whose read-only "
            "fractional-permission half has no counterpart on this "
            "referentially-transparent, precondition-free carrier."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a LOOP-FREE
    # `registry.filterMap` closed form (see the CARRIER NOTE) so its extracted
    # tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-default-structural-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug-delta (nagini ATTACK A). In the DEFAULT branch match
        # structurally only (matchesStructural) instead of exactly (matchesExact).
        # Correct whenever the incoming refinement tag equals the entry's, WRONG
        # on the F2P sub-domain: two structurally-identical entries with distinct
        # refinement tags under default selection — it wrongly keeps BOTH where
        # the spec keeps only the exact match.
        "module": _filtermap(
            "(if restrictedMode allowed restricted then\n"
            "        allowedMember allowed e.1 && matchesStructural e.2 req\n"
            "      else\n"
            "        (allowed.isNone || allowedMember allowed e.1) && matchesStructural e.2 req)"),
        "refinement": (
            "this is the pre-change default predicate: it matches on the "
            "structural identity only, ignoring the refinement tag. With two "
            "existing entries on the same relation but different conditions (the "
            "F2P scenario: the same relation filtered two different ways), the "
            "second is wrongly merged onto the first instead of kept distinct. The "
            "failing test asserts the two stay distinct, so the faithful real "
            "patch FAILS the F2P; it does NOT resolve. This is exactly the defect "
            "the fix corrects."),
        "rationale": (
            "REJECT from C1 (`out = eligibleEntries …`): the default arm of "
            "`entryEligible` uses `matchesExact` (full identity), so a "
            "structural-only match keeps an entry the fold drops ⇒ `out` acquires "
            "an id the post-image omits. Refuted at a two-entry registry sharing a "
            "structKey with distinct refineTags — gold keeps [0], the rival keeps "
            "[0,1]. If it verified => SPEC-TOO-WEAK (admits the bug)."),
        "witness": _witness(
            _reg([(0, 5, 1), (1, 5, 2)]), _E(5, 1), "none", "false"),
        # gold's tester cannot be decided (stuck for every claim, measured); the
        # refutation is taken against the VERIFYING loop-free impl of the same
        # spec, where it fails by DECIDING the claim false. rival exit 0,
        # reference exit 1 ("`decide` proved that the proposition … is false").
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-default-ignore-permission",
        "kind": "uniqueness",
        "expect": "reject",
        # nagini ATTACK B (partial-domain: permission gate ignored in default
        # mode). Drop the `(allowed.isNone || allowedMember allowed e.1)`
        # permission guard in the DEFAULT branch — match exactly but ignore the
        # allowance. Correct whenever the allowance is absent or already lists the
        # id, WRONG when an allowance IS supplied and a matching entry's id is NOT
        # in it: the spec drops that entry (not permitted), this rival keeps it.
        "module": _filtermap(
            "(if restrictedMode allowed restricted then\n"
            "        allowedMember allowed e.1 && matchesStructural e.2 req\n"
            "      else\n"
            "        matchesExact e.2 req)"),
        "refinement": (
            "this drops the allowance guard from the default selection. When an "
            "explicit allowance IS supplied but a matching entry's id is NOT in it, "
            "the fixed behaviour must exclude that entry; this rival wrongly keeps "
            "an entry outside the permitted set, sharing something the caller "
            "forbade. The reuse-set discipline the surrounding machinery relies on "
            "would break, so the faithful real patch does NOT resolve."),
        "rationale": (
            "REJECT from C1: the default arm of `entryEligible` gates the exact "
            "match by `(allowed.isNone || allowedMember allowed e.1)`; dropping it "
            "keeps an unpermitted id the fold omits ⇒ `out` acquires an extra id. "
            "Refuted at a one-entry registry whose id (0) is NOT in the supplied "
            "allowance `some [7]` — gold gives [], the rival gives [0]. A DISTINCT "
            "point from structural-only (this varies `allowed` from `none` to a "
            "non-covering list). If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            _reg([(0, 3, 4)]), _E(3, 4), "(some [7])", "false"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-restricted-exact-match",
        "kind": "uniqueness",
        "expect": "reject",
        # nagini ATTACK C (partial-domain: restricted branch uses EXACT match).
        # In the RESTRICTED branch use matchesExact (structKey AND refineTag)
        # instead of matchesStructural (structKey only). Correct whenever the
        # permitted entry's refinement tag happens to equal the request's, WRONG
        # when a permitted entry has the same structKey but a DIFFERENT refineTag:
        # the spec shares it (structural), this rival reports no match.
        "module": _filtermap(
            "(if restrictedMode allowed restricted then\n"
            "        allowedMember allowed e.1 && matchesExact e.2 req\n"
            "      else\n"
            "        (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req)"),
        "refinement": (
            "this makes the restricted branch require the full identity where the "
            "fixed behaviour requires only the structural identity over the "
            "permitted set. When computing a filtered relation's own sub-selection "
            "joins, an entry is shared by structural identity regardless of its "
            "refinement tag; requiring the tag too would spuriously refuse a "
            "reusable entry and create extra aliases, changing the generated SQL "
            "of the filtered-relation aggregation scenarios, so the faithful real "
            "patch does NOT resolve."),
        "rationale": (
            "REJECT from C1: the restricted arm of `entryEligible` uses "
            "`matchesStructural` (structKey only); using `matchesExact` drops a "
            "permitted same-structKey distinct-refineTag entry the fold keeps ⇒ "
            "`out` omits an id the post-image contains. Refuted in RESTRICTED mode "
            "(`restricted = true`, allowance `some [0]` non-empty) at a "
            "distinct-tag permitted entry — gold gives [0], the rival gives []. "
            "This is the ONLY witness that drives `restricted` true and a non-empty "
            "allowance (restrictedMode = true). If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            _reg([(0, 5, 2)]), _E(5, 1), "(some [0])", "true"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-default-permission-mask-only",
        "kind": "uniqueness",
        "expect": "reject",
        # nagini ATTACK D (partial-domain: default permission uses membership
        # only). Replace the default permission guard `(allowed.isNone ||
        # allowedMember allowed e.1)` with `allowedMember allowed e.1` — dropping
        # the allowance-absent ⇒ all-permitted case. Correct whenever an
        # allowance is supplied, WRONG on the common `allowed = none` path: the
        # spec permits every entry, this rival permits none (membership in `none`
        # is always false).
        "module": _filtermap(
            "(if restrictedMode allowed restricted then\n"
            "        allowedMember allowed e.1 && matchesStructural e.2 req\n"
            "      else\n"
            "        allowedMember allowed e.1 && matchesExact e.2 req)"),
        "refinement": (
            "this replaces the default permission gate with bare membership, "
            "dropping the allowance-absent ⇒ all-permitted case. On the "
            "overwhelmingly common call with no allowance supplied, a perfectly "
            "shareable identical entry would be SKIPPED and a duplicate created, "
            "changing counts and generated SQL across nearly every query, so the "
            "faithful real patch does NOT resolve."),
        "rationale": (
            "REJECT from C1: with `allowed = none` the default arm permits every "
            "entry (`allowed.isNone` true), but `allowedMember none _` is always "
            "false, so this rival drops an exactly-matching entry the fold keeps ⇒ "
            "`out` omits an id. Refuted at a one-entry registry with `allowed = "
            "none` and an exact match — gold gives [0], the rival gives []. A "
            "DISTINCT point (varies `req` and holds `allowed = none` while the "
            "structural-only rival also has `none` but a two-entry registry). If "
            "it verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            _reg([(0, 2, 8)]), _E(2, 8), "none", "false"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-result-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss (nagini ATTACK E): compute the eligibility decision
        # exactly as gold but INVERT its polarity — keep the entries that are NOT
        # eligible and drop the eligible ones. A cheap polarity flip; still a real
        # C1 divergence with a refinement argument. Kept as a SUPPORTING case, not
        # a substitute for the reasoned partial-domain attacks above.
        "module": _impl_reproved(
            "    return (registry.filterMap (fun e => "
            "if entryEligible req allowed restricted e then none else some e.1))"),
        "refinement": (
            "this reports 'shareable' exactly for the entries that are NOT and "
            "vice-versa: every eligible entry would be dropped and every "
            "ineligible one wrongly shared. The sharing decision would be "
            "wholesale inverted — wrong SQL across the entire suite; the faithful "
            "real patch does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = eligibleEntries …`): keeping the complement of "
            "the eligible set gives `out` = the ids the fold OMITS and omits the "
            "ids it keeps — the exact inversion. Refuted at a registry with one "
            "eligible and one ineligible entry — gold gives [0], the rival gives "
            "[1]. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(
            _reg([(0, 5, 1), (1, 9, 9)]), _E(5, 1), "none", "false"),
        "witness_reference": _POS_DIRECT,
    },

    # =====================================================================
    # ADDED BY AUDIT — two behaviours of C1 the ported reject set left wholly
    # unattacked. Neither has a nagini counterpart (the sibling's carrier splits
    # the mode on a `constrained` flag whose allowance-presence coupling is a
    # precondition, and its post-image is a single Bool, so neither the mode
    # GUARD nor the result's ORDER/MULTIPLICITY is observable there). Both are
    # observable and attackable here, so leaving them unprobed was a real gap:
    # the frozen `ensures` pins an ordered LIST, and every ported rival varied
    # only the per-entry PREDICATE, so nothing tested the list structure at all.
    # =====================================================================
    {
        "id": "weak-mode-guard-flag-only",
        "kind": "uniqueness",
        "expect": "reject",
        # MODE SELECTION, the one behaviour of `entryEligible` the ported set never
        # touched. `restrictedMode` fires only when `restricted` is set AND a
        # non-empty allowance is supplied; this rival keys the branch on the flag
        # ALONE, dropping the allowance-presence requirement. Correct whenever the
        # flag agrees with the allowance's presence, WRONG when the flag is set but
        # NO allowance (or an empty one) is supplied: the spec falls back to the
        # default mode and permits every entry, this rival takes the restricted arm
        # where `allowedMember none _` is always false and so selects nothing.
        "module": _filtermap(
            "(if restricted then\n"
            "        allowedMember allowed e.1 && matchesStructural e.2 req\n"
            "      else\n"
            "        (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req)"),
        "refinement": (
            "the mode guard requires BOTH the request for restricted selection AND "
            "an actual non-empty allowance; keying it on the flag alone makes the "
            "restricted arm fire with no allowance to consult, so every entry is "
            "refused and a duplicate is created where the fixed behaviour shares an "
            "identical entry. The flag is threaded down from callers that do not "
            "always supply an allowance, so this misfires on live paths and the "
            "faithful real patch does NOT resolve."),
        "rationale": (
            "REJECT from C1: `restrictedMode allowed restricted` conjoins the flag "
            "with a non-empty allowance, so with `restricted = true` and `allowed = "
            "none` the fold takes the DEFAULT arm and keeps an exact match; this "
            "rival takes the restricted arm and drops it ⇒ `out` omits an id the "
            "post-image contains. Refuted at a one-entry exact-match registry with "
            "`allowed = none` and `restricted = TRUE` — gold gives [0], the rival "
            "gives []. This is the only witness driving `restricted = true` with an "
            "ABSENT allowance (restrictedMode = false while the flag is set), the "
            "point that separates the guard from the flag. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness(_reg([(0, 5, 1)]), _E(5, 1), "none", "true"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-result-order",
        "kind": "uniqueness",
        "expect": "reject",
        # RESULT ORDER. Every ported rival varied the per-entry PREDICATE, so the
        # eligible SET was attacked five ways and the list's ORDER never once. C1
        # pins an ordered list ("in registry order"), and the consumer reads a
        # positional element out of it, so order is load-bearing and separately
        # falsifiable. This rival applies the GOLD per-entry decision — the
        # selected set is exactly right — and only reverses the result.
        "module": _impl_reproved(
            "    return ((registry.filterMap (fun e => "
            "if entryEligible req allowed restricted e then some e.1 else none)).reverse)"),
        "refinement": (
            "the selection must come back in registry order, because the consumer "
            "picks a positional element out of the candidate list rather than "
            "treating it as a set. Reversing it hands back a different candidate "
            "whenever two or more entries are eligible, so a request would share "
            "the wrong existing entry and the generated result changes on exactly "
            "the multi-candidate shapes the failing scenario exercises; the "
            "faithful real patch does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = eligibleEntries …`): `eligibleEntries` is a "
            "FRONT-recursive fold, so its result is in registry order; reversing it "
            "gives a permutation, and list equality is not equality of sets ⇒ `out` "
            "≠ the post-image as soon as two entries are eligible. Refuted at a "
            "two-entry registry BOTH eligible (identical structKey and refineTag, "
            "ids 0 and 1) — gold gives [0,1], the rival gives [1,0]. A genuinely new "
            "point: the first witness in the battery at which the eligible set has "
            "more than one member, so it is the only one that can see order at all. "
            "If it verified => SPEC-TOO-WEAK (the spec would not actually pin "
            "order, contradicting its own prose)."),
        "witness": _witness(
            _reg([(0, 5, 1), (1, 5, 1)]), _E(5, 1), "none", "false"),
        "witness_reference": _POS_DIRECT,
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                     kind          -> here                            disposition
#   -----------------------------------------------------------------------------------------------
#   pos-control-reorder             soundness     -> pos-control-inline-keep         RE-SHAPED
#   pos-cheapest-grounded           soundness     -> pos-control-direct              PORTED
#   admiss-self-call                admissibility -> admiss-nondegenerate            RE-AIMED
#   frame-mut-base-write            uniqueness    -> (none)                          VACUOUS
#   weak-default-base-only          uniqueness    -> weak-default-structural-only    PORTED
#   weak-default-ignore-eligibility uniqueness    -> weak-default-ignore-permission  PORTED
#   weak-constrained-full-identity  uniqueness    -> weak-restricted-exact-match     PORTED
#   weak-default-mask-only-eligib.  uniqueness    -> weak-default-permission-mask-only PORTED
#   weak-result-polarity            uniqueness    -> weak-result-polarity            PORTED
#   AXIOM_TESTS (1)                 axiom         -> (none)                          DROPPED (G-AX lane)
#
# 11 velvet SPEC cases: 3 soundness, 1 admissibility, 7 uniqueness. EVERY nagini
# uniqueness rival that attacks a modeled clause is ported (5 of them); the sole
# omission is the mandatory frame-mutation rival, which is VACUOUS on a
# referentially-transparent carrier.
#
# ADDED BY AUDIT (no nagini counterpart — carrier-only behaviours the sibling
#   cannot express): pos-control-filtermap (soundness), weak-mode-guard-flag-only
#   and weak-result-order (uniqueness). See the two blocks below.
#
# RE-SHAPED (pos-control-reorder -> pos-control-inline-keep): the nagini positive
#   reorders the constrained/default branch order in the impl. On this carrier the
#   per-entry decision is the single pure `entryEligible` def (there is no
#   in-impl branch chain to reorder — the mode split lives inside the pure def,
#   which is FROZEN spec and may not be touched). The loop-preserving correct
#   reshape here inlines the `keep` local into the `if`, a structurally-different
#   impl that keeps the frozen loop proof intact. The maximally-different correct
#   impl (loop-free direct return of the grounded fold) is pos-control-direct.
# PORTED (pos-cheapest-grounded -> pos-control-direct): the nagini cheapest honest
#   positive returns the grounded @Pure oracle directly. Here the oracle IS the
#   transparent `eligibleEntries` and C1 IS `out = eligibleEntries …`, so the
#   cheapest honest impl is `return eligibleEntries …` — same argument (the
#   grounded pin admits no wrong echo), loop-free.
# RE-AIMED (admiss-self-call -> admiss-nondegenerate): the nagini case constructs
#   an F2P-shaped one-entry registry and self-calls to show the read-only
#   fractional-permission precondition is satisfiable. This method has NO `require`
#   (empty pre-conditions region) and no permission surface, so that probe is
#   degenerate; re-aimed at the residual total-domain risk (a DEGENERATE
#   post-image), witnessed by an in-region assert pinning all THREE distinct
#   outcomes (exact-keep / distinct-tag-drop / restricted-structural-keep) at
#   F2P-shaped inputs, with the surrounding gold impl kept verbatim.
# PORTED (the five value/branch rivals): weak-default-base-only ->
#   weak-default-structural-only (THE bug-delta: default structural-only match;
#   refuted on the distinct-refineTag F2P sub-domain). weak-default-ignore-
#   eligibility -> weak-default-ignore-permission (drop the default allowance
#   gate; refuted when a non-covering allowance is supplied). weak-constrained-
#   full-identity -> weak-restricted-exact-match (restricted branch requires the
#   full identity; refuted on a permitted distinct-refineTag entry in restricted
#   mode). weak-default-mask-only-eligibility -> weak-default-permission-mask-only
#   (default permission via membership only, dropping the allowance-absent case;
#   refuted on the common `allowed = none` path). weak-result-polarity ->
#   weak-result-polarity (invert the eligibility decision). Each carries its
#   nagini refinement argument, now backed by a machine-checked witness.
# VACUOUS (frame-mut-base-write): the nagini MANDATORY frame-mutation rival writes
#   to a registry input held at Acc(.,1/2) and is rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: `registry` / `req` /
#   `allowed` are immutable values declared read-only (no `mut`), there is no
#   heap, no aliasing, no `Old`, and no permission system. There is no read-only
#   input to overwrite and no frame clause to violate, so the class has no carrier
#   analogue. Omitted as a genuine carrier fact, NOT fabricated.
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
# DROPPED (AXIOM_TESTS): the nagini file's single axiom-soundness/containment
#   probe over the real comparison callees is G-AX's job (axiom_check.py /
#   mapping.md §3); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# ADDED, no nagini source (weak-mode-guard-flag-only): the MODE GUARD. The sibling
#   splits the mode on a bare `constrained` flag and carries the allowance coupling
#   as a PRECONDITION (`Implies(constrained, not reuse_all)`), so on that carrier
#   the flag and the guard cannot be pulled apart and no rival could exist. Here
#   `restrictedMode` conjoins the flag with a non-empty allowance INSIDE the pure
#   def, making the two independently falsifiable, and the ported set attacked only
#   the two branch BODIES — never which branch is taken. Closed by keying the
#   branch on the flag alone, refuted at `restricted = true, allowed = none`.
# ADDED, no nagini source (weak-result-order): the RESULT ORDER. The sibling's
#   post-image is a single Bool ("is a fresh slot needed"), so order and
#   multiplicity are simply not observable there. Here C1 pins an ordered LIST and
#   its own prose promises "in registry order", yet all five ported rivals varied
#   the per-entry PREDICATE only — the eligible SET was attacked five ways and the
#   list STRUCTURE not once. Closed by a rival with the exact gold predicate and a
#   reversed result, refuted at the battery's first two-eligible-entry registry.
# ADDED, no nagini source (pos-control-filtermap): the negative control for the
#   reject lane. Measured, and the reason the audit added it: a loop-free but fully
#   CORRECT filterMap impl fails under the flat `loom_solve` body with `unsolved
#   goals` on C1 — the identical failure MODE as every wrong rival — so on this
#   carrier a rejection carries no information without its witness. Shipping the
#   control makes that fact part of the artifact, and its retuned proof (fold
#   peeled by induction, exit 0) shows the spec is not SPEC-TOO-STRONG here.
#
# CLAUSE / BINDER / POINT COVERAGE. The only clause is C1 (`out = eligibleEntries
#   req allowed restricted registry`), a function of all FOUR binders. It is
#   attacked on every independent behaviour of `entryEligible`:
#     * default MATCH GRANULARITY  -> weak-default-structural-only  (matchesExact
#         demoted to matchesStructural)
#     * default PERMISSION gate    -> weak-default-ignore-permission (allowance
#         dropped) AND weak-default-permission-mask-only (allowance-absent case
#         dropped)
#     * restricted MATCH GRANULARITY -> weak-restricted-exact-match (matchesStructural
#         promoted to matchesExact)
#     * whole-decision POLARITY    -> weak-result-polarity
#     * MODE GUARD (flag vs guard) -> weak-mode-guard-flag-only (ADDED BY AUDIT:
#         restrictedMode's allowance-presence conjunct dropped)
#     * RESULT ORDER               -> weak-result-order (ADDED BY AUDIT: the gold
#         predicate with the list reversed — the SET is right, the ORDER is not)
#   The seven reject witnesses probe seven DISTINCT input points (pts=7):
#     * weak-default-structural-only    reg=[(0,5,1),(1,5,2)]  req=(5,1)  allowed=none      restricted=false
#     * weak-default-ignore-permission  reg=[(0,3,4)]          req=(3,4)  allowed=some[7]   restricted=false
#     * weak-restricted-exact-match     reg=[(0,5,2)]          req=(5,1)  allowed=some[0]   restricted=true
#     * weak-default-permission-mask-only reg=[(0,2,8)]        req=(2,8)  allowed=none      restricted=false
#     * weak-result-polarity            reg=[(0,5,1),(1,9,9)]  req=(5,1)  allowed=none      restricted=false
#     * weak-mode-guard-flag-only       reg=[(0,5,1)]          req=(5,1)  allowed=none      restricted=TRUE
#     * weak-result-order               reg=[(0,5,1),(1,5,1)]  req=(5,1)  allowed=none      restricted=false
#   So `restricted` ranges over {true, false} and — this is what the audit added —
#   it is now load-bearing in BOTH couplings: weak-restricted-exact-match is the
#   only witness reaching restrictedMode=TRUE (flag set AND a non-empty allowance,
#   the restricted arm), while weak-mode-guard-flag-only is the only witness with
#   the flag SET and restrictedMode still FALSE (allowance absent), which is the
#   point that separates the guard from the flag and which no ported witness
#   reached. `allowed` ranges over {none, some[7] (non-covering), some[0]
#   (covering)} (proving the permission gate and the allowance-absent case are both
#   load-bearing), `req` ranges over (5,1)/(3,4)/(2,8), and the registry over one-
#   and two-entry shapes with matching and non-matching structKeys/refineTags —
#   including, only at weak-result-order, a registry where TWO entries are eligible
#   at once, the sole point at which the post-image's ORDER is observable. No
#   binder is held at a single value across the reject set. All three positives and
#   the admissibility case defend C1.
#
# WITNESS MECHANICS (CORRECTED BY AUDIT): the tester+`decide` path is LIVE for a
#   loop-free impl (the post-image `eligibleEntries` is a fold over
#   Nat/Bool/EntryId, all DecidableEq, with no opaque term), so every rival's own
#   `computeEligibleTester` reduces and the ELABORATES-on-the-rival half is a real
#   computation. It is NOT live for the frozen impl: its `while` loop under demonic
#   choice elaborates through `Classical.choice`, so `decide` there is STUCK for
#   every claim regardless of truth. An earlier revision of this footer said the
#   same witness "FAILS against gold" and read that as discrimination; it is not.
#   Measured on the frozen solution: the real refutation, the OPPOSITE claim (true
#   of gold), and a trivially true claim about the empty registry ALL exit 1 with
#   the identical "did not reduce to `isTrue` or `isFalse`". Gold's exit code
#   carries zero information, which is the gate's `witness-undecided` condition.
#   Every reject case therefore now declares `witness_reference = _POS_DIRECT` —
#   the loop-free `return (eligibleEntries …)` impl, shipped independently as
#   pos-control-direct, which the gate re-checks shares the frozen spec and
#   VERIFIES before using it. An impl the verifier accepts cannot violate its own
#   spec, so a genuine refutation must still fail there, and it fails by DECIDING.
#   No witness binds a hypothesis, so no consistency probe is needed. No banned
#   token (sorry/admit/native_decide/axiom/opaque). All SEVEN re-checked by the
#   audit with scripts/lean_verify.sh: rival exit 0; reference exit 1 with
#   "Tactic `decide` proved that the proposition … is false", naming the witnessed
#   input — a semantic refutation, not a stuck reduction and not a missing name.
AXIOM_TESTS = []
