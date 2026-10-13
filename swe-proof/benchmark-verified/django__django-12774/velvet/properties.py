"""properties.py — G-PBT falsification battery for django__django-12774 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct validateLookupField`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method decides whether a requested lookup key
is admissible for a keyed retrieval, over three read-only inputs:

    validateLookupField (fieldName : String) (fieldUnique : Bool)
                        (constraints : List (List String))
      return (out : Except ValidationErr Unit)
    ensures out = lookupFieldDecision fieldName fieldUnique constraints

``lookupFieldDecision`` is a fully-unfolded ``def`` in the ``pure`` region — the
key is REJECTED (``Except.error``) exactly when ALL of three sub-conditions
hold, otherwise it is admissible (``Except.ok ()``):

  (a) it is not the primary-key alias (``fieldName != "pk"``);
  (b) it is not individually declared unique (``!fieldUnique``);
  (c) it is not the sole column of any single-column uniqueness guarantee
      (``!(singleColumnKeys constraints).contains fieldName``).

``singleColumnKeys`` is itself a concrete front-recursive ``def`` (each
guarantee contributes its sole column iff it spans exactly one column), so the
whole postcondition is GROUNDED in the inputs — there is no opaque answer key to
echo, and a direct ``return lookupFieldDecision fieldName fieldUnique
constraints`` is simply the cheapest honest correct impl (it does the real work
because ``singleColumnKeys`` IS the work). The single ``ensures`` clause carries
three INDEPENDENT sub-behaviours (a)/(b)/(c); every one is defended by a verify
control and attacked by a reject rival, and the reject witnesses vary all three
input binders (``fieldName``, ``fieldUnique``, ``constraints`` — including the
empty ``constraints`` and a length-2 list whose permitting guarantee is NOT
first), so no sub-behaviour is left pinned at one point.

The discriminating content of the fix is sub-condition (c): a key that is the
sole column of a single-column uniqueness guarantee MUST be accepted. The
pre-fix decision lacked (c) entirely (such a non-primary, non-unique key was
ALWAYS rejected) — that is the F2P: a lookup on a key that is the sole column of
one single-column unconditional guarantee must now succeed. Rival
``partial-ignore-constraints`` reproduces that pre-fix behaviour EXACTLY.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION (nagini ``frame-mutate-guarantees``, MANDATORY
    there) — VACUOUS here. The nagini sibling carries it because the guarantee
    list holds a fractional heap permission (``Acc(..., 1/2)``) a rival could
    illegally demand at full strength and WRITE through to forge a permitting
    guarantee. Lean and Velvet are referentially transparent: every input is an
    immutable value, this method declares no ``mut`` parameter, there is no heap
    and no aliasing — there is nothing to overwrite. No substitute fabricated
    (per the porting map: this class is vacuous on Lean/Velvet).
  * CONDITIONAL-GUARANTEE class (nagini ``weak-ignore-unconditional``) — NOT
    EXPRESSIBLE on this carrier. The nagini rival drops the "unconditional"
    (``condition is None``) filter so a CONDITIONAL single-column guarantee is
    treated as permitting. This backend's carrier for a guarantee is a bare
    ``List String`` (the columns it spans) with NO condition flag: the modeled
    input already contains only the unconditional guarantees (the "total" filter
    is upstream and unchanged), so the conditional/unconditional distinction the
    nagini rival abuses simply does not exist in the modeled values. The rival's
    abstraction collapses here; there is no discriminating witness because the
    spec has no conditional binder to mishandle. Documented, not fabricated.
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
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class, exactly as the sibling
    records: ``lookupFieldDecision`` / ``singleColumnKeys`` are concrete ``def``s
    in the ``pure`` region and the ``axioms`` region is empty, so there is no
    answer key to echo. The honest grounded direct-decision control is the
    sibling's directive-2 substitute, carried here.
  * PARTIAL-DOMAIN / VALUE — the core attacks. Each reject rival is correct on
    part of the domain but diverges on a sub-domain: ignore the guarantees
    entirely (the pre-fix bug), consult only the FIRST guarantee, treat a
    MULTI-column guarantee's first column as permitting, or drop the
    individually-unique / primary-key exemption. The single grounded equality is
    what rejects each divergence.

WITNESS MECHANICS ON THIS BUNDLE — AND THE EXACT LIMIT OF WHAT THEY ATTEST.
Each reject rival is authored as a straight-line COMPUTABLE impl (referencing the
``pure``-region ``def``s, which is in scope) and refuted by a witness
``validateLookupFieldTester fieldName fieldUnique constraints = false`` at
concrete literals. The report carrier is ``Except ValidationErr Unit``, so each
witness first ``deriving instance DecidableEq for Except`` (an instance, not an
assumption: no ``sorry`` / ``axiom`` / ``native_decide``). No witness binds a
hypothesis (every input is a concrete literal), so there is no
carrier-conditioning and no consistency-probe obligation.

The RIVAL half is a genuine value-level oracle and carries the discriminating
content. ``validateLookupFieldTester f u c`` reduces for a straight-line impl and
computes ``decide (out = lookupFieldDecision f u c)``, so ``= false`` says the
extracted program's result really does violate the postcondition at that literal
input. This was confirmed to be a SEMANTIC and not a vacuous claim: at a point
where a rival happens to AGREE with the frozen decision the ``= false`` witness
FAILS to elaborate (measured EXIT 1) while ``= true`` elaborates (EXIT 0), and
against the honest ``pos-direct-decision`` impl ``= false`` fails at every point
tried. So a witness that elaborates against its rival pins a real disagreement.

The GOLD half, however, attests LESS than it appears to, and this is recorded
here rather than glossed. The frozen impl's ``while`` loop makes
``validateLookupFieldExec`` kernel-IRREDUCIBLE, so on the frozen solution
``decide`` never gets a truth value at all: it reports "reduction got stuck at
the ``Decidable`` instance", not a refuted equality. The failure is therefore an
UNFOLDING failure, not a semantic refutation — and it is input-independent:
``… = true`` (the TRUE claim for gold, ``#eval`` confirms the tester returns
``true``) fails on the frozen solution identically to ``… = false``. Measured:
gold ``= false`` EXIT 1, gold ``= true`` EXIT 1, ``#eval`` prints ``true``,
and ``decide +kernel`` / ``rfl`` / ``simp`` / ``grind`` / ``unfold``-then-
``decide`` / an ``Exec``-level restatement all fail to reduce it too. So the
gate's "witness fails on gold" half is satisfied by the loop's irreducibility for
EVERY witness of this shape, and it does NOT independently establish that the
witness is non-tautological on this bundle. What rules out a tautology here is
the rival-side evidence above (a ``= false`` witness fails at non-violating
points), plus the per-case observable-difference derivation recorded in each
``rationale``. This is a property of the frozen loop shape, which is not
editable from this lane; it is documented, not patched.

AXIOM lane: EMPTY (``meta.json`` declares no ``axiom`` and no A-reference deep
model; the decision and the single-column extraction are modeled DEEPLY as
``lookupFieldDecision`` / ``singleColumnKeys``, both I ops, not axiomatized
callees). There is nothing for the axiom lane to probe here, and the gate ignores
``AXIOM_TESTS`` regardless. (The sibling's A-reference soundness + containment
probes are a G-AX concern and are dropped per the porting map.)
"""
from pathlib import Path

