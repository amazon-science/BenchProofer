"""properties.py — G-PBT falsification battery for django__django-13807 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
each ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must ELABORATE against the rival and FAIL, by
DECIDING, against a correct impl of the same spec. Here that second subject is
the shared ``witness_reference`` rather than the frozen solution; see WITNESS
MECHANICS).

DEFENDED SURFACE. Two contracted methods that assemble ordered sequences of
statement strings over ``List Char`` identifiers:

  buildCheckStatements (tables : List (List Char))
      return (out : List (List Char))
    ensures out = checkStmts tables

  buildViolationStatements (violations : List Violation)
      return (out : List (List Char))
    ensures out = violationStmts violations

Each ``ensures`` is grounded in the method's own input through the transparent
pure functions ``checkStmts`` / ``violationStmts`` (front-recursive folds), which
in turn call ``fkCheckSql`` / ``fkListSql`` / ``selectSql`` — each a fixed
sequence of literal fragments concatenated around the QUOTED form of every
embedded identifier. The single LOAD-BEARING discriminator, at every position, is
that the embedded identifier is its ``quoteIdent name`` form (a bare identifier
wrapped in double quotes; an already-double-quoted one left unchanged), NOT the
bare identifier. ``quoteIdent`` is a fully-unfolded ``def`` grounded ENTIRELY in
its input code points (the ``axioms`` region declares nothing; it is a deep
A-reference validated ``== the real quoter`` by axiom_check.py, G-AX's job) — so
there is no opaque answer key to echo, and the cheapest wrong impl is to splice
the BARE identifier (``quoteIdent name != name`` for a reserved word such as
``order``).

BINDER STRUCTURE (read before judging binder coverage).
  * ``buildCheckStatements`` has ONE binder, ``tables``. The reject witnesses vary
    it in length (a one-element list, a two-element list).
  * ``buildViolationStatements`` has ONE binder, ``violations : List Violation``.
    Each ``Violation`` carries three quoted identifier positions — ``table``
    (quoted by both ``fkListSql`` and ``selectSql``), ``pk`` and ``col`` (quoted
    by ``selectSql``). The reject witnesses vary WHICH position carries the
    reserved-word identifier so that each quoted position is attacked by a rival
    that mishandles ONLY that position.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as a
    MANDATORY rival (two cases: mutate the read-only ``table_name`` / ``ident_a``
    in place to manufacture the delimited bytes) because those inputs are held at
    a fractional heap permission a write would exceed. Lean and Velvet are
    referentially transparent: every input here is an immutable value, both
    methods declare their argument read-only (no ``mut`` binder), there is no heap
    and no aliasing — so there is no read-only input to overwrite and no
    permission system to trip. Not fabricated (per the porting map, this class is
    legitimately vacuous on Lean/Velvet).
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
    loop in the impl (2 loops here, measures ``i``). A rival that loops without
    a measure is refused outright (``Decreasing annotations are required in
    total correctness semantics``), and a rival that supplies a CONSTANT
    measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE ECHO — N/A. ``checkStmts`` / ``violationStmts`` /
    ``fkCheckSql`` / ``fkListSql`` / ``selectSql`` / ``quoteIdent`` are concrete
    ``def``s spelled out as closed-form concatenations of the inputs (no opaque
    answer key to echo); the nagini sibling notes the same — its ``delimit``
    oracle is GROUNDED in the input code points. The honest positive controls
    cover the cheapest correct impl (evaluate the pure folds directly).
  * PARTIAL-DOMAIN / BARE-IDENTIFIER — the heart of the port, exactly as in
    nagini. The cheapest WRONG impl splices the BARE identifier (the prepatch bug
    itself) or a constant quoted stand-in; each is correct only on the sub-domain
    where the input's quoted form equals the bare/constant text, and wrong on
    every reserved-word identifier the F2P exercises.

WITNESS MECHANICS (specific to this carrier) — READ THE LIMITATION. The spec is a
``method`` CONTRACT, not a bare predicate, so a witness reaches the postcondition
through Velvet's own tester machinery: ``<name>Tester <args> = false`` says the
extracted program's result violates the postcondition at that concrete input.
Every reject witness ``decide``s over concrete ``Char`` literals — ``quoteIdent``
computes on literals, so no witness binds a hypothesis and there is no
joint-satisfiability obligation. Checked in a file whose ``prove_correct`` blocks
are stripped, so no tactic script can mask the verdict.

The rival half is a genuine SEMANTIC refutation: against each loop-free rival
``decide`` reduces the extracted program to a literal and proves the tester
``false`` at the probed input (measured, exit 0).

THE FROZEN SOLUTION CANNOT SERVE AS THE SECOND SUBJECT, so every reject case
names a ``witness_reference`` instead. The extracted program of the FROZEN impl
contains a ``while`` loop whose fixpoint elaborates through ``Classical.choice``
and does not kernel-reduce, so against gold ``decide`` fails with "did not reduce
to isTrue or isFalse" — a STUCK REDUCTION, not a refutation. That failure would
arise for any loop-bearing impl, right or wrong, so gold's exit code carries NO
information and a witness scored against it would attest to a refutation never
performed. Measured, not assumed: ``decide``/``rfl``/``simp``/``simp_arith``/
``grind``/``norm_num``/``unfold``+``decide``/``simp_all``+``decide`` were each
built against the frozen solution and ALL failed identically, and the TRUE
statement (``… = true``) is equally unprovable there — which is what shows the
stuck reduction is a property of the loop fixpoint rather than of the claim's
truth. No tactic choice can strengthen a gold-side leg on this carrier.

The repair is the one the protocol prescribes: ``_LOOPFREE`` — both methods
collapsed to the closed forms their ``ensures`` clauses name, loop-free so its
testers reduce, and correct by construction. The gate checks it shares the frozen
spec and VERIFIES (measured: exit 0, ~10s) before refuting any witness against
it, and an impl the verifier accepts cannot violate its own spec, so a genuine
witness must still fail there. It is also shipped as the ``pos-both-closed-form``
positive, so the battery records that loop-freeness — the one property it shares
with every rival — is not what any rival is rejected for.

Against ``_LOOPFREE`` the second half DECIDES, which is the whole point. Measured
for all nine reject cases: rival exit 0, reference exit 1 with "Tactic ``decide``
proved that the proposition ``<name>Tester …  = false`` is false" — i.e. the
tester is TRUE there, the postcondition HOLDS, and the witness's claim is
genuinely refuted on a correct impl at the same input. No case's reference-side
build was stuck.

The check is therefore truth-tracking rather than loop-presence-tracking, and
that was verified adversarially, twice.

FORGERY TEST 1 — flip the claim. For each of the nine reject cases, a second file
differing from the witness ONLY in what it claims (``= true`` in place of
``= false``, i.e. asserting the tester HOLDS at the probed input) was built
against all three subjects. The reference side SWAPS: the real claim fails there
(exit 1, ``decide`` proved it false) and the flipped claim SUCCEEDS (exit 0,
clean), so the reference's exit code is a function of what is claimed — which is
exactly what admissible evidence means. Against the rival the pair swaps the
other way (real claim exit 0, flipped claim exit 1). Against the frozen solution
BOTH polarities fail with the byte-identical ``did not reduce to `isTrue` or
`isFalse` `` — which is the measurement proving gold's exit code carries no
information here, and hence why the reference is the subject.

FORGERY TEST 2 — an AGREEMENT point. ``buildCheckStatementsTester
["\"order\"".toList] = false`` against the bare-splice rival, an already-quoted
identifier where the bare and quoted forms coincide, fails to elaborate against
that rival (``decide`` proves it false, exit 1), so it cannot clear the first
half. Under a gold-side leg that same forgery would have cleared both halves.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; ``quoteIdent`` is
a deep A-reference validated ``== the real backend quoter`` by axiom_check.py
(G-AX's job — see mapping.md §3), not a consumed contract, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13807"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies WHOLLY inside one impl region (between -- impl-start and
# -- impl-end) or inside a prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only these
# keeps markers.same_spec True and each prove_correct statement byte-identical
# (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of buildCheckStatements: the backward accumulating
# loop plus the return. Reject rivals / closed-form positives replace this.
_M1_IMPL = (
    "    let mut result : List (List Char) := []\n"
    "    let mut i := tables.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ tables.length\n"
    "      invariant result = checkStmts (tables.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let t := tables[i - 1]!\n"
    "      result := fkCheckSql t :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# The WHOLE executable body of buildViolationStatements.
_M2_IMPL = (
    "    let mut result : List (List Char) := []\n"
    "    let mut i := violations.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ violations.length\n"
    "      invariant result = violationStmts (violations.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let v := violations[i - 1]!\n"
    "      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# The single per-row assignment inside each loop body (loop-preserving positive
# controls stage the built statement into a named local before prepending).
_M1_STEP = (
    "      let t := tables[i - 1]!\n"
    "      result := fkCheckSql t :: result\n"
)
_M2_STEP = (
    "      let v := violations[i - 1]!\n"
    "      result := fkListSql v.table :: selectSql v.pk v.col v.table :: result\n"
)

# The FULL frozen proof bodies. A closed-form positive control (loop removed)
# retunes its tactic body to a bare `loom_solve`; the tactic body is elided from
# the spec view, so this is a proof reshape, not a spec change. Each is unique.
_M1_PROOF = (
    "prove_correct buildCheckStatements by\n"
    "  loom_solve\n"
    "  rw [checkStmts_drop_step tables i (by omega) (by omega)]\n"
    "  simp_all"
)
_M2_PROOF = (
    "prove_correct buildViolationStatements by\n"
    "  loom_solve\n"
    "  rw [violationStmts_drop_step violations i (by omega) (by omega)]\n"
    "  simp_all"
)
_M1_PROOF_BARE = "prove_correct buildCheckStatements by\n  loom_solve"
_M2_PROOF_BARE = "prove_correct buildViolationStatements by\n  loom_solve"

assert _BASE.count(_M1_IMPL) == 1, "M1 impl region drifted"
assert _BASE.count(_M2_IMPL) == 1, "M2 impl region drifted"
assert _BASE.count(_M1_PROOF) == 1, "M1 proof drifted"
assert _BASE.count(_M2_PROOF) == 1, "M2 proof drifted"


def _m1_closed(body, ):
    """buildCheckStatements: replace the loop with a closed form AND retune the
    loop-tuned proof to a bare `loom_solve` (soundness positive)."""
    return _swap(_swap(_BASE, _M1_IMPL, body), _M1_PROOF, _M1_PROOF_BARE)


def _m2_closed(body):
    return _swap(_swap(_BASE, _M2_IMPL, body), _M2_PROOF, _M2_PROOF_BARE)


# The shared WITNESS REFERENCE: BOTH methods collapsed to their closed forms
# (loop-free, so the extracted testers kernel-reduce) with both loop-tuned proof
# scripts retuned to a bare `loom_solve`. Correct by construction — it returns
# exactly the post-image each `ensures` names — and measured to VERIFY (exit 0),
# which is the contract the gate independently re-checks before using it. Every
# reject case names this as its `witness_reference` so the discrimination half is
# decided against an impl that satisfies the spec AND reduces, rather than
# against the frozen loop (see WITNESS MECHANICS in the module docstring). It is
# ALSO shipped as the `pos-both-closed-form` positive below, so the battery
# itself records that loop-freeness is not what any rival is rejected for.
_LOOPFREE = _swap(
    _swap(
        _swap(_swap(_BASE, _M1_IMPL, "    return (checkStmts tables)"),
              _M2_IMPL, "    return (violationStmts violations)"),
        _M1_PROOF, _M1_PROOF_BARE),
    _M2_PROOF, _M2_PROOF_BARE)


# ADMISSIBILITY (added by a later audit; see the accounting note). Discharged BY
# EVALUATION at a concrete F2P-SHAPED input, as a `have`, BEFORE the frozen
# obligation is closed verbatim. The analogue of PRECOND-TOO-STRONG on a total
# carrier with no `require` clause is the OBLIGATION being unsatisfiable at
# exactly the input the failing test exercises: a post-image no computation can
# hit, or one whose value at that point is not the one the statement builders must
# produce. Each `have` exhibits a witness `out` for one obligation at a
# reserved-word identifier and pins its value by `decide`, so if either
# post-image were unsatisfiable there — or evaluated to anything other than the
# quoted-identifier form — the `have` could not be discharged and the case would
# FAIL. The frozen loop-tuned script still closes both real obligations
# afterwards, so nothing is weakened; only the elided tactic body changes.
_M1_PROOF_ADMISS = r'''prove_correct buildCheckStatements by
  have hadm1 : ∃ out : List (List Char),
      out = checkStmts ["order".toList]
        ∧ out = ["PRAGMA foreign_key_check(".toList ++ "\"order\"".toList
                  ++ ")".toList] :=
    ⟨checkStmts ["order".toList], rfl, by decide⟩
  have hadm2 : ∃ out : List (List Char),
      out = violationStmts
              [{table := "order".toList, pk := "id".toList, col := "order_id".toList}]
        ∧ out = ["PRAGMA foreign_key_list(".toList ++ "\"order\"".toList ++ ")".toList,
                 "SELECT ".toList ++ "\"id\"".toList ++ ", ".toList
                   ++ "\"order_id\"".toList ++ " FROM ".toList
                   ++ "\"order\"".toList ++ " WHERE rowid = %s".toList] :=
    ⟨_, rfl, by decide⟩
  loom_solve
  rw [checkStmts_drop_step tables i (by omega) (by omega)]
  simp_all'''


def _m1_reject(body):
    """buildCheckStatements: replace the loop with a loop-free wrong closed form,
    keeping the frozen proof (its failure to close is the intended rejection; the
    witness — not the tactic failure — is what the gate scores)."""
    return _swap(_BASE, _M1_IMPL, body)


def _m2_reject(body):
    return _swap(_BASE, _M2_IMPL, body)


# A wrong closed form that additionally gets a BEST-EFFORT proof attempt instead
# of the loop-tuned frozen script. Keeping the frozen script would leave the
# rejection ambiguous (it is tuned to the loop's form, so it cannot close over a
# loop-free body whether that body is right or wrong); a `first | …` ladder that
# tries reflexivity, the unfolded simp set, `grind` and `decide` removes the
# tactic-mismatch reading, so a rival that STILL fails to verify fails on the
# obligation itself. The tactic body is elided from the spec view, so this is a
# proof reshape, not a spec change.
_M1_PROOF_TRY = (
    "prove_correct buildCheckStatements by\n"
    "  loom_solve\n"
    "  first\n"
    "  | rfl\n"
    "  | simp_all [checkStmts, fkCheckSql, quoteIdent]\n"
    "  | grind\n"
    "  | decide"
)
_M2_PROOF_TRY = (
    "prove_correct buildViolationStatements by\n"
    "  loom_solve\n"
    "  first\n"
    "  | rfl\n"
    "  | simp_all [violationStmts, fkListSql, selectSql, quoteIdent]\n"
    "  | grind\n"
    "  | decide"
)


def _m1_reject_try(body):
    return _swap(_swap(_BASE, _M1_IMPL, body), _M1_PROOF, _M1_PROOF_TRY)


def _m2_reject_try(body):
    return _swap(_swap(_BASE, _M2_IMPL, body), _M2_PROOF, _M2_PROOF_TRY)


# ---- witness preamble. `<name>Tester <args> = false` reaches the method
# ---- postcondition through Velvet's tester machinery; checked in a file whose
# ---- `prove_correct` blocks have been stripped. Every witness closes by
# ---- `decide` over concrete Char literals (quoteIdent computes on literals).
def _w1(arg):
    return (
        "extract_program_for buildCheckStatements\n"
        "prove_precondition_decidable_for buildCheckStatements\n"
        "prove_postcondition_decidable_for buildCheckStatements\n"
        "derive_tester_for buildCheckStatements\n\n"
        f"example : buildCheckStatementsTester {arg} = false := by\n  decide\n"
    )


def _w2(arg):
    return (
        "extract_program_for buildViolationStatements\n"
        "prove_precondition_decidable_for buildViolationStatements\n"
        "prove_postcondition_decidable_for buildViolationStatements\n"
        "derive_tester_for buildViolationStatements\n\n"
        f"example : buildViolationStatementsTester {arg} = false := by\n  decide\n"
    )


def _viol(table, pk, col):
    return (f'{{table := "{table}".toList, pk := "{pk}".toList, '
            f'col := "{col}".toList}}')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-check-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image names
        # directly (a maximally different control-flow shape: no loop, no
        # accumulator). The loop-specific proof is retuned to a bare `loom_solve`.
        "module": _m1_closed("    return (checkStmts tables)"),
        "rationale": "a loop-free impl that returns the statement sequence "
                     "directly must satisfy `out = checkStmts tables`; "
                     "`checkStmts` is a fully-unfolded fold over the input (not an "
                     "opaque answer key), so evaluating it IS the correct "
                     "computation. A correct reshape verifying is exactly what "
                     "SPEC-TOO-STRONG would deny.",
    },
    {
        "id": "pos-violation-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _m2_closed("    return (violationStmts violations)"),
        "rationale": "a loop-free impl returning `violationStmts violations` "
                     "directly must satisfy `out = violationStmts violations`; the "
                     "post-image is a grounded fold, not an oracle, so evaluating "
                     "it is the honest cheapest correct impl. If it fails => "
                     "SPEC-TOO-STRONG.",
    },
    {
        # The shared `witness_reference` source, shipped as a case in its own
        # right. The gate re-verifies it before refuting any witness against it,
        # but recording it HERE is what shows loop-freeness is not the property
        # any rival is rejected for: this impl is loop-free exactly as every
        # rival is, and it VERIFIES.
        "id": "pos-both-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": "BOTH methods collapsed to the closed forms their `ensures` "
                     "clauses name, with both loop-tuned proof scripts retuned to a "
                     "bare `loom_solve`. This is the impl every reject case names as "
                     "its `witness_reference`, so the battery records that it "
                     "verifies: the reject lane's discrimination half is decided "
                     "against a correct impl of THIS spec, and loop-freeness — the "
                     "one thing it shares with every rival — is therefore not what "
                     "any rival is rejected for. If it fails => SPEC-TOO-STRONG, and "
                     "every reject case's witness evidence collapses with it.",
    },
    {
        "id": "pos-check-let-staged",
        "kind": "soundness",
        "expect": "verify",
        # Keep the frozen backward loop and its invariants BYTE-IDENTICAL; only
        # stage the per-row statement into a named local before prepending.
        # Observationally identical, so the frozen proof closes untouched.
        "module": _swap(
            _BASE, _M1_STEP,
            "      let t := tables[i - 1]!\n"
            "      let s := fkCheckSql t\n"
            "      result := s :: result\n"),
        "rationale": "a loop-preserving reshape that binds the per-row statement to "
                     "a named local before prepending computes the identical "
                     "accumulator each step, so every invariant and "
                     "`out = checkStmts tables` still discharge under the frozen "
                     "proof. A faithful reshape MUST verify, else the clause is "
                     "over-fit to the impl FORM => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-violation-let-staged",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _M2_STEP,
            "      let v := violations[i - 1]!\n"
            "      let a := fkListSql v.table\n"
            "      let b := selectSql v.pk v.col v.table\n"
            "      result := a :: b :: result\n"),
        "rationale": "a loop-preserving reshape that binds each row's two statements "
                     "to named locals before prepending is observationally "
                     "identical, so every invariant and "
                     "`out = violationStmts violations` still discharge under the "
                     "frozen proof. If it fails => SPEC-TOO-STRONG.",
    },

    # ---- ADDED BY AUDIT: non-definitional correct reshapes ----------------
    # The two `*-let-staged` positives above bind the statement to a local before
    # prepending, which is DEFINITIONALLY equal to the inlined expression — so
    # they are honest but test little beyond elaboration. These two are
    # extensionally equal to the frozen post-image but NOT definitionally: the
    # closed form is a `map` / `flatMap` over the input where the post-image is a
    # front-recursive fold, so closing the obligation needs a real induction that
    # the frozen drop-step script does not supply. Measured: both verify.
    {
        "id": "pos-check-map-induction",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _M1_IMPL, "    return (tables.map fkCheckSql)"),
            _M1_PROOF,
            "prove_correct buildCheckStatements by\n"
            "  have key : ∀ l : List (List Char), l.map fkCheckSql = checkStmts l := by\n"
            "    intro l; induction l with\n"
            "    | nil => rfl\n"
            "    | cons hd tl ih => simp [checkStmts_cons, ih]\n"
            "  loom_solve\n"
            "  all_goals simp_all [key]"),
        "rationale": "`tables.map fkCheckSql` is extensionally equal to the "
                     "front-recursive `checkStmts` fold but NOT definitionally "
                     "equal — the equality needs a list induction, supplied here as "
                     "an in-tactic `have`. That is what makes this a real "
                     "SPEC-TOO-STRONG probe where the let-staged positives are not: "
                     "the clause is shown to pin the SEQUENCE OF STATEMENTS rather "
                     "than the recursion shape the frozen impl happens to use. If a "
                     "faithful reshape at this distance could not verify, the clause "
                     "would be over-fit to the fold => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-violation-flatmap-induction",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _M2_IMPL,
                  "    return (violations.flatMap (fun v =>\n"
                  "      [fkListSql v.table, selectSql v.pk v.col v.table]))"),
            _M2_PROOF,
            "prove_correct buildViolationStatements by\n"
            "  have key : ∀ l : List Violation,\n"
            "      l.flatMap (fun v => [fkListSql v.table, selectSql v.pk v.col v.table])\n"
            "        = violationStmts l := by\n"
            "    intro l; induction l with\n"
            "    | nil => rfl\n"
            "    | cons hd tl ih => simp [violationStmts_cons, ih]\n"
            "  loom_solve\n"
            "  all_goals simp_all [key]"),
        "rationale": "the `flatMap` form emits the same two statements per row as the "
                     "front-recursive `violationStmts` fold, but the two are only "
                     "extensionally equal — closing the obligation needs the list "
                     "induction supplied as an in-tactic `have`. A non-definitional "
                     "correct reshape verifying is what shows "
                     "`out = violationStmts violations` pins the statement SEQUENCE "
                     "and not the impl's recursion shape. If it fails => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY / PRECOND-TOO-STRONG — the third direction this gate exists
    # to test. Neither method declares a `require`, so the analogue on this total
    # carrier is the OBLIGATION being unsatisfiable at an F2P-shaped input; the
    # case discharges it there by evaluation before closing the frozen obligation
    # verbatim. See _M1_PROOF_ADMISS.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-reserved-word",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _M1_PROOF, _M1_PROOF_ADMISS),
        "rationale": "PASS SOURCE = both obligations are SATISFIABLE at exactly the "
                     "kind of input the failing test exercises — an identifier that "
                     "is a reserved word. `hadm1` exhibits an `out` for "
                     "`out = checkStmts tables` at a one-element list holding such a "
                     "name and pins its value by `decide`; `hadm2` does the same for "
                     "`out = violationStmts violations` at one offending row whose "
                     "table identifier is that name, across both per-row statements "
                     "and all three quoted positions. Since no `require` clause "
                     "exists, this is the total-carrier analogue of "
                     "PRECOND-TOO-STRONG: if either post-image were unsatisfiable at "
                     "that concrete point — or evaluated to anything other than the "
                     "quoted-identifier form the statements must carry — the `have` "
                     "could not be discharged and the case would FAIL. The `have`s "
                     "are LIVE, not decoration: replacing either pinned value with "
                     "the BARE identifier makes the same case FAIL (measured, exit 1, "
                     "`decide` proved the equation false), so a false claim about "
                     "this point does not close. The frozen loop-tuned script still "
                     "closes both real obligations afterwards and the frozen "
                     "`ensures` are untouched — only the elided tactic body changes — "
                     "so nothing is weakened.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a DISTINCT
    # concrete input, and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- buildCheckStatements: the check-statement clause -----------------
    {
        "id": "check-constant-quote",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit a CONSTANT double-quoted stand-in (`""`) for the table identifier
        # regardless of its actual value — the identifier is dropped entirely.
        # Correct only on the empty-identifier sub-domain; wrong on every
        # reserved-word table name the F2P exercises.
        "module": _m1_reject(
            '    return (tables.map (fun _ => '
            '"PRAGMA foreign_key_check(".toList ++ [\'"\', \'"\'] ++ ")".toList))'),
        "refinement": "emitting a constant empty quoted identifier ignores the "
                      "actual table name: the real fix places the QUOTED table "
                      "name into the integrity-check statement, not a fixed empty "
                      "quoted token. A statement that names an empty identifier "
                      "does not name the reserved-word table under check, so the "
                      "constraint violation the failing test induces would go "
                      "undetected — the expected error would not be raised. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = checkStmts tables`: the post-image places "
                     "`quoteIdent t` (= the quoted table name) into each statement, "
                     "but the rival emits the fixed `\"\"` token, so the sequences "
                     "differ for any non-empty table name. Refuted at a one-element "
                     "list `[\"group\"]` (a reserved word) — the rival's statement "
                     "names `\"\"`, gold's names `\"group\"`.",
        "witness": _w1('["group".toList]'),
        "witness_reference": _LOOPFREE,
    },

    {
        "id": "check-bare-table",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch bug at the integrity-check statement: splice the BARE table
        # identifier into `PRAGMA foreign_key_check(%s)` (skip quoting). Correct
        # only on the sub-domain where the identifier's quoted form equals itself
        # (an already-double-quoted name); wrong on every reserved-word table name.
        "module": _m1_reject(
            '    return (tables.map (fun t => '
            '"PRAGMA foreign_key_check(".toList ++ t ++ ")".toList))'),
        "refinement": "this is the pre-patch integrity-check statement: the bare "
                      "table identifier spliced into `PRAGMA foreign_key_check(%s)`. "
                      "For a reserved-word table name the statement is a syntax "
                      "error (the reserved word is not quoted), which is exactly the "
                      "reported crash; the constraint check aborts before detecting "
                      "the violation, so the failing test's expected error is not "
                      "raised. It would NOT resolve.",
        "rationale": "REJECT from `out = checkStmts tables`: the post-image places "
                     "`quoteIdent t` into each statement, but the rival splices the "
                     "bare `t`, and `quoteIdent name != name` for a reserved word. "
                     "Refuted at a TWO-element list `[\"order\", \"table\"]` — a "
                     "distinct input point (and a distinct length) from the "
                     "constant-quote rival's `[\"group\"]`, so `tables` is varied in "
                     "both contents and length.",
        "witness": _w1('["order".toList, "table".toList]'),
        "witness_reference": _LOOPFREE,
    },

    # ---- buildViolationStatements: the fkListSql clause -------------------
    {
        "id": "violation-bare-fklist-table",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch bug at the listing statement: splice the BARE table
        # identifier into the foreign-key-listing statement (skip quoting). The
        # SELECT is left gold-correct, isolating the failure to fkListSql.
        "module": _m2_reject(
            "    return (violations.flatMap (fun v =>\n"
            '      ["PRAGMA foreign_key_list(".toList ++ v.table ++ ")".toList,\n'
            "       selectSql v.pk v.col v.table]))"),
        "refinement": "this is the pre-patch listing statement: the bare table "
                      "identifier spliced into `PRAGMA foreign_key_list(%s)`. For a "
                      "reserved-word table name the statement is a syntax error "
                      "(the reserved word is not quoted), so the listing lookup "
                      "fails before the value-fetch ever runs and the expected "
                      "error is not raised. It would NOT resolve.",
        "rationale": "REJECT from `out = violationStmts violations`: the post-image "
                     "places `quoteIdent v.table` into the listing statement, but "
                     "the rival splices the bare `v.table`, and "
                     "`quoteIdent name != name` for a reserved word. The SELECT is "
                     "gold-correct, isolating the failure to fkListSql. Refuted at "
                     "one row with `table = \"order\"`.",
        "witness": _w2("[" + _viol("order", "p", "c") + "]"),
        "witness_reference": _LOOPFREE,
    },

    # ---- buildViolationStatements: the selectSql pk position --------------
    {
        "id": "violation-bare-select-pk",
        "kind": "uniqueness",
        "expect": "reject",
        # Splice the BARE primary-key-column identifier into the value-fetch
        # SELECT (skip quoting it); the other two quoted positions and fkListSql
        # are gold-correct. Isolates the failure to the pk position of selectSql.
        "module": _m2_reject(
            "    return (violations.flatMap (fun v =>\n"
            "      [fkListSql v.table,\n"
            '       "SELECT ".toList ++ v.pk ++ ", ".toList ++ quoteIdent v.col\n'
            '         ++ " FROM ".toList ++ quoteIdent v.table '
            '++ " WHERE rowid = %s".toList]))'),
        "refinement": "splicing the bare primary-key-column name into the "
                      "value-fetch SELECT reproduces the pre-patch assembly at the "
                      "pk position. When the primary-key column name is a reserved "
                      "word the SELECT is a syntax error, so the offending row's "
                      "value lookup fails and the expected error is not raised. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = violationStmts violations`: the post-image "
                     "places `quoteIdent v.pk` into the SELECT, but the rival "
                     "splices the bare `v.pk`. The other positions are "
                     "gold-correct, isolating the failure to the pk position. "
                     "Refuted at one row with `pk = \"select\"` (a reserved word).",
        "witness": _w2("[" + _viol("t", "select", "c") + "]"),
        "witness_reference": _LOOPFREE,
    },

    # ---- buildViolationStatements: the selectSql col position -------------
    {
        "id": "violation-bare-select-col",
        "kind": "uniqueness",
        "expect": "reject",
        # Splice the BARE referencing-column identifier into the SELECT; the pk
        # and table quoted positions and fkListSql are gold-correct.
        "module": _m2_reject(
            "    return (violations.flatMap (fun v =>\n"
            "      [fkListSql v.table,\n"
            '       "SELECT ".toList ++ quoteIdent v.pk ++ ", ".toList ++ v.col\n'
            '         ++ " FROM ".toList ++ quoteIdent v.table '
            '++ " WHERE rowid = %s".toList]))'),
        "refinement": "splicing the bare referencing-column name into the SELECT is "
                      "the pre-patch assembly at the column position. When that "
                      "column name is a reserved word the SELECT is a syntax error, "
                      "so the value lookup fails and the expected error is not "
                      "raised. It would NOT resolve.",
        "rationale": "REJECT from `out = violationStmts violations`: the post-image "
                     "places `quoteIdent v.col` into the SELECT, but the rival "
                     "splices the bare `v.col`. Isolated to the col position "
                     "(pk/table quoted). Refuted at one row with `col = \"where\"` "
                     "— a distinct reserved word at a distinct binder position.",
        "witness": _w2("[" + _viol("t", "p", "where") + "]"),
        "witness_reference": _LOOPFREE,
    },

    # ---- buildViolationStatements: the selectSql table position -----------
    {
        "id": "violation-bare-select-table",
        "kind": "uniqueness",
        "expect": "reject",
        # Splice the BARE table identifier into the SELECT's FROM clause; fkListSql
        # (which also quotes the table) and the pk/col positions are gold-correct.
        # This attacks the table position of selectSql specifically — the position
        # a rival that fixed only fkListSql's table would still get wrong.
        "module": _m2_reject(
            "    return (violations.flatMap (fun v =>\n"
            "      [fkListSql v.table,\n"
            '       "SELECT ".toList ++ quoteIdent v.pk ++ ", ".toList '
            '++ quoteIdent v.col\n'
            '         ++ " FROM ".toList ++ v.table '
            '++ " WHERE rowid = %s".toList]))'),
        "refinement": "splicing the bare table name into the SELECT's FROM clause "
                      "is the pre-patch assembly at the SELECT's table position. "
                      "For a reserved-word table name the value-fetch SELECT is a "
                      "syntax error even though the listing statement is quoted "
                      "correctly, so the row lookup fails and the expected error is "
                      "not raised. It would NOT resolve.",
        "rationale": "REJECT from `out = violationStmts violations`: the post-image "
                     "places `quoteIdent v.table` into the SELECT's FROM clause, "
                     "but the rival splices the bare `v.table` there (fkListSql and "
                     "the pk/col positions are gold-correct). Refuted at one row "
                     "with `table = \"where\"`, distinct from the fkListSql-table "
                     "rival's `\"order\"` input, so the SELECT's own table position "
                     "is demonstrated independently of the listing statement's.",
        "witness": _w2("[" + _viol("where", "p", "c") + "]"),
        "witness_reference": _LOOPFREE,
    },

    # ---- ADDED BY AUDIT: the already-quoted sub-domain --------------------
    # Every rival above splices a BARE identifier, so each is refuted at a
    # reserved word. None of them can be refuted at an ALREADY-DOUBLE-QUOTED
    # identifier: there the bare form and the quoted form COINCIDE, so the bare
    # rivals are accidentally correct on exactly that sub-domain (measured: the
    # witness below, applied to the bare-splice rival, reports the tester TRUE).
    # `quoteIdent` has two branches and the whole battery above exercised only
    # one, leaving the second — "an identifier already double-quoted at both ends
    # is returned UNCHANGED" — undefended. This rival wraps unconditionally, so
    # it agrees with the frozen post-image on every bare identifier and differs
    # ONLY on an already-quoted one. It is the near-miss the battery was missing.
    {
        "id": "check-quote-always-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m1_reject_try(
            '    return (tables.map (fun t => "PRAGMA foreign_key_check(".toList\n'
            "      ++ ('\"' :: (t ++ ['\"'])) ++ \")\".toList))"),
        "refinement": "wrapping the table identifier in double quotes "
                      "UNCONDITIONALLY double-wraps an identifier that already "
                      "carries them, yielding a statement that names a different "
                      "(doubly-quoted) table than the one under check. The "
                      "identifier transform the fix must route every position "
                      "through quotes only once — an identifier already quoted at "
                      "both ends is passed through unchanged. Since the doubly "
                      "wrapped name does not designate the intended table, the "
                      "constraint violation would go undetected and the expected "
                      "error would not be raised. It would NOT resolve.",
        "rationale": "REJECT from `out = checkStmts tables`: the post-image places "
                     "`quoteIdent t`, whose FIRST branch returns an "
                     "already-double-quoted identifier unchanged, but this rival "
                     "always wraps. Refuted at a one-element list holding the "
                     "already-quoted identifier `\"order\"` (with its quotes) — an "
                     "input point NO other rival in this battery can be refuted "
                     "at, since every other rival splices the bare identifier and "
                     "bare == quoted exactly there. This is the second "
                     "`quoteIdent` branch, otherwise undefended.",
        "witness": _w1(r'["\"order\"".toList]'),
        "witness_reference": _LOOPFREE,
    },

    # ---- ADDED BY AUDIT: identifier ORDER inside the value-fetch ---------
    # Every rival above attacks WHETHER a position is quoted. None attacks WHICH
    # identifier lands in WHICH position: this rival quotes all three correctly
    # and merely transposes the first two, so it is refuted only by the clause
    # that fixes their order.
    {
        "id": "violation-select-transpose-pk-col",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m2_reject_try(
            "    return (violations.flatMap (fun v =>\n"
            "      [fkListSql v.table,\n"
            '       "SELECT ".toList ++ quoteIdent v.col ++ ", ".toList '
            "++ quoteIdent v.pk\n"
            '         ++ " FROM ".toList ++ quoteIdent v.table '
            '++ " WHERE rowid = %s".toList]))'),
        "refinement": "transposing the two selected identifiers makes the "
                      "value-fetch read the referencing column where the "
                      "primary-key column belongs and vice versa. Every "
                      "identifier is still correctly quoted, so nothing is a "
                      "syntax error — the statement simply retrieves the wrong "
                      "pair of values, so the reported detail for the offending "
                      "row is wrong and the expected error is not raised as "
                      "specified. It would NOT resolve.",
        "rationale": "REJECT from `out = violationStmts violations`: the "
                     "post-image fixes the order `quoteIdent pk` then "
                     "`quoteIdent col`; this rival emits them transposed. All "
                     "three positions remain QUOTED, so this is refuted purely by "
                     "the ORDER clause — the one thing the quoting rivals leave "
                     "untested. Refuted at a row with `pk = \"select\"`, "
                     "`col = \"where\"` (distinct identifiers, so the transposition "
                     "is observable).",
        "witness": _w2("[" + _viol("t", "select", "where") + "]"),
        "witness_reference": _LOOPFREE,
    },

    # ---- ADDED BY AUDIT: per-row statement ORDER -------------------------
    # The post-image fixes that a row's listing statement precedes its
    # value-fetch. No rival above varies that; this one emits both statements,
    # each fully correct, in the opposite order.
    {
        "id": "violation-row-statement-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _m2_reject_try(
            "    return (violations.flatMap (fun v =>\n"
            "      [selectSql v.pk v.col v.table, fkListSql v.table]))"),
        "refinement": "emitting a row's value-fetch before its listing statement "
                      "inverts the order the construction depends on: the listing "
                      "step is what identifies the referencing column the "
                      "value-fetch then selects, so running the fetch first uses "
                      "an identifier not yet determined for that row. The expected "
                      "error would not be raised as specified. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = violationStmts violations`: the "
                     "post-image emits `fkListSql v.table` FIRST and "
                     "`selectSql …` second per row; this rival swaps them. Both "
                     "statements are individually byte-correct and every "
                     "identifier is quoted, so the rejection is attributable "
                     "solely to the per-row ORDER clause. Refuted at a single row "
                     "with `table = \"group\"`, `pk = \"id\"`, `col = \"group_id\"` — "
                     "an input point no other reject case in this battery probes "
                     "(the earlier `\"order\"`-table row is the "
                     "violation-bare-fklist-table point).",
        "witness": _w2("[" + _viol("group", "id", "group_id") + "]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 2 bare-identifier rivals,
# 1 partial-domain constant rival) plus a 2-case AXIOM lane. This bundle models
# the SAME purely-functional core the sibling models — the assembly of the
# integrity-check / listing / value-fetch statements with every embedded
# identifier quoted — but reshapes the two nagini functions
# (build_single_table_command, build_three_id_command) into the two methods this
# backend actually contracts (buildCheckStatements over a LIST of tables,
# buildViolationStatements over a LIST of offending rows). The value/quoting
# surface carries across intact; the permission surface does not exist here.
#
#   sibling case                     -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-single-combined      -> pos-check-closed-form          RE-EXPRESSED
#                                       + pos-check-let-staged          (loop-preserving)
#   pos-control-three-reorder        -> pos-violation-closed-form      RE-EXPRESSED
#                                       + pos-violation-let-staged      (loop-preserving)
#   admissibility-single-call        -> admiss-obligation-satisfiable-  RE-EXPRESSED
#                                       at-reserved-word                (audit-added)
#   frame-mutation-single            -> (none)                         VACUOUS
#   frame-mutation-three             -> (none)                         VACUOUS
#   bare-identifier-single           -> check-constant-quote /         RE-EXPRESSED
#                                       violation-bare-* (bare splice)
#   bare-identifier-three            -> violation-bare-select-*         RE-EXPRESSED
#   partial-domain-constant-delim    -> check-constant-quote           PORTED
#   AXIOM_TESTS (2)                  -> (none)                         DROPPED (G-AX)
#
# 17 SPEC cases (7 soundness, 1 admissibility, 9 uniqueness). check-bare-table is ADDED so
# buildCheckStatements is attacked by TWO reject witnesses at distinct inputs
# (pts coverage), not one. pos-both-closed-form is ADDED as the shipped copy of
# the shared `witness_reference` (see WITNESS MECHANICS): the reject lane's
# discrimination half is decided against it, so the battery records that it
# verifies.
#
# THREE cases were ADDED BY A LATER INDEPENDENT AUDIT, each closing a clause the
# original six rivals left undefended (all three were built and measured):
#   check-quote-always-wrap            the SECOND `quoteIdent` branch
#                                      (already-quoted -> unchanged). The six
#                                      original rivals all splice a BARE
#                                      identifier, and bare == quoted on exactly
#                                      that sub-domain, so none of them could be
#                                      refuted there — measured: this witness
#                                      reports the tester TRUE against the
#                                      bare-splice rival.
#   violation-select-transpose-pk-col  WHICH identifier lands in WHICH selected
#                                      position (all three still quoted).
#   violation-row-statement-order      the per-row listing-before-value-fetch
#                                      order (both statements byte-correct).
# The original six all attack WHETHER a position is quoted; none attacked
# identifier ORDER or the pass-through branch. The added three carry a
# best-effort `first | rfl | simp_all […] | grind | decide` proof body instead of
# the loop-tuned frozen script, so their failure to verify cannot be read as a
# tactic mismatch.
#
# RE-EXPRESSED (positives): the sibling's single-table positive builds the whole
#   command in ONE combined concatenation; the equivalent maximally-different
#   reshape here is the loop-free `return (checkStmts tables)` (proof retuned to a
#   bare `loom_solve`, the tactic body being elided from the spec view). The
#   sibling's three-id positive reorders the three delimit calls; the analogous
#   loop-PRESERVING reshape here stages each statement into a named local before
#   prepending, keeping every invariant byte-identical so the frozen proof closes
#   untouched. Both reshapes are given for both methods (four positives total), so
#   each obligation is defended by a loop-free AND a loop-preserving correct impl.
# RE-EXPRESSED (bare-identifier / partial-domain rivals): the sibling's cheapest
#   WRONG impl splices the BARE identifier (the prepatch bug). Here that becomes
#   four bare-splice rivals — one per QUOTED identifier position the two methods
#   embed: the check statement's table (attacked via the constant-quote rival,
#   which drops the identifier entirely — the sibling's partial-domain-constant
#   rival), the listing statement's table, and the value-fetch SELECT's pk, col,
#   and table. The sibling's partial-domain-constant rival (emit a fixed `""`)
#   ports directly as check-constant-quote. Each refinement argument carries over:
#   a reserved-word identifier spliced bare (or replaced by an empty quoted token)
#   makes the assembled statement a syntax error / names the wrong table, so the
#   failing test's expected error is not raised and it would NOT resolve.
# VACUOUS (frame-mutation-single, frame-mutation-three): the sibling carries these
#   MANDATORY because `table_name` / `ident_a` are held at a fractional heap
#   permission and a rival can illegally write into them. This backend is
#   referentially transparent, both methods declare their argument read-only (no
#   `mut` binder), there is no heap and no aliasing — so there is no read-only
#   input to overwrite and no substitute probe. Not fabricated.
# RE-EXPRESSED (admissibility-single-call) — CORRECTED BY A LATER AUDIT. The
#   original port dropped this lane as VACUOUS, on the argument that no `require`
#   clause exists so there is no precondition to be too strong, and that a total
#   post-image is satisfiable everywhere by construction. That argument is WRONG as
#   a reason to omit the case: the analogue of PRECOND-TOO-STRONG on a total
#   carrier is the OBLIGATION being unsatisfiable at exactly an F2P-shaped input,
#   which a positive that discharges the obligation AT THAT CONCRETE INPUT — by
#   evaluation, as a `have`, before closing the frozen obligation verbatim — tests
#   directly. "Satisfiable by construction" is precisely the claim a machine-checked
#   case should be made to demonstrate rather than assert, and the four soundness
#   positives do NOT demonstrate it: they discharge the obligation universally
#   under the frozen script and never evaluate either post-image at a concrete
#   reserved-word identifier. Landed as admiss-obligation-satisfiable-at-
#   reserved-word, whose two `have`s pin `checkStmts` and `violationStmts` at a
#   reserved-word identifier by `decide`; both were measured LIVE (each conjunct
#   falsified to the bare identifier makes the case FAIL, exit 1).
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
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `quoteIdent == the real backend quoter`, mapping.md §3); this
#   bundle consumes no axiom `ensures`, and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. buildCheckStatements' single binder `tables` is
#   attacked by TWO rivals at distinct inputs — check-constant-quote (a
#   one-element list `["group"]`, the identifier dropped for a constant `""`) and
#   check-bare-table (a two-element list `["order", "table"]`, the bare identifier
#   spliced) — so `tables` is varied in both contents and length; its clause
#   `out = checkStmts tables` — i.e. the quoted table identifier in each
#   integrity-check statement — is the load-bearing thing both rivals get wrong.
#   buildViolationStatements' single binder `violations` carries three quoted
#   identifier positions, EACH attacked by a rival that mishandles ONLY that
#   position: `table` in the listing statement (violation-bare-fklist-table),
#   `pk` / `col` / `table` in the value-fetch SELECT (violation-bare-select-pk /
#   -col / -table). The nine reject witnesses probe NINE DISTINCT input points —
#   corrected by a later audit, which measured only EIGHT: violation-row-statement-
#   order originally reused violation-bare-fklist-table's exact row, so the
#   "DISTINCT input point" claim recorded here was false for that pair. It now
#   probes a row of its own (`table = "group"`, `pk = "id"`, `col = "group_id"`,
#   rebuilt and measured: rival exit 0, reference exit 1 by DECIDING). The points:
#   `["group"]` and `["order", "table"]` for buildCheckStatements, plus the
#   already-quoted `["\"order\""]`; and single-row batches with the reserved word
#   at table ("order"), pk ("select"), col ("where"), the SELECT's table ("where",
#   a row distinct from the "order" fkListSql-table row), the transposition row
#   (pk "select" / col "where"), and the statement-order row ("group"/"id"/
#   "group_id"). So both binders are varied (in length and contents) and
#   every quoted identifier position — the load-bearing discriminator of the whole
#   instance — is attacked by at least one rival.
#   The three audit-added rivals extend this from "is each position quoted" to the
#   two other things the post-image fixes: the already-quoted PASS-THROUGH branch
#   of `quoteIdent` (probed at `"order"` WITH its quotes — an input point outside
#   the reachable refutation set of every bare-splice rival) and ORDER, both of
#   WHICH identifier goes in WHICH selected position and of the two statements
#   within a row. Those two clauses were previously satisfiable by a rival that
#   quoted everything correctly, so the battery could not have detected them.
# WITNESS DISCRIMINATION. Each witness ELABORATES against its loop-free rival
#   (the extracted program reduces to a literal that provably differs from the
#   fold at the probed input) and FAILS, BY DECIDING, against the shared
#   `witness_reference` `_LOOPFREE`. The frozen solution cannot serve as that
#   second subject — its `while` fixpoint is stuck for EVERY claim, the true one
#   included, so its exit code carries no information — which is why every reject
#   case names the reference instead; see the docstring's WITNESS MECHANICS.
#   Measured for all nine: rival exit 0; reference exit 1 with "Tactic `decide`
#   proved that the proposition `<name>Tester … = false` is false", i.e. the
#   postcondition HOLDS there and the witness's claim is genuinely refuted on a
#   correct impl at the same input. None was stuck on the reference side. The
#   check is truth-tracking, not loop-presence-tracking: a FORGED witness at an
#   AGREEMENT point (`buildCheckStatementsTester ["\"order\"".toList] = false`
#   against the bare-splice rival, where bare and quoted coincide) does NOT
#   elaborate against the rival, so it fails the first half — though it would
#   have cleared both halves under a gold-side leg. No witness binds a hypothesis
#   (`quoteIdent` computes on Char literals), so there is no joint-satisfiability
#   obligation. No `sorry`/`admit`/`native_decide`/`axiom` appears.
# SPEC PROBES RUN BY THE AUDITS AND NOT SHIPPED AS CASES (all measured, exit
#   codes observed). CORRECT reshapes that VERIFY, none definitionally equal to
#   the frozen fold: `tables.map fkCheckSql` and the per-row `flatMap` form (both
#   now SHIPPED, as pos-check-map-induction / pos-violation-flatmap-induction);
#   `tables.foldr`; the per-row `map`-then-`flatten` form; and the identifier
#   transform applied TWICE per position (extensionally equal only because the
#   transform is idempotent, which the probe had to prove). So the spec is not
#   over-fit to the fold's shape — no SPEC-TOO-STRONG at any distance reached.
#   WRONG impls, all REJECTED under a best-effort ladder strong enough to close
#   the correct reshapes above (so no rejection is a tactic mismatch): reversing
#   the whole statement sequence; dropping the value-fetch so each row yields one
#   statement; emitting a statement for the FIRST table only; wrapping in SINGLE
#   quotes instead of double; reusing the primary-key identifier in the
#   referencing-column slot; emitting the rows in reverse; and three NEAR-MISSES on
#   the pass-through branch's guard — testing only the leading delimiter, joining
#   the two delimiter tests with OR instead of AND, and a looser guard that accepts
#   any non-empty identifier whose first and last characters agree. No spec hole
#   was found in either direction.
AXIOM_TESTS = []