INSTANCE = "django__django-12774"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). ----

# The whole frozen impl BODY (the mutable-accumulator `while` scan plus the
# guard). Rivals replace it with a straight-line computable impl so their
# extracted program reduces under `decide`.
_IMPL = (
    "    let mut uniqueFields : List String := []\n"
    "    let mut i := constraints.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ constraints.length\n"
    "      invariant uniqueFields = singleColumnKeys (constraints.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let g := constraints[i - 1]!\n"
    "      uniqueFields := soleColumn g ++ uniqueFields\n"
    "      i := i - 1\n"
    "    if (fieldName != \"pk\") && (!fieldUnique) && (!uniqueFields.contains fieldName) then\n"
    "      return Except.error ValidationErr.fieldNotUnique\n"
    "    else\n"
    "      return Except.ok ()"
)

# The final decision guard line only (for the conjunct-reorder positive control,
# which keeps the loop and only commutes the three independent conjuncts).
_GUARD = (
    "    if (fieldName != \"pk\") && (!fieldUnique) && (!uniqueFields.contains fieldName) then"
)

# The frozen `prove_correct` tactic body (drop-step + simp). Rivals and the
# direct-decision controls collapse it to `loom_solve` (the loop is gone);
# the reorder control keeps it verbatim.
_PROOF = (
    "prove_correct validateLookupField by\n"
    "  loom_solve\n"
    "  rw [singleColumnKeys_drop_step constraints i (by omega) (by omega)]\n"
    "  simp_all\n"
    "  all_goals simp_all [lookupFieldDecision]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"

_PROOF_LOOMSOLVE = "prove_correct validateLookupField by\n  loom_solve"


def _direct(new_body: str) -> str:
    """Full variant: replace the loop-based body AND collapse the proof to
    `loom_solve` (the drop-step lemma is unused once the loop is gone)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, _PROOF_LOOMSOLVE)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `validateLookupFieldTester f u c = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict. The report carrier is `Except`, whose DecidableEq the
# ---- postcondition-decidability derivation needs, so the witness derives it
# ---- first (an instance, not an assumption). ----
_TESTER = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for validateLookupField\n"
    "prove_precondition_decidable_for validateLookupField\n"
    "prove_postcondition_decidable_for validateLookupField\n"
    "derive_tester_for validateLookupField\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-decision",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the GROUNDED decision directly, no
        # loop at all — maximally structurally different from the frozen
        # scan-and-accumulate. `out` IS `lookupFieldDecision ...` so the single
        # ensures holds trivially; the loop-specific drop-step lemma is unused so
        # the proof collapses to `loom_solve`.
        "module": _direct(
            "    return lookupFieldDecision fieldName fieldUnique constraints"),
        "rationale": "the cheapest honest correct impl returns the grounded "
                     "decision `lookupFieldDecision fieldName fieldUnique "
                     "constraints` directly (no loop). `out` IS that expression "
                     "so `out = lookupFieldDecision ...` holds trivially and "
                     "`loom_solve` closes. If this fails => the spec is over-fit "
                     "to the scan-and-accumulate code shape (SPEC-TOO-STRONG). "
                     "Also the honest no-ungrounded-echo control: singleColumnKeys "
                     "IS the real work, so a direct return is correct, not a cheat.",
    },
    {
        "id": "pos-reorder-conjuncts",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: the three independent conjuncts of
        # the decision guard are reordered (test individual-uniqueness before the
        # primary-key exemption). `&&` is commutative and the decision pins the
        # boolean VALUE, not the term order, so the reorder is behaviour-
        # preserving; the scan loop and the frozen proof are kept verbatim.
        "module": _swap(
            _BASE, _GUARD,
            "    if (!fieldUnique) && (fieldName != \"pk\") && "
            "(!uniqueFields.contains fieldName) then"),
        "rationale": "commuting the three conjuncts of the decision guard "
                     "computes the same boolean, so `out = lookupFieldDecision "
                     "...` is unchanged and the frozen loop proof closes verbatim. "
                     "If a faithful correct reshape could NOT verify => the spec is "
                     "over-fit to the conjunct order (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-branch-ladder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: an early-accept nested-if LADDER
        # instead of one three-conjunct guard, testing the sub-conditions in the
        # opposite polarity (accept-first rather than reject-first). This is the
        # shape the nagini sibling's reorder control actually had (two early
        # `return False` branches), reachable here as an `if/else if` value ladder
        # since Velvet bans early return inside a branch chain. Equivalent by
        # boolean case analysis, NOT by definitional unfolding: `loom_solve` alone
        # leaves the goal open, so the proof must genuinely re-derive the decision
        # over all eight sub-condition combinations.
        "module": _direct(
            "    let e : Except ValidationErr Unit :=\n"
            "      if fieldName = \"pk\" then Except.ok ()\n"
            "      else if fieldUnique then Except.ok ()\n"
            "      else if (singleColumnKeys constraints).contains fieldName then "
            "Except.ok ()\n"
            "      else Except.error ValidationErr.fieldNotUnique\n"
            "    return e").replace(
            _PROOF_LOOMSOLVE,
            "prove_correct validateLookupField by\n"
            "  loom_solve\n"
            "  by_cases h1 : fieldName = \"pk\" <;> by_cases h2 : fieldUnique <;>\n"
            "    by_cases h3 : (singleColumnKeys constraints).contains fieldName <;>\n"
            "    simp_all [lookupFieldDecision]"),
        "rationale": "an accept-first nested-if ladder over the three "
                     "sub-conditions computes the same decision as the frozen "
                     "reject-first conjunction, so `out = lookupFieldDecision ...` "
                     "still holds. Unlike `pos-direct-decision` this is NOT "
                     "definitionally the frozen expression — `loom_solve` alone "
                     "leaves the goal open (measured EXIT 1) and the proof must "
                     "case-split all three sub-conditions to close it, so the case "
                     "tests that the spec admits a genuinely different control "
                     "shape. If a faithful correct reshape could NOT verify => the "
                     "spec is over-fit to the guard's polarity/shape "
                     "(SPEC-TOO-STRONG). Verified live EXIT 0.",
    },
    {
        "id": "pos-filter-map-extraction",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: build the covered-key list by
        # FILTER-then-MAP over the guarantees rather than by the frozen
        # front-recursive `singleColumnKeys` fold. Extensionally equal but NOT
        # definitionally so — the equality needs its own induction on the
        # guarantee list, supplied inline in the tactic body (no new top-level
        # lemma, so the variant stays in scope). This is the reshape that most
        # directly probes whether the spec pins the covered-key SET or merely the
        # frozen fold's syntactic form.
        "module": _direct(
            "    let uniqueFields : List String :=\n"
            "      (constraints.filter (fun g => g.length = 1)).map (fun g => g[0]!)\n"
            "    if (fieldName != \"pk\") && (!fieldUnique) && "
            "(!uniqueFields.contains fieldName) then\n"
            "      return Except.error ValidationErr.fieldNotUnique\n"
            "    else\n"
            "      return Except.ok ()").replace(
            _PROOF_LOOMSOLVE,
            "prove_correct validateLookupField by\n"
            "  have hk : ∀ cs : List (List String),\n"
            "      (cs.filter (fun g => g.length = 1)).map (fun g => g[0]!) = "
            "singleColumnKeys cs := by\n"
            "    intro cs; induction cs with\n"
            "    | nil => rfl\n"
            "    | cons g gs ih => simp [singleColumnKeys, soleColumn, List.filter]\n"
            "                      split <;> simp_all\n"
            "  simp only [hk]\n"
            "  loom_solve\n"
            "  all_goals simp_all [lookupFieldDecision]"),
        "rationale": "extracting the covered keys by filter-then-map over the "
                     "guarantees is extensionally equal to the frozen "
                     "front-recursive fold but NOT definitionally equal — the "
                     "equality is discharged by an inline induction on the "
                     "guarantee list. So this control establishes the spec pins "
                     "the covered-key CONTENT rather than the fold's syntactic "
                     "shape, complementing `pos-direct-decision` (which is "
                     "definitionally the frozen expression and so tests the shape "
                     "question not at all). If it could not verify => "
                     "SPEC-TOO-STRONG. Verified live EXIT 0.",
    },
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The method carries NO `require` clause, so no input is excluded and the
        # usual "a normal input satisfies the precondition" probe is vacuous. The
        # residual admissibility risk on a total domain is a DEGENERATE /
        # unsatisfiable post-image — a spec no impl can meet reads exactly like a
        # spec every impl meets. This discharges an in-region assert that the
        # decision genuinely VARIES with each of its three sub-conditions:
        # rejection fires only when all three hold ("x", false, []), and flipping
        # ANY ONE of them (the primary-key alias / an individually-unique key /
        # the sole column of a single-column guarantee) flips the outcome to
        # accept. The direct-decision body is kept so the ensures still discharges.
        "module": _swap(
            _direct(
                "    assert (with_name_prefix `admiss\n"
                "      (lookupFieldDecision \"x\" false [] = "
                "Except.error ValidationErr.fieldNotUnique ∧\n"
                "       lookupFieldDecision \"pk\" false [] = Except.ok () ∧\n"
                "       lookupFieldDecision \"x\" true [] = Except.ok () ∧\n"
                "       lookupFieldDecision \"x\" false [[\"x\"]] = Except.ok ()))\n"
                "    return lookupFieldDecision fieldName fieldUnique constraints"),
            _PROOF_LOOMSOLVE,
            "prove_correct validateLookupField by\n"
            "  loom_solve\n"
            "  refine ⟨?_, ?_, ?_, ?_⟩ <;> rfl"),
        "rationale": "the post-image is satisfiable AND non-degenerate: the "
                     "decision genuinely tracks all three sub-conditions — "
                     "rejection fires at (\"x\", false, []) and flipping any one "
                     "input flips it to accept (the primary-key alias, an "
                     "individually-unique key, and a key that is the sole column "
                     "of a single-column guarantee are each accepted). The "
                     "in-region assert must discharge (else an "
                     "unsatisfiable/degenerate obligation would read as trivially "
                     "met) and the direct-decision body keeps `out = "
                     "lookupFieldDecision ...`. Verified live: the true assert "
                     "builds (EXIT 0) and a falsified conjunct leaves an unsolved "
                     "goal (EXIT 1).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # that fails on the frozen solution, and each carries the refinement argument
    # that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "partial-ignore-constraints",
        "kind": "uniqueness",
        "expect": "reject",
        # The EXACT pre-fix behaviour: never consult the guarantees, decide on the
        # primary-key alias / individual-uniqueness alone. Correct on every key
        # that is the primary-key alias, individually unique, or covered by no
        # guarantee; diverges on the sub-domain where some single-column guarantee
        # covers the key.
        "module": _direct(
            "    if (fieldName != \"pk\") && (!fieldUnique) then\n"
            "      return Except.error ValidationErr.fieldNotUnique\n"
            "    else\n"
            "      return Except.ok ()"),
        "refinement": "this is the pre-fix decision (sub-condition (c) absent): a "
                      "faithful patch that never consults the guarantees ALWAYS "
                      "rejects a non-primary, non-individually-unique key. It fails "
                      "the F2P — a lookup on a key that is the sole column of one "
                      "single-column unconditional uniqueness guarantee must now "
                      "SUCCEED, but the pre-fix decision refuses it — so it does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = lookupFieldDecision ...` via "
                     "sub-condition (c): on (\"year\", false, [[\"year\"]]) the "
                     "key is the sole column of a single-column guarantee so the "
                     "spec accepts (ok), but this rival never consults the "
                     "guarantees and returns error. Refuted on the exact "
                     "F2P-shaped input.",
        "witness": _witness(
            "validateLookupFieldTester \"year\" false [[\"year\"]]"),
    },
    {
        "id": "partial-first-constraint-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: consult only the FIRST guarantee. Correct when the
        # covering single-column guarantee is at index 0 (or none exists), but
        # mis-rejects a key whose covering guarantee sits at index >= 1.
        "module": _direct(
            "    let uniqueFields : List String :=\n"
            "      if constraints.length > 0 then soleColumn constraints[0]! else []\n"
            "    if (fieldName != \"pk\") && (!fieldUnique) && "
            "(!uniqueFields.contains fieldName) then\n"
            "      return Except.error ValidationErr.fieldNotUnique\n"
            "    else\n"
            "      return Except.ok ()"),
        "refinement": "a faithful patch that only inspected the FIRST guarantee "
                      "would admit a key only when its covering single-column "
                      "guarantee is listed first. The guarantee list can carry a "
                      "multi-column (or other) guarantee before the covering "
                      "single-column one, so such a patch would still refuse the "
                      "F2P key whenever the covering guarantee is not first, and "
                      "does NOT resolve.",
        "rationale": "REJECT from `out = lookupFieldDecision ...` via "
                     "sub-condition (c) over ALL guarantees: on (\"year\", false, "
                     "[[\"b\", \"c\"], [\"year\"]]) the covering single-column "
                     "guarantee sits at index 1, so the spec accepts (ok), but "
                     "this rival (whose first guarantee is the multi-column "
                     "[\"b\",\"c\"]) rejects. Refuted where the covering guarantee "
                     "is NOT first.",
        "witness": _witness(
            "validateLookupFieldTester \"year\" false [[\"b\", \"c\"], [\"year\"]]"),
    },
    {
        "id": "weak-ignore-arity",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: treat EVERY guarantee's first column as covering,
        # dropping the single-column (`length = 1`) restriction. Correct on
        # single-column guarantees, but wrongly ACCEPTS the first column of a
        # MULTI-column guarantee.
        "module": _direct(
            "    let uniqueFields : List String := constraints.map (fun g => g[0]!)\n"
            "    if (fieldName != \"pk\") && (!fieldUnique) && "
            "(!uniqueFields.contains fieldName) then\n"
            "      return Except.error ValidationErr.fieldNotUnique\n"
            "    else\n"
            "      return Except.ok ()"),
        "refinement": "this is the patch with the single-column restriction "
                      "dropped: taking the first column of EVERY guarantee, not "
                      "only single-column ones. Such a patch would ACCEPT the "
                      "first column of a MULTI-column uniqueness guarantee, which "
                      "does not by itself make that column unique across rows — so "
                      "it would wrongly admit such a key and does NOT resolve.",
        "rationale": "REJECT from `out = lookupFieldDecision ...` via "
                     "sub-condition (c): a MULTI-column guarantee contributes "
                     "NOTHING to the covered keys (singleColumnKeys keeps only "
                     "singletons). On (\"brand\", false, [[\"brand\", \"name\"]]) "
                     "the spec rejects (error) but this rival treats \"brand\" as "
                     "covered and accepts (ok). Refuted on a multi-column "
                     "guarantee whose first column is the queried key.",
        "witness": _witness(
            "validateLookupFieldTester \"brand\" false [[\"brand\", \"name\"]]"),
    },
    {
        "id": "weak-ignore-individual-unique",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop sub-condition (b): decide without the individual-uniqueness
        # exemption. Correct on every non-individually-unique key, but wrongly
        # REJECTS an individually-unique key covered by no guarantee.
        "module": _direct(
            "    let uniqueFields : List String := singleColumnKeys constraints\n"
            "    if (fieldName != \"pk\") && (!uniqueFields.contains fieldName) then\n"
            "      return Except.error ValidationErr.fieldNotUnique\n"
            "    else\n"
            "      return Except.ok ()"),
        "refinement": "dropping the individual-uniqueness exemption makes the "
                      "guard reject a key that IS individually declared unique "
                      "(when no single-column guarantee also covers it). A "
                      "faithful patch that dropped it would refuse lookups on "
                      "genuinely-unique keys — behaviour the pre-existing "
                      "(already-passing) suite relies on — so it does NOT resolve.",
        "rationale": "REJECT from `out = lookupFieldDecision ...` via "
                     "sub-condition (b): on (\"slug\", true, []) the key is "
                     "individually unique so the spec accepts (ok), but this rival "
                     "omits the `!fieldUnique` conjunct and rejects (error). "
                     "Refuted at fieldUnique = true — the only witness that "
                     "exercises the individual-uniqueness binder.",
        "witness": _witness("validateLookupFieldTester \"slug\" true []"),
    },
    {
        "id": "weak-ignore-primary-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop sub-condition (a): decide without the primary-key exemption.
        # Correct on every non-primary key, but wrongly REJECTS the primary-key
        # alias.
        "module": _direct(
            "    let uniqueFields : List String := singleColumnKeys constraints\n"
            "    if (!fieldUnique) && (!uniqueFields.contains fieldName) then\n"
            "      return Except.error ValidationErr.fieldNotUnique\n"
            "    else\n"
            "      return Except.ok ()"),
        "refinement": "dropping the primary-key exemption makes the guard reject "
                      "the primary-key alias itself (it is not flagged "
                      "individually unique and appears in no guarantee list). A "
                      "faithful patch that dropped it would refuse the DEFAULT "
                      "lookup key, breaking the pre-existing (already-passing) "
                      "suite wholesale, so it does NOT resolve.",
        "rationale": "REJECT from `out = lookupFieldDecision ...` via "
                     "sub-condition (a): on (\"pk\", false, []) the key is the "
                     "primary-key alias so the spec accepts (ok), but this rival "
                     "omits the `fieldName != \"pk\"` conjunct and rejects "
                     "(error). Refuted at fieldName = \"pk\" — the only witness "
                     "that exercises the primary-key-alias binder.",
        "witness": _witness("validateLookupFieldTester \"pk\" false []"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 4 partial-domain/weak
# rivals) plus 2 AXIOM_TESTS. This bundle models a NARROWED carrier: the decision
# over (fieldName : String, fieldUnique : Bool, constraints : List (List String))
# where each guarantee is the bare list of columns it spans — there is NO
# condition flag, because the "total" (unconditional) filter is upstream and
# unchanged, so the modeled input already contains only unconditional guarantees.
#
#   sibling case                 -> here                            disposition
#   -----------------------------------------------------------------------------
#   pos-control-direct-oracle    -> pos-direct-decision              PORTED
#   pos-control-reorder-branches -> pos-reorder-conjuncts            RE-AIMED
#                                +  pos-branch-ladder                ADDED (audit)
#   admiss-meta-constraint       -> admiss-nondegenerate             RE-AIMED
#   frame-mutate-guarantees      -> (none)                           VACUOUS
#   partial-ignore-guarantees    -> partial-ignore-constraints       PORTED
#   partial-first-guarantee-only -> partial-first-constraint-only    PORTED
#   weak-ignore-arity            -> weak-ignore-arity                PORTED
#   weak-ignore-unconditional    -> (none)                           NOT EXPRESSIBLE
#   (no sibling)                 -> weak-ignore-individual-unique     ADDED
#   (no sibling)                 -> weak-ignore-primary-key           ADDED
#   (no sibling)                 -> pos-filter-map-extraction         ADDED (audit)
#   ax-ref-sound / ax-containment-> (none)                           DROPPED
#
# 4 ported, 2 re-aimed, 1 vacuous, 1 not-expressible, 4 added, 2 dropped.
#
# ADDED BY AUDIT (pos-branch-ladder, pos-filter-map-extraction): the port's only
#   two positives were `pos-direct-decision` (definitionally the frozen
#   expression, so `loom_solve` closes it and it tests no shape question) and
#   `pos-reorder-conjuncts` (a `&&` commutation the frozen proof closes verbatim).
#   Neither forces the spec to admit a genuinely re-derived decision. These two do:
#   the ladder needs an eight-way case split (measured: `loom_solve` alone leaves
#   the goal open) and the filter-map extraction needs its own induction to relate
#   a non-definitionally-equal covered-key computation to the frozen fold. Both
#   VERIFY (EXIT 0), so the spec is not over-fit to the frozen code shape.
#
# PORTED (pos-direct-decision): the sibling's cheapest honest correct impl
#   returns the grounded pin directly (no loop). Here the direct-decision impl
#   returns `lookupFieldDecision fieldName fieldUnique constraints`; the
#   loop-specific drop-step lemma is unused so `loom_solve` closes. Verified EXIT 0.
# RE-AIMED (pos-reorder-conjuncts): the sibling reorders the two early-accept
#   branches (pk vs individually-unique). This carrier has no early-return
#   branches — the decision is a single guard with three `&&` conjuncts — so the
#   reorder is expressed as commuting those conjuncts. `&&` is commutative and the
#   frozen loop proof closes verbatim. Verified EXIT 0.
# RE-AIMED (admiss-nondegenerate): the sibling's admissibility asserts the only
#   precondition (Acc(list_pred, 1/2)) is establishable on the F2P-shaped input.
#   This backend has NO `require` clause, so that probe is vacuous. It is re-aimed
#   at the residual total-domain risk — a DEGENERATE/unsatisfiable post-image —
#   via an in-region assert that the decision genuinely varies with each of its
#   three sub-conditions (reject at ("x",false,[]); accept when any one input is
#   flipped). Verified live: the true assert builds EXIT 0, a falsified conjunct
#   fails EXIT 1.
# VACUOUS (frame-mutate-guarantees): the sibling carries it because the guarantee
#   list holds a fractional heap permission a rival could demand at full strength
#   and WRITE through to forge a permitting guarantee. Lean and Velvet are
#   referentially transparent — every input is an immutable value, no `mut`
#   parameter, no heap, no aliasing — so there is nothing to overwrite. No
#   substitute fabricated (per the porting map).
# NOT EXPRESSIBLE (weak-ignore-unconditional): the sibling rival drops the
#   `condition is None` (unconditional) filter so a CONDITIONAL single-column
#   guarantee is treated as permitting. This backend's guarantee carrier is a bare
#   `List String` (columns spanned) with NO condition flag — the modeled input
#   already contains only unconditional guarantees (the "total" filter is upstream
#   and unchanged). The conditional/unconditional distinction the rival abuses
#   does not exist in the modeled values, so the abstraction collapses it and no
#   discriminating witness exists (the spec has no conditional binder to
#   mishandle). Dropped with reason, per the porting map's "not actually wrong on
#   this carrier" clause — NOT omitted for difficulty.
# PORTED (partial-ignore-constraints, partial-first-constraint-only,
#   weak-ignore-arity): the pre-fix ignore-guarantees bug, the first-only scan,
#   and the drop-single-column-restriction rival port directly, each authored
#   loop-free (referencing the pure-region defs) with a machine-checked witness
#   that ELABORATES against the rival (EXIT 0) and FAILS against gold (EXIT 1).
#   NOTE on what the gold EXIT 1 means here: see "WITNESS MECHANICS" above. The
#   frozen `while` loop is kernel-irreducible, so the gold-side failure is an
#   unfolding failure ("reduction got stuck"), input-independent, and NOT a
#   semantic refutation. The non-tautology evidence for these witnesses is
#   rival-side (a `= false` witness fails at points where the rival agrees with
#   the frozen decision) plus the observable-difference derivation per case.
# ADDED (weak-ignore-individual-unique, weak-ignore-primary-key): the frozen
#   decision's single ensures carries three independent sub-conditions
#   (a) primary-key exemption, (b) individual-uniqueness exemption, (c) the
#   single-column-guarantee allowance. The sibling attacks (c) directly and pins
#   (a)/(b) only as ENTAILED `Implies` clauses with no dedicated rival. These two
#   ADDED rivals attack (a) and (b) directly (drop each exemption) so every
#   sub-condition is defended AND attacked. Each carries a witness that
#   discriminates (EXIT 0 rival / EXIT 1 gold).
# DROPPED (ax-ref-sound, ax-containment): the sibling's axiom lane re-runs the
#   real-callee soundness + containment checks. That is a G-AX concern; this
#   bundle declares no axiom and no A-reference deep model (the decision and the
#   single-column extraction are modeled deeply, both I ops), so there is nothing
#   for the axiom lane to probe and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / SUB-CONDITION COVERAGE of the five reject witnesses:
#   fieldName    — "year", "year", "brand", "slug", "pk": varied (never pinned at
#                  one value), so a rival mishandling only a specific key could not
#                  hide.
#   fieldUnique  — false (four rivals), true (weak-ignore-individual-unique): both
#                  polarities exercised; the true value is the only witness that
#                  probes sub-condition (b).
#   constraints  — [["year"]], [["b","c"],["year"]] (len 2, covering guarantee NOT
#                  first), [["brand","name"]] (multi-column), [] (EMPTY, twice):
#                  varied in length, arity, and content.
#   SUB-CONDITIONS: (a) primary-key attacked by weak-ignore-primary-key; (b)
#     individual-uniqueness attacked by weak-ignore-individual-unique; (c)
#     single-column-guarantee allowance attacked by partial-ignore-constraints,
#     partial-first-constraint-only, and weak-ignore-arity. Each of the three
#     independent sub-conditions is both defended (verify controls) and attacked.
#   All five reject witnesses probe DISTINCT input points (pts=5).
#
# INDEPENDENT SPEC-TOO-WEAK SWEEP (audit, attack D). Eight FURTHER wrong impls the
# battery does not contain were built against the frozen spec, aimed at what the
# five shipped rivals leave unattacked. ALL EIGHT were rejected, each on the
# `ensures_1: out = lookupFieldDecision ...` goal (a postcondition failure, not a
# tactic artifact — the residual goal was read in every case):
#   always-accept                            -> rejected
#   always-reject                            -> rejected
#   sole column taken as the LAST element    -> rejected
#   arity test off by one (`length ≤ 1`, so  -> rejected
#     an EMPTY guarantee contributes "")
#   flatten ALL guarantees (any column of    -> rejected
#     any guarantee treated as covering)
#   wrong primary-key sentinel ("id")        -> rejected
#   drop the LAST guarantee (`dropLast`)     -> rejected
#   `||` for the final `&&` conjunct         -> rejected
# No wrong impl was found that the frozen spec admits, so no spec hole is recorded.
#
# INDEPENDENT SPEC-TOO-STRONG SWEEP (audit, attack E). Four correct reshapes were
# built; two are now shipped as positives above (the ladder and the filter-map
# extraction, both EXIT 0). A `flatMap soleColumn` reshape hit a Velvet/Lean
# TOOLING failure, not a spec rejection — `error: not a triple:
# _inhabitedExprDummy` followed by `PANIC at Lean.SMap.find!` inside the
# elaborator, i.e. the surgery leaves a file the toolchain cannot process. That is
# a bug to report upstream, not evidence about the spec, so it is recorded and not
# counted either way. A forward-direction `while` loop (take-based invariant) was
# not landed: it needs a take-side step lemma the frozen file does not carry and a
# variant may not add a new top-level lemma, so this one is UNCERTAIN rather than a
# claimed hole.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model, so there is nothing there to probe.
AXIOM_TESTS = []
